"""Build 382: the units search rides above the keyboard; a drag-select's auto-scroll stops when the finger lifts.
Madison (two recordings): "Tapping the search button while looking at units, the search bar isn't properly pulling up" and
"the screens are automatically scrolling down". The field's lift was computed from its box mid-transition; the drag-select's
auto-scroll stopped only on a pointerup its list heard, which an iPhone does not send when a native switch took the touch.
Run:  python3 tools/check-b382-input.py   (--against: copy the old index.html over first)"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
from playwright.sync_api import sync_playwright
srv, url = g["serve"]()
INIT = """(()=>{ if(localStorage.getItem('class26e.drill.v1')) return;
 localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-0382');
 ['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.getstarted'].forEach(k=>localStorage.setItem(k,'1'));
 localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.penal256578.seen','1'); })()"""
d = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]())); d["publicId"] = "pubtest0382i"; d["firstName"] = "Casey"; d["novaMet"] = 99
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else info)
RUN = """async ()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms));
 const real=window.visualViewport; const H=innerHeight; let h=H;
 const fake={ get height(){ return h; }, get offsetTop(){ return 0; }, get scale(){ return 1; }, get width(){ return innerWidth; }, addEventListener(){}, removeEventListener(){} };
 const btn=document.querySelector('.tabsearch-btn'); if(!btn) return 'no search button';
 btn.click(); await wait(60);
 const input=document.querySelector('.tabsearch-field input, .tabsearch input'); if(input && document.activeElement!==input) input.focus();
 Object.defineProperty(window,'visualViewport',{configurable:true,get:()=>fake});
 const KB=336; const steps=18;
 for(let i=1;i<=steps;i++){ h=H-KB*(1-Math.pow(1-i/steps,2)); real.dispatchEvent(new Event('resize')); await wait(16); }
 await wait(700);
 const el=document.querySelector('.tabsearch'); const r=el.getBoundingClientRect();
 const out={ fieldBottom: Math.round(r.bottom), keyboardTop: Math.round(H-KB), gapAboveKeyboard: Math.round((H-KB)-r.bottom), translate: getComputedStyle(el).translate, focused: document.activeElement===input };
 delete window.visualViewport; return out; }"""
DRAG = """async (how)=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms));
 const card=[...document.querySelectorAll('label.pick')][2]; const r=card.getBoundingClientRect(); const x=r.left+r.width/2, y=r.top+r.height/2;
 const fire=(t,px,py,target)=>{ (target||document.elementFromPoint(px,py)||card).dispatchEvent(new PointerEvent(t,{bubbles:true,cancelable:true,pointerId:7,pointerType:'touch',clientX:px,clientY:py,isPrimary:true,button:0})); };
 fire('pointerdown',x,y,card);
 for(let i=1;i<8;i++){ fire('pointermove',x+i*4,y,card); await wait(16); }
 for(let i=1;i<20;i++){ fire('pointermove',x+28,y+(innerHeight-40-y)*i/19,card); await wait(16); }
 await wait(300);
 /* the lift as an iPhone sends it when a native switch took the touch: no pointerup */
 if(how==='touchend'){ const te=new TouchEvent('touchend',{bubbles:true,cancelable:true,touches:[],changedTouches:[]}); window.dispatchEvent(te); }
 const s0=scrollY; await wait(800); const s1=scrollY;
 if(how==='navigate'){ window.scrollTo(0,0); showProfile(); await wait(900); const p0=scrollY; await wait(800); return {how, p0, p1:scrollY}; }
 return {how, s0, s1}; }"""
def units(br, w, h, ins):
    g["new_page"].w, g["new_page"].h = w, h
    ctx, pg = g["new_page"](br, ins, True, False)
    pg.add_init_script(INIT % json.dumps(json.dumps(d)))
    pg.goto(url); pg.wait_for_timeout(3000); pg.evaluate("document.getElementById('splashscreen')?.remove()")
    pg.evaluate("()=>{ homeUnlocksOwed=()=>false; showSetup(); }"); pg.wait_for_timeout(2500)
    return ctx, pg
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    for name, (w, h, ins) in {"phone": (440, 956, (62, 0, 34, 0)), "Pro Max at 85%": (518, 1125, (73, 0, 40, 0))}.items():
        ctx, pg = units(br, w, h, ins)
        r = pg.evaluate(RUN)
        chk("%s: as the keyboard rises in steps, the units search ends 10px above it (%s)" % (name, r), isinstance(r, dict) and r["focused"] and 8 <= r["gapAboveKeyboard"] <= 12, r)
        ctx.close()
    for how in ("touchend", "navigate"):
        ctx, pg = units(br, 440, 956, (62, 0, 34, 0))
        r = pg.evaluate(DRAG, how)
        if how == "touchend":
            chk("a drag-select near the bottom whose finger lifts with no pointerup (a native switch took it) stops scrolling (%s)" % (r,), r["s1"] == r["s0"], r)
        else:
            chk("and one that never lifts before the screen changes does not scroll the next screen (%s)" % (r,), r["p1"] == r["p0"], r)
        ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
