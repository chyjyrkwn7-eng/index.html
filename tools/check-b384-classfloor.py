#!/usr/bin/env python3
"""Build 384 r11: the sign-up class step fits its screen and its Continue is on the shared floor.

check-positions flagged it on every build of the day: on an iPhone 13 mini (375x812, installed) the step ran 15px past
the screen and its Continue sat 34px under the line every other sign-up step's Continue shares; in a laptop window
(1366x638, 1280x670, 1440x770, 1512x852 in a browser) it scrolled 27-101px. This walks the same devices the same way
check-positions does (its seed, its insets, its standalone patch, showWelcome() first) and asserts:

  A  the class step does not scroll on the SE 2nd/3rd gen (r13: the cards stacked as rows there), the 13 mini, the Dell Latitude, the MacBook Pro 14", the MacBook Air and the
     small laptop, and Continue is fully on the screen there;
  B  on the SE 2nd/3rd gen and the 13 mini (and the other phones that already shared the floor: 14/15/16, Pro Max, Android phone) its Continue's
     top is within 2px of the other sign-up steps' (the median of the five);
  C  no type on the step got smaller than the build before it: the cards' title and line, the line under the title and
     the small print keep their computed sizes on those devices (a fit bought by shrinking text is not the fix).

  D  on the SE 2nd/3rd gen the class cards are full-width rows, one per row (the mark, kicker and name beside each other),
     and still carry every part: kicker, name, line, Fire Code's "Needs" line, the chip; a pick does not move Continue.

    python3 tools/check-b384-classfloor.py [--against OLD/index.html]   (must FAIL on the build before)
"""
import io, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
CP = os.path.join(HERE, "check-positions.py")
g = {"__file__": CP, "__name__": "cp"}
exec(io.open(CP, encoding="utf-8").read().rsplit("\nmain()", 1)[0], g)
from playwright.sync_api import sync_playwright

AGAINST = sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else None
SRC = io.open(AGAINST or os.path.join(g["ROOT"], "index.html"), encoding="utf-8").read()
def patched(ins):
    t, r, b, l = ins
    v = {"top": f"{t}px", "right": f"{r}px", "bottom": f"{b}px", "left": f"{l}px"}
    return g["INSET_RE"].sub(lambda m: v[m.group(1)], SRC)

FITS = ["iPhone SE (2nd/3rd gen)", "iPhone 13 mini", "Dell Latitude", "MacBook Pro 14-inch", "MacBook Air", "small laptop"]
FLOOR = ["iPhone SE (2nd/3rd gen)", "iPhone 13 mini", "iPhone 14 / 15 / 16", "iPhone 16/17 Pro Max", "Android phone"]
# the type as it was signed off (the build before this round), read off that build on these devices: none may shrink
TYPE_MIN = {"cc-title": 18.4, "cc-desc": 13.12, "sub": 16.0, "note": 10.88, "kicker": 10.56}
TYPE_MIN_ANDROID = {"note": 9.92, "cc-title": 16.32, "cc-desc": 12.16}   # 360px: the 22.5rem tier (base) draws these
TYPE_MIN_SE = {"cc-desc": 12.16}   # 375x667: the short-phone tier (base) draws the line at .76rem

ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond)
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  -> " + str(info)[:300]), flush=True)

SETTLE = """async ()=>{
  const read = () => { const b = document.querySelector('.next.playbtn'); const r = b.getBoundingClientRect();
    return {top: Math.round(r.top), bottom: Math.round(r.bottom), sh: document.documentElement.scrollHeight, vh: innerHeight}; };
  const frame = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  let prev = read();
  for(let i = 0; i < 20; i++){ await frame(); const now = read(); if(now.top === prev.top && now.sh === prev.sh) return now; prev = now; }
  return prev; }"""
TYPE = """()=>{ const p = document.querySelector('#stage .classselect-panel'); const fs = s => { const e = p.querySelector(s);
    return e ? parseFloat(getComputedStyle(e).fontSize) : null; };
  return { 'cc-title': fs('.class-card:not(.is-soon) .cc-title'), 'cc-desc': fs('.class-card:not(.is-soon) .cc-desc'),
           kicker: fs('.class-card:not(.is-soon) .cc-kicker'), sub: fs('.classselect-sub'), note: fs('.affiliation-note') }; }"""

srv, url = g["serve"]()
errs = []
try:
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=g["CHROME"])
        for name, w, h, plat, ins in g["DEVICES"]:
            if name not in FITS and name not in FLOOR: continue
            installed = plat != "desktop"
            if not installed:
                h = max(320, h - g["CHROME_H"][plat][0]); ins = (0, 0, 0, 0)
            ctx = br.new_context(viewport={"width": w, "height": h})
            ctx.add_init_script(g["SEED"])
            if installed: ctx.add_init_script(g["STANDALONE"])
            page = ctx.new_page(); body = patched(ins)
            page.on("pageerror", lambda e: errs.append(str(e)[:160]))
            page.route("**/index.html", lambda route, request, b=body: route.fulfill(
                status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
            page.goto(url); page.wait_for_timeout(2300)
            page.evaluate("document.getElementById('splashscreen')?.remove()")
            tag = f"{name} {w}x{h}" + ("" if installed else " browser")
            tops = {}
            for fn in g["ONBOARDING"]:
                g["run"](page, fn)
                if fn == "showWelcomeCharacterPrompt": page.wait_for_timeout(500)
                m = page.evaluate(SETTLE)
                tops[fn] = m
                if fn == "showClassSelection":
                    ty = page.evaluate(TYPE)
            cs = tops["showClassSelection"]
            if name in FITS:
                chk(f"A {tag}: the class step does not scroll ({cs['sh'] - cs['vh']}px) and Continue is on the screen (bottom {cs['bottom']} of {cs['vh']})",
                    cs["sh"] <= cs["vh"] + 1 and cs["bottom"] <= cs["vh"], cs)
            if name in FLOOR:
                others = sorted(v["top"] for k, v in tops.items() if k != "showClassSelection")
                med = others[len(others) // 2]
                chk(f"B {tag}: class step's Continue at y={cs['top']}, the other steps' at {med} (all {others})",
                    abs(cs["top"] - med) <= 2, (cs, others))
            mins = dict(TYPE_MIN, **(TYPE_MIN_ANDROID if name == "Android phone" else TYPE_MIN_SE if "SE" in name else {}))
            small = {k: (ty.get(k), v) for k, v in mins.items() if ty.get(k) is None or ty[k] + .01 < v}
            if "SE (2nd" in name:
                d = page.evaluate("""async ()=>{ showWelcome(); await new Promise(r=>setTimeout(r,120)); showClassSelection(); scrollTo(0,0);
                  await new Promise(r=>setTimeout(r,900));
                  const R = e => e.getBoundingClientRect(); const grid = document.querySelector('#stage .classselect-cards');
                  const cards = [...grid.querySelectorAll('.class-card:not(.is-soon)')];
                  const parts = cards.map(c => ['.cc-emblem','.cc-kicker','.cc-title','.cc-desc','.cc-status'].every(s => { const e = c.querySelector(s); return e && R(e).height > 0; }));
                  const ifc = document.querySelector('#stage .class-card.is-ifc .cc-needs');
                  const rowish = cards.map(c => { const m = R(c.querySelector('.cc-emblem')), t = R(c.querySelector('.cc-title')); return t.left > m.right && t.top < m.bottom; });
                  const b = document.getElementById('nextbtn'); b.hidden = false; const top0 = Math.round(R(b).top);
                  cards[0].click(); cards[1].click(); await new Promise(r=>setTimeout(r,700)); scrollTo(0,0); await new Promise(r=>setTimeout(r,200));
                  return { w: cards.map(c => Math.round(R(c).width)), gw: Math.round(R(grid).width), tops: cards.map(c => Math.round(R(c).top)), h: cards.map(c => Math.round(R(c).height)),
                           parts, needs: !!(ifc && R(ifc).height > 0), rowish, top0, top1: Math.round(R(b).top), sh: document.documentElement.scrollHeight, vh: innerHeight }; }""")
                chk(f"D {tag}: the class cards are full-width rows, one per row (widths {d['w']} of {d['gw']}, tops {d['tops']}, heights {d['h']})",
                    all(abs(x - d["gw"]) <= 2 for x in d["w"]) and d["tops"][1] >= d["tops"][0] + d["h"][0] and all(d["rowish"]), d)
                chk(f"D {tag}: every part is still there (mark, kicker, name, line, chip; Fire Code's Needs line)", all(d["parts"]) and d["needs"], d)
                chk(f"D {tag}: picking both does not move Continue ({d['top0']} -> {d['top1']}) or scroll ({d['sh'] - d['vh']}px)",
                    abs(d["top1"] - d["top0"]) <= 1 and d["sh"] <= d["vh"] + 1, d)
            chk(f"C {tag}: no type on the step smaller than signed off ({', '.join('%s %.2f' % (k, v or 0) for k, v in ty.items())})", not small, small)
            ctx.close()
        br.close()
finally:
    srv.shutdown()
chk("no page errors", not errs, errs[:3])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
