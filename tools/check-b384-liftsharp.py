#!/usr/bin/env python3
"""384.150: A BADGE LIFTS OUT SHARP. Madison (recording, the Badges screen): "The badges come up blurry when you select them ... they
aren't clear hd as they pull up". The Badges tab draws each found badge's in-hand face in the quiet (binspectWarmSoon) and a finger
coming down draws it too (badgeInspectPrewarm); the lift (openBadgeInspect) starts on that face if one is cached (peekFace,
binspectFaceKey: a pin's in-hand face is the BARE one). Here, per class: every badge found, the warm-up let finish, then each badge
opened in turn: the picture the lift STARTS on (the front face's src the moment it opens) must be a face of at least the in-hand
size (its decoded width >= 90% of the float's width x the pixel ratio), never the case's small picture.
  python3 tools/check-b384-liftsharp.py [--against FILE]   (384.149 FAILS: every pin starts on the case's picture)"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b384-badges2.py"), encoding="utf-8").read().split("\ndef capture(")[0]
g = {"__file__": os.path.join(HERE, "check-b384-badges2.py"), "__name__": "b2"}; exec(src, g)
fails = 0
with g["sync_playwright"]() as p:
    br = p.chromium.launch()
    for cls in ("academy", "ifc"):
        ctx, pg, errs = g["open_page"](br, g["HERE"], cls, 440, 956, 2)
        units = pg.evaluate("() => { const us = unitsInTeachingOrder(); us.forEach(u => store.unitPerfects[u] = badgeThresholdFor(u)); return us; }")
        # the warm-up's own jobs (it runs them one at a time while the Badges screen is up; here all of them, in order)
        pg.evaluate("() => { binspectWarmSoon(); }")
        for i in range(40):
            pg.wait_for_timeout(500)
            if pg.evaluate("() => binspectWarmJobs.length > 0"): break
        n = pg.evaluate("() => { clearTimeout(binspectWarmT); let n = 0; while(binspectWarmJobs.length){ try{ binspectWarmJobs.shift()(); }catch(e){} n++; } return n; }")
        print("     warm-up jobs run: %d" % n, flush=True)
        bad = []
        for u in units:
            pg.evaluate("() => { try{ badgeInspectNow && badgeInspectNow.close(); }catch(e){} }"); pg.wait_for_timeout(700)
            pg.evaluate("() => { document.querySelectorAll('.binspect').forEach(n => n.remove()); badgeInspectNow = null; }")
            r = pg.evaluate("""async (u) => {
              const t = document.createElement('div'); t.style.cssText = 'position:fixed;left:180px;top:400px;width:80px;height:80px'; document.body.appendChild(t);
              openBadgeInspect(u, t); t.remove();
              const img = document.querySelector('.binspect .binspect-art.is-current'), fl = document.querySelector('.binspect .binspect-float');
              if(!img) return { none: true };
              const src = img.getAttribute('src') || '';
              const want = fl.getBoundingClientRect().width * devicePixelRatio;
              /* the src must be one of the in-hand faces the cache holds (bare for a pin), finished, at the in-hand size */
              const d = badgeDirtStage(u), list = BADGE_STRIKE_CACHE[binspectFaceKey(u, d)] || [];
              const hit = list.find(e => e.url === src);
              return { face: !!hit, w: hit ? hit.W : 0, draft: hit ? hit.draft : null, want: Math.round(want), kind: src.slice(0, 22) }; }""", u)
            if r.get("none") or not r["face"] or r["draft"] or r["w"] < .9 * r["want"]: bad.append((u[:28], r))
        ok = not bad
        fails += 0 if ok else 1
        print(("PASS" if ok else "FAIL"), "[%s] every found badge (%d) lifts out on its in-hand face, not the case's picture" % (cls, len(units)), "" if ok else bad[:6], flush=True)
        ctx.close()
    br.close()
print("ALL PASS" if not fails else "FAILURES: %d" % fails)
sys.exit(1 if fails else 0)
