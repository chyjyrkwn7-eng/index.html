#!/usr/bin/env python3
"""Study time counts time spent studying, not time a run was open (build 314).

A test left open with the phone locked banked every hour until it was
finished - one live test of 117 hours, days of 68 and 118. Usage:
  python3 tools/check-study-time.py [--against old-index.html]
Exits non-zero on any failure. Written against the build it failed on."""
import sys, threading, http.server, functools, json
from playwright.sync_api import sync_playwright
import os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
page = "index.html"
if "--against" in sys.argv:
    page = os.path.relpath(os.path.abspath(sys.argv[sys.argv.index("--against") + 1]), root)
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
srv=http.server.ThreadingHTTPServer(("127.0.0.1",0),functools.partial(Q,directory=root)); threading.Thread(target=srv.serve_forever,daemon=True).start()
seed={"onboardingComplete":True,"firstName":"T","tourRev":99,"seenProfileTour":True,"seenRewardsTour":True,"seenSettingsTour":True,"lifetime":{"points":5000},"studyLog":{}}
with sync_playwright() as pw:
    br=pw.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome",args=["--no-sandbox"])
    pg=br.new_page(); errs=[]; pg.on("pageerror",lambda e: errs.append(str(e)[:200]))
    pg.add_init_script("localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.intro.seen','1');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.drill.v1',%s)"%json.dumps(json.dumps(seed)))
    pg.goto("http://127.0.0.1:%d/%s"%(srv.server_address[1], page)); pg.wait_for_timeout(2500)
    try:
      r = pg.evaluate("""()=>{
      document.getElementById('splashscreen')?.remove();
      const H = 3600000, day = () => store.studyLog[dayKey(new Date())] || 0;
      const out = {};
      // 1. left open: started 3h ago, last input 3h ago, nothing since
      store.studyLog = {}; runStartTime = Date.now() - 3*H; studyActiveAt = runStartTime; studyIdleMs = 0;
      out.leftOpen = { elapsedReturned: flushStudyTime(), credited: day() };
      // 2. steady studying: 40 minutes, an input every 2 minutes
      store.studyLog = {}; const t0 = Date.now() - 40*60000; runStartTime = t0; studyActiveAt = t0; studyIdleMs = 0;
      const realNow = Date.now; let fake = t0;
      Date.now = () => fake;
      for(let m = 2; m <= 40; m += 2){ fake = t0 + m*60000; noteStudyActivity(); }
      Date.now = realNow;
      flushStudyTime();
      out.steady = { credited: day(), minutes: Math.round(day()/60000) };
      // 2b. reading slowly: one input every 4 minutes for 40 minutes still counts in full
      store.studyLog = {}; const r0 = Date.now() - 40*60000; runStartTime = r0; studyActiveAt = r0; studyIdleMs = 0;
      fake = r0; Date.now = () => fake;
      for(let m = 4; m <= 40; m += 4){ fake = r0 + m*60000; noteStudyActivity(); }
      Date.now = realNow; flushStudyTime();
      out.slowReader = { minutes: Math.round(day()/60000) };
      // 3. studied 20 min, then phone locked 2 days, then came back and left via Profile
      store.studyLog = {}; const s0 = Date.now() - 48*H - 20*60000; runStartTime = s0; studyActiveAt = s0 + 20*60000; studyIdleMs = 0;
      out.abandoned = { credited: day() || (flushStudyTime(), day()) };
      // 4. paused for an hour mid-run is not idle twice
      store.studyLog = {}; const p0 = Date.now() - 70*60000; runStartTime = p0; studyActiveAt = p0 + 10*60000; studyIdleMs = 0;
      paused = true; pauseStartedAt = Date.now() - 60*60000; cancelPauseTiming();
      out.paused = { credited: (flushStudyTime(), day()) };
      // 5. day ceiling
      store.studyLog = {}; addStudyTime(30*H); out.ceiling = day();
      return out; }""")
    except Exception as e:
      r = None; print("FAIL: threw", str(e)[:160])
    H = 3600000; fails = []
    def check(name, ok, got):
        print(("  PASS " if ok else "  FAIL ") + name + "  -> " + str(got))
        if not ok: fails.append(name)
    if r:
        check("a run left open 3 hours credits only the 5-minute idle allowance", r["leftOpen"]["credited"] == 300000, r["leftOpen"])
        check("and still reports its real elapsed time to results", r["leftOpen"]["elapsedReturned"] == 3 * H, r["leftOpen"])
        check("40 minutes of steady study counts 40", r["steady"]["minutes"] == 40, r["steady"])
        check("a slow reader (an input every 4 minutes) still counts in full", r["slowReader"]["minutes"] == 40, r["slowReader"])
        check("20 minutes then 2 days locked counts 25", r["abandoned"]["credited"] == 1500000, r["abandoned"])
        check("a pause is not taken out twice", r["paused"]["credited"] == 600000, r["paused"])
        check("no day holds more than 16 hours", r["ceiling"] == 16 * H, r["ceiling"])
    else:
        fails.append("probe")
    print("errors", [e for e in errs if 'firebase' not in e.lower()][:3])
    br.close()
srv.shutdown()
print("ALL PASS" if not fails else "FAILED: %d" % len(fails))
sys.exit(1 if fails else 0)
