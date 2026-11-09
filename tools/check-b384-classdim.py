#!/usr/bin/env python3
"""Build 384 final check: what is behind the open class list dims - without making the whole app restyle on every change.

The full check dimmed Home behind the open class list with  #stage:has(> .class-bubble-wrap.is-open) > :not(.class-bubble-wrap).
A :has() on #stage whose styled elements are "everything but one" is re-checked on any change under #stage, and each time it
invalidates the WHOLE screen's style: opening one "Show the code" in a Fire Code Review list cost a 138ms restyle of 6,914
elements at 4x CPU (check-b384-codeopen (2) failing on every build since). Now the list sets #stage.class-list-open itself.
On an installed iPhone 17 Pro Max, the owner's class button, enrolled in Fire Code too:
(1) a tap on the class button dims the rest of Home (opacity <= .3) and the rest takes no tap;
(2) a tap outside shuts the list, and Home comes back (opacity 1) and takes taps again;
(3) a screen mounted while the list is open (the list goes with Home) is never left dimmed or untappable;
(4) no style rule in the app pairs a :has() with a "broad" styled set (:not(...), *, or a bare tag after it) - the shape that
    restyles a whole screen on any change;
(5) no page errors.
  python3 tools/check-b384-classdim.py [--against OLD/index.html]   (must FAIL on the build before)"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b381-class.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b381-class.py"), "__name__": "b384cd"}
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
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
BEHIND = """()=>{ const p=[...document.querySelectorAll('#stage > *')].find(e=>!e.classList.contains('class-bubble-wrap') && e.offsetHeight>0);
  const b=document.querySelector('#stage .playbtn, #stage #nextbtn, #stage button:not(.class-bubble):not(.class-stack-item)');
  let hit=null; if(b){ const r=b.getBoundingClientRect(); const e=document.elementFromPoint(r.left+r.width/2, r.top+r.height/2); hit = !!(e && (e===b || b.contains(e))); }
  return { opacity: p ? +(+getComputedStyle(p).opacity).toFixed(2) : null, pe: p ? getComputedStyle(p).pointerEvents : null, takesTap: hit,
           open: !!document.querySelector('.class-bubble-wrap.is-open'), screen: p ? p.className.slice(0,60) : null }; }"""
BROAD = r"""()=>{ const out=[]; const broad=(sel)=>{ for(const part of sel.split(',')){ const i=part.lastIndexOf(':has('); if(i<0) continue;
      let d=0, j=-1; for(let k=i+4;k<part.length;k++){ if(part[k]==='(') d++; else if(part[k]===')'){ d--; if(d===0){ j=k; break; } } }
      const tail=part.slice(j+1).trim(); if(!tail) continue; const last=tail.split(/\s*[>+~ ]\s*/).pop();
      if(last==='*' || last.startsWith(':not(') || /^[a-z]+$/.test(last)) out.push(part.trim().slice(0,140)); } };
    const walk=(rules)=>{ for(const r of rules){ if(r.selectorText) broad(r.selectorText); if(r.cssRules) walk(r.cssRules); } };
    for(const sh of document.styleSheets){ try{ walk(sh.cssRules); }catch(e){} } return out; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    ctx, pg, cdp = G["page"](br, 440, 956, (62, 0, 34, 0), True)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    c = pg.evaluate(G["CENTRE"], ".class-bubble")
    if not c:
        chk("the class button is on Home", False)
    else:
        b0 = pg.evaluate(BEHIND)
        G["tap"](cdp, *c); pg.wait_for_timeout(700)
        b1 = pg.evaluate(BEHIND)
        chk("(1) open, the rest of Home steps back (%s -> %s) and takes no tap" % (b0["opacity"], b1),
            b1["open"] and b1["opacity"] is not None and b1["opacity"] <= .3 and b1["pe"] == "none" and b1["takesTap"] is False, [b0, b1])
        G["tap"](cdp, 220, 120); pg.wait_for_timeout(700)
        b2 = pg.evaluate(BEHIND)
        chk("(2) a tap outside shuts it and Home comes back (%s)" % b2,
            not b2["open"] and b2["opacity"] == 1 and b2["pe"] != "none" and b2["takesTap"] is True, b2)
        G["tap"](cdp, *pg.evaluate(G["CENTRE"], ".class-bubble")); pg.wait_for_timeout(600)
        pg.evaluate("()=>{ showProfile(); }"); pg.wait_for_timeout(1200)
        b3 = pg.evaluate(BEHIND)
        chk("(3) a screen put up while the list is open is not left dimmed or untappable (%s)" % b3,
            b3["opacity"] == 1 and b3["pe"] != "none", b3)
    bad = pg.evaluate(BROAD)
    chk("(4) no :has() rule styles a broad set after it (%s)" % bad, not bad, bad)
    chk("(5) no page errors", not errs, errs[:3])
    br.close()
G["srv"].shutdown()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
