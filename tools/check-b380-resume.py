"""Build 380: coming back to a paused test, nothing heavy runs behind the Pause menu.
Madison: "on the iPad, when leaving the app and coming back mid test, the app laps ...
it stutters and the pause menu lags to open". Profiled: launch warm-ups (the badge
pictures) running in 130-640ms slices at 4x CPU behind the Pause menu. Safari has no
requestIdleCallback, so it is taken away here too.
Run:  python3 tools/check-b380-resume.py   (--against: copy the old index.html over first)"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
from playwright.sync_api import sync_playwright
srv, url = g["serve"]()
INIT = """(()=>{ if(localStorage.getItem('class26e.drill.v1')) return;
 localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-0380');
 ['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card','class26e.getstarted'].forEach(k=>localStorage.setItem(k,'1'));
 localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.penal256578.seen','1'); })()"""
d = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]())); d["publicId"] = "pubtest0380r"; d["firstName"] = "Casey"; d["novaMet"] = 99
START = """async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const unit=QUESTIONS[0].topic.trim();
 const idx=QUESTIONS.map((q,i)=>i).filter(i=>(QUESTIONS[i].topic||'').trim()===unit && inWholeUnit(QUESTIONS[i]));
 cfg.source='all'; cfg.mode='drill'; cfg.units=[unit]; beginRun(idx); for(let t=0;t<80&&!document.querySelector('.qpanel .choice');t++) await wait(100); await wait(1500); }"""
# Leave (blur, hidden: the app pauses itself), come back, and a launch warm-up lands while the Pause menu is up.
RUN = """async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms));
 let calls=0; const real=window.badgeStrikeGeometry; window.badgeStrikeGeometry=function(){ calls++; return real.apply(this,arguments); };
 const realE=window.badgeStrikeEntry; window.badgeStrikeEntry=function(){ calls++; return realE.apply(this,arguments); };
 Object.defineProperty(document,'hidden',{configurable:true,get:()=>true}); Object.defineProperty(document,'visibilityState',{configurable:true,get:()=>'hidden'});
 window.dispatchEvent(new Event('blur')); document.dispatchEvent(new Event('visibilitychange'));
 await wait(600); delete document.hidden; delete document.visibilityState;
 document.dispatchEvent(new Event('visibilitychange')); window.dispatchEvent(new Event('focus'));
 const pause=!!document.querySelector('.pausepanel');
 const lt=[]; const po=new PerformanceObserver(l=>l.getEntries().forEach(e=>lt.push(Math.round(e.duration)))); po.observe({type:'longtask'});
 warmBadgeStrikes();
 await wait(5000); const during=calls, tasks=lt.slice(); calls=0;
 /* the test ends: the warm-up goes on */
 testInProgress=false; showHome(); await wait(9000); po.disconnect();
 return {pause, during, tasks, after: calls}; }"""
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else info)
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    for name, (w, h, ins) in {"iPad 11": (834, 1194, (24, 0, 20, 0)), "phone": (440, 956, (62, 0, 34, 0))}.items():
        g["new_page"].w, g["new_page"].h = w, h
        ctx, pg = g["new_page"](br, ins, True, False)
        pg.add_init_script(INIT % json.dumps(json.dumps(d)))
        pg.add_init_script("try{ window.requestIdleCallback = undefined; }catch(e){}")   # Safari
        pg.goto(url); pg.wait_for_timeout(3000); pg.evaluate("document.getElementById('splashscreen')?.remove()")
        pg.evaluate("()=>{ homeUnlocksOwed=()=>false; showHome(); }"); pg.wait_for_timeout(1500)
        pg.evaluate(START)
        r = pg.evaluate(RUN)
        print("  ", name, r)
        chk("%s: leaving mid-test pauses it (%s)" % (name, r["pause"]), r["pause"])
        chk("%s: behind the Pause menu a launch warm-up draws no badges (%d drawings in 5s, tasks over 50ms %s)" % (name, r["during"], r["tasks"]), r["during"] == 0, r)
        chk("%s: and once the test is over it carries on (%d drawings)" % (name, r["after"]), r["after"] > 0, r)
        ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
