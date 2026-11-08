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

(11) BUILD 384 ROUND 3b (Madison's review of round 3): six items, seven banners, redrawn and measured on the page itself, not by hashes alone -
     INSPECTION TEAM (was Engine Company; five inspectors, five different heights, none overlapping, feet on the apron, two flashlight beams),
     PERFECT SCORE (was Fully Compliant; a lit seven-segment 100 and a percent sign, ten lit lamps), GRAND FINALE (a proper Silverado in profile:
     its proportions, two tyres standing ON the ground, windows, ghost lettering, a roof bar; fireworks with glows; clipped light on the body),
     TOP OF THE LADDER (was Fully Involved; a ladder of 12+ rungs whose top reaches the roof edge, one firefighter standing on it, no hose, no fire)
     and TEN IN A ROW (was Hose Line; exactly ten gauges in one evenly spaced row, ten needles in the green, ten lamps, ten numbered plates),
     the two pictures sharing nothing; FIRE INVESTIGATOR's tape at chest height, tied at both ends, sagging, twisted once, its lettering whole;
     AFTER HOURS (a flashlight on a riser's valve, gauge and PASSED tag; no thermal camera, no PANEL 4B; the clock near eleven).
     Every one of the seven differs from c8143d5 (prev2.json) and the other fourteen non-Pulsar banners are exactly as c8143d5 drew them.

  python3 tools/check-b384-fcbanners.py [--against OLD/index.html]    (must FAIL on bb7eb94, and on c8143d5 for the round 3b lines)
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
NAMES = {"tests100": "Certified", "tests250": "Plan Review", "tests500": "Inspection Team", "hundos100": "Perfect Score", "hundos250": "Grand Finale",
         "vr50": "Mutual Aid", "study50": "Code Book", "study60": "On Call", "correct5000": "Downpour", "correct10000": "Fire Investigator",
         "level80": "Top of the Ladder", "early10": "After Hours", "exam100": "Ten in a Row", "adept_rank": "Sapphire", "elite_rank": "Amethyst", "titan_rank": "Supernova",
         "flare_void": "Nebula", "flare_umbra": "Quasar", "flare_horizon": "Pulsar", "flare_genesis": "Eclipse", "zenith": "Star Ranger"}
REDONE = ["tests100", "tests250", "tests500", "hundos100", "hundos250", "vr50", "study50", "study60", "correct10000", "level80", "early10", "exam100",
          "flare_umbra", "flare_horizon", "flare_genesis"]
KEEP = ["correct5000", "flare_void", "adept_rank", "elite_rank", "titan_rank", "zenith"]
# round 3b: the six redrawn in it, and hashes taken on c8143d5 (--dump --against its index.html)
R3B = ["tests500", "hundos100", "hundos250", "level80", "exam100", "early10", "correct10000"]
PREV2 = {}
try: PREV2 = json.load(open(os.path.join(HERE, "check-b384-fcbanners.prev2.json")))
except Exception: pass
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
  const has = (id, str) => !!out.layers[id] && out.layers[id].all.indexOf(str) >= 0;
  out.has = has; 
  out.text = { sysnorm: has('study60', tp('SYSTEMS NORMAL', 238, 60.6, 7.4)), pull: has('study60', 'class="fb-pull"'), clock: has('study60', 'r="25" fill="#2A2D34"'), tag: has('study60', 'fill="#F2C21E"/>' + '<circle'),
    cert: has('tests100', tp('CERTIFIED', 222, 38, 11)), plan: has('tests250', tp('PLAN REVIEW', 173, 163, 3.6)) || has('tests250', tp('PLAN REVIEW', 128 + 45, 163, 3.6)),
    unitScore: has('hundos100', tp('UNIT SCORE', 240, 33.6, 7.4)), tenAced: has('exam100', tp('10 UNITS ACED IN A ROW', 240, 29.2, 6.4)),
    fireStation: has('tests500', tp('FIRE STATION', 240, 38.6, 7.4)), old187: has('early10', tp('187F', 234, 62, 4.4)), oldPanel: has('early10', tp('PANEL 4B', 322, 30.6, 5.2)),
    engine: has('tests500', tp('ENGINE COMPANY 5', 240, 20.4, 8.6)), oldCompliant: has('hundos100', tp('COMPLIANT', 0, 12.4, 5.6)) };
  out.coins = ((out.layers.tests100 || { all: '' }).all.match(/stroke-dasharray="\.7 \.65"/g) || []).length;
  out.flags = has('tests100', 'x="14" y="30" width="2" height="100"') || has('tests100', 'x="462" y="30" width="2" height="100"');
  out.ghost = has('hundos250', 'class="fb-ghost"') && has('hundos250', tp('FIRE MARSHAL', 0, 0, 1)) === false;
  out.stations = ((out.layers.vr50 || { all: '' }).all.match(/r="3\.6" fill="#0B1626"/g) || []).length; out.yellowEnd = has('vr50', 'L251 58');
  out.glyphs = ['P', 'K', 'W', 'V', 'G', '0', '5', '9', '%', '-'].filter(g => !(window.FB_GLYPH || (typeof FB_GLYPH !== 'undefined' && FB_GLYPH) || {})[g]);
  /* shapes: counts of things in the still pictures, mounted off screen */
  const mount = id => { const d = document.createElement('div'); d.innerHTML = out.svg[id]; return d; };
  const cnt = (id, sel) => mount(id).querySelectorAll(sel).length;
  out.shape = { persons: cnt('tests500', '.fb-person'), ffTower: cnt('level80', '.fb-ff'), ffHose: cnt('exam100', '.fb-ff'),
    chips: mount('vr50').querySelectorAll('rect[stroke="#0B1626"][rx="3"]').length };
  const longs = id => { const s = new Set(); mount(id).querySelectorAll('path').forEach(p => { const d = p.getAttribute('d') || ''; if(d.length > 60) s.add(d); }); return s; };
  const shared = ids => { const sets = ids.map(longs); return [...sets[0]].filter(k => sets.every(s => s.has(k))).length; };
  out.sharedFlares = shared(['flare_void', 'flare_umbra', 'flare_horizon', 'flare_genesis']);
  out.sharedAH = shared(['early10', 'correct10000']);
  out.sharedLE = shared(['level80', 'exam100']);
  out.fwk = (out.layers.hundos250 || { cls: [] }).cls.filter(c => /bl-fwk/.test(c)).length;
  out.fw = {}; ['tests100', 'hundos100', 'level80', 'vr50'].forEach(id => out.fw[id] = true);
  /* how cold a picture is: the share of its colours (by use) with more blue in them than red */
  const cold = id => { const m = (out.svg[id].match(/#[0-9a-fA-F]{6}/g) || []); let c = 0; m.forEach(h => { const n = parseInt(h.slice(1), 16); if((n & 255) >= (n >> 16)) c++; }); return Math.round(c / Math.max(1, m.length) * 100) / 100; };
  out.cold = { early10: cold('early10'), correct10000: cold('correct10000') };
  out.colours = {}; ['flare_void', 'flare_umbra', 'flare_horizon', 'flare_genesis'].forEach(id => out.colours[id] = (out.layers[id].all + out.svg[id]).toUpperCase());
  return out;
}"""
GEO = r"""() => {
  /* the still pictures, mounted 1:1 (a unit is a pixel) so the app's own drawing can be measured: ids per copy, so each is mounted once */
  const mount = id => { const box = document.createElement('div'); box.style.cssText = 'position:fixed;left:0;top:0;width:480px;height:180px;overflow:hidden;z-index:99999';
    box.innerHTML = bannerStaticSVG(id) || ''; document.body.appendChild(box); const sv = box.querySelector('svg'); if(sv){ sv.setAttribute('width', 480); sv.setAttribute('height', 180); sv.setAttribute('preserveAspectRatio', 'none'); } return box; };
  const R = e => { const r = e.getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height, r: r.right, b: r.bottom, cx: r.left + r.width / 2, cy: r.top + r.height / 2 }; };
  const r1 = v => Math.round(v * 10) / 10;
  const all = (b, sel) => [...b.querySelectorAll(sel)];
  const out = {};
  const layerStr = id => { try{ const a = BANNER_ART[id]('gq'); return Array.isArray(a) ? a.map(l => (l.svg || '') + (l.kids || []).map(k => k.svg || '').join('')).join('') : String(a); }catch(e){ return ''; } };
  /* A. inspection team */
  try{ const b = mount('tests500'); const ins = all(b, '.fb-inspector').map(R).sort((p, q) => p.x - q.x);
    out.A = { n: ins.length, heights: ins.map(r => r1(r.h)), feet: ins.map(r => r1(r.b)), tops: ins.map(r => r1(r.y)),
      overlap: ins.slice(1).map((r, i) => r1(ins[i].r - r.x)), beams: (layerStr('tests500').match(/class="fb-beam"/g) || []).length }; b.remove(); }catch(e){ out.err = (out.err || '') + String(e).slice(0, 120) + ' '; }
  /* B. perfect score */
  try{ const b = mount('hundos100'); out.B = { segs: all(b, '.fb-seg').map(e => (e.getAttribute('d').match(/Z/g) || []).length), pct: all(b, '.fb-pct').length, lamps: all(b, '.fb-lamp').length,
      lampsLit: all(b, '.fb-lamp').filter(e => /^#[5-9a-f][0-9a-f]ff[0-9a-f]{2}$/i.test(e.getAttribute('fill'))).length,
      digitsY: all(b, '.fb-seg').map(e => { const r = R(e); return [r1(r.y), r1(r.b)]; }) }; b.remove(); }catch(e){ out.err = (out.err || '') + String(e).slice(0, 120) + ' '; }
  /* C. grand finale */
  try{ const b = mount('hundos250'); const tk = b.querySelector('.fb-truck'); const T = tk ? R(tk) : null;
    const ty = all(b, '.fb-tyre').map(R);
    const glass = all(tk || b, 'path').filter(e => /tkglass/.test(e.getAttribute('fill') || '')).length;
    const body = all(tk || b, 'path').filter(e => /tkbody/.test(e.getAttribute('fill') || ''))[0];
    const B = body ? R(body) : null;
    const ls = layerStr('hundos250');
    out.C = { truck: !!tk, tyres: ty.map(r => ({ cx: r1(r.cx), bottom: r1(r.b), d: r1(r.w) })), body: B && { x: r1(B.x), y: r1(B.y), w: r1(B.w), h: r1(B.h), b: r1(B.b) },
      ratio: B ? r1(B.w / (165 - B.y)) : 0, glass, ghost: !!(tk && tk.querySelector('.fb-ghost')), bar: /#6A1418/.test(tk ? tk.innerHTML : ''),
      glows: (ls.match(/class="fb-glow"/g) || []).length, clips: (ls.match(/clip-path="url\(#[^)]*tkclip\)"/g) || []).length,
      cones: all(b, 'path').filter(e => (e.getAttribute('fill') || '') === '#FF7A2E').length, groundY: 165 }; b.remove(); }catch(e){ out.err = (out.err || '') + String(e).slice(0, 120) + ' '; }
  /* D. top of the ladder, ten in a row */
  try{ const b = mount('level80'); const lad = b.querySelector('.fb-ladder'), roof = b.querySelector('.fb-roof'), ff = all(b, '.fb-ff').map(R);
    const L = lad && R(lad), O = roof && R(roof), rungs = ((b.querySelector('.fb-rung') || { getAttribute: () => '' }).getAttribute('d').match(/M/g) || []).length;
    out.D1 = { ladder: L && { x: r1(L.x), y: r1(L.y), r: r1(L.r), b: r1(L.b) }, roof: O && { x: r1(O.x), y: r1(O.y), r: r1(O.r) }, rungs, ff: ff.map(r => ({ cx: r1(r.cx), b: r1(r.b), y: r1(r.y) })), svg: b.innerHTML.length,
      fire: /#E8481E|#FF8A1E/.test(layerStr('level80')), hose: /#B5121B/.test(layerStr('level80')) }; b.remove(); }catch(e){ out.err = (out.err || '') + String(e).slice(0, 120) + ' '; }
  try{ const b = mount('exam100'); const g = all(b, '.fb-gauge').map(R), nd = all(b, '.fb-needle').map(e => +e.getAttribute('data-frac'));
    const lamps = all(b, '.fb-lamp').map(R), plates = all(b, '.fb-plate').map(R);
    out.D2 = { gauges: g.length, xs: g.map(r => r1(r.cx)), ys: g.map(r => r1(r.cy)), needles: nd, lamps: lamps.length, plates: plates.length, ff: all(b, '.fb-ff').length,
      fire: /#E8481E|#FF8A1E/.test(layerStr('exam100')), hose: /#B5121B/.test(layerStr('exam100')) }; b.remove(); }catch(e){ out.err = (out.err || '') + String(e).slice(0, 120) + ' '; }
  /* E. fire investigator's tape */
  try{ const b = mount('correct10000'); const band = b.querySelector('.fb-tape-band'), tp = b.querySelector('.fb-tape'), back = b.querySelector('.fb-tape-back');
    const Bd = band && R(band), turns = all(b, '.fb-turn').map(R), knots = all(b, '.fb-knot').map(R), Tp = tp && R(tp);
    const nums = band ? band.getAttribute('d').match(/-?\d+\.?\d*/g).map(Number) : [];
    const ys = []; for(let i = 1; i < nums.length; i += 2) ys.push(nums[i]);
    const post = all(b, 'rect').filter(e => e.getAttribute('x') === '449' && e.getAttribute('width') === '6' && e.getAttribute('height') === '146')[0];
    const door = all(b, 'rect').filter(e => e.getAttribute('x') === '40' && e.getAttribute('width') === '112')[0];
    out.E = { band: Bd && { x: r1(Bd.x), y: r1(Bd.y), r: r1(Bd.r), b: r1(Bd.b) }, letters: tp ? tp.querySelectorAll('path').length : 0, lettersBox: Tp && { x: r1(Tp.x), y: r1(Tp.y), r: r1(Tp.r), b: r1(Tp.b) },
      backLen: back ? (back.getAttribute('d') || '').length : 0, turns: turns.map(r => r1(r.cx)), knots: knots.length, post: post ? R(post).x : null, doorRight: door ? R(door).r : null,
      sag: ys.length ? r1(Math.max.apply(null, ys.filter((_, i) => i > ys.length * .3 && i < ys.length * .7)) - ys[0]) : 0, firstY: ys[0], lastY: ys[ys.length - 1],
      oldTop: /M149 33|M452 25/.test(layerStr('correct10000')) }; b.remove(); }catch(e){ out.err = (out.err || '') + String(e).slice(0, 120) + ' '; }
  /* F. after hours */
  try{ const b = mount('early10'); const bm = b.querySelector('.fb-beam'), wh = b.querySelector('.fb-wheel'), gg = b.querySelector('.fb-gauge'), tg = b.querySelector('.fb-tag'), ck = b.querySelector('.fb-clock');
    const Bm = bm && R(bm), W = wh && R(wh), G = gg && R(gg), Tg = tg && R(tg);
    const inside = (A, c) => !!(A && c && c.cx >= A.x && c.cx <= A.r && c.cy >= A.y && c.cy <= A.b);
    out.F = { beam: Bm && { x: r1(Bm.x), y: r1(Bm.y), r: r1(Bm.r), b: r1(Bm.b) }, wheel: !!W, gauge: !!G, tag: !!Tg, tagCheck: !!(tg && /fill="none"|stroke="#FFFFFF"/.test(tg.innerHTML) && tg.querySelectorAll('path').length >= 2),
      wheelLit: inside(Bm, W), gaugeLit: inside(Bm, G), tagLit: inside(Bm, Tg), time: ck ? ck.getAttribute('data-time') : null, thermal: /iron|hot\b/.test(layerStr('early10')) || /#FF8AD0/i.test(layerStr('early10')), b: b.innerHTML.length }; b.remove(); }catch(e){ out.err = (out.err || '') + String(e).slice(0, 120) + ' '; }
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
    G = pg.evaluate(GEO)
    ctx.close(); br.close()
srv.shutdown()
if DUMP:
    print(json.dumps(F["hashes"], indent=1)); sys.exit(0)
chk("(1) the page is Fire Code (%s), every banner draws with a tint, no page errors" % F["cls"], F["cls"] == "ifc" and not F["errs"] and not perr and all(F["tint"].values()), (F["errs"], perr))
bad = {i: (F["names"].get(i), n) for i, n in NAMES.items() if F["names"].get(i) != n}
chk("(1) each banner is named for its challenge (%d wrong)" % len(bad), not bad, bad)
same = [i for i in REDONE if PREV.get(i) and F["hashes"].get(i) == PREV[i]]
chk("(2) every redrawn banner differs from 976c414 (the build before round 3) (unchanged: %s; %d hashes known)" % (same, len(PREV)), PREV and not same, same)
moved = [i for i in KEEP if PREV.get(i) and F["hashes"].get(i) != PREV[i]]
chk("(2) Downpour, Nebula, Star Ranger and the rank banners are as they were (changed: %s)" % moved, PREV and not moved, moved)
S = F["shape"]
chk("(4) Certified has its CERTIFIED lettering, no flag poles, and twenty challenge coins (%s)" % F["coins"], F["text"]["cert"] and not F["flags"] and F["coins"] == 20, (F["text"]["cert"], F["flags"], F["coins"]))
chk("(4) Plan Review has its title block", F["text"]["plan"], F["text"])
chk("(4) On Call reads SYSTEMS NORMAL, has a pull station, and no wall clock or tag (%s)" % F["text"], F["text"]["sysnorm"] and F["text"]["pull"] and not F["text"]["clock"], F["text"])
chk("(4) Mutual Aid has its five unit chips (%s), five station rings (%s) and its yellow line ends on the incident (%s)" % (S["chips"], F["stations"], F["yellowEnd"]), S["chips"] >= 5 and F["stations"] == 5 and F["yellowEnd"], S)
L = F["layers"]
chk("(5) Grand Finale is a composition, not a sky of them: four to six shells on their own clocks (%s; there were 13), and the truck wears ghost lettering (%s)" % (F["fwk"], F["ghost"]), 4 <= F["fwk"] <= 6 and F["ghost"], (F["fwk"], F["ghost"]))
chk("(7) After Hours and Fire Investigator share no long shape (%s) and After Hours is still the colder picture (by more than .15; the warm beam and red valve took it from .26 to .21 over) (%s)" % (F["sharedAH"], F["cold"]),
    F["sharedAH"] == 0 and F["cold"]["early10"] - F["cold"]["correct10000"] > .15, F["cold"])
fl = ["flare_void", "flare_umbra", "flare_horizon", "flare_genesis"]
chk("(8) the four secret flares are four scenes (shared long shapes %s, hashes %s)" % (F["sharedFlares"], len(set(F["hashes"][i] for i in fl))), F["sharedFlares"] == 0 and len(set(F["hashes"][i] for i in fl)) == 4, F["sharedFlares"])
C = F["colours"]
chk("(8) each carries its character's colour",
    all(c in C["flare_void"] for c in ["#EF4444", "#F97316", "#FACC15"]) and "#8B5CF6" in C["flare_umbra"] and "#CFEAFF" in C["flare_horizon"] and "#FF5CA8" in C["flare_genesis"], {k: v[:0] for k, v in C.items()})
chk("(9) no svg filter in the redrawn (%s); ids per copy (%s); every url(#) resolves (%s)" % (F["filters"], F["idClash"], F["unresolved"]), not F["filters"] and not F["idClash"] and not F["unresolved"])
heavy = {i: F["weight"][i] for i in REDONE if F["weight"][i][0] > 700 or F["weight"][i][1] > 24}
chk("(9) none of the redrawn is heavier than 700 elements or 24 layers (%s)" % {i: F["weight"][i] for i in REDONE}, not heavy, heavy)
chk("(10) the sign-writer's grid has P K W V G, the figures and the percent sign (missing: %s)" % F["glyphs"], not F["glyphs"], F["glyphs"])

# ---- (11) round 3b, measured on the page itself ----
G = G or {}
same2 = [i for i in R3B if PREV2.get(i) and F["hashes"].get(i) == PREV2[i]]
chk("(11) the seven banners redrawn in round 3b (items A to F) differ from c8143d5 (unchanged: %s; %d hashes known)" % (same2, len(PREV2)), PREV2 and not same2, same2)
rest = [i for i in NAMES if i not in R3B and i != "flare_horizon"]   # Pulsar is being redrawn with its character, in another branch
moved2 = [i for i in rest if PREV2.get(i) and F["hashes"].get(i) != PREV2[i]]
chk("(11) nothing else moved since c8143d5 (changed: %s) (Pulsar is another branch's)" % moved2, PREV2 and not moved2, moved2)
A = G.get("A", {})
chk("(11) INSPECTION TEAM: five inspectors (%s), in a row on the apron (feet %s), five different heights (%s), a clear gap between each (%s), two beams (%s), a FIRE STATION sign and no ENGINE COMPANY plaque (%s)" %
    (A.get("n"), A.get("feet"), A.get("heights"), A.get("overlap"), A.get("beams"), F["text"].get("fireStation")),
    A.get("n") == 5 and max(A["feet"]) - min(A["feet"]) < 3 and len(set(round(h / 3) for h in A["heights"])) >= 4 and max(A["overlap"]) <= -4 and A.get("beams") == 2
    and F["text"]["fireStation"] and not F["text"]["engine"], (A, F["text"]))
B = G.get("B", {})
chk("(11) PERFECT SCORE: a lit 1, 0, 0 (lit segments %s, a 1 has two, a 0 six) and a percent sign (%s), ten lamps all lit (%s of %s), UNIT SCORE over it (%s), and neither the door nor the COMPLIANT tag (%s)" %
    (B.get("segs"), B.get("pct"), B.get("lampsLit"), B.get("lamps"), F["text"].get("unitScore"), F["text"].get("oldCompliant")),
    B.get("segs") == [2, 6, 6] and B.get("pct") == 1 and B.get("lamps") == 10 and B.get("lampsLit") == 10 and F["text"]["unitScore"] and not F["text"]["oldCompliant"], B)
C = G.get("C", {})
ty = C.get("tyres") or []; bd = C.get("body") or {}
chk("(11) GRAND FINALE'S TRUCK: a body %sx%s, %s long for every 1 from the ground to its roof (a Silverado is 3.0), two tyres (%s) each standing ON the ground (bottom y %s = %s) and inside the body's length, two door windows (%s), ghost lettering (%s), a roof bar (%s)" %
    (bd.get("w"), bd.get("h"), C.get("ratio"), len(ty), [t["bottom"] for t in ty], C.get("groundY"), C.get("glass"), C.get("ghost"), C.get("bar")),
    C.get("truck") and 2.85 <= C.get("ratio", 0) <= 3.25 and len(ty) == 2 and all(abs(t["bottom"] - C["groundY"]) <= .8 for t in ty) and all(bd["x"] < t["cx"] < bd["x"] + bd["w"] for t in ty)
    and C.get("glass") == 2 and C.get("ghost") and C.get("bar"), C)
chk("(11) GRAND FINALE'S FIREWORKS: a soft glow behind every burst (%s glow discs for six bursts), and their light on the truck's body clipped to it (%s layers) and %s shells on their own clocks" % (C.get("glows"), C.get("clips"), F["fwk"]),
    C.get("glows", 0) >= 6 and C.get("clips", 0) >= 2 and 4 <= F["fwk"] <= 6, C)
D1 = G.get("D1", {}); D2 = G.get("D2", {})
lad = D1.get("ladder") or {}; roof = D1.get("roof") or {}; ff = D1.get("ff") or []
chk("(11) TOP OF THE LADDER: a ladder of %s rungs whose top (y %s) reaches the roof edge (y %s) and whose end is on the roof (x %s to %s), one firefighter standing on that roof (%s), no hose and no fire in it (fire %s, hose %s)" %
    (D1.get("rungs"), lad.get("y"), roof.get("y"), lad.get("r"), roof.get("x"), ff, D1.get("fire"), D1.get("hose")),
    D1.get("rungs", 0) >= 12 and abs(lad.get("y", -99) - roof.get("y", 99)) <= 9 and roof.get("x", 999) <= lad.get("r", -999) <= roof.get("r", -999) and len(ff) == 1 and abs(ff[0]["b"] - roof["y"]) <= 6 and roof["x"] <= ff[0]["cx"] <= roof["r"]
    and not D1.get("fire") and not D1.get("hose"), D1)
xs = D2.get("xs") or []
chk("(11) TEN IN A ROW: ten gauges (%s) in one row (y %s) at an even pitch (%s), ten needles in the green (%s), ten lit lamps (%s), ten plates (%s), the heading (%s), no firefighter, hose or fire (%s)" %
    (D2.get("gauges"), sorted(set(D2.get("ys") or [])), [round(b - a, 1) for a, b in zip(xs, xs[1:])], D2.get("needles"), D2.get("lamps"), D2.get("plates"), F["text"].get("tenAced"), (D2.get("ff"), D2.get("fire"), D2.get("hose"))),
    D2.get("gauges") == 10 and len(set(D2["ys"])) == 1 and max(b - a for a, b in zip(xs, xs[1:])) - min(b - a for a, b in zip(xs, xs[1:])) < 1 and len(D2["needles"]) == 10 and all(.52 < n <= 1 for n in D2["needles"])
    and D2.get("lamps") == 10 and D2.get("plates") == 10 and F["text"]["tenAced"] and not D2.get("ff") and not D2.get("fire") and not D2.get("hose"), D2)
chk("(11) Level 80 and Ten in a Row are no longer 'the exact same one' (a firefighter with a hose at a burning building): neither has fire or a hose (Top of the Ladder fire %s hose %s; Ten in a Row fire %s hose %s) or a firefighter at the gauges (%s), and they share no long shape (%s)" %
    (D1.get("fire"), D1.get("hose"), D2.get("fire"), D2.get("hose"), D2.get("ff"), F["sharedLE"]),
    not (D1.get("fire") or D1.get("hose") or D2.get("fire") or D2.get("hose") or D2.get("ff")) and F["sharedLE"] == 0, (D1, D2))
E = G.get("E", {}); band = E.get("band") or {}
chk("(11) FIRE INVESTIGATOR'S TAPE hangs at chest height: its band runs y %s to %s (the investigator's chest is about y 85 and his waist y 112; the old tape ran y 16 to 50), from x %s to x %s" % (band.get("y"), band.get("b"), band.get("x"), band.get("r")),
    band and 84 <= band["y"] and band["b"] <= 135 and 90 <= (band["y"] + band["b"]) / 2 <= 125 and not E.get("oldTop"), E)
chk("(11) ...tied at both ends: the jamb (the doorway's right edge x %s) and the post (x %s) each have two turns of tape (turns at x %s) and a knot (%s knots), and the band reaches both" % (E.get("doorRight"), E.get("post"), E.get("turns"), E.get("knots")),
    E.get("turns") and sorted(E["turns"]) and len([t for t in E["turns"] if abs(t - E["doorRight"]) <= 6]) >= 2 and len([t for t in E["turns"] if E["post"] - 4 <= t <= E["post"] + 10]) >= 2 and E.get("knots") == 2
    and band["x"] <= E["doorRight"] and band["r"] >= E["post"], E)
chk("(11) ...sagging (%s units lower in the middle than at the jamb) with one twist (the back of the tape shows: %s), and lettered whole: %s glyphs inside the picture (%s)" % (E.get("sag"), E.get("backLen"), E.get("letters"), E.get("lettersBox")),
    E.get("sag", 0) >= 6 and E.get("backLen", 0) > 20 and E.get("letters", 0) >= 30 and E.get("lettersBox") and E["lettersBox"]["x"] >= 0 and E["lettersBox"]["r"] <= 480 and E["lettersBox"]["y"] >= 0 and E["lettersBox"]["b"] <= 180, E)
Fh = G.get("F", {}); bm = Fh.get("beam") or {}
tm = (Fh.get("time") or "0:0").split(":"); mins = int(tm[0]) * 60 + int(tm[1])
chk("(11) AFTER HOURS: a flashlight beam (x %s to %s) that lands on the valve's handwheel (%s), the gauge (%s) and the PASSED tag (%s); the sign reads SPRINKLER RISER, the clock %s is near eleven; no thermal camera (%s), no 187F or PANEL 4B (%s)" %
    (bm.get("x"), bm.get("r"), Fh.get("wheelLit"), Fh.get("gaugeLit"), Fh.get("tagLit"), Fh.get("time"), Fh.get("thermal"), (F["text"]["old187"], F["text"]["oldPanel"])),
    Fh.get("wheel") and Fh.get("gauge") and Fh.get("tag") and Fh.get("wheelLit") and Fh.get("gaugeLit") and Fh.get("tagLit") and 10 * 60 + 40 <= mins <= 11 * 60 + 15 and not Fh.get("thermal")
    and not F["text"]["old187"] and not F["text"]["oldPanel"], Fh)
chk("(11) the round 3b art had no page error while it was measured (%s)" % G.get("err"), not G.get("err"), G.get("err"))
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
