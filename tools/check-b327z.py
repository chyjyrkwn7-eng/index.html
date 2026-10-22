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
    if kind == "ipad":
        s += "Object.defineProperty(navigator,'maxTouchPoints',{get:()=>5});"
    if kind == "android":
        s += "navigator.vibrate = navigator.vibrate || (()=>true);"
    # what the app's own document-level listeners would see
    s += """window.__docSeen = [];
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
        pg.evaluate("() => { window.__novaTaptic = 0; window.__docSeen = []; }")
        # read at the end of the tap's own click dispatch (window, bubbling):
        # the tick has to happen inside the gesture, not on a timer after it
        pg.evaluate("""() => { window.__inClick = null; window.addEventListener('click', e => {
          if(e.target && e.target.closest && e.target.closest('.qpanel .choice')) window.__inClick = window.__novaTaptic || 0; }); }""")
        pg.tap(".qpanel .choice")
        pg.wait_for_timeout(250)
        got = pg.evaluate("() => window.__novaTaptic || 0")
        check("z2 a tap on an answer flips the hidden switch", got >= 1, str(got))
        inside = pg.evaluate("() => window.__inClick")
        check("z2 ...inside the tap's own click handler", inside is not None and inside >= 1, str(inside))
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
        pg.tap(".qpanel .choice")
        pg.wait_for_timeout(250)
        got = pg.evaluate("() => window.__novaTaptic || 0")
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
        pg.evaluate("() => { window.__novaTaptic = 0; NovaSound.play('ui.tap.primary'); NovaSound.haptic('tap'); }")
        got = pg.evaluate("() => window.__novaTaptic || 0")
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


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cb.CHROME)
        try:
            only = os.environ.get("ONLY", "")
            for fn in (z1, z2_z3_z4, z5, z6, z8):
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
