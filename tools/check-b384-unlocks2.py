"""Build 384.136 (unlocks2): THE UNLOCKS BROWSER - Customize > All unlocks, redesigned (the tracks and every rule unchanged).

Madison: "The way of looking through challenges for all the characters, banners, themes, and hundo effects, can we make that just look
and feel way better, if it needs an overhaul then do it." Asserted by SHAPE and by numbers read off the page (no label strings), both
classes, on the made-up rich accounts of check-b384-unlocks.py (an in-memory Firestore):
 (U1) EVERY ITEM: each filter (Characters, Banners, Themes, Effects, Rims) shows one card per item the class has (counted here from the
      app's own lists and checks, the way Customize counts them), each with a drawn preview (a picture with a size: an svg, an image, a
      banner scene, a swatch, an effect's stage or a plate) and EITHER the earned state (held, by the app's own check) OR a rule (locked);
      a held card is never shown locked and a locked one never earned.
 (U2) PROGRESS IS THE REAL NUMBERS: every locked card's bar fills to the share its own unlock card says (have / need, or the rank's
      share), and the numbers under it are that card's numbers; every tier row of the five tracks fills to its tier's have / need -
      and a new rim whose own count is met but a tier before it is not shows the tiers before it held, never a full bar; the
      overview's percentage is the collection's held / total counted here.
 (U3) ONE GRID: in every group, every card is the same width, the cards of a row share their top and their height, the previews of a
      row are the same height, the columns of every row start at the same x as the first row's, and the bars of a row end at one line.
 (U4) 44px: every card, filter chip, tier row, rim and the way in is at least 44 x 44.
 (U5) NOTHING CLIPS at Safari's 85% and 135% text sizes (a 518 and a 326 px wide phone) and on the iPad: no text box is cut
      (scrollWidth within clientWidth), every text sits inside its card, and the page never scrolls sideways.
 (U6) SCROLL COST (phone): scrolling the All page and the Characters grid end to end, frame by frame, forces at most one style pass
      for every 3 frames (no per-frame style work) and averages under 10ms of main-thread task time a frame; and no animation is running
      inside a card more than a screen away from the view (motion only near the screen).
  python3 tools/check-b384-unlocks2.py [--against REV|path/index.html] [--only U1,U5] [--cls academy|ifc]
--against b27f363 must FAIL (none of this exists there)."""
import json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
G = os.path.join(HERE, "check-b384-unlocks.py")
_argv = sys.argv[:]
sys.argv = [G]
h = {"__file__": G, "__name__": "u2"}
exec(open(G).read().split("\n# ---- the gate ----")[0], h)
sys.argv = _argv
from playwright.sync_api import sync_playwright

def arg(n): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else None
AGAINST = arg("--against"); ONLY = set((arg("--only") or "").split(",")) - {""}; CLS = arg("--cls")
def wanted(n): return not ONLY or n in ONLY
ROOT = h["ROOT"]
if AGAINST:
    if os.path.exists(AGAINST): text = open(AGAINST, encoding="utf-8").read()
    else: text = subprocess.check_output(["git", "-C", ROOT, "show", AGAINST + ":index.html"]).decode("utf-8")
else:
    text = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
fx = h["fixtures"]()
FAILS = []; PASSES = [0]
def chk(name, ok, info=None):
    if ok: PASSES[0] += 1; print("PASS", name, flush=True)
    else: FAILS.append(name); print("FAIL", name, ("" if info is None else str(info)[:600]), flush=True)

KINDS = ["char", "banner", "theme", "fx"]   # (384.136, changed on purpose: Madison, "Remove the rims") no Rims filter
OPEN = """async (k) => { const W = ms => new Promise(r => setTimeout(r, ms));
  document.querySelectorAll('.invite-overlay').forEach(o => o.remove());
  try{ showUnlockTracks(); }catch(e){ return 'no screen: ' + e; } await W(700);
  if(k !== 'all'){ const c = document.querySelector('#stage .ulk-chip[data-filter="' + k + '"]'); if(!c) return 'no filter ' + k; c.click(); await W(900); }
  window.scrollTo(0, 0); await W(200); return 'ok'; }"""

# the model, counted here from the app's own lists and checks (as Customize counts them); details from the cards' own builders
MODEL = """(k) => { const v = unlockTrackView();
  if(k === 'char') return AVATAR_CHARACTERS.filter(c => !(c.retired && store.avatarChar !== c.id) && !(c.legacy && isLockedCharacter(c.id))).map(c => ({ id: c.id, held: !isLockedCharacter(c.id) }));
  if(k === 'banner') return [{ id: '', held: true }].concat(BANNERS.map(b => ({ id: b.id, held: bannerEarned(b.id) })));
  if(k === 'theme') return ACCENTS.map(n => ({ id: n, held: !isLockedAccent(n) }));
  if(k === 'fx') return HUNDO_FX.map(d => ({ id: d.id, held: hundoFxEarned(d.id) }));
  return unlockRimList(v).map(r => ({ id: r.id, held: !!r.held })); }"""

CARDS = r"""(k) => { const model = (%s)(k);
  const det = id => { try{ if(k === 'char') return characterDetail(id); if(k === 'banner') return id ? bannerDetail(id) : {};
    if(k === 'theme') return id === 'ink' ? {} : themeDetail(id); if(k === 'fx') return hundoFxDetail(id); return rimDetail(id); }catch(e){ return {}; } };
  const nums = s => (String(s || '').match(/\d[\d,]*/g) || []).map(x => +x.replace(/,/g, ''));
  const cards = [...document.querySelectorAll('#stage .ulk-item')];
  const rows = cards.map(c => {
    const id = c.dataset.id, m = model.find(x => x.id === id), pv = c.querySelector('.ulk-prev');
    const drawn = !!pv && [...pv.children].some(ch => { if(ch.classList.contains('ulk-badge')) return false; const r = ch.getBoundingClientRect();
      return r.width > 8 && r.height > 8 && (ch.matches('svg, img, canvas, .bnr, .swatch, .hfx-stage, .rim-plate') || !!ch.querySelector('svg, img, canvas, .dot') || getComputedStyle(ch).backgroundImage !== 'none'); });
    const earned = !!c.querySelector('.ulk-state.is-earned'), req = ((c.querySelector('.ulk-req') || {}).textContent || '').trim();
    const bar = c.querySelector('.ulk-bar'), f = bar && bar.querySelector('i');
    const frac = bar && f ? f.getBoundingClientRect().width / bar.getBoundingClientRect().width : null;
    const d = m && !m.held ? det(id) : {};
    const want = m && !m.held ? (typeof d.frac === 'number' ? d.frac : (typeof d.have === 'number' && d.need ? d.have / d.need : null)) : null;
    const wantNums = d.countText ? nums(d.countText) : (typeof d.have === 'number' && d.need > 1 ? [d.have, d.need] : null);
    return { id, known: !!m, held: m ? m.held : null, drawn, earned, req: req.length, frac, want: want == null ? null : Math.max(0, Math.min(1, want)),
             nums: nums((c.querySelector('.ulk-count') || {}).textContent), wantNums };
  });
  return { n: cards.length, want: model.length, ids: model.map(x => x.id).sort().join(','), got: cards.map(c => c.dataset.id).sort().join(','), rows }; }""" % MODEL

TIERS = r"""() => { const v = unlockTrackView(); const out = [];
  document.querySelectorAll('#stage .trk-card.is-ladder .trk-tier').forEach(r => {
    const t = v.tracks.find(x => x.key === r.dataset.track), x = t && t.tiers[+r.dataset.tier - 1]; if(!x) { out.push({ bad: true }); return; }
    const bar = r.querySelector('.trk-bar'), f = bar && bar.querySelector('i');
    const shown = bar && getComputedStyle(bar).display !== 'none' && bar.getBoundingClientRect().width > 0;
    let have = x.lead.have, need = x.lead.need;
    const miss = x.lead.k === 'rim' && x.lead.goalMet ? t.tiers.slice(0, x.n - 1).filter(y => !y.held) : [];
    if(!x.held && miss.length){ need = x.n - 1; have = need - miss.length; }
    out.push({ track: t.key, n: x.n, held: x.held, rowHeld: r.classList.contains('is-held'), shown: !!shown,
               frac: shown && f ? f.getBoundingClientRect().width / bar.getBoundingClientRect().width : null,
               want: x.held ? 1 : (need ? Math.min(1, have / need) : 0), rimWait: miss.length > 0 && !x.held });
  });
  const ring = document.querySelector('#stage .ulk-ring-pct');
  return { tiers: out, ring: ring ? +(ring.textContent.match(/\d+/) || [NaN])[0] : null, nTiers: v.tracks.reduce((s, t) => s + t.tiers.length, 0) }; }"""

GRID = r"""() => { const out = [];
  document.querySelectorAll('#stage .ulk-grid').forEach((g, gi) => {
    const cs = [...g.querySelectorAll(':scope > .ulk-item')].map(c => { const r = c.getBoundingClientRect(), p = c.querySelector('.ulk-prev').getBoundingClientRect();
      const m = c.querySelector('.ulk-meter, .ulk-state'); const mr = m ? m.getBoundingClientRect() : null;
      return { l: r.left, t: r.top, w: r.width, h: r.height, ph: p.height, mb: mr ? mr.bottom : null, bb: r.bottom }; });
    out.push(cs); });
  return out; }"""

TARGETS = r"""() => [...document.querySelectorAll('#stage :is(.ulk-item, .ulk-chip, .trk-tier, .trk-rim, .trk-all)')].map(e => { const r = e.getBoundingClientRect();
  return [e.className.split(' ')[0], Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10]; })"""

CLIP = r"""() => { const bad = [];
  const sel = '.ulk-name, .ulk-req, .ulk-count, .ulk-state, .ulk-chip-label, .ulk-chip-count, .ulk-hero-count, .ulk-hero-sub, .ulk-kicker, .ulk-ring-pct, .trk-name, .trk-plus, .trk-goal, .trk-count, .trk-kicker, .trk-rim-name, .trk-rim-state, .cz-group-name, .cz-group-note, .cz-group-count';
  document.querySelectorAll('#stage :is(' + sel + ')').forEach(e => {
    if(!e.getClientRects().length) return;
    const card = e.closest('.ulk-item, .trk-tier, .trk-rim, .ulk-chip, .cz-group'); const r = e.getBoundingClientRect(), c = card ? card.getBoundingClientRect() : null;
    if(e.scrollWidth > e.clientWidth + 1 || e.scrollHeight > e.clientHeight + 2) bad.push(['cut', e.className, e.textContent.slice(0, 30), e.scrollWidth, e.clientWidth]);
    else if(c && (r.left < c.left - .5 || r.right > c.right + .5 || r.top < c.top - .5 || r.bottom > c.bottom + .5)) bad.push(['out', e.className, e.textContent.slice(0, 30), Math.round(r.right - c.right), Math.round(r.bottom - c.bottom)]);
  });
  const side = document.documentElement.scrollWidth > innerWidth + 1 || document.body.scrollWidth > innerWidth + 1;
  return { bad, side, n: document.querySelectorAll('#stage :is(' + sel + ')').length }; }"""

SCROLL = r"""async () => { window.__gateFarProbe = function __gateFarProbe(){ const vh = innerHeight; let n = 0;
      document.getAnimations().forEach(a => { if(a.playState !== 'running') return; const t = a.effect && a.effect.target; const card = t && t.closest && t.closest('.ulk-item, .trk-tier');
        if(!card) return; const r = card.getBoundingClientRect(); if(r.bottom < -vh || r.top > 2 * vh) n++; }); return n; }; const W = ms => new Promise(r => setTimeout(r, ms)); const fr = () => new Promise(r => requestAnimationFrame(r));
  window.scrollTo(0, 0); await W(400);
  const max = document.documentElement.scrollHeight - innerHeight; const step = 36; let frames = 0; const times = []; let last = performance.now();
  const far = [];
  while(scrollY < max - 1 && frames < 400){ window.scrollBy(0, step); await fr(); const now = performance.now(); times.push(now - last); last = now; frames++;
    if(frames % 20 === 0) far.push(__gateFarProbe()); }
  return { frames, times, far }; }"""

def run_cls(br, cls):
    seed, init = fx["rich_" + cls]
    # ---- the phone: U1-U4, U6
    ctx, pg, errs = h["page"](br, text, seed, init, w=440, h=956, scale=1)
    pg.wait_for_timeout(1200); h["quiet"](pg); h["load_board"](pg); h["quiet"](pg)
    tot_have = tot = 0
    for k in KINDS:
        st = pg.evaluate(OPEN, k)
        if st != "ok":
            chk("[%s] (U1) the %s filter exists (%s)" % (cls, k, st), False); continue
        c = pg.evaluate(CARDS, k)
        rows = c["rows"]
        tot += c["want"]; tot_have += sum(1 for r in rows if r["held"])
        if wanted("U1"):
            chk("[%s] (U1) %s: one card per item (%d of %d)" % (cls, k, c["n"], c["want"]), c["n"] == c["want"] and c["ids"] == c["got"], [c["ids"][:200], c["got"][:200]])
            nod = [r["id"] for r in rows if not r["drawn"]]
            chk("[%s] (U1) %s: every card has a drawn preview (%d without)" % (cls, k, len(nod)), rows and not nod, nod)
            wrong = [r["id"] for r in rows if not r["known"] or (r["held"] and (not r["earned"] or r["req"])) or (not r["held"] and (r["earned"] or not r["req"]))]
            chk("[%s] (U1) %s: earned exactly when held, a rule exactly when locked (%d wrong)" % (cls, k, len(wrong)), rows and not wrong, wrong)
        if wanted("U2"):
            bad = [(r["id"], r["frac"], r["want"]) for r in rows if not r["held"] and r["want"] is not None and (r["frac"] is None or abs(r["frac"] - r["want"]) > .02)]
            chk("[%s] (U2) %s: every locked bar fills to its card's share (%d off)" % (cls, k, len(bad)), rows and not bad, bad)
            badn = [(r["id"], r["nums"], r["wantNums"]) for r in rows if not r["held"] and r["wantNums"] and r["nums"] != r["wantNums"]]
            chk("[%s] (U2) %s: the numbers under each bar are its card's (%d off)" % (cls, k, len(badn)), rows and not badn, badn)
        if wanted("U3"):
            g = pg.evaluate(GRID)
            probs = []
            for cs in g:
                if not cs: continue
                w0 = cs[0]["w"]; lefts0 = []
                byrow = {}
                for x in cs: byrow.setdefault(round(x["t"]), []).append(x)
                rws = [byrow[t] for t in sorted(byrow)]
                lefts0 = [round(x["l"], 1) for x in rws[0]]
                for rw in rws:
                    if any(abs(x["w"] - w0) > .5 for x in rw): probs.append("width")
                    if max(x["h"] for x in rw) - min(x["h"] for x in rw) > .5: probs.append("height")
                    if max(x["ph"] for x in rw) - min(x["ph"] for x in rw) > .5: probs.append("preview")
                    if [round(x["l"], 1) for x in rw] != lefts0[:len(rw)]: probs.append("columns")
                    mbs = [x["bb"] - x["mb"] for x in rw if x["mb"] is not None]
                    if mbs and max(mbs) - min(mbs) > 1: probs.append("foot")
            chk("[%s] (U3) %s: one even grid (%d groups; %s)" % (cls, k, len(g), sorted(set(probs)) or "aligned"), g and not probs, probs[:10])
        if wanted("U4"):
            t = pg.evaluate(TARGETS)
            small = [x for x in t if x[1] < 44 or x[2] < 44]
            chk("[%s] (U4) %s: every target >= 44px (%d, %d small)" % (cls, k, len(t), len(small)), t and not small, small[:8])
    if wanted("U2"):
        pg.evaluate(OPEN, "all")
        tr = pg.evaluate(TIERS)
        tiers = tr["tiers"]
        chk("[%s] (U2) all: every tier of the five tracks is a ladder row (%d of %d)" % (cls, len(tiers), tr["nTiers"]), len(tiers) == tr["nTiers"] and not any(x.get("bad") for x in tiers), tiers[:3])
        off = [(x.get("track"), x.get("n"), x.get("frac"), x.get("want")) for x in tiers if not x.get("bad") and not x["held"] and (x["frac"] is None or abs(x["frac"] - x["want"]) > .02)]
        chk("[%s] (U2) all: every locked tier's bar = its have / need (%d off)" % (cls, len(off)), tiers and not off, off)
        full = [(x["track"], x["n"]) for x in tiers if not x.get("bad") and x["rimWait"] and (x["frac"] or 0) > .99]
        chk("[%s] (U2) all: a rim waiting on an earlier tier never shows a full bar (%d)" % (cls, len(full)), not full, full)
        hm = [(x["track"], x["n"]) for x in tiers if not x.get("bad") and x["held"] != x["rowHeld"]]
        chk("[%s] (U2) all: held rows exactly the held tiers (%d off)" % (cls, len(hm)), tiers and not hm, hm)
        want_pct = round(100 * tot_have / tot) if tot else -1
        chk("[%s] (U2) the overview's share = held / total counted here (%s vs %d%%: %d of %d)" % (cls, tr["ring"], want_pct, tot_have, tot), tr["ring"] == want_pct, tr["ring"])
        if wanted("U4"):
            t = pg.evaluate(TARGETS)
            small = [x for x in t if x[1] < 44 or x[2] < 44]
            chk("[%s] (U4) all: every row, rim and chip >= 44px (%d, %d small)" % (cls, len(t), len(small)), t and not small, small[:8])
    if wanted("U6"):
        import collections
        CATS = "devtools.timeline,disabled-by-default-devtools.timeline,disabled-by-default-devtools.timeline.stack"
        cdp = ctx.new_cdp_session(pg)
        for k in ("all", "char"):
            pg.evaluate(OPEN, k); pg.wait_for_timeout(1500)
            # a first pass end to end, untraced: the flip-book recorder makes each character's sheet once a session (recordCharSheet,
            # frameSrc - the same on Customize's pages); what is measured is the page as scrolled after that
            pg.evaluate(SCROLL); pg.wait_for_timeout(2500)
            evs, done = [], []
            cdp.on("Tracing.dataCollected", lambda p_: evs.extend(p_["value"]))
            cdp.on("Tracing.tracingComplete", lambda p_: done.append(1))
            cdp.send("Tracing.start", {"categories": CATS, "transferMode": "ReportEvents"})
            s = pg.evaluate(SCROLL)
            cdp.send("Tracing.end")
            for _ in range(300):
                if done: break
                pg.wait_for_timeout(100)
            names = {}
            for e in evs:
                if e.get("name") == "thread_name": names[(e["pid"], e["tid"])] = e["args"]["name"]
            main = [e for e in evs if e.get("ph") == "X" and names.get((e.get("pid"), e.get("tid"))) == "CrRendererMain"]
            forced = collections.Counter(); app = collections.Counter()
            for e in main:
                if e["name"] not in ("UpdateLayoutTree", "Layout"): continue
                a = e.get("args", {})
                st = (a.get("beginData", {}) or {}).get("stackTrace") or a.get("stackTrace") or []
                fn = next((f.get("functionName") for f in st if f.get("functionName")), None)
                # not this screen's: the gate's own loop (eval, __gateFarProbe) and the app-wide keyboard correction every screen runs on
                # every scroll event (setShift, build 313 - reported as INFO, untouched by this build)
                if not fn or fn in ("__gateFarProbe", "eval"): continue
                if fn == "setShift": app[fn] += 1; continue
                if (e["name"] == "UpdateLayoutTree" and (a.get("elementCount") or 0) > 0) or (e["name"] == "Layout" and e.get("tdur", 0) >= 50): forced[fn] += 1
            fr = max(1, s["frames"])
            task = sum(e.get("tdur", e["dur"]) for e in main if e["name"] == "RunTask") / 1000.0 / fr
            ts = sorted(s["times"]); p95 = ts[int(len(ts) * .95)] if ts else 0
            nf = sum(forced.values())
            print("INFO [%s] %s scroll: %d frames, %d script-forced style/layout passes %s, %.2fms main-thread task a frame, frame p95 %.1fms" % (cls, k, fr, nf, dict(forced.most_common(4)), task, p95) + " (app-wide, not counted: %s)" % dict(app), flush=True)
            chk("[%s] (U6) %s: no per-frame style or layout pass forced by script while scrolling (%d over %d frames)" % (cls, k, nf, fr), fr > 20 and nf <= fr / 10, dict(forced))
            chk("[%s] (U6) %s: under 10ms of main-thread work a frame (%.2f)" % (cls, k, task), fr > 20 and task < 10, task)
            chk("[%s] (U6) %s: no animation runs in a card a screen away (%s)" % (cls, k, s["far"]), s["far"] and max(s["far"]) == 0, s["far"])
    chk("[%s] no page errors (%s)" % (cls, errs[:2]), not errs, errs)
    ctx.close()
    # ---- U5: 85% and 135% text (Safari page zoom = a wider / narrower CSS viewport), and the iPad
    if wanted("U5"):
        for name, w, hh in (("85%", 518, 1125), ("135%", 326, 708), ("iPad", 834, 1194)):
            ctx, pg, errs = h["page"](br, text, seed, init, w=w, h=hh, scale=1)
            pg.wait_for_timeout(1000); h["quiet"](pg)
            for k in ["all"] + KINDS:
                st = pg.evaluate(OPEN, k)
                if st != "ok": chk("[%s] (U5) %s %s: the screen opens (%s)" % (cls, name, k, st), False); continue
                c = pg.evaluate(CLIP)
                chk("[%s] (U5) %s %s: nothing clipped, no sideways scroll (%d texts; %d bad)" % (cls, name, k, c["n"], len(c["bad"])),
                    c["n"] > 0 and not c["bad"] and not c["side"], [c["side"], c["bad"][:5]])
            ctx.close()

with sync_playwright() as p:
    br = p.chromium.launch(executable_path=h["g"]["CHROME"], args=["--no-sandbox"])
    for cls in ("academy", "ifc"):
        if CLS and CLS != cls: continue
        run_cls(br, cls)
    br.close()
print("\n%d PASS, %d FAIL" % (PASSES[0], len(FAILS)))
print("ALL PASS" if not FAILS else "FAILED")
sys.exit(1 if FAILS else 0)
