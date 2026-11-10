"""Build 384 r9: the sync code card is What's new's card. Madison, the card circled: "This should match the what's new frost look".
On Home (iPhone 17 Pro Max and iPad Pro 11"), read off What's new (.intro-card) and the sync code card (.savecode-card) on the same page:
 (1) the frosted sheet is the same (background, backdrop blur, edge, shadow);
 (2) the eyebrow is What's new's colour (white, not gold); the title is the app's sans, NOT What's new's serif (384 r16: "why does the
     font look weird here" - the confirm family left the serif, see check-b384-popglass.py);
 (3) the code sits in What's new's frosted panel (.intro-gate-note's wash and edge), not a dark slab;
 (4) ticked, Continue is What's new's "Got it" pill (same fill, same ink); and no page errors.
Run:  python3 tools/check-b384-savefrost.py   (--against OLD/index.html must FAIL)"""
import os, re, sys, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
if "--against" in sys.argv:
    body = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
    cb.BODY = cb.INSET_RE.sub("0px", body).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)
R = """(sel)=>{ const e=document.querySelector(sel); if(!e) return null; const c=getComputedStyle(e);
  return { bg:c.backgroundColor, bi:c.backgroundImage, bf:c.backdropFilter||c.webkitBackdropFilter, bd:c.borderTopColor, sh:c.boxShadow, ff:c.fontFamily, col:c.color }; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch()
    for lab, W, H in (("iPhone 17 Pro Max", 440, 956), ("iPad Pro 11in", 834, 1194)):
        ctx, pg = cb.booted(br, W, H, seed=cb.USED_ACCOUNT, dpr=1)
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        pg.evaluate("()=>showHome()"); pg.wait_for_timeout(1200)
        pg.evaluate("()=>showIntroPopup({})"); pg.wait_for_timeout(1000)
        I = {k: pg.evaluate(R, s) for k, s in (("card", ".intro-card"), ("eye", ".intro-eyebrow"), ("title", ".intro-title"), ("note", ".intro-gate-note"), ("go", ".intro-go"))}
        pg.evaluate("()=>document.getElementById('intro-pop').remove()")
        pg.evaluate("()=>showSaveCodeCard({})"); pg.wait_for_timeout(1000)
        S = {k: pg.evaluate(R, s) for k, s in (("card", ".savecode-sheet"), ("eye", ".savecode-tag"), ("title", ".savecode-title"), ("val", ".savecode-value"))}
        pg.click(".savecode-ack"); pg.wait_for_timeout(400)
        S["go"] = pg.evaluate(R, ".savecode-continue")
        same = lambda k: all(I["card"][x] == S["card"][x] for x in ("bg", "bi", "bf", "bd", "sh"))
        chk("(1) %s: the same frosted sheet" % lab, same("card"), [I["card"], S["card"]])
        chk("(2) %s: the eyebrow What's new's colour (%s / %s) and the title the app's sans, not the serif" % (lab, S["eye"]["col"], I["eye"]["col"]),
            S["eye"]["col"] == I["eye"]["col"] and not re.search(r"Georgia|Iowan|Palatino", S["title"]["ff"]), [S["eye"]["col"], S["title"]["ff"][:30], I["title"]["ff"][:30]])
        note = I["note"] or {"bi": "linear-gradient(rgba(61, 139, 255, 0.16), rgba(61, 139, 255, 0.06))", "bd": "rgba(143, 193, 255, 0.38)"}
        chk("(3) %s: the code in What's new's frosted panel" % lab, S["val"]["bi"] == note["bi"] and S["val"]["bd"] == note["bd"], [S["val"]["bi"][:90], S["val"]["bd"], note["bi"][:90]])
        chk("(4) %s: Continue is the Got it pill (%s / %s)" % (lab, S["go"]["bg"], I["go"]["bg"]), S["go"]["bg"] == I["go"]["bg"] and S["go"]["col"] == I["go"]["col"], [S["go"], I["go"]])
        chk("%s: no page errors" % lab, not errs, errs[:2])
        ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
