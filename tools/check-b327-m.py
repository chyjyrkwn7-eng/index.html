#!/usr/bin/env python3
"""Build 327 (b327m): a shorter meeting with Nova, What's New on Home.

Madison (Oct 20): "I think the nova intro may be a little drawn out. I feel
like we could cut that down just a little cause it has the intro, the what's
new new stuff, and the home main menu walk through. The what's new stuff,
make it just show on the main menu like how we have done it before, and then
the walkthrough. So the nova instructor won't go through what's new one by
one. It's too much I think."

  m1. an existing account that has not met him: the signal, his talk (ending
      in his goodbye - 'I'll speak with you again'), then the What's New CARD
      on Home with every row at once (no Nova, no typing), Got it, then the
      tips, then nothing more of his; once only; met recorded.
  m2. an account that has met him: the card alone, not narrated; Got it ends
      it with no tips; once.
  m3. the level-wall note is a box on the card when it applies, not otherwise.
  m4. a new account: his introduction then the main menu's tips, no What's New,
      and the introduction a little shorter (at most 14 lines).
  m5. the card on both reference devices: on screen, Got it reachable.

  python3 tools/check-b327-m.py
  python3 tools/check-b327-m.py --against /path/to/e5d3143/index.html

Every section fails on e5d3143 (narrated What's New, a separate goodbye).
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py"))
cb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cb)
from playwright.sync_api import sync_playwright

check, booted, USED_ACCOUNT = cb.check, cb.booted, cb.USED_ACCOUNT
DEVS = ((440, 956, "17 Pro Max"), (834, 1194, "iPad Pro 11"))

SETUP_EXISTING = """() => { store.rankUpShown = TIER_ORDER_FULL.length; delete store.novaMet; saveStore();
  localStorage.removeItem('class26e.intro.seen');
  window.__seen = []; new MutationObserver(() => { ['nova-intro', 'intro-pop', 'tour-tooltip'].forEach(id => {
    const e = document.getElementById(id); if(e && !e.__m){ e.__m = 1; window.__seen.push(id); } }); })
    .observe(document.body, { childList: true });
  showHome(); }"""

# Click through one of his dialogues, line by line; returns what he said.
TALK = r"""async (id) => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  for(let i = 0; i < 80 && !document.getElementById(id); i++) await wait(100);
  const el = document.getElementById(id);
  if(!el || !el.__nova) return { open: !!el, nova: false, lines: [] };
  const nv = el.__nova, out = { open: true, nova: true, lines: [] };
  for(let i = 0; i < 60 && nv.index < 0; i++) await wait(100);
  for(let i = 0; i < 200 && el.isConnected; i++){
    const t = el.querySelector('.nt-text').textContent;
    if(out.lines[out.lines.length - 1] !== t) out.lines.push(t);
    if(nv.typing){ el.querySelector('.nt-stage').click(); await wait(30); continue; }
    const go = el.querySelector('.nt-go');
    if(go && getComputedStyle(go).display !== 'none'){ out.go = go.textContent; go.click(); break; }
    el.querySelector('.nt-stage').click(); await wait(40);
  }
  return out;
}"""

CARD = r"""async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  for(let i = 0; i < 80 && !document.getElementById('intro-pop'); i++) await wait(100);
  const el = document.getElementById('intro-pop');
  if(!el) return { open: false };
  /* at once: read in the same moment it is seen */
  const rows0 = el.querySelectorAll('.intro-row').length;
  await wait(500);
  const want = WHATS_NEW_320.map(x => x.title);
  const titles = [...el.querySelectorAll('.intro-row .intro-row-title')].map(t => t.textContent);
  const go = el.querySelector('.intro-go');
  const card = el.querySelector('.intro-card');
  const out = { open: true, rows0, titles, want,
    narrated: !!el.__nova || !!el.querySelector('.nt-text, .nova-svg, .nt-nova'),
    onHome: !!document.querySelector('#stage [data-screen="home"]'),
    eyebrow: (el.querySelector('.intro-eyebrow') || {}).textContent || '',
    note: !!el.querySelector('.intro-gate-note'), go: go ? go.textContent : null,
    card: !!card, novaUp: !!document.getElementById('nova-intro') };
  if(go){ go.scrollIntoView({ block: 'nearest' }); await wait(150);
    const r = go.getBoundingClientRect(); out.goInView = r.top >= 0 && r.bottom <= innerHeight + 1 && r.width > 100;
    if(card){ const c = card.getBoundingClientRect(); out.cardInView = c.left >= -1 && c.right <= innerWidth + 1; } }
  return out;
}"""

TOUR = """async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  for(let i = 0; i < 50 && !document.getElementById('tour-tooltip'); i++) await wait(100);
  await wait(300);
  const out = [];
  for(let i = 0; i < 20; i++){
    const tt = document.getElementById('tour-tooltip');
    if(!tt) break;
    out.push((document.getElementById('tour-text') || {}).textContent || '');
    document.getElementById('tour-next').click(); await wait(450);
  }
  return out;
}"""

AFTER = """async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
  await wait(1500);
  const n0 = window.__seen.length;
  const after = { novaAgain: !!document.getElementById('nova-intro'), card: !!document.getElementById('intro-pop'),
                  met: store.novaMet, local: Number(localStorage.getItem('class26e.intro.seen')) >= INTRO_REV };
  showProfile('profile'); await wait(400); showHome(); await wait(3600);
  after.more = window.__seen.slice(n0);
  after.seen = window.__seen.slice();
  return after; }"""


def click_go(pg):
    pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
      const b = document.querySelector('#intro-pop .intro-go'); if(b) b.click(); await wait(500); }""")


def m1(br):
    print("\nm1. an existing account meets him: signal, his talk ending in goodbye, the What's New card on Home, the tips")
    for (w, h, dev) in DEVS:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        pg.evaluate(SETUP_EXISTING)
        talk = pg.evaluate(TALK, "nova-intro")
        last = (talk.get("lines") or [""])[-1]
        check("%s his talk opens first and its last line is his goodbye ('I'll speak with you again'), button Goodbye" % dev,
              talk.get("open") and talk.get("nova") and "speak with you again" in last and talk.get("go") == "Goodbye",
              {"last": last[:120], "go": talk.get("go"), "n": len(talk.get("lines") or [])})
        card = pg.evaluate(CARD)
        check("%s then the What's New card on Home - not narrated, every row there at once" % dev,
              card.get("open") and not card.get("narrated") and card.get("onHome") and not card.get("novaUp")
              and card.get("rows0") == len(card.get("want") or []) and card.get("titles") == card.get("want")
              and "version" in (card.get("eyebrow") or "").lower() and card.get("go") == "Got it",
              {k: card.get(k) for k in ("open", "narrated", "onHome", "rows0", "titles", "go", "novaUp")})
        click_go(pg)
        tips = pg.evaluate(TOUR)
        want = pg.evaluate("() => NOVA_NEW_TIPS_321.length")
        gone = pg.evaluate("() => !document.getElementById('intro-pop')")
        check("%s Got it closes the card and the tips follow (%d)" % (dev, want), gone and len(tips) == want and want >= 1, {"tips": [t[:40] for t in tips]})
        after = pg.evaluate(AFTER)
        order = [x for x in after.get("seen") or []]
        check("%s nothing of his after the tips - no second Nova overlay, no goodbye" % dev,
              not after.get("novaAgain") and order[:3] == ["nova-intro", "intro-pop", "tour-tooltip"] and order.count("nova-intro") == 1,
              order)
        check("%s once: met recorded on the account and the card seen on the device, nothing on the next Home" % dev,
              after.get("met") == 1 and after.get("local") and not after.get("more") and not after.get("card"), after)
        ctx.close()


def m2(br):
    print("\nm2. an account that has met him: just the card")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    pg.evaluate("""() => { store.rankUpShown = TIER_ORDER_FULL.length; store.novaMet = 1; saveStore(); localStorage.removeItem('class26e.intro.seen');
      window.__seen = []; new MutationObserver(() => { ['nova-intro', 'intro-pop', 'tour-tooltip'].forEach(id => {
        const e = document.getElementById(id); if(e && !e.__m){ e.__m = 1; window.__seen.push(id); } }); })
        .observe(document.body, { childList: true });
      showHome(); }""")
    card = pg.evaluate(CARD)
    check("the card, not narrated, with every row", card.get("open") and not card.get("narrated") and card.get("titles") == card.get("want"),
          {k: card.get(k) for k in ("open", "narrated", "titles")})
    click_go(pg)
    after = pg.evaluate(AFTER)
    check("Got it ends it: no Nova, no tips, seen once and not again",
          "nova-intro" not in (after.get("seen") or []) and "tour-tooltip" not in (after.get("seen") or []) and after.get("local") and not after.get("more"),
          after)
    ctx.close()


def m3(br):
    print("\nm3. the level-wall note is a box on the card when it applies")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      const U = topicsIn(QUESTIONS); store.unitPerfects = {}; store.levelFloor = 0; store.rankFloor = 0; store.levelWallRule = 325;
      store.lifetime.points = xpForLevel(35) + 10; saveStore();
      showIntroPopup(); await wait(300);
      out.held = !!document.querySelector('#intro-pop .intro-gate-note');
      out.text = (document.querySelector('#intro-pop .intro-gate-note') || {}).textContent || '';
      document.getElementById('intro-pop')?.remove();
      store.lifetime.points = xpForLevel(12) + 10; saveStore();
      showIntroPopup(); await wait(300);
      out.free = !!document.querySelector('#intro-pop .intro-gate-note');
      document.getElementById('intro-pop')?.remove();
      return out; }""")
    check("held at the wall: the note box is on the card; under it: no box",
          r.get("held") and "badge" in r.get("text", "") and not r.get("free"), r)
    ctx.close()


def m4(br):
    print("\nm4. a new account: his introduction (a little shorter), then the main menu's tips, no What's New")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    n = pg.evaluate("() => ({ fresh: novaIntroLines({}).length, existing: novaIntroLines({ existing: true }).length })")
    pg.evaluate("""() => { localStorage.removeItem('class26e.intro.seen');
      window.__seen = []; new MutationObserver(() => { ['nova-intro', 'intro-pop', 'tour-tooltip'].forEach(id => {
        const e = document.getElementById(id); if(e && !e.__m){ e.__m = 1; window.__seen.push(id); } }); })
        .observe(document.body, { childList: true });
      store.onboardingComplete = false; store.tourRev = 0; pendingMainMenuTour = true; showHome(); }""")
    talk = pg.evaluate(TALK, "nova-intro")
    tips = pg.evaluate(TOUR)
    seen = pg.evaluate("async () => { await new Promise(r => setTimeout(r, 2500)); return window.__seen.slice(); }")
    check("a new account's introduction is at most 14 lines (16 before) and an existing one's at most 18 (21 before)",
          0 < n["fresh"] <= 14 and 0 < n["existing"] <= 18, n)
    check("then the main menu's tips, and no What's New card",
          talk.get("open") and len(tips) >= 6 and "intro-pop" not in seen and seen.count("nova-intro") == 1, {"seen": seen, "tips": len(tips)})
    ctx.close()


def m5(br):
    print("\nm5. the card on both reference devices: on screen, Got it reachable")
    for (w, h, dev) in DEVS:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        pg.evaluate("() => { document.getElementById('intro-pop')?.remove(); showIntroPopup(); }")
        card = pg.evaluate(CARD)
        check("%s the card is inside the screen and Got it can be reached" % dev, card.get("cardInView") and card.get("goInView"), card)
        ctx.close()


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cb.CHROME)
        try:
            fns = os.environ.get("ONLY_FN")
            for fn in (fns.split(",") if fns else ["m1", "m2", "m3", "m4", "m5"]):
                try:
                    globals()[fn](br)
                except Exception as e:
                    check("%s ran to the end" % fn, False, str(e)[:200])
        finally:
            br.close()
    cb.SERVER.shutdown()
    print("\n%s  (%d failure(s))" % ("ALL PASS" if not cb.FAILURES else "FAILED: " + ", ".join(cb.FAILURES), len(cb.FAILURES)))
    return 1 if cb.FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
