"""Build 347: Home keeps the proportions he sent (the words and Start Studying low, near the bar) on every tall phone;
the Classes list does nothing when a class you are enrolled in is tapped.
Run:  python3 tools/check-b347.py"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(HERE + "/check-b330.py").read().split("want = sys.argv")[0]
g = {"__file__": HERE + "/check-b330.py", "__name__": "b330"}; exec(src, g)
from playwright.sync_api import sync_playwright
g["DEV"]["se"] = (375, 667, (20, 0, 0, 0), True); g["DEV"]["p15"] = (393, 852, (59, 0, 34, 0), True)
POS = """()=>{ const r=s=>{ const e=document.querySelector(s); const b=e.getBoundingClientRect(); return [b.top, b.bottom]; };
  return { greet:r('.screen-home-actual .homegreeting'), tag:r('.screen-home-actual .hometagline'), play:r('.screen-home-actual > .playbtn'), bar:document.getElementById('bottomtabs').getBoundingClientRect().top, vh:innerHeight }; }"""
CLEAR = "()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }"
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    for dev in ("promax", "p15"):
        ctx, pg = g["page_for"](br, dev)
        for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(300)
        pg.evaluate("()=>{ showHome(); }"); pg.wait_for_timeout(1500)
        p = pg.evaluate(POS)
        below = (p["bar"] - p["play"][1]) / p["vh"]; words = (p["play"][0] - p["tag"][1]) / p["vh"]
        g["chk"]("%s: Start Studying is %.3f of the screen above the tab bar (his: .057, allowed .045-.07)" % (dev, below), .045 <= below <= .07, p)
        g["chk"]("%s: and %.3f of the screen under the tagline (his: .063, allowed .05-.08)" % (dev, words), .05 <= words <= .08, p)
        ctx.close()
    # a short phone keeps its thirds (its planet needs the room)
    ctx, pg = g["page_for"](br, "se")
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    pg.evaluate("()=>{ showHome(); }"); pg.wait_for_timeout(1500)
    p = pg.evaluate(POS); gap1 = p["play"][0] - p["tag"][1]; gap2 = p["bar"] - p["play"][1]
    g["chk"]("SE: the planet keeps its room (the two gaps under the words stay about equal: %.0f and %.0f)" % (gap1, gap2), abs(gap1 - gap2) <= 14, p)
    ctx.close()
    # the Classes list
    ctx, pg = g["page_for"](br, "promax")
    pg.evaluate("()=>{ localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); showClassCatalog(); }"); pg.wait_for_timeout(900)
    cards = pg.evaluate("()=>[...document.querySelectorAll('.class-card:not(.is-soon)')].map(c=>({k:c.className, dis:c.getAttribute('aria-disabled'), st:c.querySelector('.cc-status').textContent, pe:getComputedStyle(c).pointerEvents}))")
    chk_ = all(c["st"] == "Enrolled" and c["dis"] == "true" and c["pe"] == "none" for c in cards) and len(cards) == 2
    g["chk"]("every class you are in says Enrolled and is not tappable (%s)" % [c["st"] for c in cards], chk_, cards)
    pg.evaluate("()=>{ document.querySelectorAll('.class-card:not(.is-soon)').forEach(c=>c.click()); }"); pg.wait_for_timeout(900)
    still = pg.evaluate("()=>({ catalog: !!document.querySelector('.class-catalog'), class: window.NOVA_CLASS })")
    g["chk"]("tapping them does nothing (still on the list, same class)", still["catalog"] and still["class"] == "academy", still)
    pg.evaluate("()=>{ localStorage.setItem('class26e.enrolled', '[]'); showClassCatalog(); }"); pg.wait_for_timeout(900)
    pg.evaluate("()=>document.querySelector('.class-card.is-ifc').click()"); pg.wait_for_timeout(900)
    e = pg.evaluate("()=>!!document.querySelector('.class-enroll')")
    g["chk"]("a class you are not in still opens its enrolment", e)
    ctx.close(); br.close()
sys.exit(0 if g["ok"] else 1)
