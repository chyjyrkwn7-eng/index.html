#!/usr/bin/env python3
"""Build 326, package e: Nova's story told with a cause, a payoff and no end;
when he speaks after his introduction (one scheduler, one message a day, on
Home only); his weekly challenge with Accept; his progress messages; and the
in-world "away".

Madison (Oct 18): "I think the storyline is still kinda missing something,
what happens when we bring him back his stuff, why is our own planet system
cracking? What do we get for helping him? What's he do when he finds the
badges and characters and stuff? ... I need clarity on when nova will be
seen/come back after his introduction? Will it be when you rank up? If
that's the case, only make his messages appear or get to you when you are
out of the profile tab ... maybe when you finally get back to the main menu?
Let's also ensure you get like a challenge to play him once a week ... he
will randomly send you messages when you make progress with helping him.
Let's not make it where they double up though or become spam whatsoever.
When nova says he away in chat make it more game/storyline like ... Do we
save Mr nova by finding everything? Idk it's hard because we will get more
levels and ranks at some point and more badges and stuff."

Every check here fails on build 325 (5869856):

  python3 tools/check-b326-e.py
  python3 tools/check-b326-e.py --against /path/to/325/index.html

ONLY_FN=check_story,check_day,... runs just those sections.
Exits non-zero on any failure.
"""
import datetime
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
SHOTS = os.environ.get("SHOTS")
SEED = USED_ACCOUNT.replace('"onboardingComplete":true,', '"onboardingComplete":true,"novaMet":1,"publicId":"PUBMADISON01",', 1)

# A Wednesday morning, local time (the container runs on UTC): not the
# recap's Tuesday, not a Monday.
WED = datetime.datetime(2026, 10, 21, 10, 0)


def at(pg, when):
    pg.clock.set_system_time(when)


# Helpers every scenario uses. `kinds()` is what he has said on his own
# (rank-up, broadcast, challenge, progress, tip) - never a reply or hello.
PRE = r"""
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const D = 86400e3;
  const OWN = ['rank', 'broadcast', 'challenge', 'progress', 'tip'];
  const own = () => novaThread().filter(m => m.key === 'nova' && OWN.indexOf(m.kind) >= 0);
  const clearTop = () => { document.querySelectorAll('.daily-alert, .vroom-chat-alert, .tierup-banner, #daily-lock-tip').forEach(e => e.remove());
    document.querySelectorAll('.daily-question-fab.is-charging').forEach(e => e.classList.remove('is-charging'));
    try{ popupGapUntil = 0; }catch(e){} try{ if(chatDockOpen) closeChatDock(); }catch(e){} };
  /* his own clock (the minute interval, a screen's tick-soon) is held
     while a scenario is set up and the system time moved; the scenario
     ticks him itself, through the same function */
  if(!window.__realTick){ window.__realTick = novaTick; novaTick = function(){ if(window.__hold) return; return window.__realTick.apply(this, arguments); }; }
  window.__hold = true;
  /* MOVED IN 327z15: "The challenges from nova need to be random" - his
     challenge now comes two weeks in five, on a day of its own
     (novaChallengeDue). What these scenarios measure is what happens in a
     week that has one, so every week here is one; check-b327z15 and the
     notes cover the draw itself. */
  if(!window.__dueAll){ window.__dueAll = true; novaChallengeDue = function(){ return true; }; }
  const ticks = async n => { for(let i = 0; i < (n || 4); i++){ window.__realTick(); await wait(80); } };
  const home = async () => { showHome(); await wait(500); clearTop(); try{ clearTimeout(homeUnlockTimer); homeUnlockTimer = null; }catch(e){}
    store.pendingBadgeUnlocks = []; };
  /* an account friends with him for ten days, everything it has heard,
     his last message two days ago - and a new session */
  const settled = () => {
    localStorage.removeItem('class26e.nova'); novaAwayForce = false;
    store.novaHeard = {}; novaBefriend({ quiet: true });
    const s = novaState(); s.since = Date.now() - 10 * D; s.spontAt = Date.now() - 10 * D; novaSave(s);
    const h = novaHeardMap(); novaSeed(h, Date.now() - 10 * D); h['@last'] = Date.now() - 2 * D;
    h['wk:' + weekKeyNow()] = Date.now() - 2 * D;
    novaSessionAt = 0;
    store.studyLog = Object.assign({}, store.studyLog);
    persistLocally();
  };
  /* a rank-up whose journey has played: shown up to the rank held, the
     reaction not yet said */
  const rankDone = () => { const held = rankUpHeldIdxReal(); store.rankUpShown = held + 1; novaHeardMap()['@rank'] = held; return held; };
  /* a badge found: a unit's hundos to its threshold, then the rank kept
     in step (more badges can mean a rank) */
  const findBadge = () => { const U = topicsIn(QUESTIONS).filter(u => !unitBadgeEarned(u)); const u = U[0];
    store.unitPerfects[u] = badgeThresholdFor(u); return u; };
  /* one of his crew found, its Home unlock card already shown (the card
     goes before him - that is checked in check_day) */
  const findCrew = (id, card) => { store.legacyChars = (store.legacyChars || []).filter(x => x !== id).concat([id]); delete novaHeardMap()['char:' + id];
    if(!card){ store.unlocksShown = store.unlocksShown || { chars: [], banners: [] }; if(store.unlocksShown.chars.indexOf(id) < 0) store.unlocksShown.chars.push(id); } };
  /* tap away whatever Home's unlock cards put up */
  const cardsAway = async () => { for(let i = 0; i < 40; i++){ const c = document.querySelector('.rs-spot'); let busy = false; try{ busy = homeUnlockPlaying; }catch(e){}
    if(!c && !busy) return i; if(c) c.click(); await wait(250); } return -1; };
"""


def check_story(br):
    print("\ne1. the story: why your planet cracks, what you get, and no end - in every place he tells it")
    ctx, pg = booted(br, 440, 956, seed=SEED)
    r = pg.evaluate("""() => {
      const out = {};
      const txt = ls => ls.map(l => l.text);
      out.fresh = txt(novaIntroLines({}));
      try{ out.existing = txt(novaIntroLines({ existing: true })); }catch(e){ out.existing = []; out.err = String(e); }
      out.keys = novaIntroLines({}).map(l => Object.keys(l).filter(k => k !== 'text' && k !== 'gesture').sort().join('+'));
      out.ranks = TIER_ORDER_FULL.map((k, i) => { try{ return novaRankLine(i); }catch(e){ return ''; } });
      /* MOVED IN 327z15: Version 9.2 is RELEASE_NOTES[0] now; the note is Version 9's */
      out.note = (((RELEASE_NOTES.find(v => v.version === '9') || {}).groups || []).flatMap(g => g.items || []).find(i => /Your Instructor/.test(i.title)) || {}).body || '';
      out.chats = ['why is my planet cracking', 'what do i get for helping you', 'where are my crew', 'where are you'].map(q => novaReplyFor(q));
      out.tip = NOVA_NEW_TIPS_321.map(t => t.text).join(' | ');
      out.lore = RANK_LORE.titan + ' | ' + RANK_LORE.veteran;
      try{ out.planet = homeTapCopyPlanet(0).parts.join(' '); }catch(e){ out.planet = ''; }
      try{ out.cells = novaCardCells().map(c => c.join(': ')); }catch(e){ out.cells = []; }
      /* MOVED IN 327 (b327m): What's New is a card on Home, not narrated -
         the story is told in his introduction alone */
      out.news = typeof whatsNewLines === 'function' ? whatsNewLines(whatsNewState(), false).map(l => l.text).join(' | ') : '';
      return out; }""")
    src = cb.BODY
    fresh, existing = r.get("fresh") or [], r.get("existing") or []
    allt = " | ".join(fresh + existing)
    # MOVED IN 327z15: "We aren't gonna do the whole 'my planet blew up'
    # path" - the introduction is now the voyage: he sails the stars, a
    # storm scatters his badges, flares and crew into the class material,
    # each one you find joins you, and it ends on the start of your
    # adventure (new) / What's New on Home (existing). The planet and its
    # crack stay in the rank-up lines and his chat (checked below);
    # check-b327-c carries the voyage itself (order, no explosion, short boxes).
    storm = [i for i, t in enumerate(fresh) if re.search(r"storm", t, re.I)]
    scat = [i for i, t in enumerate(fresh) if re.search(r"scattered", t) and re.search(r"badges", t) and re.search(r"flares", t) and re.search(r"crew", t)]
    check("why things are lost: a storm hit his ship, then his badges, flares and crew were scattered (in that order)",
          storm and scat and storm[0] < scat[0], fresh[:6])
    land = [i for i, t in enumerate(fresh) if re.search(r"your studies", t)]
    check("...and they landed in your studies, after the storm", land and scat and land[0] > scat[0], fresh[:7])
    check("what you get: every one you find joins your team, and no 'teach you' / log",
          re.search(r"joins your team|join you", allt) and not re.search(r"instructor.s log|teach you", allt),
          [t for t in fresh if re.search(r"join", t)])
    check("an open end: a new account's last line starts the adventure; an existing one is pointed to What's New on Home",
          re.search(r"adventure", fresh[-1] if fresh else "") and re.search(r"Home", existing[-1] if existing else ""), [fresh[-1:], existing[-1:]])
    bad = [t for t in fresh + existing if re.search(r"\b(all seven|seven|sixteen|16|only three|three secret|a few secret flares)\b", t, re.I)]
    check("no fixed totals in his introduction (no 'seven', '16', 'a few secret flares')", not bad, bad[:3])
    # MOVED IN 327z15: a new account's introduction now asks his name and
    # his first character inside it (2 asks + the pick's answer), so 16 -> 20
    # MOVED IN 329: Madison asked for a longer storm, a sync-code line and two boxes on the modes, so 20 -> 26
    check("short: a new account hears at most 26 lines (two of them asks), an existing one at most 21, and every slide trigger is kept",
          0 < len(fresh) <= 26 and 0 < len(existing) <= 21
          and any("friend" in k for k in r.get("keys") or []) and any("final" in k for k in r.get("keys") or []) and sum(1 for k in r.get("keys") or [] if "enter" in k) >= 9,
          {"new": len(fresh), "existing": len(existing), "keys": r.get("keys")})
    ranks = r.get("ranks") or []
    rbad = [x for x in ranks if re.search(r"(four more|one rank left|all seven|to go\b)", x, re.I)]
    check("rank-up lines: each is his flare's light returned, with his thanks, no countdown of ranks left",
          len(ranks) == 7 and all(re.search(r"flare|star", x) for x in ranks) and all(re.search(r"thanks|Thank", x) for x in ranks) and not rbad,
          rbad[:2] or [x[:70] for x in ranks])
    check("...Gold's says the planet starts to crack and why; Supernova's says it is a star, he has a home, and there is more out there",
          len(ranks) == 7 and re.search(r"crack", ranks[2]) and re.search(r"light", ranks[2]) and re.search(r"star", ranks[6])
          and re.search(r"home", ranks[6]) and re.search(r"scanners", ranks[6]), [ranks[2:3], ranks[6:7]])
    ch = r.get("chats") or []
    # MOVED IN 327 (b327c): the same story everywhere - badges hold the
    # planet together, the crack is the strain, Supernova a star that held
    check("his chat replies tell the same story: the planet held by badges (a star at Supernova), what you get, the crew joining you, where he is",
          len(ch) == 4 and re.search(r"star", ch[0]) and re.search(r"[Bb]adges are what hold", ch[0]) and re.search(r"rewards", ch[1])
          and re.search(r"joins you", ch[2]) and re.search(r"scanning|storm", ch[3]),  # MOVED IN 327z15: no debris field - the storm story
          [c[:60] for c in ch])
    # MOVED IN 327z15: the note tells the voyage - a storm scattered them
    check("the Version 9 'Nova, Your Instructor' note gives the cause (a storm), what a badge is (a unit mastered), and the crew coming back",
          re.search(r"storm", r.get("note", "")) and re.search(r"scattered", r.get("note", ""))
          and re.search(r"master", r.get("note", "")) and re.search(r"crew", r.get("note", "")) and not re.search(r"explod|blew up|debris", r.get("note", "")),  # "explorer" is fine
          r.get("note", "")[:160])
    # MOVED IN 327 (b327m): "So the nova instructor won't go through what's
    # new one by one" - nothing of his is said on What's New any more
    check("What's New (on its own) is not narrated - he does not tell the story there", r.get("news", "") == "", r.get("news", "")[:300])
    # MOVED IN 327z15: the returning tips no longer retell the crack (the
    # planet tip is about tapping it); the Rank tab's lore still carries it
    check("the Rank tab's lore says the crack comes from his light, and Supernova makes it a star; no returning tip has the planet blowing up",
          not re.search(r"explo|blew up", r.get("tip", "")) and re.search(r"becomes a star", r.get("lore", "")) and re.search(r"Nova's light", r.get("lore", "")),
          [r.get("tip", "")[:200], r.get("lore", "")[:200]])
    check("no totals the story cannot keep: Home's planet says how many secret flares you found (not 'of 3'), his card counts without '/'",
          not re.search(r"of \d+ secret", r.get("planet", "")) and r.get("cells") and not any("/" in c for c in r.get("cells") or []),
          {"planet": r.get("planet"), "cells": r.get("cells")})
    check("the secret flare scenes no longer say every flare is lit, or that the sixth is the last",
          "Every flare in the sky is lit" not in src and "sixth and last" not in src and "ALL THREE FOUND" not in src
          and "ALL THREE SECRET" not in src and "last of the three in the sky" not in src, "")
    ctx.close()


def check_day(br):
    print("\ne2. one message a day, on Home only: a rank-up, a badge, one of his crew and the week's challenge all waiting")
    for (w, h, dev) in DEVS:
        ctx, pg = booted(br, w, h, seed=SEED)
        at(pg, WED)
        r = pg.evaluate("async () => {" + PRE + """
          if(typeof novaSchedule !== 'function') return { err: 'no scheduler' };
          settled();
          const u = findBadge(); const held = rankDone();
          delete novaHeardMap()['wk:' + weekKeyNow()];
          const out = { u, held, owed: !!rankUpOwed() };
          /* on Profile, where the rank-up journey ends: nothing */
          showProfile('profile'); await wait(500); clearTop(); await ticks();
          out.profile = own().length;
          /* a rank-up scene still on, even on Home: nothing */
          await home(); rankUpScene = { toIdx: held }; await ticks(); rankUpScene = null;
          out.scene = own().length;
          /* a cutscene's focus: nothing */
          let foc = false; try{ setCutsceneFocus(true); foc = true; }catch(e){}
          await ticks(); if(foc) setCutsceneFocus(false);
          out.focus = own().length;
          /* a test: nothing */
          testInProgress = true; await ticks(); testInProgress = false;
          out.test = own().length;
          /* Home: a reward card up (the character's unlock, a rank's
             rewards) goes first, and he waits for it */
          findCrew('detective');
          await home();
          const card = document.createElement('div'); card.className = 'rs-spot'; document.body.appendChild(card);
          await ticks(4);
          out.underCard = own().length; out.card = true; card.remove();
          out.cardsTapped = await cardsAway(); clearTop();
          /* then, calm: exactly one, the rank-up, saying the badge or the crew too */
          for(let i = 0; i < 12 && !own().length; i++){ window.__realTick(); await wait(80); }
          out.banner = !!document.querySelector('.vroom-chat-alert.is-ping');
          await ticks(4);
          const m = own();
          out.home = m.map(x => x.kind); out.text = (m[0] || {}).text || '';
          /* and nothing more today, however often it is asked */
          clearTop(); novaSessionAt = 0; await ticks(6);
          out.again = own().length;
          /* the same session goes on until the next scenario says otherwise */
          novaSessionAt = Date.now();
          out.unitName = u; out.crewName = AVATAR_DISPLAY_NAME.detective;
          return out; }""")
        if r.get("err"):
            check("%s: the scheduler exists" % dev, False, r)
            ctx.close()
            continue
        check("%s: nothing on Profile, in a rank-up scene, under a cutscene or in a test" % dev,
              r.get("profile") == 0 and r.get("scene") == 0 and r.get("focus") == 0 and r.get("test") == 0, {k: r.get(k) for k in ("profile", "scene", "focus", "test", "owed")})
        check("%s: on Home, a reward card goes first and he says nothing under it" % dev,
              r.get("card") and r.get("underCard") == 0 and r.get("cardsTapped", -1) >= 0, {k: r.get(k) for k in ("card", "underCard", "cardsTapped")})
        check("%s: back on Home, exactly ONE message - the rank-up's - and it says the badge or crew found with it" % dev,
              r.get("home") == ["rank"] and (r.get("unitName", "@") in r.get("text", "") or r.get("crewName", "@") in r.get("text", "")),
              {"home": r.get("home"), "text": r.get("text", "")[:200]})
        check("%s: ...announced with the chat's own banner, and nothing more that day (even in a new session)" % dev,
              r.get("banner") and r.get("again") == 1, {"banner": r.get("banner"), "again": r.get("again")})
        # the next day, the next one: the week's challenge
        # (327z15) his gap is 44h, not 20h (NOVA_QUIET_MS, two days between messages): 'the next' is two days on
        at(pg, WED + datetime.timedelta(days=2))
        r2 = pg.evaluate("async () => {" + PRE + """
          await home(); novaSessionAt = 0; await ticks(6);
          const m = own();
          const out = { kinds: m.map(x => x.kind), banner: !!document.getElementById('nova-challenge'),
            act: (document.querySelector('#nova-challenge .app-banner-act') || {}).textContent,
            face: !!document.querySelector('#nova-challenge .nova-friend-face .nova-svg') };
          const b = document.getElementById('nova-challenge');
          if(b){ const r = b.getBoundingClientRect(); out.rect = [r.left, r.top, r.right, r.bottom]; out.vw = innerWidth; }
          return out; }""")
        if SHOTS:
            pg.screenshot(path=os.path.join(SHOTS, "e-challenge-banner-%s.png" % w))
        check("%s: the next day, the next one - the week's challenge, with the Virtual Room banner, his face and Accept" % dev,
              r2.get("kinds") == ["rank", "challenge"] and r2.get("banner") and r2.get("act") == "Accept" and r2.get("face")
              and r2.get("rect") and r2["rect"][0] >= 0 and r2["rect"][2] <= r2.get("vw", 0) + 1, r2)
        # the badge and crew were said with the rank-up: they never come again
        at(pg, WED + datetime.timedelta(days=3))
        r3 = pg.evaluate("async () => {" + PRE + """
          novaSessionAt = 0; store.studyLog = {}; store.testHistory = []; await home(); await ticks(6);
          return { kinds: own().map(x => x.kind) }; }""")
        check("%s: the day after, nothing doubles up - what the rank-up said is not said again" % dev,
              r3.get("kinds") == ["rank", "challenge"], r3)
        ctx.close()


def check_devices(br):
    print("\ne3. two devices on one account: he speaks on one of them")
    ctx, pg = booted(br, 440, 956, seed=SEED)
    at(pg, WED)
    r = pg.evaluate("async () => {" + PRE + """
      if(typeof novaSchedule !== 'function') return { err: 'no scheduler' };
      settled(); findBadge(); rankDone(); delete novaHeardMap()['wk:' + weekKeyNow()];
      await home(); await ticks(6);
      const out = { a: own().map(x => x.kind) };
      const synced = JSON.parse(JSON.stringify(store));
      /* DEVICE B: the same account, its own class26e.nova, friends with him
         from long ago too - and the account's record synced */
      localStorage.removeItem('class26e.nova'); applyLoadedData(synced);
      novaBefriend({ quiet: true }); const s = novaState(); s.since = Date.now() - 10 * D; s.spontAt = Date.now() - 10 * D; novaSave(s);
      novaSessionAt = 0; await home(); await ticks(6);
      out.b = own().map(x => x.kind);
      /* the record merges by the higher copy */
      const d = { novaHeard: { '@last': 5, 'badge:x': 3 } }; mergeSameAccount(d, { novaHeard: { '@last': 9, 'wk:2026-10-19': 4 } });
      out.merged = d.novaHeard;
      out.syncedB = JSON.stringify(store.novaHeard || {});
      return out; }""")
    if r.get("err"):
        check("the scheduler exists", False, r)
        ctx.close()
        return
    check("device A says the rank-up; device B, synced, says nothing that day", r.get("a") == ["rank"] and r.get("b") == [], r)
    # (327z15) his gap is 44h, not 20h (NOVA_QUIET_MS, two days between messages): 'the next' is two days on
    at(pg, WED + datetime.timedelta(days=2))
    r2 = pg.evaluate("async () => {" + PRE + """
      novaSessionAt = 0; await home(); await ticks(6);
      const b = own().map(x => x.kind);
      const synced = JSON.parse(JSON.stringify(store));
      /* back to a device A that has B's record: nothing new */
      localStorage.removeItem('class26e.nova'); applyLoadedData(synced);
      novaBefriend({ quiet: true }); const s = novaState(); s.since = Date.now() - 10 * D; novaSave(s);
      novaSessionAt = 0; await home(); await ticks(6);
      return { b, a: own().map(x => x.kind) }; }""")
    check("the next day the week's challenge comes on B, and a device holding B's record does not send it again",
          r2.get("b") == ["challenge"] and r2.get("a") == [], r2)
    check("the account's record merges by the higher copy", (r.get("merged") or {}).get("@last") == 9 and (r.get("merged") or {}).get("wk:2026-10-19") == 4, r.get("merged"))
    ctx.close()


def check_quiet(br):
    print("\ne4. no burst: an existing account's first launch of this build, and a new account's first day")
    ctx, pg = booted(br, 440, 956, seed=SEED)
    at(pg, WED)
    r = pg.evaluate("async () => {" + PRE + """
      if(typeof novaSchedule !== 'function') return { err: 'no scheduler' };
      /* friends since build 324, with a lot already found and nothing
         recorded on the account by this build */
      localStorage.removeItem('class26e.nova'); store.novaHeard = {}; novaBefriend({ quiet: true });
      const s = novaState(); s.since = Date.now() - 30 * D; s.spontAt = Date.now() - 30 * D; novaSave(s);
      findBadge(); findCrew('detective'); findCrew('masked');
      const held = rankUpHeldIdxReal(); store.rankUpShown = held + 1;
      novaSessionAt = 0; await home(); await ticks(6);
      const out = { first: own().map(x => x.kind), base: !!novaHeardMap()['@base'] };
      return out; }""")
    if r.get("err"):
        check("the scheduler exists", False, r)
        ctx.close()
        return
    check("an existing account's first launch: nothing at all, and what it already has is recorded as heard", r.get("first") == [] and r.get("base"), r)
    at(pg, WED + datetime.timedelta(days=1))
    r2 = pg.evaluate("async () => {" + PRE + """
      novaSessionAt = 0; await home(); await ticks(6);
      return { kinds: own().map(x => x.kind), text: (own()[0] || {}).text || '' }; }""")
    check("...the next day, at most one message, and never old news (no rank-up or progress it already had)",
          len(r2.get("kinds") or []) <= 1 and not any(k in ("rank", "progress") for k in r2.get("kinds") or []), r2)
    # a brand-new account
    at(pg, WED + datetime.timedelta(days=3))
    r3 = pg.evaluate("async () => {" + PRE + """
      localStorage.removeItem('class26e.nova'); store.novaHeard = {}; novaSessionAt = 0;
      novaBefriend({ intro: true, quiet: true });
      await home(); await ticks(4);
      /* found on day one, after his introduction */
      const u = findBadge(); findCrew('marksman');
      store.rankUpShown = rankUpHeldIdxReal() + 1;
      await wait(100); novaSessionAt = 0; await ticks(6);
      const s = novaState(); s.since = Date.now() - 3 * 3600e3; novaSave(s);
      novaSessionAt = 0; await ticks(6);
      return { day1: own().map(x => x.kind), u }; }""")
    check("a new account's first day stays quiet beyond his introduction, with a badge and a character found", r3.get("day1") == [], r3)
    # (327z15) his gap is 44h, not 20h (NOVA_QUIET_MS, two days between messages): 'the next' is two days on
    at(pg, WED + datetime.timedelta(days=5, hours=2))
    r4 = pg.evaluate("async () => {" + PRE + """
      novaSessionAt = 0; await home(); await ticks(6);
      return { kinds: own().map(x => x.kind) }; }""")
    check("...and the next day exactly one", len(r4.get("kinds") or []) == 1, r4)
    ctx.close()


def check_week(br):
    print("\ne5. the week's challenge: once a week, Accept opens a room with him in it, over at the week's end")
    for (w, h, dev) in DEVS:
        # the room fake from check-behaviour: a write comes back as a snapshot,
        # so the lobby draws who is in it
        ctx, pg = booted(br, w, h, seed=SEED, init=cb._ROOM_FAKE)
        at(pg, WED)
        r = pg.evaluate("async () => {" + PRE + """
          if(typeof novaSchedule !== 'function') return { err: 'no scheduler' };
          settled(); delete novaHeardMap()['wk:' + weekKeyNow()];
          await home(); await ticks(6);
          const out = { kinds: own().map(x => x.kind), wk: (own()[0] || {}).wk, text: (own()[0] || {}).text || '' };
          /* declined: the banner's x */
          const x = document.querySelector('#nova-challenge .app-banner-x'); out.hadX = !!x; if(x) x.click();
          return out; }""")
        if r.get("err"):
            check("%s: the scheduler exists" % dev, False, r)
            ctx.close()
            continue
        check("%s: the invitation, in his voice, says Accept and when it ends" % dev,
              r.get("kinds") == ["challenge"] and r.get("wk") and re.search(r"Accept", r.get("text", "")) and re.search(r"Sunday", r.get("text", "")) and r.get("hadX"), r)
        at(pg, WED + datetime.timedelta(days=2))
        r2 = pg.evaluate("async () => {" + PRE + """
          novaSessionAt = 0; store.studyLog = {}; store.testHistory = []; await home(); await ticks(6);
          return { kinds: own().map(x => x.kind) }; }""")
        check("%s: declined, it is not sent again that week" % dev, r2.get("kinds") == ["challenge"], r2)
        at(pg, WED + datetime.timedelta(days=7))
        r3 = pg.evaluate("async () => {" + PRE + """
          novaSessionAt = 0; store.studyLog = {}; store.testHistory = []; await home(); await ticks(6);
          const m = own().filter(x => x.kind === 'challenge');
          /* his chat: last week's Accept has ended, this week's is live */
          clearTop(); openNovaChat(); await wait(900);
          await wait(600);
          const acts = [...document.querySelectorAll('#chatdock .nova-msg-accept')].map(b => ({ t: b.textContent, d: b.disabled,
            r: (r => [r.left, r.right, b.offsetHeight])(b.getBoundingClientRect()) }));
          const out = { n: m.length, wks: m.map(x => x.wk), acts, vw: innerWidth };
          return out; }""")
        if SHOTS:
            pg.screenshot(path=os.path.join(SHOTS, "e-challenge-chat-%s.png" % w))
        acts = r3.get("acts") or []
        check("%s: the next week, a new one; in his chat last week's Accept has ended and this week's is live, 44px, on screen" % dev,
              r3.get("n") == 2 and len(set(r3.get("wks") or [])) == 2 and [a["t"] for a in acts] == ["Ended", "Accept"]
              and acts[0]["d"] and not acts[1]["d"] and acts[1]["r"][2] >= 44 and acts[1]["r"][0] >= 0 and acts[1]["r"][1] <= r3.get("vw", 0), r3)
        r4 = pg.evaluate("async () => {" + PRE + """
          const b = [...document.querySelectorAll('#chatdock .nova-msg-accept')].find(x => !x.disabled);
          if(!b) return { tapped: false };
          __useRooms();
          b.click();
          for(let i = 0; i < 40 && !(vroomCode && vroomIsHost); i++) await wait(100);
          await wait(2600);
          const p = Object.assign({}, (vroomLastDoc && vroomLastDoc.data && vroomLastDoc.data.participants) || {}, liveVroomParticipants || {});
          const rows = [...document.querySelectorAll('#stage .vroom-roster-list .vroom-row')].map(r => r.textContent);
          return { tapped: true, code: !!vroomCode, host: vroomIsHost, nova: !!p.nova, dock: chatDockOpen,
                   lobby: !!document.querySelector('#stage > .screen-vroom-lobby'), rows }; }""")
        if SHOTS:
            pg.screenshot(path=os.path.join(SHOTS, "e-challenge-lobby-%s.png" % w))
        check("%s: Accept opens a Virtual Room you host with Nova already in it" % dev,
              r4.get("tapped") and r4.get("code") and r4.get("host") and r4.get("nova") and not r4.get("dock") and r4.get("lobby")
              and any("Nova" in x for x in r4.get("rows") or []), r4)
        ctx.close()


def check_rules(br):
    print("\ne6. the rest of the rules: progress varies by find, a Tuesday is the recap's, muted banners, one per session")
    ctx, pg = booted(br, 440, 956, seed=SEED)
    at(pg, WED)
    r = pg.evaluate("async () => {" + PRE + """
      if(typeof novaProgressLine !== 'function') return { err: 'no progress lines' };
      const out = {};
      out.lines = [
        novaProgressLine({ badges: ['Ethics'] }), novaProgressLine({ badges: ['Ethics', 'Penal Code'] }),
        novaProgressLine({ crew: ['detective'] }), novaProgressLine({ crew: ['voidwalker'] }),
        novaProgressLine({ crew: [(AVATAR_CHARACTERS.find(c => c.ultimate) || { id: 'detective' }).id] }),
        novaProgressLine({ sflares: ['red'] }), novaProgressLine({ level: 30 })];
      /* a find on its own: its own message */
      settled(); const u = findBadge(); store.rankUpShown = rankUpHeldIdxReal() + 1; novaHeardMap()['@rank'] = rankUpHeldIdxReal() + 1;
      theme.muteBanners = true;
      await home(); await ticks(6);
      out.solo = own().map(x => x.kind); out.soloText = (own()[0] || {}).text || ''; out.u = u;
      out.mutedBanner = !!document.querySelector('.vroom-chat-alert.is-ping, #nova-challenge');
      theme.muteBanners = false;
      return out; }""")
    if r.get("err"):
        check("progress lines exist", False, r)
        ctx.close()
        return
    L = r.get("lines") or []
    # MOVED IN 327 (b327c): a badge is a unit mastered, not a page of his log
    check("progress messages differ by what was found: a badge is a unit mastered, crew come home, a secret flare, a level",
          len(L) == 7 and re.search(r"mastered", L[0]) and re.search(r"units mastered", L[1]) and re.search(r"home|with you", L[2])
          and re.search(r"secret flares", L[3]) and re.search(r"again", L[4]) and re.search(r"secret flares", L[5]) and re.search(r"scanners", L[6])
          and len(set(L)) == 7, [x[:60] for x in L])
    check("a badge on its own is its own message - delivered, with banners muted, and no banner",
          r.get("solo") == ["progress"] and r.get("u", "@") in r.get("soloText", "") and not r.get("mutedBanner"), r)
    # Tuesday: the recap's day - the challenge waits while it is owed; a rank-up does not
    at(pg, datetime.datetime(2026, 10, 27, 10, 0))
    r2 = pg.evaluate("async () => {" + PRE + """
      settled(); delete novaHeardMap()['wk:' + weekKeyNow()];
      localStorage.removeItem('class26e.weekrecap.v1');
      const owed = novaRecapOwedToday(Date.now());
      novaSessionAt = 0; await home(); try{ clearTimeout(weekRecapTimer); }catch(e){} document.querySelectorAll('.nova-talk').forEach(e => e.__nova && e.__nova.close());
      await wait(300); clearTop(); await ticks(6);
      const a = own().map(x => x.kind);
      rankDone(); novaSessionAt = 0; await ticks(6);
      const b = own().map(x => x.kind);
      /* and the recap does not play on a day he has already messaged you */
      store.leaderboardOptIn = false; localStorage.removeItem('class26e.weekrecap.v1');
      maybeShowWeekRecap(0); await wait(400);
      const recap = !!document.querySelector('.nova-talk.is-weekrecap');
      return { owed, a, b, recap }; }""")
    check("on a Tuesday with the recap owed, the challenge waits; a rank-up still comes; and the recap does not play on top of it",
          r2.get("owed") and r2.get("a") == [] and r2.get("b") == ["rank"] and not r2.get("recap"), r2)
    at(pg, datetime.datetime(2026, 10, 28, 10, 0))
    r3 = pg.evaluate("async () => {" + PRE + """
      settled(); store.leaderboardOptIn = false; localStorage.removeItem('class26e.weekrecap.v1');
      /* (327z15) since 327z the recap waits for this launch's server copy (cloudConfirmedFor);
         this account has a code and no cloud here, so it is marked read */
      if(syncCode) cloudConfirmedFor = syncCode;
      novaHeardMap()['@last'] = Date.now() - 2 * D; novaSessionAt = 0;
      await home(); try{ clearTimeout(weekRecapTimer); }catch(e){}
      maybeShowWeekRecap(0); await wait(600);
      const recap = !!document.querySelector('.nova-talk.is-weekrecap');
      const el = document.querySelector('.nova-talk.is-weekrecap'); if(el && el.__nova) el.__nova.close(); await wait(500);
      delete novaHeardMap()['wk:' + weekKeyNow()]; clearTop(); novaSessionAt = 0; await ticks(6);
      return { recap, after: own().map(x => x.kind) }; }""")
    check("the weekly recap is the day's moment: after it plays, nothing else of his that day", r3.get("recap") and r3.get("after") == [], r3)
    ctx.close()


def check_away(br):
    print("\ne7. away: out of range, scanning the debris field - his header, the composer, his words, every friends list")
    for (w, h, dev) in DEVS:
        ctx, pg = booted(br, w, h, seed=SEED)
        at(pg, WED)
        r = pg.evaluate("async () => {" + PRE + """
          localStorage.removeItem('class26e.nova'); novaBefriend({ quiet: true });
          novaAwayForce = true; showHome(); await wait(300); clearTop();
          openNovaChat(); await wait(1600);
          const note = document.querySelector('#chatdock .vroom-chat-awaynote');
          const inp = document.querySelector('#chatdock .vroom-chat-input');
          const nr = note ? note.getBoundingClientRect() : null, ir = inp ? inp.getBoundingClientRect() : null;
          const out = { status: (document.querySelector('.nova-head-status') || {}).textContent || '',
            ph: inp ? inp.placeholder : '', disabled: inp && inp.disabled, note: note ? note.textContent : '',
            noteAbove: !!(nr && ir && nr.bottom <= ir.top + 1 && nr.height > 10), noteIn: !!(nr && nr.left >= 0 && nr.right <= innerWidth) };
          closeChatRoom(); closeChatDock(); await wait(200);
          out.cell = (novaCardCells().find(c => c[0] === 'Right now') || [])[1];
          out.manage = novaManageRow().textContent;
          novaAwayForce = false; openNovaChat(); await wait(1600);
          out.backNote = !!document.querySelector('#chatdock .vroom-chat-awaynote');
          out.backPh = (document.querySelector('#chatdock .vroom-chat-input') || {}).placeholder;
          novaAwayForce = true; await wait(1300);
          return out; }""")
        if SHOTS:
            pg.screenshot(path=os.path.join(SHOTS, "e-away-%s.png" % w))
        check("%s: his header says what he is doing and when he is back in range (no bare 'Away')" % dev,
              re.search(r"back in range", r.get("status", "")) and not re.search(r"\bAway\b", r.get("status", "")), r.get("status"))
        check("%s: the composer is off and says he is out of range" % dev, r.get("disabled") and re.search(r"out of range", r.get("ph", ""), re.I), r.get("ph"))
        check("%s: above it, his own words: out searching for more of his ship, back in range soon" % dev,
              re.search(r"ship|signal|debris|storm|scann|cargo", r.get("note", "")) and re.search(r"back in range", r.get("note", "")) and r.get("noteAbove") and r.get("noteIn"),
              {k: r.get(k) for k in ("note", "noteAbove", "noteIn")})
        check("%s: his card and Manage friends say 'Out of range' too" % dev,
              r.get("cell") == "Out of range" and "Out of range" in (r.get("manage") or ""), {k: r.get(k) for k in ("cell", "manage")})
        check("%s: back in range, his note goes and the composer is his again" % dev,
              r.get("note") and not r.get("backNote") and "Message" in (r.get("backPh") or ""), {k: r.get(k) for k in ("note", "backNote", "backPh")})
        ctx.close()


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cb.CHROME)
        try:
            fns = os.environ.get("ONLY_FN")
            for fn in (fns.split(",") if fns else ["check_story", "check_day", "check_devices", "check_quiet", "check_week", "check_rules", "check_away"]):
                globals()[fn](br)
        finally:
            br.close()
    cb.SERVER.shutdown()
    print("\n%s  (%d failure(s))" % ("ALL PASS" if not cb.FAILURES else "FAILED: " + ", ".join(cb.FAILURES), len(cb.FAILURES)))
    return 1 if cb.FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
