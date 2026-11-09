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
  5. (383: "the see rank ladder button and 4 of 24 badges button ... improve those buttons so they seem more clickable, ensure the
     wording of those two buttons are centered") - (384: "the customize button, the badge button, and rank button. I actually do
     not like that at all. It's terrible. Please change that") each is a Settings row now, Customize's kind: wide, 56px+, its tile
     on the left and its chevron on the right, its name at 18px+ straight after the tile, the words in the row's middle top to
     bottom, a light rim.
  (384) 2. "stands out": the rows are the tab bar's dark glass now, so Customize stands out by its light rim and its tile (3:1+
     on the card) rather than a light fill. 3. the Tap tag is for a colour already missed once (384: "only appear when they miss
     it the first time"), so the account that has never found one has missed orange.
  6. (383: "Why does the bottom right corner side of the badges within the unit selection cards look kinda off? There's like a
     gap thing on them?") a found badge on a unit card is the token alone - no slot (the case's dark wall and lit lip) round it;
     one not yet found is still drawn as its empty slot.
  4. (383, from a Calendar screenshot: "I notice the test one is glowing. Ensure they are all the same cohesive look")
     the calendar's key and grid dots carry no glow, phone and iPad.
Run:  python3 tools/check-b383-profile.py   (--against OLD/index.html must FAIL)"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b382-savecode.py")).read().split("\nwith sync_playwright() as pw:")[0]
g = {"__file__": os.path.join(HERE, "check-b382-savecode.py"), "__name__": "b383p"}
exec(src, g)
from playwright.sync_api import sync_playwright
fails = g["fails"] = []
ck = g["ck"]

LUM = """const lum = c => { let n = (c.match(/[\\d.]+/g) || []).map(Number); if(n.length < 3) return null;
  if(/^color\\(/.test(c)) n = n.map((v, i) => i < 3 ? v * 255 : v);   /* (384) color(srgb r g b) is 0-1 */
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
      const tileEl = btn ? btn.querySelector('.settings-row-icon') : null;
      /* (384 r8) the tile's fill can be on its ::before (the squircle mask lives there so the new-dot is not cut) */
      const fill = tileEl ? ((/rgba?\([^)]*,\s*0\)$|transparent/.test(getComputedStyle(tileEl).backgroundColor)) ? getComputedStyle(tileEl, '::before').backgroundColor : getComputedStyle(tileEl).backgroundColor) : null;
      const rimC = btn ? getComputedStyle(btn).borderTopColor : '', rimW = btn ? parseFloat(getComputedStyle(btn).borderTopWidth) : 0;
      const rimA = +((rimC.match(/rgba\([^)]*,\s*([\d.]+)\)/) || [])[1] || (rimC.startsWith('rgb(') ? 1 : 0));
      const rim = rimW >= 1 && rimA >= .14 && (lum(rimC) || 0) > .5;
      const card = hero ? solid(hero.querySelector('.profile-hero-id') || hero) : null;
      let ratio = null;
      if(fill && card){ const a = lum(fill), b = lum(card); if(a != null && b != null) ratio = (Math.max(a, b) + .05) / (Math.min(a, b) + .05); }
      const steps = (typeof PROFILE_TIPS_289 !== 'undefined' ? PROFILE_TIPS_289 : []).map(s => s.target);
      return { order: cls, caseBottom: cr ? Math.round(cr.bottom) : null, barTop: Math.round(barTop),
        widthPct: br && hr ? Math.round(100 * br.width / hr.width) : 0, h: br ? Math.round(br.height) : 0,
        sameRowAsName, fill, card, rim, rimC, ratio: ratio && Math.round(ratio * 10) / 10,
        tourCase: steps.findIndex(t => /pf-case/.test(t)), tourGoal: steps.findIndex(t => /pf-goal/.test(t)) }; }""")
    ck("1. the badge case is the card straight under the person card, above the next rank (%s)" % r["order"],
       r["order"][:3] == ["hero", "case", "goal"], r["order"])
    ck("1. and it is on screen without scrolling (bottom %s above the tab bar %s)" % (r["caseBottom"], r["barTop"]),
       r["caseBottom"] is not None and r["caseBottom"] <= r["barTop"], r)
    ck("1. the Profile tour visits the case before the next rank", 0 <= r["tourCase"] < r["tourGoal"], r)
    ck("2. Customize is its own row, not beside the name", r["sameRowAsName"] is False, r)
    ck("2. Customize spans the person card (%s%% of its width) and is a full tap target (%spx)" % (r["widthPct"], r["h"]),
       r["widthPct"] >= 80 and r["h"] >= 44, r)
    ck("2. Customize stands out from the card behind it: a light rim (%s) and its tile %s:1 on the card (%s on %s)" % (r["rimC"], r["ratio"], r["fill"], r["card"]),
       r["rim"] and (r["ratio"] or 0) >= 3, r)
    pg.evaluate("()=>document.querySelector('#stage .profile-hero .profile-edit-btn').click()"); pg.wait_for_timeout(1200)
    ck("2. and it opens Customize", pg.evaluate("()=>!!document.querySelector('#stage .screen-customize')"))
    ck("no page errors", not errs, errs[:2])
    ctx.close()

    print("\n3. the secret flare in a test")
    ARM = """(found)=>{ const topics=[...new Set(QUESTIONS.map(q=>(q.topic||'').trim()))].filter(Boolean); const t=topics[0];
      cfg.mode='drill'; cfg.source='all'; cfg.units=[t];
      const pool=QUESTIONS.map((q,i)=>[q,i]).filter(([q])=>(q.topic||'').trim()===t).map(([,i])=>i);
      store.mysteryColorsFound = found; store.flareMissed = Object.keys(found).length ? {} : { orange: true }; beginRun(pool, null, null); }"""
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
    ck("3. never found one (and missed orange once): a 'Tap' tag beside it, part of the button", m0.get("tag") is True and m0.get("inButton") is True and (m0.get("text") or "").lower().startswith("tap"), m0)
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

    print("\n5. Rank ladder and the badge case: Settings rows, Customize's kind (384)")
    errs = []
    ctx, pg = g["open_page"](br, g["init_account"]("", g["store"]()), errs=errs)
    pg.evaluate("()=>{ showProfile('profile'); }"); pg.wait_for_timeout(1600)
    r5 = pg.evaluate("""()=>{ """ + LUM + """
      return ['.pf-goal .pf-goal-foot', '.pf-case-closed .pf-case-count'].map(sel => { const b = document.querySelector('#stage .profile-identity-tab ' + sel); if(!b) return { sel, missing: true };
        const r = b.getBoundingClientRect(); const w = b.querySelector('.pf-goal-foot-word, .pf-case-num');
        const tile = b.querySelector('.settings-row-icon'), chev = b.querySelector('.pf-act-chev'), lab = b.querySelector('.pf-act-label'), words = b.querySelector('.pf-act-words');
        const card = b.closest('.pf-goal, .pf-case'); const cr = card.getBoundingClientRect();
        const tr = tile ? tile.getBoundingClientRect() : null, hr = chev ? chev.getBoundingClientRect() : null, wr = words ? words.getBoundingClientRect() : null;
        const rimC = getComputedStyle(b).borderTopColor, rimW = parseFloat(getComputedStyle(b).borderTopWidth);
        return { sel: sel.split(' ').pop(), words: w ? w.textContent : null, widthPct: Math.round(100 * r.width / cr.width), h: Math.round(r.height),
          tileW: tr ? Math.round(tr.width) : 0, tileIn: tr ? Math.round(tr.left - r.left) : null, chevIn: hr ? Math.round(r.right - hr.right) : null,
          label: lab ? parseFloat(getComputedStyle(lab).fontSize) : 0, after: tr && wr ? Math.round(wr.left - tr.right) : null,
          dy: wr ? Math.round(((wr.top + wr.height / 2) - (r.top + r.height / 2)) * 10) / 10 : null, rim: rimW >= 1 && (lum(rimC) || 0) > .5 }; }); }""")
    for b in r5:
        ck("5. %s: a row - (384 r8) the Settings menu's 28px tile on the left (%spx, %spx in), its chevron on the right (%spx in), its name at %spx straight after the tile (%spx)"
           % (b.get("sel"), b.get("tileW"), b.get("tileIn"), b.get("chevIn"), b.get("label"), b.get("after")),
           not b.get("missing") and 27 <= b.get("tileW", 0) <= 29 and 0 <= (b.get("tileIn") or -1) <= 18 and 0 <= (b.get("chevIn") or -1) <= 20 and b.get("label", 0) >= 18 and 8 <= (b.get("after") or 0) <= 20, b)
        ck("5. %s: the words in the row's middle top to bottom (%spx off)" % (b.get("sel"), b.get("dy")), b.get("dy") is not None and abs(b["dy"]) <= 1, b)
        ck("5. %s: wide (%s%% of its card), a full tap target (%spx), a light rim" % (b.get("sel"), b.get("widthPct"), b.get("h")),
           b.get("widthPct", 0) >= 60 and b.get("h", 0) >= 56 and b.get("rim"), b)
    pg.evaluate("()=>document.querySelector('#stage .pf-goal .pf-goal-foot').click()"); pg.wait_for_timeout(1200)
    ck("5. See rank ladder still opens the rank ladder", pg.evaluate("()=>!!document.querySelector('#stage .screen-ranks')"))
    ck("no page errors", not errs, errs[:2])
    ctx.close()

    print("\n6. a found badge on a unit card: the token alone, not the case's slot round it")
    errs = []
    ctx, pg = g["open_page"](br, g["init_account"]("", g["store"]()), errs=errs)
    pg.evaluate("""()=>{ const all = topicsIn(QUESTIONS);
      store.unitPerfects = Object.fromEntries(all.slice(0, 6).map(u => [u, badgeThresholdFor(u)]));
      try{ warmBadgeStrikes(); }catch(e){} }""")
    pg.wait_for_timeout(5000)
    pg.evaluate("()=>{ cfg.mode='drill'; cfg.units=[]; cfg.source='all'; showSetup(); }"); pg.wait_for_timeout(2500)
    r6 = pg.evaluate("""async()=>{ const read = async b => { const im = b.querySelector('img.pick-badge-img'), sv = b.querySelector('svg');
        const xml = im ? await (await fetch(im.src)).text() : sv ? new XMLSerializer().serializeToString(sv) : '';
        return { slot: /-lip"|badge-seat-shade/.test(xml), wall: /-wall"/.test(xml) }; };
      const cards = [...document.querySelectorAll('#stage .picks > label.pick')];
      const found = [], open = [];
      for(const c of cards){ const b = c.querySelector('.pick-badge'); if(!b) continue;
        if(b.classList.contains('earned')){ if(found.length < 4) found.push(await read(b)); } else if(open.length < 2) open.push(await read(b)); }
      return { found, open }; }""")
    ck("6. found badges on the cards: no dark wall or light lip round them (%d read)" % len(r6["found"]),
       len(r6["found"]) >= 3 and not any(x["slot"] or x["wall"] for x in r6["found"]), r6)
    ck("6. a badge not yet found is still its empty slot (build 314: seen, not shown)", r6["open"] and all(x["wall"] for x in r6["open"]), r6)
    ck("no page errors", not errs, errs[:2])
    ctx.close()

    print("\n4. the calendar's dots: one flat look (383: \"I notice the test one is glowing\")")
    for (w, h, dev) in ((440, 956, "phone"), (834, 1194, "iPad")):
        errs = []
        ctx, pg = g["open_page"](br, g["init_account"]("", g["store"]()), w=w, h=h, errs=errs)
        pg.evaluate("()=>{ showCalendarTab(); }"); pg.wait_for_timeout(1500)
        r = pg.evaluate("""()=>{ const sh = e => getComputedStyle(e).boxShadow;
          const key = [...document.querySelectorAll('#stage .cal-grid-legend .cal-legend-dot')].map(d => ({ cls: d.className, sh: sh(d) }));
          const grid = [...document.querySelectorAll('#stage .cal-grid .cal-cell-dot')].map(d => sh(d));
          return { key, keyGlow: key.filter(k => k.sh !== 'none').map(k => k.cls), gridDots: grid.length, gridGlow: grid.filter(x => x !== 'none').length,
                   testInKey: key.some(k => /cal-cell-dot-test/.test(k.cls)), testInGrid: !!document.querySelector('#stage .cal-grid .cal-cell-dot-test') }; }""")
        ck("4. %s: the key's four marks, none glowing (%s)" % (dev, r["keyGlow"]), len(r["key"]) >= 4 and r["testInKey"] and not r["keyGlow"], r)
        ck("4. %s: the grid's dots, none glowing (%d of %d)" % (dev, r["gridGlow"], r["gridDots"]), r["gridDots"] > 0 and r["testInGrid"] and r["gridGlow"] == 0, r)
        ck("no page errors", not errs, errs[:2])
        ctx.close()
    br.close()

print("\nALL PASS" if not fails else "\nFAILED: %d" % len(fails))
sys.exit(1 if fails else 0)
