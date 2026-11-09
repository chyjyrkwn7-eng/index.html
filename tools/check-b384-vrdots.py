#!/usr/bin/env python3
"""Build 384 r8: in a Virtual Room the question dots stay in their own place.
Madison (a race question, the dots circled with "move up"): "the amount of questions or the question progress bar needs to be in
its normal spot, that way the pause button and chat button are still in great spots, and then the stuff under it within the virtual
room modes will look good."
A real drill question on an iPhone 17 Pro Max and an iPad Pro 11", then the same question with the race line up and pinned:
(1) the dots (#meter) are at the same height as in an ordinary question (1px); (2) the race track starts below the dots;
(3) Pause and the chat button do not touch the track or its finish flag; (4) the dots stay where they are when the page scrolls;
(5) with the race line gone the dots are back in their own place in the page (after the line) and still where an ordinary
question puts them; (6) no page errors.
  python3 tools/check-b384-vrdots.py [--against OLD/index.html]   (must FAIL on the build before)"""
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
START = """()=>{ const t='Identity Crimes'; cfg.mode='drill'; runMode='drill'; cfg.units=[t]; cfg.source='all';
  beginRun(QUESTIONS.map((q,i)=>[q,i]).filter(([q])=>(q.topic||'').trim()===t).map(([,i])=>i), null, null); }"""
G = """()=>{ const b=s=>{const e=document.querySelector(s); if(!e||!e.offsetParent&&getComputedStyle(e).position!=='fixed') return null; const r=e.getBoundingClientRect(); return {t:r.top,b:r.bottom,l:r.left,r:r.right};};
  const m=document.getElementById('meter'), rb=document.getElementById('vroomracebar');
  return { meter:b('#meter'), track:b('.vroom-racetrack'), flag:b('.vroom-racetrack-finish'), pause:b('#pausebtn'),
    chat:[...document.querySelectorAll('.chatdock-btn')].map(e=>e.getBoundingClientRect()).filter(r=>r.width>0).map(r=>({t:r.top,b:r.bottom,l:r.left,r:r.right}))[0]||null,
    afterLine: !!(m && rb && rb.nextElementSibling===m), inLine: !!(m && rb && m.parentElement===rb) }; }"""
hit = lambda a, c: a and c and not (a["b"] <= c["t"] or c["b"] <= a["t"] or a["r"] <= c["l"] or c["r"] <= a["l"])
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    for lab, w, h in (("iPhone 17 Pro Max", 440, 956), ("iPad Pro 11in", 834, 1194)):
        ctx, pg = cb.booted(br, w, h, seed=cb.USED_ACCOUNT, dpr=1)
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        pg.evaluate(START)
        for _ in range(40):
            if pg.evaluate("()=>!!document.querySelector('.qpanel .choice')"): break
            pg.wait_for_timeout(250)
        pg.wait_for_timeout(1000)
        n = pg.evaluate(G)
        pg.evaluate("""()=>{ const rb=document.getElementById('vroomracebar'); rb.hidden=false; inVirtualRoom=true;
          const m=document.getElementById('vroomracemarkers'); ['0%','50%','100%'].forEach(l=>{ const d=document.createElement('div'); d.className='vroom-race-marker'; d.style.left=l; m.appendChild(d); });
          syncTestPin(true); }""")
        pg.wait_for_timeout(800)
        v = pg.evaluate(G)
        chk("(1) %s: the dots at their ordinary height (%.1f, ordinary %.1f)" % (lab, v["meter"]["t"] if v["meter"] else -1, n["meter"]["t"]),
            v["meter"] and abs(v["meter"]["t"] - n["meter"]["t"]) <= 1, (n, v))
        chk("(2) %s: the race track starts below the dots" % lab, v["meter"] and v["track"] and v["track"]["t"] >= v["meter"]["b"], v)
        clear = not any(hit(x, y) for x in (v["pause"], v["chat"]) for y in (v["track"], v["flag"]))
        chk("(3) %s: Pause and the chat button touch neither the track nor its flag" % lab, clear, v)
        pg.evaluate("()=>{ document.querySelector('.qpanel').style.minHeight='3000px'; window.scrollTo({top:400, behavior:'instant'}); }"); pg.wait_for_timeout(500)
        s = pg.evaluate(G)
        chk("(4) %s: scrolled, the dots stay put (%.1f)" % (lab, s["meter"]["t"] if s["meter"] else -1), s["meter"] and abs(s["meter"]["t"] - v["meter"]["t"]) <= 1, s)
        pg.evaluate("()=>{ window.scrollTo({top:0, behavior:'instant'}); document.querySelector('.qpanel').style.minHeight=''; const rb=document.getElementById('vroomracebar'); rb.hidden=true; inVirtualRoom=false; syncTestPin(true); }")
        pg.wait_for_timeout(600)
        e = pg.evaluate(G)
        chk("(5) %s: with the line gone, the dots are back in their own place and height" % lab,
            e["afterLine"] and not e["inLine"] and e["meter"] and abs(e["meter"]["t"] - n["meter"]["t"]) <= 1, e)
        chk("(6) %s: no page errors" % lab, not errs, errs[:3])
        ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILURES"); sys.exit(0 if ok else 1)
