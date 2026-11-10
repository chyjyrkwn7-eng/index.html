#!/usr/bin/env python3
"""Record the class switch (Police Academy <-> Fire Code) as a person sees it, and lay it out frame by frame.

  python3 tools/record-b384-switch.py OUTDIR [--device phone|se|laptop] [--cpu 4] [--reduce] [--against OLD/index.html] [--to ifc|academy|both]

Writes, in OUTDIR, per switch: <device>-<to>[-cpuN][-reduce].moments.png (a frame every 100ms from the tap, each labelled with its ms
from the tap, to just after the cover is gone: the sequence at a glance), .sheet.png (every frame), .light.json (each frame's average
light and the page's own log), and, with --frames, the frames themselves as JPEGs (for ffmpeg). CDP screencast: the compositor's own frames and timing
(a screenshot loop misses the fast parts). The Firestore CDN is blocked here, so the class stores load from localStorage."""
import json, os, subprocess, sys, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b384_switchfx_lib as L
from playwright.sync_api import sync_playwright

def arg(n, d=None): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d
OUT = os.path.abspath(sys.argv[1]); os.makedirs(OUT, exist_ok=True)
DEV = arg("--device", "phone"); CPU = float(arg("--cpu", "1")); REDUCE = "--reduce" in sys.argv; TO = arg("--to", "both")
tag = DEV + ("-cpu%g" % CPU if CPU != 1 else "") + ("-reduce" if REDUCE else "")
srv = L.Server()
with sync_playwright() as pw:
    s = L.Session(pw, srv, DEV, reduce_motion=REDUCE).boot()
    s.throttle(CPU)
    for to in (["ifc", "academy"] if TO == "both" else [TO]):
        r = s.switch(to)
        name = "%s-%s" % (tag, to)
        n = L.contact_sheet(r, os.path.join(OUT, name + ".sheet.png"), step=1, cols=14, tw=130)
        # every 100ms from just before the tap to a moment after the cover is gone: the sequence at a glance (the full sheet is every frame)
        t0 = r["t_tap"] * 1000
        gone = next((e["t"] - t0 for e in r["log"] if e.get("mark") == "gone"), None)
        end = (gone if gone is not None else 3500) + 300
        L.pick_sheet(r, list(range(-100, int(end), 100)), os.path.join(OUT, name + ".moments.png"), cols=12, tw=120)
        light = L.analyse(r)
        json.dump({"light": [(x["dt"], round(x["lum"], 1)) for x in light], "log": r["log"][::3]}, open(os.path.join(OUT, name + ".light.json"), "w"))
        if "--frames" in sys.argv:
            d = os.path.join(OUT, name + ".frames"); os.makedirs(d, exist_ok=True)
            t0 = r["frames"][0][0]
            for i, (ts, jpg) in enumerate(r["frames"]): open(os.path.join(d, "%04d.jpg" % i), "wb").write(jpg)
        print("%s: %d frames, %.2fs from the tap to rest" % (name, n, (r["frames"][-1][0] - r["t_tap"]) if r["frames"] else 0), flush=True)
        s.pg.wait_for_timeout(1500)
    print("errors:", s.errs[:3])
    s.close()
srv.close()
