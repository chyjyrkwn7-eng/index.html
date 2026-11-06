#!/usr/bin/env python3
"""Build 384: the stuck zoom, the tab bar, Sign out's buttons, the sync code's copy, Save it on a laptop.

Madison (on the live 383): "when I first logged into nova signing in, the screen was zoomed in" / "The bottom tab is
glitching right now, it's showing up in the middle of the screen of review and the unit selection screen and stuff ...
when paused the box is glitched and is showing at the top" / "The copy button to how the friend button has, the sync code
needs that same kinda button as well." / "When you sign out the buttons overlap as well." / "Why did my laptop do a weird
thing when I selected save code by the way?"

Devices are their own browsers: an iPhone 17 Pro Max (440x956) installed and in a Safari tab (440x797), the same phone at
Safari's 85% page zoom (518x1125 installed, 518x938 in a tab, the screen still 440x956 - how the app sees the zoom), an
iPhone SE (375x667), an iPad Pro 11 (834x1194, iPadOS's Mac user agent with touch points) and a Windows laptop (1536x864,
Chrome's user agent, a mouse, no touch). Both classes (the Police Academy and Fire Code) where a screen is in both.

  fields  - every text field the app can show is 16px+ ON THE GLASS (its computed size x its CSS zoom x the page zoom) at 440
            and at 518, in both classes: the sign-in code and username fields (Welcome), the units and Review searches, the
            Leaderboard's, Manage friends', the name (Account), Enter a code (Sync), the bug report, the Virtual Room's, Nova's
            ask field and the tab bar's search. And the sign-in walk itself at 518: Welcome -> Sign in -> the code field.
  zoom    - a held page scale. (a) A real one (Chromium's pinch, CDP): with no field focused, a screen change and a pageshow
            each ask for it back (the viewport clamped to maximum-scale=1, then lifted to exactly what it was); with a field
            focused, neither pageshow, coming back to the app nor the keyboard's resize does; at scale 1 nothing touches the
            viewport. (b) iOS's answer simulated (a visual viewport held at 1.6 that comes back to 1 when the viewport is
            clamped, as Safari's does): unwound at boot, on pageshow, on coming back to the app; and the sign-in walk with
            the code field's zoom held: Continue -> Sync This Device -> Home comes back to scale 1, the viewport as authored.
  place   - the tab bar at the bottom (or hidden where it should be) on the unit screen, Review's list and through Pause, every
            frame for 1.2s after each transition, no transformed/filtered/contained ancestor of the bar or Pause; Pause's
            card on the middle of what is showing, at scale 1 and under a held (real) zoom.
  copy    - Settings > Sync: a copy button beside the code, Manage friends' own (same class, size, colour, glyph), 44px+,
            centred on the code's well and clear of it, both classes; a tap copies the code as shown (never "__ifc"), turns
            to the tick, says so, and does not show or hide the code.
  signout - Sign out's sheet: no two buttons touch or overlap (a 6px gap at least), each 44px+, its buttons inside the
            screen, at every device above, both classes, and with a label long enough to wrap.
  save    - Save it on a laptop (the save-code card, Settings' Save it row, Sign out's Save my code): copies the code, never
            calls navigator.share (Windows' share dialog), says it copied; on an iPhone the share sheet is still used.

  python3 tools/check-b384-glitches.py [section ...]
  python3 tools/check-b384-glitches.py --against 34765be     (a git revision or a folder holding another build's index.html)
Checks marked [fix] are what this build changed and FAIL on 34765be (and on the live 42bbffa); [guard] checks hold on both.
"""
import functools, http.server, io, json, os, re, shutil, socket, subprocess, sys, tempfile, threading, time
from playwright.sync_api import sync_playwright

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[1:]
ROOT = REPO
if "--against" in args:
    i = args.index("--against"); target = args[i + 1]; del args[i:i + 2]
    if os.path.isdir(target):
        ROOT = os.path.abspath(target)
    else:
        ROOT = tempfile.mkdtemp(prefix="glitch384-")
        tar = subprocess.run(["git", "-C", REPO, "archive", "--format=tar", target, "index.html", "ifc", "launch", "version.json", "share"],
                             check=True, capture_output=True).stdout
        subprocess.run(["tar", "-x", "-C", ROOT], input=tar, check=True)
SECTIONS = args or ["fields", "zoom", "place", "copy", "signout", "save"]
SRC = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
BUILD = re.search(r'const APP_BUILD = "([^"]+)"', SRC).group(1)
print("build", BUILD, "from", ROOT)
INSET_RE = re.compile(r"env\(safe-area-inset-(top|bottom|left|right)(?:\s*,[^()]*)?\)")
UA_IPHONE = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1"
UA_IPAD = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Safari/605.1.15"
UA_WIN = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
# name: (w, h, screen w, screen h, insets, user agent, touch, installed)
DEV = {
    "promax":     (440, 956, 440, 956, (62, 0, 34, 0), UA_IPHONE, True, True),
    "promax-tab": (440, 797, 440, 956, (0, 0, 0, 0), UA_IPHONE, True, False),
    "pm85":       (518, 1125, 440, 956, (73, 0, 40, 0), UA_IPHONE, True, True),
    "pm85-tab":   (518, 938, 440, 956, (0, 0, 0, 0), UA_IPHONE, True, False),
    "se":         (375, 667, 375, 667, (20, 0, 0, 0), UA_IPHONE, True, True),
    "ipad":       (834, 1194, 834, 1194, (24, 0, 20, 0), UA_IPAD, True, True),
    "laptop":     (1536, 864, 1536, 864, (0, 0, 0, 0), UA_WIN, False, False),
}
STANDALONE = """Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});
(function(){ const mm = window.matchMedia.bind(window); window.matchMedia = q => /display-mode:\\s*standalone/.test(q)
 ? {matches:true, media:q, addListener(){}, removeListener(){}, addEventListener(){}, removeEventListener(){}, onchange:null, dispatchEvent(){return false;}} : mm(q); })();"""
TOUCH_POINTS = "Object.defineProperty(navigator,'maxTouchPoints',{get:()=>5,configurable:true});"
# The cloud (the CDN is blocked here): documents with get/set/update/delete and listeners, kept in the tab's sessionStorage.
FAKE_CLOUD = r"""(()=>{ if(location.protocol !== 'http:') return;
  let C = null; try{ C = JSON.parse(sessionStorage.getItem('__fakecloud') || 'null'); }catch(e){}
  if(!C) C = JSON.parse(JSON.stringify(window.__cloudSeed || {}));
  ['progress','leaderboard','vrooms'].forEach(k => { C[k] = C[k] || {}; }); window.__cloud = C;
  const keep = () => { try{ sessionStorage.setItem('__fakecloud', JSON.stringify(C)); }catch(e){} };
  const subs = {}; const clone = v => v == null ? v : JSON.parse(JSON.stringify(v));
  const snap = (c, id) => { const d = (C[c] || {})[id]; return { id, exists: d !== undefined, data: () => clone(d), metadata: { fromCache: false, hasPendingWrites: false } }; };
  const fire = (c, id) => (subs[c + '/' + id] || []).forEach(f => setTimeout(() => f(snap(c, id)), 15));
  const doc = (c, id) => ({ id, get: () => Promise.resolve(snap(c, id)),
    set: (v, o) => { C[c][id] = (o && o.merge) ? Object.assign({}, C[c][id] || {}, clone(v)) : clone(v); keep(); fire(c, id); return Promise.resolve(); },
    update: v => { C[c][id] = Object.assign({}, C[c][id] || {}, clone(v)); keep(); fire(c, id); return Promise.resolve(); },
    delete: () => { delete C[c][id]; keep(); fire(c, id); return Promise.resolve(); },
    onSnapshot: function(){ const next = [...arguments].find(x => typeof x === 'function'); const k = c + '/' + id; (subs[k] = subs[k] || []).push(next);
      setTimeout(() => next(snap(c, id)), 30); return () => { subs[k] = (subs[k] || []).filter(f => f !== next); }; },
    collection: n => coll(c + '/' + id + '/' + n) });
  const coll = c => { C[c] = C[c] || {}; const q = { doc: id => doc(c, id), where(){ return q; }, orderBy(){ return q; }, limit(){ return q; },
    get: () => Promise.resolve({ empty: true, docs: [], forEach(){}, size: 0 }),
    onSnapshot: function(){ const next = [...arguments].find(x => typeof x === 'function'); setTimeout(() => next({ empty: true, docs: [], size: 0, forEach(){}, metadata: { fromCache: false }, docChanges: () => [] }), 30); return () => {}; } }; return q; };
  const db = { collection: coll, runTransaction: fn => { const tx = { get: r => r.get(), set: (r, v, o) => { r.set(v, o); return tx; }, update: (r, v) => { r.update(v); return tx; }, delete: r => { r.delete(); return tx; } }; return Promise.resolve().then(() => fn(tx)); },
    batch: () => ({ set(){}, update(){}, delete(){}, commit: () => Promise.resolve() }) };
  const fs = () => db; fs.FieldValue = { delete: () => null, serverTimestamp: () => Date.now(), arrayUnion: (...x) => x, arrayRemove: () => [], increment: n => n }; fs.FieldPath = function(){};
  window.firebase = { apps: [], initializeApp(){ this.apps.push({}); }, firestore: fs };
})()"""
# Every write to the viewport meta, with the scale and whether a text field was focused at that moment.
META_LOG = r"""(()=>{ window.__metaLog = [];
  const isField = el => !!el && (el.tagName === 'TEXTAREA' || (el.tagName === 'INPUT' && !/^(checkbox|radio|button|submit|reset|range|color|file|image|hidden)$/i.test(el.type || '')));
  /* the meta as the parser wrote it, before any of the page's own scripts can touch it */
  window.__onViewportMeta((m) => { window.__metaAuthored = m.getAttribute('content');
    new MutationObserver(() => { const v = window.visualViewport;
      window.__metaLog.push({ t: Math.round(performance.now()), c: m.getAttribute('content'), s: v ? Math.round(v.scale * 1000) / 1000 : 0, focused: isField(document.activeElement) });
    }).observe(m, { attributes: true, attributeFilter: ['content'] }); }); })()"""
# calls back once with the viewport meta as soon as the parser has inserted it
ON_META = r"""(()=>{ const cbs = []; let found = null;
  window.__onViewportMeta = cb => { if(found) cb(found); else cbs.push(cb); };
  const look = () => { const m = document.getElementById('viewportmeta'); if(m && !found){ found = m; cbs.splice(0).forEach(cb => cb(m)); return true; } return !!found; };
  const mo = new MutationObserver(() => { if(look()) mo.disconnect(); }); mo.observe(document, { childList: true, subtree: true }); })()"""
# iOS's side of a held zoom, simulated: the visual viewport reports a scale (window.__vvHold(s)) until the viewport meta has
# been clamped to maximum-scale=1 for 150ms on end - Safari gives a scale back when the viewport is clamped, and applies a
# viewport change in its own process, not in the frame it is written (the latency is this check's model, not a measurement;
# a clamp lifted after two frames, as build 383's was, is taken as one Safari never saw). Events still come from the real one.
FAKE_VV = r"""(()=>{ const real = window.visualViewport; if(!real) return;
  const st = { s: (window.__vvStart || 1), ot: 0, keep: false }; const LAT = window.__vvLatency || 150; let since = 0;
  const clamped = () => { const m = document.getElementById('viewportmeta'); return !!m && /maximum-scale\s*=\s*1(\.0+)?(\s*,|\s*$)/.test(m.getAttribute('content') || ''); };
  window.__onViewportMeta(m => new MutationObserver(() => { since = clamped() ? (since || performance.now()) : 0; }).observe(m, { attributes: true, attributeFilter: ['content'] }));
  setInterval(() => { if(!st.keep && since && performance.now() - since >= LAT){ st.s = 1; st.ot = 0; } }, 10);
  const fake = { get scale(){ return st.s; }, get width(){ return innerWidth / st.s; }, get height(){ return innerHeight / st.s; },
    get offsetTop(){ return st.ot; }, get offsetLeft(){ return 0; }, get pageTop(){ return scrollY + st.ot; }, get pageLeft(){ return scrollX; },
    addEventListener: (...a) => real.addEventListener(...a), removeEventListener: (...a) => real.removeEventListener(...a),
    dispatchEvent: e => real.dispatchEvent(e) };
  Object.defineProperty(window, 'visualViewport', { get: () => fake, configurable: true });
  /* __vvHold(scale, offsetTop, keep): held at a scale, the visible part offsetTop down the page; keep = Safari not giving it back */
  window.__vvHold = (s, ot, keep) => { st.s = s; st.ot = ot || 0; st.keep = !!keep; }; window.__vvScale = () => st.s;
})()"""
SEEN = ("['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card',"
        "'class26e.getstarted','class26e.frame.ok','class26e.penal55124.seen','class26e.penal124256.seen','class26e.penal256578.seen','class26e.a2hs']"
        ".forEach(k=>localStorage.setItem(k, k==='class26e.frame.ok'?'go-live-1':(k==='class26e.a2hs'?'done':'1')));")
CODE = "TEST-3849"   # a fake code
ACCOUNT = {"firstName": "Casey", "avatarChar": "ghost", "onboardingComplete": True, "publicId": "xph5b57jbp5a", "leaderboardOptIn": True,
           "tourRev": 999, "novaMet": 99, "lastModified": 1790500000000, "novaHeard": {"@recap": 99991231}, "savedCodeSaved": True,
           "rankMapFx244": True, "seenMainMenuTour": True, "seenClassTip": True, "seenProfileTour": True, "seenModeSelectTour": True, "seenUnitSelectTour": True,
           "seenRankingsTour": True, "seenAppearanceTour": True, "seenSettingsTour": True, "seenRewardsTour": True, "seenHomeTour": True,
           "seenLadderTour": True, "friendCode": "QRT-384",
           "lifetime": {"points": 6400, "answered": 840, "correct": 712, "drillPlays": 22, "examPlays": 9, "gamePlays": 6, "perfectTests": 3,
                        "currentStreak": 11, "longestStreak": 17},
           "testStats": {"Penal Code": {"plays": 3}}}

def seed_init(active="academy", code=CODE, signed_out=False):
    s = "(()=>{ if(location.protocol !== 'http:' || sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); " + SEEN
    if signed_out:
        return s + "localStorage.setItem('class26e.signedout','1'); })()"
    s += "localStorage.setItem('class26e.drill.v1', %s);" % json.dumps(json.dumps(ACCOUNT))
    if code: s += "localStorage.setItem('class26e.synccode', '%s');" % code
    s += "localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done');"
    s += ("['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card',"
          "'class26e.ifc.getstarted'].forEach(k=>localStorage.setItem(k,'1'));")
    ifc = {k: v for k, v in ACCOUNT.items() if k.startswith("seen") or k in ("firstName", "avatarChar", "publicId", "onboardingComplete", "tourRev", "novaMet", "novaHeard")}
    ifc.update({"lifetime": {"points": 900, "correct": 200, "answered": 260}, "leaderboardOptIn": False, "leaderboardOptInChanged": True, "lastModified": 1790500000000})
    s += "localStorage.setItem('class26e.ifc.drill.v1', %s);" % json.dumps(json.dumps(ifc))
    if active == "ifc": s += "localStorage.setItem('class26e.activeclass','ifc');"
    return s + " })()"

s = socket.socket(); s.bind(("127.0.0.1", 0)); PORT = s.getsockname()[1]; s.close()
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
http.server.ThreadingHTTPServer.handle_error = lambda *a: None
threading.Thread(target=http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Q, directory=ROOT)).serve_forever, daemon=True).start()
URL = "http://127.0.0.1:%d/index.html" % PORT
BODIES = {}
def body(ins):
    if ins not in BODIES:
        v = {"top": "%dpx" % ins[0], "right": "%dpx" % ins[1], "bottom": "%dpx" % ins[2], "left": "%dpx" % ins[3]}
        BODIES[ins] = INSET_RE.sub(lambda m: v[m.group(1)], SRC)
    return BODIES[ins]

fails = []; fix_fails = []
def chk(name, cond, info=""):
    print(("  PASS " if cond else "  FAIL ") + name + ("" if cond else "  -> " + str(info)[:600]), flush=True)
    if not cond:
        fails.append(name)
        if name.startswith("[fix]"): fix_fails.append(name)

def open_dev(br, dev, inits=(), dsf=1, wait=3200, perms=None, cloud=None):
    w, h, sw, sh, ins, ua, touch, inst = DEV[dev]
    kw = dict(viewport={"width": w, "height": h}, screen={"width": sw, "height": sh}, user_agent=ua, has_touch=touch, is_mobile=touch,
              device_scale_factor=dsf)
    if perms: kw["permissions"] = perms
    ctx = br.new_context(**kw)
    if inst: ctx.add_init_script(STANDALONE)
    if "Macintosh" in ua and touch: ctx.add_init_script(TOUCH_POINTS)
    ctx.add_init_script("window.__cloudSeed = %s;" % json.dumps(cloud or {}))
    ctx.add_init_script(FAKE_CLOUD)
    ctx.add_init_script(ON_META)
    ctx.add_init_script(META_LOG)
    for sc in inits: ctx.add_init_script(sc)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:240]))
    b = body(ins)
    pg.route("**/index.html", lambda r, q, b=b: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.route("**/version.json*", lambda r, q: r.fulfill(status=200, headers={"content-type": "application/json"},
             body=json.dumps({"build": BUILD, "force": False, "frameId": ""})))
    pg.goto(URL); pg.wait_for_timeout(wait)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); try{ homeUnlocksOwed=()=>false; }catch(e){} }")
    pg.errs = errs; pg.dev = dev; pg.ctx = ctx
    return pg

def clear_popups(pg):
    pg.evaluate("""()=>{ [...document.querySelectorAll('button')].filter(b=>/^(Got it|Not now|Skip|I.ll add it later)$/.test(b.textContent.trim()) && b.offsetParent).forEach(b=>b.click());
      document.querySelectorAll('.rs-spot,.unlock-card,#tour-tooltip,.tour-dim').forEach(n=>n.remove()); }""")

# ---------------------------------------------------------------------------------------------------------------- fields
FIELDS = r"""(label)=>{ const z = screen.width / innerWidth;
  return [...document.querySelectorAll('input, textarea, select, [contenteditable=true]')]
    .filter(e => !/^(checkbox|radio|range|button|submit|color|file|hidden|image|reset)$/i.test(e.type || '') && !e.closest('.nova-hsw'))
    .map(e => { const fs = parseFloat(getComputedStyle(e).fontSize), cz = e.currentCSSZoom || 1;
      return { where: label, f: (e.className || e.tagName).toString().slice(0, 40), css: fs, glass: Math.round(fs * cz * z * 10) / 10 }; }); }"""
NOVA_ASK = "()=>{ const t=document.createElement('div'); t.className='nova-talk'; t.id='__gate-nt'; const i=document.createElement('input'); i.type='text'; i.className='searchbox searchbox-plain nt-ask-input'; t.appendChild(i); document.body.appendChild(t); }"
FIELD_SCREENS = [
    ("the sign-in code (Welcome > Sign in)", "()=>showWelcomeCodeEntry()", "academy"),
    ("the username (sign-up)", "()=>showWelcomeNamePrompt()", "academy"),
    ("Nova's ask field", NOVA_ASK, "both"),
    ("the units search", "()=>{ cfg.mode='drill'; showSetup(); }", "both"),
    ("Review's units", "()=>{ cfg.mode='review'; showSetup(); }", "both"),
    ("Review's list", "()=>{ cfg.mode='review'; showAnswerReview([topicsIn(QUESTIONS)[0]], 'all'); }", "both"),
    ("the Leaderboard", "()=>showRankings('overall')", "academy"),
    ("Manage friends", "()=>showFriends()", "both"),
    ("Account's name", "()=>showAppearance({page:'account'})", "both"),
    ("Sync > Enter a code", "()=>{ const was=syncCode; syncCode=null; showAppearance({page:'sync'}); const b=[...document.querySelectorAll('#stage button')].find(x=>/Enter a code/.test(x.textContent)); b && b.click(); syncCode=was; }", "academy"),
    ("the bug report", "()=>showBugReport()", "both"),
    ("the Virtual Room", "()=>showVirtualRoomSetup()", "academy"),
    ("the chat", "()=>{ showHome(); openChatDock(); }", "both"),
]
def sec_fields(br):
    print("\nfields: 16px+ on the glass")
    for dev in ["promax", "pm85", "pm85-tab", "se"]:
        for cls in ["academy", "ifc"]:
            pg = open_dev(br, dev, [seed_init(cls)])
            got = []
            for label, js, where in FIELD_SCREENS:
                if where != "both" and where != cls: continue
                try:
                    pg.evaluate(js); pg.wait_for_timeout(650)
                    got += pg.evaluate(FIELDS, label)
                    pg.evaluate("()=>{ document.getElementById('__gate-nt')?.remove(); try{ closeChatDock(); }catch(e){} }")
                except Exception as e:
                    got.append({"where": label, "f": "error " + str(e)[:80], "css": 0, "glass": 0})
            under = sorted({(f["where"], f["f"], f["css"], f["glass"]) for f in got if f["glass"] < 16})
            seen = {f["where"] for f in got}
            mark = "[fix]" if dev.startswith("pm85") and cls == "academy" else "[guard]"
            chk("%s %s %s: %d fields on %d screens, none under 16px on the glass %s" % (mark, dev, cls, len(got), len(seen), under[:4]),
                not under and len(seen) >= (10 if cls == "academy" else 7), under)
            chk("[guard] %s %s: no page errors" % (dev, cls), not pg.errs, pg.errs[:2])
            pg.ctx.close()
    # the walk itself, as a person signs in on the reference phone at 85%: Welcome -> Sign in -> the field
    for dev in ["pm85", "pm85-tab"]:
        pg = open_dev(br, dev, [seed_init(signed_out=True)])
        if pg.evaluate("()=>!!document.querySelector('.gs-page .gs-go')"): pg.click(".gs-go"); pg.wait_for_timeout(1100)
        pg.click(".welcome-signin"); pg.wait_for_timeout(700)
        pg.click(".synccode-entry-panel input.searchbox"); pg.wait_for_timeout(200)
        f = pg.evaluate("""()=>{ const i=document.activeElement; const fs=parseFloat(getComputedStyle(i).fontSize);
          return { css: fs, glass: Math.round(fs * (i.currentCSSZoom||1) * screen.width / innerWidth * 10) / 10, zoomed: document.documentElement.classList.contains('page-zoomed') }; }""")
        chk("[fix] %s: Welcome > Sign in, the code field as it is tapped: %spx CSS = %spx on the glass (iOS zooms under 16)" % (dev, f["css"], f["glass"]),
            f["zoomed"] and f["glass"] >= 16, f)
        pg.ctx.close()

# ---------------------------------------------------------------------------------------------------------------- zoom
def pinch(pg, scale, pan=0.25):
    """A real held page scale in Chromium: the page scale set from outside (CDP Emulation.setPageScaleFactor - the page cannot
    change it, which is what makes it a HELD scale here), then the visible part panned down the page by a scroll gesture, as
    iOS pans to a field it zooms to. (A synthesized pinch does not take on this app: body is touch-action:pan-y.) Chromium can
    drop the scale once while the page settles, so it is set again until it reads back."""
    if not getattr(pg, "cdp", None): pg.cdp = pg.ctx.new_cdp_session(pg)
    w, h = pg.evaluate("[innerWidth, innerHeight]")
    for _ in range(8):
        pg.cdp.send("Emulation.setPageScaleFactor", {"pageScaleFactor": scale}); pg.wait_for_timeout(450)
        if pg.evaluate("()=>visualViewport.scale") > scale - 0.05: break
    if pan and pg.evaluate("()=>visualViewport.offsetTop") < 10:
        pg.cdp.send("Input.synthesizeScrollGesture", {"x": int(w / 2), "y": int(h / 3), "yDistance": -int(h * pan), "gestureSourceType": "mouse", "speed": 1200})
        pg.wait_for_timeout(700)
    return pg.evaluate("()=>({ s: visualViewport.scale, ot: visualViewport.offsetTop, h: visualViewport.height })")
CLAMPS = "(since)=>window.__metaLog.filter(e=>e.t>=since && /maximum-scale/.test(e.c))"
NOW = "()=>Math.round(performance.now())"
META = "()=>({ now: document.getElementById('viewportmeta').getAttribute('content'), authored: window.__metaAuthored })"
VIS = """(state)=>{ Object.defineProperty(document, 'visibilityState', { get: () => state, configurable: true });
  Object.defineProperty(document, 'hidden', { get: () => state !== 'visible', configurable: true }); document.dispatchEvent(new Event('visibilitychange')); }"""
def sec_zoom(br):
    print("\nzoom: a held page scale is given back")
    for dev in ["promax", "pm85"]:
        for cls in ["academy", "ifc"]:
            # (a) a real held scale (Chromium's pinch): the app asks for it back; it is iOS that answers
            pg = open_dev(br, dev, [seed_init(cls)])
            pg.evaluate("()=>showHome()"); pg.wait_for_timeout(900); clear_popups(pg)
            t0 = pg.evaluate(NOW)
            for js in ["()=>showRankings ? showRankings('overall') : showProfile()", "()=>showHome()", "()=>window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true }))"]:
                pg.evaluate(js); pg.wait_for_timeout(700)
            pg.evaluate(VIS, "hidden"); pg.evaluate(VIS, "visible"); pg.wait_for_timeout(900)
            n = pg.evaluate("(t)=>window.__metaLog.filter(e=>e.t>=t).length", t0)
            chk("[guard] %s %s: at scale 1, screen changes, pageshow and coming back never touch the viewport (%d writes)" % (dev, cls, n), n == 0, n)
            pg.evaluate("()=>showAppearance({ page: 'study' })"); pg.wait_for_timeout(1200)   # a still screen to hold the scale on
            v = pinch(pg, 1.5)
            chk("[guard] %s %s: Chromium holds a real page scale (%s)" % (dev, cls, v), v["s"] > 1.4, v)
            t0 = pg.evaluate(NOW)
            pg.evaluate("()=>{ cfg.mode='drill'; showSetup(); }"); pg.wait_for_timeout(1900)
            c = pg.evaluate(CLAMPS, t0); m = pg.evaluate(META)
            chk("[fix] %s %s: a screen change under a held scale (%.2f) asks for it back - the viewport clamped (%d) and then lifted to exactly what it was (%r)"
                % (dev, cls, v["s"], len(c), m["now"]), len(c) >= 1 and all(not e["focused"] and e["s"] > 1.01 for e in c) and m["now"] == m["authored"], [c[:2], m])
            v = pinch(pg, 1.5)
            t0 = pg.evaluate(NOW)
            pg.evaluate("()=>window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true }))"); pg.wait_for_timeout(1900)
            c = pg.evaluate(CLAMPS, t0); m = pg.evaluate(META)
            chk("[fix] %s %s: so does a pageshow (%d clamps at %.2f, the viewport back to %r)" % (dev, cls, len(c), v["s"], m["now"]),
                v["s"] > 1.4 and len(c) >= 1 and m["now"] == m["authored"], [c[:2], m])
            v = pinch(pg, 1.5)
            t0 = pg.evaluate(NOW)
            pg.evaluate(VIS, "hidden"); pg.evaluate(VIS, "visible"); pg.wait_for_timeout(1900)
            c = pg.evaluate(CLAMPS, t0); m = pg.evaluate(META)
            chk("[fix] %s %s: so does coming back to the app (%d clamps at %.2f, the viewport back to %r)" % (dev, cls, len(c), v["s"], m["now"]),
                v["s"] > 1.4 and len(c) >= 1 and m["now"] == m["authored"], [c[:2], m])
            # a field focused: nothing - not pageshow, not coming back, not the keyboard's resize
            # (on Manage friends, a still screen with a field in both classes; Chromium's page scale is set again until it holds)
            pg.evaluate("()=>showFriends()"); pg.wait_for_timeout(1000)
            for _ in range(3):
                pg.evaluate("()=>{ const i=document.querySelector('#stage .friend-add-input'); i && i.focus(); }")
                pg.wait_for_timeout(300)
                v = pinch(pg, 1.5, 0)
                if v["s"] > 1.4: break
            t0 = pg.evaluate(NOW)
            focused = pg.evaluate("()=>{ const a=document.activeElement; return !!a && /INPUT|TEXTAREA/.test(a.tagName); }")
            pg.evaluate("()=>window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true }))")
            pg.evaluate(VIS, "hidden"); pg.evaluate(VIS, "visible")
            pg.evaluate("()=>visualViewport.dispatchEvent(new Event('resize'))"); pg.wait_for_timeout(1200)
            n = pg.evaluate("(t)=>window.__metaLog.filter(e=>e.t>=t).length", t0); s1 = pg.evaluate("()=>visualViewport.scale")
            chk("[guard] %s %s: with a field focused (%s) and the scale held (%.2f -> %.2f), neither pageshow, coming back nor the keyboard's resize touches the viewport (%d writes)"
                % (dev, cls, focused, v["s"], s1, n), focused and v["s"] > 1.4 and s1 > 1.4 and n == 0, n)
            chk("[guard] %s %s: no page errors" % (dev, cls), not pg.errs, pg.errs[:2])
            pg.ctx.close()
    # (b) iOS's answer simulated: a scale that is given back when the viewport is clamped
    for dev in ["promax", "pm85"]:
        pg = open_dev(br, dev, ["window.__vvStart = 1.6;", FAKE_VV, seed_init("academy")])
        r = pg.evaluate("()=>({ s: window.__vvScale(), log: window.__metaLog.length })"); m = pg.evaluate(META)
        chk("[fix] %s: a page that comes up held at 1.6 (a reload carrying it) is given back at boot (scale %s, %d writes, viewport %r)" % (dev, r["s"], r["log"], m["now"]),
            r["s"] == 1 and m["now"] == m["authored"], [r, m])
        for label, js in [("pageshow", "()=>window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true }))"),
                          ("coming back to the app", "()=>{ Object.defineProperty(document, 'visibilityState', { get: () => 'visible', configurable: true }); document.dispatchEvent(new Event('visibilitychange')); }"),
                          ("a screen change", "()=>showProfile()")]:
            pg.evaluate("()=>window.__vvHold(1.6)"); pg.wait_for_timeout(100)
            pg.evaluate(js); pg.wait_for_timeout(1300)
            r = pg.evaluate("()=>window.__vvScale()"); m = pg.evaluate(META)
            chk("[fix] %s: held at 1.6, %s gives it back (scale %s, viewport %r)" % (dev, label, r, m["now"]), r == 1 and m["now"] == m["authored"], [r, m])
        # how long a clamp is held while the scale has not come back (Safari not answering): long enough for it to be applied
        pg.evaluate("()=>showHome()"); pg.wait_for_timeout(800)
        pg.evaluate("()=>window.__vvHold(1.6, 0, true)"); pg.wait_for_timeout(100)
        t0 = pg.evaluate(NOW)
        pg.evaluate("()=>{ document.activeElement && document.activeElement.blur && document.activeElement.blur(); document.dispatchEvent(new FocusEvent('focusout')); }")
        pg.evaluate("()=>showProfile()"); pg.wait_for_timeout(1600)
        log = pg.evaluate("(t)=>window.__metaLog.filter(e=>e.t>=t)", t0)
        held = [b["t"] - a["t"] for a, b in zip(log, log[1:]) if "maximum-scale" in a["c"] and "maximum-scale" not in b["c"]]
        chk("[fix] %s: a clamp is held until the scale is back or ~400ms, not two frames (%s ms)" % (dev, held[:4]), held and min(held) >= 300, log[:6])
        pg.evaluate("()=>window.__vvHold(1, 0, false)"); pg.wait_for_timeout(700)
        # a field focused under the held scale: never
        pg.evaluate("()=>{ showRankings('overall'); }"); pg.wait_for_timeout(900)
        pg.evaluate("()=>window.__vvHold(1.6)")
        pg.evaluate("()=>{ const i=document.querySelector('#stage input[type=search], #stage input.searchbox, .tabsearch-input'); i && i.focus(); }"); pg.wait_for_timeout(200)
        t0 = pg.evaluate(NOW)
        pg.evaluate("()=>window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true }))")
        pg.evaluate("()=>visualViewport.dispatchEvent(new Event('resize'))"); pg.wait_for_timeout(1000)
        r = pg.evaluate("()=>window.__vvScale()"); n = pg.evaluate("(t)=>window.__metaLog.filter(e=>e.t>=t).length", t0)
        chk("[guard] %s: held at 1.6 with a field focused - left alone (scale %s, %d writes)" % (dev, r, n), r == 1.6 and n == 0, [r, n])
        pg.evaluate("()=>document.activeElement && document.activeElement.blur()"); pg.wait_for_timeout(1200)
        r = pg.evaluate("()=>window.__vvScale()")
        chk("[fix] %s: ...and given back once the field is left (scale %s)" % (dev, r), r == 1, r)
        chk("[guard] %s: no page errors (simulated scale)" % dev, not pg.errs, pg.errs[:2])
        pg.ctx.close()
    # the sign-in walk with the code field's zoom held, as on his phone: Continue -> Sync This Device -> Home
    acct = dict(ACCOUNT); acct["lifetime"] = dict(ACCOUNT["lifetime"], points=4321)
    for dev in ["pm85", "promax"]:
        pg = open_dev(br, dev, [FAKE_VV, seed_init(signed_out=True)], cloud={"progress": {CODE: acct}})
        if pg.evaluate("()=>!!document.querySelector('.gs-page .gs-go')"): pg.click(".gs-go"); pg.wait_for_timeout(1100)
        pg.click(".welcome-signin"); pg.wait_for_timeout(700)
        pg.click(".synccode-entry-panel input.searchbox"); pg.evaluate("()=>window.__vvHold(1.18)")   # iOS zooms to the field
        pg.keyboard.type(CODE); pg.click(".synccode-entry-panel #nextbtn")
        try: pg.wait_for_selector(".synccode-confirm.show .next.playbtn", timeout=6000)
        except Exception: pass
        pg.wait_for_timeout(300)
        pg.evaluate("()=>{ const b=document.querySelector('.synccode-confirm .next.playbtn'); b && b.click(); }")
        try:
            pg.wait_for_selector("#genprofile-overlay", timeout=4000)
            pg.wait_for_selector("#genprofile-overlay", state="detached", timeout=15000)
        except Exception: pass
        pg.wait_for_timeout(600)
        pg.evaluate("()=>visualViewport.dispatchEvent(new Event('resize'))")   # the keyboard going away
        pg.wait_for_timeout(1200)
        r = pg.evaluate("()=>({ s: window.__vvScale(), screen: document.querySelector('#stage [data-screen]')?.dataset.screen, code: syncCode })"); m = pg.evaluate(META)
        chk("[fix] %s: signed in with the code field's zoom held (1.18): Home at scale %s, the viewport %r" % (dev, r["s"], m["now"]),
            r["screen"] == "home" and r["code"] == CODE and r["s"] == 1 and m["now"] == m["authored"], [r, m])
        chk("[guard] %s: no page errors (sign-in walk)" % dev, not pg.errs, pg.errs[:2])
        pg.ctx.close()

# ---------------------------------------------------------------------------------------------------------------- place
SAMPLER = r"""(ms)=>new Promise(res=>{ const out=[]; const t0=performance.now();
  const bad = a => { const c=getComputedStyle(a); const b=[];
    if(c.transform!=='none') b.push('transform'); if(c.translate!=='none') b.push('translate'); if(c.scale!=='none') b.push('scale'); if(c.rotate!=='none') b.push('rotate');
    if(c.filter!=='none') b.push('filter'); if(c.backdropFilter && c.backdropFilter!=='none') b.push('backdrop-filter'); if(c.perspective!=='none') b.push('perspective');
    if(/paint|layout|strict|content/.test(c.contain)) b.push('contain'); if(/transform|filter|perspective|translate|scale/.test(c.willChange)) b.push('will-change');
    if(c.containerType && c.containerType!=='normal') b.push('container'); return b; };
  const who = a => a.tagName.toLowerCase()+(a.id?'#'+a.id:'')+(typeof a.className==='string'&&a.className?'.'+a.className.trim().split(/\s+/)[0]:'');
  const look = sel => { const el=document.querySelector(sel); if(!el) return null; const r=el.getBoundingClientRect(), cs=getComputedStyle(el);
    const shown = !el.hidden && cs.display!=='none' && cs.visibility!=='hidden' && +cs.opacity>0.05 && r.height>0;
    const anc=[]; for(let a=el.parentElement;a && a!==document.documentElement;a=a.parentElement){ const b=bad(a); if(b.length) anc.push(who(a)+' '+b.join(',')); }
    return { shown, top:Math.round(r.top), bottom:Math.round(r.bottom), anc }; };
  function f(){ out.push({ t:Math.round(performance.now()-t0), tabs:look('#bottomtabs'), pause:look('#pausebtn'), stack:look('#stage .pause-stack'), ih:innerHeight,
      q: !!document.querySelector('#stage > .qpanel') });
    if(performance.now()-t0<ms) requestAnimationFrame(f); else res(out); }
  requestAnimationFrame(f); })"""
def judge(rows, want_tabs, settle=600, need=None):
    bad = []
    if need:   # judged from 500ms after the screen it is about came up
        first = next((r["t"] for r in rows if r.get(need)), None)
        settle = (first + 500) if first is not None else 10 ** 9
    for r in rows:
        t, p, s, ih = r["tabs"], r["pause"], r["stack"], r["ih"]
        if t and t["shown"]:
            if t["bottom"] > ih + 1 or t["bottom"] < ih - 140: bad.append("t%d tab bar %d-%d of %d" % (r["t"], t["top"], t["bottom"], ih))
            if t["anc"]: bad.append("t%d tab bar ancestor %s" % (r["t"], t["anc"][0]))
        if want_tabs is not None and r["t"] > settle and bool(t and t["shown"]) != want_tabs: bad.append("t%d tab bar shown=%s" % (r["t"], bool(t and t["shown"])))
        if p and p["shown"]:
            if p["top"] < 0 or p["bottom"] > ih * 0.25: bad.append("t%d Pause %d-%d" % (r["t"], p["top"], p["bottom"]))
        if s and s["shown"] and r["t"] > 500:
            mid = (s["top"] + s["bottom"]) / 2
            if abs(mid - ih / 2) > 40: bad.append("t%d Pause's card middle %d of %d" % (r["t"], mid, ih))
    return bad
def step(pg, js, ms=1200):
    p = pg.evaluate_handle(SAMPLER, ms)
    if js.startswith("click:"):
        try: pg.click(js[6:], timeout=3000)
        except Exception as e: pg.evaluate("(s)=>{ const b=document.querySelector(s); b && b.click(); }", js[6:])
    else: pg.evaluate(js)
    return p.json_value()
START_DRILL = """()=>{ const u=topicsIn(QUESTIONS)[0]; cfg.mode='drill'; cfg.source='all'; cfg.units=[u];
  const pool=QUESTIONS.map((q,i)=>i).filter(i=>(QUESTIONS[i].topic||'').trim()===u); beginRun(pool); }"""
def sec_place(br):
    print("\nplace: the tab bar and Pause where they belong, every frame after a transition")
    for dev in ["promax", "promax-tab", "pm85", "pm85-tab"]:
        for cls in ["academy", "ifc"]:
            pg = open_dev(br, dev, [seed_init(cls)])
            pg.evaluate("()=>showHome()"); pg.wait_for_timeout(900); clear_popups(pg)
            flow = [("Start Studying", "click:.panel.home.screen-home-actual .playbtn", True),
                    ("Review's units", "click:.modecard[data-mode=review]", True),
                    ("the units scrolled", "()=>window.scrollTo(0, 700)", True),
                    ("Review's list", "()=>{ cfg.mode='review'; showAnswerReview([topicsIn(QUESTIONS)[0]], 'all'); }", True),
                    ("Review's list scrolled", "()=>window.scrollTo(0, 2500)", True),
                    ("Review paused", "click:#pausebtn", None),
                    ("Review resumed", "click:#resumebtn", True),
                    ("Home by the tab", "click:#bottomtab-home", True),
                    ("Drill's units", "()=>{ cfg.mode='drill'; showSetup(); }", True),
                    ("a question", START_DRILL, False),
                    ("paused", "click:#pausebtn", None),
                    ("resumed", "click:#resumebtn", False),
                    ("paused again", "click:#pausebtn", None)]
            problems = []
            for label, js, tabs in flow:
                if label == "a question":
                    # a run takes 2-3s to put its first question up (the units stay until it does): sampled from the moment it is up
                    pg.evaluate(js)
                    try: pg.wait_for_selector("#stage > .qpanel", timeout=12000)
                    except Exception: problems.append("a question: none came up in 12s"); continue
                    rows = step(pg, "()=>0", 1200)
                    b = judge(rows, tabs, 350)
                else:
                    rows = step(pg, js, 1200 if "scrolled" not in label else 700)
                    b = judge(rows, tabs)
                if b: problems.append("%s: %s" % (label, b[:3]))
            chk("[guard] %s %s: through the units, Review's list, Pause and a question, every frame: the tab bar at the bottom or hidden where it should be, no "
                "transformed ancestor, Pause at the top, the pause card on the middle" % (dev, cls), not problems, problems[:4])
            chk("[guard] %s %s: no page errors" % (dev, cls), not pg.errs, pg.errs[:2])
            pg.ctx.close()
    # Pause's card under a held zoom that is not given back: on the middle of what is showing - Safari's simulated (held at
    # 1.5, the visible part 240px down the page). (Chromium's own page scale cannot stand in here: it drops it as the screen
    # changes under it.)
    CARD = """()=>{ const s=document.querySelector('#stage .pause-stack'); if(!s) return null; const b=s.getBoundingClientRect(), v=visualViewport;
      return { mid: (b.top + b.bottom) / 2, band: v.offsetTop + v.height / 2, s: v.scale, ot: v.offsetTop, h: v.height }; }"""
    for dev in ["promax", "pm85"]:
        for cls in ["academy", "ifc"]:
            for how in ["simulated"]:
                pg = open_dev(br, dev, [seed_init(cls)] + ([FAKE_VV] if how == "simulated" else []))
                pg.evaluate("()=>showHome()"); pg.wait_for_timeout(900); clear_popups(pg)
                pg.evaluate(START_DRILL)
                pg.wait_for_selector("#stage .qpanel", timeout=8000); pg.wait_for_timeout(600)
                if how == "real": pinch(pg, 1.5, 0.25)
                else: pg.evaluate("()=>window.__vvHold(1.5, 240, true)")
                pg.evaluate("()=>pauseRun()"); pg.wait_for_timeout(1100)
                r = pg.evaluate(CARD)
                ok = r and r["s"] > 1.4 and r["ot"] > 100 and abs(r["mid"] - r["band"]) <= 6
                chk("[fix] %s %s: paused under a held zoom (%s: %.2f, the visible part %dpx down the page) the card is on the middle of what is showing (%s vs %s)"
                    % (dev, cls, how, r and r["s"] or 0, r and r["ot"] or 0, r and round(r["mid"]), r and round(r["band"])), ok, r)
                pg.ctx.close()

# ---------------------------------------------------------------------------------------------------------------- copy
COPY_LOOK = r"""()=>{ const S=document.querySelector('#stage'); const b=S.querySelector('.sync-code-block .friend-copy-btn, .sync-copy-btn');
  const well=S.querySelector('.sync-code-row .sync-code-well'); if(!b || !well) return { btn: !!b, well: !!well };
  const r=b.getBoundingClientRect(), w=well.getBoundingClientRect(), cs=getComputedStyle(b);
  const hit=document.elementFromPoint(r.left + r.width/2, r.top + r.height/2);
  return { btn:true, cls:b.className, w:r.width, h:r.height, text:b.textContent.trim(), label:b.getAttribute('aria-label'), svg:!!b.querySelector('svg.friend-copy-ic'), tick:!!b.querySelector('svg.friend-copy-tick'),
    bg:cs.backgroundColor, radius:cs.borderRadius, color:cs.color, dy:Math.abs((r.top+r.height/2)-(w.top+w.height/2)), gap:r.left-w.right, inRow:!!b.closest('.sync-code-row'),
    onTop: !!hit && (hit===b || b.contains(hit)), inView: r.right <= innerWidth && r.left >= 0 }; }"""
FRIEND_LOOK = r"""()=>{ const b=document.querySelector('#stage .friend-mycode-wrap .friend-copy-btn'); if(!b) return null; const r=b.getBoundingClientRect(), cs=getComputedStyle(b);
  return { w:r.width, h:r.height, bg:cs.backgroundColor, radius:cs.borderRadius, color:cs.color }; }"""
def sec_copy(br):
    print("\ncopy: the sync code's copy button")
    for dev in ["promax", "pm85", "se", "ipad", "laptop"]:
        for cls in ["academy", "ifc"]:
            pg = open_dev(br, dev, [seed_init(cls)], perms=["clipboard-read", "clipboard-write"])
            pg.evaluate("()=>showFriends()"); pg.wait_for_timeout(900)
            fr = pg.evaluate(FRIEND_LOOK)
            pg.evaluate("()=>showAppearance({ page: 'sync' })"); pg.wait_for_timeout(900)
            c = pg.evaluate(COPY_LOOK)
            same = bool(fr and c.get("btn") and abs(fr["w"] - c["w"]) < .6 and abs(fr["h"] - c["h"]) < .6 and fr["bg"] == c["bg"] and fr["radius"] == c["radius"] and fr["color"] == c["color"])
            chk("[fix] %s %s: Settings > Sync has a copy button beside the code, Manage friends' own (%s vs %s)" % (dev, cls, c and {k: c.get(k) for k in ("w", "bg", "label")}, fr),
                c.get("btn") and c["svg"] and c["tick"] and c["text"] == "" and c["label"] and same, [c, fr])
            if c.get("btn"):
                chk("[fix] %s %s: 44px+ (%.1fx%.1f), centred on the code's well (%.1fpx), clear of it (%.1fpx), not part of the reveal row, on top, on screen"
                    % (dev, cls, c["w"], c["h"], c["dy"], c["gap"]), c["w"] >= 44 and c["h"] >= 44 and c["dy"] <= 1.5 and c["gap"] >= 4 and not c["inRow"] and c["onTop"] and c["inView"], c)
                ov = pg.evaluate("()=>{ const v=document.querySelector('#stage .sync-code-value'); return { txt: v.textContent, over: v.scrollWidth - v.clientWidth, wellOver: v.parentElement.scrollWidth - v.parentElement.clientWidth }; }")
                chk("[guard] %s %s: the code still fits its well on one line (%s)" % (dev, cls, ov), ov["over"] <= 0 and ov["wellOver"] <= 0, ov)
                before = ov["txt"]
                pg.evaluate("()=>navigator.clipboard.writeText('nothing yet')")
                pg.click("#stage .sync-copy-btn"); pg.wait_for_timeout(350)
                r = pg.evaluate("""async ()=>({ clip: await navigator.clipboard.readText(), shown: shownSyncCode(), raw: syncCode, copied: document.querySelector('#stage .sync-copy-btn').classList.contains('is-copied'),
                    tickOp: +getComputedStyle(document.querySelector('#stage .sync-copy-btn .friend-copy-tick')).opacity, toast: [...document.querySelectorAll('.toast')].map(t=>t.textContent).join(' | '),
                    masked: document.querySelector('#stage .sync-code-value').textContent })""")
                chk("[fix] %s %s: a tap copies the code as shown (%r; the account is %r), turns to the tick, says so (%r), and leaves the code as it was (%r)"
                    % (dev, cls, r["clip"], r["raw"], r["toast"][:60], r["masked"]), r["clip"] == r["shown"] and "__" not in r["clip"] and r["copied"] and r["tickOp"] > .5
                    and re.search(r"copied", r["toast"], re.I) and r["masked"] == before, r)
            chk("[guard] %s %s: no page errors" % (dev, cls), not pg.errs, pg.errs[:2])
            pg.ctx.close()

# ---------------------------------------------------------------------------------------------------------------- signout
SHEET = r"""()=>{ const s=document.querySelector('#signout-confirm .savecode-sheet'); if(!s) return null;
  const bs=[...s.querySelectorAll('button')].filter(b=>b.offsetParent).map(b=>{ const r=b.getBoundingClientRect(); return { t:b.textContent.trim().slice(0,30), top:r.top, bottom:r.bottom, left:r.left, right:r.right, w:r.width, h:r.height, over: b.scrollWidth - b.clientWidth }; });
  const pairs=[]; for(let i=0;i<bs.length;i++) for(let j=i+1;j<bs.length;j++){ const a=bs[i], b=bs[j];
    const ix=Math.min(a.right,b.right)-Math.max(a.left,b.left); if(ix<=0) continue; pairs.push({ a:a.t, b:b.t, gap: Math.round((Math.max(a.top,b.top)-Math.min(a.bottom,b.bottom))*10)/10 }); }
  const card=document.getElementById('signout-confirm');
  return { bs, minGap: pairs.length ? Math.min(...pairs.map(p=>p.gap)) : 99, pairs, small: bs.filter(b=>b.w<44||b.h<44).map(b=>b.t), wide: bs.filter(b=>b.over>1).map(b=>b.t),
    fits: card.scrollHeight <= card.clientHeight + 1 || getComputedStyle(card).overflowY === 'auto', ih: innerHeight }; }"""
def sec_signout(br):
    print("\nsignout: Sign out's buttons never touch")
    for dev in ["promax", "promax-tab", "pm85", "pm85-tab", "se", "ipad", "laptop"]:
        for cls in ["academy", "ifc"]:
            pg = open_dev(br, dev, [seed_init(cls)])
            pg.evaluate("()=>showAppearance({ page: 'account' })"); pg.wait_for_timeout(900)
            pg.evaluate("()=>{ const r=document.querySelector('#stage .signout-row'); r && r.click(); }"); pg.wait_for_timeout(700)
            m = pg.evaluate(SHEET)
            chk("[fix] %s %s: Sign out's sheet - the closest two buttons are %spx apart (%s), each 44px+ %s, words inside %s" % (dev, cls, m and m["minGap"],
                m and [(p["a"], p["b"], p["gap"]) for p in m["pairs"]], m and m["small"], m and m["wide"]),
                m and len(m["bs"]) >= 3 and m["minGap"] >= 6 and not m["small"] and not m["wide"] and m["fits"], m)
            # a label long enough to wrap
            pg.evaluate("()=>{ document.querySelector('#signout-confirm .signout-save').textContent = 'Save my code somewhere safe before signing out of this device'; }"); pg.wait_for_timeout(200)
            m = pg.evaluate(SHEET)
            chk("[fix] %s %s: with a label that wraps, still %spx apart, words inside %s" % (dev, cls, m and m["minGap"], m and m["wide"]),
                m and m["minGap"] >= 6 and not m["wide"] and not m["small"], m)
            pg.ctx.close()

# ---------------------------------------------------------------------------------------------------------------- save
SHARE_SPY = r"""(()=>{ window.__shares = []; const fake = function(d){ window.__shares.push(d); return Promise.resolve(); };
  try{ Object.defineProperty(Navigator.prototype, 'share', { value: fake, configurable: true, writable: true }); }catch(e){ navigator.share = fake; } })()"""
def sec_save(br):
    print("\nsave: Save it on a laptop copies; on a phone it shares")
    for dev in ["laptop", "promax"]:
        for cls in ["academy", "ifc"]:
            laptop = dev == "laptop"
            pg = open_dev(br, dev, [SHARE_SPY, seed_init(cls)], perms=["clipboard-read", "clipboard-write"])
            had = pg.evaluate("()=>typeof navigator.share === 'function'")
            res = {}
            # the save-code card (Settings' Start syncing and a new account's)
            if cls == "academy":
                pg.evaluate("()=>{ showHome(); showSaveCodeCard({ mode: 'settings' }); }"); pg.wait_for_timeout(700)
                pg.evaluate("()=>navigator.clipboard.writeText('nothing yet')")
                pg.click("#savecode-card .savecode-save"); pg.wait_for_timeout(600)
                res["card"] = pg.evaluate("""async ()=>({ shares: window.__shares.length, clip: await navigator.clipboard.readText(), shown: shownSyncCode(),
                    status: document.querySelector('#savecode-card .savecode-status').textContent, cont: !document.querySelector('#savecode-card .savecode-continue').disabled })""")
                pg.evaluate("()=>{ const c=document.getElementById('savecode-card'); c && c.remove(); window.__shares=[]; }")
            # Settings > Sync > Save it
            pg.evaluate("()=>showAppearance({ page: 'sync' })"); pg.wait_for_timeout(900)
            pg.evaluate("()=>{ navigator.clipboard.writeText('nothing yet'); document.querySelectorAll('.toast').forEach(t=>t.remove()); }")
            if pg.evaluate("()=>!!document.querySelector('#stage .sync-save-code-row')"):
                pg.click("#stage .sync-save-code-row"); pg.wait_for_timeout(600)
                res["row"] = pg.evaluate("""async ()=>({ shares: window.__shares.length, clip: await navigator.clipboard.readText(), shown: shownSyncCode(),
                    toast: [...document.querySelectorAll('.toast')].map(t=>t.textContent).join(' | '), sub: (document.querySelector('#stage .sync-save-code-row .settings-row-sub')||{}).textContent })""")
            pg.evaluate("()=>{ window.__shares=[]; }")
            # Sign out's Save my code
            pg.evaluate("()=>showAppearance({ page: 'account' })"); pg.wait_for_timeout(800)
            pg.evaluate("()=>{ navigator.clipboard.writeText('nothing yet'); const r=document.querySelector('#stage .signout-row'); r && r.click(); }"); pg.wait_for_timeout(600)
            pg.click("#signout-confirm .signout-save"); pg.wait_for_timeout(600)
            res["signout"] = pg.evaluate("""async ()=>({ shares: window.__shares.length, clip: await navigator.clipboard.readText(), shown: shownSyncCode(),
                msg: document.querySelector('#signout-confirm .signout-msg').textContent })""")
            for where, r in res.items():
                if laptop:
                    said = r.get("status") or r.get("toast") or r.get("msg") or ""
                    chk("[fix] laptop %s %s: Save it copies the code (%r), never opens the share dialog (%d calls; the browser has one: %s), and says it copied (%r)"
                        % (cls, where, r["clip"], r["shares"], had, said[:70]), had and r["shares"] == 0 and r["clip"] == r["shown"] and "__" not in r["clip"] and re.search(r"copied", said, re.I), r)
                else:
                    chk("[guard] iPhone %s %s: Save it still hands the code to the share sheet (%d calls)" % (cls, where, r["shares"]), r["shares"] == 1, r)
            if laptop and "row" in res:
                chk("[fix] laptop %s: Settings' Save it says what it will do on a computer (%r)" % (cls, res["row"]["sub"]), re.search(r"copy", res["row"]["sub"] or "", re.I), res["row"])
            chk("[guard] %s %s: no page errors" % (dev, cls), not pg.errs, pg.errs[:2])
            pg.ctx.close()

def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME)
        for sec in SECTIONS:
            globals()["sec_" + sec](br)
        br.close()
    print("\n%d failed (%d [fix])" % (len(fails), len(fix_fails)))
    print("ALL PASS" if not fails else "SOME FAILED")
    sys.exit(0 if not fails else 1)

if __name__ == "__main__":   # (check-b384-walk.py imports the set-up above)
    main()
