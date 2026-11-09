"""Build 384 r9: your own Profile card always carries a rank line. Madison, at level 21 with no badges: "Our current rank should be
here, similar to how it looks when you view someone on leaderboard and click them". On Profile (iPhone 17 Pro Max, iPad Pro 11"),
both classes, for an account below Iron:
 (1) the rank line (.profile-rankline, the person card's .person-card-rank) is there, between the name and "Level N · N badges",
     the words "No rank yet" and no flare (a flare is a rank held - "why is the bronze flare next to it?");
 (2) the words are the line's soft colour (not a rank's colour, not white) and no page errors.
Run:  python3 tools/check-b384-profrank.py   (--against OLD/index.html must FAIL)"""
import os, sys, json, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
if "--against" in sys.argv:
    body = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
    cb.BODY = cb.INSET_RE.sub("0px", body).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
a = json.loads(cb.USED_ACCOUNT); a["publicId"] = "xph5b57jbp5a"; a["novaMet"] = 99; IACCT = json.dumps(a)
IINIT = ("try{localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));localStorage.setItem('class26e.greet.ifc','done');"
         "['intro.seen','unithold.tip','daily.seen','weekrecap.v1','savecode.card'].forEach(k=>localStorage.setItem('class26e.ifc.'+k, k==='weekrecap.v1'?'9999-12-31':'9'));"
         "localStorage.setItem('class26e.ifc.drill.v1', %s);}catch(e){}" % json.dumps(IACCT))
M = """()=>{ const q=s=>document.querySelector(s); const rl=q('.profile-rankline'), nm=[...document.querySelectorAll('#stage *')].find(e=>e.childElementCount===0 && e.textContent.trim()==='Madison' || false);
  const lv=q('.pf-level'); const r=e=>e?e.getBoundingClientRect():null;
  return { rank: rankOf(store), has: !!rl, text: rl ? rl.textContent.trim() : '', mark: !!(rl && rl.querySelector('.person-card-mark')),
    col: rl ? getComputedStyle(rl.querySelector('.person-card-rankword')).color : '', soft: getComputedStyle(document.documentElement).getPropertyValue('--soft').trim(),
    lvTop: lv ? r(lv).top : null, rlTop: rl ? r(rl).top : null, rlBot: rl ? r(rl).bottom : null }; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch()
    for cls in ("academy", "ifc"):
        for lab, W, H in (("iPhone 17 Pro Max", 440, 956), ("iPad Pro 11in", 834, 1194)):
            ctx, pg = (cb.booted(br, W, H, seed=IACCT, dpr=1, init=IINIT) if cls == "ifc" else cb.booted(br, W, H, seed=cb.USED_ACCOUNT, dpr=1))
            errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
            pg.evaluate("()=>showProfile()"); pg.wait_for_timeout(1200)
            m = pg.evaluate(M); tag = "%s %s" % (cls, lab)
            if m["rank"]: chk("%s: the fixture is below Iron" % tag, False, m); ctx.close(); continue
            # (r9, next) "No rank yet, why is the bronze flare next to it?" - no flare without a rank
            chk("(1) %s: the rank line is there, above the level: 'No rank yet' and NO flare (%r)" % (tag, m["text"]),
                m["has"] and not m["mark"] and m["text"].lower() == "no rank yet" and m["rlBot"] <= m["lvTop"] + 1, m)
            soft = pg.evaluate("(c)=>{ const d=document.createElement('i'); d.style.color=c; document.body.appendChild(d); const v=getComputedStyle(d).color; d.remove(); return v; }", m["soft"] or "#999")
            chk("(2) %s: in the soft colour (%s) and no page errors" % (tag, m["col"]), m["col"] == soft and not errs, [m["col"], soft, errs[:2]])
            ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
