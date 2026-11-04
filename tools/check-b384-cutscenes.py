"""Build 384: every cutscene, unlock and celebration, in both classes, ready for go-live.
Madison: "ensure all the cutscenes for the ifc version have been updated. Ensure all the unlock banners and everything else for
that version is good to go. We are gonna go live with the fire code and add class button tomorrow. Ensure all the cutscenes and
everything for the police academy are good to go as well too."
Played in Chromium on the iPhone 17 Pro Max (440x956) - the Police Academy (academy) and Fire Code (ifc) side by side, one page
each - and read off the page (the words every scene and card puts up, sampled while it plays; what is left on the page after):
 (1) THE CARDS: every unlock card's words (each character, banner, hundo effect, theme, rank flare, the rank's reward card, each
     secret flare's find and hint card, a badge) - Fire Code's carry no academy word (police, academy, Class 26E ... and no name
     that is only the academy's: Void, Sheriff, Zenith, Fireworks ...), the academy's no Fire Code word; Fire Code's hundo effect
     cards ask for its own counts (HUNDO_FX: 25 / 50 / 75 / 150, the academy 50 / 100 / 150 / 200) under its own names, and no
     effect anywhere is the Fire Alarm; each class's rank cards ask its own badge counts (TIER_UNLOCKS: Fire Code's from its
     chapters); a character's, a banner's and an effect's card, played, show the class's own art (Fire Code's differs from the
     academy's) and leave nothing behind when tapped away; the Thermal Camera stopped part way (a card tapped away) moves no piece
     to the corner of the screen;
 (2) THE SECRET FLARE SCENES: the Void scene's title is the character's own name in each class (BREACHER in Fire Code, VOID in the
     academy), the Genesis scene's lines never say GENESIS in Fire Code (its character is the Flashbang), and the other three are
     titled with the class's names; each leaves nothing on the page;
 (3) THE BADGE CASE: Fire Code's case says "Nova - Fire Code" and "Badge Case" (never "Class 26E" or the academy's "Level 1"),
     every badge's back says FIRE CODE and none CLASS 26E; the academy's is as it was; the longest chapter's name sits under the
     open case (not over its latches) and above the bottom, on a phone and an iPad;
 (4) THE RANK-UP AND SUPERNOVA: each titles its rank, plays its sounds (every sound a scene plays is in the catalogue, Fire Code's
     hundo sounds its own), clears its pending flag and leaves nothing (no layer, no cutscene focus; the tab bar and chat button
     back);
 (5) FIRE CODE'S GREETING (enrolling): Nova names no other class, says the class's own differences - a chapter's badge for one
     100%, the hundo effects at 25, 50, 75 and 150 (read off HUNDO_FX) - and promises no tour that never comes; the "enrolled"
     banner follows; it plays once (a relaunch does not play it again);
 (6) A SECRET FLARE FOUND, PLAYED ON HOME: the scene, its card ("... of Breacher's 3" in Fire Code), its character and banner,
     the next secret - in that order, the class's names - and a relaunch plays none of it again;
 (7) WHAT'S NEW, the academy's news (its new units, the Calendar tab, the Sheriff), does not show in Fire Code; it still does in
     the academy;
 (8) NOVA'S WORDS: beaten in a Virtual Room he hands over the class's own character (the Chief in Fire Code), his answers name it
     too, and in Fire Code he sends nobody to a Calendar tab; Customize's ultimate note names the class's own top character;
 (9) THE WHOLE EARN, WALKED: the last answer of a chapter / unit at 100% - the results (grade, XP, the badge's case, the hundo
     effect's card), Main menu, the Profile tab's call, the rank-up journey (the road map, the cutscene, the reward card) and
     Nova's words over the flare - each class's own words throughout, and nothing left on the page at the end;
(10) no page errors in either class.
Run:  python3 tools/check-b384-cutscenes.py   (--against OLD/index.html must FAIL; ONLY=1,3,5 runs those sections)"""
import json, os, re, sys, time, functools, http.server, socket, threading
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
if not os.path.exists(CHROME):   # the sandbox's browser moved once (1194 -> 1243): take whichever is installed
    import glob as _g; CHROME = (sorted(_g.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")) or [CHROME])[-1]
BODY = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read() if "--against" in sys.argv else open(ROOT + "/index.html", encoding="utf-8").read()
ONLY = set(os.environ.get("ONLY", "").split(",")) - {""}
def want(n): return not ONLY or str(n) in ONLY
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:600], flush=True)
def serve():
    so = socket.socket(); so.bind(("127.0.0.1", 0)); port = so.getsockname()[1]; so.close()
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, port
OWNER = "xph5b57jbp5a"   # the class owner's public id (the only account that can open another class today)
ALL_CHARS = ["detective", "masked", "zeus", "poseidon", "clown", "valkyrie", "marksman", "astronaut", "hacker", "timekeeper", "ronin", "hive",
             "voidwalker", "umbra", "singularity", "genesis", "lunar", "solar", "tempest", "frost", "oracle", "inferno", "astral", "celestial", "zenith"]
ALL_BANNERS = ["tests100", "tests250", "tests500", "hundos100", "hundos250", "vr50", "study50", "study60", "correct5000", "correct10000", "level80",
               "early10", "exam100", "adept_rank", "elite_rank", "titan_rank", "flare_void", "flare_umbra", "flare_horizon", "flare_genesis",
               "astral", "celestial", "zenith"]
# an existing account (its tours seen, Nova met, everything it holds already announced) - the moments are played on purpose
SEED = {"onboardingComplete": True, "firstName": "Maddog", "avatarChar": "ninja", "publicId": OWNER, "novaMet": 99,
        "tourRev": 99, "rankMapFx244": True, "seenProfileTour": True, "seenModeSelectTour": True, "seenUnitSelectTour": True,
        "seenMainMenuTour": True, "seenRankingsTour": True, "seenAppearanceTour": True, "novaHeard": {"@recap": 99991231},
        "lifetime": {"points": 41000, "answered": 2100, "correct": 1980, "drillPlays": 60, "examPlays": 12, "perfectTests": 64,
                     "longestStreak": 44, "currentStreak": 12},
        "unitPerfects": {"Professionalism and Ethics": 35, "TCOLE Rules": 35, "Penal Code": 35, "Racial Profiling": 35, "Victims of Crime": 35},
        "unlocksShown": {"chars": ALL_CHARS, "banners": ALL_BANNERS, "fx": ["fireworks", "underwater", "bubbles", "ufo"]},
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
# sampled while a moment plays: the words of everything put on the page since it started; then what it left behind; and
# every sound asked for
CAP = r"""(()=>{
  const TOP_SKIP = /^(SCRIPT|STYLE|LINK|TEMPLATE)$/;
  const wrap = () => { if(window.__sndWrapped || typeof window.playSound !== 'function') return; window.__sndWrapped = true;
    const orig = window.playSound; window.__snd = []; window.playSound = function(id){ try{ window.__snd.push(String(id)); }catch(e){} return orig.apply(this, arguments); }; };
  const textOf = el => { const out = []; const tw = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); let n;
    while((n = tw.nextNode())){ const p = n.parentElement; if(p && p.closest('.nt-text')) continue; const v = n.nodeValue.replace(/\s+/g, ' ').trim(); if(v) out.push(v); }
    el.querySelectorAll && el.querySelectorAll('.nt-text').forEach(t => { const v = t.textContent.replace(/\s+/g, ' ').trim(); if(v) out.push(v); });
    return out; };
  window.__capStart = function(){ wrap(); window.__snd = [];
    const C = window.__cap = { base: new Set([...document.body.children]), bodyCls: new Set(document.body.classList), texts: new Set() };
    clearInterval(window.__capT); window.__capT = setInterval(window.__capSample, 100); return true; };
  window.__capSample = function(){ const C = window.__cap; if(!C) return;
    [...document.body.children].forEach(el => { if(C.base.has(el) || TOP_SKIP.test(el.tagName)) return; textOf(el).forEach(t => C.texts.add(t)); });
    const st = document.getElementById('stage');
    if(st) st.querySelectorAll('.rs-spot, .rs-screen, .rankmap, .rank-journey, .ru-card, .ranklore').forEach(el => textOf(el).forEach(t => C.texts.add(t))); };
  window.__capEnd = function(){ const C = window.__cap; clearInterval(window.__capT); window.__capSample();
    const vis = el => { const r = el.getBoundingClientRect(), cs = getComputedStyle(el); return r.width > 0 && r.height > 0 && r.right > 0 && r.bottom > 0 && r.left < innerWidth && r.top < innerHeight && cs.display !== 'none' && cs.visibility !== 'hidden' && +cs.opacity > .02; };
    const left = [...document.body.children].filter(el => !C.base.has(el) && !TOP_SKIP.test(el.tagName) && vis(el)).map(el => (el.id ? '#' + el.id + ' ' : '') + String(el.className).slice(0, 60));
    const shown = el => { if(!el) return false; const r = el.getBoundingClientRect(), cs = getComputedStyle(el); return r.width > 0 && r.top >= -1 && r.bottom <= innerHeight + 1 && cs.visibility !== 'hidden' && +cs.opacity > .5 && cs.display !== 'none'; };
    return { texts: [...C.texts], left, bodyAdd: [...document.body.classList].filter(c => !C.bodyCls.has(c) && c !== 'has-bottomtabs'),
      focus: ['cutscene-focus', 'bc-covering', 'rankup-lock'].filter(c => document.body.classList.contains(c)),
      tab: shown(document.getElementById('bottomtabs')), chat: shown(document.getElementById('chatdock-btn')), snd: (window.__snd || []).slice() }; };
})()"""
srv, port = serve()
def page(br, cls, w=440, h=956):
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=1, has_touch=True)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});")
    pg.add_init_script(init_js(cls))
    pg.add_init_script(CAP)
    pg.route("**/index.html", lambda route, request: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(3500)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    return ctx, pg, errs
ACAD_WORDS = re.compile(r"\b(academy|police|officers?|cadets?|recruits?|patrol|tcole|penal code|class 26e|26e|law enforcement)\b", re.I)
FIRE_WORDS = re.compile(r"\b(chapters?|fire code|ifc|harris county)\b", re.I)
NAMES = r"""()=>({ chars: Object.fromEntries(AVATAR_CHARACTERS.filter(c=>!c.retired).map(c=>[c.id, AVATAR_DISPLAY_NAME[c.id] || c.id])),
  banners: Object.fromEntries(BANNERS.map(b=>[b.id, b.name])), fx: Object.fromEntries(HUNDO_FX.map(d=>[d.id, d.name])) })"""
def word_rx(names):
    names = sorted({n for n in names if n and len(n) > 2}, key=len, reverse=True)
    return re.compile(r"(?<![\w’'])(" + "|".join(re.escape(n) for n in names) + r")(?![\w])", re.I) if names else None
def leaks(texts, rx_words, rx_names, allow=()):
    bad = []
    for t in texts:
        u = t
        for a in allow: u = re.sub(re.escape(a), "", u, flags=re.I)
        m = rx_words.search(u) or (rx_names.search(u) if rx_names else None)
        if m: bad.append((m.group(0), t[:90]))
    return bad
def drive(pages, secs, step=None, every=0.25):
    end = time.time() + secs
    while time.time() < end:
        for p in pages:
            if step:
                try: p.evaluate(step)
                except Exception: pass
        pages[0].wait_for_timeout(int(every * 1000))
TAP_CARD = """()=>{ const s = document.querySelector('.rs-spot.is-up'); if(!s) return; if(!s.__t0) s.__t0 = performance.now(); if(performance.now() - s.__t0 > 2600) s.click(); }"""
TALK = """(id)=>{ const el = document.getElementById(id); if(!el || !el.__nova) return 'none'; const n = el.__nova;
  if(n.typing){ n.advance(); return 'typing'; } if(n.index < n.count - 1){ n.advance(); return 'next'; } const g = el.querySelector('.nt-go'); if(g) g.click(); return 'go'; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME)
    actx, A, aerr = page(br, "academy")
    fctx, F, ferr = page(br, "ifc")
    P = {"academy": A, "ifc": F}
    cls_ok = A.evaluate("()=>window.NOVA_CLASS") == "academy" and F.evaluate("()=>window.NOVA_CLASS") == "ifc"
    chk("the two pages are the two classes (academy, Fire Code)", cls_ok)
    NA, NF = A.evaluate(NAMES), F.evaluate(NAMES)
    acad_only = [NA[k][i] for k in NA for i in NA[k] if NF[k].get(i) != NA[k][i]]
    fire_only = [NF[k][i] for k in NF for i in NF[k] if NA[k].get(i) != NF[k][i]]
    # names that are ordinary words too, left out of the academy's list: a card there could say them as words
    fire_only = [n for n in fire_only if n not in ("Exit", "Dispatch", "Chief", "Thermal", "Strobe", "Recon", "Nebula", "Sprinklers")]
    # "Summit" is also the road map's word for its top, in both classes (rankmap-summit), not only the academy banner's name
    acad_only = [n for n in acad_only if n not in ("Summit",)]
    RXA = word_rx(acad_only); RXF = word_rx(fire_only)
    ALLOW_F = ("Event Horizon",)   # the fifth secret flare's own name, in both classes
    def fire_leaks(texts): return leaks(texts, ACAD_WORDS, RXA, ALLOW_F)
    def acad_leaks(texts): return leaks(texts, FIRE_WORDS, RXF)
    # ---------------------------------------------------------------- (1) the cards
    if want(1):
        CARDS = r"""()=>{ const out = []; const add = (tag, it) => { if(it) out.push([tag, [it.kicker, it.name, it.sub, it.need].filter(Boolean).join(' | ')]); };
          AVATAR_CHARACTERS.filter(c => !c.retired && (c.feat || c.unlock)).forEach(c => add('char:' + c.id, characterUnlockItem(c.id)));
          BANNERS.forEach(b => add('banner:' + b.id, bannerUnlockItem(b.id)));
          HUNDO_FX.forEach(d => add('fx:' + d.id, hundoFxUnlockItem(d.id)));
          TIER_ORDER_FULL.forEach(k => { add('theme:' + k, themeUnlockItem(k)); add('flare:' + k, flareUnlockItem(k)); const r = rankRewardsItem(k, rankRewardParts(k)); add('rank:' + k, r); r.parts.forEach(p => add('rank:' + k + ':' + p.kind, p)); });
          ['red','orange','yellow','violet','white','core'].forEach(c => add('find:' + c, flareFoundItem(c, c === 'yellow')));
          ['umbra','singularity','genesis'].forEach(h => add('hint:' + h, flareHintItem(h)));
          const u = [...new Set(QUESTIONS.map(q => q.topic))][1]; add('badge', { kicker: 'Badge found', name: badgeTitle(u), sub: chapterFix ? chapterFix('Unit mastered') : 'Unit mastered' });
          const fx = HUNDO_FX.filter(d => d.need > 0).map(d => ({ id: d.id, name: d.name, need: d.need, said: hundoFxUnlockItem(d.id).need }));
          const chapters = [...new Set(QUESTIONS.map(q => (q.topic || '').trim()))].filter(Boolean).length;
          const ranks = TIER_ORDER_FULL.map(k => ({ k, label: TIER_UNLOCKS[k].label, level: TIER_UNLOCKS[k].level, badges: TIER_UNLOCKS[k].badges,
            acad: (TIER_UNLOCKS_ACADEMY[k] || {}).badges }));
          return { cards: out, fx, ranks, chapters }; }"""
        CA, CF = A.evaluate(CARDS), F.evaluate(CARDS)
        bad = fire_leaks([t for _, t in CF["cards"]])
        chk("(1) Fire Code: no card (%d of them) says an academy word or a name only the academy has (%s)" % (len(CF["cards"]), bad[:4]), not bad, bad)
        bad = acad_leaks([t for _, t in CA["cards"]])
        chk("(1) academy: no card (%d) says a Fire Code word or name (%s)" % (len(CA["cards"]), bad[:4]), not bad, bad)
        fx = CF["fx"]
        chk("(1) Fire Code's hundo effect cards ask for its own counts, %s" % [(d["name"], d["said"]) for d in fx],
            [d["need"] for d in fx] == [25, 50, 75, 150] and all(d["said"] == "Earn %d hundos" % d["need"] for d in fx)
            and [d["name"] for d in fx] == ["Extinguisher", "Sprinklers", "Thermal Camera", "Hazmat"], fx)
        chk("(1) the academy's ask for its own, %s" % [(d["name"], d["said"]) for d in CA["fx"]],
            [d["need"] for d in CA["fx"]] == [50, 100, 150, 200] and all(d["said"] == "Earn %d hundos" % d["need"] for d in CA["fx"]), CA["fx"])
        alarm = [t for _, t in CF["cards"] + CA["cards"] if re.search(r"fire alarm", t, re.I)]
        chk("(1) no card in either class is the Fire Alarm (Hazmat is the 150, the Thermal Camera the 75)", not alarm, alarm)
        want_b = [max(1, round(r["acad"] / 14 * (CF["chapters"] - 2))) for r in CF["ranks"]]
        chk("(1) Fire Code's rank cards ask its own badge counts, from its %d chapters (%s)" % (CF["chapters"], [r["label"] for r in CF["ranks"]]),
            [r["badges"] for r in CF["ranks"]] == want_b and all(r["label"] == "Reach level %d and %d badge%s" % (r["level"], r["badges"], "" if r["badges"] == 1 else "s") for r in CF["ranks"]), CF["ranks"])
        # the cards, played: the class's own art, and nothing left once tapped away
        PLAY = r"""async (kind) => {
          const it = kind === 'char' ? characterUnlockItem('detective') : kind === 'banner' ? bannerUnlockItem('tests100') : hundoFxUnlockItem('bubbles');
          __capStart(); playUnlockSpotlight(it, 1, 1, () => {}); await new Promise(r => setTimeout(r, 2600));
          const s = document.querySelector('.rs-spot'); const art = s && s.querySelector('.rs-spot-art');
          const svg = art && (art.querySelector('svg.avatarchar-svg') || art.querySelector('.rs-spot-bannerart svg') || art.querySelector('svg'));
          const hash = x => { let h = 2166136261; for(let i = 0; i < x.length; i++){ h ^= x.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0).toString(16); };
          /* the drawing's geometry (every path's d, in order): classes, ids and live state do not change it */
          const geo = el => el ? [...el.querySelectorAll('path')].map(p => p.getAttribute('d') || '').join('|') : '';
          const ser = geo(svg);
          const name = s && s.querySelector('.rs-spot-name') ? s.querySelector('.rs-spot-name').textContent : null;
          /* the same art built again off the card: a drawing is stable, so a difference between the classes is a different drawing */
          const again = kind === 'char' ? buildAvatarCharSVGSafe('detective') : kind === 'banner' ? buildBannerArt('tests100').querySelector('svg') : null;
          const ser2 = geo(again);
          const fc = !!(svg && svg.querySelector('[class*="cx-fc-"]'));
          const fxStage = art && art.querySelector('.hfx-stage'); const build = kind === 'fx' ? (HUNDO_FX_BUILD.bubbles || {}).name : null;
          if(s) s.click();
          /* the tab bar and chat button slide back as the card goes (cutscene-return): up to 6s for it */
          const back = () => { const t = document.getElementById('bottomtabs'), c = document.getElementById('chatdock-btn');
            return t && c && t.getBoundingClientRect().bottom <= innerHeight + 1 && c.getBoundingClientRect().top >= 0 && !document.body.classList.contains('cutscene-return'); };
          for(let i = 0; i < 60 && !(i > 6 && back()); i++) await new Promise(r => setTimeout(r, 100));
          return { name, hash: ser ? hash(ser) : null, again: ser2 ? hash(ser2) : null, fc, n: ser.length, fx: fxStage ? fxStage.dataset.fx : null, build, end: __capEnd() }; }"""
        for kind, label in (("char", "a character"), ("banner", "a banner"), ("fx", "a hundo effect")):
            ra, rf = A.evaluate(PLAY, kind), F.evaluate(PLAY, kind)
            if kind == "fx": art_ok = rf["build"] == "ifxThermal" and ra["build"] != "ifxThermal" and rf["fx"] == "bubbles"
            else: art_ok = rf["hash"] and rf["hash"] == rf["again"] and ra["hash"] == ra["again"] and rf["hash"] != ra["hash"] and (kind != "char" or (rf["fc"] and not ra["fc"]))
            chk("(1) %s's card in Fire Code (%s) shows Fire Code's art, not the academy's (%s) [%s / %s]" % (label, rf["name"], ra["name"], rf["hash"] or rf["build"], ra["hash"] or ra["build"]), art_ok, (rf, ra))
            for c, r in (("academy", ra), ("Fire Code", rf)):
                e = r["end"]
                chk("(1) %s, %s's card tapped away leaves nothing: no layer %s, no focus %s, the tab bar and chat button back" % (c, label, e["left"], e["focus"]),
                    not e["left"] and not e["focus"] and e["tab"] and e["chat"] and "res.unlock.banner" in e["snd"], e)
        JUMP = r"""async (a) => {
          const card = document.createElement('div'); card.className = 'rs-card rs-grade is-perfect __probe';
          card.style.cssText = 'position:fixed;left:30px;top:170px;width:380px;height:185px';
          const pct = document.createElement('span'); pct.className = 'rs-pct pct perfect'; pct.style.cssText = 'position:absolute;left:24px;top:44px;font-size:67px;line-height:.95';
          gradePctMarkup(pct, 100); card.appendChild(pct); document.body.appendChild(card);
          let h, st = null;
          if(a.box){ st = buildHundoFxStage(a.id, { big: true }); st.classList.add('__probe'); st.style.cssText = 'position:fixed;left:20px;top:420px;width:400px'; document.body.appendChild(st);
            h = playHundoFx(a.id, { box: st, pct: st.querySelector('.hfx-stage-pct'), boxOnly: true }); }
          else h = playHundoFx(a.id, { box: card, pct, preview: true });
          await new Promise(r => setTimeout(r, a.at));
          const roots = [h.screen, h.box].filter(Boolean), leaves = [];
          roots.forEach(r => r.querySelectorAll('*').forEach(e => { if(!e.children.length) leaves.push(e); }));
          const eff = el => { let o = 1; for(let e = el; e && roots.indexOf(e) < 0; e = e.parentElement) o *= +getComputedStyle(e).opacity; return o; };
          const snap = () => leaves.map(e => { const r = e.getBoundingClientRect(); return { o: eff(e), x: r.left, y: r.top, w: r.width }; });
          const before = snap(); h.stop(); const after = snap();
          const bad = after.filter((q, i) => q.o > .05 && q.w > 0 && (before[i].o < .05 || Math.abs(q.x - before[i].x) > 4 || Math.abs(q.y - before[i].y) > 4)).map(q => [Math.round(q.x), Math.round(q.y)]);
          await new Promise(r => setTimeout(r, 800)); card.remove(); if(st) st.remove();
          return bad; }"""
        jumps = []
        for fid in ("fireworks", "underwater", "bubbles", "ufo"):
            for box in (False, True):
                for at in (1400, 3000):
                    b = F.evaluate(JUMP, {"id": fid, "box": box, "at": at})
                    if b: jumps.append((fid, "box" if box else "screen", at, b[:3]))
        chk("(1) Fire Code's effects stopped part way (a card tapped away, the screen changing) move no piece: none goes to the corner (%s)" % jumps[:3], not jumps, jumps)
    # ---------------------------------------------------------------- (2) the secret flare scenes
    if want(2):
        def flare(color, all_, found):
            js = "(a)=>{ store.mysteryColorsFound = {}; a.found.forEach(k => store.mysteryColorsFound[k] = true); showHome(); setTimeout(() => { __capStart(); playFlareFoundScene(a.c, a.all, () => {}); }, 900); }"
            for p in (A, F): p.evaluate(js, {"c": color, "all": all_, "found": found})
        ORDER = ["red", "orange", "yellow", "violet", "white", "core"]
        R = {}
        for color, all_ in (("yellow", True), ("core", False)):
            flare(color, all_, ORDER[:ORDER.index(color) + 1])
            drive([A, F], 38, TAP_CARD)   # the scene (~28s), then what Home owes after it (the next secret's card), tapped through
            R[color] = {c: P[c].evaluate("()=>__capEnd()") for c in P}
        void_a, void_f = R["yellow"]["academy"], R["yellow"]["ifc"]
        who_f = F.evaluate("()=>AVATAR_DISPLAY_NAME.voidwalker.toUpperCase()")
        chk("(2) Fire Code's Void scene is titled with its character's own name, %s (not VOID): %s" % (who_f, [t for t in void_f["texts"] if t.isupper() and len(t) > 3][-3:]),
            who_f in void_f["texts"] and "VOID" not in void_f["texts"] and who_f != "VOID", void_f["texts"])
        chk("(2) the academy's is still VOID", "VOID" in void_a["texts"], void_a["texts"])
        gen_f, gen_a = R["core"]["ifc"], R["core"]["academy"]
        chk("(2) Fire Code's sixth flare scene never says GENESIS (its character is the %s): %s" % (F.evaluate("()=>AVATAR_DISPLAY_NAME.genesis"), [t for t in gen_f["texts"] if t.isupper() and len(t) > 3]),
            not any("GENESIS" in t for t in gen_f["texts"]) and F.evaluate("()=>AVATAR_DISPLAY_NAME.genesis.toUpperCase()") in gen_f["texts"], gen_f["texts"])
        chk("(2) the academy's still does", any("GENESIS" in t for t in gen_a["texts"]), gen_a["texts"])
        for c, label in (("academy", "academy"), ("ifc", "Fire Code")):
            for color in ("yellow", "core"):
                e = R[color][c]
                bad = fire_leaks(e["texts"]) if c == "ifc" else acad_leaks(e["texts"])
                chk("(2) %s, the %s scene: the class's own words (%s), its sound, nothing left after (%s %s)" % (label, color, bad[:2], e["left"], e["focus"]),
                    not bad and not e["left"] and not e["focus"] and any(s.startswith("flare.scene.") for s in e["snd"]) and e["tab"], e)
        # the other three, as reduce motion plays them (their last frame and title at once)
        STILL = r"""async (c) => { theme.reduceMotion = true; document.documentElement.dataset.reduceMotion = 'true';
          const order = ['red','orange','yellow','violet','white','core']; store.mysteryColorsFound = {}; order.slice(0, order.indexOf(c) + 1).forEach(k => store.mysteryColorsFound[k] = true);
          __capStart(); playFlareFoundScene(c, false, () => {}); await new Promise(r => setTimeout(r, 2600));
          const e = __capEnd(); document.querySelectorAll('.sf-scene').forEach(x => x.click()); await new Promise(r => setTimeout(r, 1500));
          theme.reduceMotion = false; delete document.documentElement.dataset.reduceMotion; e.after = [...document.querySelectorAll('.sf-scene')].length; return e; }"""
        for color, ch in (("red", None), ("violet", "umbra"), ("white", "singularity")):
            for c, p in P.items():
                e = p.evaluate(STILL, color)
                p.evaluate("()=>{ store.mysteryColorsFound = {}; saveStore(); }")
                who = p.evaluate("(ch)=>ch ? AVATAR_DISPLAY_NAME[ch].toUpperCase() : null", ch)
                bad = fire_leaks(e["texts"]) if c == "ifc" else acad_leaks(e["texts"])
                chk("(2) %s, the %s scene (still): titled %s, the class's own words (%s), gone after" % (c, color, who or "SECRET FLARE FOUND", bad[:2]),
                    (who in e["texts"] if who else "SECRET FLARE FOUND" in e["texts"]) and not bad and e["after"] == 0, e)
    # ---------------------------------------------------------------- (3) the badge case
    if want(3):
        LONG = r"""()=>[...new Set(QUESTIONS.map(q => (q.topic || '').trim()))].filter(Boolean).sort((a, b) => b.length - a.length)[0]"""
        CASE = r"""async (u) => { showHome(); await new Promise(r => setTimeout(r, 900)); __capStart();
          let done = false; playBadgeCaseScene([u], () => { done = true; });
          let words = null;
          for(let i = 0; i < 260 && !done; i++){ await new Promise(r => setTimeout(r, 100));
            const w = document.querySelector('.bc-scene .bc-words.bc-words-in');
            if(w && !words && i > 30){ await new Promise(r => setTimeout(r, 700));
              const sc = document.querySelector('.bc-scene'), o = sc.getBoundingClientRect(), pb = parseFloat(getComputedStyle(sc).paddingBottom) || 0;
              const low = Math.max(...[...sc.querySelectorAll('.bc-handle, .bc-front')].map(e => e.getBoundingClientRect()).filter(r => r.width > 0 && r.top < o.bottom).map(r => r.bottom));
              const wr = w.getBoundingClientRect(), nr = w.querySelector('.bc-name').getBoundingClientRect();
              words = { top: Math.round(wr.top), low: Math.round(low), bottom: Math.round(wr.bottom), floor: Math.round(o.bottom - pb), name: w.querySelector('.bc-name').textContent.length };
              sc.click(); } }
          /* the scene hands over through its bridge, which lets go ~1.9s on and fades */
          await new Promise(r => setTimeout(r, 3800));
          const e = __capEnd(); e.words = words; return e; }"""
        for (w, h, dev) in ((440, 956, "phone"), (834, 1194, "iPad")):
            if dev == "iPad":
                for p in (A, F): p.set_viewport_size({"width": w, "height": h})
                A.wait_for_timeout(800)
            u = {c: p.evaluate(LONG) for c, p in P.items()}
            ra = A.evaluate(CASE, u["academy"]) if dev == "phone" else None
            rf = F.evaluate(CASE, u["ifc"])
            wf = rf["words"]
            chk("(3) %s, Fire Code's longest chapter (%d letters) is named under the open case (its front and handle), and above the bottom (%s)" % (dev, len(u["ifc"]), wf),
                wf and wf["top"] >= wf["low"] - 1 and wf["bottom"] <= wf["floor"] + 1, wf)
            if dev == "phone":
                chk("(3) Fire Code's badge case says \"Nova · Fire Code\" and \"Badge Case\", never Class 26E or the academy's Level 1 (%s)" % [t for t in rf["texts"] if re.search(r"case|nova", t, re.I)][:4],
                    "Nova · Fire Code" in rf["texts"] and not any(re.search(r"26E|Level 1", t, re.I) for t in rf["texts"]) and any(t.upper() == "BADGE CASE" for t in rf["texts"]), rf["texts"])
                chk("(3) the academy's is as it was (Nova · Class 26E, Level 1 Badge Case)", "Nova · Class 26E" in ra["texts"] and "Level 1 Badge Case" in ra["texts"], ra["texts"])
                for c, r in (("academy", ra), ("Fire Code", rf)):
                    bad = fire_leaks(r["texts"]) if c == "Fire Code" else acad_leaks(r["texts"])
                    chk("(3) %s's case: its sounds, its own words (%s), nothing left after (%s %s)" % (c, bad[:2], r["left"], r["focus"]),
                        not bad and not r["left"] and not r["focus"] and "cs.badge" in r["snd"] and "bc.rise" in r["snd"] and r["tab"], r)
            if dev == "iPad":
                for p in (A, F): p.set_viewport_size({"width": 440, "height": 956})
                A.wait_for_timeout(800)
        BACKS = r"""()=>{ const ts = [...new Set(QUESTIONS.map(q => (q.topic || '').trim()))].filter(Boolean); const all = [];
          ts.slice(0, 14).forEach(u => { try{ badgeBackPlan(u).items.forEach(i => { if(i.s) all.push(i.s); }); }catch(e){ all.push('ERR ' + e); } });
          return all.join(' ').replace(/(\w) (?=\w )/g, '$1'); }"""
        bf, ba = F.evaluate(BACKS), A.evaluate(BACKS)
        chk("(3) Fire Code's badge backs say FIRE CODE, none CLASS 26E", "FIRE CODE" in bf and "26E" not in bf and "ERR" not in bf, bf[:300])
        chk("(3) the academy's still say CLASS 26E", "CLASS 26E" in ba and "FIRE CODE" not in ba, ba[:300])
    # ---------------------------------------------------------------- (4) rank-up and Supernova
    if want(4):
        SEED_RANK = r"""(k)=>{ const rule = TIER_UNLOCKS[k] || {}; const topics = [...new Set(QUESTIONS.map(q => (q.topic||'').trim()))].filter(Boolean);
          store.unitPerfects = {}; topics.slice(0, rule.badges || 0).forEach(t => { store.unitPerfects[t] = badgeThresholdFor(t); });
          let pts = 500; while(levelProgress(pts).level < (rule.level || 0)) pts += 250; store.lifetime.points = pts;
          store.seenUnlockedTiers = TIER_ORDER_FULL.slice(0, TIER_ORDER_FULL.indexOf(k) + 1); store.rankUpShown = TIER_ORDER_FULL.indexOf(k) + 1;
          saveStore(); showHome(); }"""
        for key, call, secs, title in (("veteran", "()=>{ __capStart(); store.pendingTierCutscene='veteran'; playTierCutscene('veteran'); }", 31, "GOLD"),
                                       ("titan", "()=>{ __capStart(); store.pendingSupernovaCutscene=true; playSupernovaCutscene(); }", 39, "SUPERNOVA")):
            for p in (A, F): p.evaluate(SEED_RANK, key)
            A.wait_for_timeout(1500)
            for p in (A, F): p.evaluate(call)
            drive([A, F], secs, TAP_CARD)
            A.wait_for_timeout(2500)
            for c, p in P.items():
                e = p.evaluate("()=>__capEnd()")
                pend = p.evaluate("()=>[store.pendingTierCutscene || null, !!store.pendingSupernovaCutscene]")
                rs = [s for s in e["snd"] if s.startswith("rank.")]
                bad = fire_leaks(e["texts"]) if c == "ifc" else acad_leaks(e["texts"])
                chk("(4) %s, the %s scene: titled %s, its sounds (%d rank.*), its own words (%s), pending cleared %s, nothing left (%s %s), the tab bar and chat back" % (c, key, title, len(rs), bad[:2], pend, e["left"], e["focus"]),
                    title in e["texts"] and len(rs) >= 3 and not bad and pend[0] is None and not e["left"] and not e["focus"] and e["tab"] and e["chat"], e)
        SOUNDS = r"""()=>{ const ids = ['rank.attn','rank.whirl','rank.bang','rank.windup','rank.flash','rank.title','rank.supernova','rank.road.fill','rank.unlock.pop','rank.card',
            'cs.badge','bc.rise','badge.case.open','badge.drop','res.unlock.banner','res.found.badge','res.found.flare','res.found.character','res.levelup',
            'flare.scene.small','flare.scene.void','flare.scene.umbra','flare.scene.horizon','flare.scene.genesis','nova.arrive','ob.whatsnew',
            'hundo.confetti','hundo.fireworks','hundo.underwater','hundo.bubbles','hundo.ufo','vr.end','vr.podium'];
          const missing = ids.filter(i => !(SOUND_CATALOGUE[i] && typeof SOUND_CATALOGUE[i].fn === 'function'));
          const own = typeof SND_IFX === 'undefined' ? [] : Object.keys(SND_IFX).filter(i => window.NOVA_CLASS === 'ifc' ? SOUND_CATALOGUE[i].fn !== SND_IFX[i].fn : SOUND_CATALOGUE[i].fn === SND_IFX[i].fn);
          return { missing, own }; }"""
        for c, p in P.items():
            s = p.evaluate(SOUNDS)
            chk("(4) %s: every sound a cutscene plays is in the catalogue (%s missing) and the hundo effects play the class's own (%s wrong)" % (c, s["missing"], s["own"]), not s["missing"] and not s["own"], s)
    # ---------------------------------------------------------------- (5) Fire Code's greeting
    if want(5):
        F.evaluate("()=>{ localStorage.setItem('class26e.greet.ifc','pending'); __capStart(); showHome(); }")
        t0 = time.time(); talk = []
        while time.time() - t0 < 50:
            F.wait_for_timeout(700)
            st = F.evaluate(TALK, "nova-class-greet")
            if st == "go" or (st == "none" and talk): break
            talk.append(st)
        F.wait_for_timeout(9500)   # the enrolled banner comes up ~1.2s after he goes and stays 6s
        e = F.evaluate("()=>__capEnd()")
        lines = [t for t in e["texts"] if len(t) > 12]
        needs = F.evaluate("()=>HUNDO_FX.filter(d => d.need > 0).map(d => d.need)")
        said = " ".join(e["texts"])
        counts = ", ".join(str(n) for n in needs[:-1]) + " and " + str(needs[-1])
        bad = fire_leaks(e["texts"])
        chk("(5) Nova's Fire Code greeting names no other class's words (%s)" % bad[:3], not bad and not re.search(r"academy|police", said, re.I), lines)
        chk("(5) it says the class's own differences: a chapter's badge for one 100%%, the hundo effects at %s (HUNDO_FX)" % counts,
            re.search(r"chapter has a badge.*100% on it once", said) and ("at " + counts + " hundos") in said, lines)
        chk("(5) and promises no tour that never comes (no \"point them out as we go\")", not re.search(r"point them out", said, re.I), lines)
        chk("(5) the enrolled banner follows (%s), with its sound, and nothing is left (%s)" % ([t for t in e["texts"] if "enrolled" in t.lower()], e["left"]),
            any("You’re enrolled in Fire Code" in t for t in e["texts"]) and "nova.arrive" in e["snd"] and not e["left"], e)
        st = F.evaluate("()=>localStorage.getItem('class26e.greet.ifc')")
        F.reload(); F.wait_for_timeout(5000)
        again = F.evaluate("()=>!!document.getElementById('nova-class-greet')")
        chk("(5) it plays once: marked done (%s), and a relaunch does not play it again" % st, st == "done" and not again, (st, again))
        A.evaluate("()=>{ __capStart(); showHome(); showEnrolledBanner('academy'); }"); A.wait_for_timeout(2200)
        e = A.evaluate("()=>__capEnd()")
        chk("(5) the academy's enrolled banner says the academy (%s)" % [t for t in e["texts"] if "enrolled" in t.lower()], any("enrolled in Police Academy" in t for t in e["texts"]), e["texts"])
    # ---------------------------------------------------------------- (6) a secret flare found, played on Home
    if want(6):
        FIND = r"""()=>{ store.mysteryColorsFound = { red: true, orange: true, yellow: true };
          store.unlocksShown.chars = store.unlocksShown.chars.filter(x => x !== 'voidwalker'); store.unlocksShown.banners = store.unlocksShown.banners.filter(x => x !== 'flare_void');
          store.flareHintsShown = (store.flareHintsShown || []).filter(x => x !== 'umbra'); oweFlareFind('yellow', true); saveStore(); __capStart(); showHome(); }"""
        for p in (A, F): p.evaluate(FIND)
        drive([A, F], 56, TAP_CARD, every=.4)
        R6 = {c: p.evaluate("()=>__capEnd()") for c, p in P.items()}
        for c, p in P.items():
            e = R6[c]; who = p.evaluate("()=>AVATAR_DISPLAY_NAME.voidwalker"); ban = p.evaluate("()=>bannerDef('flare_void').name")
            hint = p.evaluate("()=>AVATAR_DISPLAY_NAME.umbra")
            seq = [t for t in e["texts"] if t in (who.upper(), "Secret flare found", "Character unlocked", "Banner unlocked", "A new secret")]
            order = []
            for t in seq:
                if t not in order: order.append(t)
            bad = fire_leaks(e["texts"]) if c == "ifc" else acad_leaks(e["texts"])
            chk("(6) %s: the scene, then its card (%s), the character, its banner (%s), the next secret (%s) - in that order, the class's words (%s)" %
                (c, [t for t in e["texts"] if "’s 3" in t], ban, hint + " is out there", bad[:2]),
                order == [who.upper(), "Secret flare found", "Character unlocked", "Banner unlocked", "A new secret"] and any(("of " + who + "’s 3") in t for t in e["texts"])
                and ban in e["texts"] and (hint + " is out there") in e["texts"] and not bad and not e["left"] and not e["focus"], (order, e))
        for p in (A, F): p.reload()
        A.wait_for_timeout(4000); F.wait_for_timeout(500)
        for p in (A, F): p.evaluate("()=>__capStart()")
        A.wait_for_timeout(7000)
        for c, p in P.items():
            e = p.evaluate("()=>__capEnd()")
            again = [t for t in e["texts"] if t in ("Secret flare found", "Character unlocked", "Banner unlocked", "A new secret") or "SECRET FLARE" in t]
            chk("(6) %s: a relaunch plays none of it again (%s)" % (c, again), not again, e["texts"])
    # ---------------------------------------------------------------- (7) What's New
    if want(7):
        W = "()=>{ try{ localStorage.removeItem(INTRO_KEY); }catch(e){} showHome(); setTimeout(maybeShowIntro, 300); }"
        for p in (A, F): p.evaluate(W)
        A.wait_for_timeout(4500)
        wa, wf = A.evaluate("()=>!!document.getElementById('intro-pop')"), F.evaluate("()=>!!document.getElementById('intro-pop')")
        chk("(7) What's New (the academy's news) does not show in Fire Code", not wf, wf)
        chk("(7) it still shows in the academy", wa, wa)
        for p in (A, F): p.evaluate("()=>{ document.querySelector('#intro-pop .intro-go')?.click(); localStorage.setItem(INTRO_KEY, '9'); }")
        A.wait_for_timeout(600)
    # ---------------------------------------------------------------- (8) Nova's words
    if want(8):
        WORDS = r"""async ()=>{ const won = novaVrMatchLine('won', true, 'race'); const vr = novaReplyFor('can I race you in a virtual room'); const test = novaReplyFor('when is the next test');
          showCustomize('character'); await new Promise(r => setTimeout(r, 900));
          const notes = [...document.querySelectorAll('#stage *')].filter(e => !e.children.length && /takes everything/.test(e.textContent)).map(e => e.textContent);
          showHome(); return { won, vr, test, notes, char: AVATAR_DISPLAY_NAME.poseidon, top: AVATAR_DISPLAY_NAME.zenith }; }"""
        wa, wf = A.evaluate(WORDS), F.evaluate(WORDS)
        chk("(8) Fire Code: beaten in a Virtual Room, Nova hands over its own character (%s), not the Sheriff: %r" % (wf["char"], wf["won"][-70:]),
            wf["char"] != "Sheriff" and wf["char"] in wf["won"] and "Sheriff" not in wf["won"], wf)
        chk("(8) Fire Code: his answer about a match names it too, and he sends nobody to a Calendar tab (%r)" % wf["test"][:70],
            ("Sheriff" not in wf["vr"]) and (wf["char"] in wf["vr"] or "Virtual Room" in wf["vr"]) and "Calendar tab" not in wf["test"], wf)
        chk("(8) Fire Code: Customize's ultimate note names its own top character (%s)" % wf["notes"], wf["notes"] and wf["top"] in wf["notes"][0] and "Zenith" not in wf["notes"][0], wf["notes"])
        chk("(8) the academy's words are as they were (the Sheriff, the Calendar tab, Zenith)", "Sheriff" in wa["won"] and "Calendar tab" in wa["test"] and wa["notes"] and "Zenith" in wa["notes"][0], wa)
    # ---------------------------------------------------------------- (9) the whole earn, walked
    if want(9):
        SETUP = r"""(a) => {
          const topics = [...new Set(QUESTIONS.map(q => (q.topic||'').trim()))].filter(Boolean).filter(t => t !== a.topic);
          const rank = window.NOVA_CLASS === 'ifc' ? 'rookie' : 'adept', rule = TIER_UNLOCKS[rank];
          store.unitPerfects = {}; topics.slice(0, rule.badges - 1).forEach(t => { store.unitPerfects[t] = badgeThresholdFor(t); });
          store.unitPerfects[a.topic] = badgeThresholdFor(a.topic) - 1;
          let pts = 500; while(levelProgress(pts).level < rule.level) pts += 100;
          store.lifetime.points = pts; store.lifetime.perfectTests = window.NOVA_CLASS === 'ifc' ? 24 : 49;
          const held = TIER_ORDER_FULL.indexOf(rank) - 1; store.rankUpShown = held + 1; store.seenUnlockedTiers = TIER_ORDER_FULL.slice(0, held + 1);
          saveStore(); showHome();
          cfg.source = 'all'; cfg.mode = 'drill'; cfg.units = [a.topic];
          setTimeout(() => beginRun(QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === a.topic)), 1500);
          return { rank, fx: HUNDO_FX.find(d => d.need === store.lifetime.perfectTests + 1).name }; }"""
        ANSWER = r"""()=>{ if(!document.querySelector('.choice') || typeof order === 'undefined' || !order.length) return 'wait';
          const key = order.length + ':' + pos;
          if(window.__answered !== key){ if(performance.now() - (window.__nextAt || 0) < 900) return 'wait'; const c = document.querySelector('.choice[data-index="' + correctSlot(order[pos]) + '"]'); if(!c) return 'wait'; c.click(); window.__answered = key; window.__answeredAt = performance.now(); return 'answered'; }
          const n = document.getElementById('nextbtn'); if(n && !n.hidden && performance.now() - window.__answeredAt > 500){ n.click(); window.__nextAt = performance.now(); return 'next'; } return 'wait'; }"""
        TOPIC = {"ifc": "Appendix H: Hazardous Materials Management Plan (HMMP) and Hazardous Materials Inventory Statement (HMIS) Instructions", "academy": "Identity Crimes"}
        W9 = {}
        for c, p in P.items():
            W9[c] = p.evaluate(SETUP, {"topic": TOPIC[c]})
        A.wait_for_timeout(6000)
        stage = {c: "answer" for c in P}; t0 = time.time()
        while time.time() - t0 < 260 and any(s != "end" for s in stage.values()):
            for c, p in P.items():
                s = stage[c]
                try:
                    if s == "answer":
                        if p.evaluate("()=>!!document.querySelector('.rs-screen')"):
                            stage[c] = "results"; p.evaluate("()=>__capStart()")
                        else: p.evaluate(ANSWER)
                    elif s == "results":
                        p.evaluate(TAP_CARD)
                        if p.evaluate("()=>!!document.querySelector('.rs-rewards.rs-done')"):
                            W9[c]["results"] = p.evaluate("()=>__capEnd()"); p.evaluate("()=>__capStart()")
                            stage[c] = "menu"; W9[c]["at"] = time.time()
                    elif s == "menu":
                        # Main menu, as a person taps it: not inside the results' guard against a tap that ran on from a card
                        if time.time() - W9[c]["at"] > 1.8:
                            if p.evaluate("()=>!!document.querySelector('.rs-screen')"):
                                p.evaluate("()=>{ const b = [...document.querySelectorAll('.rs-actions button')].find(x => /main menu/i.test(x.textContent)); b && b.click(); }")
                                W9[c]["at"] = time.time()
                            else: stage[c] = "home"; W9[c]["at"] = time.time()
                    elif s == "home":
                        p.evaluate(TAP_CARD)
                        if time.time() - W9[c]["at"] > 5 and p.evaluate("()=>document.body.classList.contains('rankup-lock') || !!document.querySelector('.ru-nudge')"):
                            p.evaluate("()=>document.getElementById('bottomtab-profile')?.click()"); stage[c] = "journey"; W9[c]["at"] = time.time()
                    elif s == "journey":
                        p.evaluate(TAP_CARD)
                        st = p.evaluate(TALK, "nova-rank")
                        if st == "go": stage[c] = "settle"; W9[c]["at"] = time.time()
                    elif s == "settle":
                        if time.time() - W9[c]["at"] > 3:
                            W9[c]["journey"] = p.evaluate("()=>__capEnd()"); stage[c] = "end"
                except Exception as ex:
                    print("   (walk %s at %s: %s)" % (c, s, str(ex)[:120]))
            A.wait_for_timeout(250)
        for c, p in P.items():
            w = W9[c]; res = w.get("results"); jr = w.get("journey")
            chk("(9) %s: the walk reached its end (results, Main menu, the Profile tab's call, the journey, Nova) - stopped at %r" % (c, stage[c]), stage[c] == "end", stage)
            if not res or not jr: continue
            words = res["texts"] + jr["texts"]
            bad = fire_leaks(words) if c == "ifc" else acad_leaks(words)
            chk("(9) %s: every word of it is the class's own (%s)" % (c, bad[:3]), not bad, bad)
            badge = p.evaluate("(u)=>badgeTitle(u)", TOPIC[c])
            chk("(9) %s: the results found the badge (its case) and unlocked %s (its card), with their sounds" % (c, w["fx"]),
                badge in res["texts"] and w["fx"] in res["texts"]
                and "cs.badge" in res["snd"] and "res.unlock.banner" in res["snd"], res["texts"])
            rk = p.evaluate("(k)=>RANK_DISPLAY_NAME[k].toUpperCase()", w["rank"])
            chk("(9) %s: the journey ranked up to %s, its reward card and Nova's words over the flare (%s)" % (c, rk, [t for t in jr["texts"] if "flare!" in t][:1]),
                rk in jr["texts"] and any("rank rewards" in t for t in jr["texts"]) and any(("my " + rk.title() + " flare") in t for t in jr["texts"]), jr["texts"])
            chk("(9) %s: nothing left on the page at the end (%s %s), the tab bar and chat button back" % (c, jr["left"], jr["focus"]),
                not jr["left"] and not jr["focus"] and jr["tab"] and jr["chat"], jr)
    chk("(10) no page errors in the academy (%s)" % aerr[:2], not aerr, aerr)
    chk("(10) no page errors in Fire Code (%s)" % ferr[:2], not ferr, ferr)
    br.close()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
