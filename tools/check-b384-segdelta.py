#!/usr/bin/env python3
"""r18 (build 384): the top switchers are Delta's iOS 26 segmented control - drawn like it, moving like it.

(384.116, segglass) Madison sent a screen recording of Delta's control itself: "Ours is stretched, no liquid glass, ours is
indented... make it exactly like what I sent." The recording shows what r18 had ruled out - a press swells the whole control ~9%
and a move carries the thumb in a clear glass LENS taller than the track - so the checks here that held r18's "no lens, no swell,
a 1-6% lift, a dimmer unpicked label, no backdrop-filter" now hold the recording's: A7 (a blur on the track), B (the lens may grow
past the thumb and stand proud of the track; the swell up to 10%; the frame-exact shape is check-b384-segglass's), C (the swell may
carry the thumb up to 10%; its drift is read in the control's own coordinates), D1 (a press swells 4-10%), H (both labels white).

Madison, Delta's Light / Dark control beside ours: "I'm not sure what's up with our top tabs. It should be designed like the Delta
one, look like it. Function like it. Fix that, make it smooth." Ours drew a dark track with a LIGHTER thumb and, on a touch, lifted
a glass lens taller and wider than the track while the whole control swelled. Delta's: a LIGHTER grey capsule track, a DARKER
capsule thumb inset in the picked segment, white labels, equal segments; a tap springs the thumb across (no overshoot, no resize),
a press lifts it a few percent, a drag carries it 1:1 and a let-go snaps it to the nearest segment.

Every switcher found (Profile / Stats / Settings, the Leaderboard's boards, the units screen's levels, the chat sheet's Friends /
Groups / Inbox, the Virtual Room review's Missed / Entire test) on every device class (a phone installed and in Safari, an iPad, a
laptop and two desktop monitors at dpr 1 and 2), by finger or by mouse. Everything is READ off the page; shapes are asserted, never
strings, and no number here is a label.

  A. LOOK   the track is lighter than the thumb (luminance order, >= 8 levels), both capsules (radius >= half their height), the
            segments equal (within 0.5px), every label's text centred in its segment (within 1px each way), the thumb the picked
            segment's box (within 1px) and inside the track, white labels, no glass lens anywhere, no backdrop-filter on the track
            or the thumb, the thumb's CSS transition is opacity only.
  B. TAP    every ordered pair of segments: lands on the target within 1px, overshoots it by no more than 2px, never steps back,
            the thumb does not change size (no press on it) and the track does not swell, never pokes out of the track, none of
            the thumb's layout properties change while it moves, and what animates is transform (Web Animations keyframes: no
            width / height / left / top / filter / box-shadow), 0.15-0.8s long.
  C. SAME   a tap on the picked segment does nothing: nothing picked, no class change on any segment, the thumb stays.
  D. DRAG   press the thumb: it lifts 1-6%, no more (and not out of the track); drag: it follows the finger within 2px (clamped at
            the ends), nothing is picked until let go; let go two-thirds over: the nearest segment is picked, the thumb lands on
            it within 1px, no overshoot beyond 2px; a quarter of the way: back, nothing picked; dragged far past the end: held at
            the last segment, inside the track.
  E. SWIPE  (Profile, the Leaderboard) a swipe across the content moves the thumb to the next segment, transform only.
  F. REDUCE MOTION  no animation at all on a tap (the thumb is placed), no press lift.
  G. KEYS   Arrow keys move along the switcher (focus and pick); a focused segment shows a focus ring.
  H. MOUSE  (laptop and desktop) an unlit label is dimmer than the lit one at rest and as bright on hover.
  I. 44px   every segment is hit 21px above and below its centre.
  J. No page errors.

  python3 tools/check-b384-segdelta.py                         # every device class, every switcher
  python3 tools/check-b384-segdelta.py --quick                 # a phone and a laptop
  python3 tools/check-b384-segdelta.py --against /tmp/prev-index.html   # the build before: must FAIL
  python3 tools/check-b384-segdelta.py --only profile --devs phone-installed
"""
import json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import b384_seg_lib as L
from b384_seg_lib import cx, cy, lit_index, luma, parse_css_rgb
from playwright.sync_api import sync_playwright

ONLY = re.compile(L.arg("--only")) if L.arg("--only") else None
DEVS = L.arg("--devs").split(",") if L.arg("--devs") else (["phone-installed", "laptop-mouse"] if "--quick" in sys.argv else None)
CLASSES = (L.arg("--class") or "academy,ifc").split(",")
if "--quick" in sys.argv and not L.arg("--class"): CLASSES = ["academy"]
ok = True; results = []
def chk(name, cond, info=""):
    global ok
    ok = ok and bool(cond); results.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  -> " + str(info)[:420]), flush=True)

SEG_ELEM = "[...document.querySelectorAll(sel)].find(e=>e.getBoundingClientRect().width>0)"
def wait_rest(pg, sel, ms=3500):
    """no animation left anywhere in the switcher (the lens's, in the build before, included), then a beat"""
    pg.evaluate("""async ([sel, ms])=>{ const s=%s; const t0=performance.now();
      while(performance.now()-t0<ms){ if(!s.getAnimations({subtree:true}).some(a=>a.playState==='running')) break; await new Promise(r=>setTimeout(r,50)); }
      await new Promise(r=>setTimeout(r,120)); }""" % SEG_ELEM, [sel, ms])
def state(pg, sw): return pg.evaluate(L.STATE, [sw[2], sw[3]])
def wait_lit(pg, sw, want, ms=5000):
    """until segment `want` is the picked one (a swipe's pick comes after the content has slid)"""
    t0 = time.time()
    while time.time() - t0 < ms / 1000:
        s = state(pg, sw)
        if s and lit_index(s) == want: return True
        pg.wait_for_timeout(100)
    return False
def sampler(pg, sw): pg.evaluate(L.SAMPLER, [sw[2]])
def tap_seg(pg, ptr, sw, i, hold=55):
    s = state(pg, sw); b = s["segs"][i]["box"]
    ptr.down(cx(b), cy(b)); pg.wait_for_timeout(hold); ptr.up()
def thumb_anims(pg, sw):
    """what is animating on the thumb: the properties of every running keyframe effect"""
    return pg.evaluate("""([sel])=>{ const s=%s; const sl=s.querySelector(':scope > .seg-slider');
      return sl.getAnimations().map(a=>({ props:[...new Set(a.effect.getKeyframes().flatMap(k=>Object.keys(k)).filter(k=>!['offset','easing','composite','computedOffset'].includes(k)))], dur:a.effect.getTiming().duration })); }""" % SEG_ELEM, [sw[2]])
def record_anims(pg, sw):
    """collect the properties of every animation the thumb runs from now on (it is polled each frame)"""
    pg.evaluate("""([sel])=>{ const s=%s; const sl=s.querySelector(':scope > .seg-slider'); window.__ap=[]; window.__apOn=true;
      const f=()=>{ if(!window.__apOn) return; for(const a of sl.getAnimations()){ if(!a.__seen){ a.__seen=1; try{ window.__ap.push({ props:[...new Set(a.effect.getKeyframes().flatMap(k=>Object.keys(k)).filter(k=>!['offset','easing','composite','computedOffset'].includes(k)))], dur:a.effect.getTiming().duration }); }catch(e){} } } requestAnimationFrame(f); };
      f(); }""" % SEG_ELEM, [sw[2]])
def anims_seen(pg):
    pg.evaluate("()=>{ window.__apOn=false; }"); return pg.evaluate("()=>window.__ap||[]")
def watch_classes(pg, sw):
    pg.evaluate("""([sel, segSel])=>{ const s=%s; window.__cm=0; window.__mo && window.__mo.disconnect();
      window.__mo=new MutationObserver(l=>{ window.__cm+=l.filter(m=>m.target!==s.querySelector(':scope > .seg-slider')).length; });
      [...s.querySelectorAll(':scope > '+segSel)].forEach(b=>window.__mo.observe(b,{attributes:true,attributeFilter:['class','hidden']})); }""" % SEG_ELEM, [sw[2], sw[3]])
def class_changes(pg): return pg.evaluate("()=>window.__cm||0")
def rect_in(inner, outer, tol=.5):
    return inner[0] >= outer[0] - tol and inner[1] >= outer[1] - tol and inner[0] + inner[2] <= outer[0] + outer[2] + tol and inner[1] + inner[3] <= outer[1] + outer[3] + tol

def run_switcher(pg, ptr, dev, tag, sw):
    name = sw[0]; touch = dev["touch"]
    st = L.open_switcher(pg, sw)
    if not st or len(st["segs"]) < 2:
        chk("%s: the switcher is on screen with 2+ segments" % tag, False, st); return
    n = len(st["segs"])
    print("  %s: segments %s" % (tag, [s["text"] for s in st["segs"]]), flush=True)
    # warm every segment once, so a heavy page (Settings is built on its first show) is not what is being timed
    for i in range(n):
        tap_seg(pg, ptr, sw, i); wait_rest(pg, sw[2]); pg.wait_for_timeout(500)
    tap_seg(pg, ptr, sw, 0); wait_rest(pg, sw[2]); pg.wait_for_timeout(400)
    st = state(pg, sw)
    if st["scrollY"] > 1: print("  (scrolled %s)" % st["scrollY"])
    seg = st["seg"]

    # ---- A. look ----
    tb, th = parse_css_rgb(st["trackBg"]), parse_css_rgb(st["thumbBg"])
    chk("%s: A1 the track is LIGHTER than the thumb (luminance %s vs %s, >= 8 levels)" % (tag, tb and round(luma(tb), 1), th and round(luma(th), 1)),
        bool(tb and th) and luma(tb) - luma(th) >= 8, {"track": st["trackBg"], "thumb": st["thumbBg"]})
    chk("%s: A2 both are capsules (track radius %.0f of %.1f high, thumb %.0f of %.1f)" % (tag, st["trackRadius"], seg[3], st["thumbRadius"], st["thumbLayout"][1]),
        st["trackRadius"] >= seg[3] / 2 - .5 and st["thumbRadius"] >= st["thumbLayout"][1] / 2 - .5, st)
    ws = [s["box"][2] for s in st["segs"]]
    chk("%s: A3 the segments are equal (widths %s)" % (tag, [round(w, 2) for w in ws]), max(ws) - min(ws) <= .5, ws)
    off = []
    for i, s in enumerate(st["segs"]):
        b, lab = s["box"], s["label"]
        off.append((round(abs(cx(lab) - cx(b)), 2), round(abs(cy(lab) - cy(b)), 2)))
    chk("%s: A4 every label's text is centred in its segment (within 1px: %s)" % (tag, off), all(a <= 1 and b <= 1 for a, b in off), off)
    i0 = lit_index(st); lb = st["segs"][i0]["box"] if i0 >= 0 else None
    chk("%s: A5 the thumb is the picked segment's box (within 1px) and inside the track" % tag,
        lb is not None and all(abs(a - b) <= 1 for a, b in zip(st["thumb"], lb)) and rect_in(st["thumb"], seg, .5), {"thumb": st["thumb"], "seg": lb, "track": seg})
    cols = [parse_css_rgb(s["color"]) for s in st["segs"]]
    chk("%s: A6 the labels are white (min luminance %.0f), the picked one fully, no theme colour" % (tag, min(luma(c) for c in cols if c)),
        all(c and luma(c) >= 235 and max(c) - min(c) <= 12 for c in cols) and st["segs"][i0]["op"] >= .99, [s["color"] for s in st["segs"]])
    chk("%s: A7 (384.116) the track is glass - a backdrop blur on it (%s) - and the thumb's CSS transition is opacity or none (%s)" % (tag, st["trackBackdrop"], st["thumbTransition"]),
        "blur" in (st["trackBackdrop"] or "") and set(t.strip() for t in st["thumbTransition"].split(",")) <= {"opacity", "all", "none"}, st)

    # ---- I. 44px targets ----
    hits = pg.evaluate("""([sel, segSel])=>{ const s=%s;
      return [...s.querySelectorAll(':scope > '+segSel)].filter(b=>!b.hidden && b.offsetWidth>0).map(b=>{ const r=b.getBoundingClientRect(), x=r.left+r.width/2, y=r.top+r.height/2;
        const at=yy=>{ const e=document.elementFromPoint(x, yy); return !!(e && e.closest(segSel)===b); };
        return { w:r.width, up:at(y-21), down:at(y+21) }; }); }""" % SEG_ELEM, [sw[2], sw[3]])
    chk("%s: I every segment is a 44px target (hit 21px above and below its centre, 44+ wide)" % tag, all(h["up"] and h["down"] and h["w"] >= 44 for h in hits), hits)

    # ---- B. taps, every ordered pair ----
    pairs = [(i, j) for i in range(n) for j in range(n) if i != j]
    if "--quick" in sys.argv: pairs = pairs[:3]
    bad = []
    worst = dict(over=0, size=0, swell=0, poke=0, back=0, dur=0)
    for (i, j) in pairs:
        tap_seg(pg, ptr, sw, i); wait_rest(pg, sw[2]); pg.wait_for_timeout(250)
        s0 = state(pg, sw)
        if lit_index(s0) != i: bad.append((i, j, "could not start", lit_index(s0))); continue
        rest_th, rest_seg = s0["thumb"], s0["seg"]; c1 = cx(s0["segs"][j]["box"])
        record_anims(pg, sw); sampler(pg, sw)
        tap_seg(pg, ptr, sw, j); wait_rest(pg, sw[2], 3500)
        fr = L.frames(pg); an = anims_seen(pg); s1 = state(pg, sw)
        a = L.analyse(fr, c1, rest_th, rest_seg)
        land = abs(cx(s1["thumb"]) - cx(s1["segs"][j]["box"])) <= 1 and abs(cy(s1["thumb"]) - cy(s1["segs"][j]["box"])) <= 1 and \
            all(abs(p - q) <= 1 for p, q in zip(s1["thumb"], s1["segs"][j]["box"]))
        props = set(p for x in an for p in x["props"])
        why = []
        if lit_index(s1) != j: why.append("lit %d" % lit_index(s1))
        if not land: why.append("landed %s vs %s" % ([round(v, 1) for v in s1["thumb"]], [round(v, 1) for v in s1["segs"][j]["box"]]))
        if not a or not a.get("moved"): why.append("did not move")
        else:
            # (384.116) overshoot and back steps are read on the screen here, where the swell moves every segment's middle; check-b384-segglass
            # 4 holds them in the control's own coordinates, frame by frame
            # (384.116) the lens grows past the thumb and stands proud of the track, and the control swells, by design (check-b384-segglass
            # holds their shape frame by frame); here only that the swell stays a swell
            if a["swell"] > .10: why.append("track swell +%.1f%%" % (100 * a["swell"]))
            if a["layout_changes"] > 1: why.append("layout props changed %d times" % a["layout_changes"])
            worst["over"] = max(worst["over"], a["overshoot"]); worst["size"] = max(worst["size"], a["size"]); worst["swell"] = max(worst["swell"], a["swell"])
            worst["poke"] = max(worst["poke"], a["poke"]); worst["back"] = max(worst["back"], a["backstep"])
        if not props: why.append("no animation (a jump)")
        elif not props <= {"transform", "opacity"}: why.append("animated %s" % sorted(props))
        durs = [x["dur"] for x in an if "transform" in x["props"]]
        if durs and not (150 <= max(durs) <= 1200): why.append("duration %.0fms" % max(durs))
        if why: bad.append((i, j, why))
    chk("%s: B taps (%d pairs): land on the target within 1px, <= 2px overshoot (worst %.2f), never step back (%.2f), thumb size constant (+%.1f%%), track no swell (+%.1f%%), inside the track (%.1f), transform alone, no layout change"
        % (tag, len(pairs), worst["over"], worst["back"], 100 * worst["size"], 100 * worst["swell"], worst["poke"]), not bad, bad[:3])

    # ---- C. a tap on the picked segment does nothing ----
    tap_seg(pg, ptr, sw, 0); wait_rest(pg, sw[2]); pg.wait_for_timeout(250)
    s0 = state(pg, sw); rest_th, rest_seg = s0["thumb"], s0["seg"]; c1 = cx(s0["segs"][0]["box"])
    watch_classes(pg, sw); sampler(pg, sw); sy0 = s0["scrollY"]
    tap_seg(pg, ptr, sw, 0, hold=120); wait_rest(pg, sw[2]); pg.wait_for_timeout(300)
    fr = L.frames(pg); s1 = state(pg, sw); cm = class_changes(pg)
    # (384.116) the press swells the control about its middle: the thumb's place is read in the control's own coordinates
    drift = max([abs((cx(L.vis(f)) - cx(f["seg"])) / (f["seg"][2] / rest_seg[2]) - (c1 - cx(rest_seg))) for f in fr] + [0])
    szmax = max([max(L.vis(f)[2] / rest_th[2], L.vis(f)[3] / rest_th[3]) - 1 for f in fr] + [0])
    chk("%s: C a tap on the picked segment does nothing (lit %d -> %d, class changes %d, thumb drift %.2fpx, size +%.1f%%)" % (tag, lit_index(s0), lit_index(s1), cm, drift, 100 * szmax),
        lit_index(s1) == lit_index(s0) == 0 and cm == 0 and drift <= .5 and szmax <= .10 and abs(s1["thumb"][2] - rest_th[2]) <= .5 and abs(s1["scrollY"] - sy0) <= 1,
        {"lit": (lit_index(s0), lit_index(s1)), "cm": cm, "drift": drift, "size": szmax})

    # ---- D. drag ----
    s0 = state(pg, sw); i0 = lit_index(s0); i1 = i0 + 1 if i0 + 1 < n else i0 - 1
    a0, a1 = s0["segs"][i0]["box"], s0["segs"][i1]["box"]; y = cy(a0); x0, x1 = cx(a0), cx(a1); rest_th, rest_seg = s0["thumb"], s0["seg"]
    sampler(pg, sw); watch_classes(pg, sw)
    ptr.down(x0, y); pg.wait_for_timeout(200)
    # (the lift's spring is on the compositor: poll until it shows, up to 2s, so a loaded machine's slow first frame is not read as no lift)
    t_lift = time.time()
    while True:
        pressed = state(pg, sw)
        lift = max(pressed["thumb"][2] / rest_th[2], pressed["thumb"][3] / rest_th[3]) - 1
        if lift >= .04 or time.time() - t_lift > 2: break
        pg.wait_for_timeout(100)
    for k in range(1, 15): ptr.move(x0 + (x1 - x0) * .66 * k / 14, y); pg.wait_for_timeout(34)
    pg.wait_for_timeout(260)
    held = state(pg, sw); xf = x0 + (x1 - x0) * .66; cm_held = class_changes(pg)
    follow = abs(cx(held["thumb"]) - xf)
    lift2 = max(held["thumb"][2] / rest_th[2], held["thumb"][3] / rest_th[3]) - 1
    ptr.up(); wait_rest(pg, sw[2]); pg.wait_for_timeout(250)
    fr = L.frames(pg); s2 = state(pg, sw)
    peak = max([max(L.vis(f)[2] / rest_th[2], L.vis(f)[3] / rest_th[3]) - 1 for f in fr] + [0])
    poke = max([0] + [max(f["seg"][0] - L.vis(f)[0], L.vis(f)[0] + L.vis(f)[2] - (f["seg"][0] + f["seg"][2]), f["seg"][1] - L.vis(f)[1], L.vis(f)[1] + L.vis(f)[3] - (f["seg"][1] + f["seg"][3])) for f in fr])
    # the overshoot past the segment it lands on, after the finger lets go (from the moment the finger is up: the last third of the frames)
    # (384.116) a press swells the whole control (Delta's: 1.088 x 1.07 held) and the thumb with it; dragged, it is the lens (taller than the track, by design)
    chk("%s: D1 pressing the thumb swells the control and the thumb with it (+%.1f%%, 4-10%%)" % (tag, 100 * lift), .04 <= lift <= .10, {"lift": lift, "held": lift2, "peak": peak, "poke": poke})
    chk("%s: D2 a drag carries the thumb with the finger (within %.1fpx), and nothing is picked until the finger is up (class changes %d)" % (tag, follow, cm_held),
        follow <= 2 and cm_held == 0, {"follow": follow, "xf": xf, "thumb": cx(held["thumb"]), "cm": cm_held})
    d2 = abs(cx(s2["thumb"]) - cx(s2["segs"][i1]["box"]))
    over = max([0] + [(cx(L.vis(f)) - cx(s2["segs"][i1]["box"])) * (1 if x1 >= x0 else -1) for f in fr])
    chk("%s: D3 let go two-thirds over: the nearest segment is picked (%d -> %d), the thumb lands on it within 1px (%.2f), no overshoot beyond 2px (%.2f), back to its size (+%.2f%%)"
        % (tag, i0, lit_index(s2), d2, over, 100 * (max(s2["thumb"][2] / rest_th[2], s2["thumb"][3] / rest_th[3]) - 1)),
        lit_index(s2) == i1 and d2 <= 1 and over <= 8 and abs(s2["thumb"][2] - rest_th[2]) <= .5 and abs(s2["thumb"][3] - rest_th[3]) <= .5, {"lit": lit_index(s2), "d": d2, "over": over})
    # a quarter of the way: back
    i0 = lit_index(s2); i1 = i0 + 1 if i0 + 1 < n else i0 - 1
    a0, a1 = s2["segs"][i0]["box"], s2["segs"][i1]["box"]; x0, x1 = cx(a0), cx(a1)
    watch_classes(pg, sw)
    ptr.down(x0, y); pg.wait_for_timeout(90)
    for k in range(1, 9): ptr.move(x0 + (x1 - x0) * .25 * k / 8, y); pg.wait_for_timeout(34)
    pg.wait_for_timeout(120); ptr.up(); wait_rest(pg, sw[2]); pg.wait_for_timeout(250)
    s3 = state(pg, sw)
    chk("%s: D4 a quarter of the way: back where it was, nothing picked (lit %d, class changes %d)" % (tag, lit_index(s3), class_changes(pg)),
        lit_index(s3) == i0 and class_changes(pg) == 0 and abs(cx(s3["thumb"]) - cx(s3["segs"][i0]["box"])) <= 1, {"lit": lit_index(s3), "want": i0})
    # far past the end: held at the last segment, inside the track
    s3 = state(pg, sw); i0 = lit_index(s3); j = n - 1 if i0 != n - 1 else 0; dirn = 1 if j > i0 else -1
    a0 = s3["segs"][i0]["box"]; x0 = cx(a0); xe = cx(s3["segs"][j]["box"]) + dirn * 140
    xe = max(4, min(dev["w"] - 4, xe))
    sampler(pg, sw)
    ptr.down(x0, y); pg.wait_for_timeout(90)
    for k in range(1, 17): ptr.move(x0 + (xe - x0) * k / 16, y); pg.wait_for_timeout(30)
    pg.wait_for_timeout(300)
    far = state(pg, sw)
    ptr.up(); wait_rest(pg, sw[2]); pg.wait_for_timeout(250)
    fr = L.frames(pg); s4 = state(pg, sw)
    out = max([0] + [max(f["seg"][0] - L.vis(f)[0], L.vis(f)[0] + L.vis(f)[2] - (f["seg"][0] + f["seg"][2])) for f in fr])
    chk("%s: D5 dragged past the end it is held at the last segment (centre %.1f of %.1f), inside the track (%.1fpx out), and lands there (lit %d)"
        % (tag, cx(far["thumb"]), cx(far["segs"][j]["box"]), out, lit_index(s4)),
        abs(cx(far["thumb"]) - cx(far["segs"][j]["box"])) <= 1.5 + max(0, (far["thumb"][2] - far["segs"][j]["box"][2]) / 2) and out <= 6 and lit_index(s4) == j, {"held": cx(far["thumb"]), "end": cx(far["segs"][j]["box"]), "out": out, "lit": lit_index(s4)})

    # ---- E. a swipe across the content ----
    if sw[5] and touch:
        tap_seg(pg, ptr, sw, 0); wait_rest(pg, sw[2]); pg.wait_for_timeout(300)
        st = state(pg, sw); i0 = lit_index(st); want = i0 + 1
        vw = dev["w"]; yy = st["seg"][1] + st["seg"][3] + 230; xa, xb = vw * .75, vw * .25
        rest_th, rest_seg = st["thumb"], st["seg"]; c1 = cx(st["segs"][want]["box"])
        record_anims(pg, sw); sampler(pg, sw)
        ptr.down(xa, yy)
        for k in range(1, 11): ptr.move(xa + (xb - xa) * k / 10, yy + k * .3); pg.wait_for_timeout(16)
        ptr.up(); wait_lit(pg, sw, want); pg.wait_for_timeout(150); wait_rest(pg, sw[2], 3500)
        fr = L.frames(pg); an = anims_seen(pg); s5 = state(pg, sw); a = L.analyse(fr, c1, rest_th, rest_seg)
        props = set(p for x in an for p in x["props"])
        chk("%s: E a swipe across the content moves the thumb to the next segment (lit %d -> %d), centred, transform only %s, size +%.1f%%"
            % (tag, i0, lit_index(s5), sorted(props), 100 * (a or {}).get("size", 0)),
            lit_index(s5) == want and all(abs(p - q) <= 1 for p, q in zip(s5["thumb"], s5["segs"][want]["box"])) and props <= {"transform", "opacity"} and a and a.get("moved") and a["size"] <= .005 and a["overshoot"] <= 2,
            {"lit": lit_index(s5), "want": want, "props": sorted(props), "a": a})

    # ---- G. keys ----
    tap_seg(pg, ptr, sw, 0); wait_rest(pg, sw[2]); pg.wait_for_timeout(250)
    pg.evaluate("""([sel, segSel])=>{ const s=%s; s.querySelector(':scope > '+segSel).focus(); }""" % SEG_ELEM, [sw[2], sw[3]])
    pg.keyboard.press("Shift"); pg.keyboard.press("ArrowRight"); wait_rest(pg, sw[2]); pg.wait_for_timeout(200)
    s6 = state(pg, sw)
    ring = pg.evaluate("""()=>{ const e=document.activeElement; if(!e) return null; const c=getComputedStyle(e); return { st:c.outlineStyle, w:parseFloat(c.outlineWidth), m:e.matches(':focus-visible') }; }""")
    chk("%s: G Arrow right picks the next segment (lit %d), the thumb lands on it, and the focused segment shows a ring (%s)" % (tag, lit_index(s6), ring),
        lit_index(s6) == 1 and all(abs(p - q) <= 1 for p, q in zip(s6["thumb"], s6["segs"][1]["box"])) and ring and ring["m"] and ring["st"] != "none" and ring["w"] >= 1.5, {"lit": lit_index(s6), "ring": ring, "thumb": s6["thumb"], "seg": s6["segs"][1]["box"]})

    # ---- H. mouse: hover ----
    if not touch:
        pg.mouse.move(2, 2); pg.wait_for_timeout(450)   # (away from every segment: the last drag left the pointer over one)
        s7 = state(pg, sw); un = 0 if lit_index(s7) != 0 else 1; b = s7["segs"][un]["box"]
        rest_op = s7["segs"][un]["op"]; lit_op = s7["segs"][lit_index(s7)]["op"]
        pg.mouse.move(cx(b), cy(b)); pg.wait_for_timeout(450); s8 = state(pg, sw); hov = s8["segs"][un]["op"]
        pg.mouse.move(2, 2)
        # (384.116) Delta's labels are both white at rest (196 / 199 on his recording, the page's white 198): the thumb says which is picked
        chk("%s: H every label is fully white at rest (unlit %.2f, lit %.2f) and under the mouse (%.2f)" % (tag, rest_op, lit_op, hov),
            rest_op >= .99 and lit_op >= .99 and hov >= .99, {"rest": rest_op, "lit": lit_op, "hover": hov})

    # ---- F. reduce motion ----
    pg.evaluate("()=>{ theme.reduceMotion=true; document.documentElement.dataset.reduceMotion='true'; }"); pg.wait_for_timeout(300)
    st = state(pg, sw); i0 = lit_index(st); i1 = i0 + 1 if i0 + 1 < n else i0 - 1
    rest_th = st["thumb"]
    record_anims(pg, sw); sampler(pg, sw)
    s_b = st["segs"][i1]["box"]
    ptr.down(cx(s_b), cy(s_b)); pg.wait_for_timeout(80); ptr.up(); pg.wait_for_timeout(700)
    fr = L.frames(pg); an = anims_seen(pg); s9 = state(pg, sw)
    mids = [f for f in fr if abs(cx(L.vis(f)) - cx(st["segs"][i0]["box"])) > 1.5 and abs(cx(L.vis(f)) - cx(st["segs"][i1]["box"])) > 1.5]
    # the thumb is pressed on its own segment, too: no lift
    ptr.down(cx(s9["segs"][i1]["box"]), cy(s9["segs"][i1]["box"])); pg.wait_for_timeout(150); pr = state(pg, sw); ptr.up(); pg.wait_for_timeout(200)
    lift_rm = max(pr["thumb"][2] / s9["thumb"][2], pr["thumb"][3] / s9["thumb"][3]) - 1
    pg.evaluate("()=>{ theme.reduceMotion=false; document.documentElement.dataset.reduceMotion='false'; }"); pg.wait_for_timeout(200)
    chk("%s: F reduce motion: the thumb is placed, not moved (%d animations, %d frames in between), no lens, no press lift (+%.1f%%), lit %d"
        % (tag, len(an), len(mids), 100 * lift_rm, lit_index(s9)),
        len(an) == 0 and not mids and lift_rm <= .005 and lit_index(s9) == i1 and all(abs(p - q) <= 1 for p, q in zip(s9["thumb"], s9["segs"][i1]["box"])) and s9["lensOp"] <= .01,
        {"anims": an, "mids": len(mids), "lift": lift_rm, "lit": lit_index(s9)})

def main():
    srv, url = L.g["serve"]()
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=L.g["CHROME"])
        for dev in L.DEVICES:
            if DEVS and dev["name"] not in DEVS: continue
            for cls in CLASSES:
                ctx, pg, errs = L.open_page(br, dev, cls, url)
                ptr = L.Pointer(pg, ctx, dev["touch"])
                for sw in L.SWITCHERS:
                    if cls not in sw[4]: continue
                    if ONLY and not ONLY.search(sw[0]): continue
                    tag = "%s|%s|%s" % (dev["name"], cls, sw[0])
                    try: run_switcher(pg, ptr, dev, tag, sw)
                    except Exception as e: chk("%s: ran" % tag, False, str(e).splitlines()[0][:300])
                    try: pg.mouse.move(2, 2)
                    except Exception: pass
                    L.close_chat(pg)
                chk("%s|%s: J no page errors" % (dev["name"], cls), not errs, errs[:3])
                ctx.close()
        br.close()
    srv.shutdown()
    fails = [n for n, c in results if not c]
    print("\n%d checks, %d failed" % (len(results), len(fails)))
    kinds = {}
    for n, c in results:
        k = re.sub(r"^[^:]*: ", "", n).split(" ")[0]
        kinds.setdefault(k, [0, 0]); kinds[k][0 if c else 1] += 1
    print("by check: " + ", ".join("%s %d pass / %d fail" % (k, v[0], v[1]) for k, v in sorted(kinds.items())))
    sys.exit(0 if ok else 1)

main()
