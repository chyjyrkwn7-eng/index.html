#!/usr/bin/env python3
"""Build 384, round 8 (r3-chars): Madison's third look at the Fire Code characters (drawn in the Fire Code class only).

  "The undercover one, not a fan.. try something else."      -> valkyrie is the Lookout, a fire lookout tower with a face (fclookout)
  "I don't like the pump operator, try something else."      -> timekeeper is the Smoke Alarm, a round alarm with its vent ring (fcsmoke)
  "Not sure what happened to the sprinkler head, try again there or revert."  -> hive: a brass-bodied pendent sprinkler, face on the body
  "Pulsar, try something else."                               -> singularity: a dark star, two narrow opposed beams with a wake, a pulse profile
  "Pulsar character banner is not it and doesn't go with the rest.."  -> flare_horizon follows the new Pulsar, on the Eclipse banner's ground

  python3 tools/check-b384-r3-chars.py [--against OLD/index.html]     (every line must FAIL on c8143d5)
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
seed = dict(rc["SEED"]); seed.update(seenClassTip=True, novaMet=99, publicId="tst4fc8chars4", classes=["academy", "ifc"])
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
  const lum = h => { h = (h || '#000000').replace('#', ''); if(h.length !== 6) return 1; const c = [0, 2, 4].map(i => parseInt(h.substr(i, 2), 16) / 255).map(v => v <= .04045 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4)); return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]; };
  const out = {};
  out.names = Object.fromEntries(['valkyrie', 'timekeeper', 'hive', 'singularity'].map(id => [id, [AVATAR_DISPLAY_NAME[id], AVATAR_CHARACTERS.find(c => c.id === id).kind]]));
  /* the Pulsar */
  { const s = mount('singularity');
    const stops = n => { const m = (n.getAttribute('fill') || '').match(/url\(#([^)]+)\)/); const g = m && s.querySelector('[id="' + m[1] + '"]'); return g ? [...g.querySelectorAll('stop')].map(x => x.getAttribute('stop-color')) : []; };
    const head = [...s.querySelectorAll('.cx-head circle')].filter(c => /^url\(/.test(c.getAttribute('fill') || '')).sort((a, b) => b.getAttribute('r') - a.getAttribute('r'))[0];
    const hc = { x: +head.getAttribute('cx'), y: +head.getAttribute('cy'), r: +head.getAttribute('r') };
    const ls = stops(head).map(lum);
    const nums = d => (d.match(/-?[\d.]+/g) || []).map(Number);
    /* a wedge is M p1 L p2 L p3 L p4 Z: p1/p4 its start (the pole), p2/p3 its far end */
    const geo = p => { const n = nums(p.getAttribute('d')); const sx = (n[0] + n[6]) / 2, sy = (n[1] + n[7]) / 2, ex = (n[2] + n[4]) / 2, ey = (n[3] + n[5]) / 2;
      return { op: p.getAttribute('opacity'), x0: sx, y0: sy, x1: ex, y1: ey, L: Math.hypot(ex - sx, ey - sy), w0: Math.hypot(n[0] - n[6], n[1] - n[7]), w1: Math.hypot(n[2] - n[4], n[3] - n[5]) }; };
    const beams = [...s.querySelectorAll('.cx-fx-fcpulse path')].map(geo);
    const tips = beams.filter(b => !b.op);
    /* the two white-hot cores: their start points lie on the head's axis and on opposite sides of the centre */
    const f = s.querySelector('.cx-fx-flare circle:nth-of-type(2)'); const fl = f ? { x: +f.getAttribute('cx'), y: +f.getAttribute('cy') } : null;
    const wake = [...s.querySelectorAll('.cx-fx-sqlight')].filter(g => !g.matches('.cx-fx-fcpulse, .cx-fx-flare') && g.querySelectorAll(':scope > path').length >= 4).length;
    const prof = [...s.querySelectorAll('.cx-body path')].filter(p => (p.getAttribute('d') || '').split('L').length > 15 && p.getAttribute('stroke') === '#7FC8FF').length;
    const white = [...s.querySelectorAll('.cx-head circle')].filter(c => +c.getAttribute('r') > 5 && /^#(F|E)/i.test(c.getAttribute('fill') || '')).length;
    out.pulsar = { head: hc, darkest: Math.min(...ls), lightest: Math.max(...ls), beams: beams.length, narrow: tips.filter(b => b.w1 < 3.6 && b.L > 18).length, tips, flare: fl, wake, prof, whiteDisc: white,
      brows: !!s.querySelector('.cx-head path[d^="M14.6 17.4"]'), sweepClass: !!s.querySelector('.cx-fx-fcpulse') };
    delete out.pulsar.beamsRaw;
    s.remove(); }
  /* the banner */
  { const ids = ['flare_horizon', 'flare_genesis'];
    out.ban = {};
    ids.forEach(id => { const art = BANNER_ART[id]('t-'); const arr = Array.isArray(art) ? art : [];
      const all = arr.map(l => (l.svg || '')).join('');
      out.ban[id] = { n: arr.length, cls: arr.map(l => l.cls || ''), all, still: bannerStaticSVG(id) || '' }; });
    const g = out.ban.flare_horizon; const spin = (() => { const a = BANNER_ART.flare_horizon('t-'); return a.find(l => l.cls === 'bl-spin'); })();
    out.spin = spin ? { svg: spin.svg } : null;
  }
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
import math, re
chk("no page errors (%s)" % errs[:2], not errs, errs)
N = r["names"]
chk("the four are Lookout (fclookout), Smoke Alarm (fcsmoke), Sprinkler Head (fcsprinkler3) and Pulsar (fcpulsar) (%s)" % N,
    N["valkyrie"] == ["Lookout", "fclookout"] and N["timekeeper"] == ["Smoke Alarm", "fcsmoke"] and N["hive"] == ["Sprinkler Head", "fcsprinkler3"] and N["singularity"] == ["Pulsar", "fcpulsar"], N)
P = r["pulsar"]
chk("Pulsar's head is a dark sphere like its squad's, not a white star (darkest stop %.4f, lightest %.3f; no pale disc: %s)" % (P["darkest"], P["lightest"], P["whiteDisc"]),
    P["darkest"] < .005 and P["lightest"] < .2 and P["whiteDisc"] == 0, P)
chk("...two narrow beams (%s white-hot cores under 3.6 units wide at the far end and over 18 long) with no brows or face-star left over (%s)" % (P["narrow"], P["brows"]), P["narrow"] >= 2 and not P["brows"], P)
t = P["tips"]; cx, cy = P["head"]["x"], P["head"]["y"]
ang = [math.degrees(math.atan2(a["y0"] - cy, a["x0"] - cx)) for a in t] if len(t) >= 2 else []
opp = len(ang) == 2 and abs(((ang[0] - ang[1]) % 360) - 180) < 4
chk("...the beams are opposed through the head's centre (their starts are %s degrees apart) on a tilted axis (%s)" % ([round(a, 1) for a in ang], [round(a % 180, 1) for a in ang]),
    opp and 5 < abs(ang[0] % 180) < 85 or opp and 95 < abs(ang[0] % 180) < 175, P)
f = P["flare"]
dist = abs(math.hypot(f["x"] - cx, f["y"] - cy) - P["head"]["r"]) if f else 99
onaxis = min(abs(((math.degrees(math.atan2(f["y"] - cy, f["x"] - cx)) - a) + 180) % 360 - 180) for a in ang) if f and ang else 99
chk("...the flare is the north pole's lamp: on the rim (%.2f off) and on the beam's axis (%.1f degrees)" % (dist, onaxis), f and dist <= .5 and onaxis < 3, P)
chk("...each beam leaves a wake (%s fan groups) and the chest carries the pulse profile (%s stacked lines)" % (P["wake"], P["prof"]), P["wake"] >= 1 and P["prof"] >= 3, P)
B = r["ban"]["flare_horizon"]; E = r["ban"]["flare_genesis"]
chk("the Pulsar banner turns the star as one body (a bl-spin layer holding the beams, the bands and the flare's bead) (%s)" % B["cls"],
    r["spin"] and 'bmN' in r["spin"]["svg"] and 'bmS' in r["spin"]["svg"] and 'bead' in r["spin"]["svg"] and r["spin"]["svg"].count("rotate(") >= 5, B["cls"])
chk("...it stands on the Eclipse banner's ground: the same hills and pines, a lake with the star in it, the cool rim on the ridge, the shimmer (hill/lake gradients, a 'bl-shimmer' layer)",
    all(k in B["all"] for k in ("hill", "lake")) and "bl-shimmer" in B["cls"] and len(re.findall(r"M\-10 140 Q40 118", B["all"])) >= 2 and "bl-rise" in B["cls"], B["cls"])
chk("...and it has no leftover of the old Pulsar: no face (no slanted eyes), no field lines, no ice spires, no orbiting bead on a dotted ring",
    'rotate(13' not in B["all"] and 'stroke-dasharray="1.4 4"' not in B["all"] and 'field' not in B["all"] and 'spire' not in B["all"] and 'rx="3.5" ry="6.4"' not in B["all"], B["all"][:100])
chk("...one star, one pair of beams: no stray pieces (a single dark ball, a single flare bead) and no svg filter",
    B["all"].count('url(#t-ball)') == 1 and B["all"].count('url(#t-bead)') == 1 and "<filter" not in B["all"] and B["n"] <= 14, (B["n"], B["all"].count('url(#t-ball)')))
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
