#!/usr/bin/env python3
"""Build 385: Fire Code gets a leaderboard of its own, and Stats moves into Profile.

Madison: "fire code is gonna get the leaderboard. So move stats to profile as a top tab option. The leaderboard for fire code. It will
be an entirely different leaderboard than the academy one. They will look the same but ifc one will only be for the people in the
class. In other words, every class will have their own leaderboard. Different about the fire code one, there won't be a weekly one or
whatever. Just hundos and overall."

With an in-memory Firestore (the CDN is blocked here; check-b384-friends' stand-in: documents, dotted updates, FieldValue, transactions,
listeners, every write logged) holding the academy's rows in `leaderboard` AND a Fire Code board in `vrooms/lb-ifc-v1`, with one person
(Alexis) in both classes under different numbers:

 (1) THE BAR. Fire Code's is Home, Profile, Leaderboard, Settings (Stats' own button is hidden for good), on an iPhone 17 Pro Max, an
     SE 2nd gen and a laptop; the academy's is as it was (Home, Profile, Leaderboard, Calendar).
 (2) PROFILE HAS STATS. Fire Code's Profile has two top tabs, Profile and Stats (no Settings: that is its bar tab), Stats shows the
     Stats content, a swipe across the content goes between them in the buttons' order, Test history comes back to it, and the bar
     lights Profile. The academy's Profile keeps Profile / Stats / Settings.
 (3) THE LEADERBOARD. Exactly two boards - Overall and Hundos, the academy's own two, read off the page - none of this week; the same
     screen as the academy's (the same pieces); each class lists only its own people (Alexis with each class's own numbers); the
     viewer's own row is marked; nothing weekly anywhere on it; an honest empty state.
 (4) THE WRITES. Opted in: one row in `vrooms/lb-ifc-v1` under the public id (nothing weekly, nothing of the friends block, no sync code in
     any document), no write to `leaderboard`; the same state again is not written again; opted out: nothing is written, and an
     opt-out takes the row off (everybody else's row stays); leaving Fire Code from the academy takes it off too.
 (5) NO BUILD ALREADY OUT CAN SEE IT. The previous build (3a6675d), as the academy, listing `leaderboard` and `vrooms` over the very same
     data, draws none of Fire Code's people anywhere (its board, its Friends list), reads nothing of it, and throws nothing.
 (6) SETTINGS. Leaderboard & Privacy is a real switch in Fire Code, naming Fire Code and its two boards; each class is listed
     Shown or Hidden.

Labels are read off the page; shapes are asserted, not strings (the two exceptions are Madison's own words: the empty state names Fire Code).

  python3 tools/check-b384-fcboard.py [--against OLD/index.html] [--shots DIR]     (--against must FAIL)"""
import json, os, os, re, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
ARGV = list(sys.argv)
def arg(n, d=None): return ARGV[ARGV.index(n) + 1] if n in ARGV else d
SHOTS = arg("--shots")
# the stand-in Firestore, the fixtures and the page helper are check-b384-friends'
src = open(os.path.join(HERE, "check-b384-friends.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b384-friends.py"), "__name__": "b385fc"}
exec(src, G)
g = G["g"]
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:500], flush=True)

class section:
    """a part of the run that may not hold together on a build it was not written for (--against): what it raises is a failure, and the run goes on"""
    def __init__(self, name): self.name = name
    def __enter__(self): return self
    def __exit__(self, t, v, tb):
        if v is not None: chk(self.name + ": raised %s: %s" % (t.__name__, v), False)
        return True

PREV = "ca5f8f0"   # the build before this one (main now): what every phone not yet updated runs; 3a6675d and 383 read the same collections the same way
PREV_HTML = subprocess.check_output(["git", "-C", ROOT, "show", PREV + ":index.html"]).decode("utf-8")
OWNER, CODE, ALEX, KIM, PAT, LEE = G["OWNER"], G["CODE"], G["ALEX"], G["KIM"], G["PAT"], G["LEE"]
FIONA, GUS, HALE = "tst385fione01", "tst385gusss02", "tst385haleee03"
now = G["now_ms"]
BOARD = "lb-ifc-v1"
def frow(name, lvl, hundos, **x):
    r = {"firstName": name, "avatarChar": "ghost", "accent": "ink", "level": lvl, "badges": 1, "hundos": hundos, "correct": 100 + lvl, "xp": 900 * lvl,
         "tests": 5, "rankFloor": 0, "banner": "", "lastModified": now - 60000}
    r.update(x); return r
WEEK_KEY = G['WEEK']
FIRE_ONLY = {FIONA: "Fiona", GUS: "Gus", HALE: "Hale"}
FIRE_ROWS = {ALEX: frow("Alexis", 6, 9), FIONA: frow("Fiona", 22, 2), GUS: frow("Gus", 11, 14), HALE: frow("Hale", 3, 0)}
def cloud0(fire=True):
    c = json.loads(json.dumps(G["CLOUD0"]))
    if fire: c["vrooms"][BOARD] = {"kind": "board", "cls": "ifc", "rows": json.loads(json.dumps(FIRE_ROWS))}
    return c
def ifc_copy(opt, changed=False, hundos=5):
    G["ifc"].update({"leaderboardOptIn": opt, "leaderboardOptInChanged": changed})
    G["ifc"]["lifetime"] = dict(G["academy"]["lifetime"], points=4321, correct=777, perfectTests=hundos)
SW_TAPS = """async ()=>{ const w = ms => new Promise(r => setTimeout(r, ms)); document.getElementById('splashscreen')?.remove();
  document.querySelectorAll('#tour-overlay, #tour-tooltip, #nova-intro, .nova-talk, .unlock-card, .rs-spot').forEach(n => n.remove()); return true; }"""
BAR = """()=>[...document.querySelectorAll('.bottomtabs .bottomtab:not(.bottomtab-start)')].filter(b => !b.hidden && b.getBoundingClientRect().width > 0).map(b => ({ id: b.id, label: (b.querySelector('.bottomtab-label')||{}).textContent, r: b.getBoundingClientRect().toJSON() }))"""
def bar(pg):
    pg.wait_for_timeout(300); return pg.evaluate(BAR)
ROWS_OF = """()=>{ const s = document.querySelector('#stage .screen-rankings'); if(!s) return null;
  return { segs: [...s.querySelectorAll(':scope > .navsegment .iconbtn')].map(b => ({ t: b.textContent, on: b.classList.contains('active') })),
    rows: [...s.querySelectorAll('.rank-row[data-pub]')].map(r => ({ pub: r.dataset.pub, name: (r.querySelector('.rank-name')||{}).textContent, me: r.dataset.me === '1',
      txt: r.innerText.replace(/\\s+/g, ' ').trim() })),
    parts: ['.navsegment.profiletabs', '.rank-blurb', '.rank-tools', '.rank-search', '.rank-me-btn', '.rank-rows', '.rank-row-head'].map(q => !!s.querySelector(q)),
    text: s.innerText, podium: !!s.querySelector('.lw-podium'), empty: (s.querySelector('.lb-board-empty')||{}).textContent || null }; }"""
def open_board(pg, key=None):
    pg.evaluate("(k)=>showRankings(k)", key);
    for _ in range(30):
        r = pg.evaluate(ROWS_OF)
        if r and r["rows"]: return r
        pg.wait_for_timeout(300)
    return pg.evaluate(ROWS_OF)
def pick(pg, label):
    pg.evaluate("(l)=>{ const b = [...document.querySelectorAll('#stage .screen-rankings > .navsegment .iconbtn')].find(x => x.textContent === l); if(b) b.click(); }", label)
    pg.wait_for_timeout(900); return pg.evaluate(ROWS_OF)
def new_ctx(br, init, seed, w=440, h=956, html=None):
    """a page of the stand-in cloud; `html` (a build's source) stands in for this build"""
    if html is not None:
        keep = g["patched"]
        INSET = g["INSET_RE"]
        def _p(ins, _o=html):
            v = {"top": "%dpx" % ins[0], "right": "%dpx" % ins[1], "bottom": "%dpx" % ins[2], "left": "%dpx" % ins[3]}
            return INSET.sub(lambda m: v[m.group(1)], _o)
        g["patched"] = _p
        keep_build = G.get("OLD_BUILD"); G["OLD_BUILD"] = re.search(r'const APP_BUILD = "([^"]+)"', html).group(1)   # version.json says what it runs: no update reload
    try:
        ctx, pg, errs = G["page"](br, init, seed=seed)
    finally:
        if html is not None: g["patched"] = keep; G["OLD_BUILD"] = keep_build
    if html is not None:
        # a standing-in build must not be "updated" mid-check (its own build against the repo's version.json is a mismatch, and a forced
        # update reloads the page under the evaluate calls)
        import re as _re
        _m = _re.search(r'const APP_BUILD = "([^"]+)"', html)
        if _m:
            _b = _m.group(1)
            ctx.route("**/version.json*", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps({"build": _b, "note": "", "frameId": "", "frameNote": "", "force": False})))
    if html is not None and os.environ.get('FCB_DEBUG'):
        pg.on('framenavigated', lambda f: print('NAV', f.url[:90], flush=True)); pg.on('console', lambda m: print('CON', m.text[:160], flush=True) if 'eload' in m.text or 'pdate' in m.text else None)
    if (w, h) != (440, 956): pg.set_viewport_size({"width": w, "height": h}); pg.wait_for_timeout(500)
    pg.evaluate(SW_TAPS)
    return ctx, pg, errs
def sync_leak(cl):
    """any document of the two shared collections that carries the sync code (or its Fire Code name) anywhere: key or value"""
    bad = []
    for coll in ("vrooms", "leaderboard"):
        for k, v in cl.get(coll, {}).items():
            s = k + json.dumps(v)
            if CODE in s or CODE.lower() in s.lower(): bad.append(coll + "/" + k)
    return bad

touch_swipe = """async ([from, to, y])=>{ return true; }"""
def cdp_touch(cdp, typ, x=None, y=None):
    cdp.send("Input.dispatchTouchEvent", {"type": typ, "touchPoints": [] if x is None else [{"x": x, "y": y}]})
def swipe(pg, cdp, left=True):
    vw = pg.evaluate("innerWidth"); y = 600
    xa, xb = (vw * .8, vw * .2) if left else (vw * .2, vw * .8)
    cdp_touch(cdp, "touchStart", xa, y)
    for k in range(1, 11): cdp_touch(cdp, "touchMove", xa + (xb - xa) * k / 10, y + k * .3); pg.wait_for_timeout(16)
    cdp_touch(cdp, "touchEnd"); pg.wait_for_timeout(1100)
PROFILE_STATE = """()=>{ const s = document.querySelector('#stage .screen-profile'); if(!s) return null;
  const segs = [...s.querySelectorAll(':scope > .navsegment .iconbtn')].map(b => ({ t: b.textContent, on: b.classList.contains('active') }));
  const shown = q => { const e = s.querySelector(q); return !!e && !e.closest('[hidden]') && e.getBoundingClientRect().width > 0; };
  return { segs, hero: shown('.profile-hero'), stats: shown('.profile-stats-tab'), dots: shown('.stx-dots'), recent: shown('.stx-recent'),
           settings: !!s.querySelector('.profile-settings-tab-btn'), title: (document.getElementById('count')||{}).textContent,
           lit: [...document.querySelectorAll('.bottomtabs .bottomtab.active')].map(b => b.id) }; }"""

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    errs_all = []

    # ================= (1)-(3) Fire Code, an iPhone 17 Pro Max =================
    ifc_copy(True)
    ctx, pg, errs = new_ctx(br, G["init"]("ifc"), cloud0())
    cdp = ctx.new_cdp_session(pg)
    pg.wait_for_timeout(2200)
    b = bar(pg)
    ids = [x["id"] for x in b]
    chk("(1) Fire Code's bar is Home, Profile, Leaderboard, Settings, and Stats' own button is hidden (%s)" % [(x["id"], x["label"]) for x in b],
        ids == ["bottomtab-home", "bottomtab-profile", "bottomtab-rewards", "bottomtab-settings"]
        and all(x["r"]["left"] >= 0 and x["r"]["right"] <= 440 for x in b), b)
    with section('(2) profile tabs'):
        # (2) Profile: two top tabs
        pg.evaluate("()=>showProfile()"); pg.wait_for_timeout(900)
        ps = pg.evaluate(PROFILE_STATE)
        chk("(2) Fire Code's Profile has two top tabs, Profile then Stats (no Settings: that is its bar tab) (%s)" % (ps and ps["segs"]),
            ps and [s["t"] for s in ps["segs"]][0] == "Profile" and len(ps["segs"]) == 2 and re.search(r"stat", ps["segs"][1]["t"], re.I)
            and ps["segs"][0]["on"] and ps["hero"] and not ps["stats"] and not ps["settings"], ps)
        pg.evaluate("()=>{ [...document.querySelectorAll('#stage .screen-profile > .navsegment .iconbtn')][1].click(); }"); pg.wait_for_timeout(1500)
        ps = pg.evaluate(PROFILE_STATE)
        chk("(2) the Stats tab shows the Stats content (the week's study dots, the recent tests), Profile's card goes, the title and the bar say Profile (%s)" % ps,
            ps and ps["segs"][1]["on"] and ps["stats"] and ps["dots"] and ps["recent"] and not ps["hero"] and ps["lit"] == ["bottomtab-profile"], ps)
        swipe(pg, cdp, left=False); ps = pg.evaluate(PROFILE_STATE)
        chk("(2) a swipe right across the content goes back to Profile (%s)" % (ps and ps["segs"]), ps and ps["segs"][0]["on"] and ps["hero"] and not ps["stats"], ps)
        swipe(pg, cdp, left=True); ps = pg.evaluate(PROFILE_STATE)
        chk("(2) a swipe left goes on to Stats, the buttons' order (%s)" % (ps and ps["segs"]), ps and ps["segs"][1]["on"] and ps["stats"] and not ps["hero"], ps)
        swipe(pg, cdp, left=True); ps = pg.evaluate(PROFILE_STATE)
        chk("(2) and a swipe past the last tab stays on it (two tabs, no third)", ps and ps["segs"][1]["on"] and ps["stats"], ps)
    with section('(2) test history and settings'):
        # Test history, and back
        th = pg.evaluate("""async ()=>{ const w = ms => new Promise(r => setTimeout(r, ms)); showTestReviewList(); await w(700);
            const back = document.querySelector('#stage .back-link'); const lit = [...document.querySelectorAll('.bottomtabs .bottomtab.active')].map(b => b.id);
            const t = back ? back.textContent : null; if(back) back.click(); await w(1000);
            const s = document.querySelector('#stage .screen-profile'); return { backText: t, lit, onStats: !!s && !s.querySelector('.profile-stats-tab').closest('[hidden]') }; }""")
        chk("(2) Test history lights Profile, says it goes back to Profile, and goes back to its Stats tab (%s)" % th,
            th["lit"] == ["bottomtab-profile"] and re.search(r"profile", th["backText"] or "", re.I) and th["onStats"], th)
        # Settings: its own bar tab, alone
        pg.evaluate("()=>document.getElementById('bottomtab-settings').click()"); pg.wait_for_timeout(1200)
        st = pg.evaluate("()=>({ settings: !!document.querySelector('#stage .screen-settings'), segs: document.querySelectorAll('#stage .screen-profile > .navsegment').length, lit: [...document.querySelectorAll('.bottomtabs .bottomtab.active')].map(b => b.id) })")
        chk("(2) the Settings tab is Settings alone, lit alone (%s)" % st, st["settings"] and st["segs"] == 0 and st["lit"] == ["bottomtab-settings"], st)
    with section('(3) the leaderboard'):
        # (3) the Leaderboard
        pg.evaluate("()=>document.getElementById('bottomtab-rewards').click()")
        r = None
        for _ in range(30):
            r = pg.evaluate(ROWS_OF)
            if r and r["rows"]: break
            pg.wait_for_timeout(300)
        boards = pg.evaluate("()=>({ fire: rankingBoardsFor().map(b => b.tab), all: RANKING_BOARDS.map(b => b.tab) })")
        chk("(3) Fire Code's Leaderboard has ONE board, Overall - no Hundos (removed at the owner's word: 'Not many people will get any'), none of This Week, and so no pill switcher (%s of %s)" % ([s["t"] for s in r["segs"]], boards["all"]),
            boards["fire"] == ["Overall"] and r["segs"] == [] and boards["all"][0] not in boards["fire"] and "Hundos" not in boards["fire"], (r["segs"], boards))
        names = {x["name"] for x in r["rows"]}
        mine = [x["name"] for x in r["rows"] if x["me"]]
        chk("(3) Overall lists Fire Code's people and only them - Alexis, Fiona, Gus, Hale and the viewer (%s)" % sorted(names),
            names == {"Alexis", "Fiona", "Gus", "Hale", "Maddox"}, names)
        chk("(3) the viewer's own row is marked, once, and is the viewer's (%s)" % mine, mine == ["Maddox"], mine)
        chk("(3) nothing weekly on the board: no last week's podium, no 'week' anywhere in it (%s)" % r["podium"], not r["podium"] and not re.search(r"week", r["text"], re.I), r["text"][:300])
        chk("(3) the screen has the pieces the academy's has bar the switcher: the blurb, search, Find me, the column header",
            all(r["parts"][1:]) and not r["parts"][0], r["parts"])
        hb = pg.evaluate("()=>{ showRankings('hundos'); return { key: rankingsBoardKey }; }"); pg.wait_for_timeout(900)
        chk("(3) a link or stored name for the Hundos board lands on Overall in Fire Code (%s)" % hb["key"], hb["key"] == "overall", hb)
        pg.evaluate("()=>showRankings('overall')"); pg.wait_for_timeout(600)
        # Find me
        fm = pg.evaluate("""async ()=>{ const w = ms => new Promise(r => setTimeout(r, ms)); document.querySelector('.rank-me-btn').click(); await w(500);
            const me = document.querySelector('.rank-row[data-me="1"]'); return { flash: !!me && me.classList.contains('rank-flash'), toast: !!document.querySelector('.daily-alert') }; }""")
        chk("(3) Find me flashes the viewer's own row, with no 'not loaded' notice (%s)" % fm, fm["flash"] and not fm["toast"], fm)
        # the empty state
        emp = pg.evaluate("""()=>{ const d = document.createElement('div'); renderRankingRows(d, [], RANKING_BOARDS.find(b => b.key === 'overall'), {}); return (d.querySelector('.lb-board-empty')||{}).textContent || null; }""")
        chk("(3) a class nobody has joined says so honestly, naming Fire Code (%r)" % emp, bool(emp) and "Fire Code" in emp and "Nobody" in emp, emp)
        # the card of a person
        pg.evaluate("()=>{ showRankings('overall'); }"); pg.wait_for_timeout(900)
        card = pg.evaluate("""async ()=>{ const w = ms => new Promise(r => setTimeout(r, ms)); const row = [...document.querySelectorAll('.rank-row[data-pub]')].find(r => r.querySelector('.rank-name').textContent === 'Gus');
            row.click(); await w(700); const c = document.querySelector('.person-card'); return c ? { name: (c.querySelector('.person-sheet-name')||{}).textContent, txt: c.innerText.replace(/\\s+/g,' ') } : null; }""")
        chk("(3) a tap on a row opens the same person card, with Fire Code's numbers (%s)" % (card and card["txt"][:120]), card and card["name"] == "Gus" and "14" in card["txt"], card)
        pg.evaluate("()=>document.querySelectorAll('.invite-overlay').forEach(n => n.remove())")
        if SHOTS:
            os.makedirs(SHOTS, exist_ok=True)
            pg.evaluate("()=>showRankings('overall')"); pg.wait_for_timeout(1600); pg.screenshot(path=os.path.join(SHOTS, "ifc-promax-leaderboard-overall.png"))
            pg.evaluate("()=>showProfile('stats')"); pg.wait_for_timeout(1800); pg.screenshot(path=os.path.join(SHOTS, "ifc-promax-profile-stats.png"))
    with section('(4) the writes'):
        # (4) the writes of this device (opted in): one row, in the Fire Code board, nothing of the academy's board
        ws = G["writes_of"](pg)
        cl = pg.evaluate("()=>JSON.parse(JSON.stringify(window.__cloud))")
        row = ((cl["vrooms"].get(BOARD) or {}).get("rows") or {}).get(OWNER)
        expect = {"firstName", "avatarChar", "accent", "correct", "level", "badges", "hundos", "rankFloor", "xp", "tests", "banner", "lastModified"}
        chk("(4) opted in: this device's row is in the Fire Code board under its public id, with the numbers the two boards rank on (%s)" % (row and sorted(row)),
            bool(row) and set(row) == expect and row["firstName"] == "Maddox" and row["hundos"] == 5 and row["correct"] == 777, row)
        others = {k: v for k, v in cl["vrooms"][BOARD]["rows"].items() if k != OWNER}
        chk("(4) ...and every other person's row in it is as it was (%s)" % sorted(others), others == FIRE_ROWS or {k: v for k, v in others.items()} == {k: v for k, v in FIRE_ROWS.items()}, others)
        chk("(4) nothing weekly and nothing of the friends block in it (no week, weekPoints, prevWeek*, wk, pwk, fcode, freq, facc, inv, cinv, seenAt)",
            row and not any(k in row for k in ["week", "weekPoints", "prevWeek", "prevWeekPoints", "wk", "pwk", "fcode", "freq", "facc", "inv", "cinv", "seenAt", "mystery"]), row)
        bad = G["foreign"](ws, ["progress/" + CODE + "__ifc", "vrooms/"])
        chk("(4) Fire Code writes only its own account and `vrooms`: nothing to `leaderboard`, nothing to the academy's progress (%s)" % sorted(set(bad)),
            not bad and cl["leaderboard"] == G["ROWS"] and cl["progress"].get(CODE) == G["academy"], sorted(set(ws)))
        leak = sync_leak(cl)
        chk("(4) no sync code in any document of `vrooms` or `leaderboard`, as a key or a value (%s)" % leak, not leak, leak)
        n0 = len([w for w in ws if w == "vrooms/" + BOARD])
        pg.evaluate("()=>{ flushLeaderboardRow(); pushLeaderboardRow(); publishNow(); }"); pg.wait_for_timeout(1200)
        pg.evaluate("()=>{ flushLeaderboardRow(); }"); pg.wait_for_timeout(800)
        n1 = len([w for w in G["writes_of"](pg) if w == "vrooms/" + BOARD])
        chk("(4) the same numbers are not written again - flush, push and put-away change nothing (%d write(s), then %d)" % (n0, n1), n0 == 1 and n1 == n0, (n0, n1))
        # a run: the numbers move, the row follows (the account's write carries it)
        pg.evaluate("()=>{ store.lifetime.perfectTests += 2; store.lifetime.points += 700; store.lifetime.correct += 40; flushLeaderboardRow(); }"); pg.wait_for_timeout(1500)
        row2 = ((pg.evaluate("()=>window.__cloud.vrooms['%s']" % BOARD) or {}).get("rows") or {}).get(OWNER)
        chk("(4) after a run the row says so (hundos %s, xp %s)" % (row2 and row2["hundos"], row2 and row2["xp"]), row2 and row2["hundos"] == 7 and row2["xp"] > row["xp"] and row2["correct"] == 817, row2)
    errs_all += errs
    if SHOTS:
        pg.set_viewport_size({"width": 834, "height": 1194}); pg.wait_for_timeout(700)
        pg.evaluate("()=>showRankings('overall')"); pg.wait_for_timeout(1800); pg.screenshot(path=os.path.join(SHOTS, "ifc-ipad-leaderboard-overall.png"))
        pg.evaluate("()=>showProfile('stats')"); pg.wait_for_timeout(1800); pg.screenshot(path=os.path.join(SHOTS, "ifc-ipad-profile-stats.png"))
    with section('(4) opt out and back in'):
        # opt out in Settings: the row comes off, everybody else's stays
        pg.set_viewport_size({"width": 440, "height": 956}); pg.wait_for_timeout(500)
        pg.evaluate("()=>showAppearance({ page: 'rankings' })"); pg.wait_for_timeout(1200)
        pg.evaluate("()=>{ document.querySelector('#stage input[type=checkbox]').click(); }")
        rows_after = None
        for _ in range(40):
            rows_after = (pg.evaluate("()=>window.__cloud.vrooms['%s']" % BOARD) or {}).get("rows") or {}
            if OWNER not in rows_after: break
            pg.wait_for_timeout(300)
        chk("(4) switched off in Settings, the row comes off the Fire Code board and nobody else's does (%s)" % sorted(rows_after),
            OWNER not in rows_after and set(rows_after) == set(FIRE_ROWS), sorted(rows_after))
        hidden = pg.evaluate("()=>{ showRankings(); return { optout: !!document.querySelector('#stage .is-optout'), boards: document.querySelectorAll('#stage .screen-rankings .navsegment').length }; }")
        chk("(4) ...and the board is hidden from the one who hides, as the academy's is (%s)" % hidden, hidden["optout"] and not hidden["boards"], hidden)
        n_off = len([w for w in G["writes_of"](pg) if w == "vrooms/" + BOARD])
        pg.evaluate("()=>{ store.lifetime.perfectTests += 1; flushLeaderboardRow(); pushLeaderboardRow(); publishNow(); }"); pg.wait_for_timeout(1500)
        n_off2 = len([w for w in G["writes_of"](pg) if w == "vrooms/" + BOARD])
        rows_after = (pg.evaluate("()=>window.__cloud.vrooms['%s']" % BOARD) or {}).get("rows") or {}
        chk("(4) opted out, nothing is published, whatever the run (%d writes, then %d; row there: %s)" % (n_off, n_off2, OWNER in rows_after), n_off2 == n_off and OWNER not in rows_after, rows_after.keys())
        # and on again, from the board's own button
        pg.evaluate("()=>{ document.querySelector('#stage .lb-optout-on').click(); }");
        back = None
        for _ in range(40):
            back = (pg.evaluate("()=>window.__cloud.vrooms['%s']" % BOARD) or {}).get("rows") or {}
            if OWNER in back: break
            pg.wait_for_timeout(300)
        chk("(4) switched on again, the row is back (%s)" % (OWNER in back), OWNER in back, sorted(back))
    chk("(4) no page errors in Fire Code", not errs_all, errs_all[:3])
    ctx.close()

    # ---- the narrow phone and a laptop: the bar and the board fit ----
    for tag, w, h in (("iPhone SE 2nd gen", 375, 667), ("a laptop", 1366, 768)):
        ctx, pg, errs = new_ctx(br, G["init"]("ifc"), cloud0(), w=w, h=h)
        pg.wait_for_timeout(2000)
        b = bar(pg); ids = [x["id"] for x in b]
        chk("(1) %s: the bar is Home, Profile, Leaderboard, Settings, inside the screen (%s)" % (tag, [(x["id"], round(x["r"]["left"]), round(x["r"]["right"])) for x in b]),
            ids == ["bottomtab-home", "bottomtab-profile", "bottomtab-rewards", "bottomtab-settings"] and all(x["r"]["left"] >= 0 and x["r"]["right"] <= w for x in b), b)
        pg.evaluate("()=>document.getElementById('bottomtab-rewards').click()"); pg.wait_for_timeout(1500)
        r = open_board(pg)
        ov = pg.evaluate("()=>({ sx: document.documentElement.scrollWidth - innerWidth })")
        chk("(3) %s: the board is up with its one board (no switcher) and its rows, and the page does not scroll sideways (%s)" % (tag, ov),
            r and len(r["segs"]) == 0 and len(r["rows"]) == 5 and ov["sx"] <= 0, (r and r["segs"], ov))
        pg.evaluate("()=>showProfile('stats')"); pg.wait_for_timeout(1300)
        ps = pg.evaluate(PROFILE_STATE)
        chk("(2) %s: Profile's two tabs, Stats showing (%s)" % (tag, ps and [s["t"] for s in ps["segs"]]), ps and len(ps["segs"]) == 2 and ps["stats"], ps)
        if tag == "a laptop":
            pg.evaluate("()=>showHome()"); pg.wait_for_timeout(1500)
            b = bar(pg)
            chk("(1) the laptop's Home bar is still Home, Profile, Leaderboard, Settings, with Start Studying in the bar beside it (%s)" % [x["id"] for x in b],
                [x["id"] for x in b] == ["bottomtab-home", "bottomtab-profile", "bottomtab-rewards", "bottomtab-settings"], b)
        errs_all += errs; ctx.close()

    # ================= the academy, over the same data: unchanged =================
    ctx, pg, errs = new_ctx(br, G["init"]("academy"), cloud0())
    cdp = ctx.new_cdp_session(pg)
    pg.wait_for_timeout(2200)
    b = bar(pg)
    chk("(1) the academy's bar is as it was: Home, Profile, Leaderboard, Calendar (%s)" % [x["id"] for x in b],
        [x["id"] for x in b] == ["bottomtab-home", "bottomtab-profile", "bottomtab-rewards", "bottomtab-calendar"], b)
    pg.evaluate("()=>showProfile()"); pg.wait_for_timeout(900)
    ps = pg.evaluate(PROFILE_STATE)
    chk("(2) the academy's Profile keeps Profile, Stats and Settings (%s)" % (ps and [s["t"] for s in ps["segs"]]),
        ps and len(ps["segs"]) == 3 and ps["settings"] and re.search(r"stat", ps["segs"][1]["t"], re.I), ps)
    pg.evaluate("()=>showProfile('stats')"); pg.wait_for_timeout(1300)
    ps = pg.evaluate(PROFILE_STATE)
    chk("(2) ...and its Stats tab shows what it showed (%s)" % ps, ps["stats"] and ps["dots"] and ps["recent"] and ps["lit"] == ["bottomtab-profile"], ps)
    r = open_board(pg)
    boards_a = pg.evaluate("()=>RANKING_BOARDS.map(b => b.tab)")
    names = {x["name"] for x in r["rows"]}
    chk("(3) the academy's Leaderboard has its three boards, This Week first (%s)" % [s["t"] for s in r["segs"]], [s["t"] for s in r["segs"]] == boards_a and len(boards_a) == 3, r["segs"])
    chk("(3) ...and lists the academy's people only - not one of Fire Code's (%s)" % sorted(names),
        names == {"Maddox", "Alexis", "Kimber", "Patton", "Leeland"} and not (names & set(FIRE_ONLY.values())), names)
    alex = [x for x in r["rows"] if x["name"] == "Alexis"]
    h = pick(pg, boards_a[2])
    alexh = [x for x in h["rows"] if x["name"] == "Alexis"]
    chk("(3) ...Alexis there with the academy's numbers (4 hundos), not Fire Code's 9 (%s)" % (alexh and alexh[0]["txt"]), alexh and re.search(r"\b4\b", alexh[0]["txt"]) and not re.search(r"\b9\b", alexh[0]["txt"]), alexh)
    wk = pick(pg, boards_a[0])
    chk("(3) ...and This Week is there, as ever (%s)" % (wk and wk["segs"]), wk and wk["segs"][0]["on"] and len(wk["rows"]) >= 1, wk and wk["segs"])
    ws = G["writes_of"](pg)
    chk("(4) the academy never writes Fire Code's board (%s)" % [w for w in ws if BOARD in w], not [w for w in ws if BOARD in w], ws)
    if SHOTS:
        pg.evaluate("()=>showRankings('overall')"); pg.wait_for_timeout(1700); pg.screenshot(path=os.path.join(SHOTS, "academy-promax-leaderboard-overall.png"))
        pg.evaluate("()=>showProfile('stats')"); pg.wait_for_timeout(1700); pg.screenshot(path=os.path.join(SHOTS, "academy-promax-profile-stats.png"))
        pg.set_viewport_size({"width": 834, "height": 1194}); pg.wait_for_timeout(700)
        pg.evaluate("()=>showRankings('overall')"); pg.wait_for_timeout(1800); pg.screenshot(path=os.path.join(SHOTS, "academy-ipad-leaderboard-overall.png"))
    errs_all += errs
    with section('(4) leaving Fire Code'):
        # leaving Fire Code from the academy takes the person's row off Fire Code's board
        pg.set_viewport_size({"width": 440, "height": 956})
        gone = pg.evaluate("""async (pub)=>{ const w = ms => new Promise(r => setTimeout(r, ms));
            // the account is in both classes, and publishes a Fire Code row of its own (written as Fire Code would have)
            window.__cloud.vrooms['%s'].rows[pub] = { firstName: 'Maddox', level: 20, hundos: 5 };
            enrolledClasses = () => ['academy', 'ifc']; setEnrolled = () => true;
            finishLeaveClass('ifc'); await w(900);
            return Object.keys(window.__cloud.vrooms['%s'].rows); }""" % (BOARD, BOARD), OWNER)
        chk("(4) leaving Fire Code (from the academy) takes the person off Fire Code's board, and only them (%s)" % gone, OWNER not in gone and set(gone) == set(FIRE_ROWS), gone)
        ctx.close()

    # ================= (5) THE BUILD BEFORE THIS ONE, over the same data =================
    # it lists `leaderboard` (and `vrooms`, twice: the history seeds and the open-rooms search) and draws what it finds
    ctx, pg, errs = new_ctx(br, G["init"]("academy"), cloud0(), html=PREV_HTML)
    pg.wait_for_timeout(2200)
    build = pg.evaluate("()=>APP_BUILD")
    r = open_board(pg)
    names = {x["name"] for x in r["rows"]}
    chk("(5) build %s (what is on phones now): its Leaderboard lists the academy only - none of Fire Code's people (%s)" % (build, sorted(names)),
        names == {"Maddox", "Alexis", "Kimber", "Patton", "Leeland"} and not (names & set(FIRE_ONLY.values())), names)
    alexh = [x for x in pick(pg, "Hundos")["rows"] if x["name"] == "Alexis"]
    chk("(5) ...Alexis with the academy's own numbers (%s)" % (alexh and alexh[0]["txt"]), alexh and re.search(r"\b4\b", alexh[0]["txt"]) and not re.search(r"\b9\b", alexh[0]["txt"]), alexh)
    seen = pg.evaluate("""async ()=>{ const w = ms => new Promise(r => setTimeout(r, ms));
        // its once-per-account scans of every document in `vrooms`, and its open-rooms search
        store.vrRetroDone = false; store.vrTop3RetroDone = false; let thrown = null;
        try{ seedVroomHistory(); seedVroomTop3(); }catch(e){ thrown = String(e); }
        await w(1200);
        const pubs = (leaderboardRows || []).map(e => e.pub);
        return { thrown, pubs, matches: store.vrMatches || 0, text: document.body.innerText }; }""")
    chk("(5) ...its board data holds none of Fire Code's rows, and its scans of `vrooms` read the board document as nothing (%s)" % {"pubs": len(seen["pubs"]), "thrown": seen["thrown"], "matches": seen["matches"]},
        not seen["thrown"] and not (set(seen["pubs"]) & set(FIRE_ONLY)) and seen["matches"] == 0 and not any(n in seen["text"] for n in FIRE_ONLY.values()), seen["pubs"])
    pg.evaluate("()=>{ showHome(); }"); pg.wait_for_timeout(600)
    try:
        fr = pg.evaluate("""async ()=>{ const w = ms => new Promise(r => setTimeout(r, ms)); try{ showFriends(); }catch(e){ try{ openFriendsFromChat(); }catch(x){} } await w(1500);
            try{ chatDockTab = 'friends'; openChatDock(); }catch(e){} await w(1200); return document.body.innerText; }""")
    except Exception as _e:   # the standing-in build reloaded itself under the call (its own update check against the repo's version.json): look again
        pg.wait_for_timeout(2500)
        fr = pg.evaluate("()=>{ try{ showFriends(); }catch(e){} return document.body.innerText; }")
    chk("(5) ...its Friends screens name none of Fire Code's people", not any(n in fr for n in FIRE_ONLY.values()), fr[:200])
    ws = G["writes_of"](pg)
    chk("(5) ...and it writes nothing to Fire Code's board (%s)" % [w for w in ws if BOARD in w], not [w for w in ws if BOARD in w])
    chk("(5) no page errors in the previous build over this data", not errs, errs[:3])
    ctx.close()
    # and its Fire Code copy, which has no board at all, keeps working over it
    ifc_copy(True)
    ctx, pg, errs = new_ctx(br, G["init"]("ifc"), cloud0(), html=PREV_HTML)
    pg.wait_for_timeout(2200)
    for _try in range(3):   # the standing-in build may reload itself (its update check) under a call: wait and ask again
        try:
            pg.evaluate("()=>showRankings()"); break
        except Exception:
            pg.wait_for_timeout(2500)
    pg.wait_for_timeout(900)
    chk("(5) the previous build's Fire Code copy, over this data, is where it was: Stats on its bar, no board, no errors (%s)" % errs[:2],
        pg.evaluate("()=>!!document.querySelector('#stage .screen-stats')") and not errs, errs)
    ctx.close()

    # THE CONTROL: the same people in `leaderboard` (the naive design - a Fire Code row beside the academy's) are drawn by that build, so
    # the check above is able to see them; what keeps them out is that they are not there
    c = cloud0(fire=False)
    for pub, nm in FIRE_ONLY.items(): c["leaderboard"][pub] = {"firstName": nm, "avatarChar": "ghost", "level": 9, "badges": 1, "hundos": 3, "correct": 120, "week": WEEK_KEY, "weekPoints": 5, "lastModified": now - 60000}
    ctx, pg, errs = new_ctx(br, G["init"]("academy"), c, html=PREV_HTML)
    pg.wait_for_timeout(2200)
    names = {x["name"] for x in open_board(pg)["rows"]}
    chk("(5) the control: put in `leaderboard`, Fire Code's people ARE drawn by that build (%s) - so what keeps them out is where they are (`vrooms`)" % sorted(names),
        set(FIRE_ONLY.values()) <= names, names)
    ctx.close()


    # ================= (4)/(6) opted out from the start; Settings =================
    ifc_copy(False, changed=False)
    ctx, pg, errs = new_ctx(br, G["init"]("ifc"), cloud0())
    # a first launch of this build on a copy somebody hid themselves with is left hidden: the one-shot only moves the copy the first-visit
    # seed wrote (hidden, "changed") - this one is hidden and unchanged, which is a choice the old build could not have written either,
    # so it is also left as it is
    pg.wait_for_timeout(2600)
    ws = G["writes_of"](pg)
    cl = pg.evaluate("()=>JSON.parse(JSON.stringify(window.__cloud))")
    chk("(4) opted out from the start: nothing is written to Fire Code's board, and its rows are as they were (%s)" % [w for w in ws if BOARD in w],
        not [w for w in ws if BOARD in w] and set(cl["vrooms"][BOARD]["rows"]) == set(FIRE_ROWS), ws)
    errs_all += errs; ctx.close()

    ifc_copy(True)
    ctx, pg, errs = new_ctx(br, G["init"]("ifc"), cloud0())
    pg.wait_for_timeout(2000)
    with section('(6) settings'):
        pg.evaluate("()=>showAppearance()"); pg.wait_for_timeout(1200)
        menu = pg.evaluate("()=>{ const r = document.getElementById('settings-row-rankings'); return r ? { value: (r.querySelector('.settings-row-value')||{}).textContent } : null; }")
        chk("(6) Fire Code's Settings has a real Leaderboard & Privacy row, Shown (%s), and not 'Police Academy only'" % menu, menu and menu["value"] == "Shown", menu)
        pg.evaluate("()=>{ enrolledClasses = () => ['academy','ifc']; }")
        pg.evaluate("()=>{ document.getElementById('settings-row-rankings').click(); }"); pg.wait_for_timeout(1000)
        pg_ = pg.evaluate("""()=>({ sw: !!document.querySelector('#stage input[type=checkbox]'), hint: (document.querySelector('#stage .ohint')||{}).textContent || '',
            classes: [...document.querySelectorAll('#stage .settings-lb-class')].map(r => r.querySelector('.otext').firstChild.textContent + '=' + (r.querySelector('input').checked ? 'Shown' : 'Hidden')),
            boards: rankingBoardsFor().map(b => b.tab), text: document.getElementById('stage').innerText })""")
        # (385 r17) the hint explains the per-class switches below the master (check-b384-privacy); the boards a class has are the tabs of its Leaderboard
        chk("(6) its page has the master switch and a hint that explains the class switches (%s); Fire Code has one board" % pg_["hint"][:160],
            pg_["sw"] and "below" in pg_["hint"] and len(pg_["boards"]) == 1 and not re.search(r"week|hundo", pg_["hint"], re.I)
            and not re.search(r"no leaderboard|police academy only", pg_["text"], re.I), pg_)
        chk("(6) ...and lists each class, Shown or Hidden - no 'No leaderboard' (%s)" % pg_["classes"],
            len(pg_["classes"]) == 2 and all(c.split("=")[1] in ("Shown", "Hidden") for c in pg_["classes"]), pg_["classes"])
    errs_all += errs; ctx.close()

    # ================= (7) THE TIPS POINT AT THINGS THAT ARE THERE (check-tours walks the academy only) =================
    ifc_copy(True)
    ctx, pg, errs = new_ctx(br, G["init"]("ifc"), cloud0())
    pg.wait_for_timeout(2200)
    with section("(7) tips"):
        pg.evaluate("()=>showHome()"); pg.wait_for_timeout(1500)
        main = pg.evaluate("""()=>[true, false].flatMap(ret => mainMenuTourSteps(ret).map(s => { const e = document.querySelector(s.target); const r = e ? e.getBoundingClientRect() : null;
            return { target: s.target, text: s.text, shown: !!r && r.width > 0 && r.height > 0 && !e.closest('[hidden]') }; }))""")
        miss = [m["target"] for m in main if not m["shown"]]
        chk("(7) Fire Code's main-menu tips (new and returning) each point at something on screen, and none names a Stats tab on the bar (%s missing of %d)" % (miss, len(main)),
            not miss and not any("bottomtab-stats" in m["target"] for m in main) and any("bottomtab-rewards" in m["target"] for m in main), main)
        pg.evaluate("()=>{ store.seenProfileTour = false; showProfile(); }"); pg.wait_for_timeout(1800)
        tip = pg.evaluate("""()=>{ const e = document.querySelector('.profile-stats-tab-btn'); const r = e ? e.getBoundingClientRect() : null;
            return { shown: !!r && r.width > 0, tour: !!document.querySelector('#tour-tooltip'), text: (document.querySelector('#tour-tooltip')||{}).innerText || '' }; }""")
        chk("(7) Fire Code's Profile has the Stats tab button the Profile tour points at (%s)" % tip, tip["shown"], tip)
        pg.evaluate("()=>document.querySelectorAll('#tour-overlay, #tour-tooltip').forEach(n => n.remove())")
        pg.evaluate("()=>{ store.seenRewardsTour = false; showRankings(); }"); pg.wait_for_timeout(2200)
        rt = pg.evaluate("""()=>({ tour: !!document.querySelector('#tour-tooltip'), text: (document.querySelector('#tour-tooltip')||{}).innerText || '',
            targets: ['.rank-search', '.rank-me-btn'].map(q => !!document.querySelector(q)), noSwitcher: !document.querySelector('.screen-rankings .navsegment') })""")
        chk("(7) the Leaderboard's own tour runs in Fire Code and does not speak of This Week (%s)" % rt, rt["tour"] and all(rt["targets"]) and rt["noSwitcher"] and not re.search(r"this week|26E|hundo", rt["text"], re.I), rt)
    errs_all += errs; ctx.close()

    chk("no page errors", not errs_all, errs_all[:3])
    br.close()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
