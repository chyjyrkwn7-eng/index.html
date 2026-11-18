#!/usr/bin/env python3
"""384 profilerows2: Profile's three entry rows - the Rank ladder, the Badge case and Customize.

(384 ui3, round three) REVISED ON PURPOSE: the Badge case is one row now - option B's words beside the plain row icon (no ring,
coin, case or bar); a|b|c stay reachable by ?pfbadge= for comparison. Customize's default is the new d (C's theme ring, the count,
"Next" and a slim bar); e is B's next unlock in a small frame with the count and the bar; a|b|c by ?pfcz=. B1 / C1 now check the
default rows on every rank and e / the old options on one each. L7 is new: the ladder's halo and the prestige tag were cut off.

  python3 tools/check-b384-profilerows2.py [--quick] [--against REV|FILE]

  --quick    the Pro Max only (both classes); the full run adds the iPad Pro 11"
  --against  the build to test (a new check must FAIL on the build before: origin/claude/b384-final has none of this)

Per device and class:
  L1-L6  THE LADDER, for an account below the first rank, on the first, in the middle, on the top (and, in Fire Code, the top with a
         prestige count a test build left on the account - 384.135 retired prestige): one cell per rank (TIER_ORDER_FULL); yours is the one rankOf(store) says, lit (opacity 1, its own ring
         white), the ranks under it lit, the next one dashed, the rest dim; the lit line ends on your rank's centre (2px) and at 0
         below the first; your rank and its neighbours inside the track's box and the screen.
  L7     NOTHING OF THE LADDER IS CLIPPED: every node, its ring and glow (box-shadow), the pulse ring (and the prestige tag while it existed; 384.135 retired it), as
         painted (their transformed boxes plus their shadows' reach), inside every ancestor that clips (overflow other than visible,
         clip-path, contain:paint), at rest AND on every frame of the entrance (the swell and the pulse), in every state, both
         classes, the phone and the iPad, and on the phone at 85% and 135% text size (Safari's page zoom: the viewport 440/0.85 and
         440/1.35 wide). Must FAIL on fa11d79 (the halo and the tag were cut off at the top and right).
  L8     (384.135) PRESTIGE IS GONE: with an old `prestige: 1` on the account (Fire Code's "oldpg" position), the top rank's node
         holds only its emblem and the pulse (no mark beside it) and the ladder's line under its title is the plain top-rank
         account's, word for word. Must FAIL on fa11d79 (the mark and "Supernova · Prestige I").
  B1     THE BADGE CASE, the default row (B's words, the plain row icon, none of the art) and each old option: its count is badgeCountOf(store) of classTopics().length; a's front filled to that share, b's
         ring one tick per badge with that many lit, c's bar one segment per badge with that many lit; the newest badge drawn.
  C1     CUSTOMIZE, each option: held / total the sum of customizeTally over Customize's pages, its words carry them; b's, d's and
         e's next is unlockNextUp's first and its bar its share; d's icon is the theme ring and e's the next unlock in a frame.
  M1     MOTION: every animation the three rows run animates transform or opacity only, there are some, and the ladder under
         the fold has none until it is scrolled into view.
  M2     REDUCE MOTION: none at all, every row drawn at its last frame.
  T1     every row's button at least 44 x 44.
  D1     the Badge case is a Delta card (--delta-card-fill, --delta-card-r), as are the cards holding the other two.
  E1     no page error, no console error (the sandbox's blocked network aside).
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b384_seg_lib as L
from playwright.sync_api import sync_playwright

QUICK = "--quick" in sys.argv
DEVS = ["phone-installed"] if QUICK else ["phone-installed", "ipad-pro-11"]
FAILS = []; N = [0]
def ok(cond, what):
    N[0] += 1
    if not cond: FAILS.append(what)
    print(("PASS " if cond else "FAIL ") + what, flush=True)

def open_pf(br, dev, cls, q=""):
    kw = dict(viewport={"width": dev["w"], "height": dev["h"]}, device_scale_factor=dev["dpr"], user_agent=dev["ua"])
    if dev["touch"]: kw.update(has_touch=True, is_mobile=True)
    ctx = br.new_context(**kw)
    if dev["installed"]: ctx.add_init_script(L.g["STANDALONE"])
    ctx.add_init_script(L.g["FAKE_FIREBASE"].replace("__ROWS__", L.g["rows_json"]()))
    pg = ctx.new_page(); b = L.body_for(dev["ins"])
    pg.route(re.compile(r".*/index\.html(\?.*)?$"), lambda route, request: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    m = re.search(r'const APP_BUILD = "([^"]+)"', b); bld = m.group(1) if m else ""
    pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"},
             body=json.dumps({"build": bld, "note": "", "frameId": "", "force": True, "safariSound": True})))
    d = json.loads(L.g["SEED"].replace("__WEEK__", L.g["week_key_now"]())); d["publicId"] = L.OWNER; d["firstName"] = "Casey"; d["novaMet"] = 99
    pg.add_init_script(L.INIT % (json.dumps(json.dumps(d)), L.IFC if cls == "ifc" else ""))
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.on("console", lambda m: errs.append("console: " + m.text[:200]) if m.type == "error" and "net::ERR" not in m.text and "Failed to load resource" not in m.text else None)
    pg.set_default_timeout(180000)
    return ctx, pg, errs

# (L7) the ladder's painted boxes against every ancestor that clips them; window.__pfClipWorst keeps the worst overshoot seen
CLIPJS = r"""()=>{ window.__pfClipWorst = { over: 0, what: '', n: 0 };
  const ext = el => { const cs = getComputedStyle(el); let e = 0; const re = /(-?[\d.]+)px (-?[\d.]+)px (-?[\d.]+)px(?: (-?[\d.]+)px)?/g; let m;
    if(cs.boxShadow && cs.boxShadow !== 'none'){ for(const seg of cs.boxShadow.split(/,(?![^(]*\))/)){ if(/inset/.test(seg)) continue; re.lastIndex = 0; m = re.exec(seg); if(m) e = Math.max(e, Math.max(Math.abs(+m[1]), Math.abs(+m[2])) + (+m[3]) + (+(m[4] || 0))); } }
    return e; };
  const shown = el => { let o = 1; for(let n = el; n && n.nodeType === 1; n = n.parentElement) o *= +getComputedStyle(n).opacity; return o > .02; };
  const clips = el => { const out = []; for(let a = el.parentElement; a && a !== document.documentElement; a = a.parentElement){ const cs = getComputedStyle(a);
      if(cs.overflowX !== 'visible' || cs.overflowY !== 'visible' || (cs.clipPath && cs.clipPath !== 'none') || /paint|strict|content/.test(cs.contain || '')){
        const r = a.getBoundingClientRect(); const bl = parseFloat(cs.borderLeftWidth) || 0, br = parseFloat(cs.borderRightWidth) || 0, bt = parseFloat(cs.borderTopWidth) || 0, bb = parseFloat(cs.borderBottomWidth) || 0;
        out.push({ el: a, l: r.left + bl, r: r.right - br, t: r.top + bt, b: r.bottom - bb }); } } return out; };
  window.__pfClipSample = () => {
    const foot = document.querySelector('#stage .pf-goal-foot'); if(!foot) return;
    const parts = [...foot.querySelectorAll('.pfr-ld-node, .pfr-ld-pulse, .pfr-ld-pg')];
    for(const el of parts){ if(!shown(el)) continue;
      const r = el.getBoundingClientRect(); if(!r.width) continue;
      const k = el.offsetWidth ? r.width / el.offsetWidth : 1; const e = ext(el) * k;
      const p = { l: r.left - e, r: r.right + e, t: r.top - e, b: r.bottom + e };
      for(const c of clips(el)){
        /* a scrolled track: a node scrolled out of view is meant to be off - only one whose centre is inside the box counts */
        const cx = (r.left + r.right) / 2; if(cx < c.l || cx > c.r) continue;
        const over = Math.max(c.l - p.l, p.r - c.r, c.t - p.t, p.b - c.b, 0);
        window.__pfClipWorst.n++;
        if(over > window.__pfClipWorst.over){ const cl = s => String(s.className && s.className.baseVal !== undefined ? s.className.baseVal : s.className).split(' ')[0];
          window.__pfClipWorst = { over: +over.toFixed(2), what: cl(el) + (el.closest('.is-here') ? '(here)' : '') + ' in ' + cl(c.el) + ' [' + ['l','r','t','b'].filter((s, i) => [c.l - p.l, p.r - c.r, c.t - p.t, p.b - c.b][i] > .5).join('') + ']', n: window.__pfClipWorst.n }; } } } };
  let live = true; window.__pfClipStop = () => { live = false; };
  const tick = () => { if(!live) return; try{ window.__pfClipSample(); }catch(e){} requestAnimationFrame(tick); }; requestAnimationFrame(tick); }"""

# the account: rank `rank` (none / first / mid / last / oldpg), badges held, the newest not looked at; Profile opened from Home
SETUP = """async(want)=>{
  const wait = ms => new Promise(r => setTimeout(r, ms));
  document.getElementById('splashscreen')?.remove();
  try{ homeUnlocksOwed=()=>false; scheduleWeekRecap=()=>{}; maybeShowWeekRecap=()=>{}; playUnlockSpotlight=(it,n,of,release)=>{ try{ release && release(); }catch(e){} }; }catch(e){}
  store.novaMet = 99;
  document.querySelectorAll('#tour-overlay, #tour-tooltip, #nova-intro, .rs-spot, .unlock-card').forEach(n=>n.remove());
  const topics = classTopics();
  topics.forEach(u => { store.unitPerfects[u] = 0; });
  const top = want.rank === 'last' || want.rank === 'oldpg';
  const nb = top ? topics.length : want.rank === 'none' ? 0 : want.badges;
  topics.slice(0, nb).forEach(u => { store.unitPerfects[u] = badgeThresholdFor(u); });
  /* one unit part-way to its badge (the academy: hundos toward its band) */
  if(!top && topics[nb]) store.unitPerfects[topics[nb]] = Math.max(0, badgeThresholdFor(topics[nb]) - 1);
  const lvl = want.rank === 'none' ? 2 : want.rank === 'first' ? 22 : top ? 80 : want.level;
  store.lifetime.points = 0;
  for(let p = 0; p < 2000000; p += 1500){ store.lifetime.points = p; if(levelStateFor(store).level >= lvl) break; }
  store.rankFloor = top ? 7 : 0;
  /* (384.135) a retired prestige count, as a test build of 384.126 left it: it must draw nothing */
  if(want.rank === 'oldpg') store.prestige = 1;
  const s = ensureSeenUnlocks();
  s.badges = badgesEarnedList().slice(0, Math.max(0, badgesEarnedList().length - 1));
  if(want.reduce){ theme.reduceMotion = true; try{ saveTheme(); }catch(e){} document.documentElement.dataset.reduceMotion = 'true'; }
  const st = document.createElement('style'); st.textContent = '.bottomtabs, #bottomtabs, .bottomtab-bar{ display:none !important; }'; document.body.appendChild(st);
  try{ showHome(); }catch(e){}
  await wait(400);
  window.__pfAnims = [];
  showProfile('profile');
  window.scrollTo({ top: 0, behavior: 'instant' });
  /* every animation that starts on the three rows while it plays, sampled */
  const rows = () => [...document.querySelectorAll('#stage .profile-customize-btn, #stage .pf-case, #stage .pf-goal-foot')];
  const seen = new Map();
  const sample = () => rows().forEach(r => r.getAnimations({ subtree: true }).filter(a => /^pfr-/.test(a.animationName || '')).forEach(a => {
    const kf = (a.effect && a.effect.getKeyframes) ? a.effect.getKeyframes() : [];
    const props = new Set(); kf.forEach(k => Object.keys(k).forEach(p => { if(!['offset','computedOffset','easing','composite'].includes(p)) props.add(p); }));
    const tg = a.effect && a.effect.target;
    const key = (a.animationName || a.id || '') + '|' + (tg ? (tg.className && tg.className.baseVal !== undefined ? tg.className.baseVal : tg.className) : '');
    seen.set(key, { name: a.animationName || '', props: [...props], row: r.className.split(' ')[0], cls: tg ? String(tg.className && tg.className.baseVal !== undefined ? tg.className.baseVal : tg.className).slice(0, 40) : '' });
  }));
  for(let i = 0; i < 12; i++){ sample(); await wait(100); }
  const ldIn = !!document.querySelector('#stage .pf-goal-foot.is-in');
  const ldAnimsBefore = [...seen.values()].filter(x => x.row === 'pf-goal-foot').map(x => x.name + ':' + x.cls);
  const foot = document.querySelector('#stage .pf-goal-foot');
  const footBelow = foot ? foot.getBoundingClientRect().top > innerHeight : false;
  if(foot) foot.scrollIntoView({ block: 'center', behavior: 'instant' });
  for(let i = 0; i < 14; i++){ sample(); await wait(100); }
  /* until the rows' own have finished (the ring goes out twice: about 4s after the ladder comes into view) */
  for(let i = 0; i < 80; i++){ const live = rows().reduce((n, e) => n + e.getAnimations({ subtree: true }).filter(a => /^pfr-/.test(a.animationName || '') && a.playState === 'running').length, 0); if(!live) break; await wait(100); }
  await wait(300);
  return { rank: rankOf(store), anims: [...seen.values()], ldInBefore: ldIn, ldAnimsBefore, footBelow };
}"""

MEASURE = """()=>{
  const R = e => { const q = e.getBoundingClientRect(); return { l: q.left, r: q.right, t: q.top, b: q.bottom, w: q.width, h: q.height, cx: q.left + q.width / 2 }; };
  const out = {};
  const order = TIER_ORDER_FULL, cur = rankOf(store);
  out.ladder = (() => {
    const foot = document.querySelector('#stage .pf-goal-foot'); if(!foot) return null;
    const cells = [...foot.querySelectorAll('.pfr-ld-cell')];
    const sc = foot.querySelector('.pfr-ld-scroll'), rail = foot.querySelector('.pfr-ld-rail'), fill = foot.querySelector('.pfr-ld-fill');
    const states = cells.map(c => ['is-here','is-done','is-next','is-locked'].find(k => c.classList.contains(k)) || '');
    const hi = states.indexOf('is-here');
    const node = i => cells[i] && cells[i].querySelector('.pfr-ld-node');
    const vis = i => { if(i < 0 || i >= cells.length) return true; const a = R(node(i)), b = R(sc); return a.l >= b.l - 1 && a.r <= b.r + 1 && a.l >= -1 && a.r <= innerWidth + 1; };
    const hereNode = hi >= 0 ? node(hi) : null;
    return { n: cells.length, states, hi, want: cur ? order.indexOf(cur) : -1,
      hereOpacity: hereNode ? Number(getComputedStyle(hereNode).opacity) : null,
      hereBorder: hereNode ? getComputedStyle(hereNode).borderTopColor : null,
      doneOpacity: cells.filter((c, i) => states[i] === 'is-done').map(c => Number(getComputedStyle(c.querySelector('.pfr-ld-node')).opacity)),
      embOp: cells.map(c => Number(getComputedStyle(c.querySelector('.pfr-ld-emb')).opacity)),
      nextDashed: cells.filter((c, i) => states[i] === 'is-next').map(c => getComputedStyle(c.querySelector('.pfr-ld-node')).borderTopStyle),
      fillEnd: fill ? R(fill).r : null, fillW: fill ? R(fill).w : null, railL: rail ? R(rail).l : null,
      hereCx: hereNode ? R(hereNode).cx : null, firstCx: node(0) ? R(node(0)).cx : null,
      visible: hi >= 0 ? [vis(hi - 1), vis(hi), vis(hi + 1)] : [vis(0), vis(1)],
      extra: hereNode ? [...hereNode.children].filter(n => !n.classList.contains('pfr-ld-emb') && !n.classList.contains('pfr-ld-pulse')).length : -1,
      sub: (foot.querySelector('.pfr-ld-sub') || {}).textContent || '',
      box: R(foot) };
  })();
  out.badge = (() => {
    const b = document.querySelector('#stage .pf-case .pf-case-count'); if(!b) return null;
    const ticks = [...b.querySelectorAll('.pfr-ring-t')], segs = [...b.querySelectorAll('.pfr-seg > i')];
    const fill = b.querySelector('.pfr-mc-fill');
    /* option a's front: the gold is the lower --f of it, at rest (no transform left once it has risen in) */
    let sy = null; if(fill){ const cs = getComputedStyle(fill); sy = /^(none|matrix\\(1, 0, 0, 1, 0, 0\\))$/.test(cs.transform) ? Number(cs.getPropertyValue('--f')) : null; }   /* (a finished `both` animation holds identity) */
    const opt = ['a','b','c','row'].find(o => b.classList.contains('pfr-bc-' + o)) || '';
    const tile = b.querySelector(':scope > .settings-row-icon'); const tr = tile ? tile.getBoundingClientRect() : null;
    return { opt, text: (b.querySelector('.pf-case-num') || {}).textContent || '', have: badgeCountOf(store), total: classTopics().length,
      ticks: ticks.length, ticksOn: ticks.filter(t => t.classList.contains('is-on')).length, segs: segs.length, segsOn: segs.filter(t => t.classList.contains('is-on')).length,
      fillY: sy, newest: !!b.querySelector('.pfr-mc-pin svg, .pfr-ring-pin svg, .pfr-coin-top svg'),
      newestOp: (() => { const p = b.querySelector('.pfr-mc-pin, .pfr-ring-pin, .pfr-coin-top'); return p ? Number(getComputedStyle(p).opacity) : null; })(),
      card: (() => { const c = b.closest('.pf-case'), cs = getComputedStyle(c); return { bg: cs.backgroundColor, r: cs.borderTopLeftRadius }; })(),
      tile: tr ? { w: tr.width, h: tr.height, op: Number(getComputedStyle(tile).opacity) } : null,
      art: !!b.querySelector('.pfr-ring, .pfr-coin, .pfr-mc, .pfr-seg, .pfr-bc-art'),
      lines: [...b.querySelectorAll(':scope > .pf-act-words > *')].filter(e => e.getBoundingClientRect().height > 0).length,
      pct: (() => { const t = (b.querySelector('.pf-case-num') || {}).textContent || ''; const m = /(\\d+)%/.exec(t); return m ? +m[1] : null; })(),
      box: R(b) };
  })();
  out.cz = (() => {
    const b = document.querySelector('#stage .profile-customize-btn'); if(!b) return null;
    let have = 0, total = 0; CUSTOMIZE_ORDER.forEach(k => { const t = customizeTally(k); have += t.have; total += t.total; });
    const nx = unlockNextUp(null, 1)[0] || null;
    const opt = ['a','b','c','d','e'].find(o => b.classList.contains('pfr-cz-' + o)) || '';
    const bar = b.querySelector('.pfr-bar > i');
    const icon = b.firstElementChild; const ir = icon ? icon.getBoundingClientRect() : null;
    return { opt, have, total, dh: b.dataset.have, dt: b.dataset.total, text: b.textContent, aria: b.getAttribute('aria-label') || '',
      next: nx ? nx.item.k + ':' + nx.item.id : '', dnext: b.dataset.next || '', nextName: nx ? nx.item.name : '',
      barW: bar ? bar.getBoundingClientRect().width / bar.parentNode.getBoundingClientRect().width : null, frac: nx ? nx.frac : null,
      barH: bar ? bar.parentNode.getBoundingClientRect().height : null,
      icon: icon ? { ring: !!icon.querySelector('.pfr-swatch-ring'), thumb: !!icon.querySelector('.trk-thumb'), w: ir.width, h: ir.height, r: getComputedStyle(icon).borderTopLeftRadius } : null,
      host: (() => { const c = b.closest('.profile-hero'), cs = c ? getComputedStyle(c) : null; return cs ? { bg: cs.backgroundColor, r: cs.borderTopLeftRadius } : null; })(),
      box: R(b) };
  })();
  const goal = document.querySelector('#stage .pf-goal'); const gs = goal ? getComputedStyle(goal) : null;
  out.goal = gs ? { bg: gs.backgroundColor, r: gs.borderTopLeftRadius } : null;
  const ds = getComputedStyle(document.documentElement);
  const probe = document.createElement('i'); probe.style.background = ds.getPropertyValue('--delta-card-fill').trim() || '#2C2C2E'; document.body.appendChild(probe);
  out.delta = { fill: getComputedStyle(probe).backgroundColor, r: ds.getPropertyValue('--delta-card-r').trim() || '26px' }; probe.remove();
  out.still = [...document.querySelectorAll('#stage .profile-customize-btn, #stage .pf-case-count, #stage .pf-goal-foot')].map(e => e.classList.contains('is-still'));
  out.running = [...document.querySelectorAll('#stage .profile-customize-btn, #stage .pf-case, #stage .pf-goal-foot')].reduce((n, e) => n + e.getAnimations({ subtree: true }).filter(a => /^pfr-/.test(a.animationName || '') && a.playState === 'running').length, 0);
  return out;
}"""

def run_case(br, url, dev, cls, rank, q, reduce=False):
    ctx, pg, errs = open_pf(br, dev, cls)
    pg.goto(url + q, wait_until="load", timeout=180000)
    pg.wait_for_timeout(3500)
    want = {"badges": 12 if cls == "ifc" else 7, "level": 45 if cls == "ifc" else 36, "rank": rank, "reduce": reduce}
    pg.evaluate(CLIPJS)
    info = pg.evaluate(SETUP, want)
    pg.evaluate("()=>{ window.__pfClipStop(); window.__pfClipSample(); }")
    m = pg.evaluate(MEASURE); m["clip"] = pg.evaluate("()=>window.__pfClipWorst")
    ctx.close()
    return info, m, errs
def zoomed(dev, z):
    d = dict(dev); d["name"] = "%s@%d%%" % (dev["name"], round(z * 100)); d["w"] = round(dev["w"] / z); d["h"] = round(dev["h"] / z)
    d["ins"] = tuple(round(v / z) for v in dev["ins"]); return d

ALLOWED = {"transform", "opacity", "clipPath", "clip-path", "translate", "rotate", "scale"}

def main():
    srv, url = L.g["serve"]()
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=L.g["CHROME"])
        for dev in [d for d in L.DEVICES if d["name"] in DEVS]:
            for cls in ("academy", "ifc"):
                tag = "%s %s" % (dev["name"], cls)
                ranks = ["none", "first", "mid", "last"] + (["oldpg"] if cls == "ifc" else [])
                lastSub = None
                # the default rows on every rank; Customize e on the first and the top; the old badge / customize options once each
                cases = [(rk, "") for rk in ranks] + [("first", "?pfcz=e"), ("last", "?pfcz=e"), ("mid", "?pfbadge=a&pfcz=a"), ("mid", "?pfbadge=b&pfcz=b"), ("mid", "?pfbadge=c&pfcz=c")]
                for rank, q in cases:
                    info, m, errs = run_case(br, url, dev, cls, rank, q)
                    t = "%s rank=%s(%s)%s" % (tag, rank, info["rank"], (" " + q) if q else " default")
                    ld = m["ladder"]
                    if not ld or not ld["n"]:
                        ok(False, "L1 %s: the ladder is drawn (one cell per rank)" % t); continue
                    if not q:
                        ok(ld["n"] == 7, "L1 %s: one cell per rank (%d)" % (t, ld["n"]))
                        ok(ld["hi"] == ld["want"], "L2 %s: yours is the one rankOf says (cell %d, want %d)" % (t, ld["hi"], ld["want"]))
                        w = ld["want"]
                        exp = ["is-here" if i == w else "is-done" if i < w else "is-next" if i == w + 1 else "is-locked" for i in range(ld["n"])]
                        ok(ld["states"] == exp, "L3 %s: lit under yours, next, dim beyond (%s)" % (t, ",".join(s[3:] for s in ld["states"])))
                        if w >= 0:
                            ok(ld["hereOpacity"] == 1 and ld["hereBorder"] in ("rgb(255, 255, 255)",) and all(o == 1 for o in ld["doneOpacity"]) and ld["embOp"][w] == 1,
                               "L4 %s: your rank and those under it lit (opacity %s, ring %s)" % (t, ld["hereOpacity"], ld["hereBorder"]))
                            if w > 0: ok(abs(ld["fillEnd"] - ld["hereCx"]) <= 2, "L5 %s: the lit line ends on your rank (%.1f vs %.1f)" % (t, ld["fillEnd"], ld["hereCx"]))
                            else: ok(ld["fillW"] is not None and ld["fillW"] <= 1, "L5 %s: the first rank, no line lit (%.1f)" % (t, ld["fillW"] or 0))
                        else:
                            ok(ld["fillW"] is not None and ld["fillW"] <= 1 and ld["nextDashed"] == ["dashed"], "L5 %s: no rank, no line, the first one next (dashed)" % t)
                        ok(all(v for v in ld["visible"]), "L6 %s: your rank and its neighbours on screen (%s)" % (t, ld["visible"]))
                        if rank == "last": lastSub = ld["sub"]
                        if rank == "oldpg":
                            ok(ld["extra"] == 0, "L8 %s: an old prestige count draws nothing on the top rank (%d extra)" % (t, ld["extra"]))
                            ok(lastSub is not None and ld["sub"] == lastSub, "L8 %s: the ladder's line is the plain top rank's (%r vs %r)" % (t, ld["sub"], lastSub))
                        cl = m["clip"]
                        ok(cl["n"] > 0 and cl["over"] <= .5, "L7 %s: no node, ring, glow or tag clipped, at rest or mid-entrance (worst %spx %s; %d samples)" % (t, cl["over"], cl["what"], cl["n"]))
                    b = m["badge"]
                    if b:
                        good = b["text"].startswith("%d of %d" % (b["have"], b["total"]))
                        if b["opt"] == "a": good = good and b["fillY"] is not None and abs(b["fillY"] - b["have"] / b["total"]) < .01
                        if b["opt"] == "b": good = good and b["ticks"] == b["total"] and b["ticksOn"] == b["have"]
                        if b["opt"] == "c": good = good and b["segs"] == b["total"] and b["segsOn"] == b["have"]
                        if b["opt"] in ("a", "b", "c"): good = good and (b["newest"] if b["have"] else True) and (b["newestOp"] in (None, 1))
                        if b["opt"] == "row":
                            # B's words (the count, its share, a second line), the plain row icon (square, a Profile row tile's size), none of the art
                            good = (good and b["tile"] is not None and abs(b["tile"]["w"] - b["tile"]["h"]) < .5 and 24 <= b["tile"]["w"] <= 40 and b["tile"]["op"] == 1
                                    and not b["art"] and b["lines"] == 3 and b["pct"] == round(100 * b["have"] / max(1, b["total"])))
                        ok(b["opt"] == ("row" if "pfbadge" not in q else q.split("pfbadge=")[1][0]) and good,
                           "B1 %s: badge case (%s) reads the store: '%s', tile %s, art %s, lines %s, ticks %d/%d, segs %d/%d, fill %s" % (
                            t, b["opt"], b["text"], b["tile"], b["art"], b["lines"], b["ticksOn"], b["ticks"], b["segsOn"], b["segs"], b["fillY"]))
                        ok(b["card"]["bg"] == m["delta"]["fill"] and b["card"]["r"] == m["delta"]["r"], "D1 %s: the case is a Delta card (%s %s)" % (t, b["card"]["bg"], b["card"]["r"]))
                    else: ok(False, "B1 %s: the badge case row" % t)
                    c = m["cz"]
                    want_cz = q.split("pfcz=")[1][0] if "pfcz=" in q else "d"
                    if c and c["opt"]:
                        good = c["opt"] == want_cz and c["dh"] == str(c["have"]) and c["dt"] == str(c["total"]) and ("%d of %d" % (c["have"], c["total"])) in (c["aria"])
                        if c["opt"] in ("a", "c", "d", "e"): good = good and ("%d of %d unlocked" % (c["have"], c["total"])) in c["text"]
                        if c["opt"] in ("b", "d", "e"): good = good and c["dnext"] == c["next"] and (not c["next"] or (c["barW"] is not None and abs(c["barW"] - c["frac"]) < .02))
                        if c["opt"] in ("b", "d"): good = good and (not c["next"] or c["nextName"] in c["text"])
                        if c["opt"] == "d": good = good and c["icon"]["ring"] and (not c["next"] or c["barH"] <= 4)
                        if c["opt"] == "e": good = good and c["icon"]["thumb"] and c["icon"]["w"] <= 40 and float(c["icon"]["r"].replace("px", "") or 0) >= 6
                        ok(good, "C1 %s: customize (%s) reads the store: %s of %s, next %s, bar %s/%s, icon %s" % (t, c["opt"], c["have"], c["total"], c["next"], c["barW"], c["frac"], c["icon"]))
                    else: ok(False, "C1 %s: the customize row carries an option" % t)
                    ok(m["cz"] and m["cz"]["host"] and m["cz"]["host"]["bg"] == m["delta"]["fill"] and m["goal"]["bg"] == m["delta"]["fill"] and m["goal"]["r"] == m["delta"]["r"],
                       "D1 %s: the person card and the Next rank card are Delta cards" % t)
                    boxes = [x for x in (m["cz"] and m["cz"]["box"], b and b["box"], ld["box"]) if x]
                    ok(len(boxes) == 3 and all(x["h"] >= 44 and x["w"] >= 44 for x in boxes), "T1 %s: three buttons at least 44px (%s)" % (t, [(round(x["w"]), round(x["h"])) for x in boxes]))
                    an = info["anims"]
                    bad = [a for a in an if not set(a["props"]) <= ALLOWED]
                    ok(len(an) > 0 and not bad, "M1 %s: %d of the rows' animations, transform/opacity only%s" % (t, len(an), (" - BAD: %s" % bad[:3]) if bad else ""))
                    if info["footBelow"]:
                        ok(not info["ldInBefore"] and not info["ldAnimsBefore"], "M1 %s: the ladder under the fold waits (in %s, anims %s)" % (t, info["ldInBefore"], info["ldAnimsBefore"][:3]))
                    ok(m["running"] == 0, "M1 %s: nothing still running once played (%d)" % (t, m["running"]))
                    ok(not errs, "E1 %s: no page/console error %s" % (t, errs[:2]))
                # Reduce motion
                info, m, errs = run_case(br, url, dev, cls, "mid", "", reduce=True)
                ok(len(info["anims"]) == 0 and all(m["still"]) and len(m["still"]) == 3, "M2 %s: Reduce motion - %d animations, rows still %s" % (tag, len(info["anims"]), m["still"]))
                ok(m["badge"] and m["badge"]["newestOp"] in (None, 1) and m["ladder"] and m["ladder"]["hereOpacity"] == 1, "M2 %s: Reduce motion - drawn at the last frame" % tag)
                for q in ("?pfcz=e", "?pfbadge=b&pfcz=b"):
                    info, m, errs = run_case(br, url, dev, cls, "mid", q, reduce=True)
                    ok(len(info["anims"]) == 0 and all(m["still"]), "M2 %s %s: Reduce motion - no animation (%d)" % (tag, q, len(info["anims"])))
            # L7 at the phone's text sizes (Safari's page zoom): 85% and 135%, every rank, Fire Code (its top rank with an old prestige count: 384.135)
            if dev["name"] == "phone-installed":
                for z in (.85, 1.35):
                    zd = zoomed(dev, z)
                    for cls, rank in (("academy", "first"), ("academy", "mid"), ("academy", "last"), ("ifc", "none"), ("ifc", "oldpg")):
                        info, m, errs = run_case(br, url, zd, cls, rank, "")
                        cl = m["clip"]; ld = m["ladder"] or {}
                        ok(cl["n"] > 0 and cl["over"] <= .5, "L7 %s %s rank=%s: nothing of the ladder clipped (worst %spx %s; %d samples)" % (zd["name"], cls, rank, cl["over"], cl["what"], cl["n"]))
                        ok(all(v for v in ld.get("visible", [False])), "L6 %s %s rank=%s: your rank and its neighbours on screen (%s)" % (zd["name"], cls, rank, ld.get("visible")))
        br.close()
    print("\n%d checks, %d failed" % (N[0], len(FAILS)))
    for f in FAILS: print("  FAIL", f)
    sys.exit(1 if FAILS else 0)

main()
