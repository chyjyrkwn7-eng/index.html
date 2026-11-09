#!/usr/bin/env python3
"""r8 (build 384): the top switchers are the iOS 26 segmented control - the bottom tab bar's glass.

Madison, with a recording of Delta's iOS 26 Light / Dark control: "Our top tabs should look and function like this, that's gonna
work and function similar to our bottom tab by the way."

Every top pill switcher found (Profile / Stats / Settings, the Leaderboard's boards, the units screen's levels, the chat sheet's
Friends / Groups / Inbox, the Virtual Room review's Missed / Entire test), on an iPhone 17 Pro Max (440x956) and an iPad Pro 11"
(834x1194), both at 2x with an iPhone / iPad user agent and real touches (CDP Input.dispatchTouchEvent), in both classes (the
academy and Fire Code - in Fire Code only the chat's and the review's exist: it has one Profile tab, no board and one level):

  1. AT REST the thumb is a neutral grey pill: read off the screen inside its round end, low chroma (max-min <= 4 levels), the same
     under two themes (within 2), nowhere near the theme's accent colour, a full pill (radius >= half its height), and the very grey
     the glass lens turns as it sinks into it (the lens's grey coat has the thumb's colour).
  2. A TAP on another segment: the glass lens appears, it is taller than the track and stands out above AND below it, the control
     swells (>= 3% wider; not the chat's, which has no track), the lens sets off over the old segment and glides to the new one
     (monotonic until it is over the new one - the swell and a spring's overshoot carry it a little past - and over it within 3px), and it then lands: the thumb is not drawn while the lens is up (the lens is the thumb), then the lens is gone and the thumb back, centred under the new label within 1px.
  3. A DRAG from the lit segment two-thirds of the way to its neighbour: the lens follows the finger (held, within 14px of it when the
     finger stops), and let go it snaps to the nearest segment, which is picked, the thumb centred under its label within 1px.
     A drag only a quarter of the way snaps back: nothing is picked.
  4. A SWIPE across the content (Profile and the Leaderboard, which swipe between their tabs) moves the thumb - with the lens - to
     the next segment, centred under its label.
  5. REDUCE MOTION: the switcher has its glass, but a tap shows no lens and no swell; the thumb ends centred under the new label.
  6. 44px TARGETS: every segment is hit 21px above and below its centre (the chat's 36px pills reach 4px past themselves).
  7. No page errors.

Labels are read off the page; shapes are asserted, never strings.

  python3 tools/check-b384-toptabs.py                    # both devices, both classes
  python3 tools/check-b384-toptabs.py --against 68c4216  # the build before (a git revision or a file): must FAIL
  python3 tools/check-b384-toptabs.py --only profile     # switchers whose name matches
"""
import json, os, re, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
def arg(n, d=None): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d
ONLY = re.compile(arg("--only")) if arg("--only") else None
AG = arg("--against")
if AG:
    HTML = open(AG, encoding="utf-8").read() if os.path.isfile(AG) else subprocess.check_output(["git", "-C", ROOT, "show", AG + ":index.html"]).decode("utf-8")
else:
    HTML = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
from playwright.sync_api import sync_playwright
from PIL import Image
import io, base64

UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1"
UA_IPAD = "Mozilla/5.0 (iPad; CPU OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1"
DEVICES = [("iPhone 17 Pro Max", 440, 956, (62, 0, 34, 0), UA), ("iPad Pro 11", 834, 1194, (24, 0, 20, 0), UA_IPAD)]
if arg("--sizes"): DEVICES = [d for d in DEVICES if re.search(arg("--sizes"), d[0], re.I)]
CLASSES = (arg("--class") or "academy,ifc").split(",")
OWNER = "xph5b57jbp5a"
SEEN = ("['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card','class26e.getstarted',"
        "'class26e.ifc.intro.seen','class26e.ifc.unithold.tip','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted','class26e.ifc.freshstart'].forEach(k=>localStorage.setItem(k,'1'));"
        "localStorage.setItem('class26e.frame.ok','go-live-1'); ['55124','124256','256578'].forEach(k=>localStorage.setItem('class26e.penal'+k+'.seen','1'));")
INIT = "(()=>{ if(localStorage.getItem('class26e.drill.v1')) return; localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-3843'); " + SEEN + " %s })()"
IFC = ("localStorage.setItem('class26e.ifc.drill.v1', localStorage.getItem('class26e.drill.v1')); localStorage.setItem('class26e.ifc.synccode','TEST-3843');"
       "localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done'); localStorage.setItem('class26e.activeclass','ifc');")

REVIEW = ("showProfile('stats'); const run={missed:[0,1], order:[0,1,2,3], timedOutSet:{}, mode:'exam', vroom:true, attempts:{}, picked:{}, firstPick:{}};"
          "const p=document.createElement('section'); p.className='panel'; p.appendChild(buildRoomReviewTabs(run)); stage.replaceChildren(p); window.scrollTo({top:0, behavior:'instant'});")
# name, how to open it, its selector, its segments, the classes it exists in, whether a swipe across the content changes it, track
SWITCHERS = [
    ("profile", "showProfile('stats');", "#stage .screen-profile > .navsegment.profiletabs", ".iconbtn", ("academy",), True, True),
    ("boards", "showRankings();", "#stage .screen-rankings > .navsegment.profiletabs", ".iconbtn", ("academy",), True, True),
    # (the academy's levels 2 and 3 have no units yet, and a tap on one opens "coming" instead: the fixture gives them two each)
    ("levels", "if(!window.__lv2){ window.__lv2=1; const u0=unitsOfLevel; unitsOfLevel=(lv,all)=>{ const r=u0(lv,all); return r.length ? r : (all||[]).slice(0,2); }; } cfg.mode='drill'; cfg.units=[]; showSetup();", "#stage .setup-levels", ".iconbtn", ("academy",), False, True),
    ("chat", "showHome(); chatDockTab='friends'; openChatDock();", ".chatdock-tabs", ".chatdock-tab", ("academy", "ifc"), False, False),
    ("review", REVIEW, "#stage .rs-tabs", ".rs-tab", ("academy", "ifc"), False, True),
]

ok = True
results = []
def chk(name, cond, info=""):
    global ok
    ok = ok and bool(cond); results.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  -> " + str(info)[:400]), flush=True)

def body_for(ins):
    t, r, b, l = ins; v = {"top": f"{t}px", "right": f"{r}px", "bottom": f"{b}px", "left": f"{l}px"}
    return g["INSET_RE"].sub(lambda m: v[m.group(1)], HTML)

def open_page(br, dev, cls, url):
    name, w, h, ins, ua = dev
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=2, has_touch=True, is_mobile=True, user_agent=ua)
    ctx.add_init_script(g["STANDALONE"]); ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]()))
    pg = ctx.new_page(); b = body_for(ins)
    pg.route("**/index.html", lambda route, request: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    m = re.search(r'const APP_BUILD = "([^"]+)"', b); bld = m.group(1) if m else ""
    pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"},
             body=json.dumps({"build": bld, "note": "", "frameId": "", "force": True, "safariSound": True})))
    d = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]())); d["publicId"] = OWNER; d["firstName"] = "Casey"; d["novaMet"] = 99
    pg.add_init_script(INIT % (json.dumps(json.dumps(d)), IFC if cls == "ifc" else ""))
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.goto(url); pg.wait_for_timeout(3500)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); try{ homeUnlocksOwed=()=>false; }catch(e){} store.novaMet=99;"
                "try{ scheduleWeekRecap=()=>{}; maybeShowWeekRecap=()=>{}; }catch(e){}"
                # an unlock's spotlight (a character the seed's level has earned) lands over the page a few seconds in
                "try{ playUnlockSpotlight=(it,n,of,release)=>{ try{ release && release(); }catch(e){} }; }catch(e){}"
                "document.querySelectorAll('#tour-overlay, #tour-tooltip, #nova-intro, .rs-spot, .unlock-card').forEach(n=>n.remove()); }")
    return ctx, pg, errs

# the switcher's state: its box, each segment (its box and its label's box: the ink of all its text - a count beside a word is part of what is centred), the lit one, the thumb, the lens
STATE = """([sel, segSel])=>{ const s=document.querySelector(sel); if(!s) return null; const r=s.getBoundingClientRect(); if(!r.width) return null;
  const segs=[...s.querySelectorAll(':scope > '+segSel)].filter(b=>!b.hidden && b.offsetWidth>0).map(b=>{ const q=b.getBoundingClientRect();
    const rg=document.createRange(); const tw=document.createTreeWalker(b, NodeFilter.SHOW_TEXT); let L=1e9,R=-1e9,T=1e9,B=-1e9, n;
    while((n=tw.nextNode())){ if(!n.textContent.trim()) continue; if(n.parentElement.closest('[hidden]') || !n.parentElement.getClientRects().length) continue; rg.selectNodeContents(n); for(const x of (n.parentElement!==b ? [n.parentElement.getBoundingClientRect()] : rg.getClientRects())){ if(!x.width) continue; L=Math.min(L,x.left); R=Math.max(R,x.right); T=Math.min(T,x.top); B=Math.max(B,x.bottom); } }
    return { box:[q.left,q.top,q.width,q.height], label:[L,T,R-L,B-T], text:b.textContent.trim(),
             lit: b.classList.contains('active')||b.classList.contains('is-on') }; });
  const sl=s.querySelector(':scope > .seg-slider'); const slr=sl?sl.getBoundingClientRect():null; const cs=sl?getComputedStyle(sl):null;
  const le=s.querySelector(':scope > .seg-lens'); const grey=le?le.querySelector('.tab-lens-grey'):null;
  return { seg:[r.left,r.top,r.width,r.height], segs, thumb: slr&&[slr.left,slr.top,slr.width,slr.height], thumbOp: cs?+cs.opacity:0,
    thumbRadius: cs?parseFloat(cs.borderTopLeftRadius):0, thumbBg: cs?cs.backgroundColor:'', greyBg: grey?getComputedStyle(grey).backgroundColor:null,
    lens: !!le, lensOp: le?+getComputedStyle(le).opacity:0,
    accent: getComputedStyle(document.documentElement).getPropertyValue('--accent').trim(), scrollY: scrollY }; }"""
# every frame: the switcher's box, the lens's (its frame, .tab-lens-body) and opacity, the thumb's box and opacity
SAMPLER = """([sel])=>{ const s=document.querySelector(sel); window.__fr=[]; window.__on=true;
  const le=s.querySelector(':scope > .seg-lens'), lb=le?le.querySelector('.tab-lens-body'):null, sl=s.querySelector(':scope > .seg-slider');
  const f=()=>{ if(!window.__on) return; const r=s.getBoundingClientRect(), b=lb?lb.getBoundingClientRect():null, q=sl.getBoundingClientRect();
    __fr.push({ t:performance.now(), seg:[r.left,r.top,r.width,r.height], lens:b?[b.left,b.top,b.width,b.height]:null, lo:le?+getComputedStyle(le).opacity:0,
      th:[q.left,q.width], to:+getComputedStyle(sl).opacity });
    requestAnimationFrame(f); }; requestAnimationFrame(f); }"""

def touch(cdp, typ, x=None, y=None):
    cdp.send("Input.dispatchTouchEvent", {"type": typ, "touchPoints": [] if x is None else [{"x": x, "y": y}]})
def rgb_of(pix): return tuple(int(v) for v in pix[:3])
def chroma(c): return max(c) - min(c)
def parse_css_rgb(s):
    m = re.match(r"rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)", s or "")
    if m: return tuple(float(v) for v in m.groups())
    m = re.match(r"color\(srgb ([\d.]+) ([\d.]+) ([\d.]+)", s or "")
    if m: return tuple(float(v) * 255 for v in m.groups())
    m = re.match(r"#([0-9a-fA-F]{6})", s or "")
    if m: h = m.group(1); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    return None
def cx(b): return b[0] + b[2] / 2

def thumb_pixel(pg, st):
    """the thumb's colour off the screen: inside its round end, on its middle line (no text reaches there)"""
    t = st["thumb"]
    x, y = t[0] + min(8, t[3] / 3), t[1] + t[3] / 2
    png = pg.screenshot(clip={"x": x - 1, "y": y - 1, "width": 3, "height": 3})
    im = Image.open(io.BytesIO(png)).convert("RGB")
    return rgb_of(im.getpixel((im.width // 2, im.height // 2)))

def settle(pg, ms=1100): pg.wait_for_timeout(ms)
def frames(pg):
    pg.evaluate("()=>{ window.__on=false; }"); return pg.evaluate("()=>window.__fr || []")
def lit_index(st): return next((i for i, s in enumerate(st["segs"]) if s["lit"]), -1)

def centred(st, i):
    """the thumb's centre against segment i's label centre, both ways"""
    t, lab = st["thumb"], st["segs"][i]["label"]
    return abs(cx(t) - cx(lab)), abs((t[1] + t[3] / 2) - (lab[1] + lab[3] / 2))

def run_switcher(pg, cdp, tag, sw):
    name, js, sel, segSel, classes, swipes, track = sw
    pg.evaluate("()=>{ theme.accent='ink'; theme.reduceMotion=false; applyTheme(); }")
    pg.evaluate("()=>{" + js + "}"); settle(pg, 1500)
    st = pg.evaluate(STATE, [sel, segSel])
    if st and abs(st["scrollY"]) > 1: print("  (scrolled %s)" % st["scrollY"])
    if not st or len(st["segs"]) < 2:
        chk("%s: the switcher is on screen with 2+ segments" % tag, False, st); return
    labels = [s["text"] for s in st["segs"]]
    print("  %s: segments %s" % (tag, labels), flush=True)
    seg_rest = st["seg"]

    # 6. 44px targets
    hits = pg.evaluate("""([sel, segSel])=>{ const s=document.querySelector(sel);
      return [...s.querySelectorAll(':scope > '+segSel)].filter(b=>!b.hidden && b.offsetWidth>0).map(b=>{ const r=b.getBoundingClientRect(), x=r.left+r.width/2, y=r.top+r.height/2;
        const at=yy=>{ const e=document.elementFromPoint(x, yy); return !!(e && e.closest(segSel)===b); };
        return { w:r.width, up:at(y-21), down:at(y+21) }; }); }""", [sel, segSel])
    chk("%s: 6. every segment is a 44px target (hit 21px above and below its centre, 44+ wide)" % tag,
        all(h["up"] and h["down"] and h["w"] >= 44 for h in hits), hits)

    # 1. at rest
    pa = thumb_pixel(pg, st)
    # (a theme change can rebuild what is open - the chat sheet on an iPad - so the switcher is opened again under each theme)
    pg.evaluate("()=>{ theme.accent='vanguard'; applyTheme(); }"); settle(pg, 300)
    pg.evaluate("()=>{" + js + "}"); settle(pg, 1300)
    st_b = pg.evaluate(STATE, [sel, segSel]); pb = thumb_pixel(pg, st_b)
    acc = parse_css_rgb(st_b["accent"])
    pg.evaluate("()=>{ theme.accent='ink'; applyTheme(); }"); settle(pg, 300)
    pg.evaluate("()=>{" + js + "}"); settle(pg, 1300)
    st = pg.evaluate(STATE, [sel, segSel])
    far = acc is None or sum((pb[k] - acc[k]) ** 2 for k in range(3)) ** .5 > 60
    grey_same = st["greyBg"] is not None and parse_css_rgb(st["greyBg"]) is not None and parse_css_rgb(st["thumbBg"]) is not None and \
        max(abs(a - b) for a, b in zip(parse_css_rgb(st["greyBg"]), parse_css_rgb(st["thumbBg"]))) < 1.5
    rest_ok = chroma(pa) <= 4 and chroma(pb) <= 4 and max(abs(pa[k] - pb[k]) for k in range(3)) <= 2 and far \
        and st["thumbRadius"] >= st["thumb"][3] / 2 - .5 and grey_same
    chk("%s: 1. at rest the thumb is a neutral grey pill, the same under two themes, not the accent, and the lens's own grey" % tag, rest_ok,
        {"ink": pa, "vanguard": pb, "accent": acc, "radius": st["thumbRadius"], "h": st["thumb"][3], "thumbBg": st["thumbBg"], "lensGrey": st["greyBg"]})

    # 2. a tap on another segment
    i0 = lit_index(st); i1 = (i0 + 1) % len(st["segs"]) if i0 != len(st["segs"]) - 1 else i0 - 1
    if i0 < 0: chk("%s: a segment is lit" % tag, False, st); return
    pg.evaluate(SAMPLER, [sel])
    b1 = st["segs"][i1]["box"]
    touch(cdp, "touchStart", cx(b1), b1[1] + b1[3] / 2); pg.wait_for_timeout(60); touch(cdp, "touchEnd")
    settle(pg, 1200)
    fr = frames(pg); st2 = pg.evaluate(STATE, [sel, segSel])
    vis = [f for f in fr if f["lens"] and f["lo"] > .5 and f["lens"][2] > 1]
    track_h = lambda f: f["seg"][3] if track else st["thumb"][3] + 8
    taller = [f for f in vis if f["lens"][3] > track_h(f) + 4]
    poke = [f for f in vis if (f["lens"][1] < f["seg"][1] - 1 and f["lens"][1] + f["lens"][3] > f["seg"][1] + f["seg"][3] + 1) or not track]
    c0, c1 = cx(st["segs"][i0]["box"]), cx(b1); segw = b1[2]
    # in the switcher's own (unswollen) coordinates: the swell scales about the control's centre, so on its left half a lens
    # moving right is also carried left while the swell grows
    rc = cx(seg_rest)
    cs = [rc + (cx(f["lens"]) - cx(f["seg"])) * seg_rest[2] / f["seg"][2] for f in vis]
    glides = bool(cs) and abs(cs[0] - c0) < .35 * segw and any(abs(c - c1) < 3 for c in cs) and \
        all((cs[k + 1] - cs[k]) * (c1 - c0) >= -2.5 for k in range(len(cs) - 1) if abs(cs[k] - c1) > .12 * segw)
    swell = max((f["seg"][2] for f in fr), default=0) / seg_rest[2]
    dx, dy = centred(st2, i1)
    lit_now = lit_index(st2)
    chk("%s: 2a. a tap lifts the glass lens (%d frames up), taller than the track (%d frames) and out above and below it (%d)" % (tag, len(vis), len(taller), len(poke)),
        len(vis) >= 4 and len(taller) >= 2 and len(poke) >= 2, {"vis": len(vis), "maxH": max((f["lens"][3] for f in vis), default=0), "track": seg_rest[3]})
    chk("%s: 2b. the lens sets off over the lit segment and glides to the tapped one" % tag, glides, {"from": c0, "to": c1, "path": [round(c) for c in cs[::3]]})
    if track: chk("%s: 2c. the control swells while the lens is up (x%.3f)" % (tag, swell), swell >= 1.03, swell)
    # the hand-over: while the lens was up the thumb was not drawn (the lens IS it), and once the lens has gone the thumb is back
    hidden = [f for f in vis if f["to"] < .05]
    chk("%s: 2d. it lands: the thumb hidden under the lens (%d of %d frames), then the lens gone, the thumb back, centred under the new label (dx %.2f, dy %.2f)" % (tag, len(hidden), len(vis), dx, dy),
        len(vis) >= 4 and len(hidden) >= len(vis) - 1 and lit_now == i1 and st2["lensOp"] < .05 and st2["thumbOp"] > .95 and dx <= 1 and dy <= 1,
        {"lit": lit_now, "want": i1, "lensOp": st2["lensOp"], "thumbOp": st2["thumbOp"], "vis": len(vis), "hidden": len(hidden),
         "shown under the lens": [(round(f["t"] - fr[0]["t"]), round(f["lo"], 2), round(f["to"], 2)) for f in vis if f["to"] >= .05][:6]})

    # 3. a drag two-thirds of the way to the neighbour, then one a quarter of the way
    st = st2; i0 = lit_index(st); i1 = i0 + 1 if i0 + 1 < len(st["segs"]) else i0 - 1
    a0, a1 = st["segs"][i0]["box"], st["segs"][i1]["box"]
    y = a0[1] + a0[3] / 2; x0, x1 = cx(a0), cx(a1)
    pg.evaluate(SAMPLER, [sel])
    touch(cdp, "touchStart", x0, y); pg.wait_for_timeout(90)
    fx = []
    N = 16
    for k in range(1, N + 1):
        xx = x0 + (x1 - x0) * .66 * k / N
        touch(cdp, "touchMove", xx, y); fx.append((time.time(), xx)); pg.wait_for_timeout(28)
    pg.wait_for_timeout(120)
    # the finger has stopped two-thirds over: where is the lens, still held?
    xf = x0 + (x1 - x0) * .66
    lens_now = pg.evaluate("([sel])=>{ const s=document.querySelector(sel), le=s.querySelector(':scope > .seg-lens'); if(!le) return null; const b=le.querySelector('.tab-lens-body').getBoundingClientRect(); return [b.left+b.width/2, +getComputedStyle(le).opacity]; }", [sel])
    touch(cdp, "touchEnd"); settle(pg, 1200)
    fr = frames(pg); st3 = pg.evaluate(STATE, [sel, segSel])
    held = [f for f in fr if f["lens"] and f["lo"] > .5]
    near = [abs(lens_now[0] - xf)] if lens_now and lens_now[1] > .5 else [99]
    follows = len(held) >= 8 and min(near) <= 14
    dx, dy = centred(st3, i1)
    chk("%s: 3a. a drag carries the lens with the finger (within %.1fpx of it as the finger stops)" % (tag, min(near)), follows, {"held": len(held), "near": [round(v, 1) for v in near]})
    chk("%s: 3b. let go two-thirds over, it snaps to the nearest segment, picked, thumb centred under its label (dx %.2f, dy %.2f)" % (tag, dx, dy),
        lit_index(st3) == i1 and st3["thumbOp"] > .95 and dx <= 1 and dy <= 1 and st3["lensOp"] < .05, {"lit": lit_index(st3), "want": i1})
    st = st3; i0 = lit_index(st); i1 = i0 + 1 if i0 + 1 < len(st["segs"]) else i0 - 1
    a0, a1 = st["segs"][i0]["box"], st["segs"][i1]["box"]; x0, x1 = cx(a0), cx(a1)
    pg.evaluate(SAMPLER, [sel])
    touch(cdp, "touchStart", x0, y); pg.wait_for_timeout(90)
    for k in range(1, 9): touch(cdp, "touchMove", x0 + (x1 - x0) * .25 * k / 8, y); pg.wait_for_timeout(28)
    pg.wait_for_timeout(100); touch(cdp, "touchEnd"); settle(pg, 1200)
    fr = frames(pg); st4 = pg.evaluate(STATE, [sel, segSel])
    dx, dy = centred(st4, i0)
    up = [f for f in fr if f["lens"] and f["lo"] > .5]
    chk("%s: 3c. a drag a quarter of the way snaps back: the lens was up, nothing picked, thumb centred (dx %.2f)" % (tag, dx),
        len(up) >= 4 and lit_index(st4) == i0 and dx <= 1 and dy <= 1, {"lit": lit_index(st4), "want": i0, "up": len(up)})

    # 4. a swipe across the content
    if swipes:
        st = st4; i0 = lit_index(st); n = len(st["segs"])
        go_left = i0 + 1 < n            # a swipe to the left goes to the next segment
        want = i0 + 1 if go_left else i0 - 1
        vw = pg.evaluate("innerWidth"); yy = st["seg"][1] + st["seg"][3] + 230
        xa, xb = (vw * .75, vw * .25) if go_left else (vw * .25, vw * .75)
        pg.evaluate(SAMPLER, [sel])
        touch(cdp, "touchStart", xa, yy)
        for k in range(1, 11): touch(cdp, "touchMove", xa + (xb - xa) * k / 10, yy + k * .3); pg.wait_for_timeout(16)
        touch(cdp, "touchEnd"); settle(pg, 1300)
        fr = frames(pg); st5 = pg.evaluate(STATE, [sel, segSel])
        up = [f for f in fr if f["lens"] and f["lo"] > .5]
        moved = any(abs(f["th"][0] + f["th"][1] / 2 - cx(st["segs"][want]["box"])) < 2 for f in fr[-5:]) if fr else False
        dx, dy = centred(st5, want) if lit_index(st5) == want else (99, 99)
        chk("%s: 4. a swipe across the content moves the thumb to the next segment with the lens (%d frames up), centred (dx %.2f)" % (tag, len(up), dx),
            lit_index(st5) == want and len(up) >= 4 and dx <= 1 and dy <= 1 and moved, {"lit": lit_index(st5), "want": want, "up": len(up)})

    # 5. reduce motion
    pg.evaluate("()=>{ theme.reduceMotion=true; document.documentElement.dataset.reduceMotion='true'; }"); settle(pg, 300)
    st = pg.evaluate(STATE, [sel, segSel]); i0 = lit_index(st); i1 = i0 + 1 if i0 + 1 < len(st["segs"]) else i0 - 1
    b1 = st["segs"][i1]["box"]
    pg.evaluate(SAMPLER, [sel])
    touch(cdp, "touchStart", cx(b1), b1[1] + b1[3] / 2); pg.wait_for_timeout(60); touch(cdp, "touchEnd"); settle(pg, 900)
    fr = frames(pg); st6 = pg.evaluate(STATE, [sel, segSel])
    pg.evaluate("()=>{ theme.reduceMotion=false; document.documentElement.dataset.reduceMotion='false'; }")
    shown = [f for f in fr if f["lo"] > .02]
    grew = max((f["seg"][2] for f in fr), default=0) - st["seg"][2]
    dx, dy = centred(st6, i1) if lit_index(st6) == i1 else (99, 99)
    chk("%s: 5. reduce motion: the glass is there but never shown (%d frames), no swell (+%.1fpx), thumb centred under the new label (dx %.2f)" % (tag, len(shown), grew, dx),
        st6["lens"] and not shown and grew < .5 and dx <= 1 and dy <= 1, {"lens": st6["lens"], "shown": len(shown), "grew": grew})

def main():
    srv, url = g["serve"]()
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=g["CHROME"])
        for dev in DEVICES:
            for cls in CLASSES:
                ctx, pg, errs = open_page(br, dev, cls, url)
                cdp = ctx.new_cdp_session(pg)
                for sw in SWITCHERS:
                    if cls not in sw[4]: continue
                    if ONLY and not ONLY.search(sw[0]): continue
                    tag = "%s|%s|%s" % (dev[0], cls, sw[0])
                    try: run_switcher(pg, cdp, tag, sw)
                    except Exception as e: chk("%s: ran" % tag, False, str(e).splitlines()[0][:300])
                    try: pg.evaluate("()=>{ try{ if(chatDockOpen) closeChatDock(); }catch(e){} theme.reduceMotion=false; theme.accent='ink'; applyTheme(); }")
                    except Exception: pass
                chk("%s|%s: 7. no page errors" % (dev[0], cls), not errs, errs[:3])
                ctx.close()
        br.close()
    srv.shutdown()
    fails = [n for n, c in results if not c]
    print("\n%d checks, %d failed" % (len(results), len(fails)))
    # by kind, so a run --against the build before shows which kinds fail there
    kinds = {}
    for n, c in results:
        k = re.sub(r"^[^:]*: ", "", n).split(" ")[0]
        kinds.setdefault(k, [0, 0]); kinds[k][0 if c else 1] += 1
    print("by check: " + ", ".join("%s %d pass / %d fail" % (k, v[0], v[1]) for k, v in sorted(kinds.items())))
    sys.exit(0 if ok else 1)

main()
