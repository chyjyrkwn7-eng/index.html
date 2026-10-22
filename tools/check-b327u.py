"""Build 327 round 7, package U - the status line on the choice's clock, the
rank-up climb with no "extra XP", the challenge card faded not flipped.

Madison's words, each held by checks that FAIL on 61d9620 and pass here:

  python3 tools/check-b327u.py
  python3 tools/check-b327u.py --against /path/to/61d9620/index.html
  B327U_ONLY=A,B,C python3 tools/check-b327u.py

  A. "When taking a test, the words above the first answer choice, when you
     get it right or wrong it changes crazy fast. Could it match the speed of
     the button lighting up to green?"
     Drill (a wrong pick, then the right one) and Mock Test (a pick), phone and
     iPad: the status line's new words arrive by an opacity animation whose
     delay, duration and curve are the picked choice's colour transition
     (read off getAnimations and getComputedStyle); the line's box does not
     change height during it; a render that does not change the words plays
     nothing.
  B. "WHEN YOU HAVE EXTRA XP going into ranking up, the number on the left
     will obviously be higher, but at the cutscene it would do the level up
     effect/sound then go to the next level, THE NUMBER on the left would go
     into the level?"
     The Profile climb (rankUpStandingClimb, the journey's own function) on
     a Silver-to-Gold-sized wall, phone and iPad: no text matching /extra XP/
     anywhere in any frame; the left number starts larger than the span; at
     each level the bar's level-up class and res.levelup fire, and the left
     number then reads the previous less that level's cost; at every step
     xpForLevel(level) + x is the total; it ends on the right level.
  C. "In the rank road map cutscene when the challenges change, don't flip
     the sheet, just do a nice fade like the other one.."
     rankUpProfileReturn's hand-over: no rotate/3D transform and no
     ru-flip-out on any challenge card in any frame; both cards fade by
     opacity.

Exits non-zero on any failure.
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py"))
cb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cb)   # reads --against from sys.argv itself
from playwright.sync_api import sync_playwright

PHONE = ("iPhone 17 Pro Max", 440, 956)
TABLET = ("iPad Pro 11\"", 834, 1194)
FAILURES = []
ONLY = set(x.strip().upper() for x in os.environ.get("B327U_ONLY", "").split(",") if x.strip())
if "--against" in sys.argv:
    print("against: %s" % cb.SRC)


def check(name, ok, detail=""):
    print("  %-4s %s%s" % ("PASS" if ok else "FAIL", name, ("  -> " + str(detail)[:600]) if detail else ""))
    if not ok:
        FAILURES.append(name)


def boot(br, w, h):
    return cb.booted(br, w, h, seed=cb.USED_ACCOUNT, touch=True)


# --------------------------------------------------------------------------
STATUS = """async (a) => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const out = { errs: [], events: [] };
  try{
  document.querySelectorAll('#pushing-update,#intro-pop').forEach(n => n.remove());
  theme.autoAdvance = false;
  /* every status line added to the question, with its animations as it lands */
  const seen = new WeakSet();
  const grab = () => {
    const st = document.querySelector('.qpanel > .status');
    if(!st || seen.has(st)) return;
    seen.add(st);
    const w = st.querySelector('.status-words') || st;
    const anims = (w.getAnimations ? w.getAnimations() : []).map(x => {
      const t = x.effect.getTiming(); const kf = x.effect.getKeyframes();
      return { delay: t.delay, dur: t.duration, ease: t.easing, op0: kf.length ? String(kf[0].opacity) : null, op1: kf.length ? String(kf[kf.length - 1].opacity) : null };
    });
    let pick = document.querySelector('.qpanel .choice.is-right-pop, .qpanel .choice.is-wrong-flash');
    let probe = null;
    /* a Mock Test pick has no right/wrong colour of its own (a fresh dot, no
       ease): the choice colour's timing is the result colour's, read off a
       probe choice carrying it */
    if(!pick && document.querySelector('.qpanel .choice.is-pick-pop')){
      probe = document.createElement('button'); probe.className = 'choice is-right-pop';
      const mk = document.createElement('span'); mk.className = 'mark'; probe.appendChild(mk);
      document.querySelector('.qpanel').appendChild(probe); pick = probe;
    }
    let ch = null;
    if(pick){
      const cs = getComputedStyle(pick.querySelector('.mark') || pick);
      const props = cs.transitionProperty.split(','), durs = cs.transitionDuration.split(','), eases = cs.transitionTimingFunction.split(/,(?![^(]*\\))/), dels = cs.transitionDelay.split(',');
      const i = Math.max(0, props.findIndex(p => /color/.test(p)));
      ch = { dur: parseFloat(durs[i % durs.length]) * 1000, ease: (eases[i % eases.length] || '').trim(), delay: parseFloat(dels[i % dels.length]) * 1000 };
      if(probe) probe.remove();
    }
    out.events.push({ text: st.textContent, anims, choice: ch, h: st.offsetHeight, el: st });
  };
  const mo = new MutationObserver(grab);
  mo.observe(document.getElementById('stage'), { childList: true, subtree: true });
  cfg.mode = a.mode; cfg.units = ['Identity Crimes']; cfg.versions = {}; cfg.source = 'all'; cfg.size = 0; cfg.timer = 'off'; cfg.flashcards = false; cfg.recall = false;
  beginRun(freshOrder(QUESTIONS.map((q, i) => i).filter(i => QUESTIONS[i].topic === 'Identity Crimes')), null);
  for(let t = 0; t < 120 && !document.querySelector('.qpanel .choice'); t++) await wait(100);
  await wait(500);
  out.events.length = 0;
  const right = correctSlot(order[pos]);
  if(a.mode === 'drill'){
    document.querySelector('.qpanel .choice[data-index="' + ((right + 1) % 4) + '"]').click();
    await wait(120);
    const e1 = out.events[out.events.length - 1];
    if(e1){ await wait(120); e1.hMid = e1.el.offsetHeight; }
    await wait(500);
    document.querySelector('.qpanel .choice[data-index="' + right + '"]').click();
    await wait(600);
  } else {
    document.querySelector('.qpanel .choice[data-index="' + right + '"]').click();
    await wait(120);
    const e1 = out.events[out.events.length - 1];
    if(e1){ await wait(120); e1.hMid = e1.el.offsetHeight; }
    await wait(500);
  }
  /* a render that changes nothing */
  const n0 = out.events.length;
  render(); await wait(60);
  const re = out.events.slice(n0);
  out.rerender = re.map(e => ({ text: e.text, anims: e.anims.length, swapping: e.el.classList.contains('is-swapping') }));
  out.events = out.events.slice(0, n0).map(e => ({ text: e.text, anims: e.anims, choice: e.choice, h: e.h, hMid: e.hMid }));
  testInProgress = false;
  mo.disconnect();
  }catch(e){ out.errs.push(String(e && e.stack || e)); }
  return out;
}"""


def section_status(br):
    print("\nA. the status line's words change on the choice's clock")
    for label, w, h in (PHONE, TABLET):
        for mode in ("drill", "exam"):
            ctx, pg = boot(br, w, h)
            r = pg.evaluate(STATUS, {"mode": mode})
            ctx.close()
            tag = "%s %s" % (label, "Drill" if mode == "drill" else "Mock Test")
            if r.get("errs"):
                check(tag + ": ran", False, r["errs"])
                continue
            ev = [e for e in r["events"] if e.get("choice")]
            want = 2 if mode == "drill" else 1
            check("%s: %d result render(s) with a picked choice" % (tag, want), len(ev) >= want, [e["text"] for e in r["events"]])
            for i, e in enumerate(ev[:want]):
                ch, an = e["choice"], [x for x in e["anims"] if x["op0"] == "0" and x["op1"] == "1"]
                ok = bool(an) and ch and abs(an[0]["dur"] - ch["dur"]) < 1 and abs(an[0]["delay"] - ch["delay"]) < 1 \
                    and an[0]["ease"].replace(" ", "") == ch["ease"].replace(" ", "")
                check("%s: words #%d (%r) fade in on the choice's colour timing" % (tag, i + 1, e["text"][:40]), ok, [e["anims"], ch])
                check("%s: words #%d - the line's box holds its height during the fade" % (tag, i + 1),
                      e.get("hMid") is None or e["hMid"] == e["h"], [e["h"], e.get("hMid")])
            check("%s: a render that does not change the words plays nothing" % tag,
                  r["rerender"] and all(x["anims"] == 0 and not x["swapping"] for x in r["rerender"]), r["rerender"])


# --------------------------------------------------------------------------
CLIMB = """async (a) => {
  const out = { errs: [] };
  try{
  const U = topicsIn(QUESTIONS);
  store.unitPerfects = {}; U.slice(0, a.badges).forEach(u => store.unitPerfects[u] = badgeThresholdFor(u) + 1);
  store.rankFloor = 0; store.levelFloor = 0; store.levelWallRule = 325; store.lifetime.points = a.points; store.rankUpShown = 9;
  try{ localStorage.setItem(PF_XP_SEEN_KEY, String(Math.round(levelStateFor(store).total))); }catch(e){}
  saveStore(); showProfile(); await new Promise(r => setTimeout(r, 900));
  const st = document.querySelector('.pf-standing');
  const from = levelStateOf(store.lifetime.points, a.badges - 1, 0, 0), to = levelStateFor(store);
  out.from = { level: from.level, into: Math.round(from.into), span: Math.round(from.span) };
  out.to = { level: to.level, into: Math.round(to.into), span: Math.round(to.span), stopped: to.stopped, total: to.total };
  rankUpStandingAt(st, from);
  const num = s => Number(String(s || '').replace(/[^0-9]/g, ''));
  /* the sound and the level-up class, as they happen */
  const sounds = []; const realPlay = window.playSound;
  window.playSound = (id, o) => { sounds.push({ id, t: performance.now() }); return realPlay(id, o); };
  const ups = [];
  const wrapEl = st.querySelector('.pf-xpbarwrap');
  const mo = new MutationObserver(() => { if(wrapEl && wrapEl.classList.contains('ru-levelup')) ups.push(performance.now()); });
  if(wrapEl) mo.observe(wrapEl, { attributes: true, attributeFilter: ['class'] });
  const sc = {}, samples = [];
  let done = false;
  rankUpStandingClimb(st, from, to, null, sc).then(() => { done = true; });
  const T0 = performance.now();
  out.extraText = null;
  await new Promise(res => { const tick = () => {
    const s = document.querySelector('.pf-standing');
    if(/extra\\s*XP/i.test(s.textContent) && !out.extraText) out.extraText = s.textContent.replace(/\\s+/g, ' ').slice(0, 160);
    samples.push({ t: Math.round(performance.now() - T0), lv: num((s.querySelector('.pf-level') || {}).textContent),
      have: num((s.querySelector('.xpnums-have') || {}).textContent), need: num((s.querySelector('.xpnums-need') || {}).textContent) });
    if(!done && performance.now() - T0 < 40000) requestAnimationFrame(tick); else res(); };
    requestAnimationFrame(tick); });
  window.playSound = realPlay; mo.disconnect();
  out.samples = samples;
  out.rec = sc.climb || null;
  out.levelups = sounds.filter(x => x.id === 'res.levelup').length;
  out.ups = ups.length;
  out.spans = []; for(let L = from.level; L < to.level; L++) out.spans.push(xpForLevel(L + 1) - xpForLevel(L));
  out.xpFor = {}; for(let L = from.level; L <= to.level + 1; L++) out.xpFor[L] = xpForLevel(L);
  out.after = { have: num((st.querySelector('.xpnums-have') || {}).textContent), level: (st.querySelector('.pf-level') || {}).textContent };
  }catch(e){ out.errs.push(String(e && e.stack || e)); }
  return out;
}"""


def section_climb(br):
    print("\nB. the climb: no 'extra XP', the number on the left goes into each level")
    for (label, w, h), lv in ((PHONE, 44), (TABLET, 43)):
        ctx, pg = boot(br, w, h)
        pts = pg.evaluate("(lv) => xpForLevel(lv) + 600", lv)
        r = pg.evaluate(CLIMB, {"badges": 5, "points": pts})
        ctx.close()
        if r.get("errs"):
            check("%s: the climb ran" % label, False, r["errs"])
            continue
        fr, to, s = r["from"], r["to"], r["samples"]
        tot = to["total"]
        check("%s: no text matching 'extra XP' in any of %d frames" % (label, len(s)), r["extraText"] is None and len(s) >= 30, r["extraText"])
        check("%s: the number on the left starts larger than the span (%s / %s, the bar full)" % (label, s[0]["have"] if s else None, s[0]["need"] if s else None),
              s and s[0]["have"] == fr["into"] and s[0]["need"] == fr["span"] and fr["into"] > fr["span"], [s[:2], fr])
        rec = r.get("rec") or {}
        steps = rec.get("steps") or []
        n = to["level"] - fr["level"]
        check("%s: a level up at every level - the bar's level-up class and res.levelup (%d levels, %d classes, %d sounds)" % (label, n, r["ups"], r["levelups"]),
              n > 0 and r["ups"] >= n and r["levelups"] >= min(n, 1) and r["levelups"] >= n - (n // 2 if n > 10 else 0), [r["ups"], r["levelups"], n])
        check("%s: at each level the number on the left is the previous less that level's cost" % label,
              len(steps) == n and all(st.get("prev") is not None and st["prev"] - st["cost"] == st["have"] for st in steps)
              and [st["cost"] for st in steps] == r["spans"] and (not steps or steps[0]["prev"] == fr["into"]),
              [(st.get("level"), st.get("prev"), st.get("cost"), st.get("have")) for st in steps][:6])
        check("%s: nothing lost - xpForLevel(level) + x is the total (%d) at every step" % (label, tot),
              steps and all(st["sum"] == tot and int(r["xpFor"][str(st["level"])]) + st["have"] == tot for st in steps),
              [(st["level"], st["have"], st["sum"]) for st in steps][:6])
        # the left number only falls within a level (it pours in), never rises
        rises = []
        for i in range(1, len(s)):
            if s[i]["lv"] == s[i - 1]["lv"] and s[i]["have"] > s[i - 1]["have"] and s[i]["lv"] != to["level"] + 99:
                rises.append((s[i - 1], s[i]))
        check("%s: within a level the number on the left only goes down, into the level" % label, not rises, rises[:3])
        check("%s: it ends on Level %s with %s / %s XP" % (label, to["level"], to["into"], to["span"]),
              r["after"]["level"] == "Level %d" % to["level"] and r["after"]["have"] == to["into"], [r["after"], to])


# --------------------------------------------------------------------------
HANDOVER = """async () => {
  const out = { errs: [], rot: [], flip: false, oldFade: false, newFade: false, frames: 0 };
  try{
  showProfile(); await new Promise(r => setTimeout(r, 900));
  const panel = document.querySelector('.screen-profile');
  const goal = panel.querySelector('.pf-goal');
  if(!goal){ out.errs.push('no .pf-goal'); return out; }
  const old = goal.cloneNode(true);
  const scene = { nums: { cap: levelStateFor(store) }, oldGoal: old, from: null, to: null, phase: 'return' };
  window.rankUpSceneEnd = () => { out.ended = true; };
  rankUpScene = scene;
  let done = false;
  rankUpProfileReturn(scene, panel).then(() => { done = true; });
  const T0 = performance.now();
  const rotOf = tf => tf && (tf.startsWith('matrix3d') || /rotate/.test(tf));
  await new Promise(res => { const tick = () => {
    out.frames++;
    document.querySelectorAll('.pf-goal').forEach(g => {
      if(g.classList.contains('ru-flip-out') || g.classList.contains('ru-flip-in')) out.flip = true;
      const tf = getComputedStyle(g).transform;
      if(rotOf(tf)) out.rot.push(tf.slice(0, 40));
      (g.getAnimations ? g.getAnimations() : []).forEach(x => {
        const kf = x.effect && x.effect.getKeyframes ? x.effect.getKeyframes() : [];
        if(kf.some(k => /rotate|matrix3d/.test(String(k.transform || '')))) out.rot.push('kf:' + (x.animationName || 'waapi'));
        if(kf.length >= 2 && String(kf[0].opacity) === '1' && String(kf[kf.length - 1].opacity) === '0' && g !== goal) out.oldFade = true;
        if(kf.length >= 2 && String(kf[0].opacity) === '0' && String(kf[kf.length - 1].opacity) === '1' && g === goal) out.newFade = true;
      });
    });
    if(!done && performance.now() - T0 < 15000) requestAnimationFrame(tick); else res(); };
    requestAnimationFrame(tick); });
  out.left = document.querySelectorAll('.pf-goal').length;
  rankUpScene = null;
  }catch(e){ out.errs.push(String(e && e.stack || e)); }
  return out;
}"""


def section_handover(br):
    print("\nC. the challenge card fades into the next one, no flip")
    for label, w, h in (PHONE, TABLET):
        ctx, pg = boot(br, w, h)
        r = pg.evaluate(HANDOVER)
        ctx.close()
        if r.get("errs"):
            check("%s: ran" % label, False, r["errs"])
            continue
        check("%s: no flip class and no rotate / 3D transform on a challenge card in %d frames" % (label, r["frames"]),
              not r["flip"] and not r["rot"] and r["frames"] >= 20, [r["flip"], r["rot"][:4]])
        check("%s: the completed card fades out and the next fades in, by opacity" % label, r["oldFade"] and r["newFade"], r)
        check("%s: one card left when it is done" % label, r["left"] == 1, r["left"])


def main():
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=cb.CHROME if hasattr(cb, "CHROME") else None)
        try:
            if not ONLY or "A" in ONLY:
                section_status(br)
            if not ONLY or "B" in ONLY:
                section_climb(br)
            if not ONLY or "C" in ONLY:
                section_handover(br)
        finally:
            br.close()
    print("\n%s" % ("ALL PASS" if not FAILURES else "%d FAILURE(S)" % len(FAILURES)))
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
