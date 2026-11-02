"""Build 382: the start sheet's switches - the words at the bottom, and the glass knob.
Madison: "When toggling stuff, the words coming up at the bottom come in a little laggy as well. Fix this too." and "the Liquid
Glass gets picked and put down just a smidge too slow ... a smidge faster".
As an iPhone (its user agent, real touches through CDP), Drill's start sheet, the Shuffle switch tapped off and on again, on a
Pro Max-width phone whose sheet is capped (it scrolls) and one tall enough that the sheet sizes to what is on it (it grows up):
(1) the line of switched-on words in the box above Begin opens and shuts with transforms and opacity only - nothing that lays
    the page out (grid rows, margins, heights) is animated, and the box's laid-out height changes once, at the tap, not frame
    by frame;
(2) it starts from where things were - the first frame after the tap draws the box's top (and the sheet's top) where they were
    before the tap, not already at the end - and is home, words fully shown or gone, within 400ms of the tap;
(3) when it has played out nothing of it is left behind (no stand-in, no ghost words, the box's own look is back, no transform);
(4) the knob's swell (picked up) and settle (put down), read off the lens's own animations, are each a smidge shorter than
    build 381's 260ms / 360ms - between 65% and 85% of them - on the same curves.
Run:  python3 tools/check-b382-toggles.py   (--against: copy the old index.html over first)"""
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
d = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]())); d["publicId"] = "pubtest0382t"; d["firstName"] = "Casey"; d["novaMet"] = 99
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1"
OLD_POP, OLD_SHRINK = 260, 360   # build 381's swell and settle (NSW_T), the "before" this is measured against
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else info)
def tap(cdp, x, y):
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]}); time.sleep(0.08)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
OPEN = """async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms));
  theme.reduceMotion=false; try{ applyTheme(); }catch(e){}
  cfg.mode='drill'; cfg.source='all'; cfg.timer='off'; showSetup(); await wait(700);
  const c=document.querySelector('.pick input'); c.checked=true; c.dispatchEvent(new Event('change',{bubbles:true})); await wait(300);
  document.getElementById('nextbtn').click(); await wait(1500);
  /* only Shuffle can put words on the line: everything else that would is off */
  const sh=document.querySelector('.unitoptions-modal-sheet.is-setup'); if(!sh) return null;
  for(const o of sh.querySelectorAll('.opt')){ const cb=o.querySelector(':scope > input[type=checkbox]'); if(!cb || /Shuffle/.test(o.textContent)) continue;
    if(cb.checked){ cb.click(); await wait(500); } }
  const r=sh.getBoundingClientRect(); return { capped: sh.scrollHeight > sh.clientHeight + 1, top: Math.round(r.top), h: Math.round(r.height) }; }"""
CENTRE = """(name)=>{ const o=[...document.querySelectorAll('.unitoptions-modal-sheet .opt')].find(o=>o.textContent.includes(name)); if(!o) return null;
  const b=o.querySelector(':scope > .box'); b.scrollIntoView({block:'nearest'}); const r=b.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]; }"""
STATE = """()=>{ const sh=document.querySelector('.unitoptions-modal-sheet.is-setup'); const cb=[...sh.querySelectorAll('.opt')].find(o=>/Shuffle/.test(o.textContent)).querySelector('input');
  return { on: cb.checked, empty: !!sh.querySelector('.sheet-summary-optswrap.is-empty') }; }"""
# frame recorder: the box's drawn top (its stand-in's while there is one), the sheet's drawn top, the box's LAID-OUT height
# (offsetHeight ignores transforms), the words' drawn opacity, and every animation started in the sheet outside the switches
REC = """()=>{ const sh=document.querySelector('.unitoptions-modal-sheet.is-setup'), card=sh.querySelector('.start-summary'), w=sh.querySelector('.sheet-summary-opts');
  const R={ fr:[], anims:new Map(), change:null, T0:performance.now() }; window.__rec=R; R.on=true;
  const opOf=e=>{ let o=1; for(let x=e; x && x!==sh; x=x.parentElement) o*=+getComputedStyle(x).opacity; return o; };
  if(!window.__recHook){ window.__recHook=1; document.addEventListener('change', e=>{ const r=window.__rec; if(r && r.change==null && e.target.closest && e.target.closest('.unitoptions-modal-sheet')) r.change=performance.now()-r.T0; }, true);
    /* at the end of the tap's own task (window, bubbling: after the row's handlers): what is already set going, and for how long */
    window.addEventListener('change', e=>{ const r=window.__rec; if(!r || r.inTask || !e.target.closest || !e.target.closest('.unitoptions-modal-sheet')) return;
      const s=document.querySelector('.unitoptions-modal-sheet.is-setup');
      r.inTask=document.getAnimations().filter(a=>{ const el=a.effect && a.effect.target; return el && el.closest && s.contains(el) && !el.closest('.box, .nsw, .nsw-lens'); })
        .map(a=>{ const t=a.effect.getComputedTiming(); return { el:String(a.effect.target.className).slice(0,40), end: (t.delay||0) + (t.activeDuration||0),
          props: a.transitionProperty ? [a.transitionProperty] : [...new Set((a.effect.getKeyframes()||[]).flatMap(k=>Object.keys(k)).filter(p=>!['offset','easing','composite','computedOffset'].includes(p)))] }; }); }); }
  const f=()=>{ const t=performance.now()-R.T0;
    const bg=card.querySelector('.sheet-summary-foldbg'); const top=(bg||card).getBoundingClientRect().top;
    const gh=card.querySelector('.sheet-summary-foldghost');
    R.fr.push({ t, top, stop: sh.getBoundingClientRect().top, lh: card.offsetHeight, wop: opOf(w) * (w.closest('.is-empty') ? 0 : 1), gop: gh ? +getComputedStyle(gh).opacity : null });
    document.getAnimations().forEach(a=>{ const el=a.effect && a.effect.target; if(!el || !el.closest || !sh.contains(el) || el.closest('.box, .nsw, .nsw-lens')) return;
      if(R.anims.has(a)) return; const props=new Set();
      if(a.transitionProperty) props.add(a.transitionProperty);
      try{ (a.effect.getKeyframes()||[]).forEach(k=>Object.keys(k).forEach(p=>{ if(!['offset','easing','composite','computedOffset'].includes(p)) props.add(p); })); }catch(e){}
      R.anims.set(a, { at: Math.round(t), el: String(el.className).slice(0,40), props:[...props] }); });
    if(R.on) requestAnimationFrame(f); };
  /* the state before the tap, read now (a loaded machine may draw no frame between here and the tap) */
  R.on=false; f(); R.on=true; R.fr[0].t=-1; requestAnimationFrame(f); }"""
READ = """()=>{ const R=window.__rec; R.on=false; return { fr:R.fr, change:R.change, anims:[...R.anims.values()], inTask:R.inTask||[] }; }"""
LEFT = """()=>{ const sh=document.querySelector('.unitoptions-modal-sheet.is-setup'), card=sh.querySelector('.start-summary'), cs=getComputedStyle(card);
  return { stand: card.querySelectorAll('.sheet-summary-foldbg, .sheet-summary-foldghost').length, folding: card.classList.contains('is-folding'),
           bg: cs.backgroundColor, border: cs.borderTopColor, shadow: cs.boxShadow,
           moved: [sh, card, ...card.children, ...sh.querySelectorAll('.sheet-begin-bar > *')].filter(e=>getComputedStyle(e).transform!=='none').map(e=>String(e.className).slice(0,30)) }; }"""
LAYOUT = {"grid-template-rows", "gridTemplateRows", "margin-top", "marginTop", "height", "max-height", "maxHeight", "padding-top", "paddingTop", "top", "bottom", "margin-bottom", "marginBottom", "all"}
def page(br, w, h):
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=2, has_touch=True, is_mobile=True, user_agent=UA)
    ctx.add_init_script(g["STANDALONE"]); ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]()))
    pg = ctx.new_page(); body = g["patched"]((62, 0, 34, 0))
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.add_init_script(INIT % json.dumps(json.dumps(d)))
    pg.goto(url); pg.wait_for_timeout(3000); pg.evaluate("document.getElementById('splashscreen')?.remove()")
    pg.evaluate("()=>{ homeUnlocksOwed=()=>false; showHome(); }"); pg.wait_for_timeout(2500)
    return ctx, pg, ctx.new_cdp_session(pg)
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    for label, (w, h) in (("phone, sheet capped", (440, 956)), ("tall phone, sheet sized to its rows", (440, 1400))):
        ctx, pg, cdp = page(br, w, h)
        info = pg.evaluate(OPEN)
        if not info:
            chk("%s: the start sheet opens" % label, False); ctx.close(); continue
        pg.wait_for_timeout(8000)   # idle warmers (badges, sounds) done, so the frames below are the toggle's
        c0 = pg.evaluate("()=>{ const c=document.querySelector('.unitoptions-modal-sheet.is-setup .start-summary'), cs=getComputedStyle(c); return { bg: cs.backgroundColor, border: cs.borderTopColor, shadow: cs.boxShadow }; }")
        for want in ("off", "on", "off", "on"):
            st0 = pg.evaluate(STATE)
            if (want == "on") == st0["on"]: continue
            xy = pg.evaluate(CENTRE, "Shuffle"); pg.wait_for_timeout(300)
            xy = pg.evaluate(CENTRE, "Shuffle")
            pg.evaluate(REC); time.sleep(0.05)
            tap(cdp, *xy); time.sleep(0.9)
            r = pg.evaluate(READ); st = pg.evaluate(STATE); pg.wait_for_timeout(200); left = pg.evaluate(LEFT)
            name = "%s, Shuffle %s (line %s)" % (label, want, "shuts" if st["empty"] else "opens")
            fr, ch = r["fr"], r["change"]
            if ch is None or st["on"] != (want == "on"):
                chk("%s: the tap flips the switch" % name, False, [st, ch]); continue
            before = [f for f in fr if f["t"] <= ch]; after = [f for f in fr if f["t"] > ch]
            if os.environ.get("DEBUG"):
                print("   change at %.0f; frames:" % ch, " ".join("%.0f:%.1f/%.2f" % (f["t"], f["top"], f["wop"] if f["gop"] is None else f["gop"]) for f in fr))
            b = before[-1] if before else fr[0]; end = after[-1]
            dtop = end["top"] - b["top"]; dsheet = end["stop"] - b["stop"]
            props = sorted({p for a in r["anims"] if a["at"] >= (ch - 20) for p in a["props"]})
            layouty = [p for p in props if p in LAYOUT]
            lhs = []
            for f in after:
                if not lhs or lhs[-1] != f["lh"]: lhs.append(f["lh"])
            chk("%s: transforms and opacity only (animated: %s); the box's laid-out height changes once (%s)" % (name, ", ".join(props) or "nothing", lhs),
                not layouty and len(lhs) <= 1 and abs(dtop) > 4, [props, lhs, dtop])
            first = after[0] if after else None
            # first frame drawn after the change: still near the old place (a glide), not at the end (a jump)
            near = first is not None and abs(first["top"] - b["top"]) <= max(1.5, .45 * abs(dtop)) and (abs(dsheet) < 1 or abs(first["stop"] - b["stop"]) <= max(1.5, .45 * abs(dsheet)))
            done = next((f["t"] - ch for f in after if abs(f["top"] - end["top"]) < .6 and abs(f["stop"] - end["stop"]) < .6
                         and (f["wop"] > .99 if not st["empty"] else (f["gop"] in (None, 0) or f["gop"] < .01))), None)
            # the words' own entrance (or the leaving words' fade) is set going in the tap's own task; the whole glide's
            # length is read off its animations (the sandbox's frames are too uneven under load to time it by the clock)
            it = r["inTask"]; words = [a for a in it if "sheet-summary-opts" in a["el"] and "opacity" in a["props"]]
            longest = max([a["end"] for a in it] or [0])
            chk("%s: it starts from where it was (first frame %+.1fpx of %+.1fpx; sheet %+.1f of %+.1f), the words' fade is set going in the tap's own task (%s) and all of it plays in %sms (wall clock here: %sms)" % (
                name, (first["top"] - b["top"]) if first else 0, dtop, (first["stop"] - b["stop"]) if first else 0, dsheet, len(words), round(longest), done and round(done)),
                near and words and 0 < longest <= 300 and done is not None and abs(end["top"] - after[-1]["top"]) < .6 and (end["wop"] > .99) != st["empty"], [first, b, end, it])
            chk("%s: nothing is left behind (%s)" % (name, left),
                left["stand"] == 0 and not left["folding"] and not left["moved"] and left["bg"] == c0["bg"] and left["border"] == c0["border"] and left["shadow"] == c0["shadow"], [left, c0])
            pg.wait_for_timeout(500)
        ctx.close()
    # (4) the knob's swell and settle
    ctx, pg, cdp = page(br, 440, 956)
    pg.evaluate("()=>{ theme.reduceMotion=false; try{ applyTheme(); }catch(e){} showAppearance({ page: 'study' }); }"); pg.wait_for_timeout(2500)
    K = pg.evaluate("""async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms));
      const box=[...document.querySelectorAll('#stage .opt > .box')].find(b=>!/Reduce motion/i.test(b.closest('.opt').textContent)); if(!box) return null;
      box.scrollIntoView({block:'center'}); await wait(400);
      const r=box.getBoundingClientRect(), x=r.left+r.width/2, y=r.top+r.height/2;
      const mk=t=>new PointerEvent(t,{bubbles:true,cancelable:true,pointerType:'touch',pointerId:58,isPrimary:true,clientX:x,clientY:y});
      const of=()=>{ const body=box.querySelector('.nsw-lens-body'); return body ? body.getAnimations().map(a=>({ dur:a.effect.getTiming().duration, delay:a.effect.getTiming().delay, ease:a.effect.getTiming().easing, to:(a.effect.getKeyframes().slice(-1)[0]||{}).transform })) : []; };
      const T0=performance.now(); box.dispatchEvent(mk('pointerdown')); await wait(20); const up=of();
      await wait(400); box.dispatchEvent(mk('pointerup')); box.parentNode.querySelector(':scope > input').click(); await wait(20); const down=of();
      let gone=null; for(let i=0;i<120;i++){ if(!box.querySelector('.nsw-lens')){ gone=performance.now()-T0-420; break; } await wait(10); }
      box.parentNode.querySelector(':scope > input').click(); await wait(900);
      return { up, down, gone: gone && Math.round(gone) }; }""")
    pop = K and K["up"] and K["up"][-1]["dur"]
    sh = K and K["down"] and K["down"][-1]["dur"]
    chk("the knob is picked up in %sms (was %s) and put down in %sms (was %s): a smidge faster, %s / %s of before, lens gone %sms after the release" % (
        pop, OLD_POP, sh, OLD_SHRINK, pop and round(pop / OLD_POP, 2), sh and round(sh / OLD_SHRINK, 2), K and K["gone"]),
        pop and sh and .65 <= pop / OLD_POP <= .85 and .65 <= sh / OLD_SHRINK <= .85 and K["up"][-1]["ease"] == "cubic-bezier(0.3, 1.25, 0.5, 1)" and K["down"][-1]["ease"] == "cubic-bezier(0.3, 1.04, 0.4, 1)", K)
    ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
