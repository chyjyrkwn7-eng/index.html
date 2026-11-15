#!/usr/bin/env python3
"""384.125: THE FIRE CODE CALCULATOR.

Madison: "Let's add a calculator for the ifc version. It would be a little button similar to the star, it pulls up a tiny simple
calculator. Make it look cool and make it match the test theme. This is due to a lot of the occupant load stuff requires math."

Fire Code, installed iPhone 17 Pro Max 440x956 (and iPad Pro 11" 834x1194 for placement):
 (A) ON EVERY ANSWERING SCREEN (drill, mock, review, the daily question, a race): a .qcalc-btn just before the star in the same
     row, its size within 1px of the star's and >= 44px, level with it (centre within 1px), left of it by a gap under 24px,
     aria-label "Calculator"; the iPad too.  The academy: no calculator button and no panel anywhere (drill, mock), the star
     still there.
 (B) OPENING on the phone: the panel is shown (opacity 1, inside the screen) and, after its own scroll, no answer choice is under
     it, and the question's text is still below the top row (Pause); on the iPad the card is below the choices with no scroll.
 (C) THE KEYS: a table of sequences, each result read off the display (12.5 / 0.25, 0.1 + 0.2, 4,200 / 7 x 3, chained ops with
     x before +, division by zero, backspace, clear, repeated =, decimals, negatives, sign change, a long result kept inside
     the display), and the keyboard: "4200/7" + Enter gives 600 and picks no answer.
 (D) DISMISS: the x, Escape, the button again, a tap on an answer (closes AND picks it), Pause, Home, the next question - and the
     panel is gone from <body> after the screen goes.
 (E) THEME: the equals key's background and an operator's colour come from the theme (they differ between three themes and carry
     the theme's own colour).
 (F) REDUCE MOTION (the in-app switch): opened, the panel is at opacity 1 at once.
 (G) every key is a <button> >= 44x44 with its text or icon; (H) no page errors.
  python3 tools/check-b384-calc.py [--against OLD/index.html]      (384.107 must FAIL (A)-(G))
"""
import json, os, sys, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
from playwright.sync_api import sync_playwright
RAW = open(sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else cb.SRC, encoding="utf-8").read()
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:600], flush=True)
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 26_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.1 Mobile/15E148 Safari/604.1"
UA_PAD = UA.replace("iPhone; CPU iPhone OS", "iPad; CPU OS")
SEEN = ("['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card','class26e.getstarted',"
        "'class26e.ifc.intro.seen','class26e.ifc.unithold.tip','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted','class26e.ifc.freshstart',"
        "'class26e.penal55124.seen','class26e.penal124256.seen','class26e.penal256578.seen','class26e.a2hs'].forEach(k=>localStorage.setItem(k,'1'));"
        "localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.weekrecap.v1','9999-12-31');")
IFC = ("localStorage.setItem('class26e.ifc.drill.v1', localStorage.getItem('class26e.drill.v1')); localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc']));"
       "localStorage.setItem('class26e.greet.ifc','done'); localStorage.setItem('class26e.activeclass','ifc');")
def account(cls):
    d = json.loads(cb.USED_ACCOUNT); d["novaMet"] = 99
    if cls == "ifc": d["publicId"] = "xph5b57jbp5a"; d["classes"] = ["academy", "ifc"]   # the owner's account is in Fire Code
    return json.dumps(d)
errs = []
def boot(br, W, H, ua, it, ib, cls):
    ins = {"top": "%dpx" % it, "bottom": "%dpx" % ib, "left": "0px", "right": "0px"}
    body = cb.INSET_RE.sub(lambda m: ins[m.group(1)], RAW).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
    ctx = br.new_context(viewport={"width": W, "height": H}, screen={"width": W, "height": H}, device_scale_factor=2, has_touch=True, is_mobile=True, user_agent=ua)
    ctx.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true});")
    ctx.add_init_script("(()=>{ try{ if(localStorage.getItem('class26e.drill.v1')) return; localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-3843'); %s %s }catch(e){} })();"
                        % (json.dumps(account(cls)), SEEN, IFC if cls == "ifc" else ""))
    pg = ctx.new_page(); pg.set_default_timeout(180000)
    pg.route("**/index.html*", lambda r: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=body))
    pg.route("**/version.json*", lambda r: r.abort())
    pg.on("pageerror", lambda e: errs.append("%s %dx%d: %s" % (cls, W, H, str(e)[:160])))
    pg.goto("http://127.0.0.1:%d/index.html" % PORT, timeout=180000); pg.wait_for_timeout(3000)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); try{ homeUnlocksOwed=()=>false; }catch(e){} try{ store.novaMet = 99; }catch(e){}"
                " try{ scheduleWeekRecap=()=>{}; maybeShowWeekRecap=()=>{}; }catch(e){} document.querySelectorAll('#tour-overlay,#tour-tooltip,#nova-intro,.unlock-card').forEach(n=>n.remove()); }")
    pg.wait_for_timeout(600)
    return ctx, pg
CLEAR = ("()=>{ document.querySelectorAll('.intro-pop,#intro-pop,.update-banner,.daily-alert,.savecode-card,.unlock-card,.challenge-pop,#tour-overlay,#tour-tooltip').forEach(n=>n.remove());"
         " document.body.classList.remove('cutscene-focus','cutscene-return'); }")
START = """(mode)=>{ theme.autoAdvance=false; try{ showHome(); }catch(e){} window.scrollTo(0,0);
  const topics=[...new Set(QUESTIONS.map(q=>(q.topic||'').trim()))]; const u = topics.find(t=>/^Chapter 10\\b/.test(t)) || topics.find(t=>/Identity Crimes/.test(t)) || topics[0];
  const idx = QUESTIONS.map((q,i)=>i).filter(i => (QUESTIONS[i].topic||'').trim() === u);
  cfg.source='all'; cfg.units=[u]; cfg.versions={};
  if(mode === 'daily'){ store.dailyQuestionDate = null; startDailyQuestion(); return; }
  if(mode === 'race'){ cfg.mode='drill'; raceTimedNext = true; beginRun(idx.slice(0, 6)); return; }
  cfg.mode = mode; beginRun(idx); }"""
def start(pg, mode):
    pg.evaluate(CLEAR); pg.evaluate(START, mode)
    pg.wait_for_selector("#stage .choice", timeout=90000); pg.wait_for_timeout(1000); pg.evaluate(CLEAR); pg.wait_for_timeout(150)
ROW = """()=>{ const R=e=>{ if(!e) return null; const b=e.getBoundingClientRect(); return {l:b.left,t:b.top,w:b.width,h:b.height,r:b.right,cy:b.top+b.height/2}; };
  const f=document.querySelector('#stage .qnumrow > .flagbtn'), c=document.querySelector('#stage .qcalc-btn');
  return { star:R(f), calc:R(c), next: !!(c && c.nextElementSibling === f), label: c && c.getAttribute('aria-label'), tag: c && c.tagName,
    any: document.querySelectorAll('.qcalc-btn, .qcalc').length }; }"""
STATE = """()=>{ const p=document.querySelector('.qcalc'); const R=e=>{ const b=e.getBoundingClientRect(); return {t:b.top,b:b.bottom,l:b.left,r:b.right}; };
  const v=document.querySelector('.qcalc-val');
  return { inBody: !!(p && p.parentElement === document.body), open: !!(p && p.classList.contains('is-open')), op: p ? +getComputedStyle(p).opacity : null,
    panel: p ? R(p) : null, val: v ? v.textContent : null, fits: v ? v.scrollWidth <= v.clientWidth + 1 : null,
    choices: [...document.querySelectorAll('#stage .choice')].map(R), q: (e=>e?R(e):null)(document.querySelector('#stage .qtext')),
    pause: (e=>e && e.getClientRects().length ? R(e) : null)(document.getElementById('pausebtn')), sy: scrollY, H: innerHeight }; }"""
OPEN = "()=>{ const b=document.querySelector('#stage .qcalc-btn'); if(b) b.click(); }"
KEYS = "(ks)=>{ for(const k of ks){ const b=document.querySelector('.qcalc-key[data-k=\"'+k+'\"]'); if(!b) throw new Error('no key '+k); b.click(); } return document.querySelector('.qcalc-val').textContent; }"
def keys(s):
    out = []
    i = 0
    while i < len(s):
        for w in ("back", "neg"):
            if s.startswith(w, i): out.append(w); i += len(w); break
        else:
            ch = s[i]; i += 1
            if ch != " ": out.append({"x": "*", "÷": "/"}.get(ch, ch))
    return out
TABLE = [("12.5÷0.25=", "50"), ("0.1+0.2=", "0.3"), ("4200÷7x3=", "1,800"), ("4200÷7=", "600"), ("2+3x4=", "14"), ("9-4+2=", "7"),
         ("2x3+4=", "10"), ("5÷0=", "Error"), ("5÷0=4", "4"), ("123back", "12"), ("12+3C", "0"), ("5+3===", "14"), ("1÷3=", "0.333333333333"),
         ("3-8=", "−5"), ("2.5x4=", "10"), ("7negx6=", "−42"), ("1.0.5", "1.05"), ("0.1x3=", "0.3"), ("1.2-1=", "0.2"),
         ("5x=", "25"), ("8+-2=", "6"), ("1000x1000=", "1,000,000"), ("49÷7÷7=", "1")]
srv, PORT = rc["serve"]()
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    # ---------------- Fire Code, phone ----------------
    ctx, pg = boot(br, 440, 956, UA, 59, 34, "ifc")
    chk("Fire Code page (ownClass ifc)", pg.evaluate("()=>ownClass()") == "ifc")
    for mode in ("drill", "exam", "review", "daily", "race"):
        try:
            start(pg, mode); r = pg.evaluate(ROW)
        except Exception as e:
            r = None; errs.append("start %s: %s" % (mode, str(e)[:120]))
        s, c = (r or {}).get("star"), (r or {}).get("calc")
        good = bool(s and c and r["next"] and r["tag"] == "BUTTON" and r["label"] == "Calculator" and abs(c["w"] - s["w"]) <= 1 and abs(c["h"] - s["h"]) <= 1
                    and min(c["w"], c["h"]) >= 44 and abs(c["cy"] - s["cy"]) <= 1 and c["r"] <= s["l"] and s["l"] - c["r"] < 24)
        chk("(A) Fire Code %s: the calculator button sits just left of the star, its size, level, >= 44px, labelled" % mode, good, r)
    # (B) geometry, a drill question
    start(pg, "drill"); pg.evaluate(OPEN); pg.wait_for_timeout(900); st = pg.evaluate(STATE)
    p = st["panel"]
    chk("(B) open: the panel is on <body>, shown, inside the screen", st["inBody"] and st["open"] and st["op"] > .99 and p and p["t"] >= 0 and p["b"] <= st["H"] and p["l"] >= 0, st)
    cover = [c for c in st["choices"] if p and c["b"] > p["t"] + .5]
    chk("(B) phone: no answer choice under the panel once open (scrolled %dpx)" % st["sy"], p and not cover, (p, cover))
    chk("(B) phone: the question's text still below the top row", st["q"] and st["pause"] and st["q"]["t"] >= st["pause"]["b"], (st["q"], st["pause"]))
    # (C) the keys
    bad = []
    for seq, want in TABLE:
        got = pg.evaluate("()=>{ document.querySelector('.qcalc-key[data-k=\"C\"]').click(); }") or pg.evaluate(KEYS, keys(seq))
        if got != want: bad.append((seq, want, got))
    chk("(C) %d key sequences read off the display" % len(TABLE), not bad, bad)
    pg.evaluate("()=>document.querySelector('.qcalc-key[data-k=\"C\"]').click()")
    pg.evaluate(KEYS, keys("1÷7=")); st = pg.evaluate(STATE)
    pg.evaluate(KEYS, ["C"] + keys("123456789012x1000000=")); st2 = pg.evaluate(STATE)
    chk("(C) a long result stays inside the display (%s, %s)" % (st["val"], st2["val"]), st["fits"] and st2["fits"] and len(st2["val"]) <= 14, (st, st2))
    pg.evaluate(KEYS, ["C"])
    att0 = pg.evaluate("()=>JSON.stringify(attempts)")
    for k in "4200/7": pg.keyboard.press(k)
    pg.keyboard.press("Enter"); pg.wait_for_timeout(200)
    kv = pg.evaluate("()=>document.querySelector('.qcalc-val').textContent"); att1 = pg.evaluate("()=>JSON.stringify(attempts)")
    chk("(C) keyboard: 4200/7 Enter shows 600 and answers nothing (got %s)" % kv, kv == "600" and att0 == att1 and pg.evaluate("()=>!!document.querySelector('.qcalc.is-open')"), (kv, att0, att1))
    # (D) dismiss paths
    def is_open(): return pg.evaluate("()=>!!document.querySelector('.qcalc.is-open')")
    def gone(): return pg.evaluate("()=>!document.querySelector('.qcalc')")
    pg.evaluate("()=>document.querySelector('.qcalc-close').click()"); pg.wait_for_timeout(400)
    chk("(D) the x closes it (and it leaves <body>)", not is_open() and gone())
    pg.evaluate(OPEN); pg.wait_for_timeout(400); pg.keyboard.press("Escape"); pg.wait_for_timeout(400)
    chk("(D) Escape closes it, and does not pause the run", not is_open() and pg.evaluate("()=>!paused"))
    pg.evaluate(OPEN); pg.wait_for_timeout(300); pg.evaluate(OPEN); pg.wait_for_timeout(400)
    chk("(D) the button again closes it", not is_open())
    pg.evaluate(OPEN); pg.wait_for_timeout(500)
    a0 = pg.evaluate("()=>attempts[order[pos]] || 0")
    pg.locator("#stage .choice").first.click(); pg.wait_for_timeout(600)
    a1 = pg.evaluate("()=>attempts[order[pos]] || 0")
    chk("(D) a tap on an answer closes it and the answer is still taken (attempts %s -> %s)" % (a0, a1), not is_open() and a1 > a0)
    pg.evaluate(OPEN); pg.wait_for_timeout(400)
    pg.evaluate("()=>{ pauseRun(); }"); pg.wait_for_timeout(500)
    chk("(D) Pause takes it away (nothing left on <body>)", gone() and not pg.evaluate("()=>document.documentElement.classList.contains('qcalc-room')"))
    pg.evaluate("()=>{ resumeRun(); }"); pg.wait_for_timeout(700)
    pg.evaluate(OPEN); pg.wait_for_timeout(400)
    pg.evaluate("()=>{ const r=correctSlot(order[pos]); render(); }"); pg.wait_for_timeout(300)
    chk("(D) a redraw of the same question keeps it open", is_open())
    pg.evaluate("()=>{ const r=correctSlot(order[pos]); const c=document.querySelector('#stage .choice[data-index=\"'+r+'\"]'); if(c && !c.disabled) c.click(); }"); pg.wait_for_timeout(500)
    pg.evaluate(OPEN); pg.wait_for_timeout(400); p0 = pg.evaluate("()=>pos"); was = is_open()
    pg.evaluate("()=>{ advance(); }"); pg.wait_for_timeout(500)
    chk("(D) the next question closes it (pos %s -> %s)" % (p0, pg.evaluate("()=>pos")), was and not is_open() and pg.evaluate("()=>pos") == p0 + 1)
    # the slide to the next question with it open (motion on): it goes, the slide finishes clean, the new question has its button
    pg.evaluate("()=>{ theme.reduceMotion=false; applyTheme(); const r=correctSlot(order[pos]); const c=document.querySelector('#stage .choice[data-index=\\\"'+r+'\\\"]'); if(c && !c.disabled) c.click(); }"); pg.wait_for_timeout(500)
    pg.evaluate(OPEN); pg.wait_for_timeout(400); p0 = pg.evaluate("()=>pos")
    pg.evaluate("()=>advanceWithSlide()"); pg.wait_for_timeout(1200)
    sl = pg.evaluate("()=>({ pos, sliding: document.documentElement.classList.contains('q-sliding'), clones: document.querySelectorAll('.q-slide-clone').length, open: !!document.querySelector('.qcalc.is-open'), btn: document.querySelectorAll('#stage .qcalc-btn').length, room: document.documentElement.classList.contains('qcalc-room') })")
    chk("(D) the slide to the next question with it open: closed, slide done clean, the new question has its button (%s)" % sl,
        sl["pos"] == p0 + 1 and not sl["sliding"] and not sl["clones"] and not sl["open"] and sl["btn"] == 1 and not sl["room"], sl)
    pg.evaluate(OPEN); pg.wait_for_timeout(400); pg.evaluate("()=>showHome()"); pg.wait_for_timeout(600)
    chk("(D) navigation (Home) clears it from <body>", gone() and not pg.evaluate("()=>document.querySelectorAll('.qcalc-btn').length"))
    # (E) theme
    cols = {}
    for acc in ("ink", "adept", "titan"):
        pg.evaluate("(a)=>{ theme.accent=a; applyTheme(); }", acc); start(pg, "drill"); pg.evaluate(OPEN); pg.wait_for_timeout(500)
        cols[acc] = pg.evaluate("""()=>{ const eq=getComputedStyle(document.querySelector('.qcalc-key.is-eq')), op=getComputedStyle(document.querySelector('.qcalc-key.is-op'));
          const hue=getComputedStyle(document.querySelector('.qcalc')).getPropertyValue('--qcalc-hue').trim();
          const c=document.createElement('i'); c.style.color=hue; document.body.appendChild(c); const h=getComputedStyle(c).color; c.remove();
          return { eq: eq.backgroundImage, op: op.color, hue: h }; }""")
        pg.evaluate("()=>document.querySelector('.qcalc-close').click()"); pg.wait_for_timeout(300)
    def nums(s):
        import re; return [round(float(x), 2) for x in re.findall(r"[\d.]+", s)[:3]]
    differ = len({cols[a]["eq"] for a in cols}) == 3 and len({cols[a]["op"] for a in cols}) == 3
    carries = all(cols[a]["hue"] and cols[a]["eq"].count("gradient") for a in cols)
    chk("(E) equals and operators take the theme's colour (all three themes differ)", differ and carries, cols)
    pg.evaluate("()=>{ theme.accent='ink'; applyTheme(); }")
    # (G) keys
    start(pg, "drill"); pg.evaluate(OPEN); pg.wait_for_timeout(500)
    g = pg.evaluate("""()=>[...document.querySelectorAll('.qcalc button')].map(b=>{ const r=b.getBoundingClientRect(); return [b.dataset.k||b.className, Math.round(r.width), Math.round(r.height), b.tagName, !!(b.textContent.trim()||b.querySelector('svg')), b.getAttribute('aria-label')||b.textContent.trim()]; })""")
    small = [x for x in g if x[1] < 44 or x[2] < 44 or x[3] != "BUTTON" or not x[4] or not x[5]]
    chk("(G) %d keys and the x: real buttons, >= 44x44, labelled" % len(g), len(g) == 20 and not small, small or g)
    pg.evaluate("()=>document.querySelector('.qcalc-close').click()"); pg.wait_for_timeout(300)
    # (F) the in-app Reduce motion switch
    pg.evaluate("()=>{ theme.reduceMotion=true; applyTheme(); }"); pg.evaluate(OPEN); pg.wait_for_timeout(60)
    st = pg.evaluate(STATE)
    chk("(F) Reduce motion: shown at once (opacity %s)" % st["op"], st["op"] is not None and st["op"] > .99)
    pg.evaluate("()=>document.querySelector('.qcalc-close').click()"); pg.wait_for_timeout(60)
    chk("(F) Reduce motion: closed at once", pg.evaluate("()=>!document.querySelector('.qcalc')"))
    ctx.close()
    # ---------------- Fire Code, iPad ----------------
    ctx, pg = boot(br, 834, 1194, UA_PAD, 24, 20, "ifc")
    start(pg, "drill"); r = pg.evaluate(ROW); s, c = r["star"], r["calc"]
    chk("(A) iPad: beside the star, its size, level", bool(s and c and r["next"] and abs(c["w"] - s["w"]) <= 1 and abs(c["cy"] - s["cy"]) <= 1), r)
    pg.evaluate(OPEN); pg.wait_for_timeout(700); st = pg.evaluate(STATE); p = st["panel"]
    cover = [x for x in st["choices"] if p and x["b"] > p["t"] and x["r"] > p["l"]]
    chk("(B) iPad: a card below the choices, no scroll (top %s)" % (p and round(p["t"])), p and st["op"] > .99 and not cover and st["sy"] == 0, (p, cover, st["sy"]))
    ctx.close()
    # ---------------- the academy ----------------
    ctx, pg = boot(br, 440, 956, UA, 59, 34, "academy")
    for mode in ("drill", "exam"):
        start(pg, mode); r = pg.evaluate(ROW)
        chk("(A) academy %s: no calculator anywhere, the star still there" % mode, r["any"] == 0 and r["star"] is not None, r)
    ctx.close()
    br.close()
chk("(H) no page errors", not errs, errs[:6])
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
