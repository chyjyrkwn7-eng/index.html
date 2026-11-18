"""Screenshots for 384.136 (unlocks2): every screen where unlockables and their challenges are browsed, before and after the
redesign. iPhone 17 Pro Max 440x956 @3x and iPad Pro 11" 834x1194 @2x, both classes. Made-up classmates and the rich fixture of
check-b384-unlocks.py (an in-memory Firestore).

  python3 tools/shoot-b384-unlocks2.py OUTDIR [--src index.html] [--only academy|ifc] [--dev pm|ipad] [--zoom 85|135]

The step list works on both builds: a step whose screen does not exist on the build being shot is skipped (it prints "skip")."""
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
ONLY = arg("--only"); DEV = arg("--dev"); ZOOM = arg("--zoom")
os.makedirs(OUT, exist_ok=True)
text = open(SRC, encoding="utf-8").read()
fx = h["fixtures"]()

CLOSE = "document.querySelectorAll('.invite-overlay').forEach(o => o.remove())"
TOP = "window.scrollTo(0, 0)"
def scroll_to(sel, off=90):
    return "return (()=>{ const c = document.querySelector(%s); if(!c) return false; window.scrollTo(0, c.getBoundingClientRect().top + scrollY - %d); return true; })()" % (json.dumps(sel), off)
def has(fn): return "typeof %s === 'function'" % fn

# (name, js that returns false to skip, wait ms)
STEPS = [
    ("01-customize", CLOSE + "; showCustomize(); " + TOP + "; return true;", 1800),
    ("02-customize-look", scroll_to(".cz-list", 120), 900),
    ("03-character-page", CLOSE + "; showCustomize('character'); return true;", 2200),
    ("04-character-page-challenges", scroll_to(".cz-group-chars-2", 90), 1200),
    ("05-banner-page", CLOSE + "; showCustomize('banner'); return true;", 2400),
    ("06-banner-page-challenges", scroll_to(".cz-group-banner-challenge", 90), 1500),
    ("07-theme-page", CLOSE + "; showCustomize('theme'); return true;", 1500),
    ("08-fx-page", CLOSE + "; showCustomize('fx'); return true;", 1800),
    ("10-unlocks-top", CLOSE + "; showUnlockTracks(); " + TOP + "; return true;", 2200),
    ("11-unlocks-tracks-mid", scroll_to('.trk-card[data-track="ans"]'), 1200),
    ("12-unlocks-feats", scroll_to(".cz-group-trk-feats", 120), 1200),
    ("13-unlocks-rims", scroll_to(".cz-group-trk-rims", 200), 1200),
    # the redesign's type filters (absent before)
    ("14-unlocks-characters", "return (()=>{ const b = document.querySelector('.ulk-chip[data-filter=\"char\"]'); if(!b) return false; " + TOP + "; b.click(); return true; })()", 2200),
    ("15-unlocks-characters-scrolled", "return (()=>{ if(!document.querySelector('.ulk-chip[data-filter=\"char\"].is-on')) return false; window.scrollTo(0, 900); return true; })()", 1500),
    ("16-unlocks-banners", "return (()=>{ const b = document.querySelector('.ulk-chip[data-filter=\"banner\"]'); if(!b) return false; b.click(); " + TOP + "; return true; })()", 2400),
    ("17-unlocks-themes", "return (()=>{ const b = document.querySelector('.ulk-chip[data-filter=\"theme\"]'); if(!b) return false; b.click(); " + TOP + "; return true; })()", 1600),
    ("18-unlocks-effects", "return (()=>{ const b = document.querySelector('.ulk-chip[data-filter=\"fx\"]'); if(!b) return false; b.click(); " + TOP + "; return true; })()", 1800),
    ("19-unlocks-rims-filter", "return (()=>{ const b = document.querySelector('.ulk-chip[data-filter=\"rim\"]'); if(!b) return false; b.click(); " + TOP + "; return true; })()", 1500),
    # the cards an item opens
    ("20-card-locked-character", CLOSE + "; return (()=>{ const id = (AVATAR_CHARACTERS.find(c => c.feat && !c.secret && !c.retired && isLockedCharacter(c.id)) || {}).id; if(!id) return false; showUnlockDetail(characterDetail(id)); return true; })()", 2000),
    ("21-card-locked-banner", CLOSE + "; return (()=>{ const d = BANNERS.find(b => !b.rank && !b.flareChar && !bannerEarned(b.id) && b.have() > 0); if(!d) return false; showUnlockDetail(bannerDetail(d.id)); return true; })()", 2200),
    ("22-card-locked-theme", CLOSE + "; return (()=>{ const a = ACCENTS.find(n => isLockedAccent(n)); if(!a) return false; showUnlockDetail(themeDetail(a)); return true; })()", 1600),
    ("23-card-locked-fx", CLOSE + "; return (()=>{ const d = HUNDO_FX.find(x => x.need && !hundoFxEarned(x.id)); if(!d) return false; showUnlockDetail(hundoFxDetail(d.id)); return true; })()", 2200),
    ("24-card-rim", CLOSE + "; showUnlockDetail(rimDetail('acc')); return true;", 1600),
    ("25-card-held-character", CLOSE + "; return (()=>{ const id = (AVATAR_CHARACTERS.find(c => c.feat && !c.secret && !isLockedCharacter(c.id)) || {}).id; if(!id) return false; showUnlockDetail(characterDetail(id)); return true; })()", 2000),
]

with sync_playwright() as p:
    br = p.chromium.launch(executable_path=h["g"]["CHROME"], args=["--no-sandbox"])
    for cls in ("academy", "ifc"):
        if ONLY and ONLY != cls: continue
        for dev, w, hh, sc in (("pm", 440, 956, 3), ("ipad", 834, 1194, 2)):
            if DEV and DEV != dev: continue
            seed, init = fx["rich_" + cls]
            ctx, pg, errs = h["page"](br, text, seed, init, w=w, h=hh, scale=sc)
            pg.wait_for_timeout(1500)
            h["quiet"](pg); h["load_board"](pg); h["quiet"](pg)
            if ZOOM:
                pg.evaluate("(z)=>{ document.documentElement.style.fontSize = z + '%'; }", ZOOM)
            pre = os.path.join(OUT, "%s-%s-" % (cls, dev))
            for name, js, ms in STEPS:
                ok = pg.evaluate("()=>{ try{ %s }catch(e){ return false; } }" % js)
                if ok is False:
                    print("skip", cls, dev, name, flush=True); continue
                pg.wait_for_timeout(ms)
                pg.screenshot(path=pre + name + ".png")
            pg.evaluate("()=>{ %s }" % CLOSE)
            print(cls, dev, "errors:", errs[:3], flush=True)
            ctx.close()
    br.close()
