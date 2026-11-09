"""Build 384: the back button's flash, the search circle's glass, the Start pill's light-up.
Madison: "The back button flashed white or something when you hit it" / "that search icon where applied that's right above the
bottom tab, that needs to look like the bottom tab as well that nice look. Ensure it's all cohesive, and then the pause
button/chat button also match as well." / (a recording) "I feel like there's start button also has a small catch/lag to it when
it shows something has been selected and turns white. Can we fix that and make it super super smooth?"
iPhone 17 Pro Max (440x956), dark, read off the page:
(1) a round back button pressed (setupBubbleButtons' .glass-pressed): nothing is painted in its ::after - no shimmer, no pale
    square thrown off the button by its tap-target box;
(2) the search circle over the tab bar (a Review list), the Pause pill (a drill) and the chat button wear the tab bar's glass:
    fill, lift, rim, blur and shadow, computed, equal;
(3) the Start pill lighting up (a unit ticked on the units screen): in the first frame its words keep the unlit colour and ease
    to the lit ink (a colour transition), never dark on the grey; the fill grows by transform and opacity alone (no clip-path)
    and ends exactly at the lit pill (transform none, opacity 1); its background under the fill is still the unlit grey;
(4) no page errors.
Run:  python3 tools/check-b384-smooth.py   (--against OLD/index.html must FAIL)"""
import os, sys, re
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b382-savecode.py")).read().split("\nwith sync_playwright() as pw:")[0]
g = {"__file__": os.path.join(HERE, "check-b382-savecode.py"), "__name__": "b384sm"}
exec(src, g)
from playwright.sync_api import sync_playwright
fails = g["fails"] = []
ck = g["ck"]
P = ["backgroundColor", "backgroundImage", "borderTopColor", "borderTopWidth", "backdropFilter", "boxShadow"]
GLASS = """(sel)=>{ const P=%s; const e=document.querySelector(sel), t=document.querySelector('.bottomtabs'); if(!e) return null;
  const a=getComputedStyle(e), b=getComputedStyle(t); return { same: P.every(p=>a[p]===b[p]), diff: P.filter(p=>a[p]!==b[p]).map(p=>[p, a[p].slice(0,60), b[p].slice(0,60)]) }; }""" % str(P)
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    errs = []
    ctx, pg = g["open_page"](br, g["init_account"]("", g["store"]()), errs=errs)
    # (1) the back button pressed
    pg.evaluate("()=>{ showModeSelect(); }"); pg.wait_for_timeout(1200)
    b1 = pg.evaluate("""()=>{ const b=document.querySelector('#stage .ios-nav-back'); b.classList.add('glass-pressed'); b.style.setProperty('--shimmer-x','50%'); b.style.setProperty('--shimmer-y','50%');
      const a=getComputedStyle(b,'::after'); const out={ img: a.backgroundImage, color: a.backgroundColor }; b.classList.remove('glass-pressed'); return out; }""")
    ck("(1) a pressed back button paints nothing in its ::after (%s)" % b1, b1["img"] == "none" and b1["color"] in ("rgba(0, 0, 0, 0)", "transparent"), b1)
    # (2) the search circle, Pause, the chat button
    pg.evaluate("()=>{ showAnswerReview([topicsIn(QUESTIONS)[3]], 'all'); }"); pg.wait_for_timeout(1600)
    gs = pg.evaluate(GLASS, ".tabsearch:not([hidden])"); gc = pg.evaluate(GLASS, "#chatdock-btn")
    ctx.close()
    ctx, pg = g["open_page"](br, g["init_account"]("", g["store"]()), errs=errs)
    pg.evaluate("""()=>{ const t=topicsIn(QUESTIONS)[3]; cfg.mode='drill'; cfg.units=[t]; cfg.source='all'; beginRun(QUESTIONS.map((q,i)=>[q,i]).filter(([q])=>(q.topic||'').trim()===t).map(([,i])=>i).slice(0,4), null, null); }""")
    for _ in range(30):
        if pg.evaluate("()=>!!document.querySelector('#pausebtn:not([hidden])')"): break
        pg.wait_for_timeout(250)
    pg.wait_for_timeout(600)
    gp = pg.evaluate(GLASS, "#pausebtn:not([hidden])")
    ctx.close()
    ctx, pg = g["open_page"](br, g["init_account"]("", g["store"]()), errs=errs)
    ck("(2) the search circle, Pause and the chat button wear the tab bar's glass (%s / %s / %s)" % (gs and gs["same"], gp and gp["same"], gc and gc["same"]),
       gs and gs["same"] and gp and gp["same"] and gc and gc["same"], [gs, gp, gc])
    # (3) the Start pill lighting up
    pg.evaluate("()=>{ cfg.mode='drill'; cfg.units=[]; showSetup(); }"); pg.wait_for_timeout(1800)
    s3 = pg.evaluate("""async ()=>{ const t=document.getElementById('bottomtab-start'); if(!t) return null;
      const inert = getComputedStyle(t).color;
      startReadyQuietUntil = 0;
      const card = document.querySelector('#stage .picks > label.pick'); card.querySelector('input').click();
      const first = { color: getComputedStyle(t).color, just: t.classList.contains('just-ready'), tr: getComputedStyle(t).transitionProperty, bg: getComputedStyle(t).backgroundColor };
      const be = getComputedStyle(t, '::before');
      const anims = t.getAnimations({ subtree: true }).filter(a => a.effect && a.effect.pseudoElement === '::before');
      const kf = anims.length ? anims[0].effect.getKeyframes() : [];
      const props = [...new Set(kf.flatMap(k => Object.keys(k).filter(x => !['offset','easing','composite','computedOffset'].includes(x))))];
      const last = kf.length ? kf[kf.length - 1] : null;
      await new Promise(r=>setTimeout(r, 900));
      return { inert, first, props, clip: be.clipPath, last, lit: getComputedStyle(t).color, unlitBg: 'rgba(128, 128, 128, 0.16)' }; }""")
    ok3 = s3 and s3["first"]["just"] and s3["first"]["color"] == s3["inert"] and "color" in s3["first"]["tr"] and s3["props"] and set(s3["props"]) <= {"transform", "opacity"} \
          and s3["last"] and s3["last"].get("transform") in ("none", None) and str(s3["last"].get("opacity", "1")) == "1" and s3["first"]["bg"] == s3["unlitBg"] and s3["lit"] != s3["inert"]
    ck("(3) the Start pill lights up smoothly: words %s -> eased (%s), the fill on %s ending at %s" % (s3 and s3["first"]["color"], s3 and s3["first"]["tr"], s3 and s3["props"], s3 and s3["last"]), ok3, s3)
    ck("(4) no page errors", not errs, errs[:3])
    br.close()
print("\nALL PASS" if not fails else "\nFAILED: %d" % len(fails))
sys.exit(1 if fails else 0)
