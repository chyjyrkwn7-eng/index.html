"""Build 328: another class, for one account (NOVA_CLASS, mountClassBubble, switchClass).

Owner (publicId xph5b57jbp5a): the class bubble is on Home; switching to Fire Code reloads
into a copy that starts at zero with the same name, stays off the leaderboard, has no cloud
and no sync code, keeps its own class26e.ifc.* keys and ifc: IndexedDB, leaves the academy's
saved copy byte-for-byte as it was, and switching back finds the academy as it was.
A classmate: no bubble, and setting class26e.activeclass by hand changes nothing.
"""
import json
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
from playwright.sync_api import sync_playwright
srv, url = g["serve"]()
def seed(pid):
    d = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]())); d["publicId"]=pid; d["firstName"]="Maddog"; d["novaMet"]=99
    return json.dumps(d)
INIT = """(()=>{ if(localStorage.getItem('class26e.drill.v1')) return;
 localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-0001');
 ['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked'].forEach(k=>localStorage.setItem(k,'1'));
 localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.penal256578.seen','1'); })()"""
ok=True
def chk(name, cond, info=""):
    global ok; ok = ok and cond; print(("PASS " if cond else "FAIL ")+name, info if not cond else "")
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    for who,pid in (("owner","xph5b57jbp5a"),("classmate","abc123classmt")):
        g["new_page"].w, g["new_page"].h = 393, 852
        ctx, page = g["new_page"](br, (59,0,34,0), True, False)
        page.add_init_script(INIT % json.dumps(seed(pid)))
        errs=[]; page.on("pageerror", lambda e: errs.append(str(e)[:150]))
        page.goto(url); page.wait_for_timeout(3500)
        page.evaluate("document.getElementById('splashscreen')?.remove()")
        page.evaluate("()=>{ homeUnlocksOwed=()=>false; showHome(); }"); page.wait_for_timeout(1200)
        has = page.evaluate("()=>!!document.querySelector('.class-bubble')")
        if who=="classmate":
            chk("classmate: no class bubble", not has)
            page.evaluate("()=>localStorage.setItem('class26e.activeclass','ifc')"); page.reload(); page.wait_for_timeout(3500)
            st = page.evaluate("()=>({cls:window.NOVA_CLASS, key:localStorage.getItem('class26e.activeclass'), pts:store.lifetime.points})")
            chk("classmate forcing the key stays in the academy, key cleared", st["cls"]=="academy" and st["key"] is None and st["pts"]==12400, st)
            chk("no page errors", not errs, errs[:3]); ctx.close(); continue
        chk("owner: class bubble on Home", has)
        before = page.evaluate("()=>localStorage.getItem('class26e.drill.v1')")
        page.click(".class-bubble"); page.wait_for_timeout(500)
        page.click(".class-menu-row.is-ifc"); page.wait_for_timeout(4500)
        page.evaluate("document.getElementById('splashscreen')?.remove()")
        page.evaluate("()=>{ try{ showHome(); }catch(e){} }"); page.wait_for_timeout(1500)
        st = page.evaluate("""()=>({cls:window.NOVA_CLASS, pts:store.lifetime.points, ans:store.lifetime.answered, name:store.firstName, pid:store.publicId,
           onb:store.onboardingComplete, lb:store.leaderboardOptIn, fb:fbDb, code:syncCode, q:QUESTIONS.length,
           ifcKey:!!Storage.prototype.getItem.call(localStorage,'class26e.drill.v1'), icon:document.querySelector('.class-bubble')?.className,
           home:!!document.querySelector('.panel.home')})""")
        chk("in Fire Code: class is ifc", st["cls"]=="ifc", st)
        chk("Fire Code starts at zero (points/answered)", st["pts"]==0 and st["ans"]==0, st)
        chk("same person: name + publicId, onboarding done", st["name"]=="Maddog" and st["pid"]=="xph5b57jbp5a" and st["onb"] is True, st)
        chk("off the leaderboard, no cloud, no sync code", st["lb"] is False and st["fb"] is None and st["code"] is None, st)
        chk("Home shows with the flame bubble", st["home"] and "is-ifc" in (st["icon"] or ""), st)
        page.click("#nextbtn"); page.wait_for_timeout(700)
        toast = page.evaluate("()=>document.getElementById('toast')?.textContent||''")
        chk("Start Studying with no questions yet says so", "not been added" in toast, toast)
        # the academy's copy, untouched (read raw, past the shim)
        raw = page.evaluate("""()=>{ const k='class26e.drill.v1'; const n=localStorage.length; for(let i=0;i<n;i++){ if(localStorage.key(i)===k) return localStorage[k]; } return null; }""")
        chk("academy's saved copy byte-for-byte unchanged", raw==before)
        keys = page.evaluate("()=>{const o=[];for(let i=0;i<localStorage.length;i++)o.push(localStorage.key(i));return o.sort()}")
        chk("Fire Code keeps its own keys", "class26e.ifc.drill.v1" in keys and "class26e.ifc.synccode" not in keys, keys)
        dbs = page.evaluate("async()=> (await indexedDB.databases()).map(d=>d.name)")
        print("   IndexedDB:", dbs)
        # back
        page.click(".class-bubble"); page.wait_for_timeout(500)
        page.click(".class-menu-row.is-academy"); page.wait_for_timeout(4500)
        st2 = page.evaluate("()=>({cls:window.NOVA_CLASS, pts:store.lifetime.points, code:syncCode, raw:localStorage.getItem('class26e.drill.v1')})")
        chk("back in the academy with its progress and code", st2["cls"]=="academy" and st2["pts"]==12400 and st2["code"]=="TEST-0001", {k:st2[k] for k in ("cls","pts","code")})
        chk("no page errors", not errs, errs[:3])
        ctx.close()
    srv.shutdown()
print("ALL PASS" if ok else "FAILURES"); sys.exit(0 if ok else 1)
