"""Build 381: the trophy without its star, "Search names" centred, the tab bar's slide at the screen's rate.
Madison: "I don't like the leaderboards icon with the star in the middle"; "The word search names is not
centered for leaderboard search"; "The tapping of the bottom tab is really really good now, however the
sliding is now the problem, it's okay but not perfect like the tapping."
Run:  python3 tools/check-b381.py   (--against: copy the old index.html over first)"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
from playwright.sync_api import sync_playwright
srv, url = g["serve"]()
INIT = """(()=>{ if(localStorage.getItem('class26e.drill.v1')) return;
 localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-0381');
 ['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.getstarted'].forEach(k=>localStorage.setItem(k,'1'));
 localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.penal256578.seen','1'); })()"""
d = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]())); d["publicId"] = "pubtest0381"; d["firstName"] = "Casey"; d["novaMet"] = 99
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else info)
def page(br, w, h, ins, touch=False):
    if not touch:
        g["new_page"].w, g["new_page"].h = w, h
        ctx, pg = g["new_page"](br, ins, True, False)
    else:
        ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=3, has_touch=True, is_mobile=True)
        ctx.add_init_script(g["STANDALONE"]); ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]()))
        pg = ctx.new_page(); body = g["patched"](ins)
        pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
        pg.add_init_script(g["STATUS_BAR"].replace("__H__", str(ins[0])))
    pg.add_init_script(INIT % json.dumps(json.dumps(d)))
    pg.goto(url); pg.wait_for_timeout(3000); pg.evaluate("document.getElementById('splashscreen')?.remove()")
    pg.evaluate("()=>{ homeUnlocksOwed=()=>false; }")
    return ctx, pg
# (1) the trophy: its middle, where the star was, is filled
TROPHY = """()=>{ const t=document.getElementById('bottomtab-rewards'); const p=t && t.querySelector('svg path.tg-cup'); if(!p) return null;
 const pts=[[12,7.4],[11.6,6.6],[12.4,6.6],[12,8.6]]; return {filled: pts.map(([x,y])=>{ const q=p.ownerSVGElement.createSVGPoint(); q.x=x; q.y=y; return p.isPointInFill(q); }),
   rim: (()=>{ const q=p.ownerSVGElement.createSVGPoint(); q.x=12; q.y=3.2; return p.isPointInFill(q); })(), paths: t.querySelectorAll('svg path').length}; }"""
# (2) the placeholder's middle against the field's
SEARCH = """()=>{ const i=document.querySelector('.rank-search'); const r=i.getBoundingClientRect(); const cs=getComputedStyle(i);
 const c=document.createElement('canvas').getContext('2d'); c.font=cs.fontWeight+' '+cs.fontSize+' '+cs.fontFamily; const tw=c.measureText(i.placeholder).width;
 const bl=parseFloat(cs.borderLeftWidth), pl=parseFloat(cs.paddingLeft), pr=parseFloat(cs.paddingRight); const cw=r.width-pl-pr-bl-parseFloat(cs.borderRightWidth);
 const al=cs.textAlign; const left = al==='center' ? r.left+bl+pl+(cw-tw)/2 : (al==='right'||al==='end') ? r.left+bl+pl+cw-tw : r.left+bl+pl;
 const ic=document.querySelector('.rank-search-wrap > .searchicon').getBoundingClientRect();
 return {off: Math.round((left+tw/2)-(r.left+r.width/2)), fits: tw<=cw+.5, clearOfIcon: left >= ic.right - .5, w: Math.round(r.width)}; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    for name, (w, h, ins) in {"phone": (440, 956, (62, 0, 34, 0)), "Pro Max at 85%": (518, 1125, (73, 0, 40, 0)),
                              "SE": (375, 667, (20, 0, 0, 0)), "iPad 11": (834, 1194, (24, 0, 20, 0))}.items():
        ctx, pg = page(br, w, h, ins)
        pg.evaluate("()=>showRankings()"); pg.wait_for_timeout(2500)
        if name == "phone":
            t = pg.evaluate(TROPHY)
            chk("the Leaderboard tab's trophy is one solid piece with no star cut out of its middle (%s)" % (t,),
                t and all(t["filled"]) and not t["rim"] is None and t["paths"] == 1, t)
        s = pg.evaluate(SEARCH)
        if name == "SE":
            chk("on an SE \"Search names\" still fits whole and clear of the magnifier (%s)" % (s,), s["fits"] and s["clearOfIcon"], s)
        else:
            chk("on %s \"Search names\" sits on the field's middle (%d px off) and fits (%s)" % (name, s["off"], s["fits"]),
                abs(s["off"]) <= 1 and s["fits"] and s["clearOfIcon"], s)
        ctx.close()
    # (3) a slide with a real finger: the lens's moving parts carry a one-frame transition while it follows, none after
    ctx, pg = page(br, 440, 956, (62, 0, 34, 0), touch=True)
    pg.evaluate("()=>showProfile()"); pg.wait_for_timeout(3000)
    cdp = ctx.new_cdp_session(pg)
    tabs = pg.evaluate("()=>[...document.querySelectorAll('#bottomtabs .bottomtab')].map(t=>{const r=t.getBoundingClientRect(); return [t.id, t.classList.contains('active'), Math.round(r.left+r.width/2), Math.round(r.top+r.height/2)];})")
    lit = [t for t in tabs if t[1]][0]; far = [t for t in tabs if t[0] == "bottomtab-calendar"][0]
    LENSTX = "()=>[...document.querySelectorAll('#bottomtabs-lens *')].filter(e=>e.style && e.style.transition).map(e=>e.style.transition).slice(0,6)"
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": lit[2], "y": lit[3]}]})
    during = []
    for i in range(1, 31):
        x = lit[2] + (far[2] - lit[2]) * i / 30
        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x, "y": lit[3]}]}); time.sleep(0.016)
        if i in (15, 28): during.append(pg.evaluate(LENSTX))
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    pg.wait_for_timeout(1500)
    after = pg.evaluate(LENSTX)
    landed = pg.evaluate("()=>[!!document.querySelector('.screen-calendar-tab'), (document.querySelector('#bottomtabs .bottomtab.active')||{}).id]")
    import re
    ms = [int(m) for lst in during for t in lst for m in re.findall(r"transform (\d+)ms linear", t)]
    # REVERSED ON PURPOSE IN BUILD 382: the one-frame transition put the glass a frame behind every position ("behind the finger");
    # the lens is written exactly where the finger is (plus a small lead) and carries no transition while it follows (check-b382-slide)
    chk("while a finger slides, the lens's moving parts carry no transition - each position is drawn as written (%s)" % (during,),
        len(during) == 2 and not ms and not any("transform" in t for lst in during for t in lst), during)
    chk("and once it is let go they carry none (%s), and the slide landed on the tab let go over (%s)" % (after, landed),
        not any("linear" in t for t in after) and landed[0] and landed[1] == "bottomtab-calendar", [after, landed])
    ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
