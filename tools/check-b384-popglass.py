#!/usr/bin/env python3
"""Build 384 r16: every pop-up is the same frosted glass.

Madison, the "Leave Police Academy?" confirm on his iPhone 17 Pro Max: "These pop ups need the Frosted look, why does the font look
weird here by the way??" The confirm family read as a flat navy slab: a .66 dim over a mostly empty page, a dark .5 tint at a 9px blur,
and overlays that were backdrop roots (opacity fade + overflow scroll, or a blur of their own), which leave the sheet blurring nothing.
And its title was forced into Georgia (384 r9, "title in What's new's serif") beside a sans body.

Every pop-up in tools/b384_pop_lib.INVENTORY is opened by the app's own function, over Settings / the Leaderboard / Profile, at an iPhone
17 Pro Max (440x956 @3x) in both classes and an iPad Pro 11" (834x1194) in the academy, and read by SHAPE (never a label):
  (1) glass: a translucent fill (alpha < .75) and a backdrop blur >= 16px with a saturate, on every sheet, settled;
  (2) one glass: every sheet's fill and backdrop-filter is the same pair (the shared tokens), so a new pop-up cannot drift;
  (3) no backdrop root above the sheet: no ancestor up to <body> with opacity < 1, a filter, a backdrop-filter, a mask, a clip-path,
      or its own scroll (overflow auto / scroll), in its settled state (384.52: the chat's leave sheet is on <body> now, like the rest, and
      is read with this one too; tools/check-b384-leavefrost.py proves the blur reaches the page with pixels);
  (4) the dim is thin: the scrim a confirm sits on is <= .5 alpha (every other overlay is read and reported);
  (5) a confirm's title is the app's sans, not a serif stack;
  (6) a tall card scrolls inside itself, never its overlay (a short window, the save-code card).
  python3 tools/check-b384-popglass.py [--against OLD/index.html]    (must FAIL on the build before)
  python3 tools/check-b384-popglass.py --shots DIR                    (the contact-sheet frames: DIR/<key>-<class>-<size>.png)"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import b384_pop_lib as L
from playwright.sync_api import sync_playwright

against = sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else None
shots = sys.argv[sys.argv.index("--shots") + 1] if "--shots" in sys.argv else None
only = set(os.environ.get("ONLY", "").split(",")) - {""}
cb = L.load_cb(against)
if shots: os.makedirs(shots, exist_ok=True)
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:500], flush=True)

READ = """(arg)=>{ const [sel, host] = arg; const e = document.querySelector(sel); if(!e) return null;
  const A = s => { const m = (s||'').match(/rgba?\\(([^)]+)\\)/); if(!m) return null; const p = m[1].split(',').map(x=>parseFloat(x)); return p.length>3 ? p[3] : 1; };
  const cs = getComputedStyle(e), bf = cs.backdropFilter || cs.webkitBackdropFilter || 'none';
  const out = { bg: cs.backgroundColor, alpha: A(cs.backgroundColor), img: cs.backgroundImage.slice(0, 140), bf, op: cs.opacity, w: Math.round(e.getBoundingClientRect().width), h: Math.round(e.getBoundingClientRect().height) };
  out.blur = (bf.match(/blur\\(([\\d.]+)px\\)/)||[])[1]; out.sat = (bf.match(/saturate\\(([\\d.]+)\\)/)||[])[1];
  const bad = []; let a = e.parentElement; const chain = [];
  while(a && a !== document.body){ const c = getComputedStyle(a); chain.push(a.className || a.tagName);
    const why = [];
    if(parseFloat(c.opacity) < 1) why.push('opacity ' + c.opacity);
    if(c.filter && c.filter !== 'none') why.push('filter');
    const abf = c.backdropFilter || c.webkitBackdropFilter; if(abf && abf !== 'none') why.push('backdrop-filter');
    if((c.maskImage && c.maskImage !== 'none') || (c.webkitMaskImage && c.webkitMaskImage !== 'none')) why.push('mask');
    if(c.clipPath && c.clipPath !== 'none') why.push('clip-path');
    if(/auto|scroll/.test(c.overflowY) || /auto|scroll/.test(c.overflowX)) why.push('scroll ' + c.overflowY);
    if(/opacity|filter/.test(c.willChange)) why.push('will-change ' + c.willChange);
    if(why.length) bad.push((a.className || a.tagName) + ': ' + why.join(', '));
    a = a.parentElement; }
  out.bad = bad; out.chain = chain;
  const ov = e.closest(host || '.savecode-card, .chatdock-confirm, .resume-offer, .friend-moment, .installguide-overlay, .unitver, .invite-overlay, .intro-pop') || e.parentElement;
  const b4 = getComputedStyle(ov, '::before'); const ovc = getComputedStyle(ov);
  const layer = A(b4.backgroundColor), plain = A(ovc.backgroundColor);
  out.scrim = (b4.content !== 'none' && b4.content !== 'normal' && layer !== null && layer > 0) ? layer : plain;
  const t = e.querySelector('.savecode-title, .resume-title, .chatdock-confirm-title, .chat-leavesheet-title, .installguide-title');
  out.title = t ? getComputedStyle(t).fontFamily : null;
  return out; }"""

CLEAR = """()=>{ document.querySelectorAll('.savecode-card,.chatdock-confirm,.resume-offer,.friend-moment,.invite-overlay,.intro-pop,.installguide-overlay,.unitver').forEach(n=>n.remove()); }"""

def serif(f):
    f = re.sub(r"sans-serif", "", f or "", flags=re.I)
    return bool(re.search(r"\bserif\b|Georgia|Iowan|Palatino|Times", f))

def run(br, cls, w, h, tag):
    ctx, pg = L.boot(br, cb, w, h, cls)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    pairs = set(); rows = []
    got = pg.evaluate("()=>window.NOVA_CLASS")
    chk("%s is really the %s class (NOVA_CLASS %s)" % (tag, cls, got), got == cls)
    for key, js, sel, kind, bg in L.INVENTORY:
        if only and key not in only: continue
        pg.evaluate(CLEAR); pg.evaluate("()=>{ " + L.BGS[bg] + "; }"); pg.wait_for_timeout(600)
        try: pg.evaluate("()=>{ " + js + "; }")
        except Exception as e: chk("%s %s: opens (%s)" % (tag, key, str(e)[:100]), False); continue
        pg.wait_for_timeout(1100)
        host = ".invite-overlay.chat-members" if key == "chat-members" else None
        # the settled state: a loaded machine can be late with a fade, so wait for the sheet to be fully opaque (and say so if it never is)
        try: pg.wait_for_function("(s)=>{ const e=document.querySelector(s); return !!e && parseFloat(getComputedStyle(e).opacity) >= 1; }", arg=sel, timeout=6000)
        except Exception: pass
        r = pg.evaluate(READ, [sel, host])
        if not r: chk("%s %s: the sheet is on screen (%s)" % (tag, key, sel), False); continue
        if shots: pg.screenshot(path=os.path.join(shots, "%s-%s-%s.png" % (key, cls, "tablet" if w > 600 else "phone")))
        chk("%s %-18s (1) glass: fill alpha %s < .75, blur %spx >= 16, saturate %s, opacity %s" % (tag, key, r["alpha"], r["blur"], r["sat"], r["op"]),
            r["alpha"] is not None and r["alpha"] < .75 and r["blur"] and float(r["blur"]) >= 16 and r["sat"] and float(r["op"]) == 1, r)
        pairs.add((r["img"], r["bf"]))
        chk("%s %-18s (3) nothing above the sheet is a backdrop root (%s)" % (tag, key, " > ".join(reversed(r["chain"]))), not r["bad"], r["bad"])
        if kind == "confirm":
            chk("%s %-18s (4) the dim is thin: %s <= .5" % (tag, key, r["scrim"]), r["scrim"] is not None and r["scrim"] <= .5, r["scrim"])
            chk("%s %-18s (5) the title is the app's sans (%s)" % (tag, key, (r["title"] or "")[:60]), r["title"] and not serif(r["title"]), r["title"])
        else:
            print("     %s %-18s dim %s" % (tag, key, r["scrim"]))
    chk("%s (2) one glass: every sheet has the same fill and blur (%d distinct)" % (tag, len(pairs)), len(pairs) <= 1, sorted(pairs)[:3])
    chk("%s no page errors (%s)" % (tag, errs[:2]), not errs)
    if tag == "phone/academy":
        pg.evaluate(CLEAR); pg.evaluate("()=>{ showAppearance(); }"); pg.wait_for_timeout(500)
        pg.set_viewport_size({"width": 440, "height": 330})
        pg.evaluate("()=>{ syncCode = syncCode || 'TEST-0000-0000'; showSaveCodeCard({mode:'new'}); }"); pg.wait_for_timeout(1100)
        s = pg.evaluate("""()=>{ const sh=document.querySelector('.savecode-sheet'), ov=document.querySelector('.savecode-card'); const r=sh.getBoundingClientRect();
          return { sheetScrolls: sh.scrollHeight > sh.clientHeight + 2 && /auto|scroll/.test(getComputedStyle(sh).overflowY), ovScrolls: ov.scrollHeight > ov.clientHeight + 2 || /auto|scroll/.test(getComputedStyle(ov).overflowY),
                   top: r.top, bottom: r.bottom, vh: innerHeight }; }""")
        chk("%s (6) a short window: the card scrolls inside itself (%s), its overlay does not (%s), and the card stays on screen (%d..%d of %d)" % (tag, s["sheetScrolls"], s["ovScrolls"], s["top"], s["bottom"], s["vh"]),
            s["sheetScrolls"] and not s["ovScrolls"] and s["top"] >= -1 and s["bottom"] <= s["vh"] + 1, s)
    ctx.close()

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    run(br, "academy", 440, 956, "phone/academy")
    run(br, "ifc", 440, 956, "phone/ifc")
    run(br, "academy", 834, 1194, "tablet/academy")
    br.close()
cb.SERVER.shutdown()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
