#!/usr/bin/env python3
"""Build 384, round 11 (r6-chars): every Fire Code unlock character checked again, in Madison's world.

  "We are FIRE inspectors. Fire inspectors wear police gear. We mostly wear the vests but a lot of us are also police officers. If we
   aren't police officers we dress almost identical except we don't have a gun... Our police outfits are navy blue pants and short sleeved
   polo shirts." / "If there is going to be any hard hats ... they will be navy blue." / faces each their own, not cartoon-smiley on
   everything, nothing floating.

  Everything is read off the drawn SVG of each Fire Code character (drawAvatarCharSVG, the app's own drawing):
  A. NO COWBOY HATS. No character a Fire Code account can pick wears one (round 3's western look is gone).
  B. THE INSPECTOR is a fire inspector of his agency: a navy polo (its collar and placket), a dark tactical vest over it, the gold badge
     on the vest, a radio mic on the strap with its light, the navy duty ball cap with the gold cross; his glasses and clipboard kept; a
     closed mouth (no teeth).
  C. THE CHIEF: bareheaded, silver hair, a moustache, the same navy polo with gold collar piping, the chief's insignia on both collar
     points and the gold badge.
  D. EVERY HARD HAT, HELMET AND CAP IS NAVY (the Smoke Diver's helmet was yellow).
  E. THE PEOPLE IN UNIFORM WEAR NAVY: the Inspector, the Chief, the Dispatcher and the Drone Pilot's shirts are one navy.
  F. THE DRONE PILOT: goggles pushed up above eyes that show, a controller held at the chest with its screen, a closed mouth.
     (check-b384-ifcchars C measures the drone's clear air and that it is whole in the coin.)
  G. STAR RANGER: a space helmet, a star badge, clear eyes (white, no glow over them) - not the rulers' lit eyes.
  H. ONE GRIN IN THE CLASS: only Toxic Spill (a monster) shows teeth.
  I. PULSAR: the visor slit is drawn over the spin ring's near half (it no longer cuts a cross through it).
  J. STROBE: no bar drawn across the visor between its two lamps (it read as the bridge of a pair of glasses).
  K. DISPATCHER: the earcup's line light is a small lamp, not a glowing ball the size of an eye.

  ROUND 12 (r9-chars) retired A, B, C, F, G, H and I: Madison picked older versions of the Inspector, Chief, Drone Pilot and Star Ranger
  (cowboy hats and all) and replaced Pulsar. D, E (Inspector, Chief, Dispatcher), J and K still hold; check-b384-r9-chars has the rest.

  python3 tools/check-b384-r6-chars.py [--against OLD/index.html]      (every lettered group FAILS on ea31d43)
"""
import json, os, sys, colorsys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
from playwright.sync_api import sync_playwright
BODY = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read() if "--against" in sys.argv else None
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:600], flush=True)

seed = dict(rc["SEED"]); seed.update(seenClassTip=True, novaMet=99, publicId="tst4fc11chars6", classes=["academy", "ifc"])
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
  const stops = (s, f) => { f = f || ''; const m = f.match(/^url\(#([^)]+)\)/); if(!m) return f && f !== 'none' ? [f] : []; const g = s.querySelector('[id="' + m[1] + '"]'); return g ? [...g.querySelectorAll('stop')].map(x => x.getAttribute('stop-color')) : []; };
  const base = (s, el) => { const st = stops(s, el && el.getAttribute('fill')); return st.length >= 3 ? st[1] : st[0] || null; };
  const out = { cls: window.NOVA_CLASS, chars: {} };
  const ids = AVATAR_CHARACTERS.filter(c => !c.retired && !c.legacy).map(c => c.id);
  for(const id of ids){
    const s = mount(id), ser = new XMLSerializer().serializeToString(s);
    /* every hat group: cx-fx-hat (the fire helmet carries no kind class) or cx-fc-hat-<kind>; its shell is its first shape */
    const hats = [...s.querySelectorAll('.cx-fx-hat, [class*="cx-fc-hat-"]')].map(e => ({ kind: (e.getAttribute('class').match(/cx-fc-hat-([a-z]+)/) || [])[1] || 'helmet', fill: base(s, e.querySelector('path')) }));
    const body = s.querySelector('.cx-body > path');
    /* teeth: any near-white filled shape in the mouth group */
    const light = h => { const m = (h || '').match(/^#([0-9a-f]{6})$/i); if(!m) return false; const v = [0, 2, 4].map(i => parseInt(m[1].substr(i, 2), 16)); return Math.min(...v) > 200; };
    const mouthWhite = [...s.querySelectorAll('.cx-mouth [fill]')].some(e => light(e.getAttribute('fill')));
    const eyes = s.querySelector('.cx-eyes');
    out.chars[id] = { kind: (AVATAR_CHARACTERS.find(c => c.id === id) || {}).kind, hats, shirt: base(s, body), mouthWhite,
      eyeShapes: eyes ? eyes.querySelectorAll('path,circle,ellipse,rect').length : 0, eyeWhite: eyes ? [...eyes.querySelectorAll('ellipse')].filter(e => /^#fff(fff)?$/i.test(e.getAttribute('fill') || '')).length : 0,
      scopeglow: !!s.querySelector('.cx-fx-scopeglow'), ser: ser.length };
    if(id === 'detective'){
      const bp = [...s.querySelectorAll('.cx-body path')];
      out.insp = {
        vest: bp.filter(p => (p.getAttribute('d') || '').split('M').length === 3 && (() => { const b = base(s, p); if(!b) return false; const h = b.match(/[0-9a-f]{2}/gi).map(x => parseInt(x, 16)); return Math.max(...h) - Math.min(...h) < 40 && Math.max(...h) < 90; })()).length,
        collar: bp.filter(p => (p.getAttribute('d') || '').split('M').length === 3 && /^url/.test(p.getAttribute('fill') || '') && /^#[0-9a-f]{6}$/i.test(p.getAttribute('stroke') || '') && p.getBBox().y > 26 && p.getBBox().y < 29).length,
        badge: [...s.querySelectorAll('.cx-body path')].filter(p => p.getAttribute('stroke') === '#6E4A0C' && /^url/.test(p.getAttribute('fill') || '')).length,
        mic: !!s.querySelector('.cx-body .cx-fx-led') && !!s.querySelector('.cx-body rect[transform*="rotate"]'),
        glasses: !!s.querySelector('.cx-head path[stroke="#22242A"], .cx-head path[stroke="#2A2A30"]'), clipboard: (ser.match(/#2E9A5A/g) || []).length >= 2,
        capCross: !!s.querySelector('.cx-fc-hat-cap path[fill="#F2C14E"]') };
    }
    if(id === 'poseidon'){
      const hp = [...s.querySelectorAll('.cx-head path')];
      out.chief = {
        hair: hp.filter(p => { const st = stops(s, p.getAttribute('fill')); if(st.length < 3) return false; const v = st.map(c => c.match(/[0-9a-f]{2}/gi).map(x => parseInt(x, 16))); return v.every(c => Math.max(...c) - Math.min(...c) < 26) && Math.max(...v[1]) > 170 && p.getBBox().y < 12; }).length,
        moustache: hp.filter(p => { const b = p.getBBox(); const st = stops(s, p.getAttribute('fill')); return st.length >= 3 && b.y > 23.5 && b.y < 25.5 && b.width > 8 && b.width < 11; }).length,
        insignia: [...s.querySelectorAll('.cx-body path')].filter(p => p.getAttribute('stroke') === '#F2C14E' && /M.*L.*M.*L/.test(p.getAttribute('d') || '')).length,
        piping: [...s.querySelectorAll('.cx-body path')].filter(p => p.getAttribute('stroke') === '#F2C14E' && /^url/.test(p.getAttribute('fill') || '')).length,
        badge: [...s.querySelectorAll('.cx-body path')].filter(p => p.getAttribute('stroke') === '#6E4A0C' && /^url/.test(p.getAttribute('fill') || '')).length };
    }
    if(id === 'ronin'){
      const lens = [...s.querySelectorAll('.cx-head path')].filter(p => (stops(s, p.getAttribute('fill')).join(',').toUpperCase().indexOf('#3DE0C0') >= 0)).map(p => p.getBBox());
      const ey = [...s.querySelectorAll('.cx-eyes ellipse')].map(e => +e.getAttribute('cy'));
      out.drone = { lensBottom: lens.length ? Math.max(...lens.map(b => b.y + b.height)) : 99, eyeY: ey.length ? Math.min(...ey) : -1,
        screen: [...s.querySelectorAll('.cx-body rect')].some(r => /^#0[0-9a-f]2/i.test(r.getAttribute('fill') || '') && +r.getAttribute('width') > 5) };
    }
    if(id === 'zenith'){
      out.ranger = { starBadge: [...s.querySelectorAll('circle + path[stroke-linejoin="round"]')].length, eyesGlow: [...s.querySelectorAll('.cx-fx-scopeglow ellipse')].length };
    }
    if(id === 'singularity'){
      const head = s.querySelector('.cx-head'), kids = [...head.querySelectorAll('*')];
      const ring = [...head.querySelectorAll('g[transform*="rotate"].cx-fx-sqlight')][0], eyesG = head.querySelector('.cx-eyes');
      out.pulsar = { ringInHead: !!ring, ringBeforeSlit: !!(ring && eyesG && (ring.compareDocumentPosition(eyesG) & Node.DOCUMENT_POSITION_FOLLOWING)) };
    }
    if(id === 'clown'){
      out.strobe = { bar: [...s.querySelectorAll('.cx-head path')].filter(p => /^M1[45](\.\d+)? (19|20|21)(\.\d+)? L2[45](\.\d+)? (19|20|21)(\.\d+)?$/.test((p.getAttribute('d') || '').trim()) && p.getAttribute('stroke')).length };
    }
    if(id === 'hacker'){
      out.disp = { ball: [...s.querySelectorAll('circle')].filter(c => +c.getAttribute('cx') > 28 && +c.getAttribute('cy') > 18 && +c.getAttribute('cy') < 23 && +c.getAttribute('r') >= 1.5).length };
    }
    s.remove();
  }
  out.names = Object.fromEntries(ids.map(i => [i, AVATAR_DISPLAY_NAME[i] || i]));
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
    R = pg.evaluate(SNAP)
    ctx.close(); br.close()
srv.shutdown()

def hsl(h):
    if not h or not h.startswith("#") or len(h) != 7: return (0, 0, 0)
    r, g, b = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    hh, l, s = colorsys.rgb_to_hls(r, g, b); return (hh * 360, s, l)
def navy(h):
    H, Sa, L = hsl(h); return 205 <= H <= 245 and Sa >= .35 and L <= .38   # (the Dispatcher's is the lightest, #344C86, lifted off his navy sky in 384)

C = R["chars"]; N = R["names"]
chk("the page is the Fire Code class with no page error (%s)" % errs[:2], R["cls"] == "ifc" and not errs, errs)
# A, B, C, F, G, H, I are RETIRED by round 12 (r9-chars, Madison's picks from the version sheet): the Inspector is build 383's
# investigator in a cowboy hat, the Chief round 3's in his white hat, the Drone Pilot (goggles down, grinning) and the Star Ranger
# (night-sky hat) round 3's, and Pulsar is gone (Whiteout). tools/check-b384-r9-chars.py asserts what replaced them.
print("RETIRED A, B, C, F, G, H, I (round 12 brought back the cowboy hats, round 3's Drone Pilot and Star Ranger, and replaced Pulsar; see check-b384-r9-chars)")
# D
helm = [(N[i], h["kind"], h["fill"]) for i, c in C.items() for h in c["hats"] if h["kind"] in ("helmet", "hardhat", "cap")]
chk("D. every hard hat, helmet and cap is navy (%s)" % helm, helm and all(navy(f) for _, _, f in helm), helm)
chk("D. ...the Smoke Diver's helmet among them (%s)" % C["masked"]["hats"], any(h["kind"] == "helmet" and navy(h["fill"]) for h in C["masked"]["hats"]), C["masked"]["hats"])
# E
uni = {N[i]: C[i]["shirt"] for i in ("detective", "poseidon", "hacker")}   # (round 12: the Drone Pilot is round 3's again, in his own dark gear)
chk("E. the people in uniform wear navy shirts (%s)" % uni, all(navy(v) for v in uni.values()), {k: [round(x, 2) for x in hsl(v)] for k, v in uni.items()})
# J
chk("J. Strobe: no bar across the visor between the lamps (%s)" % R.get("strobe"), (R.get("strobe") or {}).get("bar", 1) == 0, R.get("strobe"))
# K
chk("K. Dispatcher: the earcup's light is a small lamp, no glowing ball there (%s)" % R.get("disp"), (R.get("disp") or {}).get("ball", 1) == 0, R.get("disp"))
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
