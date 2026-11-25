#!/usr/bin/env python3
"""384.153 (lbstill): EVERY LEADERBOARD CIRCLE SHOWS ITS CHARACTER FROM THE FIRST FRAME OF THE TAB.

Madison: "the characters within their circles aren't loading properly on the leaderboard sometimes when i go to the tab" / "right
when I click the tab, some of the characters within the circle don't load". A row whose recorded loop was ready was built with the
loop ALONE; the loop is a canvas a frame is copied into, and on an iPhone the sheet behind it is often not decoded as the tab opens
(only the 14 used most lately are kept decoded), so the canvas was blank until it was. Chromium decodes at once, so here the
sheets are made slow on purpose: each loop's image gets its source 900ms late, as a slow decode would.

On an installed Pro Max, Fire Code's board seeded with 30 classmates (varied characters): open the board and stay until at least 8
loops are recorded (as a phone does over its visits), relaunch, open the board, go Home, make the sheets slow, open the board again
and read the first screenful at 80, 200, 400, 800, 1500 and 3000ms:
 (1) NO EMPTY CIRCLE: at every sample every circle shows its character - a drawn loop frame, or a visible picture;
 (2) NO DOUBLE: at 3000ms a circle whose loop has drawn has no other picture visible in it (the still hides on the loop's first draw);
 (3) USED: >= 5 circles of the screenful are playing a loop at 3000ms (else (1) measured nothing);
 (4) no page errors.
Run:  TMPDIR=/dev/shm python3 tools/check-b384-lbstill.py [--against REV]      --against 384.152 must FAIL (1).
"""
import importlib.util, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("glitches", os.path.join(HERE, "check-b384-glitches.py"))
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)
from playwright.sync_api import sync_playwright

results = []
def chk(ok, msg):
    results.append(bool(ok)); print(("PASS " if ok else "FAIL ") + msg, flush=True)

SLOW = """()=>{ window.charFlipSrcOf = function(sp){ const im = new Image(); im.decoding = 'async'; setTimeout(() => { im.src = sp.url; }, 900); return im; }; }"""
READ = """()=>{ const vh = innerHeight;
  const ws = [...document.querySelectorAll('#stage .rank-avatar-wrap')].filter(w => { const r = w.getBoundingClientRect(); return r.width > 0 && r.bottom > 0 && r.top < vh - 90; });
  const vis = w => [...w.querySelectorAll('.rank-avatar svg')].filter(v => getComputedStyle(v).visibility !== 'hidden' && v.getBoundingClientRect().width > 4).length;
  const drawn = w => { const cv = w.querySelector('canvas.char-flip-cv'); return !!(cv && cv.__f >= 0); };
  return { n: ws.length, empty: ws.filter(w => !drawn(w) && !vis(w)).length, playing: ws.filter(drawn).length,
           double: ws.filter(w => drawn(w) && vis(w)).length }; }"""
TAB = """(name)=>{ const b = [...document.querySelectorAll('#bottomtabs button, #bottomtabs .bottomtab')].find(b => new RegExp(name).test(b.textContent)); b && b.click(); }"""

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G.CHROME)
    pg = G.open_dev(br, "promax", inits=[G.seed_init("ifc")], dsf=1)
    chars = pg.evaluate("()=>AVATAR_CHARACTERS.filter(c => !c.retired && c.id !== 'nova').map(c => c.id)")
    pg.ctx.close()
    rows = {}
    for i in range(30):
        rows["p%011d" % i] = {"firstName": "Mate%d" % i, "avatarChar": chars[(i * 7) % len(chars)], "accent": "ink", "banner": "",
                              "badges": i % 9, "hundos": i % 13, "correct": 400 - i * 9, "level": 30 - i // 2, "rankFloor": 0,
                              "xp": 12000 - i * 350, "tests": 20, "lastModified": 1795000000000}
    cloud = {"vrooms": {"lb-ifc-v1": {"kind": "board", "cls": "ifc", "rows": rows}}}
    pg = G.open_dev(br, "promax", inits=[G.seed_init("ifc"), "try{localStorage.setItem('class26e.intro.seen','99');}catch(e){}"], dsf=1, cloud=cloud)
    pg.evaluate("()=>{ try{ theme.muteBanners = true; }catch(e){} }"); G.clear_popups(pg)
    pg.evaluate(TAB, "Leaderboard")
    n = 0
    for _ in range(14):
        pg.wait_for_timeout(5000)
        n = pg.evaluate("()=>charAnimReady.size")
        if n >= 8: break
    print("INFO loops recorded on the first visit: %d" % n, flush=True)
    pg.evaluate(TAB, "Home"); pg.wait_for_timeout(1500)
    pg.reload(); pg.wait_for_timeout(6000)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); try{ theme.muteBanners = true; }catch(e){} }"); G.clear_popups(pg)
    pg.evaluate(TAB, "Leaderboard"); pg.wait_for_timeout(1500)
    pg.evaluate(TAB, "Home"); pg.wait_for_timeout(1500)
    pg.evaluate(SLOW)
    pg.evaluate(TAB, "Leaderboard")
    seen = []; t0 = 0
    for t in (80, 200, 400, 800, 1500, 3000):
        pg.wait_for_timeout(t - t0); t0 = t
        seen.append((t, pg.evaluate(READ)))
    worst = max(seen, key=lambda x: x[1]["empty"])
    chk(all(r["empty"] == 0 for _, r in seen) and all(r["n"] >= 6 for _, r in seen),
        "(1) NO EMPTY CIRCLE: empty circles per sample %s (worst %d of %d at %dms)" % (
            " ".join("%dms:%d" % (t, r["empty"]) for t, r in seen), worst[1]["empty"], worst[1]["n"], worst[0]))
    last = seen[-1][1]
    chk(last["double"] == 0, "(2) NO DOUBLE: at 3000ms %d circles show a picture under their playing loop" % last["double"])
    chk(last["playing"] >= 5, "(3) USED: %d of %d circles are playing a loop at 3000ms" % (last["playing"], last["n"]))
    chk(not pg.errs, "(4) no page errors %s" % pg.errs[:2])
    pg.ctx.close(); br.close()
bad = results.count(False)
print("\n%d checks, %d failed" % (len(results), bad))
print("ALL PASS" if not bad else "FAILED")
sys.exit(1 if bad else 0)
