"""Build 363, Fire Code: tapping Profile lights Profile (not Settings), tapping Settings lights Settings. Profile builds its own
Settings panel hidden, which the bar used to count as "on Settings".
Run:  python3 tools/check-b363-ifc.py   (add --against old.html: copy it over index.html first, as the other checks do)"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); H = ROOT + "/tools"
src = open(H + "/record-landing.py").read().split("\nSCENES = {")[0]
g = {"__file__": H + "/record-landing.py", "__name__": "rl"}; exec(src, g)
rl_main = open(H + "/record-landing.py").read()
exec(rl_main[rl_main.index("def encode("):rl_main.index("\ndef main(") if "\ndef main(" in rl_main else None], g)
from playwright.sync_api import sync_playwright
rc = g["g"]; seed = dict(rc["SEED"]); seed["publicId"] = "xph5b57jbp5a"; seed["firstName"] = "Maddog"; seed["novaMet"] = 99
srv, port = rc["serve"]()
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else info)
KEYS = "['class26e.ifc.intro.seen','class26e.ifc.unithold.tip','class26e.ifc.daily.seen','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen']"
TAP = "(d)=>{ document.getElementById('nova-intro')?.remove(); const el=document.getElementById('bottomtab-'+d); const b=el.getBoundingClientRect(); const x=b.left+b.width/2,y=b.top+b.height/2; const mk=t=>new PointerEvent(t,{bubbles:true,cancelable:true,pointerType:'touch',pointerId:71,isPrimary:true,clientX:x,clientY:y}); el.dispatchEvent(mk('pointerdown')); setTimeout(()=>{ el.dispatchEvent(mk('pointerup')); el.dispatchEvent(new MouseEvent('click',{bubbles:true,clientX:x,clientY:y})); },60); }"
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    for ifc in (True, False):
        tag = "Fire Code" if ifc else "Academy"
        ctx, pg = rc["new_page"](br, port, 440, 956, seed)
        if ifc: pg.evaluate("()=>{ localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done'); localStorage.setItem('class26e.activeclass','ifc'); }")
        pg.reload(); pg.wait_for_timeout(3200)
        pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); try{ homeUnlocksOwed=()=>false; }catch(e){} store.novaMet=99; " + KEYS + ".forEach(k=>localStorage.setItem(k,'1')); document.querySelectorAll('.rs-spot,.unlock-card,.nova-talk').forEach(n=>n.remove()); }")
        pg.wait_for_timeout(1500)
        lit = lambda: pg.evaluate("()=>[...document.querySelectorAll('#bottomtabs .bottomtab.active')].map(b=>b.id).join(',')")
        got = []
        for d in (["profile", "settings", "profile", "rewards", "profile"] if ifc else ["profile", "rewards", "profile"]):
            pg.evaluate(TAP, d); pg.wait_for_timeout(1800); got.append((d, lit()))
        if ifc:
            chk(tag + ": each tap lights its own tab and only it (%s)" % (got,), all(l == "bottomtab-" + d for d, l in got), got)
        else:
            chk(tag + ": Profile lights Profile (%s)" % (got,), all(l == "bottomtab-" + d for d, l in got), got)
        ctx.close()
    br.close()
sys.exit(0 if ok else 1)
