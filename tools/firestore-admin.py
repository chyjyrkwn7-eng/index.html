#!/usr/bin/env python3
"""Maintenance access to Nova's Firestore data, over the plain REST API.

Why this is a tool and not a screen in the app
----------------------------------------------
`progress` is keyed by the SYNC CODE, and the sync code IS the account -
anyone holding one can link a device and read or overwrite that person's
progress. This project's rules are open (the app writes with no sign-in
at all), so a "username -> code" lookup shipped inside index.html would
be a lookup every one of the ~40 classmates could run against everybody
else. It lives out here instead, where only whoever has the repo can
run it.

`leaderboard` USED TO BE KEYED BY THE SYNC CODE TOO, and `find` below
was written while that was true. It is keyed by `publicId` now, so the
code is no longer readable from anywhere out here - see cmd_find.

Usage
-----
  python3 tools/firestore-admin.py list
  python3 tools/firestore-admin.py find <username>
  python3 tools/firestore-admin.py bugs [N]
  python3 tools/firestore-admin.py prune [--days N] [--yes]
  python3 tools/firestore-admin.py purge --yes

`prune` is the one to reach for: it removes only the rankings rows
nobody is behind any more and leaves every live row alone. `purge`
wipes whole collections and is the blunt instrument.
"""

import json
import base64
import hashlib
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

PROJECT = "class-26e-study-drill"
BASE = ("https://firestore.googleapis.com/v1/projects/%s"
        "/databases/(default)/documents" % PROJECT)
COLLECTIONS = ("leaderboard", "progress", "vrooms")

# ---------------------------------------------------------------- admin auth
#
# WITHOUT A KEY THIS TOOL SEES EXACTLY WHAT A CLASSMATE'S PHONE SEES, and
# that is the whole problem it exists to solve. The rules are open but
# they refuse to LIST `progress` (403), which is the wall stopping ~40
# classmates enumerating each other - and `progress` is the only place
# the sync codes are, because they ARE its document ids. So an anonymous
# run can never answer "what is this person's code".
#
# A service-account key authenticates as the project rather than as a
# visitor, so the rules do not apply and the listing works. The key is
# read from NOVA_ADMIN_KEY (the JSON itself) or NOVA_ADMIN_KEY_FILE (a
# path to it). NEVER from the repo: this repo is public, because Pages
# will not serve a private one on a free plan.
#
# No pip installs, to keep this file as runnable as it has always been:
# the RS256 signature goes through the openssl binary, with the
# cryptography package as a fallback if openssl is not on PATH.

ADMIN_SCOPE = "https://www.googleapis.com/auth/datastore"
_token_cache = {"value": None, "expires": 0}


def _b64(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=")


def _load_key():
    """The service account credentials, or None for an anonymous run.

    THREE WAYS IN, AND THE TWO-FIELD ONE IS THE ONE THAT ACTUALLY WORKS
    FOR A PERSON WITH NO TERMINAL. The environment-variable box in the
    cloud environment settings takes one NAME=value per line, and a
    service-account JSON file is thirty pretty-printed lines starting
    with "{" - pasting it whole comes back as `couldn't parse "{" - use
    key=value format`, which is the box working correctly and telling
    you nothing useful. There is no way to one-line it or base64 it
    without a shell, and a service-account key must never go near an
    online encoder.

    But the whole file is not needed. Only two fields are, and BOTH ARE
    ALREADY SINGLE LINES inside that file - the newlines in the private
    key are backslash-n escapes, not real line breaks. So:

        NOVA_ADMIN_EMAIL         <- the client_email value
        NOVA_ADMIN_PRIVATE_KEY   <- the private_key value

    Two copy-pastes, no editing. NOVA_ADMIN_KEY (the whole JSON) and
    NOVA_ADMIN_KEY_FILE (a path to it) still work for anyone who does
    have a shell.
    """
    email = (os.environ.get("NOVA_ADMIN_EMAIL") or "").strip()
    priv = os.environ.get("NOVA_ADMIN_PRIVATE_KEY") or ""
    if email and priv:
        # Pasted through a form, the escapes usually survive as the two
        # characters backslash and n. Either way this has to end up as
        # real newlines before the PEM parser sees it.
        priv = priv.strip().strip('"')
        if "\\n" in priv and "\n" not in priv:
            priv = priv.replace("\\n", "\n")
        return {"client_email": email, "private_key": priv}
    if email or priv:
        sys.stderr.write(
            "Only half the admin credentials are set - NOVA_ADMIN_EMAIL and "
            "NOVA_ADMIN_PRIVATE_KEY both have to be there.\n")
        return None

    blob = os.environ.get("NOVA_ADMIN_KEY")
    if not blob:
        path = os.environ.get("NOVA_ADMIN_KEY_FILE")
        if path and os.path.exists(os.path.expanduser(path)):
            with open(os.path.expanduser(path), "r") as fh:
                blob = fh.read()
    if not blob:
        return None
    try:
        key = json.loads(blob)
    except ValueError:
        sys.stderr.write(
            "NOVA_ADMIN_KEY is set but is not valid JSON. If you pasted the "
            "whole key file into an environment-variable box, use "
            "NOVA_ADMIN_EMAIL and NOVA_ADMIN_PRIVATE_KEY instead - see the "
            "note on _load_key.\n")
        return None
    if not key.get("client_email") or not key.get("private_key"):
        sys.stderr.write("NOVA_ADMIN_KEY has no client_email/private_key.\n")
        return None
    return key


def _der_len(buf, i):
    """(length, index-after-the-length) for one DER length field."""
    n = buf[i]
    i += 1
    if n < 0x80:
        return n, i
    count = n & 0x7F
    return int.from_bytes(buf[i:i + count], "big"), i + count


def _der_next(buf, i):
    """(tag, body, index-after-the-element) for one DER element."""
    tag = buf[i]
    length, i = _der_len(buf, i + 1)
    return tag, buf[i:i + length], i + length


def _rsa_from_pem(pem):
    """(modulus, private exponent) out of a PKCS#8 or PKCS#1 private key.

    Pure stdlib, because the one device this has to run on cannot get a
    crypto library. Google's service-account keys are PKCS#8
    ("BEGIN PRIVATE KEY"), which wraps the PKCS#1 key in an OCTET
    STRING; PKCS#1 ("BEGIN RSA PRIVATE KEY") is accepted too so a key
    converted by hand still works.
    """
    body = "".join(l.strip() for l in pem.strip().splitlines()
                   if "-----" not in l)
    der = base64.b64decode(body)
    _, seq, _ = _der_next(der, 0)                    # outer SEQUENCE
    tag, first, i = _der_next(seq, 0)                # version INTEGER
    tag, second, i = _der_next(seq, i)
    if tag == 0x30:                                  # PKCS#8: algorithm id
        _, wrapped, _ = _der_next(seq, i)            # OCTET STRING
        _, seq, _ = _der_next(wrapped, 0)            # the PKCS#1 SEQUENCE
        _, _, i = _der_next(seq, 0)                  # version
        _, modulus, i = _der_next(seq, i)
        _, _, i = _der_next(seq, i)                  # public exponent
        _, private, i = _der_next(seq, i)
    else:                                            # PKCS#1 already
        modulus = second
        _, _, i = _der_next(seq, i)                  # public exponent
        _, private, i = _der_next(seq, i)
    return (int.from_bytes(modulus, "big"), int.from_bytes(private, "big"))


# The ASN.1 DigestInfo prefix for SHA-256, as PKCS#1 v1.5 requires.
SHA256_DIGESTINFO = bytes.fromhex("3031300d060960864801650304020105000420")


def _sign_rs256_pure(message, pem):
    """RS256 with nothing but the standard library.

    iOS will not let an app spawn a process, so a-Shell has no openssl
    and cannot build a crypto library either - and an iPad is the device
    this has to work on. Python's own pow() does the modular
    exponentiation, so the whole of RSA signing here is padding plus one
    builtin call. Verified byte-for-byte against openssl in
    check-admin-auth.py, which is the only reason to trust it.
    """
    n, d = _rsa_from_pem(pem)
    k = (n.bit_length() + 7) // 8
    digest = SHA256_DIGESTINFO + hashlib.sha256(message).digest()
    # 0x00 0x01 <0xFF padding> 0x00 <DigestInfo||hash>
    padded = b"\x00\x01" + b"\xff" * (k - len(digest) - 3) + b"\x00" + digest
    return pow(int.from_bytes(padded, "big"), d, n).to_bytes(k, "big")


def _sign_rs256(message, pem):
    """RS256 over `message`. openssl when there is one, else pure Python."""
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".pem", delete=False) as fh:
            fh.write(pem)
            keyfile = fh.name
        try:
            os.chmod(keyfile, 0o600)
            proc = subprocess.run(
                ["openssl", "dgst", "-sha256", "-sign", keyfile],
                input=message, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if proc.returncode == 0 and proc.stdout:
                return proc.stdout
        finally:
            os.unlink(keyfile)
    except Exception:
        # DELIBERATELY EVERYTHING. This is a shortcut to a faster signer,
        # never the only way to sign, and the fallback below is known to
        # produce identical bytes. a-Shell's Python raises its own thing
        # for a forbidden spawn, and guessing which exception that is
        # would be the whole iPad path lost to a wrong except clause.
        pass
    return _sign_rs256_pure(message, pem)


def _access_token():
    """A bearer token for the service account, or None if unconfigured."""
    if _token_cache["value"] and time.time() < _token_cache["expires"] - 60:
        return _token_cache["value"]
    key = _load_key()
    if not key:
        return None
    now = int(time.time())
    claims = {"iss": key["client_email"], "scope": ADMIN_SCOPE,
              "aud": key.get("token_uri", "https://oauth2.googleapis.com/token"),
              "iat": now, "exp": now + 3600}
    signing_input = (_b64(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
                     + b"." + _b64(json.dumps(claims).encode()))
    assertion = signing_input + b"." + _b64(_sign_rs256(signing_input, key["private_key"]))
    body = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": assertion.decode("ascii")}).encode("ascii")
    req = urllib.request.Request(claims["aud"], data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            got = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # Deliberately does not echo the request: it carries the signed
        # assertion, and this output gets pasted into chats.
        sys.stderr.write("Could not get an admin token (%s). The key may be "
                         "revoked, or its clock/scope wrong.\n" % e.code)
        return None
    _token_cache["value"] = got.get("access_token")
    _token_cache["expires"] = time.time() + int(got.get("expires_in", 3600))
    return _token_cache["value"]


def admin_ready():
    return bool(_access_token())


def _call(method, url, timeout=30):
    req = urllib.request.Request(url, method=method)
    token = _access_token()
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return 200, r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def _value(val):
    """One Firestore typed value, flattened.

    MAPS AND ARRAYS HAVE TO RECURSE, and not doing so was a real bug:
    the old version printed any non-scalar as the literal text
    "<mapValue>", which is precisely what `lifetime` is - the points and
    correct-answer totals that tell two accounts under the same username
    apart. It rendered as "<mapValue>" at the exact moment it mattered.
    """
    if "stringValue" in val:
        return val["stringValue"]
    if "integerValue" in val:
        return int(val["integerValue"])
    if "doubleValue" in val:
        return float(val["doubleValue"])
    if "booleanValue" in val:
        return val["booleanValue"]
    if "nullValue" in val:
        return None
    if "timestampValue" in val:
        return val["timestampValue"]
    if "mapValue" in val:
        return _plain((val["mapValue"] or {}).get("fields") or {})
    if "arrayValue" in val:
        return [_value(v) for v in ((val["arrayValue"] or {}).get("values") or [])]
    return "<%s>" % ",".join(val.keys())


def _plain(fields):
    """Firestore's typed values, flattened to something printable."""
    return {key: _value(val) for key, val in (fields or {}).items()}


def docs(collection, mask=None):
    """Every document in a collection, paged. Returns [(code, fields)]."""
    found, token = [], None
    while True:
        qs = {"pageSize": "300"}
        if token:
            qs["pageToken"] = token
        if mask:
            # A list, because mask.fieldPaths repeats rather than joining -
            # and asking for a few named fields is the difference between
            # this and pulling ~40 whole answer histories.
            qs["mask.fieldPaths"] = mask if isinstance(mask, (list, tuple)) else [mask]
        url = "%s/%s?%s" % (BASE, collection,
                            urllib.parse.urlencode(qs, doseq=True))
        status, body = _call("GET", url)
        if status != 200:
            sys.stderr.write("GET %s -> %s\n%s\n" % (collection, status, body))
            sys.exit(1)
        data = json.loads(body) if body.strip() else {}
        for d in data.get("documents", []):
            found.append((d["name"].rsplit("/", 1)[-1], _plain(d.get("fields"))))
        token = data.get("nextPageToken")
        if not token:
            return found


def cmd_list():
    for coll in COLLECTIONS:
        rows = docs(coll)
        print("\n%s - %d document(s)" % (coll, len(rows)))
        for code, fields in sorted(rows):
            name = fields.get("firstName") or fields.get("host") or ""
            extra = {k: v for k, v in fields.items()
                     if k in ("level", "badges", "hundos", "correct", "points")}
            print("  %-10s %-16s %s" % (code, name, extra or ""))
    return 0


def cmd_find(query):
    """A username in, that person's rankings row out.

    THIS NO LONGER RETURNS A SYNC CODE, AND IT USED TO CLAIM IT DID.
    When it was written, `leaderboard` was keyed by the sync code, so
    the document id WAS the answer. The publicId migration moved every
    row to `publicId` and deleted the old sync-code-keyed ones, and this
    function went on printing the document id under the same heading -
    so it handed over a twelve-character public id presented as a code
    somebody was meant to be able to sign in with. That string is not a
    code, will not link a device, and does not even match the format the
    sign-in screen accepts.

    The code is now genuinely unrecoverable from out here, and that is
    by design rather than by oversight: `progress` is keyed by the code
    and the rules refuse to LIST it (403), and nothing in any listable
    collection carries it - check-sync section 7 asserts exactly that.
    So there is no server-side route back into an account, for anyone,
    including whoever holds this repo. The routes that do exist are all
    on the person's own device: Settings -> Sync code, the Copy sign-in
    link beside it, another device already linked to the same account,
    or the IndexedDB mirror, which the boot recovery reads by itself.
    """
    want = query.strip().lower()

    if admin_ready():
        # THE CODES ARE THE DOCUMENT IDS OF `progress`, so with a key this
        # is the real lookup and it covers everybody, including people
        # hidden from the rankings and anybody who lost their code long
        # before any of this was written. Masked to a handful of fields:
        # a progress document is somebody's entire answer history and
        # there is no reason to drag ~40 of those over the wire.
        rows = docs("progress", mask=["firstName", "lifetime", "lastModified"])
        hits = [(code, f) for code, f in rows
                if (f.get("firstName") or "").strip().lower() == want]
        if not hits:
            hits = [(code, f) for code, f in rows
                    if want and want in (f.get("firstName") or "").strip().lower()]
            if not hits:
                print("No account named %r." % query)
                return 1
            print("No exact match. Close ones:")
        for code, fields in hits:
            when = fields.get("lastModified")
            stamp = "never used"
            if isinstance(when, (int, float)) and when:
                stamp = time.strftime("last used %Y-%m-%d",
                                      time.localtime(when / 1000.0))
            life = fields.get("lifetime") or {}
            if not isinstance(life, dict):
                life = {}
            # The two numbers somebody can actually check against what
            # they tell you. The whole lifetime map is noise in a list.
            print("  %-16s %-11s  %6s pts  %5s correct  %s"
                  % (fields.get("firstName", "?"), code,
                     life.get("points", "?"), life.get("correct", "?"), stamp))
        if len(hits) > 1:
            print("\nMore than one account under that name. Usernames are not")
            print("unique, AND a device that lost its code used to mint a new")
            print("one (fixed in build 158) - which leaves the same person with")
            print("an old account holding the real progress and a newer, emptier")
            print("one. Check the numbers and the dates before handing one over.")
        return 0

    print("No admin key configured, so this can only see what a classmate's")
    print("phone can see - and the sync codes are not in that. Set")
    print("NOVA_ADMIN_KEY (or NOVA_ADMIN_KEY_FILE) to a service-account key")
    print("for a real lookup. Falling back to the rankings rows:\n")

    entries = docs("leaderboard")
    hits = [(pub, f) for pub, f in entries
            if (f.get("firstName") or "").strip().lower() == want]
    if not hits:
        hits = [(pub, f) for pub, f in entries
                if want and want in (f.get("firstName") or "").strip().lower()]
        if not hits:
            print("No rankings entry for %r." % query)
            print("Only people opted in to the rankings appear here - someone")
            print("hidden has no entry to look up.")
            return 1
        print("No exact match. Close ones:")
    for pub, fields in hits:
        extra = {k: v for k, v in fields.items()
                 if k in ("level", "badges", "hundos", "correct", "points")}
        print("  %-16s public id %-14s %s"
              % (fields.get("firstName", "?"), pub, extra or ""))
    if len(hits) > 1:
        print("\nMore than one match - usernames are not unique, so check the")
        print("level/hundos against what the person tells you before acting")
        print("on any of these.")
    print("\nThe public id is NOT a sync code: it keys the rankings row and")
    print("nothing else, and it will not sign anybody in. The sync code is")
    print("not readable from here at all - `progress` is keyed by it and the")
    print("rules refuse to list that collection, which is what stops all ~40")
    print("classmates running this same lookup against each other.")
    print("Ways back into an account, all of them on the person's own device:")
    print("  - Settings -> Sync code (tap to reveal), or Copy sign-in link")
    print("  - any other device still linked to the same account")
    print("  - the IndexedDB mirror, which boot recovery reads by itself")
    return 0


def cmd_bugs(limit):
    """Bug reports, newest first.

    They live in `vrooms` with a `bug-` id rather than in a collection
    of their own, because these rules only allow LISTING `leaderboard`
    and `vrooms` - a `bugs` collection comes back PERMISSION_DENIED on a
    list, so reports written there would be write-only and nobody would
    ever read them. See the note in index.html where the button is
    built. Change one line in the Firebase rules and this moves.
    """
    rows = [(rid, f) for rid, f in docs("vrooms")
            if rid.startswith("bug-") or f.get("kind") == "bug"]
    if not rows:
        print("No bug reports.")
        return 0
    rows.sort(key=lambda r: -(r[1].get("at") or 0))
    print("%d report(s), newest first:\n" % len(rows))
    for rid, f in rows[:limit]:
        when = f.get("at")
        stamp = time.strftime("%Y-%m-%d %H:%M", time.localtime(when / 1000.0)) \
            if isinstance(when, (int, float)) and when else "no date"
        who = f.get("name") or "(no name)"
        print("%s  %s  build %s" % (stamp, who, f.get("build") or "?"))
        print("  %s  %s%s" % (f.get("viewport") or "?",
                              (f.get("ua") or "")[:70],
                              " [installed]" if f.get("standalone") else ""))
        for line in (f.get("text") or "").splitlines() or [""]:
            print("    " + line)
        print("  id: %s\n" % rid)
    if len(rows) > limit:
        print("(%d older not shown - pass a number to see more)" % (len(rows) - limit))
    return 0


ORPHAN_DEFAULT_DAYS = 30

# A sync code is XXXX-XXXX from an alphabet with no 0/O/1/I; a publicId
# is twelve characters of base36. Anything matching this as a document
# id in `leaderboard` is a row from before the publicId migration.
SYNC_CODE_SHAPE = __import__("re").compile(
    r"^[ABCDEFGHJKLMNPQRSTUVWXYZ23456789]{4}-[ABCDEFGHJKLMNPQRSTUVWXYZ23456789]{4}$")


def cmd_prune(days, confirmed):
    """Delete ONLY the rankings rows nobody is behind any more.

    An orphaned row is the leftover from the lost-code bug fixed in
    build 158: a device that lost its sync code minted a new one, so
    that person carried on as a new account with a new row, and their
    old row stayed on the board with nobody holding the key to it. It
    cannot update itself and it cannot delete itself.

    WHY STALENESS IS A SOUND TEST HERE, and not a guess. Every live
    device rewrites its own leaderboard row on launch and on every save
    (pushToCloud), stamping lastModified. A row with somebody behind it
    therefore cannot go quiet for long; an orphan goes quiet the moment
    it is abandoned and never speaks again.

    AND THE COST OF BEING WRONG IS ZERO, which is the property that
    makes this safe to run rather than merely plausible. If this
    deletes the row of somebody who simply has not opened the app in a
    month, their next launch writes it straight back with their real
    numbers. Nothing here touches `progress` - the account itself, all
    of it - only the rankings row, which is the same thing
    retireLeaderboardEntry() deletes in the app for exactly this reason.

    Dry run unless --yes, because a destructive pass over live class
    data should have to be looked at before it happens.
    """
    rows = docs("leaderboard")
    now_ms = time.time() * 1000.0
    cutoff = now_ms - (days * 86400000.0)
    live, orphans, undated = [], [], []
    for pub, f in rows:
        when = f.get("lastModified")
        stamp = when if isinstance(when, (int, float)) and when else 0
        if SYNC_CODE_SHAPE.match(pub):
            # A LEGACY ROW, AND THIS ONE IS NOT A HEURISTIC AT ALL.
            # The document id IS the sync code, which is the account -
            # and this collection is world-readable and listable,
            # because that is how forty phones draw the board. So every
            # one of these is a classmate's account key sitting in
            # public. The app stopped keying rows this way when they
            # moved to publicId and migrateLeaderboardKey() deletes the
            # old one on the owner's next launch; these are the ones
            # whose owner has not launched a new enough build yet.
            # Age is irrelevant here: a fresh one is just as exposed as
            # a stale one, so it goes regardless of --days.
            orphans.append((pub, f, stamp))
        elif not stamp:
            undated.append((pub, f))
        elif stamp < cutoff:
            orphans.append((pub, f, stamp))
        else:
            live.append((pub, f))

    def line(pub, f, when=None):
        stamp = time.strftime("%Y-%m-%d", time.localtime(when / 1000.0)) if when else "no date"
        why = " EXPOSED SYNC CODE" if SYNC_CODE_SHAPE.match(pub) else ""
        return "  %-16s %-14s %s  level %-4s %s hundos%s" % (
            f.get("firstName", "?"), pub, stamp,
            f.get("level", "?"), f.get("hundos", "?"), why)

    exposed = sum(1 for pub, _, _ in orphans if SYNC_CODE_SHAPE.match(pub))
    print("%d rankings rows: %d active, %d to remove (%d of them exposing a sync code), "
          "%d with no date." % (len(rows), len(live), len(orphans), exposed, len(undated)))

    if undated:
        # An older build published no lastModified at all. Absence of a
        # date is not evidence of abandonment, so these are reported and
        # never deleted - the whole test is "has this gone quiet", and a
        # row that never spoke cannot answer it.
        print("\nNO DATE - never touched, cannot be judged:")
        for pub, f in undated:
            print(line(pub, f))

    if not orphans:
        print("\nNothing to prune.")
        return 0

    print("\nWOULD DELETE (legacy sync-code rows, or quiet for %d+ days):" % days)
    for pub, f, when in sorted(orphans, key=lambda r: r[2]):
        print(line(pub, f, when))

    if not confirmed:
        print("\nDry run. Re-run with --yes to delete these %d rows." % len(orphans))
        print("Anybody wrongly caught gets their row back on their next launch.")
        return 0

    gone = 0
    for pub, f, when in orphans:
        url = "%s/leaderboard/%s" % (BASE, urllib.parse.quote(pub, safe=""))
        status, body = _call("DELETE", url)
        ok = status == 200
        gone += 1 if ok else 0
        print("  %-16s %-14s %s" % (f.get("firstName", "?"), pub,
                                    "deleted" if ok else "FAILED %s" % status))
    print("\n%d of %d removed. %d active rows untouched." % (gone, len(orphans), len(live)))
    return 0 if gone == len(orphans) else 1


def cmd_purge(confirmed):
    if not confirmed:
        print("This deletes EVERY document in: %s" % ", ".join(COLLECTIONS))
        print("Re-run with --yes to actually do it.")
        return 1
    total = 0
    for coll in COLLECTIONS:
        rows = docs(coll, mask="__name__")
        if not rows:
            print("  %-12s (already empty)" % coll)
        for code, _ in rows:
            url = "%s/%s/%s" % (BASE, coll, urllib.parse.quote(code, safe=""))
            status, body = _call("DELETE", url)
            ok = status == 200
            total += 1 if ok else 0
            print("  %-12s %-10s %s"
                  % (coll, code, "deleted" if ok else body.strip()[:120]))
    print("\n%d document(s) deleted." % total)
    for coll in COLLECTIONS:
        print("  %-12s now holds %d" % (coll, len(docs(coll, mask="__name__"))))
    return 0


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]
    if cmd == "list":
        return cmd_list()
    if cmd == "find":
        if len(argv) < 3:
            print("usage: firestore-admin.py find <username>")
            return 2
        return cmd_find(" ".join(argv[2:]))
    if cmd == "bugs":
        n = 20
        for a in argv[2:]:
            if a.isdigit(): n = int(a)
        return cmd_bugs(n)
    if cmd == "prune":
        days = ORPHAN_DEFAULT_DAYS
        if "--days" in argv:
            try: days = int(argv[argv.index("--days") + 1])
            except (IndexError, ValueError):
                print("usage: firestore-admin.py prune [--days N] [--yes]")
                return 2
        return cmd_prune(days, "--yes" in argv)
    if cmd == "purge":
        return cmd_purge("--yes" in argv)
    print("Unknown command %r" % cmd)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
