#!/usr/bin/env python3
"""Build 384.131 (frostfix): every sheet and pop-up is the person card's glass, and the person card is the OLD frost again.

Madison, Test history's new Units sheet on his iPhone: "why does this frost look like that. The old type of frost we had looked better.
The old frost we had on like when you clicked someone on the leaderboard, the box that came up had a really nice frost. You changed it
too but the old one was so awesome. Revert that and ensure it's app cohesive where needed."

The person card's glass was changed once on main: 384 r16 (on main from 384.19) swapped the build-382 recipe (a dark neutral .5 pane,
blur 9px at saturate 1.9, a .11 rim, over a .5 dim) for a lighter, bluer .42 pane at 22px over a .4 dim, and the Units sheet took the
same tokens. So the reference is READ OFF THE PAGE of the build that had the old frost (build 382, git a330ee8; FROSTFIX_REF=FILE
overrides): its person card over the Leaderboard, opened by the app's own openPersonSheet. Nothing here is a typed number.

  (0) the reference: build 382's person card has a blurring backdrop-filter and a translucent fill (a reference that reads nothing
      cannot pass anything);
  (1) this build's person card has the reference's recipe: fill colour, the sheen gradient's stops, blur / saturate / brightness,
      the rim, the shadow, and the dim behind it (its colour times its opacity) - within a small tolerance;
  (2) every pop-up in tools/b384_pop_lib.INVENTORY (Test history's Units and Mode sheets included) has the PERSON CARD'S recipe and the
      reference's, the same six things, on an iPhone 17 Pro Max in both classes and an iPad Pro 11" in the academy;
  (3) the stripe test (check-b384-leavefrost's) on the Units sheet and the person card: a black/white stripe page under each, blur on
      vs off; the page is smeared (ratio < .35) and the unblurred strip has real contrast (>= 20), so a test that sees nothing fails;
  (4) the Units sheet: nothing above it is a backdrop root (opacity / filter / backdrop-filter / mask / clip-path / will-change naming
      one); its words have contrast >= 4.5 against the sheet as drawn (the lightest pixel of a text-free strip of each row); its rows
      and buttons are >= 44px tall;
  (5) no page errors.
  python3 tools/check-b384-frostfix.py [--against OLD/index.html] [--shots DIR] [--quick]   (must FAIL on origin/claude/b384-testhistory)"""
import io, os, re, statistics, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import b384_pop_lib as L
from playwright.sync_api import sync_playwright
from PIL import Image

against = sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else None
shots = sys.argv[sys.argv.index("--shots") + 1] if "--shots" in sys.argv else None
quick = "--quick" in sys.argv
only = set(os.environ.get("ONLY", "").split(",")) - {""}
cb = L.load_cb(against)
if shots: os.makedirs(shots, exist_ok=True)
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:600], flush=True)

# ---- the reference build: the person card as it was through build 382 ----
REF_REV = "a330ee8"
ref_path = os.environ.get("FROSTFIX_REF")
if not ref_path:
    ref_path = os.path.join(tempfile.gettempdir(), "frostfix-ref-382.html")
    if not os.path.exists(ref_path):
        data = subprocess.check_output(["git", "-C", os.path.dirname(HERE), "show", REF_REV + ":index.html"])
        open(ref_path, "wb").write(data)
REF_SRC = open(ref_path, encoding="utf-8").read()
REF_BODY = cb.INSET_RE.sub("0px", REF_SRC).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
REF_BUILD = (re.search(r'const APP_BUILD = "([^"]+)"', REF_SRC) or [None, ""])[1]

BOARD = """(a)=>{ store.leaderboardOptIn=true; const docs=a.names.map((n,i)=>({id:'tstpub'+String(i).padStart(6,'0'), data:()=>Object.assign({}, (typeof boardNumbersOf==='function'?boardNumbersOf(store):{}), {firstName:n, avatarChar:a.chars[i], level:30-i, points:9000-i*300, xp:9000-i*300, weekPoints:100-i, badges:5-(i>>1), correct:900-i*20, hundos:12-i})}));
  onSnapshotResilient=function(r,on){ setTimeout(()=>on({metadata:{fromCache:false}, forEach:f=>docs.forEach(f), docs:docs, size:docs.length}),50); return function(){}; }; showRankings(); }"""
NAMES = ["Avery", "Jordan", "Kim", "Lee", "Sam", "Pat", "Chris", "Dana", "Rowan", "Quinn"]
CHARS = ["alien", "ninja", "wizard", "grizzly", "ghost", "hacker", "zeus", "masked", "marksman", "timekeeper"]
PERSON = "openPersonSheet({ pub:'tstpub000001', firstName:'Jordan', avatarChar:'ninja', level:29, badges:5, points:8700, xp:8700, correct:880, hundos:11, banner:'' })"
HOSTS = ".savecode-card, .chatdock-confirm, .resume-offer, .friend-moment, .installguide-overlay, .unitver, .invite-overlay, .intro-pop, .pop-glass-host"

RECIPE = """(arg)=>{ const [sel, hosts] = arg; const e = document.querySelector(sel); if(!e) return null; const cs = getComputedStyle(e);
  const ov = e.closest(hosts) || e.parentElement; const oc = getComputedStyle(ov), b4 = getComputedStyle(ov, '::before');
  const hasLayer = b4.content !== 'none' && b4.content !== 'normal';
  const r = e.getBoundingClientRect();
  return { fill: cs.backgroundColor, img: cs.backgroundImage, bf: cs.backdropFilter || cs.webkitBackdropFilter || 'none',
    rim: cs.borderTopWidth + ' ' + cs.borderTopColor, shadow: cs.boxShadow, op: cs.opacity,
    scrim: hasLayer ? b4.backgroundColor : oc.backgroundColor, scrimOp: hasLayer ? b4.opacity : '1', ovbg: oc.backgroundColor,
    box: [r.left, r.top, r.width, r.height] }; }"""

NUM = re.compile(r"-?\d*\.?\d+")
def rgba(s):
    m = re.search(r"rgba?\(([^)]+)\)", s or "")
    if not m: return None
    p = [float(x) for x in NUM.findall(m.group(1))]
    return p if len(p) == 4 else p + [1.0]
def bfn(s):
    g = lambda k: float((re.search(k + r"\(([\d.]+)", s or "") or [0, "nan"])[1])
    return [g("blur"), g("saturate"), g("brightness")]
def nums(s): return [float(x) for x in NUM.findall(s or "")]
def scrim_alpha(r):
    a = rgba(r["scrim"]) or [0, 0, 0, 0]
    return a[:3] + [round(a[3] * float(r["scrimOp"]), 3)]
def close(a, b, tol):
    if a is None or b is None or len(a) != len(b): return False
    return all(abs(x - y) <= tol for x, y in zip(a, b))

def compare(r, ref):
    """the six parts of the recipe; returns a list of what differs"""
    bad = []
    if not close(rgba(r["fill"]), rgba(ref["fill"]), 2.01) or abs(rgba(r["fill"])[3] - rgba(ref["fill"])[3]) > .02: bad.append("fill %s vs %s" % (r["fill"], ref["fill"]))
    if not close(nums(r["img"]), nums(ref["img"]), 2.01): bad.append("sheen %s vs %s" % (r["img"][:110], ref["img"][:110]))
    b1, b2 = bfn(r["bf"]), bfn(ref["bf"])
    if not (abs(b1[0] - b2[0]) <= .5 and abs(b1[1] - b2[1]) <= .05 and abs(b1[2] - b2[2]) <= .02): bad.append("blur %s vs %s" % (r["bf"], ref["bf"]))
    if not close(nums(r["rim"]), nums(ref["rim"]), 2.01): bad.append("rim %s vs %s" % (r["rim"], ref["rim"]))
    if not close(nums(r["shadow"]), nums(ref["shadow"]), 2.01): bad.append("shadow %s vs %s" % (r["shadow"][:120], ref["shadow"][:120]))
    if not close(scrim_alpha(r), scrim_alpha(ref), 3.01) or abs(scrim_alpha(r)[3] - scrim_alpha(ref)[3]) > .03: bad.append("dim %s vs %s" % (scrim_alpha(r), scrim_alpha(ref)))
    return bad

CLEAR = """()=>{ document.querySelectorAll('.savecode-card,.chatdock-confirm,.resume-offer,.friend-moment,.invite-overlay,.intro-pop,.installguide-overlay,.unitver,.__stripes').forEach(n=>n.remove());
  try{ closeLeaveChatConfirm(); }catch(e){} }"""
SETTLE = "(s)=>{ const e=document.querySelector(s); return !!e && parseFloat(getComputedStyle(e).opacity) >= 1; }"

def open_person(pg):
    pg.evaluate(CLEAR); pg.evaluate(BOARD, {"names": NAMES, "chars": CHARS}); pg.wait_for_timeout(2200)
    pg.evaluate("()=>{ " + PERSON + "; }"); pg.wait_for_timeout(1200)
    try: pg.wait_for_function(SETTLE, arg=".invite-sheet.person-card", timeout=6000)
    except Exception: pass
    pg.wait_for_timeout(400)

# ---- the stripe test (leavefrost's) ----
STRIPES = "repeating-linear-gradient(90deg,#fff 0 6px,#000 6px 12px)"
def spread(png, box, sc):
    im = Image.open(io.BytesIO(png)).convert("L"); x0, y0, x1, y1 = [int(round(v * sc)) for v in box]
    return statistics.pstdev(list(im.crop((x0, y0, x1, y1)).getdata()))
def stripe(pg, sel, w):
    r = pg.evaluate("""(a)=>{ const e=document.querySelector(a[0]); if(!e) return null; let top=e; while(top.parentElement&&top.parentElement!==document.body) top=top.parentElement;
       const z=parseInt(getComputedStyle(top).zIndex,10); const d=document.createElement('div'); d.className='__stripes';
       d.style.cssText='position:fixed;inset:0;pointer-events:none;z-index:'+(isNaN(z)?0:z-1)+';background:'+a[1]; top.parentElement.insertBefore(d, top);
       const b=e.getBoundingClientRect(); return [b.left,b.top,b.width,b.height]; }""", [sel, STRIPES])
    if not r: return None
    pg.wait_for_timeout(300)
    vh = pg.evaluate("innerHeight")
    x0 = max(r[0], 0) + 4; y0 = max(r[1], 0) + min(r[3], vh - r[1]) * .3; y1 = max(r[1], 0) + min(r[3], vh - r[1]) * .7
    png = pg.screenshot(); sc = Image.open(io.BytesIO(png)).size[0] / w
    on = spread(png, (x0, y0, x0 + 10, y1), sc)
    pg.evaluate("(s)=>{ const e=document.querySelector(s); e.style.setProperty('backdrop-filter','none','important'); e.style.setProperty('-webkit-backdrop-filter','none','important'); }", sel)
    pg.wait_for_timeout(250)
    off = spread(pg.screenshot(), (x0, y0, x0 + 10, y1), sc)
    pg.evaluate("(s)=>{ const e=document.querySelector(s); if(e){ e.style.removeProperty('backdrop-filter'); e.style.removeProperty('-webkit-backdrop-filter'); } document.querySelectorAll('.__stripes').forEach(n=>n.remove()); }", sel)
    return on / max(off, .01), on, off

UNITS_SEL = ".invite-overlay > .invite-sheet.thx-pick-sheet"
UNITS_FIX = ("const T=topicsIn(QUESTIONS), now=Date.now(); store.testHistory=[]; for(let i=0;i<40;i++){ store.testHistory.push({units:[T[i%T.length]],"
             "pct:[100,80,60,92,75][i%5],mode:['drill','exam','game'][i%3],playedAt:now-i*3.6e6*7,n:20,ok:16}); } showTestReviewList();")
UNITS_READ = """()=>{ const sh=document.querySelector('.invite-overlay > .invite-sheet.thx-pick-sheet'); if(!sh) return null;
  const roots=[]; for(let a=sh.parentElement;a&&a!==document.documentElement;a=a.parentElement){ const c=getComputedStyle(a), w=[];
    if(parseFloat(c.opacity)<1) w.push('opacity '+c.opacity); if(c.filter!=='none') w.push('filter');
    const bf=c.backdropFilter||c.webkitBackdropFilter; if(bf&&bf!=='none') w.push('backdrop-filter');
    if((c.maskImage&&c.maskImage!=='none')||(c.webkitMaskImage&&c.webkitMaskImage!=='none')) w.push('mask'); if(c.clipPath&&c.clipPath!=='none') w.push('clip-path');
    if(/opacity|filter|mask|clip-path/.test(c.willChange)) w.push('will-change '+c.willChange);
    if(w.length) roots.push((a.id||a.className||a.tagName)+': '+w.join(', ')); }
  const own=/opacity|filter|mask|clip-path/.test(getComputedStyle(sh).willChange) ? getComputedStyle(sh).willChange : '';
  const R=e=>{ const b=e.getBoundingClientRect(); return [b.left,b.top,b.width,b.height]; };
  const rows=[...sh.querySelectorAll('.thx-pick-row')].map(r=>({ box:R(r), name:R(r.querySelector('.thx-pick-name')), ink:getComputedStyle(r.querySelector('.thx-pick-name')).color,
     n: r.querySelector('.thx-pick-n') ? getComputedStyle(r.querySelector('.thx-pick-n')).color : null }));
  const title=sh.querySelector('.thx-pick-title');
  const btns=[...sh.querySelectorAll('button')].map(b=>({ h:b.getBoundingClientRect().height, t:b.className }));
  return { roots, own, rows, btns, title: title ? getComputedStyle(title).color : null, box:R(sh), vh:innerHeight }; }"""

def L_(c):
    c = [v / 255 for v in c[:3]]
    c = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]
def contrast(a, b):
    la, lb = L_(a), L_(b); return (max(la, lb) + .05) / (min(la, lb) + .05)

def boot_ref(br):
    keep = (cb.BODY, cb.SERVED_BUILD)
    cb.BODY, cb.SERVED_BUILD = REF_BODY, REF_BUILD
    try:
        ctx, pg = cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT, dpr=3, touch=True)
    finally:
        cb.BODY, cb.SERVED_BUILD = keep
    return ctx, pg

def run(br, cls, w, h, tag, ref, first):
    ctx, pg = L.boot(br, cb, w, h, cls)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    print("\n== %s ==" % tag)
    open_person(pg)
    pc = pg.evaluate(RECIPE, [".invite-sheet.person-card", HOSTS])
    chk("%s (1) the person card is on screen" % tag, pc, pc)
    if not pc: ctx.close(); return
    bad = compare(pc, ref)
    chk("%s (1) the person card is the old frost (fill %s, %s, rim %s, dim %.2f)" % (tag, pc["fill"], pc["bf"], pc["rim"], scrim_alpha(pc)[3]), not bad, bad)
    if shots: pg.screenshot(path=os.path.join(shots, "person-%s-%s.png" % (cls, "tablet" if w > 600 else "phone")))
    if first:
        res = stripe(pg, ".invite-sheet.person-card", w)
        chk("%s (3) the person card blurs the page behind it (stripe ratio %.3f, unblurred spread %.1f)" % (tag, res[0], res[2]), res and res[0] < .35 and res[2] >= 20, res)
    for key, js, sel, kind, bg in L.INVENTORY:
        if only and key not in only: continue
        if quick and key not in ("history-units", "class-leave", "whats-new", "invite-chat", "chat-leave", "unlock"): continue
        pg.evaluate(CLEAR); pg.evaluate("()=>{ try{ closeChatDock(); }catch(e){} }"); pg.evaluate("()=>{ " + L.BGS[bg] + "; }"); pg.wait_for_timeout(500)
        try:
            if key == "chat-leave":
                pg.evaluate("()=>{ openChatDock(); }"); pg.wait_for_timeout(900); pg.evaluate("()=>{ confirmLeaveChat('TESTROOM', ()=>{}); }")
            elif key == "history-units":
                pg.evaluate("()=>{ " + UNITS_FIX + " }"); pg.wait_for_timeout(900); pg.evaluate("()=>document.querySelector('#stage .thx-units-btn').click()")
            else:
                pg.evaluate("()=>{ " + js + "; }")
        except Exception as e:
            chk("%s %s opens (%s)" % (tag, key, str(e)[:100]), False); continue
        pg.wait_for_timeout(1100)
        try: pg.wait_for_function(SETTLE, arg=sel, timeout=6000)
        except Exception: pass
        hosts = ".invite-overlay.chat-members" if key == "chat-members" else HOSTS
        r = pg.evaluate(RECIPE, [sel, hosts])
        if not r: chk("%s %-18s is on screen (%s)" % (tag, key, sel), False); continue
        if shots: pg.screenshot(path=os.path.join(shots, "%s-%s-%s.png" % (key, cls, "tablet" if w > 600 else "phone")))
        # the person card's glass, and so the old frost (a sheet that matched a person card that had drifted would hide it)
        bad = compare(r, pc) + ["not the old frost: " + x for x in compare(r, ref)]
        chk("%s %-18s (2) the person card's glass, the old frost (fill %s, %s, dim %.2f)" % (tag, key, r["fill"], r["bf"], scrim_alpha(r)[3]), not bad, bad)
        if key == "history-units":
            u = pg.evaluate(UNITS_READ)
            chk("%s units (4) nothing above the sheet is a backdrop root, nor the sheet a will-change group (%s %s)" % (tag, u["roots"], u["own"]), not u["roots"] and not u["own"], u["roots"])
            # contrast: the sheet as drawn, the lightest pixel of a text-free strip at each visible row's left padding, against each row's ink
            png = pg.screenshot(); im = Image.open(io.BytesIO(png)).convert("RGB"); sc = im.size[0] / w
            worst = 99; worst_n = 99
            sx0 = u["box"][0] + 3
            for row in u["rows"]:
                bx = row["box"]
                if bx[1] < 0 or bx[1] + bx[3] > u["vh"] - 2 or bx[1] + bx[3] > u["box"][1] + u["box"][3] - 70: continue
                strip = im.crop((int((sx0) * sc), int((bx[1] + 6) * sc), int((sx0 + 6) * sc), int((bx[1] + bx[3] - 6) * sc)))
                px = list(strip.getdata()); bgp = max(px, key=lambda p: L_(p)); dkp = min(px, key=lambda p: L_(p))
                ink = rgba(row["ink"])[:3]
                worst = min(worst, contrast(ink, bgp), contrast(ink, dkp))
                if row["n"]: worst_n = min(worst_n, contrast(rgba(row["n"])[:3], bgp), contrast(rgba(row["n"])[:3], dkp))
            chk("%s units (4) the unit names read at contrast %.1f >= 4.5 on the sheet as drawn" % (tag, worst), worst >= 4.5, worst)
            chk("%s units (4) the counts read at contrast %.1f >= 4.5" % (tag, worst_n), worst_n >= 4.5, worst_n)
            hs = [rw["box"][3] for rw in u["rows"]] + [b["h"] for b in u["btns"]]
            chk("%s units (4) every row and button is >= 44px tall (min %.1f)" % (tag, min(hs)), min(hs) >= 44, hs)
            if first:
                res = stripe(pg, sel, w)
                chk("%s units (3) the Units sheet blurs the page behind it (stripe ratio %.3f, unblurred spread %.1f)" % (tag, res[0], res[2]), res and res[0] < .35 and res[2] >= 20, res)
    chk("%s (5) no page errors (%s)" % (tag, errs[:2]), not errs)
    ctx.close()

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    rctx, rpg = boot_ref(br)
    open_person(rpg)
    ref = rpg.evaluate(RECIPE, [".invite-sheet.person-card", HOSTS])
    if shots and ref: rpg.screenshot(path=os.path.join(shots, "person-ref-382-phone.png"))
    rctx.close()
    chk("(0) the reference (build %s) person card is translucent glass (fill %s, %s, dim %s)" % (REF_BUILD, ref and ref["fill"], ref and ref["bf"], ref and scrim_alpha(ref)),
        ref and rgba(ref["fill"])[3] < .75 and bfn(ref["bf"])[0] > 0, ref)
    if ref:
        run(br, "academy", 440, 956, "phone/academy", ref, True)
        if not quick:
            run(br, "ifc", 440, 956, "phone/ifc", ref, False)
            run(br, "academy", 834, 1194, "tablet/academy", ref, False)
    br.close()
cb.SERVER.shutdown()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
