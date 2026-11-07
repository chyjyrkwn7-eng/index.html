"""Build 384: the rank ladder's colours, one rule; no flare bobbing.
Madison, on Gold's card while unranked: "The flare shouldn't be moving up and down. The theme unlock looks bad (that's all of
them). Why can't I see the color of the flare in the unlocks, why is the big flare so dark without its color. ... I'm not sure if
we should make it where when you click any of the ranks you can see the colors of stuff, or just the ones you have unlocked and
your next rank? Idk make it the best and make it consistent and make it make sense."
The rule (Customize's: dim in the list, shown as it is when opened): the road map's list colours what you have and the rank you
are working towards and dims the ranks past it; OPENING any rank shows it as it really is, a padlock on what isn't yours.
iPhone 17 Pro Max (440x956), an unranked account at level 2, all read off the page:
(1) a rank two past the next one (Gold): its card's big emblem at full opacity, no filter, nothing laid over it, a padlock on the
    circle, its name drawn as a reached rank's is (no locked grey of its own);
(2) its unlocks: the theme is its swatch (the swirl, Customize's), the flare lit, a padlock on every chip;
(3) the next rank's card (Bronze): the same - in colour, padlocks, "Up next"; a reached rank's card: no padlocks anywhere;
(4) the road map: every stop's theme is its swatch; the next stop's swatch and flare in colour (opacity 1, no filter), every stop
    past it dim (opacity under .5);
(5) still: the flare chip on a rank's card, Profile's reward tiles' flare and its To-reach emblem don't move up or down (their box
    tops sampled over 2.2s vary under .25px);
(6) no page errors.
Run:  python3 tools/check-b384-ranks.py   (--against OLD/index.html must FAIL)"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b382-savecode.py")).read().split("\nwith sync_playwright() as pw:")[0]
g = {"__file__": os.path.join(HERE, "check-b382-savecode.py"), "__name__": "b384rk"}
exec(src, g)
from playwright.sync_api import sync_playwright
fails = g["fails"] = []
ck = g["ck"]
CARD = """(k)=>{ document.querySelectorAll('.invite-overlay').forEach(o=>o.remove()); showRankLore(k); }"""
READ = """()=>{ const c=document.querySelector('.ranklore-card'); if(!c) return null; const svg=c.querySelector('.ranklore-art svg'), art=c.querySelector('.ranklore-art');
  const af=getComputedStyle(art,'::after'); const nm=c.querySelector('.ranklore-name');
  const chips=[...c.querySelectorAll('.rankmap-gift')];
  return { cls: c.className, state: (c.querySelector('.ranklore-state')||{}).textContent, op: svg ? +getComputedStyle(svg).opacity : 0, filter: svg ? getComputedStyle(svg).filter : null,
    over: af.content !== 'none' && af.backgroundImage !== 'none', lock: !!art.querySelector('.ranklore-lock'), name: getComputedStyle(nm).color, rank: getComputedStyle(c).getPropertyValue('--rank-color').trim(),
    chips: chips.map(g=>({ cls: g.className, swatch: !!g.querySelector('.swatch .dot'), lit: g.querySelector('.flare-solo') ? g.querySelector('.flare-solo').classList.contains('cosmic-badge-lit') : null,
                           lock: !!g.querySelector('.rankmap-giftlock') })) }; }"""
STILL = """async (sels)=>{ const els=sels.map(s=>document.querySelector(s)); const tops=els.map(()=>[]);
  for(let i=0;i<23;i++){ els.forEach((e,j)=>{ if(e) tops[j].push(e.getBoundingClientRect().top); }); await new Promise(r=>setTimeout(r,100)); }
  return sels.map((s,j)=>({ sel: s, found: !!els[j], swing: tops[j].length ? Math.max(...tops[j]) - Math.min(...tops[j]) : null })); }"""
def grey(c):
    import re
    v = [float(x) for x in re.findall(r"[\d.]+", c or "")[:3]]
    if (c or "").startswith("color("): v = [x * 255 for x in v]
    return len(v) == 3 and max(v) - min(v) < 12
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    errs = []
    ctx, pg = g["open_page"](br, g["init_account"]("", g["store"]()), errs=errs)
    info = pg.evaluate("()=>({ order: TIER_ORDER_FULL, held: rankOf(store) })")
    order = info["order"]; hi = order.index(info["held"]) if info["held"] in order else -1
    nxt, far = order[hi + 1], order[hi + 3]
    pg.evaluate("()=>{ showRanksScreen('ranks'); }"); pg.wait_for_timeout(1600)
    # (4) the road map
    stops = pg.evaluate("""()=>[...document.querySelectorAll('#stage .rankmap-stop')].map(s=>{ const g=s.querySelector('.rankmap-gift.is-theme'); const d=g && g.querySelector('.swatch .dot');
      const fl=s.querySelector('.rankmap-giftbubble .flare-solo');
      return { cls: s.className, swatch: !!d, op: d ? +getComputedStyle(d).opacity : null, filter: d ? getComputedStyle(d).filter : null,
               flOp: fl ? +getComputedStyle(fl).opacity : null, flFilter: fl ? getComputedStyle(fl).filter : null }; })""")
    nx = [s for s in stops if "is-next" in s["cls"]]
    past = [s for s in stops if "is-next" not in s["cls"] and "is-reached" not in s["cls"]]
    ok4 = stops and all(s["swatch"] for s in stops) and nx and nx[0]["op"] == 1 and nx[0]["filter"] == "none" and nx[0]["flOp"] == 1 and nx[0]["flFilter"] == "none" \
          and past and all(s["op"] is not None and s["op"] < .5 for s in past)
    ck("(4) the road map: every theme a swatch (%d/%d), the next stop in colour (%s), every stop past it dim (%s)" % (sum(s["swatch"] for s in stops), len(stops), nx[:1], [s["op"] for s in past]),
       ok4, stops[:3])
    # a reached rank's name, for (1): the same card with its rank held
    pg.evaluate("(k)=>{ window.__rankOf = rankOf; rankOf = () => k; }", order[0]); pg.evaluate(CARD, order[0]); pg.wait_for_timeout(900)
    NAME_REACHED = [pg.evaluate("()=>getComputedStyle(document.querySelector('.ranklore-card .ranklore-name')).color")]
    pg.evaluate("()=>{ rankOf = window.__rankOf; document.querySelectorAll('.invite-overlay').forEach(o=>o.remove()); }")
    # (1)(2) a rank two past the next
    pg.evaluate(CARD, far); pg.wait_for_timeout(1500)
    r1 = pg.evaluate(READ)
    ck("(1) %s's card (past the next): the emblem at full opacity (%s), no filter (%s), nothing over it (%s), a padlock on the circle (%s), the name as a reached rank's (%s)"
       % (far, r1 and r1["op"], r1 and r1["filter"], r1 and r1["over"], r1 and r1["lock"], r1 and r1["name"]),
       r1 and r1["op"] >= .99 and r1["filter"] == "none" and not r1["over"] and r1["lock"] and r1["name"] == NAME_REACHED[0], r1)
    ck("(2) its unlocks: the theme its swatch, the flare lit, a padlock on every chip (%s)" % (r1 and [(c["swatch"], c["lit"], c["lock"]) for c in r1["chips"]],),
       r1 and r1["chips"] and any(c["swatch"] for c in r1["chips"]) and all(c["lit"] is not False for c in r1["chips"]) and any(c["lit"] for c in r1["chips"]) and all(c["lock"] for c in r1["chips"]), r1)
    # (5) the card's flare chip is still
    s5a = pg.evaluate(STILL, [".ranklore-card .rankmap-giftbubble .flare-solo"])
    # (3) the next rank's card; a reached rank's card
    pg.evaluate(CARD, nxt); pg.wait_for_timeout(1500)
    r3 = pg.evaluate(READ)
    pg.evaluate("(k)=>{ window.__rk = k; rankOf = () => k; tierColorUnlocked = t => TIER_ORDER_FULL.indexOf(t) <= TIER_ORDER_FULL.indexOf(k); }", order[0])
    pg.evaluate(CARD, order[0]); pg.wait_for_timeout(1500)
    r3b = pg.evaluate(READ)
    ck("(3) the next rank's card (%s): in colour with padlocks, '%s'; a reached rank's card: no padlocks (%s)" % (nxt, r3 and r3["state"], r3b and [c["lock"] for c in r3b["chips"]]),
       r3 and r3["op"] >= .99 and r3["lock"] and all(c["lock"] for c in r3["chips"]) and any(c["lit"] for c in r3["chips"])
       and r3b and not r3b["lock"] and not any(c["lock"] for c in r3b["chips"]) and "is-reached" in r3b["cls"], [r3, r3b])
    pg.evaluate("()=>document.querySelectorAll('.invite-overlay').forEach(o=>o.remove())")
    ctx.close()
    # (5) Profile: the reward tiles' flare and the To-reach emblem
    ctx, pg = g["open_page"](br, g["init_account"]("", g["store"]()), errs=errs)
    pg.evaluate("()=>{ showProfile('profile'); }"); pg.wait_for_timeout(1500)
    pg.evaluate("()=>{ const e=document.querySelector('#stage .pf-goal'); e && e.scrollIntoView({ block: 'center' }); }"); pg.wait_for_timeout(800)
    s5b = pg.evaluate(STILL, ["#stage .pf-rw .flare-solo", "#stage .pf-goal .pf-goal-emb > svg"])
    s5 = s5a + s5b
    ck("(5) no flare moves up or down: %s" % [(x["sel"].split(" ")[-1], x["found"], x["swing"] if x["swing"] is None else round(x["swing"], 2)) for x in s5],
       all(x["found"] and x["swing"] is not None and x["swing"] < .25 for x in s5), s5)
    ck("(6) no page errors", not errs, errs[:3])
    br.close()
print("\nALL PASS" if not fails else "\nFAILED: %d" % len(fails))
sys.exit(1 if fails else 0)
