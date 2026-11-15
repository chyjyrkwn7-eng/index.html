"""Shared harness for the 384.55 rank-up journey gate and its recorders: a served copy of index.html (any file), a seeded
existing account just short of a rank, the page's stepped clock (tools/record-sound.py's CLOCK) and the journey's driver."""
import functools, glob, http.server, json, os, re, socket, threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
if not os.path.exists(CHROME):
    CHROME = (sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")) or [CHROME])[-1]
_rs = open(os.path.join(ROOT, "tools", "record-sound.py"), encoding="utf-8").read()
CLOCK = re.search(r'CLOCK = r"""(.*?)"""', _rs, re.S).group(1)
STUB = re.search(r'FIRESTORE_STUB = """(.*?)"""', _rs, re.S).group(1)
KEYS = ["rookie", "ranger", "veteran", "vanguard", "adept", "elite", "titan"]

ALL_CHARS = ["detective", "masked", "zeus", "poseidon", "clown", "valkyrie", "marksman", "astronaut", "hacker", "timekeeper", "ronin", "hive",
             "voidwalker", "umbra", "singularity", "genesis", "lunar", "solar", "tempest", "frost", "oracle", "inferno", "astral", "celestial", "zenith"]
ALL_BANNERS = ["tests100", "tests250", "tests500", "hundos100", "hundos250", "vr50", "study50", "study60", "correct5000", "correct10000", "level80",
               "early10", "exam100", "adept_rank", "elite_rank", "titan_rank", "flare_void", "flare_umbra", "flare_horizon", "flare_genesis",
               "astral", "celestial", "zenith"]
SEED = {"onboardingComplete": True, "firstName": "Alex", "avatarChar": "ninja", "publicId": "xph5b57jbp5a", "novaMet": 99,
        "tourRev": 99, "rankMapFx244": True, "seenProfileTour": True, "seenModeSelectTour": True, "seenUnitSelectTour": True,
        "seenMainMenuTour": True, "seenClassTip": True, "seenRankingsTour": True, "seenAppearanceTour": True, "novaHeard": {"@recap": 99991231},
        "seenFirstResultsTour": True, "seenRewardsTour": True, "seenSettingsTour": True, "seenUnitOptionsTour": True, "seenRanksTour": True,
        "seenBadgesTour": True,
        "lifetime": {"points": 41000, "answered": 2100, "correct": 1980, "drillPlays": 60, "examPlays": 12, "perfectTests": 64,
                     "longestStreak": 44, "currentStreak": 12},
        "unitPerfects": {},
        "unlocksShown": {"chars": ALL_CHARS, "banners": ALL_BANNERS, "fx": ["fireworks", "underwater", "bubbles", "ufo"]},
        "flareHintsShown": ["umbra", "singularity", "genesis"]}
SEEN = ["freshstart", "unithold.tip", "savecode.asked", "savecode.card", "getstarted", "penal55124.seen", "penal124256.seen", "penal256578.seen",
        "soundon.327"]
TOPIC = {"academy": "Identity Crimes", "ifc": "Appendix H: Hazardous Materials Management Plan (HMMP) and Hazardous Materials Inventory Statement (HMIS) Instructions"}


class Served:
    """index.html (or any copy of it) served from an http server on a free port, the Firestore stub in"""
    def __init__(self, src=None):
        self.src = src or os.path.join(ROOT, "index.html")
        raw = open(self.src, encoding="utf-8").read()
        self.body = raw.replace("let fbDb = null;", "let fbDb = null;" + STUB, 1)
        self.build = (re.search(r'APP_BUILD\s*=\s*"([^"]+)"', self.body) or [None, "x"])[1]
        s = socket.socket(); s.bind(("127.0.0.1", 0)); self.port = s.getsockname()[1]; s.close()

        class Q(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *a): pass
        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", self.port), functools.partial(Q, directory=ROOT))
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()


def init_js(cls, seed=None):
    seed = seed or SEED
    s = ("(()=>{ try{ if(sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1');"
         "localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.intro.seen','9');"
         "localStorage.setItem('class26e.weekrecap.v1','9999-12-31');")
    for k in SEEN:
        s += "localStorage.setItem('class26e.%s','1');" % k
    s += "localStorage.setItem('class26e.drill.v1', %s);" % json.dumps(json.dumps(seed))
    if cls == "ifc":
        s += ("localStorage.setItem('class26e.activeclass','ifc'); localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc']));"
              "localStorage.setItem('class26e.greet.ifc','done'); localStorage.setItem('class26e.ifc.weekrecap.v1','9999-12-31');"
              "localStorage.setItem('class26e.ifc.intro.seen','9');")
        for k in SEEN:
            s += "localStorage.setItem('class26e.ifc.%s','1');" % k
        s += "localStorage.setItem('class26e.ifc.drill.v1', %s);" % json.dumps(json.dumps(seed))
    return s + " }catch(e){} })()"


def open_page(br, served, cls="academy", w=440, h=956, dpr=1, clock=False):
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=dpr, has_touch=True)
    ctx.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});")
    ctx.add_init_script(init_js(cls))
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:300]))
    pg.route("**/index.html", lambda r: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=served.body))
    pg.route("**/version.json*", lambda r: r.fulfill(status=200, headers={"content-type": "application/json"},
                                                     body='{"build":"%s","frameId":"","force":false}' % served.build))
    pg.goto("http://127.0.0.1:%d/index.html" % served.port)
    pg.wait_for_timeout(3200)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); try{ __stub(); }catch(e){} theme.reduceMotion = false; theme.muteBanners = false; applyTheme(); }")
    if clock:
        pg.evaluate(CLOCK)
    return ctx, pg, errs


def step(pg, ms=1000 / 30):
    return pg.evaluate("async (d) => await __clk.advance(d)", ms)


SEED_A = r"""(a) => {
  const topics = [...new Set(QUESTIONS.map(q => (q.topic||'').trim()))].filter(Boolean);
  const unit = topics.includes(a.topic) ? a.topic : topics.find(t => QUESTIONS.filter(q => (q.topic || '').trim() === t).length >= 8);
  const rule = TIER_UNLOCKS[a.rank], ri = TIER_ORDER_FULL.indexOf(a.rank);
  const others = topics.filter(t => t !== unit);
  store.unitPerfects = {};
  if(a.mode === 'run'){
    others.slice(0, rule.badges - 1).forEach(t => { store.unitPerfects[t] = badgeThresholdFor(t); });
    store.unitPerfects[unit] = badgeThresholdFor(unit) - 1;
  } else others.slice(0, rule.badges).forEach(t => { store.unitPerfects[t] = badgeThresholdFor(t); });
  let pts = 500; while(levelProgress(pts).level < rule.level) pts += 100;
  store.lifetime.points = pts + 300; store.lifetime.perfectTests = 900;
  const shown = a.mode === 'run' ? ri : ri - (a.owe || 1) + 1;
  store.rankUpShown = shown; store.rankUpFrom = null; store.rankMapSeen = shown - 1; store.seenUnlockedTiers = TIER_ORDER_FULL.slice(0, shown);
  if(a.fresh){
    /* the rank-tied rewards (a character a rank hands over, a banner a rank earns) are unannounced; everything else was announced
       long ago, so Home's own queue has nothing of its own to play */
    const u = store.unlocksShown = store.unlocksShown || { chars: [], banners: [], fx: [] };
    u.chars = (u.chars || []).filter(id => !((AVATAR_CHARACTERS.find(c => c.id === id) || {}).unlock));
    u.banners = (u.banners || []).filter(id => !((BANNERS.find(b => b.id === id) || {}).rank));
  }
  saveStore();
  return { unit, rank: rankOf(store), owed: rankUpOwed() }; }"""
RUN_UNIT = r"""(unit) => {
  showHome();
  cfg.mode = 'drill'; cfg.source = 'all'; cfg.units = [unit]; cfg.size = 0;
  order = QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === unit && (typeof inWholeUnit !== 'function' || inWholeUnit(i)));
  runTrackable = true; timedOut = false; runMode = 'drill'; runLabel = null; isMissedRetake = false;
  practiceTestMinutes = null; inVirtualRoom = false; attempts = {}; picked = {}; timedOutSet = {};
  try{ firstPick = {}; }catch(e){}
  order.forEach(qi => { attempts[qi] = 1; picked[qi] = optionOrder(qi).indexOf(QUESTIONS[qi].answer); });
  runStartTime = Date.now() - 60000; testInProgress = true; pos = order.length - 1;
  summarize(); return { owed: rankUpOwed(), n: order.length }; }"""


# ---------------------------------------------------------------- real-time journey: frame pacing per phase
SAMPLER = r"""() => {
  if(window.__s) return;
  const S = window.__s = { f: [], on: true, lt: [] };
  try{ new PerformanceObserver(l => l.getEntries().forEach(e => S.lt.push([Math.round(e.startTime), Math.round(e.duration), rankUpScene ? rankUpScene.phase : null]))).observe({ entryTypes: ['longtask'] }); }catch(e){}
  let last = performance.now();
  const rc = el => { const b = el.getBoundingClientRect(); return [b.left, b.top, b.width, b.height]; };
  const tick = t => {
    if(!S.on) return;
    const dt = t - last; last = t;
    const row = { t: Math.round(t), dt: +dt.toFixed(1), ph: rankUpScene ? rankUpScene.phase : null };
    if(S.geo) row.sy = Math.round(scrollY);
    if(S.geo){
      const st = document.querySelectorAll('.rankmap-stop');
      if(st.length) row.n = [...st].slice(0, 3).map(s => { const n = s.querySelector('.rankmap-node'), rd = s.querySelector('.rankmap-road'), c = s.querySelector('.rankmap-card');
        const nb = rc(n), rb = rd ? rc(rd) : null, cb = rc(c);
        return [+(nb[0] + nb[2]/2).toFixed(2), rb ? +(rb[0] + rb[2]/2).toFixed(2) : null, +nb[2].toFixed(2), +nb[1].toFixed(1), +cb[1].toFixed(1)]; });
    }
    S.f.push(row);
    requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}"""
EVENTS = r"""() => { if(window.__ev) return; const E = window.__ev = []; const t0 = () => Math.round(performance.now());
  let last = null;
  setInterval(() => { const p = (typeof rankUpScene !== 'undefined' && rankUpScene) ? rankUpScene.phase : null; if(p !== last){ E.push([t0(), 'phase', p]); last = p; } }, 16);
  new MutationObserver(ms => ms.forEach(m => { [...m.addedNodes].forEach(n => { if(n.nodeType === 1 && (n.id || n.className)) E.push([t0(), 'add', n.id || String(n.className).split(' ')[0]]); }); })).observe(document.body, { childList: true });
  new MutationObserver(() => { const s = stage.querySelector('[data-screen]'); const cls = stage.firstElementChild ? stage.firstElementChild.className.split(' ').slice(0, 3).join('.') : ''; if(cls !== window.__lastScr){ window.__lastScr = cls; E.push([t0(), 'screen', cls, s ? s.dataset.screen : null]); } }).observe(stage, { childList: true });
}"""
PROBE = r"""() => { const sp = document.querySelector('.rs-spot.is-up'); return { lock: document.body.classList.contains('rankup-lock'), sc: rankUpScene ? rankUpScene.phase : null,
  home: !!document.querySelector('[data-screen=home]'), nova: !!document.getElementById('nova-rank'), spot: !!sp, now: Math.round(performance.now()),
  owed: !!rankUpOwed(), cut: !!document.getElementById('supernova-cutscene') }; }"""
PERSON = r"""() => {
  const sp = document.querySelector('.rs-spot.is-up');
  if(sp){ if(!sp.__t0) sp.__t0 = performance.now(); if(performance.now() - sp.__t0 > 2600) sp.click(); }
  const el = document.getElementById('nova-rank'); const n = el && el.__nova;
  if(n){ if(!el.__t0) el.__t0 = performance.now(); if(performance.now() - el.__t0 > 900){ el.__t0 = performance.now(); if(n.typing) n.advance(); else if(n.index < n.count - 1) n.advance(); else { const g = el.querySelector('.nt-go'); if(g) g.click(); } } } }"""


def run_journey(pg, cdp=None, rate=1, timeout=170, geo=False, tick=None, settle=6, home_wait=0, stop_after=None):
    """Real time. Owes one rank on Home, taps the Profile tab when Home calls, plays everything as a person would (reward
    cards tapped once they have been up 2.6s, Nova's words read through) until the journey, its cutscene and the reward
    cards are done and `settle` seconds have passed with nothing owed. Returns (frames, events, longtasks, tap_ms)."""
    import time as _t
    if cdp is not None and rate != 1:
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": rate})
    pg.evaluate(SAMPLER); pg.evaluate(EVENTS)
    if geo:
        pg.evaluate("()=>{ window.__s.geo = true; }")
    pg.evaluate("()=>{ showHome(); }")
    t0 = _t.time(); tap = None; over_at = None
    while _t.time() - t0 < timeout:
        pg.wait_for_timeout(200)
        st = pg.evaluate(PROBE)
        if st["lock"] and not st["sc"] and tap is None and _t.time() - t0 >= home_wait:
            tap = pg.evaluate("()=>{ const t = Math.round(performance.now()); window.__tap = t; document.getElementById('bottomtab-profile').click(); return t; }")
        pg.evaluate(PERSON)
        if tick:
            tick(pg, st)
        if stop_after and st["sc"] == stop_after:
            break
        if tap is not None and not st["sc"] and not st["owed"] and not st["lock"] and not st["spot"] and not st["cut"]:
            if over_at is None:
                over_at = _t.time()
            if _t.time() - over_at > settle:
                break
        else:
            over_at = None
    out = pg.evaluate("()=>{ __s.on = false; return { f: __s.f, lt: __s.lt, ev: __ev }; }")
    if cdp is not None and rate != 1:
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
    return out["f"], out["ev"], out["lt"], tap


def pacing(frames, key="ph", lo=None, hi=None):
    """per-phase frame stats: n, mean, p95, max, and the count over 20ms (a dropped frame at 60Hz) and over 33ms (a visibly chopped one)"""
    d = {}
    for f in frames:
        if lo is not None and f["t"] < lo:
            continue
        if hi is not None and f["t"] > hi:
            continue
        d.setdefault(f[key], []).append(f["dt"])
    res = {}
    for k, v in d.items():
        s = sorted(v)
        res[k] = dict(n=len(v), mean=round(sum(v) / len(v), 1), p95=s[max(0, int(len(s) * .95) - 1)], max=max(v), gt20=sum(1 for x in v if x > 20), gt33=sum(1 for x in v if x > 33))
    return res
