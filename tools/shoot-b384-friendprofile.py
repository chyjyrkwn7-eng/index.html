"""Screenshots of a friend's profile (384.115), made with the gate's own fixture: the card with View profile, the profile at the top and
scrolled to the badge case and the collection, and the no-activity state (a row from before the fields). iPhone 17 Pro Max 440x956 and
iPad Pro 11" 834x1194 (2x), saved to OUT (default scratchpad/friendprofile).

  python3 tools/shoot-b384-friendprofile.py [OUT_DIR]"""
import importlib.util, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("fpgate", os.path.join(HERE, "check-b384-friendprofile.py"))
G = importlib.util.module_from_spec(spec)
OUT = next((a for a in sys.argv[1:] if not a.startswith("--")), None)
sys.argv = [sys.argv[0]]
spec.loader.exec_module(G)
OUT = OUT or os.environ.get("SHOOT_OUT") or "/tmp/claude-0/-home-user-index-html/5c94975c-e6e8-50f1-8dfe-822e5a33e1da/scratchpad/friendprofile"
os.makedirs(OUT, exist_ok=True)
from playwright.sync_api import sync_playwright

DEVICES = [("iphone-17-pro-max", 440, 956), ("ipad-pro-11", 834, 1194)]
# the document scrolls (not an inner box), so scroll the window itself
SCROLL_TO = "(s)=>{ const e = document.querySelector(s); if(e) window.scrollTo({ top: e.getBoundingClientRect().top + window.scrollY - 95, behavior: 'instant' }); }"
text = G._src_of(os.path.join(G.ROOT, "index.html"))
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G.g["CHROME"])
    for label, w, h in DEVICES:
        ctx, pg, errs = G.page(br, text, G.cloud0(), w=w, h=h, scale=2)
        pg.wait_for_timeout(1500)
        pg.evaluate("()=>showRankings()"); pg.wait_for_timeout(2500)
        pg.evaluate(G.OPEN_CARD, G.ALEX); pg.wait_for_timeout(700)
        pg.screenshot(path="%s/%s-1-card-view-profile.png" % (OUT, label))
        pg.click(".person-sheet-view"); pg.wait_for_timeout(2500)
        pg.screenshot(path="%s/%s-2-profile-top.png" % (OUT, label))
        for i, sel in enumerate((".fp-activity", ".fp-case", ".fp-hold"), 3):
            pg.evaluate(SCROLL_TO, sel); pg.wait_for_timeout(700)
            pg.screenshot(path="%s/%s-%d-profile-%s.png" % (OUT, label, i, sel[4:]))
        pg.evaluate("()=>window.scrollTo({ top: document.documentElement.scrollHeight, behavior: 'instant' })"); pg.wait_for_timeout(700)
        pg.screenshot(path="%s/%s-6-profile-bottom.png" % (OUT, label))
        pg.click(".fp-back"); pg.wait_for_timeout(1500)
        pg.evaluate(G.OPEN_CARD, G.LEE); pg.wait_for_timeout(500)
        pg.click(".person-sheet-view"); pg.wait_for_timeout(2200)
        pg.screenshot(path="%s/%s-7-no-activity-top.png" % (OUT, label))
        pg.evaluate(SCROLL_TO, ".fp-activity"); pg.wait_for_timeout(700)
        pg.screenshot(path="%s/%s-8-no-activity-case.png" % (OUT, label))
        print(label, "errors:", errs[:3], flush=True)
        ctx.close()
    br.close()
