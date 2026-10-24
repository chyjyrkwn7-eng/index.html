#!/usr/bin/env python3
"""Build 327z14: Safari tabs (the sky under the bars, the tab kept over a
reload, no sound), a silent exit, and the hundo preview matching results.

Madison: "Safari version of the app has a bad problem ... The boxes at the
top and bottom are still there. It also randomly refreshes." Then: "The app
randomly freezes again in safari, I think the sound may be breaking it",
"When leaving the app with sound on, it makes a weird/glitchy noise", and
"for the undo effect unlocks, when you click one to see a preview, that
doesn't match up with our results screen anymore".

  python3 tools/check-b327z14.py
  python3 tools/check-b327z14.py --against /path/to/old/index.html

  A. Leaving is silent: with sound playing, the page going hidden fades the
     master to silence before the context is suspended (150ms later the
     master is under 2% of its level, not frozen at full), and coming back
     brings it up again. (327z15) Nothing is left playing into the
     suspended context: no voice and no ambience loop.
  B. An iPhone Safari tab with the Safari sound switch off still has haptics:
     Settings offers the haptics row and no sound row, and the haptic switch
     layer is mounted.
  C. The hundo preview is the results screen in order: grade card before
     the XP card (as the real results screen has it), the mode pill in its
     header, the count's line under the count, and a second heading in the
     XP card.
  D. In a browser tab the fixed sky runs past the viewport at both ends
     (under Safari's bars), and the root's own colour is the paper.
  E. In a browser tab a reload comes back on the tab that was open.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
import importlib.util
_spec = importlib.util.spec_from_file_location("z5b", os.path.join(HERE, "check-b327z5-b.py"))
z5b = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(z5b)
cb = z5b.cb
check = cb.check
from playwright.sync_api import sync_playwright

ONLY = os.environ.get("B327Z14_ONLY", "ABCDE")
UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1")
HIDE = """h => { Object.defineProperty(document, 'hidden', { get: () => h, configurable: true });
  Object.defineProperty(document, 'visibilityState', { get: () => h ? 'hidden' : 'visible', configurable: true });
  document.dispatchEvent(new Event('visibilitychange')); }"""


def tab_ctx(br, init=None):
    """An iPhone Safari tab (not installed) on Home, the gate's account."""
    ctx = br.new_context(viewport={"width": 440, "height": 830}, has_touch=True, is_mobile=True,
                         device_scale_factor=3, user_agent=UA)
    if init:
        ctx.add_init_script(init)
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.penal256578.seen','1');"
                        "if(!sessionStorage.getItem('__seeded')){localStorage.setItem('class26e.drill.v1', '%s');sessionStorage.setItem('__seeded','1');}"
                        "localStorage.setItem('class26e.weekrecap.v1','9999-12-31');}catch(e){}" % cb.USED_ACCOUNT)
    pg = cb.open_page(ctx)
    pg.goto(cb.URL)
    pg.wait_for_timeout(2600)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __stub();}")
    return ctx, pg


def silent_exit(br):
    print("\nA. leaving with sound on")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    pg.evaluate("()=>{theme.soundOn=true; theme.soundVolume=.7; NovaSound.sync();}")
    c = pg.evaluate("()=>{const r=document.getElementById('bottomtab-home').getBoundingClientRect(); return {x:r.left+r.width/2,y:r.top+r.height/2}}")
    pg.touchscreen.tap(c["x"], c["y"])
    pg.wait_for_timeout(900)
    s0 = pg.evaluate("()=>NovaSound.state()")
    pg.evaluate(HIDE, True)
    pg.wait_for_timeout(150)
    s1 = pg.evaluate("()=>NovaSound.state()")
    pg.wait_for_timeout(300)
    s2 = pg.evaluate("()=>NovaSound.state()")
    check("%s: A. sound is running before leaving" % label, s0["ctxState"] == "running" and (s0["master"] or 0) > .1, s0)
    check("%s: A. 150ms after hiding the master is faded to silence (<2%% of %.2f)" % (label, s0["master"] or 0),
          s1["master"] is not None and s1["master"] < .02 * (s0["master"] or 1), s1)
    check("%s: A. and the context is then suspended" % label, s2["ctxState"] == "suspended", s2)
    # 327z15: nothing is left playing into a suspended context (iOS throttles
    # a hidden page, and what is still scheduled is what glitched)
    check("%s: A. no voice and no ambience loop is left running" % label, s2["voices"] == 0 and s2["amb"] is None, s2)
    pg.evaluate(HIDE, False)
    pg.touchscreen.tap(c["x"], c["y"])
    pg.wait_for_timeout(900)
    s3 = pg.evaluate("()=>NovaSound.state()")
    check("%s: A. back again, it is running at its level" % label,
          s3["ctxState"] == "running" and abs((s3["master"] or 0) - (s0["master"] or 0)) < .05 * (s0["master"] or 1), s3)
    ctx.close()


def tab_haptics(br):
    print("\nB. an iPhone Safari tab with sound switched off keeps haptics")
    ctx, pg = tab_ctx(br, "try{localStorage.setItem('class26e.safarisound','0');}catch(e){}")
    r = pg.evaluate("""()=>{ theme.soundOn=true; theme.haptics=true; NovaSound.sync(); showAppearance();
      return { tab: NovaSound.iosTab, off: NovaSound.tabOff(),
        sound: !!document.querySelector('#stage .settings-sound-row'),
        haptics: !!document.querySelector('#stage .settings-haptics-row'),
        note: !!document.querySelector('#stage .settings-sound-tabnote'),
        on: NovaSound.state().on }; }""")
    pg.wait_for_timeout(600)
    n = pg.evaluate("()=>NovaSound.hswCount()")
    check("B. the page is an iPhone tab with the switch off", r["tab"] and r["off"], r)
    check("B. sound stays off there", not r["on"] and not r["sound"], r)
    check("B. Settings still offers haptics, under the note", r["haptics"] and r["note"], r)
    check("B. and the haptic switches are mounted (%d)" % n, n > 0, n)
    ctx.close()


def mock_order(br):
    print("\nC. the hundo preview is the results screen, in order")
    label, w, h, dpr = z5b.PHONE
    ctx, pg = z5b.boot(br, w, h, dpr)
    r = pg.evaluate("""()=>{ showUnlockDetail(hundoFxDetail(HUNDO_FX[2].id));
      const m=document.querySelector('.hfx-mock'); if(!m) return null;
      const kids=[...m.children].filter(k=>/rs-(head|card|actions)/.test(k.className));
      const at=sel=>kids.findIndex(k=>k.matches(sel));
      const gr=m.querySelector('.rs-grade'), xp=m.querySelector('.rs-xp'), head=m.querySelector('.rs-head');
      const row=gr&&gr.querySelector('.hfx-mk-row');
      return { grade: at('.rs-grade'), xp: at('.rs-xp'), acts: at('.rs-actions'),
        headParts: head ? head.children.length : 0,
        countLines: row && row.lastElementChild ? row.lastElementChild.children.length : 0,
        xpHeads: xp ? xp.querySelectorAll('.hfx-mk-kicker').length : 0,
        unitFrac: gr ? gr.querySelectorAll('.rs-byunit .rs-pair, .rs-byunit b').length : -1,
        fits: (()=>{ const M=m.getBoundingClientRect(), A=m.querySelector('.rs-actions').getBoundingClientRect(); return A.bottom <= M.bottom + .5; })() }; }""")
    check("%s: C. the preview is up" % label, r is not None, r)
    if r:
        check("%s: C. grade card before the XP card, buttons last" % label, 0 <= r["grade"] < r["xp"] < r["acts"], r)
        check("%s: C. header has its title, mode pill, scope and unit (4 parts)" % label, r["headParts"] >= 4, r)
        check("%s: C. the count has its line under it" % label, r["countLines"] >= 2, r)
        check("%s: C. the XP card has its second heading" % label, r["xpHeads"] >= 2, r)
        check("%s: C. the unit's row has no fraction" % label, r["unitFrac"] == 0, r)
        check("%s: C. the buttons fit inside the preview" % label, r["fits"], r)
    ctx.close()


def sky(br):
    print("\nD. the sky runs under Safari's bars")
    ctx, pg = tab_ctx(br)
    r = pg.evaluate("""()=>{ const b=getComputedStyle(document.body,'::before'), a=getComputedStyle(document.body,'::after');
      const probe=document.createElement('div'); probe.style.background='var(--paper)'; document.body.appendChild(probe);
      const paper=getComputedStyle(probe).backgroundColor; probe.remove();
      return { browser: document.documentElement.classList.contains('is-browser'),
        top: parseFloat(b.top), bottom: parseFloat(b.bottom), h: parseFloat(b.height), vh: innerHeight,
        atop: parseFloat(a.top), abottom: parseFloat(a.bottom),
        root: getComputedStyle(document.documentElement).backgroundColor, paper }; }""")
    check("D. the page is in browser mode", r["browser"], r)
    check("D. the glow layer reaches 100px+ above and below the viewport", r["top"] <= -100 and r["bottom"] <= -100 and r["h"] >= r["vh"] + 200, r)
    check("D. the stars layer too", r["atop"] <= -100 and r["abottom"] <= -100, r)
    check("D. the root's colour is the paper", r["root"] == r["paper"], r)
    ctx.close()


def keep_tab(br):
    print("\nE. a reload in a browser tab keeps the tab")
    ctx, pg = tab_ctx(br)
    c = pg.evaluate("()=>{const r=document.getElementById('bottomtab-calendar').getBoundingClientRect(); return {x:r.left+r.width/2,y:r.top+r.height/2}}")
    pg.touchscreen.tap(c["x"], c["y"])
    pg.wait_for_timeout(1200)
    STATE = """()=>({ home: !!document.querySelector('#stage [data-screen="home"]'),
      lit: [...document.querySelectorAll('.bottomtab.active')].map(b=>b.dataset.dest) })"""
    before = pg.evaluate(STATE)
    pg.reload()
    pg.wait_for_timeout(6000)
    after = pg.evaluate(STATE)
    check("E. the calendar was open before the reload", not before["home"] and before["lit"] == ["calendar"], before)
    check("E. and is open after it, with its tab lit", not after["home"] and after["lit"] == ["calendar"], after)
    ctx.close()


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cb.CHROME)
        for k, fn in (("A", silent_exit), ("B", tab_haptics), ("C", mock_order), ("D", sky), ("E", keep_tab)):
            if k in ONLY:
                try:
                    fn(br)
                except Exception as e:
                    check("section %s ran" % k, False, repr(e)[:300])
        br.close()
    print("\n%s" % ("ALL PASS" if not cb.FAILURES else "%d FAILED" % len(cb.FAILURES)))
    sys.exit(1 if cb.FAILURES else 0)


if __name__ == "__main__":
    main()
