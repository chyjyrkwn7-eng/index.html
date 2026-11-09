"""Build 384 r20: signing in to Fire Code must not hand over what the academy held.
Madison: "people signing into the fire code class, they unlocked the character of the placeholder of that one that they have
selected from the academy class".
The leak: a Fire Code store's first load worked out its "kept from before" list (store.legacyChars, which makes
isLockedCharacter() false) from the character it was SEEDED with - legacyCharsFromRanks() counts whoever wears a Clown or an
Astronaut, migrateHive384() whoever wears the Hive - so the academy's selected character came across as kept, unlocked and
selected in Fire Code. With an in-memory Firestore (the CDN is blocked here) and an academy account with real progress:
  A  a fresh device signing in to an account in Fire Code (the academy's copy and code on the device, no Fire Code copy), the
     academy wearing each of a dozen characters in turn;
  A2 the same where the academy's copy has not yet written its Hive flag (hiveMoved384);
  B  the account's Fire Code document already in the cloud carrying the leak from before (the character worn, kept, shown and
     queued): on a fresh device; and the MIGRATION on a device whose own Fire Code copy carries it - repaired once and left alone,
     what Fire Code did earn kept (and a copy with no sync repaired at launch);
  C  the first class switch (switchClass) from the academy page;
  D  a sign-up for both classes (a starter, nothing earned): the starter comes across;
  E  the real Sign in screen, an account in Fire Code alone, a Clown worn;
  F  the other way: the academy opened after Fire Code ran - its own kept characters kept, nothing of Fire Code's in it.
After each, in Fire Code: nobody wears a character this class has not unlocked, no character reads unlocked that it has not
earned (isLockedCharacter against the class's own challenge or rank, "kept from before" aside), the Customize page shows those
locked, no queued unlock or Home card for one, and the academy's saved copy is byte for byte what it was.
Run:  python3 tools/check-b384-signinchars.py   (--against OLD/index.html must FAIL)"""
import json, os, sys, re
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
OLD_BUILD = None
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
    def _patched(ins, _o=OLD):
        v = {"top": f"{ins[0]}px", "right": f"{ins[1]}px", "bottom": f"{ins[2]}px", "left": f"{ins[3]}px"}
        return g["INSET_RE"].sub(lambda m: v[m.group(1)], _o)
    g["patched"] = _patched
    OLD_BUILD = re.search(r'const APP_BUILD = "([^"]+)"', OLD).group(1)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else ("  -> " + str(info)[:400]), flush=True)
CODE = "TEST-3840"; PUB = "pubsignin3840"
FAKE = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split('FAKE = r"""')[1].split('"""')[0]
SEEN = ("['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card',"
        "'class26e.getstarted','class26e.frame.ok'].forEach(k=>localStorage.setItem(k, k==='class26e.frame.ok'?'go-live-1':'1'));")
SEEN_IFC = ("['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card',"
            "'class26e.ifc.getstarted','class26e.ifc.unithold.tip'].forEach(k=>localStorage.setItem(k,'1'));")
srv, serve_url = g["serve"]()
def page(br, init, seed=None):
    ctx = br.new_context(viewport={"width": 440, "height": 956}, has_touch=True)
    ctx.add_init_script("window.__cloudSeed = %s;" % json.dumps(seed or {}))
    ctx.add_init_script(FAKE); ctx.add_init_script(g["STANDALONE"]); ctx.add_init_script(init)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    body = g["patched"]((59, 0, 34, 0))
    if OLD_BUILD:
        pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"}, body=json.dumps({"build": OLD_BUILD, "force": False, "frameId": ""})))
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.goto(serve_url); pg.wait_for_timeout(3500)
    pg.evaluate("document.getElementById('splashscreen')?.remove()")
    return ctx, pg, errs
def academy_acct(char, **kw):
    a = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]()))
    a.update({"publicId": PUB, "firstName": "Pat", "avatarChar": char, "novaMet": 99, "hiveMoved384": True, "tourRev": 999,
              "novaHeard": {"@recap": 99991231}, "classes": ["academy", "ifc"], "lastModified": 1790500000000})
    a.update(kw); return a
def init_js(academy, active, ifc_store=None):
    s = "(()=>{ if(sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); " + SEEN
    s += "localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode', '%s');" % (json.dumps(json.dumps(academy)), CODE)
    if active == "ifc":
        s += "localStorage.setItem('class26e.activeclass','ifc'); localStorage.setItem('class26e.greet.ifc','done');" + SEEN_IFC
    if ifc_store is not None: s += "localStorage.setItem('class26e.ifc.drill.v1', %s);" % json.dumps(json.dumps(ifc_store))
    return s + " })()"

PROBE = """()=>{
  /* what the class itself earned: read with the "kept from before" list emptied, which is the one thing that makes a character read held without its own challenge or rank */
  const own = id => { const keep = store.legacyChars; store.legacyChars = [];
    try{ const d = AVATAR_CHARACTERS.find(c => c.id === id); if(!d) return false; if(d.feat) return featAchieved(d.feat); if(d.unlock) return tierColorUnlocked(d.unlock); return true; }
    finally{ store.legacyChars = keep; } };
  const live = AVATAR_CHARACTERS.filter(c => !c.retired && !c.legacy);
  const o = { cls: window.NOVA_CLASS, avatar: store.avatarChar, legacy: (store.legacyChars || []).slice(), pend: (store.pendingCharUnlocks || []).slice(),
    shown: ((store.unlocksShown || {}).chars || []).slice(), seen: ((store.seenUnlocks || {}).chars || []).slice(), flag: store.ifcCharsFixed384, hive: store.hiveMoved384,
    pts: (store.lifetime || {}).points, starter: (typeof classDefaultCharacter === 'function') ? classDefaultCharacter() : null, name: store.firstName };
  o.avatarLocked = isLockedCharacter(store.avatarChar); o.avatarOwn = own(store.avatarChar);
  o.leak = live.filter(c => !isLockedCharacter(c.id) && !own(c.id)).map(c => c.id);
  o.heldCount = live.filter(c => !isLockedCharacter(c.id)).length;
  o.pendLocked = o.pend.filter(id => isLockedCharacter(id));
  try{ o.home = pendingHomeUnlocks().chars.slice(); o.homeBad = o.home.filter(id => !own(id)); }catch(e){ o.home = 'ERR ' + e; o.homeBad = []; }
  o.ownedIds = live.filter(c => own(c.id)).map(c => c.id);
  try{
    showCustomize('character');
    const byName = {}; live.forEach(c => { byName[AVATAR_DISPLAY_NAME[c.id] || c.id] = c.id; });
    o.tiles = [...document.querySelectorAll('#stage .avatarchar-option')].map(t => ({ id: byName[t.title] || t.title, locked: t.classList.contains('locked'), sel: t.classList.contains('selected') }));
    o.tilesBad = o.tiles.filter(t => !t.locked && o.ownedIds.indexOf(t.id) < 0).map(t => t.id);
    o.selLocked = o.tiles.filter(t => t.sel && t.locked).map(t => t.id);
  }catch(e){ o.tiles = 'ERR ' + e; o.tilesBad = []; o.selLocked = []; }
  o.acadRaw = window.localStorage['class26e.drill.v1'] || null;
  return o; }"""
def probe(pg):
    for _ in range(4):
        try: return pg.evaluate(PROBE)
        except Exception as e:
            if "context was destroyed" in str(e) or "navigation" in str(e).lower(): pg.wait_for_timeout(1500); continue
            raise
def wait_class(pg, cls, secs=40):
    for _ in range(secs * 2):
        try:
            if pg.evaluate("()=>window.NOVA_CLASS === %s && typeof store === 'object' && !!store && !!(document.querySelector('#stage [data-screen=\"home\"]'))" % json.dumps(cls)): return True
        except Exception: pass
        pg.wait_for_timeout(500)
    return False
def init_js(academy, active, ifc_store=None, code=CODE):
    s = "(()=>{ if(sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); " + SEEN
    if academy is not None:
        s += "localStorage.setItem('class26e.drill.v1', %s);" % json.dumps(json.dumps(academy))
    if code: s += "localStorage.setItem('class26e.synccode', '%s');" % code
    if active == "ifc":
        s += "localStorage.setItem('class26e.activeclass','ifc'); localStorage.setItem('class26e.greet.ifc','done');" + SEEN_IFC
    if ifc_store is not None: s += "localStorage.setItem('class26e.ifc.drill.v1', %s);" % json.dumps(json.dumps(ifc_store))
    return s + " })()"
def retried(fn, tries=4):
    """the machine is loaded and a page sometimes crashes (TargetClosedError): the same walk again, from a fresh context"""
    for i in range(tries):
        try: return fn()
        except Exception as e:
            if i == tries - 1 or not any(w in str(e) for w in ("crashed", "Target", "closed", "Timeout")): raise
            print("  (retry: %s)" % str(e).split("\n")[0][:80], flush=True)
def run(br, academy, active="ifc", ifc_store=None, cloud=None, code=CODE, settle=2.5, after=None):
    def go():
        ctx, pg, errs = page(br, init_js(academy, active, ifc_store, code), seed={"progress": cloud or {}})
        try:
            if after: after(pg)
            else: pg.wait_for_timeout(int(settle * 1000))
            r = probe(pg); r["errs"] = errs[:2]; r["pg"] = pg; r["ctx"] = ctx
            return r
        except Exception:
            try: ctx.close()
            except Exception: pass
            raise
    return retried(go)
def done(r): r["ctx"].close()
def academy_acct(char, **kw):
    a = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]()))
    a.update({"publicId": PUB, "firstName": "Pat", "avatarChar": char, "novaMet": 99, "hiveMoved384": True, "tourRev": 999, "seenClassTip": True,
              "novaHeard": {"@recap": 99991231}, "classes": ["academy", "ifc"], "lastModified": 1790500000000})
    a.update(kw); return a
def fc_store(char, **kw):
    s = {"firstName": "Pat", "publicId": PUB, "avatarChar": char, "onboardingComplete": True, "tourRev": 999, "novaMet": 99, "hiveMoved384": True,
         "sheriffMoved324": True, "seenClassTip": True, "seenMainMenuTour": True, "seenProfileTour": True, "seenModeSelectTour": True,
         "seenUnitSelectTour": True, "seenRankingsTour": True, "seenAppearanceTour": True, "novaHeard": {"@recap": 99991231}, "leaderboardOptIn": False,
         "leaderboardOptInChanged": True, "lastModified": 1790400000000, "lifetime": {"points": 4321, "answered": 900, "correct": 777}}
    s.update(kw); return s
def leaked(char, **kw):
    return fc_store(char, legacyChars=[char, "hive"] if char != "hive" else ["hive"], unlocksShown={"chars": [char, "hive"], "banners": [], "fx": []},
                    seenUnlocks={"chars": [char], "banners": [], "themes": [], "badges": [], "fx": [], "v": 99}, pendingCharUnlocks=["hive"], **kw)
def common(label, r, acad_raw=None, kept=()):
    """what must hold in Fire Code after any way in"""
    bad = []
    if r["cls"] != "ifc": bad.append("class " + str(r["cls"]))
    if r["avatarLocked"] or not r["avatarOwn"]: bad.append("wears %s (locked=%s, earned=%s)" % (r["avatar"], r["avatarLocked"], r["avatarOwn"]))
    if r["leak"]: bad.append("unlocked unearned: %s" % r["leak"])
    if r["tilesBad"] or r["selLocked"]: bad.append("Customize shows unlocked %s / selected-locked %s" % (r["tilesBad"], r["selLocked"]))
    if r["pendLocked"]: bad.append("queued for locked %s" % r["pendLocked"])
    if r["homeBad"]: bad.append("Home card for %s" % r["homeBad"])
    for k in kept:
        if k not in r["ownedIds"] or k in r["leak"]: bad.append("lost what it earned: %s" % k)
        if r["avatarLocked"]: pass
    if acad_raw is not None and r["acadRaw"] != acad_raw: bad.append("the academy's saved copy changed")
    if r["errs"]: bad.append("page errors %s" % r["errs"])
    chk(label, not bad, "; ".join(bad))
    return not bad

CHARS = ["clown", "astronaut", "hive", "voidwalker", "poseidon", "zeus", "detective", "ronin", "marksman", "forge", "inferno", "hacker"]
only = [a.split("=", 1)[1] for a in sys.argv if a.startswith("--only=")]
def want(k): return not only or k in only[0].split(",")
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    # ---- A: a fresh device signs in to an account in Fire Code (no Fire Code copy yet)
    if want("A"):
        print("\nA  fresh device, the academy's copy and code on it, Fire Code opening for the first time", flush=True)
        for c in CHARS:
            ac = academy_acct(c)
            r = run(br, ac, cloud={CODE: ac})
            common("A  academy wears %-10s -> Fire Code wears %s (kept list %s)" % (c, r["avatar"], r["legacy"]), r, json.dumps(ac)); done(r)
    # ---- A2: the academy copy has not written its Hive flag yet
    if want("A2"):
        print("\nA2 the academy's copy has no hiveMoved384 yet (opened the new build, switched at once)", flush=True)
        for c in ["hive", "clown", "astronaut"]:
            ac = academy_acct(c); ac.pop("hiveMoved384")
            r = run(br, ac, cloud={CODE: ac})
            common("A2 academy wears %-10s -> Fire Code wears %s (kept list %s, hive flag %s)" % (c, r["avatar"], r["legacy"], r["hive"]), r, json.dumps(ac)); done(r)
    # ---- B: Fire Code's document already in the cloud, carrying the leak
    if want("B"):
        print("\nB  Fire Code's own document in the cloud carries the leak from before", flush=True)
        for c in ["clown", "astronaut", "hive"]:
            ac = academy_acct(c); doc = leaked(c)
            r = run(br, ac, cloud={CODE: ac, CODE + "__ifc": doc}, settle=4)
            common("B  fresh device, cloud copy wears %-10s -> %s (kept list %s)" % (c, r["avatar"], r["legacy"]), r); done(r)
        print("\nB2 the migration: this device's own Fire Code copy carries the leak", flush=True)
        for c in ["clown", "astronaut", "hive"]:
            ac = academy_acct(c); loc = leaked(c, bestTestStreak=120, vrWins=0)
            r = run(br, ac, ifc_store=loc, cloud={CODE: ac, CODE + "__ifc": loc}, settle=5)
            ok1 = common("B2 own copy wears %-10s -> %s; earned Marksman kept" % (c, r["avatar"]), r, kept=["marksman"])
            chk("B2 %-10s repaired once: kept list cleared, flag set, nothing shown or queued for it, points %s untouched" % (c, r["pts"]),
                ok1 and r["legacy"] == [] and r["flag"] is True and c not in r["shown"] and "hive" not in r["pend"] and (c in ("hive",) or "hive" not in r["shown"]) and r["pts"] == 4321, r)
            # left alone after: wear what Fire Code earned, relaunch - still worn, not reset
            r["pg"].evaluate("()=>{ store.avatarChar = 'marksman'; saveStore(); }"); r["pg"].wait_for_timeout(600)
            r["pg"].reload(); r["pg"].wait_for_timeout(4500)
            r2 = probe(r["pg"]); r2["errs"] = r["errs"]
            chk("B2 %-10s left alone after: the Marksman worn on a relaunch stays (%s), flag still set" % (c, r2["avatar"]), r2["avatar"] == "marksman" and r2["flag"] is True and not r2["leak"], r2)
            done(r)
        # Fire Code earned the Clown itself (five Virtual Room wins): what is earned stays selected and unlocked
        ac = academy_acct("clown"); loc = leaked("clown", vrWins=5)
        r = run(br, ac, ifc_store=loc, cloud={CODE: ac, CODE + "__ifc": loc}, settle=5)
        chk("B2 a Clown Fire Code earned on its own stays worn and unlocked (%s), the kept list cleared (%s)" % (r["avatar"], r["legacy"]),
            r["avatar"] == "clown" and not r["avatarLocked"] and r["flag"] is True and r["legacy"] == [] and not r["leak"], r); done(r)
        # no sync on the device: repaired at launch
        ac = academy_acct("astronaut"); loc = leaked("astronaut")
        r = run(br, ac, ifc_store=loc, code=None, settle=3)
        common("B3 no sync, own copy wears astronaut -> %s" % r["avatar"], r); done(r)
    # ---- C: the first class switch
    if want("C"):
        print("\nC  the first class switch, from the academy page", flush=True)
        for c in ["clown", "hive", "voidwalker"]:
            ac = academy_acct(c)
            ctx, pg, errs = page(br, init_js(ac, "academy"), seed={"progress": {CODE: ac}})
            try:
                pg.evaluate("()=>switchClass('ifc')")
                got = wait_class(pg, "ifc", 60); pg.wait_for_timeout(2500)
                r = probe(pg); r["errs"] = errs[:2]
                chk("C  switched (%s)" % got, got)
                common("C  academy wears %-10s -> after the switch Fire Code wears %s (kept list %s)" % (c, r["avatar"], r["legacy"]), r)
            except Exception as e:
                chk("C  switch ran (%s)" % c, False, str(e)[:200])
            ctx.close()
    # ---- D: a sign-up for both classes
    if want("D"):
        print("\nD  a sign-up for both classes: the starter, nothing earned", flush=True)
        for c in ["ghost", "grizzly"]:
            ac = academy_acct(c, lifetime={"points": 100, "answered": 0, "correct": 0}, unitPerfects={}, weekPoints=0, classes=["academy", "ifc"])
            r = run(br, ac, cloud={CODE: ac})
            common("D  new account, starter %-8s -> Fire Code wears %s" % (c, r["avatar"]), r)
            chk("D  the starter comes across (%s)" % r["avatar"], r["avatar"] == c, r); done(r)
    # ---- E: the real Sign in screen
    if want("E"):
        print("\nE  the Sign in screen, an account in Fire Code alone, a Clown worn", flush=True)
        ac = academy_acct("clown", classes=["ifc"])
        ctx = br.new_context(viewport={"width": 440, "height": 956}, has_touch=True); errs = []
        ctx.add_init_script("window.__cloudSeed = %s;" % json.dumps({"progress": {CODE: ac}})); ctx.add_init_script(FAKE); ctx.add_init_script(g["STANDALONE"])
        ctx.add_init_script("(()=>{ if(sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); " + SEEN + " })()")
        pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        body = g["patched"]((59, 0, 34, 0))
        if OLD_BUILD: pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"}, body=json.dumps({"build": OLD_BUILD, "force": False, "frameId": ""})))
        pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
        try:
            pg.goto(serve_url); pg.wait_for_timeout(3500); pg.evaluate("document.getElementById('splashscreen')?.remove()")
            scr = pg.evaluate("()=>{ const s=document.querySelector('#stage [data-screen]'); return s ? s.dataset.screen : ''; }")
            pg.click(".gs-signin" if scr == "getstarted" else ".welcome-signin"); pg.wait_for_timeout(500)
            pg.focus(".synccode-entry-panel input:not([type=checkbox])"); pg.keyboard.type(CODE)
            pg.click(".synccode-entry-panel #nextbtn"); pg.wait_for_timeout(900)
            pg.click(".synccode-confirm .next.playbtn")
            got = wait_class(pg, "ifc", 80); pg.wait_for_timeout(3500)
            r = probe(pg); r["errs"] = errs[:2]
            chk("E  signing in with the code opens Fire Code (%s)" % got, got)
            common("E  signed in with a Clown worn in the academy -> Fire Code wears %s (kept list %s)" % (r["avatar"], r["legacy"]), r)
        except Exception as e:
            chk("E  the sign-in walk ran", False, str(e)[:300])
        ctx.close()
    # ---- F: the other way - the academy after Fire Code
    if want("F"):
        print("\nF  the other way: the academy opened with a Fire Code copy that carries the leak", flush=True)
        for c, kept in [("clown", ["clown"]), ("ghost", [])]:
            ac = academy_acct(c, legacyChars=kept)
            loc = leaked("astronaut")
            ctx, pg, errs = page(br, init_js(ac, "academy", loc), seed={"progress": {CODE: ac}})
            pg.wait_for_timeout(3000)
            a = pg.evaluate("""()=>({ cls: window.NOVA_CLASS, avatar: store.avatarChar, legacy: (store.legacyChars||[]).slice(),
                clownLocked: isLockedCharacter('clown'), astroLocked: isLockedCharacter('astronaut'), hiveLocked: isLockedCharacter('hive'), flag: store.ifcCharsFixed384 })""")
            good = a["cls"] == "academy" and a["avatar"] == c and a["legacy"] == kept and a["clownLocked"] == (c != "clown") and a["astroLocked"] and a["hiveLocked"] and not errs
            chk("F  academy wearing %-6s (kept %s) is as it was: %s" % (c, kept, a), good, [a, errs[:2]])
            ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
