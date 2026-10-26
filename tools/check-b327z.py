#!/usr/bin/env python3
"""Build 327 (b327z): haptics on an iPhone, through the native switch.

Madison: "It seems like it is possible to make it work on iPhones after
all. Let's make this work... would be the greatest feature we could add."

Chromium has no Taptic Engine, so this cannot feel anything. What it holds
is everything around the tick:

  z1. an iPhone gets a Haptics switch in Settings, on by default; an iPad, an
      Android phone (Vibration instead) and a desktop do not.
  z2. a real tap on an answer flips the hidden switch, in the tap's own
      handler (the counter moves before the click returns), and keeps
      doing it with sound turned off.
  z3. each tick is a fresh display:none label + switch in <head>, clicked and
      removed (ios-haptics' own form, round 8), hidden from screen readers;
      none of its click / change events reach the app.
  z4. a text field that had focus keeps it.
  z5. Haptics off: nothing flips; the choice is saved and survives a reload.
  z6. Home's planet and bubbles answer on pointerdown, which is not a gesture
      to WebKit for a finger: their tick is held to that touch's release
      (pointerup/touchend), one per touch, and a touch that becomes a scroll
      (pointercancel) drops it. Round 8; fails on a22b1ff.

  python3 tools/check-b327z.py [--against FILE]

Fails on 363b05d (no switch, no row).
"""
import importlib.util, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py"))
cb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cb)
from playwright.sync_api import sync_playwright

check, booted, USED_ACCOUNT = cb.check, cb.booted, cb.USED_ACCOUNT

UA = {
    "iphone": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
    "ipad": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Safari/605.1.15",
    "android": "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Mobile Safari/537.36",
}

def init_for(kind):
    s = ""
    if kind in UA:
        s += "Object.defineProperty(navigator,'userAgent',{get:()=>%r});" % UA[kind]
    if kind == "iphone":
        s += "try{Object.defineProperty(navigator,'standalone',{get:()=>true});}catch(e){}"
    if kind == "ipad":
        s += "Object.defineProperty(navigator,'maxTouchPoints',{get:()=>5});"
    if kind == "android":
        s += "navigator.vibrate = navigator.vibrate || (()=>true);"
    # what the app's own document-level listeners would see
    s += """window.__hswFlips = 0; window.__flipEv = [];
      window.addEventListener('change', e => { const t = e.target; if(t && t.classList && t.classList.contains('nova-hsw')){ window.__hswFlips++; window.__flipEv.push(window.__lastEvName || 'none'); } }, true);
      ['pointerdown','pointerup','touchstart','touchend','click'].forEach(ev => window.addEventListener(ev, () => { window.__lastEvName = ev; }, true));
      window.__docSeen = [];
      ['click','change','input'].forEach(ev => document.addEventListener(ev, e => {
        const t = e.target; window.__docSeen.push(ev + ':' + (t && (t.className || t.tagName)));
      }, true));"""
    return s

SETTINGS_ROWS = """() => ({
  haptics: !!document.querySelector('.settings-haptics-row'),
  vibrate: !!document.querySelector('.settings-vibrate-row'),
  on: (() => { const r = document.querySelector('.settings-haptics-row'); const i = r && r.querySelector('input[type=checkbox], [role=switch]');
               return i ? (i.getAttribute('aria-checked') === 'true' || i.checked === true) : null; })() })"""

START = """() => { cfg.mode = 'drill';
  beginRun(QUESTIONS.map((q, i) => i).filter(i => QUESTIONS[i].topic === 'Identity Crimes'), null); }"""


def open_settings(pg):
    pg.evaluate("() => showAppearance()")
    pg.wait_for_timeout(900)


def start_run(pg):
    pg.evaluate(START)
    for _ in range(40):
        pg.wait_for_timeout(250)
        if pg.evaluate("() => !!document.querySelector('.qpanel .choice')"):
            return True
    return False


def z1(br):
    for kind, want in (("iphone", "haptics"), ("ipad", None), ("android", "vibrate"), ("desktop", None)):
        ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, init=init_for(kind), touch=kind != "desktop", dpr=2)
        try:
            open_settings(pg)
            r = pg.evaluate(SETTINGS_ROWS)
            if want == "haptics":
                check("z1 iPhone: Settings has a Haptics switch", r["haptics"], str(r))
                check("z1 iPhone: it is on by default", r["on"] is True, str(r))
                check("z1 iPhone: no Android Vibration row", not r["vibrate"], str(r))
            elif want == "vibrate":
                check("z1 Android: Vibration, not Haptics", r["vibrate"] and not r["haptics"], str(r))
            else:
                check("z1 %s: no Haptics switch (no Taptic Engine)" % kind, not r["haptics"], str(r))
        finally:
            ctx.close()


def z2_z3_z4(br):
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, init=init_for("iphone"), touch=True, dpr=2)
    try:
        check("z2 a run starts", start_run(pg))
        pg.evaluate("() => { window.__novaTaptic = 0; window.__hswFlips = 0; window.__docSeen = []; }")
        # read at the end of the tap's own click dispatch (window, bubbling):
        # a script tick has to happen inside the gesture, not on a timer after it
        pg.evaluate("""() => { window.__inClick = null; window.addEventListener('click', e => {
          if(e.target && e.target.closest && e.target.closest('.qpanel .choice')) window.__inClick = window.__novaTaptic || 0; }); }""")
        pg.tap(".qpanel .choice")
        pg.wait_for_timeout(250)
        got = pg.evaluate("() => (window.__novaTaptic || 0) + (window.__hswFlips || 0)")
        check("z2 a tap on an answer ticks (the switch under the finger, or the script one where it missed)", got >= 1, str(got))
        inside = pg.evaluate("() => ({ click: window.__inClick, flips: window.__hswFlips || 0, ev: window.__flipEv.slice(0, 3) })")
        check("z2 ...inside the tap's own gesture (the switch flips on the tap itself; a script tick is inside the click)",
              inside["flips"] >= 1 or (inside["click"] is not None and inside["click"] >= 1), str(inside))
        pg.wait_for_timeout(700)   # no tap on a switch is "recent" any more: the script form below is the fallback
        # MOVED IN 327 round 8: the switch is ios-haptics' own form now - a
        # fresh display:none label in <head>, clicked and removed per tick.
        el = pg.evaluate("""() => { let got = null;
          /* the label is in and out inside one call, so catch it as it goes in */
          const orig = HTMLLabelElement.prototype.click;
          HTMLLabelElement.prototype.click = function(){
            if(!got && this.matches('label.nova-haptic')){ const i = this.querySelector('input');
              got = { sw: !!(i && i.hasAttribute('switch')), disp: this.style.display, aria: this.getAttribute('aria-hidden'),
                      tab: i ? i.tabIndex : null, inHead: this.parentNode === document.head }; }
            return orig.apply(this, arguments); };
          window.__novaTaptic = 0; NovaSound.haptic('select');
          HTMLLabelElement.prototype.click = orig;
          return { got, left: document.querySelectorAll('label.nova-haptic').length, n: window.__novaTaptic }; }""")
        g = (el or {}).get("got") or {}
        check("z3 each tick is a native switch in a label", g.get("sw") is True, str(el))
        check("z3 ...display:none, in <head>, and gone again straight after (the ios-haptics form)",
              g.get("disp") == "none" and g.get("inHead") is True and el["left"] == 0 and el["n"] == 1, str(el))
        check("z3 it is hidden from screen readers and the tab order", g.get("aria") == "true" and g.get("tab") == -1, str(el))
        seen = pg.evaluate("() => window.__docSeen.filter(x => /nova-haptic|INPUT/.test(x))")
        check("z3 none of its click/change events reach the app", not seen, str(seen))
        # sound off, haptics still on
        pg.evaluate("() => { theme.soundOn = false; saveTheme(); NovaSound.sync(); window.__novaTaptic = 0; }")
        pg.wait_for_timeout(500)
        pg.evaluate("""() => { const c = [...document.querySelectorAll('.qpanel .choice')].find(x => !x.disabled && !x.classList.contains('is-wrong-pick'));
          window.__tapTarget = c; }""")
        if pg.evaluate("() => !!document.querySelector('#nextbtn') && !document.querySelector('#nextbtn').hidden"):
            pg.evaluate("() => document.querySelector('#nextbtn').click()")
            pg.wait_for_timeout(900)
        pg.evaluate("() => { window.__hswFlips = 0; window.__novaTaptic = 0; }")
        pg.tap(".qpanel .choice")
        pg.wait_for_timeout(250)
        got = pg.evaluate("() => (window.__novaTaptic || 0) + (window.__hswFlips || 0)")
        check("z2 with sound off, a tap still ticks", got >= 1, str(got))
        # focus kept
        r = pg.evaluate("""() => { const f = document.createElement('input'); f.type = 'text'; f.id = 'zfield';
          document.body.appendChild(f); f.focus(); NovaSound.haptic('tap');
          const kept = document.activeElement === f; f.remove(); return { kept, n: window.__novaTaptic }; }""")
        check("z4 a focused text field keeps its focus", r["kept"], str(r))
    finally:
        ctx.close()


def z5(br):
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, init=init_for("iphone"), touch=True, dpr=2)
    try:
        open_settings(pg)
        row = pg.query_selector(".settings-haptics-row")
        check("z5 the Haptics row is there", bool(row))
        if not row:
            return
        row.scroll_into_view_if_needed()
        pg.wait_for_timeout(300)
        b = row.bounding_box()
        pg.mouse.click(b["x"] + b["width"] - 30, b["y"] + b["height"] / 2)
        pg.wait_for_timeout(500)
        st = pg.evaluate("() => ({ t: theme.haptics, saved: JSON.parse(localStorage.getItem('class26e.drill.v1')||'{}').theme })")
        check("z5 turning it off saves haptics:false", st["t"] is False and st["saved"] and st["saved"].get("haptics") is False, str(st)[:200])
        pg.evaluate("() => { window.__novaTaptic = 0; window.__hswFlips = 0; NovaSound.play('ui.tap.primary'); NovaSound.haptic('tap'); }")
        got = pg.evaluate("() => (window.__novaTaptic || 0) + (window.__hswFlips || 0)")
        check("z5 off: nothing flips", got == 0, str(got))
        # the seed is re-written on every navigation, so read it back the way
        # a reload does: loadTheme() from the saved account
        back = pg.evaluate("() => { theme.haptics = true; loadTheme(); return theme.haptics; }")
        check("z5 off survives a reload (loadTheme reads it back)", back is False, str(back))
    finally:
        ctx.close()


def z6(br):
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, init=init_for("iphone"), touch=True, dpr=2)
    try:
        pg.evaluate("() => showHome()")
        pg.wait_for_timeout(1500)
        r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
          const out = {};
          const sphere = [...document.querySelectorAll('[data-screen="home"] svg circle')].find(c => c.style.cursor === 'pointer');
          const bubble = document.querySelector('[data-screen="home"] .cosmic-badge-tappable');
          out.have = { sphere: !!sphere, bubble: !!bubble };
          const pe = (t, el) => el.dispatchEvent(new PointerEvent(t, { bubbles: true, cancelable: true, pointerType: 'touch', isPrimary: true, pointerId: 7, button: 0 }));
          let duringDown = null;
          const spy = () => { duringDown = window.__novaTaptic || 0; };
          for(const [name, el] of [['sphere', sphere], ['bubble', bubble]]){
            if(!el) continue;
            await wait(200);
            window.__novaTaptic = 0;
            window.addEventListener('pointerdown', spy, { once: true });
            pe('pointerdown', el);
            out[name + 'Down'] = duringDown;
            pe('pointerup', el);
            out[name + 'Up'] = window.__novaTaptic || 0;
            el.dispatchEvent(new MouseEvent('click', { bubbles: true }));
            out[name + 'Click'] = window.__novaTaptic || 0;
          }
          /* a touch that turns into a scroll */
          if(bubble){
            await wait(200);
            window.__novaTaptic = 0;
            pe('pointerdown', bubble); pe('pointercancel', bubble); pe('pointerup', bubble);
            out.cancelled = window.__novaTaptic || 0;
          }
          return out; }""")
        check("z6 Home's planet and a rank bubble are there", r["have"]["sphere"] and r["have"]["bubble"], str(r))
        for k in ("sphere", "bubble"):
            check("z6 %s: no tick inside the finger's pointerdown (not a gesture to WebKit)" % k, r.get(k + "Down") == 0, str(r))
            check("z6 %s: one tick on the release" % k, r.get(k + "Up") == 1, str(r))
            check("z6 %s: the click after it does not tick again" % k, r.get(k + "Click") == 1, str(r))
        check("z6 a touch that becomes a scroll (pointercancel) does not tick", r.get("cancelled") == 0, str(r))
        # z7 (round 8): a tap on a results screen / unlock pop-up / cutscene,
        # which makes no sound of its own, still ticks - once
        z = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
          for(const [k, html] of [['results', '<div class="rs-screen"><p>x</p></div>'], ['spot', '<div class="rs-spot"><p>x</p></div>'],
                                  ['cutscene', '<div id="badge-cutscene"><p>x</p></div>'], ['plain', '<div class="plainbox"><p>x</p></div>']]){
            await wait(120);
            const host = document.createElement('div'); host.innerHTML = html; document.body.appendChild(host);
            window.__novaTaptic = 0;
            host.querySelector('p').dispatchEvent(new MouseEvent('click', { bubbles: true }));
            out[k] = window.__novaTaptic || 0; host.remove(); }
          return out; }""")
        for k in ("results", "spot", "cutscene"):
            check("z7 a tap on a %s ticks once" % k, z.get(k) == 1, str(z))
        check("z7 a tap on plain page text does not", z.get("plain") == 0, str(z))
    finally:
        ctx.close()


def z8(br):
    """Nova's introduction, the tour and What's New, with a real finger.

    Madison: "I need it to work through the nova introduction ... and feel
    like the app is legit." Every tap on the bubble, the Let's go button, the
    What's New card's button and each tour tooltip has to tick ONCE, on the
    release (inside the tap's own gesture - WebKit refuses a haptic from a
    timer or a pointerdown), and the typing and the auto-advance must not
    buzz on their own (nothing but a finger may)."""
    ctx = br.new_context(viewport={"width": 440, "height": 956}, has_touch=True, is_mobile=True, device_scale_factor=2)
    ctx.add_init_script(init_for("iphone"))
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.penal256578.seen','1');localStorage.setItem('class26e.savecode.asked','1');localStorage.setItem('class26e.drill.v1', '%s');}catch(e){}" % USED_ACCOUNT)
    ctx.add_init_script("try{localStorage.setItem('class26e.weekrecap.v1','9999-12-31');}catch(e){}")
    pg = cb.open_page(ctx)
    try:
        pg.goto(cb.URL)
        pg.wait_for_timeout(2600)
        pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __stub();}")
        pg.evaluate("""() => { window.__tk = []; window.__ev = [];
          const orig = HTMLLabelElement.prototype.click;
          const op = window.playSound; window.__ids = [];
          HTMLLabelElement.prototype.click = function(){ if(this.matches('label.nova-haptic')) window.__tk.push((window.__lastEv || 'none')); return orig.apply(this, arguments); };
          /* a tap that lands on a switch under the finger flips it: that is the tick on an iPhone with the 26.5 patch */
          /* counted on the CLICK that lands on it, not its change event: a card's button removes its own card in its click handler, and a
             removed input fires no change - but the finger did land on the real switch, which is the whole of what an iPhone needs */
          window.addEventListener('click', e => { if(e.target && e.target.classList && e.target.classList.contains('nova-hsw')) window.__tk.push('click'); }, true);
          const ps = NovaSound.play; NovaSound.play = function(id){ window.__ids.push(id); return ps.apply(this, arguments); };
          ['pointerdown','pointerup','touchstart','touchend','click'].forEach(ev => window.addEventListener(ev, () => { window.__lastEv = ev; }, true)); }""")
        up = pg.wait_for_selector("#nova-intro", timeout=20000) if pg.evaluate("()=>!!document.getElementById('nova-intro')") or True else None
    except Exception as e:
        check("z8 Nova's introduction came up", False, str(e)[:200])
        ctx.close(); return
    check("z8 Nova's introduction came up", True)
    # nothing may buzz by itself while he types and talks
    pg.wait_for_timeout(2500)
    check("z8 typing and talking do not buzz (only a notice banner may, and iOS ignores that outside a tap)", pg.evaluate("()=>window.__tk.length") <= pg.evaluate("()=>window.__ids.filter(i=>i==='ui.notice').length"), str(pg.evaluate("()=>[window.__tk, window.__ids]")))
    pg.evaluate("()=>{window.__tk=[];}")
    steps = 0; bad = []
    for _ in range(60):
        if not pg.evaluate("()=>!!document.getElementById('nova-intro')"): break
        st = pg.evaluate("()=>{const e=document.getElementById('nova-intro'); return e&&e.__nova?{i:e.__nova.index,n:e.__nova.count,t:!!e.__nova.typing}:null}")
        if not st: pg.wait_for_timeout(200); continue
        pg.evaluate("()=>{window.__tk=[];}")
        last = st["i"] == st["n"] - 1 and pg.evaluate("()=>!!document.querySelector('#nova-intro .nt-go')")
        sel = "#nova-intro .nt-go" if last else "#nova-intro"
        try:
            if last: pg.tap(sel)
            else:
                box = pg.evaluate("()=>{const b=document.querySelector('#nova-intro .nt-bubble, #nova-intro .nt-box, #nova-intro'); const r=b.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2];}")
                pg.touchscreen.tap(box[0], box[1])
        except Exception as e:
            bad.append("tap failed: " + str(e)[:80]); break
        pg.wait_for_timeout(350)
        tk = pg.evaluate("()=>window.__tk")
        steps += 1
        if len(tk) > 3 or any(x in ("pointerdown", "touchstart") for x in tk):
            bad.append("step %d: %s %s" % (st["i"], tk, pg.evaluate("()=>window.__ids.slice(-8)")))
        if len(tk) == 0 and not st["t"]:
            bad.append("step %d: silent tap" % st["i"])
        pg.wait_for_timeout(1700)
    check("z8 %d taps through the introduction: each ticks on the release (a prop's own sound may add a short pattern), never on touch-down" % steps, steps > 8 and not bad, str(bad[:6]))
    # then What's New's card and the tooltips that follow it
    try:
        pg.wait_for_selector("#intro-pop .intro-go", timeout=20000); pg.wait_for_timeout(1500)
        pg.evaluate("()=>{window.__tk=[];}")
        pg.evaluate("()=>{const c=document.getElementById('intro-pop'); const sc=[c,...c.querySelectorAll('*')].find(e=>e.scrollHeight>e.clientHeight+20&&getComputedStyle(e).overflowY!='visible'); if(sc) sc.scrollTop=sc.scrollHeight;}")
        pg.wait_for_timeout(500)
        pg.tap("#intro-pop .intro-go"); pg.wait_for_timeout(400)
        tk = pg.evaluate("()=>window.__tk")
        check("z8 What's New's button ticks once, on the release", 1 <= len(tk) <= 3 and "pointerdown" not in tk and "touchstart" not in tk, str(tk))
        n = 0; badtips = []
        pg.wait_for_timeout(1500)
        for _ in range(12):
            if not pg.evaluate("()=>!!document.getElementById('tour-next')"): break
            pg.wait_for_timeout(1500); pg.evaluate("()=>{window.__tk=[];}")
            pg.tap("#tour-next"); pg.wait_for_timeout(400); n += 1
            tk = pg.evaluate("()=>window.__tk")
            if not (1 <= len(tk) <= 3) or "pointerdown" in tk or "touchstart" in tk: badtips.append((n, tk, pg.evaluate("()=>window.__ids.slice(-4)"), pg.evaluate("()=>!!document.getElementById('tour-next')")))
        check("z8 %d tooltip taps: each ticks on the release" % n, n >= 3 and not badtips, str(badtips))
    except Exception as e:
        check("z8 What's New and the tour were reachable", False, str(e)[:200])
    ctx.close()


HSW_STATE = """() => { const all = [...document.querySelectorAll('.nova-hsw')];
  const cs = e => getComputedStyle(e);
  const tabs = [...document.querySelectorAll('.bottomtab')];
  return { n: all.length, count: NovaSound.hswCount ? NovaSound.hswCount() : null,
    tabsWith: tabs.filter(t => t.lastElementChild && t.lastElementChild.classList.contains('nova-hsw')).length, tabs: tabs.length,
    native: all.length && all.every(e => e.tagName === 'INPUT' && e.type === 'checkbox' && e.hasAttribute('switch')),
    hidden: all.filter(e => { const c = cs(e); return c.display === 'none' || c.visibility === 'hidden' || c.appearance === 'none' || c.webkitAppearance === 'none'; }).length,
    opaque: all.filter(e => parseFloat(cs(e).opacity) > 0.02).length,
    badParent: all.filter(e => !e.parentElement || e.parentElement.lastElementChild !== e).length,
    nested: all.filter(e => e.parentElement && e.parentElement.closest('.nova-hsw')).length }; }"""


def z9(br):
    """The real switch under the finger (build 328 / 327l): iOS 26.5 stopped
    ticking for a switch flipped from script; a real finger on a real
    native switch still does. Chromium cannot feel it - this holds the
    wiring: it is there, native, inside its control, covering it, and the
    tap still reaches the control's own handlers."""
    # --- iPhone: present, native, invisible, the whole size of its control
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, init=init_for("iphone"), touch=True, dpr=2)
    try:
        pg.evaluate("() => showHome()")
        pg.wait_for_timeout(1800)
        r = pg.evaluate(HSW_STATE)
        check("z9 iPhone: switches are laid over the controls", r["n"] >= 6 and r["count"] == r["n"], str(r))
        check("z9 iPhone: every tab has one as its last child", r["tabs"] >= 4 and r["tabsWith"] == r["tabs"], str(r))
        check("z9 iPhone: they are real native switches (not stripped, not hidden)", r["native"] and r["hidden"] == 0, str(r))
        check("z9 iPhone: and invisible (opacity 0)", r["opaque"] == 0, str(r))
        check("z9 iPhone: last child of the control, never nested", r["badParent"] == 0 and r["nested"] == 0, str(r))
        # the switch covers the control's padding box (inset:0), so a 1px border
        # shows as 2px at most; a secret flare's switch is its 44px tap disc
        geo = pg.evaluate("""() => [...document.querySelectorAll('.nova-hsw')].map(e => { const a = e.getBoundingClientRect(), b = e.parentElement.getBoundingClientRect();
          const flare = e.parentElement.classList.contains('cosmic-flare-dot');
          if(flare) return (a.width >= b.width - 1 && a.height >= b.height - 1) ? 0 : 99;
          return Math.max(Math.abs(a.width - b.width), Math.abs(a.height - b.height), Math.abs(a.left - b.left), Math.abs(a.top - b.top)); }).filter(d => d > 2.3).length""")
        check("z9 iPhone: each covers its control (within its border)", geo == 0, str(geo))
        planet = pg.evaluate("() => { const p = document.querySelector('.cosmic-sphere-hsw'); return p ? { has: !!p.querySelector('.nova-hsw'), w: p.getBoundingClientRect().width } : null; }")
        check("z9 iPhone: Home's planet has its own overlay", planet and planet["has"] and planet["w"] > 60, str(planet))

        # --- a real tap on a tab reaches the tab's own handler through the switch
        pg.evaluate("""() => { window.__clickT = []; window.addEventListener('click', e => { window.__clickT.push(e.target.className || e.target.tagName); }, true);
          window.__docSeen = []; }""")
        box = pg.evaluate("() => { const r = document.getElementById('bottomtab-profile').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }")
        pg.touchscreen.tap(box[0], box[1])
        pg.wait_for_timeout(1200)
        seen = pg.evaluate("() => ({ clicks: window.__clickT, screen: !!document.querySelector('#stage .screen-profile'), leak: window.__docSeen.filter(x => /^(change|input):/.test(x)) })")
        check("z9 a tap on a tab lands on the switch", any("nova-hsw" in str(c) for c in seen["clicks"]), str(seen))
        check("z9 ...and the tab still navigates (the click reached it)", seen["screen"], str(seen))
        check("z9 ...and no change/input event leaves the switch", not seen["leak"], str(seen))
        check("z9 ...and the switch is left unchecked or reset (never stuck on)", pg.evaluate("() => [...document.querySelectorAll('.nova-hsw')].filter(e => e.checked).length") <= 1)

        # --- a run: answers get switches, a tap on one still answers
        check("z9 a run starts", start_run(pg))
        pg.wait_for_timeout(700)
        ch = pg.evaluate("""() => { const c = [...document.querySelectorAll('.qpanel .choice')];
          return { n: c.length, with: c.filter(x => x.querySelector(':scope > .nova-hsw')).length }; }""")
        check("z9 every answer choice has a switch", ch["n"] >= 2 and ch["with"] == ch["n"], str(ch))
        pg.evaluate("""() => { window.__novaTaptic = 0; window.__clickT = []; window.__atClick = null;
          window.addEventListener('click', e => { if(window.__atClick === null) window.__atClick = window.__novaTaptic || 0; }); }""")
        pg.tap(".qpanel .choice")
        pg.wait_for_timeout(500)
        st = pg.evaluate("""() => ({ clicks: window.__clickT, picked: !!document.querySelector('.qpanel .choice.is-wrong-pick, .qpanel .choice.is-right-pop, .qpanel .choice.is-wrong-flash, .qpanel .choice.locked, .qpanel .choice.picked'),
          taptic: window.__atClick })""")
        check("z9 a tap on an answer lands on the switch and still answers", any("nova-hsw" in str(c) for c in st["clicks"]) and st["picked"], str(st))
        check("z9 ...and that tap's first tick came from the switch, not a script flip (pattern ticks follow on a timer)", st["taptic"] == 0, str(st))
        # a tap that did NOT land on a switch still ticks from script (the fallback)
        pg.evaluate("() => { window.__novaTaptic = 0; }")
        pg.wait_for_timeout(700)
        pg.evaluate("() => { const b = document.createElement('div'); b.id = 'zplain'; document.body.appendChild(b); b.dispatchEvent(new MouseEvent('click', { bubbles: true })); b.remove(); NovaSound.haptic('tap'); }")
        check("z9 a tap not on a switch falls back to the script tick", pg.evaluate("() => window.__novaTaptic || 0") >= 1)

        # --- off: nothing left in the page, and position put back
        pg.evaluate("() => showHome()")
        pg.wait_for_timeout(1500)
        pos_on = pg.evaluate("() => [...document.querySelectorAll('.nova-hsw')].map(e => e.parentElement).filter(h => h.style.position).length")
        check("z9 hosts are positioned by a zero-specificity rule, never an inline style", pos_on == 0, str(pos_on))
        pg.evaluate("() => { theme.haptics = false; saveTheme(); NovaSound.sync(); }")
        pg.wait_for_timeout(300)
        off = pg.evaluate("() => ({ n: document.querySelectorAll('.nova-hsw').length, count: NovaSound.hswCount(), marked: document.querySelectorAll('[data-hsw]').length })")
        check("z9 Haptics off: every switch is gone", off["n"] == 0 and off["count"] == 0, str(off))
        check("z9 Haptics off: no host left marked", off["marked"] == 0, str(off))
        pg.evaluate("() => showProfile()")
        pg.wait_for_timeout(900)
        check("z9 Haptics off: new screens get none", pg.evaluate("() => document.querySelectorAll('.nova-hsw').length") == 0)
        pg.evaluate("() => { theme.haptics = true; saveTheme(); NovaSound.sync(); }")
        pg.wait_for_timeout(1200)
        check("z9 Haptics back on: they return", pg.evaluate("() => document.querySelectorAll('.nova-hsw').length") > 3)
    finally:
        ctx.close()

    # --- not on anything but an iPhone
    for kind in ("ipad", "android", "desktop"):
        ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, init=init_for(kind), touch=kind != "desktop", dpr=2)
        try:
            pg.evaluate("() => showHome()")
            pg.wait_for_timeout(1500)
            n = pg.evaluate("() => document.querySelectorAll('.nova-hsw, .cosmic-sphere-hsw').length")
            check("z9 %s: no switches at all" % kind, n == 0, str(n))
        finally:
            ctx.close()


def z10(br):
    """What the switches must not break: the question swipe that starts on an
    answer, a list scroll that starts on a button, a text field, a native
    toggle, a disabled/locked control."""
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, init=init_for("iphone"), touch=True, dpr=2)
    cdp = ctx.new_cdp_session(pg)
    try:
        check("z10 a run starts", start_run(pg))
        pg.wait_for_timeout(900)
        # which slot is right, which is not (the run is a drill: a wrong pick does not move on)
        info = pg.evaluate("""() => { const qi = order[pos], oo = optionOrder(qi); const right = oo.indexOf(QUESTIONS[qi].answer);
          const cs = [...document.querySelectorAll('.qpanel .choice')];
          const pt = i => { const r = cs[i].getBoundingClientRect(); return [r.left + r.width * .85, r.top + r.height / 2]; };
          return { right, wrong: right === 0 ? 1 : 0, pr: pt(right), pw: pt(right === 0 ? 1 : 0), n: cs.length,
                   sw: cs.filter(c => c.querySelector(':scope > .nova-hsw')).length }; }""")
        check("z10 the unanswered choices carry switches", info["sw"] == info["n"], str(info))
        qn = "() => document.querySelector('.qnum') ? document.querySelector('.qnum').textContent : ''"
        marks = "() => document.querySelectorAll('.qpanel .choice.is-wrong-pick, .qpanel .choice.is-wrong-flash, .qpanel .choice.is-right-pop, .qpanel .choice.locked').length"
        # a swipe that starts on an unanswered answer (its switch) is a swipe: it answers nothing
        cb._swipe(cdp, info["pw"][0], info["pw"][1], -330, 6, steps=10)
        pg.wait_for_timeout(900)
        check("z10 a swipe starting on an unanswered choice (its switch) answers nothing", pg.evaluate(marks) == 0 and pg.evaluate(qn) == "Question 1", "%s marks, %r" % (pg.evaluate(marks), pg.evaluate(qn)))
        # answer it for real (a tap on the right one's switch), then swipe on
        pg.touchscreen.tap(info["pr"][0], info["pr"][1])
        pg.wait_for_timeout(1500)
        check("z10 a tap on the right choice's switch answers it", pg.evaluate("() => { const n = document.getElementById('nextbtn'); return !!n && !n.hidden; }"), "")
        b = pg.evaluate("() => { const c = document.querySelector('.qpanel .choice'); const r = c.getBoundingClientRect(); return [r.left + r.width * .85, r.top + r.height / 2]; }")
        cb._swipe(cdp, b[0], b[1], -330, 6, steps=10)
        pg.wait_for_timeout(1300)
        after = pg.evaluate(qn)
        check("z10 and a swipe from there advances the question", after != "Question 1" and after != "", repr(after))
        # locked choices carry none
        locked = pg.evaluate("() => [...document.querySelectorAll('.choice.locked')].filter(c => c.querySelector('.nova-hsw')).length")
        check("z10 a locked choice has no switch", locked == 0, str(locked))
        # no switch in the controls that are not 'a button'
        pg.evaluate("() => showAppearance()")
        pg.wait_for_timeout(1400)
        bad = pg.evaluate("""() => ({ inInput: document.querySelectorAll('input .nova-hsw, select .nova-hsw, textarea .nova-hsw, label .nova-hsw, .nsw .nova-hsw, .opt .nova-hsw').length,
          onHost: [...document.querySelectorAll('.nova-hsw')].filter(e => e.parentElement.querySelector('button:not(.nova-hsw), a, select, textarea, input:not(.nova-hsw)')).length })""")
        check("z10 none inside a native control, a label, a Settings switch, or a card holding other controls", bad["inInput"] == 0 and bad["onHost"] == 0, str(bad))
        # a scroll that starts on a button (its switch) still scrolls the page, and does not tap it
        done = False
        for name, js in (("Profile", "() => showProfile()"), ("Stats", "() => showProfile('stats')"), ("Leaderboard", "() => showRankings()")):
            pg.evaluate(js)
            pg.wait_for_timeout(1600)
            pg.evaluate("() => window.scrollTo(0, 0)")
            pg.wait_for_timeout(300)
            h = pg.evaluate("() => document.documentElement.scrollHeight - innerHeight")
            pt = pg.evaluate("""() => { const b = [...document.querySelectorAll('#stage button, #stage [role=button]')].find(x => { const r = x.getBoundingClientRect(); return x.querySelector(':scope > .nova-hsw') && r.top > 260 && r.bottom < innerHeight - 200 && r.width > 80; });
              if(!b) return null; const r = b.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }""")
            if h > 250 and pt:
                pg.evaluate("() => { window.__clicks = 0; window.addEventListener('click', () => { window.__clicks++; }, true); }")
                y0 = pg.evaluate("() => scrollY")
                cb._swipe(cdp, pt[0], pt[1], 0, -260, steps=12)
                pg.wait_for_timeout(600)
                y1 = pg.evaluate("() => scrollY")
                clicks = pg.evaluate("() => window.__clicks")
                check("z10 %s: a drag that starts on a button scrolls the page" % name, y1 - y0 > 60, "%s -> %s" % (y0, y1))
                check("z10 %s: ...and does not tap it" % name, clicks == 0, str(clicks))
                done = True
                break
        check("z10 a scrollable page with a switch-bearing button was found", done)
    finally:
        ctx.close()


def z11(br):
    """The layer is invisible: with it on, nothing in any screen moves a pixel
    compared with it off (same page, animations stopped at frame 0)."""
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT, init=init_for("iphone"), touch=True, dpr=2)
    # every element that exists when the first snapshot is taken is numbered; the
    # second reads the same elements (new ones - a flip-book landing, a row
    # arriving - are not what is being tested)
    SNAP1 = """() => { document.getAnimations().forEach(a => { try{ a.pause(); a.currentTime = 0; }catch(e){} });
      /* MOVED IN 327z10: a switch row's own input IS its switch on an iPhone
         (.hsw-opt) and grows over the track by design - it is set aside */
      /* MOVED IN 327z15 round 47: a character's own art is set aside too - its sway runs while
         the character is live (.char-live), which a list row turns on and off on its own clock,
         so between the two snapshots it moved without any switch being touched (failed the same
         way on round 38's build) */
      const els = [...document.querySelectorAll('body *')].filter(e => !e.classList.contains('nova-hsw') && !e.closest('.nova-hsw') && !e.classList.contains('hsw-opt') && !e.closest('.avatarchar-svg'));
      window.__zEls = els; return els.map(e => { const r = e.getBoundingClientRect(); return [Math.round(r.left * 2) / 2, Math.round(r.top * 2) / 2, Math.round(r.width * 2) / 2, Math.round(r.height * 2) / 2]; }); }"""
    SNAP2 = """() => { document.getAnimations().forEach(a => { try{ a.pause(); a.currentTime = 0; }catch(e){} });
      return window.__zEls.map(e => { if(!e.isConnected) return null; const r = e.getBoundingClientRect(); return [Math.round(r.left * 2) / 2, Math.round(r.top * 2) / 2, Math.round(r.width * 2) / 2, Math.round(r.height * 2) / 2]; }); }"""
    def settle(pg):
        last, same = -1, 0
        for _ in range(30):
            n = pg.evaluate("() => [...document.querySelectorAll('body *')].filter(e => !e.classList.contains('nova-hsw') && !e.closest('.nova-hsw')).length")
            same = same + 1 if n == last else 0
            last = n
            if same >= 3: return
            pg.wait_for_timeout(300)
    screens = [("Home", "() => showHome()"), ("Profile", "() => showProfile()"), ("Stats", "() => showProfile('stats')"),
               ("Settings", "() => showAppearance()"), ("Leaderboard", "() => showRankings()"),
               ("Calendar", "() => showCalendarTab ? showCalendarTab() : showCalendar()"),
               ("Units", "() => { cfg.mode = 'drill'; showSetup(); }"), ("Modes", "() => showModeSelect()"),
               ("Friends", "() => showFriends()"), ("Badges", "() => showRanksScreen('badges')"), ("Rank", "() => showRanksScreen('ranks')"),
               ("Customize", "() => showCustomize()"), ("Question", START)]
    try:
        for name, js in screens:
            try:
                # (327z10: the Profile tab's character plays specials now; none
                # may land between the two snapshots - they are not switches)
                pg.evaluate("() => { theme.haptics = true; saveTheme(); NovaSound.sync(); charSpecialTiming = { first: [1e9, 1e9], gap: [1e9, 1e9] }; document.querySelectorAll('[data-sp-next]').forEach(e => e.dataset.spNext = String(Date.now() + 1e9)); }")
                pg.evaluate(js)
                pg.wait_for_timeout(1800)
                settle(pg)
                on = pg.evaluate(SNAP1)
                n_on = pg.evaluate("() => document.querySelectorAll('.nova-hsw').length")
                pg.evaluate("() => { theme.haptics = false; saveTheme(); NovaSound.sync(); }")
                pg.wait_for_timeout(500)
                off = pg.evaluate(SNAP2)
                diffs = []
                for i, (a, b) in enumerate(zip(on, off)):
                    if b is None: continue
                    if any(abs(a[k] - b[k]) > .6 for k in range(4)):
                        diffs.append("%d:%s->%s" % (i, a, b))
                        if len(diffs) > 4: break
                if diffs and os.environ.get("Z11_WHO"):
                    idx = [int(d.split(":")[0]) for d in diffs]
                    print("   who", pg.evaluate("ix => ix.map(i => { const e = window.__zEls[i]; return e ? [e.tagName, String(e.className && e.className.baseVal !== undefined ? e.className.baseVal : e.className).slice(0,60), (e.textContent||'').trim().slice(0,30), e.parentElement && String(e.parentElement.className).slice(0,50)] : null; })", idx))
                check("z11 %s: %d switches, no element moves or resizes by them" % (name, n_on), not diffs and n_on > 0, "; ".join(diffs)[:300])
            except Exception as e:
                check("z11 %s ran" % name, False, str(e)[:200])
    finally:
        ctx.close()


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cb.CHROME)
        try:
            only = os.environ.get("ONLY", "")
            for fn in (z1, z2_z3_z4, z5, z6, z8, z9, z10, z11):
                if only and fn.__name__ not in only.split(","):
                    continue
                try:
                    fn(br)
                except Exception as e:
                    check("%s ran to the end" % fn.__name__, False, str(e)[:200])
        finally:
            br.close()
    cb.SERVER.shutdown()
    print("\n%s  (%d failure(s))" % ("ALL PASS" if not cb.FAILURES else "FAILED: " + ", ".join(cb.FAILURES), len(cb.FAILURES)))
    return 1 if cb.FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
