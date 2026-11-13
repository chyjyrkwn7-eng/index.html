#!/usr/bin/env python3
"""Build 384.98: the new dot is a small lit flare in the person's theme colour.
Madison: "The yellow dot for the notification, doesn't match the theme, it should almost look a little like the secret flare.."

Every place the dot appears - the Profile tab, the class button, Profile's rows (Customize, the badge case, the rank), Customize's
character / banner / theme / hundo-effect tiles and the badge case's tiles - is found with everything new (seen-unlocks cleared,
a rank not yet shown, a class not yet looked at), on an iPhone 17 Pro Max (440x956 at 3x) and, for where it sits, an iPad Pro 11"
(834x1194 at 2x). Read off the page and off the pixels; no colour, label or size is typed into this file.

(1) WHERE IT SITS: every place has its dot, drawn (a non-zero box, visible, painted), and each dot's centre and size are where
    the reference build puts them (--ref; by default the commit this tree was cut from, its merge-base with origin/main),
    within 0.75px - the look changed, the place did not - and on its host's corner on the 45-degree line.
(2) WHAT IT LOOKS LIKE, on the default theme, a warm one (Bronze), the grey one (Silver), a cool one (Sapphire) and the red one
    (Supernova), read off the screenshot:
    a. a white-hot core: the brightest pixel near its middle is near white, and brighter than its rim;
    b. its colour is the theme's (the colour between core and rim, against --rank-accent / --theme-c2 read off <html>): the same
       hue family (within 15 degrees) for a coloured theme; for a theme whose colour is the chat's unread red (read off the chat's own count), its
       warm side (between that red and the theme's --theme-c1), never the red; for a grey theme, grey - and lit (below);
    c. never red: no dot's colour is within 14 degrees of the chat's unread count;
    d. one look everywhere: on a theme, every place's dot is the same colour;
    e. it follows the theme: no two themes' dots are the same colour;
    f. it is lit on the tab bar's glass: its colour has 3:1 against the glass, and a halo of its own (a layer that, hidden, takes
       light away from the ring of glass round it), in the theme's hue; a grey theme's light is no weaker than a coloured one's.
(3) HOW IT MOVES: with motion on, every dot's halo breathes (a running animation on a layer of the dot), and every animation on
    any dot layer is transform/opacity only; with Reduce motion on (data-reduce-motion) and with prefers-reduced-motion, none runs.
(4) no page errors.

  python3 tools/check-b384-newdot.py [--against REV] [--ref REV]
--against REV checks REV's index.html instead of the working tree (it FAILS on 384.92, where the dot is a fixed yellow).
"""
import colorsys, io, json, os, re, subprocess, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
from playwright.sync_api import sync_playwright
srv, url = g["serve"]()
args = sys.argv[1:]
def opt(name, default=None):
    if name in args:
        i = args.index(name); v = args[i + 1]; del args[i:i + 2]; return v
    return default
AGAINST = opt("--against")
# where the dot sat before: the build this tree was cut from (its merge-base with origin/main), unless --ref names another
REF = opt("--ref") or subprocess.check_output(["git", "-C", ROOT, "merge-base", "HEAD", "origin/main"]).decode().strip()
def git_src(rev): return subprocess.check_output(["git", "-C", ROOT, "show", rev + ":index.html"]).decode("utf-8")
TEST = git_src(AGAINST) if AGAINST else io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
REFSRC = git_src(REF)
def build_of(s):
    m = re.search(r'const APP_BUILD = "([^"]+)"', s); return m.group(1) if m else "?"
print("checking", build_of(TEST), "(" + (AGAINST or "working tree") + ")", " positions against", build_of(REFSRC), "(" + REF + ")", flush=True)
ok = True; ALLERRS = []
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond)
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  -> " + str(info)[:900]), flush=True)

UA_IPHONE = "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
UA_IPAD = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Safari/605.1.15"
DEV = {"phone": (440, 956, 3, (62, 0, 34, 0), UA_IPHONE), "ipad": (834, 1194, 2, (24, 0, 20, 0), UA_IPAD)}
INIT = """(()=>{ if(localStorage.getItem('class26e.drill.v1')) return;
 localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-3895');
 ['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card','class26e.getstarted'].forEach(k=>localStorage.setItem(k,'1'));
 localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.penal256578.seen','1'); })()"""
def seed():
    d = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]())); d["publicId"] = "pubtest0384nd"; d["firstName"] = "Casey"; d["novaMet"] = 99
    return d

def boot(br, source, dev):
    w, h, dsf, ins, ua = DEV[dev]
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=dsf, has_touch=True, is_mobile=(dev == "phone"), user_agent=ua)
    ctx.add_init_script(g["STANDALONE"])
    if dev == "ipad": ctx.add_init_script("Object.defineProperty(navigator,'maxTouchPoints',{get:()=>5,configurable:true});")
    ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]()))
    pg = ctx.new_page()
    t, r, b, l = ins; v = {"top": f"{t}px", "right": f"{r}px", "bottom": f"{b}px", "left": f"{l}px"}
    body = g["INSET_RE"].sub(lambda m: v[m.group(1)], source)
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.route("**/version.json*", lambda route, request, b=build_of(source): route.fulfill(status=200, headers={"content-type": "application/json"},
             body=json.dumps({"build": b, "note": "", "frameId": "", "force": False, "safariSound": True})))
    pg.add_init_script(INIT % json.dumps(json.dumps(seed())))
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.goto(url); pg.wait_for_timeout(3500)
    pg.evaluate("document.getElementById('splashscreen')?.remove()")
    pg.evaluate("""()=>{ homeUnlocksOwed=()=>false; try{ scheduleWeekRecap=()=>{}; maybeShowWeekRecap=()=>{}; }catch(e){}
      store.seenUnlocks={chars:[],banners:[],themes:[],badges:[],fx:[],v:2}; store.rankMapSeen=-1; store.rankMapFx244=true; }""")
    pg.errs = errs; pg.dsf = dsf
    return ctx, pg

def clear(pg):
    pg.evaluate("()=>{ [...document.querySelectorAll('button')].filter(b=>/^(Got it|Not now|Skip)$/.test(b.textContent.trim()) && b.offsetParent).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card,#tour-tooltip,#tour-overlay,.daily-alert').forEach(n=>n.remove()); }")

SCREENS = [
    ("home", "()=>{ newClassPulseOn = true; showHome(); }"),
    ("profile", "()=>{ showProfile('profile'); window.scrollTo(0,0); }"),
    ("character", "()=>{ showCustomize('character'); window.scrollTo(0,0); }"),
    ("banner", "()=>{ showCustomize('banner'); window.scrollTo(0,0); }"),
    ("theme", "()=>{ showCustomize('theme'); window.scrollTo(0,0); }"),
    ("fx", "()=>{ showCustomize('fx'); window.scrollTo(0,0); }"),
    ("badges", "()=>{ showRanksScreen('badges'); }"),
]
def visit(pg, name, js):
    pg.evaluate(js); pg.wait_for_timeout(2300 if name == "home" else 1900)
    if name == "badges":
        pg.evaluate("()=>{ try{ finishBadgeCaseOpen(document.querySelector('.badges-tab .ncase')); }catch(e){} window.scrollTo(0,0); }"); pg.wait_for_timeout(900)
    pg.evaluate("()=>{ try{ syncProfileTabDot(); }catch(e){} }"); pg.wait_for_timeout(250)
    clear(pg); pg.wait_for_timeout(150)

# Every dot on the screen, whichever way a build draws it: a .new-dot element (its body is its ::after when it has one, else
# itself), the Profile tab icon's ::after, the class button's ::after (384.92) or its .new-dot child (384.98).
DOTS = r"""(screen)=>{ const out=[]; const px=v=>parseFloat(v)||0; const seen={};
  const keyOf=h=>{ let k=h.id?('#'+h.id):(((typeof h.className==='string')?h.className:((h.className&&h.className.baseVal)||'')).trim().split(/\s+/)[0]||h.tagName.toLowerCase());
    seen[k]=(seen[k]||0)+1; return screen+':'+k+'#'+seen[k]; };
  const shown=el=>{ for(let e=el; e && e!==document.documentElement; e=e.parentElement){ const c=getComputedStyle(e); if(c.display==='none'||c.visibility==='hidden'||+c.opacity===0) return false; } return true; };
  const pbox=(host, pe)=>{ const cs=getComputedStyle(host, pe); if(cs.content==='none'||cs.content==='normal'||cs.display==='none') return null;
    const hb=host.getBoundingClientRect(); const w=px(cs.width), h=px(cs.height);
    const l=cs.left!=='auto'?px(cs.left):host.clientWidth-px(cs.right)-w, t=cs.top!=='auto'?px(cs.top):host.clientHeight-px(cs.bottom)-h;
    return { x:hb.left+host.clientLeft+l, y:hb.top+host.clientTop+t, w, h, vis:cs.visibility!=='hidden' && +cs.opacity>0 }; };
  /* a dot in the tab bar's shade (the bar's own shadow and glass reach ~20px round it) is there, but not what is measured for colour */
  const bar=document.querySelector('.bottomtabs'); const bb=bar && shown(bar) ? bar.getBoundingClientRect() : null;
  const rec=(host, body, halo, kind)=>{ const hb=host.getBoundingClientRect(); if(!hb.width || hb.bottom<0 || hb.top>innerHeight) return;
    if(!body || !body.w) return;
    const cx=body.x+body.w/2, cy=body.y+body.h/2;
    const shaded=(kind!=='tab' && !!bb && cx>bb.left-20 && cx<bb.right+20 && cy>bb.top-20 && cy<bb.bottom+20)
      || body.x<0 || body.y<0 || body.x+body.w>innerWidth || body.y+body.h>innerHeight;   /* or not wholly on the screen */
    out.push({ key:keyOf(host), kind, cx, cy, w:body.w, h:body.h, vis:body.vis, shaded, halo:halo?{w:halo.w, h:halo.h, x:halo.x+halo.w/2, y:halo.y+halo.h/2}:null,
      hx:hb.left, hy:hb.top, hw:hb.width, hh:hb.height, dx:hb.right-cx, dy:cy-hb.top }); };
  document.querySelectorAll('.new-dot').forEach(d=>{ if(!shown(d)) return; let host=d.parentElement;
    if(host.classList.contains('new-dot-anchor') && host.firstElementChild!==d) host=host.firstElementChild;
    const b=d.getBoundingClientRect(); const a=pbox(d,'::after'); const body=a||{x:b.left, y:b.top, w:b.width, h:b.height, vis:true};
    rec(host, body, pbox(d,'::before'), a?'el+after':'el'); });
  document.querySelectorAll('#bottomtab-profile.has-new .bottomtab-icon').forEach(i=>{ if(!shown(i)) return; rec(i, pbox(i,'::after'), pbox(i,'::before'), 'tab'); });
  document.querySelectorAll('.class-bubble-wrap.has-new .class-bubble').forEach(i=>{ if(!shown(i) || i.querySelector(':scope > .new-dot')) return;
    const a=pbox(i,'::after'); if(a) rec(i, a, null, 'pseudo'); });
  return out; }"""
ANIMS = r"""()=>{ const out=[];
  document.getAnimations().forEach(a=>{ const e=a.effect; const t=e&&e.target; if(!t||!t.classList) return; const pe=e.pseudoElement||'';
    const dot=t.classList.contains('new-dot') || (pe && t.classList.contains('bottomtab-icon') && t.closest('#bottomtab-profile.has-new')) || (pe==='::after' && t.classList.contains('class-bubble'));
    if(!dot) return; const props=new Set();
    (e.getKeyframes()||[]).forEach(k=>Object.keys(k).forEach(p=>{ if(['offset','computedOffset','easing','composite'].indexOf(p)<0) props.add(p); }));
    out.push({ t:(t.className||'').toString().slice(0,30), pe, name:a.animationName||'', state:a.playState, props:[...props] }); });
  return out; }"""
THEME = r"""()=>{ const cs=getComputedStyle(document.documentElement); const g=n=>cs.getPropertyValue(n).trim();
  const cd=document.getElementById('chatdock-dot')||document.querySelector('.chatdock-tabcount');
  return { accent: document.documentElement.dataset.accent||'(default)', colour: g('--rank-accent')||g('--theme-c2'), c1: g('--theme-c1'),
           red: cd?getComputedStyle(cd).backgroundColor:null }; }"""
GLASS = r"""()=>{ const t=document.getElementById('bottomtab-profile'), i=t&&t.querySelector('.bottomtab-icon'); if(!t||!i) return null;
  const tb=t.getBoundingClientRect(), ib=i.getBoundingClientRect(); return [tb.right, ib.top+ib.height/2]; }"""
HIDE_HALO = "html body .new-dot::before, html body #bottomtab-profile.has-new .bottomtab-icon::before{ visibility:hidden !important; }"

def parse_colour(s):
    s = (s or "").strip()
    m = re.match(r"#([0-9a-fA-F]{6})$", s)
    if m: return tuple(int(m.group(1)[i:i + 2], 16) for i in (0, 2, 4))
    m = re.match(r"#([0-9a-fA-F]{3})$", s)
    if m: return tuple(int(c * 2, 16) for c in m.group(1))
    m = re.match(r"rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)", s)
    if m: return tuple(float(m.group(i)) for i in (1, 2, 3))
    return None
def lin(c):
    c = np.asarray(c, dtype=float) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def lum(rgb):
    l = lin(rgb); y = 0.2126 * l[..., 0] + 0.7152 * l[..., 1] + 0.0722 * l[..., 2]
    return float(y) if np.ndim(y) == 0 else y
def contrast(a, b): la, lb = lum(a), lum(b); return (max(la, lb) + .05) / (min(la, lb) + .05)
def hsv(rgb): h, s, v = colorsys.rgb_to_hsv(*[float(x) / 255 for x in rgb]); return h * 360, s, v
def hdist(a, b): d = abs(a - b) % 360; return min(d, 360 - d)
def shot(pg):
    p = "/dev/shm/nd-%d.png" % os.getpid(); pg.screenshot(path=p)
    return np.asarray(Image.open(p).convert("RGB")).astype(float)
def rings(img, d, dsf, r0, r1, half=None):
    """pixels whose distance from the dot's centre is in [r0, r1] CSS px (half: 'out' = the up-right half only)"""
    cx, cy = d["cx"] * dsf, d["cy"] * dsf; R = int(r1 * dsf) + 2
    x0, y0 = max(0, int(cx) - R), max(0, int(cy) - R)
    sub = img[y0:int(cy) + R + 1, x0:int(cx) + R + 1]
    yy, xx = np.mgrid[y0:y0 + sub.shape[0], x0:x0 + sub.shape[1]]
    dist = np.hypot(xx + .5 - cx, yy + .5 - cy) / dsf
    m = (dist >= r0) & (dist <= r1)
    if half == "out": m &= (xx + .5 - cx > 0) & (yy + .5 - cy < 0)
    return sub[m]
def paint(img, d, dsf):
    r = d["w"] / 2
    core = rings(img, d, dsf, 0, r * .42); rim = rings(img, d, dsf, r * .74, r * .9); mid = rings(img, d, dsf, r * .3, r * .66)
    cl = lum(core); i = int(np.argmax(cl))
    return {"core": tuple(core[i]), "coreL": float(cl[i]), "rimL": float(np.mean(lum(rim))), "colour": tuple(np.mean(mid, axis=0)), "rim": tuple(np.mean(rim, axis=0))}

with sync_playwright() as p:
    br = p.chromium.launch(executable_path=g["CHROME"], args=["--no-sandbox"])
    # ---------------------------------------------------------------- (1) where it sits, against the reference build
    POS = {}
    for dev in ("phone", "ipad"):
        for which, source in (("ref", REFSRC), ("test", TEST)):
            ctx, pg = boot(br, source, dev)
            pg.evaluate("()=>{ theme.accent='ink'; theme.reduceMotion=true; applyTheme(); }")
            got = []
            for name, js in SCREENS:
                visit(pg, name, js); got += pg.evaluate(DOTS, name)
            POS[(dev, which)] = {d["key"]: d for d in got}
            if which == "test": ALLERRS.extend(pg.errs)
            ctx.close()
        ref, test = POS[(dev, "ref")], POS[(dev, "test")]
        places = lambda D: sorted(set(re.sub(r"#\d+$", "", k) for k in D))
        need = {"home:#bottomtab-profile", "home:class-bubble", "profile:settings-row-icon", "character:avatarchar-option", "banner:banner-opt",
                "theme:swatch", "fx:hfx-opt", "badges:badge-tile-art"}
        found = set(re.sub(r"#\d+$", "", k).replace("bottomtab-icon", "#bottomtab-profile") for k in test)
        chk("(1) %s: a dot in every place (%d dots: %s)" % (dev, len(test), places(test)), need <= found and set(ref) == set(test),
            {"missing": sorted(need - found), "only on ref": sorted(set(ref) - set(test)), "only here": sorted(set(test) - set(ref))})
        bad = [(k, d["w"], d["h"], d["vis"]) for k, d in test.items() if not (d["w"] >= 6 and d["h"] >= 6 and d["vis"])]
        chk("(1) %s: every dot drawn (a box, visible)" % dev, not bad, bad[:5])
        moved = [(k, round(test[k]["cx"] - ref[k]["cx"], 2), round(test[k]["cy"] - ref[k]["cy"], 2), (ref[k]["w"], test[k]["w"])) for k in test if k in ref
                 and (abs(test[k]["cx"] - ref[k]["cx"]) > .75 or abs(test[k]["cy"] - ref[k]["cy"]) > .75 or abs(test[k]["w"] - ref[k]["w"]) > .5 or abs(test[k]["h"] - ref[k]["h"]) > .5)]
        chk("(1) %s: every dot's centre and size where %s has them (within 0.75px; %d compared)" % (dev, build_of(REFSRC), len([k for k in test if k in ref])), not moved, moved[:6])
        bad = [(k, round(d["dx"], 1), round(d["dy"], 1)) for k, d in test.items() if abs(d["dx"] - d["dy"]) > 1.5 or d["dx"] < -1 or d["dx"] > min(d["hw"], d["hh"]) / 3]
        chk("(1) %s: each on its host's corner, on the 45-degree line" % dev, not bad, bad[:6])

    # ---------------------------------------------------------------- (2) what it looks like, theme by theme
    THEMES = [("ink", "the default"), ("rookie", "warm (Bronze)"), ("ranger", "grey (Silver)"), ("adept", "cool (Sapphire)"), ("titan", "red (Supernova)")]
    ctx, pg = boot(br, TEST, "phone"); dsf = pg.dsf
    R = {}
    for acc, label in THEMES:
        pg.evaluate("(a)=>{ theme.accent=a; theme.reduceMotion=true; applyTheme(); }", acc)
        info = pg.evaluate(THEME); dots = []; halo = None
        for name, js in SCREENS:
            visit(pg, name, js)
            ds = pg.evaluate(DOTS, name); img = shot(pg)
            ds = [d for d in ds if not d["shaded"]]
            for d in ds: d.update(paint(img, d, dsf))
            dots += ds
            if name == "home":
                tab = next((d for d in ds if d["kind"] == "tab"), None)
                gl = pg.evaluate(GLASS)
                glass = tuple(np.mean(rings(img, {"cx": gl[0], "cy": gl[1]}, dsf, 0, 2.5), axis=0)) if gl else None
                if tab:
                    rr = tab["w"] / 2 + 2
                    lit = rings(img, tab, dsf, rr + .5, rr + 3.5, "out")
                    pg.evaluate("(css)=>{ const s=document.createElement('style'); s.id='__nd-hide-halo'; s.textContent=css; document.body.appendChild(s); }", HIDE_HALO)
                    pg.wait_for_timeout(200)
                    img2 = shot(pg)
                    pg.evaluate("()=>document.getElementById('__nd-hide-halo')?.remove()"); pg.wait_for_timeout(100)
                    dark = rings(img2, tab, dsf, rr + .5, rr + 3.5, "out")
                    diff = np.mean(lit, axis=0) - np.mean(dark, axis=0)
                    halo = {"lift": float(np.mean(lum(lit)) - np.mean(lum(dark))), "add": tuple(diff), "glass": glass}
        R[acc] = {"label": label, "info": info, "dots": dots, "halo": halo}
    red =parse_colour(R["ink"]["info"]["red"]); red_h = hsv(red)[0] if red else 0.0
    print("  the chat's unread count:", R["ink"]["info"]["red"], "hue %.0f" % red_h)
    means = {}
    for acc, label in THEMES:
        r = R[acc]; dots = r["dots"]; tc = parse_colour(r["info"]["colour"]); th, ts, _ = hsv(tc)
        col = tuple(np.mean([d["colour"] for d in dots], axis=0)) if dots else (0, 0, 0); means[acc] = col
        ch, cs_, _ = hsv(col)
        print("  %-16s theme %s (hue %.0f, sat %.2f) -> dot colour rgb(%d,%d,%d) hue %.0f sat %.2f; core L %.2f, rim L %.2f; halo %s" % (
            label, r["info"]["colour"], th, ts, col[0], col[1], col[2], ch, cs_, np.mean([d["coreL"] for d in dots] or [0]), np.mean([d["rimL"] for d in dots] or [0]),
            {k: (round(v, 3) if isinstance(v, float) else [round(x) for x in v] if v else v) for k, v in (r["halo"] or {}).items()}), flush=True)
        bad = [(d["key"], round(d["coreL"], 2), round(d["rimL"], 2)) for d in dots if not (d["coreL"] >= .8 and (d["coreL"] + .05) / (d["rimL"] + .05) >= 1.5)]
        chk("(2a) %s: every dot has a white-hot core, brighter than its rim (1.5:1 at least; %d dots, rim L %.2f-%.2f)" % (
            label, len(dots), min([d["rimL"] for d in dots] or [0]), max([d["rimL"] for d in dots] or [0])), dots and not bad, bad[:5])
        if ts < .25:
            want = "grey, as the theme is"; good = cs_ < .25
        elif hdist(th, red_h) <= 14:
            c1h = hsv(parse_colour(r["info"]["c1"]))[0]; want = "its warm side, %.0f-%.0f degrees" % (red_h + 14, c1h + 10)
            good = hdist(ch, red_h) > 14 and red_h + 14 <= (ch if ch < 180 else ch - 360) <= c1h + 10
        else:
            want = "the theme's hue %.0f, within 15 degrees" % th; good = hdist(ch, th) <= 15
        chk("(2b) %s: its colour is the theme's - %s (it is hue %.0f, sat %.2f)" % (label, want, ch, cs_), dots and good, col)
        bad = [(d["key"], round(hsv(d["colour"])[0])) for d in dots if hsv(d["colour"])[1] >= .25 and hdist(hsv(d["colour"])[0], red_h) <= 14]
        chk("(2c) %s: never red (no dot within 14 degrees of the chat's count)" % label, not bad, bad[:5])
        spread = max([float(np.linalg.norm(np.subtract(d["colour"], col))) for d in dots] or [999])
        chk("(2d) %s: one look everywhere (every place's dot within %.0f of the same colour)" % (label, spread), spread <= 22,
            [(d["key"], [round(x) for x in d["colour"]]) for d in dots if np.linalg.norm(np.subtract(d["colour"], col)) > 22][:5])
        h = r["halo"]
        if h and h["glass"]:
            cr = contrast(col, h["glass"]); ah, as_, _ = hsv(tuple(max(0, x) * 4 for x in h["add"]))
            halo_ok = h["lift"] > .015 and (as_ < .25 if ts < .25 else hdist(ah, ch) <= 30)
            chk("(2f) %s: lit on the tab bar's glass - %.1f:1 against it; a halo of its own lifting the glass round it by %.3f, hue %.0f" % (label, cr, h["lift"], ah),
                cr >= 3 and halo_ok, h)
        else:
            chk("(2f) %s: the Profile tab's dot measured" % label, False, h)
    # "the same colour" = no further apart than one theme's own dots are from place to place (the noise of the measure)
    names = [a for a, _ in THEMES]
    noise = max([max([float(np.linalg.norm(np.subtract(d["colour"], means[a]))) for d in R[a]["dots"]] or [0]) for a in names] + [6.0])
    close = [(a, b, round(float(np.linalg.norm(np.subtract(means[a], means[b]))))) for i, a in enumerate(names) for b in names[i + 1:]
             if np.linalg.norm(np.subtract(means[a], means[b])) <= noise]
    nearest = min(float(np.linalg.norm(np.subtract(means[a], means[b]))) for i, a in enumerate(names) for b in names[i + 1:])
    chk("(2e) it follows the theme: no two themes' dots the same colour (the nearest two %.0f apart; one theme's own dots vary by up to %.0f)" % (nearest, noise), not close, close)
    lifts = [R[a]["halo"]["lift"] for a, _ in THEMES if R[a]["halo"] and hsv(parse_colour(R[a]["info"]["colour"]))[1] >= .25]
    for a, label in THEMES:
        if R[a]["halo"] and hsv(parse_colour(R[a]["info"]["colour"]))[1] < .25:
            med = float(np.median(lifts)) if lifts else 0
            chk("(2f) %s: a grey theme's light is no weaker than a coloured one's (lift %.3f, the coloured themes' median %.3f)" % (label, R[a]["halo"]["lift"], med),
                R[a]["halo"]["lift"] >= med * .9 and R[a]["halo"]["lift"] > .015, R[a]["halo"])

    # ---------------------------------------------------------------- (3) how it moves
    pg.evaluate("()=>{ theme.accent='adept'; theme.reduceMotion=false; applyTheme(); }")
    for name, js in (SCREENS[0], SCREENS[1], SCREENS[2]):
        visit(pg, name, js)
        ds = pg.evaluate(DOTS, name); an = pg.evaluate(ANIMS)
        running = [a for a in an if a["state"] == "running"]
        chk("(3) %s, motion on: every dot breathes (%d dots, %d running animations on their layers: %s)" % (name, len(ds), len(running), sorted(set(a["name"] + a["pe"] for a in running))),
            ds and len(running) >= len(ds), an[:6])
        bad = [a for a in an if not set(a["props"]) <= {"transform", "opacity"}]
        chk("(3) %s: every dot animation is transform/opacity only" % name, not bad, bad[:4])
    pg.evaluate("()=>{ theme.reduceMotion=true; applyTheme(); }"); pg.wait_for_timeout(300)
    for name, js in (SCREENS[0], SCREENS[2]):
        visit(pg, name, js); an = [a for a in pg.evaluate(ANIMS) if a["state"] == "running"]
        chk("(3) %s, Reduce motion on: nothing on a dot runs" % name, not an, an[:4])
    pg.evaluate("()=>{ theme.reduceMotion=false; applyTheme(); }"); pg.emulate_media(reduced_motion="reduce"); pg.wait_for_timeout(300)
    for name, js in (SCREENS[0], SCREENS[2]):
        visit(pg, name, js); an = [a for a in pg.evaluate(ANIMS) if a["state"] == "running"]
        chk("(3) %s, prefers-reduced-motion: nothing on a dot runs" % name, not an, an[:4])
    ALLERRS.extend(pg.errs); ctx.close(); br.close()
chk("(4) no page errors", not ALLERRS, ALLERRS[:4])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
