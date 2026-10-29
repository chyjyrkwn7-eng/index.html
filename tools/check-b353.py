"""Build 353: the grey platter goes to the tab you tapped and stays there (it no longer glides back to the tab you left
while the new screen is being built, then overshoots left of Home), and the tab under the glass is back to full size
before the glass hands over.   Run:  python3 tools/check-b353.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(HERE + "/check-b330.py").read().split("want = sys.argv")[0]
g = {"__file__": HERE + "/check-b330.py", "__name__": "b330"}; exec(src, g)
from playwright.sync_api import sync_playwright
chk = g["chk"]
CLEAR = "()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }"
FILL = """()=>{ const n=AVATAR_CHARACTERS.length; const rows=[]; for(let i=0;i<42;i++){ rows.push(Object.assign({pub:'zz'+i, firstName:'Cadet'+i, avatarChar:AVATAR_CHARACTERS[i%n].id}, boardNumbersOf(store), {weekPoints:1000-i*17, hundos:60-i, correct:5000-i*70, level:40-(i>>1), badges:20-(i>>2)})); } leaderboardRows = rows; }"""
LOG = """(dest)=>{ window.__l=[]; const s=document.getElementById('bottomtabs-slider'); const lens=document.querySelector('.tab-lens'); const tt=document.getElementById('bottomtab-'+dest); const t0=performance.now();
 const tick=()=>{ const r=s.getBoundingClientRect(); const m=getComputedStyle(tt).transform; const sc = m==='none' ? 1 : new DOMMatrixReadOnly(m).a;
   window.__l.push([performance.now()-t0, r.left+r.width/2, parseFloat(getComputedStyle(s).opacity), lens?parseFloat(getComputedStyle(lens).opacity):0, sc]); if(performance.now()-t0<2400) requestAnimationFrame(tick); }; requestAnimationFrame(tick); }"""
def run(pg, ctx, frm, to):
    tabs = {t[0]: t for t in pg.evaluate("()=>[...document.querySelectorAll('.bottomtabs-navrow .bottomtab')].map(t=>{const r=t.getBoundingClientRect(); return [t.id, r.left+r.width/2, r.top+r.height/2]})")}
    t = tabs["bottomtab-" + frm]; pg.mouse.click(t[1], t[2]); pg.wait_for_timeout(2500)
    pg.evaluate(LOG, to)
    t = tabs["bottomtab-" + to]; pg.wait_for_timeout(50)
    pg.mouse.move(t[1], t[2]); pg.mouse.down(); pg.wait_for_timeout(110); pg.mouse.up(); pg.wait_for_timeout(2600)
    return tabs["bottomtab-" + to][1], pg.evaluate("()=>window.__l")
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    ctx, pg = g["page_for"](br, "promax")
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    pg.evaluate(FILL)
    cdp = ctx.new_cdp_session(pg); cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
    for frm, to in (("rewards", "home"), ("home", "rewards"), ("profile", "home")):
        c, L = run(pg, ctx, frm, to)
        up = next((i for i, r in enumerate(L) if r[3] > .5), None)
        after = L[up:] if up is not None else []
        shown = [r for r in after if r[3] <= .05 and r[2] >= .9]
        worst = max((abs(r[1] - c) for r in shown), default=99)
        chk("%s -> %s: once the platter shows it is on the tab you tapped, never off it by more than 3px (worst %.1f)" % (frm, to, worst), bool(shown) and worst <= 3, worst)
        gone = [r for r in after if r[3] <= .05]
        big = max((r[4] for r in gone), default=9) if gone else 9
        chk("%s -> %s: the tab is back to full size when the glass has gone (%.3f)" % (frm, to, big), big <= 1.03, big)
    ctx.close(); br.close()
sys.exit(0 if g["ok"] else 1)
