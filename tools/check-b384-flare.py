"""Build 384: the secret flare's "Tap" - only after a miss, per colour; a burst when it is tapped; the bubble's point.
Madison: "Secret flare 'tap' button, only appear when they miss it the first time, don't show that the first time a flare comes up,
for each color even. But if they miss it, then next time it's there it should say tap. Ensure when you tap it, it does a cool
animation. ensure the pointy part lines up in the tap bubble box thing cause it looked off."
A drill on an iPhone 17 Pro Max, the flare put on the question on screen:
(1) a colour's first appearance (no flare found, nothing missed): no "Tap";
(2) moving on past it without tapping notes that colour as missed (store.flareMissed);
(3) the next run with that colour: "Tap" beside it; (4) another colour, never missed: no "Tap";
(5) the bubble is one solid shape - no outline, its point the body's own fill, the point's centre on the body's left edge and its
    middle on the body's middle (within 1px);
(6) a tap: the burst - ten sparks and two rings out of the orb - and the orb's own burst running (not the beckon);
(7) a flare on the LAST question and the run finished without it: missed too;
(8) the miss is saved with the account and read back (applyLoadedData), and a second device's miss merges in (mergeSameAccount);
(9) no page errors.
Run:  python3 tools/check-b384-flare.py   (--against OLD/index.html must FAIL)"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b382-savecode.py")).read().split("\nwith sync_playwright() as pw:")[0]
g = {"__file__": os.path.join(HERE, "check-b382-savecode.py"), "__name__": "b384fl"}
exec(src, g)
from playwright.sync_api import sync_playwright
fails = g["fails"] = []
ck = g["ck"]
START = """(n)=>{ const t=topicsIn(QUESTIONS)[3]; cfg.mode='drill'; runMode='drill'; cfg.units=[t]; cfg.source='all';
  beginRun(QUESTIONS.map((q,i)=>[q,i]).filter(([q])=>(q.topic||'').trim()===t).map(([,i])=>i).slice(0, n), null, null); }"""
WAITQ = "()=>!!document.querySelector('.qpanel .choice')"
PUT = """(c)=>{ mysteryColorThisRun = c; mysteryAppearsAtPos = pos; mysteryFoundThisSession = false; render(); }"""
TAG = "()=>{ const b=document.querySelector('.qpanel .mystery-spark'); return b ? { spark: true, tap: !!b.querySelector('.mystery-tap') } : { spark: false, tap: false }; }"
ANSWER_NEXT = """async ()=>{ const w=ms=>new Promise(r=>setTimeout(r,ms)); const q=QUESTIONS[order[pos]]; const ch=[...document.querySelectorAll('.qpanel .choice')];
  const right = ch.find(c => (c.querySelector('.text')||c).textContent.trim() === String(q.choices[q.answer]).trim()) || ch[0]; right.click(); await w(500);
  const n=document.querySelector('#nextbtn'); if(n && !n.hidden) n.click(); await w(900); return pos; }"""
def run(pg, n):
    pg.evaluate("()=>{ try{ testInProgress=false; paused=false; stopTimer(); stopQuestionTimer(); }catch(e){} showHome(); }"); pg.wait_for_timeout(600)
    pg.evaluate(START, n)
    for _ in range(60):
        if pg.evaluate(WAITQ): break
        pg.wait_for_timeout(250)
    pg.wait_for_timeout(900)
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    errs = []
    ctx, pg = g["open_page"](br, g["init_account"]("", g["store"](mysteryColorsFound={}, flareMissed={})), errs=errs)
    # (1) first appearance
    run(pg, 4)
    pg.evaluate(PUT, "orange"); pg.wait_for_timeout(700)
    t1 = pg.evaluate(TAG)
    ck("(1) a colour's first appearance: the flare, no 'Tap' (%s)" % t1, t1["spark"] and not t1["tap"], t1)
    # (2) moving on past it
    pg.evaluate(ANSWER_NEXT); pg.wait_for_timeout(500)
    m = pg.evaluate("()=>({ missed: Object.assign({}, store.flareMissed || {}), pos })")
    ck("(2) moving on past it untapped notes the colour as missed (%s)" % m, (m["missed"] or {}).get("orange") is True, m)
    # (3) next run, same colour
    run(pg, 4)
    pg.evaluate(PUT, "orange"); pg.wait_for_timeout(700)
    t3 = pg.evaluate(TAG)
    ck("(3) the next time that colour comes up: 'Tap' beside it (%s)" % t3, t3["spark"] and t3["tap"], t3)
    # (5) the bubble: one solid shape, the point on the body's edge and middle
    shape = pg.evaluate("""()=>{ const t=document.querySelector('.qpanel .mystery-spark .mystery-tap'); if(!t) return null;
      const s=t.getBoundingClientRect(); const c=getComputedStyle(t), be=getComputedStyle(t,'::before'), af=getComputedStyle(t,'::after');
      const rot = new DOMMatrixReadOnly(be.transform);
      const bw = parseFloat(be.width), bh = parseFloat(be.height), bl = parseFloat(be.left), bt = parseFloat(be.top) + parseFloat(be.marginTop || 0);
      return { tagBorder: parseFloat(c.borderLeftWidth) || 0, beBorder: parseFloat(be.borderLeftWidth) || 0, afBorder: parseFloat(af.borderLeftWidth) || 0,
               fillSame: be.backgroundColor === af.backgroundColor && be.backgroundColor !== 'rgba(0, 0, 0, 0)', tagBg: c.backgroundColor,
               cx: bl + bw / 2, cy: bt + bh / 2, h: s.height, angle: Math.round(Math.atan2(rot.b, rot.a) * 180 / Math.PI) }; }""")
    ck("(5) the bubble is one solid shape: no outline anywhere, the point the body's own fill (%s)" % shape,
       shape and shape["tagBorder"] == 0 and shape["beBorder"] == 0 and shape["afBorder"] == 0 and shape["fillSame"] and shape["tagBg"] == "rgba(0, 0, 0, 0)", shape)
    ck("(5) the point's centre is on the body's left edge and its middle on the body's middle (%s)" % (shape and [round(shape["cx"], 1), round(shape["cy"], 1), shape["h"]],),
       shape and abs(shape["cx"]) <= 1 and abs(shape["cy"] - shape["h"] / 2) <= 1 and abs(shape["angle"]) == 45, shape)
    # (6) a tap: the burst
    pg.evaluate("()=>document.querySelector('.qpanel .mystery-spark').click()"); pg.wait_for_timeout(120)
    b = pg.evaluate("""()=>{ const s=document.querySelector('.qpanel .mystery-spark'); if(!s) return null; const p=s.querySelector('.mystery-pop');
      const sv=s.querySelector('svg'); return { found: s.classList.contains('mystery-spark-found'), sparks: p ? p.querySelectorAll('i').length : 0, rings: p ? p.querySelectorAll('b').length : 0,
        orb: sv ? getComputedStyle(sv).animationName : null, sparkAnim: p && p.querySelector('i') ? getComputedStyle(p.querySelector('i')).animationName : null }; }""")
    ck("(6) a tap bursts it: ten sparks and two rings out of the orb, the orb's own burst running (%s)" % b,
       b and b["found"] and b["sparks"] == 10 and b["rings"] == 2 and b["orb"] == "mystery-burst" and b["sparkAnim"] == "mystery-spark-fly", b)
    pg.wait_for_timeout(1200)
    # (4) another colour, never missed
    run(pg, 4)
    pg.evaluate(PUT, "yellow"); pg.wait_for_timeout(700)
    t4 = pg.evaluate(TAG)
    ck("(4) another colour, never missed: no 'Tap' (%s)" % t4, t4["spark"] and not t4["tap"], t4)
    # (7) on the last question, the run finished without it
    run(pg, 2)
    pg.evaluate(ANSWER_NEXT); pg.wait_for_timeout(400)
    pg.evaluate(PUT, "violet"); pg.wait_for_timeout(600)
    pg.evaluate(ANSWER_NEXT); pg.wait_for_timeout(1500)
    m7 = pg.evaluate("()=>Object.assign({}, store.flareMissed || {})")
    ck("(7) a flare on the last question, the run finished without it: missed (%s)" % m7, m7.get("violet") is True, m7)
    # (8) saved with the account, read back by applyLoadedData (a reload's path - the harness re-seeds storage on a real reload),
    # and a second device's miss merges in
    m8 = pg.evaluate("""()=>{ const saved = JSON.parse(localStorage.getItem('class26e.drill.v1') || '{}'); const before = saved.flareMissed || null;
      applyLoadedData(JSON.parse(JSON.stringify(saved))); return { saved: before, loaded: Object.assign({}, store.flareMissed || {}) }; }""")
    mg = pg.evaluate("()=>{ const dst = JSON.parse(JSON.stringify(store)); mergeSameAccount(dst, { flareMissed: { white: true } }); return dst.flareMissed; }")
    ck("(8) the misses are saved and read back (%s) and another device's merges in (%s)" % (m8, mg),
       (m8["saved"] or {}).get("orange") is True and m8["loaded"].get("orange") is True and m8["loaded"].get("violet") is True
       and (mg or {}).get("white") is True and (mg or {}).get("orange") is True, [m8, mg])
    ck("(9) no page errors", not errs, errs[:3])
    br.close()
print("\nALL PASS" if not fails else "\nFAILED: %d" % len(fails))
sys.exit(1 if fails else 0)
