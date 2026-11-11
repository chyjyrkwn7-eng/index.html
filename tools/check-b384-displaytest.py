"""Build 384.26: the display test's TRIALS for the iOS top-edge blur.
The owner's installed iPhone (iOS 26.x) draws a soft grey wash over the top ~95pt of every screen that no layer of ours makes (the 13 steps of the display
test did not move it). The web reports a handful of things that did or did not remove it on other apps; none can be confirmed in Chromium, which cannot draw
the system's blur. So this gate does not claim a fix. It holds the experiments to their shape, by what each does to the page it runs on:
 (1) nothing is there without the flag: no panel, no trial styles or strip, no readout hook; the flag is reachable from Settings > Advanced > Troubleshooting;
 (2) with the flag the panel lists every candidate (strip sizes and kinds, keeping the top edge still, viewport-fit / theme-color / color-scheme live,
     the two inner-scroller modes, content lower, no-overscroll), every trial is OFF at load, there is an All off button and a "what is on" line,
     and the panel starts and stays below the top 120px;
 (3) each trial, switched on from its own button, does the intended thing to the intended computed style / meta / element, changes nothing else
     (the Home screen's key boxes stay where they were unless the trial is meant to move them) and, switched off, leaves the page exactly as it was
     (the head's tags, the root and body style attributes, the body's children, the number of style elements, the screen's boxes);
 (4) radio groups hold one: two strips never at once; a strip hides today's strip while it is up and today's comes back;
 (5) a trial strip is what is at the middle of the top edge, 4px down (the point WebKit samples), and takes touch;
 (6) All off after a mix of trials and suspects puts everything back, and so does the auto test's Done;
 (7) the panel moves and cannot be dragged above 120px; the readout lists the geometry; the notch (59px / 34px) is simulated;
 (8) ?sbs=default / black changes the status-bar-style tag, anything else does not; no page errors.
Run:  python3 tools/check-b384-displaytest.py   (--against OLD/index.html must FAIL)"""
import os, sys, re, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
# the installed iPhone's notch: 59px at the top, 34px at the bottom (the sweep's own figures)
INSETS = {"top": "59px", "bottom": "34px", "left": "0px", "right": "0px"}
SRC = sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else cb.SRC
RAW = open(SRC, encoding="utf-8").read()
cb.BODY = cb.INSET_RE.sub(lambda m: INSETS[m.group(1)], RAW).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1"
def boot(br, flag=True, extra="", url=None):
    ctx = br.new_context(viewport={"width": 440, "height": 956}, device_scale_factor=2, has_touch=True, is_mobile=True, user_agent=UA)
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
                        "localStorage.setItem('class26e.drill.v1','%s');localStorage.setItem('class26e.weekrecap.v1','9999-12-31');localStorage.setItem('class26e.savecode.card','1');%s%s}catch(e){}"
                        % (cb.USED_ACCOUNT, "localStorage.setItem('class26e.displaytest','1');" if flag else "", extra))
    ctx.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true});")
    pg = cb.open_page(ctx)
    pg.route(re.compile(r"index\.html\?.*"), lambda r: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=cb.BODY))
    pg.goto(url or cb.URL); pg.wait_for_timeout(3000)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); }")
    return ctx, pg
STATE = """()=>{
  const de = document.documentElement, b = document.body, q = s => document.querySelector(s);
  const r = s => { const e = q(s); if(!e) return null; const x = e.getBoundingClientRect(); return [Math.round(x.left), Math.round(x.top), Math.round(x.width), Math.round(x.height)]; };
  const g = document.getElementById('top-guard');
  return { metas: [...document.head.querySelectorAll('meta')].map(m => m.outerHTML).join('|'),
           htmlStyle: de.getAttribute('style') || '', bodyStyle: b.getAttribute('style') || '', kids: [...b.children].map(e => e.id || e.className || e.tagName).filter(k => !/^rk-|^top-guard$/.test(k)).sort().join(','),
           styles: [...document.querySelectorAll('style')].filter(e => !/^rk-/.test(e.id)).length, dx: document.querySelectorAll('style[id^=dx-]').length, strip: !!document.getElementById('dx-strip'),
           guard: g ? [getComputedStyle(g).display, g.dataset.color] : null, tc: document.getElementById('themecolor').content,
           boxes: { play: r('.playbtn'), tabs: r('.bottomtabs'), title: r('.hometitle-wrap'), hero: r('.cosmic-hero-wrap'), stage: r('#stage') },
           cs: [getComputedStyle(de).overflow, getComputedStyle(b).overflow, getComputedStyle(b).paddingTop, getComputedStyle(document.getElementById('stage')).position] }; }"""
HIT = "()=>{ const e = document.elementFromPoint(Math.round(innerWidth/2), 4); return e ? (e.id || e.className || e.tagName) : null; }"
def diff_boxes(a, b, tol=1):
    out = []
    for k in a:
        if (a[k] is None) != (b[k] is None): out.append(k); continue
        if a[k] and any(abs(x - y) > tol for x, y in zip(a[k], b[k])): out.append(k)
    return out
def hexof(c):
    if re.match(r"^#[0-9a-fA-F]{6}$", c or ""): return c.lower()
    m = re.findall(r"[\d.]+", c or "")
    return "#%02x%02x%02x" % tuple(int(float(x)) for x in m[:3]) if len(m) >= 3 else None
def click_trial(pg, tid):
    pg.evaluate("(t)=>document.querySelector('#diagpanel [data-trial=\"'+t+'\"]').click()", tid)
    pg.wait_for_timeout(120)
errs = []
with sync_playwright() as pw:
    br = pw.chromium.launch()
    # ---------------- (1) nothing without the flag ----------------
    ctx, pg = boot(br, flag=False)
    pg.on("pageerror", lambda e: errs.append(str(e)[:140]))
    n = pg.evaluate("()=>({ panel: !!document.getElementById('diagpanel'), hook: typeof window.__diagTrials, dx: document.querySelectorAll('[id^=dx-]').length, diag: document.querySelectorAll('[id^=diag-]').length })")
    chk("(1) without the flag: no panel, no trials, no trial styles (%s)" % n, not n["panel"] and n["hook"] == "undefined" and n["dx"] == 0 and n["diag"] == 0, n)
    pg.evaluate("()=>showAdvancedSettings()"); pg.wait_for_timeout(500)
    btn = pg.evaluate("()=>{ const b = document.querySelector('.settings-adv-diag button, .settings-adv-diag [role=button], .settings-adv-diag .settings-row'); return b ? b.textContent.trim() : null; }")
    chk("(1) Settings > Advanced > Troubleshooting offers the panel (%s)" % btn, bool(btn) and re.search(r"display test", btn, re.I), btn)
    if btn:
        with pg.expect_navigation(timeout=15000):
            pg.evaluate("()=>{ (document.querySelector('.settings-adv-diag button, .settings-adv-diag [role=button], .settings-adv-diag .settings-row')).click(); }")
        pg.wait_for_timeout(3000); pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); }")
        flag = pg.evaluate("()=>[localStorage.getItem('class26e.displaytest'), !!document.getElementById('diagpanel')]")
        chk("(1) tapping it sets the flag and the panel is up after the reload (%s)" % flag, flag == ["1", True], flag)
    ctx.close()
    # ---------------- (2) the panel and its candidates ----------------
    ctx, pg = boot(br)
    pg.on("pageerror", lambda e: errs.append(str(e)[:140]))
    base = pg.evaluate(STATE)
    ACC0 = pg.evaluate("()=>theme.accent"); ALT = "veteran" if ACC0 != "veteran" else "ink"
    ids = pg.evaluate("()=>[...document.querySelectorAll('#diagpanel [data-trial]')].map(b => b.dataset.trial)")
    chk("(2) the panel has trials (%d)" % len(ids), len(ids) >= 20, ids)
    off = pg.evaluate("()=>[...document.querySelectorAll('#diagpanel [data-trial]')].every(b => b.getAttribute('aria-checked') === 'false') && document.querySelectorAll('style[id^=dx-]').length === 0 && !document.getElementById('dx-strip')")
    chk("(2) every trial is OFF at load, none has put anything in the page", off)
    sw = pg.evaluate("()=>[...document.querySelectorAll('#diagpanel [data-trial]')].map(b => (b.textContent || '').trim().length)")
    chk("(2) each trial carries a one-line label", all(0 < x <= 140 for x in sw), sw)
    chk("(2) a big All off button and a 'what is on' line", pg.evaluate("()=>{ const f = [...document.querySelectorAll('#diagpanel button')].find(b => /^all off$/i.test(b.textContent.trim())); return !!f && f.getBoundingClientRect().height >= 44 && /nothing/i.test(document.querySelector('#diagpanel').textContent); }"))
    box = pg.evaluate("()=>{ const r = document.getElementById('diagpanel').getBoundingClientRect(); return [r.top, r.bottom, r.width, innerWidth, innerHeight]; }")
    chk("(2) the panel starts below the top 120px and inside the screen (%s)" % box, box[0] >= 120 and box[1] <= box[4] and box[2] <= box[3] * 0.8, box)
    want = {"strip": 7, "vfit": 1, "tc": 3, "cs": 2, "scroll": 2, "low": 2, "still": 2}
    groups = {"strip": [i for i in ids if re.match(r"s\d", i)], "vfit": [i for i in ids if i == "vfit"], "tc": [i for i in ids if i.startswith("tc")],
              "cs": [i for i in ids if i.startswith("cs")], "scroll": [i for i in ids if i in ("inner", "fixb")], "low": [i for i in ids if i.startswith("lo")],
              "still": [i for i in ids if i in ("gin", "ftc", "fcs")]}
    chk("(2) the candidates are all there (%s)" % {k: len(v) for k, v in groups.items()}, all(len(groups[k]) >= v for k, v in want.items()), groups)
    # ---------------- (3) each trial does its one thing and puts it back ----------------
    STRIP = {"s1": (1, "sky", "fixed"), "s8": (8, "sky", "fixed"), "s12": (12, "sky", "fixed"), "s24": (24, "sky", "fixed"), "s12st": (12, "sky", "sticky"),
             "s12k": (12, "#000000", "fixed"), "s12t": (12, "transparent", "fixed"), "s12b": (12, "transparent", "fixed")}
    STRIPREAD = """()=>{ const d = document.getElementById('dx-strip'); if(!d) return null; const cs = getComputedStyle(d), r = d.getBoundingClientRect(); const g = document.getElementById('top-guard');
        return { h: r.height, top: r.top, w: r.width, pos: cs.position, pe: cs.pointerEvents, bg: cs.backgroundColor, bdf: cs.backdropFilter || cs.webkitBackdropFilter, vw: innerWidth, guard: g ? getComputedStyle(g).display : 'none', count: document.querySelectorAll('#dx-strip').length, hit: (document.elementFromPoint(Math.round(innerWidth/2), 4) || {}).id }; }"""
    problems = []
    for tid in ids:
        click_trial(pg, tid)
        on = pg.evaluate("(t)=>document.querySelector('#diagpanel [data-trial=\"'+t+'\"]').getAttribute('aria-checked')", tid)
        st = pg.evaluate(STATE); moved = diff_boxes(base["boxes"], st["boxes"])
        why = []
        if on != "true": why.append("not on")
        if tid in STRIP:
            h, bg, pos = STRIP[tid]; r = pg.evaluate(STRIPREAD)
            if not r: why.append("no strip")
            else:
                if abs(r["h"] - h) > 0.5 or r["top"] != 0 or abs(r["w"] - r["vw"]) > 1 or r["pos"] != pos or r["pe"] != "auto" or r["count"] != 1: why.append(("shape", r))
                if bg == "sky" and hexof(r["bg"]) != hexof(st["tc"]): why.append(("colour", r["bg"], st["tc"]))
                if bg == "#000000" and hexof(r["bg"]) != "#000000": why.append(("colour", r["bg"]))
                if bg == "transparent" and not re.search(r"rgba\(0, 0, 0, 0\)|transparent", r["bg"]): why.append(("colour", r["bg"]))
                if tid == "s12b" and (not r["bdf"] or r["bdf"] == "none"): why.append(("no blur", r["bdf"]))
                if r["guard"] != "none": why.append(("today's strip still shown", r["guard"]))
                if h > 4 and r["hit"] != "dx-strip": why.append(("not what is 4px down", r["hit"]))
            if moved: why.append(("moved", moved))
        elif tid == "vfit":
            v = pg.evaluate("()=>document.getElementById('viewportmeta').content")
            if "viewport-fit" in v or "width=device-width" not in v: why.append(v)
            if moved: why.append(("moved", moved))
        elif tid in ("tcb", "tcw", "tcc"):
            v = pg.evaluate("()=>document.getElementById('themecolor').content"); exp = {"tcb": "#000000", "tcw": "#FFFFFF", "tcc": "transparent"}[tid]
            pg.evaluate("()=>{ theme.accent = '%s'; applyTheme(); }" % ALT); pg.wait_for_timeout(300)
            v2 = pg.evaluate("()=>document.getElementById('themecolor').content")
            if v != exp or v2 != exp: why.append(("theme-color", v, v2))
            pg.evaluate("()=>{ theme.accent = '%s'; applyTheme(); }" % ACC0)
            if moved: why.append(("moved", moved))
        elif tid == "tcm":
            m = pg.evaluate("()=>[...document.querySelectorAll('meta[name=theme-color][media]')].map(e => e.media)")
            if len(m) != 2 or not all("prefers-color-scheme" in x for x in m): why.append(m)
        elif tid in ("csl", "csb"):
            c = pg.evaluate("()=>[document.getElementById('colorscheme').content, getComputedStyle(document.documentElement).colorScheme]")
            if c[0] != {"csl": "light", "csb": "light dark"}[tid] or c[1] != c[0]: why.append(c)
        elif tid == "csn":
            if pg.evaluate("()=>!!document.getElementById('colorscheme')"): why.append("tag still there")
        elif tid == "ftc":
            before = pg.evaluate("()=>document.getElementById('themecolor').content")
            pg.evaluate("()=>{ theme.accent = '%s'; applyTheme(); }" % ALT); pg.wait_for_timeout(300)
            after = pg.evaluate("()=>document.getElementById('themecolor').content")
            pg.evaluate("()=>{ theme.accent = '%s'; applyTheme(); }" % ACC0)
            if before != after: why.append(("tag was rewritten", before, after))
        elif tid == "fcs":
            pg.evaluate("()=>{ document.documentElement.style.colorScheme = 'light'; }")
            if pg.evaluate("()=>document.documentElement.style.colorScheme") == "light": why.append("write went through")
        elif tid == "gin":
            pg.evaluate("()=>{ window.__g0 = document.getElementById('top-guard'); theme.accent = '%s'; applyTheme(); }" % ALT); pg.wait_for_timeout(500)
            r = pg.evaluate("()=>{ const g = document.getElementById('top-guard'); return g ? { same: g === window.__g0, c: g.dataset.color, tc: document.getElementById('themecolor').content, n: document.querySelectorAll('#top-guard').length } : null; }")
            pg.evaluate("()=>{ theme.accent = '%s'; applyTheme(); }" % ACC0)
            if not r or not r["same"] or r["n"] != 1 or r["c"].lower() != r["tc"].lower(): why.append(r)
        elif tid in ("inner", "fixb"):
            c = pg.evaluate("()=>({ html: getComputedStyle(document.documentElement).overflow, body: getComputedStyle(document.body).overflow, stage: getComputedStyle(document.querySelector('body > .wrap')).position, stageOv: getComputedStyle(document.querySelector('body > .wrap')).overflowY, bodyPos: getComputedStyle(document.body).position, sw: document.documentElement.scrollWidth, iw: innerWidth })")
            if c["html"] != "hidden" or c["sw"] > c["iw"] + 1: why.append(c)
            if tid == "inner" and (c["stage"] != "fixed" or c["stageOv"] != "auto" or c["body"] != "hidden"): why.append(c)
            if tid == "fixb" and (c["bodyPos"] != "fixed" or c["body"] != "auto"): why.append(c)
            if moved: why.append(("moved", moved))
        elif tid == "ovs":
            c = pg.evaluate("()=>[getComputedStyle(document.documentElement).overscrollBehaviorY, getComputedStyle(document.body).overscrollBehaviorY, getComputedStyle(document.documentElement).scrollBehavior]")
            if c[0] != "none" or c[1] != "none" or c[2] != "auto": why.append(c)
            if moved: why.append(("moved", moved))
        elif tid.startswith("lo"):
            pt = pg.evaluate("()=>getComputedStyle(document.body).paddingTop")
            exp = {"lo24": "24px", "lo40": "40px", "loin": "59px"}[tid]
            if pt != exp: why.append(("padding", pt))
            if not moved: why.append("content did not move")
        else:
            why.append("no check for this trial")
        click_trial(pg, tid)
        back = pg.evaluate(STATE)
        for k in ("metas", "htmlStyle", "bodyStyle", "kids", "styles", "dx", "strip", "guard", "cs"):
            if back[k] != base[k]: why.append(("not restored", k, str(base[k]), str(back[k])))
        if diff_boxes(base["boxes"], back["boxes"]): why.append(("boxes not restored", diff_boxes(base["boxes"], back["boxes"])))
        if why: problems.append((tid, why))
    chk("(3) every trial: on does the intended thing, off restores the page exactly (%d trials, %d with problems)" % (len(ids), len(problems)), not problems and len(ids) >= 20, problems[:6])
    # ---------------- (4) radio groups; today's strip comes back ----------------
    click_trial(pg, "s8"); click_trial(pg, "s24")
    r = pg.evaluate(STRIPREAD)
    chk("(4) two strips are never up at once: switching to 24px leaves one, 24px (%s)" % (r and r["h"]), r and r["count"] == 1 and r["h"] == 24)
    click_trial(pg, "s24")
    g = pg.evaluate("()=>{ const g = document.getElementById('top-guard'); return g ? getComputedStyle(g).display : null; }")
    chk("(4) with the trial off, today's strip is shown again (%s)" % g, g == "block")
    # ---------------- (5) the point WebKit samples ----------------
    click_trial(pg, "s12")
    hit = pg.evaluate(HIT)
    chk("(5) with a 12px trial up, the element 4px down in the middle is the trial strip (%s)" % hit, hit == "dx-strip")
    click_trial(pg, "s12")
    hit0 = pg.evaluate(HIT)
    print("INFO today's strip: the element 4px down in the middle is '%s' (not top-guard: it takes no touch, so a hit test goes through it)" % hit0)
    # ---------------- (6) All off, and the auto test's end ----------------
    for t in ("s12", "tcb", "csl", "gin", "inner", "lo24", "ovs", "vfit"): click_trial(pg, t)
    pg.evaluate("()=>{ document.querySelectorAll('#diagpanel input[type=checkbox]').forEach((c, i) => { if(i < 3){ c.checked = true; c.dispatchEvent(new Event('change')); } }); }")
    mid = pg.evaluate("()=>document.getElementById('diagpanel').textContent.match(/On now: [^A-Z]*/)[0]")
    chk("(6) the 'what is on' line names what is on (%s)" % mid, all(t in mid for t in ("s12", "tcb", "csl", "gin", "inner", "lo24", "ovs", "vfit", "blur")), mid)
    pg.evaluate("()=>[...document.querySelectorAll('#diagpanel button')].find(b => /^all off$/i.test(b.textContent.trim())).click()"); pg.wait_for_timeout(300)
    back = pg.evaluate(STATE)
    bad = [k for k in ("metas", "htmlStyle", "bodyStyle", "kids", "styles", "dx", "strip", "guard", "cs", "tc") if back[k] != base[k]]
    chk("(6) All off puts the page back exactly (%s)" % bad, not bad and not diff_boxes(base["boxes"], back["boxes"]), [bad, diff_boxes(base["boxes"], back["boxes"])])
    chk("(6) ...and every switch reads off, 'On now: nothing'", pg.evaluate("()=>[...document.querySelectorAll('#diagpanel [data-trial]')].every(b => b.getAttribute('aria-checked') === 'false') && [...document.querySelectorAll('#diagpanel input[type=checkbox]')].every(c => !c.checked) && /On now: nothing/.test(document.getElementById('diagpanel').textContent)"))
    # ---------------- (7) move, clamp, readout, notch ----------------
    pg.mouse.move(300, 160); hb = pg.evaluate("()=>{ const r = document.querySelector('#diagpanel div').getBoundingClientRect(); return [r.left + 20, r.top + 12]; }")
    pg.mouse.move(*hb); pg.mouse.down(); pg.mouse.move(120, 20, steps=6); pg.mouse.up(); pg.wait_for_timeout(150)
    top = pg.evaluate("()=>document.getElementById('diagpanel').getBoundingClientRect().top")
    chk("(7) dragged to the top of the screen, the panel stops at 120px (%s)" % top, abs(top - 120) < 1.5, top)
    hb = pg.evaluate("()=>{ const r = document.querySelector('#diagpanel div').getBoundingClientRect(); return [r.left + 20, r.top + 12]; }")
    pg.mouse.move(*hb); pg.mouse.down(); pg.mouse.move(100, 420, steps=6); pg.mouse.up(); pg.wait_for_timeout(150)
    box2 = pg.evaluate("()=>{ const r = document.getElementById('diagpanel').getBoundingClientRect(); return [r.left, r.top, r.bottom]; }")
    chk("(7) dragged lower, it follows (%s)" % box2, 330 < box2[1] < 470 and box2[2] <= 956, box2)
    pg.evaluate("()=>window.__diagTrials.toggle('s12', true)")
    rd = pg.evaluate("()=>window.__diagTrials.readout()")
    need = ["installed", "window", "screen", "safe area top", "100vh", "lvh", "status bar style tag", "viewport:", "theme-color", "4px down", "today's strip", "trial strip", "scrolls"]
    chk("(7) the readout has the geometry (%s lines)" % len(rd.splitlines()), all(k in rd for k in need), [k for k in need if k not in rd])
    chk("(7) the notch is simulated (safe area top 59px) and the trial strip is read (%s)" % rd.splitlines()[3], "top 59px" in rd and "trial strip: 440x12" in rd, rd)
    pg.evaluate("()=>window.__diagTrials.toggle('s12', false)")
    # the auto test still ends clean and names nothing of the trials
    pg.evaluate("()=>window.__diagTrials.toggle('lo24', true)")
    ctx.close()
    # ---------------- (7b) a trial can be kept for the next launch, and All off forgets it ----------------
    ctx, pg = boot(br)
    pg.on("pageerror", lambda e: errs.append(str(e)[:140]))
    click_trial(pg, "s12"); click_trial(pg, "gin")
    pg.evaluate("()=>[...document.querySelectorAll('#diagpanel button')].find(b => /keep what is on/i.test(b.textContent)).click()")
    pg.reload(); pg.wait_for_timeout(3000); pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); }")
    r = pg.evaluate("()=>({ on: window.__diagTrials.onNames(), strip: !!document.getElementById('dx-strip'), stored: localStorage.getItem('class26e.dxboot') })")
    chk("(7b) kept trials are on again after a relaunch (%s)" % r, r["on"] == ["s12", "gin"] and r["strip"], r)
    pg.evaluate("()=>[...document.querySelectorAll('#diagpanel button')].find(b => /^all off$/i.test(b.textContent.trim())).click()")
    pg.reload(); pg.wait_for_timeout(3000); pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); }")
    r = pg.evaluate("()=>({ on: window.__diagTrials.onNames(), strip: !!document.getElementById('dx-strip'), stored: localStorage.getItem('class26e.dxboot') })")
    chk("(7b) after All off a relaunch starts with nothing (%s)" % r, r["on"] == [] and not r["strip"] and r["stored"] is None, r)
    pg.evaluate("()=>{ localStorage.setItem('class26e.dxboot', JSON.stringify(['s12'])); }")
    pg.evaluate("()=>showAdvancedSettings()"); pg.wait_for_timeout(500)
    with pg.expect_navigation(timeout=15000):
        pg.evaluate("()=>{ document.querySelector('.settings-adv-diag button, .settings-adv-diag [role=button], .settings-adv-diag .settings-row').click(); }")
    pg.wait_for_timeout(2500)
    r = pg.evaluate("()=>[localStorage.getItem('class26e.dxboot'), localStorage.getItem('class26e.displaytest')]")
    chk("(7b) hiding the panel from Settings forgets what was kept (%s)" % r, r[0] is None, r)
    ctx.close()
    # ---------------- (8) ?sbs ----------------
    for q, exp in (("?sbs=default", "default"), ("?sbs=black", "black"), ("?sbs=nonsense", "black-translucent"), ("", "black-translucent")):
        ctx, pg = boot(br, flag=False, url=cb.URL + q)
        v = pg.evaluate("()=>document.querySelector('meta[name=apple-mobile-web-app-status-bar-style]').content")
        chk("(8) the address '%s' leaves the status bar style tag at '%s' (%s)" % (q, exp, v), v == exp, v)
        ctx.close()
    chk("(8) no page errors", not errs, errs)
    br.close()
print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
