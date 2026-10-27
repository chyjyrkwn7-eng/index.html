#!/usr/bin/env python3
"""Sound and vibration (build 322): off by default, free while off, and every
sound in the catalogue real, clean and its own.

Madison: "This will be a setting in settings that will be off by default ...
I NEED you to ensure all the sounds and sound effects are unique and make
sense."

  1. ON by default since build 327 ("Let's automatically put the sound on
     as default now ... option will still be in settings though to turn it
     off"): a brand-new account is on; an existing account saved with the
     old default (off) is switched on ONCE; turned off afterwards it stays
     off, across a reload, and on a device that never saw the switch-on
     (the account carries soundOn327); a non-boolean is ignored.
     (Re-read in build 327 - this section asserted off-by-default before.)
  2. Free while off: no AudioContext is ever constructed - after boot, taps
     across Home and Settings, and direct calls to playSound/startAmbience.
  3. Settings: the switch (off), the volume shown only while on, Vibration
     only on Android; turning it on makes exactly one running context; the
     switch and the volume persist across a reload.
  4. The engine: per-id cooldown, the global voice cap, suspended while the
     page is hidden and resumed after, the ambience looping and stopping
     when the screen it belongs to is gone (and not coming back with it).
  5. Vibration: with sound off and vibration on, a sound's id still buzzes
     on Android; with vibration off it does not.
  6. Every catalogue id renders offline (no limiter, volume 1) to a buffer
     that is not silent and does not clip, and the catalogue covers every
     event Madison listed.
  7. No two ids are near-identical: a spectro-temporal fingerprint, the
     average spectrum and the loudness envelope, compared pair by pair. The
     metric is proven able to fail first: two renders of one sound with
     different seeds, and a tick against its own tock, must score above
     the threshold.
  8. The Home ambience loops seamlessly: the step across the seam is no
     bigger than an ordinary step inside the loop, and the level either
     side of it matches.
  9. Wired (phase 2): with sound on, the hooks fire - Home's ambience and
     planet, the tab bar, a Settings switch, LOADING TEST, wrong, right,
     the star, pause and resume, next, Nova's blips, last week's fanfare,
     the badge cutscene's entrance and the Badges tab's case opening, and a
     real results screen: the count's ticks, the grade's landing, the XP fill.

  python3 tools/check-sound.py [--against old-index.html]
"""
import functools, http.server, json, math, os, socket, sys, threading
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGAINST = sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else None
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
THRESH = 0.90

# Every event Madison's request names, by the id it plays under.
REQUIRED = """
ui.tap.primary ui.tap.secondary ui.toggle.on ui.toggle.off ui.tab.bottom ui.tab.top
ui.sheet.open ui.sheet.close ui.back ui.popup.open ui.error ui.locked ui.slider.tick ui.field.focus
test.select test.correct test.wrong test.streak.1 test.streak.2 test.streak.3 test.next test.star
test.unstar test.pause test.resume test.tick test.timeup test.save test.load
res.bar.tick res.grade.fail res.grade.pass res.grade.great res.grade.perfect res.xp.fill res.levelup
res.xp.overflow res.unlock.reveal res.found.badge res.found.flare res.found.character
hundo.confetti hundo.fireworks hundo.underwater hundo.bubbles hundo.ufo
react.confetti react.fireworks react.underwater react.bubbles react.ufo
home.planet home.flare.rookie home.flare.ranger home.flare.veteran home.flare.vanguard home.flare.adept
home.flare.elite home.flare.titan home.flare.locked home.secret.found home.daily.ready home.daily.fill
res.xp.line res.xp.count res.xp.total
badge.case.open badge.case.close badge.lift badge.spin badge.rub badge.squeak badge.sparkle badge.drop cs.badge
rank.road.scroll rank.challenge.tick rank.road.fill rank.unlock.pop rank.flare.zoom rank.windup rank.flash
rank.supernova rank.upnext rank.card rank.xp.climb rank.whirl
lb.switch lb.findme lb.winner vr.lobby vr.join vr.leave vr.ready vr.count vr.go vr.progress vr.tug vr.end vr.podium
chat.send chat.receive chat.react chat.invite
ob.step pick.character nova.arrive nova.blip ob.whatsnew ob.tooltip
cust.theme ui.locked bc.rise badge.slide rank.word
""".split()

COUNT_CTX = r"""
(() => {
  window.__acMade = 0; window.__vibes = [];
  const wrap = name => {
    const C = window[name];
    if(!C) return;
    const W = function(...a){ window.__acMade++; return new C(...a); };
    W.prototype = C.prototype;
    try{ Object.defineProperty(window, name, { value: W, configurable: true, writable: true }); }catch(e){ window[name] = W; }
  };
  wrap("AudioContext"); wrap("webkitAudioContext");
  try{ navigator.vibrate = p => { window.__vibes.push(p); return true; }; }catch(e){}
  try{ localStorage.setItem('class26e.freshstart','1'); localStorage.setItem('class26e.frame.ok','go-live-1');
       localStorage.setItem('class26e.intro.seen','9'); localStorage.setItem('class26e.unithold.tip','1');
       localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.penal256578.seen','1'); }catch(e){}
})();
"""

SEED = """()=>{ document.getElementById('splashscreen')?.remove(); try{ __useFake(); }catch(e){}
  store.onboardingComplete=true; store.firstName='Madison'; store.publicId='me01'; store.tourRev=99;
  ['seenFirstResultsTour','seenModeSelectTour','seenProfileTour','seenRewardsTour','seenSettingsTour',
   'seenUnitOptionsTour','seenUnitSelectTour','seenMainMenuTour'].forEach(k=>store[k]=true); }"""

# The fingerprint: a 1024-point FFT every 512 samples, energy in 32 log
# bands from 80Hz to 16kHz; the active part (within 50dB of the loudest
# frame) resampled to 24 steps; the average spectrum; the loudness envelope.
FINGERPRINT = r"""
async ({ ids, extra }) => {
  const N = 1024, H = 512, NB = 32, T = 24, E = 48;
  const win = new Float32Array(N); for(let i = 0; i < N; i++) win[i] = .5 - .5 * Math.cos(2 * Math.PI * i / N);
  const fft = (re, im) => {
    for(let i = 1, j = 0; i < N; i++){ let b = N >> 1; for(; j & b; b >>= 1) j ^= b; j ^= b; if(i < j){ [re[i], re[j]] = [re[j], re[i]]; [im[i], im[j]] = [im[j], im[i]]; } }
    for(let len = 2; len <= N; len <<= 1){
      const a = -2 * Math.PI / len, wr = Math.cos(a), wi = Math.sin(a);
      for(let i = 0; i < N; i += len){ let cr = 1, ci = 0;
        for(let k = 0; k < len / 2; k++){ const ur = re[i + k], ui = im[i + k], xr = re[i + k + len / 2], xi = im[i + k + len / 2];
          const vr = xr * cr - xi * ci, vi = xr * ci + xi * cr; re[i + k] = ur + vr; im[i + k] = ui + vi; re[i + k + len / 2] = ur - vr; im[i + k + len / 2] = ui - vi;
          const nr = cr * wr - ci * wi; ci = cr * wi + ci * wr; cr = nr; } } }
  };
  const one = async (id, opts) => {
    const buf = await NovaSound.render(id, Object.assign({ sr: 44100 }, opts || {}));
    const sr = buf.sampleRate, L = buf.getChannelData(0), R = buf.numberOfChannels > 1 ? buf.getChannelData(1) : L, n = L.length;
    let peak = 0; const m = new Float32Array(n);
    for(let i = 0; i < n; i++){ peak = Math.max(peak, Math.abs(L[i]), Math.abs(R[i])); m[i] = (L[i] + R[i]) / 2; }
    const edges = []; for(let b = 0; b <= NB; b++) edges.push(80 * Math.pow(16000 / 80, b / NB));
    const binOf = f => Math.min(N / 2, Math.round(f * N / sr));
    const frames = [], energy = [];
    const re = new Float32Array(N), im = new Float32Array(N);
    for(let s = 0; s + N <= n || s === 0; s += H){
      for(let i = 0; i < N; i++){ re[i] = (m[s + i] || 0) * win[i]; im[i] = 0; }
      fft(re, im);
      const bands = new Float32Array(NB); let tot = 0;
      for(let b = 0; b < NB; b++){ let e = 0; const lo = binOf(edges[b]), hi = Math.max(lo + 1, binOf(edges[b + 1]));
        for(let k = lo; k < hi; k++) e += re[k] * re[k] + im[k] * im[k]; bands[b] = e; tot += e; }
      frames.push(bands); energy.push(tot);
      if(s + N > n) break;
    }
    const emax = Math.max(...energy, 1e-20);
    let a = 0, z = energy.length - 1;
    while(a < z && energy[a] < emax * 1e-5) a++;
    while(z > a && energy[z] < emax * 1e-5) z--;
    const db = e => Math.max(-60, 10 * Math.log10(e / emax + 1e-12));
    const st = [], spec = new Array(NB).fill(0), env = [];
    for(let t = 0; t < T; t++){ const f = frames[Math.round(a + (z - a) * t / (T - 1))]; for(let b = 0; b < NB; b++) st.push(db(f[b])); }
    let wsum = 0;
    for(let i = a; i <= z; i++){ const w = energy[i]; wsum += w; for(let b = 0; b < NB; b++) spec[b] += frames[i][b]; }
    for(let b = 0; b < NB; b++) spec[b] = db(spec[b] / Math.max(1, z - a + 1));
    for(let t = 0; t < E; t++) env.push(db(energy[Math.round(a + (z - a) * t / (E - 1))]));
    /* the loudest 50ms: a short sound and a long sparse one alike */
    const w = Math.round(sr * .05); let ss = 0, best = 0;
    for(let i = 0; i < n; i++){ ss += m[i] * m[i]; if(i >= w) ss -= m[i - w] * m[i - w]; if(i >= w - 1) best = Math.max(best, ss / w); }
    return { id, peak, rms: Math.sqrt(Math.max(0, best)), dur: (z - a + 1) * H / sr, len: n / sr, st, spec, env };
  };
  const out = {};
  for(const id of ids){ try{ out[id] = await one(id); }catch(e){ out[id] = { id, error: String(e && e.message || e) }; } }
  const ex = {};
  for(const [key, id, opts] of extra){ try{ ex[key] = await one(id, opts); }catch(e){ ex[key] = { error: String(e) }; } }
  return { out, ex };
}
"""

AMB = r"""
async () => {
  const t0 = performance.now(), r = await NovaSound.renderAmbience('amb.home');
  const ms = Math.round(performance.now() - t0);
  const res = { len: r.length / r.sampleRate, ms, sr: r.sampleRate, ch: [] };
  r.channels.forEach(d => {
    const n = d.length, steps = [];
    for(let i = 1; i < n; i++) steps.push(Math.abs(d[i] - d[i - 1]));
    steps.sort((x, y) => x - y);
    const p999 = steps[Math.floor(steps.length * .999)], seam = Math.abs(d[0] - d[n - 1]);
    const w = Math.round(r.sampleRate * .25);
    let a = 0, b = 0; for(let i = 0; i < w; i++){ a += d[n - w + i] ** 2; b += d[i] ** 2; }
    let pk = 0; for(let i = 0; i < n; i++) pk = Math.max(pk, Math.abs(d[i]));
    res.ch.push({ seam, p999, dbEnd: 10 * Math.log10(a / w + 1e-12), dbStart: 10 * Math.log10(b / w + 1e-12), peak: pk });
  });
  return res;
}
"""


def cos(x, y):
    mx, my = sum(x) / len(x), sum(y) / len(y)
    a = [v - mx for v in x]; b = [v - my for v in y]
    na = math.sqrt(sum(v * v for v in a)); nb = math.sqrt(sum(v * v for v in b))
    if na < 1e-9 or nb < 1e-9:
        return 1.0 if na < 1e-9 and nb < 1e-9 else 0.0
    return sum(p * q for p, q in zip(a, b)) / (na * nb)


NB, T = 32, 24
def band_cos(x, y, sh, rows):
    """x against y moved sh bands: a pitch shift of sh bands"""
    xs, ys = [], []
    for r in range(rows):
        for b in range(NB):
            if 0 <= b + sh < NB:
                xs.append(x[r * NB + b]); ys.append(y[r * NB + b + sh])
    return cos(xs, ys)

def similarity(p, q):
    """1 = the same sound. Spectro-temporal shape counts most; a sound twice
    as long as another cannot be its near-copy. Pitch-tolerant: the best of
    the two compared up to two bands (about six semitones) apart, so a copy
    of a sound moved up or down a few notes still counts as a copy."""
    st, sp = max(((band_cos(p["st"], q["st"], sh, T), band_cos(p["spec"], q["spec"], sh, 1)) for sh in (-2, -1, 0, 1, 2)),
                 key=lambda v: v[0] + v[1])
    en = cos(p["env"], q["env"])
    dr = min(p["dur"], q["dur"]) / max(p["dur"], q["dur"], 1e-6)
    return (0.5 * st + 0.25 * sp + 0.25 * en) * math.sqrt(dr), (st, sp, en, dr)


s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
threading.Thread(target=srv.serve_forever, daemon=True).start()
_VR = open(os.path.join(ROOT, "tools", "check-vroom.py"), encoding="utf-8").read()
import re
FAKE = re.search(r'FAKE_FIRESTORE = """(.*?)"""', _VR, re.S).group(1)
URL = "http://127.0.0.1:%d/index.html" % port
ok = True
def ck(n, c, d=""):
    global ok
    print(" ", "PASS" if c else "FAIL", n, ("-> " + str(d)) if d != "" else "")
    if not c: ok = False

def new_page(br, ua=None):
    ctx = br.new_context(viewport={"width": 440, "height": 956}, user_agent=ua) if ua else br.new_context(viewport={"width": 440, "height": 956})
    ctx.add_init_script(FAKE)
    ctx.add_init_script(COUNT_CTX)
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    if AGAINST:
        html = open(AGAINST, encoding="utf-8").read()
        pg.route("**/index.html", lambda r, q=None: r.fulfill(status=200, content_type="text/html", body=html))
    return ctx, pg, errs

def boot(pg):
    pg.goto(URL); pg.wait_for_timeout(2200)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")

def ev(pg, js, default=None):
    try: return pg.evaluate(js)
    except Exception as e:
        return default if default is not None else {"__err": str(e)[:200]}

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])

    print("\n  1. on by default (build 327), off when turned off")
    ctx, pg, errs = new_page(br)
    boot(pg)
    r = ev(pg, "()=>({ on: theme.soundOn, vib: theme.vibrate, vol: theme.soundVolume, fresh: !store.onboardingComplete, api: typeof NovaSound === 'object' && typeof playSound === 'function' && typeof startAmbience === 'function' && typeof stopAmbience === 'function' })")
    ck("the engine and its API exist (NovaSound, playSound, startAmbience, stopAmbience)", r.get("api") is True, r)
    ck("a brand-new account: sound ON, vibration off", r.get("fresh") is True and r.get("on") is True and r.get("vib") is False, r)
    ev(pg, SEED.rstrip("}") + "; store.theme = { mode:'dark', accent:'ink', layout:'modern', swipeAdvance:true, autoAdvance:false, reduceMotion:false, muteBanners:false, autoFlagMissed:false, showClassDaysLeft:true, soundOn:false, soundVolume:.7, vibrate:false }; saveStore(); try{ localStorage.removeItem('class26e.soundon.327'); }catch(e){} }")
    pg.reload(); pg.wait_for_timeout(2200); ev(pg, "()=>document.getElementById('splashscreen')?.remove()")
    r = ev(pg, "()=>({ on: theme.soundOn, vib: theme.vibrate, flag: store.theme && store.theme.soundOn327, dev: localStorage.getItem('class26e.soundon.327'), done: store.onboardingComplete, made: window.__acMade })")
    ck("an existing account saved with the old default (off): switched on once, recorded on the account and the device", r.get("done") is True and r.get("on") is True and r.get("vib") is False and r.get("flag") is True and r.get("dev") == "1", r)
    ck("on, but no AudioContext before the first gesture (iOS)", r.get("made") == 0, r)
    ev(pg, "()=>{ theme.soundOn = false; saveTheme(); }")
    pg.reload(); pg.wait_for_timeout(2200); ev(pg, "()=>document.getElementById('splashscreen')?.remove()")
    r = ev(pg, "()=>({ on: theme.soundOn, saved: store.theme.soundOn })")
    ck("turned off afterwards, it stays off across a reload", r.get("on") is False and r.get("saved") is False, r)
    ev(pg, "()=>{ try{ localStorage.removeItem('class26e.soundon.327'); }catch(e){} }")
    pg.reload(); pg.wait_for_timeout(2200); ev(pg, "()=>document.getElementById('splashscreen')?.remove()")
    r = ev(pg, "()=>({ on: theme.soundOn })")
    ck("...and on a device that never saw the switch-on (the account remembers it)", r.get("on") is False, r)
    r = ev(pg, "()=>{ store.theme.soundOn = 'yes'; store.theme.vibrate = 1; theme.soundOn = false; theme.vibrate = false; loadTheme(); return { on: theme.soundOn, vib: theme.vibrate }; }")
    ck("a saved value that is not a boolean is ignored", r.get("on") is False and r.get("vib") is False, r)
    ev(pg, "()=>{ theme.soundOn = false; saveTheme(); }")

    print("\n  2. free while off")
    ev(pg, "()=>{ showHome(); }"); pg.wait_for_timeout(500)
    for sel in [".cosmic-hero-wrap", "#bottomtab-profile", "#bottomtab-appearance", ".settings-card label.opt", "#bottomtab-home"]:
        try:
            el = pg.query_selector(sel)
            if el: el.click(timeout=1500, force=True); pg.wait_for_timeout(250)
        except Exception: pass
    r = ev(pg, """()=>{ try{ playSound('test.correct'); playSound('home.planet'); startAmbience('amb.home', { owner: document.body }); NovaSound.wake && NovaSound.wake(); }catch(e){}
      return { made: window.__acMade, st: (typeof NovaSound === 'object') ? NovaSound.state() : null }; }""")
    ck("no AudioContext constructed after boot, taps and direct calls", r.get("made") == 0 and r.get("st") and r["st"]["hasContext"] is False, r)
    ev(pg, "()=>stopAmbience()")

    print("\n  3. Settings")
    ev(pg, "()=>{ store.seenSettingsTour = true; showAppearance(); }"); pg.wait_for_timeout(400)
    r = ev(pg, """()=>{ const g = document.getElementById('settings-sound'), row = document.querySelector('.settings-sound-row');
      const cb = row && row.querySelector('input'), vol = document.querySelector('.settings-volume');
      const title = row && row.querySelector('.otext') ? row.querySelector('.otext').firstChild.textContent : null;
      const order = [...document.querySelectorAll('.slab.motion-summary')].map(x => x.id);
      return { group: g ? g.textContent : null, title, checked: cb ? cb.checked : null, volHidden: vol ? vol.hidden : null,
               vib: !!document.querySelector('.settings-vibrate-row'), order }; }""")
    ck("a 'Sound & vibration' group with a 'Sound effects' switch, off", r.get("group") == "Sound & vibration" and r.get("title") == "Sound effects" and r.get("checked") is False, r)
    ck("the group sits after Display & motion, before Studying & tests", (r.get("order") or [])[:3] == ["settings-motion", "settings-sound", "settings-study"], r.get("order"))
    ck("the volume is hidden while sound is off", r.get("volHidden") is True, r)
    ck("no Vibration switch where vibration cannot work (not Android)", r.get("vib") is False, r)
    try: pg.click(".settings-sound-row .otext", timeout=4000, no_wait_after=True)
    except Exception as e: print("    click failed:", str(e)[:120])
    pg.wait_for_timeout(500)
    r = ev(pg, "()=>({ on: theme.soundOn, made: window.__acMade, st: NovaSound.state(), volHidden: document.querySelector('.settings-volume').hidden, saved: store.theme && store.theme.soundOn })")
    ck("turning it on makes exactly one context, running", r.get("on") is True and r.get("made") == 1 and (r.get("st") or {}).get("ctxState") == "running", r)
    ck("the volume appears once it is on, and it is saved", r.get("volHidden") is False and r.get("saved") is True, r)
    r = ev(pg, """()=>{ const s = document.querySelector('.settings-volume input[type=range]'); s.value = '35';
      s.dispatchEvent(new Event('input', { bubbles: true })); s.dispatchEvent(new Event('change', { bubbles: true }));
      return { vol: theme.soundVolume, saved: store.theme.soundVolume, master: NovaSound.state().master, label: document.querySelector('.settings-volume .sliderval').textContent }; }""")
    ck("the volume slider sets the volume and saves it", abs((r.get("vol") or 0) - .35) < 1e-6 and abs((r.get("saved") or 0) - .35) < 1e-6 and r.get("label") == "35%", r)
    pg.reload(); pg.wait_for_timeout(2200); ev(pg, "()=>document.getElementById('splashscreen')?.remove()")
    ev(pg, "()=>{ store.seenSettingsTour = true; showAppearance(); }"); pg.wait_for_timeout(300)
    r = ev(pg, """()=>({ on: theme.soundOn, vol: theme.soundVolume, made: window.__acMade, checked: document.querySelector('.settings-sound-row input').checked,
      volHidden: document.querySelector('.settings-volume').hidden, slider: document.querySelector('.settings-volume input').value })""")
    ck("after a reload: still on, volume 35, the switch checked and the slider showing it", r.get("on") is True and abs((r.get("vol") or 0) - .35) < 1e-6 and r.get("checked") is True and r.get("volHidden") is False and r.get("slider") == "35", r)
    ck("after a reload: no context until the first gesture", r.get("made") == 0, r)
    try: pg.mouse.click(220, 300)
    except Exception: pass
    pg.wait_for_timeout(400)
    r = ev(pg, "()=>({ made: window.__acMade, st: NovaSound.state() })")
    ck("the first tap after a reload wakes it", r.get("made") == 1 and (r.get("st") or {}).get("ctxState") == "running", r)

    print("\n  4. the engine")
    r = ev(pg, """()=>{ const a = playSound('test.correct'), b = playSound('test.correct');
      let most = 0; const ids = Object.keys(SOUND_CATALOGUE).filter(i => SOUND_CATALOGUE[i].bus === 'ui');
      for(let k = 0; k < 120; k++){ playSound(ids[k % ids.length], { seed: k }); most = Math.max(most, NovaSound.state().voices); }
      return { first: !!a, second: !!b, most, cap: SOUND_MAX_VOICES }; }""")
    ck("a cooldown: the same sound twice at once plays once", r.get("first") is True and r.get("second") is False, r)
    ck("120 sounds at once never exceed the voice cap", 0 < (r.get("most") or 0) <= (r.get("cap") or 0), r)
    r = ev(pg, """async ()=>{ showHome(); await new Promise(z => setTimeout(z, 300));
      const owner = document.querySelector('#stage > *'); startAmbience('amb.home', { owner });
      const t0 = performance.now();
      for(let i = 0; i < 150 && !NovaSound.state().amb; i++) await new Promise(z => setTimeout(z, 100));
      const started = NovaSound.state().amb, ms = Math.round(performance.now() - t0);
      Object.defineProperty(document, 'hidden', { configurable: true, get: () => true });
      Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => 'hidden' });
      document.dispatchEvent(new Event('visibilitychange'));
      await new Promise(z => setTimeout(z, 300));
      const hiddenState = NovaSound.state().ctxState, playHidden = !!playSound('test.correct');
      showAppearance();
      Object.defineProperty(document, 'hidden', { configurable: true, get: () => false });
      Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => 'visible' });
      document.dispatchEvent(new Event('visibilitychange'));
      await new Promise(z => setTimeout(z, 500));
      const back = NovaSound.state();
      return { started, ms, hiddenState, playHidden, backState: back.ctxState, ambAfter: back.amb, wantAfter: back.ambWant }; }""")
    ck("the ambience starts and loops", (r.get("started") or {}).get("loop") is True, r)
    ck("hidden: the context is suspended and nothing plays", r.get("hiddenState") == "suspended" and r.get("playHidden") is False, r)
    ck("back: the context resumes, but not the ambience - its screen has gone", r.get("backState") == "running" and r.get("ambAfter") is None and r.get("wantAfter") is None, r)
    r = ev(pg, """async ()=>{ showHome(); await new Promise(z => setTimeout(z, 300));
      startAmbience('amb.home', { owner: document.querySelector('#stage > *') });
      for(let i = 0; i < 40 && !NovaSound.state().amb; i++) await new Promise(z => setTimeout(z, 150));
      const a = !!NovaSound.state().amb; showAppearance();
      await new Promise(z => setTimeout(z, 1800)); return { a, after: NovaSound.state().amb }; }""")
    ck("leaving the ambience's screen stops it on its own", r.get("a") is True and r.get("after") is None, r)
    r = ev(pg, """()=>{ theme.soundOn = false; saveTheme(); NovaSound.sync(); const s = NovaSound.state();
      return { st: s.ctxState, voices: s.voices, play: !!playSound('test.correct') }; }""")
    ck("turned off: everything stops and nothing plays", r.get("st") == "suspended" and r.get("voices") == 0 and r.get("play") is False, r)
    ck("no page errors", not errs, errs[:3])
    ctx.close()

    print("\n  5. vibration (Android)")
    ctx, pg, errs = new_page(br, ua="Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Mobile Safari/537.36")
    boot(pg)
    ev(pg, SEED.rstrip("}") + "; theme.soundOn = false; saveTheme(); store.seenSettingsTour = true; showAppearance(); }"); pg.wait_for_timeout(400)
    r = ev(pg, "()=>{ const v = document.querySelector('.settings-vibrate-row'); return { row: !!v, checked: v ? v.querySelector('input').checked : null, vibOn: theme.vibrate }; }")
    ck("Android: a Vibration switch, off", r.get("row") is True and r.get("checked") is False and r.get("vibOn") is False, r)
    r = ev(pg, "()=>{ window.__vibes = []; playSound('test.correct'); return window.__vibes.length; }", default=-1)
    ck("vibration off: a sound's id does not buzz", r == 0, r)
    try: pg.click(".settings-vibrate-row .otext", timeout=4000, no_wait_after=True)
    except Exception as e: print("    click failed:", str(e)[:120])
    pg.wait_for_timeout(300)
    r = ev(pg, "()=>{ window.__vibes = []; playSound('test.wrong'); playSound('res.grade.perfect'); return { n: window.__vibes.length, v: window.__vibes, made: window.__acMade, saved: store.theme.vibrate }; }")
    ck("vibration on, sound off: ids buzz with their own patterns, and still no context", r.get("n") == 2 and r.get("made") == 0 and r.get("saved") is True and r["v"][0] != r["v"][1], r)
    ctx.close()

    print("\n  6. every sound renders, not silent, not clipping")
    ctx, pg, errs = new_page(br)
    boot(pg)
    ids = ev(pg, "()=>Object.keys(SOUND_CATALOGUE)", default=[])
    if not isinstance(ids, list): ids = []
    missing = [i for i in REQUIRED if i not in ids]
    ck("the catalogue covers every event asked for (%d required, %d in it)" % (len(set(REQUIRED)), len(ids)), ids and not missing, missing[:20])
    descs = ev(pg, "()=>Object.keys(SOUND_CATALOGUE).filter(k => { const e = SOUND_CATALOGUE[k]; return !(e.desc && e.desc.length > 20 && typeof e.fn === 'function' && ['ui','music','cut'].includes(e.bus) && typeof e.cd === 'number'); })", default=["?"])
    ck("every entry has a design, a bus, a cooldown and a description", descs == [], descs)
    extra = [["seedA", "test.correct", {"seed": 1}], ["seedB", "test.correct", {"seed": 9}],
             ["tick", "test.tick", {"left": 10}], ["tock", "test.tick", {"left": 9}],
             ["ufoA", "hundo.ufo", {"seed": 1}], ["ufoB", "hundo.ufo", {"seed": 5}]]
    try:
        data = pg.evaluate("(a)=>(" + FINGERPRINT + ")(a)", {"ids": ids, "extra": extra})
    except Exception as e:
        data = {"out": {}, "ex": {}}; print("    render failed:", str(e)[:200])
    out, ex = data.get("out", {}), data.get("ex", {})
    bad = [(i, out[i].get("error")) for i in ids if "error" in out.get(i, {"error": "missing"})]
    ck("every id renders offline", ids and not bad, bad[:5])
    silent = [(i, round(v["peak"], 4), round(v["rms"], 5)) for i, v in out.items() if "peak" in v and (v["peak"] < .04 or v["rms"] < .01)]
    clip = [(i, round(v["peak"], 3)) for i, v in out.items() if "peak" in v and v["peak"] > .97]
    ck("none is silent (peak >= 0.04, loudest 50ms RMS >= 0.01)", out and not silent, silent)
    ck("none clips (peak <= 0.97 with no limiter at full volume)", out and not clip, clip)
    if out:
        pk = sorted(((v["peak"], i) for i, v in out.items() if "peak" in v))
        print("    peaks: quietest %s %.3f, loudest %s %.3f" % (pk[0][1], pk[0][0], pk[-1][1], pk[-1][0]))

    print("\n  7. no two sounds near-identical (threshold %.2f)" % THRESH)
    good = {i: v for i, v in out.items() if "st" in v}
    if ex.get("seedA") and "st" in ex["seedA"]:
        s1 = similarity(ex["seedA"], ex["seedB"])[0]; s2 = similarity(ex["tick"], ex["tock"])[0]; s3 = similarity(ex["ufoA"], ex["ufoB"])[0]
        ck("the metric can fail: one sound against itself with another seed scores above it", s1 > THRESH, "%.3f" % s1)
        print("    (the UFO against itself with another seed: %.3f - its sparkles land at random)" % s3)
        ck("the metric can fail: the timer's tick against its tock (one sound, two pitches) scores above it", s2 > THRESH, "%.3f" % s2)
    else:
        ck("the metric's self-test rendered", False, ex)
    pairs = []
    keys = sorted(good)
    for a_ in range(len(keys)):
        for b_ in range(a_ + 1, len(keys)):
            sim, parts = similarity(good[keys[a_]], good[keys[b_]])
            pairs.append((sim, keys[a_], keys[b_], parts))
    pairs.sort(reverse=True)
    over = [p for p in pairs if p[0] > THRESH]
    ck("%d pairs compared, none above %.2f" % (len(pairs), THRESH), pairs and not over, [(round(p[0], 3), p[1], p[2]) for p in over[:10]])
    if pairs:
        print("    closest pairs:")
        for p in pairs[:8]:
            print("      %.3f  %-22s %-22s (shape %.2f, spectrum %.2f, envelope %.2f, length ratio %.2f)" % ((p[0], p[1], p[2]) + p[3]))
        sims = sorted(p[0] for p in pairs)
        print("    median pair %.3f, 90th percentile %.3f, 99th %.3f" % (sims[len(sims) // 2], sims[int(len(sims) * .9)], sims[int(len(sims) * .99)]))

    print("\n  8. the Home ambience loops seamlessly")
    try:
        r = pg.evaluate("()=>(" + AMB + ")()")
    except Exception as e:
        r = {"__err": str(e)[:200]}
    chs = r.get("ch") or []
    ck("it renders a loop of 10s or more", (r.get("len") or 0) >= 10, r.get("len"))
    print("    rendered %ss at %s Hz in %s ms" % (r.get("len"), r.get("sr"), r.get("ms")))
    ck("the step across the seam is no bigger than an ordinary step inside the loop (99.9th percentile)",
       chs and all(c["seam"] <= c["p999"] for c in chs), [(round(c["seam"], 5), round(c["p999"], 5)) for c in chs])
    ck("the level either side of the seam matches within 1.5 dB",
       chs and all(abs(c["dbEnd"] - c["dbStart"]) <= 1.5 for c in chs), [(round(c["dbEnd"], 2), round(c["dbStart"], 2)) for c in chs])
    ck("it is low: peak under 0.5", chs and all(0.02 < c["peak"] < .5 for c in chs), [round(c["peak"], 3) for c in chs])
    ck("no page errors", not errs, errs[:3])
    ctx.close()

    print("\n  9. wired into the app (phase 2): the hooks fire, with sound on")
    ctx, pg, errs = new_page(br)
    boot(pg)
    ev(pg, SEED.rstrip("}") + "; theme.soundOn = true; saveTheme(); showHome(); }")
    pg.wait_for_timeout(400)
    try: pg.mouse.click(4, 4)
    except Exception: pass
    pg.wait_for_timeout(300)
    ev(pg, """()=>{ window.__played = []; const P = NovaSound.play;
      NovaSound.play = (id, o) => { window.__played.push(id); return P(id, o); }; return true; }""")
    def played(): return ev(pg, "()=>window.__played.splice(0)", default=[]) or []
    r = ev(pg, "()=>NovaSound.state()")
    ck("Home: the main menu's ambience is asked for", isinstance(r, dict) and r.get("ambWant") == "amb.home", r)
    xy = ev(pg, """()=>{ const c = [...document.querySelectorAll('.screen-home-actual circle')].find(x => x.style.cursor === 'pointer');
      if(!c) return null; const b = c.getBoundingClientRect(); return [b.left + b.width / 2, b.top + b.height / 2]; }""")
    if isinstance(xy, list): pg.mouse.click(xy[0], xy[1]); pg.wait_for_timeout(250)
    got = played()
    ck("Home: tapping the planet plays the planet", "home.planet" in got, got)
    # build 323: Settings is Profile's third tab, not a bar tab
    try: pg.click("#bottomtab-profile", timeout=3000, no_wait_after=True)
    except Exception: pass
    pg.wait_for_timeout(500)
    got = played()
    ck("the bottom tab bar slides", "ui.tab.bottom" in got, got)
    try: pg.click(".profile-settings-tab-btn", timeout=3000, no_wait_after=True)
    except Exception: pass
    pg.wait_for_timeout(500)
    played()
    try: pg.click("text=Reduce motion", timeout=3000, no_wait_after=True)
    except Exception: pass
    pg.wait_for_timeout(300)
    got = played()
    ck("a Settings switch toggles", "ui.toggle.on" in got or "ui.toggle.off" in got, got)
    ev(pg, "()=>{ theme.reduceMotion = false; applyTheme(); saveTheme(); }")
    r = ev(pg, """async ()=>{ const wait = ms => new Promise(z => setTimeout(z, ms));
      const U = QUESTIONS[0].topic; const ix = QUESTIONS.map((q, i) => i).filter(i => QUESTIONS[i].topic === U).slice(0, 4);
      cfg.mode = 'drill'; cfg.units = [U]; cfg.source = 'all'; runMode = 'drill'; beginRun(ix, null);
      for(let i = 0; i < 60 && !document.querySelector('.qpanel .choice'); i++) await wait(100);
      const out = {};
      const take = k => { out[k] = window.__played.splice(0); };
      take('load');
      let qi = order[pos], right = correctSlot(qi), wrong = right === 0 ? 1 : 0;
      choose(wrong); await wait(250); take('wrong');
      choose(right); await wait(250); take('right');
      document.querySelector('.qpanel .flagbtn')?.click(); await wait(100); take('star');
      pauseRun(); await wait(200); take('pause');
      resumeRun(); await wait(200); take('resume');
      advanceWithSlide(); await wait(500); take('next');
      const d = document.createElement('div'); document.body.appendChild(d);
      novaType(d, 'Hello there, class twenty six.', 120); await wait(400); d.remove(); take('nova');
      return out; }""", default={})
    r = r if isinstance(r, dict) else {}
    ck("LOADING TEST powers up", "test.load" in (r.get("load") or []), r.get("load"))
    ck("a wrong answer sounds wrong", "test.wrong" in (r.get("wrong") or []), r.get("wrong"))
    ck("a right answer sounds right", any(x in (r.get("right") or []) for x in ("test.correct", "test.streak.1")), r.get("right"))
    ck("starring a question", "test.star" in (r.get("star") or []), r.get("star"))
    ck("pause and resume", "test.pause" in (r.get("pause") or []) and "test.resume" in (r.get("resume") or []), [r.get("pause"), r.get("resume")])
    ck("on to the next question", "test.next" in (r.get("next") or []), r.get("next"))
    ck("Nova talks in blips", (r.get("nova") or []).count("nova.blip") >= 2, r.get("nova"))
    r = ev(pg, """async ()=>{ showHome(); await new Promise(z => setTimeout(z, 300)); window.__played.splice(0);
      /* build 324: last week's winners are presented by Nova on Home (his
         weekly recap), not on a Leaderboard card - the fanfare comes as he
         names first place */
      let el = null;
      try{ el = playWeekRecap({ week: lastWeekKey(), optedOut: false, story: { kind: 'plain' }, mentions: [], sheriffNew: false,
        top: [{ name: 'Ann', pub: 'a', avatar: 'ninja', pts: 900 }, { name: 'Bo', pub: 'b', avatar: 'ninja', pts: 800 }],
        viewer: { pts: 0, place: 0, inTop: -1, mention: false } }); }catch(e){ return 'err ' + e.message; }
      await new Promise(z => setTimeout(z, 900));
      for(let k = 0; k < 8 && el && el.__nova && el.__nova.index < 2; k++){
        if(el.__nova.typing) el.__nova.advance();
        el.__nova.advance(); await new Promise(z => setTimeout(z, 250)); }
      await new Promise(z => setTimeout(z, 200)); const got = window.__played.splice(0);
      try{ el.__nova.close('skip'); }catch(e){}
      await new Promise(z => setTimeout(z, 400)); return got; }""", default=[])
    ck("last week's winner gets the fanfare from Nova, not the plain sheet sound", isinstance(r, list) and "lb.winner" in r and "ui.sheet.open" not in r, r)
    r = ev(pg, """async ()=>{ const wait = ms => new Promise(z => setTimeout(z, ms));
      document.querySelectorAll('.invite-overlay').forEach(o => o.remove());
      theme.muteBanners = false; window.__played.splice(0);
      const u = QUESTIONS[0].topic, h = playBadgeCaseScene([u], () => {});
      await wait(1200); const scene = window.__played.splice(0);
      try{ h && h.stop(); }catch(e){}
      showHome(); await wait(300); window.__played.splice(0);
      showRanksScreen('badges');
      for(let i = 0; i < 40 && !window.__played.includes('badge.case.open'); i++) await wait(100);
      return { scene, tab: window.__played.splice(0) }; }""", default={})
    r = r if isinstance(r, dict) else {}
    ck("BADGE FOUND: the badge's entrance is scored", "cs.badge" in (r.get("scene") or []), r.get("scene"))
    # MOVED IN 327 (round 10): the Badges tab is a tray ("tray only") - it has
    # no lid to open, so it makes no opening sound
    ck("the Badges tab's tray is quiet (no lid to open)", "badge.case.open" not in (r.get("tab") or []), r.get("tab"))
    r = ev(pg, """async ()=>{ const wait = ms => new Promise(z => setTimeout(z, ms));
      showHome(); await wait(300); window.__played.splice(0);
      const unit = QUESTIONS[0].topic.trim();
      cfg.mode = 'drill'; cfg.source = 'all'; cfg.units = [unit]; cfg.size = 0;
      order = QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === unit);
      runTrackable = true; timedOut = false; runMode = 'drill'; runLabel = null; isMissedRetake = false;
      practiceTestMinutes = null; inVirtualRoom = false; attempts = {}; picked = {}; timedOutSet = {};
      order.forEach((qi, k) => { const oo = optionOrder(qi), right = oo.indexOf(QUESTIONS[qi].answer); attempts[qi] = k < 2 ? 2 : 1; picked[qi] = right; });
      runStartTime = Date.now() - 42000; testInProgress = true; pos = order.length - 1;
      summarize();
      const got = [];
      /* 22s: b327j made the XP bar 1.4x slower on request (a budget, not a decision) */
      for(let i = 0; i < 220; i++){ await wait(100); got.push(...window.__played.splice(0));
        if(got.some(x => x === 'res.xp.pop' || x === 'res.xp.knock')) break; }
      return got; }""", default=[])
    r = r if isinstance(r, list) else []
    ck("results: the grade counts in with ticks", r.count("res.bar.tick") >= 3, r[:6])
    ck("results: the grade lands by its verdict", any(x.startswith("res.grade.") for x in r), [x for x in r if x.startswith("res.grade")])
    ck("results: the XP bar fills, then pops or knocks", "res.xp.fill" in r and any(x in r for x in ("res.xp.pop", "res.xp.knock")), [x for x in r if x.startswith("res.xp")])
    ck("no page errors", not errs, errs[:3])
    ctx.close()
    br.close()
srv.shutdown()
print("\n" + ("ALL PASS" if ok else "FAILED"))
sys.exit(0 if ok else 1)
