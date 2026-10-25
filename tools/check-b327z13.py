#!/usr/bin/env python3
"""Build 327z13: the tab bar's glass crosses slower, and nothing is built under it.

Madison: "The bottom tab is getting better but the pill bubble thing still
moves too fast when clicking through the bottom tab. It also lags. Please
ensure it's perfect, leave no stone unturned."

Real touch input on an iPhone 17 Pro Max (440x956 @3), installed:

  python3 tools/check-b327z13.py
  python3 tools/check-b327z13.py --against /path/to/old/index.html

  S. The glide, read off the lens's own 60fps track (so the machine's speed
     cannot move it): a quarter to two fifths of the way at 4 frames, no
     more than four fifths at 8, nine tenths by 16, and never past the tab.
  T. A quick tap (60ms): the lens does not start to shrink until it is
     95% of the way to the tapped tab, and is up 320ms or more from the
     press - a glide you can watch (the 327z12 one was down at ~260ms).
  U. The tapped tab's screen is built only once the glass has crossed: at
     the moment #stage changes, 270ms or more after the press, the lens's
     own track is 90% or more of the way. (A build is a long main-thread
     task; under the glide it held the glass's frames.)

  Round 2 (the same build), one section per report:
  V. "The calendar tab ... it's hard to scroll down all over this page it's
     registering clicking stuff": on an iPhone no wide button repeated in a
     list (the Final exams rows) carries a native switch; a lone one still does.
  W. "Haptic Touch isn't working ... mode selection and unit selection":
     every unit card's own checkbox is a native switch over its tick (44px),
     and picking by it still picks; every mode card carries a switch over
     its head only.
  X. Profile: "there's a button to open the tab but if you click anywhere it
     opens it ... should only be the button" - a tap on the case or the Next
     rank card away from their pills opens nothing; the pills open the
     Badges and Rank screens; a challenge row and each unlock tile open their
     own card; tapping your character plays its move.
  Y. Stats has no "Your units" box (Needs work / Strongest); Find me has no
     icon; the UFO takes 200 hundos and Bubbles 150; Astral, Celestial and
     Zenith are veiled until earned; the Sheriff's note is one sentence; a
     locked card sets its requirement apart from its note.
  Z. A board's characters move while their sheets are made: of a fresh
     board's rows on screen, at least six are moving within three seconds.
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

ONLY = os.environ.get("B327Z13_ONLY", "STUVWXYZ")

# the lens body's centre x on each keyframe, and its height
TRACK = """() => { const body = document.querySelector('#bottomtabs-lens .tab-lens-body'); const a = body && body.getAnimations()[0];
  if(!a) return null;
  const rd = k => { const m = /translate3d\\(([-\\d.]+)px,\\s*([-\\d.]+)px[^)]*\\) scale\\(([-\\d.]+),\\s*([-\\d.]+)/.exec(k.transform || '');
    return m ? { cx: +m[1] + +m[3] * 50, h: +m[4] } : null; };
  /* MOVED IN 327z15 round 40: the track has 120 keyframes a second - read at 60 a second, by its duration */
  const all = a.effect.getKeyframes().map(rd).filter(Boolean);
  const per = (all.length - 1) / ((a.effect.getTiming().duration || 1) / (1000 / 60));
  const frames = []; for(let f = 0; f * per <= all.length - 1; f++) frames.push(all[Math.round(f * per)]);
  return { t: a.currentTime, frames }; }"""


def centre(pg, tid):
    return pg.evaluate("id => { const r = document.getElementById(id).getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; }", tid)


def glide(br):
    print("\nS. the glide's pace")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.wait_for_timeout(2500)
    cdp = ctx.new_cdp_session(pg)
    for tid in ("bottomtab-profile", "bottomtab-calendar"):
        t = centre(pg, tid)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [t]})
        pg.wait_for_timeout(30)
        r = pg.evaluate(TRACK)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        pg.wait_for_timeout(1500)
        xs = [f["cx"] for f in (r or {}).get("frames", [])]
        p = [(x - xs[0]) / ((xs[-1] - xs[0]) or 1) for x in xs] if xs else []
        ok = len(p) > 17 and .25 <= p[4] <= .42 and p[8] <= .8 and p[16] >= .9 and max(p) <= 1.01
        check("%s: S. to %s the glass is %s of the way at frames 4 / 8 / 16, never past it (max %.3f)"
              % (label, tid.split("-")[1], p and "%.2f / %.2f / %.2f" % (p[4], p[8], p[min(16, len(p) - 1)]), max(p) if p else -1),
              ok, [round(v, 3) for v in p[:24]])
    ctx.close()


def quick_tap(br):
    print("\nT. a quick tap stays up until it has arrived")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.wait_for_timeout(2500)
    cdp = ctx.new_cdp_session(pg)
    t = centre(pg, "bottomtab-calendar")
    x0 = pg.evaluate(TRACK)
    pg.evaluate("() => { window.__t = {}; addEventListener('pointerdown', () => { __t.down = performance.now(); }, { capture: true, once: true }); addEventListener('touchend', () => { __t.up = performance.now(); }, { capture: true, once: true }); }")
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [t]})
    pg.wait_for_timeout(20)
    a = pg.evaluate(TRACK)
    time.sleep(0.04)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    pg.wait_for_timeout(30)
    r = pg.evaluate(TRACK)
    tt = pg.evaluate("() => window.__t")
    rel = (tt.get("up") or 0) - (tt.get("down") or 0)
    pg.wait_for_timeout(1500)
    start = (a or {}).get("frames", [{}])[0].get("cx")
    fr = (r or {}).get("frames", [])
    if not fr or start is None:
        check("%s: T. the release has a track" % label, False, [a, r])
        ctx.close()
        return
    end = fr[-1]["cx"]
    hmax = max(f["h"] for f in fr)
    shrink = next((i for i, f in enumerate(fr) if i > 0 and f["h"] < hmax * .97 and fr[i - 1]["h"] >= f["h"] and any(g["h"] >= hmax * .99 for g in fr[:i])), None)
    prog = (fr[shrink]["cx"] - start) / ((end - start) or 1) if shrink is not None else None
    upMs = rel + shrink * 1000 / 60 if shrink is not None else None
    check("%s: T. a 60ms tap's lens starts to shrink only once it is 95%%+ of the way (%.2f), %.0fms after the press (320+)"
          % (label, prog if prog is not None else -1, upMs or -1), prog is not None and prog >= .95 and (upMs or 0) >= 320, [prog, shrink, upMs])
    ctx.close()


def build_after(br):
    print("\nU. the screen is built once the glass has crossed")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.wait_for_timeout(2500)
    cdp = ctx.new_cdp_session(pg)
    for tid in ("bottomtab-profile", "bottomtab-calendar", "bottomtab-home"):
        t = centre(pg, tid)
        pg.evaluate("""() => { window.__u = { mount: null, down: null, track: null, at: null };
          addEventListener('pointerdown', () => { __u.down = performance.now(); setTimeout(() => {
            const body = document.querySelector('#bottomtabs-lens .tab-lens-body'); const a = body && body.getAnimations()[0];
            if(a) __u.track = a; }, 0); }, { capture: true, once: true });
          const mo = new MutationObserver(() => { if(__u.mount !== null || __u.down === null) return;
            __u.mount = performance.now() - __u.down;
            const body = document.querySelector('#bottomtabs-lens .tab-lens-body'); const a = body && body.getAnimations()[0];
            __u.at = a ? a.currentTime : null; mo.disconnect(); });
          mo.observe(document.getElementById('stage'), { childList: true }); }""")
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [t]})
        time.sleep(0.06)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        pg.wait_for_timeout(1600)
        # where the glide (the press's own track) was at the moment of the build:
        # the same spring is replayed from rest to read it at that time
        r = pg.evaluate("""() => { const m = __u.mount, a = __u.track;
          if(!a || m === null) return { mount: m, prog: null, track: !!a };
          const rd = k => { const mm = /translate3d\\(([-\\d.]+)px,\\s*([-\\d.]+)px[^)]*\\) scale\\(([-\\d.]+)/.exec(k.transform || ''); return mm ? +mm[1] + +mm[3] * 50 : null; };
          const xs = a.effect.getKeyframes().map(rd).filter(v => v !== null);
          /* by the track's duration: it has 120 keyframes a second since round 40 */
          const i = Math.min(xs.length - 1, Math.floor(m / (a.effect.getTiming().duration || 1) * (xs.length - 1)));
          return { mount: m, prog: (xs[i] - xs[0]) / ((xs[xs.length - 1] - xs[0]) || 1),
                   lit: document.querySelector('.bottomtab.active') && document.querySelector('.bottomtab.active').id }; }""")
        # MOVED IN 327z15 round 35 (TAB_SCREEN_AFTER 290 -> 170): "When using the bottom
        # tab, there is lag ... when opening different screens". The page goes in just
        # past a quick tap's release, while the glass is still crossing (a transform the
        # compositor carries), not after it lands - 150ms+, with the glide well under way.
        check("%s: U. %s's screen goes in %.0fms after the press (150+), the glide %.0f%% of the way (80%%+), on its tab"
              % (label, tid.split("-")[1], r.get("mount") or -1, 100 * (r.get("prog") or 0)),
              (r.get("prog") or 0) >= .8 and (r.get("mount") or 0) >= 150 and r.get("lit") == tid, r)
    ctx.close()


UA_IPHONE = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1"
IPHONE_INIT = "Object.defineProperty(navigator,'userAgent',{get:()=>%r});try{Object.defineProperty(navigator,'standalone',{get:()=>true});}catch(e){}" % UA_IPHONE
CLEAN = "() => document.querySelectorAll('#tour-overlay, #tour-tooltip, .daily-alert, .toast, .invite-overlay').forEach(x => x.remove())"


def iphone(br):
    ctx, pg = cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT, touch=True, dpr=2, init=IPHONE_INIT)
    pg.wait_for_timeout(2500)
    pg.evaluate("() => { document.getElementById('splashscreen')?.remove(); store.seenUnitSelectTour = true; store.seenUnitHoldTip = true; }")
    return ctx, pg


def lists(br):
    print("\nV. no switch on a list's rows")
    ctx, pg = iphone(br)
    pg.evaluate("() => showCalendarTab()")
    pg.wait_for_timeout(2500)
    r = pg.evaluate("""() => ({ rows: [...document.querySelectorAll('#stage .cal-big-row')].map(b => !!b.querySelector(':scope > .nova-hsw')),
      arrows: [...document.querySelectorAll('#stage .cal-grid-arrow')].map(b => !!b.querySelector(':scope > .nova-hsw')) })""")
    check("V. the calendar's Final exams rows carry no switch (%d rows), its arrows keep theirs" % len(r["rows"]),
          len(r["rows"]) >= 3 and not any(r["rows"]) and r["arrows"] and all(r["arrows"]), r)
    pg.evaluate("() => showAppearance()")
    pg.wait_for_timeout(2500)
    a = pg.evaluate("() => { const b = document.querySelector('#stage .adv-toggle'); return b ? !!b.querySelector(':scope > .nova-hsw') : null; }")
    check("V. a lone wide button (Advanced settings) still carries its switch", a is True, a)
    ctx.close()


def picks(br):
    print("\nW. unit cards and mode cards tick on an iPhone")
    ctx, pg = iphone(br)
    pg.evaluate("() => showSetup()")
    pg.wait_for_timeout(2500)
    pg.evaluate(CLEAN)
    r = pg.evaluate("""() => { const ps = [...document.querySelectorAll('.picks > label.pick')];
      const ok = ps.filter(p => { const i = p.querySelector(':scope > input'); if(!i || !i.hasAttribute('switch')) return false;
        const b = p.querySelector(':scope > .box').getBoundingClientRect(), r = i.getBoundingClientRect();
        return r.width >= 44 && r.height >= 44 && r.width <= 46 && Math.abs((r.left + r.width / 2) - (b.left + b.width / 2)) < 1.5 && Math.abs((r.top + r.height / 2) - (b.top + b.height / 2)) < 1.5; });
      const p = ps[0], b = p.querySelector(':scope > .box').getBoundingClientRect();
      return { n: ps.length, ok: ok.length, x: b.left + b.width / 2, y: b.top + b.height / 2 }; }""")
    check("W. every unit card's checkbox is a native switch over its tick, 44px (%d of %d)" % (r["ok"], r["n"]), r["n"] >= 4 and r["ok"] == r["n"], r)
    before = pg.evaluate("() => cfg.units.length")
    pg.touchscreen.tap(r["x"], r["y"])
    pg.wait_for_timeout(400)
    after = pg.evaluate("() => cfg.units.length")
    check("W. a tap on the tick's switch picks the unit", after == before + 1, [before, after])
    pg.evaluate("() => showModeSelect()")
    pg.wait_for_timeout(2500)
    m = pg.evaluate("""() => [...document.querySelectorAll('#stage .modecard')].map(c => { const s = c.querySelector(':scope > .nova-hsw'); if(!s) return null;
      const r = s.getBoundingClientRect(), cr = c.getBoundingClientRect(); return { w: Math.round(r.width / cr.width * 100), h: Math.round(r.height), top: Math.round(r.top - cr.top) }; })""")
    check("W. every mode card carries a switch over its head only (%s)" % m, len(m) >= 3 and all(x and x["h"] <= 70 and x["w"] <= 70 and x["top"] <= 2 for x in m), m)
    ctx.close()


def profile_taps(br):
    print("\nX. Profile: only the pills open the screens; the rest open their own cards")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.wait_for_timeout(2500)
    def tap(sel, idx=0):
        pg.evaluate("() => { document.querySelectorAll('.invite-overlay').forEach(o => o.remove()); showProfile('profile'); }")
        pg.wait_for_timeout(1400)
        pg.evaluate(CLEAN)
        r = pg.evaluate("""([s, i]) => { const e = document.querySelectorAll(s)[i]; if(!e) return null; const top = e.getBoundingClientRect().top + scrollY;
          window.scrollTo({ top: top - 300, behavior: 'instant' }); const r = e.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }""", [sel, idx])
        if not r:
            return None
        pg.wait_for_timeout(300)
        pg.touchscreen.tap(r[0], r[1])
        pg.wait_for_timeout(900)
        return pg.evaluate("""() => ({ ranks: !!document.querySelector('#stage .screen-ranks:not(:has(.badges-tab))'), badges: !!document.querySelector('#stage .badges-tab'),
          card: (document.querySelector('.unlock-card') || {}).className || null })""")
    head = tap(".pf-goal .pf-goal-head")
    lid = tap(".pf-case .pf-ccase-lid")
    check("X. a tap on the Next rank card's head or the case's lid opens nothing", head and lid and not head["ranks"] and not head["card"] and not lid["badges"], [head, lid])
    foot = tap(".pf-goal .pf-goal-foot")
    count = tap(".pf-case .pf-case-count")
    check("X. See every rank opens the Rank screen; the case's count opens the Badges page", foot and foot["ranks"] and count and count["badges"], [foot, count])
    task = tap(".pf-goal .pf-task")
    tile = tap(".pf-goal .pf-rw", 1)
    check("X. a challenge row opens it, big, on its card; an unlock tile opens its own card",
          task and "unlock-card-challenge" in (task["card"] or "") and tile and "unlock-card" in (tile["card"] or "") and not tile["ranks"], [task, tile])
    pg.evaluate("() => { document.querySelectorAll('.invite-overlay').forEach(o => o.remove()); showProfile('profile'); window.scrollTo({ top: 0, behavior: 'instant' }); }")
    pg.wait_for_timeout(1400)
    pg.evaluate(CLEAN)
    a = pg.evaluate("() => { const r = document.querySelector('.profile-hero-avatar').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }")
    pg.touchscreen.tap(a[0], a[1])
    pg.wait_for_timeout(150)
    s = pg.evaluate("() => { const e = document.querySelector('.profile-hero-avatar'); return { boop: e.classList.contains('pf-boop'), special: e.classList.contains('char-special') }; }")
    check("X. tapping your character springs it and plays its move", s["boop"] and s["special"], s)
    ctx.close()


def small(br):
    print("\nY. the smaller asks")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.wait_for_timeout(2500)
    r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
      /* answers in two units, enough for the old box to have shown */
      const us = topicsIn(QUESTIONS).slice(0, 2);
      QUESTIONS.forEach((q, i) => { if(us.indexOf((q.topic || '').trim()) >= 0) store.stats[KEYS[i]] = { n: 3, m: 1 }; });
      showProfile('stats'); await wait(800);
      const units = !!document.querySelector('#stage .stx-units') || /Needs work/.test(document.querySelector('#stage .profile-stats-tab').textContent);
      showRankings(); await wait(800);
      const icon = !!document.querySelector('#stage .rank-me-btn svg');
      const need = id => (HUNDO_FX.find(d => d.id === id) || {}).need;
      const veiled = ['astral', 'celestial', 'zenith'].map(id => isVeiledBanner(id));
      const sheriff = CHARACTER_FEATS.novabeat.note;
      showUnlockDetail(characterDetail('poseidon')); await wait(500);
      const d = document.querySelector('.unlock-card .unlock-card-desc'), n = document.querySelector('.unlock-card .unlock-card-note');
      const dc = d && getComputedStyle(d), nc = n && getComputedStyle(n);
      const apart = !!(dc && nc) && parseFloat(dc.fontSize) > parseFloat(nc.fontSize) + 2 && +dc.fontWeight >= 700 && dc.backgroundColor !== 'rgba(0, 0, 0, 0)' && getComputedStyle(d, '::before').content.includes('unlock');
      return { units, icon, ufo: need('ufo'), bubbles: need('bubbles'), veiled, sheriff, apart }; }""")
    check("Y. Stats has no Your units box", r["units"] is False, r["units"])
    check("Y. Find me has no icon", r["icon"] is False, r["icon"])
    check("Y. the UFO takes 200 hundos, Bubbles 150", r["ufo"] == 200 and r["bubbles"] == 150, [r["ufo"], r["bubbles"]])
    check("Y. Astral, Celestial and Zenith are veiled until earned", all(r["veiled"]), r["veiled"])
    check("Y. the Sheriff's note is one plain sentence - no speeds, no modes", r["sheriff"].count(".") == 1 and not __import__("re").search(r"seconds|Battle|Tug|Race", r["sheriff"]), r["sheriff"])
    check("Y. a locked card's requirement is set apart: bigger, bold, in a tray, under 'To unlock'", r["apart"], r["apart"])
    ctx.close()


def board_moves(br):
    print("\nZ. a fresh board's characters move while their sheets are made")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.wait_for_timeout(3000)
    pg.evaluate("() => { caches.keys().then(ks => ks.forEach(k => caches.delete(k))); showRankings(); }")
    pg.wait_for_timeout(3000)
    pg.evaluate("""() => { document.querySelectorAll('#tour-overlay, #tour-tooltip, .daily-alert, .toast').forEach(x => x.remove());
      try{ if(leaderboardLiveUnsub){ leaderboardLiveUnsub(); leaderboardLiveUnsub = null; } }catch(e){}
      const chars = AVATAR_CHARACTERS.filter(c => !c.retired).map(c => c.id), wk = weekKeyNow();
      const ents = Array.from({ length: 22 }, (_, i) => ({ pub: 'zp' + i, firstName: 'Cadet' + i, avatarChar: chars[(i + 3) % chars.length], level: 20 + i, badges: i % 8, hundos: i * 3, correct: 100 + i * 20, week: wk, weekPoints: 1000 - i * 30 }));
      renderRankingRows(document.querySelector('#stage .rank-rows'), ents, RANKING_BOARDS.find(b => b.key === 'overall'), { query: '' }); }""")
    pg.wait_for_timeout(3000)
    r = pg.evaluate("""() => { const vis = [...document.querySelectorAll('#stage .rank-row .rank-avatar-wrap')].filter(w => { const r = w.getBoundingClientRect(); return r.bottom > 0 && r.top < innerHeight; });
      const moving = vis.filter(w => w.querySelector('.char-flip-play') || (w.classList.contains('char-live') && w.querySelector('svg.avatarchar-svg').getAnimations({ subtree: true }).some(a => a.playState === 'running')));
      return { visible: vis.length, moving: moving.length }; }""")
    check("%s: Z. %d of %d characters on screen are moving 3s after a fresh board (6+)" % (label, r["moving"], r["visible"]), r["visible"] >= 6 and r["moving"] >= 6, r)
    ctx.close()


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cb.CHROME)
        for k, fn in (("S", glide), ("T", quick_tap), ("U", build_after), ("V", lists), ("W", picks), ("X", profile_taps), ("Y", small), ("Z", board_moves)):
            if k in ONLY:
                try:
                    fn(br)
                except Exception as e:
                    check("section %s ran" % k, False, repr(e)[:300])
        br.close()
    print("\n%s" % ("ALL PASS" if not cb.FAILURES else "%d FAILED" % len(cb.FAILURES)))
    sys.exit(1 if cb.FAILURES else 0)


if __name__ == "__main__":
    main()
