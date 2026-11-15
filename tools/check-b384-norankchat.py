#!/usr/bin/env python3
"""Build 384.123: Nova no longer comes on screen to talk after a rank-up.

  python3 tools/check-b384-norankchat.py [--against FILE|REV] [--class academy|ifc] [--ranks rookie,ranger,...] [--full]

Madison (he/him): "Nova coming to talk to you after ranking up, remove that part." Since 327z15 a finished rank-up journey
(rankUpSceneEnd) had Nova come on over the relit flare - his dialog ("<name>! You found my <rank> flare!", the rank's beats, a
closing line) - and read it through before the player was back on the screen. It is gone: the journey ends and nothing talks.

For every rank of both classes (Bronze ... Supernova in the academy and in Fire Code) the gate owes that one rank on Home, taps the
Profile tab when Home calls, plays the journey as a person would (reward cards tapped once they have been up a while) and, once
it is over and nothing is owed, WAITS 7 seconds (the talk used to come up 0.3-0.9s after the end and its first line to type) -
and asserts, by SHAPE (nothing read from a label):
  1. no Nova talk ever mounted: from the first frame of the journey to the end of the wait, no element of the talk's shape was
     added to the document (the dialog `.nova-talk` - role=dialog, aria-modal - with its `.nt-bubble` / `.nt-stage` / `.nt-go`),
     and none was present on any 100ms poll (a talk that is built and closed in between is caught by the observer);
  2. the player is back on Home, nothing owed, none of the journey's classes or layers left (rankup-lock, ru-journey, ru-scene,
     veil, curtain, the supernova cutscene, a reward card), the tab bar and the chat button on top at their own centres;
  3. taps are live: a real touch tap on the Leaderboard tab leaves Home;
  4. his CHAT is as quiet about the rank as it was (the decision of 384.123): no message of kind "rank" was sent, and heard "@rank"
     is at or past the rank just reached (the journey's end still moves it, so the chat has nothing to add).
Every rank is played with Reduce motion on (the journey's short still form: the same funnel, rankUpSceneEnd, every ending goes
through) and, so the full-motion journey is covered, the first rank and Supernova of each class are played again with full motion
(`--full` plays every rank in full motion; that is about 80s a rank).

Fails on 384.98 (origin/claude/b384-rankup2): the talk mounts at the end of every journey.
"""
import functools, json, os, re, subprocess, sys, tempfile, time
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b384_rankjourney_lib import *  # noqa: E402,F401


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


AGAINST = arg("--against")
if AGAINST and not os.path.exists(AGAINST):
    tmp = os.path.join(tempfile.mkdtemp(), "index.html")
    open(tmp, "wb").write(subprocess.check_output(["git", "show", "%s:index.html" % AGAINST], cwd=ROOT))
    AGAINST = tmp
CLASSES = (arg("--class") or "academy,ifc").split(",")
RANKS = (arg("--ranks") or ",".join(KEYS)).split(",")
FULL_ALL = "--full" in sys.argv
SELF = Served(AGAINST)
FAILS = []


def ck(name, ok, info=None):
    print(("  PASS  " if ok else "  FAIL  ") + name + ("" if ok or info is None else "  -> " + str(info)[:700]), flush=True)
    if not ok:
        FAILS.append(name)


# the talk's shape: the dialog Nova's talks are mounted as, and its own parts
SHAPE = ".nova-talk, [role=dialog][aria-modal=true] .nt-bubble, .nt-bubble, .nt-stage, .nt-go, .nt-talk"

WATCH = r"""(shape) => {
  if(window.__nrc) return;
  const N = window.__nrc = { mounts: [], polls: 0, scenes: 0 };
  const note = (how, n) => N.mounts.push({ how, t: Math.round(performance.now()), cls: String(n.className || '').slice(0, 60), id: n.id || '', scene: !!rankUpScene });
  new MutationObserver(ms => ms.forEach(m => m.addedNodes.forEach(n => {
    if(n.nodeType !== 1) return;
    if(n.matches(shape)) note('added', n); else { const d = n.querySelector(shape); if(d) note('added-inside', d); }
  }))).observe(document.documentElement, { childList: true, subtree: true });
  setInterval(() => { N.polls++; const d = document.querySelector(shape); if(d) note('poll', d); if(rankUpScene) N.scenes++; }, 100);
}"""

DONE = r"""() => !rankUpScene && !rankUpOwed() && !document.body.classList.contains('rankup-lock') && !document.querySelector('.rs-spot, #supernova-cutscene, .ru-veil, .ru-curtain.is-on')"""

FRIEND = r"""() => { try{ if(!novaIsFriend()) novaBefriend({ quiet: true }); }catch(e){} return !!novaIsFriend(); }"""

END = r"""(a) => {
  const centre = el => { if(!el) return null; const b = el.getBoundingClientRect(); return { x: b.left + b.width / 2, y: b.top + b.height / 2, w: b.width, h: b.height }; };
  const onTop = el => { const c = centre(el); if(!c || c.w < 4 || c.h < 4) return false; const t = document.elementFromPoint(c.x, c.y); return !!t && (t === el || el.contains(t)); };
  const heard = novaHeardMap();
  return {
    home: !!document.querySelector('[data-screen=home]'), owed: !!rankUpOwed(), scene: !!rankUpScene,
    classes: ['rankup-lock', 'ru-journey'].filter(c => document.body.classList.contains(c)).concat(document.documentElement.classList.contains('ru-scene') ? ['ru-scene'] : []),
    left: [...document.querySelectorAll('.ru-veil, .ru-curtain.is-on, #supernova-cutscene, .rs-spot, .ru-ghost')].map(e => String(e.className || e.id).slice(0, 30)),
    tab: onTop(document.getElementById('bottomtab-rewards')), tabProfile: onTop(document.getElementById('bottomtab-profile')),
    chat: onTop(document.querySelector('.chatdock-btn')),
    rankMsgs: novaThread().filter(m => m.kind === 'rank').length, heard: Number(heard['@rank']) || 0, want: a.toIdx + 1,
    shown: store.rankUpShown, rank: rankOf(store), still: ruStill(), friend: novaIsFriend() };
}"""


def play(br, cls, rank, still):
    ctx, pg, errs = open_page(br, SELF, cls)
    try:
        pg.evaluate("(s)=>{ theme.reduceMotion = !!s; applyTheme(); }", still)
        info = pg.evaluate(SEED_A, {"topic": TOPIC[cls], "rank": rank, "mode": "owed", "owe": 1, "fresh": True})
        if rank == "titan":
            # Supernova asks for every badge of the class and the top level. The academy's rule is 25 badges over 24 units (out of reach
            # on purpose, "there will be eventually"), so there the rule is lowered to the 24 there are - in the page, for this case only
            info = pg.evaluate("""()=>{ const all = classTopics(); TIER_UNLOCKS.titan.badges = Math.min(TIER_UNLOCKS.titan.badges, all.length);
              all.forEach(t => { store.unitPerfects[t] = badgeThresholdFor(t); }); saveStore(); return { rank: rankOf(store), owed: !!rankUpOwed(), badges: badgeCountOf(store) }; }""")
        friend = pg.evaluate(FRIEND)
        pg.evaluate(WATCH, SHAPE)
        pg.evaluate("()=>{ showHome(); }")
        t0 = time.time(); tapped = False; over = None; ended = None
        while time.time() - t0 < 420:
            pg.wait_for_timeout(150)
            st = pg.evaluate(PROBE)
            if st["lock"] and not st["sc"] and not tapped:
                pg.wait_for_timeout(1000)
                pg.evaluate("()=>{ document.getElementById('bottomtab-profile').click(); }")
                tapped = True
            pg.evaluate(PERSON)   # reward cards tapped once up; (a talk, if one is up, is read through so the journey can finish)
            if tapped and pg.evaluate(DONE):
                over = over or time.time()
                if time.time() - over > 7:
                    ended = round(time.time() - t0, 1)
                    break
            else:
                over = None
        toIdx = KEYS.index(rank)
        end = pg.evaluate(END, {"toIdx": toIdx})
        watch = pg.evaluate("()=>window.__nrc")
        tap_ok = None
        if ended is not None:
            c = pg.evaluate("()=>{ const b = document.getElementById('bottomtab-rewards').getBoundingClientRect(); return [b.left + b.width / 2, b.top + b.height / 2]; }")
            pg.touchscreen.tap(c[0], c[1])
            pg.wait_for_timeout(1500)
            tap_ok = pg.evaluate("()=>!document.querySelector('[data-screen=home]') && !!stage.firstElementChild && document.getElementById('bottomtab-rewards').getAttribute('aria-current') === 'page'")
        return dict(info=info, friend=friend, ended=ended, end=end, watch=watch, tap=tap_ok, errs=errs)
    finally:
        ctx.close()


def check_case(br, cls, rank, still):
    tag = "%s %s %s" % (cls, rank, "still" if still else "full motion")
    r = None
    for attempt in range(3):
        try:
            r = play(br, cls, rank, still)
            break
        except Exception as e:
            print("  (case %s stopped: %s - again)" % (tag, str(e)[:160]), flush=True)
            if not re.search(r"crash|closed|Target|Timeout|timeout", str(e)):
                raise
    if r is None:
        ck("%s: the case ran" % tag, False, "no result after 3 tries")
        return
    e, w = r["end"], r["watch"]
    ck("%s: the journey ran to its end and the page was left alone for 7s (%ss; a scene was up on %d polls; the account's rank is %s, owed %s)" % (tag, r["ended"], w["scenes"], e["rank"], e["owed"]),
       r["ended"] is not None and w["scenes"] > 5 and e["rank"] == rank and r["friend"] and e["friend"], r)
    ck("%s: no Nova talk ever mounted (added to the page or found on a 100ms poll: %s)" % (tag, [(m["how"], m["cls"], m["id"]) for m in w["mounts"]][:3]),
       not w["mounts"], w["mounts"][:4])
    ck("%s: the player is back on Home, nothing owed, nothing of the journey left (%s %s), tab bar and chat button on top" % (tag, e["classes"], e["left"]),
       e["home"] and not e["owed"] and not e["scene"] and not e["classes"] and not e["left"] and e["tab"] and e["tabProfile"] and e["chat"], e)
    ck("%s: taps are live: a touch on the Leaderboard tab leaves Home" % tag, r["tap"] is True, r["tap"])
    ck("%s: his chat sent no rank message and heard '@rank' is at or past the rank reached (%s >= %s)" % (tag, e["heard"], e["want"]),
       e["rankMsgs"] == 0 and e["heard"] >= e["want"], e)
    ck("%s: no page errors" % tag, not r["errs"], r["errs"][:3])


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox", "--disable-dev-shm-usage"])
        try:
            for cls in CLASSES:
                for rank in RANKS:
                    print("-- %s / %s (reduced motion)" % (cls, rank), flush=True)
                    check_case(br, cls, rank, True)
            for cls in CLASSES:
                fulls = RANKS if FULL_ALL else [k for k in (RANKS[0], "titan") if k in RANKS]
                for rank in dict.fromkeys(fulls):
                    print("-- %s / %s (full motion)" % (cls, rank), flush=True)
                    check_case(br, cls, rank, False)
        finally:
            br.close()
    print("ALL PASS" if not FAILS else "FAILURES (%d): %s" % (len(FAILS), FAILS[:6]))
    sys.exit(0 if not FAILS else 1)


main()
