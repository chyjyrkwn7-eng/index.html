#!/usr/bin/env python3
"""Build 327, round 6 (b327p): every sound lower, darker, one palette.

  python3 tools/check-b327p.py [--against FILE] [--only A,B,C,D,E] [--measure]

Madison (round 6): "The result screen sound effects like the xp box, the xp
bar the grade box are all just high pitched things. It doesn't sound very dark
themed. It doesn't sound very space themed ... The background music for
cutscenes need to be cool like and sound like the main menu background music
... the rank road map cutscenes I feel like they are random noises and come
out of nowhere. When the road map transitions to the planet system it's so
loud and fast and bad ... The grade percentage, when it changes from red to
green the sound changes for some reason?? ... The correct answer is okay but
it's just super high pitched."

A. THE GRADE TICK IS ONE SOUND. sndGradeTick hands res.bar.tick the same
   options either side of PASS_MARK (no `pass`), and res.bar.tick rendered
   with and without the old `pass` flag is the same buffer, sample for
   sample.
B. LOWER. The spectral centroid (energy-weighted mean frequency of an offline
   render, FFT) of every results-screen sound, test.correct, test.load and the
   rank-up journey/cutscene sounds is under 75% of build 327's (e83f307),
   whose figures are written below (measured with this same code).
C. THE JOURNEY HAS A BED. rank.journey.bed exists on the music bus, renders
   30s with no 0.4s window silent anywhere between its first and last sound,
   and the journey turns it on going to the map, fades it under the hand-off,
   turns it on again after the cutscene and stops it when the journey ends.
D. THE HAND-OFF IS QUIET AND SLOW. rank.flare.zoom's peak is under build
   327's, and it takes longer to reach its loudest 50ms (onset).
E. A START-UP STING. app.start exists, renders, and the sound engine plays it
   on the first touch that wakes the sound on Home or Welcome.

Every section fails on e83f307 and passes on this build.
"""
import functools, http.server, json, os, socket, sys, threading
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default
SRC = arg("--against") or os.path.join(ROOT, "index.html")
ONLY = set((arg("--only") or "A,B,C,D,E").split(","))

B_IDS = ["res.bar.tick", "res.grade.fail", "res.grade.pass", "res.grade.great", "res.grade.perfect",
         "res.xp.line", "res.xp.count", "res.xp.total", "res.xp.fill", "res.xp.pop", "res.xp.overflow", "res.levelup",
         "test.correct", "test.load",
         "rank.road.fill", "rank.unlock.pop", "rank.upnext", "rank.word", "rank.xp.climb", "rank.challenge.tick",
         "rank.attn", "rank.windup", "rank.bang", "rank.flash", "rank.title"]
# build 327 (e83f307), measured with CENTROID below (--measure prints them)
# Measured on e83f307 with --measure (spectral centroid, Hz).
BASE_CEN = {"res.bar.tick": 1231, "res.grade.fail": 237, "res.grade.pass": 1021, "res.grade.great": 672, "res.grade.perfect": 480,
            "res.xp.line": 746, "res.xp.count": 1908, "res.xp.total": 479, "res.xp.fill": 529, "res.xp.pop": 1351,
            "res.xp.overflow": 1854, "res.levelup": 630, "test.correct": 988, "test.load": 1164,
            "rank.road.fill": 356, "rank.unlock.pop": 496, "rank.upnext": 1867, "rank.word": 987, "rank.xp.climb": 430,
            "rank.challenge.tick": 1361, "rank.attn": 239, "rank.windup": 116, "rank.bang": 1289, "rank.flash": 1625, "rank.title": 409}
BASE_ZOOM = {"peak": 0.1301, "onset": 1.00}

CENTROID = r"""
async (ids) => {
  const N = 2048, out = {};
  const win = new Float32Array(N); for(let i = 0; i < N; i++) win[i] = .5 - .5 * Math.cos(2 * Math.PI * i / N);
  const fft = (re, im) => {
    for(let i = 1, j = 0; i < N; i++){ let b = N >> 1; for(; j & b; b >>= 1) j ^= b; j ^= b; if(i < j){ [re[i], re[j]] = [re[j], re[i]]; [im[i], im[j]] = [im[j], im[i]]; } }
    for(let len = 2; len <= N; len <<= 1){ const a = -2 * Math.PI / len, wr = Math.cos(a), wi = Math.sin(a);
      for(let i = 0; i < N; i += len){ let cr = 1, ci = 0;
        for(let k = 0; k < len / 2; k++){ const ur = re[i + k], ui = im[i + k], xr = re[i + k + len / 2], xi = im[i + k + len / 2];
          const vr = xr * cr - xi * ci, vi = xr * ci + xi * cr; re[i + k] = ur + vr; im[i + k] = ui + vi; re[i + k + len / 2] = ur - vr; im[i + k + len / 2] = ui - vi;
          const nr = cr * wr - ci * wi; ci = cr * wi + ci * wr; cr = nr; } } } };
  for(const id of ids){
    if(!SOUND_CATALOGUE[id]){ out[id] = { missing: true }; continue; }
    const buf = await NovaSound.render(id, { sr: 44100 });
    const sr = buf.sampleRate, L = buf.getChannelData(0), R = buf.numberOfChannels > 1 ? buf.getChannelData(1) : L, n = L.length;
    const m = new Float32Array(n); let peak = 0;
    for(let i = 0; i < n; i++){ m[i] = (L[i] + R[i]) / 2; peak = Math.max(peak, Math.abs(L[i]), Math.abs(R[i])); }
    let num = 0, den = 0;
    const re = new Float32Array(N), im = new Float32Array(N);
    for(let s = 0; s + N <= n; s += N / 2){
      for(let i = 0; i < N; i++){ re[i] = m[s + i] * win[i]; im[i] = 0; }
      fft(re, im);
      for(let k = 1; k < N / 2; k++){ const e = re[k] * re[k] + im[k] * im[k]; num += e * k * sr / N; den += e; }
    }
    /* the loudest 50ms and when it is reached */
    const w = Math.round(sr * .05); let ss = 0, best = 0, at = 0;
    for(let i = 0; i < n; i++){ ss += m[i] * m[i]; if(i >= w) ss -= m[i - w] * m[i - w]; if(i >= w - 1 && ss / w > best){ best = ss / w; at = i / sr; } }
    out[id] = { cen: den ? num / den : 0, peak, rms: Math.sqrt(best), onset: at, len: n / sr };
  }
  return out;
}
"""

s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = "http://127.0.0.1:%d/index.html" % port
HTML = open(SRC, encoding="utf-8").read()
ok = True
def ck(name, cond, detail=""):
    global ok
    print(" ", "PASS" if cond else "FAIL", name, ("-> " + str(detail)) if detail != "" else "")
    if not cond: ok = False

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    pg = br.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.route("**/index.html", lambda r: r.fulfill(status=200, content_type="text/html", body=HTML))
    pg.goto(URL)
    pg.wait_for_function("() => typeof NovaSound === 'object' && typeof SOUND_CATALOGUE === 'object'", timeout=60000)
    pg.evaluate("() => document.getElementById('splashscreen')?.remove()")

    if "--measure" in sys.argv:
        r = pg.evaluate(CENTROID, B_IDS + ["rank.flare.zoom"])
        print(json.dumps({k: round(v.get("cen", 0)) for k, v in r.items()}))
        print(json.dumps(r.get("rank.flare.zoom")))
        sys.exit(0)

    if "A" in ONLY:
        print("\nA. the grade tick is one sound either side of the pass mark")
        r = pg.evaluate("""async () => {
          const log = [], keep = window.playSound;
          window.playSound = (id, o) => { log.push([id, Object.keys(o || {}).sort().join(","), o && o.frac]); return null; };
          const P = typeof PASS_MARK === "number" ? PASS_MARK : 70;
          const wait = ms => new Promise(r => setTimeout(r, ms));
          for(const [a, b] of [[P - 2, P - 1], [P - 1, P], [P, P + 1], [P + 1, P + 2]]){ sndGradeTick(a, b); await wait(80); }
          window.playSound = keep;
          const pk = async o => { const b = await NovaSound.render("res.bar.tick", Object.assign({ sr: 22050, seed: 3 }, o)); return b.getChannelData(0); };
          const x = await pk({ frac: P / 100, pass: false }), y = await pk({ frac: P / 100, pass: true });
          let d = 0; for(let i = 0; i < Math.max(x.length, y.length); i++) d = Math.max(d, Math.abs((x[i] || 0) - (y[i] || 0)));
          return { log, diff: d, lens: [x.length, y.length] };
        }""")
        keys = set(e[1] for e in r["log"])
        ck("sndGradeTick plays res.bar.tick four times across the pass mark", len(r["log"]) == 4 and all(e[0] == "res.bar.tick" for e in r["log"]), r["log"])
        ck("...with the same options either side (no `pass` flag)", len(keys) == 1 and "pass" not in list(keys)[0], keys)
        ck("res.bar.tick with and without the old pass flag is the same sound", r["diff"] < 1e-6 and r["lens"][0] == r["lens"][1], r)

    if "B" in ONLY:
        print("\nB. lower: the spectral centroid under 75% of build 327's")
        r = pg.evaluate(CENTROID, B_IDS)
        for i in B_IDS:
            v = r.get(i, {})
            ck("%-20s centroid %5d Hz (327: %d, wants < %d)" % (i, round(v.get("cen", 0)), BASE_CEN[i], BASE_CEN[i] * .75),
               not v.get("missing") and 0 < v.get("cen", 0) < BASE_CEN[i] * .75)

    if "C" in ONLY:
        print("\nC. the rank-up journey has a bed")
        r = pg.evaluate("""async () => {
          const e = SOUND_CATALOGUE["rank.journey.bed"];
          if(!e) return { missing: true };
          const buf = await NovaSound.render("rank.journey.bed", { sr: 22050, dur: 30 });
          const sr = buf.sampleRate, d = buf.getChannelData(0), w = Math.round(sr * .4), rms = [];
          for(let s = 0; s + w <= d.length; s += w){ let ss = 0; for(let i = s; i < s + w; i++) ss += d[i] * d[i]; rms.push(Math.sqrt(ss / w)); }
          const pk = Math.max(...rms), on = rms.findIndex(v => v > pk * .05), off = rms.length - 1 - [...rms].reverse().findIndex(v => v > pk * .05);
          const gaps = rms.slice(on, off + 1).filter(v => v < pk * .05).length;
          const src = f => typeof window[f] === "function" ? String(window[f]) : "";
          return { bus: e.bus, len: buf.length / sr, gaps, on: on * .4, off: off * .4,
            toMap: /rankUpBed\\(scene, true\\)/.test(src("rankUpSceneToMap")),
            hand: /rankUpBed\\(scene, false/.test(src("rankUpHandOut")),
            after: /rankUpCutscene\\(scene, api\\);[\\s\\S]{0,80}rankUpBed\\(scene, true\\)/.test(src("rankUpMapShow")),
            end: /rankUpBed\\(scene, false/.test(src("rankUpSceneEnd")) };
        }""")
        ck("rank.journey.bed exists, on the music bus", not r.get("missing") and r.get("bus") == "music", r)
        ck("it renders 30s with no silent 0.4s window between its first and last sound", not r.get("missing") and r.get("gaps") == 0 and r.get("off", 0) - r.get("on", 0) >= 28, r)
        ck("the journey turns it on for the map, fades it under the hand-off, on again after the cutscene, off at the end",
           all(r.get(k) for k in ("toMap", "hand", "after", "end")), r)

    if "D" in ONLY:
        print("\nD. the hand-off is quiet and slow")
        r = pg.evaluate(CENTROID, ["rank.flare.zoom"])["rank.flare.zoom"]
        ck("rank.flare.zoom's peak under 327's %.3f" % BASE_ZOOM["peak"], r["peak"] < BASE_ZOOM["peak"] * .85, round(r["peak"], 3))
        ck("its loudest 50ms comes later than 327's %.2fs" % BASE_ZOOM["onset"], r["onset"] > BASE_ZOOM["onset"] + .2, round(r["onset"], 2))
        ck("its centroid is low (dark): under 700 Hz", r["cen"] < 700, round(r["cen"]))

    if "E" in ONLY:
        print("\nE. a start-up sting")
        r = pg.evaluate("""async () => {
          if(!SOUND_CATALOGUE["app.start"]) return { missing: true };
          const b = await NovaSound.render("app.start", { sr: 22050 });
          let pk = 0; const d = b.getChannelData(0); for(let i = 0; i < d.length; i++) pk = Math.max(pk, Math.abs(d[i]));
          return { peak: pk, len: b.length / b.sampleRate, wired: /play\\("app\\.start"\\)/.test(document.documentElement.innerHTML) };
        }""")
        ck("app.start exists and renders, audible and not clipping", not r.get("missing") and .04 < r.get("peak", 0) < .97, r)
        ck("the engine plays it on the first touch that wakes the sound on Home or Welcome", r.get("wired") is True, r)

    ck("no page errors", not errs, errs[:3])
    br.close()
print("\nALL PASS" if ok else "\nSOME FAILED")
sys.exit(0 if ok else 1)
