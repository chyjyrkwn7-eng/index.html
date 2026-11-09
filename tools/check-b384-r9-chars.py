#!/usr/bin/env python3
"""Build 384, round 12 (r9-chars): Madison picked a version of every Fire Code challenge character from the version-history sheet
(A = 42bbffa, B = 478a689, C = d096932, D = 7b65a06, E = ea31d43, F = cd82880, the branch's start).

  Kept as F: Ghost, Bear, Alien, Strobe, Hazmat, Toxic Spill, Dispatcher, Sprinkler Head (and every rank character, and the whole academy).
  Inspector  - "the investigator from toxic spill build A ... but with glasses", "D give him some facial hair ... a shaved down beard";
               "Our button ups are navy": A's figure (dark brown felt cowboy hat, brown skin, button-up) in navy, D's glasses and clipboard,
               a short stubble, not a full beard.
  Smoke Diver - F, "don't make the helmet logo a FD logo, make it a badge".
  Chief      - E (white cowboy hat, grey moustache, bolo), in a navy button-up.
  Undercover - "redo, try that one again": a plainclothes officer (leather jacket, badge on a chain, aviators, earpiece, crew cut).
  The Irons  - "I hate this one, think of an entire new character" / "We are doing weapons as characters?": the Fire Marshal, a person.
  Drone Pilot, Star Ranger - E.   Nebula - C.   Quasar (umbra) - B (build 383's hooded recon figure; the name stays Quasar).
  Pulsar     - "do whiteout but try it again. A blizzard type character": the Whiteout.
  Eclipse    - "I don't like eclipse at all. Try something else": the Firebird.

  Everything is read off the app's own drawing (drawAvatarCharSVG), in both classes:
  A. THE ACADEMY IS UNTOUCHED: every academy character byte for byte cd82880's.
  B. IN FIRE CODE THE KEPT ONES ARE UNTOUCHED: the starters, the eight kept challenge characters and the seven rank characters byte for byte
     cd82880's; and every one of the eleven picked characters DIFFERS from cd82880's (F).
  C. THE RESTORED ONES ARE THEIR VERSIONS: the Drone Pilot and the Star Ranger byte for byte ea31d43's (E); Quasar is 478a689's recon drawing (B)
     with only its flare marked to stay lit in the secret-flare scene; Nebula keeps F's body and cloud and wears d096932's face (C).
  D. THE INSPECTOR: the banners' blue plate carrier over his shirt ("Our vests are blue and not black"), a dark brown felt cowboy hat, brown skin, a navy short-sleeved shirt, glasses, the clipboard, the star badge, and a heavy stubble
     (jaw, chin and lip; not a solid beard) with no teeth - in the banners' inspector colours (FB_KIT, r9-banners).
  E. THE SMOKE DIVER'S HELMET carries a badge with a star, and no Maltese cross (the fire department's mark) anywhere on it; still navy.
  F. THE CHIEF (round 13: "I preferred the chief with the brown coat"): E's drawing byte for byte - the brown sport coat over the white shirt,
     the white cowboy hat, the grey moustache, the bolo's turquoise, the star.
  M. (round 14) THE DISPATCHER is a woman: a crown of curls, gold hoops, the headset, the console's light, the navy polo.
     Round 14 also shipped Plainclothes as Undercover (G) and Aurora as the genesis secret (I), and replaced the timekeeper's options (L).
  H / I / L (round 16, r13-chars: "Do exit and comet. Make them look good."): the timekeeper is the Exit and genesis the Comet, both finished;
     the options are closed - no IFC_CHAR_OPTIONS / IFC_CHAR_PICK, and no turned-down or unpicked drawing left in IFC_CHAR_DRAW. (The round
     13-15 wording below is history.)
  L. (round 15) THE OPTIONS: four each for the timekeeper and genesis ids, none shipped, all drawn whole, all different, the secret's carrying
     the core flare, and the drawings he turned down out of the file. (Round 13's wording below is history.)
  L. (round 13) THE OPTIONS: three finished concepts each for the timekeeper, genesis and valkyrie ids sit in IFC_CHAR_OPTIONS, none shipped
     (IFC_CHAR_PICK all 0, so the shipped three are unchanged - B); each of the nine draws whole (head, eyes, closed eyes, mouth, special
     parts, no svg filter), each differs from the others and from the shipped drawing, and the secret one's options carry the core flare.
  G. UNDERCOVER: no hat, aviators (gold frame, dark mirrored lenses), the eye group empty (the glasses are the eyes), a badge on a chain, an
     earpiece, hair, a nearly flat mouth.
  H. THE FIRE MARSHAL: a person (a face with two eyes and a mouth, hair), the agency's BLUE vest (clearly blue, lighter than the navy shirt
     under it - "Our vests are blue and not black"), the star badge, a flashlight with its beam; no tool crossed over a shield, no hat.
  I. THE WHITEOUT: a parka hood with a fur ruff, goggles with two lit eyes behind them, no mouth, the white flare, the blizzard (wind and snow
     groups); THE FIREBIRD: wings, two round eyes with pupils, a beak in the mouth group, the core flare at its breast.
  J. EVERY SECRET'S FLARE IS ON ITS CHARACTER (inside the figure's own drawn shapes), and every changed drawing has a head, eyes, closed eyes,
     a mouth group, special parts and no svg filter.
  K. THE NAMES: Inspector, Smoke Diver, Chief, Undercover, Fire Marshal, Drone Pilot, Nebula, Quasar, Whiteout, Aurora, Star Ranger, Dispatcher.

  python3 tools/check-b384-r9-chars.py [--against OLD/index.html]      (B's differs, C to K FAIL on cd82880)
  python3 tools/check-b384-r9-chars.py --write-prev                     (re-reads cd82880 / ea31d43 / 478a689 from git into the .prev.json)
"""
import json, os, sys, subprocess, colorsys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
from playwright.sync_api import sync_playwright
BODY = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read() if "--against" in sys.argv else None
PREV_PATH = os.path.join(HERE, "check-b384-r9-chars.prev.json")
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:600], flush=True)

seed = dict(rc["SEED"]); seed.update(seenClassTip=True, novaMet=99, publicId="tst4fc12chars9", classes=["academy", "ifc"])
S = json.dumps(json.dumps(seed))
INIT_IFC = ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
            "localStorage.setItem('class26e.drill.v1',%s);localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));"
            "localStorage.setItem('class26e.greet.ifc','done');['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted','class26e.a2hs'].forEach(k=>localStorage.setItem(k,'1'));"
            "localStorage.setItem('class26e.ifc.drill.v1',%s);}catch(e){}") % (S, S)
INIT_ACA = ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
            "localStorage.setItem('class26e.drill.v1',%s);}catch(e){}") % S

KEPT = ["ghost", "grizzly", "alien", "clown", "marksman", "astronaut", "hive", "hacker"]   # (round 14b: the Dispatcher is the man again - "Nvm don't make dispatch a women"; M)
RANKS = ["forge", "lunar", "solar", "tempest", "frost", "oracle", "inferno"]
PICKED = ["detective", "masked", "poseidon", "valkyrie", "timekeeper", "ronin", "voidwalker", "umbra", "singularity", "genesis", "zenith", "hacker"]
NAMES = {"detective": "Inspector", "masked": "Smoke Diver", "poseidon": "Chief", "valkyrie": "Undercover", "timekeeper": "Exit", "ronin": "Drone Pilot",
         "voidwalker": "Nebula", "umbra": "Quasar", "singularity": "Whiteout", "genesis": "Comet", "zenith": "Star Ranger", "hacker": "Dispatcher"}

SNAP = r"""(detail) => {
  document.getElementById('splashscreen')?.remove();
  const host = document.createElement('div'); host.style.cssText = 'position:fixed;left:0;top:0;width:340px;height:340px;opacity:0;pointer-events:none';
  document.body.appendChild(host);
  const hash = s => { let h = 2166136261; for(let i = 0; i < s.length; i++){ h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0).toString(16); };
  const mount = id => { const s = drawAvatarCharSVG(id); s.setAttribute('width', 340); s.setAttribute('height', 340); host.appendChild(s); return s; };
  const ser = s => new XMLSerializer().serializeToString(s).split(s.getAttribute('data-cx-uid')).join('U');
  const stops = (s, f) => { f = f || ''; const m = f.match(/^url\(#([^)]+)\)/); if(!m) return f && f !== 'none' ? [f] : []; const g = s.querySelector('[id="' + m[1] + '"]'); return g ? [...g.querySelectorAll('stop')].map(x => x.getAttribute('stop-color')) : []; };
  const base = (s, el) => { const st = stops(s, el && el.getAttribute('fill')); return st.length >= 3 ? st[1] : st[0] || null; };
  const box = e => { const b = e.getBBox(); return [b.x, b.y, b.x + b.width, b.y + b.height]; };
  const out = { cls: window.NOVA_CLASS || 'academy', hash: {}, names: {}, d: {} };
  AVATAR_CHARACTERS.filter(c => !c.retired && !c.legacy).forEach(c => {
    const s = mount(c.id), x = ser(s);
    out.hash[c.id] = hash(x);
    out.names[c.id] = AVATAR_DISPLAY_NAME[c.id] || c.id;
    if(detail && detail.indexOf(c.id) >= 0){
      const q = sel => [...s.querySelectorAll(sel)];
      const hats = q('[class*="cx-fc-hat-"], .cx-fx-hat').map(e => ({ kind: (e.getAttribute('class').match(/cx-fc-hat-([a-z]+)/) || [])[1] || 'helmet', fill: base(s, e.querySelector('path')),
        stops: stops(s, (e.querySelector('path') || { getAttribute: () => '' }).getAttribute('fill')) }));
      const eyes = s.querySelector('.cx-eyes'), mouth = s.querySelector('.cx-mouth'), head = s.querySelector('.cx-head');
      const fig = s.querySelector('.cx-fig');
      const flareG = s.querySelector('.cx-fx-flare');
      let flare = null;
      if(flareG){ const c = flareG.querySelector('circle[stroke]') || flareG.querySelector('circle'); const b = c.getBBox(); flare = [b.x + b.width / 2, b.y + b.height / 2]; }
      /* what the flare sits on: drawn figure shapes (head and body, not the flare or the special) that contain its centre */
      let onFig = 0;
      if(flare){ const pt = s.createSVGPoint(); pt.x = flare[0]; pt.y = flare[1];
        q('.cx-head path, .cx-head ellipse, .cx-head circle, .cx-body path, .cx-body ellipse, .cx-fx-wings path').forEach(e => {
          if(e.closest('.cx-fx-flare') || e.closest('.cx-sp') || e.closest('.cx-eyes') || e.closest('.cx-eyes-closed')) return;
          try{ if(e.isPointInFill && e.isPointInFill(pt)) onFig++; }catch(err){} }); }
      out.d[c.id] = { kind: c.kind, hats, ser: x.length,
        eyes: eyes ? eyes.querySelectorAll('path,circle,ellipse,rect').length : -1,
        eyeWhites: eyes ? q('.cx-eyes ellipse').filter(e => /^#fff(fff)?$/i.test(e.getAttribute('fill') || '')).length : 0,
        eyeCircles: eyes ? q('.cx-eyes circle').map(e => [+e.getAttribute('cx'), +e.getAttribute('r'), e.getAttribute('fill')]) : [],
        eyesLit: !!s.querySelector('.cx-eyes .cx-fx-sqlight'),
        closed: !!s.querySelector('.cx-eyes-closed'), mouth: mouth ? mouth.querySelectorAll('path,circle,ellipse,rect').length : -1,
        mouthWhite: mouth ? [...mouth.querySelectorAll('[fill]')].some(e => /^#(f[0-9a-f]){3}$/i.test(e.getAttribute('fill') || '') || /^#fff(fff)?$/i.test(e.getAttribute('fill') || '')) : false,
        mouthFills: mouth ? [...mouth.querySelectorAll('[fill]')].map(e => e.getAttribute('fill')) : [],
        heads: q('.cx-head').length, sp: q('.cx-sp').length, filter: /<filter|filter=/.test(x),
        shirt: base(s, s.querySelector('.cx-body > path')),
        flare, onFig, fills: [...new Set(q('[fill]').map(e => (e.getAttribute('fill') || '').toUpperCase()))], strokes: [...new Set(q('[stroke]').map(e => (e.getAttribute('stroke') || '').toUpperCase()))],
        gstops: [...new Set(q('stop').map(e => (e.getAttribute('stop-color') || '').toUpperCase()))],
        groups: [...new Set(q('g[class]').map(e => e.getAttribute('class')))],
        /* paths in the head drawn at a low opacity in a near-black brown: the stubble */
        stubble: q('.cx-head > path, .cx-head path').filter(e => (e.getAttribute('fill') || '').toUpperCase() === '#22140C').map(e => ({ op: +(e.getAttribute('opacity') || 1), box: box(e) })),
        dashed: q('.cx-body path[stroke-dasharray]').length,
        hatPaths: hats.length ? q('[class*="cx-fc-hat-"] path, .cx-fx-hat path').map(e => ({ fill: (e.getAttribute('fill') || '').toUpperCase(), stroke: (e.getAttribute('stroke') || '').toUpperCase(), n: (e.getAttribute('d') || '').split(/[LQ]/).length })) : [],
        /* the vest: two-panel body shapes (two subpaths) filled with a gradient */
        panels: q('.cx-body path').filter(e => (e.getAttribute('d') || '').split('M').length === 3 && /^url/.test(e.getAttribute('fill') || '')).map(e => base(s, e)),
        rotGroups: q('g[transform*="rotate"]').length,
        screws: q('.cx-head circle').filter(e => (e.getAttribute('fill') || '').toUpperCase() === '#8A929E' && +e.getAttribute('r') < .5).length,
        facets: q('.cx-head path').filter(e => (e.getAttribute('stroke') || '').toUpperCase() === '#E8F8FF' && (e.getAttribute('d') || '').split('L').length >= 4).length,
        curls: q('.cx-head > circle, .cx-head circle').filter(e => +e.getAttribute('r') >= 1.8 && +e.getAttribute('r') <= 2.6 && /^url/.test(e.getAttribute('fill') || '')).length,
        /* the blue plate carrier: a body shape filled with the banners' vest gradient (#2D5DAA at its middle stop), edged #10285A */
        plate: q('.cx-body path').filter(e => (base(s, e) || '').toUpperCase() === '#2D5DAA' && (e.getAttribute('stroke') || '').toUpperCase() === '#10285A').map(e => box(e)) };
    }
    s.remove();
  });
  return out; }"""


OPTS_SNAP = r"""() => {
  if(typeof IFC_CHAR_OPTIONS === 'undefined') return null;
  const hash = s => { let h = 2166136261; for(let i = 0; i < s.length; i++){ h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0).toString(16); };
  const out = { pick: Object.assign({}, IFC_CHAR_PICK), o: {}, kinds: Object.keys(IFC_CHAR_DRAW) };
  Object.keys(IFC_CHAR_OPTIONS).forEach(id => {
    const def = AVATAR_CHARACTERS.find(c => c.id === id); if(!def) return;
    const k0 = def.kind, ser = s => new XMLSerializer().serializeToString(s).split(s.getAttribute('data-cx-uid')).join('U');
    const shipped = hash(ser(drawAvatarCharSVG(id)));
    out.o[id] = IFC_CHAR_OPTIONS[id].map(([kind, name]) => { def.kind = kind; const s = drawAvatarCharSVG(id), x = ser(s);
      const r = { kind, name, h: hash(x), shipped, heads: s.querySelectorAll('.cx-head').length, eyes: !!s.querySelector('.cx-eyes'), closed: !!s.querySelector('.cx-eyes-closed'),
        mouth: !!s.querySelector('.cx-mouth'), sp: s.querySelectorAll('.cx-sp').length, filter: /<filter|filter=/.test(x), flare: !!s.querySelector('.cx-fx-flare'), scene: !!s.querySelector('.cx-bg') };
      def.kind = k0; return r; });
  });
  return out; }"""

def snap(init, body, detail):
    srv, port = rc["serve"]()
    errs = []
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=rc["CHROME"])
        ctx = br.new_context(viewport={"width": 440, "height": 956}, device_scale_factor=1)
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
        if body is not None:
            pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=body))
        pg.add_init_script(init)
        pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(3500)
        r = pg.evaluate(SNAP, detail)
        r["opts"] = pg.evaluate(OPTS_SNAP)
        r["kinds"] = pg.evaluate("() => typeof IFC_CHAR_DRAW === 'object' ? Object.keys(IFC_CHAR_DRAW) : []")
        ctx.close(); br.close()
    srv.shutdown()
    r["errs"] = errs
    return r


if "--write-prev" in sys.argv:
    git = lambda sha: subprocess.run(["git", "show", sha + ":index.html"], cwd=os.path.dirname(HERE), capture_output=True, text=True, check=True).stdout
    F = git("cd82880"); E = git("ea31d43"); B = git("478a689")
    prev = {"F": {"ifc": snap(INIT_IFC, F, [])["hash"], "academy": snap(INIT_ACA, F, [])["hash"]},
            "E": snap(INIT_IFC, E, [])["hash"], "B": snap(INIT_IFC, B, [])["hash"]}
    json.dump(prev, open(PREV_PATH, "w"), indent=0, sort_keys=True)
    print("wrote", PREV_PATH); sys.exit(0)

PREV = json.load(open(PREV_PATH))
IFC = snap(INIT_IFC, BODY, PICKED)
ACA = snap(INIT_ACA, BODY, [])
chk("the pages are the Fire Code class and the academy, with no page error (%s)" % (IFC["errs"] + ACA["errs"])[:2],
    IFC["cls"] == "ifc" and ACA["cls"] == "academy" and not IFC["errs"] and not ACA["errs"], IFC["errs"] + ACA["errs"])
H, D, N = IFC["hash"], IFC["d"], IFC["names"]

# A
moved = sorted(i for i, h in PREV["F"]["academy"].items() if ACA["hash"].get(i) != h)
chk("A. the academy's %d characters are byte for byte cd82880's (moved: %s)" % (len(PREV["F"]["academy"]), moved or "none"), not moved and len(PREV["F"]["academy"]) >= 25, moved)
# B
moved = [i for i in KEPT + RANKS if H.get(i) != PREV["F"]["ifc"].get(i)]
chk("B. Fire Code's starters, eight kept challenge characters and seven rank characters are byte for byte cd82880's (moved: %s)" % (moved or "none"), not moved, moved)
same = [i for i in PICKED if i not in KEPT and H.get(i) == PREV["F"]["ifc"].get(i)]   # (14b) the Dispatcher is in both: kept (byte for byte) and still read (M)
chk("B. ...and each of the eleven he picked a version for differs from cd82880's (unchanged: %s)" % (same or "none"), not same, same)
# C
chk("C. the Drone Pilot and the Star Ranger are ea31d43's drawings byte for byte (round 3's: %s, %s)" % (H["ronin"] == PREV["E"].get("ronin"), H["zenith"] == PREV["E"].get("zenith")),
    H["ronin"] == PREV["E"].get("ronin") and H["zenith"] == PREV["E"].get("zenith"), {"ronin": (H["ronin"], PREV["E"].get("ronin")), "zenith": (H["zenith"], PREV["E"].get("zenith"))})
du = D["umbra"]
chk("C. Quasar is build 383's recon drawing (kind %s), its flare marked to stay lit in the secret-flare scene (%s)" % (du["kind"], [g for g in du["groups"] if "flare" in g]),
    du["kind"] == "fcrecon" and "cx-fx cx-fx-flare cx-fx-sqlight" in du["groups"] and "#8B5CF6" in du["strokes"] and "#D8CCFF" in du["fills"], du["groups"])
dn = D["voidwalker"]
lit = [c for c in dn["eyeCircles"]]
chk("C. Nebula wears round 5's face: two lit eyes, orange and gold (%s), and a small mouth (%s shapes) - not round 10's embers" % (sorted({c[2] for c in lit}), dn["mouth"]),
    dn["kind"] == "fcnebula" and {"#F97316", "#FACC15"} <= {c[2] for c in lit} and dn["mouth"] == 1 and "#FF4A1C" not in dn["fills"], dn["eyeCircles"])

def hsl(h):
    if not h or not h.startswith("#") or len(h) != 7: return (0, 0, 0)
    r, g, b = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    hh, l, s = colorsys.rgb_to_hls(r, g, b); return (hh * 360, s, l)
def navy(h): H_, Sa, L = hsl(h); return 205 <= H_ <= 245 and Sa >= .35 and L <= .38

# D
d = D["detective"]
cow = [h for h in d["hats"] if h["kind"] == "cowboy"]
felt = hsl(cow[0]["fill"]) if cow else (0, 0, 1)
chk("D. the Inspector wears a dark brown felt cowboy hat (%s, hue %.0f, lightness %.2f; the banners' #4A382A)" % (cow and cow[0]["fill"], felt[0], felt[2]), len(cow) == 1 and 15 <= felt[0] <= 45 and felt[2] < .25 and cow[0]["fill"].upper() == "#4A382A", d["hats"])
# the banners' inspector kit (FB_KIT, r9-banners): skin #A86C48, navy button-up #1E2C4E, glasses #0B0E14, stubble #22140C, felt #4A382A
chk("D. ...the banners' inspector: skin #A86C48 (%s), the navy button-up #1E2C4E (%s), the rectangular glasses #0B0E14 (%s), the clipboard's ticks (%s) and the star badge (%s)" % ("#A86C48" in d["gstops"], d["shirt"], "#0B0E14" in d["strokes"], "#2E9A5A" in d["strokes"], "#6E4A0C" in d["strokes"]),
    "#A86C48" in d["gstops"] and (d["shirt"] or "").upper() == "#1E2C4E" and navy(d["shirt"]) and "#0B0E14" in d["strokes"] and "#2E9A5A" in d["strokes"] and "#6E4A0C" in d["strokes"], d)
pl = d["plate"]
chk("D. ...the banners' BLUE plate carrier over the shirt (%d plate, %s; vest #2D5DAA edged #10285A, its straps and cummerbund #21488A, webbing #1B3F7C), lighter than the navy shirt" % (len(pl), [[round(v, 1) for v in b] for b in pl]),
    len(pl) == 1 and pl[0][2] - pl[0][0] > 10 and pl[0][1] < 32 and "#21488A" in d["fills"] and "#1B3F7C" in d["strokes"] and hsl("#2D5DAA")[2] > hsl(d["shirt"])[2] and hsl("#2D5DAA")[1] > .45, d["plate"])
st = d["stubble"]
chk("D. ...a shaved-down beard: a heavy stubble on the jaw, chin and lip (%d shapes, opacity %s; at most .35, not a solid beard) and no teeth" % (len(st), [x["op"] for x in st]),
    len(st) >= 2 and all(0 < x["op"] <= .35 for x in st) and max(x["box"][3] for x in st) > 29.5 and not d["mouthWhite"], st)
# E
m = D["masked"]
cross = [p for p in m["hatPaths"] if p["fill"] == "#FFE9A8"]
badge = [p for p in m["hatPaths"] if p["stroke"] == "#6E4A0C"]
star = [p for p in m["hatPaths"] if p["fill"] == "#FFE7A0" and p["n"] >= 10]
chk("E. the Smoke Diver's helmet carries a badge (%d) with a star (%d), and no Maltese cross (%d); the shell is still navy (%s)" % (len(badge), len(star), len(cross), m["hats"][0]["fill"] if m["hats"] else None),
    badge and star and not cross and "#C0392B" not in m["fills"] and m["hats"] and navy(m["hats"][0]["fill"]), m["hatPaths"])
# F
c = D["poseidon"]
cw = [h for h in c["hats"] if h["kind"] == "cowboy"]
# (384 round 13, r10-chars) Madison: "I preferred the chief with the brown coat as well." - E's chief exactly, brown sport coat over the white shirt
chk("F. the Chief is ea31d43's (E) drawing byte for byte (%s), in the brown sport coat (%s, hue %.0f) over the white shirt (%s)" % (H["poseidon"] == PREV["E"].get("poseidon"), c["shirt"], hsl(c["shirt"])[0], "#F6F4EE" in c["fills"]),
    H["poseidon"] == PREV["E"].get("poseidon") and c["kind"] == "fcchief3" and 15 <= hsl(c["shirt"])[0] <= 40 and hsl(c["shirt"])[2] < .45 and "#F6F4EE" in c["fills"], c)
chk("F. ...with his white cowboy hat (%s), the grey moustache (%s), the bolo's turquoise (%s) and the star (%s)" % (cw and cw[0]["fill"], "#DADCE2" in c["fills"], "#3FC8B8" in c["fills"], "#6E4A0C" in c["strokes"]),
    len(cw) == 1 and hsl(cw[0]["fill"])[2] > .85 and "#DADCE2" in c["fills"] and "#3FC8B8" in c["fills"] and "#6E4A0C" in c["strokes"], c)
# G (round 14: "I like the plainclothes one" - round 13's option 1 shipped under the name Undercover)
u = D["valkyrie"]
fed = [h for h in u["hats"] if h["kind"] == "fedora"]
chk("G. Undercover is the Plainclothes detective: a charcoal fedora (%s), the tan trench coat (%s), a white shirt and dark tie, the notebook (%s), eyes of his own (%s whites)" % (fed and fed[0]["fill"], u["shirt"], "#F6F2E2" in u["fills"], u["eyeWhites"]),
    u["kind"] == "fcopt_plain" and len(fed) == 1 and hsl(fed[0]["fill"])[2] < .3 and 25 <= hsl(u["shirt"])[0] <= 45 and "#F2F2EE" in u["fills"] and "#F6F2E2" in u["fills"] and u["eyeWhites"] == 2 and "#E2BC5E" not in u["strokes"], u)
# H (round 16: "Do exit and comet. Make them look good." - round 15's option 3, the exit sign, finished)
f = D["timekeeper"]
chk("H. the timekeeper is the Exit: EXIT lit on its plate (%s), the green face panel with eyes and a smirk (%s eyes, mouth %s), a bevelled white housing with four screws (%s), the chains, the running-man pictogram (%s)" % ("#F0FFF6" in f["strokes"], f["eyeWhites"], f["mouth"], f["screws"], "#FFFFFF" in f["strokes"]),
    f["kind"] == "fcexit" and "#F0FFF6" in f["strokes"] and f["mouth"] >= 1 and f["eyes"] >= 4 and f["screws"] == 4 and "#B8C0CC" in f["strokes"] and "#FFFFFF" in f["strokes"] and not f["hats"] and f["rotGroups"] == 0, f)
# I
w = D["singularity"]
chk("I. the Whiteout: a parka hood (%s) with its fur, two lit eyes behind goggles (lit %s, %s shapes), no mouth (%s), the white flare, wind and snow (%s)" % ([h["kind"] for h in w["hats"]], w["eyesLit"], w["eyes"], w["mouth"], [g for g in w["groups"] if "wind" in g or "snow" in g]),
    [h["kind"] for h in w["hats"]] == ["hood"] and w["eyesLit"] and w["eyes"] >= 4 and w["mouth"] == 0 and "cx-fx cx-fx-wind" in w["groups"] and "cx-fx cx-fx-snow" in w["groups"] and w["flare"] and w["kind"] == "fcwhiteout2", w)
b = D["genesis"]
# (round 16) the Comet, shipped and finished: a faceted ice head, a glare of cyan slits, the tail in layers, the core flare its nucleus at the heart
chk("I. Comet: an ice head cut in planes (%s facets), two lit cyan slits (lit %s), a hard mouth (%s), its tail (%s), the core flare at its heart with the ice cracked round it (%s)" % (b["facets"], b["eyesLit"], b["mouth"], "cx-fx cx-fx-tail" in b["groups"], b["flare"]),
    b["kind"] == "fccomet" and b["facets"] >= 5 and b["eyesLit"] and b["mouth"] >= 1 and "cx-fx cx-fx-tail" in b["groups"] and not b["hats"] and b["flare"] and b["flare"][1] > 30 and "#5CE8FF" in b["fills"] and "#FF6AB4" in b["strokes"], b)
# M (round 14 asked for a woman Dispatcher; round 14b: "Nvm don't make dispatch a women") - the Dispatcher is the man again, fcdispatch3
h = D["hacker"]
chk("M. the Dispatcher is the man again (fcdispatch3: no curls, no hoops; %s, curls %s)" % (h["kind"], h["curls"]),
    h["kind"] == "fcdispatch3" and h["curls"] < 16 and "#F2C14E" not in h["strokes"] and "cx-fx cx-fx-headset" in h["groups"], h)
# J
off = {i: (D[i]["flare"], D[i]["onFig"]) for i in ("voidwalker", "umbra", "singularity", "genesis") if not D[i]["onFig"]}
chk("J. every secret's flare sits on its character's own drawn shapes (off: %s)" % (off or "none"), not off, {i: (D[i]["flare"], D[i]["onFig"]) for i in ("voidwalker", "umbra", "singularity", "genesis")})
bad = [i for i in PICKED if D[i]["heads"] != 1 or D[i]["eyes"] < 0 or not D[i]["closed"] or D[i]["mouth"] < 0 or D[i]["sp"] < 1 or D[i]["filter"]]
chk("J. every changed drawing has one head, an eye group, closed eyes, a mouth group, special parts and no svg filter (bad: %s)" % (bad or "none"), not bad, {i: D[i] for i in bad})
# L (round 16) the option rounds are closed: no options table, no pick, and none of the drawings he turned down or did not pick left in the file
O = IFC.get("opts")
chk("L. no options are left (IFC_CHAR_OPTIONS / IFC_CHAR_PICK gone: %s)" % ("gone" if not O else O.get("pick")), not O, O)
REJ = ["fcirons", "fcmarshal", "fcopt_oldtimer", "fcopt_bombtech", "fcopt_site", "fcopt_arson", "fcopt_k9", "fcopt_codeofficer", "fcopt_warden", "fcopt_recruit", "fcopt_exit", "fcopt_blackout",
       "fceclipse", "fcfirebird", "fcopt_magma", "fcopt_prism", "fcopt_aurora", "fcopt_wraith", "fcopt_darkmatter", "fcopt_comet", "fcopt_constellation", "fcagent2", "fcopt_stakeout", "fcopt_handyman", "fcdispatch4"]
left = [k for k in REJ if k in (IFC.get("kinds") or [])]
chk("L. ...and no dead drawing is left in IFC_CHAR_DRAW (left: %s; %d kinds)" % (left or "none", len(IFC.get("kinds") or [])), not left and len(IFC.get("kinds") or []) > 10, left)
# K
wrong = {i: N.get(i) for i in NAMES if N.get(i) != NAMES[i]}
chk("K. the names: %s (wrong: %s)" % (", ".join(NAMES.values()), wrong or "none"), not wrong, wrong)
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
