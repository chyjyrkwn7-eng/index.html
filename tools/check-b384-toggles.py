#!/usr/bin/env python3
"""384.134 (toggles): every toggle switch is iOS 26's, at iOS 26's speeds, all of them the same.
Madison, with a screen recording of iOS 26's own switches: "These toggle switches are great. I feel like our toggle switches
aren't the same, ours change at different speeds and stuff. Update that. Make it perfect."
Measured off his recording at 60fps (3px a point): a 64x28pt track, a 37x24pt capsule knob; a tap: glass in ~3 frames, swollen
in ~6, the glass crosses in ~17 (280ms) while the colour fades over the same 17 on the same curve, and the solid knob is back
in ~5 frames AS IT LANDS, its size settling on a small spring.
Every toggle on the toggle screens (Settings > Study, Motion & Effects, Sound & Haptics, Leaderboard & Privacy; the Drill start
sheet), an installed iPhone 17 Pro Max (440x956, 2x, CDP touches), read off the page:
 T1 the same box everywhere: a 64x28 track (+-1) and a capsule knob 37x24 (+-1, w/h 1.4-1.7), identical on every toggle;
 T2 one speed: on every toggle the track colour's transition and the knob's are the same duration and curve (a flip with no
    glass); with the glass, a tap's glide and its colour fade are one duration and one curve, a whole crossing 250-320ms, the
    swell <= 130ms, and the solid knob comes back as the glass lands (its fade ends within 0-160ms after the glide), not
    before it; and every toggle's tap reads the same numbers;
 T3 a press turns the knob to glass: a lens >= 1.3x the knob's width, its solid face gone (opacity <= .1) and the pixels
    under the knob's middle no longer the white knob;
 T4 a release settles back: the lens gone, the knob solid at the other end, the control flipped once;
 T5 a drag across flips it, the glass under the finger mid-drag (+-6px, inside the travel);
 T6 ON is the theme's colour (a probe painted with --switch-on) in Default, Amethyst and Sapphire;
 T7 Reduce motion: a tap flips it with no glass and nothing animating;
 T8 a switch to a screen reader (role=switch, its checked state) and to a keyboard (Space flips it); the row is >= 44px tall;
 T9 no long task over 50ms at 4x CPU from a press to the end of a drag's settle;
 T10 no page errors.
Run:  TMPDIR=/dev/shm python3 tools/check-b384-toggles.py [--against OLD/index.html]   (must FAIL on 384.133: 64x30 / 39x26,
a 190ms swell, the colour on a linear ramp, the solid knob back half-way along the glide, a 250ms colour vs a 300ms knob)"""
import io, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b384-sliders.py")).read().split("\nwith sync_playwright() as pw:")[0]
argv = sys.argv[:]
G = {"__file__": os.path.join(HERE, "check-b384-sliders.py"), "__name__": "toggles"}; exec(src, G)
sys.argv = argv
from playwright.sync_api import sync_playwright
from PIL import Image
ok = True; fails = 0
def chk(name, cond, info=""):
    global ok, fails
    ok = ok and bool(cond); fails += 0 if cond else 1
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  -> " + str(info)[:500]), flush=True)
touch, shot, px, dist, rgb, open_page, COMMON = G["touch"], G["shot"], G["px"], G["dist"], G["rgb"], G["open_page"], G["COMMON"]

SCREENS = [
  ("Study", "async()=>{ ${C} __sl.calm(); store.seenSettingsTour = true; showAppearance({ page: 'study' }); await __sl.wait(900); return 'ok'; }"),
  ("Motion", "async()=>{ ${C} __sl.calm(); store.seenSettingsTour = true; showAppearance({ page: 'motion' }); await __sl.wait(900); return 'ok'; }"),
  ("Sound", "async()=>{ ${C} __sl.calm(); store.seenSettingsTour = true; theme.soundOn = false; showAppearance({ page: 'sound' }); await __sl.wait(900); return 'ok'; }"),
  ("Leaderboard", "async()=>{ ${C} __sl.calm(); store.seenSettingsTour = true; showAppearance({ page: 'rankings' }); await __sl.wait(900); return 'ok'; }"),
  ("Start sheet", """async()=>{ ${C} __sl.calm(); document.getElementById('unitoptions-modal')?.remove();
     cfg.mode='drill'; cfg.source='all'; cfg.timer='off'; showSetup(); await __sl.wait(900);
     const picks = [...document.querySelectorAll('.pick input')]; if(!picks.length) return 'nounit'; picks.slice(0, 2).forEach(c => { c.checked = true; c.dispatchEvent(new Event('change', { bubbles: true })); }); await __sl.wait(300);
     document.getElementById('nextbtn').click(); await __sl.wait(1400); return document.querySelector('.unitoptions-modal-sheet.is-setup') ? 'ok' : 'nosheet'; }"""),
]
# every visible toggle: its track, its knob (::after), its control; skipped: disabled / locked ones (they do not move)
LIST = """()=>{ const out = [];
  document.querySelectorAll('.opt > .box, .nsw').forEach((t, i) => { const r = t.getBoundingClientRect(); if(!(r.width > 0 && r.height > 0)) return;
    const row = t.closest('.opt'), cb = row && row.querySelector(':scope > input[type=checkbox]'), btn = t.closest('[role="switch"]');
    const ctl = cb || btn; if(!ctl) return;
    const a = getComputedStyle(t, '::after'), b = getComputedStyle(t, '::before');
    const rr = (row || btn).getBoundingClientRect();
    out.push({ i, name: ((row || btn).textContent || '').trim().slice(0, 28), l: r.left, t: r.top, w: r.width, h: r.height, cx: r.left + r.width / 2, cy: r.top + r.height / 2,
      kw: parseFloat(a.width), kh: parseFloat(a.height), kl: parseFloat(a.left), kt: parseFloat(a.top),
      aT: a.transitionProperty + '|' + a.transitionDuration + '|' + a.transitionTimingFunction,
      bT: b.transitionProperty + '|' + b.transitionDuration + '|' + b.transitionTimingFunction,
      on: cb ? cb.checked : btn.getAttribute('aria-checked') === 'true', off: cb ? (cb.disabled || row.classList.contains('is-locked') || row.classList.contains('locked')) : !!btn.disabled,
      role: ctl.getAttribute('role') || (ctl.tagName === 'BUTTON' ? '' : ''), rowH: rr.height, vis: r.top > 70 && r.bottom < innerHeight - 90 });
  });
  return out; }"""
# what the tap is doing right now: the lens's glide, the colour's fade, the swell, the solid face's fade
LENS = """(i)=>{ const t = [...document.querySelectorAll('.opt > .box, .nsw')][i]; const L = t && t.querySelector('.nsw-lens'); if(!L) return null;
  const body = L.querySelector('.nsw-lens-body'), solid = L.querySelector('.nsw-lens-solid'), glass = L.querySelector('.nsw-lens-glass'), fill = L.querySelector('.nsw-lens-fill');
  const tr = el => { const cs = getComputedStyle(el); return cs.transitionProperty + '|' + cs.transitionDuration + '|' + cs.transitionTimingFunction; };
  const an = el => el.getAnimations().map(a => { const tm = a.effect.getTiming(); return { d: tm.duration, dl: tm.delay, e: tm.easing, p: a.playState }; });
  const before = getComputedStyle(t, '::before');
  const r = body.getBoundingClientRect();
  return { lens: tr(L), fill: tr(fill), nswT: t.style.getPropertyValue('--nsw-t'), beforeT: before.transitionDuration + '|' + before.transitionTimingFunction,
    body: an(body), solid: an(solid), glass: an(glass), bw: r.width, bh: r.height, bcx: r.left + r.width / 2,
    solidOp: +getComputedStyle(solid).opacity, glassOp: +getComputedStyle(glass).opacity }; }"""

def ms(v):
    v = (v or "").strip()
    return float(v[:-2]) if v.endswith("ms") else float(v[:-1]) * 1000 if v.endswith("s") else None

def parse_tr(s):
    p, d, e = (s or "||").split("|")
    return [x.strip() for x in p.split(",")], [ms(x) for x in d.split(",")], [x.strip() for x in re.split(r",(?![^(]*\))", e)]

def run():
    with sync_playwright() as pw:
        srv, G["URL"] = G["g"]["serve"]()
        br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
        ctx, pg, cdp, errs = open_page(br)
        boxes, taps = [], []
        for label, js in SCREENS:
            r = pg.evaluate(js.replace("${C}", COMMON)); pg.wait_for_timeout(300)
            lst = pg.evaluate(LIST)
            print("\n  %s: %s, %d toggles" % (label, r, len(lst)))
            if r != "ok" or not lst:
                chk(label + " opens with toggles", False, r); continue
            for t in lst:
                boxes.append((label, t))
            # T2 (no glass): the colour and the knob at one speed
            same = [(round(parse_tr(t["aT"])[1][0] or 0), parse_tr(t["aT"])[2][0], round(parse_tr(t["bT"])[1][0] or 0), parse_tr(t["bT"])[2][0]) for t in lst]
            chk(label + " T2a a flip with no glass: the colour and the knob move at one speed", all(a == c and b == d for a, b, c, d in same), same[:3])
            # the toggles to tap: visible, live
            live = [t for t in lst if not t["off"] and t["vis"]]
            if not live:
                pg.evaluate("()=>{ const t = [...document.querySelectorAll('.opt > .box, .nsw')].find(x => x.getBoundingClientRect().width > 0); t && t.scrollIntoView({ block: 'center' }); }"); pg.wait_for_timeout(400)
                lst = pg.evaluate(LIST); live = [t for t in lst if not t["off"] and t["vis"]]
            for t in live[:2]:
                img0 = shot(pg)
                kx = t["l"] + t["kl"] + t["kw"] / 2 + (t["w"] - t["kw"] - 2 * t["kl"] if t["on"] else 0)
                knob0 = px(img0, kx, t["cy"])
                touch(cdp, "touchStart", t["cx"], t["cy"]); pg.wait_for_timeout(25)
                early = pg.evaluate(LENS, t["i"])
                pg.wait_for_timeout(170)
                pressed = pg.evaluate(LENS, t["i"]); img1 = shot(pg)
                touch(cdp, "touchEnd", 0, 0); pg.wait_for_timeout(30)
                rel = pg.evaluate(LENS, t["i"])
                pg.wait_for_timeout(900)
                after = [x for x in pg.evaluate(LIST) if x["i"] == t["i"]]
                after = after[0] if after else None
                # a toggle tapped here may be Reduce motion itself: put it back, the rest of the gate needs the glass
                calmed = pg.evaluate("()=>{ const was = !!theme.reduceMotion; if(was){ theme.reduceMotion = false; applyTheme(); } return was; }")
                lensGone = pg.evaluate("(i)=>{ const t = [...document.querySelectorAll('.opt > .box, .nsw')][i]; return !t.querySelector('.nsw-lens'); }", t["i"])
                if not calmed: taps.append((label, t, early, pressed, rel))
                nm = "%s '%s'" % (label, t["name"])
                if not (early and pressed):
                    chk(nm + " T3 a press puts out the glass", False, {"early": early, "pressed": pressed}); continue
                under = px(img1, kx, t["cy"])
                chk(nm + " T3 a press turns the knob to glass", pressed["bw"] >= 1.3 * t["kw"] and pressed["solidOp"] <= .1 and dist(under, knob0) > 40,
                    {"lens w": pressed["bw"], "knob w": t["kw"], "solid": pressed["solidOp"], "knob px": knob0, "pressed px": under})
                swell = max([a["d"] for a in early["body"]] or [0])
                chk(nm + " T2b the swell <= 130ms", 0 < swell <= 130, early["body"])
                if calmed:
                    print("  (this switch is Reduce motion itself: turning it on makes its own flip instant, by design - T2c/T2d not read)")
                elif rel:
                    lp, ld, le = parse_tr(rel["lens"]); fp, fd, fe = parse_tr(rel["fill"])
                    glide = ld[lp.index("transform")] if "transform" in lp else None
                    gease = le[lp.index("transform")] if "transform" in lp else None
                    fdur = fd[fp.index("opacity")] if "opacity" in fp else None
                    fease = fe[fp.index("opacity")] if "opacity" in fp else None
                    tdur = ms(rel["nswT"]); bdur, bease = rel["beforeT"].split("|", 1)
                    chk(nm + " T2c the glide and the colour: one duration, one curve, 250-320ms",
                        glide and 250 <= glide <= 320 and glide == fdur == tdur and gease == fease == bease.strip(),
                        {"glide": [glide, gease], "lens colour": [fdur, fease], "track colour": [tdur, bease]})
                    sol = [a for a in rel["solid"] if a["p"] != "finished"]
                    end = max([a["dl"] + a["d"] for a in sol] or [0])
                    chk(nm + " T2d the solid knob comes back as the glass lands (0-160ms after the glide)", glide and glide <= end + 30 and end <= (glide or 0) + 160,
                        {"glide": glide, "solid back at": end, "solid": sol})
                else:
                    chk(nm + " T2c a tap glides with the glass", False, rel)
                chk(nm + " T4 let go: flipped once, the glass gone, the knob solid", after and after["on"] != t["on"] and lensGone, {"before": t["on"], "after": after and after["on"], "lensGone": lensGone})
        if taps:
            sig = lambda e, p, r: (r and r["lens"], r and r["fill"], r and r["nswT"], e and tuple((a["d"], a["e"]) for a in e["body"]), r and tuple((a["d"], a["e"]) for a in r["solid"]))
            sigs = {sig(e, p, r) for _, _, e, p, r in taps}
            chk("T2e every toggle's tap has the same timings", len(sigs) == 1, list(sigs)[:3])
        # T1: one box
        W = {(round(t["w"], 1), round(t["h"], 1), round(t["kw"], 1), round(t["kh"], 1)) for _, t in boxes}
        chk("T1 every toggle the same box (%d toggles)" % len(boxes), len(W) == 1, W)
        t0 = boxes[0][1] if boxes else None
        chk("T1 the iOS 26 size: a 64x28 track, a 37x24 capsule knob", t0 and abs(t0["w"] - 64) <= 1 and abs(t0["h"] - 28) <= 1 and abs(t0["kw"] - 37) <= 1 and abs(t0["kh"] - 24) <= 1 and 1.4 <= t0["kw"] / t0["kh"] <= 1.7,
            t0 and [t0["w"], t0["h"], t0["kw"], t0["kh"]])
        # T8: a11y and target
        bad = [(l, t["name"]) for l, t in boxes if t["role"] != "switch" and not t["name"].startswith("Open")]
        chk("T8a every toggle is role=switch", not bad, bad[:5])
        small = [(l, t["name"], round(t["rowH"])) for l, t in boxes if t["rowH"] < 44]
        chk("T8b every toggle's row is a >= 44px target", not small, small[:5])
        # keyboard: Space on the start sheet's first live toggle
        r = pg.evaluate(SCREENS[0][1].replace("${C}", COMMON)); pg.wait_for_timeout(300)
        lst = [t for t in pg.evaluate(LIST) if not t["off"]]
        pg.evaluate("(i)=>{ const t = [...document.querySelectorAll('.opt > .box, .nsw')][i]; const row = t.closest('.opt'); (row.querySelector(':scope > input[type=checkbox]')).focus(); }", lst[0]["i"])
        pg.keyboard.press("Space"); pg.wait_for_timeout(700)
        k2 = [x for x in pg.evaluate(LIST) if x["i"] == lst[0]["i"]][0]
        chk("T8c Space flips a focused toggle", k2["on"] != lst[0]["on"], [lst[0]["on"], k2["on"]])
        # T5: a drag across
        pg.evaluate("()=>{ const t = [...document.querySelectorAll('.opt > .box')].find(x => { const c = x.parentElement.querySelector(':scope > input'); return x.getBoundingClientRect().width > 0 && c && !c.disabled; }); t.scrollIntoView({ block: 'center' }); }"); pg.wait_for_timeout(400)
        lst = [t for t in pg.evaluate(LIST) if not t["off"] and t["vis"]]
        t = lst[0]; on0 = t["on"]
        x0 = t["l"] + t["kl"] + t["kw"] / 2 + (t["w"] - t["kw"] - 2 * t["kl"] if on0 else 0)
        x1 = t["l"] + t["kl"] + t["kw"] / 2 + (0 if on0 else t["w"] - t["kw"] - 2 * t["kl"])
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4}); pg.evaluate("()=>{ window.__lt = []; }")
        touch(cdp, "touchStart", x0, t["cy"]); pg.wait_for_timeout(120)
        mid = (x0 + x1) / 2
        for k in range(1, 9): touch(cdp, "touchMove", x0 + (mid - x0) * k / 8, t["cy"]); pg.wait_for_timeout(16)
        pg.wait_for_timeout(60)
        m = pg.evaluate(LENS, t["i"])
        for k in range(1, 9): touch(cdp, "touchMove", mid + (x1 - mid) * k / 8, t["cy"]); pg.wait_for_timeout(16)
        touch(cdp, "touchEnd", 0, 0); pg.wait_for_timeout(900)
        lt = pg.evaluate("()=>window.__lt.slice()")
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
        a2 = [x for x in pg.evaluate(LIST) if x["i"] == t["i"]][0]
        chk("T5 a drag across flips it, the glass under the finger", m and abs(m["bcx"] - mid) <= 6 and a2["on"] != on0, {"glass": m and m["bcx"], "finger": mid, "before": on0, "after": a2["on"]})
        chk("T9 no long task over 50ms at 4x CPU, press to settle", all(d <= 50 for d in lt), [round(d) for d in lt])
        # T6: ON is the theme's colour
        for nm, acc in (("Default", "ink"), ("Amethyst", "elite"), ("Sapphire", "adept")):
            pg.evaluate("(a)=>{ theme.accent = a; theme.mode = 'dark'; applyTheme(); }", acc); pg.wait_for_timeout(500)
            lst = [t for t in pg.evaluate(LIST) if t["vis"] and t["on"]]
            if not lst:
                chk("T6 an ON toggle to read (%s)" % nm, False); continue
            t = lst[0]; img = shot(pg)
            probe = pg.evaluate("()=>{ const p = document.createElement('div'); p.style.cssText = 'position:fixed;left:-50px;top:0;width:4px;height:4px;background:var(--switch-on)'; document.body.appendChild(p); const c = getComputedStyle(p).backgroundColor; p.remove(); return c; }")
            got = px(img, t["l"] + 8, t["cy"])
            chk("T6 ON is the theme's colour: " + nm, dist(got, rgb(probe)) <= 60, {"on": got, "theme": probe})
        # T7: Reduce motion
        pg.evaluate("()=>{ theme.reduceMotion = true; theme.accent = 'elite'; applyTheme(); }"); pg.wait_for_timeout(400)
        lst = [t for t in pg.evaluate(LIST) if not t["off"] and t["vis"]]
        t = lst[0]
        touch(cdp, "touchStart", t["cx"], t["cy"]); pg.wait_for_timeout(60)
        rm = pg.evaluate(LENS, t["i"])
        touch(cdp, "touchEnd", 0, 0); pg.wait_for_timeout(40)
        anim = pg.evaluate("(i)=>{ const t = [...document.querySelectorAll('.opt > .box, .nsw')][i]; return document.getAnimations().filter(a => a.effect && a.effect.target && (a.effect.target === t || t.contains(a.effect.target))).length; }", t["i"])
        pg.wait_for_timeout(500)
        a3 = [x for x in pg.evaluate(LIST) if x["i"] == t["i"]][0]
        chk("T7 Reduce motion: no glass, nothing animating, flipped", rm is None and anim == 0 and a3["on"] != t["on"], {"lens": rm, "anims": anim, "flipped": a3["on"] != t["on"]})
        chk("T10 no page errors", not errs, errs)
        br.close()

run()
print("\nALL PASS" if ok else "\n%d FAILED" % fails)
sys.exit(0 if ok else 1)
