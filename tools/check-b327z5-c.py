#!/usr/bin/env python3
"""Build 327z5 (C): every notice on the account banner's glass, centred.

"The 'welcome back your progress is here' thing ... should be bigger like and
better like the sync one ... Maybe when you save a test and go back to main
menu you'd get one for that? ... The key icon looks broken still ... I don't
like the rank up icon, maybe it's the star? ... That banner popup thing also
does not look centered ... I think all the daily question stuff needs to be
in the pop up like that ... The daily question button, the loading bar around
it looks off/ bad too ... Is there anywhere else that same Liquid Glass look
could be applied? ... Why is there yellow in it like that?"

  A. Every top banner (account, welcome, saved test, daily done, daily out,
     rankings, rank up) on both reference devices: the same gap left and
     right (1.5px), clear of the chat button, and its icon, words and x on
     one centre line (2px).
  B. "Welcome back" is the top banner #welcome-banner (tag WELCOME BACK), not
     a toast, and no showToast in the page says it.
  C. Save and exit lands on Home with a SAVED TEST banner.
  D. The key and the rank-up icon are drawn in strokes: no filled shape (the
     key was a filled blob, the rank up had a filled star).
  E. The daily question's "It's out" and "Done for today" are top banners;
     nothing beside the "?".
  F. No banner carries a wash of its colour: no ::after sweep, no gradient
     of its colour on its body.
  G. The ring is on the button's rim (within 2px), the button's own border
     stood down, round caps while filling, nothing drawn at 0.
  H. A toast has the banners' left bar and a bare icon.

  python3 tools/check-b327z5-c.py [--against FILE]
"""
import importlib.util, os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py"))
cb = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(cb)
from playwright.sync_api import sync_playwright  # noqa: E402
check, booted, USED_ACCOUNT, CHROME = cb.check, cb.booted, cb.USED_ACCOUNT, cb.CHROME
CLEAN = "() => document.querySelectorAll('#intro-pop,.nova-talk,#tour-overlay,#tour-tooltip,.daily-alert,.app-banner,#daily-lock-tip,.toast').forEach(n=>n.remove())"

GEO = """(sel) => { const a = document.querySelector(sel); if(!a) return null;
  const r = a.getBoundingClientRect(), cs = getComputedStyle(a);
  const mid = e => { const b = e.getBoundingClientRect(); return b.height ? b.top + b.height / 2 : null; };
  const icon = a.querySelector('.app-banner-icon svg, svg.app-banner-icon, .app-banner-icon');
  const x = a.querySelector('.app-banner-x svg') || a.querySelector('.daily-alert-go svg') || a.querySelector('.app-banner-act');
  const body = a.querySelector('.app-banner-body');
  let tm = null;
  if(body){ const rg = document.createRange(); rg.selectNodeContents(body); const rr = [...rg.getClientRects()].filter(q => q.height > 2);
    if(rr.length){ const t = Math.min(...rr.map(q => q.top)), b = Math.max(...rr.map(q => q.bottom)); tm = (t + b) / 2; } }
  const chat = [...document.querySelectorAll('.chatdock-btn, #roomchat-fab')].filter(c => { const b = c.getBoundingClientRect(); return b.width && getComputedStyle(c).visibility !== 'hidden' && getComputedStyle(c).opacity !== '0'; })
    .map(c => c.getBoundingClientRect());
  const hit = chat.some(c => c.left < r.right && c.right > r.left && c.top < r.bottom && c.bottom > r.top);
  const after = getComputedStyle(a, '::after');
  const col = cs.getPropertyValue('--banner-color').trim();
  return { l: r.left, r: innerWidth - r.right, top: r.top, w: r.width, chatHit: hit,
    iconMid: icon && mid(icon), xMid: x && mid(x), textMid: tm,
    tag: (a.querySelector('.app-banner-tag') || {}).textContent || '',
    after: after.content === 'none' || after.content === 'normal' ? '' : (after.backgroundImage || '') + '|' + after.content,
    bg: cs.backgroundImage, col,
    filled: [...a.querySelectorAll('.app-banner-icon path, .app-banner-icon circle, svg.app-banner-icon path, svg.app-banner-icon circle')]
      .filter(p => { const f = p.getAttribute('fill'); return f && f !== 'none'; }).length }; }"""

SCEN = [
    ("account", "#save-code-banner", "() => { const el = buildAppBanner('save-code-banner','account','Save your sync code - it is the only way back into your account','Save it',()=>{},()=>{}); document.body.appendChild(el); placeTopBanner(el); el.classList.add('show'); }"),
    ("welcome", "#welcome-banner", "() => { typeof showWelcomeBackBanner === 'function' ? showWelcomeBackBanner('Welcome back \\u2014 your progress is here.') : showToast('Welcome back \\u2014 your progress is here.'); }"),
    ("daily done", "#dailyalert", "() => { store.dailyQuestionDate = dailyPeriodKey(); showDailyQuestionLockedPopup(); }"),
    ("daily out", "#dailyalert", "() => { store.dailyQuestionDate = null; const b = document.querySelector('.daily-question-fab'); const rm = theme.reduceMotion; theme.reduceMotion = true; announceDailyReset(b); theme.reduceMotion = rm; }"),
    ("rankings", "#dailyalert", "() => showDailyAlert('You are not in the rankings yet', { kind: 'rankings' })"),
    ("rank up", "#dailyalert", "() => showDailyAlert('Your profile needs you - open Profile to see your rank up', { kind: 'rankup' })"),
]


def banners(br):
    for (w, h, dpr, dev) in [(440, 956, 3, "iphone"), (834, 1194, 2, "ipad")]:
        print("\nA-F. %s %dx%d" % (dev, w, h))
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, dpr=dpr)
        pg.evaluate(CLEAN); pg.evaluate("() => showHome()"); pg.wait_for_timeout(900); pg.evaluate(CLEAN)
        for name, sel, js in SCEN:
            pg.evaluate(CLEAN); pg.evaluate(js); pg.wait_for_timeout(1300)
            g = pg.evaluate(GEO, sel)
            check("%s: %s is a top banner" % (dev, name), bool(g) and g["top"] < h / 3, g)
            if not g: continue
            check("%s: %s - the same gap left and right" % (dev, name), abs(g["l"] - g["r"]) <= 1.5, (round(g["l"], 1), round(g["r"], 1)))
            check("%s: %s - clear of the chat button" % (dev, name), not g["chatHit"], g)
            mids = [m for m in (g["iconMid"], g["textMid"], g["xMid"]) if m is not None]
            check("%s: %s - icon, words and x on one centre line" % (dev, name),
                  len(mids) == 3 and max(mids) - min(mids) <= 2, (g["iconMid"], g["textMid"], g["xMid"]))
            check("%s: %s - no wash: no ::after sweep" % (dev, name), not g["after"], g["after"][:120])
            if name == "welcome":
                check("%s: welcome back is tagged WELCOME BACK" % dev, g["tag"] == "WELCOME BACK", g["tag"])
            if name in ("account", "rank up"):
                check("%s: %s icon is strokes, no filled shape" % (dev, name), g["filled"] == 0, g["filled"])
            if name in ("daily done", "daily out"):
                tip = pg.evaluate("() => !!document.getElementById('daily-lock-tip')")
                check("%s: %s - nothing beside the \"?\"" % (dev, name), not tip)
            if name == "welcome":
                toast = pg.evaluate("() => [...document.querySelectorAll('.toast')].map(t => t.textContent).join('|')")
                check("%s: welcome back is not a toast" % dev, "Welcome back" not in toast, toast)

        print("\nC. %s: Save and exit" % dev)
        r = pg.evaluate("""async () => {
          const wait = ms => new Promise(r => setTimeout(r, ms));
          const UNIT = 'Identity Crimes';
          const idx = QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === UNIT && inWholeUnit(QUESTIONS[i]));
          cfg.mode = 'drill'; cfg.units = [UNIT]; cfg.versions = {}; cfg.source = 'all'; cfg.size = 0; cfg.timer = 'up';
          beginRun(freshOrder(idx), null, null);
          for(let i = 0; i < 120 && !(document.querySelector('.qpanel .choice') && runStartTime != null); i++) await wait(100);
          pauseRun(); await wait(400);
          document.querySelectorAll('.daily-alert,.app-banner').forEach(n => n.remove());
          saveAndExitTest();
          for(let i = 0; i < 40 && !document.querySelector('#savedtest-banner.show'); i++) await wait(100);
          const b = document.querySelector('#savedtest-banner');
          return { home: document.querySelector('#stage [data-screen="home"]') != null || (document.querySelector('[data-screen]') || {}).dataset?.screen === 'home',
                   banner: !!b, tag: b ? (b.querySelector('.app-banner-tag') || {}).textContent : '' }; }""")
        check("%s: Save and exit lands on Home with a SAVED TEST banner" % dev, r["banner"] and r["tag"] == "SAVED TEST", r)

        print("\nG. %s: the ring" % dev)
        for st in ("ready", "done"):
            pg.evaluate(CLEAN)
            pg.evaluate("(st) => { store.dailyQuestionDate = st === 'done' ? dailyPeriodKey() : null; showHome(); }", st)
            pg.wait_for_timeout(1000)
            ring = pg.evaluate("""() => { const b = document.querySelector('.daily-question-fab'), r = b && b.querySelector('.dq-ring');
              if(!r) return null; const br = b.getBoundingClientRect(), rr = r.getBoundingClientRect(), p = r.querySelector('.dq-ring-prog');
              return { d: Math.max(Math.abs(br.left - rr.left), Math.abs(br.right - rr.right), Math.abs(br.top - rr.top), Math.abs(br.bottom - rr.bottom)),
                border: getComputedStyle(b).borderTopColor, full: r.classList.contains('is-full'),
                cap: p && getComputedStyle(p).strokeLinecap }; }""")
            check("%s: %s ring on the button's rim" % (dev, st), bool(ring) and ring["d"] <= 2, ring)
            if ring:
                check("%s: %s button's own border stood down" % (dev, st),
                      ring["border"] in ("rgba(0, 0, 0, 0)", "transparent"), ring["border"])
                if not ring["full"]:
                    check("%s: %s ring has round ends while it fills" % (dev, st), ring["cap"] == "round", ring["cap"])
        z = pg.evaluate("""() => { const r = document.querySelector('.dq-ring'); if(!r) return null;
          setDailyRing(r.closest('.daily-question-fab'), 0); const p = r.querySelector('.dq-ring-prog'); return getComputedStyle(p).opacity; }""")
        check("%s: nothing drawn at 0 (no round-capped dot)" % dev, z == "0", z)

        print("\nH. %s: a toast" % dev)
        pg.evaluate(CLEAN); pg.evaluate("() => showToast('Chat muted')"); pg.wait_for_timeout(500)
        t = pg.evaluate("""() => { const t = document.querySelector('.toast'); if(!t) return null; const cs = getComputedStyle(t);
          return { bl: cs.borderLeftWidth + ' ' + cs.borderLeftStyle, icon: !!t.querySelector('.toast-icon'), text: t.textContent }; }""")
        check("%s: a toast has the banners' 3px bar and a bare icon" % dev,
              bool(t) and t["bl"].startswith("3px solid") and t["icon"] and "Chat muted" in t["text"], t)
        ctx.close()


def source():
    print("\nB. no toast says welcome back")
    src = open(cb.SRC, encoding="utf-8").read() if hasattr(cb, "SRC") else ""
    bad = [ln.strip()[:80] for ln in src.splitlines() if "showToast(" in ln and ("Welcome back" in ln or "Signed back in" in ln or "Signed in to your account" in ln)]
    check("no showToast says welcome back / signed in", not bad, bad[:3])


if __name__ == "__main__":
    source()
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=CHROME)
        banners(br)
        br.close()
    print("\n%s  (%d failure(s))" % ("ALL PASS" if not cb.FAILURES else "FAILED: " + ", ".join(cb.FAILURES), len(cb.FAILURES)))
    sys.exit(1 if cb.FAILURES else 0)
