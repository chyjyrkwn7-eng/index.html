"""Build 333: the Fire Code class shows its reference under the question (not where it gives the answer
away) and opens the code in a zoomable page viewer inset from every edge.
Run:  PDFJS_DIR=<unpacked pdfjs-dist 5.4.149 package> python3 tools/check-b333.py
(the county booklet is in the repo; the owner's IFC PDF is not needed here)"""
import os, sys, json, mimetypes
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDFJS = os.environ.get("PDFJS_DIR", "") + "/"
if not os.path.exists(PDFJS + "build/pdf.min.mjs") and not os.path.exists(PDFJS + "build"):
    print("SKIP: set PDFJS_DIR to an unpacked pdfjs-dist@5.4.149"); sys.exit(0)
H = ROOT + "/tools"
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
def route(ctx):
    def h(r, req):
        rel = req.url.split("pdfjs-dist@5.4.149/", 1)[1].split("?")[0]; p = PDFJS + rel
        if not os.path.exists(p): return r.fulfill(status=404, body="")
        r.fulfill(status=200, body=open(p, "rb").read(), content_type=mimetypes.guess_type(p)[0] or "text/javascript", headers={"access-control-allow-origin": "*"})
    ctx.route("**/pdfjs-dist@5.4.149/**", h)
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    ctx, pg = rc["new_page"](br, port, 390, 844, seed); route(ctx)
    pg.evaluate("()=>{ localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done'); localStorage.setItem('class26e.activeclass','ifc'); }")
    pg.reload(); pg.wait_for_timeout(3200)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); try{ homeUnlocksOwed=()=>false; }catch(e){} store.novaMet=99; ['class26e.ifc.intro.seen','class26e.ifc.unithold.tip','class26e.ifc.daily.seen'].forEach(k=>localStorage.setItem(k,'1')); document.querySelectorAll('#tour-overlay, #tour-tooltip, #nova-intro').forEach(n=>n.remove()); showHome(); }")
    pg.wait_for_timeout(600)
    r = pg.evaluate("""()=>{ const withRef = QUESTIONS.filter(q => q.ref), fin = QUESTIONS.filter(q => q.ifc.type === 'chapter_finder');
      const leaks = withRef.filter(q => { const a = String(q.choices[q.answer]); return a.length > 3 && q.ref.toLowerCase().indexOf(a.toLowerCase()) >= 0; });
      return { n: QUESTIONS.length, refs: withRef.length, finderRefs: fin.filter(q => q.ref).length, finders: fin.length, leaks: leaks.length, sample: withRef[0].ref }; }""")
    chk("most Fire Code questions carry a reference line, in the Penal Code's brackets", r["refs"] > r["n"] * 0.8 and r["sample"].startswith("(") and r["sample"].endswith(")"), r)
    chk("the chapter finder shows none (its label is the answer), and no reference contains its question's answer", r["finders"] > 0 and r["finderRefs"] == 0 and r["leaks"] == 0, r)
    u = pg.evaluate("()=>topicsIn(QUESTIONS).find(t=>/Chapter 10/.test(t))")
    rc["start_unit_run"](pg, u); pg.wait_for_selector(".choice", timeout=25000); pg.wait_for_timeout(700)
    s = pg.evaluate("()=>{ const r = document.querySelector('.qpanel .ref'), q = document.querySelector('.qpanel .qtext'); return r && q ? { hidden: r.hidden, text: r.textContent, below: r.getBoundingClientRect().top >= q.getBoundingClientRect().bottom - 2 } : null; }")
    chk("the reference shows under the question text before it is answered", s and not s["hidden"] and s["text"].startswith("(") and s["below"], s)
    # the page viewer, from the county booklet (a county question; no IFC PDF needed)
    pg.evaluate("""()=>{ const it = QUESTIONS.find(q => q.ifc.citation.source === 'amendment' && !q.ifc.citation.blur); window.__it = it; const box = buildIfcRef(it); stage.replaceChildren(box); box.querySelector('details').open = true; }""")
    for _ in range(60):
        if pg.evaluate("()=>!!document.querySelector('.ifc-code .ifc-link')"): break
        pg.wait_for_timeout(250)
    pg.wait_for_timeout(1500)
    pic = pg.evaluate("""()=>{ const h = document.querySelector('.ifc-code-body .ifc-clips'), t = document.querySelector('.ifc-code-body .ifc-county-text');
      return { clips: !!h && !h.hidden && !!h.querySelector('canvas'), textHidden: !!t && t.hidden }; }""")
    chk("an HC Amendments reference opens on the cropped picture, the text one tap away", pic["clips"] and pic["textHidden"], pic)
    g_ = pg.evaluate("()=>ifcGreetingLines().map(l => l.text).join(' | ')")
    chk("Nova's welcome to the class names the 2021 IFC and the HC amendments", "2021 IFC" in g_ and "amendments" in g_, g_)
    pg.evaluate("()=>[...document.querySelectorAll('.ifc-code .ifc-link')].find(x => /whole page/.test(x.textContent)).click()")
    for _ in range(60):
        if pg.evaluate("()=>!!document.querySelector('.ifc-vz-pages canvas')"): break
        pg.wait_for_timeout(250)
    pg.wait_for_timeout(700)
    v = pg.evaluate("""()=>{ const c = document.querySelector('.ifc-vz-card').getBoundingClientRect(), cv = document.querySelector('.ifc-vz-pages canvas');
      return { l: c.left, t: c.top, r: innerWidth - c.right, b: innerHeight - c.bottom, cw: cv.getBoundingClientRect().width, btn: document.querySelector('.ifc-vz-btn.is-in').getBoundingClientRect().height }; }""")
    chk("the whole page opens in a card inset from every edge (the app shows around it), buttons 44px", min(v["l"], v["t"], v["r"], v["b"]) >= 8 and v["btn"] >= 44, v)
    pg.click(".ifc-vz-btn.is-in"); pg.click(".ifc-vz-btn.is-in"); pg.wait_for_timeout(300)
    z = pg.evaluate("()=>document.querySelector('.ifc-vz-pages canvas').getBoundingClientRect().width")
    chk("+ zooms the page (more than twice as wide)", z > v["cw"] * 2, [v["cw"], z])
    pg.dispatch_event(".ifc-vz-scroll", "pointerdown", {"pointerId": 5, "clientX": 100, "clientY": 300, "pointerType": "touch"})
    pg.dispatch_event(".ifc-vz-scroll", "pointerup", {"pointerId": 5, "clientX": 100, "clientY": 300, "pointerType": "touch"})
    pg.dispatch_event(".ifc-vz-scroll", "pointerdown", {"pointerId": 6, "clientX": 100, "clientY": 300, "pointerType": "touch"})
    pg.dispatch_event(".ifc-vz-scroll", "pointerup", {"pointerId": 6, "clientX": 100, "clientY": 300, "pointerType": "touch"})
    pg.wait_for_timeout(300)
    z2 = pg.evaluate("()=>document.querySelector('.ifc-vz-pages canvas').getBoundingClientRect().width")
    chk("a double-tap zooms back out to fit", z2 < z * 0.6, [z, z2])
    pg.click(".ifc-vz-btn.is-done"); pg.wait_for_timeout(600)
    chk("Done closes it", pg.evaluate("()=>!document.querySelector('.ifc-vz')"))
    pg.evaluate("()=>[...document.querySelectorAll('.ifc-code .ifc-link')].find(x => /Enlarge/.test(x.textContent)).click()"); pg.wait_for_timeout(1500)
    chk("Enlarge opens the crop in the same viewer", pg.evaluate("()=>!!document.querySelector('.ifc-vz-pages canvas')"))
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(600)
    chk("leaving the screen closes it", pg.evaluate("()=>!document.querySelector('.ifc-vz')"))
    # the class bubble on a phone: the daily question's mirror, the list opening upward
    pg.evaluate("()=>{ try{ const u=pendingHomeUnlocks(); markUnlocksShown(u.chars,u.banners,u.fx); store.pendingBadgeUnlocks=[]; saveStore(); }catch(e){} document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); showHome(); }")
    pg.wait_for_timeout(2200)
    for _ in range(3):
        pg.evaluate("()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }"); pg.wait_for_timeout(700)
    cb = pg.evaluate("""()=>{ const b = document.querySelector('.class-bubble'), f = document.querySelector('.daily-question-fab');
      if(!b || !f) return null; const a = b.getBoundingClientRect(), c = f.getBoundingClientRect();
      return { dBottom: Math.round(Math.abs(a.bottom - c.bottom)), dSize: Math.round(Math.abs(a.width - c.width)), left: Math.round(a.left), right: Math.round(innerWidth - c.right) }; }""")
    chk("the class bubble stands on the daily question's line, the same size, at the opposite edge", cb and cb["dBottom"] <= 3 and cb["dSize"] <= 2 and abs(cb["left"] - cb["right"]) <= 6, cb)
    pg.evaluate("()=>document.querySelector('.class-bubble').click()"); pg.wait_for_timeout(900)
    up = pg.evaluate("()=>{ const b = document.querySelector('.class-bubble').getBoundingClientRect(), i = document.querySelector('.class-stack-item').getBoundingClientRect(); return { bub: Math.round(b.top), item: Math.round(i.bottom) }; }")
    chk("its list opens upward from the bubble", up["item"] <= up["bub"], up)
    # Start Studying on a big phone, the mode cards, the loading screen on a relaunch
    pg.set_viewport_size({"width": 440, "height": 956}); pg.evaluate("()=>{ showHome(); }"); pg.wait_for_timeout(1500)
    for _ in range(3):
        pg.evaluate("()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }"); pg.wait_for_timeout(500)
    sb = pg.evaluate("()=>{ const r = document.querySelector('.panel.home .playbtn').getBoundingClientRect(); return { w: Math.round(r.width), h: Math.round(r.height) }; }")
    chk("Start Studying on a Pro Max-sized phone is at least 210 x 54 (it had shrunk to 202 x 50)", sb["w"] >= 210 and sb["h"] >= 54, sb)
    pg.evaluate("()=>{ cfg.mode = 'drill'; showModeSelect(); }"); pg.wait_for_timeout(900)
    mc = pg.evaluate("()=>[...document.querySelectorAll('.modecard')].map(c => ({ h: Math.round(c.getBoundingClientRect().height), d: (c.querySelector('.modecarddesc') || {}).textContent || '' }))")
    chk("the four mode cards are at least 130px tall, their descriptions 60-130 characters and none says classmates",
        len(mc) == 4 and all(m["h"] >= 130 and 60 <= len(m["d"]) <= 130 and "classmate" not in m["d"].lower() for m in mc), mc)
    pg.evaluate("()=>{ localStorage.removeItem('class26e.synccode'); }")
    pg.reload(); pg.wait_for_timeout(4800)
    sp = pg.evaluate("()=>{ const s = document.getElementById('splashscreen'); return !s || s.hidden || getComputedStyle(s).display === 'none' || getComputedStyle(s).visibility === 'hidden' || parseFloat(getComputedStyle(s).opacity) === 0; }")
    chk("a relaunch with a saved account but no sync code (the Fire Code class) is past the loading screen by 4.8s", sp, sp)
    br.close()
print("\nALL PASS" if ok else "\nFAILED"); sys.exit(0 if ok else 1)
