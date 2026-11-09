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
     ROUND 6 retired the lines for the four scenes it replaced or re-dressed (Inspection Team's hi-vis men, Certificate of Merit, Ten in a Row's system,
     Top of the Ladder) and Grand Finale's hats; the fireworks, the tape and After Hours' tag lines stand.

(13) BUILD 384 ROUND 6 (Madison: "We are FIRE inspectors. Fire inspectors wear police gear" / "Inspectors across the banners should have the same kinda look"),
     measured on the page: THE ONE INSPECTOR - every visible inspector in every Fire Code banner is drawn by the shared kit (.fb-officer: Inspection Team 5,
     Grand Finale 7, Top Floor 1, After Hours 1), each with a navy polo (.fb-polo) and navy pants (.fb-pants) and a black plate carrier (.fb-tacvest); no
     round-4 hi-vis man (.fb-inspector), no hard hat (.fb-hat) and every cap navy; no hi-vis yellow-green anywhere in a Fire Code banner. CERTIFIED: every
     ribbon tail starts under its rosette and ends on the paper; the desk badge is off the centre line. PLAN REVIEW: no scale ruler and no hard hat; the lamp's
     base, three joints, shade and bulb are joined (the base under the first joint, the shade's narrow end at the last joint, the cone leaving the bulb's
     rim); a flashlight, a radio, gloves and a navy cap on the table. INSPECTION TEAM: five officers on one pavement line with gaps between them, three with a
     holstered handgun and two without, the beams starting at their lenses. GRAND FINALE: seven officers on the crest, two saluting, hands on belts and
     arms folded. SQUARED AWAY (was Certificate of Merit): the gear wall - a plate carrier, the duty belt with a holstered handgun, three flashlights, a
     radio, cuffs, a navy cap, gloves, a badge wallet, contact shadows, no certificate. TOP FLOOR (was Top of the Ladder): the stair sign with 80 on it, one
     officer from behind, no ladder or firefighter. CLEAN SWEEP (was Ten in a Row): ten inspection tags, five a side of the vanishing point, all inside the
     strip, an EXIT, no gauges. AFTER HOURS: the kneeling officer, his beam from his lens, no cowboy hat. Nine banners differ from ea31d43 (prev4.json) and
     the other twelve are exactly as ea31d43 drew them.

     ROUND 9 (r9-banners) follows Madison's review: the look (cowboy hat, glasses, stubble, navy shirt, BLUE vest), three inspectors in the warehouse, the hat in
     place of the caps, After Hours' tag wired to the gauge line; the Inspection Team and Top Floor round 6 lines are retired and the round 9 banners are left out
     of the older "nothing else moved" pins - tools/check-b384-r9-banners.py holds them, and the academy, byte for byte.

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
NAMES = {"tests100": "Certified", "tests250": "Plan Review", "tests500": "Inspection Team", "hundos100": "Squared Away", "hundos250": "Grand Finale",
         "vr50": "Mutual Aid", "study50": "Code Book", "study60": "On Call", "correct5000": "Downpour", "correct10000": "Fire Investigator",
         "level80": "Top Floor", "early10": "After Hours", "exam100": "Clean Sweep", "adept_rank": "Sapphire", "elite_rank": "Amethyst", "titan_rank": "Supernova",
         "flare_void": "Nebula", "flare_umbra": "Quasar", "flare_horizon": "Whiteout", "flare_genesis": "Comet", "zenith": "Star Ranger"}
REDONE = ["tests100", "tests250", "tests500", "hundos100", "hundos250", "vr50", "study50", "study60", "correct10000", "level80", "early10", "exam100",
          "flare_umbra", "flare_horizon", "flare_genesis", "correct5000", "flare_void"]   # round 9 redrew Downpour and Nebula too
KEEP = ["adept_rank", "elite_rank", "titan_rank", "zenith"]
# round 9 (r9-banners; Madison's review, tools/check-b384-r9-banners.py): these moved on purpose, so the older "nothing else moved" pins leave them out
R9 = ["tests500", "correct5000", "level80", "early10", "flare_void", "flare_umbra", "flare_horizon", "flare_genesis", "hundos100", "tests250", "hundos250"]
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
  const ls = {}; ['hundos250', 'early10', 'correct10000'].forEach(id => ls[id] = layerStr(id));
  /* C. grand finale */
  try{ const b = mount('hundos250'); const art = BANNER_ART.hundos250('gq'); const fw = art.filter(l => /bl-fwk/.test(l.cls || ''));
    const cs = fw.map(l => ({ cx: l.o[0], cy: l.o[1], R: l.box[2] / 3.8, spokes: ((l.svg.match(/class="fb-spokes" d="([^"]*)"/) || [0, ''])[1].match(/Q/g) || []).length, glow: /<circle cx="[^"]*" cy="[^"]*" r="[^"]*" fill="url\(#gq/.test(l.svg), top: l.box[1] }));
    out.C = { bursts: cs.map(c => ({ x: r1(c.cx), y: r1(c.cy), R: r1(c.R), n: c.spokes, glow: c.glow })),
      rises: all(b, '.fb-rise').length, truck: !!b.querySelector('.fb-truck') || !!b.querySelector('.fb-tyre') || /tkbody/.test(ls.hundos250), clock: fw.map(l => /animation-duration:([\d.]+)s/.exec(l.style)[1]), glowAlways: cs.every(c => c.glow) }; b.remove(); }catch(e){ out.err = (out.err || '') + 'C ' + String(e).slice(0, 120) + ' '; }
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
    const hole = b.querySelector('.fb-hole'), str = b.querySelector('.fb-string'), sn = str ? nums(str.getAttribute('d')) : [], Ho = hole && R(hole), gl = all(b, '.fb-gaugeline').map(R);
    const gm = /id="gqtagb">(?:<stop[^>]*stop-color="(#[0-9A-Fa-f]{6})"[^>]*\/>)+/.exec(ls.early10), cols = ((/id="gqtagb"[^>]*>(.*?)<\/linearGradient>/.exec(ls.early10) || [0, ''])[1].match(/#[0-9A-Fa-f]{6}/g) || []);
    const blue = cols.length > 0 && cols.every(h => { const n = parseInt(h.slice(1), 16); return (n & 255) > (n >> 16 & 255) * 1.5; });
    out.G = { beam: Bm && { x: r1(Bm.x), r: r1(Bm.r) }, wheel: !!W, gauge: !!G2, tag: !!Tg, wheelLit: inside(Bm, W), gaugeLit: inside(Bm, G2), tagLit: inside(Bm, Tg), time: ck ? ck.getAttribute('data-time') : null,
      rows: all(b, '.fb-tagrows').reduce((a, e) => a + (e.getAttribute('d').match(/M/g) || []).length, 0), boxes: all(b, '.fb-tagbox').length, ticks: all(b, '.fb-tagticks').reduce((a, e) => a + (e.getAttribute('d').match(/M/g) || []).length, 0), punches: all(b, '.fb-punch').length,
      stringEnd: sn.length ? [r1(sn[sn.length - 2]), r1(sn[sn.length - 1])] : null, hole: Ho && [r1(Ho.cx), r1(Ho.cy)], stringToHole: Ho && sn.length ? r1(Math.hypot(sn[sn.length - 2] - Ho.cx, sn[sn.length - 1] - Ho.cy)) : null,
      onLine: !!sn.length && gl.some(l => sn[0] >= l.x - 3 && sn[0] <= l.r + 3 && sn[1] >= l.y - 4 && sn[1] <= l.b + 4), blue, cols, header: !!tg && tg.querySelectorAll('path[stroke="#FFFFFF"]').length >= 2, ok: ls.early10.indexOf(tp('OK', 414, 137, 5.6)) >= 0,
      thermal: /iron|hot\b/.test(ls.early10) || /#FF8AD0/i.test(ls.early10) }; b.remove(); }catch(e){ out.err = (out.err || '') + 'G ' + String(e).slice(0, 120) + ' '; }
  return out;
}"""

GEO6 = r"""() => {
  /* round 6: every Fire Code banner's still picture mounted 1:1 (a unit is a pixel) and measured */
  const mount = id => { const box = document.createElement('div'); box.style.cssText = 'position:fixed;left:0;top:0;width:480px;height:180px;overflow:hidden;z-index:99999';
    box.innerHTML = bannerStaticSVG(id) || ''; document.body.appendChild(box); const sv = box.querySelector('svg'); if(sv){ sv.setAttribute('width', 480); sv.setAttribute('height', 180); sv.setAttribute('preserveAspectRatio', 'none'); } return box; };
  const R = e => { const r = e.getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height, r: r.right, b: r.bottom, cx: r.left + r.width / 2, cy: r.top + r.height / 2 }; };
  const r1 = v => Math.round(v * 10) / 10, all = (b, sel) => [...b.querySelectorAll(sel)], nums = d => (d.match(/-?\d+\.?\d*/g) || []).map(Number);
  const rgb = h => { const m = /^#([0-9a-f]{6})$/i.exec(h || ''); if(!m) return null; const n = parseInt(m[1], 16); return [n >> 16, n >> 8 & 255, n & 255]; };
  const navy = h => { const c = rgb(h); return !!c && c[2] > c[0] + 18 && c[2] > c[1] + 8 && c[2] < 150 && c[0] < 70; };
  const dark = h => { const c = rgb(h); return !!c && Math.max.apply(null, c) < 60; };
  const hsl = c => { const r = c[0] / 255, g = c[1] / 255, b = c[2] / 255, mx = Math.max(r, g, b), mn = Math.min(r, g, b), l = (mx + mn) / 2, d = mx - mn; const sat = d === 0 ? 0 : d / (1 - Math.abs(2 * l - 1));
    let hue = 0; if(d){ hue = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4; hue = (hue * 60 + 360) % 360; } return [hue, sat, l]; };
  const layerStr = id => { try{ const a = BANNER_ART[id]('gq'); return Array.isArray(a) ? a.map(l => (l.svg || '') + (l.kids || []).map(k => k.svg || '').join('')).join('') : String(a); }catch(e){ return ''; } };
  const out = { err: '' }, ids = Object.keys(IFC_BANNER_ART);
  /* A. the one inspector, everywhere */
  try{ out.A = { per: {}, bad: [], old: {}, hivis: {}, caps: [] };
    ids.forEach(id => { const b = mount(id), offs = all(b, '.fb-officer');
      out.A.per[id] = offs.length;
      offs.forEach((o, i) => { const polo = o.querySelector('.fb-polo'), pants = o.querySelector('.fb-pants'), vest = o.querySelector('.fb-tacvest');
        const vf = vest ? [...vest.querySelectorAll('path')].map(e => e.getAttribute('fill')).filter(f => /^#/.test(f || '')) : [];
        const vc = rgb(vest && vest.getAttribute('data-col')), blue = !!vc && vc[2] > 140 && vc[2] > vc[0] + 80;
        const ok = polo && navy(polo.getAttribute('fill')) && pants && navy(pants.getAttribute('stroke') || pants.getAttribute('fill')) && vest && vf.length && blue;
        if(!ok) out.A.bad.push([id, i, polo && polo.getAttribute('fill'), pants && (pants.getAttribute('stroke') || pants.getAttribute('fill')), vf[0]]); });
      const old = all(b, '.fb-inspector, .fb-hat, .fb-person, .fb-ff, .fb-band').length; if(old) out.A.old[id] = old;
      all(b, '.fb-cap').forEach(c => out.A.caps.push([id, c.getAttribute('data-col')]));
      all(b, '.fb-cowboy').forEach(c => out.A.hats = (out.A.hats || []).concat([[id, c.getAttribute('data-col')]]));
      const cols = new Set(((bannerStaticSVG(id) || '') + layerStr(id)).match(/#[0-9a-fA-F]{6}\b/g) || []), hv = [...cols].filter(h => { const q = hsl(rgb(h)); return q[0] >= 62 && q[0] <= 100 && q[1] > .55 && q[2] > .38; });
      if(hv.length) out.A.hivis[id] = hv;
      b.remove(); }); }catch(e){ out.err += 'A ' + String(e).slice(0, 120) + ' '; }
  /* B. certified: tails under their rosettes and on the paper; the desk badge off the centre line */
  try{ const b = mount('tests100'), papers = all(b, '.fb-paper').map(R), ros = all(b, '.fb-rosette').map(R), tails = all(b, '.fb-tail');
    const inPaper = t => papers.some(p => t.x >= p.x - .3 && t.r <= p.r + .3 && t.y >= p.y - .3 && t.b <= p.b + .3);
    const tops = tails.map(t => { const n = nums(t.getAttribute('d')), pts = []; for(let i = 0; i < n.length; i += 2) pts.push([n[i], n[i + 1]]); pts.sort((p, q) => p[1] - q[1]); return pts.slice(0, 2); });
    const under = tops.map(tp => tp.every(p => ros.some(r => Math.hypot(p[0] - r.cx, p[1] - r.cy) <= r.w / 2 - .2)));
    const db = b.querySelector('.fb-deskbadge');
    out.B = { tails: tails.length, rosettes: ros.length, onPaper: tails.map(t => inPaper(R(t))), under, badgeX: db ? r1(R(db).cx) : null }; b.remove(); }catch(e){ out.err += 'B ' + String(e).slice(0, 120) + ' '; }
  /* C. plan review */
  try{ const b = mount('tests250'), ls = layerStr('tests250'), J = all(b, '.fb-joint').map(R).sort((p, q) => p.cx - q.cx), base = b.querySelector('.fb-lampbase'), sh = b.querySelector('.fb-shade'), bu = b.querySelector('.fb-bulb');
    const sn = sh ? nums(sh.getAttribute('d')) : [], narrow = sn.length >= 4 ? [(sn[0] + sn[2]) / 2, (sn[1] + sn[3]) / 2] : null, B0 = base && R(base), BU = bu && R(bu);
    const cone = (BANNER_ART.tests250('gq')[1] || {}).svg || '', cn = nums((/d="([^"]*)"/.exec(cone) || [0, ''])[1]);
    out.C = { joints: J.length, baseUnderFirst: !!(B0 && J[0] && J[0].cx > B0.x && J[0].cx < B0.r && J[0].cy < B0.cy + 2 && J[0].cy > B0.y - 14), shadeAtLast: !!(narrow && J[2] && Math.hypot(narrow[0] - J[2].cx, narrow[1] - J[2].cy) < 8),
      coneFromBulb: !!(BU && cn.length >= 4 && [[cn[0], cn[1]], [cn[2], cn[3]]].every(p => p[0] >= BU.x - 3 && p[0] <= BU.r + 3 && p[1] >= BU.y - 3 && p[1] <= BU.b + 3)),
      ruler: /url\(#gqscale\)/.test(ls), hardhat: /url\(#gqhat\)/.test(ls), torch: all(b, '.fb-geartorch').length, radio: all(b, '.fb-gearradio').length, gloves: all(b, '.fb-geargloves').length, cap: all(b, '.fb-gearhat').length }; b.remove(); }catch(e){ out.err += 'C ' + String(e).slice(0, 120) + ' '; }
  /* D. inspection team */
  try{ const b = mount('tests500'), offs = all(b, '.fb-officer').sort((p, q) => R(p).cx - R(q).cx), vests = offs.map(o => R(o.querySelector('.fb-tacvest')));
    const lenses = all(b, '.fb-lens').map(R), beams = all(b, '.fb-beam').map(e => { const n = nums(e.getAttribute('d')); return [(n[0] + n[n.length - 2]) / 2, (n[1] + n[n.length - 1]) / 2]; });
    out.D = { n: offs.length, feet: offs.map(o => r1(R(o.querySelector('.fb-pants')).b)), gap: vests.slice(1).map((v, i) => r1(v.x - vests[i].r)), guns: offs.filter(o => o.querySelector('.fb-gun')).length,
      lensToBeam: beams.map(p => lenses.length ? r1(Math.min.apply(null, lenses.map(l => Math.hypot(l.cx - p[0], l.cy - p[1])))) : 99), boards: all(b, '.fb-board').length }; b.remove(); }catch(e){ out.err += 'D ' + String(e).slice(0, 120) + ' '; }
  /* E. grand finale */
  try{ const b = mount('hundos250'), offs = all(b, '.fb-officer'), poses = offs.map(o => o.getAttribute('data-pose'));
    out.E = { n: offs.length, back: all(b, '.fb-officer.fb-back').length, feet: offs.map(o => r1(R(o.querySelector('.fb-pants')).b)), salute: poses.filter(p => p === 'salute').length, belt: poses.filter(p => p === 'belt').length, cross: poses.filter(p => p === 'cross').length,
      lettering: offs.every(o => o.querySelector('.fb-tacvest path[fill="none"]')) }; b.remove(); }catch(e){ out.err += 'E ' + String(e).slice(0, 120) + ' '; }
  /* F. squared away */
  try{ const b = mount('hundos100'), ls = layerStr('hundos100');
    out.F = { vest: all(b, '.fb-gearvest').length, belt: all(b, '.fb-gearbelt').length, holster: all(b, '.fb-gearbelt .fb-holster').length, gun: all(b, '.fb-gearbelt .fb-gun').length, torches: all(b, '.fb-geartorch').length, radio: all(b, '.fb-gearradio').length,
      cuffs: all(b, '.fb-cuffs').length, cap: all(b, '.fb-gearhat').length, gloves: all(b, '.fb-geargloves').length, wallet: all(b, '.fb-gearwallet').length, shadows: b.querySelector('.fb-gearshadows') ? b.querySelector('.fb-gearshadows').children.length : 0,
      cert: all(b, '.fb-cert, .fb-cert-frame').length, patch: ls.indexOf(fbTextPath('FIRE MARSHAL', 212, 30 + 28.5 * 1.72, 2.3 * 1.72)) >= 0 }; b.remove(); }catch(e){ out.err += 'F ' + String(e).slice(0, 120) + ' '; }
  /* G. top floor */
  try{ const b = mount('level80'), sg = b.querySelector('.fb-stairsign'), n80 = b.querySelector('.fb-floor80'), S = sg && R(sg), N = n80 && R(n80);
    out.G = { sign: !!sg, eighty: !!(S && N && N.x >= S.x && N.r <= S.r && N.y >= S.y && N.b <= S.b && N.h > S.h * .25), officers: all(b, '.fb-officer').length, back: all(b, '.fb-officer.fb-back').length, ladder: all(b, '.fb-ladder, .fb-rung, .fb-ff').length }; b.remove(); }catch(e){ out.err += 'G ' + String(e).slice(0, 120) + ' '; }
  /* H. clean sweep */
  try{ const b = mount('exam100'), ls = layerStr('exam100'), tg = all(b, '.fb-sweeptag').map(R);
    out.H = { tags: tg.length, left: tg.filter(t => t.cx < 228).length, right: tg.filter(t => t.cx > 228).length, inStrip: tg.every(t => t.x >= 0 && t.r <= 480 && t.y >= 10.5 && t.b <= 169.5), exit: ls.indexOf(fbTextPath('EXIT', 0, 0, 3).slice(0, 0)) >= 0 && /fill="#FF6A5A"|stroke="#FF6A5A"/.test(ls),
      gauges: all(b, '.fb-gauge, .fb-header, .fb-branch').length }; b.remove(); }catch(e){ out.err += 'H ' + String(e).slice(0, 120) + ' '; }
  /* I. after hours */
  try{ const b = mount('early10'), ls = layerStr('early10'), offs = all(b, '.fb-officer'), lens = b.querySelector('.fb-lens'), bm = b.querySelector('.fb-beam'), L = lens && R(lens), bn = bm ? nums(bm.getAttribute('d')) : [];
    out.I = { officers: offs.length, kneel: offs.filter(o => o.getAttribute('data-pose') === 'kneel').length, lensToBeam: L && bn.length ? r1(Math.hypot(L.cx - bn[0], L.cy - (bn[1] + bn[bn.length - 1]) / 2)) : null, cowboy: !!(offs[0] && offs[0].querySelector('.fb-cowboy')) }; b.remove(); }catch(e){ out.err += 'I ' + String(e).slice(0, 120) + ' '; }
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
    G6 = pg.evaluate(GEO6)
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
chk("(2) Star Ranger and the rank banners are as they were (Downpour and Nebula were redrawn in round 9) (changed: %s)" % moved, PREV and not moved, moved)
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
R6 = ["tests100", "tests250", "tests500", "hundos100", "hundos250", "level80", "early10", "exam100", "study50"]   # round 6 moved these on purpose (13)
rest = [i for i in NAMES if i not in R3B and i not in R6 and i not in R9 and i != "flare_horizon"]   # Pulsar is being redrawn with its character, in another branch
moved2 = [i for i in rest if PREV2.get(i) and F["hashes"].get(i) != PREV2[i]]
chk("(11) nothing else moved since c8143d5 but round 6's (changed: %s) (Pulsar is another branch's)" % moved2, PREV2 and not moved2, moved2)
# ---- (12) round 4 (Madison's review of round 3b), measured on the page itself ----
PREV3 = {}
try: PREV3 = json.load(open(os.path.join(HERE, "check-b384-fcbanners.prev3.json")))
except Exception: pass
R4 = ["tests500", "hundos100", "hundos250", "level80", "exam100", "early10", "correct10000"]
same3 = [i for i in R4 if PREV3.get(i) and F["hashes"].get(i) == PREV3[i]]
chk("(12) the seven banners redrawn in round 4 differ from c1d224b (unchanged: %s; %d hashes known)" % (same3, len(PREV3)), PREV3 and not same3, same3)
moved3 = [i for i in NAMES if i not in R4 and i not in R6 and i not in R9 and PREV3.get(i) and F["hashes"].get(i) != PREV3[i]]
chk("(12) nothing else moved since c1d224b but round 6's (changed: %s)" % moved3, PREV3 and not moved3, moved3)
C = G.get("C", {}); bu = C.get("bursts") or []
xs = sorted(b["x"] for b in bu); gaps4 = [round(b - a, 1) for a, b in zip(xs, xs[1:])]
chk("(12) GRAND FINALE has no truck (%s)" % C.get("truck"), C.get("bursts") and not C.get("truck"), C)
chk("(12) ...the fireworks are NOT a pattern: %s bursts, %s distinct sizes, %s distinct spoke counts, a spread of %s units in x (uneven gaps %s) and %s in y, one more than half off the top edge, one low and wide, %s still rising as trails, every burst with a glow (%s), %s distinct clocks" %
    (len(bu), len(set(round(b["R"] / 6) for b in bu)), len(set(b["n"] for b in bu)), (max(b["x"] for b in bu) - min(b["x"] for b in bu)) if bu else 0, gaps4, (max(b["y"] for b in bu) - min(b["y"] for b in bu)) if bu else 0, C.get("rises"), C.get("glowAlways"), len(set(C.get("clock") or []))),
    len(bu) == 6 and len(set(round(b["R"] / 6) for b in bu)) >= 4 and len(set(b["n"] for b in bu)) >= 4 and (max(gaps4) - min(gaps4)) > 25 and max(b["y"] for b in bu) - min(b["y"] for b in bu) >= 80
    and any(b["y"] < b["R"] * .25 for b in bu) and any(b["y"] > 80 for b in bu) and C.get("rises", 0) >= 3 and C.get("glowAlways") and len(set(C["clock"])) >= 5, C)
Fh = G.get("F", {}); wr = Fh.get("wraps") or []; fb = Fh.get("band") or {}
chk("(12) FIRE INVESTIGATOR'S TAPE: no knots (%s), no twists or turns (%s, back %s), wrapped once at each end (wraps at x %s: the jamb %s, the post %s), at chest height (band y %s to %s), sagging (%s)" % (Fh.get("knots"), Fh.get("turns"), Fh.get("back"), [w["cx"] for w in wr], Fh.get("doorRight"), Fh.get("post"), fb.get("y"), fb.get("b"), Fh.get("sag")),
    Fh.get("knots") == 0 and Fh.get("turns") == 0 and Fh.get("back") == 0 and len(wr) == 2 and abs(wr[0]["cx"] - (Fh["doorRight"] - 3)) <= 4 and abs(wr[1]["cx"] - Fh["post"]) <= 4 and fb and 84 <= fb["y"] and fb["b"] <= 135 and Fh.get("sag", 0) >= 6, Fh)
chk("(12) ...and printed along its WHOLE length: %s glyphs, the first %s units from the jamb's wrap and the last %s from the post's, the widest gap between glyphs %s (a blank stretch would be 30+)" % (Fh.get("glyphs"), Fh.get("firstGap"), Fh.get("lastGap"), Fh.get("maxGap")),
    Fh.get("glyphs", 0) >= 38 and 0 <= Fh.get("firstGap", 99) <= 16 and 0 <= Fh.get("lastGap", 99) <= 16 and Fh.get("maxGap", 99) <= 14, Fh)
Gh = G.get("G", {}); tm = (Gh.get("time") or "0:0").split(":"); mins = int(tm[0]) * 60 + int(tm[1])
chk("(12) AFTER HOURS, the tag is a BLUE inspection tag (blue %s %s): INSPECTION heading (%s), %s handwriting rows, %s check boxes (%s ticked), %s punched holes, the string goes through its hole (%s units) from riser 1's gauge line (round 9: %s); nothing says OK (%s)" %
    (Gh.get("blue"), Gh.get("cols"), Gh.get("header"), Gh.get("rows"), Gh.get("boxes"), Gh.get("ticks"), Gh.get("punches"), Gh.get("stringToHole"), Gh.get("onLine"), Gh.get("ok")),
    Gh.get("blue") and Gh.get("header") and Gh.get("rows") == 10 and Gh.get("boxes") == 10 and 4 <= Gh.get("ticks", 0) < 10 and Gh.get("punches", 0) >= 22 and Gh.get("stringToHole") is not None and Gh["stringToHole"] <= 3
    and Gh.get("onLine") and not Gh.get("ok"), Gh)
chk("(12) ...and the scene is kept: a handwheel (%s) and a gauge (%s), the beam (x %s to %s) lands on the tag (%s; round 9 aims it at riser 1's gauge line and its tag, not the wheel), the clock %s is near eleven, no thermal camera (%s)" % (Gh.get("wheel"), Gh.get("gauge"), (Gh.get("beam") or {}).get("x"), (Gh.get("beam") or {}).get("r"), Gh.get("tagLit"), Gh.get("time"), Gh.get("thermal")),
    Gh.get("wheel") and Gh.get("gauge") and Gh.get("tag") and Gh.get("tagLit") and 10 * 60 + 40 <= mins <= 11 * 60 + 15 and not Gh.get("thermal"), Gh)
chk("(12) the round 4 art still standing had no page error while it was measured (%s)" % G.get("err"), not G.get("err"), G.get("err"))
# ---- (13) round 6 (the one inspector; the gear wall, the top floor, the clean sweep), measured on the page itself ----
PREV4 = {}
try: PREV4 = json.load(open(os.path.join(HERE, "check-b384-fcbanners.prev4.json")))
except Exception: pass
same4 = [i for i in R6 if PREV4.get(i) and F["hashes"].get(i) == PREV4[i]]
chk("(13) the nine banners round 6 redrew differ from ea31d43 (unchanged: %s; %d hashes known)" % (same4, len(PREV4)), PREV4 and not same4, same4)
moved4 = [i for i in NAMES if i not in R6 and i not in R9 and PREV4.get(i) and F["hashes"].get(i) != PREV4[i]]
chk("(13) the others (but round 9's) are exactly as ea31d43 drew them (changed: %s)" % moved4, PREV4 and not moved4, moved4)
G6 = G6 or {}; A6 = G6.get("A") or {}; per = A6.get("per") or {}
want = {"tests500": 3, "hundos250": 7, "level80": 1, "early10": 1}   # round 9: the Inspection Team is three, in a warehouse
chk("(13) THE ONE INSPECTOR: the shared kit draws every inspector (%s; want %s, and none elsewhere)" % ({k: v for k, v in per.items() if v}, want),
    all(per.get(k) == v for k, v in want.items()) and sum(per.values()) == sum(want.values()), per)
chk("(13) ...each in a navy shirt, navy pants and (round 9) a BLUE plate carrier (wrong: %s)" % A6.get("bad"), sum(per.values()) == sum(want.values()) and not A6.get("bad"), A6.get("bad"))
chk("(13) ...no round-4 hi-vis man, hard hat, crew figure or reflective band left in any Fire Code banner (%s); round 9: no ball cap (%s) and every hat the one dark brown cowboy hat (%s)" % (A6.get("old"), A6.get("caps"), sorted(set(c[1] for c in A6.get("hats") or []))),
    per and not A6.get("old") and not A6.get("caps") and A6.get("hats") and len(set(c[1] for c in A6["hats"])) == 1, (A6.get("old"), A6.get("caps"), A6.get("hats")))
chk("(13) ...and no hi-vis yellow-green anywhere in a Fire Code banner (%s)" % A6.get("hivis"), per and not A6.get("hivis"), A6.get("hivis"))
B6 = G6.get("B") or {}
chk("(13) CERTIFIED: every ribbon tail (%s, under %s rosettes) starts under its rosette (%s) and ends on the paper (%s); the desk badge is off the centre line (x %s)" % (B6.get("tails"), B6.get("rosettes"), B6.get("under"), B6.get("onPaper"), B6.get("badgeX")),
    B6.get("tails", 0) >= 14 and all(B6.get("under") or [False]) and all(B6.get("onPaper") or [False]) and B6.get("badgeX") is not None and abs(B6["badgeX"] - 240) > 40, B6)
C6 = G6.get("C") or {}
chk("(13) PLAN REVIEW: no scale ruler (%s), no hard hat (%s); the lamp is joined: %s joints, base under the first (%s), shade at the last (%s), the cone leaving the bulb (%s); flashlight %s, radio %s, gloves %s, the hat (round 9; was a cap) %s" %
    (C6.get("ruler"), C6.get("hardhat"), C6.get("joints"), C6.get("baseUnderFirst"), C6.get("shadeAtLast"), C6.get("coneFromBulb"), C6.get("torch"), C6.get("radio"), C6.get("gloves"), C6.get("cap")),
    C6 and not C6.get("ruler") and not C6.get("hardhat") and C6.get("joints") == 3 and C6.get("baseUnderFirst") and C6.get("shadeAtLast") and C6.get("coneFromBulb") and all(C6.get(k) == 1 for k in ("torch", "radio", "gloves", "cap")), C6)
# INSPECTION TEAM's round 6 line (five officers on one pavement line) is retired: round 9 replaced the scene (check-b384-r9-banners (6)).
E6 = G6.get("E") or {}
chk("(13) GRAND FINALE: seven officers from behind (%s / %s) on the crest (feet %s), %s saluting, %s hands on belts, %s arms folded, FIRE MARSHAL on every back (%s)" %
    (E6.get("n"), E6.get("back"), E6.get("feet"), E6.get("salute"), E6.get("belt"), E6.get("cross"), E6.get("lettering")),
    E6.get("n") == 7 and E6.get("back") == 7 and max(E6["feet"]) - min(E6["feet"]) <= 8 and E6.get("salute") == 2 and E6.get("belt", 0) >= 1 and E6.get("cross", 0) >= 1 and E6.get("lettering"), E6)
F6 = G6.get("F") or {}
chk("(13) SQUARED AWAY (was Certificate of Merit): the gear wall (round 9: the cap is the hat) - %s" % {k: F6.get(k) for k in ("vest", "belt", "holster", "gun", "torches", "radio", "cuffs", "cap", "gloves", "wallet", "shadows", "cert", "patch")},
    F6.get("vest") == 1 and F6.get("belt") == 1 and F6.get("holster") == 1 and F6.get("gun") == 1 and F6.get("torches", 0) >= 3 and F6.get("radio") == 1 and F6.get("cuffs") == 1 and F6.get("cap") == 1 and F6.get("gloves") == 1 and F6.get("wallet") == 1 and F6.get("shadows", 0) >= 6 and not F6.get("cert") and F6.get("patch"), F6)
# TOP FLOOR's round 6 line (the stair sign with its 80) is retired: round 9 took the door and the sign out (check-b384-r9-banners (5)).
H6 = G6.get("H") or {}
chk("(13) CLEAN SWEEP (was Ten in a Row): ten inspection tags (%s: %s left, %s right of the vanishing point), all inside the strip (%s), an EXIT (%s), no gauges or pipes (%s)" % (H6.get("tags"), H6.get("left"), H6.get("right"), H6.get("inStrip"), H6.get("exit"), H6.get("gauges")),
    H6.get("tags") == 10 and H6.get("left") == 5 and H6.get("right") == 5 and H6.get("inStrip") and H6.get("exit") and not H6.get("gauges"), H6)
I6 = G6.get("I") or {}
chk("(13) AFTER HOURS: the kneeling inspector in the kit (%s, kneeling %s), his beam starting at his lens (%s units), and (round 9) his cowboy hat (%s)" % (I6.get("officers"), I6.get("kneel"), I6.get("lensToBeam"), I6.get("cowboy")),
    I6.get("officers") == 1 and I6.get("kneel") == 1 and I6.get("lensToBeam") is not None and I6["lensToBeam"] <= 4 and I6.get("cowboy"), I6)
chk("(13) the round 6 measurements ran without a page error, over the twelve inspectors (%s)" % G6.get("err"), G6 and not G6.get("err") and sum(per.values()) == 12, G6.get("err"))

print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
