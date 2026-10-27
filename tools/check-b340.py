"""Build 340: the tab bar's platter is checked against its lit tab once things settle, and put right if it is off.
A phone left it about a dozen points left of the Home tab, out past the bar's edge, and it stayed there.
Run:  python3 tools/check-b340.py"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b330.py")).read().split("want = sys.argv")[0]
g = {"__file__": os.path.join(HERE, "check-b330.py"), "__name__": "b330"}; exec(src, g)
from playwright.sync_api import sync_playwright
INV = """()=>{ const sl=document.querySelector('.bottomtabs-slider'), a=document.querySelector('.bottomtab.active'); const s=sl.getBoundingClientRect(), t=a.getBoundingClientRect(), b=document.querySelector('.bottomtabs').getBoundingClientRect();
  return {dc:+((s.left+s.width/2)-(t.left+t.width/2)).toFixed(1), dw:+(s.width-t.width).toFixed(1), outside:+(s.left-b.left).toFixed(1)} }"""
BREAK = """(d)=>{ const sl=document.querySelector('.bottomtabs-slider'); sl.style.transition='none'; const m=/translateX\\(([-\\d.]+)px/.exec(sl.style.transform);
  sl.style.transform='translateX('+(parseFloat(m[1])+d)+'px)'; sl.style.width=(sl.offsetWidth+6)+'px'; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    for label, dev in (("promax", "promax"), ("iPad", "ipad11")):
        ctx, page = g["page_for"](br, dev)
        for _ in range(3):
            page.evaluate("()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }"); page.wait_for_timeout(400)
        tabs = {t[0]: t for t in page.evaluate("()=>[...document.querySelectorAll('.bottomtabs-navrow .bottomtab')].map(t=>{const r=t.getBoundingClientRect(); return [t.id, r.left+r.width/2, r.top+r.height/2]})")}
        for frm, to in (("profile", "home"), ("rewards", "calendar")):
            t = tabs["bottomtab-" + frm]; page.mouse.click(t[1], t[2]); page.wait_for_timeout(1400)
            t = tabs["bottomtab-" + to]; page.mouse.click(t[1], t[2])
            # the lens has handed over to the platter by now, the settle check is still to come
            page.wait_for_timeout(750)
            page.evaluate(BREAK, -14)
            b = page.evaluate(INV)
            page.wait_for_timeout(2200)
            r = page.evaluate(INV)
            g["chk"]("%s %s->%s: a platter left of its tab (%.0fpx off, %.0fpx past the bar) is put back once the bar settles, with no further tap" % (label, frm, to, b["dc"], -b["outside"] if b["outside"] < 0 else b["outside"]), abs(r["dc"]) <= 1 and abs(r["dw"]) <= 1.5, (b, r))
        ctx.close()
    br.close()
sys.exit(0 if g["ok"] else 1)
