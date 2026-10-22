#!/usr/bin/env python3
"""Build 325, stream E: Settings, Stats, the unit screen, the Virtual Room's
setup and lobby. Each check was written against 6fc16b7 (build 324), where
it fails, and passes on this build:

  python3 tools/check-b325-e.py
  python3 tools/check-b325-e.py --against /path/to/old-index.html

Madison's words, Oct 18, for each section are quoted in front of it. The
helpers (booted, the Firestore stub, the fake rooms) are check-behaviour's,
loaded without running it. Exits non-zero on any failure.
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py"))
cb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cb)   # reads --against from sys.argv itself

from playwright.sync_api import sync_playwright

check, booted, USED, PHONE, TABLET = cb.check, cb.booted, cb.USED_ACCOUNT, cb.PHONE, cb.TABLET
ROOM_FAKE = cb._ROOM_FAKE
B323V_ROOM = cb._B323V_ROOM
CLEAN = "() => { document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove()); }"
MODE_WORDS = ["drill", "qualifier", "exam", "briefing", "review", "virtual room", "game"]

# A used account with history in four modes, so Recent tests and Test
# history have a Drill, a Qualifier and a Virtual Room row to colour.
HIST_SEED = """() => { const now = Date.now();
  store.testHistory = [
    { label: 'Penal Code', units: ['Penal Code'], pct: 100, elapsedMs: 600000, playedAt: now - 3600000, mode: 'drill' },
    { label: 'Identity Crimes', units: ['Identity Crimes'], pct: 83, elapsedMs: 300000, playedAt: now - 7200000, mode: 'exam' },
    { label: 'Identity Crimes', units: ['Identity Crimes'], pct: 92, elapsedMs: 280000, playedAt: now - 9000000, mode: 'exam', vr: true }
  ];
  const k = d => { const x = new Date(now - d * 864e5); return x.getFullYear() + '-' + String(x.getMonth() + 1).padStart(2, '0') + '-' + String(x.getDate()).padStart(2, '0'); };
  store.studyLog = {}; [0, 1, 2].forEach(d => store.studyLog[k(d)] = (50 + 30 * d) * 60000);
  saveStore(); }"""

HUE = """(c) => { const m = String(c).match(/[\\d.]+/g); if(!m) return null;
  let [r, g, b] = m.slice(0, 3).map(Number);
  if(/color\\(srgb/.test(c)){ r *= 255; g *= 255; b *= 255; }
  r /= 255; g /= 255; b /= 255;
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn;
  if(d < 0.04) return { h: null, s: 0 };
  let h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
  h = (h * 60 + 360) % 360; return { h: Math.round(h), s: +(d / mx).toFixed(2) }; }"""


def hue_in(h, lo, hi):
    if h is None:
        return False
    return lo <= h <= hi if lo <= hi else (h >= lo or h <= hi)


# --------------------------------------------------------------------------
def check_settings_and_soundtest(br):
    """1. "Move on after next question in settings title? That's a weird
    title, and the description is weird because it only mentions qualifier?
    It probably shouldn't mention any."  2. "I see a picture of a 'sound
    test' but I don't want that screen in the app." """
    print("\n1-2. the auto-advance row names no mode; the sound test page is gone")
    for label, w, h in (PHONE,):
        ctx, pg = booted(br, w, h, seed=USED)
        pg.evaluate(CLEAN)
        pg.evaluate("() => showProfile('settings')"); pg.wait_for_timeout(1200)
        row = pg.evaluate("""() => {
          /* the row whose switch IS theme.autoAdvance: flip it and see */
          for(const r of document.querySelectorAll('label.opt')){
            const cb = r.querySelector('input[type=checkbox]'); if(!cb) continue;
            const was = theme.autoAdvance; cb.click();
            const moved = theme.autoAdvance !== was; if(moved) cb.click();
            if(moved){ const t = r.querySelector('.otext'); const hint = r.querySelector('.ohint');
              return { title: t && t.firstChild ? t.firstChild.textContent.trim() : '', hint: hint ? hint.textContent.trim() : '' }; }
          }
          return null; }""")
        words = lambda s: [m for m in MODE_WORDS if m in (s or "").lower()]
        check("%s: the auto-advance row's title and line name no mode, and the title is short" % label,
              bool(row) and not words(row["title"]) and not words(row["hint"]) and 0 < len(row["title"]) <= 24
              and len(row["hint"]) > 20, row)
        st = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
          const out = { fn: typeof window.showSoundTest, css: 0 };
          for(const sh of document.styleSheets){ try{ for(const r of sh.cssRules){ if(/soundtest|\\.snd-row/.test(r.cssText)) out.css++; } }catch(e){} }
          const bl = document.querySelector('.settings-buildline'); out.line = !!bl;
          if(bl){ bl.scrollIntoView({ block: 'center', behavior: 'instant' }); await wait(200);
            const r = bl.getBoundingClientRect(); out.at = { x: r.left + r.width / 2, y: r.top + r.height / 2 }; }
          return out; }""")
        if st.get("at"):
            pg.mouse.move(st["at"]["x"], st["at"]["y"]); pg.mouse.down(); pg.wait_for_timeout(1100); pg.mouse.up()
            pg.wait_for_timeout(500)
        after = pg.evaluate("() => !!document.querySelector('.screen-soundtest')")
        check("%s: no showSoundTest, no sound-test CSS, and holding the build line opens nothing" % label,
              st["fn"] == "undefined" and st["css"] == 0 and st["line"] and not after, {**st, "opened": after})
        ctx.close()


RACE_SETUP = """async (auto) => { const wait = ms => new Promise(r => setTimeout(r, ms));
  __useRooms(); theme.autoAdvance = auto;
  const me = publicIdOf();
  __rooms.RACE325 = { hostCode: me, hostName: 'Madison', units: ['Identity Crimes'], versions: {}, game: 'race', open: false,
    status: 'starting', mode: 'exam', createdAt: 1, count: null, startAt: Date.now() - 1000,
    participants: { [me]: { name: 'Madison', avatarChar: 'ninja', joinedAt: 1, seen: 9e15, ready: true, progress: 0 },
                    pB0000000001: { name: 'Avery', avatarChar: 'zeus', joinedAt: 2, seen: 9e15, ready: true, progress: 0 } } };
  vroomCode = 'RACE325'; vroomMyKey = me; vroomIsHost = true;
  beginVirtualRoomTest(['Identity Crimes'], null, Date.now() - 1000, 0);
  for(let i = 0; i < 80 && !document.querySelector('.qpanel .choice'); i++) await wait(100);
  await wait(500);
  const p0 = pos, dl0 = raceQuestionDeadline, inRoom = !!inVirtualRoom;
  const c = document.querySelectorAll('.qpanel .choice')[1]; if(c) c.click();
  await wait(2200);
  const out = { inRoom, moved: pos !== p0, picked: picked[order[p0]] !== undefined,
                sameDeadline: raceQuestionDeadline === dl0 };
  /* the question's own clock still ends it: a picked answer stands and the race moves on */
  raceQuestionDeadline = Date.now() - 5; await wait(900);
  out.movedByClock = pos === p0 + 1;
  return out; }"""

DRILL_AUTO = """async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
  try{ leaveVirtualRoom(); }catch(e){} inVirtualRoom = false; vroomCode = null;
  theme.autoAdvance = true;
  cfg.mode = 'drill'; cfg.units = ['Identity Crimes']; cfg.source = 'all'; cfg.size = 0; cfg.versions = {};
  beginRun(poolNow(), null, null);
  for(let i = 0; i < 80 && !document.querySelector('.qpanel .choice'); i++) await wait(100);
  await wait(400);
  const p0 = pos; choose(correctSlot(order[pos])); await wait(1600);
  return { moved: pos === p0 + 1 }; }"""


def check_auto_advance_fair(br):
    """1. "Ensure that the timing of that when on doesn't mess with any of
    the timing of the virtual room game modes so it's still fair for
    everyone." On 324 a race pick with auto-advance on moved on by itself
    after 550ms while everyone else reached for Next."""
    print("\n1b. auto-advance changes nothing in a Virtual Room race (or a classic room), and still works outside one")
    ctx, pg = booted(br, 440, 956, seed=USED, init=ROOM_FAKE)
    pg.evaluate(CLEAN)
    on = pg.evaluate(RACE_SETUP, True)
    pg.evaluate("() => { try{ stopQuestionTimer(); }catch(e){} testInProgress = false; try{ leaveVirtualRoom(); }catch(e){} showHome(); }")
    pg.wait_for_timeout(600)
    off = pg.evaluate(RACE_SETUP, False)
    pg.evaluate("() => { try{ stopQuestionTimer(); }catch(e){} testInProgress = false; try{ leaveVirtualRoom(); }catch(e){} showHome(); }")
    pg.wait_for_timeout(600)
    drill = pg.evaluate(DRILL_AUTO)
    same = {k: on.get(k) for k in ("moved", "picked", "sameDeadline", "movedByClock")} == \
           {k: off.get(k) for k in ("moved", "picked", "sameDeadline", "movedByClock")}
    check("a race pick with auto-advance ON waits for Next or the clock exactly as with it OFF - and a Drill still auto-advances",
          on.get("inRoom") and same and on.get("moved") is False and on.get("picked") and on.get("sameDeadline")
          and on.get("movedByClock") and drill.get("moved"), {"on": on, "off": off, "drill": drill})
    # Tug of War and Battle have their own pauses between questions; they
    # never read the setting. Can't fail on any build, so it is reported,
    # not counted.
    src = pg.evaluate("""() => [tugSettleAnswer, renderTugScreen, startTugClock, battleSettleAnswer, renderBattleScreen, startBattleClock]
      .map(f => /autoAdvance/.test(String(f))).filter(Boolean).length""")
    print("  INFO Tug of War / Battle question functions that read theme.autoAdvance: %d (0 on every build)" % src)
    ctx.close()


PAUSE = """async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
  theme.autoAdvance = false;
  cfg.mode = 'drill'; cfg.units = ['Identity Crimes']; cfg.source = 'all'; cfg.size = 0; cfg.versions = {};
  beginRun(poolNow(), null, null);
  for(let i = 0; i < 80 && !document.querySelector('.qpanel .choice'); i++) await wait(100);
  document.querySelectorAll('.unlock-overlay,.hu-overlay').forEach(n => n.remove());
  pauseRun(); await wait(700);
  const s = document.getElementById('pause-save'), q = document.getElementById('pause-quit'), r = document.getElementById('resumebtn');
  if(!s) return null;
  const cs = getComputedStyle(s);
  const a = (cs.backgroundColor.match(/[\\d.]+/g) || []);
  return { alpha: a.length > 3 ? +a[3] : 1, bf: cs.backdropFilter || cs.webkitBackdropFilter || 'none',
           shadows: (cs.boxShadow.match(/inset/g) || []).length, outer: cs.boxShadow.split(/,(?![^(]*\\))/).filter(x => !/inset/.test(x)).length,
           h: Math.round(s.getBoundingClientRect().height), hq: Math.round(q.getBoundingClientRect().height),
           w: Math.round(s.getBoundingClientRect().width), wr: Math.round(r.getBoundingClientRect().width) }; }"""


def check_pause_save(br):
    """3. "The save and exit button idk how I feel about the color." """
    # MOVED in build 326: "The save and exit button is clear and see
    # through? Thats a terrible idea, let's try something else." It is
    # opaque now, with no backdrop blur (tools/check-b326-a.py holds the
    # new look); what is kept from 325 is the size and the lift.
    print("\n3. Save and exit is solid (326), the same size as its neighbours, with a lift")
    for label, w, h in (PHONE, TABLET):
        ctx, pg = booted(br, w, h, seed=USED)
        pg.evaluate(CLEAN)
        r = pg.evaluate(PAUSE)
        check("%s: Save and exit is opaque (no see-through fill, no backdrop blur) with a lift, as tall and wide as Quit and Resume" % label,
              bool(r) and r["alpha"] == 1 and r["bf"] == "none" and r["outer"] >= 2
              and abs(r["h"] - r["hq"]) <= 1 and abs(r["w"] - r["wr"]) <= 1, r)
        ctx.close()


STATS = """async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
  showProfile('stats'); await wait(900);
  /* on screen, as it is when anybody reads it: an off-screen chart's
     light-up is not guaranteed to have run */
  const ch0 = document.querySelector('.profile-stats-tab .stx-dots');
  /* twice: the tab's own smooth scroll to the top can still be running */
  if(ch0){ ch0.scrollIntoView({ block: 'center', behavior: 'instant' }); await wait(700);
           ch0.scrollIntoView({ block: 'center', behavior: 'instant' }); await wait(1300); }
  const tab = document.querySelector('.profile-stats-tab') || document;
  const g = tab.querySelector('.stx-glance .stat-grid');
  const cards = g ? [...g.querySelectorAll(':scope > .stat-card')] : [];
  const rows = {}; cards.forEach(c => { const t = Math.round(c.getBoundingClientRect().top); rows[t] = (rows[t] || 0) + 1; });
  const widths = cards.map(c => Math.round(c.getBoundingClientRect().width));
  const recent = [...tab.querySelectorAll('.stx-recent .thx-row')].map(r => {
    const rr = r.getBoundingClientRect(), body = r.querySelector('.thx-row-body').getBoundingClientRect();
    const right = [...r.children].filter(c => c.getBoundingClientRect().left >= body.right - 1 && c.getBoundingClientRect().width > 0);
    return { right: right.length, bodyToEdge: Math.round(rr.right - body.right) }; });
  /* the foot of the last lit column: the theme's own colour, deepened -
     not the top of the scale, where it warms toward --theme-c1 */
  const dot = [...tab.querySelectorAll('.stx-dot.on.is-mid:not(.is-cap)')].pop();
  const sel = tab.querySelector('.stx-dots-switch button[aria-selected="true"]');
  return { n: cards.length, wide: g ? g.querySelectorAll('.stat-card-wide').length : -1, rows: Object.values(rows), widths, recent,
           dot: dot ? getComputedStyle(dot).backgroundColor : null, sel: sel ? getComputedStyle(sel).backgroundColor : null,
           num: (tab.querySelector('.stx-glance .stat-num') ? getComputedStyle(tab.querySelector('.stx-glance .stat-num')).color : null) }; }"""


def check_stats(br):
    """4. "The stats tab, the study time one is purple and still needs to
    match the rest of the stats colors/theme. I'm not sure why total xp is
    in the at a glance box. Remove that. The recent tests also has the
    badge on the right, remove that." """
    print("\n4. Stats: no Total XP and no hole; the study chart in the theme's colour; nothing on the right of a recent test")
    for label, w, h in (PHONE, TABLET):
        ctx, pg = booted(br, w, h, seed=USED)
        pg.evaluate(CLEAN); pg.evaluate(HIST_SEED)
        r = pg.evaluate(STATS)
        cols = 2 if w < 640 else 4
        check("%s: At a glance is four even cards in full rows of %d - no Total XP, no wide card, no hole" % (label, cols),
              r["n"] == 4 and r["wide"] == 0 and all(x == cols for x in r["rows"]) and max(r["widths"]) - min(r["widths"]) <= 1, r)
        check("%s: a Recent tests row has nothing on its right - the row ends with the test" % label,
              len(r["recent"]) == 3 and all(x["right"] == 0 for x in r["recent"]), r["recent"])
        hue = lambda c: pg.evaluate(HUE, c)
        d0, n0, s0 = hue(r["dot"]), hue(r["num"]), r["sel"]
        # the same tab on another theme: the chart must follow it as the numbers do
        pg.evaluate("() => { document.documentElement.dataset.accent = 'adept'; }")
        r2 = pg.evaluate(STATS)
        d1, n1 = hue(r2["dot"]), hue(r2["num"])
        near = lambda a, b: a and b and a["h"] is not None and b["h"] is not None and min(abs(a["h"] - b["h"]), 360 - abs(a["h"] - b["h"])) <= 22
        check("%s: the study chart's dots are the Stats numbers' colour, and follow a theme change with them (not violet)" % label,
              near(d0, n0) and near(d1, n1) and not near(d0, d1) and r2["sel"] != s0,
              {"default": {"dot": d0, "num": n0}, "sapphire": {"dot": d1, "num": n1}, "switch": [s0, r2["sel"]]})
        ctx.close()


def check_mode_colours(br):
    """5. "In recent tests, I see drill tests but they aren't showing up in
    the drill color for the word and same for qualifier." """
    print("\n5. a test row's mode word is in its mode's colour - Recent tests, Test history and a test's page")
    ctx, pg = booted(br, 440, 956, seed=USED)
    pg.evaluate(CLEAN); pg.evaluate(HIST_SEED)
    res = {}
    for where, js in (("stats", "() => showProfile('stats')"), ("history", "() => showTestReviewList()")):
        pg.evaluate(js); pg.wait_for_timeout(1400)
        res[where] = pg.evaluate("""(sel) => [...document.querySelectorAll(sel + ' .thx-chip')].map(c => ({ cls: c.className, color: getComputedStyle(c).color, border: getComputedStyle(c).borderTopColor }))""",
                                 ".stx-recent" if where == "stats" else ".screen-testhistory")
    pg.evaluate("() => showTestHistoryDetail(testHistoryEntries()[1])"); pg.wait_for_timeout(900)
    res["detail"] = pg.evaluate("() => [...document.querySelectorAll('.screen-testdetail .thx-chip')].map(c => ({ cls: c.className, color: getComputedStyle(c).color, border: getComputedStyle(c).borderTopColor }))")
    # the mode picker's own colours: Drill red, Mock orange, Virtual Room blue (MOVED IN 327 (b327k): Mock)
    want = {"thx-chip-drill": (340, 12), "thx-chip-exam": (18, 40), "thx-chip-vr": (195, 225)}
    bad = []
    for where, chips in res.items():
        for c in chips:
            k = next((x for x in want if x in c["cls"]), None)
            if not k:
                bad.append((where, c["cls"], "no mode class")); continue
            hb = pg.evaluate(HUE, c["border"])
            if not (hb and hue_in(hb["h"], *want[k]) and hb["s"] >= 0.3):
                bad.append((where, k, c["border"], hb))
    n = sum(len(v) for v in res.values())
    check("every mode chip (%d) is its mode's colour: Drill red, Mock orange, Virtual Room blue" % n,
          n >= 7 and not bad, bad or n)
    ctx.close()


UNITS = """async (mode) => { const wait = ms => new Promise(r => setTimeout(r, ms));
  cfg.mode = mode; cfg.units = []; showSetup(); await wait(900);
  const list = document.querySelector('.picks');
  const cards = [...list.querySelectorAll(':scope > label.pick')];
  cards.forEach(c => c.classList.add('pick-revealed'));
  const a = cards[0].getBoundingClientRect(), b = cards[1].getBoundingClientRect();
  const h0 = Math.round(cards[1].getBoundingClientRect().height);
  cards[1].querySelector('input').click(); await wait(700);
  const h1 = Math.round(cards[1].getBoundingClientRect().height);
  const kids = [...list.children];
  return { side: Math.abs(a.top - b.top) < 2 && b.left > a.right, w: Math.round(a.width), h: Math.round(a.height),
           drawers: document.querySelectorAll('.pick-more, .pick-main, .pick-more-open').length,
           grow: h1 - h0, hint: (document.querySelector('.picks-holdhint') || {}).textContent || '',
           starredLast: mode === 'review' ? (kids.filter(k => !k.classList.contains('pick-tba')).pop() || {}).className : null }; }"""


def check_units(br):
    """6. "The unit selection screen, I think we can revert that, the
    square boxes were better I think." """
    print("\n6. the unit screen is build 322's squares again (two across, no drawer), Starred still last")
    for label, w, h in (PHONE, TABLET):
        ctx, pg = booted(br, w, h, seed=USED)
        pg.evaluate(CLEAN); pg.evaluate("() => { store.seenUnitSelectTour = true; store.seenUnitHoldTip = true; }")
        r = pg.evaluate(UNITS, "drill")
        rv = pg.evaluate(UNITS, "review")
        # 322's squares: two across, and a box (h/w 1.1 on a phone, 0.55 on
        # an iPad Pro 11") - a 323 row was one across at h/w ~0.2 and less
        # ...and what 323 fixed that still applies is kept: Briefing's Starred
        # questions box after the units, not on top (not a check of its own:
        # it holds on 324 too, and a check that cannot fail is not one)
        check("%s: cards sit two across as boxes (h/w %.2f), no drawer, no growth when ticked - and Starred still after the units" % (label, r["h"] / max(1, r["w"])),
              r["side"] and r["h"] / max(1, r["w"]) >= 0.45 and r["drawers"] == 0 and abs(r["grow"]) <= 1
              and "pick-flagged-all" in (rv["starredLast"] or ""), {**r, "starredLast": rv["starredLast"]})
        ctx.close()


def tap_at(pg, sel):
    """A real tap at the element's middle. Not pg.click(): the not-yet button
    carries aria-disabled (it still takes the tap, and says why), which
    Playwright's actionability check refuses to click."""
    r = pg.evaluate("(s) => { const e = document.querySelector(s); if(!e) return null; const b = e.getBoundingClientRect(); return { x: b.left + b.width / 2, y: b.top + b.height / 2 }; }", sel)
    if r:
        pg.mouse.click(r["x"], r["y"])
    return bool(r)


VR_BAR = """() => { const bar = document.querySelector('#stage > .vroom-setup-bar');
  const t = document.getElementById('bottomtabs');
  const tabsShown = !!t && !t.hidden && t.getBoundingClientRect().height > 0;
  if(!bar) return { tabsShown, bar: false };
  const btn = bar.querySelector('.vroom-setup-go, .vroom-readyup-btn');
  const cs = getComputedStyle(bar), bs = getComputedStyle(btn);
  const r = bar.getBoundingClientRect();
  const a = (bs.backgroundColor.match(/[\\d.]+/g) || []);
  return { tabsShown, bar: true, blur: cs.backdropFilter || cs.webkitBackdropFilter || '', radius: parseFloat(cs.borderTopLeftRadius) > 30,
           sheen: getComputedStyle(bar, '::before').animationName, fixed: cs.position === 'fixed',
           centred: Math.abs((r.left + r.right) / 2 - innerWidth / 2) <= 1, bottom: Math.round(innerHeight - r.bottom),
           btnAlpha: a.length > 3 ? +a[3] : 1, bgImg: bs.backgroundImage !== 'none', label: btn.textContent.trim(),
           inert: btn.classList.contains('is-inert') || btn.disabled }; }"""


def check_vroom(br):
    """7. "When in virtual room lobby, the button tab should not be there,
    it should not be there when you are selecting the units for the
    virtual room lobby either. So revert that but make the match settings
    button how it was just better but give it to the button tab vibe." """
    print("\n7. no tab bar on Match settings or in the lobby; the action on its own pill in the tab bar's glass")
    for label, w, h in (PHONE, TABLET):
        ctx, pg = booted(br, w, h, seed=USED, init=ROOM_FAKE)
        pg.evaluate(CLEAN); pg.evaluate("() => { __useRooms(); store.seenUnitSelectTour = true; store.seenUnitHoldTip = true; }")
        pg.evaluate("() => showVirtualRoomSetup()"); pg.wait_for_timeout(1000)
        a = pg.evaluate(VR_BAR)
        ok_a = a["bar"] and not a["tabsShown"] and a["fixed"] and a["centred"] and "blur(30px)" in a["blur"] and a["radius"] \
            and a["sheen"] not in ("none", "") and a["inert"] and a["btnAlpha"] < 0.2
        check("%s: picking units - no tab bar; a centred glass pill (the tab bar's 30px blur, its sheen); the button unlit (326: the Start pill's own grey, was clear glass) until a unit is picked" % label,
              ok_a, a)
        early = None
        if a.get("bar"):
            tap_at(pg, "#stage > .vroom-setup-bar .vroom-setup-go"); pg.wait_for_timeout(500)
            early = pg.evaluate("() => ({ toast: (document.querySelector('.toast') || {}).textContent || '', sheet: !(document.getElementById('unitoptions-modal') || { hidden: true }).hidden })")
            pg.evaluate("() => document.querySelector('.picks .pick input').click()"); pg.wait_for_timeout(800)
            # MOVED IN 326: the pill now holds its unlit grey through the
            # fill's .3s by an ANIMATION (vroom-bar-hold, step-end) rather
            # than lighting at once, so its lit colour arrives when that
            # animation has run - on a loaded machine its start was still
            # pending at 800ms (measured: grey at 270ms with currentTime 0,
            # lit at 807ms). The lit look is read once the lighting is over.
            try:
                pg.wait_for_function("() => { const b = document.querySelector('#stage > .vroom-setup-bar .vroom-setup-go'); return !b || !b.classList.contains('is-lighting'); }", timeout=6000)
            except Exception:
                pass
        b = pg.evaluate(VR_BAR)
        opened = False
        if b.get("bar"):
            tap_at(pg, "#stage > .vroom-setup-bar .vroom-setup-go"); pg.wait_for_timeout(700)
            opened = pg.evaluate("() => !(document.getElementById('unitoptions-modal') || { hidden: true }).hidden")
        check("%s: pressed early it says to select units and opens nothing; with a unit it lights (filled) and opens the sheet" % label,
              bool(early) and "unit" in early["toast"].lower() and not early["sheet"] and b.get("bar") and not b["inert"]
              and b["btnAlpha"] > 0.9 and opened, {"early": early, "lit": b, "opened": opened})
        pg.evaluate("() => { const m = document.getElementById('unitoptions-modal'); if(m) m.hidden = true; }")
        # the lobby, as host and as a guest
        pg.evaluate("(a) => (%s)(a[0], a[1])" % B323V_ROOM, [4, "race"]); pg.wait_for_timeout(1300)
        L = pg.evaluate(VR_BAR)
        rd = None
        if L.get("bar"):
            tap_at(pg, "#stage > .vroom-setup-bar .vroom-readyup-btn"); pg.wait_for_timeout(800)
            rd = pg.evaluate("() => ({ doc: !!(((__rooms.ROOM323 || {}).participants || {})[vroomMyKey] || {}).ready, cls: document.querySelector('.vroom-readyup-btn').className })")
        check("%s: the lobby - no tab bar; Ready up on the same glass pill, lit; a tap readies you and turns it green" % label,
              L["bar"] and not L["tabsShown"] and "blur(30px)" in L["blur"] and "ready" in L["label"].lower()
              and not L["inert"] and L["btnAlpha"] > 0.9 and bool(rd) and rd["doc"] and "is-ready" in rd["cls"], {"bar": L, "tap": rd})
        ctx.close()


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cb.CHROME)
        try:
            only = os.environ.get("ONLY_FN")
            fns = [check_settings_and_soundtest, check_auto_advance_fair, check_pause_save,
                   check_stats, check_mode_colours, check_units, check_vroom]
            for f in fns:
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
