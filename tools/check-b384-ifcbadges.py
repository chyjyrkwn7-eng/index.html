"""Build 384: Fire Code's badges, each its own.
Madison: "IFC badges, there's multiple duplicates badges, by that I mean, there's multiple of the exact same style/shape in the
case.." and "Ensure all the badges for ifc, they aren't duplicated and ensure the wording on the back of them is good to go."
Played in Chromium in the Fire Code class (class26e.activeclass = "ifc") and read off the page:
 (1) EVERY CHAPTER'S FRONT, as the case draws it (the struck token, the case slot's size at 2x): no two outlines alike - the
     edges of every pair's silhouettes (a 3px band along each) coincide by less than 80% (intersection over union; two badges
     cut from one outline coincide 100% whatever their colour, and the old build's 58 had pairs at 100%; the closest outlines
     here, the octagon and the coin, are under 60%) - and no two drawn the same (the pictures differ); the worst pairs are
     printed;
 (2) THE CASE ON PROFILE (Profile > Badges, every chapter found): a slot per chapter, each drawing its own chapter (its label)
     with an outline no other slot draws, in its own enamel;
 (3) EVERY BACK'S WORDS: its own chapter's title as the class's data has it (uppercased, nothing added, nothing reworded, no
     word left out) and FIRE CODE - nothing else: no "CLASS 26E", no academy word - and every word set inside the back's
     field (a back that could not fit used to come out as one row over the middle, across the rim, with no class line);
 (4) EVERY BACK FITS, ON AN IPHONE 17 PRO MAX (440x956 at 3x), AN IPHONE SE (375x667 at 2x) AND AN IPAD PRO 11" (834x1194
     at 2x): at the size the badge in your hand is drawn there (binspectW) and the badge case cutscene's coin, every inked pixel
     of every back's words is inside its field - clear of the rim - and its title is no smaller than the academy's smallest
     back at that size (within 3%); in your hand the badge and its words (the longest title's, Appendix H) are on the screen,
     the name not overflowing its line;
 (5) EVERY PLACE A FIRE CODE BADGE IS DRAWN shows the new design: Chapter 40 earned for real (its 8 questions at 100%, with
     Chapter 26 - its twin on the old build, the same steel shield - already found): the results' "Found & unlocked" row and
     the badge case cutscene's coin (read while they are up), and its unlock card (the results' badge item, played with
     playUnlockSpotlight when the walk shows none), each draw Chapter 40's outline and enamel as the case on Profile does,
     and none of them looks like Chapter 26's badge;
 (6) THE ACADEMY'S BADGES ARE AS THEY WERE: its 24 units' outlines, channels, colours, back plans and vector drawings hash to
     what build 384 had before this round (taken with --dump on 1dca98e);
 (7) no page errors in either class.
Run:  python3 tools/check-b384-ifcbadges.py   (--against OLD/index.html must FAIL; ONLY=1,3 runs those sections; --dump prints
the academy's hash)"""
import json, os, re, sys, time, functools, http.server, socket, threading
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
if not os.path.exists(CHROME):
    import glob as _g; CHROME = (sorted(_g.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")) or [CHROME])[-1]
BODY = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read() if "--against" in sys.argv else open(ROOT + "/index.html", encoding="utf-8").read()
DUMP = "--dump" in sys.argv
ONLY = set(os.environ.get("ONLY", "").split(",")) - {""}
def want(n): return not ONLY or str(n) in ONLY
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:700], flush=True)
def serve():
    so = socket.socket(); so.bind(("127.0.0.1", 0)); port = so.getsockname()[1]; so.close()
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, port
OWNER = "xph5b57jbp5a"   # the class owner's public id (the account that can open Fire Code today)
ALL_CHARS = ["detective", "masked", "zeus", "poseidon", "clown", "valkyrie", "marksman", "astronaut", "hacker", "timekeeper", "ronin", "hive",
             "voidwalker", "umbra", "singularity", "genesis", "lunar", "solar", "tempest", "frost", "oracle", "inferno", "astral", "celestial", "zenith"]
# an existing account (tours seen, Nova met, everything it holds announced), so nothing lands over what is measured
SEED = {"onboardingComplete": True, "firstName": "Maddog", "avatarChar": "ninja", "publicId": OWNER, "novaMet": 99,
        "tourRev": 99, "rankMapFx244": True, "seenProfileTour": True, "seenModeSelectTour": True, "seenUnitSelectTour": True,
        "seenMainMenuTour": True, "seenRankingsTour": True, "seenAppearanceTour": True, "novaHeard": {"@recap": 99991231},
        "lifetime": {"points": 9000, "answered": 900, "correct": 860, "drillPlays": 30, "examPlays": 4, "perfectTests": 30,
                     "longestStreak": 20, "currentStreak": 3},
        "unlocksShown": {"chars": ALL_CHARS, "banners": [], "fx": ["fireworks", "underwater", "bubbles", "ufo"]},
        "flareHintsShown": ["umbra", "singularity", "genesis"]}
SEEN = ["freshstart", "unithold.tip", "savecode.asked", "savecode.card", "getstarted", "penal55124.seen", "penal124256.seen", "penal256578.seen"]
def init_js(cls):
    s = "(()=>{ try{ if(sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.intro.seen','9');"
    for k in SEEN: s += "localStorage.setItem('class26e.%s','1');" % k
    s += "localStorage.setItem('class26e.drill.v1', %s);" % json.dumps(json.dumps(SEED))
    if cls == "ifc":
        s += "localStorage.setItem('class26e.activeclass','ifc'); localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done');"
        for k in SEEN: s += "localStorage.setItem('class26e.ifc.%s','1');" % k
        s += "localStorage.setItem('class26e.ifc.drill.v1', %s);" % json.dumps(json.dumps(SEED))
    return s + " }catch(e){} })()"
srv, port = serve()
def page(br, cls, w=440, h=956, dsf=1):
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=dsf, has_touch=True)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});")
    pg.add_init_script(init_js(cls))
    pg.route("**/index.html", lambda route, request: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(3500)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    return ctx, pg, errs
ACAD_WORDS = re.compile(r"\b(academy|police|officers?|cadets?|recruits?|patrol|tcole|penal code|class 26e|26e|law enforcement)\b", re.I)
# page helpers: a picture's silhouette and colour at S x S, and how alike two are
HELP = r"""(()=>{
  window.__pic = (url, S) => new Promise(res => { const im = new Image(); im.onload = () => { const c = document.createElement('canvas'); c.width = c.height = S;
    const g = c.getContext('2d'); g.drawImage(im, 0, 0, S, S); const d = g.getImageData(0, 0, S, S).data; const m = new Uint8Array(S * S), rgb = new Float32Array(S * S * 3);
    for(let i = 0; i < S * S; i++){ m[i] = d[i * 4 + 3] > 127 ? 1 : 0; rgb[i * 3] = d[i * 4]; rgb[i * 3 + 1] = d[i * 4 + 1]; rgb[i * 3 + 2] = d[i * 4 + 2]; }
    res({ m, rgb }); }; im.onerror = () => res(null); im.src = url; });
  /* the silhouette's edge as a 3px band: two outlines are one outline when their edges coincide */
  window.__edge = (a, S) => { const m = a.m, e = new Uint8Array(S * S), b = new Uint8Array(S * S);
    for(let y = 1; y < S - 1; y++) for(let x = 1; x < S - 1; x++){ const i = y * S + x; if(m[i] && (!m[i-1] || !m[i+1] || !m[i-S] || !m[i+S])) e[i] = 1; }
    for(let y = 1; y < S - 1; y++) for(let x = 1; x < S - 1; x++){ const i = y * S + x; if(e[i] || e[i-1] || e[i+1] || e[i-S] || e[i+S]) b[i] = 1; } return { m: b }; };
  window.__iou = (a, b) => { let i = 0, u = 0; for(let k = 0; k < a.m.length; k++){ const x = a.m[k], y = b.m[k]; if(x && y) i++; if(x || y) u++; } return u ? i / u : 1; };
  /* the pictures' difference: mean |RGB| over where either is drawn, 0-255 (and a silhouette that differs counts as 255 there) */
  window.__diff = (a, b) => { let s = 0, n = 0; for(let k = 0; k < a.m.length; k++){ if(!a.m[k] && !b.m[k]) continue; n++;
    if(a.m[k] !== b.m[k]){ s += 255; continue; } s += (Math.abs(a.rgb[k*3] - b.rgb[k*3]) + Math.abs(a.rgb[k*3+1] - b.rgb[k*3+1]) + Math.abs(a.rgb[k*3+2] - b.rgb[k*3+2])) / 3; } return n ? s / n : 0; };
  /* the outline an svg badge is drawn from: the path drawn most often in it (the slot, keyline, rim and plate are all rings of it) */
  window.__outline = sv => { const c = {}; sv.querySelectorAll('path').forEach(p => { const d = p.getAttribute('d'); if(d) c[d] = (c[d] || 0) + 1; });
    let best = null; Object.keys(c).forEach(d => { if(!best || c[d] > c[best]) best = d; }); return best; };
  window.__h = s => { let h = 2166136261; for(let i = 0; i < s.length; i++){ h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0).toString(16); };
  window.__chapters = () => [...new Set(QUESTIONS.map(q => (q.topic || '').trim()))].filter(Boolean);
})()"""
CH26, CH40 = "Chapter 26: Fumigation and Insecticidal Fogging", "Chapter 40: Storage of Distilled Spirits and Wines"
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME)
    fctx, F, ferr = page(br, "ifc", dsf=2)
    F.evaluate(HELP)
    chk("the page is the Fire Code class, with its 58 chapters", F.evaluate("()=>window.NOVA_CLASS") == "ifc" and F.evaluate("()=>__chapters().length") == 58,
        F.evaluate("()=>[window.NOVA_CLASS, __chapters().length]"))
    # ------------------------------------------------------------------ (1) every front, drawn
    if want(1):
        R1 = F.evaluate(r"""async () => { const us = unitsInTeachingOrder(), S = 104, P = [];
          for(const u of us){ const e = badgeStrikeEntry(u, false, S, false, 0); P.push(await __pic(e.url, S)); }
          const E = P.map(p => __edge(p, S));
          let worst = [0, '', '', 0], same = [], minDiff = [1e9, '', ''];
          for(let i = 0; i < us.length; i++) for(let j = i + 1; j < us.length; j++){
            const v = __iou(E[i], E[j]); if(v > worst[0]) worst = [+v.toFixed(3), us[i], us[j], +__iou(P[i], P[j]).toFixed(3)];
            if(v >= .8) same.push([us[i].slice(0, 12), us[j].slice(0, 12), +v.toFixed(3)]);
            const d = __diff(P[i], P[j]); if(d < minDiff[0]) minDiff = [+d.toFixed(1), us[i], us[j]]; }
          return { n: us.length, worst, same, minDiff }; }""")
        chk("(1) no two of Fire Code's %d badges share an outline: every pair's edges coincide under 80%% (closest: %s and %s, edges %s, areas %s); %d pairs at 80%% or more"
            % (R1["n"], R1["worst"][1][:24], R1["worst"][2][:24], R1["worst"][0], R1["worst"][3], len(R1["same"])), R1["n"] == 58 and not R1["same"], R1["same"][:12])
        chk("(1) no two are drawn alike: the most alike pair's pictures still differ by %s of 255 (%s and %s)" % (R1["minDiff"][0], R1["minDiff"][1][:24], R1["minDiff"][2][:24]),
            R1["minDiff"][0] > 40, R1["minDiff"])
    # ------------------------------------------------------------------ (2) the case on Profile
    if want(2):
        F.evaluate("()=>{ unitsInTeachingOrder().forEach(u => { store.unitPerfects[u] = Math.max(store.unitPerfects[u] || 0, badgeThresholdFor(u)); }); showRanksScreen('badges'); }")
        F.wait_for_timeout(3000)
        R2 = F.evaluate(r"""() => { const cells = [...document.querySelectorAll('#stage .badge-tile')];
          return { order: unitsInTeachingOrder(), cells: cells.map(c => { const sv = c.querySelector('svg.badge-art'), im = sv && sv.querySelector('image.badge-raster');
            return { label: c.getAttribute('aria-label') || '', d: sv ? __h(__outline(sv) || '') : null, en: im ? im.getAttribute('data-enamel') : null }; }) }; }""")
        cells = R2["cells"]
        named = all(c["label"].startswith(u + " Badge") for c, u in zip(cells, R2["order"]))
        chk("(2) the case on Profile has a slot for each of the %d chapters, in order, each found and named for its chapter" % len(cells),
            len(cells) == 58 and named and all(c["d"] and c["en"] for c in cells), [(c["label"][:30], c["d"], c["en"]) for c in cells][:4])
        outs = {}
        for c in cells: outs.setdefault(c["d"], []).append(c["label"][:14])
        dup = [v for v in outs.values() if len(v) > 1]
        chk("(2) every slot draws an outline no other slot draws (%d outlines for %d badges)" % (len(outs), len(cells)), len(outs) == len(cells) and not dup, dup[:6])
        pairs = {(c["d"], c["en"]) for c in cells}
        chk("(2) and no two slots are the same outline in the same enamel (%d looks)" % len(pairs), len(pairs) == len(cells), len(pairs))
    # ------------------------------------------------------------------ (3) the backs' words
    if want(3):
        R3 = F.evaluate(r"""() => { const R = BADGE_BACK_RELIEF;
          return unitsInTeachingOrder().map(u => { const p = badgeBackPlan(u), g = badgeStrikeGeometry(badgeShapeFor(u)), W = p.W, D = badgeBackField(g, W);
            const cv = document.createElement('canvas'); cv.width = cv.height = W; const c2 = cv.getContext('2d'); badgeBackDrawPlan(c2, p, W);
            const px = c2.getImageData(0, 0, W, W).data; let out = 0;
            for(let i = 0; i < W * W; i++) if(px[i * 4 + 3] > 25 && D[i] > -R.rimIn) out++;
            const rows = p.items.filter(i => i.s);
            return { u, mode: p.mode, text: p.mode === 'arc' ? rows.map(i => i.s).join('') : rows.map(i => i.s).join(' '), out, fs: p.fs / W }; }); }""")
        norm = lambda s: re.sub(r"\s*—\s*", "—", re.sub(r"\s+", " ", s)).strip()
        bad = []
        for r in R3:
            t, want_t = norm(r["text"]), norm(r["u"].upper())
            rest = t.replace(want_t, "", 1) if want_t in t else None
            if rest is None or norm(rest) != "FIRE CODE": bad.append((r["u"][:40], r["text"][:120]))
        chk("(3) every one of the %d backs says its own chapter's title, word for word as the class's data has it, and FIRE CODE - and nothing else" % len(R3),
            len(R3) == 58 and not bad, bad[:5])
        acad = [(r["u"][:30], r["text"][:80]) for r in R3 if ACAD_WORDS.search(r["text"])]
        chk("(3) no back says CLASS 26E or any academy word", not acad, acad[:4])
        spill = [(r["u"][:40], r["out"]) for r in R3 if r["out"]]
        chk("(3) every back's words are set inside its field, clear of the rim (none laid across it)", not spill, spill[:5])
    # ------------------------------------------------------------------ (4) the backs fit, on three devices
    if want(4):
        FIT = r"""(A) => { const R = BADGE_BACK_RELIEF, dpr = badgeDpr(), rem = parseFloat(getComputedStyle(document.documentElement).fontSize) || 16;
          const wide = !!(window.matchMedia && window.matchMedia('(min-width:40rem)').matches);
          const coinCss = wide ? Math.min(innerWidth * .36, 15.5 * rem, innerHeight * .34) : Math.min(innerWidth * .52, 14 * rem, innerHeight * .34);
          const sizes = { hand: binspectW(), coin: Math.min(864, badgeStrikeSize(coinCss * dpr)) };
          const us = A ? A : unitsInTeachingOrder(), res = { sizes, dpr, spill: [], minName: [1e9, ''] };
          us.forEach(u => { const g = badgeStrikeGeometry(badgeShapeFor(u)), p = badgeBackPlan(u);
            Object.keys(sizes).forEach(k => { const W = sizes[k], M = badgeBackLayout(u, g, W), D = badgeBackField(g, W); let out = 0;
              for(let i = 0; i < W * W; i++) if(M[i] > .1 && D[i] > -R.rimIn) out++;
              if(out) res.spill.push([u.slice(0, 30), k, W, out]); });
            const css = p.fs / p.W * sizes.hand / dpr; if(css < res.minName[0]) res.minName = [+css.toFixed(2), u]; });
          return res; }"""
        HAND = r"""async (u) => { const h = openBadgeInspect(u, null); await new Promise(r => setTimeout(r, 1600));
          const R = e => { const r = e.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.right), Math.round(r.bottom)]; };
          const f = document.querySelector('.binspect-float'), w = document.querySelector('.binspect-words'), nm = document.querySelector('.binspect-name');
          const o = { float: R(f), words: R(w), name: nm.textContent, over: nm.scrollWidth - nm.clientWidth, vw: innerWidth, vh: innerHeight };
          h.teardown(); await new Promise(r => setTimeout(r, 300)); return o; }"""
        LONG = "Appendix H: Hazardous Materials Management Plan (HMMP) and Hazardous Materials Inventory Statement (HMIS) Instructions"
        for (w, h, dsf, dev) in ((440, 956, 3, "iPhone 17 Pro Max"), (375, 667, 2, "iPhone SE"), (834, 1194, 2, "iPad Pro 11\"")):
            dctx, D4, derr = page(br, "ifc", w, h, dsf)
            actx, A4, aerr = page(br, "academy", w, h, dsf)
            D4.evaluate(HELP)
            D4.evaluate("()=>{ unitsInTeachingOrder().forEach(u => { store.unitPerfects[u] = Math.max(store.unitPerfects[u] || 0, badgeThresholdFor(u)); }); showRanksScreen('badges'); }")
            D4.wait_for_timeout(1500)
            rf, ra = D4.evaluate(FIT, None), A4.evaluate(FIT, None)
            chk("(4) %s: every back's words are inside its field at the size it is drawn in your hand (%dpx) and on the cutscene's coin (%dpx) - %s"
                % (dev, rf["sizes"]["hand"], rf["sizes"]["coin"], "nothing on the rim" if not rf["spill"] else "%d spill" % len(rf["spill"])), not rf["spill"], rf["spill"][:5])
            chk("(4) %s: the smallest title on a back is %.1fpx in your hand (%s), the academy's smallest %.1fpx - no smaller (within 3%%)"
                % (dev, rf["minName"][0], rf["minName"][1][:28], ra["minName"][0]), rf["minName"][0] >= ra["minName"][0] * .97, (rf["minName"], ra["minName"]))
            hd = D4.evaluate(HAND, LONG)
            inside = lambda r: r[0] >= 0 and r[1] >= 0 and r[2] <= hd["vw"] and r[3] <= hd["vh"]
            chk("(4) %s: in your hand, the longest title's badge %s and its words %s are on the screen, the name on its lines (overflow %dpx)"
                % (dev, hd["float"], hd["words"], hd["over"]), inside(hd["float"]) and inside(hd["words"]) and hd["over"] <= 1 and hd["name"].startswith(LONG), hd)
            ok_err = not derr and not aerr
            chk("(4) %s: no page errors" % dev, ok_err, derr + aerr)
            dctx.close(); actx.close()
    # ------------------------------------------------------------------ (5) a chapter earned for real: results, cutscene, card
    if want(5):
        SETUP = r"""(a) => { store.unitPerfects = {}; store.unitPerfects[a.twin] = badgeThresholdFor(a.twin);
          ['Chapter 2: Definitions', 'Chapter 3: General Requirements'].forEach(t => { store.unitPerfects[t] = badgeThresholdFor(t); });
          store.lifetime.perfectTests = 30; saveStore(); showHome();
          cfg.source = 'all'; cfg.mode = 'drill'; cfg.units = [a.topic];
          setTimeout(() => beginRun(QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === a.topic)), 1200);
          window.__seen = { row: null, coin: null, card: null }; return true; }"""
        ANSWER = r"""()=>{ if(!document.querySelector('.choice') || typeof order === 'undefined' || !order.length) return 'wait';
          const key = order.length + ':' + pos;
          if(window.__answered !== key){ if(performance.now() - (window.__nextAt || 0) < 700) return 'wait'; const c = document.querySelector('.choice[data-index="' + correctSlot(order[pos]) + '"]'); if(!c) return 'wait'; c.click(); window.__answered = key; window.__answeredAt = performance.now(); return 'answered'; }
          const n = document.getElementById('nextbtn'); if(n && !n.hidden && performance.now() - window.__answeredAt > 400){ n.click(); window.__nextAt = performance.now(); return 'next'; } return 'wait'; }"""
        # what each place draws for the chapter, read while it is up (a card is tapped away once read)
        WATCH = r"""() => { const S = window.__seen;
          const row = document.querySelector('.rs-unlock.badgebanner svg.badge-art');
          if(row && !S.row){ const im = row.querySelector('image.badge-raster'); S.row = { d: __h(__outline(row) || ''), en: im && im.getAttribute('data-enamel'), name: (row.closest('.rs-unlock').querySelector('.unlockbanner-name') || {}).textContent }; }
          const coin = document.querySelector('.bc-scene .bc-face.is-front .bc-face-art');
          if(coin && !S.coin && coin.complete && coin.naturalWidth){ S.coin = { src: coin.src, name: (document.querySelector('.bc-scene .bc-name') || {}).textContent || '' }; }
          const card = document.querySelector('.rs-spot.rs-spot-badge');
          if(card && !S.card){ const sv = card.querySelector('svg.badge-art'), im = sv && sv.querySelector('image.badge-raster'); S.card = { d: sv ? __h(__outline(sv) || '') : null, en: im && im.getAttribute('data-enamel'), text: card.textContent.replace(/\s+/g, ' ').trim() }; }
          const up = document.querySelector('.rs-spot.is-up'); if(up){ if(!up.__t0) up.__t0 = performance.now(); if(performance.now() - up.__t0 > 2200) up.click(); }
          const sc = document.querySelector('.bc-scene'); if(sc && S.coin){ if(!sc.__t0) sc.__t0 = performance.now(); if(performance.now() - sc.__t0 > 2500) sc.click(); }
          return { row: !!S.row, coin: !!S.coin, card: !!S.card, results: !!document.querySelector('.rs-screen'), done: !!document.querySelector('.rs-rewards.rs-done') }; }"""
        F.evaluate(SETUP, {"topic": CH40, "twin": CH26})
        t0, st, fin = time.time(), "answer", None
        while time.time() - t0 < 200:
            try:
                if st == "answer":
                    if F.evaluate("()=>!!document.querySelector('.rs-screen')"): st = "results"
                    else: F.evaluate(ANSWER)
                else:
                    w5 = F.evaluate(WATCH)
                    if w5["done"] and w5["row"] and w5["coin"]:
                        if fin is None: fin = time.time()
                        if time.time() - fin > 2.5: break
            except Exception as ex:
                print("   (walk at %s: %s)" % (st, str(ex)[:120]))
            F.wait_for_timeout(200)
        seen = F.evaluate("()=>window.__seen")
        # the references: the case on Profile's own drawing of each chapter, and their struck pictures
        REF = r"""async (a) => { const out = {}; for(const u of [a.topic, a.twin]){ const sv = buildUnitBadgeSVG(u, true, {}), im = sv.querySelector('image.badge-raster');
            out[u] = { d: __h(__outline(sv) || ''), en: im && im.getAttribute('data-enamel') }; }
          const S = 96, coin = a.coin ? await __pic(a.coin, S) : null, mine = await __pic(badgeStrikeEntry(a.topic, false, S * 2, false, 0).url, S), twin = await __pic(badgeStrikeEntry(a.twin, false, S * 2, false, 0).url, S);
          out.coin = coin ? { mine: +__iou(coin, mine).toFixed(3), twin: +__iou(coin, twin).toFixed(3), dTwin: +__diff(coin, twin).toFixed(1) } : null;
          out.twins = { iou: +__iou(mine, twin).toFixed(3), diff: +__diff(mine, twin).toFixed(1) }; return out; }"""
        ref = F.evaluate(REF, {"topic": CH40, "twin": CH26, "coin": (seen.get("coin") or {}).get("src")})
        me, tw = ref[CH40], ref[CH26]
        chk("(5) Chapter 40 earned at 100%%: the walk reached the results with its badge's row and its badge case cutscene (%s)" % {k: bool(v) for k, v in seen.items()},
            seen.get("row") and seen.get("coin"), seen)
        r = seen.get("row") or {}
        chk("(5) the results' Found & unlocked row draws Chapter 40's badge as the case does (outline %s, enamel %s) - not Chapter 26's (%s, %s)"
            % (r.get("d"), r.get("en"), tw["d"], tw["en"]), r.get("d") == me["d"] and r.get("en") == me["en"] and (r.get("d"), r.get("en")) != (tw["d"], tw["en"]), (r, me, tw))
        c = ref.get("coin") or {}
        chk("(5) the badge case cutscene's coin is Chapter 40's (its silhouette %.3f its own, %.3f Chapter 26's; the pictures differ by %s of 255)"
            % (c.get("mine", 0), c.get("twin", 0), c.get("dTwin")), c and c["mine"] >= .9 and c["twin"] < .95 and c["dTwin"] > 40, c)
        card = seen.get("card")
        if card is None:   # the unlock card the results use for a badge (playUnlockSpotlight), played on its own
            F.evaluate("""(u)=>{ window.__seen.card = null; playUnlockSpotlight({ kind: 'badge', unit: u, kicker: 'Badge found', name: badgeTitle(u), sub: 'Unit mastered', color: '#D8E2EC',
              art: () => buildUnitBadgeSVG(u, true, { fine: true }) }, 1, 1, () => {}); }""", CH40)
            for _ in range(20):
                F.wait_for_timeout(200)
                if F.evaluate("()=>{ const c = document.querySelector('.rs-spot.rs-spot-badge'); if(!c) return false; const sv = c.querySelector('svg.badge-art'), im = sv && sv.querySelector('image.badge-raster'); window.__seen.card = { d: sv ? __h(__outline(sv) || '') : null, en: im && im.getAttribute('data-enamel'), text: c.textContent.replace(/\\s+/g, ' ').trim() }; return true; }"): break
            F.wait_for_timeout(2600); F.evaluate("()=>document.querySelector('.rs-spot.is-up')?.click()"); F.wait_for_timeout(1200)
            card = F.evaluate("()=>window.__seen.card")
        card = card or {}
        chk("(5) its unlock card draws Chapter 40's badge as the case does, not Chapter 26's (%s, %s)" % (card.get("d"), card.get("en")),
            card.get("d") == me["d"] and card.get("en") == me["en"] and (card.get("d"), card.get("en")) != (tw["d"], tw["en"]), (card, me, tw))
        chk("(5) Chapters 26 and 40 - the same steel shield before - look nothing alike now (silhouettes %.3f alike, pictures %s of 255 apart)"
            % (ref["twins"]["iou"], ref["twins"]["diff"]), ref["twins"]["iou"] < .95 and ref["twins"]["diff"] > 40, ref["twins"])
    # ------------------------------------------------------------------ (6) the academy's badges, as they were
    if want(6):
        actx, A, aerr = page(br, "academy")
        A.evaluate(HELP)
        ACAD = r"""() => { const us = unitsInTeachingOrder(); const rows = us.map(u => { const s = badgeShapeFor(u), p = badgeBackPlan(u);
            const sv = buildUnitBadgeSVG(u, true, { slot: false, fine: true, vector: true }); const ser = new XMLSerializer().serializeToString(sv).replace(/bdg\d+/g, 'U');
            return [u, s.d, (s.cuts || []).join('|'), badgeThemeFor(u).p, p.mode, p.rows, p.items.map(i => i.rule ? 'R' + i.rule.map(v => v.toFixed(2)).join(',') : i.s + '@' + i.x.toFixed(2) + ',' + i.y.toFixed(2) + ',' + i.fs.toFixed(2)).join(';'), __h(ser)]; });
          return { n: us.length, h: __h(JSON.stringify(rows)), cls: window.NOVA_CLASS }; }"""
        ra = A.evaluate(ACAD)
        PIN = "8996cbb2"   # 1dca98e (build 384 before this round), --dump
        if DUMP: print("DUMP academy badges", ra)
        chk("(6) the academy's %d badges - outlines, channels, colours, back plans, drawings - are exactly as they were (%s)" % (ra["n"], ra["h"]),
            ra["cls"] == "academy" and ra["n"] == 24 and ra["h"] == PIN, ra)
        chk("(7) the academy page: no page errors", not aerr, aerr)
        actx.close()
    chk("(7) the Fire Code page: no page errors", not ferr, ferr)
    br.close()
print("\nALL PASS" if ok else "\nSOME CHECKS FAILED")
sys.exit(0 if ok else 1)
