"""Build 346: Settings has a Version history button; it opens the release history with Settings as its way back.
Run:  python3 tools/check-b346.py [--shots DIR]"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H = ROOT + "/tools"
src = open(H + "/record-landing.py").read().split("\nSCENES = {")[0]
g = {"__file__": H + "/record-landing.py", "__name__": "rl"}; exec(src, g)
rl_main = open(H + "/record-landing.py").read()
exec(rl_main[rl_main.index("def encode("):rl_main.index("\ndef main(") if "\ndef main(" in rl_main else None], g)
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
    h = pg.evaluate("()=>({ title: [...document.querySelectorAll('.slab')].map(e=>e.textContent).join('|'), back: (document.querySelector('.back-link')||{}).textContent })")
    chk("it opens the release history, with Settings as the way back", "Release History" in h["title"] and "Settings" in (h["back"] or ""), h)
    pg.evaluate("()=>document.querySelector('.back-link')?.click()"); pg.wait_for_timeout(1200)
    s = pg.evaluate("()=>!!document.querySelector('.screen-settings') || /Settings/.test(document.body.innerText) && !!document.getElementById('settings-version-history')")
    chk("Back returns to Settings", s)
    # Home's version tag still goes back to Home
    pg.evaluate("()=>{ showHome(); }"); pg.wait_for_timeout(1500)
    pg.evaluate("()=>document.querySelector('.homeversion-btn')?.click()"); pg.wait_for_timeout(1200)
    b = pg.evaluate("()=>(document.querySelector('.back-link')||{}).textContent")
    chk("opened from Home's version tag, its way back is still Home", "Home" in (b or ""), b)
    ctx.close(); br.close()
sys.exit(0 if ok else 1)
