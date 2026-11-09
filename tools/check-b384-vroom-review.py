"""Build 384 review of the Virtual Room. Madison: "your account friends, that's your account friends for any class. However if one
of your friends isn't enrolled into the class of whatever virtual room you are in, they won't appear on the invite list or maybe
their invite button is greyed out and when you try to invite it says this player is not enrolled" / "do a check on the virtual room
games, ensure they work wonderfully and if they need any fixes, updates, improvements do them, I've barely been able to use them."

SEVERAL DEVICES, ONE CLOUD (the check-b384-vrifc arrangement): each device is its own browser context with its own storage and
class, and they share a Firestore stand-in served over HTTP - documents, dotted updates, FieldValue / FieldPath, transactions,
batches, document and collection listeners by long poll. New here: a device's writes can be held back (/slow) the way a slow
connection holds them (CLOUD.slow), so "the screen waited for the server" can be seen. Accounts and codes are made up.
 (A) the presence beat says which classes each account is in (`c`, with its name and character), from an academy device, a Fire
     Code-only device and the owner's Fire Code device - in the beat it already writes;
 (B) the invite list in a Fire Code room greys the academy-only friend and a tap says he is not enrolled (no invite sent); the
     friend in both classes is invited; in an academy room the Fire Code-only friend is greyed the same way;
 (C) an account not in a room's class is turned away at the join, and the open rooms list does not offer it the room;
 (D) the host leaves the lobby: whoever is host now has Invite friends and Open to class, and the open rooms list names them;
 (E) the app died mid-race and came back on the same device: it is let back in (a second device of the account is still
     refused), and the finale of the race it left does not wait on its fresh entry;
 (F) somebody who quits mid-race is announced as leaving the match, not the lobby;
 (G) joining a room from another room's lobby takes this device out of the first room;
 (H) the wait card after your race and Return to lobby do not wait for the server's answer;
 (I) Battle with fewer than fifty questions picked runs the fifty every device plays (it was called over at the room's count),
     and its winners' cutscene stands on a floor, not Tug of War's rope;
 (J) Tug of War's results put your side first in the standings (the podium, 384 r8), as the rope does, and every figure on the
     rope card is inside the field;
 (K) Nova invited while the server is slow still readies (his driver outlived a first answer from before his entry);
 (L) the lobby line for a Fire Code room, with the switch on (Open lobby), names Fire Code, and a Battle lobby says the number of
     questions it runs;
 (M) the invite sheet in Fire Code asks for class sharing only when the account has it off;
 (N) no sync code in any `vrooms` document; no page errors;
 (O) (384, Virtual Room round 2: "Just ensure it makes sense and ensure it works") EVERY DOOR: an invite to a Fire Code room that
     reaches the academy-only account anyway (as an older build would send it) is turned away from its banner's Join and from the
     Inbox's Join, as (C) turns away a join by code and the open rooms list; an account in both classes joins an academy room from
     Fire Code's page, as (B) has one join a Fire Code room from the academy's.
Run:  python3 tools/check-b384-vroom-review.py     (--against OLD/index.html must FAIL)    ONLY=B,C to run some sections"""
import copy, http.server, json, os, re, socket, sys, threading, time
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
INDEX_PATH = os.path.join(g["ROOT"], "index.html")
OLD_BUILD = None
if "--against" in sys.argv:
    INDEX_PATH = sys.argv[sys.argv.index("--against") + 1]
    OLD_BUILD = re.search(r'const APP_BUILD = "([^"]+)"', open(INDEX_PATH, encoding="utf-8").read()).group(1)
ONLY = set(x.strip().upper() for x in os.environ.get("ONLY", "").split(",") if x.strip())
def want(s): return not ONLY or s in ONLY
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else ("  -> " + str(info)[:600]), flush=True)

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
        self.cv = threading.Condition(); self.data = copy.deepcopy(seed)
        for c in ("progress", "leaderboard", "vrooms"): self.data.setdefault(c, {})
        self.log = []; self.writes = []; self.slow = {}
    @property
    def v(self): return len(self.log)
    def apply(self, dev, o):
        c, i, op = o["c"], o["id"], o["op"]
        col = self.data.setdefault(c, {})
        if op == "set":
            if o.get("merge"): cur = copy.deepcopy(col.get(i) or {}); merge_into(cur, o.get("v") or {})
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
        self.writes.append({"dev": dev, "op": op, "path": c + "/" + i, "at": now_ms()}); self.log.append((c, i))
    def handle(self, op, b):
        # a slow connection: this device's writes reach the server late (outside the lock - the others carry on)
        if op in ("set", "update", "delete", "commit") and self.slow.get(b.get("dev")): time.sleep(self.slow[b.get("dev")])
        with self.cv:
            if op == "get":
                d = self.data.get(b["c"], {}).get(b["id"]); return {"exists": d is not None, "data": d, "v": self.v}
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
                for n in range(since, self.v): latest[self.log[n]] = n + 1
                return {"v": self.v, "changed": [[c, i, self.data.get(c, {}).get(i) is not None, self.data.get(c, {}).get(i), v] for (c, i), v in latest.items()]}
            return {"error": "unknown op " + op}
CLOUD = None
INDEX_BODY = None
MIME = {".js": "application/javascript", ".json": "application/json", ".html": "text/html; charset=utf-8", ".css": "text/css", ".png": "image/png",
        ".jpg": "image/jpeg", ".svg": "image/svg+xml", ".pdf": "application/pdf", ".webp": "image/webp", ".mp3": "audio/mpeg", ".woff2": "font/woff2"}
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        p = self.path.split("?")[0]
        if p in ("/", "/index.html"): b, ct = INDEX_BODY, MIME[".html"]
        elif p == "/version.json" and OLD_BUILD: b, ct = json.dumps({"build": OLD_BUILD, "force": False, "frameId": ""}).encode(), MIME[".json"]
        else:
            f = os.path.realpath(os.path.join(g["ROOT"], p.lstrip("/")))
            if not f.startswith(os.path.realpath(g["ROOT"]) + os.sep) or not os.path.isfile(f):
                self.send_response(404); self.send_header("Content-Length", "0"); self.end_headers(); return
            b, ct = open(f, "rb").read(), MIME.get(os.path.splitext(f)[1].lower(), "application/octet-stream")
        self.send_response(200); self.send_header("Content-Type", ct); self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(b)
    def _send(self, code, obj=None):
        b = json.dumps(obj).encode() if obj is not None else b""
        self.send_response(code); self.send_header("Access-Control-Allow-Origin", "*"); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b))); self.end_headers()
        if b: self.wfile.write(b)
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
        def handle_error(self, request, client_address): pass
    srv = Srv(("127.0.0.1", port), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, "http://127.0.0.1:%d" % port
# the client each page gets as window.firebase (check-b384-vrifc's, unchanged)
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
  const applyCol = (s, e) => { const [c, id, ex, data, v] = e; if(v <= s.v) return 0;
    const was = s.map.has(id), now = ex && match(data, s.f);
    if(now){ s.map.set(id, data); return 1; } if(was){ s.map.delete(id); return 1; } return 0; };
  const deliverCol = s => { const docs = [...s.map.entries()].map(([id, d]) => dsnap(s.c, id, true, d)); try{ s.cb(qsnap(docs)); }catch(err){ later(err); } };
  function startPoll(){
    if(polling) return; polling = true;
    (async () => { for(;;){
      try{
        const r = await call('poll', { since: ver }); ver = r.v;
        r.changed.forEach(e => {
          const [c, id, ex, data, v] = e, k = c + '/' + id;
          const subs = (docSubs[k] || []).slice();
          if(subs.length && v > (lastV[k] || 0)){ lastV[k] = v; subs.forEach(cb => { try{ cb(dsnap(c, id, ex, data)); }catch(err){ later(err); } }); }
          colSubs.slice().forEach(s => { if(s.c !== c) return; if(!s.ready){ s.pending.push(e); return; } if(applyCol(s, e)) deliverCol(s); });
        });
      }catch(err){ await new Promise(res => setTimeout(res, 300)); }
    } })();
  }
  function doc(c, id){
    const k = c + '/' + id;
    return { id, path: k, __c: c,
      get: () => call('get', { c, id }).then(r => dsnap(c, id, r.exists, r.data)),
      set: (v, o) => call('set', { c, id, v: enc(v), merge: !!(o && o.merge) }).then(() => undefined),
      update: function(){ const a = [...arguments];
        const body = (a.length === 1 && a[0] && typeof a[0] === 'object' && !(a[0] instanceof FieldPath)) ? { fields: enc(a[0]) } : { pairs: enc(a) };
        return call('update', Object.assign({ c, id }, body)).then(() => undefined); },
      delete: () => call('delete', { c, id }).then(() => undefined),
      onSnapshot: function(){
        const next = [...arguments].find(x => typeof x === 'function');
        let alive = true; const cb = s => { if(alive) next(s); };
        (docSubs[k] = docSubs[k] || []).push(cb); startPoll();
        call('get', { c, id }).then(r => { if(!alive || (lastV[k] || 0) > r.v) return; lastV[k] = r.v; try{ next(dsnap(c, id, r.exists, r.data)); }catch(err){ later(err); } }).catch(() => {});
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
      get: () => call('query', { c, f: enc(f) }).then(r => qsnap(r.docs.map(([id, d]) => dsnap(c, id, true, d)))),
      add: v => { const d = doc(c, 'auto' + Math.random().toString(36).slice(2)); return d.set(v).then(() => d); },
      onSnapshot: function(){
        const next = [...arguments].find(x => typeof x === 'function');
        const s = { c, f, cb: x => { if(s.alive) next(x); }, map: new Map(), ready: false, pending: [], v: 0, alive: true };
        colSubs.push(s); startPoll();
        call('query', { c, f: enc(f) }).then(r => { if(!s.alive) return; r.docs.forEach(([id, d]) => s.map.set(id, d)); s.v = r.v; s.ready = true;
          const pend = s.pending; s.pending = []; pend.forEach(e => applyCol(s, e)); deliverCol(s); }).catch(() => {});
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
      tx.get = r => call('get', { c: r.__c, id: r.id }).then(x => dsnap(r.__c, r.id, x.exists, x.data));
      return Promise.resolve().then(() => fn(tx)).then(res => call('commit', { ops }).then(() => res)); },
    batch: () => { const ops = []; const b = writer(ops); b.commit = () => call('commit', { ops }).then(() => undefined); return b; } };
  const fs = () => db;
  fs.FieldValue = { delete: () => new FV('delete'), serverTimestamp: () => new FV('ts'), arrayUnion: (...x) => new FV('arrayUnion', x),
                    arrayRemove: (...x) => new FV('arrayRemove', x), increment: n => new FV('increment', n) };
  fs.FieldPath = FieldPath;
  window.firebase = { apps: [], initializeApp(){ this.apps.push({}); }, firestore: fs };
})()"""

# ------------------------------------------------------------------ accounts (all made up)
INDEX_BODY = g["INSET_RE"].sub(lambda m: {"top": "59px", "right": "0px", "bottom": "34px", "left": "0px"}[m.group(1)],
                               open(INDEX_PATH, encoding="utf-8").read()).encode("utf-8")
WEEK = g["week_key_now"](); T0 = now_ms()
OWNER, ALEX, KIM, DEV = "xph5b57jbp5a", "tst384rvax01", "tst384rvkm02", "tst384rvdv03"
CODE = {OWNER: "TEST-3861", ALEX: "TEST-3862", KIM: "TEST-3863", DEV: "TEST-3864"}
NAMES = {OWNER: "Maddox", ALEX: "Alexis", KIM: "Kimber", DEV: "Devon"}
FCODE = {OWNER: "QRW-384", ALEX: "AXW-384", KIM: "KMW-384", DEV: "DVW-384"}
AVATAR = {OWNER: "ninja", ALEX: "ghost", KIM: "grizzly", DEV: "ninja"}
CLASSES = {OWNER: ["academy", "ifc"], ALEX: None, KIM: ["academy", "ifc"], DEV: ["ifc"]}   # Alexis: an account from before 384 (academy)
FRIENDS = {OWNER: [ALEX, KIM, DEV], ALEX: [OWNER, KIM, DEV], KIM: [OWNER, ALEX], DEV: [OWNER, ALEX]}
def academy_store(pub):
    d = json.loads(g["SEED"].replace("__WEEK__", WEEK))
    d.update({"publicId": pub, "firstName": NAMES[pub], "novaMet": 99, "friendCode": FCODE[pub], "friendsIn": list(FRIENDS[pub]), "friendsOut": [],
              "friendsDeclined": [], "chats": [], "leaderboardOptIn": True, "lastModified": T0 - 3600000, "avatarChar": AVATAR[pub],
              "seenClassTip": True, "badgeBandsVersion": 4})
    if CLASSES[pub] is not None: d["classes"] = list(CLASSES[pub])
    d.setdefault("novaHeard", {})["@recap"] = 99991231
    return d
def ifc_store(pub):
    ac = academy_store(pub)
    d = {k: ac[k] for k in ["firstName", "avatarChar", "publicId", "onboardingComplete", "tourRev", "novaMet", "novaHeard", "weekKey"] if k in ac}
    d.update({k: v for k, v in ac.items() if k.startswith("seen")})
    d.update({"lifetime": dict(ac["lifetime"], points=4321, correct=777), "leaderboardOptIn": False, "leaderboardOptInChanged": True,
              "lastModified": T0 - 1800000, "badgeBandsVersion": 4})
    return d
def row(pub):
    return {"firstName": NAMES[pub], "avatarChar": AVATAR[pub], "level": 20, "badges": 3, "mystery": 0, "hundos": 4, "correct": 120,
            "week": WEEK, "weekPoints": 50, "fcode": FCODE[pub], "freq": [], "facc": list(FRIENDS[pub]), "lastModified": T0 - 60000}
SEED_CLOUD = {"progress": {CODE[p]: academy_store(p) for p in CODE},
              # Devon is in Fire Code alone: the academy's board has no row for him (pushLeaderboardRow writes none)
              "leaderboard": {p: row(p) for p in (OWNER, ALEX, KIM)},
              "vrooms": {"presence-v1": {"kind": "presence", "p": {}, "a": {}}}}
CLOUD = Cloud(SEED_CLOUD)
csrv, cloud_url = serve_cloud()
SEEN = ("['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card',"
        "'class26e.getstarted','class26e.frame.ok','class26e.penal55124.seen','class26e.penal124256.seen','class26e.penal256578.seen','class26e.a2hs.tip','class26e.newclass.ifc']"
        ".forEach(k=>localStorage.setItem(k, k==='class26e.frame.ok'?'go-live-1':k==='class26e.intro.seen'?'99':'1'));")
def init_academy(pub):
    return ("(()=>{ if(sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); " + SEEN +
            "localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode', '%s'); localStorage.removeItem('class26e.activeclass'); })()"
            % (json.dumps(json.dumps(academy_store(pub))), CODE[pub]))
def init_ifc(pub):
    s = "(()=>{ if(sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); " + SEEN
    s += "localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode', '%s');" % (json.dumps(json.dumps(academy_store(pub))), CODE[pub])
    s += "localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done');"
    s += "['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted','class26e.ifc.a2hs.tip'].forEach(k=>localStorage.setItem(k,k==='class26e.ifc.intro.seen'?'99':'1'));"
    s += "localStorage.setItem('class26e.activeclass','ifc'); localStorage.setItem('class26e.ifc.drill.v1', %s);" % json.dumps(json.dumps(ifc_store(pub)))
    return s + " })()"

ERRS = {}
def boot(pg, dev):
    pg.goto(cloud_url + "/index.html"); pg.wait_for_timeout(3800)
    pg.evaluate("document.getElementById('splashscreen')?.remove()")
    for _ in range(60):
        if not pg.evaluate("()=>document.body.classList.contains('cutscene-focus') || document.body.classList.contains('cutscene-return') || (typeof cutsceneFocusActive === 'function' && cutsceneFocusActive())"): break
        pg.evaluate("()=>{ document.querySelectorAll('.unlock-card .next, .rs-spot .next, .cutscene-skip, .ru-skip').forEach(b=>{ try{ b.click(); }catch(e){} }); }")
        pg.wait_for_timeout(500)
def device(br, dev, pub, cls="academy"):
    ctx = br.new_context(viewport={"width": 440, "height": 956}, has_touch=True)
    ctx.add_init_script("window.__cloudUrl = %s; window.__dev = %s;" % (json.dumps(cloud_url), json.dumps(dev)))
    ctx.add_init_script(CLIENT); ctx.add_init_script(g["STANDALONE"])
    ctx.add_init_script(init_ifc(pub) if cls == "ifc" else init_academy(pub))
    pg = ctx.new_page(); ERRS[dev] = []
    pg.on("pageerror", lambda e, d=dev: ERRS[d].append(str(e)[:240]))
    boot(pg, dev)
    try: ctx.new_cdp_session(pg).send("Page.setWebLifecycleState", {"state": "active"})
    except Exception: pass
    return ctx, pg
def wait_for(pg, js, arg=None, tries=40, step=400):
    v = None
    for _ in range(tries):
        try: v = pg.evaluate(js, arg) if arg is not None else pg.evaluate(js)
        except Exception: v = None
        if v: return v
        pg.wait_for_timeout(step)
    return v
def dump(): return CLOUD.data
def room(code): return copy.deepcopy(CLOUD.data["vrooms"].get(code) or {})
READY = "body:has(#stage > .screen-vroom-lobby) #stage > .vroom-setup-bar > .vroom-readyup-btn"
SMALL_UNIT = """()=>{ const t = topicsIn(QUESTIONS).map(u => [u, unitQuestionCount(u)]).filter(x => x[1] >= 6).sort((a, b) => a[1] - b[1]);
  return t.length ? t[0][0] : null; }"""
LOBBY = """()=>{ const s = document.querySelector('#stage .screen-vroom-lobby'); if(!s) return null;
  return { host: !!vroomIsHost, invite: !!s.querySelector('.vroom-invite-btn'), open: !!s.querySelector('.vroom-open-switch'),
           settings: !!s.querySelector('.vroom-settings-btn'), openLine: (s.querySelector('.vroom-open-line') || {}).textContent || '',
           summary: (s.querySelector('.vroom-test-summary') || {}).innerText || '' }; }"""
TOASTS = "()=>[...document.querySelectorAll('.toast')].map(t=>t.innerText).join(' / ')"
def host_room(pg, unit, game="race", n=5):
    pg.evaluate("()=>{ if(typeof vroomCode !== 'undefined' && vroomCode){ try{ leaveVirtualRoom(); }catch(e){} } cfg.mode = 'vroom'; showVirtualRoomChoice(); }"); pg.wait_for_timeout(700)
    pg.click("#stage .vrc-card-host")
    code = wait_for(pg, "()=>(typeof vroomCode === 'string' && vroomCode && document.querySelector('#stage .screen-vroom-lobby')) ? vroomCode : null", tries=30)
    if not code: return None
    pg.evaluate("(a)=>vroomDb().collection('vrooms').doc(vroomCode).update({ units: [a.unit], game: a.game, count: a.n, versions: {} })", {"unit": unit, "n": n, "game": game})
    wait_for(pg, "(u)=>{ const s = document.querySelector('#stage .vroom-test-summary'); return !!(s && s.innerText.indexOf(u) >= 0); }", unit, tries=20)
    return code
def join(pg, code):
    pg.evaluate("(c)=>joinVirtualRoomLobby(c)", code)
    return wait_for(pg, "(c)=>!!(document.querySelector('#stage .screen-vroom-lobby') && vroomCode === c)", code, tries=30)
def ready(pages):
    for pg in pages: pg.wait_for_selector(READY + ":not([disabled])", state="visible", timeout=25000)
    for pg in pages: pg.click(READY); pg.wait_for_timeout(250)
def leave(pg):
    pg.evaluate("()=>{ try{ document.getElementById('vroom-race-cut')?.remove(); document.getElementById('vroom-cutscene')?.remove(); document.getElementById('vroom-prep')?.remove(); if(vroomCode) leaveVirtualRoom(); testInProgress = false; showHome(); }catch(e){} }")
    pg.wait_for_timeout(700)
# (384 r5) a Tug of War or Battle is not called over in its first five minutes, and a Battle side has 300 health a member: the
# matches (I) and (J) play run in seconds, so they set the app's own test hook for them (as check-vroom does); the five-minute
# floor has its own gate (check-b384-matchlength). Off again after, for the sections that follow.
def fast(pages, on):
    for pg in pages: pg.evaluate("(on)=>{ window.__vroomFast = on; }", bool(on))
RACE_UP = "()=>!!document.querySelector('.qpanel .choice') && !document.getElementById('vroom-reveal-overlay') && typeof inVirtualRoom !== 'undefined' && inVirtualRoom"
ANSWER_ALL = """async (n)=>{ const W = ms => new Promise(r => setTimeout(r, ms)); let k = 0;
  while(typeof inVirtualRoom !== 'undefined' && inVirtualRoom && pos < order.length && (n == null || k < n)){
    const qi = order[pos]; choose(optionOrder(qi).indexOf(QUESTIONS[qi].answer)); await W(220); advance(); await W(220); k++; }
  return k; }"""
def team_answer(pg, right):
    return pg.evaluate("""(right)=>{ const sel = '.screen-tug .choices:not(.is-arming) .choice:not([disabled]):not(.locked), .screen-battle .choices .choice:not([disabled]):not(.locked)';
        const cs = [...document.querySelectorAll(sel)]; if(!cs.length) return 0;
        if(typeof battleFrozenUntil !== 'undefined' && battleFrozenUntil > Date.now()) return 0;
        const isT = !!document.querySelector('.screen-tug');
        const item = isT ? QUESTIONS[tugPool[tugMyPos % tugPool.length]] : QUESTIONS[battlePool[battlePos]];
        const r = item.answer; cs[right ? r : (r + 1) % cs.length].click(); return 1; }""", right)

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    actx, A = device(br, "alex", ALEX)                   # academy only (an account from before 384)
    kctx, K = device(br, "kim", KIM)                     # in both, on the academy's page
    octx, O = device(br, "owner", OWNER, "ifc")          # in both, on Fire Code's page
    unit_a = A.evaluate(SMALL_UNIT); unit_f = O.evaluate(SMALL_UNIT)

    # ===================== (A) the presence beat says which classes =====================
    if want("A") or want("B"):
        print("\n-- (A) the classes each account is in, on the presence beat", flush=True)
        for pg in (A, K, O): pg.evaluate("()=>{ try{ sendHeartbeat(true); }catch(e){} }")
        dctx, D = device(br, "devon", DEV, "ifc")         # in Fire Code alone
        D.evaluate("()=>{ try{ sendHeartbeat(true); }catch(e){} }")
        cmap = None
        for _ in range(30):
            cmap = (dump()["vrooms"].get("presence-v1") or {}).get("c") or {}
            if all(p in cmap for p in (ALEX, KIM, OWNER, DEV)): break
            A.wait_for_timeout(400)
        ck = lambda p: ((cmap.get(p) or {}).get("k") if isinstance(cmap.get(p), dict) else cmap.get(p))
        chk("(A) each device's beat carries its account's classes: academy-only %r, both %r (academy page), owner %r (Fire Code page), Fire Code-only %r"
            % (ck(ALEX), ck(KIM), ck(OWNER), ck(DEV)),
            ck(ALEX) == "academy" and ck(KIM) == "academy,ifc" and ck(OWNER) == "academy,ifc" and ck(DEV) == "ifc", cmap)
        chk("(A) with the account's own name and character, so a friend with no board row has one (%s)" % cmap.get(DEV),
            isinstance(cmap.get(DEV), dict) and cmap[DEV].get("n") == NAMES[DEV] and cmap[DEV].get("v") == AVATAR[DEV], cmap.get(DEV))
        pw_writes = [w for w in CLOUD.writes if w["path"] == "vrooms/presence-v1"]
        chk("(A) and it is in the beat each device already writes - no presence write of its own (%d presence writes from 4 devices)" % len(pw_writes),
            len(pw_writes) <= 4 * 3, pw_writes[-8:])
        dctx.close()

    # ===================== (B) the invite list follows the room's class =====================
    if want("B"):
        print("\n-- (B) the invite list in a Fire Code room and in an academy room", flush=True)
        try:
            code_f = host_room(O, unit_f, "race", 5)
            chk("(B) the owner hosts a Fire Code room from Fire Code (%s)" % (room(code_f).get("cls"),), room(code_f).get("cls") == "ifc", room(code_f))
            O.click("#stage .vroom-invite-btn")
            sheet = wait_for(O, """(p)=>{ const rows = [...document.querySelectorAll('.invite-overlay .invite-list:not(.invite-list-nova) .friend-row')];
                if(rows.length < 3) return null;
                const out = rows.map(r => { const b = r.querySelector('.friend-act'); return { name: (r.querySelector('.friend-row-name')||{}).textContent,
                  pub: b && b.dataset.invitePub, grey: !!(b && b.classList.contains('is-unenrolled')), op: b ? getComputedStyle(b).opacity : null,
                  disabled: !!(b && b.disabled) }; });
                return out.find(x => x.pub === p.alex && x.grey) ? out : null; }""", {"alex": ALEX}, tries=25) or []
            by = {x.get("pub"): x for x in sheet}
            chk("(B) in the Fire Code room the academy-only friend's Invite is greyed and still tappable (%s)" % by.get(ALEX),
                bool(by.get(ALEX)) and by[ALEX]["grey"] and float(by[ALEX]["op"] or 1) < 0.6 and not by[ALEX]["disabled"], sheet)
            chk("(B) the friend in both classes and the one in Fire Code alone are invitable (%s / %s)" % (by.get(KIM), by.get(DEV)),
                bool(by.get(KIM)) and not by[KIM]["grey"] and bool(by.get(DEV)) and not by[DEV]["grey"], sheet)
            chk("(B) the greyed friend sorts below the invitable ones", bool(sheet) and sheet[-1].get("pub") == ALEX, [x.get("pub") for x in sheet])
            chk("(B) the friend in Fire Code alone, who has no board row, is listed by name (%r)" % (by.get(DEV) or {}).get("name"),
                (by.get(DEV) or {}).get("name") == NAMES[DEV], by.get(DEV))
            O.evaluate("(p)=>document.querySelector('.invite-overlay .friend-act[data-invite-pub=\"' + p + '\"]').click()", ALEX)
            O.wait_for_timeout(700)
            t = O.evaluate(TOASTS)
            inv_a = ((dump()["vrooms"].get("inbox-" + ALEX) or {}).get("msgs") or {}).get(OWNER)
            chk("(B) tapping it says the friend is not enrolled in Fire Code, by name, and sends nothing (%r)" % t,
                NAMES[ALEX] in t and "Fire Code" in t and "enrolled" in t and not inv_a, {"toast": t, "invite": inv_a})
            O.evaluate("(p)=>document.querySelector('.invite-overlay .friend-act[data-invite-pub=\"' + p + '\"]').click()", KIM)
            O.wait_for_timeout(900)
            inv_k = ((dump()["vrooms"].get("inbox-" + KIM) or {}).get("msgs") or {}).get(OWNER) or {}
            chk("(B) the friend in both classes is sent the invite, with the room's class (%s)" % {k: inv_k.get(k) for k in ("type", "code", "cls")},
                inv_k.get("type") == "vroom" and inv_k.get("code") == code_f and inv_k.get("cls") == "ifc", inv_k)
            O.evaluate("()=>document.querySelector('.invite-overlay .invite-close')?.click()")
            lk = join(K, code_f)
            chk("(B) and joins it from the academy's page", bool(lk) and K.evaluate("()=>BANK_CLASS") == "ifc", lk)
            # (round 8) the line follows the switch: off it says who can join ("Only people you invite"), so the class is only named
            # with the switch ON - turn it on, read the line, turn it back off (the room stays private for what follows)
            off_line = (O.evaluate(LOBBY) or {}).get("openLine") or ""
            O.evaluate("()=>document.querySelector('#stage .screen-vroom-lobby .vroom-open-switch').click()")
            on_doc = wait_for(O, "()=>!!vroomIsOpen", tries=10, step=200)
            for _ in range(20):
                if room(code_f).get("open") is True: break
                O.wait_for_timeout(200)
            lo = O.evaluate(LOBBY) or {}
            on_line = lo.get("openLine") or ""
            O.evaluate("()=>{ const sw = document.querySelector('#stage .screen-vroom-lobby .vroom-open-switch'); if(sw && vroomIsOpen) sw.click(); }")
            O.wait_for_timeout(500)
            chk("(L) the Fire Code room's Open lobby line names Fire Code, not the academy's 26E (on %r; off %r; room open: %s)" % (on_line, off_line, room(code_f).get("open")),
                bool(on_doc) and on_line != off_line and "Fire Code" in on_line and "26E" not in on_line, lo)
            leave(K); leave(O)
            # an academy room: the Fire Code-only friend is the greyed one
            code_a = host_room(A, unit_a, "race", 5)
            A.click("#stage .vroom-invite-btn")
            sheet2 = wait_for(A, """(p)=>{ const b = document.querySelector('.invite-overlay .friend-act[data-invite-pub="' + p.dev + '"]');
                const o = document.querySelector('.invite-overlay .friend-act[data-invite-pub="' + p.owner + '"]');
                return (b && o && b.classList.contains('is-unenrolled')) ? { dev: true, owner: o.classList.contains('is-unenrolled') } : null; }""",
                {"dev": DEV, "owner": OWNER}, tries=25)
            chk("(B) in an academy room the Fire Code-only friend is the greyed one, the owner (in both) is not (%s)" % sheet2,
                bool(sheet2) and sheet2["dev"] and sheet2["owner"] is False, sheet2)
            A.evaluate("(p)=>document.querySelector('.invite-overlay .friend-act[data-invite-pub=\"' + p + '\"]').click()", DEV); A.wait_for_timeout(700)
            t2 = A.evaluate(TOASTS)
            chk("(B) and a tap says that friend is not enrolled in the Police Academy (%r)" % t2, "Police Academy" in t2 and "enrolled" in t2
                and not ((dump()["vrooms"].get("inbox-" + DEV) or {}).get("msgs") or {}).get(ALEX), t2)
            A.evaluate("()=>document.querySelector('.invite-overlay .invite-close')?.click()")
            leave(A)
        except Exception as e:
            chk("(B) the invite section ran to the end", False, repr(e)[:300])
            for pg in (A, K, O): leave(pg)

    # ===================== (C) a room is for its class =====================
    if want("C"):
        print("\n-- (C) an account not in the room's class is turned away", flush=True)
        try:
            code_f = host_room(O, unit_f, "race", 5)
            O.evaluate("()=>document.querySelector('#stage .vroom-open-switch').click()"); O.wait_for_timeout(800)
            r = A.evaluate("(c)=>joinVirtualRoomLobby(c)", code_f); A.wait_for_timeout(800)
            t = A.evaluate(TOASTS)
            chk("(C) the academy-only account cannot join the Fire Code room, and is told why (%r)" % t,
                r is False and ALEX not in (room(code_f).get("participants") or {}) and "Fire Code" in t and "enrolled" in t, {"r": r, "toast": t})
            leave(A)   # (an older build let her in; out again, so the list below is asked as an outsider)
            A.evaluate("()=>showRoomBrowser()")
            lst = wait_for(A, "()=>{ const l = document.querySelector('#stage .rooms-list'); if(!l || /Looking/.test(l.innerText)) return null; return [...l.querySelectorAll('.room-row')].length + '|' + l.innerText.slice(0, 120); }", tries=30)
            chk("(C) and the open rooms list does not offer it (%r)" % lst, bool(lst) and lst.startswith("0|"), lst)
            K.evaluate("()=>showRoomBrowser()")
            lk = wait_for(K, "()=>{ const l = document.querySelector('#stage .rooms-list'); if(!l || /Looking/.test(l.innerText)) return null; return [...l.querySelectorAll('.room-row')].length; }", tries=30)
            chk("(C) an account in both classes is offered it (%s rows)" % lk, lk == 1, lk)
            leave(O); A.evaluate("()=>showHome()"); K.evaluate("()=>showHome()")
        except Exception as e:
            chk("(C) ran to the end", False, repr(e)[:300]); leave(O)

    # ===================== (D) the host leaves the lobby =====================
    if want("D"):
        print("\n-- (D) the host leaves; the next one is host with everything a host has", flush=True)
        try:
            code = host_room(A, unit_a, "race", 5)
            A.evaluate("()=>document.querySelector('#stage .vroom-open-switch').click()"); A.wait_for_timeout(600)
            join(K, code); A.wait_for_timeout(1200)
            A.evaluate("()=>{ leaveVirtualRoom(); showHome(); }")
            lk = wait_for(K, "()=>{ const l = (%s)(); return (l && l.host) ? l : null; }" % LOBBY, tries=25)
            chk("(D) the promoted host has Invite friends and Open to class, not just Match settings (%s)" % lk,
                bool(lk) and lk["invite"] and lk["open"] and lk["settings"], lk)
            on = K.evaluate("()=>{ const s = document.querySelector('#stage .vroom-open-switch'); return s ? s.getAttribute('aria-checked') : null; }")
            chk("(D) and the switch shows the room as it is (open)", on == "true", on)
            O.evaluate("()=>showRoomBrowser()")
            nm = wait_for(O, "(c)=>{ const l = document.querySelector('#stage .rooms-list'); if(!l || /Looking/.test(l.innerText)) return null; const r = [...l.querySelectorAll('.room-row .friend-row-name')].map(x => x.textContent); return r.length ? r.join('|') : null; }", code, tries=30)
            chk("(D) the open rooms list names the room after who is host now (%r)" % nm, bool(nm) and NAMES[KIM] in nm and NAMES[ALEX] not in nm, nm)
            O.evaluate("()=>showHome()"); leave(K)
        except Exception as e:
            chk("(D) ran to the end", False, repr(e)[:300]); leave(K)

    # ===================== (E) the app died mid-race and came back =====================
    if want("E"):
        print("\n-- (E) back in after the app died; a second device still refused; the finale is not held", flush=True)
        try:
            code = host_room(A, unit_a, "race", 5)
            join(K, code); ready([A, K])
            for pg in (A, K): wait_for(pg, RACE_UP, tries=90, step=300)
            K.evaluate(ANSWER_ALL, 1)
            cdp = kctx.new_cdp_session(K); cdp.send("Page.setWebLifecycleState", {"state": "frozen"})
            # a second device of the same account (its own storage, so its own device id), while her entry is fresh
            x2ctx, X2 = device(br, "kim2", KIM)
            r2 = X2.evaluate("(c)=>joinVirtualRoomLobby(c)", code); X2.wait_for_timeout(900)
            t2 = X2.evaluate(TOASTS)
            chk("(E) a second device of the account is still refused while the first is in the room (%r)" % t2, r2 is False and "already" in t2, {"r": r2, "t": t2})
            x2ctx.close()
            # the same device, relaunched: a new page in the same context (its storage, its device id)
            K2 = kctx.new_page(); ERRS["kim-relaunch"] = []
            K2.on("pageerror", lambda e: ERRS["kim-relaunch"].append(str(e)[:240]))
            boot(K2, "kim")
            r3 = K2.evaluate("(c)=>joinVirtualRoomLobby(c)", code)
            lk = wait_for(K2, "(c)=>!!(document.querySelector('#stage .screen-vroom-lobby') && vroomCode === c)", code, tries=25)
            mid = K2.evaluate("()=>{ const b = document.querySelector('.vroom-readyup-btn'); return b ? { midmatch: b.classList.contains('is-midmatch'), disabled: b.disabled } : null; }")
            chk("(E) coming back on the same device after the app died lets her in (%s), to a lobby that says a match is on (%s)" % (r3, mid),
                r3 is True and bool(lk) and bool(mid) and mid["disabled"], {"r": r3, "toast": K2.evaluate(TOASTS)})
            t_fin = time.time()
            A.evaluate(ANSWER_ALL, None)
            allin = wait_for(A, "()=>!!document.querySelector('.vroom-waitcard.is-all-in')", tries=60, step=500)
            took = time.time() - t_fin
            chk("(E) the race she left does not wait on her fresh entry: the host is all in %.0fs after finishing (presence would take 150s)" % took,
                bool(allin) and took < 40, {"allin": allin, "racers": room(code).get("racers"), "kim": (room(code).get("participants") or {}).get(KIM)})
            K2.close()
            leave(A)
        except Exception as e:
            chk("(E) ran to the end", False, repr(e)[:300]); leave(A)
        # Kimber's device again for the sections after this one
        try: kctx.close()
        except Exception: pass
        kctx, K = device(br, "kim-b", KIM)

    # ===================== (F) quitting mid-race is leaving the match =====================
    if want("F"):
        print("\n-- (F) quitting mid-race is announced as leaving the match", flush=True)
        try:
            code = host_room(A, unit_a, "race", 5)
            join(K, code); ready([A, K])
            for pg in (A, K): wait_for(pg, RACE_UP, tries=90, step=300)
            K.evaluate("()=>{ document.getElementById('pausebtn').click(); }"); K.wait_for_timeout(400)
            K.evaluate("()=>document.getElementById('pause-quit').click()"); K.wait_for_timeout(300)
            K.evaluate("()=>document.getElementById('quit-confirm').click()")
            t = wait_for(A, "(n)=>{ const t = [...document.querySelectorAll('.toast')].map(x => x.innerText).join(' / '); return t.indexOf(n) >= 0 ? t : null; }", NAMES[KIM], tries=20)
            chk("(F) the racer still in it is told she left the match, not the lobby (%r)" % t, bool(t) and "match" in t and "lobby" not in t, t)
            leave(A); K.evaluate("()=>showHome()")
        except Exception as e:
            chk("(F) ran to the end", False, repr(e)[:300]); leave(A); leave(K)

    # ===================== (G) from one lobby into another =====================
    if want("G"):
        print("\n-- (G) joining another room from a lobby leaves the first", flush=True)
        try:
            code1 = host_room(A, unit_a, "race", 5)
            join(K, code1)
            code2 = host_room(O, unit_f, "race", 5)
            ok2 = join(K, code2)
            K.wait_for_timeout(1500)
            still = KIM in (room(code1).get("participants") or {})
            chk("(G) she is in the second room and gone from the first (%s; still in the first: %s)" % (bool(ok2), still), bool(ok2) and not still, room(code1).get("participants"))
            leave(K); leave(A); leave(O)
        except Exception as e:
            chk("(G) ran to the end", False, repr(e)[:300]); leave(K); leave(A); leave(O)

    # ===================== (H) not waiting on the server =====================
    if want("H"):
        print("\n-- (H) the wait card and Return to lobby, on a slow connection", flush=True)
        try:
            code = host_room(A, unit_a, "race", 5)
            join(K, code); ready([A, K])
            for pg in (A, K): wait_for(pg, RACE_UP, tries=90, step=300)
            A.evaluate(ANSWER_ALL, 4)
            CLOUD.slow["alex"] = 4.0
            t0 = time.time()
            A.evaluate(ANSWER_ALL, None)
            card = wait_for(A, "()=>!!document.querySelector('.vroom-waitcard')", tries=40, step=150)
            took = time.time() - t0
            chk("(H) the wait card is up %.1fs after the last answer, with the server 4s behind (it waited for the server's answer)" % took, bool(card) and took < 2.6, took)
            CLOUD.slow["alex"] = 0
            K.evaluate(ANSWER_ALL, None)
            wait_for(A, "()=>!!document.querySelector('.vroom-waitcard.is-all-in')", tries=60, step=500)
            CLOUD.slow["alex"] = 4.0
            t1 = time.time()
            A.evaluate("()=>{ document.getElementById('vroom-prep')?.remove(); vroomReturnToLobby(); }")
            lob = wait_for(A, "()=>!!document.querySelector('#stage .screen-vroom-lobby')", tries=40, step=150)
            took2 = time.time() - t1
            chk("(H) Return to lobby opens the lobby %.1fs after the tap, with the server 4s behind" % took2, bool(lob) and took2 < 2.6, took2)
            A.wait_for_timeout(4500); CLOUD.slow["alex"] = 0
            leave(A); leave(K)
        except Exception as e:
            CLOUD.slow["alex"] = 0
            chk("(H) ran to the end", False, repr(e)[:300]); leave(A); leave(K)

    # ===================== (I) Battle under fifty questions =====================
    if want("I"):
        print("\n-- (I) a Battle with six questions picked runs the fifty every device plays", flush=True)
        try:
            fast([A, K], True)
            code = host_room(A, unit_a, "battle", 6)
            join(K, code)
            lb = A.evaluate(LOBBY) or {}
            line = A.evaluate("()=>{ const l = document.querySelectorAll('#stage .vroom-test-summary .vroom-test-summary-line'); return l[1] ? l[1].textContent : ''; }")
            minq, qs = A.evaluate("()=>[BATTLE_MIN_Q, Math.round(BATTLE_Q_MS / 1000)]")
            # the numbers read off the app: the match's questions and each one's seconds, said outright (it said "at least 50")
            chk("(L) the Battle lobby says how many questions the match runs and how long each is (%r; %s, %ss)" % (line, minq, qs),
                re.search(r"\b%d questions" % minq, line) and re.search(r"\b%d seconds" % qs, line) and "at least" not in line, lb.get("summary"))
            ready([A, K])
            for pg in (A, K): wait_for(pg, "()=>!!document.querySelector('.screen-battle .choice')", tries=90, step=300)
            # nobody hits anybody: both answer wrong through question 8
            for _ in range(240):
                for pg in (A, K): team_answer(pg, False)
                pos = [pg.evaluate("()=>battlePos") for pg in (A, K)]
                if min(pos) >= 8: break
                A.wait_for_timeout(300)
            A.wait_for_timeout(2500)
            b = room(code).get("battle") or {}
            chk("(I) both are past question 8 of %s and the match is still on (over: %s)" % (A.evaluate("()=>battleCount"), b.get("over")),
                min(pos) >= 8 and not b.get("over") and A.evaluate("()=>!!document.querySelector('.screen-battle')"), {"pos": pos, "over": b.get("over"), "winner": b.get("winner")})
            # now Alexis's side takes the other down: the winners' scene
            for _ in range(500):
                team_answer(A, True); team_answer(K, False)
                if A.evaluate("()=>!!document.getElementById('vroom-cutscene') || !!document.querySelector('.screen-battle-result')"): break
                A.wait_for_timeout(250)
            sc = wait_for(A, "()=>{ const c = document.getElementById('vroom-cutscene'); return c ? { team: !!c.querySelector('.vroom-cut-team'), rope: !!c.querySelector('.vroom-cut-rope'), floor: !!c.querySelector('.vroom-cut-floor') } : null; }", tries=20, step=200)
            chk("(I) Battle's winners stand on a floor, not on Tug of War's rope (%s)" % sc, bool(sc) and sc["team"] and not sc["rope"] and sc["floor"], sc)
            wait_for(A, "()=>!!document.querySelector('.screen-battle-result')", tries=40)
            leave(A); leave(K); fast([A, K], False)
        except Exception as e:
            chk("(I) ran to the end", False, repr(e)[:300]); leave(A); leave(K); fast([A, K], False)

    # ===================== (J) Tug of War's standings and rope =====================
    if want("J"):
        print("\n-- (J) Tug of War: your side first in the standings; every figure on the rope inside the field", flush=True)
        try:
            fast([A, K], True)
            code = host_room(A, unit_a, "tug", 6)
            join(K, code); ready([A, K])
            for pg in (A, K): wait_for(pg, "()=>!!document.querySelector('.screen-tug .choice')", tries=90, step=300)
            for _ in range(400):
                team_answer(A, True); team_answer(K, False)
                if K.evaluate("()=>!!document.querySelector('.screen-tug-result')"): break
                A.wait_for_timeout(250)
            # (384 r8) the result is the drill's results screen: the podium ("Final standings") puts each side on a step and its
            # members in a column under it, your side first; the game's own card is the rope as it ended. Read off the losing
            # side's device (Kimber), where "first" is not simply the winners: her side, the step's side and her own row.
            res = wait_for(K, """()=>{ const s = document.querySelector('.screen-tug-result'); if(!s) return null;
                const team = tugTeamOf(tugLastData || {}, vroomMyKey);
                const spots = [...s.querySelectorAll('.vr-podium-sides .vr-side')];
                const cols = [...s.querySelectorAll('.vr-podium-cols .vr-podium-col')];
                const keysIn = c => c ? [...c.querySelectorAll('[data-key]')].map(r => r.dataset.key) : [];
                const f = s.querySelector('.tug-field'); if(!f) return { team: team, spots: spots.length, cols: cols.length, figs: 0, out: null };
                const fr = f.getBoundingClientRect();
                const figs = [...f.querySelectorAll('.tug-team-fig')].map(x => x.getBoundingClientRect());
                const out = figs.filter(r => r.left < fr.left - .5 || r.right > fr.right + .5).length;
                return { team: team, winner: (tugLastData && tugLastData.tug || {}).winner, spots: spots.length, cols: cols.length,
                         firstSide: spots[0] ? spots[0].dataset.side : null, firstColMine: keysIn(cols[0]).indexOf(vroomMyKey) >= 0,
                         secondColMine: keysIn(cols[1]).indexOf(vroomMyKey) >= 0, figs: figs.length, out: out }; }""", tries=30)
            r = res or {}
            chk("(J) the standings put her side first, as the rope does (her side %s, the winners %s; first step %s; her row in the first column: %s)"
                % (r.get("team"), r.get("winner"), r.get("firstSide"), r.get("firstColMine")),
                bool(res) and r["spots"] == 2 and r["cols"] == 2 and r["team"] and r["firstSide"] == r["team"] and r["firstColMine"] and not r["secondColMine"]
                and r.get("winner") and r["winner"] != r["team"], res)
            chk("(J) every figure on the rope is inside the field (%s outside of %s)" % (r.get("out"), r.get("figs")), bool(res) and r["figs"] >= 2 and r["out"] == 0, res)
            leave(A); leave(K); fast([A, K], False)
        except Exception as e:
            chk("(J) ran to the end", False, repr(e)[:300]); leave(A); leave(K); fast([A, K], False)

    # ===================== (K) Nova, invited on a slow connection =====================
    if want("K"):
        print("\n-- (K) Nova invited while the server is slow still readies", flush=True)
        try:
            code = host_room(O, unit_f, "race", 5)
            O.evaluate("()=>{ novaVrTimeScale = 0.3; }")
            CLOUD.slow["owner"] = 2.5
            O.click("#stage .vroom-invite-btn"); O.wait_for_timeout(900)
            O.evaluate("()=>document.querySelector('.invite-overlay .friend-row.is-nova .friend-act').click()"); O.wait_for_timeout(300)
            O.evaluate("()=>document.querySelector('.invite-overlay .invite-close')?.click()")
            nv = None
            for _ in range(50):
                nv = (room(code).get("participants") or {}).get("nova") or {}
                if nv.get("ready") or nv.get("prep"): break
                O.wait_for_timeout(400)
            CLOUD.slow["owner"] = 0
            chk("(K) Nova gets ready in the room (prep %s, ready %s; driving: %s)" % (nv.get("prep"), nv.get("ready"), O.evaluate("()=>!!novaVr")),
                bool(nv.get("ready") or nv.get("prep")), nv)
            leave(O)
        except Exception as e:
            CLOUD.slow["owner"] = 0
            chk("(K) ran to the end", False, repr(e)[:300]); leave(O)

    # ===================== (M) the invite sheet's class-sharing line in Fire Code =====================
    if want("M"):
        print("\n-- (M) the invite sheet in Fire Code, an account with no friends", flush=True)
        try:
            code = host_room(O, unit_f, "race", 5)
            O.evaluate("()=>{ window.__keep = [store.friendsIn, leaderboardRows]; store.friendsIn = []; leaderboardRows = [{ pub: 'zz-someone-else', firstName: 'Zed' }]; openInviteFriendsSheet(vroomCode); }")
            O.wait_for_timeout(700)
            line = O.evaluate("()=>{ const p = document.querySelector('.invite-overlay .friend-hint'); return p ? p.textContent : null; }")
            O.evaluate("()=>{ store.friendsIn = window.__keep[0]; leaderboardRows = window.__keep[1]; document.querySelector('.invite-overlay .invite-close')?.click(); }")
            chk("(M) an account sharing with the class is not told to turn class sharing on in Fire Code (%r)" % line, bool(line) and "class sharing" not in line, line)
            leave(O)
        except Exception as e:
            chk("(M) ran to the end", False, repr(e)[:300]); leave(O)

    # ===================== (O) every door, for an account not in the room's class =====================
    if want("O"):
        print("\n-- (O) every way in: the invite banner and the Inbox turn her away; an account in both classes joins either", flush=True)
        try:
            code_f = host_room(O, unit_f, "race", 5)
            # an invite as an older build would send it (the greyed button sends none) - straight into her mailbox
            inv = {"type": "vroom", "code": code_f, "cls": "ifc", "pub": OWNER, "at": now_ms(), "firstName": NAMES[OWNER], "avatarChar": AVATAR[OWNER]}
            CLOUD.handle("set", {"dev": "test", "c": "vrooms", "id": "inbox-" + ALEX, "v": {"kind": "inbox", "msgs": {OWNER: inv}}, "merge": True})
            A.evaluate("()=>showHome()")
            ban = wait_for(A, "()=>{ try{ checkLobbyInvites(); }catch(e){} return document.querySelector('#lobby-invite .app-banner-act') ? true : null; }", tries=30, step=400)
            if ban: A.evaluate("()=>document.querySelector('#lobby-invite .app-banner-act').click()")
            A.wait_for_timeout(1500)
            t1 = A.evaluate(TOASTS)
            in1 = ALEX in (room(code_f).get("participants") or {}) or A.evaluate("()=>!!document.querySelector('#stage .screen-vroom-lobby')")
            chk("(O) the invite banner's Join turns the academy-only account away from the Fire Code room, and says why (banner %s; in: %s; %r)" % (bool(ban), in1, t1),
                bool(ban) and not in1 and bool(t1.strip()), {"toast": t1})
            # the same invite again, from the Inbox
            inv["at"] = now_ms()
            CLOUD.handle("set", {"dev": "test", "c": "vrooms", "id": "inbox-" + ALEX, "v": {"kind": "inbox", "msgs": {OWNER: inv}}, "merge": True})
            A.wait_for_timeout(1500)
            A.evaluate("()=>{ document.getElementById('lobby-invite')?.remove(); document.querySelectorAll('.toast').forEach(t => t.remove()); chatDockTab = 'notifs'; openChatDock(); try{ syncChatDock(); renderNotifications(); }catch(e){} }")
            JOIN = ".chatdock-notif-vroom .chatdock-notif-acts .next:not(.ghost)"
            jb = wait_for(A, "(s)=>{ try{ renderNotifications(); }catch(e){} return document.querySelector(s) ? true : null; }", JOIN, tries=20, step=400)
            if jb: A.evaluate("(s)=>document.querySelector(s).click()", JOIN)
            A.wait_for_timeout(1500)
            t2 = A.evaluate(TOASTS)
            in2 = ALEX in (room(code_f).get("participants") or {}) or A.evaluate("()=>!!document.querySelector('#stage .screen-vroom-lobby')")
            chk("(O) the Inbox's Join turns her away the same (row %s; in: %s; %r)" % (bool(jb), in2, t2), bool(jb) and not in2 and bool(t2.strip()), {"toast": t2})
            A.evaluate("()=>{ try{ closeChatDock(); }catch(e){} showHome(); }")
            leave(O)
            # an account in both classes, on Fire Code's page, into an academy room
            code_a = host_room(A, unit_a, "race", 5)
            lo = join(O, code_a)
            chk("(O) an account in both classes joins an academy room from Fire Code's page (%s)" % bool(lo),
                bool(lo) and OWNER in (room(code_a).get("participants") or {}) and room(code_a).get("cls") in (None, "academy"), room(code_a).get("participants"))
            leave(O); leave(A)
        except Exception as e:
            chk("(O) ran to the end", False, repr(e)[:300]); leave(O); leave(A)

    # ===================== (N) =====================
    print("\n-- (N) no sync code in any vrooms document; no page errors", flush=True)
    A.wait_for_timeout(1000)
    leak = [k for k, v in CLOUD.data["vrooms"].items() if any(c in json.dumps(v) or c in k for c in CODE.values())]
    chk("(N) no sync code in any `vrooms` document (%d documents; %s)" % (len(CLOUD.data["vrooms"]), leak), not leak, leak)
    for dev, es in ERRS.items():
        chk("(N) no page errors on %s" % dev, not es, es[:3])
    for c in (actx, kctx, octx):
        try: c.close()
        except Exception: pass
    br.close()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
