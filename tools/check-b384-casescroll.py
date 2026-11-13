"""Build 384.93: a finger on the badge case scrolls the page (and on every other grid of small controls).
Madison: "When looking at the badge case, you can't use the case to scroll up and down."

On an iPhone the app lays a native <input type=checkbox switch> over a small control, because that is the only way a page
gets the Taptic tick (NovaSound). WebKit gives a touch that STARTS on a native switch to the switch (it handles the
touchstart, so the page does not pan), so a grid of small controls each carrying one is a wall a finger cannot scroll by.
Every badge slot in the case is a small button: on main 384.92 all 24 (academy) and 58 (Fire Code) took a switch - 47% of
Fire Code's Badges screen - and Customize's 26 characters and the theme swatches were the same. A grid now takes the
LABEL instead (.nova-hlb over the control, its own 1px switch out of a finger's reach): a finger on it scrolls the page
as on any element, a tap on it still clicks the switch (the tick) and the control.

Chromium has no Taptic Engine and does not hand a touch to a switch, so a drag test cannot see the bug (S5 passes on
both builds and is kept only to show nothing ELSE holds the finger). What it can read is what a finger lands on:
  S1  the badge case, both classes, every slot scrolled into view: the slot's own label, never a native switch;
  S2  Customize > Character and > Theme color: every character and swatch the same;
  S3  every screen in SCREENS that scrolls, scrolled top to bottom, both classes: no 150px band of the page clear of the
      fixed chrome (tab bar, top row, chat button) is more than 30% native switch (the units screen's tick circles, the
      sparsest legitimate case, are ~15%; the case was ~90%);
  S4  a tap still works and still ticks: a touch tap on a found badge opens its card and toggles its label's switch once;
      a tap on a character you hold selects it; a tap on a theme swatch you hold applies it;
  S5  a touch drag that starts on the case scrolls the page (both builds; see above).
Phone = iPhone 17 Pro Max installed (440x956) and iPhone SE (375x667), an iPhone user agent with touch (the haptic layer mounts).
Run:  python3 tools/check-b384-casescroll.py [--against REV|DIR]   (--against origin/main must FAIL S1-S3)"""
import importlib.util, json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("glitches", os.path.join(HERE, "check-b384-glitches.py"))
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)   # takes --against from sys.argv
from playwright.sync_api import sync_playwright
chk = G.chk

# what a finger at the middle of each control lands on: 'label' (its own scroll-safe label), 'switch' (its own native
# switch: the wall), 'other' (something else's), 'none'
LAND = """(sel)=>{
  const nat = i => !!(i && i.tagName === 'INPUT' && i.type === 'checkbox' && i.hasAttribute('switch'));
  const fixedUp = e => { for(let x = e; x && x.nodeType === 1; x = x.parentElement){ const p = getComputedStyle(x).position; if(p === 'fixed' || p === 'sticky') return true; } return false; };
  const out = [];
  let i = 0;
  for(const el of document.querySelectorAll(sel)){
    if(!el.dataset.gateI) el.dataset.gateI = String(i); i++;
    const r = el.getBoundingClientRect(); if(r.width < 4 || r.height < 4) continue;
    const x = r.left + r.width / 2, y = r.top + r.height / 2; if(y < 0 || y > innerHeight || x < 0 || x > innerWidth) continue;
    const h = document.elementFromPoint(x, y); if(!h) continue;
    if(fixedUp(h) && !el.contains(h)) continue;   /* under the fixed chrome: not this control's question */
    let got = 'none';
    if(nat(h)) got = el.contains(h) ? 'switch' : 'other';
    else { const lb = h.closest ? h.closest('label') : null; if(lb && nat(lb.control)) got = el.contains(lb) ? 'label' : 'other'; }
    out.push({ key: el.dataset.gateI, el: (el.getAttribute('aria-label') || el.className || el.tagName).toString().slice(0, 50), got, y: Math.round(y) });
  }
  return out;
}"""
# the switch share of each 150px band of the page clear of the fixed chrome, at the current scroll
BANDS = """()=>{
  const nat = i => !!(i && i.tagName === 'INPUT' && i.type === 'checkbox' && i.hasAttribute('switch') && getComputedStyle(i).pointerEvents !== 'none');
  const fixedUp = e => { for(let x = e; x && x.nodeType === 1; x = x.parentElement){ const p = getComputedStyle(x).position; if(p === 'fixed' || p === 'sticky') return true; } return false; };
  const rows = [];
  for(let y = 6; y < innerHeight - 6; y += 10){ let n = 0, on = 0;
    for(let x = 6; x < innerWidth - 6; x += 10){ const h = document.elementFromPoint(x, y); if(!h || fixedUp(h)) continue; n++; if(nat(h)) on++; }
    rows.push({ y, n, on }); }
  let worst = { share: 0, y: 0 };
  for(let i = 0; i + 15 <= rows.length; i++){ let n = 0, on = 0; for(let j = i; j < i + 15; j++){ n += rows[j].n; on += rows[j].on; }
    if(n > 200 && on / n > worst.share) worst = { share: Math.round(on / n * 100) / 100, y: rows[i].y }; }
  return worst;
}"""
SCROLLER = """()=>{ const se = document.scrollingElement; if(se.scrollHeight > innerHeight + 4) return null;
  let best = null; for(const e of document.querySelectorAll('#stage *')){ const c = getComputedStyle(e);
    if(/(auto|scroll)/.test(c.overflowY) && e.scrollHeight > e.clientHeight + 40 && (!best || e.clientHeight > best.clientHeight)) best = e; }
  if(best) best.setAttribute('data-gate-scroller', ''); return best ? 'inner' : 'none'; }"""
def scroll_steps(pg):
    """scroll the page (or its inner scroller) top to bottom in 70%-of-a-screen steps; yields after each step"""
    kind = pg.evaluate(SCROLLER)
    if kind == "none": yield 0; return
    js_max = "()=>{ const e = document.querySelector('[data-gate-scroller]') || document.scrollingElement; return e.scrollHeight - e.clientHeight; }"
    js_to = "(y)=>{ const e = document.querySelector('[data-gate-scroller]') || document.scrollingElement; e.scrollTo({ top: y, behavior: 'instant' }); }"
    mx = pg.evaluate(js_max); y = 0; step = int(pg.evaluate("innerHeight") * .7)
    while True:
        pg.evaluate(js_to, y); pg.wait_for_timeout(220); yield y
        if y >= mx: break
        y = min(mx, y + step)
    pg.evaluate(js_to, 0); pg.wait_for_timeout(120)

def land_all(pg, sel):
    seen = {}
    for _ in scroll_steps(pg):
        for r in pg.evaluate(LAND, sel):
            key = r["key"]   # each control once; a reading where it is clear of the chrome replaces one where it was not
            if key not in seen or seen[key]["got"] != "label": seen[key] = r
    return list(seen.values())

def settle(pg, js, wait=2600):
    pg.evaluate(js); pg.wait_for_timeout(wait); G.clear_popups(pg); pg.wait_for_timeout(300)

def tap(cdp, x, y, hold=0.06):
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]}); time.sleep(hold)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})

SCREENS = [
    ("Profile > Badges", "()=>showProfile('badges')"), ("Customize > Character", "()=>showCustomize('character')"),
    ("Customize > Theme color", "()=>showCustomize('theme')"), ("Customize > Banner", "()=>showCustomize('banner')"),
    ("Customize > Hundo effect", "()=>showCustomize('fx')"), ("Customize", "()=>showCustomize()"),
    ("Profile", "()=>showProfile()"), ("Profile > Stats", "()=>showProfile('stats')"), ("Profile > Rank", "()=>showProfile('ranks')"),
    ("units (Drill)", "()=>{ cfg.mode='drill'; showSetup(); }"), ("Settings", "()=>showAppearance()"), ("Calendar", "()=>showCalendarTab()"),
    ("Leaderboard", "()=>showRankings('overall')"), ("Friends", "()=>showFriends()"), ("Review's list", "()=>{ cfg.mode='review'; showAnswerReview([topicsIn(QUESTIONS)[0]], 'all'); }"),
    ("Release history", "()=>showReleaseHistory()"), ("Credits", "()=>showCredits()"), ("Virtual Room setup", "()=>showVirtualRoomSetup()"),
]

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G.CHROME)
    for cls in ["academy", "ifc"]:
        for dev in ["promax", "se"]:
            pg = G.open_dev(br, dev, inits=[G.seed_init(cls)])
            tag = "%s %s" % (cls, dev)
            if not pg.evaluate("()=>NovaSound.canTaptic()"):
                chk("[%s] the haptic layer is on (an iPhone)" % tag, False, "canTaptic false"); pg.ctx.close(); continue
            print("\n%s - build %s" % (tag, G.BUILD), flush=True)
            # S1 the case
            settle(pg, "()=>showProfile('badges')", 3200)
            r = land_all(pg, ".ncase-cell")
            n_all = pg.evaluate("()=>document.querySelectorAll('.ncase-cell').length")
            bad = [x for x in r if x["got"] != "label"]
            chk("[%s] S1 the badge case: every slot (%d of %d read) lands on its own label, none on a native switch" % (tag, len(r), n_all),
                len(r) >= n_all - 2 and n_all >= 16 and not bad, {"bad": bad[:6], "kinds": {k: sum(1 for x in r if x["got"] == k) for k in ("switch", "label", "other", "none")}})
            # S2 characters and swatches
            for name, js, sel, minimum in [("Customize > Character", "()=>showCustomize('character')", ".avatarchar-option", 12),
                                           ("Customize > Theme color", "()=>showCustomize('theme')", ".swatch", 6)]:
                settle(pg, js)
                r = land_all(pg, sel)
                bad = [x for x in r if x["got"] != "label"]
                chk("[%s] S2 %s: every one (%d) lands on its own label, none on a native switch" % (tag, name, len(r)),
                    len(r) >= minimum and not bad, {"bad": bad[:6], "kinds": {k: sum(1 for x in r if x["got"] == k) for k in ("switch", "label", "other", "none")}})
            # S3 no wall anywhere
            walls = []
            for name, js in SCREENS:
                try: settle(pg, js, 2200)
                except Exception as e: walls.append((name, "ERR " + str(e)[:80])); continue
                worst = {"share": 0}
                for y in scroll_steps(pg):
                    w = pg.evaluate(BANDS)
                    if w["share"] > worst["share"]: worst = dict(w, scroll=y)
                if worst["share"] > .30: walls.append((name, worst))
            chk("[%s] S3 no screen of %d has a 150px band more than 30%% native switch (a wall a finger cannot scroll by)" % (tag, len(SCREENS)),
                not walls, walls)
            if dev == "promax":
                cdp = pg.ctx.new_cdp_session(pg)
                # S4 a tap still works and ticks
                settle(pg, "()=>showProfile('badges')", 3200)
                pg.evaluate("()=>{ const t = document.querySelector('.ncase-cell'); t && t.scrollIntoView({ block: 'center', behavior: 'instant' }); }"); pg.wait_for_timeout(400)
                pt = pg.evaluate("""()=>{ const t = document.querySelector('.ncase-cell'); const r = t.getBoundingClientRect(); const sw = t.querySelector('.nova-hlb-sw, .nova-hsw');
                  window.__s4 = { clicks: 0, sw }; t.addEventListener('click', () => window.__s4.clicks++);
                  if(sw) window.__s4.was = sw.checked; return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; }""")
                tap(cdp, pt["x"], pt["y"]); pg.wait_for_timeout(1400)
                s4 = pg.evaluate("""()=>({ clicks: window.__s4.clicks, toggled: !!window.__s4.sw && window.__s4.sw.checked !== window.__s4.was,
                  open: !!document.querySelector('.binspect, .binspect-hit, .badge-inspect, [class*="binspect"]') })""")
                chk("[%s] S4 a tap on a badge slot opens its card, clicks it once and ticks (its switch toggles)" % tag,
                    s4["clicks"] == 1 and s4["toggled"] and s4["open"], s4)
                pg.evaluate("()=>{ try{ closeBadgeInspect && closeBadgeInspect(); }catch(e){} }")
                settle(pg, "()=>showCustomize('character')")
                pt = pg.evaluate("""()=>{ const o = [...document.querySelectorAll('.avatarchar-option')].find(b => !b.matches('.is-locked, [aria-disabled=true]') && !b.closest('.is-selected') && !b.classList.contains('is-selected') && b.getBoundingClientRect().top > 140);
                  if(!o) return null; o.scrollIntoView({ block: 'center', behavior: 'instant' }); const r = o.getBoundingClientRect(); window.__was = store.avatarChar;
                  return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; }""")
                if pt:
                    pg.wait_for_timeout(300); tap(cdp, pt["x"], pt["y"]); pg.wait_for_timeout(900)
                chk("[%s] S4 a tap on a character you hold selects it" % tag, bool(pt) and pg.evaluate("()=>store.avatarChar !== window.__was"), pt)
                settle(pg, "()=>showCustomize('theme')")
                pt = pg.evaluate("""()=>{ const o = [...document.querySelectorAll('.swatch-cell:not(.is-locked) .swatch')].find(b => !b.classList.contains('is-active') && !b.classList.contains('is-selected') && b.getBoundingClientRect().top > 140);
                  if(!o) return null; o.scrollIntoView({ block: 'center', behavior: 'instant' }); const r = o.getBoundingClientRect(); window.__was = theme.accent;
                  return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; }""")
                if pt:
                    pg.wait_for_timeout(300); tap(cdp, pt["x"], pt["y"]); pg.wait_for_timeout(900)
                chk("[%s] S4 a tap on a theme swatch you hold applies it" % tag, bool(pt) and pg.evaluate("()=>theme.accent !== window.__was"), pt)
                # S5 a drag from the case scrolls the page
                settle(pg, "()=>showProfile('badges')", 3200)
                kind = pg.evaluate(SCROLLER)
                if kind != "none":
                    pg.evaluate("()=>{ const t = document.querySelector('.ncase-cell'); t.scrollIntoView({ block: 'center', behavior: 'instant' }); }"); pg.wait_for_timeout(300)
                    y0 = pg.evaluate("()=>(document.querySelector('[data-gate-scroller]') || document.scrollingElement).scrollTop")
                    pt = pg.evaluate("()=>{ const r = document.querySelector('.ncase-cell').getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; }")
                    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": pt["x"], "y": pt["y"]}]})
                    for i in range(1, 13):
                        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": pt["x"], "y": pt["y"] - i * 14}]}); time.sleep(.016)
                    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []}); pg.wait_for_timeout(700)
                    y1 = pg.evaluate("()=>(document.querySelector('[data-gate-scroller]') || document.scrollingElement).scrollTop")
                    chk("[%s] S5 a drag that starts on a badge slot scrolls the page (passes on both builds: Chromium does not give a touch to a switch)" % tag,
                        y1 - y0 > 40, {"before": y0, "after": y1})
            chk("[%s] no page errors" % tag, not pg.errs, pg.errs[:3])
            pg.ctx.close()
    br.close()
print("\n%s - %d failed" % ("ALL PASS" if not G.fails else "FAIL", len(G.fails)))
sys.exit(1 if G.fails else 0)
