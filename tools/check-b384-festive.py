#!/usr/bin/env python3
"""384 festive: the seasons on Home. Madison: "On thanksgiving can we add some thanksgiving spirit somehow on the main menu? ... when
December first hits, it will be Christmas festive themed and that will last till new years which will have new years stuff and then
after new years say like January 2nd it will go back to normal. We have to make this super cool and fun though."
The season is forced with the preview key (localStorage "class26e.season": a season's name or a local date and time; the clock is
moved there and runs on). iPhone 17 Pro Max (440x956), installed, both classes. Read off the page, by shape:
 (1) THE CALENDAR, by what Home shows for a forced date: nothing on Nov 22 2026 and Jan 2; Thanksgiving from the Monday of
     Thanksgiving week (the fourth Thursday, worked out here for 2026-2030) to Nov 30, its day marked on the fourth Thursday only;
     Christmas Dec 1 - 30 (Dec 24 and 25 marked); New Year's Dec 31 and Jan 1 (each marked);
 (2) both classes read the one device key (Fire Code maps its own keys, not this one); each season, in each class, puts on Home: a sky layer with its falling / bursting pieces, a hat in the planet's box, a dressing
     on the outer ring - three different pictures for the three seasons - and a normal date puts on nothing at all;
 (3) NOTHING TAKES A TOUCH: every festive element computes pointer-events none; the point in the middle of each of Home's controls
     (Start Studying, the daily question, the class button, the chat button, the tab bar's buttons, the planet, each rank bubble)
     hits the same element with the season on as with it off; and the controls stand where they stood (within .5px);
 (4) a real click on Start Studying still leaves Home; a real click on the planet still gives the planet's caption, and the
     season's throw runs (leaves, the sleigh, confetti), every piece of it transform and opacity only;
 (5) THE SKY MOVES ON THE COMPOSITOR: the pieces animate (a piece's transform changes over 600ms), and every animation on a festive
     element animates transform and opacity only;
 (6) REDUCE MOTION (the app's switch, and the system's setting): no animation runs on any festive element, the pieces are on the
     glass (opacity > 0) and do not move over 700ms, the hat and the ring are there, and a planet tap throws nothing;
 (7) LEFT ON NAVIGATION: Profile, Settings and a mode select have no festive element in the document and no animation on one; Home
     built twice has one sky, one hat, one ring;
 (8) MIDNIGHT WITH HOME UP: Nov 30 23:59:57 -> Thanksgiving, and three seconds later Christmas, with no new Home; Dec 31 23:59:51 ->
     the greeting counts down to the next year (its number read off the page), the last seconds stand over the planet, and at
     midnight the year is shown over the planet and the greeting and the day turn to the new year;
 (9) the days' greetings differ from the ordinary greeting, and Jan 2's is the ordinary one;
 (11) OPEN SKY ONLY (round 2 - Madison saw a burst over the chat button and one over the greeting): on an iPhone 17 Pro Max in both
     classes, an SE, and an iPad upright and turned, New Year's Eve, its countdown and New Year's Day, many frames apart: no visible
     burst or flash (a circle of its drawn size) touches a control (Start Studying, the daily question, the class button, the chat
     button, the tab bar) or Home's text (greeting, NOVA and tagline, the flares caption); the countdown and the year touch no
     control; Thanksgiving's leaves, the snow, the leaf swirl and the confetti: none visible is ever over the tab bar, and wherever
     one crosses another control the control is painted over it (elementsFromPoint, the pieces made hit-testable for the read).
 (12) NO HAT IS SEEN THROUGH (round 3 - Madison: "All the hats can be seen through to the planet"): at 3x on the Pro Max in both
     classes and on the iPad, for each hat, every animation paused: the hat's own pixels (hat shown vs hidden, its contact shadow
     off, eroded 4px off its edge) do not change at all when everything else in the planet's box is recoloured (inverted and
     turned) - so nothing of the planet shows through any part and nothing of it paints over the hat; again just after a tap on
     the planet (its press and ripple), on the Pro Max.
 (13) THE GLASS IN FRONT, THE RINGS CLEAR (round 4 - Madison: "It should still be behind the flares so you can see the hats through the
     Liquid Glass"): for each hat (Pro Max both classes, iPad), each rank bubble and each orbit dot in turn is brought over the hat's
     middle (an added translate, its own animation left alone) and the hat made hit-testable for the read: at that point the orb (or a
     part of it) is above the hat in elementsFromPoint; and no part of any hat (its pixels, at 3x) reaches the inner ring (r108).
 (10) no page errors.
Run:  python3 tools/check-b384-festive.py   (--against OLD/index.html must FAIL)"""
import datetime, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b384fest"}
exec(src, G)
g = G["g"]
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = g["INSET_RE"]
    def _old(ins):
        t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
        return IR.sub(lambda m: v[m.group(1)], OLD)
    g["patched"] = _old
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)
CLEAN = ("try{ homeUnlocksOwed = () => false; }catch(e){} try{ maybeShowIntro = () => {}; }catch(e){} try{ scheduleHomeUnlocks = () => {}; playHomeUnlocks = () => {}; }catch(e){} "
         "document.querySelectorAll('.intro-popup,.daily-alert,#intro-pop,.nova-talk,.app-banner,.unlock-card,.rs-spot,.rs-fly').forEach(e=>e.remove());")
def page(br, cls, reduce=False, pre=None, vp=(440, 956), ins=(59, 0, 34, 0), dpr=1):
    ctx = br.new_context(viewport={"width": vp[0], "height": vp[1]}, device_scale_factor=dpr, has_touch=True, reduced_motion="reduce" if reduce else "no-preference")
    ctx.add_init_script("window.__cloudSeed = {};")
    ctx.add_init_script(G["FAKE"])
    ctx.add_init_script(g["STANDALONE"])
    ctx.add_init_script(G["init"](G["ifc"] if cls == "ifc" else G["academy"], active=cls))
    ctx.add_init_script("try{ localStorage.setItem('class26e.intro.seen', '99'); }catch(e){}")
    if pre: ctx.add_init_script("try{ localStorage.setItem('class26e.season', %s); }catch(e){}" % json.dumps(pre))
    ctx.add_init_script("try{ localStorage.setItem('class26e.weekrecap.v1','9999-12-31'); localStorage.setItem('class26e.ifc.weekrecap.v1','9999-12-31'); }catch(e){}")
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    body = g["patched"](ins)
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.goto(G["serve_url"]); pg.wait_for_timeout(3500)
    pg.evaluate("document.getElementById('splashscreen')?.remove()")
    return ctx, pg, errs
# the fixture's account is owed challenge cards (.rs-spot), which come up over Home a while after it is built: off before a tap
UNCOVER = "()=>document.querySelectorAll('.rs-spot,.rs-fly,.unlock-card,.intro-popup,.app-banner,.daily-alert,.nova-talk').forEach(e=>e.remove())"
def force(pg, val, wait=900):
    pg.evaluate("(v)=>{ if(v === null) localStorage.removeItem('class26e.season'); else localStorage.setItem('class26e.season', v); %s showHome(); }" % CLEAN, val)
    pg.wait_for_timeout(wait)
# what Home carries: the sky's season and day, its pieces, the hat, the ring; every element whose class starts fest-
STATE = """()=>{
  const sky = document.querySelectorAll('#stage > .fest-sky'), hero = document.querySelector('#stage .cosmic-hero-wrap');
  const s = sky[0] || null;
  const all = [...document.querySelectorAll('[class*="fest-"]')];
  return { skies: sky.length, season: s ? s.dataset.season || '' : null, day: s ? s.dataset.day || '' : null,
    leaves: s ? s.querySelectorAll('.fest-leaf').length : 0, snow: s ? s.querySelectorAll('.fest-snow').length : 0,
    bursts: s ? s.querySelectorAll('.fest-fw').length : 0,
    hats: hero ? hero.querySelectorAll('.fest-planet .fest-hat').length : 0, rings: hero ? hero.querySelectorAll('.fest-ring').length : 0,
    hatPic: hero && hero.querySelector('.fest-hat') ? hero.querySelector('.fest-hat').innerHTML.replace(/fest\\d+-/g, '').length : 0,
    festEls: all.length, greet: (document.querySelector('#stage .homegreeting') || {}).textContent || '' };
}"""
CONTROLS = """()=>{
  const sel = ['#nextbtn', '#stage .daily-question-fab', '.class-bubble', '#chatdock-btn', '.bottomtabs button, .bottomtabs a, nav button',
               '#stage .cosmic-hero-wrap .cosmic-badge-rank'];
  const out = [];
  sel.forEach(q => document.querySelectorAll(q).forEach((e, i) => { const r = e.getBoundingClientRect(); if(r.width < 4 || r.height < 4) return;
    const cx = r.left + r.width / 2, cy = r.top + r.height / 2; const hit = document.elementFromPoint(cx, cy);
    out.push({ q: q + '#' + i, rect: [r.left, r.top, r.width, r.height].map(v => Math.round(v * 2) / 2), hitSelf: !!hit && (hit === e || e.contains(hit)),
               hit: hit ? (hit.tagName + '.' + (typeof hit.className === 'string' ? hit.className : '')).slice(0, 60) : null }); }));
  const hw = document.querySelector('#stage .cosmic-hero-wrap'); const r = hw.getBoundingClientRect();
  const px = r.left + r.width / 2 + r.width * .06, py = r.top + r.height * .47368 + r.width * .07; const hp = document.elementFromPoint(px, py);
  out.push({ q: 'planet', rect: [Math.round(px), Math.round(py)], hitSelf: !!hp && !/fest-/.test(hp.className && hp.className.baseVal !== undefined ? hp.className.baseVal : hp.className || ''),
             hit: hp ? (hp.tagName + '.' + (hp.className && hp.className.baseVal !== undefined ? hp.className.baseVal : hp.className || '')).slice(0, 60) : null });
  return out;
}"""
FESTANIMS = """()=>{
  const anims = document.getAnimations().filter(a => { const t = a.effect && a.effect.target; return t && t.closest && t.closest('[class*="fest-"]'); });
  const props = new Set(); anims.forEach(a => { try{ a.effect.getKeyframes().forEach(k => Object.keys(k).forEach(p => { if(!['offset', 'easing', 'composite', 'computedOffset'].includes(p)) props.add(p); })); }catch(e){} });
  return { n: anims.length, running: anims.filter(a => a.playState === 'running').length, props: [...props] };
}"""
PIECE = """()=>{ const p = document.querySelector('#stage > .fest-sky .fest-p, #stage > .fest-sky .fest-fw-burst'); if(!p) return null;
  const c = getComputedStyle(p); let o = 1, n = p; while(n && n !== document.documentElement){ o *= +getComputedStyle(n).opacity; n = n.parentElement; }
  const r = p.getBoundingClientRect(); return { tf: c.transform, op: o, box: [r.left, r.top, r.width, r.height].map(v => Math.round(v)) }; }"""
POINTER = """()=>[...document.querySelectorAll('[class*="fest-"], [class*="fest-"] *')].filter(e => getComputedStyle(e).pointerEvents !== 'none').map(e => e.tagName + '.' + (e.className && e.className.baseVal !== undefined ? e.className.baseVal : e.className)).slice(0, 6)"""

OPEN = r"""(phase)=>{
  const vis = e => { let o = 1, n = e; while(n && n !== document.documentElement){ const c = getComputedStyle(n); if(c.visibility === 'hidden' || c.display === 'none') return 0; o *= +c.opacity; n = n.parentElement; } return o; };
  const R = e => { const r = e.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; };
  const ctl = [], txt = [];
  ['#nextbtn', '#stage .daily-question-fab', '#stage .dq-card', '.class-bubble', '#chatdock-btn', '#bottomtabs'].forEach(q => document.querySelectorAll(q).forEach(e => { const r = e.getBoundingClientRect(); if(r.width > 2 && r.height > 2 && vis(e) > .05) ctl.push([q, R(e), e]); }));
  ['#stage .homegreeting', '#stage .hometitle-wrap', '#stage .home-caption'].forEach(q => document.querySelectorAll(q).forEach(e => { const r = e.getBoundingClientRect(); if(r.width > 2 && r.height > 2) txt.push([q, R(e)]); }));
  const circ = (cx, cy, rad, b) => { const nx = Math.max(b[0], Math.min(cx, b[2])), ny = Math.max(b[1], Math.min(cy, b[3])); return Math.hypot(nx - cx, ny - cy) < rad; };
  const hitBox = (a, b) => a[0] < b[2] && a[2] > b[0] && a[1] < b[3] && a[3] > b[1];
  const bad = [], seen = { bursts: 0, pieces: 0, big: 0 };
  document.querySelectorAll('#stage .fest-fw-burst, #stage .fest-fw-flash').forEach(e => {
    if(vis(e) < .03) return; seen.bursts++;
    const r = e.getBoundingClientRect(), cx = (r.left + r.right) / 2, cy = (r.top + r.bottom) / 2, rad = r.width / 2 * (e.classList.contains('fest-fw-burst') ? .95 : .8);
    ctl.concat(txt).forEach(([q, b]) => { if(circ(cx, cy, rad, b)) bad.push(['burst', q, [cx, cy, rad].map(Math.round)]); });
  });
  document.querySelectorAll('#stage .fest-count, #stage .fest-year').forEach(e => {
    if(vis(e) < .03) return; const t = e.querySelector('text'); if(!t) return; seen.big++;
    const b = R(t); ctl.forEach(([q, c]) => { if(hitBox(b, c)) bad.push(['year/count', q, b.map(Math.round)]); });
  });
  const st = document.createElement('style'); st.textContent = 'html body .fest-sky.fest-sky *{ pointer-events:auto !important; }'; document.body.appendChild(st);
  document.querySelectorAll('#stage .fest-p, #stage .fest-throw').forEach(e => {
    if(vis(e) < .05) return; seen.pieces++;
    const b = R(e);
    ctl.forEach(([q, c, el]) => {
      if(!hitBox(b, c)) return;
      if(q === '#bottomtabs'){ bad.push(['piece over the tab bar', e.className, b.map(Math.round)]); return; }
      /* the point of the overlap nearest the control's middle (a round button is not hit at its box's corners) */
      const mx = (c[0] + c[2]) / 2, my = (c[1] + c[3]) / 2;
      const x = Math.max(Math.max(b[0], c[0]), Math.min(mx, Math.min(b[2], c[2]))), y = Math.max(Math.max(b[1], c[1]), Math.min(my, Math.min(b[3], c[3])));
      const list = document.elementsFromPoint(x, y), ic = list.findIndex(n => el === n || el.contains(n)), ip = list.findIndex(n => e === n || e.contains(n));
      if(ip >= 0 && ic >= 0 && ip < ic) bad.push(['piece painted over', q, e.className, [x, y].map(Math.round)]);
    });
  });
  st.remove();
  return { bad: bad.slice(0, 6), nbad: bad.length, seen };
}"""

def see_through(pg, tap=False):
    # (384.137) a pop-up the account is owed (a challenge card, its dim) could land between the shots and darken the whole frame: the hat
    # then "changed" though the planet was all that was recoloured. A frame is only trusted when a patch outside the hero (the sky in the
    # clip's corner, which nothing here touches) is the same in every shot; otherwise the overlays are cleared again and it retries.
    for attempt in range(4):
        r = _see_through_once(pg, tap)
        if r.get("steady"): r.pop("steady", None); return r
        pg.evaluate(UNCOVER); pg.wait_for_timeout(1200)
    r.pop("steady", None); return r
def _see_through_once(pg, tap=False):
    import io
    import numpy as np
    from PIL import Image
    from scipy import ndimage
    pg.evaluate(UNCOVER)
    pg.evaluate("()=>document.querySelectorAll('#stage .fest-year, #stage .fest-count').forEach(e=>e.remove())")
    if tap:
        hp = [c for c in pg.evaluate(CONTROLS) if c["q"] == "planet"][0]["rect"]
        pg.mouse.click(hp[0], hp[1]); pg.wait_for_timeout(140)
    pg.evaluate("()=>document.getAnimations().forEach(a=>{ try{ a.pause(); }catch(e){} })")
    clip = pg.evaluate("""()=>{ const h=document.querySelector('#stage .cosmic-hero-wrap').getBoundingClientRect(); const cx=h.left+h.width/2, cy=h.top+h.height*.47368, w=h.width*.5;
      return {x:cx-w/2, y:cy-w*.8, width:w, height:w}; }""")
    shot = lambda: np.asarray(Image.open(io.BytesIO(pg.screenshot(clip=clip, scale="device"))).convert("RGB")).astype(int)
    a = shot()
    # (round 4) the PLANET's layers are recoloured - its glow, body, smoke, rings and the tap's press - not the glass orbs and orbit dots,
    # which pass in front of the hat by design (section 13 checks that they do)
    pg.evaluate("()=>{ const h=document.querySelector('#stage .cosmic-hero-wrap'); [...h.children].forEach(c=>{ if(!c.classList.contains('fest-planet') && !c.matches('.cosmic-icon-badge, .cosmic-hero-orbitlayer')) c.style.filter='invert(1) hue-rotate(90deg)'; }); }")
    b = shot()
    pg.evaluate("()=>{ const h=document.querySelector('#stage .cosmic-hero-wrap'); [...h.children].forEach(c=>c.style.filter=''); const sh=h.querySelector('.fest-hat-shadow'); if(sh) sh.style.display='none'; }")
    on = shot()
    pg.evaluate("()=>{ const p=document.querySelector('#stage .fest-planet'); if(p) p.style.visibility='hidden'; }")
    off = shot()
    pg.evaluate("()=>{ const p=document.querySelector('#stage .fest-planet'); if(p) p.style.visibility=''; const sh=document.querySelector('#stage .fest-hat-shadow'); if(sh) sh.style.display=''; document.getAnimations().forEach(a=>{ try{ a.play(); }catch(e){} }); }")
    hat = np.abs(on - off).sum(2) > 30
    core = ndimage.binary_erosion(hat, iterations=4)
    # (round 4) where a glass orb or an orbit dot is over the hat, the hat is seen THROUGH the glass, with the planet round it: those
    # pixels are the glass's (section 13 checks the orbs are on top), not the hat's
    orbs = pg.evaluate("""()=>[...document.querySelectorAll('#stage .cosmic-hero-wrap > .cosmic-icon-badge, #stage .cosmic-hero-wrap .cosmic-orbit-dot, #stage .cosmic-hero-wrap .cosmic-orbit-dot > *')]
      .map(e => { const r = e.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; }).filter(r => r[2] - r[0] > 2)""")
    sc = a.shape[1] / clip["width"]
    for (l, t, r_, b_) in orbs:
        x0, y0 = int((l - clip["x"]) * sc) - 12, int((t - clip["y"]) * sc) - 12
        x1, y1 = int((r_ - clip["x"]) * sc) + 12, int((b_ - clip["y"]) * sc) + 12
        core[max(0, y0):max(0, y1), max(0, x0):max(0, x1)] = False
    d = np.abs(a - b).sum(2)
    k = max(6, a.shape[0] // 20); corner = lambda x: x[:k, :k].mean(axis=(0, 1))
    steady = all(np.abs(corner(x) - corner(a)).sum() < 6 for x in (on, off)) and np.abs(corner(b) - corner(a)).sum() < 60
    return {"core": int(core.sum()), "through": int((d[core] > 12).sum()), "max": int(d[core].max()) if core.any() else None, "steady": bool(steady)}
def thanksgiving(y):
    d = datetime.date(y, 11, 1); first_thu = 1 + (3 - d.weekday()) % 7; return first_thu + 21
errs_all = []
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    # (1) the calendar
    ctx, pg, errs = page(br, "academy")
    want = []
    for y in (2026, 2027, 2028, 2029, 2030):
        tg = thanksgiving(y)
        want += [("%d-11-%02dT12:00" % (y, tg - 4), None, ""), ("%d-11-%02dT12:00" % (y, tg - 3), "thanksgiving", ""),
                 ("%d-11-%02dT12:00" % (y, tg), "thanksgiving", "thanksgiving-day"), ("%d-11-%02dT12:00" % (y, tg + 1), "thanksgiving", ""),
                 ("%d-11-30T23:00" % y, "thanksgiving", "")]
    want += [("2026-11-22T12:00", None, ""), ("2026-11-23T00:01", "thanksgiving", ""), ("2026-12-01T00:01", "christmas", ""), ("2026-12-12T12:00", "christmas", ""),
             ("2026-12-24T12:00", "christmas", "christmas-eve"), ("2026-12-25T12:00", "christmas", "christmas-day"), ("2026-12-30T23:30", "christmas", ""),
             ("2026-12-31T00:01", "newyear", "nye"), ("2027-01-01T12:00", "newyear", "newyears-day"), ("2027-01-02T00:01", None, ""), ("2027-03-10T12:00", None, "")]
    bad = []
    for at, season, day in want:
        force(pg, at, 250)
        st = pg.evaluate(STATE)
        got = (st["season"] or None, st["day"] or "")
        if got != (season, day): bad.append((at, got, (season, day)))
    chk("(1) the calendar: %d forced dates (Thanksgiving's Monday and Day worked out for 2026-2030), %d wrong" % (len(want), len(bad)), not bad, bad[:5])
    errs_all += errs; ctx.close()
    pics = {}
    # (2) the preview key is the DEVICE's: set as the address bar's console would (before the class's own storage map), both classes read it
    for cls in ("academy", "ifc"):
        ctx, pg, errs = page(br, cls, pre="christmas")
        pg.evaluate("()=>{ %s showHome(); }" % CLEAN); pg.wait_for_timeout(900)
        st = pg.evaluate(STATE)
        chk("(2) %s reads the device's own preview key (class26e.season, unmapped): %s" % (cls, st["season"]), st["season"] == "christmas", st)
        errs_all += errs; ctx.close()
    for cls in ("academy", "ifc"):
        ctx, pg, errs = page(br, cls)
        force(pg, "off", 1200)
        off = pg.evaluate(STATE); ctl_off = pg.evaluate(CONTROLS)
        chk("(2) %s, a normal date: nothing festive on the page (%d elements)" % (cls, off["festEls"]), off["festEls"] == 0 and off["skies"] == 0, off)
        for season in ("thanksgiving", "christmas", "newyear"):
            force(pg, {"newyear": "2026-12-31T20:00"}.get(season, season), 1400)
            st = pg.evaluate(STATE)
            pieces = {"thanksgiving": st["leaves"], "christmas": st["snow"], "newyear": st["bursts"]}[season]
            chk("(2) %s, %s: one sky (%d) of that season with its pieces (%d), a hat on the planet (%d) and the ring dressed (%d)" % (cls, season, st["skies"], pieces, st["hats"], st["rings"]),
                st["skies"] == 1 and st["season"] == season and pieces >= 6 and st["hats"] == 1 and st["rings"] == 1, st)
            pics.setdefault(cls, {})[season] = st["hatPic"]
            pe = pg.evaluate(POINTER)
            ctl = pg.evaluate(CONTROLS)
            moved = [(a["q"], a["rect"], b["rect"]) for a, b in zip(ctl_off, ctl) if a["q"] == b["q"] and a["q"] != "planet" and "cosmic-badge" not in a["q"] and max(abs(x - y) for x, y in zip(a["rect"], b["rect"])) > .5]
            stolen = [(c["q"], c["hit"]) for c in ctl if not c["hitSelf"]]
            was = {c["q"]: c["hitSelf"] for c in ctl_off}
            stolen = [s for s in stolen if was.get(s[0], True)]
            chk("(3) %s, %s: every festive element lets touches through (%s), %d controls hit as without it (%s taken), none moved (%s)" % (cls, season, pe or "all none", len(ctl), len(stolen), len(moved)),
                not pe and len(ctl) >= 8 and not stolen and not moved and len(ctl) == len(ctl_off), [pe, stolen, moved])
            fa = pg.evaluate(FESTANIMS)
            p1 = pg.evaluate(PIECE); pg.wait_for_timeout(600); p2 = pg.evaluate(PIECE)
            chk("(5) %s, %s: the pieces move (%s -> %s), %d animations, transform and opacity only (%s)" % (cls, season, p1 and p1["tf"][:40], p2 and p2["tf"][:40], fa["n"], fa["props"]),
                p1 and p2 and p1["tf"] != p2["tf"] and fa["running"] >= 6 and set(fa["props"]) <= {"transform", "opacity"}, [p1, p2, fa])
        chk("(2) %s: three seasons, three different hats" % cls, len(set(pics[cls].values())) == 3 and all(pics[cls].values()), pics[cls])
        # (4) taps
        if cls == "academy":
            for season in ("thanksgiving", "christmas", "newyear"):
                force(pg, {"newyear": "2026-12-31T20:00"}.get(season, season), 1200)
                pg.evaluate("()=>document.querySelectorAll('.homecaption, .home-caption').forEach(e=>e.remove())")
                hp = [c for c in pg.evaluate(CONTROLS) if c["q"] == "planet"][0]["rect"]
                cap0 = pg.evaluate("()=>document.querySelectorAll('[class*=caption]').length")
                over = pg.evaluate("(p)=>{ const n=document.elementFromPoint(p[0],p[1]); return n ? n.tagName+'.'+(n.className && n.className.baseVal!==undefined ? n.className.baseVal : n.className)+' in '+(n.closest('[id]')||{}).id : null; }", hp)
                pg.evaluate(UNCOVER); pg.mouse.click(hp[0], hp[1]); pg.wait_for_timeout(500)
                thrown = pg.evaluate("""()=>{ const a = document.getAnimations().filter(x => { const t = x.effect && x.effect.target; return t && t.closest && t.closest('.fest-throw, .fest-sleigh, .fest-fw'); });
                  const props = new Set(); a.forEach(x => { try{ x.effect.getKeyframes().forEach(k => Object.keys(k).forEach(p => { if(!['offset','easing','composite','computedOffset'].includes(p)) props.add(p); })); }catch(e){} });
                  return { n: a.filter(x => x.playState === 'running' && x.effect.getTiming().iterations !== Infinity).length, props: [...props], caption: document.querySelectorAll('[class*=caption]').length }; }""")
                chk("(4) %s: a real click on the planet still gives its caption (%d -> %d) and throws the season's pieces (%d animations: %s)" % (season, cap0, thrown["caption"], thrown["n"], thrown["props"]),
                    thrown["caption"] > cap0 and thrown["n"] >= 5 and set(thrown["props"]) <= {"transform", "opacity"}, [thrown, over])
            force(pg, "christmas", 1000)
            b = pg.evaluate("()=>{ const r = document.querySelector('#nextbtn').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }")
            pg.evaluate(UNCOVER); pg.mouse.click(b[0], b[1]); pg.wait_for_timeout(900)
            left = pg.evaluate("()=>({ home: !!document.querySelector('#stage [data-screen=\"home\"]'), fest: document.querySelectorAll('[class*=\"fest-\"]').length })")
            chk("(4) a real click on Start Studying leaves Home (%s), and nothing festive is left (%d)" % (not left["home"], left["fest"]), not left["home"] and left["fest"] == 0, left)
            # (7) navigation
            gone = []
            for js in ("showProfile('profile')", "showAppearance()", "showModeSelect()"):
                force(pg, "newyear", 900)
                pg.evaluate("()=>{ %s %s; }" % (CLEAN, js)); pg.wait_for_timeout(900)
                r = pg.evaluate("()=>({ els: document.querySelectorAll('[class*=\"fest-\"]').length, anims: document.getAnimations().filter(a => { const t = a.effect && a.effect.target; return t && (!t.isConnected || (t.closest && t.closest('[class*=\"fest-\"]'))); }).filter(a => a.playState === 'running').length })")
                if r["els"] or r["anims"]: gone.append((js, r))
            chk("(7) Profile, Settings and a mode select: no festive element and no animation on one (%s)" % (gone or "none"), not gone, gone)
            pg.evaluate("()=>{ localStorage.setItem('class26e.season', 'christmas'); %s showHome(); showHome(); }" % CLEAN); pg.wait_for_timeout(800)
            st = pg.evaluate(STATE)
            chk("(7) Home built twice: one sky, one hat, one ring (%d, %d, %d)" % (st["skies"], st["hats"], st["rings"]), st["skies"] == 1 and st["hats"] == 1 and st["rings"] == 1, st)
            # (9) the greetings
            gr = {}
            for at in ("2026-11-24T12:00", "2026-11-26T12:00", "2026-12-24T12:00", "2026-12-25T12:00", "2026-12-31T12:00", "2027-01-01T12:00", "2027-01-02T12:00"):
                force(pg, at, 200); gr[at] = pg.evaluate(STATE)["greet"]
            pg.evaluate("()=>localStorage.removeItem('class26e.season')")
            plain = pg.evaluate("()=>homeGreetingText()")
            days = [gr[k] for k in ("2026-11-26T12:00", "2026-12-24T12:00", "2026-12-25T12:00", "2026-12-31T12:00", "2027-01-01T12:00")]
            chk("(9) the five days' greetings are their own (%s) and an ordinary day's is the ordinary one (%r / %r)" % (days, gr["2026-11-24T12:00"], gr["2027-01-02T12:00"]),
                len(set(days)) == 5 and plain not in days and gr["2027-01-02T12:00"] == plain and gr["2026-11-24T12:00"] == plain, gr)
            # (8) midnight with Home up
            force(pg, "2026-11-30T23:59:57", 600)
            a = pg.evaluate(STATE); pg.wait_for_timeout(3600); b = pg.evaluate(STATE)
            chk("(8) Nov 30 23:59:57 is Thanksgiving (%s) and three seconds on, with no new Home, Christmas (%s, one sky %d, hat changed %s)" % (a["season"], b["season"], b["skies"], a["hatPic"] != b["hatPic"]),
                a["season"] == "thanksgiving" and b["season"] == "christmas" and b["skies"] == 1 and b["hats"] == 1 and a["hatPic"] != b["hatPic"], [a, b])
            force(pg, "2026-12-31T23:59:51", 300)
            seq = []
            for _ in range(26):
                seq.append(pg.evaluate("""()=>{ const s = document.querySelector('#stage > .fest-sky'); const c = document.querySelector('#stage .cosmic-hero-wrap .fest-count text');
                  const y = document.querySelector('#stage .cosmic-hero-wrap .fest-year text');
                  return { g: (document.querySelector('#stage .homegreeting') || {}).textContent || '', count: c ? c.textContent : null, year: y ? y.textContent : null, day: s ? s.dataset.day || '' : null }; }"""))
                pg.wait_for_timeout(500)
            nums = [int(m.group(1)) for x in seq for m in [re.search(r"(\d{4})", x["g"])] if m and x["day"] == "nye"]
            counts = sorted({int(x["count"]) for x in seq if x["count"] and x["count"].isdigit()})
            after = [x for x in seq if x["day"] == "newyears-day"]
            yr = [x["year"] for x in after if x["year"]]
            chk("(8) the last seconds of Dec 31: the greeting counts to %s, the seconds stand over the planet (%s), and at midnight %s is shown over the planet, the day turns (%d samples after) and the greeting with it (%r)" %
                (sorted(set(nums)), counts[:3] + ["..."] + counts[-2:] if len(counts) > 5 else counts, yr[:1], len(after), after[-1]["g"] if after else None),
                nums and set(nums) == {2027} and len(counts) >= 5 and counts[0] <= 2 and counts[-1] >= 6 and yr and yr[0] == "2027" and after and after[-1]["g"] != seq[0]["g"] and "2027" not in after[-1]["g"], seq[::4])
        errs_all += errs; ctx.close()
    # (6) Reduce motion: the app's switch, then the system's setting
    for how in ("switch", "system"):
        ctx, pg, errs = page(br, "academy", reduce=(how == "system"))
        if how == "switch":
            pg.evaluate("()=>{ theme.reduceMotion = true; applyTheme(); }")
        for season in ("thanksgiving", "christmas", "newyear"):
            force(pg, {"newyear": "2026-12-31T20:00"}.get(season, season), 1200)
            st = pg.evaluate(STATE); fa = pg.evaluate(FESTANIMS)
            p1 = pg.evaluate(PIECE); pg.wait_for_timeout(700); p2 = pg.evaluate(PIECE)
            hp = [c for c in pg.evaluate(CONTROLS) if c["q"] == "planet"][0]["rect"]
            pg.evaluate(UNCOVER); pg.mouse.click(hp[0], hp[1]); pg.wait_for_timeout(400)
            th = pg.evaluate("()=>document.getAnimations().filter(a => { const t = a.effect && a.effect.target; return t && t.closest && t.closest('.fest-throw, .fest-sleigh'); }).length")
            chk("(6) Reduce motion (%s), %s: no festive animation (%d), the pieces on the glass and still (opacity %s, %s), hat %d and ring %d, a planet tap throws nothing (%d)" %
                (how, season, fa["n"], p1 and round(p1["op"], 2), p1 and p2 and p1["box"] == p2["box"], st["hats"], st["rings"], th),
                fa["n"] == 0 and p1 and p2 and p1["op"] > .2 and p1["box"] == p2["box"] and p1["tf"] == p2["tf"] and st["hats"] == 1 and st["rings"] == 1 and th == 0, [fa, p1, p2, st, th])
        errs_all += errs; ctx.close()
    # (11) open sky only
    for (dev, vp, ins, cls) in (("Pro Max", (440, 956), (59, 0, 34, 0), "academy"), ("Pro Max", (440, 956), (59, 0, 34, 0), "ifc"), ("SE", (375, 667), (20, 0, 0, 0), "academy"),
                                ("iPad", (834, 1194), (24, 0, 20, 0), "academy"), ("iPad turned", (1194, 834), (24, 0, 20, 0), "academy")):
        ctx, pg, errs = page(br, cls, vp=vp, ins=ins)
        for scene, at, tap in (("Thanksgiving", "thanksgiving", True), ("Christmas", "christmas", False), ("New Year's Eve", "2026-12-31T20:00", True),
                               ("the countdown", "2026-12-31T23:59:52", False), ("New Year's Day", "newyear", False)):
            force(pg, at, 900)
            tot = {"bursts": 0, "pieces": 0, "big": 0}; bad = []
            for i in range(12):
                if tap and i == 3:
                    hp = [c for c in pg.evaluate(CONTROLS) if c["q"] == "planet"][0]["rect"]; pg.evaluate(UNCOVER); pg.mouse.click(hp[0], hp[1])
                r = pg.evaluate(OPEN, scene)
                for k in tot: tot[k] += r["seen"][k]
                bad += r["bad"]
                pg.wait_for_timeout(420)
            want = {"Thanksgiving": tot["pieces"] > 20, "Christmas": tot["pieces"] > 50, "New Year's Eve": tot["bursts"] >= 6,
                    "the countdown": tot["bursts"] >= 6 and tot["big"] >= 3, "New Year's Day": tot["bursts"] >= 6 and tot["big"] >= 3}[scene]
            chk("(11) %s %s, %s: over 12 frames, %d bursts, %d pieces, %d countdown/year seen - %d on a control or Home's text (%s)" % (dev, cls, scene, tot["bursts"], tot["pieces"], tot["big"], len(bad), bad[:2]),
                want and not bad, bad[:4])
        errs_all += errs; ctx.close()
    # (13) the glass in front of the hat; no ring crosses a hat
    ORB = """()=>{
      const h = document.querySelector('#stage .cosmic-hero-wrap'), hat = h && h.querySelector('.fest-planet .fest-hat');
      if(!hat) return { n: 0, under: ['no hat'], reach: null };
      document.getAnimations().forEach(a => { try{ a.pause(); }catch(e){} });
      const st = document.createElement('style'); st.textContent = 'html body .fest-planet.fest-planet, html body .fest-planet.fest-planet *, html body .cosmic-hero-orbitlayer.cosmic-hero-orbitlayer, html body .cosmic-hero-orbitlayer.cosmic-hero-orbitlayer *{ pointer-events:auto !important; }'; document.body.appendChild(st);
      const shape = hat.querySelector('g > path:not(.fest-hat-shadow)') || hat; const hr = shape.getBoundingClientRect();
      const cx = hr.left + hr.width / 2, cy = hr.top + hr.height * .55;
      const orbs = [...h.querySelectorAll(':scope > .cosmic-icon-badge, :scope > .cosmic-hero-orbitlayer .cosmic-orbit-dot')];
      const under = []; let n = 0;
      orbs.forEach(o => {
        const r = o.getBoundingClientRect(); if(r.width < 4) return;
        /* an orbit dot sits in a turned layer: its translate moves it in the layer's own axes - so the two axes are measured and the
           move that brings its middle onto the point is solved for */
        const was = o.style.translate;
        const mid = () => { const q = o.getBoundingClientRect(); return [q.left + q.width / 2, q.top + q.height / 2]; };
        const c0 = mid(); o.style.translate = '10px 0px'; const cx1 = mid(); o.style.translate = '0px 10px'; const cy1 = mid();
        const a11 = (cx1[0] - c0[0]) / 10, a21 = (cx1[1] - c0[1]) / 10, a12 = (cy1[0] - c0[0]) / 10, a22 = (cy1[1] - c0[1]) / 10, det = a11 * a22 - a12 * a21 || 1;
        const ex = cx - c0[0], ey = cy - c0[1];
        o.style.translate = ((a22 * ex - a12 * ey) / det) + 'px ' + ((-a21 * ex + a11 * ey) / det) + 'px';
        /* every point of a 7x7 grid over the orb where both the orb and the hat are hit: the orb must come first; at least one such point */
        const q = o.getBoundingClientRect(); let both = 0, bad = 0;
        for(let i = 1; i < 8; i++) for(let j = 1; j < 8; j++){
          const x = q.left + q.width * i / 8, y = q.top + q.height * j / 8;
          const list = document.elementsFromPoint(x, y); const io = list.findIndex(e => o === e || o.contains(e)), ih = list.findIndex(e => hat === e || hat.contains(e));
          if(io >= 0 && ih >= 0){ both++; if(ih < io) bad++; }
        }
        n++; if(!both || bad) under.push((o.className || '').toString().slice(0, 40) + ' over ' + both + ', under ' + bad);
        o.style.translate = was;
      });
      st.remove();
      document.getAnimations().forEach(a => { try{ a.play(); }catch(e){} });
      return { n, under: under.slice(0, 4) };
    }"""
    REACH = """()=>{ const h = document.querySelector('#stage .cosmic-hero-wrap'); const r = h.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height * .47368, r.width / 360]; }"""
    for (dev, vp, ins, cls, dpr) in (("Pro Max", (440, 956), (59, 0, 34, 0), "academy", 3), ("Pro Max", (440, 956), (59, 0, 34, 0), "ifc", 3), ("iPad", (834, 1194), (24, 0, 20, 0), "academy", 2)):
        ctx, pg, errs = page(br, cls, vp=vp, ins=ins, dpr=dpr)
        for name, at in (("the pilgrim hat", "thanksgiving"), ("the Santa hat", "christmas"), ("the party hat", "2026-12-31T20:00")):
            force(pg, at, 1300); pg.evaluate(UNCOVER)
            r = pg.evaluate(ORB)
            # how far the hat's own pixels reach from the planet's centre, in the hero's units
            import io as _io
            import numpy as np
            from PIL import Image
            c = pg.evaluate(REACH)
            box = {"x": c[0] - 115 * c[2], "y": c[1] - 115 * c[2], "width": 230 * c[2], "height": 230 * c[2]}
            pg.evaluate("()=>document.getAnimations().forEach(a=>{ try{ a.pause(); }catch(e){} })")
            on = np.asarray(Image.open(_io.BytesIO(pg.screenshot(clip=box, scale="device"))).convert("RGB")).astype(int)
            pg.evaluate("()=>{ const p=document.querySelector('#stage .fest-planet'); if(p) p.style.visibility='hidden'; }")
            off = np.asarray(Image.open(_io.BytesIO(pg.screenshot(clip=box, scale="device"))).convert("RGB")).astype(int)
            pg.evaluate("()=>{ const p=document.querySelector('#stage .fest-planet'); if(p) p.style.visibility=''; document.getAnimations().forEach(a=>{ try{ a.play(); }catch(e){} }); }")
            m = np.abs(on - off).sum(2) > 30
            ys, xs = np.nonzero(m); k = on.shape[1] / 230
            reach = float(np.max(np.hypot(xs / k - 115, ys / k - 115))) if len(xs) else 0
            chk("(13) %s %s, %s: every orb and orbit dot over the hat is above it (%d tried, %s under) and the hat reaches %.1f of the inner ring's 108" % (dev, cls, name, r["n"], r["under"] or "none", reach),
                r["n"] >= 6 and not r["under"] and 30 < reach < 104, [r, reach])
        errs_all += errs; ctx.close()
    # (12) no hat is seen through
    for (dev, vp, ins, cls, dpr) in (("Pro Max", (440, 956), (59, 0, 34, 0), "academy", 3), ("Pro Max", (440, 956), (59, 0, 34, 0), "ifc", 3), ("iPad", (834, 1194), (24, 0, 20, 0), "academy", 2)):
        ctx, pg, errs = page(br, cls, vp=vp, ins=ins, dpr=dpr)
        for name, at in (("the pilgrim hat", "thanksgiving"), ("the Santa hat", "christmas"), ("the party hat", "2026-12-31T20:00")):
            for tap in ((False, True) if (dev == "Pro Max" and cls == "academy") else (False,)):
                force(pg, at, 1300)
                r = see_through(pg, tap)
                chk("(12) %s %s, %s%s: %d of the hat's own pixels, %d change when the planet is recoloured (most %s)" % (dev, cls, name, " just after a tap" if tap else "", r["core"], r["through"], r["max"]),
                    r["core"] > 1500 and r["through"] == 0, r)
        errs_all += errs; ctx.close()
    br.close()
chk("(10) no page errors", not errs_all, errs_all[:3])
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
