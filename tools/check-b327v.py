#!/usr/bin/env python3
"""Build 327 round 7 (b327v): the road map's line is one fluid movement, and
a tap on the planet is a gentle surge.

Madison (Oct 22): "The rank road map, the progress bar of the map is messed
up it skips sections and it's not fluid. Fix that." and "When tapping the
center planet in the video all the stuff around it started glitching and
moving incredibly fast."

  python3 tools/check-b327v.py                 (ONLY=still,climb,planet)
  python3 tools/check-b327v.py --against OLD_INDEX.html   (fails on 61d9620)

still  - opening the Rank tab with nothing new: every stretch is drawn where
         it is from the first frame; nothing refills from zero.
climb  - a rank to celebrate, then the climb after it, read every frame:
         the circle opens only once its line has arrived; on the climb the
         line never goes backwards, its light stays on its tip (2px), and
         the stub between the circle and the line is there whenever the
         line is (no gap that appears all at once).
planet - ten taps in two seconds: the rings speed up gently (at most 2.2x
         their pace), never run slower than their pace, and are back at it
         within 3s of the last tap.
"""
import importlib.util, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py"))
cb = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(cb)
from playwright.sync_api import sync_playwright

ONLY = set(filter(None, os.environ.get("ONLY", "").split(",")))
def want(k): return not ONLY or k in ONLY

BASE = """(mode) => { document.querySelectorAll('#pushing-update,#intro-pop,.nova-talk').forEach(n => n.remove());
  const units = topicsIn(QUESTIONS); store.unitPerfects = store.unitPerfects || {};
  units.slice(0, 5).forEach(u => store.unitPerfects[u] = badgeThresholdFor(u));
  store.lifetime.points = xpForLevel(46) + 500; store.levelFloor = 0; store.levelWallRule = 325;
  store.rankMapFx244 = true; store.rankUpShown = null;
  const held = TIER_ORDER_FULL.indexOf('veteran');
  if(mode === 'still'){ store.rankMapSeen = held; store.rankMapProg = { i: held, p: 1 }; }
  else { store.rankMapSeen = TIER_ORDER_FULL.indexOf('ranger'); store.rankMapProg = null; }
  showRanksScreen('ranks'); }"""

# every reached stretch's scale, the moment the map is in and 1.6s later
STILL = """async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
  const sc = e => { const t = getComputedStyle(e).transform; return t === 'none' ? 1 : new DOMMatrix(t).d; };
  const read = () => [...document.querySelectorAll('.rankmap-roadfill')].map(sc);
  for(let i = 0; i < 40 && !document.querySelector('.rankmap-roadfill'); i++) await wait(50);
  await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  await wait(120);
  const a = read(); await wait(1600); const b = read();
  const moving = [...document.querySelectorAll('.rankmap-roadfill')].filter(e => e.getAnimations().length).length;
  return { a, b, moving }; }"""

# every frame for up to 16s: the celebrated stretch, the moment its circle
# opens, then the climb's line, light and stub
CLIMB = """async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
  const sc = e => { const t = getComputedStyle(e).transform; return t === 'none' ? 1 : new DOMMatrix(t).d; };
  const out = { pops: [], frames: [] }; let stop = false;
  const mo = new MutationObserver(() => document.querySelectorAll('.rankmap-stop.is-celebrating').forEach(s => {
    if(s.__seen) return; s.__seen = 1;
    const k = s.dataset.rank || ''; const rf = document.querySelector('.rankmap-roadfill[data-celebrate-for]');
    out.pops.push({ at: performance.now(), lit: rf ? sc(rf) : null }); }));
  mo.observe(document.body, { subtree: true, attributes: true, attributeFilter: ['class'] });
  const rec = () => { if(stop) return;
    const f = document.querySelector('.rankmap-roadfill[data-progress-for]');
    if(f){ const st = f.closest('.rankmap-stop'), dot = st && st.querySelector('.rankmap-roadtip-dot');
      const stub = f.parentElement.querySelector('.rankmap-roadstub');
      const fr = f.getBoundingClientRect(), dr = dot ? dot.getBoundingClientRect() : null;
      let sv = 0; if(stub){ const cs = getComputedStyle(stub); sv = +cs.opacity * (cs.transform === 'none' ? 1 : new DOMMatrix(cs.transform).d); }
      out.frames.push({ t: performance.now(), s: sc(f), front: fr.bottom, dot: dr ? dr.top + dr.height / 2 : null,
        lit: !!(dot && getComputedStyle(dot).opacity > .5), stub: sv, to: +f.dataset.progressTo }); }
    requestAnimationFrame(rec); };
  requestAnimationFrame(rec);
  for(let i = 0; i < 320; i++){ await wait(50); const f = document.querySelector('.rankmap-roadfill[data-progress-for]');
    const n = out.frames.length; if(f && n > 20 && Math.abs(out.frames[n - 1].s - out.frames[n - 1].to) < .002 && out.pops.length) break; }
  await wait(300); stop = true; mo.disconnect(); return out; }"""


def road(br):
    for label, w, h in (cb.PHONE, cb.TABLET):
        if want("still"):
            print("\nstill (%s)" % label)
            ctx, pg = cb.booted(br, w, h, seed=cb.USED_ACCOUNT)
            pg.evaluate(BASE, "still")
            r = pg.evaluate(STILL)
            reached = [x for x in r["a"] if x > .99]
            cb.check("%s: every stretch is where it is on the first frame (nothing refills from zero)" % label,
                     len(r["a"]) >= 3 and len(reached) >= 2 and all(abs(x - y) < .01 for x, y in zip(r["a"], r["b"])) and r["moving"] == 0,
                     r)
            ctx.close()
        if want("climb"):
            print("\nclimb (%s)" % label)
            ctx, pg = cb.booted(br, w, h, seed=cb.USED_ACCOUNT)
            pg.evaluate(BASE, "climb")
            r = pg.evaluate(CLIMB)
            pops = r["pops"]
            cb.check("%s: the circle opens only once its line has arrived (scale >= .995)" % label,
                     bool(pops) and all(p["lit"] is not None and p["lit"] >= .995 for p in pops), pops)
            fr = [f for f in r["frames"] if f["s"] > .002]
            back = [round(fr[i - 1]["front"] - fr[i]["front"], 2) for i in range(1, len(fr)) if fr[i]["front"] < fr[i - 1]["front"] - .5]
            cb.check("%s: the climb's line moves on and never goes back" % label,
                     len(fr) >= 8 and not back and abs(fr[-1]["s"] - fr[-1]["to"]) < .01,
                     {"frames": len(fr), "back": back[:5], "end": fr[-1] if fr else None})
            off = [round(f["dot"] - f["front"], 1) for f in fr if f["dot"] is not None and f["lit"] and abs(f["dot"] - f["front"]) > 2]
            cb.check("%s: its light is on the line's tip in every frame (within 2px)" % label,
                     bool(fr) and not off, off[:6])
            gaps = [round(f["stub"], 2) for f in fr if f["stub"] < .95]
            cb.check("%s: the stub joining it to the circle is there whenever the line is (no gap appearing at once)" % label,
                     bool(fr) and not gaps, gaps[:6])
            ctx.close()


def planet(br):
    print("\nplanet (iPhone 17 Pro Max)")
    ctx, pg = cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT)
    pg.evaluate("() => { theme.soundOn = false; try{ NovaSound.sync(); }catch(e){} }")
    pg.evaluate(cb.HOMETAP_PREP, {})
    for kind in ("default", "orange"):
        st = pg.evaluate(cb.B318_STATE, kind)
        pg.wait_for_timeout(1500)
        res = pg.evaluate(cb.B318_SPAM)
        rr = cb._b318_rates(res)
        fr, laps = res["frames"], res["lap"]
        last_tap = fr[0][0] + 500 + 9 * 200
        late = []
        for k in range(2):
            base = 360 / laps[k] / 1000
            for i in range(1, len(fr)):
                if fr[i][0] < last_tap + 3000:
                    continue
                dt = fr[i][0] - fr[i - 1][0]
                if dt > 0:
                    late.append(((fr[i][k + 1] - fr[i - 1][k + 1] + 180) % 360 - 180) / dt / base)
        lab = "%s (rings %s)" % (st.get("accent"), st.get("ring") or "plain")
        print("    %s: %s" % (lab, rr))
        cb.check(lab + ": ten fast taps speed the rings up gently - at most 2.2x their pace",
                 all(1.2 <= r["maxRate"] <= 2.2 for r in rr), rr)
        cb.check(lab + ": never slower than their own pace", all(r["minRate"] >= .95 for r in rr), rr)
        cb.check(lab + ": back at their own pace within 3s of the last tap",
                 bool(late) and all(.9 <= x <= 1.1 for x in late), [round(min(late), 2), round(max(late), 2)] if late else None)
    ctx.close()


with sync_playwright() as p:
    br = p.chromium.launch(executable_path=cb.CHROME)
    if want("still") or want("climb"):
        road(br)
    if want("planet"):
        planet(br)
    br.close()

fails = list(getattr(cb, "FAILURES", []))
print("\nALL PASS" if not fails else "\nFAILED: %d" % len(fails))
sys.exit(1 if fails else 0)
