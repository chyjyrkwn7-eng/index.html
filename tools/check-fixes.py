#!/usr/bin/env python3
"""Assert each fix from the iPad bug report, on every device, both ways in.

The sweep asks "is anything broken" and check-positions asks "did it land
where I meant it to". Neither asks "is this specific fix actually in effect
here", which is the question after a batch of device-reported bugs. Every
check below is a measurement, not a code read.
"""
import argparse, functools, http.server, io, os, re, socket, sys, threading
from PIL import Image
from playwright.sync_api import sync_playwright

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSET_RE = re.compile(r"env\(safe-area-inset-(top|bottom|left|right)(?:\s*,[^()]*)?\)")
STANDALONE = """
Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});
(function(){ const mm = window.matchMedia.bind(window);
  window.matchMedia = q => /display-mode:\\s*standalone/.test(q)
    ? {matches:true, media:q, addListener(){}, removeListener(){},
       addEventListener(){}, removeEventListener(){}, onchange:null, dispatchEvent(){return false;}}
    : mm(q); })();"""

def load(name, pat):
    s = io.open(os.path.join(ROOT, "tools/sweep-layout.py")).read()
    m = re.search(pat, s, re.S)
    return m.group(1)

SEED = load("SEED", r'SEED = """(.*?)"""')
DEVICES = eval("[" + load("DEVICES", r'DEVICES = \[(.*?)\n\]') + "]")
CHROME_H = eval(load("CHROME_H", r'CHROME_H = (\{.*?\})'))

def patched(insets):
    src = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    t, r, b, l = insets
    v = {"top": f"{t}px", "right": f"{r}px", "bottom": f"{b}px", "left": f"{l}px"}
    return INSET_RE.sub(lambda m: v[m.group(1)], src)

def serve():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{port}/index.html"

CHECKS = """(() => {
  const out = {};
  const R = s => { const e = document.querySelector(s); return e && e.getBoundingClientRect(); };

  // 1. grey bar: html's fallback glow must be anchored to the viewport
  const hs = getComputedStyle(document.documentElement);
  /* No background-attachment assertion. It was one, and it was wrong:
     `fixed` was the first attempted grey-bar fix, it is unsupported on
     iOS Safari (treated as scroll), and asserting it here only proved
     Chromium honoured something the target platform ignores. The grey
     bar is checked by reproducing it instead - see the screenshot
     comparison further down. */
  out.htmlLayers = (hs.backgroundImage.match(/radial-gradient/g) || []).length;

  // 5. sphere tap highlight (Home only)
  const hero = document.querySelector(".cosmic-hero-wrap");
  out.sphereHighlight = hero ? getComputedStyle(hero).webkitTapHighlightColor : null;
  const circ = hero && hero.querySelector("circle");
  out.sphereChildHighlight = circ ? getComputedStyle(circ).webkitTapHighlightColor : null;

  // 3. the points-fly destination must exist
  out.profileTab = !!document.getElementById("bottomtab-profile");

  /* 4. NO TEXT FIELD UNDER 16px, ANYWHERE.
     iOS Safari zooms the whole page in when it focuses a text field
     computing to under 16px, and does not reliably zoom back out -
     reported from a device as the username screen zooming in with no
     way to zoom out or move. Every field in the app was 15.2px.
     Chromium never does this, so the number is the only thing that
     can catch a regression. Measured on whatever screen this run is
     on, so the matrix as a whole covers every field. */
  const typed = ["text","search","email","number","tel","password"];
  out.smallFields = [...document.querySelectorAll("input, textarea, select")]
    .filter(e => e.tagName !== "INPUT" || typed.includes(e.type))
    .map(e => ({ cls: (e.className || e.tagName.toLowerCase()),
                 px: Math.round(parseFloat(getComputedStyle(e).fontSize) * 10) / 10 }))
    .filter(f => f.px < 16);

  /* 4b. AND A WAY BACK OUT IF IT ZOOMS ANYWAY.
     The floor above is the prevention; this is the cure. Reported
     twice, the second time as "I had to restart the app" - so the app
     needs something that reconciles a scale Safari is holding on to,
     whatever caused it. Two halves, and the check asserts both because
     either alone is useless: the viewport meta must be addressable,
     and the unwind must be a REAL scroll rather than the no-op it was
     (scrollTo to the position you are already at changes nothing, so
     the unwind this all hangs off never ran). */
  out.hasViewportMeta = !!document.getElementById("viewportmeta");
  out.hasZoomReset = typeof resetStuckZoom === "function";
  out.zoomResetIsCheap = (() => {
    /* It must do nothing at all when there is no stuck scale - it runs
       on every focusout in the app. */
    const meta = document.getElementById("viewportmeta");
    if(!meta) return false;
    const before = meta.getAttribute("content");
    try{ resetStuckZoom(); }catch(e){ return false; }
    return meta.getAttribute("content") === before;
  })();
  return out;
})()"""

def rgb(s):
    m = re.findall(r"[\d.]+", s or "")
    return tuple(float(x) for x in m[:3]) if len(m) >= 3 else None

def main():
    # Same --only as the sweep, and for the same reason: the whole matrix
    # is 63 runs of a page that waits on a splash, which is a long time to
    # wait to find out one device is wrong.
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="substring of the device label")
    args = ap.parse_args()
    devices = DEVICES
    if args.only:
        devices = [d for d in devices if args.only.lower() in d[0].lower()]
        if not devices:
            sys.exit(f"no device matches {args.only!r}")
    srv, url = serve()
    fails, checked = [], 0
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(executable_path=CHROME)
            for name, w, h, kind, ins_p, ins_l in devices:
                for orient in ("portrait", "landscape"):
                    vw, vh = (w, h) if orient == "portrait" else (h, w)
                    ins = ins_p if orient == "portrait" else ins_l
                    for mode in ("installed", "browser"):
                        if kind == "desktop" and mode == "installed": continue
                        if kind == "desktop" and orient == "landscape": continue
                        # CHROME_H holds (portrait, landscape) pairs, not a
                        # single number - browser chrome is shorter on a phone
                        # held sideways. Same indexing the sweep uses.
                        chrome = CHROME_H[kind][0 if orient == "portrait" else 1]
                        H = vh if mode == "installed" else vh - chrome
                        I = ins if mode == "installed" else (0, 0, 0, 0)
                        tag = f"{name} {vw}x{H} {mode}"
                        ctx = br.new_context(viewport={"width": vw, "height": H})
                        ctx.add_init_script(SEED)
                        if mode == "installed": ctx.add_init_script(STANDALONE)
                        pg = ctx.new_page(); body = patched(I)
                        pg.route("**/index.html", lambda r, q, b=body: r.fulfill(
                            status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
                        errs = []
                        pg.on("pageerror", lambda e: errs.append(str(e)[:120]))
                        pg.goto(url); pg.wait_for_timeout(1400)

                        # --- REPRODUCTION, not a happy path. The splash bug is
                        # an oversized fixed box during an iOS launch, which
                        # Chromium never produces on its own: measured here the
                        # overlay matches the viewport on frame one, which is
                        # exactly why two earlier "fixes" passed locally and
                        # shipped broken. Force the box oversized and require
                        # the group to stay centred on the VIEWPORT.
                        sp = pg.evaluate("""()=>{
                          const o=document.getElementById('splashscreen'); if(!o) return null;
                          o.style.width=(innerWidth+260)+'px'; o.style.height=(innerHeight+260)+'px';
                          return new Promise(res=>requestAnimationFrame(()=>requestAnimationFrame(()=>{
                            const g=document.getElementById('splash-group');
                            const r=g.getBoundingClientRect();
                            res({dx:Math.round((r.left+r.right)/2-innerWidth/2),
                                 dy:Math.round((r.top+r.bottom)/2-innerHeight/2),
                                 vis:+getComputedStyle(g).opacity>0});})));}""")
                        if sp is not None:
                            if abs(sp["dx"])>2 or abs(sp["dy"])>2:
                                fails.append(f"{tag}: splash off-centre by {sp['dx']},{sp['dy']} in an oversized box")
                            if not sp["vis"]:
                                fails.append(f"{tag}: splash group never became visible")

                        # 2. splash: revealed and centred, before it is torn down
                        sp = pg.evaluate("""()=>{const g=document.getElementById('splash-group');
                          if(!g) return null; const r=g.getBoundingClientRect();
                          return {ready:g.classList.contains('splash-ready'),
                                  op:+getComputedStyle(g).opacity,
                                  dx:Math.round((r.left+r.right)/2-innerWidth/2),
                                  dy:Math.round((r.top+r.bottom)/2-innerHeight/2)};}""")
                        if sp:
                            if not sp["ready"]: fails.append(f"{tag}: splash never revealed")
                            elif abs(sp["dx"]) > 2 or abs(sp["dy"]) > 2:
                                fails.append(f"{tag}: splash off-centre by {sp['dx']},{sp['dy']}")

                        pg.wait_for_timeout(2200)
                        pg.evaluate("()=>{document.documentElement.style.background='';"
                                    "document.getElementById('splashscreen')?.remove();}")
                        pg.evaluate("()=>showHome()"); pg.wait_for_timeout(500)
                        c = pg.evaluate(CHECKS)
                        checked += 1

                        if c["htmlLayers"] < 2:
                            fails.append(f"{tag}: html fallback glow missing ({c['htmlLayers']} layers)")
                        for k in ("sphereHighlight", "sphereChildHighlight"):
                            v = rgb(c[k])
                            if c[k] and v and len(re.findall(r"[\d.]+", c[k])) > 3 and float(
                                    re.findall(r"[\d.]+", c[k])[3]) != 0:
                                fails.append(f"{tag}: {k} is {c[k]}, not transparent")
                        if not c["profileTab"]:
                            fails.append(f"{tag}: #bottomtab-profile missing (points fly target)")
                        for f in (c.get("smallFields") or []):
                            fails.append(
                                f"{tag}: text field {f['cls']} is {f['px']}px "
                                f"- under 16px, iOS will zoom and not zoom back")
                        # 4b. AND A WAY BACK OUT IF IT ZOOMS ANYWAY. The
                        # floor above is prevention; this is the cure,
                        # after "I had to restart the app". Both halves
                        # are asserted because either alone is useless:
                        # the meta has to be addressable, and the reset
                        # has to be inert when nothing is stuck, since it
                        # runs on every focusout in the app.
                        if not c.get("hasViewportMeta"):
                            fails.append(f"{tag}: the viewport meta has no id, "
                                         f"so a stuck zoom cannot be reset")
                        if not c.get("hasZoomReset"):
                            fails.append(f"{tag}: no resetStuckZoom(), "
                                         f"so a stuck zoom has no cure")
                        if not c.get("zoomResetIsCheap"):
                            fails.append(f"{tag}: resetStuckZoom() rewrites the "
                                         f"viewport with no stuck scale")

                        # 9. Home's bottom furniture must not collide. The
                        # daily-question circle and the version label are both
                        # position:fixed off the bottom edge, so they hold no
                        # space in the panel, and Home's primary button was
                        # centred as though the tab bar were the only thing
                        # under it. Measured before the fix: the button
                        # overlapped the "?" by 8x44px on an SE 2nd/3rd gen and
                        # 8x9px on a 13 mini, and cleared it by ONE pixel on a
                        # 14/15/16 - every phone within a rounding error of the
                        # same bug. 12px is the floor because anything under
                        # that reads as a collision even when the rectangles
                        # technically miss.
                        hf = pg.evaluate("""()=>{showHome();
                          const R=s=>{const e=document.querySelector(s);
                            return e && e.getBoundingClientRect();};
                          const btn=R('.panel.home .playbtn'), fab=R('.daily-question-fab'),
                                ver=R('.homeversion'), bar=R('.bottomtabs');
                          if(!btn) return null;
                          const hit=(a,b)=>a&&b&&!(a.right<=b.left||a.left>=b.right||
                                                   a.bottom<=b.top||a.top>=b.bottom);
                          const near=(a,b)=>(a&&b)?Math.round(Math.max(b.top-a.bottom,
                                                                       b.left-a.right)):null;
                          return {btnFab:hit(btn,fab), btnVer:hit(btn,ver),
                                  fabVer:hit(fab,ver), fabBar:hit(fab,bar),
                                  gapFab:near(btn,fab), gapVer:near(btn,ver)};}""")
                        if hf:
                            if hf["btnFab"]: fails.append(f"{tag}: Start Studying overlaps the daily-question circle")
                            if hf["btnVer"]: fails.append(f"{tag}: Start Studying overlaps the version label")
                            if hf["fabVer"]: fails.append(f"{tag}: the daily-question circle overlaps the version label")
                            if hf["fabBar"]: fails.append(f"{tag}: the daily-question circle overlaps the tab bar")
                            for k, what in (("gapFab", "daily-question circle"), ("gapVer", "version label")):
                                if hf[k] is not None and 0 <= hf[k] < 12:
                                    fails.append(f"{tag}: Start Studying clears the {what} by only {hf[k]}px")

                        # 9b. The daily question's "not yet" answer opens BESIDE
                        # the "?" (build 309): "we've been over this before and
                        # it's still not fixed ... needs to be near the button".
                        # It had come back as a top banner, then as a tethered
                        # popup over Start Studying. So: next to the button,
                        # on screen, clear of Start Studying and the tab bar,
                        # and no banner at the top.
                        dl = pg.evaluate("""async ()=>{ store.dailyQuestionDate = dailyPeriodKey(); showHome();
                          await new Promise(r=>setTimeout(r,300));
                          const f=document.querySelector('.daily-question-fab'); if(!f||!f.getBoundingClientRect().width) return null;
                          f.click(); await new Promise(r=>setTimeout(r,350));
                          const t=document.getElementById('daily-lock-tip'); const R=e=>e&&e.getBoundingClientRect();
                          const tr=R(t), fr=R(f), btn=R(document.querySelector('.panel.home .playbtn')), bar=R(document.querySelector('.bottomtabs:not([hidden])'));
                          const hit=(a,b)=>!!(a&&b&&b.width&&!(a.right<=b.left||a.left>=b.right||a.bottom<=b.top||a.top>=b.bottom));
                          const out = {tip:!!t, banner:!!document.querySelector('.daily-alert')};
                          if(tr){ out.gap=Math.round(Math.max(fr.left-tr.right, tr.left-fr.right, fr.top-tr.bottom, tr.top-fr.bottom));
                            out.onScreen=tr.left>=0&&tr.top>=0&&tr.right<=innerWidth&&tr.bottom<=innerHeight;
                            out.btn=hit(tr,btn); out.bar=hit(tr,bar);
                            const q=r=>r?[Math.round(r.left),Math.round(r.top),Math.round(r.right),Math.round(r.bottom)]:null;
                            out.geo={tip:q(tr),fab:q(fr),btn:q(btn),bar:q(bar),cls:t.className}; }
                          t&&t.remove(); store.dailyQuestionDate=null; return out; }""")
                        if dl:
                            if not dl["tip"]: fails.append(f"{tag}: tapping a done daily question opened no bubble by the button")
                            if dl["banner"]: fails.append(f"{tag}: tapping a done daily question put a banner at the top")
                            if dl["tip"]:
                                if not dl["onScreen"]: fails.append(f"{tag}: the daily 'done' bubble runs off the screen")
                                if dl["btn"]: fails.append(f"{tag}: the daily 'done' bubble covers Start Studying")
                                if dl["bar"]: fails.append(f"{tag}: the daily 'done' bubble covers the tab bar")
                                # Within 24px: where two lines will not fit beside the
                                # "?" (a phone browser window, Start Studying just above
                                # the bar) it drops to one line rather than lifting away.
                                if dl["gap"] > 24: fails.append(f"{tag}: the daily 'done' bubble is {dl['gap']}px from the button {dl.get('geo')}")

                        # --- The version label on a phone (build 300): "can be put
                        # on the phone ... the very bottom left corner, with just
                        # the letter v". It lives in the home-indicator strip under
                        # the tab bar, so: where that strip exists (an installed
                        # phone with a bottom inset of 20px or more) it is shown,
                        # in the left corner, wholly below the bar, clear of the
                        # indicator in the middle and on screen; where there is no
                        # strip it stays off, as it was.
                        if vw < 640:
                            # Measured once its entrance has finished (it arrives 6px
                            # low and rises), and by the TEXT, not the button: the
                            # button carries tap padding pulled back out with a
                            # negative margin, and invisible padding past the edge
                            # is not a label running off the screen.
                            vl = pg.evaluate("""async ()=>{ const v=document.querySelector('.homeversion'), b=document.querySelector('.bottomtabs');
                              if(!v||!b) return null;
                              const settle = [v, ...(v.parentElement ? [v.parentElement] : [])].flatMap(e => e.getAnimations ? e.getAnimations() : []).map(a => a.finished.catch(()=>{}));
                              await Promise.race([Promise.all(settle), new Promise(r => setTimeout(r, 2500))]);
                              const s=v.querySelector('.homeversion-short');
                              const r=(s && getComputedStyle(s).display!=='none' ? s : v).getBoundingClientRect(), br=b.getBoundingClientRect();
                              return {shown: r.width>0 && getComputedStyle(v).display!=='none', l:r.left, r:r.right, t:r.top, b:r.bottom,
                                      barBottom:br.bottom, text:(s&&getComputedStyle(s).display!=='none')?s.textContent:v.textContent};}""")
                            strip = mode == "installed" and I[2] >= 20
                            if vl is not None:
                                if strip and not vl["shown"]:
                                    fails.append(f"{tag}: the version label is missing from the bottom-left corner")
                                elif strip:
                                    if vl["t"] < vl["barBottom"] + 2:
                                        fails.append(f"{tag}: the version label touches the tab bar ({round(vl['t'])} vs bar bottom {round(vl['barBottom'])})")
                                    if vl["b"] > H or vl["l"] < 0:
                                        fails.append(f"{tag}: the version label runs off the screen ({round(vl['l'])},{round(vl['b'])} vs H {H})")
                                    if vl["l"] > 64 or vl["r"] > vw / 2 - 70:
                                        fails.append(f"{tag}: the version label is not in the bottom-left corner (left {round(vl['l'])}, right {round(vl['r'])})")
                                    # A phone with a home indicator has rounded display
                                    # corners, ~55-62pt on a current iPhone. The label's
                                    # lowest-left point must sit outside a 62px corner
                                    # circle, or the corner eats the "v" (build 302: "it's
                                    # off the screen and barely visible").
                                    R = 62
                                    up = H - vl["b"]
                                    if up < R:
                                        import math
                                        edge = R - math.sqrt(R * R - (R - up) ** 2)
                                        if vl["l"] < edge + 4:
                                            fails.append(f"{tag}: the version label is inside the rounded display corner (left {round(vl['l'])}, corner edge {round(edge)} at {round(up)}px up)")
                                    if not str(vl["text"]).startswith("v"):
                                        fails.append(f"{tag}: the version label reads {vl['text']!r}, not 'v...'")
                                elif vl["shown"]:
                                    fails.append(f"{tag}: the version label shows on a phone with no room under the tab bar")

                        # --- The grey bar, measured the only way that means
                        # anything: what body::before paints at the bottom edge
                        # against what html falls back to there. body::before is
                        # FIXED, so its bottom-edge colour is the same at every
                        # scroll offset, which makes it the correct target
                        # wherever the page happens to be.
                        #
                        # Two earlier versions of this check were worthless and
                        # both are worth remembering. One asserted
                        # background-attachment:fixed - a property iOS ignores,
                        # so it only proved Chromium honoured it. One compared
                        # the bottom row against "just above the 100lvh
                        # boundary", computed as SH-overflow-6, which clamps to
                        # the TOP ROW whenever the overflow exceeds the screen:
                        # on a 568x260 viewport it compared the bottom of the
                        # screen to the top and called a gradient a seam. A
                        # step-detector fails too - on a long page the boundary
                        # is far above the screen, so the whole visible bottom
                        # is uniformly wrong with no step to find.
                        #
                        # This one is verified against a build that actually has
                        # the bug: 23 levels there, 4 here.
                        pg.evaluate("""()=>{const s=document.createElement('style'); s.id='__hc';
                          s.textContent='body>*{visibility:hidden!important}';
                          document.head.appendChild(s);
                          window.scrollTo(0, document.documentElement.scrollHeight);}""")
                        pg.wait_for_timeout(260)
                        withFixed = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
                        pg.evaluate("""()=>{const s=document.createElement('style'); s.id='__hb';
                          s.textContent='body::before{display:none!important}';
                          document.head.appendChild(s);}""")
                        pg.wait_for_timeout(220)
                        fallback = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
                        SW, SH = withFixed.size
                        worst, worst_at = 0, None
                        for col in (SW // 4, SW // 2, (3 * SW) // 4):
                            for y in range(max(0, SH - 40), SH):
                                d = max(abs(a - b) for a, b in
                                        zip(withFixed.getpixel((col, y)), fallback.getpixel((col, y))))
                                if d > worst: worst, worst_at = d, (col, y)
                        if worst > 6:
                            fails.append(f"{tag}: GREY BAR - fallback is {worst} levels off the "
                                         f"fixed layer at the bottom edge, at {worst_at}")
                        pg.evaluate("()=>{document.getElementById('__hc')?.remove();document.getElementById('__hb')?.remove();}")

                        # 7. back-to-top must never sit under the tab bar
                        bt = pg.evaluate("""()=>{showAppearance();
                          const b=document.querySelector('.backtotop');
                          if(b){b.hidden=false;b.classList.add('show');}
                          const bar=document.querySelector('.bottomtabs');
                          if(!b||!bar||bar.hidden) return null;
                          const B=b.getBoundingClientRect(), A=bar.getBoundingClientRect();
                          const overlap=!(B.right<A.left||B.left>A.right||B.bottom<A.top||B.top>A.bottom);
                          return {overlap, w:Math.round(B.width),
                                  bottomGap:Math.round(innerHeight-B.bottom),
                                  offRight:Math.round(innerWidth-B.right),
                                  offBottom:B.bottom>innerHeight};}""")
                        if bt:
                            if bt["overlap"]: fails.append(f"{tag}: back-to-top overlaps the tab bar")
                            if bt["offBottom"]: fails.append(f"{tag}: back-to-top below the fold")
                            if bt["offRight"] < 0: fails.append(f"{tag}: back-to-top off the right edge")

                        # 8. daily "already done": the bubble beside the "?" since
                        # build 309 (checked in 9b). The top banner is only the
                        # FALLBACK for when the "?" is not on screen, and that
                        # fallback must still be on screen and clear of the bar.
                        dq = pg.evaluate("""async ()=>{showHome();
                          store.dailyQuestionDate = dailyPeriodKey(); startDailyQuestion();
                          const tip=document.getElementById('daily-lock-tip');
                          if(tip){ tip.remove(); store.dailyQuestionDate=null; return {bubble:true}; }
                          const a=document.getElementById('dailyalert');
                          // .daily-alert enters from translateY(-8px) and only
                          // gets .show on the next frame, so measuring it
                          // synchronously reads the animation's FIRST frame and
                          // calls a healthy banner off-screen by 2px. Ask for the
                          // settled position, not the starting one.
                          const t=document.querySelector('.toast');
                          const bar=document.querySelector('.bottomtabs');
                          if(!a) return {banner:false, toast:!!t};
                          /* Wait for the entrance to SETTLE, not for a fixed
                             delay. .daily-alert enters from translateY(-8px)
                             over .22s; a flat 320ms read it mid-transition on
                             a 2560px display and called a healthy banner 1px
                             off-screen. Poll the computed transform instead. */
                          for(let i=0;i<40;i++){
                            const cs = getComputedStyle(a);
                            if(a.classList.contains('show') && cs.opacity === '1' &&
                               (cs.transform === 'none' || /matrix\(1, 0, 0, 1, 0, 0\)/.test(cs.transform))) break;
                            await new Promise(r=>setTimeout(r,25));
                          }
                          if(!a.classList.contains('show')) return {banner:true, toast:!!t, never:true};
                          const r=a.getBoundingClientRect();
                          const A=bar&&!bar.hidden?bar.getBoundingClientRect():null;
                          return {banner:true, toast:!!t, top:Math.round(r.top),
                                  onScreen:r.top>=0&&r.bottom<=innerHeight,
                                  clearsBar:A?Math.round(A.top-r.bottom):999};}""")
                        if dq.get("bubble"): pass
                        elif not dq["banner"]: fails.append(f"{tag}: daily 'already done' shows neither the bubble nor the fallback banner")
                        elif dq["toast"]: fails.append(f"{tag}: daily 'already done' still raises a toast")
                        elif dq.get("never"): fails.append(f"{tag}: daily banner never animated in")
                        elif not dq["onScreen"]: fails.append(f"{tag}: daily banner off-screen (top {dq['top']})")
                        elif dq["clearsBar"] < 0: fails.append(f"{tag}: daily banner behind the tab bar")

                        # 4. Advanced settings: dark, and a real tap target
                        adv = pg.evaluate("""()=>{showAppearance();
                          const b=document.querySelector('.more-toggle.adv-toggle');
                          if(!b) return null; const cs=getComputedStyle(b);
                          return {bg:cs.backgroundColor, h:Math.round(b.getBoundingClientRect().height)};}""")
                        if not adv: fails.append(f"{tag}: Advanced settings button missing")
                        else:
                            v = rgb(adv["bg"])
                            if v and sum(v) / 3 > 60: fails.append(f"{tag}: Advanced settings still light {adv['bg']}")
                            if adv["h"] < 44: fails.append(f"{tag}: Advanced settings {adv['h']}px tall")

                        # 9/10. release history has no back link; tooltip names the daily question
                        # 11. RECENT TEST REVIEW: a row says which units it
                        # covered, and looks tappable. The affordance used to be
                        # a @media (hover:hover) colour, which no phone or
                        # tablet has, and the name was entry.label - "3 units
                        # - Drill", naming none of them. Measured rather than
                        # read, because two separate things here are only
                        # visible at a particular width: the chevron was
                        # stranded on a line of its own on the ONE row long
                        # enough to wrap (flex wraps on an item's base size,
                        # not its shrunk size), and the meta line ran 44-52px
                        # past the panel on a 320px phone.
                        # Build 311 rebuilt the rows (.thx-row): a score ring,
                        # the units, a mode chip and the stats, with the time
                        # and chevron in a column of their own on the right,
                        # centred on the row. Same questions as before, asked
                        # of that shape: every row names its units and its
                        # mode, the chevron is at the far end and level with
                        # the row, nothing overflows, nothing scrolls sideways.
                        tr = pg.evaluate("""()=>{showTestReviewList();
                          const rows=[...document.querySelectorAll('.thx-row')];
                          const doc=document.documentElement;
                          return {pageOverflow:Math.round(doc.scrollWidth-doc.clientWidth),
                            n:rows.length,
                            rows:rows.map(r=>{
                              const n=r.querySelector('.thx-row-name'), c=r.querySelector('.thx-row-chev'),
                                    m=r.querySelector('.thx-row-meta'), chip=r.querySelector('.thx-chip'),
                                    rr=r.getBoundingClientRect();
                              const cs=getComputedStyle(r);
                              const edge = rr.right-(parseFloat(cs.borderRightWidth)||0)-(parseFloat(cs.paddingRight)||0);
                              const cb=c?c.getBoundingClientRect():null;
                              return {name:n?n.textContent:null, chev:!!c, mode:chip?chip.textContent:null,
                                level: cb ? Math.round(Math.abs((cb.top+cb.bottom)/2-(rr.top+rr.bottom)/2)) : null,
                                chevRight: cb ? Math.round(edge-cb.right) : null,
                                metaBelow:(n&&m)?Math.round(m.getBoundingClientRect().top-n.getBoundingClientRect().bottom):null,
                                overflow:Math.round(r.scrollWidth-r.clientWidth)};})};}""")
                        if not tr["n"]:
                            fails.append(f"{tag}: test history is empty - the seed has no history")
                        if tr["pageOverflow"] > 0:
                            fails.append(f"{tag}: test history scrolls the page sideways by {tr['pageOverflow']}px")
                        for i, r in enumerate(tr["rows"]):
                            if not r["chev"]:
                                fails.append(f"{tag}: test history row {i} has no chevron - nothing says it opens")
                            elif r["level"] is not None and r["level"] > 4:
                                fails.append(f"{tag}: test history row {i} chevron is {r['level']}px off the row's centre line")
                            elif r["chevRight"] is not None and r["chevRight"] > 2:
                                fails.append(f"{tag}: test history row {i} chevron sits {r['chevRight']}px in from the row's content edge")
                            if r["overflow"] > 0:
                                fails.append(f"{tag}: test history row {i} overflows by {r['overflow']}px")
                            if r["metaBelow"] is not None and r["metaBelow"] < 0:
                                fails.append(f"{tag}: test history row {i} meta line is not below the name")
                            nm = r["name"] or ""
                            if not nm or "undefined" in nm:
                                fails.append(f"{tag}: test history row {i} name is {nm!r}")
                            if not r["mode"]:
                                fails.append(f"{tag}: test history row {i} does not say its mode")

                        misc = pg.evaluate("""()=>{showReleaseHistory();
                          const back=!!document.querySelector('.panel .back-link');
                          return {back};}""")
                        if misc["back"]: fails.append(f"{tag}: Release History still has a back link")

                        real = [e for e in errs if not any(k in e.lower() for k in
                                ("firebase", "firestore", "gstatic", "failed to fetch", "net::"))]
                        if real: fails.append(f"{tag}: JS error {real[0]}")
                        ctx.close()
            br.close()
    finally:
        srv.shutdown()
    print(f"\n{checked} device/orientation/mode combinations checked")
    if fails:
        print(f"\n{len(fails)} FAILURES")
        for f in fails: print("  *", f)
        sys.exit(1)
    print("all fixes verified on every combination")

main()
