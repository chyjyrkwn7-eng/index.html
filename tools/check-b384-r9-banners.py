#!/usr/bin/env python3
"""Build 384 round 9 (r9-banners): Madison's review of the Fire Code banners.

 (1) the round 9 banners differ from the build before (check-b384-r9-banners.prev.json: bannerStaticSVG hashes of cd82880 in both classes), every
     other Fire Code banner is exactly as it was, and EVERY academy banner is byte-identical (the academy is not touched);
 (2) THE INSPECTOR LOOK, everywhere: every inspector in every Fire Code banner is the shared kit (.fb-officer: Inspection Team 3, Grand Finale 7, Top Floor 1,
     After Hours 1) and each wears the dark brown cowboy hat (.fb-cowboy), and from the front or the side the dark glasses (.fb-shades) and the stubble
     (.fb-stubble); the shirt is NAVY and the vest is BLUE (a blue clearly brighter and bluer than the navy shirt); no ball cap is left anywhere in a Fire Code
     banner (no .fb-cap), and the hat off his head lies on the plans table (Plan Review) and hangs on the gear wall (Squared Away);
 (3) DOWNPOUR is not a wastebasket fire: no can; exactly one sprinkler head open and at least two shut with their bulbs whole; the fire under the open head;
     the spray going out from the open head's deflector;
 (4) AFTER HOURS has two risers (two plates, two handwheels, two gauges, two gauge lines); the inspection tag's wire starts ON a gauge line and ends in the tag's
     hole, the tag hanging below that line; the beam starts at the lens and lands on the tag; the kneeling inspector wears the hat;
 (5) TOP FLOOR has no door, EXIT sign or stair sign: a skyline of at least twelve towers across the whole window, one inspector from behind;
 (6) INSPECTION TEAM is not a line-up in front of a building: three inspectors at three depths (the lead's feet lower than the two behind him), two beams
     starting at their lenses, no lit building windows behind them, the racks' orange beams in the scene;
 (7) THE SECRET FLARES share no long shape between ANY two of the four (Pulsar and Eclipse used to share their hills and lake), each keeps its colour;
 (8) none of the round 9 banners has an svg filter, a clashing id or an unresolved url(#), or is heavier than 700 elements or 24 layers.

  python3 tools/check-b384-r9-banners.py [--against OLD/index.html]     (FAILS on cd82880)
  python3 tools/check-b384-r9-banners.py --dump --against <cd82880 index.html>   writes the .prev.json
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
from playwright.sync_api import sync_playwright
BODY = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read() if "--against" in sys.argv else None
DUMP = "--dump" in sys.argv
PREVF = os.path.join(HERE, "check-b384-r9-banners.prev.json")
R9 = ["tests500", "correct5000", "level80", "early10", "flare_void", "flare_umbra", "flare_horizon", "flare_genesis", "hundos100", "tests250", "hundos250"]
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:600])
seed = dict(rc["SEED"]); seed["publicId"] = "xph5b57jbp9r"; seed["novaMet"] = 99; seed["classes"] = ["academy", "ifc"]; seed["seenClassTip"] = True
def init(cls):
    s = json.dumps(json.dumps(seed))
    return ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
            "localStorage.setItem('class26e.drill.v1',%s);localStorage.setItem('class26e.ifc.drill.v1',%s);"
            "localStorage.setItem('class26e.activeclass','%s');localStorage.setItem('class26e.enrolled',JSON.stringify(['%s']));localStorage.setItem('class26e.greet.ifc','done');"
            "['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted'].forEach(k=>localStorage.setItem(k,'1'));}catch(e){}") % (s, s, cls, cls)
HASH = r"""() => { const hash = s => { let h = 2166136261; for(let i = 0; i < s.length; i++){ h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0).toString(16); };
  const out = { cls: window.NOVA_CLASS, h: {} }; BANNERS.forEach(b => { if(BANNER_ART[b.id]) out.h[b.id] = hash(bannerStaticSVG(b.id) || ''); }); return out; }"""
MEASURE = r"""(R9) => {
  const mount = id => { const box = document.createElement('div'); box.style.cssText = 'position:fixed;left:0;top:0;width:480px;height:180px;overflow:hidden;z-index:99999';
    box.innerHTML = bannerStaticSVG(id) || ''; document.body.appendChild(box); const sv = box.querySelector('svg'); if(sv){ sv.setAttribute('width', 480); sv.setAttribute('height', 180); sv.setAttribute('preserveAspectRatio', 'none'); } return box; };
  const R = e => { const r = e.getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height, r: r.right, b: r.bottom, cx: r.left + r.width / 2, cy: r.top + r.height / 2 }; };
  const r1 = v => Math.round(v * 10) / 10, all = (b, sel) => [...b.querySelectorAll(sel)], nums = d => (d.match(/-?\d+\.?\d*/g) || []).map(Number);
  const rgb = h => { const m = /^#([0-9a-f]{6})$/i.exec(h || ''); if(!m) return null; const n = parseInt(m[1], 16); return [n >> 16, n >> 8 & 255, n & 255]; };
  const layers = id => { try{ const a = BANNER_ART[id]('gq'); return Array.isArray(a) ? a : []; }catch(e){ return []; } };
  const lstr = id => layers(id).map(l => (l.svg || '') + (l.kids || []).map(k => k.svg || '').join('')).join('');
  const out = { err: '' }, ids = Object.keys(IFC_BANNER_ART);
  /* 2. the look */
  try{ out.A = { per: {}, bad: [], caps: {}, hats: {} };
    ids.forEach(id => { const b = mount(id), offs = all(b, '.fb-officer'); out.A.per[id] = offs.length;
      offs.forEach((o, i) => { const back = o.classList.contains('fb-back'), hat = o.querySelector('.fb-cowboy'), hc = rgb(hat && hat.getAttribute('data-col'));
        const shirt = o.querySelector('.fb-polo'), sc = rgb(shirt && shirt.getAttribute('fill')), vest = o.querySelector('.fb-tacvest'), vc = rgb(vest && vest.getAttribute('data-col'));
        const brown = !!hc && hc[0] > hc[2] + 12 && hc[0] < 120 && hc[1] < 90;
        const navy = !!sc && sc[2] > sc[0] + 25 && sc[2] < 110;
        const blue = !!vc && !!sc && vc[2] > 140 && vc[2] > vc[0] + 80 && vc[2] - sc[2] > 50;
        const face = back || (!!o.querySelector('.fb-shades') && !!o.querySelector('.fb-stubble'));
        if(!(brown && navy && blue && face)) out.A.bad.push([id, i, { brown, navy, blue, face }]); });
      const caps = all(b, '.fb-cap').length; if(caps) out.A.caps[id] = caps;
      const gh = all(b, '.fb-gearhat').length; if(gh) out.A.hats[id] = gh;
      b.remove(); }); }catch(e){ out.err += 'A ' + String(e).slice(0, 120) + ' '; }
  /* 3. downpour */
  try{ const b = mount('correct5000'), ls = lstr('correct5000'), open = all(b, '.fb-headopen').map(R), shut = all(b, '.fb-head').filter(h => !h.classList.contains('fb-headopen')), art = layers('correct5000');
    const fire = art.filter(l => /bl-flame/.test(l.cls || '')).map(l => l.o), spray = art.filter(l => /bl-out/.test(l.cls || '')).map(l => l.o);
    out.D = { can: /gqcan/.test(ls), open: open.length, shut: shut.length, bulbs: shut.filter(h => h.querySelector('.fb-bulb')).length, openBulb: all(b, '.fb-headopen .fb-bulb').length,
      fireUnder: open.length === 1 && fire.length > 0 && fire.every(o => Math.abs(o[0] - open[0].cx) < 34 && o[1] > open[0].b + 40),
      sprayFrom: open.length === 1 && spray.length >= 2 && spray.every(o => Math.abs(o[0] - open[0].cx) < 2 && Math.abs(o[1] - open[0].b) < 4) }; b.remove(); }catch(e){ out.err += 'D ' + String(e).slice(0, 120) + ' '; }
  /* 4. after hours */
  try{ const b = mount('early10'), lines = all(b, '.fb-gaugeline').map(R), tag = b.querySelector('.fb-tag'), T = tag && R(tag), str = b.querySelector('.fb-string'), sn = str ? nums(str.getAttribute('d')) : [], hole = b.querySelector('.fb-hole'), Ho = hole && R(hole);
    const bm = b.querySelector('.fb-beam'), lens = b.querySelector('.fb-lens'), L = lens && R(lens), bn = bm ? nums(bm.getAttribute('d')) : [], Bm = bm && R(bm);
    const onLine = sn.length && lines.some(l => sn[0] >= l.x - 3 && sn[0] <= l.r + 3 && sn[1] >= l.y - 4 && sn[1] <= l.b + 4);
    const off = b.querySelector('.fb-officer');
    out.H = { plates: all(b, '.fb-riserplate').length, wheels: all(b, '.fb-wheel').length, gauges: all(b, '.fb-gauge').length, lines: lines.length, onLine: !!onLine,
      toHole: Ho && sn.length ? r1(Math.min.apply(null, [0, 2].map(k => Math.hypot(sn[sn.length - 2 - k * 0] - Ho.cx, sn[sn.length - 1] - Ho.cy)))) : null,
      below: !!(T && sn.length && T.y > sn[1] - 6), lensToBeam: L && bn.length ? r1(Math.hypot(L.cx - bn[0], L.cy - (bn[1] + bn[bn.length - 1]) / 2)) : null,
      tagLit: !!(Bm && T && T.cx >= Bm.x && T.cx <= Bm.r && T.cy >= Bm.y && T.cy <= Bm.b), hat: !!(off && off.querySelector('.fb-cowboy')), wire: lines.length ? 'ok' : '' }; b.remove(); }catch(e){ out.err += 'H ' + String(e).slice(0, 120) + ' '; }
  /* 5. top floor */
  try{ const b = mount('level80'), ls = lstr('level80'), tw = all(b, '.fb-tower').map(R);
    out.T = { door: all(b, '.fb-door, .fb-stairsign, .fb-floor80').length, exit: ls.indexOf(fbTextPath('EXIT', 39, 55.6, 6)) >= 0, towers: tw.length, spanL: tw.length ? r1(Math.min.apply(null, tw.map(t => t.x))) : null, spanR: tw.length ? r1(Math.max.apply(null, tw.map(t => t.r))) : null,
      officers: all(b, '.fb-officer').length, back: all(b, '.fb-officer.fb-back').length }; b.remove(); }catch(e){ out.err += 'T ' + String(e).slice(0, 120) + ' '; }
  /* 6. inspection team */
  try{ const b = mount('tests500'), ls = lstr('tests500'), offs = all(b, '.fb-officer').map(o => ({ cx: R(o).cx, feet: R(o.querySelector('.fb-pants')).b, board: !!o.querySelector('.fb-board') })).sort((p, q) => q.feet - p.feet);
    const lenses = all(b, '.fb-lens').map(R), beams = [];
    layers('tests500').forEach(l => (l.svg || '').replace(/class="fb-beam" d="([^"]*)"/g, (m, d) => { const n = nums(d); beams.push([(n[0] + n[n.length - 2]) / 2, (n[1] + n[n.length - 1]) / 2]); }));
    out.I = { n: offs.length, feet: offs.map(o => r1(o.feet)), leadBoard: offs.length ? offs[0].board : false, beams: beams.length, lensToBeam: beams.map(p => lenses.length ? r1(Math.min.apply(null, lenses.map(l => Math.hypot(l.cx - p[0], l.cy - p[1])))) : 99),
      windows: all(b, '.fb-window').length, racks: /fill="#E0621E"/.test(b.innerHTML) }; b.remove(); }catch(e){ out.err += 'I ' + String(e).slice(0, 120) + ' '; }
  /* 7. the flares: pairwise shared long shapes, colours */
  try{ const fl = ['flare_void', 'flare_umbra', 'flare_horizon', 'flare_genesis'];
    const longs = id => { const s = new Set(); const d = document.createElement('div'); d.innerHTML = (bannerStaticSVG(id) || '') + '<svg>' + lstr(id) + '</svg>'; d.querySelectorAll('path').forEach(p => { const v = p.getAttribute('d') || ''; if(v.length > 60) s.add(v); }); return s; };
    const L = fl.map(longs), pairs = [];
    for(let i = 0; i < 4; i++) for(let j = i + 1; j < 4; j++){ const n = [...L[i]].filter(v => L[j].has(v)).length; if(n) pairs.push([fl[i], fl[j], n]); }
    const C = {}; fl.forEach(id => C[id] = ((bannerStaticSVG(id) || '') + lstr(id)).toUpperCase());
    out.F = { pairs, colours: ['#EF4444', '#F97316', '#FACC15'].every(c => C.flare_void.indexOf(c) >= 0) && C.flare_umbra.indexOf('#8B5CF6') >= 0 && C.flare_horizon.indexOf('#CFEAFF') >= 0 && C.flare_genesis.indexOf('#FF5CA8') >= 0 }; }catch(e){ out.err += 'F ' + String(e).slice(0, 120) + ' '; }
  /* 8. hygiene */
  try{ out.W = {}; out.bad = [];
    R9.forEach(id => { const x = buildBannerArt(id), y = buildBannerArt(id); out.W[id] = [x.querySelectorAll('*').length, x.querySelectorAll('.bnl').length];
      const ia = new Set([...x.querySelectorAll('[id]')].map(e => e.id)); if([...y.querySelectorAll('[id]')].some(e => ia.has(e.id))) out.bad.push(id + ' ids');
      const refs = (x.innerHTML.match(/url\(#([^)]+)\)/g) || []).map(m => m.slice(5, -1)); if(refs.some(r => !ia.has(r))) out.bad.push(id + ' url');
      if(/<filter|filter=/.test(x.innerHTML + lstr(id))) out.bad.push(id + ' filter'); }); }catch(e){ out.err += 'W ' + String(e).slice(0, 120) + ' '; }
  return out;
}"""
srv, port = rc["serve"]()
res = {}
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    for cls in ("ifc", "academy"):
        ctx = br.new_context(viewport={"width": 440, "height": 956}); pg = ctx.new_page(); perr = []
        pg.on("pageerror", lambda e: perr.append(str(e)[:200]))
        pg.add_init_script(init(cls))
        if BODY is not None:
            pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
        pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(3000)
        pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
        res[cls] = pg.evaluate(HASH); res[cls]["perr"] = perr
        if cls == "ifc" and not DUMP: res["m"] = pg.evaluate(MEASURE, R9)
        ctx.close()
    br.close()
srv.shutdown()
if DUMP:
    json.dump({"ifc": res["ifc"]["h"], "academy": res["academy"]["h"]}, open(PREVF, "w"), indent=1); print("wrote", PREVF); sys.exit(0)
PREV = json.load(open(PREVF))
chk("(0) the two classes load as themselves (%s, %s) with no page error (%s)" % (res["ifc"]["cls"], res["academy"]["cls"], res["ifc"]["perr"] + res["academy"]["perr"]),
    res["ifc"]["cls"] == "ifc" and res["academy"]["cls"] == "academy" and not res["ifc"]["perr"] and not res["academy"]["perr"])
H = res["ifc"]["h"]
same = [i for i in R9 if H.get(i) == PREV["ifc"].get(i)]
chk("(1) the eleven round 9 banners differ from cd82880 (unchanged: %s)" % same, not same and all(i in H for i in R9), same)
moved = [i for i in PREV["ifc"] if i not in R9 and H.get(i) != PREV["ifc"][i]]
chk("(1) every other Fire Code banner is exactly as cd82880 drew it (%d checked; moved: %s)" % (len([i for i in PREV["ifc"] if i not in R9]), moved), not moved and len(H) == len(PREV["ifc"]), moved)
A0 = res["academy"]["h"]; amoved = [i for i in PREV["academy"] if A0.get(i) != PREV["academy"][i]]
chk("(1) every academy banner is byte-identical to cd82880 (%d checked; moved: %s)" % (len(PREV["academy"]), amoved), not amoved and len(A0) == len(PREV["academy"]) and len(A0) > 15, amoved)
M = res["m"]; A = M.get("A") or {}; per = {k: v for k, v in (A.get("per") or {}).items() if v}
want = {"tests500": 3, "hundos250": 7, "level80": 1, "early10": 1}
chk("(2) THE INSPECTOR: the shared kit draws every inspector (%s; want %s)" % (per, want), per == want, per)
chk("(2) ...each in the dark brown cowboy hat, the dark glasses and stubble where his face shows, a navy shirt and a BLUE vest (wrong: %s)" % A.get("bad"), per and not A.get("bad"), A.get("bad"))
chk("(2) ...no ball cap anywhere in a Fire Code banner (%s); the hat off his head on the plans table and the gear wall (%s)" % (A.get("caps"), A.get("hats")),
    not A.get("caps") and (A.get("hats") or {}).get("tests250") == 1 and (A.get("hats") or {}).get("hundos100") == 1, (A.get("caps"), A.get("hats")))
D = M.get("D") or {}
chk("(3) DOWNPOUR: no wastebasket (%s); one head open (%s, no bulb in it: %s) and %s shut with their bulbs (%s); the fire under the open head (%s); the spray going out from its deflector (%s)" %
    (D.get("can"), D.get("open"), D.get("openBulb") == 0, D.get("shut"), D.get("bulbs"), D.get("fireUnder"), D.get("sprayFrom")),
    D and not D.get("can") and D.get("open") == 1 and D.get("openBulb") == 0 and D.get("shut", 0) >= 2 and D.get("bulbs") == D.get("shut") and D.get("fireUnder") and D.get("sprayFrom"), D)
Hh = M.get("H") or {}
chk("(4) AFTER HOURS: two risers (plates %s, handwheels %s, gauges %s, gauge lines %s)" % (Hh.get("plates"), Hh.get("wheels"), Hh.get("gauges"), Hh.get("lines")),
    Hh.get("plates") == 2 and Hh.get("wheels") == 2 and Hh.get("gauges") == 2 and Hh.get("lines") == 2, Hh)
chk("(4) ...the tag's wire starts on a gauge line (%s) and ends in its hole (%s units), the tag hanging below the line (%s); the beam starts at the lens (%s units) and lands on the tag (%s); the kneeling inspector wears the hat (%s)" %
    (Hh.get("onLine"), Hh.get("toHole"), Hh.get("below"), Hh.get("lensToBeam"), Hh.get("tagLit"), Hh.get("hat")),
    Hh.get("onLine") and Hh.get("toHole") is not None and Hh["toHole"] <= 3 and Hh.get("below") and Hh.get("lensToBeam") is not None and Hh["lensToBeam"] <= 4 and Hh.get("tagLit") and Hh.get("hat"), Hh)
T = M.get("T") or {}
chk("(5) TOP FLOOR: no door or stair sign (%s), no EXIT (%s); a skyline of %s towers from x %s to %s; one inspector from behind (%s / %s)" % (T.get("door"), T.get("exit"), T.get("towers"), T.get("spanL"), T.get("spanR"), T.get("officers"), T.get("back")),
    T and not T.get("door") and not T.get("exit") and T.get("towers", 0) >= 12 and T.get("spanL", 99) < 30 and T.get("spanR", 0) > 450 and T.get("officers") == 1 and T.get("back") == 1, T)
I = M.get("I") or {}; fe = I.get("feet") or [0]
chk("(6) INSPECTION TEAM: %s inspectors at three depths (feet %s: the lead lower by %s), the lead with his clipboard (%s), %s beams from their lenses (%s), no lit building windows (%s), the racks (%s)" %
    (I.get("n"), fe, round(fe[0] - max(fe[1:] or [0]), 1), I.get("leadBoard"), I.get("beams"), I.get("lensToBeam"), I.get("windows"), I.get("racks")),
    I.get("n") == 3 and fe[0] - max(fe[1:]) >= 8 and I.get("leadBoard") and I.get("beams") == 2 and max(I.get("lensToBeam") or [99]) <= 4 and not I.get("windows") and I.get("racks"), I)
Fl = M.get("F") or {}
chk("(7) THE SECRET FLARES share no long shape between any two (%s) and each keeps its colour (%s)" % (Fl.get("pairs"), Fl.get("colours")), Fl and not Fl.get("pairs") and Fl.get("colours"), Fl)
W = M.get("W") or {}; heavy = {k: v for k, v in W.items() if v[0] > 700 or v[1] > 24}
chk("(8) no filter, id clash or unresolved url in the round 9 banners (%s); none heavier than 700 elements or 24 layers (%s)" % (M.get("bad"), W), W and not M.get("bad") and not heavy, (M.get("bad"), heavy))
chk("(8) the measurements ran without a page error (%s)" % M.get("err"), not M.get("err"), M.get("err"))
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
