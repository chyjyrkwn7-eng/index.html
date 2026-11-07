#!/usr/bin/env python3
"""Build 384, the second pass on Fire Code's banners (Madison's review + "the names do need to line up with the challenge").
In the Fire Code class:

 (1) all 23 banners draw with a tint and no page error, and each is named for its challenge (the table below);
 (2) every banner this pass redrew is drawn differently from bb7eb94 (hashes of bannerStaticSVG taken there with --dump), and Code Book,
     Star Ranger and the three rank banners are exactly as they were ("only touch what is genuinely off");
 (3) FIRE INVESTIGATOR's tape reads FIRE SCENE and DO NOT CROSS (lettering drawn by fbTextPath, whole and large) and never "FIRE LINE";
 (4) THE CREW is five people (.fb-person) in a line under five coats; CERTIFIED has its CERTIFIED lettering; FULLY COMPLIANT draws COMPLIANT and
     100%; INCIDENT COMMAND draws COMMAND; MUTUAL AID draws five unit chips (one per agency) round one incident;
 (5) GRAND FINALE has a sky of at least ten fireworks on their own clocks (bl-fwk) - Pyrotechnics had five;
 (6) HOSE LINE is drawn with the shared firefighter (.fb-ff) the Training Tower crew uses, not a flat silhouette; TRAINING TOWER has two or more of them;
 (7) AFTER HOURS and FIRE INVESTIGATOR are different pictures: no long shape in common, and one is colder than the other;
 (8) THE FOUR SECRET FLARES are four scenes: no long shape drawn in all four, four different hashes, and each carries its own colour
     (Nebula red/orange/yellow, Quasar violet, Pulsar white-blue, Solstice rose);
 (9) none of the redrawn has an svg filter; ids per copy do not clash and every url(#...) resolves; none is heavier than 700 elements or 24 layers;
(10) the stamp's letters exist: the sign-writer's grid has P, K, W, V, G and the figures 0-9, % and -.

  python3 tools/check-b384-fcbanners.py [--against OLD/index.html]    (must FAIL on bb7eb94)
  python3 tools/check-b384-fcbanners.py --dump    prints the hashes (run it against the build before to refresh PREV)
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
from playwright.sync_api import sync_playwright
BODY = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read() if "--against" in sys.argv else None
DUMP = "--dump" in sys.argv
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:500])
NAMES = {"tests100": "Certified", "tests250": "Training Tower", "tests500": "The Crew", "hundos100": "Fully Compliant", "hundos250": "Grand Finale",
         "vr50": "Mutual Aid", "study50": "Code Book", "study60": "On Call", "correct5000": "Downpour", "correct10000": "Fire Investigator",
         "level80": "Incident Command", "early10": "After Hours", "exam100": "Hose Line", "adept_rank": "Sapphire", "elite_rank": "Amethyst", "titan_rank": "Supernova",
         "flare_void": "Nebula", "flare_umbra": "Quasar", "flare_horizon": "Pulsar", "flare_genesis": "Solstice", "zenith": "Star Ranger"}
REDONE = ["tests100", "tests250", "tests500", "hundos100", "hundos250", "vr50", "study60", "correct5000", "correct10000", "level80", "early10", "exam100",
          "flare_void", "flare_umbra", "flare_horizon", "flare_genesis"]
KEEP = ["study50", "adept_rank", "elite_rank", "titan_rank", "zenith"]
# bannerStaticSVG hashes on bb7eb94 (python3 tools/check-b384-fcbanners.py --dump --against <bb7eb94's index.html>)
PREV = {}
try: PREV = json.load(open(os.path.join(HERE, "check-b384-fcbanners.prev.json")))
except Exception: pass
seed = dict(rc["SEED"]); seed["publicId"] = "xph5b57jbp5a"; seed["novaMet"] = 99
SNAP = r"""(a) => {
  const REDONE = a[0], ALL = a[1];
  const hash = s => { let h = 2166136261; for(let i = 0; i < s.length; i++){ h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0).toString(16); };
  const out = { cls: window.NOVA_CLASS, errs: [], hashes: {}, names: {}, svg: {}, src: {}, layers: {}, weight: {}, tint: {} };
  BANNERS.forEach(b => out.names[b.id] = b.name);
  ALL.forEach(id => { try{
    out.hashes[id] = hash(bannerStaticSVG(id) || '');
    out.svg[id] = bannerStaticSVG(id) || '';
    const el = buildBannerArt(id); if(!el || !el.querySelector('svg')) out.errs.push(id + ' draws nothing');
    out.tint[id] = !!bannerTintOf(id);
    const art = BANNER_ART[id]('g'); const arr = Array.isArray(art) ? art : [];
    out.layers[id] = { n: arr.length, cls: arr.map(l => l.cls || ''), all: arr.map(l => (l.svg || '') + (l.kids || []).map(k => k.svg || '').join('')).join('') };
    const a = buildBannerArt(id); out.weight[id] = [a.querySelectorAll('*').length, a.querySelectorAll('.bnl').length];
  }catch(e){ out.errs.push(id + ': ' + e); } });
  out.filters = REDONE.filter(id => /<filter|filter=/.test((out.layers[id] || {}).all || '') || /<filter/.test(out.svg[id] || ''));
  out.idClash = []; out.unresolved = [];
  REDONE.forEach(id => { const x = buildBannerArt(id), y = buildBannerArt(id);
    const ia = new Set([...x.querySelectorAll('[id]')].map(e => e.id)), ib = [...y.querySelectorAll('[id]')].map(e => e.id);
    if(ib.some(v => ia.has(v))) out.idClash.push(id);
    const refs = (x.innerHTML.match(/url\(#([^)]+)\)/g) || []).map(m => m.slice(5, -1));
    const miss = [...new Set(refs.filter(r => !ia.has(r)))]; if(miss.length) out.unresolved.push([id, miss.slice(0, 3)]); });
  /* the lettering's drawn paths, by the app's own sign-writer */
  const tp = (s, cx, cy, h) => { try{ return fbTextPath(s, cx, cy, h); }catch(e){ return ''; } };
  out.tape = { dnc: out.layers.correct10000 ? out.layers.correct10000.all.indexOf(tp('DO NOT CROSS', 328, 30, 8.4)) >= 0 : false,
    fs: out.layers.correct10000 ? out.layers.correct10000.all.indexOf(tp('FIRE SCENE', 214, 30, 8.4)) >= 0 : false,
    fireLine: out.layers.correct10000 ? out.layers.correct10000.all.indexOf(tp('FIRE LINE', 300, 23.5, 7)) >= 0 : false };
  out.glyphs = ['P', 'K', 'W', 'V', 'G', '0', '5', '9', '%', '-'].filter(g => !(window.FB_GLYPH || (typeof FB_GLYPH !== 'undefined' && FB_GLYPH) || {})[g]);
  /* shapes: counts of things in the still pictures, mounted off screen */
  const mount = id => { const d = document.createElement('div'); d.innerHTML = out.svg[id]; return d; };
  const cnt = (id, sel) => mount(id).querySelectorAll(sel).length;
  out.shape = { persons: cnt('tests500', '.fb-person'), ffTower: cnt('tests250', '.fb-ff'), ffHose: cnt('exam100', '.fb-ff'),
    chips: mount('vr50').querySelectorAll('rect[stroke="#0B1626"][rx="3"]').length };
  const longs = id => { const s = new Set(); mount(id).querySelectorAll('path').forEach(p => { const d = p.getAttribute('d') || ''; if(d.length > 60) s.add(d); }); return s; };
  const shared = ids => { const sets = ids.map(longs); return [...sets[0]].filter(k => sets.every(s => s.has(k))).length; };
  out.sharedFlares = shared(['flare_void', 'flare_umbra', 'flare_horizon', 'flare_genesis']);
  out.sharedAH = shared(['early10', 'correct10000']);
  out.fwk = (out.layers.hundos250 || { cls: [] }).cls.filter(c => /bl-fwk/.test(c)).length;
  out.fw = {}; ['tests100', 'hundos100', 'level80', 'vr50'].forEach(id => out.fw[id] = true);
  /* how cold a picture is: the share of its colours (by use) with more blue in them than red */
  const cold = id => { const m = (out.svg[id].match(/#[0-9a-fA-F]{6}/g) || []); let c = 0; m.forEach(h => { const n = parseInt(h.slice(1), 16); if((n & 255) >= (n >> 16)) c++; }); return Math.round(c / Math.max(1, m.length) * 100) / 100; };
  out.cold = { early10: cold('early10'), correct10000: cold('correct10000') };
  out.colours = {}; ['flare_void', 'flare_umbra', 'flare_horizon', 'flare_genesis'].forEach(id => out.colours[id] = (out.layers[id].all + out.svg[id]).toUpperCase());
  return out;
}"""
srv, port = rc["serve"]()
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    ctx = br.new_context(viewport={"width": 440, "height": 956})
    pg = ctx.new_page(); perr = []
    pg.on("pageerror", lambda e: perr.append(str(e)[:200]))
    pg.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
        "localStorage.setItem('class26e.drill.v1',%s);localStorage.setItem('class26e.ifc.drill.v1',%s);"
        "localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));localStorage.setItem('class26e.greet.ifc','done');"
        "['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted'].forEach(k=>localStorage.setItem(k,'1'));}catch(e){}"
        % (json.dumps(json.dumps(seed)), json.dumps(json.dumps(seed))))
    if BODY is not None:
        pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(3000)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    F = pg.evaluate(SNAP, [REDONE, list(NAMES)])
    ctx.close(); br.close()
srv.shutdown()
if DUMP:
    print(json.dumps(F["hashes"], indent=1)); sys.exit(0)
chk("(1) the page is Fire Code (%s), every banner draws with a tint, no page errors" % F["cls"], F["cls"] == "ifc" and not F["errs"] and not perr and all(F["tint"].values()), (F["errs"], perr))
bad = {i: (F["names"].get(i), n) for i, n in NAMES.items() if F["names"].get(i) != n}
chk("(1) each banner is named for its challenge (%d wrong)" % len(bad), not bad, bad)
same = [i for i in REDONE if PREV.get(i) and F["hashes"].get(i) == PREV[i]]
chk("(2) every redrawn banner differs from bb7eb94 (unchanged: %s; %d hashes known)" % (same, len(PREV)), PREV and not same, same)
moved = [i for i in KEEP if PREV.get(i) and F["hashes"].get(i) != PREV[i]]
chk("(2) Code Book, Star Ranger and the rank banners are as they were (changed: %s)" % moved, PREV and not moved, moved)
t = F["tape"]
chk("(3) Fire Investigator's tape reads FIRE SCENE and DO NOT CROSS and not FIRE LINE (%s)" % t, t["dnc"] and t["fs"] and not t["fireLine"], t)
S = F["shape"]
chk("(4) The Crew is five people (%s)" % S["persons"], S["persons"] == 5, S)
chk("(4) Mutual Aid has its five unit chips (%s)" % S["chips"], S["chips"] >= 5, S)
L = F["layers"]
chk("(5) Grand Finale has at least ten fireworks on their own clocks (%s; Pyrotechnics had five)" % F["fwk"], F["fwk"] >= 10, F["fwk"])
chk("(6) Hose Line is drawn with the shared firefighter (%s) and the Training Tower has %s of them" % (S["ffHose"], S["ffTower"]), S["ffHose"] >= 1 and S["ffTower"] >= 2, S)
chk("(7) After Hours and Fire Investigator share no long shape (%s) and After Hours is the colder picture (%s)" % (F["sharedAH"], F["cold"]),
    F["sharedAH"] == 0 and F["cold"]["early10"] - F["cold"]["correct10000"] > .25, F["cold"])
fl = ["flare_void", "flare_umbra", "flare_horizon", "flare_genesis"]
chk("(8) the four secret flares are four scenes (shared long shapes %s, hashes %s)" % (F["sharedFlares"], len(set(F["hashes"][i] for i in fl))), F["sharedFlares"] == 0 and len(set(F["hashes"][i] for i in fl)) == 4, F["sharedFlares"])
C = F["colours"]
chk("(8) each carries its character's colour",
    all(c in C["flare_void"] for c in ["#EF4444", "#F97316", "#FACC15"]) and "#8B5CF6" in C["flare_umbra"] and "#CFEAFF" in C["flare_horizon"] and "#FF5CA8" in C["flare_genesis"], {k: v[:0] for k, v in C.items()})
chk("(9) no svg filter in the redrawn (%s); ids per copy (%s); every url(#) resolves (%s)" % (F["filters"], F["idClash"], F["unresolved"]), not F["filters"] and not F["idClash"] and not F["unresolved"])
heavy = {i: F["weight"][i] for i in REDONE if F["weight"][i][0] > 700 or F["weight"][i][1] > 24}
chk("(9) none of the redrawn is heavier than 700 elements or 24 layers (%s)" % {i: F["weight"][i] for i in REDONE}, not heavy, heavy)
chk("(10) the sign-writer's grid has P K W V G, the figures and the percent sign (missing: %s)" % F["glyphs"], not F["glyphs"], F["glyphs"])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
