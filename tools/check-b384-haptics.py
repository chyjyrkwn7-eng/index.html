"""Build 384: haptics everywhere on an iPhone.
Madison: "Haptic Touch is inconsistent right now. Haptic Touch isn't working on the planet system, and it's not working in
other places randomly. Ensure haptic touch is good to go."
iOS has no navigator.vibrate. The only tick a page can get is a native <input type=checkbox switch> toggled by a TRUSTED
click inside a user gesture (WebKit CheckboxInputType::willDispatchClick -> performSwitchVisuallyOnAnimation). A real
finger on the switch gives one; so does a real finger on a <label> whose control is a switch (the label's
dispatchSimulatedClick is trusted when the tap was). A script's click never does (iOS 26.5+).
So this gate, as an iPhone (its user agent, touch, no vibrate - the haptic layer mounts), reads the page: for every
primary tappable surface on every screen, what a finger at its centre lands on (elementFromPoint), and passes it only when
that is a native switch of its own, or a label of its own whose control is a native switch. It also checks:
(1) the planet system's switches are there the moment Home is built, not ~0.5s+ after (every return to Home);
(2) a mode card's head switch is not taken off (and put back) by a tap elsewhere on that screen (the click prune did);
(3) a tap on a control ticked through a label reaches the control once, toggles the label's switch, and runs no scripted
    tick on top (the scripted tick does nothing on iOS 26.5+, and on 17.4-26.4 it would be a second tick);
(4) nothing is put in under a finger that is down (iOS drops a tap whose element changed under it);
(5) Settings > Sound & Haptics > Haptics off takes every switch and label away, on puts them back (passes on both builds:
    a guard on the toggle, which existed).
Chromium has no Taptic Engine: this holds the wiring, not the buzz.
Run:  python3 tools/check-b384-haptics.py   (--against OLD/index.html must FAIL;  ONLY=surfaces|planet|mode|label|finger|toggle|tab)"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
    def patched_old(insets):
        t, r, b, l = insets; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
        return g["INSET_RE"].sub(lambda m: v[m.group(1)], OLD)
    g["patched"] = patched_old
from playwright.sync_api import sync_playwright
srv, url = g["serve"]()
ONLY = os.environ.get("ONLY", "")
INIT = """(()=>{ if(localStorage.getItem('class26e.drill.v1')) return;
 localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-0384');
 ['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card','class26e.getstarted'].forEach(k=>localStorage.setItem(k,'1'));
 localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.penal256578.seen','1'); })()"""
d = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]())); d["publicId"] = "pubtest0384h"; d["firstName"] = "Casey"; d["novaMet"] = 99
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1"
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:700], flush=True)
def tap(cdp, x, y, hold=0.08):
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]}); time.sleep(hold)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
def page(br, installed=True, w=440, h=956):
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=2, has_touch=True, is_mobile=True, user_agent=UA)
    if installed: ctx.add_init_script(g["STANDALONE"])
    ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]()))
    pg = ctx.new_page(); body = g["patched"]((62, 0, 34, 0))
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.add_init_script(INIT % json.dumps(json.dumps(d)))
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    pg.goto(url); pg.wait_for_timeout(3000); pg.evaluate("document.getElementById('splashscreen')?.remove()")
    pg.evaluate("()=>{ try{ homeUnlocksOwed=()=>false; }catch(e){} theme.reduceMotion=false; showHome(); }"); pg.wait_for_timeout(2500)
    return ctx, pg, ctx.new_cdp_session(pg), errs

# What a finger at the middle of each surface lands on. A surface passes when that is a native switch of its own (inside
# it, or the switch's control is it) or a label of its own whose control is a native switch. Everything is read off the page.
SURF = """(o)=>{
  const root = o.root ? document.querySelector(o.root) : document.body; if(!root) return { missing: o.root };
  const sel = o.sel || "button, [role='button'], a[href], label.pick, label.opt, .choice, .cosmic-sphere-hsw, .fc-face";
  const vis = el => { const r = el.getBoundingClientRect(); if(r.width < 2 || r.height < 2) return null;
    const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    if(cx < 1 || cy < 1 || cx > innerWidth - 1 || cy > innerHeight - 1) return null;
    let op = 1; for(let x = el; x && x.nodeType === 1; x = x.parentElement){ const c = getComputedStyle(x); if(c.display === 'none' || c.visibility === 'hidden') return null; op *= +c.opacity; }
    if(op < .05) return null; return r; };
  const nat = i => !!(i && i.tagName === 'INPUT' && i.type === 'checkbox' && i.hasAttribute('switch') && !i.disabled);
  const desc = e => !e ? 'null' : (e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + ([...e.classList].slice(0, 2).map(c => '.' + c).join('')));
  const avoid = o.avoid ? [...document.querySelectorAll(o.avoid)].map(e => e.getBoundingClientRect()).filter(r => r.width) : [];
  const out = [];
  for(const el of root.querySelectorAll(sel)){
    if(el.matches('input, .nova-hlb, .nova-hsw') || el.disabled || el.getAttribute('aria-disabled') === 'true') continue;
    if(o.skip && el.matches(o.skip)) continue;
    const r = vis(el); if(!r) continue;
    if(getComputedStyle(el).pointerEvents === 'none') continue;
    const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    if(avoid.some(a => cx >= a.left && cx <= a.right && cy >= a.top && cy <= a.bottom)) continue;
    /* a control inside another surface of this list (the star on a flash card face) is its own surface */
    const h = document.elementFromPoint(cx, cy);
    let got = 'none:' + desc(h);
    if(nat(h)){
      const host = h.closest('label') && !h.classList.contains('nova-hsw') ? h.closest('label') : h.parentElement;
      got = (el.contains(h) || (host && host.contains(el)) || (h.closest('label') === el)) ? 'switch' : 'other:' + desc(host);
    } else {
      const lb = h && h.closest ? h.closest('label') : null;
      if(lb && nat(lb.control)) got = (el.contains(lb) || lb === el || lb.contains(el)) ? 'label' : 'other-label:' + desc(lb.parentElement);
    }
    out.push({ el: desc(el), w: Math.round(r.width), h: Math.round(r.height), x: Math.round(cx), y: Math.round(cy), got });
  }
  return { list: out };
}"""
W = "const wait=ms=>new Promise(r=>setTimeout(r,ms));"
TABS = "#bottomtabs"
def surfaces(pg, name, root="#stage", sel=None, skip=None, avoid=TABS, minimum=1, extra_roots=()):
    found = []
    for rt in (root,) + tuple(extra_roots):
        r = pg.evaluate(SURF, {"root": rt, "sel": sel, "skip": skip, "avoid": avoid if rt == root else None})
        if r.get("missing"): chk("%s: %s is on the screen" % (name, rt), False, r); return
        found += r["list"]
    bad = [x for x in found if x["got"] not in ("switch", "label")]
    chk("%s: every surface (%d) has its own native switch under a finger at its middle%s" % (name, len(found), "" if not bad else " - %d without" % len(bad)),
        len(found) >= minimum and not bad, bad[:8] if bad else "only %d surfaces found" % len(found))
    return found

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    ctx, pg, cdp, errs = page(br)
    chk("the haptic layer is on (an iPhone, Haptics on)", pg.evaluate("()=>NovaSound.canTaptic() && NovaSound.hswCount() > 5"), pg.evaluate("()=>NovaSound.hswCount()"))

    if not ONLY or "planet" in ONLY:
        # (1) the planet system's switches the moment Home is built
        r = pg.evaluate("""()=>{ showProfile(); showHome();
          const h=document.querySelector('#stage .cosmic-hero-wrap'); if(!h) return null;
          const hosts=[h.querySelector('.cosmic-sphere-hsw'), ...h.querySelectorAll('.cosmic-icon-badge.cosmic-badge-tappable, .cosmic-flare-dot.cosmic-badge-tappable')].filter(Boolean);
          return { n: hosts.length, with: hosts.filter(x=>x.querySelector(':scope > input.nova-hsw[switch]')).length }; }""")
        chk("(1) the planet, every rank bubble and secret flare carry their switch in the same task Home is built (%s)" % r,
            r and r["n"] >= 8 and r["with"] == r["n"], r)
        pg.wait_for_timeout(2200)
        # and a real tap on each flips its switch (the tick) and still answers (the caption)
        res = []
        for sel in (".cosmic-sphere-hsw", ".cosmic-icon-badge.cosmic-badge-tappable", ".cosmic-flare-dot.cosmic-badge-tappable"):
            xy = pg.evaluate("""(s)=>{ const e=[...document.querySelectorAll('#stage '+s)].find(e=>{ const r=e.getBoundingClientRect(); const x=r.left+r.width/2, y=r.top+r.height/2; const h=document.elementFromPoint(x,y); return h && h.parentElement===e; });
              if(!e) return null; const sw=e.querySelector(':scope > .nova-hsw'); window.__p0=sw.checked; window.__pe=e; const r=e.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]; }""", sel)
            if not xy: res.append((sel, "none clear of the others")); continue
            tap(cdp, *xy); pg.wait_for_timeout(500)
            res.append((sel, pg.evaluate("()=>{ const sw=window.__pe.querySelector(':scope > .nova-hsw'); return { flipped: sw.checked!==window.__p0, caption: !!document.querySelector('#stage .home-caption .hc-item.is-in') }; }")))
            pg.wait_for_timeout(700)
        chk("(1) a finger on the planet, a rank bubble and a secret flare flips its switch and still answers", all(isinstance(v, dict) and v["flipped"] and v["caption"] for _, v in res), res)

    if not ONLY or "surfaces" in ONLY:
        pg.evaluate("async()=>{ %s showHome(); await wait(2000); }" % W)
        surfaces(pg, "Home", sel="button, [role='button'], .cosmic-sphere-hsw", skip=".cosmic-flare-dot", minimum=8,
                 extra_roots=(TABS, "#chatdock-btn"))
        # the secret flares ride the rings under the bubbles: each has its switch, and one clear of the bubbles takes a finger
        fl = pg.evaluate("""()=>[...document.querySelectorAll('#stage .cosmic-flare-dot.cosmic-badge-tappable')].map(e=>{ const r=e.getBoundingClientRect(); const h=document.elementFromPoint(r.left+r.width/2, r.top+r.height/2);
            return { own: !!e.querySelector(':scope > input.nova-hsw[switch]'), hit: h && h.classList.contains('nova-hsw') ? (h.parentElement===e ? 'own' : 'planet') : 'none' }; })""")
        chk("Home: every secret flare has its switch and a finger on one lands on a switch of the planet system", fl and all(f["own"] and f["hit"] != "none" for f in fl), fl)
        pg.evaluate("async()=>{ %s showModeSelect(); await wait(1800); }" % W)
        surfaces(pg, "Mode select", minimum=5)
        pg.evaluate("async()=>{ %s cfg.mode='drill'; cfg.source='all'; showSetup(); await wait(2000); }" % W)
        surfaces(pg, "Units", minimum=10)
        pg.evaluate("async()=>{ %s const c=document.querySelector('.pick input'); c.checked=true; c.dispatchEvent(new Event('change',{bubbles:true})); await wait(600); document.getElementById('nextbtn').click(); await wait(2200); }" % W)
        surfaces(pg, "Start sheet", root=".unitoptions-modal-sheet.is-setup", skip=".sheet-begin-bar *", avoid=".sheet-begin-bar", minimum=4)
        surfaces(pg, "Start sheet: Begin", root=".unitoptions-modal-sheet.is-setup .sheet-begin-bar", avoid=None, minimum=1)
        pg.evaluate("async()=>{ %s const b=document.querySelector('.unitoptions-modal-sheet .sheet-begin-btn'); b && b.click(); await wait(6500); }" % W)
        surfaces(pg, "Question", sel=".choice, button, [role='button']", minimum=4, extra_roots=("#pausebtn",))
        pg.evaluate("async()=>{ %s const c=document.querySelector('#stage .choice'); c && c.click(); await wait(1500); const p=document.getElementById('pausebtn'); p && p.click(); await wait(1500); }" % W)
        surfaces(pg, "Pause", root=".pausepanel", avoid=None, minimum=2)
        pg.evaluate("""async()=>{ %s testInProgress=false; theme.reduceMotion=true; cfg.mode='drill'; cfg.source='all'; const units=['Identity Crimes']; cfg.units=units.slice(); cfg.size=0;
          order=QUESTIONS.map((q,i)=>i).filter(i=>units.indexOf((QUESTIONS[i].topic||'').trim())>=0).slice(0,6); runTrackable=true; timedOut=false; runMode='drill'; runLabel=null; isMissedRetake=false; practiceTestMinutes=null; inVirtualRoom=false;
          attempts={}; picked={}; timedOutSet={}; try{ firstPick={}; }catch(e){}
          order.forEach((qi,k)=>{ const oo=optionOrder(qi), right=oo.indexOf(QUESTIONS[qi].answer), miss=k%%2===1; attempts[qi]=miss?2:1; picked[qi]=miss?(right+1)%%oo.length:right; });
          runStartTime=Date.now()-order.length*7000; testInProgress=true; pos=order.length-1; summarize(); await wait(9000); window.scrollTo(0, document.documentElement.scrollHeight); await wait(1500); }""" % W)
        surfaces(pg, "Results", minimum=1)
        pg.evaluate("async()=>{ %s window.scrollTo(0,0); testInProgress=false; theme.reduceMotion=false; showProfile(); await wait(2500); }" % W)
        surfaces(pg, "Profile", minimum=5)
        pg.evaluate("async()=>{ %s window.scrollTo(0, 600); await wait(1500); }" % W)
        surfaces(pg, "Profile, scrolled", minimum=3)
        pg.evaluate("async()=>{ %s window.scrollTo(0,0); showStatsScreen(); await wait(2500); }" % W)
        surfaces(pg, "Stats", minimum=4)
        pg.evaluate("async()=>{ %s window.scrollTo(0, 500); await wait(1500); }" % W)
        surfaces(pg, "Stats, scrolled", minimum=3)
        pg.evaluate("async()=>{ %s window.scrollTo(0,0); showCalendar(); await wait(2500); }" % W)
        surfaces(pg, "Calendar", minimum=2)
        pg.evaluate("async()=>{ %s window.scrollTo(0, 700); await wait(1500); }" % W)
        surfaces(pg, "Calendar, scrolled (the month)", minimum=20)
        pg.evaluate("async()=>{ %s window.scrollTo(0,0); showLeaderboard(); await wait(3500); }" % W)
        surfaces(pg, "Leaderboard", minimum=3)
        pg.evaluate("async()=>{ %s window.scrollTo(0, 500); await wait(1500); }" % W)
        surfaces(pg, "Leaderboard, scrolled", minimum=3)
        pg.evaluate("async()=>{ %s window.scrollTo(0,0); showAppearance(); await wait(2500); }" % W)
        surfaces(pg, "Settings", minimum=8)
        pg.evaluate("async()=>{ %s document.getElementById('settings-row-sound').click(); await wait(2200); }" % W)
        surfaces(pg, "Settings: Sound & Haptics", minimum=3)
        pg.evaluate("async()=>{ %s showCustomize(); await wait(2200); }" % W)
        surfaces(pg, "Customize", minimum=4)
        pg.evaluate("async()=>{ %s document.querySelector('.cz-row-character').click(); await wait(2500); }" % W)
        surfaces(pg, "Customize: a picker", minimum=10)
        pg.evaluate("async()=>{ %s window.scrollTo(0,0); showFriends(); await wait(2200); }" % W)
        surfaces(pg, "Friends", minimum=1)
        pg.evaluate("""async()=>{ %s cfg.mode='review'; cfg.source='all'; showSetup(); await wait(1500); const c=document.querySelector('.pick input'); c.checked=true; c.dispatchEvent(new Event('change',{bubbles:true})); await wait(600);
          document.getElementById('nextbtn').click(); await wait(1600); const sh=document.querySelector('.unitoptions-modal-sheet.is-setup'); const o=[...sh.querySelectorAll('.opt')].find(o=>o.querySelector(':scope > input') && /flash/i.test(o.className + o.textContent));
          const cb=o&&o.querySelector('input'); if(cb && !cb.checked){ cb.click(); await wait(500); } const b=sh.querySelector('.sheet-begin-btn'); b && b.click(); await wait(5000); }""" % W)
        # the face turned away is not there to tap (backface hidden): only the one facing up, and what is on it
        surfaces(pg, "Flash cards", skip=".fc-card:not(.is-flipped) .fc-back, .fc-card:not(.is-flipped) .fc-back *, .fc-card.is-flipped .fc-front, .fc-card.is-flipped .fc-front *", minimum=3)
        pg.evaluate("async()=>{ %s testInProgress=false; showHome(); await wait(1500); openChatDock(); await wait(2500); }" % W)
        surfaces(pg, "Chat dock", root="#chatdock-panel", avoid=None, minimum=3)
        pg.evaluate("async()=>{ %s try{ closeChatDock(); }catch(e){} await wait(800); }" % W)

    if not ONLY or "mode" in ONLY:
        # (2) the mode cards' head switch survives a tap elsewhere on that screen: the click prune took it off (it is "too big")
        #     and the observer put a new one in a beat later - no switch under a finger in between, and churn under one
        pg.evaluate("async()=>{ %s window.scrollTo(0,0); showModeSelect(); await wait(1800); }" % W)
        n0 = pg.evaluate("""()=>{ window.__mcRm=0; const mo=new MutationObserver(rs=>{ for(const m of rs) m.removedNodes.forEach(n=>{ if(n.classList && n.classList.contains('nova-hsw') && m.target.classList.contains('modecard')) window.__mcRm++; }); });
          document.querySelectorAll('#stage .modecard').forEach(c=>mo.observe(c, {childList:true})); window.__mcMo=mo;
          return [...document.querySelectorAll('#stage .modecard')].filter(c=>c.querySelector(':scope > .nova-hsw')).length; }""")
        xy = pg.evaluate("()=>{ const t=document.querySelector('#stage .panel.modeselect h1, #stage .panel.modeselect h2, #stage .panel.modeselect') ; const r=t.getBoundingClientRect(); return [r.left+r.width/2, r.top+12]; }")
        tap(cdp, *xy); pg.wait_for_timeout(1200)
        n1 = pg.evaluate("()=>{ window.__mcMo.disconnect(); return { left: [...document.querySelectorAll('#stage .modecard')].filter(c=>c.querySelector(':scope > .nova-hsw')).length, removed: window.__mcRm }; }")
        chk("(2) a mode card's head switch is never taken off by a tap elsewhere on the screen (%d before, %s after)" % (n0, n1), n0 >= 4 and n1["left"] == n0 and n1["removed"] == 0, [n0, n1])

    if not ONLY or "label" in ONLY:
        # (3) a tap on a control too big for a switch: one click reaches it, its switch flips, no scripted tick on top
        rows = []
        for open_js, sel in (("showStatsScreen()", "#stage .stat-card"), ("showLeaderboard()", "#stage .rank-row.lb-place-1"),
                             ("showAppearance()", "#stage .settings-row"), ("showCalendar()", "#stage .cal-grid .cal-cell:not(:empty):not([disabled])")):
            pg.evaluate("async()=>{ %s window.scrollTo(0,0); %s; await wait(2500); }" % (W, open_js))
            a = pg.evaluate("""(s)=>{ const h=document.querySelector(s); if(!h) return null; h.scrollIntoView({block:'center'}); h.__n=0;
              /* counted as it reaches the control (capture); a Settings row is then kept from opening its page */
              if(!h.__armed){ h.__armed=1; h.addEventListener('click', e=>{ h.__n++; if(h.matches('.settings-row')) e.stopImmediatePropagation(); }, true); }
              const sw=h.querySelector(':scope > label > input[switch], :scope > input[switch]'); window.__s0 = sw ? sw.checked : null; window.__t0 = window.__novaTaptic || 0; window.__lh = h;
              const r=h.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]; }""", sel)
            if not a: rows.append((sel, "missing")); continue
            pg.wait_for_timeout(900)   # the page scrolls smoothly: read where it is once it has stopped
            a = pg.evaluate("()=>{ const r=window.__lh.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]; }")
            tap(cdp, *a); pg.wait_for_timeout(700)
            rows.append((sel, pg.evaluate("""()=>{ const h=window.__lh; const sw=h.querySelector(':scope > label > input[switch], :scope > input[switch]');
              return { clicks: h.__n, flipped: sw ? sw.checked !== window.__s0 : false, scripted: (window.__novaTaptic||0) - window.__t0 }; }""")))
        chk("(3) a finger on a stat card, a leaderboard row, a Settings row and a calendar day: one click each, its own switch flipped, no scripted tick",
            all(isinstance(v, dict) and v["clicks"] == 1 and v["flipped"] and v["scripted"] == 0 for _, v in rows), rows)
        # a Settings row's words (a .opt label round its switch): the switch flips, the tick is not scripted on top
        pg.evaluate("async()=>{ %s window.scrollTo(0,0); showAppearance(); await wait(1500); document.getElementById('settings-row-sound').click(); await wait(2200); }" % W)
        r = pg.evaluate("""()=>{ const o=[...document.querySelectorAll('#stage label.opt')].find(o=>{ const i=o.querySelector(':scope > input'); return i && !i.disabled && o.querySelector('.otext'); });
          if(!o) return null; const t=o.querySelector('.otext'); const r=t.getBoundingClientRect(); window.__o=o; window.__c0=o.querySelector(':scope > input').checked; window.__t0=window.__novaTaptic||0; return [r.left+Math.min(r.width/2, 40), r.top+r.height/2]; }""")
        if r:
            tap(cdp, *r); pg.wait_for_timeout(800)
            v = pg.evaluate("()=>({ flipped: window.__o.querySelector(':scope > input').checked !== window.__c0, scripted: (window.__novaTaptic||0) - window.__t0 })")
            pg.evaluate("()=>{ const i=window.__o.querySelector(':scope > input'); if(i.checked !== window.__c0) i.click(); }"); pg.wait_for_timeout(600)
        else: v = None
        chk("(3) a finger on a switch row's words flips its native switch and runs no scripted tick on top (%s)" % v, v and v["flipped"] and v["scripted"] == 0, v)
        # a drag that starts on a label scrolls the page and clicks nothing
        pg.evaluate("async()=>{ %s showAppearance(); await wait(2000); window.scrollTo(0,0); await wait(300); }" % W)
        a = pg.evaluate("""()=>{ const h=[...document.querySelectorAll('#stage .settings-row')].find(h=>h.querySelector(':scope > .nova-hlb') && h.getBoundingClientRect().top > 300); if(!h) return null; h.__n=0; h.addEventListener('click', ()=>{ h.__n++; }, true); window.__dh=h;
          const r=h.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2, scrollY]; }""")
        if a:
            cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": a[0], "y": a[1]}]})
            for i in range(1, 9):
                time.sleep(0.016); cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": a[0], "y": a[1] - 200 * i / 8}]})
            time.sleep(0.03); cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []}); pg.wait_for_timeout(900)
            v = pg.evaluate("()=>({ clicks: window.__dh.__n, scrolled: scrollY, there: window.__dh.isConnected })")
            chk("(3) a drag that starts on a Settings row's label scrolls the page (%d -> %d) and opens nothing" % (a[2], v["scrolled"]), v["clicks"] == 0 and v["there"] and v["scrolled"] > a[2] + 40, v)
        else:
            chk("(3) a Settings row carries a label to drag from", False)

    if not ONLY or "finger" in ONLY:
        # (4) nothing goes in under a finger that is down: Home drawn, a finger straight down on Start Studying and held
        pg.evaluate("async()=>{ %s window.scrollTo(0,0); showProfile(); await wait(1500); }" % W)
        xy = pg.evaluate("()=>{ showHome(); const b=document.querySelector('#stage #nextbtn'); const r=b.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]; }")
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": xy[0], "y": xy[1]}]})
        held = []; t0 = time.time()
        while time.time() - t0 < 1.0:   # a held finger: the switch would go in ~0.5s after Home is drawn
            time.sleep(0.08); held.append(pg.evaluate("()=>!!document.querySelector('#stage #nextbtn > .nova-hsw, #stage #nextbtn > .nova-hlb')"))
        cdp.send("Input.dispatchTouchEvent", {"type": "touchCancel", "touchPoints": []})
        pg.wait_for_timeout(1500)
        after = pg.evaluate("()=>!!document.querySelector('#stage #nextbtn > .nova-hsw')")
        chk("(4) no switch goes in under a finger held on a control (%s), and it goes in once the finger is up (%s)" % (held, after), not any(held) and after, [held, after])

    if not ONLY or "toggle" in ONLY:
        # (5) Haptics off takes every switch and label away; on puts them back (a guard on the toggle that existed)
        pg.evaluate("async()=>{ %s window.scrollTo(0,0); showAppearance(); await wait(1500); document.getElementById('settings-row-sound').click(); await wait(2200); }" % W)
        def haprow():
            return pg.evaluate("""()=>{ const o=document.querySelector('#stage label.opt.settings-haptics-row, #stage label.opt[class*=haptic]'); if(!o) return null; o.scrollIntoView({block:'center'});
              const b=o.querySelector(':scope > .box') || o; const r=b.getBoundingClientRect(); return { x:r.left+r.width/2, y:r.top+r.height/2, on: o.querySelector(':scope > input').checked }; }""")
        hr = haprow()
        if not hr:
            chk("(5) the Haptics row is in Settings > Sound & Haptics", False)
        else:
            if not hr["on"]: tap(cdp, hr["x"], hr["y"]); pg.wait_for_timeout(1500); hr = haprow()
            tap(cdp, hr["x"], hr["y"]); pg.wait_for_timeout(1500)
            off = pg.evaluate("()=>({ theme: theme.haptics, sw: document.querySelectorAll('.nova-hsw').length, lb: document.querySelectorAll('.nova-hlb').length, opt: document.querySelectorAll('input.hsw-opt, input[switch]').length })")
            hr = haprow(); tap(cdp, hr["x"], hr["y"]); pg.wait_for_timeout(2500)
            on = pg.evaluate("()=>({ theme: theme.haptics, sw: document.querySelectorAll('.nova-hsw').length, opt: document.querySelectorAll('input.hsw-opt').length })")
            chk("(5) Haptics off leaves no switch or label on the page (%s); on puts them back (%s)" % (off, on),
                off["theme"] is False and off["sw"] == 0 and off["lb"] == 0 and off["opt"] == 0 and on["theme"] is not False and on["sw"] > 3 and on["opt"] >= 1, [off, on])
    chk("no page errors (%d)" % len(errs), not errs, errs[:4])
    ctx.close()

    if not ONLY or "tab" in ONLY:
        # a Safari tab (not installed): the same layer
        ctx, pg, cdp, errs = page(br, installed=False)
        surfaces(pg, "Safari tab: Home", sel="button, [role='button'], .cosmic-sphere-hsw", skip=".cosmic-flare-dot", minimum=8, extra_roots=(TABS,))
        pg.evaluate("async()=>{ %s showAppearance(); await wait(2500); }" % W)
        surfaces(pg, "Safari tab: Settings", minimum=8)
        pg.evaluate("async()=>{ %s showCalendar(); await wait(2500); window.scrollTo(0, 700); await wait(1500); }" % W)
        surfaces(pg, "Safari tab: Calendar's month", minimum=20)
        chk("Safari tab: no page errors", not errs, errs[:4])
        ctx.close()
    br.close()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
