"""Build 346: Settings has a Version history button; it opens the release history with Settings as its way back.
Run:  python3 tools/check-b346.py [--shots DIR]"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H = ROOT + "/tools"
# (384) record-landing.py no longer wraps the cutscene harness (Get Started round 2 made it self-contained), so the
# harness it used to hand over as g["g"] - record-cutscenes.py's, at 1.5x - is loaded here the way it loaded it
src = open(H + "/record-cutscenes.py").read().split("\nSCENES = [")[0].replace("device_scale_factor=1)", "device_scale_factor=1.5)")
_rc = {"__file__": H + "/record-cutscenes.py", "__name__": "rc"}; exec(src, _rc)
g = {"g": _rc}
from playwright.sync_api import sync_playwright
rc = g["g"]; seed = dict(rc["SEED"]); seed["publicId"] = "xph5b57jbp5a"; seed["firstName"] = "Maddog"; seed["novaMet"] = 99
SHOTS = sys.argv[sys.argv.index("--shots") + 1] if "--shots" in sys.argv else None
srv, port = rc["serve"]()
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else info)
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    ctx, pg = rc["new_page"](br, port, 440, 956, seed); pg.reload(); pg.wait_for_timeout(3000)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); store.novaMet=99; ['class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen'].forEach(k=>localStorage.setItem(k,'1')); showAppearance(); }"); pg.wait_for_timeout(1500)
    for _ in range(3):
        pg.evaluate("()=>{ [...document.querySelectorAll('button')].filter(b=>/^(Got it|Continue|Close|Done|Skip|Not now)$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }"); pg.wait_for_timeout(300)
    r = pg.evaluate("()=>{ const b=document.getElementById('settings-version-history'); if(!b) return null; const r=b.getBoundingClientRect(); return { text:b.textContent, h:r.height, w:r.width, vis: r.width>0 && r.bottom>0 }; }")
    chk("Settings has a Version history button, a proper tap target", r and r["text"] == "Version history" and r["h"] >= 44, r)
    if SHOTS:
        os.makedirs(SHOTS, exist_ok=True)
        pg.evaluate("()=>document.getElementById('settings-version-history')?.scrollIntoView({block:'center'})"); pg.wait_for_timeout(500); pg.screenshot(path=SHOTS + "/settings-version.png")
    pg.evaluate("()=>document.getElementById('settings-version-history')?.click()"); pg.wait_for_timeout(1200)
    # (384) the history wears the iOS nav bar every pushed screen has, its title "Version history" - so the screen is found by
    # its class and the bar's title read off the page, not a label string
    h = pg.evaluate("()=>{ const p=document.querySelector('.screen-releasehistory'); return { screen: !!p, versions: p ? p.querySelectorAll('.releasehistory-version').length : 0, title: p ? ((p.querySelector('.ios-navbar-title,.ios-nav-title,h1,h2')||{}).textContent||'') : '', back: (document.querySelector('.back-link')||{}).textContent }; }")
    chk("it opens the release history, with Settings as the way back", h["screen"] and h["title"].strip() and h["versions"] >= 2 and "Settings" in (h["back"] or ""), h)
    pg.evaluate("()=>document.querySelector('.back-link')?.click()"); pg.wait_for_timeout(1200)
    s = pg.evaluate("()=>!!document.querySelector('.screen-settings') || /Settings/.test(document.body.innerText) && !!document.getElementById('settings-version-history')")
    chk("Back returns to Settings", s)
    # (383/384) Home's version tag is a plain label now - Settings' Version history is the one way in - so the Home check is gone
    ctx.close(); br.close()
sys.exit(0 if ok else 1)
