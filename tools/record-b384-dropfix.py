#!/usr/bin/env python3
"""Record 384.129's drop-downs as mp4s at iPhone 17 Pro Max size (440x956, 3x): the frames the compositor produced (CDP
Page.screencastFrame, each with its own timestamp) laid end to end at their real timing, at 4x CPU, a ring where a finger lands
and a caption naming the build - plus, for every tap, a filmstrip of the frames from the tap to 700ms after it.

  dropdowns: his question (the Harris County wood-chips permit), his sequence: the Hint shut/open (four taps), the answer, the
             AMENDMENTS code box shut and opened at the end of the page (twice)
  review:    Answer Review (Fire Code, every unit): the biggest unit opened, then shut

  PDFJS_DIR=... python3 tools/record-b384-dropfix.py OUTDIR [--against FILE] [--tag main|lagaudio|dropfix] [--clips dropdowns,review]
"""
import base64, json, os, re, shutil, subprocess, sys, tempfile, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from playwright.sync_api import sync_playwright
def arg(n, d=None): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d
OUT = sys.argv[1]
RAW = open(arg("--against") or os.path.join(os.path.dirname(HERE), "index.html"), encoding="utf-8").read()
TAG = arg("--tag") or "dropfix"
CLIPS = (arg("--clips") or "dropdowns,review").split(",")
FF = "/usr/bin/ffmpeg" if os.path.exists("/usr/bin/ffmpeg") else "ffmpeg"
os.makedirs(OUT, exist_ok=True)
RING = """(() => {
  const s = document.createElement('style');
  s.textContent = '#__cap{position:fixed;left:10px;right:10px;top:6px;z-index:2147483646;pointer-events:none;padding:5px 10px;border-radius:12px;background:rgba(0,0,0,.72);color:#fff;font:600 12px/1.3 system-ui,sans-serif;text-align:center}'
   + '.__ring{position:fixed;z-index:2147483647;width:44px;height:44px;margin:-22px 0 0 -22px;border-radius:50%;border:3px solid rgba(255,200,80,.95);pointer-events:none;animation:__r .5s ease-out forwards}'
   + '@keyframes __r{from{transform:scale(.6);opacity:1}to{transform:scale(1.25);opacity:0}}';
  document.body.appendChild(s);
  const c = document.createElement('div'); c.id = '__cap'; document.body.appendChild(c);
  window.__capSet = t => { c.innerHTML = t; };
  addEventListener('pointerdown', e => { const r = document.createElement('div'); r.className = '__ring'; r.style.left = e.clientX + 'px'; r.style.top = e.clientY + 'px';
    document.body.appendChild(r); setTimeout(() => r.remove(), 600); }, true);
})()"""
def cap(pg, t):
    try: pg.evaluate("(t)=>window.__capSet && window.__capSet(t)", "<b>%s</b> - %s" % (TAG.upper(), t))
    except Exception: pass
class Rec:
    def __init__(self, cdp):
        self.cdp, self.frames, self.on, self.taps = cdp, [], False, []
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
        d = tempfile.mkdtemp(prefix="b384df-")
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
        # a filmstrip per tap: every compositor frame from the tap to 700ms after, each labelled with its ms from the tap
        from PIL import Image, ImageDraw
        for k, (t0, name) in enumerate(self.taps):
            fs = [(ts, fn) for ts, fn in lst if t0 - .02 <= ts <= t0 + .7]
            if not fs: continue
            fs = fs[:24]
            tiles = []
            for ts, fn in fs:
                im = Image.open(fn).convert("RGB"); im = im.resize((im.width // 3, im.height // 3))
                dr = ImageDraw.Draw(im); dr.rectangle((0, 0, 120, 16), fill=(0, 0, 0)); dr.text((3, 2), "%+.0f ms" % ((ts - t0) * 1000), fill=(255, 220, 80))
                tiles.append(im)
            cols = min(8, len(tiles)); rows = (len(tiles) + cols - 1) // cols
            W, H = tiles[0].width, tiles[0].height
            sheet = Image.new("RGB", (cols * (W + 4), rows * (H + 4) + 22), (40, 0, 40))
            ImageDraw.Draw(sheet).text((6, 4), "%s - %s (4x CPU; frames from the tap)" % (TAG, name), fill=(255, 255, 255))
            for i, im in enumerate(tiles): sheet.paste(im, ((i % cols) * (W + 4), 22 + (i // cols) * (H + 4)))
            sp = path.replace(".mp4", "-strip%02d.jpg" % (k + 1)); sheet.save(sp, quality=85)
            print("  filmstrip", sp)
        shutil.rmtree(d, ignore_errors=True)
        print("  wrote %s (%d frames, %.1fs)" % (path, len(lst), lst[-1][0] - lst[0][0]))

src = open(os.path.join(HERE, "check-b382-test.py")).read().split("\nwith sync_playwright() as pw:")[0]
src = src.replace("device_scale_factor=2", "device_scale_factor=3").replace("pg.goto(url)", "pg.set_default_timeout(180000); pg.goto(url, timeout=240000)")
G = {"__file__": os.path.join(HERE, "check-b382-test.py"), "__name__": "b384dfrec"}; exec(src, G)
IR = G["g"]["INSET_RE"]
def _pat(ins):
    t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
    return IR.sub(lambda m: v[m.group(1)], RAW)
G["g"]["patched"] = _pat
_rp = G["route_pdf"]; _bld = (re.search(r'const APP_BUILD = "([^"]+)"', RAW) or [None, ""])[1]
def _route(c):
    _rp(c)
    c.route("**/version.json*", lambda r, q: r.fulfill(status=200, headers={"content-type": "application/json"},
            body=json.dumps({"build": _bld, "note": "", "frameId": "", "force": True, "safariSound": True})))
G["route_pdf"] = _route

def setup(br):
    label, w, h, ins, ua = G["SIZES"][0]
    ctx, pg, cdp = G["page"](br, w, h, ins, ua)
    pg.evaluate("()=>{ " + RING + "; }")
    pg.keyboard.press("Shift"); pg.wait_for_timeout(800)   # the sound woken, as on his phone
    pg.evaluate("()=>{ try{ localStorage.removeItem('class26e.codeopen'); localStorage.removeItem('class26e.ifc.codeopen'); }catch(e){} }")
    return ctx, pg, cdp
def tapsel(pg, cdp, rec, sel, name):
    c = pg.evaluate("(s)=>{ const b=document.querySelector(s); if(!b) return null; const r=b.getBoundingClientRect(); return [r.left+Math.min(r.width/2, 120), r.top+r.height/2]; }", sel)
    if not c: print("  missing", sel); return
    rec.taps.append((time.time(), name))
    G["tap"](cdp, c[0], c[1], .08)

def dropdowns(br):
    ctx, pg, cdp = setup(br)
    pg.evaluate("""()=>{ let ids = %s; ids = ids.filter(i => /\\d/.test(QUESTIONS[i].choices.join(' ')));
      const his = ids.find(i => /wood chips or hogged/i.test(String(QUESTIONS[i].q || ''))); ids = his != null ? [his] : ids.slice(0, 1);
      cfg.source='all'; cfg.mode='drill'; cfg.units=[QUESTIONS[ids[0]].topic]; beginRun(ids); }""" % G["AMEND"])
    pg.wait_for_selector(".qpanel .choice", timeout=60000)
    for _ in range(160):
        if pg.evaluate("()=>!!document.querySelector('.qpanel .ifc-hint-btn')"): break
        pg.wait_for_timeout(250)
    pg.wait_for_timeout(2500)
    rec = Rec(cdp)
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
    rec.start()
    for k in range(2):
        cap(pg, "4x CPU - Hint: Show the code"); tapsel(pg, cdp, rec, ".qpanel .ifc-hint-btn", "Hint opening (%d)" % (k + 1)); pg.wait_for_timeout(1500)
        cap(pg, "4x CPU - Hint: Hide the code"); tapsel(pg, cdp, rec, ".qpanel .ifc-hint-btn", "Hint shutting (%d)" % (k + 1)); pg.wait_for_timeout(1500)
    cap(pg, "4x CPU - the answer"); G["answer_right"](pg, cdp); pg.wait_for_timeout(800)
    # his answer had the code box open (he had opened it before): open it as he had it, then his shut/open at the end of the page
    if not pg.evaluate("()=>{ const d = document.querySelector('.qpanel details.ifc-code'); return !!(d && d.open); }"):
        tapsel(pg, cdp, rec, ".qpanel .ifc-code-sum", "code box opening (after the answer)"); pg.wait_for_timeout(2200)
    for k in range(2):
        pg.evaluate("()=>scrollTo({ top: 99999, behavior: 'instant' })"); pg.wait_for_timeout(600)
        cap(pg, "4x CPU - end of the page: Hide the code"); tapsel(pg, cdp, rec, ".qpanel .ifc-code-sum", "code box shutting at the page's end (%d)" % (k + 1)); pg.wait_for_timeout(1800)
        cap(pg, "4x CPU - AMENDMENTS: Show the code"); tapsel(pg, cdp, rec, ".qpanel .ifc-code-sum", "code box opening (%d)" % (k + 1)); pg.wait_for_timeout(2000)
    rec.stop(); cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
    rec.write(os.path.join(OUT, "%s-dropdowns.mp4" % TAG))
    ctx.close()

def review(br):
    ctx, pg, cdp = setup(br)
    pg.evaluate("()=>{ const u = [...new Set(QUESTIONS.map(q => q.topic))]; showAnswerReview(u, 'all', {}); }")
    pg.wait_for_timeout(3000)
    pg.evaluate("""()=>{ let best = null, n = -1; document.querySelectorAll('.cal-month-sect').forEach(s => { const h = s.querySelector('.cal-month-head');
      const lab = h && h.textContent || ''; const c = QUESTIONS.filter(q => (q.topic || '').trim() === lab.trim()).length; if(h && c > n){ n = c; best = h; } });
      if(best){ best.setAttribute('data-df', '1'); best.scrollIntoView({ block: 'start', behavior: 'instant' }); } }""")
    pg.wait_for_timeout(800)
    rec = Rec(cdp)
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
    rec.start()
    cap(pg, "4x CPU - Answer Review: open a unit"); tapsel(pg, cdp, rec, ".cal-month-head[data-df]", "Answer Review unit opening"); pg.wait_for_timeout(2200)
    cap(pg, "4x CPU - Answer Review: shut it"); tapsel(pg, cdp, rec, ".cal-month-head[data-df]", "Answer Review unit shutting"); pg.wait_for_timeout(2000)
    rec.stop(); cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
    rec.write(os.path.join(OUT, "%s-review.mp4" % TAG))
    ctx.close()

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    if "dropdowns" in CLIPS: dropdowns(br)
    if "review" in CLIPS: review(br)
    br.close()
G["srv"].shutdown()
