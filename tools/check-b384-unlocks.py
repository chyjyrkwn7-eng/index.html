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
