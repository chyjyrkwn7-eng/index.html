"""Build 380: Next question moves no faster on an iPad than on a phone.
Madison: "on my iPad, when going to next question, there is lag/its not smooth.
On the phone it's super nice and smooth ... All larger devices should be just as
smooth". The slide crossed the panel's whole width in a fixed time, so a wide
panel moved about twice as many px per frame. The push (side by side, build 311)
stays; a wide one takes longer. Read off the slide's own keyframes.
Run:  python3 tools/check-b380-slide.py   (--against: copy the old index.html over first)"""
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
d = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]())); d["publicId"] = "pubtest0380s"; d["firstName"] = "Casey"; d["novaMet"] = 99
START = """async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const unit=QUESTIONS[0].topic.trim();
 const idx=QUESTIONS.map((q,i)=>i).filter(i=>(QUESTIONS[i].topic||'').trim()===unit && inWholeUnit(QUESTIONS[i]));
 cfg.source='all'; cfg.mode='drill'; cfg.units=[unit]; beginRun(idx); for(let t=0;t<80&&!document.querySelector('.qpanel .choice');t++) await wait(100); await wait(1500); }"""
ANSWER = """async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const qi=order[pos]; const k=optionOrder(qi).indexOf(QUESTIONS[qi].answer);
 [...document.querySelectorAll('.qpanel .choice')][k].click(); await wait(1600); }"""
# Every animation advanceWithSlide starts: how far it travels, its biggest step
# per 60Hz frame, and the strength it ends (outgoing) or starts (incoming) at.
STEP = """async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const w=document.querySelector('#stage .panel').getBoundingClientRect().width;
 const anims=[]; const orig=Element.prototype.animate; Element.prototype.animate=function(k,o){ anims.push([this,k,o]); return orig.call(this,k,o); };
 try{ advanceWithSlide(0); } finally { Element.prototype.animate=orig; }
 const tx=s=>{ const m=/translateX\\(([-0-9.]+)px\\)/.exec(s||''); return m?+m[1]:0; };
 const res=anims.map(([el,k,o])=>{ const xs=k.map(f=>tx(f.transform)), n=k.length-1, per=16.7/o.duration*n; let big=0;
   for(let t=0;t+per<=n;t+=per) big=Math.max(big,Math.abs(xs[Math.min(n,Math.floor(t+per))]-xs[Math.floor(t)]));
   return {who: el.closest('#stage')?'in':'out', travel:Math.round(Math.abs(xs[n]-xs[0])), peak:Math.round(big), ms:o.duration}; });
 const pr=document.querySelector('#stage .panel'); const b=pr.getBoundingClientRect();
 await wait(SLIDE_MS+300);
 const after=document.querySelector('#stage .panel').getBoundingClientRect();
 return {w:Math.round(w), res, left:Math.round(after.left), clones:document.querySelectorAll('body > .panel, .q-blurpair').length}; }"""
DEV = {"widest phone": (518, 1125, (73, 0, 40, 0)), "phone": (440, 956, (62, 0, 34, 0)),
       "iPad mini": (744, 1133, (24, 0, 20, 0)), "iPad 11": (834, 1194, (24, 0, 20, 0)), "iPad landscape": (1194, 834, (24, 0, 20, 0))}
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else info)
out = {}
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    for name, (w, h, ins) in DEV.items():
        g["new_page"].w, g["new_page"].h = w, h
        ctx, pg = g["new_page"](br, ins, True, False)
        pg.add_init_script(INIT % json.dumps(json.dumps(d)))
        pg.goto(url); pg.wait_for_timeout(3000); pg.evaluate("document.getElementById('splashscreen')?.remove()")
        pg.evaluate("()=>{ homeUnlocksOwed=()=>false; showHome(); }"); pg.wait_for_timeout(1200)
        pg.evaluate(START); pg.evaluate(ANSWER)
        out[name] = pg.evaluate(STEP)
        ctx.close()
    br.close()
for k, v in out.items(): print("  ", k, v)
ref = out["widest phone"]
refo = next(r for r in ref["res"] if r["who"] == "out")
# every device: still the push - the outgoing question leaves the panel's whole width
for name, v in out.items():
    o = next((r for r in v["res"] if r["who"] == "out"), None); i = next((r for r in v["res"] if r["who"] == "in"), None)
    chk("on %s the question still pushes the whole width (%s of %d px) and the new one arrives from beside it (%s px)" % (name, o and o["travel"], v["w"], i and i["travel"]),
        o and i and o["travel"] >= v["w"] and i["travel"] >= v["w"], v)
    chk("on %s the new question lands in place with nothing left behind (left %d px, clones %d)" % (name, v["left"], v["clones"]), v["clones"] == 0)
# phones: the old timing, untouched
for name in ("phone", "widest phone"):
    o = next(r for r in out[name]["res"] if r["who"] == "out")
    chk("on a %s the slide keeps the phone's time (%d ms, the same as the %s)" % (name, o["ms"], "phone" if name != "phone" else "widest phone"),
        o["ms"] == next(r for r in out["phone" if name != "phone" else "widest phone"]["res"] if r["who"] == "out")["ms"])
for name in ("iPad mini", "iPad 11", "iPad landscape"):
    v = out[name]; o = next((r for r in v["res"] if r["who"] == "out"), None); i = next((r for r in v["res"] if r["who"] == "in"), None)
    chk("on an %s the question moves no farther per frame than on the widest phone (%s vs %d px at the peak)" % (name, o and o["peak"], refo["peak"]),
        o and i and o["peak"] <= refo["peak"] + 1 and i["peak"] <= refo["peak"] + 1 and v["w"] > ref["w"], v)
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
