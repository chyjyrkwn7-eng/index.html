#!/usr/bin/env python3
"""Build 384 review: a person's card and your own profile, one look.

Madison: the default banner's stars leaked below where a banner's go; the flare on a person's card gave a Haptic Touch response (it is
a picture, not a control); tapping someone on the leaderboard faded in and out roughly (and vanished on close); the badges belong on
the line beside the level, so the card's fourth box goes; and your own profile says your rank the same way, flare and name.
(1) the card's level line reads "Level N · N badges", and the grid has three cells, none of them Badges, the first across both columns;
(2) the rank line takes no touch (pointer-events none, no callout, no selection);
(3) the default banner's stars all sit in the top 55% of the strip;
(4) closing: Close fades the card (is-leaving), then removes it; and the dim is a layer of its own faded by opacity;
(5) your own profile, ranked: the rank line (the flare and the name, in its colour) is the card's own, above "Level N · N badges".
  python3 tools/check-b384-card.py [--against OLD/index.html]   (must FAIL on the build before)"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
import importlib.util
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = cb.INSET_RE
    cb.patched = lambda ins: IR.sub(lambda m: {"top": "%dpx" % ins[0], "right": "%dpx" % ins[1], "bottom": "%dpx" % ins[2], "left": "%dpx" % ins[3]}[m.group(1)], OLD)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    ctx, pg = cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT, dpr=3)
    pg.evaluate("document.querySelectorAll('#splashscreen').forEach(n=>n.remove())")
    r = pg.evaluate("""async ()=>{ const w=ms=>new Promise(r=>setTimeout(r,ms));
      openPersonSheet({ pub:'bo0000000000', firstName:'Lev', avatarChar:'hacker', level:60, badges:7, hundos:78, xp:144000, correct:10563, banner:'' }); await w(1200);
      const out={}; out.level=(document.querySelector('.person-card-level')||{}).textContent;
      const cells=[...document.querySelectorAll('.person-card-cell')]; out.labels=cells.map(c=>(c.querySelector('.person-card-cell-label')||{}).textContent);
      out.firstWide = cells[0] && getComputedStyle(cells[0]).gridColumnStart === '1' && getComputedStyle(cells[0]).gridColumnEnd === '-1';
      const rk=document.querySelector('.person-card-rank'); const cs=rk&&getComputedStyle(rk); out.rank = rk && { pe:cs.pointerEvents, callout:cs.webkitTouchCallout||'', us:cs.userSelect||cs.webkitUserSelect };
      const bn=document.querySelector('.person-card-cover > .bnr-theme'); const bi = bn ? getComputedStyle(bn,'::before').backgroundImage : '';
      out.starYs=[...bi.matchAll(/at [\\d.]+% ([\\d.]+)%/g)].map(m=>+m[1]);
      const ov=document.querySelector('.invite-overlay'); out.dimLayer = getComputedStyle(ov,'::before').content;
      document.querySelector('.person-sheet-close').click(); await w(60); out.leaving = ov.classList.contains('is-leaving') && ov.isConnected; await w(450); out.gone = !ov.isConnected;
      return out; }""")
    chk("(1) level line reads 'Level 60 · 7 badges' (%r), three cells and no Badges (%s), the first across both columns (%s)" % (r["level"], r["labels"], r["firstWide"]),
        re.match(r"Level 60 · 7 badges$", r["level"] or "") and len(r["labels"]) == 3 and "Badges" not in r["labels"] and r["firstWide"], r)
    chk("(2) the rank line takes no touch: %s" % (r["rank"],), r["rank"] and r["rank"]["pe"] == "none" and r["rank"]["us"] == "none"   # (the touch callout is WebKit-only and Chromium does not report it), r)
    chk("(3) the default banner's stars all sit in the top 55%% of the strip (%s)" % (r["starYs"],), r["starYs"] and max(r["starYs"]) <= 55, r["starYs"])
    chk("(4) the dim is a layer of its own (%s); Close fades the card (is-leaving: %s) and then removes it (%s)" % (r["dimLayer"], r["leaving"], r["gone"]),
        r["dimLayer"] not in ("none", "normal", "") and r["leaving"] and r["gone"], r)
    o = pg.evaluate("""async ()=>{ const w=ms=>new Promise(r=>setTimeout(r,ms)); const R=TIER_UNLOCKS.vanguard; let xp=0; while(levelProgress(xp).level < R.level) xp+=25; store.lifetime.points=xp;
      store.unitPerfects={}; topicsIn(QUESTIONS).slice(0,R.badges).forEach(u=>store.unitPerfects[u]=BADGE_THRESHOLD); showProfile('profile'); await w(1500);
      const rl=document.querySelector('.pf-standing > .profile-rankline'); const lv=document.querySelector('.pf-standing .pf-idsub');
      return { has: !!rl, mark: !!(rl && rl.querySelector('.person-card-mark')), word: rl && (rl.querySelector('.person-card-rankword')||{}).textContent, color: rl && getComputedStyle(rl).color,
               above: !!(rl && lv && (rl.compareDocumentPosition(lv) & Node.DOCUMENT_POSITION_FOLLOWING)), sub: lv && lv.textContent }; }""")
    chk("(5) your own profile has the card's rank line (flare %s, name %r), above %r" % (o["mark"], o["word"], o["sub"]),
        o["has"] and o["mark"] and o["word"] and o["above"] and re.search(r"Level \d+\s*·\s*\d+ badges", o["sub"] or ""), o)
    br.close()
cb.SERVER.shutdown()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
