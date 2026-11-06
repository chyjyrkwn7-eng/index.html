"""The Fire Code clips on the Get Started page:
  landing/test - Fire Code questions played in a Drill, the code under each answer cut from the owner's own book
                 ("Show the code" on a right answer; a miss opens it by itself);
  landing/ifc  - loading the book: the Enroll in Fire Code screen, "Choose my IFC PDF", the Analyzing screen to Verified.

  PDFJS_DIR=<unpacked pdfjs-dist 5.4.149 package> IFC_BOOK=<the owner's 2021 IFC PDF> python3 tools/record-landing-ifc.py [test|ifc]

Build 330 made both; build 384 (round 2) re-recorded them with record-landing.py's capture (780x1690, the page in slow
motion, a true 30 fps clock, each clip from its beginning and looping on itself, its poster its first frame) - see there.
"Ensure the videos show a lot of the test example with the ifc fire code stuff": the test clip is two Fire Code questions
with their code open, read in place (a small cut of the section, never a whole page). The ifc clip used to open on the
Analyzing screen already running - "start at weird spots and skip around like the upload pdf one"; it now starts on the
enroll screen and runs the screen at its own pace (its 12-second floor), to Verified.
THE BOOK IS THE OWNER'S LICENSED PDF AND NEVER GOES INTO THE REPO (the repo is public): its path is given when this runs, and
only the small cut the app draws under a question appears in the clip. The account is a fixture ("Alex"); its publicId is
the class owner's, because only that account can open the Fire Code class (that id is not shown anywhere on screen)."""
import importlib.util, json, mimetypes, os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("record_landing", os.path.join(HERE, "record-landing.py"))
rl = importlib.util.module_from_spec(spec); spec.loader.exec_module(rl)
from playwright.sync_api import sync_playwright

PDFJS = os.environ.get("PDFJS_DIR", "").rstrip("/") + "/"
BOOK = os.environ.get("IFC_BOOK", "")
OWNER = "xph5b57jbp5a"
SEED = dict(rl.SEED, publicId=OWNER)
IFC_SEED = dict(SEED, unitPerfects={})
IN_IFC = ("localStorage.setItem('class26e.activeclass','ifc'); localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc']));"
          "localStorage.setItem('class26e.greet.ifc','done');"
          "['freshstart','intro.seen','daily.seen','savecode.asked','savecode.card','getstarted','unithold.tip'].forEach(k=>localStorage.setItem('class26e.ifc.'+k,'1'));"
          "localStorage.setItem('class26e.ifc.drill.v1', %s);" % json.dumps(json.dumps(IFC_SEED)))
# 307.4.2 (a recreational fire's distance from a structure), 907.4.2.2 (a manual fire alarm box's height): short text
# sections, each a small cut of one page
TEST_QS = [int(x) for x in os.environ.get("IFC_QS", "200,593").split(",")]


def route_pdfjs(ctx):
    def h(route, req):
        rel = req.url.split("pdfjs-dist@5.4.149/", 1)[1].split("?")[0]
        p = PDFJS + rel
        if not os.path.exists(p): return route.fulfill(status=404, body="")
        ct = "application/wasm" if p.endswith(".wasm") else ("text/javascript" if p.endswith((".mjs", ".js")) else (mimetypes.guess_type(p)[0] or "application/octet-stream"))
        route.fulfill(status=200, body=open(p, "rb").read(), content_type=ct, headers={"access-control-allow-origin": "*"})
    ctx.route("**/pdfjs-dist@5.4.149/**", h)


def poll(pg, js, ms):
    t = 0
    while t < ms:
        if pg.evaluate(js): return True
        pg.wait_for_timeout(200); t += 200
    return bool(pg.evaluate(js))


def open_code(pg):
    """'Show the code' (unless a miss has opened it already), then wait for its picture"""
    pg.evaluate("()=>{ const d = [...document.querySelectorAll('.qpanel .ifc-code')].filter(x => x.getBoundingClientRect().height > 0).pop(); if(d && !d.open) d.querySelector('summary').click(); }")
    got = poll(pg, "()=>{ const d = [...document.querySelectorAll('.qpanel .ifc-code[open]')].filter(x => x.getBoundingClientRect().height > 0).pop(); const c = d && d.querySelector('.ifc-code-body canvas'); return !!c && c.width > 0; }", 40000)
    if not got: print("  !! the code picture was not drawn", flush=True)


def scene_test(br, port):
    if not os.path.exists(PDFJS + "build/pdf.min.mjs") or not os.path.isfile(BOOK):
        raise SystemExit("test: set PDFJS_DIR (pdfjs-dist 5.4.149, unpacked) and IFC_BOOK (the owner's 2021 IFC PDF)")
    ctx, pg = rl.new_page(br, port, SEED, IN_IFC, route=route_pdfjs)
    print("  test: class %s, %d questions; loading the book (the reader's own path, a minute or two here)..." % tuple(
        pg.evaluate("()=>[window.NOVA_CLASS, QUESTIONS.length]")), flush=True)
    pg.evaluate("()=>{ ifcPickBook(); }"); pg.wait_for_timeout(400)
    pg.set_input_files("#ifc-book-input", BOOK)
    if not poll(pg, "()=>!!document.querySelector('.ifc-analyze.is-ok, .ifc-analyze.is-bad')", 300000) or \
       not pg.evaluate("()=>!!document.querySelector('.ifc-analyze.is-ok')"):
        raise SystemExit("test: the book was not accepted")
    pg.evaluate("()=>{ document.querySelector('.ifc-analyze .ia-actions button')?.click(); document.querySelector('.ifc-analyze')?.remove(); }")
    pg.wait_for_timeout(800); rl.settle(pg)
    unit = pg.evaluate("(i)=>(QUESTIONS[i].topic||'').trim()", TEST_QS[0])
    print("  test: " + " | ".join(pg.evaluate("(ix)=>ix.map(i=>QUESTIONS[i].ifc.citation.label)", TEST_QS)), flush=True)
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(600)
    rl.start_unit_run(pg, unit, TEST_QS)
    rec = rl.Recorder(pg); rec.start()
    rl.wait(pg, int(1100 * rl.HOLD))
    # a right answer, then the code under it
    rl.answer(pg, True, 1200)
    open_code(pg); rl.wait(pg, 250)
    print("  glide", rl.glide_to(pg, ".qpanel .ifc-code", "center", 900), flush=True); rl.wait(pg, 2600)
    rl.next_q(pg, 900)
    # a miss: the code opens by itself once it is answered
    rl.answer(pg, False, 1300); rl.answer(pg, True, 1100)
    open_code(pg); rl.wait(pg, 250)
    print("  glide", rl.glide_to(pg, ".qpanel .ifc-code", "center", 900), flush=True); rl.wait(pg, 2800)
    frames = rec.stop(); ctx.close()
    rl.encode(frames, "test")


def scene_ifc(br, port):
    ctx, pg = rl.new_page(br, port, SEED)
    pg.evaluate("()=>showIfcEnroll()"); pg.wait_for_timeout(1500)
    # the analysis itself stands in (the screen and its 12-second floor are the app's own): a file name, no file read
    pg.evaluate("""()=>{ ifcAnalyzeBook = async (file, step) => { const W = ms => new Promise(r => setTimeout(r, ms));
        for(let i = 0; i <= 10; i++){ step('open', i / 10); await W(70); }
        for(let i = 0; i <= 40; i++){ step('index', i / 40); await W(150); }
        for(let i = 0; i <= 20; i++){ step('verify', i / 20); await W(170); }
        return { level: 'exact', kept: true }; }; }""")
    d = tempfile.mkdtemp(prefix="ifcpick-")
    f = os.path.join(d, "2021 International Fire Code.pdf")
    open(f, "wb").write(b"%PDF-1.4\n%stand-in\n")
    rec = rl.Recorder(pg); rec.start()
    rl.wait(pg, 1600)
    with pg.expect_file_chooser() as fc:
        pg.evaluate("()=>document.querySelector('.class-enroll .ce-go').click()")
    fc.value.set_files(f)
    poll(pg, "()=>!!document.querySelector('.ifc-analyze.is-ok')", 240000)
    rl.wait(pg, 2600)
    frames = rec.stop(); ctx.close()
    rl.encode(frames, "ifc")


SCENES = {"test": scene_test, "ifc": scene_ifc}

if __name__ == "__main__":
    srv, port = rl.serve()
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=rl.CHROME)
        for name in (sys.argv[1:] or list(SCENES)):
            SCENES[name](br, port)
        br.close()
    srv.shutdown()
