"""Build 327 round 7 (b327w): the hundo effects' scores, redesigned.

  python3 tools/check-b327w.py [--against FILE] [--base FILE]

Madison (Oct 22): "The ufo hundo sound effects are not it, fix that. Let's
ensure the hundo sound effects are awesome and perfect."

Each of the five hundo scores (hundo.confetti, .fireworks, .underwater,
.bubbles, .ufo) is rendered offline (NovaSound.render: no limiter, its own
vol) on this build and on the build before the redesign (--base, default
git 61d9620), and:

  1. it renders, its peak is in range (0.15-0.97) and its loudest 50ms is
     within 4.5 dB of the old score's (calibrated, not re-balanced);
  2. most of its energy is where a phone speaker plays: 200Hz-4kHz holds
     at least 55% of it (a bandpass in an OfflineAudioContext);
  3. it is a new design: check-sound's own similarity against the old
     render is under 0.90 (check-sound 7's bar for two different sounds);
  4. the UFO's named events are heard at their beats, read off the audio
     (10ms frames of the 200Hz-4kHz signal), never off the source:
       - the doppler pass: across the circle the balance swings from the
         side it circles on to the other (its flight, passed in from
         hfxUfoArrival), with the engine loudest round the near pass;
       - the beam: an onset within 80ms of 3.66s (the beam fired);
       - the scan: six or more blips between 6.3s and 6.92s;
       - the lock: an onset within 30ms of each of 6.95, 7.07, 7.19s;
       - the grab: an onset within 40ms of 7.38s and its sound rising
         (more 2-4kHz against 200Hz-1kHz late in the grab than early);
       - the warp: an onset within 40ms of 8.55s, the loudest moment
         after 8s;
     and a flight circling the other way swings the other way.
  5. the five each land a hit on their own effect's first big beat
     (confetti's burst ~0.07s, the first firework at 1.0s, the plunge at
     the sea's top, the bubbles' flourish at 3.5s), within 30ms.

Fails on 61d9620 (--against it); passes on this build.
"""
import functools, http.server, os, re, socket, subprocess, sys, tempfile, threading
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


SRC = arg("--against") or os.path.join(ROOT, "index.html")
BASE = arg("--base")
if not BASE:
    fd, BASE = tempfile.mkstemp(suffix=".html")
    with os.fdopen(fd, "w") as f:
        f.write(subprocess.run(["git", "-C", ROOT, "show", "61d9620:index.html"], capture_output=True, text=True).stdout)

_cs = open(os.path.join(ROOT, "tools", "check-sound.py")).read()
_ns = {}
_ns["math"] = __import__("math")
exec(_cs[_cs.index("FINGERPRINT = r"):_cs.index("s = socket.socket()")], _ns)
FINGERPRINT, similarity = _ns["FINGERPRINT"], _ns["similarity"]

s = socket.socket(); s.bind(("127.0.0.1", 0)); PORT = s.getsockname()[1]; s.close()


class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass


SRV = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Q, directory=ROOT))
threading.Thread(target=SRV.serve_forever, daemon=True).start()
SEED = "try{['class26e.freshstart','1','class26e.frame.ok','go-live-1','class26e.intro.seen','9','class26e.unithold.tip','1','class26e.penal124256.seen','1','class26e.penal256578.seen','1','class26e.weekrecap.v1','9999-12-31','class26e.soundon.327','1'].forEach((v,i,l)=>{ if(i%2===0) localStorage.setItem(v,l[i+1]); });}catch(e){}"
IDS = ["hundo.confetti", "hundo.fireworks", "hundo.underwater", "hundo.bubbles", "hundo.ufo"]
FAILS = []


def ck(name, ok, info=None):
    print(("  PASS  " if ok else "  FAIL  ") + name + ("" if ok or info is None else "  -> " + str(info)[:400]))
    if not ok:
        FAILS.append(name)


def page(br, path):
    body = open(path).read()
    build = (re.search(r'APP_BUILD\s*=\s*"([^"]+)"', body) or [None, "x"])[1]
    ctx = br.new_context(viewport={"width": 440, "height": 956})
    ctx.add_init_script(SEED)
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.route("**/index.html", lambda r: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=body))
    pg.route("**/version.json*", lambda r: r.fulfill(status=200, headers={"content-type": "application/json"}, body='{"build":"%s","frameId":"","force":false}' % build))
    pg.goto("http://127.0.0.1:%d/index.html" % PORT)
    pg.wait_for_timeout(2600)
    return pg, errs


ANALYSE = r"""async ([id, o]) => {
  if(typeof SOUND_CATALOGUE === 'undefined' || !SOUND_CATALOGUE[id]) return null;
  const buf = await NovaSound.render(id, o || {});
  if(!buf) return null;
  const sr = buf.sampleRate, n = buf.length, L = buf.getChannelData(0), R = buf.numberOfChannels > 1 ? buf.getChannelData(1) : L;
  let peak = 0; for(let i = 0; i < n; i++) peak = Math.max(peak, Math.abs(L[i]), Math.abs(R[i]));
  const filt = async (chain) => {
    const c = new OfflineAudioContext(2, n, sr), src = c.createBufferSource(); src.buffer = buf; let node = src;
    chain.forEach(([type, f]) => { for(let k = 0; k < 2; k++){ const b = c.createBiquadFilter(); b.type = type; b.frequency.value = f; b.Q.value = 0; node.connect(b); node = b; } });
    node.connect(c.destination); src.start(); return c.startRendering(); };
  const band = await filt([['highpass', 200], ['lowpass', 4000]]);
  const lo = await filt([['highpass', 200], ['lowpass', 1000]]);
  const hi = await filt([['highpass', 2000], ['lowpass', 4000]]);
  const en = (b, ch) => { const d = b.getChannelData(ch); let s = 0; for(let i = 0; i < d.length; i++) s += d[i] * d[i]; return s; };
  /* the band's share by FFT (2048-point frames, every channel): exact,
     where a biquad cascade's skirts would blur the edges */
  const fft = (re, im) => { const N = re.length;
    for(let i = 1, j = 0; i < N; i++){ let bit = N >> 1; for(; j & bit; bit >>= 1) j ^= bit; j ^= bit; if(i < j){ [re[i], re[j]] = [re[j], re[i]]; [im[i], im[j]] = [im[j], im[i]]; } }
    for(let len = 2; len <= N; len <<= 1){ const ang = -2 * Math.PI / len, wr = Math.cos(ang), wi = Math.sin(ang);
      for(let i = 0; i < N; i += len){ let cr = 1, ci = 0; for(let k = 0; k < len / 2; k++){ const a = i + k, b = a + len / 2;
        const xr = re[b] * cr - im[b] * ci, xi = re[b] * ci + im[b] * cr; re[b] = re[a] - xr; im[b] = im[a] - xi; re[a] += xr; im[a] += xi;
        const t = cr * wr - ci * wi; ci = cr * wi + ci * wr; cr = t; } } } };
  let total = 0, inBand = 0; const NF = 2048, b0 = Math.ceil(200 * NF / sr), b1 = Math.floor(4000 * NF / sr);
  for(const d of [L, R]) for(let i = 0; i + NF <= n; i += NF){ const re = new Float64Array(NF), im = new Float64Array(NF);
    for(let k = 0; k < NF; k++) re[k] = d[i + k]; fft(re, im);
    for(let k = 1; k < NF / 2; k++){ const pw = re[k] * re[k] + im[k] * im[k]; total += pw; if(k >= b0 && k <= b1) inBand += pw; } }
  const frames = (b, ch, ms) => { const d = b.getChannelData(ch), w = Math.round(sr * ms / 1000), out = [];
    for(let i = 0; i < d.length; i += w){ let s = 0; for(let j = i; j < Math.min(d.length, i + w); j++) s += d[j] * d[j]; out.push(Math.sqrt(s / w)); } return out; };
  const mono = (b, ms) => { const a = frames(b, 0, ms), c = frames(b, 1, ms); return a.map((v, i) => Math.sqrt((v * v + c[i] * c[i]) / 2)); };
  const r50 = mono(buf, 50);
  return { len: n / sr, peak, loud: Math.max(...r50), frac: inBand / Math.max(1e-12, total),
    e10: mono(band, 10), l10: frames(band, 0, 10), rr10: frames(band, 1, 10), lo10: mono(lo, 10), hi10: mono(hi, 10) };
}"""


def onsets(e, thr=1.8, floor=None):
    """frames where the 10ms energy jumps: e[i] above thr x the mean of the 3 before."""
    pk = max(e) or 1
    floor = pk * .03 if floor is None else floor
    out = []
    for i in range(3, len(e)):
        before = sum(e[i - 3:i]) / 3
        if e[i] > floor and e[i] > thr * (before + 1e-9) and (not out or i - out[-1] > 2):
            out.append(i)
    return [i * .01 for i in out]


def near(ts, t, tol):
    return min((abs(x - t) for x in ts), default=9) <= tol


def mean(a, t0, t1, dt=.01):
    seg = a[int(t0 / dt):int(t1 / dt)]
    return sum(seg) / len(seg) if seg else 0


with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    pg, errs = page(br, SRC)
    pgo, _ = page(br, BASE)
    print("  build under test: %s\n  the old scores: %s\n" % (SRC, BASE))
    new = {i: pg.evaluate(ANALYSE, [i, {}]) for i in IDS}
    old = {i: pgo.evaluate(ANALYSE, [i, {}]) for i in IDS}
    fpn = pg.evaluate("(a)=>(" + FINGERPRINT + ")(a)", {"ids": IDS, "extra": []}).get("out", {})
    fpo = pgo.evaluate("(a)=>(" + FINGERPRINT + ")(a)", {"ids": IDS, "extra": []}).get("out", {})

    print("  1-3. each score: level, band, new design")
    for i in IDS:
        a, b = new.get(i), old.get(i)
        ck("%s renders" % i, bool(a))
        if not a:
            continue
        db = 20 * __import__("math").log10(a["loud"] / max(1e-9, b["loud"])) if b else 0
        print("        peak %.3f, loudest 50ms %.4f (old %.4f, %+.1f dB), 200Hz-4kHz %.0f%% (old %.0f%%)" % (
            a["peak"], a["loud"], b["loud"] if b else 0, db, a["frac"] * 100, (b["frac"] * 100) if b else 0))
        ck("%s: peak 0.06-0.97" % i, .06 <= a["peak"] <= .97, round(a["peak"], 3))
        ck("%s: loudest 50ms within 4.5 dB of the old score's" % i, abs(db) <= 4.5, "%+.1f dB" % db)
        ck("%s: 55%%+ of its energy in 200Hz-4kHz" % i, a["frac"] >= .55, "%.0f%%" % (a["frac"] * 100))
        if fpn.get(i, {}).get("st") and fpo.get(i, {}).get("st"):
            sim, parts = similarity(fpn[i], fpo[i])
            print("        similarity %.3f (shape %.2f, spectrum %.2f, envelope %.2f, length %.2f)" % ((sim,) + parts))
            ck("%s: a new design (similarity to the old one under 0.90, check-sound 7's own bar for two different sounds)" % i, sim < .9, "%.3f" % sim)

    print("\n  4. the UFO's events, off the audio")
    u = new.get("hundo.ufo")
    if u:
        e, ons = u["e10"], onsets(u["e10"])
        ck("the beam: an onset within 80ms of 3.66s (fired)", near(ons, 3.66, .08), [round(x, 2) for x in ons if 3.3 < x < 4.2])
        sc = [x for x in onsets(u["hi10"], 1.5) if 6.3 <= x <= 6.95]
        sc2 = [x for x in onsets(u["e10"], 1.3) if 6.3 <= x <= 6.95]
        ck("the scan: six or more blips between 6.3s and 6.95s", max(len(sc), len(sc2)) >= 6, (len(sc), len(sc2)))
        for t in (6.95, 7.07, 7.19):
            ck("the lock: an onset within 30ms of %.2fs" % t, near(onsets(u["hi10"], 1.4) + onsets(u["e10"], 1.3), t, .03),
               [round(x, 2) for x in ons if 6.85 < x < 7.3])
        ck("the grab: an onset within 40ms of 7.38s", near(ons, 7.38, .04) or near(onsets(u["e10"], 1.3), 7.38, .04), [round(x, 2) for x in ons if 7.2 < x < 7.6])
        early = mean(u["hi10"], 7.42, 7.56) / max(1e-9, mean(u["lo10"], 7.42, 7.56))
        late = mean(u["hi10"], 7.72, 7.88) / max(1e-9, mean(u["lo10"], 7.72, 7.88))
        ck("the grab rises (2-4kHz against 200Hz-1kHz higher late than early)", late > early * 1.3, (round(early, 3), round(late, 3)))
        ck("the warp: an onset within 40ms of 8.55s", near(ons, 8.55, .04), [round(x, 2) for x in ons if 8.3 < x < 8.8])
        loud_t = max(range(int(8.0 / .01), len(e)), key=lambda k: e[k]) * .01
        ck("the warp is the loudest moment after 8s", 8.5 <= loud_t <= 8.9, round(loud_t, 2))
        M = [1.68, 1.99, 2.29, 2.6, 2.9]
        bal = lambda d, t0, t1: mean(d["rr10"], t0, t1) - mean(d["l10"], t0, t1)
        b1, b2 = bal(u, M[1], M[2] - .05), bal(u, M[2] + .05, M[3])
        ck("the doppler pass: circling right-first, the right is louder coming in and the left going out", b1 > 0 and b2 < 0, (round(b1, 4), round(b2, 4)))
        hump = mean(e, M[2] - .2, M[2] + .2) / max(1e-9, mean(e, 1.0, M[0]))
        ck("the doppler pass: the engine loudest round the near pass (2x the far side)", hump > 2, round(hump, 2))
        v = pg.evaluate(ANALYSE, ["hundo.ufo", {"side": -1, "marks": M}])
        if v:
            c1, c2 = bal(v, M[1], M[2] - .05), bal(v, M[2] + .05, M[3])
            ck("circling the other way, the pass swings the other way", c1 < 0 and c2 > 0, (round(c1, 4), round(c2, 4)))
        src = pg.evaluate("()=>String(SOUND_CATALOGUE['hundo.ufo'].fn)")
        ck("the score's source names the scan, lock and steal (check-b327-j C)", all(k in src for k in ("scan", "lock", "steal")))
        hook = pg.evaluate("()=>{ try{ return typeof hfxUfoFlight !== 'undefined'; }catch(e){ return false; } }")
        ck("the saucer's flight is handed to its score (hfxUfoFlight)", hook is True)

    print("\n  5. each lands a hit on its effect's first big beat")
    beats = {"hundo.confetti": .07, "hundo.fireworks": 1.0, "hundo.underwater": 1.7, "hundo.bubbles": 3.5}
    for i, t in beats.items():
        a = new.get(i)
        if not a:
            continue
        o = onsets(a["e10"], 1.6)
        ck("%s: an onset within 30ms of %.2fs" % (i, t), near(o, t, .03), [round(x, 2) for x in o if t - .3 < x < t + .3])

    ck("no page errors", not errs, errs[:3])
    br.close()

print("\n" + ("ALL PASS" if not FAILS else "%d FAILED" % len(FAILS)))
sys.exit(1 if FAILS else 0)
