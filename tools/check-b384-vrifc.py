"""Build 384: the Virtual Room in every class. Madison: "The ifc version says the virtual room is only for the police academy
when I try to use it, but it shouldn't be. It should be for all the versions!"

A room belongs to the class it was made in: a Fire Code room carries `cls: "ifc"` and plays Fire Code's bank on every device
in it, an academy joiner's included (his app swaps the room's bank in for the room). A player from another class gets the
match (standings, vrMatches / vrWins / vrTop3) and nothing else of it: no XP, no question stats, no stars, no study time.
Fire Code reaches the room through its scoped friends handle (vroomDb = socialDb), which writes `vrooms` and nothing else.

THREE DEVICES, ONE CLOUD. Every device is its own browser context (its own storage, its own class) and they share one
Firestore: a stand-in served by this script over HTTP (documents, dotted updates, FieldValue / FieldPath, transactions,
batches, document and collection listeners by long poll), so a write on one phone reaches the others the way Firestore's
does. Every write is logged with the device that made it; every read a device takes is counted on that device (a get, a
query's documents, one per document change a listener is told of). The owner's account is TEST-3849 (a made-up code) and
the classmates are made up too.
 (1) the owner in Fire Code hosts: the room is a Fire Code room (cls "ifc"), his lobby says so;
 (2) an academy classmate is invited (the invite and the banner say "Fire Code room"), joins, and plays the SAME Fire Code
     questions in the SAME order; his lobby says what counts for him;
 (3) both finish and both devices rank the room the same way;
 (4) the academy joiner's academy store gains vrMatches and nothing else - no XP, no answers, no stats for Fire Code keys,
     no stars, no test, no study time - in his cloud copy too; the Fire Code host's own match counts as ever;
 (5) an academy room (two classmates) still works exactly as before: no class on the document or in the lobby, XP and stats
     as ever - and, the other way round, the owner in Fire Code joins an academy room and plays the academy's questions
     with nothing of them landing in Fire Code;
 (6) nothing from Fire Code is written to progress/<code> (the academy's) or the leaderboard - only progress/<code>__ifc
     and `vrooms`;
 (7) no sync code in any `vrooms` document;
 (8) no page errors; and the cost: room-document reads and writes for a match, Fire Code room against academy room.
Run:  python3 tools/check-b384-vrifc.py      (--against OLD/index.html must FAIL; it still runs (5) and prints its cost)"""
import copy, http.server, json, os, socket, sys, threading, time
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
OLD_BUILD = None
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
    def _patched(ins, _o=OLD):
        v = {"top": f"{ins[0]}px", "right": f"{ins[1]}px", "bottom": f"{ins[2]}px", "left": f"{ins[3]}px"}
        return g["INSET_RE"].sub(lambda m: v[m.group(1)], _o)
    g["patched"] = _patched
    import re as _re
    OLD_BUILD = _re.search(r'const APP_BUILD = "([^"]+)"', OLD).group(1)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else ("  -> " + str(info)[:500]), flush=True)

OWNER, CODE = "xph5b57jbp5a", "TEST-3849"
ALEX, ALEXCODE = "tst384vrax01", "TEST-3850"
KIM, KIMCODE = "tst384vrkm02", "TEST-3851"
CODES = [CODE, ALEXCODE, KIMCODE]
NAMES = {OWNER: "Maddox", ALEX: "Alexis", KIM: "Kimber"}
FCODES = {OWNER: "QRV-384", ALEX: "AXV-384", KIM: "KMV-384"}

# ------------------------------------------------------------------ the shared cloud
now_ms = lambda: int(time.time() * 1000)
def is_fv(x): return isinstance(x, dict) and "__fv" in x
def jkey(x): return json.dumps(x, sort_keys=True)
def resolve(v):
    if is_fv(v): return now_ms() if v["__fv"] == "ts" else None
    if isinstance(v, list): return [resolve(x) for x in v]
    if isinstance(v, dict): return {k: resolve(x) for k, x in v.items() if not (is_fv(x) and x["__fv"] == "delete")}
    return v
def set_path(obj, segs, v):
    o = obj
    for s in segs[:-1]:
        if not isinstance(o.get(s), dict): o[s] = {}
        o = o[s]
    k = segs[-1]
    if is_fv(v):
        kind, arg = v["__fv"], v.get("arg")
        if kind == "delete": o.pop(k, None)
        elif kind == "arrayUnion":
            a = o.get(k) if isinstance(o.get(k), list) else []
            for x in arg or []:
                if jkey(x) not in [jkey(y) for y in a]: a.append(copy.deepcopy(x))
            o[k] = a
        elif kind == "arrayRemove":
            a = o.get(k) if isinstance(o.get(k), list) else []
            o[k] = [y for y in a if jkey(y) not in [jkey(x) for x in arg or []]]
        elif kind == "increment": o[k] = (o.get(k) or 0) + arg
        else: o[k] = now_ms()
    else: o[k] = resolve(v)
def merge_into(o, v):
    for k, x in v.items():
        if isinstance(x, dict) and not is_fv(x):
            if not isinstance(o.get(k), dict): o[k] = {}
            merge_into(o[k], x)
        else: set_path(o, [k], x)
def matches(d, f):
    for k, op, v in f or []:
        x = (d or {}).get(k)
        try:
            okk = {">": lambda: x > v, ">=": lambda: x >= v, "<": lambda: x < v, "<=": lambda: x <= v, "==": lambda: x == v,
                   "!=": lambda: x != v, "array-contains": lambda: isinstance(x, list) and v in x, "in": lambda: x in (v or [])}.get(op, lambda: True)()
        except TypeError: okk = False
        if not okk: return False
    return True

class Cloud:
    def __init__(self, seed):
        self.cv = threading.Condition()
        self.data = copy.deepcopy(seed)
        for c in ("progress", "leaderboard", "vrooms"): self.data.setdefault(c, {})
        self.log = []          # log[v-1] = (c, id)
        self.writes = []       # {dev, op, path}
    @property
    def v(self): return len(self.log)
    def apply(self, dev, o):
        c, i, op = o["c"], o["id"], o["op"]
        col = self.data.setdefault(c, {})
        if op == "set":
            if o.get("merge"):
                cur = copy.deepcopy(col.get(i) or {}); merge_into(cur, o.get("v") or {})
            else: cur = resolve(o.get("v") or {})
            col[i] = cur
        elif op == "update":
            if i not in col: raise KeyError("not-found")
            cur = copy.deepcopy(col[i])
            if "fields" in o:
                for k, x in o["fields"].items(): set_path(cur, k.split("."), x)
            else:
                p = o.get("pairs") or []
                for n in range(0, len(p) - 1, 2):
                    key = p[n]
                    segs = key["__fp"] if isinstance(key, dict) and "__fp" in key else str(key).split(".")
                    set_path(cur, segs, p[n + 1])
            col[i] = cur
        elif op == "delete": col.pop(i, None)
        self.writes.append({"dev": dev, "op": op, "path": c + "/" + i})
        self.log.append((c, i))
    def handle(self, op, b):
        with self.cv:
            if op == "get":
                d = self.data.get(b["c"], {}).get(b["id"])
                return {"exists": d is not None, "data": d, "v": self.v}
            if op == "query":
                return {"docs": [[i, d] for i, d in self.data.get(b["c"], {}).items() if matches(d, b.get("f"))], "v": self.v}
            if op in ("set", "update", "delete"):
                try: self.apply(b.get("dev"), dict(b, op=op))
                except KeyError: return {"error": "not-found"}
                self.cv.notify_all(); return {"ok": True}
            if op == "commit":
                ops = b.get("ops") or []
                for o in ops:
                    if o["op"] == "update" and o["id"] not in self.data.get(o["c"], {}): return {"error": "not-found"}
                for o in ops: self.apply(b.get("dev"), o)
                self.cv.notify_all(); return {"ok": True}
            if op == "poll":
                since = int(b.get("since") or 0); end = time.time() + 1.5
                while self.v <= since and time.time() < end: self.cv.wait(max(0.01, end - time.time()))
                latest = {}
                for n in range(since, self.v):
                    latest[self.log[n]] = n + 1
                out = []
                for (c, i), v in latest.items():
                    d = self.data.get(c, {}).get(i)
                    out.append([c, i, d is not None, d, v])
                return {"v": self.v, "changed": out}
            if op == "dump": return {"data": self.data}
            if op == "writes": return {"writes": self.writes}
            return {"error": "unknown op " + op}

CLOUD = None
# THE PAGE IS SERVED FROM THE CLOUD'S OWN ORIGIN. A page Playwright fulfils by route sits outside the loopback address space,
# and Chromium's local-network checks then refuse its requests to 127.0.0.1 - so the app, its files and the stand-in are one
# origin here, and the stand-in's requests are same-origin.
INDEX_BODY = None
MIME = {".js": "application/javascript", ".mjs": "application/javascript", ".json": "application/json", ".html": "text/html; charset=utf-8",
        ".css": "text/css", ".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml", ".pdf": "application/pdf", ".webp": "image/webp",
        ".mp3": "audio/mpeg", ".woff2": "font/woff2", ".wasm": "application/wasm"}
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        p = self.path.split("?")[0]
        if p in ("/", "/index.html"):
            b, ct = INDEX_BODY, MIME[".html"]
        elif p == "/version.json" and OLD_BUILD:
            b, ct = json.dumps({"build": OLD_BUILD, "force": False, "frameId": ""}).encode(), MIME[".json"]
        else:
            f = os.path.realpath(os.path.join(g["ROOT"], p.lstrip("/")))
            if not f.startswith(os.path.realpath(g["ROOT"]) + os.sep) or not os.path.isfile(f):
                self.send_response(404); self.send_header("Content-Length", "0"); self.end_headers(); return
            b, ct = open(f, "rb").read(), MIME.get(os.path.splitext(f)[1].lower(), "application/octet-stream")
        self.send_response(200)
        self.send_header("Content-Type", ct); self.send_header("Content-Length", str(len(b))); self.send_header("Cache-Control", "no-store")
        self.end_headers(); self.wfile.write(b)
    def _send(self, code, obj=None):
        b = json.dumps(obj).encode() if obj is not None else b""
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        if b: self.wfile.write(b)
    def do_OPTIONS(self): self._send(204)
    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        try: body = json.loads(self.rfile.read(n) or b"{}")
        except Exception: body = {}
        try: self._send(200, CLOUD.handle(self.path.strip("/").split("?")[0], body))
        except Exception as e: self._send(200, {"error": "server: " + str(e)})
def serve_cloud():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    class Srv(http.server.ThreadingHTTPServer):
        daemon_threads = True
        def handle_error(self, request, client_address): pass   # a page closed mid long-poll is not a finding
    srv = Srv(("127.0.0.1", port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, "http://127.0.0.1:%d" % port

# ------------------------------------------------------------------ the client stand-in each page gets as window.firebase
CLIENT = r"""(()=>{
  const BASE = window.__cloudUrl, DEV = window.__dev;
  const clone = v => v == null ? v : JSON.parse(JSON.stringify(v));
  function FV(kind, arg){ this.__fv = kind; this.arg = arg; }
  function FieldPath(){ this.segs = Array.prototype.slice.call(arguments); }
  const enc = v => {
    if(v instanceof FV) return { __fv: v.__fv, arg: v.arg === undefined ? null : enc(v.arg) };
    if(v instanceof FieldPath) return { __fp: v.segs.slice() };
    if(Array.isArray(v)) return v.map(enc);
    if(v && typeof v === 'object'){ const o = {}; Object.keys(v).forEach(k => { if(v[k] !== undefined) o[k] = enc(v[k]); }); return o; }
    return v;
  };
  const S = window.__fs = { reads: 0, by: {} };
  const countRead = (key, n) => { n = n || 1; S.reads += n; S.by[key] = (S.by[key] || 0) + n; };
  const call = (op, body) => fetch(BASE + '/' + op, { method: 'POST', body: JSON.stringify(Object.assign({ dev: DEV }, body || {})) })
    .then(r => r.json()).then(j => { if(j && j.error){ const e = new Error(j.error); e.code = j.error; throw e; } return j; });
  const meta = { fromCache: false, hasPendingWrites: false };
  const dsnap = (c, id, ex, data) => ({ id, exists: !!ex, data: () => ex ? clone(data) : undefined, get: k => clone((data || {})[k]), metadata: meta });
  const qsnap = docs => ({ empty: !docs.length, size: docs.length, docs, forEach: cb => docs.forEach(cb), metadata: meta, docChanges: () => [] });
  const match = (d, f) => f.every(([k, op, v]) => { const x = d ? d[k] : undefined;
    return op === '>' ? x > v : op === '>=' ? x >= v : op === '<' ? x < v : op === '<=' ? x <= v : op === '==' ? x === v : op === '!=' ? x !== v
      : op === 'array-contains' ? (Array.isArray(x) && x.indexOf(v) >= 0) : op === 'in' ? (Array.isArray(v) && v.indexOf(x) >= 0) : true; });
  const later = e => setTimeout(() => { throw e; }, 0);
  const docSubs = {}, colSubs = [], lastV = {};
  let ver = 0, polling = false;
  const applyCol = (s, e) => {
    const [c, id, ex, data, v] = e;
    if(v <= s.v) return 0;
    const was = s.map.has(id), now = ex && match(data, s.f);
    if(now){ s.map.set(id, data); return 1; }
    if(was){ s.map.delete(id); return 1; }
    return 0;
  };
  const deliverCol = s => { const docs = [...s.map.entries()].map(([id, d]) => dsnap(s.c, id, true, d)); try{ s.cb(qsnap(docs)); }catch(err){ later(err); } };
  function startPoll(){
    if(polling) return; polling = true;
    (async () => { for(;;){
      try{
        const r = await call('poll', { since: ver });
        ver = r.v;
        r.changed.forEach(e => {
          const [c, id, ex, data, v] = e, k = c + '/' + id;
          const subs = (docSubs[k] || []).slice();
          if(subs.length && v > (lastV[k] || 0)){
            lastV[k] = v; countRead(k);
            subs.forEach(cb => { try{ cb(dsnap(c, id, ex, data)); }catch(err){ later(err); } });
          }
          colSubs.slice().forEach(s => {
            if(s.c !== c) return;
            if(!s.ready){ s.pending.push(e); return; }
            if(applyCol(s, e)){ countRead(c + '?'); deliverCol(s); }
          });
        });
      }catch(err){ await new Promise(res => setTimeout(res, 300)); }
    } })();
  }
  function doc(c, id){
    const k = c + '/' + id;
    return { id, path: k, __c: c,
      get: () => call('get', { c, id }).then(r => { countRead(k); return dsnap(c, id, r.exists, r.data); }),
      set: (v, o) => call('set', { c, id, v: enc(v), merge: !!(o && o.merge) }).then(() => undefined),
      update: function(){ const a = [...arguments];
        const body = (a.length === 1 && a[0] && typeof a[0] === 'object' && !(a[0] instanceof FieldPath)) ? { fields: enc(a[0]) } : { pairs: enc(a) };
        return call('update', Object.assign({ c, id }, body)).then(() => undefined); },
      delete: () => call('delete', { c, id }).then(() => undefined),
      onSnapshot: function(){
        const next = [...arguments].find(x => typeof x === 'function');
        let alive = true;
        const cb = s => { if(alive) next(s); };
        (docSubs[k] = docSubs[k] || []).push(cb);
        startPoll();
        call('get', { c, id }).then(r => { if(!alive || (lastV[k] || 0) > r.v) return; lastV[k] = r.v; countRead(k); try{ next(dsnap(c, id, r.exists, r.data)); }catch(err){ later(err); } }).catch(() => {});
        return () => { alive = false; docSubs[k] = (docSubs[k] || []).filter(x => x !== cb); };
      },
      collection: n => coll(c + '/' + id + '/' + n) };
  }
  function coll(c, f){
    f = f || [];
    const q = {
      doc: id => doc(c, id === undefined ? 'auto' + Math.random().toString(36).slice(2) : id),
      where: (k, op, v) => coll(c, f.concat([[k, op, v]])),
      orderBy(){ return q; }, limit(){ return q; }, limitToLast(){ return q; }, startAt(){ return q; }, startAfter(){ return q; }, endAt(){ return q; }, endBefore(){ return q; },
      get: () => call('query', { c, f: enc(f) }).then(r => { countRead(c + '?', Math.max(1, r.docs.length)); return qsnap(r.docs.map(([id, d]) => dsnap(c, id, true, d))); }),
      add: v => { const d = doc(c, 'auto' + Math.random().toString(36).slice(2)); return d.set(v).then(() => d); },
      onSnapshot: function(){
        const next = [...arguments].find(x => typeof x === 'function');
        const s = { c, f, cb: x => { if(s.alive) next(x); }, map: new Map(), ready: false, pending: [], v: 0, alive: true };
        colSubs.push(s);
        startPoll();
        call('query', { c, f: enc(f) }).then(r => {
          if(!s.alive) return;
          r.docs.forEach(([id, d]) => s.map.set(id, d));
          s.v = r.v; s.ready = true;
          const pend = s.pending; s.pending = []; pend.forEach(e => applyCol(s, e));
          countRead(c + '?', Math.max(1, r.docs.length));
          deliverCol(s);
        }).catch(() => {});
        return () => { s.alive = false; const i = colSubs.indexOf(s); if(i >= 0) colSubs.splice(i, 1); };
      } };
    return q;
  }
  const writer = ops => { const w = {
    set(r, v, o){ ops.push({ op: 'set', c: r.__c, id: r.id, v: enc(v), merge: !!(o && o.merge) }); return w; },
    update(r){ const a = [...arguments].slice(1);
      ops.push(Object.assign({ op: 'update', c: r.__c, id: r.id }, (a.length === 1 && a[0] && typeof a[0] === 'object' && !(a[0] instanceof FieldPath)) ? { fields: enc(a[0]) } : { pairs: enc(a) }));
      return w; },
    delete(r){ ops.push({ op: 'delete', c: r.__c, id: r.id }); return w; } }; return w; };
  const db = { collection: n => coll(n),
    runTransaction: fn => { const ops = []; const tx = writer(ops);
      tx.get = r => call('get', { c: r.__c, id: r.id }).then(x => { countRead(r.__c + '/' + r.id); return dsnap(r.__c, r.id, x.exists, x.data); });
      return Promise.resolve().then(() => fn(tx)).then(res => call('commit', { ops }).then(() => res)); },
    batch: () => { const ops = []; const b = writer(ops); b.commit = () => call('commit', { ops }).then(() => undefined); return b; } };
  const fs = () => db;
  fs.FieldValue = { delete: () => new FV('delete'), serverTimestamp: () => new FV('ts'), arrayUnion: (...x) => new FV('arrayUnion', x),
                    arrayRemove: (...x) => new FV('arrayRemove', x), increment: n => new FV('increment', n) };
  fs.FieldPath = FieldPath;
  window.firebase = { apps: [], initializeApp(){ this.apps.push({}); }, firestore: fs };
})()"""

# ------------------------------------------------------------------ accounts
INDEX_BODY = g["patched"]((59, 0, 34, 0)).encode("utf-8")
csrv, cloud_url = serve_cloud()
WEEK = g["week_key_now"]()
T0 = now_ms()
def academy_store(pub, friends):
    d = json.loads(g["SEED"].replace("__WEEK__", WEEK))
    d.update({"publicId": pub, "firstName": NAMES[pub], "novaMet": 99, "friendCode": FCODES[pub], "friendsIn": list(friends), "friendsOut": [],
              "friendsDeclined": [], "chats": [], "leaderboardOptIn": True, "lastModified": T0 - 3600000})
    d.setdefault("novaHeard", {})["@recap"] = 99991231
    return d
owner_acad = academy_store(OWNER, [ALEX])
alex = academy_store(ALEX, [OWNER, KIM]); alex["avatarChar"] = "ghost"
kim = academy_store(KIM, [ALEX]); kim["avatarChar"] = "grizzly"
ifc = {k: owner_acad[k] for k in ["firstName", "avatarChar", "publicId", "onboardingComplete", "tourRev", "novaMet", "novaHeard", "weekKey"] if k in owner_acad}
ifc.update({k: v for k, v in owner_acad.items() if k.startswith("seen")})
ifc.update({"lifetime": dict(owner_acad["lifetime"], points=4321, correct=777), "leaderboardOptIn": False, "leaderboardOptInChanged": True,
            "lastModified": T0 - 1800000})
def row(pub, lvl):
    return {"firstName": NAMES[pub], "avatarChar": "ninja", "level": lvl, "badges": 3, "mystery": 0, "hundos": 4, "correct": 120,
            "week": WEEK, "weekPoints": 50, "fcode": FCODES[pub], "freq": [], "facc": [], "lastModified": T0 - 60000}
SEED_CLOUD = {
    "progress": {CODE: owner_acad, ALEXCODE: alex, KIMCODE: kim},
    "leaderboard": {OWNER: row(OWNER, 23), ALEX: row(ALEX, 31), KIM: row(KIM, 12)},
    "vrooms": {"presence-v1": {"kind": "presence", "p": {}, "a": {}}},
}
CLOUD = Cloud(SEED_CLOUD)
SEEN = ("['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card',"
        "'class26e.getstarted','class26e.frame.ok','class26e.penal55124.seen','class26e.penal124256.seen','class26e.penal256578.seen']"
        ".forEach(k=>localStorage.setItem(k, k==='class26e.frame.ok'?'go-live-1':k==='class26e.intro.seen'?'9':'1'));")
def init_academy(st, code):
    return ("(()=>{ if(sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); " + SEEN +
            "localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode', '%s'); })()" % (json.dumps(json.dumps(st)), code))
def init_ifc():
    s = "(()=>{ if(sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); " + SEEN
    s += "localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode', '%s');" % (json.dumps(json.dumps(owner_acad)), CODE)
    s += "localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done');"
    s += "['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted'].forEach(k=>localStorage.setItem(k,'1'));"
    s += "localStorage.setItem('class26e.activeclass','ifc'); localStorage.setItem('class26e.ifc.drill.v1', %s);" % json.dumps(json.dumps(ifc))
    return s + " })()"

ERRS = {}
def device(br, dev, init):
    ctx = br.new_context(viewport={"width": 440, "height": 956}, has_touch=True)
    ctx.add_init_script("window.__cloudUrl = %s; window.__dev = %s;" % (json.dumps(cloud_url), json.dumps(dev)))
    ctx.add_init_script(CLIENT)
    ctx.add_init_script(g["STANDALONE"])
    ctx.add_init_script(init)
    pg = ctx.new_page(); ERRS[dev] = []
    pg.on("pageerror", lambda e, d=dev: ERRS[d].append(str(e)[:240]))
    pg.goto(cloud_url + "/index.html"); pg.wait_for_timeout(3800)
    pg.evaluate("document.getElementById('splashscreen')?.remove()")
    try: ctx.new_cdp_session(pg).send("Page.setWebLifecycleState", {"state": "active"})
    except Exception: pass
    # a seeded account can open on an unlock cutscene, which holds every banner until it ends (check-b384-navmeet): let it end
    for _ in range(60):
        if not pg.evaluate("()=>document.body.classList.contains('cutscene-focus') || document.body.classList.contains('cutscene-return') || (typeof cutsceneFocusActive === 'function' && cutsceneFocusActive())"): break
        pg.evaluate("()=>{ document.querySelectorAll('.unlock-card .next, .rs-spot .next, .cutscene-skip, .ru-skip').forEach(b=>{ try{ b.click(); }catch(e){} }); }")
        pg.wait_for_timeout(500)
    return ctx, pg

def wait_for(pg, js, arg=None, tries=40, step=400):
    v = None
    for _ in range(tries):
        try: v = pg.evaluate(js, arg) if arg is not None else pg.evaluate(js)
        except Exception as e: v = None
        if v: return v
        pg.wait_for_timeout(step)
    return v
def dump(): return CLOUD.handle("dump", {})["data"]
def writes(): return list(CLOUD.writes)
def room_cost(code, w0, reads0, pages):
    """the room document's writes (by device) and reads (by device) since the marks"""
    ws = [w for w in writes()[w0:] if w["path"] == "vrooms/" + code]
    out = {"writes": len(ws), "reads": 0, "by": {}}
    for dev, pg in pages.items():
        r = pg.evaluate("(k)=>(window.__fs.by[k] || 0)", "vrooms/" + code) - reads0.get(dev, 0)
        out["by"][dev] = {"w": len([w for w in ws if w["dev"] == dev]), "r": r}
        out["reads"] += r
    return out
def reads_of(pages, code):
    return {dev: pg.evaluate("(k)=>(window.__fs.by[k] || 0)", "vrooms/" + code) for dev, pg in pages.items()}

READY = "body:has(#stage > .screen-vroom-lobby) #stage > .vroom-setup-bar > .vroom-readyup-btn"
STORE = """()=>{ const keys = Object.keys(store.stats || {});
  let study = 0; Object.values(store.studyLog || {}).forEach(v => { study += Number(v) || 0; });
  return { cls: window.NOVA_CLASS, points: store.lifetime.points, answered: store.lifetime.answered, correct: store.lifetime.correct,
           stats: keys.length, statKeys: keys, flagged: Object.keys(store.flagged || {}).length, perfects: JSON.stringify(store.unitPerfects || {}),
           tests: (store.testHistory || []).length, study, vrMatches: store.vrMatches || 0, vrWins: store.vrWins || 0, vrTop3: store.vrTop3 || 0,
           exam: store.lifetime.examPlays || 0, retaken: store.retakenQuestions || 0 }; }"""
SMALL_UNIT = """()=>{ const t = topicsIn(QUESTIONS).map(u => [u, unitQuestionCount(u)]).filter(x => x[1] >= 6).sort((a, b) => a[1] - b[1]);
  return t.length ? t[0][0] : null; }"""
LOBBY_TEXT = "()=>{ const s = document.querySelector('#stage .vroom-test-summary'); return s ? s.innerText : null; }"
ORDER = """()=>(typeof order !== 'undefined' && order.length && testInProgress) ? { qs: order.map(qi => QUESTIONS[qi].q), topics: [...new Set(order.map(qi => QUESTIONS[qi].topic))],
  ifc: order.every(qi => !!QUESTIONS[qi].ifc), bank: (typeof BANK_CLASS !== 'undefined') ? BANK_CLASS : null } : null"""
REVEALED = "()=>!!document.querySelector('.qpanel .choice') && !document.getElementById('vroom-reveal-overlay') && typeof vroomStartAt === 'number' && Date.now() > vroomStartAt + 300"
ANSWER = """async (miss)=>{ const W = ms => new Promise(r => setTimeout(r, ms));
  const n = order.length; let done = 0;
  for(let i = 0; i < n; i++){
    const qi = order[pos];
    const right = optionOrder(qi).indexOf(QUESTIONS[qi].answer);
    const slot = (i < miss) ? (right + 1) % optionOrder(qi).length : right;
    choose(slot); await W(260); advance(); await W(220); done++;
  }
  return done; }"""
ALL_IN = "()=>!!document.querySelector('.vroom-waitcard.is-all-in')"
STANDINGS = """()=>{ const d = (typeof lastFinaleData !== 'undefined' && lastFinaleData) || null; if(!d) return null;
  return vroomRankedEntries(d).map(e => [e.key, e.xp, !!e.p.finished]); }"""

def host_room(pg, unit, n=5):
    """the host card, then Match settings' result written the way the setup screen writes it (units, game, count)"""
    pg.evaluate("()=>{ cfg.mode = 'vroom'; showVirtualRoomChoice(); }"); pg.wait_for_timeout(700)
    has = pg.evaluate("()=>!!document.querySelector('#stage .vrc-card-host')")
    if not has: return None
    pg.click("#stage .vrc-card-host")
    code = wait_for(pg, "()=>(typeof vroomCode === 'string' && vroomCode && document.querySelector('#stage .screen-vroom-lobby')) ? vroomCode : null", tries=30)
    if not code: return None
    pg.evaluate("""(a)=>vroomDb().collection('vrooms').doc(vroomCode).update({ units: [a.unit], game: 'race', count: a.n, versions: {} })""".replace("vroomDb()", "(typeof vroomDb === 'function' ? vroomDb() : fbDb)"), {"unit": unit, "n": n})
    wait_for(pg, "(u)=>{ const s = document.querySelector('#stage .vroom-test-summary'); return !!(s && s.innerText.indexOf(u) >= 0); }", unit, tries=20)
    return code
def ready_both(pages):
    for pg in pages:
        pg.wait_for_selector(READY + ":not([disabled])", state="visible", timeout=20000)
    for pg in pages:
        pg.click(READY); pg.wait_for_timeout(300)
def play_match(pages, misses):
    """both devices: wait out the shared countdown, take the order, answer every question (misses[i] wrong first)"""
    orders = []
    for pg in pages:
        orders.append(wait_for(pg, ORDER, tries=80, step=300))
    for pg in pages:
        wait_for(pg, REVEALED, tries=80, step=300)
    for pg, m in zip(pages, misses):
        pg.evaluate(ANSWER, m)
    ins = [wait_for(pg, ALL_IN, tries=80, step=400) for pg in pages]
    pages[0].wait_for_timeout(1500)
    return orders, ins
def leave(pg):
    pg.evaluate("()=>{ try{ document.getElementById('vroom-race-cut')?.remove(); document.getElementById('vroom-prep')?.remove(); leaveVirtualRoom(); showHome(); }catch(e){} }")
    pg.wait_for_timeout(900)

COST = {}
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    actx, A = device(br, "ifc", init_ifc())            # the owner, in Fire Code
    bctx, B = device(br, "alex", init_academy(alex, ALEXCODE))   # an academy classmate, his friend
    pages = {"ifc": A, "alex": B}
    r = A.evaluate("()=>({ cls: window.NOVA_CLASS, fb: (typeof fbDb === 'undefined') ? 'undef' : (fbDb === null ? null : 'set'), pub: store.publicId })")
    chk("the owner's device is in Fire Code with fbDb null, as the academy account %s (%s)" % (OWNER, r), r["cls"] == "ifc" and r["fb"] is None and r["pub"] == OWNER, r)

    # ===================== (1)-(4): a Fire Code room, an academy joiner =====================
    print("\n-- a Fire Code room: the owner hosts from Fire Code, an academy classmate joins", flush=True)
    s1 = False
    try:
        choice = A.evaluate("()=>{ cfg.mode = 'vroom'; showVirtualRoomChoice(); const s = document.querySelector('#stage .screen-vroom-choice');"
                            " return s ? { note: (s.querySelector('.info-note') || {}).textContent || '', host: !!s.querySelector('.vrc-card-host'), join: !!s.querySelector('.vrc-card-browse') } : null; }")
        chk("(1) Fire Code's Virtual Room screen offers Host a room and Join an open room, with no 'only for the Police Academy' note (%s)" % choice,
            bool(choice) and choice["host"] and choice["join"] and "Police Academy" not in choice["note"], choice)
        ifc_unit = A.evaluate(SMALL_UNIT)
        w0 = len(writes()); r0 = {d: p.evaluate("()=>window.__fs.reads") for d, p in pages.items()}
        code = host_room(A, ifc_unit) if choice and choice["host"] else None
        doc = (dump()["vrooms"].get(code) or {}) if code else {}
        chk("(1) hosting from Fire Code makes a Fire Code room: cls 'ifc', the academy account as host, units %r (%s)" % (ifc_unit, {k: doc.get(k) for k in ("cls", "hostCode", "units", "game")}),
            bool(code) and doc.get("cls") == "ifc" and doc.get("hostCode") == OWNER and OWNER in (doc.get("participants") or {}) and doc.get("units") == [ifc_unit], doc)
        lt = A.evaluate(LOBBY_TEXT) or ""
        chk("(1) the host's lobby says it is a Fire Code room (%r)" % lt[:160], "Fire Code room" in lt and "No XP" not in lt, lt)
        if not code: raise RuntimeError("no room")
        # the invite
        A.evaluate("(c)=>inviteFriendToLobby(%s, c)" % json.dumps(ALEX), code)
        A.wait_for_timeout(800)
        inv = ((dump()["vrooms"].get("inbox-" + ALEX) or {}).get("msgs") or {}).get(OWNER) or {}
        chk("(2) the invite in the friend's mailbox carries the room and its class (%s)" % {k: inv.get(k) for k in ("type", "code", "cls")},
            inv.get("type") == "vroom" and inv.get("code") == code and inv.get("cls") == "ifc", inv)
        ban = wait_for(B, """(c)=>{ const x = incomingLobbyInvites().find(i => i.code === c); if(!x) return null; checkLobbyInvites();
            const b = document.getElementById('lobby-invite'); return { cls: x.cls, banner: b ? b.innerText : '' }; }""", code, tries=30)
        chk("(2) the academy classmate's invite banner says 'Fire Code room' (%s)" % ban, bool(ban) and ban["cls"] == "ifc" and "Fire Code room" in ban["banner"], ban)
        before_b = B.evaluate(STORE); before_a = A.evaluate(STORE)
        if ban and B.evaluate("()=>!!document.querySelector('#lobby-invite .app-banner-act')"):
            B.click("#lobby-invite .app-banner-act")
        else:
            B.evaluate("(c)=>joinVirtualRoomLobby(c)", code)
        joined = wait_for(B, "()=>(document.querySelector('#stage .screen-vroom-lobby') && vroomCode) ? { bank: BANK_CLASS, ifcq: !!QUESTIONS[0].ifc, noun: classNoun(true) } : null", tries=40)
        chk("(2) the academy classmate joins the Fire Code room, and his app now holds Fire Code's bank (%s)" % joined,
            bool(joined) and joined["bank"] == "ifc" and joined["ifcq"] and joined["noun"] == "chapters", joined)
        lt = B.evaluate(LOBBY_TEXT) or ""
        chk("(2) his lobby says it is a Fire Code room, what counts for him, and names the chapter (%r)" % lt[:220],
            "Fire Code room" in lt and "No XP" in lt and ifc_unit in lt, lt)
        rows = wait_for(A, "()=>{ const n = document.querySelectorAll('#stage .vroom-row').length; return n >= 2 ? n : 0; }", tries=20)
        chk("(2) the host sees him arrive (%s rows)" % rows, rows == 2, rows)
        ws_mid = len(writes()); rd_mid = reads_of(pages, code)
        COST["fc_setup"] = room_cost(code, w0, {d: 0 for d in pages}, pages)
        ready_both([A, B])
        orders, ins = play_match([A, B], [0, 1])
        oa, ob = orders
        chk("(2) both devices play the same Fire Code questions in the same order (%d questions, chapter %s)" % (len((oa or {}).get("qs") or []), (oa or {}).get("topics")),
            bool(oa) and bool(ob) and oa["qs"] == ob["qs"] and len(oa["qs"]) == 5 and oa["ifc"] and ob["ifc"] and oa["topics"] == [ifc_unit] and ob["bank"] == "ifc", {"a": oa, "b": ob})
        st_a, st_b = A.evaluate(STANDINGS), B.evaluate(STANDINGS)
        chk("(3) both finish and both devices rank the room the same: %s" % st_a,
            all(ins) and bool(st_a) and st_a == st_b and len(st_a) == 2 and all(x[2] for x in st_a) and st_a[0][0] == OWNER and st_a[0][1] > st_a[1][1] > 0, {"a": st_a, "b": st_b, "in": ins})
        COST["fc_match"] = room_cost(code, ws_mid, rd_mid, pages)
        after_b = wait_for(B, "(m)=>{ const s = (%s)(); return s.vrMatches > m ? s : null; }" % STORE, before_b["vrMatches"], tries=20) or B.evaluate(STORE)
        ifc_keys = [k for k in after_b["statKeys"] if k.startswith(ifc_unit + "|") or k.startswith("Chapter ")]
        chk("(4) the academy joiner's academy store gains the match (vrMatches %d -> %d) and nothing else: XP %d -> %d, answered %d -> %d, stats %d -> %d (Fire Code keys %d), stars, hundos, tests, study time unchanged"
            % (before_b["vrMatches"], after_b["vrMatches"], before_b["points"], after_b["points"], before_b["answered"], after_b["answered"], before_b["stats"], after_b["stats"], len(ifc_keys)),
            after_b["vrMatches"] == before_b["vrMatches"] + 1 and after_b["points"] == before_b["points"] and after_b["answered"] == before_b["answered"]
            and after_b["correct"] == before_b["correct"] and after_b["stats"] == before_b["stats"] and not ifc_keys and after_b["flagged"] == before_b["flagged"]
            and after_b["perfects"] == before_b["perfects"] and after_b["tests"] == before_b["tests"] and after_b["study"] == before_b["study"]
            and after_b["exam"] == before_b["exam"] and after_b["cls"] == "academy", {"before": {k: v for k, v in before_b.items() if k != "statKeys"}, "after": {k: v for k, v in after_b.items() if k != "statKeys"}})
        rnote = B.evaluate("()=>{ const x = document.querySelector('#stage .rs-xp'); return x ? x.innerText : null; }") or ""
        chk("(4) his results say no XP, and why (%r)" % rnote[:140], "No XP" in rnote and "Fire Code room" in rnote and "Level" not in rnote, rnote)
        # the account's push is at most once a minute; flush it the way leaving the app does
        B.evaluate("()=>pushToCloud()")
        cdoc = {}
        for _ in range(30):
            cdoc = dump()["progress"].get(ALEXCODE) or {}
            if (cdoc.get("vrMatches") or 0) == after_b["vrMatches"]: break
            B.wait_for_timeout(400)
        chk("(4) and his cloud copy the same: vrMatches %s, XP %s (was %s), stats %d" % (cdoc.get("vrMatches"), (cdoc.get("lifetime") or {}).get("points"), before_b["points"], len(cdoc.get("stats") or {})),
            cdoc.get("vrMatches") == after_b["vrMatches"] and (cdoc.get("lifetime") or {}).get("points") == before_b["points"]
            and not [k for k in (cdoc.get("stats") or {}) if k.startswith(ifc_unit + "|")], {k: cdoc.get(k) for k in ("vrMatches", "lifetime")})
        after_a = wait_for(A, "(m)=>{ const s = (%s)(); return s.vrMatches > m ? s : null; }" % STORE, before_a["vrMatches"], tries=20) or A.evaluate(STORE)
        chk("(4) the Fire Code host's own match counts in Fire Code as ever: vrMatches %d -> %d, XP %d -> %d, Fire Code stats %d -> %d"
            % (before_a["vrMatches"], after_a["vrMatches"], before_a["points"], after_a["points"], before_a["stats"], after_a["stats"]),
            after_a["vrMatches"] == before_a["vrMatches"] + 1 and after_a["points"] > before_a["points"] and after_a["stats"] >= before_a["stats"] + 5
            and any(k.startswith(ifc_unit + "|") for k in after_a["statKeys"]), {k: v for k, v in after_a.items() if k != "statKeys"})
        leave(A); leave(B)
        back = B.evaluate("()=>({ bank: BANK_CLASS, ifcq: !!QUESTIONS[0].ifc, noun: classNoun(true), topics: classTopics().length === topicsIn(QUESTIONS).length })")
        chk("(4) out of the room his app is the academy's again: its own bank and words (%s)" % back, back["bank"] == "academy" and not back["ifcq"] and back["noun"] == "units", back)
        s1 = True
    except Exception as e:
        chk("(1)-(4) the Fire Code room ran to the end", False, repr(e)[:300])
        try: leave(A); leave(B)
        except Exception: pass

    # ===================== (5): an academy room, as before =====================
    print("\n-- an academy room: two classmates, exactly as before", flush=True)
    cctx, C = device(br, "kim", init_academy(kim, KIMCODE))
    pages3 = {"ifc": A, "alex": B, "kim": C}
    try:
        acad_unit = B.evaluate(SMALL_UNIT)
        before_b = B.evaluate(STORE); before_c = C.evaluate(STORE)
        w0 = len(writes())
        code2 = host_room(B, acad_unit)
        doc2 = dump()["vrooms"].get(code2) or {}
        chk("(5) an academy room is the document it always was: no class on it (%s)" % {k: doc2.get(k) for k in ("cls", "hostCode", "units")},
            bool(code2) and "cls" not in doc2 and doc2.get("hostCode") == ALEX, doc2)
        lt = B.evaluate(LOBBY_TEXT) or ""
        chk("(5) and its lobby names no class (%r)" % lt[:120], bool(lt) and " room" not in lt.replace("No units", ""), lt)
        C.evaluate("(c)=>joinVirtualRoomLobby(c)", code2)
        j2 = wait_for(C, "()=>(document.querySelector('#stage .screen-vroom-lobby') && vroomCode) ? ((typeof BANK_CLASS !== 'undefined') ? BANK_CLASS : 'academy') : null", tries=40)
        chk("(5) the second classmate joins it, on the academy's bank (%s)" % j2, j2 == "academy", j2)
        wait_for(B, "()=>document.querySelectorAll('#stage .vroom-row').length >= 2", tries=20)
        ws_mid = len(writes()); rd_mid = reads_of(pages3, code2)
        COST["ac_setup"] = room_cost(code2, w0, {d: 0 for d in pages3}, pages3)
        ready_both([B, C])
        orders, ins = play_match([B, C], [0, 1])
        ob, oc = orders
        chk("(5) both play the same academy questions in the same order (%d, %s)" % (len((ob or {}).get("qs") or []), (ob or {}).get("topics")),
            bool(ob) and bool(oc) and ob["qs"] == oc["qs"] and len(ob["qs"]) == 5 and not ob["ifc"] and ob["topics"] == [acad_unit], {"b": ob, "c": oc})
        st_b, st_c = B.evaluate(STANDINGS), C.evaluate(STANDINGS)
        chk("(5) both finish and rank the room the same: %s" % st_b, all(ins) and bool(st_b) and st_b == st_c and len(st_b) == 2 and st_b[0][0] == ALEX, {"b": st_b, "c": st_c})
        COST["ac_match"] = room_cost(code2, ws_mid, rd_mid, pages3)
        after_b = wait_for(B, "(m)=>{ const s = (%s)(); return s.vrMatches > m ? s : null; }" % STORE, before_b["vrMatches"], tries=20) or B.evaluate(STORE)
        after_c = wait_for(C, "(m)=>{ const s = (%s)(); return s.vrMatches > m ? s : null; }" % STORE, before_c["vrMatches"], tries=20) or C.evaluate(STORE)
        chk("(5) each gets the match and the run as ever: XP %d -> %d and %d -> %d, stats +%d and +%d, vrMatches +%d and +%d"
            % (before_b["points"], after_b["points"], before_c["points"], after_c["points"], after_b["stats"] - before_b["stats"], after_c["stats"] - before_c["stats"],
               after_b["vrMatches"] - before_b["vrMatches"], after_c["vrMatches"] - before_c["vrMatches"]),
            after_b["points"] > before_b["points"] and after_c["points"] > before_c["points"] and after_b["vrMatches"] == before_b["vrMatches"] + 1
            and after_c["vrMatches"] == before_c["vrMatches"] + 1 and after_b["answered"] == before_b["answered"] + 5 and after_c["answered"] == before_c["answered"] + 5
            and any(k.startswith(acad_unit + "|") for k in after_b["statKeys"]), {"b": {k: v for k, v in after_b.items() if k != "statKeys"}})
        leave(B); leave(C)
    except Exception as e:
        chk("(5) the academy room ran to the end", False, repr(e)[:300])
        try: leave(B); leave(C)
        except Exception: pass

    # ===================== (5b): the owner in Fire Code joins an academy room =====================
    print("\n-- the other way round: the owner, in Fire Code, joins a classmate's academy room", flush=True)
    try:
        acad_unit = B.evaluate(SMALL_UNIT)
        before_a = A.evaluate(STORE)
        code3 = host_room(B, acad_unit)
        B.evaluate("(c)=>inviteFriendToLobby(%s, c)" % json.dumps(OWNER), code3)
        ban = wait_for(A, """(c)=>{ const x = incomingLobbyInvites().find(i => i.code === c); if(!x) return null; checkLobbyInvites();
            const b = document.getElementById('lobby-invite'); return { cls: x.cls, banner: b ? b.innerText : '' }; }""", code3, tries=30)
        chk("(5b) the owner, in Fire Code, is invited to a 'Police Academy room' (%s)" % ban, bool(ban) and ban["cls"] == "academy" and "Police Academy room" in ban["banner"], ban)
        A.evaluate("(c)=>joinVirtualRoomLobby(c)", code3)
        j3 = wait_for(A, "()=>(document.querySelector('#stage .screen-vroom-lobby') && vroomCode) ? { bank: BANK_CLASS, ifcq: !!QUESTIONS[0].ifc, noun: classNoun(true) } : null", tries=40)
        chk("(5b) he joins, and Fire Code holds the academy's bank and says 'units' for the room (%s)" % j3, bool(j3) and j3["bank"] == "academy" and not j3["ifcq"] and j3["noun"] == "units", j3)
        lt = A.evaluate(LOBBY_TEXT) or ""
        chk("(5b) his lobby says it is a Police Academy room and what counts for him (%r)" % lt[:200], "Police Academy room" in lt and "No XP" in lt, lt)
        wait_for(B, "()=>document.querySelectorAll('#stage .vroom-row').length >= 2", tries=20)
        ready_both([B, A])
        orders, ins = play_match([B, A], [1, 0])
        ob, oa = orders
        chk("(5b) both play the same academy questions in the same order", bool(ob) and bool(oa) and ob["qs"] == oa["qs"] and not oa["ifc"] and oa["bank"] == "academy", {"b": ob, "a": oa})
        st_b, st_a = B.evaluate(STANDINGS), A.evaluate(STANDINGS)
        chk("(5b) both finish and rank it the same, the owner first: %s" % st_a, all(ins) and bool(st_a) and st_a == st_b and st_a[0][0] == OWNER, {"a": st_a, "b": st_b})
        after_a = wait_for(A, "(m)=>{ const s = (%s)(); return s.vrMatches > m ? s : null; }" % STORE, before_a["vrMatches"], tries=20) or A.evaluate(STORE)
        acad_keys = [k for k in after_a["statKeys"] if k.startswith(acad_unit + "|")]
        chk("(5b) Fire Code gains the match (vrMatches %d -> %d, a win %d -> %d) and nothing of the academy's questions: XP %d -> %d, stats %d -> %d (academy keys %d)"
            % (before_a["vrMatches"], after_a["vrMatches"], before_a["vrWins"], after_a["vrWins"], before_a["points"], after_a["points"], before_a["stats"], after_a["stats"], len(acad_keys)),
            after_a["vrMatches"] == before_a["vrMatches"] + 1 and after_a["vrWins"] == before_a["vrWins"] + 1 and after_a["points"] == before_a["points"]
            and after_a["stats"] == before_a["stats"] and not acad_keys and after_a["answered"] == before_a["answered"] and after_a["study"] == before_a["study"]
            and after_a["cls"] == "ifc", {k: v for k, v in after_a.items() if k != "statKeys"})
        leave(A); leave(B)
        back = A.evaluate("()=>({ bank: BANK_CLASS, ifcq: !!QUESTIONS[0].ifc, noun: classNoun(true) })")
        chk("(5b) out of the room Fire Code is itself again (%s)" % back, back["bank"] == "ifc" and back["ifcq"] and back["noun"] == "chapters", back)
    except Exception as e:
        chk("(5b) the owner's visit to an academy room ran to the end", False, repr(e)[:300])

    # ===================== (6)-(8) =====================
    print("\n-- what Fire Code wrote, what the rooms hold, page errors, cost", flush=True)
    A.wait_for_timeout(1500)
    allw = writes()
    fc = sorted(set(w["path"] for w in allw if w["dev"] == "ifc"))
    bad = [p for p in fc if not (p.startswith("progress/" + CODE + "__ifc") or p.startswith("vrooms/"))]
    chk("(6) nothing from Fire Code to progress/%s or the leaderboard - only progress/%s__ifc and `vrooms` (%d paths; foreign %s)" % (CODE, CODE, len(fc), bad),
        not bad and any(p.startswith("vrooms/") for p in fc), fc)
    lim = A.evaluate("""async (code)=>{ if(typeof vroomDb !== 'function' || !vroomDb()) return null; const tryit = p => Promise.resolve().then(p).then(() => 'wrote', () => 'refused');
        return { progress: await tryit(() => vroomDb().collection('progress').doc(code).set({ x: 1 }, { merge: true })),
                 board: await tryit(() => vroomDb().collection('leaderboard').doc('%s').update({ x: 1 })) }; }""".replace("'%s'", json.dumps(OWNER)), CODE)
    chk("(6) the room's handle in Fire Code refuses the academy's progress and the board (%s)" % lim, bool(lim) and lim["progress"] == lim["board"] == "refused", lim)
    cl = dump()
    leak = [k for k, v in cl["vrooms"].items() if any(c in json.dumps(v) or c in k for c in CODES)]
    chk("(7) no sync code in any `vrooms` document (%d documents; %s)" % (len(cl["vrooms"]), leak), not leak, leak)
    for dev, es in ERRS.items():
        chk("(8) no page errors on %s" % dev, not es, es[:3])
    fm, am = COST.get("fc_match"), COST.get("ac_match")
    print("COST  room document, per match (ready to everyone in): Fire Code room %s ; academy room %s" % (fm, am), flush=True)
    print("COST  room document, setting up (host, units, invite, join): Fire Code room %s ; academy room %s" % (COST.get("fc_setup"), COST.get("ac_setup")), flush=True)
    chk("(8) a Fire Code room costs the same order as an academy room: writes %s vs %s, reads %s vs %s" % ((fm or {}).get("writes"), (am or {}).get("writes"), (fm or {}).get("reads"), (am or {}).get("reads")),
        bool(fm) and bool(am) and fm["writes"] <= am["writes"] * 1.5 + 4 and fm["reads"] <= am["reads"] * 1.5 + 6, {"fc": fm, "ac": am})
    for c in (actx, bctx, cctx): c.close()
    br.close()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
