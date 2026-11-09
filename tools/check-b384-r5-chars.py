#!/usr/bin/env python3
"""Build 384, round 10 (r5-chars): Madison's reply to round 4 of the characters.

  "Yo what did you Do!!!!!! I never said don't give them faces revert their faces. I was just saying the smoke and eyes for a few looked like
   a copy paste. The sprinkler and fire alarm ones these older ones are cooler, unlike the glowing eyes"

  So faces are BACK on every object and cosmic body (this gate REPLACES check-b384-r4-chars, which is deleted: its "faceless set" leg
  is turned round into leg 1 here, and its Undercover / Irons / Pulsar / whole-drawing / banner / rule legs are legs 5-7 here), and the real ask is
  that no two faces are a stamp of one another. Everything is DERIVED FROM THE DRAWN SVG of each character:

  1. FACES EXIST. Per class, the characters with no face mark at all (no eye shape, no mouth shape, no symmetric pair of lit dots) are exactly
     The Irons (two tools over a shield, round 9) in Fire Code and the academy's Koi and Void (they never had one). Undercover has no eye marks
     (mirrored shades) and a flat mouth. Strobe, Toxic
     Spill, Nebula, Quasar, Pulsar, Eclipse, Sprinkler Head and, in the academy, Koi, Void, Genesis and Hive all have one.
  2. NO COPY-PASTE. A face signature is read off the eye and mouth groups: how many eyes, the shape of the largest lit shape (round / wide / tall /
     slit / lens / crescent / pill, from its aspect and how much of its box it fills), its size, the hue of the lamp, the mouth. (a) The FINE
     signature (every eye and mouth shape, its place and colour) differs between every two characters of a class. (b) The COARSE signature differs
     between every two NON-HUMAN faces (objects, cosmic bodies, the ghost, bear and alien). (c) The four secret flares differ from each other in
     eye shape AND colour, and so do Strobe and Sprinkler Head.
  3. EACH ONE'S OWN: Nebula two small round embers of unequal size, red-orange and yellow, no mouth; Quasar ONE central eye with a tall slit pupil;
     Pulsar a very wide, very thin slit (no round eye anywhere); Eclipse two mirrored crescents; Toxic Spill three acid eyes and a toothed grin;
     Strobe two white pill lamps in a visor; Sprinkler Head two blue eyes and a small smile.
  4. STROBE and SPRINKLER HEAD are the older looks of the build 384 review (9416af1): kinds fcstrobe and fcsprinkler2, same ids, names, glows, rules.
  5. UNDERCOVER and THE IRONS are as round 9 left them; Pulsar keeps its two narrow beams, wake, pulse profile, flare on the rim, equator ring, polar caps.
  6. Every drawing keeps its parts (one head, a body, the eye and mouth groups, special parts) in one figure.
  7. The ACADEMY's art is byte for byte c1d224b again (every character), the Fire Code characters changed are exactly the ones named here, the
     flare and rank banners, the unlock rules and the glows are as they were.

  (384 r6 eyes) leg 7 lets exactly Forge, Lunar, Solar and Tempest differ, in both classes, for their new eyes (check-b384-r6-eyes.py);
  (384 r7 eyes) and Inferno too, for the rulers' glare (check-b384-r7-eyes.py);
  it FAILS on 130a41c, where they still match.

  ROUND 12 (r9-chars, Madison's picks from the version sheet) moved the goalposts this gate was written to: Fire Code's four secret flares
  are now Nebula (round 5's face), Quasar (build 383's recon drawing), Whiteout and Firebird, The Irons is the Fire Marshal (a person), and the Drone Pilot and Star
  Ranger are round 3's again. 1, 2c, 2d, 3 and 7 follow that; 5 is retired (check-b384-r9-chars has those characters).

  python3 tools/check-b384-r5-chars.py [--against OLD/index.html]       (every line group must FAIL on 7b65a06; the faces legs also on c1d224b)
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
from playwright.sync_api import sync_playwright
BODY = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read() if "--against" in sys.argv else None
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:500], flush=True)

seed = dict(rc["SEED"]); seed.update(seenClassTip=True, novaMet=99, publicId="tst4fc9chars4", classes=["academy", "ifc"])
S = json.dumps(json.dumps(seed))
INIT_IFC = ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
        "localStorage.setItem('class26e.drill.v1',%s);localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));"
        "localStorage.setItem('class26e.greet.ifc','done');['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted','class26e.a2hs'].forEach(k=>localStorage.setItem(k,'1'));"
        "localStorage.setItem('class26e.ifc.drill.v1',%s);}catch(e){}") % (S, S)
INIT_ACA = ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
            "localStorage.setItem('class26e.drill.v1',%s);}catch(e){}") % S

# ---- what the page measures (the same function runs in both classes) ----
SNAP = r"""() => {
  document.getElementById('splashscreen')?.remove();
  const host = document.createElement('div'); host.style.cssText = 'position:fixed;left:0;top:0;width:340px;height:340px;opacity:0;pointer-events:none';
  document.body.appendChild(host);
  const hash = s => { let h = 2166136261; for(let i = 0; i < s.length; i++){ h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0).toString(16); };
  const mount = id => { const s = drawAvatarCharSVG(id); s.setAttribute('width', 340); s.setAttribute('height', 340); host.appendChild(s); return s; };
  const shapes = n => n ? n.querySelectorAll('path,circle,ellipse,rect').length : 0;
  /* two lit dots set symmetrically either side of the face's middle, anywhere in the drawing but its sparkles, its special and the flares it wears */
  const pairs = s => { const dots = [...s.querySelectorAll('circle,ellipse')].filter(e => !e.closest('.cx-fx-sparkles, .cx-sp, .cx-fx-flare, defs, clipPath')).map(e => ({ x: +e.getAttribute('cx'), y: +e.getAttribute('cy'), r: +(e.getAttribute('r') || e.getAttribute('rx')) })).filter(d => d.y >= 14 && d.y <= 26 && d.r > .5 && d.r <= 3);
    let n = 0; for(let i = 0; i < dots.length; i++) for(let j = i + 1; j < dots.length; j++){ const a = dots[i], b = dots[j]; if(Math.abs(a.y - b.y) < .2 && Math.abs(a.r - b.r) < .05 && Math.abs((a.x + b.x) / 2 - 20) < .15 && Math.abs(a.x - b.x) > 3) n++; } return n; };
  /* ---- the face signature: read off the eye and mouth groups of the drawn SVG ---- */
  const rgbOf = (el, svg) => { let f = el.getAttribute('fill') || ''; if(!f || f === 'none') return null;
    const rgb = h => { const m = (h || '').match(/^#([0-9a-fA-F]{6})$/); return m ? [0, 2, 4].map(i => parseInt(m[1].substr(i, 2), 16) / 255) : null; };
    const u = f.match(/^url\(#([^)]+)\)/);
    if(u){ const g = svg.querySelector('[id="' + u[1] + '"]'); const cs = g ? [...g.querySelectorAll('stop')].map(st => rgb(st.getAttribute('stop-color'))).filter(Boolean) : []; return cs.length ? [0, 1, 2].map(i => cs.reduce((a, c) => a + c[i], 0) / cs.length) : [.5, .5, .5]; }
    return rgb(f); };
  const hslOf = ([r, g, b]) => { const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn, l = (mx + mn) / 2, sat = d ? d / (1 - Math.abs(2 * l - 1)) : 0; let h = 0; if(d){ h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4; h *= 60; if(h < 0) h += 360; } return { h, s: sat, l }; };
  const hueName = c => { if(!c) return 'none'; const o = hslOf(c); if(o.l < .16) return 'dark'; if(o.s < .2) return o.l > .75 ? 'white' : 'grey'; return 'h' + Math.floor(o.h / 40); };
  const effOp = (el, stop) => { let o = 1, n = el; while(n && n !== stop){ const v = n.getAttribute && n.getAttribute('opacity'); if(v !== null && v !== undefined && v !== '') o *= parseFloat(v); n = n.parentNode; } return o; };
  const fillRatio = el => { try{ const b = el.getBBox(); let hit = 0, tot = 0; const N = 18; for(let i = 0; i < N; i++) for(let j = 0; j < N; j++){ tot++; if(el.isPointInFill(new DOMPoint(b.x + (i + .5) / N * b.width, b.y + (j + .5) / N * b.height))) hit++; } return hit / tot; }catch(e){ return -1; } };
  const faceSig = svg => {
    const eg = svg.querySelector('.cx-eyes'), mg = svg.querySelector('.cx-mouth');
    const shapesOf = g => g ? [...g.querySelectorAll('path,circle,ellipse,rect')].filter(e => !e.closest('defs,clipPath')) : [];
    const els = shapesOf(eg).map(e => { const b = e.getBBox(), c = rgbOf(e, svg); return { tag: e.tagName, x: b.x, y: b.y, w: b.width, h: b.height, area: b.width * b.height, fill: c, op: effOp(e, eg.parentNode), ratio: e.tagName === 'path' && !c ? -1 : fillRatio(e), stroke: !c }; });
    const bodies = els.filter(o => o.fill && o.op >= .6 && o.area >= .6);
    const big = bodies.slice().sort((a, b) => b.area - a.area)[0];
    const kindOf = o => { if(!o) return 'none'; const asp = o.w / o.h; if(o.ratio >= 0 && o.ratio < .55) return 'crescent'; if(asp >= 3 || asp <= 1 / 3) return 'slit'; if(o.tag === 'rect' && o.ratio > .85) return asp > 1.25 ? 'pill' : 'square'; if(o.ratio < .68) return 'lens'; return asp > 1.25 ? 'wide' : asp < .8 ? 'tall' : 'round'; };
    const heavy = bodies.filter(o => big && o.area >= big.area * .45);
    const clusters = [...new Set(heavy.map(o => Math.round((o.x + o.w / 2) * 2) / 2))].length;
    const lampCand = bodies.filter(o => { const h = hslOf(o.fill); return h.s >= .3 && h.l > .15 && h.l < .92; }).sort((a, b) => b.area - a.area)[0];
    const lamp = lampCand ? hueName(lampCand.fill) : (bodies.some(o => hslOf(o.fill).l > .78) ? 'white' : 'dark');
    const size = !big ? 'none' : Math.sqrt(big.area) < 1.3 ? 'xs' : Math.sqrt(big.area) < 2.4 ? 's' : Math.sqrt(big.area) < 3.6 ? 'm' : 'l';
    const ms = shapesOf(mg).map(e => e.getBBox()); const mx0 = Math.min(...ms.map(b => b.x)), mx1 = Math.max(...ms.map(b => b.x + b.width)), my0 = Math.min(...ms.map(b => b.y)), my1 = Math.max(...ms.map(b => b.y + b.height));
    const mouth = !ms.length ? 'none' : 'm' + (mx1 - mx0 < 2 ? 'dot' : mx1 - mx0 < 4 ? 'small' : 'wide') + (my1 - my0 < .9 ? 'flat' : 'open') + (ms.length >= 6 ? 'teeth' : '');
    const q = v => Math.round(v * 4) / 4;
    const fine = JSON.stringify([els.map(o => [o.tag, q(o.x), q(o.y), q(o.w), q(o.h), o.fill ? o.fill.map(v => Math.round(v * 255)).join(',') : 's', Math.round(o.op * 10)]), ms.map(b => [q(b.x), q(b.y), q(b.width), q(b.height)])]);
    return { n: els.length, clusters, kind: kindOf(big), size, lamp, mouth, coarse: [clusters, kindOf(big), size, lamp, mouth].join('|'), fine: hash(fine), asp: big ? big.w / big.h : 0, ratio: big ? big.ratio : 0,
      bodies: bodies.map(o => [+(o.x + o.w / 2).toFixed(2), +(o.y + o.h / 2).toFixed(2), +o.w.toFixed(2), +o.h.toFixed(2), hueName(o.fill), kindOf(o), +o.ratio.toFixed(2)]), sizes: heavy.map(o => +Math.sqrt(o.area).toFixed(2)), lamps: [...new Set(heavy.map(o => hueName(o.fill)))], minAsp: Math.min(...bodies.map(o => o.w / o.h)), maxAsp: Math.max(...bodies.map(o => o.w / o.h)), kinds: [...new Set(heavy.map(kindOf))] };
  };
  const out = { cls: window.NOVA_CLASS || 'academy', chars: {}, names: {}, feats: {} };
  for(const c of AVATAR_CHARACTERS.filter(c => !c.retired && !c.legacy)){
    const s = mount(c.id); const fig = s.querySelector('.cx-fig') || s;
    const eyes = s.querySelector('.cx-eyes'), shut = s.querySelector('.cx-eyes-closed'), mouth = s.querySelector('.cx-mouth'), head = s.querySelector('.cx-head');
    out.chars[c.id] = { kind: c.kind, face: faceSig(s), eyes: shapes(eyes), mouth: shapes(mouth), pairs: pairs(s), heads: s.querySelectorAll('.cx-head').length, bodies: s.querySelectorAll('.cx-body').length,
      hasEyes: !!eyes, hasShut: !!shut, hasMouth: !!mouth, sp: s.querySelectorAll('.cx-sp').length,
      sameParent: !!(head && s.querySelector('.cx-body') && head.parentNode === s.querySelector('.cx-body').parentNode), filter: /<filter|filter=/.test(new XMLSerializer().serializeToString(s)),
      hash: hash(new XMLSerializer().serializeToString(s).split(s.getAttribute('data-cx-uid')).join('U')) };
    out.names[c.id] = AVATAR_DISPLAY_NAME[c.id] || c.name; out.feats[c.id] = c.feat || c.unlock || '';
    s.remove();
  }
  /* the banners: every banner's art, hashed */
  out.banners = {};
  Object.keys(BANNER_ART).forEach(id => { try{ const a = BANNER_ART[id]('gq'); out.banners[id] = hash(Array.isArray(a) ? a.map(l => (l.svg || '') + (l.kids || []).map(k => k.svg || '').join('')).join('') : String(a)); }catch(e){ out.banners[id] = 'err'; } });
  out.glows = Object.fromEntries(['detective', 'masked', 'poseidon', 'clown', 'valkyrie', 'marksman', 'astronaut', 'hacker', 'timekeeper', 'ronin', 'hive'].map(i => [i, (AVATAR_GLOW[i] || '').toLowerCase()]));
  /* ---- the four redrawn characters in the Fire Code class ---- */
  if(window.NOVA_CLASS === 'ifc'){
    const P = s => [...s.querySelectorAll('path')].map(p => ({ d: p.getAttribute('d') || '', f: p.getAttribute('fill') || '', st: p.getAttribute('stroke') || '', b: p.getBBox() }));
    { const s = mount('valkyrie'); const p = P(s); const ser = new XMLSerializer().serializeToString(s);
      const lens = p.find(o => /^url\(/.test(o.f) && o.b.width > 14 && o.b.width < 17 && o.b.y > 18 && o.b.y < 20);
      const coil = p.find(o => (o.d.match(/Q/g) || []).length >= 10 && o.f === 'none' && o.b.x + o.b.width > 28);
      const mn = ((s.querySelector('.cx-mouth path') || { getAttribute: () => '' }).getAttribute('d').match(/-?[\d.]+/g) || []).map(Number);
      out.agent = { hat: /cx-fc-hat/.test(ser), lens: !!lens, coil: !!coil, flaps: [...s.querySelectorAll('.cx-collar > path')].filter(q => /^url\(/.test(q.getAttribute('fill') || '')).length,
        mouthCurve: mn.length >= 6 ? Math.abs(mn[3] - (mn[1] + mn[5]) / 2) : 99, hair: p.filter(o => /^url\(/.test(o.f) && o.b.y < 10).length >= 1, wallet: /#E8B84A/.test(ser), led: !!s.querySelector('.cx-head .cx-fx-led') };
      s.remove(); }
    { const s = mount('timekeeper'); const ser = new XMLSerializer().serializeToString(s);
      out.irons = { hat: /cx-fc-hat/.test(ser), tools: [...s.querySelectorAll('.cx-head > g[transform]')].map(g => g.getAttribute('transform')),
        cross: [...s.querySelectorAll('.cx-body path')].filter(p => ((p.getAttribute('d') || '').match(/M/g) || []).length === 5).length,
        shield: !!s.querySelector('.cx-body path[stroke^="url("]'), glints: !!s.querySelector('.cx-fx-star') };
      s.remove(); }
    { const s = mount('singularity'); const ser = new XMLSerializer().serializeToString(s);
      const nums = d => (d.match(/-?[\d.]+/g) || []).map(Number);
      const wedges = [...s.querySelectorAll('.cx-fx-fcpulse path')].map(p => { const n = nums(p.getAttribute('d')); return { op: p.getAttribute('opacity'), w1: Math.hypot(n[2] - n[4], n[3] - n[5]), L: Math.hypot((n[2] + n[4]) / 2 - (n[0] + n[6]) / 2, (n[3] + n[5]) / 2 - (n[1] + n[7]) / 2) }; });
      const f = s.querySelector('.cx-fx-flare circle:nth-of-type(2)'); const head = [...s.querySelectorAll('.cx-head circle')].filter(c => /^url\(/.test(c.getAttribute('fill') || '')).sort((a, b) => b.getAttribute('r') - a.getAttribute('r'))[0];
      const off = f && head ? Math.abs(Math.hypot(+f.getAttribute('cx') - +head.getAttribute('cx'), +f.getAttribute('cy') - +head.getAttribute('cy')) - +head.getAttribute('r')) : 99;
      out.pulsar = { narrow: wedges.filter(w => !w.op && w.w1 < 3.6 && w.L > 18).length, flareOff: off, rings: [...s.querySelectorAll('.cx-fx-sqlight[transform*="rotate"]')].length, caps: !!s.querySelector('.cx-head g[clip-path]'), bands: [...s.querySelectorAll('.cx-head path')].filter(p => p.getAttribute('stroke') === '#7FC8FF' && /Q/.test(p.getAttribute('d') || '')).length,
        profile: [...s.querySelectorAll('.cx-body path')].filter(p => (p.getAttribute('d') || '').split('L').length > 15).length, pulse: s.querySelectorAll('.cx-eyes .cx-fx-fcpulse').length };
      s.remove(); }
  }
  return out; }"""

def run(init, label):
    srv, port = rc["serve"]()
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=rc["CHROME"])
        ctx = br.new_context(viewport={"width": 440, "height": 956}, device_scale_factor=1)
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
        if BODY is not None:
            pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
        pg.add_init_script(init)
        pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(3500)
        r = pg.evaluate(SNAP)
        ctx.close(); br.close()
    srv.shutdown()
    chk("%s: the page is the %s class with no page error (%s)" % (label, r["cls"], errs[:2]), not errs, errs)
    return r

IFC = run(INIT_IFC, "Fire Code")
ACA = run(INIT_ACA, "Academy")
if "--dump" in sys.argv:   # writes the hashes of THIS build (run against c1d224b to make check-b384-r5-chars.prev.json)
    json.dump({k: {"banners": R["banners"], "chars": {i: c["hash"] for i, c in R["chars"].items()}} for k, R in (("ifc", IFC), ("academy", ACA))}, open(os.path.join(HERE, "check-b384-r5-chars.prev.json"), "w"), indent=0)
    print("dumped"); sys.exit(0)

if "--faces" in sys.argv:
    for key, R in (("ifc", IFC), ("academy", ACA)):
        print("==", key)
        for i, c in R["chars"].items(): f = c["face"]; print("%-12s %-16s %-34s fine=%s n=%s sizes=%s lamps=%s asp=%.2f ratio=%.2f" % (i, R["names"][i], f["coarse"], f["fine"], f["n"], f["sizes"], f["lamps"], f["asp"], f["ratio"]))
    sys.exit(0)

N = IFC["names"]; CI = IFC["chars"]; CA = ACA["chars"]
def faced(C): return {i for i, c in C.items() if c["eyes"] or c["mouth"] or c["pairs"]}
# ---- 1. faces exist: the only characters with no mark at all are the two who hide theirs on purpose ----
# (384 round 12, r9-chars) The Irons is gone: the Fire Marshal in its place is a person with a face, so Fire Code has no bare drawing left
for key, R, expect in (("ifc", IFC, set()), ("academy", ACA, {"valkyrie", "voidwalker"})):
    C = R["chars"]; bare = {i for i, c in C.items() if c["eyes"] == 0 and c["mouth"] == 0 and c["pairs"] == 0}
    chk("1. [%s] the characters with no face mark at all are only %s (found %s)" % (key, sorted(expect), sorted(bare)), bare == expect, {"extra": sorted(bare - expect), "missing": sorted(expect - bare)})
MUST = {"ifc": {"clown": "Strobe", "astronaut": "Toxic Spill", "hive": "Sprinkler Head", "voidwalker": "Nebula", "umbra": "Quasar", "singularity": "Whiteout", "genesis": "Firebird"},   # (round 12 names)
        "academy": {"hive": "Hive", "genesis": "Genesis"}}
for key, R in (("ifc", IFC), ("academy", ACA)):
    C = R["chars"]
    chk("1. [%s] these have a face again: %s" % (key, sorted(MUST[key].values())), all(i in faced(C) and C[i]["face"]["n"] >= 2 and R["names"][i] == MUST[key][i] for i in MUST[key]), {i: (C[i]["eyes"], C[i]["mouth"], C[i]["face"]["n"]) for i in MUST[key]})
    for i in ("ghost", "grizzly", "alien"):
        chk("1. [%s] the %s keeps both eyes and its mouth (%s eye marks, %s mouth)" % (key, i, C[i]["eyes"], C[i]["mouth"]), C[i]["eyes"] >= 4 and C[i]["mouth"] >= 1, C[i])
    gone = [i for i, c in C.items() if i in MUST[key] and not (c["hasEyes"] and c["hasShut"] and c["hasMouth"])]
    chk("1. [%s] each keeps its eye, closed-eye and mouth groups (missing: %s)" % (key, gone), not gone, gone)

# ---- 2. no copy-paste: the signature of every face, read off the drawing ----
NONHUMAN = {"ifc": ["ghost", "grizzly", "alien", "clown", "astronaut", "hive", "voidwalker", "umbra", "singularity", "genesis"], "academy": ["ghost", "grizzly", "alien", "hive", "genesis"]}
for key, R in (("ifc", IFC), ("academy", ACA)):
    C = R["chars"]; F = faced(C)
    fine = {}
    for i in F: fine.setdefault(C[i]["face"]["fine"], []).append(i)
    dup = [v for v in fine.values() if len(v) > 1]
    chk("2a. [%s] no two characters share a FINE face signature (every eye and mouth shape, its place and colour; %d faces, shared: %s)" % (key, len(F), dup), not dup, dup)
    co = {}
    for i in NONHUMAN[key]: co.setdefault(C[i]["face"]["coarse"], []).append(i)
    dup = [(k, v) for k, v in co.items() if len(v) > 1]
    chk("2b. [%s] no two non-human faces share a COARSE signature (eyes|shape|size|colour|mouth): %s" % (key, {i: C[i]["face"]["coarse"] for i in NONHUMAN[key]}), not dup, dup)
FL = ["voidwalker", "umbra", "singularity", "genesis"]
def differ(C, a, b):
    fa, fb = C[a]["face"], C[b]["face"]
    return fa["kind"] != fb["kind"] and fa["lamp"] != fb["lamp"]
# (384 round 12) Madison picked round 5's Nebula (two lit eyes and a mouth) and the Firebird is a bird with amber eyes, so two of the four now share
# a warm hue; they must still differ in eye SHAPE or colour, and no two may carry the same number of eyes AND the same mouth (2d)
def differ_any(C, a, b):
    fa, fb = C[a]["face"], C[b]["face"]
    return fa["kind"] != fb["kind"] or fa["lamp"] != fb["lamp"]
bad = [(a, b, CI[a]["face"]["kind"], CI[b]["face"]["kind"], CI[a]["face"]["lamp"], CI[b]["face"]["lamp"]) for n, a in enumerate(FL) for b in FL[n + 1:] if not differ_any(CI, a, b)]
chk("2c. the four secret flares differ from each other in eye shape or colour: %s" % {N[i]: (CI[i]["face"]["kind"], CI[i]["face"]["lamp"], CI[i]["face"]["clusters"]) for i in FL}, not bad, bad)
chk("2c. Strobe and Sprinkler Head differ in eye shape AND colour: %s" % {N[i]: (CI[i]["face"]["kind"], CI[i]["face"]["lamp"]) for i in ("clown", "hive")}, differ(CI, "clown", "hive"), {i: CI[i]["face"] for i in ("clown", "hive")})
sig2d = [(CI[i]["face"]["clusters"], CI[i]["face"]["mouth"]) for i in FL]
chk("2d. the four flares are not one treatment stamped four times: no two carry the same number of eyes and the same mouth (%s)" % {N[i]: (CI[i]["face"]["clusters"], CI[i]["face"]["mouth"]) for i in FL},
    len(set(sig2d)) == 4, {i: CI[i]["face"] for i in FL})
# the same eyes must not be stamped on the secret flares and Toxic Spill either (the other glowing-eyed one)
bad = [i for i in FL if CI[i]["face"]["coarse"] == CI["astronaut"]["face"]["coarse"] or CI[i]["face"]["fine"] == CI["astronaut"]["face"]["fine"]]
chk("2c. ...and none of them wears Toxic Spill's face either (%s)" % bad, not bad, bad)

# ---- 3. each one's own face ----
# (384 round 12, r9-chars) the four flares' own faces: Nebula round 5's (two lit eyes, orange and gold, and a small mouth), Quasar build 383's recon figure's
# (two narrow violet eyes in the slot of the wrap, no mouth), Whiteout two pale lenses of light behind the goggles (no mouth: the gaiter),
# Firebird two round amber eyes and a beak. check-b384-r9-chars measures the rest of each.
f = CI["voidwalker"]["face"]
chk("3. Nebula: two lit eyes (%s), orange and gold (%s), a small mouth (%s)" % (f["clusters"], f["lamps"], f["mouth"]), f["clusters"] == 2 and {"h0", "h1"} <= set(f["lamps"]) and f["mouth"] not in ("none",) and f["mouth"].startswith("msmall"), f)
f = CI["umbra"]["face"]
chk("3. Quasar (the recon figure): violet eyes (%s, %s), no mouth (%s)" % (f["lamp"], f["kind"], f["mouth"]), f["lamp"] == "h6" and f["mouth"] == "none", f)
f = CI["singularity"]["face"]
chk("3. Whiteout: two pale lenses of light (%s, %s, %s eyes), no mouth (%s)" % (f["kind"], f["lamp"], f["clusters"], f["mouth"]), f["clusters"] == 2 and f["lamp"] in ("white", "h4", "h5") and f["mouth"] == "none", f)
f = CI["genesis"]["face"]
chk("3. Firebird: two round eyes (%s, %s eyes) and a beak for a mouth (%s)" % (f["kind"], f["clusters"], f["mouth"]), f["clusters"] == 2 and f["kind"] == "round" and f["mouth"] != "none", f)
f = CI["astronaut"]["face"]; eyes3 = {round(b[0] * 2) / 2 for b in f["bodies"] if b[2] * b[3] >= 4}
chk("3. Toxic Spill keeps its three acid eyes (%s) and its toothed grin (%s)" % (sorted(eyes3), f["mouth"]), len(eyes3) == 3 and f["mouth"].startswith("mwideopen"), f)
f = CI["clown"]["face"]
chk("3. Strobe: two white pill lamps in a visor (%s, %s, %s eyes), a horn slot for a mouth (%s)" % (f["kind"], f["lamp"], f["clusters"], f["mouth"]), f["kind"] == "pill" and f["lamp"] == "white" and f["clusters"] == 2 and f["mouth"] != "none", f)
f = CI["hive"]["face"]
chk("3. Sprinkler Head: two blue eyes (%s, %s, %s eyes)" % (f["kind"], f["lamp"], f["clusters"]), f["lamp"] == "h5" and f["clusters"] == 2, f)

# ---- 4. strobe and sprinkler are the older looks ----
chk("4. clown is Strobe (fcstrobe) and hive Sprinkler Head (fcsprinkler2), the older drawings of the 384 review (%s %s, %s %s)" % (N["clown"], CI["clown"]["kind"], N["hive"], CI["hive"]["kind"]),
    (N["clown"], CI["clown"]["kind"], N["hive"], CI["hive"]["kind"]) == ("Strobe", "fcstrobe", "Sprinkler Head", "fcsprinkler2"), N)
# ---- 5. Undercover, The Irons, Pulsar's structure ----
# (384 round 12) RETIRED: round 9's Undercover, The Irons and Pulsar are all replaced; check-b384-r9-chars asserts the new Undercover, the Fire
# Marshal and the Whiteout
print("RETIRED 5 (round 9's Undercover, The Irons and Pulsar were replaced in round 12; see check-b384-r9-chars)")

# ---- 6. every drawing is whole ----
for key, R in (("ifc", IFC), ("academy", ACA)):
    bad = [i for i, c in R["chars"].items() if c["heads"] != 1 or c["bodies"] < 1 or not c["sameParent"] or c["filter"] or (c["sp"] < 1 and i != "forge")]
    chk("6. [%s] every character has one head, a body in the same figure, special parts (forge has none, as before) and no svg filter (bad: %s)" % (key, bad), not bad, {i: R["chars"][i] for i in bad})

# ---- 7. rules, glows, banners, and everybody else's art ----
glows = list(IFC["glows"].values())
chk("7. the eleven challenge characters have eleven different glow colours (%s)" % glows, len(set(glows)) == 11, glows)
FEATS = {"valkyrie": "studyrun7", "timekeeper": "days30", "hive": "busyday300", "singularity": "flare5", "clown": "vrwins5", "astronaut": "hundo7day"}
chk("7. every unlock rule is as it was (%s)" % {i: IFC["feats"][i] for i in FEATS}, all(IFC["feats"][i] == f for i, f in FEATS.items()) and all(ACA["feats"][i] == f for i, f in FEATS.items()), IFC["feats"])
PREV = json.load(open(os.path.join(HERE, "check-b384-r5-chars.prev.json")))
PINNED = lambda i: i.startswith("flare_") or i.endswith("_rank") or i in ("astral", "celestial", "zenith", "galaxy")   # (the banners round of 384 changed seven others on purpose)
for key, R in (("ifc", IFC), ("academy", ACA)):
    # (384 round 9, r9-banners) Madison asked for the Fire Code class's four secret flare banners to be redrawn ("The secret flare ones need to be better");
    # check-b384-r9-banners.py holds them now, and pins every academy banner byte for byte
    R9F = ("flare_void", "flare_umbra", "flare_horizon", "flare_genesis") if key == "ifc" else ()
    moved = sorted(i for i, h in PREV[key]["banners"].items() if PINNED(i) and i not in R9F and R["banners"].get(i) != h)
    chk("7. [%s] no flare or rank banner moved since c1d224b (moved: %s)" % (key, moved), not moved, moved)
# (384 r6 eyes, check-b384-r6-eyes.py) Forge, Lunar, Solar and Tempest got eyes of their own, in both classes; Oracle, Frost and everybody
# else stay byte for byte, and only those four may (and must) differ
# (384 r7 eyes, check-b384-r7-eyes.py) the rulers' glare: Inferno joins them (its eyes and only its eyes), Oracle and Frost still do not
EYES4 = {"forge", "lunar", "solar", "tempest", "inferno"}
mov = sorted(i for i, h in PREV["academy"]["chars"].items() if ACA["chars"].get(i, {}).get("hash") != h)
chk("7. the ACADEMY's characters are byte for byte what c1d224b drew, all %d of them, bar the five rulers' new eyes (changed: %s)" % (len(PREV["academy"]["chars"]), mov), set(mov) == EYES4, {"changed": mov, "expected": sorted(EYES4)})
mov = sorted(i for i, h in PREV["ifc"]["chars"].items() if IFC["chars"].get(i, {}).get("hash") != h)
expect = {"clown", "valkyrie", "timekeeper", "hive", "voidwalker", "umbra", "singularity", "genesis",
          # (384 r6, check-b384-r6-chars.py) the police-gear round: the Inspector, Chief, Drone Pilot and Star Ranger redrawn, the Smoke
          # Diver's helmet navy, the Dispatcher's earcup lamp and collar; the Strobe's visor bar and the Pulsar's ring (both already named)
          "detective", "poseidon", "masked", "hacker"} | EYES4
# (384 round 12, r9-chars) the Drone Pilot and the Star Ranger are round 3's drawings again, byte for byte what c1d224b drew, so they are
# NOT in the changed set any more
chk("7. in Fire Code only the characters named here changed their art since c1d224b; Toxic Spill is exactly c1d224b's (changed: %s)" % mov, set(mov) == expect and "astronaut" not in mov, {"changed": mov, "expected": sorted(expect)})
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
