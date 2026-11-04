#!/usr/bin/env python3
"""Build 384: Add to Home Screen at the end of sign-up (showHomeScreenSheet).

Madison: "let's ensure that the sign up process gives a thing for the adding app to your iPhone/samsung homescreen as
a popup ... then let it do the walkthrough. For when people select Apple. Have it show them this video ... blur that
out ... Maybe add some pointers like the add button. A pointer for "open as web app" ensuring it's on."

Walked as a person would, in a BROWSER TAB (not installed), with an in-memory Firestore (the CDN is blocked here):
Get Started -> Welcome -> I'm new here -> the class -> GENERATING PROFILE -> Nova (name, partner, the save-code card)
-> the tips -> Home. Codes are made up by the app; names are made up.

  iphone     - iPhone 17 Pro Max (440x956, an iOS Safari user agent): the sheet comes up on Home only after the last tip
               (never over Nova, the save-code card or a tip), once the +100 XP has gone, with the iPhone choice
               already picked; one choice of three; 44px+ buttons, nothing wider than the screen, the sheet inside it.
               The clip: a poster that loads, a source that plays (its clock moves); each pointer comes on inside its
               own window on the clip's clock and is the only one on, its ring inside the clip's box at the place
               it declares, its label inside the box, the step it belongs to lit; none before the first; the ring
               over Open as Web App sits on the switch's green and the one over Add on the button's blue (pixels read
               off the clip at those times). While the walkthrough is up the address carries the account's code
               (the icon opens signed in), and Not now takes it off again. Not now closes it; the enrolled banner
               waited for it; a reload (the next launch) does not bring it back.
  samsung    - Galaxy S24 (412x915, Samsung Internet's user agent): Android preselected, Samsung Internet's card first and
               marked; the clip is not downloaded; the browser's own Install appears when the browser offers it
               (beforeinstallprompt) and runs its prompt.
  desktop    - a laptop (1536x864, Chrome on Windows): Computer preselected; Not now; not back after a reload.
  installed  - the same sign-up in the installed app (iPhone, navigator.standalone): no sheet, nothing owed.
  settings   - an existing account, Settings > Share & Install > Add to Home Screen: the same sheet, with Done; it does not
               mark the sign-up's showing.
  clip       - the shipped file: H.264, yuv420p, no sound, ~30fps, 440-660px wide, under 2.5MB, its index at the front
               (faststart), a poster of the same size; in every frame the share sheet's row of people is in, that band
               holds a fraction of the detail of the row of apps right under it (a blur, not the photos and names),
               and the Messages back-link under the clock likewise against the clock beside it.

  python3 tools/check-b384-a2hs.py
  python3 tools/check-b384-a2hs.py --against /path/to/old-index.html
  ONLY=iphone,clip python3 tools/check-b384-a2hs.py
  A2_SHOTS=/some/folder python3 tools/check-b384-a2hs.py      (a picture of each sheet)
"""
import functools, http.server, io, json, os, re, socket, subprocess, sys, threading, time
from playwright.sync_api import sync_playwright

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_PATH = sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else os.path.join(ROOT, "index.html")
SRC = io.open(SRC_PATH, encoding="utf-8").read()
BUILD = re.search(r'const APP_BUILD = "([^"]+)"', SRC).group(1)
ONLY = set(x for x in os.environ.get("ONLY", "").split(",") if x)
SHOTS = os.environ.get("A2_SHOTS")
CLIP = os.environ.get("A2_CLIP") or os.path.join(ROOT, "landing", "a2hs-iphone.mp4")
POSTER = os.path.join(ROOT, "landing", "a2hs-iphone.jpg")
INSET_RE = re.compile(r"env\(safe-area-inset-(top|bottom|left|right)(?:\s*,[^()]*)?\)")
UA = {
    "iphone": "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1",
    "samsung": "Mozilla/5.0 (Linux; Android 14; SM-S921B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/26.0 Chrome/122.0.0.0 Mobile Safari/537.36",
    "desktop": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
}
DEVICES = {"iphone": (440, 956, (62, 0, 34, 0)), "samsung": (412, 915, (32, 0, 16, 0)), "desktop": (1536, 864, (0, 0, 0, 0))}
WANT_DEV = {"iphone": "apple", "samsung": "android", "desktop": "computer"}

STANDALONE = """Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});
(function(){ const mm = window.matchMedia.bind(window); window.matchMedia = q => /display-mode:\\s*standalone/.test(q)
 ? {matches:true, media:q, addListener(){}, removeListener(){}, addEventListener(){}, removeEventListener(){}, onchange:null, dispatchEvent(){return false;}} : mm(q); })();"""
# The cloud (as check-b383-signup's): documents kept in the tab's sessionStorage so a reload sees them.
FAKE = r"""(()=>{ if(location.protocol !== 'http:') return;
  let C = null; try{ C = JSON.parse(sessionStorage.getItem('__fakecloud') || 'null'); }catch(e){}
  if(!C) C = JSON.parse(JSON.stringify(window.__cloudSeed || {}));
  ['progress','leaderboard','vrooms'].forEach(k => { C[k] = C[k] || {}; });
  window.__cloud = C;
  const keep = () => { try{ sessionStorage.setItem('__fakecloud', JSON.stringify(C)); }catch(e){} };
  const subs = {};
  const clone = v => v == null ? v : JSON.parse(JSON.stringify(v));
  const snap = (c, id) => { const d = (C[c] || {})[id]; return { id, exists: d !== undefined, data: () => clone(d), metadata: { fromCache: false, hasPendingWrites: false } }; };
  const fire = (c, id) => (subs[c + '/' + id] || []).forEach(f => setTimeout(() => f(snap(c, id)), 15));
  const doc = (c, id) => ({ id,
    get: () => Promise.resolve(snap(c, id)),
    set: (v, o) => { C[c] = C[c] || {}; C[c][id] = (o && o.merge) ? Object.assign({}, C[c][id] || {}, clone(v)) : clone(v); keep(); fire(c, id); return Promise.resolve(); },
    update: v => { C[c] = C[c] || {}; C[c][id] = Object.assign({}, C[c][id] || {}, clone(v)); keep(); fire(c, id); return Promise.resolve(); },
    delete: () => { if(C[c]) delete C[c][id]; keep(); fire(c, id); return Promise.resolve(); },
    onSnapshot: function(){ const a = [...arguments]; const next = a.find(x => typeof x === 'function'); const k = c + '/' + id; (subs[k] = subs[k] || []).push(next); setTimeout(() => next(snap(c, id)), 30); return () => { subs[k] = (subs[k] || []).filter(f => f !== next); }; },
    collection: n => coll(c + '/' + id + '/' + n) });
  const coll = c => { const q = { doc: id => doc(c, id), where(){ return q; }, orderBy(){ return q; }, limit(){ return q; },
    get: () => Promise.resolve({ empty: true, docs: [], forEach(){}, size: 0 }),
    onSnapshot: function(){ const a = [...arguments]; const next = a.find(x => typeof x === 'function'); setTimeout(() => next({ empty: true, docs: [], size: 0, forEach(){}, metadata: { fromCache: false }, docChanges: () => [] }), 30); return () => {}; } }; return q; };
  const db = { collection: coll, batch: () => ({ set(){}, update(){}, delete(){}, commit: () => Promise.resolve() }) };
  const fs = () => db; fs.FieldValue = { delete: () => null, serverTimestamp: () => Date.now(), arrayUnion: (...x) => x, increment: n => n }; fs.FieldPath = function(){};
  window.firebase = { apps: [], initializeApp(){ this.apps.push({}); }, firestore: fs };
})()"""
# When the sheet came up, and what else was on screen then; when the tips last went; whether the enrolled banner was
# ever up together with the sheet.
WATCH = r"""(()=>{ const a = window.__a2 = { tourOn: false };
  const look = () => {
    const has = id => !!document.getElementById(id);
    const s = has('a2hs-sheet'), t = has('tour-overlay') || has('tour-tooltip');
    if(t) a.tourSeen = true;
    if(a.tourOn && !t) a.tourGoneAt = performance.now();
    a.tourOn = t;
    if(s && !a.sheetAt){ const sc = document.querySelector('#stage [data-screen]');
      a.sheetAt = performance.now();
      a.atShow = { nova: !!document.querySelector('.nova-talk'), tour: t, card: has('savecode-card'), bonus: has('welcomebonus-banner'),
        enrolled: has('enrolled-banner'), screen: sc ? sc.dataset.screen : '' }; }
    if(s && has('enrolled-banner')) a.enrolledUnder = true;
    if(!s && a.sheetAt && !a.sheetGoneAt) a.sheetGoneAt = performance.now();
    if(has('enrolled-banner') && !a.enrolledAt) a.enrolledAt = performance.now();
  };
  const go = () => { new MutationObserver(look).observe(document.body, { childList: true, subtree: true }); look(); };
  if(document.body) go(); else document.addEventListener('DOMContentLoaded', go);
})()"""

s = socket.socket(); s.bind(("127.0.0.1", 0)); PORT = s.getsockname()[1]; s.close()
class Q(http.server.SimpleHTTPRequestHandler):
    """a static server that answers byte ranges, as GitHub Pages does: a <video> seeks only where it can ask for one"""
    def log_message(self, *a): pass
    def send_head(self):
        rng = self.headers.get("Range")
        path = self.translate_path(self.path)
        if not rng or not os.path.isfile(path):
            return super().send_head()
        m = re.match(r"bytes=(\d*)-(\d*)$", rng.strip())
        size = os.path.getsize(path)
        if not m or (not m.group(1) and not m.group(2)):
            return super().send_head()
        if m.group(1):
            a = int(m.group(1)); b = int(m.group(2)) if m.group(2) else size - 1
        else:
            a = max(0, size - int(m.group(2))); b = size - 1
        b = min(b, size - 1)
        if a > b:
            self.send_response(416); self.send_header("Content-Range", "bytes */%d" % size); self.end_headers(); return None
        f = open(path, "rb"); f.seek(a)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Range", "bytes %d-%d/%d" % (a, b, size))
        self.send_header("Content-Length", str(b - a + 1))
        self.end_headers()
        return io.BytesIO(f.read(b - a + 1))
    def end_headers(self):
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()
http.server.ThreadingHTTPServer.handle_error = lambda *a: None
threading.Thread(target=http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Q, directory=ROOT)).serve_forever, daemon=True).start()
URL = "http://127.0.0.1:%d/index.html" % PORT

fails = []
def chk(name, cond, info=""):
    print(("  PASS " if cond else "  FAIL ") + name + ("" if cond else "  -> " + str(info)[:600]), flush=True)
    if not cond: fails.append(name)
def want(sec): return not ONLY or sec in ONLY

def body(ins):
    v = {"top": "%dpx" % ins[0], "right": "%dpx" % ins[1], "bottom": "%dpx" % ins[2], "left": "%dpx" % ins[3]}
    return INSET_RE.sub(lambda m: v[m.group(1)], SRC)

def open_page(br, dev, installed=False, init="", seed=None, wait=3500):
    w, h, ins = DEVICES[dev]
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=1, has_touch=(dev != "desktop"), user_agent=UA[dev])
    ctx.add_init_script("window.__cloudSeed = %s;" % json.dumps(seed or {}))
    ctx.add_init_script(FAKE)
    ctx.add_init_script(WATCH)
    if installed: ctx.add_init_script(STANDALONE)
    if init:
        ctx.add_init_script("(()=>{ try{ if(location.protocol !== 'http:' || sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); "
                            + init + " }catch(e){} })()")
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)[:240]))
    pg.on("console", lambda m: errs.append("console: " + m.text[:240]) if m.type == "error"
          and "Failed to load resource" not in m.text and "net::" not in m.text else None)
    b = body(ins)
    pg.route("**/index.html*", lambda r, q, b=b: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.route("**/version.json*", lambda r, q: r.fulfill(status=200, headers={"content-type": "application/json"},
             body=json.dumps({"build": BUILD, "force": False, "frameId": ""})))
    pg.goto(URL); pg.wait_for_timeout(wait)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    pg.errs = errs; pg.dev = dev
    return ctx, pg

def relaunch(pg, wait=3500):
    pg.goto("about:blank"); pg.wait_for_timeout(200)
    pg.goto(URL); pg.wait_for_timeout(wait)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    pg.wait_for_timeout(600)

SCREEN = """()=>{ const s=document.querySelector('#stage [data-screen]'); return s ? s.dataset.screen : ''; }"""
def screen(pg): return pg.evaluate(SCREEN)

def nova(pg):
    return pg.evaluate("""()=>{ const n=document.getElementById('nova-intro'); if(!n||!n.__nova) return null;
      return { asking:n.__nova.asking, typing:n.__nova.typing, i:n.__nova.index, count:n.__nova.count,
        name: !!n.querySelector('.nt-ask-name input'), char: !!n.querySelector('.nt-ask-char .avatarchar-option'),
        card: !!document.getElementById('savecode-card') }; }""")

def sign_up(pg, name):
    """a new account, as a person makes one; returns when the last tip has been tapped"""
    if screen(pg) == "getstarted":
        pg.evaluate("()=>{ const s=document.querySelector('.gs-scroll'); s && s.scrollTo(0, s.scrollHeight); }"); pg.wait_for_timeout(1400)
        pg.click(".gs-go"); pg.wait_for_timeout(1000)
    pg.click(".welcome-new"); pg.wait_for_timeout(700)
    pg.click(".signupcheck-go"); pg.wait_for_timeout(600)
    pg.click(".classselect-panel .class-card.is-academy"); pg.wait_for_timeout(300)
    pg.click(".classselect-panel #nextbtn")
    try: pg.wait_for_selector("#classenroll-confirm .classenroll-yes", timeout=4000); pg.wait_for_timeout(400); pg.click("#classenroll-confirm .classenroll-yes")
    except Exception: pass   # builds before 384's enroll confirm go straight on
    try: pg.wait_for_selector("#genprofile-overlay", state="attached", timeout=5000)
    except Exception: pass
    pg.wait_for_selector("#genprofile-overlay", state="detached", timeout=30000)
    pg.wait_for_selector("#nova-intro", state="attached", timeout=15000)
    seen = set(); t1 = time.time(); early = []
    while time.time() - t1 < 300:
        if pg.evaluate("()=>!!document.getElementById('a2hs-sheet')"): early.append("during Nova")
        st = nova(pg)
        if not st:
            if pg.evaluate("()=>!!document.getElementById('savecode-card')"): pass
            elif "end" in seen or time.time() - t1 > 8: break
            pg.wait_for_timeout(150); continue
        if st["card"] and "card" not in seen:
            seen.add("card"); pg.wait_for_timeout(300)
            pg.click("#savecode-card .savecode-ack"); pg.wait_for_timeout(150)
            pg.click("#savecode-card .savecode-continue"); pg.wait_for_timeout(500)
            continue
        if st["asking"] and not st["typing"] and st["name"] and "name" not in seen:
            seen.add("name")
            pg.click(".nt-ask-input"); pg.keyboard.type(name); pg.keyboard.press("Enter")
            for _ in range(60):
                if not pg.evaluate("()=>!!document.querySelector('#nova-intro .nt-ask-name')"): break
                pg.wait_for_timeout(100)
            continue
        if st["asking"] and not st["typing"] and st["char"] and "char" not in seen:
            seen.add("char")
            pg.click(".nt-ask-char .avatarchar-option"); pg.wait_for_timeout(300)
            pg.click(".nt-ask-char .nt-ask-go"); pg.wait_for_timeout(1200)
            continue
        if st["typing"]:
            # a tap while he types finishes the line, as a person taps through
            pg.evaluate("()=>document.getElementById('nova-intro').__nova.advance()")
        elif not st["asking"]:
            if st["i"] == st["count"] - 1:
                seen.add("end"); pg.evaluate("()=>document.querySelector('#nova-intro .nt-go')?.click()")
            else: pg.evaluate("()=>document.getElementById('nova-intro').__nova.advance()")
        pg.wait_for_timeout(120)
    tip = False
    for _ in range(80):
        if pg.evaluate("()=>!!document.getElementById('tour-tooltip')"): tip = True; break
        if nova(pg) and "end" in seen:   # his last line was still being written; tap again
            pg.evaluate("()=>document.querySelector('#nova-intro .nt-go')?.click()")
        pg.wait_for_timeout(250)
    if not tip: print("  INFO the tips did not start: Nova %s, screen %s, seen %s" % (nova(pg), screen(pg), sorted(seen)))
    tips = 0
    for _ in range(20):
        if pg.evaluate("()=>!!document.getElementById('a2hs-sheet')"): early.append("during the tips")
        if not pg.evaluate("()=>!!document.getElementById('tour-next')"): break
        pg.evaluate("()=>document.getElementById('tour-next').click()"); tips += 1; pg.wait_for_timeout(350)
    return {"nova": {"name", "char", "card"} <= seen, "tips": tip and tips > 0, "early": early}

def wait_sheet(pg, secs=25):
    t0 = time.time()
    while time.time() - t0 < secs:
        if pg.evaluate("()=>{ const o=document.getElementById('a2hs-sheet'); return !!o && o.classList.contains('invite-overlay-show'); }"):
            return round(time.time() - t0, 2)
        pg.wait_for_timeout(200)
    return None

LAYOUT = r"""()=>{ const o=document.getElementById('a2hs-sheet'); if(!o) return null;
  const vis=e=>{ const r=e.getBoundingClientRect(), c=getComputedStyle(e); return r.width>0 && r.height>0 && c.visibility!=='hidden' && c.display!=='none' && !e.closest('[hidden]'); };
  const sh=o.querySelector('.a2hs-sheet').getBoundingClientRect();
  const btns=[...o.querySelectorAll('button')].filter(vis).filter(b=>!b.closest('.a2hs-phone'));
  const small=btns.filter(b=>{ const r=b.getBoundingClientRect(); return r.height<43.5 || r.width<43.5; }).map(b=>b.className+' '+Math.round(b.getBoundingClientRect().width)+'x'+Math.round(b.getBoundingClientRect().height));
  const radios=[...o.querySelectorAll('[role=radio]')];
  const panels=[...o.querySelectorAll('.a2hs-panel')];
  const de=document.documentElement;
  return { sideways: de.scrollWidth-de.clientWidth, small,
    inside: sh.left>=-0.5 && sh.top>=-0.5 && sh.right<=innerWidth+0.5 && sh.bottom<=innerHeight+0.5,
    radios: radios.length, checked: radios.filter(r=>r.getAttribute('aria-checked')==='true').map(r=>r.dataset.dev),
    shown: panels.filter(p=>!p.hidden).map(p=>p.dataset.dev), owner: /madison/i.test(o.innerText),
    intro: (o.querySelector('.a2hs-intro')||{}).textContent || '', close: !!o.querySelector('.a2hs-foot button'),
    from: o.dataset.from, src: (o.querySelector('video')||{}).getAttribute ? o.querySelector('video').getAttribute('src') : null }; }"""

def sheet_layout(pg, label):
    r = pg.evaluate(LAYOUT)
    if SHOTS and r:
        os.makedirs(SHOTS, exist_ok=True); pg.screenshot(path=os.path.join(SHOTS, "%s-%s.png" % (pg.dev, re.sub(r"[^a-z0-9]+", "-", label.lower()))))
    chk("%s %s: the sheet is inside the screen, nothing sideways, every button 44px+, one choice of three, no owner's name" % (pg.dev, label),
        bool(r) and r["inside"] and r["sideways"] <= 0 and not r["small"] and r["radios"] == 3 and len(r["checked"]) == 1 and not r["owner"] and r["close"], r)
    return r

def close_sheet(pg):
    pg.click("#a2hs-sheet .a2hs-foot button"); pg.wait_for_timeout(600)
    return pg.evaluate("()=>!document.getElementById('a2hs-sheet')")

def errs_ok(pg, where):
    chk("%s %s: no page or console errors" % (pg.dev, where), not pg.errs, pg.errs[:3])

def a2(pg): return pg.evaluate("()=>window.__a2")

def check_signup_point(pg, walk, label):
    chk("%s the sign-up ran: Nova asked the name and the partner, the save-code card was answered, the tips ran" % label, walk["nova"] and walk["tips"], walk)
    chk("%s nothing of the sheet while Nova talked or a tip was up" % label, not walk["early"], walk["early"])
    t = wait_sheet(pg)
    w = a2(pg)
    chk("%s the sheet comes up on Home after the last tip (%ss after it)" % (label, t),
        t is not None and w.get("sheetAt") and w.get("tourGoneAt") and w["sheetAt"] > w["tourGoneAt"]
        and w["atShow"]["screen"] == "home" and not w["atShow"]["nova"] and not w["atShow"]["tour"] and not w["atShow"]["card"], w)
    chk("%s ...once the +100 XP has gone, and with the enrolled banner held for after it" % label,
        bool(w.get("atShow")) and not w["atShow"]["bonus"] and not w["atShow"]["enrolled"], w)
    return t

print("check-b384-a2hs against", SRC_PATH, "(build %s)" % BUILD)
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME, args=["--autoplay-policy=no-user-gesture-required"])

    # ------------------------------------------------------------------ iphone
    if want("iphone"):
        print("\niPhone, a browser tab, a new account")
        ctx, pg = open_page(br, "iphone")
        walk = sign_up(pg, "Casey Rivera")
        t = check_signup_point(pg, walk, "iphone")
        if t is not None:
            r = sheet_layout(pg, "sheet")
            chk("iphone the iPhone choice is already picked, and only its panel is shown", r["checked"] == ["apple"] and r["shown"] == ["apple"], r)
            chk("iphone the sheet says what it is (an intro under the title)", len(r["intro"].split()) >= 12, r["intro"])
            code = pg.evaluate("()=>syncCode")
            h = pg.evaluate("location.hash")
            chk("iphone while the walkthrough is up the address carries the account's code (an icon added now opens signed in)", bool(code) and code in h, h)
            # the clip
            v = None
            for _ in range(40):
                v = pg.evaluate("""()=>{ const v=document.querySelector('#a2hs-sheet video'); return v && { t:v.currentTime, rs:v.readyState, paused:v.paused,
                    w:v.videoWidth, h:v.videoHeight, poster:v.poster, src:v.currentSrc, muted:v.muted, loop:v.loop, inline:v.playsInline }; }""")
                if v and v["t"] > 1.0: break
                pg.wait_for_timeout(150)
            chk("iphone the clip loads and plays on its own, muted, inline, looping (its clock at %.2fs)" % (v["t"] if v else -1),
                bool(v) and v["rs"] >= 2 and v["t"] > 1.0 and not v["paused"] and v["muted"] and v["loop"] and v["inline"] and v["src"].endswith(".mp4"), v)
            poster = pg.evaluate("""async src=>{ const i=new Image(); i.src=src; try{ await i.decode(); }catch(e){ return null; } return [i.naturalWidth, i.naturalHeight]; }""", v["poster"] if v else "")
            chk("iphone the clip has a poster, and it loads (%s)" % (poster,), bool(v and v["poster"]) and bool(poster) and poster[0] > 0, (v, poster))
            box = pg.evaluate("()=>{ const f=document.querySelector('#a2hs-sheet .a2hs-phone').getBoundingClientRect(); return [f.left,f.top,f.width,f.height]; }")
            chk("iphone the clip's frame has the clip's own shape (%.3f against %.3f)" % (box[2] / box[3], v["w"] / max(1, v["h"])), abs(box[2] / box[3] - v["w"] / max(1, v["h"])) < .01, (box, v))
            # each pointer, inside its own window on the clip's clock
            pts = pg.evaluate("()=>[...document.querySelectorAll('#a2hs-sheet .a2hs-pt')].map(p=>({from:+p.dataset.from, to:+p.dataset.to, step:+p.dataset.step, x:parseFloat(p.style.left)/100, y:parseFloat(p.style.top)/100}))")
            chk("iphone there are pointers over the clip (%d), in order on its clock" % len(pts), len(pts) >= 5 and all(pts[i]["from"] < pts[i]["to"] <= pts[i + 1]["from"] + 1e-6 for i in range(len(pts) - 1)), pts)
            pg.evaluate("()=>document.querySelector('#a2hs-sheet video').pause()")
            SEEK = """async t=>{ const v=document.querySelector('#a2hs-sheet video'); v.pause();
                await new Promise(r=>{ const f=()=>{ v.removeEventListener('seeked', f); r(); }; v.addEventListener('seeked', f); v.currentTime=t; setTimeout(r, 1500); });
                await new Promise(r=>setTimeout(r, 450)); return v.currentTime; }"""
            STATE = """()=>{ const o=document.getElementById('a2hs-sheet'); const f=o.querySelector('.a2hs-phone').getBoundingClientRect();
                const on=[...o.querySelectorAll('.a2hs-pt')].map((p,i)=>({i, on:p.classList.contains('is-on'), op:+getComputedStyle(p).opacity}));
                const lit=[...o.querySelectorAll('.a2hs-apple .a2hs-step')].map((s,i)=>s.classList.contains('is-now')?i:-1).filter(i=>i>=0);
                const ring=[...o.querySelectorAll('.a2hs-pt')].map(p=>{ const r=p.querySelector('.a2hs-pt-ring').getBoundingClientRect(), l=p.querySelector('.a2hs-pt-label').getBoundingClientRect();
                  return { cx:(r.left+r.width/2-f.left)/f.width, cy:(r.top+r.height/2-f.top)/f.height, inF: r.left+r.width/2>=f.left && r.left+r.width/2<=f.right && r.top+r.height/2>=f.top && r.top+r.height/2<=f.bottom,
                    labelIn: l.left>=f.left-1 && l.right<=f.right+1 && l.top>=f.top-1 && l.bottom<=f.bottom+1 }; });
                const nw=o.querySelector('.a2hs-now'); let cap=null;
                if(nw){ const r=nw.getBoundingClientRect(), litEl=o.querySelector('.a2hs-apple .a2hs-step.is-now .a2hs-step-main');
                  cap={ shown:getComputedStyle(nw).display!=='none' && r.height>0, gap:r.top-f.bottom, inView:r.bottom<=innerHeight && r.top>=0,
                    head:(nw.querySelector('.a2hs-now-n')||{}).textContent||'', text:nw.textContent.replace((nw.querySelector('.a2hs-now-n')||{}).textContent||'','').trim(),
                    litText: litEl ? litEl.textContent.trim() : null }; }
                return { on, lit, ring, cap, steps:o.querySelectorAll('.a2hs-apple .a2hs-step').length }; }"""
            PIX = """([x,y])=>{ const v=document.querySelector('#a2hs-sheet video'); const c=document.createElement('canvas'); c.width=v.videoWidth; c.height=v.videoHeight;
                const g=c.getContext('2d'); g.drawImage(v,0,0); const d=g.getImageData(Math.round(x*c.width)-3, Math.round(y*c.height)-3, 7, 7).data;
                let r=0,gg=0,b=0,n=0; for(let i=0;i<d.length;i+=4){ r+=d[i]; gg+=d[i+1]; b+=d[i+2]; n++; } return [r/n, gg/n, b/n]; }"""
            # across the ring (the ring's width on the clip's own pixels): how much of it is a switch's green
            GREEN = """([x,y])=>{ const v=document.querySelector('#a2hs-sheet video'); const f=document.querySelector('#a2hs-sheet .a2hs-phone').getBoundingClientRect();
                const ring=document.querySelector('#a2hs-sheet .a2hs-pt-ring').offsetWidth; const half=Math.round(ring/2*v.videoWidth/f.width);
                const c=document.createElement('canvas'); c.width=v.videoWidth; c.height=v.videoHeight; const g=c.getContext('2d'); g.drawImage(v,0,0);
                const d=g.getImageData(Math.round(x*c.width)-half, Math.round(y*c.height)-2, half*2, 5).data;
                let n=0, green=0; for(let i=0;i<d.length;i+=4){ n++; if(d[i+1]>d[i]+40 && d[i+1]>d[i+2]+30) green++; } return green/n; }"""
            pg.evaluate(SEEK, 0.05)
            st = pg.evaluate(STATE)
            chk("iphone before the first pointer's time none is on", not any(p["on"] for p in st["on"]), st["on"])
            for i, p in enumerate(pts):
                mid = (p["from"] + min(p["to"], p["from"] + 3)) / 2
                pg.evaluate(SEEK, mid)
                for _ in range(8):   # its fade (.18s) may be late to start on a loaded machine
                    st = pg.evaluate(STATE)
                    if st["on"][i]["op"] > .9 and all(q["op"] < .1 for q in st["on"] if q["i"] != i): break
                    pg.wait_for_timeout(300)
                onlist = [q["i"] for q in st["on"] if q["on"]]
                rg = st["ring"][i]
                chk("iphone pointer %d at %.2fs: it alone is on and showing, its ring inside the clip at the place it declares (%.3f,%.3f), its label inside, step %d lit"
                    % (i + 1, mid, rg["cx"], rg["cy"], p["step"] + 1),
                    onlist == [i] and st["on"][i]["op"] > .9 and rg["inF"] and abs(rg["cx"] - p["x"]) < .01 and abs(rg["cy"] - p["y"]) < .01 and rg["labelIn"] and st["lit"] == [p["step"]], (st, p))
                # build 384: on a phone the list is below the fold, so the step is said right under the clip as well
                cp = st.get("cap") or {}
                head = re.findall(r"\d+", cp.get("head", ""))
                chk("iphone ...and right under the clip, in view, the same step said: '%s %s'" % (cp.get("head"), cp.get("text")),
                    cp.get("shown") and 0 <= cp.get("gap", -1) <= 24 and cp.get("inView") and head == [str(p["step"] + 1), str(st["steps"])] and cp.get("text") == cp.get("litText"), cp)
            # the ring on the switch sits on its green, the one on Add on its blue: read off the clip
            sw = [i for i, p in enumerate(pts) if p["step"] == 3]
            ad = [i for i, p in enumerate(pts) if p["step"] == 4]
            if sw and ad:
                p = pts[sw[0]]; pg.evaluate(SEEK, (p["from"] + p["to"]) / 2); c = pg.evaluate(GREEN, [p["x"], p["y"]])
                pg.evaluate(SEEK, 0.05); c0 = pg.evaluate(GREEN, [p["x"], p["y"]])
                chk("iphone the Open as Web App pointer sits on the switch, on: %.0f%% of the line across its ring is the switch's green (%.0f%% there at the clip's start)" % (c * 100, c0 * 100),
                    c > .15 and c0 < .02, (c, c0))
                p = pts[ad[0]]; pg.evaluate(SEEK, min(p["to"], p["from"] + 1.5)); c = pg.evaluate(PIX, [p["x"], p["y"]])
                chk("iphone the Add pointer sits on the Add button: blue under it (%s)" % [round(x) for x in c], c[2] > c[0] + 60 and c[2] > c[1] + 20, c)
            pg.evaluate("()=>document.querySelector('#a2hs-sheet video').play()")
            pg.wait_for_timeout(300)
            enrolled_before = pg.evaluate("()=>!!document.getElementById('enrolled-banner')")
            chk("iphone the enrolled banner waits while the sheet is up", not enrolled_before and not a2(pg).get("enrolledUnder"), a2(pg))
            gone = close_sheet(pg)
            st = pg.evaluate("()=>({ key: localStorage.getItem('class26e.a2hs'), hash: location.hash })")
            chk("iphone Not now closes it, takes the code off the address, and the device remembers the showing", gone and "k=" not in st["hash"] and bool(re.match(r"^\d+$", st["key"] or "")), st)
            for _ in range(30):
                if a2(pg).get("enrolledAt"): break
                pg.wait_for_timeout(250)
            chk("iphone ...and then the enrolled banner comes", bool(a2(pg).get("enrolledAt")) and a2(pg)["enrolledAt"] > (a2(pg).get("sheetGoneAt") or 1e18), a2(pg))
            relaunch(pg)
            pg.wait_for_timeout(7000)
            chk("iphone opened again: Home, signed in, and no sheet (%s)" % screen(pg), screen(pg) == "home" and pg.evaluate("()=>!document.getElementById('a2hs-sheet') && !!syncCode"), screen(pg))
        errs_ok(pg, "sign-up and sheet")
        ctx.close()

    # ------------------------------------------------------------------ samsung
    if want("samsung"):
        print("\nSamsung Galaxy, Samsung Internet, a new account")
        ctx, pg = open_page(br, "samsung")
        walk = sign_up(pg, "Jordan Ellis")
        t = check_signup_point(pg, walk, "samsung")
        if t is not None:
            r = sheet_layout(pg, "sheet")
            chk("samsung Android is already picked, and only its panel is shown", r["checked"] == ["android"] and r["shown"] == ["android"], r)
            first = pg.evaluate("()=>{ const c=document.querySelector('#a2hs-sheet .a2hs-android .a2hs-browser'); return c ? { yours: !!c.querySelector('.a2hs-yours'), art: !!c.querySelector('.a2hs-browser-art svg'), steps: c.querySelectorAll('.a2hs-step').length, name: c.querySelector('.a2hs-browser-name').firstChild.textContent } : null; }")
            marks = pg.evaluate("()=>document.querySelectorAll('#a2hs-sheet .a2hs-yours').length")
            chk("samsung this browser's card comes first, marked, with its drawing and its steps (%s)" % first, bool(first) and first["yours"] and first["art"] and first["steps"] >= 3 and marks == 1 and "Samsung" in first["name"], (first, marks))
            chk("samsung the iPhone clip is not downloaded on Android", not r["src"], r["src"])
            inst = pg.evaluate("()=>{ const b=document.querySelector('#a2hs-sheet .a2hs-android .a2hs-install-btn'); return !!b && !b.hidden && !b.closest('[hidden]'); }")
            chk("samsung no Install button when the browser has not offered one", not inst, inst)
            pg.evaluate("""()=>{ window.__prompted = 0; const e = new Event('beforeinstallprompt'); e.prompt = () => { window.__prompted++; return Promise.resolve(); };
                e.userChoice = Promise.resolve({ outcome: 'accepted' }); window.dispatchEvent(e); }""")
            pg.wait_for_timeout(300)
            inst = pg.evaluate("()=>{ const b=document.querySelector('#a2hs-sheet .a2hs-android .a2hs-install-btn'); const r=b && b.getBoundingClientRect(); return !!b && !b.hidden && !b.closest('[hidden]') && r.height>=43.5; }")
            chk("samsung the browser offers to install: a one-tap Install button appears", inst, inst)
            if inst:
                pg.click("#a2hs-sheet .a2hs-android .a2hs-install-btn"); pg.wait_for_timeout(400)
                chk("samsung ...and it runs the browser's own prompt", pg.evaluate("window.__prompted") == 1, pg.evaluate("window.__prompted"))
            gone = close_sheet(pg)
            chk("samsung Not now closes it", gone, gone)
            relaunch(pg); pg.wait_for_timeout(7000)
            chk("samsung opened again: no sheet", screen(pg) == "home" and pg.evaluate("()=>!document.getElementById('a2hs-sheet')"), screen(pg))
        errs_ok(pg, "sign-up and sheet")
        ctx.close()

    # ------------------------------------------------------------------ desktop
    if want("desktop"):
        print("\na laptop, Chrome, a new account")
        ctx, pg = open_page(br, "desktop")
        walk = sign_up(pg, "Morgan Hale")
        t = check_signup_point(pg, walk, "desktop")
        if t is not None:
            r = sheet_layout(pg, "sheet")
            chk("desktop Computer is already picked, and only its panel is shown", r["checked"] == ["computer"] and r["shown"] == ["computer"], r)
            pg.click("#a2hs-sheet .a2hs-seg-apple"); pg.wait_for_timeout(1200)
            v = pg.evaluate("()=>{ const v=document.querySelector('#a2hs-sheet video'); return { t:v.currentTime, rs:v.readyState, shown: !v.closest('[hidden]') }; }")
            chk("desktop choosing iPhone shows the clip, and it plays", v["shown"] and v["rs"] >= 2 and v["t"] > 0.2, v)
            cap = pg.evaluate("()=>{ const n=document.querySelector('#a2hs-sheet .a2hs-now'); return n ? getComputedStyle(n).display : 'none'; }")
            chk("desktop the steps sit beside the clip, so no step is repeated under it (%s)" % cap, cap == "none", cap)
            sheet_layout(pg, "sheet, iPhone chosen")
            pg.click("#a2hs-sheet .a2hs-seg-computer"); pg.wait_for_timeout(300)
            chk("desktop choosing Computer again pauses the clip", pg.evaluate("()=>document.querySelector('#a2hs-sheet video').paused"), "playing")
            gone = close_sheet(pg)
            chk("desktop Not now closes it", gone, gone)
            relaunch(pg); pg.wait_for_timeout(7000)
            chk("desktop opened again: no sheet", screen(pg) == "home" and pg.evaluate("()=>!document.getElementById('a2hs-sheet')"), screen(pg))
        errs_ok(pg, "sign-up and sheet")
        ctx.close()

    # ------------------------------------------------------------------ installed
    if want("installed"):
        print("\niPhone, the installed app, a new account")
        ctx, pg = open_page(br, "iphone", installed=True)
        walk = sign_up(pg, "Riley Brooks")
        chk("installed the sign-up ran to the tips", walk["nova"] and walk["tips"], walk)
        t = wait_sheet(pg, 15)
        st = pg.evaluate("()=>({ key: localStorage.getItem('class26e.a2hs'), screen: (document.querySelector('#stage [data-screen]')||{dataset:{}}).dataset.screen, enrolled: !!document.getElementById('enrolled-banner') || !!(window.__a2||{}).enrolledAt })")
        chk("installed no Add to Home Screen sheet in the installed app, nothing owed, and the enrolled banner still comes", t is None and not st["key"] and st["screen"] == "home" and st["enrolled"], (t, st))
        errs_ok(pg, "sign-up")
        ctx.close()

    # ------------------------------------------------------------------ settings
    if want("settings"):
        print("\nSettings > Share & Install > Add to Home Screen, an existing account")
        CODE = "TEST-3841"
        acct = {"firstName": "Gate Tester", "avatarChar": "ghost", "onboardingComplete": True, "publicId": "gatetest3841", "leaderboardOptIn": False,
                "tourRev": 999, "novaMet": 99, "lastModified": 1790500000000, "novaHeard": {"@recap": 99991231}, "savedCodeSaved": True,
                "seenMainMenuTour": True, "seenProfileTour": True, "seenModeSelectTour": True, "seenUnitSelectTour": True, "seenRankingsTour": True, "seenAppearanceTour": True,
                "lifetime": {"points": 1200, "answered": 300, "correct": 250}}
        seen = ("['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.getstarted','class26e.daily.seen'].forEach(k=>localStorage.setItem(k,'1'));"
                "localStorage.setItem('class26e.frame.ok','go-live-1');")
        ctx, pg = open_page(br, "iphone", init=seen, seed={"progress": {CODE: acct}})
        # Welcome > Sign in > the code > Continue > Sync This Device > Home
        pg.click(".welcome-signin"); pg.wait_for_timeout(500)
        pg.fill(".synccode-entry-panel input:not([type=checkbox])", CODE)
        pg.click(".synccode-entry-panel #nextbtn"); pg.wait_for_timeout(800)
        pg.click(".synccode-confirm .next.playbtn")
        pg.wait_for_selector("#genprofile-overlay", state="detached", timeout=15000)
        pg.wait_for_timeout(2500)
        chk("settings an existing account, signed in with its code, is on Home with no sheet of its own", screen(pg) == "home" and pg.evaluate("()=>!document.getElementById('a2hs-sheet')"), screen(pg))
        pg.evaluate("()=>showAppearance({ page: 'share' })"); pg.wait_for_timeout(700)
        pg.evaluate("()=>{ const b=[...document.querySelectorAll('#stage button')].find(x=>/Add to Home Screen/.test(x.textContent)); b && b.click(); }"); pg.wait_for_timeout(900)
        r = pg.evaluate(LAYOUT)
        chk("settings the row opens the same sheet, for an existing account (from Settings, iPhone picked)", bool(r) and r["from"] == "settings" and r["checked"] == ["apple"], r)
        if r:
            sheet_layout(pg, "sheet from Settings")
            gone = close_sheet(pg)
            st = pg.evaluate("()=>({ key: localStorage.getItem('class26e.a2hs'), hash: location.hash, screen: (document.querySelector('#stage [data-screen]')||{dataset:{}}).dataset.screen })")
            chk("settings closing it leaves Settings as it was, the address clean, and does not mark the sign-up's showing", gone and not st["key"] and "k=" not in st["hash"], st)
        errs_ok(pg, "Settings")
        ctx.close()
    br.close()

# ------------------------------------------------------------------ clip
if want("clip"):
    print("\nthe shipped clip")
    def probe(path):
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height,pix_fmt,avg_frame_rate,nb_frames",
                              "-show_entries", "format=duration,size", "-of", "json", path], capture_output=True, text=True).stdout
        return json.loads(out or "{}")
    ok_files = os.path.exists(CLIP) and os.path.exists(POSTER)
    chk("the clip and its poster are in landing/", ok_files, (CLIP, POSTER))
    if ok_files:
        p = probe(CLIP)
        vs = [s for s in p.get("streams", []) if s.get("codec_type") == "video"]
        aus = [s for s in p.get("streams", []) if s.get("codec_type") == "audio"]
        v = vs[0] if vs else {}
        num, den = (v.get("avg_frame_rate", "0/1").split("/") + ["1"])[:2]
        fps = float(num) / max(1.0, float(den))
        size = os.path.getsize(CLIP)
        chk("H.264, yuv420p, no sound, ~30fps, 440-660px wide, under 2.5MB (%s %s %dx%d %.1ffps %d bytes, %s audio)"
            % (v.get("codec_name"), v.get("pix_fmt"), v.get("width", 0), v.get("height", 0), fps, size, len(aus)),
            v.get("codec_name") == "h264" and v.get("pix_fmt") == "yuv420p" and not aus and 29 <= fps <= 31 and 440 <= v.get("width", 0) <= 660 and size < 2.5e6, p)
        head = open(CLIP, "rb").read(4096)
        chk("faststart: the index (moov) comes before the frames (mdat)", head.find(b"moov") != -1 and (head.find(b"mdat") == -1 or head.find(b"moov") < head.find(b"mdat")), head[:64])
        from PIL import Image
        pw_, ph_ = Image.open(POSTER).size
        chk("the poster is the clip's size (%dx%d)" % (pw_, ph_), (pw_, ph_) == (v.get("width"), v.get("height")), (pw_, ph_))
        # the blur: per frame, the band the row of people is in (frame ranges -> its top and bottom), as cut
        BANDS = ("132-132:770:920;133-133:730:900;134-134:690:860;135-135:650:840;136-136:658:828;137-139:656:826;140-141:658:828;142-204:660:830;"
                 "205-205:622:792;206-206:532:702;207-207:446:616;208-208:378:548;209-209:330:500;210-210:296:466;211-211:280:450;212-212:260:430;"
                 "213-213:256:426;214-214:248:418;215-215:244:414;216-216:242:412;217-303:240:410")
        want_n = {}
        for part in BANDS.split(";"):
            rng, y0, y1 = part.split(":"); a, b = rng.split("-")
            for n in range(int(a), int(b) + 1): want_n[n] = (int(y0), int(y1))
        import numpy as np
        W, H = v["width"], v["height"]
        proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", CLIP, "-f", "rawvideo", "-pix_fmt", "gray", "-"], stdout=subprocess.PIPE)
        def detail(a):
            """mean |high-pass|: what a face or a letter leaves, and a blur does not"""
            a = a.astype(np.float32)
            lo = (a[:-2, 1:-1] + a[2:, 1:-1] + a[1:-1, :-2] + a[1:-1, 2:]) / 4.0
            return float(np.abs(a[1:-1, 1:-1] - lo).mean())
        worst_row, worst_msg, n, rows_seen = 0.0, 0.0, 0, 0
        worst_at = None
        while True:
            buf = proc.stdout.read(W * H)
            if len(buf) < W * H: break
            f = np.frombuffer(buf, np.uint8).reshape(H, W)
            # the Messages back-link under the clock, against the clock beside it (every frame)
            msg = detail(f[46:66, 8:100]); clock = detail(f[16:42, 30:110])
            worst_msg = max(worst_msg, msg / max(clock, 1e-3))
            if n in want_n:
                y0, y1 = want_n[n]
                band = detail(f[y0 + 8:y1 - 8, 4:W - 4])
                ref = detail(f[min(H - 2, y1 + 6):min(H, y1 + 130), 4:W - 4])
                rows_seen += 1
                ratio = band / max(ref, 1e-3)
                if ratio > worst_row: worst_row, worst_at = ratio, n
            n += 1
        proc.wait()
        chk("the share sheet's row of people is blurred in all %d frames it is in: at most %.2f of the detail of the apps row under it (frame %s)"
            % (rows_seen, worst_row, worst_at), rows_seen == len(want_n) and worst_row < .25, (rows_seen, len(want_n), worst_row, worst_at))
        chk("the Messages back-link under the clock is blurred in all %d frames: at most %.2f of the clock's detail" % (n, worst_msg), n > 300 and worst_msg < .3, worst_msg)

print("\n%d failed" % len(fails) if fails else "\nALL PASS")
for f in fails: print("  FAILED: " + f)
sys.exit(1 if fails else 0)
