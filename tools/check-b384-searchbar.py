#!/usr/bin/env python3
"""Build 384.111: every search field is one Apple capsule, Find me is its companion, and your row is found, not lit.

Madison, his Leaderboard beside Apple Music's Search tab: "The find me button stands out just a little bit, maybe cause it's not
color matched to the search bar? I feel like the search bar and the find me button don't have that Apple vibe, it's missing the
round edges and stuff." And of his own row (#2, washed lighter): "Notice in my leaderboard screenshot, I'm permanently highlighted,
don't do that. When I hit find me it'll flash or whatever."

SEARCH FIELDS - on every screen that has one (the Leaderboard, Choose your units and its Review variant, the Virtual Room's unit
picker, Review's question list, the Starred list in a unit's card), found by shape (an input of type search, or an input sharing a
wrapper with an svg glyph), on an iPhone 17 Pro Max, an iPad Pro 11", a 320x568 phone and a Pro Max on its side, both classes:
 (1) CAPSULE: every corner's drawn radius (min(radius, h/2, w/2)) is half the field's height; the same for the button on its line;
 (2) ONE FILL: every field's fill (computed background colour, no image) is one value on every screen, device and class, not
     transparent, and the button on the field's line has that same fill;
 (3) ONE HEIGHT, ONE LINE: the button on the field's line is the field's height and centred on the same line (within .5px);
 (4) TEXT: the field's text and its placeholder compute to 16px or more;
 (5) TAP TARGETS: the field and the button beside it are 44px or more each way; with a character typed, the clear (x) is shown,
     44x44, inside the field's box; the magnifier is inside the field, centred on its middle (within 1px);
 (6) NOTHING OVERFLOWS (all four devices; the 320px phone is the point): no sideways page scroll, the row inside the screen, the
     field and its button not overlapping, the button's label not clipped, the placeholder's words fit the field's text box.
YOUR ROW - academy (three boards; fixture: twenty classmates, you 3rd on This Week, 15th on Hundos), Pro Max and iPad:
 (7) AT REST your row is drawn like its neighbours: on Hundos (you in the list) its background (computed colour + image, and the
     pixels at its corners) equals the rows above and below it; on This Week (you 3rd) it equals third place's on Hundos, held by
     someone else - the bronze tint survives, no wash;
 (8) FIND ME FLASHES IT, AS DRAWN (every frame for 2.3s, on This Week and on Hundos): an overlay inside your row (a box covering the
     row's box within 1px, found by shape) shows with opacity > 0 within 300ms of the tap - or, where the page drew no frame for 250ms+
     before it (this sandbox under load draws frames seconds apart, and then the wall clock measures the machine), in whatever frame came;
     it is 0 (or gone) by the end; the row's own background never changes (the tint underneath survives); the row ends up on screen
     (on Hundos it starts below the fold). AND ON ITS OWN CLOCK (the tap and every reading in one task, so no frame or timer comes
     between): the overlay exists the moment Find me returns, its opacity is > 0 by 300ms, and it is 0 at its end, 2s or sooner;
 (9) AGAIN: held at 700ms (fading), a second tap leaves one overlay - the old one gone - whose clock is at its start and whose tint is
     back above the 700ms value by more than .2, and 0 at its end, 2s or sooner;
(10) REDUCE MOTION (Pro Max): the tint is there at once (at 0ms of its clock, >= .8 of its peak - no rise), 0 at its end, 2s or sooner,
     and the row never moves (transform none on every frame drawn).
(11) no page errors.
  python3 tools/check-b384-searchbar.py [--against OLD/index.html]     (origin/main 384.95 must FAIL (1), (2), (7), (8))
  SB_DEVS=promax,se1 / SB_CLASSES=academy run a part."""
import io, json, os, re, sys, math
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
from playwright.sync_api import sync_playwright
from PIL import Image
SRC = sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else os.path.join(ROOT, "index.html")
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:700], flush=True)

ME = "pubme000sbar"
NAMES = ["Avery", "Logan", "Sam", "Matt", "Cody", "Dana", "Rookie", "Jordan", "Riley", "Quinn", "Taylor", "Morgan", "Reese", "Parker",
         "Drew", "Skyler", "Rowan", "Emerson", "Hayden"]
CHARS = ["detective", "wizard", "ghost", "grizzly", "ghost", "alien", "ghost", "ninja", "ghost", "alien", "wizard", "ghost", "grizzly",
         "ghost", "alien", "ghost", "wizard", "ghost", "ghost"]
WK = g["week_key_now"]()
# you (the seed): 640 XP this week, 234 hundos. Two classmates above you this week, fourteen above you on hundos.
ROWS = []
for i, (n, a) in enumerate(zip(NAMES, CHARS)):
    p = "pubsbar%05d" % (i + 1)
    ROWS.append({"code": p, "pub": p, "publicId": p, "firstName": n, "avatarChar": a, "level": max(1, 40 - i * 2), "badges": max(0, 10 - i),
                 "hundos": (400 - i * 10) if i < 14 else (100 - i), "correct": 3000 - i * 100, "week": WK,
                 "weekPoints": (900 - i * 120) if i < 2 else max(10, 600 - i * 25)})
lb = open(os.path.join(HERE, "check-b384-lbclean.py")).read()
FAKE = re.search(r'FAKE = """(.*?)""" % json.dumps\(ROWS\)', lb, re.S).group(1) % json.dumps(ROWS)
# name, w, h, insets (t, r, b, l), dpr
DEVS = [("promax", 440, 956, (62, 0, 34, 0), 3), ("ipad11", 834, 1194, (24, 0, 20, 0), 2), ("se1", 320, 568, (20, 0, 0, 0), 2),
        ("promaxL", 956, 440, (0, 62, 21, 62), 3)]
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1"

def seed(cls):
    d = json.loads(g["SEED"].replace("__WEEK__", WK)); d["publicId"] = ME; d["firstName"] = "Casey"
    d["classes"] = ["academy", "ifc"] if cls == "ifc" else ["academy"]
    return json.dumps(d)

# ---- the screens, opened the way the app opens them (a unit's card from a real unit row on Choose your units) ----
OPEN = r"""async (which) => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const quiet = () => { [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click());
    document.querySelectorAll('.daily-alert,.toast').forEach(n=>n.remove()); };
  try{ document.querySelectorAll('.unitdetail, .unitdetail-scrim').forEach(n => n.remove()); unitDetailOpen = false; }catch(e){}
  const flag = (unit, n) => { let k = 0; QUESTIONS.forEach((q, i) => { if(k < n && (q.topic || '').trim() === unit){ store.flagged[KEYS[i]] = Date.now(); k++; } }); };
  if(which === 'board'){ store.seenRewardsTour = true; showRankings(rankingBoardsFor()[0].key); }
  else if(which === 'units'){ cfg.mode = 'drill'; cfg.units = []; showSetup(); }
  else if(which === 'units-review'){ cfg.mode = 'review'; cfg.units = []; showSetup(); }
  else if(which === 'room'){ showVirtualRoomSetup(); }
  else if(which === 'review'){ const u = unitsInTeachingOrder().slice(0, 2); u.forEach(x => flag(x, 3)); showAnswerReview(u, 'flagged', {}, { allFlagged: true }); }
  else if(which === 'starred'){
    cfg.mode = 'drill'; cfg.units = []; showSetup(); await wait(900);
    const row = document.querySelector('#stage label.pick'); const name = row && row.querySelector('input').value;
    flag(name, 3); openUnitDetail(row, name, cfg.mode); await wait(1100);
    const d = document.querySelector('.unitdetail-door.is-flagged'); if(d) d.click();
  }
  await wait(1300); quiet(); window.scrollTo({ top: 0, behavior: 'instant' });
  /* Review's own field stands down while the tab bar's search is up (registerTabSearch); it is measured as drawn where it shows */
  if(which === 'review'){ const w = [...document.querySelectorAll('#stage .searchwrap')].find(x => x.querySelector('input')); if(w && w.hidden){ w.hidden = false; w.dataset.sbShown = '1'; } }
  await wait(300);
  return true; }"""

# every search field on the page, found by shape: a text-entry input that is type=search or shares its wrapper with an svg glyph
FIND = r"""const sbFields = () => [...document.querySelectorAll('input')].filter(i => { const b = i.getBoundingClientRect(), s = getComputedStyle(i);
    return b.width > 0 && b.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && /^(search|text|)$/.test(i.type)
      && (i.type === 'search' || (i.parentElement && i.parentElement.querySelector(':scope > svg'))) && !i.closest('#tabsearch'); });"""
# ... and what sits beside it
READ = r"""() => { """ + FIND + r"""
  const R = e => e.getBoundingClientRect(), cs = (e, p) => getComputedStyle(e, p || null), px = v => parseFloat(v) || 0;
  const shown = e => { const b = R(e), s = cs(e); return b.width > 0 && b.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  const fields = sbFields();
  const rad = (e) => { const b = R(e), s = cs(e); return ['TopLeft', 'TopRight', 'BottomLeft', 'BottomRight'].map(k => Math.min(px(s['border' + k + 'Radius']), b.height / 2, b.width / 2)); };
  const textW = (i) => { const c = document.createElement('canvas').getContext('2d'); const s = cs(i); c.font = s.fontWeight + ' ' + s.fontSize + ' ' + s.fontFamily; return c.measureText(i.placeholder || '').width; };
  return { vw: innerWidth, docW: document.scrollingElement.scrollWidth, fields: fields.map(f => {
    const b = R(f), s = cs(f), ph = cs(f, '::placeholder'); const wrap = f.parentElement;
    const glyph = wrap.querySelector(':scope > svg');
    /* the button on the field's line: a button that is a sibling of the field's wrapper (not the field's own clear) and level with it */
    const row = wrap.parentElement; let comp = null;
    if(row){ comp = [...row.children].filter(x => x !== wrap && x.tagName === 'BUTTON' && shown(x)).find(x => Math.abs((R(x).top + R(x).bottom) / 2 - (b.top + b.bottom) / 2) < b.height / 2) || null; }
    const cb = comp ? R(comp) : null, ccs = comp ? cs(comp) : null;
    return { cls: f.className, type: f.type, x: b.left, r: b.right, t: b.top, bt: b.bottom, w: b.width, h: b.height, rad: rad(f), fill: s.backgroundColor, img: s.backgroundImage,
      fs: px(s.fontSize), phfs: px(ph.fontSize), cw: f.clientWidth, padL: px(s.paddingLeft), padR: px(s.paddingRight), phW: textW(f),
      glyph: glyph ? (() => { const g = R(glyph); return { l: g.left, r: g.right, t: g.top, b: g.bottom }; })() : null,
      comp: comp ? { cls: comp.className, x: cb.left, r: cb.right, t: cb.top, b: cb.bottom, w: cb.width, h: cb.height, rad: rad(comp), fill: ccs.backgroundColor, img: ccs.backgroundImage,
        clipped: comp.scrollWidth > comp.clientWidth + 1 } : null }; }) }; }"""

# type one character into each field, read the clear button that appears, then clear it again
CLEAR = r"""async () => { """ + FIND + r"""
  const wait = ms => new Promise(r => setTimeout(r, ms)); const out = [];
  const fields = sbFields();
  for(const f of fields){
    f.value = 'q'; f.dispatchEvent(new Event('input', { bubbles: true })); await wait(250);
    const fb = f.getBoundingClientRect();
    const btn = [...f.parentElement.querySelectorAll(':scope > button')].find(x => { const b = x.getBoundingClientRect(); return b.width > 0 && b.height > 0; });
    const bb = btn ? btn.getBoundingClientRect() : null;
    out.push({ cls: f.className, btn: bb ? { w: bb.width, h: bb.height, inside: bb.left >= fb.left - .5 && bb.right <= fb.right + .5 && bb.top >= fb.top - .5 && bb.bottom <= fb.bottom + .5 } : null,
      padR: parseFloat(getComputedStyle(f).paddingRight) });
    if(btn) btn.click(); else { f.value = ''; f.dispatchEvent(new Event('input', { bubbles: true })); }
    await wait(250); try{ f.blur(); }catch(e){}
    out[out.length - 1].emptied = f.value === '';
  }
  return out; }"""

# ---- your row ----
ROWREAD = r"""() => {
  const rows = [...document.querySelectorAll('#stage .screen-rankings .rank-rows > .rank-row[data-pub]')];
  const i = rows.findIndex(r => r.dataset.me === '1'); if(i < 0) return null;
  const bg = r => { const s = getComputedStyle(r); return { c: s.backgroundColor, i: s.backgroundImage, pub: r.dataset.pub }; };
  return { i, n: rows.length, me: bg(rows[i]), above: i > 0 ? bg(rows[i - 1]) : null, below: i < rows.length - 1 ? bg(rows[i + 1]) : null,
    third: (() => { const t = rows.find(r => /rank-podium-3/.test(r.className)); return t ? Object.assign(bg(t), { me: t.dataset.me === '1' }) : null; })() }; }"""

# Find me pressed (taps at the given times), and every frame for `span` ms: the overlays inside your row (found by shape), the row's own
# background and transform, and where it is
FLASH = r"""async ([taps, span]) => {
  const btn = [...document.querySelectorAll('#stage .rank-tools > button')].find(b => b.getBoundingClientRect().width > 0);
  const tb = document.querySelector('.bottomtabs'); const top = document.querySelector('.wrap > .top');
  const series = []; const t0 = performance.now(); let k = 0; const ids = new WeakMap(); let nid = 0;
  const idOf = el => { if(!ids.has(el)) ids.set(el, ++nid); return ids.get(el); };
  const overlays = row => { const rb = row.getBoundingClientRect(); const out = [];
    const consider = (el, pseudo) => { const s = getComputedStyle(el, pseudo || null); if(s.display === 'none' || !/absolute|fixed/.test(s.position)) return;
      if(pseudo && (s.content === 'none' || s.content === 'normal')) return;
      let b; if(pseudo){ b = { left: rb.left + parseFloat(s.left), top: rb.top + parseFloat(s.top), width: parseFloat(s.width), height: parseFloat(s.height) }; } else b = el.getBoundingClientRect();
      if(!(b.width >= rb.width * .95 && b.height >= rb.height * .95)) return;
      const paint = s.backgroundColor !== 'rgba(0, 0, 0, 0)' || s.backgroundImage !== 'none';
      out.push({ op: paint ? parseFloat(s.opacity) : 0, l: b.left - rb.left, r: (b.left + b.width) - rb.right, t: b.top - rb.top, b: (b.top + b.height) - rb.bottom,
        id: pseudo ? pseudo : idOf(el) }); };
    [...row.children].forEach(c => consider(c)); consider(row, '::before'); consider(row, '::after'); return out; };
  /* a tap is a time in ms, or "fading": the moment the tint, having been near its peak, has fallen under .7 (a loaded machine draws
     frames far apart, so a fixed 700ms can land before the first tint was ever drawn) - with 3000ms as the latest */
  let peakSeen = 0, lastOp = 0, end = span, hd = [], firstOn = 0;
  return await new Promise(res => {
    const step = () => { const t = performance.now() - t0;
      while(k < taps.length && (typeof taps[k] === 'number' ? t >= taps[k] : ((peakSeen >= .9 && lastOp < .7 && lastOp > 0) || t >= 3000))){
        const h0 = performance.now(); btn.click(); hd.push(Math.round(performance.now() - h0)); k++; end = Math.max(end, t + 2300); }
      const row = document.querySelector('#stage .screen-rankings .rank-rows > .rank-row[data-me="1"]');
      if(row){ const ov = overlays(row); const s = getComputedStyle(row); const b = row.getBoundingClientRect();
        const op = ov.length ? Math.max(...ov.map(o => o.op)) : 0; lastOp = op; if(k === 1) peakSeen = Math.max(peakSeen, op);
        /* frames seconds apart (a loaded machine): keep reading until 2.3s after the tint was first drawn, up to 12s */
        if(op > 0 && !firstOn){ firstOn = t; end = Math.min(12000, Math.max(end, t + 2300)); }
        series.push({ t: Math.round(t), taps: k, op, ov: ov.length ? ov[0] : null, bg: s.backgroundImage + '|' + s.backgroundColor, tf: s.transform,
          top: b.top, bot: b.bottom, vis0: top ? top.getBoundingClientRect().bottom : 0, vis1: tb && tb.getBoundingClientRect().height ? tb.getBoundingClientRect().top : innerHeight, hd: hd.slice() }); }
      else series.push({ t: Math.round(t), op: -1, taps: k });
      if(t < end) requestAnimationFrame(step); else res(series); };
    requestAnimationFrame(step); }); }"""

# THE SAME, ON THE OVERLAY'S OWN CLOCK, IN THE TAP'S OWN TASK (no frame, no timer can come between): Find me tapped, the overlay found by
# shape at once, its animations held and read at 0..300ms and at their end; then, held at 700ms (fading), Find me tapped again - one
# overlay after it, the old one gone, the new one's clock at its start and its tint back at the peak. The frames a loaded machine draws
# seconds apart cannot fake or hide any of this; the frame series above is what the page actually drew.
CLOCKRUN = r"""() => {
  const btn = [...document.querySelectorAll('#stage .rank-tools > button')].find(b => b.getBoundingClientRect().width > 0);
  const rowOf = () => document.querySelector('#stage .screen-rankings .rank-rows > .rank-row[data-me="1"]');
  const overlayEls = row => { const rb = row.getBoundingClientRect(); return [...row.children].filter(c => { const s = getComputedStyle(c), b = c.getBoundingClientRect();
    return s.display !== 'none' && /absolute|fixed/.test(s.position) && b.width >= rb.width * .95 && b.height >= rb.height * .95
      && (s.backgroundColor !== 'rgba(0, 0, 0, 0)' || s.backgroundImage !== 'none'); }); };
  const reader = el => { const an = el.getAnimations ? el.getAnimations() : [];
    const at = t => { an.forEach(a => { a.pause(); a.currentTime = t; }); return parseFloat(getComputedStyle(el).opacity); };
    const end = an.length ? Math.max(...an.map(a => a.effect.getComputedTiming().endTime)) : null;
    return { an, at, end }; };
  const out = {};
  btn.click();
  const row = rowOf(); if(!row) return { err: 'no row' };
  const o1 = overlayEls(row); out.n1 = o1.length; if(!o1.length) return out;
  const R1 = reader(o1[0]); out.anims = R1.an.length; out.end = R1.end;
  out.at = [0, 50, 100, 150, 200, 250, 300].map(t => [t, +R1.at(t).toFixed(3)]);
  out.peak = Math.max(...[0, 100, 200, 224, 300, 400, 600].map(t => R1.at(t)));
  out.atEnd = R1.end != null ? +R1.at(R1.end).toFixed(3) : null;
  out.op700 = +R1.at(700).toFixed(3);
  btn.click();
  const o2 = overlayEls(row); out.n2 = o2.length; out.oldGone = !o1[0].isConnected; out.same = o2[0] === o1[0];
  if(o2.length){ const R2 = reader(o2[0]); out.ct2 = R2.an.length ? (R2.an[0].currentTime || 0) : null; out.end2 = R2.end;
    out.peak2 = Math.max(...[100, 200, 224, 300].map(t => R2.at(t))); out.atEnd2 = R2.end != null ? +R2.at(R2.end).toFixed(3) : null;
    R2.an.forEach(a => { a.currentTime = 0; a.play(); }); }
  return out; }"""

QUIET = """()=>{ if(!document.getElementById('sbar-quiet')){ const st=document.createElement('style'); st.id='sbar-quiet';
  st.textContent='.invite-overlay,.rs-spot,.unlock-card,.week-recap,.nova-say{display:none !important}'; document.body.appendChild(st); } }"""

def lum(p): return (p[0] * 299 + p[1] * 587 + p[2] * 114) / 1000

def boot(br, raw, dev, cls, errs):
    dn, W, H, ins, dpr = dev
    ctx = br.new_context(viewport={"width": W, "height": H}, device_scale_factor=dpr, has_touch=True, is_mobile=True, user_agent=UA)
    ctx.add_init_script(g["STANDALONE"]); ctx.add_init_script(FAKE)
    ctx.add_init_script("try{ if(!localStorage.getItem('class26e.drill.v1')){ localStorage.setItem('class26e.freshstart','1'); localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-SBAR');"
                        "['class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card','class26e.getstarted','class26e.penal256578.seen','class26e.penal55124.seen','class26e.penal124256.seen'].forEach(k=>localStorage.setItem(k,'9'));"
                        "localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.weekrecap.v1','9999-12-31'); localStorage.setItem('class26e.a2hs','1790500000000'); %s } }catch(e){}"
                        % (json.dumps(seed(cls)), "localStorage.setItem('class26e.activeclass','ifc');" if cls == "ifc" else ""))
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errs.append("%s %s: %s" % (dn, cls, str(e)[:200])))
    t, r, b, l = ins; v = {"top": f"{t}px", "right": f"{r}px", "bottom": f"{b}px", "left": f"{l}px"}
    body = g["INSET_RE"].sub(lambda m: v[m.group(1)], raw)
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    bm = re.search(r'const APP_BUILD = "([^"]+)"', raw); vj = json.dumps({"build": bm.group(1) if bm else "", "note": "", "frameId": "", "force": True})
    pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"}, body=vj))
    pg.goto(URL, timeout=180000); pg.wait_for_timeout(4500)
    pg.evaluate("document.getElementById('splashscreen')?.remove()")
    pg.evaluate("()=>{ try{ homeUnlocksOwed=()=>false; }catch(e){} showHome(); }"); pg.wait_for_timeout(900)
    pg.evaluate(QUIET)
    return ctx, pg

def shot(pg, clip):
    for attempt in range(4):
        try: return Image.open(io.BytesIO(pg.screenshot(clip=clip))).convert("RGB")
        except Exception:
            if attempt == 3: raise
            pg.wait_for_timeout(1500)

FILLS = []   # (where, fill) of every field and every companion

def fields_pass(pg, tag, scr, dev):
    rd = pg.evaluate(READ)
    F = rd["fields"]
    t = "%s %s" % (tag, scr)
    chk("%s: a search field is on the screen (%d)" % (t, len(F)), len(F) >= 1, rd)
    for f in F:
        n = "%s [%s]" % (t, f["cls"] or f["type"])
        h = f["h"]; c = f["comp"]
        chk("(1) %s: a capsule - corners %s drawn on a %.1fpx field (half: %.1f)%s" % (n, [round(x, 1) for x in f["rad"]], h, h / 2,
            ("; its button's corners %s on %.1fpx" % ([round(x, 1) for x in c["rad"]], c["h"])) if c else ""),
            all(abs(x - h / 2) <= .5 for x in f["rad"]) and (not c or all(abs(x - c["h"] / 2) <= .5 for x in c["rad"])), f)
        FILLS.append((n, f["fill"], f["img"]))
        if c:
            FILLS.append((n + " button", c["fill"], c["img"]))
            fm = (c["t"] + c["b"]) / 2 - (f["t"] + f["bt"]) / 2
            chk("(3) %s: the button on its line is the field's height (%.1f / %.1f), on the same middle (off %.2f)" % (n, c["h"], h, fm), abs(c["h"] - h) <= .5 and abs(fm) <= .5, c)
        chk("(4) %s: text %.1fpx, placeholder %.1fpx (16 or more)" % (n, f["fs"], f["phfs"]), f["fs"] >= 16 and f["phfs"] >= 16, f)
        gl = f["glyph"]
        gm = ((gl["t"] + gl["b"]) / 2 - (f["t"] + f["bt"]) / 2) if gl else None
        chk("(5) %s: field %.0fx%.0f%s; the magnifier inside it, centred on its middle (off %s)" % (n, f["w"], h, (", its button %.0fx%.0f" % (c["w"], c["h"])) if c else "", None if gm is None else round(gm, 2)),
            h >= 44 and f["w"] >= 44 and (not c or (c["w"] >= 44 and c["h"] >= 44)) and gl is not None and gl["l"] >= f["x"] and gl["r"] <= f["r"] and abs(gm) <= 1, f)
        room = f["cw"] - f["padL"] - f["padR"]
        over = c is not None and c["x"] < f["r"] + 2
        chk("(6) %s: inside the screen (%.1f..%.1f of %d), %s, the placeholder %.1fpx in %.1fpx of text box"
            % (n, f["x"], (c or f)["r"], rd["vw"], ("button %.1f past the field, label %s" % (c["x"] - f["r"], "clipped" if c["clipped"] else "whole")) if c else "no button",
               f["phW"], room),
            f["x"] >= 0 and (c or f)["r"] <= rd["vw"] and not over and not (c and c["clipped"]) and f["phW"] <= room + .5, f)
    chk("(6) %s: no sideways page scroll (%d in %d)" % (t, rd["docW"], rd["vw"]), rd["docW"] <= rd["vw"], rd)
    cl = pg.evaluate(CLEAR)
    for x in cl:
        b = x["btn"]
        chk("(5) %s [%s]: with a character typed the clear x is shown, %s, inside the field; it empties the field (%s)" % (t, x["cls"], b and "%.0fx%.0f" % (b["w"], b["h"]), x["emptied"]),
            b is not None and b["w"] >= 44 and b["h"] >= 44 and b["inside"] and x["emptied"], x)

def board_pass(pg, tag, dev, raw_reduce=False):
    dn, W, H, ins, dpr = dev
    keys = pg.evaluate("()=>rankingBoardsFor().map(b=>b.key)")
    out = {}
    for k in keys:
        pg.evaluate("(k)=>{ store.seenRewardsTour = true; showRankings(k); }", k)
        pg.wait_for_function("()=>document.querySelectorAll('#stage .rank-rows > .rank-row[data-pub]').length >= 15", timeout=15000)
        pg.wait_for_timeout(1200)
        pg.evaluate("()=>{ try{ document.querySelector('#stage .rank-rows')._lbFinish(); }catch(e){} document.querySelectorAll('.daily-alert,.toast').forEach(n=>n.remove()); window.scrollTo({top:0, behavior:'instant'}); }")
        pg.wait_for_timeout(500)
        rr = pg.evaluate(ROWREAD)
        if rr:
            # pixels inside each row's padding, near its two top corners (a 3x3 average) - your row against the rows round it
            def px_of(pub):
                if not pub: return None
                # in the middle of the screen, clear of the fixed top strip and the tab bar
                bx = pg.evaluate("""(p)=>{ const r=document.querySelector('#stage .rank-rows > .rank-row[data-pub="'+p+'"]'); r.scrollIntoView({block:'center', behavior:'instant'});
                  return null; }""", pub)
                pg.wait_for_timeout(300)
                bx = pg.evaluate("""(p)=>{ const b=document.querySelector('#stage .rank-rows > .rank-row[data-pub="'+p+'"]').getBoundingClientRect(); return {x:b.left, y:b.top, width:b.width, height:b.height}; }""", pub)
                im = shot(pg, bx)
                pts = [(int(6 * dpr), int(5 * dpr)), (im.width - int(6 * dpr), int(5 * dpr))]
                return [tuple(round(sum(im.getpixel((x + dx, y + dy))[i] for dx in (0, 1, 2) for dy in (0, 1, 2)) / 9) for i in range(3)) for (x, y) in pts]
            rr["px"] = {"me": px_of(rr["me"]["pub"]), "above": rr["above"] and px_of(rr["above"]["pub"]), "below": rr["below"] and px_of(rr["below"]["pub"]),
                        "third": rr["third"] and px_of(rr["third"]["pub"])}
            pg.evaluate("()=>window.scrollTo({top:0, behavior:'instant'})"); pg.wait_for_timeout(300)
        out[k] = rr
    return keys, out

def flash_run(pg, board, taps, span):
    pg.evaluate("(k)=>{ showRankings(k); }", board)
    pg.wait_for_function("()=>document.querySelectorAll('#stage .rank-rows > .rank-row[data-pub]').length >= 15", timeout=15000)
    pg.wait_for_timeout(1200)
    pg.evaluate("()=>{ document.querySelectorAll('.daily-alert,.toast').forEach(n=>n.remove()); window.scrollTo({top:0, behavior:'instant'}); }")
    pg.wait_for_timeout(500)
    before = pg.evaluate("()=>{ const r=document.querySelector('#stage .rank-rows > .rank-row[data-me=\"1\"]'); if(!r) return null; const s=getComputedStyle(r); const b=r.getBoundingClientRect(); return { bg: s.backgroundImage + '|' + s.backgroundColor, top: b.top, bot: b.bottom }; }")
    ser = pg.evaluate(FLASH, [taps, span])
    return before, ser

srv, URL = g["serve"]()
RAW = io.open(SRC, encoding="utf-8").read()
SCREENS = [s for s in os.environ.get("SB_SCREENS", "board,units,units-review,room,review,starred").split(",") if s]
errs = []
with sync_playwright() as pw:
    for dev in [d for d in DEVS if d[0] in os.environ.get("SB_DEVS", "promax,ipad11,se1,promaxL").split(",")]:
        for cls in os.environ.get("SB_CLASSES", "academy,ifc").split(","):
            if dev[0] in ("ipad11", "promaxL") and cls == "ifc" and not os.environ.get("SB_ALL"): continue   # Fire Code: the phones (Pro Max, 320)
            br = pw.chromium.launch(executable_path=g["CHROME"])
            tag = "%s %s" % (dev[0], cls)
            try:
                ctx, pg = boot(br, RAW, dev, cls, errs)
                got = pg.evaluate("()=>window.NOVA_CLASS")
                chk("%s: the page is that class (%s)" % (tag, got), got == cls, got)
                for scr in SCREENS:
                    if scr == "room" and cls == "ifc": continue   # the Virtual Room is the academy's
                    try:
                        pg.evaluate(OPEN, scr)
                        fields_pass(pg, tag, scr, dev)
                    except Exception as e:
                        chk("%s %s: measured (%s)" % (tag, scr, str(e).splitlines()[0][:200]), False)
                # ---- your row, Find me ----
                if cls == "academy" and dev[0] in ("promax", "ipad11"):
                    keys, rest = board_pass(pg, tag, dev)
                    hund = rest.get("hundos"); wk = rest.get(keys[0])
                    if hund:
                        same = lambda a, b: a and b and a["c"] == b["c"] and a["i"] == b["i"]
                        pxd = lambda a, b: max(max(abs(x - y) for x, y in zip(p, q)) for p, q in zip(a, b) if p and q) if a and b else 99
                        d1, d2 = pxd(hund["px"]["me"], hund["px"]["above"]), pxd(hund["px"]["me"], hund["px"]["below"])
                        chk("(7) %s Hundos: you are #%d of %d, in the list; your row's background is the rows' above and below (computed %s/%s, pixels off %s/%s)"
                            % (tag, hund["i"] + 1, hund["n"], same(hund["me"], hund["above"]), same(hund["me"], hund["below"]), d1, d2),
                            hund["i"] >= 3 and same(hund["me"], hund["above"]) and same(hund["me"], hund["below"]) and d1 <= 3 and d2 <= 3, hund)
                    else: chk("(7) %s: the Hundos board is there" % tag, False, keys)
                    if wk and hund and wk["third"] and hund["third"]:
                        a, b = wk["third"], hund["third"]
                        d3 = max(max(abs(x - y) for x, y in zip(p, q)) for p, q in zip(wk["px"]["third"], hund["px"]["third"]) if p and q)
                        chk("(7) %s %s: you are third, and third place looks as it does held by someone else (Hundos): computed %s, pixels off %d"
                            % (tag, keys[0], a["c"] == b["c"] and a["i"] == b["i"], d3),
                            a["me"] and not b["me"] and a["c"] == b["c"] and a["i"] == b["i"] and d3 <= 3, {"you": a, "them": b})
                    else: chk("(7) %s: you are third on %s" % (tag, keys[0]), False, wk)
                    def clock_run(board):
                        pg.evaluate("(k)=>{ showRankings(k); }", board)
                        pg.wait_for_function("()=>document.querySelectorAll('#stage .rank-rows > .rank-row[data-pub]').length >= 15", timeout=15000)
                        pg.wait_for_timeout(1000)
                        r = pg.evaluate(CLOCKRUN); pg.wait_for_timeout(2500); return r
                    # (8) one tap, on the podium (This Week) and from below the fold (Hundos)
                    for bk in (keys[0], "hundos"):
                        before, ser = flash_run(pg, bk, [0], 2300)
                        fr = [s for s in ser if s.get("taps", 0) >= 1]
                        on = [s for s in ser if s["op"] > 0]
                        nth = next((i for i, s in enumerate(fr) if s["op"] > 0), None)
                        first = on[0]["t"] if on else None
                        # the frames the page drew before the tint showed: on a loaded machine they can be seconds apart, and then the wall
                        # clock measures the machine; the overlay's own clock (below) is held to 300ms either way
                        gaps = [y["t"] - x["t"] for x, y in zip(fr, fr[1:]) if first is None or y["t"] <= first]
                        regular = max(gaps or [0]) < 250
                        soon = bool(on) and (first <= 300 or not regular or nth <= 2)
                        peak = max([s["op"] for s in ser] or [0])
                        bgs = sorted(set(s["bg"] for s in ser if s["op"] >= 0))
                        fit = [s["ov"] for s in on if s.get("ov")]
                        worst = max([max(abs(o["l"]), abs(o["r"]), abs(o["t"]), abs(o["b"])) for o in fit] or [99])
                        end = ser[-1]
                        seen = end["top"] >= end["vis0"] - 1 and end["bot"] <= end["vis1"] + 1
                        chk("(8) %s %s: Find me, as drawn - an overlay over your row from %sms (frame %s after the tap's; the frames %s), peak %.2f, 0 at the end; its box the row's within %.2fpx; the row's own background the same throughout (%d value%s, at rest %s)"
                            % (tag, bk, first, nth, "regular" if regular else "%dms apart" % max(gaps or [0]), peak, worst, len(bgs), "" if len(bgs) == 1 else "s", bgs == [before["bg"]] if before else None),
                            soon and ser[-1]["op"] <= 0 and worst <= 1 and before and bgs == [before["bg"]],
                            {"first": [(s["t"], s["op"]) for s in ser[:6]], "bgs": bgs[:3], "before": before})
                        chk("(8) %s %s: the row is on screen afterwards (%.0f..%.0f in %.0f..%.0f; it started at %.0f)" % (tag, bk, end["top"], end["bot"], end["vis0"], end["vis1"], before["top"] if before else -1),
                            seen and (bk != "hundos" or before["bot"] > end["vis1"]), end)
                    # (8) and (9) on the overlay's own clock: once on the podium (This Week)
                    ck = clock_run(keys[0])
                    on300 = [o for t, o in (ck.get("at") or []) if o > 0]
                    chk("(8) %s: on its own clock, the overlay is there in the tap's own task (%s), its tint > 0 by 300ms (%s), 0 at its end (%s, %sms)"
                        % (tag, ck.get("n1"), ck.get("at"), ck.get("atEnd"), ck.get("end")),
                        ck.get("n1") == 1 and ck.get("anims", 0) >= 1 and on300 and ck.get("atEnd") == 0 and ck.get("end") is not None and ck["end"] <= 2000, ck)
                    # (9) a second tap while it fades (held at 700ms): one overlay, the old one gone, its clock at the start, the tint back up
                    chk("(9) %s: a second tap while it fades (%.2f at 700ms) starts it over - %s overlay, the old one %s, its clock at %sms, the tint back to %.2f, 0 at its end (%s, %sms)"
                        % (tag, ck.get("op700", -1), ck.get("n2"), "gone" if ck.get("oldGone") else "still there", ck.get("ct2"), ck.get("peak2") or -1, ck.get("atEnd2"), ck.get("end2")),
                        ck.get("n2") == 1 and ck.get("oldGone") and ck.get("ct2") is not None and ck["ct2"] <= 50 and (ck.get("peak2") or 0) >= (ck.get("op700") or 1) + .2
                        and ck.get("atEnd2") == 0 and (ck.get("end2") or 9e9) <= 2000, ck)
                    # (10) reduce motion
                    if dev[0] == "promax":
                        pg.evaluate("()=>{ document.documentElement.dataset.reduceMotion = 'true'; }")
                        before, ser = flash_run(pg, keys[0], [0], 2300)
                        tfs = sorted(set(s["tf"] for s in ser if s["op"] >= 0))
                        on = [s for s in ser if s["op"] > 0]
                        ck = clock_run(keys[0])
                        at0 = (ck.get("at") or [[0, -1]])[0][1]
                        chk("(10) %s reduce motion: the tint is there at once (%.2f at 0ms of a %.2f peak; drawn from %sms), 0 at its end (%s, %sms), the row never moves (%s)"
                            % (tag, at0, ck.get("peak", -1), on[0]["t"] if on else None, ck.get("atEnd"), ck.get("end"), tfs),
                            ck.get("n1") == 1 and at0 >= .8 * (ck.get("peak") or 9) and ck.get("atEnd") == 0 and (ck.get("end") or 9e9) <= 2000 and bool(on) and ser[-1]["op"] <= 0 and tfs == ["none"],
                            {"clock": ck, "frames": [(s["t"], s["op"]) for s in ser[:6]]})
                        pg.evaluate("()=>{ delete document.documentElement.dataset.reduceMotion; }")
                ctx.close()
            except Exception as e:
                chk("%s: measured (%s)" % (tag, str(e).splitlines()[0][:200]), False)
            finally:
                br.close()
fills = sorted(set((f, i) for _, f, i in FILLS))
chk("(2) one fill for every field and the button beside it, on every screen, device and class: %s" % fills[:4],
    len(fills) == 1 and fills[0][1] == "none" and fills[0][0] not in ("rgba(0, 0, 0, 0)", "transparent"),
    [(w, f) for w, f, i in FILLS][:12])
chk("(11) no page errors (%d)" % len(errs), not errs, errs[:3])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
