#!/usr/bin/env python3
"""Build 384 full check: the sign-up class step fits a phone, and "More classes" is a row, not a third card.

With Fire Code beside the academy, "More classes" wrapped to a row of its own in a two-column grid whose rows are all as tall
as the tallest (a ~300px box saying "Coming soon"), and the sign-up step's Continue fell below the fold on every iPhone but a
Pro Max (338px of scroll on an SE 2nd/3rd gen, 193 on a 13 mini). Now the box is a slim full-width row (sign-up at every
width, the Classes screen on a phone), the two cards draw tighter on a short phone, and where the step still cannot fit (a
small phone in Safari) picking a class brings Continue into view.

  python3 tools/check-b384-classstep.py [--against OLD/index.html]   (must FAIL on the build before)
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
from playwright.sync_api import sync_playwright
BODY = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read() if "--against" in sys.argv else None
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
seed = dict(rc["SEED"]); seed["seenClassTip"] = True
MEASURE = """()=>{ const R=e=>{ if(!e) return null; const b=e.getBoundingClientRect(); return { l:b.left, t:b.top, r:b.right, b:b.bottom, w:b.width, h:b.height }; };
  const grid=document.querySelector('#stage .class-cards'), soon=document.querySelector('#stage .class-card.is-soon');
  const title=soon && soon.querySelector('.cc-title'), chip=soon && soon.querySelector('.cc-status');
  const lh = title ? parseFloat(getComputedStyle(title).lineHeight) || parseFloat(getComputedStyle(title).fontSize) * 1.2 : 0;
  const note=document.querySelector('#stage .classselect-panel > .affiliation-note'), cont=document.getElementById('nextbtn');
  const tw = title ? (() => { const g = document.createRange(); g.selectNodeContents(title); return g.getBoundingClientRect(); })() : null;
  return { vh: innerHeight, grid: R(grid), soon: R(soon), titleLines: title ? Math.round(title.getBoundingClientRect().height / lh) : 0,
    textRight: tw ? tw.right : null, textBottom: tw ? tw.bottom : null, chip: R(chip), note: R(note), cont: R(cont), cards: [...document.querySelectorAll('#stage .class-card:not(.is-soon)')].map(R) }; }"""
srv, port = rc["serve"]()
def page(br, w, h, account):
    ctx = br.new_context(viewport={"width": w, "height": h}, has_touch=True); pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    init = "localStorage.setItem('class26e.drill.v1',%s);localStorage.setItem('class26e.intro.seen','99');" % json.dumps(json.dumps(seed)) if account else "localStorage.setItem('class26e.getstarted','1');"
    pg.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.a2hs','1');localStorage.setItem('class26e.frame.ok','go-live-1');%s}catch(e){}" % init)
    pg.route("**/version.json", lambda r, q: r.abort())
    if BODY is not None:
        pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(2600)
    return ctx, pg, errs
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    errs_all = []
    # the sign-up step: fits (no scroll to Continue) on these, and is brought into view on the two short ones
    for w, h, fits in ((375, 667, True), (375, 812, True), (393, 742, True), (440, 956, True), (834, 1194, True), (375, 548, False), (320, 568, False),
                       (1440, 820, True), (1366, 638, False)):
        ctx, pg, errs = page(br, w, h, False)
        pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); document.querySelectorAll('.gs-page').forEach(n=>n.remove()); showClassSelection(); }")
        pg.wait_for_timeout(1500)
        pg.tap("#stage .class-card.is-academy"); pg.wait_for_timeout(1200)
        m = pg.evaluate(MEASURE); errs_all += errs; ctx.close()
        tag = "%dx%d sign-up" % (w, h)
        s, g = m["soon"], m["grid"]
        # (384.136, changed on purpose: Madison, "This 'more classes' thing should be bigger, should be the same size as the other class
        # boxes for a cohesive look") More classes is a class card the same size as the others at every width: in line with them where
        # they sit side by side (a tablet, a laptop), one of the stacked rows on a phone; its name never runs under its chip
        same = s and all(abs(s[k] - m["cards"][0][k]) < 2 for k in ("w", "h"))
        chk("%s: 'More classes' is the same size as the class cards (%dx%d; a class card %dx%d)" % (tag, s["w"], s["h"], m["cards"][0]["w"], m["cards"][0]["h"]), same, (s, m["cards"]))
        if w >= 640:
            chk("%s: side by side, 'More classes' in line with the classes" % tag, abs(s["t"] - m["cards"][0]["t"]) < 2, (s, m["cards"]))
        chk("%s: its name is clear of its chip (%s lines, text ends %s, chip starts %s)" % (tag, m["titleLines"], m["textRight"] and round(m["textRight"]), m["chip"] and round(m["chip"]["l"])),
            # (384.136) a full-size card sets its chip in the card's foot, under the name (a tablet, a laptop), or beside it (a phone's
            # row): either way the name's ink and the chip do not meet
            m["textRight"] is not None and (m["textRight"] <= m["chip"]["l"] - 4 or m["textBottom"] <= m["chip"]["t"] - 4), m)
        c, n = m["cont"], m["note"]
        chk("%s: after a pick Continue is on the screen (bottom %d of %d)" % (tag, c["b"], m["vh"]), c and c["h"] > 0 and c["b"] <= m["vh"] + .5, c)
        chk("%s: ... and clear of the small print above it (%dpx)" % (tag, c["t"] - n["b"]), n and c["t"] - n["b"] >= 8, (n, c))
    # it fits without the pick's scroll: measured before any tap
    # (384.136) with More classes a full card, a phone's step is three rows tall: on an SE, a 13 mini and a phone in Safari Continue
    # comes into view with the pick's scroll (held above, on every size); a laptop window still fits with nothing scrolled
    for w, h in ((1440, 820), (1536, 864)):
        ctx, pg, errs = page(br, w, h, False)
        pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); document.querySelectorAll('.gs-page').forEach(n=>n.remove()); showClassSelection(); }")
        pg.wait_for_timeout(1500)
        m = pg.evaluate("()=>{ const c=document.getElementById('nextbtn'); c.hidden=false; const b=c.getBoundingClientRect(); return { b: b.bottom, vh: innerHeight }; }")
        errs_all += errs; ctx.close()
        chk("%dx%d sign-up: Continue is above the fold with nothing scrolled (bottom %d of %d)" % (w, h, m["b"], m["vh"]), m["b"] <= m["vh"], m)
    # the Classes screen on a phone: the same row; on a tablet three across, as before
    for w, h in ((375, 667), (440, 956), (834, 1194)):
        ctx, pg, errs = page(br, w, h, True)
        pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); homeUnlocksOwed=()=>false; document.querySelectorAll('.unlock-card,.rs-spot').forEach(n=>n.remove()); showClassCatalog(); }")
        pg.wait_for_timeout(1500)
        m = pg.evaluate(MEASURE); errs_all += errs; ctx.close()
        s, g, cards = m["soon"], m["grid"], m["cards"]
        if w < 640:
            chk("%dx%d Classes: 'More classes' is the same size as the class cards (384.136)" % (w, h), all(abs(s[k] - cards[0][k]) < 2 for k in ("w", "h")), (s, cards))
        else:
            chk("%dx%d Classes: three across on a tablet, 'More classes' in line with the classes" % (w, h), abs(s["t"] - cards[0]["t"]) < 2 and abs(s["h"] - cards[0]["h"]) < 2, (s, cards))
    chk("no page errors", not errs_all, errs_all[:3])
    br.close()
srv.shutdown()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
