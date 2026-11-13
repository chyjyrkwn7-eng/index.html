#!/usr/bin/env python3
"""Build 384.114: Completionist, Fire Code's banner for unlocking everything else.

Madison: "Add a banner in the IFC for completionist or however you spell it. Unlocking everything in the game. Make it
incredibly sick. All characters banners hundo effects ranks and stuff."

Every number here is read off the page (the class's own tables and the app's own unlock functions), never typed. Fixtures are
REAL counters on the store (points, chapters at 100%, the study log, the flares found ...), set in the page after it boots.
  (1) THE REGISTRY is the app's: completionistParts() lists, per category, exactly the items the gate reads off the app's own
      tables - every earnable character (Star Ranger included, the starters and retired ones not), every banner but
      Completionist (Star Ranger's included), the rank colours, the hundo effects to earn, the ranks, one badge per chapter
      and the secret flares - and each item's "held" is the app's own answer for it (isLockedCharacter, bannerEarned,
      isLockedAccent, hundoFxEarned, rankOf, unitBadgeEarned, mysteryColorsFound);
  (2) everything held (real counters): Completionist is held, have == need, its label has no count left in it;
  (3) everything but ONE (a rank floor holds Supernova; one chapter is short of its badge): locked, exactly one left, the label
      says "1 of N left" with N the registry's size, and Star Ranger (character and banner) is still held - no circle;
  (4) each category alone re-locks it (chars, banners, themes, hundo effects, ranks, badges, secret flares), and its message
      names the count the gate reads independently off the app's functions;
  (5) it reads the SAME functions: flipping one app predicate for one item (window.isLockedCharacter, bannerEarned,
      isLockedAccent, hundoFxEarned, rankOf, unitBadgeEarned) puts exactly that item in what is left;
  (6) no circularity: Star Ranger's count (ultimateProgress) and "every other banner" (collectionProgress) leave Completionist
      out, and do not move when Completionist is forced locked;
  (7) derived, never stored: nothing about it is written to the store; worn and then not held, wornBanner() and the Profile
      cover fall back to the default; held again, it is worn again;
  (8) the academy has no such banner (BANNERS, Customize, the registry), but can draw a Fire Code friend's in Fire Code's art;
  (9) Customize: the last tile of the challenge rewards, after Star Ranger; locked, a padlock, the label as its line, and its
      locked still picture actually loads (an svg image, XML); held, no padlock, a tap wears it and the Profile cover shows it;
 (10) the art: a layered banner at every size a banner is drawn at (cover, unlock card, Customize tile, lobby row, its own
      strip), never blank there; transform and opacity only, no svg filter; under Reduce motion nothing runs and two frames
      are identical, with motion on it moves;
 (11) the unlock moment: Home announces it with the ultimate's card (is-ultimate, its strip, the rank-up's flash pieces, the
      rank-up journey's two sounds), the last of what was earned; held back while a rank-up is still owed.
  python3 tools/check-b384-completionist.py [--against OLD/index.html]     (must FAIL on origin/main: there is no such banner)
"""
import json, os, sys, time, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
from playwright.sync_api import sync_playwright
BODY = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read() if "--against" in sys.argv else None
import re
_m = re.search(r'const APP_BUILD = "([^"]+)"', BODY if BODY is not None else open(os.path.join(os.path.dirname(HERE), "index.html"), encoding="utf-8").read())
BUILD = _m.group(1) if _m else ""
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:500], flush=True)
seed = dict(rc["SEED"]); seed.update(seenClassTip=True, novaMet=99, publicId="tst4fccompl1", classes=["academy", "ifc"], rankUpShown=7)
S = json.dumps(json.dumps(seed))
INIT = ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
        "localStorage.setItem('class26e.drill.v1',%s);localStorage.setItem('class26e.activeclass','ACTIVE');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));"
        "localStorage.setItem('class26e.greet.ifc','done');['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted','class26e.a2hs','class26e.daily.seen'].forEach(k=>localStorage.setItem(k,'1'));"
        "localStorage.setItem('class26e.ifc.drill.v1',%s);}catch(e){}") % (S, S)

# Everything held, from real counters (in the page, so the chapters and question keys are the bank's own).
EVERY = r"""() => {
  document.getElementById('splashscreen')?.remove(); document.getElementById('launch-trouble')?.remove();
  /* off Home first, so its unlock queue does not start announcing what this fixture hands over under the checks */
  try{ showAppearance(); }catch(e){}
  /* ...and whatever the seed's own unlocks put up at boot (its hundo effects) is let go: off Home, the queue stops behind it */
  document.querySelectorAll('.rs-spot').forEach(sp => { try{ sp.__nova.skip(); }catch(e){ sp.remove(); } });
  const s = store;
  s.lifetime = Object.assign({}, s.lifetime, { points: 400000, correct: 12000, answered: 14000, perfectTests: 300, fullTests: 260, longestStreak: 120 });
  s.unitPerfects = {}; classTopics().forEach(u => { s.unitPerfects[u] = 99; });
  s.dailyCorrectTotal = 12; s.novaBeaten = true; s.vrWins = 4; s.vrMatches = 30; s.vrHosted = 4; s.hundoDayBest = 4;
  s.bigTest450Passed = true; s.friendsBest = 6; s.lateHundos = 4; s.lateHundosSeed312 = true; s.practiceExamPerfect = true; s.unitHundoStreakBest = 12;
  s.mysteryColorsFound = {}; MYSTERY_ORDER.forEach(k => { s.mysteryColorsFound[k] = true; });
  s.rankFloor = 0; s.rankUpShown = TIER_ORDER_FULL.length;
  const log = {}, d0 = Date.parse('2026-09-01T12:00:00Z');
  for(let i = 0; i < 40; i++) log[new Date(d0 + i * 864e5).toISOString().slice(0, 10)] = 2 * 3600000;
  s.studyLog = log;
  s.stats = s.stats || {};
  Array.from(retakeKeySet()).slice(0, 120).forEach(k => { s.stats[k] = Object.assign({}, s.stats[k] || {}, { m: 2, c: 3 }); });
  return true; }"""
# The gate's OWN read of the registry: the app's tables and the app's functions, nothing of completionistParts.
MINE = r"""() => {
  const H = (f) => { try{ return !!f(); }catch(e){ return false; } };
  const held = rankOf(store), hi = TIER_ORDER_FULL.indexOf(held);
  return {
    chars: AVATAR_CHARACTERS.filter(c => !c.retired && !c.legacy && (c.feat || c.unlock)).map(c => [c.id, H(() => !isLockedCharacter(c.id))]),
    banners: BANNERS.filter(b => b.id !== 'completionist').map(b => [b.id, H(() => bannerEarned(b.id))]),
    themes: ACCENTS.filter(a => !!TIER_UNLOCKS[a]).map(a => [a, H(() => !isLockedAccent(a))]),
    fx: HUNDO_FX.filter(d => d.need > 0).map(d => [d.id, H(() => hundoFxEarned(d.id))]),
    ranks: TIER_ORDER_FULL.filter(k => !!TIER_UNLOCKS[k]).map(k => [k, !!held && TIER_ORDER_FULL.indexOf(k) <= hi]),
    badges: classTopics().map(u => [u, H(() => unitBadgeEarned(u))]),
    flares: MYSTERY_ORDER.map(k => [k, !!(store.mysteryColorsFound || {})[k]]) }; }"""
APP = r"""() => { const p = (typeof completionistProgress === 'function') ? completionistProgress() : null; const d = (typeof bannerDef === 'function') ? bannerDef('completionist') : null;
  return { p: p && { have: p.have, need: p.need, left: p.left, note: p.note, missing: p.missing },
    parts: (typeof completionistParts === 'function') ? completionistParts().map(c => [c.key, c.items.map(it => [it.id, it.held()])]) : null,
    def: !!d, earned: !!d && bannerEarned('completionist'), label: d ? d.label : null, worn: typeof wornBanner === 'function' ? wornBanner() : null,
    zenithChar: !isLockedCharacter(typeof ULTIMATE_TOP === 'string' ? ULTIMATE_TOP : 'zenith'), zenithBanner: bannerEarned(typeof ULTIMATE_TOP === 'string' ? ULTIMATE_TOP : 'zenith') }; }"""
CATS = ["chars", "banners", "themes", "fx", "ranks", "badges", "flares"]
WORD = {"chars": "character", "banners": "banner", "themes": "theme", "fx": "hundo effect", "ranks": "rank", "badges": "badge", "flares": "secret flare"}

srv, port = rc["serve"]()
def page(br, active="ifc", w=440, h=956, dpr=1):
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=dpr)
    ctx.set_default_timeout(150000)   # a 10MB page on a busy machine: loads and screenshots wait, the checks themselves do not change
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:300]))
    if BODY is not None:
        pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    # the update check answers with the page's own build, so no reload lands in the middle of a check
    pg.route("**/version.json*", lambda r, q: r.fulfill(status=200, headers={"content-type": "application/json"}, body=json.dumps({"build": BUILD, "frameId": "", "note": ""})))
    pg.add_init_script(INIT.replace("ACTIVE", active))
    pg.goto("http://127.0.0.1:%d/index.html" % port)
    for _ in range(60):
        try:
            if pg.evaluate("() => typeof showHome === 'function' && !!document.getElementById('stage')"): break
        except Exception: pass
        pg.wait_for_timeout(500)
    pg.wait_for_timeout(1500)
    pg.evaluate("() => { document.getElementById('splashscreen')?.remove(); document.getElementById('launch-trouble')?.remove(); }")
    return ctx, pg, errs
def app(pg): return pg.evaluate(APP)
def mine(pg): return pg.evaluate(MINE)
def left_of(m): return {c: [i for i, h in m[c] if not h] for c in CATS}
from contextlib import contextmanager
@contextmanager
def section(name):
    """a part that cannot run at all (a build without the banner throws on its first call) is one FAIL, and the rest still run"""
    try:
        yield
    except Exception as e:
        chk(name + " runs", False, repr(e)[:300])

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    errs_ifc, errs_art, errs_unl, errs_ac = [], [], [], []
    with section("(1)-(9) the rule and Customize"):
        ctx, pg, errs = page(br)
        pg.evaluate(EVERY)
        A, M = app(pg), mine(pg)
        print("  registry:", {c: len(M[c]) for c in CATS}, "total", sum(len(M[c]) for c in CATS), flush=True)
        # ---- (1) the registry is the app's
        parts = dict((k, v) for k, v in (A.get("parts") or []))
        chk("(1) Fire Code has a Completionist banner", A.get("def") is True, A)
        chk("(1) the registry has every category, in order: characters, banners, themes, hundo effects, ranks, badges, secret flares", list(parts.keys()) == CATS, list(parts.keys()))
        for c in CATS:
            chk("(1) %s: the same items as the class's own tables (%d)" % (c, len(M[c])), [i for i, _ in parts.get(c, [])] == [i for i, _ in M[c]] and len(M[c]) > 0,
                {"app": [i for i, _ in parts.get(c, [])][:30], "gate": [i for i, _ in M[c]][:30]})
        top = pg.evaluate("() => ULTIMATE_TOP")
        chk("(1) Star Ranger (the ultimate) is counted, character and banner; Completionist is not; no starter or retired character is",
            top in [i for i, _ in parts.get("chars", [])] and top in [i for i, _ in parts.get("banners", [])] and "completionist" not in [i for i, _ in parts.get("banners", [])]
            and not pg.evaluate("(ids) => ids.some(id => { const c = AVATAR_CHARACTERS.find(x => x.id === id); return !c || c.retired || c.legacy || (!c.feat && !c.unlock); })", [i for i, _ in parts.get("chars", [])]), top)
        chk("(1) one badge per chapter of the bank, and the top rank asks for every one", len(M["badges"]) == pg.evaluate("() => classTopics().length") == pg.evaluate("() => TIER_UNLOCKS.titan.badges"),
            [len(M["badges"]), pg.evaluate("() => TIER_UNLOCKS.titan.badges")])
        need = sum(len(M[c]) for c in CATS)
        chk("(1) its size is the registry's (%d)" % need, (A.get("p") or {}).get("need") == need, A.get("p"))
        # ---- (2) everything held
        chk("(2) everything held (real counters): Completionist is held", A.get("earned") is True and A["p"]["have"] == A["p"]["need"] and all(all(h for _, h in M[c]) for c in CATS), left_of(M))
        chk("(2) its label has nothing left in it", A.get("label") and " left" not in A["label"] and A["label"].startswith("Unlock everything in Fire Code"), A.get("label"))
        # ---- (3) everything but one: the floor holds Supernova, one chapter is short of its badge
        r = pg.evaluate("""() => { const ch = classTopics(); store.rankFloor = TIER_ORDER_FULL.length; store.unitPerfects[ch[7]] = 0; return ch[7]; }""")
        A, M = app(pg), mine(pg)
        lo = left_of(M)
        chk("(3) everything but one (a badge): exactly one thing is left, and it is that chapter's badge", sum(len(v) for v in lo.values()) == 1 and lo["badges"] == [r], lo)
        chk("(3) Completionist is locked and says so: '1 of %d left'" % need, A.get("earned") is False and A["p"]["left"] == 1 and ("1 of %d left" % need) in (A.get("label") or ""), [A.get("label"), A.get("p")])
        chk("(3) the note names it: '1 badge'", "1 badge" in (A["p"].get("note") or "") and "badges" not in (A["p"].get("note") or ""), A["p"].get("note"))
        chk("(3) Star Ranger, which Completionist counts, is still held (character and banner) - nothing waits on itself", A.get("zenithChar") is True and A.get("zenithBanner") is True, A)
        pg.evaluate("(u) => { store.unitPerfects[u] = 99; store.rankFloor = 0; }", r)
        chk("(3) and that badge back, it is held again", app(pg).get("earned") is True)
        # ---- (4) each category alone re-locks it
        BREAK = {
            "chars": ("store.novaBeaten = false", "store.novaBeaten = true"),
            "banners": ("store.vrMatches = 20", "store.vrMatches = 30"),
            "themes": ("window.__ila = isLockedAccent; window.isLockedAccent = a => a === 'adept' ? true : window.__ila(a)", "window.isLockedAccent = window.__ila"),
            "fx": ("store.lifetime.perfectTests = 90", "store.lifetime.perfectTests = 300"),
            "ranks": ("store.unitPerfects[classTopics()[3]] = 0", "store.unitPerfects[classTopics()[3]] = 99"),
            "badges": ("store.rankFloor = TIER_ORDER_FULL.length; store.unitPerfects[classTopics()[11]] = 0", "store.rankFloor = 0; store.unitPerfects[classTopics()[11]] = 99"),
            "flares": ("store.mysteryColorsFound[MYSTERY_ORDER[MYSTERY_ORDER.length - 1]] = false", "store.mysteryColorsFound[MYSTERY_ORDER[MYSTERY_ORDER.length - 1]] = true"),
        }
        for c in CATS:
            brk, fix = BREAK[c]
            pg.evaluate("() => { " + brk + "; }")
            A, M = app(pg), mine(pg); lo = left_of(M); n = sum(len(v) for v in lo.values())
            chk("(4) %s: one taken away re-locks it, and what is left is the gate's own count (%d)" % (c, n),
                A.get("earned") is False and len(lo[c]) >= 1 and A["p"]["left"] == n and A["p"]["missing"] == lo and ("%d of %d left" % (n, need)) in (A.get("label") or ""),
                {"label": A.get("label"), "app": A.get("p"), "gate": lo})
            chk("(4) %s: the note names it ('%s')" % (c, WORD[c]), WORD[c] in (A["p"].get("note") or ""), A["p"].get("note"))
            pg.evaluate("() => { " + fix + "; }")
            chk("(4) %s: put back, held again" % c, app(pg).get("earned") is True, app(pg).get("p"))
        # ---- (5) the same functions
        FLIP = {
            "chars": ("forge", "window.__f = isLockedCharacter; window.isLockedCharacter = id => id === 'forge' ? true : window.__f(id)", "window.isLockedCharacter = window.__f"),
            "banners": ("tests100", "window.__f = bannerEarned; window.bannerEarned = id => id === 'tests100' ? false : window.__f(id)", "window.bannerEarned = window.__f"),
            "themes": ("elite", "window.__f = isLockedAccent; window.isLockedAccent = a => a === 'elite' ? true : window.__f(a)", "window.isLockedAccent = window.__f"),
            "fx": ("bubbles", "window.__f = hundoFxEarned; window.hundoFxEarned = (id, n) => id === 'bubbles' ? false : window.__f(id, n)", "window.hundoFxEarned = window.__f"),
            "ranks": ("titan", "window.__f = rankOf; window.rankOf = st => st === store ? 'elite' : window.__f(st)", "window.rankOf = window.__f"),
            "badges": (None, "window.__f = unitBadgeEarned; window.__u = classTopics()[20]; window.unitBadgeEarned = u => u === window.__u ? false : window.__f(u)", "window.unitBadgeEarned = window.__f"),
        }
        for c, (want, on, off) in FLIP.items():
            pg.evaluate("() => { " + on + "; }")
            p = pg.evaluate("() => { const p = completionistProgress(); return { missing: p.missing[%s], left: p.left, u: window.__u || null }; }" % json.dumps(c))
            pg.evaluate("() => { " + off + "; }")
            w = want or p.get("u")
            chk("(5) %s: the app's own function decides it (flip it for %s, and that is what is missing)" % (c, w), w in (p.get("missing") or []), p)
        # ---- (6) no circularity
        r = pg.evaluate("""() => { const a = ultimateProgress(), b = collectionProgress('banners'); const zc = !isLockedCharacter(ULTIMATE_TOP), zb = bannerEarned(ULTIMATE_TOP);
          window.__f = bannerEarned; window.bannerEarned = id => id === 'completionist' ? false : window.__f(id);
          const a2 = ultimateProgress(), b2 = collectionProgress('banners'), zc2 = !isLockedCharacter(ULTIMATE_TOP);
          window.bannerEarned = window.__f;
          return { a: [a.have, a.need], a2: [a2.have, a2.need], b: [b.have, b.need], b2: [b2.have, b2.need], zc, zb, zc2,
            uBanners: BANNERS.filter(x => x.id !== ULTIMATE_TOP && !x.completionist).length, cBanners: BANNERS.filter(x => !x.ultimate && !x.completionist).length }; }""")
        chk("(6) Star Ranger's count leaves Completionist out and does not move when it is forced locked", r["a"] == r["a2"] and r["a"][0] == r["a"][1] and r["zc"] and r["zb"] and r["zc2"], r)
        chk("(6) 'every other banner' leaves it out too", r["b"] == r["b2"] and r["b"][1] == r["cBanners"], r)
        # ---- (7) derived, never stored
        r = pg.evaluate("""async () => { const wait = ms => new Promise(f => setTimeout(f, ms));
          /* the pick (store.banner) and the viewing record (shown on a card, looked at in Customize) are not a grant; nothing else may name it */
          const out = {}; const keysWith = () => JSON.stringify(Object.assign({}, store, { banner: '', unlocksShown: null, seenUnlocks: null })).indexOf('completionist') >= 0;
          out.storedBefore = keysWith(); store.banner = 'completionist'; out.worn = wornBanner();
          showProfile(); await wait(900); out.cover = !!document.querySelector('.profile-cover .bnr-completionist');
          store.vrMatches = 20; out.wornLocked = wornBanner(); showProfile(); await wait(900); out.coverLocked = !!document.querySelector('.profile-cover .bnr-completionist');
          store.vrMatches = 30; out.wornAgain = wornBanner(); out.storedAfter = keysWith(); return out; }""")
        chk("(7) nothing about it is on the store (only the pick, when worn)", r["storedBefore"] is False and r["storedAfter"] is False, r)
        chk("(7) worn while held: it is the banner, on the Profile cover", r["worn"] == "completionist" and r["cover"] is True, r)
        chk("(7) worn and no longer held: the default, on the cover too; held again, worn again", r["wornLocked"] == "" and r["coverLocked"] is False and r["wornAgain"] == "completionist", r)
        # ---- (9) Customize
        r = pg.evaluate("""async () => { const wait = ms => new Promise(f => setTimeout(f, ms)); const out = {};
          store.banner = ''; store.vrMatches = 20; showCustomize('banner'); await wait(1800);
          const cards = [...document.querySelectorAll('.cz-group')];
          const card = cards.find(g => g.querySelector('.banner-opt[data-banner="' + ULTIMATE_TOP + '"]'));
          const tiles = card ? [...card.querySelectorAll('.banner-opt')].map(b => b.dataset.banner) : [];
          out.tiles = tiles.slice(-3); out.lastInCard = tiles[tiles.length - 1]; out.afterTop = tiles.indexOf('completionist') > tiles.indexOf(ULTIMATE_TOP);
          const t = document.querySelector('.banner-opt[data-banner="completionist"]');
          out.locked = !!t && t.classList.contains('locked'); out.lock = !!(t && t.querySelector('.banner-opt-lock'));
          out.need = t && t.querySelector('.banner-opt-need') ? t.querySelector('.banner-opt-need').textContent : null; out.label = bannerDef('completionist').label;
          t && t.scrollIntoView({ block: 'center' });
          /* the tiles' art is filled a few a frame after the screen is up (fillDeferredBannerArt): wait for this one's */
          for(let i = 0; i < 40 && t && !t.querySelector('img'); i++) await wait(250);
          const im = t && t.querySelector('img'); if(im && !im.complete) await new Promise(f => { im.onload = f; im.onerror = f; setTimeout(f, 4000); });
          out.still = im ? im.naturalWidth : -1;
          store.vrMatches = 30; showCustomize('banner'); await wait(1800);
          const t2 = document.querySelector('.banner-opt[data-banner="completionist"]');
          out.lockedHeld = !!t2 && t2.classList.contains('locked'); out.lockHeld = !!(t2 && t2.querySelector('.banner-opt-lock'));
          t2 && t2.click(); await wait(300); out.picked = store.banner; out.sel = !!t2 && t2.classList.contains('selected');
          return out; }""")
        chk("(9) Customize: the last tile of the challenge rewards, after Star Ranger", r["lastInCard"] == "completionist" and r["afterTop"] is True, r)
        chk("(9) locked: a padlock, and its line is the label (what is left)", r["locked"] and r["lock"] and r["need"] == r["label"] and " left" in (r["need"] or ""), r)
        chk("(9) its locked still picture loads (an svg image is XML: one repeated attribute and it draws nothing)", (r.get("still") or 0) > 0, r)
        chk("(9) held: no padlock, a tap wears it", r["lockedHeld"] is False and r["lockHeld"] is False and r["picked"] == "completionist" and r["sel"], r)
        errs_ifc = list(errs)
        ctx.close()

    with section("(10) the art"):
        # ---- (10) the art, at every size it is drawn at
        ctx, pg, errs = page(br, w=1000, h=900)
        SIZES = [[960, 360], [440, 165], [288, 108], [232, 87], [170, 64], [400, 56]]
        r = pg.evaluate("""(sizes) => { const out = { mark: '', layers: [], props: [], anims: 0 };
          const wrap = document.createElement('div'); wrap.id = 'cw'; wrap.style.cssText = 'position:fixed;left:0;top:0;z-index:2147483646;background:#000;display:flex;flex-wrap:wrap;gap:6px;width:1000px';
          sizes.forEach(([w, h], i) => { const b = document.createElement('div'); b.id = 'cb' + i; b.style.cssText = 'position:relative;overflow:hidden;width:' + w + 'px;height:' + h + 'px;border-radius:12px';
            const el = buildBannerArt('completionist'); b.appendChild(el); wrap.appendChild(b); out.layers.push(el.querySelectorAll('.bnl').length); out.mark += el.innerHTML; });
          document.body.appendChild(wrap);
          out.filter = /<filter|\\sfilter=/.test(out.mark); out.mark = out.mark.length;
          return out; }""", SIZES)
        pg.wait_for_timeout(800)
        r2 = pg.evaluate("""() => { const props = new Set(); let n = 0; const el = document.querySelector('#cb0 .bnr');
          el.getAnimations({ subtree: true }).forEach(a => { n++; (a.effect.getKeyframes() || []).forEach(k => Object.keys(k).forEach(p => { if(['offset', 'easing', 'composite', 'computedOffset'].indexOf(p) < 0) props.add(p); })); });
          return { n, props: [...props] }; }""")
        chk("(10) a layered banner at every size (%s)" % ", ".join("%dx%d" % tuple(s) for s in SIZES), all(n > 5 for n in r["layers"]), r["layers"])
        chk("(10) no svg filter anywhere in it", r["filter"] is False, r)
        chk("(10) it moves (%d animations) and only by transform and opacity" % r2["n"], r2["n"] > 5 and set(r2["props"]) <= {"transform", "opacity"}, r2)
        def shot(i, path):
            pg.evaluate("() => document.getElementById('launch-trouble')?.remove()")
            pg.query_selector("#cb%d" % i).screenshot(path=path)
            from PIL import Image, ImageStat
            im = Image.open(path).convert("RGB"); st = ImageStat.Stat(im)
            w, h = im.size; c = im.crop((int(w * .35), int(h * .2), int(w * .65), int(h * .8)))
            gold = sum(1 for p in c.getdata() if p[0] > 170 and p[1] > 110 and p[2] < 120) / float(c.size[0] * c.size[1])
            return im, sum(st.stddev) / 3.0, gold, hashlib.md5(im.tobytes()).hexdigest()
        tmp = os.path.join("/dev/shm", "compl-%d" % os.getpid()); os.makedirs(tmp, exist_ok=True)
        for i, s in enumerate(SIZES):
            im, sd, gold, _ = shot(i, os.path.join(tmp, "s%d.png" % i))
            chk("(10) %dx%d: drawn, not blank (contrast %.0f), the helmet's gold in the middle (%.0f%%)" % (s[0], s[1], sd, gold * 100), sd > 20 and gold > .04, [sd, gold])
        pg.evaluate("() => { document.documentElement.dataset.reduceMotion = 'true'; }"); pg.wait_for_timeout(400)
        n_rm = pg.evaluate("() => document.querySelector('#cb0 .bnr').getAnimations({ subtree: true }).filter(a => a.playState === 'running').length")
        _, _, _, h1 = shot(1, os.path.join(tmp, "rm1.png")); pg.wait_for_timeout(1300); _, sd, gold, h2 = shot(1, os.path.join(tmp, "rm2.png"))
        chk("(10) Reduce motion: nothing runs, two frames 1.3s apart are the same picture, and it is still the scene", n_rm == 0 and h1 == h2 and sd > 20 and gold > .04, [n_rm, h1 == h2, sd, gold])
        pg.evaluate("() => { delete document.documentElement.dataset.reduceMotion; }"); pg.wait_for_timeout(600)
        _, _, _, m1 = shot(0, os.path.join(tmp, "mv1.png")); pg.wait_for_timeout(900); _, _, _, m2 = shot(0, os.path.join(tmp, "mv2.png"))
        chk("(10) motion on: two frames differ", m1 != m2, [m1, m2])
        errs_art = list(errs)
        ctx.close()

    with section("(11) the unlock moment"):
        # ---- (11) the unlock moment
        ctx, pg, errs = page(br)
        pg.evaluate(EVERY)
        r = pg.evaluate("""async () => { const wait = ms => new Promise(f => setTimeout(f, ms)); const out = {};
          /* everything else already announced; only Completionist is owed */
          ensureUnlocksShown();
          store.unlocksShown.chars = announceableHeldCharacters().concat(HOME_UNLOCK_SKIP);
          store.unlocksShown.banners = BANNERS.filter(b => bannerEarned(b.id) && b.id !== 'completionist').map(b => b.id);
          store.unlocksShown.fx = earnedHundoFx(); store.flareHintsShown = ['umbra', 'singularity', 'genesis'];
          try{ localStorage.removeItem(FLARE_OWED_KEY); }catch(e){}
          out.pending = pendingHomeUnlocks().banners;
          /* a rank-up still owed holds it back, on the results and on Home */
          const was = store.rankUpShown; store.rankUpShown = TIER_ORDER_FULL.length - 1;
          out.heldHome = pendingHomeUnlocks().banners;
          out.heldResults = rsUnlockItems({ badges: [], retroBadges: [], characters: [], banners: ['completionist'], fx: [] }).map(it => it.banner || it.character);
          store.rankUpShown = was;
          out.order = rsUnlockItems({ badges: [], retroBadges: [], characters: [ULTIMATE_TOP], banners: ['completionist', ULTIMATE_TOP], fx: [] }).map(it => it.banner || it.character);
          for(let i = 0; i < 20 && (homeUnlockPlaying || document.querySelector('.rs-spot')); i++) await wait(250);
          out.queueIdle = !homeUnlockPlaying && !document.querySelector('.rs-spot');
          const sounds = []; const ps = window.playSound; window.playSound = (id, o) => { sounds.push(id); return ps(id, o); };
          showHome();
          let spot = null;
          for(let i = 0; i < 60 && !spot; i++){ await wait(500); spot = document.querySelector('.rs-spot:not(.is-leaving)'); }
          /* the card's own clock: its flash at 1.22s and its title at 1.9s after it is up (more on a loaded machine) */
          for(let i = 0; spot && i < 40 && sounds.indexOf('rank.title') < 0; i++) await wait(250);
          if(spot){ await wait(400);
            out.cls = spot.className; out.ult = spot.classList.contains('is-ultimate');
            out.art = !!spot.querySelector('.bnr-completionist'); out.strip = (spot.querySelector('.rs-spot-strip span') || {}).textContent || '';
            out.name = (spot.querySelector('.rs-spot-name') || {}).textContent || '';
            out.pieces = ['.rs-morph-rays', '.rs-morph-flash', '.rs-morph-ring', '.rs-morph-sparks'].filter(s => spot.querySelector(s)).length;
            out.foot = (spot.querySelector('.rs-spot-foot') || {}).textContent || '';
          }
          window.playSound = ps; out.sounds = sounds;
          out.shown = (store.unlocksShown.banners || []).indexOf('completionist') >= 0;
          return out; }""")
        chk("(11) Home owes it once everything else has been told", r.get("pending") == ["completionist"], r)
        chk("(11) a rank-up still owed holds it back, on Home and on the results", "completionist" not in (r.get("heldHome") or []) and "completionist" not in (r.get("heldResults") or []), r)
        chk("(11) on the results it is the last thing told, after Star Ranger", (r.get("order") or [None])[-1] == "completionist" and len(r.get("order") or []) == 3, r.get("order"))
        chk("(11) Home plays it with the ultimate's card: the banner, its strip, the rank-up's flash pieces", r.get("ult") is True and r.get("art") is True and r.get("strip") and r.get("pieces") == 4 and r.get("name") == "Completionist", r)
        chk("(11) and the rank-up journey's two sounds on its clock", "rank.flash" in (r.get("sounds") or []) and "rank.title" in (r.get("sounds") or []), r.get("sounds"))
        chk("(11) seen, it is marked shown", r.get("shown") is True, r)
        errs_unl = list(errs)
        ctx.close()

    with section("(8) the academy"):
        # ---- (8) the academy
        ctx, pg, errs = page(br, active="academy")
        r = pg.evaluate("""async () => { const wait = ms => new Promise(f => setTimeout(f, ms)); const out = { cls: window.NOVA_CLASS };
          out.inBanners = BANNERS.some(b => b.id === 'completionist' || b.completionist); out.def = !!bannerDef('completionist');
          out.parts = typeof completionistParts === 'function' ? completionistParts().length : -1;
          showCustomize('banner'); await wait(1500);
          out.tile = !!document.querySelector('.banner-opt[data-banner="completionist"]'); out.text = /Completionist/.test(document.body.innerText);
          out.drawable = typeof bannerDrawableIn === 'function' && bannerDrawableIn('completionist', 'ifc') && !bannerDrawableIn('completionist', 'academy');
          const el = typeof buildWornBannerArt === 'function' ? buildWornBannerArt('completionist', 'ink', 'ifc') : null;
          out.friend = !!el && el.classList.contains('bnr-completionist') && el.querySelectorAll('.bnl').length > 5;
          store.banner = 'completionist'; out.worn = wornBanner(); return out; }""")
        chk("(8) the academy has no such banner: not in its list, no definition, no registry, no tile, no word of it in Customize",
            r["cls"] == "academy" and not r["inBanners"] and not r["def"] and r["parts"] == 0 and not r["tile"] and not r["text"], r)
        chk("(8) and cannot wear one (a stray pick is the default)", r["worn"] == "", r)
        chk("(8) but a Fire Code friend's is drawn on a card here, in Fire Code's art", r["drawable"] is True and r["friend"] is True, r)
        errs_ac = list(errs)
        ctx.close()
    allerrs = [e for e in errs_ifc + errs_art + errs_unl + errs_ac]
    chk("no page errors, either class", not allerrs, allerrs[:4])
    br.close()
print("ALL PASS" if ok else "FAILURES", flush=True)
sys.exit(0 if ok else 1)
