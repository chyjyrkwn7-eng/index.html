#!/usr/bin/env python3
"""Build 384 r8/r9: the Virtual Room choice screen. (r9: (2c) is the cards right under the line - Madison: "maybe they should just be back towards the top on the phone, and then for larger devices just side by side?" - stacked on a phone, side by side from 40rem.) FINAL (Madison): "needs to be like the mode selection screen. Title at the top,
description under it, then the boxes are centered.." - (1) the line under the title at the top, (2c) the cards + Inbox note centred
between that line and the tab bar, (2d) the cards' contents left-aligned like Choose your mode's. History: (The vertical centring this gate first held was reverted - Madison: "Centering the
virtual room stuff??? Why would you center it like that?" - its legs (1)-(2) are off; (2b) and (3) stand. (2c): Madison then said "Center this" meant the cards' contents - their icon and title row and words are centred.)
Madison, everything under the title circled: "Center this".
On an iPhone 17 Pro Max, an iPad Pro 11" and an iPhone SE: (1) the group under the title (the line, the games, the two cards, the
Inbox note) has as much room above it (to the title bar) as below it (to the tab bar) - 4px; on
a screen too short for it (the group runs under the tab bar and the page scrolls) it starts just under the title and nothing overflows sideways; (2) the group is below the title bar and above the tab bar; (2b) nothing on it that is not a button is drawn like one (Madison: "The stuff at the top, they look like buttons" - the three game
pills are a sentence now); (3) no errors.
  python3 tools/check-b384-vrcenter.py [--against OLD/index.html]   (must FAIL on the build before)"""
import os, sys, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = cb.INSET_RE
    cb.patched = lambda ins: IR.sub(lambda m: {"top": "%dpx" % ins[0], "right": "%dpx" % ins[1], "bottom": "%dpx" % ins[2], "left": "%dpx" % ins[3]}[m.group(1)], OLD)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
M = """()=>{ const p=document.querySelector('.screen-vroom-choice'); const kids=[...p.children]; const nav=p.querySelector(':scope > .ios-nav');
  const rest=kids.filter(k=>k!==nav); const pr=p.getBoundingClientRect(), nr=nav.getBoundingClientRect();
  const top=Math.min(...rest.map(k=>k.getBoundingClientRect().top)), bot=Math.max(...rest.map(k=>k.getBoundingClientRect().bottom));
  const pb=parseFloat(getComputedStyle(p).paddingBottom)||0; const tb=document.querySelector('.bottomtabs'); const tbt=tb?tb.getBoundingClientRect().top:innerHeight;
  return { above: top-nr.bottom, below: tbt-bot, top, bot, navB:nr.bottom, tab:tbt, sw: document.documentElement.scrollWidth, vw: innerWidth }; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    for lab, w, h in (("iPhone 17 Pro Max", 440, 956), ("iPad Pro 11in", 834, 1194), ("iPhone SE", 375, 667)):
        ctx, pg = cb.booted(br, w, h, seed=cb.USED_ACCOUNT, dpr=1)
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        pg.evaluate("()=>{ window.vroomDb = window.vroomDb || (()=>({})); showVirtualRoomChoice(); }"); pg.wait_for_timeout(1200)
        m = pg.evaluate(M)
        base = min(m["above"], m["below"])
        if False: chk("(1) %s: as much room above the group (to the title) as below it (to the tab bar) (%.0f / %.0f)" % (lab, m["above"], m["below"]), (abs(m["above"] - m["below"]) <= 4 if m["below"] > 0 else m["above"] <= 30) and m["sw"] <= m["vw"], m)
        if False: chk("(2) %s: the group sits between the title bar and the tab bar" % lab, m["top"] >= m["navB"] and (m["bot"] <= m["tab"] or h < 700), m)
        pills = pg.evaluate("""()=>{ const p=document.querySelector('.screen-vroom-choice'); const nav=p.querySelector(':scope > .ios-nav');
          return [...p.querySelectorAll('*')].filter(e=>!nav.contains(e) && e.getBoundingClientRect().width>0).filter(e=>{ const c=getComputedStyle(e);
            const boxed=(c.backgroundColor!=='rgba(0, 0, 0, 0)' && c.backgroundColor!=='transparent') || parseFloat(c.borderTopWidth)>0;
            const tap=e.closest('button, a, [role=button], .modecard'); return boxed && !tap && parseFloat(c.borderTopLeftRadius)>=8; }).map(e=>e.className).slice(0,5); }""")
        chk("(2b) %s: nothing that is not a button is drawn like one - no boxed pills (%s)" % (lab, pills), not pills, pills)
        g = pg.evaluate("""()=>{ const p=document.querySelector('.screen-vroom-choice'), sub=p.querySelector(':scope > .cal-sub'), nav=p.querySelector(':scope > .ios-nav');
          const grp=[...p.querySelectorAll(':scope > .vrc-modecards, :scope > .vrc-note')]; const top=Math.min(...grp.map(k=>k.getBoundingClientRect().top)), bot=Math.max(...grp.map(k=>k.getBoundingClientRect().bottom));
          const tb=document.querySelector('.bottomtabs'); const fl=tb&&tb.getBoundingClientRect().height>0?tb.getBoundingClientRect().top:innerHeight;
          const ms=[...document.querySelectorAll('.vrc-modecard')].map(c=>{ const r=c.getBoundingClientRect(), t=c.querySelector('.modecardtitlerow').getBoundingClientRect(); return t.left - r.left; });
          return { subGap: sub.getBoundingClientRect().top - nav.getBoundingClientRect().bottom, above: top - sub.getBoundingClientRect().bottom, below: fl - bot, titleIn: ms }; }""")
        chk("(1) %s: the title and the line under it at the top (line %.0fpx under the title bar)" % (lab, g["subGap"]), 0 <= g["subGap"] <= 30, g)
        # (384 r9) the centring is reverted - "The two virtual options, maybe they should just be back towards the top on the phone,
        # and then for larger devices just side by side?" - (2c) is now: right under the line, and side by side from 40rem
        cards = pg.evaluate("()=>[...document.querySelectorAll('.vrc-modecard')].map(c=>{const r=c.getBoundingClientRect(); return [r.left, r.top, r.width];})")
        chk("(2c) %s: the cards right under the line (%.0fpx below it)" % (lab, g["above"]), 0 <= g["above"] <= 30, g)
        side = len(cards) == 2 and abs(cards[0][1] - cards[1][1]) < 2 and abs(cards[0][0] - cards[1][0]) > 50
        chk("(2c) %s: %s" % (lab, "side by side" if w >= 640 else "stacked"), side if w >= 640 else (len(cards) == 2 and cards[1][1] > cards[0][1]), cards)
        chk("(2d) %s: the cards' contents start at the left like Choose your mode's (%s)" % (lab, [round(v) for v in g["titleIn"]]), all(v < 40 for v in g["titleIn"]), g)
        z = pg.evaluate("()=>({ note: !!document.querySelector('.screen-vroom-choice .vrc-note'), h: [...document.querySelectorAll('.vrc-modecard')].map(c=>c.getBoundingClientRect().height), sub: document.querySelector('.screen-vroom-choice > .cal-sub').getBoundingClientRect().height })")
        chk("(2e) %s: no Inbox heads-up; a one-line description; the two cards (Choose your mode's size - the bigger cards were reverted) (%s, line %.0fpx)" % (lab, [round(v) for v in z["h"]], z["sub"]), not z["note"] and z["sub"] <= 30 and len(z["h"]) == 2, z)
        chk("(3) %s: no page errors" % lab, not errs, errs[:3])
        ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILURES"); sys.exit(0 if ok else 1)
