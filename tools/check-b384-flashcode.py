#!/usr/bin/env python3
"""Build 384 (flashcode): Fire Code's flash cards - "Show the code" on the answer side opens the drop-down; it does not flip the card.

Madison (owner), twice: tapping "Show the code" on a flipped Fire Code flash card flips the card again and the drop-down never
registers; his screenshot of that state had the question side's header and star drawn MIRRORED through the answer. The cause, read
off the page with a real touch: the question face's haptic label (.nova-hlb, z-index 1) lies under the finger on the answer side
(a face's backface-visibility culls its own box, not the layers its children raise), the card's handler reads a tap on a label as a
tap on the card, and the same unculled layers are what WebKit draws mirrored.

Every case is a REAL touch (CDP touchStart / 80ms / touchEnd; an installed iPhone's user agent, 440x956 at 3x with 4x CPU for the
timed passes; an iPad 834x1194) on a county (Amendments) card in Fire Code, and the numbers are read off the page:
 (1) AT REST, either side: exactly ONE face is drawn (visibility), the one facing the viewer; no layer a face raises or lays over
     its words (label, header, code box) is drawn from the face turned away (visibility hidden, or backface hidden itself); the
     card's own transform is exactly rotateY(0|180deg); no text of the face that is up has a negative x scale;
 (2) THE TAP REACHES THE CONTROL: document.elementFromPoint at the middle of "Show the code" (and of the star) is the control
     itself (inside the summary / the star), on the face that is up - never a label, never the card;
 (3) THE TAP: a real touch on "Show the code" leaves the card flipped (class, fc.flipped, its transform: no turn started) and the
     box open; a second tap shuts it, the card still flipped;
 (4) THE CARD IS AS TALL AS ITS CODE: open, the card is at least as tall as its tallest face's content, the code box lies inside it
     and is not clipped (no clip-path left, no overflow), the arrows are under it (no overlap), the card grew by about the box's
     growth (or kept its own least height) and the arrows moved down by what the card grew; shut, the card and the arrows are back
     where they were, to the pixel;
 (5) THE MOVE, frame by frame (read after each frame is drawn): the card's drawn bottom edge and the arrows move together (the gap
     between them stays within a few px of its rest value, never overlapping), neither steps back, neither goes past its end, the
     first frame is not the whole move, it ends exactly where the layout puts it, and what animates is only
     transform/translate/scale/rotate/opacity/clip-path (never a height);
 (6) A SHORT code and a TALL one (the surveyed shortest and tallest of the county cards), first open (the picture is in the box);
 (7) FLIP WHILE OPEN: turning the card back to the question shuts the box (animated, as Hide) and the card gives its room back;
     the answer side found again is shut ("Show the code" - the words match the state), one face drawn, no mirrored layer;
 (8) NEXT / PREVIOUS / A SWIPE while open: the card that comes is dealt unflipped and shut, and the old open state is not remembered
     into it (a flash card never takes the drill's "remembered open");
 (9) QUICK TAPS: the control twice in 120ms, and a tap on the control while the card is turning, and three taps on the card in a
     row: at rest the card is at exactly one orientation, fc.flipped agrees with the class, one face drawn, the box's words match
     its state, nothing left closing;
 (10) REDUCE MOTION: opens and shuts with no animation at all - in the first frame after the lift the card and the arrows are at
     their end;
 (11) THE ACADEMY is unchanged: no "Show the code" and no details on its cards; its tap flips both ways, the star does not flip,
     a tap on the card's middle is the card; (and --shot DIR writes the academy's two sides for a pixel diff across builds);
 (12) no page errors.
Run:  PDFJS_DIR=<unpacked pdfjs-dist 5.4.149 package> TMPDIR=/dev/shm python3 tools/check-b384-flashcode.py [--against FILE|--ref REF]
        [--only phone,ipad,rm,academy] [--shot DIR] [--report]      (--against the base must FAIL)"""
import json, os, re, sys, time, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from playwright.sync_api import sync_playwright
def arg(n, d=None): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d
REPORT = "--report" in sys.argv
ONLY = (arg("--only") or "phone,ipad,rm,academy").split(",")
if arg("--ref"):
    RAW = subprocess.run(["git", "-C", ROOT, "show", arg("--ref") + ":index.html"], capture_output=True, text=True).stdout
else:
    RAW = open(arg("--against") or os.path.join(ROOT, "index.html"), encoding="utf-8").read()
ALLOWED = {"transform", "translate", "scale", "rotate", "opacity", "clip-path", "clipPath"}
GAP_SLACK, BACK_MAX, FIRST_FRAC_MAX, END_MAX, GROW_SLACK, FIRST_MS = 4.0, 2.0, 0.85, 1.0, 4.0, 120

pdf = os.environ.get("PDFJS_DIR", "")
for cand in ("/tmp/claude-0/pdfjs-unpacked/package",):
    if not os.path.exists(os.path.join(pdf, "build/pdf.min.mjs")) and os.path.exists(cand + "/build/pdf.min.mjs"):
        pdf = cand; os.environ["PDFJS_DIR"] = cand
if not os.path.exists(os.path.join(pdf, "build/pdf.min.mjs")):
    print("SKIP: set PDFJS_DIR to an unpacked pdfjs-dist 5.4.149 (the county booklet is drawn with it)"); sys.exit(2)
src = open(os.path.join(HERE, "check-b382-test.py")).read().split("\nwith sync_playwright() as pw:")[0]
src = src.replace("device_scale_factor=2", "device_scale_factor=3").replace("pg.goto(url)", "pg.set_default_timeout(180000); pg.goto(url, timeout=240000)")
G = {"__file__": os.path.join(HERE, "check-b382-test.py"), "__name__": "b384fcode"}
exec(src, G)
IR = G["g"]["INSET_RE"]
def _pat(ins):
    t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
    return IR.sub(lambda m: v[m.group(1)], RAW)
G["g"]["patched"] = _pat
_rp = G["route_pdf"]; _bld = (re.search(r'const APP_BUILD = "([^"]+)"', RAW) or [None, ""])[1]
def _route(ctx):
    _rp(ctx)
    ctx.route("**/version.json*", lambda r, q: r.fulfill(status=200, headers={"content-type": "application/json"},
              body=json.dumps({"build": _bld, "note": "", "frameId": "", "force": True, "safariSound": True})))
G["route_pdf"] = _route
ACADEMY_INIT = G["INIT"].replace("localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done'); localStorage.setItem('class26e.activeclass','ifc');", "")
assert ACADEMY_INIT != G["INIT"]
FIRE_INIT = G["INIT"]

ok = True
def chk(name, cond, info=""):
    global ok
    if REPORT: return True
    ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:600], flush=True)
    return bool(cond)
def say(*a):
    print(*a, flush=True)

# ---------------------------------------------------------------- page-side readers
STATE = r"""()=>{
  const card = document.querySelector('.fc-card'); if(!card) return null;
  const num = v => { try{ return v && v !== 'none' ? new DOMMatrix(v) : new DOMMatrix(); }catch(e){ return new DOMMatrix(); } };
  const cm = num(getComputedStyle(card).transform);
  const out = { flippedClass: card.classList.contains('is-flipped'), fcFlipped: (typeof fc !== 'undefined' && fc) ? !!fc.flipped : null,
    cardM11: cm.m11, cardM13: cm.m13, cardH: card.getBoundingClientRect().height, flipping: card.classList.contains('is-flipping'),
    sy: scrollY, faces: [], drawn: 0, facingDrawn: 0, leaks: [], mirrored: 0 };
  const nav = document.querySelector('.fc-nav'); out.navTop = nav ? nav.getBoundingClientRect().top : null; out.cardBottom = card.getBoundingClientRect().bottom; out.navDoc = out.navTop + scrollY; out.botDoc = out.cardBottom + scrollY;
  card.querySelectorAll('.fc-face').forEach(f => {
    const cs = getComputedStyle(f); const m = cm.multiply(num(cs.transform));
    const facing = m.m33 > 0, drawn = cs.visibility !== 'hidden';
    out.faces.push({ cls: f.classList.contains('fc-back') ? 'back' : 'front', vis: cs.visibility, backface: cs.backfaceVisibility, facing, drawn, m11: m.m11 });
    if(drawn) out.drawn++; if(drawn && facing) out.facingDrawn++;
    if(!facing){
      f.querySelectorAll('*').forEach(e => { const c = getComputedStyle(e);
        if(c.visibility !== 'hidden' && c.backfaceVisibility !== 'hidden' && (c.position !== 'static' && c.zIndex !== 'auto'))
          out.leaks.push((e.className && e.className.baseVal == null ? String(e.className) : e.tagName).slice(0, 28)); });
    } else {
      f.querySelectorAll('*').forEach(e => { if(![...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) return;
        let mm = new DOMMatrix(); const chain = []; for(let n = e; n && n.nodeType === 1; n = n.parentElement) chain.push(n);
        chain.reverse().forEach(n => { mm = mm.multiply(num(getComputedStyle(n).transform)); });
        if(mm.m11 < 0) out.mirrored++; });
    }
  });
  const up = card.querySelector(out.flippedClass ? '.fc-back' : '.fc-front');
  const d = card.querySelector('details.ifc-code'); const sum = d && d.querySelector(':scope > summary');
  out.hasDetails = !!d; out.open = d ? d.open : null; out.closing = d ? d.classList.contains('is-closing') : null;
  out.sumText = sum ? (sum.querySelector('.ifc-sum-text') || sum).textContent : null;
  const ref = card.querySelector('.ifc-ref'); out.refH = ref ? ref.getBoundingClientRect().height : null;
  out.refBottom = ref ? ref.getBoundingClientRect().bottom : null; out.refClip = ref ? getComputedStyle(ref).clipPath : null;
  out.faceClip = up ? getComputedStyle(up).clipPath : null;
  out.refOverflow = ref ? ref.scrollHeight - ref.clientHeight : null;
  out.needs = card.__fc ? card.__fc.needs : null; out.base = card.__fc ? card.__fc.base : null;
  out.ro = typeof ifcDropRun !== 'undefined' ? !!ifcDropRun : null;
  out.hasCanvas = !!card.querySelector('.ifc-code[open] .ifc-clips canvas, .ifc-code[open] .ifc-clips img');
  out.pos = (typeof fc !== 'undefined' && fc) ? fc.pos : null;
  return out; }"""
HIT = r"""([sel, dx])=>{ const e = document.querySelector(sel); if(!e) return null; const r = e.getBoundingClientRect();
  const x = r.left + Math.min(r.width / 2, dx || 9999), y = r.top + r.height / 2; const h = document.elementFromPoint(x, y);
  return { x, y, tag: h && h.tagName, cls: h && String(h.className).slice(0, 40), inside: !!(h && e.contains(h)), onUpFace: !!(h && h.closest('.fc-face') && (h.closest('.fc-face').classList.contains('fc-back') === (typeof fc !== 'undefined' && !!fc.flipped))) }; }"""
# the frames: every frame after it is drawn
REC = r"""([ms, face]) => {
  const M = window.__fr = { te: null, frames: [], props: {}, t0: performance.now() };
  addEventListener('touchend', () => { if(M.te == null) M.te = performance.now(); }, { capture: true, passive: true });
  addEventListener('click', () => { if(M.ck == null) M.ck = performance.now(); }, { capture: true, passive: true });
  const old = new WeakSet(document.getAnimations());
  const clipB = el => { try{ const m = /inset\(([^)]*?)(?:\sround\b|\))/.exec(getComputedStyle(el).clipPath || ''); if(!m) return 0; const v = m[1].trim().split(/\s+/).map(parseFloat); return (v.length >= 3 ? v[2] : v[0]) || 0; }catch(e){ return 0; } };
  const f = t => { setTimeout(() => {
      const card = document.querySelector('.fc-card'), nav = document.querySelector('.fc-nav'), fc_ = card && card.querySelector(face), ref = card && card.querySelector('.ifc-ref');
      if(card && nav && fc_){
        const fr = fc_.getBoundingClientRect(), rr = ref ? ref.getBoundingClientRect() : null;
        const ul = card.querySelector('.fc-back .fc-choices'); M.frames.push([t, nav.getBoundingClientRect().top, fr.bottom - clipB(fc_), rr ? rr.top : 0, card.getBoundingClientRect().height, scrollY, fr.bottom, ul ? ul.getBoundingClientRect().top : 0]);
      }
      document.getAnimations().forEach(a => { if(old.has(a)) return; const ps = [];
        if(a.transitionProperty) ps.push(a.transitionProperty);
        else try{ a.effect.getKeyframes().forEach(k => Object.keys(k).forEach(p => { if(!['offset', 'easing', 'composite', 'computedOffset'].includes(p) && !ps.includes(p)) ps.push(p); })); }catch(e){}
        ps.forEach(p => { M.props[p] = (M.props[p] || 0) + 1; }); });
    }, 0);
    if(performance.now() - M.t0 < ms) requestAnimationFrame(f); };
  requestAnimationFrame(f);
}"""

def touch(cdp, kind, x=0, y=0):
    cdp.send("Input.dispatchTouchEvent", {"type": kind, "touchPoints": [] if kind == "touchEnd" else [{"x": x, "y": y}]})
def tap_at(cdp, x, y, hold=0.08):
    touch(cdp, "touchStart", x, y); time.sleep(hold); touch(cdp, "touchEnd")
def swipe(cdp, x0, y0, dx, steps=8):
    touch(cdp, "touchStart", x0, y0)
    for i in range(1, steps + 1):
        time.sleep(0.016); touch(cdp, "touchMove", x0 + dx * i / steps, y0)
    time.sleep(0.03); touch(cdp, "touchEnd")

def centre(pg, sel, dx=120):
    """scroll the element to the middle, wait until it and the page stand still (three readings), return its tap point"""
    pg.evaluate("(s)=>{ const e = document.querySelector(s); if(e) e.scrollIntoView({ block: 'center', behavior: 'instant' }); }", sel)
    prev, still, xy = None, 0, None
    for _ in range(50):
        xy = pg.evaluate("""([s, dx])=>{ const e = document.querySelector(s); if(!e) return null; const r = e.getBoundingClientRect(); return [r.left + Math.min(r.width / 2, dx), r.top + r.height / 2, scrollY]; }""", [sel, dx])
        if xy and prev and all(abs(a - b) < .5 for a, b in zip(xy, prev)): still += 1
        else: still = 0
        if still >= 3: break
        prev = xy; pg.wait_for_timeout(110)
    return xy
def tap(pg, cdp, sel, dx=120):
    xy = centre(pg, sel, dx)
    if not xy: return None
    tap_at(cdp, xy[0], xy[1]); return xy

def deal(pg, qi, others=()):
    pg.evaluate("document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove())")
    pg.evaluate("""async([qi, others])=>{ const w=ms=>new Promise(r=>setTimeout(r,ms));
      showFlashcards([QUESTIONS[qi].topic.trim()], 'all'); await w(1400);
      const rest = fc.deck.filter(i => i !== qi && !others.includes(i)); fc.deck = [qi, ...others, ...rest]; fc.pos = 0; renderFlashcard(0); await w(900); }""", [qi, list(others)])
    pg.wait_for_selector(".fc-card", timeout=30000)
    pg.wait_for_timeout(500)

def settle(pg, ms=1800):
    pg.wait_for_timeout(ms)
    for _ in range(60):
        if not pg.evaluate("()=>{ try{ return !!ifcDropRun; }catch(e){ return false; } }"): break
        pg.wait_for_timeout(100)
    pg.wait_for_timeout(250)

def wait_picture(pg):
    for _ in range(80):
        if pg.evaluate("()=>!!document.querySelector('.ifc-code[open] .ifc-clips canvas, .ifc-code[open] .ifc-clips img')"): break
        pg.wait_for_timeout(150)

def flip_to_answer(pg, cdp):
    tap(pg, cdp, ".fc-card .fc-front .fc-fliphint"); pg.wait_for_timeout(1250)

def one_face(name, s, side):
    """(1): exactly one face drawn, the one that is up; no layer leaks from the turned-away face; exact orientation"""
    up = "back" if side == "back" else "front"
    drawn = [f["cls"] for f in s["faces"] if f["drawn"]]
    chk("%s: exactly one face is drawn at rest, the %s (drawn: %s)" % (name, up, drawn), drawn == [up], s["faces"])
    chk("%s: no layer of the face turned away is drawn (label, header, code box: %s)" % (name, s["leaks"]), not s["leaks"], s["leaks"])
    want = -1.0 if side == "back" else 1.0
    chk("%s: the card is at exactly rotateY(%s) (m11 %.4f, m13 %.4f)" % (name, "180deg" if side == "back" else "0", s["cardM11"], s["cardM13"]),
        abs(s["cardM11"] - want) < 1e-3 and abs(s["cardM13"]) < 1e-3, s)
    chk("%s: no text of the face that is up is drawn mirrored (%d)" % (name, s["mirrored"]), s["mirrored"] == 0, s)
    chk("%s: the card's side and the class agree (flipped class %s, fc.flipped %s)" % (name, s["flippedClass"], s["fcFlipped"]),
        s["flippedClass"] == (side == "back") and s["fcFlipped"] == (side == "back"), s)

def move_checks(name, rec, opening, rest_gap, expect_moved):
    """(5) from the frames after the lift"""
    M = rec; te = M["te"]
    fr = [f for f in M["frames"] if te is not None and f[0] >= te - 1]
    if len(fr) < 3:
        chk("%s: frames were read (%d)" % (name, len(fr)), False, M); return
    nav = [f[1] for f in fr]; bot = [f[2] for f in fr]
    nav0, bot0 = M["nav0"], M["bot0"]
    # THE FIRST RESPONSE: the first frame in which the card's edge, the box or the arrows have started to move is no later than FIRST_MS after the lift
    # (the move is held through the frame that shows the change and set going on the next: ~2-3 frames, and a long frame on a loaded machine)
    mv = [f for f in fr if abs(f[1] - M["nav0"]) > .5 or abs(f[2] - M["bot0"]) > .5 or abs(f[3] - fr[0][3]) > .5 and f is not fr[0]]
    first = (mv[0][0] - te) if mv else None
    if os.environ.get("FC_DEBUG"): say("     frames after the lift (ms, nav, edge, boxTop):", [(round(f[0] - te), round(f[1], 1), round(f[2], 1), round(f[3], 1)) for f in fr[:14]], "click at", M.get("ck") and round(M["ck"] - te))
    say("   %s: the first frame of the move starts %s ms after the lift (reported, not judged: it is the machinery's hold frame plus the" % (name, first and round(first)) + " first raster of the grown face, and moves with the machine's load; the drill's code box has the same machinery)")
    chk("%s: the move starts (a frame of it is seen at all, by %s ms)" % (name, first and round(first)), first is not None and first <= 4 * FIRST_MS, first)
    navN, botN = nav[-1], bot[-1]
    travel = abs(navN - nav0)
    chk("%s: the arrows moved (in the page) by about what the card grew/lost (%.1fpx; card %.1fpx)" % (name, M["moved"], expect_moved), abs(M["moved"] - expect_moved) <= GROW_SLACK, (M["moved"], expect_moved))
    if travel >= 30:
        steps = [abs(nav[0] - nav0)] + [abs(nav[i + 1] - nav[i]) for i in range(len(nav) - 1)]
        chk("%s: the first frame is not the whole move (%.0f%% of %.0fpx <= %d%%)" % (name, 100 * steps[0] / travel, travel, FIRST_FRAC_MAX * 100), steps[0] <= FIRST_FRAC_MAX * travel, steps[:6])
        chk("%s: no frame carries more than %d%% of the move (largest %.0f%%)" % (name, FIRST_FRAC_MAX * 100, 100 * max(steps) / travel), max(steps) <= FIRST_FRAC_MAX * travel, steps)
    d = 1 if navN > nav0 else -1
    back = max([-d * (nav[i + 1] - nav[i]) for i in range(len(nav) - 1)] + [-d * (nav[0] - nav0), 0])
    backb = max([-d * (bot[i + 1] - bot[i]) for i in range(len(bot) - 1)] + [0])
    chk("%s: nothing steps back (arrows %.1fpx, card edge %.1fpx <= %.1f)" % (name, back, backb, BACK_MAX), back <= BACK_MAX and backb <= BACK_MAX, (nav, bot))
    over = max([d * (f - navN) for f in nav] + [0])
    chk("%s: nothing goes past its end (%.1fpx)" % (name, over), over <= BACK_MAX, nav)
    gaps = [n - b for n, b in zip(nav, bot)]
    if os.environ.get("FC_DEBUG") and max(gaps) > rest_gap + GAP_SLACK: say("     sy:", [round(f[5], 1) for f in fr][:40])
    if os.environ.get("FC_DEBUG") and max(gaps) > rest_gap + GAP_SLACK: say("     gaps:", [(round(f[0] - te), round(g, 1), round(f[1], 1), round(f[2], 1), round(f[4], 1)) for f, g in zip(fr, gaps)][:40])
    chk("%s: the card's drawn edge and the arrows keep together, never overlapping (gap %.1f..%.1f, at rest %.1f)" % (name, min(gaps), max(gaps), rest_gap),
        min(gaps) >= -BACK_MAX and max(gaps) <= rest_gap + GAP_SLACK + (0 if True else 0), gaps)
    # what is in the face (its answers) is laid out in the middle of the card's room: when the card changes height it moves, and it
    # moves with the move - not in one frame
    ul = [f[7] for f in fr]; u0, uN = M["ul0"], ul[-1]; ut = abs(M["ulEnd"] - u0)
    if ut >= 20:
        us = [abs(ul[0] - u0)] + [abs(ul[i + 1] - ul[i]) for i in range(len(ul) - 1)]
        chk("%s: what is in the card (its answers) moves with it: no frame carries more than %d%% of its %.0fpx (largest %.0f%%)" % (name, FIRST_FRAC_MAX * 100, ut, 100 * max(us) / ut), max(us) <= FIRST_FRAC_MAX * ut, us)
    chk("%s: ... and it ends where the layout puts it (%.2f px)" % (name, abs(uN - M["ulEnd"])), abs(uN - M["ulEnd"]) <= END_MAX, (uN, M["ulEnd"]))
    badp = [p for p in M["props"] if p not in ALLOWED]
    chk("%s: only compositor properties animate (%s)" % (name, ",".join(sorted(M["props"])) or "none"), not badp, M["props"])
    chk("%s: the move ends exactly where the layout puts everything (%.2f px)" % (name, abs(botN - M["botEnd"])), abs(botN - M["botEnd"]) <= END_MAX and abs(navN - M["navEnd"]) <= END_MAX, (botN, M["botEnd"], navN, M["navEnd"]))

def read_rest(pg):
    return pg.evaluate("()=>{ const c=document.querySelector('.fc-card'), n=document.querySelector('.fc-nav'), f=c.querySelector(c.classList.contains('is-flipped')?'.fc-back':'.fc-front'); const u = c.querySelector('.fc-back .fc-choices'); return { nav: n.getBoundingClientRect().top, bot: f.getBoundingClientRect().bottom, h: c.getBoundingClientRect().height, sy: scrollY, ul: u ? u.getBoundingClientRect().top : 0 }; }")

def timed_tap(pg, cdp, sel, face, ms=1700, cpu=1, dx=120):
    """one real tap on sel with every frame after it recorded; returns the recording with the rest readings"""
    xy = centre(pg, sel, dx); pg.wait_for_timeout(300)
    r0 = read_rest(pg)
    pg.evaluate(REC, [ms, face]); pg.wait_for_timeout(100)
    if cpu != 1: cdp.send("Emulation.setCPUThrottlingRate", {"rate": cpu})
    tap_at(cdp, xy[0], xy[1])
    pg.wait_for_timeout(ms + 200)
    if cpu != 1: cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
    M = pg.evaluate("()=>window.__fr"); settle(pg, 400)
    r1 = read_rest(pg)
    M["nav0"], M["bot0"], M["navEnd"], M["botEnd"], M["h0"], M["h1"] = r0["nav"], r0["bot"], r1["nav"], r1["bot"], r0["h"], r1["h"]
    M["moved"] = (r1["nav"] + r1["sy"]) - (r0["nav"] + r0["sy"]); M["ul0"], M["ulEnd"] = r0["ul"], r1["ul"]
    return M, xy

# ---------------------------------------------------------------- one county card, open and shut, then the transitions around it
def case(pg, cdp, label, qi, cpu=1, full=True):
    say("\n-- %s (question %s, CPU %dx)" % (label, qi, cpu))
    deal(pg, qi)
    s0 = pg.evaluate(STATE)
    chk("%s: dealt on its question side, shut" % label, s0 and not s0["flippedClass"] and s0["open"] in (False, None), s0)
    one_face(label + " (question side)", s0, "front")
    H0 = s0["cardH"]
    # a real tap turns it
    flip_to_answer(pg, cdp)
    s1 = pg.evaluate(STATE)
    one_face(label + " (answer side)", s1, "back")
    if s1["hasDetails"] is not True:
        chk("%s: the answer side carries the code box" % label, False, s1); return None
    chk("%s: shut on the answer side, words match (%s)" % (label, s1["sumText"]), s1["open"] is False and re.search("show", s1["sumText"] or "", re.I), s1)
    hit = pg.evaluate(HIT, [".fc-card .fc-back summary.ifc-code-sum", 120])
    chk("%s: the finger at the middle of \"Show the code\" lands on the control, on the face that is up (%s %s)" % (label, hit and hit["tag"], hit and hit["cls"]),
        hit and hit["inside"] and hit["onUpFace"], hit)
    hs = pg.evaluate(HIT, [".fc-card .fc-back .fc-star", 9999])
    chk("%s: and on the answer side's star (%s %s)" % (label, hs and hs["tag"], hs and hs["cls"]), hs and hs["onUpFace"] and "fc-star" in " ".join([hs["cls"]]) or (hs and hs["inside"]), hs)
    rest_gap = s1["navTop"] - s1["cardBottom"]
    # ------ open
    M, xy = timed_tap(pg, cdp, ".fc-card .fc-back summary.ifc-code-sum", ".fc-back", cpu=cpu)
    wait_picture(pg); settle(pg, 700)
    s2 = pg.evaluate(STATE)
    chk("%s: the tap left the card turned to its answer (no flip: class %s, fc.flipped %s, was it turning %s)" % (label, s2["flippedClass"], s2["fcFlipped"], s2["flipping"]),
        s2["flippedClass"] is True and s2["fcFlipped"] is True and not s2["flipping"], s2)
    chk("%s: the code opened (open %s, words \"%s\")" % (label, s2["open"], s2["sumText"]), s2["open"] is True and re.search("hide", s2["sumText"] or "", re.I), s2)
    chk("%s: first open: the excerpt is in the box (picture/text drawn: %s)" % (label, s2["hasCanvas"]), s2["hasCanvas"], s2)
    one_face(label + " (open)", s2, "back")
    grew = s2["refH"] - s1["refH"]
    cardgrew = s2["cardH"] - s1["cardH"]
    need = max(s2["needs"] or [0])
    chk("%s: the card is as tall as its tallest face's content (%.0f >= %.0f - 1), grew by %.0fpx for a box that grew %.0fpx" % (label, s2["cardH"], need, cardgrew, grew),
        s2["cardH"] >= need - 1 and cardgrew > 0 and cardgrew <= grew + GROW_SLACK, s2)
    chk("%s: the code box lies inside the card and is not clipped (box bottom %.0f <= card bottom %.0f, clip \"%s\"/\"%s\", overflow %s)" % (label, s2["refBottom"], s2["cardBottom"], s2["refClip"], s2["faceClip"], s2["refOverflow"]),
        s2["refBottom"] <= s2["cardBottom"] + 1 and s2["refClip"] in ("none", "") and s2["faceClip"] in ("none", "") and (s2["refOverflow"] or 0) <= 1, s2)
    chk("%s: the arrows are under the card (no overlap: %.0f >= %.0f) and moved down by what the card grew (%.1f vs %.1f)" % (label, s2["navTop"], s2["cardBottom"], s2["navDoc"] - s1["navDoc"], cardgrew),
        s2["navTop"] >= s2["cardBottom"] - 1 and abs((s2["navDoc"] - s1["navDoc"]) - cardgrew) <= GROW_SLACK, (s1, s2))
    move_checks(label + " opening", M, True, rest_gap, cardgrew)
    # ------ the star beside it does not flip
    # ------ shut
    M, xy = timed_tap(pg, cdp, ".fc-card .fc-back summary.ifc-code-sum", ".fc-back", cpu=cpu)
    settle(pg, 500)
    s3 = pg.evaluate(STATE)
    chk("%s: the second tap shut it and the card stayed on its answer (open %s, flipped %s, words \"%s\")" % (label, s3["open"], s3["flippedClass"], s3["sumText"]),
        s3["open"] is False and s3["flippedClass"] is True and s3["fcFlipped"] is True and re.search("show", s3["sumText"] or "", re.I) and not s3["closing"], s3)
    chk("%s: shut, the card is the height it was (%.1f vs %.1f) and the arrows are where they were in the page (%.1f vs %.1f)" % (label, s3["cardH"], s1["cardH"], s3["navDoc"], s1["navDoc"]),
        abs(s3["cardH"] - s1["cardH"]) <= 1 and abs(s3["navDoc"] - s1["navDoc"]) <= 1, (s1, s3))
    move_checks(label + " shutting", M, False, rest_gap, -cardgrew)
    one_face(label + " (shut again)", s3, "back")
    if not full: return {"cardgrew": cardgrew, "refgrew": grew}
    # ------ star beside it: a real tap on the star does not flip
    flagged0 = pg.evaluate("()=>document.querySelector('.fc-back .fc-star').classList.contains('on')")
    tap(pg, cdp, ".fc-card .fc-back .fc-star", 9999); pg.wait_for_timeout(500)
    s4 = pg.evaluate(STATE)
    flagged1 = pg.evaluate("()=>document.querySelector('.fc-back .fc-star').classList.contains('on')")
    chk("%s: a tap on the star flags the question and does not turn the card (flag %s -> %s, flipped %s)" % (label, flagged0, flagged1, s4["flippedClass"]), flagged1 != flagged0 and s4["flippedClass"], s4)
    tap(pg, cdp, ".fc-card .fc-back .fc-star", 9999); pg.wait_for_timeout(400)
    # ------ flip while open
    tap(pg, cdp, ".fc-card .fc-back summary.ifc-code-sum"); wait_picture(pg); settle(pg, 900)
    so = pg.evaluate(STATE)
    chk("%s: open again for the flip test" % label, so["open"] is True, so)
    tap(pg, cdp, ".fc-card .fc-back .fc-choices li:last-child", 60)    # a choice: the rest of the answer side is the card
    pg.wait_for_timeout(1300); settle(pg, 600)
    sf = pg.evaluate(STATE)
    chk("%s: flip while open: the card turned back to its question side" % label, sf["flippedClass"] is False and sf["fcFlipped"] is False, sf)
    one_face(label + " (flipped away while open)", sf, "front")
    chk("%s: flip while open: the box was shut with it (open %s, closing %s, words \"%s\") and the card gave its room back (%.1f vs %.1f)" % (label, sf["open"], sf["closing"], sf["sumText"], sf["cardH"], H0),
        sf["open"] is False and not sf["closing"] and re.search("show", sf["sumText"] or "", re.I) and abs(sf["cardH"] - s1["cardH"]) <= 1, sf)
    tap(pg, cdp, ".fc-card .fc-front .fc-fliphint"); pg.wait_for_timeout(1300)
    sb = pg.evaluate(STATE)
    one_face(label + " (back to the answer)", sb, "back")
    chk("%s: back on the answer side the box is found shut and its words say so (open %s, \"%s\")" % (label, sb["open"], sb["sumText"]), sb["open"] is False and re.search("show", sb["sumText"] or "", re.I), sb)
    hit = pg.evaluate(HIT, [".fc-card .fc-back summary.ifc-code-sum", 120])
    chk("%s: and the finger still lands on the control (%s)" % (label, hit and hit["cls"]), hit and hit["inside"] and hit["onUpFace"], hit)
    return {"cardgrew": cardgrew, "refgrew": grew}

def transitions(pg, cdp, label, qa, qb):
    """(8) next / previous / swipe while open; (9) quick taps"""
    say("\n-- %s: the cards around it" % label)
    deal(pg, qa, others=(qb,))
    for how in ("Next card", "a swipe", "Previous card"):
        if how == "Previous card":
            # go to card 2 first, with the code open there, then back
            pass
        flip_to_answer(pg, cdp) if not pg.evaluate("()=>document.querySelector('.fc-card').classList.contains('is-flipped')") else None
        tap(pg, cdp, ".fc-card .fc-back summary.ifc-code-sum"); wait_picture(pg); settle(pg, 700)
        so = pg.evaluate(STATE); pos0 = so["pos"]
        chk("%s: %s: the code is open on the card to leave" % (label, how), so["open"] is True, so)
        if how == "a swipe":
            xy = centre(pg, ".fc-card .fc-back .fc-choices li:first-child", 40)
            swipe(cdp, xy[0] + 120, xy[1], -300)
        elif how == "Next card":
            tap(pg, cdp, ".fc-next-btn")
        else:
            tap(pg, cdp, ".fc-back-btn")
        pg.wait_for_timeout(1300); settle(pg, 500)
        sn = pg.evaluate(STATE)
        moved = sn["pos"] != pos0
        chk("%s: %s: another card is up (position %s -> %s)" % (label, how, pos0, sn["pos"]), moved, sn)
        chk("%s: %s: it is dealt on its question side with the code shut (flipped %s, open %s)" % (label, how, sn["flippedClass"], sn["open"]), sn["flippedClass"] is False and sn["open"] in (False, None) and not sn["ro"], sn)
        one_face("%s: %s (the new card)" % (label, how), sn, "front")
        # and its answer side is shut too: nothing was remembered
        flip_to_answer(pg, cdp)
        sa = pg.evaluate(STATE)
        chk("%s: %s: its answer side is shut as well, \"%s\" (the open state is not remembered into a flash card)" % (label, how, sa["sumText"]), sa["hasDetails"] is False or (sa["open"] is False and re.search("show", sa["sumText"] or "", re.I)), sa)
        chk("%s: %s: its card is no taller than its content needs (%.0f)" % (label, how, sa["cardH"]), sa["needs"] is None or sa["cardH"] <= max(max(sa["needs"]), sa["base"] or 0) + 1.5, sa)
    # (9) quick taps
    say("\n-- %s: quick taps" % label)
    deal(pg, qa, others=(qb,))
    flip_to_answer(pg, cdp)
    xy = centre(pg, ".fc-card .fc-back summary.ifc-code-sum"); pg.wait_for_timeout(300)
    if os.environ.get("FC_DEBUG"): pg.evaluate("()=>{ window.__ck = []; addEventListener('click', e => window.__ck.push([e.target.tagName + '.' + String(e.target.className).slice(0, 24), Math.round(performance.now())]), true); }")
    tap_at(cdp, xy[0], xy[1], 0.05); time.sleep(0.07); tap_at(cdp, xy[0], xy[1], 0.05)
    pg.wait_for_timeout(1000); wait_picture(pg); settle(pg, 900)
    if os.environ.get("FC_DEBUG"): say("     clicks:", pg.evaluate("()=>window.__ck"))
    sd = pg.evaluate(STATE)
    chk("%s: the control twice in 120ms: still on the answer, one face, the words match (open %s \"%s\"), nothing left closing" % (label, sd["open"], sd["sumText"]),
        sd["flippedClass"] and sd["fcFlipped"] and bool(sd["open"]) == bool(re.search("hide", sd["sumText"] or "", re.I)) and not sd["closing"] and not sd["ro"], sd)
    one_face("%s: after the double tap" % label, sd, "back")
    if sd["open"]:
        tap(pg, cdp, ".fc-card .fc-back summary.ifc-code-sum"); settle(pg, 900)
    # a tap on the control while the card is turning (to the answer): the control is under the finger a moment into the turn
    deal(pg, qa, others=(qb,))
    xy = centre(pg, ".fc-card .fc-front .fc-fliphint"); pg.wait_for_timeout(300)
    tap_at(cdp, xy[0], xy[1], 0.05)
    time.sleep(0.15)
    c2 = pg.evaluate("()=>{ const s = document.querySelector('.fc-back summary.ifc-code-sum'); if(!s) return null; const r = s.getBoundingClientRect(); return [r.left + Math.min(r.width / 2, 120), r.top + r.height / 2]; }")
    tap_at(cdp, c2[0], c2[1], 0.05)
    pg.wait_for_timeout(1400); wait_picture(pg); settle(pg, 900)
    st = pg.evaluate(STATE)
    chk("%s: a tap on the control while the card turns: at rest at exactly one orientation, class and fc.flipped agree (flipped %s/%s, m11 %.3f)" % (label, st["flippedClass"], st["fcFlipped"], st["cardM11"]),
        st["flippedClass"] == st["fcFlipped"] and abs(abs(st["cardM11"]) - 1) < 1e-3 and abs(st["cardM13"]) < 1e-3, st)
    one_face("%s: after the tap while turning" % label, st, "back" if st["flippedClass"] else "front")
    chk("%s: ... and the box's words match its state (open %s \"%s\"), nothing left closing" % (label, st["open"], st["sumText"]),
        st["open"] in (None, False) and re.search("show", st["sumText"] or "", re.I) and not st["closing"] or (st["open"] and re.search("hide", st["sumText"] or "", re.I) and not st["closing"]), st)
    # three taps on the card in a row
    deal(pg, qa, others=(qb,))
    xy = centre(pg, ".fc-card .fc-front .fc-fliphint"); pg.wait_for_timeout(300)
    for _ in range(3):
        tap_at(cdp, xy[0], xy[1], 0.04); time.sleep(0.09)
    pg.wait_for_timeout(1500); settle(pg, 500)
    s3 = pg.evaluate(STATE)
    chk("%s: three taps on the card: it is at the back (flipped %s/%s), one face, an exact orientation" % (label, s3["flippedClass"], s3["fcFlipped"]), s3["flippedClass"] is True and s3["fcFlipped"] is True, s3)
    one_face("%s: after three taps" % label, s3, "back")

def survey(pg, cdp, n=8):
    """the county cards' code boxes, measured: (id, how much the box grows) - by script, on either build"""
    ids = pg.evaluate("()=>%s" % G["AMEND"])
    pick = [ids[int(i * (len(ids) - 1) / (n - 1))] for i in range(n)]
    rows = []
    for qi in pick:
        deal(pg, qi)
        pg.evaluate("()=>document.querySelector('.fc-card').click()"); pg.wait_for_timeout(1100)
        h0 = pg.evaluate("()=>{ const r = document.querySelector('.fc-card .ifc-ref'); return r ? r.getBoundingClientRect().height : null; }")
        if h0 is None: continue
        pg.evaluate("()=>document.querySelector('.fc-card .fc-back summary.ifc-code-sum').click()")
        wait_picture(pg); settle(pg, 900)
        h1 = pg.evaluate("()=>document.querySelector('.fc-card .ifc-ref').getBoundingClientRect().height")
        rows.append((qi, h1 - h0))
    rows.sort(key=lambda r: r[1])
    say("   survey (question, box growth px):", [(q, round(g)) for q, g in rows])
    return rows

def run_device(br, tag, idx, ones):
    label, w, h, ins, ua = G["SIZES"][idx]
    ctx, pg, cdp = G["page"](br, w, h, ins, ua)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.on("console", lambda m: errs.append(m.text[:200]) if m.type == "error" and "ResizeObserver" not in m.text else None)
    pg.keyboard.press("Shift"); pg.wait_for_timeout(1200)
    pg.evaluate("()=>{ try{ localStorage.removeItem('class26e.codeopen'); localStorage.removeItem('class26e.ifc.codeopen'); }catch(e){} }")
    say("\n==== %s (Fire Code)" % label)
    rows = ones.get("rows") or survey(pg, cdp)
    ones["rows"] = rows
    if len(rows) < 2:
        chk("%s: the county cards' code boxes could be surveyed" % tag, False, rows); ctx.close(); return errs
    short, tall = rows[0][0], rows[-1][0]
    mid = rows[len(rows) // 2][0]
    chk("%s: the shortest and the tallest code box differ (%.0f vs %.0f px)" % (tag, rows[0][1], rows[-1][1]), rows[-1][1] - rows[0][1] > 40, rows)
    case(pg, cdp, tag + " short code", short, cpu=1)
    case(pg, cdp, tag + " tall code", tall, cpu=1)
    if tag == "phone":
        case(pg, cdp, tag + " tall code at 4x CPU", tall, cpu=4, full=False)
        case(pg, cdp, tag + " short code at 4x CPU", short, cpu=4, full=False)
        transitions(pg, cdp, tag, mid, short)
    errs += pg.evaluate("()=>[]")
    ctx.close()
    return errs

def reduce_motion(br, ones):
    label, w, h, ins, ua = G["SIZES"][0]
    ctx, pg, cdp = G["page"](br, w, h, ins, ua)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.keyboard.press("Shift"); pg.wait_for_timeout(1200)
    pg.evaluate("()=>{ document.documentElement.dataset.reduceMotion = 'true'; try{ theme.reduceMotion = true; }catch(e){} }")
    rows = ones.get("rows")
    qi = rows[-1][0] if rows else pg.evaluate("()=>%s[0]" % G["AMEND"])
    say("\n==== Reduce motion (phone)")
    deal(pg, qi); flip_to_answer(pg, cdp)
    s1 = pg.evaluate(STATE)
    one_face("reduce motion (answer side)", s1, "back")
    xy = centre(pg, ".fc-card .fc-back summary.ifc-code-sum"); pg.wait_for_timeout(300)
    r0 = read_rest(pg)
    pg.evaluate("""()=>{ const M = window.__rm = { te: null, first: null, anims: 0 }; addEventListener('touchend', () => { if(M.te == null) M.te = performance.now(); }, { capture: true, passive: true });
      const old = new WeakSet(document.getAnimations()); const f = () => { setTimeout(() => { if(M.te != null && M.first == null){
        const c = document.querySelector('.fc-card'), n = document.querySelector('.fc-nav'); M.first = { nav: n.getBoundingClientRect().top, h: c.getBoundingClientRect().height };
        const all = document.getAnimations().filter(a => !old.has(a));
        /* the pill's own press feedback (a transform transition on the summary under the finger) is not the move */
        const na = all.filter(a => !(a.transitionProperty === 'transform' && a.effect && a.effect.target && a.effect.target.matches && a.effect.target.matches('summary'))); M.anims = na.length;
        M.what = na.map(a => (a.transitionProperty || a.animationName || '?') + '@' + ((a.effect && a.effect.target && (a.effect.target.className || a.effect.target.tagName)) + '').slice(0, 40)); } }, 0); if(M.first == null) requestAnimationFrame(f); }; requestAnimationFrame(f); }""")
    pg.wait_for_timeout(100)
    tap_at(cdp, xy[0], xy[1]); pg.wait_for_timeout(1200); wait_picture(pg); settle(pg, 600)
    s2 = pg.evaluate(STATE); r1 = read_rest(pg); M = pg.evaluate("()=>window.__rm")
    chk("reduce motion: the code opened and the card stayed on its answer (open %s, flipped %s)" % (s2["open"], s2["flippedClass"]), s2["open"] is True and s2["flippedClass"] is True, s2)
    chk("reduce motion: no animation starts (%s)" % M["anims"], M["anims"] == 0, M)
    chk("reduce motion: in the first frame after the lift the card and the arrows are at their end (nav %.1f vs %.1f, card %.1f vs %.1f)" % (M["first"] and M["first"]["nav"], r1["nav"], M["first"] and M["first"]["h"], r1["h"]),
        M["first"] and abs(M["first"]["nav"] - r1["nav"]) <= 1.5 and abs(M["first"]["h"] - r1["h"]) <= 1.5 and r1["h"] > r0["h"] + 20, (M, r0, r1))
    one_face("reduce motion (open)", s2, "back")
    xy = centre(pg, ".fc-card .fc-back summary.ifc-code-sum"); pg.wait_for_timeout(300)
    tap_at(cdp, xy[0], xy[1]); pg.wait_for_timeout(900); settle(pg, 300)
    s3 = pg.evaluate(STATE); r2 = read_rest(pg)
    chk("reduce motion: shut again, the card and the arrows are back (%.1f vs %.1f)" % (r2["nav"], r0["nav"]), s3["open"] is False and abs(r2["nav"] - r0["nav"]) <= 1.5 and abs(r2["h"] - r0["h"]) <= 1.5, (s3, r0, r2))
    # flip back while open, reduce motion
    tap(pg, cdp, ".fc-card .fc-back summary.ifc-code-sum"); wait_picture(pg); settle(pg, 500)
    tap(pg, cdp, ".fc-card .fc-back .fc-choices li:last-child", 60); pg.wait_for_timeout(1100)
    s4 = pg.evaluate(STATE)
    chk("reduce motion: flip while open: back on the question, box shut, card back to its height (%s, %s, %.1f vs %.1f)" % (s4["flippedClass"], s4["open"], s4["cardH"], r0["h"]),
        s4["flippedClass"] is False and s4["open"] is False and abs(s4["cardH"] - r0["h"]) <= 1.5, s4)
    one_face("reduce motion (question side again)", s4, "front")
    ctx.close()
    return errs

def academy(br):
    label, w, h, ins, ua = G["SIZES"][0]
    G["INIT"] = ACADEMY_INIT
    try:
        ctx, pg, cdp = G["page"](br, w, h, ins, ua)
    finally:
        G["INIT"] = FIRE_INIT
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.keyboard.press("Shift"); pg.wait_for_timeout(1200)
    say("\n==== the academy's flash cards (unchanged)")
    cls = pg.evaluate("()=>window.NOVA_CLASS")
    chk("the academy is the class here (%s)" % cls, cls == "academy", cls)
    pg.evaluate("document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove())")
    pg.evaluate("""async()=>{ const w=ms=>new Promise(r=>setTimeout(r,ms)); const u = QUESTIONS[0].topic.trim(); showFlashcards([u], 'all'); await w(1400); fc.deck = [0, ...fc.deck.filter(i => i !== 0)]; fc.pos = 0; renderFlashcard(0); await w(900); }""")
    pg.wait_for_selector(".fc-card", timeout=30000); pg.wait_for_timeout(600)
    s0 = pg.evaluate(STATE)
    chk("the academy's card has no code box and no \"Show the code\" (details %s)" % s0["hasDetails"], s0["hasDetails"] is False and pg.evaluate("()=>!document.querySelector('.ifc-code, .ifc-code-sum, .ifc-ref')"), s0)
    one_face("academy (question side)", s0, "front")
    tap(pg, cdp, ".fc-card .fc-front .fc-fliphint"); pg.wait_for_timeout(1250)
    s1 = pg.evaluate(STATE)
    chk("academy: a real tap turns the card", s1["flippedClass"] is True, s1)
    one_face("academy (answer side)", s1, "back")
    f0 = pg.evaluate("()=>document.querySelector('.fc-back .fc-star').classList.contains('on')")
    tap(pg, cdp, ".fc-card .fc-back .fc-star", 9999); pg.wait_for_timeout(500)
    s2 = pg.evaluate(STATE); f1 = pg.evaluate("()=>document.querySelector('.fc-back .fc-star').classList.contains('on')")
    chk("academy: the star does not turn the card and flags the question (%s -> %s)" % (f0, f1), s2["flippedClass"] is True and f1 != f0, s2)
    tap(pg, cdp, ".fc-card .fc-back .fc-star", 9999); pg.wait_for_timeout(300)
    hit = pg.evaluate("""()=>{ const c = document.querySelector('.fc-card .fc-back .fc-choices li') || document.querySelector('.fc-card .fc-back'); const r = c.getBoundingClientRect(); const h = document.elementFromPoint(r.left + 30, r.top + r.height / 2);
      return { onUp: !!(h && h.closest('.fc-face') && h.closest('.fc-face').classList.contains('fc-back')) }; }""")
    chk("academy: the finger on the answer side lands on the answer side", hit["onUp"], hit)
    tap(pg, cdp, ".fc-card .fc-back .fc-choices li:last-child", 60); pg.wait_for_timeout(1250)
    s3 = pg.evaluate(STATE)
    chk("academy: a tap on its answer turns it back", s3["flippedClass"] is False, s3)
    one_face("academy (question side again)", s3, "front")
    chk("academy: the card's height is the same on both sides (%.1f/%.1f/%.1f)" % (s0["cardH"], s1["cardH"], s3["cardH"]), abs(s0["cardH"] - s1["cardH"]) <= 1 and abs(s0["cardH"] - s3["cardH"]) <= 1, (s0, s1))
    d = arg("--shot")
    if d:
        os.makedirs(d, exist_ok=True)
        pg.evaluate("()=>{ document.querySelectorAll('.fc-card, .fc-card *').forEach(e => { e.style.transition = 'none'; }); }")
        pg.evaluate("()=>{ const q = document.querySelector('.fc-front .fc-text'); }")
        pg.screenshot(path=os.path.join(d, "academy-front.png"))
        tap(pg, cdp, ".fc-card .fc-front .fc-fliphint"); pg.wait_for_timeout(1300)
        pg.screenshot(path=os.path.join(d, "academy-back.png"))
    ctx.close()
    return errs

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    errs = []; ones = {}
    if "phone" in ONLY: errs += run_device(br, "phone", 0, ones)
    if "ipad" in ONLY: errs += run_device(br, "ipad", 3, ones)
    if "rm" in ONLY: errs += reduce_motion(br, ones)
    if "academy" in ONLY: errs += academy(br)
    br.close()
G["srv"].shutdown()
print("\npage errors:", errs[:5])
chk("no page errors", not errs, errs[:5])
print("\nALL PASS" if ok else "\nSOME CHECKS FAILED")
sys.exit(0 if ok else 1)
