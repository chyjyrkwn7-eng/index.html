"""python3 tools/record-landing-ifc.py [test|ifc]   (PDFJS_DIR=<unpacked pdfjs-dist package>)
Build 330: Fire Code clips for the Get Started page: landing/test (a Fire Code drill, a wrong try opens the code)
and landing/ifc (the green analysis of an IFC PDF). Owner account in the Fire Code class; pdf.js from npm."""
import os, sys, json, mimetypes
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# pdf.js 5.4.149 unpacked from npm (npm pack pdfjs-dist@5.4.149), folder "package": the sandbox cannot reach jsDelivr
PDFJS = os.environ.get("PDFJS_DIR", "") + "/"
H = ROOT + "/tools"
src = open(H + "/record-landing.py").read().split("\nSCENES = {")[0]
g = {"__file__": H + "/record-landing.py", "__name__": "rl"}; exec(src, g)
rl_main = open(H + "/record-landing.py").read()
exec(rl_main[rl_main.index("def encode("):rl_main.index("\ndef main(") if "\ndef main(" in rl_main else None], g)
from playwright.sync_api import sync_playwright
rc = g["g"]
seed = dict(rc["SEED"]); seed["publicId"] = "xph5b57jbp5a"; seed["firstName"] = "Maddog"; seed["novaMet"] = 99
def route_pdfjs(ctx):
    def h(route, req):
        rel = req.url.split("pdfjs-dist@5.4.149/", 1)[1].split("?")[0]
        p = PDFJS + rel
        if not os.path.exists(p): return route.fulfill(status=404, body="")
        route.fulfill(status=200, body=open(p, "rb").read(), content_type=mimetypes.guess_type(p)[0] or "text/javascript",
                      headers={"access-control-allow-origin": "*"})
    ctx.route("**/pdfjs-dist@5.4.149/**", h)
srv, port = rc["serve"]()
only = sys.argv[1:] or ["test", "ifc"]
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    for name in only:
        ctx, pg = rc["new_page"](br, port, 360, 780, seed)
        route_pdfjs(ctx)
        pg.evaluate("()=>{ localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done'); localStorage.setItem('class26e.activeclass','ifc'); }")
        pg.reload(); pg.wait_for_timeout(3200)
        pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); try{ homeUnlocksOwed=()=>false; }catch(e){} store.novaMet=99; ['class26e.ifc.intro.seen','class26e.ifc.unithold.tip','class26e.ifc.daily.seen'].forEach(k=>localStorage.setItem(k,'9')); }")
        print(name, pg.evaluate("()=>({cls: window.NOVA_CLASS, n: QUESTIONS.length, u: topicsIn(QUESTIONS)[0]})"))
        rec = rc["Recorder"](pg)
        if name == "test":
            pg.evaluate("()=>{ document.querySelectorAll('#tour-overlay, #tour-tooltip, #nova-intro').forEach(n=>n.remove()); showHome(); }"); pg.wait_for_timeout(500)
            u = pg.evaluate("()=>topicsIn(QUESTIONS)[0]")
            rc["start_unit_run"](pg, u)
            pg.wait_for_selector(".choice", timeout=25000); pg.wait_for_timeout(700)
            rec.start(); pg.wait_for_timeout(600)
            for k in range(2):
                pg.evaluate("""()=>{const r=correctSlot(order[pos]); document.querySelector('.choice[data-index="'+r+'"]').click();}""")
                pg.wait_for_timeout(1300); p = pg.evaluate("()=>pos")
                pg.evaluate("()=>document.getElementById('nextbtn')?.click()")
                for _ in range(30):
                    pg.wait_for_timeout(120)
                    if pg.evaluate("()=>pos") != p: break
                pg.wait_for_timeout(500)
            # a wrong first try: the code opens by itself
            pg.evaluate("""()=>{const r=correctSlot(order[pos]); const all=[...document.querySelectorAll('.choice')]; const w=all.find(c=>c.dataset.index!=String(r)); w && w.click();}""")
            pg.wait_for_timeout(1500)
            pg.evaluate("""()=>{const r=correctSlot(order[pos]); document.querySelector('.choice[data-index="'+r+'"]').click();}""")
            pg.wait_for_timeout(1200)
            for _ in range(40):
                if pg.evaluate("()=>!!document.querySelector('.ifc-code[open] .ifc-code-body canvas, .ifc-code[open] .ifc-code-body img')"): break
                pg.wait_for_timeout(250)
            pg.evaluate("()=>{ const c=document.querySelector('.ifc-code'); c && c.scrollIntoView({block:'center', behavior:'smooth'}); }")
            pg.wait_for_timeout(2600)
            pg.evaluate("()=>{ const b=[...document.querySelectorAll('.ifc-code .ifc-link')].find(x=>/page picture/.test(x.textContent)); b && b.click(); }")
            for _ in range(40):
                if pg.evaluate("()=>!!document.querySelector('.ifc-code canvas, .ifc-code img')"): break
                pg.wait_for_timeout(250)
            pg.wait_for_timeout(600)
            pg.evaluate("()=>{ const c=document.querySelector('.ifc-code canvas, .ifc-code img'); c && c.scrollIntoView({block:'center', behavior:'smooth'}); }")
            pg.wait_for_timeout(3800)
        else:
            pg.evaluate("()=>{ document.querySelectorAll('#tour-overlay, #tour-tooltip, #nova-intro').forEach(n=>n.remove()); showHome(); }"); pg.wait_for_timeout(600)
            rec.start(); pg.wait_for_timeout(500)
            pg.evaluate("""()=>{ const W = ms => new Promise(r => setTimeout(r, ms));
              ifcAnalyzeBook = async (file, step) => { for(let i = 0; i <= 10; i++){ step('open', i / 10); await W(60); }
                for(let i = 0; i <= 40; i++){ step('index', i / 40); await W(110); }
                for(let i = 0; i <= 20; i++){ step('verify', i / 20); await W(120); } return { level: 'exact', kept: true }; };
              runIfcAnalysis({ name: 'International Fire Code 2021.pdf' }, { enroll: false }); }""")
            pg.wait_for_timeout(14500)
        frames = rec.stop()
        g["encode"](frames, name)
        ctx.close()
    br.close()
