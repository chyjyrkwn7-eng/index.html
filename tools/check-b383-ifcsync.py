"""Build 383: Fire Code syncs. Madison: "The police class has sync code working. The fire code side says sync code isn't
reachable. Fix that as well."
Fire Code's account lives at progress/<academy code>__ifc (beside the academy's, never in it); only the account reaches the
cloud there - fbDb stays null, so the leaderboard, Virtual Room, chat and invites stay off. With an in-memory Firestore stand-in
(the CDN is blocked here) and the owner's account (TEST-3830, a fake code):
 (1) device 1 in Fire Code writes its Fire Code progress to progress/TEST-3830__ifc - and nothing to progress/TEST-3830, the
     leaderboard or the rooms;
 (2) its Settings: the Sync row reads On, not Unreachable; the code it shows is the academy's (no suffix); fbDb is still null;
 (3) device 2, signed in to the same academy account and opening Fire Code for the first time, gets device 1's Fire Code
     progress from the cloud;
 (4) the academy class still syncs to progress/TEST-3830 as before.
Run:  python3 tools/check-b383-ifcsync.py   (--against OLD/index.html must FAIL)"""
import json, os, sys
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
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else ("  -> " + str(info)[:300]), flush=True)
OWNER = "xph5b57jbp5a"; CODE = "TEST-3830"
# an in-memory Firestore: docs, get, set, update, delete, live listeners; every write logged as collection/id
FAKE = r"""(()=>{
  const seed = window.__cloudSeed || {};
  const C = window.__cloud = { progress: {}, leaderboard: {}, vrooms: {} }; window.__writes = [];
  Object.keys(seed).forEach(c => { C[c] = Object.assign(C[c] || {}, seed[c]); });
  const subs = {};
  const clone = v => v == null ? v : JSON.parse(JSON.stringify(v));
  const snap = (c, id) => { const d = (C[c] || {})[id]; return { id, exists: d !== undefined, data: () => clone(d), metadata: { fromCache: false, hasPendingWrites: false } }; };
  const fire = (c, id) => (subs[c + '/' + id] || []).forEach(f => setTimeout(() => f(snap(c, id)), 15));
  const doc = (c, id) => ({ id,
    get: () => Promise.resolve(snap(c, id)),
    set: (v, o) => { (C[c] = C[c] || {}); C[c][id] = (o && o.merge) ? Object.assign({}, C[c][id] || {}, clone(v)) : clone(v); __writes.push(c + '/' + id); fire(c, id); return Promise.resolve(); },
    update: v => { (C[c] = C[c] || {}); C[c][id] = Object.assign({}, C[c][id] || {}, clone(v)); __writes.push(c + '/' + id); fire(c, id); return Promise.resolve(); },
    delete: () => { if(C[c]) delete C[c][id]; __writes.push('DEL ' + c + '/' + id); fire(c, id); return Promise.resolve(); },
    onSnapshot: function(){ const a = [...arguments]; const next = a.find(x => typeof x === 'function'); const k = c + '/' + id; (subs[k] = subs[k] || []).push(next); setTimeout(() => next(snap(c, id)), 30); return () => { subs[k] = (subs[k] || []).filter(f => f !== next); }; },
    collection: n => coll(c + '/' + id + '/' + n) });
  const coll = c => { const q = { doc: id => doc(c, id), where(){ return q; }, orderBy(){ return q; }, limit(){ return q; },
    get: () => Promise.resolve({ empty: true, docs: [], forEach(){} }), onSnapshot: function(){ const a=[...arguments]; const next=a.find(x=>typeof x==='function'); setTimeout(()=>next({ empty:true, docs:[], forEach(){}, metadata:{fromCache:false}, docChanges:()=>[] }),30); return ()=>{}; } }; return q; };
  const db = { collection: coll, batch: () => ({ set(){}, update(){}, delete(){}, commit: () => Promise.resolve() }) };
  const fs = () => db; fs.FieldValue = { delete: () => null, serverTimestamp: () => Date.now(), arrayUnion: (...x) => x, increment: n => n }; fs.FieldPath = function(){};
  window.firebase = { apps: [], initializeApp(){ this.apps.push({}); }, firestore: fs };
})()"""
def page(br, init, seed=None):
    ctx = br.new_context(viewport={"width": 440, "height": 956}, has_touch=True)
    ctx.add_init_script("window.__cloudSeed = %s;" % json.dumps(seed or {}))
    ctx.add_init_script(FAKE)
    ctx.add_init_script(g["STANDALONE"])
    ctx.add_init_script(init)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    body = g["patched"]((59, 0, 34, 0))
    if OLD_BUILD:
        pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"}, body=json.dumps({"build": OLD_BUILD, "force": False, "frameId": ""})))
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.goto(g["url"] if "url" in g else serve_url); pg.wait_for_timeout(3500)
    pg.evaluate("document.getElementById('splashscreen')?.remove()")
    return ctx, pg, errs
srv, serve_url = g["serve"]()
academy = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]())); academy["publicId"] = OWNER; academy["firstName"] = "Maddog"; academy["novaMet"] = 99
academy.setdefault("novaHeard", {})["@recap"] = 99991231
ifc = dict(academy); ifc["lifetime"] = dict(academy["lifetime"], points=4321, correct=777); ifc["novaMet"] = 99
SEEN = "['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card','class26e.getstarted','class26e.frame.ok'].forEach(k=>localStorage.setItem(k, k==='class26e.frame.ok'?'go-live-1':'1'));"
def init(ifc_store, active="ifc"):
    s = "(()=>{ if(sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); " + SEEN
    s += "localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode', '%s');" % (json.dumps(json.dumps(academy)), CODE)
    if active == "ifc":
        s += "localStorage.setItem('class26e.activeclass','ifc'); localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done');"
        s += "['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted'].forEach(k=>localStorage.setItem(k,'1'));"
        if ifc_store is not None: s += "localStorage.setItem('class26e.ifc.drill.v1', %s);" % json.dumps(json.dumps(ifc_store))
    return s + " })()"
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    # (1)(2) device 1 in Fire Code
    ctx, pg, errs = page(br, init(ifc))
    for _ in range(20):
        if pg.evaluate("()=>!!(window.__cloud.progress[%s])" % json.dumps(CODE + "__ifc")): break
        pg.wait_for_timeout(500)
    r = pg.evaluate("""(code)=>({ cls: window.NOVA_CLASS, doc: window.__cloud.progress[code + '__ifc'] || null, academyDoc: !!window.__cloud.progress[code],
        writes: window.__writes.slice(), fb: (typeof fbDb === 'undefined') ? 'undef' : (fbDb === null ? null : 'set') })""", CODE)
    pts = r["doc"] and (r["doc"].get("lifetime") or {}).get("points")
    chk("(1) in Fire Code, device 1's Fire Code progress is saved to its own account (progress/%s__ifc, %s points)" % (CODE, pts), r["cls"] == "ifc" and pts == 4321, r)
    bad = [w for w in r["writes"] if not w.startswith("progress/" + CODE + "__ifc")]
    chk("(1) and nothing else is written - not the academy's account, not the leaderboard, not the rooms (%s)" % bad, not r["academyDoc"] and not bad, r["writes"])
    chk("(2) fbDb stays null in Fire Code (the leaderboard, rooms and chat stay off)", r["fb"] is None, r["fb"])
    pg.evaluate("()=>showAppearance()"); pg.wait_for_timeout(900)
    row = pg.evaluate("()=>{ const b=document.getElementById('settings-row-sync'); return b ? b.textContent.replace(/\\s+/g,' ').trim() : null; }")
    chk("(2) Settings' Sync row reads On, not Unreachable (%r)" % row, bool(row) and "On" in row and "Unreachable" not in row, row)
    pg.evaluate("()=>showAppearance({ page: 'sync' })"); pg.wait_for_timeout(900)
    shown = pg.evaluate("""async ()=>{ const r=document.querySelector('#stage .sync-code-row'); if(!r) return null; r.click(); await new Promise(x=>setTimeout(x,300));
        return { code: r.querySelector('.sync-code-value').textContent, unreachable: !!document.querySelector('#stage .sync-status-row') }; }""")
    chk("(2) the Sync page shows the academy's code, not unreachable (%s)" % (shown,), shown and shown["code"] == CODE and not shown["unreachable"], shown)
    chk("(1) no page errors on device 1", not errs, errs[:2])
    cloud = pg.evaluate("()=>window.__cloud")
    ctx.close()
    # (3) device 2: the same academy account, Fire Code for the first time on this device
    ctx, pg, errs = page(br, init(None), seed={"progress": cloud.get("progress", {})})
    got = None
    for _ in range(24):
        got = pg.evaluate("()=>({ cls: window.NOVA_CLASS, pts: (store.lifetime||{}).points, correct: (store.lifetime||{}).correct })")
        if got["pts"] == 4321: break
        pg.wait_for_timeout(500)
    chk("(3) device 2 opening Fire Code gets device 1's Fire Code progress from the cloud (%s)" % (got,), got and got["cls"] == "ifc" and got["pts"] == 4321 and got["correct"] == 777, got)
    w2 = pg.evaluate("()=>window.__writes.filter(w => !w.startsWith('progress/%s__ifc'))" % CODE)
    chk("(3) and writes nothing outside its Fire Code account (%s)" % w2, not w2, w2)
    chk("(3) no page errors on device 2", not errs, errs[:2])
    ctx.close()
    # (4) the academy is as it was
    ctx, pg, errs = page(br, init(None, active="academy"))
    for _ in range(20):
        if pg.evaluate("()=>!!window.__cloud.progress[%s]" % json.dumps(CODE)): break
        pg.wait_for_timeout(500)
    a = pg.evaluate("(code)=>({ cls: window.NOVA_CLASS, doc: !!window.__cloud.progress[code], ifcDoc: !!window.__cloud.progress[code + '__ifc'] })", CODE)
    chk("(4) the academy class still syncs to its own account (%s)" % (a,), a["cls"] == "academy" and a["doc"] and not a["ifcDoc"], a)
    ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
