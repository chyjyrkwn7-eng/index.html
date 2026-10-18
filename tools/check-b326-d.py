#!/usr/bin/env python3
"""Build 326, stream d: Nova's introduction slides.

Madison (Oct 18, second list): "I did notice that when the badge one comes up
it lags and they don't start cycling till after a second, fix this. The
character one is the same, the character one is also good but all the not
unlocked ones there for this intro needs the same look, you did well with the
ones with like a blue outline and stripes ... The slide that explains how to
find each character is very badly shown and confusing, either fix it or
remove it. I kinda prefer briefing to be called review actually. I also don't
like the qualifier logo still. You can put the virtual room mode in that slide
too.. not just the 3 ... On the slide that says 'now Madison let's see how
you are doing' this could be way better ... it says there's only 3 secret
flares but there's more than that? ... If the main menu needs to now show
every single secret flare not lit up ... let's do that. It also talks about
how many characters you have found as if that's an achievement? ... I think
the character slide could have another one after it too but it would be for
banners and hundo effects maybe? ... it also doesn't mention anything about
your level if it went back some to reflect the new required gate stuff ...
Remove the weekly recap and badge case from what's new."

Every section fails on the build before it (build 325, 5869856):

  git show 5869856:index.html > /tmp/base325.html
  python3 tools/check-b326-d.py
  python3 tools/check-b326-d.py --against /tmp/base325.html
  ONLY_FN=check_lag,check_recap python3 tools/check-b326-d.py

Exits non-zero on any failure.
"""
import importlib.util
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py"))
cb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cb)
from playwright.sync_api import sync_playwright

check, booted, USED_ACCOUNT = cb.check, cb.booted, cb.USED_ACCOUNT
DEVS = ((440, 956, "17 Pro Max"), (834, 1194, "iPad Pro 11"))

NEW_ACCOUNT = "() => { store.lifetime.points = 0; store.unitPerfects = {}; store.testHistory = []; store.mysteryColorsFound = {}; saveStore(); }"
# three badges found (so the badge parade has struck badges in it), Gold
EXISTING = """() => { const U = topicsIn(QUESTIONS); store.unitPerfects = {}; U.slice(0, 3).forEach(u => store.unitPerfects[u] = badgeThresholdFor(u) + 1);
  store.levelFloor = 0; store.rankFloor = 3; store.levelWallRule = 325; store.lifetime.points = xpForLevel(49) + 300;
  store.mysteryColorsFound = { red: true }; saveStore(); }"""

# Walk to the line before the one matching `re`, the way a person reads: let
# each line finish, wait, tap. Then measure what happens when he moves on.
LAG = r"""async (o) => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const frame = () => new Promise(r => requestAnimationFrame(() => r(performance.now())));
  for(let i = 0; i < 60 && !document.getElementById('nova-intro'); i++) await wait(100);
  const el = document.getElementById('nova-intro');
  if(!el || !el.__nova) return { open: false };
  for(let i = 0; i < 60 && el.__nova.index < 0; i++) await wait(100);
  const lineAt = () => el.querySelector('.nt-text').textContent;
  let guard = 0;
  /* find the line by walking: stop on the line BEFORE the target */
  while(guard++ < 40){
    if(el.__nova.typing) el.__nova.advance();
    await wait(o.read);
    /* peek: what the next line is, without moving on */
    const L = novaIntroLines(o.existing ? { existing: true } : {});
    const nx = L[el.__nova.index + 1];
    if(nx && new RegExp(o.re).test(nx.text)) break;
    el.__nova.advance(); await wait(60);
  }
  if(el.__nova.typing) el.__nova.advance();
  await wait(o.read);
  const stage = el.querySelector('.nt-stage');
  const out = { open: true };
  /* made ahead: the slide is already on the stage, invisible, measured */
  const pre = stage.querySelector('.nt-prop.is-prepped ' + o.sel);
  out.prepped = !!pre;
  if(pre){
    const rows = [...pre.querySelectorAll('.nt-parade-row:not(.is-still) .nt-parade-track')];
    out.preMeasured = rows.length > 0 && rows.every(t => Math.abs(parseFloat(t.style.getPropertyValue('--pan')) || 0) > 4);
  }
  /* no badge struck again once it is up */
  let restruck = 0;
  const mo = new MutationObserver(ms => ms.forEach(m => { if(m.target.closest && m.target.closest(o.sel)) restruck++; }));
  mo.observe(stage, { subtree: true, attributes: true, attributeFilter: ['href'] });
  const svgsBefore = new Set(stage.querySelectorAll('svg'));
  const t0 = performance.now();
  el.__nova.advance();
  out.syncMs = Math.round(performance.now() - t0);
  const svgsAfter = [...stage.querySelectorAll('svg')];
  out.builtInTap = svgsAfter.filter(s => !svgsBefore.has(s)).length;
  const live = () => [...stage.querySelectorAll('.nt-prop:not(.is-out):not(.is-prepped)')].pop();
  const p = live();
  out.inSameTask = !!(p && p.querySelector(o.sel) && p.classList.contains('is-in'));
  /* the glide: no wait, running, moving from the first frames */
  const tr = p && p.querySelector('.nt-parade-row:not(.is-still) .nt-parade-track');
  const xs = [];
  if(tr){
    const an = tr.getAnimations().find(a => a.animationName === 'nt-pan');
    if(an){ const t = an.effect.getComputedTiming(); out.delay = t.delay; }
    for(let i = 0; i < 6; i++){ await frame(); xs.push(new DOMMatrix(getComputedStyle(tr).transform).m41);
      if(i === 0 && an){ out.firstFrame = { state: an.playState, progress: an.effect.getComputedTiming().progress }; } }
  }
  out.moved = xs.length > 2 && Math.abs(xs[xs.length - 1] - xs[0]) > 0.3;
  out.xs = xs.map(x => Math.round(x * 10) / 10);
  await wait(1200);
  mo.disconnect();
  out.restruck = restruck;
  return out;
}"""

# Click through one dialogue; per line: the words and what the stage shows.
TALK = r"""async (o) => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  for(let i = 0; i < 60 && !document.getElementById(o.id); i++) await wait(100);
  const el = document.getElementById(o.id);
  if(!el || !el.__nova) return { open: false, lines: [] };
  for(let i = 0; i < 60 && el.__nova.index < 0; i++) await wait(100);
  const vw = innerWidth, vh = innerHeight;
  const out = { open: true, lines: [], props: [] };
  const inView = e => { const b = e.getBoundingClientRect(); return b.width > 0 && b.left >= -1 && b.right <= vw + 1 && b.top >= -1 && b.bottom <= vh + 1; };
  for(let i = 0; i < 200 && el.isConnected; i++){
    const nv = el.__nova, t = el.querySelector('.nt-text').textContent;
    if(out.lines[out.lines.length - 1] !== t){
      out.lines.push(t);
      await wait(o.hold || 1700);
      const p = [...el.querySelectorAll('.nt-prop')].filter(x => !x.classList.contains('is-out') && !x.classList.contains('is-prepped')).pop();
      const snap = { i: out.lines.length - 1, kind: null };
      if(p){
        const stageR = el.querySelector('.nt-stage').getBoundingClientRect();
        snap.cap = (p.querySelector('.nt-cap') || {}).textContent || '';
        snap.text = (p.innerText || '').replace(/\s+/g, ' ').slice(0, 400);
        if(p.querySelector('.nt-badgepar')) snap.kind = 'badges';
        else if(p.querySelector('.nt-crewpar')) snap.kind = 'crew';
        else if(p.querySelector('.nt-kinds')) snap.kind = 'kinds';
        else if(p.querySelector('.nt-flair')) snap.kind = 'flair';
        else if(p.querySelector('.nt-modes') || p.querySelectorAll('.nt-mode').length >= 3) snap.kind = 'modes';
        else if(p.querySelector('.nt-rc, .nt-recap')) snap.kind = 'recap';
        if(snap.kind === 'crew'){
          const tiles = [...p.querySelectorAll('.nt-crewman')];
          snap.crew = tiles.map(t => { const sv = t.querySelector('svg.char-sil-svg');
            const rim = sv && sv.querySelector('.char-sil-rim [style*="stroke"]');
            const pat = sv && sv.querySelector('pattern');
            return { lost: t.classList.contains('is-lost'), look: sv ? ([...sv.classList].find(c => /^char-sil-(secret|challenge|ultimate)$/.test(c)) || '') : '',
                     rim: rim ? rim.style.stroke : '', hatched: !!pat, grey: t.classList.contains('is-ranklocked') }; });
        }
        if(snap.kind === 'kinds'){
          const cards = [...p.querySelectorAll('.nt-kind')];
          snap.kinds = cards.map(c => { const b = c.getBoundingClientRect(); const how = c.querySelector('.nt-kind-how, .nt-kind-t span');
            const ic = c.querySelector('.nt-kind-ic svg, .nt-kind-ic');
            const lh = how ? parseFloat(getComputedStyle(how).lineHeight) || 16 : 16;
            return { cls: c.className, n: (c.querySelector('.nt-kind-n') || {}).textContent || '', x: Math.round(b.left), y: Math.round(b.top),
                     icon: ic ? Math.round(ic.getBoundingClientRect().width) : 0, char: !!c.querySelector('.nt-crewman'),
                     lines: how ? Math.round(how.getBoundingClientRect().height / lh) : 0, howPx: how ? parseFloat(getComputedStyle(how).fontSize) : 0,
                     fits: c.scrollWidth <= c.clientWidth + 1, inView: inView(c) && b.top >= stageR.top - 1 && b.bottom <= stageR.bottom + 1 }; });
        }
        if(snap.kind === 'flair'){
          snap.banners = [...p.querySelectorAll('.nt-flair-sec.is-banners .nt-flair-item')].map(f => ({ id: ((f.querySelector('.bnr') || { className: '' }).className.match(/bnr-(\w+)/) || [])[1] || '',
            name: (f.querySelector('figcaption') || {}).textContent || '', inView: inView(f) }));
          snap.fx = [...p.querySelectorAll('.nt-flair-sec.is-fx .nt-flair-item')].map(f => ({ id: (f.querySelector('.hfx-stage') || { dataset: {} }).dataset.fx || '',
            name: (f.querySelector('figcaption') || {}).textContent || '', inView: inView(f) }));
        }
        if(snap.kind === 'modes'){
          snap.modes = [...p.querySelectorAll('.nt-mode')].map(m => ({ title: ((m.querySelector('b') || m.querySelector('span:last-child') || {}).textContent || '').trim(),
            icon: ((m.querySelector('svg.modeicon') || { getAttribute: () => '' }).getAttribute('class') || ''), line: !!m.querySelector('.nt-mode-t > span'), inView: inView(m) }));
        }
        if(snap.kind === 'recap'){
          const c = p.querySelector('.nt-rc');
          snap.recap = c ? { tiles: [...c.querySelectorAll('.nt-rc-tile')].map(t => t.className.replace('nt-rc-tile', '').trim().split(' ')[0]),
            secret: c.querySelectorAll('.nt-rc-sf').length, secretLit: c.querySelectorAll('.nt-rc-sf.is-found').length,
            flares: c.querySelectorAll('.nt-rc-flare').length, flaresLit: c.querySelectorAll('.nt-rc-flare.is-lit').length,
            bar: !!c.querySelector('.nt-rc-bar i'), level: (c.querySelector('.nt-rc-level') || {}).textContent || '',
            inView: inView(c) && c.getBoundingClientRect().top >= stageR.top - 1 && c.getBoundingClientRect().bottom <= stageR.bottom + 1,
            revealed: c.classList.contains('is-in') } : null;
        }
      }
      out.props.push(snap);
    }
    if(nv.typing){ el.querySelector('.nt-stage').click(); await wait(40); continue; }
    const go = el.querySelector('.nt-go');
    if(go && getComputedStyle(go).display !== 'none'){ out.go = go.textContent; go.click(); break; }
    el.querySelector('.nt-stage').click(); await wait(60);
  }
  return out;
}"""


def kinds_truth(pg):
    return pg.evaluate("""() => {
      const shown = AVATAR_CHARACTERS.filter(c => !(c.retired && store.avatarChar !== c.id) && !(c.legacy && isLockedCharacter(c.id)));
      const cat = c => c.retired || c.legacy ? 'kept' : c.ultimate ? 'ultimate' : c.secret ? 'secret' : c.feat ? 'challenge' : c.unlock ? 'rank' : 'starter';
      const k = {}; shown.forEach(c => { const x = cat(c); k[x] = k[x] || [0, 0]; k[x][1]++; if(!isLockedCharacter(c.id)) k[x][0]++; });
      return { kinds: k, locked: shown.filter(c => isLockedCharacter(c.id)).length, owned: shown.filter(c => !isLockedCharacter(c.id)).length }; }""")


def check_lag(br):
    print("\nd1. the badge and character slides: made ahead, no stall, the glide moving from its first frame, no badge struck again")
    for (w, h, dev) in DEVS:
        for which, rx, sel in (("badges", r"badges were scattered", ".nt-badgepar"), ("characters", r"crew got away", ".nt-crewpar")):
            for throttle in (1, 4):
                ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, dpr=2 if w < 600 else 1)
                if throttle > 1:
                    cdp = ctx.new_cdp_session(pg)
                    cdp.send("Emulation.setCPUThrottlingRate", {"rate": throttle})
                pg.evaluate(EXISTING)
                pg.evaluate("() => playNovaIntro(() => {}, { existing: true })")
                r = pg.evaluate(LAG, {"re": rx, "sel": sel, "read": 900, "existing": True})
                ctx.close()
                tag = "%s %s%s" % (dev, which, " (CPU x4)" if throttle > 1 else "")
                check("%s: the slide was made while the line before it was said, its rows already measured" % tag,
                      r.get("prepped") and r.get("preMeasured"), {k: r.get(k) for k in ("prepped", "preMeasured")})
                check("%s: moving on draws nothing new - the slide comes in in the same tap" % tag,
                      r.get("inSameTask") and r.get("builtInTap") == 0, {k: r.get(k) for k in ("inSameTask", "builtInTap", "syncMs")})
                check("%s: the glide has no wait and is already moving on its first frame" % tag,
                      r.get("delay") is not None and r.get("delay") <= 0 and (r.get("firstFrame") or {}).get("state") == "running"
                      and ((r.get("firstFrame") or {}).get("progress") or 0) > 0 and r.get("moved"),
                      {k: r.get(k) for k in ("delay", "firstFrame", "moved", "xs")})
                if which == "badges":
                    check("%s: no badge on it is struck again once it is up" % tag, r.get("restruck") == 0, r.get("restruck"))


def check_story(br):
    print("\nd2. the slides, both flows, both reference devices: one locked look, how they're found, banners and effects, every mode")
    for (w, h, dev) in DEVS:
        for existing in (False, True):
            who = "existing" if existing else "new"
            ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
            pg.evaluate(EXISTING if existing else NEW_ACCOUNT)
            truth = kinds_truth(pg)
            picker = pg.evaluate("""async () => { showModeSelect(); await new Promise(r => setTimeout(r, 400));
              return [...document.querySelectorAll('.modecard')].map(c => ((c.querySelector('.modecardtitle') || c.querySelector('b, strong, h3') || {}).textContent || '').trim()).filter(Boolean); }""")
            tables = pg.evaluate("() => ({ banners: BANNERS.map(b => [b.id, b.name]), fx: HUNDO_FX.map(d => [d.id, d.name]) })")
            pg.evaluate("() => { showHome(); playNovaIntro(() => {}, %s); }" % ("{ existing: true }" if existing else "{}"))
            r = pg.evaluate(TALK, {"id": "nova-intro", "hold": 1500})
            ctx.close()
            props = r.get("props") or []
            order = [p.get("kind") for p in props if p.get("kind")]
            seq = []
            for k in order:
                if not seq or seq[-1] != k:
                    seq.append(k)
            idx = {k: seq.index(k) if k in seq else -1 for k in ("badges", "crew", "kinds", "flair", "modes")}
            check("%s %s: badges, then the crew, how they come home, banners and effects, and later every mode" % (dev, who),
                  0 <= idx["badges"] < idx["crew"] < idx["kinds"] < idx["flair"] < idx["modes"], seq)
            # one locked look
            crew = next((p for p in props if p.get("kind") == "crew"), {}).get("crew") or []
            lost = [c for c in crew if c["lost"]]
            same = lost and all(c["look"] == "char-sil-challenge" and c["hatched"] and (c["rim"] or "").replace(" ", "") in ("rgb(127,163,214)", "#7fa3d6") and not c["grey"] for c in lost)
            check("%s %s: every character not yet yours is the one striped, steel-blue-edged cut-out (%d of them); the rest in colour" % (dev, who, truth["locked"]),
                  same and len(lost) == truth["locked"] and len(crew) - len(lost) == truth["owned"]
                  and all(not c["look"] for c in crew if not c["lost"]),
                  {"looks": sorted(set((c["look"], c["rim"], c["hatched"]) for c in lost)), "lost": len(lost), "want": truth["locked"]})
            # how they're found
            kp = next((p for p in props if p.get("kind") == "kinds"), {}).get("kinds") or []
            got = {}
            for k in kp:
                m = re.search(r"is-(\w+)", k["cls"]); mm = re.search(r"(\d+)\s+of\s+(\d+)", k["n"])
                if m:
                    got[m.group(1)] = [int(mm.group(1)), int(mm.group(2))] if mm else None
            want = {k: v for k, v in truth["kinds"].items() if k not in ("kept", "starter")}
            cols = sorted(set(k["x"] for k in kp)); rows_ = sorted(set(k["y"] for k in kp))
            check("%s %s: how they come home - a card per way (ranks, challenges, secrets, ultimate), counts from the table" % (dev, who),
                  got == want, {"got": got, "want": want})
            check("%s %s: ...two by two, each led by a mark (not a character), one short line, all on the stage, nothing cut off" % (dev, who),
                  len(kp) == 4 and len(cols) == 2 and len(rows_) == 2 and all(k["icon"] >= 30 and not k["char"] and 1 <= k["lines"] <= 2
                                                                              and k["howPx"] >= 12 and k["fits"] and k["inView"] for k in kp),
                  [{x: k.get(x) for x in ("icon", "char", "lines", "howPx", "fits", "inView")} for k in kp])
            # banners and effects
            fp = next((p for p in props if p.get("kind") == "flair"), None)
            fi = next((i for i, p in enumerate(props) if p.get("kind") == "flair"), -1)
            fline = (r.get("lines") or [""])[fi] if fi >= 0 else ""
            bid = dict(tables["banners"]); fid = dict(tables["fx"])
            ok_b = fp and len(fp.get("banners") or []) >= 3 and all(b["id"] in bid and bid[b["id"]] == b["name"] and b["inView"] for b in fp["banners"])
            ok_f = fp and len(fp.get("fx") or []) >= 3 and all(x["id"] in fid and fid[x["id"]] == x["name"] and x["inView"] for x in fp["fx"])
            check("%s %s: a slide on banners and hundo effects - real ones from the tables, named, on screen - and where to find them, with no number said" % (dev, who),
                  ok_b and ok_f and re.search(r"banner", fline, re.I) and re.search(r"hundo", fline, re.I) and "Customize" in fline and not re.search(r"\d", fline),
                  {"banners": (fp or {}).get("banners"), "fx": (fp or {}).get("fx"), "line": fline})
            # every mode
            mp = next((p for p in props if p.get("kind") == "modes"), {}).get("modes") or []
            check("%s %s: the modes slide shows every mode the picker offers (%s), each with its mark and a line, on screen" % (dev, who, ", ".join(picker)),
                  [m["title"] for m in mp] == picker and len(picker) >= 4 and all("modeicon" in m["icon"] and m["line"] and m["inView"] for m in mp),
                  {"slide": [m["title"] for m in mp], "picker": picker})
            # no secret-flare total in his voice, anywhere
            lines = r.get("lines") or []
            bad = [t for t in lines if re.search(r"\b(?:only|just|all)\s+(?:three|3|six|6)\b|\b(?:three|3|six|6)\s+secret flares|secret flares[^.]*\bof\s+\d", t, re.I)]
            check("%s %s: he never gives a number of secret flares there are" % (dev, who), not bad, bad)


def check_recap(br):
    print("\nd3. 'let's see how you're doing': a card of what you have earned, the level said truthfully, no character count, no secret-flare total")
    cases = (
        ("plain", "Gold at 49, under its wall", 3, 49, 0, 3, {"red": True}),
        ("held", "Bronze held at Silver's level 30 with saved levels", 2, 35, 0, 0, {}),
        ("kept", "kept above the wall by 325's grandfather floor", 0, 45, 40, 0, {"red": True, "orange": True}),
    )
    for (w, h, dev) in DEVS + ((375, 667, "SE 2/3"),):
        for key, label, badges, lvl, floor, rf, found in cases:
            if dev == "SE 2/3" and key != "held":
                continue
            ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
            st = pg.evaluate("""(a) => { const U = topicsIn(QUESTIONS); store.unitPerfects = {}; U.slice(0, a[0]).forEach(u => store.unitPerfects[u] = badgeThresholdFor(u) + 1);
              store.levelFloor = a[2]; store.rankFloor = a[3]; store.levelWallRule = 325; store.lifetime.points = xpForLevel(a[1]) + 10; store.mysteryColorsFound = a[4]; saveStore();
              const ls = levelStateFor(store);
              return { level: levelOf(store), rank: rankOf(store) ? RANK_DISPLAY_NAME[rankOf(store)] : null, held: ls.held, gate: ls.gateKey ? RANK_DISPLAY_NAME[ls.gateKey] : null,
                       secrets: MYSTERY_ORDER.length, found: MYSTERY_ORDER.filter(k => a[4][k]).length, badges: badgeCountOf(store) }; }""",
                             [badges, lvl, floor, rf, found])
            pg.evaluate("() => { showHome(); playNovaIntro(() => {}, { existing: true }); }")
            r = pg.evaluate(TALK, {"id": "nova-intro", "hold": 1600})
            ctx.close()
            lines = r.get("lines") or []
            ri = next((i for i, p in enumerate(r.get("props") or []) if p.get("kind") == "recap"), -1)
            tail = lines[ri:] if ri >= 0 else []
            rc = (r.get("props") or [{}])[ri].get("recap") if ri >= 0 else None
            said = " ".join(tail)
            tag = "%s %s (%s)" % (dev, key, label)
            check("%s: the recap is a card - who you are, your XP bar, then badges, hundos, flares lit and every secret flare there is" % tag,
                  rc and rc["tiles"] == ["is-badges", "is-hundos", "is-flares", "is-secret"] and rc["bar"] and rc["secret"] == st["secrets"]
                  and rc["secretLit"] == st["found"] and rc["flares"] == 7 and rc["revealed"], rc)
            check("%s: ...and it all fits the stage" % tag, rc and rc["inView"], rc and rc.get("inView"))
            stage = " ".join((p.get("text") or "") for p in (r.get("props") or [])[ri:]) if ri >= 0 else ""
            check("%s: no character count, and no total of secret flares, said or printed" % tag,
                  ri >= 0 and not re.search(r"character|crew", said, re.I) and not re.search(r"characters found", stage, re.I)
                  and not re.search(r"of\s+\d+\s+secret", stage + " " + said, re.I),
                  {"said": tail, "stage": stage[:200]})
            lv = "level %d" % st["level"]
            if key == "plain":
                ok = lv in said and st["rank"] in said and not re.search(r"gate|wait", said, re.I)
            elif key == "held":
                ok = lv in said.lower() and re.search(r"\bgate\b", said) and st["gate"] in said and re.search(r"badge", said) and re.search(r"paid for", said)
            else:
                ok = lv in said.lower() and re.search(r"keep level %d" % st["level"], said) and st["gate"] in said and re.search(r"nobody loses a level", said)
            check("%s: he says your level, and what the level wall means for you (held: the gate; kept: you keep it; neither: nothing)" % tag, ok,
                  {"state": st, "said": tail})


def check_home_flares(br):
    print("\nd4. Home shows every secret flare - the found ones lit, the rest dark - and they still answer a tap")
    for (w, h, dev) in DEVS:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
          store.mysteryColorsFound = { red: true }; store.rankUpShown = TIER_ORDER_FULL.length; saveStore(); showHome(); await wait(900);
          const hero = document.querySelector('.panel.home .cosmic-hero-wrap'); const H = hero.getBoundingClientRect();
          const dots = [...hero.querySelectorAll('.cosmic-flare-dot')];
          const box = d => d.getBoundingClientRect();
          const out = { n: dots.length, want: MYSTERY_ORDER.length, keys: dots.map(d => d.dataset.flare),
            found: dots.filter(d => d.classList.contains('is-found')).map(d => d.dataset.flare),
            tints: [...new Set(dots.filter(d => !d.classList.contains('is-found')).map(d => getComputedStyle(d).getPropertyValue('--fc').trim().toUpperCase()))],
            inside: dots.every(d => { const b = box(d); return b.left >= H.left - 2 && b.right <= H.right + 2 && b.top >= H.top - 2 && b.bottom <= H.bottom + 2; }) };
          /* no two flares on top of each other */
          let clash = 0;
          for(let i = 0; i < dots.length; i++) for(let j = i + 1; j < dots.length; j++){ const a = box(dots[i]), b = box(dots[j]);
            if(Math.hypot((a.left + a.right) / 2 - (b.left + b.right) / 2, (a.top + a.bottom) / 2 - (b.top + b.bottom) / 2) < a.width) clash++; }
          out.clash = clash;
          const miss = dots.find(d => d.dataset.flare === 'core');
          if(miss){ miss.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true })); miss.dispatchEvent(new PointerEvent('pointerup', { bubbles: true })); miss.click(); await wait(500);
            out.caption = (document.querySelector('.home-caption, .hc-item') || {}).textContent || ''; }
          return out; }""")
        ctx.close()
        check("%s every secret flare is on Home's planet (%s), the found one lit, the rest the colourless unfound marble" % (dev, r.get("want")),
              r.get("n") == r.get("want") and r.get("found") == ["red"] and r.get("tints") == ["#C9D2DF"], r)
        check("%s ...inside the planet system, no two on top of each other, and a dark one still answers a tap" % dev,
              r.get("inside") and r.get("clash") == 0 and "Secret flare" in (r.get("caption") or ""), {k: r.get(k) for k in ("inside", "clash", "caption")})


def check_review_name(br):
    print("\nd5. Briefing is Review again, everywhere a person reads it")
    src = io.open(cb.SRC, encoding="utf-8").read()
    # every string literal (single, double or backtick) that says it
    lits = [m.group(0) for m in re.finditer(r'"[^"\n]*"|\'[^\'\n]*\'', src) if re.search(r"briefing", m.group(0), re.I)]
    check("no string in the app says Briefing", not lits, lits[:6])
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      out.title = modeTitleOf('review'); out.begin = beginLabelOf('review');
      showModeSelect(); await wait(400);
      out.card = [...document.querySelectorAll('.modecard')].map(c => (c.textContent || '')).find(t => /Not a test/.test(t)) || '';
      out.activity = (ACTIVITY_TEXT.review || []).join(' | ');
      out.news = WHATS_NEW_320.map(x => x.title + ' ' + x.body + ' ' + x.say).join(' | ');
      out.v9 = RELEASE_NOTES[0].groups.flatMap(g => g.items).map(i => i.title + ' ' + i.body).join(' | ');
      return out; }""")
    ctx.close()
    check("the mode is called Review: its title, Begin review, the picker card, the friends' activity line",
          r.get("title") == "Review" and r.get("begin") == "Begin review" and r.get("card", "").startswith("Review") and "Review" in r.get("activity", ""),
          {k: (r.get(k) or "")[:60] for k in ("title", "begin", "card", "activity")})
    hits = re.findall(r"[^.|]*[Bb]riefing[^.|]*", r.get("news", "") + " | " + r.get("v9", ""))
    check("What's New and Version 9's notes do not call anything the Briefing", not hits, hits[:3])


def check_qualifier_icon(br):
    print("\nd6. the Qualifier's mark is new: a tick through a ring, at the target's weight, and the same mark everywhere it appears")
    for (w, h, dev) in DEVS:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const out = {};
          const sig = s => s ? [...s.querySelectorAll('path, circle')].map(p => p.getAttribute('d') || ('c' + p.getAttribute('r'))).join('|') : '';
          const ref = modeIcon('exam'); out.ref = sig(ref);
          const paths = [...ref.querySelectorAll('path')].map(p => p.getAttribute('d'));
          out.seal = paths.some(d => (d.match(/Q/g) || []).length >= 10); out.tails = !!ref.querySelector('.modeiconsolid');
          out.ring = paths.some(d => /A\\s*8\\.\\d/.test(d)); out.tick = !!ref.querySelector('.modeiconcheck');
          showModeSelect(); await wait(400);
          out.picker = sig(document.querySelector('.modecard .modeicon-exam'));
          out.news = (() => { const it = WHATS_NEW_320.find(x => x.key === 'modes'); if(!it) return ''; const row = introRow(it.icon || it.glyph, it.color, it.title, it.body); return sig(row.querySelector('svg.modeicon-exam')); })();
          out.notes = (() => { const it = RELEASE_NOTES[0].groups.flatMap(g => g.items).find(i => /Qualifier/.test(i.title)); try{ return sig(it.icon()); }catch(e){ return ''; } })();
          out.slide = sig(novaModeRow().querySelector('.modeicon-exam'));
          return out; }""")
        ctx.close()
        same = all(r.get(k) == r.get("ref") for k in ("picker", "news", "notes", "slide"))
        check("%s modeIcon('exam'): one ring and a bold tick - no seal, no ribbon tails" % dev,
              r.get("ring") and r.get("tick") and not r.get("seal") and not r.get("tails"), {k: r.get(k) for k in ("ring", "tick", "seal", "tails")})
        check("%s ...the same mark on the mode picker, What's New, Version 9's notes and Nova's modes slide" % dev, same and bool(r.get("ref")),
              {k: (r.get(k) or "")[:30] for k in ("ref", "picker", "news", "notes", "slide")})


def check_whatsnew(br):
    print("\nd7. What's New: no weekly recap, no Level 1 Badge Case (both still in the version history)")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""() => { const st = whatsNewState();
      const lines = whatsNewLines(st, true).map(l => l.text).join(' | ');
      const rows = WHATS_NEW_320.map(x => x.title + ' ' + x.body + ' ' + x.say).join(' | ');
      const hist = JSON.stringify(RELEASE_NOTES.map(v => v.groups.map(g => g.items.map(i => i.title))));
      return { lines, rows, n: WHATS_NEW_320.length, hist }; }""")
    ctx.close()
    gone = [n for n, rx in (("weekly recap", r"weekly recap|top three"), ("badge case", r"badge case")) if re.search(rx, r["lines"] + " " + r["rows"], re.I)]
    kept = [n for n, rx in (("weekly recap", r"Weekly Recap"), ("badge case", r"Level 1 Badge Case")) if re.search(rx, r["hist"])]
    check("neither is in his What's New (%d rows), and both are still in the version history" % r["n"], not gone and len(kept) == 2, {"present": gone, "history": kept})


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cb.CHROME)
        try:
            fns = os.environ.get("ONLY_FN")
            for fn in (fns.split(",") if fns else ["check_lag", "check_story", "check_recap", "check_home_flares", "check_review_name",
                                                   "check_qualifier_icon", "check_whatsnew"]):
                globals()[fn](br)
        finally:
            br.close()
    cb.SERVER.shutdown()
    print("\n%s  (%d failure(s))" % ("ALL PASS" if not cb.FAILURES else "FAILED: " + ", ".join(cb.FAILURES), len(cb.FAILURES)))
    return 1 if cb.FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
