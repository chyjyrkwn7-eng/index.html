"""Build 384, round 6: Hazmat, the showpiece, without the tape, the placard or the walk across the screen.
Madison: "The hazmat one I love the concept but it needs to be better. I don't like the caution tape and I don't think I like
the hazmat placard across the screen? I don't know if I like the hazmat guy coming across the screen either? Maybe it's the
spray? Idk just get on this and make it better."
In the Fire Code class (iPhone 17 Pro Max 440x956 and iPad 834x1194), the ufo rung's effect on a 100% box, every animation
paused and seeked, read off the page:
 (D1) NO TAPE, NO PLACARD: the hazard stripe, the scene tape, the 704 placard's quarters and frame, the tag and its ALL CLEAR
      twin are not drawn at all (no such sprite, no repeat-x band in any layer), and neither are they in the tile or the still;
 (D2) THE RESPONDER DOES NOT CROSS: he is under the screen's foot before he rises, comes up into his corner, and his x does not
      move from there to the end of the decon;
 (D3) THE JET: round 5's spray was a fan of dots. The new sprite is a solid white core with a body round it - its opaque area
      (alpha >= .5) is at least 1.8x the old one's, and its body (alpha >= .16) at least 1.5x;
 (D4) THE SURGE where the placard slammed: a flash that jumps on the slam (none just before), a shockwave ring from the box's
      middle, and at least eight sparks thrown off the BOX'S edge (not off a placard on the floor) that fly outward;
 (D5) the all clear still goes off (a flash after the decon, the pop of the number) - the beats the other gates hold;
 (D6) the beats the sound is scored on still hold: the sound renders, its loudest moment on the surge or the all clear.
Run:  python3 tools/check-b384-hzdecon.py   (--against OLD/index.html must FAIL)"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b384-hazmat.py")).read().split("\nres = {}")[0]
G = {"__file__": os.path.join(HERE, "check-b384-hazmat.py"), "__name__": "b384hzdecon"}
exec(src, G)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:500], flush=True)
BEATS = G["BEATS"]; SETUP = G["SETUP"]; SOUND = G["SOUND"]
I = G["G"]   # the hazmat gate's own harness dict (page, init, ifc, g)

MEASURE = r"""() => {
  const X = window.__hz, Z = X.Z, out = {};
  const at = (t, fn) => { X.seek(t); return fn(); };
  const all = () => X.layers.flatMap(l => [...l.querySelectorAll('*')]);
  out.removed = ['stripe', 'quad', 'tag', 'hzTape', 'hzFrame', 'hzSheen', 'hzTagOk'].filter(k => typeof ifxSpr[k] !== 'undefined');
  out.repeatx = all().filter(e => /repeat-x/.test((e.style.background || '') + (e.style.backgroundRepeat || ''))).length;
  const b = X.box, W = X.W, H = X.H;
  /* D2: the responder */
  const suit = X.find('ifx-suit2')[0];
  if(suit){
    out.before = at((Z.walk || 2.95) - .02, () => [Math.round(X.R(suit).t), H, X.eff(suit)]);
    out.after = at((Z.walked || 3.5) + .2, () => [Math.round(X.R(suit).t), Math.round(X.R(suit).b), H, X.eff(suit)]);
    out.xs = [(Z.walked || 3.5) + .2, Z.aim || 3.82, (Z.spray || 3.84) + .5, Z.sprayEnd || 5].map(t => at(t, () => Math.round(X.R(suit).cx)));
  }
  /* D4: the surge */
  const sparks = X.find('ifx-hzspark');
  const ex = { l: b.l - b.w * .25, r: b.r + b.w * .25, t: b.t - b.h * .25, b: b.b + b.h * .25 };
  out.sparks = sparks.length;
  out.sparksNear = at(Z.slam + .03, () => sparks.filter(e => { const r = X.R(e); return X.eff(e) > .3 && r.cx >= ex.l && r.cx <= ex.r && r.cy >= ex.t && r.cy <= ex.b; }).length);
  out.sparksOut = at(Z.slam + .4, () => sparks.filter(e => { const r = X.R(e); return Math.hypot(r.cx - b.cx, r.cy - b.cy) > Math.max(b.w, b.h) * .55; }).length);
  const flashes = all().filter(e => /radial-gradient/.test(e.style.background || '') && e.style.width === W + 'px' && e.style.height === H + 'px');
  out.flash = flashes.map(e => [Math.round(at(Z.slam - .02, () => X.eff(e)) * 100) / 100, Math.round(at(Z.slam + .06, () => X.eff(e)) * 100) / 100]);
  out.flashClear = flashes.map(e => [Math.round(at(Z.clear - .02, () => X.eff(e)) * 100) / 100, Math.round(at(Z.clear + .06, () => X.eff(e)) * 100) / 100]);
  const rings = X.find('ifx-ring#B4F03A').concat(X.find('ifx-ring#FFFFFF'), X.find('ifx-ring#FFD54A'));
  out.ringAtSlam = rings.filter(e => { const r = X.R(e); return at(Z.slam + .1, () => X.eff(e)) > .5 && Math.hypot(r.cx - b.cx, r.cy - b.cy) < Math.max(b.w, b.h) * .1; }).length;
  out.ringAtSlam = at(Z.slam + .1, () => rings.filter(e => X.eff(e) > .4 && Math.hypot(X.R(e).cx - b.cx, X.R(e).cy - b.cy) < Math.max(b.w, b.h) * .12).length);
  return out;
}"""
JET = r"""async () => {
  const key = ['ifx-hzspray2', 'ifx-hzspray'].find(k => hfxSprites[k]);
  for(let i = 0; i < 60 && !(hfxSprites[key] && hfxSprites[key].png); i++) await new Promise(r => setTimeout(r, 100));
  const sp = hfxSprites[key], u = (sp.png || sp.svg || '').replace(/^url\(["']?/, '').replace(/["']?\)$/, '');
  const img = new Image(); img.src = u; try{ await img.decode(); }catch(e){}
  const c = document.createElement('canvas'); c.width = 400; c.height = 200; const x = c.getContext('2d'); x.drawImage(img, 0, 0, 400, 200);
  const d = x.getImageData(0, 0, 400, 200).data; let solid = 0, body = 0;
  for(let i = 3; i < d.length; i += 4){ if(d[i] >= 128) solid++; if(d[i] >= 40) body++; }
  return { key, solid, body };
}"""
res = {}
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=I["g"]["CHROME"])
    errs_all = []
    for dev, (w, h) in (("phone", (440, 956)), ("ipad", (834, 1194))):
        ctx, pg, errs = I["page"](br, I["init"](I["ifc"]))
        pg.set_viewport_size({"width": w, "height": h}); pg.wait_for_timeout(400)
        info = pg.evaluate(SETUP, BEATS)
        m = pg.evaluate(MEASURE)
        extra = {}
        if dev == "phone":
            extra["jet"] = pg.evaluate(JET)
            extra["tile"] = pg.evaluate("""() => { const t = buildHundoFxTile('ufo').querySelector('svg'), s = buildHundoFxStill('ufo'); const h = (t ? t.outerHTML : '') + (s ? s.outerHTML : '');
              return { len: h.length, yellowBand: /#F5C518/i.test(h) && /width="160" height="4"/.test(h), placard: ['#E3262E', '#1F6FD1', '#F4F4F2'].filter(c => h.toUpperCase().indexOf(c) >= 0).length }; }""")
            extra["sound"] = pg.evaluate(SOUND)
        res[dev] = dict(info=info, m=m, **extra)
        errs_all += errs
        ctx.close()
    br.close()
P = res["phone"]
chk("the page is the Fire Code class and plays ifxHazmat (%s)" % P["info"]["build"], P["info"]["cls"] == "ifc" and P["info"]["build"] == "ifxHazmat", P["info"])
for dev in ("phone", "ipad"):
    R = res[dev]; m = R["m"]
    chk("(D1) %s: no stripe, tape, placard or tag sprite is drawn any more (still defined: %s) and no repeat-x band in a layer (%s)" % (dev, m["removed"], m["repeatx"]), not m["removed"] and m["repeatx"] == 0, m)
    b, a, xs = m.get("before"), m.get("after"), m.get("xs") or [0, 1e9]
    chk("(D2) %s: the responder is under the screen's foot before he comes up (top %s of %s), in his corner after (%s) and his x does not move (%s)" % (dev, b and b[0], b and b[1], a, xs),
        b and b[0] >= b[1] - 2 and a and a[0] < a[2] and a[3] > .9 and max(xs) - min(xs) <= 3, m)
    chk("(D4) %s: eight+ sparks thrown off the box's edge on the surge (%s of %s start at the box, %s fly out of it)" % (dev, m["sparksNear"], m["sparks"], m["sparksOut"]), m["sparks"] >= 8 and m["sparksNear"] >= 8 and m["sparksOut"] >= 6, m)
    fl = m["flash"]
    chk("(D4) %s: a flash that jumps on the surge (%s) and a ring from the box's middle (%s)" % (dev, fl, m["ringAtSlam"]), any(f[0] < .1 and f[1] > .6 for f in fl) and m["ringAtSlam"] >= 1, m)
    fc = m["flashClear"]
    chk("(D5) %s: the all clear still goes off (a flash after it: %s)" % (dev, fc), any(f[0] < .1 and f[1] > .5 for f in fc), fc)
j = P["jet"]
print("jet", j)
chk("(D3) the jet is a solid body, not a fan of dots (opaque area %s px, body %s px)" % (j["solid"], j["body"]), j["key"] == "ifx-hzspray2" and j["solid"] >= 6500 and j["body"] >= 20000, j)
t = P["tile"]
chk("(D1) the tile and the still draw no placard colours and no hazard band (%s)" % t, t["len"] > 300 and t["placard"] == 0 and not t["yellowBand"], t)
snd = P["sound"]
chk("(D6) the sound renders in Fire Code, not silent, not clipping (peak %.2f)" % snd["peak"], snd["cls"] == "ifc" and .05 < snd["peak"] < 1 and snd["len"] >= 6.5, snd)
chk("(D6) ...its loudest moment on the surge or the all clear (at %.2fs)" % snd["loudestAt"], 1.69 <= snd["loudestAt"] <= 2.04 or 5.1 <= snd["loudestAt"] <= 5.55, snd)
chk("no page errors (%s)" % errs_all[:2], not errs_all, errs_all)
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
