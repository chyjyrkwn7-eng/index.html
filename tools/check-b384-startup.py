"""384.124 (startup): the Get Started page's badges clip and its rank ladder.
Madison: "Badges should be a little video in the start up screen. So update the start up, remove the badges from the thing
on the bottom, make badges a badge but only show a few of the ifc ones. Like 10 max. And then the rank will be shown
vertically from bronze to supernova in a cool way."
Read off the page (shape, not label strings or typed numbers):
 clip    - a scene whose video is landing/badges.mp4, after the hundo scene and before the rank scene; the file exists and
           decodes (ffprobe: h264, yuv420p, 780x1690, 30 fps, no audio, under 3.2 MB, 4-30 s); its poster exists and is its
           first frame; the recorder's CLIP_UNITS (the badges the clip shows) holds 1-10 distinct Fire Code chapters, all in
           the bank; the page has two more clips than scenes (the title's two) as before.
 ladder  - the showcase has no badge row and no badge art; it lists every rank in TIER_ORDER_FULL order top to bottom (the
           names are RANK_DISPLAY_NAME's, each with its TIER_UNLOCKS level), strictly increasing y, every flare's centre on
           one vertical line, each rank a button 44px+ each way, the last (Supernova) flare the biggest, all inside the
           screen with no sideways scroll - at 390x844, 440x956 and 834x1194.
 scroll  - with the ladder below the screen its rungs are unlit (flare opacity < .5, line fill scaleY 0); part way, some are
           lit and some not, the lit ones the top ones; scrolled through, every rung is lit (opacity 1) and every half of the
           line full; it moves by transform and opacity only.
 calm    - Reduce motion, the app's own switch (theme.reduceMotion in the saved copy) AND the system's media: every rung
           visible and lit and every line full from the first look, before any scrolling past it, nothing left at opacity 0.
 tap     - a tap on a rank changes the caption.
 errors  - no page errors.
Run:  python3 tools/check-b384-startup.py [clip ladder scroll calm tap] [--against DIR]
      DIR holds an older tree's index.html, landing/ and tools/ (git archive origin/main index.html landing version.json tools
      | tar -x -C /dev/shm/old) - it must FAIL there."""
import functools, http.server, importlib.util, json, os, re, socket, subprocess, sys, threading
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if "--against" in sys.argv:
    ROOT = os.path.abspath(sys.argv[sys.argv.index("--against") + 1])
    if ROOT.endswith("index.html"): ROOT = os.path.dirname(ROOT)
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
TIMEOUT = 180000
DEV = {"p390": (390, 844, 3), "phone": (440, 956, 3), "ipad": (834, 1194, 2)}

ok = True
ERRS = []
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond)
    print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:420], flush=True)


def serve():
    so = socket.socket(); so.bind(("127.0.0.1", 0)); port = so.getsockname()[1]; so.close()
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    http.server.ThreadingHTTPServer.handle_error = lambda *a: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, "http://127.0.0.1:%d/index.html" % port


def page(br, url, dev, calm_app=False, calm_os=False):
    w, h, d = DEV[dev]
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=d, has_touch=True, is_mobile=dev != "ipad",
                         reduced_motion="reduce" if calm_os else "no-preference")
    s = "localStorage.setItem('class26e.frame.ok','go-live-1');"
    if calm_app:   # a saved copy with no account (Get Started still opens) whose theme has Reduce motion on
        s += "localStorage.setItem('class26e.drill.v1', %s);" % json.dumps(json.dumps(
            {"onboardingComplete": False, "lifetime": {"points": 0}, "theme": {"accent": "ink", "reduceMotion": True}}))
    ctx.add_init_script("(()=>{ if(sessionStorage.getItem('__st')) return; sessionStorage.setItem('__st','1'); try{" + s + "}catch(e){} })()")
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: ERRS.append("%s: %s" % (dev, str(e)[:200])))
    pg.goto(url, timeout=TIMEOUT)
    pg.wait_for_selector(".gs-page", timeout=TIMEOUT)
    pg.wait_for_timeout(3500)
    return ctx, pg


SCROLL_TO = """([sel, frac])=>{ const s=document.querySelector('.gs-scroll'), e=document.querySelector(sel); if(!e) return false;
  s.scrollTop += e.getBoundingClientRect().top - innerHeight * frac; return true; }"""

LADDER = """()=>{ const show = document.querySelector('.gs-show'); if(!show) return null;
  const R = e => e.getBoundingClientRect();
  const rungs = [...show.querySelectorAll('.gs-ladder > .gs-rung')];
  const mat = e => { const t = getComputedStyle(e).transform; if(t === 'none') return 1; const m = t.match(/matrix\\(([^)]+)\\)/); return m ? +m[1].split(',')[3] : 1; };
  const rows = rungs.map(r => { const f = r.querySelector('.gs-rung-flare'), b = r.querySelector('button'), fr = R(f), br = R(b);
    const segs = [...r.querySelectorAll('.gs-seg > i')];
    return { tier: r.dataset.rankTier, text: (r.querySelector('.gs-rung-words') || r).textContent.trim(),
      y: fr.top + fr.height / 2, cx: fr.left + fr.width / 2, fw: f.offsetWidth, bw: br.width, bh: br.height, left: br.left, right: br.right,
      op: +getComputedStyle(f).opacity, wop: +getComputedStyle(r.querySelector('.gs-rung-words')).opacity,
      lit: r.classList.contains('is-lit'), segs: segs.map(mat), vis: getComputedStyle(f).visibility };
  });
  const tr = e => getComputedStyle(e).transitionProperty.split(',').map(x => x.trim()).filter(x => x !== 'all' || getComputedStyle(e).transitionDuration !== '0s');
  const moving = [...show.querySelectorAll('.gs-rung-flare, .gs-rung-words, .gs-rung-halo, .gs-seg > i')];
  return { rows, badgeRow: show.querySelectorAll('.gs-badges, .gs-badge-btn, svg.badge-art').length,
    order: typeof TIER_ORDER_FULL !== 'undefined' ? TIER_ORDER_FULL : [],
    names: typeof RANK_DISPLAY_NAME !== 'undefined' ? TIER_ORDER_FULL.map(t => RANK_DISPLAY_NAME[t]) : [],
    levels: typeof TIER_UNLOCKS !== 'undefined' ? TIER_ORDER_FULL.map(t => TIER_UNLOCKS[t] && TIER_UNLOCKS[t].level) : [],
    trans: [...new Set(moving.flatMap(tr))], side: document.querySelector('.gs-scroll').scrollWidth - innerWidth, iw: innerWidth,
    calm: document.documentElement.dataset.reduceMotion };
}"""


def sec_clip(br, url):
    print("\nclip: a badges scene, its clip a real file, at most ten badges in it")
    rec = os.path.join(ROOT, "tools", "record-landing-badges.py")
    units = []
    if os.path.exists(rec):
        m = re.search(r"CLIP_UNITS = \[(.*?)\]", open(rec, encoding="utf-8").read(), re.S)
        units = re.findall(r'"([^"]+)"', m.group(1)) if m else []
    chk("the recorder lists the clip's badges: 1-10, all different (%d)" % len(units), 1 <= len(units) <= 10 and len(set(units)) == len(units), units)
    mp4, jpg = os.path.join(ROOT, "landing", "badges.mp4"), os.path.join(ROOT, "landing", "badges.jpg")
    chk("landing/badges.mp4 and its poster exist", os.path.isfile(mp4) and os.path.isfile(jpg), [mp4, jpg])
    if os.path.isfile(mp4):
        pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", mp4],
                                       capture_output=True, text=True).stdout or "{}")
        vs = [s for s in pr.get("streams", []) if s.get("codec_type") == "video"]
        au = [s for s in pr.get("streams", []) if s.get("codec_type") == "audio"]
        v = vs[0] if vs else {}
        dur, size = float(pr.get("format", {}).get("duration", 0)), os.path.getsize(mp4)
        chk("it decodes: h264 yuv420p %sx%s at %s, no audio, %.1fs, %d KB" % (v.get("width"), v.get("height"), v.get("r_frame_rate"), dur, size // 1024),
            v.get("codec_name") == "h264" and v.get("pix_fmt") == "yuv420p" and v.get("width") == 780 and v.get("height") == 1690
            and v.get("r_frame_rate") == "30/1" and not au and 4 <= dur <= 30 and size < 3.2 * 1024 * 1024, [v, au, dur, size])
        dec = subprocess.run(["ffmpeg", "-v", "error", "-i", mp4, "-f", "null", "-"], capture_output=True, text=True)
        chk("every frame decodes with no error", dec.returncode == 0 and not dec.stderr.strip(), dec.stderr[:300])
        if os.path.isfile(jpg):
            from PIL import Image, ImageChops, ImageStat
            import io
            raw = subprocess.run(["ffmpeg", "-v", "error", "-i", mp4, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
            a = Image.open(io.BytesIO(raw)).convert("RGB"); b = Image.open(jpg).convert("RGB").resize(a.size)
            diff = sum(ImageStat.Stat(ImageChops.difference(a, b)).mean) / 3
            chk("the poster is the clip's first frame (mean diff %.1f)" % diff, diff < 6, diff)
    ctx, pg = page(br, url, "phone")
    r = pg.evaluate("""(units)=>{ const keys = [...document.querySelectorAll('.gs-scene video')].map(v => v.dataset.gs);
      const all = document.querySelectorAll('.gs-page video').length;
      const bank = typeof IFC_UNITS_FOR_GATE !== 'undefined' ? null : null;
      return { keys, scenes: document.querySelectorAll('.gs-scene').length, all,
               badgeSrc: (document.querySelector('.gs-scene video[data-gs="badges"]') || {}).getAttribute ? document.querySelector('.gs-scene video[data-gs="badges"]').getAttribute('src') : null }; }""", units)
    k = r["keys"]
    chk("a badges scene with its clip (landing/badges.mp4): %s" % k, "badges" in k and r["badgeSrc"] == "landing/badges.mp4", r)
    chk("it comes after the hundo scene and before the rank scene", "badges" in k and "hundo" in k and "rank" in k
        and k.index("hundo") < k.index("badges") < k.index("rank"), k)
    chk("one clip per scene, two more beside the title (%d scenes, %d clips)" % (r["scenes"], r["all"]), r["all"] == r["scenes"] + 2 and len(k) == r["scenes"], r)
    ctx.close()
    # the clip's chapters are Fire Code's own (the bank is read in the Fire Code class)
    if units:
        spec = importlib.util.spec_from_file_location("rli", os.path.join(ROOT, "tools", "record-landing-ifc.py"))
        try:
            ri = importlib.util.module_from_spec(spec); spec.loader.exec_module(ri)
            ri.rl.ROOT = ROOT
            srv2, port2 = ri.rl.serve()
            c2, p2 = ri.rl.new_page(br, port2, ri.SEED, ri.IN_IFC)
            bank = p2.evaluate("()=>[window.NOVA_CLASS, unitsInTeachingOrder()]")
            c2.close(); srv2.shutdown()
            chk("all %d are Fire Code chapters in the bank" % len(units), bank[0] == "ifc" and all(u in bank[1] for u in units), [u for u in units if u not in bank[1]])
        except Exception as e:
            chk("the Fire Code bank could be read", False, e)


def sec_ladder(br, url):
    print("\nladder: no badge row; every rank top to bottom, Bronze first, Supernova last and biggest")
    for dev in ("p390", "phone", "ipad"):
        ctx, pg = page(br, url, dev)
        pg.evaluate(SCROLL_TO, [".gs-show", .02]); pg.wait_for_timeout(600)
        L = pg.evaluate(LADDER)
        if not L: chk("%s: the showcase is on the page" % dev, False, "no .gs-show"); ctx.close(); continue
        rows = L["rows"]
        chk("%s: no badge row and no badge art in it (%d)" % (dev, L["badgeRow"]), L["badgeRow"] == 0, L["badgeRow"])
        chk("%s: a rung for every rank, in TIER_ORDER_FULL order (%s)" % (dev, [x["tier"] for x in rows]),
            len(L["order"]) >= 2 and [x["tier"] for x in rows] == L["order"], [x["tier"] for x in rows])
        named = len(rows) == len(L["names"]) and all(nm and nm in x["text"] and str(lv) in x["text"] for x, nm, lv in zip(rows, L["names"], L["levels"]))
        chk("%s: each names its rank and its level, read off the app" % dev, named, [x["text"] for x in rows])
        ys = [x["y"] for x in rows]
        chk("%s: top to bottom, strictly increasing y (%s)" % (dev, [round(y) for y in ys]), len(ys) > 1 and all(b > a + 20 for a, b in zip(ys, ys[1:])), ys)
        cxs = [x["cx"] for x in rows]
        chk("%s: every flare's centre on one vertical line (spread %.1fpx)" % (dev, max(cxs) - min(cxs) if cxs else -1), cxs and max(cxs) - min(cxs) <= 1.5, cxs)
        chk("%s: every rank is a 44px+ button (smallest %.0fx%.0f)" % (dev, min((x["bw"] for x in rows), default=0), min((x["bh"] for x in rows), default=0)),
            rows and all(x["bw"] >= 44 and x["bh"] >= 44 for x in rows), [(x["bw"], x["bh"]) for x in rows])
        fws = [x["fw"] for x in rows]
        chk("%s: the last flare (the top rank) is the biggest, laid out (%s)" % (dev, [round(f) for f in fws]), len(fws) > 1 and fws[-1] > max(fws[:-1]) * 1.15, fws)
        chk("%s: inside the screen, no sideways scroll" % dev, rows and all(x["left"] >= 0 and x["right"] <= L["iw"] for x in rows) and L["side"] <= 0,
            [(x["left"], x["right"]) for x in rows])
        ctx.close()


def sec_scroll(br, url):
    print("\nscroll: the line fills and the ranks light as the ladder comes up the screen")
    for dev in ("phone", "ipad"):
        ctx, pg = page(br, url, dev)
        pg.evaluate(SCROLL_TO, [".gs-show", 1.5]); pg.wait_for_timeout(1200)
        pg.evaluate(SCROLL_TO, [".gs-ladder", 1.2]); pg.wait_for_timeout(1500)
        A = pg.evaluate(LADDER)
        if not A or not A["rows"]: chk("%s: the ladder is on the page" % dev, False, "none"); ctx.close(); continue
        chk("%s: below the screen every rung is unlit (flare opacity <= %.2f, line fill %s)" % (dev, max(x["op"] for x in A["rows"]), max(max(x["segs"] or [0]) for x in A["rows"])),
            max(x["op"] for x in A["rows"]) < .5 and max(max(x["segs"] or [0]) for x in A["rows"]) < .05, A["rows"])
        # part way: the third rung at the middle of the screen
        pg.evaluate(SCROLL_TO, [".gs-ladder > .gs-rung:nth-child(3)", .6]); pg.wait_for_timeout(2500)
        B = pg.evaluate(LADDER)
        lit = [x["op"] > .95 for x in B["rows"]]
        chk("%s: part way, the top rungs are lit and the bottom ones not (%s)" % (dev, "".join("L" if v else "." for v in lit)),
            any(lit) and not all(lit) and lit == sorted(lit, reverse=True), [x["op"] for x in B["rows"]])
        chk("%s: the computed styles changed with the scroll (flare opacity, line fill)" % dev,
            any(abs(a["op"] - b["op"]) > .3 for a, b in zip(A["rows"], B["rows"])) and any(max(b["segs"] or [0]) > .95 for b in B["rows"]),
            [[a["op"], b["op"]] for a, b in zip(A["rows"], B["rows"])])
        pg.evaluate("()=>{ const s=document.querySelector('.gs-scroll'); s.scrollTop = s.scrollHeight; }"); pg.wait_for_timeout(3500)
        C = pg.evaluate(LADDER)
        chk("%s: scrolled through, every rung lit and every half of the line full" % dev,
            all(x["op"] > .99 and x["wop"] > .99 for x in C["rows"]) and all(s > .99 for x in C["rows"] for s in x["segs"]), C["rows"])
        chk("%s: it moves by transform and opacity only (%s)" % (dev, C["trans"]), set(C["trans"]) <= {"opacity", "transform"}, C["trans"])
        ctx.close()


def sec_calm(br, url):
    print("\ncalm: Reduce motion (the app's switch and the system's): all of it there and lit at once")
    for label, app, osr in (("the app's switch", True, False), ("the system's setting", False, True)):
        for dev in ("phone", "ipad"):
            ctx, pg = page(br, url, dev, calm_app=app, calm_os=osr)
            pg.evaluate(SCROLL_TO, [".gs-show", .02]); pg.wait_for_timeout(250)
            L = pg.evaluate(LADDER)
            if not L or not L["rows"]: chk("%s, %s: the ladder is on the page" % (dev, label), False, "none"); ctx.close(); continue
            if app: chk("%s: the switch is on in the page (data-reduce-motion %s)" % (dev, L["calm"]), L["calm"] == "true", L["calm"])
            show_op = pg.evaluate("()=>+getComputedStyle(document.querySelector('.gs-show')).opacity")
            chk("%s, %s: every rung visible and lit, every line full, the section shown (flares %s, words %s, section %.2f)" % (
                dev, label, min(x["op"] for x in L["rows"]), min(x["wop"] for x in L["rows"]), show_op),
                all(x["op"] > .99 and x["wop"] > .99 and x["vis"] == "visible" for x in L["rows"]) and all(s > .99 for x in L["rows"] for s in x["segs"]) and show_op > .99,
                L["rows"])
            ctx.close()


def sec_tap(br, url):
    print("\ntap: a rank names itself")
    ctx, pg = page(br, url, "phone")
    pg.evaluate(SCROLL_TO, [".gs-show", .02]); pg.wait_for_timeout(1500)
    c0 = pg.evaluate("()=>(document.querySelector('.gs-show-cap')||{}).textContent")
    pg.evaluate("()=>{ const b = document.querySelectorAll('.gs-ladder .gs-rung-btn')[2]; b && b.click(); }"); pg.wait_for_timeout(300)
    c1 = pg.evaluate("()=>(document.querySelector('.gs-show-cap')||{}).textContent")
    chk("a tap on a rank changes the caption (%r -> %r)" % (c0, c1), bool(c1) and c1 != c0 and len(c1) > 3, [c0, c1])
    ctx.close()


SECS = {"clip": sec_clip, "ladder": sec_ladder, "scroll": sec_scroll, "calm": sec_calm, "tap": sec_tap}
if __name__ == "__main__":
    args = [a for i, a in enumerate(sys.argv[1:]) if not a.startswith("--") and (i == 0 or sys.argv[i] != "--against")]
    want = [a for a in args if a in SECS] or list(SECS)
    print("tree:", ROOT)
    srv, url = serve()
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME)
        for s in want: SECS[s](br, url)
        br.close()
    srv.shutdown()
    chk("no page errors", not ERRS, ERRS)
    print("\nALL PASS" if ok else "\nSOME FAILED")
    sys.exit(0 if ok else 1)
