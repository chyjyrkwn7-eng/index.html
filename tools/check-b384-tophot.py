#!/usr/bin/env python3
"""Build 384.75 (hot fix): THE TOP OF A QUESTION IS ONE PINNED, OPAQUE UNIT, AND NOTHING SCROLLED SHOWS UNDER THE STATUS BAR.

Madison's recording of 384.70 (iPhone 17 Pro Max, installed, iOS 26, a Fire Code Drill question 1/158 scrolled up and down): the header row ("Drill", "1/158",
Pause), the progress dots, the chat button and the star sat at different heights from frame to frame; a ~40pt band of the scrolled page (the dots, the question)
showed between the status bar and the header; the question's words ran up under and through the header row; and the system's grey wash was still there.
"You did not fix the top of the screen problem. You made it so much worse AND you didn't even get rid of the thing. All you did was move stuff down???"
What this gate holds (the wash itself is drawn by iOS and Chromium cannot draw it; see docs/notes-archive.md "384.75"):
 (1) STILL   on a Drill question at installed iPhone 17 Pro Max (440x956, the island's 59px inset simulated), an SE-sized phone (375x667, 20px) and an iPad Pro 11"
             (834x1194, 24px), with two units (one whose dots fit the unit, one of 358 questions whose dots do not fit on a phone), scrolled 0, 120, 400 and to the
             bottom: the header row, Pause, the chat button and every pinned piece (the dots wherever they fit TEST_CAP_MAX of the screen, the line under them) are
             at the same rect at every scroll position (0.5px);
 (2) OPAQUE  the screenshot between y = 0 and the foot of the lowest piece, outside the pieces' own boxes, is one colour - the cap's paper - at every scroll
             position: no dot, no word of the question, no band of anything (the cap's colour read off the page, tolerance 3 levels);
 (3) UNDER   no text of the question whose box reaches into the unit is what a tap there reaches (the cap is on top of it);
 (4) STAYS   with the visual viewport reading offset by the scroll (what 384.62's heal read on his phone while a scroll was moving), the header, Pause and the chat
             button do not move;
 (5) PLACE   --sat is the raw inset again (the 42pt push-down is gone) and the header row starts where 384.62 put it (max of the inset and .wrap's 1.25rem);
 (6) STRIP   Profile, Settings and the Leaderboard scrolled: the status bar's area (0 to the inset) is one colour, nothing of the page in it;
 (7) no page errors.
Run:  python3 tools/check-b384-tophot.py [--shots DIR] [--against OLD/index.html]   (main 384.70 must FAIL (1)-(6))"""
import os, sys, io, re, json, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
args = sys.argv[1:]
SHOTS = None
if "--shots" in args:
    SHOTS = os.path.abspath(args[args.index("--shots") + 1]); os.makedirs(SHOTS, exist_ok=True)
TAG = args[args.index("--tag") + 1] if "--tag" in args else "build"
ONLY = args[args.index("--only") + 1] if "--only" in args else ""
RAW = open(args[args.index("--against") + 1] if "--against" in args else cb.SRC, encoding="utf-8").read()
_bm = re.search(r'const APP_BUILD = "([^"]+)"', RAW)
if _bm: cb.SERVED_BUILD = _bm.group(1)
def serve_with(top, bottom):
    ins = {"top": "%gpx" % top, "bottom": "%gpx" % bottom, "left": "0px", "right": "0px"}
    cb.BODY = cb.INSET_RE.sub(lambda m: ins[m.group(1)], RAW).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
from playwright.sync_api import sync_playwright
from PIL import Image
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:500], flush=True)
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1"
UA_PAD = UA.replace("iPhone; CPU iPhone OS", "iPad; CPU OS")
SEEN = ("localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
        "localStorage.setItem('class26e.weekrecap.v1','9999-12-31');localStorage.setItem('class26e.savecode.card','1');localStorage.setItem('class26e.a2hs','1790500000000');")
VVM = "window.__vvm = {follow: false}; try{ const d = Object.getOwnPropertyDescriptor(VisualViewport.prototype, 'offsetTop'); Object.defineProperty(window.visualViewport, 'offsetTop', { get(){ return window.__vvm.follow ? Math.min(500, Math.round(window.scrollY)) : d.get.call(this); }, configurable: true }); }catch(e){}"
DEVICES = [("promax", 440, 956, 59, 34, UA), ("se", 375, 667, 20, 0, UA), ("ipad11", 834, 1194, 24, 20, UA_PAD)]
errs = []
def boot(br, W, H, ua):
    ctx = br.new_context(viewport={"width": W, "height": H}, device_scale_factor=2, has_touch=True, is_mobile=True, user_agent=ua)
    ctx.add_init_script("try{%slocalStorage.setItem('class26e.drill.v1','%s');}catch(e){}" % (SEEN, cb.USED_ACCOUNT))
    ctx.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true});")
    ctx.add_init_script(VVM)
    pg = cb.open_page(ctx); pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    pg.goto(cb.URL); pg.wait_for_timeout(2500)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); }"); pg.wait_for_timeout(700)
    return ctx, pg
# the unit whose size is nearest his Fire Code chapter (158), and the biggest
UNITS = """()=>{ const c = {}; QUESTIONS.forEach(q => c[q.topic] = (c[q.topic] || 0) + 1); const e = Object.entries(c);
  const mid = e.slice().sort((a, b) => Math.abs(a[1] - 158) - Math.abs(b[1] - 158))[0]; const big = e.slice().sort((a, b) => b[1] - a[1])[0]; return [mid, big]; }"""
START = """(u)=>{ showHome(); cfg.mode='drill'; cfg.units=[u]; cfg.versions={}; cfg.source='all'; cfg.size=0; cfg.timer='off'; cfg.flashcards=false; theme.autoAdvance=false; theme.reduceMotion=true;
  beginRun(freshOrder(QUESTIONS.map((q,i)=>i).filter(i=>QUESTIONS[i].topic===u)), null); }"""
# every piece of the top of a question, as rects; the content's text lines; the cap's colour
READ = """()=>{ const R = e => { if(!e) return null; const cs = getComputedStyle(e); if(cs.display === 'none' || cs.visibility === 'hidden') return null; const r = e.getBoundingClientRect(); if(!r.width || !r.height) return null;
    return [r.left, r.top, r.right, r.bottom].map(v => Math.round(v * 10) / 10); };
  const top = document.querySelector('.wrap > .top'), pinned = {};
  pinned.header = R(top); pinned.pause = R(document.getElementById('pausebtn')); pinned.chat = R(document.getElementById('chatdock-btn'));
  for(const id of ['meter', 'timerline', 'count']){ const e = document.getElementById(id); if(e && e.parentElement && e.parentElement.classList.contains('wrap')) pinned[id] = R(e); }
  /* the boxes the pixel scan leaves out: every painted descendant of the header, Pause, the chat button (with its badge), the pinned pieces */
  const holes = [];
  const add = e => { const r = R(e); if(r) holes.push(r); };
  if(top) top.querySelectorAll('*').forEach(add);
  ['pausebtn', 'chatdock-btn'].forEach(id => { const e = document.getElementById(id); if(e){ add(e); e.querySelectorAll('*').forEach(add); } });
  const pins = ['meter', 'timerline', 'count'].map(id => document.getElementById(id)).filter(e => e && getComputedStyle(e).position === 'fixed');
  pins.forEach(e => { add(e); e.querySelectorAll('*').forEach(add); });
  const p = document.createElement('i'); p.style.cssText = 'position:absolute;width:0;height:0;color:var(--paper)'; document.body.appendChild(p); const paper = getComputedStyle(p).color; p.remove();
  /* the unit's foot: the lowest piece that holds its place (header row, Pause, chat, fixed pieces) */
  const lows = [pinned.header, pinned.pause, pinned.chat].concat(pins.map(R)).filter(Boolean).map(r => r[3]);
  const foot = Math.max.apply(null, lows);
  /* the question's text lines that reach into the unit */
  const lines = []; const st = document.getElementById('stage');
  if(st){ const w = document.createTreeWalker(st, NodeFilter.SHOW_TEXT); let n; while((n = w.nextNode())){ if(!n.textContent.trim()) continue; const rg = document.createRange(); rg.selectNodeContents(n);
    for(const r of rg.getClientRects()){ if(r.width < 4 || r.bottom <= 0 || r.top >= foot) continue; const x = Math.min(innerWidth - 2, Math.max(1, r.left + r.width / 2)), y = Math.max(1, (Math.max(0, r.top) + Math.min(foot, r.bottom)) / 2);
      const hit = document.elementFromPoint(x, y); lines.push({ t: n.textContent.trim().slice(0, 24), y: Math.round(r.top), hitContent: !!(hit && st.contains(hit)) }); } } }
  const cs0 = getComputedStyle(document.documentElement);
  return { y: scrollY, maxY: document.documentElement.scrollHeight - innerHeight, pinned, holes, paper, foot, lines, ih: innerHeight,
           sat: (() => { const q = document.createElement('i'); q.style.cssText = 'position:fixed;top:0;width:0;height:var(--sat, 0px)'; document.body.appendChild(q); const h = q.getBoundingClientRect().height; q.remove(); return h; })(),
           pad: parseFloat(getComputedStyle(document.querySelector('.wrap')).getPropertyValue('--test-top-y')) || null,
           capPieces: !!document.querySelector('.wrap.cap-pieces'), meterRest: null }; }"""
def rgb(s):
    m = re.findall(r"[\d.]+", s or ""); v = [float(x) for x in m[:3]]
    return tuple(round(c * 255) if "srgb" in (s or "") else round(c) for c in v) if len(v) == 3 else None
def scan(im, d, scale=2):
    """every 5th pixel between y = 0 and the unit's foot, outside the pieces' boxes (padded 8px for glow and shadow), against the cap's colour"""
    paper = rgb(d["paper"]); foot = d["foot"]; holes = [[h[0] - 8, h[1] - 8, h[2] + 8, h[3] + 8] for h in d["holes"]]
    bad = []; n = 0
    for y in range(0, int(foot) - 1, 5):
        for x in range(2, int(im.width / scale) - 2, 5):
            if any(h[0] <= x <= h[2] and h[1] <= y <= h[3] for h in holes): continue
            px = im.getpixel((x * scale, y * scale))[:3]; n += 1
            if max(abs(a - b) for a, b in zip(px, paper)) > 3: bad.append((x, y, px))
    return n, bad, paper
def question(br, dev, which):
    name, W, H, top, bottom, ua = dev
    serve_with(top, bottom)
    ctx, pg = boot(br, W, H, ua)
    mid, big = pg.evaluate(UNITS); unit = (mid if which == "mid" else big)
    pg.evaluate(START, unit[0]); pg.wait_for_selector(".qpanel .choice", timeout=25000); pg.wait_for_timeout(1300)
    pg.evaluate("()=>{ document.querySelectorAll('.intro-pop,#intro-pop,.unlock-card,.rs-spot').forEach(n=>n.remove()); }")
    # the question given the length a long one with its code card has (harness only: a spacer at the end of the question's own panel)
    pg.evaluate("()=>{ const d = document.createElement('div'); d.className = 'harness-len'; d.style.cssText = 'height:1600px;pointer-events:none'; (document.querySelector('#stage .qpanel') || document.getElementById('stage')).appendChild(d); }")
    pg.wait_for_timeout(500)
    label = "%s, %s (%s, %d questions)" % (name, which, unit[0], unit[1])
    rows = {}
    for y in (0, 120, 400, "bottom"):
        pg.evaluate("(y)=>window.scrollTo({top: y === 'bottom' ? document.documentElement.scrollHeight : y, behavior:'instant'})", y); pg.wait_for_timeout(450)
        d = pg.evaluate(READ); b = pg.screenshot(); im = Image.open(io.BytesIO(b)).convert("RGB")
        if SHOTS and which == "mid": im.save(os.path.join(SHOTS, "%s__%s__question_%s.png" % (TAG, name, y)))
        rows[y] = d
        n, bad, paper = scan(im, d)
        chk("%s scrolled %s (y %d): between the top of the screen and the unit's foot (%.0f) every pixel outside the pieces is the cap's colour %s (%d sampled, %d off)" % (label, y, d["y"], d["foot"], paper, n, len(bad)),
            n > 50 and not bad, bad[:6])
        under = [l for l in d["lines"] if l["hitContent"]]
        chk("%s scrolled %s: no line of the question that reaches into the unit can be reached through it (%d lines there, %d reachable)" % (label, y, len(d["lines"]), len(under)), not under, under[:4])
    base = rows[0]["pinned"]
    for y in (120, 400, "bottom"):
        moved = {k: [base[k], v] for k, v in rows[y]["pinned"].items() if v != base.get(k) and not (v and base.get(k) and max(abs(a - b) for a, b in zip(v, base[k])) <= .5)}
        # a piece that does not fit the unit (the dots of a 358-question unit on a phone) is allowed to scroll - beneath the cap, which (2) holds
        fits = rows[0]["pinned"].get("meter") and rows[0]["pinned"]["meter"][3] <= rows[0]["ih"] * .45
        if not fits: moved = {k: v for k, v in moved.items() if k not in ("meter", "timerline", "count")}
        chk("%s: scrolled %s every piece of the top is where it was at 0 (%s; the dots %s the unit)" % (label, y, sorted(rows[y]["pinned"]), "fit" if fits else "do not fit"), not moved, moved)
    if which == "mid" and rows[0]["pinned"].get("meter") and rows[0]["pinned"]["meter"][3] <= rows[0]["ih"] * .45:
        chk("%s: the dots are part of the unit (pinned; %s)" % (label, rows[0]["capPieces"]), rows[0]["capPieces"], rows[0]["pinned"])
    # (4) the visual viewport reading offset by the scroll
    pg.evaluate("()=>window.scrollTo({top:0, behavior:'instant'})"); pg.wait_for_timeout(400)
    a = pg.evaluate(READ)["pinned"]
    pg.evaluate("()=>{ window.__vvm.follow = true; }")
    seen = []
    for y in (150, 350, 250):
        pg.evaluate("(y)=>window.scrollTo({top:y, behavior:'instant'})", y); pg.wait_for_timeout(420)
        b2 = pg.evaluate(READ)["pinned"]
        seen.append({k: (round(b2[k][1] - a[k][1], 1) if b2.get(k) and a.get(k) else None) for k in ("header", "pause", "chat")})
    pg.evaluate("()=>{ window.__vvm.follow = false; }")
    worst = max(abs(v) for s in seen for v in s.values() if v is not None)
    chk("%s: with the visual viewport reading offset by the scroll (the heal's mid-scroll reading) the header, Pause and the chat button do not move (worst %.1fpx: %s)" % (label, worst, seen), worst <= .5, seen)
    if which == "mid":
        d0 = rows[0]
        chk("%s: --sat is the raw inset (%.1f vs %d) - no push-down" % (label, d0["sat"], top), abs(d0["sat"] - top) < .6, d0["sat"])
        hdr = d0["pinned"]["header"][1]
        want = max(top, 20)   # .wrap's top padding is 1.25rem plus what the inset adds over it (--pad-inset-top)
        chk("%s: the header row starts where 384.62 put it: max(the inset, .wrap's 1.25rem) (%.1f, want %.1f)" % (label, hdr, want), abs(hdr - want) <= 1.5, hdr)
    ctx.close()
STRIP = """()=>{ const t = document.getElementById('top-safe') || document.getElementById('top-edge'); return { y: scrollY, maxY: document.documentElement.scrollHeight - innerHeight }; }"""
def screens(br, dev):
    name, W, H, top, bottom, ua = dev
    serve_with(top, bottom)
    ctx, pg = boot(br, W, H, ua)
    for scr, js in (("profile", "()=>showProfile()"), ("settings", "()=>showAppearance()"), ("leaderboard", "()=>showRankings()")):
        pg.evaluate("()=>showHome()"); pg.wait_for_timeout(500); pg.evaluate(js); pg.wait_for_timeout(1800)
        pg.evaluate("()=>{ document.querySelectorAll('.intro-pop,#intro-pop,.unlock-card,.rs-spot').forEach(n=>n.remove()); const d = document.createElement('div'); d.style.cssText = 'height:1400px;pointer-events:none'; document.getElementById('stage').appendChild(d); }")
        pg.wait_for_timeout(300)
        for y in (300, 700):
            pg.evaluate("(y)=>window.scrollTo({top:y, behavior:'instant'})", y); pg.wait_for_timeout(450)
            b = pg.screenshot(); im = Image.open(io.BytesIO(b)).convert("RGB")
            if SHOTS: im.save(os.path.join(SHOTS, "%s__%s__%s_%d.png" % (TAG, name, scr, y)))
            ref = im.getpixel((4, 4))[:3]; bad = []; n = 0
            for yy in range(0, max(1, top * 2) - 1, 3):
                for xx in range(4, im.width - 4, 6):
                    px = im.getpixel((xx, yy))[:3]; n += 1
                    if max(abs(a - b2) for a, b2 in zip(px, ref)) > 3: bad.append((xx // 2, yy // 2, px))
            chk("%s %s scrolled %d: the status bar's area (0-%dpx) is one colour %s, nothing of the page in it (%d sampled, %d off)" % (name, scr, y, top, ref, n, len(bad)), n > 20 and not bad, bad[:6])
    ctx.close()
def retry(fn, *a, tries=3):
    for i in range(tries):
        try:
            with sync_playwright() as pw:
                br = pw.chromium.launch(executable_path=cb.CHROME)
                try: return fn(br, *a)
                finally:
                    try: br.close()
                    except Exception: pass
        except Exception as e:
            if "closed" in repr(e).lower() or "crashed" in repr(e).lower():
                print("  (retry %d: %s)" % (i + 1, repr(e)[:80]), flush=True); continue
            raise
    raise RuntimeError("page kept crashing")
for dev in DEVICES:
    if ONLY and ONLY not in dev[0]: continue
    for which in ("mid", "big"):
        retry(question, dev, which)
    if dev[0] in ("promax", "se"): retry(screens, dev)
chk("no page errors (%d)" % len(errs), not errs, errs[:4])
print("ALL PASS" if ok else "SOME FAIL")
sys.exit(0 if ok else 1)
