#!/usr/bin/env python3
"""Self-test for `firestore-admin.py merge-now` (the server-side fold of a duplicate account).

It NEVER touches the real Firestore: the tool is pointed at a small in-memory stand-in
that speaks the same REST calls (list, beginTransaction, batchGet, commit with
preconditions, rollback), and the merge itself is also run against the app's own
`mergeLeavingAccount` in Chromium so the Python port cannot drift from index.html.

  python3 tools/check-merge-now.py             # everything
  python3 tools/check-merge-now.py --no-browser   # skip the parity section (no Chromium)
  python3 tools/check-merge-now.py --mutant NAME [--browser]
                                                  # run the suite against ONE deliberately wrong tool;
                                                  # it must FAIL (names: see MUTANTS; --browser adds the
                                                  # parity section, which catches a wrong merge rule too)

The default run also runs every mutant and requires each to be caught - a check that
passes against a wrong tool measures nothing.

Sections: 1 the merge rules on synthetic documents; 2 the fold and the notes on the
stand-in server (dry run writes nothing, --yes writes once, a second run changes
nothing, floors only rise, refusals, a concurrent write aborts, no sync code is ever
printed); 3 parity with the app's own functions; 4 the mutants.
"""
import contextlib
import copy
import functools
import http.server
import importlib.util
import io
import json
import os
import re
import socket
import sys
import threading
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "tools", "firestore-admin.py")
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"


def load_tool():
    spec = importlib.util.spec_from_file_location("fa_under_test", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------------------------ the stand-in server

class Fake:
    """Firestore's REST surface, in memory. Documents are typed values like the real thing."""

    def __init__(self):
        self.docs = {}              # (coll, id) -> {"fields", "createTime", "updateTime"}
        self.clock = 0
        self.commits = 0            # successful commits
        self.writes = 0             # documents written
        self.tx = {}
        self.race = None            # called right after a transaction read: a concurrent writer
        self.lock = threading.Lock()

    def stamp(self):
        self.clock += 1
        return "2026-11-08T%02d:%02d:%02d.000000Z" % (self.clock // 3600, (self.clock // 60) % 60, self.clock % 60)

    def put(self, coll, doc_id, plain, fa):
        self.docs[(coll, doc_id)] = {"fields": {k: fa._typed_value(v) for k, v in plain.items()},
                                     "createTime": self.stamp(), "updateTime": self.stamp()}

    def doc(self, key):
        d = self.docs.get(key)
        if not d:
            return None
        return {"name": "projects/p/databases/(default)/documents/%s/%s" % key, "fields": d["fields"],
                "createTime": d["createTime"], "updateTime": d["updateTime"]}


def start_server(fake):
    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, status, obj):
            body = json.dumps(obj).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = urllib.parse.urlparse(self.path).path
            coll = path.rsplit("/documents/", 1)[1]
            with fake.lock:
                docs = [fake.doc(k) for k in sorted(fake.docs) if k[0] == coll]
            self._send(200, {"documents": docs})

        def do_POST(self):
            path = urllib.parse.urlparse(self.path).path
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
            op = path.rsplit(":", 1)[1]
            with fake.lock:
                if op == "beginTransaction":
                    tid = "tx%d" % (len(fake.tx) + 1)
                    fake.tx[tid] = {}
                    return self._send(200, {"transaction": tid})
                if op == "rollback":
                    fake.tx.pop(body.get("transaction"), None)
                    return self._send(200, {})
                if op == "batchGet":
                    out = []
                    for name in body["documents"]:
                        key = tuple(name.split("/documents/", 1)[1].split("/", 1))
                        d = fake.doc(key)
                        if body.get("transaction"):
                            fake.tx[body["transaction"]][key] = d["updateTime"] if d else None
                        out.append({"found": d} if d else {"missing": name})
                    if body.get("transaction") and fake.race:
                        fake.race(fake)             # somebody else writes between the read and the commit
                    return self._send(200, out)
                if op == "commit":
                    return self._commit(body)
            self._send(404, {})

        def _commit(self, body):
            tid = body.get("transaction")
            if tid:
                for key, seen in fake.tx.get(tid, {}).items():
                    cur = fake.docs.get(key)
                    if (cur["updateTime"] if cur else None) != seen:
                        return self._send(409, {"error": {"status": "ABORTED", "message": "transaction aborted"}})
            staged = []
            for w in body["writes"]:
                up = w["update"]
                key = tuple(up["name"].split("/documents/", 1)[1].split("/", 1))
                cur = fake.docs.get(key)
                pre = w.get("currentDocument") or {}
                if "updateTime" in pre and (not cur or cur["updateTime"] != pre["updateTime"]):
                    return self._send(400, {"error": {"status": "FAILED_PRECONDITION", "message": "stale"}})
                if pre.get("exists") is False and cur:
                    return self._send(400, {"error": {"status": "ALREADY_EXISTS", "message": "exists"}})
                staged.append((key, w, cur))
            for key, w, cur in staged:
                up = w["update"]
                if "updateMask" in w and cur:
                    fields = dict(cur["fields"])
                    for fp in w["updateMask"]["fieldPaths"]:
                        fp = fp.strip("`")
                        if fp in up.get("fields", {}):
                            fields[fp] = up["fields"][fp]
                        else:
                            fields.pop(fp, None)
                else:
                    fields = up.get("fields", {})
                fake.docs[key] = {"fields": fields, "createTime": cur["createTime"] if cur else fake.stamp(),
                                  "updateTime": fake.stamp()}
                fake.writes += 1
            fake.commits += 1
            self._send(200, {"writeResults": [{} for _ in staged]})

    so = socket.socket(); so.bind(("127.0.0.1", 0)); port = so.getsockname()[1]; so.close()
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, port


# ------------------------------------------------------------------ fixtures

WEEK = "2026-11-02"
UNITS = ["Penal Code", "Racial Profiling", "Identity Crimes", "Professionalism and Ethics"]


def account(name, pid, xp, correct, tests, seed=1, week=WEEK):
    """A realistic plain document (the shape the app writes), with every family of field the merge touches."""
    st = {"%s|%d|k%d" % (UNITS[i % 4], i, seed): {"n": 3 + seed + i, "m": i % 2, "r": [100 * seed + i]} for i in range(6)}
    hist = [{"playedAt": 1790000000000 + seed * 10 ** 7 + i * 10 ** 5, "label": "t%d" % i, "pct": 80 + i, "xp": 50, "mode": "drill"}
            for i in range(tests)]
    d = {
        "firstName": name, "publicId": pid, "friendCode": "FC%s" % pid[:4], "avatarChar": "ninja", "onboardingComplete": True,
        "lastModified": 1790000000000, "weekKey": week, "weekPoints": 100 * seed,
        "theme": {"accent": "ink", "accentAt": 5 * seed}, "tourRev": 3, "banner": "b%d" % seed,
        "lifetime": {"points": xp, "correct": correct, "answered": correct + 40 * seed, "perfectTests": 2 * seed,
                     "fullTests": 3 * seed, "drillPlays": 4 * seed, "examPlays": seed, "gamePlays": 0,
                     "longestStreak": 5 * seed, "currentStreak": 2 * seed},
        "stats": st,
        "testStats": {"Penal Code~drill": {"plays": 2 * seed, "totalMs": 5000 * seed, "bestMs": 2000 + 100 * seed,
                                            "lastPlayedAt": 1790000100000 + seed, "lastElapsedMs": 2500, "lastPct": 90, "label": "x"}},
        "studyLog": {"2026-11-01": 3600000 * seed, "2026-11-02": 1800000},
        "unitPerfects": {"Penal Code": 3 * seed, "Racial Profiling": 5, UNITS[3]: seed},
        "unitBestPct": {"Penal Code": 80 + seed}, "unitBestMs": {"Penal Code": 90000 // seed},
        "unitRuns": {"Penal Code": seed + 1}, "unitExam": {"Penal Code": {"best": 90}},
        "gameFarthest": {"Penal Code": {"easy": seed, "hard": seed % 2 == 1}}, "flareLevels": {"ember": seed},
        "flagged": {"Penal Code|1|k%d" % seed: True}, "unitBlackStar": {},
        "testHistory": hist,
        "vrMatches": seed, "vrWins": seed - 1, "vrTop3": 0, "weeklyWins": 0, "weeklyTop3": 0, "retakenQuestions": 10 * seed, "lateHundos": 0,
        "bestTestStreak": 4 * seed, "friendsBest": seed, "dailyCorrectBest": 3 * seed,
        "friendsOut": ["f%d" % seed, "shared"], "friendsIn": [], "vrCounted": ["room%d" % seed, "roomS"],
        "classes": ["academy"], "levelFloor": 0, "rankFloor": 0, "levelWallRule": 325,
        "bigTestPassed": seed == 2, "creditsApplied": [], "mergeHold": None, "mergeHoldDone": 0,
        # real documents carry this flag; the app seeds it (and lateHundos) the first time it reads banners, which
        # the tool does not do - see the notes
        "lateHundosSeed312": True,
        "tallyBase": {"L:points": xp - 1000 * seed}, "tally": {"devA": {"L:points": 1000 * seed}},
        "unlocksShown": {"chars": ["a"], "banners": [], "fx": []},
    }
    return d


def world(fa, fake, with_base=False, old_ahead=0, same_history=False, dup_target=False, floor_ahead=False,
          note_extra=None, hold=None):
    """old (pid OLDP, 'Old') -> target (pid TGTP). Returns codes (synthetic)."""
    tgt = account("Target", "TGTP", 50000, 4000, 20, seed=2)
    old = account("Old", "OLDP", 8000, 700, 6, seed=1)
    if same_history:     # the old account's tests are already in the target's history (an earlier fold)
        tgt["testHistory"] = old["testHistory"] + tgt["testHistory"][:10]
    if hold is not None:
        tgt["mergeHold"] = hold
    codes = {"old": "TESTOLD-0001", "tgt": "TESTTGT-0002"}
    note = {"to": codes["tgt"], "at": 1790500000000}
    if note_extra:
        note.update(note_extra)
    if with_base:
        note["base"] = fa.base_of(old)
        old["lifetime"]["points"] += old_ahead          # played on the old account since the base
        old["lifetime"]["correct"] += old_ahead // 10
    fake.put("progress", codes["old"], old, fa)
    fake.put("progress", codes["tgt"], tgt, fa)
    fake.put("progress", codes["old"] + "__merge", note, fa)
    floor = copy.deepcopy(tgt)
    if floor_ahead:
        floor["lifetime"]["points"] += 100000
    fake.put("progress", codes["tgt"] + "__floor", floor, fa)
    if dup_target:
        dup = account("Target", "TGTP", 10, 1, 1, seed=3)
        fake.put("progress", "TESTDUP-0003", dup, fa)
        codes["dup"] = "TESTDUP-0003"
    return codes


def run_cmd(fa, fake, port, argv):
    fa.BASE = "http://127.0.0.1:%d/v1/projects/%s/databases/(default)/documents" % (port, fa.PROJECT)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = fa.cmd_merge_now(argv)
    return rc, buf.getvalue()


def plain_of(fa, fake, coll, doc_id):
    d = fake.docs.get((coll, doc_id))
    return fa._plain(d["fields"]) if d else None


# ------------------------------------------------------------------ the suite

def run_suite(fa, browser=False):
    fails = []

    def check(name, ok, detail=""):
        print("  %-4s %s%s" % ("PASS" if ok else "FAIL", name, ("  -> " + str(detail)) if detail and not ok else ""))
        if not ok:
            fails.append(name)

    fa.admin_ready = lambda: True
    fa._access_token = lambda: None

    # ---- 1. the merge rules, on documents -------------------------------------------------
    print("\n1. the merge rules on synthetic documents")
    tgt, old = account("Target", "TGTP", 50000, 4000, 20, seed=2), account("Old", "OLDP", 8000, 700, 6, seed=1)
    m = copy.deepcopy(tgt)
    fa.merge_leaving_account(m, old, None, 1790600000000, WEEK, {"chars": ["x"], "banners": ["y"]})
    L, TL, OL = m["lifetime"], tgt["lifetime"], old["lifetime"]
    adds = all(L[k] == TL[k] + OL[k] for k in fa.ADD_LIFETIME)
    check("counts add (XP, correct, answered, hundos, tests, plays)", adds, {k: (L[k], TL[k], OL[k]) for k in fa.ADD_LIFETIME})
    # the two fixtures share no question key by construction (the seed is in the key): make one shared
    t2, o2 = copy.deepcopy(tgt), copy.deepcopy(old)
    o2["stats"]["SHARED|1|z"] = {"n": 4, "m": 2, "r": [7, 3]}
    t2["stats"]["SHARED|1|z"] = {"n": 10, "m": 1, "r": [5]}
    fa.merge_leaving_account(t2, o2, None, 1, WEEK, {"chars": [], "banners": []})
    s = t2["stats"]["SHARED|1|z"]
    check("a question both accounts saw: n and m add, misses union sorted", s == {"n": 14, "m": 3, "r": [3, 5, 7]}, s)
    check("study days, hundos per unit and counters add",
          m["studyLog"]["2026-11-01"] == tgt["studyLog"]["2026-11-01"] + old["studyLog"]["2026-11-01"]
          and m["unitPerfects"]["Penal Code"] == tgt["unitPerfects"]["Penal Code"] + old["unitPerfects"]["Penal Code"]
          and m["vrMatches"] == tgt["vrMatches"] + old["vrMatches"] and m["retakenQuestions"] == 30)
    check("bests keep the better (streaks, best pct, best time is the LOWER, game records)",
          L["longestStreak"] == max(TL["longestStreak"], OL["longestStreak"])
          and m["unitBestPct"]["Penal Code"] == max(tgt["unitBestPct"]["Penal Code"], old["unitBestPct"]["Penal Code"])
          and m["unitBestMs"]["Penal Code"] == min(tgt["unitBestMs"]["Penal Code"], old["unitBestMs"]["Penal Code"])
          and m["gameFarthest"]["Penal Code"]["easy"] == 2 and m["gameFarthest"]["Penal Code"]["hard"] is True
          and m["bestTestStreak"] == 8 and m["testStats"]["Penal Code~drill"]["bestMs"] == 2100
          and m["testStats"]["Penal Code~drill"]["plays"] == 6)
    check("lists union (friends minus both ids, rooms), a flag either had stays, classes union",
          m["friendsOut"] == ["f2", "shared", "f1"] and m["vrCounted"] == ["room2", "roomS", "room1"]
          and m["bigTestPassed"] is True and m["classes"] == ["academy"])
    check("who the person is stays the target's (name, public id, friend code, character, theme, banner, tour rev)",
          all(m[k] == tgt[k] for k in ("firstName", "publicId", "friendCode", "avatarChar", "theme", "banner", "tourRev")))
    check("test history: both, newest first, capped at 50",
          [h["playedAt"] for h in m["testHistory"]] == sorted((h["playedAt"] for h in tgt["testHistory"] + old["testHistory"]),
                                                              reverse=True)[:50])
    check("this week's points add when both are this week", m["weekPoints"] == tgt["weekPoints"] + old["weekPoints"])
    check("the hold keeps the account as it stood (points, hundos, perfects) and the app's sets",
          m["mergeHold"]["points"] == 50000 and m["mergeHold"]["hundos"] == 4 and m["mergeHold"]["chars"] == ["x"]
          and m["mergeHold"]["perfects"] == tgt["unitPerfects"])
    t3 = copy.deepcopy(tgt); t3["mergeHold"] = {"points": 1, "perfects": {}, "chars": [], "banners": [], "hundos": 0, "at": 5}
    fa.merge_leaving_account(t3, old, None, 9, WEEK, {"chars": ["z"], "banners": []})
    check("an existing hold is kept (a second merge keeps the first baseline)", t3["mergeHold"]["points"] == 1)
    t4 = copy.deepcopy(tgt); t4["levelFloor"] = 20; o4 = copy.deepcopy(old); o4["levelFloor"] = 25
    fa.merge_leaving_account(t4, o4, None, 9, WEEK, {"chars": [], "banners": []})
    check("the level floor never falls (the higher of the two)", t4["levelFloor"] == 25)
    t5 = copy.deepcopy(tgt)
    fa.merge_leaving_account(t5, old, {"bonusLevels": 1, "extra": {"points": 500, "correct": 20, "week": WEEK, "weekPoints": 5}},
                             9, WEEK, {"chars": [], "banners": []})
    check("a note's extra is added, and bonusLevels raises the level",
          t5["lifetime"]["points"] > m["lifetime"]["points"] + 500 and fa.level_detail(t5["lifetime"]["points"])["level"]
          > fa.level_detail(m["lifetime"]["points"])["level"])
    base = fa.base_of(old)
    old2 = copy.deepcopy(old); old2["lifetime"]["points"] += 300; old2["lifetime"]["correct"] += 30
    old2["stats"]["Penal Code|0|k1"]["n"] += 2
    d = fa.progress_since_base(old2, base)
    check("a note with a base adds only the difference (progressSinceBase)",
          d["lifetime"]["points"] == 300 and d["lifetime"]["correct"] == 30 and d["lifetime"]["answered"] == 0
          and d["stats"]["Penal Code|0|k1"]["n"] == 2 and d["testHistory"] == [] and d["studyLog"]["2026-11-01"] == 0)
    check("nothing to add when the old account holds no more than its base",
          fa.nothing_to_add(fa.progress_since_base(old, base), old) and not fa.nothing_to_add(d, old2))
    ts = copy.deepcopy(tgt); ts["tally"] = {"devA": {"L:points": 1000}}; ts["tallyBase"] = {"L:points": 100}
    ts["lifetime"]["points"] += 777
    fa.tally_normalize(ts)
    check("a count raised on the server goes into the tally base (base + tallies = the count)",
          ts["tallyBase"]["L:points"] + 1000 == ts["lifetime"]["points"], ts["tallyBase"])
    check("a floor that holds more than the merged account is detected; one that holds less is not",
          fa.floor_is_ahead({"lifetime": {"points": 9}}, {"lifetime": {"points": 8}})
          and not fa.floor_is_ahead({"lifetime": {"points": 7}}, {"lifetime": {"points": 8}}))

    # ---- 2. the fold on the stand-in server ----------------------------------------------
    print("\n2. the fold, the notes and the safety, on a stand-in Firestore")
    fake = Fake()
    srv, port = start_server(fake)
    NOHOLD = ["--no-hold"]

    def fresh(**kw):
        fake.docs.clear(); fake.tx.clear(); fake.race = None
        fake.commits = fake.writes = 0
        return world(fa, fake, **kw)

    def leaked(out, codes):
        return [c for c in codes.values() if c in out]

    # 2a dry run
    codes = fresh()
    snap = copy.deepcopy(fake.docs)
    rc, out = run_cmd(fa, fake, port, ["OLDP"] + NOHOLD)
    check("a dry run writes nothing (no commit, every document identical)", fake.writes == 0 and fake.docs == snap and rc == 0, (rc, out[-300:]))
    check("a dry run prints the before/after table", "XP" in out and "before" in out and "after" in out, out[-300:])
    check("no sync code appears in the dry-run output", not leaked(out, codes), out)
    # 2b --yes
    before_t, before_old, before_floor = (copy.deepcopy(fake.docs[("progress", codes[k] + s)]) for k, s in
                                          (("tgt", ""), ("old", ""), ("tgt", "__floor")))
    rc, out = run_cmd(fa, fake, port, ["OLDP", "--yes"] + NOHOLD)
    after_t = plain_of(fa, fake, "progress", codes["tgt"])
    tgt0 = fa._plain(before_t["fields"])
    check("--yes writes (one commit, three documents)", rc == 0 and fake.commits == 1 and fake.writes == 3, (rc, fake.commits, fake.writes, out[-400:]))
    check("the target gained exactly the old account's XP and correct answers",
          after_t["lifetime"]["points"] == tgt0["lifetime"]["points"] + 8000 and after_t["lifetime"]["correct"] == tgt0["lifetime"]["correct"] + 700)
    unchanged_ok = all(fake.docs[("progress", codes["tgt"])]["fields"].get(k) == before_t["fields"].get(k)
                       for k in before_t["fields"] if k not in fa_changed(fa, tgt0, after_t))
    check("every field the merge did not change is byte-for-byte the stored value", unchanged_ok)
    check("the old account's document is untouched", fake.docs[("progress", codes["old"])] == before_old)
    floor_after = plain_of(fa, fake, "progress", codes["tgt"] + "__floor")
    check("the high-water mark was raised to the merged account and never lowered",
          floor_after["lifetime"]["points"] == after_t["lifetime"]["points"]
          and all(floor_after["lifetime"][k] >= fa._plain(before_floor["fields"])["lifetime"][k] for k in fa.ADD_LIFETIME))
    note_after = plain_of(fa, fake, "progress", codes["old"] + "__merge")
    check("the note now carries base and serverMergedAt, still points at the target and is NOT marked done",
          isinstance(note_after.get("base"), dict) and note_after.get("serverMergedAt") and note_after["to"] == codes["tgt"]
          and not note_after.get("done"))
    check("tally base follows the count (no device reads the raise as its own play)",
          after_t["tallyBase"]["L:points"] + sum(v.get("L:points", 0) for v in after_t["tally"].values()) == after_t["lifetime"]["points"])
    check("the output says what was added and that the read-back matched", "WRITTEN" in out and "hold the merged XP" in out, out[-300:])
    check("no sync code appears in the --yes output", not leaked(out, codes), out)
    # 2c idempotent
    snap = copy.deepcopy(fake.docs); commits = fake.commits
    rc, out = run_cmd(fa, fake, port, ["OLDP", "--yes"] + NOHOLD)
    check("a second merge-now of the same pair changes nothing", rc == 0 and fake.docs == snap and fake.commits == commits
          and "nothing to add" in out, (rc, out[-300:]))
    # 2d the old account moves on, then the difference is merged once and only once
    o = plain_of(fa, fake, "progress", codes["old"])
    o["lifetime"]["points"] += 250; o["lifetime"]["correct"] += 25
    fake.put("progress", codes["old"], o, fa)
    tpts = after_t["lifetime"]["points"]
    rc, out = run_cmd(fa, fake, port, ["OLDP", "--yes"] + NOHOLD)
    t_now = plain_of(fa, fake, "progress", codes["tgt"])
    check("what the old account played since is added once (the difference only)", rc == 0 and t_now["lifetime"]["points"] == tpts + 250, (rc, out[-300:]))
    rc, out = run_cmd(fa, fake, port, ["OLDP", "--yes"] + NOHOLD)
    check("...and not again", plain_of(fa, fake, "progress", codes["tgt"])["lifetime"]["points"] == tpts + 250 and "nothing to add" in out)
    # 2e refusals
    codes = fresh(dup_target=True)
    rc, out = run_cmd(fa, fake, port, ["OLDP", "--yes"] + NOHOLD)
    check("refuses when the target's public id is on more than one document, and writes nothing",
          rc != 0 and fake.writes == 0 and "exactly one" in out, (rc, out[-300:]))
    codes = fresh()
    fake.docs.pop(("progress", codes["tgt"]))
    rc, out = run_cmd(fa, fake, port, ["OLDP", "--yes"] + NOHOLD)
    check("refuses when the note points at an account that is not there", rc != 0 and fake.writes == 0, (rc, out[-200:]))
    codes = fresh()
    rc, out = run_cmd(fa, fake, port, ["NOSUCH", "--yes"] + NOHOLD)
    check("refuses an old account that names no document", rc != 0 and fake.writes == 0)
    codes = fresh()
    fake.docs.pop(("progress", codes["old"] + "__merge"))
    rc, out = run_cmd(fa, fake, port, ["OLDP", "--yes"] + NOHOLD)
    check("refuses an old account with no merge note", rc != 0 and fake.writes == 0)
    codes = fresh(same_history=True)
    rc, out = run_cmd(fa, fake, port, ["OLDP", "--yes"] + NOHOLD)
    check("refuses a note with no base when the old tests are already in the target (would count twice)",
          rc != 0 and fake.writes == 0 and "already folded" in out, (rc, out[-400:]))
    codes = fresh(floor_ahead=True)
    rc, out = run_cmd(fa, fake, port, ["OLDP", "--yes"] + NOHOLD)
    check("refuses when the high-water mark holds progress the target lacks (never lowers it)",
          rc != 0 and fake.writes == 0 and "high-water" in out, (rc, out[-300:]))
    codes = fresh()
    rc, out = run_cmd(fa, fake, port, ["OLDP", "--yes"])
    check("refuses a write that would unlock something with no hold and no --no-hold", rc != 0 and fake.writes == 0 and "mergeHold" in out, (rc, out[-300:]))
    # hold from a file
    codes = fresh()
    hp = os.path.join(os.environ.get("TMPDIR", "/tmp"), "merge-now-hold-test.json")
    json.dump({"TGTP": {"chars": ["ninja"], "banners": ["b2"]}}, open(hp, "w"))
    rc, out = run_cmd(fa, fake, port, ["OLDP", "--yes", "--hold-file", hp])
    h = plain_of(fa, fake, "progress", codes["tgt"])["mergeHold"]
    check("with a hold file the hold is written (points as they stood, the file's sets)",
          rc == 0 and h and h["points"] == 50000 and h["chars"] == ["ninja"] and h["banners"] == ["b2"], (rc, h, out[-300:]))
    os.unlink(hp)
    # bonus levels from the note
    codes = fresh(note_extra={"bonusLevels": 1})
    tp = plain_of(fa, fake, "progress", codes["tgt"])
    rc, out = run_cmd(fa, fake, port, ["OLDP", "--yes"] + NOHOLD)
    t_after = plain_of(fa, fake, "progress", codes["tgt"])
    n_after = plain_of(fa, fake, "progress", codes["old"] + "__merge")
    check("a note's bonusLevels is paid once and removed from the note",
          rc == 0 and fa.effective_level(t_after) > fa.effective_level(tp) and "bonusLevels" not in n_after, (rc, out[-300:]))
    # 2f concurrency
    codes = fresh()
    def race(f):
        key = ("progress", codes["tgt"])
        d = f.docs[key]
        d["fields"]["racer"] = {"stringValue": "a phone saved"}
        d["updateTime"] = f.stamp()
    fake.race = race
    snap_t = copy.deepcopy(fake.docs[("progress", codes["tgt"])]["fields"]["lifetime"])
    rc, out = run_cmd(fa, fake, port, ["OLDP", "--yes"] + NOHOLD)
    after = fake.docs[("progress", codes["tgt"])]
    check("a write that lands between the read and the commit aborts the merge and nothing is written",
          rc != 0 and fake.commits == 0 and after["fields"]["lifetime"] == snap_t and "racer" in after["fields"]
          and ("NOT WRITTEN" in out), (rc, out[-300:]))
    fake.race = None
    # 2g name selector
    codes = fresh()
    rc, out = run_cmd(fa, fake, port, ["name:Old", "--yes"] + NOHOLD)
    check("an old account with no public id is selected by name", rc == 0 and fake.commits == 1, (rc, out[-200:]))
    # 2h labels
    codes = fresh()
    rc, out = run_cmd(fa, fake, port, ["OLDP"] + NOHOLD)
    check("accounts are labelled acct1/acct2 and no code is printed", "acct1" in out and "acct2" in out and not leaked(out, codes))
    srv.shutdown()

    # ---- 3. the app's own functions ------------------------------------------------------
    if browser:
        fails.extend(parity(fa, check))
    return fails


def fa_changed(fa, a, b):
    return [k for k in set(a) | set(b) if a.get(k) != b.get(k)]


# ------------------------------------------------------------------ parity with index.html

def parity(fa, check):
    """Run the app's own mergeLeavingAccount / progressSinceBase / levelProgress in Chromium on the same
    documents and require the port to give the same answer, field by field."""
    from playwright.sync_api import sync_playwright
    fails_before = 0
    so = socket.socket(); so.bind(("127.0.0.1", 0)); port = so.getsockname()[1]; so.close()

    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print("\n3. parity with the app's own functions (Chromium, index.html)")
    init = ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');"
            "localStorage.setItem('class26e.intro.seen','9');}catch(e){}")
    out_fails = []
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME)
        ctx = br.new_context(viewport={"width": 834, "height": 1194})
        ctx.add_init_script(init)
        pg = ctx.new_page()
        pg.goto("http://127.0.0.1:%d/index.html" % port)
        pg.wait_for_timeout(2500)
        wk = pg.evaluate("()=>weekKeyNow()")
        levels = pg.evaluate("""()=>[0,299,300,5000,40000,100000,201060,290840,500000,1000000].map(p=>({p, lv:levelProgress(p).level, span:levelProgress(p).span, fr:levelProgress(p).fraction, atCap:levelProgress(p).atCap}))""")
        ok = all(fa.level_detail(x["p"])["level"] == x["lv"] and fa.level_detail(x["p"])["span"] == x["span"]
                 and abs(fa.level_detail(x["p"])["fraction"] - x["fr"]) < 1e-9 and fa.level_detail(x["p"])["at_cap"] == x["atCap"] for x in levels)
        check("levelProgress: level, span, fraction and cap equal the app's at ten XP totals", ok,
              [(x["p"], x["lv"], fa.level_detail(x["p"])["level"]) for x in levels if fa.level_detail(x["p"])["level"] != x["lv"]])
        xs = pg.evaluate("()=>[2,10,21,26,30,45,46,51,60,79,80].map(l=>[l,xpForLevel(l)])")
        check("xpForLevel equals the app's for eleven levels", all(fa.xp_for_level(l) == v for l, v in xs), [(l, v, fa.xp_for_level(l)) for l, v in xs if fa.xp_for_level(l) != v])

        def js_merge(target, old, note):
            return pg.evaluate("""(a)=>{
                applyLoadedData(JSON.parse(JSON.stringify(a.target)));
                const tgt = JSON.parse(JSON.stringify(store));
                applyLoadedData(JSON.parse(JSON.stringify(a.old)));
                const oldS = JSON.parse(JSON.stringify(store));
                applyLoadedData(JSON.parse(JSON.stringify(a.target)));
                const sets = { chars: [...lockedCharacterSet()], banners: [...earnedBannerSet()] };
                let leaving = JSON.parse(JSON.stringify(oldS));
                if(a.note.base) leaving = progressSinceBase(leaving, a.note.base);
                mergeLeavingAccount(leaving, a.note);
                return { tgt, oldS, sets, leaving, out: JSON.parse(JSON.stringify(store)) };
            }""", {"target": target, "old": old, "note": note})

        VOLATILE = {"lastModified", "weekStats", "prevWeekStats", "prevWeekKey", "prevWeekPoints"}

        def diff(a, b, path=""):
            if isinstance(a, dict) and isinstance(b, dict):
                bad = []
                for k in set(a) | set(b):
                    if path == "" and k in VOLATILE:
                        continue
                    if path == "mergeHold" and k == "at":
                        continue
                    if k not in a or k not in b:
                        va, vb = a.get(k), b.get(k)
                        if va is None and vb is None:
                            continue
                        bad.append("%s.%s only in %s" % (path, k, "app" if k in a else "tool"))
                        continue
                    bad += diff(a[k], b[k], path + "." + k if path else k)
                return bad
            if isinstance(a, list) and isinstance(b, list):
                if len(a) != len(b):
                    return ["%s length %d vs %d" % (path, len(a), len(b))]
                bad = []
                for i, (x, y) in enumerate(zip(a, b)):
                    bad += diff(x, y, "%s[%d]" % (path, i))
                return bad
            if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and not isinstance(b, bool):
                return [] if abs(a - b) < 1e-9 else ["%s %r vs %r" % (path, a, b)]
            return [] if a == b else ["%s %r vs %r" % (path, a, b)]

        cases = []
        t1, o1 = account("Target", "TGTP", 50000, 4000, 20, seed=2, week=wk), account("Old", "OLDP", 8000, 700, 6, seed=1, week=wk)
        cases.append(("synthetic pair, whole add", t1, o1, {"to": "x", "at": 1}))
        t2, o2 = copy.deepcopy(t1), copy.deepcopy(o1)
        o2["stats"]["SHARED|1|z"] = {"n": 4, "m": 2, "r": [7, 3]}
        t2["stats"]["SHARED|1|z"] = {"n": 10, "m": 1, "r": [5]}
        o2["testHistory"] = t2["testHistory"][:3] + o2["testHistory"]
        o2["friendsOut"] = ["shared", "TGTP", "OLDP", "q"]
        o2["classes"] = ["academy", "ifc"]
        cases.append(("overlapping history, shared question, classes, friends", t2, o2, {"to": "x", "at": 1}))
        t3, o3 = copy.deepcopy(t1), copy.deepcopy(o1)
        cases.append(("bonus level and extra on the note", t3, o3,
                      {"to": "x", "at": 1, "bonusLevels": 2, "extra": {"points": 900, "correct": 30, "week": wk, "weekPoints": 40}}))
        t4, o4 = copy.deepcopy(t1), copy.deepcopy(o1)
        t4["unitPerfects"] = {u: 12 for u in UNITS}
        o4["unitPerfects"] = {u: 30 for u in UNITS}
        cases.append(("hundos that complete badges, bonus at a badge wall", t4, o4, {"to": "x", "at": 1, "bonusLevels": 1}))
        t5 = copy.deepcopy(t1); t5["mergeHold"] = {"points": 3, "perfects": {}, "chars": [], "banners": [], "hundos": 0, "at": 99999999999999}
        cases.append(("target already holds a live hold", t5, copy.deepcopy(o1), {"to": "x", "at": 1}))
        t6, o6 = copy.deepcopy(t1), copy.deepcopy(o1)
        base = fa.base_of(o6)
        o6["lifetime"]["points"] += 321; o6["lifetime"]["correct"] += 31
        o6["stats"]["Penal Code|0|k1"]["n"] += 3; o6["studyLog"]["2026-11-01"] += 777
        o6["testHistory"].insert(0, {"playedAt": 1799999999999, "label": "new", "pct": 100, "xp": 1, "mode": "drill"})
        cases.append(("note with base: only the difference", t6, o6, {"to": "x", "at": 1, "base": base}))
        for name, tg, od, note in cases:
            res = js_merge(tg, od, note)
            eff = fa.progress_since_base(res["oldS"], note["base"]) if note.get("base") else res["oldS"]
            if note.get("base"):
                bad = diff(res["leaving"], eff)
                check("progressSinceBase equals the app's (%s)" % name, not bad, bad[:4])
            py = copy.deepcopy(res["tgt"])
            fa.merge_leaving_account(py, eff, note, 1, wk, res["sets"])
            bad = diff(res["out"], py)
            check("merged document equals the app's, every field (%s)" % name, not bad, bad[:6])
        # the base the tool writes must make the app add nothing
        first = js_merge(t1, o1, {"to": "x", "at": 1})
        res = js_merge(t1, o1, {"to": "x", "at": 1, "base": fa.base_of(first["oldS"])})
        before_pts = res["tgt"]["lifetime"]["points"]
        check("a note carrying the base the tool writes makes the app add nothing a second time",
              res["out"]["lifetime"]["points"] == before_pts and res["out"]["lifetime"]["correct"] == res["tgt"]["lifetime"]["correct"],
              (before_pts, res["out"]["lifetime"]["points"]))
        br.close()
    srv.shutdown()
    return out_fails


# ------------------------------------------------------------------ mutants

def mutants():
    """name -> a function that makes `fa` WRONG in one specific way."""
    def wrong_add(fa):
        real = fa.merge_leaving_account

        def bad(dst, src, note=None, now_ms=0, week_key=None, hold_sets=None):
            before = dict(dst.get("lifetime") or {})
            r = real(dst, src, note, now_ms, week_key, hold_sets)
            dst["lifetime"]["points"] = max(fa._num(before.get("points")), fa._num((src.get("lifetime") or {}).get("points")))
            return r
        fa.merge_leaving_account = bad

    def wrong_union(fa):
        real = fa.merge_leaving_account

        def bad(dst, src, note=None, now_ms=0, week_key=None, hold_sets=None):
            r = real(dst, src, note, now_ms, week_key, hold_sets)
            dst["friendsOut"] = list(src.get("friendsOut") or [])
            return r
        fa.merge_leaving_account = bad

    def wrong_best(fa):
        real = fa.merge_leaving_account

        def bad(dst, src, note=None, now_ms=0, week_key=None, hold_sets=None):
            t = dict(dst.get("unitBestMs") or {})
            r = real(dst, src, note, now_ms, week_key, hold_sets)
            for u, v in (src.get("unitBestMs") or {}).items():
                dst["unitBestMs"][u] = max(fa._num(t.get(u)), fa._num(v))
            return r
        fa.merge_leaving_account = bad

    def no_base(fa):
        fa.base_of = lambda old: {}

    def floor_not_raised(fa):
        fa._floor_fields = lambda merged_fields, floor_raw: dict(floor_raw["fields"]) if floor_raw else merged_fields

    def floor_lowered(fa):
        real = fa._floor_fields

        def bad(merged_fields, floor_raw):
            f = dict(merged_fields)
            f["lifetime"] = fa._typed_value({"points": 1})
            return f
        fa._floor_fields = bad

    def no_unique_check(fa):
        real = fa.plan_merge_now
        fa.plan_merge_now = lambda *a, **k: real(*a, **dict(k, target_pid_count=1))

    def no_fold_guard(fa):
        real = fa.plan_merge_now
        fa.plan_merge_now = lambda *a, **k: real(*a, **dict(k, force=True))

    def no_precondition(fa):
        real = fa._post

        def bad(path, body, timeout=60):
            if path == ":commit":
                body = {"writes": [{k: v for k, v in w.items() if k != "currentDocument"} for w in body["writes"]]}
            return real(path, body, timeout)
        fa._post = bad

    def whole_not_delta(fa):
        fa.progress_since_base = lambda src, base: json.loads(json.dumps(src))

    return {"wrong_add": wrong_add, "wrong_union": wrong_union, "wrong_best": wrong_best, "no_base": no_base,
            "floor_not_raised": floor_not_raised, "floor_lowered": floor_lowered, "no_unique_check": no_unique_check,
            "no_fold_guard": no_fold_guard, "no_precondition": no_precondition, "whole_not_delta": whole_not_delta}


MUTANTS = mutants()


def main():
    args = sys.argv[1:]
    if "--mutant" in args:
        name = args[args.index("--mutant") + 1]
        fa = load_tool()
        MUTANTS[name](fa)
        print("running the suite against the deliberately wrong tool %r (it must FAIL)" % name)
        fails = run_suite(fa, browser="--browser" in args)
        print("\n%s: %d failing line(s)" % (name, len(fails)))
        return 1 if fails else 0
    browser = "--no-browser" not in args
    fa = load_tool()
    fails = run_suite(fa, browser=browser)
    print("\n4. the mutants (each deliberately wrong tool must be caught)")
    quiet = io.StringIO()
    missed = []
    for name in MUTANTS:
        fam = load_tool()
        MUTANTS[name](fam)
        with contextlib.redirect_stdout(quiet):
            got = run_suite(fam, browser=False)
        print("  %-4s %s%s" % ("PASS" if got else "FAIL", "caught: " + name, ("  (%d line(s) fail)" % len(got)) if got else "  NOT CAUGHT"))
        if not got:
            missed.append(name)
    allfails = fails + ["mutant not caught: " + m for m in missed]
    print("\n%s" % ("ALL PASS" if not allfails else "%d FAILED: %s" % (len(allfails), "; ".join(allfails))))
    return 1 if allfails else 0


if __name__ == "__main__":
    sys.exit(main())
