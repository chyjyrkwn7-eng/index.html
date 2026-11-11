#!/usr/bin/env python3
"""Build 384.39: two classmates can add each other.

The owner: "My buddies are using the app, they are saying they can't add each other." Two phones, each a brand-new account made
through the REAL sign-up (the installed app, Police Academy, the 21-press walk), on one shared in-memory Firestore
(tools/b384_cloud_lib.py: documents, queries, listeners, the real rules' refusal to list `progress`) with a class board that
already has other people on it - which is what a real class looks like, and what the old check (an empty board) never had.

What a real pair of phones hit on 384.34:
 * a request typed in by CODE went only into the sender's board row; the other phone reads the board once in fifteen minutes and
   a Friends screen opened with rows already held read nothing, so the request never appeared ("Request sent" on one phone,
   nothing on the other);
 * so two buddies who each typed the other's code ended with a request each way and nobody ever accepting;
 * a person who had declined (or removed) somebody could never see that person's new request;
 * the code field cut a pasted line to 7 characters; a Firestore refusal (a day's quota spent) was shown as "nobody has that
   code".

Asserted by shape, read off the pages (no strings typed as expectations beyond the messages being DIFFERENT from "nobody has it"):
 (1) both accounts are whole after sign-up: a sync code, a public id, a friend code of the right shape, a row on the board;
 (2) B types A's code (lower case, spaces, a typographic dash) into the field: A has the request within seconds, with no tap, and
     the Friends screen opened on A shows it with an Accept button;
 (3) A types B's code: that is A's yes - both are friends, on both phones, with no further tap;
 (4) a pasted line (a whole sentence with the code in it, six characters with no dash, a code with a trailing newline or space,
     a fullwidth dash) reads as the one code, and a code with an O, I, 0 or 1 in it says so (a different message from the
     generic one);
 (5) a request after a decline is seen (the mailbox's request is new), and accepting works;
 (6) a refused cloud (resource-exhausted) is not "nobody has that code": a code nobody holds, asked of the cloud, says so
     differently; and a request whose mailbox write is refused says so;
 (7) no sync code in any cloud document (the board, presence, the inboxes).

  python3 tools/check-b384-addfriend.py [--against OLD/index.html]      (must FAIL on 384.34)"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import b384_flow_lib as L
import b384_cloud_lib as C
from playwright.sync_api import sync_playwright

args = sys.argv[1:]
SRC = L.load_src(args[args.index("--against") + 1] if "--against" in args else None)
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond)
    print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:500], flush=True)

now = int(time.time() * 1000)
SEED = {"leaderboard": {}}
for i in range(6):   # a class already on the board: every phone holds rows before either of these two joins
    SEED["leaderboard"]["cls%08dxx" % i] = {"firstName": "Class%d" % i, "avatarChar": "ninja", "level": 5 + i, "badges": 1, "mystery": 0, "hundos": 1,
        "correct": 100 + i, "week": "2026-W46", "weekPoints": 10, "fcode": "KM%s-23%d" % ("ABCDEF"[i], i), "freq": [], "facc": [],
        "lastModified": now - 3600000, "xp": 100, "tests": 1}
import re
# version.json answers with the build of the page under test, so an older page (--against) is not told to update itself
BUILD = re.search(r'const APP_BUILD = "([^"]+)"', SRC).group(1)
cloud, srv, url = C.make_cloud(SEED, L.patched(SRC, (62, 0, 34, 0)).encode(), L.ROOT, build=BUILD)

def device(br, name):
    ctx = br.new_context(viewport={"width": 440, "height": 956}, device_scale_factor=2, user_agent=L.UA["iphone-safari"], has_touch=True, is_mobile=False)
    ctx.add_init_script("Object.defineProperty(navigator,'maxTouchPoints',{get:()=>5,configurable:true});")
    ctx.add_init_script(L.STANDALONE)
    ctx.add_init_script(C.init_script(url, name)); ctx.add_init_script(C.CLIENT)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.goto(url + "/index.html"); pg.wait_for_timeout(2500)
    pg.evaluate("()=>{ const s=document.getElementById('splashscreen'); if(s) s.remove(); }"); pg.wait_for_timeout(500)
    return pg, errs

def until(pg, js, tries=40, step=250, arg=None):
    v = None
    for _ in range(tries):
        v = pg.evaluate(js, arg) if arg is not None else pg.evaluate(js)
        if v: return v
        pg.wait_for_timeout(step)
    return v

def add_by_typing(pg, text):
    """what a person does: open Friends, put the text in the field, tap Send; returns the toasts that came up"""
    pg.evaluate("()=>{ document.querySelectorAll('.friend-moment').forEach(e => e.remove()); }")
    pg.evaluate("()=>{ window.__toasts = []; if(!window.__toastHook){ window.__toastHook = 1; const o = showToast; showToast = function(){ window.__toasts.push(String(arguments[0])); return o.apply(this, arguments); }; } }")
    if not pg.evaluate("()=>!!document.querySelector('#stage > .screen-friends')"):
        pg.evaluate("()=>showFriends()"); pg.wait_for_timeout(1200)
    pg.fill(".friend-add-input", text)
    shown = pg.evaluate("()=>document.querySelector('.friend-add-input').value")
    pg.click(".friend-send"); pg.wait_for_timeout(2500)
    return shown, pg.evaluate("()=>window.__toasts.slice()")

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=L.CHROME)
    (A, errsA), (B, errsB) = device(br, "A"), device(br, "B")
    # ---- (1) two brand-new accounts through the real sign-up
    for pg, nm in ((A, "Alice"), (B, "Bobby")):
        r = L.walk_signup(pg, nm)
        print("  signed up %s: %d presses, onboarded %s" % (nm, r["taps"], r["onboarded"]), flush=True)
    A.wait_for_timeout(3000); B.wait_for_timeout(3000)
    ia = A.evaluate("()=>({ code: syncCode, pub: store.publicId, fc: friendCodeOf(), rows: leaderboardRows.length, opt: !!store.leaderboardOptIn })")
    ib = B.evaluate("()=>({ code: syncCode, pub: store.publicId, fc: friendCodeOf(), rows: leaderboardRows.length, opt: !!store.leaderboardOptIn })")
    SYNC = [ia["code"], ib["code"]]
    import re
    FC = re.compile(r"^[A-HJ-NP-Z2-9]{3}-[A-HJ-NP-Z2-9]{3}$")
    chk("(1) both new accounts have a sync code, a public id, a friend code and class sharing on",
        all(x["code"] and x["pub"] and FC.match(x["fc"]) and x["opt"] for x in (ia, ib)) and ia["fc"] != ib["fc"], {k: (ia[k] if k in ("rows", "opt") else bool(ia[k])) for k in ia})
    rows = cloud.data.get("leaderboard", {})
    chk("(1) both are on the class board with their friend code, and each phone already held the class's rows (a stale board)",
        rows.get(ia["pub"], {}).get("fcode") == ia["fc"] and rows.get(ib["pub"], {}).get("fcode") == ib["fc"] and ia["rows"] >= 6 and ib["rows"] >= 6, {"onboard": len(rows), "A rows": ia["rows"], "B rows": ib["rows"]})
    # ---- (2) B types A's code, messily; A is told with no tap
    messy = "  " + ia["fc"].lower().replace("-", " – ") + " "
    shown, toasts = add_by_typing(B, messy)
    chk("(2) B's messy typing (lower case, spaces, a typographic dash) is read as A's code and sent (%s)" % (toasts[:1],),
        shown == ia["fc"] and len(toasts) >= 1 and toasts[0] != "" and B.evaluate("()=>store.friendsOut.indexOf(%s) >= 0" % json.dumps(ia["pub"])), {"shown": shown == ia["fc"], "toasts": toasts})
    got = until(A, "(p)=>incomingFriendRequests().some(e=>e.pub===p)", 40, 250, ib["pub"])
    chk("(2) A has B's request within ten seconds, without opening anything, though A's board was read before B joined", got, {"pending": A.evaluate("()=>incomingFriendRequests().length")})
    A.evaluate("()=>showFriends()"); A.wait_for_timeout(1500)
    nrows = A.evaluate("()=>document.querySelectorAll('.friend-sect-pending .friend-row').length")
    nacc = A.evaluate("()=>document.querySelectorAll('.friend-sect-pending .friend-act').length")
    chk("(2) A's Friends screen shows one request with its buttons", nrows == 1 and nacc >= 2, {"rows": nrows, "buttons": nacc})
    # ---- (3) A types B's code: that is A's yes
    shown, toasts = add_by_typing(A, ib["fc"])
    both = until(A, "(p)=>friendPublicIds().indexOf(p) >= 0", 20, 250, ib["pub"])
    both_b = until(B, "(p)=>friendPublicIds().indexOf(p) >= 0", 40, 250, ia["pub"])
    chk("(3) A typing B's code (B has already asked) makes them friends on A's phone", both, {"toasts": toasts})
    chk("(3) and on B's phone, with no further tap", both_b, {"B friends": B.evaluate("()=>friendPublicIds()"), "B in": B.evaluate("()=>store.friendsIn")})
    # ---- (4) what is pasted
    fa = ia["fc"]
    if A.evaluate("()=>typeof friendCodeFromText") == "function":
        read = lambda t: B.evaluate("(t)=>friendCodeFromText(t)", t)
    else:   # 384.34 has no reader: the closest it has is the typed field, so its answer is "no code"
        read = lambda t: {}
    variants = ["my code is " + fa, fa.replace("-", ""), fa + "\n", fa + " ", fa.replace("-", "–"), fa.replace("-", "－"), fa.lower(), "  " + fa.replace("-", " ") + "  "]
    reads = [read(v).get("code") for v in variants]
    chk("(4) a sentence, six characters, a trailing newline or space, a typographic or fullwidth dash, lower case: all read as the one code", all(r == fa for r in reads), reads)
    for v in ("my code is " + fa, fa.replace("-", ""), fa.replace("-", "–")):
        B.evaluate("()=>{ if(!document.querySelector('#stage > .screen-friends')) showFriends(); }"); B.wait_for_timeout(300)
        B.fill(".friend-add-input", v)
        seen = B.evaluate("()=>document.querySelector('.friend-add-input').value")
        chk("(4) the field shows a pasted %r as the code" % v[:14], seen == fa, seen)
    generic = read("hello").get("why")
    bad = read("OBC-234")
    chk("(4) a code with an O in it says so, in words that differ from the generic one", bad.get("why") and bad.get("why") != generic and not bad.get("code"), {"bad": bad, "generic": generic})
    # ---- (5) a request after a decline is seen
    # the decline case on the same two phones: clear both friend lists, then B asks, A declines, B asks again
    for pg in (A, B):
        pg.evaluate("()=>{ store.friendsIn = []; store.friendsOut = []; store.friendsDeclined = []; saveStore(); pushToCloud(); }")
    # wait until each phone's row is up without the other in it, then refresh both phones' view of the other's row
    for _ in range(40):
        r = cloud.data.get("leaderboard", {})
        if not (r.get(ia["pub"], {}).get("facc") or r.get(ib["pub"], {}).get("facc")): break
        A.wait_for_timeout(250)
    for pg in (A, B): pg.evaluate("()=>{ boardFetchedAt = 0; fetchBoardForInvites(true); }")
    A.wait_for_timeout(2500)
    shown, toasts = add_by_typing(B, fa)
    until(A, "(p)=>incomingFriendRequests().some(e=>e.pub===p)", 40, 250, ib["pub"])
    A.evaluate("()=>{ declineFriendRequest(%s); }" % json.dumps(ib["pub"])); A.wait_for_timeout(1500)
    gone = A.evaluate("()=>incomingFriendRequests().length") == 0
    B.evaluate("()=>{ store.friendsOut = []; }")
    shown, toasts = add_by_typing(B, fa); B.wait_for_timeout(500)
    again = until(A, "(p)=>incomingFriendRequests().some(e=>e.pub===p)", 40, 250, ib["pub"])
    chk("(5) A declined B; B asks again: A sees the new request (the decline was of the first)", gone and again, {"declinedGone": gone, "again": again})
    A.evaluate("()=>{ document.querySelectorAll('.friend-moment').forEach(e => e.remove()); showFriends(); }"); A.wait_for_timeout(1200)
    A.evaluate("()=>{ document.querySelectorAll('.friend-moment').forEach(e => e.remove()); }")
    if A.evaluate("()=>!!document.querySelector('.friend-sect-pending .friend-act')"):
        A.click(".friend-sect-pending .friend-act >> nth=0"); A.wait_for_timeout(1500)
    chk("(5) A taps Accept: they are friends", A.evaluate("(p)=>friendPublicIds().indexOf(p) >= 0", ib["pub"]) and until(B, "(p)=>friendPublicIds().indexOf(p) >= 0", 40, 250, ia["pub"]), "")
    # ---- (5b) a classmate in Fire Code alone has no board row: their code is in their presence beat, and this phone may not have heard it yet
    cloud.data.setdefault("vrooms", {}).setdefault("presence-v1", {"kind": "presence"}).setdefault("c", {})["zzfireonly01"] = {"k": "ifc", "n": "Fay", "f": "FYR-234"}
    B.evaluate("()=>{ presenceClasses = null; }")
    fire = B.evaluate("async()=>{ const r = await sendFriendRequestAsync('fyr 234'); return { ok: !!r.ok, name: r.name || '', out: store.friendsOut.indexOf('zzfireonly01') >= 0 }; }")
    chk("(5b) a code held only in somebody's presence beat (Fire Code alone, no board row) is found even before this phone has heard the beat", fire["ok"] and fire["out"] and fire["name"] == "Fay", fire)
    # ---- (6) a refused cloud, and a refused write
    B.evaluate("()=>{ window.__toasts = []; }")
    nobody = B.evaluate("async()=>{ const r = await sendFriendRequestAsync('KQR-234'); return { notFound: !!r.notFound, why: r.why || '' }; }")
    cloud.fail = "resource-exhausted"
    refused = B.evaluate("async()=>{ const r = await sendFriendRequestAsync('KQR-235'); return { notFound: !!r.notFound, ok: !!r.ok, why: r.why || '' }; }")
    chk("(6) with the cloud refusing (a day's quota spent), an unknown code is not reported as 'nobody has that code' (%s)" % refused.get("why", "")[:60],
        nobody["notFound"] and (not refused["notFound"]) and (not refused["ok"]) and refused["why"] and refused["why"] != nobody["why"], {"served empty": nobody, "refused": refused})
    cloud.fail = None
    # a third, unseen classmate; the mailbox write is refused after the code is found locally
    B.evaluate("()=>{ leaderboardRows = leaderboardRows.concat([{ pub: 'zzclassmate01', firstName: 'Zed', fcode: 'ZZD-234', freq: [], facc: [], level: 3, badges: 0, avatarChar: 'ninja' }]); showFriends(); }"); B.wait_for_timeout(1200)
    cloud.fail = "resource-exhausted"
    shown, toasts = add_by_typing(B, "ZZD-234")
    B.wait_for_timeout(1500)
    toasts = B.evaluate("()=>window.__toasts.slice()")
    cloud.fail = None
    chk("(6) a request whose mailbox write the cloud refuses says so after the 'sent' (%d toasts)" % len(toasts), len(toasts) >= 2 and toasts[-1] != toasts[0], toasts)
    # ---- (7) no sync code in any cloud document
    chk("(7) no sync code anywhere in the shared cloud's board, presence or inboxes (only in the accounts' own documents)",
        not any(c and c in json.dumps({k: v for k, v in cloud.data.items() if k != "progress"}) for c in SYNC), "")
    chk("(8) no page errors", not errsA and not errsB, [errsA[:2], errsB[:2]])
    br.close()
print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
