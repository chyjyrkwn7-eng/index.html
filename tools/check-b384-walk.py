#!/usr/bin/env python3
"""Build 384: a full walk of the screens a person moves through, with the tab bar and Pause in mind.

Madison: "We need a full check of the entire app to ensure everything is running perfectly" - after "The bottom tab is
glitching right now, it's showing up in the middle of the screen of review and the unit selection screen and stuff ...
when paused the box is glitched and is showing at the top".

Walked as a person moves (taps where a tap gets there, the screen's own function where the tap needs a finger on a moving
thing), in both classes, on: an iPhone 17 Pro Max installed (440x956) and in a Safari tab (440x797), the same phone at
Safari's 85% page zoom (518x1125 installed, 518x938 in a tab), an iPhone SE (375x667), an iPad Pro 11 (834x1194) and a
Windows laptop (1536x864, a mouse). Screens: Home; Start Studying -> Choose your mode -> the units -> a question -> Pause ->
Resume -> Pause -> Save and exit; a run's results; Review's units and list (scrolled) and its Pause; Profile, Stats,
Customize, the badge case, the rank ladder; the Leaderboard (the academy's); the Calendar; Settings and every page of it,
Contributors, Legal; the chat; Account -> Sign out's sheet; and, signed out, Welcome and Sign in.

On every screen:
  - the tab bar is at the bottom of the screen (its foot within 150px of the screen's, nothing of it off the screen) where
    it is shown, and shown / hidden where the screen says (shown on Home, the units, Review's list; hidden on a question,
    Pause and the sign-in screens);
  - the app's own fixed controls (the tab bar, its search circle, Pause, the chat button) are on the screen, Pause and the
    chat button in the top quarter, the bar and its circle in the bottom quarter - nothing of theirs mid-screen;
  - no two buttons on fixed things overlap (past a fifth of the smaller, or their words on each other), and scrolled to its end,
    the screen's last button is not under the tab bar;
  - no button cuts its words off;
  - Pause's card (on a pause screen) on the middle of the screen - or as high as it may go, under a long progress meter;
  - no sideways scroll; no page errors.
Found by it and fixed in this build: Pause's "Save and exit" cut to "Save and exi" on an iPhone SE (the pair went to one column
below 360px; now below 400px). Run it --against 34765be / 42bbffa to see the same on the builds before.
Run:  python3 tools/check-b384-walk.py [device ...]   (devices: promax promax-tab pm85 pm85-tab se ipad laptop)
      python3 tools/check-b384-walk.py --against REV|DIR
"""
import importlib.util, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
# the devices, the cloud, the seeds and the page set-up are check-b384-glitches.py's (run with no sections)
argv = sys.argv[1:]
against = []
if "--against" in argv:
    i = argv.index("--against"); against = argv[i:i + 2]; del argv[i:i + 2]
want = argv or ["promax", "promax-tab", "pm85", "pm85-tab", "se", "ipad", "laptop"]
sys.argv = [sys.argv[0]] + against
spec = importlib.util.spec_from_file_location("glitches", os.path.join(HERE, "check-b384-glitches.py"))
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)
from playwright.sync_api import sync_playwright
chk = G.chk

LOOK = r"""(label)=>{ const vw=innerWidth, vh=innerHeight;
  const vis = e => { if(!e || e.hidden) return false; const c=getComputedStyle(e); if(c.display==='none'||c.visibility==='hidden'||+c.opacity<0.05) return false;
    const r=e.getBoundingClientRect(); return r.width>0 && r.height>0; };
  const box = e => { const r=e.getBoundingClientRect(); return { l:r.left, t:r.top, r:r.right, b:r.bottom, w:r.width, h:r.height }; };
  const name = e => e.id ? '#'+e.id : (e.tagName.toLowerCase() + (typeof e.className==='string' && e.className ? '.'+e.className.trim().split(/\s+/)[0] : ''));
  const out = { label, problems: [], tabs: false };
  const tb=document.getElementById('bottomtabs');
  out.tabs = vis(tb) && getComputedStyle(tb).position === 'fixed';
  if(out.tabs){ const b=box(tb); out.tabsBox=b;
    if(b.b > vh + 1 || b.t < 0 || b.b < vh - 150) out.problems.push('the tab bar at ' + Math.round(b.t) + '-' + Math.round(b.b) + ' of ' + vh);
    if(b.l < -1 || b.r > vw + 1) out.problems.push('the tab bar off the side ' + Math.round(b.l) + '-' + Math.round(b.r)); }
  // the app's own fixed controls and their bands
  const BANDS = [['#bottomtabs','bottom'], ['#tabsearch','bottom'], ['#pausebtn','top'], ['#chatdock-btn','top']];
  const chrome = [];
  BANDS.forEach(([sel, band]) => { const e=document.querySelector(sel); if(!vis(e)) return; const p=getComputedStyle(e).position; if(p!=='fixed') return;
    const b=box(e); chrome.push([sel, e, b]);
    if(b.t < -1 || b.b > vh + 1 || b.l < -1 || b.r > vw + 1) out.problems.push(sel + ' off the screen ' + JSON.stringify([Math.round(b.l), Math.round(b.t), Math.round(b.r), Math.round(b.b)]));
    const mid=(b.t+b.b)/2;
    if(band==='top' && mid > vh * 0.25) out.problems.push(sel + ' not at the top: its middle at ' + Math.round(mid) + ' of ' + vh);
    if(band==='bottom' && mid < vh * 0.75) out.problems.push(sel + ' not at the bottom: its middle at ' + Math.round(mid) + ' of ' + vh); });
  // every button on anything fixed (the bar's tabs, Pause, the chat button, a pinned header's, a floating pill's), against each
  // other: no two overlap (a fixed row is a container - it is its buttons that must not sit on one another)
  const BTN = 'button, a[href], [role=button]';
  const roots=[]; const tw=document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT); let n;
  while((n = tw.nextNode())){ if(getComputedStyle(n).position !== 'fixed' || !vis(n)) continue; const b=box(n);
    if(b.w >= vw * 0.9 && b.h >= vh * 0.6) continue;   // a full-screen layer (a backdrop, a sheet's dim)
    if(n.closest('[aria-hidden=true]')) continue;
    roots.push(n); }
  const btns=[]; roots.forEach(r => (r.matches(BTN) ? [r] : [...r.querySelectorAll(BTN)]).forEach(b => {
    if(btns.includes(b) || !vis(b) || b.closest('[aria-hidden=true]')) return; const bb=box(b); if(bb.w < 8 || bb.h < 8) return; btns.push(b); }));
  const all = btns.map(b => [name(b), b, box(b)]);
  // (two neighbours' tap areas may share a few px - the tab bar's do, by 5-7px, with their words well apart - so an overlap is
  // one past a fifth of the smaller button either way, or their words on each other)
  const ink = e => { const ws=[...e.querySelectorAll('.bottomtab-label, .bottomtab-icon, span, svg')].filter(vis).map(box); return ws.length ? ws : [box(e)]; };
  const hit = (a, b, f) => { const ix=Math.min(a.r,b.r)-Math.max(a.l,b.l), iy=Math.min(a.b,b.b)-Math.max(a.t,b.t); return ix > Math.max(2, f * Math.min(a.w, b.w)) && iy > Math.max(2, f * Math.min(a.h, b.h)) ? [ix, iy] : null; };
  for(let i=0;i<all.length;i++) for(let j=i+1;j<all.length;j++){ const [na, ea, a] = all[i], [nb, eb, b] = all[j];
    if(ea.contains(eb) || eb.contains(ea)) continue;
    const o = hit(a, b, .2) || (hit(a, b, 0) && ink(ea).some(x => ink(eb).some(y => hit(x, y, 0))) ? hit(a, b, 0) : null);
    if(o) out.problems.push(na + ' overlaps ' + nb + ' (' + Math.round(o[0]) + 'x' + Math.round(o[1]) + ')'); }
  // words cut off by their button (the screen's and the fixed controls' - a button that clips, and has more than it shows)
  const btnAll = [...document.querySelectorAll('#stage button, #stage [role=button]')].filter(vis).concat(btns);
  [...new Set(btnAll)].forEach(b => { if(b.closest('[aria-hidden=true]')) return; const cs=getComputedStyle(b);
    if(cs.overflowX === 'visible') return;   // nothing is cut off (a badge hanging off the chat button is meant to)
    if(b.scrollWidth > b.clientWidth + 1 && b.clientWidth > 0 && (b.textContent||'').trim()) out.problems.push('words cut off in ' + name(b) + ' "' + b.textContent.trim().slice(0, 24) + '" (' + b.scrollWidth + ' > ' + b.clientWidth + ')'); });
  const st=document.querySelector('#stage .pause-stack');
  if(vis(st)){ const b=box(st); const mid=(b.t+b.b)/2; const pt=st.closest('.panel') ? box(st.closest('.panel')).t : 0;
    // on the middle - or as high as it may go: under the panel's top (a long progress meter pushes it down on a small phone)
    if(Math.abs(mid - vh/2) > 40 && b.t > pt + 12) out.problems.push("Pause's card middle at " + Math.round(mid) + ' of ' + vh); }
  const over = document.documentElement.scrollWidth - vw; if(over > 0) out.problems.push('sideways scroll ' + over + 'px');
  out.fixedCount = all.length;
  return out; }"""
# scrolled to the end: the last button on the screen is not under the tab bar
UNDER = r"""async ()=>{ const tb=document.getElementById('bottomtabs'); if(!tb || tb.hidden || getComputedStyle(tb).display==='none') return null;
  /* a jump, not the person's smooth scrolling (a glide still under way reads as a button under the bar) */
  const de=document.documentElement, was=de.style.scrollBehavior; de.style.scrollBehavior='auto'; void getComputedStyle(de).scrollBehavior;
  window.scrollTo(0, de.scrollHeight); de.style.scrollBehavior=was; await new Promise(r=>setTimeout(r, 450));
  const bs=[...document.querySelectorAll('#stage button, #stage a, #stage [role=button]')].filter(b=>{ const r=b.getBoundingClientRect(), c=getComputedStyle(b);
    return r.width>8 && r.height>8 && c.visibility!=='hidden' && +c.opacity>0.05 && !b.closest('[aria-hidden=true]') && r.bottom > 0 && r.top < innerHeight; });
  if(!bs.length) return null; const last=bs.reduce((a,b)=>b.getBoundingClientRect().bottom > a.getBoundingClientRect().bottom ? b : a);
  const r=last.getBoundingClientRect(); const x=r.left + r.width/2, y=Math.min(innerHeight - 1, r.top + r.height/2);
  const hit=document.elementFromPoint(x, y); const t=tb.getBoundingClientRect();
  const under = !!hit && tb.contains(hit) && !last.contains(hit);
  const res = { last: (last.textContent||'').trim().slice(0,24) || last.className, under, y: Math.round(r.bottom), bar: Math.round(t.top) };
  de.style.scrollBehavior='auto'; void getComputedStyle(de).scrollBehavior; window.scrollTo(0, 0); de.style.scrollBehavior=was; await new Promise(r=>setTimeout(r, 200)); return res; }"""
START_DRILL = G.START_DRILL
FINISH = """async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms));
  theme.reduceMotion = true; theme.muteBanners = true;
  order.forEach((qi, k) => { attempts[qi] = k < 2 ? 2 : 1; picked[qi] = optionOrder(qi).indexOf(QUESTIONS[qi].answer); });
  stopQuestionTimer(); summarize(); await wait(1500);
  for(let t = 0; t < 10 && document.querySelector('#stage .rs-final.rs-unarmed'); t++){ const p=document.querySelector('#stage .rs-screen'); p && p.dispatchEvent(new MouseEvent('click', { bubbles: true })); await wait(300); } }"""
def click_or(pg, sel, js):
    try:
        if pg.evaluate("(s)=>{ const b=document.querySelector(s); if(!b) return false; const r=b.getBoundingClientRect(); return r.width>0 && r.height>0; }", sel):
            pg.click(sel, timeout=2500); return
    except Exception:
        pass
    pg.evaluate(js)

def walk(br, dev, cls):
    pg = G.open_dev(br, dev, [G.seed_init(cls)])
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(1000); G.clear_popups(pg)
    seen = []
    def at(label, tabs=None, settle=900, under=False):
        pg.wait_for_timeout(settle); G.clear_popups(pg)
        r = pg.evaluate(LOOK, label)
        if tabs is not None and r["tabs"] != tabs:
            r["problems"].append("the tab bar %s here" % ("shown" if r["tabs"] else "hidden"))
        if under:
            u = pg.evaluate(UNDER)
            if u and u["under"]: r["problems"].append("the last button (%s, foot %s) under the tab bar (top %s)" % (u["last"], u["y"], u["bar"]))
        seen.append(r)
    at("Home", True)
    click_or(pg, ".panel.home.screen-home-actual .playbtn", "()=>showModeSelect()"); at("Choose your mode", None, under=True)
    click_or(pg, ".modecard[data-mode=drill]", "()=>{ cfg.mode='drill'; showSetup(); }"); at("the units (Drill)", True, under=True)
    pg.evaluate("()=>window.scrollTo(0, 800)"); at("the units, scrolled", True, 500)
    pg.evaluate(START_DRILL); at("a question", False, 1800)
    click_or(pg, "#pausebtn", "()=>pauseRun()"); at("Pause", False)
    click_or(pg, "#resumebtn", "()=>resumeRun()"); at("Resume", False)
    click_or(pg, "#pausebtn", "()=>pauseRun()"); at("Pause again", False)
    click_or(pg, "#pause-save", "()=>saveAndExitTest()"); at("Save and exit", None, 1400)
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(600)
    pg.evaluate(START_DRILL); pg.wait_for_timeout(1500)
    pg.evaluate(FINISH); at("the results", None, 600, under=True)
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(600)
    click_or(pg, ".panel.home.screen-home-actual .playbtn", "()=>showModeSelect()"); pg.wait_for_timeout(700)
    click_or(pg, ".modecard[data-mode=review]", "()=>{ cfg.mode='review'; showSetup(); }"); at("Review's units", True, under=True)
    pg.evaluate("()=>{ cfg.mode='review'; showAnswerReview([topicsIn(QUESTIONS)[0]], 'all'); }"); at("Review's list", True)
    pg.evaluate("()=>window.scrollTo(0, 2500)"); at("Review's list, scrolled", True, 500)
    click_or(pg, "#pausebtn", "()=>pauseRun()"); at("Review paused", None)
    click_or(pg, "#resumebtn", "()=>resumeRun()"); at("Review resumed", True)
    click_or(pg, "#bottomtab-profile", "()=>showProfile()"); at("Profile", None, under=True)
    pg.evaluate("()=>showProfile('stats')"); at("Stats", None, under=True)
    click_or(pg, "#stage .profile-customize-btn", "()=>showCustomize()"); at("Customize", None, under=True)
    pg.evaluate("()=>showProfile()"); pg.wait_for_timeout(700)
    click_or(pg, "#stage .pf-case-count", "()=>showRanksScreen('badges')"); at("the badge case", None, under=True)
    pg.evaluate("()=>showProfile()"); pg.wait_for_timeout(700)
    click_or(pg, "#stage .pf-goal-foot", "()=>showRanksScreen()"); at("the rank ladder", None, under=True)
    if cls == "academy":
        click_or(pg, "#bottomtab-rewards", "()=>showRankings('overall')"); at("the Leaderboard", True, 1500, under=True)
        click_or(pg, "#bottomtab-calendar", "()=>showCalendarTab()"); at("the Calendar", True, under=True)
        pg.evaluate("()=>showAppearance()"); at("Settings", None, under=True)
    else:
        # Fire Code's bar: Home, Profile, Stats, Settings
        click_or(pg, "#bottomtab-stats", "()=>showProfile('stats')"); at("the Stats tab", True, under=True)
        click_or(pg, "#bottomtab-settings", "()=>showAppearance()"); at("the Settings tab", True, under=True)
    for page in ["sound", "study", "motion", "sync", "share", "rankings", "account"]:
        if page == "rankings" and cls == "ifc": continue
        pg.evaluate("(p)=>showAppearance({ page: p })", page); at("Settings > " + page, None, 700, under=True)
    pg.evaluate("()=>showCredits()"); at("Contributors", None, under=True)
    pg.evaluate("()=>showSettingsText('legal')"); at("Legal", None, 700, under=True)
    pg.evaluate("()=>{ showHome(); }"); pg.wait_for_timeout(700)
    click_or(pg, "#chatdock-btn", "()=>openChatDock()"); at("the chat", None, 1100)
    pg.evaluate("()=>{ try{ closeChatDock(); }catch(e){} }"); pg.wait_for_timeout(500)
    pg.evaluate("()=>showAppearance({ page: 'account' })"); pg.wait_for_timeout(800)
    click_or(pg, "#stage .signout-row", "()=>showSignOutConfirm()"); at("Sign out's sheet", None, 700)
    click_or(pg, "#signout-confirm .signout-cancel", "()=>document.getElementById('signout-confirm')?.remove()"); at("Sign out cancelled", None, 600)
    errs = pg.errs[:]
    pg.ctx.close()
    # signed out: Welcome and Sign in
    if cls == "academy":
        pg = G.open_dev(br, dev, [G.seed_init(signed_out=True)])
        if pg.evaluate("()=>!!document.querySelector('.gs-page .gs-go')"): pg.click(".gs-go"); pg.wait_for_timeout(1100)
        at("Welcome", False)
        click_or(pg, ".welcome-signin", "()=>showWelcomeCodeEntry()"); at("Sign in", False)
        errs += pg.errs
        pg.ctx.close()
    return seen, errs

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G.CHROME)
    for dev in want:
        for cls in ["academy", "ifc"]:
            seen, errs = walk(br, dev, cls)
            bad = [(r["label"], r["problems"][:3]) for r in seen if r["problems"]]
            print("  INFO %s %s: the tab bar up on %d of %d screens; %d buttons on fixed things compared" % (dev, cls, sum(1 for r in seen if r["tabs"]), len(seen),
                  sum(r.get("fixedCount", 0) for r in seen)), flush=True)
            chk("%s %s: %d screens walked - the tab bar at the bottom or hidden where it should be, the fixed controls in their places, nothing "
                "overlapping, nothing under the bar, no sideways scroll" % (dev, cls, len(seen)), not bad, bad[:6])
            chk("%s %s: no page errors" % (dev, cls), not errs, errs[:3])
    br.close()
print("ALL PASS" if not G.fails else "SOME FAILED")
sys.exit(0 if not G.fails else 1)
