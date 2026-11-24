"""Screenshots for 384.132 (unlocks3): the worn rim on Profile and on the person card (your own, and classmates' only when their
row's code holds the rim), your own Leaderboard row before and after taking the rim off (no write in between), and the fixed rim
cards. iPhone 17 Pro Max 440x956 and iPad Pro 11" 834x1194, both classes. Made-up classmates; the harness is
check-b384-unlocks.py's (an in-memory Firestore).

"profile-rims" is a sheet of Profile's hero with EVERY rim of the class worn in turn. The fixture holds only the Answers rim, so
for that sheet alone this device's own tier code is stood in with one that holds every tier (unlockRowFieldsSafe, the source the
plate reads); every other shot is the fixture as it is.

  python3 tools/shoot-b384-unlocks3.py OUTDIR [--src index.html] [--only academy|ifc] [--dev pm|ipad]"""
import io, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
G = os.path.join(HERE, "check-b384-unlocks.py")
sys_argv = sys.argv[:]
sys.argv = [G]
h = {"__file__": G, "__name__": "shoot"}
exec(open(G).read().split("\n# ---- the gate ----")[0], h)
sys.argv = sys_argv
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw

OUT = sys.argv[1]
def arg(n): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else None
SRC = arg("--src") or os.path.join(h["ROOT"], "index.html")
ONLY = arg("--only"); DEV = arg("--dev")
os.makedirs(OUT, exist_ok=True)
text = open(SRC, encoding="utf-8").read()
fx = h["fixtures"]()
CLOSE = "()=>document.querySelectorAll('.invite-overlay').forEach(o => o.remove())"

def open_row(pg, name):
    return pg.evaluate("""(n)=>{ const r = [...document.querySelectorAll('.screen-rankings .rank-row')].find(x => (x.querySelector('.rank-name') || {}).textContent === n);
        if(!r) return false; r.click(); return true; }""", name)

def own_row_into_view(pg):
    return pg.evaluate("""()=>{ const r = document.querySelector('.screen-rankings .rank-row:is(.lb-row-me, [data-me="1"])'); if(!r) return null;
        r.classList.remove('is-offscreen'); window.scrollTo(0, r.getBoundingClientRect().top + scrollY - innerHeight / 2); return true; }""")

with sync_playwright() as p:
    br = p.chromium.launch(executable_path=h["g"]["CHROME"], args=["--no-sandbox"])
    for cls in ("academy", "ifc"):
        if ONLY and ONLY != cls: continue
        for dev, w, hh in (("pm", 440, 956), ("ipad", 834, 1194)):
            if DEV and DEV != dev: continue
            seed, init = fx["rich_" + cls]
            ctx, pg, errs = h["page"](br, text, seed, init, w=w, h=hh, scale=2)
            pg.wait_for_timeout(1500)
            h["quiet"](pg); h["load_board"](pg); h["quiet"](pg)
            pre = os.path.join(OUT, "%s-%s-" % (cls, dev))
            # 1. Profile, wearing the Answers rim (held by the fixture)
            pg.evaluate(CLOSE); pg.evaluate("()=>{ showProfile('profile'); window.scrollTo(0, 0); }"); pg.wait_for_timeout(1800)
            pg.screenshot(path=pre + "1-profile-ans.png")
            # 2. the person card: your own, then classmates (Kimber: Accuracy rim held; Alexis: Mastery; Tomas: a rim his code does not hold)
            pg.evaluate("()=>showRankings()"); pg.wait_for_timeout(3000)
            pg.evaluate("()=>{ const r = document.querySelector('.screen-rankings .rank-row:is(.lb-row-me, [data-me=\"1\"])'); if(r) r.click(); }"); pg.wait_for_timeout(1500)
            pg.screenshot(path=pre + "2-card-own.png"); pg.evaluate(CLOSE)
            for i, nm in enumerate(("Kimber", "Alexis", "Tomas")):
                if open_row(pg, nm):
                    pg.wait_for_timeout(1500); pg.screenshot(path=pre + "3%s-card-%s.png" % ("abc"[i], nm.lower())); pg.evaluate(CLOSE)
            # 3. your own row: wearing the Answers rim, then taken off - with the account push held, so nothing is written in between
            pg.evaluate(CLOSE); pg.evaluate("()=>showRankings()"); pg.wait_for_timeout(2500)
            own_row_into_view(pg); pg.wait_for_timeout(900)
            pg.screenshot(path=pre + "4a-board-own-before.png")
            pg.evaluate("()=>{ window.__keepPush = scheduleCloudPush; window.scheduleCloudPush = () => {}; wearRim(''); showRankings(); }"); pg.wait_for_timeout(2000)
            own_row_into_view(pg); pg.wait_for_timeout(900)
            pg.screenshot(path=pre + "4b-board-own-after-takeoff.png")
            pg.evaluate("()=>{ wearRim('ans'); window.scheduleCloudPush = window.__keepPush; }")
            # 4. the rim cards: the Accuracy rim (its own count met, tier 1 not held), the Answers rim (held), Fire Code's Hundos rim
            for tag, rid in (("acc", "acc"), ("ans", "ans"), ("hun", "hun")):
                if rid == "hun" and cls != "ifc": continue
                pg.evaluate(CLOSE); pg.evaluate("(id)=>showUnlockDetail(rimDetail(id))", rid); pg.wait_for_timeout(1500)
                pg.screenshot(path=pre + "5-rimcard-%s.png" % tag)
            pg.evaluate(CLOSE)
            # 5. the sheet: Profile's hero with every rim worn in turn (the code stood in: see the docstring)
            ids = pg.evaluate("()=>unlockRimList(unlockTrackView()).map(r => r.id)")
            full = pg.evaluate("()=>'1-' + unlockTrackSpec().map(t => ('0' + ((1 << t.tiers.length) - 1).toString(16)).slice(-2)).join('') + '00'")
            tiles = []
            for rid in ids:
                pg.evaluate("([c, r])=>{ window.unlockRowFieldsSafe = () => ({ ut: c, rim: r }); showProfile('profile'); window.scrollTo(0, 0); }", [full, rid])
                pg.wait_for_timeout(1300)
                box = pg.evaluate("""()=>{ const a = document.querySelector('.profile-hero-avatar'), n = document.querySelector('.profile-hero .profile-name-display');
                    if(!a) return null; const r = a.getBoundingClientRect(), q = n ? n.getBoundingClientRect() : r;
                    return { x: r.left - 40, y: r.top - 40, w: r.width + 80, h: Math.max(r.bottom, q.bottom) - r.top + 60 }; }""")
                if not box: continue
                png = pg.screenshot(clip={"x": max(0, box["x"]), "y": max(0, box["y"]), "width": box["w"], "height": box["h"]})
                tiles.append((rid, Image.open(io.BytesIO(png)).convert("RGB")))
            if tiles:
                tw = max(t.width for _, t in tiles); th = max(t.height for _, t in tiles) + 40
                cols = 3 if dev == "pm" else 5
                rows_ = (len(tiles) + cols - 1) // cols
                sheet = Image.new("RGB", (tw * cols, th * rows_), (18, 20, 26))
                d = ImageDraw.Draw(sheet)
                for i, (rid, t) in enumerate(tiles):
                    x, y = (i % cols) * tw, (i // cols) * th
                    sheet.paste(t, (x, y + 40)); d.text((x + 12, y + 12), rid, fill=(235, 235, 235))
                sheet.save(pre + "6-profile-rims.png")
            print(cls, dev, "errors:", errs[:3], flush=True)
            ctx.close()
    br.close()
