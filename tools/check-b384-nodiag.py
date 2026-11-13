"""Build 384.105: THE DISPLAY TEST IS GONE, AND NO DEVICE IS LEFT ON ONE OF ITS SWITCHES.
Madison: "Remove the 'show the display test panel' stuff from settings by the way." The display test (384 r17 to 384.85) was a panel of
switches for chasing the iOS 26 top-of-screen blur, opened from Settings > Advanced > Troubleshooting or with ?diag in the address. Several
of its switches were localStorage flags the head script read before the first paint, and phones had them on (docs/notes-archive.md
"384.105"). Installed iPhone 17 Pro Max (440x956, 62/34 simulated) unless said:
  N1 SETTINGS  every Settings screen (the menu, its eight pages, Advanced), in the academy and in Fire Code, with the panel's own flag set
               beforehand: no "display test" words anywhere on the page and no panel; Advanced's sections are each a header, a card with
               rows and its notes, none empty; and every element of every Settings screen sits on 384.99's rect (0.5px) - Advanced is
               384.99's page with its LAST section (header, card, note) gone and nothing above it moved.
  N2 ?diag     ?diag, ?diag=1 and ?x=1&diag show nothing: no panel, no hook, none of its style or trial elements, the same <body>
               children and <html> classes as the plain address.
  N3 FLAGS     every flag the panel could set (and the investigation's others, both classes' copies: class26e.X and class26e.ifc.X) set
               to its "on" value before the page loads: after boot none is left in storage, and the top renders exactly as with no
               flags - the same <html> classes, the same #top-edge (display, box, colour, touch, layer), the same theme-color, and the
               top band (the strip and 100px under it) pixel for pixel on Home, a question and Profile. Pro Max in both classes, an SE,
               and a Safari tab.
  N4 384.99    with no flags the same top band is 384.99's pixel for pixel on Home, a question and Profile (the default is untouched).
  N5 no page errors.
Run:  python3 tools/check-b384-nodiag.py [--against REV|DIR] [--only N1,N2,N3]   (--against origin/main 384.99 must FAIL N1, N2, N3)"""
import importlib.util, io, json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("glitches", os.path.join(HERE, "check-b384-glitches.py"))
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)   # takes --against from sys.argv
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops
chk = G.chk
REF_REV = "ac2f923"   # main 384.99, the last build with the display test (merged in before the final gates)
REF = subprocess.run(["git", "-C", G.REPO, "show", REF_REV + ":index.html"], check=True, capture_output=True).stdout.decode("utf-8")
assert 'APP_BUILD = "2026-11-13-384.99"' in REF, "384.99 not readable from git"
FLAGS = {"displaytest": "1", "dxboot": '["s12","lo24"]', "topguard": "0", "topedgeold": "1", "topedgepe": "none", "topmatch": "1",
         "topdeep": "1", "top383": "1", "topclip": "1", "ojappoff": "1", "topclear": "0", "sbdefault": "1"}
SET_FLAGS = """(()=>{ if(location.protocol !== 'http:' || sessionStorage.getItem('__flagsSet')) return; sessionStorage.setItem('__flagsSet','1');
  const F = %s; for(const k in F){ localStorage.setItem('class26e.' + k, F[k]); localStorage.setItem('class26e.ifc.' + k, F[k]); } })()""" % json.dumps(FLAGS)
# raw keys (key() is not redirected in Fire Code; getItem is)
LEFT = """(names)=>{ const re = new RegExp('^class26e\\\\.(ifc\\\\.)?(' + names.join('|') + ')$'), out = [];
  for(let i = 0; i < localStorage.length; i++){ const k = localStorage.key(i); if(k && re.test(k)) out.push(k + '=' + localStorage.getItem(k)); } return out; }"""
QUIET = "()=>{ theme.reduceMotion = true; try{ applyTheme(); }catch(e){} try{ homeUnlocksOwed=()=>false; }catch(e){} }"
QSTART = """()=>{ showHome(); const u = topicsIn(QUESTIONS)[0]; cfg.mode='drill'; cfg.units=[u]; cfg.versions={}; cfg.source='all'; cfg.size=0; cfg.timer='off';
  cfg.flashcards=false; theme.autoAdvance=false; beginRun(QUESTIONS.map((q,i)=>i).filter(i=>QUESTIONS[i].topic===u), null); }"""
TOP = """()=>{ const e = document.getElementById('top-edge'); const cs = e && getComputedStyle(e), r = e && e.getBoundingClientRect();
  const m = document.getElementById('themecolor');
  return { cls: document.documentElement.className.split(/\\s+/).filter(c => c && c !== 'page-locked').sort().join(' '),
    edge: e ? [cs.display, cs.position, Math.round(r.top), Math.round(r.height), Math.round(r.width), cs.backgroundColor, cs.backgroundImage, cs.backgroundClip, cs.pointerEvents, cs.zIndex] : null,
    tc: m ? m.getAttribute('content') : null, guard: !!document.getElementById('top-guard'), deep: !!document.getElementById('top-deep') && getComputedStyle(document.getElementById('top-deep')).display !== 'none' }; }"""
GONE = """()=>({ panel: !!document.getElementById('diagpanel'), hook: typeof window.__diagTrials !== 'undefined',
  styles: document.querySelectorAll('style[id^="diag-"], style[id^="dx-"]').length, trials: document.querySelectorAll('[id^="dx-"], [data-trial]').length,
  kids: [...document.body.children].map(e => e.id).filter(Boolean).join(','),   /* the named ones: an unnamed toast or pop-up comes and goes on its own clock */
  cls: document.documentElement.className.split(/\\s+/).filter(c => c && c !== 'page-locked').sort().join(' ') })"""
SETTINGS = [("menu", "()=>showAppearance()")] + [(k, "()=>showAppearance({page:'%s'})" % k) for k in
            ("sound", "study", "motion", "sync", "share", "rankings", "account", "classes")] + [("advanced", "()=>showAdvancedSettings()")]
# every box on a Settings screen, in document order
BOXES = """()=>{ const p = document.querySelector('#stage > .panel'); if(!p) return null;
  const els = [...p.querySelectorAll('.settings-nav, .settings-nav h1, .slab, .settings-card, .settings-row, .settings-footnotes, .settings-footnote, .settings-buildline')]
    .filter(e => e.getClientRects().length);
  return { sh: document.documentElement.scrollHeight, els: els.map(e => { const r = e.getBoundingClientRect(); return [e.className.split(' ')[0], ...[r.left, r.top + scrollY, r.width, r.height].map(v => Math.round(v * 2) / 2)]; }),
    words: /display test/i.test(document.body.innerText || ''), panel: !!document.getElementById('diagpanel') }; }"""
ADV_SHAPE = """()=>{ const p = document.querySelector('#stage .screen-advsettings'); if(!p) return null; const kids = [...p.children], out = [];
  kids.forEach((k, i) => { if(k.classList.contains('slab')){ const c = kids[i + 1]; out.push({ head: !!c && c.classList.contains('settings-card'), rows: c ? c.querySelectorAll('.settings-row').length : 0 }); } });
  return { sections: out, emptyCards: [...p.querySelectorAll('.settings-card')].filter(c => !c.querySelector('.settings-row')).length,
    last: kids.length ? kids[kids.length - 1].className : null }; }"""
errs = []
ONLY = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else ["N1", "N2", "N3"]   # N3 runs N4 too

def open_raw(br, dev, raw, inits=(), query="", dsf=2, wait=3200):
    w, h, sw, sh, ins, ua, touch, inst = G.DEV[dev]
    ctx = br.new_context(viewport={"width": w, "height": h}, screen={"width": sw, "height": sh}, user_agent=ua, has_touch=touch, is_mobile=touch, device_scale_factor=dsf)
    if inst: ctx.add_init_script(G.STANDALONE)
    if "Macintosh" in ua and touch: ctx.add_init_script(G.TOUCH_POINTS)
    ctx.add_init_script("window.__cloudSeed = {};"); ctx.add_init_script(G.FAKE_CLOUD)
    for sc in inits: ctx.add_init_script(sc)
    pg = ctx.new_page(); mine = []
    pg.on("pageerror", lambda e: mine.append(str(e)[:200]))
    v = {"top": "%dpx" % ins[0], "right": "%dpx" % ins[1], "bottom": "%dpx" % ins[2], "left": "%dpx" % ins[3]}
    body = G.INSET_RE.sub(lambda m: v[m.group(1)], raw)
    build = re.search(r'const APP_BUILD = "([^"]+)"', raw).group(1)
    pg.route("**/index.html*", lambda r, q, b=body: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.route("**/version.json*", lambda r, q, b=build: r.fulfill(status=200, headers={"content-type": "application/json"}, body=json.dumps({"build": b, "force": False, "frameId": ""})))
    # a loaded machine can take longer than the default 30s to fire "load" (the blocked Firebase CDN scripts are in it)
    pg.goto(G.URL + query, wait_until="domcontentloaded", timeout=120000); pg.wait_for_timeout(wait)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); }"); pg.wait_for_timeout(900)
    pg.evaluate(QUIET); G.clear_popups(pg)
    pg.errs = mine; pg.ctx = ctx; pg.ins = ins
    return pg

def mount(pg, js, question=False):
    pg.evaluate("()=>{ showHome(); }"); pg.wait_for_timeout(500)
    pg.evaluate(js)
    if question: pg.wait_for_selector(".qpanel .choice", timeout=30000)
    pg.wait_for_timeout(1500); G.clear_popups(pg)
    pg.evaluate("()=>{ document.querySelectorAll('.intro-pop,#intro-pop,.unlock-card,.rs-spot').forEach(n=>n.remove()); window.scrollTo({top:0, behavior:'instant'}); }")
    pg.wait_for_timeout(900)

def band(pg):
    w = pg.viewport_size["width"]; h = pg.ins[0] + 100
    return Image.open(io.BytesIO(pg.screenshot(clip={"x": 0, "y": 0, "width": w, "height": h}))).convert("RGB")

def pxdiff(a, b):
    if a.size != b.size: return {"n": -1, "sizes": [a.size, b.size]}
    d = ImageChops.difference(a, b); bb = d.getbbox()
    if not bb: return {"n": 0}
    px = d.load(); n = sum(1 for y in range(bb[1], bb[3]) for x in range(bb[0], bb[2]) if max(px[x, y]) > 0)
    return {"n": n, "box": bb, "max": max(e[1] for e in d.getextrema())}

def close(*pgs):
    for p in pgs:
        errs.extend(p.errs)
        try: p.ctx.close()
        except Exception: pass

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G.CHROME)
    # ---------------- N1 Settings ----------------
    if "N1" in ONLY:
        for cls in ("academy", "ifc"):
            pg = open_raw(br, "promax", G.SRC, [G.seed_init(cls), SET_FLAGS])
            pr = open_raw(br, "promax", REF, [G.seed_init(cls)])
            words, moved, shape = [], {}, None
            for name, js in SETTINGS:
                pg.evaluate(js); pr.evaluate(js); pg.wait_for_timeout(1100); G.clear_popups(pg); G.clear_popups(pr)
                a, b = pg.evaluate(BOXES), pr.evaluate(BOXES)
                if a is None or b is None: moved[name] = ["not mounted", a is None, b is None]; continue
                if a["words"] or a["panel"]: words.append(name)
                if name == "advanced":
                    # 384.99's page less its last section: the header, the card and its note
                    if not (len(a["els"]) == len(b["els"]) - 4 and a["els"] == b["els"][:len(a["els"])]):
                        moved[name] = {"here": len(a["els"]), "384.99": len(b["els"]), "first off": next((i for i, (x, y) in enumerate(zip(a["els"], b["els"])) if x != y), None)}
                    shape = pg.evaluate(ADV_SHAPE)
                elif a["els"] != b["els"] or a["sh"] != b["sh"]:
                    i = next((i for i, (x, y) in enumerate(zip(a["els"], b["els"])) if x != y), None)
                    moved[name] = {"first off": i, "here": a["els"][i] if i is not None else len(a["els"]), "384.99": b["els"][i] if i is not None else len(b["els"]), "sh": [a["sh"], b["sh"]]}
            cl = pg.evaluate("window.NOVA_CLASS")
            chk("[N1 %s] no 'display test' words and no panel on any of the %d Settings screens, the panel's flag set beforehand (%s)" % (cl, len(SETTINGS), words or "none"), not words and cl == cls, words)
            chk("[N1 %s] Advanced: each section a header and a card with rows, no empty card, the page ending on a note (%s)" % (cl, shape),
                shape and all(s["head"] and s["rows"] >= 1 for s in shape["sections"]) and shape["emptyCards"] == 0 and (shape["last"] or "").startswith("settings-footnote"), shape)
            chk("[N1 %s] every Settings screen sits on 384.99's rects; Advanced is 384.99's less its last section, nothing above it moved (%s)" % (cl, moved or "same"), not moved, moved)
            close(pg, pr)
    # ---------------- N2 ?diag ----------------
    if "N2" in ONLY:
        plain = open_raw(br, "promax", G.SRC, [G.seed_init("academy")])
        plain.wait_for_timeout(2000); p0 = plain.evaluate(GONE); close(plain)
        for q in ("?diag", "?diag=1", "?x=1&diag"):
            pg = open_raw(br, "promax", G.SRC, [G.seed_init("academy")], query=q)
            pg.wait_for_timeout(2000)   # the old panel re-added itself every 1.5s
            r = pg.evaluate(GONE)
            # nothing on <body> the plain address does not have (Home's daily alert and the intro pop-up come on their own clock, on either load)
            extra = sorted(set(r["kids"].split(",")) - set(p0["kids"].split(",")) - {"dailyalert", "intro-pop"})
            chk("[N2] %s shows nothing: no panel, no hook, no test styles or trials, nothing on <body> the plain address lacks, the same <html> classes (%s, extra %s)"
                % (q, {k: r[k] for k in ("panel", "hook", "styles", "trials")}, extra),
                not r["panel"] and not r["hook"] and r["styles"] == 0 and r["trials"] == 0 and not extra and r["cls"] == p0["cls"], [r, p0])
            close(pg)
    # ---------------- N3 the flags, N4 384.99 ----------------
    if "N3" in ONLY:
        SCREENS = [("home", "()=>showHome()", False), ("question", QSTART, True), ("profile", "()=>showProfile()", False)]
        for dev, cls in (("promax", "academy"), ("promax", "ifc"), ("se", "academy"), ("promax-tab", "academy")):
            pf = open_raw(br, dev, G.SRC, [G.seed_init(cls), SET_FLAGS])
            pn = open_raw(br, dev, G.SRC, [G.seed_init(cls)])
            pr = open_raw(br, dev, REF, [G.seed_init(cls)])
            tag = "%s %s" % (dev, pf.evaluate("window.NOVA_CLASS"))
            left = pf.evaluate(LEFT, list(FLAGS))
            chk("[N3 %s] after boot none of the %d flags is left in storage, in either class's copy (%s)" % (tag, len(FLAGS), left or "none"), not left, left)
            topf, topn, out3, out4 = [], [], {}, {}
            for name, js, q in SCREENS:
                for p in (pf, pn, pr): mount(p, js, q)
                tf, tn, tr = pf.evaluate(TOP), pn.evaluate(TOP), pr.evaluate(TOP)
                bf, bn, brf = band(pf), band(pn), band(pr)
                d3, d4 = pxdiff(bf, bn), pxdiff(bn, brf)
                if tf != tn or d3["n"]: out3[name] = {"flags": tf, "none": tn, "px": d3}
                if d4["n"]: out4[name] = {"px": d4, "384.99": tr, "here": tn}
                if os.environ.get("OUT"):
                    os.makedirs(os.environ["OUT"], exist_ok=True)
                    for lab, im in (("flags", bf), ("none", bn), ("38495", brf)): im.save(os.path.join(os.environ["OUT"], "%s-%s-%s-%s.png" % (dev, cls, name, lab)))
            chk("[N3 %s] with every flag set the top is the default's: <html> classes, #top-edge, theme-color and the top band pixel for pixel on Home, a question and Profile (%s)"
                % (tag, out3 or "same"), not out3, out3)
            chk("[N4 %s] with no flags the top band is 384.99's pixel for pixel on Home, a question and Profile (%s)" % (tag, out4 or "same"), not out4, out4)
            close(pf, pn, pr)
    br.close()
chk("[N5] no page errors (%d)" % len(errs), not errs, errs[:4])
print("\n%s - %d failed" % ("ALL PASS" if not G.fails else "FAIL", len(G.fails)))
sys.exit(1 if G.fails else 0)
