"""384.137 (unlocks4): what the unlocks walkthrough found, at three stages of an account, in both classes.

Asserted by shape and by numbers read off the page:
 (1) NEXT UP STARTS ON A TRACK. A new account (every share 0): no Feat is among Customize's Next up rows, the Unlocks screen's
     "closest" row or Profile's Customize row, while a track's first tier is still to earn at the same share; in any state, a Feat
     never comes before a track tier with the same share (unlockNextUp's order, read in the page).
 (2) NEXT UP SAYS HOW MANY IT LISTS: with three rows its note names three; with fewer (a near-complete Fire Code account whose
     only Feat is held) the note does not say three, and names the number of rows there are.
 (3) FIRE CODE'S COMPLETIONIST IS ON ALL's CAPSTONES CARD (the academy's is not, it has none): its row's tick / bar is
     completionistProgress()'s have / need and its held state bannerEarned's; its row's rule carries no count (the bar says it).
 (4) COMPLETIONIST'S CARD: locked, the "To unlock" line is the rule with no number in it, and the bar's numbers are the progress.
 (5) YOUR OWN LEADERBOARD ROW WEARS THE BANNER THIS DEVICE WEARS: with the account push held (nothing written), a banner
     changed on this device shows on your own row at once and on the card the row opens; the published copy still
     says the old ones (drawing only); everybody else's row is their published banner.

  python3 tools/check-b384-unlocks4.py [--against OLD/index.html] [--only 1,2,3,4,5]
--against must FAIL (none of this is there before)."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
G = os.path.join(HERE, "check-b384-unlocks.py")
sys_argv = sys.argv[:]
sys.argv = [G]
h = {"__file__": G, "__name__": "gate4"}
exec(open(G).read().split("\n# ---- the gate ----")[0], h)
sys.argv = sys_argv
from playwright.sync_api import sync_playwright

def arg(n): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else None
AGAINST = arg("--against")
ONLY = set((arg("--only") or "").split(",")) - {""}
def wanted(n): return not ONLY or str(n) in ONLY
SRC = AGAINST or os.path.join(h["ROOT"], "index.html")
text = open(SRC, encoding="utf-8").read()
fx = h["fixtures"]()

fails = []; passes = 0
def chk(name, ok, detail=None):
    global passes
    if ok: passes += 1; print("PASS", name, flush=True)
    else: fails.append(name); print("FAIL", name, "--", json.dumps(detail)[:600] if detail is not None else "", flush=True)

def new_seed(cls):
    a = h["account"](ifc=(cls == "ifc"))
    a.update({"lifetime": {"points": 0, "answered": 0, "correct": 0, "perfectTests": 0, "currentStreak": 0, "longestStreak": 0},
              "unitPerfects": {}, "testHistory": [], "studyLog": {}, "vrWins": 0, "vrMatches": 0, "banner": "", "avatarChar": "ghost"})
    if cls == "academy":
        return ({"progress": {h["CODE"]: a}, "leaderboard": h["mate_rows"]()}, h["init_js"](a))
    a2 = dict(h["account"](), classes=["academy", "ifc"])
    seed = {"progress": {h["CODE"]: a2, h["CODE"] + "__ifc": a}, "leaderboard": {},
            "vrooms": {"lb-ifc-v1": {"kind": "board", "cls": "ifc", "rows": dict(list(h["mate_rows"]("unifcm").items())[:8])}}}
    return (seed, h["init_js"](a2, a))

# nearly everything (the shot tool's "near" stage): every badge, years of study, every Feat; short of the 10th room win
NEAR = r"""()=>{ const day = n => { const d = new Date(); d.setDate(d.getDate() - n); return d.toISOString().slice(0, 10); };
  const s = store; const up = {}; classTopics().forEach(u => { up[u] = badgeThresholdFor(u) + 2; }); s.unitPerfects = up;
  s.lifetime = Object.assign({}, s.lifetime, { points: 70000, answered: 14000, correct: 12000, perfectTests: 260, longestStreak: 320, currentStreak: 40, fullTests: 600 });
  const log = {}; for(let i = 1; i <= 80; i++) log[day(i)] = 3600000; s.studyLog = log;
  Object.assign(s, { dailyCorrectTotal: 40, hundoDayBest: 4, vrWins: 9, vrMatches: 40, vrHosted: 10, friendsBest: 8, novaBeaten: true, bigTest500Passed: true,
    weeklyTop3: 3, weeklyWins: 1, lateHundos: 4, bestTestStreak: 320, unitHundoStreakBest: 12, practiceExamPerfect: true });
  try{ unlockTrackMemo = null; }catch(e){} saveStore(); return true; }"""

READ_NEXT = r"""async ()=>{ const W = ms => new Promise(r => setTimeout(r, ms)); const out = {};
  const list = unlockNextUp(unlockTrackView(), 99);
  out.order = list.map(e => ({ feat: e.track === 'feat', frac: e.frac, first: !!e.first }));
  out.trackAtTop = list.length ? Math.max(...list.filter(e => e.track !== 'feat').map(e => e.frac).concat([-1])) : -1;
  out.featAtTop = list.length ? Math.max(...list.filter(e => e.track === 'feat').map(e => e.frac).concat([-1])) : -1;
  document.querySelectorAll('.invite-overlay').forEach(o => o.remove());
  showCustomize(); await W(900);
  const nu = document.querySelector('.trk-nextup');
  const rows = nu ? [...nu.querySelectorAll('.trk-tier')] : [];
  out.rows = rows.length;
  out.rowStars = rows.map(r => !!r.querySelector('.trk-num.is-star'));
  const note = nu && nu.querySelector('.cz-group-note, .cz-group-sub, .cz-group-head p, .cz-group-head span:not(.cz-group-count):not(.cz-group-title)');
  out.note = nu ? ([...nu.querySelectorAll('.cz-group-head *')].map(x => x.children.length ? '' : x.textContent).filter(Boolean)) : [];
  showUnlockTracks(); await W(900);
  const cl = document.querySelector('.ulk-closest');
  out.closestStar = !!(cl && (cl.querySelector('.trk-num.is-blank') || cl.querySelector('.trk-num.is-star')));
  out.closestFeat = !!(list[0] && list[0].track === 'feat');
  showProfile('profile'); await W(1200);
  out.profileNext = (unlockNextUp(null, 1)[0] || {}).track || null;
  return out; }"""

CAPS = r"""async ()=>{ const W = ms => new Promise(r => setTimeout(r, ms)); const out = {};
  document.querySelectorAll('.invite-overlay').forEach(o => o.remove());
  showUnlockTracks(); await W(900);
  const caps = document.querySelector('.cz-group-trk-caps');
  const rows = caps ? [...caps.querySelectorAll('.trk-tier')] : [];
  out.names = rows.map(r => (r.querySelector('.trk-name') || {}).textContent || '');
  const hasC = typeof COMPLETIONIST_ID !== 'undefined' && !!bannerDef(COMPLETIONIST_ID);
  out.hasC = hasC;
  if(hasC){
    const p = completionistProgress(), held = bannerEarned(COMPLETIONIST_ID), name = bannerDef(COMPLETIONIST_ID).name;
    const r = rows.find(x => ((x.querySelector('.trk-name') || {}).textContent || '') === name);
    out.row = !!r;
    if(r){ const f = r.querySelector('.trk-bar > i'); out.fill = f ? parseFloat(f.style.width) : null; out.want = held ? 100 : Math.round(p.have / p.need * 1000) / 10;
      out.count = (r.querySelector('.trk-count') || {}).textContent || ''; out.wantCount = held ? '' : p.have.toLocaleString() + ' / ' + p.need.toLocaleString();
      out.held = r.classList.contains('is-held'); out.wantHeld = held; out.goal = (r.querySelector('.trk-goal') || {}).textContent || ''; }
    /* the card */
    r && r.click(); await W(700);
    const c = document.querySelector('.unlock-card');
    out.desc = c ? ((c.querySelector('.unlock-card-desc') || {}).textContent || '') : null;
    out.cardCount = c ? ((c.querySelector('.unlock-card-count') || {}).textContent || '') : null;
    out.cardWant = held ? null : p.have + ' of ' + p.need;
    document.querySelectorAll('.invite-overlay').forEach(o => o.remove());
  }
  return out; }"""

OWN = r"""async ()=>{ const W = ms => new Promise(r => setTimeout(r, ms)); const out = {};
  const board = () => window.NOVA_CLASS === 'ifc' ? (classBoardRows || []) : (leaderboardRows || []);
  const pub = store.publicId;
  const held = BANNERS.filter(b => bannerEarned(b.id)).map(b => b.id);
  const cur = wornBanner() || '';
  const pick = held.find(id => id !== cur && !!bannerRowStillURL(id));
  const chars = ['ghost', 'bear', 'alien'].filter(c => !isLockedCharacter(c));
  const nowChar = store.avatarChar || 'ghost';
  const newChar = chars.find(c => c !== nowChar) || nowChar;
  out.pick = pick; out.newChar = newChar;
  const keep = window.scheduleCloudPush; window.scheduleCloudPush = () => {};
  try{ clearTimeout(cloudPushTimer); cloudPushTimer = null; }catch(e){}
  const n0 = (window.__payloads || []).length;
  store.banner = pick; store.avatarChar = newChar; saveStore();
  document.querySelectorAll('.invite-overlay').forEach(o => o.remove());
  showRankings(); await W(1800);
  const me = document.querySelector('.screen-rankings .rank-row[data-me="1"]');
  out.meRow = !!me;
  if(me){
    const bw = me.querySelector('.lb-row-bnr');
    out.rowBanner = bw ? (bw.dataset.key || '').split('|').pop() : '';
    out.rowChar = me.dataset.av || '';
    me.classList.remove('is-offscreen'); me.click(); await W(900);
    const card = document.querySelector('.person-card');
    const cov = card && card.querySelector('.bnr');
    out.cardBanner = cov ? ([...cov.classList].find(c => /^bnr-/.test(c) && c !== 'bnr-' ) || '').replace(/^bnr-/, '') : '';
    document.querySelectorAll('.invite-overlay, .person-sheet-overlay').forEach(o => o.remove());
  }
  const e = board().find(x => x.pub === pub);
  out.published = e ? { banner: e.banner || '', av: e.avatarChar || '' } : null;
  /* everybody else: their own published banner */
  out.others = [...document.querySelectorAll('.screen-rankings .rank-row:not([data-me="1"])')].map(r => {
    const row = board().find(x => x.pub === r.dataset.pub); const bw = r.querySelector('.lb-row-bnr');
    return { want: row && row.banner && bannerDef(row.banner) ? row.banner : '', got: bw ? (bw.dataset.key || '').split('|').pop() : '' }; });
  /* the account and the board rows (the presence heartbeat runs on its own clock and is not about this) */
  out.writeList = (window.__payloads || []).slice(n0).filter(x => /^(progress|leaderboard)\/|^vrooms\/lb-ifc/.test(x)).map(x => x.slice(0, 80));
  out.writes = out.writeList.length;
  window.scheduleCloudPush = keep;
  return out; }"""

with sync_playwright() as p:
    br = p.chromium.launch(executable_path=h["g"]["CHROME"], args=["--no-sandbox"])
    for cls in ("academy", "ifc"):
        def open_page(seed_init):
            ctx, pg, errs = h["page"](br, text, seed_init[0], seed_init[1])
            pg.wait_for_timeout(1500); h["quiet"](pg); h["load_board"](pg); h["quiet"](pg)
            return ctx, pg, errs
        if wanted(1) or wanted(2):
            ctx, pg, errs = open_page(new_seed(cls))
            n = pg.evaluate(READ_NEXT)
            if wanted(1):
                chk("[%s] (1) a new account: every share is 0 and a track's first tier is to earn" % cls, n["trackAtTop"] == 0 and n["featAtTop"] in (0, -1), n)
                chk("[%s] (1) a new account: no Feat in Customize's Next up rows (%s)" % (cls, n["rowStars"]), n["rows"] >= 1 and not any(n["rowStars"]), n)
                chk("[%s] (1) a new account: the Unlocks screen's closest and Profile's Next are a track's tier" % cls, not n["closestFeat"] and not n["closestStar"] and n["profileNext"] not in (None, "feat"), n)
                bad = [i for i in range(1, len(n["order"])) if n["order"][i - 1]["feat"] and not n["order"][i]["feat"] and abs(n["order"][i - 1]["frac"] - n["order"][i]["frac"]) < 1e-9]
                chk("[%s] (1) a new account: no Feat before a track tier of the same share (%d in order)" % (cls, len(n["order"])), not bad, n["order"][:8])
            if wanted(2):
                chk("[%s] (2) three rows, a note that names three (%s)" % (cls, n["note"]), n["rows"] == 3 and any("three" in x for x in n["note"]), n)
            ctx.close()
        if wanted(1) or wanted(2) or wanted(3) or wanted(4):
            ctx, pg, errs = open_page(fx["rich_" + cls])
            if wanted(1):
                n = pg.evaluate(READ_NEXT)
                bad = [i for i in range(1, len(n["order"])) if n["order"][i - 1]["feat"] and not n["order"][i]["feat"] and abs(n["order"][i - 1]["frac"] - n["order"][i]["frac"]) < 1e-9]
                chk("[%s] (1) mid account: no Feat before a track tier of the same share" % cls, not bad, n["order"][:10])
            if wanted(3) or wanted(4):
                c = pg.evaluate(CAPS)
                if cls == "academy":
                    chk("[academy] (3) the capstones card has no Completionist (the academy has none)", not c["hasC"] and "Completionist" not in c["names"], c)
                else:
                    if wanted(3):
                        chk("[ifc] (3) Completionist has a row on All's capstones card (%s)" % c["names"], c.get("row") is True, c)
                        chk("[ifc] (3) its bar and count are completionistProgress's (%s ~ %s, '%s')" % (c.get("fill"), c.get("want"), c.get("count")),
                            c.get("fill") is not None and abs(c["fill"] - c["want"]) < .2 and c.get("count") == c.get("wantCount") and c.get("held") == c.get("wantHeld"), c)
                        chk("[ifc] (3) its rule says no count ('%s')" % c.get("goal"), bool(c.get("goal")) and not any(ch.isdigit() for ch in c["goal"]), c)
                    if wanted(4):
                        chk("[ifc] (4) the card's To unlock is the rule, with no number ('%s')" % c.get("desc"), bool(c.get("desc")) and not any(ch.isdigit() for ch in c["desc"]), c)
                        chk("[ifc] (4) the card's count is the progress ('%s')" % c.get("cardCount"), c.get("cardCount") == c.get("cardWant"), c)
            ctx.close()
        if wanted(2) and cls == "ifc":
            ctx, pg, errs = open_page(fx["rich_" + cls])
            pg.evaluate(NEAR); h["quiet"](pg)
            n = pg.evaluate(READ_NEXT)
            words = {1: "closest unlock", 2: "two", 3: "three"}
            chk("[ifc] (2) near the end, fewer rows (%d) than three, and the note says so (%s)" % (n["rows"], n["note"]),
                1 <= n["rows"] < 3 and not any("three" in x for x in n["note"]) and any(words[n["rows"]] in x for x in n["note"]), n)
            ctx.close()
        if wanted(5):
            ctx, pg, errs = open_page(fx["rich_" + cls])
            o = pg.evaluate(OWN)
            chk("[%s] (5) a held banner to change to, and a starter (%s, %s)" % (cls, o.get("pick"), o.get("newChar")), bool(o.get("pick")) and o.get("meRow"), o)
            chk("[%s] (5) your own row wears the banner at once (%s)" % (cls, o.get("rowBanner")), o.get("rowBanner") == o.get("pick"), o)
            chk("[%s] (5) the card your row opens wears it (%s)" % (cls, o.get("cardBanner")), o.get("cardBanner") == o.get("pick"), o)
            chk("[%s] (5) drawing only: nothing written, the published row still the old one" % cls,
                o.get("writes") == 0 and o.get("published") is not None and o["published"]["banner"] != o.get("pick"), o)
            chk("[%s] (5) everybody else's row is their published banner (%d rows)" % (cls, len(o.get("others") or [])),
                len(o.get("others") or []) >= 3 and all(x["want"] == x["got"] for x in o["others"]), o.get("others"))
            chk("[%s] (5) no page errors" % cls, not errs, errs)
            ctx.close()
    br.close()
print("\n%s - %d pass, %d fail" % ("ALL PASS" if not fails else "FAILURES", passes, len(fails)))
sys.exit(1 if fails else 0)
