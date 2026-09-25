#!/usr/bin/env python3
"""Stats you can ask, a badge case whose shadow is not cut off, and the
banner that says the daily question is out.

Three small things that no other gate can see. The sweep asks "is
anything broken on this device"; check-positions asks "did it land where
I meant it to"; neither can tell you that a stat card is not a button,
that a slot's shade is still at a quarter strength where its box stops,
or that a banner telling you to tap something is not itself tappable.

Every check here was written against build 189 and fails there:

    python3 tools/check-statsbadges.py --against /path/to/189/index.html

The badge-case check is PIXEL-MEASURED on purpose. "The shadow is hard
cut off at the top" is not visible in the DOM at all - the element is
there, the gradient string is there, and the only thing wrong is how many
levels of shade are left at the boundary. Build 189 measures a 9-level
step across the top edge of every unearned slot; a fade that has
genuinely reached zero measures under 2.

Device-independent, so it runs once.
Exits non-zero on any failure.
"""
import argparse
import functools
import http.server
import json
import os
import re
import shutil
import socket
import sys
import tempfile
import threading

from PIL import Image
from playwright.sync_api import sync_playwright

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ap = argparse.ArgumentParser()
ap.add_argument("--against")
A = ap.parse_args()
SERVE = ROOT
if A.against:
    other = A.against if os.path.isabs(A.against) else os.path.join(ROOT, A.against)
    SERVE = tempfile.mkdtemp(prefix="statsbadges-")
    shutil.copy(other, os.path.join(SERVE, "index.html"))
    if os.path.exists(os.path.join(ROOT, "version.json")):
        shutil.copy(os.path.join(ROOT, "version.json"), SERVE)
    print("against: %s" % other)

_VR = open(os.path.join(ROOT, "tools", "check-vroom.py"), encoding="utf-8").read()
FAKE = re.search(r'FAKE_FIRESTORE = """(.*?)"""', _VR, re.S).group(1)

_s = socket.socket(); _s.bind(("127.0.0.1", 0))
PORT = _s.getsockname()[1]; _s.close()


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


SERVER = http.server.ThreadingHTTPServer(
    ("127.0.0.1", PORT), functools.partial(_Quiet, directory=SERVE))
threading.Thread(target=SERVER.serve_forever, daemon=True).start()

FAILURES = []


def check(name, ok, detail=""):
    print("  %-4s %s%s" % ("PASS" if ok else "FAIL", name,
                           ("  -> " + str(detail)) if detail else ""))
    if not ok:
        FAILURES.append(name)


# A FIXTURE IS AN EXISTING, UP-TO-DATE ACCOUNT, so it carries tourRev -
# without it the one-time tour re-arm fires inside the gate and puts a
# tooltip over whatever is being measured.
SEED = """()=>{
  document.getElementById('splashscreen')?.remove();
  try{ __useFake(); }catch(e){}
  store.onboardingComplete = true; store.firstName = 'Madison';
  store.publicId = 'me01'; store.tourRev = 99; store.avatarChar = 'wizard';
  store.lifetime = { points: 42000, answered: 5400, correct: 4980, drillPlays: 64,
                     examPlays: 22, gamePlays: 9, perfectTests: 141,
                     currentStreak: 23, longestStreak: 57 };
  ['seenFirstResultsTour','seenModeSelectTour','seenProfileTour','seenRewardsTour',
   'seenSettingsTour','seenUnitOptionsTour','seenUnitSelectTour','seenMainMenuTour',
   'seenCustomizeTour','seenFriendsTour'].forEach(k => store[k] = true);
  /* One unit mastered and one untouched, so the case has both an earned
     tile and an empty slot to measure - a case of sixteen empty slots
     cannot tell you whether an earned one lights up. */
  try{
    const us = topicsIn(QUESTIONS);
    store.unitPerfects = store.unitPerfects || {};
    store.unitPerfects[us[0]] = 400;
  }catch(e){}
  showHome();
}"""


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = br.new_context(viewport={"width": 440, "height": 956})
        ctx.add_init_script(FAKE)
        ctx.add_init_script("try{localStorage.setItem('class26e.frame.ok','go-live-1');}catch(e){}")
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto("http://127.0.0.1:%d/index.html" % PORT)
        pg.wait_for_timeout(2400)
        pg.evaluate(SEED)
        pg.wait_for_timeout(300)

        # ---------------------------------------------------------------
        print("\n1. a stat says what it counts")
        pg.evaluate("()=>showProfile('stats')")
        pg.wait_for_timeout(600)
        r = pg.evaluate("""()=>{
          const cards = [...document.querySelectorAll('.stat-card')];
          return { n: cards.length,
                   tags: [...new Set(cards.map(c => c.tagName))],
                   labels: cards.map(c => (c.querySelector('.stat-lab')||{}).textContent),
                   why: !!document.querySelector('.stat-why') };}""")
        check("every stat card is a real button", r["tags"] == ["BUTTON"], r["tags"])
        check("ten of them", r["n"] == 10, r["n"])
        check("there is an explanation panel", r["why"] is True)
        if r["why"]:
            first = pg.evaluate("""()=>{
              const c = document.querySelectorAll('.stat-card')[0];
              const box = document.querySelector('.stat-why');
              const before = box.hidden;
              c.click();
              const after = { hidden: box.hidden, label: box.querySelector('.stat-why-label').textContent,
                              text: box.textContent, asked: c.classList.contains('is-asked'),
                              expanded: c.getAttribute('aria-expanded') };
              return { before, after };}""")
            check("it starts closed", first["before"] is True)
            check("tapping a card opens it", first["after"]["hidden"] is False)
            check("and marks that card", first["after"]["asked"] is True
                  and first["after"]["expanded"] == "true")
            check("with that card's own label on it",
                  first["after"]["label"] == "THIS WEEK", first["after"]["label"])
            check("and a sentence that is not empty",
                  len(first["after"]["text"] or "") > 40, len(first["after"]["text"] or ""))
            second = pg.evaluate("""()=>{
              const cs = [...document.querySelectorAll('.stat-card')];
              cs[5].click();
              const box = document.querySelector('.stat-why');
              const openCount = cs.filter(c => c.classList.contains('is-asked')).length;
              const label = box.querySelector('.stat-why-label').textContent;
              cs[5].click();
              return { openCount, label, closedAfterSecondTap: box.hidden };}""")
            check("only one explanation is open at a time", second["openCount"] == 1,
                  second["openCount"])
            check("tapping the open card closes it",
                  second["closedAfterSecondTap"] is True)
            """Every card must have a sentence. A label added later with
            no entry in STAT_MEANINGS opens an empty panel, which reads
            as broken rather than as missing."""
            gaps = pg.evaluate("""()=>{
              const out = [];
              [...document.querySelectorAll('.stat-card')].forEach(c => {
                c.click();
                const box = document.querySelector('.stat-why');
                const txt = box.querySelector('.stat-why-label').nextSibling;
                if(box.hidden || !txt || (txt.textContent || '').length < 30){
                  out.push((c.querySelector('.stat-lab')||{}).textContent);
                }
                c.click();
              });
              return out;}""")
            check("no card opens an empty panel", not gaps, gaps)

        # ---------------------------------------------------------------
        print("\n2. the badge case")
        pg.evaluate("()=>showProfile('badges')")
        pg.wait_for_timeout(800)
        tiles = pg.evaluate("""()=>{
          const t = [...document.querySelectorAll('.badge-tile')];
          const locked = t.find(x => x.classList.contains('is-locked'));
          const earned = t.find(x => x.classList.contains('is-earned'));
          const box = el => { if(!el) return null;
            const a = el.querySelector('.badge-tile-art');
            a.scrollIntoView({block:'center'});
            const r = a.getBoundingClientRect();
            return { x:r.left, y:r.top, width:r.width, height:r.height }; };
          return { n: t.length,
                   lockedBox: box(locked), earnedBox: box(earned),
                   glow: earned ? (earned.querySelector('.badge-tile-art')
                                   .style.getPropertyValue('--badge-glow') || '') : null };}""")
        check("sixteen tiles", tiles["n"] == 16, tiles["n"])
        check("an earned tile carries its unit's own colour",
              bool((tiles["glow"] or "").strip()), tiles["glow"])
        if tiles["lockedBox"]:
            b = tiles["lockedBox"]
            """Sample a strip spanning the slot's top edge - a few pixels
            of tile above it and a few of shade below. A fade that has
            reached zero crosses that boundary smoothly; one that is
            still a quarter strength when its box stops puts a step
            there, and the step is what "hard cut off" means."""
            """THE WINDOW MATTERS AS MUCH AS THE MEASUREMENT. A first
            draft sampled 10px either side of the art box's top edge and
            reported a 4.9-level step on a build whose shade is smooth -
            the step was the tile ABOVE, whose progress line sits about
            24px up. The shade itself lives inside the pseudo-element's
            own box, so the window runs from a quarter of a tile above
            the art box down to just inside it, in a column narrow
            enough to stay clear of the badge artwork's own drawn lip."""
            clip = {"x": b["x"] + b["width"] * 0.35, "y": b["y"] - b["height"] * 0.25,
                    "width": max(8, b["width"] * 0.30), "height": b["height"] * 0.30}
            path = os.path.join(tempfile.mkdtemp(prefix="slot-"), "top.png")
            pg.screenshot(path=path, clip=clip)
            im = Image.open(path).convert("RGB")
            w, h = im.size
            px = list(im.getdata())
            lum = [0.299 * r + 0.587 * g + 0.114 * bb for r, g, bb in px]
            rows = [sum(lum[y * w:(y + 1) * w]) / w for y in range(h)]
            step = max(abs(rows[i + 1] - rows[i]) for i in range(len(rows) - 1))
            check("the slot's shade is not cut off at its top edge", step < 2.5,
                  "biggest one-row step %.1f levels" % step)

        # ---------------------------------------------------------------
        print("\n3. the daily question announcement")
        pg.evaluate("()=>showHome()")
        pg.wait_for_timeout(400)
        d = pg.evaluate("""()=>{
          let tapped = false;
          const btn = document.querySelector('.daily-question-fab');
          if(!btn) return { noButton: true };
          const realClick = btn.click.bind(btn);
          btn.click = () => { tapped = true; };
          announceDailyReset(btn);
          const el = document.getElementById('dailyalert');
          if(!el) return { noBanner: true };
          const cs = getComputedStyle(el);
          const out = {
            live: el.classList.contains('is-live'),
            fresh: el.classList.contains('is-fresh'),
            pointer: cs.pointerEvents,
            role: el.getAttribute('role'),
            tag: (el.querySelector('.daily-alert-tag')||{}).textContent || null,
            text: (el.querySelector('.daily-alert-text')||{}).textContent || null,
            icon: !!el.querySelector('.daily-alert-icon svg'),
            sweep: getComputedStyle(el, '::after').animationName,
            onTop: el.getBoundingClientRect().top
          };
          el.click();
          out.tapped = tapped;
          out.goneAfterTap = !document.getElementById('dailyalert');
          btn.click = realClick;
          return out;}""")
        print("     ", json.dumps(d))
        check("the announcement is the live banner", d.get("live") is True)
        check("it can actually be tapped", d.get("pointer") == "auto", d.get("pointer"))
        check("it says what it is", (d.get("tag") or "") == "DAILY QUESTION", d.get("tag"))
        check("it carries an icon", d.get("icon") is True)
        check("it is announced to assistive tech as a button",
              d.get("role") == "button", d.get("role"))
        check("the first sighting sweeps",
              (d.get("sweep") or "none") != "none", d.get("sweep"))
        check("and rings, finitely", d.get("fresh") is True)
        check("tapping it opens the daily question", d.get("tapped") is True)
        check("and dismisses itself", d.get("goneAfterTap") is True)
        """The other two messages this banner carries are plain
        sentences and must stay plain - a locked-question notice with a
        TAP on it would be telling somebody to do something that does
        not work."""
        plain = pg.evaluate("""()=>{
          showDailyAlert('A plain sentence.');
          const el = document.getElementById('dailyalert');
          const out = { live: el.classList.contains('is-live'),
                        pointer: getComputedStyle(el).pointerEvents,
                        text: el.textContent };
          el.remove();
          return out;}""")
        check("a plain message stays plain", plain["live"] is False
              and plain["pointer"] == "none", plain)

        check("no uncaught JS along the way", not errs, errs[:3])
        ctx.close(); br.close()
    SERVER.shutdown()
    print("\n%s  (%d failure(s))" %
          ("ALL PASS" if not FAILURES else "FAILED: " + ", ".join(FAILURES), len(FAILURES)))
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
