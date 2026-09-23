#!/usr/bin/env python3
"""The two Secret Flare screens a walk cannot reach, and the sixteen
characters laid out side by side.

shoot-flow.py clicks through from a fresh install, which is the right way
to shoot anything that can be reached that way - and is why the Customise
screen is in it rather than here. A flare cannot be: it appears at one
randomly chosen question inside a run that has to be started first, and
the banner only exists for five seconds after it is tapped. So this
starts a real run, forces the armed position to the question on screen,
and shoots what is actually there.

The contact sheet is the other half. Every fault in the four new
characters - a marble Zeus that read as a featureless egg, a Detective
whose hat, shadow, skin and coat were all one brown - was invisible in
the path data and obvious the moment sixteen were rendered together, at
the tile size AND at the 34px a rankings row actually uses.

  python3 tools/shoot-flares.py [outdir]
"""
import functools
import http.server
import os
import re
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "shots-flares")
INSET_RE = re.compile(r"env\(safe-area-inset-(top|bottom|left|right)(?:\s*,[^()]*)?\)")

# Madison's own two, and the only two she asked to be sent.
DEVICES = [
    ("iphone-17-pro-max", 440, 956, {"top": 59, "bottom": 34, "left": 0, "right": 0}),
    ("ipad-pro-11", 834, 1194, {"top": 24, "bottom": 20, "left": 0, "right": 0}),
]

SEED = ('{"firstName":"Madison","avatarChar":"ninja","onboardingComplete":true,'
        '"tourRev":99,"leaderboardOptIn":true,'
        '"lifetime":{"points":14820,"answered":5400,"correct":4980,"drillPlays":64,'
        '"examPlays":22,"gamePlays":9,"perfectTests":141,"currentStreak":23,'
        '"longestStreak":57}}')

SRC = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()


def serve():
    so = socket.socket(); so.bind(("127.0.0.1", 0))
    port = so.getsockname()[1]; so.close()

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    srv = http.server.ThreadingHTTPServer(
        ("127.0.0.1", port), functools.partial(Quiet, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, "http://127.0.0.1:%d/index.html" % port


# The status bar is DRAWN, because a screenshot with an unexplained black
# band at the top has now been misread twice - once as a tab-bar bug, once
# as the update banner not being aligned.
STATUS_BAR = """(h)=>{
  if(!h) return;
  const b = document.createElement('div');
  b.style.cssText = 'position:fixed;top:0;left:0;right:0;height:' + h + 'px;z-index:9999;'
    + 'display:flex;align-items:center;justify-content:space-between;'
    + 'padding:0 1.6rem;font:600 15px -apple-system,system-ui;color:#fff;'
    + 'pointer-events:none;letter-spacing:.01em';
  b.innerHTML = '<span>9:41</span><span>\\u25cf\\u25cf\\u25cf  \\u25b0</span>';
  document.body.appendChild(b);
}"""

ARM_HERE = """()=>{
  const topics = [...new Set(QUESTIONS.map(q => (q.topic||'').trim()))].filter(Boolean);
  const t = topics.find(x => /identity/i.test(x)) || topics[0];
  cfg.mode='drill'; cfg.source='all'; cfg.units=[t];
  const pool = QUESTIONS.map((q,i)=>[q,i]).filter(([q]) => (q.topic||'').trim() === t).map(([,i]) => i);
  store.mysteryColorsFound = { red:false, orange:false, yellow:false };
  store.testsUntilMystery = 0;
  beginRun(pool, null, null);
  return true;}"""

# beginRun() puts a ~3s LOADING TEST overlay up before the first
# question, and it swallows pointer events - which is how the first
# version of this ended up retrying a click on the glint until it timed
# out. Wait it out, THEN force the position and re-render.
ARM_NOW = """()=>{
  /* The position is random by design; forcing it to the question on
     screen is the only way to photograph it. Everything else about the
     run is real. */
  mysteryAppearsAtPos = pos;
  mysteryColorThisRun = mysteryColorThisRun || nextNeededMysteryColor();
  mysteryFoundThisSession = false;
  render();
  return !!document.querySelector('.mystery-spark');}"""

SHEET = """()=>{
  const wrap = document.createElement('div');
  wrap.style.cssText = 'padding:20px;display:grid;grid-template-columns:repeat(4,1fr);'
    + 'gap:14px 10px;background:var(--bg,#0F1115);min-height:100vh';
  AVATAR_CHARACTERS.forEach(c => {
    const cell = document.createElement('div');
    cell.style.cssText = 'display:flex;flex-direction:column;align-items:center;gap:6px';
    const box = document.createElement('div');
    box.style.cssText = 'width:100%;aspect-ratio:1;display:flex;align-items:center;'
      + 'justify-content:center;border-radius:12px;background:rgba(255,255,255,.04);'
      + 'border:1px solid rgba(255,255,255,.07)';
    const big = buildAvatarCharSVG(c.id);
    big.style.width = '82%'; big.style.height = '82%';
    box.appendChild(big);
    /* At 34px as well, which is the size a rankings row actually uses -
       a character that only works at tile size is a character nobody
       ever really sees working. */
    const small = buildAvatarCharSVG(c.id);
    small.style.width = '34px'; small.style.height = '34px';
    const lbl = document.createElement('div');
    lbl.style.cssText = 'font:600 12px system-ui;color:var(--ink,#E6EAF2);text-align:center';
    lbl.textContent = AVATAR_DISPLAY_NAME[c.id] || c.id;
    const sub = document.createElement('div');
    sub.style.cssText = 'font:500 9.5px system-ui;color:var(--soft,#8B95A5);'
      + 'text-align:center;line-height:1.3';
    sub.textContent = c.feat ? ((CHARACTER_FEATS[c.feat]||{}).label || '')
      : (c.unlock ? RANK_DISPLAY_NAME[c.unlock] : 'free');
    cell.append(box, small, lbl, sub);
    wrap.appendChild(cell);
  });
  document.body.replaceChildren(wrap);}"""


def main():
    os.makedirs(OUT, exist_ok=True)
    srv, url = serve()
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(executable_path=CHROME)
            for label, w, h, ins in DEVICES:
                body = INSET_RE.sub(
                    lambda m: "%dpx" % ins[m.group(1)], SRC)
                ctx = br.new_context(viewport={"width": w, "height": h},
                                     device_scale_factor=2)
                ctx.add_init_script(
                    "Object.defineProperty(navigator,'standalone',{get:()=>true});")
                ctx.add_init_script(
                    "try{localStorage.setItem('class26e.freshstart','1');"
                    "localStorage.setItem('class26e.frame.ok','go-live-1');"
                    "localStorage.setItem('class26e.drill.v1', '%s');}catch(e){}" % SEED)
                pg = ctx.new_page()
                # A NAMED FUNCTION, NOT A LAMBDA WITH A DEFAULT ARG.
                # Playwright inspects the handler's arity and calls a
                # two-parameter one with (route, request) - so
                # `lambda r, b=body:` had `b` silently replaced by the
                # Request object, fulfill() raised inside the handler,
                # the route was never resolved and every goto hung until
                # its timeout with nothing in the output to say why.
                def route(r, _body=body):
                    r.fulfill(status=200,
                              headers={"content-type": "text/html; charset=utf-8"},
                              body=_body)

                pg.route("**/index.html", lambda r: route(r))
                pg.goto(url, wait_until="domcontentloaded", timeout=60000)
                pg.wait_for_timeout(3000)
                pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
                pg.wait_for_timeout(500)
                pg.evaluate(STATUS_BAR, ins["top"])

                pg.evaluate(ARM_HERE)
                pg.wait_for_selector("#teststart-overlay", state="detached", timeout=20000)
                pg.wait_for_timeout(600)
                armed = pg.evaluate(ARM_NOW)
                pg.wait_for_timeout(700)
                if not armed:
                    print("  !! %s: NO GLINT - the flare never rendered" % label)
                pg.screenshot(path="%s/%s-1-flare-hidden.png" % (OUT, label))

                # And zoomed, because the point of it is that it is small.
                spark = pg.query_selector(".mystery-spark")
                if spark:
                    b = spark.bounding_box()
                    pg.screenshot(path="%s/%s-2-flare-closeup.png" % (OUT, label),
                                  clip={"x": max(0, b["x"] - 80), "y": max(0, b["y"] - 50),
                                        "width": min(w, b["width"] + 160),
                                        "height": b["height"] + 100})
                    spark.click()
                    pg.wait_for_timeout(700)
                    pg.screenshot(path="%s/%s-3-flare-found.png" % (OUT, label))
                    # The third one is the one that matters.
                    pg.evaluate("""()=>{ store.mysteryColorsFound =
                        { red:true, orange:true, yellow:false };
                        mysteryFoundThisSession = false; mysteryColorThisRun = 'yellow';
                        showFlareFoundBanner('yellow', true); }""")
                    pg.wait_for_timeout(700)
                    pg.screenshot(path="%s/%s-4-void-unlocked.png" % (OUT, label))
                    # This is the only banner in the app that lands on a
                    # QUESTION, so the one thing worth measuring is
                    # whether it is sitting on the counter, the Pause
                    # button, the meter or the flag - the controls.
                    # .qnumrow itself is deliberately NOT in this list:
                    # topNoticeOffset() parks the banner directly under
                    # the meter, which is as high as it can go, and what
                    # it then overlaps is the words "Question 1". Lower
                    # would cover the question itself. A label is the
                    # right thing to cover for five seconds; a control
                    # is not. Fixed-position elements
                    # render oddly in fullPage captures, so it is
                    # measured rather than eyeballed.
                    hit = pg.evaluate("""()=>{
                      const b = document.querySelector('.flare-banner');
                      if(!b) return ['no banner'];
                      const r = b.getBoundingClientRect();
                      /* A banner that cannot take a tap cannot steal
                         one, so an overlap is only a defect while it
                         is interactive. */
                      if(getComputedStyle(b).pointerEvents === 'none') return [];
                      return [...document.querySelectorAll(
                        '.wrap > .top, .wrap > .count, .wrap > .meter, #timerline, .flagbtn')]
                        .filter(e => { const q = e.getBoundingClientRect();
                          return q.width && q.height &&
                            !(r.right <= q.left || r.left >= q.right ||
                              r.bottom <= q.top || r.top >= q.bottom); })
                        .map(e => e.className || e.id);}""")
                    if hit:
                        print("  !! %s: the flare banner is sitting on %s"
                              % (label, hit))

                # Home, with all three orbit dots lit.
                pg.evaluate("""()=>{ store.mysteryColorsFound =
                    { red:true, orange:true, yellow:true }; saveStore();
                    window.forceHideBottomTabs = false; showHome(); }""")
                pg.wait_for_timeout(900)
                pg.screenshot(path="%s/%s-5-home-three-found.png" % (OUT, label))

                pg.evaluate(SHEET)
                pg.wait_for_timeout(600)
                pg.screenshot(path="%s/%s-6-all-sixteen.png" % (OUT, label),
                              full_page=True)
                print("%s: done" % label)
                ctx.close()
            br.close()
    finally:
        srv.shutdown()
    print("-> %s" % OUT)


main()
