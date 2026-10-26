#!/usr/bin/env python3
"""Records the four clips on the Get Started page (landing/*.mp4 + a first-frame landing/*.jpg).

  python3 tools/record-landing.py [test|hundo|rank|customize ...]

Built on record-cutscenes.py's helpers (a used account, CDP screencast). Each clip is a phone-shaped
360x780 page at 1.5x, muted, 7-15 seconds, encoded small (x264, crf 29, no audio) because the page
loads them over the web. The page behind a clip starts in the app's own dark, so there is no white
flash at the head of any of them, and the first frames (before anything has painted) are cut."""
import os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
src = src.replace("device_scale_factor=1)", "device_scale_factor=1.5)").replace('rsplit("/tools/", 1)[0]', 'rsplit("/tools/", 1)[0]')
g = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, g)
ROOT = g["ROOT"]; OUT = os.path.join(ROOT, "landing")
FFMPEG = "ffmpeg"

def scene_test(pg, rec):
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(500)
    rec.start(); pg.wait_for_timeout(500)
    g["start_unit_run"](pg, "Identity Crimes")
    pg.wait_for_selector(".choice", timeout=25000); pg.wait_for_timeout(900)
    for k in range(5):
        pg.evaluate("""()=>{const r=correctSlot(order[pos]); document.querySelector('.choice[data-index="'+r+'"]').click();}""")
        pg.wait_for_timeout(1100)
        p = pg.evaluate("()=>pos")
        pg.evaluate("()=>document.getElementById('nextbtn')?.click()")
        for _ in range(30):
            pg.wait_for_timeout(120)
            if pg.evaluate("()=>pos") != p: break
        pg.wait_for_timeout(500)

def scene_hundo(pg, rec):
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(400)
    g["start_unit_run"](pg, "Identity Crimes")
    g["answer_all"](pg, upto=1)
    rec.start(); pg.wait_for_timeout(700)
    pg.evaluate("""()=>{const r=correctSlot(order[pos]); document.querySelector('.choice[data-index="'+r+'"]').click();}""")
    pg.wait_for_timeout(1200)
    pg.evaluate("()=>document.getElementById('nextbtn').click()")
    pg.wait_for_timeout(9500)

def scene_rank(pg, rec):
    pg.evaluate(g["SEED_RANK"], "ranger")
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(700)
    rec.start(); pg.wait_for_timeout(300)
    pg.evaluate("(k)=>{store.pendingTierCutscene=k; playTierCutscene(k)}", "ranger")
    pg.wait_for_timeout(15000)

def scene_customize(pg, rec):
    pg.evaluate("()=>showCustomize('character')"); pg.wait_for_timeout(1000)
    rec.start(); pg.wait_for_timeout(900)
    for k in (2, 5, 8, 3, 6, 1):
        pg.evaluate("(k)=>{ const o=[...document.querySelectorAll('.screen-customize .avatarchar-option:not(.locked)')]; if(o[k]) o[k].click(); }", k)
        pg.wait_for_timeout(1500)

SCENES = {"test": scene_test, "hundo": scene_hundo, "rank": scene_rank, "customize": scene_customize}

def encode(frames, name):
    import io
    from PIL import Image
    t0 = frames[0][0]
    d = tempfile.mkdtemp(prefix="landing-")
    lst = os.path.join(d, "list.txt")
    # drop the first 0.25s (a page that is still painting), keep the timing of the rest
    keep = [(t, b) for t, b in frames if t - t0 >= .25] or frames
    with open(lst, "w") as f:
        for i, (t, b) in enumerate(keep):
            fn = os.path.join(d, "%05d.jpg" % i); open(fn, "wb").write(b)
            dur = (keep[i + 1][0] - t) if i + 1 < len(keep) else .5
            f.write("file '%s'\nduration %.3f\n" % (fn, min(dur, 1.0)))
        f.write("file '%s'\n" % os.path.join(d, "%05d.jpg" % (len(keep) - 1)))
    os.makedirs(OUT, exist_ok=True)
    mp4 = os.path.join(OUT, name + ".mp4")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-vf", "fps=30,scale=540:-2", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "29", "-preset", "slow",
                    "-movflags", "+faststart", "-an", mp4], check=True)
    Image.open(io.BytesIO(keep[min(len(keep) - 1, 3)][1])).convert("RGB").resize((540, 1170)).save(os.path.join(OUT, name + ".jpg"), quality=78)
    # a clip's still is the moment that sells it, not its first frame
    still = {"hundo": 11.5, "rank": 9}.get(name)
    if still: subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-ss", str(still), "-i", mp4, "-frames:v", "1", "-q:v", "4", os.path.join(OUT, name + ".jpg")], check=True)
    print("  %-10s %3d frames  %6.0f KB" % (name, len(keep), os.path.getsize(mp4) / 1024))

def main(argv):
    want = argv or list(SCENES)
    srv, port = g["serve"]()
    with g["sync_playwright"]() as pw:
        br = pw.chromium.launch(executable_path=g["CHROME"])
        for name in want:
            ctx, pg = g["new_page"](br, port, 360, 780, g["SEED"])
            rec = g["Recorder"](pg)
            SCENES[name](pg, rec)
            frames = rec.stop(); ctx.close()
            encode(frames, name)
        br.close()
    srv.shutdown()

if __name__ == "__main__":
    main(sys.argv[1:])
