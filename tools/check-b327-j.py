#!/usr/bin/env python3
"""Build 327 (b327j): the grade box red into green with no grey, and its
sound on the number.

  python3 tools/check-b327-j.py [--against FILE] [--only A,B,C,D,E,F]

Madison (Oct 20, after the build 327 videos): "The grade box is still grey?
It was red then grey then green? That regressed badly and needs to be fixed.
The sound effects aren't perfectly lined up with the percentage grade going
up, fix that ... The ufo sound effect is missing the scan and steal of the
grade. Ensure when you get on an answer streak that has a sound effect that's
satisfying. Ensure the unlock banner sound effect is nice."

A. THE CARD IS NEVER GREY. A real results screen (summarize()) on the page's
   own clock (the recorder's: timers, rAF, performance.now and every
   animation stepped 1/30s a frame), every frame from the card's first frame
   through the landing and a 100's hand-off: the rim (top row and left
   column), the wash under the top edge, the number while it counts, and
   every unit bar are read off the pixels and none may be a neutral grey (a
   red and a green blended). A pass, a fail, a 100 on Confetti and on
   Underwater, and a pass on an iPad. A fail never shows green; a pass ends
   green; a 100 ends in its effect's colours.
B. EVERY TICK IS ON A CHANGE OF THE NUMBER. Same runs: each res.bar.tick is
   in a frame where the number changed, pitched by the number it changed to;
   a frame where the number changed with no tick has had one in the last
   SND_GRADE_GAP_MS; the landing's sound is in the frame the real grade goes
   on the card.
C. THE UFO SCANS AND STEALS THE GRADE (sound). hundo.ufo, rendered offline:
   energy at the scan (just after the landing), the lock, the grab of the
   score (7.38s) and the take-off - and those beats are the new parts of the
   score (opts the design reads).
D. A STREAK IS A SOUND YOU WANT. One sound for each of the pop's eight
   looks, every one rendering, each longer than the one below it, the top
   tiers resolving to D major, each played in the same task as its pop and
   at its own tier (10 the first; 350 and every 50 after the eighth).
E. THE UNLOCK BANNER. res.unlock.banner, its own sound: a swell into a bell
   chord that peaks as the card lands, played as the card starts to rise.
F. THE SECRET FLARE SCENES ARE SCORED. They were the one set of cutscenes
   with no sound. Each has a score heard on its own beats, played as the
   scene opens and stopped with it; the find in a test speaks the key.

Every section fails on 7ec06e0 and passes on this build.
"""
import functools, http.server, io, json, os, re, socket, sys, threading
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


SRC = arg("--against") or os.path.join(ROOT, "index.html")
ONLY = set((arg("--only") or "A,B,C,D,E,F").split(","))
_rs = open(os.path.join(ROOT, "tools", "record-sound.py")).read()
CLOCK = re.search(r'CLOCK = r"""(.*?)"""', _rs, re.S).group(1)
STUB = re.search(r'FIRESTORE_STUB = """(.*?)"""', _rs, re.S).group(1)
SETUP = re.search(r'SETUP = r"""(.*?)"""', _rs, re.S).group(1)
BODY = open(SRC).read().replace("let fbDb = null;", "let fbDb = null;" + STUB, 1)
BUILD = (re.search(r'APP_BUILD\s*=\s*"([^"]+)"', BODY) or [None, "x"])[1]
s = socket.socket(); s.bind(("127.0.0.1", 0)); PORT = s.getsockname()[1]; s.close()


class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass


SRV = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Q, directory=ROOT))
threading.Thread(target=SRV.serve_forever, daemon=True).start()
SEED = "try{['class26e.freshstart','1','class26e.frame.ok','go-live-1','class26e.intro.seen','9','class26e.unithold.tip','1','class26e.penal124256.seen','1','class26e.penal256578.seen','1','class26e.weekrecap.v1','9999-12-31','class26e.soundon.327','1'].forEach((v,i,l)=>{ if(i%2===0) localStorage.setItem(v,l[i+1]); });}catch(e){}"

FAILS = []


def ck(name, ok, info=None):
    print(("  PASS  " if ok else "  FAIL  ") + name + ("" if ok or info is None else "  -> " + str(info)[:400]))
    if not ok:
        FAILS.append(name)


# A fabricated run put through the real summarize(): the first n-good asked twice
RUN = """([unit, n, good, fx]) => {
  if(fx){ store.lifetime = store.lifetime || {}; store.lifetime.perfectTests = 900; store.hundoFx = fx; }
  cfg.mode = 'drill'; cfg.source = 'all'; cfg.units = [unit]; cfg.size = 0;
  order = QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === unit && (typeof inWholeUnit !== 'function' || inWholeUnit(i))).slice(0, n);
  runTrackable = true; timedOut = false; runMode = 'drill'; runLabel = null; isMissedRetake = false;
  practiceTestMinutes = null; inVirtualRoom = false; attempts = {}; picked = {}; timedOutSet = {};
  try{ firstPick = {}; }catch(e){}
  order.forEach((qi, k) => { const oo = optionOrder(qi), right = oo.indexOf(QUESTIONS[qi].answer);
    attempts[qi] = k < n - good ? 2 : 1; picked[qi] = right; try{ if(k < n - good) firstPick[qi] = (right + 1) % oo.length; }catch(e){} });
  runStartTime = Date.now() - 42000; testInProgress = true; pos = order.length - 1;
  summarize(); return true; }"""

SPY = r"""() => {
  window.__plays = [];
  const P = window.playSound;
  window.playSound = (id, o) => { window.__plays.push({ id, t: performance.now(), o: o && typeof o === 'object' ? JSON.parse(JSON.stringify(o)) : null }); return null; };
}"""

READ = r"""() => { const g = document.querySelector('.rs-card.rs-grade'); if(!g) return null;
  const r = g.getBoundingClientRect(), pe = g.querySelector('.rs-pct');
  const pr = pe ? pe.getBoundingClientRect() : null;
  const bars = [...g.querySelectorAll('.unit-breakdown-fill')].map(f => { const b = f.getBoundingClientRect(), t = (f.parentNode || f).getBoundingClientRect();
    return [Math.max(b.left, t.left), b.top, Math.min(b.right, t.right), b.bottom]; });
  return { t: performance.now(), cls: g.className, op: +getComputedStyle(g).opacity, box: [r.left, r.top, r.right, r.bottom],
    pct: pe ? pe.textContent.trim() : null, pbox: pr ? [pr.left, pr.top, pr.right, pr.bottom] : null, bars,
    tone: !!g.querySelector('.rs-grade-tone'), plays: window.__plays.length }; }"""


def chroma(p):
    m = max(p)
    return (m - min(p)) / m if m else 0


def rim_wash(im, box, scale):
    x0, y0, x1, y1 = [int(round(v * scale)) for v in box]
    W, H = im.size
    x0 = max(0, x0); y0 = max(0, y0); x1 = min(W - 1, x1); y1 = min(H - 1, y1)
    rim = [im.getpixel((x, y0 + 1)) for x in range(x0 + 14, x1 - 14, 2)] + [im.getpixel((x0 + 1, y)) for y in range(y0 + 14, min(y1 - 14, y0 + 220), 2)]
    wash = [im.getpixel((x, min(H - 1, y0 + 6))) for x in range(x0 + 14, x1 - 14, 2)]
    rn = sum(1 for p in rim if max(p) > 60 and chroma(p) < .3)
    wn = sum(1 for p in wash if max(p) > 35 and max(p) - min(p) < 10)
    import colorsys
    hue = lambda p: colorsys.rgb_to_hsv(*[v / 255 for v in p])[0] * 360
    col = [p for p in rim if max(p) > 60 and chroma(p) >= .3]
    rg = sum(1 for p in col if 120 <= hue(p) <= 165)
    rr = sum(1 for p in col if hue(p) >= 330 or hue(p) <= 20)
    return rn, wn, rg, rr, len(rim)


def number_grey(im, pbox, scale):
    x0, y0, x1, y1 = [int(round(v * scale)) for v in pbox]
    W, H = im.size
    px = [im.getpixel((x, y)) for x in range(max(0, x0), min(W, x1), 2) for y in range(max(0, y0), min(H, y1), 2)]
    bright = [p for p in px if max(p) > 110]
    return sum(1 for p in bright if chroma(p) < .3), len(bright)


def bars_grey(im, bars, scale):
    out = 0
    for b in bars:
        x0, y0, x1, y1 = [int(round(v * scale)) for v in b]
        if x1 - x0 < 6: continue
        ym = (y0 + y1) // 2
        px = [im.getpixel((x, ym)) for x in range(x0 + 2, x1 - 2)]
        out = max(out, sum(1 for p in px if max(p) > 60 and chroma(p) < .3))
    return out


def run_case(pw, label, good, fx=None, size=(440, 956), n=12, frames=260):
    from PIL import Image
    br = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    ctx = br.new_context(viewport={"width": size[0], "height": size[1]}, device_scale_factor=1)
    ctx.add_init_script(SEED)
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.route("**/index.html", lambda r: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    pg.route("**/version.json*", lambda r: r.fulfill(status=200, headers={"content-type": "application/json"}, body='{"build":"%s","frameId":"","force":false}' % BUILD))
    pg.goto("http://127.0.0.1:%d/index.html" % PORT)
    pg.wait_for_timeout(2600)
    pg.evaluate(SETUP)
    pg.evaluate("()=>{ showHome(); }"); pg.wait_for_timeout(400)
    pg.evaluate(CLOCK); pg.evaluate(SPY)
    gap = pg.evaluate("()=>typeof SND_GRADE_GAP_MS === 'number' ? SND_GRADE_GAP_MS : 0")
    pg.evaluate(RUN, ["Identity Crimes", n, good, fx])
    rows = []
    seen_land = None
    for f in range(frames):
        pg.evaluate("async () => await __clk.advance(1000/30)")
        st = pg.evaluate(READ)
        if not st:
            continue
        st["f"] = f
        landed = "rs-graded" in st["cls"]
        if st["op"] > .05 and (st["tone"] or not landed or seen_land is None or f <= seen_land + 4):
            im = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
            st["rim"] = rim_wash(im, st["box"], 1)
            if os.environ.get("B327J_DUMP") and (st["rim"][0] > 3 or st["rim"][1] > 3):
                im.save(os.path.join(os.environ["B327J_DUMP"], "%s-%03d.png" % (re.sub(r"\W+", "_", label), f)))
            if not landed and st["pbox"]:
                st["num"] = number_grey(im, st["pbox"], 1)
            st["bargrey"] = bars_grey(im, st["bars"], 1)
        if landed and seen_land is None:
            seen_land = f
        rows.append(st)
        if seen_land is not None and f > seen_land + 4 and not st["tone"]:
            break
    plays = pg.evaluate("()=>window.__plays")
    pct = pg.evaluate("()=>{ const g = document.querySelector('.rs-card.rs-grade .rs-pct'); return g ? g.textContent.trim() : null; }")
    br.close()
    return {"label": label, "rows": rows, "plays": plays, "gap": gap, "errs": errs, "final": pct, "good": good, "n": n, "fx": fx}


def section_a(c):
    rows = [r for r in c["rows"] if "rim" in r]
    worst = max(rows, key=lambda r: (r["rim"][0], r["rim"][1]), default=None)
    rim_bad = [(r["f"], r["rim"][:2]) for r in rows if r["rim"][0] > 3 or r["rim"][1] > 3]
    num_bad = [(r["f"], r["num"]) for r in rows if "num" in r and r["num"][1] > 8 and r["num"][0] > .06 * r["num"][1]]
    bar_bad = [(r["f"], r["bargrey"]) for r in rows if r.get("bargrey", 0) > 3 and "rs-graded" not in r["cls"]]
    lab = c["label"]
    ck("A %s: %d frames read, the card's rim and wash are never a neutral grey" % (lab, len(rows)), rows and not rim_bad, rim_bad[:6] or worst)
    ck("A %s: the number is never grey while it counts" % lab, rows and not num_bad, num_bad[:6])
    ck("A %s: no unit bar is ever grey while it counts" % lab, rows and not bar_bad, bar_bad[:6])
    rows = [r for r in rows if r["op"] > .97] or rows
    greens = [r["rim"][2] for r in rows]
    reds = [r["rim"][3] for r in rows]
    if c["good"] * 100 // c["n"] < 70:
        ck("A %s: a fail never takes any green" % lab, max(greens or [0]) <= 3, max(greens or [0]))
    elif c["good"] < c["n"]:
        ck("A %s: starts red, ends green" % lab, reds and reds[0] > .8 * rows[0]["rim"][4] and greens[-1] > .8 * rows[-1]["rim"][4], [reds[:1], greens[-1:]])
    else:
        ck("A %s: starts red, ends out of the green (its effect's colours)" % lab, reds and reds[0] > .8 * rows[0]["rim"][4] and greens[-1] < .2 * rows[-1]["rim"][4], [reds[:1], greens[-1:]])
    ck("A %s: no page errors" % lab, not c["errs"], c["errs"][:3])


def section_b(c):
    lab = c["label"]
    rows = c["rows"]
    plays = c["plays"]
    gap = c["gap"] or 45
    ticks = [p for p in plays if p["id"] == "res.bar.tick"]
    lands = [p for p in plays if p["id"].startswith("res.grade.")]
    bad_pitch, untimed, missing = [], [], []
    prev_pct, prev_t, last_tick = None, None, -1e9
    for r in rows:
        t = r["t"]
        inframe = [p for p in ticks if (prev_t is None or p["t"] > prev_t) and p["t"] <= t + 1e-6]
        try:
            shown = int(str(r["pct"]).rstrip("%"))
        except Exception:
            shown = None
        changed = prev_pct is not None and shown is not None and shown != prev_pct
        for p in inframe:
            if not changed:
                untimed.append((r["f"], p["o"]))
            elif not p["o"] or round(p["o"].get("frac", -1) * 100) != shown:
                bad_pitch.append((r["f"], shown, p["o"]))
            last_tick = p["t"]
        landed_now = "rs-graded" in r["cls"]
        if changed and not inframe and not landed_now and (t - last_tick) >= gap - .5:
            missing.append((r["f"], prev_pct, shown))
        prev_pct, prev_t = shown, t
    ck("B %s: the count ticks (%d ticks)" % (lab, len(ticks)), len(ticks) >= 8, len(ticks))
    ck("B %s: every tick is in a frame where the number changed" % lab, not untimed, untimed[:6])
    ck("B %s: ...pitched by the number it changed to" % lab, not bad_pitch, bad_pitch[:6])
    ck("B %s: no change of the number goes unticked unless the last tick was under %dms ago" % (lab, gap), not missing, missing[:8])
    land_row = next((r for r in rows if "rs-graded" in r["cls"]), None)
    prev = rows[rows.index(land_row) - 1] if land_row and rows.index(land_row) else None
    ok = bool(lands) and land_row and prev and prev["t"] < lands[0]["t"] <= land_row["t"] + 1e-6
    ck("B %s: the landing's sound is in the frame the grade goes on the card" % lab, ok,
       [lands[:1], land_row and land_row["t"], prev and prev["t"]])


def render_sound(pg, ident, opts=None):
    return pg.evaluate("""async ([id, o]) => {
      if(!SOUND_CATALOGUE[id]) return null;
      const r = await NovaSound.render(id, o || {});
      if(!r) return null;
      const ch = r.getChannelData(0), sr = r.sampleRate, win = Math.round(sr * .05);
      const env = []; for(let i = 0; i < ch.length; i += win){ let s = 0; for(let j = i; j < Math.min(ch.length, i + win); j++) s += ch[j] * ch[j]; env.push(Math.sqrt(s / win)); }
      return { len: ch.length / sr, env, peak: Math.max(...env) };
    }""", [ident, opts])


def boot_plain(pw):
    br = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    ctx = br.new_context(viewport={"width": 440, "height": 956})
    ctx.add_init_script(SEED)
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.route("**/index.html", lambda r: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    pg.route("**/version.json*", lambda r: r.fulfill(status=200, headers={"content-type": "application/json"}, body='{"build":"%s","frameId":"","force":false}' % BUILD))
    pg.goto("http://127.0.0.1:%d/index.html" % PORT)
    pg.wait_for_timeout(2600)
    pg.evaluate(SETUP)
    return br, pg, errs


def win(env, a, b):
    i0, i1 = int(a / .05), max(int(a / .05) + 1, int(b / .05))
    seg = env[i0:i1]
    return max(seg) if seg else 0


def section_c(pg):
    has = pg.evaluate("()=>{ const c = (typeof SOUND_CATALOGUE !== 'undefined') && SOUND_CATALOGUE['hundo.ufo']; return c ? String(c.fn) : ''; }")
    r = render_sound(pg, "hundo.ufo")
    ck("C hundo.ufo renders", bool(r), r and r.get("len"))
    if not r:
        return
    env, pk = r["env"], r["peak"]
    ck("C the score names the scan and the steal (a scan sweep over the box, the lock, the grade lifted up the beam)",
       all(k in has for k in ("scan", "lock", "steal")), [k for k in ("scan", "lock", "steal") if k not in has])
    # the landing is at 6.1s, the scan right after it, the grab at 7.38s
    ck("C the scan is heard after the landing (6.25-6.95s)", win(env, 6.25, 6.95) > .12 * pk, [round(win(env, 6.25, 6.95) / pk, 3)])
    ck("C the steal is heard at the grab (7.35-7.75s)", win(env, 7.35, 7.75) > .2 * pk, [round(win(env, 7.35, 7.75) / pk, 3)])
    ck("C the take-off after it (8.5-9.2s)", win(env, 8.5, 9.2) > .2 * pk, [round(win(env, 8.5, 9.2) / pk, 3)])


def section_d(pg):
    tiers = pg.evaluate("()=>Object.keys(SOUND_CATALOGUE).filter(k => /^test\\.streak\\./.test(k)).sort((a, b) => +a.split('.')[2] - +b.split('.')[2])")
    ck("D the streak has a sound for each of the pop's eight looks", len(tiers) >= 8, tiers)
    rs = {t: render_sound(pg, t) for t in tiers}
    ck("D every tier renders with sound in it", all(v and v["peak"] > .01 for v in rs.values()), {k: v and round(v["peak"], 3) for k, v in rs.items()})
    src = pg.evaluate("()=>Object.keys(SOUND_CATALOGUE).filter(k => /^test\\.streak\\./.test(k)).map(k => k + '|' + String(SOUND_CATALOGUE[k].fn)).join('\\n') + (typeof sndStreak === 'function' ? String(sndStreak) : '')")
    ck("D the tiers speak the ambience's language (chime/pad/bass, a resolve to D major on the big ones)",
       "K.chime" in src and ("K.pad" in src or "K.bass" in src) and "F#" in src, None)
    lens = [rs[t]["len"] for t in tiers if rs.get(t)]
    ck("D each tier is longer than the one below (a bigger streak, a bigger sound)", lens == sorted(lens) and len(set(round(x, 2) for x in lens)) == len(lens), [round(x, 2) for x in lens])
    # the streak plays in the same task as its pop, at the right tier
    r = pg.evaluate("""() => { const P = window.playSound, out = [];
      window.playSound = (id, o) => { out.push({ id, pop: !!document.querySelector('.streak-pop'), n: window.__n }); return null; };
      try{ runMode = 'drill'; runLabel = null; isMissedRetake = false; theme.muteBanners = false;
        [10, 25, 50, 100, 350, 400].forEach(n => { document.querySelectorAll('.streak-pop').forEach(e => e.remove());
          window.__n = n; runLiveStreak = n - 1; runStreakLive(true); });
      }catch(e){ window.playSound = P; return 'err ' + e; }
      window.playSound = P; document.querySelectorAll('.streak-pop, .streak-flash').forEach(e => e.remove()); return out; }""")
    st = [p for p in (r if isinstance(r, list) else []) if p["id"].startswith("test.streak.")]
    ck("D the streak's sound is played with its pop", len(st) == 6 and all(p["pop"] for p in st), r)
    want = {10: "1", 25: "2", 50: "3", 100: "5", 350: "8", 400: "8"}
    ck("D each tier plays its own sound (10 the first, 350 and every 50 after the eighth)",
       all(p["id"] == "test.streak." + want[p["n"]] for p in st) and len(st) == 6, [(p["n"], p["id"]) for p in st])


def section_e(pg):
    src = pg.evaluate("()=>{ const c = SOUND_CATALOGUE['res.unlock.banner']; return c ? String(c.fn) : ''; }")
    ck("E the unlock banner has its own sound: a swell and a bell chord", "K.chime" in src and ("K.pad" in src or "K.hush" in src) and src.count("K.chime") + src.count("K.twinkle") >= 3, src[:200])
    r = render_sound(pg, "res.unlock.banner")
    ck("E it renders and rings (more than half a second)", bool(r) and r["len"] > .6 and r["peak"] > .01, r and [r["len"], r["peak"]])
    if r:
        env, pk = r["env"], r["peak"]
        # the chord lands with the card (it rises from .45s over .8s): the swell before, the peak after it
        ck("E it swells up to the card and peaks as it lands (.75-1.3s), not at once", win(env, 0, .3) < .5 * pk and win(env, .75, 1.3) > .8 * pk,
           [round(win(env, 0, .3) / pk, 2), round(win(env, .75, 1.3) / pk, 2)])
    r = pg.evaluate("""async () => { window.__p = []; const P = window.playSound;
      window.playSound = (id, o) => { const c = document.querySelector('.rs-spot'); window.__p.push({ id, card: !!c, up: !!(c && c.classList.contains('is-up')) }); return null; };
      try{ const it = { kind: 'banner', id: (BANNERS[0] || {}).id, name: 'Test', label: 'x' };
        const h = playUnlockSpotlight(it, () => {}); }catch(e){ window.playSound = P; return 'err ' + e; }
      await new Promise(r => setTimeout(r, 600)); window.playSound = P; document.querySelectorAll('.rs-spot').forEach(e => e.remove()); return window.__p; }""")
    ok = isinstance(r, list) and any(p["id"] == "res.unlock.banner" and p["card"] and p["up"] for p in r)
    ck("E it plays as the card starts to come in", ok, r)


def section_f(pg):
    kinds = ["small", "void", "umbra", "horizon", "genesis"]
    # beats each score has to be heard on (seconds), from the scenes' own S.later/S.step
    BEATS = {"small": [3.35], "void": [2.05, 10.25, 20.2], "umbra": [1.5, 9.1, 17.65], "horizon": [1.95, 8.2, 18.75], "genesis": [.9, 8.7, 18.3]}
    for k in kinds:
        r = render_sound(pg, "flare.scene." + k, {"color": "red"} if k == "small" else None)
        ck("F %s: a score of its own that renders" % k, bool(r) and r["peak"] > .01, r and round(r["peak"], 3))
        if not r:
            continue
        env, pk = r["env"], r["peak"]
        hits = [round(win(env, b, b + .5) / pk, 2) for b in BEATS[k]]
        ck("F %s: heard on its beats %s" % (k, BEATS[k]), all(h > .12 for h in hits), hits)
    src = pg.evaluate("()=>{ const c = SOUND_CATALOGUE['home.secret.found']; return c ? String(c.fn) : ''; }")
    ck("F the find in a test speaks the key (no whole-tone glide, no G#/A#)", src and "G#" not in src and "A#" not in src and "K.twinkle" in src, src[:160])
    r = pg.evaluate("""async () => { const P = window.playSound, out = [];
      window.playSound = (id, o) => { if(/^flare\\.scene\\./.test(id)) out.push({ id, scene: !!document.querySelector('.sf-scene') }); return { stop(){ out.push({ id: 'stop' }); } }; };
      let h = null;
      try{ h = playUmbraFlareScene(() => {}); }catch(e){ window.playSound = P; return 'err ' + e; }
      await new Promise(r => setTimeout(r, 200));
      try{ h && h.stop && h.stop(); }catch(e){}
      window.playSound = P; document.querySelectorAll('.sf-scene, .scene-bridge').forEach(e => e.remove()); document.body.classList.remove('bc-covering');
      return out; }""")
    ok = isinstance(r, list) and any(p["id"] == "flare.scene.umbra" and p["scene"] for p in r)
    ck("F a scene plays its score as it opens", ok, r)
    ck("F and a scene stopped stops its score", isinstance(r, list) and any(p["id"] == "stop" for p in r), r)


with sync_playwright() as pw:
    cases = []
    if "A" in ONLY or "B" in ONLY:
        print("\n  A/B. the grade card and its ticks, frame by frame (" + os.path.basename(SRC) + ")")
        CASES = [("9/12 pass (phone)", 9, None, (440, 956)), ("6/12 fail (phone)", 6, None, (440, 956)),
                 ("12/12 Confetti (phone)", 12, None, (440, 956)), ("12/12 Underwater (phone)", 12, "underwater", (440, 956)),
                 ("9/12 pass (iPad)", 9, None, (834, 1194))]
        pick = os.environ.get("B327J_CASES")
        for i, (lab, good, fx, size) in enumerate(CASES):
            if pick and str(i) not in pick.split(","):
                continue
            cases.append(run_case(pw, lab, good, fx=fx, size=size, frames=300 if good == 12 else 260))
    if "A" in ONLY:
        print("\n  A. the card is never grey")
        for c in cases:
            section_a(c)
    if "B" in ONLY:
        print("\n  B. every tick is on a change of the number")
        for c in cases:
            section_b(c)
    if ONLY & {"C", "D", "E", "F"}:
        br, pg, errs = boot_plain(pw)
        if "C" in ONLY:
            print("\n  C. the UFO scans and steals the grade")
            section_c(pg)
        if "D" in ONLY:
            print("\n  D. the answer streak")
            section_d(pg)
        if "E" in ONLY:
            print("\n  E. the unlock pop-up")
            section_e(pg)
        if "F" in ONLY:
            print("\n  F. the secret flare scenes are scored")
            section_f(pg)
        ck("no page errors (C-E)", not errs, errs[:3])
        br.close()
SRV.shutdown()
print("\n" + ("ALL PASS" if not FAILS else "%d FAILED" % len(FAILS)))
sys.exit(1 if FAILS else 0)
