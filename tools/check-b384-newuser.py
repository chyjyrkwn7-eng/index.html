"""384.137 (videos): what a new person sees - two faults found by watching the new-user videos frame by frame
(tools/record-b384-newuser.py), each read off the page.

 bar     - A NEW ACCOUNT'S FIRST HOME KEEPS ITS TAB BAR FROM GENERATING PROFILE TO NOVA. GENERATING PROFILE fades over a whole Home
           with its bar (round 37), the overlay goes, Home holds on its own for HOME_HOLD_BEFORE_NOVA_MS, then Nova comes in. The
           bar's rule (syncVisibility) kept it only while the overlay or Nova was up, so in that beat it blinked out (on, gone
           ~1.1s, back under Nova). A fresh device, iPhone 17 Pro Max (440x956), the real sign-up (Select your classes, the
           academy, Continue, Enroll), every frame from Enroll until Nova is up:
           (1) the overlay came and went, Home was under it, Nova came after a beat of Home on its own (0.5s+);
           (2) from Home's first frame to Nova's the tab bar is never hidden and has its height.
 switch  - NO BANNER DROPS INTO A CLASS SWITCH. In the switch video the daily question's "It's out" banner (which waits out the
           "Welcome back" banner) came due as the class was tapped and dropped in at the top, with its chime, as the cover faded
           in. An account in both classes on the academy's Home (installed iPhone), the class button and Fire Code tapped for
           real, the reload held off (so the cover stays up): while it is up, the daily question's announcement and a plain
           banner are asked for -
           (3) no banner is shown and the daily chime is not played;
           (4) the cover is up the whole time (the switch itself is untouched).
 (5) no page errors, either section.
Run:  python3 tools/check-b384-newuser.py [bar switch] [--against OLD/index.html]   (--against 1cb2318's index.html FAILS (2) and (3))"""
import os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
ARGS = [a for a in sys.argv[1:] if not a.startswith("--") and not a.endswith(".html")]
AGAINST = sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else None
want = lambda k: not ARGS or k in ARGS
src = open(os.path.join(HERE, "check-b382-savecode.py")).read().split("\nwith sync_playwright() as pw:")[0]
g = {"__file__": os.path.join(HERE, "check-b382-savecode.py"), "__name__": "b384nu"}
exec(src, g)    # (it reads --against itself, for the sign-up page)
from playwright.sync_api import sync_playwright
fails = g["fails"] = []
ck = g["ck"]
LOG = r"""()=>{ window.__bar = []; const t0 = performance.now();
  const tick = () => {
    const b = document.getElementById('bottomtabs'), r = b ? b.getBoundingClientRect() : null;
    window.__bar.push({ t: Math.round(performance.now() - t0), ov: !!document.getElementById('genprofile-overlay'),
      home: !!document.querySelector('#stage .screen-home-actual'), nova: !!document.getElementById('nova-intro'),
      hidden: !b || b.hidden, h: r ? Math.round(r.height) : 0 });
    if(window.__bar.length < 4000) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick); }"""

with sync_playwright() as pw:
    if want("bar"):
        print("\nbar: a new account's first Home keeps its tab bar until Nova")
        br = pw.chromium.launch(executable_path=g["CHROME"])
        errs = []
        ctx, pg = g["open_page"](br, g["SEEN"], errs=errs)
        pg.evaluate("()=>{ document.querySelectorAll('.intro-popup,.daily-alert,#intro-pop,.nova-talk,.app-banner').forEach(e=>e.remove()); showClassSelection(); }")
        pg.wait_for_timeout(1200)
        pg.click(".classselect-panel .class-card.is-academy"); pg.wait_for_timeout(400)
        pg.click(".classselect-panel #nextbtn"); pg.wait_for_timeout(700)
        pg.evaluate(LOG)
        pg.click("#classenroll-confirm .classenroll-yes")
        for _ in range(160):
            pg.wait_for_timeout(250)
            if pg.evaluate("()=>!!document.getElementById('nova-intro')"): break
        pg.wait_for_timeout(600)
        log = pg.evaluate("()=>window.__bar")
        ov = [e for e in log if e["ov"]]
        first_home = next((i for i, e in enumerate(log) if e["home"]), None)
        nova_at = next((i for i, e in enumerate(log) if e["nova"]), None)
        hold = [e for e in log[first_home or 0:nova_at or 0] if not e["ov"] and e["home"] and not e["nova"]]
        hold_ms = (hold[-1]["t"] - hold[0]["t"]) if len(hold) > 1 else 0
        ck("(1) the overlay came (%d frames) and went, Home under it, Nova after a beat of Home alone (%dms)" % (len(ov), hold_ms),
           bool(ov) and first_home is not None and nova_at is not None and first_home < nova_at and hold_ms >= 500,
           {"frames": len(log), "first_home": first_home, "nova_at": nova_at})
        span = log[first_home:nova_at + 1] if first_home is not None and nova_at is not None else []
        off = [e for e in span if e["hidden"] or e["h"] < 40]
        ck("(2) from Home's first frame to Nova's, the tab bar is never hidden (%d of %d frames without it%s)"
           % (len(off), len(span), (", first at %dms, overlay %s" % (off[0]["t"], "up" if off[0]["ov"] else "gone")) if off else ""),
           bool(span) and not off, off[:3])
        ck("(5) bar: no page errors", not errs, errs[:3])
        br.close()

    if want("switch"):
        print("\nswitch: no banner drops into a class switch")
        sys.path.insert(0, HERE)
        import b384_switchfx_lib as L
        srv = L.Server(src_path=os.path.abspath(AGAINST) if AGAINST else None, no_reload=True)
        s = L.Session(pw, srv, "phone").boot()
        pg = s.pg
        L.ev(pg, "()=>{ window.__plays = []; const P = NovaSound.play; NovaSound.play = (id, o) => { window.__plays.push(id); return P(id, o); };"
                 " document.querySelectorAll('.daily-alert,.app-banner').forEach(e => e.remove()); }")
        s.tap(".class-bubble"); pg.wait_for_timeout(900)
        s.tap(".class-stack-item.is-ifc"); pg.wait_for_timeout(350)
        before = L.ev(pg, "()=>({ sw: document.documentElement.classList.contains('class-switching'), cover: !!document.getElementById('class-switch-loader') })")
        # what came due in that moment on the video: the daily question's announcement (its recharge, chime and banner) and a banner
        L.ev(pg, """()=>{ const b = document.querySelector('.daily-question-fab');
          try{ if(b) announceDailyReset(b); }catch(e){ window.__annErr = String(e); }
          try{ showDailyAlert('Welcome back \\u2014 test banner', { kind: 'enrolled', tag: 'TEST' }); }catch(e){ window.__bErr = String(e); } }""")
        seen, cover_all = [], True
        for _ in range(24):
            pg.wait_for_timeout(200)
            st = L.ev(pg, "()=>({ ban: [...document.querySelectorAll('.daily-alert, .app-banner')].filter(e => e.isConnected && e.getBoundingClientRect().height > 0).map(e => e.id || e.className), cover: !!document.getElementById('class-switch-loader') })")
            seen += st["ban"]; cover_all = cover_all and st["cover"]
        plays = L.ev(pg, "()=>window.__plays.slice()")
        ck("(3) while the switch is under way no banner is shown (%s) and the daily chime is not played (%s)" % (sorted(set(seen)) or "none", [p for p in plays if "daily" in p] or "none"),
           before["sw"] and not seen and not any("daily" in p for p in plays), {"before": before, "plays": plays})
        ck("(4) the cover was up from the tap to the end (%s)" % cover_all, before["cover"] and cover_all, before)
        ck("(5) switch: no page errors", not [e for e in s.errs if "console:" not in e], s.errs[:3])
        s.close(); srv.close()
print("\nALL PASS" if not fails else "\nFAILED: %d" % len(fails))
sys.exit(1 if fails else 0)
