"""Shared pieces for the 384.126 prestige gate and its shot tools (check-b384-prestige.py, shoot-b384-prestige.py).

A Fire Code page (or the academy's) loaded from the worktree's index.html - or a given file - with a seeded account, the board stubbed
the way check-b384-unlocks stubs it (the Firestore fake from check-b384-friends, every set() recorded in window.__payloads), and helpers
that build real-shaped accounts in the page: the counters an account carries, from nothing held up to everything held (the same
counters check-b384-completionist's EVERY sets), so eligibility is worked out by the app's own model, never stubbed."""
import json, os, re, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
_src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(_src, g)
CHROME = g["CHROME"]

_f = open(os.path.join(HERE, "check-b384-friends.py"), encoding="utf-8").read()
_i = _f.index('FAKE = r"""') + len('FAKE = r"""'); _j = _f.index('"""', _i)
FAKE = _f[_i:_j]
_wset = "set(c, id, v, o){ C[c] = C[c] || {};"
assert FAKE.count(_wset) == 1
FAKE = FAKE.replace(_wset, "set(c, id, v, o){ (window.__payloads = window.__payloads || []).push(c + '/' + id + ' ' + JSON.stringify(v)); C[c] = C[c] || {};")

OWNER = "pgowner00001"; CODE = "PGTE-0126"; MYCODE = "PGO-384"
now_ms = int(time.time() * 1000)
WEEK = g["week_key_now"]()
DAY = 86400000
SEEN = ("['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card',"
        "'class26e.getstarted','class26e.frame.ok','class26e.a2hs'].forEach(k=>localStorage.setItem(k, k==='class26e.frame.ok'?'go-live-1':'1'));")
IFC_SEEN = ("['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card',"
            "'class26e.ifc.getstarted'].forEach(k=>localStorage.setItem(k,'1'));")

def account(extra=None, ifc=False, pub=OWNER, name="Maddox"):
    a = json.loads(g["SEED"].replace("__WEEK__", WEEK))
    a.update({"publicId": pub, "firstName": name, "novaMet": 99, "friendCode": MYCODE, "friendsIn": [], "friendsOut": [],
              "friendsDeclined": [], "chats": [], "leaderboardOptIn": True, "lastModified": now_ms - 3600000})
    a.setdefault("novaHeard", {})["@recap"] = 99991231
    if ifc:
        a = {k: a[k] for k in ["firstName", "avatarChar", "publicId", "onboardingComplete", "tourRev", "novaMet", "novaHeard", "weekKey",
                               "leaderboardOptIn", "lastModified"] if k in a}
        a.update({k: v for k, v in json.loads(g["SEED"].replace("__WEEK__", WEEK)).items() if k.startswith("seen")})
        a.update({"lifetime": {"points": 0, "answered": 0, "correct": 0}, "unitPerfects": {}, "testHistory": [], "leaderboardOptInChanged": False,
                  "rankUpShown": 7})
    if extra: a.update(extra)
    return a

def init_js(acad, ifc_store=None, active="ifc"):
    s = "(()=>{ if(sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); " + SEEN
    s += "localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode', '%s');" % (json.dumps(json.dumps(acad)), CODE)
    if ifc_store is not None:
        s += "localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done'); localStorage.setItem('class26e.activeclass','%s');" % active
        s += IFC_SEEN
        s += "localStorage.setItem('class26e.ifc.drill.v1', %s);" % json.dumps(json.dumps(ifc_store))
    return s + " })()"

# made-up Fire Code classmates on the board: name, character, level, badges, pg (None: a row from before this build), banner, days since active
MATES = [
    ("Alexis", "pgstate", 80, 40, 3, "pglaurel", 0),
    ("Kimber", "pgmarshal", 80, 38, 2, "pgcommand", 1),
    ("Leeland", "pgdeputy", 80, 38, 1, "pgoath", 2),
    ("Rosa", "grizzly", 52, 20, 0, "", 3),
    ("Dmitri", "alien", 41, 13, None, "", 1),
    ("Priya", "ghost", 30, 8, 7, "", 4),          # an unknown value: drawn as nothing
    ("Tomas", "grizzly", 80, 38, "3", "", 6),     # a string, not a count: drawn as nothing
]
def mate_rows(prefix="pgmate"):
    rows = {}
    for i, (nm, ch, lv, bd, pgv, bn, ago) in enumerate(MATES):
        pub = "%s%05d" % (prefix, i)
        r = {"firstName": nm, "avatarChar": ch, "level": lv, "badges": bd, "mystery": 0, "hundos": 10 + lv, "correct": 120 * lv,
             "xp": 1250 * lv, "tests": lv, "lastModified": now_ms - ago * DAY - 60000, "seenAt": now_ms - ago * DAY - 60000, "banner": bn,
             "ut": "1-3f3f3f3f3f00" if pgv == 3 else "1-000000000000"}
        if pgv is not None: r["pg"] = pgv
        rows[pub] = r
    return rows

def ifc_seed(fc, friends=None):
    a2 = dict(account(), classes=["academy", "ifc"])
    rows = mate_rows()
    if friends:
        for pub in friends: rows[pub]["facc"] = [OWNER]
        fc = dict(fc, friendsOut=list(friends))
    seed = {"progress": {CODE: a2, CODE + "__ifc": fc}, "leaderboard": {},
            "vrooms": {"lb-ifc-v1": {"kind": "board", "cls": "ifc", "rows": rows}}}
    return seed, init_js(a2, fc)

def make_patched(text):
    def _p(ins, _o=text):
        v = {"top": f"{ins[0]}px", "right": f"{ins[1]}px", "bottom": f"{ins[2]}px", "left": f"{ins[3]}px"}
        return g["INSET_RE"].sub(lambda m: v[m.group(1)], _o)
    return _p

SRV = SERVE_URL = None
def serve():
    global SRV, SERVE_URL
    if SERVE_URL is None: SRV, SERVE_URL = g["serve"]()
    return SERVE_URL

def page(br, text, seed, init, w=440, h=956, scale=1, reduced=False, video_dir=None, color_scheme="dark"):
    url = serve()
    kw = dict(viewport={"width": w, "height": h}, has_touch=True, device_scale_factor=scale, color_scheme=color_scheme)
    if reduced: kw["reduced_motion"] = "reduce"
    if video_dir: kw["record_video_dir"] = video_dir; kw["record_video_size"] = {"width": w, "height": h}
    ctx = br.new_context(**kw)
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
    pg.goto(url, timeout=180000); pg.wait_for_timeout(3800)
    pg.evaluate("document.getElementById('splashscreen')?.remove(); document.getElementById('launch-trouble')?.remove();")
    return ctx, pg, errs

QUIET = """()=>{ try{ const u = pendingHomeUnlocks(); markUnlocksShown(u.chars, u.banners, u.fx); (u.hints || []).forEach(markFlareHintShown); }catch(e){}
  try{ homeUnlockPlaying = false; }catch(e){} try{ store.pendingBadgeUnlocks = []; saveStore(); }catch(e){}
  document.querySelectorAll('.rs-spot, .daily-alert, .scene-bridge, #intro-pop, .invite-overlay, .pg-scene').forEach(n => { try{ n.__nova && n.__nova.skip(); }catch(e){} n.remove(); }); }"""
def quiet(pg):
    pg.evaluate(QUIET); pg.wait_for_timeout(300); pg.evaluate(QUIET)

# THE ACCOUNT, BUILT IN THE PAGE (the bank's own chapters and keys). stage:
#   "none"   a mid-ladder account: Gold, two tracks part way, nothing gold
#   "super"  Supernova (level 80, every chapter's badge) but no track gold
#   "one"    Supernova + the Answers track gold (one gold rim)
#   "three"  Supernova + Answers, Hundos and Study Time gold (three)
#   "five"   Supernova + all five gold (Mastery) but one secret flare still hidden (no Completionist)
#   "all"    everything: Mastery and Completionist
BUILD = r"""(stage) => {
  try{ showAppearance(); }catch(e){}
  document.querySelectorAll('.rs-spot').forEach(sp => { try{ sp.__nova.skip(); }catch(e){ sp.remove(); } });
  const s = store;
  const top = stage !== 'none';
  const lvlPts = p => { let lo = 0, hi = 2e6; while(lo < hi){ const m = (lo + hi) >> 1; s.lifetime.points = m; if(levelOf(s) >= p) hi = m; else lo = m + 1; } return lo; };
  s.lifetime = Object.assign({}, s.lifetime, { answered: 800, correct: 600, perfectTests: 20, fullTests: 10, longestStreak: 12, currentStreak: 3 });
  s.unitPerfects = {};
  const units = classTopics();
  units.forEach((u, i) => { s.unitPerfects[u] = top ? 99 : (i < 10 ? 99 : 0); });
  s.rankFloor = 0; s.rankUpShown = TIER_ORDER_FULL.length;
  s.mysteryColorsFound = {}; MYSTERY_ORDER.forEach(k => { s.mysteryColorsFound[k] = false; });
  s.dailyCorrectTotal = 0; s.novaBeaten = false; s.vrWins = 0; s.vrMatches = 0; s.vrHosted = 0; s.hundoDayBest = 0; s.bigTest450Passed = false;
  s.friendsBest = 0; s.lateHundos = 0; s.practiceExamPerfect = false; s.unitHundoStreakBest = 0; s.studyLog = {}; s.bestTestStreak = 0;
  s.stats = s.stats || {};
  const tracks = { one: ['ans'], three: ['ans', 'hun', 'study'], five: ['ans', 'hun', 'study', 'acc', 'vr'], all: ['ans', 'hun', 'study', 'acc', 'vr'] }[stage] || [];
  const L = s.lifetime;
  if(tracks.indexOf('ans') >= 0){ L.correct = 12000; L.answered = 14000; L.fullTests = 260; s.bigTest450Passed = true; s.bigTest500Passed = true; }
  if(tracks.indexOf('hun') >= 0){ L.perfectTests = 300; }
  if(tracks.indexOf('study') >= 0){ const log = {}, d0 = Date.parse('2026-09-01T12:00:00Z'); for(let i = 0; i < 40; i++) log[new Date(d0 + i * 864e5).toISOString().slice(0, 10)] = 2 * 3600000; s.studyLog = log; s.dailyCorrectTotal = 12; }
  if(tracks.indexOf('acc') >= 0){ L.longestStreak = 120; s.bestTestStreak = 120; s.hundoDayBest = 4; s.practiceExamPerfect = true; s.unitHundoStreakBest = 12;
    Array.from(retakeKeySet()).slice(0, 120).forEach(k => { s.stats[k] = Object.assign({}, s.stats[k] || {}, { m: 2, c: 3 }); }); }
  if(tracks.indexOf('vr') >= 0){ L.fullTests = Math.max(L.fullTests, 520); s.vrWins = 12; s.vrMatches = 60; s.vrHosted = 4; s.novaBeaten = true; s.friendsBest = 6; s.lateHundos = 4;
    try{ ['drillPlays', 'examPlays', 'gamePlays'].forEach(k => { L[k] = Math.max(Number(L[k]) || 0, 40); }); }catch(e){} }
  if(stage === 'all' || stage === 'five'){ MYSTERY_ORDER.forEach((k, i) => { s.mysteryColorsFound[k] = stage === 'all' || i < MYSTERY_ORDER.length - 1; }); }
  if(top) lvlPts(80); else lvlPts(42);
  s.lifetime.points = Math.max(s.lifetime.points, top ? s.lifetime.points : 0);
  try{ unlockTrackMemo = null; friendShowcaseMemo = null; }catch(e){}
  saveStore();
  let v = null; try{ v = unlockTrackView(); }catch(e){}
  return { rank: rankOf(s), level: levelOf(s), golds: v ? v.tracks.filter(t => t.gold).map(t => t.key) : null,
           completionist: (() => { try{ return bannerEarned('completionist'); }catch(e){ return null; } })() };
}"""
def build(pg, stage):
    return pg.evaluate(BUILD, stage)
