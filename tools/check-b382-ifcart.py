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
Run:  python3 tools/check-b382-ifcart.py   (add --against old.html: copy it over index.html first, as the other checks do)"""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); H = ROOT + "/tools"
src = open(H + "/record-landing.py").read().split("\nSCENES = {")[0]
g = {"__file__": H + "/record-landing.py", "__name__": "rl"}; exec(src, g)
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
        if(h) h.stop();
        const st = buildHundoFxStage(d.id, {}); const h2 = playHundoFx(d.id, { box: st, pct: st.querySelector('.hfx-stage-pct'), boxOnly: true, mini: true });
        out.boxOnly = h2 && h2.box ? h2.box.querySelectorAll('*').length : 0; if(h2) h2.stop();
        out.tile = (buildHundoFxTile(d.id).querySelector('svg') || { innerHTML: '' }).innerHTML.length;
        out.still = (buildHundoFxStill(d.id) || { innerHTML: '' }).innerHTML.length;
        card.remove();
      }catch(e){ out.err = String(e); }
      return out; }) };
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
    print(json.dumps({"academy": {"chars": A["chars"], "banners": A["banners"]}, "ifc": {"chars": F["chars"], "banners": F["banners"]}}))
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
off = [n for n in ["Hotshot", "Sparky", "Fire Marshal", "Truckie", "Air Attack", "Rescue Diver", "Gold Helmet", "Backdraft", "Night Shift", "Flashover", "Blue Flame", "Phoenix"] if n in F["cnames"].values()]
chk("no round-1 character he turned down is left in Fire Code (%s)" % off, not off, off)
need = ["K9 Officer", "Logistics", "Horn Strobe", "Sprinkler Head", "Investigator"]
chk("the K9 officer, logistics, fire alarm and sprinkler-head characters are there (%s)" % [n for n in need if n not in F["cnames"].values()], all(n in F["cnames"].values() for n in need))
boff = [n for n in ["Station 26", "Ladder 26", "The Crew", "Tower Ladder", "Night Watch", "Night Call", "Gold Helmet"] if n in F["bnames"].values()]
chk("no firehouse, engine, ladder, crew or helmet banner is left (%s)" % boff, not boff, boff)
chk("a headquarters, two hazmat banners and an alarm panel banner are there", all(n in F["bnames"].values() for n in ["Headquarters", "Spill Response", "Hazmat", "Alarm Panel"]), sorted(F["bnames"].values()))
afx, ffx = dict((r[0], r) for r in A["fx"]), dict((r[0], r) for r in F["fx"])
chk("the hundo ladder keeps its ids and counts in Fire Code (%s)" % F["fx"], [(r[0], r[2]) for r in A["fx"]] == [(r[0], r[2]) for r in F["fx"]])
chk("Confetti, the default, is the same in both classes", afx["confetti"] == ffx["confetti"] and F["fxBuild"]["confetti"] == "celebrate")
newfx = [i for i in ffx if i != "confetti" and (ffx[i][1] == afx[i][1] or F["fxBuild"][i] == A["fxBuild"][i])]
chk("every other Fire Code hundo effect is new - its own name and its own build (same as academy: %s; %s)" % (newfx, F["fxBuild"]), not newfx, newfx)
chk("...and they are sirens, sprinklers, hazmat and a fire alarm", sorted(ffx[i][1] for i in ffx if i != "confetti") == ["Fire Alarm", "Hazmat", "Sirens", "Sprinklers"], [ffx[i][1] for i in ffx])
acfx = [i for i in afx if A["fxBuild"][i] != {"confetti": "celebrate", "fireworks": "hfxFireworks", "underwater": "hfxUnderwater", "bubbles": "hfxBubbles", "ufo": "hfxUfo"}.get(i)]
chk("the academy plays its own effects (%s)" % A["fxBuild"], not acfx, acfx)
bad = [p for p in F["fxPlay"] if not F["fxBuild"].get(p["id"], "").startswith("ifx") or p.get("err") or p["screen"] < 8 or p["box"] < 2 or p["boxOnly"] < 6 or p["tile"] < 200 or p["still"] < 100]
chk("each Fire Code effect (its own ifx build) plays across a screen, in the box and in a tile's box, and draws its tile and still (%s)" % [(p["id"], p.get("screen"), p.get("box"), p.get("boxOnly"), p.get("tile"), p.get("still"), p.get("err")) for p in F["fxPlay"]], not bad, bad)
sys.exit(0 if ok else 1)
