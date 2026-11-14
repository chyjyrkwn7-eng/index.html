#!/usr/bin/env python3
"""Build 384.117: with Reduce motion on, nothing the app means to show is left invisible.

Madison's class reported (found by a helper on the live 384.107): with Settings > Motion & Effects > Reduce motion ON, the two
class cards on "Select your classes" and on "Classes" never appear. The global rule `[data-reduce-motion="true"] *{animation:none
!important}` also removes the fill that carried `.class-card` from its resting `opacity:0` to 1 (cc-in, `forwards`), so the page
was a title over an empty space. Every gate read styles, not what is on the glass, so all of them passed.

What this measures is what is on the glass: computed opacity (multiplied up the tree), visibility and the box.

  A  SCREENS, in-app switch. Every screen the sweep mounts (minus the ones that take their own run, or that loop by timer, which
     a still comparison cannot read) is mounted twice, motion normal and given time to finish, and with the in-app switch on. An
     element whose effective opacity is at least .9 and that is visible in the first and below .5 in the second is a failure.
     Both samples (two, .8s apart) must agree, so a timer's on/off cannot fake one. Plus the pickers themselves, by what they ARE
     (`#stage .class-card`, the Select your classes step and the Classes screen, phone and iPad): at least two, each computed
     opacity exactly 1, visibility visible, a box inside the screen.
  B  SCREENS, the OS setting (prefers-reduced-motion: reduce, the in-app switch off): the same comparison. (The app does not mirror
     the OS setting into the switch; its motion is mostly inside `prefers-reduced-motion:no-preference`, so the resting state and
     the animation go together. This keeps it that way.)
  C  RULES. Every rule in the stylesheet that sets an animation (about 1,700 selectors) gets an element built to match it, its
     animations are finished, and it is read three ways: motion normal, the in-app switch, the OS setting. Whatever ends VISIBLE with
     motion on must not end hidden with it off, so a screen nobody has mounted here (a pop-up, a copy tick, the splash, the tour) is
     covered the day its rule is written (and an element its animation brings home from 20px away or from under half size must
     not rest there: the tour's XP bar sat at 8%). Rules that are hidden by design are listed in ALLOWED with the reason; a new one that is
     not listed fails.
  D  THE SPLASH, booted with Reduce motion saved: its word is on the glass once the switch is applied (before 384.117 it was
     faded in by the animation and then dropped out of sight when the switch took the animation away).

    python3 tools/check-b384-reducemotion.py [A] [B] [C] [D] [--against REV|DIR] [--shots DIR]
  --against origin/main must FAIL A, C and D.   --shots DIR saves the two class pickers, motion normal and Reduce motion, at
  440x956 and 834x1194 (name-WxH-normal.png / name-WxH-reduce.png).
"""
import importlib.util, json, os, re, subprocess, sys, tempfile, time
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
spec = importlib.util.spec_from_file_location("sweep", os.path.join(HERE, "sweep-layout.py"))
S = importlib.util.module_from_spec(spec); spec.loader.exec_module(S)
from playwright.sync_api import sync_playwright

args = sys.argv[1:]
SHOTS = None
if "--shots" in args:
    i = args.index("--shots"); SHOTS = args[i + 1]; del args[i:i + 2]; os.makedirs(SHOTS, exist_ok=True)
ROOT = REPO
if "--against" in args:
    i = args.index("--against"); target = args[i + 1]; del args[i:i + 2]
    if os.path.isdir(target):
        ROOT = os.path.abspath(target)
    else:
        ROOT = tempfile.mkdtemp(prefix="rm384-")
        tar = subprocess.run(["git", "-C", REPO, "archive", "--format=tar", target, "index.html", "ifc", "launch", "version.json", "share"],
                             check=True, capture_output=True).stdout
        subprocess.run(["tar", "-x", "-C", ROOT], input=tar, check=True)
S.ROOT = ROOT                      # S.serve() serves S.ROOT
SECTIONS = args or ["A", "B", "C", "D"]
BUILD = re.search(r'const APP_BUILD = "([^"]+)"', open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()).group(1)
print("build", BUILD, "from", ROOT, flush=True)

ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond)
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  -> " + str(info)[:400]), flush=True)

SEED_REDUCE = S.SEED.replace("layout:'modern'}", "layout:'modern',reduceMotion:true}")
assert SEED_REDUCE != S.SEED, "the fixture's theme line changed: put reduceMotion:true on it"
# screens with a run of their own (they switch Reduce motion on themselves) or a timer loop (a still comparison reads its phase)
SKIP = ("__sweep", "showCustomize('banner')", "showHomeScreenSheet", "view:'video'")
SCREENS = [s for s in S.SCREENS if not any(k in s for k in SKIP)] + ["showClassCatalog"]
LOAD_MS = 180000

SNAP = r"""()=>{
 const out = {};
 const eff = el => { let o = 1; for(let e = el; e && e.nodeType === 1; e = e.parentElement){ const cs = getComputedStyle(e); o *= parseFloat(cs.opacity); if(cs.visibility === 'hidden') return 0; if(cs.display === 'none') return -1; } return o; };
 const walk = (el, path) => { let i = 0; for(const c of el.children){ const t = c.tagName;
   if(/^(SCRIPT|STYLE|LINK|META|TITLE|NOSCRIPT)$/.test(t) || (c.namespaceURI !== 'http://www.w3.org/1999/xhtml' && t !== 'svg')){ i++; continue; }
   const k = path + '/' + t.toLowerCase() + i; const r = c.getBoundingClientRect();
   out[k] = { o: eff(c), w: r.width, h: r.height, cls: String(c.className && c.className.baseVal !== undefined ? c.className.baseVal : c.className).slice(0, 60), id: c.id };
   if(t !== 'svg' && t !== 'CANVAS') walk(c, k); i++; } };
 walk(document.body, ''); return out; }"""

def new_page(br, seed, w=440, h=956, os_reduce=False):
    kw = dict(viewport={"width": w, "height": h}, device_scale_factor=1, has_touch=True)
    if os_reduce: kw["reduced_motion"] = "reduce"
    ctx = br.new_context(**kw)
    ctx.add_init_script(seed); ctx.add_init_script(S.STANDALONE)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    pg.route("**/version.json", lambda r, q: r.abort())
    pg.goto(url, timeout=LOAD_MS); pg.wait_for_timeout(2600)
    pg.evaluate("document.getElementById('splashscreen')?.remove()")
    pg.evaluate("()=>{ try{ const u=pendingHomeUnlocks(); markUnlocksShown(u.chars,u.banners,u.fx); }catch(e){} try{ homeUnlocksOwed=()=>false; }catch(e){} document.querySelectorAll('.rs-spot').forEach(n=>n.remove()); }")
    return ctx, pg, errs

def mount(pg, fn):
    fname = fn.split("(")[0]
    if not pg.evaluate(f"typeof {fname}==='function'"): return False
    if fn in S.ONBOARDING_SCREENS:
        pg.evaluate("showWelcome();"); pg.wait_for_timeout(150)
    pg.evaluate(f"{fn if fn.endswith(')') else fn + '()'}; scrollTo(0,0);")
    return True

def sweep(pg, wait_ms):
    """screen -> [snapshot, snapshot] (two, .8s apart)"""
    res = {}
    for fn in SCREENS:
        try:
            if not mount(pg, fn): continue
            pg.wait_for_timeout(wait_ms)
            a = pg.evaluate(SNAP); pg.wait_for_timeout(800); b = pg.evaluate(SNAP)
            res[fn] = [a, b]
        except Exception as exc:
            res[fn] = [{"__err": str(exc)[:100]}]
    return res

def shown(s): return s["o"] >= .9 and s["w"] > 0 and s["h"] > 0
def lost(base, other):
    """elements on the glass in every normal sample and below .5 in every other sample; topmost of nested ones"""
    hits = []
    a0, a1, b0, b1 = base[0], base[1], other[0], other[1]
    for k, v in a0.items():
        v1, w0, w1 = a1.get(k), b0.get(k), b1.get(k)
        if not (v1 and w0 and w1): continue
        if shown(v) and shown(v1) and w0["o"] < .5 and w1["o"] < .5: hits.append((k, v["cls"] or v["id"] or k.rsplit("/", 1)[-1]))
    return [h for h in hits if not any(h[0] != g[0] and h[0].startswith(g[0] + "/") for g in hits)]

PICKER = """()=>{ const vw = innerWidth, vh = innerHeight; return [...document.querySelectorAll('#stage .class-card')].map(c => {
  const cs = getComputedStyle(c), r = c.getBoundingClientRect();
  return { o: cs.opacity, vis: cs.visibility, disp: cs.display, w: r.width, h: r.height, l: r.left, rt: r.right, t: r.top, b: r.bottom, vw, vh, tf: cs.transform }; }); }"""

# ---- C: one element per animation rule, three ways ----
RULES_JS = r"""()=>{
 const SVGT = new Set(['svg','path','circle','g','rect','ellipse','line','polyline','polygon','use','defs','text','tspan','stop','lineargradient','radialgradient','mask','clippath','filter','image']);
 const splitTop = sel => { const out = []; let d = 0, cur = ''; for(const ch of sel){ if(ch === '(' || ch === '[') d++; if(ch === ')' || ch === ']') d--; if(ch === ',' && d === 0){ out.push(cur.trim()); cur = ''; } else cur += ch; } out.push(cur.trim()); return out; };
 const chain = sel => { const parts = []; let d = 0, cur = '', pend = ' ';
   for(let i = 0; i < sel.length; i++){ const ch = sel[i];
     if(ch === '(' || ch === '[') d++; if(ch === ')' || ch === ']') d--;
     if(d === 0 && (ch === ' ' || ch === '>' || ch === '+' || ch === '~')){ if(cur){ parts.push({ c: cur, comb: pend }); cur = ''; pend = ' '; } if(ch !== ' ') pend = ch; continue; }
     cur += ch; }
   if(cur) parts.push({ c: cur, comb: pend }); return parts; };
 const simplify = c => { let s = c;
   for(let n = 0; n < 8; n++){ const m = s.match(/:(is|where)\(/); if(!m) break; const st = m.index, open = st + m[0].length - 1; let d = 0, j = open; for(; j < s.length; j++){ if(s[j] === '(') d++; if(s[j] === ')'){ d--; if(!d) break; } } s = s.slice(0, st) + splitTop(s.slice(open + 1, j))[0] + s.slice(j + 1); }
   for(let n = 0; n < 8; n++){ const m = s.match(/:(not|has)\(/); if(!m) break; const st = m.index, open = st + m[0].length - 1; let d = 0, j = open; for(; j < s.length; j++){ if(s[j] === '(') d++; if(s[j] === ')'){ d--; if(!d) break; } } s = s.slice(0, st) + s.slice(j + 1); }
   return s; };
 const build = c0 => { const pe = (c0.match(/::?(before|after)\s*$/) || [])[1] || ''; let c = simplify(c0.replace(/::?(before|after)\s*$/, ''));
   c = c.replace(/::?[a-z-]+(\([^)]*\))?/g, '');
   const tag = (c.match(/^[a-zA-Z][\w-]*/) || [''])[0].toLowerCase(); const ids = [...c.matchAll(/#([\w-]+)/g)].map(m => m[1]); const cls = [...c.matchAll(/\.([\w-]+)/g)].map(m => m[1]);
   const attrs = [...c.matchAll(/\[([\w-]+)(?:[~|^$*]?=(?:"([^"]*)"|'([^']*)'|([^\]\s]*)))?(?:\s+[is])?\]/g)].map(m => [m[1], m[2] ?? m[3] ?? m[4] ?? '']);
   return { tag, ids, cls, attrs, pe }; };
 const seen = new Set(), cands = [];
 const walk = list => { for(const r of list){ if(r.type === CSSRule.STYLE_RULE){ const s = r.style; if(s.animationName && s.animationName !== 'none') for(const sel of splitTop(r.selectorText)) if(!seen.has(sel)){ seen.add(sel); cands.push({ sel, name: s.animationName, fill: s.animationFillMode }); } }
   else if(r.cssRules && r.type !== CSSRule.KEYFRAMES_RULE) walk(r.cssRules); } };
 for(const sh of document.styleSheets){ try{ walk(sh.cssRules); }catch(e){} }
 const holder = document.createElement('div'); holder.id = '__probe'; holder.style.cssText = 'position:fixed;left:0;top:0;width:300px;height:300px;'; document.body.appendChild(holder);
 const root = document.documentElement;
 const state = (el, pe) => { const cs = getComputedStyle(el, pe ? '::' + pe : null); return { o: parseFloat(cs.opacity), v: cs.visibility, t: cs.transform }; };
 const finish = el => { try{ el.getAnimations({ subtree: true }).forEach(a => { if(a.effect.getComputedTiming().iterations !== Infinity) a.finish(); }); }catch(e){} };
 const results = []; let skipped = 0;
 for(const c of cands){
   const parts = chain(c.sel.replace(/\s+/g, ' ').replace(/\s*([>+~])\s*/g, ' $1 ').trim());
   if(!parts.length || parts.some(p => p.comb === '+' || p.comb === '~')){ skipped++; continue; }
   const undo = []; let parent = holder, leaf = null, pe = '';
   for(let i = 0; i < parts.length; i++){ const b = build(parts[i].c); if(i === parts.length - 1) pe = b.pe;
     if(/^(html|body)$/.test(b.tag) || /^:root/.test(parts[i].c)){
       const el = b.tag === 'body' ? document.body : root;
       b.cls.forEach(k => { if(!el.classList.contains(k)){ el.classList.add(k); undo.push(() => el.classList.remove(k)); } });
       b.attrs.forEach(([k, v]) => { if(!el.hasAttribute(k)){ el.setAttribute(k, v); undo.push(() => el.removeAttribute(k)); } });
       if(i === parts.length - 1) leaf = el; continue; }
     const el = SVGT.has(b.tag) ? document.createElementNS('http://www.w3.org/2000/svg', b.tag) : document.createElement(b.tag || 'div');
     b.ids.forEach(k => el.setAttribute('id', k)); b.cls.forEach(k => el.classList.add(k)); b.attrs.forEach(([k, v]) => el.setAttribute(k, v));
     parent.appendChild(el); parent = el; leaf = el; }
   let matches = false; try{ matches = !!leaf && leaf.matches(c.sel.replace(/::?(before|after)\s*$/, '')); }catch(e){}
   if(!matches){ skipped++; undo.forEach(f => f()); holder.replaceChildren(); continue; }
   const had = root.dataset.reduceMotion; root.dataset.reduceMotion = 'false';
   finish(leaf); const n = state(leaf, pe);
   root.dataset.reduceMotion = 'true'; const a = state(leaf, pe);
   root.dataset.reduceMotion = had === undefined ? 'false' : had;
   results.push({ sel: c.sel, name: c.name, fill: c.fill, pe, n, a });
   undo.forEach(f => f()); holder.replaceChildren(); }
 holder.remove(); return { results, skipped, total: cands.length }; }"""

# Hidden with Reduce motion on BY DESIGN, with the reason. A rule that ends visible with motion on and hidden with it off and is
# not here fails section C.
ALLOWED = [
    (r"^body\.cutscene-focus", "a cutscene holds the stage: the tab bar and chat button are hidden outright (visibility), as before"),
    (r"^\.rs-(land|card\.rs-land|xpline\.rs-land|grade(\.is-counting)?\.rs-land|screen \.rs-unlocked)", "the results cards: with Reduce motion they are built already landed (rs-in-now), never rs-in"),
    (r"^\.badge-cutscene-in", "the badge cutscene is never built with Reduce motion: showTierUpStyleBadgeNote is shown instead"),
    (r"^\.rs-spot\.is-up \.rs-morph-rays", "the rank-up's turning rays are an effect layer, off at rest"),
    (r"^\.bc-slot\.is-new \.badge-shine-band", "a glint across a badge: off at rest"),
    (r"^\.sf-absence \.sfv-blackwave", "a flash layer of the rank scenes: off at rest (their still has its own rules)"),
]

def rules_check(br, os_reduce):
    ctx = br.new_context(viewport={"width": 440, "height": 956}, reduced_motion="reduce" if os_reduce else "no-preference")
    ctx.add_init_script(S.SEED); ctx.add_init_script(S.STANDALONE)
    pg = ctx.new_page(); pg.route("**/version.json", lambda r, q: r.abort())
    pg.goto(url, timeout=LOAD_MS); pg.wait_for_timeout(2600)
    d = pg.evaluate(RULES_JS); ctx.close(); return d

def vis(s): return s["o"] >= .5 and s["v"] != "hidden"
def mat(t):
    if t in ("none", ""): return (1, 0, 0, 1, 0, 0)
    m = re.match(r"matrix3?d?\(([^)]*)\)", t)
    if not m: return None
    v = [float(x) for x in m.group(1).split(",")]
    return tuple(v) if len(v) == 6 else (v[0], v[1], v[4], v[5], v[12], v[13])
def settled(t):   # at its place: no offset past 2px, no scale below .9
    m = mat(t); return m is not None and abs(m[4]) <= 2 and abs(m[5]) <= 2 and m[0] >= .9 and m[3] >= .9
def displaced(t):  # left off its place: 20px or more away, or shrunk to under half
    m = mat(t); return m is not None and (abs(m[4]) > 20 or abs(m[5]) > 20 or m[0] < .5 or m[3] < .5)

srv, url = S.serve()
errs_all = []
try:
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=S.CHROME)
        base = None
        if "A" in SECTIONS or "B" in SECTIONS:
            ctx, pg, errs = new_page(br, S.SEED); errs_all += errs
            base = sweep(pg, 2200); ctx.close()
            chk("A/B baseline: %d screens mounted with motion normal" % len(base), len(base) >= 20, len(base))
        if "A" in SECTIONS:
            ctx, pg, errs = new_page(br, SEED_REDUCE); errs_all += errs
            chk("A the page is in Reduce motion (data-reduce-motion=true)", pg.evaluate("document.documentElement.dataset.reduceMotion") == "true")
            red = sweep(pg, 700); ctx.close()
            bad = {}
            for fn, b in base.items():
                if "__err" in b[0] or fn not in red or "__err" in red[fn][0]: continue
                h = lost(b, red[fn])
                if h: bad[fn] = h
            for fn in base:
                if fn in red and "__err" not in base[fn][0] and "__err" not in red[fn][0]:
                    chk(f"A {fn}: everything that shows with motion on shows with Reduce motion on", fn not in bad, bad.get(fn, [])[:4])
            for name, w, h in (("phone", 440, 956), ("iPad Pro 11", 834, 1194)):
                ctx, pg, errs = new_page(br, SEED_REDUCE, w, h); errs_all += errs
                for fn, label in (("showClassSelection", "Select your classes"), ("showClassCatalog", "Classes")):
                    mount(pg, fn); pg.wait_for_timeout(1500)
                    cards = pg.evaluate(PICKER)
                    chk(f"A {label} {name}: the class cards are there (at least 2; found {len(cards)})", len(cards) >= 2, cards)
                    for i, c in enumerate(cards):
                        chk(f"A {label} {name} card {i + 1}: computed opacity 1, visible, a box inside the screen (opacity {c['o']}, {c['vis']}, {c['w']:.0f}x{c['h']:.0f} at {c['l']:.0f},{c['t']:.0f})",
                            float(c["o"]) == 1 and c["vis"] == "visible" and c["w"] > 40 and c["h"] > 40 and c["l"] >= -1 and c["rt"] <= c["vw"] + 1, c)
                errs_all += errs; ctx.close()
        if "B" in SECTIONS:
            ctx, pg, errs = new_page(br, S.SEED, os_reduce=True); errs_all += errs
            chk("B the OS setting is on and the in-app switch is not", pg.evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches && document.documentElement.dataset.reduceMotion !== 'true'"))
            osr = sweep(pg, 1200); ctx.close()
            bad = {}
            for fn, b in base.items():
                if "__err" in b[0] or fn not in osr or "__err" in osr[fn][0]: continue
                h = lost(b, osr[fn])
                if h: bad[fn] = h
            chk(f"B no screen loses an element under the OS setting ({len(base)} screens)", not bad, bad)
        if "C" in SECTIONS:
            n = rules_check(br, False)
            o = {r["sel"]: r for r in rules_check(br, True)["results"]}
            chk(f"C built an element for {len(n['results'])} of {n['total']} animation selectors ({n['skipped']} sibling/unbuildable skipped)", len(n["results"]) > 1500, n["total"])
            appbad, osbad, allowed, tfbad = [], [], 0, []
            for r in n["results"]:
                if not vis(r["n"]): continue
                why = next((w for pat, w in ALLOWED if re.search(pat, r["sel"])), None)
                if not vis(r["a"]):
                    if why: allowed += 1
                    else: appbad.append((("::" + r["pe"] + " ") if r["pe"] else "") + r["sel"][:110])
                elif settled(r["n"]["t"]) and displaced(r["a"]["t"]) and not r["pe"]: tfbad.append(r["sel"][:110] + "  " + r["a"]["t"][:40])
                x = o.get(r["sel"])
                if x and not vis(x["n"]) and not why: osbad.append(r["sel"][:110])
                if x and vis(x["n"]) and settled(r["n"]["t"]) and displaced(x["n"]["t"]) and not r["pe"]: tfbad.append("(OS) " + r["sel"][:110])
            print(f"     ({allowed} hidden-by-design selectors allowed, see ALLOWED)")
            chk(f"C in-app Reduce motion: no animation rule ends visible with motion on and hidden with it off ({len(appbad)})", not appbad, appbad[:8])
            chk(f"C the OS setting: the same ({len(osbad)})", not osbad, osbad[:8])
            chk(f"C nothing is left 20px off its place, or shrunk to under half, that its animation brings home ({len(tfbad)})", not tfbad, tfbad[:8])
        if "D" in SECTIONS:
            ctx = br.new_context(viewport={"width": 440, "height": 956}, device_scale_factor=1, has_touch=True)
            ctx.add_init_script(SEED_REDUCE); ctx.add_init_script(S.STANDALONE)
            pg = ctx.new_page(); pg.route("**/version.json", lambda r, q: r.abort())
            pg.add_init_script("""window.__sp = []; (function tick(){ try{ const g = document.getElementById('splash-group'), s = document.getElementById('splashscreen');
              window.__sp.push({ t: Math.round(performance.now()), up: !!s, hide: !!(s && s.classList.contains('splash-hide')), attr: document.documentElement.dataset.reduceMotion || '',
                o: g ? parseFloat(getComputedStyle(g).opacity) : null, v: g ? getComputedStyle(g).visibility : null }); }catch(e){} if(window.__sp.length < 4000) requestAnimationFrame(tick); })();""")
            pg.goto(url, timeout=LOAD_MS, wait_until="commit"); pg.wait_for_timeout(4500)
            sp = pg.evaluate("window.__sp")
            ctx.close()
            # frames where the switch is applied, the splash is up and not leaving, and the word's group is placed (visible)
            after = [f for f in sp if f["up"] and not f["hide"] and f["attr"] == "true" and f["v"] == "visible"]
            chk(f"D the splash was on screen with the switch applied for {len(after)} frames (of {len(sp)})", len(after) >= 3, len(sp))
            worst = min((f["o"] for f in after), default=None)
            chk(f"D the splash's word is fully shown in every one of them (lowest opacity {worst})", bool(after) and worst >= .99, worst)
        if SHOTS:
            for name, w, h in (("phone", 440, 956), ("ipad", 834, 1194)):
                for mode, seed in (("normal", S.SEED), ("reduce", SEED_REDUCE)):
                    ctx, pg, errs = new_page(br, seed, w, h)
                    for fn, tag in (("showClassSelection", "select"), ("showClassCatalog", "classes")):
                        mount(pg, fn); pg.wait_for_timeout(2200)
                        pg.screenshot(path=os.path.join(SHOTS, f"{tag}-{w}x{h}-{mode}.png"))
                    ctx.close()
            print("screenshots in", SHOTS)
        br.close()
finally:
    srv.shutdown()
real = [e for e in errs_all if not any(k in e for k in S.EXPECTED_ERRORS)]
chk("no page errors", not real, real[:3])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
