#!/usr/bin/env python3
"""Build 384 r8: one row tile for the whole app - Delta's, the Settings menu's - and only the menu is coloured.

Madison, of Profile's Customize and Badge case rows: "These icons would need to be fixed too, wherever else they are on the app as
well." Then, of Stats' Test history: "Why is this purple? Shouldn't it just be grey?" And of Settings' pages: "when you click a
section and open it, there are icons within them? But there shouldn't be.."

On every screen it can reach, in BOTH classes (iPhone 17 Pro Max; Profile and Stats on the iPad Pro 11" as well), every visible row
tile (.settings-row-icon, [data-tile]) is read:
(1) the Settings menu keeps its tiles: every row tiled on cd34de2 (the reference build, loaded from git and measured in the same
    run) still has one, the same size, masked (on the tile or its layers) - (384.110) the mask itself is iOS's continuous corner now,
    so it is no longer cd34de2's string. (Their material and colours did
    change, on purpose, in 384 r8's Delta pass - check-b384-tilematerial holds those);
(2) every row tile OUTSIDE the menu is the menu's tile in shape: 27-29px, the menu's own superellipse mask (on the tile or on the
    ::before that carries its fill), the menu's sheen, the menu's glyph size and stroke;
(3) ...and one neutral grey: low chroma, and the same colour on every one of them (Profile's Customize / Badge case / Rank ladder,
    Stats' Test history - which was Settings' indigo);
(4) the pages Settings opens have no tile at all;
(5) the screens were really reached: 4+ tiles outside the menu in each class, 8+ menu tiles; no page errors.
Shape, not strings: the menu's mask, sheen, glyph and stroke are read off the menu on the page, never typed here.
  python3 tools/check-b384-rowtiles.py [--against OLD/index.html]   (must FAIL on cd34de2: 34px squares, a purple Test history)"""
import os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
import importlib.util
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
from playwright.sync_api import sync_playwright
REF = "cd34de2"
REF_BODY = cb.INSET_RE.sub(lambda m: "0px", subprocess.run(["git", "-C", cb.ROOT, "show", REF + ":index.html"], capture_output=True, check=True).stdout.decode("utf-8")) \
    .replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:900], flush=True)
IFC_SEED = cb.USED_ACCOUNT[:-1] + ',"publicId":"xph5b57jbp5a","novaMet":99}'
IFC_INIT = "try{localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.greet.ifc','done');}catch(e){}"
SCREENS = ["showHome()", "showProfile('profile')", "showProfile('stats')", "showStatsScreen()", "showCalendarTab()", "showFriends()", "showClassCatalog()",
           "showRankings()", "showLeaderboard()", "showVirtualRoomChoice()", "showRoomBrowser()", "showModeSelect()", "showSetup()", "showCustomize()",
           "showTestReviewList()", "showRanksScreen('badges')", "showRanksScreen('ranks')", "showBugReport()", "showReleaseHistory()",
           "showAppearance()", "showAppearance({page:'sound'})", "showAppearance({page:'study'})", "showAppearance({page:'motion'})",
           "showAppearance({page:'account'})", "showAppearance({page:'classes'})", "showAppearance({page:'sync'})", "showAppearance({page:'rankings'})",
           "showAppearance({page:'share'})", "showAdvancedSettings()", "showCredits()"]
TILES = r"""()=>{ const vis=e=>{ const b=e.getBoundingClientRect(); if(!b.width||!b.height) return false;
    for(let x=e; x && x.nodeType===1; x=x.parentElement){ const cs=getComputedStyle(x); if(cs.display==='none'||cs.visibility==='hidden'||parseFloat(cs.opacity)===0) return false; } return true; };
  const rgb=s=>{ const m=(s||'').match(/[\d.]+/g)||[]; const v=m.slice(0,3).map(Number); return /^color\(/.test(s||'') ? v.map(x=>Math.round(x*255)) : v; };
  const alpha=s=>{ const m=(s||'').match(/[\d.]+/g)||[]; return m.length>3 ? +m[3] : (m.length ? 1 : 0); };
  return [...document.querySelectorAll('#stage .settings-row-icon, #stage [data-tile]')].filter(vis).map(t=>{
    const cs=getComputedStyle(t), be=getComputedStyle(t,'::before'), af=getComputedStyle(t,'::after'), b=t.getBoundingClientRect();
    const on=p=>p.content!=='none' && p.content!=='normal';
    const own=cs.maskImage && cs.maskImage!=='none' ? cs.maskImage : (cs.webkitMaskImage && cs.webkitMaskImage!=='none' ? cs.webkitMaskImage : 'none');
    const pm=be.content!=='none' && be.content!=='normal' ? (be.maskImage && be.maskImage!=='none' ? be.maskImage : (be.webkitMaskImage||'none')) : 'none';
    /* the layer that carries the fill: the tile itself, or (384 r8, Delta's material) its ::after - the fill inside the rim that
       ::before paints - or its ::before, when the tile's own background is clear */
    const layer = alpha(cs.backgroundColor) > .5 ? cs : (on(af) && alpha(af.backgroundColor) > .5 ? af : (on(be) && alpha(be.backgroundColor) > .5 ? be : cs));
    const fill=rgb(layer.backgroundColor), svg=t.querySelector('svg'), ss=svg && getComputedStyle(svg);
    const row=t.closest('button, .settings-row, label, [role=button], .pf-act') || t.parentElement;
    return { name:((row.querySelector('.settings-row-label, .pf-act-label, .otext')||row).textContent||'').trim().slice(0,28), kind:t.dataset.tile||'',
      menu: !!t.closest('.screen-settings'), sub: !!t.closest('.screen-settings-sub'), w:Math.round(b.width*10)/10, h:Math.round(b.height*10)/10,
      mask: own!=='none' ? own : pm, fill, fillAlpha: alpha(layer.backgroundColor), chroma: fill.length ? Math.max(...fill)-Math.min(...fill) : 99,
      sheen: layer.backgroundImage, shadow: cs.boxShadow, glyph: svg ? Math.round(svg.getBoundingClientRect().width*10)/10 : 0, stroke: ss ? ss.strokeWidth : '',
      sig: [Math.round(b.width*10)/10, own!=='none' ? own : pm].join(' | ') }; }); }"""
def calm(pg):
    pg.evaluate("()=>{ try{ homeUnlocksOwed=()=>false; }catch(e){} }")
def sweep(br, cls, w, h, screens, body=None):
    saved = cb.BODY
    if body is not None: cb.BODY = body
    try:
        ctx, pg = cb.booted(br, w, h, seed=(IFC_SEED if cls == "ifc" else cb.USED_ACCOUNT), init=(IFC_INIT if cls == "ifc" else None))
    finally:
        cb.BODY = saved
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    calm(pg)
    got = {}
    if cls == "ifc" and pg.evaluate("()=>window.NOVA_CLASS") != "ifc":
        ctx.close(); return None, ["the page did not open in Fire Code"]
    for s in screens:
        pg.evaluate("()=>{ try{ %s }catch(e){ window.__shownErr=String(e); } }" % s); pg.wait_for_timeout(900)
        pg.evaluate("()=>document.querySelectorAll('#tour-overlay,#tour-tooltip,#tour-line,#tour-line-dot,.rs-spot').forEach(n=>n.remove())")
        got[s] = pg.evaluate(TILES)
    ctx.close()
    return got, errs
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    errs_all, bad1, bad2, bad3, bad4, counts = [], [], [], [], [], {}
    for cls in ("academy", "ifc"):
        ref, e0 = sweep(br, cls, 440, 956, ["showAppearance()"], body=REF_BODY)
        if ref is None: bad1.append((cls, "reference", e0)); continue
        refsig = {t["name"]: t["sig"] for t in ref["showAppearance()"] if t["menu"]}
        for (w, h, screens) in ((440, 956, SCREENS), (834, 1194, ["showAppearance()", "showProfile('profile')", "showProfile('stats')"])):
            got, errs = sweep(br, cls, w, h, screens)
            if got is None: bad2.append((cls, w, errs)); continue
            errs_all += errs
            menu = [t for t in got.get("showAppearance()", []) if t["menu"]]
            M = menu[0] if menu else None
            counts[(cls, w, "menu")] = len(menu)
            if w == 440:
                for t in menu:
                    # (384.110) the corner was re-fitted to iOS's continuous curve (Delta's tiles, mse .06px), so the mask is no longer
                    # cd34de2's string: the same SIZE as there, and a mask on the tile or its layers (check-b384-settingslook holds its curve)
                    ref = refsig.get(t["name"])
                    if not ref or ref.split(" | ")[0] != t["sig"].split(" | ")[0] or t["mask"] in ("", "none"): bad1.append((cls, t["name"], t["sig"][:140], (ref or "missing")[:140]))
                gone = [n for n in refsig if n not in set(t["name"] for t in menu)]
                if gone: bad1.append((cls, "rows that lost their tile", gone))
            outside, greys = [], set()
            for s, tiles in got.items():
                for t in tiles:
                    if t["menu"]: continue
                    if t["sub"]: bad4.append((cls, w, s, t["name"])); continue
                    outside.append(t)
                    why = []
                    if not (27 <= t["w"] <= 29 and abs(t["w"] - t["h"]) < .5): why.append("%sx%spx" % (t["w"], t["h"]))
                    if not M or t["mask"] != M["mask"]: why.append("not the menu's squircle mask (%s)" % t["mask"][:40])
                    if not M or t["sheen"] != M["sheen"]: why.append("not the menu's sheen (%s)" % t["sheen"][:60])
                    if not M or abs(t["glyph"] - M["glyph"]) > .5 or t["stroke"] != M["stroke"]: why.append("glyph %spx / %s, the menu's %s / %s" % (t["glyph"], t["stroke"], M and M["glyph"], M and M["stroke"]))
                    if why: bad2.append((cls, w, s, t["name"], why))
                    if t["chroma"] > 8 or t["fillAlpha"] < .5: bad3.append((cls, w, s, t["name"], t["fill"], "chroma %s" % t["chroma"]))
                    greys.add(tuple(t["fill"]))
            if len(greys) > 1: bad3.append((cls, w, "more than one grey", sorted(greys)))
            counts[(cls, w, "outside")] = len(outside)
            counts[(cls, w, "outside names")] = sorted(set(t["name"] for t in outside))
    br.close()
cb.SERVER.shutdown()
print("tiles read:", counts)
chk("(1) the Settings menu keeps every tile it had on %s, the same size, masked, in both classes" % REF, not bad1 and all(counts.get((c, 440, "menu"), 0) >= 8 for c in ("academy", "ifc")), bad1[:6])
chk("(2) every row tile outside the menu is the menu's tile: 27-29px, the menu's squircle mask, its sheen, its glyph and stroke", not bad2, bad2[:6])
chk("(3) ...and one neutral grey, the same on every one (no colour outside the menu)", not bad3, bad3[:6])
chk("(4) no tile on any page Settings opens", not bad4, bad4[:6])
chk("(5) the screens were reached (4+ row tiles outside the menu per class on the phone, 3+ on the tablet's Profile and Stats) and no page errors",
    all(counts.get((c, 440, "outside"), 0) >= 4 and counts.get((c, 834, "outside"), 0) >= 3 for c in ("academy", "ifc")) and not errs_all, [counts, errs_all[:3]])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
