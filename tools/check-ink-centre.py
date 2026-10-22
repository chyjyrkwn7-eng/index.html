#!/usr/bin/env python3
"""Are the LETTERS in a button centred in it? (build 327, round 9)

Madison, of a Back pill: "It's not centered ... this app will be reviewed for
perfection." A control's box can be perfectly centred and still look wrong,
because a font's letters are not centred in its line box - they sit a pixel
or two high or low, by a different amount in every font. Nothing that
measures boxes can see that, so this measures INK: for each text control it
screenshots the control twice, once as drawn and once with its text made
transparent, and the difference is exactly the letters. The gap above them
and the gap below must match within TOL px.

  python3 tools/check-ink-centre.py [--tol 0.8] [--against FILE]

Controls whose label has a descender (g j p q y Q) are skipped: a descender
hangs below the baseline, so the letters' box is lopsided by design.
Chromium here draws Inter, not the iPhone's San Francisco, so the numbers
are this font's; what the fix uses (text-box: trim-both cap alphabetic)
works from each font's own capital height and baseline, so it centres the
letters in either. Exits non-zero on a failure."""
import functools, http.server, io, os, re, socket, sys, threading
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
def arg(n, d=None): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d
SRC = arg("--against") or os.path.join(ROOT, "index.html")
TOL = float(arg("--tol", "0.8"))
HTOL = float(arg("--htol", "1.5"))

SEED = ('{"firstName":"Madison","avatarChar":"ninja","onboardingComplete":true,"leaderboardOptIn":true,"lastModified":1700000000000,'
        '"tourRev":99,"rankMapFx244":true,"seenProfileTour":true,"seenModeSelectTour":true,"seenUnitSelectTour":true,"seenMainMenuTour":true,'
        '"seenRankingsTour":true,"seenAppearanceTour":true,"novaMet":99,"lifetime":{"points":12400,"answered":5400,"correct":4980,"perfectTests":141}}')
CAND = """()=>{ const out=[]; const seen=new Set();
 document.querySelectorAll('button, a, [role=button], .back-link, .chip, .rs-mode, .sheet-tag, .iconbtn, .friend-act').forEach(el=>{
   if(seen.has(el)) return; seen.add(el);
   const r=el.getBoundingClientRect(); if(r.width<28||r.height<18||r.height>80) return;
   const cs=getComputedStyle(el); if(cs.visibility==='hidden'||cs.display==='none'||+cs.opacity<.5) return;
   if(r.bottom<0||r.top>innerHeight||r.right<0||r.left>innerWidth) return;
   const t=(el.innerText||'').trim(); if(!t||t.length>26||/[gjpqyQ,;()@]/.test(t)||/\\n/.test(t)||/^\\d+$/.test(t)) return;
   if(el.classList.contains('bottomtab')||el.classList.contains('cal-cell')) return;
   const hit=document.elementFromPoint(r.left+r.width/2, r.top+r.height/2); if(!hit||!(el===hit||el.contains(hit))) return;
   el.dataset.inkId=String(out.length);
   out.push({id:out.length, t, cls:String((el.className&&el.className.baseVal!==undefined?el.className.baseVal:el.className)||el.tagName), x:r.left,y:r.top,w:r.width,h:r.height});
 }); return out; }"""

def serve():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    d = os.path.dirname(SRC)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=d))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{port}/" + os.path.basename(SRC)

def audit(pg, tag, rows):
    for c in pg.evaluate(CAND):
        clip = {"x": c["x"], "y": c["y"], "width": c["w"], "height": c["h"]}
        a = Image.open(io.BytesIO(pg.screenshot(clip=clip))).convert("RGB")
        pg.evaluate("""(id)=>{ const el=document.querySelector('[data-ink-id="'+id+'"]'); el.__old=el.getAttribute('style')||'';
           el.style.setProperty('color','transparent','important'); el.style.setProperty('-webkit-text-fill-color','transparent','important'); el.style.setProperty('text-shadow','none','important');
           el.querySelectorAll('svg, img, i').forEach(s=>{ s.__v=s.style.visibility; s.style.visibility='hidden'; }); }""", c["id"])
        b = Image.open(io.BytesIO(pg.screenshot(clip=clip))).convert("RGB")
        pg.evaluate("""(id)=>{ const el=document.querySelector('[data-ink-id="'+id+'"]'); el.setAttribute('style', el.__old); el.querySelectorAll('svg, img, i').forEach(s=>{ s.style.visibility=s.__v||''; }); }""", c["id"])
        bb = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v > 60 else 0).getbbox()
        if not bb: continue
        sc = a.size[1] / c["h"]
        top, bot = bb[1] / sc, (a.size[1] - bb[3]) / sc
        left, right = bb[0] / sc, (a.size[0] - bb[2]) / sc
        rows.append((tag, c["t"], c["cls"][:36], round(c["h"], 1), round((top - bot) / 2, 2), round((left - right) / 2, 2)))

def main():
    rows = []; fails = []
    srv, url = serve()
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME)
        for (W, H, ins, name) in [(440, 956, (62, 0, 34, 0), "17 Pro Max"), (834, 1194, (24, 0, 20, 0), "iPad Pro 11")]:
            ctx = br.new_context(viewport={"width": W, "height": H}, device_scale_factor=2)
            ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.drill.v1', '%s');"
                                "localStorage.setItem('class26e.synccode','MADI-0001');localStorage.setItem('class26e.frame.ok','go-live-1');"
                                "localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');"
                                "localStorage.setItem('class26e.daily.seen','x');localStorage.setItem('class26e.savecode.asked','1');}catch(e){}" % SEED)
            ctx.route("**/version.json", lambda r, req: r.fulfill(status=200, content_type="application/json",
                      body='{"build":"%s"}' % (re.search(r'APP_BUILD\s*=\s*"([^"]+)"', open(SRC, encoding="utf-8").read()) or [0, ""])[1]))
            pg = ctx.new_page()
            pg.goto(url); pg.wait_for_timeout(2500)
            pg.evaluate("document.getElementById('splashscreen')?.remove()"); pg.wait_for_timeout(500)
            pg.evaluate("()=>{ try{ const u=pendingHomeUnlocks(); markUnlocksShown(u.chars,u.banners,u.fx); }catch(e){} store.novaMet=99; saveStore(); }")
            for tag, js in [("home", "showHome()"), ("mode", "showModeSelect()"), ("profile", "showProfile()"), ("leaderboard", "showRankings()"),
                            ("settings", "showAppearance()"), ("stats", "showProfile('stats')"), ("friends", "showFriends()")]:
                pg.evaluate("()=>" + js); pg.wait_for_timeout(1200); audit(pg, name + " " + tag, rows)
            pg.evaluate("()=>showModeSelect()"); pg.wait_for_timeout(500)
            pg.click(".modecard[data-mode='drill']"); pg.wait_for_timeout(1000); audit(pg, name + " units", rows)
            ctx.close()
        br.close()
    srv.shutdown()
    print("%d controls measured, letters centred within %.1fpx:" % (len(rows), TOL))
    for r in sorted(rows, key=lambda r: -abs(r[4])):
        if abs(r[4]) > TOL: fails.append(r); print("  FAIL %-24s %-16s %-34s h=%-5s letters %+.2fpx %s" % (r[0], r[1], r[2], r[3], r[4], "high" if r[4] < 0 else "low"))
    # and across: a pill whose label (with its icon) sits left or right of the middle
    for r in sorted(rows, key=lambda r: -abs(r[5])):
        if abs(r[5]) > HTOL: fails.append(r); print("  FAIL %-24s %-16s %-34s w-offset %+.2fpx %s" % (r[0], r[1], r[2], r[5], "left" if r[5] < 0 else "right"))
    print("\nALL PASS" if not fails else "\nFAILED: %d" % len(fails))
    sys.exit(1 if fails else 0)

main()
