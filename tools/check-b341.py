"""Build 341: the sky starts at Safari's status-band colour at the top edge of a phone's Safari tab, so there is no seam.
(Measured off his screenshot: band flat (31,33,38) over a sky of (37,40,45) left and (27,30,35) right.)
Run:  python3 tools/check-b341.py"""
import io, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b330.py")).read().split("want = sys.argv")[0]
g = {"__file__": os.path.join(HERE, "check-b330.py"), "__name__": "b330"}; exec(src, g)
from playwright.sync_api import sync_playwright
from PIL import Image
g["DEV"]["tab"] = (440, 956, (0, 0, 0, 0), False)
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    _nc = br.new_context
    br.new_context = lambda **kw: _nc(has_touch=True, **kw)
    ctx, page = g["page_for"](br, "tab")
    for _ in range(3):
        page.evaluate("()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }"); page.wait_for_timeout(400)
    page.evaluate("()=>{ showHome(); }"); page.wait_for_timeout(1800)
    band = page.evaluate("()=>document.documentElement.style.getPropertyValue('--band').trim()")
    im = Image.open(io.BytesIO(page.screenshot())).convert("RGB")
    ctx.close(); br.close()
m = re.match(r"#([0-9a-f]{6})", band or "", re.I)
bc = tuple(int(m.group(1)[i:i + 2], 16) for i in (0, 2, 4)) if m else None
g["chk"]("the root's band colour is set (--band) in a tab", bc is not None, band)
w, h = im.size
row = [im.getpixel((x, 1)) for x in range(8, w - 8, max(1, (w - 16) // 12))]
worst = max(max(abs(a - b) for a, b in zip(p, bc)) for p in row) if bc else 99
g["chk"]("the very top row of the page is Safari's band colour all the way across (worst %d levels, 3 allowed)" % worst, worst <= 3, (bc, row[:4]))
# it eases into the sky: nothing steps by more than 2 levels from one row to the next down the first 140px, at the two edge columns
step = 0
for x in (2, w - 3):
    prev = im.getpixel((x, 0))
    for y in range(1, 140):
        p = im.getpixel((x, y)); step = max(step, max(abs(a - b) for a, b in zip(p, prev)) if max(p) < 90 and max(prev) < 90 else 0); prev = p
g["chk"]("it eases into the sky without a line (largest step between rows %d, 3 allowed)" % step, step <= 3, step)
sys.exit(0 if g["ok"] else 1)
