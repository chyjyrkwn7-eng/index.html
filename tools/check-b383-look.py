"""Build 383: the clean look beyond Home - a plain background and one solid card; the unit cards' green dot; the daily question
asking to be tapped.
Madison (round 1): "We need a cohesive look ... The main menu background is perfect, it's the rest though." / "What if we did like
a green glowing dot/circle signifying it's been selected?" / "The daily question button, when it's ready ... doesn't look very
cool or like 'click me' feel." Then (round 2, with Orbit's and Delta's screens): "I feel like the app may have too much Liquid
Glass ... the Netflix YouTube spots, they aren't Liquid Glass just a nice look. Same for both settings backgrounds, they are
clean ... profile and stuff within profile, the stats, the settings, the customize, the calendar, the unit selection screen,
review mode. HOWEVER, I love the way the flashcards look ... The result screen, same kinda thing ... the badge screen, that top
box, the rank up screen top box and the boxes that contain the rank information ... The sign up screen and everything and start
would have to be updated to reflect this all."
Phone 440x956, dark theme:
(1) Home keeps its sky (the stars at full); beyond Home - mode selection, the units, Profile, Stats, Settings, Customize, the
    Calendar, Review's list, the Rank and Badges screens, a results screen and a sign-up step - no stars and no wash layer;
(2) one card: every card on those screens is solid (an opaque fill), with no rim, no shadow, no blur and no gradient of its own -
    the same colour everywhere;
(3) the switches are a flat track with a flat lighter pill; the search field is the card's colour; the round back button and
    the chat button are solid, not glass;
(4) no serif display face on Profile, Stats, the Rank tab or Badges (the names and titles);
(5) a picked unit card: a step lighter, the green dot (scale 1, no tick), no green edge; unpicked: nothing in the corner;
(6) the daily question, ready: a light running round its rim and a glow inside; answered: neither;
(7) the flash cards keep their own look (their face's gradient and rim).
Run:  python3 tools/check-b383-look.py   (--against OLD/index.html must FAIL)"""
import os, sys, re
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b382-savecode.py")).read().split("\nwith sync_playwright() as pw:")[0]
g = {"__file__": os.path.join(HERE, "check-b382-savecode.py"), "__name__": "b383l"}
exec(src, g)
from playwright.sync_api import sync_playwright
fails = g["fails"] = []
ck = g["ck"]
SKY = """()=>({ stars: +getComputedStyle(document.body,'::after').opacity, wash: !!document.getElementById('nova-wash') })"""
CARDS = """(sels)=>{ const out=[]; for(const sel of sels){ for(const e of [...document.querySelectorAll('#stage ' + sel)].slice(0, 3)){ const c=getComputedStyle(e); if(!e.getClientRects().length) continue;
    const a = (c.backgroundColor.match(/[\\d.]+/g) || []).map(Number); const alpha = /^rgba|\\/ /.test(c.backgroundColor) ? a[3] : 1;
    /* a gradient that paints anything: any of its colours not fully transparent */
    const grads = (c.backgroundImage.match(/gradient\\([^)]*(\\([^)]*\\)[^)]*)*\\)/g) || []).filter(gr => (gr.match(/(rgba?|color)\\([^)]*\\)/g) || []).some(col => { const n = col.match(/[\\d.]+/g) || []; return /rgba|\\//.test(col) ? +n[n.length - 1] > 0 : true; }));
    const bw = parseFloat(c.borderTopWidth) || 0; const rim = bw > 0 && !/rgba\\([^)]*, 0\\)$/.test(c.borderTopColor) && !/ \\/ 0\\)$/.test(c.borderTopColor);
    out.push({ sel, color: c.backgroundColor, alpha, grads: grads.length, rim, rimC: c.borderTopColor, shadow: c.boxShadow !== 'none', blur: (c.backdropFilter || c.webkitBackdropFilter || 'none') !== 'none' }); } }
  return out; }"""
# titles only (17px and up): the answer choices' reading face and the Settings wordmark are not this round's
SERIF = """()=>[...document.querySelectorAll('#stage *')].filter(e => [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()) && e.getClientRects().length)
  .map(e => [e.className, getComputedStyle(e).fontFamily, parseFloat(getComputedStyle(e).fontSize)]).filter(([k, f, z]) => z >= 17 && /^\\s*(georgia|"?iowan|times)/i.test(f)).map(([k]) => String(k).slice(0, 30))"""
def settle(pg, js, ms=1400):
    pg.evaluate("()=>{ document.querySelectorAll('.intro-popup,.daily-alert,#intro-pop,.nova-talk').forEach(e=>e.remove()); %s }" % js); pg.wait_for_timeout(ms)
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    errs = []
    ctx, pg = g["open_page"](br, g["init_account"]("", g["store"]()), errs=errs)
    pg.evaluate("()=>{ try{ theme.accent='elite'; applyTheme(); }catch(e){} }"); pg.wait_for_timeout(400)
    settle(pg, "store.dailyQuestionDate=null; showHome();", 2200)
    h = pg.evaluate(SKY)
    ck("(1) Home keeps its sky: the stars at full (%s)" % h, h["stars"] >= .95, h)
    d = pg.evaluate("""()=>{ const b=document.querySelector('.daily-question-fab'); const r=b && b.querySelector('.dq-ring');
      if(!b || !r) return null; const be=getComputedStyle(r,'::before'), af=getComputedStyle(r,'::after');
      return { ready: b.classList.contains('is-ready'), ring: +getComputedStyle(r).opacity, comet: be.animationName, glow: af.animationName,
               cometOn: be.content !== 'none' && parseFloat(be.width) > 0 }; }""")
    ck("(6) the daily question, ready: a light running round its rim and a glow inside (%s)" % d,
       d and d["ready"] and d["ring"] > .9 and d["cometOn"] and d["comet"] not in ("none", "") and d["glow"] not in ("none", ""), d)
    pg.evaluate("()=>{ store.dailyQuestionDate = dailyPeriodKey(); showHome(); }"); pg.wait_for_timeout(1500)
    d2 = pg.evaluate("""()=>{ const b=document.querySelector('.daily-question-fab'); const r=b && b.querySelector('.dq-ring'); if(!b||!r) return null;
      const be=getComputedStyle(r,'::before'); return { done: b.classList.contains('is-done'), comet: be.content === 'none' ? 'none' : be.animationName }; }""")
    ck("(6) answered: no running light (%s)" % d2, d2 and d2["done"] and d2["comet"] in ("none", ""), d2)
    screens = [("mode selection", "showModeSelect();", [".modecard"]),
               ("the units", "cfg.mode='drill'; cfg.units=[]; showSetup();", [".picks > label.pick"]),
               ("Profile", "showProfile('profile');", [".profile-identity-tab > .profile-hero", ".profile-identity-tab > .pf-goal", ".pf-case .pf-ccase"]),
               ("Stats", "showProfile('stats');", [".profile-stats-tab > .points-progress-sect"]),
               ("Settings", "showAppearance();", [".settings-card"]),
               ("Customize", "showCustomize();", [".cz-row"]),
               ("the Calendar", "showCalendarTab();", [".screen-calendar-tab .cal-card", ".cal-monthview"]),
               ("Review's list", "showAnswerReview([topicsIn(QUESTIONS)[6]], 'all');", [".ar-head"]),
               ("the Rank tab", "showRanksScreen('ranks');", [".rankhero", ".rankmap-card"]),
               ("Badges", "showRanksScreen('badges');", [".badges-head"])]
    allcards, colors, serifs = [], set(), {}
    for name, js, sels in screens:
        settle(pg, js)
        s = pg.evaluate(SKY)
        ck("(1) %s: no stars, no wash (%s)" % (name, s), s["stars"] <= .01 and not s["wash"], s)
        cs = pg.evaluate(CARDS, sels)
        if not cs: ck("(2) %s: its cards are on screen" % name, False, sels)
        for c in cs: c["screen"] = name; allcards.append(c); colors.add(re.sub(r"\s+", "", c["color"]))
        sf = pg.evaluate(SERIF) if name in ("Profile", "Stats", "the Rank tab", "Badges") else []
        if sf: serifs[name] = sf
        if name == "Profile":
            seg = pg.evaluate("""()=>{ const t=document.querySelector('#stage .navsegment.profiletabs'), sl=t && (t.querySelector('.seg-slider') || t.querySelector('.iconbtn.active'));
              const ct=getComputedStyle(t), cs=getComputedStyle(sl); return { track: ct.backgroundColor, trackImg: ct.backgroundImage, trackRim: ct.borderTopColor, trackBlur: ct.backdropFilter,
                pill: cs.backgroundColor, pillImg: cs.backgroundImage, pillShadow: cs.boxShadow }; }""")
            ck("(3) the switch: a flat track and a flat lighter pill (%s)" % seg,
               seg["trackImg"] == "none" and seg["pillImg"] == "none" and seg["pillShadow"] == "none" and seg["trackBlur"] in ("none", "") and seg["pill"] != seg["track"], seg)
            btn = pg.evaluate("""()=>{ const c=getComputedStyle(document.getElementById('chatdock-btn')); return { img: c.backgroundImage, blur: c.backdropFilter || c.webkitBackdropFilter, bg: c.backgroundColor }; }""")
            ck("(3) the chat button beyond Home is solid, not glass (%s)" % btn, btn["img"] == "none" and btn["blur"] in ("none", "") and "/ 0." not in btn["bg"] and not re.search(r"rgba\([^)]*,\s*0?\.\d+\)", btn["bg"]), btn)
        if name == "the units":
            f = pg.evaluate("()=>{ const i=document.querySelector('#stage .searchwrap input'); const c=getComputedStyle(i); return { bg: c.backgroundColor, img: c.backgroundImage, rim: c.borderTopColor }; }")
            ck("(3) the units' search field is the card's colour, no rim (%s)" % f, f["img"] == "none" and re.sub(r"\s+", "", f["bg"]) in colors, f)
        if name == "mode selection":
            b = pg.evaluate("()=>{ const c=getComputedStyle(document.querySelector('#stage .ios-nav-back')); return { img: c.backgroundImage, shadow: c.boxShadow, blur: c.backdropFilter }; }")
            ck("(3) the round back button is solid (%s)" % b, b["img"] == "none" and b["shadow"] == "none" and b["blur"] in ("none", ""), b)
    bad = [c for c in allcards if c["alpha"] < .99 or c["grads"] or c["rim"] or c["shadow"] or c["blur"]]
    ck("(2) every card beyond Home is solid - opaque, no gradient, rim, shadow or blur (%d of %d)" % (len(allcards) - len(bad), len(allcards)), allcards and not bad, bad[:4])
    ck("(2) and one colour (%s)" % sorted(colors), len(colors) == 1, sorted(colors))
    ck("(4) no serif display face on Profile, Stats, Ranks or Badges", not serifs, serifs)
    # results
    pg.evaluate("""()=>{ const t=topicsIn(QUESTIONS)[6]; cfg.mode='drill'; cfg.units=[t]; cfg.source='all';
      beginRun(QUESTIONS.map((q,i)=>[q,i]).filter(([q])=>(q.topic||'').trim()===t).map(([,i])=>i).slice(0,3), null, null); }""")
    pg.wait_for_timeout(4500)
    pg.evaluate("()=>{ try{ order.forEach(qi=>{ attempts[qi]=1; }); pos=order.length; summarize(); }catch(e){} }"); pg.wait_for_timeout(4500)
    r = pg.evaluate(SKY)
    ck("(1) a results screen: no stars, no wash (%s)" % r, r["stars"] <= .01 and not r["wash"], r)
    rc = pg.evaluate(CARDS, [".rs-screen .rs-card:not(.hfx-tinted)"])
    tone = pg.evaluate("()=>[...document.querySelectorAll('#stage .rs-grade-tone')].map(t=>getComputedStyle(t).display)")
    rbad = [c for c in rc if c["alpha"] < .99 or c["grads"] or c["rim"] or c["shadow"]]
    ck("(2) the results' cards are the solid card, the grade's coloured frame gone (%d cards, tone %s)" % (len(rc), tone), rc and not rbad and all(t == "none" for t in tone), rbad[:3] or tone)
    # (5) the green dot
    settle(pg, "showHome(); cfg.mode='drill'; cfg.units=[]; showSetup();", 1500)
    pg.evaluate("()=>{ const c=document.querySelectorAll('.picks > label.pick')[1]; c.querySelector('input').click(); }"); pg.wait_for_timeout(900)
    dot = pg.evaluate("""()=>{ const cs=[...document.querySelectorAll('.picks > label.pick')]; const on=cs[1], off=cs[0];
      const b=on.querySelector(':scope > .box'), s=getComputedStyle(b), o=getComputedStyle(off.querySelector(':scope > .box'));
      const t=b.querySelector('.pick-tick'); const m=new DOMMatrixReadOnly(s.transform);
      const green = (s.backgroundImage.match(/rgb\\((\\d+), (\\d+), (\\d+)\\)/g) || []).some(c => { const n=c.match(/\\d+/g).map(Number); return n[1] > n[0] + 60 && n[1] > n[2] + 40; });
      const co=getComputedStyle(on), cf=getComputedStyle(off);
      return { picked: on.classList.contains('pick-checked'), op: +s.opacity, scale: Math.round(Math.hypot(m.a, m.b) * 100) / 100, green,
               tickShown: !!t && getComputedStyle(t).display !== 'none', offOp: +o.opacity, w: Math.round(b.getBoundingClientRect().width),
               onBg: co.backgroundColor, offBg: cf.backgroundColor, onRim: co.borderTopColor, onShadow: co.boxShadow }; }""")
    ck("(5) a picked unit: a step lighter, the green dot at full, no tick, no green edge (%s)" % dot,
       dot["picked"] and dot["op"] > .95 and abs(dot["scale"] - 1) < .02 and dot["green"] and not dot["tickShown"] and dot["w"] <= 16
       and dot["onBg"] != dot["offBg"] and dot["onShadow"] == "none" and (re.search(r",\s*0\)$", dot["onRim"]) or "/ 0)" in dot["onRim"] or dot["onRim"] == "rgba(0, 0, 0, 0)"), dot)
    ck("(5) an unpicked card: nothing in the corner", dot["offOp"] < .05, dot)
    # (7) the flash cards keep theirs
    settle(pg, "showFlashcards([topicsIn(QUESTIONS)[6]], 'all');", 1500)
    fcf = pg.evaluate("()=>{ const f=document.querySelector('#stage .fc-face'); const c=getComputedStyle(f); return { img: c.backgroundImage.slice(0, 40), rim: c.borderTopColor, bw: c.borderTopWidth }; }")
    ck("(7) the flash cards keep their own face - a gradient and a rim (%s)" % fcf, "gradient" in fcf["img"] and float(fcf["bw"].replace("px","") or 0) > 0, fcf)
    ck("no page errors", not errs, errs[:2])
    ctx.close()
    # a sign-up step: the clean look too
    errs2 = []
    ctx, pg = g["open_page"](br, g["SEEN"], errs=errs2)
    pg.evaluate("()=>{ showSignUpCheck(); }"); pg.wait_for_timeout(1300)
    su = pg.evaluate(SKY)
    ck("(1) a sign-up step (New to Nova?): no stars, no wash (%s)" % su, su["stars"] <= .01 and not su["wash"], su)
    pg.evaluate("()=>{ showWelcome(); }"); pg.wait_for_timeout(1300)
    wl = pg.evaluate(SKY)
    ck("(1) Welcome (its planet) keeps Home's sky (%s)" % wl, wl["stars"] >= .95, wl)
    ctx.close()
    br.close()
print("\nALL PASS" if not fails else "\nFAILED: %d" % len(fails))
sys.exit(1 if fails else 0)
