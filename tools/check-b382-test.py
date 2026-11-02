"""Build 382, the test screen, the code card, its viewer and the results (an iPhone's user agent and real touch events: every
control carries a native haptic switch, as on his phone).
(1) the chat button beside Pause keeps its box when the code card is opened (its pictures arrive while the finger scrolls) and the
    page is scrolled - including while a box read in that moment comes back moved, as an iPhone's does against its visual viewport
    in a rubber-band or a momentum scroll (simulated: getBoundingClientRect answers 29px up while the card fills in);
(2) the results: taps where Main menu WILL be, from the moment the results are up until the buttons show, never press it; a
    touch that starts while they rise and lifts once they are up does not press it either (after such taps, and untouched); a
    fresh tap once they have settled does (home);
(3) Next question never covers the code card: a long answer with its card open, at every scroll, on 440x956, 518x1125, 375x667 and
    an iPad 834x1194 - and is 2.85-3.65rem under the content, short question or long, card open or shut;
(4) the code card has no "Show as text"; its two ways on are Enlarge and Show the whole page, each a 44px tap target, laid out with
    no overflow (side by side filling the row, or stacked full width), at each size;
(5) Enlarge opens the excerpt fitted to the view's width and on its middle (not stuck to the top), and its hint does not stay as a
    bar under it (faded by 3.5s, taking no room); + still zooms and Done still closes.
Run:  PDFJS_DIR=<unpacked pdfjs-dist 5.4.149 package> python3 tools/check-b382-test.py
      (npm's registry tarball: registry.npmjs.org/pdfjs-dist/-/pdfjs-dist-5.4.149.tgz; --against: copy the old index.html over first)"""
import json, os, sys, time, mimetypes
HERE = os.path.dirname(os.path.abspath(__file__))
PDFJS = os.environ.get("PDFJS_DIR", "") + "/"
if not os.path.exists(PDFJS + "build/pdf.min.mjs"):
    print("SKIP: set PDFJS_DIR to an unpacked pdfjs-dist@5.4.149 package (the code card draws the county booklet with it)"); sys.exit(2)
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
from playwright.sync_api import sync_playwright
srv, url = g["serve"]()
OWNER = "xph5b57jbp5a"   # the Fire Code class is the owner's (window.NOVA_CLASS_OWNER)
INIT = """(()=>{ if(localStorage.getItem('class26e.drill.v1')) return;
 localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.ifc.drill.v1', localStorage.getItem('class26e.drill.v1'));
 localStorage.setItem('class26e.synccode','TEST-0382'); localStorage.setItem('class26e.ifc.synccode','TEST-0382');
 ['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card','class26e.getstarted',
  'class26e.ifc.intro.seen','class26e.ifc.unithold.tip','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.getstarted'].forEach(k=>localStorage.setItem(k,'1'));
 localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done'); localStorage.setItem('class26e.activeclass','ifc');
 localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.penal256578.seen','1'); })()"""
d = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]())); d["publicId"] = OWNER; d["firstName"] = "Casey"; d["novaMet"] = 99
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1"
UA_IPAD = "Mozilla/5.0 (iPad; CPU OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1"
SIZES = [("Pro Max 440x956", 440, 956, (62, 0, 34, 0), UA), ("Pro Max at 85% 518x1125", 518, 1125, (73, 0, 40, 0), UA),
         ("SE 375x667", 375, 667, (20, 0, 0, 0), UA), ("iPad 834x1194", 834, 1194, (24, 0, 20, 0), UA_IPAD)]
ok = True
ONLY = os.environ.get("ONLY", "")   # e.g. ONLY=results (chat, layout, results)
want = lambda k: not ONLY or k in ONLY.split(",")
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else info, flush=True)
def route_pdf(ctx):
    def h(r, req):
        rel = req.url.split("pdfjs-dist@5.4.149/", 1)[1].split("?")[0]; p = PDFJS + rel
        if not os.path.exists(p): return r.fulfill(status=404, body="")
        r.fulfill(status=200, body=open(p, "rb").read(), content_type=mimetypes.guess_type(p)[0] or "text/javascript", headers={"access-control-allow-origin": "*"})
    ctx.route("**/pdfjs-dist@5.4.149/**", h)
def touch(cdp, kind, x=0, y=0):
    cdp.send("Input.dispatchTouchEvent", {"type": kind, "touchPoints": [] if kind == "touchEnd" else [{"x": x, "y": y}]})
def tap(cdp, x, y, hold=0.08):
    touch(cdp, "touchStart", x, y); time.sleep(hold); touch(cdp, "touchEnd")
def page(br, w, h, ins, ua=UA):
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=2, has_touch=True, is_mobile=True, user_agent=ua)
    ctx.add_init_script(g["STANDALONE"])
    ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]()))
    route_pdf(ctx)
    pg = ctx.new_page(); body = g["patched"](ins)
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.add_init_script(INIT % json.dumps(json.dumps(d)))
    pg.goto(url); pg.wait_for_timeout(3500)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); try{ homeUnlocksOwed=()=>false; }catch(e){} store.novaMet=99; document.querySelectorAll('#tour-overlay, #tour-tooltip, #nova-intro, .rs-spot, .unlock-card').forEach(n=>n.remove()); }")
    return ctx, pg, ctx.new_cdp_session(pg)
CENTRE = "(sel)=>{ const b=document.querySelector(sel); if(!b) return null; b.scrollIntoView({block:'center',behavior:'instant'}); const r=b.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]; }"
AMEND = "QUESTIONS.map((q,i)=>i).filter(i => QUESTIONS[i].ifc && QUESTIONS[i].ifc.citation.source==='amendment' && !QUESTIONS[i].ifc.citation.blur)"
def start(pg, which, n=4):
    """a drill of county questions: 'long' = the longest answers first, 'short' = the shortest"""
    pg.evaluate("""([lf, n])=>{ let ids = %s;
      const L = i => (QUESTIONS[i].ifc.explanation||'').length + String(QUESTIONS[i].q||'').length + QUESTIONS[i].choices.join('').length;
      ids.sort((a,b)=> lf ? L(b)-L(a) : L(a)-L(b)); ids = ids.slice(0, n);
      cfg.source='all'; cfg.mode='drill'; cfg.units=[QUESTIONS[ids[0]].topic]; beginRun(ids); }""" % AMEND, [which == "long", n])
    pg.wait_for_selector(".qpanel .choice", timeout=25000); pg.wait_for_timeout(1200)
def answer_right(pg, cdp):
    c = pg.evaluate("()=>{ const r=correctSlot(order[pos]); const el=document.querySelector('.choice[data-index=\"'+r+'\"]'); el.scrollIntoView({block:'center',behavior:'instant'}); const b=el.getBoundingClientRect(); return [b.left+b.width/2, b.top+b.height/2]; }")
    tap(cdp, *c); pg.wait_for_timeout(1900)   # the pill rises .78s + .62s after the answer
def open_code(pg, cdp, before_wait=None):
    tap(cdp, *pg.evaluate(CENTRE, ".ifc-code-sum"))
    if before_wait: before_wait()
    for _ in range(100):
        if pg.evaluate("()=>!!document.querySelector('.ifc-code[open] .ifc-links') && !!document.querySelector('.ifc-code[open] .ifc-clips canvas')"): break
        pg.wait_for_timeout(150)
    pg.wait_for_timeout(700)
CHAT = "()=>{ const r=document.getElementById('chatdock-btn').getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; }"

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])

    # ---- (1) the chat button
    for label, w, h, ins, ua in (SIZES[:2] if want("chat") else []):
        ctx, pg, cdp = page(br, w, h, ins, ua)
        start(pg, "long")
        boxes = [("question", pg.evaluate(CHAT))]
        answer_right(pg, cdp); boxes.append(("answered", pg.evaluate(CHAT)))
        # the card fills in while a box read in that moment comes back 29px up (an iPhone mid-bounce)
        def skew():
            pg.evaluate("""()=>{ const o=Element.prototype.getBoundingClientRect; window.__gbcr=o;
              Element.prototype.getBoundingClientRect=function(){ const r=o.call(this); return new DOMRect(r.x, r.y-29, r.width, r.height); }; }""")
        open_code(pg, cdp, skew)
        pg.evaluate("()=>{ const s=document.getElementById('stage'); const c=document.createComment('x'); s.appendChild(c); setTimeout(()=>c.remove(), 30); }")
        pg.wait_for_timeout(300)
        pg.evaluate("()=>{ Element.prototype.getBoundingClientRect=window.__gbcr; }")
        boxes.append(("card open", pg.evaluate(CHAT)))
        for y in (60, 250, 99999, 0):
            pg.evaluate("(y)=>scrollTo({top:y, behavior:'instant'})", y); pg.wait_for_timeout(250); boxes.append(("scroll %d" % y, pg.evaluate(CHAT)))
        tap(cdp, *pg.evaluate(CENTRE, ".ifc-code-sum")); pg.wait_for_timeout(500); boxes.append(("card shut", pg.evaluate(CHAT)))
        chk("%s: the chat button keeps one box through the code card opening (a moved box read mid-bounce), scrolling and shutting (%s)" % (label, boxes),
            len(set(tuple(b) for _, b in boxes)) == 1, boxes)
        ctx.close()

    # ---- (3)/(4)/(5) Next question, the links and the viewer, at each size
    for label, w, h, ins, ua in (SIZES if want("layout") else []):
        ctx, pg, cdp = page(br, w, h, ins, ua)
        rem = pg.evaluate("()=>parseFloat(getComputedStyle(document.documentElement).fontSize)||16")
        GAP = """()=>{ const b=document.getElementById('nextbtn'), p=document.querySelector('.qpanel'); if(!b||b.hidden) return null;
          const keys=document.getElementById('hint'); let low=0;
          [...p.children, ...(keys && getComputedStyle(b).position==='fixed' ? [keys] : [])].forEach(k=>{ if(!k.offsetHeight) return; const ps=getComputedStyle(k).position; if(ps==='fixed'||ps==='absolute') return; low=Math.max(low, k.getBoundingClientRect().bottom); });
          const r=b.getBoundingClientRect(); return { gap:(r.top-low), top:r.top, low }; }"""
        for which in ("short", "long"):
            start(pg, which)
            answer_right(pg, cdp)
            pg.evaluate("()=>scrollTo({top:0, behavior:'instant'})"); pg.wait_for_timeout(300)
            shut = pg.evaluate(GAP)
            open_code(pg, cdp); pg.wait_for_timeout(500)
            pg.evaluate("()=>scrollTo({top:0, behavior:'instant'})"); pg.wait_for_timeout(300)
            opened = pg.evaluate(GAP)
            # every scroll position, the card open: the pill never on the card
            hits = pg.evaluate("""async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const b=document.getElementById('nextbtn'), c=document.querySelector('.qpanel .ifc-ref');
              const max=document.documentElement.scrollHeight-innerHeight; const out=[]; const n=Math.max(1, Math.ceil(max/40));
              for(let k=0;k<=n;k++){ scrollTo({top:Math.round(max*k/n), behavior:'instant'}); await wait(40);
                const r=b.getBoundingClientRect(), q=c.getBoundingClientRect(); const seen=parseFloat(getComputedStyle(b).opacity)>0.05;
                if(seen && r.top < q.bottom-1 && r.bottom > q.top+1 && r.left < q.right && r.right > q.left) out.push(Math.round(scrollY)); }
              scrollTo({top:0, behavior:'instant'}); return { hits: out, max }; }""")
            g1 = shut and shut["gap"] / rem; g2 = opened and opened["gap"] / rem
            chk("%s, %s answer: Next question is 2.85-3.65rem under the content, card shut %.2frem and open %.2frem" % (label, which, g1 or -1, g2 or -1),
                shut and opened and 2.85 <= g1 <= 3.65 and 2.85 <= g2 <= 3.65, [shut, opened])
            chk("%s, %s answer, card open: Next question is never over the card at any scroll (over it at %s of 0-%d)" % (label, which, hits["hits"][:8], hits["max"]),
                not hits["hits"], hits)
            if which == "long":
                pg.evaluate("()=>{ document.querySelector('.ifc-links').scrollIntoView({block:'center',behavior:'instant'}); }"); pg.wait_for_timeout(300)
                L = pg.evaluate("""()=>{ const box=document.querySelector('.ifc-code[open] .ifc-links'), card=document.querySelector('.qpanel .ifc-ref').getBoundingClientRect();
                  const a=[...box.querySelectorAll('.ifc-link')].filter(x=>!x.hidden && x.offsetWidth); const lb=box.getBoundingClientRect();
                  return { all:[...document.querySelectorAll('.ifc-code .ifc-link, .ifc-code button')].filter(x=>!x.hidden).map(x=>x.textContent.trim()),
                    links:a.map(x=>{ const r=x.getBoundingClientRect(); const t=x.querySelector('span')||x; return { t:x.textContent.trim(), w:Math.round(r.width), h:Math.round(r.height), l:Math.round(r.left), r:Math.round(r.right), top:Math.round(r.top),
                      clipped: t.scrollWidth > t.clientWidth + 1 }; }),
                    box:{ l:Math.round(lb.left), r:Math.round(lb.right), sw:box.scrollWidth, cw:box.clientWidth }, card:{ l:Math.round(card.left), r:Math.round(card.right) } }; }""")
                lk = L["links"]
                one_row = len(lk) == 2 and abs(lk[0]["top"] - lk[1]["top"]) <= 2
                stacked = len(lk) == 2 and not one_row and all(abs(x["w"] - (L["box"]["r"] - L["box"]["l"])) <= 2 for x in lk)
                chk("%s: the code card's ways on are Enlarge and Show the whole page only - no \"Show as text\" (%s)" % (label, L["all"]),
                    not any("as text" in t.lower() for t in L["all"]) and [x["t"] for x in lk] == ["Enlarge", "Show the whole page"], L["all"])
                fills = one_row and abs(lk[0]["l"] - L["box"]["l"]) <= 1 and abs(lk[1]["r"] - L["box"]["r"]) <= 1
                chk("%s: each is a 44px tap target, inside the card, nothing cut off, side by side filling the row edge to edge or stacked full width (%s)" % (label, L),
                    len(lk) == 2 and all(x["h"] >= 44 and x["w"] >= 44 and not x["clipped"] and x["l"] >= L["card"]["l"] and x["r"] <= L["card"]["r"] for x in lk)
                    and L["box"]["sw"] <= L["box"]["cw"] + 1 and (fills or stacked), L)
                # (5) the viewer
                if lk:
                    tap(cdp, *pg.evaluate(CENTRE, ".ifc-code[open] .ifc-links .ifc-link"))
                    for _ in range(60):
                        if pg.evaluate("()=>!!document.querySelector('.ifc-vz-pages canvas')"): break
                        pg.wait_for_timeout(150)
                    pg.wait_for_timeout(3500)
                    V = pg.evaluate("""()=>{ const s=document.querySelector('.ifc-vz-scroll'), cv=document.querySelector('.ifc-vz-pages canvas'), card=document.querySelector('.ifc-vz-card'), bar=document.querySelector('.ifc-vz-bar'), hint=document.querySelector('.ifc-vz-hint');
                      const a=s.getBoundingClientRect(), c=cv.getBoundingClientRect(), k=card.getBoundingClientRect(), br=bar.getBoundingClientRect();
                      const hs=getComputedStyle(hint); return { sw:Math.round(a.width), sh:Math.round(a.height), cw:Math.round(c.width), ch:Math.round(c.height), dMid:Math.round((c.top+c.bottom)/2-(a.top+a.bottom)/2),
                        room:Math.round(k.bottom-br.bottom-a.height), hint:+(+hs.opacity).toFixed(2), hintShown: hs.display!=='none' && hs.visibility!=='hidden' && +hs.opacity>0.05 }; }""")
                    chk("%s: Enlarge opens the excerpt fitted to the width (%d of %d) and on the view's middle (off by %dpx)" % (label, V["cw"], V["sw"], V["dMid"]),
                        V["cw"] >= V["sw"] * 0.9 and (V["ch"] >= V["sh"] - 2 or abs(V["dMid"]) <= 4), V)
                    chk("%s: the zoom hint is not a bar under the page (gone by 3.5s: opacity %s; room it takes %dpx)" % (label, V["hint"], V["room"]),
                        not V["hintShown"] and V["room"] <= 2, V)
                    if label.startswith("Pro Max 440"):
                        tap(cdp, *pg.evaluate(CENTRE, ".ifc-vz-btn.is-in")); pg.wait_for_timeout(500)
                        z = pg.evaluate("()=>Math.round(document.querySelector('.ifc-vz-pages canvas').getBoundingClientRect().width)")
                        tap(cdp, *pg.evaluate(CENTRE, ".ifc-vz-btn.is-done")); pg.wait_for_timeout(700)
                        gone = pg.evaluate("()=>!document.querySelector('.ifc-vz')")
                        chk("+ still zooms (%d -> %d) and Done still closes (%s)" % (V["cw"], z, gone), z > V["cw"] * 1.3 and gone, [z, gone])
                    else:
                        pg.evaluate("()=>ifcCloseViewer()"); pg.wait_for_timeout(400)
            pg.evaluate("()=>{ try{ testInProgress=false; }catch(e){} showHome(); }"); pg.wait_for_timeout(900)
        ctx.close()

    # ---- (2) the results
    MM = """()=>{ const p=document.querySelector('.rs-screen'); if(!p) return { left:true }; const b=[...p.querySelectorAll('.rs-final button')].find(x=>/Main menu/.test(x.textContent));
      if(!b) return { none:true }; const c=b.parentElement; if(b.getBoundingClientRect().bottom>innerHeight || b.getBoundingClientRect().top<0) b.scrollIntoView({block:'center',behavior:'instant'});
      const r=b.getBoundingClientRect(); const anim=b.getAnimations().filter(a=>a.playState==='running').length;
      return { x:r.left+r.width/2, y:r.top+r.height/2, op:Math.min(+getComputedStyle(b).opacity, +getComputedStyle(c).opacity), rising:c.classList.contains('rs-rising') || anim>0, landed:c.classList.contains('rs-in-now') }; }"""
    def results(tapping):
        ctx, pg, cdp = page(br, 440, 956, (62, 0, 34, 0))
        pg.evaluate("""async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const ids=%s.slice(0, 5);
          cfg.source='all'; cfg.mode='drill'; cfg.units=[QUESTIONS[ids[0]].topic]; beginRun(ids); for(let t=0;t<80 && !document.querySelector('.qpanel .choice');t++) await wait(100);
          order.forEach((qi,k)=>{ attempts[qi] = k < 3 ? 2 : 1; picked[qi] = optionOrder(qi).indexOf(QUESTIONS[qi].answer); }); stopQuestionTimer(); summarize(); }""" % AMEND)
        log = []; last = 0; t0 = time.time(); seen = None
        while time.time() - t0 < 30:
            st = pg.evaluate(MM)
            if st.get("left"): log.append("LEFT"); break
            if st.get("none"): pg.wait_for_timeout(60); continue
            if (st["rising"] or st["landed"]) and st["op"] >= 0.3: seen = st; break
            if tapping and time.time() - last > 0.3:
                tap(cdp, st["x"], st["y"]); last = time.time(); log.append("tap")
            pg.wait_for_timeout(40)
        out = { "taps": log.count("tap"), "left_early": "LEFT" in log, "seen": seen }
        if seen:
            # a finger lands while the buttons come up (a third of the way in) and lifts 450ms later, once they are up
            st = pg.evaluate(MM)
            touch(cdp, "touchStart", st["x"], st["y"]); time.sleep(0.45); touch(cdp, "touchEnd"); pg.wait_for_timeout(700)
            out["held_still"] = pg.evaluate("()=>!!document.querySelector('.rs-screen')")
            if out["held_still"]:
                pg.wait_for_timeout(1300)
                st = pg.evaluate(MM)
                if st.get("x"): tap(cdp, st["x"], st["y"]); pg.wait_for_timeout(900)
                out["home"] = pg.evaluate("()=>!!document.querySelector('.screen-home-actual') && !document.querySelector('.rs-screen')")
        ctx.close()
        return out
    r1 = results(True) if want("results") else None
    r2 = results(False) if want("results") else None
    if r1: chk("results: %d taps where Main menu would be, before it was up, pressed nothing (%s)" % (r1["taps"], r1), r1["taps"] >= 2 and not r1["left_early"] and r1["seen"], r1)
    for tag, r in ((("after taps", r1), ("untouched", r2)) if r1 else ()):
        chk("results (%s): a touch that starts while the buttons come up and lifts once they are up does not press Main menu (still on the results: %s)" % (tag, r.get("held_still")), r.get("held_still") is True, r)
        chk("results (%s): a fresh tap once they have settled presses it (home: %s)" % (tag, r.get("home")), r.get("home") is True, r)
    br.close()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
