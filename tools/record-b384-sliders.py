#!/usr/bin/env python3
"""Record the slider (Settings > Sound & Haptics > Volume) dragged the way Madison's iOS 26 recording drags his: at rest, a press,
a drag both ways, past both ends, and the release - on an iPhone 17 Pro Max (440x956, installed) at 2x, through CDP's screencast
(the compositor's own frames and timing), in the given themes.

  TMPDIR=/dev/shm python3 tools/record-b384-sliders.py OUTDIR [--accents elite,ink] [--his HIS.mp4] [--toggles]

Writes OUTDIR/ours-<accent>.mp4 (the phone's whole screen), OUTDIR/strip.mp4 (his slider on top when --his is given, then ours in
each accent, cut to the slider's card, side by side in time) and OUTDIR/sheet.png (the moments: rest, pressed, past each end,
released). With --toggles it records Settings > Study's switches instead: a tap each way, then a drag each way (toggles-*.mp4).
Chromium cannot show iOS's own frame pacing, haptics or what WebKit draws; this shows the motion and the look."""
import io, json, os, subprocess, sys, shutil, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b384-sliders.py")).read().split("\nwith sync_playwright() as pw:")[0]
argv = sys.argv[:]; sys.argv = [argv[0]]
G = {"__file__": os.path.join(HERE, "check-b384-sliders.py"), "__name__": "rec"}; exec(src, G)
sys.argv = argv
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw
OUT = os.path.abspath(argv[1]); os.makedirs(OUT, exist_ok=True)
def arg(n, d=None): return argv[argv.index(n) + 1] if n in argv else d
ACCENTS = arg("--accents", "elite,ink").split(",")
HIS = arg("--his")
TOGGLES = "--toggles" in argv
NAMES = {"elite": "Amethyst (purple)", "ink": "Default (orange)", "adept": "Sapphire", "ranger": "Silver"}
touch = G["touch"]

def record(pw, accent):
    srv, G["URL"] = G["g"]["serve"]()
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    ctx, pg, cdp, errs = G["open_page"](br)
    pg.evaluate("(a)=>{ theme.accent = a; theme.mode = 'dark'; applyTheme(); }", accent)
    if TOGGLES:
        pg.evaluate("async()=>{ " + G["COMMON"] + " __sl.calm(); store.seenSettingsTour = true; showAppearance({ page: 'study' }); await __sl.wait(900); }")
        box = pg.evaluate("()=>{ const t = [...document.querySelectorAll('.opt > .box')].find(x => { const c = x.parentElement.querySelector(':scope > input'); return x.getBoundingClientRect().width > 0 && c && !c.disabled; }); t.closest('.settings-card').scrollIntoView({ block: 'center' }); const r = t.getBoundingClientRect(); const c = t.closest('.settings-card').getBoundingClientRect(); return { l: r.left, t: r.top, w: r.width, h: r.height, on: t.parentElement.querySelector(':scope > input').checked, card: [c.top, c.bottom] }; }")
    else:
        pg.evaluate("async()=>{ " + G["COMMON"] + " __sl.calm(); store.seenSettingsTour = true; theme.soundOn = true; theme.soundVolume = .5; showAppearance({ page: 'sound' }); await __sl.wait(900); document.querySelector('.settings-volume').scrollIntoView({ block: 'center' }); }")
    pg.wait_for_timeout(2500)
    frames = []
    def on_frame(p):
        frames.append((p["metadata"]["timestamp"], p["data"]))
        try: cdp.send("Page.screencastFrameAck", {"sessionId": p["sessionId"]})
        except Exception: pass
    cdp.on("Page.screencastFrame", on_frame)
    cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92, "maxWidth": 880, "maxHeight": 1912, "everyNthFrame": 1})
    marks = {}
    def mark(n): marks[n] = pg.evaluate("()=>performance.timeOrigin + performance.now()") / 1000.0
    def glide(x0, x1, y, ms):
        n = max(2, int(ms / 16))
        for i in range(1, n + 1): touch(cdp, "touchMove", x0 + (x1 - x0) * i / n, y); pg.wait_for_timeout(16)
    pg.wait_for_timeout(900); mark("rest")
    if TOGGLES:
        b = box; y = b["t"] + b["h"] / 2
        offx, onx = b["l"] + 2 + 18.5, b["l"] + b["w"] - 2 - 18.5
        for _ in range(2):   # two taps: over and back
            touch(cdp, "touchStart", b["l"] + b["w"] / 2, y); pg.wait_for_timeout(90); touch(cdp, "touchEnd", 0, 0); pg.wait_for_timeout(1100)
        mark("tapped")
        on = pg.evaluate("()=>[...document.querySelectorAll('.opt > .box')].find(x => x.getBoundingClientRect().width > 0 && !x.parentElement.querySelector(':scope > input').disabled).parentElement.querySelector(':scope > input').checked")
        a, z = (onx, offx) if on else (offx, onx)
        touch(cdp, "touchStart", a, y); pg.wait_for_timeout(350); mark("pressed")
        glide(a, z, y, 600); pg.wait_for_timeout(300); touch(cdp, "touchEnd", 0, 0); pg.wait_for_timeout(1000)
        touch(cdp, "touchStart", z, y); pg.wait_for_timeout(350)
        glide(z, a, y, 600); pg.wait_for_timeout(300); touch(cdp, "touchEnd", 0, 0); pg.wait_for_timeout(1200); mark("released")
        crop = (0, max(0, b["card"][0] - 20), 440, min(956, b["card"][1] + 20))
    else:
        q = pg.evaluate(G["INFO"], ".settings-volume input[type=range]")
        t, k = q["track"], q["knob"]; y = t["cy"]
        span = t["w"] - k["w"]; at = lambda f: t["l"] + k["w"] / 2 + f * span
        touch(cdp, "touchStart", k["cx"], y); pg.wait_for_timeout(450); mark("pressed")
        glide(k["cx"], at(.85), y, 800); pg.wait_for_timeout(200)
        glide(at(.85), t["r"] + 70, y, 450); pg.wait_for_timeout(350); mark("past right")
        glide(t["r"] + 70, at(.2), y, 1000); pg.wait_for_timeout(200)
        glide(at(.2), t["l"] - 70, y, 450); pg.wait_for_timeout(350); mark("past left")
        glide(t["l"] - 70, at(.6), y, 700); pg.wait_for_timeout(350)
        touch(cdp, "touchEnd", 0, 0); pg.wait_for_timeout(120); mark("releasing"); pg.wait_for_timeout(1100); mark("released")
        crop = (0, max(0, t["cy"] - 70), 440, min(956, t["cy"] + 70))
    pg.wait_for_timeout(300)
    cdp.send("Page.stopScreencast")
    br.close()
    return frames, marks, crop, errs

def write_mp4(frames, path, crop=None, w=None):
    d = tempfile.mkdtemp(dir="/dev/shm")
    import base64
    lst = []
    for i, (ts, data) in enumerate(frames):
        im = Image.open(io.BytesIO(base64.b64decode(data))).convert("RGB")
        if crop: im = im.crop(tuple(int(v * im.width / 440) for v in crop))
        if w: im = im.resize((w, int(im.height * w / im.width) // 2 * 2))
        if im.height % 2 or im.width % 2: im = im.crop((0, 0, im.width // 2 * 2, im.height // 2 * 2))
        f = os.path.join(d, "%05d.png" % i); im.save(f); lst.append((f, ts))
    with open(os.path.join(d, "list.txt"), "w") as fh:
        for i, (f, ts) in enumerate(lst):
            dur = (lst[i + 1][1] - ts) if i + 1 < len(lst) else 0.5
            fh.write("file '%s'\nduration %.4f\n" % (f, max(.001, dur)))
        fh.write("file '%s'\n" % lst[-1][0])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(d, "list.txt"), "-vf", "fps=60,format=yuv420p",
                    "-c:v", "libx264", "-crf", "16", "-preset", "medium", path], check=True)
    shutil.rmtree(d, ignore_errors=True)

def frame_at(frames, t):
    import base64
    best = min(frames, key=lambda f: abs(f[0] - t))
    return Image.open(io.BytesIO(base64.b64decode(best[1]))).convert("RGB")

with sync_playwright() as pw:
    clips, sheet_rows = [], []
    tag = "toggles" if TOGGLES else "ours"
    for acc in ACCENTS:
        frames, marks, crop, errs = record(pw, acc)
        full = os.path.join(OUT, "%s-%s.mp4" % (tag, acc)); write_mp4(frames, full)
        cut = os.path.join(OUT, "%s-%s-cut.mp4" % (tag, acc)); write_mp4(frames, cut, crop, 880); clips.append(cut)
        row = []
        for name, t in marks.items():
            im = frame_at(frames, t + (0.0 if name != "pressed" else 0)); im = im.crop(tuple(int(v * im.width / 440) for v in crop))
            row.append((name, im))
        sheet_rows.append((NAMES.get(acc, acc), row))
        print("%s: %d frames, %.1fs, errors %s" % (acc, len(frames), frames[-1][0] - frames[0][0], errs), flush=True)
    # his, cut to his control and scaled to the same width
    if HIS:
        his = os.path.join(OUT, "his-toggles-cut.mp4" if TOGGLES else "his-slider-cut.mp4")
        vf = "crop=1320:420:0:1750,scale=880:-2" if not TOGGLES else "crop=1320:500:0:500,scale=880:-2"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", HIS, "-vf", vf + ",fps=60,format=yuv420p", "-an", "-c:v", "libx264", "-crf", "16", his], check=True)
        clips = [his] + clips
    # one strip: every clip stacked, each held on its last frame to the longest
    durs = [float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", c], capture_output=True, text=True).stdout.strip() or 0) for c in clips]
    L = max(durs)
    inputs = sum([["-i", c] for c in clips], [])
    fl = ";".join("[%d:v]tpad=stop_mode=clone:stop_duration=%.2f,setpts=PTS-STARTPTS[v%d]" % (i, L - d + .05, i) for i, d in enumerate(durs))
    fl += ";" + "".join("[v%d]" % i for i in range(len(clips))) + "vstack=inputs=%d,format=yuv420p[o]" % len(clips)
    strip = os.path.join(OUT, "%s-strip.mp4" % ("toggles" if TOGGLES else "slider"))
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + inputs + ["-filter_complex", fl, "-map", "[o]", "-t", "%.2f" % L, "-c:v", "libx264", "-crf", "17", strip], check=True)
    # the moments, as a sheet
    if HIS and not TOGGLES:
        hd = tempfile.mkdtemp(dir="/dev/shm")
        his_moments = [("rest", 0.5), ("pressed", 1.4), ("past right", 5.0), ("past left", 5.5), ("released", 11.6)]
        row = []
        for name, t in his_moments:
            f = os.path.join(hd, "h.png")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", HIS, "-frames:v", "1", "-vf", "crop=1320:420:0:1750,scale=880:-2", f], check=True)
            row.append((name, Image.open(f).convert("RGB").copy()))
        sheet_rows.insert(0, ("iOS 26 (his recording)", row))
    tw = 440
    rows = [(lab, [(n, im.resize((tw, int(im.height * tw / im.width)))) for n, im in r]) for lab, r in sheet_rows]
    cols = max(len(r) for _, r in rows)
    rh = [max(im.height for _, im in r) + 26 for _, r in rows]
    sheet = Image.new("RGB", (cols * (tw + 8) + 8, sum(rh) + 8), (16, 16, 18)); d = ImageDraw.Draw(sheet)
    y = 4
    for (lab, r), h in zip(rows, rh):
        for i, (n, im) in enumerate(r):
            x = 8 + i * (tw + 8); sheet.paste(im, (x, y + 22)); d.text((x + 2, y + 4), "%s - %s" % (lab, n), fill=(230, 230, 235))
        y += h
    sheet.save(os.path.join(OUT, "%s-sheet.png" % ("toggles" if TOGGLES else "slider")))
    print("wrote", OUT)
