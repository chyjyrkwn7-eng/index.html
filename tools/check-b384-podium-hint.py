"""Build 384: last week's podium back, nicer; Fire Code's hint button.
Madison: "Last weeks top 3 should not look like the list, I liked the podium style, it just needed a nicer look to it that's all.."
         "The hint button in ifc, fix that layout/wording. Cause all the words are layed out weird? Idk."
Shape is read off the page (no label strings, no typed sizes beyond the 44px tap minimum):
(a) LAST WEEK'S TOP 3 on This Week, at 440x956 (iPhone 17 Pro Max), 375x667 (SE), 834x1194 (iPad Pro 11") and a 1536x864 laptop,
    dark (the app's only theme), with a long name and big XP numbers:
    (a1) a podium: three places side by side, 2nd - 1st - 3rd from the left, 1st in the middle of the card; each place has a disc
         with its character, a name, its XP and a step under them; the steps stand on one floor (the card's bottom) and 1st's
         step is the tallest (then 2nd, then 3rd) and its disc the highest;
    (a2) nothing clipped or overlapping: every part of every place (the disc with its ring, the name, the XP, the step) is inside
         the card and the screen; the places do not overlap each other; in a place, disc / name / XP / step stack without
         overlapping; the XP numbers are whole (not cut short); a name too long for its place ends in an ellipsis on one line
         inside its place (the long one does here), never wraps or runs out of it;
    (a3) GUARD (passes on both builds - it says nothing was lost): each place is tappable and opens that person's card, by a tap on
         its disc; they are buttons (role, tab stop, a name) in the page in 1st-2nd-3rd order; each place is 44px+ to tap.
(b) FIRE CODE'S HINT (class26e.activeclass = "ifc"), a Drill question whose code can be shown with the answer hidden, at 375x667
    and 440x956 (and 440 again at 125% text, as a user's text size makes it):
    (b1) the hint control's words lie on one line (or on two lines that start at the same left edge - never a centred ragged
         wrap), none cut short, the control 44px+ tall and inside the question's panel;
    (b2) GUARD: a tap shows the code with the answer hidden (a picture is drawn under it, the question is still unanswered) and a
         second tap puts it away;
    (b3) GUARD: the academy's own hint ("show me the answer" after three misses in a Drill) still comes, on one line, and a tap on
         it marks the right answer (it is a text link about 33px tall on this build and the one before - not changed here);
(c) no page errors.
pdf.js: the code is drawn with pdf.js, which the sandbox cannot reach. With PDFJS_DIR (an unpacked pdfjs-dist@5.4.149) the real
path runs (the county's booklet in ifc/, cut and painted); without it, ifcCountyDoc and the viewer's three drawing calls are
stood in for (the button, its words and its tap are the app's own code either way) and the gate says so.
Run:  [PDFJS_DIR=...] python3 tools/check-b384-podium-hint.py [--against REV|FILE] [--only a,b]
      (--against 1dca98e must FAIL (a1), (a2) and (b1))"""
import json, os, re, subprocess, sys, time, mimetypes
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
from playwright.sync_api import sync_playwright
srv, url = g["serve"]()
ONLY = None
if "--only" in sys.argv: ONLY = set(sys.argv[sys.argv.index("--only") + 1].split(","))
def want(k): return ONLY is None or k in ONLY
AGAINST = None
if "--against" in sys.argv:
    a = sys.argv[sys.argv.index("--against") + 1]
    AGAINST = open(a, encoding="utf-8").read() if os.path.isfile(a) else subprocess.check_output(["git", "-C", ROOT, "show", a + ":index.html"]).decode("utf-8")
def body_for(ins):
    if AGAINST is None: return g["patched"](ins)
    t, r, b, l = ins; v = {"top": f"{t}px", "right": f"{r}px", "bottom": f"{b}px", "left": f"{l}px"}
    return g["INSET_RE"].sub(lambda m: v[m.group(1)], AGAINST)
PDFJS = os.environ.get("PDFJS_DIR", "").rstrip("/") + "/"
REAL_PDF = os.path.exists(PDFJS + "build/pdf.min.mjs")
SHOTS = os.environ.get("SHOTS", "")
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:900], flush=True)
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1"
UA_IPAD = "Mozilla/5.0 (iPad; CPU OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1"
OWNER = "xph5b57jbp5a"
SEEN = ("['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card','class26e.getstarted',"
        "'class26e.ifc.intro.seen','class26e.ifc.unithold.tip','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted','class26e.ifc.freshstart'].forEach(k=>localStorage.setItem(k,'1'));"
        "localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.penal256578.seen','1');")
INIT = """(()=>{ if(localStorage.getItem('class26e.drill.v1')) return;
 localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-3843'); """ + SEEN + """ %s })()"""
IFC = ("localStorage.setItem('class26e.ifc.drill.v1', localStorage.getItem('class26e.drill.v1')); localStorage.setItem('class26e.ifc.synccode','TEST-3843');"
       "localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done'); localStorage.setItem('class26e.activeclass','ifc');")
def seed():
    d = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]())); d["publicId"] = OWNER; d["firstName"] = "Casey"; d["novaMet"] = 99
    return d
def route_pdf(ctx):
    def h(r, req):
        rel = req.url.split("pdfjs-dist@5.4.149/", 1)[1].split("?")[0]; p = PDFJS + rel
        if not os.path.exists(p): return r.fulfill(status=404, body="")
        ct = "application/wasm" if p.endswith(".wasm") else ("text/javascript" if p.endswith((".mjs", ".js")) else (mimetypes.guess_type(p)[0] or "application/octet-stream"))
        r.fulfill(status=200, body=open(p, "rb").read(), content_type=ct, headers={"access-control-allow-origin": "*"})
    ctx.route("**/pdfjs-dist@5.4.149/**", h)
def page(br, w, h, ins, installed=True, touch=True, ua=None, cls="academy"):
    kw = {"viewport": {"width": w, "height": h}, "device_scale_factor": 2, "has_touch": touch}
    if ua: kw.update(is_mobile=True, user_agent=ua)
    ctx = br.new_context(**kw)
    if installed: ctx.add_init_script(g["STANDALONE"])
    ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]()))
    if REAL_PDF: route_pdf(ctx)
    pg = ctx.new_page(); body = body_for(ins)
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    m = re.search(r'const APP_BUILD = "([^"]+)"', body); bld = m.group(1) if m else ""
    pg.route("**/version.json*", lambda route, request, b=bld: route.fulfill(status=200, headers={"content-type": "application/json"},
             body=json.dumps({"build": b, "note": "", "frameId": "", "force": True, "safariSound": True})))
    pg.add_init_script(INIT % (json.dumps(json.dumps(seed())), IFC if cls == "ifc" else ""))
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.goto(url); pg.wait_for_timeout(3500)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); try{ homeUnlocksOwed=()=>false; }catch(e){} store.novaMet=99; "
                "try{ scheduleWeekRecap=()=>{}; maybeShowWeekRecap=()=>{}; }catch(e){} "
                "document.querySelectorAll('#tour-overlay, #tour-tooltip, #nova-intro, .rs-spot, .unlock-card').forEach(n=>n.remove()); }")
    return ctx, pg, errs
def tap(cdp, x, y, hold=0.07):
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]}); time.sleep(hold)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
def press(pg, cdp, touch, x, y):
    if touch: tap(cdp, x, y)
    else: pg.mouse.click(x, y)
ALLERRS = []

# ------------------------------------------------------------------------------------------------ (a) last week's top 3
FILLFN = """()=>{ const ids=['ninja','wizard','ghost','grizzly','alien','detective','zeus','clown']; const rows=[];
  for(let i=0;i<30;i++){ rows.push(Object.assign({pub:'zz'+i, firstName:'Cadet'+i, avatarChar:ids[i%ids.length]}, boardNumbersOf(store),
    {week: weekKeyNow(), weekPoints:1000-i*17, hundos:60-i, correct:5000-i*70, level:Math.max(1,84-i*3), badges:Math.max(0,24-i), mystery:0, rankFloor:0, xp:90000-i*2000})); }
  return rows; }"""
# a long name (it cannot fit a place on any screen here) in second, big numbers on all three
TOP = [{"pub": "zz4", "name": "OdinSavior", "avatar": "alien", "pts": 12345},
       {"pub": "zz1", "name": "Bartholomew-Montgomery", "avatar": "wizard", "pts": 11980},
       {"pub": "zz7", "name": "Alexandria", "avatar": "clown", "pts": 10402}]
SHAPE = r"""()=>{ const pod=document.querySelector('.screen-rankings .lw-podium'); if(!pod) return null;
  const px=v=>parseFloat(v)||0; const R=e=>{ const b=e.getBoundingClientRect(); return {l:b.left, t:b.top, r:b.right, b:b.bottom, w:b.width, h:b.height}; };
  const card=pod.querySelector(':scope > :not(.lw-podium-head)'); const C=card?R(card):null;
  const spots=[...pod.querySelectorAll('.lw-podium-spot')];
  const place=s=>{ const m=/lw-place-(\d)/.exec(s.className); return m?+m[1]:0; };
  const out={ C, vw:innerWidth, vh:innerHeight, spots:[] };
  spots.forEach((s,i)=>{ const o={ place:place(s), dom:i, S:R(s) };
    const av=s.querySelector('.lw-podium-avwrap, .lw-podium-av'); const nm=s.querySelector('.lw-podium-name'); const pt=s.querySelector('.lw-podium-pts'); const st=s.querySelector('.lw-podium-block');
    if(av){ const cs=getComputedStyle(av); const ring=(cs.outlineStyle!=='none'?px(cs.outlineWidth)+Math.max(0,px(cs.outlineOffset)):0); const b=R(av);
      o.disc={ l:b.l-ring, t:b.t-ring, r:b.r+ring, b:b.b+ring, w:b.w, h:b.h, art:!!av.querySelector('svg, img') }; }
    if(nm){ const cs=getComputedStyle(nm); o.name={ ...R(nm), lh:px(cs.lineHeight)||px(cs.fontSize)*1.3, fs:px(cs.fontSize), cut:nm.scrollWidth>nm.clientWidth+1, ell:cs.textOverflow, ws:cs.whiteSpace, empty:!nm.textContent.trim() }; }
    if(pt){ o.pts={ ...R(pt), cut:pt.scrollWidth>pt.clientWidth+1, empty:!pt.textContent.trim() }; }
    if(st){ o.step=R(st); }
    o.tap={ role:s.getAttribute('role'), tab:s.tabIndex, label:(s.getAttribute('aria-label')||'').length>0, tappable:s.classList.contains('is-tappable') };
    out.spots.push(o); });
  return out; }"""
def judge_podium(sh):
    """(a1) and (a2) from the shape; returns (podium_ok, podium_info, clean_ok, clean_info)"""
    if not sh or len(sh["spots"]) != 3: return False, ("spots", sh and len(sh["spots"])), False, "no podium"
    by = {s["place"]: s for s in sh["spots"]}
    if set(by) != {1, 2, 3}: return False, ("places", list(by)), False, "places"
    C = sh["C"]; cx = lambda s: (s["S"]["l"] + s["S"]["r"]) / 2
    parts_ok = all(s.get("disc") and s["disc"]["art"] and s.get("name") and not s["name"]["empty"] and s.get("pts") and not s["pts"]["empty"] and s.get("step") for s in sh["spots"])
    a1 = {"parts": parts_ok}
    if parts_ok:
        x1, x2, x3 = cx(by[1]), cx(by[2]), cx(by[3])
        a1["order213"] = x2 < x1 < x3 and min(x1 - x2, x3 - x1) > 20
        a1["firstMid"] = abs(x1 - (C["l"] + C["r"]) / 2) <= 2
        a1["sideBySide"] = max(s["S"]["t"] for s in sh["spots"]) < min(s["S"]["b"] for s in sh["spots"])
        hs = [by[k]["step"]["h"] for k in (1, 2, 3)]
        a1["steps"] = [round(h, 1) for h in hs]
        a1["tallest"] = hs[0] > hs[1] > hs[2] > 0 and hs[0] - hs[2] >= 8
        floors = [by[k]["step"]["b"] for k in (1, 2, 3)]
        a1["floor"] = max(floors) - min(floors) <= 1 and abs(max(floors) - (C["b"] - 1)) <= 2.5
        a1["firstHighest"] = by[1]["disc"]["t"] < min(by[2]["disc"]["t"], by[3]["disc"]["t"]) - 4
        a1["round"] = all(abs(s["disc"]["w"] - s["disc"]["h"]) <= .5 for s in sh["spots"])
    a1ok = parts_ok and all(v for k, v in a1.items() if k not in ("steps",))
    if not parts_ok: return a1ok, a1, False, "parts missing"
    bad = []
    inside = lambda r, B, e=0.6: r["l"] >= B["l"] - e and r["r"] <= B["r"] + e and r["t"] >= B["t"] - e and r["b"] <= B["b"] + e
    screen = {"l": 0, "t": -1e9, "r": sh["vw"], "b": 1e9}
    for s in sh["spots"]:
        for k in ("disc", "name", "pts", "step"):
            if not inside(s[k], C): bad.append((s["place"], k, "outside the card"))
            if not inside(s[k], screen): bad.append((s["place"], k, "off the screen"))
        if s["name"]["l"] < s["S"]["l"] - .6 or s["name"]["r"] > s["S"]["r"] + .6: bad.append((s["place"], "name runs out of its place"))
        if s["name"]["h"] > s["name"]["lh"] * 1.5: bad.append((s["place"], "name wraps", s["name"]["h"]))
        if s["name"]["cut"] and not (s["name"]["ell"] == "ellipsis" and s["name"]["ws"] == "nowrap"): bad.append((s["place"], "name cut without an ellipsis"))
        if s["pts"]["cut"]: bad.append((s["place"], "XP cut short"))
        seq = [s["disc"], s["name"], s["pts"], s["step"]]
        for u, v in zip(seq, seq[1:]):
            if u["b"] > v["t"] + .6: bad.append((s["place"], "parts overlap", round(u["b"] - v["t"], 1)))
    def box(s):
        rs = [s[k] for k in ("disc", "name", "pts", "step")]
        return {"l": min(r["l"] for r in rs), "r": max(r["r"] for r in rs), "t": min(r["t"] for r in rs), "b": max(r["b"] for r in rs)}
    bx = [box(s) for s in sh["spots"]]
    for i in range(3):
        for j in range(i + 1, 3):
            A, B = bx[i], bx[j]
            if min(A["r"], B["r"]) - max(A["l"], B["l"]) > .6 and min(A["b"], B["b"]) - max(A["t"], B["t"]) > .6: bad.append(("places overlap", i, j))
    longcut = [s["place"] for s in sh["spots"] if s["name"]["cut"]]
    if 2 not in longcut: bad.append(("the long name is not ended with an ellipsis", longcut))
    return a1ok, a1, not bad, bad

if want("a"):
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=g["CHROME"])
        for label, w, h, ins, inst, touch, ua in [("iPhone 17 Pro Max 440x956", 440, 956, (62, 0, 34, 0), True, True, UA),
                                                ("iPhone SE 375x667", 375, 667, (20, 0, 0, 0), True, True, UA),
                                                ("iPad Pro 11 834x1194", 834, 1194, (24, 0, 20, 0), True, True, UA_IPAD),
                                                ("laptop 1536x864", 1536, 864, (0, 0, 0, 0), False, False, None)]:
            ctx, pg, errs = page(br, w, h, ins, inst, touch, ua)
            cdp = ctx.new_cdp_session(pg)
            pg.evaluate("()=>{ showHome(); }"); pg.wait_for_timeout(900)
            pg.evaluate("()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); }")
            pg.evaluate("(T)=>{ window.__fill=(" + FILLFN + "); const c={}; c[lastWeekKey()] = T; localStorage.setItem(WEEK_TOP_KEY, JSON.stringify(c)); leaderboardRows=__fill(); showRankings('week'); window.scrollTo(0,0); }", TOP)
            pg.wait_for_timeout(2600)
            pg.evaluate("()=>{ const p=document.querySelector('.screen-rankings .lw-podium'); if(p) p.scrollIntoView({block:'center', behavior:'instant'}); }"); pg.wait_for_timeout(500)
            sh = pg.evaluate(SHAPE)
            if SHOTS:
                os.makedirs(SHOTS, exist_ok=True); pg.screenshot(path=os.path.join(SHOTS, "podium-%s-%s.png" % (w, "before" if AGAINST else "after")))
            a1ok, a1, a2ok, a2 = judge_podium(sh)
            chk("(a1) %s: a podium - 2nd, 1st, 3rd side by side, each a disc, name, XP and step; one floor, 1st's step tallest %s and its disc highest" % (label, a1.get("steps") if isinstance(a1, dict) else ""), a1ok, a1)
            chk("(a2) %s: nothing clipped or overlapping, inside the card and the screen; XP whole; the long name one line, ended with an ellipsis" % label, a2ok, a2)
            # (a3) GUARD: tappable, buttons in 1-2-3 order, 44px+; a tap on 2nd's disc opens 2nd's card
            g3 = {}
            if sh and len(sh["spots"]) == 3:
                g3["dom123"] = [s["place"] for s in sh["spots"]] == [1, 2, 3]
                g3["buttons"] = all(s["tap"]["role"] == "button" and s["tap"]["tab"] == 0 and s["tap"]["label"] and s["tap"]["tappable"] for s in sh["spots"])
                g3["44px"] = all(s["S"]["w"] >= 44 and s["S"]["h"] >= 44 for s in sh["spots"])
                # 2nd place is TOP[1]; its card is the board's entry for that id (the card shows the board's name for it)
                xy = pg.evaluate("(pub)=>{ const s=document.querySelector('.screen-rankings .lw-podium .lw-place-2'); const a=s.querySelector('.lw-podium-avwrap, .lw-podium-av') || s; const b=a.getBoundingClientRect(); const e=(leaderboardRows||[]).find(r=>r.pub===pub); return [b.left+b.width/2, b.top+b.height/2, e ? e.firstName : null]; }", TOP[1]["pub"])
                press(pg, cdp, touch, xy[0], xy[1]); pg.wait_for_timeout(900)
                card = pg.evaluate("()=>{ const n=document.querySelector('.person-card .person-sheet-name'); return n ? n.textContent : null; }")
                g3["opens"] = bool(xy[2]) and card == xy[2]
            chk("(a3) GUARD %s: each place a button (role, tab stop, a name) in 1st-2nd-3rd page order, 44px+, and a tap on a disc opens that person's card %s" % (label, g3), g3 and all(g3.values()), g3)
            ALLERRS.extend(errs); ctx.close()
        br.close()

# ------------------------------------------------------------------------------------------------ (b) Fire Code's hint
STANDIN = r"""async ()=>{ const M = await ifcViewer(); const fakeDoc = { numPages: 1 };
  window.__paints = 0;
  const V = Object.assign({}, M, {
    countyClip: async () => ({ ok: true, segments: [{ page: 1 }], hide: [] }),
    hideAnswer: async (doc, clip, nums) => (nums && nums.length ? { hide: [{ page: 1, x0: 0, x1: 1, y0: 0, y1: 1 }], hiddenText: nums } : null),
    paint: async (doc, clip, holder) => { __paints++; await new Promise(r => setTimeout(r, 60)); const c = document.createElement('canvas'); c.width = 600; c.height = 160;
      const x = c.getContext('2d'); x.fillStyle = '#fff'; x.fillRect(0, 0, 600, 160); x.fillStyle = '#ccc'; (clip.hide || []).forEach(() => x.fillRect(300, 60, 40, 30)); holder.appendChild(c); } });
  window.ifcViewer = () => Promise.resolve(V); window.ifcCountyDoc = () => Promise.resolve(fakeDoc); return true; }"""
FIND = r"""async (real)=>{ const V = await ifcViewer(); const doc = await ifcCountyDoc(); const out = [];
  const ids = QUESTIONS.map((q, i) => i).filter(i => QUESTIONS[i].ifc && QUESTIONS[i].ifc.citation.source === 'amendment' && !QUESTIONS[i].ifc.citation.blur && V.answerNumbers(QUESTIONS[i].ifc).length);
  for(const i of ids){ const q = QUESTIONS[i].ifc; const clip = await V.countyClip(doc, q.citation, ifcCountyOpts); if(!clip || !clip.ok) continue;
    if(await V.hideAnswer(doc, clip, V.answerNumbers(q))){ out.push(i); if(out.length >= 3) break; } }
  return out; }"""
# the lines a control's words lie on: every text node's line boxes, grouped by their middles (one group, one line)
LINES = r"""(el => { const boxes = []; const walk = n => { if(n.nodeType === 3 && n.textContent.trim()){ const rg = document.createRange(); rg.selectNodeContents(n);
    [...rg.getClientRects()].forEach(q => { if(q.width > 0.5) boxes.push([q.left, q.top, q.right, q.bottom]); }); } else n.childNodes.forEach(walk); }; walk(el);
  const rows = []; boxes.sort((a, c) => a[1] - c[1]).forEach(q => { const mid = (q[1] + q[3]) / 2; const row = rows.find(w => Math.abs((w.top + w.bottom) / 2 - mid) < 4);
    if(row){ row.left = Math.min(row.left, q[0]); row.right = Math.max(row.right, q[2]); } else rows.push({ top: q[1], bottom: q[3], left: q[0], right: q[2] }); });
  return rows; })"""
HINT = r"""()=>{ const b = document.querySelector('.qpanel .ifc-hint-btn'); if(!b) return null; const px = v => parseFloat(v) || 0;
  const r = b.getBoundingClientRect(); const panel = b.closest('.qpanel').getBoundingClientRect();
  const rows = LINES(b);
  const cut = [b, ...b.querySelectorAll('*')].filter(e => { const cs = getComputedStyle(e); return cs.overflow !== 'visible' && e.scrollWidth > e.clientWidth + 1; }).length;
  return { w: r.width, h: r.height, l: r.left, r: r.right, pl: panel.left, pr: panel.right, vw: innerWidth, rows: rows.map(w => [Math.round(w.left * 10) / 10, Math.round(w.top), Math.round(w.right * 10) / 10]), cut,
    on: b.classList.contains('is-on'), pics: document.querySelectorAll('.qpanel .ifc-hintpic canvas').length, cleared: (typeof cleared !== 'undefined') ? cleared : null }; }""".replace("LINES", LINES)
def hint_ok(s):
    if not s: return False
    if len(s["rows"]) == 1: shape = True
    elif len(s["rows"]) == 2: shape = abs(s["rows"][0][0] - s["rows"][1][0]) <= 1
    else: shape = False
    return shape and s["cut"] == 0 and s["h"] >= 44 and s["l"] >= s["pl"] - .5 and s["r"] <= s["pr"] + .5 and s["r"] <= s["vw"]
if want("b"):
    print("(b) pdf.js: %s" % ("the real one from PDFJS_DIR, the county booklet cut and painted" if REAL_PDF else "NOT available - the viewer's drawing calls are stood in for (set PDFJS_DIR for the real path)"), flush=True)
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=g["CHROME"])
        # each width: its layout in both states (shown and put away) at the default text size - and the 440 phone again at 125%
        for label, w, h, ins, zooms in [("SE 375x667", 375, 667, (20, 0, 0, 0), (1,)), ("Pro Max 440x956", 440, 956, (62, 0, 34, 0), (1, 1.25))]:
            seen = []
            for zoom in zooms:
                ctx, pg, errs = page(br, w, h, ins, True, True, UA, cls="ifc")
                cdp = ctx.new_cdp_session(pg)
                cls = pg.evaluate("()=>window.NOVA_CLASS")
                if not REAL_PDF: pg.evaluate(STANDIN)
                if zoom != 1: pg.evaluate("(z)=>{ const r=document.documentElement; r.style.fontSize = (parseFloat(getComputedStyle(r).fontSize) * z) + 'px'; }", zoom)
                ids = pg.evaluate(FIND, REAL_PDF)
                if ids:
                    pg.evaluate("(ids)=>{ cfg.source='all'; cfg.mode='drill'; cfg.units=[QUESTIONS[ids[0]].topic]; beginRun(ids); }", ids)
                    try: pg.wait_for_selector(".qpanel .ifc-hint-btn", timeout=25000)
                    except Exception: pass
                    pg.wait_for_timeout(700)
                    pg.evaluate("()=>{ const b=document.querySelector('.qpanel .ifc-hint-btn'); if(b) b.scrollIntoView({block:'center', behavior:'instant'}); }"); pg.wait_for_timeout(400)
                s = pg.evaluate(HINT) if ids else None
                seen.append(("%s%s, shut" % (w, "@125%" if zoom != 1 else ""), cls == "ifc", s))
                if SHOTS and s:
                    os.makedirs(SHOTS, exist_ok=True); y = pg.evaluate("()=>document.querySelector('.qpanel .ifc-hint-btn').getBoundingClientRect().top")
                    pg.screenshot(path=os.path.join(SHOTS, "hint-%s%s-%s.png" % (w, "-125" if zoom != 1 else "", "before" if AGAINST else "after")), clip={"x": 0, "y": max(0, y - 140), "width": w, "height": 300})
                if s:
                    t0 = pg.evaluate("()=>document.querySelector('.qpanel .ifc-hint-btn').textContent")
                    tap(cdp, *pg.evaluate("()=>{ const r=document.querySelector('.qpanel .ifc-hint-btn').getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]; }"))
                    pg.wait_for_timeout(2500 if REAL_PDF else 900)
                    s1 = pg.evaluate(HINT); t1 = pg.evaluate("()=>document.querySelector('.qpanel .ifc-hint-btn').textContent")
                    seen.append(("%s%s, shown" % (w, "@125%" if zoom != 1 else ""), True, s1))
                    pg.evaluate("()=>document.querySelector('.qpanel .ifc-hint-btn').scrollIntoView({block:'center', behavior:'instant'})"); pg.wait_for_timeout(500)
                    tap(cdp, *pg.evaluate("()=>{ const r=document.querySelector('.qpanel .ifc-hint-btn').getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]; }"))
                    pg.wait_for_timeout(700)
                    s2 = pg.evaluate(HINT); t2 = pg.evaluate("()=>document.querySelector('.qpanel .ifc-hint-btn').textContent")
                    if zoom == 1:
                        chk("(b2) GUARD %s: a tap shows the code with the answer hidden (%s picture, still unanswered: %s, words changed: %s), another puts it away (%s left, words back: %s)"
                            % (label, s1 and s1["pics"], s1 and s1["cleared"] is False, t1 != t0, s2 and s2["pics"], t2 == t0),
                            s1 and s1["pics"] >= 1 and s1["on"] and s1["cleared"] is False and t1 != t0 and s2 and s2["pics"] == 0 and not s2["on"] and t2 == t0, [s1, s2, t0, t1, t2])
                ALLERRS.extend(errs); ctx.close()
            bad = [(k, x and {q: x[q] for q in ("rows", "h", "w", "cut")}) for k, isifc, x in seen if not (isifc and hint_ok(x))]
            chk("(b1) %s, Fire Code: the hint's words on one line (or two from one left edge), none cut short, 44px+, inside the panel - shut and shown%s (%s)"
                % (label, ", and at 125% text" if len(zooms) > 1 else "", "; ".join("%s %s" % (k, x and x["rows"]) for k, _, x in seen)),
                seen and not bad and len(seen) == 2 * len(zooms), bad or seen)
        # (b3) GUARD: the academy's own hint
        ctx, pg, errs = page(br, 375, 667, (20, 0, 0, 0), True, True, UA, cls="academy")
        cdp = ctx.new_cdp_session(pg)
        pg.evaluate("()=>{ const ids=QUESTIONS.map((q,i)=>i).filter(i=>!QUESTIONS[i].ifc && QUESTIONS[i].choices && QUESTIONS[i].choices.length===4).slice(0,3); cfg.source='all'; cfg.mode='drill'; cfg.units=[QUESTIONS[ids[0]].topic]; beginRun(ids); }")
        pg.wait_for_selector(".qpanel .choice", timeout=20000); pg.wait_for_timeout(900)
        for k in range(3):
            pg.evaluate("()=>{ const r=correctSlot(order[pos]); const w=[0,1,2,3].filter(s=>s!==r && !(window.__tried||[]).includes(s))[0]; (window.__tried=window.__tried||[]).push(w); choose(w); }")
            pg.wait_for_timeout(700)
        pg.evaluate("()=>{ const b=document.querySelector('.giveup button'); if(b) b.scrollIntoView({block:'center', behavior:'instant'}); }"); pg.wait_for_timeout(500)
        gv = pg.evaluate("""()=>{ const b=document.querySelector('.giveup button'); if(!b) return null; const r=b.getBoundingClientRect();
          return { h:r.height, lines:LINES(b).length, x:r.left+r.width/2, y:r.top+r.height/2, inView:r.top>=0 && r.bottom<=innerHeight, cls:window.NOVA_CLASS }; }""".replace("LINES", LINES))
        marked = None
        if gv:
            pg.wait_for_timeout(300); tap(cdp, gv["x"], gv["y"]); pg.wait_for_timeout(800)
            marked = pg.evaluate("()=>{ const r=correctSlot(order[pos]); const m=[...document.querySelectorAll('.qpanel .choice.hinted')]; return { n:m.length, right: m.length===1 && m[0].dataset.index===String(r) }; }")
        chk("(b3) GUARD the academy's own hint comes after three misses, on one line (%s; %spx tall - a text link, as on the build before), and a tap marks the right answer (%s)"
            % (gv and {k: gv[k] for k in ("lines", "cls")}, gv and round(gv["h"], 1), marked),
            gv and gv["cls"] != "ifc" and gv["lines"] == 1 and gv["inView"] and marked and marked["right"], [gv, marked])
        ALLERRS.extend(errs); ctx.close()
        br.close()

chk("(c) no page errors (%s)" % (ALLERRS[:3],), not ALLERRS, ALLERRS[:5])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
