#!/usr/bin/env python3
"""384.106: Software Update is a page of its own, and its Settings row says what the last check found.

Madison: "When selecting the check for update button, it just checks for an update right there, shouldn't it open a screen and
then have it in there? And if you have one available it would say update available update now? Idk" - and, with Delta's Settings
beside ours: "For check for update, maybe ours can say up to date similar to how Delta does it?"

version.json is served by the gate (each section says what it serves: the page's own build, a newer one, a 404, a blocked request,
or a request held open), every fetch of it is logged with its cache mode, and applyUpdate is a counter (no reload). Shape, not words:
states are read off the page (a spinner, a button or none, the build numbers, a time), never off a label.

 (1) the Settings row opens a page: a pushed Settings page (its round back button), the tab bar still up with the same tab lit, and
     the page asks for version.json itself (cache "reload") as it opens;
 (2) the page's head: the app's icon (the Home Screen icon the page holds), a name, the build running;
 (3) checking: while the request is out, a turning spinner in the status and no button; then
 (4) the same build: no button, the build running, and the time it checked;
 (5) a newer build: the new build, ONE button in the theme's colour; what's new only when version.json carries a note (none made
     up); Update Now (tapped twice) calls applyUpdate once, after the "Pushing update" bar; the automatic forced path did not fire;
 (6) a 404 and a blocked request: one button; Try again asks again, once however often it is tapped;
 (7) the row tapped twice, by script and by a real double tap: one request;
 (8) Back returns to Settings' menu with the row on it; the same tab lit throughout; (both classes)
 (9) the row's pill: none until a check has answered; "up to date" green / "update available" in the theme's colour; a row out of
     sight asks nothing; a row that comes into view with no fresh answer asks ONCE, and a second visit within the minute reuses it;
     when the app's own check has just run the row reuses its answer and asks nothing; a failed check, a check still out and an
     answer over a minute old all show nothing;
(10) the pill's shape, Delta's (1.09x and 0.65 on his screenshot): a capsule 0.95-1.3x the row's words' size tall, its words
     0.6-0.82 of theirs and semibold, 6-12px of air each side and even, on one line, on the row's middle, between the label and the
     chevron - at 440px, at 320px and on an iPad;
(11) every state on a phone and an iPad both ways and a 320px phone: no sideways scroll, nothing past the edge, buttons 44px+; in
     every theme the button and the update pill are the theme's colour, their words readable on it (3:1+);
(12) no page errors.
Run:  python3 tools/check-b384-swupdate.py            (--against FILE|REV must FAIL; origin/main 384.95 does)"""
import colorsys, functools, http.server, io, json, os, re, socket, subprocess, sys, threading
from playwright.sync_api import sync_playwright

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def arg(n, d=None): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d
AG = arg("--against")
if AG:
    SRC_TEXT = open(AG, encoding="utf-8").read() if os.path.isfile(AG) else subprocess.check_output(["git", "-C", ROOT, "show", AG + ":index.html"]).decode("utf-8")
else:
    SRC_TEXT = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
INSET = {"top": "62px", "bottom": "34px", "left": "0px", "right": "0px"}
BODY = re.sub(r"env\(safe-area-inset-(top|bottom|left|right)(?:\s*,[^()]*)?\)", lambda m: INSET[m.group(1)], SRC_TEXT)
BUILD = re.search(r'const APP_BUILD = "([^"]+)"', SRC_TEXT).group(1)
NEWER = BUILD + "-next"

so = socket.socket(); so.bind(("127.0.0.1", 0)); PORT = so.getsockname()[1]; so.close()
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
threading.Thread(target=http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Q, directory=ROOT)).serve_forever, daemon=True).start()
URL = "http://127.0.0.1:%d/index.html" % PORT

SEEN = ("localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');"
        "localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');"
        "localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');"
        "localStorage.setItem('class26e.penal256578.seen','1');localStorage.setItem('class26e.savecode.card','1');"
        "localStorage.setItem('class26e.weekrecap.v1','9999-12-31');localStorage.setItem('class26e.daily.seen','x');")
def store(**extra):
    d = {"firstName": "Gate Tester", "avatarChar": "ninja", "onboardingComplete": True, "leaderboardOptIn": False,
         "tourRev": 999, "novaMet": 99, "lastModified": 1790400000000, "seenSettingsTour": True, "seenProfileTour": True,
         "seenMainMenuTour": True, "novaHeard": {"@recap": 99991231}, "savedCodeSaved": True,
         "lifetime": {"points": 420, "correct": 88}, "testStats": {"Penal Code": {"plays": 1}}}
    d.update(extra)
    return d
def init_for(cls):
    if cls == "ifc":
        st = store(publicId="xph5b57jbp5a", classes=["academy", "ifc"])
        return SEEN + "localStorage.setItem('class26e.drill.v1', %s);" % json.dumps(json.dumps(st)) + \
            "localStorage.setItem('class26e.synccode','GATE-0384');localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.greet.ifc','done');"
    return SEEN + "localStorage.setItem('class26e.drill.v1', %s);" % json.dumps(json.dumps(store())) + "localStorage.setItem('class26e.synccode','GATE-0384');"
# every fetch of version.json, with its cache mode
FETCH_LOG = """(()=>{ const real = window.fetch; window.__vj = [];
  window.fetch = function(u, o){ try{ const s = String((u && u.url) || u); if(s.indexOf('version.json') >= 0) window.__vj.push({ cache: (o && o.cache) || '', t: Date.now() }); }catch(e){}
    return real.apply(this, arguments); }; })();"""

fails = []
def ck(name, ok, detail=""):
    print("  %-4s %s%s" % ("PASS" if ok else "FAIL", name, ("  -> " + str(detail)[:400]) if (not ok and detail != "") else ""), flush=True)
    if not ok: fails.append(name)

SERVE = {"mode": "same", "note": ""}
HELD = []
def vj_route(route):
    m = SERVE["mode"]
    if m == "hold": HELD.append(route); return
    if m == "404": return route.fulfill(status=404, body="not found")
    if m == "abort": return route.abort()
    b = NEWER if m == "new" else BUILD
    route.fulfill(status=200, headers={"content-type": "application/json"},
                  body=json.dumps({"build": b, "note": SERVE["note"], "frameId": "", "frameNote": "", "force": False}))
def release(pg, mode="same"):
    SERVE["mode"] = mode
    while HELD:
        r = HELD.pop(0)
        try: vj_route(r)
        except Exception: pass

# WAITS ARE CONDITIONS, NOT CLOCKS: a shared machine (load 70 at 384.106) can take seconds over a fulfilled request, and a fixed
# wait then reads "still checking" as a failure. Each wait polls for what it is waiting for, up to a ceiling.
ANSWERED = "()=>{ const st=document.querySelector('#stage .screen-settings-sub [role=status]'); return !st || st.getAttribute('aria-busy') === 'false'; }"   # (no status at all: nothing to wait for)
SETTLED = "()=>{ try{ return swuCheckOut === null; }catch(e){ return true; } }"
HASPILL = "()=>{ const r=document.querySelector('#stage [data-row=update]'); return !!(r && r.querySelector('.settings-pill')); }"
def until(pg, js, ms=10000, step=200, least=0):
    if least: pg.wait_for_timeout(least)
    t = 0
    while t < ms:
        if pg.evaluate(js): return True
        pg.wait_for_timeout(step); t += step
    return bool(pg.evaluate(js))

def open_page(br, cls="academy", w=440, h=956, errs=None):
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=2)
    ctx.add_init_script("try{" + init_for(cls) + "}catch(e){}")
    ctx.add_init_script(FETCH_LOG)
    pg = ctx.new_page()
    if errs is not None: pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.route("**/index.html", lambda r: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    pg.route("**/version.json*", vj_route)
    SERVE["mode"] = "same"; SERVE["note"] = ""
    pg.goto(URL, timeout=180000); pg.wait_for_timeout(2800)
    pg.evaluate("""()=>{ document.getElementById('splashscreen')?.remove();
      try{ const u=pendingHomeUnlocks(); markUnlocksShown(u.chars,u.banners,u.fx); }catch(e){} try{ homeUnlocksOwed=()=>false; }catch(e){}
      document.querySelectorAll('.rs-spot, .daily-alert, #intro-pop, #nova-intro').forEach(n=>n.remove()); document.body.classList.remove('cutscene-focus');
      window.__applied = 0; applyUpdate = async function(){ window.__applied++; };
      window.__realCheck = checkForUpdate; }""")
    pg.wait_for_timeout(300)
    return ctx, pg

# ---- probes (they tolerate a build without the page) ----
OPEN = "()=>{ if(typeof showSoftwareUpdate === 'function') showSoftwareUpdate(); else { showAppearance(); const r=document.querySelector('#stage [data-row=update]'); if(r) r.click(); } }"
STATE = r"""()=>{ const P=document.querySelector('#stage .screen-settings-sub'); if(!P) return null;
  const vis=e=>{ const b=e.getBoundingClientRect(); return b.width>0 && b.height>0 && getComputedStyle(e).visibility!=='hidden'; };
  const st=P.querySelector('[role=status]');
  const spin=st ? [...st.querySelectorAll('*')].some(e=>e.getAnimations && e.getAnimations().some(a=>a.playState==='running' && /rotate|spin/i.test(String(a.animationName||'') + JSON.stringify((a.effect&&a.effect.getKeyframes&&a.effect.getKeyframes())||[])))) : false;
  const btns=st ? [...st.querySelectorAll('button')].filter(vis) : [];
  const after=[...P.children].slice([...P.children].indexOf(st)+1).map(n=>(n.innerText||'').trim()).join(' ').trim();
  const img=P.querySelector('img'); const lk=document.querySelector('link[rel="icon"][href^="data:image"]') || document.querySelector('link[rel="apple-touch-icon"]');
  return { back: !!P.querySelector('.settings-nav-back'), status: !!st, busy: st ? st.getAttribute('aria-busy') : null, spin,
    buttons: btns.map(b=>{ const r=b.getBoundingClientRect(), cs=getComputedStyle(b); return { h: r.height, w: r.width, bg: cs.backgroundColor, fg: cs.color, disabled: b.disabled }; }),
    text: st ? st.innerText : '', page: P.innerText, after, icon: !!(img && lk && img.src === lk.href && vis(img)),
    /* the icon's card: a line that is not the build (the name) and a line that is */
    head: (()=>{ const c=img && img.closest('.settings-card'); if(!c) return []; return c.innerText.split('\n').map(t=>t.trim()).filter(Boolean); })(),
    state: P.dataset.state || '' }; }"""
REQ = "()=>(window.__vj||[]).filter(x=>x.cache==='reload').length"
ALL = "()=>(window.__vj||[]).length"
LIT = "()=>{ const b=document.getElementById('bottomtabs'); if(!b || b.hidden) return null; const a=b.querySelector('.active[aria-current=page], [aria-current=page]'); return a ? a.id : ''; }"
SIG = """()=>{ const p=document.createElement('i'); p.style.cssText='position:fixed;left:-9px;top:0;width:1px;height:1px;background:var(--theme-sig)'; document.body.appendChild(p);
  const c=getComputedStyle(p).backgroundColor; p.remove(); return c; }"""
ROWPILL = """()=>{ const r=document.querySelector('#stage [data-row=update]'); if(!r) return { row: false };
  const p=r.querySelector('.settings-pill'); const vis=p && p.getBoundingClientRect().width>0;
  return { row: true, pill: !!vis, cls: p ? p.className : '', bg: p ? getComputedStyle(p).backgroundColor : '', fg: p ? getComputedStyle(p).color : '', words: p ? p.textContent : '' }; }"""
NOCHECK = "()=>{ checkForUpdate = async function(){}; }"
ROWDBG = """()=>{ const r=document.querySelector('#stage [data-row=update]'); const o={ row: !!r, swu: r && r.dataset.swu, vj: (window.__vj||[]).map(x=>x.cache) };
  try{ Object.assign(o, { known: swuKnown, asked: swuRowAskedAt, out: !!swuCheckOut, lu: lastUpdateCheck, inf: updateCheckInFlight, now: Date.now() }); }catch(e){} return o; }"""
REALCHECK = "()=>{ checkForUpdate = window.__realCheck; }"
RESET_ROW = "()=>{ try{ swuKnown = null; }catch(e){} try{ swuRowAskedAt = 0; }catch(e){} try{ lastUpdateCheck = 0; updateCheckInFlight = 0; }catch(e){} window.__vj.length = 0; }"
SHOW_ROW = "()=>{ showAppearance(); const r=document.querySelector('#stage [data-row=update]'); if(r){ const de=document.documentElement, w=de.style.scrollBehavior; de.style.scrollBehavior='auto'; window.scrollTo(0, Math.max(0, r.getBoundingClientRect().top + scrollY - 300)); de.style.scrollBehavior=w; } }"

def rgb(s):
    v = [float(x) for x in re.findall(r"[\d.]+", s or "")[:4]]
    if not v: return None
    if (s or "").startswith("color("): v = [x * 255 for x in v[:3]] + v[3:]
    return v
def lum(c):
    def ch(x):
        x = x / 255
        return x / 12.92 if x <= .03928 else ((x + .055) / 1.055) ** 2.4
    return .2126 * ch(c[0]) + .7152 * ch(c[1]) + .0722 * ch(c[2])
def contrast(a, b):
    la, lb = lum(a), lum(b)
    return (max(la, lb) + .05) / (min(la, lb) + .05)
def same_colour(a, b, tol=6):
    a, b = rgb(a), rgb(b)
    return bool(a and b) and all(abs(x - y) <= tol for x, y in zip(a[:3], b[:3]))
def hue(c):
    c = rgb(c)
    if not c: return None
    h, l, s = colorsys.rgb_to_hls(*[x / 255 for x in c[:3]]); return round(h * 360)

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME)
    errs = []

    print("\n(1)-(8) the page, Police Academy, iPhone 17 Pro Max")
    ctx, pg = open_page(br, errs=errs)
    pg.evaluate("()=>showAppearance()"); pg.wait_for_timeout(900)
    lit0 = pg.evaluate(LIT)
    pg.evaluate("()=>{ window.__vj.length = 0; }")
    tapped = pg.evaluate("()=>{ const r=document.querySelector('#stage [data-row=update]'); if(!r) return false; r.click(); return true; }")
    until(pg, ANSWERED, least=900)
    s = pg.evaluate(STATE); lit1 = pg.evaluate(LIT); n = pg.evaluate(REQ)
    ck("(1) the Settings row opens a pushed page with its back button (tapped %s, page %s)" % (tapped, bool(s)), tapped and s and s["back"] and s["status"], s)
    ck("(1) the tab bar stays up with the same tab lit (%s -> %s)" % (lit0, lit1), lit0 and lit0 == lit1, [lit0, lit1])
    ck("(1) the page asks for version.json itself as it opens, cache reload (%s request)" % n, n == 1, pg.evaluate("()=>window.__vj"))
    hd = (s or {}).get("head") or []
    ck("(2) the head: the app's icon, and beside it a name and the build running (%s)" % hd, s and s["icon"] and any(BUILD in t for t in hd) and any(t and BUILD not in t for t in hd), s and {k: s[k] for k in ("icon", "head")})

    pg.evaluate(NOCHECK)
    SERVE["mode"] = "hold"
    pg.evaluate(OPEN); pg.wait_for_timeout(350)
    s = pg.evaluate(STATE)
    ck("(3) checking: a turning spinner in the status, busy, and no button", s and s["spin"] and s["busy"] == "true" and not s["buttons"], s and {k: s[k] for k in ("spin", "busy", "buttons", "state")})
    pg.wait_for_timeout(1200)
    s2 = pg.evaluate(STATE)
    ck("(3) ...and it stays that way while the request is out (1.5s)", s2 and s2["spin"] and not s2["buttons"], s2 and s2["state"])
    release(pg, "same"); until(pg, ANSWERED, least=300)
    s = pg.evaluate(STATE)
    ck("(4) same build: no button, the build running, the time it checked (%r)" % (s and s["text"][-60:]), s and not s["buttons"] and not s["spin"] and BUILD in s["text"] and re.search(r"\b\d{1,2}[:.]\d{2}\b", s["text"]), s)

    sig = pg.evaluate(SIG)
    for note in ("A line of what this build fixes.", ""):
        SERVE["mode"] = "new"; SERVE["note"] = note
        pg.evaluate(OPEN); until(pg, ANSWERED, least=300)
        s = pg.evaluate(STATE)
        b = s["buttons"][0] if s and len(s["buttons"]) == 1 else None
        ck("(5) a newer build (note %r): the new build and ONE button in the theme's colour, 44px+ (%s)" % (note[:12], b), s and NEWER in s["text"] and b and b["h"] >= 44 and same_colour(b["bg"], sig), [s and s["text"], b, sig])
        ck("(5) what's new is the note and nothing else (%r)" % (s and s["after"][:80]), s and ((note in s["after"]) if note else s["after"] == ""), s and s["after"])
    SERVE["note"] = ""
    pg.evaluate("()=>{ window.__applied = 0; }")
    r = pg.evaluate("""async ()=>{ const b=document.querySelector('#stage [role=status] button'); if(!b) return null; b.click(); b.click();
      await new Promise(r=>setTimeout(r, 1500)); return { applied: window.__applied, bars: document.querySelectorAll('#pushing-update').length,
      forced: (()=>{ try{ return !!forcedUpdateStarted; }catch(e){ return null; } })() }; }""")
    ck("(5) Update Now tapped twice: the Pushing update bar, applyUpdate once, the automatic forced push not fired (%s)" % r, r and r["applied"] == 1 and r["bars"] == 1 and r["forced"] is False, r)
    pg.evaluate("()=>{ document.querySelectorAll('#pushing-update').forEach(n=>n.remove()); document.documentElement.classList.remove('is-reloading'); }")

    for mode in ("404", "abort"):
        SERVE["mode"] = mode
        pg.evaluate(OPEN); until(pg, ANSWERED, least=300)
        s = pg.evaluate(STATE)
        ck("(6) %s: says it could not check, with one button" % ("a 404" if mode == "404" else "a blocked request"), s and len(s["buttons"]) == 1 and not s["spin"] and NEWER not in s["text"], s and {k: s[k] for k in ("buttons", "text", "state")})
    SERVE["mode"] = "hold"
    pg.evaluate("()=>{ window.__vj.length = 0; }")
    r = pg.evaluate("""async ()=>{ const b=document.querySelector('#stage [role=status] button'); if(!b) return null; b.click(); b.click(); b.click();
      await new Promise(r=>setTimeout(r, 250)); const sp=document.querySelector('#stage [role=status] button'); return { again: !!sp }; }""")
    s = pg.evaluate(STATE); n = pg.evaluate(REQ)
    ck("(6) Try again tapped three times: checking again, ONE request (%s)" % n, r is not None and s and s["spin"] and n == 1, [r, n, s and s["state"]])
    release(pg, "404"); until(pg, ANSWERED, least=300)

    # (7) the row tapped twice
    SERVE["mode"] = "same"
    pg.evaluate("()=>showAppearance()"); pg.wait_for_timeout(700)
    pg.evaluate("()=>{ window.__vj.length = 0; const r=document.querySelector('#stage [data-row=update]'); if(r){ r.click(); r.click(); } }")
    until(pg, ANSWERED, least=900)
    n1 = pg.evaluate(REQ)
    pg.evaluate("()=>showAppearance()"); pg.wait_for_timeout(700)
    box = pg.evaluate("()=>{ const r=document.querySelector('#stage [data-row=update]'); if(!r) return null; r.scrollIntoView({block:'center', behavior:'instant'}); const b=r.getBoundingClientRect(); return { x: b.left + b.width / 2, y: b.top + b.height / 2 }; }")
    pg.wait_for_timeout(300)
    pg.evaluate("()=>{ window.__vj.length = 0; }")
    if box: pg.mouse.dblclick(box["x"], box["y"])
    until(pg, ANSWERED, least=900)
    n2 = pg.evaluate(REQ)
    ck("(7) the row tapped twice asks once (by script %s, a real double tap %s)" % (n1, n2), n1 == 1 and n2 == 1, [n1, n2])

    # (8) Back
    s = pg.evaluate(STATE)
    pg.evaluate("()=>{ const b=document.querySelector('#stage .screen-settings-sub .settings-nav-back'); if(b) b.click(); }"); pg.wait_for_timeout(900)
    back = pg.evaluate("()=>({ menu: [...document.querySelectorAll('#stage .screen-settings')].some(e=>!e.closest('[hidden]') && e.getBoundingClientRect().height>0), row: !!document.querySelector('#stage [data-row=update]'), sub: !!document.querySelector('#stage .screen-settings-sub') })")
    ck("(8) Back returns to Settings' menu, the row on it (%s)" % back, s and back["menu"] and back["row"] and not back["sub"], back)
    ck("(8) the same tab lit on the menu after Back (%s)" % pg.evaluate(LIT), pg.evaluate(LIT) == lit0, [lit0, pg.evaluate(LIT)])

    # (9) the row's pill
    print("\n(9) the row's pill")
    pg.evaluate(NOCHECK); pg.evaluate(RESET_ROW); SERVE["mode"] = "hold"
    pg.evaluate(SHOW_ROW); pg.wait_for_timeout(600)
    p = pg.evaluate(ROWPILL); n = pg.evaluate(REQ)
    ck("(9) no answer yet this session: the row comes into view and asks once, and shows nothing while it is out (%s, %s request)" % (p.get("pill"), n), p["row"] and not p["pill"] and n == 1, [p, n])
    release(pg, "same"); until(pg, HASPILL, least=200)
    p = pg.evaluate(ROWPILL)
    ck("(9) its answer: a green pill on the row (%s, hue %s)" % (p.get("words"), hue(p.get("bg"))), p["pill"] and "is-good" in p["cls"] and 90 <= (hue(p["bg"]) or 0) <= 150, p)
    pg.evaluate("()=>{ window.__vj.length = 0; }")
    pg.evaluate(SHOW_ROW)
    p0 = pg.evaluate(ROWPILL); pg.wait_for_timeout(800); n = pg.evaluate(REQ)
    ck("(9) Settings again within the minute: the pill at once, no request (%s, %s)" % (p0.get("pill"), n), p0["pill"] and n == 0, [p0, n])
    # hidden
    pg.evaluate(RESET_ROW)
    pg.evaluate("()=>{ showHome(); const d=document.createElement('div'); d.id='__hid'; d.hidden=true; document.getElementById('stage').appendChild(d); showAppearance({ into: d }); }")
    pg.wait_for_timeout(900); nh = pg.evaluate(REQ)
    pg.evaluate("()=>{ const d=document.getElementById('__hid'); if(d) d.hidden=false; const r=d && d.querySelector('[data-row=update]'); if(r) r.scrollIntoView({block:'center', behavior:'instant'}); }")
    until(pg, "()=>!!document.querySelector('#__hid [data-row=update] .settings-pill')", least=300); ns = pg.evaluate(REQ)
    ph = pg.evaluate("()=>{ const r=document.querySelector('#__hid [data-row=update]'); const p=r && r.querySelector('.settings-pill'); return !!p; }")
    ck("(9) a row out of sight asks nothing (%s); shown, it asks once and fills in (%s, pill %s)" % (nh, ns, ph), nh == 0 and ns == 1 and ph, [nh, ns, ph])
    pg.evaluate("()=>document.getElementById('__hid')?.remove()")
    # the app's own check
    pg.evaluate(REALCHECK); pg.evaluate(RESET_ROW)
    pg.evaluate(SHOW_ROW); until(pg, HASPILL, least=400)
    p = pg.evaluate(ROWPILL); vj = pg.evaluate("()=>window.__vj.map(x=>x.cache)")
    ck("(9) with the app's own check running as Settings opens, the row reuses its answer and asks nothing itself (%s, requests %s)" % (p.get("pill"), vj), p["pill"] and pg.evaluate(REQ) == 0 and len(vj) >= 1, [p, vj])
    pg.evaluate(NOCHECK)
    # newer -> accent; failed / stale -> nothing
    pg.evaluate(RESET_ROW); SERVE["mode"] = "new"
    pg.evaluate(SHOW_ROW); until(pg, HASPILL, least=400)
    p = pg.evaluate(ROWPILL)
    ck("(9) a newer build: the pill in the theme's colour (%s)" % p.get("words"), p["pill"] and "is-accent" in p["cls"] and same_colour(p["bg"], sig), [p, sig])
    pg.evaluate(RESET_ROW); SERVE["mode"] = "404"
    pg.evaluate(SHOW_ROW); until(pg, "()=>(window.__vj||[]).some(x=>x.cache==='reload')", least=400); until(pg, SETTLED); pg.wait_for_timeout(300)
    p = pg.evaluate(ROWPILL); n = pg.evaluate(REQ)
    ck("(9) a failed check shows nothing (asked %s)" % n, p["row"] and not p["pill"] and n == 1, [p, n])
    pg.evaluate(RESET_ROW); SERVE["mode"] = "hold"
    pg.evaluate("()=>{ try{ swuKnown = { build: APP_BUILD, at: Date.now() - 5 * 60 * 1000 }; }catch(e){} }")
    pg.evaluate(SHOW_ROW); pg.wait_for_timeout(700)
    p = pg.evaluate(ROWPILL); n = pg.evaluate(REQ)
    ck("(9) an answer five minutes old is not shown; the row asks afresh (%s request) and shows nothing meanwhile" % n, p["row"] and not p["pill"] and n == 1, [p, n])
    release(pg, "same"); pg.wait_for_timeout(500)
    pg.evaluate(REALCHECK)
    ctx.close()

    # (10) the pill's shape
    print("\n(10) the pill's shape, at 440px, 320px and on an iPad")
    PILLGEO = r"""()=>{ const r=document.querySelector('#stage [data-row=update]'); const p=r && r.querySelector('.settings-pill'); if(!p) return null;
      const lab=r.querySelector('.settings-row-label'), ch=r.querySelector('.settings-row-chev');
      const rb=r.getBoundingClientRect(), pb=p.getBoundingClientRect(), lb=lab.getBoundingClientRect(), cb=ch.getBoundingClientRect();
      const g=document.createRange(); g.selectNodeContents(p); const lines=[...g.getClientRects()].filter(q=>q.width>1).length;
      const ps=getComputedStyle(p), ls=getComputedStyle(lab);
      return { h: pb.height, w: pb.width, lf: parseFloat(ls.fontSize), pf: parseFloat(ps.fontSize), wt: parseFloat(ps.fontWeight), pl: parseFloat(ps.paddingLeft), pr: parseFloat(ps.paddingRight),
        lines, over: p.scrollWidth - p.clientWidth, mid: (pb.top + pb.height / 2) - (rb.top + rb.height / 2),
        afterLabel: pb.left - lb.right, beforeChev: cb.left - pb.right, inRow: pb.left >= rb.left && pb.right <= rb.right, rowR: rb.right, vw: innerWidth }; }"""
    for (w, h, label) in ((440, 956, "iPhone 17 Pro Max"), (320, 568, "320px phone"), (834, 1194, "iPad Pro 11\"")):
        ctx, pg = open_page(br, w=w, h=h, errs=errs)
        for mode in ("same", "new"):
            SERVE["mode"] = mode
            pg.evaluate(NOCHECK); pg.evaluate(RESET_ROW); pg.evaluate(SHOW_ROW); until(pg, HASPILL, ms=20000, least=400); pg.wait_for_timeout(200)
            g = pg.evaluate(PILLGEO)
            if not g: g = None; print("     (no pill: %s)" % pg.evaluate(ROWDBG))
            okg = g and 0.95 <= g["h"] / g["lf"] <= 1.3 and 0.6 <= g["pf"] / g["lf"] <= 0.82 and g["wt"] >= 600 and g["lines"] == 1 and g["over"] <= 0 \
                and abs(g["mid"]) <= 1 and g["afterLabel"] >= 4 and g["beforeChev"] >= 0 and g["inRow"] and 6 <= g["pl"] <= 12 and abs(g["pl"] - g["pr"]) < .5
            ck("(10) %s, %s: %s" % (label, "up to date" if mode == "same" else "update available",
                g and "%.0fx%.0f, %.2f of the words tall, words %.2f at %d, %d line, %+.1fpx off the middle" % (g["w"], g["h"], g["h"] / g["lf"], g["pf"] / g["lf"], g["wt"], g["lines"], g["mid"])), okg, g)
        ctx.close()

    # (11) every state, every size, every theme
    print("\n(11) every state on a phone and an iPad both ways, a 320px phone; every theme")
    LAYOUT = r"""()=>{ const P=document.querySelector('#stage .screen-settings-sub'); if(!P) return { page: false };
      const vw=innerWidth, de=document.documentElement; const bad=[];
      if(de.scrollWidth > vw + 1) bad.push('page scrolls sideways ' + de.scrollWidth);
      P.querySelectorAll('*').forEach(e=>{ const b=e.getBoundingClientRect(); if(b.width && (b.right > vw + .5 || b.left < -.5)) bad.push((e.className||e.tagName) + ' ' + Math.round(b.left) + '..' + Math.round(b.right)); });
      P.querySelectorAll('button').forEach(b=>{ const r=b.getBoundingClientRect(); if(r.width && (r.height < 44 || r.width < 44)) bad.push('tap ' + (b.className||'') + ' ' + Math.round(r.width) + 'x' + Math.round(r.height)); });
      return { page: true, state: P.dataset.state || '', bad: bad.slice(0, 6) }; }"""
    SIZES = ((440, 956), (956, 440), (834, 1194), (1194, 834), (320, 568))
    seen = {}
    for (w, h) in SIZES:
        ctx, pg = open_page(br, w=w, h=h, errs=errs)
        pg.evaluate(NOCHECK)
        for mode in ("hold", "same", "new", "404"):
            SERVE["mode"] = mode
            pg.evaluate(OPEN)
            if mode == "hold": pg.wait_for_timeout(400)
            else: until(pg, ANSWERED, least=300)
            L = pg.evaluate(LAYOUT)
            seen["%dx%d %s" % (w, h, mode)] = L.get("state")
            ck("(11) %dx%d, %s: %s" % (w, h, {"hold": "checking", "same": "up to date", "new": "update available", "404": "can't reach"}[mode], L.get("bad") or "clean"), L["page"] and not L["bad"], L)
            if mode == "hold": release(pg, "same"); until(pg, ANSWERED, least=300)
        ctx.close()
    ctx, pg = open_page(br, errs=errs)
    pg.evaluate(NOCHECK)
    accents = pg.evaluate("()=>(typeof ACCENTS !== 'undefined' ? ACCENTS.slice() : ['ink'])")
    badt = []
    for acc in accents:
        pg.evaluate("(a)=>{ theme.accent=a; applyTheme(); }", acc)
        sig = pg.evaluate(SIG)
        SERVE["mode"] = "new"
        pg.evaluate(OPEN); until(pg, ANSWERED, least=300)
        s = pg.evaluate(STATE)
        b = s["buttons"][0] if s and s["buttons"] else None
        if not (b and same_colour(b["bg"], sig) and contrast(rgb(b["fg"]), rgb(b["bg"])) >= 3):
            badt.append((acc, "button", b and b["bg"], b and b["fg"], sig, b and round(contrast(rgb(b["fg"]), rgb(b["bg"])), 2)))
        pg.evaluate(RESET_ROW); pg.evaluate(SHOW_ROW); until(pg, HASPILL, least=400)
        p = pg.evaluate(ROWPILL)
        if not (p["pill"] and same_colour(p["bg"], sig) and contrast(rgb(p["fg"]), rgb(p["bg"])) >= 3):
            badt.append((acc, "pill", p.get("bg"), p.get("fg"), sig))
    ck("(11) every theme (%d): Update Now and the update pill are the theme's colour, words 3:1+ on it" % len(accents), not badt and len(accents) >= 7, badt[:4])
    ctx.close()

    # both classes: the row opens the page, Back returns, the same tab lit
    print("\n(8) Fire Code")
    ctx, pg = open_page(br, cls="ifc", errs=errs)
    cls = pg.evaluate("()=>window.NOVA_CLASS")
    pg.evaluate("()=>showAppearance()"); pg.wait_for_timeout(900)
    lit0 = pg.evaluate(LIT)
    pg.evaluate("()=>{ window.__vj.length = 0; const r=document.querySelector('#stage [data-row=update]'); if(r) r.click(); }"); until(pg, ANSWERED, least=900)
    s = pg.evaluate(STATE); lit1 = pg.evaluate(LIT); n = pg.evaluate(REQ)
    pg.evaluate("()=>{ const b=document.querySelector('#stage .screen-settings-sub .settings-nav-back'); if(b) b.click(); }"); pg.wait_for_timeout(900)
    back = pg.evaluate("()=>({ row: !!document.querySelector('#stage [data-row=update]'), sub: !!document.querySelector('#stage .screen-settings-sub') })")
    lit2 = pg.evaluate(LIT)
    ck("(8) Fire Code (%s): the row opens the page and asks once (%s), Back returns to the menu, the same tab lit (%s %s %s)" % (cls, n, lit0, lit1, lit2),
       cls == "ifc" and s and s["status"] and n == 1 and back["row"] and not back["sub"] and lit0 and lit0 == lit1 == lit2, [s and s["state"], back])
    ctx.close()

    ck("(12) no page errors", not errs, errs[:4])
    br.close()
print("\nALL PASS" if not fails else "\nFAILED: %d" % len(fails))
sys.exit(1 if fails else 0)
