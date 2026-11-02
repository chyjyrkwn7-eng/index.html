"""Build 382: badges no longer lose their shine and are not rubbed clean; every badge wears one look.
Madison: "let's get rid of the 'lost its shine' thing for badges, no more rubbing badges to clean them. You can
still pull the badges up though ... give them a smidge more of a dirty look ... less shine more dirty but not a lot."
A fixture with badges last cleaned ten weeks, two weeks and an hour ago (and one with no time at all):
  - the Badges screen says nothing about shine, cleaning or rubbing (no tip on a badge, no hint in your hand);
  - every found badge is drawn at the same stage, whatever its clean time: badgeDirtStage agrees across clean
    times, every slot carries the same stage, and the ten-week badge's render is the one-hour badge's look;
  - a badge lifted out and rubbed (short strokes back and forth over its middle) is not cleaned: its stage, its
    stored clean time (store and saved copy) and its face do not change, and no sparkle plays;
  - lifting still works: the slot empties, the badge floats, Close puts the same badge back in its slot;
  - the Profile tour's badge-case step does not tell you to rub badges.
Run:  python3 tools/check-b382-badges.py   (--against: copy the old index.html over first)"""
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
d = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]())); d["publicId"] = "pubtest0382b"; d["firstName"] = "Casey"; d["novaMet"] = 99
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else info)

# the first four units found; cleaned 10 weeks, 2 weeks and 1 hour ago, the fourth with no time
SEED = """() => { const units = unitsInTeachingOrder(), W = 7 * 24 * 3600e3, now = Date.now(); store.unitPerfects = {};
  units.forEach((u, i) => store.unitPerfects[u] = i < 4 ? badgeThresholdFor(u) : 0);
  store.seenUnlocks = store.seenUnlocks || { chars: [], banners: [], themes: [], badges: [] }; store.seenUnlocks.badges = units.slice();
  const held = unlockedIdsNow(); ['chars', 'banners', 'themes', 'fx'].forEach(k => { store.seenUnlocks[k] = (held[k] || []).slice(); });
  store.badgeCleanedAt = { [units[0]]: now - 10 * W, [units[1]]: now - 2 * W - 3600e3, [units[2]]: now - 3600e3 };
  store.pendingBadgeUnlocks = []; theme.muteBanners = true; try{ applyTheme(); }catch(e){}
  try{ persistLocally(); }catch(e){}
  document.querySelectorAll('#pushing-update,#intro-pop,.app-banner,.daily-alert,.update-banner').forEach(n => n.remove());
  return units.slice(0, 4); }"""
WORDS = r"/\b(shine|shiny|clean|cleaned|cleaning|rub|rubbing|dirty|dull)\b/i"
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    ctx = br.new_context(viewport={"width": 440, "height": 956}, device_scale_factor=2)
    ctx.add_init_script(g["STANDALONE"])
    ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]()))
    pg = ctx.new_page(); body = g["patched"]((62, 0, 34, 0))
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.add_init_script(INIT % json.dumps(json.dumps(d)))
    pg.goto(url); pg.wait_for_timeout(3000); pg.evaluate("document.getElementById('splashscreen')?.remove()")
    units = pg.evaluate(SEED)
    pg.evaluate("() => showRanksScreen('badges')"); pg.wait_for_timeout(2200)
    pg.evaluate("() => { try{ finishBadgeCaseOpen(document.querySelector('.badges-tab .ncase')); }catch(e){} }"); pg.wait_for_timeout(600)

    # ---- 1. the case: nothing about shine; every found badge at one stage ----
    case = pg.evaluate("""(re) => { const R = new RegExp(re.slice(1, re.lastIndexOf('/')), 'i'); const tab = document.querySelector('.badges-tab') || document.getElementById('stage');
      const cells = [...document.querySelectorAll('.badges-tab .ncase-cell.is-earned')];
      const said = [...tab.querySelectorAll('*')].filter(e => !e.children.length && R.test(e.textContent || '')).map(e => e.textContent.trim().slice(0, 60));
      return { said, tipEls: tab.querySelectorAll('[class*="clean"], [class*="tip"][class*="badge"]').length,
               stages: cells.map(c => { const a = c.querySelector('.badge-tile-art'); return a ? a.dataset.dirt : null; }),
               tileDirt: cells.filter(c => c.dataset.dirt != null).length, n: cells.length }; }""", WORDS)
    chk("the Badges screen says nothing about shine, cleaning or rubbing, and no badge carries a tip (%s)" % case["said"][:3],
        case["n"] == 4 and not case["said"] and case["tipEls"] == 0, case)
    chk("every found badge in the case is drawn at the same stage, whatever its clean time (%s)" % case["stages"],
        case["n"] == 4 and len(set(case["stages"])) == 1 and None not in case["stages"] and case["tileDirt"] == 0, case)
    st = pg.evaluate("""(units) => { const W = 7 * 24 * 3600e3, now = Date.now(), keep = JSON.stringify(store.badgeCleanedAt);
      const at = [0, 1, 2, 3, 5, 10, 60].map(k => { store.badgeCleanedAt[units[0]] = now - k * W - 3600e3; return badgeDirtStage(units[0]); });
      store.badgeCleanedAt = JSON.parse(keep);
      const live = units.map(u => badgeDirtStage(u));
      /* the ten-week badge's picture is the one-hour badge's look: the same unit drawn both ways */
      const px = s => renderBadgeStrike(units[0], false, 160, 1, s).getContext('2d').getImageData(0, 0, 160, 160).data;
      const a = px(live[0]), b = px(live[2]); let diff = 0; for(let i = 0; i < a.length; i++) diff += Math.abs(a[i] - b[i]);
      return { at, live, diff, unchanged: JSON.stringify(store.badgeCleanedAt) === keep }; }""", units)
    chk("badgeDirtStage is one value for every clean time (an hour to sixty weeks) and every found badge (%s / %s)" % (st["at"], st["live"]),
        len(set(st["at"])) == 1 and len(set(st["live"])) == 1 and st["at"][0] == st["live"][0], st)
    chk("the ten-week-old badge renders identically to the one cleaned an hour ago (sum |diff| %s)" % st["diff"], st["diff"] == 0, st)
    chk("reading a badge's stage writes nothing (the stored clean times untouched)", st["unchanged"], st)

    # ---- 2. lift the oldest badge, rub it ----
    before = pg.evaluate("""(u) => ({ t: store.badgeCleanedAt[u], saved: (() => { try{ return JSON.parse(localStorage.getItem('class26e.drill.v1')).badgeCleanedAt[u]; }catch(e){ return null; } })() })""", units[0])
    c = pg.evaluate("""() => { const c = document.querySelectorAll('.badges-tab .ncase-cell')[0]; c.scrollIntoView({ block: 'center', behavior: 'instant' });
      const b = c.getBoundingClientRect(); return [b.left + b.width / 2, b.top + b.height / 2]; }""")
    pg.mouse.click(c[0], c[1]); pg.wait_for_timeout(1600)
    up = pg.evaluate("""(re) => { const R = new RegExp(re.slice(1, re.lastIndexOf('/')), 'i'); const ov = document.querySelector('.binspect');
      const s = (typeof badgeInspectNow !== 'undefined' && badgeInspectNow) ? badgeInspectNow.state() : null;
      const cell = document.querySelectorAll('.badges-tab .ncase-cell')[0];
      return { ov: !!ov, found: !!(ov && ov.classList.contains('is-found')), unit: badgeInspectNow && badgeInspectNow.unit, stage: s ? s.stage : null,
               lifted: cell.classList.contains('is-lifted'), empty: !cell.querySelector('image.badge-raster'),
               said: ov ? [...ov.querySelectorAll('*')].filter(e => !e.children.length && !e.hidden && R.test(e.textContent || '')).map(e => e.textContent.trim()) : ['(no view)'],
               face: (ov && (ov.querySelector('.binspect-face.is-front img.is-current') || {}).dataset || {}).dirt }; }""", WORDS)
    chk("a tap lifts the badge out: the view opens on that badge and its slot is left empty (%s)" % {k: up[k] for k in ("ov", "found", "lifted", "empty")},
        up["ov"] and up["found"] and up["unit"] == units[0] and up["lifted"] and up["empty"], up)
    chk("the badge in your hand says nothing about shine, cleaning or rubbing (%s)" % up["said"], up["ov"] and not up["said"], up)
    chk("the badge in your hand is at the same stage as every other (%s vs %s)" % (up["stage"], st["live"][2]), up["stage"] == st["live"][2], up)
    box = pg.evaluate("() => { const r = document.querySelector('.binspect-float').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2, r.width]; }")
    x, y, wd = box
    sparks, stages = 0, []
    pg.mouse.move(x, y); pg.mouse.down()
    for k in range(60):
        pos = (k % 6) if (k % 6) < 3 else 6 - (k % 6)
        pg.mouse.move(x - wd * .08 + pos * wd * .055, y + (k % 2)); pg.wait_for_timeout(16)
        if k % 4 == 0:
            r = pg.evaluate("() => [document.querySelectorAll('.binspect-spark').length, badgeInspectNow ? badgeInspectNow.state().stage : null]")
            sparks = max(sparks, r[0]); stages.append(r[1])
    pg.mouse.up(); pg.wait_for_timeout(900)
    after = pg.evaluate("""(u) => ({ t: store.badgeCleanedAt[u], saved: (() => { try{ return JSON.parse(localStorage.getItem('class26e.drill.v1')).badgeCleanedAt[u]; }catch(e){ return null; } })(),
      stage: badgeInspectNow ? badgeInspectNow.state().stage : null, open: !!document.querySelector('.binspect'),
      face: ((document.querySelector('.binspect-face.is-front img.is-current') || {}).dataset || {}).dirt })""", units[0])
    chk("rubbing the badge does not clean it: its stage never changes and no sparkle plays (%s, sparks %s)" % (sorted(set(stages)), sparks),
        up["ov"] and len(set(stages + [after["stage"]])) == 1 and after["stage"] == up["stage"] and sparks == 0 and after["face"] == up["face"], [stages, after, up["face"]])
    chk("rubbing writes nothing: the stored clean time is the same in the store and the saved copy (%s -> %s)" % (before, {k: after[k] for k in ("t", "saved")}),
        before["t"] == after["t"] and before["saved"] == after["saved"] and before["t"] is not None, [before, after])

    # ---- 3. put it back ----
    cb = pg.evaluate("() => { const b = document.querySelector('.binspect-close'); if(!b) return null; const r = b.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }")
    if cb: pg.mouse.click(cb[0], cb[1])
    pg.wait_for_timeout(1400)
    back = pg.evaluate("""() => { const cell = document.querySelectorAll('.badges-tab .ncase-cell')[0];
      return { ov: !!document.querySelector('.binspect'), lifted: cell.classList.contains('is-lifted'), raster: !!cell.querySelector('image.badge-raster'),
               stage: (cell.querySelector('.badge-tile-art') || {dataset: {}}).dataset.dirt }; }""")
    chk("Close puts the badge back in its slot, at the stage it lifted out at (%s)" % back,
        not back["ov"] and not back["lifted"] and back["raster"] and back["stage"] == case["stages"][0], back)

    # ---- 4. the Profile tour ----
    tour = pg.evaluate("""(re) => { const R = new RegExp(re.slice(1, re.lastIndexOf('/')), 'i');
      try{ return PROFILE_TIPS_289.filter(t => R.test(t.text)).map(t => t.text.slice(-80)); }catch(e){ return ['(no tips: ' + e + ')']; } }""", WORDS)
    chk("the Profile tour's badge-case step does not tell you to rub badges clean (%s)" % tour, not tour, tour)
    chk("no page errors (%s)" % errs[:2], not errs, errs)
    ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
