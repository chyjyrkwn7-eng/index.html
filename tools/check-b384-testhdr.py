#!/usr/bin/env python3
"""Build 384 r15: the test header reads clearly and the question progress follows it.
Madison, in a Drill on an iPhone (screen recording, question 6 of 102): "The top tab thing in tests broke. Why can't you see the
amount of questions, why is it when you scroll down it doesn't follow now?" In the recording the mode ("Drill"), the count ("6/102")
and Pause's label read soft and grey next to crisp text lower down, and the dots under the row scroll away (and leave a hole under the
row when the page is pulled down).

WHAT THIS CAN AND CANNOT SHOW. Chromium paints this header crisply in 383 and in the build before this one: the soft raster is an iOS
(WebKit) compositing result and cannot be reproduced here - confirm it on a phone. What is asserted is the STRUCTURE the header's text
sits in, which is what was changed: the row is a plain fixed layer (no `isolation`, no negative-z child under its text, nothing with a
filter or backdrop-filter above it); the fade behind it is its own fixed layer one z-index lower (.wrap::before, not .top::before);
and the mode and the count are, at their centres, the topmost things on the page, at opacity 1, with the contrast they are drawn at
(read off a screenshot: the brightest ink in the box against the page colour under it) at least 4.5:1.
Real Drill on an iPhone 17 Pro Max (440x956 @3x, Dynamic Island inset) and an iPhone SE 3 (375x667 @2x), installed (standalone), in the
academy and in Fire Code. For each:
 (1) at rest, scrolled 300px (the question stretched to 3000px) and "rubber-banded" (SIMULATED: Chromium has no overscroll, so every
     in-flow child of .wrap but the header is moved down 200px with a transform, which is what iOS does to the document while the
     fixed header stays): the mode and the count are the topmost element at their centres, at the same y, rendered at >= 4.5:1;
 (1b) a white page scrolled under the row does not show through it between the mode and the count;
 (2) no opacity below 1, filter or backdrop-filter on either or on any ancestor up to body; .top has no isolation and no ::before /
     ::after; the fade is a fixed .wrap::before below the row's z-index;
 (3) the progress line: hidden at rest (the dots are under the row), shown when scrolled and when pulled, under the row, clear of
     Pause and the chat button, inside the page's side padding, painted from the dots (green for a right answer, red for a miss,
     the accent where you are), and it takes no room (the question sits where it does with the line removed);
 (4) in a Virtual Room race (line pinned, dots pinned with it) the line is not drawn and the header text is still on top;
 (5) no page errors.
  python3 tools/check-b384-testhdr.py [--against OLD/index.html]    (must FAIL on 54a6848's index.html and on 383's)"""
import os, sys, re, io, importlib.util, warnings
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
SRC = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
if "--against" in sys.argv:
    SRC = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
def body_for(ins):
    v = {"top": "%dpx" % ins[0], "right": "0px", "bottom": "%dpx" % ins[1], "left": "0px"}
    return cb.INSET_RE.sub(lambda m: v[m.group(1)], SRC).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
sf = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0], sf)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
IFC = ("(()=>{ try{ localStorage.setItem('class26e.activeclass','ifc'); localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done');"
       "['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted'].forEach(k=>localStorage.setItem(k,'1'));"
       "const a=JSON.parse(localStorage.getItem('class26e.drill.v1')); a.publicId='tst384hdrx01'; a.classes=['academy','ifc']; localStorage.setItem('class26e.drill.v1', JSON.stringify(a)); localStorage.setItem('class26e.ifc.drill.v1', JSON.stringify(a)); }catch(e){} })()")
DEVICES = (("iPhone 17 Pro Max", 440, 956, 3, (59, 34)), ("iPhone SE 3", 375, 667, 2, (20, 0)))
START = """()=>{ const cnt={}; QUESTIONS.forEach(q=>{ const t=(q.topic||'').trim(); cnt[t]=(cnt[t]||0)+1; });
  const t=Object.keys(cnt).sort((a,b)=>cnt[b]-cnt[a])[0]; cfg.mode='drill'; runMode='drill'; cfg.units=[t]; cfg.source='all';
  beginRun(QUESTIONS.map((q,i)=>[q,i]).filter(([q])=>(q.topic||'').trim()===t).map(([,i])=>i), null, null); return cnt[t]; }"""
PROBE = """()=>{ const out={}; const rect=e=>{ const r=e.getBoundingClientRect(); return {l:r.left,t:r.top,r:r.right,b:r.bottom,w:r.width,h:r.height}; };
  const probe=(sel)=>{ const e=document.querySelector(sel); if(!e) return null; const r=e.getBoundingClientRect(); const cx=r.left+r.width/2, cy=r.top+r.height/2;
    const top=document.elementFromPoint(cx,cy); const chain=[]; let op=1, bad=[];
    for(let n=e;n&&n!==document.documentElement;n=n.parentElement){ const c=getComputedStyle(n); op*=parseFloat(c.opacity);
      if(c.filter!=='none') bad.push('filter:'+n.tagName+'.'+n.className); if(c.backdropFilter!=='none'&&c.backdropFilter) bad.push('backdrop:'+n.tagName+'.'+n.className); if(c.mixBlendMode!=='normal') bad.push('blend:'+n.className); if(c.maskImage!=='none') bad.push('mask:'+n.className); }
    return { text:e.textContent, rect:rect(e), topIsSelf: top===e, topIs: top? top.tagName+'.'+(top.className||top.id):null, op, bad, color:getComputedStyle(e).color }; };
  out.count=probe('.test-qcounter'); out.mode=probe('.test-modelabel');
  const row=document.querySelector('.wrap > .top'); const rc=getComputedStyle(row);
  out.row={ pos:rc.position, z:rc.zIndex, isolation:rc.isolation, before:getComputedStyle(row,'::before').content, after:getComputedStyle(row,'::after').content, rect:rect(row) };
  const wf=getComputedStyle(document.querySelector('.wrap'),'::before'); out.fade={ content:wf.content, pos:wf.position, z:wf.zIndex, h:parseFloat(wf.height) };
  const pr=document.getElementById('testprogress'); if(pr){ const c=getComputedStyle(pr); out.prog={ display:c.display, op:parseFloat(c.opacity), rect:rect(pr), bg:c.backgroundImage, pos:c.position }; } else out.prog=null;
  const pb=document.getElementById('pausebtn'); out.pause=pb&&!pb.hidden?rect(pb):null;
  const ch=[...document.querySelectorAll('.chatdock-btn')].map(rect).filter(r=>r.w>0)[0]||null; out.chat=ch;
  const m=document.getElementById('meter'); out.meter=m&&!m.hidden?rect(m):null; const q=document.querySelector('.qpanel'); out.qpanel=q?rect(q):null;
  const w=document.querySelector('.wrap'); out.wrapPad=parseFloat(getComputedStyle(w).paddingLeft); out.pinned=w.classList.contains('test-pinned'); out.raced=w.classList.contains('race-pinned');
  return out; }"""
def lum(c):
    f = lambda v: (v / 255 / 12.92) if v / 255 <= .03928 else (((v / 255) + .055) / 1.055) ** 2.4
    return .2126 * f(c[0]) + .7152 * f(c[1]) + .0722 * f(c[2])
def ratio(a, b):
    la, lb = lum(a), lum(b); hi, lo = max(la, lb), min(la, lb); return (hi + .05) / (lo + .05)
def rendered_contrast(pg, r, dpr):
    """Brightest ink inside the element's box against the page colour just around it, read off a screenshot."""
    from PIL import Image
    png = pg.screenshot(clip={"x": max(0, r["l"] - 4), "y": max(0, r["t"] - 4), "width": r["w"] + 8, "height": r["h"] + 8})
    im = Image.open(io.BytesIO(png)).convert("RGB"); W, H = im.size
    edge = [im.getpixel((x, y)) for x in range(W) for y in (0, H - 1)] + [im.getpixel((x, y)) for y in range(H) for x in (0, W - 1)]
    bg = tuple(sorted(c[i] for c in edge)[len(edge) // 2] for i in range(3))
    inner = [im.getpixel((x, y)) for x in range(int(4 * dpr), W - int(4 * dpr)) for y in range(int(4 * dpr), H - int(4 * dpr))]
    ink = max(inner, key=lambda c: abs(lum(c) - lum(bg)))
    return ratio(ink, bg), bg, ink
GRAD_COLS = lambda bg: re.findall(r"rgb\(\d+, \d+, \d+\)|color\([^)]*\)", bg or "")
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    for cls in ("academy", "ifc"):
        for lab, w, h, dpr, (it, ib) in DEVICES:
            tag = "%s %s" % (cls, lab)
            cb.BODY = body_for((it, ib))
            ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=dpr, has_touch=True, is_mobile=True, user_agent=UA)
            ctx.add_init_script(sf["STANDALONE"])
            ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.drill.v1','%s');localStorage.setItem('class26e.weekrecap.v1','9999-12-31');localStorage.setItem('class26e.savecode.card','1');}catch(e){}" % cb.USED_ACCOUNT)
            if cls == "ifc": ctx.add_init_script(IFC)
            pg = cb.open_page(ctx); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
            pg.goto(cb.URL); pg.wait_for_timeout(2600)
            pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __stub();}")
            got = pg.evaluate("()=>window.NOVA_CLASS")
            chk("(0) %s: the page is in the %s class (%s)" % (tag, cls, got), got == cls, got)
            n = pg.evaluate(START)
            for _ in range(40):
                if pg.evaluate("()=>!!document.querySelector('.qpanel .choice')"): break
                pg.wait_for_timeout(250)
            pg.wait_for_timeout(1200)
            rest = pg.evaluate(PROBE)
            if not rest["count"] or not rest["mode"] or not rest["pinned"]:
                chk("(0) %s: a real Drill is up with its header pinned (%s questions)" % (tag, n), False, rest); ctx.close(); continue
            # ---- (2) structure
            bad = rest["count"]["bad"] + rest["mode"]["bad"]
            chk("(2) %s: no opacity, filter, backdrop-filter, blend or mask on the mode / count or above them (opacity %.2f/%.2f) %s" % (tag, rest["count"]["op"], rest["mode"]["op"], bad),
                not bad and rest["count"]["op"] == 1 and rest["mode"]["op"] == 1, rest)
            R = rest["row"]
            chk("(2) %s: the row is a plain fixed layer - no isolation, no ::before / ::after under its text (%s, before %s)" % (tag, R["isolation"], R["before"]),
                R["pos"] == "fixed" and R["isolation"] == "auto" and R["before"] in ("none", "normal") and R["after"] in ("none", "normal"), R)
            F = rest["fade"]
            chk("(2) %s: the fade is its own fixed layer under the row (.wrap::before z %s < row z %s, %.0fpx tall)" % (tag, F["z"], R["z"], F["h"]),
                F["content"] not in ("none", "normal") and F["pos"] == "fixed" and F["z"] != "auto" and int(F["z"]) < int(R["z"]) and F["h"] >= R["rect"]["b"], rest)
            # ---- (1) at rest, scrolled, pulled
            states = [("at rest", None)]
            def stateAt(name):
                if name == "scrolled 300px":
                    pg.evaluate("()=>{ document.querySelector('.qpanel').style.minHeight='3000px'; window.scrollTo({top:300, behavior:'instant'}); }")
                elif name == "pulled down 200px (simulated)":
                    pg.evaluate("()=>{ window.scrollTo({top:0, behavior:'instant'}); [...document.querySelector('.wrap').children].filter(e=>!e.classList.contains('top')).forEach(e=>{ e.style.transform='translateY(200px)'; }); window.dispatchEvent(new Event('scroll')); }")
                pg.wait_for_timeout(450)
                return pg.evaluate(PROBE)
            snaps = {"at rest": rest}
            snaps["scrolled 300px"] = stateAt("scrolled 300px")
            pg.evaluate("()=>{ window.scrollTo({top:0, behavior:'instant'}); }"); pg.wait_for_timeout(300)
            snaps["pulled down 200px (simulated)"] = stateAt("pulled down 200px (simulated)")
            for name, s in snaps.items():
                for which in ("mode", "count"):
                    e = s[which]
                    chk("(1) %s %s: the %s (%r) is the topmost thing at its centre (%s)" % (tag, name, which, e["text"], e["topIs"]), e["topIsSelf"], e)
                    chk("(1) %s %s: the %s is at the same y as at rest (%.1f vs %.1f)" % (tag, name, which, e["rect"]["t"], rest[which]["rect"]["t"]), abs(e["rect"]["t"] - rest[which]["rect"]["t"]) <= .5, e)
            # the contrast, rendered, at rest and scrolled (the longest question under the row)
            pg.evaluate("()=>{ [...document.querySelector('.wrap').children].forEach(e=>{ e.style.transform=''; }); window.scrollTo({top:300, behavior:'instant'}); }"); pg.wait_for_timeout(450)
            sc = pg.evaluate(PROBE)
            for which in ("mode", "count"):
                rc, bg, ink = rendered_contrast(pg, sc[which]["rect"], dpr)
                chk("(1) %s scrolled: the %s is drawn at %.1f:1 (ink %s on %s), at least 4.5:1" % (tag, which, rc, ink, bg), rc >= 4.5, [rc, bg, ink])
            # (1b) a long question under the row must not show through it: scrolled over a white page, the band between the mode and the count
            #      (the row's own height) stays the page colour. Measured off a screenshot; the fade used to start thinning in the middle of the row.
            pg.evaluate("()=>{ const q=document.querySelector('.qpanel'); q.style.background='#fff'; q.style.minHeight='3000px'; window.scrollTo({top:700, behavior:'instant'}); }"); pg.wait_for_timeout(450)
            bl = pg.evaluate(PROBE); from PIL import Image
            x0, x1 = bl["mode"]["rect"]["r"] + 6, bl["count"]["rect"]["l"] - 6; y0, y1 = bl["row"]["rect"]["t"], bl["row"]["rect"]["b"]
            im = Image.open(io.BytesIO(pg.screenshot(clip={"x": x0, "y": y0, "width": x1 - x0, "height": y1 - y0}))).convert("RGB")
            hi = max(max(im.getpixel((x, y))) for x in range(im.size[0]) for y in range(im.size[1]))
            chk("(1b) %s: a white page scrolled under the row does not show through it (brightest level in the row's band %d of 255; the page colour is ~25)" % (tag, hi), hi <= 60, hi)
            pg.evaluate("()=>{ document.querySelector('.qpanel').style.background=''; window.scrollTo({top:0, behavior:'instant'}); }"); pg.wait_for_timeout(300)
            # ---- (3) the progress line
            P = snaps["at rest"]["prog"]
            chk("(3) %s: a progress line exists in the row, and at rest it is not drawn (the dots are under the row)" % tag, P and P["display"] == "block" and P["op"] == 0, P)
            S = snaps["scrolled 300px"]; Pp = S["prog"]
            on = Pp and Pp["op"] == 1
            chk("(3) %s scrolled 300px: the dots are out of sight (%s) and the line is drawn" % (tag, S["meter"] and round(S["meter"]["b"])), on and S["meter"]["b"] <= S["row"]["rect"]["b"] + 6, S)
            Q = snaps["pulled down 200px (simulated)"]; Qp = Q["prog"]
            chk("(3) %s pulled down: the line is drawn in the gap the dots left" % tag, Qp and Qp["op"] == 1, Q)
            if on:
                r = Pp["rect"]; rr = S["row"]["rect"]; pad = S["wrapPad"]
                chk("(3) %s: it sits under the row, inside the side padding (%.1f..%.1f of %d, pad %.1f), 3px tall" % (tag, r["l"], r["r"], w, pad),
                    r["t"] >= rr["b"] and abs(r["l"] - pad) <= 1 and abs((w - r["r"]) - pad) <= 1 and abs(r["h"] - 3) <= .5, S)
                clear = lambda a, b: (not b) or a["r"] <= b["l"] or b["r"] <= a["l"] or a["b"] <= b["t"] or b["b"] <= a["t"]
                chk("(3) %s: it is clear of Pause and the chat button" % tag, clear(r, S["pause"]) and clear(r, S["chat"]), S)
            # painted from the dots: mark tick 0 right, 1 missed, tick 2 current, rest still to come
            pg.evaluate("()=>{ const t=document.getElementById('meter').children; t[0].className='tick clean'; t[1].className='tick messy'; t[2].className='tick now'; window.scrollTo({top:300, behavior:'instant'}); }"); pg.wait_for_timeout(450)
            bgimg = pg.evaluate("()=>{ const e=document.getElementById('testprogress'); return e ? getComputedStyle(e).backgroundImage : ''; }")
            cols = GRAD_COLS(bgimg)
            want = pg.evaluate("()=>{ const probe=(v)=>{ const d=document.createElement('i'); d.style.color='var('+v+')'; document.body.appendChild(d); const c=getComputedStyle(d).color; d.remove(); return c; }; return [probe('--right'), probe('--wrong'), probe('--accent'), probe('--rule')]; }")
            norm = lambda c: re.sub(r"\s+", "", c)
            have = [norm(c) for c in cols]
            chk("(3) %s: the line is painted from the dots - right, missed, current, then still-to-come (%s)" % (tag, n),
                len(have) >= 4 and all(norm(x) in have for x in want[:3]) and have.index(norm(want[0])) < have.index(norm(want[1])) < have.index(norm(want[2])), [have, want])
            # it takes no room: the question sits where it does with the line taken out
            pg.evaluate("()=>{ window.scrollTo({top:0, behavior:'instant'}); }"); pg.wait_for_timeout(300)
            a = pg.evaluate("()=>{ const q=document.querySelector('.qpanel').getBoundingClientRect().top, m=document.getElementById('meter').getBoundingClientRect().top; return [q,m]; }")
            pg.evaluate("()=>{ const e=document.getElementById('testprogress'); if(e) e.remove(); }"); pg.wait_for_timeout(200)
            b = pg.evaluate("()=>{ const q=document.querySelector('.qpanel').getBoundingClientRect().top, m=document.getElementById('meter').getBoundingClientRect().top; return [q,m]; }")
            chk("(3) %s: it takes no room (question at %.1f with it, %.1f without)" % (tag, a[0], b[0]), abs(a[0] - b[0]) <= .5 and abs(a[1] - b[1]) <= .5, [a, b])
            # ---- (4) a race: the line is not drawn, the header text is still on top
            ctx2 = ctx
            pg.reload(); pg.wait_for_timeout(2600)
            pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __stub();}")
            pg.evaluate(START)
            for _ in range(40):
                if pg.evaluate("()=>!!document.querySelector('.qpanel .choice')"): break
                pg.wait_for_timeout(250)
            pg.wait_for_timeout(900)
            pg.evaluate("""()=>{ const rb=document.getElementById('vroomracebar'); rb.hidden=false; inVirtualRoom=true;
              const m=document.getElementById('vroomracemarkers'); ['0%','50%','100%'].forEach(l=>{ const d=document.createElement('div'); d.className='vroom-race-marker'; d.style.left=l; m.appendChild(d); });
              syncTestPin(true); document.querySelector('.qpanel').style.minHeight='3000px'; window.scrollTo({top:400, behavior:'instant'}); }""")
            pg.wait_for_timeout(600)
            rr = pg.evaluate(PROBE)
            P4 = rr["prog"]
            chk("(4) %s in a race (line pinned): the progress line is not drawn" % tag, rr["raced"] and (P4 is None or P4["display"] == "none" or P4["op"] == 0), rr)
            chk("(4) %s in a race: the mode and the count are still the topmost things at their centres" % tag, rr["count"] and rr["mode"] and rr["count"]["topIsSelf"] and rr["mode"]["topIsSelf"], rr)
            chk("(5) %s: no page errors" % tag, not errs, errs[:3])
            ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILURES"); sys.exit(0 if ok else 1)
