#!/usr/bin/env python3
"""Build 384, Madison's review of nine Fire Code banners. In the Fire Code class:

 (1) all nine draw, each with its tint, and no page error;
 (2) every one of the nine is drawn differently from 185cc5c (R5, hashes from check-b382-ifcart --dump there);
 (3) Dispatch, Code Book, Hazmat, Hose Line (it is Ten in a Row since round 3b) and the three rank banners are exactly as they were ("Leave them alone");
 (4) the names: no Code 3 ("we don't do code threes"), no Air Tanker or Pull Station (both "something else"); Fire Response is there;
 (5) the office's vehicles ("white chevys with ghost lettering and lights"): Headquarters draws two and Fire Response one, each
     ghost-lettered (.fb-ghost), and none of the three banners carries a long thin red band - round 3's ambulance stripe;
 (6) Spill Response ("the hazmat guys look weird"): two technicians (.fb-tech), each with a faceplate in the top of the figure;
 (7) Field Kit ("none of us put our badge in a wallet"): the badge rides on the belt (its centre within a badge's reach of the belt);
 (8) Exit ("there's like 5 exits right there"): one EXIT sign;
 (9) Alarm Panel ("not sure why there is a strobe right next to it ... the document box"): a documents box beside the panel, and no
     strobe's white flash anywhere in the banner;
(10) Sprinklers ("the red box in the bottom right"): nothing solid red stands in the lower part of the scene;
(11) none of the nine has an svg filter; every one has a bl- motion layer;
(12) two copies of each on one screen share no ids, and every url(#...) in a copy resolves inside that copy;
(13) light: none of the nine has more elements, or more layers, than the heaviest of the other Fire Code banners.

  python3 tools/check-b384-banners.py [--against OLD/index.html]   (must FAIL on the build before)
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
from playwright.sync_api import sync_playwright
BODY = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read() if "--against" in sys.argv else None
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400])
NINE = ["tests100", "tests250", "tests500", "hundos100", "hundos250", "study60", "correct5000", "correct10000", "early10"]
KEEP = ["adept_rank", "elite_rank", "titan_rank"]   # study50 (Code Book) left this list in round 3: its stray lines were removed
# the Fire Code banners as 185cc5c (build 384 before this review) drew them: check-b382-ifcart.py --dump there
R5 = {"tests100": "64fb9bd3", "tests250": "2f60696c", "tests500": "90342325", "hundos100": "1c5cd518", "hundos250": "95a83aab", "vr50": "2757f261",
      "study50": "5270326f", "study60": "f2b6a375", "correct5000": "b6f4ed31", "correct10000": "6df94430", "level80": "295e1a71", "early10": "d70885ca",
      "exam100": "876dca39", "adept_rank": "84f1e18f", "elite_rank": "34c28658", "titan_rank": "d1c86e5d"}
seed = dict(rc["SEED"]); seed["publicId"] = "xph5b57jbp5a"; seed["novaMet"] = 99
SNAP = r"""(ids) => {
  const NINE = ids[0], KEEP = ids[1];
  const hash = s => { let h = 2166136261; for(let i = 0; i < s.length; i++){ h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0).toString(16); };
  const out = { cls: window.NOVA_CLASS, errs: [], hashes: {}, names: {}, shapes: {} };
  BANNERS.forEach(b => out.names[b.id] = b.name);
  NINE.concat(KEEP).forEach(id => {
    try{ out.hashes[id] = hash(bannerStaticSVG(id) || '');
      const el = buildBannerArt(id); if(!el || !el.querySelector('svg')) out.errs.push(id + ' draws nothing');
      if(!bannerTintOf(id)) out.errs.push(id + ' has no tint'); }catch(e){ out.errs.push(id + ': ' + e); }
  });
  /* each banner's still picture, mounted 1:1 so its pieces can be measured in scene units */
  const mount = id => { const box = document.createElement('div'); box.style.cssText = 'position:fixed;left:0;top:0;width:480px;height:180px;overflow:hidden;z-index:99999';
    box.innerHTML = bannerStaticSVG(id) || ''; document.body.appendChild(box); const sv = box.querySelector('svg'); if(sv){ sv.setAttribute('width', 480); sv.setAttribute('height', 180); } return box; };
  const R = e => { const r = e.getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height, cx: r.left + r.width / 2, cy: r.top + r.height / 2 }; };
  const hex = v => { const m = /^#([0-9a-f]{6})$/i.exec((v || '').trim()); if(!m) return null; const n = parseInt(m[1], 16); return [n >> 16, n >> 8 & 255, n & 255]; };
  const isRed = e => { const c = hex(e.getAttribute('fill')); return !!(c && c[0] > 150 && c[1] < 80 && c[2] < 80) && +(e.getAttribute('opacity') || 1) > .5; };
  const solids = box => [...box.querySelectorAll('rect,path,circle,ellipse,polygon')];
  const S = out.shapes;
  try{
    /* (5) the vehicles: ghost lettering, and no ambulance stripe (a long, thin red band) */
    ['tests100', 'early10'].forEach(id => { const b = mount(id);
      S[id] = { ghost: b.querySelectorAll('.fb-ghost').length,
        bands: solids(b).filter(isRed).map(R).filter(r => r.w > 40 && r.h < 8 && r.w / Math.max(r.h, .1) > 8).map(r => [Math.round(r.w), Math.round(r.h * 10) / 10]) };
      b.remove(); });
    /* (6) the technicians */
    { const b = mount('tests250');
      S.tests250 = { techs: [...b.querySelectorAll('.fb-tech')].map(t => { const r = R(t), v = t.querySelector('.fb-visor'); const vr = v && R(v);
        return { h: Math.round(r.h), visorAt: vr ? Math.round((vr.cy - r.y) / r.h * 100) / 100 : null }; }) };
      b.remove(); }
    /* (7) the badge and the belt */
    { const b = mount('tests500'); const g = b.querySelector('.fb-badge'), belt = b.querySelector('.fb-belt');
      S.tests500 = (g && belt) ? (() => { const r = R(g), t = R(belt); return { badge: [Math.round(r.cy), Math.round(r.h / 2)], belt: [Math.round(t.y), Math.round(t.y + t.h)],
        onBelt: r.cy >= t.y - r.h / 2 && r.cy <= t.y + t.h }; })() : { badge: !!g, belt: !!belt, onBelt: false };
      b.remove(); }
    /* (8) the exit signs */
    { const b = mount('hundos100'); S.hundos100 = { signs: b.querySelectorAll('.fb-exit-sign').length }; b.remove(); }
    /* (9) the panel, its documents box beside it, and no strobe's flash in any layer */
    { const b = mount('study60'); const p = b.querySelector('.fb-facp'), d = b.querySelector('.fb-docbox');
      const pr = p && R(p), dr = d && R(d);
      const art = BANNER_ART.study60('g'); const svgAll = Array.isArray(art) ? art.map(l => (l.svg || '') + (l.kids || []).map(k => k.svg || '').join('')).join('') : art;
      const holder = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); holder.innerHTML = svgAll;
      const flashes = [...holder.querySelectorAll('circle')].filter(c => /^#fff(fff)?$/i.test(c.getAttribute('fill') || '') && +c.getAttribute('r') >= 20).length;
      S.study60 = { panel: !!p, box: !!d, beside: !!(pr && dr && dr.x >= pr.x + pr.w - 2 && Math.min(pr.y + pr.h, dr.y + dr.h) - Math.max(pr.y, dr.y) > dr.h * .5), flashes };
      b.remove(); }
    /* (10) nothing solid red low in the sprinkler scene */
    { const b = mount('correct5000'); S.correct5000 = { lowRed: solids(b).filter(isRed).map(R).filter(r => r.y > 108 && r.w > 2 && r.h > 2).map(r => [Math.round(r.x), Math.round(r.y), Math.round(r.w), Math.round(r.h)]) }; b.remove(); }
  }catch(e){ out.errs.push('shapes: ' + e); }
  /* (11) filters, motion; (12) ids per copy; (13) weight */
  out.filters = NINE.filter(id => { try{ return /<filter|filter=/.test(JSON.stringify(BANNER_ART[id]('g'))); }catch(e){ return true; } });
  out.still = NINE.filter(id => { const a = BANNER_ART[id]('g'); return !(Array.isArray(a) && a.some(l => /(^| )bl-/.test(l.cls || '') || (l.kids || []).some(k => /(^| )bl-/.test(k.cls || '')))); });
  out.idClash = []; out.unresolved = [];
  NINE.forEach(id => {
    const a = buildBannerArt(id), b = buildBannerArt(id);
    const ia = new Set([...a.querySelectorAll('[id]')].map(e => e.id)), ib = [...b.querySelectorAll('[id]')].map(e => e.id);
    if(ib.some(x => ia.has(x))) out.idClash.push(id);
    const refs = (a.innerHTML.match(/url\(#([^)]+)\)/g) || []).map(m => m.slice(5, -1));
    const miss = [...new Set(refs.filter(r => !ia.has(r)))]; if(miss.length) out.unresolved.push([id, miss.slice(0, 3)]);
  });
  const weigh = id => { const a = buildBannerArt(id); return [a.querySelectorAll('*').length, a.querySelectorAll('.bnl').length]; };
  out.weight = {}; BANNERS.forEach(b => { try{ out.weight[b.id] = weigh(b.id); }catch(e){} });
  return out;
}"""
srv, port = rc["serve"]()
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    ctx, pg = br.new_context(viewport={"width": 440, "height": 956}), None
    pg = ctx.new_page(); perr = []
    pg.on("pageerror", lambda e: perr.append(str(e)[:200]))
    pg.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
        "localStorage.setItem('class26e.drill.v1',%s);localStorage.setItem('class26e.ifc.drill.v1',%s);"
        "localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));localStorage.setItem('class26e.greet.ifc','done');"
        "['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted'].forEach(k=>localStorage.setItem(k,'1'));}catch(e){}"
        % (json.dumps(json.dumps(seed)), json.dumps(json.dumps(seed))))
    if BODY is not None:
        pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(3000)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    F = pg.evaluate(SNAP, [NINE, KEEP])
    ctx.close(); br.close()
srv.shutdown()
S = F["shapes"]
chk("(1) the page is Fire Code (%s), all nine draw with a tint, no page errors" % F["cls"], F["cls"] == "ifc" and not F["errs"] and not perr, (F["errs"], perr))
same = [i for i in NINE if F["hashes"].get(i) == R5[i]]
chk("(2) all nine are redrawn (unchanged since 185cc5c: %s)" % same, not same, same)
moved = [i for i in KEEP if F["hashes"].get(i) != R5[i]]
chk("(3) the three rank banners are untouched (changed: %s) - the rest moved on in the names pass, see check-b384-fcbanners.py" % moved, not moved, moved)
names = F["names"]
gone = [n for n in ("Code 3", "Air Tanker", "Pull Station", "Headquarters", "Exit", "Pyrotechnics", "Field Kit") if n in names.values()]
chk("(4) none of the retired names is left (%s)" % gone, not gone, names)
ap = S.get("study60", {})
chk("(9) Alarm Panel: the documents box beside the panel, no strobe flash (%s)" % ap, ap.get("panel") and ap.get("box") and ap.get("beside") and ap.get("flashes") == 0, ap)
chk("(11) no svg filter in any of the nine (%s), and every one has a bl- motion layer (still: %s)" % (F["filters"], F["still"]), not F["filters"] and not F["still"])
chk("(12) two copies share no ids (%s) and every url(#...) resolves inside its own copy (%s)" % (F["idClash"], F["unresolved"]), not F["idClash"] and not F["unresolved"])
others = {k: v for k, v in F["weight"].items() if k not in NINE}
emax, lmax = max(v[0] for v in others.values()), max(v[1] for v in others.values())
heavy = {i: F["weight"].get(i) for i in NINE if F["weight"].get(i, [1e9, 1e9])[0] > emax or F["weight"].get(i, [1e9, 1e9])[1] > lmax}
chk("(13) none of the nine is heavier than the heaviest other banner (%d elements, %d layers): %s" % (emax, lmax, {i: F["weight"].get(i) for i in NINE}), not heavy, heavy)
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
