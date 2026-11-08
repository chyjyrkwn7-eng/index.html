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
  C. Strobe (round 10: the older red alarm back, with its face): FIRE across the top, a visor with two white eyes in it, a speaker grille down each side of the visor, a horn slot for a mouth, the flash and the horn's waves
  D. Sprinkler Head (round 10: the older white robot back): a chrome head with a dark visor and two blue eyes, a smile of light, two arms to a notched deflector crown, the red bulb seated in the crown and on the head
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
  /* C: the strobe (round 10: the older red alarm with its visor and eyes) */
  { const s = mount('clown'); const head = s.querySelector('.cx-head'); const ser = new XMLSerializer().serializeToString(s);
    const eyes = [...s.querySelectorAll('.cx-eyes > rect')].filter(r => +r.getAttribute('height') < 2 && +r.getAttribute('width') > 2 && +r.getAttribute('width') < 3);
    const fillOf = e => e.getAttribute('fill') || '';
    const visor = [...head.querySelectorAll('path')].map(p => ({ b: p.getBBox(), f: p.getAttribute('fill') || '' })).filter(o => o.b.width > 12 && o.b.width < 15 && o.b.y > 16 && o.b.y < 17.5)[0];
    const grille = [...head.querySelectorAll('rect')].filter(r => +r.getAttribute('height') === .7 && +r.getAttribute('width') === 1.4).length;
    const fireStrokes = [...head.querySelectorAll('path')].filter(p => /^M16\.9 11\.8 v1\.2/.test(p.getAttribute('d') || '')).length;
    out.strobe = { eyes: eyes.length, eyeFills: eyes.map(fillOf), eyeX: eyes.map(r => +r.getAttribute('x') + +r.getAttribute('width') / 2), visor: visor ? { x: visor.b.x, r: visor.b.x + visor.b.width, y: visor.b.y, b: visor.b.y + visor.b.height } : null,
      grille, fire: fireStrokes, mouth: s.querySelectorAll('.cx-mouth > *').length, flash: !!s.querySelector('.cx-fx-fcflash'), waves: s.querySelectorAll('.cx-fx-fcwave').length, plate: /M11\.2 6\.2 L28\.8 6\.2/.test(ser) };
    s.remove(); }
  /* D: the sprinkler (round 10: the white robot with the sprinkler on its head) */
  { const s = mount('hive'); const head = s.querySelector('.cx-head'); const ser = new XMLSerializer().serializeToString(s);
    const P = [...head.querySelectorAll('path')].map(p => ({ d: p.getAttribute('d') || '', b: p.getBBox(), f: p.getAttribute('fill') || '' }));
    const eyes = [...new Set([...s.querySelectorAll('.cx-eyes > ellipse')].map(e => +e.getAttribute('cx')))].map(cx => ({ cx, cy: +s.querySelector('.cx-eyes > ellipse[cx="' + cx + '"]').getAttribute('cy') }));
    const helm = P.find(o => o.d.indexOf('M11.6 20 Q11.4 12.8') === 0), visor = P.find(o => o.d.indexOf('M12.8 18.6') === 0), crown = [...P].sort((a, b) => b.d.split('L').length - a.d.split('L').length)[0];
    const bulb = [...head.querySelectorAll('ellipse')].map(e => ({ cx: +e.getAttribute('cx'), cy: +e.getAttribute('cy'), rx: +e.getAttribute('rx'), ry: +e.getAttribute('ry') })).find(e => e.ry > 3 && Math.abs(e.cx - 20) < .5);
    const arms = P.find(o => o.d.indexOf('M12.2 18 Q10.2 11') === 0);
    const B = o => o ? { x: o.b.x, r: o.b.x + o.b.width, y: o.b.y, b: o.b.y + o.b.height } : null;
    out.spr = { eyes, helm: B(helm), visor: B(visor), crown: B(crown), crownVerts: crown ? crown.d.split('L').length : 0, arms: B(arms), bulb: bulb ? { top: bulb.cy - bulb.ry, bottom: bulb.cy + bulb.ry } : null, smile: P.some(o => o.d.indexOf('M17.6 26.8 Q20 27.8') === 0), mouth: s.querySelectorAll('.cx-mouth').length,
      gold: /#(?:FFD3|F5C|E8A2|D4A)/i.test(ser) };
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
chk("C. the strobe has a face again: two white lamp eyes (%s, fills %s) set either side of the middle inside a visor (%s), a mouth slot (%s marks)" % (St["eyes"], St["eyeFills"], St["visor"], St["mouth"]),
    St["eyes"] == 2 and all(f == "#FFFFFF" for f in St["eyeFills"]) and St["visor"] and St["visor"]["x"] < min(St["eyeX"]) and max(St["eyeX"]) < St["visor"]["r"] and abs(sum(St["eyeX"]) / 2 - 20) < .2 and St["mouth"] >= 3, St)
chk("C. ...a speaker grille of %s slots down the two sides of the visor, FIRE across the top (%s), the flash (%s) and the horn's two waves (%s), and the old round 7 mounting plate is gone (%s)" % (St["grille"], St["fire"], St["flash"], St["waves"], St["plate"]),
    St["grille"] == 8 and St["fire"] >= 1 and St["flash"] and St["waves"] == 2 and not St["plate"], St)
Sp = r["spr"]
chk("D. the sprinkler is the white robot again: two blue eyes in a dark visor on the helm (%s) and a smile of light (%s)" % (Sp["eyes"], Sp["smile"]),
    len(Sp["eyes"]) == 2 and Sp["visor"] and Sp["helm"] and all(Sp["visor"]["x"] < e["cx"] < Sp["visor"]["r"] and Sp["visor"]["y"] < e["cy"] < Sp["visor"]["b"] for e in Sp["eyes"]) and Sp["smile"], Sp)
chk("D. ...two arms from the helm's sides up to the notched crown (%s vertices, arms top %s, crown bottom %s), the red bulb seated in the crown (bottom of the bulb %s over the crown's top %s) and standing on the helm (bulb foot %s under the helm's top %s), no gold" % (
        Sp["crownVerts"], Sp["arms"] and Sp["arms"]["y"], Sp["crown"] and Sp["crown"]["b"], Sp["bulb"] and Sp["bulb"]["top"], Sp["crown"] and Sp["crown"]["y"], Sp["bulb"] and Sp["bulb"]["bottom"], Sp["helm"] and Sp["helm"]["y"]),
    Sp["crown"] and Sp["arms"] and Sp["bulb"] and Sp["helm"] and Sp["crownVerts"] >= 10 and Sp["arms"]["y"] < Sp["crown"]["b"] and Sp["bulb"]["top"] < Sp["crown"]["b"] and Sp["bulb"]["bottom"] > Sp["helm"]["y"] - 1.5 and Sp["bulb"]["bottom"] <= Sp["helm"]["y"] + 1.5, Sp)
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
