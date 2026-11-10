"""Shared harness for the unlit-secret-flare gate and its screenshots (build 384 r15).
Loads shoot-flow's stubs (standalone, fake Firebase), serves any index.html you point it at,
and opens a seeded near-fresh account in the Police Academy class or in Fire Code."""
import io, json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
_sf = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
G = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(_sf, G)
CHROME = G["CHROME"]
OWNER = "xph5b57jbp5a"
KEYS = ['class26e.freshstart', 'class26e.intro.seen', 'class26e.unithold.tip', 'class26e.daily.seen', 'class26e.savecode.asked', 'class26e.savecode.card',
        'class26e.getstarted', 'class26e.weekrecap.v1', 'class26e.penal55124.seen', 'class26e.penal124256.seen', 'class26e.penal256578.seen']
INIT = """(()=>{ if(localStorage.getItem('class26e.drill.v1')) return;
 localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-0384');
 %s.forEach(k=>localStorage.setItem(k, k==='class26e.weekrecap.v1' ? '9999-12-31' : '1'));
 localStorage.setItem('class26e.frame.ok','go-live-1'); %s })()"""
SEED = {"firstName": "Casey", "avatarChar": "ninja", "onboardingComplete": True, "leaderboardOptIn": True, "lastModified": 1700000000000,
        "tourRev": 99, "rankMapFx244": True, "seenProfileTour": True, "seenModeSelectTour": True, "seenUnitSelectTour": True,
        "seenMainMenuTour": True, "seenClassTip": True, "seenRankingsTour": True, "seenAppearanceTour": True, "novaMet": 99,
        "lifetime": {"points": 150, "answered": 40, "correct": 30}}
INSET_RE = re.compile(r"env\(safe-area-inset-(top|bottom|left|right)(?:\s*,[^()]*)?\)")


def body_of(path, insets=(62, 0, 34, 0)):
    src = io.open(path, encoding="utf-8").read()
    t, r, b, l = insets
    v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
    return INSET_RE.sub(lambda m: v[m.group(1)], src)


def serve():
    return G["serve"]()


def page(br, url, src_path, ifc, w=440, h=956, dpr=3, found=None, fresh=False, insets=(62, 0, 34, 0)):
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=dpr)
    ctx.add_init_script(G["STANDALONE"])
    ctx.add_init_script(G["FAKE_FIREBASE"].replace("__ROWS__", G["rows_json"]()))
    pg = ctx.new_page(); body = body_of(src_path, insets)
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    if not fresh:
        d = dict(SEED); d["publicId"] = OWNER if ifc else "pubtest0384u"
        if found: d["mysteryColorsFound"] = found
        extra = ("localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done');"
                 "localStorage.setItem('class26e.activeclass','ifc');" + "".join("localStorage.setItem('%s','1');" % k.replace("class26e.", "class26e.ifc.") for k in KEYS)) if ifc else ""
        pg.add_init_script(INIT % (json.dumps(json.dumps(d)), json.dumps(KEYS), extra))
    pg.goto(url); pg.wait_for_timeout(3200)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); }")
    if not fresh:
        pg.evaluate("()=>{ try{ homeUnlocksOwed=()=>false; }catch(e){} document.querySelectorAll('.rs-spot,.unlock-card,.nova-talk,.invite-overlay,#intro-pop').forEach(n=>n.remove()); }")
        pg.wait_for_timeout(600)
    return ctx, pg, errs
