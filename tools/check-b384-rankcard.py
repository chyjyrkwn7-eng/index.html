#!/usr/bin/env python3
"""Build 384.74: the rank ladder's Up next card is the newer solid card, on the Rank tab and in the rank-up journey.

  python3 tools/check-b384-rankcard.py [--against FILE|REV] [--only A,B] [--quick]

Madison (he/him), on a frame of the rank-up recording (384.55, Bronze to Silver, the journey's "upnext" phase): the Up next card
(Gold, "UP NEXT", Level 40 - 5 badges, Theme / Flare / Solar) was a tinted gold glass card - a gold-tinted fill, a gold rim, a white
sheen streak across it, translucent rows - beside Silver ("You are here") and Platinum ("Locked"), which were the flat card. "This
needs to be updated to match the newer look. That's the rank up video, ensure it's even updated outside of the video too though."
The newer look (build 383, the clean look): every card is one solid colour from the surface tokens (--clean-card), no rim, no shadow,
no blur, no gradient of its own; a state's colour lives only in small marks (the chip, the circle, the unlock dots).

  A. THE SETTLED LADDER, every state, both classes (academy, Fire Code), an iPhone 17 Pro Max (440x956) and an iPad Pro 11"
     (834x1194), installed. The four state cards (Reached / You are here / Up next / Locked) read off the real page: the same solid
     background (the --clean-card token, read from a probe, not typed), no background-image, no box-shadow, no backdrop-filter, no
     filter, no border painted, no visible ::before / ::after layer, full opacity; the unlock rows the same flat tile on all four;
     nothing inside a card but the allowed marks (the state chip, the name, the unlock dots / flares / characters / banners, the
     progress meter) paints a gradient, a glow or a coloured fill. And Up next still reads as the next target: its chip carries the
     rank's colour (different from the Locked chip's), its circle is dashed.
  B. THE JOURNEY'S UP NEXT POP (real time, a rank-up from the Profile tap: Bronze to Silver, Gold pops as Up next), sampled every
     ~200ms from the pop to the end of the phase, phone and iPad, both classes: at every sample the popping card is the same solid
     card as the Silver card beside it, no layer of the pop (.ru-nextfx) paints a gradient or a shadow, no sheen layer exists, and
     by the end of the phase the pop's layer is gone and the card is exactly the settled Up next card.

Every check was written against a build where it fails: `--against origin/claude/b384-rankjourney` (384.55) must FAIL (B).
"""
import os, re, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b384_rankjourney_lib import *
from playwright.sync_api import sync_playwright

ROOT_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


ONLY = set((arg("--only") or "A,B").split(","))
QUICK = "--quick" in sys.argv
AGAINST = arg("--against")
if AGAINST and not os.path.exists(AGAINST):
    tmp = os.path.join(tempfile.mkdtemp(), "index.html")
    open(tmp, "wb").write(subprocess.check_output(["git", "show", "%s:index.html" % AGAINST], cwd=ROOT_))
    AGAINST = tmp
SELF = Served(AGAINST)
FAILS = []
_BUF = None


def ck(name, ok, info=None):
    line = ("  PASS  " if ok else "  FAIL  ") + name + ("" if ok or info is None else "  -> " + str(info)[:700])
    if _BUF is not None:
        _BUF.append((line, ok, name))
        return
    print(line, flush=True)
    if not ok:
        FAILS.append(name)


def case(fn, *a, tries=6):
    """one self-contained case (its own browser); the sandbox's chromium now and then crashes a tab, so a case that dies on
    'crashed' / 'closed' is run again from the start and only the run that finished is reported"""
    global _BUF
    last = None
    for _ in range(tries):
        _BUF = []
        try:
            fn(*a)
            buf, _BUF = _BUF, None
            for line, ok, name in buf:
                print(line, flush=True)
                if not ok:
                    FAILS.append(name)
            return
        except Exception as e:
            last = e
            _BUF = None
            if not re.search(r"crash|closed|Target", str(e)):
                raise
    raise last


def launch(pw):
    return pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox", "--disable-dev-shm-usage"])


def page(br, w, h, cls, retries=3):
    last = None
    for _ in range(retries):
        try:
            return open_page(br, SELF, cls, w, h, 1)
        except Exception as e:
            last = e
    raise last


# what the page paints for one ladder card: its own surface, its layers, and what is inside it. Read off computed styles.
MEASURE = r"""(sel) => {
  const probe = document.createElement('div'); probe.style.cssText = 'position:absolute;left:-9999px;top:0;width:4px;height:4px;background:var(--clean-card)';
  document.querySelector('#stage').appendChild(probe);
  const token = getComputedStyle(probe).backgroundColor; probe.remove();
  const probe2 = document.createElement('div'); probe2.style.cssText = 'position:absolute;left:-9999px;top:0;width:4px;height:4px;background:var(--clean-card-2)';
  document.querySelector('#stage').appendChild(probe2);
  const token2 = getComputedStyle(probe2).backgroundColor; probe2.remove();
  const num = s => (s.match(/[\d.]+/g) || []).map(Number);
  const alpha = s => { const n = num(s); return /^rgba|\//.test(s) ? (n.length > 3 ? n[3] : 1) : 1; };
  const chroma = s => { const n = num(s).slice(0, 3); return Math.max(...n) - Math.min(...n); };
  const hasGrad = bi => /gradient/.test(bi);
  const lit = (c) => { const n = c.getClientRects().length; return n > 0; };
  /* inside a card these are the marks a state's colour may live in */
  const ALLOWED = '.rankmap-state, .rankmap-name, .rankmap-giftico, .rankmap-giftico *, .rankmap-giftav, .rankmap-giftav *, .rankmap-dot, .rankmap-swatch, .rankmap-swatch *, .rankmap-giftbubble, .rankmap-giftbubble *, .rankmap-giftbanner, .rankmap-giftbanner *, .rankmap-giftlock, .rankmap-giftlock *, .rankcard-meter, .rankcard-meter *, .rankmap-meter, .rankmap-meter *, .ru-nextfx, .ru-nextfx *';
  const out = [];
  document.querySelectorAll(sel || '.rankmap-stop').forEach(stop => {
    const card = stop.querySelector('.rankmap-card'); if(!card) return;
    const c = getComputedStyle(card);
    const pseudo = ['::before', '::after'].map(p => { const q = getComputedStyle(card, p); const painted = q.content !== 'none' && q.content !== 'normal' && q.display !== 'none' && +q.opacity > 0.01;
      return { p, painted, bi: q.backgroundImage, bg: q.backgroundColor, shadow: q.boxShadow, content: q.content }; });
    const node = stop.querySelector('.rankmap-node'), chip = stop.querySelector('.rankmap-state'), name = stop.querySelector('.rankmap-name');
    const rows = [...card.querySelectorAll('.rankmap-gift')].map(r => { const q = getComputedStyle(r); return { bg: q.backgroundColor, bi: q.backgroundImage, shadow: q.boxShadow, blur: q.backdropFilter || 'none' }; });
    /* anything inside the card, outside the allowed marks, that paints a gradient, a glow or a coloured fill */
    const stray = [];
    card.querySelectorAll('*').forEach(e => {
      if(e.matches(ALLOWED) || e.closest(ALLOWED) || !lit(e)) return;
      const q = getComputedStyle(e);
      const bad = [];
      if(hasGrad(q.backgroundImage)) bad.push('gradient');
      if(q.boxShadow !== 'none') bad.push('shadow ' + q.boxShadow.slice(0, 50));
      if((q.backdropFilter || 'none') !== 'none') bad.push('blur');
      if(alpha(q.backgroundColor) > 0 && !e.matches('.rankmap-gift') && chroma(q.backgroundColor) > 14) bad.push('coloured fill ' + q.backgroundColor);
      if(bad.length) stray.push((e.className && e.className.baseVal === undefined ? String(e.className) : e.tagName).slice(0, 40) + ': ' + bad.join(', '));
    });
    const own = (e, a) => { const q = getComputedStyle(e); return { bg: q.backgroundColor, bi: q.backgroundImage }; };
    out.push({
      name: name ? name.textContent : '', state: chip ? chip.textContent : '', cls: stop.className,
      bg: c.backgroundColor, bi: c.backgroundImage, shadow: c.boxShadow, blur: (c.backdropFilter || c.webkitBackdropFilter || 'none'), filter: c.filter,
      opacity: +c.opacity, borderW: c.borderTopWidth, borderC: c.borderTopColor, borderA: alpha(c.borderTopColor), borderS: c.borderTopStyle,
      pseudo, rows, stray, chip: chip ? { bg: getComputedStyle(chip).backgroundColor, color: getComputedStyle(chip).color } : null,
      nodeStyle: node ? getComputedStyle(node).borderTopStyle : null, nameColor: name ? getComputedStyle(name).color : null,
      fx: [...card.querySelectorAll('.ru-nextfx')].map(f => ({ kids: [...f.children].map(k => { const q = getComputedStyle(k); return { cls: k.className, bi: q.backgroundImage, shadow: q.boxShadow, op: +q.opacity, bg: q.backgroundColor }; }) })),
      token, token2
    });
  });
  return out;
}"""


def judge(tag, c, token):
    """one card, against the token: the solid-card checks; returns a list of what is wrong"""
    bad = []
    if c["bg"] != token:
        bad.append("background %s is not the card token %s" % (c["bg"], token))
    if c["bi"] != "none":
        bad.append("background-image %s" % c["bi"][:80])
    if c["shadow"] != "none":
        bad.append("box-shadow %s" % c["shadow"][:80])
    if c["blur"] != "none":
        bad.append("backdrop-filter %s" % c["blur"])
    if c["filter"] != "none":
        bad.append("filter %s" % c["filter"])
    if c["borderA"] > 0 and float(re.match(r"[\d.]+", c["borderW"]).group(0)) > 0 and c["borderS"] != "none":
        bad.append("a border is painted %s %s" % (c["borderW"], c["borderC"]))
    if c["opacity"] < .999:
        bad.append("opacity %s" % c["opacity"])
    for p in c["pseudo"]:
        if p["painted"]:
            bad.append("%s paints (%s, %s)" % (p["p"], p["bi"][:50], p["bg"]))
    for f in c["fx"]:
        for k in f["kids"]:
            if "gradient" in k["bi"] and k["op"] > .01:
                bad.append("the pop's layer %s paints a gradient (opacity %.2f)" % (k["cls"], k["op"]))
            if k["shadow"] != "none" and k["op"] > .01:
                bad.append("the pop's layer %s paints a glow (opacity %.2f)" % (k["cls"], k["op"]))
    if c["stray"]:
        bad.append("inside the card: %s" % "; ".join(c["stray"][:3]))
    return bad


# ---------------------------------------------------------------- A
def a_case(pw, cls, w, h, lab, rank):
    br = launch(pw)
    ctx, pg, errs = page(br, w, h, cls)
    pg.evaluate(SEED_A, {"topic": TOPIC[cls], "rank": rank, "mode": "owed", "owe": 1})
    pg.evaluate("()=>{ const ri = TIER_ORDER_FULL.indexOf(rankOf(store)); store.rankUpShown = ri + 1; store.rankMapSeen = ri + 1; store.seenUnlockedTiers = TIER_ORDER_FULL.slice(0, ri + 1); saveStore(); showRanksScreen('ranks'); }")
    pg.wait_for_timeout(1500)
    cards = pg.evaluate(MEASURE)
    lab2 = "%s, %s, an account at %s" % (cls, lab, rank)
    by = {}
    for c in cards:
        k = "here" if "is-here" in c["cls"] else "next" if "is-next" in c["cls"] else "locked" if "is-locked" in c["cls"] else "reached" if "is-reached" in c["cls"] else "?"
        by.setdefault(k, c)
    want = {"rookie": ("here", "next", "locked"), "ranger": ("reached", "here", "next", "locked")}[rank]
    ck("A %s: the ladder has the states %s (%s)" % (lab2, "/".join(want), "/".join(sorted(by))), all(k in by for k in want), [c["cls"] for c in cards])
    token = cards[0]["token"]
    for k in want:
        bad = judge(k, by[k], token)
        ck("A %s: the %s card (%s) is the solid card: the surface token, no gradient / shadow / blur / rim / sheen layer, nothing glowing inside" % (lab2, k, by[k]["name"] + " " + by[k]["state"]), not bad, bad)
    bgs = sorted({by[k]["bg"] for k in want})
    ck("A %s: all %d state cards are one colour (%s)" % (lab2, len(want), bgs), len(bgs) == 1, bgs)
    rows = sorted({(r["bg"], r["bi"], r["shadow"], r["blur"]) for k in want for r in by[k]["rows"]})
    ck("A %s: every unlock row on every state is the same flat tile (%s)" % (lab2, rows), len(rows) == 1 and rows[0][1] == "none" and rows[0][2] == "none" and rows[0][3] == "none", rows)
    nx = by["next"]; lk = by["locked"]
    ck("A %s: Up next still reads as the target: its chip takes the rank's colour (%s, the Locked chip is %s) and its circle is dashed (%s)" % (
        lab2, nx["chip"]["bg"], lk["chip"]["bg"], nx["nodeStyle"]), nx["chip"]["bg"] != lk["chip"]["bg"] and nx["nodeStyle"] == "dashed" and lk["nodeStyle"] != "dashed", [nx["chip"], lk["chip"], nx["nodeStyle"]])
    ck("A %s: no page errors" % lab2, not errs, errs[:3])
    ctx.close(); br.close()


def section_a(pw):
    sizes = [(440, 956, "iPhone 17 Pro Max"), (834, 1194, "iPad Pro 11")]
    for cls in ("academy", "ifc"):
        for w, h, lab in sizes:
            for rank in (("ranger",) if QUICK else ("ranger", "rookie")):
                case(a_case, pw, cls, w, h, lab, rank)


# ---------------------------------------------------------------- B
def b_case(pw, cls, w, h, lab):
    br = launch(pw)
    ctx, pg, errs = page(br, w, h, cls)
    pg.evaluate(SEED_A, {"topic": TOPIC[cls], "rank": "ranger", "mode": "owed", "owe": 1, "fresh": False})
    samples = []
    pop = {"t0": None}

    def tick(pg_, st):
        if st["sc"] != "upnext":
            return
        r = pg_.evaluate("""(m)=>{ const np = document.querySelector('.rankmap-stop.ru-nextpop'); if(!np) return null;
          const all = (%s)('.rankmap-stop'); const mine = all.find(c => /ru-nextpop/.test(c.cls));
          const here = all.find(c => /is-here/.test(c.cls));
          return { mine, here, t: Math.round(performance.now()), kids: np.querySelectorAll('.ru-nextfx > i').length,
                   sheen: !!np.querySelector('.ru-nx-sheen, .ru-nx-wash') }; }""" % MEASURE, None)
        if r and r["mine"]:
            if pop["t0"] is None:
                pop["t0"] = r["t"]
            r["dt"] = r["t"] - pop["t0"]
            samples.append(r)

    fr, ev, lt, tap = run_journey(pg, None, 1, home_wait=3, timeout=150, settle=0, stop_after="top", tick=tick)
    lab2 = "%s, %s" % (cls, lab)
    ck("B %s: the Up next pop was sampled (%d samples over %.1fs)" % (lab2, len(samples), (samples[-1]["dt"] / 1000 if samples else 0)), len(samples) >= 6 and samples[-1]["dt"] >= 1800, len(samples))
    if samples:
        token = samples[0]["mine"]["token"]
        bads = []
        for s in samples:
            b = judge("pop", s["mine"], token)
            if s["sheen"]:
                b.append("a sheen / wash layer exists")
            if s["here"] and s["here"]["bg"] != s["mine"]["bg"]:
                b.append("not the colour of the You are here card (%s vs %s)" % (s["mine"]["bg"], s["here"]["bg"]))
            if b:
                bads.append((s["dt"], b))
        ck("B %s: at every sample of the pop the Gold card is the solid card, the same colour as Silver's, with no wash, glow or sheen layer" % lab2, not bads, bads[:2])
        last = samples[-1]
        ck("B %s: by the end of the phase the pop's layer is gone (%d left) and the card is the settled Up next card" % (lab2, last["kids"]),
           last["kids"] == 0 and not judge("end", last["mine"], token), judge("end", last["mine"], token))
        ck("B %s: the chip carries the rank colour while it pops (%s) and the card lifted (a ring, then gone)" % (lab2, last["mine"]["chip"]["bg"]),
           last["mine"]["chip"]["bg"] != "rgba(255, 255, 255, 0.07)" and any(s["kids"] for s in samples), last["mine"]["chip"])
    ck("B %s: no page errors" % lab2, not errs, errs[:3])
    ctx.close(); br.close()


def section_b(pw):
    runs = [("academy", 440, 956, "iPhone 17 Pro Max"), ("ifc", 440, 956, "iPhone 17 Pro Max"), ("academy", 834, 1194, "iPad Pro 11")]
    if QUICK:
        runs = runs[:1]
    for cls, w, h, lab in runs:
        case(b_case, pw, cls, w, h, lab)


def main():
    print("serving %s (build %s)" % (SELF.src, SELF.build))
    with sync_playwright() as pw:
        for key, title, fn in (("A", "the settled ladder: every state card is the one solid card", section_a),
                               ("B", "the journey's Up next pop leaves the card solid", section_b)):
            if key in ONLY:
                print("\n  %s. %s" % (key, title))
                fn(pw)
    print("\n%s (%d failed)" % ("ALL PASS" if not FAILS else "FAILURES", len(FAILS)))
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
