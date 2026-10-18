#!/usr/bin/env python3
"""Build 325, stream d: Nova's walkthrough as one story, What's New, the
returning tips, his "message me" broadcast once per account, the locked
character looks and the Qualifier's mark.

Madison (Oct 18): "Nova walk through for new accounts, when it shows the
characters ... only 4 even though it says 5 and it says there's 30 but only
shows like 10 ... Can we make it so all the unlockable characters you don't
have THAT aren't unlocked by a rank do this [blacked out]? ... the challenge
ones can all have the same challenge look, the secret flare ones can be how
they are, and the ultimate ones can be a little cooler like a glow ... the
badges are the same, mentions 16 badges and only shows a few ... we can't say
there were only 16 badges ... add another box or slide mentioning the
challenges and stuff to find them ... the story line for the non lit up flares
doesn't make sense ... For existing accounts ... it needs to feel more
surprising ... It doesn't mention virtual room ... Qualifier is a cool name,
not a fan of the icon though. Remove the skip button during this ... Remove
all of those from the what's new stuff ... only the ones with the 'new' at the
beginning need to be there, it doesn't need to say new though ... 'something
new, you can message me now' but I've seen it multiple times."

Every check here fails on the build before it (6fc16b7):

  python3 tools/check-b325-d.py
  python3 tools/check-b325-d.py --against /tmp/claude-0/wbase325/index.html

Exits non-zero on any failure.
"""
import importlib.util
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

# Click through one of Nova's dialogues; per line: the words, whether Skip is
# there, and (for the props worth asking about) what the stage shows.
TALK = r"""async (o) => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const id = o.id;
  for(let i = 0; i < 60 && !document.getElementById(id); i++) await wait(100);
  const el = document.getElementById(id);
  if(!el || !el.__nova) return { open: false, lines: [] };
  const out = { open: true, lines: [], skipSeen: false, signalBeforeFirst: false, props: {} };
  /* the signal, if any, is on the stage before he says a word */
  for(let i = 0; i < 40 && el.__nova.index < 0; i++){
    if(el.querySelector('.nt-signal')) out.signalBeforeFirst = true;
    await wait(100);
  }
  const vw = innerWidth, vh = innerHeight;
  for(let i = 0; i < 160 && el.isConnected; i++){
    if(el.querySelector('.nt-skip')) out.skipSeen = true;
    const nv = el.__nova, t = el.querySelector('.nt-text').textContent;
    if(out.lines[out.lines.length - 1] !== t){
      out.lines.push(t);
      await wait(700);
      const prop = [...el.querySelectorAll('.nt-prop')].filter(p => !p.classList.contains('is-out')).pop();
      if(prop){
        const cap = (prop.querySelector('.nt-cap') || {}).textContent || '';
        const par = prop.querySelector('.nt-parade');
        const kinds = [...prop.querySelectorAll('.nt-kind')].map(k => ({ cls: k.className, n: (k.querySelector('.nt-kind-n') || {}).textContent || '' }));
        const slots = prop.querySelectorAll('.nt-slot').length;
        const r = prop.firstElementChild ? prop.firstElementChild.getBoundingClientRect() : null;
        const vis = [...prop.querySelectorAll('.nt-kind, .nt-crewman, .nt-mode')].every(e => { const b = e.getBoundingClientRect(); return b.left >= -1 && b.right <= vw + 1 && b.top >= -1 && b.bottom <= vh + 1; });
        out.props[out.lines.length - 1] = { cap, parade: !!par, kinds, slots,
          parTiles: par ? par.querySelectorAll('.nt-slot').length : 0,
          lost: par ? par.querySelectorAll('.nt-crewman.is-lost').length : 0,
          crewFound: prop.querySelectorAll('.nt-crew .nt-crewman:not(.is-lost)').length,
          crewLost: prop.querySelectorAll('.nt-crew .nt-crewman.is-lost').length,
          vis, text: (prop.innerText || '').replace(/\s+/g, ' ').slice(0, 300) };
      }
    }
    if(nv.typing){ el.querySelector('.nt-stage').click(); await wait(40); continue; }
    const go = el.querySelector('.nt-go');
    if(go && getComputedStyle(go).display !== 'none'){ out.go = go.textContent; go.click(); break; }
    /* Escape must not end or skip it where there is no Skip */
    if(i === 3){ const before = nv.index; document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
      await wait(150); out.escMoved = nv.index !== before || !el.isConnected; if(!el.isConnected) break; }
    el.querySelector('.nt-stage').click(); await wait(60);
  }
  return out;
}"""

TOUR = """async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  for(let i = 0; i < 60 && !document.getElementById('tour-tooltip'); i++) await wait(100);
  await wait(400);
  const out = [];
  for(let i = 0; i < 20; i++){
    const tt = document.getElementById('tour-tooltip');
    if(!tt) break;
    out.push((document.getElementById('tour-text') || {}).textContent || '');
    document.getElementById('tour-next').click(); await wait(450);
  }
  return out;
}"""

TRUTH = """() => {
  const shown = AVATAR_CHARACTERS.filter(c => !(c.retired && store.avatarChar !== c.id) && !(c.legacy && isLockedCharacter(c.id)));
  const cat = c => c.retired || c.legacy ? 'kept' : c.ultimate ? 'ultimate' : c.secret ? 'secret' : c.feat ? 'challenge' : c.unlock ? 'rank' : 'starter';
  const kinds = {};
  shown.forEach(c => { const k = cat(c); kinds[k] = kinds[k] || [0, 0]; kinds[k][1]++; if(!isLockedCharacter(c.id)) kinds[k][0]++; });
  return { total: shown.length, have: shown.filter(c => !isLockedCharacter(c.id)).length, units: topicsIn(QUESTIONS).length, kinds,
           owned: shown.filter(c => !isLockedCharacter(c.id)).map(c => c.id) };
}"""


def story_checks(dev, r, truth, existing):
    lines = r.get("lines") or []
    props = r.get("props") or {}
    who = "existing" if existing else "new"
    txt = " | ".join(lines)
    # 1. the story's causes: the planet was cracking, then exploded; the
    #    flares are dark BECAUSE of the blast, and a rank relights one
    i_crack = next((i for i, t in enumerate(lines) if re.search(r"crack", t, re.I) and re.search(r"planet", t, re.I)), -1)
    i_boom = next((i for i, t in enumerate(lines) if re.search(r"explod", t, re.I)), -1)
    i_flare = next((i for i, t in enumerate(lines) if re.search(r"flares", t) and re.search(r"blast", t) and re.search(r"Home screen", t)), -1)
    i_relit = next((i for i, t in enumerate(lines) if re.search(r"flare", t) and re.search(r"rank", t) and re.search(r"earned", t)), -1)
    check("%s %s: the story runs in order - the planet cracking, then exploding, then his flares dark on your Home screen because of the blast, then a rank relighting one" % (dev, who),
          0 <= i_crack < i_boom < i_flare <= i_relit, {"crack": i_crack, "boom": i_boom, "flare": i_flare, "relit": i_relit, "head": lines[:6]})
    # 2. the Virtual Room is in the walkthrough
    check("%s %s: the walkthrough mentions the Virtual Room" % (dev, who), "Virtual Room" in txt, lines[-6:])
    # 3. no badge total, said or printed
    units = str(truth["units"])
    badge_lines = [t for t in lines if re.search(r"badge", t, re.I)]
    caps = " | ".join(p.get("cap", "") for p in props.values())
    bad = [t for t in badge_lines if re.search(r"\b%s\b" % units, t) or re.search(r"in all", t)] + \
          [c for c in caps.split(" | ") if re.search(r"badge", c, re.I) and re.search(r"\bof\s+%s\b" % units, c)]
    stage_badge = next((p for p in props.values() if p.get("parade") and re.search(r"badge", p.get("cap", ""), re.I)), None)
    check("%s %s: badges - no total said or printed, and every unit's badge is on the stage (%s)" % (dev, who, units),
          not bad and stage_badge is not None and stage_badge.get("parTiles") == truth["units"],
          {"bad": bad[:2], "tiles": stage_badge and stage_badge.get("parTiles"), "caps": caps[:200]})
    # 4. characters - every one shown, and the caption's numbers are the shown ones
    crew = next((p for p in props.values() if p.get("parade") and re.search(r"character", p.get("cap", ""), re.I)), None)
    m = re.search(r"(\d+)\s+of\s+(\d+)", (crew or {}).get("cap", ""))
    check("%s %s: characters - all %d drawn, and 'N of M found' counts what is drawn (M=%d, N=%d)" % (dev, who, truth["total"], truth["total"], truth["have"]),
          crew is not None and crew.get("parTiles") == truth["total"] and m and int(m.group(2)) == truth["total"] and int(m.group(1)) == truth["have"]
          and crew.get("parTiles") - crew.get("lost") == truth["have"],
          {k: (crew or {}).get(k) for k in ("cap", "parTiles", "lost")})
    # 5. a box on how they are found, its counts the table's
    kp = next((p for p in props.values() if p.get("kinds")), None)
    got = {}
    for k in (kp or {}).get("kinds") or []:
        kind = re.search(r"is-(\w+)", k["cls"]).group(1)
        mm = re.search(r"(\d+)\s+of\s+(\d+)", k["n"])
        got[kind] = [int(mm.group(1)), int(mm.group(2))] if mm else None
    want = {k: v for k, v in truth["kinds"].items() if k != "kept"}
    check("%s %s: a box on how characters are found - starters, ranks, challenges, secrets, ultimate - each 'have of total' from the table, all on screen" % (dev, who),
          kp is not None and got == want and kp.get("vis"), {"got": got, "want": want, "vis": (kp or {}).get("vis")})
    # 6. no Skip, and Escape does not skip either
    check("%s %s: no Skip on the introduction, and Escape does not skip it" % (dev, who),
          r.get("open") and not r.get("skipSeen") and r.get("escMoved") is False, {k: r.get(k) for k in ("open", "skipSeen", "escMoved")})


def check_story(br):
    print("\nd1. Nova's introduction: one story, both flows, both reference devices")
    for (w, h, dev) in DEVS:
        # a NEW account
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        pg.evaluate("() => { store.lifetime.points = 0; store.unitPerfects = {}; store.testHistory = []; saveStore(); }")
        truth = pg.evaluate(TRUTH)
        pg.evaluate("() => { playNovaIntro(() => {}, {}); }")
        r = pg.evaluate(TALK, {"id": "nova-intro"})
        story_checks(dev, r, truth, False)
        ctx.close()
        # an EXISTING account: a signal first, then 'you've already found some'
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        pg.evaluate("""() => { const U = topicsIn(QUESTIONS); store.unitPerfects = {}; U.slice(0, 3).forEach(u => store.unitPerfects[u] = badgeThresholdFor(u) + 1);
          store.rankFloor = 3; store.lifetime.points = xpForLevel(49) + 300; saveStore(); }""")
        truth = pg.evaluate(TRUTH)
        pg.evaluate("() => { playNovaIntro(() => {}, { existing: true }); }")
        r = pg.evaluate(TALK, {"id": "nova-intro"})
        story_checks(dev, r, truth, True)
        lines = r.get("lines") or []
        p1 = (r.get("props") or {}).get("1") or (r.get("props") or {}).get(1) or {}
        check("%s existing: a signal comes in before he says a word; he has not met them; and line two shows only characters they have found" % dev,
              r.get("signalBeforeFirst") and re.search(r"met", lines[0] if lines else "") and re.search(r"already found", lines[1] if len(lines) > 1 else "")
              and p1.get("crewFound", 0) > 0 and p1.get("crewLost") == 0,
              {"signal": r.get("signalBeforeFirst"), "l0": lines[:2], "p1": {k: p1.get(k) for k in ("crewFound", "crewLost", "cap")}})
        ctx.close()
    # Reduce motion: no signal, the first line is there at once
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
      theme.reduceMotion = true; applyTheme(); playNovaIntro(() => {}, { existing: true }); await wait(250);
      const el = document.getElementById('nova-intro');
      const out = { sig: !!document.querySelector('.nt-signal'), idx: el && el.__nova.index, typing: el && el.__nova.typing };
      theme.reduceMotion = false; applyTheme();
      /* and in motion, the signal is up first */
      el.__nova.close(); await wait(500); playNovaIntro(() => {}, { existing: true }); await wait(400);
      out.sigMotion = !!document.querySelector('#nova-intro .nt-signal'); return out; }""")
    check("the signal plays in motion and is skipped under Reduce motion (his first line at once)",
          r.get("sigMotion") and not r.get("sig") and r.get("idx") == 0 and not r.get("typing"), r)
    ctx.close()


def check_meeting(br):
    print("\nd2. the meeting: introduction, What's New, the new tips alone (no 'New'), goodbye - no Skip anywhere")
    for (w, h, dev) in DEVS:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        pg.evaluate("""() => { store.rankUpShown = TIER_ORDER_FULL.length; delete store.novaMet; saveStore(); localStorage.removeItem('class26e.intro.seen');
          window.__seen = []; new MutationObserver(() => { ['nova-intro', 'intro-pop', 'tour-tooltip'].forEach(id => {
            const e = document.getElementById(id); if(e && !e.__d){ e.__d = 1; window.__seen.push(id); } }); }).observe(document.body, { childList: true });
          showHome(); }""")
        intro = pg.evaluate(TALK, {"id": "nova-intro"})
        news = pg.evaluate(TALK, {"id": "intro-pop"})
        tips = pg.evaluate(TOUR)
        bye = pg.evaluate(TALK, {"id": "nova-intro"})
        want = pg.evaluate("() => { try{ return NOVA_NEW_TIPS_321.map(t => t.text); }catch(e){ return []; } }")
        seen = pg.evaluate("() => window.__seen")
        check("%s the meeting runs introduction, What's New, tips, goodbye, with no Skip in any of his three dialogues" % dev,
              intro.get("open") and news.get("open") and bye.get("open") and seen[:2] == ["nova-intro", "intro-pop"]
              and not intro.get("skipSeen") and not news.get("skipSeen") and not bye.get("skipSeen"),
              {"seen": seen, "skip": [intro.get("skipSeen"), news.get("skipSeen"), bye.get("skipSeen")]})
        check("%s the tips after What's New are only the once-'New' ones, and none starts 'New'" % dev,
              len(tips) == len(want) and len(want) >= 1 and not any(t.lower().startswith("new") for t in tips)
              and not any("Home always brings you back" in t for t in tips),
              {"tips": [t[:40] for t in tips], "want": len(want)})
        ctx.close()


def check_whatsnew(br):
    print("\nd3. Nova's What's New: the six minor items gone (still in the version history), real Version 9 additions in")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""() => {
      const lines = whatsNewLines(whatsNewState(), true).map(l => l.text).join(' | ');
      const rows = WHATS_NEW_320.map(x => (x.title + ' ' + x.body + ' ' + x.say));
      const hist = JSON.stringify(RELEASE_NOTES.map(v => v.groups.map(g => g.items.map(i => i.title + ' ' + i.body))));
      return { lines, rows, keys: WHATS_NEW_320.map(x => x.key), hist }; }""")
    gone = [("grade", r"grade (first|counts)|Results, grade first"), ("celebrate", r"celebrate|thrilled"),
            ("road map", r"road map"), ("cracks", r"planet that cracks|cracks a little more"),
            ("Supernova's mark", r"mark of the blast|Supernova’s mark"), ("daily ring", r"daily question ring|ring around (its|the daily)")]
    present = [n for n, rx in gone if re.search(rx, r["lines"] + " " + " ".join(r["rows"]), re.I)]
    in_hist = [n for n, rx in gone if re.search(rx, r["hist"], re.I)]
    check("none of the six is in Nova's What's New, and all six are still in the version history",
          not present and len(in_hist) == len(gone), {"present": present, "history": in_hist})
    adds = [n for n, rx in (("Qualifier", r"Qualifier"), ("Briefing", r"Briefing"), ("message him", r"Message Nova|message"),
                            ("challenge him", r"Challenge Nova|Sheriff"), ("study hours", r"study time|study hours"),
                            ("weekly recap", r"weekly recap|top three")) if re.search(rx, " ".join(r["rows"]), re.I)]
    check("Version 9's real additions are in it: the new modes, messaging and challenging Nova, study hours, the weekly recap",
          len(adds) == 6, adds)
    ctx.close()


def check_broadcast(br):
    print("\nd4. 'Something new: you can message me now' - once per account, not per device")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
      const fmt = d => d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0')
        + 'T' + String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0');
      const B = NOVA_BROADCASTS.find(b => /message me/.test(b.text)); if(!B) return { err: 'no broadcast' };
      /* time-independent: it went out an hour ago */
      B.at = fmt(new Date(Date.now() - 3600e3));
      const count = () => novaThread().filter(m => m.text === B.text).length;
      const out = {};
      /* DEVICE A: friends with him since before it went out - it comes, once */
      localStorage.removeItem('class26e.nova'); novaBefriend({ quiet: true });
      let s = novaState(); s.since = Date.now() - 2 * 3600e3; novaSave(s);
      showHome(); await wait(300); novaTick(); await wait(50); novaTick(); await wait(50);
      out.a = count();
      out.heard = !!(store.novaHeard && store.novaHeard[B.id]);
      const synced = JSON.parse(JSON.stringify(store));
      /* DEVICE B: the same account, a fresh device (its own class26e.nova),
         friends with him from earlier too - the account has had it */
      localStorage.removeItem('class26e.nova'); applyLoadedData(synced);
      novaBefriend({ quiet: true }); s = novaState(); s.since = Date.now() - 2 * 3600e3; novaSave(s);
      novaTick(); await wait(50); novaTick(); await wait(50);
      out.b = count();
      /* A NEW ACCOUNT made friends after it went out: his hello already says it */
      localStorage.removeItem('class26e.nova'); store.novaHeard = {};
      novaBefriend({ quiet: true }); s = novaState(); s.since = Date.now() - 1800e3; novaSave(s);
      novaTick(); await wait(50); novaTick(); await wait(50);
      out.fresh = count(); out.hello = (novaThread()[0] || {}).text || '';
      /* the record syncs: kept by a merge, defaulted on load */
      const d = { novaHeard: { x: 5 } }; try{ mergeSameAccount(d, { novaHeard: { x: 9, y: 2 } }); }catch(e){ out.mergeErr = String(e); }
      out.merged = d.novaHeard;
      const g = JSON.parse(JSON.stringify(store)); delete g.novaHeard; applyLoadedData(g); out.def = store.novaHeard;
      return out; }""")
    check("an account friends with him from before it went out gets it once, and the account records it",
          r.get("a") == 1 and r.get("heard"), r)
    check("a second device of that account does not get it again", r.get("a") == 1 and r.get("b") == 0, r)
    check("an account befriended after it went out never gets it (his hello already says it)",
          r.get("fresh") == 0 and re.search(r"message me", r.get("hello") or ""), {k: r.get(k) for k in ("fresh", "hello")})
    check("the record merges by the higher copy and defaults to none on load",
          (r.get("merged") or {}).get("x") == 9 and (r.get("merged") or {}).get("y") == 2 and r.get("def") == {}, {k: r.get(k) for k in ("merged", "def", "mergeErr")})
    ctx.close()


def check_locked_looks(br):
    print("\nd5. locked characters: challenge, secret and ultimate each blacked out in their own look; ranks as before")
    for (w, h, dev) in DEVS:
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT)
        r = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
          showCustomize('character'); await wait(1200);
          const cat = c => c.ultimate ? 'ultimate' : c.secret ? 'secret' : c.feat ? 'challenge' : c.unlock ? 'rank' : 'starter';
          const out = { rows: [] };
          AVATAR_CHARACTERS.forEach(c => {
            if(c.retired || c.legacy) return;
            const cell = [...document.querySelectorAll('.avatarchar-cell')].find(x => (x.querySelector('.avatarchar-option') || {}).title === (AVATAR_DISPLAY_NAME[c.id] || c.id));
            if(!cell) return;
            const opt = cell.querySelector('.avatarchar-option');
            const svg = opt.querySelector('svg.char-sil-svg');
            const rim = svg && svg.querySelector('.char-sil-rim [style*="stroke"]');
            out.rows.push({ id: c.id, cat: cat(c), locked: isLockedCharacter(c.id), sil: opt.classList.contains('is-silhouette'),
              look: (svg ? [...svg.classList].find(x => /^char-sil-(secret|challenge|ultimate)$/.test(x)) : null) || null,
              rim: rim ? rim.style.stroke : null, halo: svg ? svg.querySelectorAll('.char-sil-halo').length : 0,
              colour: !!opt.querySelector('svg.avatarchar-svg:not(.char-sil-svg)') });
          });
          /* the unlock card of a locked challenge character */
          const ch = AVATAR_CHARACTERS.find(c => c.feat && !c.secret && !c.ultimate && isLockedCharacter(c.id));
          if(ch){ showUnlockDetail(characterDetail(ch.id)); await wait(500);
            out.card = !!document.querySelector('.unlock-card-art.is-silhouette .char-sil');
            document.querySelectorAll('.invite-overlay, .unlock-card').forEach(e => e.remove()); }
          return out; }""")
        rows = r.get("rows") or []
        wrong = [x["id"] for x in rows if x["locked"] and x["cat"] in ("challenge", "secret", "ultimate") and not (x["sil"] and x["look"] == "char-sil-" + x["cat"])]
        rankwrong = [x["id"] for x in rows if x["locked"] and x["cat"] == "rank" and x["sil"]]
        rims = {c: sorted(set(x["rim"] for x in rows if x["cat"] == c and x["sil"])) for c in ("challenge", "secret", "ultimate")}
        shared = all(len(v) == 1 for v in rims.values()) and len(set(v[0] for v in rims.values() if v)) == 3
        ult = [x for x in rows if x["cat"] == "ultimate" and x["sil"]]
        check("%s Customize: every locked challenge, secret and ultimate character is a cut-out in its category's look; a rank's is not" % dev,
              rows and not wrong and not rankwrong and any(x["cat"] == "challenge" and x["sil"] for x in rows),
              {"wrong": wrong, "rank": rankwrong, "n": len(rows)})
        check("%s ...one shared look per category (one edge colour each, three different), and the ultimates glow" % dev,
              shared and ult and all(x["halo"] >= 1 for x in ult), {"rims": rims, "ultHalo": [x["halo"] for x in ult]})
        check("%s ...and a locked challenge character's card shows its cut-out, not the character" % dev, r.get("card") is True, r.get("card"))
        ctx.close()


def check_cutout_tops(br):
    print("\nd5b. the new cut-outs are not cut off: nothing of a challenge or ultimate cut-out in the top 6% of its tile")
    import io
    from PIL import Image
    for (w, h, dev), dpr in zip(DEVS, (3, 2)):
        ctx, pg = booted(br, w, h, seed=USED_ACCOUNT, dpr=dpr)
        pg.evaluate("async () => { showCustomize('character'); }")
        pg.wait_for_timeout(1200)
        tops = {}
        for look in ("challenge", "ultimate"):
            sel = ".avatarchar-option.is-sil-" + look
            if not pg.evaluate("(s) => !!document.querySelector(s)", sel):
                tops[look] = None
                continue
            pg.evaluate("(s) => document.querySelector(s).scrollIntoView({ block: 'center', behavior: 'instant' })", sel)
            for _ in range(80):
                n = pg.evaluate("""(s) => [...document.querySelectorAll(s)].filter(o => { const b = o.getBoundingClientRect(); return b.top > 0 && b.bottom < innerHeight; })
                  .map(o => !!o.querySelector('.char-flip-play img') || !o.classList.contains('char-flip'))""", sel)
                if n and all(n):
                    break
                pg.wait_for_timeout(400)
            pg.wait_for_timeout(500)
            tiles = pg.evaluate("""(s) => [...document.querySelectorAll(s)].map(o => { const b = o.getBoundingClientRect();
              return { id: o.title, box: [b.left, b.top, b.width, b.height] }; }).filter(t => t.box[1] > 0 && t.box[1] + t.box[3] < innerHeight)""", sel)
            shot = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
            for t in tiles:
                x, y, tw, th = t["box"]
                crop = shot.crop((int(x * dpr), int(y * dpr), int((x + tw) * dpr), int((y + th) * dpr)))
                W, H = crop.size
                px = crop.load()
                top = None
                for yy in range(0, int(H * .5)):
                    # a lit RUN wider than the sky's stars (about 1.5 CSS px), not a star
                    run = best = 0
                    for xx in range(int(W * .1), int(W * .9)):
                        run = run + 1 if sum(px[xx, yy]) / 3 >= 110 else 0
                        best = max(best, run)
                    if best >= 2 * dpr + 1:
                        top = yy / H
                        break
                tops[t["id"]] = round(top, 3) if top is not None else None
        bad = {k: v for k, v in tops.items() if v is not None and v < 0.06}
        seen = [k for k, v in tops.items() if v is not None]
        check("%s every challenge and ultimate cut-out in view clears the top 6%% of its tile" % dev,
              len(seen) >= 8 and not bad and tops.get("challenge", 1) is not None, tops)
        ctx.close()


def check_qualifier(br):
    print("\nd6. the Qualifier's mark is new: a seal with ribbon tails and a tick, not the shield")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    r = pg.evaluate("""() => { const s = modeIcon('exam'); document.body.appendChild(s);
      const paths = [...s.querySelectorAll('path')].map(p => p.getAttribute('d'));
      const out = { n: paths.length, seal: paths.some(d => (d.match(/Q/g) || []).length >= 10),
        solid: s.querySelectorAll('.modeiconsolid').length, check: !!s.querySelector('.modeiconcheck'),
        shield: paths.some(d => /^M12 2\\.2l8\\.1 3/.test(d)), fill: getComputedStyle(s.querySelector('.modeiconsolid') || s).fill };
      const rn = RELEASE_NOTES[0].groups.flatMap(g => g.items).find(i => /Qualifier/.test(i.title));
      try{ const ic = rn.icon(); out.notes = ic.classList.contains('modeicon-exam'); }catch(e){ out.notes = false; }
      s.remove(); return out; }""")
    check("modeIcon('exam'): a scalloped seal, solid ribbon tails and a bold tick; the shield is gone; the Version 9 note uses it",
          r.get("seal") and r.get("solid", 0) >= 1 and r.get("check") and not r.get("shield") and r.get("notes"), r)
    ctx.close()


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cb.CHROME)
        try:
            fns = os.environ.get("ONLY_FN")
            for fn in (fns.split(",") if fns else ["check_story", "check_meeting", "check_whatsnew", "check_broadcast", "check_locked_looks", "check_cutout_tops", "check_qualifier"]):
                globals()[fn](br)
        finally:
            br.close()
    cb.SERVER.shutdown()
    print("\n%s  (%d failure(s))" % ("ALL PASS" if not cb.FAILURES else "FAILED: " + ", ".join(cb.FAILURES), len(cb.FAILURES)))
    return 1 if cb.FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
