"""Build 338: a phone's Safari tab shows the app under its bars - the sky runs edge to edge as in the installed app,
with no black fade at the top or bottom, and nothing solid for Safari 26 to take as its bars' colour.
Run:  python3 tools/check-b338.py"""
import io, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b330.py")).read().split("want = sys.argv")[0]
g = {"__file__": os.path.join(HERE, "check-b330.py"), "__name__": "b330"}; exec(src, g)
from playwright.sync_api import sync_playwright
from PIL import Image
g["DEV"]["inst"] = (440, 956, (62, 0, 34, 0), True)
g["DEV"]["tab"] = (440, 956, (0, 0, 0, 0), False)
FIXED = """()=>{ const vw = innerWidth, vh = innerHeight, bad = [];
  const test = (el, pseudo) => { const c = getComputedStyle(el, pseudo); if(c.position !== 'fixed' && c.position !== 'sticky') return;
    if(pseudo && (!c.content || c.content === 'none')) return; if(c.display === 'none') return;
    const m = /rgba?\\(([^)]+)\\)/.exec(c.backgroundColor); const a = m ? (m[1].split(',').length > 3 ? parseFloat(m[1].split(',')[3]) : 1) : 0;
    const r = el.getBoundingClientRect();
    if(r.top >= vh || r.bottom <= 0) return;
    if(a > 0.05 && r.width >= vw * .6 && (r.top <= 2 || r.bottom >= vh - 2 || r.top < 0 || r.bottom > vh)) bad.push((el.id || el.className || el.tagName) + (pseudo || '') + ' ' + c.backgroundColor); };
  [document.body, ...document.querySelectorAll('body *')].forEach(el => { test(el); test(el, '::before'); test(el, '::after'); });
  const h = getComputedStyle(document.documentElement);
  return { bad, band: document.documentElement.style.getPropertyValue('--band'), fadePaper: h.getPropertyValue('--fade-paper').trim() }; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    _nc = br.new_context
    br.new_context = lambda **kw: _nc(has_touch=True, **kw)    # a phone: no mouse, so the laptop's no-fade rule does not apply
    shots = {}
    for dev in ("inst", "tab"):
        ctx, page = g["page_for"](br, dev)
        for _ in range(3):
            page.evaluate("()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }"); page.wait_for_timeout(400)
        for name, fn in (("home", "showHome()"), ("profile", "showProfile()")):
            page.evaluate("()=>{ " + fn + "; }"); page.wait_for_timeout(1800)
            shots[(dev, name)] = Image.open(io.BytesIO(page.screenshot())).convert("RGB")
        if dev == "tab":
            f = page.evaluate(FIXED)
        ctx.close()
    br.close()
for name in ("home", "profile"):
    a, b = shots[("inst", name)], shots[("tab", name)]; w, h = a.size
    worst = 0
    for y in list(range(80, 150, 10)) + list(range(h - 40, h - 4, 7)):
        for x in (8, w - 8):
            pa, pb = a.getpixel((x, y)), b.getpixel((x, y)); worst = max(worst, max(abs(i - j) for i, j in zip(pa, pb)))
    g["chk"]("%s: a phone's Safari tab shows the same sky as the installed app under the status bar and at the very bottom (worst %d levels, 8 allowed)" % (name, worst), worst <= 8, worst)
g["chk"]("no fixed full-width element at the top or bottom edge carries an opaque background colour (Safari 26 would take it as its bars' tint)", not f["bad"], f["bad"])
g["chk"]("the root's colour is the sky's own top colour, set for the status-bar band, and the fades are off", bool(f["band"]) and f["fadePaper"] == "transparent", f)
sys.exit(0 if g["ok"] else 1)
