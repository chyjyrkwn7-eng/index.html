"""Build 384: friends in every class. Madison: "your friends will be shown no matter what class type you are in. So for example
while I'm in the ifc, I should be able to see any friend I have in the chat and friends list and stuff. Vice Versa, any class."
In Fire Code the friends, the chat and presence are the academy account's (its public id and friend code), reached through a
scoped handle of their own (socialDb / ifcSocialDb); fbDb stays null, so the leaderboard and the Virtual Room stay academy-only,
and Fire Code still writes nothing of the academy's progress. With an in-memory Firestore (the CDN is blocked here; documents,
dotted updates, FieldValue/FieldPath, transactions, batches, collection and document listeners, every write logged), the
owner's account (TEST-3846, a fake code) and made-up classmates:
 (A) device 1 in Fire Code: the chat's Friends tab and Manage friends show the academy's friends, its friend code, a waiting
     request and who is online; accepting a request, adding a friend by code and a DM all reach the same documents the academy
     uses; nothing is written to progress/TEST-3846 or the leaderboard - only progress/TEST-3846__ifc and `vrooms`; the two
     Fire Code handles refuse the academy's progress and the board outright;
 (B) the same device back in the academy: the friend accepted and the request sent in Fire Code are there, and the DM sent in
     Fire Code is in the academy's thread; a friend added here...
 (C) ...shows in Fire Code on a second device whose own copy of the academy is older (read from the academy's account).
Run:  python3 tools/check-b384-friends.py   (--against OLD/index.html must FAIL)"""
import json, os, sys, time
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
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else ("  -> " + str(info)[:400]), flush=True)

OWNER = "xph5b57jbp5a"; CODE = "TEST-3846"; MYCODE = "QRT-384"
ALEX, KIM, PAT, LEE = "tst384alex01", "tst384kimm02", "tst384patt03", "tst384leee04"
FCODES = {ALEX: "AXL-384", KIM: "KMW-384", PAT: "PTZ-384", LEE: "LEY-384"}
NAMES = {ALEX: "Alexis", KIM: "Kimber", PAT: "Patton", LEE: "Leeland"}
def dm(a, b): return "DM-" + "-".join(sorted([a.upper(), b.upper()]))

# an in-memory Firestore: documents (set/merge, dotted update, FieldPath pairs, FieldValue sentinels), get, delete, document and
# collection listeners (with where), transactions and batches; every write is logged as collection/id
FAKE = r"""(()=>{
  const seed = window.__cloudSeed || {};
  const clone = v => v == null ? v : JSON.parse(JSON.stringify(v));
  const C = window.__cloud = { progress: {}, leaderboard: {}, vrooms: {} }; window.__writes = [];
  Object.keys(seed).forEach(c => { C[c] = Object.assign(C[c] || {}, clone(seed[c])); });
  function FV(kind, arg){ this.__fv = kind; this.arg = arg; }
  const isFV = v => v instanceof FV;
  function FieldPath(){ this.segs = Array.prototype.slice.call(arguments); }
  const docSubs = {}, colSubs = {};
  const meta = { fromCache: false, hasPendingWrites: false };
  const resolve = v => { if(isFV(v)) return v.__fv === 'ts' ? Date.now() : null; if(Array.isArray(v)) return v.map(resolve);
    if(v && typeof v === 'object'){ const o = {}; Object.keys(v).forEach(k => { if(!(isFV(v[k]) && v[k].__fv === 'delete')) o[k] = resolve(v[k]); }); return o; } return v; };
  const setPath = (obj, segs, v) => { let o = obj;
    for(let i = 0; i < segs.length - 1; i++){ if(typeof o[segs[i]] !== 'object' || o[segs[i]] === null) o[segs[i]] = {}; o = o[segs[i]]; }
    const k = segs[segs.length - 1];
    if(isFV(v)){
      if(v.__fv === 'delete') delete o[k];
      else if(v.__fv === 'arrayUnion'){ const a = Array.isArray(o[k]) ? o[k] : []; v.arg.forEach(x => { if(!a.some(y => JSON.stringify(y) === JSON.stringify(x))) a.push(clone(x)); }); o[k] = a; }
      else if(v.__fv === 'arrayRemove'){ const a = Array.isArray(o[k]) ? o[k] : []; o[k] = a.filter(y => !v.arg.some(x => JSON.stringify(x) === JSON.stringify(y))); }
      else if(v.__fv === 'increment') o[k] = (Number(o[k]) || 0) + v.arg;
      else o[k] = Date.now();
    } else o[k] = resolve(v); };
  const mergeInto = (o, v) => Object.keys(v).forEach(k => { const x = v[k];
    if(x && typeof x === 'object' && !Array.isArray(x) && !isFV(x)){ if(typeof o[k] !== 'object' || o[k] === null || Array.isArray(o[k])) o[k] = {}; mergeInto(o[k], x); }
    else setPath(o, [k], x); });
  const dsnap = (c, id) => { const d = (C[c] || {})[id]; return { id, exists: d !== undefined, data: () => clone(d), get: k => clone((d || {})[k]), metadata: meta }; };
  const qsnap = (c, f) => { const ids = Object.keys(C[c] || {}).filter(id => !f || f(C[c][id])); const docs = ids.map(id => dsnap(c, id));
    return { empty: !docs.length, size: docs.length, docs, forEach: cb => docs.forEach(cb), metadata: meta, docChanges: () => [] }; };
  const fire = (c, id) => { (docSubs[c + '/' + id] || []).slice().forEach(cb => setTimeout(() => cb(dsnap(c, id)), 15));
    (colSubs[c] || []).slice().forEach(s => setTimeout(() => s.cb(qsnap(c, s.f)), 20)); };
  const W = {
    set(c, id, v, o){ C[c] = C[c] || {}; if(o && o.merge){ const cur = clone(C[c][id]) || {}; mergeInto(cur, v); C[c][id] = cur; } else C[c][id] = resolve(v); __writes.push(c + '/' + id); fire(c, id); },
    update(c, id, a){ C[c] = C[c] || {}; if(C[c][id] === undefined) throw new Error('not-found: ' + c + '/' + id); const cur = clone(C[c][id]);
      if(a.length === 1 && a[0] && typeof a[0] === 'object' && !(a[0] instanceof FieldPath)) Object.keys(a[0]).forEach(k => setPath(cur, k.split('.'), a[0][k]));
      else for(let i = 0; i < a.length; i += 2) setPath(cur, a[i] instanceof FieldPath ? a[i].segs : String(a[i]).split('.'), a[i + 1]);
      C[c][id] = cur; __writes.push(c + '/' + id); fire(c, id); },
    del(c, id){ if(C[c]) delete C[c][id]; __writes.push('DEL ' + c + '/' + id); fire(c, id); } };
  const later = f => { try{ f(); return Promise.resolve(); }catch(e){ return Promise.reject(e); } };
  function doc(c, id){ return { id, path: c + '/' + id, __c: c,
    get: () => Promise.resolve(dsnap(c, id)),
    set: (v, o) => later(() => W.set(c, id, v, o)),
    update: function(){ const a = [...arguments]; return later(() => W.update(c, id, a)); },
    delete: () => later(() => W.del(c, id)),
    onSnapshot: function(){ const next = [...arguments].find(x => typeof x === 'function'); const k = c + '/' + id;
      (docSubs[k] = docSubs[k] || []).push(next); setTimeout(() => next(dsnap(c, id)), 30);
      return () => { docSubs[k] = (docSubs[k] || []).filter(x => x !== next); }; },
    collection: n => coll(c + '/' + id + '/' + n) }; }
  function coll(c, f){ const q = {
    doc: id => doc(c, id === undefined ? 'auto' + Math.random().toString(36).slice(2) : id),
    where: (k, op, v) => coll(c, d => (!f || f(d)) && (op === '>' ? d[k] > v : op === '>=' ? d[k] >= v : op === '<' ? d[k] < v : op === '==' ? d[k] === v : true)),
    orderBy(){ return q; }, limit(){ return q; },
    get: () => Promise.resolve(qsnap(c, f)),
    add: v => { const d = doc(c, 'auto' + Math.random().toString(36).slice(2)); return d.set(v).then(() => d); },
    onSnapshot: function(){ const next = [...arguments].find(x => typeof x === 'function'); const s = { cb: next, f };
      (colSubs[c] = colSubs[c] || []).push(s); setTimeout(() => next(qsnap(c, f)), 30);
      return () => { colSubs[c] = (colSubs[c] || []).filter(x => x !== s); }; } }; return q; }
  const writer = ops => { const w = {
    set(r, v, o){ ops.push(() => W.set(r.__c, r.id, v, o)); return w; },
    update(r){ const a = [...arguments].slice(1); ops.push(() => W.update(r.__c, r.id, a)); return w; },
    delete(r){ ops.push(() => W.del(r.__c, r.id)); return w; } }; return w; };
  const db = { collection: n => coll(n),
    runTransaction: fn => { const ops = []; const tx = writer(ops); tx.get = r => Promise.resolve(dsnap(r.__c, r.id));
      return Promise.resolve().then(() => fn(tx)).then(res => { ops.forEach(o => o()); return res; }); },
    batch: () => { const ops = []; const b = writer(ops); b.commit = () => later(() => ops.forEach(o => o())); return b; } };
  const fs = () => db;
  fs.FieldValue = { delete: () => new FV('delete'), serverTimestamp: () => new FV('ts'), arrayUnion: (...x) => new FV('arrayUnion', x),
                    arrayRemove: (...x) => new FV('arrayRemove', x), increment: n => new FV('increment', n) };
  fs.FieldPath = FieldPath;
  window.firebase = { apps: [], initializeApp(){ this.apps.push({}); }, firestore: fs };
})()"""

def page(br, init, seed=None, state=None):
    kw = {"viewport": {"width": 440, "height": 956}, "has_touch": True}
    if state: kw["storage_state"] = state
    ctx = br.new_context(**kw)
    ctx.add_init_script("window.__cloudSeed = %s;" % json.dumps(seed or {}))
    ctx.add_init_script(FAKE)
    ctx.add_init_script(g["STANDALONE"])
    if init: ctx.add_init_script(init)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    body = g["patched"]((59, 0, 34, 0))
    if OLD_BUILD:
        pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"}, body=json.dumps({"build": OLD_BUILD, "force": False, "frameId": ""})))
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.goto(serve_url); pg.wait_for_timeout(3800)
    pg.evaluate("document.getElementById('splashscreen')?.remove()")
    return ctx, pg, errs

srv, serve_url = g["serve"]()
WEEK = g["week_key_now"]()
now_ms = int(time.time() * 1000)
academy = json.loads(g["SEED"].replace("__WEEK__", WEEK))
academy.update({"publicId": OWNER, "firstName": "Maddox", "novaMet": 99, "friendCode": MYCODE, "friendsIn": [ALEX], "friendsOut": [],
                "friendsDeclined": [], "chats": [], "leaderboardOptIn": True, "lastModified": now_ms - 3600000})
academy.setdefault("novaHeard", {})["@recap"] = 99991231
# Fire Code's own copy, as the class's first visit left it: the same person, its own progress, off the board, no friends of its own
ifc = {k: academy[k] for k in ["firstName", "avatarChar", "publicId", "onboardingComplete", "tourRev", "novaMet", "novaHeard", "weekKey"] if k in academy}
ifc.update({k: v for k, v in academy.items() if k.startswith("seen")})
ifc.update({"lifetime": dict(academy["lifetime"], points=4321, correct=777), "leaderboardOptIn": False, "leaderboardOptInChanged": True,
            "lastModified": now_ms - 1800000})
def row(pub, lvl, extra=None):
    r = {"firstName": NAMES.get(pub, "Maddox"), "avatarChar": "ghost", "level": lvl, "badges": 3, "mystery": 0, "hundos": 4, "correct": 120,
         "week": WEEK, "weekPoints": 50, "fcode": FCODES.get(pub, MYCODE), "freq": [], "facc": [], "lastModified": now_ms - 60000}
    r.update(extra or {}); return r
ROWS = {OWNER: row(OWNER, 23, {"facc": [ALEX], "avatarChar": "ninja"}), ALEX: row(ALEX, 31), KIM: row(KIM, 12),
        PAT: row(PAT, 58, {"freq": [OWNER]}), LEE: row(LEE, 40)}
CLOUD0 = {
    "progress": {CODE: academy},
    "leaderboard": ROWS,
    "vrooms": {
        "presence-v1": {"kind": "presence", "p": {ALEX: now_ms, KIM: now_ms - 3 * 3600000}, "a": {ALEX: "menu"}},
        "inbox-" + OWNER: {"kind": "inbox", "msgs": {PAT: {"type": "friendreq", "pub": PAT, "at": now_ms - 600000, "firstName": NAMES[PAT], "avatarChar": "ghost", "level": 58}}},
    },
}
SEEN = ("['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card',"
        "'class26e.getstarted','class26e.frame.ok'].forEach(k=>localStorage.setItem(k, k==='class26e.frame.ok'?'go-live-1':'1'));")
def init(active, with_ifc=True, academy_copy=None):
    s = "(()=>{ if(sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); " + SEEN
    s += "localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode', '%s');" % (json.dumps(json.dumps(academy_copy or academy)), CODE)
    s += "localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done');"
    s += "['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted'].forEach(k=>localStorage.setItem(k,'1'));"
    if active == "ifc": s += "localStorage.setItem('class26e.activeclass','ifc');"
    if with_ifc: s += "localStorage.setItem('class26e.ifc.drill.v1', %s);" % json.dumps(json.dumps(ifc))
    return s + " })()"
def wait_for(pg, js, arg=None, tries=30, step=400):
    v = None
    for _ in range(tries):
        v = pg.evaluate(js, arg) if arg is not None else pg.evaluate(js)
        if v: return v
        pg.wait_for_timeout(step)
    return v
# what a class wrote, by kind
def writes_of(pg):
    return pg.evaluate("()=>window.__writes.slice()")
def foreign(ws, allowed):
    return [w for w in ws if not any(w.startswith(a) for a in allowed)]
DOCK_FRIENDS = """async ()=>{ const W = ms => new Promise(r => setTimeout(r, ms));
  try{ if(chatRoomCode) closeChatRoom(); }catch(e){}
  chatDockTab = 'friends'; openChatDock(); await W(900);
  const rows = [...document.querySelectorAll('.chatdock-chatlist.is-friends .chatdock-chatrow')].map(r => ({
      code: r.dataset.code, name: (r.querySelector('.chatdock-chatrow-name') || {}).textContent || '',
      online: !!r.querySelector('.chatdock-chatrow-avatar.is-online') }));
  const bar = (document.querySelector('.chatdock-friendsbar-info') || {}).textContent || '';
  const btn = (document.querySelector('.chatdock-friendsbar-btn') || {}).textContent || '';
  return { rows, bar, btn }; }"""
MANAGE = """async ()=>{ const W = ms => new Promise(r => setTimeout(r, ms));
  openFriendsFromChat(); await W(1200);
  const s = document.querySelector('#stage > .screen-friends'); if(!s) return null;
  const sect = [...s.querySelectorAll('.friend-sect')].map(x => ({ label: (x.querySelector('.sect-label') || {}).textContent || '',
      names: [...x.querySelectorAll('.friend-row-name')].map(n => n.textContent) }));
  return { code: (s.querySelector('.friend-mycode') || {}).textContent || '', sect,
           online: [...s.querySelectorAll('.friend-row')].filter(r => r.querySelector('.friend-online-dot')).map(r => (r.querySelector('.friend-row-name') || {}).textContent) }; }"""
SEND_DM = """async (a)=>{ const W = ms => new Promise(r => setTimeout(r, ms));
  openFriendChat(a.pub); await W(1200);
  const inp = document.querySelector('.chatdock-chathost .vroom-chat-input'), btn = document.querySelector('.chatdock-chathost .vroom-chat-send');
  if(!inp || !btn) return { sent: false, why: 'no composer', room: chatRoomCode };
  inp.value = a.text; inp.dispatchEvent(new Event('input', { bubbles: true })); btn.click(); await W(900);
  return { sent: true, room: chatRoomCode }; }"""
READ_DM = """async (a)=>{ const W = ms => new Promise(r => setTimeout(r, ms));
  try{ if(chatRoomCode) closeChatRoom(); }catch(e){}
  openFriendChat(a.pub);
  let txt = '';
  for(let i = 0; i < 20; i++){ await W(250);
    txt = [...document.querySelectorAll('.chatdock-chathost .vroom-chat-list')].map(l => l.textContent).join(' ');
    if(txt.indexOf(a.text) >= 0) break; }
  return { room: chatRoomCode, has: txt.indexOf(a.text) >= 0, txt: txt.slice(0, 300), open: chatDockOpen,
           host: !!document.querySelector('.chatdock-chathost'), doc: !!(window.__cloud.vrooms[chatRoomCode || ''] || null) }; }"""

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    # ---------------- (A) device 1, in Fire Code ----------------
    ctx, pg, errs = page(br, init("ifc"), seed=CLOUD0)
    r = pg.evaluate("""()=>({ cls: window.NOVA_CLASS, fb: (typeof fbDb === 'undefined') ? 'undef' : (fbDb === null ? null : 'set'),
        social: (typeof socialDb === 'function' && !!socialDb()), pub: store.publicId, fcode: store.friendCode, optin: store.leaderboardOptIn })""")
    chk("(A) Fire Code: fbDb stays null (no leaderboard, no Virtual Room) and the friends reach the cloud through their own handle (%s)" % r,
        r["cls"] == "ifc" and r["fb"] is None and r["social"] is True, r)
    chk("(A) Fire Code is the academy account on the friends side: its public id and its friend code %s (%s / %s), off the board itself" % (MYCODE, r["pub"], r["fcode"]),
        r["pub"] == OWNER and r["fcode"] == MYCODE and r["optin"] is False, r)
    d = wait_for(pg, "async ()=>{ const x = await (%s)(); return (x.rows.length && x.rows.some(r => r.online)) ? x : null; }" % DOCK_FRIENDS, tries=12) or pg.evaluate(DOCK_FRIENDS)
    alex = [x for x in d["rows"] if x["code"] == dm(OWNER, ALEX)]
    chk("(A) the chat's Friends tab lists the academy's friend %s, online (%s)" % (NAMES[ALEX], d),
        bool(alex) and alex[0]["name"] == NAMES[ALEX] and alex[0]["online"] and "1 online" in d["bar"], d)
    chk("(A) the Friends tab's button counts the request waiting from %s (%r)" % (NAMES[PAT], d["btn"]), "1 request" in d["btn"], d)
    m = pg.evaluate(MANAGE)
    labels = {x["label"]: x["names"] for x in (m or {}).get("sect", [])}
    yours = [v for k, v in labels.items() if k.startswith("Your friends")]
    pend = [v for k, v in labels.items() if "friend request" in k]
    chk("(A) Manage friends: the academy's friend code, %s among your friends (online) and %s's request (%s)" % (NAMES[ALEX], NAMES[PAT], m),
        bool(m) and m["code"] == MYCODE and yours and NAMES[ALEX] in yours[0] and pend and NAMES[PAT] in pend[0] and NAMES[ALEX] in m["online"], m)
    # accept the request, add a friend by code
    acc = pg.evaluate("""async (name)=>{ const W = ms => new Promise(r => setTimeout(r, ms));
        const row = [...document.querySelectorAll('#stage .friend-sect-pending .friend-row')].find(r => (r.querySelector('.friend-row-name')||{}).textContent === name);
        if(!row) return null; const b = [...row.querySelectorAll('button')].find(x => x.textContent === 'Accept'); if(!b) return null; b.click(); await W(900);
        document.querySelectorAll('.friend-moment').forEach(x => x.remove());
        const inp = document.querySelector('#stage .friend-add-input'); const send = [...document.querySelectorAll('#stage .friend-sect-add button')].find(x => x.textContent === 'Send');
        return { inp: !!inp, send: !!send }; }""", NAMES[PAT])
    pg.evaluate("""async (code)=>{ const inp = document.querySelector('#stage .friend-add-input'); inp.value = code; inp.dispatchEvent(new Event('input', { bubbles: true }));
        [...document.querySelectorAll('#stage .friend-sect-add button')].find(x => x.textContent === 'Send').click(); await new Promise(r => setTimeout(r, 900)); }""", FCODES[KIM]) if acc and acc["send"] else None
    st = pg.evaluate("""(me)=>{ const r = (typeof rowsByPublicId === 'function' && rowsByPublicId()[me]) || {};
        return { fin: store.friendsIn.slice(), fout: store.friendsOut.slice(), at: store.socialAt,
                 rowLevel: typeof r.rawLevel === 'number' ? r.rawLevel : r.level, ownLevel: levelOf(store) }; }""", OWNER)
    cl = pg.evaluate("()=>JSON.parse(JSON.stringify(window.__cloud))")
    accd = ((cl["vrooms"].get("inbox-" + PAT) or {}).get("msgs") or {}).get(OWNER) or {}
    reqd = ((cl["vrooms"].get("inbox-" + KIM) or {}).get("msgs") or {}).get(OWNER) or {}
    chk("(A) accepting %s in Fire Code: a friend, and the accept is in their mailbox as the academy's (%s, %s)" % (NAMES[PAT], st, accd),
        PAT in st["fin"] and accd.get("type") == "friendacc" and accd.get("pub") == OWNER and accd.get("firstName") == "Maddox", {"st": st, "acc": accd, "a": acc})
    chk("(A) adding %s by friend code in Fire Code: asked, and the request is in their mailbox, from the academy account at the level its row publishes (%s, not Fire Code's %s) (%s)" % (NAMES[KIM], st["rowLevel"], st["ownLevel"], reqd),
        KIM in st["fout"] and reqd.get("type") == "friendreq" and reqd.get("firstName") == "Maddox" and reqd.get("level") == st["rowLevel"]
        and st["rowLevel"] != st["ownLevel"], {"st": st, "req": reqd})
    # a DM from Fire Code
    s = pg.evaluate(SEND_DM, {"pub": ALEX, "text": "fire code hello 384"})
    pg.wait_for_timeout(600)
    cl = pg.evaluate("()=>JSON.parse(JSON.stringify(window.__cloud))")
    thread = (cl["vrooms"].get(dm(OWNER, ALEX)) or {})
    msgs = [x for x in (thread.get("chatMessages") or []) if x.get("text") == "fire code hello 384"]
    chk("(A) a DM sent in Fire Code is in the friend chat the academy uses (%s, %s)" % (s, msgs[:1]),
        s.get("sent") and s.get("room") == dm(OWNER, ALEX) and msgs and msgs[0].get("key") == OWNER and msgs[0].get("name") == "Maddox", {"s": s, "thread": thread})
    pres = ((cl["vrooms"].get("presence-v1") or {}).get("p") or {}).get(OWNER)
    chk("(A) and Fire Code says the academy account is online (presence %s)" % pres, isinstance(pres, (int, float)) and pres > now_ms - 600000, pres)
    # the handles' own limits
    lim = pg.evaluate("""async (code)=>{ const tryit = p => Promise.resolve().then(p).then(() => 'wrote', e => 'refused');
        const s = typeof ifcSocialDb !== 'undefined' ? ifcSocialDb : null, a = typeof ifcAcctDb !== 'undefined' ? ifcAcctDb : null;
        if(!s || !a) return null;
        return { socialProgress: await tryit(() => s.collection('progress').doc(code).set({ x: 1 })),
                 socialBoard: await tryit(() => s.collection('leaderboard').doc('%s').set({ x: 1 }, { merge: true })),
                 acctAcademy: await tryit(() => a.collection('progress').doc(code).set({ x: 1 })),
                 acctFloor: await tryit(() => a.collection('progress').doc(code + '__floor').update({ x: 1 })),
                 acctTx: await tryit(() => a.runTransaction(tx => tx.get(a.collection('progress').doc(code)).then(() => { tx.set(a.collection('progress').doc(code), { x: 1 }); }))),
                 acctBatch: await tryit(() => { const b = a.batch(); b.set(a.collection('progress').doc(code), { x: 1 }); return b.commit(); }),
                 acctOwn: await tryit(() => a.collection('progress').doc(code + '__ifc').get()),
                 socialRooms: await tryit(() => s.collection('vrooms').doc('presence-v1').get()) }; }""".replace("'%s'", json.dumps(OWNER)), CODE)
    chk("(A) the friends handle cannot write the academy's progress or the board, and the account handle writes nothing of the academy's - not by set, update, transaction or batch (%s)" % lim,
        bool(lim) and lim["socialProgress"] == lim["socialBoard"] == lim["acctAcademy"] == lim["acctFloor"] == lim["acctTx"] == lim["acctBatch"] == "refused"
        and lim["acctOwn"] == "wrote" and lim["socialRooms"] == "wrote", lim)
    pg.wait_for_timeout(1500)
    ws = writes_of(pg)
    cl = pg.evaluate("()=>JSON.parse(JSON.stringify(window.__cloud))")
    bad = foreign(ws, ["progress/" + CODE + "__ifc", "vrooms/"])
    chk("(A) Fire Code wrote nothing to progress/%s or the leaderboard - only progress/%s__ifc and `vrooms` (%s)" % (CODE, CODE, sorted(set(bad))),
        not bad and cl["progress"].get(CODE) == academy and cl["leaderboard"] == ROWS and any(w.startswith("vrooms/") for w in ws), sorted(set(ws)))
    leak = [k for k, v in list(cl["vrooms"].items()) + list(cl["leaderboard"].items()) if CODE in json.dumps(v) or CODE in k]
    chk("(A) no sync code in any rooms or board document (%s)" % leak, not leak, leak)
    own = cl["progress"].get(CODE + "__ifc") or {}
    chk("(A) Fire Code's own account carries the friends block, dated (friendsIn %s, socialAt %s)" % (own.get("friendsIn"), own.get("socialAt")),
        PAT in (own.get("friendsIn") or []) and (own.get("socialAt") or 0) > now_ms - 600000, own.get("friendsIn"))
    chk("(A) no page errors in Fire Code", not errs, errs[:3])
    state = ctx.storage_state()
    cloud_a = cl
    ctx.close()

    # ---------------- (B) the same device, back in the academy ----------------
    for o in state.get("origins", []):
        o["localStorage"] = [kv for kv in o.get("localStorage", []) if kv["name"] != "class26e.activeclass"]
    ctx, pg, errs = page(br, None, seed=cloud_a, state=state)
    b = wait_for(pg, "()=>{ const x = { cls: window.NOVA_CLASS, fin: (store.friendsIn||[]).slice(), fout: (store.friendsOut||[]).slice(), fcode: store.friendCode }; return (x.fin.indexOf('%s') >= 0) ? x : null; }" % PAT, tries=15) \
        or pg.evaluate("()=>({ cls: window.NOVA_CLASS, fin: (store.friendsIn||[]).slice(), fout: (store.friendsOut||[]).slice(), fcode: store.friendCode })")
    chk("(B) in the academy, %s (accepted in Fire Code) is a friend and %s (asked in Fire Code) is waiting on them (%s)" % (NAMES[PAT], NAMES[KIM], b),
        b["cls"] == "academy" and PAT in b["fin"] and ALEX in b["fin"] and KIM in b["fout"] and b["fcode"] == MYCODE, b)
    d = pg.evaluate(DOCK_FRIENDS)
    chk("(B) the academy's Friends tab has %s and %s (%s)" % (NAMES[ALEX], NAMES[PAT], [x["name"] for x in d["rows"]]),
        {NAMES[ALEX], NAMES[PAT]} <= set(x["name"] for x in d["rows"]), d)
    rd = pg.evaluate(READ_DM, {"pub": ALEX, "text": "fire code hello 384"})
    chk("(B) the DM sent in Fire Code is in the academy's thread with %s (%s)" % (NAMES[ALEX], rd), rd["room"] == dm(OWNER, ALEX) and rd["has"], rd)
    # the academy saves them to its own account, as it saves everything
    wait_for(pg, "(a)=>{ const d = window.__cloud.progress[a.code]; return !!(d && (d.friendsIn || []).indexOf(a.pat) >= 0); }", {"code": CODE, "pat": PAT}, tries=40)
    cl = pg.evaluate("()=>JSON.parse(JSON.stringify(window.__cloud))")
    acad_doc = cl["progress"].get(CODE) or {}
    chk("(B) the academy saves the friends to its own account (friendsIn %s)" % acad_doc.get("friendsIn"), PAT in (acad_doc.get("friendsIn") or []), acad_doc.get("friendsIn"))
    # a friend added here, in the academy
    pg.evaluate("()=>{ try{ if(chatRoomCode) closeChatRoom(); }catch(e){} }")
    m = pg.evaluate(MANAGE)
    pg.evaluate("""async (code)=>{ const inp = document.querySelector('#stage .friend-add-input'); if(!inp) return; inp.value = code; inp.dispatchEvent(new Event('input', { bubbles: true }));
        [...document.querySelectorAll('#stage .friend-sect-add button')].find(x => x.textContent === 'Send').click(); await new Promise(r => setTimeout(r, 900)); }""", FCODES[LEE])
    # ...and accepted by them (their row accepts the academy account)
    pg.evaluate("(a)=>{ const r = window.__cloud.leaderboard[a.lee]; r.facc = [a.owner]; }", {"lee": LEE, "owner": OWNER})
    wait_for(pg, "(a)=>{ const d = window.__cloud.progress[a.code]; return !!(d && (d.friendsOut || []).indexOf(a.lee) >= 0); }", {"code": CODE, "lee": LEE}, tries=40)
    cl = pg.evaluate("()=>JSON.parse(JSON.stringify(window.__cloud))")
    acad_doc = cl["progress"].get(CODE) or {}
    chk("(B) a request sent in the academy is saved to its account (friendsOut %s)" % acad_doc.get("friendsOut"), LEE in (acad_doc.get("friendsOut") or []), acad_doc.get("friendsOut"))
    chk("(B) no page errors in the academy", not errs, errs[:3])
    cloud_b = cl
    ctx.close()

    # ---------------- (C) a second device in Fire Code, whose copy of the academy predates all of it ----------------
    ctx, pg, errs = page(br, init("ifc", with_ifc=False), seed=cloud_b)
    c = wait_for(pg, "()=>{ const x = { fin: (store.friendsIn||[]).slice(), fout: (store.friendsOut||[]).slice() }; return (x.fout.indexOf('%s') >= 0 && x.fin.indexOf('%s') >= 0) ? x : null; }" % (LEE, PAT), tries=20) \
        or pg.evaluate("()=>({ fin: (store.friendsIn||[]).slice(), fout: (store.friendsOut||[]).slice() })")
    chk("(C) Fire Code on a second device has the friends changed in the academy and in Fire Code elsewhere (%s)" % c,
        PAT in c["fin"] and ALEX in c["fin"] and LEE in c["fout"] and KIM in c["fout"], c)
    d = wait_for(pg, "async ()=>{ const x = await (%s)(); return x.rows.some(r => r.name === %s) ? x : null; }" % (DOCK_FRIENDS, json.dumps(NAMES[LEE])), tries=8) or pg.evaluate(DOCK_FRIENDS)
    chk("(C) its Friends tab shows %s, who accepted the request sent from the academy (%s)" % (NAMES[LEE], [x["name"] for x in d["rows"]]),
        NAMES[LEE] in [x["name"] for x in d["rows"]] and NAMES[PAT] in [x["name"] for x in d["rows"]], d)
    rd = pg.evaluate(READ_DM, {"pub": ALEX, "text": "fire code hello 384"})
    chk("(C) and the same thread with %s (%s)" % (NAMES[ALEX], rd["has"]), rd["has"], rd)
    pg.wait_for_timeout(1500)
    ws = writes_of(pg)
    bad = foreign(ws, ["progress/" + CODE + "__ifc", "vrooms/"])
    cl = pg.evaluate("()=>JSON.parse(JSON.stringify(window.__cloud))")
    chk("(C) and writes nothing to progress/%s or the leaderboard (%s)" % (CODE, sorted(set(bad))),
        not bad and cl["progress"].get(CODE) == cloud_b["progress"].get(CODE) and cl["leaderboard"] == cloud_b["leaderboard"], sorted(set(ws)))
    chk("(C) no page errors on the second device", not errs, errs[:3])
    ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
