#!/usr/bin/env python3
"""Build 384, round 7: Madison's second review of the Fire Code characters (drawn in the Fire Code class only).

  "Inspector ... could the hat be a little darker? Make the clipboard better?"
  "Pyrotech is eh, what about like an undercover styled character? A character with some mystery."
  "Strobe is okay, doesn't look legit enough though, it's kinda hard to tell it's a strobe tbh."
  "Salamander is kinda random and not like any of the others.. could we change that?"
  "Toxic spill is cool, the purple stuff on the barrel isn't connected right though ... go through each character thoroughly
   to ensure all pieces connect right"
  "Sprinkler is kinda in the same position as strobe.. it's hard to tell now that it's a sprinkler head."
  "pulsar needs to be better..and I don't like solstice. Ensure each of them you can see how their secret flares come from
   their character"

  A. valkyrie is Undercover, timekeeper is The Irons (round 9; round 8 had the Lookout and the Smoke Alarm), genesis is Eclipse; Pyrotech, Salamander, Solstice, Lookout, Smoke Alarm and Pump Operator are gone
  B. the Inspector's hat is a darker felt than it was; his clipboard has a hand on it, two ticks and a cross, and is mostly inside the coin
  C. Strobe is the appliance: a mounting plate that frames the housing, ribs down its lens, the horn's speaker grille (upright slots, round 9: no face), FIRE in strokes
  D. Sprinkler Head (round 9: chrome, no face, no gold): threaded inlet, a frame block, a bulb between two arms joined to the block and the boss, a notched deflector under it, a fan of water
  E. Toxic Spill: the ooze spans the drum's width and every drip starts up inside the ooze, not on the rim
  F. each secret's flare sits ON its character: Quasar's on its ring, Pulsar's and Eclipse's on the rim of their head disc
  G. Undercover (round 9): a person in shades, a coiled earpiece wire, a turned-up collar, no hat; The Irons: two tools crossed over a shield
Every check fails on the build before:  python3 tools/check-b384-fcchars3.py --against OLD/index.html
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
from playwright.sync_api import sync_playwright
BODY = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read() if "--against" in sys.argv else None
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
seed = dict(rc["SEED"]); seed.update(seenClassTip=True, novaMet=99, publicId="tst4fc8chars3", classes=["academy", "ifc"])
S = json.dumps(json.dumps(seed))
INIT = ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
        "localStorage.setItem('class26e.drill.v1',%s);localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));"
        "localStorage.setItem('class26e.greet.ifc','done');['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted','class26e.a2hs'].forEach(k=>localStorage.setItem(k,'1'));"
        "localStorage.setItem('class26e.ifc.drill.v1',%s);}catch(e){}") % (S, S)
SNAP = r"""() => {
  document.getElementById('splashscreen')?.remove();
  const host = document.createElement('div'); host.style.cssText = 'position:fixed;left:0;top:0;width:340px;height:340px;opacity:0;pointer-events:none';
  document.body.appendChild(host);
  const mount = id => { const s = drawAvatarCharSVG(id); s.setAttribute('width', 340); s.setAttribute('height', 340); host.appendChild(s); return s; };
  const lum = h => { h = (h || '#000000').replace('#', ''); if(h.length !== 6) return null; const c = [0, 2, 4].map(i => parseInt(h.substr(i, 2), 16) / 255).map(v => v <= .04045 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4)); return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]; };
  const stops = (s, n) => { const f = (n && n.getAttribute('fill')) || ''; const m = f.match(/url\(#([^)]+)\)/); const g = m && s.querySelector('[id="' + m[1] + '"]'); return g ? [...g.querySelectorAll('stop')].map(x => x.getAttribute('stop-color')) : [f]; };
  const bb = n => { const b = n.getBBox(); return { x: b.x, y: b.y, w: b.width, h: b.height, cx: b.x + b.width / 2, cy: b.y + b.height / 2 }; };
  const out = { names: Object.fromEntries(AVATAR_CHARACTERS.filter(c => !c.retired && !c.legacy).map(c => [c.id, AVATAR_DISPLAY_NAME[c.id] || c.name])) };
  /* B: the inspector */
  { const s = mount('detective'); const hat = s.querySelector('.cx-fc-hat-cowboy'); const felt = hat && hat.querySelector('path');
    const ser = new XMLSerializer().serializeToString(s);
    out.insp = { feltBase: stops(s, felt)[1], ticks: (ser.match(/#2E9A5A/g) || []).length, crosses: (ser.match(/#D8342A/g) || []).length, hand: /#7A4A2A/.test(ser) };
    const board = [...s.querySelectorAll('.cx-body rect')].filter(r => Number(r.getAttribute('width')) > 7 && Number(r.getAttribute('height')) > 7 && r.getAttribute('fill') && r.getAttribute('fill').indexOf('url(') === 0)[0];
    if(board){ const b = board.getBoundingClientRect(), sr = s.getBoundingClientRect(), cx = sr.left + sr.width / 2, cy = sr.top + sr.height / 2, R = sr.width / 2;
      let inside = 0, n = 0; for(let i = 0; i <= 12; i++) for(let j = 0; j <= 12; j++){ const x = b.left + b.width * i / 12, y = b.top + b.height * j / 12; n++; if(Math.hypot(x - cx, y - cy) <= R * .97) inside++; }
      out.insp.boardIn = inside / n; out.insp.boardH = Number(board.getAttribute('height')); } else { out.insp.boardIn = 0; out.insp.boardH = 0; }
    s.remove(); }
  /* C: the strobe */
  { const s = mount('clown'); const head = s.querySelector('.cx-head');
    const ser = new XMLSerializer().serializeToString(s);
    const paths = [...head.querySelectorAll('path')].map(p => ({ p, b: p.getBBox(), f: p.getAttribute('fill') || '' })).filter(o => o.b.width > 15);
    const red = paths.find(o => /url\(#[^)]*head/.test(o.f)), plate = paths.filter(o => o !== red).sort((a, b) => b.b.width * b.b.height - a.b.width * a.b.height)[0];
    const ribs = [...head.querySelectorAll('path')].filter(p => /^M[\d.]+ 14\.5 V24\.1$/.test(p.getAttribute('d') || '')).length;
    const slots = [...head.querySelectorAll('path')].filter(p => /^M[\d.]+ 26\.5 v2$/.test(p.getAttribute('d') || '')).length;
    const mg = (red && plate) ? Math.min(red.b.x - plate.b.x, plate.b.x + plate.b.width - red.b.x - red.b.width, red.b.y - plate.b.y, plate.b.y + plate.b.height - red.b.y - red.b.height) : -1;
    out.strobe = { eyes: s.querySelectorAll('.cx-eyes > *').length, plateMargin: mg, ribs, slots, flash: !!s.querySelector('.cx-fx-fcflash'), screws: (ser.match(/<circle[^>]*r="0?\.62"/g) || []).length };
    s.remove(); }
  /* D: the sprinkler (round 9: chrome, no face) */
  { const s = mount('hive'); const head = s.querySelector('.cx-head'); const ser = new XMLSerializer().serializeToString(s);
    const ser2 = [...s.querySelectorAll('.cx-head, .cx-body')].map(g => new XMLSerializer().serializeToString(g)).join('');
    const P = [...head.querySelectorAll('path')].map(p => ({ d: p.getAttribute('d') || '', b: p.getBBox() }));
    const by = pre => P.find(o => o.d.indexOf(pre) === 0);
    const rim = [...P].sort((a, b) => b.d.split('L').length - a.d.split('L').length)[0];
    const bulb = by('M18.4 19.6 Q18.4 18.9'), block = by('M12.8 16 L27.2 16'), boss = by('M17.4 27.2 L22.6 27.2'), arms = by('M13.2 18.2'), plate = by('M10.6 9.6'), inlet = by('M17 10.6 L23 10.6'), pipe = by('M18 -12 L22 -12');
    const hues = [...ser2.matchAll(/#([0-9A-Fa-f]{6})/g)].map(m => { const h = m[1], r = parseInt(h.substr(0, 2), 16) / 255, g = parseInt(h.substr(2, 2), 16) / 255, b = parseInt(h.substr(4, 2), 16) / 255, mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn; if(!d) return null; let hh = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4; hh *= 60; if(hh < 0) hh += 360; const l = (mx + mn) / 2; return { hh, s: d / (1 - Math.abs(2 * l - 1)), l }; }).filter(Boolean);
    const gold = hues.filter(o => o.hh >= 38 && o.hh <= 52 && o.s >= .5 && o.l >= .3 && o.l <= .85).length;
    const B = o => o ? { y: o.b.y, bottom: o.b.y + o.b.height } : null;
    out.spr = { rimVerts: rim ? rim.d.split('L').length : 0, rimBox: rim ? { y: rim.b.y, h: rim.b.height } : null, eyes: s.querySelectorAll('.cx-eyes > *').length, bulb: B(bulb), block: B(block), boss: B(boss), arms: B(arms), plate: B(plate), inlet: B(inlet), pipe: B(pipe),
      ridges: P.filter(o => /^M17 [\d.]+ L23 [\d.]+$/.test(o.d)).length, gold, streaks: P.length && [...s.querySelectorAll('.cx-body path')].filter(p => /^M[\d.]+ 31\.6 Q/.test(p.getAttribute('d') || '')).length, red: /#FF5A4E/.test(ser) };
    s.remove(); }
  /* E: the toxic spill */
  { const s = mount('astronaut'); const head = s.querySelector('.cx-head');
    const ooze = head.querySelector('path'); const ob = ooze.getBBox(); const of = ooze.getAttribute('fill');
    const drips = [...s.querySelectorAll('path')].filter(p => p.getAttribute('fill') === of && !p.closest('.cx-head') && !p.closest('.cx-body'));
    const tops = drips.map(p => { const b = p.getBBox(), t = (b.x + b.width / 2 - 7.8) / 24.4, lip = 27.2 + 7.8 * t * (1 - t); return { top: b.y, lip, up: lip - b.y }; });
    out.spill = { x0: ob.x, x1: ob.x + ob.width, n: drips.length, minUp: tops.length ? Math.min(...tops.map(t => t.up)) : -9 };
    s.remove(); }
  /* F: the secrets' flares on their characters */
  const ptsOf = (el, n) => { const L = el.getTotalLength(), m = el.transform.baseVal.numberOfItems ? el.transform.baseVal.consolidate().matrix : null; const a = [];
    for(let i = 0; i <= n; i++){ const p = el.getPointAtLength(L * i / n); a.push(m ? { x: m.a * p.x + m.c * p.y + m.e, y: m.b * p.x + m.d * p.y + m.f } : { x: p.x, y: p.y }); } return a; };
  const flareOf = s => { const g = s.querySelector('.cx-fx-flare'); const c = g && g.querySelector('circle:nth-of-type(2)'); return c ? { x: +c.getAttribute('cx'), y: +c.getAttribute('cy') } : null; };
  out.flare = {};
  { const s = mount('umbra'); const f = flareOf(s);
    const rings = [...s.querySelectorAll('.cx-fx-disc path')].filter(p => /A15\.6 4\.4/.test(p.getAttribute('d') || '') || true);
    let best = 99; if(f) rings.forEach(r => { try{ ptsOf(r, 240).forEach(p => { best = Math.min(best, Math.hypot(p.x - f.x, p.y - f.y)); }); }catch(e){} });
    out.flare.umbra = { f, ringDist: best }; s.remove(); }
  const discOf = (s, id) => { const cs = [...s.querySelectorAll('.cx-head circle')].map(c => ({ cx: +c.getAttribute('cx'), cy: +c.getAttribute('cy'), r: +c.getAttribute('r'), fill: c.getAttribute('fill') || '' })).filter(c => /^url\(/.test(c.fill)).sort((a, b) => b.r - a.r); return cs[0]; };
  for(const id of ['singularity', 'genesis']){ const s = mount(id); const f = flareOf(s), d = discOf(s, id);
    out.flare[id] = { f, d, off: f && d ? Math.abs(Math.hypot(f.x - d.cx, f.y - d.cy) - d.r) : 99 }; s.remove(); }
  /* G (round 9): Undercover and The Irons */
  { const s = mount('valkyrie'); const ser = new XMLSerializer().serializeToString(s);
    const P = [...s.querySelectorAll('path')].map(p => ({ d: p.getAttribute('d') || '', f: p.getAttribute('fill') || '', b: p.getBBox() }));
    const lens = P.find(o => o.d.indexOf('Q') > 0 && /^url\(/.test(o.f) && o.b.width > 14 && o.b.width < 17 && o.b.y > 18 && o.b.y < 20);
    const coil = P.find(o => (o.d.match(/Q/g) || []).length >= 10 && o.f === 'none' && o.b.x + o.b.width > 28);
    const mouth = s.querySelector('.cx-mouth path'); const mn = mouth ? (mouth.getAttribute('d').match(/-?[\d.]+/g) || []).map(Number) : [];
    out.agent = { person: /cx-fc-hat/.test(ser), eyes: s.querySelectorAll('.cx-eyes > *').length, lens: lens ? { w: lens.b.width, y: lens.b.y, h: lens.b.height } : null, coil: coil ? { top: coil.b.y, bottom: coil.b.y + coil.b.height } : null,
      collar: [...s.querySelectorAll('.cx-collar > path')].filter(p => /^url\(/.test(p.getAttribute('fill') || '')).length, collarTop: Math.min(...[...s.querySelectorAll('.cx-collar > path')].map(p => p.getBBox().y)),
      mouthCurve: mn.length >= 6 ? Math.abs(mn[3] - (mn[1] + mn[5]) / 2) : 99, wallet: /#E8B84A/.test(ser), earLed: !!s.querySelector('.cx-head .cx-fx-led') };
    s.remove(); }
  { const s = mount('timekeeper'); const ser = new XMLSerializer().serializeToString(s);
    const tools = [...s.querySelectorAll('.cx-head > g[transform]')].map(g => g.getAttribute('transform'));
    const cross = [...s.querySelectorAll('.cx-body path')].filter(p => ((p.getAttribute('d') || '').match(/M/g) || []).length === 5).length;
    out.irons = { person: /cx-fc-hat/.test(ser), eyes: s.querySelectorAll('.cx-eyes > *').length, tools, cross, shield: !!s.querySelector('.cx-body path[stroke^="url("]'), glints: !!s.querySelector('.cx-fx-star') };
    s.remove(); }
  return out; }"""
srv, port = rc["serve"]()
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    ctx = br.new_context(viewport={"width": 440, "height": 956}, device_scale_factor=1)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    if BODY is not None:
        pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    pg.add_init_script(INIT)
    pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(3500)
    r = pg.evaluate(SNAP)
    ctx.close(); br.close()
srv.shutdown()
def lum(h):
    h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]; c = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]
chk("no page errors (%s)" % errs[:2], not errs, errs)
N = r["names"]
chk("A. valkyrie is Undercover, timekeeper The Irons, genesis Eclipse (%s, %s, %s)" % (N.get("valkyrie"), N.get("timekeeper"), N.get("genesis")),
    (N.get("valkyrie"), N.get("timekeeper"), N.get("genesis")) == ("Undercover", "The Irons", "Eclipse"), N)
chk("A. Pyrotech, Salamander, Solstice, Lookout, Smoke Alarm and Pump Operator are gone from the class's list", not {"Pyrotech", "Salamander", "Solstice", "Lookout", "Smoke Alarm", "Pump Operator"} & set(N.values()), N)
I = r["insp"]
fb = lum(I["feltBase"]) if I.get("feltBase") else 1
chk("B. the Inspector's hat is a darker felt: base %s, luminance %.2f (it was .52; now under .40 and still not black, over .10)" % (I.get("feltBase"), fb), .10 < fb < .40, I)
chk("B. his clipboard: two ticks and a cross on the form, a hand on the board (%s ticks, %s crosses, hand %s)" % (I["ticks"], I["crosses"], I["hand"]), I["ticks"] >= 2 and I["crosses"] >= 1 and I["hand"], I)
chk("B. ...and the board is bigger (%.1f units tall, it was 7.4) with most of it inside the coin (%.2f)" % (I["boardH"], I["boardIn"]), I["boardH"] >= 8.5 and I["boardIn"] >= .55, I)
St = r["strobe"]
chk("C. the strobe's housing sits inside a mounting plate that shows round it (margin %.2f units, at least 1.5), with screws (%s)" % (St["plateMargin"], St["screws"]), St["plateMargin"] >= 1.5 and St["screws"] >= 2, St)
chk("C. ...a ribbed lens (%s ribs), a speaker grille of upright slots (%s) and no eyes and a flash that goes off (%s)" % (St["ribs"], St["slots"], St["flash"]), St["ribs"] >= 8 and St["slots"] >= 6 and St["flash"] and St["eyes"] == 0, St)
Sp = r["spr"]
chk("D. the sprinkler has no face (%s eye marks) and no gold (%s gold-hued colours); its bulb is red (%s) and it has a notched deflector (%s vertices)" % (Sp["eyes"], Sp["gold"], Sp["red"], Sp["rimVerts"]),
    Sp["eyes"] == 0 and Sp["gold"] == 0 and Sp["red"] and Sp["rimVerts"] >= 40, Sp)
chk("D. ...and every part is joined: the pipe (bottom %s) runs into the ceiling plate (%s), the inlet (top %s) hangs from it, the frame block (%s) sits on the inlet's collar, the arms (top %s) start under the block (bottom %s) and end in the boss (%s, top %s), the bulb (%s..%s) is seated in both, the boss overlaps the deflector (top %s), thread ridges %s, water streaks %s" % (
        Sp["pipe"] and Sp["pipe"]["bottom"], Sp["plate"] and Sp["plate"]["y"], Sp["inlet"] and Sp["inlet"]["y"], Sp["block"] and Sp["block"]["y"], Sp["arms"] and Sp["arms"]["y"], Sp["block"] and Sp["block"]["bottom"], Sp["arms"] and Sp["arms"]["bottom"], Sp["boss"] and Sp["boss"]["y"],
        Sp["bulb"] and Sp["bulb"]["y"], Sp["bulb"] and Sp["bulb"]["bottom"], Sp["rimBox"] and Sp["rimBox"]["y"], Sp["ridges"], Sp["streaks"]),
    all(Sp[k] for k in ("pipe", "plate", "inlet", "block", "arms", "boss", "bulb", "rimBox"))
    and Sp["pipe"]["bottom"] > Sp["plate"]["y"] and Sp["inlet"]["y"] < Sp["plate"]["bottom"] and Sp["inlet"]["bottom"] > Sp["block"]["y"] - 3
    and Sp["arms"]["y"] < Sp["block"]["bottom"] and Sp["arms"]["bottom"] > Sp["boss"]["y"] and Sp["bulb"]["y"] < Sp["block"]["bottom"] and Sp["bulb"]["bottom"] > Sp["boss"]["y"]
    and Sp["boss"]["bottom"] > Sp["rimBox"]["y"] and Sp["ridges"] >= 3 and Sp["streaks"] >= 9, Sp)
Sl = r["spill"]
chk("E. the ooze spans the drum's width (%.1f to %.1f, the drum is 7.8 to 32.2)" % (Sl["x0"], Sl["x1"]), Sl["x0"] <= 8.3 and Sl["x1"] >= 31.7, Sl)
chk("E. every drip (%s of them) starts up inside the ooze, at least 1.5 units over the rim (least: %.2f)" % (Sl["n"], Sl["minUp"]), Sl["n"] >= 4 and Sl["minUp"] >= 1.5, Sl)
F = r["flare"]
chk("F. Quasar's flare sits ON its ring (%.2f units from it, at most .6)" % F["umbra"]["ringDist"], F["umbra"]["ringDist"] <= .6, F["umbra"])
chk("F. Pulsar's flare is set on the rim of its star (%.2f off the rim, at most .5)" % F["singularity"]["off"], F["singularity"]["off"] <= .5, F["singularity"])
chk("F. Eclipse's flare is the bead on the rim of its black disc (%.2f off the rim, at most .5)" % F["genesis"]["off"], F["genesis"]["off"] <= .5, F["genesis"])
A_ = r["agent"]
chk("G. Undercover is a person in shades, not a hat or a smiley: no hat group, no eye marks (%s), a pair of mirrored lenses (%s), a barely curved mouth (%.2f units, a smile is 1.6+)" % (A_["eyes"], A_["lens"], A_["mouthCurve"]),
    not A_["person"] and A_["eyes"] == 0 and A_["lens"] and A_["mouthCurve"] <= .8, A_)
chk("G. ...with a coiled earpiece wire (%s) that ends under a turned-up collar of two flaps (%s, tops at y %.1f, above the neck line 27), a blinking light on the earpiece (%s) and a badge wallet's gold (%s)" % (A_["coil"], A_["collar"], A_["collarTop"], A_["earLed"], A_["wallet"]),
    A_["coil"] and A_["collar"] == 2 and A_["collarTop"] < 27 and A_["coil"]["bottom"] > A_["collarTop"] + 4 and A_["earLed"] and A_["wallet"], A_)
M = r["irons"]
chk("G. The Irons are two tools crossed over a shield, not a person and not a face: no hat, no eye marks (%s), two tool groups turned opposite ways (%s), the Maltese cross (%s) in a shield with a rim (%s), glints (%s)" % (M["eyes"], M["tools"], M["cross"], M["shield"], M["glints"]),
    not M["person"] and M["eyes"] == 0 and len(M["tools"]) == 2 and any("rotate(-" in t for t in M["tools"]) and any("rotate(3" in t for t in M["tools"]) and M["cross"] >= 1 and M["shield"] and M["glints"], M)
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
