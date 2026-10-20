#!/usr/bin/env python3
"""Build 327 (b327h): one account each.

Madison, Oct 20:
  "when you get on and you aren't logged in, ensure that page is clear and
   makes sense to prevent people from making a second account ... people
   keep making second accounts. We need the sign up page to clear that
   signing in or creating an account.."
A classmate whose account is "TSale" signed up again as "T.Sale": build
322's name check only ignored case and spaces.

  A  the name key: punctuation, spacing and case make no different person,
     an email-like name is the part before "@", and nothing near-matches
  B  the username screen STOPS on a taken name: named plainly, with the
     row's character and level, "That's me - sign in" first, and "I'm a
     different person" does not go on - only a free name does
  C  a board not yet read is read before a name is let through
  D  Welcome, the check before sign-up and the code screen say plainly
     what each choice is, what a second account costs, and "Ask an admin for help"
  E  nothing beyond the public rankings row is shown or read
  F  a rename in Customize may not take a name somebody else wears

Every section fails on the build before (7ec06e0):
  python3 tools/check-b327-i.py
  python3 tools/check-b327-i.py --against /path/to/old/index.html
"""
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py"))
cb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cb)   # reads --against from sys.argv itself
booted, USED_ACCOUNT, FAILURES = cb.booted, cb.USED_ACCOUNT, cb.FAILURES


def check(name, ok, detail=""):
    """cb.check, with the detail printed only when the check fails."""
    cb.check(name, ok, "" if ok else detail)

ROWS = [
    {"pub": "tsaleaaaaaaa", "firstName": "TSale", "avatarChar": "alien", "level": 24,
     "badges": 6, "xp": 12345, "hundos": 77, "correct": 913},
    {"pub": "dmenbbbbbbbb", "firstName": "dmendoza9989@gmail.com", "avatarChar": "ghost", "level": 9},
    {"pub": "alexcccccccc", "firstName": "Alex", "avatarChar": "wizard", "level": 31},
]
ROWS_JS = json.dumps(ROWS)

SETUP = """
  window.__wait = ms => new Promise(res => setTimeout(res, ms));
  window.__rows = () => { leaderboardRows = JSON.parse(JSON.stringify(%s)); boardFetchedAt = Date.now(); };
  window.__type = v => { const i = document.querySelector('.onboarding-shortform-panel .searchbox');
                         i.value = v; i.dispatchEvent(new Event('input')); };
  window.__go = () => [...document.querySelectorAll('.onboarding-shortform-panel > .playbtn')].pop();
  window.__vis = el => !!el && el.isConnected && !el.hidden && getComputedStyle(el).display !== 'none'
                        && getComputedStyle(el).visibility !== 'hidden' && el.getBoundingClientRect().height > 0;
""" % ROWS_JS


def section_key(br):
    print("\nA. the name key ignores punctuation, spacing and case")
    ctx, pg = booted(br, 440, 956)
    pg.evaluate("() => { %s }" % SETUP)
    r = pg.evaluate("""() => {
      __rows();
      const t = n => nameTakenOnBoard(n);
      return { dot: t('T.Sale'), space: t('T Sale'), lower: t('tsale'), under: t('t_sale'), dash: t('t-sale!'),
               email: t('DMendoza9989'), emailFull: t('dmendoza9989@gmail.com'),
               near1: t('TSales'), near2: t('Alex2'), near3: t('Ale'), free: t('Taylor') }; }""")
    ctx.close()
    check("'T.Sale', 'T Sale', 'tsale', 't_sale' and 't-sale!' all hit the existing 'TSale' row",
          all(r[k] == "TSale" for k in ("dot", "space", "lower", "under", "dash")), r)
    check("a row named as an email matches on the part before the '@'",
          r["email"] == "dmendoza9989@gmail.com" and r["emailFull"] == "dmendoza9989@gmail.com", r)
    check("nothing near-matches: 'TSales', 'Alex2', 'Ale' and 'Taylor' are free",
          not any(r[k] for k in ("near1", "near2", "near3", "free")), r)


def section_block(br):
    print("\nB. a taken username is a stop: sign in, or choose a different name")
    for dev, w, h in cb.DEVICES:
        ctx, pg = booted(br, w, h)
        pg.evaluate("() => { %s }" % SETUP)
        r = pg.evaluate("""async () => {
          const out = {};
          try{
            __rows();
            showWelcomeNamePrompt(); await __wait(200);
            __type('T.Sale'); __go().click(); await __wait(400);
            const card = document.querySelector('.namecheck-card');
            out.stopped = !document.querySelector('.charselect-panel');
            out.shown = __vis(card);
            out.text = card ? card.innerText.replace(/\\s+/g, ' ') : '';
            out.title = (card && card.querySelector('.namecheck-title') || {}).textContent || '';
            const av = card && card.querySelector('.namecheck-avatar .rank-avatar');
            out.avatar = av ? av.dataset.char : null;
            out.avatarSvg = !!(av && av.querySelector('svg'));
            const btns = card ? [...card.querySelectorAll('button')].filter(__vis) : [];
            out.btns = btns.map(b => b.textContent.trim());
            out.firstPrimary = !!(btns[0] && !btns[0].classList.contains('ghost'));
            out.continueGone = !__vis(__go());
            const cr = card ? card.getBoundingClientRect() : null;
            out.inside = !!cr && cr.left >= -1 && cr.right <= innerWidth + 1;
            out.sideScroll = document.documentElement.scrollWidth > innerWidth + 1;
            /* a Continue reached anyway (a script, a stale tap) still stops */
            __go().click(); await __wait(400);
            out.stillStopped = !document.querySelector('.charselect-panel');
            /* "I'm a different person" does not go on */
            const other = card && card.querySelector('.namecheck-other');
            out.otherLabel = other ? other.textContent.trim() : null;
            if(other) other.click(); await __wait(300);
            out.afterOther = !document.querySelector('.charselect-panel') && !__vis(__go());
            out.otherText = card ? card.innerText.replace(/\\s+/g, ' ') : '';
            /* the same name spelled another way is still the same name */
            __type('T Sale'); await __wait(100);
            out.spaceGone = !__vis(__go());
            if(__go()) __go().click(); await __wait(400);
            out.spaceStopped = !document.querySelector('.charselect-panel');
            /* a free name goes on */
            __type('Taylor'); await __wait(100);
            out.freeShown = __vis(__go());
            out.cardGone = !__vis(card);
            __go().click(); await __wait(400);
            out.freeGoes = !!document.querySelector('.charselect-panel');
            out.name = store.firstName;
            /* and "That's me - sign in" opens the code screen */
            showWelcomeNamePrompt(); await __wait(200);
            __type('tsale'); __go().click(); await __wait(400);
            const si = document.querySelector('.namecheck-card .namecheck-signin');
            if(si) si.click(); await __wait(300);
            out.signInOpens = !!document.querySelector('.synccode-entry-panel');
          }catch(e){ out.err = String(e && e.stack || e); }
          return out; }""")
        ctx.close()
        check("%s: 'T.Sale' stops on the username screen with a card naming 'TSale already has a Nova account.'" % dev,
              not r.get("err") and r.get("stopped") and r.get("shown") and r.get("title") == "TSale already has a Nova account.", r)
        check("%s: the card shows the row's own character and its level, and fits the screen" % dev,
              r.get("avatar") == "alien" and r.get("avatarSvg") and "Level 24" in r.get("text", "")
              and r.get("inside") and not r.get("sideScroll"), r)
        check("%s: 'That’s me — sign in' comes first and is the primary button; 'I’m a different person' is second" % dev,
              r.get("btns", [])[:2] == ["That’s me — sign in", "I’m a different person"] and r.get("firstPrimary"), r)
        check("%s: Continue is gone while the name is taken, and a Continue tap anyway still does not go on" % dev,
              r.get("continueGone") and r.get("stillStopped"), r)
        check("%s: 'I’m a different person' does not go on: it says to change the name" % dev,
              r.get("afterOther") and "Change it to continue" in r.get("otherText", ""), r)
        check("%s: 'T Sale' is still taken; a free name ('Taylor') brings Continue back and goes on" % dev,
              r.get("spaceGone") and r.get("spaceStopped") and r.get("freeShown") and r.get("cardGone")
              and r.get("freeGoes") and r.get("name") == "Taylor", r)
        check("%s: 'That’s me — sign in' opens the code screen" % dev, r.get("signInOpens"), r)


def section_wait(br):
    print("\nC. a board not yet read is read before a name is let through")
    ctx, pg = booted(br, 440, 956)
    pg.evaluate("() => { %s }" % SETUP)
    r = pg.evaluate("""async () => {
      const out = {};
      try{
        leaderboardRows = []; boardFetchedAt = 0;
        window.fetchBoardForInvites = function(){ setTimeout(() => __rows(), 700); };
        showWelcomeNamePrompt(); await __wait(200);
        __type('t.sale'); __go().click(); await __wait(150);
        out.checking = (__go() || {}).textContent;
        await __wait(1500);
        out.stopped = !document.querySelector('.charselect-panel');
        out.card = __vis(document.querySelector('.namecheck-card'));
      }catch(e){ out.err = String(e && e.stack || e); }
      return out; }""")
    ctx.close()
    check("Continue waits for the board ('Checking…') and then stops on the taken name",
          not r.get("err") and r.get("stopped") and r.get("card"), r)


def section_copy(br):
    print("\nD. the logged-out screens say plainly what each choice is")
    for dev, w, h in cb.DEVICES:
        ctx, pg = booted(br, w, h)
        pg.evaluate("() => { %s }" % SETUP)
        r = pg.evaluate("""async () => {
          const out = {};
          try{
            const acts = document.querySelector('[data-screen="welcome"] .cosmic-welcome-actions');
            const kids = acts ? [...acts.children] : [];
            out.order = kids.map(k => k.tagName === 'BUTTON' ? 'B:' + k.textContent.trim() : 'P:' + k.textContent.trim());
            out.capsVisible = kids.filter(k => k.tagName === 'P').every(__vis);
            showSignUpCheck(); await __wait(300);
            const p = document.querySelector('.signupcheck-panel');
            out.check = p ? p.innerText.replace(/\\s+/g, ' ') : '';
            const lost = p && p.querySelector('.lostcode-line');
            out.checkLost = __vis(lost);
            const go = p && p.querySelector('.signupcheck-go');
            out.lostAboveGo = !!(lost && go && lost.getBoundingClientRect().bottom <= go.getBoundingClientRect().top + 1);
            showWelcomeCodeEntry(); await __wait(300);
            const c = document.querySelector('.synccode-entry-panel');
            out.code = c ? c.innerText.replace(/\\s+/g, ' ') : '';
            out.codeLost = __vis(c && c.querySelector('.lostcode-line'));
          }catch(e){ out.err = String(e && e.stack || e); }
          return out; }""")
        ctx.close()
        check("%s: Welcome reads Sign in, its line, I'm new here, its line - one line each, in that order" % dev,
              not r.get("err") and r.get("order") == [
                  "B:Sign in", "P:Already use Nova on another phone or before? Use your sync code.",
                  "B:I’m new here", "P:Never used Nova before."] and r.get("capsVisible"), r.get("order"))
        check("%s: the check says a second account splits your progress and puts you on the leaderboard twice" % dev,
              "second account splits your progress" in r.get("check", "") and "leaderboard twice" in r.get("check", ""),
              r.get("check"))
        check("%s: the check and the code screen both say 'Lost your code? Ask an admin for help.'" % dev,
              "Lost your code? Ask an admin for help." in r.get("check", "") and r.get("checkLost")
              and "Lost your code? Ask an admin for help." in r.get("code", "") and r.get("codeLost")
              and r.get("lostAboveGo"), r)


def section_public(br):
    print("\nE. nothing beyond the public rankings row")
    ctx, pg = booted(br, 440, 956)
    pg.evaluate("() => { %s }" % SETUP)
    r = pg.evaluate("""async () => {
      const out = { reads: [] };
      try{
        __rows();
        const real = fbDb;
        fbDb = { collection: name => { out.reads.push(name); return real.collection(name); } };
        showWelcomeNamePrompt(); await __wait(200);
        __type('T.Sale'); __go().click(); await __wait(400);
        const card = document.querySelector('.namecheck-card');
        out.text = card ? card.innerText.replace(/\\s+/g, ' ') : '';
        out.html = card ? card.innerHTML : '';
        fbDb = real;
      }catch(e){ out.err = String(e && e.stack || e); }
      return out; }""")
    ctx.close()
    t = r.get("text", "")
    # numbers in the text only (the drawing's own markup is full of them); words and the id anywhere
    leaks = [x for x in ("12345", "12,345", "77", "913") if x in t] + \
            [x for x in ("badge", "hundo", "XP", "tsaleaaaaaaa") if x in t or x in r.get("html", "")]
    check("the card shows the name, character and level and nothing else of that row (no XP, hundos, badges, id)",
          not r.get("err") and "Level 24" in t and not leaks, [leaks, t])
    check("no sync code is anywhere in the card", not re.search(r"[A-Z0-9]{4}-[A-Z0-9]{4}", r.get("html", "")), t)
    check("the name check reads no account document (no 'progress' read)", "progress" not in r.get("reads", []), r.get("reads"))


def section_rename(br):
    print("\nF. a rename may not take a name somebody else wears")
    ctx, pg = booted(br, 440, 956, seed=USED_ACCOUNT)
    pg.evaluate("() => { %s }" % SETUP)
    r = pg.evaluate("""async () => {
      const out = {};
      try{
        __rows();
        const before = store.firstName;
        showCustomize(); await __wait(500);
        const edit = document.querySelector('.customize-namerow .profile-edit-btn');
        edit.click(); await __wait(150);
        const inp = document.querySelector('#customize-name-input');
        const save = [...document.querySelectorAll('.customize-namebtns .next')].find(b => !b.classList.contains('ghost'));
        inp.value = 'T.Sale'; save.click(); await __wait(200);
        out.blocked = store.firstName === before;
        out.editorOpen = !document.querySelector('.customize-nameedit').hidden;
        inp.value = 'Jordan Q'; save.click(); await __wait(200);
        out.freeSaved = store.firstName === 'Jordan Q';
      }catch(e){ out.err = String(e && e.stack || e); }
      return out; }""")
    ctx.close()
    check("saving 'T.Sale' as your name keeps your old name and leaves the editor open; a free name saves",
          not r.get("err") and r.get("blocked") and r.get("editorOpen") and r.get("freeSaved"), r)


def main():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=cb.CHROME, args=["--no-sandbox"])
        only = os.environ.get("ONLY", "")
        for key, fn in (("key", section_key), ("block", section_block), ("wait", section_wait),
                        ("copy", section_copy), ("public", section_public), ("rename", section_rename)):
            if not only or key in only:
                fn(br)
        br.close()
    print("\n%d failure(s)" % len(FAILURES))
    for f in FAILURES:
        print("  - " + f)
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
