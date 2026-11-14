"""Screenshots for 384.120 (unlocks): Customize's Next up, the Tracks screen (top and the rims), a rim's card with its rarity, and
the Leaderboard with banners along the edge and rims on the plates. iPhone 17 Pro Max 440x956 and iPad Pro 11" 834x1194, both
classes. Made-up classmates; the harness is check-b384-unlocks.py's (an in-memory Firestore).

  python3 tools/shoot-b384-unlocks.py OUTDIR [--src index.html] [--only academy|ifc] [--dev pm|ipad]"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
G = os.path.join(HERE, "check-b384-unlocks.py")
sys_argv = sys.argv[:]
sys.argv = [G]
h = {"__file__": G, "__name__": "shoot"}
exec(open(G).read().split("\n# ---- the gate ----")[0], h)
sys.argv = sys_argv
from playwright.sync_api import sync_playwright

OUT = sys.argv[1]
def arg(n): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else None
SRC = arg("--src") or os.path.join(h["ROOT"], "index.html")
ONLY = arg("--only"); DEV = arg("--dev")
os.makedirs(OUT, exist_ok=True)
text = open(SRC, encoding="utf-8").read()
fx = h["fixtures"]()

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
            pg.evaluate("()=>showCustomize()"); pg.wait_for_timeout(1800)
            pg.screenshot(path=pre + "1-customize.png")
            pg.evaluate("()=>showUnlockTracks()"); pg.wait_for_timeout(1800)
            pg.screenshot(path=pre + "2-tracks.png")
            pg.evaluate("()=>{ const c = document.querySelector('.trk-card[data-track=\"ans\"]'); if(c) window.scrollTo(0, c.getBoundingClientRect().top + scrollY - 90); }"); pg.wait_for_timeout(900)
            pg.screenshot(path=pre + "3-tracks-mid.png")
            pg.evaluate("()=>{ const c = document.querySelector('.cz-group-trk-rims'); if(c) window.scrollTo(0, c.getBoundingClientRect().top + scrollY - 260); }"); pg.wait_for_timeout(900)
            pg.screenshot(path=pre + "4-tracks-rims.png")
            pg.evaluate("()=>{ const r = document.querySelector('.trk-card[data-track=\"acc\"] .trk-tier[data-tier=\"3\"]'); if(r) r.click(); }"); pg.wait_for_timeout(1500)
            pg.screenshot(path=pre + "5-rim-card.png")
            pg.evaluate("()=>document.querySelectorAll('.invite-overlay').forEach(o => o.remove())")
            pg.evaluate("()=>showRankings()"); pg.wait_for_timeout(3500)
            pg.screenshot(path=pre + "6-leaderboard.png")
            print(cls, dev, "errors:", errs[:3], flush=True)
            ctx.close()
    br.close()
