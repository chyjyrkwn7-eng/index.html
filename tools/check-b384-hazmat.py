"""Build 384: Fire Code's 150 - Hazmat, the showpiece (ifxHazmat on the ufo rung).
Madison: "The hazmat one is super cool, I don't love love it though, I just feel like it has so much potential. The hazmat
one should probably be the 200 hundos one, it's my favorite/coolest/has the best potential. ... Tighten up all of them where
you can to ensure they perfect". In the Fire Code class, on the iPhone 17 Pro Max (440x956) and the iPad (834x1194), a 100%
box on the page plays the ufo rung; its animations are paused and seeked to moments on the effect's own clock (IFX_HZ, or
the 384 beats where an older build has none) and everything is read off the page:
 (1) the ufo rung in Fire Code is ifxHazmat; its run is 6.5-7.5s with the tail before the total;
 (2) [ROUND 6: REMOVED] the NFPA 704 placard that assembled a quarter at a time and slammed is gone ("I don't like the caution
     tape and I don't think I like the hazmat placard across the screen") - tools/check-b384-hzdecon.py asserts it is gone;
 (3) the containment scan locks on the box: four brackets fly in from the screen's four corners and lock on the box's four
     corners, drawn OVER the lifted box (their layer stacks above it);
 (4) [ROUND 6: REMOVED] the tag the placard sat on is gone with it;
 (5) the responder (round 6: no longer walking across the screen) comes up from under the screen's foot into his corner,
     and his jet reaches the box, swept side to side across it;
 (6) it ends by its total: at the tail every piece has faded, and after the total no layer, box piece or lift is left;
 (7) only transform and opacity move, no ifx sprite has an svg filter, no more than 170 pieces across its layers;
 (8) the small box (a tile's stage) plays its own short one and is gone by its total; the tile and the still draw the
     placard's four colours;
 (9) its sound renders in Fire Code - not silent, not clipping, its loudest moment on the slam or the all clear and the
     decon not left quiet;
 (10) no page errors.
Run:  python3 tools/check-b384-hazmat.py   (--against OLD/index.html must FAIL)"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b384hazmat"}
exec(src, G)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)
# the 384 beats, for a build that has no IFX_HZ
BEATS = {"tot": 7.2, "slam": 1.74, "brk": 2.38, "lock": 2.64, "walk": 2.95, "walked": 3.5, "spray": 3.84,
         "sweep": [3.86, 4.48, 4.96], "sprayEnd": 5.0, "clear": 5.15, "fade": 6.05}
SETUP = r"""async (beats) => {
  const Z = (typeof IFX_HZ !== 'undefined') ? IFX_HZ : beats;
  try{ hfxWarm('ufo'); }catch(e){}
  /* the sprites drawn to bitmaps first, as on the results screen */
  for(let i = 0; i < 80 && !['ifx-bracket', 'ifx-hzspray2'].every(k => hfxSprites[k] && hfxSprites[k].png); i++) await new Promise(r => setTimeout(r, 100));
  await new Promise(r => setTimeout(r, 300));
  const W = innerWidth, H = innerHeight, bw = Math.min(W - 60, 600), bh = Math.round(bw * .45);
  const card = document.createElement('div'); card.className = 'rs-card rs-grade is-perfect';
  card.style.cssText = 'position:fixed;left:' + Math.round((W - bw) / 2) + 'px;top:' + Math.round(H * .18) + 'px;width:' + bw + 'px;height:' + bh + 'px;border-radius:18px';
  const pct = document.createElement('span'); pct.className = 'rs-pct pct perfect'; gradePctMarkup(pct, 100); pct.style.cssText = 'position:absolute;left:24px;top:30px;font-size:64px;font-weight:800;line-height:1';
  card.appendChild(pct); document.body.appendChild(card);
  const h = playHundoFx('ufo', { box: card, pct });
  await new Promise(r => setTimeout(r, 0)); await new Promise(r => requestAnimationFrame(() => r()));
  const top = document.querySelector('.hfx-ufo-top');
  const layers = [h && h.screen, top, h && h.box].filter(Boolean);
  const S = id => (typeof hfxSprites !== 'undefined' && hfxSprites[id]) || null;
  const is = (el, id) => { const sp = S(id); if(!sp) return false; const b = el.style.backgroundImage || ''; return (sp.png && b === sp.png) || b === sp.svg || (sp.png && b.indexOf(sp.png.slice(5, -2)) >= 0); };
  const all = () => layers.flatMap(l => [...l.querySelectorAll('*')]);
  const find = id => all().filter(e => is(e, id));
  const anims = () => document.getAnimations().filter(a => a.effect && a.effect.target && layers.some(l => l.contains(a.effect.target)));
  const eff = el => { let o = 1, e = el; while(e && e !== document.body){ o *= +getComputedStyle(e).opacity; e = e.parentElement; } return o; };
  const R = el => { const r = el.getBoundingClientRect(); return { l: r.left, t: r.top, r: r.right, b: r.bottom, cx: (r.left + r.right) / 2, cy: (r.top + r.bottom) / 2, w: r.width, h: r.height }; };
  const cr = card.getBoundingClientRect(), box = { l: cr.left, t: cr.top, r: cr.right, b: cr.bottom, cx: (cr.left + cr.right) / 2, cy: (cr.top + cr.bottom) / 2, w: cr.width, h: cr.height };
  const props = [...new Set(anims().filter(a => a.constructor === Animation).flatMap(a => a.effect.getKeyframes().flatMap(k => Object.keys(k))))].filter(p => ['offset', 'computedOffset', 'easing', 'composite'].indexOf(p) < 0).sort();
  window.__hz = { Z, h, card, top, layers, find, anims, eff, R, box, W, H,
    seek: t => { anims().forEach(a => { try{ a.pause(); a.currentTime = t * 1000; }catch(e){} }); } };
  return { cls: window.NOVA_CLASS, build: ((typeof HUNDO_FX_BUILD !== 'undefined' && HUNDO_FX_BUILD.ufo) || {}).name, total: HUNDO_FX_TOTAL.ufo, tail: HUNDO_FX_TAIL_AT.ufo,
    def: (typeof IFX_DEF !== 'undefined' && IFX_DEF.ufo) ? [IFX_DEF.ufo.total, IFX_DEF.ufo.tail, IFX_DEF.ufo.box] : null, hasTop: !!top, props,
    pieces: layers.reduce((n, l) => n + l.querySelectorAll('*').length, 0), screenPieces: h && h.screen ? h.screen.querySelectorAll('*').length : 0,
    filters: Object.keys(hfxSprites).filter(k => /^ifx-/.test(k) && /<filter|filter=/.test(hfxSprites[k].text || '')), hz: Object.keys(hfxSprites).filter(k => /^ifx-hz/.test(k)).length };
}"""
MEASURE = r"""() => {
  const X = window.__hz, Z = X.Z, out = {};
  const at = (t, fn) => { X.seek(t); return fn(); };
  /* (3) the brackets: from the screen's corners onto the box's, over the box */
  const br = X.find('ifx-bracket');
  out.brackets = br.length;
  if(br.length === 4){
    const corner = r => [[r.l, r.t], [r.r, r.t], [r.r, r.b], [r.l, r.b]];
    const near = (r, p) => Math.min(...corner(r).map(c => Math.hypot(c[0] - p[0], c[1] - p[1])));
    const bc = corner(X.box), sc = [[0, 0], [X.W, 0], [X.W, X.H], [0, X.H]], diag = Math.hypot(X.W, X.H);
    /* how far the bracket's outer corner sits off the box's corner, in brackets (its L is drawn inset in its square) */
    out.lockErr = at(Z.lock + .4, () => br.map(b => { const r = X.R(b); return Math.round(Math.min(...bc.map(c => near(r, c))) / r.w * 100) / 100; }));
    out.lockVis = at(Z.lock + .4, () => br.map(b => Math.round(X.eff(b) * 100) / 100));
    out.fromCorners = at(Z.brk + .03, () => br.map(b => { const r = X.R(b); return Math.round(Math.min(...sc.map(c => Math.hypot(r.cx - c[0], r.cy - c[1]))) / diag * 100) / 100; }));
    const lay = br[0].closest('.hfx-layer') || br[0].closest('.hfx-box');
    out.zOver = lay ? [+getComputedStyle(lay).zIndex || 0, +getComputedStyle(X.card).zIndex || 0, lay.classList.contains('hfx-box')] : null;
  }
  /* (5) the responder: below the screen's foot before he rises, in his corner after, and not walking (his x holds); the jet's far end on the box */
  const suit = X.find('ifx-suit2')[0], sp = X.find('ifx-hzspray2')[0];
  if(suit){
    const rig = suit.parentElement, arm = X.find('ifx-hzarm2')[0];
    out.offBefore = at(Z.walk - .02, () => [X.R(suit).t, X.H, X.eff(suit)]);
    out.onAfter = at(Z.walked + .2, () => { const r = X.R(suit); return [r.t, r.b, X.H, X.eff(suit)]; });
    out.xs = [Z.walked + .2, Z.aim, Z.spray + .5, Z.sprayEnd].map(t => at(t, () => Math.round(X.R(suit).cx)));
  }
  if(sp){
    const probe = document.createElement('i'); probe.style.cssText = 'position:absolute;left:0;top:50%;width:0;height:0;';
    sp.appendChild(probe);
    const end = t => at(t, () => { const r = probe.getBoundingClientRect(); return { x: Math.round(r.left), y: Math.round(r.top), vis: Math.round(X.eff(sp) * 100) / 100 }; });
    out.spray = { a: end(Z.sweep[0] + .12), b: end(Z.sweep[1]), c: end((Z.sweep[0] + Z.sweep[1]) / 2) };
    probe.remove();
  }
  /* (6) at the tail's end every piece has faded */
  out.left = at(Z.tot - .3, () => X.layers.flatMap(l => [...l.querySelectorAll('*')]).filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && X.eff(e) > .02 && getComputedStyle(e).backgroundImage !== 'none'; }).length);
  out.box = X.box;
  return out;
}"""
END = r"""async () => {
  const X = window.__hz;
  X.anims().forEach(a => { try{ a.play(); }catch(e){} });
  await new Promise(r => setTimeout(r, X.h.total + 500));
  /* (384, cutscenes) only a layer this play could leave: an unlock card Home puts up meanwhile (What's New no longer holds
     Fire Code's queue) shows its own effect in a layer of its own, inside the card */
  return { layers: [...document.querySelectorAll('.hfx-layer')].filter(l => !l.closest('.rs-spot')).length, top: document.querySelectorAll('.hfx-ufo-top').length, box: X.card.querySelectorAll('.hfx-box').length,
    lifted: X.card.classList.contains('hfx-over') || X.card.classList.contains('hfx-lift'), done: X.h.done };
}"""
SMALL = r"""async () => {
  const st = buildHundoFxStage('ufo', { big: true }); st.style.cssText = 'position:fixed;left:20px;top:620px;width:300px;'; document.body.appendChild(st);
  await new Promise(r => requestAnimationFrame(() => r()));
  const h = playHundoFx('ufo', { box: st, pct: st.querySelector('.hfx-stage-pct'), boxOnly: true });
  const n = h && h.box ? h.box.querySelectorAll('*').length : 0, total = h ? h.total : 0;
  await new Promise(r => setTimeout(r, total + 400));
  const tile = buildHundoFxTile('ufo').querySelector('svg'), still = buildHundoFxStill('ufo');
  const cols = s => ['#E3262E', '#1F6FD1'].filter(c => (s || '').toUpperCase().indexOf(c) >= 0).length;   /* the placard's: none may be drawn now */
  return { n, total, gone: !st.querySelector('.hfx-box'), tile: tile ? tile.outerHTML.length : 0, tileCols: cols(tile && tile.outerHTML), still: still ? still.outerHTML.length : 0, stillCols: cols(still && still.outerHTML) };
}"""
SOUND = r"""async () => {
  const buf = await NovaSound.render('hundo.ufo', { sr: 44100 });
  const L = buf.getChannelData(0), R = buf.numberOfChannels > 1 ? buf.getChannelData(1) : L, n = L.length, sr = buf.sampleRate, w = Math.round(sr * .05);
  let peak = 0; for(let i = 0; i < n; i++) peak = Math.max(peak, Math.abs(L[i]), Math.abs(R[i]));
  const rms = []; for(let s = 0; s + w <= n; s += w){ let e = 0; for(let i = s; i < s + w; i++) e += (L[i] * L[i] + R[i] * R[i]) / 2; rms.push(Math.sqrt(e / w)); }
  const top = rms.indexOf(Math.max(...rms)), win = (a, b) => Math.max(...rms.slice(Math.round(a / .05), Math.round(b / .05)));
  return { peak, len: n / sr, loudestAt: Math.round(top * .05 * 100) / 100, loudest: Math.max(...rms), decon: win(3.9, 4.9), cls: window.NOVA_CLASS };
}"""
res = {}
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    errs_all = []
    for dev, (w, h) in (("phone", (440, 956)), ("ipad", (834, 1194))):
        ctx, pg, errs = G["page"](br, G["init"](G["ifc"]))
        pg.set_viewport_size({"width": w, "height": h}); pg.wait_for_timeout(400)
        info = pg.evaluate(SETUP, BEATS)
        m = pg.evaluate(MEASURE)
        e = pg.evaluate(END)
        extra = {}
        if dev == "phone":
            extra["small"] = pg.evaluate(SMALL)
            extra["sound"] = pg.evaluate(SOUND)
        res[dev] = dict(info=info, m=m, end=e, **extra)
        errs_all += errs
        ctx.close()
    br.close()
P, I = res["phone"], res["ipad"]
info = P["info"]
chk("the page is the Fire Code class (%s)" % info["cls"], info["cls"] == "ifc", info)
chk("(1) the ufo rung in Fire Code plays ifxHazmat (%s)" % info["build"], info["build"] == "ifxHazmat", info["build"])
d = info["def"] or [0, 0, 0]
chk("(1) ...a run of 6.5-7.5s, its tail before its total (total %s, tail %s, layers removed at %s)" % (d[0], d[1], info["total"]),
    6500 <= d[0] <= 7500 and d[1] < d[0] and info["total"] == d[0], info)
for dev, R in (("phone", P), ("ipad", I)):
    m = R["m"]
    lockErr, vis = m.get("lockErr") or [999] * 4, m.get("lockVis") or [0] * 4
    chk("(3) %s: four brackets lock on the box's four corners (%s of a bracket off, shown %s)" % (dev, lockErr, vis), m.get("brackets") == 4 and max(lockErr) <= .5 and min(vis) > .9, m)
    fc = m.get("fromCorners") or [1] * 4
    chk("(3) %s: ...flying in from the screen's four corners (%s of the diagonal away as they start)" % (dev, fc), max(fc) <= .2, fc)
    z = m.get("zOver")
    chk("(3) %s: ...drawn over the lifted box (their layer z %s, the box %s)" % (dev, z and z[0], z and z[1]), z and (z[2] or z[0] > z[1]), z)
    box = m["box"]
    ob, oa, xs = m.get("offBefore"), m.get("onAfter"), m.get("xs") or [0, 1e9]
    chk("(5) %s: the responder is under the screen's foot before he comes up (top %s of %s) and in his corner after (%s) - not walking across (x %s)" % (dev, ob and ob[0], ob and ob[1], oa, xs),
        ob and (ob[0] >= ob[1] - 2 or ob[2] < .05) and oa and oa[0] < oa[2] and oa[3] > .9 and max(xs) - min(xs) <= 8, [ob, oa, xs])
    sp = m.get("spray")
    onbox = lambda p: p and p["vis"] > .9 and box["l"] - box["w"] * .08 <= p["x"] <= box["r"] + box["w"] * .08 and box["t"] - box["h"] * .25 <= p["y"] <= box["b"] + box["h"] * .25
    chk("(5) %s: his spray reaches the box (its far end at %s)" % (dev, sp and sp["c"]), sp and onbox(sp["c"]) and onbox(sp["a"]) and onbox(sp["b"]), sp)
    chk("(5) %s: ...swept side to side across it (left end %s, right %s, the box's middle %s)" % (dev, sp and sp["a"]["x"], sp and sp["b"]["x"], round(box["cx"])),
        sp and sp["a"]["x"] < box["cx"] - box["w"] * .15 and sp["b"]["x"] > box["cx"] + box["w"] * .15, sp)
    chk("(6) %s: at the end of its tail every piece has faded (%s still showing)" % (dev, m.get("left")), m.get("left") == 0, m.get("left"))
    e = R["end"]
    chk("(6) %s: after its total nothing is left - no layer, no box piece, the box set down (%s)" % (dev, e), e["done"] and not e["layers"] and not e["top"] and not e["box"] and not e["lifted"], e)
    i2 = R["info"]
    chk("(7) %s: only transform and opacity move (%s), no ifx sprite has an svg filter (%s), %s pieces (170 at most) across %s layers" % (dev, i2["props"], i2["filters"], i2["pieces"], 3 if i2["hasTop"] else 2),
        i2["props"] and all(p in ("opacity", "transform") for p in i2["props"]) and not i2["filters"] and i2["pieces"] <= 170 and i2["hz"] >= 10, i2)
s = P["small"]
chk("(8) the small box plays its own (%s pieces) and is gone by its total (%sms)" % (s["n"], s["total"]), s["n"] >= 6 and s["gone"] and 3500 <= s["total"] <= 6000, s)
chk("(8) the tile and the still draw neither of the placard's red and blue any more (%s/4, %s/4)" % (s["tileCols"], s["stillCols"]), s["tile"] > 200 and s["still"] > 100 and s["tileCols"] == 0 and s["stillCols"] == 0, s)
snd = P["sound"]
slam, clear = BEATS["slam"], BEATS["clear"]
chk("(9) its sound renders in Fire Code, not silent, not clipping (peak %.2f, %.1fs)" % (snd["peak"], snd["len"]), snd["cls"] == "ifc" and .05 < snd["peak"] < 1 and snd["len"] >= 6.5, snd)
chk("(9) ...its loudest moment on the slam or the all clear (at %.2fs)" % snd["loudestAt"], slam - .05 <= snd["loudestAt"] <= slam + .3 or clear - .05 <= snd["loudestAt"] <= clear + .4, snd)
chk("(9) ...and the decon is not left quiet (%.3f against %.3f)" % (snd["decon"], snd["loudest"]), snd["decon"] >= snd["loudest"] * .4, snd)
chk("(10) no page errors (%s)" % errs_all[:3], not errs_all, errs_all)
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
