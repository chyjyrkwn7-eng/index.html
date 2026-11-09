#!/usr/bin/env python3
"""Build 384 r8: the unit card - a status strip, the title, the foot - and the units screen's line under its title.

Madison, the unit picker's "NEXT TEST / Nov 9" marks circled: "The way and the position it says next test could be better,
secondly, how could the titles look better within the boxes for the phone? Seems a little cramped for a lot of them in the top
left corners? ... I'm almost wondering if the '15 questions' should be centered at the bottom". Then, the band under the
Virtual Room's "Pick the units" circled: "Bad spacing where I circled.. should it say select your units for your virtual room
match or something there? Idk".

On an iPhone 17 Pro Max (440x956), an iPhone SE (375x667) and an iPad Pro 11" (834x1194), academy and Fire Code, on the
Virtual Room's units screen (and the ordinary picker on the academy), with a fixture where every third unit is on the next
test and every card picked (Select all) for the selected-state legs. Everything is read off the page.
 (1) TITLE FIT: every title inside its card (no sideways overflow, clear of the count), no word broken across two lines
     (a Range over each word has one line), and room round it: at least 14px in from the card's left and top edges;
 (2) SAME LAYOUT WITH OR WITHOUT A TAG: in each row a tagged card's title top is the untagged cards' (1px), and nothing but
     the title lies between the strip and the count - the tag is never wedged under the title;
 (3) TAG PLACEMENT: every tag on the screen at the same offset in its card (1px) and on one line;
 (4) COUNT ALIGNMENT: every count in a row on one baseline (1px), flush with the title's left edge (the chosen alignment:
     the badge holds the bottom-right, so the count holds the bottom-left);
 (5) CARDS: one height per row (1px);
 (6) SELECTED: a picked card's background differs from an unpicked one's, its dot is shown inside the card and covers no
     word of the title;
 (7) TAP TARGETS: every card, the search field and Select all at least 44px tall;
 (8) THE LINE UNDER THE TITLE: no caption on the screen repeats the title in capitals; a line sits under the title, centred
     on it, one line on a phone, and in Fire Code it says chapters, never units; the grid starts at least 14px below the
     search row (Virtual Room, phone and tablet);
 (9) no page errors.
(5), (7) and (9) guard what worked before (they pass on the previous build too); every other leg fails on it.
  python3 tools/check-b384-unitcards.py [--against OLD/index.html]"""
import io, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
from playwright.sync_api import sync_playwright
if "--against" in sys.argv:
    OLD = io.open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
    def _patched(ins, OLD=OLD):
        v = {"top": "%dpx" % ins[0], "right": "%dpx" % ins[1], "bottom": "%dpx" % ins[2], "left": "%dpx" % ins[3]}
        return g["INSET_RE"].sub(lambda m: v[m.group(1)], OLD)
    g["patched"] = _patched
srv, url = g["serve"]()
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  -> " + str(info)[:400]), flush=True)

def page(br, w, h, ifc=False):
    phone = w < 600
    ins = (62, 0, 34, 0) if phone else (24, 0, 20, 0)
    kw = dict(viewport={"width": w, "height": h}, device_scale_factor=2)
    if phone: kw.update(user_agent=UA, has_touch=True, is_mobile=True)
    ctx = br.new_context(**kw)
    ctx.add_init_script(g["STANDALONE"])
    ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]()))
    d = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]())); d["novaMet"] = 99
    if ifc: d["publicId"] = "xph5b57jbp5a"
    pre = "class26e.ifc." if ifc else "class26e."
    ctx.add_init_script("""(()=>{ if(localStorage.getItem('%sdrill.v1')) return; const d=%s;
      localStorage.setItem('class26e.drill.v1', JSON.stringify(d)); %s
      ['freshstart','intro.seen','unithold.tip','daily.seen','savecode.asked','getstarted','penal256578.seen','penal55124.seen','penal124256.seen'].forEach(k=>localStorage.setItem('%s'+k,'1'));
      localStorage.setItem('%ssynccode','TEST-0384'); localStorage.setItem('%sframe.ok','go-live-1'); localStorage.setItem('class26e.savecode.card','1'); })()""" % (
        pre, json.dumps(d), ("localStorage.setItem('class26e.ifc.drill.v1', JSON.stringify(d)); localStorage.setItem('class26e.activeclass','ifc');" if ifc else ""), pre, pre, pre))
    ctx.add_init_script("addEventListener('DOMContentLoaded',()=>{const s=document.createElement('style');s.textContent='.daily-alert{display:none!important}';document.head.appendChild(s);});")
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    body = g["patched"](ins)
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.goto(url); pg.wait_for_timeout(3500)
    pg.evaluate("document.getElementById('splashscreen')?.remove()")
    pg.evaluate("""()=>{ try{ const p=pendingHomeUnlocks(); markUnlocksShown(p.chars,p.banners,p.fx); }catch(e){}
      try{ homeUnlocksOwed=()=>false; }catch(e){} store.seenUnitSelectTour=true; store.seenUnitOptionsTour=true; showHome(); }""")
    pg.wait_for_timeout(1200)
    # THE FIXTURE'S NEXT TEST: every third unit in teaching order, a week out - so most rows mix a tagged card and an untagged one
    pg.evaluate("""()=>{ const u = unitsInTeachingOrder(); const v = { date:'2026-11-16', when:'Nov 16', units:new Set(u.filter((x,i)=>i%3===1)) };
      window.nextTestUnits = () => v; window.nextTestUnitsNow = () => v; }""")
    return ctx, pg, errs

CLEAR = """()=>{ document.querySelectorAll('.rs-spot-card').forEach(e=>{ let n=e; while(n.parentElement && n.parentElement!==document.body) n=n.parentElement;
  if(n!==document.getElementById('stage')) n.remove(); }); }"""
MEASURE = """()=>{
  const R = e => { const b = e.getBoundingClientRect(); return { l:b.left, t:b.top, r:b.right, b:b.bottom, w:b.width, h:b.height }; };
  const cards = [...document.querySelectorAll('.picks > label.pick')].filter(c => !c.hidden && c.offsetParent !== null && !c.classList.contains('is-other-level'));
  const out = cards.map(c => {
    const nm = c.querySelector('.pname'), tag = c.querySelector('.pick-nexttest'), cnt = c.querySelector('.pcount'), box = c.querySelector('.box');
    const text = nm.textContent;
    const broken = [], wordRects = [];
    /* a word: a run with no space and no em or en dash in it (a line may break at a dash between two words, never inside
       "Hard-of-Hearing"); every text node, so a word kept whole in a span of its own is read too */
    const tw = document.createTreeWalker(nm, NodeFilter.SHOW_TEXT); let tn;
    while((tn = tw.nextNode())){
      const re = /[^\\s\\u2014\\u2013]+/g; let m; const tx = tn.textContent;
      while((m = re.exec(tx))){
        const rg = document.createRange(); rg.setStart(tn, m.index); rg.setEnd(tn, m.index + m[0].length);
        const rs = [...rg.getClientRects()].filter(x => x.width > 0.5);
        const tops = new Set(rs.map(x => Math.round(x.top)));
        if(tops.size > 1) broken.push(m[0]);
        rs.forEach(x => wordRects.push({ l:x.left, t:x.top, r:x.right, b:x.bottom }));
      }
    }
    const tcs = tag ? getComputedStyle(tag) : null;
    const tagLH = tag ? (parseFloat(tcs.lineHeight) || parseFloat(tcs.fontSize) * 1.25) : 0;
    const bs = box ? getComputedStyle(box) : null;
    return { name: text, card: R(c), title: R(nm), sw: nm.scrollWidth, cw: nm.clientWidth, broken, wordRects,
      tag: tag ? R(tag) : null, tagLH, count: R(cnt), countCs: { ff: getComputedStyle(cnt).fontSize },
      picked: c.classList.contains('pick-checked'), bg: getComputedStyle(c).backgroundImage + '|' + getComputedStyle(c).backgroundColor,
      box: box ? Object.assign(R(box), { op: parseFloat(bs.opacity), vis: bs.visibility, disp: bs.display }) : null };
  });
  const panel = document.querySelector('#stage > .panel');
  const nav = panel.querySelector(':scope > .settings-nav');
  const title = nav ? nav.querySelector('h1') : null;
  const kids = [...panel.querySelectorAll('*')].filter(e => (!nav || !nav.contains(e)) && e.offsetParent !== null && e.childElementCount === 0 && e.textContent.trim());
  const firstAfter = [...panel.children].filter(e => e !== nav && e.offsetParent !== null && e.getBoundingClientRect().height > 0)[0];
  const lineUnder = firstAfter && firstAfter.tagName === 'P' ? { text: firstAfter.textContent.trim(), r: R(firstAfter), ta: getComputedStyle(firstAfter).textAlign,
    lh: parseFloat(getComputedStyle(firstAfter).lineHeight) || parseFloat(getComputedStyle(firstAfter).fontSize) * 1.3 } : (firstAfter ? { tag: firstAfter.tagName, cls: firstAfter.className, text: firstAfter.textContent.trim().slice(0, 40) } : null);
  const caps = kids.filter(e => { const t = e.textContent.trim(); const tt = getComputedStyle(e).textTransform; return t.length <= 24 && (tt === 'uppercase' || (t === t.toUpperCase() && /[A-Z]/.test(t))); })
    .map(e => e.textContent.trim());
  const tools = panel.querySelector('.setup-tools'), search = panel.querySelector('.setup-tools .searchbox'), selall = panel.querySelector('.selall-btn');
  const grid = panel.querySelector('.picks');
  return { cards: out, title: title ? { text: title.textContent.trim(), r: R(title) } : null, lineUnder, caps,
    tools: tools ? R(tools) : null, search: search ? R(search) : null, selall: selall ? R(selall) : null, grid: grid ? R(grid) : null,
    vw: innerWidth, sw: document.documentElement.scrollWidth };
}"""

def rows(cards):
    out = {}
    for c in cards: out.setdefault(round(c["card"]["t"]), []).append(c)
    return [v for k, v in sorted(out.items())]

def inter(a, b, pad=0):
    return a["l"] < b["r"] + pad and b["l"] < a["r"] + pad and a["t"] < b["b"] + pad and b["t"] < a["b"] + pad

def card_legs(lab, m, errs):
    cards = m["cards"]
    if not cards: chk("%s: the grid has cards" % lab, False, m); return
    # (1)
    bad = []
    for c in cards:
        cr, t, n = c["card"], c["title"], c["count"]
        if t["r"] > cr["r"] + 0.5 or t["l"] < cr["l"] - 0.5 or c["sw"] > c["cw"] + 1 or t["b"] > n["t"] + 0.5: bad.append((c["name"][:30], "overflow", round(t["b"]), round(n["t"])))
        if c["broken"]: bad.append((c["name"][:30], "word broken", c["broken"]))
        if t["l"] - cr["l"] < 14 - 0.5 or t["t"] - cr["t"] < 14 - 0.5: bad.append((c["name"][:30], "inset", round(t["l"] - cr["l"], 1), round(t["t"] - cr["t"], 1)))
    chk("(1) %s: every title fits its card, breaks no word, and sits >=14px in from the left and top (%d cards)" % (lab, len(cards)), not bad, bad[:4])
    # (2)
    bad = []; mixed = 0
    for row in rows(cards):
        tagged = [c for c in row if c["tag"]]; plain = [c for c in row if not c["tag"]]
        if tagged and plain:
            mixed += 1
            ref = plain[0]["title"]["t"] - plain[0]["card"]["t"]
            for c in tagged:
                d = c["title"]["t"] - c["card"]["t"]
                if abs(d - ref) > 1: bad.append((c["name"][:24], "title top", round(d, 1), round(ref, 1)))
        for c in tagged:
            if c["tag"]["b"] > c["title"]["t"] + 0.5 and c["tag"]["t"] < c["count"]["t"]: bad.append((c["name"][:24], "tag between title and count", round(c["tag"]["t"] - c["card"]["t"]), round(c["title"]["b"] - c["card"]["t"])))
    chk("(2) %s: a tagged card's title is where an untagged one's is, and nothing but the title lies above the count (%d mixed rows)" % (lab, mixed), mixed > 0 and not bad, bad[:4] or "no mixed row")
    # (3)
    tags = [c for c in cards if c["tag"]]
    offs = [(round(c["tag"]["l"] - c["card"]["l"], 1), round(c["tag"]["t"] - c["card"]["t"], 1)) for c in tags]
    spread = (max(o[0] for o in offs) - min(o[0] for o in offs), max(o[1] for o in offs) - min(o[1] for o in offs)) if offs else (0, 0)
    multi = [(c["name"][:24], round(c["tag"]["h"], 1), round(c["tagLH"], 1)) for c in tags if c["tag"]["h"] > c["tagLH"] * 1.5]
    chk("(3) %s: every tag at one offset in its card (spread %.1f / %.1f px) and on one line (%d tags)" % (lab, spread[0], spread[1], len(tags)), tags and spread[0] <= 1 and spread[1] <= 1 and not multi, {"offsets": sorted(set(offs))[:6], "multi": multi[:3]})
    # (4)
    bad = []
    for row in rows(cards):
        bs = [c["count"]["b"] for c in row]
        if max(bs) - min(bs) > 1: bad.append(("baseline", [c["name"][:14] for c in row], [round(b - row[0]["card"]["t"]) for b in bs]))
        for c in row:
            if abs(c["count"]["l"] - c["title"]["l"]) > 1: bad.append(("not flush with the title", c["name"][:20], round(c["count"]["l"] - c["title"]["l"], 1)))
    chk("(4) %s: every count in a row on one baseline, flush with the title's left edge" % lab, not bad, bad[:4])
    # (5)
    bad = [[round(c["card"]["h"], 1) for c in row] for row in rows(cards) if max(c["card"]["h"] for c in row) - min(c["card"]["h"] for c in row) > 1]
    chk("(5) %s: one card height per row" % lab, not bad, bad[:3])
    # (7)
    small = [("card", c["name"][:20], round(c["card"]["h"])) for c in cards if c["card"]["h"] < 44]
    for k in ("search", "selall"):
        if m[k] and m[k]["h"] < 44 - 0.5: small.append((k, round(m[k]["h"], 1)))
    chk("(7) %s: every card, the search field and Select all are at least 44px tall" % lab, not small, small[:4])
    chk("(9) %s: no page errors" % lab, not errs, errs[:3])

def selected_leg(lab, m, unpicked_bg):
    bad = []
    picked = [c for c in m["cards"] if c["picked"]]
    for c in picked:
        b = c["box"]
        if not b or b["op"] < 0.9 or b["vis"] == "hidden" or b["disp"] == "none" or b["w"] < 6: bad.append((c["name"][:20], "dot not shown", b)); continue
        if b["l"] < c["card"]["l"] - 0.5 or b["r"] > c["card"]["r"] + 0.5 or b["t"] < c["card"]["t"] - 0.5: bad.append((c["name"][:20], "dot outside the card"))
        hits = [w for w in c["wordRects"] if inter(b, w, 1)]
        if hits: bad.append((c["name"][:20], "dot on the title's words", round(b["l"]), round(b["t"]), [(round(w["l"]), round(w["t"]), round(w["r"])) for w in hits][:2]))
        if c["bg"] == unpicked_bg: bad.append((c["name"][:20], "same background as an unpicked card"))
    chk("(6) %s: a picked card reads as picked - a background of its own, its dot inside the card and on no word (%d picked)" % (lab, len(picked)), picked and not bad, bad[:4])

def subtitle_legs(lab, m, ifc, phone, vroom):
    caps = [t for t in m["caps"] if m["title"] and t.lower() in m["title"]["text"].lower()]
    chk("(8a) %s: no caption repeats the title in capitals (%s)" % (lab, caps), not caps, caps)
    lu, t = m["lineUnder"], m["title"]
    good = bool(lu and "r" in lu and t and len(lu["text"]) > 12 and lu["ta"] in ("center", "-webkit-center")
                and abs((lu["r"]["l"] + lu["r"]["r"]) / 2 - (t["r"]["l"] + t["r"]["r"]) / 2) <= 2 and 0 <= lu["r"]["t"] - t["r"]["b"] <= 48)
    one = bool(lu and "r" in lu and (not phone or lu["r"]["h"] <= lu["lh"] * 1.5))
    words = bool(lu and "text" in lu and (not ifc or ("chapter" in lu["text"].lower() and not re.search(r"\bunits?\b", lu["text"], re.I))))
    chk("(8b) %s: a line under the title, centred on it%s%s" % (lab, ", on one line" if phone else "", ", saying chapters" if ifc else ""), good and one and words, lu)
    if vroom:
        gap = (m["grid"]["t"] - m["tools"]["b"]) if (m["grid"] and m["tools"]) else -1
        chk("(8c) %s: the grid starts >=14px below the search row (%.1f px)" % (lab, gap), gap >= 14, gap)

DEVICES = (("iPhone 17 Pro Max", 440, 956, True), ("iPhone SE", 375, 667, True), ("iPad Pro 11in", 834, 1194, False))
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    for dev, w, h, phone in DEVICES:
        for ifc in (False, True):
            lab = "%s, %s, Virtual Room" % (dev, "Fire Code" if ifc else "academy")
            ctx, pg, errs = page(br, w, h, ifc=ifc)
            pg.evaluate("()=>{ window.vroomDb = window.vroomDb || (()=>({})); cfg.mode='vroom'; showVirtualRoomSetup(); }")
            pg.wait_for_timeout(1500); pg.evaluate(CLEAR)
            m = pg.evaluate(MEASURE)
            card_legs(lab, m, errs)
            subtitle_legs(lab, m, ifc, phone, True)
            unpicked_bg = m["cards"][0]["bg"] if m["cards"] else None
            pg.evaluate("()=>{ document.querySelector('#stage .selall-btn').click(); }"); pg.wait_for_timeout(900)
            selected_leg(lab, pg.evaluate(MEASURE), unpicked_bg)
            chk("(9) %s: no page errors after Select all" % lab, not errs, errs[:3])
            ctx.close()
        lab = "%s, academy, the ordinary picker" % dev
        ctx, pg, errs = page(br, w, h)
        pg.evaluate("()=>{ cfg.mode='drill'; cfg.units=[]; showSetup(); }"); pg.wait_for_timeout(1500); pg.evaluate(CLEAR)
        m = pg.evaluate(MEASURE)
        card_legs(lab, m, errs)
        subtitle_legs(lab, m, False, phone, False)
        ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILURES"); sys.exit(0 if ok else 1)
