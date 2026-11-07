#!/usr/bin/env python3
"""Build 384: Madison's review of Fire Code's challenge characters.

  "I don't like the plane examiner. Could we make that a fire extinguisher character?"
  "The inspector looks cool but inspector needs the blue colored shirt like investigator."
  "Let's not do the investigator, can you make that a hazmat monster or something cool?"
  "I don't like public educator, try something else."
  "Strobe and sprinkler look awesome, could they be better? We don't need to add stuff to it"
  "Drone pilot is sick, the drone is like sitting on his head though?"
  "After this do any touchups on the entire character list"

Checked in the Fire Code class (the academy draws these ids as its own characters and is untouched):
  A. the plans examiner, investigator and public educator are three new drawings (kinds of their own, none of the
     turned-down names), each with the parts every character has (eyes, closed eyes, a mouth, a head), no svg filter,
     its own scene and glow, and a special that draws; the hazmat monster is not a second suited person (no hat, not
     the Hazmat's drawing or colour)
  B. the inspector's shirt is blue (its hue read off the drawing), the rest of him as he was (hat, glasses, clipboard)
  C. the drone flies: measured in a coin, clear air between the drone (its downlight included) and the pilot's hair,
     and the whole drone inside the coin's circle
  D. the strobe and the sprinkler are redrawn with exactly the parts they had: no new part, none lost
  E. the dispatcher's shirt reads against his sky (its base colour lighter than before)
  F. every Fire Code challenge character's special ends with its own last part (check-b327z15 N's measure, which runs in
     the academy only), the three new kinds among them
Every check here fails on 185cc5c (the build before):  python3 tools/check-b384-ifcchars.py --against OLD/index.html
"""
import colorsys, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
from playwright.sync_api import sync_playwright
BODY = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read() if "--against" in sys.argv else None
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)
seed = dict(rc["SEED"]); seed.update(seenClassTip=True, novaMet=99, publicId="tst4fc8chars1", classes=["academy", "ifc"])
INIT = ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
        "localStorage.setItem('class26e.drill.v1',%s);localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));"
        "localStorage.setItem('class26e.greet.ifc','done');['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted','class26e.a2hs'].forEach(k=>localStorage.setItem(k,'1'));"
        "localStorage.setItem('class26e.ifc.drill.v1',%s);}catch(e){}") % (json.dumps(json.dumps(seed)), json.dumps(json.dumps(seed)))
# the three he turned down, and the strobe's and sprinkler's parts and drawings as 185cc5c drew them (--dump on that build)
OLD_KINDS = {"valkyrie": "fcplans", "astronaut": "fcinvest2", "timekeeper": "fceducator"}
OLD_NAMES = ["Plans Examiner", "Investigator", "Public Educator"]
BEFORE = {"clown": {"hash": "3062d90d", "parts": ["cx-body", "cx-eyes", "cx-eyes-closed", "cx-fx cx-fx-fcflash", "cx-fx cx-fx-fcwave", "cx-head", "cx-mouth"]},
          "hive": {"hash": "c6aee1e9", "parts": ["cx-body", "cx-eyes", "cx-eyes-closed", "cx-fx cx-fx-fcspray", "cx-fx cx-fx-scopeglow", "cx-head", "cx-mouth"]},
          "hacker": {"shirt": "#26355A"}}
SNAP = r"""async (oldKinds) => {
  document.getElementById('splashscreen')?.remove();
  const hash = s => { let h = 2166136261; for(let i = 0; i < s.length; i++){ h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0).toString(16); };
  const drawn = id => { const s = drawAvatarCharSVG(id), uid = s.getAttribute('data-cx-uid'); return { s, ser: new XMLSerializer().serializeToString(s).split(uid).join('U') }; };
  const parts = s => [...new Set([...s.querySelectorAll('g[class]')].map(g => g.getAttribute('class')).filter(c => /^cx-/.test(c) && !/^cx-(fig|sp|spark|fx cx-fx-sparkles|fx cx-fx-bg|bg|centre)/.test(c)))].sort();
  const stops = (s, n) => { const f = (n && n.getAttribute('fill')) || ''; const m = f.match(/url\(#([^)]+)\)/); const g = m && s.querySelector('[id="' + m[1] + '"]'); return g ? [...g.querySelectorAll('stop')].map(x => x.getAttribute('stop-color')) : [f]; };
  const out = { cls: window.NOVA_CLASS, three: {}, strobe: {} };
  for(const id of Object.keys(oldKinds)){
    const def = AVATAR_CHARACTERS.find(c => c.id === id), { s, ser } = drawn(id);
    const sp = (() => { try{ const b = buildAvatarCharSVG(id); return b.querySelectorAll('.cx-sp *').length; }catch(e){ return -1; } })();
    out.three[id] = { kind: def.kind, name: AVATAR_DISPLAY_NAME[id], glow: AVATAR_GLOW[id], drawer: !!(IFC_CHAR_DRAW && IFC_CHAR_DRAW[def.kind]),
      scene: !!(IFC_BACKDROP && IFC_BACKDROP[def.kind]), hasHead: !!s.querySelector('.cx-head'), eyes: !!s.querySelector('.cx-eyes'), closed: !!s.querySelector('.cx-eyes-closed'),
      mouth: !!s.querySelector('.cx-mouth'), filter: /<filter|filter=/.test(ser), hat: !!s.querySelector('[class*="cx-fc-hat-"]'), special: sp, hash: hash(ser) };
  }
  const mk = AVATAR_CHARACTERS.find(c => c.id === 'marksman');
  out.hazmat = { kind: mk.kind, glow: AVATAR_GLOW.marksman, hash: hash(drawn('marksman').ser) };
  /* the inspector: the shirt is the first lit shape in his body */
  { const { s } = drawn('detective'); const body = s.querySelector('.cx-body path'); out.inspector = { shirt: stops(s, body), hat: !!s.querySelector('.cx-fc-hat-cowboy'), parts: parts(s) }; }
  { const { s } = drawn('hacker'); out.dispatcher = { shirt: stops(s, s.querySelector('.cx-body path')) }; }
  for(const id of ['clown', 'hive']){ const { s, ser } = drawn(id); out.strobe[id] = { hash: hash(ser), parts: parts(s) }; }
  /* the drone in a 340px coin, a unit is 10px */
  { const box = document.createElement('div'); box.style.cssText = 'position:fixed;left:0;top:0;width:340px;height:340px;border-radius:50%;overflow:hidden';
    const sv = buildAvatarCharSVG('ronin'); sv.style.cssText = 'width:100%;height:100%;display:block'; box.appendChild(sv); document.body.appendChild(box);
    await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
    const R = e => { const b = e.getBoundingClientRect(); return [b.left, b.top, b.right, b.bottom]; };
    const drone = sv.querySelector('.cx-fx-fchover'), head = sv.querySelector('.cx-head');
    /* the hair's top: the highest point of the head's own shapes (not its goggles' antenna) */
    const hairTop = Math.min(...[...head.querySelectorAll('path')].filter(p => /url\(/.test(p.getAttribute('fill') || '') || p.getAttribute('fill') === '#1E140C').map(p => p.getBoundingClientRect().top));
    const d = drone ? R(drone) : null;
    const corners = d ? [[d[0], d[1]], [d[2], d[1]], [d[0], d[3]], [d[2], d[3]]] : [];
    out.drone = d && { box: d.map(v => Math.round(v)), hairTop: Math.round(hairTop), gapUnits: +((hairTop - d[3]) / 10).toFixed(2),
      worst: +Math.max(...[[ (d[0] + d[2]) / 2, d[1] ], [d[0], (d[1] + d[3]) / 2], [d[2], (d[1] + d[3]) / 2]].map(([x, y]) => Math.hypot(x - 170, y - 170) / 170)).toFixed(3) };
    box.remove(); }
  /* F: check-b327z15 N's measure, here in Fire Code, on the challenge characters */
  out.specials = { bad: [], ok: [], kinds: {} };
  for(const id of ['detective', 'masked', 'poseidon', 'clown', 'valkyrie', 'marksman', 'astronaut', 'hacker', 'timekeeper', 'ronin', 'hive']){
    const el = document.createElement('div'); el.className = 'profile-hero-avatar __n';
    el.style.cssText = 'position:fixed;left:0;top:0;width:160px;height:160px';
    const svg = buildAvatarCharSVGSafe(id); el.appendChild(svg); document.body.appendChild(el); el.classList.add('char-live');
    await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
    out.specials.kinds[id] = (AVATAR_CHARACTERS.find(c => c.id === id) || {}).kind;
    if(!charHasSpecial(el)){ out.specials.bad.push(id + ' none'); el.remove(); continue; }
    const before = new Set(svg.getAnimations({ subtree: true }));
    charSpecialBusyUntil = 0;
    const t0 = Date.now();
    playCharSpecial(el);
    /* the call's own time comes off: on a loaded machine it alone ran past N's 60ms */
    const spent = Date.now() - t0, planned = charSpecialBusyUntil - 400 - t0;
    let end = 0;
    svg.getAnimations({ subtree: true }).forEach(a => { if(before.has(a)) return; const e = a.effect.getComputedTiming().endTime; if(isFinite(e)) end = Math.max(end, e); });
    (end > 400 && planned >= end - 5 && planned <= end + 60 + spent ? out.specials.ok : out.specials.bad).push(id + ' ' + Math.round(planned) + '/' + Math.round(end) + ' (+' + spent + ')');
    el.__charSpecial = null; el.classList.remove('char-special'); el.remove();
  }
  return out; }"""
srv, port = rc["serve"]()
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    ctx = br.new_context(viewport={"width": 440, "height": 956}, device_scale_factor=2)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    if BODY is not None:
        pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    pg.add_init_script(INIT)
    pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(3500)
    r = pg.evaluate(SNAP, OLD_KINDS)
    ctx.close(); br.close()
srv.shutdown()
if "--dump" in sys.argv:
    print(json.dumps({k: r[k] for k in ("strobe", "dispatcher")})); sys.exit(0)
chk("the page is the Fire Code class (%s), no page errors (%s)" % (r["cls"], errs[:2]), r["cls"] == "ifc" and not errs, errs)
# A
for i, t in r["three"].items():
    chk("A. %s is a new drawing - %s (%s), not %s - with its own scene and a glow" % (i, t["name"], t["kind"], OLD_KINDS[i]),
        t["kind"] != OLD_KINDS[i] and t["drawer"] and t["scene"] and t["glow"] and t["name"] not in OLD_NAMES, t)
    chk("A. %s has every part a character has (head, eyes, closed eyes, mouth), no svg filter, and a special that draws (%d parts)" % (i, t["special"]),
        t["kind"] != OLD_KINDS[i] and t["hasHead"] and t["eyes"] and t["closed"] and t["mouth"] and not t["filter"] and t["special"] > 10, t)
names = [t["name"] for t in r["three"].values()]
chk("A. none of the three carries a name he turned down (%s), and the three are three different names" % names, not set(names) & set(OLD_NAMES) and len(set(names)) == 3, names)
sp, hz = r["three"]["astronaut"], r["hazmat"]
chk("A. the hazmat monster is not a second suited person: no hat, not the Hazmat's drawing, kind or colour (%s / %s)" % (sp["glow"], hz["glow"]),
    sp["kind"] != OLD_KINDS["astronaut"] and not sp["hat"] and sp["hash"] != hz["hash"] and sp["kind"] != hz["kind"] and (sp["glow"] or "").lower() != (hz["glow"] or "").lower(), (sp, hz))
# B
def hue_sat(h):
    h = h.lstrip("#"); rr, gg, bb = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)); hh, ll, ss = colorsys.rgb_to_hls(rr, gg, bb); return hh * 360, ss, ll
shirt = r["inspector"]["shirt"]; hs = hue_sat(shirt[1]) if len(shirt) > 1 and shirt[1].startswith("#") else (0, 0, 0)
chk("B. the inspector's shirt is blue (base %s: hue %d, saturation %.2f)" % (shirt[1] if len(shirt) > 1 else shirt, hs[0], hs[1]), 195 <= hs[0] <= 240 and hs[1] >= .35, shirt)
chk("B. ...and he still wears his cowboy hat", r["inspector"]["hat"], r["inspector"])
# C
dr = r["drone"]
chk("C. the drone flies clear of his head: %.2f units of air between it (downlight and all) and his hair (at least 3)" % (dr["gapUnits"] if dr else -99), dr and dr["gapUnits"] >= 3, dr)
chk("C. ...and the whole drone is inside the coin (worst edge at %.3f of the radius)" % (dr["worst"] if dr else 9), dr and dr["worst"] <= 1.0, dr)
# D
for i in ("clown", "hive"):
    now, was = r["strobe"][i], BEFORE[i]
    chk("D. %s is redrawn (%s, was %s)" % (i, now["hash"], was["hash"]), now["hash"] != was["hash"], now)
    added, lost = sorted(set(now["parts"]) - set(was["parts"])), sorted(set(was["parts"]) - set(now["parts"]))
    chk("D. ...with exactly the parts it had: nothing added (%s), nothing lost (%s)" % (added, lost), now["hash"] != was["hash"] and not added and not lost, now["parts"])
# E
def lum(h):
    h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]; c = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]
ds = r["dispatcher"]["shirt"]; base = ds[1] if len(ds) > 1 else ds[0]
chk("E. the dispatcher's shirt reads against his sky: base %s, luminance %.3f (was %.3f)" % (base, lum(base), lum(BEFORE["hacker"]["shirt"])), lum(base) >= lum(BEFORE["hacker"]["shirt"]) * 1.5, ds)
# F
spc = r["specials"]; newk = all(spc["kinds"].get(i) != k for i, k in OLD_KINDS.items())
chk("F. in Fire Code all %d challenge characters' specials end with their own last part, the three new kinds among them (%s)" % (len(spc["ok"]) + len(spc["bad"]), spc["bad"]),
    newk and not spc["bad"] and len(spc["ok"]) == 11, spc)
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
