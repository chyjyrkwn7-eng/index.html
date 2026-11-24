#!/usr/bin/env python3
"""Build 384 ui3: with the class list open, the background art is gone and the foreground steps back.
Madison: "When changing classes, you shouldn't be able to see the background stars and stuff like that through the other stuff,
the stuff over that normally should still be there but it should still be darker and stuff of course."
check-b384-classdim holds the list's dim itself (Home at <= .3, no tap, no broad :has()). This holds what is behind it, read as
EFFECTIVE opacity (the element's own times every ancestor's; the stars are body::after, times body's), with the list open, on
an installed iPhone 17 Pro Max, the same in a Safari tab, an installed iPad Pro 11" and the same in a browser, both classes:
  (1) the cosmic hero (planet, rings, orbiting planets, its glow) and the star field are at most .03 - gone;
  (2) the foreground is still there but darker: greeting, title, Start Studying, the help button, the tab bar and the chat
      button each between .1 and .5 (none lost, none at full);
  (3) the class list itself (every glass button and its label) is at full;
  (4) the art goes with the list: the hero's and the stars' opacity transition takes the dimmed screen's duration, and the
      rules that do it set only opacity / transition / pointer-events (no filter, no backdrop-filter);
  (5) shut (a tap outside), the hero, the stars, the tab bar and the chat button are back at full;
  (6) no page errors.
  python3 tools/check-b384-classdim2.py [--against REV|DIR]   (--against fa11d79 must FAIL (1) and (2))"""
import importlib.util, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("glitches", os.path.join(HERE, "check-b384-glitches.py"))
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)   # takes --against from sys.argv
from playwright.sync_api import sync_playwright
chk = G.chk
G.DEV["ipad-tab"] = (834, 1100, 834, 1194, (0, 0, 0, 0), G.UA_IPAD, True, False)
QUIET = "()=>{ try{ homeUnlocksOwed=()=>false; }catch(e){} showHome(); }"
READ = r"""()=>{ const eff = e => { if(!e) return null; let o = 1; for(let n = e; n && n.nodeType === 1; n = n.parentElement) o *= +getComputedStyle(n).opacity; return +o.toFixed(3); };
  const q = s => document.querySelector(s);
  const hero = q('#stage .cosmic-hero-wrap');
  const fg = { greeting: eff(q('#stage .homegreeting')), title: eff(q('#stage .hometitle-wrap')), start: eff(q('#stage .playbtn')),
               help: eff(q('#stage .daily-question-fab')), tabs: eff(q('#bottomtabs')), chat: eff(q('#chatdock-btn')) };
  const list = [...document.querySelectorAll('.class-bubble-wrap .class-stack-item')].flatMap(b => [eff(b.querySelector('.csi-bubble')), eff(b.querySelector('.csi-label'))]);
  const dur = s => s ? parseFloat(s.transitionDuration) : null;
  const dimmed = [...document.querySelectorAll('#stage > *')].find(e => !e.classList.contains('class-bubble-wrap') && e.offsetHeight > 0);
  return { open: !!q('.class-bubble-wrap.is-open'), hero: eff(hero), stars: +(+getComputedStyle(document.body, '::after').opacity * eff(document.body)).toFixed(3),
           fg, list, heroDur: hero ? dur(getComputedStyle(hero)) : null, starsDur: dur(getComputedStyle(document.body, '::after')),
           heroProp: hero ? getComputedStyle(hero).transitionProperty : null, dimDur: dimmed ? dur(getComputedStyle(dimmed)) : null }; }"""
RULES = r"""()=>{ const bad = []; let n = 0; const walk = rs => { for(const r of rs){ if(r.cssRules) walk(r.cssRules);
    if(!r.selectorText || !/class-list-(open|dim)/.test(r.selectorText)) continue; n++;
    for(let i = 0; i < r.style.length; i++){ const p = r.style[i]; if(!/^(opacity|transition|pointer-events)/.test(p)) bad.push(r.selectorText.slice(0, 90) + ' { ' + p + ' }'); } } };
  for(const sh of document.styleSheets){ try{ walk(sh.cssRules); }catch(e){} } return { n, bad }; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G.CHROME)
    for dev in ("promax", "promax-tab", "ipad", "ipad-tab"):
        for cls in ("academy", "ifc"):
            tag = "%s, %s" % (dev, cls)
            pg = G.open_dev(br, dev, inits=[G.seed_init(cls)])
            errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
            pg.evaluate(QUIET); pg.wait_for_timeout(1800); G.clear_popups(pg)
            if not pg.query_selector(".class-bubble"):
                chk("%s: the class button is on Home" % tag, False); pg.context.close(); continue
            pg.evaluate("()=>document.querySelector('.class-bubble').click()"); pg.wait_for_timeout(900)
            r = pg.evaluate(READ)
            chk("(1) %s: open, the hero (%s) and the stars (%s) are gone" % (tag, r["hero"], r["stars"]),
                r["open"] and r["hero"] is not None and r["hero"] <= .03 and r["stars"] <= .03, r)
            fg = r["fg"]
            chk("(2) %s: the foreground is there but darker %s" % (tag, fg), all(v is not None and .1 <= v <= .5 for v in fg.values()), fg)
            chk("(3) %s: the list's glass buttons and labels at full (%d)" % (tag, len(r["list"])), len(r["list"]) >= 4 and all(v == 1 for v in r["list"]), r["list"])
            chk("(4) %s: the art fades with the list (hero %ss, stars %ss, screen %ss; %s)" % (tag, r["heroDur"], r["starsDur"], r["dimDur"], r["heroProp"]),
                r["dimDur"] and r["heroDur"] == r["dimDur"] and r["starsDur"] == r["dimDur"] and "opacity" in (r["heroProp"] or ""), r)
            if dev == "promax" and cls == "academy":
                ru = pg.evaluate(RULES)
                chk("(4) the open-list rules set only opacity / transition / pointer-events (%d rules)" % ru["n"], ru["n"] >= 2 and not ru["bad"], ru)
            w = pg.viewport_size["width"]
            pg.mouse.click(w * .75, 140) if not G.DEV[dev][6] else pg.touchscreen.tap(w * .75, 140)
            pg.wait_for_timeout(1200)
            r2 = pg.evaluate(READ)
            chk("(5) %s: shut, everything is back (hero %s, stars %s, tabs %s, chat %s)" % (tag, r2["hero"], r2["stars"], r2["fg"]["tabs"], r2["fg"]["chat"]),
                not r2["open"] and r2["hero"] == 1 and r2["stars"] == 1 and r2["fg"]["tabs"] == 1 and r2["fg"]["chat"] == 1, r2)
            chk("(6) %s: no page errors" % tag, not errs, errs[:3])
            pg.context.close()
    br.close()
print("\nALL PASS" if not G.fails else "\nFAILURES (%d)" % len(G.fails))
sys.exit(0 if not G.fails else 1)
