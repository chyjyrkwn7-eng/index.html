"""Build 383, Madison:
  1. "Should the badge case be between the challenges and the top box instead? I feel like it's easy to miss at the
     bottom the way it is.."
  2. "the customize button is kinda hidden because the background can be dark. Let's figure out a better way to show
     the customize button in profile.. there's so much behind that button so we need to get this right."
  3. "I've seen people ask about the secret flares popping up in the middle of their test, they haven't clicked it
     because they didn't know they should. How do we make those secret flares ... seem more like 'click me'"
Checks (measured on the page, phone 440x956):
  1. Profile: the badge case is the card straight under the person card, above the next rank, and on screen without
     scrolling; the Profile tour visits it before the next rank.
  2. Customize is its own row in the person card (not beside the name), at least 80% of the card's width, at least
     44px tall, and stands out from the card: its fill's luminance is far from the card's (contrast 4.5:1 or more);
     it still opens Customize.
  3. The secret flare in a test: a second ring rippling out of it, and - until the account has found a flare - a
     "Tap" tag beside it that is part of the button (tapping it finds the flare), clear of the question number, the
     flag and the choices; an account that has found one gets no tag.
Run:  python3 tools/check-b383-profile.py   (--against OLD/index.html must FAIL)"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b382-savecode.py")).read().split("\nwith sync_playwright() as pw:")[0]
g = {"__file__": os.path.join(HERE, "check-b382-savecode.py"), "__name__": "b383p"}
exec(src, g)
from playwright.sync_api import sync_playwright
fails = g["fails"] = []
ck = g["ck"]

LUM = """const lum = c => { const n = (c.match(/[\\d.]+/g) || []).map(Number); if(n.length < 3) return null;
  const f = v => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); };
  return .2126 * f(n[0]) + .7152 * f(n[1]) + .0722 * f(n[2]); };
const solid = el => { for(let e = el; e; e = e.parentElement){ const c = getComputedStyle(e).backgroundColor;
  const a = (c.match(/rgba\\([^)]*,\\s*([\\d.]+)\\)/) || [])[1]; if(c && c !== 'rgba(0, 0, 0, 0)' && (a === undefined || +a > .5)) return c; } return 'rgb(0, 0, 0)'; };"""

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])

    print("\n1-2. Profile: the badge case under the person card; Customize its own light row")
    errs = []
    ctx, pg = g["open_page"](br, g["init_account"]("", g["store"]()), errs=errs)
    pg.evaluate("()=>{ showProfile('profile'); }"); pg.wait_for_timeout(1600)
    r = pg.evaluate("""()=>{ """ + LUM + """
      const tab = document.querySelector('#stage .profile-identity-tab');
      const kids = tab ? [...tab.children].filter(e => e.getBoundingClientRect().height > 0) : [];
      const cls = kids.map(e => e.classList.contains('profile-hero') ? 'hero' : e.classList.contains('pf-case') ? 'case' : e.classList.contains('pf-goal') ? 'goal' : e.className);
      const cs = document.querySelector('#stage .pf-case'); const cr = cs ? cs.getBoundingClientRect() : null;
      const tabs = document.getElementById('bottomtabs'); const barTop = tabs ? tabs.getBoundingClientRect().top : innerHeight;
      const hero = document.querySelector('#stage .profile-hero'); const hr = hero ? hero.getBoundingClientRect() : null;
      const btn = document.querySelector('#stage .profile-hero .profile-edit-btn'); const br = btn ? btn.getBoundingClientRect() : null;
      const name = document.querySelector('#stage .profile-name-display');
      const sameRowAsName = !!(btn && name && name.closest('.namedisplay-row') && name.closest('.namedisplay-row').contains(btn));
      const fill = btn ? getComputedStyle(btn).backgroundColor : null;
      const card = hero ? solid(hero.querySelector('.profile-hero-id') || hero) : null;
      let ratio = null;
      if(fill && card){ const a = lum(fill), b = lum(card); if(a != null && b != null) ratio = (Math.max(a, b) + .05) / (Math.min(a, b) + .05); }
      const steps = (typeof PROFILE_TIPS_289 !== 'undefined' ? PROFILE_TIPS_289 : []).map(s => s.target);
      return { order: cls, caseBottom: cr ? Math.round(cr.bottom) : null, barTop: Math.round(barTop),
        widthPct: br && hr ? Math.round(100 * br.width / hr.width) : 0, h: br ? Math.round(br.height) : 0,
        sameRowAsName, fill, card, ratio: ratio && Math.round(ratio * 10) / 10,
        tourCase: steps.findIndex(t => /pf-case/.test(t)), tourGoal: steps.findIndex(t => /pf-goal/.test(t)) }; }""")
    ck("1. the badge case is the card straight under the person card, above the next rank (%s)" % r["order"],
       r["order"][:3] == ["hero", "case", "goal"], r["order"])
    ck("1. and it is on screen without scrolling (bottom %s above the tab bar %s)" % (r["caseBottom"], r["barTop"]),
       r["caseBottom"] is not None and r["caseBottom"] <= r["barTop"], r)
    ck("1. the Profile tour visits the case before the next rank", 0 <= r["tourCase"] < r["tourGoal"], r)
    ck("2. Customize is its own row, not beside the name", r["sameRowAsName"] is False, r)
    ck("2. Customize spans the person card (%s%% of its width) and is a full tap target (%spx)" % (r["widthPct"], r["h"]),
       r["widthPct"] >= 80 and r["h"] >= 44, r)
    ck("2. Customize stands out from the card behind it: contrast %s:1 (fill %s on %s)" % (r["ratio"], r["fill"], r["card"]),
       (r["ratio"] or 0) >= 4.5, r)
    pg.evaluate("()=>document.querySelector('#stage .profile-hero .profile-edit-btn').click()"); pg.wait_for_timeout(1200)
    ck("2. and it opens Customize", pg.evaluate("()=>!!document.querySelector('#stage .screen-customize')"))
    ck("no page errors", not errs, errs[:2])
    ctx.close()

    print("\n3. the secret flare in a test")
    ARM = """(found)=>{ const topics=[...new Set(QUESTIONS.map(q=>(q.topic||'').trim()))].filter(Boolean); const t=topics[0];
      cfg.mode='drill'; cfg.source='all'; cfg.units=[t];
      const pool=QUESTIONS.map((q,i)=>[q,i]).filter(([q])=>(q.topic||'').trim()===t).map(([,i])=>i);
      store.mysteryColorsFound = found; beginRun(pool, null, null); }"""
    SHOW = """(frac)=>{ mysteryAppearsAtPos = pos; mysteryColorThisRun = 'orange'; mysteryFoundThisSession = false; mysteryLeftFrac = frac; render(); }"""
    MEASURE = """()=>{ const s = document.querySelector('.mystery-spark'); if(!s) return null;
      const tag = s.querySelector('.mystery-tap'); const ring = s.querySelector('.mystery-ring');
      const tr = tag ? tag.getBoundingClientRect() : null;
      const hit = [];
      if(tr) ['.qnum', '.flagbtn', '.choice'].forEach(sel => document.querySelectorAll(sel).forEach(e => { const q = e.getBoundingClientRect();
        if(q.width && q.height && !(tr.right <= q.left || tr.left >= q.right || tr.bottom <= q.top || tr.top >= q.bottom)) hit.push(sel); }));
      const row = s.closest('.qnumrow').getBoundingClientRect();
      return { tag: !!tag, text: tag ? tag.textContent.trim() : null, inButton: !!(tag && s.contains(tag)), hit,
        inRow: tr ? (tr.left >= row.left - 1 && tr.right <= row.right + 1) : null,
        ring: !!ring && getComputedStyle(ring).animationName !== 'none',
        tagW: tr ? Math.round(tr.width) : 0 }; }"""
    errs = []
    ctx, pg = g["open_page"](br, g["init_account"]("", g["store"]()), errs=errs)
    pg.evaluate(ARM, {}); pg.wait_for_timeout(4500)
    worst = []
    for frac in (0, .5, 1):
        pg.evaluate(SHOW, frac); pg.wait_for_timeout(200)
        m = pg.evaluate(MEASURE)
        worst.append((frac, m))
    m0 = worst[1][1] or {}
    ck("3. a second ring ripples out of the flare", m0.get("ring") is True, m0)
    ck("3. never found one: a 'Tap' tag beside it, part of the button", m0.get("tag") is True and m0.get("inButton") is True and (m0.get("text") or "").lower().startswith("tap"), m0)
    ck("3. the tag is clear of the question number, the flag and the choices, and inside the row, wherever the flare lands",
       all(m and m.get("tag") and not m.get("hit") and m.get("inRow") for _, m in worst), worst)
    pg.evaluate("()=>{ const t = document.querySelector('.mystery-spark .mystery-tap'); if(t) t.click(); }"); pg.wait_for_timeout(600)
    ck("3. tapping the tag finds the flare", pg.evaluate("()=>mysteryFoundThisSession === true || !!document.querySelector('.mystery-spark-found')"))
    ctx.close()
    ctx, pg = g["open_page"](br, g["init_account"]("", g["store"]()), errs=errs)
    pg.evaluate(ARM, {"red": True}); pg.wait_for_timeout(4500)
    pg.evaluate(SHOW, .5); pg.wait_for_timeout(200)
    m1 = pg.evaluate(MEASURE) or {}
    ck("3. an account that has found a flare: no tag (it knows), the rings still", m1.get("tag") is False and m1.get("ring") is True, m1)
    ck("no page errors", not errs, errs[:2])
    ctx.close()
    br.close()

print("\nALL PASS" if not fails else "\nFAILED: %d" % len(fails))
sys.exit(1 if fails else 0)
