#!/usr/bin/env python3
"""Build 384: Fire Code's secret-flare four are one squad and its three ultimates one trio, with Star Ranger the last.

Madison: "I don't like flashbang that much, try again. I don't like how you can see his face." / "Star ranger looks sick,
that should be the last ultimate character? ... Use that idea for another character?" / "All three of the ultimate
characters need to look like they are trio. Same goes for the secret flare characters." / "The secret flare banners, I
don't really like any of those, that much. Same for the ultimate character banners".

  (1) THE LAST ULTIMATE IS STAR RANGER: the ultimate whose challenge is everything (feat "everything", last in the list)
      is round 3's Star Ranger drawing, unchanged but for its special (STAR_R3: its hash on 185cc5c, the special's
      .cx-sp parts taken out), and carries its name.
  (2) THE ULTIMATES ARE A TRIO (384 r6: one now, Star Ranger, in a space helmet; 384 round 12: round 3's again, cowboy hat and duster): the star badge and eyes, and a ring of
      sparks that grows up the three (astral < celestial < zenith); astral and celestial are new drawings.
  (3) THE SECRET FOUR ARE A SQUAD: each wears the same helmet (cx-fc-hat-helmet), and they share most of their drawing -
      the same shapes in all four - while each keeps its own colour.
  (4) NO FACE: none of the four draws an eye or skin (the Flashbang showed his face).
  (5) THE SCENES: in the secret-flare scene's silhouette each of the four has something lit to show first in the dark.
  (6) THE SPECIALS end on the squad's flare / the agency's star, not the generic cross, and each ends with its own last part.
  (7) THE BANNERS: the four squad banners are one set (the same roof, the same squad silhouette), as are the three
      rangers' (the same mesas, the same ranger); each is new; each banner is named for its character; every layer moves
      by transform/opacity only, carries no svg filter, and there are at most 14 layers.
  (8) THE ACADEMY is untouched: its seven characters and banners hash as on 185cc5c.
  (9) no page errors in either class.

  python3 tools/check-b384-sets.py [--against OLD/index.html]   (must FAIL on the build before)
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
from playwright.sync_api import sync_playwright
BODY = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read() if "--against" in sys.argv else None
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)
SQUAD = ["voidwalker", "umbra", "singularity", "genesis"]
TRIO = ["zenith"]   # (384 characters round) ONE ultimate per class now: Fire Code keeps only the Star Ranger (the academy only Astral)
SQB = ["flare_void", "flare_umbra", "flare_horizon", "flare_genesis"]
# round 3's Star Ranger (Fire Code's celestial on 185cc5c), its special's parts taken out
STAR_R3 = "348c7ae4"
# the drawings and banners as 185cc5c left them, Fire Code and academy
BEFORE = {"ifc": {"c": {"voidwalker": "df2c566", "umbra": "96a3c5b5", "singularity": "3c272ac0", "genesis": "39015c5a", "astral": "f44e59d7", "celestial": "ca691cb7", "zenith": "9d381ee6"},
                  "b": {"flare_void": "547c4df6", "flare_umbra": "8b05187f", "flare_horizon": "b3594555", "flare_genesis": "5f89a8ce", "astral": "80e25fb1", "celestial": "3788fd6b", "zenith": "6b91fb64"}},
          "academy": {"c": {"voidwalker": "5c8f0be8", "umbra": "eecf33be", "singularity": "795fd62", "genesis": "1cb73899", "astral": "52b3df87", "celestial": "88278084", "zenith": "846396fe"},
                      "b": {"flare_void": "a7d0bb50", "flare_umbra": "a3f11b57", "flare_horizon": "1390442d", "flare_genesis": "386819a6", "astral": "ba3fcacf", "celestial": "137ac563", "zenith": "5872a257"}}}
seed = dict(rc["SEED"]); seed.update(novaMet=99, seenClassTip=True, publicId="pubsets384", classes=["academy", "ifc"])
SNAP = r"""()=>{
  const hash = s => { let h = 2166136261; for(let i = 0; i < s.length; i++){ h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0).toString(16); };
  const SQUAD = %s, TRIO = %s, SQB = %s, TRB = TRIO;
  const ser = (s) => new XMLSerializer().serializeToString(s).split(s.getAttribute('data-cx-uid')).join('U');
  const out = { cls: window.NOVA_CLASS, c: {}, b: {} };
  SQUAD.concat(TRIO).forEach(id => out.c[id] = hash(ser(drawAvatarCharSVG(id))));
  SQB.concat(TRB).forEach(id => out.b[id] = hash(bannerStaticSVG(id) || ''));
  if(window.NOVA_CLASS !== 'ifc') return out;
  const ult = AVATAR_CHARACTERS.filter(c => c.ultimate);
  out.lastUlt = { id: ult[ult.length - 1].id, feat: ult[ult.length - 1].feat, order: ult.map(c => c.id) };
  const noSp = id => { const s = drawAvatarCharSVG(id); s.querySelectorAll('.cx-sp').forEach(n => n.remove()); return hash(ser(s)); };
  out.lastHash = noSp(out.lastUlt.id);
  out.noSp = Object.fromEntries(TRIO.map(id => [id, noSp(id)]));
  out.names = Object.fromEntries(SQUAD.concat(TRIO).map(id => [id, AVATAR_DISPLAY_NAME[id]]));
  out.glow = Object.fromEntries(SQUAD.concat(TRIO).map(id => [id, AVATAR_GLOW[id]]));
  /* the drawing's own shapes (no scenery, no special): every path d / circle / ellipse, as text */
  const shapes = id => { const s = drawAvatarCharSVG(id); s.querySelectorAll('.cx-bg, .cx-sp').forEach(n => n.remove());
    const set = new Set(); s.querySelectorAll('path, circle, ellipse, rect').forEach(n => {
      const k = n.tagName + ':' + ['d', 'cx', 'cy', 'r', 'rx', 'ry', 'x', 'y', 'width', 'height'].map(a => n.getAttribute(a) || '').join(','); set.add(k); });
    return set; };
  const shared = ids => { const sets = ids.map(shapes); const first = [...sets[0]]; return { shared: first.filter(k => sets.every(s => s.has(k))).length, sizes: sets.map(s => s.size) }; };
  out.squadShared = shared(SQUAD); out.trioShared = shared(TRIO);
  const look = id => { const s = drawAvatarCharSVG(id);
    const hats = [...s.querySelectorAll('[class*="cx-fc-hat-"]')].map(e => (e.getAttribute('class').match(/cx-fc-hat-([a-z]+)/) || [])[1]);
    const eyes = s.querySelector('.cx-eyes'); const orbit = s.querySelector('.cx-fx-fcorbit');
    /* skin: any gradient with a FC_SKIN stop, referenced */
    const skinCols = new Set([].concat(...Object.values(FC_SKIN)).map(c => c.toUpperCase()));
    const skinIds = [...s.querySelectorAll('radialGradient, linearGradient')].filter(g => [...g.querySelectorAll('stop')].some(st => skinCols.has((st.getAttribute('stop-color') || '').toUpperCase()))).map(g => g.id);
    const skinUsed = [...s.querySelectorAll('[fill]')].some(n => skinIds.some(i => n.getAttribute('fill') === 'url(#' + i + ')'));
    return { hats, eyes: eyes ? eyes.querySelectorAll('*').length : 0, orbit: orbit ? orbit.querySelectorAll('circle').length - 1 : 0, skin: skinUsed,
      lapel: !!s.querySelector('path[d^="M12.4 29 L16 28.2 L20 36"]'), badge: s.querySelectorAll('circle + path[stroke-linejoin="round"]').length };
  };
  out.look = Object.fromEntries(SQUAD.concat(TRIO).map(id => [id, look(id)]));
  /* the silhouette the secret-flare scene shows first */
  out.first = Object.fromEntries(SQUAD.map(id => { let n = 0; try{ const s = sfSilhouetteSVG(id); s.querySelectorAll('.sf-key-first').forEach(w => n += w.querySelectorAll('path, circle, ellipse, rect').length); }catch(e){ n = -1; } return [id, n]; }));
  /* the special's last mark: the front part's own path (a cross has 5 subpaths of 4 points; a star 10 points; a burst 8 rays) */
  out.special = Object.fromEntries(SQUAD.concat(TRIO).map(id => { const s = buildAvatarCharSVGSafe(id); const f = s.querySelector('.cx-sp-front');
    const ds = f ? [...f.querySelectorAll('path')].map(p => p.getAttribute('d') || '') : [];
    const star = ds.some(d => (d.match(/[ML]/g) || []).length === 10 && (d.match(/Z/g) || []).length === 1);
    const burst = ds.some(d => (d.match(/Z/g) || []).length === 8);
    return [id, star ? 'star' : burst ? 'burst' : 'other']; }));
  /* banners */
  const bshapes = id => { const set = new Set(); const t = document.createElement('div'); t.innerHTML = bannerStaticSVG(id) || '';
    t.querySelectorAll('path').forEach(p => { const d = p.getAttribute('d') || ''; if(d.length > 60) set.add(d); }); return set; };
  const bshared = ids => { const sets = ids.map(bshapes); return [...sets[0]].filter(k => sets.every(s => s.has(k))).length; };
  out.bSquadShared = bshared(SQB); out.bTrioShared = bshared(TRB);
  out.bnames = Object.fromEntries(SQB.concat(TRB).map(id => { const b = BANNERS.find(x => x.id === id); return [id, b && b.name]; }));
  out.bchar = Object.fromEntries(SQB.map(id => { const b = BANNERS.find(x => x.id === id); return [id, b && b.flareChar]; }));
  /* every class a layer moves by, and what its keyframes change */
  const kf = {}; for(const sh of document.styleSheets){ let rules; try{ rules = sh.cssRules; }catch(e){ continue; }
    const walk = rs => { for(const r of rs){ if(r.cssRules && !(r instanceof CSSKeyframesRule)) walk(r.cssRules);
      if(r instanceof CSSKeyframesRule){ const props = new Set(); for(const k of r.cssRules) for(let i = 0; i < k.style.length; i++) props.add(k.style[i]); kf[r.name] = [...props]; }
      if(r.selectorText && /\.bn-stage \.bl-[a-z-]+$/.test(r.selectorText) && r.style.animationName) kf['cls:' + r.selectorText.split('.').pop()] = r.style.animationName; } };
    walk(rules); }
  out.layers = Object.fromEntries(SQB.concat(TRB).map(id => { const art = BANNER_ART[id]('x'); const L = Array.isArray(art) ? art : [];
    const flat = []; const add = l => { flat.push(l); (l.kids || []).forEach(add); }; L.forEach(add);
    const bad = []; flat.forEach(l => (l.cls || '').split(/\s+/).filter(Boolean).forEach(c => { const an = kf['cls:' + c]; const props = an ? (kf[an] || ['?']) : ['?' + c];
      props.forEach(p => { if(!/^(transform|opacity|translate|scale|rotate)$/.test(p)) bad.push(c + ':' + p); }); }));
    const filt = flat.some(l => /filter/i.test(l.svg || ''));
    return [id, { n: flat.length, moving: flat.filter(l => l.cls).length, bad: [...new Set(bad)], filt }]; }));
  return out;
}""" % (json.dumps(SQUAD), json.dumps(TRIO), json.dumps(SQB))
SPEND = r"""async () => {
  const bad = [], ok = [];
  for(const id of %s){
    const el = document.createElement('div'); el.className = 'profile-hero-avatar __n';
    el.style.cssText = 'position:fixed;left:0;top:0;width:160px;height:160px';
    const svg = buildAvatarCharSVGSafe(id); el.appendChild(svg); document.body.appendChild(el); el.classList.add('char-live');
    await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
    if(!charHasSpecial(el)){ bad.push(id + ' none'); el.remove(); continue; }
    const before = new Set(svg.getAnimations({ subtree: true }));
    /* the call itself can take a while on a loaded machine, so what it planned is read as a window: from the moment
       after the call (lo) to the moment before it (hi); the animations' end has to fall in it */
    charSpecialBusyUntil = 0; const t0 = Date.now(); playCharSpecial(el); const t1 = Date.now();
    const hi = charSpecialBusyUntil - 400 - t0, lo = charSpecialBusyUntil - 400 - t1; let end = 0;
    svg.getAnimations({ subtree: true }).forEach(a => { if(before.has(a)) return; const e = a.effect.getComputedTiming().endTime; if(isFinite(e)) end = Math.max(end, e); });
    (end >= lo - 60 && end <= hi + 5 ? ok : bad).push(id + ' ' + Math.round(lo) + '-' + Math.round(hi) + '/' + Math.round(end));
    el.__charSpecial = null; el.classList.remove('char-special'); el.remove();
  }
  return { bad, ok }; }""" % json.dumps(SQUAD + TRIO)
srv, port = rc["serve"]()
R, errs = {}, {}
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    for cls in ("academy", "ifc"):
        ctx = br.new_context(viewport={"width": 440, "height": 956}); pg = ctx.new_page(); e = []
        pg.on("pageerror", lambda x, e=e: e.append(str(x)[:160]))
        init = "try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','99');localStorage.setItem('class26e.drill.v1',%s);" % json.dumps(json.dumps(seed))
        if cls == "ifc":
            init += ("localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));localStorage.setItem('class26e.greet.ifc','done');"
                     "['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted'].forEach(k=>localStorage.setItem(k,'1'));"
                     "localStorage.setItem('class26e.ifc.drill.v1',%s);" % json.dumps(json.dumps(seed)))
        pg.add_init_script(init + "}catch(e){}")
        if BODY is not None:
            pg.route("**/index.html", lambda r: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
        pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(3200)
        try:
            R[cls] = pg.evaluate(SNAP)
            if cls == "ifc":
                # (6) as check-b327z15 N: each special ends when its own last part does - no hold, no cut
                R[cls]["spEnd"] = pg.evaluate(SPEND)
        except Exception as x:
            R[cls] = {"err": str(x)[:300]}
        errs[cls] = e; ctx.close()
    br.close()
srv.shutdown()
A, F = R["academy"], R["ifc"]
if "--dump" in sys.argv:
    print(json.dumps(R, indent=1)); sys.exit(0)
chk("the pages are the two classes (%s, %s)" % (A.get("cls"), F.get("cls")), A.get("cls") == "academy" and F.get("cls") == "ifc", (A.get("err"), F.get("err")))
if F.get("err"):
    chk("Fire Code's page answered the probe", False, F["err"]); print("\nFAILURES"); sys.exit(1)
lu = F["lastUlt"]
# (1)
chk("(1) the last ultimate (%s, feat %s) is round 3's Star Ranger drawing (%s, want %s)" % (lu["id"], lu["feat"], F["lastHash"], STAR_R3),
    lu["feat"] == "everything" and lu["order"][-1] == lu["id"], lu)   # (384 r5: touched up, so no longer its hash)
chk("(1) ...and carries round 3's Star Ranger's name (%s)" % F["names"].get(lu["id"]), F["names"].get(lu["id"]) == "Star Ranger")
# (2)
lk = F["look"]
# (384 r6) "Fire inspectors wear police gear": nobody in Fire Code wears a cowboy hat any more. The one ultimate, Star Ranger, is the
# agency's uniform taken to the stars - a navy space suit, the gold star badge and a bubble helmet; the duster (a western coat) is gone and
# his eyes are clear, not lit (the lit eyes were the crowned rulers' treatment). tools/check-b384-r6-chars.py holds the rest.
# (384 round 12, r9-chars) Madison picked round 3's Star Ranger back ("Star Ranger: E"): the night-sky cowboy hat with its burning band,
# the duster over the cosmic suit, the star badge, the gold-lit eyes. The space-helmet round is undone.
notcow = [i for i in TRIO if "cowboy" not in lk[i]["hats"]]
chk("(2) the ultimate wears round 3's night-sky cowboy hat again (not: %s)" % notcow, not notcow, {i: lk[i]["hats"] for i in TRIO})
chk("(2) ...the star badge and a pair of eyes (%s)" % {i: (lk[i]["lapel"], lk[i]["badge"], lk[i]["eyes"]) for i in TRIO},
    all(lk[i]["badge"] >= 1 and lk[i]["eyes"] >= 2 for i in TRIO))
orb = [lk[i]["orbit"] for i in TRIO]
chk("(2) ...and the ring of sparks grows up the three (%s)" % orb, len(orb) < 3 or orb[0] < orb[1] < orb[2], orb)
ts = F["trioShared"]
chk("(2) the three share the bulk of one drawing (%d shapes in all three, of %s)" % (ts["shared"], ts["sizes"]), ts["shared"] >= 0.45 * min(ts["sizes"]), ts)
# (2) astral and celestial left Fire Code with the ultimates round (one per class) - nothing to hold
chk("(2) the rangers are different drawings", len({F["c"][i] for i in TRIO}) == len(TRIO))
# (3)
# (384 r5: "I don't like the secret flare characters from ifc ... follow the academy theme but come up with new ones" - the
# squad is withdrawn: the four are celestial beings now, so none wears a hat or a helmet, and they are four different drawings)
# (384 round 12) Recon (back from build 383) and the Whiteout are figures again; the Whiteout's parka hood is a hood, not a hat
noh = [i for i in SQUAD if [h for h in lk[i]["hats"] if h != "hood"]]
chk("(3) none of the four wears a helmet or a hat (a parka hood is neither) (hats: %s)" % noh, not noh, {i: lk[i]["hats"] for i in SQUAD})
chk("(3) the four are four different drawings", len({F["c"][i] for i in SQUAD}) == 4)
gl = [F["glow"][i] for i in SQUAD]
chk("(3) ...each in its own colour (%s)" % gl, len(set(gl)) == 4)
news = [i for i in SQUAD if F["c"][i] == BEFORE["ifc"]["c"][i]]
chk("(3) all four are new drawings (unchanged: %s)" % news, not news)
# (4)
face = [i for i in SQUAD if lk[i]["skin"]]
chk("(4) no human skin on any of the four (%s)" % {i: (lk[i]["eyes"], lk[i]["skin"]) for i in face}, not face)
# (5)
fs = F["first"]
dark = [i for i in SQUAD if fs[i] < 1]
chk("(5) in the secret-flare scene each of the four has something lit to show first in the dark (%s)" % fs, not dark, fs)
# (6)
sp = F["special"]
badsp = [i for i in SQUAD if sp[i] != "burst"] + [i for i in TRIO if sp[i] != "star"]
chk("(6) the squad's specials end on a flare bursting, the rangers' on the star (%s)" % sp, not badsp, sp)
se = F.get("spEnd") or {}
chk("(6) ...and each ends when its own last part does, as check-b327z15 N asks (%s)" % (se.get("ok") or se), se and not se.get("bad") and len(se.get("ok") or []) == 4 + len(TRIO), se)
# (7)
# (names pass) the four secret-flare banners are four scenes of their own, no longer one template: nothing long is drawn in all four
chk("(7) the four secret-flare banners are four different scenes (%d long shapes in all four)" % F["bSquadShared"], F["bSquadShared"] == 0, F["bSquadShared"])
chk("(7) the one ranger banner is drawn (%d long shapes)" % F["bTrioShared"], len(TRIO) < 2 or F["bTrioShared"] >= 2, F["bTrioShared"])
newb = [i for i in SQB + TRIO if F["b"][i] == BEFORE["ifc"]["b"][i]]
chk("(7) all seven banners are new (unchanged: %s)" % newb, not newb)
bn = F["bnames"]
# the secret-flare banners are named for the characters they come with (Nebula, Quasar, Pulsar, Eclipse (was Solstice): the character helper renames the four to match)
mism = [i for i in SQB if bn[i] != dict(zip(SQB, ["Nebula", "Quasar", "Pulsar", "Eclipse"]))[i]] + [i for i in TRIO if bn[i] != F["names"][i]]
chk("(7) each banner is named for its character (%s)" % bn, not mism, mism)
ly = F["layers"]
badl = {i: v for i, v in ly.items() if v["bad"] or v["filt"] or v["n"] > 14 or v["moving"] < 3}
chk("(7) every layer moves by transform/opacity only, no svg filter, 3+ moving and at most 14 layers (%s)" % {i: (v["n"], v["moving"]) for i, v in ly.items()}, not badl, badl)
# (8)
# (384 characters round 2) the base-art connection audit fixed joins in Void, Umbra and Genesis on purpose ("go through each character thoroughly to
# ensure all pieces connect right"); anything else changed is still a failure
AUDITED = {"c:voidwalker", "c:umbra", "c:genesis"}
acad = [k + ":" + i for k in ("c", "b") for i in A[k] if A[k][i] != BEFORE["academy"][k][i] and (k + ":" + i) not in AUDITED]
chk("(8) the academy's characters and banners are as 185cc5c left them, bar the three joined up in the connection audit (changed: %s)" % acad, not acad)
# (9)
chk("(9) no page errors (%s)" % (errs["academy"] + errs["ifc"])[:3], not errs["academy"] and not errs["ifc"])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
