#!/usr/bin/env python3
"""Record 384.119's two moves as mp4s at iPhone 17 Pro Max size (440x956): the frames the compositor actually produced (CDP
Page.screencastFrame, each with its own timestamp), laid end to end at their real timing, at 4x CPU, a ring where a finger lands
and a caption naming the build.

  units:     Home -> Start Studying -> (5s on Choose your mode) -> Drill -> back -> Drill  (Fire Code, installed, 3x)
  dropdowns: his question (the Harris County wood-chips permit): the Hint open, shut, open, shut; the answer; the code box open and
             shut at the end of the page, twice  (needs PDFJS_DIR, an unpacked pdfjs-dist 5.4.149)

  python3 tools/record-b384-lagaudio.py OUTDIR [--against FILE] [--tag before|after] [--clips units,dropdowns]
"""
import base64, json, os, shutil, subprocess, sys, tempfile, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import b384_lagaudio_lib as L
from playwright.sync_api import sync_playwright
def arg(n, d=None): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d
OUT = sys.argv[1]
RAW = L.raw_of(arg("--against"))
TAG = arg("--tag") or ("before" if arg("--against") else "after")
CLIPS = (arg("--clips") or "units,dropdowns").split(",")
FF = "/usr/bin/ffmpeg" if os.path.exists("/usr/bin/ffmpeg") else "ffmpeg"
os.makedirs(OUT, exist_ok=True)
RING_BODY = """
  const s = document.createElement('style');
  s.textContent = '#__cap{position:fixed;left:10px;right:10px;top:6px;z-index:2147483646;pointer-events:none;padding:5px 10px;border-radius:12px;background:rgba(0,0,0,.72);color:#fff;font:600 12px/1.3 system-ui,sans-serif;text-align:center}'
   + '.__ring{position:fixed;z-index:2147483647;width:44px;height:44px;margin:-22px 0 0 -22px;border-radius:50%;border:3px solid rgba(255,200,80,.95);pointer-events:none;animation:__r .5s ease-out forwards}'
   + '@keyframes __r{from{transform:scale(.6);opacity:1}to{transform:scale(1.25);opacity:0}}';
  document.head.appendChild(s);
  const c = document.createElement('div'); c.id = '__cap'; document.body.appendChild(c);
  window.__capSet = t => { c.innerHTML = t; };
  addEventListener('pointerdown', e => { const r = document.createElement('div'); r.className = '__ring'; r.style.left = e.clientX + 'px'; r.style.top = e.clientY + 'px';
    document.body.appendChild(r); setTimeout(() => r.remove(), 600); }, true);
"""
RING = "addEventListener('DOMContentLoaded', () => {" + RING_BODY + "});"
RING_NOW = "(() => {" + RING_BODY + "})()"
def cap(pg, t):
    try: pg.evaluate("(t)=>window.__capSet && window.__capSet(t)", "<b>%s</b> - %s" % (TAG.upper(), t))
    except Exception: pass
class Rec:
    def __init__(self, cdp):
        self.cdp, self.frames, self.on = cdp, [], False
        cdp.on("Page.screencastFrame", self.frame)
    def frame(self, p):
        if self.on: self.frames.append((p["metadata"]["timestamp"], p["data"]))
        try: self.cdp.send("Page.screencastFrameAck", {"sessionId": p["sessionId"]})
        except Exception: pass
    def start(self):
        self.on = True
        self.cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 85, "maxWidth": 880, "maxHeight": 1912, "everyNthFrame": 1})
    def stop(self):
        self.cdp.send("Page.stopScreencast"); self.on = False
    def write(self, path):
        if len(self.frames) < 2: print("  too few frames for", path); return
        d = tempfile.mkdtemp(prefix="b384lg-")
        lst = []
        for i, (ts, data) in enumerate(self.frames):
            fn = os.path.join(d, "f%05d.jpg" % i); open(fn, "wb").write(base64.b64decode(data)); lst.append((ts, fn))
        with open(os.path.join(d, "list.txt"), "w") as f:
            for i, (ts, fn) in enumerate(lst):
                dur = (lst[i + 1][0] - ts) if i + 1 < len(lst) else .5
                f.write("file '%s'\nduration %.4f\n" % (fn, max(.001, dur)))
            f.write("file '%s'\n" % lst[-1][1])
        subprocess.run([FF, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(d, "list.txt"), "-vf", "scale=880:-2,fps=60",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", path], check=True)
        shutil.rmtree(d, ignore_errors=True)
        print("  wrote %s (%d frames, %.1fs)" % (path, len(lst), lst[-1][0] - lst[0][0]))
def units(br):
    ctx, pg, errs = L.open_page(br, RAW, "promax", "ifc", extra_init=RING)
    s = L.cdp(pg); rec = Rec(s)
    pg.evaluate("()=>{ store.seenModeSelectTour = true; store.seenUnitSelectTour = true; showHome(); }"); pg.wait_for_timeout(2000)
    rec.start(); cap(pg, "Start Studying")
    c = L.center(pg, ".playbtn"); L.tap(s, c[0], c[1], 70, pg); pg.wait_for_timeout(5500)
    L.throttle(s, 4); cap(pg, "4x CPU - tap Drill")
    pg.wait_for_timeout(500)
    c = L.center(pg, '.modecard[data-mode="drill"]'); L.tap(s, c[0], c[1], 80, pg); pg.wait_for_timeout(2600)
    cap(pg, "4x CPU - back"); c = L.center(pg, ".setup-nav-back"); L.tap(s, c[0], c[1], 80, pg); pg.wait_for_timeout(2000)
    cap(pg, "4x CPU - tap Drill again"); c = L.center(pg, '.modecard[data-mode="drill"]'); L.tap(s, c[0], c[1], 80, pg); pg.wait_for_timeout(2600)
    rec.stop(); L.throttle(s, 1)
    rec.write(os.path.join(OUT, "%s-units.mp4" % TAG))
    print("  page errors:", errs[:3]); ctx.close()
def dropdowns(br):
    if not os.path.exists(os.path.join(os.environ.get("PDFJS_DIR", ""), "build/pdf.min.mjs")):
        print("  dropdowns: set PDFJS_DIR"); return
    src = open(os.path.join(HERE, "check-b382-test.py")).read().split("\nwith sync_playwright() as pw:")[0]
    src = src.replace("pg.goto(url)", "pg.set_default_timeout(180000); pg.goto(url, timeout=240000)")
    G = {"__file__": os.path.join(HERE, "check-b382-test.py"), "__name__": "b384lgrec"}; exec(src, G)
    IR = G["g"]["INSET_RE"]
    def _pat(ins):
        t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
        return IR.sub(lambda m: v[m.group(1)], RAW)
    G["g"]["patched"] = _pat
    # version.json at the build recorded (an --against build would otherwise be told of an update and reload mid-clip)
    import re
    _rp = G["route_pdf"]; _bld = (re.search(r'const APP_BUILD = "([^"]+)"', RAW) or [None, ""])[1]
    def _route(c):
        _rp(c)
        c.route("**/version.json*", lambda r, q: r.fulfill(status=200, headers={"content-type": "application/json"},
                body=json.dumps({"build": _bld, "note": "", "frameId": "", "force": True, "safariSound": True})))
    G["route_pdf"] = _route
    label, w, h, ins, ua = G["SIZES"][0]
    ctx, pg, cdp = G["page"](br, w, h, ins, ua)
    pg.evaluate("()=>{ " + RING_NOW + "; }")
    rec = Rec(cdp)
    pg.evaluate("()=>{ try{ localStorage.removeItem('class26e.codeopen'); localStorage.removeItem('class26e.ifc.codeopen'); }catch(e){} }")
    pg.evaluate("""()=>{ let ids = %s; ids = ids.filter(i => /\\d/.test(QUESTIONS[i].choices.join(' ')));
      const his = ids.find(i => /wood chips or hogged/i.test(String(QUESTIONS[i].q || ''))); ids = his != null ? [his] : ids.slice(0, 1);
      cfg.source='all'; cfg.mode='drill'; cfg.units=[QUESTIONS[ids[0]].topic]; beginRun(ids); }""" % G["AMEND"])
    pg.wait_for_selector(".qpanel .choice", timeout=60000)
    for _ in range(160):
        if pg.evaluate("()=>!!document.querySelector('.qpanel .ifc-hint-btn')"): break
        pg.wait_for_timeout(250)
    def tapsel(sel, hold=.08):
        c = pg.evaluate("(s)=>{ const b=document.querySelector(s); if(!b) return null; const r=b.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]; }", sel)
        if c: G["tap"](cdp, c[0], c[1], hold)
    L.throttle(cdp, 4)
    rec.start()
    for k in range(2):
        cap(pg, "4x CPU - Hint: Show the code"); tapsel(".qpanel .ifc-hint-btn"); pg.wait_for_timeout(2600 if k == 0 else 1500)
        cap(pg, "4x CPU - Hint: Hide the code"); tapsel(".qpanel .ifc-hint-btn"); pg.wait_for_timeout(1500)
    cap(pg, "4x CPU - the answer"); G["answer_right"](pg, cdp); pg.wait_for_timeout(800)
    for k in range(2):
        pg.evaluate("()=>scrollTo({ top: 99999, behavior: 'instant' })"); pg.wait_for_timeout(400)
        cap(pg, "4x CPU - AMENDMENTS: Show the code"); tapsel(".qpanel .ifc-code-sum"); pg.wait_for_timeout(2200)
        pg.evaluate("()=>scrollTo({ top: 99999, behavior: 'instant' })"); pg.wait_for_timeout(600)
        cap(pg, "4x CPU - at the end of the page: Hide the code"); tapsel(".qpanel .ifc-code-sum"); pg.wait_for_timeout(1800)
    rec.stop(); L.throttle(cdp, 1)
    rec.write(os.path.join(OUT, "%s-dropdowns.mp4" % TAG))
    ctx.close(); G["srv"].shutdown()
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=L.CHROME)
    if "units" in CLIPS: units(br)
    if "dropdowns" in CLIPS: dropdowns(br)
    br.close()
