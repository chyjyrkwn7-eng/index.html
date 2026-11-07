"""Build 384: Fire Code's 25 and 150 made cooler - the Extinguisher puts out a fire, Hazmat washes a spill off and goes off.
Madison, having watched both: "The hazmat one could be cooler I think. Could we try to make it cooler?" and "The fire
extinguisher one, I don't think I love that one, could we make it a little cooler too?"
Each effect plays in the Fire Code class on a stand-in 100% card (iPhone 17 Pro Max 440x956 and iPad 834x1194), every
animation paused and seeked - the layer over the box (Hazmat's) too - and everything is read off the page:
Extinguisher (the fireworks rung)
 (X1) IGNITION: the 100% is on fire from the start - within half a second at least five flames burn on the box's floor
      (their feet on its bottom edge), reaching up past its middle;
 (X2) AT THE BASE: through the sweep the stream's far end sits on the box's bottom edge - never short of it by more
      than 6% of the box's height, never more than 20% into it (behind the lifted box) - swept across at least 60% of its
      width;
 (X3) BEATEN DOWN A STEP AT A TIME: most front flames are knocked down to a lower level and a lower one again before
      they go out; every flame is out at one moment before the sputter ends;
 (X4) THE STUBBORN ONE: after that moment exactly one flame comes back, and it is out for good within half a second of
      the sputter's end;
 (X5) THE 100% SMOKES: once it is lit, wisps rise off the top of the number - in the box and, over its top edge, on
      the screen;
 (X6) the score catches fire with it (an onset at the ignition) and the stubborn flame's comeback is heard (an onset
      within 60ms of it); the screen and the box together stay under 170 pieces on a phone;
Hazmat (the ufo rung)
 (Z1) THE SPILL: a toxic film covers most of the box by the lock;
 (Z2) THE WASH: the decon's first pass carries the film's edge across the box with the spray - the box covered as the
      pass starts, the edge within a quarter of the box of the spray's far end mid-pass, the box clean as it ends;
 (Z3) THE FAN: the spray is a fan at least 0.4 as wide as it is long (round 5's lance was 0.3);
 (Z4) SPARKS: at least eight sparks fly out from the placard's slam;
 (Z5) THE ALL CLEAR GOES OFF: a flash across the screen on it (none just before), rays turning behind the box, the
      clean 100% popping (a copy of it over 1.08x, back to 1x within .4s), and the vapour left over BLOWN AWAY - out
      from the box by a fifth of the screen's width within .4s (round 5's drifted off on its own) and gone within .65s;
 (Z6) the small box (a tile's stage) has the spill and washes it off;
Both: only transform and opacity animate on these pieces and no page errors.
Run:  python3 tools/check-b384-fxcool.py   (--against OLD/index.html must FAIL)"""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b384-extspr.py")).read().split("\nsrv, port = serve()")[0]
G = {"__file__": os.path.join(HERE, "check-b384-extspr.py"), "__name__": "b384fxcool"}
exec(src, G)
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:600], flush=True)

# the parts by sprite (a redraw is still found: the sprite functions are called on the page), the layer over the box held
# and seeked with the rest
LAB2 = r"""() => {
  const U = u => { const m = /url\("?(.*?)"?\)\s*$/.exec(u || ''); return m ? m[1] : ''; };
  const G = window.__G;
  G.play2 = (id, small) => {
    const info = G.play(id, small);
    return new Promise(res => setTimeout(() => {
      const tops = [...document.querySelectorAll('.hfx-ufo-top')];
      tops.forEach(t => { t.style.visibility = 'visible'; t.style.zIndex = 2147480003; G.lab.appendChild(t); });
      const extra = document.getAnimations().filter(a => { const t = a.effect && a.effect.target; return t && tops.some(x => x.contains(t)); });
      extra.forEach(a => { try{ a.pause(); a.currentTime = 0; }catch(e){} });
      G.anims = G.anims.concat(extra); G.top = tops[0] || null;
      const S = ifxSpr, K = {}, add = (k, f) => { try{ const x = U(f()); if(x) K[x] = k; }catch(e){} };
      [0, 1, 2, 3].forEach(k => add('flame', () => S.flame(k)));
      [0, 1].forEach(k => add('steam', () => S.steam(k)));
      add('jet', () => S.jet()); add('spray', () => S.hzSpray()); add('fume0', () => S.hzFume(0)); add('fume1', () => S.hzFume(1)); add('fume2', () => S.hzFume(2));
      add('slime', () => S.hzSlime()); add('spark', () => S.hzSpark()); add('rays', () => S.hzRays()); add('quad', () => S.quad(0));
      const roots = [G.h.screen, G.h.box, G.top].filter(Boolean);
      G.P = {}; roots.forEach((r, ri) => r.querySelectorAll('*').forEach(e => { const k = K[U(e.style.backgroundImage)]; if(k){ (G.P[k] = G.P[k] || []).push(e); e.__layer = ri; } }));
      info.counts = Object.fromEntries(Object.entries(G.P).map(([k, v]) => [k, v.length]));
      info.pieces = roots.reduce((n, r) => n + r.querySelectorAll('*').length, 0);
      info.props2 = [...new Set(G.anims.flatMap(a => a.effect.getKeyframes ? a.effect.getKeyframes().flatMap(k => Object.keys(k)) : []))].filter(p => ['offset', 'computedOffset', 'easing', 'composite'].indexOf(p) < 0).sort();
      res(info); }, 60));
  };
  G.box = () => { const r = G.card.getBoundingClientRect(); return { l: r.left, t: r.top, r: r.right, b: r.bottom, w: r.width, h: r.height, cx: (r.left + r.right) / 2, cy: (r.top + r.bottom) / 2 }; };
  G.R = e => { const r = e.getBoundingClientRect(); return { l: r.left, t: r.top, r: r.right, b: r.bottom, w: r.width, h: r.height, cx: (r.left + r.right) / 2, cy: (r.top + r.bottom) / 2 }; };
  /* a point on an element (fractions of its own box), on the screen, through every transform */
  G.pt = (e, fx, fy) => { const p = document.createElement('i'); p.style.cssText = 'position:absolute;left:' + (fx * 100) + '%;top:' + (fy * 100) + '%;width:0;height:0;'; e.appendChild(p); const r = p.getBoundingClientRect(); p.remove(); return { x: r.left, y: r.top }; };
  return true;
}"""

def at(pg, t, js):
    return pg.evaluate("([t, body]) => { __G.seek(t); return eval(body)(); }", [t, js])

srv, port = G["serve"]()
R = {}
with G["sync_playwright"]() as pw:
    br = pw.chromium.launch(executable_path=G["CHROME"])
    for W, H in ((440, 956), (834, 1194)):
        phone = W == 440
        ctx, pg, errs = G["open_page"](br, port, W, H)
        pg.evaluate(LAB2)
        if pg.evaluate("() => window.NOVA_CLASS") != "ifc": chk("the page is in the Fire Code class", False); break
        for fx in ("fireworks", "ufo"):
            pg.evaluate("(id) => __G.warm(id)", fx)
            for _ in range(40):
                if pg.evaluate("(id) => __G.warmed(id)", fx): break
                pg.wait_for_timeout(150)
        pg.evaluate("([W, H]) => __G.setup(W, H)", [W, H])
        r = R[W] = {}
        # ---------------- the Extinguisher ----------------
        info = r["ext"] = pg.evaluate("() => __G.play2('fireworks')")
        T = pg.evaluate("() => (typeof EXT_T !== 'undefined') ? EXT_T.big : { on: .86, sput: 2.7, off: 2.95, tot: 5.0 }")
        lit = pg.evaluate("() => __G.lit()") or 3.19
        box = pg.evaluate("() => __G.box()")
        # the flames in the box, front and back; the front row is the shorter one, its wrapper the flame's parent
        FL = """() => (__G.P.flame || []).filter(e => __G.h.box && __G.h.box.contains(e)).map(e => { const w = e.parentElement, r = __G.R(w); return [__G.op(w), r.t, r.b, r.h, r.cx]; })"""
        f05 = at(pg, .45, FL)
        r["ign"] = sum(1 for o, t, b, h, cx in f05 if o > .5 and b >= box["b"] - box["h"] * .12 and t <= box["cy"])
        # X2: the stream's far end (its wrapper's right end) through the sweep
        ends = []
        for i in range(12):
            t = T["on"] + .3 + (T["sput"] - T["on"] - .4) * i / 11
            e = at(pg, t, "() => { const j = (__G.P.jet || [])[0]; return j ? __G.pt(j, 1, .5) : null; }")
            if e: ends.append(e)
        r["ends"] = [(round(e["x"]), round(e["y"])) for e in ends]
        r["ends_y"] = [round(min((box["b"] - e["y"]) for e in ends) / box["h"], 3), round(max((box["b"] - e["y"]) for e in ends) / box["h"], 3)] if ends else [9, 9]
        r["ends_x"] = (max(e["x"] for e in ends) - min(e["x"] for e in ends)) / box["w"] if ends else 0
        # X3: each flame's level over time (its wrapper's height while shown), and the moment every one is out
        samp = []
        t = T["on"] - .1
        while t <= T["sput"] + .5:
            samp.append((round(t, 2), at(pg, t, FL))); t += .04
        nfl = len(f05)
        peak = [max((v[j][3] for tt, v in samp if v[j][0] > .5), default=0) for j in range(nfl)]
        steps = 0
        for j in range(nfl):
            rel = [v[j][3] / peak[j] for tt, v in samp if v[j][0] > .5 and peak[j] > 0 and tt <= T["sput"] - .3]
            if any(.55 < x < .8 for x in rel) and any(.25 < x < .52 for x in rel): steps += 1
        r["steps"] = [steps, nfl]
        allout = next((tt for tt, v in samp if 2.0 <= tt <= T["sput"] + .2 and all(x[0] < .05 for x in v)), None)
        r["allout"] = allout
        back = [tt for tt, v in samp if allout and tt > allout and sum(1 for x in v if x[0] > .5) >= 1]
        r["back"] = [min(back), max(back)] if back else None
        r["back_n"] = max((sum(1 for x in v if x[0] > .5) for tt, v in samp if allout and tt > allout), default=0)
        r["late"] = sum(1 for x in at(pg, T["sput"] + .5, FL) if x[0] > .05)
        # X5: the smoke off the number, in the box and over its top edge
        SM = """() => { const pr = __G.pct.getBoundingClientRect(); return (__G.P.steam || []).map(e => { const r = __G.R(e); return [__G.op(e), r.cx, r.b, __G.h.box.contains(e) ? 'box' : 'scr', pr.left, pr.right, pr.top]; }); }"""
        s1, s2 = at(pg, lit + .2, SM), at(pg, lit + .9, SM)
        r["smoke_box"] = sum(1 for (o, cx, b, L, pl, prr, pt), (o2, cx2, b2, L2, *_ ) in zip(s1, s2) if L == "box" and pl - 4 <= cx <= prr + 4 and o2 > .25 and b2 < b - 6)
        r["smoke_scr"] = sum(1 for o, cx, b, L, pl, prr, pt in s2 if L == "scr" and o > .2 and b < box["t"] + 30 and pl - 4 <= cx <= prr + 4)
        r["ext_pieces"] = info["pieces"]; r["ext_props"] = info["props2"]
        # X6: the score's onsets
        if phone:
            sc = pg.evaluate("() => __G.score('fireworks', 587.33)")
            stub = pg.evaluate("() => (typeof extFire === 'function') ? extFire(EXT_T.big).stub : null")
            r["ign_onset"] = next((o for o in sc["on"] if o <= .1), None)
            r["stub"] = stub
            r["relit_onset"] = next((o for o in sc["on"] if stub and abs(o - stub["relit"]) <= .06), None)
        # ---------------- Hazmat ----------------
        pg.evaluate("([W, H]) => __G.setup(W, H)", [W, H])
        hi = r["hz"] = pg.evaluate("() => __G.play2('ufo')")
        Z = pg.evaluate("() => (typeof IFX_HZ !== 'undefined') ? IFX_HZ : { slam: 1.74, lock: 2.64, sweep: [3.86, 4.48, 4.96], clear: 5.15 }")
        box = pg.evaluate("() => __G.box()")
        # Z1: the film over the box at the lock
        r["film"] = at(pg, Z["lock"] + .1, "() => (__G.P.slime || []).filter(e => __G.h.box.contains(e)).map(e => { const r = __G.R(e); return [__G.op(e), r.t, r.b]; })")
        r["film_ok"] = any(o > .8 and (min(b, box["b"]) - max(t, box["t"])) >= box["h"] * .6 for o, t, b in r["film"])
        # Z2: the window's left edge against the spray's far end through the first pass
        WE = """() => { const s = (__G.P.slime || []).find(e => __G.h.box.contains(e)); const sp = (__G.P.spray || [])[0];
          if(!s) return null; const win = s.parentElement && s.parentElement.parentElement; const wl = win ? win.getBoundingClientRect().left : null;
          return [wl, sp ? __G.pt(sp, 0, .5).x : null, __G.op(s)]; }"""
        a0, am, a1 = at(pg, Z["sweep"][0] + .02, WE), at(pg, (Z["sweep"][0] + Z["sweep"][1]) / 2, WE), at(pg, Z["sweep"][1] + .03, WE)
        r["wash"] = [a0, am, a1]
        r["wash_ok"] = bool(a0 and am and a1 and a0[0] is not None and a0[0] <= box["l"] + box["w"] * .05 and am[1] is not None and abs(am[0] - am[1]) <= box["w"] * .25 and a1[0] >= box["r"] - box["w"] * .05)
        # Z3: the fan
        r["fan"] = pg.evaluate("() => { const sp = (__G.P.spray || [])[0]; return sp ? +(sp.offsetHeight / sp.offsetWidth).toFixed(3) : 0; }")
        # Z4: sparks off the slam
        SP = """() => { const q = (__G.P.quad || [])[0]; const c = q ? q.parentElement.getBoundingClientRect() : null; const cx = c ? (c.left + c.right) / 2 : 0, cy = c ? (c.top + c.bottom) / 2 : 0;
          return (__G.P.spark || []).map(e => { const r = __G.R(e); return [__G.op(e), Math.hypot(r.cx - cx, r.cy - cy)]; }); }"""
        k1, k2 = at(pg, Z["slam"] + .06, SP), at(pg, Z["slam"] + .24, SP)
        r["sparks"] = sum(1 for (o, d), (o2, d2) in zip(k1, k2) if o2 > .5 and d2 > d + 10)
        # Z5: the all clear
        FLASH = """() => [...__G.top.querySelectorAll('*')].filter(e => { const r = e.getBoundingClientRect(); return r.width >= innerWidth * .9 && r.height >= innerHeight * .9 && !e.style.backgroundImage.startsWith('url') && /gradient/.test(e.style.background || e.style.backgroundImage); }).map(e => +__G.op(e).toFixed(2))"""
        fb, fa = (at(pg, Z["clear"] - .05, FLASH) if pg.evaluate("() => !!__G.top") else []), (at(pg, Z["clear"] + .05, FLASH) if pg.evaluate("() => !!__G.top") else [])
        r["flash"] = [max(fb, default=0), max(fa, default=0)]
        r["rays"] = at(pg, Z["clear"] + .25, "() => (__G.P.rays || []).filter(e => __G.h.screen.contains(e)).map(e => { const r = __G.R(e); return [+__G.op(e).toFixed(2), Math.round(r.cx), Math.round(r.cy)]; })")
        r["rays_ok"] = any(o >= .5 and abs(cx - box["cx"]) <= 3 and abs(cy - box["cy"]) <= 3 for o, cx, cy in r["rays"])
        POP = """() => [...__G.h.box.querySelectorAll('i')].filter(e => e.textContent && /100/.test(e.textContent) && !e.closest('.hfx-lit')).map(e => [+__G.op(e).toFixed(2), +__G.sx(e).toFixed(3)])"""
        p1, p2 = at(pg, Z["clear"] + .05, POP), at(pg, Z["clear"] + .4, POP)
        r["pop"] = [p1, p2]
        r["pop_ok"] = any(o > .8 and s >= 1.08 for o, s in p1) and all(abs(s - 1) < .01 for o, s in p2 if o > .5)
        FU = """() => { const b = __G.box(); return ['fume0', 'fume1', 'fume2'].flatMap(k => __G.P[k] || []).map(e => { const r = __G.R(e); return [__G.op(e), Math.hypot(r.cx - b.cx, r.cy - b.cy)]; }); }"""
        v0, v1, v2 = at(pg, Z["clear"] - .05, FU), at(pg, Z["clear"] + .35, FU), at(pg, Z["clear"] + .65, FU)
        moving = [(b[1] - a[1]) for a, b in zip(v0, v1) if a[0] > .1]
        r["blown"] = [len(moving), round(sum(moving) / len(moving), 1) if moving else None, sum(1 for x in v2 if x[0] > .05), round(W * .2)]
        r["hz_props"] = hi["props2"]
        # Z6: the small box
        if phone:
            pg.evaluate("([W, H]) => __G.setup(W, H)", [W, H])
            pg.evaluate("() => __G.play2('ufo', true)")
            SL = "() => (__G.P.slime || []).filter(e => __G.h.box.contains(e)).map(e => +__G.op(e).toFixed(2))"
            r["small"] = [at(pg, 1.9, SL), at(pg, 3.4, SL)]
        r["errs"] = list(errs)
        ctx.close()
    br.close()
srv.shutdown()
P, I = R[440], R[834]
print("phone:", json.dumps(P)[:3000]); print("ipad:", json.dumps(I)[:1500])
for tag, r in (("phone", P), ("iPad", I)):
    chk("(X1 %s) IGNITION: %d flames burn on the box's floor, up past its middle, by .45s (at least 5)" % (tag, r["ign"]), r["ign"] >= 5, r["ign"])
    chk("(X2 %s) AT THE BASE: the stream's end lies %s of the box's height into it from its bottom edge (-.06 to .2), swept across %.2f of its width (at least .6)" % (tag, r["ends_y"], r["ends_x"]),
        r["ends_y"][0] >= -.06 and r["ends_y"][1] <= .2 and r["ends_x"] >= .6, r["ends"])
    chk("(X3 %s) BEATEN DOWN: %d of %d flames knocked down a step and another before they go out (at least half), all out at %ss (before the sputter ends)" % (tag, r["steps"][0], r["steps"][1], r["allout"]),
        r["steps"][1] >= 6 and r["steps"][0] * 2 >= r["steps"][1] and r["allout"] is not None, (r["steps"], r["allout"]))
    chk("(X4 %s) THE STUBBORN ONE: after that, %d flame comes back (%s) and none is left %d" % (tag, r["back_n"], r["back"], r["late"]),
        r["back_n"] == 1 and r["back"] and r["late"] == 0, (r["back_n"], r["back"], r["late"]))
    chk("(X5 %s) THE 100%% SMOKES: %d wisps rise off the top of the number in the box, %d run on over its top edge (at least 2 each)" % (tag, r["smoke_box"], r["smoke_scr"]),
        r["smoke_box"] >= 2 and r["smoke_scr"] >= 2, (r["smoke_box"], r["smoke_scr"]))
chk("(X6) the score catches fire with it (an onset at %s) and the comeback is heard (%s against %s); %d pieces on the screen and in the box on a phone (at most 170)" % (
    P.get("ign_onset"), P.get("relit_onset"), (P.get("stub") or {}).get("relit"), P["ext_pieces"]),
    P.get("ign_onset") is not None and P.get("relit_onset") is not None and P["ext_pieces"] <= 170, (P.get("ign_onset"), P.get("relit_onset"), P.get("stub"), P["ext_pieces"]))
for tag, r in (("phone", P), ("iPad", I)):
    chk("(Z1 %s) THE SPILL: a toxic film covers most of the box by the lock (%s)" % (tag, r["film"]), r["film_ok"], r["film"])
    chk("(Z2 %s) THE WASH: the film's edge goes across the box with the spray's first pass (window left / spray end / film at its start, middle, end: %s)" % (tag, r["wash"]), r["wash_ok"], r["wash"])
    chk("(Z3 %s) THE FAN: the spray is %.2f as wide as it is long (at least .4)" % (tag, r["fan"]), r["fan"] >= .4, r["fan"])
    chk("(Z4 %s) SPARKS: %d fly out from the slam (at least 8)" % (tag, r["sparks"]), r["sparks"] >= 8, r["sparks"])
    chk("(Z5 %s) THE ALL CLEAR GOES OFF: a flash across the screen %.2f (before it %.2f), rays behind the box %s, the 100%% pops %s" % (tag, r["flash"][1], r["flash"][0], r["rays"][:1], r["pop"]),
        r["flash"][1] >= .6 and r["flash"][0] < .05 and r["rays_ok"] and r["pop_ok"], (r["flash"], r["rays"], r["pop"]))
    chk("(Z5 %s) ...and the vapour BLOWN AWAY: %d banks still there move %s px out from the box in .4s, %d left .65s on (at least 4, at least %dpx - a fifth of the screen - none)" % (tag, r["blown"][0], r["blown"][1], r["blown"][2], r["blown"][3]),
        r["blown"][0] >= 4 and (r["blown"][1] or 0) >= r["blown"][3] and r["blown"][2] == 0, r["blown"])
chk("(Z6) the small box has the spill and washes it off (film %s at the lock, %s after the wash)" % tuple(P["small"]), any(o > .5 for o in P["small"][0]) and all(o < .05 for o in P["small"][1]) and P["small"][0], P["small"])
props = sorted(set(P["ext_props"]) | set(P["hz_props"]) | set(I["ext_props"]) | set(I["hz_props"]))
chk("(both) only %s animate, no page errors (%s)" % (props, (P["errs"] + I["errs"])[:2]), props == ["opacity", "transform"] and not (P["errs"] + I["errs"]), (props, P["errs"] + I["errs"]))
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
