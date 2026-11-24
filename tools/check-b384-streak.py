#!/usr/bin/env python3
"""384 streak: the daily check-in streak. Madison: "Let's also add a feature to keep bringing people back. Perhaps on your profile
now there will be a fire thing for streak and it has a thing for how many days you've studied. You now get xp for every day you log
in. It will show up on the main menu and shoot to your profile thing. When you click it in profile it will show like a thing on how
you get it, 3 days in a row is 100 xp, 7 days is 200 14 is 500?"
Drives the real page (iPhone 17 Pro Max 440x956, installed) with the clock moved (Date shimmed from localStorage "__fakeNow", set
before each load) and an in-memory Firestore that survives a reload (sessionStorage), so a "day" is a reload on a later date. The
daily XP and the ladder are read off the page (CHECKIN_XP, the sheet's ladder), never typed here.
 (1) DAY 1 pays the daily XP once: the account's XP rises by exactly that, the day is in store.checkins, and the account written to
     the cloud carries the day and the XP;
 (2) A RELOAD THE SAME DAY pays nothing and Home says nothing;
 (3) THE THIRD DAY IN A ROW pays the daily XP plus the 3-day bonus (the sheet's first ladder row), once;
 (3b) THE 30-DAY MARKS GROW: a run of 29 days (seeded, its earlier bonuses paid) checks in its 30th and is paid the daily XP and the
     sheet's 30-day rung; a run of 59 its 60th, the 60-day rung, which is 2000 and twice the 30-day one (Madison: "a long streak has
     to keep paying more"); the sheet lists the growing amounts;
 (4) A GAP resets the run: a day missed, then a day: the daily XP only, the streak 1, the best kept; and two more days pay the 3-day
     bonus AGAIN (a new run);
 (5) THE PROFILE ROW AND SHEET show the derived numbers: the row's streak, total and best; the sheet's Current / Best / Total days,
     the reached rungs marked, the next one lit with its days to go, all of it in sight on the Pro Max (nothing scrolls); the row is a tap target of 44px or more; the sheet is gone
     when the screen changes;
 (6) HOME'S BANNER comes up once on the day's first Home (never with a reward card up), names the streak and the XP, and its flame
     flies to the Profile tab (transform and opacity only, no filter) which bumps; a screen change clears the banner and the chip,
     and Home does not show it again that day; under Reduce motion it fades with no flight;
 (7) TWO DEVICES, ONE DAY: both open the account on the same day before either has heard of the other, both pay; when each hears
     the other's account the XP is in ONCE (and a test's XP played on one of them still adds), on both devices and in the cloud;
 (8) FIRE CODE has its own: its store and its cloud document get the day, the academy's store does not; its Profile has the row;
 (9) no page errors.
Run:  python3 tools/check-b384-streak.py   (--against OLD/index.html must FAIL)"""
import datetime, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b384streak"}
exec(src, G)
g = G["g"]
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = g["INSET_RE"]
    def _old(ins):
        t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
        return IR.sub(lambda m: v[m.group(1)], OLD)
    g["patched"] = _old
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:500], flush=True)
CODE = G["CODE"]
# a Firestore stand-in (check-b383-ifcsync's) that keeps its documents across a reload of the tab, and can be handed a document
# "from the server" (__cloudPut: set and tell the listeners, as another device's write would)
FAKE = r"""(()=>{
  let kept = null; try{ kept = JSON.parse(sessionStorage.getItem('__cloud') || 'null'); }catch(e){}
  const seed = window.__cloudSeed || {};
  const C = window.__cloud = kept || { progress: {}, leaderboard: {}, vrooms: {} }; window.__writes = [];
  if(!kept) Object.keys(seed).forEach(c => { C[c] = Object.assign(C[c] || {}, seed[c]); });
  const keep = () => { try{ sessionStorage.setItem('__cloud', JSON.stringify(C)); }catch(e){} };
  const subs = {};
  const clone = v => v == null ? v : JSON.parse(JSON.stringify(v));
  const snap = (c, id) => { const d = (C[c] || {})[id]; return { id, exists: d !== undefined, data: () => clone(d), metadata: { fromCache: false, hasPendingWrites: false } }; };
  const fire = (c, id) => (subs[c + '/' + id] || []).forEach(f => setTimeout(() => f(snap(c, id)), 15));
  window.__cloudPut = (c, id, v) => { (C[c] = C[c] || {}); C[c][id] = clone(v); keep(); fire(c, id); };
  const doc = (c, id) => ({ id,
    get: () => Promise.resolve(snap(c, id)),
    set: (v, o) => { (C[c] = C[c] || {}); C[c][id] = (o && o.merge) ? Object.assign({}, C[c][id] || {}, clone(v)) : clone(v); __writes.push(c + '/' + id); keep(); fire(c, id); return Promise.resolve(); },
    update: v => { (C[c] = C[c] || {}); C[c][id] = Object.assign({}, C[c][id] || {}, clone(v)); __writes.push(c + '/' + id); keep(); fire(c, id); return Promise.resolve(); },
    delete: () => { if(C[c]) delete C[c][id]; __writes.push('DEL ' + c + '/' + id); keep(); fire(c, id); return Promise.resolve(); },
    onSnapshot: function(){ const a = [...arguments]; const next = a.find(x => typeof x === 'function'); const k = c + '/' + id; (subs[k] = subs[k] || []).push(next); setTimeout(() => next(snap(c, id)), 30); return () => { subs[k] = (subs[k] || []).filter(f => f !== next); }; },
    collection: n => coll(c + '/' + id + '/' + n) });
  const coll = c => { const q = { doc: id => doc(c, id), where(){ return q; }, orderBy(){ return q; }, limit(){ return q; },
    get: () => Promise.resolve({ empty: true, docs: [], forEach(){} }), onSnapshot: function(){ const a=[...arguments]; const next=a.find(x=>typeof x==='function'); setTimeout(()=>next({ empty:true, docs:[], forEach(){}, metadata:{fromCache:false}, docChanges:()=>[] }),30); return ()=>{}; } }; return q; };
  const db = { collection: coll, batch: () => ({ set(){}, update(){}, delete(){}, commit: () => Promise.resolve() }) };
  const fs = () => db; fs.FieldValue = { delete: () => null, serverTimestamp: () => Date.now(), arrayUnion: (...x) => x, increment: n => n }; fs.FieldPath = function(){};
  window.firebase = { apps: [], initializeApp(){ this.apps.push({}); }, firestore: fs };
})()"""
# the clock, moved to localStorage "__fakeNow" (a local date and time) at load, and running on from there
CLOCK = r"""(()=>{ let f = null; try{ f = localStorage.getItem('__fakeNow'); }catch(e){} if(!f) return;
  const RD = Date, off = new RD(f).getTime() - RD.now();
  function D(...a){ if(!(this instanceof D)) return new RD(RD.now() + off).toString(); return a.length ? new RD(...a) : new RD(RD.now() + off); }
  D.prototype = RD.prototype; D.now = () => RD.now() + off; D.parse = RD.parse; D.UTC = RD.UTC; window.Date = D; })()"""
QUIET = "try{ localStorage.setItem('class26e.intro.seen', '99'); localStorage.setItem('class26e.weekrecap.v1','9999-12-31'); localStorage.setItem('class26e.ifc.weekrecap.v1','9999-12-31'); }catch(e){}"
# no reward cards owed on Home (the fixture is owed challenge cards): set once the app's script is in, before Home's queue asks
NOCARDS = "addEventListener('DOMContentLoaded', () => { try{ pendingHomeUnlocks = () => ({ chars: [], banners: [], hints: [], fx: [], finds: [] }); }catch(e){} });"
academy = G["academy"]; ifc = G["ifc"]
base = datetime.date.today() + datetime.timedelta(days=3)
def day(k): return (base + datetime.timedelta(days=k)).isoformat()
def page(br, cls="academy", reduce=False, cards=False, seed_cloud=True, first_day=0, store=None):
    ctx = br.new_context(viewport={"width": 440, "height": 956}, has_touch=True, reduced_motion="reduce" if reduce else "no-preference")
    store = store or (ifc if cls == "ifc" else academy)
    cloud = {"progress": {(CODE + "__ifc" if cls == "ifc" else CODE): store}} if seed_cloud else {}
    ctx.add_init_script("window.__cloudSeed = %s;" % json.dumps(cloud))
    ctx.add_init_script("if(!sessionStorage.getItem('__seeded')) try{ localStorage.setItem('__fakeNow', %s); }catch(e){}" % json.dumps(day(first_day) + "T10:00:00"))
    ctx.add_init_script(CLOCK)
    ctx.add_init_script(FAKE)
    ctx.add_init_script(g["STANDALONE"])
    if cls == "ifc": ctx.add_init_script(G["init"](store, active=cls))
    else:
        keep_ac = G["academy"]
        G["academy"] = store
        try: ctx.add_init_script(G["init"](None, active=cls))
        finally: G["academy"] = keep_ac
    ctx.add_init_script(QUIET)
    if not cards: ctx.add_init_script(NOCARDS)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    body = g["patched"]((59, 0, 34, 0))
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.goto(G["serve_url"]); pg.wait_for_timeout(2500)
    pg.evaluate("document.getElementById('splashscreen')?.remove()")
    return ctx, pg, errs
STATE = """()=>({ pts: store.lifetime.points, days: Array.isArray(store.checkins) ? store.checkins.slice() : null, miles: Array.isArray(store.checkinMiles) ? store.checkinMiles.slice() : null,
  conf: cloudConfirmedFor, xp: typeof CHECKIN_XP === 'number' ? CHECKIN_XP : null,
  info: typeof checkinInfo === 'function' ? checkinInfo(store) : { current: -1, best: -1, total: -1 }, now: new Date().toString().slice(0, 15),
  banner: !!document.getElementById('streak-banner'), fly: !!document.querySelector('.streak-fly') })"""
def state(pg): return pg.evaluate(STATE)
def cloud_doc(pg, id_): return pg.evaluate("(id)=>{ const d = (window.__cloud.progress || {})[id]; return d ? { pts: d.lifetime && d.lifetime.points, days: d.checkins || null, miles: d.checkinMiles || null } : null; }", id_)
def wait(pg, js, ms=9000, arg=None):
    t = 0
    while t < ms:
        if pg.evaluate(js, arg) if arg is not None else pg.evaluate(js): return True
        pg.wait_for_timeout(150); t += 150
    return False
def goto_day(pg, k):
    pg.evaluate("(v)=>localStorage.setItem('__fakeNow', v)", day(k) + "T10:00:00")
    pg.reload(); pg.wait_for_timeout(2500); pg.evaluate("document.getElementById('splashscreen')?.remove()")
# Home's banner, watched from the first frame it is up to the end of its flight: what it said, what moved and how, where it went
WATCH = r"""()=>new Promise(res => {
  const out = { seen: false, text: '', overCard: false, flew: false, props: [], filters: [], pulsed: false, tabHit: null, flightEnd: null };
  const tab = document.getElementById('bottomtab-profile');
  let t0 = performance.now(); const start = t0;
  const tick = () => {
    const b = document.getElementById('streak-banner');
    if(b){ out.seen = true; out.text = out.text || b.textContent; if(document.querySelector('.rs-spot')) out.overCard = true; }
    const f = document.querySelector('.streak-fly');
    if(f){
      out.flew = true;
      document.getAnimations().forEach(a => { const t = a.effect && a.effect.target; if(t && (t === f || f.contains(t))){ try{ a.effect.getKeyframes().forEach(k => Object.keys(k).forEach(p => { if(!['offset','easing','composite','computedOffset'].includes(p) && !out.props.includes(p)) out.props.push(p); })); }catch(e){} } });
      [f, ...f.querySelectorAll('*')].forEach(e => { const fl = getComputedStyle(e).filter; if(fl && fl !== 'none' && !out.filters.includes(fl)) out.filters.push(fl); });
      /* where it is going: its start plus the last keyframe of each of its two moves (across, and up and down) */
      if(!out.flightEnd){ try{
        const c = f.querySelector('.streak-fly-chip');
        const last = el => { const a = el.getAnimations()[0]; const k = a.effect.getKeyframes(); return k[k.length - 1].transform; };
        const x = +/translateX\((-?[\d.]+)px\)/.exec(last(f))[1], y = +/translateY\((-?[\d.]+)px\)/.exec(last(c))[1];
        out.flightEnd = [parseFloat(f.style.left) + x, parseFloat(f.style.top) + y];
        const r = tab.getBoundingClientRect(); out.tabAt = [r.left + r.width / 2, r.top + r.height / 2];
      }catch(e){} }
    }
    /* the tab's bump after this flight (a reward card's flight bumps it too, before) */
    if(out.flew && !f && tab && tab.classList.contains('avatar-pulse')){ out.pulsed = true; const r = tab.getBoundingClientRect(); out.tabHit = [r.left + r.width / 2, r.top + r.height / 2]; }
    if(performance.now() - start > 45000 || (out.pulsed && out.flew)) return res(out);
    if(out.seen && !b && !f && !out.flew){ if(!out.goneAt) out.goneAt = performance.now(); if(performance.now() - out.goneAt > 1500) return res(out); }
    requestAnimationFrame(tick);
  };
  tick();
})"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"], args=["--no-sandbox"])
    errs_all = []

    # ---------------- one device, day by day ----------------
    ctx, pg, errs = page(br, cards=True)
    errs_all.append(errs)
    p0 = academy["lifetime"]["points"]
    # (6) the first Home of day 1: the reward cards first, then the banner and its flight (cards tapped through as they come)
    pg.evaluate("window.__w = (" + WATCH + ")()")
    for _ in range(100):
        if pg.evaluate("!!document.getElementById('streak-banner') || !!document.querySelector('.streak-fly')"): break
        if pg.evaluate("!!document.querySelector('.rs-spot.is-up, .rs-spot')"):
            try: pg.mouse.click(220, 600)
            except Exception: pass
        pg.wait_for_timeout(400)
    w = pg.evaluate("window.__w")   # (a promise: waits for the flight's end)
    s1 = state(pg)
    xp = s1["xp"]
    chk("(1) day 1: the daily XP once (XP %s -> %s, +%s; CHECKIN_XP %s), the day in store.checkins %s" % (p0, s1["pts"], (s1["pts"] or 0) - p0, xp, s1["days"]),
        isinstance(xp, int) and xp > 0 and s1["pts"] - p0 == xp and s1["days"] == [day(0)], s1)
    xp = xp if isinstance(xp, int) else -999   # (an older build has none: every sum below then fails, not crashes)
    pg.wait_for_timeout(3500)
    cd = cloud_doc(pg, CODE)
    chk("(1) the account in the cloud carries the day and the XP (%s)" % cd, bool(cd) and cd["days"] == [day(0)] and cd["pts"] == p0 + (xp or 0), cd)
    nums = [int(x.replace(",", "")) for x in re.findall(r"\d[\d,]*", w.get("text") or "")]
    chk("(6) Home's banner came up, not over a reward card, naming the streak and the XP (%r)" % (w.get("text"),),
        w["seen"] and not w["overCard"] and 1 in nums and xp in nums and re.search(r"streak", w["text"] or "", re.I), w)
    tab_c = w.get("tabAt"); end = w.get("flightEnd")
    near = bool(tab_c and end) and abs(tab_c[0] - end[0]) < 40 and abs(tab_c[1] - end[1]) < 40
    chk("(6) its flame flew to the Profile tab (ended at %s, the tab's middle %s) and the tab bumped" % (end and [round(v) for v in end], tab_c and [round(v) for v in tab_c]),
        w["flew"] and w["pulsed"] and near, w)
    chk("(6) the flight moves transform and opacity only (%s), no filter on it (%s)" % (w["props"], w["filters"]),
        w["flew"] and set(w["props"]) <= {"transform", "opacity"} and "transform" in w["props"] and not w["filters"], w)

    # (2) a reload the same day
    pg.reload(); pg.wait_for_timeout(2500); pg.evaluate("document.getElementById('splashscreen')?.remove()")
    seen_again = wait(pg, "()=>!!document.getElementById('streak-banner')", 7000)
    s2 = state(pg)
    chk("(2) a reload the same day pays nothing (XP %s, days %s) and Home says nothing (banner: %s)" % (s2["pts"], s2["days"], seen_again),
        s2["conf"] == CODE and s2["pts"] == s1["pts"] and s2["days"] == [day(0)] and not seen_again, s2)

    # (3) days 2 and 3
    goto_day(pg, 1)
    wait(pg, "(d)=>(store.checkins || []).includes(d)", 9000, day(1))
    s3a = state(pg)
    chk("(3) day 2: the daily XP (+%s), the streak 2" % (s3a["pts"] - s2["pts"]), s3a["pts"] - s2["pts"] == xp and s3a["info"]["current"] == 2, s3a)
    goto_day(pg, 2)
    wait(pg, "(d)=>(store.checkins || []).includes(d)", 9000, day(2))
    pg.wait_for_timeout(600)
    s3 = state(pg)
    # the ladder, off the sheet
    pg.evaluate("showProfile()"); pg.wait_for_timeout(1200)
    pg.evaluate("document.querySelector('#stage .pf-streak')?.click()"); pg.wait_for_timeout(700)
    ladder = pg.evaluate("""()=>[...document.querySelectorAll('.streak-sheet .streak-step')].map(li => ({ days: +li.dataset.days,
        xp: +((li.querySelector('.streak-step-xp') || {}).textContent || '').replace(/[^0-9]/g, ''), reached: li.classList.contains('is-reached'),
        next: li.classList.contains('is-next'), togo: (li.querySelector('.streak-step-togo') || {}).textContent || '' }))""")
    first = ladder[0] if ladder else None
    chk("(3) day 3: the daily XP and the %s-day bonus (+%s = %s + %s), once (%s)" % (first and first["days"], s3["pts"] - s3a["pts"], xp, first and first["xp"], s3["miles"]),
        bool(first) and first["days"] == 3 and s3["pts"] - s3a["pts"] == xp + first["xp"] and s3["miles"] == [day(0) + "/3"], {"s3": s3, "ladder": ladder})
    first = first or {"days": -1, "xp": -999}
    pg.keyboard.press("Escape")
    pg.evaluate("document.querySelectorAll('.invite-overlay').forEach(o => o.remove())")
    pg.reload(); pg.wait_for_timeout(4500); pg.evaluate("document.getElementById('splashscreen')?.remove()")
    s3r = state(pg)
    chk("(3) ...and a reload that day pays it again: no (XP %s)" % s3r["pts"], s3r["pts"] == s3["pts"] and s3r["miles"] == s3["miles"], s3r)

    # (4) a gap: day 4 missed, day 5
    goto_day(pg, 4)
    wait(pg, "(d)=>(store.checkins || []).includes(d)", 9000, day(4))
    pg.wait_for_timeout(600)
    s4 = state(pg)
    chk("(4) after a missed day: the daily XP only (+%s), the streak back to 1, the best kept at 3, 4 days in all (%s)" % (s4["pts"] - s3["pts"], s4["info"]),
        s4["pts"] - s3["pts"] == xp and s4["info"]["current"] == 1 and s4["info"]["best"] == 3 and s4["info"]["total"] == 4, s4)
    goto_day(pg, 5)
    wait(pg, "(d)=>(store.checkins || []).includes(d)", 9000, day(5))
    goto_day(pg, 6)
    wait(pg, "(d)=>(store.checkins || []).includes(d)", 9000, day(6))
    pg.wait_for_timeout(600)
    s6 = state(pg)
    chk("(4) a new run of 3 pays the 3-day bonus again (+%s over the two days, bonuses %s)" % (s6["pts"] - s4["pts"], s6["miles"]),
        s6["pts"] - s4["pts"] == 2 * xp + first["xp"] and s6["miles"] == [day(0) + "/3", day(4) + "/3"] and s6["info"]["current"] == 3, s6)

    # (5) Profile: the row and the sheet, on day 7 of the calendar (streak 3, best 3, 6 days)
    info = s6["info"]
    pg.evaluate("document.querySelectorAll('#streak-banner, .streak-fly').forEach(e => e.remove())")
    pg.evaluate("showProfile()"); pg.wait_for_timeout(1400)
    row = pg.evaluate("""()=>{ const b = document.querySelector('#stage .pf-streak'); if(!b) return null; const r = b.getBoundingClientRect();
        return { h: r.height, w: r.width, text: b.textContent, flame: !!b.querySelector('.streak-flame'), inCard: !!b.closest('.profile-hero') }; }""")
    rn = [int(x.replace(",", "")) for x in re.findall(r"\d[\d,]*", (row or {}).get("text", ""))]
    chk("(5) Profile's row in the person card: the flame, the streak %s and the %s days (%r), %sx%s" % (info["current"], info["total"], row and row["text"], row and round(row["w"]), row and round(row["h"])),
        bool(row) and row["flame"] and row["inCard"] and row["h"] >= 44 and info["current"] in rn and info["total"] in rn, row)
    pg.evaluate("document.querySelector('#stage .pf-streak')?.click()"); pg.wait_for_timeout(700)
    sh = pg.evaluate("""()=>{ const s = document.querySelector('.streak-sheet'); if(!s) return null;
        const st = {}; s.querySelectorAll('.streak-stat').forEach(c => { st[c.dataset.k] = +c.querySelector('.streak-stat-num').textContent.replace(/[^0-9]/g, ''); });
        const steps = [...s.querySelectorAll('.streak-step')].map(li => ({ days: +li.dataset.days, reached: li.classList.contains('is-reached'), next: li.classList.contains('is-next'),
          togo: +(((li.querySelector('.streak-step-togo') || {}).textContent || '').match(/(\\d+) days? to go/) || [0, -1])[1] }));
        const r = s.getBoundingClientRect(); return { st, steps, inside: r.top >= 0 && r.bottom <= innerHeight + .5 && s.scrollHeight <= s.clientHeight + 1, text: s.textContent }; }""")
    vals = sorted((sh or {}).get("st", {}).values())
    nxt = [x for x in (sh or {}).get("steps", []) if x["next"]]
    reached = [x["days"] for x in (sh or {}).get("steps", []) if x["reached"]]
    chk("(5) the sheet: current %s, best %s, total %s (%s); reached %s; next %s" % (info["current"], info["best"], info["total"], sh and sh["st"], reached, nxt),
        bool(sh) and len(sh["st"]) == 3 and vals == sorted([info["current"], info["best"], info["total"]])
        and reached == [x["days"] for x in sh["steps"] if x["days"] <= info["current"]] and len(nxt) == 1 and nxt[0]["togo"] == nxt[0]["days"] - info["current"]
        and re.search(r"\b%d\b" % xp, sh["text"]) and sh["inside"], sh)
    pg.evaluate("showHome()"); pg.wait_for_timeout(700)
    chk("(5) the sheet is gone when the screen changes", pg.evaluate("!document.querySelector('.streak-sheet, .invite-overlay')"))

    # (6) day 8: the banner, then a screen change while it is up; Home does not say it again
    goto_day(pg, 7)
    up = wait(pg, "()=>!!document.getElementById('streak-banner')", 12000)
    pg.evaluate("document.getElementById('bottomtab-profile').click()"); pg.wait_for_timeout(500)
    gone = pg.evaluate("!document.getElementById('streak-banner') && !document.querySelector('.streak-fly')")
    pg.evaluate("document.getElementById('bottomtab-home').click()")
    again = wait(pg, "()=>!!document.getElementById('streak-banner')", 7000)
    chk("(6) a screen change clears the banner (up %s, gone %s), and Home does not show it again that day (%s)" % (up, gone, again), up and gone and not again)
    ctx.close()

    # (6) Reduce motion: the banner, no flight
    ctx, pg, errs = page(br, reduce=True)
    errs_all.append(errs)
    w = pg.evaluate("(" + WATCH + ")()")
    chk("(6) Reduce motion: the banner comes up (%s) and goes with no flight (%s)" % (w["seen"], w["flew"]), w["seen"] and not w["flew"], w)
    ctx.close()

    # ---------------- (3b) the 30-day marks: a seeded run of 29, then of 59 ----------------
    def run_of(n):
        st = json.loads(json.dumps(academy))
        st["checkins"] = [day(k) for k in range(-n, 0)]
        st["checkinMiles"] = [day(-n) + "/" + str(m) for m in (3, 7, 14, 30, 60, 90) if m <= n]
        return st
    paid = {}
    for n in (29, 59):
        ctx, pg, errs = page(br, store=run_of(n))
        errs_all.append(errs)
        wait(pg, "(x)=>(store.checkins || []).includes(x)", 9000, day(0))
        pg.wait_for_timeout(600)
        sN = state(pg)
        pg.evaluate("document.querySelectorAll('#streak-banner, .streak-fly').forEach(e => e.remove())")
        pg.evaluate("showProfile()"); pg.wait_for_timeout(1200)
        pg.evaluate("document.querySelector('#stage .pf-streak')?.click()"); pg.wait_for_timeout(700)
        lad = pg.evaluate("""()=>{ const o = {}; document.querySelectorAll('.streak-sheet .streak-step').forEach(li => { o[li.dataset.days] = +((li.querySelector('.streak-step-xp') || {}).textContent || '').replace(/[^0-9]/g, ''); }); return o; }""")
        paid[n + 1] = (sN["pts"] - academy["lifetime"]["points"] - xp, lad, sN)
        ctx.close()
    b30, lad30, s30 = paid[30]; b60, lad60, s60 = paid[60]
    chk("(3b) day 30 of a run: the daily XP and the sheet's 30-day rung (+%s bonus, the sheet says %s), streak %s" % (b30, lad30.get("30"), s30["info"]["current"]),
        b30 == lad30.get("30") and b30 > 0 and s30["info"]["current"] == 30 and (day(-29) + "/30") in (s30["miles"] or []), [b30, lad30, s30])
    chk("(3b) day 60 of a run: the 60-day rung, 2000 and twice the 30-day one (+%s bonus, the sheet says %s; 30-day %s)" % (b60, lad60.get("60"), b30),
        b60 == lad60.get("60") == 2000 and b60 == 2 * b30 and s60["info"]["current"] == 60, [b60, lad60, s60])
    rungs = sorted((int(k), v) for k, v in lad60.items())
    big = [v for k, v in rungs if k >= 30]
    chk("(3b) the sheet lists the 30-day marks growing (%s)" % rungs, len(big) >= 3 and all(b > a for a, b in zip(big, big[1:])), rungs)

    # ---------------- (7) two devices, one day ----------------
    ctxA, A, eA = page(br); ctxB, B, eB = page(br)
    errs_all += [eA, eB]
    for d in (A, B): wait(d, "(x)=>(store.checkins || []).includes(x)", 9000, day(0))
    A.wait_for_timeout(3500)   # each has written its own copy up
    a1, b1 = state(A), state(B)
    chk("(7) both devices paid the day on their own (%s, %s)" % (a1["pts"] - p0, b1["pts"] - p0), a1["pts"] - p0 == xp and b1["pts"] - p0 == xp, [a1, b1])
    # device B plays a test's worth of XP of its own, then each hears the other's account
    B.evaluate("()=>{ awardXp(300); saveStore(); }"); B.wait_for_timeout(3500)
    docA = A.evaluate("(id)=>window.__cloud.progress[id]", CODE)
    B.evaluate("([id, d])=>__cloudPut('progress', id, d)", [CODE, docA]); B.wait_for_timeout(1500)
    B.evaluate("()=>pushToCloud()"); B.wait_for_timeout(1500)
    docB = B.evaluate("(id)=>window.__cloud.progress[id]", CODE)
    A.evaluate("([id, d])=>__cloudPut('progress', id, d)", [CODE, docB]); A.wait_for_timeout(1500)
    A.evaluate("()=>pushToCloud()"); A.wait_for_timeout(1500)
    a2, b2 = state(A), state(B); ca, cb = cloud_doc(A, CODE), cloud_doc(B, CODE)
    want = p0 + xp + 300
    chk("(7) after each hears the other: the day's XP is in once and the test's adds (want %s: device A %s, device B %s, cloud %s / %s)" % (want, a2["pts"], b2["pts"], ca and ca["pts"], cb and cb["pts"]),
        a2["pts"] == want and b2["pts"] == want and ca and ca["pts"] == want and cb and cb["pts"] == want and a2["days"] == [day(0)] and b2["days"] == [day(0)], [a2, b2, ca, cb])
    # a merge straight from a copy that never heard of the day's payment, the other way round (mergeSameAccount on its own)
    m = A.evaluate("""(p0)=>{ const a = JSON.parse(JSON.stringify(store)), b = JSON.parse(JSON.stringify(store));
        const r1 = mergeSameAccount(a, b), r2 = mergeSameAccount(b, JSON.parse(JSON.stringify(a)));
        return [a.lifetime.points, b.lifetime.points, a.checkins, b.checkins]; }""", p0)
    chk("(7) merging the account with itself changes nothing (%s)" % m, m[0] == want and m[1] == want and m[2] == [day(0)], m)
    ctxA.close(); ctxB.close()

    # ---------------- (8) Fire Code ----------------
    ctx, pg, errs = page(br, cls="ifc")
    errs_all.append(errs)
    wait(pg, "(x)=>(store.checkins || []).includes(x)", 9000, day(0))
    pg.wait_for_timeout(3500)
    s8 = state(pg)
    cdi = cloud_doc(pg, CODE + "__ifc"); cda = cloud_doc(pg, CODE)
    p0i = ifc["lifetime"]["points"]
    chk("(8) Fire Code: its store paid the day (+%s, %s) and its own cloud document has it (%s); the academy's document is untouched (%s)" % (s8["pts"] - p0i, s8["days"], cdi, cda),
        pg.evaluate("window.NOVA_CLASS") == "ifc" and s8["pts"] - p0i == xp and s8["days"] == [day(0)] and cdi and cdi["days"] == [day(0)] and not (cda and cda["days"]), [s8, cdi, cda])
    pg.evaluate("showProfile()"); pg.wait_for_timeout(1400)
    chk("(8) Fire Code's Profile has the row", pg.evaluate("!!document.querySelector('#stage .profile-hero .pf-streak .streak-flame')"))
    ctx.close()

    errs = [e for es in errs_all for e in es]
    chk("(9) no page errors (%d)" % len(errs), not errs, errs[:4])
    br.close()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
