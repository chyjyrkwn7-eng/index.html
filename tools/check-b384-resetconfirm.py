"""Build 384 r18: Reset asks twice, and its descriptions say it resets the account.
Madison, Settings > Advanced: "Reset thing need a double confirmation just to be sure.. the description under it needs to be solid too, needs
to mention it will reset your account."
 (1) the footnote under Reset says it resets the account and that you will be asked twice;
 (2) Reset opens a first screen whose red button goes on to a SECOND screen (nothing is reset by it);
 (3) Cancel on either screen goes back to Settings and resets nothing;
 (4) only the second screen's red button resets (resetEverything runs exactly once, on that tap);
 (5) both screens say it resets the account; no page errors.
Run:  python3 tools/check-b384-resetconfirm.py   (--against OLD/index.html must FAIL)"""
import os, sys, re, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
if "--against" in sys.argv:
    body = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
    cb.BODY = cb.INSET_RE.sub("0px", body).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
with sync_playwright() as pw:
    br = pw.chromium.launch()
    ctx, pg = cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:140]))
    pg.evaluate("()=>{ window.__resets = 0; resetEverything = function(){ window.__resets++; }; showAdvancedSettings(); }"); pg.wait_for_timeout(1200)
    foot = pg.evaluate("()=>{ const b=document.getElementById('resetbtn'); const c=b.closest('.settings-card'); const n=c && c.nextElementSibling; return n ? n.textContent : ''; }")
    chk("(1) the footnote under Reset says it resets the account and that you are asked twice (%s)" % foot[:120], re.search(r"account", foot, re.I) and re.search(r"twice|two", foot, re.I), foot)
    STATE = "()=>{ const p=document.querySelector('.resetwarning-panel'); return p ? { step: p.dataset.resetStep || '1', text: p.innerText, red: !!p.querySelector('.resetwarning-confirm') } : null; }"
    pg.evaluate("()=>document.getElementById('resetbtn').click()"); pg.wait_for_timeout(500)
    s1 = pg.evaluate(STATE)
    chk("(2) Reset opens a first confirmation (%s)" % (s1 and s1["text"][:60].replace("\n", " | ")), s1 and s1["red"] and s1["step"] == "1", s1)
    pg.evaluate("()=>document.querySelector('.resetwarning-confirm').click()"); pg.wait_for_timeout(500)
    s2 = pg.evaluate(STATE); n = pg.evaluate("()=>window.__resets")
    chk("(2) its red button goes on to a SECOND screen and resets nothing (step %s, resets %s)" % (s2 and s2["step"], n), s2 and s2["step"] == "2" and n == 0, [s2, n])
    chk("(5) both screens say it resets the account", s1 and s2 and re.search(r"account", s1["text"], re.I) and re.search(r"account", s2["text"], re.I), [s1 and s1["text"][:80], s2 and s2["text"][:80]])
    # cancel on the second
    pg.evaluate("()=>document.querySelector('.resetwarning-panel .ghost').click()"); pg.wait_for_timeout(700)
    back = pg.evaluate("()=>({ warn: !!document.querySelector('.resetwarning-panel'), n: window.__resets, adv: !!document.getElementById('resetbtn') || !!document.querySelector('#stage .screen-settings, #stage .screen-settings-sub') })")
    chk("(3) Cancel on the second screen leaves the warning and resets nothing (%s)" % back, not back["warn"] and back["n"] == 0, back)
    # cancel on the first
    pg.evaluate("()=>{ showAdvancedSettings(); }"); pg.wait_for_timeout(700)
    pg.evaluate("()=>document.getElementById('resetbtn').click()"); pg.wait_for_timeout(400)
    pg.evaluate("()=>document.querySelector('.resetwarning-panel .ghost').click()"); pg.wait_for_timeout(600)
    b1 = pg.evaluate("()=>({ warn: !!document.querySelector('.resetwarning-panel'), n: window.__resets })")
    chk("(3) Cancel on the first screen resets nothing (%s)" % b1, not b1["warn"] and b1["n"] == 0, b1)
    # full path
    pg.evaluate("()=>{ showAdvancedSettings(); }"); pg.wait_for_timeout(700)
    pg.evaluate("()=>document.getElementById('resetbtn').click()"); pg.wait_for_timeout(300)
    pg.evaluate("()=>document.querySelector('.resetwarning-confirm').click()"); pg.wait_for_timeout(300)
    mid = pg.evaluate("()=>window.__resets")
    pg.evaluate("()=>document.querySelector('.resetwarning-confirm').click()"); pg.wait_for_timeout(300)
    end = pg.evaluate("()=>window.__resets")
    chk("(4) only the second screen's red button resets, once (after the first %s, after the second %s)" % (mid, end), mid == 0 and end == 1, [mid, end])
    chk("(5) no page errors", not errs, errs)
    br.close()
print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
