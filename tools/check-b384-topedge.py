"""Build 384.27: THE STILL TOP EDGE of an installed iPhone/iPad app.
Reports on iOS 26/27 (folio #1026 and others; docs/notes-archive.md "384.26") say the system's top blur latches on the first time, after launch, the element at
the top edge is changed or replaced, or the theme-color / color-scheme tags are rewritten. The app did all three (a new #top-guard for each colour, made after the splash;
syncStatusBarColor / applyTheme writing both tags on every theme, Home and class change). Installed on an iPhone (iOS user agent + standalone) it now:
 (1) has ONE strip, #top-edge, as the first element of <body> in the served HTML: fixed, top 0, full width, 12px (over the 10px the reports read as the floor), above
     everything, taking touch (the variant with the best device evidence), the splash's #0A0A0A at its first frame;
 (2) is that same node for the whole life of the page: after a theme accent change, a move between Home, Profile, the rankings and Settings and back, and in the page a
     class switch reloads into; its colour follows the sky's top colour by changing in place, and the cache for the next launch follows too;
 (3) writes neither <meta theme-color> nor <meta color-scheme> after the page's first paint (the head script's one replay is before it): zero writes, in all of those;
 (4) is unchanged in a Safari tab, on a laptop, and with class26e.topguard = "0" (no strip shown there; the tags still follow the theme in a tab);
 (5) has the old behaviour (a new strip for each colour, the tags rewritten) behind class26e.topedgeold = "1" - the display test's A/B - and an ignore-touch variant behind
     class26e.topedgepe = "none"; the display test's readout says which is active; no page errors.
Run:  python3 tools/check-b384-topedge.py   (--against OLD/index.html must FAIL)"""
import os, sys, re, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
if "--against" in sys.argv:
    body = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
    cb.BODY = cb.INSET_RE.sub("0px", body).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1"
# every write to either tag, from the moment the page starts, and the strip as the markup first has it
WATCH = """(() => {
  window.__tagWrites = []; window.__edge0 = null; window.__edgeBg0 = null;
  const after = () => { if(document.getElementById('splashscreen')) window.__sawSplash = true; return !!window.__sawSplash || document.readyState !== 'loading'; };
  const log = (el, how) => { try{ const n = el.getAttribute('name'); if(n === 'theme-color' || n === 'color-scheme') window.__tagWrites.push({ n, how, after: after() }); }catch(e){} };
  const d = Object.getOwnPropertyDescriptor(HTMLMetaElement.prototype, 'content');
  Object.defineProperty(HTMLMetaElement.prototype, 'content', { configurable: true, get: d.get, set(v){ log(this, 'content'); d.set.call(this, v); } });
  const sa = Element.prototype.setAttribute;
  Element.prototype.setAttribute = function(a, v){ if(this.tagName === 'META' && a === 'content') log(this, 'setAttribute'); return sa.call(this, a, v); };
  const isTag = n => n && n.nodeType === 1 && n.tagName === 'META' && /^(theme-color|color-scheme)$/.test(n.getAttribute('name') || '');
  new MutationObserver(recs => recs.forEach(r => [...r.addedNodes, ...r.removedNodes].forEach(n => { if(isTag(n)) window.__tagWrites.push({ n: n.getAttribute('name'), how: 'node', after: after() }); }))).observe(document, { subtree: true, childList: true });
  document.addEventListener('DOMContentLoaded', () => { const e = document.getElementById('top-edge'); window.__edge0 = e; window.__edgeBg0 = e ? getComputedStyle(e).backgroundColor : null; });
})();"""
def boot(br, ios=True, standalone=True, extra="", wait=3000):
    kw = dict(viewport={"width": 440, "height": 956}, device_scale_factor=2, has_touch=ios, is_mobile=ios)
    if ios: kw["user_agent"] = UA
    ctx = br.new_context(**kw)
    ctx.add_init_script(WATCH)
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
                        "localStorage.setItem('class26e.drill.v1','%s');localStorage.setItem('class26e.weekrecap.v1','9999-12-31');localStorage.setItem('class26e.savecode.card','1');%s}catch(e){}" % (cb.USED_ACCOUNT, extra))
    if standalone: ctx.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true});")
    pg = cb.open_page(ctx); pg.goto(cb.URL); pg.wait_for_timeout(wait)
    return ctx, pg
def clear_splash(pg):
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); }"); pg.wait_for_timeout(900)
EDGE = """()=>{ const e = document.getElementById('top-edge'); if(!e) return null; const cs = getComputedStyle(e), r = e.getBoundingClientRect(); const sp = document.getElementById('splashscreen');
  return { disp: cs.display, pos: cs.position, top: r.top, left: r.left, w: r.width, h: r.height, z: +cs.zIndex, pe: cs.pointerEvents, aria: e.getAttribute('aria-hidden'), vw: innerWidth,
           same: e === window.__edge0, inline: e.style.backgroundColor, data: e.dataset.color || '', sky: appTopEdgeColor(), cache: localStorage.getItem('class26e.statusbar.v1'),
           first: window.__edgeBg0, kids: [...document.body.children].slice(0, 2).map(x => x.id), hit: (document.elementFromPoint(Math.round(innerWidth / 2), 4) || {}).id }; }"""
# (384.77) the strip WEARS the sky (topStripsSky: body::before's gradients over the paper), so its colour is read from dataset.color, the sky colour syncTopGuard gives it in place
WRITES = "()=>({ after: window.__tagWrites.filter(w => w.after), before: window.__tagWrites.filter(w => !w.after).length })"
# (384.80, changed on purpose) theme-color is now set to the strip's colour and "danced" (c, c+'fe', c) whenever it changes - the Safari 26
# tinting write-up the owner found; color-scheme is still never written after launch, and that is what (3) holds now
WRITES_CS = "()=>({ after: window.__tagWrites.filter(w => w.after && w.n === 'color-scheme'), before: window.__tagWrites.filter(w => !w.after).length })"
def hexof(c):
    if re.match(r"^#[0-9a-fA-F]{6}$", c or ""): return c.lower()
    m = re.findall(r"[\d.]+", c or "")
    return "#%02x%02x%02x" % tuple(int(float(x)) for x in m[:3]) if len(m) >= 3 else None
errs = []
with sync_playwright() as pw:
    br = pw.chromium.launch()
    # ---------------- (1) the strip, in the markup, at its first frame ----------------
    m = re.search(r"<body[^>]*>\s*<div id=\"top-edge\"", cb.BODY)
    chk("(1) the served HTML has #top-edge as the first element of <body>", bool(m))
    try:
        ctx, pg = boot(br, wait=250)
        pg.on("pageerror", lambda e: errs.append(str(e)[:140]))
        r = pg.evaluate(EDGE); r["splash"] = pg.evaluate("()=>{ const s = document.getElementById('splashscreen'); return !!s && !s.classList.contains('splash-hide'); }")
        # (384.80, changed on purpose: r/PWA's production fix) the whole safe area, 12px where there is none since 384.85 (was 6; febbbi: 11px+ is the reliable height) (this gate's insets are 0), above everything,
        # (z 2147483647, as the r/PWA element; it holds the status bar's area only), taps going through
        chk("(1) installed on an iPhone, before the splash goes: the splash's colour, fixed at the top, full width, max(inset, 12px), above everything, taps through (%s)" % r,
            r and r["disp"] == "block" and r["pos"] == "fixed" and r["top"] == 0 and r["left"] == 0 and abs(r["w"] - r["vw"]) < 1 and r["h"] == 12 and r["z"] > 1000000 and r["pe"] == "none"
            and r["aria"] == "true" and hexof(r["first"]) == "#0a0a0a" and r["kids"][0] == "top-edge", r)
        chk("(1) while the splash is up the strip stays the splash's colour (it does not show as a band of sky over it) (%s)" % (r and [r["splash"], r["inline"]]), r and r["splash"] and hexof(r["inline"]) == "#0a0a0a" and r["data"] == "", r)   # (384.80) an inline colour from the first byte
        # ---------------- (2) the same node, following the sky ----------------
        pg.wait_for_timeout(2800); clear_splash(pg)
        r = pg.evaluate(EDGE)
        seen = [hexof(r["data"])] if r else []
        chk("(2) once the splash goes, the strip takes the sky's colour in place (%s vs %s)" % (r and r["inline"], r and r["sky"]), r and r["same"] and hexof(r["data"]) == r["sky"].lower(), r)
        w0 = pg.evaluate(WRITES_CS)
        chk("(3) after boot and the splash: no write to color-scheme after the first paint (theme-color follows the strip since 384.80) (%s)" % w0["after"], len(w0["after"]) == 0, w0)
        ACC0 = pg.evaluate("()=>theme.accent"); ALT = "veteran" if ACC0 != "veteran" else "ink"
        pg.evaluate("()=>{ theme.accent = '%s'; applyTheme(); }" % ALT); pg.wait_for_timeout(700)
        r2 = pg.evaluate(EDGE); seen.append(hexof(r2["data"]))
        chk("(2) a theme accent change: the same node, its colour followed (%s -> %s) and the next launch's cache follows (%s)" % (r["inline"], r2["inline"], r2["cache"]),
            r2["same"] and hexof(r2["data"]) == r2["sky"].lower() and hexof(r2["data"]) != hexof(r["data"]) and (r2["cache"] or "").lower() == r2["sky"].lower(), r2)
        steps = []
        for call in ("showProfile()", "showHome()", "showRankings()", "showHome()", "showAppearance()", "showHome()"):
            pg.evaluate("()=>{ try{ %s }catch(e){} }" % call); pg.wait_for_timeout(700)
            x = pg.evaluate(EDGE); seen.append(hexof(x["data"])); steps.append((call, x["same"], hexof(x["data"]) == x["sky"].lower()))
        chk("(2) moving between Home, Profile, the rankings and Settings (the calm and the Home sky): always the same node, always the sky's colour (%s)" % steps, all(s[1] and s[2] for s in steps), steps)
        chk("(2) the colour really did change along the way (%d different colours: not a check that nothing moved)" % len(set(seen)), len(set(seen)) >= 2, seen)
        w1 = pg.evaluate(WRITES_CS)
        chk("(3) after all of that: still no write to color-scheme after the first paint (%s)" % w1["after"], len(w1["after"]) == 0, w1)
        tags = pg.evaluate("()=>[document.getElementById('themecolor').content, document.getElementById('colorscheme').content]")
        chk("(3) the tags still say what the head set (theme-color is the head script's or the file's, color-scheme dark) (%s)" % tags, tags[1] == "dark", tags)
        # a class switch: the page it reloads into
        pg.evaluate("()=>{ theme.accent = '%s'; applyTheme(); }" % ACC0)
        try:
            with pg.expect_navigation(timeout=15000):
                pg.evaluate("()=>{ setEnrolled('ifc', true); localStorage.setItem('class26e.greet.ifc', 'done'); switchClass('ifc'); }")
            pg.wait_for_timeout(3000); clear_splash(pg)
            rc = pg.evaluate(EDGE); wc = pg.evaluate(WRITES_CS)
            chk("(2)(3) the page a class switch reloads into: one strip, the sky's colour, the same node, no tag written after the first paint (%s, %s)" % (rc and rc["inline"], wc["after"]),
                rc and rc["same"] and hexof(rc["data"]) == rc["sky"].lower() and len(wc["after"]) == 0, [rc, wc])
        except Exception as e:
            chk("(2)(3) a class switch reloads the page", False, str(e)[:200])
        ctx.close()
    except Exception as e:
        chk("(1)-(3) the scenario ran to its end", False, repr(e))
        try: ctx.close()
        except Exception: pass
    # ---------------- (2)(3) the same, measured without naming the strip: the default, installed on an iPhone ----------------
    ctx, pg = boot(br); clear_splash(pg)
    pg.evaluate("()=>{ window.__top0 = document.getElementById('top-edge') || document.getElementById('top-guard'); theme.accent = 'veteran'; applyTheme(); }"); pg.wait_for_timeout(800)
    pg.evaluate("()=>{ showProfile(); }"); pg.wait_for_timeout(700)
    x = pg.evaluate("()=>({ same: (document.getElementById('top-edge') || document.getElementById('top-guard')) === window.__top0, has: !!window.__top0, writes: window.__tagWrites.filter(w => w.after && w.n === 'color-scheme').length })")
    chk("(2)(3) after a theme change and a move to Profile, the default has the same top strip node and has not written color-scheme (%s)" % x, x["has"] and x["same"] and x["writes"] == 0, x)
    ctx.close()
    # ---------------- (4) nowhere else ----------------
    ctx, pg = boot(br, True, False); clear_splash(pg)
    r = pg.evaluate(EDGE); tc0 = pg.evaluate("()=>document.getElementById('themecolor').content")
    pg.evaluate("()=>{ theme.accent = 'veteran'; applyTheme(); }"); pg.wait_for_timeout(500)
    w = pg.evaluate(WRITES); tc1 = pg.evaluate("()=>document.getElementById('themecolor').content")
    chk("(4) an iPhone in a Safari tab: no strip shown, and the tags follow the theme as they did (%s: %s -> %s, %d writes)" % (r and r["disp"], tc0, tc1, len(w["after"])), (r is None or r["disp"] == "none") and tc1 != tc0 and len(w["after"]) > 0, [r, tc0, tc1, w])
    ctx.close()
    ctx, pg = boot(br, False, False); clear_splash(pg)
    r = pg.evaluate(EDGE)
    chk("(4) a laptop: no strip shown (%s)" % (r and r["disp"]), r is None or r["disp"] == "none", r)
    ctx.close()
    ctx, pg = boot(br, True, True, extra="localStorage.setItem('class26e.topguard','0');"); clear_splash(pg)
    r = pg.evaluate(EDGE); g = pg.evaluate("()=>!!document.getElementById('top-guard')")
    chk("(4) with class26e.topguard = 0 no strip is shown (%s)" % (r and r["disp"]), (r is None or r["disp"] == "none") and not g, [r, g])
    ctx.close()
    # ---------------- (5) the old behaviour, and the ignore-touch variant ----------------
    ctx, pg = boot(br, True, True, extra="localStorage.setItem('class26e.topedgeold','1');"); clear_splash(pg)
    r = pg.evaluate(EDGE); g0 = pg.evaluate("()=>{ const g = document.getElementById('top-guard'); window.__g0 = g; return g ? [g.offsetHeight, getComputedStyle(g).pointerEvents] : null; }")
    pg.evaluate("()=>{ theme.accent = 'veteran'; applyTheme(); }"); pg.wait_for_timeout(700)
    g1 = pg.evaluate("()=>({ replaced: document.getElementById('top-guard') !== window.__g0, n: document.querySelectorAll('#top-guard').length })"); w = pg.evaluate(WRITES)
    chk("(5) class26e.topedgeold = 1: the old behaviour - the 8px strip that ignores touch, replaced when the colour changes, the tags rewritten (%s, %s, %d writes)" % (g0, g1, len(w["after"])),
        (r is None or r["disp"] == "none") and g0 == [8, "none"] and g1["replaced"] and g1["n"] == 1 and len(w["after"]) > 0, [r, g0, g1, w])
    ctx.close()
    ctx, pg = boot(br, True, True, extra="localStorage.setItem('class26e.topedgepe','none');"); clear_splash(pg)
    r = pg.evaluate(EDGE)
    chk("(5) class26e.topedgepe = none: the same strip, ignoring touch (%s)" % (r and r["pe"]), r and r["pe"] == "none" and r["hit"] != "top-edge", r)
    ctx.close()
    for old in (False, True):
        ctx, pg = boot(br, True, True, extra="localStorage.setItem('class26e.displaytest','1');" + ("localStorage.setItem('class26e.topedgeold','1');" if old else "")); clear_splash(pg)
        rd = pg.evaluate("()=>window.__diagTrials && window.__diagTrials.readout()") or ""
        line = [l for l in rd.splitlines() if l.startswith("top edge behaviour")]
        chk("(5) the display test's readout says which behaviour is active (%s)" % line, line and (("OLD" in line[0]) if old else ("STILL" in line[0])), rd[:300])
        ctx.close()
    ctx, pg = boot(br, True, True, extra="localStorage.setItem('class26e.displaytest','1');"); clear_splash(pg)
    ids = pg.evaluate("()=>[...document.querySelectorAll('#diagpanel [data-trial]')].map(b => b.dataset.trial)")
    chk("(5) the display test has the switches for it (old behaviour, ignore touch) (%s)" % [i for i in ids if i in ("old", "pe0")], "old" in ids and "pe0" in ids, ids)
    pg.evaluate("()=>window.__diagTrials.toggle('old', true)"); pg.wait_for_timeout(500)
    live = pg.evaluate("()=>({ edge: getComputedStyle(document.getElementById('top-edge')).display, guard: !!document.getElementById('top-guard') })")
    pg.evaluate("()=>window.__diagTrials.toggle('old', false)"); pg.wait_for_timeout(500)
    back = pg.evaluate("()=>({ edge: getComputedStyle(document.getElementById('top-edge')).display, guard: !!document.getElementById('top-guard') })")
    chk("(5) ticking it puts the old behaviour on live and unticking puts the still edge back (%s, %s)" % (live, back), live == {"edge": "none", "guard": True} and back == {"edge": "block", "guard": False}, [live, back])
    ctx.close()
    chk("no page errors", not errs, errs)
    br.close()
print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
