#!/usr/bin/env python3
"""Build 384, round 9 (r4-chars): Madison's fourth look at the characters.

  "Make the undercover a secret agent or undercover agent just make it cool.. mysterious."
  "I don't like the smoke alarm, try something else. I don't like the sprinkler head, not sure why it has the smiley face, could look
   cooler and why is it gold."
  "Pulsar smiley face, like what's up with all these smiley faces on the characters.. fix that app wide I'd think."

  1. NO SMILEY ON AN OBJECT OR A COSMIC BODY, app wide, derived from the drawings: each character is built by the app and the marks it
     carries are COUNTED (the shapes in its eyes group, in its mouth group, and any pair of lit dots set symmetrically across the face
     band anywhere in its drawing). The set of characters with no face at all must be exactly the objects, tools, machines and cosmic
     bodies (and nobody else), in each class; people, and the ghost / bear / alien creatures, keep theirs.
  2. UNDERCOVER (valkyrie, Fire Code): a person in mirrored shades, an earpiece with a coiled wire, a turned-up collar - not a hat, not a tower.
  3. THE IRONS (timekeeper): a Halligan bar and an axe crossed over a shield. Not the Smoke Alarm.
  4. SPRINKLER HEAD (hive): chrome, no face, no gold; every part joined; a fan of water.
  5. PULSAR (singularity): no face; same two beams, wake, profile and flare on the rim; a glow ring and polar caps; the banner is untouched.
  6. Every drawing keeps its parts (one head, a body, the empty eye and mouth groups, special parts) in one figure, and the banners, the
     unlock rules and every other character's art are as they were (hashes of c1d224b).

  python3 tools/check-b384-r4-chars.py [--against OLD/index.html]       (every line group must FAIL on c1d224b)
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
  const out = { cls: window.NOVA_CLASS || 'academy', chars: {}, names: {}, feats: {} };
  for(const c of AVATAR_CHARACTERS.filter(c => !c.retired && !c.legacy)){
    const s = mount(c.id); const fig = s.querySelector('.cx-fig') || s;
    const eyes = s.querySelector('.cx-eyes'), shut = s.querySelector('.cx-eyes-closed'), mouth = s.querySelector('.cx-mouth'), head = s.querySelector('.cx-head');
    out.chars[c.id] = { kind: c.kind, eyes: shapes(eyes), mouth: shapes(mouth), pairs: pairs(s), heads: s.querySelectorAll('.cx-head').length, bodies: s.querySelectorAll('.cx-body').length,
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
  out.src = { cutscene: /Something lights in the dark/.test(document.documentElement.innerHTML) };
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
    { const s = mount('hive'); const ser2 = [...s.querySelectorAll('.cx-head, .cx-body')].map(g => new XMLSerializer().serializeToString(g)).join('');
      const hues = [...ser2.matchAll(/#([0-9A-Fa-f]{6})/g)].map(m => { const h = m[1], r = parseInt(h.substr(0, 2), 16) / 255, g = parseInt(h.substr(2, 2), 16) / 255, b = parseInt(h.substr(4, 2), 16) / 255, mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn; if(!d) return null; let hh = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4; hh *= 60; if(hh < 0) hh += 360; const l = (mx + mn) / 2; return { hh, s: d / (1 - Math.abs(2 * l - 1)), l }; }).filter(Boolean);
      const chromeLum = hues.length;
      out.spr = { gold: hues.filter(o => o.hh >= 38 && o.hh <= 52 && o.s >= .5 && o.l >= .3 && o.l <= .85).length, redBulb: /#FF5A4E/.test(new XMLSerializer().serializeToString(s)), rim: Math.max(...[...s.querySelectorAll('.cx-head path')].map(p => (p.getAttribute('d') || '').split('L').length)),
        streaks: [...s.querySelectorAll('.cx-body path')].filter(p => /^M[\d.]+ 31\.6 Q/.test(p.getAttribute('d') || '')).length, ridges: [...s.querySelectorAll('.cx-head path')].filter(p => /^M17 [\d.]+ L23 [\d.]+$/.test(p.getAttribute('d') || '')).length, chromeLum };
      s.remove(); }
    { const s = mount('singularity'); const ser = new XMLSerializer().serializeToString(s);
      const nums = d => (d.match(/-?[\d.]+/g) || []).map(Number);
      const wedges = [...s.querySelectorAll('.cx-fx-fcpulse path')].map(p => { const n = nums(p.getAttribute('d')); return { op: p.getAttribute('opacity'), w1: Math.hypot(n[2] - n[4], n[3] - n[5]), L: Math.hypot((n[2] + n[4]) / 2 - (n[0] + n[6]) / 2, (n[3] + n[5]) / 2 - (n[1] + n[7]) / 2) }; });
      const f = s.querySelector('.cx-fx-flare circle:nth-of-type(2)'); const head = [...s.querySelectorAll('.cx-head circle')].filter(c => /^url\(/.test(c.getAttribute('fill') || '')).sort((a, b) => b.getAttribute('r') - a.getAttribute('r'))[0];
      const off = f && head ? Math.abs(Math.hypot(+f.getAttribute('cx') - +head.getAttribute('cx'), +f.getAttribute('cy') - +head.getAttribute('cy')) - +head.getAttribute('r')) : 99;
      out.pulsar = { narrow: wedges.filter(w => !w.op && w.w1 < 3.6 && w.L > 18).length, flareOff: off, rings: [...s.querySelectorAll('.cx-fx-sqlight[transform*="rotate"]')].length, caps: !!s.querySelector('.cx-head g[clip-path]'), bands: [...s.querySelectorAll('.cx-head path')].filter(p => p.getAttribute('stroke') === '#7FC8FF' && /Q/.test(p.getAttribute('d') || '')).length,
        profile: [...s.querySelectorAll('.cx-body path')].filter(p => (p.getAttribute('d') || '').split('L').length > 15).length };
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
if "--dump" in sys.argv:   # writes the hashes of THIS build (run against c1d224b to make check-b384-r4-chars.prev.json)
    json.dump({k: {"banners": R["banners"], "chars": {i: c["hash"] for i, c in R["chars"].items()}} for k, R in (("ifc", IFC), ("academy", ACA))}, open(os.path.join(HERE, "check-b384-r4-chars.prev.json"), "w"), indent=0)
    print("dumped"); sys.exit(0)

# ---- 1. no smiley on an object or a cosmic body (derived from the drawings) ----
# The characters that carry NO face mark at all (no eye shape, no mouth shape, no symmetric pair of lit dots) must be exactly these;
# every other character is a person or one of the three creatures (ghost, bear, alien) and keeps its face.
FACELESS = {"ifc": {"clown": "Strobe, a machine", "astronaut": "Toxic Spill, a substance", "timekeeper": "The Irons, two tools and a shield", "hive": "Sprinkler Head, a part",
                    "voidwalker": "Nebula, gas", "umbra": "Quasar, a core and its disc", "singularity": "Pulsar, a neutron star", "genesis": "Eclipse, the moon"},
            "academy": {"valkyrie": "Koi, a fishbowl", "hive": "Hive, a skep", "voidwalker": "Void, a hood of stars", "genesis": "Genesis, a planet"}}
CREATURES = {"ghost", "grizzly", "alien"}
for key, R in (("ifc", IFC), ("academy", ACA)):
    C = R["chars"]
    bare = {i for i, c in C.items() if c["eyes"] == 0 and c["mouth"] == 0 and c["pairs"] == 0}
    chk("1. [%s] the characters with no face mark are exactly the objects and cosmic bodies: %s (found %s)" % (key, sorted(FACELESS[key]), sorted(bare)), bare == set(FACELESS[key]), {"extra": sorted(bare - set(FACELESS[key])), "missing": sorted(set(FACELESS[key]) - bare)})
    faced = set(C) - bare
    chk("1. [%s] every other character is a person or a creature and keeps its face (%d of them, creatures %s)" % (key, len(faced), sorted(CREATURES & faced)), CREATURES <= faced and len(faced) == len(C) - len(FACELESS[key]), sorted(faced))
    for i in CREATURES:
        c = C[i]; chk("1. [%s] the %s keeps both eyes and its mouth (%s eye marks, %s mouth)" % (key, i, c["eyes"], c["mouth"]), c["eyes"] >= 4 and c["mouth"] >= 1, c)
    # nothing without a face lost its parts: the empty eye and mouth groups stay, so every drawing has the same parts
    redrawn = {"ifc": set(FACELESS["ifc"]), "academy": {"hive", "genesis"}}[key]   # the academy's Koi and Void never had the groups
    bad = [i for i in FACELESS[key] if i in redrawn and not (C[i]["hasEyes"] and C[i]["hasShut"] and C[i]["hasMouth"])]
    chk("1. [%s] the faceless ones we redrew keep their (empty) eye, closed-eye and mouth groups (missing: %s)" % (key, bad), not bad, bad)

# ---- 6. every drawing is whole: one head, a body, in one figure, special parts, no filter ----
for key, R in (("ifc", IFC), ("academy", ACA)):
    bad = [i for i, c in R["chars"].items() if c["heads"] != 1 or c["bodies"] < 1 or not c["sameParent"] or c["filter"] or (c["sp"] < 1 and i != "forge")]
    chk("6. [%s] every character has one head, a body in the same figure, special parts (forge has none, as before) and no svg filter (bad: %s)" % (key, bad), not bad, {i: R["chars"][i] for i in bad})

# ---- 2. Undercover ----
N = IFC["names"]
chk("2. valkyrie is Undercover (fcagent), a person - not the Lookout tower (%s, %s)" % (N["valkyrie"], IFC["chars"]["valkyrie"]["kind"]), (N["valkyrie"], IFC["chars"]["valkyrie"]["kind"]) == ("Undercover", "fcagent") and "Lookout" not in N.values(), N)
A = IFC.get("agent") or {}
chk("2. ...mirrored shades (a pair of lenses), a coiled earpiece wire, a turned-up collar of two flaps, a blinking earpiece light, a badge wallet's gold, hair, no hat (%s)" % A,
    A and A["lens"] and A["coil"] and A["flaps"] == 2 and A["led"] and A["wallet"] and A["hair"] and not A["hat"], A)
chk("2. ...a flat mouth, not a smile (curve %.2f units; a smile is 1.6 or more) and no eyes drawn (the glasses cover them)" % A.get("mouthCurve", 99), A and A["mouthCurve"] <= .8 and IFC["chars"]["valkyrie"]["eyes"] == 0, A)
# ---- 3. The Irons ----
M = IFC.get("irons") or {}
chk("3. timekeeper is The Irons (fcirons), not the Smoke Alarm (%s, %s)" % (N["timekeeper"], IFC["chars"]["timekeeper"]["kind"]), (N["timekeeper"], IFC["chars"]["timekeeper"]["kind"]) == ("The Irons", "fcirons") and "Smoke Alarm" not in N.values(), N)
chk("3. ...two tools turned opposite ways about one crossing (%s), over a rimmed shield holding the Maltese cross (%s, %s), glints on the steel (%s), no hat" % (M.get("tools"), M.get("shield"), M.get("cross"), M.get("glints")),
    M and len(M["tools"]) == 2 and any("rotate(-" in t for t in M["tools"]) and any("rotate(3" in t for t in M["tools"]) and M["shield"] and M["cross"] >= 1 and M["glints"] and not M["hat"], M)
# ---- 4. Sprinkler ----
Sp = IFC.get("spr") or {}
chk("4. hive is the Sprinkler Head (fcsprinkler4), no face and no gold: %s gold-hued colours, a red glass bulb (%s), a notched deflector (%s vertices), thread ridges (%s), %s streaks of water" % (Sp.get("gold"), Sp.get("redBulb"), Sp.get("rim"), Sp.get("ridges"), Sp.get("streaks")),
    (N["hive"], IFC["chars"]["hive"]["kind"]) == ("Sprinkler Head", "fcsprinkler4") and Sp and Sp["gold"] == 0 and Sp["redBulb"] and Sp["rim"] >= 40 and Sp["ridges"] >= 3 and Sp["streaks"] >= 9, Sp)
# ---- 5. Pulsar ----
Pu = IFC.get("pulsar") or {}
chk("5. Pulsar keeps its two narrow opposed beams (%s), its flare on the rim (%.2f off, at most .5), its banded surface (%s) and its pulse profile (%s)" % (Pu.get("narrow"), Pu.get("flareOff", 99), Pu.get("bands"), Pu.get("profile")),
    Pu and Pu["narrow"] == 2 and Pu["flareOff"] <= .5 and Pu["bands"] >= 3 and Pu["profile"] >= 3, Pu)
chk("5. ...and has a glow ring on its equator (%s) and polar caps clipped to the star (%s) where its eyes and smile were" % (Pu.get("rings"), Pu.get("caps")), Pu and Pu["rings"] >= 2 and Pu["caps"], Pu)

# ---- names, rules, banners, everyone else's art ----
chk("the secret-flare cutscene's last line is class-aware (the Quasar has no eyes to open)", IFC["src"]["cutscene"], IFC["src"])
glows = list(IFC["glows"].values())
chk("the eleven challenge characters have eleven different glow colours (%s)" % glows, len(set(glows)) == 11, glows)
FEATS = {"valkyrie": "studyrun7", "timekeeper": "days30", "hive": "busyday300", "singularity": "flare5", "clown": "vrwins5", "astronaut": "hundo7day"}
chk("every unlock rule is as it was (%s)" % {i: IFC["feats"][i] for i in FEATS}, all(IFC["feats"][i] == f for i, f in FEATS.items()) and all(ACA["feats"][i] == f for i, f in FEATS.items()), IFC["feats"])
PREV_BANNERS = json.load(open(os.path.join(HERE, "check-b384-r4-chars.prev.json")))
for key, R in (("ifc", IFC), ("academy", ACA)):
    moved = sorted(i for i, h in PREV_BANNERS[key]["banners"].items() if R["banners"].get(i) != h)
    chk("[%s] no banner moved since c1d224b - the Pulsar banner (flare_horizon) turns as one body and needed no change (moved: %s)" % (key, moved), not moved, moved)
    mov = sorted(i for i, h in PREV_BANNERS[key]["chars"].items() if R["chars"].get(i, {}).get("hash") != h)
    expect = {"ifc": {"clown", "valkyrie", "astronaut", "timekeeper", "hive", "voidwalker", "umbra", "singularity", "genesis"}, "academy": {"hive", "genesis"}}[key]
    chk("[%s] only the characters named here changed their art since c1d224b (changed: %s)" % (key, mov), set(mov) == expect, {"changed": mov, "expected": sorted(expect)})
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
