"""Build 384.97: swiping between top tabs never makes the page wider than the screen (so an iPhone never zooms it out).

Madison's recording (384.94/95, installed iPhone): a swipe from Stats to Profile shrank the whole app to about a third of the
screen - a tiny tab bar in the middle of the bottom, the top tabs tiny in a corner, blank frames - then it snapped back, and
the page came back shifted sideways. attachTabSwipe carries the tab's content up to a screen's width off the side with a
transform while the finger drags and as it lets go (the new tab comes in from the other side); a transform adds to the page's
scrollable overflow, and on an iPhone (and in Chromium's mobile view) a page wider than the screen is zoomed out to fit. The
question slide has had html.q-sliding{overflow-x:clip} for this since build 311; the tab swipe never had it.

Each check drags a real touch (CDP Input.dispatchTouchEvent) across the screen and samples, every frame from the first move to
well after the next tab has landed: the document's scrollWidth against the screen's width, and visualViewport.scale.
  T1  Profile <-> Stats, a slow drag that lets go short (eases back): never wider, never zoomed out
  T2  Profile -> Stats -> Profile, drags that commit: never wider, never zoomed out, and the tab really changed
  T3  the Leaderboard's boards, a committing drag: the same
  T4  after it all the page is not left shifted sideways (scrollX 0) and the clip is off again (html.tab-sliding gone)
  T5  (the same build) Profile: the rank line and "Level N · N badges" under it are at least 8px apart - "the spacing between
      your rank and your level/badges is too tight" (it measured ~9px; a classmate's card has ~19pt)
  T6  (the same build) a rank flare's card (tap a rank's Flare tile: "This isn't animated") moves: its emblem's own parts (.rk-a)
      are running their animations (or a recorded flip-book is on), within 10s
  T7  (the same build) the start sheet's switches all start OFF - Shuffle answer choices too ("always on by default. Turn off
      that") - after the sheet's own reset (resetSheetOptions) and at boot
  T8  (the same build) a finger tapping Time limit leaves no focus ring (outline) round its switch ("puts a blue box around the
      thing, don't do that part")
Devices: iPhone 17 Pro Max installed (440x956) and at Safari's 85% page zoom (518 CSS px wide), and an iPhone SE.
Run:  python3 tools/check-b384-tabswipezoom.py [--against REV|DIR]   (--against origin/main must FAIL T1-T3)"""
import importlib.util, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("glitches", os.path.join(HERE, "check-b384-glitches.py"))
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)   # takes --against from sys.argv
from playwright.sync_api import sync_playwright
chk = G.chk

WATCH = """()=>{ window.__sw = { maxW: 0, minS: 9, n: 0, run: true };
  const w0 = document.documentElement.clientWidth;
  const tick = () => { if(!window.__sw.run) return; const s = window.__sw;
    s.maxW = Math.max(s.maxW, document.documentElement.scrollWidth - w0, document.body.scrollWidth - w0);
    s.minS = Math.min(s.minS, window.visualViewport ? visualViewport.scale : 1); s.n++;
    requestAnimationFrame(tick); };
  requestAnimationFrame(tick); }"""
STOP = "()=>{ window.__sw.run = false; return window.__sw; }"

def drag(pg, x0, x1, y, steps=14, ms=16):
    cdp = getattr(pg, "cdp", None) or pg.ctx.new_cdp_session(pg); pg.cdp = cdp
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x0, "y": y}]})
    for k in range(1, steps + 1):
        x = x0 + (x1 - x0) * k / steps
        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x, "y": y + k * 0.3}]})
        pg.wait_for_timeout(ms)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})

def swipe_check(pg, name, x0, x1, want_change, cur_js):
    w, h = pg.evaluate("[innerWidth, innerHeight]")
    before = pg.evaluate(cur_js)
    pg.evaluate(WATCH)
    drag(pg, x0 * w, x1 * w, int(h * 0.45))
    pg.wait_for_timeout(900)
    s = pg.evaluate(STOP)
    after = pg.evaluate(cur_js)
    chk("[%s] %s: the page never got wider than the screen (%d frames)" % (pg.dev, name, s["n"]), s["maxW"] <= 1, s)
    chk("[%s] %s: the page never zoomed out" % (pg.dev, name), s["minS"] >= 0.99, s)
    if want_change is not None:
        chk("[%s] %s: the tab %s" % (pg.dev, name, "changed" if want_change else "stayed"), (after != before) == want_change, (before, after))

PROF_TAB = "()=>{ const b = document.querySelector('.profiletabs .iconbtn.active'); return b ? b.textContent.trim() : ''; }"
BOARD = "()=>{ const b = document.querySelector('.navsegment.has-seg-thumb .active'); return b ? b.textContent.trim() : ''; }"

def open_retry(br, dev):
    """G.open_dev with a page load allowed 3 minutes: a loaded machine (a dozen gates at once) can take longer than Playwright's
    default 30s to serve and parse a 3MB page. The same set-up otherwise, line for line."""
    from playwright.sync_api import Page
    real_goto = Page.goto
    def slow_goto(self, url, **kw):
        kw.setdefault("timeout", 180000)
        return real_goto(self, url, **kw)
    Page.goto = slow_goto
    try:
        for k in range(3):
            try: return G.open_dev(br, dev, inits=[G.seed_init()], wait=4000)
            except Exception as e:
                print("  (retrying the page load: %s)" % str(e)[:80], flush=True)
        return G.open_dev(br, dev, inits=[G.seed_init()], wait=4000)
    finally:
        Page.goto = real_goto

GAP = """()=>{ const rl = document.querySelector('.pf-standing > .profile-rankline'), id = document.querySelector('.pf-standing .pf-idline');
  if(!rl || !id) return null; const w = rl.querySelector('.pf-rankname') || rl;
  return Math.round((id.getBoundingClientRect().top - w.getBoundingClientRect().bottom) * 10) / 10; }"""

def run_dev(br, dev):
    pg = open_retry(br, dev)
    G.clear_popups(pg)
    pg.evaluate("()=>{ store.lifetime.points = Math.max(store.lifetime.points || 0, 60000); showProfile('profile'); }"); pg.wait_for_timeout(1200); G.clear_popups(pg)
    gap = pg.evaluate(GAP)
    chk("[%s] T5 Profile: the rank line and the level line under it are at least 8px apart (%s)" % (dev, gap), gap is not None and gap >= 8, gap)
    pg.evaluate("()=>{ try{ showUnlockDetail(rankFlareDetail('adept')); }catch(e){ window.__t6err = String(e); } }")
    got = False
    for _ in range(20):
        pg.wait_for_timeout(500)
        if pg.evaluate("()=>{ const a = document.querySelector('.unlock-card-rankflare .unlock-card-art'); if(!a) return false; if(a.querySelector('.cosmic-rank-anim')) return true; return [...a.querySelectorAll('.rk-a')].some(e => e.getAnimations().some(x => x.playState === 'running')); }"): got = True; break
    chk("[%s] T6 a rank flare's card puts the flare's loop on (it moves, as on Home)" % dev, got, pg.evaluate("()=>window.__t6err || document.querySelector('.unlock-card-rankflare .unlock-card-art')?.innerHTML.slice(0,160)"))
    pg.evaluate("()=>document.querySelectorAll('.invite-overlay').forEach(n=>n.remove())")
    sh = pg.evaluate("()=>{ const boot = cfg.shuffle; resetSheetOptions(); return { boot, sheet: cfg.shuffle, recall: cfg.recall, flash: cfg.flashcards, timer: cfg.timer }; }")
    chk("[%s] T7 the start sheet's switches start off (shuffle too)" % dev, sh["boot"] is False and sh["sheet"] is False and not sh["recall"] and not sh["flash"] and sh["timer"] == "off", sh)
    if dev == "promax":
        pg.evaluate("()=>{ cfg.mode='drill'; showSetup(); }"); pg.wait_for_timeout(1500); G.clear_popups(pg)
        pt = pg.evaluate("""()=>{ const c=[...document.querySelectorAll('#stage *')].find(e=>/^\\d+ questions$/.test(e.textContent.trim()) && e.offsetParent); if(!c) return null; const r=(c.closest('button,[role=button],label')||c.parentElement).getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]; }""")
        if pt: pg.touchscreen.tap(pt[0], pt[1]); pg.wait_for_timeout(900)
        pt = pg.evaluate("""()=>{ const b=[...document.querySelectorAll('button')].find(x=>/^Start$/.test(x.textContent.trim()) && x.offsetParent); if(!b) return null; const r=b.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]; }""")
        if pt: pg.touchscreen.tap(pt[0], pt[1]); pg.wait_for_timeout(1500)
        pt = pg.evaluate("""()=>{ const l=[...document.querySelectorAll('.timer-sect .opt')].find(r=>/Time limit/.test(r.textContent)); if(!l) return null; l.scrollIntoView({block:'center'}); const b=l.querySelector('.box')||l; const r=b.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]; }""")
        if pt:
            pg.wait_for_timeout(400); pg.touchscreen.tap(pt[0], pt[1]); pg.wait_for_timeout(700)
        # Chromium does not count a tap's focus as :focus-visible and iOS WebKit does: force the state on the switch the tap
        # focused (CDP CSS.forcePseudoState), as the phone has it, and read the ring off its .box
        pg.evaluate("""()=>{ const l=[...document.querySelectorAll('.timer-sect .opt')].find(r=>/Time limit/.test(r.textContent)); if(l) l.querySelector('input').id = '__gate_tl'; }""")
        try:
            cdp = getattr(pg, "cdp", None) or pg.ctx.new_cdp_session(pg); pg.cdp = cdp
            cdp.send("DOM.enable"); cdp.send("CSS.enable")
            root = cdp.send("DOM.getDocument", {"depth": 1})["root"]["nodeId"]
            nid = cdp.send("DOM.querySelector", {"nodeId": root, "selector": "#__gate_tl"})["nodeId"]
            if nid: cdp.send("CSS.forcePseudoState", {"nodeId": nid, "forcedPseudoClasses": ["focus", "focus-visible"]})
        except Exception as e:
            print("  (could not force focus-visible: %s)" % str(e)[:80])
        pg.wait_for_timeout(200)
        ring = pg.evaluate("""()=>{ const l=[...document.querySelectorAll('.timer-sect .opt')].find(r=>/Time limit/.test(r.textContent)); if(!l) return 'no row'; const b=l.querySelector('.box'); const cs=getComputedStyle(b);
          return { on: l.querySelector('input').checked, outline: cs.outlineStyle, w: cs.outlineWidth, focused: document.activeElement === l.querySelector('input') }; }""")
        chk("[%s] T8 a tap on Time limit turns it on and leaves no ring round its switch" % dev, isinstance(ring, dict) and ring["on"] and ring["outline"] == "none", ring)
        pg.evaluate("()=>{ document.querySelectorAll('.unitoptions-modal, .optionsmodal, .invite-overlay').forEach(n=>n.remove()); }")
    pg.evaluate("()=>showProfile('stats')"); pg.wait_for_timeout(900); G.clear_popups(pg)
    # T1: a short drag towards Profile that is let go early (eases back)
    swipe_check(pg, "T1 Stats, a short drag let go (eases back)", 0.30, 0.52, False, PROF_TAB)
    # T2: commit to Profile, then back to Stats
    swipe_check(pg, "T2 Stats -> Profile, a drag that commits", 0.15, 0.85, True, PROF_TAB)
    swipe_check(pg, "T2 Profile -> Stats, a drag that commits", 0.85, 0.15, True, PROF_TAB)
    # T3: the Leaderboard's boards
    pg.evaluate("()=>showRankings('overall')"); pg.wait_for_timeout(1200); G.clear_popups(pg)
    swipe_check(pg, "T3 Leaderboard, a drag to the next board", 0.85, 0.15, None, BOARD)
    pg.wait_for_timeout(600)
    end = pg.evaluate("()=>({ x: scrollX, clip: document.documentElement.classList.contains('tab-sliding'), w: document.documentElement.scrollWidth - document.documentElement.clientWidth })")
    chk("[%s] T4 afterwards: not shifted sideways, no sideways overflow, the clip is off" % dev, end["x"] == 0 and end["w"] <= 1 and not end["clip"], end)
    chk("[%s] no page errors" % dev, not pg.errs, pg.errs)
    pg.ctx.close()

def main():
    print("build", G.BUILD, "from", G.ROOT)
    with sync_playwright() as p:
        br = p.chromium.launch()
        for dev in ["promax", "pm85", "se"]:
            print("\n" + dev)
            run_dev(br, dev)
        br.close()
    print("\nALL PASS" if not G.fails else "\nFAIL - %d failed" % len(G.fails))
    sys.exit(1 if G.fails else 0)

if __name__ == "__main__":
    main()
