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

ONLY = os.environ.get("B327Z15_ONLY", "FGHIJKLM")
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


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cb.CHROME)
        for k, fn in (("F", section_f), ("G", section_g), ("H", section_h), ("I", section_i), ("J", section_j), ("K", section_k), ("L", section_l), ("M", section_m)):
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
