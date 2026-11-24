"""Shared harness for build 384.119 (lagaudio): tools/check-b384-lagaudio.py and the before/after recordings.

The used account of the top-row gate (b384_toprow_lib: badges, hundos, the board's classmates through a fake Firestore, every one-time
card seen), in either class, on an installed iPhone 17 Pro Max at its real pixel ratio (440x956, 3x, insets 62/34 substituted into the
served copy) unless asked otherwise. TAP drives a real touch through CDP (touchStart, a held finger, touchEnd), so a press is what a
finger does: :active, pointer events, the click synthesised from the touch. TIMING watches a tap from the page: the Event Timing entry
of its click (startTime, processing, the next paint) and every animation frame after it, with what is on the screen in each."""
import json, os, re, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b384_toprow_lib as T
ROOT = T.ROOT
CHROME = T.CHROME
g = T.g

def raw_of(path=None, ref=None):
    """index.html as served: a file, a git ref (origin/main), or this checkout."""
    if ref:
        import subprocess
        return subprocess.run(["git", "-C", ROOT, "show", ref + ":index.html"], capture_output=True, text=True).stdout
    return open(path or os.path.join(ROOT, "index.html"), encoding="utf-8").read()

def open_page(br, raw, devkey="promax", cls="ifc", dpr=3, settle=True, extra_init=None, safari_sound=True):
    name, w, h, ins, installed, ua, notched = T.DEVICES[devkey]
    ctx = br.new_context(viewport={"width": w, "height": h}, screen={"width": w, "height": h}, device_scale_factor=dpr,
                         has_touch=True, is_mobile=True, user_agent=ua)
    if installed: ctx.add_init_script(g["STANDALONE"])
    ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]()))
    ctx.add_init_script(T.INIT % (json.dumps(json.dumps(T.seed())), T.IFC if cls == "ifc" else ""))
    if extra_init: ctx.add_init_script(extra_init)
    pg = ctx.new_page(); body = T.body_for(raw, ins)
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    m = re.search(r'const APP_BUILD = "([^"]+)"', body); bld = m.group(1) if m else ""
    pg.route("**/version.json*", lambda route, request, b=bld: route.fulfill(status=200, headers={"content-type": "application/json"},
             body=json.dumps({"build": b, "note": "", "frameId": "", "force": True, "safariSound": bool(safari_sound)})))
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.set_default_timeout(180000)
    pg.goto(T.url(), timeout=240000)
    if settle:
        pg.wait_for_timeout(3600)
        pg.evaluate(T.QUIET)
        pg.wait_for_timeout(400)
    return ctx, pg, errs

def cdp(pg):
    return pg.context.new_cdp_session(pg)

def throttle(s, rate):
    s.send("Emulation.setCPUThrottlingRate", {"rate": rate})

def center(pg, sel):
    r = pg.evaluate("""s => { const e = document.querySelector(s); if(!e) return null; e.scrollIntoView({ block: 'nearest' }); const b = e.getBoundingClientRect();
      return [b.left + b.width / 2, b.top + Math.min(b.height / 2, 30)]; }""", sel)
    return r

def tap(s, x, y, hold_ms=70, pg=None):
    """A finger: down, held, up (CDP touch events; Chromium makes the click from them)."""
    s.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y, "radiusX": 6, "radiusY": 6, "force": 1, "id": 1}]})
    if pg is not None: pg.wait_for_timeout(hold_ms)
    else: time.sleep(hold_ms / 1000)
    s.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})

# Every Web Audio call the page makes, logged from before the app's script runs: each node's connections, every source's start and
# stop (with the context's clock and whether the page was hidden), automation on a watched AudioParam (the master's gain, marked by
# the gate once it is found), suspend() and its resolution, the leave events as the window's FIRST capture listener sees them, and
# every localStorage write (the other leave handlers' work).
AUDIO = r"""(() => {
  const W = window.__au = { log: [], edges: [], srcs: [], params: [], nodes: new Map() };
  const now = () => performance.now();
  let id = 0;
  const tag = n => { if(!n.__id){ n.__id = ++id; W.nodes.set(n.__id, n); } return n.__id; };
  const live = n => { try{ return !(n.context instanceof OfflineAudioContext); }catch(e){ return true; } };
  const C = AudioNode.prototype.connect;
  AudioNode.prototype.connect = function(dst, ...a){
    if(live(this)) W.edges.push({ from: tag(this), to: dst instanceof AudioNode ? tag(dst) : 0, fk: this.constructor.name, tk: dst && dst.constructor ? dst.constructor.name : '', dest: dst === this.context.destination, at: now() });
    return C.call(this, dst, ...a); };
  const D = AudioNode.prototype.disconnect;
  AudioNode.prototype.disconnect = function(...a){ if(live(this)) W.log.push(['disc', tag(this), this.constructor.name, now()]); return D.apply(this, a); };
  const S0 = AudioScheduledSourceNode.prototype.start, S1 = AudioScheduledSourceNode.prototype.stop;
  AudioScheduledSourceNode.prototype.start = function(when, ...a){
    if(live(this)){ const ctx = this.context; W.srcs.push({ id: tag(this), kind: this.constructor.name, start: Math.max(when || 0, ctx.currentTime), at: now(), ct: ctx.currentTime, hidden: document.hidden, stop: null }); }
    return S0.call(this, when, ...a); };
  AudioScheduledSourceNode.prototype.stop = function(when){
    if(live(this)){ const s = W.srcs.find(x => x.id === this.__id); if(s){ const t = (when == null || when === 0) ? this.context.currentTime : Math.max(when, this.context.currentTime); s.stop = s.stop == null ? t : Math.min(s.stop, t); s.stopAt = now(); (s.st = s.st || []).push([t, now()]); } }
    return S1.call(this, when); };
  ['setValueAtTime', 'linearRampToValueAtTime', 'exponentialRampToValueAtTime', 'setTargetAtTime', 'cancelScheduledValues', 'cancelAndHoldAtTime'].forEach(m => {
    const o = AudioParam.prototype[m]; if(!o) return;
    AudioParam.prototype[m] = function(...a){ if(this.__watch) W.params.push({ m, a, at: now(), ct: this.__ctx.currentTime, w: this.__watch, v: vd.get.call(this) }); return o.apply(this, a); }; });
  const vd = Object.getOwnPropertyDescriptor(AudioParam.prototype, 'value');
  Object.defineProperty(AudioParam.prototype, 'value', { configurable: true, get(){ return vd.get.call(this); },
    set(v){ if(this.__watch) W.params.push({ m: 'value=', a: [v], at: now(), ct: this.__ctx.currentTime, w: this.__watch, v: vd.get.call(this) }); vd.set.call(this, v); } });
  const SU = AudioContext.prototype.suspend;
  AudioContext.prototype.suspend = function(){ const t = this.currentTime; W.log.push(['suspend', now(), t]); const p = SU.call(this); try{ p.then(() => W.log.push(['suspended', now()])); }catch(e){} return p; };
  ['visibilitychange', 'pagehide', 'freeze'].forEach(t => addEventListener(t, () => W.log.push(['event', t, now(), document.hidden]), true));
  const SI = Storage.prototype.setItem;
  Storage.prototype.setItem = function(k, v){ W.log.push(['setItem', k, now()]); return SI.call(this, k, v); };
  window.__made = 0;
  const A = window.AudioContext;
  window.AudioContext = function(...a){ window.__made++; return new A(...a); };
  window.AudioContext.prototype = A.prototype;
})()"""
# the live master: the gain that feeds the limiter that feeds the destination (the newest such, on the live context)
MASTER = """() => { const W = window.__au; const toDest = new Set(W.edges.filter(e => e.dest).map(e => e.from));
  const m = W.edges.filter(e => e.fk === 'GainNode' && e.tk === 'DynamicsCompressorNode' && toDest.has(e.to)).map(e => e.from);
  return m.length ? m[m.length - 1] : null; }"""
# when the page could run anything at all after a moment: a chain of 0ms timers started then (a busy main thread - the page's
# own other work, or this machine's load - holds them all back alike); FREE(after_ms) is the first that ran at or after it
PROBE = """() => { const W = window.__au; W.probe = []; const t0 = performance.now();
  const p = () => { W.probe.push(performance.now() - t0); if(performance.now() - t0 < 600) setTimeout(p, 1); }; setTimeout(p, 0); W.probeAt = t0; }"""
def free_after(probe, at_ms):
    later = [t for t in (probe or []) if t >= at_ms]
    return later[0] if later else None
HIDE = """(on) => { Object.defineProperty(document, 'hidden', { configurable: true, get: () => on });
  Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => on ? 'hidden' : 'visible' });
  document.dispatchEvent(new Event('visibilitychange', { bubbles: true })); }"""
# every frame after a tap, from the page: what each rAF sees, and the click's Event Timing entry
WATCH = """(sel) => {
  window.__lg = { frames: [], ev: [], click: null, sel };
  try{ new PerformanceObserver(l => l.getEntries().forEach(e => { if(e.name === 'click' || e.name === 'pointerup' || e.name === 'pointerdown' || e.name === 'touchend')
    window.__lg.ev.push({ name: e.name, start: e.startTime, ps: e.processingStart, pe: e.processingEnd, dur: e.duration }); }))
    .observe({ type: 'event', durationThreshold: 16, buffered: false }); }catch(e){}
  window.addEventListener('click', e => { if(!window.__lg.click) window.__lg.click = { ts: e.timeStamp, at: performance.now() }; }, true);
  const f = t => { if(!window.__lg) return; window.__lg.frames.push([Math.round(t * 10) / 10, (window.__lgProbe ? window.__lgProbe() : null)]);
    if(window.__lg.frames.length < 600) requestAnimationFrame(f); };
  requestAnimationFrame(f);
}"""
