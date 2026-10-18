"""The end of a run is two screens (build 212).

  python3 tools/check-results.py                 # this build
  python3 tools/check-results.py --against OLD   # must FAIL on build 211

"Split the test result screens up": a rewards screen first (XP, level,
badges, the grade, unlock banners one after another) and, only when
something was missed, a review screen behind a "Continue to review"
button. What is held here is the SHAPE of that, not its words:

  1. The rewards screen carries no review - no missed questions, no
     Retake - and says "Test results" where the progress bar was.
  2. It arrives in order: the grade first (build 320 - it was last),
     then the XP lines one at a time, the total after them. Measured off
     the moment each card lands, not off the source.
  3. The button is not there until everything has landed, and on a
     missed run it goes to a review screen that has the missed
     questions and the Retake / Main menu pair.
  4. Unlock banners come one at a time, and the buttons wait for the
     last of them.
  5. (build 213) No Pause on either results screen; the review shows the
     answer you gave; the XP lines come from computeRunXp() and follow its
     rules (speed in steps of 5, streak tiers with xN, multi-unit last,
     retake = right answers only); Re-run is back. (Game's bonuses and
     its lost-game screen went with Game mode in build 283.)
  6. Reduce motion gets everything at once and no banners.
  9. (build 315) One type system, set by the grade: no serif and no
     old-style figures anywhere on the results screens - the rewards
     screen, the review, a retake, a no-XP run, the daily question's
     verdict, the Virtual Room's results and its leaderboard - and every
     number in the grade's own sans with tabular figures, pseudo-element
     text included. Then the measured rules that make it one screen: one
     size per role (kicker, label, caption), one text edge for every card,
     every right-hand number ending on the content edge, the same gap
     under every card's heading, landed XP lines in their own slots, every
     pair written "N / M", and no half-width button label on two lines at
     320px or 375px. Fails on f543e95 and on 94a3108^ (the serif grade).

Drives summarize() directly with a real unit's questions, the way
check-behaviour's badge routes do, so it is fast and deterministic.
"""
import functools, http.server, os, re, socket, sys, threading
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
_VR = open(os.path.join(ROOT, "tools", "check-vroom.py"), encoding="utf-8").read()
FAKE = re.search(r'FAKE_FIRESTORE = """(.*?)"""', _VR, re.S).group(1)
AGAINST = sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else None
BOTS = re.search(r'BOTS_313 = r"""(.*?)"""', _VR, re.S).group(1)

# ---- build 315: the results screens in one type system ----------------
# Every piece of text under the given roots (and every ::before/::after
# that says something), checked against what the grade number set: never
# a serif, never old-style figures, and a number is the --sans stack's own
# face with tabular figures. SVG artwork is not text and is skipped.
TYPE_AUDIT = r"""(sel)=>{
  const SERIF = /^(georgia|iowan old style|palatino linotype|palatino|times new roman|times|new york|charter|serif)$/i;
  const first = ff => (ff || '').split(',')[0].trim().replace(/^["']|["']$/g, '');
  const SANS = first(getComputedStyle(document.documentElement).getPropertyValue('--sans'));
  const issues = []; let n = 0, nums = 0;
  const audit = (cs, text, where, numeric) => {
    const fam = first(cs.fontFamily);
    if(SERIF.test(fam)) issues.push(['serif', where, text, fam]);
    if(/oldstyle-nums/.test(cs.fontVariantNumeric) || /["']onum["'](?!\s*(0|off))/.test(cs.fontFeatureSettings)) issues.push(['old-style figures', where, text]);
    if(numeric){
      nums++;
      if(fam !== SANS) issues.push(['a number not in the sans', where, text, fam]);
      if(!/tabular-nums/.test(cs.fontVariantNumeric)) issues.push(['a number not tabular', where, text, cs.fontVariantNumeric]);
    }
  };
  const nameOf = el => el.tagName.toLowerCase() + '.' + String(el.getAttribute('class') || '').trim().split(/\s+/)
    .filter(c => !/^rs-(land|in|in-now)$/.test(c)).slice(0, 2).join('.');
  [...document.querySelectorAll(sel)].forEach(root => [root, ...root.querySelectorAll('*')].forEach(el => {
    if(el.closest('svg') || !el.getClientRects().length) return;
    const cs = getComputedStyle(el);
    if(cs.visibility === 'hidden' || cs.display === 'none' || +cs.opacity === 0) return;
    const own = [...el.childNodes].filter(t => t.nodeType === 3 && t.textContent.trim()).map(t => t.textContent.trim()).join(' ');
    if(own){ n++; audit(cs, own.slice(0, 40), nameOf(el), /\d/.test(own)); }
    ['::before', '::after'].forEach(p => {
      const ps = getComputedStyle(el, p), c = ps.content || '';
      if(!c || c === 'none' || c === 'normal' || ps.display === 'none') return;
      const lit = (c.match(/"[^"]*"/g) || []).join('').replace(/"/g, '');
      const attrs = (c.match(/attr\(([^)]+)\)/g) || []).map(a => el.getAttribute(a.slice(5, -1).trim()) || '').join('');
      const text = (lit + ' ' + attrs).trim();
      if(!/[A-Za-z0-9]/.test(text)) return;
      n++; audit(ps, text.slice(0, 40), nameOf(el) + p, /\d/.test(text));
    });
  }));
  return { n, nums, issues };
}"""
# The shape of the screen, measured: one size per role, one text edge, the
# numbers on the right edge, the same gap under every heading (heading
# baseline to the first line's cap top, from the font's own metrics), the
# cards evenly spaced, landed XP lines untransformed, the header on one
# edge, and every pair "N / M".
SHAPE_AUDIT = r"""()=>{
  const R = v => Math.round(v * 10) / 10;
  const panel = document.querySelector('#stage .rs-screen'); if(!panel) return null;
  const shown = e => e.getClientRects().length && getComputedStyle(e).display !== 'none';
  const sizes = sel => [...new Set([...panel.querySelectorAll(sel)].filter(shown).map(e => getComputedStyle(e).fontSize))];
  const roles = {
    kicker: sizes('.rs-kicker, .rs-unlocked .unlockbanner-kicker, .rs-xp .results-level-rank, .rs-stamp, .rs-q-tag, .rs-q-answers p > span'),
    label: sizes('.rs-xpline-name, .rs-xpline-val, .rs-xptotal-label, .rs-byunit .unit-breakdown-name, .rs-byunit .unit-breakdown-score, .rs-badges .badgeprogress-name, .rs-unlocked .unlockbanner-name, .vroom-wait-line, .rs-unitlist li'),
    caption: sizes('.rs-xpline-sub, .rs-grade-sub, .rs-badges .badgeprogress-line, .rs-xp .results-level-line, .rs-q-ref, .vroom-wait-leave')
  };
  const cards = [...panel.querySelectorAll(':scope > .rs-card')].filter(shown);
  const box = c => { const r = c.getBoundingClientRect(), cs = getComputedStyle(c);
    return { t: r.top, b: r.bottom, cl: r.left + parseFloat(cs.borderLeftWidth) + parseFloat(cs.paddingLeft),
             cr: r.right - parseFloat(cs.borderRightWidth) - parseFloat(cs.paddingRight) }; };
  const B = cards.map(box);
  const left = el => { const rg = document.createRange(); rg.selectNodeContents(el); const q = rg.getClientRects()[0]; return q ? q.left : el.getBoundingClientRect().left; };
  const kickLeft = cards.map((c, i) => { const k = c.querySelector(':scope > .rs-kicker'); return k ? R(left(k) - B[i].cl) : 0; });
  const shortOfRight = [...panel.querySelectorAll('.rs-xpline-val, .rs-xptotal-unit, .rs-byunit .unit-breakdown-score, .vroom-wait-count')].filter(shown)
    .map(e => R(box(e.closest('.rs-card')).cr - e.getBoundingClientRect().right));
  const cv = document.createElement('canvas').getContext('2d');
  const met = el => { const cs = getComputedStyle(el); cv.font = cs.fontWeight + ' ' + cs.fontSize + ' ' + cs.fontFamily;
    const m = cv.measureText('H0'); return { asc: m.fontBoundingBoxAscent, cap: m.actualBoundingBoxAscent }; };
  const lines = root => { const out = []; const walk = n => {
      if(n.nodeType === 3 && n.textContent.trim()){ const p = n.parentElement; if(!shown(p) || getComputedStyle(p).visibility === 'hidden') return;
        const m = met(p), rg = document.createRange(); rg.selectNodeContents(n);
        [...rg.getClientRects()].forEach(q => { if(q.width > 1) out.push({ cap: q.top + m.asc - m.cap, base: q.top + m.asc }); }); }
      else if(n.nodeType === 1 && getComputedStyle(n).display !== 'none') [...n.childNodes].forEach(walk); };
    walk(root); return out.sort((a, b) => a.cap - b.cap); };
  const headingGaps = cards.map(c => { const k = c.querySelector(':scope > .rs-kicker'); if(!k) return null;
    const kl = lines(k); if(!kl.length) return null; const kb = kl[kl.length - 1].base;
    const after = lines(c).filter(l => l.cap > kb + 1); return after.length ? R(after[0].cap - kb) : null; }).filter(v => v != null);
  const head = []; const chip = panel.querySelector(':scope > .rs-head .rs-mode'); if(chip) head.push(R(chip.getBoundingClientRect().left));
  const ttl = panel.querySelector(':scope > .rs-head .rs-units'); if(ttl) head.push(R(left(ttl)));
  const lab = document.getElementById('testscopelabel'); if(lab && lab.textContent.trim() && shown(lab)) head.push(R(left(lab)));
  return { roles, contentLefts: B.map(b => R(b.cl)), contentRights: B.map(b => R(b.cr)), kickLeft, shortOfRight, headingGaps,
    cardGaps: B.slice(1).map((b, i) => R(b.t - B[i].b)),
    lifted: [...panel.querySelectorAll('.rs-xpline')].map(e => getComputedStyle(e).transform).filter(t => t && t !== 'none'),
    head, pairs: [...panel.querySelectorAll('.rs-grade-frac, .rs-byunit .unit-breakdown-score, .vroom-wait-count')].filter(shown).map(e => e.textContent) };
}"""
# Lines of text in each matching button's own label.
ONE_LINE = r"""(sel)=>[...document.querySelectorAll(sel)].filter(b => b.getClientRects().length).map(b => {
  const tops = new Set(); const walk = n => { if(n.nodeType === 3 && n.textContent.trim()){ const rg = document.createRange(); rg.selectNodeContents(n);
    [...rg.getClientRects()].forEach(q => { if(q.width > 1) tops.add(Math.round(q.top / 3)); }); } else if(n.nodeType === 1) [...n.childNodes].forEach(walk); };
  walk(b); return [b.textContent.trim(), tops.size]; })"""
spread = lambda xs: (max(xs) - min(xs)) if xs else 0

s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
threading.Thread(target=srv.serve_forever, daemon=True).start()

ok = True
def ck(name, cond, detail=""):
    global ok
    print(" ", "PASS" if cond else "FAIL", name, ("-> " + str(detail)) if detail else "")
    if not cond: ok = False

SETUP = """()=>{
  document.getElementById('splashscreen')?.remove(); try{ __useFake(); }catch(e){}
  store.onboardingComplete=true; store.firstName='Madison'; store.tourRev=99; store.rankMapFx244=true;
  store.retroBadgePending=[]; store.badgeBandsVersion=2;
  ['seenFirstResultsTour','seenModeSelectTour','seenProfileTour','seenRewardsTour','seenSettingsTour',
   'seenUnitOptionsTour','seenUnitSelectTour','seenMainMenuTour'].forEach(k=>store[k]=true);
  theme.muteBanners=false; theme.reduceMotion=false; saveStore(); showHome();
  /* Every card's landing, timed. */
  window.__lands=[]; const t0=performance.now();
  new MutationObserver(ms=>ms.forEach(m=>{ const el=m.target;
    if(!(el.classList && (el.classList.contains('rs-in')||el.classList.contains('rs-in-now')))) return;
    if(el.__landed) return; el.__landed=performance.now()-t0;
    const kind = el.classList.contains('rs-xpline')?'line' : el.classList.contains('rs-xptotal')?'total'
      : el.classList.contains('rs-grade')?'grade' : el.classList.contains('rs-actions')?'actions'
      : el.classList.contains('rs-unlocked')?'unlocked' : el.classList.contains('rs-head')?'head'
      : el.classList.contains('rs-xp')?'xp' : el.classList.contains('results-level')?'level' : 'box';
    __lands.push({kind, t:el.__landed}); })).observe(document.body,{subtree:true,attributes:true,attributeFilter:['class']});
  window.__spots=0; window.__maxSpots=0; window.__actionsDuringSpot=false; window.__caseSeen=false;
  setInterval(()=>{ if(document.querySelector('.bc-scene')) __caseSeen=true; }, 80);
  setInterval(()=>{ const n=document.querySelectorAll('.rs-spot').length; __maxSpots=Math.max(__maxSpots,n);
    if(n){ __spots++; const a=document.querySelector('.rs-actions');
      if(a && getComputedStyle(a).opacity > .5) __actionsDuringSpot=true; } }, 60);
  window.__run=(unit, missN, mode, retake)=>{
    __lands.length=0;
    cfg.mode=mode; cfg.source='all'; cfg.units=[unit]; cfg.size=0;
    order=QUESTIONS.map((q,i)=>i).filter(i=>(QUESTIONS[i].topic||'').trim()===unit);
    if(retake) order=order.slice(0,3);
    runTrackable=!retake; timedOut=false; runMode=mode; runLabel=retake?'Missed questions':null; isMissedRetake=!!retake;
    practiceTestMinutes=null; inVirtualRoom=false; attempts={}; picked={}; timedOutSet={};
    try{ firstPick = {}; }catch(e){}
    order.forEach((qi,k)=>{ const oo=optionOrder(qi), right=oo.indexOf(QUESTIONS[qi].answer);
      attempts[qi]=k<missN?2:1; picked[qi]=k<missN?(right+1)%oo.length:right;
      try{ if(k<missN) firstPick[qi]=(right+1)%oo.length; }catch(e){} });
    runStartTime=Date.now()-42000; testInProgress=true; pos=order.length-1;
    summarize();
  };
}"""
VISIBLE = """(sel)=>{ const e=document.querySelector(sel); if(!e) return false;
  const cs=getComputedStyle(e); return cs.display!=='none' && cs.visibility!=='hidden' && +cs.opacity>.5 && e.getClientRects().length>0; }"""
DONE = "()=>!!document.querySelector('.rs-rewards.rs-done')"

def wait_done(pg, ms=40000):
    for _ in range(ms // 250):
        try:
            if pg.evaluate(DONE): return True
        except Exception: pass
        pg.wait_for_timeout(250)
    return False

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    ctx = br.new_context(viewport={"width": 440, "height": 956})
    ctx.add_init_script(FAKE)
    ctx.add_init_script("try{localStorage.setItem('class26e.frame.ok','go-live-1');"
                        "localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.penal256578.seen','1');localStorage.setItem('class26e.daily.seen','x');}catch(e){}")
    pg = ctx.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    _html = open(AGAINST or os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    if AGAINST:
        pg.route("**/index.html", lambda r, q=None: r.fulfill(status=200, content_type="text/html", body=_html))
    # version.json always names the build being served, or an older
    # build under --against sees an update waiting and reloads mid-check.
    _bld = re.search(r'const APP_BUILD = "([^"]+)"', _html).group(1)
    pg.route("**/version.json*", lambda r, q=None: r.fulfill(status=200, content_type="application/json",
             body='{"build":"%s","frameId":""}' % _bld))
    pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(2500)
    pg.evaluate(SETUP); pg.wait_for_timeout(300)
    UNIT = "Identity Crimes"

    print("1. a run with three missed: the rewards screen")
    pg.evaluate("([u])=>__run(u,3,'drill')", [UNIT]); pg.wait_for_timeout(250)
    first = pg.evaluate("""()=>({
      title: (document.getElementById('testscopelabel')||{}).textContent,
      meterHidden: document.getElementById('meter').hidden,
      pause: !document.getElementById('pausebtn').hidden,
      review: document.querySelectorAll('#stage .review li, #stage .rs-q').length,
      retake: [...document.querySelectorAll('#stage button')].some(b=>/Retake/.test(b.textContent)),
      screen: (document.getElementById('stage').firstElementChild||{dataset:{}}).dataset.screen })""")
    ck("the header says Test results where the progress bar was",
       first["title"] == "Test results" and first["meterHidden"], first)
    ck("no missed questions on the rewards screen", first["review"] == 0, first)
    ck("and no Retake on it either", not first["retake"], first)
    ck("no Pause on the results - the chat button has the corner", not first["pause"], first)
    ck("the button is not there while the reveal is still playing",
       not pg.evaluate(VISIBLE, "#stage .rs-actions, #stage .actions"))
    done = wait_done(pg)
    ck("the reveal finishes", done)
    lands = pg.evaluate("()=>__lands.slice()")
    kinds = [l["kind"] for l in lands]
    t = lambda k: [l["t"] for l in lands if l["kind"] == k]
    lines = t("line")
    ck("the total lands after the lines, with a beat between",
       bool(t("total")) and bool(lines) and t("total")[0] - lines[-1] > 400, (lines, t("total")))
    # BUILD 320 REVERSED THIS: "grade box first ... you get a grade, you see
    # how that adds up, you get awards". The grade was the last card down;
    # it is the first now, ahead of the XP box and everything in it.
    xp_side = [l["t"] for l in lands if l["kind"] in ("xp", "line", "total", "level", "box")]
    ck("the grade lands first, before the XP box and its lines (build 320)",
       bool(t("grade")) and bool(xp_side) and t("grade")[0] < min(xp_side), kinds)
    ck("and the button after the grade",
       bool(t("actions")) and bool(t("grade")) and t("actions")[0] > t("grade")[0], kinds)
    cont = pg.evaluate("()=>{const b=document.querySelector('#stage .rs-continue'); return b? b.textContent: null}")
    ck("a missed run ends in Continue to review, with the count", cont == "Continue to review (3 missed)", cont)
    # BUILD 214: Re-run and Main menu are on the RESULTS, not the review -
    # "At the end of the test, on the result screen, that's where the re
    # run and main button need to be".
    res_btns = pg.evaluate("()=>[...document.querySelectorAll('#stage .actions button')].map(b=>b.textContent)")
    ck("and Re-run and Main menu beside it, on the results",
       res_btns == ["Continue to review (3 missed)", "Re-run", "Main menu"], res_btns)
    pg.evaluate("()=>document.querySelector('#stage .rs-continue') && document.querySelector('#stage .rs-continue').click()")
    pg.wait_for_timeout(400)
    rev = pg.evaluate("""()=>({
      title: (document.getElementById('testscopelabel')||{}).textContent,
      qs: document.querySelectorAll('#stage .rs-q').length,
      yours: document.querySelectorAll('#stage .rs-q .rs-q-yours').length,
      pctInHead: /%/.test((document.querySelector('#stage .rs-review-summary')||{}).textContent||''),
      btns: [...document.querySelectorAll('#stage .actions button')].map(b=>b.textContent),
      pause: !document.getElementById('pausebtn').hidden })""")
    ck("Continue opens the review, with exactly the missed questions",
       rev["qs"] == 3 and rev["title"] == "Test review", rev)
    ck("each one shows the answer you gave, Drill included", rev["yours"] == 3, rev)
    ck("and the count at the top carries no stray percentage", not rev["pctInHead"], rev)
    ck("the review offers the retake and the way back, and nothing else",
       rev["btns"] == ["Retake missed questions (3)", "Back to results"], rev)
    ck("so no Re-run and no Main menu while reviewing",
       not any(b in ("Re-run", "Main menu") for b in rev["btns"]), rev)
    pg.evaluate("()=>[...document.querySelectorAll('#stage .actions button')].find(b=>/Back to results/.test(b.textContent)).click()")
    pg.wait_for_timeout(300)
    back = pg.evaluate("()=>({ done: !!document.querySelector('.rs-rewards.rs-done'),"
      " spots: document.querySelectorAll('.rs-spot, .bc-scene, .fl-scene').length,"
      " btns: [...document.querySelectorAll('#stage .actions button')].map(b=>b.textContent) })")
    ck("Back to results is the finished screen at once, nothing replayed",
       back["done"] and back["spots"] == 0 and back["btns"] == res_btns, back)
    ck("no Pause on the review either", not rev["pause"], rev)

    print("2. a perfect run that earns a badge: banners one at a time")
    pg.evaluate("""([u])=>{ store.unitPerfects={}; store.unitPerfects[u]=badgeThresholdFor(u)-1;
      store.pendingBadgeUnlocks=[]; __maxSpots=0; __spots=0; __actionsDuringSpot=false; saveStore(); }""", [UNIT])
    pg.evaluate("([u])=>__run(u,0,'drill')", [UNIT])
    done = wait_done(pg, 60000)
    st = pg.evaluate("()=>({max:__maxSpots, seen:__spots, during:__actionsDuringSpot, caseSeen:!!window.__caseSeen,"
                     " cont: !!document.querySelector('#stage .rs-continue'),"
                     " btns:[...document.querySelectorAll('#stage .actions button')].map(b=>b.textContent),"
                     " unlocked: document.querySelectorAll('#stage .rs-unlocked .rs-unlock').length})")
    lines2 = [l["t"] for l in pg.evaluate("()=>__lands.slice()") if l["kind"] == "line"]
    ck("the XP lines drop in one at a time (correct answers, hundo, speed)",
       len(lines2) >= 3 and all(b - a > 150 for a, b in zip(lines2, lines2[1:])), lines2)
    # BUILD 215: a badge's moment is its case, at the unlock - "move that
    # cutscene to when it hits the unlock thing" - and no banner besides.
    ck("the badge came through as its case, not a banner", st["caseSeen"] and st["seen"] == 0, st)
    ck("never two banners at once", st["max"] <= 1, st)
    ck("and no progress box for the badge it earned",
       pg.evaluate("()=>document.querySelectorAll('#stage .rs-badges').length") == 0)
    ck("the buttons waited for the last banner", not st["during"], st)
    ck("a perfect run has nothing to review, so no Continue", done and not st["cont"] and len(st["btns"]) >= 1, st)
    ck("what it unlocked is left on the page", st["unlocked"] >= 1, st)
    ck("the badge case cutscene played on the results", st["caseSeen"], st)
    ck("and Re-run is back beside Main menu", "Re-run" in st["btns"] and "Main menu" in st["btns"], st)

    print("3. the XP rules, asked of computeRunXp() directly")
    xr = pg.evaluate("""()=>{ if(typeof computeRunXp !== 'function') return null;
      const L = r => computeRunXp(r).lines.map(l => [l.key, l.label, l.value]);
      const ok = n => Array(n).fill(true);
      return {
        fast: L({good:12, answered:12, elapsedMs:12*3000, okList:ok(12), hundos:1, wholeUnits:1}),
        slow: L({good:12, answered:12, elapsedMs:12*150000, okList:ok(12), hundos:0, wholeUnits:1}),
        streaks: L({good:37, answered:38, elapsedMs:38*20000, okList:ok(12).concat([false], ok(25)), hundos:0, wholeUnits:1}),
        multi: computeRunXp({good:40, answered:40, elapsedMs:40*20000, okList:ok(40), hundos:4, wholeUnits:4}).lines.slice(-1)[0],
        retake: L({retake:true, good:3, answered:3, elapsedMs:5000, okList:ok(3)}),
        badge: typeof MASTERY_BONUS === 'number' ? MASTERY_BONUS : null
      }; }""")
    if not xr:
        ck("computeRunXp exists", False)
    else:
        g = lambda rows, key: [r for r in rows if r[0] == key]
        ck("speed under 5s a question is 150", g(xr["fast"], "speed") and g(xr["fast"], "speed")[0][2] == 150, xr["fast"])
        ck("speed past two minutes a question is 10", g(xr["slow"], "speed") and g(xr["slow"], "speed")[0][2] == 10, xr["slow"])
        ck("every speed bonus is a multiple of 5", all(r[2] % 5 == 0 for rows in (xr["fast"], xr["slow"]) for r in g(rows, "speed")))
        # ONE streak line since build 309 ("combine like the streak ones"),
        # worth what the per-tier lines were: 10 twice and 25 once.
        stl = g(xr["streaks"], "streak")
        ck("the streaks are ONE line, worth 10 twice and 25 once",
           len([r for r in xr["streaks"] if r[0].startswith("streak")]) == 1 and stl
           and stl[0][2] == pg.evaluate("()=>runStreakTierXp(10)*2 + runStreakTierXp(25)"), xr["streaks"])
        sub = pg.evaluate("""()=>computeRunXp({good:37, answered:38, elapsedMs:38*20000,
          okList:Array(12).fill(true).concat([false], Array(25).fill(true)), hundos:0, wholeUnits:1})
          .lines.find(l=>l.key==='streak').sub""")
        ck("and it lists the tiers it reached, 10 x2 and 25", sub == "10 \u00d72 \u00b7 25 in a row", sub)
        bl = pg.evaluate("()=>computeRunXp({good:12, answered:12, elapsedMs:60000, okList:Array(12).fill(true), hundos:0, wholeUnits:1, badgesPaid:['A','B','C']}).lines.filter(l=>l.badge)")
        # REVERSED IN 320: "no more xp bonus for getting a badge ... remove it
        # from the xp box". Three badges are no line at all.
        ck("a run that finds three badges has no badge line in the XP box (build 320)", len(bl) == 0, bl)
        pb = pg.evaluate("()=>computeRunXp({good:12, answered:12, elapsedMs:60000, okList:Array(12).fill(true), hundos:0, wholeUnits:1, timePRs:[{unit:'A',text:'A 1:00'}], scorePRs:[{unit:'A',text:'A 100%'},{unit:'B',text:'B 90%'}]}).lines.filter(l=>l.key.startsWith('pb'))")
        ck("personal bests are one line worth all three", len(pb) == 1 and pb[0]["value"] == pg.evaluate("()=>PB_TIME_BONUS + 2*PB_SCORE_BONUS"), pb)
        ck("a multi-unit run ends on its multiplier, x1.3 for four units",
           xr["multi"]["key"] == "multi" and "1.3" in xr["multi"]["label"], xr["multi"])
        ck("a retake earns its right answers and nothing else", [r[0] for r in xr["retake"]] == ["correct"] and xr["retake"][0][2] == 30, xr["retake"])
        # The two Game XP lines (difficulty beaten, lives left) went with
        # Game mode in build 283.
        ck("a badge is worth no XP of its own (build 320; it was 1,000)", xr["badge"] is None, xr["badge"])
    # "a lost game still gets a results screen" lived here until Game
    # mode was retired in build 283 (retired/game-mode.md).
    wait_done(pg)

    print("4. reduce motion: everything at once, no banners")
    pg.evaluate("""([u])=>{ theme.reduceMotion=true; applyTheme && applyTheme();
      store.unitPerfects={}; store.unitPerfects[u]=badgeThresholdFor(u)-1; __maxSpots=0; saveStore(); }""", [UNIT])
    pg.evaluate("([u])=>__run(u,0,'drill')", [UNIT]); pg.wait_for_timeout(200)
    # BUILD 320: the same ORDER, still - the Unlocked box waits for the
    # badge's still scene to go ("that box will be put down/show up once
    # all the pop ups and cutscenes are done"); everything else is down.
    rm = pg.evaluate("""()=>({ done: !!document.querySelector('.rs-rewards.rs-done'),
      hidden: [...document.querySelectorAll('#stage .rs-land')].filter(e=>!e.closest('.rs-unlocked') && +getComputedStyle(e).opacity<.5).length,
      spots: document.querySelectorAll('.rs-spot').length })""")
    ck("every card is already down but the Unlocked box (it waits for the still scene)", rm["done"] and rm["hidden"] == 0, rm)
    pg.wait_for_timeout(1500)
    ck("and no banner plays", pg.evaluate("()=>__maxSpots") == 0)
    pg.wait_for_timeout(6000)
    ck("and the Unlocked box is down once the still scene has gone",
       pg.evaluate("()=>{ const u=document.querySelector('#stage .rs-unlocked'); return !!u && +getComputedStyle(u).opacity > .9 && !document.querySelector('.bc-scene'); }"))
    pg.evaluate("()=>{ theme.reduceMotion=false; applyTheme && applyTheme(); }")

    print("5. build 214: the header, the labels, a retake, the room's score")
    pg.evaluate("([u])=>__run(u,2,'drill')", [UNIT]); wait_done(pg)
    hd = pg.evaluate("()=>({ title:(document.querySelector('#stage .rs-units')||{}).textContent,"
                     " items:[...document.querySelectorAll('#stage .rs-unitlist li')].map(l=>l.textContent) })")
    ck("a one-unit test says 1 unit and lists it", hd["title"] == "1 unit" and hd["items"] == [UNIT], hd)
    lab = pg.evaluate("()=>computeRunXp({good:12, answered:12, elapsedMs:60000, okList:Array(12).fill(true), hundos:0, wholeUnits:1})"
                      ".lines.filter(l=>/^streak/.test(l.key)).map(l=>l.label)")
    # build 325 renamed it ("the names of the xp ... hard to understand"):
    # the shape held is that the one streak line says it is about answers
    # in a row, not the exact words
    ck("a streak line says what kind of bonus it is", len(lab) == 1 and "in a row" in lab[0].lower(), lab)
    pg.evaluate("([u])=>__run(u,1,'drill',true)", [UNIT]); wait_done(pg)
    rt = pg.evaluate("()=>({ pct: !!document.querySelector('#stage .rs-pct'),"
      " note: (document.querySelector('#stage .rs-retake-line')||{}).textContent,"
      " xp: [...document.querySelectorAll('#stage .rs-xpline-name')].map(e=>e.textContent) })")
    ck("a retake shows no score", not rt["pct"] and bool(rt["note"]), rt)
    ck("and earns its right answers only", len(rt["xp"]) == 1 and "correct" in rt["xp"][0].lower(), rt)
    pg.evaluate("([u])=>{ store.unitBestPct = store.unitBestPct || {}; store.unitBestPct[u] = 50; saveStore(); }", [UNIT])
    pg.evaluate("([u])=>__run(u,0,'drill')", [UNIT]); wait_done(pg, 60000)
    rm2 = pg.evaluate("()=>({ mine: (lastRunResult.xpLines||[]).map(l=>l.key),"
                      " room: ((lastRunRoomXp||{}).lines||[]).map(l=>l.key) })")
    ck("a new best score is in YOUR XP", "pb" in rm2["mine"], rm2)
    ck("and not in the Virtual Room's score, nor a badge",
       "pb" not in rm2["room"] and "badge" not in rm2["room"], rm2)

    print("6. build 215: the Constitution unit")
    cu = pg.evaluate("""()=>{ const U = 'US and Texas Constitution and Rights';
      const idx = QUESTIONS.map((q,i)=>i).filter(i=>QUESTIONS[i].topic===U);
      const bySrc = n => idx.find(i=>QUESTIONS[i].src===n);
      const q61 = bySrc(61), q11 = bySrc(11), q37 = bySrc(37);
      const links = idx.filter(i=>/https?:/.test((QUESTIONS[i].ref||'') + QUESTIONS[i].q + QUESTIONS[i].choices.join(' '))).length;
      const orders = [];
      for(let k = 0; k < 8; k++){ layout = {}; runMode = 'exam'; cfg.shuffle = true;
        orders.push(optionOrder(q11).join('') + '/' + optionOrder(q37).join('')); }
      /* Drill: the note once answered. */
      cfg.mode='drill'; cfg.units=[U]; cfg.source='all'; cfg.shuffle=true; runMode='drill';
      beginRun([q61], null);
      return { q61, links, orders }; }""")
    ck("no links left in the unit", cu["links"] == 0, cu["links"])
    ck("Q11 and Q37 keep their order, even shuffled in an Exam", set(cu["orders"]) == {"0123/0123"}, cu["orders"])
    # Build 299 reversed build 215's decision for Q61: "just change the
    # answer to the correct answer and remove the advisory". The test now
    # counts excessive bail, and the red note is gone everywhere.
    pg.wait_for_selector(".qpanel .choice", timeout=20000)
    key = pg.evaluate("([q])=>QUESTIONS[q].choices[QUESTIONS[q].answer]", [cu["q61"]])
    ck("Q61 (8th Amendment) counts 'the right to be free from excessive bail'", "excessive bail" in key, key)
    pg.evaluate("()=>{const r=correctSlot(order[pos]); [...document.querySelectorAll('.qpanel .choice')].find(c=>+c.dataset.index===r).click();}")
    pg.wait_for_timeout(400)
    note = pg.evaluate("()=>!!document.querySelector('.bank-note')")
    ck("and there is no study-bank advisory once answered in Drill", note is False, note)
    rv = pg.evaluate("""([q])=>{ const run = { mode:'exam', vroom:false, gameLost:0, order:[q], missed:[q], attempts:{}, firstPick:{},
        picked: { [q]: 0 }, timedOutSet:{} };
      layout = {}; runMode='exam'; cfg.shuffle=false;
      const li = buildReviewQuestion(run, q, 0);
      return { note: !!li.querySelector('.bank-note'), text: li.textContent }; }""", [cu["q61"]])
    ck("nor in an Exam's review, which shows excessive bail as the correct answer",
       rv["note"] is False and "excessive bail" in rv["text"], (rv["note"], rv["text"][:160]))
    pg.evaluate("()=>{ testInProgress=false; try{ showHome(); }catch(e){} }")

    print("7. build 216: found recording every cutscene")
    # Both written against build 215, where both fail.
    # The Game difficulty lights were checked here until build 283.
    # The streak pill riding over "Test results" was checked here until
    # build 284 took the in-test streak pill out (check-behaviour
    # check_b284 drives a real run and asserts none appears).

    print("8. builds 217-218: the results screen, re-asked")
    # Every one of these fails on build 216.
    # Drill is red, app-wide - "red would be a better colour for drill".
    drill = pg.evaluate("""()=>{ const s=document.createElement('span'); s.className='rs-mode rs-mode-drill';
      document.body.appendChild(s); const c=getComputedStyle(s).color; s.remove(); return c; }""")
    nums = [float(x) for x in re.findall(r"[\d.]+", drill)[:3]]
    rgb = [n * 255 if drill.startswith("color(") else n for n in nums]
    # Gold (build 216) is ~255,211,122 even through the chip's mix.
    ck("the Drill chip is red", rgb[0] > 200 and rgb[1] < 175 and rgb[2] < 175, drill)
    # (The streak pill's colour was checked here until build 284.)
    # XP: the long-test bonus stacks every 50, and the daily question pays 200.
    xp = pg.evaluate("""()=>{ const f=(n,g)=>computeRunXp({good:g, answered:n, elapsedMs:n*20000, okList:[]});
      const k=r=>(r.lines.find(l=>l.key==='long')||{}).value||0;
      return { a49:k(f(49,49)), a50:k(f(50,50)), a120:k(f(120,120)), half:k(f(100,50)),
               daily:computeRunXp({daily:true, good:1}).total }; }""")
    ck("a long test pays +100 for every 50 questions, stacking", xp["a49"] == 0 and xp["a50"] == 100 and xp["a120"] == 200, xp)
    ck("scaled by accuracy", xp["half"] == 100, xp)
    ck("the daily question is worth 200 XP", xp["daily"] == 200, xp)
    # BUILD 308: the badge comes first - it is what tips the rank - then
    # the rank, then what it handed over. ("I would also think the badge
    # cutscene would be first to go because that's what is needed to
    # trigger a rank up.")
    order = pg.evaluate("""()=>rsUnlockItems({ colors:['vanguard'], badges:['Identity Crimes'], retroBadges:[],
      characters:['robot'], justBeatSpeed:null, units:[], flare:null }).map(i=>i.kind)""")
    # BUILD 319: the rank and what it hands over play on Profile's road
    # map, not here ("those popups should happen in the road map") - the
    # results keep the badge first and any other unlock after it.
    ck("unlocks run the badge first, then the rest; the rank and its rewards are not on the results (build 319)",
       order[:1] == ["badge"] and "character" in order[1:] and not any(k in ("rank", "theme", "rankflare", "rankrewards") for k in order), order)
    # BUILD 321: "The rank up is still showing in unlocks." Nothing a rank
    # hands over is ever on the results - not only while its rank-up is
    # owed (320 let a rank's character and banner through whenever it was
    # not). Fails on 6a387e2.
    rk = pg.evaluate("""()=>{ const keep = store.rankUpShown; store.rankUpShown = TIER_ORDER_FULL.length + 1;
      const ch = AVATAR_CHARACTERS.find(c => c.unlock && !c.feat && !c.retired), bn = BANNERS.find(b => b.rank && !b.retired);
      const items = rsUnlockItems({ badges: [], retroBadges: [], characters: [ch.id], banners: bn ? [bn.id] : [], fx: [], flare: null });
      store.rankUpShown = keep; return { owed: rankUpOwed(), items: items.map(i => [i.kind, i.name, i.rankReward || null]) }; }""")
    ck("a rank's own character and banner are not on the results even with no rank-up owed (build 321)",
       rk["items"] == [], rk)
    # BUILD 321: the grade's colour is red into green and nothing else -
    # red below the pass mark (a fail ends red), then straight into green,
    # all green at 100 ("It needs to be just the red slowly into the green
    # not other colors"). Asked of rsToneAt at every whole percent.
    tone = pg.evaluate("()=>Array.from({length: 101}, (_, p) => (rsToneAt(p).match(/\\d+/g) || []).slice(0, 3).map(Number))")
    R, G = (227, 112, 124), (79, 190, 140)
    def off_line(c):
        d = [g - r for r, g in zip(R, G)]
        k = max(0, min(1, sum((c[i] - R[i]) * d[i] for i in range(3)) / sum(v * v for v in d)))
        return max(abs(c[i] - (R[i] + d[i] * k)) for i in range(3))
    ck("the grade's colour runs only along the straight line from red to green (build 321)",
       all(off_line(c) <= 2 for c in tone), [(p, c) for p, c in enumerate(tone) if off_line(c) > 2][:3])
    ck("red all the way to the pass mark, green at 100",
       all(tuple(c) == R for c in tone[:70]) and tuple(tone[100]) == G, (tone[40], tone[69], tone[100]))
    # A run that missed one: the badge line, the avatar, the chip.
    pg.evaluate("([u])=>{ store.unitPerfects = store.unitPerfects || {}; store.unitPerfects[u] = 3; __run(u,0,'drill'); }", [UNIT])
    wait_done(pg)
    got = pg.evaluate("""()=>{ const lb=document.getElementById('testscopelabel').getBoundingClientRect();
      const m=document.querySelector('.rs-mode').getBoundingClientRect();
      const line=document.querySelector('.rs-badges .badgeprogress-line');
      const boxes=document.querySelectorAll('#stage .rs-badges').length;
      return { dx:Math.round(m.left-lb.left), gap:Math.round(m.top-lb.bottom),
               line: line?line.textContent:null, boxes,
               avatar: !!document.querySelector('.results-level-avatar svg'),
               rank: !!document.querySelector('.results-level-rank') }; }""")
    ck("the mode chip lines up under Test results", abs(got["dx"]) <= 2 and 0 <= got["gap"] <= 14, got)
    ck("your avatar and rank ride on the level bar", got["avatar"] and got["rank"], got)
    # BUILD 320: the badge progress box is off ("it's kinda redundant and
    # not needed, the profile tab shows all this clearly now") - the line
    # it carried ("+1 hundo · N more to go") is gone with it.
    ck("no badge progress box on the results (build 320)", got["boxes"] == 0 and not got["line"], got)
    # A nova, not confetti.
    cel = pg.evaluate("()=>{ celebrate(); const r={ confetti:document.querySelectorAll('.confetti-piece').length, dust:document.querySelectorAll('.stardust-p').length }; document.querySelectorAll('.confetti-layer').forEach(l=>l.remove()); return r; }")
    ck("the celebration is stardust, not confetti", cel["confetti"] == 0 and cel["dust"] > 10, cel)
    # A character banner names the challenge that earned it.
    need = pg.evaluate("""()=>{ let t=''; playUnlockSpotlight({kind:'character', character:'zeus', feat:true, kicker:'Challenge complete',
      name:'Zeus', sub:'', need:(typeof characterChallenge==='function'?characterChallenge('zeus'):''), color:'#7FD4F5', art:()=>buildAvatarCharSVGSafe('zeus')},1,1,()=>{});
      const n=document.querySelector('.rs-spot-need-text'); t=n?n.textContent:''; document.querySelectorAll('.rs-spot').forEach(x=>x.remove()); return t; }""")
    ck("a character unlock says what it took", bool(need) and "week" in need.lower(), need)
    pg.evaluate("()=>{ testInProgress=false; try{ showHome(); }catch(e){} }")

    # BUILD 309: the line under the level bar names the SAME level as the
    # number above it, before the wrap and after it. It was written from
    # where the run ended while the number still showed where it started:
    # "Level 23 ... 815 to level 25" for the whole fill.
    lv = pg.evaluate("""async ()=>{ let p=0; while(levelProgress(p).level < 23) p+=25;
      const lo=p; while(levelProgress(p).level < 24) p+=25; p+=200;
      /* every badge there is (build 314): this is about the line, not
         the badge gate, which would hold a badgeless account at 21 */
      const w=buildResultsLevelBlock(p-lo+50, p, { badgesBefore: 16, badgesAfter: 16 }); document.getElementById('stage').appendChild(w);
      const read=()=>{ const n=+(w.querySelector('.results-level-num').textContent.match(/\\d+/)||[0])[0];
        /* build 314: the line is "into / span XP" - the span names the level it is for */
        const m=(w.querySelector('.results-level-line').textContent.match(/\\/ ([0-9,]+) XP/)||[])[1];
        const span = m ? +m.replace(/,/g,'') : null;
        return [n, span != null && span === xpForLevel(n + 1) - xpForLevel(n) ? n + 1 : null]; };
      const start=read(); w.runFill(); await new Promise(r=>setTimeout(r,2600)); const end=read(); w.remove();
      return {start, end}; }""")
    ck("the level line names the next level after the one shown, while filling and after",
       lv["start"][1] == lv["start"][0] + 1 and lv["end"][1] == lv["end"][0] + 1 and lv["end"][0] > lv["start"][0], lv)

    print("9. build 315: the results screens in one type system")
    def fresh(w, h):
        c = br.new_context(viewport={"width": w, "height": h})
        c.add_init_script(FAKE)
        c.add_init_script("try{localStorage.setItem('class26e.frame.ok','go-live-1');"
                          "localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.penal256578.seen','1');localStorage.setItem('class26e.daily.seen','x');}catch(e){}")
        p = c.new_page()
        p.on("pageerror", lambda e: errors.append(str(e)))
        if AGAINST:
            p.route("**/index.html", lambda r, q=None: r.fulfill(status=200, content_type="text/html", body=_html))
        p.route("**/version.json*", lambda r, q=None: r.fulfill(status=200, content_type="application/json",
                body='{"build":"%s","frameId":""}' % _bld))
        p.goto("http://127.0.0.1:%d/index.html" % port); p.wait_for_timeout(2500)
        p.evaluate(SETUP); p.wait_for_timeout(300)
        # any units, any misses, Drill or Exam, a retake - the real summarize()
        p.evaluate("""()=>{ window.__run9 = (units, missN, mode, retake) => {
          cfg.mode = mode; cfg.source = 'all'; cfg.units = units.slice(); cfg.size = 0;
          order = QUESTIONS.map((q, i) => i).filter(i => units.indexOf((QUESTIONS[i].topic || '').trim()) >= 0 && inWholeUnit(QUESTIONS[i]));
          if(retake) order = order.slice(0, 3);
          runTrackable = !retake; timedOut = false; runMode = mode; runLabel = retake ? 'Missed questions' : null; isMissedRetake = !!retake;
          practiceTestMinutes = null; inVirtualRoom = false; attempts = {}; picked = {}; timedOutSet = {}; try{ firstPick = {}; }catch(e){}
          order.forEach((qi, k) => { const oo = optionOrder(qi), right = oo.indexOf(QUESTIONS[qi].answer), miss = k % 2 === 1 && k < missN * 2;
            attempts[qi] = miss ? 2 : 1; picked[qi] = miss ? (right + 1) % oo.length : right; try{ if(miss) firstPick[qi] = (right + 1) % oo.length; }catch(e){} });
          runStartTime = Date.now() - order.length * 7000; testInProgress = true; pos = order.length - 1; summarize(); }; }""")
        return c, p

    def audit(p, sel, label, shape=True):
        t = p.evaluate(TYPE_AUDIT, sel)
        ck("%s: no serif and no old-style figures; every number (%d) the grade's sans, tabular" % (label, t["nums"]),
           t["n"] > 0 and not t["issues"], t["issues"][:6])
        if not shape: return
        sh = p.evaluate(SHAPE_AUDIT)
        if not sh:
            ck("%s: the results screen is up" % label, False); return
        ck("%s: one size per role - kicker, label, caption" % label,
           all(len(v) <= 1 for v in sh["roles"].values()), sh["roles"])
        ck("%s: every card's text on one edge, every heading on it" % label,
           spread(sh["contentLefts"]) <= .6 and all(abs(v) <= .6 for v in sh["kickLeft"]), (sh["contentLefts"], sh["kickLeft"]))
        ck("%s: every right-hand number ends on the content edge" % label,
           spread(sh["contentRights"]) <= .6 and all(abs(v) <= .6 for v in sh["shortOfRight"]), (sh["contentRights"], sh["shortOfRight"]))
        ck("%s: the same gap under every card's heading (within 3.5px)" % label,
           spread(sh["headingGaps"]) <= 3.5 and all(g >= 14 for g in sh["headingGaps"]), sh["headingGaps"])
        ck("%s: the cards evenly spaced, and the XP lines resting in their own slots" % label,
           spread(sh["cardGaps"]) <= .6 and not sh["lifted"], (sh["cardGaps"], sh["lifted"][:2]))
        ck("%s: Test results, the mode chip and the title on one edge" % label, spread(sh["head"]) <= 1, sh["head"])
        ck("%s: every pair is 'N / M'" % label, all(re.match(r"^[\d,]+ / [\d,]+$", x) for x in sh["pairs"]), sh["pairs"])

    c9, p9 = fresh(440, 956)
    # the animated path once, for the landing itself
    p9.evaluate("([u])=>{ store.unitPerfects = {}; store.unitPerfects[u] = 3; saveStore(); __run9([u], 2, 'drill'); }", [UNIT])
    wait_done(p9, 60000); p9.wait_for_timeout(600)
    audit(p9, "#stage .rs-screen", "a drill with two missed")
    p9.evaluate("()=>document.querySelector('#stage .rs-continue').click()"); p9.wait_for_timeout(500)
    audit(p9, "#stage .rs-screen", "its review", shape=False)
    p9.evaluate("()=>{ theme.reduceMotion = true; }")
    p9.evaluate("""()=>{ store.unitPerfects = { 'Racial Profiling': badgeThresholdFor('Racial Profiling') - 1, 'Identity Crimes': 2 }; saveStore();
      __run9(['Identity Crimes', 'Racial Profiling', 'Victims of Crime'], 0, 'drill'); }""")
    # build 320: the Unlocked box waits for the badge's still scene
    p9.wait_for_function("()=>{ const u=document.querySelector('#stage .rs-unlocked'); return !u || u.classList.contains('rs-in-now'); }", timeout=15000)
    p9.wait_for_timeout(300)
    audit(p9, "#stage .rs-screen", "a three-unit 100% that earns a badge")
    p9.evaluate("([u])=>__run9([u], 1, 'exam')", [UNIT]); p9.wait_for_timeout(400)
    audit(p9, "#stage .rs-screen", "an exam")
    p9.evaluate("([u])=>__run9([u], 1, 'drill', true)", [UNIT]); p9.wait_for_timeout(400)
    audit(p9, "#stage .rs-screen", "a retake")
    p9.evaluate("""([u])=>{ cfg.mode='drill'; cfg.source='flagged'; cfg.units=[u]; order=QUESTIONS.map((q,i)=>i).filter(i=>QUESTIONS[i].topic===u).slice(0,4);
      runTrackable=false; timedOut=false; runMode='drill'; runLabel=null; isMissedRetake=false; inVirtualRoom=false; attempts={}; picked={}; timedOutSet={};
      order.forEach(qi=>{ attempts[qi]=1; picked[qi]=optionOrder(qi).indexOf(QUESTIONS[qi].answer); }); runStartTime=Date.now()-20000; testInProgress=true; pos=order.length-1; summarize(); }""", [UNIT])
    p9.wait_for_timeout(400)
    audit(p9, "#stage .rs-screen", "a Starred run (no XP)")
    p9.evaluate("()=>{ theme.reduceMotion = false; store.dailyQuestionDate = null; saveStore(); startDailyQuestion(); }")
    p9.wait_for_selector(".qpanel .choice", timeout=25000); p9.wait_for_timeout(300)
    p9.evaluate("()=>{ const r = correctSlot(order[pos]); [...document.querySelectorAll('.qpanel .choice')].find(c => +c.dataset.index === r).click(); const sb=document.getElementById('dailyq-submitbtn'); if(sb && !sb.disabled) sb.click(); }")
    p9.wait_for_timeout(1200)
    audit(p9, "#stage .dailyq-outro", "the daily question's verdict", shape=False)
    c9.close()

    # The same screen on an iPad: the tablet sizes are one per role too, and
    # the grade card's own padding (which outranked the tablet rule) is gone.
    c9, p9 = fresh(834, 1194)
    p9.evaluate("""()=>{ theme.reduceMotion = true; store.unitPerfects = { 'Racial Profiling': badgeThresholdFor('Racial Profiling') - 1 }; saveStore();
      __run9(['Identity Crimes', 'Racial Profiling'], 2, 'drill'); }""")
    p9.wait_for_timeout(500)
    audit(p9, "#stage .rs-screen", "a two-unit drill on an iPad (834px)")
    c9.close()

    # Two buttons share a row only when both fit in equal halves - never a
    # label broken in its pill - on the two small phones.
    for w, h in ((320, 568), (375, 667)):
        c9, p9 = fresh(w, h)
        p9.evaluate("()=>{ theme.reduceMotion = true; }")
        got = []
        for args in (([UNIT], 2, "drill", False), ([UNIT], 1, "drill", True)):
            p9.evaluate("(a)=>__run9(a[0], a[1], a[2], a[3])", list(args)); p9.wait_for_timeout(400)
            got += p9.evaluate(ONE_LINE, "#stage .actions.rs-final > button:not(.rs-wide)")
        ck("%dpx: Re-run, Re-run the full test and Main menu each on one line" % w,
           len(got) >= 4 and all(n == 1 for _, n in got), got)
        c9.close()

    # The Virtual Room: its results, its review tabs, and its leaderboard.
    c9, p9 = fresh(375, 667)
    p9.evaluate(BOTS)
    p9.evaluate("""()=>{ theme.reduceMotion = true; syncCode = 'VR15-0001'; store.publicId = 'pub-vr15';
      const parts = __vrBots.room('R315TYPE', 4, i => __vrBots.finished(i, [0, 11480, 1190, 860][i]));
      return fbDb.collection('vrooms').doc('R315TYPE').set({ status:'starting', game:'race', units:['Identity Crimes'],
        startAt: Date.now() - 2000, chatMessages: [], participants: parts, racers: Object.keys(parts) }); }""")
    p9.wait_for_timeout(300)
    p9.evaluate("()=>{ vroomCode = 'R315TYPE'; vroomMyKey = 'me'; vroomIsHost = true; theme.autoAdvance = false; beginVirtualRoomTest(['Identity Crimes'], null, null, 0); }")
    try:
        p9.wait_for_selector(".qpanel .choice", timeout=25000)
        p9.evaluate("""()=>{ order.forEach((qi, k) => { const oo = optionOrder(qi), r = oo.indexOf(QUESTIONS[qi].answer); picked[qi] = k === 2 ? (r + 1) % oo.length : r; });
          stopQuestionTimer(); summarize(); }""")
        p9.wait_for_function("()=>!!document.querySelector('.vroom-waitcard.is-all-in') && !!document.querySelector('.rs-rewards.rs-done')", timeout=20000)
        p9.wait_for_timeout(400)
        audit(p9, "#stage .rs-screen", "a Virtual Room race's results (375px)")
        p9.evaluate("()=>{ document.getElementById('vroom-prep')?.remove(); startVroomRaceCutscene(); }")
        p9.wait_for_function("()=>!!document.querySelector('#vroom-race-cut.is-done')", timeout=20000)
        p9.wait_for_timeout(300)
        audit(p9, "#vroom-race-cut", "its leaderboard", shape=False)
        ex = p9.evaluate(ONE_LINE, "#vroom-race-cut .vrc-exits button")
        ck("375px: the leaderboard's Return to lobby and Main menu each on one line", len(ex) == 2 and all(n == 1 for _, n in ex), ex)
    except Exception as e:
        ck("the Virtual Room part of section 9 ran", False, repr(e)[:200])
    c9.close()

    ck("no page errors", not errors, errors[:3])
    br.close()
srv.shutdown()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
