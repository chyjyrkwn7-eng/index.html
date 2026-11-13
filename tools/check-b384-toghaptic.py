"""Build 384.107: a swipe across a toggle flips it through the NATIVE switch's own gesture, so iOS plays its own tick.
Madison, on his installed iPhone: "The toggle switches, when tapping them, the Haptic Touch is there, when swiping them
it's not though, fix that."

On an iPhone the app lays each switch row's own checkbox over its drawn track as a real <input type=checkbox switch>
(NovaSound hsw-opt), because only a TRUSTED click on a native switch, or the switch following a finger itself, plays the
Taptic tick (WebKit, CheckboxInputType.cpp / EventDispatcher.cpp). A tap was the switch's own click. A swipe was the app's:
the glass knob (NSW layer) followed the finger and the release flipped the row with click() - untrusted, so no tick - after
putting back, with a .checked write, anything the native switch had done, and swallowing the switch's own click after it.

Chromium has no native switch and no Taptic Engine, so this gate emulates the one thing WebKit's switch does that the page
can see: a touch that started on a switch ends with the switch clicking ITSELF (WebKit: touchend/touchcancel ->
dispatchSimulatedClick), unless a page listener cancelled that touchend; and Chromium's own tap-click on it, which iOS never
sends (the switch handles the touchstart), is dropped. It also gives HTMLInputElement a `switch` property, as an engine with
switches (iOS 17.4+) has. Real CDP touches on an iPhone 17 Pro Max (440x956, installed, iPhone user agent).

  T1  every toggle on every toggle screen (Settings > Sound & Haptics, Study, Motion & Effects, Leaderboard & Privacy; the
      Drill and Review start sheets): the native switch's box IS the drawn track (each edge within 1px), a finger anywhere on
      the track lands on it, and nothing may pan a touch off it (touch-action none);
  T2  a horizontal swipe on a toggle (each screen, both ways; a quick flick and a slow drag past WebKit's 200ms hold): every
      touch and pointer event of it goes to the switch, none is cancelled or has its default prevented by the page;
  T3  ...no script changes the row's .checked or calls click() on it during or after the swipe (its handler repainting it
      the value it already has is not a commit); the flip is the switch's own click,
      exactly one change, the row flips once, and the knob glides to its new end without turning back (no flicker);
  T4  a swipe the way the switch already is leaves it as it is (the switch's own click is not let through);
  T5  an upright drag that starts on the track does not flip it; one that starts on the row's words scrolls the page;
  T6  a tap on the track, and one on the row's words, still flip it once;
  T7  Reduce motion: a swipe still flips it through the switch's own click, with no glass knob and no script write;
  T8  no page errors.
ONLY A PHONE can confirm the tick itself. What this proves is the wiring the tick needs: the finger's swipe is delivered to
the native switch untouched, and the flip a person sees is the switch's own trusted click, never the page's.

Run:  python3 tools/check-b384-toghaptic.py [--against REV|DIR]   (--against origin/main must FAIL T1, T3, T4, T5)"""
import importlib.util, json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("glitches", os.path.join(HERE, "check-b384-glitches.py"))
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)   # takes --against from sys.argv
from playwright.sync_api import sync_playwright
chk = G.chk

# WebKit's switch, as far as the page can see it (see the docstring). Runs before the page's own scripts.
EMULATE = r"""(()=>{
  if(!('switch' in HTMLInputElement.prototype)) Object.defineProperty(HTMLInputElement.prototype, 'switch', { configurable: true,
    get(){ return this.hasAttribute('switch'); }, set(v){ if(v) this.setAttribute('switch', ''); else this.removeAttribute('switch'); } });
  const isSw = t => !!(t && t.tagName === 'INPUT' && t.type === 'checkbox' && t.hasAttribute('switch'));
  const G = window.__gate = { emuNow: false, emu: 0, ownDropped: 0, prevented: [] };
  let lastEnd = null;
  const end = e => {
    const t = e.target; if(!isSw(t)) return;
    if(e.defaultPrevented){ G.prevented.push(e.type); return; }       /* WebKit: no default handling for a cancelled event */
    lastEnd = { t, at: performance.now() };
    G.emuNow = true; try{ t.click(); } finally { G.emuNow = false; }
    G.emu++;
  };
  window.addEventListener('touchend', end); window.addEventListener('touchcancel', end);
  window.addEventListener('click', e => {
    if(e.isTrusted && lastEnd && e.target === lastEnd.t && performance.now() - lastEnd.at < 600){ lastEnd = null; e.preventDefault(); e.stopImmediatePropagation(); G.ownDropped++; }
  }, true);
})()"""
# what the page writes to a switch row, what reaches it, and which click the change came from
SPY = r"""()=>{ const G = window.__gate; if(G.spy) return; G.spy = 1; G.watch = false; G.writes = []; G.ev = [];
  const st = () => (new Error().stack || '').split('\n').slice(2, 5).map(s => s.trim()).join(' | ').slice(0, 260);
  const d = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'checked');
  Object.defineProperty(HTMLInputElement.prototype, 'checked', { configurable: true, get(){ return d.get.call(this); },
    set(v){ if(G.watch && this === G.target && !!v !== d.get.call(this)) G.writes.push('checked=' + v + ' @ ' + st()); return d.set.call(this, v); } });
  const ck = HTMLElement.prototype.click;
  HTMLElement.prototype.click = function(){ if(G.watch && !G.emuNow && (this === G.target || this === (G.target && G.target.parentElement))) G.writes.push('click() @ ' + st()); return ck.call(this); };
  const nm = t => !t || t.nodeType !== 1 ? String(t && t.nodeName) : t.tagName + (t.hasAttribute && t.hasAttribute('switch') ? '[switch]' : '') + '.' + String(t.className || '').trim().split(/\s+/).slice(0, 2).join('.');
  ['pointerdown','pointermove','pointerup','pointercancel','touchstart','touchmove','touchend','touchcancel'].forEach(k => window.addEventListener(k, e => {
    if(!G.watch) return; const p = G.ev[G.ev.length - 1];
    if(p && p.k === k && k.endsWith('move') && p.tg === nm(e.target) && p.dp === e.defaultPrevented) return;
    G.ev.push({ k, tg: nm(e.target), dp: e.defaultPrevented, el: e.target }); }));
  window.addEventListener('click', e => { if(G.watch && e.target && e.target.closest && e.target.closest('.opt')) G.ev.push({ k: 'click', tg: nm(e.target), emu: G.emuNow, tr: e.isTrusted, el: e.target }); }, true);
  window.addEventListener('change', e => { if(G.watch && e.target && e.target.closest && e.target.closest('.opt')) G.ev.push({ k: 'change', tg: nm(e.target), el: e.target, at: e.target.checked }); }, true);
}"""
# every switch row on screen: its input and drawn track, each brought into view in turn
ROWS = r"""()=>{ const out = [];
  const rows = [...document.querySelectorAll('.opt')].filter(r => r.querySelector(':scope > input[type=checkbox]') && r.querySelector(':scope > .box') && r.getClientRects().length && !r.closest('[hidden]'));
  rows.forEach((r, i) => { r.dataset.tgi = String(i); });
  return rows.map(r => ({ i: r.dataset.tgi, dis: r.querySelector(':scope > input').disabled || r.matches('.is-locked, .is-disabled, .locked') })); }"""
GEO = r"""(i)=>{ const r = document.querySelector('.opt[data-tgi="' + i + '"]'); if(!r) return null;
  r.scrollIntoView({ block: 'center', behavior: 'instant' });
  const inp = r.querySelector(':scope > input'), box = r.querySelector(':scope > .box');
  const B = e => { const q = e.getBoundingClientRect(); return [q.left, q.top, q.right, q.bottom].map(v => Math.round(v * 10) / 10); };
  const b = B(box), n = B(inp);
  const pts = [[(b[0] + b[2]) / 2, (b[1] + b[3]) / 2], [b[0] + 3, b[1] + 3], [b[2] - 3, b[1] + 3], [b[0] + 3, b[3] - 3], [b[2] - 3, b[3] - 3]];
  const lands = pts.map(([x, y]) => document.elementFromPoint(x, y) === inp);
  const ka = getComputedStyle(box, '::after');
  return { sw: inp.hasAttribute('switch'), box: b, inp: n, lands, ta: getComputedStyle(inp).touchAction, on: inp.checked,
    txt: (r.querySelector('.otext') || r).textContent.trim().slice(0, 26), haptics: r.classList.contains('settings-haptics-row'),
    IN: parseFloat(ka.left) || 2, KW: parseFloat(ka.width) || 39, W: box.offsetWidth,
    words: (() => { const o = r.querySelector('.otext'); if(!o) return null; const q = o.getBoundingClientRect(); return [q.left + Math.min(40, q.width / 3), q.top + q.height / 2]; })() }; }"""
# the knob (or the glass over it) frame by frame, from the press until it has settled
REC = r"""(i)=>{ const r = document.querySelector('.opt[data-tgi="' + i + '"]'); const box = r.querySelector(':scope > .box'), inp = r.querySelector(':scope > input');
  const R = window.__rec = { fr: [], on: true, T0: performance.now(), up: null };
  if(!window.__recHook){ window.__recHook = 1; window.addEventListener('pointerup', () => { const q = window.__rec; if(q && q.up == null) q.up = performance.now() - q.T0; }, true); }
  const pos = () => { const lens = box.querySelector('.nsw-lens');
    if(lens){ const m = new DOMMatrixReadOnly(getComputedStyle(lens).transform); return { lens: 1, c: m.m41 + lens.offsetWidth / 2 }; }
    const a = getComputedStyle(box, '::after'); const m = a.transform && a.transform !== 'none' ? new DOMMatrixReadOnly(a.transform) : { m41: 0 };
    return { lens: 0, c: (parseFloat(a.left) || 0) + (parseFloat(a.width) || 0) / 2 + m.m41 }; };
  const f = () => { const p = pos(); R.fr.push({ t: performance.now() - R.T0, lens: p.lens, c: Math.round(p.c * 10) / 10, on: inp.checked }); if(R.on) requestAnimationFrame(f); };
  requestAnimationFrame(f); }"""
READ = "()=>{ const R = window.__rec; R.on = false; return { fr: R.fr, up: R.up }; }"
# the swiped row's own input is the one watched: a row's handler repainting its rows (the same value) is not a drag's commit
WATCH = "(i)=>{ const G = window.__gate; G.writes = []; G.ev = []; G.emu = 0; G.ownDropped = 0; G.prevented = []; G.target = document.querySelector('.opt[data-tgi=\"' + i + '\"] > input'); G.watch = true; }"
UNWATCH = r"""()=>{ const G = window.__gate; G.watch = false;
  const sw = G.ev.find(e => e.k === 'pointerdown'); const el = sw && sw.el;
  return { writes: G.writes, emu: G.emu, prevented: G.prevented,
    ev: G.ev.map(e => ({ k: e.k, tg: e.tg, dp: e.dp, emu: e.emu, tr: e.tr, at: e.at, same: el ? e.el === el : null })) }; }"""

def touch(cdp, kind, x, y):
    cdp.send("Input.dispatchTouchEvent", {"type": kind, "touchPoints": [] if kind == "touchEnd" else [{"x": x, "y": y}]})

def gesture(cdp, x0, y0, dx, dy, steps, dt, hold=0.0):
    touch(cdp, "touchStart", x0, y0)
    if hold: time.sleep(hold)
    for i in range(1, steps + 1):
        touch(cdp, "touchMove", x0 + dx * i / steps, y0 + dy * i / steps); time.sleep(dt)
    touch(cdp, "touchEnd", 0, 0)

def tap(cdp, x, y):
    touch(cdp, "touchStart", x, y); time.sleep(0.06); touch(cdp, "touchEnd", 0, 0)

def knob_c(g, on):
    return g["W"] - g["IN"] - g["KW"] / 2 if on else g["IN"] + g["KW"] / 2

def settle_ok(rec, g, final):
    """after the finger lifts, the knob (or the glass) heads for the final end and never turns back; then the glass is gone"""
    fr = [f for f in rec["fr"] if rec["up"] is not None and f["t"] >= rec["up"]]
    if not fr: return False, "no frames after the release"
    F = knob_c(g, final) + 0.0
    d = [abs(f["c"] - F) for f in fr]
    back = max([d[i] - min(d[:i]) for i in range(1, len(d))] or [0])
    last = fr[-1]
    ok = back <= 2.5 and not last["lens"] and abs(last["c"] - F) <= 1.5 and last["on"] == final
    return ok, {"turned back px": round(back, 1), "end": last, "want c": round(F, 1), "frames": len(fr)}

def swipe_case(pg, cdp, i, tag, kind):
    """one gesture on toggle i; returns (geometry before, result, recording)"""
    g = pg.evaluate(GEO, i); pg.wait_for_timeout(250); g = pg.evaluate(GEO, i)
    b = g["box"]; cy = (b[1] + b[3]) / 2
    on0 = g["on"]
    kc = b[0] + knob_c(g, on0)                       # the knob's middle
    toward = -1 if on0 else 1                        # the way that flips it
    pg.evaluate(WATCH, i); pg.evaluate(REC, i)
    if kind == "flick":   gesture(cdp, kc, cy, toward * 30, 1, 5, 0.018)
    elif kind == "slow":  gesture(cdp, kc, cy, toward * 30, 2, 10, 0.035, hold=0.26)
    elif kind == "wrong": gesture(cdp, kc, cy, -toward * 28, 1, 6, 0.02)
    elif kind == "upright": gesture(cdp, (b[0] + b[2]) / 2, cy, 2, -70, 8, 0.02)
    elif kind == "tap":   tap(cdp, (b[0] + b[2]) / 2, cy)
    elif kind == "words": tap(cdp, g["words"][0], g["words"][1])
    pg.wait_for_timeout(1100)
    rec = pg.evaluate(READ)
    res = pg.evaluate(UNWATCH)
    res["on0"] = on0; res["on1"] = pg.evaluate("(i)=>document.querySelector('.opt[data-tgi=\"' + i + '\"] > input').checked", i)
    return g, res, rec

def flips_by_switch(res):
    ch = [e for e in res["ev"] if e["k"] == "change"]
    cl = [e for e in res["ev"] if e["k"] == "click"]
    return ch, cl

SHEET = """async(mode)=>{ const wait = ms => new Promise(r => setTimeout(r, ms));
  cfg.mode = mode; cfg.source = 'all'; cfg.timer = 'off'; showSetup(); await wait(900);
  const c = document.querySelector('.pick input'); if(c){ c.checked = true; c.dispatchEvent(new Event('change', { bubbles: true })); } await wait(300);
  const nb = document.getElementById('nextbtn'); if(nb) nb.click(); await wait(1600);
  return !!document.querySelector('.unitoptions-modal-sheet.is-setup'); }"""
SCREENS = [("Settings > Sound & Haptics", "()=>showAppearance({ page: 'sound' })", None),
           ("Settings > Study", "()=>showAppearance({ page: 'study' })", None),
           ("Settings > Motion & Effects", "()=>showAppearance({ page: 'motion' })", None),
           ("Settings > Leaderboard & Privacy", "()=>showAppearance({ page: 'rankings' })", None),
           ("Drill's start sheet", None, "drill"), ("Review's start sheet", None, "review")]

def open_screen(pg, js, sheet):
    pg.evaluate("()=>{ try{ showHome(); }catch(e){} document.getElementById('unitoptions-modal')?.remove(); }"); pg.wait_for_timeout(700)
    if sheet: pg.evaluate(SHEET, sheet)
    else: pg.evaluate(js); pg.wait_for_timeout(2000)
    G.clear_popups(pg); pg.wait_for_timeout(500)
    return pg.evaluate(ROWS)

def pick(pg, rows):
    """the toggle to swipe: the last one that can be changed, and not the one that turns the haptic layer itself off"""
    for r in reversed(rows):
        if r["dis"]: continue
        g = pg.evaluate(GEO, r["i"])
        if g and not g["haptics"]: return r["i"]
    return None

WANT = {"T"}
def touch_section(br):
    pg = G.open_dev(br, "promax", inits=[EMULATE, G.seed_init("academy")])
    tag = "Pro Max installed"
    print("\n%s - build %s" % (tag, G.BUILD), flush=True)
    chk("[%s] the haptic layer is on (an iPhone)" % tag, pg.evaluate("()=>NovaSound.canTaptic()"))
    pg.evaluate("()=>{ theme.reduceMotion = false; try{ applyTheme(); }catch(e){} }")
    pg.evaluate(SPY)
    cdp = pg.ctx.new_cdp_session(pg)
    total = 0
    for name, js, sheet in SCREENS:
        rows = open_screen(pg, js, sheet)
        # T1 every toggle on the screen
        bad = []; n = 0
        for r in rows:
            if r["dis"]: continue
            g = pg.evaluate(GEO, r["i"]); pg.wait_for_timeout(120); g = pg.evaluate(GEO, r["i"])
            n += 1
            edges = [abs(a - b) for a, b in zip(g["inp"], g["box"])]
            if not (g["sw"] and max(edges) <= 1.0 and all(g["lands"]) and g["ta"] == "none"):
                bad.append({"row": g["txt"], "switch": g["sw"], "edges off px": [round(e, 1) for e in edges], "lands": g["lands"], "touch-action": g["ta"]})
        total += n
        chk("[%s] T1 %s: every toggle (%d) has the native switch exactly over its track (each edge within 1px), under a finger anywhere on it, and nothing pans a touch off it" % (tag, name, n),
            n >= 1 and not bad, bad[:4])
        i = pick(pg, rows)
        if i is None:
            chk("[%s] %s: a toggle to swipe" % (tag, name), False, rows); continue
        for kind in ("flick", "flick", "slow"):
            g, res, rec = swipe_case(pg, cdp, i, tag, kind)
            way = "on -> off" if g["on"] else "off -> on"
            touches = [e for e in res["ev"] if e["k"] not in ("click", "change")]
            notsw = [e for e in touches if not e["same"] or "[switch]" not in e["tg"]]
            cancelled = [e["k"] for e in touches if e["k"] in ("pointercancel", "touchcancel")]
            dp = [e["k"] for e in touches if e["dp"]] + res["prevented"]
            chk("[%s] T2 %s, a %s swipe %s: every touch and pointer event goes to the switch (%d), none cancelled, none default-prevented by the page" % (tag, name, kind, way, len(touches)),
                touches and not notsw and not cancelled and not dp, {"not the switch": notsw[:3], "cancelled": cancelled, "prevented": dp})
            ch, cl = flips_by_switch(res)
            own = len(ch) == 1 and len(cl) >= 1 and cl[-1]["emu"] and all(c["emu"] for c in cl)
            ok, info = settle_ok(rec, g, not g["on"])
            chk("[%s] T3 %s, a %s swipe %s: no script writes .checked or calls click(); the flip is the switch's own click, one change, flipped once, the knob heads home without turning back" % (tag, name, kind, way),
                not res["writes"] and own and res["on1"] != res["on0"] and ok,
                {"script": res["writes"][:3], "clicks": cl, "changes": len(ch), "flipped": res["on1"] != res["on0"], "knob": info})
            pg.wait_for_timeout(500)
        if name == "Settings > Motion & Effects":
            # T4 the way it already is
            g, res, rec = swipe_case(pg, cdp, i, tag, "wrong")
            ok, info = settle_ok(rec, g, g["on"])
            chk("[%s] T4 %s: a swipe the way the switch already is leaves it as it was (no change, knob back home)" % (tag, name),
                res["on1"] == res["on0"] and not [e for e in res["ev"] if e["k"] == "change"] and not res["writes"] and ok, {"on": [res["on0"], res["on1"]], "script": res["writes"][:2], "knob": info})
            # T5 an upright drag on the track; and on the row's words, the page scrolls
            pg.evaluate("()=>{ const h = document.querySelector('#stage > *'); if(h){ h.style.paddingBottom = '1400px'; } window.scrollTo({ top: 0, behavior: 'instant' }); }"); pg.wait_for_timeout(400)
            g, res, rec = swipe_case(pg, cdp, i, tag, "upright")
            chk("[%s] T5 %s: an upright drag that starts on the track does not flip it" % (tag, name),
                res["on1"] == res["on0"] and not [e for e in res["ev"] if e["k"] == "change"] and not res["writes"], {"on": [res["on0"], res["on1"]], "ev": [e["k"] for e in res["ev"]][-8:]})
            g = pg.evaluate(GEO, i); pg.wait_for_timeout(200); g = pg.evaluate(GEO, i)
            y0 = pg.evaluate("()=>document.scrollingElement.scrollTop")
            on0 = g["on"]
            gesture(cdp, g["words"][0], g["words"][1], 0, -160, 10, 0.02); pg.wait_for_timeout(800)
            y1 = pg.evaluate("()=>document.scrollingElement.scrollTop")
            on1 = pg.evaluate("(i)=>document.querySelector('.opt[data-tgi=\"' + i + '\"] > input').checked", i)
            chk("[%s] T5 %s: an upright drag that starts on a toggle row's words scrolls the page, and flips nothing" % (tag, name), y1 - y0 > 40 and on1 == on0, {"scroll": [y0, y1], "on": [on0, on1]})
            pg.evaluate("()=>{ window.scrollTo({ top: 0, behavior: 'instant' }); }"); pg.wait_for_timeout(400)
            # T6 taps
            for kind in ("tap", "words"):
                g, res, rec = swipe_case(pg, cdp, i, tag, kind)
                ch, cl = flips_by_switch(res)
                ok, info = settle_ok(rec, g, not g["on"])
                chk("[%s] T6 %s: a tap on the %s flips it once, and the knob lands" % (tag, name, "track" if kind == "tap" else "row's words"),
                    len(ch) == 1 and res["on1"] != res["on0"] and not res["writes"] and ok, {"changes": len(ch), "on": [res["on0"], res["on1"]], "script": res["writes"][:2], "knob": info})
                pg.wait_for_timeout(500)
    # T7 reduce motion
    rows = open_screen(pg, "()=>showAppearance({ page: 'study' })", None)
    pg.evaluate("()=>{ theme.reduceMotion = true; try{ applyTheme(); }catch(e){} }"); pg.wait_for_timeout(500)
    i = pick(pg, rows)
    g, res, rec = swipe_case(pg, cdp, i, tag, "flick")
    ch, cl = flips_by_switch(res)
    lens = any(f["lens"] for f in rec["fr"])
    chk("[%s] T7 Reduce motion: a swipe still flips the toggle through the switch's own click, once, with no glass knob and no script write" % tag,
        len(ch) == 1 and cl and all(c["emu"] for c in cl) and res["on1"] != res["on0"] and not lens and not res["writes"], {"changes": len(ch), "clicks": cl, "lens": lens, "script": res["writes"][:2]})
    pg.evaluate("()=>{ theme.reduceMotion = false; try{ applyTheme(); }catch(e){} }")
    chk("[%s] T1 toggles read, all screens: %d" % (tag, total), total >= 15, total)
    chk("[%s] T8 no page errors" % tag, not pg.errs, pg.errs[:3])
    pg.ctx.close()

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G.CHROME)
    print("build %s" % G.BUILD, flush=True)
    if "T" in WANT: touch_section(br)
    br.close()
print("\n%s - %d failed" % ("ALL PASS" if not G.fails else "FAIL", len(G.fails)))
sys.exit(1 if G.fails else 0)
