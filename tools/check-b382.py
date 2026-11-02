"""Build 382: in a Safari tab the root carries the stars, so they run on under Safari's toolbar.
Madison: "Safari version is still messed up, the bottom and top of the safari version is cut off". His
screenshot of share/edge-test.html: Safari 26 draws the root's background under its toolbar but never
a fixed layer, and the stars were only a fixed layer.
Run:  python3 tools/check-b382.py   (--against: copy the old index.html over first)"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
from playwright.sync_api import sync_playwright
from PIL import Image
srv, url = g["serve"]()
INIT = """(()=>{ if(localStorage.getItem('class26e.drill.v1')) return;
 localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-0382');
 ['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.getstarted'].forEach(k=>localStorage.setItem(k,'1'));
 localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.penal256578.seen','1'); })()"""
d = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]())); d["publicId"] = "pubtest0382"; d["firstName"] = "Casey"; d["novaMet"] = 99
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1"
OUT = os.environ.get("B382_OUT", "/tmp/b382")
os.makedirs(OUT, exist_ok=True)
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else info)
ROOT = "()=>{ const h=getComputedStyle(document.documentElement); return {urls: h.backgroundImage.split('url(').length-1, browser: document.documentElement.classList.contains('is-browser')}; }"
def page(br, installed):
    ctx = br.new_context(viewport={"width": 440, "height": 800}, device_scale_factor=2, has_touch=True, is_mobile=True, user_agent=UA)
    if installed: ctx.add_init_script(g["STANDALONE"])
    ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]()))
    pg = ctx.new_page(); body = g["patched"]((0, 0, 0, 0))
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.add_init_script(INIT % json.dumps(json.dumps(d)))
    pg.goto(url); pg.wait_for_timeout(3500); pg.evaluate("document.getElementById('splashscreen')?.remove()")
    pg.evaluate("()=>{ homeUnlocksOwed=()=>false; showHome(); }"); pg.wait_for_timeout(4000)
    return ctx, pg
def bright(path):
    im = Image.open(path).convert("L"); W, H = im.size; px = im.load()
    return {(x, y) for y in range(H // 2, H) for x in range(W) if px[x, y] > 90}
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    ctx, pg = page(br, False)
    r = pg.evaluate(ROOT)
    chk("in a Safari tab the root's background carries the two star tiles on Home (%s)" % (r,), r["browser"] and r["urls"] == 2, r)
    # the root's stars on the fixed layer's grid: only one or the other showing, the same bright pixels
    pg.add_style_tag(content="#stage,#bottomtabs,.class-bubble-wrap,.daily-question-fab,.chatdock-btn,[class*=fab]{visibility:hidden !important}"
                             "body::before{display:none !important} html.x-a body::after{display:none !important} html.x-b{--root-sky-a:none !important;--root-sky-b:none !important}")
    pg.evaluate("()=>document.documentElement.classList.add('x-a')"); pg.wait_for_timeout(500); pg.screenshot(path=OUT + "/root.png")
    pg.evaluate("()=>{ document.documentElement.classList.remove('x-a'); document.documentElement.classList.add('x-b'); }"); pg.wait_for_timeout(900); pg.screenshot(path=OUT + "/fixed.png")
    a, b = bright(OUT + "/root.png"), bright(OUT + "/fixed.png")
    chk("and they sit exactly where the fixed layer's stars are (%d and %d bright pixels, %d shared)" % (len(a), len(b), len(a & b)),
        len(b) > 50 and len(a) == len(b) and len(a & b) == len(b), [len(a), len(b), len(a & b)])
    # a test has no stars
    pg.evaluate("""async()=>{ document.documentElement.classList.remove('x-b'); const wait=ms=>new Promise(r=>setTimeout(r,ms)); const unit=QUESTIONS[0].topic.trim();
      const idx=QUESTIONS.map((q,i)=>i).filter(i=>(QUESTIONS[i].topic||'').trim()===unit && inWholeUnit(QUESTIONS[i]));
      cfg.source='all'; cfg.mode='drill'; cfg.units=[unit]; beginRun(idx); for(let t=0;t<80&&!document.querySelector('.qpanel .choice');t++) await wait(100); await wait(800); }""")
    r = pg.evaluate("()=>({calm: document.body.classList.contains('sky-calm'), urls: getComputedStyle(document.documentElement).backgroundImage.split('url(').length-1})")
    chk("on a test (no stars) the root carries none either (%s)" % (r,), r["calm"] and r["urls"] == 0, r)
    ctx.close()
    ctx, pg = page(br, True)
    r = pg.evaluate(ROOT)
    chk("the installed app is as it was: not a browser tab, no stars on the root (%s)" % (r,), not r["browser"] and r["urls"] == 0, r)
    ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
