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
  z3. the hidden switch is rendered (never display:none), takes no taps and
      is hidden from screen readers; none of its click / change events reach
      the app (no listener at document level sees them, no switch sound).
  z4. a text field that had focus keeps it.
  z5. Haptics off: nothing flips; the choice is saved and survives a reload.

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
        el = pg.evaluate("""() => { const l = document.querySelector('label.nova-haptic'); if(!l) return null;
          const i = l.querySelector('input'); const cs = getComputedStyle(l); const r = l.getBoundingClientRect();
          return { sw: i && i.hasAttribute('switch'), disp: cs.display, pe: cs.pointerEvents, aria: l.getAttribute('aria-hidden'),
                   w: r.width, h: r.height, tab: i && i.tabIndex, inBody: l.parentNode === document.body }; }""")
        check("z3 the hidden control is a native switch in a label", el and el["sw"], str(el))
        check("z3 it is rendered (not display:none), 1px, takes no taps",
              el and el["disp"] != "none" and el["w"] >= 1 and el["pe"] == "none", str(el))
        check("z3 it is hidden from screen readers and the tab order", el and el["aria"] == "true" and el["tab"] == -1, str(el))
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


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cb.CHROME)
        try:
            only = os.environ.get("ONLY", "")
            for fn in (z1, z2_z3_z4, z5):
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
