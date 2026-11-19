"""Shared pieces for the 384 pin gate and its shot tool (check-b384-pin.py, shoot-b384-pin.py).

Madison: "adding a badge to your profile to flex ... You can equip a badge on your profile, and people can see this badge."

Every device is a browser context on ONE in-memory Firestore (tools/b384_cloud_lib.py: documents, dotted updates, transactions,
listeners, every write logged with the device that made it), so two phones of the same account really merge through the cloud and a
write count is the cloud's own. The account is seeded in both classes (the academy, and Fire Code's own copy); the class board holds
made-up classmates whose rows carry a pin (`pb`), a pin of a badge that is not of that class, a row from before this build (none), and
junk, so readers are measured on what an older or a hostile client could publish.

    cloud, url = start(src)                       # the app and the cloud from one origin
    ctx, pg, errs = device(br, url, "A", cls="academy"|"ifc", w=440, h=956)
"""
import json, os, re, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import b384_cloud_lib as C
import b384_flow_lib as L

_src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(_src, g)
CHROME = L.CHROME
WEEK = g["week_key_now"]()
now_ms = int(time.time() * 1000)
DAY = 86400000
OWNER = "pinowner0001"; CODE = "PINT-0384"; MYCODE = "PNO-384"
SEEN = ("['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card',"
        "'class26e.getstarted','class26e.frame.ok','class26e.a2hs'].forEach(k=>localStorage.setItem(k, k==='class26e.frame.ok'?'go-live-1':'1'));")
IFC_SEEN = ("['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card',"
            "'class26e.ifc.getstarted'].forEach(k=>localStorage.setItem(k,'1'));")

# the units each class really has (read off the bank once, see units_of); the made-up rows below pin these
ACAD_UNITS = ["Professionalism and Ethics", "Professional Policing", "Fitness, Wellness, and Stress Management", "TCOLE Rules",
              "Multiculturalism and Human Relations", "Racial Profiling", "US and Texas Constitution and Rights", "Penal Code",
              "Code of Criminal Procedure and Bill of Rights", "Arrest, Search, and Seizure"]
IFC_UNITS = ["Chapter 1: Scope and Administration", "Chapter 2: Definitions", "Chapter 3: General Requirements",
             "Chapter 4: Emergency Planning and Preparedness", "Chapter 5: Fire Service Features", "Chapter 6: Building Services and Systems",
             "Chapter 7: Fire and Smoke Protection Features", "Chapter 8: Interior Finish, Decorative Materials and Furnishings",
             "Chapter 9: Fire Protection and Life Safety Systems", "Chapter 10: Means of Egress"]
UNITS = {"academy": ACAD_UNITS, "ifc": IFC_UNITS}

def account(extra=None, ifc=False, name="Jordan"):
    a = json.loads(g["SEED"].replace("__WEEK__", WEEK))
    a.update({"publicId": OWNER, "firstName": name, "novaMet": 99, "friendCode": MYCODE, "friendsIn": [], "friendsOut": [],
              "friendsDeclined": [], "chats": [], "leaderboardOptIn": True, "lastModified": now_ms - 3600000, "classes": ["academy", "ifc"]})
    a.setdefault("novaHeard", {})["@recap"] = 99991231
    if ifc:
        a = {k: a[k] for k in ["firstName", "avatarChar", "publicId", "onboardingComplete", "tourRev", "novaMet", "novaHeard", "weekKey",
                               "leaderboardOptIn", "lastModified", "classes"] if k in a}
        a.update({k: v for k, v in json.loads(g["SEED"].replace("__WEEK__", WEEK)).items() if k.startswith("seen")})
        a.update({"lifetime": {"points": 64000, "answered": 3000, "correct": 2600, "perfectTests": 40}, "unitPerfects": {}, "testHistory": [],
                  "leaderboardOptInChanged": False, "rankUpShown": 7,
                  # (384.135) a copy written on Fire Code's fitted curve: without the flag the launch lowers the rank-up count to the
                  # rank held (none, here), and the badges this gate hands over would then owe rank-ups over what it measures
                  "ifcCurveRule": 38435})
    if extra: a.update(extra)
    return a

def init_js(acad, ifc_store, active):
    s = "(()=>{ if(sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); " + SEEN
    s += "localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode', '%s');" % (json.dumps(json.dumps(acad)), CODE)
    s += "localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done'); localStorage.setItem('class26e.activeclass','%s');" % active
    s += IFC_SEEN
    s += "localStorage.setItem('class26e.ifc.drill.v1', %s);" % json.dumps(json.dumps(ifc_store))
    return s + " })()"

# made-up classmates: name, character, level, badges, pin (None: a row from before this build), banner, days since active
def mates(units, other_units):
    u = units
    return [
        ("Alexis", "grizzly", 52, 9, u[3], "", 0),
        ("Kimberly Ann Montgomery-Vasquez", "alien", 47, 8, u[0], "", 1),     # a long name: it ellipsizes, the badge stays whole
        ("Leeland", "ghost", 41, 7, u[2], "", 1),
        ("Rosa", "ninja", 38, 5, u[4], "", 2),
        ("Dmitri", "grizzly", 33, 4, None, "", 1),                            # a row from before this build: no pb
        ("Priya", "ghost", 30, 3, other_units[0], "", 3),                     # a badge of the OTHER class: drawn as nothing
        ("Tomas", "alien", 28, 2, "<b>x</b>", "", 4),                         # junk: drawn as nothing
        ("Nadia", "ninja", 25, 2, 7, "", 5),                                  # not a string: drawn as nothing
        ("Omar", "ghost", 22, 2, "", "", 6),                                  # nothing pinned
        ("Zed", "grizzly", 20, 3, u[6], "", 6),                               # a badge their own row says they do not hold: nothing
    ]
MATE_PREFIX = "pinmate"
def mate_rows(units, other_units, bd_for=None):
    rows = {}
    for i, (nm, ch, lv, bdn, pb, bn, ago) in enumerate(mates(units, other_units)):
        pub = "%s%04d" % (MATE_PREFIX, i)
        r = {"firstName": nm, "avatarChar": ch, "level": lv, "badges": bdn, "mystery": 0, "hundos": 10 + lv, "correct": 120 * lv,
             "xp": 1250 * lv, "tests": lv, "lastModified": now_ms - ago * DAY - 60000, "seenAt": now_ms - ago * DAY - 60000, "banner": bn,
             "week": WEEK, "weekPoints": 400 - i * 20, "bd": list(units[:bdn])}
        if pb is not None: r["pb"] = pb
        rows[pub] = r
    return rows

def seed(acad_units, ifc_units, acad=None, ifc=None, friends=()):
    a = acad or account()
    f = ifc or account(ifc=True)
    ar = mate_rows(acad_units, ifc_units); fr = mate_rows(ifc_units, acad_units)
    for pub in friends:
        ar[pub]["facc"] = [OWNER]; fr[pub]["facc"] = [OWNER]
    if friends:
        a = dict(a, friendsOut=list(friends)); f = dict(f, friendsOut=list(friends))
    return ({"progress": {CODE: a, CODE + "__ifc": f}, "leaderboard": ar,
             "vrooms": {"lb-ifc-v1": {"kind": "board", "cls": "ifc", "rows": fr}}}, a, f)

def start(src, seed_doc):
    build = re.search(r'const APP_BUILD = "([^"]+)"', src).group(1)
    cloud, srv, url = C.make_cloud(seed_doc, L.patched(src, (62, 0, 34, 0)).encode(), L.ROOT, build=build)
    return cloud, srv, url

def device(br, url, dev, init, w=440, h=956, scale=2, reduced=False, zoom=None, extra_init=""):
    """zoom: the phone's text size as Safari applies it (page zoom, as check-b384-profilerows2 models it): the layout viewport is
    w/zoom by h/zoom CSS pixels, drawn at scale*zoom"""
    if zoom and zoom != 100:
        z = zoom / 100.0; w, h, scale = round(w / z), round(h / z), scale * z
    kw = dict(viewport={"width": w, "height": h}, has_touch=True, device_scale_factor=scale, color_scheme="dark")
    if reduced: kw["reduced_motion"] = "reduce"
    ctx = br.new_context(**kw)
    ctx.add_init_script(g["STANDALONE"])
    ctx.add_init_script(C.init_script(url, dev)); ctx.add_init_script(C.CLIENT)
    ctx.add_init_script(init)
    if extra_init: ctx.add_init_script(extra_init)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.on("console", lambda m: errs.append("console: " + m.text[:200]) if m.type == "error" and not BLOCKED.search(m.text) else None)
    pg.set_default_timeout(180000)
    pg.goto(url + "/index.html", timeout=180000); pg.wait_for_timeout(3800)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); document.getElementById('launch-trouble')?.remove(); }")
    return ctx, pg, errs
# the sandbox's blocked network (Firebase's CDN, Google's fonts and the like) is not the page's error
import re as _re
BLOCKED = _re.compile(r"ERR_|Failed to load resource|net::|gstatic|googleapis|firebase|status of 40|status of 50", _re.I)

QUIET = """()=>{ try{ const u = pendingHomeUnlocks(); markUnlocksShown(u.chars, u.banners, u.fx); (u.hints || []).forEach(markFlareHintShown); }catch(e){}
  try{ homeUnlockPlaying = false; }catch(e){} try{ store.pendingBadgeUnlocks = []; store.retroBadgePending = []; }catch(e){}
  try{ markBadgeScenesPlayed(classTopics()); }catch(e){}
  document.querySelectorAll('.rs-spot, .daily-alert, .scene-bridge, #intro-pop, .invite-overlay, .pg-scene').forEach(n => { try{ n.__nova && n.__nova.skip(); }catch(e){} n.remove(); }); }"""
def quiet(pg):
    pg.evaluate(QUIET); pg.wait_for_timeout(300); pg.evaluate(QUIET)

# hold the first `n` units' badges (the app's own threshold per unit), as a real account's counters
HOLD = """(n)=>{ const s = store; s.unitPerfects = s.unitPerfects || {};
  classTopics().forEach((u, i) => { s.unitPerfects[u] = i < n ? Math.max(badgeThresholdFor(u), Number(s.unitPerfects[u]) || 0) : 0; });
  try{ markBadgeScenesPlayed(classTopics()); }catch(e){}
  saveStore(); return badgesEarnedList(); }"""
def hold(pg, n):
    return pg.evaluate(HOLD, n)

def units_of(pg):
    return pg.evaluate("()=>classTopics()")

# ---- a Virtual Room: made-up members whose entries carry a pin (the same cases as the board) ----
# the presence beat (45 s) runs at 250 ms so a gate can see it: nothing else in the app waits exactly 45000
FAST = "window.__si = window.setInterval; window.setInterval = function(f, ms){ return window.__si.apply(window, [f, ms === 45000 ? 250 : ms].concat([].slice.call(arguments, 2))); };"
def vr_pub(i): return "pinvr%06d" % i
def room(cls, units, other_units, n=6):
    parts = {}
    cast = mates(units, other_units)[:n]
    for i, (nm, ch, lv, bdn, pb, bn, ago) in enumerate(cast):
        e = {"name": nm, "avatarChar": ch, "level": lv, "badges": bdn, "joinedAt": 10 + i, "seen": 9e15, "ready": i % 2 == 0, "progress": 0,
             "finished": False, "banner": "", "accent": "ink"}
        if pb is not None: e["pb"] = pb
        parts[vr_pub(i)] = e
    d = {"hostCode": vr_pub(0), "units": [], "versions": {}, "timeLimit": None, "count": None, "game": "race", "open": False, "hostName": cast[0][0],
         "hostAvatar": cast[0][1], "status": "waiting", "startAt": None, "mode": "exam", "createdAt": now_ms - 600000, "participants": parts}
    if cls == "ifc": d["cls"] = "ifc"
    return d
JOIN = "async(code)=>{ const ok = await joinVirtualRoomLobby(code); await new Promise(r=>setTimeout(r,2200)); return [ok, vroomCode, BANK_CLASS]; }"
