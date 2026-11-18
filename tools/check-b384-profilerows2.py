#!/usr/bin/env python3
"""384 profilerows2: Profile's three entry rows - the Rank ladder (finished), the Badge case and Customize (options a|b|c).

  python3 tools/check-b384-profilerows2.py [--quick] [--against REV|FILE]

  --quick    the Pro Max only (both classes); the full run adds the iPad Pro 11"
  --against  the build to test (a new check must FAIL on the build before: origin/claude/b384-final has none of this)

Per device and class:
  L1-L6  THE LADDER, for an account below the first rank, on the first, in the middle, on the top (and, in Fire Code, the top with a
         prestige count a test build left on the account - 384.135 retired prestige): one cell per rank (TIER_ORDER_FULL); yours is the one rankOf(store) says, lit (opacity 1, its own ring
         white), the ranks under it lit, the next one dashed, the rest dim; the lit line ends on your rank's centre (2px) and at 0
         below the first; your rank and its neighbours inside the track's box and the screen.
  L7     (384.135) PRESTIGE IS GONE: with an old `prestige: 1` on the account, the top rank's node holds only its emblem and the pulse
         (no mark beside it) and the ladder's line under its title is the plain top-rank account's, word for word.
  B1     THE BADGE CASE, each option: its count is badgeCountOf(store) of classTopics().length; a's front filled to that share, b's
         ring one tick per badge with that many lit, c's bar one segment per badge with that many lit; the newest badge drawn.
  C1     CUSTOMIZE, each option: held / total the sum of customizeTally over Customize's pages, its words carry them; b's next is
         unlockNextUp's first and its bar its share.
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
    const opt = ['a','b','c'].find(o => b.classList.contains('pfr-bc-' + o)) || '';
    return { opt, text: (b.querySelector('.pf-case-num') || {}).textContent || '', have: badgeCountOf(store), total: classTopics().length,
      ticks: ticks.length, ticksOn: ticks.filter(t => t.classList.contains('is-on')).length, segs: segs.length, segsOn: segs.filter(t => t.classList.contains('is-on')).length,
      fillY: sy, newest: !!b.querySelector('.pfr-mc-pin svg, .pfr-ring-pin svg, .pfr-coin-top svg'),
      newestOp: (() => { const p = b.querySelector('.pfr-mc-pin, .pfr-ring-pin, .pfr-coin-top'); return p ? Number(getComputedStyle(p).opacity) : null; })(),
      card: (() => { const c = b.closest('.pf-case'), cs = getComputedStyle(c); return { bg: cs.backgroundColor, r: cs.borderTopLeftRadius }; })(),
      box: R(b) };
  })();
  out.cz = (() => {
    const b = document.querySelector('#stage .profile-customize-btn'); if(!b) return null;
    let have = 0, total = 0; CUSTOMIZE_ORDER.forEach(k => { const t = customizeTally(k); have += t.have; total += t.total; });
    const nx = unlockNextUp(null, 1)[0] || null;
    const opt = ['a','b','c'].find(o => b.classList.contains('pfr-cz-' + o)) || '';
    const bar = b.querySelector('.pfr-bar > i');
    return { opt, have, total, dh: b.dataset.have, dt: b.dataset.total, text: b.textContent, aria: b.getAttribute('aria-label') || '',
      next: nx ? nx.item.k + ':' + nx.item.id : '', dnext: b.dataset.next || '', nextName: nx ? nx.item.name : '',
      barW: bar ? bar.getBoundingClientRect().width / bar.parentNode.getBoundingClientRect().width : null, frac: nx ? nx.frac : null,
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

def run_case(br, url, dev, cls, rank, opt, reduce=False):
    ctx, pg, errs = open_pf(br, dev, cls)
    pg.goto(url + "?pfbadge=%s&pfcz=%s" % (opt, opt), wait_until="load", timeout=180000)
    pg.wait_for_timeout(3500)
    want = {"badges": 12 if cls == "ifc" else 7, "level": 45 if cls == "ifc" else 36, "rank": rank, "reduce": reduce}
    info = pg.evaluate(SETUP, want)
    m = pg.evaluate(MEASURE)
    ctx.close()
    return info, m, errs

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
                for rank in ranks:
                    opt = "abc"[ranks.index(rank) % 3]
                    info, m, errs = run_case(br, url, dev, cls, rank, opt)
                    t = "%s rank=%s(%s) opt=%s" % (tag, rank, info["rank"], opt)
                    ld = m["ladder"]
                    if not ld or not ld["n"]:
                        ok(False, "L1 %s: the ladder is drawn (one cell per rank)" % t); continue
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
                        ok(ld["extra"] == 0, "L7 %s: an old prestige count draws nothing on the top rank (%d extra)" % (t, ld["extra"]))
                        ok(lastSub is not None and ld["sub"] == lastSub, "L7 %s: the ladder's line is the plain top rank's (%r vs %r)" % (t, ld["sub"], lastSub))
                    b = m["badge"]
                    if b:
                        good = b["text"].startswith("%d of %d" % (b["have"], b["total"]))
                        if b["opt"] == "a": good = good and b["fillY"] is not None and abs(b["fillY"] - b["have"] / b["total"]) < .01
                        if b["opt"] == "b": good = good and b["ticks"] == b["total"] and b["ticksOn"] == b["have"]
                        if b["opt"] == "c": good = good and b["segs"] == b["total"] and b["segsOn"] == b["have"]
                        good = good and (b["newest"] if b["have"] else True) and (b["newestOp"] in (None, 1))
                        ok(good, "B1 %s: badge case (%s) reads the store: '%s', ticks %d/%d, segs %d/%d, fill %s, newest %s" % (
                            t, b["opt"], b["text"], b["ticksOn"], b["ticks"], b["segsOn"], b["segs"], b["fillY"], b["newest"]))
                        ok(b["card"]["bg"] == m["delta"]["fill"] and b["card"]["r"] == m["delta"]["r"], "D1 %s: the case is a Delta card (%s %s)" % (t, b["card"]["bg"], b["card"]["r"]))
                    else: ok(False, "B1 %s: the badge case row" % t)
                    c = m["cz"]
                    if c and c["opt"]:
                        good = c["dh"] == str(c["have"]) and c["dt"] == str(c["total"]) and ("%d of %d" % (c["have"], c["total"])) in (c["aria"])
                        if c["opt"] in ("a", "c"): good = good and ("%d of %d unlocked" % (c["have"], c["total"])) in c["text"]
                        if c["opt"] == "b": good = good and c["dnext"] == c["next"] and (not c["next"] or (c["nextName"] in c["text"] and abs(c["barW"] - c["frac"]) < .02))
                        ok(good, "C1 %s: customize (%s) reads the store: %s of %s, next %s" % (t, c["opt"], c["have"], c["total"], c["next"]))
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
                info, m, errs = run_case(br, url, dev, cls, "mid", "a", reduce=True)
                ok(len(info["anims"]) == 0 and all(m["still"]) and len(m["still"]) == 3, "M2 %s: Reduce motion - %d animations, rows still %s" % (tag, len(info["anims"]), m["still"]))
                ok(m["badge"] and m["badge"]["newestOp"] in (None, 1) and m["ladder"] and m["ladder"]["hereOpacity"] == 1, "M2 %s: Reduce motion - drawn at the last frame" % tag)
                for opt in ("b", "c"):
                    info, m, errs = run_case(br, url, dev, cls, "mid", opt, reduce=True)
                    ok(len(info["anims"]) == 0 and all(m["still"]), "M2 %s opt=%s: Reduce motion - no animation (%d)" % (tag, opt, len(info["anims"])))
        br.close()
    print("\n%d checks, %d failed" % (N[0], len(FAILS)))
    for f in FAILS: print("  FAIL", f)
    sys.exit(1 if FAILS else 0)

main()
