#!/usr/bin/env python3
"""Record the whole NEW first-run path of 384.23 as one mp4 at iPhone 17 Pro Max size (440x956), with a caption on every screen.

  1. an iPhone in a Safari tab with no account: the install page, what Open Share menu does (the share menu is SIMULATED here: Chromium has
     none, so navigator.share is stubbed and a mock sheet is drawn, labelled as such), the guide, and the page an in-app browser (Instagram) sees;
  2. the Home Screen icon (installed, a fresh storage as the icon has): Get Started, Welcome, the sign-up, Nova's introduction, the tips, Home.

No sound. Playwright's own recorder (webm, real time) joined with title cards by ffmpeg.

  python3 tools/record-b384-flow.py OUT.mp4 [--against OLD/index.html]
"""
import json, os, subprocess, sys, tempfile, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import b384_flow_lib as L
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

OUT = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "b384-flow.mp4"
SRC = L.load_src(sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else None)
W, H = 440, 956
FF = "/usr/bin/ffmpeg" if os.path.exists("/usr/bin/ffmpeg") else "ffmpeg"
TMP = tempfile.mkdtemp(prefix="b384flow-")

# a caption strip (top, over the status bar) and a ring where a finger lands; both exist only in the recording
OVERLAY = """
addEventListener('DOMContentLoaded', function(){
  var s = document.createElement('style');
  s.textContent = '#__cap{position:fixed;left:10px;right:10px;top:8px;z-index:99999;pointer-events:none;padding:7px 12px;border-radius:14px;background:rgba(0,0,0,.72);'
   + 'color:#fff;font:600 13px/1.3 ui-sans-serif,system-ui,sans-serif;text-align:center;border:1px solid rgba(255,255,255,.18)}'
   + '#__cap b{color:#F5B54D}'
   + '.__tap{position:fixed;width:46px;height:46px;margin:-23px 0 0 -23px;border-radius:50%;border:3px solid #F5B54D;background:rgba(245,181,77,.25);z-index:99999;pointer-events:none;'
   + 'animation:__tap .55s ease-out forwards}@keyframes __tap{from{transform:scale(.4);opacity:1}to{transform:scale(1.25);opacity:0}}';
  document.head.appendChild(s);
  var c = document.createElement('div'); c.id = '__cap'; c.hidden = true; document.body.appendChild(c);
  window.__cap = function(t){ c.innerHTML = t || ''; c.hidden = !t; };
  addEventListener('pointerdown', function(e){ var d = document.createElement('div'); d.className = '__tap'; d.style.left = e.clientX + 'px'; d.style.top = e.clientY + 'px'; document.body.appendChild(d); setTimeout(function(){ d.remove(); }, 650); }, true);
});"""
# the share menu, simulated: navigator.share draws a sheet with Add to Home Screen in it and resolves when that row is tapped
SHARE_SIM = """(()=>{ window.__shares = [];
  navigator.share = function(d){ window.__shares.push(d); return new Promise(function(res, rej){
    var o = document.createElement('div'); o.id = '__sharesim'; o.style.cssText = 'position:fixed;inset:0;z-index:99990;background:rgba(0,0,0,.45);display:flex;align-items:flex-end;font-family:ui-sans-serif,system-ui,sans-serif';
    o.innerHTML = '<div style="width:100%;background:#2a2a2e;border-radius:22px 22px 0 0;padding:14px 16px 34px;color:#fff;box-sizing:border-box">'
      + '<div style="text-align:center;font:600 11px/1.3 system-ui;color:#F5B54D;margin-bottom:8px">SIMULATED: on a phone this is the system share menu</div>'
      + '<div style="display:flex;gap:12px;align-items:center;padding:8px 4px 14px"><div style="width:44px;height:44px;border-radius:10px;background:#111;display:flex;align-items:center;justify-content:center;font-weight:800">N</div><div><div style="font-weight:600">Nova</div><div style="font-size:12px;opacity:.7">' + (d && d.url || '') + '</div></div></div>'
      + '<div style="background:#38383c;border-radius:14px;overflow:hidden">'
      + '<div style="padding:15px 16px;border-bottom:1px solid #4a4a4e">Copy</div><div style="padding:15px 16px;border-bottom:1px solid #4a4a4e">Add to Reading List</div>'
      + '<div id="__a2hsrow" style="padding:15px 16px;background:#5a4a2a;font-weight:700">Add to Home Screen &nbsp;+</div></div></div>';
    document.body.appendChild(o);
    window.__shareDone = function(){ o.remove(); res(); };
  }); }; })();"""
COUNT = []   # (label, seconds) of every segment, for the log


def slow(pg, ms): pg.wait_for_timeout(ms)


def cap(pg, text):
    try: pg.evaluate("t => window.__cap && window.__cap(t)", text)
    except Exception: pass


def tap(pg, sel, ms=1400):
    el = pg.locator(sel).first
    el.scroll_into_view_if_needed()
    b = el.bounding_box()
    pg.mouse.click(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
    slow(pg, ms)


def title_card(path, lines, secs=2.6):
    im = Image.new("RGB", (W, H), (10, 10, 12)); d = ImageDraw.Draw(im)
    try: f1 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26); f2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 17)
    except Exception: f1 = f2 = ImageFont.load_default()
    y = H // 2 - 70
    for i, t in enumerate(lines):
        f = f1 if i == 0 else f2
        w = d.textlength(t, font=f); d.text(((W - w) / 2, y), t, font=f, fill=(255, 255, 255) if i == 0 else (190, 190, 200)); y += 46 if i == 0 else 30
    png = path + ".png"; im.save(png)
    subprocess.run([FF, "-y", "-loglevel", "error", "-loop", "1", "-t", str(secs), "-i", png, "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "20", path], check=True)
    return path


def segment(br, name, url, ua, *, installed, extra=(), fn):
    vd = os.path.join(TMP, name); os.makedirs(vd, exist_ok=True)
    ctx = br.new_context(viewport={"width": W, "height": H}, device_scale_factor=1, user_agent=L.UA.get(ua, ua), has_touch=True, is_mobile=False,
                         record_video_dir=vd, record_video_size={"width": W, "height": H})
    ctx.add_init_script("Object.defineProperty(navigator,'maxTouchPoints',{get:()=>5,configurable:true});")
    if installed: ctx.add_init_script(L.STANDALONE)
    ctx.add_init_script(L.FAKE_FIREBASE); ctx.add_init_script(OVERLAY)
    for sc in extra: ctx.add_init_script(sc)
    pg = ctx.new_page()
    body = L.patched(SRC, (47, 0, 34, 0))
    pg.route("**/index.html", lambda r, q, b=body: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8", "cache-control": "no-store"}, body=b))
    t0 = time.time()
    pg.goto(url); slow(pg, 1500)
    pg.evaluate("()=>{ const s=document.getElementById('splashscreen'); if(s) s.remove(); }"); slow(pg, 600)
    res = fn(pg)
    vid = pg.video; ctx.close()
    webm = vid.path(); mp4 = os.path.join(TMP, name + ".mp4")
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", webm, "-vf", "fps=30,scale=%d:%d,format=yuv420p" % (W, H), "-c:v", "libx264", "-crf", "21", mp4], check=True)
    COUNT.append((name, round(time.time() - t0, 1)))
    return mp4, res


def safari_new(pg):
    cap(pg, "<b>1</b> iPhone, Safari, no account yet: the first page is only about the Home Screen")
    slow(pg, 3800)
    cap(pg, "<b>2</b> Tap <b>Open Share menu</b>. It opens the phone's own share menu")
    slow(pg, 1500); tap(pg, ".if-go", 1500)
    cap(pg, "<b>3</b> In the menu, tap <b>Add to Home Screen</b> (the menu here is simulated)")
    slow(pg, 2600)
    box = pg.locator("#__a2hsrow").bounding_box(); pg.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2); slow(pg, 400)
    pg.evaluate("()=>window.__shareDone && window.__shareDone()"); slow(pg, 700)
    cap(pg, "<b>4</b> The page says what is next: open Nova from the new icon, not from here")
    slow(pg, 3600)
    cap(pg, "<b>5</b> <b>Show me how</b> opens the step-by-step guide and the video")
    tap(pg, ".if-guide", 4500)
    pg.evaluate("()=>{ const e=document.querySelector('#a2hs-sheet .a2hs-close'); if(e) e.click(); }"); slow(pg, 800)
    cap(pg, "<b>6</b> <b>I can't add it</b> carries on in the browser, as before (and is remembered)")
    slow(pg, 3000)


def inapp(pg):
    cap(pg, "An in-app browser (Instagram, Facebook, TikTok...) cannot add to the Home Screen: it asks for Safari first")
    slow(pg, 4500)
    cap(pg, "<b>Open in Safari</b> hands the page to Safari; the link can also be copied")
    slow(pg, 3500)


def icon_new(pg):
    steps = [0]
    def n(text):
        steps[0] += 1; cap(pg, "<b>Screen %d</b> %s" % (steps[0], text))
    n("The icon opens: Get Started (once, here, in the app)")
    slow(pg, 3200)
    pg.evaluate("()=>{ const s=document.querySelector('.gs-scroll'); if(s) s.scrollTo({top:s.scrollHeight, behavior:'smooth'}); }"); slow(pg, 2600)
    tap(pg, ".gs-go", 1800)
    n("Welcome: Sign in, or I'm new here"); slow(pg, 1800); tap(pg, ".welcome-new", 1500)
    n("New to Nova? (a guard against a second account)"); slow(pg, 1800); tap(pg, ".signupcheck-go", 1500)
    n("Choose the class"); slow(pg, 1500); tap(pg, ".classselect-panel .class-card.is-academy", 900); tap(pg, ".classselect-panel #nextbtn", 1500)
    n("Confirm the class")
    try: pg.wait_for_selector("#classenroll-confirm .classenroll-yes", timeout=4000)
    except Exception: pass
    slow(pg, 1500); tap(pg, "#classenroll-confirm .classenroll-yes", 800)
    n("Generating the profile")
    pg.wait_for_selector("#genprofile-overlay", state="detached", timeout=30000)
    pg.wait_for_selector("#nova-intro", state="attached", timeout=15000)
    n("Nova introduces himself: 7 short boxes, a name, a partner and the sync code")
    seen = set(); asked = set(); t1 = time.time()
    while time.time() - t1 < 200:
        st = L.novastate(pg)
        if not st:
            if pg.evaluate("()=>!!document.getElementById('savecode-card')"): slow(pg, 200); continue
            if "end" in asked or time.time() - t1 > 10: break
            slow(pg, 200); continue
        if st["card"] and "card" not in asked:
            asked.add("card"); cap(pg, "<b>The sync code</b>: saved for you; copy or tick, then Continue. It is kept in Settings"); slow(pg, 2800)
            tap(pg, "#savecode-card .savecode-ack", 1200); tap(pg, "#savecode-card .savecode-continue", 900); cap(pg, "<b>Screen %d</b> Nova again" % steps[0]); continue
        if st["asking"] and not st["typing"] and st["name"] and "name" not in asked:
            asked.add("name"); cap(pg, "<b>Nova asks your name</b>"); slow(pg, 1200)
            tap(pg, ".nt-ask-input", 300); pg.keyboard.type("J.Smith", delay=120); slow(pg, 700)
            tap(pg, ".nt-ask-name .nt-ask-go", 1500); cap(pg, "<b>Screen %d</b> Nova again" % steps[0]); continue
        if st["asking"] and not st["typing"] and st["char"] and "char" not in asked:
            asked.add("char"); cap(pg, "<b>Pick your partner</b>"); slow(pg, 1500)
            tap(pg, ".nt-ask-char .avatarchar-option", 900); tap(pg, ".nt-ask-char .nt-ask-go", 1500); cap(pg, "<b>Screen %d</b> Nova again" % steps[0]); continue
        if st["typing"]: slow(pg, 250); continue
        if not st["asking"]:
            if st["i"] not in seen:
                seen.add(st["i"]); slow(pg, 1700)    # long enough to read the box
            if st["i"] == st["count"] - 1: asked.add("end"); tap(pg, "#nova-intro .nt-go", 900)
            else:
                pg.mouse.click(W / 2, H * 0.45); slow(pg, 500)
        slow(pg, 150)
    n("The tips: four, then one more (Start Studying)")
    for rnd in range(2):
        up = False
        for _ in range(70):
            if pg.evaluate("()=>!!document.getElementById('tour-tooltip')"): up = True; break
            slow(pg, 250)
        if not up: break
        for _ in range(8):
            if not pg.evaluate("()=>!!document.getElementById('tour-next')"): break
            slow(pg, 2300); tap(pg, "#tour-next", 700)
    n("Home: signed up, in the icon, nothing carried over")
    slow(pg, 4500)


def main():
    srv, url = L.serve()
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(executable_path=L.CHROME)
            a, _ = segment(br, "safari", url, "iphone-safari", installed=False, extra=(SHARE_SIM,), fn=safari_new)
            b, _ = segment(br, "inapp", url, "iphone-instagram", installed=False, fn=inapp)
            c, _ = segment(br, "icon", url, "iphone-safari", installed=True, fn=icon_new)
            br.close()
    finally:
        srv.shutdown()
    t1 = title_card(os.path.join(TMP, "t1.mp4"), ["1. In Safari", "no account yet: add Nova to the Home Screen first"])
    t2 = title_card(os.path.join(TMP, "t2.mp4"), ["2. If the link opens inside another app", "Instagram, Facebook, TikTok and so on"])
    t3 = title_card(os.path.join(TMP, "t3.mp4"), ["3. From the Home Screen icon", "start-up, sign-up, introduction and tips, once"])
    parts = [t1, a, t2, b, t3, c]
    cmd = [FF, "-y", "-loglevel", "error"]
    for p in parts: cmd += ["-i", p]
    fc = "".join("[%d:v]fps=30,scale=%d:%d,setsar=1,format=yuv420p[v%d];" % (i, W, H, i) for i in range(len(parts)))
    fc += "".join("[v%d]" % i for i in range(len(parts))) + "concat=n=%d:v=1:a=0[o]" % len(parts)
    cmd += ["-filter_complex", fc, "-map", "[o]", "-c:v", "libx264", "-crf", "21", "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT]
    subprocess.run(cmd, check=True)
    print("wrote", OUT, COUNT)


main()
