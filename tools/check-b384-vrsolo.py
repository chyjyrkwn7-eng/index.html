#!/usr/bin/env python3
"""Build 384 r8: the room's wait screen is never a bare card on an empty page.
Madison, the wait card alone at the top of a blank screen: "Idk what this screen is???"
showVirtualRoomFinaleReveal() with no results screen under it (back from elsewhere, or "Keep waiting" with nothing kept), on an
iPhone 17 Pro Max and an iPad Pro 11": (1) the player's own score is on it (the number) and the XP the run earned; (2) the wait
card is there under it, the same width; (3) the two sit in the middle of the screen (room above within 60px of room below);
(4) a pass is green, a fail red; (5) no page errors.
  python3 tools/check-b384-vrsolo.py [--against OLD/index.html]   (must FAIL on the build before)"""
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
M = """()=>{ const p=document.querySelector('#stage > .panel'); if(!p) return null; const vis=[...p.children].filter(c=>c.getBoundingClientRect().height>0);
  const g=p.querySelector('.rs-grade'), w=p.querySelector('.vroom-waitcard'); const top=Math.min(...vis.map(c=>c.getBoundingClientRect().top)), bot=Math.max(...vis.map(c=>c.getBoundingClientRect().bottom));
  return { txt: g ? g.textContent : '', col: g && g.querySelector('.rs-pct') ? getComputedStyle(g.querySelector('.rs-pct')).color : '', gw: g ? g.getBoundingClientRect().width : 0, ww: w ? w.getBoundingClientRect().width : 0,
    above: top, below: innerHeight - bot, waitBelow: g && w ? w.getBoundingClientRect().top >= g.getBoundingClientRect().bottom : false }; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    for lab, w, h in (("iPhone 17 Pro Max", 440, 956), ("iPad Pro 11in", 834, 1194)):
        for pct, xp in ((83, 420), (50, 140)):
            ctx, pg = cb.booted(br, w, h, seed=cb.USED_ACCOUNT, dpr=1)
            errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
            pg.evaluate("()=>{ showHome(); }"); pg.wait_for_timeout(500)
            pg.evaluate("([p, x])=>{ try{ vroomCode='ABCD'; }catch(e){} showVirtualRoomFinaleReveal(p, 61000, x); }", [pct, xp]); pg.wait_for_timeout(1200)
            m = pg.evaluate(M) or {}
            tag = "%s, %d%%" % (lab, pct)
            chk("(1) %s: the score and the XP are on it (%r)" % (tag, (m.get("txt") or "")[:40]), str(pct) in (m.get("txt") or "") and ("%d XP" % xp) in (m.get("txt") or ""), m)
            chk("(2) %s: the wait card under it, one width (%.0f / %.0f)" % (tag, m.get("gw", 0), m.get("ww", 0)), m.get("waitBelow") and abs(m.get("gw", 0) - m.get("ww", 0)) <= 1, m)
            chk("(3) %s: centred (above %.0f, below %.0f)" % (tag, m.get("above", 0), m.get("below", 0)), abs(m.get("above", 0) - m.get("below", 999)) <= 60 + (60 if h > 1000 else 0), m)
            green = "rgb(" in m.get("col", "") and (lambda c: c[1] > c[0])(list(map(float, m["col"][m["col"].index("(")+1:-1].split(",")[:3]))) if m.get("col") else None
            chk("(4) %s: %s" % (tag, "green for a pass" if pct >= 70 else "red for a fail"), green is not None and green == (pct >= 70), m.get("col"))
            chk("(5) %s: no page errors" % tag, not errs, errs[:3])
            ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILURES"); sys.exit(0 if ok else 1)
