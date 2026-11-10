"""Build 384 r13: friend codes find people who are not on the academy board.
Madison: "Friends codes aren't working, they are saying it says no one in the class has that code." The lookup read only the academy's
leaderboard rows this device already held: a person in Fire Code alone has no row, and a board read before somebody joined never had
them. On the academy account with an empty board:
 (1) a code carried in somebody's presence beat (`f`) finds them: the request goes out (friendsOut), and, as they have no board row, to
     their mailbox;
 (2) this device's own beat carries its friend code;
 (3) a code in neither is asked of the cloud once (a one-document query on `fcode`), and a person found there is requested;
 (4) a code nobody has still says so (and asks the cloud only once), in words that name the classes;
 (5) no page errors.
Run:  python3 tools/check-b384-friendcode.py   (--against OLD/index.html must FAIL)"""
import os, sys, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
if "--against" in sys.argv:
    body = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
    cb.BODY = cb.INSET_RE.sub("0px", body).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
with sync_playwright() as pw:
    br = pw.chromium.launch()
    ctx, pg = cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:140]))
    # (1) a presence-only person
    r = pg.evaluate("""async ()=>{ leaderboardRows = []; store.friendsOut = [];
      presenceClasses = { pubfireonly01: { k: 'ifc', n: 'Sam', v: 'ninja', f: 'KQR-234' } };
      const sent = []; const real = sendToInbox; sendToInbox = (p, m) => { sent.push([p, m && m.type]); };
      const res = await sendFriendRequestAsync('kqr-234'); sendToInbox = real;
      return { res, out: (store.friendsOut || []).slice(), sent }; }""")
    chk("(1) a code in a presence beat finds a person with no board row (%s)" % r["res"], r["res"].get("ok") and r["res"].get("name") == "Sam" and "pubfireonly01" in r["out"] and r["sent"] == [["pubfireonly01", "friendreq"]], r)
    # (2) own beat
    b = pg.evaluate("()=>({ beat: presenceClassesValue(), code: friendCodeOf() })")
    chk("(2) this device's beat carries its friend code (%s)" % b["beat"], b["beat"].get("f") == b["code"], b)
    # (3) cloud query on a miss
    r = pg.evaluate("""async ()=>{ leaderboardRows = []; store.friendsOut = []; presenceClasses = {};
      let asked = 0, field = null;
      fbDb = { collection: (n) => ({ where: (f, op, v) => { field = [n, f, op, v]; return { limit: () => ({ get: () => { asked++; const doc = { id: 'pubcloud0002', data: () => ({ firstName: 'Lee', fcode: v, level: 3, badges: 0, weekPoints: 0, avatarChar: 'ninja' }) };
        return Promise.resolve({ forEach: fn => fn(doc) }); } }) }; } }) };
      const res = await sendFriendRequestAsync('MNP-567');
      return { res, asked, field, out: (store.friendsOut || []).slice() }; }""")
    chk("(3) a code not held locally is asked of the cloud once, and the person found is requested (%s)" % r["res"], r["res"].get("ok") and r["res"].get("name") == "Lee" and r["asked"] == 1 and r["field"] == ["leaderboard", "fcode", "==", "MNP-567"] and "pubcloud0002" in r["out"], r)
    # (4) nobody has it
    r = pg.evaluate("""async ()=>{ leaderboardRows = []; store.friendsOut = []; presenceClasses = {}; let asked = 0;
      fbDb = { collection: () => ({ where: () => ({ limit: () => ({ get: () => { asked++; return Promise.resolve({ forEach: () => {} }); } }) }) }) };
      const res = await sendFriendRequestAsync('XYZ-789'); return { res, asked }; }""")
    chk("(4) a code nobody has is refused after one cloud ask (%s)" % r["res"].get("why"), (not r["res"].get("ok")) and r["asked"] == 1 and "class" in (r["res"].get("why") or ""), r)
    chk("(5) no page errors", not errs, errs)
    br.close()
print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
