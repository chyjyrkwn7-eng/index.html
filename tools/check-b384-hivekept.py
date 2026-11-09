"""Build 384 r17: whoever unlocked the Hive under the old rule keeps it, and its challenge reads as done.
Madison: "People who already unlocked the hive, they will keep it and it will say they already did the virtual room challenge."
Up to build 383 the Hive was "Answer 500 questions in a single day" (dayAnsweredBest >= 500); 384 makes it "Host 3 Virtual Room matches".
 (1) an existing account (no hiveMoved384) whose best day is 500+ and that has hosted nothing: the Hive is unlocked, the
     challenge reads done (3 of 3), and the account now carries "hive" in legacyChars and hiveMoved384;
 (2) an existing account wearing the Hive (best day under 500): the same;
 (3) an existing account with a best day under 500, not wearing it: still locked, 0 of 3;
 (4) the move runs once: an account already moved (hiveMoved384) whose best day reaches 500 later stays locked;
 (5) a brand-new account is born moved (hiveMoved384 true), so the old route never opens for it;
 (6) no page errors.
Run:  python3 tools/check-b384-hivekept.py   (--against OLD/index.html must FAIL)"""
import json, os, sys, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
if "--against" in sys.argv:
    body = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
    cb.BODY = cb.INSET_RE.sub("0px", body).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
BASE = json.loads(cb.USED_ACCOUNT)
def seed(**kw):
    a = dict(BASE); a.pop("hiveMoved384", None); a["vrHosted"] = 0
    a["legacyChars"] = [x for x in (a.get("legacyChars") or []) if x != "hive"]
    a.update(kw); return json.dumps(a)
READ = """()=>{ const f = CHARACTER_FEATS.busyday300; return { locked: isLockedCharacter('hive'), done: !!f.done(), have: f.have(), need: f.need,
  legacy: (store.legacyChars || []).indexOf('hive') >= 0, moved: store.hiveMoved384 === true }; }"""
CASES = [
    ("(1) best day 600, hosted nothing", seed(dayAnsweredBest=600, avatarChar=BASE.get("avatarChar")), True),
    ("(2) wearing the Hive, best day 120", seed(dayAnsweredBest=120, avatarChar="hive"), True),
    ("(3) best day 120, not wearing it", seed(dayAnsweredBest=120, avatarChar=BASE.get("avatarChar") if BASE.get("avatarChar") != "hive" else "fox"), False),
    ("(4) already moved, best day 600 later", seed(dayAnsweredBest=600, hiveMoved384=True, avatarChar=BASE.get("avatarChar") if BASE.get("avatarChar") != "hive" else "fox"), False),
]
with sync_playwright() as pw:
    br = pw.chromium.launch()
    for name, sd, kept in CASES:
        ctx, pg = cb.booted(br, 440, 956, seed=sd)
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        r = pg.evaluate(READ)
        if kept:
            chk(name + ": the Hive stays unlocked and the challenge reads done (%s)" % r, (not r["locked"]) and r["done"] and r["have"] == r["need"] and r["legacy"] and r["moved"], r)
        else:
            chk(name + ": still locked, nothing done (%s)" % r, r["locked"] and not r["done"] and r["have"] == 0 and not r["legacy"], r)
        chk(name + ": (6) no page errors", not errs, errs)
        ctx.close()
    # (5) a brand-new account
    ctx, pg = cb.booted(br, 440, 956)
    pg.evaluate("()=>{ try{ localStorage.clear(); }catch(e){} }")
    pg.reload(); pg.wait_for_timeout(2600)
    r = pg.evaluate("()=>({ moved: store.hiveMoved384 === true })")
    chk("(5) a brand-new account is born moved (%s)" % r, r["moved"], r)
    ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
