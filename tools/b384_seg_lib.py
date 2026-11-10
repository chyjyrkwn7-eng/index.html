"""Shared harness for the top-switcher gates and recorders (384 r18): check-b384-segdelta.py, check-b384-toptabs.py and
record-b384-seg.py. Opens the app on a device class (a phone installed or in Safari, an iPad, a laptop, a desktop monitor at
dpr 1 and 2), opens each of the five switchers, and drives it by a real finger (CDP touch) or a real mouse.

  HTML = the build under test (`--against REV|FILE` = the build before: a new check must FAIL there)
  open_page(br, dev, cls, url)   -> ctx, page, errors
  SWITCHERS                      -> name, how to open it, selector, segment selector, classes, swipes, has a track
"""
import json, os, re, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
def arg(n, d=None): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d
AG = arg("--against")
if AG:
    HTML = open(AG, encoding="utf-8").read() if os.path.isfile(AG) else subprocess.check_output(["git", "-C", ROOT, "show", AG + ":index.html"]).decode("utf-8")
else:
    HTML = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
_src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(_src, g)

UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1"
UA_IPAD = "Mozilla/5.0 (iPad; CPU OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1"
UA_DESK = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Safari/605.1.15"
# name, w, h, dpr, insets, user agent, touch, installed
DEVICES = [
    dict(name="phone-installed", w=440, h=956, dpr=3, ins=(62, 0, 34, 0), ua=UA, touch=True, installed=True),
    dict(name="phone-safari", w=440, h=790, dpr=3, ins=(0, 0, 0, 0), ua=UA, touch=True, installed=False),
    dict(name="ipad-pro-11", w=834, h=1194, dpr=2, ins=(24, 0, 20, 0), ua=UA_IPAD, touch=True, installed=True),
    dict(name="laptop-mouse", w=1512, h=852, dpr=2, ins=(0, 0, 0, 0), ua=UA_DESK, touch=False, installed=False),
    dict(name="desktop-dpr1", w=2560, h=1300, dpr=1, ins=(0, 0, 0, 0), ua=UA_DESK, touch=False, installed=False),
    dict(name="desktop-dpr2", w=1920, h=1000, dpr=2, ins=(0, 0, 0, 0), ua=UA_DESK, touch=False, installed=False),
]
OWNER = "xph5b57jbp5a"
SEEN = ("['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card','class26e.getstarted',"
        "'class26e.ifc.intro.seen','class26e.ifc.unithold.tip','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted','class26e.ifc.freshstart'].forEach(k=>localStorage.setItem(k,'1'));"
        "localStorage.setItem('class26e.frame.ok','go-live-1'); ['55124','124256','256578'].forEach(k=>localStorage.setItem('class26e.penal'+k+'.seen','1'));")
INIT = "(()=>{ if(localStorage.getItem('class26e.drill.v1')) return; localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-3843'); " + SEEN + " %s })()"
IFC = ("localStorage.setItem('class26e.ifc.drill.v1', localStorage.getItem('class26e.drill.v1')); localStorage.setItem('class26e.ifc.synccode','TEST-3843');"
       "localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done'); localStorage.setItem('class26e.activeclass','ifc');")
REVIEW = ("showProfile('stats'); const run={missed:[0,1], order:[0,1,2,3], timedOutSet:{}, mode:'exam', vroom:true, attempts:{}, picked:{}, firstPick:{}};"
          "const p=document.createElement('section'); p.className='panel'; p.appendChild(buildRoomReviewTabs(run)); stage.replaceChildren(p); window.scrollTo({top:0, behavior:'instant'});")
# name, how to open it, the switcher's selector, its segments, the classes it exists in, whether a swipe across the content changes it
SWITCHERS = [
    ("profile", "showProfile('stats');", "#stage .screen-profile > .navsegment.profiletabs", ".iconbtn", ("academy", "ifc"), True),
    ("boards", "showRankings();", "#stage .screen-rankings > .navsegment.profiletabs", ".iconbtn", ("academy", "ifc"), True),
    # (the academy's levels 2 and 3 have no units yet, and a tap on one opens "coming" instead: the fixture gives them two each)
    ("levels", "if(!window.__lv2){ window.__lv2=1; const u0=unitsOfLevel; unitsOfLevel=(lv,all)=>{ const r=u0(lv,all); return r.length ? r : (all||[]).slice(0,2); }; } cfg.mode='drill'; cfg.units=[]; showSetup();", "#stage .setup-levels", ".iconbtn", ("academy",), False),
    ("chat", "showHome(); chatDockTab='friends'; openChatDock();", ".chatdock-seg, .chatdock-tabs:not(:has(.chatdock-seg))", ".chatdock-tab", ("academy", "ifc"), False),
    ("review", REVIEW, "#stage .rs-tabs", ".rs-tab", ("academy", "ifc"), False),
]

def body_for(ins):
    t, r, b, l = ins; v = {"top": f"{t}px", "right": f"{r}px", "bottom": f"{b}px", "left": f"{l}px"}
    return g["INSET_RE"].sub(lambda m: v[m.group(1)], HTML)

def open_page(br, dev, cls, url, cpu=1):
    kw = dict(viewport={"width": dev["w"], "height": dev["h"]}, device_scale_factor=dev["dpr"], user_agent=dev["ua"])
    if dev["touch"]: kw.update(has_touch=True, is_mobile=True)
    ctx = br.new_context(**kw)
    if dev["installed"]: ctx.add_init_script(g["STANDALONE"])
    ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]()))
    pg = ctx.new_page(); b = body_for(dev["ins"])
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
                "try{ playUnlockSpotlight=(it,n,of,release)=>{ try{ release && release(); }catch(e){} }; }catch(e){}"
                "document.querySelectorAll('#tour-overlay, #tour-tooltip, #nova-intro, .rs-spot, .unlock-card').forEach(n=>n.remove()); }")
    if cpu and cpu > 1:
        cdp = ctx.new_cdp_session(pg); cdp.send("Emulation.setCPUThrottlingRate", {"rate": cpu})
    return ctx, pg, errs

# the switcher's state: its box and look, each segment (its box and the ink of its text), the lit one, the thumb (and, in the build
# before r18, the lens)
STATE = """([sel, segSel])=>{ const s=[...document.querySelectorAll(sel)].find(e=>e.getBoundingClientRect().width>0); if(!s) return null; const r=s.getBoundingClientRect();
  const segs=[...s.querySelectorAll(':scope > '+segSel)].filter(b=>!b.hidden && b.offsetWidth>0).map(b=>{ const q=b.getBoundingClientRect();
    const rg=document.createRange(); const tw=document.createTreeWalker(b, NodeFilter.SHOW_TEXT); let L=1e9,R=-1e9,T=1e9,B=-1e9, n;
    while((n=tw.nextNode())){ if(!n.textContent.trim()) continue; if(n.parentElement.closest('[hidden]') || !n.parentElement.getClientRects().length) continue; rg.selectNodeContents(n); for(const x of (n.parentElement!==b ? [n.parentElement.getBoundingClientRect()] : rg.getClientRects())){ if(!x.width) continue; L=Math.min(L,x.left); R=Math.max(R,x.right); T=Math.min(T,x.top); B=Math.max(B,x.bottom); } }
    const bcs=getComputedStyle(b);
    return { box:[q.left,q.top,q.width,q.height], label:[L,T,R-L,B-T], text:b.textContent.trim(), op:+bcs.opacity, color:bcs.color, weight:bcs.fontWeight,
             lit: b.classList.contains('active')||b.classList.contains('is-on'), selected:b.getAttribute('aria-selected') }; });
  const sl=s.querySelector(':scope > .seg-slider'); const slr=sl?sl.getBoundingClientRect():null; const cs=sl?getComputedStyle(sl):null; const sc=getComputedStyle(s);
  const le=s.querySelector(':scope > .seg-lens');
  return { seg:[r.left,r.top,r.width,r.height], segLayout:[s.offsetWidth,s.offsetHeight], segs, thumb: slr&&[slr.left,slr.top,slr.width,slr.height],
    thumbLayout: sl&&[sl.offsetWidth, sl.offsetHeight], thumbOp: cs?+cs.opacity:0, thumbRadius: cs?parseFloat(cs.borderTopLeftRadius):0,
    thumbBg: cs?cs.backgroundColor:'', thumbTransition: cs?cs.transitionProperty:'', thumbTf: sl?sl.style.transform:'',
    trackBg: sc.backgroundColor, trackRadius: parseFloat(sc.borderTopLeftRadius), trackBorder: sc.borderTopColor, trackShadow: sc.boxShadow,
    trackBackdrop: sc.backdropFilter||sc.webkitBackdropFilter||'none', lens: !!le, lensOp: le?+getComputedStyle(le).opacity:0,
    scrollY: scrollY, dpr: devicePixelRatio }; }"""
# every frame: the track's box, the thumb's (and the lens's, in the build before), the thumb's layout properties
SAMPLER = """([sel])=>{ const s=[...document.querySelectorAll(sel)].find(e=>e.getBoundingClientRect().width>0); window.__fr=[]; window.__on=true;
  const sl=s.querySelector(':scope > .seg-slider'), le=s.querySelector(':scope > .seg-lens'), lb=le?le.querySelector('.tab-lens-body'):null;
  const f=()=>{ if(!window.__on) return; const r=s.getBoundingClientRect(), q=sl.getBoundingClientRect(), b=lb?lb.getBoundingClientRect():null; const lo=le?+getComputedStyle(le).opacity:0;
    __fr.push({ t:performance.now(), seg:[r.left,r.top,r.width,r.height], th:[q.left,q.top,q.width,q.height], to:+getComputedStyle(sl).opacity,
      lens: b&&lo>.5?[b.left,b.top,b.width,b.height]:null,
      lay:[sl.offsetWidth, sl.offsetHeight, sl.style.top, sl.style.height, sl.style.width, sl.style.left] });
    requestAnimationFrame(f); }; requestAnimationFrame(f); }"""

class Pointer:
    """a finger (CDP touch) or a mouse"""
    def __init__(self, pg, ctx, touch):
        self.pg = pg; self.touch = touch; self.cdp = ctx.new_cdp_session(pg) if touch else None
    def down(self, x, y):
        if self.touch: self.cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]})
        else: self.pg.mouse.move(x, y); self.pg.mouse.down()
    def move(self, x, y):
        if self.touch: self.cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x, "y": y}]})
        else: self.pg.mouse.move(x, y)
    def up(self):
        if self.touch: self.cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        else: self.pg.mouse.up()

def cx(b): return b[0] + b[2] / 2
def cy(b): return b[1] + b[3] / 2
def parse_css_rgb(s):
    m = re.match(r"rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)", s or "")
    if m: return tuple(float(v) for v in m.groups())
    m = re.match(r"color\(srgb ([\d.]+) ([\d.]+) ([\d.]+)", s or "")
    if m: return tuple(float(v) * 255 for v in m.groups())
    m = re.match(r"#([0-9a-fA-F]{6})", s or "")
    if m: h = m.group(1); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    return None
def luma(c): return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]
def lit_index(st): return next((i for i, s in enumerate(st["segs"]) if s["lit"]), -1)
def frames(pg):
    pg.evaluate("()=>{ window.__on=false; }"); return pg.evaluate("()=>window.__fr || []")
def open_switcher(pg, sw, ms=1500):
    pg.evaluate("()=>{ theme.accent='ink'; theme.reduceMotion=false; document.documentElement.dataset.reduceMotion='false'; applyTheme(); }")
    pg.evaluate("()=>{" + sw[1] + "}"); pg.wait_for_timeout(ms)
    return pg.evaluate(STATE, [sw[2], sw[3]])
def close_chat(pg):
    try: pg.evaluate("()=>{ try{ if(chatDockOpen) closeChatDock(); }catch(e){} theme.reduceMotion=false; document.documentElement.dataset.reduceMotion='false'; theme.accent='ink'; applyTheme(); }")
    except Exception: pass

def vis(f):
    """the thumb as drawn: the glass lens while it is up (the build before r18), else the thumb"""
    return f["lens"] if f.get("lens") else f["th"]

def analyse(fr, c1, rest_th, rest_seg):
    """one move's frames: where it starts, how long it takes, how far it overshoots c1, how its size and the track's change,
    how far it pokes out of the track, the frame times in the moving window, and whether any layout property of the thumb moved"""
    if not fr: return None
    cs = [cx(vis(f)) for f in fr]
    c0 = cs[0]; d = 1 if c1 >= c0 else -1
    mv = [i for i, c in enumerate(cs) if abs(c - c0) > .5]
    if not mv: return dict(moved=False)
    i0 = mv[0]
    last = max((i for i, c in enumerate(cs) if abs(c - c1) > 1), default=i0)
    i1 = min(len(fr) - 1, last + 1)
    over = max([0] + [(c - c1) * d for c in cs])
    back = max([0] + [-(cs[k + 1] - cs[k]) * d for k in range(len(cs) - 1) if abs(cs[k] - c1) > 3])   # a step backwards, away from the target
    size = max(max(vis(f)[2] / rest_th[2], vis(f)[3] / rest_th[3]) for f in fr) - 1
    swell = max(max(f["seg"][2] / rest_seg[2], f["seg"][3] / rest_seg[3]) for f in fr) - 1
    poke = max([0] + [max(f["seg"][0] - vis(f)[0], vis(f)[0] + vis(f)[2] - (f["seg"][0] + f["seg"][2]), f["seg"][1] - vis(f)[1], vis(f)[1] + vis(f)[3] - (f["seg"][1] + f["seg"][3])) for f in fr])
    win = [fr[k + 1]["t"] - fr[k]["t"] for k in range(max(0, i0 - 3), min(len(fr) - 1, i1 + 3))]
    lay = {json.dumps(f["lay"]) for f in fr}
    return dict(moved=True, start_ms=fr[i0]["t"] - fr[0]["t"], dur_ms=fr[i1]["t"] - fr[i0]["t"], overshoot=over, backstep=back, size=size, swell=swell,
                poke=poke, dt_mean=sum(win) / len(win) if win else 0, dt_max=max(win) if win else 0, dt_p95=sorted(win)[int(.95 * (len(win) - 1))] if win else 0,
                dropped=sum(1 for v in win if v > 25), layout_changes=len(lay) - 1, end_err=abs(cs[-1] - c1), frames=len(fr))
