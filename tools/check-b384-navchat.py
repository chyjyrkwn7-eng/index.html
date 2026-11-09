#!/usr/bin/env python3
"""Build 384 r8: the back button and the chat button mirror each other's corners.
Madison (Virtual Room, the two circled): "Why aren't the chat button and button in line with each other? They should be perfectly
symmetrical with each of their own corners?"
On every pushed screen with a round back button (Choose your mode, Virtual Room, Customize's pages, Friends, a Settings page), on an
iPhone 17 Pro Max and an iPad Pro 11": (1) the two are the same size; (2) their tops are level (.5px); (3) the chat button is as far
in from the right edge as the back button is from the left (.5px); (4) back on Home, the chat button is back in its own place
(no pushed-screen position left over); (5) no page errors.
  python3 tools/check-b384-navchat.py [--against OLD/index.html]   (must FAIL on the build before)"""
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
M = """()=>{ const back=document.querySelector('#stage .ios-nav > .ios-nav-back'); const chat=document.getElementById('chatdock-btn');
  const r=e=>{ if(!e) return null; const b=e.getBoundingClientRect(); return b.width ? {l:b.left, t:b.top, w:b.width, h:b.height, r:innerWidth-b.right} : null; };
  return { back:r(back), chat:r(chat) }; }"""
SCREENS = [("Choose your mode", "showModeSelect()"), ("Virtual Room", "window.vroomDb = window.vroomDb || (()=>({})); showVirtualRoomChoice()"),
           ("Customize", "showProfile('profile'); setTimeout(()=>{ const b=[...document.querySelectorAll('#stage .settings-row, #stage button')].find(e=>/Customize/.test(e.textContent)); b&&b.click(); }, 300)"),
           ("Friends", "showFriends()"), ("a Settings page", "showAppearance({page:'sync'})")]
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    for lab, w, h in (("iPhone 17 Pro Max", 440, 956), ("iPad Pro 11in", 834, 1194)):
        ctx, pg = cb.booted(br, w, h, seed=cb.USED_ACCOUNT, dpr=1)
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        pg.evaluate("()=>{ showHome(); }"); pg.wait_for_timeout(900)
        home0 = pg.evaluate(M)["chat"]
        seen = 0
        for name, go in SCREENS:
            pg.evaluate("()=>{ %s; }" % go); pg.wait_for_timeout(1300)
            m = pg.evaluate(M)
            if not m["back"] or not m["chat"]:
                continue
            seen += 1
            b, c = m["back"], m["chat"]
            chk("(1) %s, %s: one size (back %.0f, chat %.0f)" % (lab, name, b["w"], c["w"]), abs(b["w"] - c["w"]) <= .5 and abs(b["h"] - c["h"]) <= .5, m)
            chk("(2) %s, %s: level (tops %.1f / %.1f)" % (lab, name, b["t"], c["t"]), abs(b["t"] - c["t"]) <= .5, m)
            chk("(3) %s, %s: mirrored corners (%.1f in from the left, %.1f from the right)" % (lab, name, b["l"], c["r"]), abs(b["l"] - c["r"]) <= .5, m)
        chk("(1-3) %s: pushed screens measured (%d)" % (lab, seen), seen >= 3, seen)
        pg.evaluate("()=>{ showHome(); }"); pg.wait_for_timeout(1100)
        home1 = pg.evaluate(M)["chat"]
        chk("(4) %s: back on Home, the chat button is in its own place" % lab, home0 and home1 and abs(home0["t"] - home1["t"]) <= .5 and abs(home0["r"] - home1["r"]) <= .5, (home0, home1))
        chk("(5) %s: no page errors" % lab, not errs, errs[:3])
        ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILURES"); sys.exit(0 if ok else 1)
