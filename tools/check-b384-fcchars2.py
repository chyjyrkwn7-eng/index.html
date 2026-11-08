#!/usr/bin/env python3
"""Build 384, round 5: Madison's review of the Fire Code characters, drawn in the Fire Code class only.

  "I think the characters (every single one of them) could be touched up ..."
  "Inspector is cool ... He also looks pale, and too white, make him better, shirt needs to be navy too."
  "The extinguisher character, I don't like it at all, make that something else.."
  "Hydrant character is an absolute no as well. Change the character."
  "I don't like the secret flare characters from ifc, I love the academy ones though, we need to follow the academy
   theme but just come up with new ones.."

  A. the four secret flares are Nebula, Quasar, Pulsar and Solstice: four new drawings (no helmet or hat, no human skin),
     each with the parts every character has, no svg filter, a glow that is the one the character table carries; Nebula's
     gas is the three flare colours (red, orange, yellow)
  B. the extinguisher and the hydrant are gone: the valkyrie id is Pyrotech and the timekeeper id Salamander, new kinds
     with their own scene and glow, no filter, the same ids
  C. the inspector's shirt is navy (dark and blue) and his face is not pale (darker than the light skin tone it was)
  D. every Fire Code character draws without an svg filter and has a head, eyes, closed eyes and a mouth
Every check fails on the build before:  python3 tools/check-b384-fcchars2.py --against OLD/index.html
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
seed = dict(rc["SEED"]); seed.update(seenClassTip=True, novaMet=99, publicId="tst4fc8chars2", classes=["academy", "ifc"])
S = json.dumps(json.dumps(seed))
INIT = ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
        "localStorage.setItem('class26e.drill.v1',%s);localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));"
        "localStorage.setItem('class26e.greet.ifc','done');['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted','class26e.a2hs'].forEach(k=>localStorage.setItem(k,'1'));"
        "localStorage.setItem('class26e.ifc.drill.v1',%s);}catch(e){}") % (S, S)
SNAP = r"""() => {
  document.getElementById('splashscreen')?.remove();
  const hash = s => { let h = 2166136261; for(let i = 0; i < s.length; i++){ h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0).toString(16); };
  const drawn = id => { const s = drawAvatarCharSVG(id), uid = s.getAttribute('data-cx-uid'); return { s, ser: new XMLSerializer().serializeToString(s).split(uid).join('U') }; };
  const stops = (s, n) => { const f = (n && n.getAttribute('fill')) || ''; const m = f.match(/url\(#([^)]+)\)/); const g = m && s.querySelector('[id="' + m[1] + '"]'); return g ? [...g.querySelectorAll('stop')].map(x => x.getAttribute('stop-color')) : [f]; };
  const out = { cls: window.NOVA_CLASS, ch: {}, all: {} };
  const info = id => {
    const def = AVATAR_CHARACTERS.find(c => c.id === id); if(!def) return null;
    const { s, ser } = drawn(id);
    return { kind: def.kind, name: AVATAR_DISPLAY_NAME[id], glow: AVATAR_GLOW[id], lookGlow: (IFC_CHAR_LOOK[id] || [])[2], scene: !!(IFC_BACKDROP && IFC_BACKDROP[def.kind]),
      head: !!s.querySelector('.cx-head'), eyes: !!s.querySelector('.cx-eyes'), closed: !!s.querySelector('.cx-eyes-closed'), mouth: !!s.querySelector('.cx-mouth'),
      filter: /<filter|filter=/.test(ser), hat: !!s.querySelector('[class*="cx-fc-hat-"]'), hash: hash(ser),
      grads: [...s.querySelectorAll('radialGradient stop')].map(x => (x.getAttribute('stop-color') || '').toUpperCase()) };
  };
  for(const id of ['voidwalker', 'umbra', 'singularity', 'genesis', 'valkyrie', 'timekeeper']) out.ch[id] = info(id);
  { const { s } = drawn('detective'); const body = s.querySelector('.cx-body path'); out.shirt = stops(s, body);
    const face = [...s.querySelectorAll('.cx-head path')].find(p => /url\(/.test(p.getAttribute('fill') || '')); out.face = stops(s, face); }
  for(const c of AVATAR_CHARACTERS){ if(c.retired || c.legacy || !IFC_CHAR_LOOK[c.id]) continue; const t = info(c.id); if(t) out.all[c.id] = { filter: t.filter, head: t.head, eyes: t.eyes, closed: t.closed, mouth: t.mouth }; }
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
    r = pg.evaluate(SNAP)
    ctx.close(); br.close()
srv.shutdown()
def lum(h):
    h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]; c = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]
chk("the page is the Fire Code class (%s), no page errors (%s)" % (r["cls"], errs[:2]), r["cls"] == "ifc" and not errs, errs)
C = r["ch"]
# A
want = {"voidwalker": "Nebula", "umbra": "Quasar", "singularity": "Pulsar", "genesis": "Eclipse"}
names = {i: C[i]["name"] for i in want}
chk("A. the four secrets are Nebula, Quasar, Pulsar and Eclipse (round 7: Eclipse replaced Solstice) (%s)" % names, names == want, names)
chk("A. each is a new drawing with a scene, and no helmet or hat (kinds %s)" % {i: C[i]["kind"] for i in want},
    all(C[i]["kind"].startswith("fc") and not C[i]["kind"].startswith("fcsq") and C[i]["scene"] and not C[i]["hat"] for i in want), C)
chk("A. the four are four different drawings", len({C[i]["hash"] for i in want}) == 4)
chk("A. each has a head, eyes, closed eyes and a mouth, and no svg filter", all(C[i]["head"] and C[i]["eyes"] and C[i]["closed"] and C[i]["mouth"] and not C[i]["filter"] for i in want), C)
chk("A. each one's glow is the character table's own (%s)" % {i: (C[i]["glow"], C[i]["lookGlow"]) for i in want}, all(C[i]["glow"] and C[i]["glow"] == C[i]["lookGlow"] for i in want))
g = set(C["voidwalker"]["grads"])
chk("A. Nebula's gas is three colours: red, orange and yellow (%s)" % sorted(g), {"#EF4444", "#F97316", "#FACC15"} <= g, sorted(g))
# B
chk("B. the valkyrie id is Undercover and the timekeeper id Pump Operator (%s, %s) (round 7: they replaced Pyrotech and Salamander)" % (C["valkyrie"]["name"], C["timekeeper"]["name"]),
    C["valkyrie"]["name"] == "Undercover" and C["timekeeper"]["name"] == "Pump Operator", C)
chk("B. ...new kinds (%s, %s), each with its own scene and glow, no svg filter, no hat of the fire service" % (C["valkyrie"]["kind"], C["timekeeper"]["kind"]),
    C["valkyrie"]["kind"] == "fcundercover" and C["timekeeper"]["kind"] == "fcpump" and all(C[i]["scene"] and C[i]["glow"] and not C[i]["filter"] and C[i]["head"] and C[i]["eyes"] and C[i]["closed"] and C[i]["mouth"] for i in ("valkyrie", "timekeeper")), C)
# C
sh = r["shirt"]; base = sh[1] if len(sh) > 1 else sh[0]
rr, gg, bb = (int(base.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)); hh, ll, ss = colorsys.rgb_to_hls(rr, gg, bb)
chk("C. the inspector's shirt is navy: base %s, hue %d, saturation %.2f, luminance %.3f (dark, under .05)" % (base, hh * 360, ss, lum(base)), 205 <= hh * 360 <= 240 and ss >= .4 and lum(base) < .05, sh)
fb = r["face"][1] if len(r["face"]) > 1 else r["face"][0]
chk("C. ...and his face is not pale: base %s, luminance %.3f (the light tone it was is .50; under .42)" % (fb, lum(fb)), lum(fb) < .42, r["face"])
# D
bad = [i for i, v in r["all"].items() if v["filter"] or not (v["head"] and v["eyes"] and v["closed"] and v["mouth"])]
chk("D. every character Fire Code draws itself has its parts and no svg filter (%d checked, bad: %s)" % (len(r["all"]), bad), len(r["all"]) >= 14 and not bad, bad)
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
