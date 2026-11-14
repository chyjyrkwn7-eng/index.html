"""Build 384.120: "Unlocks people notice" - the unlock tracks, the new rims, rarity, and the Leaderboard row's banner and rim.

Asserted by SHAPE and by numbers read off the page (never label strings), in both classes:
 (A) the model: five tracks per class, tiers in order, each existing tier is an item that already exists and is held exactly
     when the app's own check says so (isLockedCharacter / bannerEarned / hundoFxEarned); the new rims need their own count
     AND every earlier tier; a gold rim every tier; Mastery every gold rim; nothing is stored (a second read is the same);
     the published code round-trips (unlockTrackCode / parseUnlockTrackCode);
 (B) PROGRESS SAFETY: for real-shaped accounts (fixtures built from the shape of the live accounts - counters only, made-up
     everything else), every character, banner, theme and hundo effect held on the build this replaces (--baseline, default
     origin/main) is still held on this one, in both classes; Astral's count never needs more than before;
 (C) the Tracks screen: five track cards, each tier a row (>= 44px tall) in order, the held count and the next step match the
     model; Customize opens with a Next up card of at most three, each with a bar whose fill matches have / need;
 (D) rarity: counted from the board rows already held (active in 30 days, publishing `ut`), the share and its band read off the
     card match a count done here; a row older than 30 days or without `ut` is not counted; Fire Code under 20 rows: counts only;
 (E) the row: `ut` and `rim` ride in the row write that already happens (no extra write over a 20-question drill compared with
     the baseline, none per answer), no sync code in any row; the Leaderboard row shows the worn banner along the edge as one
     still picture (no live banner scene in a row), and a rim on the character's plate only when the row's code holds it;
 (F) wearing a rim: only a held rim can be worn; store.rim survives a reload (applyLoadedData default "" for an old copy).
 FOLLOW-UP (Madison's answers to the 384.120 report):
 (G) Fire Code's top hundo effect (id ufo) is no longer called Hazmat anywhere a person reads it - its name, its Tracks row, its
     Customize tile, its unlock card, What's New, the sound descriptions, and every non-comment string in the source - while the
     Marksman character is still the Hazmat (its row says so, and that is the only Hazmat on the Tracks screen);
 (H) the Virtual Room's top tier is a banner (vrtop10): held at 10 first places and not at 9, the tier with it, its row opens its
     banner card; the ultimate (Astral / Zenith) counts it - that banner alone moves the ultimate's count by one - and the
     ultimate's card shows the numbers; the banner is layered, moves only by transform / opacity and has no svg filter; it has
     its tile in Customize. (B) also asserts the ultimate's count grew by exactly that one banner and nobody who held the
     ultimate on the baseline loses it.

  python3 tools/check-b384-unlocks.py [--against OLD/index.html] [--baseline OLD/index.html] [--only A,B] [--real DUMP.json]
--against must FAIL (none of this exists there). --real points at a local, uncommitted read of the live accounts (never in the
repo) to run (B) on every real account as well; without it (B) runs on the real-shaped fixtures here."""
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

_f = open(os.path.join(HERE, "check-b384-friends.py"), encoding="utf-8").read()
_i = _f.index('FAKE = r"""') + len('FAKE = r"""'); _j = _f.index('"""', _i)
FAKE = _f[_i:_j]
_wset = "set(c, id, v, o){ C[c] = C[c] || {};"
assert FAKE.count(_wset) == 1
FAKE = FAKE.replace(_wset, "set(c, id, v, o){ (window.__payloads = window.__payloads || []).push(c + '/' + id + ' ' + JSON.stringify(v)); C[c] = C[c] || {};")

def make_patched(text):
    def _p(ins, _o=text):
        v = {"top": f"{ins[0]}px", "right": f"{ins[1]}px", "bottom": f"{ins[2]}px", "left": f"{ins[3]}px"}
        return g["INSET_RE"].sub(lambda m: v[m.group(1)], _o)
    return _p

OWNER = "unowner00001"; CODE = "UNTE-0001"; MYCODE = "UNO-384"
now_ms = int(time.time() * 1000)
WEEK = g["week_key_now"]()
DAY = 86400000
SEEN = ("['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card',"
        "'class26e.getstarted','class26e.frame.ok'].forEach(k=>localStorage.setItem(k, k==='class26e.frame.ok'?'go-live-1':'1'));")
IFC_SEEN = ("['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card',"
            "'class26e.ifc.getstarted'].forEach(k=>localStorage.setItem(k,'1'));")

def study_log(days, ms_per_day, end_days_ago=1):
    import datetime
    out = {}
    d0 = datetime.date.today() - datetime.timedelta(days=end_days_ago)
    for i in range(days):
        out[(d0 - datetime.timedelta(days=i)).isoformat()] = int(ms_per_day)
    return out

def account(extra=None, ifc=False):
    a = json.loads(g["SEED"].replace("__WEEK__", WEEK))
    a.update({"publicId": OWNER, "firstName": "Maddox", "novaMet": 99, "friendCode": MYCODE, "friendsIn": [], "friendsOut": [],
              "friendsDeclined": [], "chats": [], "leaderboardOptIn": True, "lastModified": now_ms - 3600000})
    a.setdefault("novaHeard", {})["@recap"] = 99991231
    if ifc:
        a = {k: a[k] for k in ["firstName", "avatarChar", "publicId", "onboardingComplete", "tourRev", "novaMet", "novaHeard", "weekKey",
                               "leaderboardOptIn", "lastModified"] if k in a}
        a.update({k: v for k, v in json.loads(g["SEED"].replace("__WEEK__", WEEK)).items() if k.startswith("seen")})
        a.update({"lifetime": {"points": 0, "answered": 0, "correct": 0}, "unitPerfects": {}, "testHistory": [], "leaderboardOptInChanged": False})
    if extra: a.update(extra)
    return a

def init_js(acad, ifc_store=None):
    s = "(()=>{ if(sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); " + SEEN
    s += "localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode', '%s');" % (json.dumps(json.dumps(acad)), CODE)
    if ifc_store is not None:
        s += "localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done'); localStorage.setItem('class26e.activeclass','ifc');"
        s += IFC_SEEN
        s += "localStorage.setItem('class26e.ifc.drill.v1', %s);" % json.dumps(json.dumps(ifc_store))
    return s + " })()"

def page(br, text, seed, init, w=440, h=956, scale=1):
    ctx = br.new_context(viewport={"width": w, "height": h}, has_touch=True, device_scale_factor=scale)
    ctx.add_init_script("window.__cloudSeed = %s;" % json.dumps(seed))
    ctx.add_init_script(FAKE)
    ctx.add_init_script(g["STANDALONE"])
    ctx.add_init_script(init)
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

# made-up classmates on the board: name, character, level, badges, ut (which tiers), rim, banner, days since they were last active
MATES = [
    ("Alexis", "grizzly", 52, 9, "1-1f3f3f3f3f03", "mastery", "exam100", 0),
    ("Kimber", "alien", 47, 8, "1-0f0f1f0f0300", "acc", "hundos100", 1),
    ("Leeland", "ghost", 41, 6, "1-070f0f030100", "ans", "study50", 2),
    ("Rosa", "grizzly", 38, 5, "1-030707030100", "", "vrtop10", 3),   # (follow-up) the Virtual Room's top banner, on a row
    ("Dmitri", "alien", 35, 4, "1-01030f010100", "ans", "", 1),
    ("Priya", "ghost", 30, 3, "1-0103030101", "", "", 4),          # a malformed code: counted as not publishing
    ("Tomas", "grizzly", 27, 2, "1-000101010000", "acc", "", 6),   # a rim the code does not hold: not drawn
    ("Wren", "alien", 24, 2, "1-000103000000", "", "correct5000", 9),
    ("Yusuf", "ghost", 22, 1, "1-000001000000", "", "", 12),
    ("Zara", "grizzly", 21, 1, "1-1f3f3f3f3f03", "mastery", "", 45), # inactive for 45 days: not counted
    ("Omar", "alien", 33, 4, None, "", "tests100", 2),               # a row from before this build: no `ut`
]

def mate_rows(prefix="unmate"):
    rows = {}
    for i, (nm, ch, lv, bd, ut, rim, bn, ago) in enumerate(MATES):
        pub = "%s%05d" % (prefix, i)
        r = {"firstName": nm, "avatarChar": ch, "level": lv, "badges": bd, "mystery": 0, "hundos": 10 + lv, "correct": 120 * lv,
             "xp": 2400 * lv, "tests": lv, "week": WEEK, "weekPoints": 40 * lv, "fcode": "M%02d-384" % i, "freq": [], "facc": [],
             "lastModified": now_ms - ago * DAY - 60000, "seenAt": now_ms - ago * DAY - 60000, "banner": bn}
        if ut is not None: r["ut"] = ut
        if rim: r["rim"] = rim
        rows[pub] = r
    return rows

def rich_store(ifc=False):
    a = account(ifc=ifc)
    a.update({"lifetime": {"points": 60000 if not ifc else 30000, "answered": 7400, "correct": 6200 if not ifc else 1400, "drillPlays": 64,
                           "examPlays": 22, "perfectTests": 141 if not ifc else 104, "currentStreak": 23, "longestStreak": 130 if not ifc else 64,
                           "fullTests": 120 if not ifc else 30},
              "studyLog": study_log(32, 1.25 * 3600000), "dailyCorrectTotal": 12, "hundoDayBest": 3, "vrWins": 3, "vrMatches": 6,
              "friendsBest": 5, "rim": "ans", "banner": "correct5000" if not ifc else "", "leaderboardOptIn": True})
    return a

def fixtures():
    out = {}
    acad = rich_store()
    out["rich_academy"] = ({"progress": {CODE: acad}, "leaderboard": mate_rows()}, init_js(acad))
    a2 = dict(account(), classes=["academy", "ifc"])
    fc = rich_store(ifc=True)
    seed = {"progress": {CODE: a2, CODE + "__ifc": fc}, "leaderboard": {},
            "vrooms": {"lb-ifc-v1": {"kind": "board", "cls": "ifc", "rows": {k: v for k, v in list(mate_rows("unifcm").items())[:8]}}}}
    out["rich_ifc"] = (seed, init_js(a2, fc))
    return out

LOAD_BOARD = """async ()=>{ const W = ms => new Promise(r => setTimeout(r, ms));
  try{ showRankings(); }catch(e){}
  for(let i = 0; i < 60; i++){ const n = window.NOVA_CLASS === 'ifc' ? (classBoardRows || []).length : (leaderboardRows || []).length; if(n >= 3) break; await W(250); }
  await W(600);
  return window.NOVA_CLASS === 'ifc' ? (classBoardRows || []).length : (leaderboardRows || []).length; }"""
def load_board(pg):
    return pg.evaluate(LOAD_BOARD)

# nothing owed on Home: a fixture holds things it was never told about, and their cards would sit over what is measured
QUIET = """()=>{ try{ const u = pendingHomeUnlocks(); markUnlocksShown(u.chars, u.banners, u.fx); (u.hints || []).forEach(markFlareHintShown); }catch(e){}
  try{ homeUnlockPlaying = false; }catch(e){} try{ store.pendingBadgeUnlocks = []; saveStore(); }catch(e){}
  document.querySelectorAll('.rs-spot, .daily-alert, .scene-bridge, #intro-pop, .invite-overlay').forEach(n => n.remove()); }"""
def quiet(pg):
    pg.evaluate(QUIET); pg.wait_for_timeout(400); pg.evaluate(QUIET)

# ---- the gate ----
# REAL-SHAPED ACCOUNTS: the counters the live accounts carry (read 2026-11-14, counts only: the top, the middle and the bottom of
# each, in both classes), with everything that identifies anybody made up. Each is a whole store as the app keeps one.
def shaped(i, correct, hundos, hours, days, run, vrW, vrM, u7, hday, daily, friends, extra=None, ifc=False):
    a = account(ifc=ifc)
    a.update({"lifetime": {"points": correct * 9, "answered": int(correct * 1.2), "correct": correct, "perfectTests": hundos,
                           "longestStreak": run, "currentStreak": run // 3, "fullTests": hundos // 2, "drillPlays": hundos, "examPlays": hundos // 3},
              "studyLog": study_log(days, hours * 3600000 / max(days, 1)), "vrWins": vrW, "vrMatches": vrM, "unitHundoStreakBest": u7,
              "hundoDayBest": hday, "dailyCorrectTotal": daily, "friendsBest": friends, "bestTestStreak": run // 2, "firstName": "Shape%d" % i})
    if extra: a.update(extra)
    return a

def shaped_set(ifc=False):
    if ifc:
        rows = [(1072, 98, 6.6, 9, 149, 1, 2, 10, 3, 4, 2), (602, 13, 4.7, 6, 51, 0, 0, 2, 1, 1, 0), (386, 12, 2.7, 4, 33, 0, 0, 1, 1, 0, 1),
                (40, 0, 0.3, 1, 23, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)]
        extra = [{"bigTest500Passed": True}, {}, {"novaBeaten": True}, {}, {}]
    else:
        rows = [(41758, 169, 134.9, 80, 817, 3, 6, 6, 4, 40, 6), (17721, 147, 116.2, 70, 755, 1, 5, 6, 3, 25, 5), (13125, 130, 86.6, 60, 428, 1, 3, 6, 3, 12, 3),
                (6793, 102, 63.9, 45, 300, 1, 2, 5, 3, 10, 2), (3607, 10, 18.7, 20, 112, 0, 0, 2, 1, 3, 1), (1000, 4, 4.0, 7, 40, 0, 1, 1, 1, 0, 0),
                (40, 0, 0.2, 1, 3, 0, 0, 0, 0, 0, 0)]
        extra = [{"legacyChars": ["clown", "astronaut"], "practiceExamPerfect": True, "rankFloor": 3, "mysteryColorsFound": {"amber": True, "rose": True, "teal": True}},
                 {"bigTest450Passed": True, "weeklyWins": 1, "novaBeaten": True, "lateHundos": 3}, {"rankFloor": 2, "vrHosted": 3},
                 {"retakenQuestions": 140}, {}, {}, {}]
    return [shaped(i, *r, extra=extra[i], ifc=ifc) for i, r in enumerate(rows)]

def real_set(path, ifc):
    try: d = json.load(open(path))
    except Exception: return []
    out = []
    for p in d.get("progress", []):
        if p.get("__floor") or bool(p.get("__ifc")) != ifc: continue
        q = {k: v for k, v in p.items() if not k.startswith("__")}
        if not (q.get("lifetime") or {}).get("points"): continue
        out.append(q)
    return out

HELD = """(fixtures)=>{ const out = [];
  for(const f of fixtures){
    try{ applyLoadedData(JSON.parse(JSON.stringify(f))); }catch(e){ out.push({ err: String(e) }); continue; }
    try{ const u = unlockedIdsNow(); const up = ultimateProgress();
      out.push({ chars: u.chars.slice().sort(), banners: u.banners.slice().sort(), themes: u.themes.slice().sort(), fx: (u.fx || []).slice().sort(),
                 aNeed: up.need, aHave: up.have, ut: typeof unlockTrackCode === 'function' ? unlockTrackCode() : null,
                 vrWins: Number(store.vrWins) || 0, ult: typeof ULTIMATE_TOP === 'string' ? !isLockedCharacter(ULTIMATE_TOP) : null,
                 nBanners: BANNERS.filter(b => b.id !== (typeof ULTIMATE_TOP === 'string' ? ULTIMATE_TOP : '')).length }); }
    catch(e){ out.push({ err: String(e) }); }
  }
  return out; }"""

MODEL = """()=>{ try{
  const v = unlockTrackView();
  const u = unlockedIdsNow();
  const held = { char: new Set(u.chars), banner: new Set(u.banners), fx: new Set(u.fx || []) };
  let agree = 0, disagree = [];
  v.tracks.forEach(t => t.tiers.forEach(x => x.rewards.forEach(r => {
    if(held[r.k]){ if(held[r.k].has(r.id) === !!r.held) agree++; else disagree.push(r.k + ':' + r.id); }
  })));
  const p = parseUnlockTrackCode(unlockTrackCode(v));
  const bitsOk = v.tracks.every((t, i) => t.tiers.every((x, j) => !!(p.tracks[i] & (1 << j)) === x.held));
  const ids = v.tracks.map(t => t.tiers.map(x => x.rewards.map(r => r.k + ':' + r.id).join('+')));
  const before = JSON.stringify(store); unlockTrackView(); unlockNextUp(); const after = JSON.stringify(store);
  return { tiers: v.tracks.map(t => t.tiers.length), keys: v.tracks.map(t => t.key), agree, disagree, bitsOk, ids, stored: before !== after,
           next: v.tracks.map(t => t.next ? t.next.n : 0), firstUnheld: v.tracks.map(t => { const x = t.tiers.find(y => !y.held); return x ? x.n : 0; }),
           exists: v.tracks.every(t => t.tiers.every(x => x.rewards.every(r => r.k === 'rim' || r.k === 'goal' ? true :
              r.k === 'char' ? AVATAR_CHARACTERS.some(c => c.id === r.id) : r.k === 'banner' ? !!bannerDef(r.id) : !!hundoFxDef(r.id)))) };
  }catch(e){ return { err: String(e) }; } }"""

def main():
    from playwright.sync_api import sync_playwright
    text = open(AGAINST or os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    base_path = arg("--baseline")
    btext = open(base_path, encoding="utf-8").read() if base_path else \
        subprocess.run(["git", "show", "origin/main:index.html"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    ok = True
    def chk(name, cond, detail=None):
        nonlocal ok
        print(("PASS " if cond else "FAIL ") + name + ("" if cond or detail is None else "  -> " + str(detail)[:600]), flush=True)
        ok = ok and bool(cond)
    fx = fixtures()
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=g["CHROME"], args=["--no-sandbox"])
        for cls in ("academy", "ifc"):
            seed, init = fx["rich_" + cls]
            ctx, pg, errs = page(br, text, seed, init)
            pg.wait_for_timeout(1200); quiet(pg)
            got_cls = pg.evaluate("()=>window.NOVA_CLASS === 'ifc' ? 'ifc' : 'academy'")
            chk("[%s] the page is that class" % cls, got_cls == cls, got_cls)
            # ---- (A) the model
            if wanted("A"):
                m = pg.evaluate(MODEL)
                want_tiers = [5, 6, 6, 6, 6]
                chk("[%s] (A) five tracks, tier counts %s" % (cls, m.get("tiers")), m.get("tiers") == want_tiers and len(set(m.get("keys") or [])) == 5, m)
                chk("[%s] (A) every existing tier is an item that exists" % cls, m.get("exists") is True, m)
                chk("[%s] (A) each item held exactly when the app's own check holds it (%s agree)" % (cls, m.get("agree")),
                    (m.get("agree") or 0) >= 20 and not m.get("disagree"), m.get("disagree"))
                chk("[%s] (A) the published code says the same tiers" % cls, m.get("bitsOk") is True, m)
                chk("[%s] (A) reading changes nothing stored" % cls, m.get("stored") is False, m)
                chk("[%s] (A) a track's next step is its first tier not held, in order %s" % (cls, m.get("next")),
                    m.get("next") is not None and m.get("next") == m.get("firstUnheld"), m)
                # the rim rule: its own count AND every tier before it (academy: legacy Masked One + Orion's day)
                r = pg.evaluate("""()=>{ try{ const s = JSON.stringify(store);
                    const acc = () => unlockTrackView().tracks[0].tiers[2].held;
                    store.bestTestStreak = 999; store.hundoDayBest = 0; store.legacyChars = []; store.retakenKeys = []; store.retakenQuestions = 0; store.stats = {};
                    const a = acc();
                    store.hundoDayBest = 3; const b = acc();
                    store.legacyChars = ['masked']; store.retakenQuestions = 100;
                    const lockedMasked = isLockedCharacter('masked'); const c = acc();
                    store.bestTestStreak = 1; store.lifetime.longestStreak = 1; store.lifetime.currentStreak = 1; const d = acc();
                    applyLoadedData(JSON.parse(s)); return [a, b, lockedMasked, c, d]; }catch(e){ return String(e); } }""")
                chk("[%s] (A) the Accuracy rim: count alone no, + tier 2 no, + tier 1 yes, the count gone no (%s)" % (cls, r),
                    isinstance(r, list) and r[0] is False and r[1] is False and (r[2] or r[3] is True) and r[4] is False, r)
                full = pg.evaluate("()=>{ try{ return unlockTrackSpec().map(t => (1 << t.tiers.length) - 1); }catch(e){ return null; } }")
                if full:
                    code = "1-" + "".join("%02x" % m_ for m_ in full) + "00"
                    gm = pg.evaluate("""(c)=>[rowHasMastery({ ut: c }), rowRimShown({ ut: c, rim: 'mastery' }), rowRimShown({ ut: c.slice(0, 4) + '00' + c.slice(6), rim: 'mastery' }),
                        rowRimShown({ ut: '1-000000000000', rim: 'ans' }), rowRimShown({ ut: '1-000000010000', rim: 'ans' }), rowRimShown({ ut: 'x', rim: 'ans' })]""", code)
                    chk("[%s] (A) a row's code: Mastery only with every tier, a rim only when held (%s)" % (cls, gm), gm == [True, "mastery", "", "", "ans", ""], gm)
                else:
                    chk("[%s] (A) the track spec exists" % cls, False)
            # ---- (C) the Tracks screen and Next up
            if wanted("C"):
                load_board(pg); quiet(pg)
                s = pg.evaluate("""async ()=>{ const W = ms => new Promise(r => setTimeout(r, ms)); try{
                    showCustomize(); await W(900);
                    const nu = document.querySelector('.trk-nextup'); const rows = nu ? [...nu.querySelectorAll('.trk-tier')] : [];
                    const near = unlockNextUp(unlockTrackView(), 3);
                    const fills = rows.map(r => { const b = r.querySelector('.trk-bar'), f = b && b.querySelector('i'); return b && f ? f.getBoundingClientRect().width / b.getBoundingClientRect().width : -1; });
                    const want = near.map(e => e.need ? Math.min(1, e.have / e.need) : 0);
                    const all = nu && nu.querySelector('.trk-all'); const allH = all ? all.getBoundingClientRect().height : 0;
                    showUnlockTracks(); await W(900);
                    const v = unlockTrackView();
                    const cards = [...document.querySelectorAll('.trk-card[data-track]')];
                    const perCard = cards.map(c => { const rs = [...c.querySelectorAll('.trk-tier')];
                      return { n: rs.map(r => +r.dataset.tier), held: rs.filter(r => r.classList.contains('is-held')).length,
                               next: rs.findIndex(r => r.classList.contains('is-next')) + 1, minH: Math.min(...rs.map(r => r.getBoundingClientRect().height)) }; });
                    const rims = [...document.querySelectorAll('.trk-rim')].map(r => r.getBoundingClientRect());
                    return { nRows: rows.length, near: near.length, fills, want, allH, cards: cards.length, perCard,
                             model: v.tracks.map(t => ({ n: t.tiers.length, held: t.held, next: t.next ? t.next.n : 0 })),
                             rimMin: rims.length ? Math.min(...rims.map(r => Math.min(r.width, r.height))) : 0, rimN: rims.length,
                             rimWant: unlockRimList(v).length + 1 }; }catch(e){ return { err: String(e) }; } }""")
                chk("[%s] (C) Customize: Next up holds at most three, the closest by the model (%s of %s)" % (cls, s.get("nRows"), s.get("near")),
                    0 < (s.get("nRows") or 0) <= 3 and s.get("nRows") == s.get("near"), s)
                chk("[%s] (C) Next up's bars fill to have / need %s ~ %s" % (cls, [round(x, 2) for x in s.get("fills") or []], [round(x, 2) for x in s.get("want") or []]),
                    bool(s.get("fills")) and all(abs(a - b) < .03 for a, b in zip(s.get("fills"), s.get("want"))), s)
                chk("[%s] (C) the way into Tracks is a 44px target (%.1f)" % (cls, s.get("allH") or 0), (s.get("allH") or 0) >= 44, s)
                pc, md = s.get("perCard") or [], s.get("model") or []
                chk("[%s] (C) five track cards" % cls, s.get("cards") == 5 and len(pc) == 5, s)
                chk("[%s] (C) each card's tiers in order, held count and next step as the model says" % cls,
                    len(pc) == 5 and all(c["n"] == list(range(1, m_["n"] + 1)) and c["held"] == m_["held"] and c["next"] == m_["next"] for c, m_ in zip(pc, md)), [pc, md])
                chk("[%s] (C) every tier row >= 44px (%s)" % (cls, [round(c["minH"]) for c in pc]), pc and all(c["minH"] >= 44 for c in pc), pc)
                chk("[%s] (C) the rims: every rim and 'none', each >= 44px (%s, %.0f)" % (cls, s.get("rimN"), s.get("rimMin") or 0),
                    s.get("rimN") == s.get("rimWant") and (s.get("rimMin") or 0) >= 44, s)
            # ---- (D) rarity
            if wanted("D"):
                load_board(pg)
                spec = pg.evaluate("()=>{ try{ return unlockTrackSpec().map(t => t.tiers.length); }catch(e){ return null; } }") or [99, 99, 99, 99, 99]
                mine = pg.evaluate("()=>{ try{ return unlockTrackCode(); }catch(e){ return null; } }")
                rows = list(mate_rows("unifcm").values())[:8] if cls == "ifc" else list(mate_rows().values())
                def count(track, tier):
                    n = k = 0
                    for r in rows + [{"ut": mine, "seenAt": now_ms}]:
                        ut = r.get("ut")
                        if not isinstance(ut, str) or not re.fullmatch(r"1-[0-9a-f]{12}", ut): continue
                        if now_ms - r.get("seenAt", 0) > 30 * DAY: continue
                        n += 1
                        if int(ut[2 + track * 2: 4 + track * 2], 16) & (1 << tier): k += 1
                    return k, n
                k, n = count(0, 2)
                card = pg.evaluate("""async ()=>{ const W = ms => new Promise(r => setTimeout(r, ms)); try{
                    document.querySelectorAll('.invite-overlay').forEach(o => o.remove());
                    showUnlockDetail(rimDetail('acc')); await W(500);
                    const el = document.querySelector('.unlock-card .unlock-card-rarity'); return el ? el.textContent : ''; }catch(e){ return 'ERR ' + e; } }""")
                nums = [int(x) for x in re.findall(r"\d+", card or "")]
                if cls == "ifc":
                    chk("[%s] (D) the Accuracy rim's rarity: %s of %s, counts only under 20 on the board (%r)" % (cls, k, n, card), nums == [k, n], nums)
                else:
                    chk("[%s] (D) the Accuracy rim's rarity: %s of %s (%s%%) counted here; the card %r" % (cls, k, n, round(k / n * 100) if n else 0, card),
                        nums == [k, n, round(k / n * 100)], nums)
                    share = k / n if n else 0
                    band = pg.evaluate("()=>{ try{ return unlockRarity({ track: 0, tier: 2 }); }catch(e){ return null; } }") or {}
                    want_band = "Legendary" if share < .05 else "Rare" if share < .2 else "Uncommon" if share < .5 else "Common"
                    chk("[%s] (D) its band is the share's (%s)" % (cls, band.get("label")), band.get("label") == want_band and band.get("pct") == round(share * 100), band)
                    km, nm = sum(1 for r in rows + [{"ut": mine, "seenAt": now_ms}] if isinstance(r.get("ut"), str) and re.fullmatch(r"1-[0-9a-f]{12}", r["ut"])
                                 and now_ms - r.get("seenAt", 0) <= 30 * DAY and all(int(r["ut"][2 + i * 2:4 + i * 2], 16) == (1 << spec[i]) - 1 for i in range(5))), n
                    mr = pg.evaluate("()=>{ try{ return unlockRarity({ mastery: true }); }catch(e){ return null; } }") or {}
                    chk("[%s] (D) Mastery: %s of %s (the 45-day-old holder not counted)" % (cls, km, nm), mr.get("k") == km and mr.get("n") == nm, mr)
            # ---- (E) the row and the Leaderboard
            if wanted("E"):
                row = pg.evaluate("""()=>{ try{ const r = window.NOVA_CLASS === 'ifc' ? buildClassBoardRow() : buildLeaderboardRow();
                    return { ut: r.ut, rim: r.rim, code: unlockTrackCode(), worn: wornRim(), lazy: ROW_LAZY_FIELDS.indexOf('ut') >= 0 && ROW_LAZY_FIELDS.indexOf('rim') >= 0,
                             json: JSON.stringify(r) }; }catch(e){ return { err: String(e) }; } }""")
                chk("[%s] (E) the row carries ut (this device's code) and rim (the worn one: %r)" % (cls, row.get("rim")),
                    row.get("ut") and row.get("ut") == row.get("code") and row.get("rim") == row.get("worn") == "ans", row)
                chk("[%s] (E) both are lazy fields: they ride with a push, never cause one" % cls, row.get("lazy") is True, row)
                chk("[%s] (E) no sync code in the row" % cls, CODE not in (row.get("json") or CODE) and CODE.split("-")[0] + "-" not in (row.get("json") or ""), row)
                lb = pg.evaluate("""async ()=>{ const W = ms => new Promise(r => setTimeout(r, ms)); try{
                    document.querySelectorAll('.invite-overlay').forEach(o => o.remove());
                    showRankings(); await W(2500);
                    const rows = [...document.querySelectorAll('.screen-rankings .rank-row')];
                    return rows.map(r => { const b = r.querySelector('.lb-row-bnr'); const av = r.querySelector('.rank-avatar-wrap');
                      return { name: (r.querySelector('.rank-name') || {}).textContent, bnr: !!b, still: !!(b && b.classList.contains('is-still-img') && /url\\(/.test(b.style.backgroundImage)),
                               live: b ? b.querySelectorAll('svg').length : 0, rim: av ? (av.dataset.rim || '') : '', ring: av ? av.querySelectorAll(':scope > .lb-rim').length : 0,
                               gold: !!(r.querySelector('.rank-name.is-mastery')) }; }); }catch(e){ return { err: String(e) }; } }""")
                if not isinstance(lb, list): lb = []
                by = {x["name"]: x for x in lb}
                src_rows = list(mate_rows("unifcm").values())[:8] if cls == "ifc" else list(mate_rows().values())
                exp_bnr = {r["firstName"] for r in src_rows if r.get("banner")}
                chk("[%s] (E) every row with a banner shows it along the edge as one still picture, no live scene (%d rows)" % (cls, len(exp_bnr)),
                    bool(lb) and all(by.get(nm_, {}).get("still") and by[nm_]["live"] == 0 for nm_ in exp_bnr) and
                    all(not x["bnr"] for x in lb if x["name"] not in exp_bnr and x["name"] != "Maddox"), [x for x in lb if x["bnr"] or x["name"] in exp_bnr])
                exp_rim = {"Alexis": "mastery", "Kimber": "acc", "Leeland": "ans", "Dmitri": "ans", "Tomas": "", "Rosa": "", "Wren": ""}
                if cls == "academy": exp_rim["Zara"] = "mastery"
                got_rim = {nm_: (by.get(nm_) or {}).get("rim") for nm_ in exp_rim}
                chk("[%s] (E) a rim on the plate only where the row's code holds it %s" % (cls, got_rim),
                    got_rim == exp_rim and all((by.get(nm_) or {}).get("ring") == (1 if exp_rim[nm_] else 0) for nm_ in exp_rim), [got_rim, exp_rim])
                chk("[%s] (E) the gold name for Mastery only" % cls, bool(lb) and {x["name"] for x in lb if x["gold"]} == {nm_ for nm_, v in exp_rim.items() if v == "mastery"}, lb)
            # ---- (F) wearing a rim
            if wanted("F"):
                w = pg.evaluate("""()=>{ try{ const a = []; wearRim('acc_gold'); a.push(store.rim); wearRim('ans'); a.push(store.rim, wornRim());
                    store.rim = 'mastery'; a.push(wornRim()); store.rim = 'ans'; saveStore(); return a; }catch(e){ return String(e); } }""")
                chk("[%s] (F) a rim not held cannot be worn, a held one can, a stored one not held is not worn (%s)" % (cls, w), w == ["", "ans", "ans", ""], w)
                pg.reload(); pg.wait_for_timeout(3800); pg.evaluate("document.getElementById('splashscreen')?.remove()")
                r2 = pg.evaluate("()=>{ try{ const a = [store.rim, wornRim()]; applyLoadedData({ lifetime: {} }); a.push(store.rim); return a; }catch(e){ return String(e); } }")
                chk("[%s] (F) the rim survives a reload; an old copy without one defaults to none (%s)" % (cls, r2), r2 == ["ans", "ans", ""], r2)
            # ---- (G) follow-up: Fire Code's top hundo effect is not "Hazmat" anywhere a person reads it; the character still is
            if wanted("G") and cls == "ifc":
                gq = pg.evaluate("""async ()=>{ const W = ms => new Promise(r => setTimeout(r, ms)); try{
                    document.querySelectorAll('.invite-overlay').forEach(o => o.remove());
                    const out = { fx: (hundoFxDef('ufo') || {}).name || '', ch: AVATAR_DISPLAY_NAME.marksman || '',
                                  notes: JSON.stringify(RELEASE_NOTES), sound: '' };
                    try{ out.sound = Object.values(typeof SND_IFX !== 'undefined' ? SND_IFX : {}).map(x => x && x.desc || '').join(' '); }catch(e){}
                    showUnlockTracks(); await W(900);
                    const rows = [...document.querySelectorAll('.trk-tier')];
                    const v = unlockTrackView();
                    const where = (k, id) => { for(let i = 0; i < v.tracks.length; i++){ const j = v.tracks[i].tiers.findIndex(x => x.rewards.some(r => r.k === k && r.id === id));
                      if(j >= 0) return [v.tracks[i].key, j + 1]; } return null; };
                    const fxAt = where('fx', 'ufo'), chAt = where('char', 'marksman');
                    const rowText = at => { const r = at && document.querySelector('.trk-card[data-track="' + at[0] + '"] .trk-tier[data-tier="' + at[1] + '"]'); return r ? r.textContent : null; };
                    out.fxRow = rowText(fxAt); out.chRow = rowText(chAt);
                    out.tracksText = document.querySelector('#stage') ? document.querySelector('#stage').textContent : '';
                    showCustomize('fx'); await W(900);
                    const tiles = [...document.querySelectorAll('.hfx-opt')];
                    out.fxTiles = tiles.map(t => t.textContent.replace(/\\s+/g, ' ').trim());
                    document.querySelectorAll('.invite-overlay').forEach(o => o.remove());
                    showUnlockDetail(hundoFxDetail('ufo')); await W(500);
                    const card = document.querySelector('.unlock-card'); out.card = card ? card.textContent : null;
                    document.querySelectorAll('.invite-overlay').forEach(o => o.remove());
                    return out; }catch(e){ return { err: String(e) }; } }""")
                hz = lambda s: "hazmat" in (s or "").lower()
                chk("[ifc] (G) the top hundo effect has a name, and it is not Hazmat (%r); the character is still the Hazmat (%r)" % (gq.get("fx"), gq.get("ch")),
                    bool(gq.get("fx")) and not hz(gq.get("fx")) and gq.get("ch") == "Hazmat", gq)
                chk("[ifc] (G) its Tracks row names it, not Hazmat; the character's row says Hazmat",
                    gq.get("fxRow") is not None and gq.get("fx", "?") in gq["fxRow"] and not hz(gq["fxRow"]) and hz(gq.get("chRow")), [gq.get("fxRow"), gq.get("chRow")])
                chk("[ifc] (G) Hazmat appears on the Tracks screen exactly where the character is (%d times)" % (gq.get("tracksText") or "").count("Hazmat"),
                    (gq.get("tracksText") or "").count("Hazmat") == (gq.get("chRow") or "").count("Hazmat") >= 1, gq.get("tracksText", "")[:300])
                fxt = [t for t in gq.get("fxTiles") or [] if gq.get("fx", "?") in t]
                chk("[ifc] (G) Customize's hundo effect page shows it by its name, no Hazmat on the page (%s)" % gq.get("fxTiles"),
                    len(fxt) == 1 and not any(hz(t) for t in gq.get("fxTiles") or []), gq.get("fxTiles"))
                chk("[ifc] (G) its unlock card, What's New and the sound descriptions never call it Hazmat",
                    gq.get("card") and gq.get("fx", "?") in gq["card"] and not hz(gq["card"]) and not hz(gq.get("notes")) and gq.get("fx", "?") in (gq.get("notes") or "")
                    and not re.search(r"hazmat \(fire code\)", (gq.get("sound") or "").lower()), [gq.get("card"), [m.start() for m in re.finditer("Hazmat", gq.get("notes") or "")]])
                # the source: no string the app shows names the effect Hazmat (the only quoted "Hazmat" left is the character's name)
                vis = re.findall(r'"[^"\n]{0,200}?\bHazmat\b[^"\n]{0,200}?"', re.sub(r"/\*.*?\*/", "", text, flags=re.S))
                chk("[ifc] (G) in the source (comments aside), the only string saying Hazmat is the character's name (%s)" % vis,
                    vis == ['"Hazmat"'], vis)
            # ---- (H) follow-up: the Virtual Room's top tier is a banner that counts towards the ultimate
            if wanted("H"):
                hq = pg.evaluate("""async ()=>{ const W = ms => new Promise(r => setTimeout(r, ms)); try{
                    const d = bannerDef('vrtop10'); if(!d) return { none: true };
                    const s = JSON.stringify(store), out = {}; { const u = ultimateProgress(); out.up0 = [u.have, u.need]; }
                    const v = unlockTrackView(); const t = v.tracks.find(x => x.key === 'vr'); const top = t.tiers[t.tiers.length - 1];
                    out.lead = top.lead.k + ':' + top.lead.id; out.goldWith = top.rewards.map(r => r.k + ':' + r.id);
                    store.vrWins = 9; out.at9 = bannerEarned('vrtop10'); out.tier9 = unlockTrackView().tracks.find(x => x.key === 'vr').tiers.slice(-1)[0].held;
                    store.vrWins = 10; out.at10 = bannerEarned('vrtop10'); out.tier10 = unlockTrackView().tracks.find(x => x.key === 'vr').tiers.slice(-1)[0].held;
                    applyLoadedData(JSON.parse(s));
                    /* the ultimate counts it: the same account with only this banner held or not, one apart */
                    const have0 = d.have; d.have = () => 0; const u0 = ultimateProgress(); d.have = () => d.need; const u1 = ultimateProgress(); d.have = have0;
                    out.ultDelta = [u1.have - u0.have, u1.need - u0.need];
                    const up = ultimateProgress(); out.up = [up.have, up.need];
                    document.querySelectorAll('.invite-overlay').forEach(o => o.remove());
                    showUnlockDetail(bannerDetail(ULTIMATE_TOP)); await W(500);
                    const c = document.querySelector('.unlock-card .unlock-card-count'), n = document.querySelector('.unlock-card .unlock-card-note');
                    out.count = c ? c.textContent : ''; out.note = n ? n.textContent : '';
                    document.querySelectorAll('.invite-overlay').forEach(o => o.remove());
                    showUnlockDetail(unlockItemDetail(top.lead)); await W(500);
                    const k = document.querySelector('.unlock-card'); out.cardKind = k ? [...k.classList].join(' ') : '';
                    out.cardArt = !!(k && k.querySelector('.bnr-vrtop10'));
                    document.querySelectorAll('.invite-overlay').forEach(o => o.remove());
                    /* the art: layered, moving only by transform / opacity, no svg filter */
                    const el = buildBannerArt('vrtop10'); el.style.cssText = 'position:fixed;left:0;top:0;width:480px;height:180px'; document.body.appendChild(el); await W(300);
                    out.layered = el.classList.contains('bnr-layered'); out.still = el.classList.contains('is-still');
                    out.filter = /<filter|filter=|feGaussian/i.test(el.innerHTML);
                    const props = new Set(); let nAnim = 0;
                    el.getAnimations({ subtree: true }).forEach(a => { nAnim++; try{ a.effect.getKeyframes().forEach(f => Object.keys(f).forEach(p => props.add(p))); }catch(e){} });
                    out.props = [...props].filter(p => ['offset', 'easing', 'composite', 'computedOffset'].indexOf(p) < 0); out.nAnim = nAnim;
                    el.remove();
                    out.inCustomize = 0; showCustomize('banner'); await W(1200);
                    out.inCustomize = document.querySelectorAll('.banner-opt .bnr-vrtop10').length;
                    return out; }catch(e){ return { err: String(e) }; } }""")
                chk("[%s] (H) the Virtual Room's top tier is the new banner, with the gold rim beside it (%s %s)" % (cls, hq.get("lead"), hq.get("goldWith")),
                    hq.get("lead") == "banner:vrtop10" and hq.get("goldWith") == ["banner:vrtop10", "rim:vr_gold"], hq)
                chk("[%s] (H) held at 10 first places, not at 9, and the tier with it (%s)" % (cls, [hq.get(k) for k in ("at9", "tier9", "at10", "tier10")]),
                    [hq.get(k) for k in ("at9", "tier9", "at10", "tier10")] == [False, False, True, True], hq)
                chk("[%s] (H) the ultimate counts it: that banner alone moves its count by one (%s)" % (cls, hq.get("ultDelta")), hq.get("ultDelta") == [1, 0], hq)
                nums = [int(x) for x in re.findall(r"\d+", (hq.get("count") or "").replace(",", ""))]
                left = (hq.get("up") or [0, 0])[1] - (hq.get("up") or [0, 0])[0]
                chk("[%s] (H) the ultimate's card says its numbers %s (%r; %r)" % (cls, hq.get("up"), hq.get("count"), hq.get("note")),
                    bool(hq.get("up")) and nums[-2:] == hq["up"] and
                    (left == 0 or sum(int(x) for x in re.findall(r"(\d+) (?:character|banner|theme|hundo effect)", hq.get("note") or "")) == left), hq)
                chk("[%s] (H) its tier row opens its banner card, the banner drawn on it" % cls, "unlock-card-banner" in (hq.get("cardKind") or "") and hq.get("cardArt"), hq)
                chk("[%s] (H) the banner is layered and moves (%d animations), only transform / opacity %s, no svg filter" % (cls, hq.get("nAnim") or 0, hq.get("props")),
                    hq.get("layered") and not hq.get("still") and (hq.get("nAnim") or 0) >= 4 and set(hq.get("props") or ["x"]) <= {"transform", "opacity"} and hq.get("filter") is False, hq)
                chk("[%s] (H) Customize's banner page has its tile (%s)" % (cls, hq.get("inCustomize")), hq.get("inCustomize") == 1, hq)
            chk("[%s] no page errors" % cls, not errs, errs[:3])
            ctx.close()
        # ---- (B) progress safety: everything held on the baseline is held here, for real-shaped (and, with --real, real) accounts
        if wanted("B"):
            real = arg("--real")
            for cls in ("academy", "ifc"):
                sets = shaped_set(ifc=(cls == "ifc"))
                if real: sets = sets + real_set(real, cls == "ifc")
                res = {}
                for tag, t_ in (("base", btext), ("this", text)):
                    a = account()
                    if cls == "ifc":
                        a2 = dict(a, classes=["academy", "ifc"]); fcs = account(ifc=True)
                        seed = {"progress": {CODE: a2, CODE + "__ifc": fcs}}; init = init_js(a2, fcs)
                    else:
                        seed = {"progress": {CODE: a}}; init = init_js(a)
                    ctx, pg, errs = page(br, t_, seed, init)
                    pg.wait_for_timeout(800)
                    res[tag] = pg.evaluate(HELD, sets)
                    ctx.close()
                lost, worse, n = [], [], 0
                ult_base = ult_here = 0
                # (follow-up) the one banner this build adds (Winner's Circle, vrtop10) joins the ultimate's "every banner": its count may
                # ask for exactly that many more items (the banners added since the baseline), and only an account short of 10 wins is
                # one further away. Nothing else may grow.
                added = None
                for i, (b_, t2) in enumerate(zip(res["base"], res["this"])):
                    if "err" in b_ or "err" in t2: lost.append((i, b_.get("err"), t2.get("err"))); continue
                    n += 1
                    for k_ in ("chars", "banners", "themes", "fx"):
                        miss = set(b_[k_]) - set(t2[k_])
                        if miss: lost.append((i, k_, sorted(miss)))
                    if b_.get("ult"): ult_base += 1
                    if t2.get("ult"): ult_here += 1
                    if b_.get("ult") and not t2.get("ult"): lost.append((i, "ULTIMATE", "held on the baseline, not here"))
                    added = t2.get("nBanners", 0) - b_.get("nBanners", 0)
                    newb = [x for x in t2["banners"] if x == "vrtop10"]
                    if t2["aNeed"] - b_["aNeed"] > added or (t2["aNeed"] - t2["aHave"]) - (b_["aNeed"] - b_["aHave"]) > added - len(newb):
                        worse.append((i, b_["aHave"], b_["aNeed"], t2["aHave"], t2["aNeed"], "wins %s" % t2.get("vrWins")))
                held_any = sum(len(x.get("chars", [])) + len(x.get("banners", [])) for x in res["this"] if "err" not in x)
                chk("[%s] (B) %d accounts (%s): nothing held on the baseline is lost here (%d characters and banners held)" % (cls, n, "real-shaped" + (" + real" if real else ""), held_any),
                    n == len(sets) and not lost and held_any > 0, lost[:5])
                chk("[%s] (B) Astral / the ultimate asks for nothing more than the banner added (%s more banner(s))" % (cls, added), not worse, worse[:5])
                grew = sorted({t2["aNeed"] - b_["aNeed"] for b_, t2 in zip(res["base"], res["this"]) if "err" not in b_ and "err" not in t2})
                # the same change for every account (nothing account-specific), at most the one banner added; in Fire Code exactly it. The
                # academy's count is also lowered by decision 5 (Supernova's three rewards left out while the rank is out of reach), so
                # there it is 1 - 3 = -2 against origin/main; (H) shows the banner itself moves the count by one.
                chk("[%s] (B) the ultimate's count changes the same for every account, by the new banner at most (%s; %s banner added)" % (cls, grew, added),
                    len(grew) == 1 and added == 1 and grew[0] <= 1 and (cls == "academy" or grew == [1]), grew)
                chk("[%s] (B) nobody who holds the ultimate on the baseline loses it (%d hold it there, %d here)" % (cls, ult_base, ult_here),
                    ult_here >= ult_base and not any(x[1] == "ULTIMATE" for x in lost), [x for x in lost if x[1] == "ULTIMATE"])
                codes = [x.get("ut") for x in res["this"]]
                chk("[%s] (B) every account publishes a well-formed code" % cls, all(isinstance(c, str) and re.fullmatch(r"1-[0-9a-f]{12}", c) for c in codes), codes[:4])
        br.close()
    print("ALL PASS" if ok else "FAILED", flush=True)
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
