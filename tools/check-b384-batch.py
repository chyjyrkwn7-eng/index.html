"""Build 384 (characters, banners, hundo effects round) - the RULES half: three starters, the challenges, one ultimate per class, the hundo rungs.
Madison: "we have too many starters ... removing two starters and leaving just three. Let's get rid of ninja, and wizard. (This goes for all classes) if
someone has either of these selected change it to one of the other available starters by random" / Inspector "just make it get 10 daily questions right" /
Strobe "make that 3" / Toxic Spill "make that 3" / Hazmat "doesn't need to be a single test ... for the ifc one, make that 100" / Hydrant "in the ifc one, make
that 14 different days" / "Sprinkler head and drone pilot are like the exact same challenge" / "There only needs to be one [ultimate] instead of three, for ifc,
only keep the star ranger and its banner. For the academy, keep astral and its banner. Change the astral challenge to zenith's" / "150 hundos is kinda a lot ...
make that 100. So the order should be 0, 25, 50, 75, 100" / academy "the highest one there should be 200".
Run in BOTH classes (Fire Code and the academy), read off the page:
(1) exactly three starters (not retired, no unlock, no challenge) in each class, and the Ninja and the Wizard are not among them;
(2) an account wearing the Ninja or the Wizard is moved to one of the three, the same one every time (a stable pick), whichever class;
(3) the Inspector/Detective counts every daily question right (not a run): 10 right with a miss between them is done; the Strobe/Clown asks 3 wins; Toxic Spill/Orion a hundo in
    3 units in a day;
(4) Fire Code: the Hazmat is 100 in a row counting runs across tests; the Hydrant's slot is 14 different days; the academy keeps 250-in-one-test and 30 days;
(5) the Hive/Sprinkler Head asks something no other reward asks: not a count of questions, not a test (the Ronin's), and it is the same on every class -
    since 384 r14 hosting 3 Virtual Room matches to the end (not the Strobe's winning ones);
(6) one ultimate per class: Fire Code keeps Zenith (the Star Ranger) and its banner, the academy Astral and its banner; the others are gone from the lists; the
    survivor's challenge is "everything" (character, banner, theme and hundo effect), it is listed under the challenge rewards, and nobody is left wearing a removed one;
(7) the hundo rungs: Fire Code 0, 25, 50, 75, 100; the academy 0 then rising, topping out at 200 (every rung below the next);
(8) no page errors.
Run:  python3 tools/check-b384-batch.py   (--against OLD/index.html must FAIL)"""

import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b384ic"}
exec(src, G)
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = G["g"]["INSET_RE"]
    def _old(ins):
        t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
        return IR.sub(lambda m: v[m.group(1)], OLD)
    G["g"]["patched"] = _old

from playwright.sync_api import sync_playwright
import json
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)
J = """()=>{
  const live = AVATAR_CHARACTERS.filter(c => !c.retired && !c.legacy);
  const out = { cls: window.NOVA_CLASS, top: typeof ULTIMATE_TOP === 'undefined' ? null : ULTIMATE_TOP,
    starters: live.filter(c => !c.unlock && !c.feat).map(c => c.id),
    ultimates: live.filter(c => c.ultimate).map(c => c.id + ':' + c.feat),
    ultBanners: BANNERS.filter(b => b.ultimate).map(b => b.id),
    fx: HUNDO_FX.map(d => d.need) };
  // (2) the pick is stable and lands on a starter
  const pick = (id, name) => { store.avatarChar = id; store.firstName = name; try{ retireStarters384(); }catch(e){ return 'ERR'; } return store.avatarChar; };
  out.moved = ['Alex','Bo','Cy','Dee','Eve','Fay','Gus','Hal'].map(n => [pick('ninja', n), pick('wizard', n), pick('ninja', n)]);
  // (3) the feats
  const f = CHARACTER_FEATS; const L = store.lifetime;
  const was = { t: store.dailyCorrectTotal, b: store.dailyCorrectBest, s: store.dailyCorrectStreak };
  store.dailyCorrectBest = 0; store.dailyCorrectStreak = 0; store.dailyCorrectTotal = 9; out.d9 = f.daily10.done();
  store.dailyCorrectTotal = 10; out.d10 = f.daily10.done(); out.dLabel = f.daily10.label;
  store.dailyCorrectTotal = was.t; store.dailyCorrectBest = was.b; store.dailyCorrectStreak = was.s;
  out.vr = [f.vrwins5.need, f.hundo7day.need];
  out.streak = { need: f.streak100.need, label: f.streak100.label };
  const wb = { b: store.bestTestStreak, l: L.longestStreak, c: L.currentStreak };
  store.bestTestStreak = 0; L.currentStreak = 0; L.longestStreak = f.streak100.need; out.streakAcross = f.streak100.done();
  L.longestStreak = f.streak100.need - 1; out.streak99 = f.streak100.done(); store.bestTestStreak = wb.b; L.longestStreak = wb.l; L.currentStreak = wb.c;
  out.days = f.days30.need;
  /* (384 r14) hosting Virtual Room matches: not the Strobe's winning one */
  out.hive = { label: f.busyday300.label, ronin: f.bigtest400.label, strobe: f.vrwins5.label, need: f.busyday300.need, hostNeed: typeof VR_HOST_NEED === 'number' ? VR_HOST_NEED : null };
  return out; }"""
res = {}
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    ctx, pg, e1 = G["page"](br, G["init"](G["ifc"])); res["ifc"] = pg.evaluate(J); ctx.close()
    ctx, pg, e2 = G["page"](br, G["init"](G["academy"], active="academy")); res["academy"] = pg.evaluate(J); ctx.close()
    br.close()
I, A = res["ifc"], res["academy"]
for k, v in (("Fire Code", I), ("academy", A)):
    chk("(1) %s has exactly three starters, never the Ninja or the Wizard (%s)" % (k, v["starters"]), len(v["starters"]) == 3 and not {"ninja", "wizard"} & set(v["starters"]), v["starters"])
    mv = v["moved"]
    chk("(2) %s: whoever wears the Ninja or the Wizard is moved to one of the three, the same one every time, and the picks are not all one (%s)" % (k, mv),
        all(set(t) <= set(v["starters"]) and t[0] == t[2] for t in mv) and len({t[0] for t in mv}) >= 2, mv)
    chk("(3) %s: the Inspector/Detective counts daily questions right, 10 not 9 (%s / %s), the Strobe 3 and Toxic Spill 3 (%s)" % (k, v["d9"], v["d10"], v["vr"]),
        v["d9"] is False and v["d10"] is True and v["vr"] == [3, 3] and "in a row" not in v["dLabel"], v)
    chk("(5) %s: the Hive's challenge is its own - not a count of questions, not the Ronin's test (%s / %s)" % (k, v["hive"]["label"], v["hive"]["ronin"]),
        "questions" not in v["hive"]["label"] and "test of" not in v["hive"]["label"].lower() and v["hive"]["label"] != v["hive"]["ronin"]
        # (384 r14) and it is hosting Virtual Room matches, VR_HOST_NEED of them - not the Strobe's winning ones
        and v["hive"]["label"].startswith("Host ") and "Virtual Room" in v["hive"]["label"] and v["hive"]["need"] == v["hive"]["hostNeed"] == 3
        and v["hive"]["label"] != v["hive"]["strobe"], v["hive"])
    chk("(6) %s: one ultimate - %s - and its banner (%s %s), asking for everything" % (k, v["top"], v["ultimates"], v["ultBanners"]),
        len(v["ultimates"]) == 1 and v["ultimates"][0].startswith(v["top"] + ":everything") and v["ultBanners"] == [v["top"]], v)
chk("(4) Fire Code: Hazmat 100 in a row across tests (99 no, 100 yes), 14 different days (%s, %s)" % (I["streak"], I["days"]),
    I["streak"]["need"] == 100 and I["streakAcross"] is True and I["streak99"] is False and I["days"] == 14, I)
chk("(4) the academy keeps 250 and 30 days; its Marksman run carries across tests too (Madison: \"doesn't need to happen in a single test. Same for both\") (%s, %s)" % (A["streak"]["need"], A["days"]),
    A["streak"]["need"] == 250 and A["days"] == 30 and A["streakAcross"] is True and A["streak99"] is False and "single test" not in A["streak"]["label"], A)
chk("(6) Fire Code's survivor is Zenith, the academy's Astral", I["top"] == "zenith" and A["top"] == "astral", [I["top"], A["top"]])
chk("(7) Fire Code's hundo rungs are 0, 25, 50, 75, 100 (%s)" % I["fx"], I["fx"] == [0, 25, 50, 75, 100], I["fx"])
chk("(7) the academy's rise and top out at 200 (%s)" % A["fx"], A["fx"][0] == 0 and A["fx"] == sorted(A["fx"]) and len(set(A["fx"])) == len(A["fx"]) and A["fx"][-1] == 200, A["fx"])
chk("(8) no page errors", not e1 and not e2, (e1 + e2)[:3])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
