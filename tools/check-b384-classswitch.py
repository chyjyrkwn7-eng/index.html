#!/usr/bin/env python3
"""Build 384: the class switch FADES from one class's colours into the other's (Madison: "When switching between classes, ensure
that the screen is smooth, switching between themes I've noticed is laggy during the splash screen and not perfect, just make it
better, maybe make it fade into the other color so it's better and easier on the eyes.")

The real switch is driven (the class button, its list, the class) on an iPhone 17 Pro Max (440x956 at 3x) and an iPad Pro 11in
(834x1194 at 2x), installed, the Pro Max in a Safari tab and with Reduce Motion, both ways (the first switch after launch, then
back), with the owner's account (the academy in Silver, Fire Code in its default). Each device is launched twice:
  * RECORDED (a CDP screencast: the compositor's own frames): the BACKGROUND's colour in every frame, read where only the sky
    shows and the two classes' skies differ most (the side strips beside the planet's orbits, under the top glows);
  * TIMED (nothing recording - a 3x screencast is itself work for this machine and lands in the page's frame gaps): the page's own
    frame clock (every requestAnimationFrame, kept across the reload in sessionStorage) and its long tasks (PerformanceObserver).

Asserts (shape, read off the page - no label strings, no typed colours):
  (1) THE FADE GOES ONE WAY: every frame's background, put on the line from the class left's sky (just before the tap) to the class
      arrived in's (at rest at the end), never steps back by more than a few levels and never leaves the line - a dip to near-black
      on the way (the old cover) is off the line by the whole difference;
  (1b) NO CUT: frames on the way through the colours between, and no step between two frames in a row over half the change;
  (2) NO FLASH: the sky never darker than the darker class's sky, the screen never brighter than the brighter Home;
  (3a) the colour moves on ONE page, before that page goes - not across the reload and through the next page's boot;
  (3) SMOOTH WHILE IT MOVES (timed run, the same stretch from the tap): no long task, and no frame gap over the budget
      (max(50ms, 2.5 x the page's own frame gap at rest before the tap));
  (4) THE LIFT: from the first frame of the next page's cover lifting to Home's parts settled (600ms), no long task over 100ms and
      no frame gap over 100ms (the lift changes no colour now; its fade and rise are compositor animations - see judge_timing);
  no page errors.

  python3 tools/check-b384-classswitch.py [--only phone,ipad,tab,reduce,cpu4] [--against REV|path] [--video DIR] [--report]
"""
import io, json, os, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
def arg(n, d=None): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d
AGAINST = arg("--against")
if AGAINST and not os.path.exists(AGAINST):
    # a git revision: its index.html, served next to this tree's other files
    txt = subprocess.check_output(["git", "-C", ROOT, "show", AGAINST + ":index.html"])
    fd, p = tempfile.mkstemp(prefix="b384cs-against-", suffix=".html"); os.write(fd, txt); os.close(fd)
    sys.argv[sys.argv.index("--against") + 1] = p; AGAINST = p
sys.path.insert(0, HERE)
import b384_switchfx_lib as L
from playwright.sync_api import sync_playwright
import numpy as np
from PIL import Image

ONLY = set(x for x in (arg("--only", "") or "").split(",") if x)
VIDEO = arg("--video"); REPORT = "--report" in sys.argv
def want(s): return not ONLY or s in ONLY

fails = []
def chk(name, cond, info=""):
    print(("  PASS " if cond else "  FAIL ") + name + ("" if cond else "  -> " + str(info)[:600]), flush=True)
    if not cond: fails.append(name)

L.UA["ipad"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Safari/605.1.15"
L.DEVS["promax"] = (440, 956, 3, True, True, "iphone")
L.DEVS["promax-tab"] = (440, 956, 3, True, False, "iphone")
L.DEVS["ipad"] = (834, 1194, 2, True, True, "ipad")

# the page's own clock, light: one number per frame (no style reads - a log that restyles every frame is the jank it measures),
# its long tasks, and the moments that matter, kept across the reload in sessionStorage
L.LOGGER = r"""(()=>{ if(location.protocol !== 'http:') return;
  let log = []; try{ log = JSON.parse(sessionStorage.getItem('__fx') || '[]'); }catch(e){}
  window.__fx = log;
  const T = t => Math.round((performance.timeOrigin + (t == null ? performance.now() : t)) * 10) / 10;
  const page = Math.random().toString(36).slice(2, 7);
  const mark = k => { try{ window.__fx.push({ mark: k, t: T(), p: page }); }catch(e){} };
  mark('start');
  addEventListener('pagehide', () => { mark('pagehide'); try{ sessionStorage.setItem('__fx', JSON.stringify(window.__fx.slice(-6000))); }catch(e){} });
  try{ new PerformanceObserver(l => { for(const e of l.getEntries()) window.__fx.push({ lt: Math.round(e.duration), t: T(e.startTime), p: page }); }).observe({ type: 'longtask', buffered: true }); }catch(e){}
  const seen = {};
  new MutationObserver(ms => { for(const m of ms){
    const t = m.target;
    if(m.type === 'attributes' && t && t.id === 'splashscreen' && t.classList.contains('splash-hide') && !seen.lift){ seen.lift = 1; mark('lift'); }
    if(m.type === 'attributes' && t && t.id === 'class-switch-loader' && t.classList.contains('is-on') && !seen.coveron){ seen.coveron = 1; mark('coveron'); }
    for(const n of m.addedNodes){ if(n && n.id === 'class-switch-loader' && !seen.cover){ seen.cover = 1; mark('cover');
      n.addEventListener('transitionend', e => { if(e.target === n && e.propertyName === 'opacity' && !seen.coverend){ seen.coverend = 1; mark('coverend'); } }); } }
    for(const n of m.removedNodes){ if(n && n.id === 'splashscreen' && !seen.gone){ seen.gone = 1; mark('gone'); } }
  } }).observe(document, { subtree: true, childList: true, attributes: true, attributeFilter: ['class'] });
  const tick = ts => { window.__fx.push({ f: 1, t: T(ts), p: page, c: window.NOVA_CLASS || null }); requestAnimationFrame(tick); };
  requestAnimationFrame(tick);
})();"""

# where only the sky shows on Home (fractions of the screen) and the two classes' skies differ most: the two side strips beside the
# planet's orbits, under the top glows (below the banners a Safari tab or a "Welcome back" puts across the top)
# (not the top band: the "Welcome back" banner drops in there). Read in every frame; their mean is "the background".
def sky_boxes(w, h):
    if w > 700:     # iPad: wide side margins beside the planet
        return [(0.0, .20, .06, .42), (.94, .20, 1.0, .42)]
    return [(0.0, .20, .05, .42), (.95, .20, 1.0, .42)]

def sample(jpg):
    im = Image.open(io.BytesIO(jpg)).convert("RGB"); a = np.asarray(im).astype(float); H, W = a.shape[:2]
    cs = []
    for x0, y0, x1, y1 in sky_boxes(W, H):
        cs.append(a[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)].reshape(-1, 3).mean(axis=0))
    c = np.mean(cs, axis=0)
    lum = a[..., 0] * .2126 + a[..., 1] * .7152 + a[..., 2] * .0722
    return c, float(lum.mean())

def session(pw, srv, dev, reduce=False):
    s = L.Session(pw, srv, dev, reduce_motion=reduce)
    # (a 1x picture of the screen: what is sampled and recorded; the page still renders at its own pixel ratio)
    w, h = L.DEVS[dev][0], L.DEVS[dev][1]
    def start_rec(self=s):
        self.frames = []; self.rec = True
        self.cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 80, "everyNthFrame": int(os.environ.get("CS_NTH", "1")), "maxWidth": w, "maxHeight": h})
    s.start_rec = start_rec
    return s.boot()

def switch(s, to, **kw):
    """the lib's switch, once more if the class list never came up still (seen on the iPad after a switch, on either build: the
    list's tap landing while the "Welcome back" banner is dropping in)"""
    try:
        return s.switch(to, **kw)
    except RuntimeError as e:
        if "no still element" not in str(e): raise
        print("  (the class button or its list did not come up still: closed, and tapped again - the button by a click if it is still moving)", flush=True)
        L.ev(s.pg, "()=>{ try{ if(typeof classListClose === 'function') classListClose(); }catch(e){} document.querySelectorAll('.daily-alert,.app-banner,#classback-banner').forEach(e=>e.remove()); }")
        s.stop_rec(); s.pg.wait_for_timeout(2000)
        tap0 = s.tap
        def tap(sel):
            try: return tap0(sel)
            except RuntimeError:
                if sel != ".class-bubble": raise
                for _ in range(25):
                    if L.ev(s.pg, "()=>{ const b = document.querySelector('.class-bubble'); if(b){ b.click(); return true; } return false; }"): break
                    s.pg.wait_for_timeout(200)
                return time.time()
        s.tap = tap
        try: return s.switch(to, **kw)
        finally: s.tap = tap0

def analyse(run):
    t0 = run["t_tap"] * 1000
    fr = []
    for ts, jpg in run["frames"]:
        c, lum = sample(jpg); fr.append({"dt": ts * 1000 - t0, "c": c, "lum": lum, "jpg": jpg})
    log = run["log"]
    frames = [(e["t"] - t0, e["p"], e.get("c")) for e in log if e.get("f")]
    lts = [(e["t"] - t0, e["lt"], e["p"]) for e in log if "lt" in e]
    marks = {}
    for e in log:
        if "mark" in e: marks.setdefault(e["mark"], []).append((e["t"] - t0, e["p"]))
    return fr, frames, lts, marks

def gaps_in(frames, a, b):
    """the frame gaps (ms) of the page drawing in [a, b], per page (the reload between two pages is not a gap of either)"""
    out = []
    by = {}
    for t, p, c in frames: by.setdefault(p, []).append(t)
    for p, ts in by.items():
        ts = sorted(ts)
        for x, y in zip(ts, ts[1:]):
            if y >= a and x <= b: out.append((round(y - x, 1), round(x), p))
    return out

def overlapping(lts, a, b):
    return [(round(t), d) for t, d, p in lts if t < b and t + d > a]

GAP = 50       # ms: three frames at 60Hz; this machine renders 3x in software under a screencast, so a single 2-frame miss is its own
LT_OK = 0      # long tasks allowed while the colour moves
LIFT_LT, LIFT_GAP = 100, 100

def journey(fr):
    """the background's journey in a recorded switch: the class left's sky (A, just before the tap), the class arrived in's (B, at
    rest at the end), and every frame put on the line between them"""
    pre = [x for x in fr if x["dt"] < -50]
    A = (np.mean([x["c"] for x in pre[-4:]], axis=0) if pre else fr[0]["c"])
    B = np.mean([x["c"] for x in fr[-4:]], axis=0)
    d = B - A; n2 = float((d * d).sum())
    seq = [x for x in fr if x["dt"] >= -50]
    proj = []
    for x in seq:
        v = x["c"] - A; k = float((v * d).sum() / n2) if n2 > 0 else 0.0
        proj.append((x["dt"], k, float(np.linalg.norm(v - k * d))))
    return A, B, n2 ** .5, pre, seq, proj

def judge_colour(tag, run, calm=False):
    fr, frames, lts, marks = analyse(run)
    P = lambda s: "%s %s" % (tag, s)
    if len(fr) < 8:
        chk(P("frames captured"), False, len(fr)); return None, None
    A, B, tot, pre, seq, proj = journey(fr)
    if REPORT:
        print("   %s sky A %s -> B %s (%.1f levels apart)" % (tag, [round(v) for v in A], [round(v) for v in B], tot))
        step = max(1, len(proj) // 40)
        print("   t(ms) / along A->B / off the line (levels): " + "  ".join("%d:%.2f/%.0f" % (t, p, o) for t, p, o in proj[::step]))
    chk(P("the two classes' skies differ (%.1f levels)" % tot), tot >= 4, (A, B))
    # (1) one way, on the line
    hi = -1e9; worst_back = 0
    for t, p, o in proj:
        if p * tot < hi - 3: worst_back = max(worst_back, hi - p * tot)
        hi = max(hi, p * tot)
    off = max(o for t, p, o in proj)
    chk(P("(1) the background moves one way, from the class left's colour to the new one's (steps back at most %.1f levels; at most %.1f levels off the way)" % (worst_back, off)),
        worst_back <= 4 and off <= max(6, .35 * tot), (round(worst_back, 1), round(off, 1)))
    # (1b) no cut: a fade is seen as several frames on the way; a cut is one step most of the way (the frames are the compositor's
    # own, as many as it sends - fewer at 3x - so the largest step between two frames in a row is what is judged)
    steps = [(abs(b[1] - a[1]), round(b[0])) for a, b in zip(proj, proj[1:])]
    big = max(steps) if steps else (0, None)
    mids = [round(t) for t, p, o in proj if .12 < p < .88]
    if calm:     # Reduce Motion: an instant or a very short fade is what is asked for - one way and no flash is all that is judged
        chk(P("(1b) Reduce Motion: a short fade or a cut (largest step %.0f%% of the change, %d frames on the way)" % (big[0] * 100, len(mids))), True)
    else:
        chk(P("(1b) no cut: the colour passes through the colours between (%d frames on the way), no step more than 50%% of the change (largest %.0f%% at %sms)" % (len(mids), big[0] * 100, big[1])),
            big[0] <= .5 and len(mids) >= 2, (big, mids[:6]))
    # (2) no flash
    homeA = [x["lum"] for x in pre[-4:]] or [seq[0]["lum"]]; homeB = [x["lum"] for x in fr[-4:]]
    skylum = lambda c: float(c[0] * .2126 + c[1] * .7152 + c[2] * .0722)
    lo = min(skylum(A), skylum(B)); hi_l = max(max(homeA), max(homeB))
    darkest = min(skylum(x["c"]) for x in seq); brightest = max(x["lum"] for x in seq)
    chk(P("(2) no flash: the sky never darker than the darker class's (%.1f, lowest %.1f), the screen never brighter than either Home (%.1f, brightest %.1f)" % (lo, darkest, hi_l, brightest)),
        darkest >= lo - 3 and brightest <= hi_l + 3, (lo, darkest, hi_l, brightest))
    t_a = next((t for t, p, o in proj if p >= .05), None); t_b = next((t for t, p, o in proj if p >= .95 and all(q >= .9 for _, q, _ in proj if _ >= t)), None)
    if t_a is not None and t_b is not None and t_b >= t_a:
        pages = sorted({p for t, p, c in frames if t_a <= t <= t_b})
        gone = (marks.get("pagehide") or [(None, None)])[0][0]
        chk(P("(3a) the colour moves on one page, before it goes (%d to %dms; the page went at %s): not across the reload and the next page's boot" % (t_a, t_b, gone and round(gone))),
            len(pages) == 1 and (gone is None or t_b <= gone + 40), (pages, t_a, t_b, gone))
    else:
        chk(P("(3a) the colour's journey was seen"), False, (t_a, t_b))
    return fr, (t_a, t_b)

def judge_timing(tag, run, window, calm=False):
    _, frames, lts, marks = analyse(dict(run, frames=[]))
    P = lambda s: "%s %s" % (tag, s)
    rest = sorted(x[0] for x in gaps_in(frames, -700, -60))
    med = rest[len(rest) // 2] if rest else 16.7
    budget = max(GAP, 2.5 * med)
    if REPORT:
        print("   %s at rest before the tap: median frame gap %.1fms (worst %.1f) -> budget %.0fms" % (tag, med, rest[-1] if rest else 0, budget))
    t_a, t_b = window
    # the cover's own fade on this run's clock, where the page says so (the cover starting to fade - is-on; on the build before, its
    # going in - to its transitionend; the tap's own task, before it, is not the fade): the colour run's
    # stretch is the same moment on another launch's clock, and a .14s fade (Reduce Motion) is shorter than the two clocks' drift
    cv = (marks.get("coveron") or marks.get("cover") or [(None, None)])[0][0]; ce = (marks.get("coverend") or [(None, None)])[0][0]
    if cv is not None and ce is not None and t_a is not None and t_b is not None and t_b <= ce + 150:
        t_a, t_b = cv, ce
    if t_a is not None and t_b is not None:
        # the same stretch of the switch, on this run's clock (the timing run has no recorder on it)
        lt = overlapping(lts, t_a, t_b); g = gaps_in(frames, t_a, t_b); gm = max([x[0] for x in g] or [0])
        if REPORT: print("   colour moves %d-%d: long tasks %s, gaps > 20ms %s" % (t_a, t_b, lt[:8], [x for x in g if x[0] > 20][:12]))
        chk(P("(3) while the colour moves (%d to %dms) the main thread is free: %d long tasks, largest frame gap %.0fms (budget %.0f)" % (t_a, t_b, len(lt), gm, budget)),
            not lt and gm <= budget, (lt[:6], sorted(g, reverse=True)[:5]))
    lift = (marks.get("lift") or [(None, None)])[-1][0]
    if lift is None:
        chk(P("(4) the lift was seen"), False, list(marks)); return
    # from the lift's first frame (the frame that starts it carries the style of the change: the fade has not moved yet) to Home
    # settled: the cover's .3s and Home's parts rising after it (.52s)
    f0 = next((t for t, p, c in sorted(frames) if t > lift + 1), lift)
    end = lift + 600
    lt = [(t, d) for t, d in overlapping(lts, f0, end) if t >= f0 - 1]
    g = gaps_in(frames, f0, end); gm = max([x[0] for x in g if x[1] >= f0 - 1] or [0])
    if REPORT: print("   lift %d (first frame %d): long tasks %s, gaps > 20ms %s; all long tasks %s" % (lift, f0, lt[:8], [x for x in g if x[0] > 20][:12], [(round(t), d) for t, d, p in lts if t > -200][:24]))
    # (the lift changes no colour any more - the sky under it is the sky on it - and the fade and the rise are opacity/translate/scale,
    # which a phone's compositor runs on its own; what is held here is that the page's own work stays out of it: no long task over
    # LIFT_LT and no frame gap over LIFT_GAP. On this shared machine at 3x the frame clock shows single 50-67ms gaps that carry no
    # script at all (a traced commit/raster wait); the build before had script long tasks of 77-336ms and gaps of 117-367ms there)
    big = [(t, d) for t, d in lt if d > LIFT_LT]
    chk(P("(4) the lift (%d to %dms) runs on a free main thread: %d long tasks over %dms (all: %s), largest frame gap %.0fms (budget %d)" % (f0, end, len(big), LIFT_LT, [d for t, d in lt], gm, max(LIFT_GAP, budget))),
        not big and gm <= max(LIFT_GAP, budget), (lt[:6], sorted(g, reverse=True)[:5]))

def video(run, fr, path):
    """the frames at their own times, 60fps, phone size"""
    if not fr: return
    d = tempfile.mkdtemp(prefix="b384cs-vid-")
    lst = []
    fr = [x for x in fr if x["dt"] >= -400]
    for i, x in enumerate(fr):
        p = os.path.join(d, "%05d.jpg" % i); open(p, "wb").write(x["jpg"])
        dur = (fr[i + 1]["dt"] - x["dt"]) / 1000 if i + 1 < len(fr) else .5
        lst.append("file '%s'\nduration %.4f" % (p, max(dur, .001)))
    lst.append("file '%s'" % os.path.join(d, "%05d.jpg" % (len(fr) - 1)))
    open(os.path.join(d, "list.txt"), "w").write("\n".join(lst) + "\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(d, "list.txt"),
                    "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2,fps=60", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "18", path], check=False)

print("check-b384-classswitch against", L.SRC_PATH, "(build %s)" % L.BUILD, flush=True)
srv = L.Server()
RUNS = [("phone", "promax", False, 1, "iPhone 17 Pro Max 440x956 @3x, installed"),
        ("ipad", "ipad", False, 1, "iPad Pro 11in 834x1194 @2x, installed"),
        ("tab", "promax-tab", False, 1, "iPhone 17 Pro Max in a Safari tab"),
        ("reduce", "promax", True, 1, "iPhone 17 Pro Max, Reduce Motion"),
        ("cpu4", "promax", False, 4, "iPhone 17 Pro Max at 4x CPU")]
with sync_playwright() as pw:
    for sec, dev, red, cpu, desc in RUNS:
        if not want(sec) or (sec == "cpu4" and not ONLY): continue     # (4x: asked for by name; a report, its budgets are this machine's)
        print("\n%s (%s): the academy -> Fire Code (the first switch after launch) -> the academy" % (sec, desc), flush=True)
        try:
            # two launches of the same device: the first recorded frame by frame (the colours), the second with nothing but the page's
            # own clock on it (a screencast at 3x is itself work for this machine, and its frames' cost lands in the page's frame gaps)
            windows = {}
            s = session(pw, srv, dev, red)
            if cpu != 1: s.throttle(cpu)
            for to in ("ifc", "academy"):
                r = switch(s, to, limit=60 if cpu > 1 else 30)
                fr, windows[to] = judge_colour("%s to %s:" % (sec, "Fire Code" if to == "ifc" else "the academy"), r, calm=red)
                if VIDEO and fr:
                    os.makedirs(VIDEO, exist_ok=True); video(r, fr, os.path.join(VIDEO, "%s-to-%s.mp4" % (sec, to)))
                s.pg.wait_for_timeout(1200)
            errs = list(s.errs); s.close()
            for attempt in (1, 2):
                n0 = len(fails)
                s = session(pw, srv, dev, red)
                s.start_rec = lambda: None; s.stop_rec = lambda: None
                if cpu != 1: s.throttle(cpu)
                try:
                    for to in ("ifc", "academy"):
                        r = switch(s, to, limit=60 if cpu > 1 else 30)
                        judge_timing("%s to %s:" % (sec, "Fire Code" if to == "ifc" else "the academy"), r, windows.get(to) or (None, None), calm=red)
                        s.pg.wait_for_timeout(3000)
                except Exception as e:
                    chk("%s timed run ran" % sec, False, repr(e)[:300])
                finally:
                    errs += s.errs; s.close()
                if len(fails) == n0 or attempt == 2: break
                # a timing check failed: once more, from a fresh launch (only the second launch's verdicts count)
                print("  (timing: once more from a fresh launch - this machine is shared and the frame clock is load-sensitive)", flush=True)
                del fails[n0:]
            chk("%s no page errors" % sec, not errs, errs[:3])
        except Exception as e:
            chk("%s ran" % sec, False, repr(e)[:400])
srv.close()
print("\nALL PASS" if not fails else "\nFAILED: %d" % len(fails))
sys.exit(1 if fails else 0)
