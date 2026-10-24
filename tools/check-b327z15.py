#!/usr/bin/env python3
"""Build 327z15: the tab bar under fast tapping - every sequence lands.

Madison: "When clicking the button tabs fast sometimes it lags, the bubble
pill lags and the screen lags ... Check all possible sequences and
combinations and make it run so smooth."

Real touches on an iPhone 17 Pro Max (440x956 @3), installed:

  python3 tools/check-b327z15.py
  python3 tools/check-b327z15.py --against /path/to/old/index.html

  F. Every ordered pair and triple of the four tabs (same tab twice too),
     tapped 60, 150 and 300ms apart from Home: when it settles the screen
     up is the LAST tab tapped (read off the highlight, which syncActive
     takes from the screen itself), exactly one tab is lit, the grey
     platter sits under it, the lens is down - and nothing is built that
     need not be: taps closer than the glide build only the last tab,
     and a tab whose screen is already up is never built again (a second
     tap on it scrolls to the top).
  G. The same, with the phone at a quarter speed (a build is then a long
     task the taps land in), for the sequences that went wrong:
     Profile-Home, Home-Profile-Home, Leaderboard-Profile-Calendar-Home.

  Round 2 (the same build):
  H. "coming back; the entire screen is black for a few seconds": a fresh
     start shows NOVA before any script has run - with scripts off, the
     middle of the splash 1.5s in is lit, not the bare background.
  I. "The daily question button ... doesn't feel like it goes with the
     screen": answered, its fill, rim and shadow are the chat button's.
  J. "tapping the back button, it makes it change color": a back button
     held down keeps the colour it had.
  K. The version history: no item title is announced in two versions (the
     per-version fixes line aside), and no exclamation marks.

  Round 3:
  L. Friends from the chat: the chat's button reads differently from "Add"
     (it manages a list that is right there); the Friends screen it opens
     goes back to the chat - its back link is not the screen underneath's
     name, and pressing it leaves the chat open on its Friends tab over
     that screen.
  M. Home's captions: a lit rank flare is one line (no "when you reached");
     a locked one has no numbers in it (no levels, badges or counts to go);
     the planet's says no more than two sentences and no "to go"; the words
     are at least 16px on a phone.

  Round 4:
  N. "The animation of void, when it does the cool effect and finishes it,
     it lags or kinda moves back ... Ensure each character's way of doing
     this is fixed": for every character with a special, the special ends
     within 60ms after the last of its own parts finishes - never before
     (a hold) and never cut short; and on a small tile (a recorded loop)
     the loop keeps running while the special plays (it is hidden, not
     removed), with the live drawing's loops set to the loop's own place.
  O. "Could the secret flares look a little better ... they don't look
     animated except the flashing part. Ensure whatever change you make
     reflects app wide": the orb every secret flare outside Home is drawn
     as has parts that turn; on Home a found flare has a turning part as
     well as its breath and flicker, and one not yet found has motion of
     its own.

  Round 5 (one section per report):
  P. Profile: the level/XP block opens nothing (a tap on it or on the badge
     count stays on Profile); the person card's Progress tiles are under it;
     the challenge rows wear the tiles' surface; the ladder button is not
     "See every rank".
  Q. Challenge cards: the count is centred in its ring (within 2px); a met
     level challenge still shows its How; a rank flare's card draws the
     flare round (its art is as wide as it is tall).
  R. Badges: the blurb does not tell you to clean; a tip sits on a dull
     badge only when one is dull.
  S. A rank's card: it opens on the tap (no wait), its big emblem moves, a
     locked one is darkened without a filter, the bars fill (a transition),
     and a locked rank's flare chip is unlit.
  T. Leaderboard: the hundo count is the same colour as This Week's; Find me
     is a dark button.
  U. Match settings: picking a unit, the button's words stay unlit while its
     fill is still grey (no word lights before the fill).
  V. Calendar: the finals and graduation are one card of pages with a dot per
     page, and a swipe moves it on a page.

  Round 6:
  W. "The toggle switches, they only switch if you tap, they also need to
     work if you swipe": as an iPhone (the native switch over the track), a
     swipe across a Settings switch moves its glass knob with the finger and
     flips it, both ways; a tap still flips it.
  X. Report a bug says where a report goes without "whoever maintains".
"""
import importlib.util
import itertools
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("z5b", os.path.join(HERE, "check-b327z5-b.py"))
z5b = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(z5b)
cb = z5b.cb
check = cb.check
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1")
ONLY = os.environ.get("B327Z15_ONLY", "FGHIJKLMNOPQRSTUVWXY")
TABS = ["home", "profile", "rewards", "calendar"]

STATE = """() => { const bar = document.getElementById('bottomtabs'), sl = document.getElementById('bottomtabs-slider');
  const lit = [...bar.querySelectorAll('.bottomtab.active')];
  let off = null;
  if(lit.length === 1){ const a = lit[0].getBoundingClientRect(), b = sl.getBoundingClientRect();
    off = Math.abs((a.left + a.width / 2) - (b.left + b.width / 2)); }
  const home = !!document.querySelector('#stage .screen-home-actual');
  return { lit: lit.map(b => b.dataset.dest), off, lensUp: bar.classList.contains('lens-up'), builds: bar._navBuilds || 0, home,
           pend: !!bar._navPend }; }"""


def tap(cdp, pt, hold=0.05):
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [pt]})
    time.sleep(hold)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})


def run(pg, cdp, pts, seq, gap):
    """From Home, tap seq with gap ms between presses; return (state, builds)."""
    pg.evaluate("() => { if(!document.querySelector('#stage .screen-home-actual')) showHome(); }")
    pg.wait_for_timeout(700)
    b0 = pg.evaluate(STATE)["builds"]
    for i, d in enumerate(seq):
        t0 = time.time()
        tap(cdp, pts[d])
        if i < len(seq) - 1:
            left = gap / 1000 - (time.time() - t0)
            if left > 0: time.sleep(left)
    pg.wait_for_timeout(1300)
    st = pg.evaluate(STATE)
    return st, st["builds"] - b0


def expect_builds(seq, gap):
    """Taps closer than the glide (290ms) build only the last tab, once,
    and none if it is the screen that was already up (Home, where every
    run starts). Further apart, each tap may build its own tab - but a
    tab whose screen is already up is never built again."""
    if gap < 290:
        return 0 if seq[-1] == "home" else 1
    n, cur = 0, "home"
    for d in seq:
        if d != cur: n += 1
        cur = d
    return n


def sweep(pg, cdp, label, seqs, gaps):
    pts = {d: pg.evaluate("d => { const r = document.querySelector('.bottomtab[data-dest=\"' + d + '\"]').getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; }", d) for d in TABS}
    bad = []
    for gap in gaps:
        for seq in seqs:
            st, nb = run(pg, cdp, pts, seq, gap)
            ok = (st["lit"] == [seq[-1]] and st["off"] is not None and st["off"] < 3 and not st["lensUp"]
                  and not st["pend"] and nb <= expect_builds(seq, gap) and (st["home"] == (seq[-1] == "home")))
            if not ok:
                bad.append((gap, "-".join(seq), st, nb))
    n = len(seqs) * len(gaps)
    check("%s: %d of %d sequences land on the last tab, lit once, platter under it, lens down, nothing extra built"
          % (label, n - len(bad), n), not bad, bad[:6])


def section_f(br):
    print("\nF. every pair and triple, full speed")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.wait_for_timeout(2500)
    cdp = ctx.new_cdp_session(pg)
    seqs = [list(p) for p in itertools.product(TABS, repeat=2) if p[0] != "home" or p[1] != "home"]
    seqs += [list(p) for p in itertools.product(TABS, repeat=3) if p[0] != p[1] and p[1] != p[2]]
    sweep(pg, cdp, label, seqs, (60, 150, 300))
    ctx.close()


def section_g(br):
    print("\nG. the reported runs, at a quarter speed")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.wait_for_timeout(2500)
    cdp = ctx.new_cdp_session(pg)
    # warm every screen once, then throttle
    for d in ("profile", "rewards", "calendar", "home"):
        pg.evaluate("d => document.querySelector('.bottomtab[data-dest=\"' + d + '\"]')._navigate()", d)
        pg.wait_for_timeout(900)
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
    seqs = [["profile", "home"], ["home", "profile", "home"], ["profile", "home", "profile", "home"],
            ["rewards", "profile", "calendar", "home"], ["calendar", "rewards"], ["profile", "calendar", "profile"]]
    sweep(pg, cdp, label + " at 4x CPU", seqs, (120, 250, 400))
    ctx.close()


def section_h(br):
    print("\nH. a fresh start shows NOVA before the app's script runs")
    ctx = br.new_context(viewport={"width": 440, "height": 956}, java_script_enabled=False)
    pg = cb.open_page(ctx)   # serves --against too
    pg.goto(cb.URL)
    pg.wait_for_timeout(1500)
    from PIL import Image
    import io
    im = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
    W, H = im.size
    # the wordmark is a block of bright gradient text in the middle band; a
    # star is a dot - count the bright pixels, not the brightest one
    lit = 0
    for y in range(int(H * .40), int(H * .60)):
        for x in range(int(W * .25), int(W * .75)):
            if max(im.getpixel((x, y))) >= 120: lit += 1
    check("H. NOVA is on the splash with no script (%d lit pixels, needs 300+)" % lit, lit >= 300, lit)
    ctx.close()


def section_i(br):
    print("\nI. answered, the daily button is the chat button's glass")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    r = pg.evaluate("""() => { store.dailyQuestionDate = dailyPeriodKey(); showHome();
      return new Promise(res => setTimeout(() => { const d = document.querySelector('.daily-question-fab'), c = document.querySelector('.chatdock-btn');
        if(!d || !c) return res(null);
        const D = getComputedStyle(d), C = getComputedStyle(c);
        res({ done: d.classList.contains('is-done'), bg: [D.backgroundImage, D.backgroundColor], cbg: [C.backgroundImage, C.backgroundColor],
              rim: D.borderTopColor, crim: C.borderTopColor, sh: D.boxShadow, csh: C.boxShadow }); }, 1200)); }""")
    check("%s: I. the button is up and answered" % label, r and r["done"], r)
    if r:
        check("%s: I. same fill as the chat button" % label, r["bg"] == r["cbg"], r)
        check("%s: I. same rim and shadow" % label, r["rim"] == r["crim"] and r["sh"] == r["csh"], r)
    ctx.close()


def section_j(br):
    print("\nJ. a back button held down keeps its colour")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.evaluate("() => showReleaseHistory()")
    pg.wait_for_timeout(700)
    c = pg.evaluate("() => { const b = document.querySelector('#stage .back-link'); const r = b.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2, bg: getComputedStyle(b).backgroundColor }; }")
    # :active forced on the button itself (a synthetic touch does not hold it)
    cdp = ctx.new_cdp_session(pg)
    cdp.send("DOM.enable"); cdp.send("CSS.enable")
    root = cdp.send("DOM.getDocument")["root"]["nodeId"]
    nid = cdp.send("DOM.querySelector", {"nodeId": root, "selector": "#stage .back-link"})["nodeId"]
    cdp.send("CSS.forcePseudoState", {"nodeId": nid, "forcedPseudoClasses": ["active"]})
    pg.wait_for_timeout(300)
    held = pg.evaluate("() => getComputedStyle(document.querySelector('#stage .back-link')).backgroundColor")
    check("%s: J. held, %s; at rest, %s" % (label, held, c["bg"]), held == c["bg"], (held, c["bg"]))
    ctx.close()


def section_k(br):
    print("\nK. the version history says each thing once")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    r = pg.evaluate("""() => { const seen = {}, dup = [], bang = [];
      RELEASE_NOTES.forEach(v => v.groups.forEach(g => g.items.forEach(it => {
        const k = String(it.title).toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
        if(/^(fixes|performance)/.test(k)) return;
        if(seen[k] && seen[k] !== v.version) dup.push(it.title + ' (' + seen[k] + ', ' + v.version + ')');
        seen[k] = seen[k] || v.version;
        if(/!/.test(it.title + it.body)) bang.push(it.title); })));
      return { dup, bang, n: Object.keys(seen).length }; }""")
    check("K. no title in two versions (%d titles)" % r["n"], not r["dup"], r["dup"][:8])
    check("K. no exclamation marks", not r["bang"], r["bang"][:8])
    ctx.close()


def section_l(br):
    print("\nL. Friends from the chat goes back to the chat")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.evaluate("() => { chatDockTab = 'friends'; openChatDock(); }")
    pg.wait_for_timeout(900)
    btn = pg.evaluate("() => document.querySelector('.chatdock-friendsbar-btn')?.textContent || null")
    check("%s: L. the chat's Friends button is not 'Add friends' (%s)" % (label, btn), btn and not btn.lower().startswith("add"), btn)
    pg.evaluate("() => document.querySelector('.chatdock-friendsbar-btn').click()")
    pg.wait_for_timeout(1000)
    back = pg.evaluate("() => document.querySelector('#stage .screen-friends .back-link')?.textContent || null")
    check("%s: L. the Friends screen's back link is not the Home screen's name (%s)" % (label, back), back and back.strip().lower() != "home", back)
    pg.evaluate("() => document.querySelector('#stage .screen-friends .back-link').click()")
    pg.wait_for_timeout(1200)
    st = pg.evaluate("() => ({ open: chatDockOpen, tab: chatDockTab, home: !!document.querySelector('#stage .screen-home-actual') })")
    check("%s: L. back: Home underneath, the chat open on Friends" % label, st["open"] and st["tab"] == "friends" and st["home"], st)
    ctx.close()


def section_m(br):
    print("\nM. Home's captions: short, plain, bigger")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    r = pg.evaluate("""() => { const out = {};
      // a held rank, whatever the account: every rank lit, for this read only
      const orig = window.tierColorUnlocked; let held;
      try{ window.tierColorUnlocked = () => true; held = homeTapCopyRank(TIER_ORDER_FULL[0]); }catch(e){}
      window.tierColorUnlocked = orig;
      out.heldParts = held && held.kind === 'held' ? held.parts.filter(Boolean).length : null;
      out.heldText = held ? held.parts.join(' ') : '';
      const lockedTier = TIER_ORDER_FULL.slice().reverse().find(t => !tierColorUnlocked(t));
      const locked = lockedTier ? homeTapCopyRank(lockedTier) : null;
      out.locked = locked ? locked.parts.join(' ') : null;
      const planet = homeTapCopyPlanet();
      out.planet = planet.parts.join(' ');
      const p = document.querySelector('.panel.home.screen-home-actual');
      homeCaptionShow(p, planet, 'm');
      return new Promise(res => setTimeout(() => { const tx = document.querySelector('.hc-item .hc-text');
        out.px = tx ? parseFloat(getComputedStyle(tx).fontSize) : 0; res(out); }, 500)); }""")
    if True:
        check("%s: M. a lit flare says only what it is (%r)" % (label, r["heldText"]), r["heldParts"] == 1 and "reached" not in r["heldText"], r)
    check("%s: M. a locked flare has no numbers (%r)" % (label, r["locked"]), r["locked"] is not None and not any(ch.isdigit() for ch in r["locked"]), r)
    sentences = [x for x in r["planet"].replace("!", ".").split(".") if x.strip()]
    check("%s: M. the planet's is two sentences at most, no 'to go' (%r)" % (label, r["planet"]), len(sentences) <= 2 and "to go" not in r["planet"], r)
    check("%s: M. caption words are 16px or more (%.1f)" % (label, r["px"]), r["px"] >= 16, r)
    ctx.close()


def section_n(br):
    print("\nN. a special ends when its move ends; a small tile's loop keeps its clock")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    r = pg.evaluate("""async () => {
      const bad = [], ok = [];
      for(const c of AVATAR_CHARACTERS.filter(c => !c.retired)){
        const el = document.createElement('div'); el.className = 'profile-hero-avatar __n';
        el.style.cssText = 'position:fixed;left:0;top:0;width:160px;height:160px';
        let svg; try{ svg = buildAvatarCharSVGSafe(c.id); }catch(e){ continue; }
        el.appendChild(svg); document.body.appendChild(el); el.classList.add('char-live');
        await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
        if(!charHasSpecial(el)){ el.remove(); continue; }
        const before = new Set(svg.getAnimations({ subtree: true }));
        charSpecialBusyUntil = 0;
        const t0 = Date.now();
        playCharSpecial(el);
        const planned = charSpecialBusyUntil - 400 - t0;
        let end = 0;
        svg.getAnimations({ subtree: true }).forEach(a => { if(before.has(a)) return; const e = a.effect.getComputedTiming().endTime; if(isFinite(e)) end = Math.max(end, e); });
        (planned >= end - 5 && planned <= end + 60 ? ok : bad).push(c.id + ' ' + Math.round(planned) + '/' + Math.round(end));
        el.__charSpecial = null; el.classList.remove('char-special'); el.remove();
      }
      return { bad, n: ok.length + bad.length }; }""")
    check("%s: N. all %d specials end with their own last part (no hold, no cut)" % (label, r["n"]), not r["bad"] and r["n"] >= 10, r["bad"][:10])
    r = pg.evaluate("""async () => {
      const el = document.createElement('div'); el.className = 'profile-hero-avatar __n';
      el.style.cssText = 'position:fixed;left:20px;top:20px;width:56px;height:56px';
      el.appendChild(buildAvatarCharSVGSafe('voidwalker')); document.body.appendChild(el);
      setCharState(el, 'live', { solo: true });
      for(let i = 0; i < 160 && !el.querySelector('.char-flip-play img'); i++) await new Promise(r => setTimeout(r, 250));
      const img = el.querySelector('.char-flip-play img');
      if(!img) return { sheet: false };
      await new Promise(r => setTimeout(r, 600));
      charSpecialBusyUntil = 0; playCharSpecial(el);
      await new Promise(r => setTimeout(r, 400));
      const running = img.getAnimations().filter(a => a.playState === 'running').length;
      // each looping part of the live drawing at the loop's own place
      const L = CHAR_ANIM_LOOP_MS, tau = ((Date.now() + Number(el.dataset.flipPhase || 0)) % L + L) % L;
      let off = 0, n = 0;
      el.querySelector('svg.avatarchar-svg').getAnimations({ subtree: true }).forEach(a => {
        const t = a.effect.getTiming(); if(isFinite(Number(t.iterations))) return;
        const P = (Number(t.duration) || 1000) * (String(t.direction || '').indexOf('alternate') >= 0 ? 2 : 1);
        const turn = /^cx-spin/.test(a.animationName || ''); const c = P > (turn ? 3.5 : 2.5) * L ? 0 : Math.max(1, Math.round(L / P));
        if(!c) return;
        const want = (tau * c * P / L) % P, got = (Number(a.currentTime) || 0) % P;
        off = Math.max(off, Math.min(Math.abs(want - got), P - Math.abs(want - got))); n++;
      });
      return { sheet: true, running, off: Math.round(off), n }; }""")
    if r.get("sheet"):
        check("%s: N. the tile's loop keeps running under the special (%d)" % (label, r["running"]), r["running"] >= 1, r)
        check("%s: N. the live drawing's %d loops are within 80ms of the loop's place (worst %dms)" % (label, r["n"], r["off"]), r["n"] >= 1 and r["off"] <= 80, r)
    else:
        check("%s: N. a small tile got its recorded loop" % label, False, r)
    ctx.close()


def section_o(br):
    print("\nO. secret flares move, everywhere")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    r = pg.evaluate("""async () => {
      const box = document.createElement('div'); box.style.cssText = 'position:fixed;left:0;top:0;width:90px;height:90px';
      const orb = buildFlareOrb(MYSTERY_COLOR.red, 'gate'); orb.style.width = orb.style.height = '90px';
      box.appendChild(orb); document.body.appendChild(box);
      await new Promise(r => setTimeout(r, 300));
      const turns = a => /rotate|turn|spin/.test(a.animationName || '') || /rotate/.test(JSON.stringify(a.effect.getKeyframes()));
      const oa = orb.getAnimations({ subtree: true });
      store.mysteryColorsFound = { red: true }; showHome();
      await new Promise(r => setTimeout(r, 1500));
      const found = document.querySelector('.cosmic-flare-dot.is-found');
      const missing = document.querySelector('.cosmic-flare-dot:not(.is-found):not(.is-next)');
      const fa = found ? found.getAnimations({ subtree: true }) : [];
      const ma = missing ? missing.getAnimations({ subtree: true }) : [];
      return { orb: oa.length, orbTurn: oa.filter(turns).length, found: !!found, foundN: fa.length, foundTurn: fa.filter(turns).length,
               missing: !!missing, missingN: ma.length }; }""")
    check("%s: O. the orb (tests, banner, cutscenes, cards) has turning parts (%d of %d)" % (label, r["orbTurn"], r["orb"]), r["orbTurn"] >= 1, r)
    check("%s: O. a found flare on Home has a turning part" % label, r["found"] and r["foundTurn"] >= 1, r)
    if r["missing"]:
        check("%s: O. one not found yet moves too (%d)" % (label, r["missingN"]), r["missingN"] >= 1, r)
    ctx.close()


def section_p(br):
    print("\nP. Profile: read, not pressed; the Progress tiles")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    r = pg.evaluate("""async () => { showProfile('profile'); await new Promise(r => setTimeout(r, 900));
      document.querySelectorAll('#tour-overlay, #tour-tooltip').forEach(n => n.remove());
      const st = document.querySelector('#stage .pf-standing');
      const was = !!document.querySelector('#stage .screen-profile');
      st && st.click(); await new Promise(r => setTimeout(r, 500));
      const after1 = !!document.querySelector('#stage .screen-profile');
      const bc = document.querySelector('#stage .pf-badgecount, #stage .pf-standing .pf-xpnums');
      bc && bc.click(); await new Promise(r => setTimeout(r, 500));
      const after2 = !!document.querySelector('#stage .screen-profile');
      const cells = document.querySelectorAll('#stage .profile-hero .person-card-cell').length;
      const cell = document.querySelector('#stage .profile-hero .person-card-cell'), row = document.querySelector('#stage .pf-goal .pf-task');
      const bg = e => e ? getComputedStyle(e).backgroundColor + '|' + getComputedStyle(e).borderTopLeftRadius : null;
      const foot = (document.querySelector('#stage .pf-goal-foot') || {}).textContent || '';
      return { was, after1, after2, isButton: st ? st.tagName === 'BUTTON' : null, cells, cellBg: bg(cell), rowBg: bg(row), foot }; }""")
    check("%s: P. the level block is not a button and a tap on it stays on Profile" % label, r["was"] and r["after1"] and r["isButton"] is False, r)
    check("%s: P. a tap on its numbers stays on Profile" % label, r["after2"], r)
    check("%s: P. four Progress tiles under it" % label, r["cells"] == 4, r)
    check("%s: P. the challenge rows wear the tiles' surface" % label, r["rowBg"] is not None and r["rowBg"] == r["cellBg"], r)
    check("%s: P. the ladder button is renamed (%s)" % (label, r["foot"].strip()), r["foot"].strip() and r["foot"].strip() != "See every rank", r)
    ctx.close()


def section_q(br):
    print("\nQ. challenge cards and the flare card")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    r = pg.evaluate("""async () => { const out = {};
      const open = async o => { document.querySelectorAll('.invite-overlay').forEach(n => n.remove()); showUnlockDetail(o); await new Promise(r => setTimeout(r, 700)); };
      await open(rankChallengeDetail({ kind: 'badges', label: 'Earn 5 badges', now: 5, need: 5, met: true }, '#E3C77A', 'Gold'));
      const ring = document.querySelector('.unlock-card-art .unlock-card-ring'), b = document.querySelector('.unlock-card-chnum b');
      if(ring && b){ const R = ring.getBoundingClientRect(), B = b.getBoundingClientRect(); out.dy = Math.abs((R.top + R.height / 2) - (B.top + B.height / 2)); out.dx = Math.abs((R.left + R.width / 2) - (B.left + B.width / 2)); }
      await open(rankChallengeDetail({ kind: 'level', label: 'Reach Level 21', now: 21, need: 21, met: true }, '#6FC2FF', 'Gold'));
      const d = document.querySelector('.unlock-card .unlock-card-desc');
      out.levelHow = d ? { shown: getComputedStyle(d).display !== 'none' && d.getBoundingClientRect().height > 20, tray: getComputedStyle(d).backgroundColor, text: d.textContent } : null;
      await open(rankFlareDetail('veteran'));
      const a = document.querySelector('.unlock-card-rankflare .unlock-card-art > *');
      if(a){ const A = a.getBoundingClientRect(); out.flare = [Math.round(A.width), Math.round(A.height)]; }
      return out; }""")
    check("%s: Q. the count is centred in its ring (%.1f, %.1f px off)" % (label, r.get("dy", 99), r.get("dx", 99)), r.get("dy", 99) <= 2 and r.get("dx", 99) <= 2, r)
    lh = r.get("levelHow") or {}
    check("%s: Q. a met level challenge still shows its How, in a tray" % label, lh.get("shown") and lh.get("tray") not in (None, "rgba(0, 0, 0, 0)"), lh)
    f = r.get("flare") or [0, 1]
    check("%s: Q. the flare card's flare is round (%s)" % (label, f), f[0] > 40 and abs(f[0] - f[1]) <= 2, r)
    ctx.close()


def section_r(br):
    print("\nR. Badges: a tip on a dull badge, only then")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    r = pg.evaluate("""async () => { const units = topicsIn(QUESTIONS); window.unitBadgeEarned = u => units.indexOf(u) < 4;
      const clean = () => { store.badgeCleanedAt = {}; units.forEach(u => store.badgeCleanedAt[u] = Date.now() - 1000); };
      clean(); showRanksScreen('badges'); await new Promise(r => setTimeout(r, 900));
      const blurb = (document.querySelector('#stage .badges-blurb') || {}).textContent || '';
      const tipClean = document.querySelectorAll('#stage .badge-clean-tip').length;
      clean(); store.badgeCleanedAt[units[1]] = Date.now() - 3 * BADGE_DIRT_WEEK_MS - 1000;
      showRanksScreen('badges'); await new Promise(r => setTimeout(r, 900));
      const tips = [...document.querySelectorAll('#stage .badge-clean-tip')];
      return { blurb, tipClean, tipDirty: tips.length, onDirty: tips.length ? !!tips[0].closest('.badge-tile[data-dirt]') : null }; }""")
    check("R. the blurb does not tell you to clean (%r)" % r["blurb"][:60], not any(w in r["blurb"].lower() for w in ("rub", "clean")), r)
    check("R. no tip while every badge shines", r["tipClean"] == 0, r)
    check("R. one tip, on the dull badge, once one is dull", r["tipDirty"] == 1 and r["onDirty"], r)
    ctx.close()


def section_s(br):
    print("\nS. a rank's card")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    r = pg.evaluate("""async () => { showRanksScreen('ranks'); await new Promise(r => setTimeout(r, 1500));
      document.querySelectorAll('#tour-overlay, #tour-tooltip').forEach(n => n.remove());
      const held = rankOf(store), hi = held ? TIER_ORDER_FULL.indexOf(held) : -1;
      const lockedKey = TIER_ORDER_FULL[Math.min(TIER_ORDER_FULL.length - 1, hi + 2)];
      const node = [...document.querySelectorAll('#stage .rankmap-node')][TIER_ORDER_FULL.indexOf(lockedKey)];
      const t0 = performance.now(); node.click();
      await new Promise(r => setTimeout(r, 40));
      const fast = !!document.querySelector('.ranklore-card');
      await new Promise(r => setTimeout(r, 900));
      const svg = document.querySelector('.ranklore-art svg');
      const running = svg ? svg.getAnimations({ subtree: true }).filter(a => a.playState === 'running').length : 0;
      const card = document.querySelector('.ranklore-card');
      const fill = document.querySelector('.ranklore-reqfill');
      const chip = document.querySelector('.ranklore-card .rankmap-giftbubble .flare-solo');
      return { fast, running, locked: card && card.classList.contains('is-locked'), filter: svg ? getComputedStyle(svg).filter : null,
               fillDur: fill ? parseFloat(getComputedStyle(fill).transitionDuration) : 0, chipLit: chip ? chip.classList.contains('cosmic-badge-lit') : null }; }""")
    check("%s: S. the card is up 40ms after the tap" % label, r["fast"], r)
    check("%s: S. its big emblem moves (%d)" % (label, r["running"]), r["running"] >= 1, r)
    check("%s: S. a locked rank's emblem is darkened without a filter" % label, r["locked"] and r["filter"] == "none", r)
    check("%s: S. its bars fill (a transition)" % label, r["fillDur"] >= .3, r)
    check("%s: S. a locked rank's flare chip is unlit" % label, r["chipLit"] is False, r)
    ctx.close()


def section_t(br):
    print("\nT. Leaderboard: hundos white, Find me dark")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    r = pg.evaluate("""async () => { showRankings(); await new Promise(r => setTimeout(r, 1200));
      const go = async t => { const b = [...document.querySelectorAll('#stage button, #stage [role=tab]')].find(x => new RegExp(t, 'i').test(x.textContent)); b && b.click(); await new Promise(r => setTimeout(r, 900)); };
      await go('week'); const wk = document.querySelector('#stage .rank-row:not(.rank-row-head) .rank-col-xp');
      const wc = wk ? getComputedStyle(wk).color : null;
      await go('hundo'); const hd = document.querySelector('#stage .rank-row:not(.rank-row-head) .rank-col-hundo');
      const hc = hd ? getComputedStyle(hd).color : null;
      const me = document.querySelector('#stage .rank-me-btn');
      const bg = me ? getComputedStyle(me).backgroundColor : null;
      return { wc, hc, bg }; }""")
    check("%s: T. the hundo count is This Week's colour (%s / %s)" % (label, r["hc"], r["wc"]), r["hc"] and r["hc"] == r["wc"], r)
    import re as _re
    m = _re.findall(r"[\d.]+", r["bg"] or "")
    lum = sum(float(x) for x in m[:3]) / 3 if len(m) >= 3 else 255
    alpha = float(m[3]) if len(m) >= 4 else 1
    check("%s: T. Find me is a dark, solid button (%s)" % (label, r["bg"]), lum < 30 and alpha > .9, r)
    ctx.close()


def section_u(br):
    print("\nU. Match settings: the words wait for the fill")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.evaluate("() => { showVirtualRoomSetup(); document.querySelectorAll('#tour-overlay, #tour-tooltip').forEach(n => n.remove()); }")
    pg.wait_for_timeout(1500)
    c = pg.evaluate("() => { const p = document.querySelector('#stage .pick'); p.scrollIntoView({ block: 'center', behavior: 'instant' }); const r = p.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; }")
    pg.evaluate("""() => { window.__s = []; const b = document.querySelector('#stage .vroom-setup-go'); let t0 = 0;
      const f = () => { const cs = getComputedStyle(b); window.__s.push([performance.now() - t0, cs.color, cs.backgroundColor]); if(performance.now() - t0 < 700) requestAnimationFrame(f); };
      window.__go = () => { t0 = performance.now(); requestAnimationFrame(f); }; }""")
    pg.evaluate("() => window.__go()")
    pg.mouse.click(c["x"], c["y"])
    pg.wait_for_timeout(900)
    s = pg.evaluate("() => window.__s")
    import re as _re
    def lum(v):
        m = _re.findall(r"[\d.]+", v)
        a = float(m[3]) if len(m) >= 4 else 1
        return sum(float(x) for x in m[:3]) / 3 * a
    first = s[1] if len(s) > 1 else None
    bad = [x for x in s if lum(x[2]) < 120 and lum(x[1]) < 90]   # dark words on a fill that is not lit yet
    lit_end = s[-1] if s else None
    check("%s: U. no frame has dark words on the unlit fill (%d of %d)" % (label, len(bad), len(s)), not bad and len(s) > 10, (first, bad[:3]))
    check("%s: U. it ends lit: the light fill under dark words" % label, lit_end and lum(lit_end[2]) > 180 and lum(lit_end[1]) < 90, lit_end)
    check("%s: U. the unlit fill is seen at all (it was white from the first frame)" % label, any(lum(x[2]) < 120 for x in s), s[:3])
    ctx.close()


def section_v(br):
    print("\nV. Calendar: one card of pages")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.evaluate("() => { showCalendarTab(); document.querySelectorAll('#tour-overlay, #tour-tooltip').forEach(n => n.remove()); }")
    pg.wait_for_timeout(1300)
    r = pg.evaluate("""() => { const tab = document.querySelector('#stage .screen-calendar-tab');
      const cards = [...tab.querySelectorAll(':scope > .cal-card, :scope > section')].filter(c => c.offsetHeight > 0);
      const track = tab.querySelector('.cal-count-track'), dots = tab.querySelectorAll('.cal-count-dots > i');
      const pages = track ? [...track.children] : [];
      if(track) track.scrollIntoView({ block: 'center', behavior: 'instant' });
      const R = track ? track.getBoundingClientRect() : null;
      return { pages: pages.length, dots: dots.length, separateBig: !!tab.querySelector(':scope > .cal-big-card:not([hidden])'), separateCourse: !!tab.querySelector(':scope > .cal-course-card:not([hidden])'),
               box: R ? { y: R.top + R.height / 2 } : null, onDot: [...dots].findIndex(d => d.classList.contains('is-on')) }; }""")
    check("%s: V. the finals and graduation are pages of one card (%d pages, %d dots)" % (label, r["pages"], r["dots"]),
          r["pages"] >= 2 and r["dots"] == r["pages"] and not r["separateBig"] and not r["separateCourse"], r)
    if r["box"]:
        cdp = ctx.new_cdp_session(pg)
        y = r["box"]["y"]
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": 360, "y": y}]})
        for i in range(1, 11):
            cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": 360 - i * 26, "y": y}]})
            pg.wait_for_timeout(16)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        pg.wait_for_timeout(900)
        on = pg.evaluate("() => [...document.querySelectorAll('#stage .cal-count-dots > i')].findIndex(d => d.classList.contains('is-on'))")
        check("%s: V. a swipe moves it one page (dot %d -> %d)" % (label, r["onDot"], on), r["onDot"] == 0 and on == 1, (r["onDot"], on))
    ctx.close()


def section_w(br):
    print("\nW. switches follow a swipe (as an iPhone)")
    ctx = br.new_context(viewport={"width": 440, "height": 956}, has_touch=True, is_mobile=True, device_scale_factor=2, user_agent=UA)
    ctx.add_init_script(z5b.STANDALONE)
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.drill.v1', '%s');localStorage.setItem('class26e.weekrecap.v1','9999-12-31');}catch(e){}" % cb.USED_ACCOUNT)
    pg = cb.open_page(ctx)
    pg.goto(cb.URL)
    pg.wait_for_timeout(2600)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __stub();}")
    pg.wait_for_timeout(2500)
    pg.evaluate("() => { showAppearance(); document.querySelectorAll('#tour-overlay, #tour-tooltip').forEach(n => n.remove()); }")
    pg.wait_for_timeout(1200)
    ROW = "() => [...document.querySelectorAll('#stage .opt')].filter(r => r.querySelector(':scope > .box') && r.offsetHeight && !/Reduce motion/.test(r.textContent))[0]"
    info = pg.evaluate("() => { const row = (" + ROW + ")(); row.scrollIntoView({ block: 'center', behavior: 'instant' }); const b = row.querySelector(':scope > .box').getBoundingClientRect(); const cb = row.querySelector(':scope > input'); return { x0: b.left + b.height / 2, x1: b.right - b.height / 2, y: b.top + b.height / 2, native: cb.classList.contains('hsw-opt') }; }")
    state = lambda: pg.evaluate("() => (" + ROW + ")().querySelector(':scope > input').checked")
    cdp = ctx.new_cdp_session(pg)
    def swipe(xa, xb):
        y = info["y"]
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": xa, "y": y}]})
        pg.wait_for_timeout(40)
        for i in range(1, 13):
            cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": xa + (xb - xa) * i / 12, "y": y}]})
            pg.wait_for_timeout(16)
        lx = pg.evaluate("() => { const l = document.querySelector('.nsw-lens'); return l ? new DOMMatrixReadOnly(getComputedStyle(l).transform).m41 : null; }")
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        pg.wait_for_timeout(800)
        return lx
    check("W. the switch has the iPhone's native switch over it", info["native"], info)
    a = state()
    l1 = swipe(info["x1"], info["x0"]) if a else swipe(info["x0"], info["x1"])
    b = state()
    l2 = swipe(info["x1"], info["x0"]) if b else swipe(info["x0"], info["x1"])
    c = state()
    check("W. a swipe flips it, and a swipe back flips it back (%s -> %s -> %s)" % (a, b, c), a != b and b != c, (a, b, c))
    check("W. the glass knob is under the finger mid-swipe (%s, %s)" % (l1, l2), l1 is not None and l2 is not None and abs((l1 or 0) - (l2 or 0)) > 12, (l1, l2))
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": info["x0"] + 8, "y": info["y"]}]})
    pg.wait_for_timeout(60)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    pg.wait_for_timeout(800)
    d = state()
    check("W. a tap still flips it (%s -> %s)" % (c, d), d != c, (c, d))
    ctx.close()


def section_x(br):
    print("\nX. Report a bug says where it goes")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    t = pg.evaluate("() => { try{ showBugReport(); }catch(e){ try{ showReportBug(); }catch(e2){} } return document.querySelector('#stage') ? document.querySelector('#stage').textContent : ''; }")
    check("X. no 'whoever maintains' on Report a bug", "whoever maintains" not in t and "Nova admin" in t, t[:200])
    ctx.close()


def section_y(br):
    print("\nY. The Profile tour for a new account: a handful of steps, each on something showing")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.evaluate("() => { store.seenProfileTour = false; store.profileTips289 = false; showProfile(); }")
    pg.wait_for_timeout(2500)
    seen, off = [], []
    for _ in range(14):
        st = pg.evaluate("""() => { const t = document.getElementById('tour-tooltip'); if(!t) return null;
          const r = t.getBoundingClientRect(); return { text: t.textContent.slice(0, 80), w: r.width, h: r.height }; }""")
        if not st:
            break
        if not seen or seen[-1] != st["text"]:
            seen.append(st["text"])
            if not (st["w"] > 0 and st["h"] > 0):
                off.append(st["text"])
        pg.evaluate("() => document.getElementById('tour-next') && document.getElementById('tour-next').click()")
        pg.wait_for_timeout(700)
    check("Y. the Profile tour is a few steps, not a lecture (%d)" % len(seen), 3 <= len(seen) <= 6, seen)
    check("Y. every step shows", not off, off)
    ctx.close()


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cb.CHROME)
        for k, fn in (("F", section_f), ("G", section_g), ("H", section_h), ("I", section_i), ("J", section_j), ("K", section_k), ("L", section_l), ("M", section_m), ("N", section_n), ("O", section_o), ("P", section_p), ("Q", section_q), ("R", section_r), ("S", section_s), ("T", section_t), ("U", section_u), ("V", section_v), ("W", section_w), ("X", section_x), ("Y", section_y)):
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
