"""Does `find` actually produce a usable answer?

EVERY CODE AND NAME IN HERE IS INVENTED. Real-looking fixtures got
pasted into a chat once and read as somebody's actual account, so they
all say FAKE- now. They keep the real format (the sync-code alphabet
has no 0/O/1/I) so the shape assertions stay honest.

Everything here is the real code path - auth, paging, the field mask,
the typed-value flattening, the printing - with only the HTTP call
stubbed, returning documents shaped exactly as Firestore returns them.
What it cannot cover is Google accepting a real key and the rules
letting the listing through; those need the key.
"""
import importlib.util, io, json, os, sys, contextlib

spec = importlib.util.spec_from_file_location(
    "fa", os.path.join(os.path.dirname(os.path.abspath(__file__)), "firestore-admin.py"))
fa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fa)

MS = 1790400000000  # inside 2026


def doc(name, code, points, correct, when):
    """A `progress` document as the REST API really returns one."""
    return {
        "name": "projects/p/databases/(default)/documents/progress/" + code,
        "fields": {
            "firstName": {"stringValue": name},
            # lifetime is a MAP - the case that used to print <mapValue>
            "lifetime": {"mapValue": {"fields": {
                "points": {"integerValue": str(points)},
                "correct": {"integerValue": str(correct)},
                # a nested array, to prove recursion does not blow up
                "recent": {"arrayValue": {"values": [
                    {"integerValue": "1"}, {"integerValue": "2"}]}},
            }}},
            "lastModified": {"doubleValue": when},
        },
    }


PAGE1 = {"documents": [
    doc("testuser", "FAKE-TEST", 14200, 903, MS),
    doc("TestUser", "FAKE-DUPE", 0, 0, MS + 86400000),   # the minted duplicate
    doc("Madison", "FAKE-MADI", 5000, 300, MS),
], "nextPageToken": "tok1"}
PAGE2 = {"documents": [doc("Dave", "FAKE-DAVE", 77, 9, MS)]}

calls = []


def fake_call(method, url, timeout=30):
    calls.append(url)
    return 200, json.dumps(PAGE2 if "pageToken=tok1" in url else PAGE1)


fa._call = fake_call
fa.admin_ready = lambda: True          # pretend a key is configured
fa._access_token = lambda: "test-token"

# ---- 1. the typed-value flattening, including the map that was broken
flat = fa._plain(PAGE1["documents"][0]["fields"])
print("flattened lifetime ->", flat["lifetime"])
assert flat["lifetime"]["points"] == 14200, flat
assert flat["lifetime"]["correct"] == 903
assert flat["lifetime"]["recent"] == [1, 2], "arrays must recurse too"
assert "<mapValue>" not in json.dumps(flat), "the old bug is back"
print("  no <mapValue> anywhere:", "<mapValue>" not in json.dumps(flat))

# ---- 2. paging: a nextPageToken must be followed
rows = fa.docs("progress", mask=["firstName", "lifetime", "lastModified"])
print("rows across pages ->", len(rows), [c for c, _ in rows])
assert len(rows) == 4, rows

# ---- 3. the field mask is actually sent, and repeated not joined
assert "mask.fieldPaths=firstName" in calls[0], calls[0]
assert "mask.fieldPaths=lifetime" in calls[0], calls[0]
assert "mask.fieldPaths=firstName%2C" not in calls[0], "mask must repeat, not join"
print("  mask sent as repeated params: yes")

# ---- 4. THE ACTUAL LOOKUP: a username in, a code out
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    rc = fa.cmd_find("testuser")
out = buf.getvalue()
print("\n--- find testuser ---")
print(out.rstrip())
print("--- rc =", rc, "---\n")

assert rc == 0
assert "FAKE-TEST" in out, "the real code must be printed"
assert "14200" in out and "903" in out, "the numbers to identify them by"
assert "FAKE-DUPE" in out, "the duplicate account must show too"
assert "<mapValue>" not in out
assert "Dave" not in out and "Madison" not in out, "must not print everyone"
assert "More than one account" in out, "two hits must be called out"
print("code returned, both accounts shown, duplicate warning present")

# ---- 5. a miss must not claim success
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    rc = fa.cmd_find("nobody-by-this-name")
assert rc == 1, "a miss must exit non-zero"
print("a name with no account -> rc 1, no false hit")

# ---- 6. WITHOUT a key it must not pretend. It must say so.
fa.admin_ready = lambda: False
fa._call = lambda m, u, timeout=30: (200, json.dumps({"documents": [
    {"name": ".../leaderboard/cx48es4mai23",
     "fields": {"firstName": {"stringValue": "sivad"},
                "correct": {"integerValue": "903"}}}]}))
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    fa.cmd_find("testuser")
out = buf.getvalue()
assert "No admin key configured" in out
assert "public id" in out.lower()
assert "NOT a sync code" in out
assert "QZ4K" not in out, "it must not invent a code it cannot see"
print("no key -> says so, labels the public id, invents nothing")

print("\nALL PASS")
print("Untested without a real key: Google issuing a token for it, and")
print("`progress` returning 200 rather than 403 under that token.")
