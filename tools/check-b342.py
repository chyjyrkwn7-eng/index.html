"""Build 342: Fire Code swaps Calendar for Settings in the bar and has no Mock; the class button is the daily question's
twin on Home; the shared link's preview names no class and its icon is a real file; the Home Screen name is "Nova".
Run:  python3 tools/check-b342.py [--shots DIR]"""
import os, sys, json, re
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
KEYS = "['class26e.ifc.intro.seen','class26e.ifc.unithold.tip','class26e.ifc.daily.seen','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen']"
BAR = """()=>{ const t=[...document.querySelectorAll('#bottomtabs .bottomtab')].filter(b=>b.offsetWidth>0).map(b=>({id:b.id, label:b.textContent.trim(), svg:!!b.querySelector('svg'), active:b.classList.contains('active')})); return t; }"""
def go(pg, ifc):
    if ifc: pg.evaluate("()=>{ localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done'); localStorage.setItem('class26e.activeclass','ifc'); }")
    pg.reload(); pg.wait_for_timeout(3200)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); try{ homeUnlocksOwed=()=>false; }catch(e){} store.novaMet=99; " + KEYS + ".forEach(k=>localStorage.setItem(k,'1')); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); showHome(); }")
    pg.wait_for_timeout(1500)
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    for ifc in (True, False):
        tag = "Fire Code" if ifc else "Academy"
        ctx, pg = rc["new_page"](br, port, 440, 956, seed); go(pg, ifc)
        bar = pg.evaluate(BAR); ids = [b["id"] for b in bar]
        if ifc:
            chk(tag + ": the bar is Home, Profile, Leaderboard, Settings", ids == ["bottomtab-home", "bottomtab-profile", "bottomtab-rewards", "bottomtab-settings"], ids)
            chk(tag + ": Settings has its gear drawn", all(b["svg"] for b in bar), bar)
        else:
            chk(tag + ": the bar is Home, Profile, Leaderboard, Calendar", ids == ["bottomtab-home", "bottomtab-profile", "bottomtab-rewards", "bottomtab-calendar"], ids)
        # the class button: the daily question's twin
        d = pg.evaluate("""()=>{ const b=document.querySelector('.class-bubble'), q=document.querySelector('.daily-question-fab'); if(!b||!q) return null;
          const rb=b.getBoundingClientRect(), rq=q.getBoundingClientRect(), cb=getComputedStyle(b), cq=getComputedStyle(q);
          return { bw:rb.width, qw:rq.width, bBottom:rb.bottom, qBottom:rq.bottom, bLeft:rb.left, qRight:innerWidth-rq.right, bg:cb.backgroundColor, qbg:cq.backgroundColor, blur:cb.backdropFilter||cb.webkitBackdropFilter, shadow:cb.boxShadow }; }""")
        if d:
            chk(tag + ": the class button is the daily question's size (%.0f vs %.0f)" % (d["bw"], d["qw"]), abs(d["bw"] - d["qw"]) <= 1, d)
            chk(tag + ": ...on its line (bottoms %.0f vs %.0f) and as far from its edge (%.0f vs %.0f)" % (d["bBottom"], d["qBottom"], d["bLeft"], d["qRight"]), abs(d["bBottom"] - d["qBottom"]) <= 1.5 and abs(d["bLeft"] - d["qRight"]) <= 1.5, d)
            chk(tag + ": ...in the same glass (body, blur) with no coloured glow", d["bg"] == d["qbg"] and "blur" in d["blur"] and not re.search(r"rgba?\(\d+, \d+, \d+, 0?\.\d+\) 0px 0px 1\d+px", d["shadow"]), d)
        if SHOTS: os.makedirs(SHOTS, exist_ok=True); pg.screenshot(path=SHOTS + "/home-" + ("ifc" if ifc else "academy") + ".png")
        if ifc:
            pg.evaluate("()=>{ document.querySelector('#bottomtab-settings')?.click(); }"); pg.wait_for_timeout(1800)
            s = pg.evaluate("()=>({ settings: !!document.querySelector('.screen-settings'), lit: !!document.querySelector('#bottomtab-settings')?.classList.contains('active'), onlyOne: document.querySelectorAll('#bottomtabs .bottomtab.active').length, platter: (()=>{ const a=(document.querySelector('#bottomtab-settings')||document.body).getBoundingClientRect(), p=document.querySelector('.bottomtabs-slider').getBoundingClientRect(); return Math.abs((a.left+a.width/2)-(p.left+p.width/2)); })() })")
            chk(tag + ": tapping Settings opens it, lights only it, and the platter is on it", s["settings"] and s["lit"] and s["onlyOne"] == 1 and s["platter"] < 2, s)
            if SHOTS: pg.screenshot(path=SHOTS + "/settings-ifc.png")
        pg.evaluate("()=>{ showModeSelect(); }"); pg.wait_for_timeout(900)
        modes = pg.evaluate("()=>[...document.querySelectorAll('.modecard')].map(c=>c.dataset.mode)")
        if ifc: chk(tag + ": no Mock card (" + ",".join(modes) + ")", "exam" not in modes and "drill" in modes, modes)
        else: chk(tag + ": Mock is still a card", "exam" in modes, modes)
        ctx.close()
    # the shared link and the Home Screen
    ctx, pg = rc["new_page"](br, port, 440, 956, seed); pg.reload(); pg.wait_for_timeout(2500)
    m = pg.evaluate("""()=>({ title: document.title, ogs: [...document.querySelectorAll('meta[property^="og:"],meta[name^="twitter:"],meta[name="description"]')].map(m=>m.content),
      img: document.querySelector('meta[property="og:image"]').content, touch: document.querySelector('link[rel="apple-touch-icon"]').href, share: typeof SHARE_URL === 'string' ? SHARE_URL : '' })""")
    chk("the page's title, which names the Home Screen app, is exactly Nova", m["title"] == "Nova", m["title"])
    chk("the link preview names no class", not any("26E" in x for x in m["ogs"]), m["ogs"])
    chk("the preview image and the touch icon are absolute addresses of real files", m["img"].startswith("https://") and m["touch"].startswith("https://") and m["touch"].endswith("share/apple-touch-icon.png") and os.path.exists(ROOT + "/share/apple-touch-icon.png") and os.path.exists(ROOT + "/share/og-card.png"), m)
    ctx.close(); br.close()
sys.exit(0 if ok else 1)
