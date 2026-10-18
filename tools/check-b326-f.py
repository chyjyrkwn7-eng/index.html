#!/usr/bin/env python3
"""Build 326, package F: the Virtual Room lobby's polish, one set of glass
surfaces app-wide, and the unit cards. Each check was written against
5869856 (build 325), where it fails, and passes on this build:

  python3 tools/check-b326-f.py
  python3 tools/check-b326-f.py --against /path/to/old-index.html
  ONLY_FN=check_ready_ring python3 tools/check-b326-f.py

Madison's words (Oct 18) are quoted in front of each section. The helpers
(booted, the Firestore stub, the fake rooms) are check-behaviour's, loaded
without running it. Exits non-zero on any failure.
"""
import importlib.util
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py"))
cb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cb)   # reads --against from sys.argv itself

from playwright.sync_api import sync_playwright
from PIL import Image

check, booted, USED, PHONE, TABLET = cb.check, cb.booted, cb.USED_ACCOUNT, cb.PHONE, cb.TABLET
ROOM_FAKE = cb._ROOM_FAKE
CLEAN = ("() => { document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove());"
         " __useRooms(); store.seenUnitSelectTour = true; store.seenUnitHoldTip = true; }")
ACCENTS = ["ink", "rookie", "ranger", "veteran", "vanguard", "adept", "elite", "titan"]
GREEN = (61, 214, 140)
# A theme, applied after the screen is up as well as before (a mount can re-apply the stored one)
SET_ACCENT = ("(a) => { theme.accent = a; applyTheme(); if(a === 'ink') delete document.documentElement.dataset.accent;"
              " else document.documentElement.dataset.accent = a; }")

# A lobby of n people: the first other person is not ready and everybody
# after them is, so the LAST card is always a ready one (the :last-child
# case). A room where everyone is ready starts, so for two people it is the
# other person who is ready and you who are not.
LOBBY = """(o) => {
  const me = publicIdOf();
  const NAMES = ['Avery','Jordan','Kim','Pat','Lee','Ray','Jose','Tara','Brooke','Dee','Fay','Hana','Quinn','Ana','Bo','Cy','Di','Ed','Flo','Gus'];
  const CH = ['zeus','alien','ghost','wizard','dragon','queen','samurai','grizzly','ninja'];
  const parts = {}; parts[me] = { name: 'Madison', avatarChar: 'ninja', level: 41, badges: 6, joinedAt: 1, seen: 9e15, ready: !!o.meReady, accent: 'ink' };
  const keys = [];
  for(let i = 0; i < o.n - 1; i++){ const k = 'pF' + String(i).padStart(10, '0'); keys.push(k);
    parts[k] = { name: NAMES[i], avatarChar: CH[i % CH.length], level: 10 + 3 * i, badges: i % 8, joinedAt: 100 + i, seen: 9e15,
                 ready: o.n === 2 ? true : (i !== 0) }; }
  const host = me;
  __rooms['ROOM326'] = { hostCode: host, hostName: host === me ? 'Madison' : NAMES[0], units: ['Identity Crimes'], versions: {}, game: 'race',
    open: false, status: 'waiting', mode: 'exam', createdAt: 1, count: null, participants: parts };
  __delay = 40;
  vroomCode = 'ROOM326'; vroomMyKey = me; vroomIsHost = host === me; vroomUnits = __rooms.ROOM326.units;
  vroomLastDoc = { code: 'ROOM326', data: JSON.parse(JSON.stringify(__rooms.ROOM326)) };
  showVirtualRoomLobby();
}"""


def tap_at(pg, sel):
    r = pg.evaluate("(s) => { const e = document.querySelector(s); if(!e) return null; const b = e.getBoundingClientRect();"
                    " return { x: b.left + b.width / 2, y: b.top + b.height / 2 }; }", sel)
    if r:
        pg.mouse.click(r["x"], r["y"])
    return bool(r)


def near(c, ref, tol=40):
    return all(abs(c[i] - ref[i]) <= tol for i in range(3))


# --------------------------------------------------------------------------
RING = """() => {
  const rgb = c => (String(c).match(/[\\d.]+/g) || []).map(Number);
  const isGreen = c => { const v = rgb(c); return v.length >= 3 && Math.abs(v[0]-61) < 12 && Math.abs(v[1]-214) < 12 && Math.abs(v[2]-140) < 12 && (v.length < 4 || v[3] > .9); };
  return [...document.querySelectorAll('.vroom-roster-list .vroom-row')].map(r => {
    const s = getComputedStyle(r), b = r.getBoundingClientRect();
    const sides = ['Top','Right','Bottom','Left'].map(k => ({ c: isGreen(s['border' + k + 'Color']), w: parseFloat(s['border' + k + 'Width']) }));
    /* a spread ring outside the border box, in the ready green */
    const spread = /rgb\\(61, 214, 140\\) 0px 0px 0px 1(\\.\\d+)?px/.test(s.boxShadow);
    /* nothing between the row and the roster clips the outside of it */
    let clipped = false;
    for(let a = r.parentElement; a && !a.classList.contains('vroom-roster'); a = a.parentElement){
      const as = getComputedStyle(a); if(as.overflow !== 'visible' || as.overflowX !== 'visible'){ const ab = a.getBoundingClientRect();
        if(b.left - ab.left < 2 || ab.right - b.right < 2 || b.top - ab.top < 2) clipped = true; } }
    return { ready: r.classList.contains('is-ready'), you: r.classList.contains('is-you'), sides, spread, clipped,
             x: b.left, y: b.top, w: b.width, h: b.height, radius: parseFloat(s.borderTopLeftRadius) };
  }); }"""


def ring_pixels(pg, rows):
    """Sample the pixel ring 1px OUTSIDE each ready row's border box, along
    all four sides and at the four corners' 45-degree points: every sample
    has to be the ready green (the ring is drawn whole, nothing covers it)."""
    img = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
    W, H = img.size
    bad = []
    for i, r in enumerate(rows):
        if not r["ready"] or r["y"] < 0 or r["y"] + r["h"] > H - 140:
            continue
        x0, y0, x1, y1 = r["x"], r["y"], r["x"] + r["w"], r["y"] + r["h"]
        rad = r["radius"]
        pts = []
        for f in (0.3, 0.5, 0.7):
            pts += [(x0 + r["w"] * f, y0 - 0.5), (x0 + r["w"] * f, y1 + 0.5 - 1), (x0 - 0.5, y0 + r["h"] * f), (x1 + 0.5 - 1, y0 + r["h"] * f)]
        k = 0.2929  # 1 - cos 45
        for cx, cy, sx, sy in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
            pts.append((cx + sx * (rad * k - 0.3) - (1 if sx < 0 else 0), cy + sy * (rad * k - 0.3) - (1 if sy < 0 else 0)))
        for (px, py) in pts:
            # the brightest-green pixel in a 3x3 around the point: the ring is 2px, anti-aliased at the curve
            best = None
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    xx, yy = int(round(px)) + dx, int(round(py)) + dy
                    if 0 <= xx < W and 0 <= yy < H:
                        c = img.getpixel((xx, yy))
                        if best is None or c[1] - (c[0] + c[2]) / 2 > best[1] - (best[0] + best[2]) / 2:
                            best = c
            if not best or not near(best, GREEN, 70):
                bad.append((i, round(px), round(py), best))
    return bad


def check_ready_ring(br):
    """1. "The virtual room, when ready up is set not everyone has a green
    outline and if they do it's not fully there." On 325: the last card had
    no bottom border (a :last-child rule from the list days), your own card
    in a full room kept its accent edge instead of green, and the ring was a
    1px border at 55% that the card's clipped banner art could cut into."""
    print("\n1. every ready player's card has the whole green ring - self and others, 2/4/8/20 players, both devices")
    for label, w, h in (PHONE, TABLET):
        for n in (2, 4, 8, 20):
            ctx, pg = booted(br, w, h, seed=USED, init=ROOM_FAKE)
            pg.evaluate(CLEAN)
            pg.evaluate("(o) => (%s)(o)" % LOBBY, {"n": n, "meReady": n != 2})
            pg.wait_for_timeout(1400)
            rows = pg.evaluate(RING)
            ready = [r for r in rows if r["ready"]]
            css_ok = bool(ready) and all(all(s["c"] and s["w"] >= 1 for s in r["sides"]) and r["spread"] and not r["clipped"] for r in ready)
            not_ready_plain = all(not any(s["c"] for s in r["sides"]) for r in rows if not r["ready"])
            you = [r for r in rows if r["you"]]
            last_ok = bool(rows) and rows[-1]["ready"] and rows[-1]["sides"][2]["w"] >= 1 and rows[-1]["sides"][2]["c"]
            # the page scrolled so the roster is in view, then the pixels
            pg.evaluate("() => { const l = document.querySelector('.vroom-roster-list'); if(l) window.scrollTo({ top: l.getBoundingClientRect().top + scrollY - 90, behavior: 'instant' }); }")
            pg.wait_for_timeout(350)
            bad = ring_pixels(pg, pg.evaluate(RING))
            check("%s, %d players: all %d ready cards ringed green on all four sides with the outer spread, unclipped; self too; the last card's bottom edge; the not-ready plain"
                  % (label, n, len(ready)),
                  css_ok and not_ready_plain and you and (n == 2 or (you[0]["ready"] and you[0]["sides"][0]["c"])) and last_ok,
                  {"bad": [(i, r["sides"], r["spread"], r["clipped"]) for i, r in enumerate(rows) if r["ready"] and not (all(s["c"] for s in r["sides"]) and r["spread"])][:4],
                   "last": rows[-1] if rows else None})
            check("%s, %d players: the ring is green in the PIXELS all the way round every visible ready card (sides and corners)" % (label, n),
                  not bad and bool(ready), bad[:6])
            if n == 4:
                # readying and un-readying: the ring arrives whole and leaves whole
                pg.evaluate("() => { const P = __rooms.ROOM326.participants[vroomMyKey]; P.ready = false; vroomLastDoc = { code:'ROOM326', data: JSON.parse(JSON.stringify(__rooms.ROOM326)) }; showVirtualRoomLobby(); }")
                pg.wait_for_timeout(1300)
                frames = []
                tap_at(pg, "#stage > .vroom-setup-bar .vroom-readyup-btn")
                for _ in range(14):
                    frames.append(pg.evaluate("""() => { const r = document.querySelector('.vroom-row.is-you'); if(!r) return 'none';
                      const s = getComputedStyle(r); const g = ['Top','Right','Bottom','Left'].map(k => /61, 214, 140/.test(s['border'+k+'Color']) && !/0\\.\\d+\\)/.test(s['border'+k+'Color']));
                      return g.every(Boolean) && /61, 214, 140\\) 0px 0px 0px 1/.test(s.boxShadow) ? 'full' : g.some(Boolean) ? 'part' : 'off'; }"""))
                    pg.wait_for_timeout(45)
                tap_at(pg, "#stage > .vroom-setup-bar .vroom-readyup-btn")
                pg.wait_for_timeout(900)
                off = pg.evaluate("() => { const r = document.querySelector('.vroom-row.is-you'); return r && !r.classList.contains('is-ready') && !/61, 214, 140/.test(getComputedStyle(r).borderTopColor); }")
                check("%s: tapping Ready up rings your card whole (never part-drawn) and tapping again takes it off whole" % label,
                      "part" not in frames and frames[-1] == "full" and off, {"frames": frames, "off": off})
            ctx.close()


# --------------------------------------------------------------------------
ACCESS = """() => {
  const L = document.querySelector('.screen-vroom-lobby') || document.getElementById('stage');
  const groups = [...L.querySelectorAll('[role="radiogroup"]')];
  const g = groups[0];
  const radios = g ? [...g.querySelectorAll('[role="radio"]')] : [];
  const line = g ? (g.parentElement.querySelector('.vroom-access-line') || g.nextElementSibling) : null;
  /* the old shape: a control named one thing with a different state printed under its name */
  const oldSwitch = !!L.querySelector('.vroom-open-toggle, .vroom-open-hint');
  const bgA = el => { const m = (getComputedStyle(el).backgroundColor.match(/[\\d.]+/g) || []).map(Number); return m.length > 3 ? m[3] : (m.length ? 1 : 0); };
  return { n: groups.length, radios: radios.map(r => ({ t: r.textContent.trim(), on: r.getAttribute('aria-checked') === 'true',
             h: r.getBoundingClientRect().height, a: bgA(r), col: getComputedStyle(r).color })),
           line: line ? line.textContent.trim() : '', oldSwitch, open: vroomIsOpen }; }"""


def check_access(br):
    """2. "The toggle for open room is confusing because it says open room and
    then invite only under it?" On 325 it was a switch named "Open room" with
    its state, "Invite only", printed underneath."""
    print("\n2. who can join: two options, one lit, a line saying what the current one means")
    for label, w, h in (PHONE, TABLET):
        ctx, pg = booted(br, w, h, seed=USED, init=ROOM_FAKE)
        pg.evaluate(CLEAN)
        pg.evaluate("(o) => (%s)(o)" % LOBBY, {"n": 3, "meReady": False})
        pg.wait_for_timeout(1300)
        a = pg.evaluate(ACCESS)
        shape = (a["n"] == 1 and len(a["radios"]) == 2 and sum(r["on"] for r in a["radios"]) == 1 and not a["oldSwitch"]
                 and all(r["h"] >= 44 for r in a["radios"]) and len(a["line"]) > 10)
        lit = [r for r in a["radios"] if r["on"]]
        unlit = [r for r in a["radios"] if not r["on"]]
        distinct = bool(lit and unlit) and lit[0]["a"] > unlit[0]["a"] + 0.1 and lit[0]["col"] != unlit[0]["col"]
        check("%s: one radio group of two options (44px each), exactly one checked, no switch with a contradicting sub-label" % label, shape, a)
        check("%s: the chosen option is raised and lit, the other quiet" % label, distinct, a["radios"])
        # choose the other one: the room's `open` flips, the line changes, the lit one moves
        other = next((i for i, r in enumerate(a["radios"]) if not r["on"]), None)
        b = None
        if other is not None:
            pg.evaluate("(i) => document.querySelectorAll('[role=radiogroup] [role=radio]')[i].click()", other)
            pg.wait_for_timeout(400)
            b = pg.evaluate(ACCESS)
            b["doc"] = pg.evaluate("() => (__rooms.ROOM326 || {}).open")
        check("%s: choosing the other option writes the room open/closed, moves the light and changes the line" % label,
              bool(b) and b["open"] != a["open"] and b["doc"] == b["open"] and b["line"] != a["line"] and len(b["line"]) > 10
              and [r["on"] for r in b["radios"]] == [not r["on"] for r in a["radios"]], {"before": a, "after": b})
        ctx.close()


# --------------------------------------------------------------------------
STYLE = """(s) => { const e = document.querySelector(s); if(!e) return null; const c = getComputedStyle(e);
  return { bg: c.backgroundColor, bgi: c.backgroundImage, color: c.color, sh: c.boxShadow, bf: c.backdropFilter, op: c.opacity,
           before: getComputedStyle(e, '::before').animationName, cls: e.className }; }"""


def check_bar_unlit(br):
    """3. "The bottom tab is a lot better, but the button when not selected is
    Liquid Glass and not the same look as the normal start button when not lit
    up, fix that." On 325 the Virtual Room bar's not-yet button was the tab
    bar's clear lens; a test's unit screen shows its Start pill in grey."""
    print("\n3. the Virtual Room bar's not-yet button is the Start pill's unlit look, and it lights the same way")
    for label, w, h in (PHONE, TABLET):
        for acc in ("ink", "titan"):
            ctx, pg = booted(br, w, h, seed=USED, init=ROOM_FAKE)
            pg.evaluate(CLEAN)
            SET = SET_ACCENT
            pg.evaluate("() => { cfg.mode = 'drill'; cfg.units = []; showSetup(); }"); pg.wait_for_timeout(1200)
            pg.evaluate(SET, acc); pg.wait_for_timeout(200)
            ref = pg.evaluate(STYLE, "#bottomtab-start")
            pg.evaluate("() => showVirtualRoomSetup()"); pg.wait_for_timeout(1200)
            pg.evaluate(SET, acc); pg.wait_for_timeout(200)
            vr = pg.evaluate(STYLE, "#stage > .vroom-setup-bar .vroom-setup-go")
            same = bool(ref and vr) and "is-inert" in ref["cls"] and "is-inert" in vr["cls"] and all(ref[k] == vr[k] for k in ("bg", "bgi", "color", "sh"))
            check("%s, %s: unlit, it is the tab bar's inert Start exactly (fill, image, words, depth)" % (label, acc), same, {"start": ref, "vr": vr})
            # light it: the grey holds while the fill grows from the centre, then it is lit
            # the whole beat, frame by frame in the page: the grey under the
            # growing fill first, then the accent, and never the grey again
            fr = pg.evaluate("""async () => { const b = document.querySelector('#stage > .vroom-setup-bar .vroom-setup-go'); const out = [];
              const t0 = performance.now(); document.querySelector('.picks .pick input').click();
              while(performance.now() - t0 < 1300){ await new Promise(r => requestAnimationFrame(r));
                const c = getComputedStyle(b); out.push({ t: Math.round(performance.now() - t0), bg: c.backgroundColor, before: getComputedStyle(b, '::before').animationName, cls: b.className }); }
              return out; }""")
            acc_col = pg.evaluate("() => { const p = document.createElement('i'); p.style.color = 'var(--accent)'; document.body.appendChild(p); const c = getComputedStyle(p).color; p.remove(); return c; }")
            grey_fill = [f for f in fr if f["bg"] == ref["bg"] and f["before"] == "start-fill-in"]
            first_lit = next((i for i, f in enumerate(fr) if f["bg"] == acc_col), None)
            flash = first_lit is not None and any(f["bg"] != acc_col for f in fr[first_lit:])
            check("%s, %s: lit by a tap, the grey holds while the fill grows from the centre (as Start's), then the accent - and no flash back" % (label, acc),
                  bool(grey_fill) and first_lit is not None and not flash and "is-lighting" not in fr[-1]["cls"] and acc_col != ref["bg"],
                  {"accent": acc_col, "frames": [(f["t"], f["bg"], f["before"]) for f in fr[::4]][:16]})
            ctx.close()


# --------------------------------------------------------------------------
def contrast(c1, c2):
    def lum(c):
        v = []
        for x in c[:3]:
            x /= 255
            v.append(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4)
        return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]
    a, b = lum(c1), lum(c2)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


def rgba(s):
    import re
    v = [float(x) for x in re.findall(r"[\d.]+", s or "")]
    if "color(srgb" in (s or ""):
        v = [v[0] * 255, v[1] * 255, v[2] * 255] + v[3:]
    return v + [1.0] * (4 - len(v)) if len(v) < 4 else v


def check_match_settings(br):
    """4. "The lobby, the match settings button is a weird color?" On 325 it
    was a 55%-see-through dark fill with a blue and a pink edge and no frost
    of its own, so its colour was the card's tint behind it - different on
    every theme."""
    print("\n4. Match settings is the app's secondary button: one opaque colour, Invite friends' own, on every theme")
    for label, w, h in (PHONE, TABLET):
        for acc in ACCENTS if label == PHONE[0] else ("ink", "titan"):
            ctx, pg = booted(br, w, h, seed=USED, init=ROOM_FAKE)
            pg.evaluate(CLEAN)
            pg.evaluate("(a) => { theme.accent = a; applyTheme(); }", acc)
            pg.evaluate("(o) => (%s)(o)" % LOBBY, {"n": 3, "meReady": False})
            pg.wait_for_timeout(1300)
            pg.evaluate(SET_ACCENT, acc); pg.wait_for_timeout(200)
            ms = pg.evaluate(STYLE, ".vroom-settings-btn")
            inv = pg.evaluate(STYLE, ".vroom-invite-btn")
            ok = bool(ms and inv) and ms["bg"] == inv["bg"] and rgba(ms["bg"])[3] == 1 and ms["bgi"] == "none" and ms["color"] == inv["color"]
            cr = contrast(rgba(ms["color"]), rgba(ms["bg"])) if ms else 0
            check("%s, %s: Match settings is opaque, the same fill and words as Invite friends (the secondary button), contrast %.1f:1" % (label, acc, cr),
                  ok and cr >= 7, {"ms": ms, "invite": inv})
            ctx.close()


# --------------------------------------------------------------------------
SURF = """(sels) => {
  const out = {};
  for(const s of sels){ const els = [...document.querySelectorAll(s)].filter(e => e.getBoundingClientRect().height > 0);
    out[s] = els.map(e => { const c = getComputedStyle(e); return { bg: c.backgroundColor, bgi: c.backgroundImage, bf: c.backdropFilter, bd: c.borderTopColor }; }); }
  const tok = {}; const p = document.createElement('i'); document.body.appendChild(p);
  for(const t of ['--surface-1', '--surface-2', '--surface-lift']){ p.style.backgroundColor = 'var(' + t + ')'; tok[t] = p.style.backgroundColor ? getComputedStyle(p).backgroundColor : null; }
  p.remove(); return { out, tok }; }"""
# the boxes on each screen that must be ONE family of surfaces
SURF_SCREENS = [
    ("Settings", "() => showProfile('settings')", [".settings-card", ".slab.motion-summary"]),
    ("the Virtual Room lobby", "LOBBY", [".vroom-test-summary", ".vroom-roster"]),
    ("the start sheet", "() => { cfg.mode = 'exam'; cfg.units = ['Penal Code', 'Identity Crimes']; showSetupWithSheet(); }",
     [".unitoptions-modal-sheet .optionsmodal-body > .sect", ".unitoptions-modal-sheet .bank-rows", ".unitoptions-modal-sheet .timer-sect", ".unitoptions-modal-sheet .sheet-summary"]),
    ("the mode picker", "() => showModeSelect()", [".modecard"]),
    ("the unit screen", "() => { cfg.mode = 'drill'; showSetup(); }", [".picks > label.pick:not(.pick-checked)", ".searchbox"]),
    ("Stats", "() => showProfile('stats')", [".stat-card", ".points-progress-sect"]),
    ("Customize", "() => showCustomize()", [".cz-row"]),
    ("Friends", "() => showFriends()", [".friend-sect"]),
    ("the Virtual Room's first screen", "() => showVirtualRoomChoice()", [".modecard"]),
]


def check_surfaces(br):
    """5. "The interface of the app is starting to become hard to see because
    of all the Liquid Glass ... Like the lobby for exam some of the boxes are
    darker which is nice but some aren't? ... like the settings menu, the
    Liquid Glass is very glass like, could be better, maybe darker?" On 325
    the boxes were eleven recipes: Settings' cards a 3.5% white wash with no
    frost, the lobby's two boxes 40% glass and 20% black, the common card a
    40% fill under a blur that saturated and brightened what was behind it."""
    print("\n5. one set of surfaces: every box on a screen is a token, dark enough to read on, frosted without boosting")
    ctx, pg = booted(br, 440, 956, seed=USED, init=ROOM_FAKE)
    pg.evaluate(CLEAN)
    for name, show, sels in SURF_SCREENS:
        if show == "LOBBY":
            pg.evaluate("(o) => (%s)(o)" % LOBBY, {"n": 4, "meReady": False})
        else:
            pg.evaluate(show)
        pg.wait_for_timeout(1300)
        r = pg.evaluate(SURF, sels)
        toks = [t for t in r["tok"].values() if t]
        # a wrapper with no fill of its own (the sheet's Timer group: its card is the .timer-sect inside) is not a box
        found = [(s, e) for s, els in r["out"].items() for e in els if rgba(e["bg"])[3] > 0 or e["bgi"] != "none"]
        bgs = set(e["bg"] for _, e in found)
        on_token = bool(found) and len(toks) == 3 and all(e["bg"] in toks for _, e in found)
        # a screen's boxes of one kind share one surface; page cards are dark and opaque enough to read on
        page = [e for s, e in found if "unitoptions" not in s and "motion-summary" not in s and "searchbox" not in s]
        dark = all(rgba(e["bg"])[3] >= 0.6 and sum(rgba(e["bg"])[:3]) / 3 <= 40 for e in page)
        no_boost = all(("saturate(1.9" not in e["bf"] and "brightness(1.0" not in e["bf"] and "saturate(2" not in e["bf"]) for _, e in found)
        check("%s: every box is a surface token (%d boxes, %d fill%s), page cards dark (>=60%%, <=40 grey), no frost that boosts what is behind"
              % (name, len(found), len(bgs), "" if len(bgs) == 1 else "s"),
              on_token and dark and no_boost, {"bgs": sorted(bgs), "tok": r["tok"], "bf": sorted(set(e["bf"] for _, e in found))})
        pg.evaluate("() => { const m = document.getElementById('unitoptions-modal'); if(m) m.hidden = true; }")
    ctx.close()
    # the two lobby boxes and the start sheet's boxes: ONE colour each
    ctx, pg = booted(br, 834, 1194, seed=USED, init=ROOM_FAKE)
    pg.evaluate(CLEAN)
    pg.evaluate("(o) => (%s)(o)" % LOBBY, {"n": 4, "meReady": False})
    pg.wait_for_timeout(1300)
    lob = pg.evaluate(SURF, [".vroom-test-summary", ".vroom-roster"])["out"]
    pg.evaluate("() => { cfg.mode = 'exam'; cfg.units = ['Penal Code', 'Identity Crimes']; showSetupWithSheet(); }")
    pg.wait_for_timeout(1300)
    sh = pg.evaluate(SURF, [".unitoptions-modal-sheet .optionsmodal-body > .sect:not(.timer-sect)", ".unitoptions-modal-sheet .bank-rows",
                            ".unitoptions-modal-sheet .timer-sect", ".unitoptions-modal-sheet .sheet-summary"])["out"]
    lob_bg = set(e["bg"] for v in lob.values() for e in v)
    sh_bg = set(e["bg"] for v in sh.values() for e in v if rgba(e["bg"])[3] > 0)
    sh_bd = set(e["bd"] for v in sh.values() for e in v if rgba(e["bg"])[3] > 0)
    check("iPad: the lobby's Room setup and In this room are one surface; the start sheet's groups and its summary one lift with one hairline",
          len(lob_bg) == 1 and all(lob.values()) and len(sh_bg) == 1 and len(sh_bd) == 1, {"lobby": lob_bg, "sheet": sh_bg, "edges": sh_bd})
    # the tab bar keeps its own glass (build 323/325), the Virtual Room's bar still matches it
    pg.evaluate("() => { cfg.mode = 'drill'; showSetup(); }"); pg.wait_for_timeout(1000)
    tb = pg.evaluate("() => { const c = getComputedStyle(document.querySelector('.bottomtabs')); return [c.backdropFilter, c.borderRadius]; }")
    pg.evaluate("() => showVirtualRoomSetup()"); pg.wait_for_timeout(1000)
    vb = pg.evaluate("() => { const c = getComputedStyle(document.querySelector('.vroom-setup-bar')); return [c.backdropFilter, c.borderRadius]; }")
    check("the tab bar's glass is left alone, and the Virtual Room's bar still wears the same frost", tb[0] == vb[0] and "30px" in tb[0], {"tab": tb, "vr": vb})
    ctx.close()


CONTRAST_SCREENS = [
    ("settings", "() => showProfile('settings')"),
    ("lobby", "LOBBY"),
    ("sheet", "() => { cfg.mode = 'exam'; cfg.units = ['Penal Code', 'Identity Crimes']; showSetupWithSheet(); }"),
    ("modes", "() => showModeSelect()"),
    ("units", "() => { cfg.mode = 'drill'; showSetup(); }"),
    ("stats", "() => showProfile('stats')"),
]
TEXT_JS = r"""() => {
 const out = [];
 const parse = c => { const m = String(c).match(/[\d.]+/g) || []; let [r,g,b,a] = m.map(Number);
   if(/color\(srgb/.test(c)){ r*=255; g*=255; b*=255; } return [r,g,b,a===undefined?1:a]; };
 const SURF = '.settings-card, .slab, .pick, .stat-card, .points-progress-sect, .vroom-roster, .vroom-test-summary, .modecard, .sect, .sheet-summary, .bank-rows, .timer-sect';
 const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
 let n;
 while((n = walker.nextNode())){
   const t = n.textContent.trim(); if(!t) continue;
   const el = n.parentElement; if(!el || !el.closest(SURF)) continue;
   if(el.closest('#bottomtabs, .bottomtabs, [aria-hidden="true"], .is-disabled, [aria-disabled="true"], :disabled, .locked, .vroom-setup-bar')) continue;
   if(!el.closest('#stage, .unitoptions-modal-sheet')) continue;
   const cs = getComputedStyle(el); if(cs.visibility === 'hidden') continue;
   let op = 1; for(let e = el; e; e = e.parentElement){ op *= parseFloat(getComputedStyle(e).opacity); }
   const c = parse(cs.webkitTextFillColor && cs.webkitTextFillColor !== cs.color ? cs.webkitTextFillColor : cs.color);
   if(c[3] * op < .05 || el.getBoundingClientRect().width <= 2) continue;
   const rg = document.createRange(); rg.selectNodeContents(n);
   const rects = [...rg.getClientRects()].filter(r => r.width > 2 && r.height > 4 && r.top > 0 && r.bottom < innerHeight && r.left > 0 && r.right < innerWidth)
     .filter(r => { const top = document.elementFromPoint((r.left + r.right) / 2, (r.top + r.bottom) / 2); return top && (top === el || el.contains(top) || top.contains(el)); })
     .map(r => [r.left, r.top, r.right, r.bottom]);
   if(rects.length) out.push({ t: t.slice(0, 30), c, op, fs: parseFloat(cs.fontSize), fw: parseInt(cs.fontWeight) || 400, rects });
 }
 return out; }"""


def check_contrast(br):
    """5b. Text on the glass, measured off the rendered page on every theme:
    each run's colour against the worst (92nd percentile) background pixel
    under its own glyph boxes with every letter hidden, so the stars, the
    glow and the frost are all counted. 4.5:1, 3:1 for large text."""
    print("\n5b. text on every surface reads at 4.5:1 (3:1 large) over its worst background pixel, on every theme")
    def lum(c):
        v = []
        for x in c[:3]:
            x /= 255
            v.append(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4)
        return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]
    for acc in ACCENTS:
        worst_all = []
        for key, show in CONTRAST_SCREENS:
            ctx, pg = booted(br, 440, 956, seed=USED, init=ROOM_FAKE)
            pg.evaluate(CLEAN)
            pg.evaluate("(a) => { theme.accent = a; applyTheme(); }", acc)
            if show == "LOBBY":
                pg.evaluate("(o) => (%s)(o)" % LOBBY, {"n": 4, "meReady": True})
            else:
                pg.evaluate(show)
            pg.wait_for_timeout(1500)
            pg.evaluate(SET_ACCENT, acc); pg.wait_for_timeout(250)
            pg.evaluate("() => document.querySelectorAll('#tour-overlay,.tour-tip,#tour-tooltip,.toast').forEach(n=>n.remove())")
            texts = pg.evaluate(TEXT_JS)
            pg.evaluate("""() => { const st = document.createElement('style'); st.id = '__hide';
              st.textContent = '*{color:transparent!important;-webkit-text-fill-color:transparent!important;text-shadow:none!important}';
              document.head.appendChild(st); }""")
            pg.wait_for_timeout(200)
            img = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
            W, H = img.size
            for t in texts:
                px = []
                for (l, tp, r, b) in t["rects"]:
                    for y in range(max(0, int(tp)), min(H, int(b))):
                        for x in range(max(0, int(l)), min(W, int(r))):
                            px.append(img.getpixel((x, y)))
                if not px:
                    continue
                px.sort(key=lum)
                med = px[len(px) // 2]
                a = t["c"][3] * t["op"]
                tc = [t["c"][i] * a + med[i] * (1 - a) for i in range(3)]
                worst = px[int(len(px) * 0.92)] if lum(tc) > lum(med) else px[int(len(px) * 0.08)]
                need = 3.0 if (t["fs"] >= 24 or (t["fs"] >= 18.66 and t["fw"] >= 700)) else 4.5
                cr = contrast(tc, worst)
                if cr < need:
                    worst_all.append((key, t["t"], round(cr, 2), need))
            ctx.close()
        check("%s: every line of text on the surfaces of Settings, the lobby, the start sheet, the mode picker, the units and Stats passes" % acc,
              not worst_all, worst_all[:8])


# --------------------------------------------------------------------------
CARDS = """() => {
  const cards = [...document.querySelectorAll('.picks > label.pick')].filter(c => c.getBoundingClientRect().height > 0);
  return cards.map(c => { const b = c.getBoundingClientRect(), s = getComputedStyle(c);
    const q = sel => { const e = c.querySelector(sel); if(!e) return null; const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
      return { x: r.left - b.left, y: r.top - b.top, w: r.width, h: r.height, r: b.right - r.right, fs: parseFloat(cs.fontSize), fw: parseInt(cs.fontWeight) || 400 }; };
    return { name: (c.querySelector('.pname') || {}).textContent, top: b.top, w: b.width, h: b.height, radius: parseFloat(s.borderTopLeftRadius),
      checked: c.classList.contains('pick-checked'), shadow: s.boxShadow, stripe: getComputedStyle(c, '::before').display !== 'none' && getComputedStyle(c, '::before').backgroundColor !== 'rgba(0, 0, 0, 0)',
      box: q('.box'), badge: q('.pick-badge'), pname: q('.pname'), pcount: q('.pcount'), bar: q('.pick-bar-track'), ver: q('.pick-version') }; }); }"""


def check_unit_cards(br):
    """6. "I think the unit selection screen could still be improved. I'm
    wondering if the layout of the stuff in the box, and the interface/look
    of the boxes could be better." Still squares ("the square boxes were
    better", 325). On 325 the badge was a 34px mark squeezed into the footer
    beside its bar, the name the same weight as everything else, and a
    selected card a darker slab with a 3px stripe caught in its corner."""
    print("\n6. the unit card: circle and badge on the top line, the name the headline, footers aligned, a ring when selected")
    for label, w, h in (PHONE, TABLET, ("iPhone SE 2nd gen", 375, 667), ("iPad Pro 12.9\"", 1024, 1366)):
        ctx, pg = booted(br, w, h, seed=USED, init=ROOM_FAKE)
        pg.evaluate(CLEAN)
        pg.evaluate("""() => { store.unitPerfects = { 'Professional Policing': 15, 'Professionalism and Ethics': 5 };
          cfg.mode = 'drill'; cfg.units = ['Professional Policing']; showSetup(); }""")
        pg.wait_for_timeout(1500)
        cards = pg.evaluate(CARDS)
        rem = pg.evaluate("() => parseFloat(getComputedStyle(document.documentElement).fontSize)")
        top_line = all(c["box"] and c["badge"] and abs((c["box"]["y"] + c["box"]["h"] / 2) - (c["badge"]["y"] + c["badge"]["h"] / 2)) <= c["badge"]["h"] * 0.35
                       and c["badge"]["x"] > c["w"] / 2 and c["badge"]["r"] <= 16 and c["badge"]["w"] >= 2.4 * rem for c in cards)
        headline = all(c["pname"]["fs"] > c["pcount"]["fs"] + 1 and c["pname"]["fw"] >= 700 and c["pname"]["y"] > c["box"]["y"] + c["box"]["h"] - 1 for c in cards)
        # footers: the question counts in a row of cards share one line
        rows = {}
        for c in cards:
            rows.setdefault(round(c["top"]), []).append(c)
        aligned = all(max(abs(a["pcount"]["y"] - b["pcount"]["y"]) for a in r for b in r) <= 1 for r in rows.values())
        squares = len(rows) >= 6 and all(len(r) == 2 for r in list(rows.values())[:-1])
        radius = len(set(c["radius"] for c in cards)) == 1
        targets = all(c["h"] >= 44 and c["w"] >= 44 for c in cards)
        check("%s: every card has the circle and the badge (>=2.4rem) on its top line, the name below as the headline, two across"
              % label, top_line and headline and squares and radius and targets,
              {"first": cards[0] if cards else None, "rows": len(rows)})
        check("%s: in every row the cards' footers (question count) line up, found badge or not" % label, aligned,
              [[(c["name"][:14], round(c["pcount"]["y"])) for c in r] for r in rows.values()][:4])
        sel = [c for c in cards if c["checked"]]
        acc = pg.evaluate("() => { const p = document.createElement('i'); p.style.color = 'var(--accent)'; document.body.appendChild(p); const c = getComputedStyle(p).color; p.remove(); return c; }")
        check("%s: a selected card is ringed in the accent all the way round (a spread outside the border), with no stripe down its left" % label,
              bool(sel) and all(acc + " 0px 0px 0px 1px" in s["shadow"] and not s["stripe"] for s in sel) and not any(c["stripe"] for c in cards),
              {"sel": [(s["name"], s["shadow"][:90], s["stripe"]) for s in sel], "accent": acc})
        # the Penal Code version line stays in the name's cell, clear of the count
        pen = next((c for c in cards if (c["name"] or "").strip() == "Penal Code"), None)
        check("%s: the Penal Code version line sits under the name, clear of the question count" % label,
              bool(pen and pen["ver"]) and pen["ver"]["y"] >= pen["pname"]["y"] and pen["ver"]["y"] + pen["ver"]["h"] <= pen["pcount"]["y"] + 1,
              pen)
        if label == PHONE[0]:
            # a long press still opens the unit's details
            pt = pg.evaluate("() => { const c = document.querySelectorAll('.picks > label.pick')[3]; c.scrollIntoView({ block: 'center', behavior: 'instant' }); const b = c.getBoundingClientRect(); return { x: b.left + b.width / 2, y: b.top + b.height * .6 }; }")
            pg.wait_for_timeout(300)
            pg.mouse.move(pt["x"], pt["y"]); pg.mouse.down(); pg.wait_for_timeout(900); pg.mouse.up(); pg.wait_for_timeout(900)
            opened = pg.evaluate("() => !!document.querySelector('.unitdetail.is-open')")
            check("%s: pressing and holding a card still opens its details" % label, opened, opened)
        ctx.close()


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cb.CHROME)
        try:
            only = os.environ.get("ONLY_FN")
            fns = [check_ready_ring, check_access, check_bar_unlit, check_match_settings, check_surfaces, check_contrast, check_unit_cards]
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
