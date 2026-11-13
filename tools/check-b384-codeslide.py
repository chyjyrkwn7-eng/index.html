#!/usr/bin/env python3
"""Build 384 review: Fire Code's "Show the code" drops down, and stays down.

Madison: "when hitting 'show the code' in the ifc tests ... ensure when you hit that drop down, it's a very smooth and nice
transition. Not just instant, it will be instant, just make it actually nicely drop down." and "when you enable show code drop
down, ensure it stays like that unless you hit the button again. Cause every question I'm having to hit the drop down if I want
to always see it."
In a Fire Code drill of county questions (their code is the county booklet in the repo, drawn with pdf.js), on an iPhone:
(1) a tap on "Show the code" starts the box growing at once and it grows over several frames (never one jump), only ever growing,
    to its full height, then is let go (no fixed height left);
(2) the next answer comes with the code shown, without a tap;
(3) a tap on "Hide the code" shrinks it over several frames back to the pill, and it ends shut;
(4) the next answer then comes with it shut;
(5) a Review list does not open its boxes because the choice was "open" (it would draw every one on the page);
(6) no page errors.
Run:  PDFJS_DIR=<unpacked pdfjs-dist 5.4.149 package> python3 tools/check-b384-codeslide.py [--against OLD/index.html]   (must FAIL there)"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b382-test.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b382-test.py"), "__name__": "b384cs"}
exec(src, G)
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = G["g"]["INSET_RE"]
    def _old(ins):
        t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
        return IR.sub(lambda m: v[m.group(1)], OLD)
    G["g"]["patched"] = _old
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
# the box's height on every frame for a while after a tap (started just before it)
# (384.119) the height SHOWN, not the height laid out: the box is laid out once and swept open or shut by a clip-path on its card
# (ifcDropOpen / ifcDropShut), so what is seen is the part of the box above the card's clipped bottom. On builds before 384.119
# nothing is clipped and this is the box's height, as it always measured. The shape asked for is unchanged.
TRACE = """(ms)=>{ window.__h=[]; const t0=performance.now();
  const clipB = el => { const m = /inset\\(([^)]*?)(?:\\sround\\b|\\))/.exec(getComputedStyle(el).clipPath || ''); if(!m) return 0; const v = m[1].trim().split(/\\s+/).map(parseFloat); return (v.length >= 3 ? v[2] : v[0]) || 0; };
  /* read in a task after each frame is drawn: a read inside the frame's first rAF callback comes before the app's own rAF work */
  const s=()=>{ const d=document.querySelector('.qpanel details.ifc-code');
  if(d){ const c = d.closest('.ifc-ref') || d, r = d.getBoundingClientRect(), cr = c.getBoundingClientRect(); const shown = Math.max(0, Math.min(r.bottom, cr.bottom - clipB(c)) - r.top);
    window.__h.push([Math.round(performance.now()-t0), Math.round(shown*10)/10, d.open, d.style.height]); } };
  const f=()=>{ setTimeout(s, 0); if(performance.now()-t0<ms) requestAnimationFrame(f); }; requestAnimationFrame(f); }"""
def answer(pg, cdp):
    G["answer_right"](pg, cdp)
def next_q(pg):
    pg.evaluate("()=>{ const b=document.getElementById('nextbtn'); if(b) b.click(); }")
    for _ in range(60):
        if pg.evaluate("()=>!!document.querySelector('.qpanel .choice') && !document.querySelector('.qpanel .choice.is-right, .qpanel .choice.correct, .qpanel .choice.right')"): break
        pg.wait_for_timeout(150)
    pg.wait_for_timeout(900)
def grew(trace):
    hs = [x[1] for x in trace if x[2] or x[3]]
    if len(hs) < 3: return False, "too few frames"
    steps = len({h for h in hs}) - 1
    mono = all(b >= a - .5 for a, b in zip(hs, hs[1:]))
    return steps >= 5 and mono and not trace[-1][3], {"distinct": steps, "mono": mono, "first": hs[:3], "last": hs[-2:], "styleLeft": trace[-1][3]}
def shrank(trace):
    hs = [x[1] for x in trace]
    steps = len({h for h in hs}) - 1
    mono = all(b <= a + .5 for a, b in zip(hs, hs[1:]))
    return steps >= 5 and mono and not trace[-1][2] and not trace[-1][3], {"distinct": steps, "mono": mono, "first": hs[:3], "last": hs[-2:], "open": trace[-1][2]}
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    label, w, h, ins, ua = G["SIZES"][0]
    ctx, pg, cdp = G["page"](br, w, h, ins, ua)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    pg.evaluate("()=>{ try{ localStorage.removeItem('class26e.codeopen'); }catch(e){} }")
    G["start"](pg, "short", 4)
    answer(pg, cdp)
    shut0 = pg.evaluate("()=>{ const d=document.querySelector('.qpanel details.ifc-code'); return d ? d.open : null; }")
    # (1) open
    pg.evaluate(TRACE, 1600)
    G["tap"](cdp, *pg.evaluate(G["CENTRE"], ".qpanel .ifc-code-sum"))
    pg.wait_for_timeout(1900)
    t1 = pg.evaluate("()=>window.__h")
    if os.environ.get("SHOW_TRACE"): print("TRACE-OPEN", [(x[0], x[1]) for x in t1][:60])
    g1, info1 = grew(t1)
    chk("(1) the first answer comes shut (%s); a tap grows the box over several frames, only growing, then lets it go (%s)" % (shut0, info1), shut0 is False and g1, t1[:12])
    # (2) the next answer: shown by itself
    next_q(pg); answer(pg, cdp)
    open2 = pg.evaluate("()=>{ const d=document.querySelector('.qpanel details.ifc-code'); return d ? d.open : null; }")
    chk("(2) the next answer comes with the code shown, untouched (%s)" % open2, open2 is True)
    # (3) close
    pg.wait_for_timeout(1500)
    pg.evaluate(TRACE, 1200)
    G["tap"](cdp, *pg.evaluate(G["CENTRE"], ".qpanel .ifc-code-sum"))
    pg.wait_for_timeout(1500)
    t3 = pg.evaluate("()=>window.__h")
    if os.environ.get("SHOW_TRACE"): print("TRACE-CLOSE", [(x[0], x[1]) for x in t3][:40])
    s3, info3 = shrank(t3)
    chk("(3) a tap on Hide shrinks it over several frames back to the pill and it ends shut (%s)" % info3, s3, t3[:12])
    # (4) the next answer: shut
    next_q(pg); answer(pg, cdp)
    open4 = pg.evaluate("()=>{ const d=document.querySelector('.qpanel details.ifc-code'); return d ? d.open : null; }")
    chk("(4) after closing it, the next answer comes shut (%s)" % open4, open4 is False)
    # (5) a list of them does not open everything
    pg.evaluate("()=>{ try{ localStorage.setItem('class26e.codeopen','1'); }catch(e){} const q = QUESTIONS.find(q=>q.ifc && q.ifc.citation && q.ifc.citation.source==='amendment'); showAnswerReview([q.topic.trim()], 'all'); }")
    pg.wait_for_timeout(2500)
    lst = pg.evaluate("()=>({ boxes: document.querySelectorAll('#stage details.ifc-code').length, open: document.querySelectorAll('#stage details.ifc-code[open]').length })")
    chk("(5) a Review list does not open its boxes for it (%s)" % lst, lst["boxes"] > 1 and lst["open"] == 0, lst)
    chk("(6) no page errors", not errs, errs[:3])
    br.close()
G["srv"].shutdown()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
