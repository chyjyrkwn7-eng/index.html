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

  A. valkyrie is Lookout, timekeeper is Smoke Alarm (round 8), genesis is Eclipse; Pyrotech, Salamander, Solstice, Undercover and Pump Operator are gone
  B. the Inspector's hat is a darker felt than it was; his clipboard has a hand on it, two ticks and a cross, and is mostly inside the coin
  C. Strobe is the appliance: a mounting plate that frames the housing, ribs down its lens, the horn grille's slots, FIRE in strokes
  D. Sprinkler Head (round 8): threaded inlet, a brass body that holds the face, a bulb between two arms joined to the body and the boss, a notched deflector under it
  E. Toxic Spill: the ooze spans the drum's width and every drip starts up inside the ooze, not on the rim
  F. each secret's flare sits ON its character: Quasar's on its ring, Pulsar's and Eclipse's on the rim of their head disc
  G. Undercover: a dark hat pulled low, glass over the eyes, a badge half hidden; Pump Operator: a hard hat, two gauges with working needles
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
    const slots = [...head.querySelectorAll('.cx-mouth path')].length;
    const mg = (red && plate) ? Math.min(red.b.x - plate.b.x, plate.b.x + plate.b.width - red.b.x - red.b.width, red.b.y - plate.b.y, plate.b.y + plate.b.height - red.b.y - red.b.height) : -1;
    out.strobe = { plateMargin: mg, ribs, slots, flash: !!s.querySelector('.cx-fx-fcflash'), screws: (ser.match(/<circle[^>]*r="0?\.62"/g) || []).length };
    s.remove(); }
  /* D: the sprinkler (round 8: the brass-bodied one - the face is on the body, the deflector is a plain notched plate under the bulb) */
  { const s = mount('hive'); const head = s.querySelector('.cx-head');
    const ellipses = [...head.querySelectorAll('ellipse')].map(e => ({ cx: +e.getAttribute('cx'), cy: +e.getAttribute('cy'), rx: +e.getAttribute('rx'), ry: +e.getAttribute('ry'), f: e.getAttribute('fill') || '' }));
    const rim = [...head.querySelectorAll('path')].map(p => ({ n: (p.getAttribute('d') || '').split('L').length, b: p.getBBox() })).sort((a, b) => b.n - a.n)[0];
    const eyes = [...s.querySelectorAll('.cx-eyes ellipse')].map(e => ({ cx: +e.getAttribute('cx'), cy: +e.getAttribute('cy') }));
    const bulb = ellipses.find(e => e.ry > 3 && Math.abs(e.cx - 20) < .5);
    const body = [...head.querySelectorAll('path')].map(p => ({ b: p.getBBox(), f: p.getAttribute('fill') || '' })).filter(o => o.b.width > 12 && o.b.width < 15.5 && o.b.height > 9 && o.b.height < 13 && o.b.y < 13)[0];
    const ridges = [...head.querySelectorAll('path')].filter(p => /^M16\.6 [\d.]+ L23\.4 [\d.]+$/.test(p.getAttribute('d') || '')).length;
    out.spr = { rimVerts: rim ? rim.n : 0, rimBox: rim && rim.b ? { x: rim.b.x, y: rim.b.y, w: rim.b.width, h: rim.b.height } : null, eyes, bulbY: bulb ? bulb.cy : null, bulbTop: bulb ? bulb.cy - bulb.ry : null, bulbBottom: bulb ? bulb.cy + bulb.ry : null, ridges,
      body: body ? { y: body.b.y, bottom: body.b.y + body.b.height, x: body.b.x, right: body.b.x + body.b.width } : null };
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
  /* G (round 8): the Lookout tower and the Smoke Alarm */
  { const s = mount('valkyrie'); const ser = new XMLSerializer().serializeToString(s);
    const eyes = [...s.querySelectorAll('.cx-eyes circle')].filter(c => Number(c.getAttribute('r')) > .9).map(c => ({ x: +c.getAttribute('cx'), y: +c.getAttribute('cy') }));
    const paths = [...s.querySelectorAll('.cx-head path')].map(p => ({ b: p.getBBox(), f: p.getAttribute('fill') || '' }));
    const roof = paths.filter(o => o.b.y < 9 && o.b.width > 15)[0], cabin = paths.filter(o => o.b.y > 12 && o.b.y < 13 && o.b.width > 12 && o.b.width < 15)[0];
    const deck = paths.filter(o => o.b.y > 20.5 && o.b.y < 21.5 && o.b.width > 17)[0], legs = paths.filter(o => o.b.y > 21 && o.b.y < 22 && o.b.height > 11);
    out.look = { person: /cx-fc-hat|cx-fc-hat-cowboy/.test(ser), eyes: eyes.length, roof: roof ? { b: roof.b.y + roof.b.height } : null, cabin: cabin ? { y: cabin.b.y, b: cabin.b.y + cabin.b.height } : null,
      deck: deck ? { y: deck.b.y, b: deck.b.y + deck.b.height } : null, legTop: legs.length ? Math.min(...legs.map(l => l.b.y)) : null, pole: /M19\.6 8\.2 L19\.6 2\.4/.test(ser), flag: !!s.querySelector('.cx-fx-fcflame'), clip: /clip-path/.test(ser) };
    s.remove(); }
  { const s = mount('timekeeper'); const ser = new XMLSerializer().serializeToString(s);
    const slots = [...s.querySelectorAll('.cx-body path')].filter(p => /^M[\d.]+ [\d.]+ L[\d.]+ [\d.]+$/.test(p.getAttribute('d') || '') && p.getAttribute('stroke') === '#4A4536').length;
    const cap = [...s.querySelectorAll('.cx-head circle')].map(c => +c.getAttribute('r')).filter(r => r > 6 && r < 7.5).length;
    out.smoke = { person: /cx-fc-hat/.test(ser), slots, cap, led: !!s.querySelector('.cx-fx-fcflash'), waves: !!s.querySelector('.cx-fx-fcwave'), eyes: s.querySelectorAll('.cx-eyes ellipse').length };
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
chk("A. valkyrie is Lookout, timekeeper Smoke Alarm, genesis Eclipse (%s, %s, %s)" % (N.get("valkyrie"), N.get("timekeeper"), N.get("genesis")),
    (N.get("valkyrie"), N.get("timekeeper"), N.get("genesis")) == ("Lookout", "Smoke Alarm", "Eclipse"), N)
chk("A. Pyrotech, Salamander, Solstice, Undercover and Pump Operator are gone from the class's list", not {"Pyrotech", "Salamander", "Solstice", "Undercover", "Pump Operator"} & set(N.values()), N)
I = r["insp"]
fb = lum(I["feltBase"]) if I.get("feltBase") else 1
chk("B. the Inspector's hat is a darker felt: base %s, luminance %.2f (it was .52; now under .40 and still not black, over .10)" % (I.get("feltBase"), fb), .10 < fb < .40, I)
chk("B. his clipboard: two ticks and a cross on the form, a hand on the board (%s ticks, %s crosses, hand %s)" % (I["ticks"], I["crosses"], I["hand"]), I["ticks"] >= 2 and I["crosses"] >= 1 and I["hand"], I)
chk("B. ...and the board is bigger (%.1f units tall, it was 7.4) with most of it inside the coin (%.2f)" % (I["boardH"], I["boardIn"]), I["boardH"] >= 8.5 and I["boardIn"] >= .55, I)
St = r["strobe"]
chk("C. the strobe's housing sits inside a mounting plate that shows round it (margin %.2f units, at least 1.5), with screws (%s)" % (St["plateMargin"], St["screws"]), St["plateMargin"] >= 1.5 and St["screws"] >= 2, St)
chk("C. ...a ribbed lens (%s ribs), a slotted horn grille for a mouth (%s strokes) and a flash that goes off (%s)" % (St["ribs"], St["slots"], St["flash"]), St["ribs"] >= 8 and St["slots"] >= 4 and St["flash"], St)
Sp = r["spr"]
chk("D. the sprinkler's face is on its brass body (%s), eyes inside it, and the deflector is a notched plate (%s vertices) with no eyes on it" % (Sp["body"], Sp["rimVerts"]),
    Sp["body"] and len(Sp["eyes"]) >= 2 and all(Sp["body"]["x"] < e["cx"] < Sp["body"]["right"] and Sp["body"]["y"] < e["cy"] < Sp["body"]["bottom"] for e in Sp["eyes"])
    and Sp["rimVerts"] >= 40 and Sp["rimBox"] and all(not (Sp["rimBox"]["y"] < e["cy"] < Sp["rimBox"]["y"] + Sp["rimBox"]["h"]) for e in Sp["eyes"]), Sp)
chk("D. ...the red bulb is joined at both ends (top %s under the body's foot %s, bottom %s into the deflector's boss, above the plate %s) and the inlet has thread ridges (%s)" % (Sp["bulbTop"], Sp["body"] and Sp["body"]["bottom"], Sp["bulbBottom"], Sp["rimBox"] and Sp["rimBox"]["y"], Sp["ridges"]),
    Sp["bulbTop"] is not None and Sp["body"] and Sp["bulbTop"] < Sp["body"]["bottom"] and Sp["rimBox"] and Sp["bulbBottom"] > Sp["rimBox"]["y"] - 4 and Sp["bulbBottom"] <= Sp["rimBox"]["y"] + 1.5 and Sp["ridges"] >= 3, Sp)
Sl = r["spill"]
chk("E. the ooze spans the drum's width (%.1f to %.1f, the drum is 7.8 to 32.2)" % (Sl["x0"], Sl["x1"]), Sl["x0"] <= 8.3 and Sl["x1"] >= 31.7, Sl)
chk("E. every drip (%s of them) starts up inside the ooze, at least 1.5 units over the rim (least: %.2f)" % (Sl["n"], Sl["minUp"]), Sl["n"] >= 4 and Sl["minUp"] >= 1.5, Sl)
F = r["flare"]
chk("F. Quasar's flare sits ON its ring (%.2f units from it, at most .6)" % F["umbra"]["ringDist"], F["umbra"]["ringDist"] <= .6, F["umbra"])
chk("F. Pulsar's flare is set on the rim of its star (%.2f off the rim, at most .5)" % F["singularity"]["off"], F["singularity"]["off"] <= .5, F["singularity"])
chk("F. Eclipse's flare is the bead on the rim of its black disc (%.2f off the rim, at most .5)" % F["genesis"]["off"], F["genesis"]["off"] <= .5, F["genesis"])
L = r["look"]
chk("G. the Lookout is a tower, not a person in a hat: no hat group, two window eyes (%s), a pole into the roof and a pennant that flutters (%s, %s)" % (L["eyes"], L["pole"], L["flag"]),
    not L["person"] and L["eyes"] >= 2 and L["pole"] and L["flag"], L)
chk("G. ...and every part stands on the next: the roof (bottom %s) over the cabin (top %s), the cabin (bottom %s) on the catwalk (%s..%s), the legs (top %s) up under the catwalk" % (L["roof"] and L["roof"]["b"], L["cabin"] and L["cabin"]["y"], L["cabin"] and L["cabin"]["b"], L["deck"] and L["deck"]["y"], L["deck"] and L["deck"]["b"], L["legTop"]),
    L["roof"] and L["cabin"] and L["deck"] and L["legTop"] is not None and L["roof"]["b"] > L["cabin"]["y"] + .2 and L["cabin"]["b"] > L["deck"]["y"] + .3 and L["legTop"] < L["deck"]["b"] - .3, L)
M = r["smoke"]
chk("G. the Smoke Alarm is a round alarm, not a person: no hat, a ring of %s vent slots, a face on a centre cap (%s), a blinking red lamp (%s), the sound arcs (%s)" % (M["slots"], M["cap"], M["led"], M["waves"]),
    not M["person"] and M["slots"] >= 16 and M["cap"] >= 1 and M["led"] and M["waves"] and M["eyes"] >= 2, M)
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
