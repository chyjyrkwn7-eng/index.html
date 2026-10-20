#!/usr/bin/env python3
"""Build 327 (builder A): the sound, redone in the Home ambience's language.

Madison: "The idle screen is the only legit one. Fix this ... The main menu
music gives me dark Pokemon music vibes and I love it. More of that kinda
stuff app wide." / "The swooshing of the random stars on supernova is not
it." / "The xp box is still missing sounds, like when the numbers come in it
should be cool." / "Sound effect for your grade, shouldn't the sound effect
be synced with the percentage and not the amount of questions you got
right..?" / "Let's automatically put the sound on as default now."

  1. Sound is ON by default: a brand-new account; an account saved with the
     old default (off) is switched on ONCE (on the account and the device);
     turned off afterwards it stays off, across a reload, and on a device
     that never saw the switch-on; no AudioContext before the first gesture.
  2. The grade's sound follows the PERCENTAGE: two real results screens at
     the same percentage with different numbers of questions land on the
     same sound and tick on percentage steps (multiples of SND_GRADE_STEP),
     never one tick per right answer; a different band lands differently.
  3. The palette exists (the kit's lead, chime, chip, pulse), and no two
     catalogue ids render to the same samples.
  4. The Supernova ring's comet (the "swooshing of the random stars") plays
     no sound - on a tap, on its pulse and at random - and has no id.
  5. The XP box is heard: a note per line of how the XP was earned, the
     total ticking as its number counts (res.xp.count, climbing) and the
     coin when it arrives (res.xp.total), in that order.

  python3 tools/check-b327-a.py [--against old-index.html]
"""
import functools, http.server, os, re, socket, sys, threading
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGAINST = sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else None
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
_VR = open(os.path.join(ROOT, "tools", "check-vroom.py"), encoding="utf-8").read()
FAKE = re.search(r'FAKE_FIRESTORE = """(.*?)"""', _VR, re.S).group(1)

COUNT_CTX = r"""
(() => {
  window.__acMade = 0;
  const wrap = name => { const C = window[name]; if(!C) return;
    const W = function(...a){ window.__acMade++; return new C(...a); }; W.prototype = C.prototype;
    try{ Object.defineProperty(window, name, { value: W, configurable: true, writable: true }); }catch(e){ window[name] = W; } };
  wrap("AudioContext"); wrap("webkitAudioContext");
  try{ ['class26e.freshstart','1','class26e.frame.ok','go-live-1','class26e.intro.seen','9','class26e.unithold.tip','1',
        'class26e.penal55124.seen','1','class26e.penal124256.seen','1','class26e.penal256578.seen','1','class26e.weekrecap.v1','9999-12-31']
       .forEach((v, i, l) => { if(i % 2 === 0) localStorage.setItem(v, l[i + 1]); }); }catch(e){}
})();
"""
SEED = """()=>{ document.getElementById('splashscreen')?.remove(); try{ __useFake(); }catch(e){}
  store.onboardingComplete=true; store.firstName='Madison'; store.publicId='me01'; store.tourRev=99; store.rankMapFx244=true;
  store.retroBadgePending=[]; store.badgeBandsVersion=3;
  ['seenFirstResultsTour','seenModeSelectTour','seenProfileTour','seenRewardsTour','seenSettingsTour',
   'seenUnitOptionsTour','seenUnitSelectTour','seenMainMenuTour'].forEach(k=>store[k]=true);
  theme.muteBanners=false; theme.reduceMotion=false; theme.soundOn=true; saveTheme(); saveStore(); }"""
SPY = """()=>{ window.__played = []; const P = NovaSound.play;
  NovaSound.play = (id, o) => { window.__played.push({ id, o: o ? JSON.parse(JSON.stringify(o)) : null, t: performance.now() }); return P(id, o); }; return true; }"""
# a real results screen, fabricated the way check-results does it: `good`
# of the first `n` questions of `unit` right on the first try
RUN = """async ([unit, n, good]) => {
  const wait = ms => new Promise(z => setTimeout(z, ms));
  showHome(); await wait(600); window.__played.splice(0);
  cfg.mode = 'drill'; cfg.source = 'all'; cfg.units = [unit]; cfg.size = 0;
  order = QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === unit && (typeof inWholeUnit !== 'function' || inWholeUnit(i))).slice(0, n);
  runTrackable = true; timedOut = false; runMode = 'drill'; runLabel = null; isMissedRetake = false;
  practiceTestMinutes = null; inVirtualRoom = false; attempts = {}; picked = {}; timedOutSet = {};
  try{ firstPick = {}; }catch(e){}
  order.forEach((qi, k) => { const oo = optionOrder(qi), right = oo.indexOf(QUESTIONS[qi].answer);
    attempts[qi] = k < n - good ? 2 : 1; picked[qi] = right; try{ if(k < n - good) firstPick[qi] = (right + 1) % oo.length; }catch(e){} });
  runStartTime = Date.now() - 42000; testInProgress = true; pos = order.length - 1;
  summarize();
  const got = [];
  for(let i = 0; i < 200; i++){ await wait(60); got.push(...window.__played.splice(0));
    if(got.some(x => x.id.startsWith('res.grade.')) && got.some(x => x.id === 'res.xp.pop' || x.id === 'res.xp.knock')) break; }
  await wait(1500); window.__played.splice(0);
  const pct = (typeof lastRun === 'object' && lastRun && lastRun.pct) || null;
  return { got, pct, lines: document.querySelectorAll('.rs-xp .rs-xpline:not(.rs-xpkick):not(.rs-xpline-none)').length }; }"""

s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = "http://127.0.0.1:%d/index.html" % port
ok = True
def ck(n, c, d=""):
    global ok
    print(" ", "PASS" if c else "FAIL", n, ("-> " + str(d)[:300]) if d != "" else "")
    if not c: ok = False

def new_page(br):
    ctx = br.new_context(viewport={"width": 440, "height": 956})
    ctx.add_init_script(FAKE); ctx.add_init_script(COUNT_CTX)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    if AGAINST:
        html = open(AGAINST, encoding="utf-8").read()
        pg.route("**/index.html", lambda r: r.fulfill(status=200, content_type="text/html", body=html))
    pg.route("**/version.json*", lambda r: r.fulfill(status=200, content_type="application/json", body='{"build":"x","frameId":"","force":false}'))
    return ctx, pg, errs

def boot(pg):
    pg.goto(URL); pg.wait_for_timeout(2200); pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")

def ev(pg, js, a=None):
    try: return pg.evaluate(js, a) if a is not None else pg.evaluate(js)
    except Exception as e: return {"__err": str(e)[:200]}

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])

    print("\n  1. sound on by default, off when turned off")
    ctx, pg, errs = new_page(br); boot(pg)
    r = ev(pg, "()=>({ on: theme.soundOn, vib: theme.vibrate, fresh: !store.onboardingComplete, made: window.__acMade })")
    ck("a brand-new account: sound on, vibration off", r.get("fresh") is True and r.get("on") is True and r.get("vib") is False, r)
    ck("no AudioContext before the first gesture (iOS needs one)", r.get("made") == 0, r)
    ev(pg, SEED.rstrip("}") + "; store.theme = { mode:'dark', accent:'ink', layout:'modern', soundOn:false, soundVolume:.7, vibrate:false }; saveStore(); try{ localStorage.removeItem('class26e.soundon.327'); }catch(e){} }")
    pg.reload(); pg.wait_for_timeout(2200); ev(pg, "()=>document.getElementById('splashscreen')?.remove()")
    r = ev(pg, "()=>({ on: theme.soundOn, saved: store.theme.soundOn, flag: store.theme.soundOn327, dev: localStorage.getItem('class26e.soundon.327') })")
    ck("an account saved with the old default (off) is switched on once - the account and the device remember", r.get("on") is True and r.get("saved") is True and r.get("flag") is True and r.get("dev") == "1", r)
    ev(pg, "()=>{ theme.soundOn = false; saveTheme(); }")
    pg.reload(); pg.wait_for_timeout(2200); ev(pg, "()=>document.getElementById('splashscreen')?.remove()")
    r = ev(pg, "()=>({ on: theme.soundOn })")
    ck("turned off afterwards: still off after a reload", r.get("on") is False, r)
    ev(pg, "()=>{ try{ localStorage.removeItem('class26e.soundon.327'); }catch(e){} }")
    pg.reload(); pg.wait_for_timeout(2200); ev(pg, "()=>document.getElementById('splashscreen')?.remove()")
    r = ev(pg, "()=>({ on: theme.soundOn })")
    ck("...and on a device that never saw the switch-on (it is on the account)", r.get("on") is False, r)
    try: pg.mouse.click(436, 500); pg.wait_for_timeout(300)
    except Exception: pass
    r = ev(pg, "()=>window.__acMade")
    ck("off: a tap makes no AudioContext", r == 0, r)
    ctx.close()

    print("\n  2. the grade's sound follows the percentage")
    ctx, pg, errs = new_page(br); boot(pg)
    ev(pg, SEED); ev(pg, "()=>showHome()"); pg.wait_for_timeout(300)
    try: pg.mouse.click(436, 500)
    except Exception: pass
    pg.wait_for_timeout(300); ev(pg, SPY)
    units = ev(pg, """()=>{ const c = {}; QUESTIONS.forEach((q, i) => { const u = (q.topic||'').trim(); if(typeof inWholeUnit === 'function' && !inWholeUnit(i)) return; c[u] = (c[u]||0) + 1; });
      return Object.entries(c).sort((a, b) => a[1] - b[1]); }""")
    small = next((u for u in units if u[1] >= 12), None)
    big = next((u for u in units if u[1] >= 40), None)
    runs = {}
    for key, unit, n, good in [("a", small[0], 12, 9), ("b", big[0], 40, 30), ("c", small[0], 12, 6)]:
        runs[key] = ev(pg, RUN, [unit, n, good])
    def land(rr): return [x["id"] for x in (rr.get("got") or []) if x["id"].startswith("res.grade.")]
    def ticks(rr): return [round(x["o"]["frac"], 4) for x in (rr.get("got") or []) if x["id"] == "res.bar.tick" and x.get("o")]
    a, b, c = runs["a"], runs["b"], runs["c"]
    ck("9 of 12 and 30 of 40 (both 75%) land on the same grade sound", land(a) and land(a) == land(b), [land(a), land(b)])
    ck("6 of 12 (50%) lands on a different one", land(c) and land(c) != land(a), [land(c), land(a)])
    step = ev(pg, "()=>typeof SND_GRADE_STEP === 'number' ? SND_GRADE_STEP : null")
    ta, tb = ticks(a), ticks(b)
    on_steps = bool(step) and all(abs(f * 100 / step - round(f * 100 / step)) < 1e-6 for f in ta + tb)
    ck("the count ticks on percentage steps, never once per right answer (pitch = the percentage)", ta and tb and on_steps, [step, ta[:12], tb[:12]])
    ck("...and never past the percentage it lands on", ta and tb and max(ta) <= .75 + 1e-9 and max(tb) <= .75 + 1e-9, [max(ta or [0]), max(tb or [0])])
    # MOVED IN 327 (b327j): "The sound effects aren't perfectly lined up with
    # the percentage grade going up." A tick now plays on every change of the
    # shown number (rate-limited by SND_GRADE_GAP_MS), so how many there are
    # follows how long the count takes, not the answers. What still holds:
    # never more ticks than percentages passed (75), and 30 answers tick about
    # as often as 9 do - nowhere near three times as many. It was "within 3".
    ck("30 right answers do not tick more than 9 do (the count is the percentage's)",
       ta and tb and len(ta) <= 75 and len(tb) <= 75 and len(tb) <= len(ta) * 1.3 + 3, [len(ta), len(tb)])
    ck("no page errors", not errs, errs[:3])

    print("\n  5. the XP box is heard")
    got = [x["id"] for x in (a.get("got") or [])]
    lines = got.count("res.xp.line")
    ck("a note for every line of how the XP was earned", lines >= 1 and lines == a.get("lines"), [lines, a.get("lines")])
    i_line = max([i for i, x in enumerate(got) if x == "res.xp.line"] or [-1])
    counts = [i for i, x in enumerate(got) if x == "res.xp.count"]
    ck("the total ticks as its number counts up (res.xp.count, after the lines)", len(counts) >= 5 and min(counts) > i_line, [len(counts), i_line])
    ks = [x["o"]["k"] for x in (a.get("got") or []) if x["id"] == "res.xp.count" and x.get("o")]
    ck("...climbing as it counts", ks and all(y >= x for x, y in zip(ks, ks[1:])), ks[:8])
    ck("...and rings the coin as it arrives (res.xp.total, after the ticks)", "res.xp.total" in got and got.index("res.xp.total") > max(counts or [10 ** 6]), got[-8:])
    ctx.close()

    print("\n  3. the palette, and no two sounds the same")
    ctx, pg, errs = new_page(br); boot(pg)
    r = ev(pg, """()=>{ const OAC = window.OfflineAudioContext, oc = new OAC(1, 128, 44100);
      const K = sndKit(sndGraph(oc, { limiter: false }), oc.createGain(), 0, 1);
      return ['lead','chime','twinkle','chip','bass','pad','hush','dm'].filter(k => typeof K[k] !== 'function'); }""")
    ck("the kit carries the palette (lead, chime, twinkle, chip, bass, pad, hush, the D minor scale)", r == [], r)
    r = ev(pg, """async ()=>{ const seen = {}, dup = [];
      for(const id of Object.keys(SOUND_CATALOGUE)){
        const b = await NovaSound.render(id, { sr: 22050 }), d = b.getChannelData(0);
        let h = 2166136261 >>> 0; for(let i = 0; i < d.length; i += 3){ h = Math.imul(h ^ Math.round(d[i] * 1e5), 16777619) >>> 0; }
        const key = d.length + ':' + h; if(seen[key]) dup.push([seen[key], id]); else seen[key] = id; }
      return { n: Object.keys(SOUND_CATALOGUE).length, dup }; }""")
    ck("no two catalogue ids render to the same samples (%s ids)" % r.get("n"), isinstance(r, dict) and r.get("n") and r.get("dup") == [], r)

    print("\n  4. the Supernova ring's comet is silent")
    ev(pg, SEED)
    ev(pg, """()=>{ const k = 'titan', rule = TIER_UNLOCKS[k] || {};
      const topics = [...new Set(QUESTIONS.map(q => (q.topic||'').trim()))].filter(Boolean);
      store.unitPerfects = {}; topics.slice(0, rule.badges || 0).forEach(t => { store.unitPerfects[t] = badgeThresholdFor(t); });
      let pts = 1000; while(levelProgress(pts).level < (rule.level || 0)) pts += 500; store.lifetime.points = pts;
      store.seenUnlockedTiers = TIER_ORDER_FULL.slice(); store.supernovaAchieved = true; try{ markRingTierSeen('supernova'); }catch(e){} /* an up-to-date account: its Supernova reward cards were shown long ago (owed cards hold the streak back) */ try{ const u = pendingHomeUnlocks(); markUnlocksShown(u.chars, u.banners, u.fx); }catch(e){} homeUnlocksOwed = () => false; homeUnlockPlaying = false; saveStore(); showHome(); }""")
    pg.wait_for_timeout(600)
    try: pg.mouse.click(436, 500)
    except Exception: pass
    pg.wait_for_timeout(300); ev(pg, SPY)
    r = ev(pg, """async ()=>{ const hero = document.querySelector('.cosmic-hero-wrap'); const out = [];
      for(const why of ['tap', 'pulse', 'random']){ document.querySelectorAll('.sn-ringglint').forEach(g => g.remove());
        out.push(homeRingStreak(hero, why)); await new Promise(z => setTimeout(z, 300)); }
      return { streaks: out, played: window.__played.map(x => x.id), id: 'home.supernova.ring' in SOUND_CATALOGUE }; }""")
    ck("the comet streaks on Home (the picture is unchanged)", isinstance(r, dict) and any(r.get("streaks") or []), r)
    ck("...and makes no sound - not on a tap, its pulse or at random", isinstance(r, dict) and not [p for p in (r.get("played") or []) if "supernova" in p or "ring" in p], r)
    ck("...and the swoosh is out of the catalogue", isinstance(r, dict) and r.get("id") is False, r)
    ck("no page errors", not errs, errs[:3])
    ctx.close()
    br.close()
srv.shutdown()
print("\n" + ("ALL PASS" if ok else "FAILED"))
sys.exit(0 if ok else 1)
