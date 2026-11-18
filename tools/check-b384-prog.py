#!/usr/bin/env python3
"""384.135 progression: prestige removed, no level cap, the academy's Full Case banner.

  python3 tools/check-b384-prog.py [--against FILE]     (must FAIL on fa11d79: prestige is there, levels stop at 80, no Full Case)

Every number is read off the page (the class's own tables and functions), never typed. Both classes, Pro Max 440x956.
  P  PRESTIGE IS GONE: none of its functions or tables exist; no character or banner carries a `prestige` flag or a pg... id;
     Customize has no Prestige group; the Tracks screen has no Prestige card and every track's last tier is a numbered gold chip
     (never "P"); an old `prestige: 3` on the account is dropped on load, never written back (the account write's document has
     none), draws nothing beside the name on Profile, and the published Fire Code row carries no `pg`.
  L  NO LEVEL CAP: for the XP of levels 81-120 (xpForLevel) the level is that level, never "at the cap"; a Supernova account
     (the rank floor) past 80 shows its curve level on Profile with an ordinary bar; Supernova is still the top rank and the
     Ascension banner still asks for Supernova's level.
  B  FULL CASE (academy): a banner whose need is the bank's unit count; held exactly when every unit's badge is (one short: not);
     derived (nothing stored); in Customize's challenge rewards and the Tracks' Feats; Fire Code's page has no such banner of its
     own but can draw an academy friend's; its art is layered, has no svg filter, and every animation it runs is transform or
     opacity, with something moving.
"""
import json, os, sys, functools, http.server, socket, threading, tempfile, shutil
from playwright.sync_api import sync_playwright

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVE = ROOT
if "--against" in sys.argv:
    src = sys.argv[sys.argv.index("--against") + 1]
    SERVE = tempfile.mkdtemp(prefix="b384prog-", dir=os.environ.get("TMPDIR") or None)
    shutil.copy(src, os.path.join(SERVE, "index.html"))
    for f in ("version.json", "ifc", "launch"):
        if os.path.exists(os.path.join(ROOT, f)): os.symlink(os.path.join(ROOT, f), os.path.join(SERVE, f))

FAILS = []
def chk(name, cond, info=""):
    if not cond: FAILS.append(name)
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  -> " + str(info)[:400]), flush=True)

def serve():
    so = socket.socket(); so.bind(("127.0.0.1", 0)); port = so.getsockname()[1]; so.close()
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=SERVE))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, port

SEED = {"onboardingComplete": True, "firstName": "Gate", "avatarChar": "ninja", "tourRev": 99, "rankMapFx244": True, "seenClassTip": True,
        "novaMet": 99, "publicId": "tst4b384prog", "classes": ["academy", "ifc"], "rankUpShown": 7, "prestige": 3,
        "lifetime": {"points": 41000, "answered": 2100, "correct": 1980, "drillPlays": 60, "examPlays": 12, "perfectTests": 64}}
def init(cls):
    S = json.dumps(json.dumps(SEED))
    return ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
        "localStorage.setItem('class26e.drill.v1',%s);localStorage.setItem('class26e.activeclass','%s');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));"
        "localStorage.setItem('class26e.greet.ifc','done');['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked',"
        "'class26e.ifc.savecode.card','class26e.ifc.getstarted','class26e.a2hs','class26e.daily.seen'].forEach(k=>localStorage.setItem(k,'1'));"
        "localStorage.setItem('class26e.ifc.drill.v1',%s);}catch(e){}") % (S, cls, S)

QUIET = """() => { document.getElementById('splashscreen')?.remove(); document.getElementById('launch-trouble')?.remove();
  try{ homeUnlocksOwed=()=>false; playUnlockSpotlight=(it,n,of,release)=>{ try{ release && release(); }catch(e){} }; }catch(e){}
  document.querySelectorAll('#tour-overlay, #tour-tooltip, #nova-intro, .rs-spot, .unlock-card').forEach(n=>n.remove()); }"""

PRESTIGE = r"""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
  out.fns = ['PRESTIGE_MAX', 'prestigeView', 'prestigeMark', 'prestigeTaken', 'takePrestige', 'showPrestige', 'setNameWithPrestige', 'vroomPrestigeFor']
    .filter(n => { try{ return typeof eval(n) !== 'undefined'; }catch(e){ return false; } });
  out.chars = AVATAR_CHARACTERS.filter(c => c.prestige || /^pg/.test(c.id)).map(c => c.id);
  out.banners = BANNERS.filter(b => b.prestige || /^pg[a-z]/.test(b.id)).map(b => b.id);
  out.storePg = 'prestige' in store;
  /* the account write's document: what writeAccount builds, through a stand-in transaction */
  out.writeHas = null;
  try{
    const prev = { db: window.acctDb, code: syncCode, conf: cloudConfirmedFor };
    let wrote = null;
    const ref = { get: () => Promise.resolve({ exists: true, data: () => ({ prestige: 2, lastModified: 1 }) }), set: d => { wrote = d; return Promise.resolve(); } };
    acctDb = () => ({ collection: () => ({ doc: () => ref }), runTransaction: f => f({ get: r => r.get(), set: (r, d) => { r.set(d); } }) });
    syncCode = 'GATECODE'; writeAccount('GATECODE', true, false, false); await wait(300);
    out.writeHas = wrote ? ('prestige' in wrote) : 'nothing written';
    acctDb = prev.db; syncCode = prev.code;
  }catch(e){ out.writeHas = 'ERR ' + e; }
  try{ out.row = window.NOVA_CLASS === 'ifc' && typeof buildClassBoardRow === 'function' ? ('pg' in (buildClassBoardRow() || {})) : null; }catch(e){ out.row = 'ERR ' + e; }
  showProfile(); await wait(1500);
  out.mark = !!document.querySelector('#stage .pg-mark, #stage [aria-label^="Prestige"]');
  showCustomize(); await wait(1200);
  out.czPrestige = [...document.querySelectorAll('#stage .cz-group-name, #stage h2, #stage h3')].some(h => /prestige/i.test(h.textContent));
  out.czText = /prestige/i.test(document.querySelector('#stage').innerText);
  showUnlockTracks(); await wait(1200);
  const st = document.querySelector('#stage');
  out.trkText = /prestige/i.test(st.innerText);
  const lasts = [...st.querySelectorAll('.trk-card[data-track]')].filter(c => c.dataset.track && c.dataset.track !== 'trk-feats').map(c => { const rows = c.querySelectorAll('.trk-tier'); const r = rows[rows.length - 1];
    const n = r && r.querySelector('.trk-num'); return { text: n ? n.textContent : null, tiers: rows.length, gold: n ? getComputedStyle(n).backgroundImage.indexOf('gradient') >= 0 : false }; });
  out.lasts = lasts;
  return out; }"""

LEVELS = r"""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
  out.past = []; for(let L = 81; L <= 120; L += 3){ const p = levelProgress(xpForLevel(L)); out.past.push([L, p.level, !!p.atCap]); }
  classTopics().forEach(u => { store.unitPerfects[u] = badgeThresholdFor(u); });
  store.lifetime.points = xpForLevel(80) + 60000; store.rankFloor = TIER_ORDER_FULL.length; store.levelFloor = 0;
  const s = levelStateFor(store); out.curve = levelProgress(store.lifetime.points).level; out.level = s.level; out.rank = rankOf(store);
  out.top = TIER_ORDER_FULL[TIER_ORDER_FULL.length - 1]; out.topLevel = TIER_UNLOCKS[out.top].level;
  out.asc = bannerDef('level80') ? { need: bannerDef('level80').need, label: bannerDef('level80').label } : null;
  showProfile(); await wait(1500);
  const lv = document.querySelector('#stage .pf-standing .pf-level'); out.shown = lv ? lv.textContent : null;
  out.over = !!document.querySelector('#stage .pf-standing .xpnums.is-over');
  return out; }"""

FULLCASE = r"""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = { cls: window.NOVA_CLASS };
  const id = 'fullcase', d = bannerDef(id); out.has = !!d;
  out.drawAcademy = typeof bannerDrawableIn === 'function' ? bannerDrawableIn(id, 'academy') : null;
  if(!d) return out;
  const units = classTopics(); out.units = units.length; out.need = d.need;
  const keys = JSON.stringify(Object.keys(store).sort());
  units.forEach(u => { store.unitPerfects[u] = badgeThresholdFor(u); });
  out.all = bannerEarned(id);
  store.unitPerfects[units[0]] = badgeThresholdFor(units[0]) - 1;
  out.short = bannerEarned(id);
  units.forEach(u => { store.unitPerfects[u] = 0; });
  out.none = bannerEarned(id);
  out.stored = JSON.stringify(Object.keys(store).sort()) !== keys;
  out.feat = unlockFeatSpec().some(it => it.k === 'banner' && it.id === id);
  showCustomize(); await wait(800);
  try{ showAppearance && 0; }catch(e){}
  out.inChallenge = BANNERS.filter(b => !b.rank && !b.flareChar && !b.ultimate).some(b => b.id === id);
  const host = document.createElement('div'); host.style.cssText = 'position:fixed;left:0;top:0;width:480px;height:180px;z-index:99999';
  host.appendChild(buildBannerArt(id)); document.body.appendChild(host); await wait(1200);
  out.layers = host.querySelectorAll('.bnl').length;
  out.filter = !!host.querySelector('filter, [filter]:not([filter="none"])');
  const anims = host.getAnimations ? host.getAnimations({ subtree: true }) : [];
  out.anims = anims.length;
  out.props = [...new Set(anims.flatMap(a => { try{ return a.effect.getKeyframes().flatMap(k => Object.keys(k).filter(x => !['offset', 'easing', 'composite', 'computedOffset'].includes(x))); }catch(e){ return []; } }))];
  host.remove();
  return out; }"""

def main():
    srv, port = serve()
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME)
        for cls in ("academy", "ifc"):
            def page():
                ctx = br.new_context(viewport={"width": 440, "height": 956})
                ctx.add_init_script(init(cls))
                pg = ctx.new_page(); errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
                pg.goto("http://127.0.0.1:%d/index.html" % port, timeout=180000); pg.wait_for_timeout(4000)
                pg.evaluate(QUIET)
                return ctx, pg, errs
            ctx, pg, errs = page()
            p = pg.evaluate(PRESTIGE)
            chk("P [%s] no prestige function or table is left (%s)" % (cls, p["fns"]), not p["fns"], p["fns"])
            chk("P [%s] no character or banner is a prestige one" % cls, not p["chars"] and not p["banners"], (p["chars"], p["banners"]))
            chk("P [%s] an old prestige count is dropped on load" % cls, p["storePg"] is False, p["storePg"])
            chk("P [%s] and never written back: the account write carries no prestige, even when the server copy has one" % cls, p["writeHas"] is False, p["writeHas"])
            if cls == "ifc": chk("P [ifc] the published board row has no pg", p["row"] is False, p["row"])
            chk("P [%s] nothing beside the name on Profile" % cls, not p["mark"], p["mark"])
            chk("P [%s] Customize says nothing of prestige" % cls, not p["czPrestige"] and not p["czText"], (p["czPrestige"], p["czText"]))
            chk("P [%s] Tracks says nothing of prestige; every track's last tier is a numbered gold chip" % cls,
                not p["trkText"] and len(p["lasts"]) >= 5 and all(x["text"] == str(x["tiers"]) and x["gold"] for x in p["lasts"]), (p["trkText"], p["lasts"]))
            ctx.close()
            ctx, pg, errs2 = page()
            l = pg.evaluate(LEVELS)
            chk("L [%s] levels 81-120 are held at their own XP, never at a cap" % cls, all(a == b and not c for a, b, c in l["past"]), l["past"])
            chk("L [%s] a Supernova account past 80 is its curve's level (%s) on Profile, an ordinary bar" % (cls, l["curve"]),
                l["curve"] > 80 and l["level"] == l["curve"] and l["shown"] == "Level %d" % l["curve"] and not l["over"], l)
            chk("L [%s] Supernova is still the top rank, and Ascension still asks for its level" % cls,
                l["rank"] == l["top"] and l["asc"] and l["asc"]["need"] == l["topLevel"] and str(l["topLevel"]) in l["asc"]["label"], l)
            ctx.close()
            ctx, pg, errs3 = page()
            f = pg.evaluate(FULLCASE)
            if cls == "academy":
                chk("B [academy] Full Case exists and asks for every unit's badge (need %s, units %s)" % (f.get("need"), f.get("units")), f["has"] and f.get("need") == f.get("units"), f)
                chk("B [academy] held with every badge, not one short, not with none - and nothing stored", f.get("all") is True and f.get("short") is False and f.get("none") is False and f.get("stored") is False, f)
                chk("B [academy] a challenge reward in Customize and a Feat in the Tracks", f.get("inChallenge") and f.get("feat"), f)
                chk("B [academy] its art: layered, no svg filter, motion by transform and opacity only, and something moves",
                    (f.get("layers") or 0) > 5 and not f.get("filter") and (f.get("anims") or 0) > 0 and set(f.get("props") or []) <= {"transform", "opacity"}, f)
            else:
                chk("B [ifc] Fire Code has no Full Case of its own, and can draw an academy friend's", not f["has"] and f["drawAcademy"] is True, f)
            ctx.close()
            e = errs + errs2 + errs3
            chk("[%s] no page errors" % cls, not e, e[:3])
        br.close()
    srv.shutdown()
    print("\n%s  (%d failure(s))" % ("ALL PASS" if not FAILS else "FAILED", len(FAILS)))
    return 1 if FAILS else 0

if __name__ == "__main__":
    sys.exit(main())
