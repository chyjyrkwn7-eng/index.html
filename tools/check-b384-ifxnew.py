"""Build 384: Fire Code's 75 - the Thermal Camera, in the Fire Alarm's place.
Madison: "The fire alarm one, absolutely not the move. That thing is terrible. Make that one something else, get creative match
the theme of them all. Give me the best you can make." In the Fire Code class, on the iPhone 17 Pro Max (440x956), read off the
page:
(1) the bubbles rung (75 hundos) plays the Thermal Camera's own build (ifxThermal) - ifxAlarm and the Fire Alarm's sprites (pull
    station, bell, horn, strobe flare, sound arcs) are gone - and the academy's bubbles is still its own (hfxBubbles);
(2) it plays across the screen and in the box, and like every effect moves only transform and opacity, carries no svg filter and
    puts up no more than 170 pieces;
(3) it ends by its total with a soft tail: every animation it starts is over by HUNDO_FX_TOTAL (the box alone by
    HUNDO_FX_BOX_TOTAL); seeked to the tail's start something is still fading, 60ms before the total nothing shows; and played
    for real, once the total has passed its screen layer and box layer are gone and no screen layer or dim is left on the page;
(4) the reticle locks round the 100%: once it has locked (.42s on) its four corners frame the number (it sits inside them, and
    they are no more than 2.4 times its area);
(5) the copies of the 100% it heats are the number itself - each sits on the real one within half a pixel, in its own tabular
    figures (a proportional copy is 7px narrower: a double image as one hands over to the other);
(6) the readout pegs at 1000 when it goes white-hot (the four digit strips read 1, 0, 0, 0);
(7) its tile and its still draw (a full drawing, not an empty one) and neither is the Fire Alarm's;
(8) its sound is installed in Fire Code (SND_IFX), renders not silent and not clipping, and is scored on the effect's beats: its
    loudest moment is the white-hot beat and the lock is a hit of its own;
(9) no page errors.
Run:  python3 tools/check-b384-ifxnew.py   (--against OLD/index.html must FAIL)"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); H = ROOT + "/tools"
# (384) record-landing.py no longer wraps the cutscene harness (Get Started round 2 made it self-contained), so the
# harness it used to hand over as g["g"] - record-cutscenes.py's, at 1.5x - is loaded here the way it loaded it
src = open(H + "/record-cutscenes.py").read().split("\nSCENES = [")[0].replace("device_scale_factor=1)", "device_scale_factor=1.5)")
_rc = {"__file__": H + "/record-cutscenes.py", "__name__": "rc"}; exec(src, _rc)
g = {"g": _rc}
from playwright.sync_api import sync_playwright
rc = g["g"]
BODY = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read() if "--against" in sys.argv else open(ROOT + "/index.html", encoding="utf-8").read()
seed = dict(rc["SEED"]); seed["publicId"] = "xph5b57jbp5a"; seed["firstName"] = "Maddog"; seed["novaMet"] = 99
srv, port = rc["serve"]()
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)
# the Fire Alarm's tile and still (3b6f4ad), hashed with their gradient ids taken out
ALARM = {"tile": "6cf37feb", "still": "126e08de"}
def page(br, ifc):
    ctx = br.new_context(viewport={"width": 440, "height": 956}, device_scale_factor=1)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true});")
    s = ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
         "localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.daily.seen','x');localStorage.setItem('class26e.drill.v1',%s);" % json.dumps(json.dumps(seed)))
    if ifc:
        s += ("localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done'); localStorage.setItem('class26e.activeclass','ifc');"
              "if(!localStorage.getItem('class26e.ifc.drill.v1')) localStorage.setItem('class26e.ifc.drill.v1', %s);" % json.dumps(json.dumps(seed)))
    pg.add_init_script(s + "}catch(e){}")
    pg.route("**/index.html", lambda route, request: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(3500)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    return ctx, pg, errs
# a grade card with a real 100% in it, on the results screen's type
CARD = """() => { document.querySelectorAll('.__probe').forEach(e => e.remove());
  const card = document.createElement('div'); card.className = 'rs-card rs-grade is-perfect __probe';
  card.style.cssText = 'position:fixed;left:30px;top:170px;width:380px;height:185px';
  const pct = document.createElement('span'); pct.className = 'rs-pct pct perfect'; pct.style.cssText = 'position:absolute;left:24px;top:44px;font-size:67px;line-height:.95';
  gradePctMarkup(pct, 100); card.appendChild(pct); document.body.appendChild(card);
  window.__card = card; window.__pct = pct; }"""
SNAP = r"""() => {
  const out = { cls: window.NOVA_CLASS };
  const hash = s => { let h = 2166136261; for(let i = 0; i < s.length; i++){ h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0).toString(16); };
  const norm = s => s.replace(/hfx[ps]\d+/g, 'G');
  out.build = (HUNDO_FX_BUILD.bubbles || {}).name || null;
  out.alarmGone = typeof ifxAlarm === 'undefined' && typeof ifxSpr !== 'undefined' && !['pull', 'pullH', 'bell', 'clapper', 'horn', 'flare', 'wave'].some(k => k in ifxSpr);
  out.need = (HUNDO_FX.find(r => r.id === 'bubbles') || {}).need;
  const t = buildHundoFxTile('bubbles'), sv = t.querySelector('svg'), st = buildHundoFxStill('bubbles');
  out.tile = sv ? { n: sv.querySelectorAll('*').length, h: hash(norm(sv.innerHTML)) } : null;
  out.still = st ? { n: st.querySelectorAll('*').length, h: hash(norm(st.innerHTML)) } : null;
  out.snd = (typeof SND_IFX !== 'undefined' && SND_IFX['hundo.bubbles'] && SOUND_CATALOGUE['hundo.bubbles'].fn === SND_IFX['hundo.bubbles'].fn);
  out.beats = (typeof IFX_TIC !== 'undefined') ? IFX_TIC : null;
  out.total = HUNDO_FX_TOTAL.bubbles; out.boxTotal = HUNDO_FX_BOX_TOTAL.bubbles; out.tail = HUNDO_FX_TAIL_AT.bubbles;
  return out; }"""
# plays it on the card, paused; reports its pieces and what its animations move and when they end
PLAY = r"""(boxOnly) => {
  document.getAnimations().forEach(a => { try{ a.cancel(); }catch(e){} });
  let h;
  if(boxOnly){ const st = buildHundoFxStage('bubbles', { big: true }); st.classList.add('__probe'); st.style.cssText = 'position:fixed;left:20px;top:420px;width:400px';
    document.body.appendChild(st); window.__st = st; h = playHundoFx('bubbles', { box: st, pct: st.querySelector('.hfx-stage-pct'), boxOnly: true }); }
  else h = playHundoFx('bubbles', { box: window.__card, pct: window.__pct, preview: true });
  window.__h = h;
  const mine = document.getAnimations().filter(a => a.effect && a.effect.target && ((h.screen && h.screen.contains(a.effect.target)) || (h.box && h.box.contains(a.effect.target))));
  mine.forEach(a => a.pause());
  window.__mine = mine;
  const props = [...new Set(mine.flatMap(a => a.effect.getKeyframes().flatMap(k => Object.keys(k))))].filter(p => ['offset', 'computedOffset', 'easing', 'composite'].indexOf(p) < 0).sort();
  return { screen: h.screen ? h.screen.querySelectorAll('*').length : 0, box: h.box ? h.box.querySelectorAll('*').length : 0, props, n: mine.length,
    end: Math.max(...mine.map(a => a.effect.getComputedTiming().endTime)),
    filters: Object.keys(hfxSprites).filter(k => /^ifx-/.test(k) && /<filter|filter=/.test(hfxSprites[k].text || '')) }; }"""
SEEK = r"""(ms) => { window.__mine.forEach(a => { a.currentTime = ms; });
  const h = window.__h, roots = [h.screen, h.box].filter(Boolean);
  const vis = el => { let o = 1; for(let e = el; e && roots.indexOf(e) < 0; e = e.parentElement) o *= +getComputedStyle(e).opacity; return o; };
  let most = 0; roots.forEach(r => r.querySelectorAll('*').forEach(e => { if(!e.children.length) most = Math.max(most, vis(e)); }));
  return Math.round(most * 1000) / 1000; }"""
# at a moment: the corners round the number, the copies on it, the readout's digits
LOOK = r"""(ms) => { window.__mine.forEach(a => { a.currentTime = ms; });
  const h = window.__h, scr = h.screen, rr = n => { const r = document.createRange(); r.selectNodeContents(n); const b = r.getBoundingClientRect(); return [b.left, b.top, b.right, b.bottom]; };
  const real = rr(window.__pct.firstChild);
  const url = k => { const s = hfxSprites[k]; return s ? [s.svg, s.png].filter(Boolean) : []; };
  const has = (e, k) => url(k).some(u => (e.style.backgroundImage || '').indexOf(u.slice(5, -2)) >= 0);
  const Ls = [...scr.querySelectorAll('i')].filter(e => has(e, 'ifx-ticl')).sort((a, b) => a.offsetWidth - b.offsetWidth).slice(0, 4).map(e => e.getBoundingClientRect());
  const fr = Ls.length === 4 ? [Math.min(...Ls.map(r => r.left)), Math.min(...Ls.map(r => r.top)), Math.max(...Ls.map(r => r.right)), Math.max(...Ls.map(r => r.bottom))] : null;
  const copies = [...scr.querySelectorAll('i'), ...(h.box ? h.box.querySelectorAll('i') : [])].filter(e => e.firstChild && e.firstChild.nodeType === 3 && e.firstChild.nodeValue === window.__pct.firstChild.nodeValue).map(e => rr(e.firstChild));
  const strips = [...scr.querySelectorAll('i')].filter(e => has(e, 'ifx-ticdig'));
  const digits = strips.map(e => { const m = new DOMMatrix(getComputedStyle(e).transform); const cell = e.offsetHeight / 11; const d = Math.round(-m.m42 / cell); return d === 10 ? '' : String(d); });
  return { real, fr, copies, digits }; }"""
RENDER = r"""async (beats) => {
  const buf = await NovaSound.render('hundo.bubbles', { sr: 24000 });
  const L = buf.getChannelData(0), R = buf.getChannelData(1), w = 1200, env = [];
  for(let k = 0; k + w <= L.length; k += w){ let m = 0; for(let i = k; i < k + w; i++) m = Math.max(m, Math.abs(L[i]), Math.abs(R[i])); env.push(m); }
  const peak = Math.max(...env), at = env.indexOf(peak) * .05;
  const near = t => Math.max(...env.slice(Math.max(0, Math.round(t / .05) - 1), Math.round(t / .05) + 2));
  const before = t => { const a = env.slice(Math.max(0, Math.round(t / .05) - 8), Math.max(1, Math.round(t / .05) - 2)); return a.reduce((x, y) => x + y, 0) / a.length; };
  return { peak, at, lock: beats ? near(beats.full.lock) : 0, lockBefore: beats ? before(beats.full.lock) : 1, len: L.length / 24000 }; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    errs_all = []
    ctx, pg, errs = page(br, False)
    acad = pg.evaluate("() => ({ cls: window.NOVA_CLASS, build: (HUNDO_FX_BUILD.bubbles || {}).name })")
    errs_all += errs; ctx.close()
    ctx, pg, errs = page(br, True)
    S = pg.evaluate(SNAP)
    chk("(1) in Fire Code (%s) the 75 (%s hundos) plays its own build, %s; the Fire Alarm and its sprites are gone (%s); the academy's is still %s"
        % (S["cls"], S["need"], S["build"], S["alarmGone"], acad["build"]),
        S["cls"] == "ifc" and S["need"] == 75 and S["build"] == "ifxThermal" and S["alarmGone"] and acad["cls"] == "academy" and acad["build"] == "hfxBubbles", [S, acad])
    pg.evaluate(CARD)
    P = pg.evaluate(PLAY, False)
    chk("(2) it plays across the screen (%s pieces) and in the box (%s), moves only %s, no svg filter (%s), no more than 170 pieces"
        % (P["screen"], P["box"], P["props"], P["filters"]), 30 <= P["screen"] <= 170 and P["box"] >= 1 and P["props"] == ["opacity", "transform"] and not P["filters"], P)
    tail = pg.evaluate(SEEK, S["tail"]); last = pg.evaluate(SEEK, S["total"] - 60)
    look_lock = pg.evaluate(LOOK, int((S["beats"] or {"full": {"lock": 2.75}})["full"]["lock"] * 1000 + 420))
    look_hot = pg.evaluate(LOOK, int((S["beats"] or {"full": {"hot": 3.35}})["full"]["hot"] * 1000 + 300))
    pg.evaluate("() => { window.__mine.forEach(a => { try{ a.cancel(); }catch(e){} }); if(window.__h) window.__h.stop(); }")
    pg.wait_for_timeout(900)
    B = pg.evaluate(PLAY, True)
    pg.evaluate("() => { window.__mine.forEach(a => { try{ a.cancel(); }catch(e){} }); if(window.__h) window.__h.stop(); document.querySelectorAll('.__probe').forEach(e => e.remove()); }")
    pg.wait_for_timeout(900)
    # for real: the whole of it, then the page as it was
    pg.evaluate(CARD)
    # (the page's own unlock card can be up with a showcase of an effect in it: only what this play put up counts)
    n0 = pg.evaluate("() => { window.__pre = new Set(document.querySelectorAll('.hfx-layer, .hfx-dim')); return window.__pre.size; }")
    pg.evaluate("() => { window.__h = playHundoFx('bubbles', { box: window.__card, pct: window.__pct, preview: true }); }")
    pg.wait_for_timeout(S["total"] + 300)
    for _ in range(30):
        if pg.evaluate("() => window.__h.done"): break
        pg.wait_for_timeout(100)
    pg.wait_for_timeout(200)
    gone = pg.evaluate("() => ({ screen: !!(window.__h.screen && window.__h.screen.isConnected), box: !!(window.__h.box && window.__h.box.isConnected), done: window.__h.done, n: [...document.querySelectorAll('.hfx-layer, .hfx-dim')].filter(e => !window.__pre.has(e) && !e.closest('.rs-spot')).length })")
    chk("(3) it ends by its total (%sms): its animations end by %sms (the box alone by %s of %s); at the tail (%sms) a piece still shows (%s), 60ms before the total none (%s); "
        "played for real its layers are gone (%s): %s screen layers or dims left (%s before)" % (S["total"], P["end"], B["end"], S["boxTotal"], S["tail"], tail, last, gone, gone["n"], n0),
        P["end"] <= S["total"] and B["end"] <= S["boxTotal"] and B["box"] >= 10 and tail > .05 and last < .03 and not gone["screen"] and not gone["box"] and gone["done"] and gone["n"] == 0, [P["end"], B, tail, last, gone, n0])
    real, fr = look_lock["real"], look_lock["fr"]
    inside = fr and fr[0] <= real[0] + 1 and fr[1] <= real[1] + 1 and fr[2] >= real[2] - 1 and fr[3] >= real[3] - 1
    ratio = fr and ((fr[2] - fr[0]) * (fr[3] - fr[1])) / max(1, (real[2] - real[0]) * (real[3] - real[1]))
    chk("(4) once it has locked (.42s on) the reticle's corners frame the 100%% (number %s, corners %s, %.2fx its area)" % ([round(v) for v in real], fr and [round(v) for v in fr], ratio or 0),
        inside and ratio <= 2.4, look_lock)
    cp = look_lock["copies"]
    off = max([max(abs(a - b) for a, b in zip(c, real)) for c in cp] or [99])
    chk("(5) the %d copies of the 100%% sit on the number (worst %.2fpx)" % (len(cp), off), len(cp) >= 5 and off <= .5, cp)
    chk("(6) the readout pegs at 1000 when it goes white-hot (%s)" % "".join(look_hot["digits"]), look_hot["digits"] == ["1", "0", "0", "0"], look_hot["digits"])
    chk("(7) its tile (%s shapes) and its still (%s) draw, and neither is the Fire Alarm's" % (S["tile"] and S["tile"]["n"], S["still"] and S["still"]["n"]),
        S["tile"] and S["still"] and S["tile"]["n"] >= 25 and S["still"]["n"] >= 10 and S["tile"]["h"] != ALARM["tile"] and S["still"]["h"] != ALARM["still"], [S["tile"], S["still"]])
    snd = pg.evaluate(RENDER, S["beats"])
    hot = S["beats"]["full"]["hot"] if S["beats"] else -9
    chk("(8) its sound is installed in Fire Code (%s), renders not silent and not clipping (peak %.3f), its loudest moment the white-hot beat (%.2fs, the beat %.2fs), the lock a hit (%.3f over %.3f before)"
        % (S["snd"], snd["peak"], snd["at"], hot, snd["lock"], snd["lockBefore"]),
        S["snd"] and .05 < snd["peak"] < .98 and abs(snd["at"] - hot) <= .12 and snd["lock"] > 2 * snd["lockBefore"], snd)
    errs_all += errs
    chk("(9) no page errors (%s)" % errs_all[:3], not errs_all)
    ctx.close(); br.close()
srv.shutdown()
sys.exit(0 if ok else 1)
