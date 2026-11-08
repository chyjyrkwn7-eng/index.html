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

(12) BUILD 384 ROUND 4 (Madison's review of round 3b, seven banners): INSPECTION TEAM (five inspectors outside a lit building, hats, vests with bands, hands that
     hold clipboards, flashlights with lenses and beams that start at them), CERTIFICATE OF MERIT (was Perfect Score: a framed certificate with a stamp and a seal on a wire
     from a nail, an inspector with his hand on the frame and a stamp raised), GRAND FINALE (no truck: seven inspectors on a crest, six uneven fireworks, three rising shells),
     TEN IN A ROW (a connected header, riser, ten branches with valves, flow switches, gauges, lamps, conduits and zone plates), TOP OF THE LADDER (an inspector, not a firefighter,
     on the roof), FIRE INVESTIGATOR's tape (no knots, one wrap at each end, lettered the whole length), AFTER HOURS' tag (a blue inspection tag with rows, boxes and punches).
     Every one differs from c1d224b (prev3.json) and nothing else moved.

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
NAMES = {"tests100": "Certified", "tests250": "Plan Review", "tests500": "Inspection Team", "hundos100": "Certificate of Merit", "hundos250": "Grand Finale",
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
  /* the still pictures, mounted 1:1 (a unit is a pixel) so the app's own drawing can be measured */
  const mount = id => { const box = document.createElement('div'); box.style.cssText = 'position:fixed;left:0;top:0;width:480px;height:180px;overflow:hidden;z-index:99999';
    box.innerHTML = bannerStaticSVG(id) || ''; document.body.appendChild(box); const sv = box.querySelector('svg'); if(sv){ sv.setAttribute('width', 480); sv.setAttribute('height', 180); sv.setAttribute('preserveAspectRatio', 'none'); } return box; };
  const R = e => { const r = e.getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height, r: r.right, b: r.bottom, cx: r.left + r.width / 2, cy: r.top + r.height / 2 }; };
  const r1 = v => Math.round(v * 10) / 10;
  const all = (b, sel) => [...b.querySelectorAll(sel)];
  const nums = d => (d.match(/-?\d+\.?\d*/g) || []).map(Number);
  const near = (A, B, m) => A.x - m <= B.r && B.x - m <= A.r && A.y - m <= B.b && B.y - m <= A.b;
  const out = {};
  const layerStr = id => { try{ const a = BANNER_ART[id]('gq'); return Array.isArray(a) ? a.map(l => (l.svg || '') + (l.kids || []).map(k => k.svg || '').join('')).join('') : String(a); }catch(e){ return ''; } };
  const tp = (s, cx, cy, h) => { try{ return fbTextPath(s, cx, cy, h); }catch(e){ return ''; } };
  const ls = {}; ['tests500', 'hundos100', 'hundos250', 'exam100', 'level80', 'early10', 'correct10000'].forEach(id => ls[id] = layerStr(id));
  /* the inspector: hat, vest with bands, hands; and what each hand holds */
  const person = (b, ins) => { const hat = all(ins, '.fb-hat').length, vest = all(ins, '.fb-vest').length, bands = all(ins, '.fb-band').reduce((a, e) => a + (e.getAttribute('d').match(/M/g) || []).length, 0), hands = all(ins, '.fb-hands'); return { hat, vest, bands, hands: hands.length }; };
  /* A. inspection team: outside a building, five people, what each holds */
  try{ const b = mount('tests500'); const ins = all(b, '.fb-inspector').sort((p, q) => R(p).cx - R(q).cx); const rs = ins.map(R);
    const hats = ins.map(i => R(i.querySelector('.fb-hat'))), vests = ins.map(i => R(i.querySelector('.fb-vest')));
    const boards = all(b, '.fb-board'), hands = all(b, '.fb-hands > *').map(R);
    const torches = all(b, '.fb-torch'), lenses = all(b, '.fb-lens').map(R);
    const beams = all(b, '.fb-beam').map(e => { const n = nums(e.getAttribute('d')); return [(n[0] + n[n.length - 2]) / 2, (n[1] + n[n.length - 1]) / 2]; });
    out.A = { n: ins.length, per: ins.map(i => person(b, i)), feet: rs.map(r => r1(r.b)), heights: hats.map((h, i) => r1(rs[i].b - h.y)), vestGap: vests.slice(1).map((v, i) => r1(v.x - vests[i].r)),
      boards: boards.map(bd => { const B = R(bd); return { w: r1(B.w), h: r1(B.h), held: hands.some(h => near(B, h, 1.5) && h.w < 12) }; }),
      torches: torches.length, lenses: lenses.length, lensToBeam: beams.map(p => Math.min.apply(null, lenses.map(l => r1(Math.hypot(l.cx - p[0], l.cy - p[1]))))), beams: beams.length,
      torchHeld: torches.map(t => [...t.querySelectorAll('path')].some(p => /^#(C98E64|8E5C3E|E0AC86|A86E4A|D49A72)$/i.test(p.getAttribute('fill') || ''))),
      windows: all(b, '.fb-window').reduce((a, e) => a + (e.getAttribute('d').match(/M/g) || []).length, 0), door: all(b, '.fb-door').length, lamp: all(b, '.fb-lamppost').length,
      fireStation: ls.tests500.indexOf(tp('FIRE STATION', 240, 38.6, 7.4)) >= 0, oldDoors: ls.tests500.indexOf('#3A4460') >= 0 }; b.remove(); }catch(e){ out.err = (out.err || '') + 'A ' + String(e).slice(0, 120) + ' '; }
  /* B. certificate of merit */
  try{ const b = mount('hundos100'); const fr = R(b.querySelector('.fb-cert-frame')), ce = R(b.querySelector('.fb-cert')), st = R(b.querySelector('.fb-stamp')), se = R(b.querySelector('.fb-seal')), na = R(b.querySelector('.fb-nail'));
    const wn = nums(b.querySelector('.fb-wire').getAttribute('d')), man = b.querySelector('.fb-inspector'), M = R(man), tool = R(b.querySelector('.fb-stamptool')), head = R(man.querySelector('.fb-hat'));
    const handsEl = all(man, '.fb-hands > *').map(R);
    out.B = { frame: { x: r1(fr.x), y: r1(fr.y), r: r1(fr.r), b: r1(fr.b), w: r1(fr.w), h: r1(fr.h) }, certInFrame: ce.x > fr.x && ce.r < fr.r && ce.y > fr.y && ce.b < fr.b, stampInCert: st.x >= ce.x - 1 && st.r <= ce.r + 1 && st.y >= ce.y && st.b <= ce.b,
      sealInCert: se.x >= ce.x && se.r <= ce.r && se.y >= ce.y && se.cy < ce.b, wire: [[wn[2], wn[3]], [wn[6], wn[7]]].map(p => [r1(p[0]), r1(p[1])]), wireStart: [r1(wn[0]), r1(wn[1])], nail: { x: r1(na.x), r: r1(na.r), b: r1(na.b) },
      wireOk: [[wn[2], wn[3]], [wn[6], wn[7]]].every(p => Math.abs(p[1] - fr.y) <= 1.6 && p[0] > fr.x && p[0] < fr.r) && wn[1] >= na.y && wn[1] <= na.b && wn[0] >= na.x && wn[0] <= na.r,
      handOnFrame: handsEl.some(h => h.x <= fr.r + 1 && h.r >= fr.r - 1 && h.cy > fr.y && h.cy < fr.b), toolAboveHead: tool.y < head.y - 4, person: person(b, man),
      heading: ls.hundos100.indexOf(tp('CERTIFICATE', 257, 44, 7)) >= 0, merit: ls.hundos100.indexOf(tp('OF MERIT', 257, 53.4, 5.6)) >= 0, sign: ls.hundos100.indexOf(tp('FIRE MARSHAL', 93, 29.2, 7)) >= 0, pct: ls.hundos100.indexOf(tp('100%', 278, 86.4, 9.4)) >= 0,
      scoreboard: !!b.querySelector('.fb-seg') || ls.hundos100.indexOf(tp('UNIT SCORE', 240, 33.6, 7.4)) >= 0, lanternAndLit: /fb-seal/.test(ls.hundos100) }; b.remove(); }catch(e){ out.err = (out.err || '') + 'B ' + String(e).slice(0, 120) + ' '; }
  /* C. grand finale */
  try{ const b = mount('hundos250'); const art = BANNER_ART.hundos250('gq'); const fw = art.filter(l => /bl-fwk/.test(l.cls || ''));
    const cs = fw.map(l => ({ cx: l.o[0], cy: l.o[1], R: l.box[2] / 3.8, spokes: ((l.svg.match(/class="fb-spokes" d="([^"]*)"/) || [0, ''])[1].match(/Q/g) || []).length, glow: /<circle cx="[^"]*" cy="[^"]*" r="[^"]*" fill="url\(#gq/.test(l.svg), top: l.box[1] }));
    const ins = all(b, '.fb-inspector').map(R), tops = ins.map(r => r.y).sort((p, q) => p - q), med = tops[Math.floor(tops.length / 2)];
    out.C = { bursts: cs.map(c => ({ x: r1(c.cx), y: r1(c.cy), R: r1(c.R), n: c.spokes, glow: c.glow })), men: ins.length, feet: ins.map(r => r1(r.b)), raised: ins.filter(r => r.y < med - 8).length, hats: all(b, '.fb-hat').length, bands: all(b, '.fb-band').length,
      rises: all(b, '.fb-rise').length, truck: !!b.querySelector('.fb-truck') || !!b.querySelector('.fb-tyre') || /tkbody/.test(ls.hundos250), clock: fw.map(l => /animation-duration:([\d.]+)s/.exec(l.style)[1]), glowAlways: cs.every(c => c.glow) }; b.remove(); }catch(e){ out.err = (out.err || '') + 'C ' + String(e).slice(0, 120) + ' '; }
  /* D. ten in a row: a connected system */
  try{ const b = mount('exam100'); const H = R(b.querySelector('.fb-header')), rz = R(b.querySelector('.fb-riser')), br = all(b, '.fb-branch').map(R), ga = all(b, '.fb-gauge').map(R), la = all(b, '.fb-lamp').map(R), pl = all(b, '.fb-plate').map(R),
      rods = all(b, '.fb-rod').map(R), co = all(b, '.fb-conduit').map(R), fs = all(b, '.fb-flowsw').map(R), va = all(b, '.fb-valve').map(R), nd = all(b, '.fb-needle').map(e => +e.getAttribute('data-frac'));
    const ok = (a, f) => a.length === 10 && a.every(f);
    out.D = { n: { branches: br.length, gauges: ga.length, lamps: la.length, plates: pl.length, rods: rods.length, conduits: co.length, flow: fs.length, valves: va.length, needles: nd.length },
      header: { x: r1(H.x), r: r1(H.r), y: r1(H.y), b: r1(H.b), h: r1(H.h) }, riserTouchesHeader: rz.y <= H.b + 1 && rz.cx > H.x && rz.cx < H.r, riserOnFloor: r1(rz.b),
      branchOnHeader: ok(br, r => r.b >= H.y - 1 && r.cx > H.x && r.cx < H.r), branchToGauge: ok(br, (r, i) => r.y <= ga[i].b + 1 && r.y >= ga[i].cy), aligned: ok(br, (r, i) => Math.abs(r.cx - ga[i].cx) < 1.2 && Math.abs(r.cx - la[i].cx) < 1.2 && Math.abs(r.cx - pl[i].cx) < 1.2 && Math.abs(r.cx - (va[i] || { cx: -99 }).cx) < 1.2),
      flowOnBranch: ok(fs, (f, i) => near(f, br[i], 1)), conduitJoins: ok(co, (c, i) => near(c, la[i], 1.6) && near(c, fs[i], 1.6)), platesHung: ok(pl, (p, i) => rods[i] && rods[i].y <= H.b + 1 && rods[i].b >= p.y - 1 && rods[i].x >= p.x && rods[i].r <= p.r),
      pitch: br.slice(1).map((r, i) => r1(r.cx - br[i].cx)), needles: nd, lampsLit: all(b, '.fb-lamp').every(e => /^#5CFFA6$/i.test(e.getAttribute('fill'))), heading: ls.exam100.indexOf(tp('TEN UNITS IN A ROW', 240, 18, 6)) >= 0,
      clipboard: /gqboard/.test(ls.exam100), oldHeading: ls.exam100.indexOf(tp('10 UNITS ACED IN A ROW', 240, 29.2, 6.4)) >= 0 }; b.remove(); }catch(e){ out.err = (out.err || '') + 'D ' + String(e).slice(0, 120) + ' '; }
  /* E. top of the ladder: an inspector, not a firefighter */
  try{ const b = mount('level80'); const lad = b.querySelector('.fb-ladder'), roof = b.querySelector('.fb-roof'), ins = all(b, '.fb-inspector');
    const L = lad && R(lad), O = roof && R(roof), rungs = ((b.querySelector('.fb-rung') || { getAttribute: () => '' }).getAttribute('d').match(/M/g) || []).length, I = ins[0] && R(ins[0]);
    const bd = b.querySelector('.fb-board'), hands = ins[0] ? all(ins[0], '.fb-hands > *').map(R) : [];
    out.E = { ladder: L && { y: r1(L.y), r: r1(L.r) }, roof: O && { x: r1(O.x), y: r1(O.y), r: r1(O.r) }, rungs, inspectors: ins.length, firefighters: all(b, '.fb-ff').length, feetOnRoof: I && O ? r1(I.b - O.y) : null, onRoofX: !!(I && O && I.cx > O.x && I.cx < O.r),
      person: ins[0] ? person(b, ins[0]) : null, board: !!bd, boardHeld: !!(bd && hands.some(h => near(R(bd), h, 1.5) && h.w < 12)), fire: /#E8481E|#FF8A1E/.test(ls.level80), hose: /#B5121B/.test(ls.level80) }; b.remove(); }catch(e){ out.err = (out.err || '') + 'E ' + String(e).slice(0, 120) + ' '; }
  /* F. fire investigator's tape: wrapped once at each end, no knot, lettered along the whole length */
  try{ const b = mount('correct10000'); const band = b.querySelector('.fb-tape-band'), tg = b.querySelector('.fb-tape'), wr = all(b, '.fb-wrap').map(R);
    const Bd = R(band), gl = [...tg.children].map(R).sort((p, q) => p.x - q.x), gaps = gl.slice(1).map((g, i) => g.x - gl[i].r);
    const post = all(b, 'rect').filter(e => e.getAttribute('x') === '449' && e.getAttribute('width') === '6' && e.getAttribute('height') === '146')[0], door = all(b, 'rect').filter(e => e.getAttribute('x') === '40' && e.getAttribute('width') === '112')[0];
    const ys = nums(band.getAttribute('d')).filter((_, i) => i % 2); 
    out.F = { band: { x: r1(Bd.x), y: r1(Bd.y), r: r1(Bd.r), b: r1(Bd.b) }, knots: all(b, '.fb-knot').length, turns: all(b, '.fb-turn').length, back: all(b, '.fb-tape-back').length, wraps: wr.map(r => ({ cx: r1(r.cx), w: r1(r.w) })), post: post ? R(post).cx : null, doorRight: door ? R(door).r : null,
      glyphs: gl.length, firstGap: r1(gl[0].x - (wr[0] ? wr[0].r : 0)), lastGap: r1((wr[1] ? wr[1].x : 0) - gl[gl.length - 1].r), maxGap: r1(Math.max.apply(null, gaps)), sag: r1(Math.max.apply(null, ys.filter((_, i) => i > ys.length * .3 && i < ys.length * .7)) - ys[0]) }; b.remove(); }catch(e){ out.err = (out.err || '') + 'F ' + String(e).slice(0, 120) + ' '; }
  /* G. after hours: the beam still reaches the valve, gauge and tag; the tag is a blue inspection tag */
  try{ const b = mount('early10'); const bm = b.querySelector('.fb-beam'), wh = b.querySelector('.fb-wheel'), gg = b.querySelector('.fb-gauge'), tg = b.querySelector('.fb-tag'), ck = b.querySelector('.fb-clock');
    const Bm = bm && R(bm), W = wh && R(wh), G2 = gg && R(gg), Tg = tg && R(tg);
    const inside = (A, c) => !!(A && c && c.cx >= A.x && c.cx <= A.r && c.cy >= A.y && c.cy <= A.b);
    const hole = b.querySelector('.fb-hole'), str = b.querySelector('.fb-string'), sn = str ? nums(str.getAttribute('d')) : [], Ho = hole && R(hole);
    const gm = /id="gqtagb">(?:<stop[^>]*stop-color="(#[0-9A-Fa-f]{6})"[^>]*\/>)+/.exec(ls.early10), cols = ((/id="gqtagb"[^>]*>(.*?)<\/linearGradient>/.exec(ls.early10) || [0, ''])[1].match(/#[0-9A-Fa-f]{6}/g) || []);
    const blue = cols.length > 0 && cols.every(h => { const n = parseInt(h.slice(1), 16); return (n & 255) > (n >> 16 & 255) * 1.5; });
    out.G = { beam: Bm && { x: r1(Bm.x), r: r1(Bm.r) }, wheel: !!W, gauge: !!G2, tag: !!Tg, wheelLit: inside(Bm, W), gaugeLit: inside(Bm, G2), tagLit: inside(Bm, Tg), time: ck ? ck.getAttribute('data-time') : null,
      rows: all(b, '.fb-tagrows').reduce((a, e) => a + (e.getAttribute('d').match(/M/g) || []).length, 0), boxes: all(b, '.fb-tagbox').length, ticks: all(b, '.fb-tagticks').reduce((a, e) => a + (e.getAttribute('d').match(/M/g) || []).length, 0), punches: all(b, '.fb-punch').length,
      stringEnd: sn.length ? [r1(sn[sn.length - 2]), r1(sn[sn.length - 1])] : null, hole: Ho && [r1(Ho.cx), r1(Ho.cy)], stringToHole: Ho && sn.length ? r1(Math.hypot(sn[sn.length - 2] - Ho.cx, sn[sn.length - 1] - Ho.cy)) : null,
      stringStartToWheel: W && sn.length ? r1(Math.hypot(sn[0] - W.cx, sn[1] - W.cy)) : null, wheelR: W && r1(W.w / 2), blue, cols, header: ls.early10.indexOf(tp('INSPECTION', 414, 113.2, 2.6)) >= 0, ok: ls.early10.indexOf(tp('OK', 414, 137, 5.6)) >= 0,
      thermal: /iron|hot\b/.test(ls.early10) || /#FF8AD0/i.test(ls.early10) }; b.remove(); }catch(e){ out.err = (out.err || '') + 'G ' + String(e).slice(0, 120) + ' '; }
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
chk("(5) Grand Finale is a composition: four to six shells on their own clocks (%s; there were 13) and no truck (round 4 took it out)" % F["fwk"], 4 <= F["fwk"] <= 6, F["fwk"])
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
# ---- (12) round 4 (Madison's review of round 3b), measured on the page itself ----
PREV3 = {}
try: PREV3 = json.load(open(os.path.join(HERE, "check-b384-fcbanners.prev3.json")))
except Exception: pass
R4 = ["tests500", "hundos100", "hundos250", "level80", "exam100", "early10", "correct10000"]
same3 = [i for i in R4 if PREV3.get(i) and F["hashes"].get(i) == PREV3[i]]
chk("(12) the seven banners redrawn in round 4 differ from c1d224b (unchanged: %s; %d hashes known)" % (same3, len(PREV3)), PREV3 and not same3, same3)
moved3 = [i for i in NAMES if i not in R4 and PREV3.get(i) and F["hashes"].get(i) != PREV3[i]]
chk("(12) nothing else moved since c1d224b (changed: %s)" % moved3, PREV3 and not moved3, moved3)
A = G.get("A", {}); per = A.get("per") or []
chk("(12) INSPECTION TEAM, outside: five inspectors (%s) each with a hard hat, a hi-vis vest, its reflective bands (%s sub-shapes) and hands, on one pavement line (feet %s), five different heights (%s), a clear gap between vests (%s)" %
    (A.get("n"), [p["bands"] for p in per], A.get("feet"), A.get("heights"), A.get("vestGap")),
    A.get("n") == 5 and len(per) == 5 and all(p["hat"] == 1 and p["vest"] == 1 and p["bands"] >= 6 and p["hands"] == 1 for p in per) and max(A["feet"]) - min(A["feet"]) < 2 and len(set(round(h / 4) for h in A["heights"])) >= 4 and min(A["vestGap"]) >= 12, A)
chk("(12) ...the building is behind them (%s lit-window sub-shapes, a door %s, a street lamp %s), and it is not a fire station (FIRE STATION lettering %s, old bay doors %s)" % (A.get("windows"), A.get("door"), A.get("lamp"), A.get("fireStation"), A.get("oldDoors")),
    A.get("windows", 0) >= 20 and A.get("door") == 1 and A.get("lamp") == 1 and not A.get("fireStation") and not A.get("oldDoors"), A)
chk("(12) ...clipboards are HELD: %s boards, each with a hand on its edge (%s); flashlights are real objects (%s torches, each with a lens, each in a fist: %s) and each beam starts at its lens (distance %s, %s beams)" %
    (len(A.get("boards") or []), [b["held"] for b in A.get("boards") or []], A.get("torches"), A.get("torchHeld"), A.get("lensToBeam"), A.get("beams")),
    len(A.get("boards") or []) >= 2 and all(b["held"] for b in A["boards"]) and A.get("torches") == 2 and A.get("lenses") == 2 and all(A["torchHeld"]) and A.get("beams") == 2 and max(A["lensToBeam"]) <= 4, A)
B = G.get("B", {})
chk("(12) CERTIFICATE OF MERIT (was Perfect Score): a framed certificate (%sx%s) with its heading, OF MERIT, a red 100%% stamp and a seal all on the paper (stamp %s, seal %s), hung from a nail by a wire to each top corner (%s)" %
    ((B.get("frame") or {}).get("w"), (B.get("frame") or {}).get("h"), B.get("stampInCert"), B.get("sealInCert"), B.get("wireOk")),
    B.get("certInFrame") and B.get("stampInCert") and B.get("sealInCert") and B.get("wireOk") and B.get("heading") and B.get("merit") and B.get("pct") and (B.get("frame") or {}).get("w", 0) >= 90, B)
chk("(12) ...an inspector (hat %s, vest %s, bands %s) whose hand rests on the frame (%s) and whose other hand raises a rubber stamp above his head (%s), at a door under a lit FIRE MARSHAL sign (%s); no scoreboard, no UNIT SCORE (%s)" %
    ((B.get("person") or {}).get("hat"), (B.get("person") or {}).get("vest"), (B.get("person") or {}).get("bands"), B.get("handOnFrame"), B.get("toolAboveHead"), B.get("sign"), B.get("scoreboard")),
    B.get("person") and B["person"]["hat"] == 1 and B["person"]["vest"] == 1 and B["person"]["bands"] >= 6 and B.get("handOnFrame") and B.get("toolAboveHead") and B.get("sign") and not B.get("scoreboard"), B)
C = G.get("C", {}); bu = C.get("bursts") or []
xs = sorted(b["x"] for b in bu); gaps4 = [round(b - a, 1) for a, b in zip(xs, xs[1:])]
chk("(12) GRAND FINALE, no truck (%s): seven inspectors on one crest (feet %s), each with hat and vest bands (%s hats, %s band shapes), two or more with an arm raised (%s)" % (C.get("truck"), C.get("feet"), C.get("hats"), C.get("bands"), C.get("raised")),
    not C.get("truck") and C.get("men") == 7 and C.get("hats") == 7 and C.get("bands") >= 7 and max(C["feet"]) - min(C["feet"]) <= 8 and C.get("raised", 0) >= 2, C)
chk("(12) ...the fireworks are NOT a pattern: %s bursts, %s distinct sizes, %s distinct spoke counts, a spread of %s units in x (uneven gaps %s) and %s in y, one more than half off the top edge, one low and wide, %s still rising as trails, every burst with a glow (%s), %s distinct clocks" %
    (len(bu), len(set(round(b["R"] / 6) for b in bu)), len(set(b["n"] for b in bu)), (max(b["x"] for b in bu) - min(b["x"] for b in bu)) if bu else 0, gaps4, (max(b["y"] for b in bu) - min(b["y"] for b in bu)) if bu else 0, C.get("rises"), C.get("glowAlways"), len(set(C.get("clock") or []))),
    len(bu) == 6 and len(set(round(b["R"] / 6) for b in bu)) >= 4 and len(set(b["n"] for b in bu)) >= 4 and (max(gaps4) - min(gaps4)) > 25 and max(b["y"] for b in bu) - min(b["y"] for b in bu) >= 80
    and any(b["y"] < b["R"] * .25 for b in bu) and any(b["y"] > 80 for b in bu) and C.get("rises", 0) >= 3 and C.get("glowAlways") and len(set(C["clock"])) >= 5, C)
D = G.get("D", {}); dn = D.get("n") or {}
chk("(12) TEN IN A ROW is a connected system: %s; the header (x %s) takes the riser up from the floor (touches header %s, reaches y %s), every one of ten branches stands on the header (%s), runs up to its gauge (%s), and carries its own valve, flow switch (%s), gauge, lamp and zone plate in one column (%s)" %
    (dn, (D.get("header") or {}).get("x"), D.get("riserTouchesHeader"), D.get("riserOnFloor"), D.get("branchOnHeader"), D.get("branchToGauge"), D.get("flowOnBranch"), D.get("aligned")),
    dn.get("branches") == 10 and dn.get("gauges") == 10 and dn.get("lamps") == 10 and dn.get("plates") == 10 and dn.get("flow") == 10 and dn.get("valves") == 11 and dn.get("conduits") == 10 and D.get("riserTouchesHeader") and D.get("riserOnFloor", 0) >= 157
    and D.get("branchOnHeader") and D.get("branchToGauge") and D.get("flowOnBranch") and D.get("aligned"), D)
chk("(12) ...each lamp is wired by a conduit to its flow switch (%s), each plate hangs on rods from the header (%s), the pitch is even (%s), ten needles in the green (%s), ten lit lamps (%s), the plate reads TEN UNITS IN A ROW (%s, old heading %s), a clipboard on the wall (%s)" %
    (D.get("conduitJoins"), D.get("platesHung"), D.get("pitch"), D.get("needles"), D.get("lampsLit"), D.get("heading"), D.get("oldHeading"), D.get("clipboard")),
    D.get("conduitJoins") and D.get("platesHung") and D.get("pitch") and max(D["pitch"]) - min(D["pitch"]) < 1 and len(D.get("needles") or []) == 10 and all(.52 < n <= 1 for n in D["needles"]) and D.get("lampsLit") and D.get("heading") and not D.get("oldHeading") and D.get("clipboard"), D)
E = G.get("E", {}); lad = E.get("ladder") or {}; roof = E.get("roof") or {}
chk("(12) TOP OF THE LADDER: the figure is an INSPECTOR (%s inspector, %s firefighters; hat %s, vest %s, bands %s) standing on the roof (feet %s below its top, x on it %s) holding a clipboard by its edge (%s %s); the ladder (%s rungs, top y %s, roof y %s, end x %s) is on the roof edge; no hose, no fire" %
    (E.get("inspectors"), E.get("firefighters"), (E.get("person") or {}).get("hat"), (E.get("person") or {}).get("vest"), (E.get("person") or {}).get("bands"), E.get("feetOnRoof"), E.get("onRoofX"), E.get("board"), E.get("boardHeld"), E.get("rungs"), lad.get("y"), roof.get("y"), lad.get("r")),
    E.get("inspectors") == 1 and E.get("firefighters") == 0 and E.get("person") and E["person"]["hat"] == 1 and E["person"]["vest"] == 1 and E["person"]["bands"] >= 6 and abs(E.get("feetOnRoof", 99)) <= 6 and E.get("onRoofX") and E.get("board") and E.get("boardHeld")
    and E.get("rungs", 0) >= 12 and abs(lad.get("y", -99) - roof.get("y", 99)) <= 9 and roof.get("x", 999) <= lad.get("r", -999) <= roof.get("r", -999) and not E.get("fire") and not E.get("hose"), E)
Fh = G.get("F", {}); wr = Fh.get("wraps") or []; fb = Fh.get("band") or {}
chk("(12) FIRE INVESTIGATOR'S TAPE: no knots (%s), no twists or turns (%s, back %s), wrapped once at each end (wraps at x %s: the jamb %s, the post %s), at chest height (band y %s to %s), sagging (%s)" % (Fh.get("knots"), Fh.get("turns"), Fh.get("back"), [w["cx"] for w in wr], Fh.get("doorRight"), Fh.get("post"), fb.get("y"), fb.get("b"), Fh.get("sag")),
    Fh.get("knots") == 0 and Fh.get("turns") == 0 and Fh.get("back") == 0 and len(wr) == 2 and abs(wr[0]["cx"] - (Fh["doorRight"] - 3)) <= 4 and abs(wr[1]["cx"] - Fh["post"]) <= 4 and fb and 84 <= fb["y"] and fb["b"] <= 135 and Fh.get("sag", 0) >= 6, Fh)
chk("(12) ...and printed along its WHOLE length: %s glyphs, the first %s units from the jamb's wrap and the last %s from the post's, the widest gap between glyphs %s (a blank stretch would be 30+)" % (Fh.get("glyphs"), Fh.get("firstGap"), Fh.get("lastGap"), Fh.get("maxGap")),
    Fh.get("glyphs", 0) >= 38 and 0 <= Fh.get("firstGap", 99) <= 16 and 0 <= Fh.get("lastGap", 99) <= 16 and Fh.get("maxGap", 99) <= 14, Fh)
Gh = G.get("G", {}); tm = (Gh.get("time") or "0:0").split(":"); mins = int(tm[0]) * 60 + int(tm[1])
chk("(12) AFTER HOURS, the tag is a BLUE inspection tag (blue %s %s): INSPECTION heading (%s), %s handwriting rows, %s check boxes (%s ticked), %s punched holes, the string goes through its hole (%s units) from the handwheel (%s units from its centre, wheel radius %s); nothing says OK (%s)" %
    (Gh.get("blue"), Gh.get("cols"), Gh.get("header"), Gh.get("rows"), Gh.get("boxes"), Gh.get("ticks"), Gh.get("punches"), Gh.get("stringToHole"), Gh.get("stringStartToWheel"), Gh.get("wheelR"), Gh.get("ok")),
    Gh.get("blue") and Gh.get("header") and Gh.get("rows") == 10 and Gh.get("boxes") == 10 and 4 <= Gh.get("ticks", 0) < 10 and Gh.get("punches", 0) >= 22 and Gh.get("stringToHole") is not None and Gh["stringToHole"] <= 3
    and Gh.get("stringStartToWheel") is not None and Gh["stringStartToWheel"] <= Gh["wheelR"] + 8 and not Gh.get("ok"), Gh)
chk("(12) ...and the scene is kept: the beam (x %s to %s) lands on the handwheel (%s), the gauge (%s) and the tag (%s), the clock %s is near eleven, no thermal camera (%s)" % ((Gh.get("beam") or {}).get("x"), (Gh.get("beam") or {}).get("r"), Gh.get("wheelLit"), Gh.get("gaugeLit"), Gh.get("tagLit"), Gh.get("time"), Gh.get("thermal")),
    Gh.get("wheel") and Gh.get("gauge") and Gh.get("tag") and Gh.get("wheelLit") and Gh.get("gaugeLit") and Gh.get("tagLit") and 10 * 60 + 40 <= mins <= 11 * 60 + 15 and not Gh.get("thermal"), Gh)
chk("(12) the round 4 art had no page error while it was measured (%s)" % G.get("err"), not G.get("err"), G.get("err"))
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
