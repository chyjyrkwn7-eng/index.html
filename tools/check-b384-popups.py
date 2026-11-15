#!/usr/bin/env python3
"""Build 384.100 (384.91 and 384.93 before it, on 384.95's top row): EVERY TOP POP-UP IS THE PAGE'S FULL WIDTH, ON THE ROW LINE, OVER THE
CHAT BUTTON AND PAUSE, and they get no taps while it shows.

Madison (iPhone 17 Pro Max, installed): "I feel like these pops need to be a little closer to the top. Not in the blurred area" (384.91,
384.93: in the chat button's row, stopping short of the button). Then: make them FULL WIDTH across the top and COVER the chat button (above
it; the chat button and Pause not tappable while one is shown), and fix the clipped gold left edge and the light smear on the glass.

For each device and screen, each pop-up is opened by the app's own function and read once it has settled:
 (1) ROW      its top border edge is the chat button's top (read off the live button) within 1px - the same row on every screen
              (Home, Profile, the Leaderboard, Settings, a question) - or, where the button sits higher than the bottom of iOS 26's
              blur (installed iPhone upright with a notch: 384.95's line E, --top-e - the line the whole top row sits on; nowhere
              else), that line: never above it;
 (2) WIDE     it spans the page's own content width: its left and right edges are .wrap's content box (the padding of the page's
              first .wrap, read off the page - 20px on a phone, 24px on an iPad) within 1px, the same gutter both sides, centred;
              no pop-up is narrower, whatever the pop-up (daily, Find me's answers, rank-up, tier-up, toast, battle alert, chat
              preview, streak pop, update notice, re-add notice), the chat button or Pause is in its way or not;
 (3) COVER    it is drawn over the chat button and Pause: at each one's centre the top of the hit-test stack is the pop-up, and the
              pop-up's z-index is above both; while it shows the chat button and Pause compute pointer-events none (no taps), and
              once it has gone they are the hit-test target again and take taps (computed pointer-events not none);
 (4) FITS     every line of its text fits its box (wraps, never clipped) and the box is inside the screen - on a 320px phone too;
 (5) STACK    the update notice and the daily alert up together do not overlap, the notice in the row and the alert under it
              (whichever came first); in a Safari tab's Home the Home Screen reminder (a slim centred bar, under the chat button on a
              phone, 384 r19) comes first and every other pop-up stacks under it; a tour holds the update notice back and it comes
              up in the row when the tour goes; a toast with the chat panel open is in the row, over the button;
 (6) ENTRANCE it arrives from above (its first frame is higher than where it settles);
 (7) EDGE     the glass: its coloured edge is a 1px border in the pop-up's colour plus a 2px inset line, never a 3px left border (which is
              cut off at the corners); the tint is dense enough (alpha at least .6) that what is behind it is a faint shade; pixels
              read off the screenshot: the 3px at the left edge at the box's middle are the pop-up's colour;
 (8) DISMISS  the x closes a pop-up that has one (a real tap through the screen), and a swipe up on any pop-up (real CDP touches,
              28px or more) dismisses it; a tap on the chat button's place while one shows does nothing to the chat;
 (9) no page errors.
Pop-ups: the daily alert ("Done for today"), Find me's answer, the rank-up banner, a toast said at the top, a battle alert, a
Virtual Room chat alert, the tier banner (showTierUpBanner), the answer-streak pop (a question), the update notice and the re-add
notice (Home: they are gated to Welcome and Home).
Devices: installed iPhone 17 Pro Max (440x956, 62/34 simulated, the inset 384.95 measured), installed SE-size (375x667, 20/0), an installed 320px phone
(320x568, 20/0), installed iPad Pro 11" (834x1194, 24/20), and the Safari-tab model (440x797, no insets, not installed).
Run:  python3 tools/check-b384-popups.py [--against FILE] [--only DEVICE[,DEVICE]] [--screens home,profile,...] [--shots DIR --tag NAME]
      (384.99 / the earlier branch head (56f3e4f) must FAIL (2) and (3): there every pop-up stops short of the chat button, 16..364 on a Pro Max)"""
import os, sys, re, json, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
args = sys.argv[1:]
RAW = open(args[args.index("--against") + 1] if "--against" in args else cb.SRC, encoding="utf-8").read()
ONLY = args[args.index("--only") + 1] if "--only" in args else None
SHOTS = args[args.index("--shots") + 1] if "--shots" in args else None
TAG = args[args.index("--tag") + 1] if "--tag" in args else "after"
if SHOTS: os.makedirs(SHOTS, exist_ok=True)
from playwright.sync_api import sync_playwright
A2HS_GAP = 6        # the Home Screen reminder under the button on a phone
REM = 16
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:600], flush=True)
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1"
UA_PAD = UA.replace("iPhone; CPU iPhone OS", "iPad; CPU OS")
SEEN = ("localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
        "localStorage.setItem('class26e.weekrecap.v1','9999-12-31');localStorage.setItem('class26e.savecode.card','1');localStorage.setItem('class26e.a2hs','1790500000000');"
        "localStorage.setItem('class26e.unithold.tip','1');")
# name, W, H, inset top, inset bottom, UA, installed, wash expected
DEVICES = [("promax", 440, 956, 62, 34, UA, True, True), ("se", 375, 667, 20, 0, UA, True, False),
           ("p320", 320, 568, 20, 0, UA, True, False),
           ("ipad11", 834, 1194, 24, 20, UA_PAD, True, False), ("safari", 440, 797, 0, 0, UA, False, False)]
if ONLY: DEVICES = [d for d in DEVICES if any(o == d[0] or (o in d[0] and o != "se") for o in ONLY.split(","))]
QSTART = """()=>{ showHome(); const u = 'Arrest, Search, and Seizure'; cfg.mode='drill'; cfg.units=[u]; cfg.versions={}; cfg.source='all'; cfg.size=0; cfg.timer='off'; cfg.flashcards=false; theme.autoAdvance=false;
  beginRun(QUESTIONS.map((q,i)=>i).filter(i=>QUESTIONS[i].topic===u), null); }"""
SCREENS = [("home", "()=>showHome()"), ("profile", "()=>showProfile()"), ("leaderboard", "()=>showRankings()"), ("settings", "()=>showAppearance()"), ("question", QSTART)]
if "--screens" in args: SCREENS = [s for s in SCREENS if s[0] in args[args.index("--screens") + 1].split(",")]
CLEAR = """()=>{ document.querySelectorAll('#dailyalert,.daily-alert,.app-banner,#updatebanner,.update-banner,.tierup-banner,.battle-alert,.vroom-chat-alert,#toast,.toast,.streak-pop,.streak-flash').forEach(n=>{ if(n.id !== 'a2hsbar') n.remove(); });
  document.body.classList.remove('chatdock-open'); try{ clearTimeout(battleAlertTimer); battleAlertTimer = null; battleAlertQueue = []; }catch(e){} }"""
# each opener returns nothing; SEL is what to read; INSET: laid out by left / right insets (runs margin to button on a phone)
POPS = {
    "daily":   ("()=>showDailyAlert('Done for today \\u2014 the next one is in 1h 42m, at 5pm', {kind:'daily', stay: 60000})", "#dailyalert"),
    "findme":  ("()=>showDailyAlert('You are 4th on the Level board \\u2014 keep going', {kind:'rankings', stay: 60000})", "#dailyalert"),
    "rankup":  ("()=>showDailyAlert('Your profile needs you \\u2014 open Profile to see your rank up', {kind:'rankup', stay: 60000})", "#dailyalert"),
    "tierup":  ("()=>{ theme.muteBanners = false; showTierUpBanner('adept'); }", ".tierup-banner"),
    "toast":   ("()=>{ document.body.classList.add('chatdock-open'); showToast('Chat muted'); }", "#toast"),
    "battle":  ("()=>battleAlert('Lev used Freeze', 'is-freeze')", ".battle-alert"),
    "vchat":   ("()=>{ const b = document.createElement('div'); b.className = 'vroom-chat-alert is-ping'; dressMessageAlert(b, { kind: 'chat', tag: 'MESSAGE', title: 'Lev', sub: 'ready?' }); document.body.appendChild(b); b.style.transition='none'; placeTopBanner(b); void b.offsetHeight; b.style.transition=''; requestAnimationFrame(()=>b.classList.add('show')); }", ".vroom-chat-alert"),
    "streak":  ("()=>{ theme.muteBanners = false; showRunStreakBanner(25); }", ".streak-pop"),
    "update":  ("()=>showUpdateBanner({})", "#updatebanner"),
    "readd":   ("()=>showFrameNotice({id:'test-frame'})", "#updatebanner"),
}
HOME_ONLY = ("update", "readd")
QUESTION_ONLY = ("streak",)
# a frame recorder: the pop-up's box every frame for 900ms from the moment it is in the document
REC = """(sel)=>{ window.__rec = []; const t0 = performance.now(); const tick = () => { const e = document.querySelector(sel);
  if(e){ const r = e.getBoundingClientRect(); window.__rec.push([Math.round((performance.now()-t0)), r.top, parseFloat(getComputedStyle(e).opacity)]); }
  if(performance.now() - t0 < 900 || (window.__rec.length < 3 && performance.now() - t0 < 3000)) requestAnimationFrame(tick); }; requestAnimationFrame(tick); }"""
READ = """(sel)=>{ const R = e => { if(!e) return null; const r = e.getBoundingClientRect(); return r.width ? [r.left, r.top, r.right, r.bottom].map(v=>Math.round(v*10)/10) : null; };
  const chatEl = document.querySelector('.chatdock-btn'); const cs = chatEl && getComputedStyle(chatEl); const chat = chatEl;
  const probe = v => { const q = document.createElement('i'); q.style.cssText = 'position:fixed;top:0;width:0;height:' + v; document.body.appendChild(q); const x = q.getBoundingClientRect().height; q.remove(); return x; };
  const sat = probe('var(--sat, 0px)'), topE = probe('var(--top-e, 0px)');
  const all = [...document.querySelectorAll('#dailyalert,.daily-alert,.app-banner,#updatebanner,.tierup-banner,.battle-alert,.vroom-chat-alert,#toast,#a2hsbar,.streak-pop')].filter((e,i,a)=>a.indexOf(e)===i)
    .filter(e => !(e.id === 'a2hsbar' && (e.classList.contains('is-leaving') || document.body.classList.contains('chatdock-open')))).map(e => [e.id || e.className.split(' ')[0], R(e)]);
  /* the pop-up where it is laid out: the streak pop drifts up 8px over its whole life while it fades (its keyframes), so a
     reading at any moment is taken back by its translate; every other pop-up is at rest (no transform) when read */
  const el = document.querySelector(sel);
  const P = e => { const r = R(e); if(!r) return r; let ty = 0; try{ const t = getComputedStyle(e).transform; if(t && t !== 'none') ty = new DOMMatrixReadOnly(t).m42; }catch(x){}
    return e.classList.contains('streak-pop') ? [r[0], Math.round((r[1] - ty) * 10) / 10, r[2], Math.round((r[3] - ty) * 10) / 10] : r; };
  /* (4) every element that holds words: its words fit (scrollWidth within clientWidth), nothing is cut with an ellipsis */
  const clipped = [];
  if(el){ [el, ...el.querySelectorAll('*')].forEach(n => { const s = getComputedStyle(n); if(s.display === 'none' || !n.clientWidth) return;
      const own = [...n.childNodes].some(c => c.nodeType === 3 && c.textContent.trim()); if(!own) return;
      if(n.scrollWidth > n.clientWidth + 1 && s.overflowX !== 'visible') clipped.push([n.className || n.tagName, n.scrollWidth, n.clientWidth, (n.textContent || '').trim().slice(0, 30)]);
      if(s.webkitLineClamp && s.webkitLineClamp !== 'none' && n.scrollHeight > n.clientHeight + 1) clipped.push([n.className || n.tagName, 'line-clamp', n.scrollHeight, n.clientHeight]); }); }
  /* (2) the page's content box: the first .wrap's padding box less its padding */
  const w = document.querySelector('.wrap'); let content = null;
  if(w){ const wr = w.getBoundingClientRect(), wc = getComputedStyle(w); content = [wr.left + parseFloat(wc.paddingLeft), wr.right - parseFloat(wc.paddingRight)]; }
  /* (3) what is on top at the chat button's and Pause's centres (the real hit test - nothing is forced), and what they compute */
  const pauseEl = document.getElementById('pausebtn');
  const hitAt = b => { if(!b) return null; const r = b.getBoundingClientRect(); if(!r.width || getComputedStyle(b).display === 'none') return null;
    const x = r.left + r.width / 2, y = r.top + r.height / 2; const n = document.elementFromPoint(x, y);
    return { inPop: !!(el && n && el.contains(n)), isBtn: !!(n && b.contains(n)), top: n ? ((n.id ? '#' + n.id : '') + '.' + String(n.className && n.className.baseVal !== undefined ? n.className.baseVal : n.className).split(' ')[0] + ' ' + n.tagName) : null,
             pe: getComputedStyle(b).pointerEvents, z: getComputedStyle(b).zIndex, at: [Math.round(x), Math.round(y)] }; };
  const zOf = e => { let n = e, best = 'auto'; while(n && n !== document.body){ const z = getComputedStyle(n).zIndex; if(z !== 'auto'){ best = z; break; } n = n.parentElement; } return best; };
  const popCs = el && getComputedStyle(el);
  /* (7) the glass's edge: the border, the shadow, the fill's alpha */
  const edge = el ? { bl: popCs.borderLeftWidth, bs: popCs.boxShadow, bg: popCs.backgroundColor, bar: popCs.getPropertyValue('--pop-bar').trim(), banner: popCs.getPropertyValue('--banner-color').trim() } : null;
  return { pop: P(el), chat: R(chat), chatShown: !!chat && cs.display !== 'none', sat, topE, all, clipped, W: innerWidth, pause: R(pauseEl), content,
           hitChat: hitAt(chat), hitPause: hitAt(pauseEl), popZ: el ? zOf(el) : null, chatZ: chat ? zOf(chat) : null, pauseZ: pauseEl ? zOf(pauseEl) : null,
           popPe: el ? popCs.pointerEvents : null, edge, edgeOn: document.documentElement.classList.contains('top-edge-on'), rec: window.__rec || [] }; }"""
def hitbox(c):
    w, h = c[2] - c[0], c[3] - c[1]
    gx, gy = max(0, (44 - w) / 2), max(0, (44 - h) / 2)
    return [c[0] - gx, c[1] - gy, c[2] + gx, c[3] + gy]
def overlaps(a, b):
    return not (a[2] <= b[0] or a[0] >= b[2] or a[3] <= b[1] or a[1] >= b[3])
errs = []
def boot(br, dev):
    name, W, H, top, bottom, ua, inst, wash = dev
    ins = {"top": "%dpx" % top, "bottom": "%dpx" % bottom, "left": "0px", "right": "0px"}
    m = re.search(r'const APP_BUILD = "([^"]+)"', RAW); cb.SERVED_BUILD = m.group(1)
    cb.BODY = cb.INSET_RE.sub(lambda m: ins[m.group(1)], RAW).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
    ctx = br.new_context(viewport={"width": W, "height": H}, device_scale_factor=2, has_touch=True, is_mobile=True, user_agent=ua)
    ctx.add_init_script("try{%slocalStorage.setItem('class26e.drill.v1','%s');}catch(e){}" % (SEEN, cb.USED_ACCOUNT))
    if inst: ctx.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true});")
    pg = cb.open_page(ctx)
    pg.on("pageerror", lambda e: errs.append("%s: %s" % (name, str(e)[:160])))
    pg.goto(cb.URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); __stub(); }"); pg.wait_for_timeout(1500)
    return ctx, pg
def goto(pg, scr, js):
    pg.evaluate(CLEAR); pg.evaluate("()=>showHome()"); pg.wait_for_timeout(450); pg.evaluate(js)
    if scr == "question": pg.wait_for_selector(".qpanel .choice", timeout=25000)
    pg.wait_for_timeout(1300)
    pg.evaluate("()=>{ document.querySelectorAll('.intro-pop,#intro-pop,.unlock-card,.rs-spot,#tour-overlay,.tour-tip').forEach(n=>n.remove()); }")
    pg.evaluate(CLEAR); pg.wait_for_timeout(250)
# settled: shown (opacity 1) and its entrance over (no translate left but the streak pop's own drift) - on a busy machine the
# entrance can take seconds of starved frames, so the read waits for it (up to 8s) instead of a fixed 1.1s
SETTLED = """(sel)=>{ const e = document.querySelector(sel); if(!e) return false; const cs = getComputedStyle(e);
  if(parseFloat(cs.opacity) < .98) return false; if(e.classList.contains('streak-pop')) return true;
  let ty = 0; try{ if(cs.transform && cs.transform !== 'none') ty = new DOMMatrixReadOnly(cs.transform).m42; }catch(x){}
  return Math.abs(ty) < .5; }"""
def settle(pg, sel, ms=8000):
    try: pg.wait_for_function(SETTLED, arg=sel, timeout=ms, polling=100)
    except Exception: pass
def open_pop(pg, key):
    js, sel = POPS[key]
    pg.evaluate(REC, sel)
    pg.evaluate(js)
    pg.wait_for_timeout(1100)
    settle(pg, sel)
    pg.wait_for_timeout(150)
    return pg.evaluate(READ, sel)
def row_of(d, wash):
    # (384.97) the band's bottom is 384.95's line E (--top-e): the inset + 18pt on an installed notched iPhone upright, else none
    washY = d["topE"] if (wash and d["edgeOn"] and d["topE"] > d["sat"] + .5) else 0
    c = d["chat"]
    return (max(c[1], washY) if c else None), washY
def check_wide(lab, key, d, W, p, inrow=True):
    c = d["chat"]
    ct = d.get("content")
    if not ct: chk("%s: the page's content box is readable" % lab, False, d); return
    chk("%s: the page's full width - %s..%s, the content box %s..%s (width %s)" % (lab, p[0], p[2], round(ct[0], 1), round(ct[1], 1), round(p[2] - p[0], 1)),
        abs(p[0] - ct[0]) <= 1 and abs(p[2] - ct[1]) <= 1, d)
    chk("%s: the same gutter both sides (%s left, %s right of %s)" % (lab, round(p[0], 1), round(W - p[2], 1), W), abs(p[0] - (W - p[2])) <= 1, d)
    # (3) COVER (a pop-up stacked under another, or under the Home Screen reminder, is not in the row)
    for nm, h, z in (("chat button", d.get("hitChat"), d.get("chatZ")), ("Pause", d.get("hitPause"), d.get("pauseZ"))):
        if not h or not inrow: continue
        chk("%s: the %s's centre %s is the pop-up's (top of the hit stack: %s)" % (lab, nm, h["at"], h["top"]), h["inPop"] and not h["isBtn"], d)
        chk("%s: the %s gets no taps while it shows (pointer-events %s)" % (lab, nm, h["pe"]), h["pe"] == "none", d)
        try: above = float(d["popZ"]) > float(z)
        except Exception: above = d["popZ"] not in (None, "auto") and z == "auto"
        chk("%s: z-index above the %s (%s over %s)" % (lab, nm, d["popZ"], z), above, d)
    if inrow: chk("%s: drawn over the top row, not under the test header" % lab, (not d.get("hitChat") or d["hitChat"]["inPop"]) and (not d.get("hitPause") or d["hitPause"]["inPop"]), d)
    chk("%s: inside the screen and every word fits (%s)" % (lab, d["clipped"] or "nothing cut"), p[0] >= -.5 and p[2] <= W + .5 and not d["clipped"], d)
def placed(pg, key, d, wash):
    """Where a lone pop-up belongs: in the chat button's row - its top on the button's top, or on the wash line where the button
    sits above it."""
    p, c = d["pop"], d["chat"]
    want, washY = row_of(d, wash)
    if not (p and c): return False, "(no pop-up or no chat button)"
    if abs(p[1] - want) <= 1:
        return True, "in the chat button's row (button top %s%s = %s)" % (c[1], ", wash line %s" % washY if washY else "", want)
    return False, "not in the row (want %s)" % want
EDGE_KEYS = ("daily", "findme", "rankup", "update", "readd", "toast", "vchat")
def parse_rgba(t):
    m = re.findall(r"[\d.]+", t or "")
    return [float(v) for v in m[:4]] if len(m) >= 3 else None
def check_edge(pg, lab, key, d, p):
    """(7) the glass: the coloured edge is a 1px border plus a 2px inset line, the fill is dense, and the 3px at the left edge are the
    pop-up's own colour in the pixels."""
    if key not in EDGE_KEYS or not d.get("edge"): return
    e = d["edge"]
    chk("%s: the coloured edge is a 1px border (not a 3px left border cut off at the corners) - border-left %s" % (lab, e["bl"]), e["bl"] in ("1px", "1.0px"), e)
    chk("%s: ...and a 2px inset line in the pop-up's colour (box-shadow has it)" % lab, bool(re.search(r"inset\s+2px 0px 0px 0px", e["bs"]) or re.search(r"\) inset 2px 0px 0px 0px", e["bs"]) or re.search(r"2px 0px 0px 0px inset", e["bs"])), e)
    rgba = parse_rgba(e["bg"])
    chk("%s: the glass is dense enough that what is behind it is only a faint shade (fill alpha %s, at least .6)" % (lab, rgba and rgba[3] if rgba and len(rgba) > 3 else rgba), bool(rgba) and (len(rgba) < 4 or rgba[3] >= .6), e)
    m = re.match(r"#([0-9a-fA-F]{6})$", e.get("bar") or "")
    if m and p:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
        want = tuple(int(m.group(1)[i:i + 2], 16) for i in (0, 2, 4))
        ym = int(round((p[1] + p[3]) / 2 * 2))
        got = [img.getpixel((int(round(p[0] * 2)) + dx, ym)) for dx in (1, 3, 5)]
        ok_px = all(all(abs(g[i] - want[i]) <= 48 for i in range(3)) for g in got)
        chk("%s: the 3px at the left edge are the pop-up's colour %s in the pixels (read %s)" % (lab, want, got), ok_px, got)
def swipe_up(pg, x, y, dy=80):
    cdp = pg.context.new_cdp_session(pg)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]})
    for i in range(1, 9):
        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x, "y": y - dy * i / 8}]}); pg.wait_for_timeout(18)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    cdp.detach()
GONE = "(sel)=>{ const e = document.querySelector(sel); if(!e) return true; return !e.isConnected || parseFloat(getComputedStyle(e).opacity) < .05; }"
def gone(pg, sel, ms=1600):
    try: pg.wait_for_function(GONE, arg=sel, timeout=ms, polling=60); return True
    except Exception: return False
def centre(pg, sel):
    return pg.evaluate("(sel)=>{ const e = document.querySelector(sel); if(!e) return null; const r = e.getBoundingClientRect(); return r.width ? [r.left + r.width / 2, r.top + r.height / 2] : null; }", sel)
def dismiss_checks(pg, name):
    """(8) the x closes a pop-up (a real tap), a swipe up dismisses any of them, a tap on the chat button's place does nothing to the
    chat while one shows, and the chat button is back (and tappable) once it has gone."""
    lab = "%s home" % name
    # the x, a real tap through the screen
    goto(pg, "home", "()=>showHome()")
    pg.evaluate(POPS["findme"][0]); pg.wait_for_timeout(1100); settle(pg, "#dailyalert")
    xc = centre(pg, "#dailyalert .app-banner-x")
    if xc: pg.touchscreen.tap(xc[0], xc[1])
    chk("%s: a tap on the x closes the pop-up (x at %s)" % (lab, xc), bool(xc) and gone(pg, "#dailyalert"), xc)
    pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    # a swipe up on each kind of pop-up
    for key in ("findme", "daily", "update", "tierup", "toast", "battle", "vchat"):
        pg.evaluate(CLEAR); pg.wait_for_timeout(250)
        pg.evaluate(POPS[key][0]); pg.wait_for_timeout(1100); settle(pg, POPS[key][1])
        c = centre(pg, POPS[key][1])
        if not c: chk("%s: %s is up to swipe" % (lab, key), False); continue
        swipe_up(pg, c[0] - 40, c[1] + 6)
        chk("%s: a swipe up on the %s pop-up dismisses it" % (lab, key), gone(pg, POPS[key][1]), c)
    pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    # a tap on the chat button's place while a pop-up shows opens nothing; once it has gone the button takes the tap again
    pg.evaluate(POPS["daily"][0].replace("stay: 60000", "stay: 60000")); pg.wait_for_timeout(1100); settle(pg, "#dailyalert")
    cc = centre(pg, ".chatdock-btn")
    if cc:
        pg.touchscreen.tap(cc[0], cc[1]); pg.wait_for_timeout(700)
        opened = pg.evaluate("()=>!!document.querySelector('.chatdock.is-open')")
        chk("%s: a tap on the chat button's place while a pop-up shows does not open the chat" % lab, not opened, cc)
        if opened: pg.evaluate("()=>{ const b = document.querySelector('.chatdock-btn'); if(b) b.click(); }")
    pg.evaluate(CLEAR); pg.wait_for_timeout(500)
    # the natural leave: a short-lived one, then the button is back
    pg.evaluate("()=>showDailyAlert('Done for today \\u2014 the next one is in 1h 42m, at 5pm', {kind:'daily', stay: 700})"); pg.wait_for_timeout(2300)
    r = pg.evaluate("""()=>{ const b = document.querySelector('.chatdock-btn'); if(!b) return null; const q = b.getBoundingClientRect(); const n = document.elementFromPoint(q.left + q.width / 2, q.top + q.height / 2);
        return { pe: getComputedStyle(b).pointerEvents, op: parseFloat(getComputedStyle(b).opacity), isBtn: !!(n && b.contains(n)), popLeft: document.querySelectorAll('#dailyalert').length }; }""")
    chk("%s: once the pop-up has cleared the chat button is back - tappable (pointer-events %s), visible (opacity %s), the hit-test target" % (lab, r and r["pe"], r and r["op"]),
        bool(r) and r["pe"] != "none" and r["op"] > .95 and r["isBtn"] and r["popLeft"] == 0, r)
    if cc:
        pg.touchscreen.tap(cc[0], cc[1]); pg.wait_for_timeout(900)
        opened = pg.evaluate("()=>!!document.querySelector('.chatdock.is-open')")
        chk("%s: ...and a tap on it opens the chat again" % lab, opened, cc)
        if opened: pg.evaluate("()=>{ const b = document.querySelector('.chatdock-btn'); if(b) b.click(); }"); pg.wait_for_timeout(700)
    # a question: the same for Pause
    goto(pg, "question", QSTART)
    pg.evaluate(POPS["daily"][0]); pg.wait_for_timeout(1100); settle(pg, "#dailyalert")
    pc = centre(pg, "#pausebtn")
    if pc:
        pg.touchscreen.tap(pc[0], pc[1]); pg.wait_for_timeout(700)
        paused = pg.evaluate("()=>!!document.querySelector('.pausepanel')")
        chk("%s question: a tap on Pause's place while a pop-up shows does not pause" % lab, not paused, pc)
        if paused: pg.evaluate("()=>{ const b = document.getElementById('pausebtn'); if(b) b.click(); }")
    pg.evaluate(CLEAR); pg.wait_for_timeout(500)
    r = pg.evaluate("""()=>{ const b = document.getElementById('pausebtn'); if(!b) return null; const q = b.getBoundingClientRect(); const n = document.elementFromPoint(q.left + q.width / 2, q.top + q.height / 2);
        return { pe: getComputedStyle(b).pointerEvents, op: parseFloat(getComputedStyle(b).opacity), isBtn: !!(n && b.contains(n)) }; }""")
    chk("%s question: once the pop-up has cleared Pause is back - tappable (pointer-events %s), visible (opacity %s), the hit-test target" % (lab, r and r["pe"], r and r["op"]),
        bool(r) and r["pe"] != "none" and r["op"] > .95 and r["isBtn"], r)
def run(br):
    for dev in DEVICES:
        name, W, H, top, bottom, ua, inst, wash = dev
        ctx, pg = boot(br, dev)
        for scr, js in SCREENS:
            goto(pg, scr, js)
            for key in POPS:
                if key in HOME_ONLY and scr != "home": continue
                if key in QUESTION_ONLY and scr != "question": continue
                d = open_pop(pg, key)
                lab = "%s %s %s" % (name, scr, key)
                p, c = d["pop"], d["chat"]
                if not p:
                    chk(lab + ": shown", False, d); pg.evaluate(CLEAR); continue
                if SHOTS and scr == "home" and key in ("daily", "update", "rankup", "tierup") and name in ("promax", "ipad11", "p320"):
                    pg.screenshot(path=os.path.join(SHOTS, "%s_%s_%s.png" % (TAG, name, key)))
                if SHOTS and key in ("daily", "streak") and name in ("promax", "ipad11", "p320") and scr != "home":
                    pg.screenshot(path=os.path.join(SHOTS, "%s_%s_%s_%s.png" % (TAG, name, scr, key)))
                want, washY = row_of(d, wash)
                if wash: chk("%s: the blur line is on here (installed iPhone, notch inset %s, line E %s)" % (lab, d["sat"], d["topE"]), d["edgeOn"] and d["sat"] > 30 and d["topE"] > d["sat"] + 10, d)
                # the Home Screen reminder (a Safari tab's Home) comes first; a pop-up up with it stacks under it
                ab = dict(d["all"]).get("a2hsbar") if key not in HOME_ONLY else None
                if ab:
                    a_want = max(c[3] + A2HS_GAP, washY) if (c and ab[2] > c[0] and ab[0] < c[2]) else want
                    chk("%s: the Home Screen reminder is in its place (%s, want %s)" % (lab, ab[1], a_want), a_want is not None and abs(ab[1] - a_want) <= 1, d)
                    chk("%s: top %s stacked under the Home Screen reminder (%s)" % (lab, p[1], ab[3]), ab[3] - .5 <= p[1] <= ab[3] + 14, d)
                else:
                    good, why = placed(pg, key, d, wash)
                    chk("%s: top %s %s" % (lab, p[1], why), good, d)
                chk("%s: not above the wash (%s >= %s)" % (lab, p[1], washY), p[1] >= washY - .5, d)
                check_wide(lab, key, d, W, p, inrow=not ab)
                check_edge(pg, lab, key, d, p)
                # the first frame it is in the document (its entrance's starting point, before it fades in) is above where it settles
                rec = d["rec"]
                if rec:
                    chk("%s: drops in from above (first frame top %.1f, settled %.1f)" % (lab, rec[0][1], p[1]), rec[0][1] < p[1] - .9, rec[:6])
                else:
                    chk("%s: drops in from above (frames recorded)" % lab, False, d["rec"][:6])
                pg.evaluate(CLEAR); pg.wait_for_timeout(200)
        # (4) the update notice and the daily alert together: no overlap, the notice in the row and the alert under it
        goto(pg, "home", "()=>showHome()")
        pg.evaluate(POPS["update"][0]); pg.wait_for_timeout(700); pg.evaluate(POPS["daily"][0]); pg.wait_for_timeout(1100)
        settle(pg, "#updatebanner"); settle(pg, "#dailyalert"); pg.wait_for_timeout(150)
        a = pg.evaluate(READ, "#updatebanner"); b = pg.evaluate(READ, "#dailyalert")
        u, dl = a["pop"], b["pop"]; good, why = placed(pg, "update", a, wash)
        chk("%s home: update notice in its place (%s) and the daily alert under it, no overlap (%s / %s)" % (name, why, u, dl),
            u and dl and good and dl[1] >= u[3] - .5, [u, dl])
        if dl: check_wide("%s home, the alert stacked under the notice" % name, "daily", b, W, dl, inrow=False)
        if SHOTS and name in ("promax", "ipad11"): pg.screenshot(path=os.path.join(SHOTS, "%s_%s_update+daily.png" % (TAG, name)))
        # late notice: the alert first, the notice a moment later - the alert moves under it
        pg.evaluate(CLEAR); pg.evaluate(POPS["daily"][0]); pg.wait_for_timeout(900); pg.evaluate(POPS["update"][0]); pg.wait_for_timeout(1100)
        settle(pg, "#updatebanner"); settle(pg, "#dailyalert"); pg.wait_for_timeout(150)
        a = pg.evaluate(READ, "#updatebanner"); b = pg.evaluate(READ, "#dailyalert")
        u, dl = a["pop"], b["pop"]
        chk("%s home: a notice arriving after the alert still stacks them (%s / %s)" % (name, u, dl), u and dl and dl[1] >= u[3] - .5, [u, dl])
        # a toast with the chat panel really open: in the row, the page's width, over the chat button (on a phone the panel is a sheet from
        # the bottom; on a tablet it hangs under the button and the toast is over it)
        pg.evaluate(CLEAR)
        pg.evaluate("()=>{ const b = document.querySelector('.chatdock-btn'); if(b) b.click(); }"); pg.wait_for_timeout(1300)
        pg.evaluate("()=>showToast('Chat muted')"); pg.wait_for_timeout(1000); settle(pg, "#toast")
        q = pg.evaluate(READ, "#toast"); q["open"] = pg.evaluate("()=>!!document.querySelector('.chatdock.is-open')")
        tp = q["pop"]
        wy = q["topE"] if (wash and q["topE"] > top + .5) else 0
        chk("%s home, chat open: the toast is up, in the chat button's row (%s, button %s)" % (name, tp, q["chat"]),
            q["open"] and tp and q["chat"] and abs(tp[1] - max(q["chat"][1], wy)) <= 1, q)
        if tp: check_wide("%s home, chat open, the toast" % name, "toast", q, W, tp)
        pg.evaluate("()=>{ const b = document.querySelector('.chatdock-btn'); if(b && document.querySelector('.chatdock.is-open')) b.click(); }"); pg.wait_for_timeout(900)
        # a tour holds the notices back; when it goes, the notice comes up in the row
        pg.evaluate(CLEAR)
        t = pg.evaluate("""()=>{ pendingNotice = { kind: 'update', info: {} }; const o = document.createElement('div'); o.id = 'tour-overlay'; document.body.appendChild(o);
            syncNoticeVisibility(); const held = !document.getElementById('updatebanner'); o.remove(); tourQuietUntil = 0; syncNoticeVisibility();
            return { held, back: !!document.getElementById('updatebanner') }; }""")
        pg.wait_for_timeout(900); settle(pg, "#updatebanner"); pg.wait_for_timeout(150)
        a = pg.evaluate(READ, "#updatebanner"); good, why = placed(pg, "update", a, wash)
        chk("%s home: a tour holds the update notice back (%s) and it comes up in its place after (%s: %s)" % (name, t, a["pop"], why),
            t["held"] and t["back"] and a["pop"] and good, [t, a["pop"], a["chat"]])
        if name in ("promax", "ipad11", "p320"): dismiss_checks(pg, name)
        ctx.close()
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    try: run(br)
    finally: br.close()
chk("no page errors (%d)" % len(errs), not errs, errs[:4])
print("ALL PASS" if ok else "SOME FAIL")
sys.exit(0 if ok else 1)
