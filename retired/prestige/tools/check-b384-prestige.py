"""Build 384.126: PRESTIGE, Fire Code only. Madison: "you can prestige. Maybe there's like 3 prestige's for the fire code class? Each one
giving you a new character, banner, and then you get an emblem next to your profile? Max prestige would be highest prestige. Somehow tie
this into the challenge unlock stuff?" - "Yes, let's prestige."

Read off the page, by shape and by the app's own numbers (never label strings), on real-shaped Fire Code accounts built in the page
(tools/b384_prestige_lib.py: the counters an account carries, from a mid-ladder account to everything held):
 (1) ELIGIBILITY, derived per account: not eligible below Supernova or with no gold rim; Prestige I at Supernova + one gold rim; II only
     after I and with three gold rims; III only after II, with Mastery (five gold) and Completionist; in order (no skipping), once
     each, never a fourth; the screen's cards say the same (the Take button only on the one that can be taken);
 (2) TAKING ONE CHANGES NOTHING ELSE: a deep diff of the whole store before and after taking each is the count (and the "told" marks
     of what it hands over) and nothing more; level, rank, XP, badges, the tracks' code, the ultimate's and Completionist's counts are
     the same; what is held grows by exactly its character and its banner; it stays taken when its requirements later fail;
 (3) THE COUNT MERGES BY THE HIGHER and never lowers (mergeSameAccount both ways, mergeLeavingAccount, a stray value, applyLoadedData
     with none / too high / not a number), and survives a reload;
 (4) PUBLISHING: the class's board row carries `pg` (the count) as a lazy field; a 20-question drill writes no more documents than
     origin/main and the row no more often; no payload carries the sync code; an account hidden from the board writes no row;
 (5) THE ACADEMY SHOWS NONE OF IT: no prestige character or banner in its tables, no count read, no emblem on Profile, a card or the
     Leaderboard, no Prestige entry on Tracks, its row carries no `pg`;
 (6) THE EMBLEM BESIDE THE NAME on Profile, the person card, the Leaderboard row and a friend's profile (centred on the name's line,
     right after it), its numeral the row's count; a row with an unknown value (7, "3") or none shows nothing; the highest prestige's
     row is framed (and is not Mastery's gold name), its emblem is the laurelled one;
 (7) THE CEREMONY: the confirm sheet says what it gives and that nothing resets (its buttons >= 44px); the scene plays catalogue
     sounds, shows the emblem, title and three reward cards, and clears itself; under Reduce motion everything is there at once, at
     full opacity, nothing running;
 (8) THE ART: each prestige character draws (head, eyes with a closed pair, mouth, its moving parts) and is held only from its
     prestige; each banner is layered, moves only by transform / opacity, has no svg filter, has a still picture; Customize has a
     Prestige group of three characters and three banners, locked until taken;
 (9) no page errors.
  python3 tools/check-b384-prestige.py [--against OLD/index.html] [--only 1,2]     (must FAIL on origin/main: there is no prestige)"""
import json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b384_prestige_lib as L
from playwright.sync_api import sync_playwright

ARGS = sys.argv[1:]
def arg(n): return ARGS[ARGS.index(n) + 1] if n in ARGS else None
AGAINST = arg("--against")
ONLY = set((arg("--only") or "").split(",")) - {""}
def wanted(n): return not ONLY or str(n) in ONLY
TEXT = open(AGAINST or os.path.join(L.ROOT, "index.html"), encoding="utf-8").read()

ok = True
def chk(name, cond, info=None):
    global ok
    ok = ok and bool(cond)
    print(("PASS " if cond else "FAIL ") + name + ("" if cond or info is None else "  -> " + str(info)[:600]), flush=True)
class section:
    def __init__(self, name): self.name = name
    def __enter__(self): return self
    def __exit__(self, t, e, tb):
        if t is not None: chk(self.name + " runs", False, repr(e)[:400]); return True

VIEW = """()=>{ try{ const v = prestigeView(); return { taken: v.taken, list: v.list.map(e => ({ n: e.n, taken: e.taken, current: e.current, eligible: e.eligible,
  reqs: e.reqs.map(r => [r.key, !!r.done]) })) }; }catch(e){ return { err: String(e) }; } }"""
SNAP = """()=>{ const u = unlockedIdsNow(); let cp = null, up = null; try{ cp = completionistProgress(); }catch(e){} try{ up = ultimateProgress(); }catch(e){}
  return { store: JSON.parse(JSON.stringify(store)), chars: u.chars.slice().sort(), banners: u.banners.slice().sort(), themes: u.themes.slice().sort(),
    fx: (u.fx || []).slice().sort(), badges: (u.badges || []).slice().sort(), level: levelOf(store), rank: rankOf(store), xp: store.lifetime.points,
    ut: unlockTrackCode(), cp: cp && [cp.have, cp.need], up: up && [up.have, up.need], ifc: window.NOVA_CLASS }; }"""

def diff(a, b, path=""):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            out += diff(a.get(k, "<none>"), b.get(k, "<none>"), path + "." + k)
    elif a != b:
        out.append(path)
    return out

def main():
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=L.CHROME, args=["--no-sandbox"])
        fc = L.account(ifc=True)
        seed, init = L.ifc_seed(fc, friends=["pgmate00000", "pgmate00001"])
        ctx, pg, errs = L.page(br, TEXT, seed, init)
        L.quiet(pg)
        chk("the page is Fire Code", pg.evaluate("window.NOVA_CLASS") == "ifc")
        has = pg.evaluate("()=>typeof prestigeView === 'function' && typeof takePrestige === 'function'")
        chk("prestige exists on this page", has)
        # ---- (1) eligibility, step by step
        if wanted(1):
            with section("(1)"):
                seq = []
                for st in ["none", "super", "one"]:
                    b = L.build(pg, st); seq.append((st, b, pg.evaluate(VIEW)))
                v = {st: x[2] for st, x in zip(["none", "super", "one"], seq)}
                chk("(1) a mid-ladder account (%s): no prestige can be taken" % seq[0][1].get("rank"), v["none"].get("taken") == 0 and not any(e["eligible"] for e in v["none"]["list"]), v["none"])
                chk("(1) Supernova with no gold rim (%s): still none" % seq[1][1].get("golds"), seq[1][1].get("rank") == "titan" and not any(e["eligible"] for e in v["super"]["list"]), v["super"])
                chk("(1) Supernova + one gold rim: Prestige I can be taken, II and III cannot", [e["eligible"] for e in v["one"]["list"]] == [True, False, False], v["one"])
                r = pg.evaluate("()=>[takePrestige(2), takePrestige(3), store.prestige || 0]")
                chk("(1) no skipping: II and III refused while I is not taken %s" % r, r == [False, False, 0], r)
                ui = pg.evaluate("async ()=>{ showPrestige(); await new Promise(r => setTimeout(r, 500)); return [...document.querySelectorAll('.pg-card')].map(c => [c.dataset.pg, !!c.querySelector('.pg-take'), c.querySelectorAll('.pg-req').length, c.querySelectorAll('.pg-give').length]); }")
                chk("(1) the screen: three cards, the Take button only on I, each with its requirements and three rewards %s" % ui,
                    len(ui) == 3 and [x[1] for x in ui] == [True, False, False] and all(x[2] >= 2 and x[3] == 3 for x in ui), ui)
                tb = pg.evaluate("()=>{ const b = document.querySelector('.pg-take'); const r = b && b.getBoundingClientRect(); return r ? [r.width, r.height] : null; }")
                chk("(1) the Take button is a 44px target %s" % tb, tb and tb[1] >= 44 and tb[0] >= 44, tb)
                r = pg.evaluate("()=>[takePrestige(1), takePrestige(1), store.prestige]")
                chk("(1) Prestige I taken once, a second take refused %s" % r, r == [True, False, 1], r)
                vv = pg.evaluate(VIEW)
                chk("(1) after I with one gold rim: II is not eligible (needs three)", [e["eligible"] for e in vv["list"]] == [False, False, False] and vv["list"][0]["taken"], vv)
                L.build(pg, "three"); vv = pg.evaluate(VIEW)
                chk("(1) three gold rims: II can be taken, III cannot", [e["eligible"] for e in vv["list"]] == [False, True, False], vv)
                r = pg.evaluate("()=>[takePrestige(3), takePrestige(2), store.prestige]")
                chk("(1) III refused before II; II taken %s" % r, r == [False, True, 2], r)
                L.build(pg, "five"); vv = pg.evaluate(VIEW)
                chk("(1) Mastery without Completionist: III not eligible (its Completionist line open)", not vv["list"][2]["eligible"] and dict(vv["list"][2]["reqs"]).get("mastery") is True and dict(vv["list"][2]["reqs"]).get("completionist") is False, vv)
                L.build(pg, "all"); vv = pg.evaluate(VIEW)
                chk("(1) Mastery and Completionist: III can be taken", vv["list"][2]["eligible"] is True, vv)
                r = pg.evaluate("()=>[takePrestige(3), takePrestige(4), takePrestige(3), store.prestige, prestigeTaken()]")
                chk("(1) III taken; a fourth and a repeat refused; the count is 3 %s" % r, r == [True, False, False, 3, 3], r)
                L.build(pg, "none")
                r = pg.evaluate("()=>[store.prestige, prestigeTaken(), !isLockedCharacter('pgstate'), bannerEarned('pglaurel')]")
                chk("(1) taken stays taken when the requirements later fail (an account back below Supernova) %s" % r, r == [3, 3, True, True], r)
        # ---- (2) taking one changes nothing else
        if wanted(2):
            with section("(2)"):
                for n, st in ((1, "one"), (2, "three"), (3, "all")):
                    pg.evaluate("(n)=>{ store.prestige = n - 1; saveStore(); }", n)
                    L.build(pg, st)
                    a = pg.evaluate(SNAP)
                    ok_take = pg.evaluate("(n)=>takePrestige(n)", n)
                    b = pg.evaluate(SNAP)
                    d = [x for x in diff(a["store"], b["store"]) if x not in (".prestige", ".lastModified", ".savedAt") and not x.startswith(".unlocksShown")]
                    chk("(2) Prestige %d: taken, and the store differs only in the count (and the told marks) %s" % (n, d[:6]), ok_take and not d and b["store"].get("prestige") == n, d)
                    same = {k: (a[k], b[k]) for k in ("themes", "fx", "badges", "level", "rank", "xp", "ut", "cp", "up") if a[k] != b[k]}
                    chk("(2) Prestige %d: level, rank, XP, badges, themes, effects, the tracks' code, Completionist's and the ultimate's counts unchanged" % n, not same, same)
                    gc = sorted(set(b["chars"]) - set(a["chars"])); gb = sorted(set(b["banners"]) - set(a["banners"]))
                    lost = sorted((set(a["chars"]) - set(b["chars"])) | (set(a["banners"]) - set(b["banners"])))
                    want = pg.evaluate("(n)=>[PRESTIGE_CHAR[n], PRESTIGE_BANNER[n]]", n)
                    chk("(2) Prestige %d hands over exactly its character and banner %s %s" % (n, gc, gb), gc == [want[0]] and gb == [want[1]] and not lost, [gc, gb, lost])
                ex = pg.evaluate("""()=>{ const ids = ['pgdeputy','pgmarshal','pgstate','pgoath','pgcommand','pglaurel'];
                  const parts = completionistParts().map(p => p.items.map(i => i.id)).flat();
                  return { inCompletionist: ids.filter(i => parts.indexOf(i) >= 0), all3: ids.every(i => AVATAR_CHARACTERS.some(c => c.id === i) || !!bannerDef(i)) }; }""")
                chk("(2) the prestige items are outside Completionist's count (no circle: III asks for Completionist) %s" % ex, ex.get("all3") and not ex.get("inCompletionist"), ex)
        # ---- (3) merge by the higher, never lower
        if wanted(3):
            with section("(3)"):
                # two copies of the same account that differ in nothing but the count, so the merge's verdict is about the count alone
                m = pg.evaluate("""()=>{ const base = JSON.stringify(store);
                  const M = (d, s) => { const dst = JSON.parse(base), src = JSON.parse(base); dst.prestige = d; if(s === undefined) delete src.prestige; else src.prestige = s;
                    const r = mergeSameAccount(dst, src); return [dst.prestige, r.gained, r.otherHadLess]; };
                  const out = { up: M(1, 3), down: M(3, 1), same: M(2, 2), stray: M(1, 7), str: M(2, '3'), neg: M(2, -1), none: M(2, undefined) };
                  const was = store.prestige; store.prestige = 1; try{ mergeLeavingAccount({ prestige: 2, lifetime: {} }, ''); }catch(e){}
                  out.leaving = store.prestige; store.prestige = 3; try{ mergeLeavingAccount({ prestige: 1, lifetime: {} }, ''); }catch(e){} out.leavingLow = store.prestige;
                  const L = v => { const g = JSON.parse(JSON.stringify(store)); if(v === undefined) delete g.prestige; else g.prestige = v; applyLoadedData(g); return store.prestige; };
                  const keep = JSON.parse(JSON.stringify(store));
                  out.load = [L(undefined), L(5), L('x'), L(2.7), L(2)];
                  applyLoadedData(keep); return out; }""")
                chk("(3) mergeSameAccount takes the higher: 1 + 3 -> 3 (gained) %s" % m.get("up"), m.get("up") == [3, True, False], m)
                chk("(3) and never lowers: 3 + 1 -> 3 (the other copy had less) %s" % m.get("down"), m.get("down") == [3, False, True], m)
                chk("(3) a stray value cannot lift it past three or lower it %s %s %s %s" % (m.get("stray"), m.get("str"), m.get("neg"), m.get("none")),
                    m.get("stray") == [3, True, False] and m.get("str")[0] == 2 and m.get("neg")[0] == 2 and m.get("none")[0] == 2, m)
                chk("(3) leaving one account for another keeps the higher (never a sum) %s / %s" % (m.get("leaving"), m.get("leavingLow")), m.get("leaving") == 2 and m.get("leavingLow") == 3, m)
                chk("(3) applyLoadedData: none 0, 5 -> 3, not a number 0, 2.7 -> 2, 2 -> 2 %s" % m.get("load"), m.get("load") == [0, 3, 0, 2, 2], m)
                pg.evaluate("()=>{ store.prestige = 2; saveStore(); }")
                pg.wait_for_timeout(600)
                pg.reload(); pg.wait_for_timeout(4200); L.quiet(pg)
                chk("(3) the count survives a reload", pg.evaluate("()=>store.prestige") == 2)
        # ---- (6) the emblem beside the name
        if wanted(6):
            with section("(6)"):
                pg.evaluate("()=>{ store.prestige = 2; saveStore(); }")
                pg.evaluate("()=>showRankings()")
                pg.wait_for_timeout(2600)
                NEAR = """(sel)=>{ const out = [];
                  document.querySelectorAll(sel).forEach(nm => { const mk = nm.querySelector('.pg-mark') || (nm.parentElement && nm.parentElement.querySelector(':scope > .pg-mark'));
                    const txt = nm.querySelector('.pg-nm') || nm; const range = document.createRange(); range.selectNodeContents(txt); const t = range.getBoundingClientRect();
                    if(!mk){ out.push({ name: (txt.textContent || '').trim(), pg: 0 }); return; }
                    const m = mk.getBoundingClientRect();
                    out.push({ name: (txt.textContent || '').trim(), pg: +mk.dataset.pg, gap: Math.round(m.left - t.right), dy: Math.round(Math.abs((m.top + m.bottom) / 2 - (t.top + t.bottom) / 2)),
                               h: Math.round(m.height), th: Math.round(t.height), svg: !!mk.querySelector('svg.pg-emblem-' + mk.dataset.pg) }); });
                  return out; }"""
                rows = pg.evaluate(NEAR, ".screen-rankings .rank-row .lb-name")
                by = {r["name"]: r for r in rows}
                want = {"Alexis": 3, "Kimber": 2, "Leeland": 1, "Rosa": 0, "Dmitri": 0, "Priya": 0, "Tomas": 0}
                got = {k: by.get(k, {}).get("pg") for k in want}
                chk("(6) Leaderboard: each row's emblem is its count, none for 0 / no field / 7 / \"3\" %s" % got, got == want, rows)
                me = by.get("Maddox", {})
                chk("(6) Leaderboard: your own row shows your own count (II) %s" % me, me.get("pg") == 2, rows)
                lit = [r for r in rows if r.get("pg")]
                chk("(6) Leaderboard: the emblem sits right after the name, on its line, about the text's height %s" % [(r["name"], r["gap"], r["dy"], r["h"], r["th"]) for r in lit],
                    lit and all(0 <= r["gap"] <= 14 and r["dy"] <= 4 and .7 * r["th"] <= r["h"] <= 1.8 * r["th"] and r["svg"] for r in lit), lit)
                fr = pg.evaluate("""()=>[...document.querySelectorAll('.screen-rankings .rank-row')].map(r => [((r.querySelector('.pg-nm') || r.querySelector('.lb-name')) || {}).textContent, !!r.querySelector(':scope > .lb-pgmax'), (r.querySelector('.lb-name') || {}).classList ? r.querySelector('.lb-name').classList.contains('is-mastery') : null])""")
                framed = sorted(x[0] for x in fr if x[1])
                chk("(6) only the highest prestige's row is framed %s" % framed, framed == ["Alexis"], fr)
                mast = [x for x in fr if x[0] == "Alexis"]
                fcol = pg.evaluate("()=>{ const r = [...document.querySelectorAll('.screen-rankings .rank-row')].find(r => /Alexis/.test(r.textContent)); const f = r && r.querySelector(':scope > .lb-pgmax'); return f ? getComputedStyle(f).boxShadow : null; }")
                chk("(6) and the frame is not Mastery's look: a gold line round the row with a crimson edge (%s)" % (fcol or "")[:90], bool(fcol) and "245, 200, 74" in fcol and "181, 18, 27" in fcol, fcol)
                em3 = pg.evaluate("()=>{ const a = buildPrestigeEmblemSVG(3).innerHTML, b = buildPrestigeEmblemSVG(1).innerHTML; return [a.split('<path').length, b.split('<path').length]; }")
                chk("(6) the highest emblem is the grander drawing (laurel and star: %d paths against I's %d)" % (em3[0], em3[1]), em3[0] > em3[1] + 10, em3)
                card = pg.evaluate("""async ()=>{ const W = ms => new Promise(r => setTimeout(r, ms)); const out = {};
                  for(const n of ['Alexis', 'Rosa']){ document.querySelectorAll('.invite-overlay').forEach(o => o.remove());
                    const e = (classBoardRows || []).find(r => r.firstName === n); openPersonSheet(Object.assign({}, e, { boardCls: ART_PAGE })); await W(500);
                    const nm = document.querySelector('.person-card .person-sheet-name'); const mk = nm && nm.querySelector('.pg-mark');
                    const range = document.createRange(); if(nm) range.setStart(nm.firstChild, 0), range.setEnd(nm.firstChild, nm.firstChild.length);
                    const t = nm ? range.getBoundingClientRect() : null, m = mk ? mk.getBoundingClientRect() : null;
                    out[n] = { pg: mk ? +mk.dataset.pg : 0, gap: m ? Math.round(m.left - t.right) : null, dy: m ? Math.round(Math.abs((m.top + m.bottom) / 2 - (t.top + t.bottom) / 2)) : null }; }
                  document.querySelectorAll('.invite-overlay').forEach(o => o.remove()); return out; }""")
                chk("(6) the person card: III beside Alexis's name, nothing beside Rosa's %s" % card, card.get("Alexis", {}).get("pg") == 3 and card["Alexis"]["gap"] is not None and 0 <= card["Alexis"]["gap"] <= 14 and card["Alexis"]["dy"] <= 5 and card.get("Rosa", {}).get("pg") == 0, card)
                prof = pg.evaluate("""async ()=>{ showProfile(); await new Promise(r => setTimeout(r, 1200)); const row = document.querySelector('.profile-hero .namedisplay-row');
                  const nm = row && row.querySelector('.profile-name-display'), mk = row && row.querySelector('.pg-mark'); if(!nm) return null;
                  const t = nm.getBoundingClientRect(), m = mk ? mk.getBoundingClientRect() : null;
                  return { pg: mk ? +mk.dataset.pg : 0, gap: m ? Math.round(m.left - t.right) : null, dy: m ? Math.round(Math.abs((m.top + m.bottom) / 2 - (t.top + t.bottom) / 2)) : null }; }""")
                chk("(6) Profile: your emblem (II) right after your name %s" % prof, prof and prof["pg"] == 2 and prof["gap"] is not None and 0 <= prof["gap"] <= 24 and prof["dy"] <= 8, prof)
                fp = pg.evaluate("""async ()=>{ const e = (classBoardRows || []).find(r => r.firstName === 'Alexis'); showFriendProfile(e); await new Promise(r => setTimeout(r, 1800));
                  const p = document.querySelector('#stage > .screen-friendprofile'); const row = p && p.querySelector('.namedisplay-row');
                  const nm = row && row.querySelector('.profile-name-display'), mk = row && row.querySelector('.pg-mark'); if(!nm) return { none: !!p };
                  const t = nm.getBoundingClientRect(), m = mk ? mk.getBoundingClientRect() : null;
                  return { pg: mk ? +mk.dataset.pg : 0, gap: m ? Math.round(m.left - t.right) : null, dy: m ? Math.round(Math.abs((m.top + m.bottom) / 2 - (t.top + t.bottom) / 2)) : null }; }""")
                chk("(6) a friend's profile: their emblem (III) right after their name %s" % fp, fp and fp.get("pg") == 3 and fp["gap"] is not None and 0 <= fp["gap"] <= 24 and fp["dy"] <= 8, fp)
        # ---- (7) the ceremony
        if wanted(7):
            with section("(7)"):
                pg.evaluate("()=>{ store.prestige = 0; saveStore(); }")
                L.build(pg, "one"); L.quiet(pg)
                c = pg.evaluate("""async ()=>{ showPrestige(); confirmPrestige(1); await new Promise(r => setTimeout(r, 700));
                  const s = document.querySelector('.invite-overlay .pg-confirm'); if(!s) return null;
                  const bs = [...s.querySelectorAll('button')].map(b => { const r = b.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; });
                  return { gives: s.querySelectorAll('.pg-give').length, names: [...s.querySelectorAll('.pg-give-name')].map(n => n.textContent),
                           want: [AVATAR_DISPLAY_NAME[PRESTIGE_CHAR[1]], bannerDef(PRESTIGE_BANNER[1]).name], keep: !!s.querySelector('.pg-confirm-keep'), bs, taken: store.prestige || 0 }; }""")
                chk("(7) the confirm sheet: its three rewards by name, the nothing-resets line, nothing taken yet %s" % c,
                    c and c["gives"] == 3 and c["names"][:2] == c["want"] and c["keep"] and c["taken"] == 0, c)
                chk("(7) its buttons are 44px targets %s" % (c or {}).get("bs"), c and len(c["bs"]) == 2 and all(h >= 44 for _, h in c["bs"]), c)
                pg.evaluate("()=>{ window.__snd = []; const o = playSound; window.playSound = function(id, x){ window.__snd.push(id); return o(id, x); }; }")
                pg.evaluate("()=>{ document.querySelector('.pg-confirm-go').click(); }")
                pg.wait_for_timeout(5200)
                sc = pg.evaluate("""()=>{ const s = document.querySelector('.pg-scene'); if(!s) return null; const V = el => { if(!el) return false; const cs = getComputedStyle(el), r = el.getBoundingClientRect(); return r.width > 4 && r.height > 4 && +cs.opacity > .95 && cs.visibility !== 'hidden'; };
                  return { emblem: V(s.querySelector('.pg-scene-emblem')), title: V(s.querySelector('.pg-scene-name')), cards: [...s.querySelectorAll('.pg-give')].filter(V).length,
                           done: V(s.querySelector('.pg-scene-done')), taken: store.prestige, focus: document.body.classList.contains('cutscene-focus'), snd: (window.__snd || []).slice(),
                           known: (window.__snd || []).every(id => !!SOUND_CATALOGUE[id]) }; }""")
                chk("(7) the ceremony: the emblem, its title, three reward cards and Done, all on screen; Prestige I taken %s" % sc,
                    sc and sc["emblem"] and sc["title"] and sc["cards"] == 3 and sc["done"] and sc["taken"] == 1, sc)
                chk("(7) it holds cutscene focus and plays the catalogue's own sounds %s" % (sc or {}).get("snd"), sc and sc["focus"] and len(sc["snd"]) >= 3 and sc["known"], sc)
                after = pg.evaluate("async ()=>{ document.querySelector('.pg-scene-done').click(); await new Promise(r => setTimeout(r, 900)); return [document.querySelectorAll('.pg-scene').length, document.body.classList.contains('cutscene-focus'), !!document.querySelector('#stage .profile-hero')]; }")
                chk("(7) Done clears it (no layer, no focus) and opens Profile %s" % after, after == [0, False, True], after)
                # under Reduce motion
                rctx, rpg, rerrs = L.page(br, TEXT, seed, init, reduced=True)
                L.quiet(rpg)
                L.build(rpg, "one")
                rs = rpg.evaluate("""async ()=>{ store.prestige = 0; if(!takePrestige(1)) return { notTaken: true }; playPrestigeScene(1); await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
                  const s = document.querySelector('.pg-scene'); const V = el => { if(!el) return false; const cs = getComputedStyle(el), r = el.getBoundingClientRect(); return r.width > 4 && r.height > 4 && +cs.opacity > .95; };
                  /* (a character's own drawing keeps its closed eyes and its special put away at rest, as everywhere: not the scene's) */
                  const op = [s, ...s.querySelectorAll('*')].filter(el => !el.closest('svg.avatarchar-svg') && getComputedStyle(el).display !== 'none' && +getComputedStyle(el).opacity < .05 && el.getBoundingClientRect().width > 0).map(el => el.className.baseVal !== undefined ? el.className.baseVal : el.className);
                  return { still: s.classList.contains('is-still'), emblem: V(s.querySelector('.pg-scene-emblem')), title: V(s.querySelector('.pg-scene-name')),
                           cards: [...s.querySelectorAll('.pg-give')].filter(V).length, done: V(s.querySelector('.pg-scene-done')), running: document.getAnimations().filter(a => s.contains(a.effect && a.effect.target)).length, hidden: op.slice(0, 6) }; }""")
                chk("(7) Reduce motion: everything there at once at full opacity, nothing running, nothing left at opacity 0 %s" % rs,
                    rs.get("still") and rs.get("emblem") and rs.get("title") and rs.get("cards") == 3 and rs.get("done") and rs.get("running") == 0 and not rs.get("hidden"), rs)
                chk("(7) no page errors under Reduce motion", not rerrs, rerrs)
                rctx.close()
        # ---- (8) the art and Customize
        if wanted(8):
            with section("(8)"):
                a = pg.evaluate("""()=>['pgdeputy', 'pgmarshal', 'pgstate'].map(id => { const s = buildAvatarCharSVGSafe(id);
                  return { id, char: s.getAttribute('data-char'), head: !!s.querySelector('.cx-head'), eyes: !!s.querySelector('.cx-eyes'), closed: !!s.querySelector('[class*="closed"]'),
                           mouth: !!s.querySelector('.cx-mouth'), fx: s.querySelectorAll('.cx-fx').length, filter: s.querySelectorAll('filter').length, special: typeof CHAR_SPECIAL_DRAW[id] === 'function',
                           name: AVATAR_DISPLAY_NAME[id], glow: avatarGlowColor(id), cat: charCategory(id) }; })""")
                chk("(8) each prestige character is drawn as itself: head, eyes and a closed pair, mouth, moving parts, its special, no filter %s" % [(x["id"], x["name"], x["fx"]) for x in a],
                    all(x["char"] == x["id"] and x["head"] and x["eyes"] and x["closed"] and x["mouth"] and x["fx"] >= 1 and x["special"] and not x["filter"] and x["cat"] == "prestige" for x in a), a)
                chk("(8) three different names, none the name of another character", len({x["name"] for x in a}) == 3 and pg.evaluate("(ns)=>Object.keys(AVATAR_DISPLAY_NAME).filter(k => ['pgdeputy','pgmarshal','pgstate'].indexOf(k) < 0 && ns.indexOf(AVATAR_DISPLAY_NAME[k]) >= 0).length", [x["name"] for x in a]) == 0)
                live = pg.evaluate("""async ()=>{ const out = []; for(const id of ['pgdeputy', 'pgmarshal', 'pgstate']){ const sp = document.createElement('span'); sp.className = 'rank-avatar';
                  sp.style.cssText = 'position:fixed;left:0;top:0;width:96px;height:96px;display:block'; sp.appendChild(buildAvatarCharSVGSafe(id)); document.body.appendChild(sp); setCharState(sp, 'live');
                  await new Promise(r => setTimeout(r, 400)); out.push(document.getAnimations().filter(a => sp.contains(a.effect && a.effect.target)).length); sp.remove(); } return out; }""")
                chk("(8) each is alive on a board (its idle loop runs) %s" % live, all(n >= 2 for n in live), live)
                held = pg.evaluate("()=>{ const out = []; for(let n = 0; n <= 3; n++){ store.prestige = n; out.push(['pgdeputy','pgmarshal','pgstate'].map(id => !isLockedCharacter(id)).concat(['pgoath','pgcommand','pglaurel'].map(id => bannerEarned(id)))); } store.prestige = 1; return out; }")
                chk("(8) held exactly from their own prestige up %s" % held,
                    held == [[False] * 6, [True, False, False, True, False, False], [True, True, False, True, True, False], [True] * 6], held)
                bn = pg.evaluate("""async ()=>{ const out = []; for(const id of ['pgoath', 'pgcommand', 'pglaurel']){ const box = document.createElement('div'); box.style.cssText = 'position:fixed;left:0;top:0;width:480px;height:180px';
                  const art = buildBannerArt(id); box.appendChild(art); document.body.appendChild(box); await new Promise(r => setTimeout(r, 300));
                  const anims = document.getAnimations().filter(a => box.contains(a.effect && a.effect.target));
                  const props = new Set(); anims.forEach(a => { try{ a.effect.getKeyframes().forEach(k => Object.keys(k).forEach(p => { if(['offset', 'easing', 'composite', 'computedOffset'].indexOf(p) < 0) props.add(p); })); }catch(e){} });
                  out.push({ id, layered: !!box.querySelector('.bnr-layered, .bn-stage'), anims: anims.length, props: [...props], filter: box.querySelectorAll('filter').length, still: !!bannerRowStillURL(id), name: bannerDef(id) && bannerDef(id).name });
                  box.remove(); } return out; }""")
                chk("(8) each banner is layered and moves (%s), only by transform / opacity, no svg filter, has a still picture" % [(x["id"], x["anims"], x["props"]) for x in bn],
                    all(x["layered"] and x["anims"] >= 4 and set(x["props"]) <= {"transform", "opacity"} and not x["filter"] and x["still"] for x in bn), bn)
                cz = pg.evaluate("""async ()=>{ const W = ms => new Promise(r => setTimeout(r, ms)); store.prestige = 1; showCustomize('character'); await W(900);
                  const grp = [...document.querySelectorAll('.cz-group')].find(g => [...g.querySelectorAll('.avatarchar-option')].some(o => /Deputy Marshal|Fire Marshal/.test(o.getAttribute('aria-label') || '')));
                  const tiles = grp ? [...grp.querySelectorAll('.avatarchar-option')].map(o => [o.getAttribute('aria-label'), o.classList.contains('locked')]) : null;
                  showCustomize('banner'); await W(1200);
                  const bt = [...document.querySelectorAll('.banner-opt')].filter(b => ['pgoath','pgcommand','pglaurel'].some(id => (b.dataset.banner || b.dataset.id || '') === id || (b.getAttribute('aria-label') || '').indexOf(bannerDef(id).name) >= 0)).map(b => b.classList.contains('locked'));
                  return { tiles, bt }; }""")
                chk("(8) Customize: a Prestige group of the three characters, only Deputy Marshal held at Prestige I %s" % cz.get("tiles"),
                    cz.get("tiles") and len(cz["tiles"]) == 3 and [x[1] for x in cz["tiles"]] == [False, True, True], cz)
                chk("(8) Customize: the three prestige banners, only the first held %s" % cz.get("bt"), cz.get("bt") == [False, True, True], cz)
        chk("(9) no page errors in Fire Code", not errs, errs)
        ctx.close()
        # ---- (4) publishing
        if wanted(4):
            with section("(4)"):
                fc2 = L.account(ifc=True, extra={"prestige": 2})
                seed2, init2 = L.ifc_seed(fc2)
                ctx, pg, errs = L.page(br, TEXT, seed2, init2)
                L.quiet(pg)
                r = pg.evaluate("()=>{ const row = buildClassBoardRow(); return { pg: row.pg, lazy: ROW_LAZY_FIELDS.indexOf('pg') >= 0, keys: Object.keys(row) }; }")
                chk("(4) the board row carries pg = the count (2), as a lazy field %s" % {k: r.get(k) for k in ("pg", "lazy")}, r.get("pg") == 2 and r.get("lazy") is True, r)
                pg.evaluate("()=>{ try{ lastRowSig = null; flushClassBoardRow(); }catch(e){} }"); pg.wait_for_timeout(2500)
                # the board as the (fake) server holds it, and every document anybody else can read: no sync code in any of it
                cl = pg.evaluate("()=>{ const C = window.__cloud || {}; const me = publicIdOf(); const b = ((C.vrooms || {})['lb-ifc-v1'] || {}).rows || {};"
                                 " return { mine: b[me] || null, pub: JSON.stringify({ vrooms: C.vrooms, leaderboard: C.leaderboard }),"
                                 " pays: (window.__payloads || []).filter(x => x.indexOf('progress/') !== 0).join('\\n'), writes: (window.__writes || []).slice() }; }")
                code = L.CODE
                # (the account's own documents are keyed by the code - progress/<code> - and nobody else reads them: they are left out)
                leak = [(w, "public docs" if w in cl["pub"] else "payload") for w in (code, code.replace("-", "")) if w in cl["pub"] or w in cl["pays"]]
                mine = cl.get("mine") or {}
                chk("(4) the row reached the board with pg = 2, and no public document or payload carries the sync code (row keys %s)" % sorted(mine)[:40],
                    mine.get("pg") == 2 and not leak, [leak, cl["writes"][-6:]])
                # hidden: no row
                pg.evaluate("()=>{ window.__writes = []; store.leaderboardOptIn = false; store.prestige = 3; try{ lastRowSig = null; pushClassBoardRow(); flushClassBoardRow(); }catch(e){} }")
                pg.wait_for_timeout(2000)
                hid = pg.evaluate("()=>(window.__writes || []).filter(x => x.indexOf('vrooms/lb-ifc-v1') >= 0).length")
                chk("(4) an account hidden from the board writes no row (%d)" % hid, hid == 0, hid)
                ctx.close()
                # the 20-question drill: writes compared with origin/main
                btext = subprocess.run(["git", "show", "origin/main:index.html"], cwd=L.ROOT, capture_output=True, text=True, check=True).stdout
                DRILL = """async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms));
                  setInterval(()=>[...document.body.children].forEach(n=>{ if(getComputedStyle(n).position==='fixed' && /challenge complete|unlocked/i.test(n.textContent||'')) n.remove(); }), 40);
                  document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove()); theme.reduceMotion = true; applyTheme();
                  const U = topicsIn(QUESTIONS).find(t => QUESTIONS.filter(q => q.topic === t).length >= 20);
                  cfg.mode='drill'; cfg.units=[U]; cfg.versions={}; cfg.source='all'; cfg.size=0; cfg.timer='off'; cfg.flashcards=false;
                  const ix = QUESTIONS.map((q,i)=>i).filter(i=>QUESTIONS[i].topic===U).slice(0, 20);
                  window.__writes = []; window.__payloads = [];
                  beginRun(freshOrder(ix), null);
                  for(let i = 0; i < 80 && !document.querySelector('.qpanel .choice'); i++) await wait(150);
                  const a0 = (store.lifetime||{}).answered || 0;
                  for(let i = 0; i < 60; i++){
                    if(document.querySelector('.rs-rewards')) break;
                    const p = pos; const r = correctSlot(order[pos]);
                    const b = document.querySelector('.qpanel .choice[data-index="' + r + '"]'); if(b) b.click();
                    await wait(200);
                    const n = document.getElementById('nextbtn'); if(n && !n.hidden) n.click();
                    for(let k = 0; k < 40; k++){ await wait(60); if(pos !== p || document.querySelector('.rs-rewards')) break; }
                  }
                  for(let i = 0; i < 80 && !document.querySelector('.rs-rewards'); i++) await wait(150);
                  await wait(1500);
                  return { results: !!document.querySelector('.rs-rewards'), answered: ((store.lifetime||{}).answered || 0) - a0, writes: (window.__writes || []).slice(), pays: (window.__payloads || []).map(x => x.slice(0, 40)) }; }"""
                def drill(text):
                    c, pgx, e = L.page(br, text, seed2, init2)
                    L.quiet(pgx); pgx.wait_for_timeout(2000)
                    r = pgx.evaluate(DRILL); c.close(); return r
                nr = drill(TEXT); brr = drill(btext)
                cnt = lambda ws: {w: ws.count(w) for w in set(ws)}
                cn, cb = cnt(nr["writes"]), cnt(brr["writes"])
                over = {k: (cn[k], cb.get(k, 0)) for k in cn if cn[k] > cb.get(k, 0)}
                chk("(4) a 20-question drill ran to its results on both builds (%s answered here, %s on origin/main)" % (nr["answered"], brr["answered"]), nr["results"] and brr["results"] and nr["answered"] >= 15, [nr["answered"], brr["answered"]])
                chk("(4) it writes no more documents than origin/main: here %s, origin/main %s" % (cn, cb), not over and sum(cn.values()) <= sum(cb.values()), over)
                rown = len([x for x in nr["writes"] if "vrooms/lb-ifc-v1" in x]); rowb = len([x for x in brr["writes"] if "vrooms/lb-ifc-v1" in x])
                chk("(4) the board row is written no more often than before and never per answer (%d here, %d on origin/main)" % (rown, rowb), rown <= rowb and rown <= 3, [rown, rowb])
        # ---- (5) the academy shows none of it
        if wanted(5):
            with section("(5)"):
                a = L.account(extra={"prestige": 3, "classes": ["academy"]})
                aseed = {"progress": {L.CODE: a}, "leaderboard": {"pgacad00001": {"firstName": "Quinn", "avatarChar": "ghost", "level": 30, "badges": 3, "pg": 3, "lastModified": L.now_ms, "seenAt": L.now_ms}}}
                ctx, pg, errs = L.page(br, TEXT, aseed, L.init_js(a))
                L.quiet(pg)
                r = pg.evaluate("""async ()=>{ const W = ms => new Promise(r => setTimeout(r, ms)); const out = { cls: window.NOVA_CLASS || 'academy' };
                  out.chars = AVATAR_CHARACTERS.filter(c => c.prestige || /^pg/.test(c.id)).length; out.banners = BANNERS.filter(b => b.prestige || /^pg/.test(b.id)).length;
                  out.taken = typeof prestigeTaken === 'function' ? prestigeTaken() : 0;
                  try{ out.rowPg = 'pg' in buildLeaderboardRow(); }catch(e){ out.rowPg = 'err'; }
                  showProfile(); await W(1000); out.profile = document.querySelectorAll('.pg-mark').length;
                  showRankings(); await W(2500); out.board = document.querySelectorAll('.pg-mark, .lb-pgmax').length;
                  showUnlockTracks(); await W(700); out.tracks = document.querySelectorAll('.pg-entry, .pg-entry-row').length;
                  out.prestigeWord = /prestige tier/.test(document.querySelector('.cz-page-note') ? document.querySelector('.cz-page-note').textContent : '');
                  return out; }""")
                chk("(5) the academy: no prestige character or banner, no count, no pg on its row %s" % r, r.get("chars") == 0 and r.get("banners") == 0 and r.get("taken") == 0 and r.get("rowPg") is False, r)
                chk("(5) the academy: no emblem on Profile or the Leaderboard (a row with pg 3 included), no Prestige entry on Tracks %s" % r,
                    r.get("profile") == 0 and r.get("board") == 0 and r.get("tracks") == 0 and r.get("prestigeWord") is True, r)
                chk("(9) no page errors in the academy", not errs, errs)
                ctx.close()
        br.close()
    print("ALL PASS" if ok else "FAILURES", flush=True)
    sys.exit(0 if ok else 1)

main()
