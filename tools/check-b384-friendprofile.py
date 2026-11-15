"""Build 384.115: a friend's profile, from the Leaderboard.

Madison: "When clicking on someone in the leaderboard, if you're friends with them, let's make it so you can visit their profile.
You can see their last activity and when, you can look at their badge case and whatever else?"

The card that opens on a classmate offers View profile when they are a friend. The screen is read-only and is built from the ONE
public document there is for a person - their row on the class's board (`leaderboard/<public id>`; Fire Code's is a field of
vrooms/lb-ifc-v1) - never from their progress document, which is keyed by their sync code. The row gains four fields (bd badges,
la last run, uc characters, ub banners) written in the same write the row already makes.

An in-memory Firestore (the CDN is blocked here; every write is logged by path, every one-shot get is logged), the owner's
account (a made-up code) and made-up classmates. Asserted by shape, read off the page:
 (1) the card: View profile for a friend (and Message beside it, both tap targets >= 44px), nothing new for somebody who is not
     a friend, for yourself, or when the card is not opened from the Leaderboard / Friends screen;
 (2) a friend with a full row: the screen has their banner, name, rank, level and the three numbers; the badge case holds the
     badges they published and only those a class unit matches (an unknown name is dropped), the count agrees; last activity
     says what and when in words; the collection counts; no read at all (their row was already held); Back returns to the board;
 (3) a friend whose row predates the fields: "No recent activity yet", an empty case under their badge count, no collection;
 (4) a friend with no row on the board: one one-shot get, then the answer ("not on the leaderboard") and a second open is cached;
 (5) PUBLISHING: the row carries the four fields (matching this device's own state), nothing else new, no sync code anywhere
     outside the account documents; an account hidden from the rankings writes no row at all;
 (6) COST: a 20-question drill writes no more documents than the build it replaces (origin/main), and none per answer;
 (7) Fire Code: its row carries the same four fields, and its friend's profile opens from its board.

  python3 tools/check-b384-friendprofile.py [--against OLD/index.html] [--baseline OLD/index.html] [--only N,N]
  --against must FAIL (it has no View profile and publishes none of the fields); --baseline is the build the cost is compared with
  (default: origin/main, read with git)."""
import json, os, re, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)

ARGS = sys.argv[1:]
def arg(name):
    return ARGS[ARGS.index(name) + 1] if name in ARGS else None
AGAINST = arg("--against")
ONLY = set((arg("--only") or "").split(",")) - {""}
def wanted(n): return not ONLY or str(n) in ONLY

def _src_of(path):
    return open(path, encoding="utf-8").read()
def make_patched(text):
    def _p(ins, _o=text):
        v = {"top": f"{ins[0]}px", "right": f"{ins[1]}px", "bottom": f"{ins[2]}px", "left": f"{ins[3]}px"}
        return g["INSET_RE"].sub(lambda m: v[m.group(1)], _o)
    return _p

# the in-memory Firestore of check-b384-friends (its FAKE), with every one-shot get logged as window.__reads
_f = open(os.path.join(HERE, "check-b384-friends.py"), encoding="utf-8").read()
_i = _f.index('FAKE = r"""') + len('FAKE = r"""'); _j = _f.index('"""', _i)
FAKE = _f[_i:_j]
_get = "get: () => Promise.resolve(dsnap(c, id)),"
assert FAKE.count(_get) == 1
FAKE = FAKE.replace(_get, "get: () => { (window.__reads = window.__reads || []).push(c + '/' + id); return Promise.resolve(dsnap(c, id)); },")
_qget = "get: () => Promise.resolve(qsnap(c, f)),"
assert FAKE.count(_qget) == 1
FAKE = FAKE.replace(_qget, "get: () => { (window.__reads = window.__reads || []).push(c + '/?'); return Promise.resolve(qsnap(c, f)); },")
# the document a transaction reads is a write's own read, not a profile's: counted apart
_tx = "tx.get = r => Promise.resolve(dsnap(r.__c, r.id));"
assert FAKE.count(_tx) == 1
FAKE = FAKE.replace(_tx, "tx.get = r => { (window.__txreads = window.__txreads || []).push(r.__c + '/' + r.id); return Promise.resolve(dsnap(r.__c, r.id)); };")
# every write's payload, so nothing that leaves the page has to be read back from the stored copy
_wset = "set(c, id, v, o){ C[c] = C[c] || {};"
assert FAKE.count(_wset) == 1
FAKE = FAKE.replace(_wset, "set(c, id, v, o){ (window.__payloads = window.__payloads || []).push(c + '/' + id + ' ' + JSON.stringify(v)); C[c] = C[c] || {};")

OWNER = "fpowner00001"; CODE = "FPTE-0001"; MYCODE = "FPO-384"
ALEX, KIM, LEE, GHOST, ROSA = "fpalex000002", "fpkimm000003", "fplee0000004", "fpghost00005", "fprosa000006"
FCODES = {ALEX: "AXL-384", KIM: "KMW-384", LEE: "LEY-384", ROSA: "RSA-384", OWNER: MYCODE}
NAMES = {ALEX: "Alexis", KIM: "Kimber", LEE: "Leeland", GHOST: "Ghosty", ROSA: "Rosa"}
now_ms = int(time.time() * 1000)
WEEK = g["week_key_now"]()
HOUR = 3600000
BD_ALEX = ["Penal Code", "TCOLE Rules", "Identity Crimes", "Not A Unit <b>x</b>"]
LA_ALEX = {"kind": "drill", "unit": "Penal Code", "units": 1, "pct": 92, "at": now_ms - 2 * HOUR}
UC_ALEX = ["ghost", "grizzly", "alien", "zeus", "marksman", "no-such-character"]
UB_ALEX = ["tests100", "hundos100", "no-such-banner"]

SEEN = ("['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card',"
        "'class26e.getstarted','class26e.frame.ok'].forEach(k=>localStorage.setItem(k, k==='class26e.frame.ok'?'go-live-1':'1'));")

def row(pub, lvl, extra=None):
    r = {"firstName": NAMES.get(pub, "Maddox"), "avatarChar": "ghost", "level": lvl, "badges": 3, "mystery": 0, "hundos": 4, "correct": 120,
         "xp": 2400 + lvl, "tests": 9, "week": WEEK, "weekPoints": 50, "fcode": FCODES.get(pub, MYCODE), "freq": [], "facc": [],
         "lastModified": now_ms - 60000, "banner": ""}
    r.update(extra or {}); return r

def academy_account(optin=True, history=True):
    a = json.loads(g["SEED"].replace("__WEEK__", WEEK))
    a.update({"publicId": OWNER, "firstName": "Maddox", "novaMet": 99, "friendCode": MYCODE, "friendsIn": [ALEX, LEE, GHOST], "friendsOut": [],
              "friendsDeclined": [], "chats": [], "leaderboardOptIn": optin, "lastModified": now_ms - 3600000})
    a.setdefault("novaHeard", {})["@recap"] = 99991231
    if history:
        a["testHistory"] = [
            {"label": "Penal Code", "units": ["Penal Code"], "pct": 88, "elapsedMs": 600000, "playedAt": now_ms - 3 * HOUR, "mode": "drill"},
            {"label": "TCOLE Rules", "units": ["TCOLE Rules"], "pct": 100, "elapsedMs": 400000, "playedAt": now_ms - 30 * HOUR, "mode": "drill"}]
    return a

def cloud0(optin=True, with_rows=True):
    rows = {}
    if with_rows:
        rows = {OWNER: row(OWNER, 23, {"facc": [ALEX, LEE, GHOST], "avatarChar": "ninja"}),
                ALEX: row(ALEX, 40, {"badges": 4, "banner": "tests100", "bd": BD_ALEX, "la": LA_ALEX, "uc": UC_ALEX, "ub": UB_ALEX, "facc": [OWNER]}),
                KIM: row(KIM, 12, {"bd": ["Penal Code"], "la": dict(LA_ALEX, unit="TCOLE Rules"), "uc": ["ghost"], "ub": []}),
                LEE: row(LEE, 31, {"badges": 5, "facc": [OWNER]}),   # a row written before this build: none of the four fields
                ROSA: row(ROSA, 55, {"bd": [], "uc": ["ghost"], "ub": []})}
    return {"progress": {CODE: academy_account(optin)}, "leaderboard": rows,
            "vrooms": {"presence-v1": {"kind": "presence", "p": {ALEX: now_ms - 30000}, "a": {ALEX: "menu"}}}}

def init(optin=True):
    s = "(()=>{ if(sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); " + SEEN
    s += "localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode', '%s'); })()" % (json.dumps(json.dumps(academy_account(optin))), CODE)
    return s

def page(br, text, seed, w=440, h=956, optin=True, scale=1, init_js=None):
    ctx = br.new_context(viewport={"width": w, "height": h}, has_touch=True, device_scale_factor=scale)
    ctx.add_init_script("window.__cloudSeed = %s;" % json.dumps(seed))
    ctx.add_init_script(FAKE)
    ctx.add_init_script(g["STANDALONE"])
    ctx.add_init_script(init_js or init(optin))
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    body = make_patched(text)((59, 0, 34, 0))
    build = re.search(r'const APP_BUILD = "([^"]+)"', text).group(1)
    pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"}, body=json.dumps({"build": build, "force": False, "frameId": ""})))
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.set_default_timeout(180000)
    pg.goto(SERVE_URL, timeout=180000); pg.wait_for_timeout(3800)
    pg.evaluate("document.getElementById('splashscreen')?.remove()")
    return ctx, pg, errs

SRV, SERVE_URL = g["serve"]()

def until(pg, js, arg=None, tries=40, step=300):
    v = None
    for _ in range(tries):
        v = pg.evaluate(js, arg) if arg is not None else pg.evaluate(js)
        if v: return v
        pg.wait_for_timeout(step)
    return v

OPEN_CARD = """async (pub)=>{ const W = ms => new Promise(r => setTimeout(r, ms));
  document.querySelectorAll('.invite-overlay').forEach(o => o.remove());
  const e = (leaderboardRows || []).find(r => r.pub === pub) || (typeof classBoardRows !== 'undefined' && (classBoardRows || []).find(r => r.pub === pub));
  if(!e) return { none: true };
  openPersonSheet(Object.assign({}, e, { boardCls: ART_PAGE })); await W(500);
  const c = document.querySelector('.person-card'); if(!c) return { noCard: true };
  const view = c.querySelector('.person-sheet-view'), msg = c.querySelector('.person-sheet-act:not(.person-sheet-view)');
  const R = el => { if(!el) return null; const r = el.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; };
  return { view: !!view, viewText: view ? view.textContent : null, msgText: msg ? msg.textContent : null, viewBox: R(view), msgBox: R(msg),
           acts: !!c.querySelector('.person-sheet-acts') }; }"""

PROFILE_STATE = """()=>{
  const p = document.querySelector('#stage > .screen-friendprofile'); if(!p) return null;
  const T = s => { const e = p.querySelector(s); return e ? e.textContent.trim() : null; };
  const earned = [...p.querySelectorAll('.fp-case .badge-tile.is-earned')].map(e => e.getAttribute('aria-label'));
  return { name: T('.profile-name-display'), rank: T('.person-card-rankword'), level: T('.fp-level'),
           cells: [...p.querySelectorAll('.person-card-cell')].map(c => c.textContent), banner: !!p.querySelector('.profile-cover.has-banner'),
           activity: T('.fp-act-main'), when: T('.fp-act-when'), caseCount: T('.fp-case .fp-count'), tiles: p.querySelectorAll('.fp-case .badge-tile').length,
           earned, notes: [...p.querySelectorAll('.fp-note')].map(n => n.textContent), hold: !!p.querySelector('.fp-hold'),
           holdRows: [...p.querySelectorAll('.fp-hold-row .fp-count')].map(n => n.textContent), stills: p.querySelectorAll('.fp-char svg').length,
           msg: !!p.querySelector('.fp-msg'), back: !!p.querySelector('.fp-back'), html: p.innerHTML.indexOf('<b>x</b>') >= 0,
           empty: T('.fp-empty .fp-note'), overflowX: document.documentElement.scrollWidth > innerWidth + 1 }; }"""

DRILL = """async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms));
  setInterval(()=>[...document.body.children].forEach(n=>{ if(getComputedStyle(n).position==='fixed' && /challenge complete|character unlocked/i.test(n.textContent||'')) n.remove(); }), 40);
  document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove()); theme.reduceMotion = true; applyTheme();
  const U = topicsIn(QUESTIONS).find(t => QUESTIONS.filter(q => q.topic === t).length >= 20);
  cfg.mode='drill'; cfg.units=[U]; cfg.versions={}; cfg.source='all'; cfg.size=0; cfg.timer='off'; cfg.flashcards=false;
  const ix = QUESTIONS.map((q,i)=>i).filter(i=>QUESTIONS[i].topic===U).slice(0, 20);
  window.__drillStart = (window.__writes||[]).length;
  beginRun(freshOrder(ix), null);
  for(let i = 0; i < 80 && !document.querySelector('.qpanel .choice'); i++) await wait(150);
  let clicks = 0; const n0 = order.length, a0 = (store.lifetime||{}).answered || 0;
  for(let i = 0; i < 60; i++){
    if(document.querySelector('.rs-rewards')) break;
    const p = pos; const r = correctSlot(order[pos]);
    const b = document.querySelector('.qpanel .choice[data-index="' + r + '"]'); if(b){ b.click(); clicks++; }
    await wait(200);
    const n = document.getElementById('nextbtn'); if(n && !n.hidden) n.click();
    for(let k = 0; k < 40; k++){ await wait(60); if(pos !== p || document.querySelector('.rs-rewards')) break; }
  }
  for(let i = 0; i < 80 && !document.querySelector('.rs-rewards'); i++) await wait(150);
  await wait(1500);
  return { results: !!document.querySelector('.rs-rewards'), questions: n0, clicks: clicks, answered: ((store.lifetime||{}).answered || 0) - a0 }; }"""

def drill_writes(br, text):
    """the documents a 20-question drill writes, by path, and when each came (before or after the results)"""
    ctx, pg, errs = page(br, text, cloud0())
    pg.evaluate("()=>{ window.__writes.length = 0; }")
    pg.wait_for_timeout(2500)
    r = pg.evaluate(DRILL)
    ws = pg.evaluate("()=>window.__writes.slice()")
    pay = pg.evaluate("()=>(window.__payloads||[]).slice()")
    ctx.close()
    return r, ws, pay, errs

def run():
    ok = True
    def chk(name, cond, info=""):
        nonlocal ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else ("  -> " + str(info)[:500]), flush=True)
    text = _src_of(AGAINST or os.path.join(ROOT, "index.html"))
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=g["CHROME"])
        if wanted(1) or wanted(2) or wanted(3) or wanted(4) or wanted(5):
            ctx, pg, errs = page(br, text, cloud0())
            pg.wait_for_timeout(1500)
            # ---------- (1) the card ----------
            pg.evaluate("()=>showRankings()"); pg.wait_for_timeout(2500)
            r = pg.evaluate(OPEN_CARD, ALEX)
            chk("(1) a friend's card from the Leaderboard offers View profile beside Message, both at least 44px tall (%s)" % r,
                r.get("view") and r.get("acts") and r["viewBox"][1] >= 44 and r["msgBox"][1] >= 44 and r["msgText"] and r["viewBox"][0] > 100, r)
            k = pg.evaluate(OPEN_CARD, KIM)
            chk("(1) somebody who is not a friend: the card is as it was - no View profile, one action (%s)" % k,
                k.get("view") is False and not k.get("acts") and k.get("msgText"), k)
            s = pg.evaluate(OPEN_CARD, OWNER)
            chk("(1) your own card: no View profile (%s)" % s, s.get("view") is False, s)
            pg.evaluate("()=>{ document.querySelectorAll('.invite-overlay').forEach(o => o.remove()); showHome(); }"); pg.wait_for_timeout(900)
            h = pg.evaluate("""async ()=>{ const e = (leaderboardRows||[]).find(r => r.pub === '%s'); openPersonSheet(Object.assign({}, e, { boardCls: ART_PAGE }));
                await new Promise(r => setTimeout(r, 400)); return { view: !!document.querySelector('.person-sheet-view') }; }""" % ALEX)
            chk("(1) opened from a screen that is not the Leaderboard or Friends (a Virtual Room's card would leave the room): no View profile (%s)" % h, h["view"] is False, h)
            pg.evaluate("()=>{ document.querySelectorAll('.invite-overlay').forEach(o => o.remove()); showRankings(); }"); pg.wait_for_timeout(2000)
            # ---------- (2) a friend with a full row ----------
            pg.evaluate("()=>{ window.__reads = []; }")
            pg.evaluate(OPEN_CARD, ALEX)
            btn = pg.query_selector(".person-sheet-view")
            if btn: btn.click(); pg.wait_for_timeout(1800)
            st = pg.evaluate(PROFILE_STATE)
            units = pg.evaluate("()=>badgeCaseUnits(BADGE_CASES[0])")
            want = [u for u in BD_ALEX if u in units]
            chk("(2) View profile opens a Profile screen for %s with their banner, rank, level and three numbers (%s)" % (NAMES[ALEX], st and {k: st[k] for k in ("name", "rank", "level", "cells", "banner")}),
                bool(st) and st["name"] == NAMES[ALEX] and st["banner"] and st["rank"] and "Level 40" in (st["level"] or "") and len(st["cells"]) == 3, st)
            chk("(2) the badge case is the Badges screen's tray with exactly the published badges a class unit matches (%d of %s); the unknown name is dropped and nothing is drawn as markup" % (len(want), len(units)),
                bool(st) and sorted(a.replace(" Badge, found", "") for a in st["earned"]) == sorted(want) and st["tiles"] == len(units) and not st["html"]
                and st["caseCount"] == "%d of %d" % (len(want), len(units)), st)
            chk("(2) last activity says what and when in words (%s / %s)" % (st and st["activity"], st and st["when"]),
                bool(st) and st["activity"] == "Finished a Drill, Penal Code, 92%" and "Online now" in st["when"] and "2 hours ago" in st["when"], st)
            chk("(2) what they hold: characters and banners as counts of the known ones only, with a few faces (%s, %s stills)" % (st and st["holdRows"], st and st["stills"]),
                bool(st) and st["hold"] and st["holdRows"][0].split(" of ")[0] == "5" and st["holdRows"][1].split(" of ")[0] == "2" and st["stills"] >= 1, st)
            chk("(2) Message and Back are there, and the page does not scroll sideways", bool(st) and st["msg"] and st["back"] and not st["overflowX"], st)
            reads = pg.evaluate("()=>window.__reads.slice()")
            chk("(2) opening it read nothing: their row was already held by the board (%s)" % reads, reads == [], reads)
            pg.click(".fp-back"); pg.wait_for_timeout(1500)
            chk("(2) Back returns to the Leaderboard", pg.evaluate("()=>!!document.querySelector('#stage > .screen-rankings')"))
            # ---------- (3) a row from before the fields ----------
            pg.evaluate(OPEN_CARD, LEE)
            b3 = pg.query_selector(".person-sheet-view")
            if b3: b3.click(); pg.wait_for_timeout(1500)
            st3 = pg.evaluate(PROFILE_STATE)
            chk("(3) a row without the new fields: 'No recent activity yet', an empty case under their badge count, no collection (%s)" % (st3 and {k: st3[k] for k in ("activity", "caseCount", "notes", "hold")}),
                bool(st3) and st3["activity"] == "No recent activity yet" and st3["caseCount"].startswith("5 of") and not st3["earned"] and st3["tiles"] > 0
                and not st3["hold"] and any("next open" in n for n in st3["notes"]), st3)
            chk("(3) the old row's numbers still show (%s)" % (st3 and st3["cells"]), bool(st3) and len(st3["cells"]) == 3 and "2,431" in st3["cells"][0], st3)
            pg.evaluate("()=>{ showRankings(); }"); pg.wait_for_timeout(1500)
            # ---------- (4) a friend with no row: one one-shot get ----------
            pg.evaluate("()=>{ window.__reads = []; }")
            pg.evaluate("""()=>{ showFriendProfile({ pub: '%s', firstName: 'Ghosty' }, { label: 'Leaderboard', go: () => showRankings() }); }""" % GHOST)
            pg.wait_for_timeout(1500)
            st4 = pg.evaluate(PROFILE_STATE)
            r4 = [x for x in pg.evaluate("()=>window.__reads.slice()") if x.startswith("leaderboard/")]
            chk("(4) a friend with no row on the board: one get of their own board document, then the answer (%s, %s)" % (r4, st4 and st4["empty"]),
                r4 == ["leaderboard/" + GHOST] and bool(st4) and "not on the" in (st4["empty"] or "") and not st4["earned"], [r4, st4])
            pg.evaluate("""()=>{ showRankings(); }"""); pg.wait_for_timeout(800)
            pg.evaluate("""()=>{ showFriendProfile({ pub: '%s', firstName: 'Ghosty' }, { label: 'Leaderboard', go: () => showRankings() }); }""" % GHOST)
            pg.wait_for_timeout(900)
            r4b = [x for x in pg.evaluate("()=>window.__reads.slice()") if x.startswith("leaderboard/")]
            chk("(4) opened again: the answer is kept for five minutes, no second read (%s)" % r4b, r4b == ["leaderboard/" + GHOST], r4b)
            chk("(2-4) no page errors", not errs, errs[:3])
            # ---------- (5) publishing ----------
            if wanted(5):
                pg.evaluate("()=>{ showHome(); }"); pg.wait_for_timeout(500)
                mine = pg.evaluate("""()=>{ const r = buildLeaderboardRow(); return { keys: Object.keys(r).sort(), bd: r.bd, la: r.la, uc: r.uc, ub: r.ub,
                  badges: badgesEarnedList(), last: store.testHistory[0] }; }""")
                new = {"bd", "la", "uc", "ub"}
                chk("(5) this device's row carries bd (its badges), la (its last run: kind, unit, pct, when), uc and ub (%s)" % ({k: mine.get(k) for k in ("bd", "la")}),
                    mine.get("bd") == mine["badges"] and bool(mine["bd"]) and mine.get("la") and mine["la"]["kind"] == "drill" and mine["la"]["unit"] == "Penal Code"
                    and mine["la"]["pct"] == 88 and mine["la"]["at"] == mine["last"]["playedAt"] and isinstance(mine.get("uc"), list) and "ghost" in mine["uc"] and isinstance(mine.get("ub"), list), mine)
                pg.evaluate("()=>{ flushLeaderboardRow(); }"); pg.wait_for_timeout(1500)
                cl = pg.evaluate("()=>JSON.parse(JSON.stringify(window.__cloud))")
                pay = pg.evaluate("()=>(window.__payloads||[]).slice()")
                wrow = cl["leaderboard"].get(OWNER) or {}
                old_keys = set(row(OWNER, 1).keys()) | {"accent", "mystery", "rankFloor", "wk", "pwk", "wins", "prevWeek", "prevWeekPoints", "inv", "cinv", "seenAt"}
                extra = sorted(set(wrow.keys()) - old_keys)
                chk("(5) what the device WROTE: the row is in the cloud with those four fields and no other new one (%s)" % extra, set(extra) == new and wrow.get("bd") == mine["bd"], [extra, wrow.get("la")])
                leak = [k for k, v in list(cl["vrooms"].items()) + list(cl["leaderboard"].items()) if CODE in json.dumps(v) or CODE in k]
                leakpay = [p[:60] for p in pay if CODE in p and not p.startswith("progress/")]
                chk("(5) no sync code in any board or rooms document, and none in any payload written outside the account's own (%s %s)" % (leak, leakpay), not leak and not leakpay, [leak, leakpay])
            ctx.close()
        if wanted(5):
            # hidden from the rankings: no row, so none of the four fields leave the device
            ctx, pg, errs = page(br, text, cloud0(optin=False, with_rows=False), optin=False)
            pg.wait_for_timeout(1500)
            pg.evaluate("()=>{ try{ pushLeaderboardRow(); flushLeaderboardRow(); publishNow(); }catch(e){} }"); pg.wait_for_timeout(2500)
            ws = pg.evaluate("()=>window.__writes.slice()"); cl = pg.evaluate("()=>JSON.parse(JSON.stringify(window.__cloud))")
            chk("(5) an account hidden from the rankings writes no row - nothing of the four fields is published (%s)" % [w for w in ws if w.startswith("leaderboard")],
                not [w for w in ws if w.startswith("leaderboard")] and OWNER not in cl["leaderboard"] and not any("fp" in k for k in cl["leaderboard"]), ws)
            ctx.close()
        if wanted(6):
            baseline = arg("--baseline")
            if baseline: btext = _src_of(baseline)
            else: btext = subprocess.run(["git", "show", "origin/main:index.html"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
            nres, nw, npay, nerr = drill_writes(br, text)
            bres, bw, bpay, berr = drill_writes(br, btext)
            def counts(ws):
                out = {}
                for w in ws: out[w] = out.get(w, 0) + 1
                return out
            cn, cb = counts(nw), counts(bw)
            chk("(6) the 20-question drill ran to its results on both builds (%s / %s)" % (nres, bres), nres.get("results") and bres.get("results"), [nres, bres, nerr[:2], berr[:2]])
            over = {k: (cn.get(k, 0), cb.get(k, 0)) for k in cn if cn.get(k, 0) > cb.get(k, 0)}
            chk("(6) it writes no more documents than the build it replaces: this build %s, the baseline %s" % (cn, cb), not over and sum(cn.values()) <= sum(cb.values()), over)
            rowpay = [p for p in npay if p.startswith("leaderboard/")]
            rowb = [p for p in bpay if p.startswith("leaderboard/")]
            chk("(6) the board row is written as often as before and never per answer (%d writes for %s answers; the baseline %d)" % (len(rowpay), nres.get("answered"), len(rowb)),
                len(rowpay) <= len(rowb) and len(rowpay) <= 3 and (nres.get("answered") or 0) >= 15, [len(rowpay), len(rowb), nres])
        if wanted(7):
            acad = academy_account()
            acad["classes"] = ["academy", "ifc"]
            ifc ={k: acad[k] for k in ["firstName", "avatarChar", "publicId", "onboardingComplete", "tourRev", "novaMet", "novaHeard", "weekKey"] if k in acad}
            ifc.update({k: v for k, v in acad.items() if k.startswith("seen")})
            ifc.update({"lifetime": dict(acad["lifetime"], points=4321, correct=777), "leaderboardOptIn": True, "leaderboardOptInChanged": False,
                        "lastModified": now_ms - 1800000, "unitPerfects": {}, "testHistory": []})
            s = "(()=>{ if(sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); " + SEEN
            s += "localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode', '%s');" % (json.dumps(json.dumps(acad)), CODE)
            s += "localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done'); localStorage.setItem('class26e.activeclass','ifc');"
            s += "['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted'].forEach(k=>localStorage.setItem(k,'1'));"
            s += "localStorage.setItem('class26e.ifc.drill.v1', %s); })()" % json.dumps(json.dumps(ifc))
            seed = cloud0()
            seed["progress"][CODE + "__ifc"] = ifc
            ctx, pg, errs = page(br, text, seed, init_js=s)
            pg.wait_for_timeout(2500)
            cls = pg.evaluate("()=>window.NOVA_CLASS")
            units = pg.evaluate("()=>badgeCaseUnits(BADGE_CASES[0])")
            # the Fire Code store holds some badges and one finished run, so its row has something to say
            pg.evaluate("""(u)=>{ store.unitPerfects = {}; u.slice(0, 3).forEach(n => store.unitPerfects[n] = 999);
                store.testHistory = [{ label: u[0], units: [u[0]], pct: 71, elapsedMs: 1000, playedAt: Date.now() - 600000, mode: 'exam' }]; }""", units)
            row7 = pg.evaluate("()=>{ const r = buildClassBoardRow(); return { keys: Object.keys(r), bd: r.bd, la: r.la, uc: r.uc, ub: r.ub, own: badgesEarnedList() }; }")
            chk("(7) Fire Code's own row carries the same four fields from Fire Code's own store (%s)" % {k: row7[k] for k in ("bd", "la")},
                cls == "ifc" and {"bd", "la", "uc", "ub"} <= set(row7["keys"]) and row7["bd"] == row7["own"] and len(row7["bd"]) == 3
                and row7["la"]["kind"] == "exam" and row7["la"]["pct"] == 71 and row7["la"]["unit"] == units[0] and isinstance(row7["uc"], list), row7)
            # a friend's row on Fire Code's board (one document holding every row), read once on opening a profile
            pg.evaluate("""([pub, u, now])=>{ window.__cloud.vrooms['lb-ifc-v1'] = { kind: 'board', cls: 'ifc', rows: { [pub]: { firstName: 'Alexis', avatarChar: 'ghost', level: 20, badges: 2, hundos: 3, correct: 90, xp: 1500, tests: 5,
                banner: '', bd: [u[1], u[2], 'not a chapter'], la: { kind: 'game', units: 4, pct: 64, at: now - 5400000 }, uc: ['ghost'], ub: [] } } }; window.__reads = []; }""", [ALEX, units, now_ms])
            pg.evaluate("()=>{ showFriendProfile({ pub: '%s', firstName: 'Alexis' }, { label: 'Leaderboard', go: () => {} }); }" % ALEX)
            until(pg, "()=>{ const p = document.querySelector('.screen-friendprofile'); return !!(p && p.querySelector('.fp-case')); }")
            st7 = pg.evaluate(PROFILE_STATE)
            r7 = pg.evaluate("()=>window.__reads.slice()")
            chk("(7) Fire Code: the friend's profile reads Fire Code's board document once and shows their badges, last activity and numbers (%s, %s)" % (r7, st7 and {k: st7[k] for k in ("activity", "caseCount")}),
                r7 == ["vrooms/lb-ifc-v1"] and bool(st7) and len(st7["earned"]) == 2 and re.fullmatch(r"Played a Game, 4 \w+, 64%", st7["activity"] or "") is not None and "hours ago" in (st7["when"] or ""),
                [r7, st7])
            pg.evaluate("()=>{ window.__reads = []; showFriendProfile({ pub: '%s', firstName: 'Alexis' }, { label: 'Leaderboard', go: () => {} }); }" % ALEX)
            pg.wait_for_timeout(600)
            chk("(7) opened again: kept, no second read", pg.evaluate("()=>window.__reads.slice()") == [], pg.evaluate("()=>window.__reads.slice()"))
            chk("(7) no page errors in Fire Code", not errs, errs[:3])
            ctx.close()
        br.close()
    print("ALL PASS" if ok else "FAILED", flush=True)
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(run())
