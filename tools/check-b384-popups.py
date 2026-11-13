#!/usr/bin/env python3
"""Build 384.93 (384.91 reworked): EVERY TOP POP-UP IN THE CHAT BUTTON'S ROW, beside the button, never in the system's top wash.

Madison (iPhone 17 Pro Max, installed, build 384.86, Home with "DAILY QUESTION / Done for today" up): "I feel like these pops need
to be a little closer to the top. Not in the blurred area but yeah. They are in an awkward spot." 384.91 put them 6px under the chat
button, which gained 4px on Home and would have sent them ~150px down once the top row moves below the blur (claude/b384-polish86).
384.93 puts them IN the button's row (docs/notes-archive.md "384.93").

For each device and screen, each pop-up is opened by the app's own function and read once it has settled:
 (1) ROW      its top border edge is the chat button's top (read off the live button) within 1px - the same row on every screen
              (Home, Profile, the Leaderboard, Settings, a question) - or, where the button sits higher than the bottom of iOS 26's
              wash (installed iPhone upright with a notch: the safe-area line + 42px; nowhere else), that line: never above it;
 (2) BESIDE   it does not overlap the chat button's hit box (the button grown to 44px at least); where it shares the button's
              rows its right edge is at most the hit box's left - 8 (within 1px), and on a phone an inset pop-up (the daily alert
              and every banner on its glass, the notices, a toast) runs from the safe-area margin to exactly that edge; on a tablet
              it keeps the 26rem it had (it does not stretch). Where there is under 180px beside the button (a 320px phone
              mid-test), or where the gate narrows the box to that span and it comes out more than 1.3x as tall (one word to a
              line), it sits 8px under the hit box at its own width instead - and only there;
 (3) FITS     every line of its text fits its box (wraps, never clipped) and the box is inside the screen - on a 320px phone too;
 (4) STACK    the update notice and the daily alert up together do not overlap, the notice in the row and the alert under it
              (whichever came first); in a Safari tab's Home the Home Screen reminder (a slim centred bar, under the chat button on a
              phone, 384 r19) comes first and every other pop-up stacks under it; a tour holds the update notice back and it comes
              up in the row when the tour goes; a toast with the chat panel open lies on neither the panel nor the button;
 (5) ENTRANCE it arrives from above (its first frame is higher than where it settles);
 (6) no page errors.
Pop-ups: the daily alert ("Done for today"), Find me's answer, the rank-up banner, a toast said at the top, a battle alert, a
Virtual Room chat alert, the tier banner (showTierUpBanner), the answer-streak pop (a question), the update notice and the re-add
notice (Home: they are gated to Welcome and Home).
Devices: installed iPhone 17 Pro Max (440x956, 59/34 simulated), installed SE-size (375x667, 20/0), an installed 320px phone
(320x568, 20/0), installed iPad Pro 11" (834x1194, 24/20), and the Safari-tab model (440x797, no insets, not installed).
Run:  python3 tools/check-b384-popups.py [--against FILE] [--only DEVICE[,DEVICE]] [--screens home,profile,...] [--shots DIR --tag NAME]
      (origin/main must FAIL (1) and (2): there every pop-up is under the button or under the tab switcher / the question count,
      and the rank and tier banners sit on the button)"""
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
BESIDE = 8          # the gap to the chat button's hit box
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
DEVICES = [("promax", 440, 956, 59, 34, UA, True, True), ("se", 375, 667, 20, 0, UA, True, False),
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
INSET = ("daily", "findme", "rankup", "toast", "vchat", "update", "readd")
HOME_ONLY = ("update", "readd")
QUESTION_ONLY = ("streak",)
# a frame recorder: the pop-up's box every frame for 900ms from the moment it is in the document
REC = """(sel)=>{ window.__rec = []; const t0 = performance.now(); const tick = () => { const e = document.querySelector(sel);
  if(e){ const r = e.getBoundingClientRect(); window.__rec.push([Math.round((performance.now()-t0)), r.top, parseFloat(getComputedStyle(e).opacity)]); }
  if(performance.now() - t0 < 900 || (window.__rec.length < 3 && performance.now() - t0 < 3000)) requestAnimationFrame(tick); }; requestAnimationFrame(tick); }"""
READ = """(sel)=>{ const R = e => { if(!e) return null; const r = e.getBoundingClientRect(); return r.width ? [r.left, r.top, r.right, r.bottom].map(v=>Math.round(v*10)/10) : null; };
  const chat = document.querySelector('.chatdock-btn'); const cs = chat && getComputedStyle(chat);
  const sat = (() => { const q = document.createElement('i'); q.style.cssText = 'position:fixed;top:0;width:0;height:var(--sat, 0px)'; document.body.appendChild(q); const x = q.getBoundingClientRect().height; q.remove(); return x; })();
  const all = [...document.querySelectorAll('#dailyalert,.daily-alert,.app-banner,#updatebanner,.tierup-banner,.battle-alert,.vroom-chat-alert,#toast,#a2hsbar,.streak-pop')].filter((e,i,a)=>a.indexOf(e)===i)
    .filter(e => !(e.id === 'a2hsbar' && (e.classList.contains('is-leaving') || document.body.classList.contains('chatdock-open')))).map(e => [e.id || e.className.split(' ')[0], R(e)]);
  /* the pop-up where it is laid out: the streak pop drifts up 8px over its whole life while it fades (its keyframes), so a
     reading at any moment is taken back by its translate; every other pop-up is at rest (no transform) when read */
  const el = document.querySelector(sel);
  const P = e => { const r = R(e); if(!r) return r; let ty = 0; try{ const t = getComputedStyle(e).transform; if(t && t !== 'none') ty = new DOMMatrixReadOnly(t).m42; }catch(x){}
    return e.classList.contains('streak-pop') ? [r[0], Math.round((r[1] - ty) * 10) / 10, r[2], Math.round((r[3] - ty) * 10) / 10] : r; };
  /* (3) every element that holds words: its words fit (scrollWidth within clientWidth), nothing is cut with an ellipsis */
  const clipped = [];
  if(el){ [el, ...el.querySelectorAll('*')].forEach(n => { const s = getComputedStyle(n); if(s.display === 'none' || !n.clientWidth) return;
      const own = [...n.childNodes].some(c => c.nodeType === 3 && c.textContent.trim()); if(!own) return;
      if(n.scrollWidth > n.clientWidth + 1 && s.overflowX !== 'visible') clipped.push([n.className || n.tagName, n.scrollWidth, n.clientWidth, (n.textContent || '').trim().slice(0, 30)]);
      if(s.webkitLineClamp && s.webkitLineClamp !== 'none' && n.scrollHeight > n.clientHeight + 1) clipped.push([n.className || n.tagName, 'line-clamp', n.scrollHeight, n.clientHeight]); }); }
  return { pop: P(el), chat: R(chat), chatShown: !!chat && cs.display !== 'none', sat, all, clipped, W: innerWidth,
           edgeOn: document.documentElement.classList.contains('top-edge-on'), rec: window.__rec || [] }; }"""
# the box's height as it is, and narrowed to the margin..edge span (inset pop-ups: a right inset; centred ones: a centre and a max-width),
# then put back
JUSTIFY = """([sel, edge])=>{ const e = document.querySelector(sel); if(!e) return null; const h0 = e.offsetHeight; const s = [e.style.left, e.style.right, e.style.maxWidth];
  const cs = getComputedStyle(e); let m41 = 0; try{ if(cs.transform !== 'none') m41 = new DOMMatrixReadOnly(cs.transform).m41; }catch(x){}
  if(Math.abs(m41 + e.offsetWidth / 2) < 2.5 && Math.abs(m41) > 1){ e.style.left = ((16 + edge) / 2) + 'px'; e.style.maxWidth = (edge - 16) + 'px'; }
  else e.style.right = (innerWidth - edge) + 'px';
  const h1 = e.offsetHeight; e.style.left = s[0]; e.style.right = s[1]; e.style.maxWidth = s[2]; return [h0, h1]; }"""
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
def open_pop(pg, key):
    js, sel = POPS[key]
    pg.evaluate(REC, sel)
    pg.evaluate(js)
    pg.wait_for_timeout(1100)
    return pg.evaluate(READ, sel)
def row_of(d, wash):
    washY = (d["sat"] + 42) if (wash and d["edgeOn"]) else 0
    c = d["chat"]
    return (max(c[1], washY) if c else None), washY
def check_beside(lab, key, d, W, p):
    c = d["chat"]
    if not c: chk("%s: the chat button is up" % lab, False, d); return
    hb = hitbox(c)
    chk("%s: clear of the chat button's hit box (%s / %s)" % (lab, p, [round(v, 1) for v in hb]), not overlaps(p, hb), d)
    if p[3] > hb[1] and p[1] < hb[3]:
        edge = hb[0] - BESIDE
        chk("%s: in the button's rows it stops %dpx short of the hit box (right %s <= %s)" % (lab, BESIDE, p[2], round(edge, 1)), p[2] <= edge + 1, d)
        if key in INSET and W < 640:
            chk("%s: a phone's inset pop-up runs from the safe-area margin to that edge (%s..%s, want %s..%s)" % (lab, p[0], p[2], REM, round(edge, 1)),
                abs(p[0] - REM) <= 1 and abs(p[2] - edge) <= 1, d)
    if W >= 640 and key in INSET:
        chk("%s: a tablet's pop-up keeps its 26rem (%spx wide)" % (lab, round(p[2] - p[0], 1)), p[2] - p[0] <= 26 * REM + 1, d)
    chk("%s: inside the screen and every word fits (%s)" % (lab, d["clipped"] or "nothing cut"), p[0] >= -.5 and p[2] <= W + .5 and not d["clipped"], d)
def placed(pg, key, d, wash):
    """Where a lone pop-up belongs: in the chat button's row (its top on the button's top, or on the wash line where the button
    sits above it), or 8px under the button's hit box at its own width where that is earned - under 180px beside the button (a
    320px phone mid-test: Pause pushes it to the middle), or where the gate itself narrows the box to the margin..hit box - 8
    span and it comes out more than 1.3x as tall (the update notice on a 320px phone went one word to a line)."""
    p, c = d["pop"], d["chat"]
    want, washY = row_of(d, wash)
    if not (p and c): return False, "(no pop-up or no chat button)"
    if abs(p[1] - want) <= 1:
        return True, "in the chat button's row (button top %s%s = %s)" % (c[1], ", wash line %s" % washY if washY else "", want)
    under = hitbox(c)[3] + 8
    if abs(p[1] - under) <= 1:
        room = hitbox(c)[0] - BESIDE - REM
        j = pg.evaluate(JUSTIFY, [POPS[key][1], hitbox(c)[0] - BESIDE])
        return (room < 180 or bool(j and j[1] > j[0] * 1.3 + 2),
                "8px under the hit box (%s): %dpx beside the button; narrowed it would be %s -> %spx tall" % (under, room, j and j[0], j and j[1]))
    return False, "neither in the row (%s) nor 8px under the hit box (%s)" % (want, under)
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
                if wash: chk("%s: the wash model is on here (installed iPhone, notch inset %s)" % (lab, d["sat"]), d["edgeOn"] and d["sat"] > 30, d)
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
                check_beside(lab, key, d, W, p)
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
        a = pg.evaluate(READ, "#updatebanner"); b = pg.evaluate(READ, "#dailyalert")
        u, dl = a["pop"], b["pop"]; good, why = placed(pg, "update", a, wash)
        chk("%s home: update notice in its place (%s) and the daily alert under it, no overlap (%s / %s)" % (name, why, u, dl),
            u and dl and good and dl[1] >= u[3] - .5, [u, dl])
        if dl: check_beside("%s home, the alert stacked under the notice" % name, "daily", b, W, dl)
        if SHOTS and name in ("promax", "ipad11"): pg.screenshot(path=os.path.join(SHOTS, "%s_%s_update+daily.png" % (TAG, name)))
        # late notice: the alert first, the notice a moment later - the alert moves under it
        pg.evaluate(CLEAR); pg.evaluate(POPS["daily"][0]); pg.wait_for_timeout(900); pg.evaluate(POPS["update"][0]); pg.wait_for_timeout(1100)
        a = pg.evaluate(READ, "#updatebanner"); b = pg.evaluate(READ, "#dailyalert")
        u, dl = a["pop"], b["pop"]
        chk("%s home: a notice arriving after the alert still stacks them (%s / %s)" % (name, u, dl), u and dl and dl[1] >= u[3] - .5, [u, dl])
        # a toast with the chat panel really open: in the row, beside the button where the panel is a sheet from the bottom (a
        # phone); where the panel hangs under the button (a tablet) it lies on neither
        pg.evaluate(CLEAR)
        pg.evaluate("()=>{ const b = document.querySelector('.chatdock-btn'); if(b) b.click(); }"); pg.wait_for_timeout(1300)
        pg.evaluate("()=>showToast('Chat muted')"); pg.wait_for_timeout(1000)
        q = pg.evaluate("""()=>{ const R = e => { if(!e) return null; const r = e.getBoundingClientRect(); return r.width ? [r.left, r.top, r.right, r.bottom].map(v=>Math.round(v*10)/10) : null; };
            return { open: !!document.querySelector('.chatdock.is-open'), panel: R(document.querySelector('.chatdock.is-open .chatdock-panel')), toast: R(document.getElementById('toast')), chat: R(document.querySelector('.chatdock-btn')) }; }""")
        tp, pp, cc = q["toast"], q["panel"], q["chat"]
        on_panel = bool(tp and pp and overlaps(tp, pp))
        on_btn = bool(tp and cc and overlaps(tp, hitbox(cc)))
        if pp and cc and pp[1] < cc[3] + 60:
            chk("%s home, chat open (panel under the button): the toast is on neither the panel nor the button (%s / %s)" % (name, tp, pp), q["open"] and tp and not on_panel and not on_btn, q)
        else:
            wy = (top + 42) if wash else 0
            chk("%s home, chat open (a sheet): the toast is in the row, beside the button, clear of the sheet (%s / %s)" % (name, tp, pp),
                q["open"] and tp and cc and abs(tp[1] - max(cc[1], wy)) <= 1 and not on_panel and not on_btn, q)
        pg.evaluate("()=>{ const b = document.querySelector('.chatdock-btn'); if(b && document.querySelector('.chatdock.is-open')) b.click(); }"); pg.wait_for_timeout(900)
        # a tour holds the notices back; when it goes, the notice comes up in the row
        pg.evaluate(CLEAR)
        t = pg.evaluate("""()=>{ pendingNotice = { kind: 'update', info: {} }; const o = document.createElement('div'); o.id = 'tour-overlay'; document.body.appendChild(o);
            syncNoticeVisibility(); const held = !document.getElementById('updatebanner'); o.remove(); tourQuietUntil = 0; syncNoticeVisibility();
            return { held, back: !!document.getElementById('updatebanner') }; }""")
        pg.wait_for_timeout(900)
        a = pg.evaluate(READ, "#updatebanner"); good, why = placed(pg, "update", a, wash)
        chk("%s home: a tour holds the update notice back (%s) and it comes up in its place after (%s: %s)" % (name, t, a["pop"], why),
            t["held"] and t["back"] and a["pop"] and good, [t, a["pop"], a["chat"]])
        ctx.close()
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    try: run(br)
    finally: br.close()
chk("no page errors (%d)" % len(errs), not errs, errs[:4])
print("ALL PASS" if ok else "SOME FAIL")
sys.exit(0 if ok else 1)
