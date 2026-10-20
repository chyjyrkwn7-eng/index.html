#!/usr/bin/env python3
"""Build 327, package D: one Liquid Glass again, a tick that draws itself,
a mark on the next test's units, bigger and whiter tab icons, the lobby's
switch back with Invite to its left and no green ring, Save and exit not
green, and a quieter sky. Every section was written against build 326
(5ce026a), where it fails, and passes on this build:

  python3 tools/check-b327-d.py
  python3 tools/check-b327-d.py --against /tmp/claude-0/b327/index-326.html
  ONLY_FN=check_lobby,check_save python3 tools/check-b327-d.py

Madison's words (Oct 20) are quoted in front of each section. The helpers
(booted, the Firestore stub, the fake rooms) are check-behaviour's and
check-b326-f's, loaded without running them. Exits non-zero on any failure.
"""
import importlib.util
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py"))
cb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cb)   # reads --against from sys.argv itself
_spec2 = importlib.util.spec_from_file_location("cf", os.path.join(HERE, "check-b326-f.py"))
cf = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(cf)

from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops

check, booted, USED, PHONE, TABLET = cb.check, cb.booted, cb.USED_ACCOUNT, cb.PHONE, cb.TABLET
UNITS = ("() => { document.querySelectorAll('#pushing-update,#intro-pop,.nova-talk').forEach(n => n.remove());"
         " store.seenUnitSelectTour = true; store.seenUnitHoldTip = true; cfg.mode = 'drill'; cfg.units = []; showSetup(); }")
RGBA = "const rgba = c => { const v = (String(c).match(/[\\d.]+/g) || []).map(Number); return { r: v[0], g: v[1], b: v[2], a: v.length > 3 ? v[3] : 1 }; };"


# --------------------------------------------------------------------------
SURF = """() => { %s
  const st = s => { const e = document.querySelector(s); if(!e) return null; const c = getComputedStyle(e);
    return { bg: rgba(c.backgroundColor), bf: c.backdropFilter || c.webkitBackdropFilter || 'none', border: c.borderTopColor, shadow: c.boxShadow }; };
  return { card: st('.picks > label.pick:not(.pick-checked)'), search: st('.searchbox'), chat: st('.chatdock-btn'), bar: st('.bottomtabs') }; }""" % RGBA


def catch_light(shadow):
    """The brightest top catch-light (an inset 0 1px 0 white) in a box-shadow."""
    import re
    best = 0
    for m in re.finditer(r"rgba\(255, 255, 255, ([\d.]+)\) 0px 1px 0px 0px inset", shadow or ""):
        best = max(best, float(m.group(1)))
    return best


def check_surfaces(br):
    """1. "The new darker Liquid Glass for the unit selection screen ... don't
    go with the rest of the page, like it doesn't go with the start bar, the
    search bar, the chat button ... It's not cohesive." On 326 the unit card
    was a near-black blue rgba(13,16,21), the chat button a third recipe
    (an 8px saturating blur), and only the tab bar had the bright top rim."""
    print("\n1. the unit card, the search field, the chat button and the tab bar are one glass")
    for label, w, h in (PHONE, TABLET):
        ctx, pg = booted(br, w, h, seed=USED)
        pg.evaluate(UNITS)
        pg.wait_for_timeout(1200)
        r = pg.evaluate(SURF)
        ctx.close()
        if not all(r.values()):
            check("%s: all four surfaces are on the unit screen" % label, False, {k: bool(v) for k, v in r.items()}); continue
        bar = r["bar"]["bg"]
        tint = lambda x: all(abs(x["bg"][k] - bar[k]) <= 16 for k in "rgb") and x["bg"]["a"] >= .55
        check("%s: card, search and chat are the bar's grey tint (within 16 of rgb(%d,%d,%d)), never 326's blue-black" % (label, bar["r"], bar["g"], bar["b"]),
              all(tint(r[k]) for k in ("card", "search", "chat")), {k: r[k]["bg"] for k in ("card", "search", "chat")})
        check("%s: card, search and chat share one frost (%s)" % (label, r["card"]["bf"]),
              r["card"]["bf"] == r["search"]["bf"] == r["chat"]["bf"] and "blur" in r["card"]["bf"] and "brightness" not in r["card"]["bf"],
              [r[k]["bf"] for k in ("card", "search", "chat")])
        check("%s: card, search and chat share one rim colour" % label,
              r["card"]["border"] == r["search"]["border"] == r["chat"]["border"], [r[k]["border"] for k in ("card", "search", "chat")])
        cl = {k: catch_light(r[k]["shadow"]) for k in r}
        check("%s: all four carry the bar's bright catch-light along the top (>= .18)" % label,
              all(v >= .18 for v in cl.values()), cl)
    # app-wide: the same card on other screens
    ctx, pg = booted(br, *PHONE[1:], seed=USED)
    pg.evaluate("() => { document.querySelectorAll('#pushing-update,#intro-pop,.nova-talk').forEach(n => n.remove()); showModeSelect(); }")
    pg.wait_for_timeout(900)
    mode = pg.evaluate("() => { const e = document.querySelector('.modecard'); return e ? getComputedStyle(e).backgroundColor : null; }")
    pg.evaluate(UNITS); pg.wait_for_timeout(900)
    card = pg.evaluate("() => getComputedStyle(document.querySelector('.picks > label.pick:not(.pick-checked)')).backgroundColor")
    tok = pg.evaluate("() => getComputedStyle(document.documentElement).getPropertyValue('--surface-1').trim()")
    ctx.close()
    check("a mode card on Mode select is the same glass as a unit card (%s / %s), off the one token (%s)" % (mode, card, tok),
          mode == card and mode is not None, (mode, card, tok))


# --------------------------------------------------------------------------
TICK = """async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
  const cards = [...document.querySelectorAll('.picks > label.pick')];
  const all = cards.length > 0 && cards.every(c => c.querySelector(':scope > .box svg.pick-tick path'));
  const c = cards.find(x => !/Penal/.test(x.textContent));
  const path = c && c.querySelector(':scope > .box svg.pick-tick path');
  const before = path ? parseFloat(getComputedStyle(path).strokeDashoffset) : null;
  const glyph = c ? getComputedStyle(c.querySelector(':scope > .box')).fontSize : null;
  if(c) c.click();
  await wait(90);
  const early = path ? parseFloat(getComputedStyle(path).strokeDashoffset) : null;
  const anim = path ? path.getAnimations().map(a => a.transitionProperty || a.animationName) : [];
  await wait(700);
  const after = path ? parseFloat(getComputedStyle(path).strokeDashoffset) : null;
  const bx = c ? getComputedStyle(c.querySelector(':scope > .box')) : null;
  return { n: cards.length, all, before, early, anim, after, glyph, bgImg: bx && bx.backgroundImage, picked: c && c.classList.contains('pick-checked') }; }"""


def check_tick(br):
    """2. "The unit selection cards, could they be improved by making the
    checkmark better?" 326's tick was the text glyph in the font's weight."""
    print("\n2. the selected circle draws its own tick")
    for label, w, h in (PHONE, TABLET):
        ctx, pg = booted(br, w, h, seed=USED)
        pg.evaluate(UNITS)
        pg.wait_for_timeout(1100)
        r = pg.evaluate(TICK)
        ctx.close()
        check("%s: every unit card's circle carries an SVG tick (%d cards), the text glyph hidden (font-size %s)" % (label, r["n"], r["glyph"]),
              r["all"] and r["glyph"] == "0px", r)
        check("%s: unpicked the tick is undrawn (dashoffset 1); picked it draws in (a stroke-dashoffset transition) to 0" % label,
              r["before"] == 1 and r["after"] == 0 and "stroke-dashoffset" in r["anim"] and r["picked"], r)
        check("%s: the picked circle is a lit disc (a light over the accent)" % label,
              bool(r["bgImg"]) and "gradient" in (r["bgImg"] or ""), r["bgImg"])


# --------------------------------------------------------------------------
TAGS = """(today) => { window.todayCalendarKey = () => today;
  document.querySelectorAll('#pushing-update,#intro-pop,.nova-talk').forEach(n => n.remove());
  store.seenUnitSelectTour = true; store.seenUnitHoldTip = true; cfg.mode = 'drill'; cfg.units = []; showSetup();
  return [...document.querySelectorAll('.picks > label.pick')].map(c => { const t = c.querySelector(':scope > .pick-nexttest');
    let hit = null;
    if(t){ c.scrollIntoView({ block: 'center', behavior: 'instant' }); const b = t.getBoundingClientRect(); const e = document.elementFromPoint(b.left + b.width / 2, b.top + b.height / 2);
      hit = e ? (e.closest('.pick-nexttest') ? 'tag' : e.closest('label.pick') === c ? 'card' : 'other') : null; }
    return { name: (c.querySelector('.pname') || {}).textContent, tag: t ? t.textContent : null, pe: t ? getComputedStyle(t).pointerEvents : null, hit }; }); }"""


def check_next_test(br):
    """3. "Would it be a cool feature if somehow like a mark on the units for
    the upcoming test?" Only where the app knows: TEST_TOPICS posts Penal
    Code (slides 256-578) for Mon Oct 26; the test after it posts nothing."""
    print("\n3. the next test's units carry a mark, only when its topics are posted")
    for label, w, h in (PHONE, TABLET, ("SE 1st gen", 320, 568)):
        ctx, pg = booted(br, w, h, seed=USED)
        r = pg.evaluate(TAGS, "2026-10-20")
        tagged = [x for x in r if x["tag"]]
        check("%s (Oct 20): Penal Code alone is marked, with its date (%s)" % (label, [(x["name"], x["tag"]) for x in tagged]),
              len(tagged) == 1 and tagged[0]["name"] == "Penal Code" and "Next test" in tagged[0]["tag"].replace("NEXT TEST", "Next test") and "26" in tagged[0]["tag"], tagged)
        check("%s: the mark is a label - a tap on it is a tap on the card" % label,
              bool(tagged) and tagged[0]["pe"] == "none" and tagged[0]["hit"] == "card", tagged[:1])
        r2 = pg.evaluate(TAGS, "2026-10-27")
        check("%s (Oct 27): the next test (Nov 2) has nothing posted, so nothing is marked" % label,
              not any(x["tag"] for x in r2), [x for x in r2 if x["tag"]])
        overflow = pg.evaluate("() => document.documentElement.scrollWidth - innerWidth")
        check("%s: no sideways scroll" % label, overflow <= 0, overflow)
        ctx.close()


# --------------------------------------------------------------------------
ICONS = """() => { %s
  const tabs = [...document.querySelectorAll('.bottomtabs .bottomtabs-navrow .bottomtab')];
  const ic = tabs.map(t => t.querySelector('.bottomtab-icon')).filter(i => i && !i.classList.contains('bottomtab-icon-avatar') && !i.classList.contains('bottomtab-start-icon'));
  const inactive = tabs.filter(t => !t.classList.contains('active')).map(t => rgba(getComputedStyle(t).color));
  const act = tabs.find(t => t.classList.contains('active'));
  const bar = document.querySelector('.bottomtabs').getBoundingClientRect();
  const out = tabs.filter(t => { const b = t.getBoundingClientRect(); return b.left < bar.left - .5 || b.right > bar.right + .5; }).length;
  return { w: ic.map(i => i.getBoundingClientRect().width), inactive: inactive.map(c => c.a), act: act ? rgba(getComputedStyle(act).color) : null,
           bar: [bar.left, bar.right], vw: innerWidth, out }; }""" % RGBA


def check_tab_icons(br):
    """4. "The bottom tab bar, the icons of the 4 things are good but could
    they not be slightly bigger and more white?" 326: 28px (35.2 tablet) at
    84% white."""
    print("\n4. the tab icons a step bigger and whiter, and the bar still fits")
    for label, w, h, need in (("iPhone 17 Pro Max", 440, 956, 30), ("iPad Pro 11\"", 834, 1194, 37), ("SE 1st gen", 320, 568, 30)):
        ctx, pg = booted(br, w, h, seed=USED)
        pg.evaluate("() => document.querySelectorAll('#pushing-update,#intro-pop,.nova-talk').forEach(n => n.remove())")
        r = pg.evaluate(ICONS)
        check("%s Home: the three line icons are >= %dpx (%s)" % (label, need, [round(x, 1) for x in r["w"]]),
              len(r["w"]) == 3 and min(r["w"]) >= need, r["w"])
        check("%s Home: tabs you are not on are near-white (alpha %s), the one you are on white" % (label, r["inactive"]),
              r["inactive"] and min(r["inactive"]) >= .9 and r["act"] and r["act"]["a"] == 1, r)
        check("%s Home: every tab inside the bar, the bar on screen" % label,
              r["out"] == 0 and r["bar"][0] >= 0 and r["bar"][1] <= r["vw"], r)
        pg.evaluate(UNITS); pg.wait_for_timeout(1000)
        r = pg.evaluate(ICONS)
        check("%s units (with Start): every tab inside the bar, the bar on screen, icons >= %dpx" % (label, need if w >= 640 else 30),
              r["out"] == 0 and r["bar"][0] >= 0 and r["bar"][1] <= r["vw"] and r["w"] and min(r["w"]) >= (need if w >= 640 else 30), r)
        ctx.close()


# --------------------------------------------------------------------------
LOBBY_READ = """() => {
  const tools = document.querySelector('.vroom-roster-tools');
  if(!tools) return null;
  const sw = tools.querySelector('[role="switch"]'), inv = tools.querySelector('.vroom-invite-btn');
  const R = e => { const b = e.getBoundingClientRect(); return { l: b.left, r: b.right, t: b.top, b: b.bottom }; };
  const lines = [...tools.querySelectorAll('p')].map(p => p.textContent);
  const rows = [...document.querySelectorAll('.vroom-roster-list .vroom-row.is-ready')].map(r => { const s = getComputedStyle(r);
    return { border: s.borderTopColor, shadow: s.boxShadow, badgeTick: getComputedStyle(r.querySelector('.vroom-ready-badge'), '::before').content }; });
  return { sw: sw ? { nsw: !!sw.querySelector('.nsw'), checked: sw.getAttribute('aria-checked'), rect: R(sw) } : null,
           inv: inv ? R(inv) : null, seg: !!document.querySelector('.vroom-access-seg'), lines, rows, open: __rooms.ROOM326 && __rooms.ROOM326.open }; }"""


def check_lobby(br):
    """5. "I don't like the green outline for being ready in the lobby, it's
    too much. For the lobby, I prefer the regular toggle switch with the
    invite friends button to the left of it. The toggles description is just
    confusing?" 326: a 2px green ring, a two-choice segment, Invite right."""
    print("\n5. the lobby: the switch with Invite to its left, one plain line, no green ring")
    for label, w, h in (PHONE, TABLET, ("SE 1st gen", 320, 568)):
        ctx, pg = booted(br, w, h, seed=USED, init=cf.ROOM_FAKE)
        pg.evaluate(cf.CLEAN)
        pg.evaluate("(o) => (%s)(o)" % cf.LOBBY, {"n": 4, "meReady": True})
        pg.wait_for_timeout(1400)
        r = pg.evaluate(LOBBY_READ)
        if not r:
            check("%s: the host's lobby has its tools row" % label, False); ctx.close(); continue
        check("%s: a role=switch with the app's .nsw track, and no two-choice segment" % label,
              bool(r["sw"]) and r["sw"]["nsw"] and not r["seg"], r)
        ok = r["sw"] and r["inv"] and r["inv"]["r"] <= r["sw"]["rect"]["l"] + .5 and min(r["inv"]["b"], r["sw"]["rect"]["b"]) - max(r["inv"]["t"], r["sw"]["rect"]["t"]) > 10
        check("%s: Invite friends is to the LEFT of the switch, on the same row" % label, ok, (r["inv"], r["sw"] and r["sw"]["rect"]))
        check("%s: one line under it (%r), and it never says 'Invite only' as if it were the switch's name" % (label, r["lines"]),
              len(r["lines"]) == 1 and "Invite only" not in r["lines"][0] and len(r["lines"][0]) <= 60, r["lines"])
        green = lambda s: "61, 214, 140" in (s or "")
        check("%s: no ready card has a green edge or ring (%d ready)" % (label, len(r["rows"])),
              r["rows"] and all(not green(x["border"]) and not green(x["shadow"]) for x in r["rows"]), r["rows"][:1])
        before = r["lines"]
        pg.evaluate("() => document.querySelector('.vroom-roster-tools [role=\"switch\"]').click()")
        pg.wait_for_timeout(500)
        r2 = pg.evaluate(LOBBY_READ)
        check("%s: a tap turns it on, writes open:true to the room, and the line does not change" % label,
              r2 and r2["sw"]["checked"] == "true" and r2["open"] is True and r2["lines"] == before, r2 and (r2["sw"], r2["open"], r2["lines"]))
        overflow = pg.evaluate("() => document.documentElement.scrollWidth - innerWidth")
        check("%s: no sideways scroll" % label, overflow <= 0, overflow)
        ctx.close()


# --------------------------------------------------------------------------
def check_save(br):
    """6. "Save and exit as a green button is ABSOLUTELY not the move ... Make
    that a color that makes sense and goes with it all." 326: #1E7A4F."""
    print("\n6. Save and exit is the app's deep blue, not green")
    for label, w, h in (PHONE, TABLET):
        ctx, pg = booted(br, w, h, seed=USED)
        r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
          document.querySelectorAll('#pushing-update,#intro-pop,.nova-talk').forEach(n => n.remove());
          theme.autoAdvance = false; cfg.mode = 'drill'; cfg.units = ['Identity Crimes']; cfg.source = 'all'; cfg.size = 0; cfg.versions = {};
          beginRun(poolNow(), null, null);
          for(let i = 0; i < 80 && !document.querySelector('.qpanel .choice'); i++) await wait(100);
          document.querySelectorAll('.unlock-overlay,.hu-overlay').forEach(n => n.remove());
          pauseRun(); await wait(700);
          const s = document.getElementById('pause-save'); if(!s) return null;
          const v = (getComputedStyle(s).backgroundColor.match(/[\\d.]+/g) || []).map(Number), c = (getComputedStyle(s).color.match(/[\\d.]+/g) || []).map(Number);
          return { bg: v, fg: c }; }""")
        ctx.close()
        if not r:
            check("%s: the pause sheet has Save and exit" % label, False); continue
        bg, fg = r["bg"], r["fg"]
        lum = lambda c: sum(k * ((v / 255) / 12.92 if v / 255 <= .03928 else (((v / 255) + .055) / 1.055) ** 2.4) for k, v in zip((.2126, .7152, .0722), c[:3]))
        con = (max(lum(bg), lum(fg)) + .05) / (min(lum(bg), lum(fg)) + .05)
        check("%s: not green (rgb %s): blue leads, green does not" % (label, bg[:3]),
              bg[2] > bg[1] + 40 and bg[2] > bg[0] + 60 and not (bg[1] > bg[0] + 30 and bg[1] > bg[2]), bg)
        check("%s: white words on it at >= 4.5:1 (%.1f)" % (label, con), con >= 4.5, con)


# --------------------------------------------------------------------------
# The light the stars add to Home's frame, everything else hidden, on a 17
# Pro Max at 3x. Build 326 measured 430,813 here (its notes) - this asks for
# a further smidge: 65-88% of it, never a bare sky.
SKY_326 = 430813


def check_sky(br):
    """7. "The stars in the background ... a smidge smidge less. They are
    great but a little distracting." """
    print("\n7. the starfield: a smidge smidge less, still there")
    ctx, pg = booted(br, 440, 956, seed=USED, dpr=3)
    pg.evaluate("() => { document.querySelectorAll('.nova-talk,.daily-alert,.toast').forEach(n => n.remove()); showHome(); }")
    pg.wait_for_timeout(1500)
    k = pg.evaluate("() => ({ n: SKY_TILES.reduce((a, t) => a + t.n, 0), a: SKY_ALPHA })")
    pg.add_style_tag(content="body > *:not(script){ visibility:hidden !important; }")
    pg.wait_for_timeout(900)
    a = Image.open(io.BytesIO(pg.screenshot())).convert("L")
    pg.evaluate("document.documentElement.classList.remove('sky-ready')")
    pg.wait_for_timeout(900)
    b = Image.open(io.BytesIO(pg.screenshot())).convert("L")
    ctx.close()
    hist = ImageChops.subtract(a, b).histogram()
    light = sum(i * n for i, n in enumerate(hist))
    stars = sum(hist[31:])
    check("fewer stars than 326's 136 (%d) and each dimmer than its .96 (%.2f)" % (k["n"], k["a"]), k["n"] < 136 and k["a"] < .96, k)
    check("the stars add 65-88%% of build 326's light to Home (%d, %.3f) and the sky is still there (%d bright pixels)" % (light, light / SKY_326, stars),
          .65 <= light / SKY_326 <= .88 and stars > 2000, (light, stars))


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cb.CHROME)
        try:
            only = os.environ.get("ONLY_FN")
            for f in (check_surfaces, check_tick, check_next_test, check_tab_icons, check_lobby, check_save, check_sky):
                if only and f.__name__ not in only.split(","):
                    continue
                try:
                    f(br)
                except Exception as e:
                    check("%s ran at all" % f.__name__, False, repr(e)[:300])
        finally:
            br.close()
    cb.SERVER.shutdown()
    print("\n%s  (%d failure(s))" % ("ALL PASS" if not cb.FAILURES else "FAILED: " + ", ".join(cb.FAILURES), len(cb.FAILURES)))
    return 1 if cb.FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
