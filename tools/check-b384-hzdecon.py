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
 (D4) THE SURGE where the placard slammed: ROUND 2 - calmed to ONE thing, a shockwave ring from the box's middle (and the camera
      kick); the flash that jumped on the slam and the ten sparks thrown off the box's edge are gone (it had nine things going at once);
 (D5) the all clear still goes off - ROUND 2: as a lime ring out of the box and rays turning behind it (the flashes, the second ring and
      the bloom are gone), the pop of the number - the beats the other gates hold;
 (D7) [ROUND 3] THE DECON READS: "I'm also not really sure what the guy is spraying to be honest? Is that something hazmat guys do?" The
      responder holds a decon NOZZLE FED BY A HOSE - the blue hose is joined to the nozzle's coupling at every moment (within 4px) and runs
      off the bottom of the screen; the stream leaves the nozzle's mouth (within 4px);
 (D3) [ROUND 3] the stream is water, not a cone of mist: a band with an edge (under .45 of the sprite's height 70% of the way down it) and a
      solid body (round 6's jet is the bar this keeps clear of: key ifx-hzspray3);
 (D8) [ROUND 3] the FOAM carries the film off: a column of suds at the wash's edge, the box's height, on the box mid-pass; suds on the glass
      behind it after the pass and gone before the all clear;
 (D9) [ROUND 3] a plain DECON label in the decon beat only (not in the alert, the surge or after the all clear), no border, no shadow;
 (D10) [ROUND 3] the little that came back: a sparkle sweep at the all clear (at least four glints, none before it), a lamp glow at each
      beacon in the alert, and a second, smaller ring behind the first in the spill;
 (D6) the beats the sound is scored on still hold: the sound renders, its loudest moment on the surge (2.3) or the all clear (4.75).
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
  const ex = { l: b.l - b.w * .6, r: b.r + b.w * .6, t: b.t - b.h * .6, b: b.b + b.h * .6 };
  out.sparks = sparks.length;
  out.sparksNear = at(Z.slam + .03, () => sparks.filter(e => { const r = X.R(e); return X.eff(e) > .3 && r.cx >= ex.l && r.cx <= ex.r && r.cy >= ex.t && r.cy <= ex.b; }).length);
  out.sparksOut = at(Z.slam + .4, () => sparks.filter(e => { const r = X.R(e); return Math.hypot(r.cx - b.cx, r.cy - b.cy) > Math.max(b.w, b.h) * .55; }).length);
  const flashes = all().filter(e => /radial-gradient/.test(e.style.background || '') && e.style.width === W + 'px' && e.style.height === H + 'px');
  out.flash = flashes.map(e => [Math.round(at(Z.slam - .02, () => X.eff(e)) * 100) / 100, Math.round(at(Z.slam + .06, () => X.eff(e)) * 100) / 100]);
  out.flashClear = flashes.map(e => [Math.round(at(Z.clear - .02, () => X.eff(e)) * 100) / 100, Math.round(at(Z.clear + .06, () => X.eff(e)) * 100) / 100]);
  const rings = X.find('ifx-ring#B4F03A').concat(X.find('ifx-ring#FFFFFF'), X.find('ifx-ring#FFD54A'));
  out.ringInfo = [rings.length, at(Z.slam + .1, () => rings.map(e => [Math.round(X.eff(e) * 100) / 100, Math.round(Math.hypot(X.R(e).cx - b.cx, X.R(e).cy - b.cy))]))];
  const clearRings = rings.filter(e => true);
  out.ringAtClear = at(Z.clear + .2, () => rings.filter(e => X.eff(e) > .3 && Math.hypot(X.R(e).cx - b.cx, X.R(e).cy - b.cy) < Math.max(b.w, b.h) * .12).length);
  out.raysAtClear = at(Z.clear + .3, () => X.find('ifx-hzrays').filter(e => X.eff(e) > .3).length);
  /* (r3) the readable decon: a hose joined to the nozzle and running off the screen, a stream from the nozzle's mouth, foam at the wash's
     edge and suds behind it, a plain DECON label, a sparkle at the all clear, a lamp at each beacon, a second smaller ring in the spill */
  const arm = X.find('ifx-hzarm3')[0], hose = X.find('ifx-hzhose')[0], sp3 = X.find('ifx-hzspray3')[0];
  const pr = (el, l, t) => { const p = document.createElement('i'); p.style.cssText = 'position:absolute;left:' + l + ';top:' + t + ';width:0;height:0;'; el.appendChild(p); return p; };
  const pt = p => { const r = p.getBoundingClientRect(); return [r.left, r.top]; };
  out.hasHose = !!(arm && hose && sp3);
  if(arm && hose){
    const Gm = IFX_HZ_ARM, pa = pr(arm, (Gm.hc.x / 230 * 100) + '%', (Gm.hc.y / 110 * 100) + '%'), ph = pr(hose, '0', '50%'), pe = pr(hose, '100%', '50%');
    out.hose = [Z.walked + .1, Z.aim + .1, Z.spray + .3, (Z.sweep[0] + Z.sweep[1]) / 2, Z.sweep[1] + .2, Z.sprayEnd - .05, Z.lower + .2].map(t => at(t, () => { const a = pt(pa), h = pt(ph), e = pt(pe);
      return { t: Math.round(t * 100) / 100, join: Math.round(Math.hypot(a[0] - h[0], a[1] - h[1]) * 10) / 10, endY: Math.round(e[1]), vis: Math.round(X.eff(hose) * 100) / 100 }; }));
    out.H = H; [pa, ph, pe].forEach(p => p.remove());
  }
  if(arm && sp3){
    const Gm = IFX_HZ_ARM, pn = pr(arm, (Gm.nz.x / 230 * 100) + '%', (Gm.nz.y / 110 * 100) + '%'), pm = pr(sp3, '100%', '50%');
    out.mouth = [Z.sweep[0] + .3, Z.sweep[1] - .1, Z.sweep[2]].map(t => at(t, () => { const a = pt(pn), m = pt(pm); return Math.round(Math.hypot(a[0] - m[0], a[1] - m[1]) * 10) / 10; }));
    [pn, pm].forEach(p => p.remove());
  }
  const foam = X.find('ifx-hzfoam')[0], suds = X.find('ifx-hzsuds')[0];
  out.foam = foam ? at((Z.sweep[0] + Z.sweep[1]) / 2, () => { const r = X.R(foam); return { vis: Math.round(X.eff(foam) * 100) / 100, cx: Math.round(r.cx), bl: Math.round(b.l), br: Math.round(b.r), h: Math.round(r.h), bh: Math.round(b.h) }; }) : null;
  out.suds = suds ? [Z.sweep[1] + .05, Z.sprayEnd - .1, Z.clear - .02, Z.clear + .1].map(t => at(t, () => Math.round(X.eff(suds) * 100) / 100)) : null;
  const chips = () => all().filter(e => !e.children.length && /^DECON$/.test((e.textContent || '').trim()));
  out.chip = [.5, Z.slam, Z.walk + .5, (Z.sweep[0] + Z.sweep[1]) / 2, Z.sprayEnd - .1, Z.clear + .1].map(t => at(t, () => { const c = chips()[0]; return c ? Math.round(X.eff(c) * 100) / 100 : -1; }));
  out.chipLook = chips()[0] ? (() => { const cs = getComputedStyle(chips()[0]); return [cs.borderTopWidth, cs.boxShadow, cs.fontWeight]; })() : null;
  const gl = X.find('ifx-hzglint'); let gmax = 0; for(let d = .1; d < 1; d += .1) gmax = Math.max(gmax, at(Z.clear + d, () => gl.filter(e => X.eff(e) > .3).length));
  out.glints = [gl.length, gmax, at(Z.clear - .05, () => gl.filter(e => X.eff(e) > .05).length)];
  out.lamps = at(.56, () => X.find('ifx-glow#FFB21A').filter(e => X.eff(e) > .3).length);
  out.rings2 = 0; for(let d = .1; d < .5; d += .05) out.rings2 = Math.max(out.rings2, at(Z.slam + d, () => rings.filter(e => X.eff(e) > .1 && Math.hypot(X.R(e).cx - b.cx, X.R(e).cy - b.cy) < Math.max(b.w, b.h) * .12).length));
  out.ringAtSlam = at(Z.slam + .1, () => rings.filter(e => X.eff(e) > .3 && Math.hypot(X.R(e).cx - b.cx, X.R(e).cy - b.cy) < Math.max(b.w, b.h) * .12).length);
  return out;
}"""
JET = r"""async () => {
  const key = ['ifx-hzspray3', 'ifx-hzspray2', 'ifx-hzspray'].find(k => hfxSprites[k]);
  for(let i = 0; i < 60 && !(hfxSprites[key] && hfxSprites[key].png); i++) await new Promise(r => setTimeout(r, 100));
  const sp = hfxSprites[key], u = (sp.png || sp.svg || '').replace(/^url\(["']?/, '').replace(/["']?\)$/, '');
  const img = new Image(); img.src = u; try{ await img.decode(); }catch(e){}
  const c = document.createElement('canvas'); c.width = 400; c.height = 200; const x = c.getContext('2d'); x.drawImage(img, 0, 0, 400, 200);
  const d = x.getImageData(0, 0, 400, 200).data; let solid = 0, body = 0, rows = 0;
  /* a STREAM has an edge: at 30% of the way from the target, the opaque part is a band a fraction of the height - a cone of mist is the full height */
  const col = 400 - Math.round(400 * .3); let top = -1, bot = -1; for(let y = 0; y < 200; y++){ if(d[(y * 400 + col) * 4 + 3] >= 128){ if(top < 0) top = y; bot = y; } }
  for(let i = 3; i < d.length; i += 4){ if(d[i] >= 128) solid++; if(d[i] >= 40) body++; }
  return { key, solid, body, band: top < 0 ? 0 : (bot - top + 1) / 200 };
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
              return { len: h.length, yellowBand: /#F5C518/i.test(h) && /width="160" height="4"/.test(h), placard: ['#E3262E', '#1F6FD1'].filter(c => h.toUpperCase().indexOf(c) >= 0).length }; }""")
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
        b and (b[0] >= b[1] - 2 or b[2] < .05) and a and a[0] < a[2] and a[3] > .9 and max(xs) - min(xs) <= 8, m)
    fl = m["flash"]
    chk("(D4) %s: the surge is one ring from the box's middle (%s) - no sparks (%s) and no flash (%s)" % (dev, m["ringAtSlam"], m["sparks"], fl), m["ringAtSlam"] >= 1 and m["sparks"] == 0 and not any(f[1] > .3 for f in fl), m)
    chk("(D7) %s: THE HOSE - there is one, joined to the nozzle's coupling at every moment of the decon (gap in px: %s) and running off the bottom of the screen (its far end's y %s, the screen's foot %s)" % (
        dev, [h["join"] for h in m.get("hose") or []], [h["endY"] for h in m.get("hose") or []], m.get("H")),
        m.get("hasHose") and all(h["vis"] > .9 and h["join"] <= 4 and h["endY"] >= m["H"] for h in m["hose"]), m)
    chk("(D7) %s: ...and the stream leaves the nozzle's mouth (gap in px at three moments of the sweep: %s)" % (dev, m.get("mouth")), m.get("mouth") and max(m["mouth"]) <= 4, m)
    fo = m.get("foam"); sd = m.get("suds")
    chk("(D8) %s: THE FOAM that carries the film off - a column of suds at the wash's edge, on the box mid-pass (%s), and suds on the glass behind it that are there after the pass (%s) and gone before the all clear (%s)" % (dev, fo, sd, sd),
        fo and fo["vis"] > .8 and fo["bl"] <= fo["cx"] <= fo["br"] and fo["h"] >= fo["bh"] * .9 and sd and sd[0] > .5 and sd[1] > .5 and sd[2] < .05 and sd[3] < .05, m)
    ch = m.get("chip") or []
    chk("(D9) %s: a plain DECON label, only in the decon beat (opacity at .5s, the surge, as he is up, mid-wash, the end of the wash, just after the all clear: %s; its look %s)" % (dev, ch, m.get("chipLook")),
        len(ch) == 6 and ch[0] <= 0 and ch[1] <= 0 and ch[3] > .9 and ch[4] > .9 and ch[5] <= 0 and m["chipLook"] and m["chipLook"][0] == "0px" and m["chipLook"][1] == "none", m)
    gl = m.get("glints") or [0, 0, 0]
    chk("(D10) %s: a sparkle sweep at the all clear - %s glints in all, %s at once at most, none before it (%s)" % (dev, gl[0], gl[1], gl[2]), gl[0] >= 4 and gl[1] >= 2 and gl[2] == 0, m)
    chk("(D10) %s: a beacon lamp glows at each beacon in the alert, over the box's own amber (3 glows, was 1: %s) and the spill has a second, smaller ring behind the first (%s at once at most)" % (dev, m.get("lamps"), m.get("rings2")), m.get("lamps") >= 3 and m.get("rings2") >= 2, m)
    chk("(D5) %s: the all clear still goes off - a lime ring out of the box (%s) and rays behind it (%s)" % (dev, m["ringAtClear"], m["raysAtClear"]), m["ringAtClear"] >= 1 and m["raysAtClear"] >= 1, m)
j = P["jet"]
print("jet", j)
chk("(D3) the jet is a solid stream, not a fan of dots or a cone of mist (round 3: sprite %s; opaque area %s px, body %s px, and an edge - a band %.2f of the sprite's height 70%% of the way down it, a cone of mist is the whole height)" % (j["key"], j["solid"], j["body"], j["band"]),
    j["key"] == "ifx-hzspray3" and j["solid"] >= 3000 and 0 < j["band"] <= .45, j)
t = P["tile"]
chk("(D1) the tile and the still draw no placard colours and no hazard band (%s)" % t, t["len"] > 300 and t["placard"] == 0 and not t["yellowBand"], t)
snd = P["sound"]
chk("(D6) the sound renders in Fire Code, not silent, not clipping (peak %.2f)" % snd["peak"], snd["cls"] == "ifc" and .05 < snd["peak"] < 1 and snd["len"] >= 6.0, snd)
chk("(D6) ...its loudest moment on the surge or the all clear (at %.2fs)" % snd["loudestAt"], 2.25 <= snd["loudestAt"] <= 2.6 or 4.7 <= snd["loudestAt"] <= 5.15, snd)
chk("no page errors (%s)" % errs_all[:2], not errs_all, errs_all)
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
