#!/usr/bin/env python3
"""Build 384 r8: Inferno's eyes are the same size as the other rulers'.
Madison: "The inferno eyes are still much different than the rest and are much bigger? Not the same size."
Both classes: (1) Inferno's eye group (its almonds, by their fill box) is within 12% of the mean width and height of Forge's, Solar's
and Tempest's; (2) its glow ring is no wider than .6 units (it was 1.1, which read as a bigger eye); (the rest of Inferno is held by check-b384-r5-chars leg 7,
which lets only the rulers' eye groups change); (4) no errors.
  python3 tools/check-b384-r8-inferno.py [--against OLD/index.html] [--dump]   (must FAIL on the build before)"""
import os, sys, json, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = cb.INSET_RE
    cb.patched = lambda ins: IR.sub(lambda m: {"top": "%dpx" % ins[0], "right": "%dpx" % ins[1], "bottom": "%dpx" % ins[2], "left": "%dpx" % ins[3]}[m.group(1)], OLD)
from playwright.sync_api import sync_playwright
PREVF = os.path.join(HERE, "check-b384-r8-inferno.prev.json")
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
M = """()=>{ const mk=id=>{ const s=buildAvatarCharSVG(id); const svg=typeof s==='string'?(()=>{const d=document.createElement('div');d.innerHTML=s;return d.firstElementChild;})():s; svg.setAttribute('width','400'); svg.setAttribute('height','400'); document.body.appendChild(svg); return svg; };
  const box = id => { const svg=mk(id); const b=svg.querySelector('.cx-eyes').getBBox(); const sw=Math.max(0,...[...svg.querySelectorAll('.cx-eyes path')].map(p=>+(p.getAttribute('stroke-width')||0)).filter(v=>v<3)); svg.remove(); return {w:b.width, h:b.height, sw}; };
  const svg=mk('inferno'); svg.querySelector('.cx-eyes')?.remove(); svg.querySelectorAll('clipPath').forEach(c=>c.remove()); const rest=new XMLSerializer().serializeToString(svg).replace(/ id="[^"]*"/g,'').replace(/url\\(#[^)]*\\)/g,'url()'); svg.remove();
  let h=0; for(let i=0;i<rest.length;i++) h=(h*31+rest.charCodeAt(i))>>>0;
  return { inf: box('inferno'), others: ['forge','solar','tempest'].map(box), rest: h, cls: window.NOVA_CLASS || 'academy' }; }"""
dump = {}
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    for cls in ("academy", "ifc"):
        init = None if cls == "academy" else "try{localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));}catch(e){}"
        ctx, pg = cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT, dpr=1, init=init)
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        m = pg.evaluate(M); dump[cls] = m["rest"]
        if "--dump" not in sys.argv:
            mw = sum(o["w"] for o in m["others"]) / 3; mh = sum(o["h"] for o in m["others"]) / 3
            chk("(1) %s: Inferno's eyes the others' size (%.2f x %.2f against %.2f x %.2f)" % (cls, m["inf"]["w"], m["inf"]["h"], mw, mh), abs(m["inf"]["w"] / mw - 1) <= .12 and abs(m["inf"]["h"] / mh - 1) <= .12, m)
            chk("(2) %s: its glow ring %.2f units (<= .6)" % (cls, m["inf"]["sw"]), m["inf"]["sw"] <= .6, m["inf"])
            chk("(4) %s: no page errors" % cls, not errs, errs[:3])
        ctx.close()
    br.close()
if "--dump" in sys.argv:
    json.dump(dump, open(PREVF, "w")); print("dumped", PREVF, dump); sys.exit(0)
print("ALL PASS" if ok else "FAILURES"); sys.exit(0 if ok else 1)
