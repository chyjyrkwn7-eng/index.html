#!/usr/bin/env python3
"""Build 384.91: EVERY TOP POP-UP ON ONE LINE, just under the chat button and the system's top wash.

Madison (iPhone 17 Pro Max, installed, build 384.86, Home with "DAILY QUESTION / Done for today" up): "I feel like these pops need
to be a little closer to the top. Not in the blurred area but yeah. They are in an awkward spot." (docs/notes-archive.md "384.91")

For each device and screen, each pop-up is opened by the app's own function and read once it has settled:
 (1) LINE     its top border edge is the chat button's bottom (read off the live button) + GAP, within 1px - the same line on
              every screen (Home, Profile, the Leaderboard, Settings, a question) - and never above the bottom of iOS 26's wash
              (installed iPhone upright with a notch: the safe-area line + 42px; nowhere else);
 (2) CLEAR    it does not overlap the chat button;
 (3) STACK    the update notice and the daily alert up together do not overlap, the alert under the notice (whichever came first);
              in a Safari tab's Home the Home Screen reminder is on the line and every other pop-up stacks under it; a tour
              holds the update notice back and it comes up on the line when the tour goes;
 (4) ENTRANCE it arrives from above (its first visible frame is higher than where it settles);
 (5) no page errors.
Pop-ups: the daily alert ("Done for today"), Find me's answer, the rank-up banner, a toast said at the top, a battle alert, a
Virtual Room chat alert, the tier banner (showTierUpBanner), the answer-streak pop (a question), the update notice and the re-add notice (Home: they are gated to
Welcome and Home).
Devices: installed iPhone 17 Pro Max (440x956, 59/34 simulated), installed SE-size (375x667, 20/0), installed iPad Pro 11"
(834x1194, 24/20), and the Safari-tab model (440x797, no insets, not installed).
Run:  python3 tools/check-b384-popups.py [--against FILE] [--only DEVICE[,DEVICE]] [--screens home,profile,...] [--shots DIR --tag NAME]
      (origin/main 384.86 must FAIL (1): Profile, the Leaderboard and Settings stopped below the tab switcher, a question below
      its count, and the rank and tier banners sat in the wash)"""
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
GAP = 6
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
           ("ipad11", 834, 1194, 24, 20, UA_PAD, True, False), ("safari", 440, 797, 0, 0, UA, False, False)]
if ONLY: DEVICES = [d for d in DEVICES if any(o in d[0] for o in ONLY.split(","))]
QSTART = """()=>{ showHome(); const u = 'Arrest, Search, and Seizure'; cfg.mode='drill'; cfg.units=[u]; cfg.versions={}; cfg.source='all'; cfg.size=0; cfg.timer='off'; cfg.flashcards=false; theme.autoAdvance=false;
  beginRun(QUESTIONS.map((q,i)=>i).filter(i=>QUESTIONS[i].topic===u), null); }"""
SCREENS = [("home", "()=>showHome()"), ("profile", "()=>showProfile()"), ("leaderboard", "()=>showRankings()"), ("settings", "()=>showAppearance()"), ("question", QSTART)]
if "--screens" in args: SCREENS = [s for s in SCREENS if s[0] in args[args.index("--screens") + 1].split(",")]
CLEAR = """()=>{ document.querySelectorAll('#dailyalert,.daily-alert,.app-banner,#updatebanner,.update-banner,.tierup-banner,.battle-alert,.vroom-chat-alert,#toast,.toast,.streak-pop,.streak-flash').forEach(n=>{ if(n.id !== 'a2hsbar') n.remove(); });
  document.body.classList.remove('chatdock-open'); try{ clearTimeout(battleAlertTimer); battleAlertTimer = null; battleAlertQueue = []; }catch(e){} }"""
# each opener returns nothing; SEL is what to read
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
  const chat = document.querySelector('.chatdock-btn'); const cs = chat && getComputedStyle(chat);
  const sat = (() => { const q = document.createElement('i'); q.style.cssText = 'position:fixed;top:0;width:0;height:var(--sat, 0px)'; document.body.appendChild(q); const x = q.getBoundingClientRect().height; q.remove(); return x; })();
  const all = [...document.querySelectorAll('#dailyalert,.daily-alert,.app-banner,#updatebanner,.tierup-banner,.battle-alert,.vroom-chat-alert,#toast,#a2hsbar,.streak-pop')].filter((e,i,a)=>a.indexOf(e)===i)
    .filter(e => !(e.id === 'a2hsbar' && (e.classList.contains('is-leaving') || document.body.classList.contains('chatdock-open')))).map(e => [e.id || e.className.split(' ')[0], R(e)]);
  /* the pop-up where it is laid out: the streak pop drifts up 8px over its whole life while it fades (its keyframes), so a
     reading at any moment is taken back by its translate; every other pop-up is at rest (no transform) when read */
  const P = e => { const r = R(e); if(!r) return r; let ty = 0; try{ const t = getComputedStyle(e).transform; if(t && t !== 'none') ty = new DOMMatrixReadOnly(t).m42; }catch(x){}
    return e.classList.contains('streak-pop') ? [r[0], Math.round((r[1] - ty) * 10) / 10, r[2], Math.round((r[3] - ty) * 10) / 10] : r; };
  return { pop: P(document.querySelector(sel)), chat: R(chat), chatShown: !!chat && cs.display !== 'none', sat, all,
           edgeOn: document.documentElement.classList.contains('top-edge-on'), rec: window.__rec || [] }; }"""
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
                if SHOTS and scr == "home" and key in ("daily", "update", "rankup", "tierup") and name in ("promax", "ipad11"):
                    pg.screenshot(path=os.path.join(SHOTS, "%s_%s_%s.png" % (TAG, name, key)))
                if SHOTS and key in ("daily", "streak") and name in ("promax", "ipad11") and scr != "home":
                    pg.screenshot(path=os.path.join(SHOTS, "%s_%s_%s_%s.png" % (TAG, name, scr, key)))
                washY = (d["sat"] + 42) if (wash and d["edgeOn"]) else 0
                if wash: chk("%s: the wash model is on here (installed iPhone, notch inset %s)" % (lab, d["sat"]), d["edgeOn"] and d["sat"] > 30, d)
                want = max(c[3] + GAP, washY) if c else None
                # the Home Screen reminder (a Safari tab's Home) is the first thing on the line; a pop-up up with it stacks under it
                ab = dict(d["all"]).get("a2hsbar") if key not in HOME_ONLY else None
                if ab:
                    chk("%s: the Home Screen reminder is on the line (%s, want %s)" % (lab, ab[1], want), want is not None and abs(ab[1] - want) <= 1, d)
                    chk("%s: top %s stacked under the Home Screen reminder (%s)" % (lab, p[1], ab[3]), ab[3] - .5 <= p[1] <= ab[3] + 14, d)
                else:
                    chk("%s: top %s on the line (chat bottom %s + %d = %s)" % (lab, p[1], c and c[3], GAP, want), c is not None and abs(p[1] - want) <= 1, d)
                chk("%s: not above the wash (%s >= %s)" % (lab, p[1], washY), p[1] >= washY - .5, d)
                over = c and not (p[2] <= c[0] or p[0] >= c[2] or p[3] <= c[1] or p[1] >= c[3])
                chk("%s: clear of the chat button (%s / %s)" % (lab, p, c), not over, d)
                # the first frame it is in the document (its entrance's starting point, before it fades in) is above where it settles
                rec = d["rec"]
                if rec:
                    chk("%s: drops in from above (first frame top %.1f, settled %.1f)" % (lab, rec[0][1], p[1]), rec[0][1] < p[1] - .9, rec[:6])
                else:
                    chk("%s: drops in from above (frames recorded)" % lab, False, d["rec"][:6])
                pg.evaluate(CLEAR); pg.wait_for_timeout(200)
        # (3) the update notice and the daily alert together: no overlap, the alert below
        goto(pg, "home", "()=>showHome()")
        pg.evaluate(POPS["update"][0]); pg.wait_for_timeout(700); pg.evaluate(POPS["daily"][0]); pg.wait_for_timeout(1100)
        a = pg.evaluate(READ, "#updatebanner"); b = pg.evaluate(READ, "#dailyalert")
        u, dl = a["pop"], b["pop"]
        chk("%s home: update notice on the line and the daily alert under it, no overlap (%s / %s)" % (name, u, dl),
            u and dl and abs(u[1] - (a["chat"][3] + GAP)) <= 1 and dl[1] >= u[3] - .5, [u, dl])
        if SHOTS and name in ("promax", "ipad11"): pg.screenshot(path=os.path.join(SHOTS, "%s_%s_update+daily.png" % (TAG, name)))
        # late notice: the alert first, the notice a moment later - the alert moves under it
        pg.evaluate(CLEAR); pg.evaluate(POPS["daily"][0]); pg.wait_for_timeout(900); pg.evaluate(POPS["update"][0]); pg.wait_for_timeout(1100)
        a = pg.evaluate(READ, "#updatebanner"); b = pg.evaluate(READ, "#dailyalert")
        u, dl = a["pop"], b["pop"]
        chk("%s home: a notice arriving after the alert still stacks them (%s / %s)" % (name, u, dl), u and dl and dl[1] >= u[3] - .5, [u, dl])
        # a toast with the chat panel really open: on the line where the panel is a sheet from the bottom (a phone); where the
        # panel hangs under the chat button (a tablet) it keeps its place in the button's row, and never lies on the panel
        pg.evaluate(CLEAR)
        pg.evaluate("()=>{ const b = document.querySelector('.chatdock-btn'); if(b) b.click(); }"); pg.wait_for_timeout(1300)
        pg.evaluate("()=>showToast('Chat muted')"); pg.wait_for_timeout(1000)
        q = pg.evaluate("""()=>{ const R = e => { if(!e) return null; const r = e.getBoundingClientRect(); return r.width ? [r.left, r.top, r.right, r.bottom].map(v=>Math.round(v*10)/10) : null; };
            return { open: !!document.querySelector('.chatdock.is-open'), panel: R(document.querySelector('.chatdock.is-open .chatdock-panel')), toast: R(document.getElementById('toast')), chat: R(document.querySelector('.chatdock-btn')) }; }""")
        tp, pp, cc = q["toast"], q["panel"], q["chat"]
        on_panel = bool(tp and pp and not (tp[2] <= pp[0] or tp[0] >= pp[2] or tp[3] <= pp[1] or tp[1] >= pp[3]))
        if pp and cc and pp[1] < cc[3] + GAP + 60:
            chk("%s home, chat open (panel under the button): the toast is clear of the panel (%s / %s)" % (name, tp, pp), q["open"] and tp and not on_panel, q)
        else:
            chk("%s home, chat open (a sheet): the toast is on the line and clear of the sheet (%s / %s)" % (name, tp, pp),
                q["open"] and tp and cc and abs(tp[1] - (cc[3] + GAP)) <= 1 and not on_panel, q)
        pg.evaluate("()=>{ const b = document.querySelector('.chatdock-btn'); if(b && document.querySelector('.chatdock.is-open')) b.click(); }"); pg.wait_for_timeout(900)
        # a tour holds the notices back; when it goes, the notice comes up on the line
        pg.evaluate(CLEAR)
        t = pg.evaluate("""()=>{ pendingNotice = { kind: 'update', info: {} }; const o = document.createElement('div'); o.id = 'tour-overlay'; document.body.appendChild(o);
            syncNoticeVisibility(); const held = !document.getElementById('updatebanner'); o.remove(); tourQuietUntil = 0; syncNoticeVisibility();
            return { held, back: !!document.getElementById('updatebanner') }; }""")
        pg.wait_for_timeout(900)
        a = pg.evaluate(READ, "#updatebanner")
        chk("%s home: a tour holds the update notice back (%s) and it comes up on the line after (%s)" % (name, t, a["pop"]),
            t["held"] and t["back"] and a["pop"] and abs(a["pop"][1] - (a["chat"][3] + GAP)) <= 1, [t, a["pop"], a["chat"]])
        ctx.close()
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    try: run(br)
    finally: br.close()
chk("no page errors (%d)" % len(errs), not errs, errs[:4])
print("ALL PASS" if ok else "SOME FAIL")
sys.exit(0 if ok else 1)
