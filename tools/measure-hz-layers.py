"""How many things are on screen at once in the Fire Code Hazmat effect, per half second of its run.
A 100% box on the page plays the ufo rung (Fire Code); every animation is paused and seeked, and the pieces of the effect's layers
(screen, the layer over the box, the box's own) that PAINT something (a sprite, a gradient, text, a border, a shadow) and are visible
(own opacity x its ancestors' > .03, a real size, inside the viewport) are counted: `pieces`, and `kinds` - the distinct things
among them (a sprite counts once however many copies; a gradient or border by its own value).
  python3 tools/measure-hz-layers.py [--against FILE] [--step .5]   -> a table, and the means / peak"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
STEP = .5
if "--step" in sys.argv:
    i = sys.argv.index("--step"); STEP = float(sys.argv[i + 1]); del sys.argv[i:i + 2]
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "hzlayers"}
exec(src, G)
from playwright.sync_api import sync_playwright
SETUP = r"""async () => {
  try{ hfxWarm('ufo'); }catch(e){}
  for(let i = 0; i < 80 && !(typeof hfxSprites !== 'undefined' && Object.keys(hfxSprites).some(k => /^ifx-hz/.test(k) && hfxSprites[k].png)); i++) await new Promise(r => setTimeout(r, 100));
  await new Promise(r => setTimeout(r, 600));
  const W = innerWidth, H = innerHeight, bw = Math.min(W - 60, 600), bh = Math.round(bw * .45);
  const card = document.createElement('div'); card.className = 'rs-card rs-grade is-perfect';
  card.style.cssText = 'position:fixed;left:' + Math.round((W - bw) / 2) + 'px;top:' + Math.round(H * .18) + 'px;width:' + bw + 'px;height:' + bh + 'px;border-radius:18px';
  const pct = document.createElement('span'); pct.className = 'rs-pct pct perfect'; gradePctMarkup(pct, 100); pct.style.cssText = 'position:absolute;left:24px;top:30px;font-size:64px;font-weight:800;line-height:1';
  card.appendChild(pct); document.body.appendChild(card);
  const h = playHundoFx('ufo', { box: card, pct });
  await new Promise(r => setTimeout(r, 0)); await new Promise(r => requestAnimationFrame(() => r()));
  const top = document.querySelector('.hfx-ufo-top');
  const layers = [h && h.screen, top, h && h.box].filter(Boolean);
  const anims = () => document.getAnimations().filter(a => a.effect && a.effect.target && layers.some(l => l.contains(a.effect.target)));
  const eff = el => { let o = 1, e = el; while(e && e !== document.body){ o *= +getComputedStyle(e).opacity; e = e.parentElement; } return o; };
  window.__m = { layers, anims, eff, W, H, total: h.total,
    seek: t => anims().forEach(a => { try{ a.pause(); a.currentTime = t * 1000; }catch(e){} }),
    count: () => {
      const seen = new Set(); let pieces = 0;
      layers.forEach(l => l.querySelectorAll('*').forEach(e => {
        const r = e.getBoundingClientRect(); if(r.width < 2 || r.height < 2 || r.right < 0 || r.left > W || r.bottom < 0 || r.top > H) return;
        const cs = getComputedStyle(e);
        const bi = cs.backgroundImage, paints = bi !== 'none' || (e.textContent || '').trim() || (parseFloat(cs.borderTopWidth) > 0 && !/, 0\)$/.test(cs.borderTopColor)) || cs.boxShadow !== 'none';
        if(!paints) return;
        if(eff(e) <= .03) return;
        pieces++; seen.add(bi !== 'none' ? bi.slice(0, 90) : (cs.boxShadow !== 'none' ? 'shadow' + cs.boxShadow.slice(0, 30) : 'text/border'));
      }));
      return { pieces, kinds: seen.size };
    } };
  return { total: h.total, tot: (typeof IFX_HZ !== 'undefined') ? IFX_HZ.tot : null };
}"""
rows = []
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    ctx, pg, errs = G["page"](br, G["init"](G["ifc"]))
    pg.set_viewport_size({"width": 440, "height": 956}); pg.wait_for_timeout(400)
    info = pg.evaluate(SETUP)
    t = 0.0
    tot = (info["total"] or 7000) / 1000.0
    while t < tot - .05:
        pg.evaluate("t => window.__m.seek(t)", t)
        rows.append((round(t, 2), pg.evaluate("() => window.__m.count()")))
        t += STEP
    br.close()
print("run %.2fs, a sample every %.2fs" % (tot, STEP))
for t, c in rows: print("%5.2fs  pieces %3d  kinds %2d  %s" % (t, c["pieces"], c["kinds"], "#" * (c["pieces"] // 2)))
import statistics
P = [c["pieces"] for _, c in rows]; K = [c["kinds"] for _, c in rows]
print("MEAN pieces %.1f (peak %d)   MEAN kinds %.1f (peak %d)" % (statistics.mean(P), max(P), statistics.mean(K), max(K)))
json.dump(rows, open("/tmp/hzlayers.json", "w"))
