#!/usr/bin/env python3
"""The top switchers' motion, per frame (384 r18): every tap between every pair of segments and a drag, on every device class,
at 4x CPU throttle (`--cpu N`), with the frame times, the overshoot, any change of the thumb's size or the track's, how far the
thumb pokes out of the track and whether any layout property of the thumb moved. Run it on the build before (`--against REV`) and
on this one for the before / after numbers.

  python3 tools/record-b384-seg.py                          # this build, every device class, 4x CPU
  python3 tools/record-b384-seg.py --against /tmp/prev-index.html --json before.json
  python3 tools/record-b384-seg.py --devs phone-installed --only profile --cpu 1
"""
import json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import b384_seg_lib as L
from playwright.sync_api import sync_playwright
CPU = int(L.arg("--cpu", "4")); ONLY = re.compile(L.arg("--only")) if L.arg("--only") else None
DEVS = L.arg("--devs"); JSON_OUT = L.arg("--json")
rows = []

def agg(vals, f):
    vals = [v for v in vals if v is not None]
    return f(vals) if vals else 0

def run(pg, ptr, dev, sw):
    st = L.open_switcher(pg, sw)
    if not st or len(st["segs"]) < 2: print("  %s: not on screen" % sw[0]); return
    n = len(st["segs"]); out = {"taps": [], "drags": []}
    rest_th = st["thumb"]; rest_seg = st["seg"]
    def tap(i, sample):
        s = pg.evaluate(L.STATE, [sw[2], sw[3]]); b = s["segs"][i]["box"]
        if sample: pg.evaluate(L.SAMPLER, [sw[2]])
        ptr.down(L.cx(b), L.cy(b)); pg.wait_for_timeout(50); ptr.up(); pg.wait_for_timeout(1000)
        return L.frames(pg) if sample else None
    for i in range(n):
        for j in range(n):
            if i == j: continue
            tap(i, False); pg.wait_for_timeout(300)
            s = pg.evaluate(L.STATE, [sw[2], sw[3]])
            if L.lit_index(s) != i: print("   (could not start on %d)" % i); continue
            rest_th = s["thumb"]; rest_seg = s["seg"]; c1 = L.cx(s["segs"][j]["box"])
            fr = tap(j, True)
            a = L.analyse(fr, c1, rest_th, rest_seg)
            if a: a["pair"] = "%d>%d" % (i, j); out["taps"].append(a)
    # a drag from the lit segment 70% of the way to its neighbour, held, then let go
    s = pg.evaluate(L.STATE, [sw[2], sw[3]]); i0 = L.lit_index(s); i1 = i0 + 1 if i0 + 1 < n else i0 - 1
    x0, x1, y = L.cx(s["segs"][i0]["box"]), L.cx(s["segs"][i1]["box"]), L.cy(s["segs"][i0]["box"])
    rest_th = s["thumb"]; rest_seg = s["seg"]
    pg.evaluate(L.SAMPLER, [sw[2]])
    ptr.down(x0, y); pg.wait_for_timeout(90)
    for k in range(1, 19): ptr.move(x0 + (x1 - x0) * .7 * k / 18, y); pg.wait_for_timeout(16)
    pg.wait_for_timeout(140)
    held = pg.evaluate(L.STATE, [sw[2], sw[3]])
    xf = x0 + (x1 - x0) * .7
    follow_err = abs(L.cx(L.vis({"lens": None, "th": held["thumb"]})) - xf)
    ptr.up(); pg.wait_for_timeout(1000)
    fr = L.frames(pg); a = L.analyse(fr, x1, rest_th, rest_seg)
    if a: a["follow_err"] = follow_err; out["drags"].append(a)
    end = pg.evaluate(L.STATE, [sw[2], sw[3]])
    out["drag_lit"] = (L.lit_index(end), i1)
    return out

def summarise(tag, o):
    t = o["taps"]
    if not t: print("  %s: no moves seen" % tag); return
    g = lambda k, f=max: agg([x.get(k) for x in t if x.get("moved")], f)
    d = o["drags"][0] if o["drags"] else {}
    print("  %-18s taps %2d  start %4.0fms  dur %4.0fms | overshoot %.2fpx backstep %.2fpx | thumb size +%.1f%%  track +%.1f%%  poke %.1fpx | frame dt mean %.1f p95 %.1f max %.1fms  dropped %d | layout changes %d"
          % (tag, len(t), g("start_ms"), g("dur_ms"), g("overshoot"), g("backstep"), 100 * g("size"), 100 * g("swell"), g("poke"), g("dt_mean"), g("dt_p95"), g("dt_max"), g("dropped", sum), g("layout_changes")))
    if d: print("  %-18s drag: follow err %.1fpx  size +%.1f%% track +%.1f%% poke %.1fpx  overshoot %.2fpx  end err %.2fpx  dt p95 %.1f max %.1f  lit %s" % ("", d.get("follow_err", 0), 100 * d.get("size", 0), 100 * d.get("swell", 0), d.get("poke", 0), d.get("overshoot", 0), d.get("end_err", 0), d.get("dt_p95", 0), d.get("dt_max", 0), o.get("drag_lit")))

def main():
    srv, url = L.g["serve"]()
    res = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=L.g["CHROME"])
        for dev in L.DEVICES:
            if DEVS and dev["name"] not in DEVS.split(","): continue
            ctx, pg, errs = L.open_page(br, dev, "academy", url)
            cdp = ctx.new_cdp_session(pg)
            if CPU > 1: cdp.send("Emulation.setCPUThrottlingRate", {"rate": CPU})
            ptr = L.Pointer(pg, ctx, dev["touch"])
            print("%s (%dx%d dpr%d, %s, cpu %dx)" % (dev["name"], dev["w"], dev["h"], dev["dpr"], "finger" if dev["touch"] else "mouse", CPU), flush=True)
            for sw in L.SWITCHERS:
                if ONLY and not ONLY.search(sw[0]): continue
                if "academy" not in sw[4]: continue
                try:
                    o = run(pg, ptr, dev, sw)
                    if o: res["%s|%s" % (dev["name"], sw[0])] = o; summarise(sw[0], o)
                except Exception as e: print("  %s: FAILED %s" % (sw[0], str(e).splitlines()[0][:200]))
                L.close_chat(pg)
            if errs: print("  page errors:", errs[:3])
            ctx.close()
        br.close()
    srv.shutdown()
    if JSON_OUT: json.dump(res, open(JSON_OUT, "w"), indent=1)

main()
