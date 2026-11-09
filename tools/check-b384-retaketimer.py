"""Build 384 r9: a retake of missed questions has no clock. Madison: "When doing a retake? Why is there a timer for the retake
questions? There shouldn't be?" With the test timer on (counting up, and counting down), on an iPhone 17 Pro Max:
 (1) an ordinary drill shows the clock (so the timer setting is really on);
 (2) a "Retake missed questions" run shows no clock and no Best chip, and nothing times it out after the countdown would have ended;
 (3) no page errors.
Run:  python3 tools/check-b384-retaketimer.py   (--against OLD/index.html must FAIL)"""
import os, sys, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
if "--against" in sys.argv:
    body = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
    cb.BODY = cb.INSET_RE.sub("0px", body).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
RUN = """(o)=>{ cfg.timer=o.timer; cfg.timerMinutes=1; const t='Identity Crimes'; cfg.mode='drill'; runMode='drill'; cfg.units=[t]; cfg.source='all';
  const ix = QUESTIONS.map((q,i)=>[q,i]).filter(([q])=>(q.topic||'').trim()===t).map(([,i])=>i).slice(0, 5);
  beginRun(ix, null, null, o.retake); }"""
SEE = "()=>{ const t=document.getElementById('timerline'), b=document.getElementById('tbest') || document.querySelector('.tbest'); return { clock: !!t && !t.hidden && t.getBoundingClientRect().height > 0, best: !!b && !b.hidden && b.getBoundingClientRect().width > 0, over: !document.querySelector('.qpanel .choice') }; }"
with sync_playwright() as pw:
    br = pw.chromium.launch()
    for timer in ("up", "down"):
        for retake in (False, True):
            ctx, pg = cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT, dpr=1)
            errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
            pg.evaluate(RUN, {"timer": timer, "retake": retake})
            for _ in range(40):
                if pg.evaluate("()=>!!document.querySelector('.qpanel .choice')"): break
                pg.wait_for_timeout(250)
            pg.wait_for_timeout(800)
            s = pg.evaluate(SEE)
            tag = "timer %s, %s" % (timer, "retake" if retake else "drill")
            if not retake:
                chk("(1) %s: the clock is up (the setting is on)" % tag, s["clock"], s)
            else:
                chk("(2) %s: no clock, no Best" % tag, not s["clock"] and not s["best"], s)
                if timer == "down":
                    pg.evaluate("()=>{ const n=Date.now; Date.now=()=>n()+120000; }"); pg.wait_for_timeout(900)
                    s2 = pg.evaluate(SEE)
                    chk("(2) %s: a minute's countdown later it is still running (not timed out)" % tag, not s2["over"], s2)
            chk("(3) %s: no page errors" % tag, not errs, errs[:2])
            ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
