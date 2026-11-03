"""Build 383: one look beyond Home, the unit cards' green dot, the daily question asking to be tapped.
Madison: "If that means we need to change the background the app beyond the main menu ... like the same color theme but kinda
how the background used to be where it just some colors but it would be kinda washed out so it's not distracting? Almost like
the result screen ... The main menu background is perfect, it's the rest though ... We need a cohesive look." / "I'm kinda tired
of the checkmark. What if we did like a green glowing dot/circle signifying it's been selected?" / "The daily question button,
when it's ready right now it doesn't look very cool or like 'click me' feel."
Phone 440x956, dark theme:
(1) Home: the stars at full, no wash. Mode selection, the units, Profile, Settings, the Calendar and a results screen: no
    stars, the wash up (#nova-wash), made of the theme's own colours (it changes with the theme);
(2) the status-bar strip is untouched: the wash is masked clear over the top inset (as the stars are);
(3) one card everywhere beyond Home: mode cards, unit cards, Settings' cards, the Calendar's cards and Profile's three cards
    all on the same thin glass (the same see-through base, no rim);
(4) a picked unit card: a green dot in its corner (grown from its centre: scale 1, opacity 1), no tick; an unpicked card: none;
(5) the daily question, ready: a light running round its rim and a glow inside, both animating; answered: neither.
Run:  python3 tools/check-b383-look.py   (--against OLD/index.html must FAIL)"""
import os, sys, re
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b382-savecode.py")).read().split("\nwith sync_playwright() as pw:")[0]
g = {"__file__": os.path.join(HERE, "check-b382-savecode.py"), "__name__": "b383l"}
exec(src, g)
from playwright.sync_api import sync_playwright
fails = g["fails"] = []
ck = g["ck"]
SKY = """()=>{ const w=document.getElementById('nova-wash'); const st=getComputedStyle(document.body,'::after');
  return { stars: +st.opacity, wash: w ? +getComputedStyle(w).opacity : null, washBg: w ? getComputedStyle(w).backgroundImage : '',
           washMask: w ? (getComputedStyle(w).maskImage || getComputedStyle(w).webkitMaskImage || '') : '' }; }"""
CARD = """(sel)=>{ const e=document.querySelector(sel); if(!e) return null; const c=getComputedStyle(e);
  const base = (c.backgroundImage.match(/rgba?\\([^)]*\\)\\s*$/) || [c.backgroundColor])[0];
  return { sel, color: c.backgroundColor, base, border: c.borderTopColor, bw: c.borderTopWidth }; }"""
def settle(pg, js, ms=1300):
    pg.evaluate("()=>{ document.querySelectorAll('.intro-popup,.daily-alert,#intro-pop').forEach(e=>e.remove()); %s }" % js); pg.wait_for_timeout(ms)
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    errs = []
    ctx, pg = g["open_page"](br, g["init_account"]("", g["store"]()), errs=errs)
    pg.evaluate("()=>{ try{ theme.accent='elite'; applyTheme(); }catch(e){} }"); pg.wait_for_timeout(400)
    settle(pg, "store.dailyQuestionDate=null; showHome();", 2200)
    h = pg.evaluate(SKY)
    ck("(1) Home: the stars at full, no wash (%s)" % h, h["stars"] >= .95 and (h["wash"] or 0) <= .01, h)
    # (5) the daily question, ready
    d = pg.evaluate("""()=>{ const b=document.querySelector('.daily-question-fab'); const r=b && b.querySelector('.dq-ring');
      if(!b || !r) return null; const be=getComputedStyle(r,'::before'), af=getComputedStyle(r,'::after');
      return { ready: b.classList.contains('is-ready'), ring: +getComputedStyle(r).opacity, comet: be.animationName, glow: af.animationName,
               cometOn: be.content !== 'none' && parseFloat(be.width) > 0 }; }""")
    ck("(5) the daily question, ready: a light running round its rim and a glow inside, both moving (%s)" % d,
       d and d["ready"] and d["ring"] > .9 and d["cometOn"] and d["comet"] not in ("none", "") and d["glow"] not in ("none", ""), d)
    pg.evaluate("()=>{ store.dailyQuestionDate = dailyPeriodKey(); showHome(); }"); pg.wait_for_timeout(1500)
    d2 = pg.evaluate("""()=>{ const b=document.querySelector('.daily-question-fab'); const r=b && b.querySelector('.dq-ring'); if(!b||!r) return null;
      const be=getComputedStyle(r,'::before'); return { done: b.classList.contains('is-done'), comet: be.content === 'none' ? 'none' : be.animationName }; }""")
    ck("(5) answered: no running light (%s)" % d2, d2 and d2["done"] and d2["comet"] in ("none", ""), d2)
    beyond = [("mode selection", "showModeSelect();", ".modecard"), ("the units", "cfg.mode='drill'; cfg.units=[]; showSetup();", ".picks > label.pick"),
              ("Profile", "showProfile('profile');", ".profile-identity-tab > .pf-goal"), ("Settings", "showAppearance();", ".settings-card"),
              ("the Calendar", "showCalendarTab();", ".screen-calendar-tab .cal-card")]
    bases = {}
    for name, js, card in beyond:
        settle(pg, js)
        s = pg.evaluate(SKY)
        ck("(1) %s: no stars, the wash up (%s / %s)" % (name, s["stars"], s["wash"]), s["stars"] <= .01 and (s["wash"] or 0) >= .95 and s["washBg"].count("radial-gradient") >= 3, s)
        if name == "mode selection":
            ck("(2) the wash is masked clear over the status bar's strip, as the stars are", "linear-gradient" in s["washMask"] and "transparent" in s["washMask"].replace("rgba(0, 0, 0, 0)", "transparent"), s["washMask"][:120])
            el = pg.evaluate(SKY)["washBg"]
        c = pg.evaluate(CARD, "#stage " + card)
        bases[name] = c
    # Profile's other two cards and the person card
    settle(pg, "showProfile('profile');")
    for sel in (".profile-identity-tab > .profile-hero", ".profile-identity-tab > .pf-case .pf-ccase"):
        bases[sel] = pg.evaluate(CARD, "#stage " + sel)
    norm = lambda x: re.sub(r"\s+", "", (x or "").lower())
    want = norm("rgba(12, 13, 19, 0.4)")
    off = {k: v for k, v in bases.items() if not v or (norm(v["base"]) != want and norm(v["color"]) != want)}
    ck("(3) one thin glass for every card beyond Home - mode, unit, Settings, Calendar and Profile's three (%d of %d on it)" % (len(bases) - len(off), len(bases)), not off, off)
    rimmed = {k: v["border"] for k, v in bases.items() if v and v["bw"] not in ("0px",) and not re.search(r"rgba\([^)]*,\s*0\)$", v["border"] or "") and "transparent" not in (v["border"] or "")}
    ck("(3) and none with a rim of its own", not rimmed, rimmed)
    # the wash takes the theme's colours
    settle(pg, "showModeSelect();")
    w1 = pg.evaluate(SKY)["washBg"]
    pg.evaluate("()=>{ try{ theme.accent='adept'; applyTheme(); }catch(e){} }"); pg.wait_for_timeout(600)
    w2 = pg.evaluate(SKY)["washBg"]
    ck("(1) the wash is the theme's own colours (it changes with the theme)", w1 and w2 and w1 != w2, [w1[:80], w2[:80]])
    # results
    pg.evaluate("""()=>{ const t=topicsIn(QUESTIONS)[6]; cfg.mode='drill'; cfg.units=[t]; cfg.source='all';
      beginRun(QUESTIONS.map((q,i)=>[q,i]).filter(([q])=>(q.topic||'').trim()===t).map(([,i])=>i).slice(0,3), null, null); }""")
    pg.wait_for_timeout(4500)
    pg.evaluate("()=>{ try{ order.forEach(qi=>{ attempts[qi]=1; }); pos=order.length; summarize(); }catch(e){} }"); pg.wait_for_timeout(3500)
    r = pg.evaluate(SKY)
    ck("(1) a results screen: no stars, the wash up (%s / %s)" % (r["stars"], r["wash"]), r["stars"] <= .01 and (r["wash"] or 0) >= .95, r)
    # (4) the green dot
    settle(pg, "showHome(); cfg.mode='drill'; cfg.units=[]; showSetup();", 1500)
    pg.evaluate("()=>{ const c=document.querySelectorAll('.picks > label.pick')[1]; c.querySelector('input').click(); }"); pg.wait_for_timeout(900)
    dot = pg.evaluate("""()=>{ const cs=[...document.querySelectorAll('.picks > label.pick')]; const on=cs[1], off=cs[0];
      const b=on.querySelector(':scope > .box'), s=getComputedStyle(b), o=getComputedStyle(off.querySelector(':scope > .box'));
      const t=b.querySelector('.pick-tick'); const m=new DOMMatrixReadOnly(s.transform);
      const green = (s.backgroundImage.match(/rgb\\((\\d+), (\\d+), (\\d+)\\)/g) || []).some(c => { const n=c.match(/\\d+/g).map(Number); return n[1] > n[0] + 60 && n[1] > n[2] + 40; });
      return { picked: on.classList.contains('pick-checked'), op: +s.opacity, scale: Math.round(Math.hypot(m.a, m.b) * 100) / 100, green,
               glow: (s.boxShadow.match(/0px 0px (\\d+(?:\\.\\d+)?)px/g) || []).some(x => parseFloat(x.split(' ')[2]) >= 6), round: s.borderTopLeftRadius,
               w: Math.round(b.getBoundingClientRect().width), tickShown: !!t && getComputedStyle(t).display !== 'none',
               offOp: +o.opacity }; }""")
    ck("(4) a picked unit card: a green glowing dot, grown to full from its centre, no tick (%s)" % dot,
       dot["picked"] and dot["op"] > .95 and abs(dot["scale"] - 1) < .02 and dot["green"] and dot["glow"] and not dot["tickShown"] and dot["w"] <= 16, dot)
    ck("(4) an unpicked card: nothing in the corner", dot["offOp"] < .05, dot)
    ck("no page errors", not errs, errs[:2])
    ctx.close()
    br.close()
print("\nALL PASS" if not fails else "\nFAILED: %d" % len(fails))
sys.exit(1 if fails else 0)
