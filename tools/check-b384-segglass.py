#!/usr/bin/env python3
"""384.116 (segglass): the top switchers are Delta's iOS 26 segmented control - compact, liquid glass, a lens that carries the thumb.

Madison, with a screen recording of Delta's "Change App Icon" screen (its Light | Dark control): "The top tab we have. It does not
look like the one I've mentioned I want... Ours is stretched, no liquid glass, ours is indented... it has none of it. We need to
change that/overhaul ours and make it exactly like what I sent." Read off his recording frame by frame (the numbers are in the notes
archive, 384.116): a COMPACT capsule sized to its labels and centred; a raised glass track (lighter, a bright rim along its top and
bottom, a soft shadow) with a DARKER flat thumb inset in the picked segment; a press swells the whole control ~9% (labels with it);
a move turns the thumb into a clear glass lens, taller than the track, that glides across and shrinks back into the thumb.

Every switcher attachSegSlider makes (Profile's tabs, the Leaderboard's boards, the units screen's levels, the chat sheet's tabs, the
Virtual Room review's Missed / Entire test) on an iPhone 17 Pro Max installed (440x956 @3x), an iPad Pro 11" (834x1194 @2x) and, for
fit, a 320x568 phone. Everything is READ off the page - shapes are asserted, never label strings; the sizes are in the label's own
font size (em), so a font or a zoom change does not move the bar.

  1 COMPACT    the segments are equal and each is no wider than its widest label plus 1.7em a side, or 5.6em (Delta: 82pt for 33pt of
               words at 15pt - 1.63em a side, 5.47em), so the control is never stretched past its labels; and it is centred in its
               column within 1px (the chat sheet's on the sheet's middle too, unless the room either side of it would be narrower
               than the close button beside it - a 320px phone - and then it ends before that button).
  2 RAISED     the track is raised glass, not set in: a backdrop blur on it; a shadow BELOW it (an outer box-shadow, y > 0) and a lighter
               rim along its top (an inset shadow, y > 0, white) - and on the screen its top rim is >= 12 levels over its middle and its
               bottom rim >= 8; the thumb is >= 12 levels DARKER than the track, and flat: its top edge (1px in) is no darker than its
               middle by more than 3 levels (an inner shadow is what read as "indented").
  3 PRESS      a finger held on the picked segment: the whole control swells about its own middle (>= 5% wide, >= 4% tall, centre
               within 1px), the thumb and the label grow with it (>= 5%), nothing is picked; let go and it is back to its size.
  4 TAP        a tap on another segment (every ordered pair; --quick a few), every frame read by FREEZING its Web Animations and stepping
               them (no frame is lost to a loaded machine): the drawn thumb (the lens while its glass is up) grows into a lens >= 15%
               wider than the thumb at rest and TALLER than the track at rest (it stands proud of it) but no more than 1.5x it, glides
               to the new segment never stepping back more than 1.5px, overshoots it by no more than 4% of the way + 1px, never
               further than 6px past the swollen track's ends, and lands on it within 1px at its own size; the control swells while
               it moves and is back to its size within 1px; no layout box (the control's, the thumb's) changes; under 1.2s.
  5 DRAG       a finger on the thumb dragged 60% of the way to its neighbour and held: the lens is up (opacity >= .5, taller than the
               track) with its middle within 3px of the finger, nothing picked; let go: the nearer segment is picked and the thumb
               lands on it within 1px. A drag a quarter of the way: back, nothing picked.
  6 COMPOSITOR every animation the control runs (press, tap, drag) animates transform and/or opacity and nothing else; the CSS
               transitions on the control, its segments and its thumb are transform / opacity or none.
  7 44px       every segment is hit 22px above and below its middle and 1px inside its sides.
  8 320px      on a 320x568 phone every label's words lie inside their segment and the control inside the screen: nothing cut.
  9 REDUCE MOTION  a tap places the thumb (no animation in the control), nothing swells, no lens.
  10 no page errors.

  python3 tools/check-b384-segglass.py                       # both reference devices + the 320px phone, every switcher
  python3 tools/check-b384-segglass.py --quick               # the Pro Max, three tap pairs per switcher
  python3 tools/check-b384-segglass.py --against origin/main # the build before: must FAIL
  python3 tools/check-b384-segglass.py --only profile --devs phone-installed
"""
import json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import b384_seg_lib as L
from b384_seg_lib import cx, cy, lit_index, luma, parse_css_rgb
from playwright.sync_api import sync_playwright
import io
from PIL import Image

ONLY = re.compile(L.arg("--only")) if L.arg("--only") else None
QUICK = "--quick" in sys.argv
SE1 = dict(name="phone-320", w=320, h=568, dpr=2, ins=(20, 0, 0, 0), ua=L.UA, touch=True, installed=True)
ALL = {d["name"]: d for d in L.DEVICES}; ALL["phone-320"] = SE1
DEVS = L.arg("--devs").split(",") if L.arg("--devs") else (["phone-installed"] if QUICK else ["phone-installed", "ipad-pro-11", "phone-320"])
CLASSES = (L.arg("--class") or "academy").split(",")
ok = True; results = []
def chk(name, cond, info=""):
    global ok
    ok = ok and bool(cond); results.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  -> " + str(info)[:500]), flush=True)

SEG = "[...document.querySelectorAll(sel)].find(e=>e.getBoundingClientRect().width>0)"
def state(pg, sw): return pg.evaluate(L.STATE, [sw[2], sw[3]])
def wait_rest(pg, sw, ms=4000):
    pg.evaluate("""async ([sel, ms])=>{ const s=%s; const t0=performance.now();
      while(performance.now()-t0<ms){ if(!s.getAnimations({subtree:true}).some(a=>a.playState==='running')) break; await new Promise(r=>setTimeout(r,50)); }
      await new Promise(r=>setTimeout(r,150)); }""" % SEG, [sw[2], ms])
def wait_lit(pg, sw, want, ms=8000):
    t0 = time.time()
    while time.time() - t0 < ms / 1000:
        s = state(pg, sw)
        if s and lit_index(s) == want: return True
        pg.wait_for_timeout(100)
    return False
def tap(pg, ptr, sw, i, hold=55):
    s = state(pg, sw); b = s["segs"][i]["box"]
    ptr.down(cx(b), cy(b)); pg.wait_for_timeout(hold); ptr.up()
def go_to(pg, ptr, sw, i):
    if lit_index(state(pg, sw)) != i:
        tap(pg, ptr, sw, i); wait_lit(pg, sw, i)
    wait_rest(pg, sw); pg.wait_for_timeout(250)

# the geometry the checks need, read off the page: the control and its column, each segment's box and its words' ink, the thumb, the
# lens (the build before has none), the computed look, the font size
GEO = """([sel, segSel])=>{ const s=%s; if(!s) return null; const r=s.getBoundingClientRect(), cs=getComputedStyle(s);
  const par=s.parentElement, pr=par.getBoundingClientRect(), pc=getComputedStyle(par);
  const col=[pr.left+parseFloat(pc.paddingLeft)+parseFloat(pc.borderLeftWidth), pr.right-parseFloat(pc.paddingRight)-parseFloat(pc.borderRightWidth)];
  /* the chat sheet's row: its close button at the end */
  const sib=[...par.children].filter(c=>c!==s && c.getBoundingClientRect().width>0 && getComputedStyle(c).position!=='absolute');
  let endSib=null; for(const c of sib){ const q=c.getBoundingClientRect(); if(q.left>=r.right-1) endSib=[q.left, q.width, parseFloat(pc.columnGap)||0]; }
  const ink=b=>{ const rg=document.createRange(); const tw=document.createTreeWalker(b, NodeFilter.SHOW_TEXT); let L=1e9,R=-1e9,T=1e9,B=-1e9,n;
    while((n=tw.nextNode())){ if(!n.textContent.trim()) continue; const pe=n.parentElement; if(pe.closest('[hidden]') || !pe.getClientRects().length || getComputedStyle(pe).display==='none') continue;
      rg.selectNodeContents(n); for(const x of rg.getClientRects()){ if(!x.width) continue; L=Math.min(L,x.left); R=Math.max(R,x.right); T=Math.min(T,x.top); B=Math.max(B,x.bottom); } }
    return [L,T,R-L,B-T]; };
  const segs=[...s.querySelectorAll(':scope > '+segSel)].filter(b=>!b.hidden && b.offsetWidth>0).map(b=>{ const q=b.getBoundingClientRect(); const c=getComputedStyle(b);
    return { box:[q.left,q.top,q.width,q.height], ink:ink(b), fs:parseFloat(c.fontSize), tr:c.transitionProperty, td:c.transitionDuration, lit:b.classList.contains('active')||b.classList.contains('is-on') }; });
  const sl=s.querySelector(':scope > .seg-slider'), sr=sl.getBoundingClientRect(), slc=getComputedStyle(sl);
  return { seg:[r.left,r.top,r.width,r.height], col, endSib, segs, thumb:[sr.left,sr.top,sr.width,sr.height], vw:innerWidth,
    backdrop: cs.backdropFilter||cs.webkitBackdropFilter||'none', shadow: cs.boxShadow, thumbShadow: slc.boxShadow, bg: cs.backgroundColor,
    segTr: cs.transitionProperty, segTd: cs.transitionDuration, thTr: slc.transitionProperty, thTd: slc.transitionDuration,
    layout:[s.offsetWidth, s.offsetHeight, sl.offsetWidth, sl.offsetHeight, sl.style.left, sl.style.top, sl.style.width, sl.style.height] }; }""" % SEG
def geo(pg, sw): return pg.evaluate(GEO, [sw[2], sw[3]])

def shadows(s):
    """a computed box-shadow list -> [(inset, x, y, blur, spread, rgba)]"""
    out = []
    for part in re.split(r",(?![^(]*\))", s or ""):
        part = part.strip()
        if not part or part == "none": continue
        m = re.search(r"rgba?\(([^)]*)\)", part); col = [float(v) for v in m.group(1).split(",")] if m else [0, 0, 0, 1]
        if len(col) == 3: col.append(1.0)
        nums = [float(v) for v in re.findall(r"(-?[\d.]+)px", re.sub(r"rgba?\([^)]*\)", "", part))]
        nums += [0] * (4 - len(nums))
        out.append(("inset" in part, nums[0], nums[1], nums[2], nums[3], col))
    return out

def shot(pg):
    return Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
def lum_at(im, dpr, x, y):
    px = im.getpixel((int(round(x * dpr)), int(round(y * dpr))))
    return luma(px)

# FREEZE AND STEP: every Web Animation in the control, paused, stepped from 0 to its end, the drawn thumb read at each step
FREEZE = """([sel])=>{ const s=%s; const an=document.getAnimations().filter(a=>a.effect && a.effect.target && (a.effect.target===s || s.contains(a.effect.target)));
  an.forEach(a=>a.pause()); window.__fz=an;
  return an.map(a=>({ d:a.effect.getTiming().duration, props:[...new Set(a.effect.getKeyframes().flatMap(k=>Object.keys(k)).filter(k=>!['offset','easing','composite','computedOffset'].includes(k)))] })); }""" % SEG
SEEK = """([sel, t])=>{ (window.__fz||[]).forEach(a=>{ a.currentTime=Math.min(t, a.effect.getTiming().duration); });
  const s=%s; const r=s.getBoundingClientRect(); const sl=s.querySelector(':scope > .seg-slider'), q=sl.getBoundingClientRect();
  const le=s.querySelector(':scope > .seg-lens'); const b=le?le.querySelector('.tab-lens-body').getBoundingClientRect():null; const lo=le?+getComputedStyle(le).opacity:0;
  return { seg:[r.left,r.top,r.width,r.height], th:[q.left,q.top,q.width,q.height], thOp:+getComputedStyle(sl).opacity, lensOp:lo, lens:b?[b.left,b.top,b.width,b.height]:null,
    layout:[s.offsetWidth, s.offsetHeight, sl.offsetWidth, sl.offsetHeight, sl.style.left, sl.style.top, sl.style.width, sl.style.height] }; }""" % SEG
def drawn(f): return f["lens"] if (f["lens"] and f["lensOp"] >= .5) else f["th"]
def unfreeze(pg): pg.evaluate("()=>{ (window.__fz||[]).forEach(a=>{ try{ a.finish(); }catch(e){ try{ a.cancel(); }catch(e2){} } }); window.__fz=[]; }")
# every animation the control starts from now on: its properties
REC = """([sel])=>{ const s=%s; window.__ap=[]; window.__apOn=true;
  const f=()=>{ if(!window.__apOn) return; for(const a of document.getAnimations()){ const t=a.effect && a.effect.target; if(!t || !(t===s || s.contains(t)) || a.__seen) continue; a.__seen=1;
    try{ window.__ap.push([...new Set(a.effect.getKeyframes().flatMap(k=>Object.keys(k)).filter(k=>!['offset','easing','composite','computedOffset'].includes(k)))]); }catch(e){} } requestAnimationFrame(f); }; f(); }""" % SEG
def rec(pg, sw): pg.evaluate(REC, [sw[2]])
def recd(pg): pg.evaluate("()=>{ window.__apOn=false; }"); return pg.evaluate("()=>window.__ap||[]")

def run_switcher(pg, ptr, dev, tag, sw, props_seen):
    st = L.open_switcher(pg, sw, 1800)
    if not st or len(st["segs"]) < 2:
        chk("%s: the switcher is on screen with 2+ segments" % tag, False, st); return
    n = len(st["segs"])
    go_to(pg, ptr, sw, 0)
    g = geo(pg, sw)
    seg = g["seg"]; segs = g["segs"]; fs = segs[0]["fs"] or 16
    if dev["name"] == "phone-320":
        # ---- 8. nothing cut at 320px ----
        bad = []
        for i, s in enumerate(segs):
            b, k = s["box"], s["ink"]
            if not (k[0] >= b[0] - .5 and k[0] + k[2] <= b[0] + b[2] + .5 and k[0] >= -.5 and k[0] + k[2] <= g["vw"] + .5): bad.append((i, [round(v, 1) for v in k], [round(v, 1) for v in b]))
        chk("%s: 8 every label's words lie inside their segment and the screen, the control inside the screen (%.1f..%.1f of %d)" % (tag, seg[0], seg[0] + seg[2], g["vw"]),
            not bad and seg[0] >= -.5 and seg[0] + seg[2] <= g["vw"] + .5, bad)
        return

    # ---- 1. compact, centred ----
    ws = [s["box"][2] for s in segs]; widest = max(s["ink"][2] for s in segs)
    bound = max(widest + 2 * 1.7 * fs, 5.6 * fs) + 1
    mid = (g["col"][0] + g["col"][1]) / 2
    # centred in its column; beside an end button (the chat sheet's close) it may give up the middle only where the room either side of
    # a centred control would be narrower than that button, and then it ends before the button
    es = g["endSib"]; centred = abs(cx(seg) - mid) <= 1
    if es and not centred:
        room = ((g["col"][1] - g["col"][0]) - seg[2]) / 2
        centred = room < es[1] + es[2] and seg[0] + seg[2] <= es[0] - es[2] + 1
    chk("%s: 1 compact - equal segments %s, each no wider than its widest label (%.1f) + 1.7em a side or 5.6em (%.1f); the control %.1f wide in a %.1f column, centred (%.2f off)"
        % (tag, [round(w, 1) for w in ws], widest, bound, seg[2], g["col"][1] - g["col"][0], abs(cx(seg) - mid)),
        max(ws) - min(ws) <= .5 and max(ws) <= bound and centred, {"ws": ws, "bound": bound, "seg": seg, "col": g["col"], "end": es})

    # ---- 2. raised glass ----
    sh = shadows(g["shadow"]); tsh = shadows(g["thumbShadow"])
    below = [x for x in sh if not x[0] and x[2] > 0 and x[5][3] > 0]
    rim = [x for x in sh if x[0] and x[2] > 0 and min(x[5][:3]) >= 200 and x[5][3] > 0]
    thumb_inset_dark = [x for x in tsh if x[0] and max(x[5][:3]) < 80 and x[5][3] >= .1 and (x[2] != 0 or x[3] > 0)]
    im = shot(pg); dpr = dev["dpr"]
    # a column through an unpicked segment, clear of its words
    un = next(i for i, s in enumerate(segs) if not s["lit"])
    ub, uk = segs[un]["box"], segs[un]["ink"]
    x = ub[0] + 3 if ub[0] + 3 < uk[0] - 2 else ub[0] + ub[2] - 3
    top_rim = max(lum_at(im, dpr, x, seg[1] + d) for d in (.4, .7, 1.0, 1.4))
    bot_rim = max(lum_at(im, dpr, x, seg[1] + seg[3] - d) for d in (.4, .7, 1.0, 1.4))
    middle = lum_at(im, dpr, x, cy(seg))
    th = g["thumb"]
    # the thumb's own fill, above its words, and its top edge 1px in (an inner shadow darkens that edge: "indented")
    th_mid = lum_at(im, dpr, cx(th), th[1] + 7); th_edge = lum_at(im, dpr, cx(th), th[1] + 1.2)
    chk("%s: 2 raised glass - backdrop %s; a shadow below %s; a light top rim %s; on screen the top rim %.0f / bottom rim %.0f over a middle of %.0f; the thumb %.0f (%.0f darker), its top edge %.0f against its middle (flat), no dark inner shadow %s"
        % (tag, g["backdrop"], bool(below), bool(rim), top_rim, bot_rim, middle, th_mid, middle - th_mid, th_edge, thumb_inset_dark[:1]),
        "blur" in g["backdrop"] and below and rim and top_rim >= middle + 12 and bot_rim >= middle + 8 and th_mid <= middle - 12 and th_edge >= th_mid - 3 and not thumb_inset_dark,
        {"backdrop": g["backdrop"], "shadow": g["shadow"], "thumb": g["thumbShadow"], "top": top_rim, "bot": bot_rim, "mid": middle, "th": th_mid, "edge": th_edge})

    # ---- 7. 44px ----
    hits = pg.evaluate("""([sel, segSel])=>{ const s=%s;
      return [...s.querySelectorAll(':scope > '+segSel)].filter(b=>!b.hidden && b.offsetWidth>0).map(b=>{ const r=b.getBoundingClientRect(), x=r.left+r.width/2, y=r.top+r.height/2;
        const at=(xx,yy)=>{ const e=document.elementFromPoint(xx, yy); return !!(e && e.closest(segSel)===b); };
        return { up:at(x,y-22), down:at(x,y+22), left:at(r.left+1,y), right:at(r.right-1,y), w:r.width }; }); }""" % SEG, [sw[2], sw[3]])
    chk("%s: 7 every segment is a 44px target (hit 22px above and below its middle, 1px in from its sides)" % tag, all(h["up"] and h["down"] and h["left"] and h["right"] and h["w"] >= 44 for h in hits), hits)

    # ---- 6a. CSS transitions ----
    def trs(p, d): return [x.strip() for x, y in zip(p.split(","), (d.split(",") * 9)) if float(y.strip().rstrip("s") or 0) > 0]
    tr = trs(g["segTr"], g["segTd"]) + trs(g["thTr"], g["thTd"]) + [t for s in segs for t in trs(s["tr"], s["td"])]
    chk("%s: 6a the control's, its segments' and its thumb's CSS transitions are transform / opacity or none (%s)" % (tag, sorted(set(tr))), set(tr) <= {"transform", "opacity"}, tr)

    # ---- 3. press ----
    rec(pg, sw)
    g = geo(pg, sw)   # (again: the chat's counts may have widened its labels since)
    b0 = g["segs"][0]["box"]; ink0 = g["segs"][0]["ink"]; rest_seg = g["seg"]; rest_th = g["thumb"]
    ptr.down(cx(b0), cy(b0))
    pr = None; t0 = time.time()
    while time.time() - t0 < 3:
        pg.wait_for_timeout(150)
        pr = geo(pg, sw)
        if pr["seg"][2] / rest_seg[2] >= 1.05 and not pg.evaluate("([sel])=>%s.getAnimations({subtree:true}).some(a=>a.playState==='running')" % SEG, [sw[2]]): break
    sx, sy = pr["seg"][2] / rest_seg[2], pr["seg"][3] / rest_seg[3]
    tgrow = pr["thumb"][2] / rest_th[2]; lgrow = pr["segs"][0]["ink"][2] / ink0[2]
    ptr.up(); wait_rest(pg, sw); pg.wait_for_timeout(300)
    back = geo(pg, sw)
    chk("%s: 3 press - the control swells x%.3f x %.3f about its middle (%.2f off), the thumb x%.3f and the label x%.3f with it, nothing picked (lit %d); let go: back to its size (%.2fpx)"
        % (tag, sx, sy, abs(cx(pr["seg"]) - cx(rest_seg)), tgrow, lgrow, lit_index({"segs": pr["segs"]}), abs(back["seg"][2] - rest_seg[2])),
        sx >= 1.05 and sy >= 1.04 and abs(cx(pr["seg"]) - cx(rest_seg)) <= 1 and tgrow >= 1.05 and lgrow >= 1.05 and lit_index({"segs": pr["segs"]}) == 0
        and abs(back["seg"][2] - rest_seg[2]) <= 1 and abs(back["seg"][3] - rest_seg[3]) <= 1, {"sx": sx, "sy": sy, "thumb": tgrow, "label": lgrow})

    # ---- 4. taps, frozen and stepped ----
    pairs = [(i, j) for i in range(n) for j in range(n) if i != j]
    if QUICK: pairs = pairs[:3]
    bad = []; worst = dict(grow=9, tall=9, over=0, back=0, out=0, dur=0)
    for (i, j) in pairs:
        go_to(pg, ptr, sw, i)
        s0 = geo(pg, sw)
        if lit_index({"segs": s0["segs"]}) != i: bad.append((i, j, "could not start")); continue
        rest_th, rest_seg = s0["thumb"], s0["seg"]; c0, c1 = cx(s0["segs"][i]["box"]), cx(s0["segs"][j]["box"])
        # freeze AT THE TAP'S CLICK, in its own task (after the page's handler, before the timeline moves on): a loaded machine's long
        # build of the next tab cannot let the move run out unseen. A build whose move starts later (in a frame of its own, the build
        # before) is caught by the poll below.
        pg.evaluate("""([sel])=>{ window.__fzReady=false; window.__fz=[]; const s=%s;
          window.addEventListener('click', function f(){ window.removeEventListener('click', f);
            const le=s.querySelector(':scope > .seg-lens'); if(!le || !le.getAnimations().length) return;
            const an=document.getAnimations().filter(a=>a.effect && a.effect.target && (a.effect.target===s || s.contains(a.effect.target)));
            an.forEach(a=>a.pause()); window.__fz=an; window.__fzReady=true; }); }""" % SEG, [sw[2]])
        tap(pg, ptr, sw, j)
        # freeze as soon as the move has started (the lens has its track, or - in a build without one - the thumb is moving)
        t0 = time.time(); fz = []
        while time.time() - t0 < 6:
            if pg.evaluate("()=>window.__fzReady"):
                fz = pg.evaluate("""()=>(window.__fz||[]).map(a=>({ d:a.effect.getTiming().duration, props:[...new Set(a.effect.getKeyframes().flatMap(k=>Object.keys(k)).filter(k=>!['offset','easing','composite','computedOffset'].includes(k)))] }))""")
                break
            # (not before the tapped segment is the picked one: a press's own swell moves the thumb too, and is not the move)
            started = pg.evaluate("""([sel, segSel, j])=>{ const s=%s; const sl=s.querySelector(':scope > .seg-slider');
              const segs=[...s.querySelectorAll(':scope > '+segSel)].filter(b=>!b.hidden && b.offsetWidth>0); const b=segs[j];
              return !!b && (b.classList.contains('active') || b.classList.contains('is-on')) && sl.getAnimations().some(a=>a.playState==='running'); }""" % SEG, [sw[2], sw[3], j])
            if started: fz = pg.evaluate(FREEZE, [sw[2]]); break
            pg.wait_for_timeout(8)
        if not fz: bad.append((i, j, "no animation")); wait_lit(pg, sw, j); continue
        D = max(a["d"] for a in fz); props = set(p for a in fz for p in a["props"])
        frames = []; t = 0
        while t <= D + .5:
            frames.append(pg.evaluate(SEEK, [sw[2], t])); t += 1000 / 120
        unfreeze(pg); wait_lit(pg, sw, j); wait_rest(pg, sw); pg.wait_for_timeout(200)
        s1 = geo(pg, sw)
        d = 1 if c1 > c0 else -1
        # the drawn middle in the control's own coordinates (the swell moves every segment's middle on the screen)
        cs = [(cx(drawn(f)) - cx(f["seg"])) / (f["seg"][2] / rest_seg[2]) + cx(rest_seg) for f in frames]
        grow = max(drawn(f)[2] for f in frames) / rest_th[2]
        tall = max(drawn(f)[3] for f in frames) / rest_seg[3]
        over = max([0] + [(c - cx(s1["segs"][j]["box"])) * d for c in cs])
        backs = max([0] + [-(cs[k + 1] - cs[k]) * d for k in range(len(cs) - 1) if abs(cs[k] - cx(s1["segs"][j]["box"])) > 3])
        out = max([0] + [max(f["seg"][0] - drawn(f)[0], drawn(f)[0] + drawn(f)[2] - (f["seg"][0] + f["seg"][2])) for f in frames])
        swell = max(f["seg"][2] / rest_seg[2] for f in frames)
        lay = {json.dumps(f["layout"]) for f in frames}
        land = all(abs(p - q) <= 1 for p, q in zip(s1["thumb"], s1["segs"][j]["box"])) and lit_index({"segs": s1["segs"]}) == j
        why = []
        if grow < 1.15: why.append("never a lens (x%.2f wide)" % grow)
        if tall <= 1.0: why.append("never taller than the track (x%.2f)" % tall)
        if tall > 1.5: why.append("a bubble (x%.2f the track)" % tall)
        if over > .04 * abs(c1 - c0) + 1: why.append("overshoot %.1f" % over)
        if backs > 1.5: why.append("stepped back %.1f" % backs)
        if out > 6: why.append("%.1fpx past the track's end" % out)
        if swell < 1.03: why.append("no swell (x%.3f)" % swell)
        if abs(s1["seg"][2] - rest_seg[2]) > 1: why.append("the control not back to its size")
        if len(lay) > 1: why.append("layout changed %d times" % (len(lay) - 1))
        if not props <= {"transform", "opacity"}: why.append("animated %s" % sorted(props))
        if D > 1200: why.append("%.0fms" % D)
        if not land: why.append("landed %s vs %s, lit %d" % ([round(v, 1) for v in s1["thumb"]], [round(v, 1) for v in s1["segs"][j]["box"]], lit_index({"segs": s1["segs"]})))
        worst["grow"] = min(worst["grow"], grow); worst["tall"] = min(worst["tall"], tall); worst["over"] = max(worst["over"], over)
        worst["back"] = max(worst["back"], backs); worst["out"] = max(worst["out"], out); worst["dur"] = max(worst["dur"], D)
        props_seen.update(props)
        if why: bad.append((i, j, why))
    chk("%s: 4 taps (%d pairs, every frame) - the thumb becomes a lens (at least x%.2f its width, x%.2f the track's height), glides there (back <= %.1fpx, overshoot <= %.1fpx, <= %.1fpx past the ends), the control swells and returns, lands within 1px, transform / opacity only, no layout change, <= %.0fms"
        % (tag, len(pairs), worst["grow"], worst["tall"], worst["back"], worst["over"], worst["out"], worst["dur"]), not bad, bad[:3])

    # ---- 5. drag ----
    go_to(pg, ptr, sw, 0)
    s0 = geo(pg, sw); a0, a1 = s0["segs"][0]["box"], s0["segs"][1]["box"]; y = cy(a0); x0, x1 = cx(a0), cx(a1)
    ptr.down(x0, y); pg.wait_for_timeout(90)
    for k in range(1, 15): ptr.move(x0 + (x1 - x0) * .6 * k / 14, y); pg.wait_for_timeout(30)
    held = None; t0 = time.time()
    while time.time() - t0 < 3:
        pg.wait_for_timeout(150)
        held = pg.evaluate(SEEK.replace("(window.__fz||[]).forEach", "([]).forEach"), [sw[2], 0])
        if held["lensOp"] >= .5 and held["lens"] and held["lens"][3] > s0["seg"][3]: break
    xf = x0 + (x1 - x0) * .6
    lit_held = lit_index(state(pg, sw))
    held = pg.evaluate(SEEK.replace("(window.__fz||[]).forEach", "([]).forEach"), [sw[2], 0])
    ptr.up(); wait_lit(pg, sw, 1); wait_rest(pg, sw); pg.wait_for_timeout(250)
    s2 = geo(pg, sw)
    lens_ok = held and held["lensOp"] >= .5 and held["lens"] and held["lens"][3] > s0["seg"][3]
    follow = abs(cx(held["lens"]) - xf) if lens_ok else abs(cx(held["th"]) - xf)
    land = lit_index({"segs": s2["segs"]}) == 1 and all(abs(p - q) <= 1 for p, q in zip(s2["thumb"], s2["segs"][1]["box"]))
    chk("%s: 5a drag 60%% and hold - the lens is up (opacity %.2f, %s tall against the track's %.1f), its middle %.1fpx from the finger, nothing picked (lit %d); let go: the nearer segment picked, the thumb on it"
        % (tag, held["lensOp"] if held else 0, round(held["lens"][3], 1) if held and held["lens"] else None, s0["seg"][3], follow, lit_held, ),
        lens_ok and follow <= 3 and lit_held == 0 and land, {"held": held, "xf": xf, "lit": lit_held, "land": land})
    s0 = s2; a0, a1 = s0["segs"][1]["box"], s0["segs"][0]["box"]; x0, x1 = cx(a0), cx(a1)
    ptr.down(x0, y); pg.wait_for_timeout(90)
    for k in range(1, 9): ptr.move(x0 + (x1 - x0) * .25 * k / 8, y); pg.wait_for_timeout(30)
    pg.wait_for_timeout(150); ptr.up(); wait_rest(pg, sw); pg.wait_for_timeout(500)
    s3 = geo(pg, sw)
    chk("%s: 5b a drag a quarter of the way: back, nothing picked (lit %d), the thumb on its segment" % (tag, lit_index({"segs": s3["segs"]})),
        lit_index({"segs": s3["segs"]}) == 1 and all(abs(p - q) <= 1 for p, q in zip(s3["thumb"], s3["segs"][1]["box"])), s3["thumb"])
    props_seen.update(p for a in recd(pg) for p in a)
    chk("%s: 6b every animation the control ran (press, taps, drags) is transform / opacity (%s)" % (tag, sorted(props_seen)), props_seen <= {"transform", "opacity"}, sorted(props_seen))

    # ---- 9. reduce motion ----
    pg.evaluate("()=>{ theme.reduceMotion=true; document.documentElement.dataset.reduceMotion='true'; }"); pg.wait_for_timeout(300)
    s0 = geo(pg, sw); i0 = lit_index({"segs": s0["segs"]}); i1 = 0 if i0 else 1
    rec(pg, sw)
    b = s0["segs"][i1]["box"]; ptr.down(cx(b), cy(b)); pg.wait_for_timeout(200)
    mid = geo(pg, sw); ptr.up(); wait_lit(pg, sw, i1); pg.wait_for_timeout(400)
    an = recd(pg); s4 = geo(pg, sw)
    pg.evaluate("()=>{ theme.reduceMotion=false; document.documentElement.dataset.reduceMotion='false'; }"); pg.wait_for_timeout(200)
    lens = pg.evaluate("([sel])=>{ const s=%s; const le=s.querySelector(':scope > .seg-lens'); return le?+getComputedStyle(le).opacity:0; }" % SEG, [sw[2]])
    chk("%s: 9 reduce motion - the thumb is placed (%d animations), nothing swells (x%.3f under the finger), no lens (%.2f)" % (tag, len(an), mid["seg"][2] / s0["seg"][2], lens),
        not an and abs(mid["seg"][2] - s0["seg"][2]) <= .5 and lens <= .01 and all(abs(p - q) <= 1 for p, q in zip(s4["thumb"], s4["segs"][i1]["box"])), {"an": an})

def main():
    srv, url = L.g["serve"]()
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=L.g["CHROME"])
        for dn in DEVS:
            dev = ALL[dn]
            for cls in CLASSES:
                ctx, pg, errs = L.open_page(br, dev, cls, url)
                pg.set_default_timeout(180000)
                ptr = L.Pointer(pg, ctx, dev["touch"])
                for sw in L.SWITCHERS:
                    if cls not in sw[4]: continue
                    if ONLY and not ONLY.search(sw[0]): continue
                    tag = "%s|%s|%s" % (dn, cls, sw[0])
                    props = set()
                    try: run_switcher(pg, ptr, dev, tag, sw, props)
                    except Exception as e: chk("%s: ran" % tag, False, str(e).splitlines()[0][:300])
                    try: unfreeze(pg); pg.mouse.move(2, 2)
                    except Exception: pass
                    L.close_chat(pg)
                chk("%s|%s: 10 no page errors" % (dn, cls), not errs, errs[:3])
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
