"""Build 384: Fire Code's 150 - Hazmat, the showpiece (ifxHazmat on the ufo rung).
Madison: "The hazmat one is super cool, I don't love love it though, I just feel like it has so much potential. The hazmat
one should probably be the 200 hundos one, it's my favorite/coolest/has the best potential. ... Tighten up all of them where
you can to ensure they perfect". In the Fire Code class, on the iPhone 17 Pro Max (440x956) and the iPad (834x1194), a 100%
box on the page plays the ufo rung; its animations are paused and seeked to moments on the effect's own clock (IFX_HZ, or
the 384 beats where an older build has none) and everything is read off the page:
 (1) the ufo rung in Fire Code is ifxHazmat; its run is 6.5-7.5s with the tail before the total;
 (2) the NFPA 704 placard assembles a quarter at a time: each quarter reaches its place at its own moment, blue (health 1)
     first and white last, at least 0.12s apart, and they sit as a diamond; then a frame slams round all four;
 (3) the containment scan locks on the box: four brackets fly in from the screen's four corners and lock on the box's four
     corners, drawn OVER the lifted box (their layer stacks above it);
 (4) the placard then sits on a tag over the box, centred on it, and the tag turns over at the all clear;
 (5) the responder walks in from beyond the right edge (wand and all) and his spray reaches the box, swept side to side
     across it;
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
BEATS = {"tot": 7.2, "q": [1.0, 1.18, 1.36, 1.54], "slam": 1.74, "brk": 2.38, "lock": 2.64, "docked": 2.66, "walk": 2.95, "spray": 3.84,
         "sweep": [3.86, 4.48, 4.96], "sprayEnd": 5.0, "clear": 5.15, "fade": 6.05}
SETUP = r"""async (beats) => {
  const Z = (typeof IFX_HZ !== 'undefined') ? IFX_HZ : beats;
  try{ hfxWarm('ufo'); }catch(e){}
  /* the sprites drawn to bitmaps first, as on the results screen */
  for(let i = 0; i < 80 && !['ifx-quad0', 'ifx-quad3', 'ifx-bracket', 'ifx-tag'].every(k => hfxSprites[k] && hfxSprites[k].png); i++) await new Promise(r => setTimeout(r, 100));
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
  /* (2) the quarters: when each comes to rest where it ends up (sampled every 20ms) */
  const quads = [0, 1, 2, 3].map(k => X.find('ifx-quad' + k)[0] || null);
  out.quadsFound = quads.filter(Boolean).length;
  if(out.quadsFound === 4){
    const fin = at(Z.slam + .3, () => quads.map(q => X.R(q)));
    /* home: no transform of its own left (moved, turned or scaled) in the placard it sits in, and shown */
    const home = q => { const m = (getComputedStyle(q).transform.match(/matrix\(([^)]*)\)/) || [, '1,0,0,1,0,0'])[1].split(',').map(Number);
      return Math.abs(m[0] - 1) < .01 && Math.abs(m[1]) < .01 && Math.abs(m[2]) < .01 && Math.abs(m[3] - 1) < .01 && Math.abs(m[4]) < .5 && Math.abs(m[5]) < .5 && X.eff(q) > .9; };
    const land = [null, null, null, null];
    for(let t = .5; t <= Z.slam + .3; t += .02){ X.seek(t); quads.forEach((q, k) => { if(home(q)){ if(land[k] == null) land[k] = Math.round(t * 100) / 100; } else land[k] = null; }); }
    out.land = land;
    const [top, right, bottom, left] = fin;
    out.diamond = Math.abs(top.cx - bottom.cx) <= 2 && Math.abs(left.cy - right.cy) <= 2 && Math.abs((bottom.cy - top.cy) - (right.cx - left.cx)) <= 3 && top.cy < left.cy && bottom.cy > left.cy;
    /* the frame round all four, slammed on at the end */
    const fr = X.find('ifx-hzframe')[0];
    out.frame = fr ? { before: at(Z.slam - .15, () => X.eff(fr)), after: at(Z.slam + .12, () => X.eff(fr)), wraps: at(Z.slam + .3, () => { const r = X.R(fr); return fin.every(q => q.l >= r.l - 1 && q.r <= r.r + 1 && q.t >= r.t - 1 && q.b <= r.b + 1); }) } : null;
    /* (4) where the placard is once it has docked: over the box, small */
    out.dock = at(Z.docked + .5, () => { const d = quads[0].parentElement, r = X.R(d); return { cy: r.cy, w: r.w, vis: X.eff(quads[0]) }; });
    out.diaW = at(Z.slam + .3, () => X.R(quads[0].parentElement).w);
  }
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
  /* (4) the tag over the box, turned over at the all clear */
  const tg = X.find('ifx-tag')[0], ok = X.find('ifx-hztagok')[0];
  out.tag = tg ? at(Z.docked + .6, () => { const r = X.R(tg.parentElement), v = X.eff(tg); return { cy: r.cy, cx: r.cx, l: r.l, vis: v }; }) : null;
  out.turned = (tg && ok) ? at(Z.clear + .5, () => [X.eff(tg), X.eff(ok)]) : null;
  /* (5) the responder: off the screen with his wand before he walks in, on it after; the spray's far end on the box */
  const suit = X.find('ifx-suit2')[0], sp = X.find('ifx-hzspray')[0];
  if(suit){
    const rig = suit.parentElement, arm = X.find('ifx-hzarm2')[0];
    out.offBefore = at(Z.walk - .02, () => [X.R(suit).l, arm ? X.R(arm).l : -1, X.W]);
    out.onAfter = at(Z.walk + .7, () => { const r = X.R(suit); return [r.l, r.r, X.W]; });
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
  return { layers: document.querySelectorAll('.hfx-layer').length, top: document.querySelectorAll('.hfx-ufo-top').length, box: X.card.querySelectorAll('.hfx-box').length,
    lifted: X.card.classList.contains('hfx-over') || X.card.classList.contains('hfx-lift'), done: X.h.done };
}"""
SMALL = r"""async () => {
  const st = buildHundoFxStage('ufo', { big: true }); st.style.cssText = 'position:fixed;left:20px;top:620px;width:300px;'; document.body.appendChild(st);
  await new Promise(r => requestAnimationFrame(() => r()));
  const h = playHundoFx('ufo', { box: st, pct: st.querySelector('.hfx-stage-pct'), boxOnly: true });
  const n = h && h.box ? h.box.querySelectorAll('*').length : 0, total = h ? h.total : 0;
  await new Promise(r => setTimeout(r, total + 400));
  const tile = buildHundoFxTile('ufo').querySelector('svg'), still = buildHundoFxStill('ufo');
  const cols = s => ['#E3262E', '#F5C518', '#F4F4F2', '#1F6FD1'].filter(c => (s || '').toUpperCase().indexOf(c) >= 0).length;
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
    land = m.get("land") or [None] * 4
    order = [3, 0, 1, 2]   # blue, red, yellow, white
    seq = [land[k] for k in order]
    one_by_one = all(x is not None for x in seq) and all(seq[i + 1] - seq[i] >= .12 for i in range(3))
    chk("(2) %s: the placard's quarters land one at a time - blue 1 first, white last, 0.12s+ apart (blue/red/yellow/white at %s)" % (dev, seq), m.get("quadsFound") == 4 and one_by_one, m.get("land"))
    chk("(2) %s: ...and sit as a diamond" % dev, m.get("diamond"), m)
    fr = m.get("frame")
    chk("(2) %s: ...then a frame slams round all four (%s)" % (dev, fr), fr and fr["before"] < .05 and fr["after"] > .9 and fr["wraps"], fr)
    lockErr, vis = m.get("lockErr") or [999] * 4, m.get("lockVis") or [0] * 4
    chk("(3) %s: four brackets lock on the box's four corners (%s of a bracket off, shown %s)" % (dev, lockErr, vis), m.get("brackets") == 4 and max(lockErr) <= .5 and min(vis) > .9, m)
    fc = m.get("fromCorners") or [1] * 4
    chk("(3) %s: ...flying in from the screen's four corners (%s of the diagonal away as they start)" % (dev, fc), max(fc) <= .2, fc)
    z = m.get("zOver")
    chk("(3) %s: ...drawn over the lifted box (their layer z %s, the box %s)" % (dev, z and z[0], z and z[1]), z and (z[2] or z[0] > z[1]), z)
    tag, box, dock = m.get("tag"), m["box"], m.get("dock") or {}
    chk("(4) %s: the placard sits on a tag over the box, centred on it (tag at %s, box %s..%s)" % (dev, tag, round(box["t"]), round(box["b"])),
        tag and tag["vis"] > .9 and tag["cy"] < box["t"] and abs(tag["cx"] - box["cx"]) < box["w"] * .2 and dock.get("cy", 1e9) < box["t"] + 6 and dock.get("w", 1e9) < (m.get("diaW") or 0) * .4 and dock.get("vis", 0) > .9, [tag, dock, m.get("diaW")])
    tn = m.get("turned")
    chk("(4) %s: ...and the tag turns over at the all clear (%s)" % (dev, tn), tn and tn[0] < .05 and tn[1] > .9, tn)
    ob, oa = m.get("offBefore"), m.get("onAfter")
    chk("(5) %s: the responder is beyond the right edge, wand and all, before he walks in (%s), and on the screen after (%s)" % (dev, ob, oa),
        ob and ob[0] >= ob[2] and ob[1] >= ob[2] and oa and oa[0] < oa[2] and oa[1] > oa[2] * .5, [ob, oa])
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
chk("(8) the tile and the still draw the placard's four colours (%s/4, %s/4)" % (s["tileCols"], s["stillCols"]), s["tile"] > 200 and s["still"] > 100 and s["tileCols"] == 4 and s["stillCols"] == 4, s)
snd = P["sound"]
slam, clear = BEATS["slam"], BEATS["clear"]
chk("(9) its sound renders in Fire Code, not silent, not clipping (peak %.2f, %.1fs)" % (snd["peak"], snd["len"]), snd["cls"] == "ifc" and .05 < snd["peak"] < 1 and snd["len"] >= 6.5, snd)
chk("(9) ...its loudest moment on the slam or the all clear (at %.2fs)" % snd["loudestAt"], slam - .05 <= snd["loudestAt"] <= slam + .3 or clear - .05 <= snd["loudestAt"] <= clear + .4, snd)
chk("(9) ...and the decon is not left quiet (%.3f against %.3f)" % (snd["decon"], snd["loudest"]), snd["decon"] >= snd["loudest"] * .4, snd)
chk("(10) no page errors (%s)" % errs_all[:3], not errs_all, errs_all)
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
