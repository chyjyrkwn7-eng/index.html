"""Every unlock screen, at three stages of an account, in both classes (the 384.137 unlocks walkthrough for Madison).

  python3 tools/shoot-b384-unlockall.py OUTDIR [--src index.html] [--only academy|ifc] [--dev pm|ipad] [--stage new|mid|near]
         [--list]   (print what each stage holds and what it does not, and shoot nothing)

Stages (made-up accounts on the in-memory Firestore of check-b384-unlocks.py, its made-up classmates on the board):
  new  - a sign-up from today: nothing earned, the starters and the defaults only;
  mid  - check-b384-unlocks.py's rich fixture (some tiers of every track, a few Feats);
  near - nearly everything: every badge, years of study; still short of a few (Zeus, the top weekly board, the 10th Virtual
         Room win, Fire Code's Completionist); at its end the rest is handed over so the unlock moment of the class's biggest
         banner (Full Case / Completionist) plays on Home, and it is worn on Profile and the Leaderboard.
Phone: iPhone 17 Pro Max 440x956 @2x; tablet: iPad Pro 11" 834x1194 @2x (the tablet shoots the mid stage's main screens).
Files: OUTDIR/<cls>-<dev>-<stage>-NN-<name>.png. A step whose screen is not there prints "skip"."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
G = os.path.join(HERE, "check-b384-unlocks.py")
sys_argv = sys.argv[:]
sys.argv = [G]
h = {"__file__": G, "__name__": "shoot"}
exec(open(G).read().split("\n# ---- the gate ----")[0], h)
sys.argv = sys_argv
from playwright.sync_api import sync_playwright

OUT = sys.argv[1]
def arg(n): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else None
SRC = arg("--src") or os.path.join(h["ROOT"], "index.html")
ONLY = arg("--only"); DEV = arg("--dev"); STAGE = arg("--stage"); LIST = "--list" in sys.argv
os.makedirs(OUT, exist_ok=True)
text = open(SRC, encoding="utf-8").read()
fx = h["fixtures"]()

def new_store(ifc=False):
    a = h["account"](ifc=ifc)
    a.update({"lifetime": {"points": 0, "answered": 0, "correct": 0, "perfectTests": 0, "currentStreak": 0, "longestStreak": 0},
              "unitPerfects": {}, "testHistory": [], "studyLog": {}, "vrWins": 0, "vrMatches": 0, "banner": "", "avatarChar": "ghost",
              "rim": ""})
    return a

def seeds(stage, cls):
    if stage != "new":
        return fx["rich_" + cls]
    if cls == "academy":
        s = new_store()
        return ({"progress": {h["CODE"]: s}, "leaderboard": h["mate_rows"]()}, h["init_js"](s))
    a2 = dict(h["account"](), classes=["academy", "ifc"])
    s = new_store(ifc=True)
    seed = {"progress": {h["CODE"]: a2, h["CODE"] + "__ifc": s}, "leaderboard": {},
            "vrooms": {"lb-ifc-v1": {"kind": "board", "cls": "ifc", "rows": dict(list(h["mate_rows"]("unifcm").items())[:8])}}}
    return (seed, h["init_js"](a2, s))

# NEARLY EVERYTHING, on the counters the app keeps (nothing forced): `all` hands over what "near" holds back
NEAR = r"""(all)=>{ const day = n => { const d = new Date(); d.setDate(d.getDate() - n); return d.toISOString().slice(0, 10); };
  const s = store, ifc = window.NOVA_CLASS === 'ifc';
  const up = {}; classTopics().forEach(u => { up[u] = badgeThresholdFor(u) + 2; }); s.unitPerfects = up;
  s.lifetime = Object.assign({}, s.lifetime, { points: all ? 400000 : (ifc ? 70000 : 150000), answered: 14000, correct: 12000, perfectTests: 260,
    longestStreak: 320, currentStreak: 40, fullTests: 600, drillPlays: 200, examPlays: 120 });
  const log = {}; for(let i = 1; i <= 80; i++) log[day(i)] = 3600000; s.studyLog = log;
  Object.assign(s, { dailyCorrectTotal: 40, hundoDayBest: 4, vrWins: all ? 10 : 9, vrMatches: 40, vrHosted: 10, friendsBest: 8, novaBeaten: true,
    bigTest500Passed: true, retakenQuestions: 160, weeklyTop3: 3, weeklyWins: all ? 1 : 0, lateHundos: 4, bestTestStreak: 320,
    unitHundoStreakBest: 12, practiceExamPerfect: true });
  const m = Object.assign({}, s.mysteryColorsFound || {});
  (typeof MYSTERY_ORDER !== 'undefined' ? MYSTERY_ORDER : []).forEach((k, i) => { if(all || i < MYSTERY_ORDER.length - 2) m[k] = Date.now() - 86400000; });
  s.mysteryColorsFound = m;
  if(all){   /* the Masked One / Smoke Diver: 120 different questions missed and answered again */
    const ks = [...(retakeKeySet() || [])].slice(0, 120), st = Object.assign({}, s.stats || {});
    ks.forEach(k => { st[k] = Object.assign({ c: 3 }, st[k] || {}, { m: 2 }); });
    s.stats = st; s.retakenKeys = ks; s.retakenQuestions = 120; }
  try{ unlockTrackMemo = null; }catch(e){}
  saveStore();
  const lockedC = AVATAR_CHARACTERS.filter(c => !c.retired && !c.legacy && isLockedCharacter(c.id)).map(c => c.id);
  const lockedB = BANNERS.filter(b => !bannerEarned(b.id)).map(b => b.id);
  const lockedT = ACCENTS.filter(a => isLockedAccent(a));
  const lockedF = HUNDO_FX.filter(x => !hundoFxEarned(x.id)).map(x => x.id);
  let comp = null; try{ comp = ifc ? completionistProgress() : null; }catch(e){}
  let ult = null; try{ ult = ultimateProgress(); }catch(e){}
  return { rank: rankOf(s), level: levelOf(s), badges: badgeCountOf(s), lockedC, lockedB, lockedT, lockedF,
           comp: comp && { have: comp.have, need: comp.need }, ult: ult && { have: ult.have, need: ult.need } }; }"""

CLOSE = "document.querySelectorAll('.invite-overlay, .rs-spot, .person-sheet-overlay').forEach(o => o.remove())"
TOP = "window.scrollTo(0, 0)"
def scroll_to(sel, off=110):
    return "return (()=>{ const c = document.querySelector(%s); if(!c) return false; window.scrollTo(0, c.getBoundingClientRect().top + scrollY - %d); return true; })()" % (json.dumps(sel), off)
def chip(k):
    return "return (()=>{ const b = document.querySelector('.ulk-chip[data-filter=\"%s\"]'); if(!b) return false; b.click(); window.scrollTo(0, 0); return true; })()" % k
def card(js):
    return CLOSE + "; return (()=>{ " + js + " })()"
PAGES = [
    ("customize", CLOSE + "; showCustomize(); " + TOP + "; return true;", 1800),
    ("customize-look", scroll_to(".cz-list", 120), 900),
    ("character-page", CLOSE + "; showCustomize('character'); return true;", 2200),
    ("character-page-challenges", scroll_to(".cz-group-chars-2", 90), 1200),
    ("character-page-secrets", scroll_to(".cz-group-chars-3", 90), 1200),
    ("banner-page", CLOSE + "; showCustomize('banner'); return true;", 2400),
    ("banner-page-challenges", scroll_to(".cz-group-banner-challenge", 90), 1500),
    ("banner-page-end", "window.scrollTo(0, document.documentElement.scrollHeight); return true;", 1500),
    ("theme-page", CLOSE + "; showCustomize('theme'); return true;", 1500),
    ("fx-page", CLOSE + "; showCustomize('fx'); return true;", 1800),
    ("unlocks-top", CLOSE + "; showUnlockTracks(); " + TOP + "; return true;", 2200),
    ("unlocks-hundos-study", scroll_to('.trk-card[data-track="hun"]'), 1200),
    ("unlocks-answers-vr", scroll_to('.trk-card[data-track="ans"]'), 1200),
    ("unlocks-vr-feats", scroll_to('.trk-card[data-track="vr"]'), 1200),
    ("unlocks-feats-capstones", scroll_to(".cz-group-trk-feats", 140), 1200),
    ("unlocks-characters", chip("char"), 2200),
    ("unlocks-characters-2", "window.scrollTo(0, 900); return true;", 1500),
    ("unlocks-characters-3", "window.scrollTo(0, 1800); return true;", 1500),
    ("unlocks-banners", chip("banner"), 2400),
    ("unlocks-banners-2", "window.scrollTo(0, 1000); return true;", 1800),
    ("unlocks-banners-3", "window.scrollTo(0, 2000); return true;", 1800),
    ("unlocks-themes", chip("theme"), 1600),
    ("unlocks-effects", chip("fx"), 1800),
]
CARDS = [
    ("card-locked-character", card("const id = (AVATAR_CHARACTERS.find(c => c.feat && !c.secret && !c.retired && isLockedCharacter(c.id)) || {}).id; if(!id) return false; showUnlockDetail(characterDetail(id)); return true;"), 2000),
    ("card-locked-banner", card("const d = BANNERS.find(b => !b.rank && !b.flareChar && !b.ultimate && !b.completionist && !bannerEarned(b.id) && b.have() > 0); if(!d) return false; showUnlockDetail(bannerDetail(d.id)); return true;"), 2200),
    ("card-rank-reward", card("const id = (AVATAR_CHARACTERS.find(c => c.unlock && !c.feat && isLockedCharacter(c.id)) || {}).id; if(!id) return false; showUnlockDetail(characterDetail(id)); return true;"), 1800),
    ("card-locked-theme", card("const a = ACCENTS.find(n => isLockedAccent(n)); if(!a) return false; showUnlockDetail(themeDetail(a)); return true;"), 1600),
    ("card-locked-fx", card("const d = HUNDO_FX.find(x => x.need && !hundoFxEarned(x.id)); if(!d) return false; showUnlockDetail(hundoFxDetail(d.id)); return true;"), 2200),
    ("card-secret", card("const id = (AVATAR_CHARACTERS.find(c => c.secret && !c.retired && isLockedCharacter(c.id)) || {}).id; if(!id) return false; showUnlockDetail(characterDetail(id)); return true;"), 1800),
    ("card-pennants", card("if(!bannerDef('vrtop10')) return false; showUnlockDetail(bannerDetail('vrtop10')); return true;"), 2200),
    ("card-feat-banner", card("const id = window.NOVA_CLASS === 'ifc' ? 'early10' : FULLCASE_ID; if(!bannerDef(id)) return false; showUnlockDetail(bannerDetail(id)); return true;"), 2200),
    ("card-ultimate-character", card("if(typeof ULTIMATE_TOP === 'undefined') return false; showUnlockDetail(characterDetail(ULTIMATE_TOP)); return true;"), 2000),
    ("card-ultimate-banner", card("const d = BANNERS.find(b => b.ultimate); if(!d) return false; showUnlockDetail(bannerDetail(d.id)); return true;"), 2200),
    ("card-completionist", card("if(window.NOVA_CLASS !== 'ifc' || !bannerDef(COMPLETIONIST_ID)) return false; showUnlockDetail(bannerDetail(COMPLETIONIST_ID)); return true;"), 2400),
    ("card-held-character", card("const id = (AVATAR_CHARACTERS.find(c => c.feat && !c.secret && !isLockedCharacter(c.id)) || {}).id; if(!id) return false; showUnlockDetail(characterDetail(id)); return true;"), 2000),
]
SOCIAL = [
    ("profile", CLOSE + "; showProfile('profile'); " + TOP + "; return true;", 2200),
    ("leaderboard", CLOSE + "; showRankings(); " + TOP + "; return true;", 2600),
    ("leaderboard-pennants-card", "return (()=>{ const r = [...document.querySelectorAll('.screen-rankings .rank-row')].find(x => /Rosa/.test(x.textContent)); if(!r) return false; r.classList.remove('is-offscreen'); r.click(); return true; })()", 1600),
]
WEAR = lambda bid: CLOSE + "; return (()=>{ if(!bannerDef(%s) || !bannerEarned(%s)) return false; store.banner = %s; saveStore(); return true; })()" % ((json.dumps(bid),) * 3)
def big_banner_moment(bid):
    # Home tells it: the account holds it and it has not been shown (the app's own queue: pendingHomeUnlocks / playHomeUnlocks)
    return CLOSE + ("; return (()=>{ if(!bannerDef(%s) || !bannerEarned(%s)) return false; const u = ensureUnlocksShown(); u.banners = u.banners.filter(x => x !== %s);"
                    " saveStore(); showHome(); return true; })()") % ((json.dumps(bid),) * 3)

def plan(stage, dev):
    if dev == "ipad":
        return [s for s in PAGES if s[0] in ("customize", "character-page", "banner-page", "unlocks-top", "unlocks-answers-vr",
                                              "unlocks-feats-capstones", "unlocks-characters", "unlocks-banners", "unlocks-effects")] + \
               [s for s in CARDS if s[0] in ("card-locked-banner",)] + SOCIAL[:2]
    if stage == "new":
        return [s for s in PAGES if s[0] in ("customize", "customize-look", "character-page", "banner-page", "theme-page", "fx-page",
                                              "unlocks-top", "unlocks-hundos-study", "unlocks-feats-capstones", "unlocks-characters",
                                              "unlocks-banners", "unlocks-effects")] + \
               [s for s in CARDS if s[0] in ("card-locked-character", "card-ultimate-character")] + SOCIAL[:1]
    if stage == "mid":
        return PAGES + CARDS + SOCIAL
    return [s for s in PAGES if s[0] in ("customize", "character-page", "character-page-challenges", "character-page-secrets", "banner-page",
                                          "banner-page-challenges", "banner-page-end",
                                          "unlocks-top", "unlocks-vr-feats", "unlocks-feats-capstones", "unlocks-banners", "unlocks-banners-3")] + \
           [s for s in CARDS if s[0] in ("card-feat-banner", "card-ultimate-character", "card-ultimate-banner", "card-completionist", "card-pennants")]

with sync_playwright() as p:
    br = p.chromium.launch(executable_path=h["g"]["CHROME"], args=["--no-sandbox"])
    for cls in ("academy", "ifc"):
        if ONLY and ONLY != cls: continue
        for dev, w, hh, sc in (("pm", 440, 956, 2), ("ipad", 834, 1194, 2)):
            if DEV and DEV != dev: continue
            for stage in ("new", "mid", "near"):
                if STAGE and STAGE != stage: continue
                if dev == "ipad" and stage != "mid": continue
                seed, init = seeds(stage, cls)
                ctx, pg, errs = h["page"](br, text, seed, init, w=w, h=hh, scale=sc)
                pg.wait_for_timeout(1500)
                h["quiet"](pg); h["load_board"](pg); h["quiet"](pg)
                if stage == "near":
                    print(cls, "near holds:", json.dumps(pg.evaluate(NEAR, False)), flush=True)
                    h["quiet"](pg)
                if LIST:
                    print(cls, stage, json.dumps(pg.evaluate(NEAR.replace("const s = store", "const s = store; if(true){ const lockedC = AVATAR_CHARACTERS.filter(c => !c.retired && !c.legacy && isLockedCharacter(c.id)).map(c => c.id); return { lockedC, lockedB: BANNERS.filter(b => !bannerEarned(b.id)).map(b => b.id) }; }"), False)))
                    ctx.close(); continue
                pre = os.path.join(OUT, "%s-%s-%s-" % (cls, dev, stage))
                steps = plan(stage, dev)
                if stage == "near":
                    big = "completionist" if cls == "ifc" else "fullcase"
                    steps = steps + [("complete", "return true;", 0)] + [
                        ("moment-home", big_banner_moment(big), 2600),
                        ("moment-home-later", "return true;", 2200),
                        ("unlocks-top-complete", CLOSE + "; showUnlockTracks(); " + TOP + "; return true;", 2200),
                        ("unlocks-capstones-complete", scroll_to(".cz-group-trk-feats", 140), 1200),
                        ("card-big-banner-held", CLOSE + "; showUnlockDetail(bannerDetail(%s)); return true;" % json.dumps(big), 2600),
                        ("wear-big-banner", WEAR(big), 300),
                        ("profile-wearing", CLOSE + "; showProfile('profile'); " + TOP + "; return true;", 2600),
                        ("leaderboard-wearing", CLOSE + "; showRankings(); " + TOP + "; return true;", 2600),
                        ("leaderboard-own-card", "return (()=>{ const r = document.querySelector('.screen-rankings .rank-row:is(.lb-row-me, [data-me=\"1\"])'); if(!r) return false; r.classList.remove('is-offscreen'); r.click(); return true; })()", 1800),
                    ]
                i = 0
                for name, js, ms in steps:
                    if name == "complete":
                        h["quiet"](pg)
                        print(cls, "complete holds:", json.dumps(pg.evaluate(NEAR, True)), flush=True)
                        h["quiet"](pg)
                        continue
                    if name == "wear-big-banner":
                        pg.evaluate("()=>{ try{ %s }catch(e){ return false; } }" % js); continue
                    ok = pg.evaluate("()=>{ try{ %s }catch(e){ return false; } }" % js)
                    if ok is False:
                        print("skip", cls, dev, stage, name, flush=True); continue
                    pg.wait_for_timeout(ms)
                    i += 1
                    pg.screenshot(path=pre + "%02d-%s.png" % (i, name))
                pg.evaluate("()=>{ %s }" % CLOSE)
                print(cls, dev, stage, "errors:", errs[:3], flush=True)
                ctx.close()
    br.close()
