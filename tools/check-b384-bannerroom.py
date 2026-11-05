#!/usr/bin/env python3
"""Build 384 final check: a top banner never strands another one mid-screen.

Madison, off a frame of the class-switch video: "Why is the pop up showing in the middle?" The "It's out" banner had arrived while
"Welcome back to Fire Code" was up, so settleTopBanner() pushed it below that one (218px down, over the planet); when "Welcome
back" left, nothing moved it back - settleTopBanner() only ever moves a banner down. The recorder's own setup made the rest of
that video wrong (an iPhone Safari tab at the installed app's full height, which lifts the tab bar clear of a Safari toolbar the
video does not show); the videos are recorded as the installed app now.
On an installed iPhone 17 Pro Max:
(1) a lone banner's place is measured first (under the chat button);
(2) a second banner shown while one is up sits under it - and when the first leaves on its own timer, the second slides back to
    the lone banner's place (within 2px, within a second);
(3) "It's out" - the daily question coming due on Home while "Welcome back to the Police Academy" is up - waits for that banner
    to go, never stacking under it, and then takes the lone banner's place;
(4) no page errors.
  python3 tools/check-b384-bannerroom.py [--against OLD/index.html]   (must FAIL on the build before)"""
import os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b381-class.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b381-class.py"), "__name__": "b384br"}
exec(src, G)
g = G["g"]
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = g["INSET_RE"]
    def _old(ins):
        t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
        return IR.sub(lambda m: v[m.group(1)], OLD)
    g["patched"] = _old
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)
TOP = "(id)=>{ const e=document.getElementById(id); if(!e || !e.isConnected) return null; return Math.round(e.getBoundingClientRect().top); }"
CLASSBACK = """(stay)=>{ const ic=document.createElement('span'); ic.innerHTML='<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/></svg>';
  showDailyAlert('Class 26E', { kind: 'enrolled', tag: 'YOUR CLASS', title: 'Welcome back to the Police Academy', color: '#93B5FF', iconEl: ic.firstElementChild, id: 'classback-banner', stay: stay }); }"""
CLEAR = "()=>{ document.querySelectorAll('.daily-alert, .app-banner, .rs-spot, .unlock-card, #tour-overlay, #tour-tooltip').forEach(n=>n.remove()); }"
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    ctx, pg, cdp = G["page"](br, 440, 956, (62, 0, 34, 0), True)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    pg.wait_for_timeout(5000)   # the page's own "It's out" comes and is cleared
    pg.evaluate(CLEAR); pg.wait_for_timeout(400)
    # (1) a lone banner's place
    pg.evaluate("()=>showDailyAlert('Lone - a banner by itself', { stay: 60000 })"); pg.wait_for_timeout(700)
    lone = pg.evaluate(TOP, "dailyalert")
    pg.evaluate(CLEAR); pg.wait_for_timeout(400)
    chk("(1) a lone banner sits at %spx (under the chat button)" % lone, lone is not None and 60 < lone < 200, lone)
    # (2) stacked, then the upper one leaves on its own timer
    pg.evaluate(CLASSBACK, 1600); pg.wait_for_timeout(500)
    pg.evaluate("()=>showDailyAlert('Second - shown while the first is up', { stay: 60000 })"); pg.wait_for_timeout(500)
    first, second = pg.evaluate(TOP, "classback-banner"), pg.evaluate(TOP, "dailyalert")
    gone_at, after = None, []
    t0 = time.time()
    while time.time() - t0 < 6:
        a = pg.evaluate(TOP, "classback-banner"); b = pg.evaluate(TOP, "dailyalert")
        if a is None and gone_at is None: gone_at = time.time()
        if gone_at is not None: after.append((round(time.time() - gone_at, 2), b))
        pg.wait_for_timeout(100)
    settled = [t for t, v in after if v is not None and lone is not None and abs(v - lone) <= 2]
    chk("(2) the second banner sat under the first (%s under %s) and, once the first had gone, came back to the lone place (%s)"
        % (second, first, after[-1] if after else None),
        first is not None and second is not None and second > first and bool(settled) and settled[0] <= 1.0 and abs(after[-1][1] - lone) <= 2, [first, second, after[:12]])
    pg.evaluate(CLEAR); pg.wait_for_timeout(400)
    # (3) "It's out" coming due while "Welcome back" is up
    pg.evaluate("()=>{ try{ localStorage.setItem('class26e.daily.seen', '1'); }catch(e){} showHome(); }")
    pg.wait_for_timeout(250)
    pg.evaluate(CLEAR); pg.evaluate(CLASSBACK, 9000)   # up long enough that the question comes due under it
    log, t0 = [], time.time()
    while time.time() - t0 < 18:
        a = pg.evaluate(TOP, "classback-banner"); b = pg.evaluate(TOP, "dailyalert")
        log.append((round(time.time() - t0, 1), a, b)); pg.wait_for_timeout(150)
    # pushed under it (its top below the other's, by a banner's height) - not the last tenth of a second of "Welcome back"
    # sliding up and out above it as "It's out" arrives in its own place
    stacked = [x for x in log if x[1] is not None and x[2] is not None and x[2] >= x[1] + 40]
    shown = [x for x in log if x[2] is not None]
    chk("(3) \"It's out\" waited for \"Welcome back\" to go (stacked under it %d times) and then sat at the lone place (%s, lone %s)"
        % (len(stacked), shown[0] if shown else None, lone),
        not stacked and bool(shown) and lone is not None and abs(shown[0][2] - lone) <= 2, [stacked[:3], shown[:3], log[::8]])
    chk("(4) no page errors", not errs, errs[:3])
    br.close()
G["srv"].shutdown()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
