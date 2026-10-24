#!/usr/bin/env python3
"""Build 327z10: the chat sheet slides down when swiped away, and smoothly.

Madison: "The chat when swiping down, it just disappears, it doesn't do the
animation that it goes downwards, and it's laggy."

Real touch input (CDP Input.dispatchTouchEvent), installed, on an iPhone 17
Pro Max (440x956 @3), the modern dark layout (the default):

  python3 tools/check-b327z10.py
  python3 tools/check-b327z10.py --against /path/to/old/index.html

  A. While a finger pulls the sheet (past the flat-fill point) and through
     the slide out, the sheet carries no backdrop blur - read off the
     computed style every frame.
  B. Let go past the line, the sheet travels from where the finger let go to
     off the bottom over at least 120ms, and at a quarter of that time it is no more
     than 58% of the way (the old .26s ease-out was about two thirds there).
  C. Closed, it rests off the bottom; opened again it comes back to rest at
     the same place it opened before. A short pull springs back and stays
     open.
"""
import importlib.util
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("z5b", os.path.join(HERE, "check-b327z5-b.py"))
z5b = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(z5b)   # check-behaviour reads --against itself
cb = z5b.cb
check = cb.check
from playwright.sync_api import sync_playwright

TRACE = """() => { const p = document.querySelector('.chatdock-panel'); window.__tr = []; window.__stop = false;
  const L = () => { const cs = getComputedStyle(p);
    __tr.push({ t: performance.now(), top: p.getBoundingClientRect().top, bf: cs.backdropFilter, wbf: cs.webkitBackdropFilter || '',
                flat: p.classList.contains('is-flat'), open: chatDockOpen, rel: !!window.__released });
    if(__tr.length < 400 && !window.__stop) requestAnimationFrame(L); };
  requestAnimationFrame(L); }"""

READ = """() => { const p = document.querySelector('.chatdock-panel'); const r = p.getBoundingClientRect();
  return { top: r.top, h: r.height, open: chatDockOpen, inline: p.style.transform, vh: innerHeight }; }"""


ONLY = os.environ.get("B327Z10_ONLY", "ABCDEFGHIJ")

UA_IPHONE = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1"
IPHONE_INIT = "Object.defineProperty(navigator,'userAgent',{get:()=>%r});" % UA_IPHONE


def chat_sheet(br):
        label, w, h, dpr = z5b.PHONE
        ctx, pg = z5b.boot(br, w, h, dpr)
        lay = pg.evaluate("() => document.documentElement.dataset.layout + '/' + document.documentElement.dataset.theme")
        check("%s: the modern dark layout is on (%s)" % (label, lay), lay == "modern/dark", lay)
        o = pg.evaluate(z5b.OPEN_CHAT)
        cdp = ctx.new_cdp_session(pg)
        pg.evaluate("() => { document.querySelector('.chatdock-panel .vroom-chat-list').scrollTop = 0; }")
        time.sleep(0.3)
        rest = pg.evaluate(READ)
        CD = max(200, int(rest["h"] * 0.5))
        pg.evaluate(TRACE)
        z5b.drag_to(cdp, o["lx"], max(40, o["ly"] - CD // 3), 0, CD, steps=16)
        time.sleep(0.08)
        pg.evaluate("() => { window.__released = true; }")
        z5b.tend(cdp)
        time.sleep(0.9)
        pg.evaluate("() => { window.__stop = true; }")
        tr = pg.evaluate("() => __tr")
        aft = pg.evaluate(READ)

        moving = [f for f in tr if f["flat"] or (f["rel"] and f["top"] > rest["top"] + 2 and f["top"] < aft["top"] - 1)]
        blurred = [f for f in moving if (f["bf"] not in ("none", "")) or (f["wbf"] not in ("none", ""))]
        check("%s: A. no backdrop blur on any frame while it is pulled or slides out (%d of %d frames blurred)"
              % (label, len(blurred), len(moving)), moving and not blurred, blurred[:3])

        check("%s: and let go past the line, it closes" % label, aft["open"] is False, aft)
        after = [f for f in tr if f["rel"]]
        start = after[0]["top"] if after else rest["top"]
        end = aft["top"]
        way = end - start
        tops = [start] + [f["top"] for f in after]
        moved = [f for f in after if f["top"] > start + 0.5]
        t0 = moved[0]["t"] - 16.7 if moved else 0
        done = next((f["t"] for f in moved if f["top"] >= end - 1), t0)
        dur = done - t0
        q = t0 + dur / 4
        # how far it is at a quarter of its slide, interpolated between frames
        prev = (t0, start)
        at_q = end
        for f in moved:
            if f["t"] >= q:
                a, b = prev, (f["t"], f["top"])
                at_q = a[1] + (b[1] - a[1]) * ((q - a[0]) / max(0.01, b[0] - a[0]))
                break
            prev = (f["t"], f["top"])
        frac = (at_q - start) / max(1, way)
        check("%s: B. it slides from where the finger let go (%.0f) to off the bottom (%.0f) over %.0fms, %.0f%% of the way at a quarter of that (an ease-out that leaps is over 58%%)"
              % (label, start, end, dur, 100 * frac),
              way > 80 and end >= aft["vh"] - 1 and dur >= 120 and frac <= 0.58,
              [round(f["top"]) for f in moved])
        check("%s: C. closed, nothing inline is left on it" % label, aft["inline"] == "", aft)

        # reopen: back where it rested
        pg.evaluate("() => { openChatDock(); }")
        time.sleep(0.6)
        re = pg.evaluate(READ)
        check("%s: C. opened again, it rests where it did (%.0f, was %.0f)" % (label, re["top"], rest["top"]),
              re["open"] and abs(re["top"] - rest["top"]) < 2, [re, rest])

        # a short pull springs back
        pg.evaluate("() => { document.querySelector('.chatdock-panel .vroom-chat-list').scrollTop = 0; }")
        time.sleep(0.3)
        z5b.drag_to(cdp, o["lx"], o["ly"], 0, 60, steps=8, wait=0.05)
        time.sleep(0.3)
        z5b.tend(cdp)
        time.sleep(0.7)
        sp = pg.evaluate(READ)
        check("%s: C. a short slow pull springs back and stays open (%.0f)" % (label, sp["top"]),
              sp["open"] and abs(sp["top"] - rest["top"]) < 2 and sp["inline"] == "", sp)
        ctx.close()


def tab_roll(br):
    print("\nD. a tapped tab's screen waits for the glass to roll over")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.wait_for_timeout(2500)
    cdp = ctx.new_cdp_session(pg)
    t = pg.evaluate("()=>{const r=document.getElementById('bottomtab-profile').getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}}")
    pg.evaluate("""() => { window.__z10 = { mount: null, lens: null, down: null };
      addEventListener('pointerdown', () => { __z10.down = performance.now(); }, true);
      new MutationObserver(() => { if(__z10.mount !== null || __z10.down === null) return;
        __z10.mount = performance.now() - __z10.down;
        const a = document.querySelector('#bottomtabs-lens .tab-lens-body');
        const an = a && a.getAnimations()[0];
        __z10.lensUp = !!document.querySelector('#bottomtabs-lens.is-up'); }).observe(document.getElementById('stage'), { childList: true }); }""")
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [t]})
    time.sleep(0.06)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    pg.wait_for_timeout(1200)
    r = pg.evaluate("() => Object.assign({}, __z10, { profile: !!document.querySelector('#stage .bottomtab-profile, #stage [class*=profile]'), lit: document.getElementById('bottomtab-profile').classList.contains('active') })")
    check("%s: D. the screen goes in %.0fms after the press - after the glass has crossed (90ms or more), not on the frame after a quick tap's click"
          % (label, r.get("mount") or -1), (r.get("mount") or 0) >= 90 and r.get("lit"), r)
    ctx.close()


def planet(br):
    print("\nE. the planet answers once")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.wait_for_timeout(2500)
    r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
      const tap = () => { const s = document.querySelector('#stage .screen-home-actual .cosmic-sphere-hsw') || [...document.querySelectorAll('#stage .screen-home-actual circle')].find(c => /^url\\(#cosmicSphereGrad/.test(c.getAttribute('fill') || ''));
        const b = s.getBoundingClientRect(), x = b.left + b.width / 2, y = b.top + b.height / 2;
        const o = { bubbles: true, cancelable: true, clientX: x, clientY: y, pointerId: 7, isPrimary: true, pointerType: 'touch', button: 0 };
        s.dispatchEvent(new PointerEvent('pointerdown', o)); s.dispatchEvent(new PointerEvent('pointerup', o)); s.dispatchEvent(new MouseEvent('click', o)); };
      const live = () => [...document.querySelectorAll('#stage .home-caption > .hc-item:not(.is-out)')].map(e => e.dataset.text);
      tap(); await wait(500); const a = live();
      tap(); await wait(500); const b = live();
      return { a, b, items: document.querySelectorAll('#stage .home-caption > .hc-item').length }; }""")
    a, b = r["a"], r["b"]
    one = a[0] if len(a) == 1 else ""
    check("%s: E. two taps on the planet: one caption, the same words both times, %d sentences" % (label, one.count(".")),
          len(a) == 1 and len(b) == 1 and a == b and one.count(".") >= 2, r)
    ctx.close()


def tab_special(br):
    print("\nF. the Profile tab's character plays its special")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.wait_for_timeout(2500)
    r = pg.evaluate("""async () => { const el = document.querySelector('#bottomtab-profile .bottomtab-icon-avatar');
      if(!el) return { el: false };
      const listed = el.matches(CHAR_SPECIAL_PROMINENT);
      /* the scheduler's own pick: everything due now */
      el.dataset.spNext = '1'; charSpecialBusyUntil = 0; charSpecialTick();
      await new Promise(r => setTimeout(r, 400));
      const on = el.classList.contains('char-special');
      const moving = [...el.querySelectorAll('.cx-sp *')].some(n => n.getAnimations().some(a => a.playState === 'running'));
      return { el: true, listed, on, moving }; }""")
    check("%s: F. the tab's character is one the specials scheduler plays, and its special runs" % label,
          r.get("listed") and r.get("on") and r.get("moving"), r)
    ctx.close()


def daily_ring(br):
    print("\nG. the daily question's ring is a line of light on the glass rim")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.wait_for_timeout(2000)
    r = pg.evaluate("""() => { store.dailyQuestionDate = dailyPeriodKey(); showHome(); return 1; }""")
    pg.wait_for_timeout(1200)
    r = pg.evaluate("""() => { const b = document.querySelector('.daily-question-fab'), ring = b && b.querySelector('.dq-ring');
      if(!ring) return null; const svg = ring.querySelector('svg'), k = svg.getBoundingClientRect().width / 100;
      const tr = getComputedStyle(ring.querySelector('.dq-ring-track')), pr = getComputedStyle(ring.querySelector('.dq-ring-prog'));
      const rgb = (tr.stroke.match(/[\d.]+/g) || []).map(Number);
      const br = b.getBoundingClientRect(), rr = ring.getBoundingClientRect();
      return { track: tr.stroke, hue: rgb.length >= 3 ? Math.max(rgb[0], rgb[1], rgb[2]) - Math.min(rgb[0], rgb[1], rgb[2]) : 99,
               progPx: parseFloat(pr.strokeWidth) * k, d: Math.max(Math.abs(br.left - rr.left), Math.abs(br.top - rr.top)) }; }""")
    check("%s: G. the unlit track is the glass rim - no colour of its own (%s)" % (label, r and r["track"]), bool(r) and r["hue"] <= 2, r)
    check("%s: G. the progress is a slim line, %.1fpx (2px at most), on the button's rim" % (label, r and r["progPx"] or -1),
          bool(r) and r["progPx"] <= 2.0 and r["d"] <= 2, r)
    ctx.close()


def round2(br):
    """H. Madison's second list (327z10): each line one report."""
    print("\nH. the second list: Profile, people, friends, sheets, switches, haptics")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.wait_for_timeout(2000)
    # H1 the Profile card's rim is the cards' rim, not the banner's colour
    r = pg.evaluate("""async () => { store.banner = 'tests250'; window.bannerEarned = () => true; muteBanners = true; showProfile();
      await new Promise(r => setTimeout(r, 900)); const c = document.querySelector('#stage .profile-hero');
      const probe = document.createElement('div'); probe.style.borderColor = 'var(--surface-border)'; document.body.appendChild(probe);
      const want = getComputedStyle(probe).borderTopColor; probe.remove();
      const b = document.querySelector('#stage .profile-cover .bnr');
      return { rim: getComputedStyle(c).borderTopColor, want, layered: !!(b && b.classList.contains('bnr-layered')), idle: !!(b && b.classList.contains('rk-idle')) }; }""")
    check("%s: H1. the Profile card's rim is the surface border every card wears (%s), not its banner's colour" % (label, r["rim"]), r["rim"] == r["want"], r)
    # H2 a layered banner is moving from the moment it is built
    r2 = pg.evaluate("""() => { const b = buildBannerArt('tests250'); const out = { layered: b.classList.contains('bnr-layered'), idle: b.classList.contains('rk-idle') }; return out; }""")
    check("%s: H2. a layered (compositor) banner is never built still - it moves from its first frame" % label, r2["layered"] and not r2["idle"], r2)
    # H3 the person card is glass from its first frame: nothing above it is part-transparent
    r3 = pg.evaluate("""() => { document.querySelectorAll('.invite-overlay').forEach(o => o.remove());
      openPersonSheet({ pub: 'pubZ10', firstName: 'Jordan', avatarChar: 'ghost', banner: 'tests250', accent: 'ink', level: 30 });
      const sheet = document.querySelector('.invite-overlay .person-card'); const ov = sheet.closest('.invite-overlay');
      const anc = []; for(let e = sheet.parentElement; e && e !== document.documentElement; e = e.parentElement) anc.push(+getComputedStyle(e).opacity);
      return { minAncestorOpacity: Math.min.apply(null, anc), blur: getComputedStyle(sheet).backdropFilter, tint: sheet.classList.contains('has-tint') }; }""")
    check("%s: H3. the person card's glass sees the page from its first frame (no ancestor below opacity 1: %s), and its banner's colours run into it"
          % (label, r3["minAncestorOpacity"]), r3["minAncestorOpacity"] == 1 and r3["blur"] not in ("", "none") and r3["tint"], r3)
    pg.evaluate("() => document.querySelectorAll('.invite-overlay').forEach(o => o.remove())")
    # H4 a board row's flip-book is cut round on its own
    r4 = pg.evaluate("""() => { const css = [...document.styleSheets].flatMap(sh => { try{ return [...sh.cssRules]; }catch(e){ return []; } });
      const rule = css.find(r => r.selectorText && /rank-row[^,]*\.rank-avatar[^,]*> \.char-flip-play|\.rank-row,\s*\.friend-row-art\) \.rank-avatar/.test(r.selectorText));
      return { mask: rule ? (rule.style.maskImage || rule.style.webkitMaskImage) : '' }; }""")
    check("%s: H4. a board row's flip-book clips itself round (a mask WebKit applies to the layer)" % label, "radial-gradient" in (r4["mask"] or ""), r4)
    # H5 Copy and Send: readable words on their own fill
    r5 = pg.evaluate("""async () => { showFriends(); await new Promise(r => setTimeout(r, 900));
      return [...document.querySelectorAll('#stage .friend-send')].map(b => { const cs = getComputedStyle(b); return [b.textContent.trim(), cs.backgroundColor, cs.color]; }); }""")
    def lum(c):
        v = [float(x) for x in c[c.index("(") + 1:c.index(")")].split(",")[:3]]
        f = lambda u: (u / 255 / 12.92) if u / 255 <= .03928 else ((u / 255 + .055) / 1.055) ** 2.4
        return .2126 * f(v[0]) + .7152 * f(v[1]) + .0722 * f(v[2])
    worst = min([(max(lum(b), lum(c)) + .05) / (min(lum(b), lum(c)) + .05) for _, b, c in r5] or [0])
    check("%s: H5. Copy and Send read on their own fill (worst %.1f:1, needs 4.5)" % (label, worst), len(r5) >= 2 and worst >= 4.5, r5)
    # H6 the start sheet's scroll stops at its ends
    r6 = pg.evaluate("""async () => { cfg.mode = 'drill'; cfg.units = []; showSetup(); await new Promise(r => setTimeout(r, 800));
      document.querySelector('.picks .pick .pname').click(); await new Promise(r => setTimeout(r, 300)); document.getElementById('nextbtn').click();
      await new Promise(r => setTimeout(r, 900)); const sh = document.querySelector('#unitoptions-modal .unitoptions-modal-sheet');
      return { ob: sh ? getComputedStyle(sh).overscrollBehaviorY : null, body: getComputedStyle(document.body).touchAction }; }""")
    check("%s: H6. the start sheet keeps its scroll to itself and nothing under it pans (%s, body %s)" % (label, r6["ob"], r6["body"]),
          r6["ob"] == "contain" and r6["body"] == "none", r6)
    # H7 Max/All leave their "on" look while the slider is still held
    r7 = pg.evaluate("""() => { const b = document.querySelector('#unitoptions-modal .howmany-sect .slider-allbtn'); if(!b) return null;
      syncTopButton(b, true); b._held = true; syncTopButton(b, false); const held = { on: b.classList.contains('on'), fill: b.classList.contains('just-ready'), pop: b.classList.contains('ready-pop') };
      b._held = false; syncTopButton(b, false); const rel = { pop: b.classList.contains('ready-pop') }; return { held, rel }; }""")
    check("%s: H7. sliding off the top: the button changes under the finger (fill, no punch) and punches on the release" % label,
          bool(r7) and not r7["held"]["on"] and r7["held"]["fill"] and not r7["held"]["pop"] and r7["rel"]["pop"], r7)
    # H8 Settings' cards carry no blur under their switches
    r8 = pg.evaluate("""async () => { document.querySelectorAll('.unitoptions-modal').forEach(m => m.remove()); showAppearance(); await new Promise(r => setTimeout(r, 900));
      return [...document.querySelectorAll('#stage .settings-card')].map(c => getComputedStyle(c).backdropFilter); }""")
    check("%s: H8. no Settings card blurs what is behind it (a switch's lens slides inside them)" % label, r8 and all(v in ("none", "") for v in r8), r8)
    # H9 the "open me" pill on the rank box and the case
    r9 = pg.evaluate("""async () => { showProfile(); await new Promise(r => setTimeout(r, 900));
      return [...document.querySelectorAll('#stage .pf-goal-foot, #stage .pf-case-closed .pf-case-count')].map(e => { const cs = getComputedStyle(e), rr = e.getBoundingClientRect();
        return { h: rr.height, radius: parseFloat(cs.borderTopLeftRadius), border: parseFloat(cs.borderTopWidth), chevron: getComputedStyle(e, '::after').content !== 'none' }; }); }""")
    check("%s: H9. the rank box and the case each end in a pill with a chevron, 40px high or more" % label,
          len(r9) == 2 and all(x["h"] >= 39.5 and x["radius"] >= 15 and x["border"] >= 1 and x["chevron"] for x in r9), r9)
    ctx.close()
    # H10 an iPhone: wide short buttons and the switch rows carry a real switch
    ctx2 = br.new_context(viewport={"width": w, "height": h}, has_touch=True, is_mobile=True, device_scale_factor=2)
    ctx2.add_init_script(IPHONE_INIT + "try{Object.defineProperty(navigator,'standalone',{get:()=>true});}catch(e){}")
    ctx2.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.drill.v1', '%s');localStorage.setItem('class26e.weekrecap.v1','9999-12-31');}catch(e){}" % cb.USED_ACCOUNT)
    pg2 = cb.open_page(ctx2); pg2.goto(cb.URL); pg2.wait_for_timeout(3000)
    pg2.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __stub(); showAppearance();}")
    pg2.wait_for_timeout(2500)
    r10 = pg2.evaluate("""() => { const rows = [...document.querySelectorAll('#stage label.opt')].filter(r => r.querySelector(':scope > .box'));
      const ok = rows.filter(r => { const i = r.querySelector(':scope > input[type=checkbox]'); if(!i || !i.hasAttribute('switch')) return false;
        r.scrollIntoView({ block: 'center', behavior: 'instant' });
        const b = r.querySelector(':scope > .box').getBoundingClientRect(); return document.elementFromPoint(b.left + b.width / 2, b.top + b.height / 2) === i; });
      return { rows: rows.length, ok: ok.length }; }""")
    check("%s: H10. on an iPhone every switch row's own input is a native switch over its track (%d of %d)" % (label, r10["ok"], r10["rows"]),
          r10["rows"] >= 4 and r10["ok"] == r10["rows"], r10)
    pg2.evaluate("()=>showFriends()"); pg2.wait_for_timeout(2500)
    r11 = pg2.evaluate("""() => [...document.querySelectorAll('#stage button')].filter(b => { const r = b.getBoundingClientRect(); return r.width > 260 && r.height <= 60 && r.height > 20; })
      .map(b => ({ t: b.textContent.trim().slice(0, 20), w: Math.round(b.getBoundingClientRect().width), hsw: !!b.querySelector(':scope > .nova-hsw') }))""")
    pg2.evaluate("()=>showProfile()"); pg2.wait_for_timeout(2500)
    r11 += pg2.evaluate("""() => [...document.querySelectorAll('#stage button')].filter(b => { const r = b.getBoundingClientRect(); return r.width > 260 && r.height <= 60 && r.height > 20; })
      .map(b => ({ t: b.textContent.trim().slice(0, 20), w: Math.round(b.getBoundingClientRect().width), hsw: !!b.querySelector(':scope > .nova-hsw') }))""")
    check("%s: H11. on an iPhone a wide button of a button's height carries its switch (%d of %d)" % (label, sum(1 for x in r11 if x["hsw"]), len(r11)),
          len(r11) >= 1 and all(x["hsw"] for x in r11), r11)
    ctx2.close()


def unit_tab(br):
    """I. "When in the unit selection screen, and tapping the tab to go
    somewhere else, the bottom tab lags and kinda has a weird placement of
    the bubble." The bar there has the Start pill and icon-only tabs; the
    tapped screen takes them away while the glass is still up. Every frame
    after the bar changes shape, the glass is over the tab that was tapped
    (it used to sit over its neighbour and land there), and the platter ends
    under it."""
    print("\nI. from the unit screen, the glass stays on the tab that was tapped as the bar changes shape")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.wait_for_timeout(2500)
    pg.evaluate("() => { cfg.mode = 'drill'; cfg.units = []; store.seenUnitSelectTour = true; showSetup(); }")
    pg.wait_for_timeout(1800)
    cdp = ctx.new_cdp_session(pg)
    t = pg.evaluate("() => { const b = document.querySelector('.bottomtabs'); const r = document.getElementById('bottomtab-rewards').getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2, start: b.classList.contains('has-start-tab') }; }")
    pg.evaluate("""() => { window.__ut = []; const bar = document.querySelector('.bottomtabs');
      const L = () => { const lens = document.getElementById('bottomtabs-lens'), body = lens && lens.querySelector('.tab-lens-body');
        if(!bar.classList.contains('has-start-tab') && lens && lens.classList.contains('is-up') && +getComputedStyle(lens).opacity > .5){
          const r = body.getBoundingClientRect(), tr = document.getElementById('bottomtab-rewards').getBoundingClientRect();
          __ut.push({ cx: Math.round(r.left + r.width / 2), l: Math.round(tr.left), r: Math.round(tr.right) }); }
        if(__ut.length < 200 && !window.__utStop) requestAnimationFrame(L); };
      requestAnimationFrame(L); }""")
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": t["x"], "y": t["y"]}]})
    time.sleep(0.07)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    pg.wait_for_timeout(1300)
    pg.evaluate("() => { window.__utStop = true; }")
    fr = pg.evaluate("() => __ut")
    end = pg.evaluate("() => { const s = document.querySelector('.bottomtabs-slider').getBoundingClientRect(), tr = document.getElementById('bottomtab-rewards').getBoundingClientRect(); return { scx: Math.round(s.left + s.width / 2), tcx: Math.round(tr.left + tr.width / 2), lit: document.getElementById('bottomtab-rewards').classList.contains('active') }; }")
    off = [f for f in fr if not (f["l"] - 2 <= f["cx"] <= f["r"] + 2)]
    check("%s: I. the bar left its Start shape with the glass up (%d frames) and on every one the glass was over Leaderboard (%d off)" % (label, len(fr), len(off)),
          t["start"] and len(fr) >= 3 and not off, off[:4] or fr[:3])
    check("%s: I. and the platter ends under Leaderboard (%d vs %d)" % (label, end["scx"], end["tcx"]), end["lit"] and abs(end["scx"] - end["tcx"]) <= 2, end)
    ctx.close()


def tab_search(br):
    """J. "The search button, while in a review can we make the search
    function similar to how the Apple Music search function is?" A circle
    beside the tab bar; tapped, the bar draws in to one circle and the
    circle stretches into the field, focused; typing filters the list;
    the small circle puts it all back, the search cleared."""
    print("\nJ. Review's search beside the tab bar, as Apple Music's")
    for label, w, h, dpr in (z5b.PHONE, ("iPhone SE", 320, 568, 2)):
        ctx, pg = z5b.boot(br, w, h, dpr)
        pg.wait_for_timeout(2000)
        pg.evaluate("() => { const u = topicsIn(QUESTIONS).slice(0, 3); showAnswerReview(u, 'all', {}, {}); }")
        pg.wait_for_timeout(1500)
        R = """() => { const rr = e => { if(!e) return null; const r = e.getBoundingClientRect(); return { l: r.left, r: r.right, t: r.top, b: r.bottom, w: r.width, h: r.height }; };
          return { bar: rr(document.querySelector('.bottomtabs')), ts: document.getElementById('tabsearch') && !document.getElementById('tabsearch').hidden ? rr(document.getElementById('tabsearch')) : null,
                   top: !!document.querySelector('#stage .screen-answerreview .searchwrap:not([hidden])'), sects: document.querySelectorAll('#stage .cal-list .cal-month-sect').length,
                   tabs: [...document.querySelectorAll('.bottomtabs-navrow .bottomtab')].filter(t => t.getBoundingClientRect().width > 4 && +getComputedStyle(t).opacity > .5).length,
                   focus: document.activeElement && document.activeElement.className, vw: innerWidth }; }"""
        c = pg.evaluate(R)
        ok = c["ts"] and abs(c["ts"]["t"] - c["bar"]["t"]) < 1.5 and abs(c["ts"]["h"] - c["bar"]["h"]) < 1.5 and 4 <= c["ts"]["l"] - c["bar"]["r"] <= 14 \
            and abs((c["bar"]["l"] + c["ts"]["r"]) / 2 - c["vw"] / 2) < 2 and not c["top"]
        check("%s: J. closed, a circle the bar's height stands beside it, the pair centred, Review's own field gone" % label, ok, c)
        cdp = ctx.new_cdp_session(pg)
        b = pg.evaluate("() => { const r = document.querySelector('#tabsearch .tabsearch-btn').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }")
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": b[0], "y": b[1]}]}); time.sleep(0.06)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        pg.wait_for_timeout(600)
        o = pg.evaluate(R)
        ok2 = o["tabs"] == 1 and o["ts"] and o["ts"]["l"] - o["bar"]["r"] < 14 and o["ts"]["w"] > c["bar"]["w"] * .6 and o["focus"] == "tabsearch-input" \
            and abs(o["ts"]["r"] - c["ts"]["r"]) < 2
        check("%s: J. tapped, the bar is one tab's circle and the field runs to where the circle was, focused" % label, ok2, o)
        n0 = o["sects"]
        pg.keyboard.type("ethics"); pg.wait_for_timeout(400)
        f = pg.evaluate(R)
        check("%s: J. typing filters the list (%d -> %d sections)" % (label, n0, f["sects"]), 0 < f["sects"] < n0 or (n0 == 1 and f["sects"] == 1), f)
        bb = pg.evaluate("() => { const r = document.querySelector('.bottomtabs').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }")
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": bb[0], "y": bb[1]}]}); time.sleep(0.06)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        pg.wait_for_timeout(700)
        e = pg.evaluate(R)
        scr = pg.evaluate("() => (document.querySelector('#stage > *') || {}).className")
        ok3 = e["tabs"] == 4 and abs(e["bar"]["l"] - c["bar"]["l"]) < 1.5 and abs(e["bar"]["w"] - c["bar"]["w"]) < 1.5 and abs(e["ts"]["l"] - c["ts"]["l"]) < 1.5 \
            and e["sects"] == n0 and "answerreview" in (scr or "")
        check("%s: J. the small circle puts it all back where it was, the search cleared, still on Review" % label, ok3, [e, scr])
        ctx.close()


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cb.CHROME)
        for k, fn in (("A", chat_sheet), ("D", tab_roll), ("E", planet), ("F", tab_special), ("G", daily_ring), ("H", round2), ("I", unit_tab), ("J", tab_search)):
            if k in ONLY or (k == "A" and any(c in ONLY for c in "ABC")):
                try:
                    fn(br)
                except Exception as e:
                    check("section %s ran" % k, False, repr(e)[:300])
        br.close()
    print("\n%s" % ("ALL PASS" if not cb.FAILURES else "%d FAILED" % len(cb.FAILURES)))
    sys.exit(1 if cb.FAILURES else 0)


if __name__ == "__main__":
    main()
