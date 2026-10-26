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
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome" if os.path.exists("/opt/pw-browsers/chromium-1194/chrome-linux/chrome") else None
def arg(n, d=None): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d
SRC = arg("--against") or os.path.join(ROOT, "index.html")
TOL = float(arg("--tol", "0.8"))
HTOL = float(arg("--htol", "1.5"))

SEED = ('{"publicId":"xph5b57jbp5a","firstName":"Madison","avatarChar":"ninja","onboardingComplete":true,"leaderboardOptIn":true,"lastModified":1700000000000,'
        '"tourRev":99,"rankMapFx244":true,"seenProfileTour":true,"seenModeSelectTour":true,"seenUnitSelectTour":true,"seenMainMenuTour":true,'
        '"seenRankingsTour":true,"seenAppearanceTour":true,"novaMet":99,"lifetime":{"points":12400,"answered":5400,"correct":4980,"perfectTests":141}}')
CAND = """()=>{ const out=[]; const seen=new Set();
 /* round 33: a pass's ids start at 0 again - last pass's must go, or [data-ink-id] finds a stale control */
 document.querySelectorAll('[data-ink-id]').forEach(n=>n.removeAttribute('data-ink-id'));
 document.querySelectorAll('button, a, [role=button], .back-link, .chip, .rs-mode, .sheet-tag, .iconbtn, .friend-act, .cc-status, .csi-label, .ifc-tag, .ifc-link').forEach(el=>{
   if(seen.has(el)) return; seen.add(el);
   const r=el.getBoundingClientRect(); if(r.width<28||r.height<18||r.height>80) return;
   const cs=getComputedStyle(el); if(cs.visibility==='hidden'||cs.display==='none'||+cs.opacity<.5) return;
   if(r.bottom<0||r.top>innerHeight||r.right<0||r.left>innerWidth) return;
   const t=(el.innerText||'').trim(); if(!t||t.length>26||/[,;()@]/.test(t)||/\\n/.test(t)||/^\\d+$/.test(t)) return;
   /* round 29: a descender only spoils the UP-DOWN measure; across, it counts like any letter */
   const desc=/[gjpqyQ]/.test(t);
   if(el.classList.contains('class-stack-item')||el.closest('.class-bubble-wrap:not(.is-open) .class-stack')) return;
   if(el.classList.contains('bottomtab')||el.classList.contains('cal-cell')) return;
   const hit=document.elementFromPoint(r.left+r.width/2, r.top+r.height/2); if(!hit||!(el===hit||el.contains(hit))) return;
   el.dataset.inkId=String(out.length);
   out.push({id:out.length, t, desc, cls:String((el.className&&el.className.baseVal!==undefined?el.className.baseVal:el.className)||el.tagName), x:r.left,y:r.top,w:r.width,h:r.height});
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
    cands = pg.evaluate(CAND)
    if os.environ.get("INK_LIST") and os.environ["INK_LIST"] in tag: print("  cand", tag, [c["t"] for c in cands], pg.evaluate("()=>[scrollY, document.documentElement.scrollHeight, innerHeight]"))
    for c in cands:
        clip = {"x": c["x"], "y": c["y"], "width": c["w"], "height": c["h"]}
        # round 29: the element's own screenshot, so a scrolled page is measured where it is
        el = pg.query_selector('[data-ink-id="%d"]' % c["id"])
        # round 33: centred first (a screenshot scrolls a control only just into view, under a
        # sticky header), and skipped if anything still lies over its middle
        if not el.evaluate("""e=>{ e.scrollIntoView({block:'center', inline:'nearest', behavior:'instant'}); const r=e.getBoundingClientRect();
             const h=document.elementFromPoint(r.left+r.width/2, r.top+r.height/2); return !!h && (h===e || e.contains(h)); }"""):
            if os.environ.get("INK_SKIPS"): print("  skip", tag, c["t"], el.evaluate("e=>{const r=e.getBoundingClientRect(); const h=document.elementFromPoint(r.left+r.width/2, r.top+r.height/2); return [Math.round(r.top), h && (h.className||h.tagName).toString().slice(0,40)]}"))
            continue
        shot = lambda: el.screenshot()
        a = Image.open(io.BytesIO(shot())).convert("RGB")
        pg.evaluate("""(id)=>{ const el=document.querySelector('[data-ink-id="'+id+'"]');
           /* a pill's arrow keeps the colour it has (it draws in currentColor, which the letters are about to lose) */
           if(el.matches('.stx-allpill, .pf-goal-foot, .pf-case-count')) el.querySelectorAll('svg').forEach(s=>{ s.__sc=s.getAttribute('style')||''; s.style.setProperty('color', getComputedStyle(s).color, 'important'); });
           el.__old=el.getAttribute('style')||'';
           el.style.setProperty('color','transparent','important'); el.style.setProperty('-webkit-text-fill-color','transparent','important'); el.style.setProperty('text-shadow','none','important');
           /* an icon is part of a label's group - except a pill's trailing arrow, which since round 29 sits in its
              padding outside the flow so the WORD is in the middle: there the letters alone are measured */
           if(!el.matches('.stx-allpill, .pf-goal-foot, .pf-case-count')) el.querySelectorAll('svg, img, i').forEach(s=>{ s.__v=s.style.visibility; s.style.visibility='hidden'; });
           /* round 29: a child with its own colour (a pill's inner span) keeps its letters unless it is cleared too */
           el.querySelectorAll('*:not(svg):not(svg *)').forEach(k=>{ k.__c=k.getAttribute('style')||''; k.style.setProperty('color','transparent','important'); k.style.setProperty('-webkit-text-fill-color','transparent','important'); }); }""", c["id"])
        b = Image.open(io.BytesIO(shot())).convert("RGB")
        pg.evaluate("""(id)=>{ const el=document.querySelector('[data-ink-id="'+id+'"]'); el.setAttribute('style', el.__old); el.querySelectorAll('*').forEach(k=>{ if(k.__c!==undefined) k.setAttribute('style', k.__c); }); el.querySelectorAll('svg').forEach(s=>{ if(s.__sc!==undefined){ s.setAttribute('style', s.__sc); delete s.__sc; } }); el.querySelectorAll('svg, img, i').forEach(s=>{ s.style.visibility=s.__v||''; }); }""", c["id"])
        bb = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v > 60 else 0).getbbox()
        if not bb: continue
        sc = a.size[1] / c["h"]
        top, bot = bb[1] / sc, (a.size[1] - bb[3]) / sc
        left, right = bb[0] / sc, (a.size[0] - bb[2]) / sc
        rows.append((tag, c["t"], c["cls"][:36], round(c["h"], 1), 0.0 if c.get("desc") else round((top - bot) / 2, 2), round((left - right) / 2, 2)))

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
            # 327z15 round 29: "a lot of these aren't perfectly centered, fix
            # them all" - the pills he named were below the fold (Profile's
            # See rank ladder and badge case, Stats' Test history) or on
            # screens this never opened (Customize's Change), so each screen
            # is measured at its top AND scrolled to its foot, and Customize
            # and the Calendar are on the list.
            for tag, js in [("home", "showHome()"), ("mode", "showModeSelect()"), ("profile", "showProfile()"), ("leaderboard", "showRankings()"),
                            ("settings", "showAppearance()"), ("stats", "showProfile('stats')"), ("friends", "showFriends()"),
                            ("customize", "showCustomize()"), ("calendar", "showCalendarTab()")]:
                pg.evaluate("()=>" + js); pg.wait_for_timeout(1200); audit(pg, name + " " + tag, rows)
                pg.evaluate("()=>{ document.querySelectorAll('#tour-overlay, #tour-tooltip').forEach(n=>n.remove()); window.scrollTo(0, 99999); }")
                pg.wait_for_timeout(700); audit(pg, name + " " + tag + "/foot", rows)
                pg.evaluate("()=>window.scrollTo(0, 0)")
            # 328: the classes screen, its Enroll / Enrolled chips, the dropdown's labels, the Fire Code tags
            for tag, js in [("classes", "showClassCatalog()"), ("enroll", "showIfcEnroll()")]:
                try:
                    pg.evaluate("()=>" + js); pg.wait_for_timeout(900); audit(pg, name + " " + tag, rows)
                except Exception as e: print("  (could not open %s: %s)" % (tag, str(e)[:60]))
            try:
                pg.evaluate("()=>{ showHome(); }"); pg.wait_for_timeout(900)
                pg.evaluate("()=>{ const b=document.querySelector('.class-bubble'); if(b) b.click(); }"); pg.wait_for_timeout(900); audit(pg, name + " dropdown", rows)
                pg.evaluate("()=>{ const b=document.querySelector('.class-bubble'); if(b) b.click(); }")
            except Exception as e: print("  (dropdown: %s)" % str(e)[:60])
            pg.evaluate("()=>showModeSelect()"); pg.wait_for_timeout(500)
            pg.click(".modecard[data-mode='drill']"); pg.wait_for_timeout(1000); audit(pg, name + " units", rows)
            # 327z15 round 42: "Seems like some of these buttons word aren't centered.
            # Ensure all buttons are good to go" - of a banner's View. The pop-ups were
            # never measured: every banner, the sheets and cards, the chat, the tips.
            CLEAR = ("()=>{ document.querySelectorAll('.app-banner, .daily-alert, .vroom-chat-alert, #intro-pop, #resume-offer, "
                     "#tour-overlay, #tour-tooltip, #tour-line, #tour-line-dot, .invite-overlay, #updatebanner').forEach(n=>n.remove()); "
                     "try{ if(chatDockOpen) closeChatDock(); }catch(e){} }")
            BAN = "(id,k,m,a)=>{ const el=buildAppBanner(id,k,m,a,()=>{},()=>{}); document.body.appendChild(el); placeTopBanner(el); el.classList.add('show'); el.style.transition='none'; }"
            pg.evaluate("()=>showHome()"); pg.wait_for_timeout(900)
            for tag, js in [
                ("banner view", "()=>(" + BAN + ")('friend-request','friend','Alex wants to be friends','View')"),
                ("banner save", "()=>(" + BAN + ")('save-code','account','Save your sync code','Save it')"),
                ("banner join", "()=>(" + BAN + ")('lobby-invite','vroom','Alex invited you to a Virtual Room','Join')"),
                ("banner accept", "()=>(" + BAN + ")('nova-challenge','vroom','Nova challenged you to a match','Accept')"),
                ("whatsnew", "()=>showIntroPopup()"),
                ("update notice", "()=>showUpdateBanner({build:'x'})"),
                ("home notice", "()=>showAddToHomeNotice()"),
                ("frame notice", "()=>showFrameNotice({frameId:'x'})"),
                ("resume", "()=>{ localStorage.setItem(RUN_SESSION_KEY, JSON.stringify({v:1,at:Date.now(),cfg:{mode:'drill',units:[]},runMode:'drill',order:[0,1,2,3],pos:1,answers:{},saved:true})); startStudying(); }"),
                ("tips", "()=>startSimpleTour(mainMenuTourSteps(false), ()=>{})"),
                ("chat", "()=>{ chatDockTab='friends'; openChatDock(); }"),
                ("chat groups", "()=>{ document.querySelector('.chatdock-tab[data-tab=groups]')?.click(); }"),
                ("chat inbox", "()=>{ document.querySelector('.chatdock-tab[data-tab=notifs]')?.click(); }"),
            ]:
                pg.evaluate(js); pg.wait_for_timeout(900); audit(pg, name + " " + tag, rows)
                if not tag.startswith("chat") or tag == "chat inbox":
                    pg.evaluate(CLEAR); pg.wait_for_timeout(300)
            try: pg.evaluate("()=>localStorage.removeItem(RUN_SESSION_KEY)")
            except Exception: pass
            pg.evaluate("()=>{ store.onboardingComplete=false; showWelcome(); }"); pg.wait_for_timeout(1200); audit(pg, name + " welcome", rows)
            pg.evaluate("()=>{ store.onboardingComplete=true; }")
            ctx.close()
        br.close()
    srv.shutdown()
    if os.environ.get("INK_LIST"): [print("   ", r) for r in rows if os.environ["INK_LIST"] in r[0]]
    print("%d controls measured, letters centred within %.1fpx:" % (len(rows), TOL))
    for r in sorted(rows, key=lambda r: -abs(r[4])):
        if abs(r[4]) > TOL: fails.append(r); print("  FAIL %-24s %-16s %-34s h=%-5s letters %+.2fpx %s" % (r[0], r[1], r[2], r[3], r[4], "high" if r[4] < 0 else "low"))
    # and across: a pill whose label (with its icon) sits left or right of the middle
    for r in sorted(rows, key=lambda r: -abs(r[5])):
        if abs(r[5]) > HTOL: fails.append(r); print("  FAIL %-24s %-16s %-34s w-offset %+.2fpx %s" % (r[0], r[1], r[2], r[5], "left" if r[5] < 0 else "right"))
    print("\nALL PASS" if not fails else "\nFAILED: %d" % len(fails))
    sys.exit(1 if fails else 0)

main()
