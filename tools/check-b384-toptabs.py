#!/usr/bin/env python3
"""r8 -> r18 (build 384): the top switchers are Delta's iOS 26 segmented control, by a real finger, on the two reference devices.

History. r8 made the top switchers a dark track with a LIGHTER grey thumb that lifted into the bottom bar's glass lens while it
moved (taller than the track, the whole control swelling 9%); this file held that rule. Madison, r18, Delta's Light / Dark control
beside ours: "I'm not sure what's up with our top tabs. It should be designed like the Delta one, look like it. Function like it.
Fix that, make it smooth." Delta's is a LIGHTER track with a DARKER thumb and no lens, so this file now holds that, read off the
SCREEN (a screenshot pixel), not off the CSS - the look the finger sees. check-b384-segdelta.py holds the geometry and the motion on
every device class; this one holds the colour and the touch on an iPhone 17 Pro Max (440x956) and an iPad Pro 11" (834x1194), both
at 2x with an iPhone / iPad user agent and real touches (CDP Input.dispatchTouchEvent), in both classes (the academy and Fire
Code - in Fire Code only the chat's and the review's exist: it has one Profile tab, no board and one level).

  1. AT REST the track is a neutral grey LIGHTER than the thumb (a screenshot pixel in each: >= 10 levels apart, chroma <= 6), the
     same under two themes (within 2), nowhere near the theme's accent colour, both full capsules.
  2. A TAP on another segment: no glass lens at any frame, the thumb the same size throughout (<= 0.5%) and the control not
     swelling, the thumb glides to the new segment (never backwards, no overshoot past 2px) and lands centred under the new label
     within 1px.
  3. A DRAG from the lit segment two-thirds of the way to its neighbour: the thumb follows the finger (within 2px as the finger
     stops), lifted a few percent (1-6%) and no more, nothing picked yet; let go it snaps to the nearest segment, which is picked,
     the thumb centred under its label within 1px. A drag only a quarter of the way snaps back: nothing picked.
  4. A SWIPE across the content (Profile and the Leaderboard, which swipe between their tabs) moves the thumb to the next segment,
     centred under its label.
  5. REDUCE MOTION: a tap places the thumb on the new segment with no animation, centred under the new label.
  6. No page errors.

Labels are read off the page; shapes are asserted, never strings.

  python3 tools/check-b384-toptabs.py                    # both devices, both classes
  python3 tools/check-b384-toptabs.py --against /tmp/prev-index.html   # the build before: must FAIL
  python3 tools/check-b384-toptabs.py --only profile     # switchers whose name matches
"""
import io, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import b384_seg_lib as L
from b384_seg_lib import cx, cy, lit_index, luma, parse_css_rgb
from playwright.sync_api import sync_playwright
from PIL import Image

ONLY = re.compile(L.arg("--only")) if L.arg("--only") else None
DEVICES = [d for d in L.DEVICES if d["name"] in ("phone-installed", "ipad-pro-11")]
if L.arg("--sizes"): DEVICES = [d for d in DEVICES if re.search(L.arg("--sizes"), d["name"], re.I)]
CLASSES = (L.arg("--class") or "academy,ifc").split(",")
ok = True; results = []
def chk(name, cond, info=""):
    global ok
    ok = ok and bool(cond); results.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  -> " + str(info)[:420]), flush=True)

def pixel(pg, x, y):
    png = pg.screenshot(clip={"x": x - 1, "y": y - 1, "width": 3, "height": 3})
    im = Image.open(io.BytesIO(png)).convert("RGB")
    return tuple(int(v) for v in im.getpixel((im.width // 2, im.height // 2)))
def chroma(c): return max(c) - min(c)
def state(pg, sw): return pg.evaluate(L.STATE, [sw[2], sw[3]])
def settle(pg, sw, ms=3500):
    pg.evaluate("""async ([sel, ms])=>{ const s=[...document.querySelectorAll(sel)].find(e=>e.getBoundingClientRect().width>0); const t0=performance.now();
      while(performance.now()-t0<ms){ if(!s.getAnimations({subtree:true}).some(a=>a.playState==='running')) break; await new Promise(r=>setTimeout(r,50)); }
      await new Promise(r=>setTimeout(r,150)); }""", [sw[2], ms])
def wait_lit(pg, sw, want, ms=5000):
    t0 = time.time()
    while time.time() - t0 < ms / 1000:
        s = state(pg, sw)
        if s and lit_index(s) == want: return True
        pg.wait_for_timeout(100)
    return False
def centred(st, i):
    t, lab = st["thumb"], st["segs"][i]["label"]
    return abs(cx(t) - cx(lab)), abs(cy(t) - cy(lab))
def tap(pg, ptr, sw, i, hold=60):
    b = state(pg, sw)["segs"][i]["box"]; ptr.down(cx(b), cy(b)); pg.wait_for_timeout(hold); ptr.up()

def run_switcher(pg, ptr, dev, tag, sw):
    st = L.open_switcher(pg, sw)
    if not st or len(st["segs"]) < 2:
        chk("%s: the switcher is on screen with 2+ segments" % tag, False, st); return
    n = len(st["segs"]); print("  %s: segments %s" % (tag, [s["text"] for s in st["segs"]]), flush=True)
    for i in range(n): tap(pg, ptr, sw, i); settle(pg, sw); pg.wait_for_timeout(500)
    tap(pg, ptr, sw, 0); settle(pg, sw); pg.wait_for_timeout(300)

    # 1. at rest, read off the screen
    def colours():
        s = state(pg, sw); i = lit_index(s); un = next(k for k in range(len(s["segs"])) if k != i)
        t = s["thumb"]; b = s["segs"][un]["box"]
        return s, pixel(pg, t[0] + min(9, t[3] / 3), cy(t)), pixel(pg, b[0] + min(9, b[3] / 3), cy(b))
    st, thumb_a, track_a = colours()
    pg.evaluate("()=>{ theme.accent='vanguard'; applyTheme(); }"); pg.wait_for_timeout(300)
    pg.evaluate("()=>{" + sw[1] + "}"); pg.wait_for_timeout(1300)
    st_b, thumb_b, track_b = colours()
    acc = parse_css_rgb(pg.evaluate("()=>getComputedStyle(document.documentElement).getPropertyValue('--accent').trim()"))
    pg.evaluate("()=>{ theme.accent='ink'; applyTheme(); }"); pg.wait_for_timeout(300)
    st = L.open_switcher(pg, sw, 1300)
    far = acc is None or min(sum((p[k] - acc[k]) ** 2 for k in range(3)) ** .5 for p in (thumb_b, track_b)) > 40
    rest_ok = luma(track_a) - luma(thumb_a) >= 10 and chroma(track_a) <= 6 and chroma(thumb_a) <= 6 \
        and max(abs(thumb_a[k] - thumb_b[k]) for k in range(3)) <= 2 and max(abs(track_a[k] - track_b[k]) for k in range(3)) <= 2 and far \
        and st["thumbRadius"] >= st["thumbLayout"][1] / 2 - .5 and st["trackRadius"] >= st["seg"][3] / 2 - .5
    chk("%s: 1. at rest the track (%s) is a neutral grey LIGHTER than the thumb (%s), the same under two themes, not the accent, both capsules" % (tag, track_a, thumb_a), rest_ok,
        {"track": (track_a, track_b), "thumb": (thumb_a, thumb_b), "accent": acc})
    # (the picked segment is the first again, a theme change can rebuild what is open)
    for i in range(n): tap(pg, ptr, sw, i); settle(pg, sw); pg.wait_for_timeout(300)
    tap(pg, ptr, sw, 0); settle(pg, sw); pg.wait_for_timeout(300)

    # 2. a tap on another segment
    st = state(pg, sw); i0 = lit_index(st); i1 = 1
    rest_th, rest_seg = st["thumb"], st["seg"]; c1 = cx(st["segs"][i1]["box"])
    pg.evaluate(L.SAMPLER, [sw[2]]); tap(pg, ptr, sw, i1); wait_lit(pg, sw, i1); settle(pg, sw)
    fr = L.frames(pg); st2 = state(pg, sw); a = L.analyse(fr, c1, rest_th, rest_seg)
    dx, dy = centred(st2, i1)
    lens_seen = [f for f in fr if f.get("lens")]
    chk("%s: 2. a tap glides the thumb to the tapped segment with no glass lens (%d frames), no resize (+%.1f%%), no swell (+%.1f%%), no overshoot (%.2fpx), centred (dx %.2f, dy %.2f)"
        % (tag, len(lens_seen), 100 * (a or {}).get("size", 0), 100 * (a or {}).get("swell", 0), (a or {}).get("overshoot", 0), dx, dy),
        a and a.get("moved") and not lens_seen and not st2["lens"] and a["size"] <= .005 and a["swell"] <= .002 and a["overshoot"] <= 2 and a["backstep"] <= 1.5
        and lit_index(st2) == i1 and dx <= 1 and dy <= 1, {"a": a, "lit": lit_index(st2), "lens": len(lens_seen)})

    # 3. a drag two-thirds of the way to the neighbour, then one a quarter of the way
    st = st2; i0 = lit_index(st); i1 = i0 + 1 if i0 + 1 < n else i0 - 1
    a0, a1 = st["segs"][i0]["box"], st["segs"][i1]["box"]; y = cy(a0); x0, x1 = cx(a0), cx(a1); rest_th = st["thumb"]
    ptr.down(x0, y); pg.wait_for_timeout(120)
    for k in range(1, 17): ptr.move(x0 + (x1 - x0) * .66 * k / 16, y); pg.wait_for_timeout(30)
    pg.wait_for_timeout(280)
    held = state(pg, sw); xf = x0 + (x1 - x0) * .66
    lift = max(held["thumb"][2] / rest_th[2], held["thumb"][3] / rest_th[3]) - 1
    near = abs(cx(held["thumb"]) - xf); lit_held = lit_index(held)
    ptr.up(); wait_lit(pg, sw, i1); settle(pg, sw)
    st3 = state(pg, sw); dx, dy = centred(st3, i1)
    chk("%s: 3a. a drag carries the thumb with the finger (within %.1fpx), lifted %.1f%% (1-6%%), nothing picked until let go (lit %d)" % (tag, near, 100 * lift, lit_held),
        near <= 2 and .01 <= lift <= .06 and lit_held == i0 and not held["lens"], {"near": near, "lift": lift, "lit": lit_held})
    chk("%s: 3b. let go two-thirds over, it snaps to the nearest segment, picked, thumb centred under its label (dx %.2f, dy %.2f)" % (tag, dx, dy),
        lit_index(st3) == i1 and dx <= 1 and dy <= 1 and abs(st3["thumb"][2] - rest_th[2]) <= .5, {"lit": lit_index(st3), "want": i1})
    st = st3; i0 = lit_index(st); i1 = i0 + 1 if i0 + 1 < n else i0 - 1
    a0, a1 = st["segs"][i0]["box"], st["segs"][i1]["box"]; x0, x1 = cx(a0), cx(a1)
    ptr.down(x0, y); pg.wait_for_timeout(100)
    for k in range(1, 9): ptr.move(x0 + (x1 - x0) * .25 * k / 8, y); pg.wait_for_timeout(30)
    pg.wait_for_timeout(120); ptr.up(); settle(pg, sw)
    st4 = state(pg, sw); dx, dy = centred(st4, i0)
    chk("%s: 3c. a drag a quarter of the way snaps back: nothing picked, thumb centred (dx %.2f)" % (tag, dx), lit_index(st4) == i0 and dx <= 1 and dy <= 1, {"lit": lit_index(st4), "want": i0})

    # 4. a swipe across the content
    if sw[5]:
        st = st4; i0 = lit_index(st); go_left = i0 + 1 < n
        want = i0 + 1 if go_left else i0 - 1
        vw = dev["w"]; yy = st["seg"][1] + st["seg"][3] + 230
        xa, xb = (vw * .75, vw * .25) if go_left else (vw * .25, vw * .75)
        ptr.down(xa, yy)
        for k in range(1, 11): ptr.move(xa + (xb - xa) * k / 10, yy + k * .3); pg.wait_for_timeout(16)
        ptr.up(); wait_lit(pg, sw, want); settle(pg, sw)
        st5 = state(pg, sw); dx, dy = centred(st5, want) if lit_index(st5) == want else (99, 99)
        chk("%s: 4. a swipe across the content moves the thumb to the next segment, centred (dx %.2f)" % (tag, dx), lit_index(st5) == want and dx <= 1 and dy <= 1, {"lit": lit_index(st5), "want": want})

    # 5. reduce motion
    pg.evaluate("()=>{ theme.reduceMotion=true; document.documentElement.dataset.reduceMotion='true'; }"); pg.wait_for_timeout(300)
    st = state(pg, sw); i0 = lit_index(st); i1 = i0 + 1 if i0 + 1 < n else i0 - 1
    pg.evaluate("""([sel])=>{ const s=[...document.querySelectorAll(sel)].find(e=>e.getBoundingClientRect().width>0); window.__n=0; window.__on2=true;
      const f=()=>{ if(!window.__on2) return; window.__n+=s.getAnimations({subtree:true}).length; requestAnimationFrame(f); }; f(); }""", [sw[2]])
    tap(pg, ptr, sw, i1, hold=80); pg.wait_for_timeout(700)
    nanim = pg.evaluate("()=>{ window.__on2=false; return window.__n; }")
    st6 = state(pg, sw)
    pg.evaluate("()=>{ theme.reduceMotion=false; document.documentElement.dataset.reduceMotion='false'; }")
    dx, dy = centred(st6, i1) if lit_index(st6) == i1 else (99, 99)
    chk("%s: 5. reduce motion: the thumb is placed with no animation (%d), centred under the new label (dx %.2f)" % (tag, nanim, dx), nanim == 0 and dx <= 1 and dy <= 1, {"anims": nanim, "lit": lit_index(st6)})

def main():
    srv, url = L.g["serve"]()
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=L.g["CHROME"])
        for dev in DEVICES:
            for cls in CLASSES:
                ctx, pg, errs = L.open_page(br, dev, cls, url)
                ptr = L.Pointer(pg, ctx, True)
                for sw in L.SWITCHERS:
                    if cls not in sw[4]: continue
                    if ONLY and not ONLY.search(sw[0]): continue
                    tag = "%s|%s|%s" % (dev["name"], cls, sw[0])
                    try: run_switcher(pg, ptr, dev, tag, sw)
                    except Exception as e: chk("%s: ran" % tag, False, str(e).splitlines()[0][:300])
                    L.close_chat(pg)
                chk("%s|%s: 6. no page errors" % (dev["name"], cls), not errs, errs[:3])
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
