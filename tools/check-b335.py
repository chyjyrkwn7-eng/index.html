"""Build 335: Start Studying sits in the middle of its room - the gap under the words equals the gap to the tab bar.
Run:  python3 tools/check-b335.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b330.py")).read().split("want = sys.argv")[0]
g = {"__file__": os.path.join(HERE, "check-b330.py"), "__name__": "b330"}; exec(src, g)
from playwright.sync_api import sync_playwright
g["DEV"].update({"p61": (390, 844, (47, 0, 34, 0), True), "plus": (430, 932, (59, 0, 34, 0), True)})
GAPS = """()=>{ const r = e => e.getBoundingClientRect();
  const tag = [...document.querySelectorAll('.panel.home *')].filter(e => /Master the material/.test(e.textContent) && !e.children.length)[0];
  const b = r(document.querySelector('.panel.home .playbtn')), t = r(tag), bar = r(document.querySelector('.bottomtabs'));
  return { above: Math.round(b.top - t.bottom), below: Math.round(bar.top - b.bottom) }; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    for dev in ("promax", "p61", "plus"):
        ctx, page = g["page_for"](br, dev)
        for _ in range(3):
            page.evaluate("()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }"); page.wait_for_timeout(600)
        page.evaluate("()=>showHome()"); page.wait_for_timeout(1500)
        r = page.evaluate(GAPS)
        g["chk"](dev + ": Start Studying is centred between the words above and the tab bar (gaps within 6px)", abs(r["above"] - r["below"]) <= 6 and r["above"] > 30, r)
        ctx.close()
    br.close()
sys.exit(0 if g["ok"] else 1)
