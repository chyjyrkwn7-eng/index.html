"""A SHARED, IN-MEMORY FIRESTORE FOR TWO OR MORE DEVICES (build 384.39). The real SDK's CDN is blocked in this sandbox, so a gate that
needs two phones to see each other's documents serves its own: documents, dotted updates, FieldValue / FieldPath, transactions,
batches, document and collection listeners by long poll, and queries on field values - one Cloud, every device its own browser
context (its own storage) with this module's CLIENT as window.firebase. Copied from check-b384-vrifc.py's stand-in (that gate keeps
its own copy) and given the two things a friends check needs:
  * the real RULES' shape: a LIST of `progress` is refused (permission-denied), a get of one document is not;
  * `Cloud.fail`: set to a Firestore error code ("resource-exhausted", "permission-denied", "unavailable") and every operation
    fails with it, which is how a quota-exhausted day looks to the app.

    cloud, srv, url = make_cloud(seed, index_html_bytes, root)
    ctx.add_init_script(init_script(url, "A")); ctx.add_init_script(CLIENT)   # then goto(url + "/index.html")
"""
import copy, http.server, json, os, socket, sys, threading, time
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
        self.fail = None       # a Firestore error code: every operation then fails with it (a day's quota spent)
        self.reads = []        # {dev, op, path}
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
            if self.fail and op != "poll": return {"error": self.fail}
            if op == "query" and b.get("c") == "progress": return {"error": "permission-denied"}   # the rules: no listing of accounts
            if op in ("get", "query"): self.reads.append({"dev": b.get("dev"), "op": op, "path": b.get("c") + ("/" + b["id"] if op == "get" else "")})
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


MIME = {".js": "application/javascript", ".mjs": "application/javascript", ".json": "application/json", ".html": "text/html; charset=utf-8",
        ".css": "text/css", ".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml", ".pdf": "application/pdf", ".webp": "image/webp",
        ".mp3": "audio/mpeg", ".woff2": "font/woff2", ".wasm": "application/wasm"}


def make_cloud(seed, index_body, root, build=None):
    """Serve the app (index_body, bytes) and the cloud from ONE origin (a page fulfilled by route sits outside the loopback address
    space, and Chromium's local-network checks then refuse its requests to 127.0.0.1). Returns (cloud, server, base_url)."""
    cloud = Cloud(seed)
    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_GET(self):
            p = self.path.split("?")[0]
            if p in ("/", "/index.html"):
                b, ct = index_body, MIME[".html"]
            elif p == "/version.json" and build:
                b, ct = json.dumps({"build": build, "force": False, "frameId": ""}).encode(), MIME[".json"]
            else:
                f = os.path.realpath(os.path.join(root, p.lstrip("/")))
                if not f.startswith(os.path.realpath(root) + os.sep) or not os.path.isfile(f):
                    self.send_response(404); self.send_header("Content-Length", "0"); self.end_headers(); return
                b, ct = open(f, "rb").read(), MIME.get(os.path.splitext(f)[1].lower(), "application/octet-stream")
            self.send_response(200)
            self.send_header("Content-Type", ct); self.send_header("Content-Length", str(len(b))); self.send_header("Cache-Control", "no-store")
            self.end_headers(); self.wfile.write(b)
        def _send(self, code, obj=None):
            b = json.dumps(obj).encode() if obj is not None else b""
            self.send_response(code)
            self.send_header("Access-Control-Allow-Origin", "*"); self.send_header("Access-Control-Allow-Headers", "*")
            self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS"); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b))); self.end_headers()
            if b: self.wfile.write(b)
        def do_OPTIONS(self): self._send(204)
        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0)
            try: body = json.loads(self.rfile.read(n) or b"{}")
            except Exception: body = {}
            try: self._send(200, cloud.handle(self.path.strip("/").split("?")[0], body))
            except Exception as e: self._send(200, {"error": "server: " + str(e)})
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    class Srv(http.server.ThreadingHTTPServer):
        daemon_threads = True
        def handle_error(self, request, client_address): pass
    srv = Srv(("127.0.0.1", port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return cloud, srv, "http://127.0.0.1:%d" % port


def init_script(url, dev):
    return "window.__cloudUrl = %s; window.__dev = %s;" % (json.dumps(url), json.dumps(dev))


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
