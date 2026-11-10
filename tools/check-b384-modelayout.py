"""Build 384 r20: the mode screens fill their screens.
Madison, on Choose your mode (Fire Code's three) and the Virtual Room's Host / Join at his phone's 85% page zoom: "There's so much open space
on these screens, it doesn't look like that. In the academy there's a 4th mode ... so it looks better, however, on the phone not so much..
should we do them as a different looking boxes? Almost like the boxes you see when signing up for a class? ... each device size may need a
different layout and that's okay. Fix it though."
The title and the question stay at the top; the cards are tiles that take the room under them down to the tab bar. Read off the page, BOTH
classes (Fire Code three modes, the academy four, Host / Join two), on seven screens: iPhone SE 375x667, Pro Max 440x956, Pro Max at 85% page
zoom (518x1126 CSS px on a 440x956 screen), iPad Pro 11" upright 834x1194 and on its side 1194x834, a laptop 1366x768 and a desktop 1920x1080:
 (1) FILL - the card group's vertical extent against the free height between the question and the tab bar: a phone or a tablet held upright
     >= 85% (the tiles TAKE the room), a laptop / desktop / landscape tablet >= 50% (the tiles are capped, 30rem, so a desktop's are not
     posters - the group is then centred); never more than the room (a small phone that cannot fit scrolls, and then the last tile clears
     the tab bar once scrolled to the end);
 (2) PLACE - the gap under the question above the first tile and the gap from the last tile to the tab bar differ by <= 3px (the group is
     centred in its room; on a phone they are both the 18px glass gap, times the page zoom's --zc);
 (3) TILES - in a row every tile has the same top and height, a column's tiles the same width (an odd one across both columns of an upright
     tablet excepted); each >= 44px tall; every tile's words and mark inside it;
 (4) NOTHING OVERLAPS - no tile meets the tab bar or any fixed control, no sideways scroll, no page errors;
 (5) BUILD - stack: the mark, the name and the line share one left edge (+-1px); snug (three or four to a phone): the mark and the name
     centre on one line (+-1.5px), the line under them on the mark's left edge;
 (6) TAP - the tile's centre and four inner corners hit that tile (the mark, name and chevron are not separate targets); a real tap on each
     of Choose your mode's tiles sets the mode it names and leaves the screen;
 (7) the page zoom is exercised (html.page-zoomed at 518x1126) and nothing is zoomed to a size smaller than at 100%: the name's size on the
     glass (CSS px x screen / layout width) is within 1px of the 100% phone's.
Run:  python3 tools/check-b384-modelayout.py   (--against OLD/index.html must FAIL; --dump prints the numbers)"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b384_modelayout_lib as L
from playwright.sync_api import sync_playwright
ok = True
DUMP = "--dump" in sys.argv
ONLY = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:420], flush=True)
READ = """()=>{ document.querySelectorAll('.daily-alert,.app-banner').forEach(n=>n.remove()); const R=e=>e.getBoundingClientRect();
  const sub=document.querySelector('#stage .modeselect-sub, #stage .cal-sub'), cards=[...document.querySelectorAll('#stage .modecards > .modecard')];
  const tb=document.getElementById('bottomtabs'), tr=tb && !tb.hidden && tb.offsetHeight ? R(tb) : null, sr=R(sub);
  const fixed=[...document.body.children].filter(e=>{ if(e.id==='bottomtabs'||e.id==='splashscreen') return false; const s=getComputedStyle(e); if(s.position!=='fixed'||s.display==='none'||s.visibility==='hidden'||+s.opacity===0) return false;
      const r=R(e); return r.width>0&&r.height>0&&!(r.width>=innerWidth*.95&&r.height>=innerHeight*.9); }).map(e=>{ const r=R(e); return {id:e.id||e.className, t:r.top, b:r.bottom, l:r.left, r:r.right}; });
  const tiles=cards.map(c=>{ const r=R(c), ic=c.querySelector('.modeicon'), ti=c.querySelector('.modecardtitle'), de=c.querySelector('.modecarddesc');
    const i=R(ic), t=R(ti), d=R(de); const z=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--zc'))||1;
    const hit=[[.5,.5],[.04,.06],[.96,.06],[.04,.94],[.96,.94]].map(([fx,fy])=>{ const e=document.elementFromPoint(r.left+r.width*fx, r.top+r.height*fy); return !!e && e.closest('.modecard')===c; });
    return { mode:c.dataset.mode||((c.className.match(/vrc-card-(\\w+)/)||[])[1]), l:r.left, t:r.top, r:r.right, b:r.bottom, w:r.width, h:r.height,
      iL:i.left, iR:i.right, iCy:(i.top+i.bottom)/2, tL:t.left, tCy:(t.top+t.bottom)/2, tR:t.right, dL:d.left, dR:d.right, dB:d.bottom, tTop:t.top, iTop:i.top, hit, vis:(r.top>=0 && r.bottom<=(tr?tr.top:innerHeight)+.5), titlePx:parseFloat(getComputedStyle(ti).fontSize), z }; });
  return { sub:sr.bottom, tab:tr?tr.top:null, ih:innerHeight, iw:innerWidth, sh:document.documentElement.scrollHeight, sw:document.documentElement.scrollWidth,
    tile:(document.querySelector('#stage .modecards')||{dataset:{}}).dataset.tile, cols:(document.querySelector('#stage .modecards')||{dataset:{}}).dataset.cols,
    zoomed:document.documentElement.classList.contains('page-zoomed'), fixed, tiles }; }"""
def analyse(r, dev, scrolled=None):
    """the numbers the checks read, from one READ"""
    tl = r["tiles"]; tops = min(t["t"] for t in tl); bots = max(t["b"] for t in tl)
    tab = r["tab"] if r["tab"] is not None else r["ih"]
    free = tab - r["sub"]; fill = (bots - tops) / free if free > 0 else 0
    return dict(fill=fill, above=tops - r["sub"], below=tab - bots, tops=tops, bots=bots, tab=tab, free=free)
SEL = {"modes": "modes", "vroom": "vroom"}
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=L.CHROME)
    glass100 = None
    for dev in L.DEVICES:
        if ONLY and not any(o in dev for o in ONLY): continue
        W, H, SW, SH, ins, installed = L.DEVICES[dev]
        k = SW / W   # glass px per CSS px (0.85 at the owner's page zoom)
        phone = W * k < 640
        upright_tab = 640 <= W * k and not (W * k >= 900 and W > H * 1.1)
        for cls in ("ifc", "academy"):
            ctx, pg, errs = L.open_page(br, cls, dev)
            for scr in ("modes", "vroom"):
                tag = "%s %s %s" % (dev, cls, scr)
                L.show(pg, scr)
                r = pg.evaluate(READ)
                n = len(r["tiles"])
                a = analyse(r, dev)
                scrollable = r["sh"] > r["ih"] + 1
                if scrollable:
                    pg.evaluate("window.scrollTo({top:1e5, behavior:'instant'})"); pg.wait_for_timeout(300)
                    r2 = pg.evaluate(READ); a2 = analyse(r2, dev); pg.evaluate("window.scrollTo({top:0, behavior:'instant'})")
                else: r2, a2 = r, a
                if DUMP:
                    print(tag, "tiles=%d kind=%s cols=%s fill=%.2f above=%.1f below=%.1f tile h=%.0f w=%.0f scroll=%s sh=%d ih=%d" % (n, r["tile"], r["cols"], a["fill"], a["above"], a["below"], r["tiles"][0]["h"], r["tiles"][0]["w"], scrollable, r["sh"], r["ih"]), flush=True)
                want = {"modes": 3 if cls == "ifc" else 4, "vroom": 2}[scr]
                chk("%s: %d tiles" % (tag, n), n == want, n)
                # (1) fill
                if phone or upright_tab:
                    need = 0.85 if not (upright_tab and scr == "vroom") else 0.55
                else: need = 0.50
                if scrollable:
                    chk("(1) %s: a small phone that cannot fit scrolls, and the last tile clears the tab bar at the end (%.0f vs %.0f)" % (tag, a2["bots"], a2["tab"]), a2["bots"] <= a2["tab"] + 0.5, a2)
                else:
                    chk("(1) %s: the tiles fill %.0f%% of the room under the question (need %d%%, no more than 100%%)" % (tag, a["fill"] * 100, need * 100), need <= a["fill"] <= 1.005, a)
                    # (2) place
                    chk("(2) %s: centred in the room (%.1f above, %.1f below)" % (tag, a["above"], a["below"]), abs(a["above"] - a["below"]) <= 3 and a["above"] >= 10, a)
                # (3) tiles
                tl = r["tiles"]
                rowsd = {}
                for t in tl: rowsd.setdefault(round(t["t"]), []).append(t)
                eqrow = all(abs(x["h"] - g[0]["h"]) <= 1 and abs(x["t"] - g[0]["t"]) <= 1 for g in rowsd.values() for x in g)
                widths = {}
                for t in tl:
                    if t["w"] < r["iw"] * 0.9 or int(r["cols"] or 1) == 1: widths.setdefault(round(t["w"]), 0)
                chk("(3) %s: tiles in a row share a top and a height, tall enough (min %.0f)" % (tag, min(t["h"] for t in tl)), eqrow and min(t["h"] for t in tl) >= 44, [(t["t"], t["h"]) for t in tl])
                cols_n = int(r["cols"] or 1)
                if cols_n >= 2:
                    firstrow = [t for t in tl if abs(t["t"] - tl[0]["t"]) <= 1]
                    chk("(3) %s: the tiles of a row are one width (%s)" % (tag, [round(t["w"]) for t in firstrow]), len(firstrow) < 2 or max(t["w"] for t in firstrow) - min(t["w"] for t in firstrow) <= 1, firstrow)
                inside = all(t["iL"] >= t["l"] - 0.5 and t["tR"] <= t["r"] + 0.5 and t["dR"] <= t["r"] + 0.5 and t["dB"] <= t["b"] + 0.5 for t in tl)
                chk("(3) %s: every tile's mark, name and line are inside it" % tag, inside, tl[0])
                # (4) overlaps
                over = [f for f in r2["fixed"] if any(not (f["b"] <= t["t"] or f["t"] >= t["b"] or f["r"] <= t["l"] or f["l"] >= t["r"]) for t in r2["tiles"])]
                chk("(4) %s: no tile meets a fixed control (%s) and no sideways scroll (%d)" % (tag, [f["id"] for f in over] or "none", r["sw"] - r["iw"]), not over and r["sw"] <= r["iw"], (over, r["sw"], r["iw"]))
                # (5) the build
                if r["tile"] == "stack":
                    okb = all(abs(t["iL"] - t["tL"]) <= 1 and abs(t["iL"] - t["dL"]) <= 1 for t in tl)
                else:
                    okb = all(abs(t["iCy"] - t["tCy"]) <= 1.5 and abs(t["iL"] - t["dL"]) <= 1 and t["tL"] > t["iR"] for t in tl)
                chk("(5) %s: the %s build keeps its edges (%s)" % (tag, r["tile"], [round(t["iL"] - t["tL"], 1) for t in tl]), okb, tl[0])
                # (6) taps land on their tile
                hits = [(t["hit"] if t["vis"] or not t2["vis"] else t2["hit"]) for t, t2 in zip(tl, r2["tiles"])]
                chk("(6) %s: the centre and four inner corners of every tile hit that tile (read where the tile is on screen)" % tag, all(all(h) for h in hits), hits)
                if scr == "modes":
                    got = []
                    for i in range(n):
                        L.show(pg, "modes")
                        box = pg.evaluate("(i)=>{ const c=document.querySelectorAll('#stage .modecards > .modecard')[i]; c.scrollIntoView({block:'center', behavior:'instant'}); const r=c.getBoundingClientRect(); return {x:r.left+r.width/2, y:r.top+r.height/2, mode:c.dataset.mode}; }", i)
                        pg.mouse.click(box["x"], box["y"]); pg.wait_for_timeout(500)
                        got.append((box["mode"], pg.evaluate("()=>({ mode: cfg.mode, left: !document.querySelector('#stage .panel.modeselect') })")))
                    chk("(6) %s: a real tap on each tile sets its mode and leaves the screen (%s)" % (tag, [(m, g["mode"]) for m, g in got]), all(g["mode"] == m and g["left"] for m, g in got), got)
                    L.show(pg, "modes")
                if r["zoomed"] is not (dev == "promax-zoom-518x1126"):
                    chk("(7) %s: page-zoomed is %s" % (tag, "set" if dev == "promax-zoom-518x1126" else "not set"), False, r["zoomed"])
                if scr == "modes" and cls == "ifc" and dev in ("promax-440x956", "promax-zoom-518x1126"):
                    sz = r["tiles"][0]["titlePx"] * k
                    if dev == "promax-440x956": glass100 = sz
                    elif glass100 is not None: chk("(7) at the owner's page zoom the name is drawn as big as at 100%% (%.1f vs %.1f pt)" % (sz, glass100), abs(sz - glass100) <= 1, (sz, glass100))
            chk("%s %s: no page errors" % (dev, cls), not errs, errs[:2])
            ctx.close()
    br.close()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
