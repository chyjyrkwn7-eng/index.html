"""Build 382, Fire Code art: in the Fire Code class every character that is not a starter and not a rank
reward, and every banner but the three rank banners, is drawn differently from the academy's (a hash of
its drawing); the starters and the rank art are the academy's own; everything draws without an error;
Zeus is not in the Fire Code class's list (it is in the academy's), and a Fire Code account saved
wearing Zeus comes back on a character it holds, with nothing else lost.
Round 2 (Madison's review of round 1): every Fire Code character but the Smoke Diver and the eleven banners
he asked about differ from round 1's drawings (R1, hashes taken on 9ab1bc6 with --dump); the academy's art
is exactly round 1's; every Fire Code non-rank banner is layered and moves; the turned-down characters and
banners are gone and the K9 officer, logistics, horn strobe, sprinkler head, headquarters, hazmat and alarm
panel are there; the hundo ladder keeps its ids and counts, Confetti is the same, the other four are new
(Sirens, Sprinklers, Hazmat, Fire Alarm) in Fire Code only, and each plays on a screen, in a box and in a
tile, and draws its tile and still.
Round 3 ("We don't wear police styled hats. We wear cowboy hats"): every Fire Code character but the Smoke
Diver, Breacher and Recon differs from round 2 (R2, hashes taken on claude/b382 after round 2's merge) and
those three are round 2's own; the Hazmat's placard is whole under the chin and inside the circle; no drawing
carries round 2's police-cap peaks, every hat is cowboy/beanie/helmet/hood/space helmet, the inspector, chief,
investigator and star ranger wear cowboy hats; the clown's character is Strobe; headquarters, code 3, exit,
code book and the ultimates' banners are new and the rest are round 2's; no SUV is left (white pickups); the
academy is untouched; the 50 and the Fire Alarm were rebuilt in round 3 (both differ from round 2).
Round 4 (383, "Hundo effects, they all need to be better"): all four Fire Code effects differ from round 3's
(R3, hashes taken on claude/b383 before this round with --dump); the 50 is now the Extinguisher (ifxExtinguisher,
in Emergency Lights' place); and every animation they start moves only transform and opacity, no sprite of
theirs carries an svg filter, and no screen play puts up more than 170 elements.
Run:  python3 tools/check-b382-ifcart.py   (add --against old.html: copy it over index.html first, as the other checks do)"""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); H = ROOT + "/tools"
# (384) record-landing.py no longer wraps the cutscene harness (Get Started round 2 made it self-contained), so the
# harness it used to hand over as g["g"] - record-cutscenes.py's, at 1.5x - is loaded here the way it loaded it
src = open(H + "/record-cutscenes.py").read().split("\nSCENES = [")[0].replace("device_scale_factor=1)", "device_scale_factor=1.5)")
_rc = {"__file__": H + "/record-cutscenes.py", "__name__": "rc"}; exec(src, _rc)
g = {"g": _rc}
from playwright.sync_api import sync_playwright
rc = g["g"]; seed = dict(rc["SEED"]); seed["publicId"] = "xph5b57jbp5a"; seed["firstName"] = "Maddog"; seed["novaMet"] = 99
srv, port = rc["serve"]()
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else info)
STARTERS = ["ninja", "ghost", "wizard", "grizzly", "alien"]
RANK_CHARS = ["lunar", "solar", "tempest", "frost", "oracle", "inferno"]
RANK_BANNERS = ["adept_rank", "elite_rank", "titan_rank"]
# a Fire Code copy of the account, saved wearing Zeus, with a little progress that must survive
ifc_seed = dict(seed); ifc_seed["avatarChar"] = "zeus"; ifc_seed["lifetime"] = dict(seed["lifetime"], points=4321, correct=777); ifc_seed["pendingCharUnlocks"] = ["zeus"]
SNAP = """()=>{
  const hash = s => { let h = 2166136261; for(let i = 0; i < s.length; i++){ h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0).toString(16); };
  const errs = [];
  const chars = {}, banners = {};
  AVATAR_CHARACTERS.filter(c => !c.retired).forEach(c => {
    try{
      const s = drawAvatarCharSVG(c.id); const uid = s.getAttribute('data-cx-uid');
      chars[c.id] = hash(new XMLSerializer().serializeToString(s).split(uid).join('U'));
      const b = buildAvatarCharSVG(c.id); if(!b || !b.querySelector('.cx-fig')) errs.push('char ' + c.id + ' empty');
    }catch(e){ errs.push('char ' + c.id + ': ' + e); }
  });
  BANNERS.forEach(b => {
    try{
      banners[b.id] = hash(bannerStaticSVG(b.id) || '');
      const el = buildBannerArt(b.id); if(!el || !el.querySelector('svg')) errs.push('banner ' + b.id + ' empty');
      if(!bannerTintOf(b.id)) errs.push('banner ' + b.id + ' has no tint');
    }catch(e){ errs.push('banner ' + b.id + ': ' + e); }
  });
  return { chars, banners, errs, ids: AVATAR_CHARACTERS.map(c => c.id), avatar: store.avatarChar, xp: store.lifetime && [store.lifetime.points, store.lifetime.correct],
    pending: store.pendingCharUnlocks || [], zeusDraws: (() => { try{ const s = buildAvatarCharSVG('zeus'); return s ? s.getAttribute('data-char') : null; }catch(e){ return 'ERR'; } })(),
    cls: window.NOVA_CLASS,
    anim: Object.fromEntries(BANNERS.filter(b => !b.rank).map(b => { let a = null; try{ a = BANNER_ART[b.id]('g'); }catch(e){}
      return [b.id, Array.isArray(a) && a.some(l => /(^| )bl-/.test(l.cls || '') || (l.kids || []).some(k => /(^| )bl-/.test(k.cls || '')))]; })),
    bnames: Object.fromEntries(BANNERS.map(b => [b.id, b.name])),
    cnames: Object.fromEntries(AVATAR_CHARACTERS.map(c => [c.id, AVATAR_DISPLAY_NAME[c.id] || c.name || c.id])),
    fx: HUNDO_FX.map(d => [d.id, d.name, d.need]),
    fxSrc: Object.fromEntries(HUNDO_FX.map(d => [d.id, d.id === 'confetti' ? '' : hash(String((typeof HUNDO_FX_BUILD !== 'undefined' && HUNDO_FX_BUILD[d.id]) || ''))])),
    hats: (typeof IFC_CHAR_LOOK === 'undefined' || window.NOVA_CLASS !== 'ifc') ? {} : Object.fromEntries(Object.keys(IFC_CHAR_LOOK).map(id => { const sv = drawAvatarCharSVG(id); const ser = new XMLSerializer().serializeToString(sv);
      const hat = [...sv.querySelectorAll('[class*="cx-fc-hat-"]')].map(e => (e.getAttribute('class').match(/cx-fc-hat-([a-z]+)/) || [])[1]);
      /* round 2's police-style caps: the duty cap's peak and the dress caps' visors */
      const peak = ['M10.6 16.8 Q20 14.4 29.4 16.8', 'M11.8 16.6 Q20 14.4 28.2 16.6', 'M11.6 16.8 Q20 14.4 28.4 16.8', 'M12.4 16.8 Q20 14.8 27.6 16.8', 'M12 16.6 Q20 14.4 28 16.6'].some(p => ser.indexOf(p) >= 0);
      return [id, { hat, peak }]; })),
    placard: (() => { try{
      if(window.NOVA_CLASS !== 'ifc') return null;
      const box = document.createElement('div'); box.style.cssText = 'position:fixed;left:0;top:0;width:200px;height:200px;border-radius:50%;overflow:hidden';
      const sv = buildAvatarCharSVG('marksman'); sv.style.cssText = 'width:100%;height:100%'; box.appendChild(sv); document.body.appendChild(box);
      const pl = sv.querySelector('.fc-placard'), hd = sv.querySelector('.cx-head');
      if(!pl){ box.remove(); return { found: false }; }
      const r = pl.getBoundingClientRect(), h = hd.getBoundingClientRect(), sr = sv.getBoundingClientRect(), cx = sr.left + sr.width / 2, cy = sr.top + sr.height / 2, R = sr.width / 2;
      const pts = [[r.left + r.width / 2, r.top], [r.left + r.width / 2, r.bottom], [r.left, r.top + r.height / 2], [r.right, r.top + r.height / 2]];
      const worst = Math.max(...pts.map(([x, y]) => Math.hypot(x - cx, y - cy)));
      const out = { found: true, worst: Math.round(worst / R * 1000) / 1000, top: Math.round(r.top * 10) / 10, headBottom: Math.round(h.bottom * 10) / 10 };
      box.remove(); return out; }catch(e){ return { err: String(e) }; } })(),
    trucks: { suv: typeof fbSUV, pickup: typeof fbChevy, hq: /fbtruck/.test(bannerStaticSVG('tests100') || ''), code3: /fbtruck/.test(bannerStaticSVG('early10') || '') },
    fxBuild: Object.fromEntries(HUNDO_FX.map(d => [d.id, d.id === 'confetti' ? 'celebrate' : ((typeof HUNDO_FX_BUILD !== 'undefined' && HUNDO_FX_BUILD[d.id]) || {}).name || '?'])),
    fxPlay: HUNDO_FX.filter(d => d.need > 0).map(d => {
      const out = { id: d.id };
      try{
        const card = document.createElement('div'); card.className = 'rs-card rs-grade is-perfect';
        card.style.cssText = 'position:fixed;left:30px;top:300px;width:380px;height:170px';
        const pct = document.createElement('span'); pct.className = 'rs-pct pct perfect'; gradePctMarkup(pct, 100); card.appendChild(pct);
        document.body.appendChild(card);
        const h = playHundoFx(d.id, { box: card, pct, preview: true });
        out.screen = h && h.screen ? h.screen.querySelectorAll('*').length : 0;
        out.box = h && h.box ? h.box.querySelectorAll('*').length : 0;
        out.anims = document.getAnimations().length;
        /* what this effect's own Web Animations move (its layer's and its box's), and how many pieces it puts up */
        const mine = document.getAnimations().filter(a => a.constructor === Animation && a.effect && a.effect.target && ((h && h.screen && h.screen.contains(a.effect.target)) || (h && h.box && h.box.contains(a.effect.target))));
        out.props = [...new Set(mine.flatMap(a => a.effect.getKeyframes().flatMap(k => Object.keys(k))))].filter(p => ['offset', 'computedOffset', 'easing', 'composite'].indexOf(p) < 0).sort();
        if(h) h.stop();
        const st = buildHundoFxStage(d.id, {}); const h2 = playHundoFx(d.id, { box: st, pct: st.querySelector('.hfx-stage-pct'), boxOnly: true, mini: true });
        out.boxOnly = h2 && h2.box ? h2.box.querySelectorAll('*').length : 0; if(h2) h2.stop();
        out.tile = (buildHundoFxTile(d.id).querySelector('svg') || { innerHTML: '' }).innerHTML.length;
        out.still = (buildHundoFxStill(d.id) || { innerHTML: '' }).innerHTML.length;
        card.remove();
      }catch(e){ out.err = String(e); }
      return out; }),
    sprFilter: (typeof hfxSprites === 'undefined') ? [] : Object.keys(hfxSprites).filter(k => /^ifx-/.test(k) && /<filter|filter=/.test(hfxSprites[k].text || '')) };
}"""
res = {}
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    for ifc in (False, True):
        ctx, pg = rc["new_page"](br, port, 440, 956, seed)
        perr = []
        pg.on("pageerror", lambda e: perr.append(str(e)))
        if ifc:
            pg.add_init_script("try{ if(!localStorage.getItem('class26e.ifc.drill.v1')) localStorage.setItem('class26e.ifc.drill.v1', %s); }catch(e){}" % json.dumps(json.dumps(ifc_seed)))
            pg.evaluate("()=>{ localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done'); localStorage.setItem('class26e.activeclass','ifc'); }")
        pg.reload(); pg.wait_for_timeout(3500)
        r = pg.evaluate(SNAP); r["perr"] = perr
        res["ifc" if ifc else "academy"] = r
        ctx.close()
    br.close()
A, F = res["academy"], res["ifc"]
chk("the pages are the two classes (%s, %s)" % (A["cls"], F["cls"]), A["cls"] == "academy" and F["cls"] == "ifc")
chk("no page errors (%s)" % (A["perr"] + F["perr"])[:3], not A["perr"] and not F["perr"])
chk("every character and banner draws in both classes (%s)" % (A["errs"] + F["errs"])[:4], not A["errs"] and not F["errs"])
redo = [i for i in F["chars"] if i not in STARTERS and i not in RANK_CHARS]
same = [i for i in redo if F["chars"].get(i) == A["chars"].get(i)]
chk("Fire Code redraws all %d non-starter, non-rank characters (unchanged: %s)" % (len(redo), same), len(redo) >= 15 and not same, same)
kept = [i for i in STARTERS + RANK_CHARS if F["chars"].get(i) != A["chars"].get(i)]
chk("the starters and the rank characters are the academy's own (changed: %s)" % kept, not kept, kept)
bredo = [i for i in F["banners"] if i not in RANK_BANNERS]
bsame = [i for i in bredo if F["banners"].get(i) == A["banners"].get(i)]
chk("Fire Code redraws all %d non-rank banners (unchanged: %s)" % (len(bredo), bsame), len(bredo) >= 15 and not bsame, bsame)
bkept = [i for i in RANK_BANNERS if F["banners"].get(i) != A["banners"].get(i)]
chk("the rank banners are the academy's own (changed: %s)" % bkept, not bkept, bkept)
chk("Zeus is in the academy's list", "zeus" in A["ids"])
chk("Zeus is not in the Fire Code list", "zeus" not in F["ids"], F["ids"])
chk("a Fire Code account saved wearing Zeus wears a starter now (%s)" % F["avatar"], F["avatar"] in STARTERS, F["avatar"])
chk("...and Zeus is out of its unlocks to announce (%s)" % F["pending"], "zeus" not in F["pending"])
chk("...and nothing else was lost (xp %s)" % F["xp"], F["xp"] == [4321, 777], F["xp"])
chk("a stray Zeus id still draws, as a starter (%s)" % F["zeusDraws"], F["zeusDraws"] in STARTERS)
# ---- round 2 (382): Madison's review of the first Fire Code art ----
# the drawings as round 1 (9ab1bc6) left them, per class: python3 tools/check-b382-ifcart.py --dump on that code
R1 = {"academy": {"chars": {"ninja": "11c7d746", "ghost": "28b4b57c", "wizard": "bc1d7da6", "grizzly": "6c41ed4", "alien": "b64b5b9e", "detective": "127df2ac", "masked": "5027dafa", "zeus": "8df67a4b", "poseidon": "7ff9736c", "clown": "47b9e89d", "valkyrie": "ac4518ef", "marksman": "2fa1bae9", "astronaut": "4c549984", "hacker": "b469a5d8", "timekeeper": "b57166be", "ronin": "8fab636e", "hive": "ddeea61d", "voidwalker": "5c8f0be8", "umbra": "eecf33be", "singularity": "795fd62", "genesis": "1cb73899", "lunar": "5a8180ef", "solar": "42e26761", "tempest": "553ac361", "frost": "71f99d3e", "oracle": "ba0ba4ef", "inferno": "dd40a0d4", "astral": "52b3df87", "celestial": "88278084", "zenith": "846396fe"}, "banners": {"tests100": "947d4b40", "tests250": "57670d4d", "tests500": "8d6ad1e9", "hundos100": "ecba3179", "hundos250": "1ba9cde8", "vr50": "b8c3cee0", "study50": "6852b0b7", "study60": "1a13a8cb", "correct5000": "4155eb5", "correct10000": "a1741974", "level80": "dfd4656c", "early10": "468aa09c", "exam100": "96c8d9f1", "adept_rank": "84f1e18f", "elite_rank": "34c28658", "titan_rank": "d1c86e5d", "flare_void": "a7d0bb50", "flare_umbra": "a3f11b57", "flare_horizon": "1390442d", "flare_genesis": "386819a6", "astral": "ba3fcacf", "celestial": "137ac563", "zenith": "5872a257"}}, "ifc": {"chars": {"ninja": "11c7d746", "ghost": "28b4b57c", "wizard": "bc1d7da6", "grizzly": "6c41ed4", "alien": "b64b5b9e", "detective": "e46549cd", "masked": "3c5ede93", "poseidon": "45d6e556", "clown": "f3e4ca4b", "valkyrie": "25318f30", "marksman": "f763c7ac", "astronaut": "bf256eab", "hacker": "bffbe124", "timekeeper": "7b357592", "ronin": "ce3d6f17", "hive": "9fcb4d84", "voidwalker": "2443c151", "umbra": "c20f6bf3", "singularity": "cba54cb3", "genesis": "af1ea286", "lunar": "5a8180ef", "solar": "42e26761", "tempest": "553ac361", "frost": "71f99d3e", "oracle": "ba0ba4ef", "inferno": "dd40a0d4", "astral": "e733a0a7", "celestial": "ddec5603", "zenith": "e568fdab"}, "banners": {"tests100": "cd5ae759", "tests250": "40c027c2", "tests500": "d137f5c6", "hundos100": "d354b205", "hundos250": "aab5215d", "vr50": "170d42fe", "study50": "c5e37133", "study60": "2df8cc8d", "correct5000": "b6f4ed31", "correct10000": "6df94430", "level80": "2dea467d", "early10": "6e64d11d", "exam100": "876dca39", "adept_rank": "84f1e18f", "elite_rank": "34c28658", "titan_rank": "d1c86e5d", "flare_void": "547c4df6", "flare_umbra": "8b05187f", "flare_horizon": "b3594555", "flare_genesis": "5f89a8ce", "astral": "4c5176ab", "celestial": "679dbc7b", "zenith": "5503b912"}}}
if "--dump" in sys.argv:
    print(json.dumps({"academy": {"chars": A["chars"], "banners": A["banners"]}, "ifc": {"chars": F["chars"], "banners": F["banners"], "fxSrc": F["fxSrc"]}}))
    sys.exit(0)
KEPT2 = ["masked"]   # Smoke Diver: "Smoke diver is great" - kept as it was
REDO2 = [i for i in F["chars"] if i not in STARTERS and i not in RANK_CHARS and i not in KEPT2]
same2 = [i for i in REDO2 if F["chars"].get(i) == R1["ifc"]["chars"].get(i)]
chk("round 2 redraws every Fire Code character but the Smoke Diver - the Hazmat's placard too (unchanged since round 1: %s)" % same2, len(REDO2) >= 16 and not same2, same2)
BREDO2 = ["tests100", "tests250", "tests500", "hundos100", "hundos250", "vr50", "study50", "study60", "level80", "early10", "celestial"]
bsame2 = [i for i in BREDO2 if F["banners"].get(i) == R1["ifc"]["banners"].get(i)]
chk("round 2 redraws the %d banners he asked about (unchanged since round 1: %s)" % (len(BREDO2), bsame2), not bsame2, bsame2)
acad = [i for i in A["chars"] if A["chars"][i] != R1["academy"]["chars"].get(i)] + [i for i in A["banners"] if A["banners"][i] != R1["academy"]["banners"].get(i)]
chk("the academy's characters and banners are exactly as round 1 left them (changed: %s)" % acad[:6], not acad, acad)
still = [i for i, v in F["anim"].items() if not v]
chk("every Fire Code non-rank banner moves (layered, with a bl- motion) (still: %s)" % still, not still, still)
off = [n for n in ["Hotshot", "Sparky", "Fire Marshal", "Truckie", "Air Attack", "Rescue Diver", "Gold Helmet", "Backdraft", "Night Shift", "Flashover", "Blue Flame", "Phoenix",
  "K9 Officer", "Logistics", "Horn Strobe", "Cyber Marshal", "Grand Marshal", "Commander"] if n in F["cnames"].values()]
chk("no round-1 character he turned down is left in Fire Code (%s)" % off, not off, off)
# (384) "I don't like the plane examiner ... a fire extinguisher character", "Let's not do the investigator, can you make that a
# hazmat monster", "I don't like public educator, try something else": those three are the Extinguisher, Toxic Spill and Hydrant now
need = ["Undercover", "Toxic Spill", "Pump Operator", "Strobe", "Sprinkler Head"]   # (384 r7) Undercover and Pump Operator replace Pyrotech and Salamander (r5: the Extinguisher and Hydrant)
chk("the extinguisher, toxic spill, hydrant, strobe and sprinkler-head characters are there (%s)" % [n for n in need if n not in F["cnames"].values()], all(n in F["cnames"].values() for n in need))
gone = [n for n in ["Plans Examiner", "Public Educator", "Investigator"] if n in F["cnames"].values()]
chk("...and the plans examiner, public educator and investigator he turned down in 384 are gone (%s)" % gone, not gone, gone)
boff = [n for n in ["Station 26", "Ladder 26", "Tower Ladder", "Night Watch", "Night Call", "Gold Helmet", "Fire Watch", "Blue Flame", "Phoenix", "Grand Marshal"] if n in F["bnames"].values()]
chk("no firehouse, engine, ladder, crew, helmet or round-2 ultimate banner is left (%s)" % boff, not boff, boff)
chk("a certificate wall, a training tower, an incident command post, an alarm panel (On Call) and a fully-compliant banner are there", all(n in F["bnames"].values() for n in ["Certified", "Training Tower", "Incident Command", "On Call", "Fully Compliant"]), sorted(F["bnames"].values()))
afx, ffx = dict((r[0], r) for r in A["fx"]), dict((r[0], r) for r in F["fx"])
# (384) Fire Code's own counts: "the amount of hundos needed to get the stuff could be lowered. Like increments of 25, 50, 75, 150?"
# Same rungs in the same order; its counts climb, none above the academy's, and the rungs past Confetti are lower (read off the page)
ladA, ladF = [(r[0], r[2]) for r in A["fx"]], [(r[0], r[2]) for r in F["fx"]]
cntF = [n for _, n in ladF]
chk("the hundo ladder keeps its ids in Fire Code, with its own lower counts (%s against %s)" % (ladF, ladA),
    [i for i, _ in ladA] == [i for i, _ in ladF] and cntF == sorted(cntF) and len(set(cntF)) == len(cntF)
    and all(f <= a for (_, f), (_, a) in zip(ladF, ladA)) and all(f < a for (i, f), (_, a) in zip(ladF, ladA) if i != "confetti"), (ladF, ladA))
chk("Confetti, the default, is the same in both classes", afx["confetti"] == ffx["confetti"] and F["fxBuild"]["confetti"] == "celebrate")
newfx = [i for i in ffx if i != "confetti" and (ffx[i][1] == afx[i][1] or F["fxBuild"][i] == A["fxBuild"][i])]
chk("every other Fire Code hundo effect is new - its own name and its own build (same as academy: %s; %s)" % (newfx, F["fxBuild"]), not newfx, newfx)
chk("...and they are an extinguisher, sprinklers, a thermal camera and hazmat (384: the Fire Alarm is gone)", sorted(ffx[i][1] for i in ffx if i != "confetti") == ["Extinguisher", "Hazmat", "Sprinklers", "Thermal Camera"], [ffx[i][1] for i in ffx])
chk("...in that order up the ladder, Hazmat on top (%s)" % [ffx[r[0]][1] for r in F["fx"]], [r[1] for r in F["fx"] if r[0] != "confetti"] == ["Extinguisher", "Sprinklers", "Thermal Camera", "Hazmat"], F["fx"])
acfx = [i for i in afx if A["fxBuild"][i] != {"confetti": "celebrate", "fireworks": "hfxFireworks", "underwater": "hfxUnderwater", "bubbles": "hfxBubbles", "ufo": "hfxUfo"}.get(i)]
chk("the academy plays its own effects (%s)" % A["fxBuild"], not acfx, acfx)
bad = [p for p in F["fxPlay"] if not F["fxBuild"].get(p["id"], "").startswith("ifx") or p.get("err") or p["screen"] < 8 or p["box"] < 2 or p["boxOnly"] < 6 or p["tile"] < 200 or p["still"] < 100]
chk("each Fire Code effect (its own ifx build) plays across a screen, in the box and in a tile's box, and draws its tile and still (%s)" % [(p["id"], p.get("screen"), p.get("box"), p.get("boxOnly"), p.get("tile"), p.get("still"), p.get("err")) for p in F["fxPlay"]], not bad, bad)
# ---- round 3 (382): "We don't wear police styled hats. We wear cowboy hats" ----
# the drawings as round 2 (claude/b382 after its merge) left them: --dump on that code
R2 = {"academy": {"chars": {"ninja": "11c7d746", "ghost": "28b4b57c", "wizard": "bc1d7da6", "grizzly": "6c41ed4", "alien": "b64b5b9e", "detective": "127df2ac", "masked": "5027dafa", "zeus": "8df67a4b", "poseidon": "7ff9736c", "clown": "47b9e89d", "valkyrie": "ac4518ef", "marksman": "2fa1bae9", "astronaut": "4c549984", "hacker": "b469a5d8", "timekeeper": "b57166be", "ronin": "8fab636e", "hive": "ddeea61d", "voidwalker": "5c8f0be8", "umbra": "eecf33be", "singularity": "795fd62", "genesis": "1cb73899", "lunar": "5a8180ef", "solar": "42e26761", "tempest": "553ac361", "frost": "71f99d3e", "oracle": "ba0ba4ef", "inferno": "dd40a0d4", "astral": "52b3df87", "celestial": "88278084", "zenith": "846396fe"}, "banners": {"tests100": "947d4b40", "tests250": "57670d4d", "tests500": "8d6ad1e9", "hundos100": "ecba3179", "hundos250": "1ba9cde8", "vr50": "b8c3cee0", "study50": "6852b0b7", "study60": "1a13a8cb", "correct5000": "4155eb5", "correct10000": "a1741974", "level80": "dfd4656c", "early10": "468aa09c", "exam100": "96c8d9f1", "adept_rank": "84f1e18f", "elite_rank": "34c28658", "titan_rank": "d1c86e5d", "flare_void": "a7d0bb50", "flare_umbra": "a3f11b57", "flare_horizon": "1390442d", "flare_genesis": "386819a6", "astral": "ba3fcacf", "celestial": "137ac563", "zenith": "5872a257"}}, "ifc": {"chars": {"ninja": "11c7d746", "ghost": "28b4b57c", "wizard": "bc1d7da6", "grizzly": "6c41ed4", "alien": "b64b5b9e", "detective": "857e90c9", "masked": "3c5ede93", "poseidon": "67f88a58", "clown": "45a8b7f9", "valkyrie": "f478949c", "marksman": "1418723b", "astronaut": "dd8a60d5", "hacker": "bd14f8b6", "timekeeper": "e23a6fb", "ronin": "254d58e0", "hive": "70fc0c7", "voidwalker": "df2c566", "umbra": "96a3c5b5", "singularity": "feccbddf", "genesis": "e3835e73", "lunar": "5a8180ef", "solar": "42e26761", "tempest": "553ac361", "frost": "71f99d3e", "oracle": "ba0ba4ef", "inferno": "dd40a0d4", "astral": "b0ae68d1", "celestial": "8693ea46", "zenith": "4642d3e1"}, "banners": {"tests100": "63633598", "tests250": "2f60696c", "tests500": "90342325", "hundos100": "429bd0ff", "hundos250": "95a83aab", "vr50": "2757f261", "study50": "a4a85120", "study60": "f2b6a375", "correct5000": "b6f4ed31", "correct10000": "6df94430", "level80": "295e1a71", "early10": "bfccff19", "exam100": "876dca39", "adept_rank": "84f1e18f", "elite_rank": "34c28658", "titan_rank": "d1c86e5d", "flare_void": "547c4df6", "flare_umbra": "8b05187f", "flare_horizon": "b3594555", "flare_genesis": "5f89a8ce", "astral": "4c5176ab", "celestial": "cb11f4cb", "zenith": "5503b912"}, "fxSrc": {"confetti": "", "fireworks": "928ccb43", "underwater": "9b316c94", "bubbles": "ecdfba36", "ufo": "7d141962"}}}
KEPT3 = ["masked", "voidwalker", "umbra"]   # Smoke Diver; "breaches and recon look great"
REDO3 = [i for i in F["chars"] if i not in STARTERS and i not in RANK_CHARS and i not in KEPT3]
same3 = [i for i in REDO3 if F["chars"].get(i) == R2["ifc"]["chars"].get(i)]
chk("round 3 redraws every Fire Code character but the Smoke Diver, Breacher and Recon (unchanged since round 2: %s)" % same3, len(REDO3) >= 15 and not same3, same3)
# (384 sets) "All three of the ultimate characters need to look like they are trio. Same goes for the secret flare characters":
# the Breacher and Recon were redrawn as two of one squad (tools/check-b384-sets.py holds that decision now)
REDO384 = ["voidwalker", "umbra", "singularity", "genesis", "astral", "celestial", "zenith", "masked"]   # (384 r5) the Smoke Diver got its touch-up
kept3 = [i for i in KEPT3 if i not in REDO384 and F["chars"].get(i) != R2["ifc"]["chars"].get(i)]
chk("...and those three are exactly as round 2 left them, but for the two 384 redrew as the squad (changed: %s)" % kept3, not kept3, kept3)
pl = F.get("placard") or {}
chk("the Hazmat is round 1's again with its placard whole: under the chin, inside the circle (%s)" % pl, pl.get("found") and pl["worst"] <= .96 and pl["top"] >= pl["headBottom"] - .5, pl)
peaks = [i for i, v in F["hats"].items() if v["peak"]]
chk("no Fire Code character wears a police-style peaked cap (%s)" % peaks, F["hats"] and not peaks, peaks)
badhat = [(i, v["hat"]) for i, v in F["hats"].items() if any(h not in ("cowboy", "beanie", "helmet", "hood", "bubble", "hardhat") for h in v["hat"])]
chk("every hat drawn is a cowboy hat, a beanie, a helmet, a hood or a space helmet (%s)" % badhat, not badhat, badhat)
# (384) the investigator (astronaut) is the Toxic Spill now, a creature with no hat; (384 sets) Star Ranger is the last ultimate's
# (zenith) now, and the other two ultimates are rangers too
west = [i for i in ("detective", "poseidon", "astral", "celestial", "zenith") if "cowboy" not in F["hats"].get(i, {}).get("hat", [])]
chk("the inspector, the chief and the three rangers wear cowboy hats (missing: %s)" % west, not west, west)
chk("the clown's character is called Strobe (%s)" % F["cnames"].get("clown"), F["cnames"].get("clown") == "Strobe")
BREDO3 = ["tests100", "early10", "hundos100", "study50", "astral", "celestial", "zenith"]
bsame3 = [i for i in BREDO3 if F["banners"].get(i) == R2["ifc"]["banners"].get(i)]
chk("round 3 redraws headquarters, code 3, exit, code book and the three ultimates' banners (unchanged since round 2: %s)" % bsame3, not bsame3, bsame3)
# (384) Madison's banner review redrew six of these as well (tools/check-b384-banners.py holds them now), and the four flare
# banners were redrawn as one set (tools/check-b384-sets.py)
REDO384 = ["tests250", "tests500", "hundos250", "study60", "correct5000", "correct10000", "flare_void", "flare_umbra", "flare_horizon", "flare_genesis", "vr50", "level80", "exam100", "early10", "tests100", "hundos100"]
bkept3 = [i for i in F["banners"] if i not in BREDO3 and i not in REDO384 and F["banners"][i] != R2["ifc"]["banners"].get(i)]
chk("...and the banners he called awesome are as round 2 left them (changed: %s)" % bkept3, not bkept3, bkept3)
tr = F["trucks"]
# (384) "Our trucks are white chevys with ghost lettering and lights": round 3's pickup (fbPickup) is the white Chevy now (fbChevy)
chk("the office's vehicles are the white Chevys: no round-2 SUV left, fbChevy is the one vehicle (Grand Finale, Incident Command) (%s)" % tr, tr["suv"] == "undefined" and tr["pickup"] == "function", tr)  # (names pass) the vehicles are drawn by fbChevy where there are any: Grand Finale and Incident Command
acad3 = [i for i in A["chars"] if A["chars"][i] != R2["academy"]["chars"].get(i)] + [i for i in A["banners"] if A["banners"][i] != R2["academy"]["banners"].get(i)]
chk("the academy's art is untouched by round 3 (changed: %s)" % acad3[:6], not acad3, acad3)
fxn = [i for i in ("fireworks", "ufo") if F["fxSrc"].get(i) == R2["ifc"]["fxSrc"].get(i)]
chk("the 50 and the Fire Alarm were rebuilt in round 3 (unchanged since round 2: %s)" % fxn, not fxn)
# ---- round 4 (383): "Hundo effects, they all need to be better" ----
# the four as round 3 left them (claude/b383 before this round): --dump on that code
R3 = {"ifc": {"fxSrc": {"confetti": "", "fireworks": "bca3f472", "underwater": "9b316c94", "bubbles": "ecdfba36", "ufo": "51d48374"}}}
same4 = [i for i in ("fireworks", "underwater", "bubbles", "ufo") if F["fxSrc"].get(i) == R3["ifc"]["fxSrc"].get(i)]
chk("round 4 redraws all four Fire Code effects (unchanged since round 3: %s)" % same4, not same4, same4)
chk("the first rung is the Extinguisher, its own build (%s, %s)" % (ffx["fireworks"][1], F["fxBuild"]["fireworks"]), ffx["fireworks"][1] == "Extinguisher" and F["fxBuild"]["fireworks"] == "ifxExtinguisher")
moves = [(p["id"], p.get("props")) for p in F["fxPlay"] if not p.get("props") or any(x not in ("opacity", "transform") for x in p["props"])]
heavy = [(p["id"], p.get("screen")) for p in F["fxPlay"] if (p.get("screen") or 0) > 170]
chk("...and each moves only transform and opacity, no sprite has an svg filter, none puts up more than 170 pieces (%s; filters %s; %s)" % (moves, F.get("sprFilter"), [(p["id"], p.get("screen")) for p in F["fxPlay"]]),
    not same4 and not moves and not F.get("sprFilter") and not heavy, (moves, F.get("sprFilter"), heavy))
# ---- round 5 (384): "Tighten up all of them where you can to ensure they perfect" ----
# the four as round 4 left them (42bbffa, build 383, live): --dump on that code
R4 = {"ifc": {"fxSrc": {"confetti": "", "fireworks": "ff0bb357", "underwater": "8e314e0", "bubbles": "6ecbf181", "ufo": "66edfbbf"}}}
same5 = [i for i in ("fireworks", "underwater", "bubbles", "ufo") if F["fxSrc"].get(i) == R4["ifc"]["fxSrc"].get(i)]
chk("round 5 rebuilds all four Fire Code effects (unchanged since 383: %s)" % same5, not same5, same5)
chk("...the 75 is the Thermal Camera and the 150 Hazmat, each its own build (%s, %s)" % (F["fxBuild"].get("bubbles"), F["fxBuild"].get("ufo")),
    F["fxBuild"].get("bubbles") == "ifxThermal" and F["fxBuild"].get("ufo") == "ifxHazmat")
sys.exit(0 if ok else 1)
