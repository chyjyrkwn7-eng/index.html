#!/usr/bin/env python3
"""Every badge in your hand, turned: a contact sheet per class of each badge in the inspector at 0, 35, 70, 90 (edge on), 145 and 180
degrees, the way a person sees it while turning it with a finger (the face, the rounded side, the back).

(384.136) Madison: "Ensure all the badges are good to go and look right when you rotate them and stuff as well." The inspector turns the
badge as a 3D stack (front face, 16 edge slices made from the outline, back face); this opens each badge found, lets its edges build,
sets the turn directly on .binspect-spin, and photographs the badge.

  python3 tools/shoot-badge-turns.py OUTDIR [--class ifc|academy|both] [--index FILE] [--only 'Chapter 32,Appendix H']
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b384-badges2.py"), encoding="utf-8").read().split("\ndef capture(")[0]
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
argv = sys.argv[:]; sys.argv = [sys.argv[0]] + (["--against", argv[argv.index("--index") + 1]] if "--index" in argv else [])
g = {"__file__": os.path.join(HERE, "check-b384-badges2.py"), "__name__": "b2"}; exec(src, g)
sys.argv = argv
from PIL import Image, ImageDraw
CLS = ["academy", "ifc"] if g["arg"]("--class", "both") == "both" else [g["arg"]("--class")]
ONLY = [s.strip() for s in (g["arg"]("--only") or "").split(",") if s.strip()]
ANG = [0, 35, 70, 90, 145, 180]
with g["sync_playwright"]() as p:
    br = p.chromium.launch()
    for cls in CLS:
        ctx, pg, errs = g["open_page"](br, g["HERE"], cls, 440, 956, 2)
        units = pg.evaluate("() => { const us = unitsInTeachingOrder(); us.forEach(u => store.unitPerfects[u] = badgeThresholdFor(u)); return us; }")
        if ONLY: units = [u for u in units if any(u.startswith(o) for o in ONLY)]
        strips = []
        for u in units:
            pg.evaluate("() => { try{ badgeInspectNow && badgeInspectNow.close(); }catch(e){} document.querySelectorAll('.binspect').forEach(n => n.remove()); }")
            pg.wait_for_timeout(150)
            for tries in range(4):
                pg.evaluate("(u) => { const t = document.createElement('div'); t.style.cssText = 'position:fixed;left:180px;top:400px;width:80px;height:80px'; document.body.appendChild(t); openBadgeInspect(u, t); t.remove(); }", u)
                pg.wait_for_timeout(300)
                if pg.evaluate("() => !!document.querySelector('.binspect-spin')"): break
                pg.evaluate("() => { try{ badgeInspectNow && badgeInspectNow.close(); }catch(e){} }"); pg.wait_for_timeout(2500)
                pg.evaluate("() => document.querySelectorAll('.binspect').forEach(n => n.remove())")
            pg.wait_for_timeout(1200)
            for i in range(60):
                if pg.evaluate("() => typeof BADGE_STRIKE_DRAFTS === 'undefined' || !BADGE_STRIKE_DRAFTS.size"): break
                pg.wait_for_timeout(250)
            pg.wait_for_timeout(900)
            shots = []
            for a in ANG:
                r = pg.evaluate("(a) => { const s = document.querySelector('.binspect-spin'); if(!s) return null; s.style.transition = 'none'; s.style.transform = 'rotateY(' + a + 'deg)'; const wr = x => { x = ((x % 360) + 360) % 360; return x > 180 ? x - 360 : x; }; const L = r => { const x = r * Math.PI / 180; return { o: Math.pow(Math.max(0, Math.cos(x)), 10), x: Math.sin(x) * 190 }; }; const ov = document.querySelector('.binspect'); const fr = L(wr(a + 14)), bk = L(wr(a + 14 - 180)); const fi = ov.querySelector('.binspect-face.is-front .binspect-spec > i'), bi = ov.querySelector('.binspect-face.is-back .binspect-spec > i'); if(fi){ fi.style.transition = 'none'; fi.style.opacity = fr.o.toFixed(3); fi.style.transform = 'translateX(' + (-fr.x).toFixed(1) + '%) rotate(16deg)'; } if(bi){ bi.style.transition = 'none'; bi.style.opacity = (bk.o * .8).toFixed(3); bi.style.transform = 'translateX(' + bk.x.toFixed(1) + '%) rotate(16deg)'; } const sh = ov.querySelector('.binspect-shadow'); if(sh) sh.style.transform = 'scaleX(' + (.22 + .78 * Math.abs(Math.cos(a * Math.PI / 180))).toFixed(3) + ')';"
                                " const b = document.querySelector('.binspect-persp').getBoundingClientRect(); const m = 24; return { x: Math.max(0, b.left - m), y: Math.max(0, b.top - m), width: b.width + 2 * m, height: b.height + 2 * m }; }", a)
                if not r: break
                pg.wait_for_timeout(120)
                f = os.path.join(OUT, "_t.png"); pg.screenshot(path=f, clip=r); shots.append(Image.open(f).convert("RGB").copy())
            if not shots: print("no inspector for", u, flush=True); continue
            h = 300; shots = [s.resize((int(s.width * h / s.height), h)) for s in shots]
            st = Image.new("RGB", (sum(s.width for s in shots) + 10 * len(shots), h + 30), (16, 18, 22)); x = 0
            for s in shots: st.paste(s, (x, 30)); x += s.width + 10
            ImageDraw.Draw(st).text((8, 8), u[:110], fill="white"); strips.append(st)
            print(cls, u[:60], flush=True)
        per = 6
        for k in range(0, len(strips), per):
            grp = strips[k:k + per]; W = max(s.width for s in grp); H = sum(s.height for s in grp)
            sheet = Image.new("RGB", (W, H), (16, 18, 22)); y = 0
            for s in grp: sheet.paste(s, (0, y)); y += s.height
            sheet.save(os.path.join(OUT, "%s-%02d.png" % (cls, k // per)))
        print(cls, "errors:", errs[:3], flush=True); ctx.close()
