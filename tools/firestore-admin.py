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
  python3 tools/firestore-admin.py audit [--backup FILE]
  python3 tools/firestore-admin.py fixlevels [--yes]
  python3 tools/firestore-admin.py prune [--days N] [--yes]
  python3 tools/firestore-admin.py purge --yes
  python3 tools/firestore-admin.py move <from-public-id> <to-public-id> [--yes]
  python3 tools/firestore-admin.py move --finish [--only NAME] [--yes]
  python3 tools/firestore-admin.py merge <from-public-id> <to-public-id> [--bonus N] [--extra-from ID] [--yes]
  python3 tools/firestore-admin.py credit <orphan-row-public-id> <to-public-id> [--yes]
  python3 tools/firestore-admin.py merge-now <old public id | name:First> [...] [--yes] [--force] [--hold-file F | --no-hold]

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
    except ValueError as e:
        # SAY WHAT IS ACTUALLY WRONG WITH IT. "not valid JSON" sent
        # somebody back to re-read the format instructions when the
        # format was fine - the paste had simply dropped two characters
        # (an opening quote and the K in "KEY"), which a drag-select
        # across a long line does easily. None of this prints any key
        # material; it only counts and looks for landmarks.
        sys.stderr.write("NOVA_ADMIN_KEY is set but does not parse: %s\n" % e)
        n = len(blob)
        if n < 1500:
            sys.stderr.write(
                "  It is only %d characters. A service-account key is about "
                "2300, so this looks cut short.\n" % n)
        if blob.count('"') % 2:
            sys.stderr.write(
                "  There is an ODD number of quote marks in it, so at least "
                "one was lost in the paste.\n")
        if "BEGIN PRIVATE KEY" not in blob:
            sys.stderr.write(
                "  The text -----BEGIN PRIVATE KEY----- is not in it, so the "
                "private key itself lost characters.\n")
        if blob.count("{") != blob.count("}"):
            sys.stderr.write("  The braces do not balance.\n")
        sys.stderr.write(
            "  Re-copy the file with Select All (Cmd+A / Ctrl+A) rather than "
            "dragging a selection, which is what drops characters. Real line "
            "breaks are fine - JSON ignores them.\n")
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
            # build 383: Fire Code keeps its own document beside the academy's (<code>__ifc, and its
            # backup <code>__ifc__floor) - the same person's other class, not a second account
            note = ""
            if code.endswith("__ifc__floor"): note = "  (Fire Code class backup of %s)" % code[:-len("__ifc__floor")]
            elif code.endswith("__ifc"): note = "  (Fire Code class of %s - not a second account)" % code[:-len("__ifc")]
            elif code.endswith("__floor"): note = "  (backup of %s)" % code[:-len("__floor")]
            print("  %-16s %-11s  %6s pts  %5s correct  %s%s"
                  % (fields.get("firstName", "?"), code,
                     life.get("points", "?"), life.get("correct", "?"), stamp, note))
        if len({c.split("__")[0] for c, _ in hits}) > 1:
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
        if f.get("edges"):
            # build 384: where the browser's bars are on that device (safariBarsReading in index.html)
            print("  edges: %s" % f.get("edges"))
        if f.get("perf"):
            print("  tab perf: %s" % f.get("perf"))
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


def _doc_url(coll, doc_id):
    return "%s/%s/%s" % (BASE, coll, urllib.parse.quote(doc_id, safe=""))


def _write_fields(coll, doc_id, fields, mask=None):
    """PATCH typed fields into one document (creating it if needed)."""
    def _typed(v):
        if isinstance(v, bool):
            return {"booleanValue": v}
        if isinstance(v, int):
            return {"integerValue": str(v)}
        if isinstance(v, float):
            return {"doubleValue": v}
        if isinstance(v, dict):
            return {"mapValue": {"fields": {k2: _typed(v2) for k2, v2 in v.items()}}}
        return {"stringValue": str(v)}
    typed = {k: _typed(v) for k, v in fields.items()}
    qs = ""
    if mask:
        qs = "?" + urllib.parse.urlencode({"updateMask.fieldPaths": list(mask)}, doseq=True)
    body = json.dumps({"fields": typed}).encode("utf-8")
    req = urllib.request.Request(_doc_url(coll, doc_id) + qs, data=body, method="PATCH")
    req.add_header("Content-Type", "application/json")
    token = _access_token()
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def cmd_move(argv):
    """MOVE A DEVICE ONTO ANOTHER ACCOUNT (build 242).

    For one person who made duplicate accounts after losing their
    sign-in: every device on the duplicate is moved onto the real one the
    next time it opens the app, without anybody typing a code. Leaves a
    note at progress/<old code>__moved -> { to: <code> }, which the app
    (checkAccountMove) follows and then marks done; setSyncCode retires
    the duplicate's rankings row on the way.

    Takes PUBLIC IDS, never names and never codes: names are not unique,
    and codes are never printed by this tool. Nothing is deleted here -
    `--finish` does that, and only for notes the device has marked done,
    because deleting a progress document a device is still listening to
    reads to that device as a reset and wipes it.
    """
    if not admin_ready():
        print("move needs the admin key: the codes are the progress document ids.")
        return 2
    rows = docs("progress", mask=["firstName", "publicId", "to", "done"])
    rows = [(c, f) for c, f in rows]
    by_pub = {}
    notes = {}
    for code, f in rows:
        if code.endswith("__moved"):
            notes[code[:-len("__moved")]] = f
        elif code.endswith("__merge"):
            notes[code[:-len("__merge")]] = dict(f, _suffix="__merge")
        elif f.get("publicId"):
            by_pub.setdefault(f["publicId"], []).append((code, f))
    confirmed = "--yes" in argv
    if "--finish" in argv:
        pending = 0
        # --only NAME: finish just that account's note (exact first name),
        # so one followed merge can be finished without the others.
        only = argv[argv.index("--only") + 1] if "--only" in argv else None
        for old, note in notes.items():
            name = next((f.get("firstName") for c, f in rows if c == old), "?")
            if only is not None and name != only:
                continue
            if not note.get("done"):
                pending += 1
                print("  %-16s not followed yet - left alone" % name)
                continue
            print("  %-16s followed; %s" % (name, "deleting the old account" if confirmed else "would delete the old account"))
            if confirmed:
                _call("DELETE", _doc_url("progress", old))
                _call("DELETE", _doc_url("progress", old + note.get("_suffix", "__moved")))
        if not confirmed:
            print("\nRe-run with --yes to delete the followed ones.")
        return 0
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 2:
        print("usage: firestore-admin.py move <from-public-id> <to-public-id> [--yes]")
        return 2
    src, dst = args
    if len(by_pub.get(dst, [])) != 1:
        print("The account to move onto must be exactly one progress document; found %d." % len(by_pub.get(dst, [])))
        return 1
    dst_code, dst_f = by_pub[dst][0]
    olds = by_pub.get(src, [])
    if not olds:
        print("No progress document carries public id %s." % src)
        return 1
    for old_code, f in olds:
        print("  %-16s -> %-16s %s" % (f.get("firstName", "?"), dst_f.get("firstName", "?"),
                                        "note written" if confirmed else "would write the note"))
        if confirmed:
            st = _write_fields("progress", old_code + "__moved",
                               {"to": dst_code, "at": int(time.time() * 1000)})
            if st != 200:
                print("    failed: HTTP %s" % st)
                return 1
    if not confirmed:
        print("\nRe-run with --yes to write it.")
    return 0


def cmd_merge(argv):
    """MERGE A DUPLICATE ACCOUNT INTO THE REAL ONE (build 279).

    Like `move`, but the device that follows the note brings its own
    progress with it - XP, right answers, hundos, stats, history, study
    time - and adds it to the account it joins (mergeLeavingAccount in
    index.html). The note lives at progress/<old code>__merge, NOT
    __moved: builds before 279 follow __moved by taking the target whole,
    so a merge written there would throw the duplicate's progress away on
    any phone that had not updated yet.

      merge <from-public-id> <to-public-id> [--bonus N] [--extra-from <row-public-id>] [--yes]

    --bonus N         whole levels added on top of the merged total
    --extra-from ID   a rankings row with NO progress document behind it
                      (an account whose device was reset): its XP, right
                      answers and this week's points ride on the note, and
                      with --yes the row itself is deleted, since nothing
                      will ever come back for it.
    Public ids in, never names and never codes."""
    if not admin_ready():
        print("merge needs the admin key: the codes are the progress document ids.")
        return 2
    args = []
    bonus = 0
    extra_from = None
    i = 0
    rest = [a for a in argv if a != "--yes"]
    while i < len(rest):
        a = rest[i]
        if a == "--bonus":
            bonus = int(rest[i + 1]); i += 2; continue
        if a == "--extra-from":
            extra_from = rest[i + 1]; i += 2; continue
        args.append(a); i += 1
    confirmed = "--yes" in argv
    if len(args) != 2:
        print("usage: firestore-admin.py merge <from-public-id> <to-public-id> [--bonus N] [--extra-from ID] [--yes]")
        return 2
    src, dst = args
    rows = docs("progress", mask=["firstName", "publicId", "lifetime"])
    by_pub = {}
    for code, f in rows:
        if "__" in code:
            continue
        if f.get("publicId"):
            by_pub.setdefault(f["publicId"], []).append((code, f))
    if len(by_pub.get(dst, [])) != 1:
        print("The account to merge into must be exactly one progress document; found %d." % len(by_pub.get(dst, [])))
        return 1
    dst_code, dst_f = by_pub[dst][0]
    # The fullest document first: the bonus and the orphan's numbers ride on
    # the first note only, and they belong with the account that was really
    # used, not with an abandoned sign-up sharing its public id.
    def _pts(item):
        life = item[1].get("lifetime") or {}
        try:
            return int(life.get("points") or 0)
        except (TypeError, ValueError):
            return 0
    olds = sorted(by_pub.get(src, []), key=_pts, reverse=True)
    if not olds:
        print("No progress document carries public id %s." % src)
        return 1
    extra = None
    if extra_from:
        row = next((f for pub, f in docs("leaderboard") if pub == extra_from), None)
        if row is None:
            print("No rankings row %s." % extra_from)
            return 1
        if by_pub.get(extra_from):
            print("Row %s still has a progress document - merge it as an account, not as --extra-from." % extra_from)
            return 1
        extra = {"points": int(row.get("xp") or 0), "correct": int(row.get("correct") or 0),
                 "weekPoints": int(row.get("weekPoints") or 0), "week": str(row.get("week") or "")}
        print("  extra from %s (%s): %s" % (extra_from, row.get("firstName", "?"), extra))
    for old_code, f in olds:
        note = {"to": dst_code, "at": int(time.time() * 1000)}
        if bonus:
            note["bonusLevels"] = bonus
        if extra:
            note["extra"] = extra
        print("  %-16s -> %-16s merge%s%s  %s" % (f.get("firstName", "?"), dst_f.get("firstName", "?"),
              (", +%d level(s)" % bonus) if bonus else "", ", + the orphan row" if extra else "",
              "note written" if confirmed else "would write the note"))
        if confirmed:
            st = _write_fields("progress", old_code + "__merge", note)
            if st != 200:
                print("    failed: HTTP %s" % st)
                return 1
        # The bonus and the orphan's numbers belong on ONE note: a second
        # device of the same duplicate must not pay them twice.
        bonus = 0
        extra = None
    if extra_from and confirmed:
        st = _call("DELETE", _doc_url("leaderboard", extra_from))
        print("  orphan row %s deleted" % extra_from)
    if not confirmed:
        print("\nRe-run with --yes to write it.")
    return 0


def cmd_credit(argv):
    """CREDIT AN ORPHANED ROW TO THE ACCOUNT IT BELONGS TO (build 284).

    For a rankings row with NO progress document behind it - a parallel
    sign-up whose device was reset - there is no device left to follow a
    merge note. A credit note goes beside the account it is FOR, at
    progress/<code>__credit, carrying the row's XP, right answers and
    this week's points; every device on that account reads it
    (checkAccountCredit in index.html) and it is paid once per account.
    With --yes the orphan row is deleted, since nothing will come back
    for it. Public ids in, never names and never codes."""
    if not admin_ready():
        print("credit needs the admin key: the codes are the progress document ids.")
        return 2
    args = [a for a in argv if not a.startswith("--")]
    confirmed = "--yes" in argv
    if len(args) != 2:
        print("usage: firestore-admin.py credit <orphan-row-public-id> <to-public-id> [--yes]")
        return 2
    orphan, dst = args
    rows = docs("progress", mask=["firstName", "publicId"])
    by_pub = {}
    for code, f in rows:
        if "__" in code:
            continue
        if f.get("publicId"):
            by_pub.setdefault(f["publicId"], []).append((code, f))
    if len(by_pub.get(dst, [])) != 1:
        print("The account to credit must be exactly one progress document; found %d." % len(by_pub.get(dst, [])))
        return 1
    if by_pub.get(orphan):
        print("Row %s still has a progress document - merge it as an account instead." % orphan)
        return 1
    dst_code, dst_f = by_pub[dst][0]
    row = next((f for pub, f in docs("leaderboard") if pub == orphan), None)
    if row is None:
        print("No rankings row %s." % orphan)
        return 1
    extra = {"points": int(row.get("xp") or 0), "correct": int(row.get("correct") or 0),
             "weekPoints": int(row.get("weekPoints") or 0), "week": str(row.get("week") or "")}
    note = {"id": "row:" + orphan, "extra": extra, "at": int(time.time() * 1000)}
    print("  %s (%s) -> %s: %s  %s" % (orphan, row.get("firstName", "?"), dst_f.get("firstName", "?"), extra,
                                     "credit written" if confirmed else "would write the credit"))
    if not confirmed:
        print("\nRe-run with --yes to write it and delete the orphan row.")
        return 0
    st = _write_fields("progress", dst_code + "__credit", note)
    if st != 200:
        print("    failed: HTTP %s" % st)
        return 1
    st, _ = _call("DELETE", _doc_url("leaderboard", orphan))
    print("  orphan row %s %s" % (orphan, "deleted" if st == 200 else "NOT deleted: HTTP %s" % st))
    return 0


# ---------------------------------------------------------------- merge-now
#
# THE SERVER-SIDE FOLD OF A DUPLICATE ACCOUNT (build 384 r4).
#
# `merge` only writes a NOTE; the folding itself happens when a device that is
# still signed in to the old account opens the app (followAccountMove ->
# mergeLeavingAccount in index.html). `merge-now` does what that phone would
# do, from here, so it no longer waits for the phone. Everything below is a
# line-for-line port of the app's own rules, and tools/check-merge-now.py runs
# the app's real functions in Chromium against this port to keep them equal.
#
# What the phone does, and so what this does (see the docstring of cmd_merge_now):
#   counts ADD, bests keep the better, lists union, and who the person IS (name,
#   character, public id, friend code, theme, tours) stays the target's.
#   A note that already carries `base` (build 287: the old account as it stood
#   when the server folded it in) adds only the DIFFERENCE (progressSinceBase),
#   which is what makes a second run, or a phone that opens later, add nothing.

ADD_LIFETIME = ("answered", "correct", "drillPlays", "examPlays", "gamePlays",
                "perfectTests", "points", "fullTests")
ADD_COUNTERS = ("vrMatches", "vrWins", "vrTop3", "weeklyWins", "weeklyTop3",
                "retakenQuestions", "lateHundos")
MAX_FIELDS = ("dailyCorrectStreak", "hundoDayBest", "bestTestStreak", "unitHundoStreak",
              "dailyCorrectBest", "dailyCorrectTotal", "unitHundoStreakBest",
              "dayAnsweredBest", "friendsBest")
UNION_LISTS = ("vrCounted", "vrTop3Rooms", "flareHintsShown", "weekWinWeeks", "weekWinLost", "retakenKeys")
OR_FLAGS = ("practiceExamPerfect", "practiceTestPassed", "bigTestPassed", "bigTest450Passed",
            "bigTest500Passed", "supernovaAchieved", "novaBeaten", "sheriffMoved324")
TEST_HISTORY_MAX = 50                    # TEST_HISTORY_MAX in index.html
STUDY_LEAK_UNTIL, STUDY_OLD_DAY_MAX, STUDY_DAY_MAX = "2026-10-10", 6 * 3600 * 1000, 16 * 3600 * 1000
MERGE_NOTE_SUFFIX = "__merge"
FLOOR_SUFFIX = "__floor"
RESOURCE_ROOT = "projects/%s/databases/(default)/documents" % PROJECT


def _num(v):
    """Number(v) || 0, as JavaScript reads it (ints stay ints)."""
    if isinstance(v, bool):
        return 1 if v else 0
    if isinstance(v, (int, float)):
        if v != v:
            return 0
        return int(v) if isinstance(v, float) and v.is_integer() else v
    if isinstance(v, str):
        try:
            x = float(v.strip() or 0)
        except ValueError:
            return 0
        if x != x:
            return 0
        return int(x) if x.is_integer() else x
    return 0


def _t(v):
    """JavaScript truthiness: an empty object or array is TRUE, 0 and "" are not."""
    if v is None or v is False or v == 0 and not isinstance(v, (dict, list)) or v == "":
        return False
    if isinstance(v, float) and v != v:
        return False
    return True


def _isnum(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v == v


def _less(a, b):
    return max(0, _num(a) - _num(b))


def _js_str(v):
    if v is None:
        return "undefined"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def _obj(d, k):
    """`store[k] || (store[k] = {})`."""
    v = d.get(k)
    if not isinstance(v, dict):
        v = d[k] = {}
    return v


def _studylog_normalize(log):
    if not isinstance(log, dict):
        return log
    for k in list(log):
        v = _num(log[k])
        cap = STUDY_OLD_DAY_MAX if k <= STUDY_LEAK_UNTIL else STUDY_DAY_MAX
        if v > cap:
            log[k] = cap
    return log


def _clean_classes(v):
    if not isinstance(v, list):
        return None
    out = []
    for k in v:
        if k in ("academy", "ifc") and k not in out:
            out.append(k)
    if not out:
        return None
    return sorted(out, key=lambda x: 0 if x == "academy" else 1)


def _classes_with_leaves(lst, a):
    if not isinstance(lst, list) or not isinstance(a, dict):
        return lst
    left, joined = a.get("classLeftAt") or {}, a.get("classJoinedAt") or {}
    return [k for k in lst if not (_num(left.get(k)) > _num(joined.get(k)))]


def merge_leaving_account(dst, src, note=None, now_ms=0, week_key=None, hold_sets=None):
    """mergeLeavingAccount(src, note) in index.html, on plain documents.

    `dst` (the target's document) is changed IN PLACE; `src` is read only.
    Returns a dict of what could not be done exactly as the phone does:
      hold_skipped - no mergeHold was written (no `hold_sets` given)
      week_skipped - the old account's weekly points were not carried (the
                     target's week is stale and the tool never rolls a week)
    Not ported on purpose: rollWeek() (the target's own phone rolls its week;
    rolling it from here would also need rollWeekStats) - everything else is.
    """
    out = {"hold_skipped": False, "week_skipped": False}
    L = dst.get("lifetime")
    if not isinstance(L, dict):
        L = dst["lifetime"] = {}
    # THE HOLD: the account as it stood before the merge, kept so what the
    # merge unlocks plays after the next test. A second merge keeps the first.
    if not _t(dst.get("mergeHold")):
        if hold_sets is None:
            out["hold_skipped"] = True
        else:
            dst["mergeHold"] = {
                "points": _num(L.get("points")),
                "perfects": dict(dst.get("unitPerfects") or {}),
                "chars": list(hold_sets.get("chars") or []),
                "banners": list(hold_sets.get("banners") or []),
                "hundos": _num(L.get("perfectTests")), "at": now_ms}
    SL = src.get("lifetime") or {}
    for k in ADD_LIFETIME:
        L[k] = _num(L.get(k)) + _num(SL.get(k))
    L["longestStreak"] = max(_num(L.get("longestStreak")), _num(SL.get("longestStreak")))
    L["currentStreak"] = max(_num(L.get("currentStreak")), _num(SL.get("currentStreak")))
    # per question: seen, missed, the recent misses
    st = _obj(dst, "stats")
    for k, b in (src.get("stats") or {}).items():
        a = st.get(k) or {"n": 0, "m": 0, "r": []}
        b = b or {}
        r = [x for x in (list(a.get("r") or []) + list(b.get("r") or [])) if _isnum(x)]
        r.sort()
        st[k] = {"n": _num(a.get("n")) + _num(b.get("n")), "m": _num(a.get("m")) + _num(b.get("m")),
                 "r": r[-20:]}
    ts = _obj(dst, "testStats")
    for k, b in (src.get("testStats") or {}).items():
        a = ts.get(k)
        b = b or {}
        if not isinstance(a, dict):
            ts[k] = dict(b)
            continue
        later = b if _num(b.get("lastPlayedAt")) > _num(a.get("lastPlayedAt")) else a
        bests = [x for x in (a.get("bestMs"), b.get("bestMs")) if _isnum(x)]
        merged = dict(a)
        merged.update({"plays": _num(a.get("plays")) + _num(b.get("plays")),
                       "totalMs": _num(a.get("totalMs")) + _num(b.get("totalMs")),
                       "bestMs": min(bests) if bests else None})
        for f in ("lastPlayedAt", "lastElapsedMs", "lastPct"):
            if f in later:                       # undefined is dropped by JSON.stringify
                merged[f] = later[f]
            else:
                merged.pop(f, None)
        ts[k] = merged

    def sum_map(k):
        d = _obj(dst, k)
        for u, v in (src.get(k) or {}).items():
            d[u] = _num(d.get(u)) + _num(v)

    def max_map(k):
        d = _obj(dst, k)
        for u, v in (src.get(k) or {}).items():
            d[u] = max(_num(d.get(u)), _num(v))

    def min_map(k):
        d = _obj(dst, k)
        for u, v in (src.get(k) or {}).items():
            v = _num(v)
            if v > 0:
                d[u] = min(_num(d[u]), v) if _t(d.get(u)) else v

    def or_map(k):
        d = _obj(dst, k)
        for u, v in (src.get(k) or {}).items():
            if _t(v):
                d[u] = d[u] if _t(d.get(u)) else v

    sum_map("studyLog")
    sum_map("unitPerfects")
    _studylog_normalize(dst["studyLog"])
    or_map("unitBlackStar")
    or_map("flagged")
    # the classes: both accounts' (a class either was in stays)
    for f in ("classJoinedAt", "classLeftAt"):
        d, o = _obj(dst, f), src.get(f) or {}
        for k in ("academy", "ifc"):
            if _num(o.get(k)) > _num(d.get(k)):
                d[k] = _num(o.get(k))
    ca, cb = _clean_classes(dst.get("classes")), _clean_classes(src.get("classes"))
    if cb:
        dst["classes"] = _clean_classes(_classes_with_leaves((ca or ["academy"]) + cb, dst)) or dst.get("classes")
    if src.get("seenClassTip") is True:
        dst["seenClassTip"] = True
    # the grandfather floor: whichever account held the higher level keeps it
    for k in ("levelFloor", "rankFloor", "levelWallRule"):
        dst[k] = max(_num(dst.get(k)), _num(src.get(k)))
    max_map("unitBestPct")
    min_map("unitBestMs")
    max_map("flareLevels")
    for k in ("unitGameBeat", "gameFarthest"):
        d = _obj(dst, k)
        for u, bv in (src.get(k) or {}).items():
            a, b = d.get(u) or {}, bv or {}
            res = dict(a)
            for sp, x in b.items():
                res[sp] = (a.get(sp) or x) if isinstance(x, bool) else max(_num(a.get(sp)), _num(x))
            d[u] = res
    min_map("gameHardcoreMs")
    # exam records and run counts re-seed themselves from the merged history
    for u in (src.get("unitExam") or {}):
        if isinstance(dst.get("unitExam"), dict) and _t(dst["unitExam"].get(u)):
            del dst["unitExam"][u]
    if isinstance(dst.get("unitRuns"), dict) and isinstance(src.get("unitRuns"), dict):
        sum_map("unitRuns")
    else:
        dst["unitRuns"] = None
    hist = list(dst.get("testHistory") or []) + list(src.get("testHistory") or [])
    hist.sort(key=lambda h: -_num(h.get("playedAt") if isinstance(h, dict) else 0))
    dst["testHistory"] = hist[:TEST_HISTORY_MAX]
    # (384.51) the wins no listed week backs are summed with the wins, before they are (the app's mergeLeavingAccount)
    def _wb(o):
        if isinstance(o.get("weekWinBase"), (int, float)) and not isinstance(o.get("weekWinBase"), bool):
            return o["weekWinBase"]
        return max(0, _num(o.get("weeklyWins")) - len({w for w in (o.get("weekWinWeeks") or []) if isinstance(w, str)}))
    dst["weekWinBase"] = _wb(dst) + _wb(src)
    if isinstance(src.get("weekWinPts"), dict) or isinstance(dst.get("weekWinPts"), dict):
        wp = dst["weekWinPts"] = dict(dst.get("weekWinPts") or {})
        for w, v in (src.get("weekWinPts") or {}).items():
            if _num(v) > _num(wp.get(w)):
                wp[w] = _num(v)
    for k in ADD_COUNTERS:
        dst[k] = _num(dst.get(k)) + _num(src.get(k))
    for k in MAX_FIELDS:
        dst[k] = max(_num(dst.get(k)), _num(src.get(k)))
    for k in UNION_LISTS:
        a = dst.get(k) if isinstance(dst.get(k), list) else []
        dst[k] = (a + [x for x in (src.get(k) or []) if x not in a])[-300:]
    for k in OR_FLAGS:
        if src.get(k) is True:
            dst[k] = True
    if isinstance(src.get("mysteryColorsFound"), dict) and isinstance(dst.get("mysteryColorsFound"), dict):
        for c, v in src["mysteryColorsFound"].items():
            if _t(v):
                dst["mysteryColorsFound"][c] = True
    if isinstance(src.get("flareMissed"), dict):
        fm = dst["flareMissed"] = dst.get("flareMissed") or {}
        for c, v in src["flareMissed"].items():
            if v is True:
                fm[c] = True
    me = [dst.get("publicId"), src.get("publicId")]
    for k in ("friendsOut", "friendsIn"):
        a = dst.get(k) if isinstance(dst.get(k), list) else []
        dst[k] = [x for x in (a + [x for x in (src.get(k) or []) if x not in a]) if x not in me][:200]
    # this week's board, where both weeks are this week (see the docstring)
    if src.get("weekKey") and week_key and src["weekKey"] == week_key:
        if dst.get("weekKey") == week_key:
            dst["weekPoints"] = _num(dst.get("weekPoints")) + _num(src.get("weekPoints"))
        else:
            out["week_skipped"] = True
    ex = (note or {}).get("extra")
    if isinstance(ex, dict):
        L["points"] = _num(L.get("points")) + _num(ex.get("points"))
        L["correct"] = _num(L.get("correct")) + _num(ex.get("correct"))
        L["answered"] = max(_num(L.get("answered")) + _num(ex.get("correct")), _num(L.get("correct")))
        if ex.get("week") and ex["week"] == dst.get("weekKey"):
            dst["weekPoints"] = _num(dst.get("weekPoints")) + _num(ex.get("weekPoints"))
    bonus = max(0, min(5, _num((note or {}).get("bonusLevels"))))
    if bonus:
        shown = effective_level(dst)
        lp = level_detail(L.get("points"))
        if not lp["at_cap"]:
            target = min(LEVEL_CAP, lp["level"] + bonus)
            base = xp_for_level(target)
            span = level_detail(base)["span"] or 0
            L["points"] = max(_num(L.get("points")), base + _js_round(lp["fraction"] * span))
        gift_to = min(LEVEL_CAP, shown + bonus)
        if effective_level(dst) < gift_to:
            dst["levelFloor"] = max(_num(dst.get("levelFloor")), gift_to)
    dst["lastModified"] = now_ms
    return out


def progress_since_base(src, base):
    """progressSinceBase(src, base): only what `src` holds beyond `base`, for
    the fields merge_leaving_account ADDS. Every max, min, either and union is
    already safe to apply twice, so those are left alone."""
    out = json.loads(json.dumps(src))
    L, BL = out.setdefault("lifetime", {}), base.get("lifetime") or {}
    for k in ADD_LIFETIME:
        L[k] = _less(L.get(k), BL.get(k))
    bs = base.get("stats") or {}
    for k in list((out.get("stats") or {}).keys()):
        a, b = out["stats"][k] or {}, bs.get(k)
        if not _t(b):
            continue
        seen = {x for x in (b.get("r") or []) if _isnum(x)}
        out["stats"][k] = {"n": _less(a.get("n"), b.get("n")), "m": _less(a.get("m"), b.get("m")),
                           "r": [x for x in (a.get("r") or []) if _isnum(x) and x not in seen]}
    bts = base.get("testStats") or {}
    for k in list((out.get("testStats") or {}).keys()):
        a, b = out["testStats"].get(k), bts.get(k)
        if not _t(a) or not _t(b):
            continue
        a["plays"] = _less(a.get("plays"), b.get("plays"))
        a["totalMs"] = _less(a.get("totalMs"), b.get("totalMs"))
    for k in ("studyLog", "unitPerfects", "unitRuns"):
        if not isinstance(out.get(k), dict) or not isinstance(base.get(k), dict):
            continue
        for u in list(out[k].keys()):
            out[k][u] = _less(out[k][u], base[k].get(u))
    had = {t.get("playedAt") for t in (base.get("testHistory") or []) if isinstance(t, dict) and t.get("playedAt")}
    out["testHistory"] = [t for t in (out.get("testHistory") or []) if t and t.get("playedAt") not in had]
    for k in ADD_COUNTERS:
        out[k] = _less(out.get(k), base.get(k))
    if base.get("weekKey") and base["weekKey"] == out.get("weekKey"):
        out["weekPoints"] = _less(out.get("weekPoints"), base.get("weekPoints"))
    return out


def base_of(old):
    """The `base` a merge note carries once the server has folded `old` in: the
    fields progressSinceBase reads, and nothing else (a note must stay small)."""
    L = old.get("lifetime") or {}
    base = {"lifetime": {k: _num(L.get(k)) for k in ADD_LIFETIME},
            "stats": {k: {"n": _num((v or {}).get("n")), "m": _num((v or {}).get("m")),
                          "r": [x for x in ((v or {}).get("r") or []) if _isnum(x)]}
                      for k, v in (old.get("stats") or {}).items()},
            "testStats": {k: {"plays": _num((v or {}).get("plays")), "totalMs": _num((v or {}).get("totalMs"))}
                          for k, v in (old.get("testStats") or {}).items()},
            "testHistory": [{"playedAt": t["playedAt"]} for t in (old.get("testHistory") or [])
                            if isinstance(t, dict) and t.get("playedAt")]}
    for k in ("studyLog", "unitPerfects", "unitRuns"):
        if isinstance(old.get(k), dict):
            base[k] = {u: _num(v) for u, v in old[k].items()}
    for k in ADD_COUNTERS:
        base[k] = _num(old.get(k))
    if old.get("weekKey"):
        base["weekKey"] = old["weekKey"]
        base["weekPoints"] = _num(old.get("weekPoints"))
    return base


def _projection(x):
    """The additive part of a document, for 'is there anything to add'."""
    L = x.get("lifetime") or {}
    return {"life": {k: _num(L.get(k)) for k in ADD_LIFETIME},
            "counters": {k: _num(x.get(k)) for k in ADD_COUNTERS},
            "week": _num(x.get("weekPoints")),
            "stats": {k: (_num((v or {}).get("n")), _num((v or {}).get("m")), len((v or {}).get("r") or []))
                      for k, v in (x.get("stats") or {}).items()},
            "testStats": {k: (_num((v or {}).get("plays")), _num((v or {}).get("totalMs")))
                          for k, v in (x.get("testStats") or {}).items()},
            "maps": {k: {u: _num(v) for u, v in (x.get(k) or {}).items()} if isinstance(x.get(k), dict) else None
                     for k in ("studyLog", "unitPerfects", "unitRuns")},
            "history": sorted(str(t.get("playedAt")) for t in (x.get("testHistory") or []) if t)}


def nothing_to_add(delta, src):
    """True when `delta` (progress_since_base) holds nothing the target lacks:
    it equals what the same account minus ITSELF would give."""
    return _projection(delta) == _projection(progress_since_base(src, base_of(src)))


def fold_evidence(target, old):
    """Is `old` already inside `target`? A test is in both histories only if
    the target took the old account in (two people never share a test), and the
    history is capped, so only the old tests NEWER than the target's oldest
    kept one can be expected to be there."""
    key = lambda h: h.get("playedAt") if isinstance(h, dict) else None
    oh = {key(h) for h in (old.get("testHistory") or []) if key(h)}
    th_list = [key(h) for h in (target.get("testHistory") or []) if key(h)]
    th = set(th_list)
    floor = min(th_list) if len(th_list) >= TEST_HISTORY_MAX else 0
    checkable = {x for x in oh if x >= floor}
    present = checkable & th
    ost, tst = old.get("stats") or {}, target.get("stats") or {}
    covered = sum(1 for k, v in ost.items() if _num((tst.get(k) or {}).get("n")) >= _num((v or {}).get("n")))
    return {"old_tests": len(oh), "checkable": len(checkable), "present": len(present),
            "stats_keys": len(ost), "stats_covered": covered}


def floor_is_ahead(floor, merged):
    """accountAhead(floor, merged) without its test-history clause (the history
    is capped, so an entry the merge pushed off the end says nothing): does the
    high-water mark hold progress the merged account lacks? Then it must be
    healed first (a launch of the target's app does it), never written over."""
    n = _num
    La, Lb = floor.get("lifetime") or {}, merged.get("lifetime") or {}
    tally_keys = ("points", "answered", "correct", "drillPlays", "examPlays", "gamePlays", "perfectTests", "fullTests")
    if any(n(La.get(k)) > n(Lb.get(k)) for k in tally_keys):
        return True
    Ua, Ub = floor.get("unitPerfects") or {}, merged.get("unitPerfects") or {}
    if any(n(Ua[u]) > n(Ub.get(u)) for u in Ua):
        return True
    Ta = floor.get("tally") if isinstance(floor.get("tally"), dict) else {}
    Tb = merged.get("tally") if isinstance(merged.get("tally"), dict) else {}
    for d, m in Ta.items():
        for k, v in (m or {}).items():
            if k[:1] != "W" and n(v) > n((Tb.get(d) or {}).get(k)):
                return True
    Sa, Sb = floor.get("studyLog") or {}, merged.get("studyLog") or {}
    if any(n(Sa[d]) > n(Sb.get(d)) for d in Sa):
        return True
    ca, cb = _clean_classes(floor.get("classes")) or [], _clean_classes(merged.get("classes")) or []
    if any(k not in cb for k in ca):
        return True
    return n(floor.get("socialAt")) > n(merged.get("socialAt"))


def tally_normalize(doc):
    """tallyNormalize(): a count raised by hand on the server goes into the
    BASE, so base + tallies equals the count again and no device later reads the
    difference as its own play. Only for a key that has a base (a copy without
    one is read the old way, higher side wins)."""
    tb, ty = doc.get("tallyBase"), doc.get("tally")
    if not isinstance(tb, dict):
        return
    ty = ty if isinstance(ty, dict) else {}
    for k in list(tb):
        if k[:1] == "L":
            v = _num((doc.get("lifetime") or {}).get(k[2:]))
        elif k[:1] == "U":
            v = _num((doc.get("unitPerfects") or {}).get(k[2:]))
        elif k[:1] == "W":
            if doc.get("weekKey") != k[2:]:
                continue
            v = _num(doc.get("weekPoints"))
        else:
            continue
        s = sum(_num((m or {}).get(k)) for m in ty.values() if isinstance(m, dict))
        if v - s > _num(tb[k]):
            tb[k] = v - s


def _growth(l):
    """levelGrowthAt(): same table as level_of's _curve_level call."""
    if l <= 25: return 1.05
    if l > 50: return min(1.0835, 1 + 0.001 * (l - 50))
    if l > 45: return 1.0835
    if l == 26: return 2.0
    return 1.0199


def _ceiling(l):
    return 9000 if l <= 25 else 150000


def level_detail(points):
    """levelProgress() for the academy: the level, what it costs, how far into
    it. (_curve_level, above, only returns the level.)"""
    p = max(0, float(points or 0))
    lvl, need, spent = 1, 300, 0
    while lvl < LEVEL_CAP and p >= spent + need:
        spent += need; lvl += 1
        need = min(_ceiling(lvl + 1), _js_round(need * _growth(lvl + 1)))
    at_cap = lvl >= LEVEL_CAP
    return {"level": lvl, "spent": spent, "span": 0 if at_cap else need, "at_cap": at_cap,
            "fraction": 1 if at_cap else min(1, max(0, (p - spent) / need))}


def xp_for_level(target):
    lvl, need, spent = 1, 300, 0
    while lvl < target and lvl < LEVEL_CAP:
        spent += need; lvl += 1
        need = min(_ceiling(lvl + 1), _js_round(need * _growth(lvl + 1)))
    return spent


# ---- typed values: the REST shape of a document, both ways ----

_EXOTIC = ("timestampValue", "bytesValue", "referenceValue", "geoPointValue")


def _has_exotic(typed):
    """True if a typed tree holds a value this tool would flatten (a timestamp
    read back as text would be written back as a string)."""
    if isinstance(typed, dict):
        if any(k in typed for k in _EXOTIC):
            return True
        return any(_has_exotic(v) for v in typed.values())
    if isinstance(typed, list):
        return any(_has_exotic(v) for v in typed)
    return False


def _typed_value(v):
    if v is None:
        return {"nullValue": None}
    if isinstance(v, bool):
        return {"booleanValue": v}
    if isinstance(v, int):
        return {"integerValue": str(v)}
    if isinstance(v, float):
        if v.is_integer() and abs(v) < 2 ** 53:
            return {"integerValue": str(int(v))}      # what the app's SDK writes for a whole number
        return {"doubleValue": v}
    if isinstance(v, str):
        return {"stringValue": v}
    if isinstance(v, list):
        return {"arrayValue": {"values": [_typed_value(x) for x in v]} if v else {}}
    if isinstance(v, dict):
        return {"mapValue": {"fields": {k: _typed_value(x) for k, x in v.items()}} if v else {}}
    raise ValueError("cannot encode %r" % type(v))


def _field_path(name):
    import re
    if re.match(r"^[A-Za-z_][A-Za-z_0-9]*$", name):
        return name
    return "`" + name.replace("\\", "\\\\").replace("`", "\\`") + "`"


# ---- the REST transaction ----

def _post(path, body, timeout=60):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode("utf-8"), method="POST")
    req.add_header("Content-Type", "application/json")
    token = _access_token()
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def _resource(coll, doc_id):
    return "%s/%s/%s" % (RESOURCE_ROOT, coll, doc_id)


def _batch_get(refs, tx=None):
    """{ (coll, id): raw document or None } in one round trip, inside the
    transaction when there is one (a read in a transaction is locked until it
    commits or is rolled back, which is what stops a concurrent write)."""
    body = {"documents": [_resource(c, i) for c, i in refs]}
    if tx:
        body["transaction"] = tx
    status, text = _post(":batchGet", body)
    if status != 200:
        raise RuntimeError("batchGet failed: HTTP %s" % status)
    got = {}
    for item in json.loads(text):
        if "found" in item:
            doc = item["found"]
            got[tuple(doc["name"].split("/documents/", 1)[1].split("/", 1))] = doc
    return {ref: got.get(ref) for ref in refs}


def _plain_doc(raw):
    return _plain(raw.get("fields")) if raw else None


def _scrub(text, ids_to_labels):
    """No sync code ever leaves this tool: an error body from Firestore names
    the document it refused, and the document id IS a code."""
    text = str(text)
    for doc_id, label in ids_to_labels.items():
        text = text.replace(doc_id, label)
    return text


def _resolve_old(rows, spec):
    """(code, fields) of the old account `spec` names - a public id, or
    name:<First name> - among the accounts that carry a merge note. Public ids
    in, never codes; a name is exact and must be unique."""
    noted = {c[:-len(MERGE_NOTE_SUFFIX)] for c, f in rows if c.endswith(MERGE_NOTE_SUFFIX)}
    hit = []
    for code, f in rows:
        if "__" in code or code not in noted:
            continue
        if spec.startswith("name:"):
            if f.get("firstName") == spec[5:]:
                hit.append((code, f))
        elif f.get("publicId") == spec:
            hit.append((code, f))
    return hit


def plan_merge_now(target, old, note, floor, now_ms, week_key, hold_sets=None,
                   force=False, allow_no_hold=False, target_pid_count=1):
    """Everything merge-now decides, with no I/O - the thing the self-test
    runs on synthetic documents. Returns:
      refusals  - reasons it will not write (empty = may write)
      warnings  - things worth reading
      mode      - "delta" (the note carries base) or "whole"
      merged    - the target's document after the merge, or None when there is
                  nothing to add
      changed   - the top-level fields that differ
      floor_doc - what the high-water mark becomes (the merged document)
      note_new  - fields to write on the merge note, and note_drop to delete
      whole     - what adding the old account WHOLE would have given (the
                  double-count a naive merge would make), for the report
    """
    refusals, warnings = [], []
    plan = {"refusals": refusals, "warnings": warnings, "mode": None, "merged": None, "changed": [],
            "floor_doc": None, "note_new": {}, "note_drop": [], "whole": None, "evidence": None,
            "hold_skipped": False, "added": {}}
    if target_pid_count != 1:
        refusals.append("the target must be exactly one progress document; found %d carrying its public id" % target_pid_count)
    if not target:
        refusals.append("the target document does not exist")
    if not old:
        refusals.append("the old account's document does not exist")
    if refusals:
        return plan
    base = note.get("base") if isinstance(note.get("base"), dict) else None
    plan["mode"] = "delta" if base else "whole"
    plan["evidence"] = fold_evidence(target, old)
    ev = plan["evidence"]
    # what a naive whole add would do, for the report only
    whole = json.loads(json.dumps(target))
    merge_leaving_account(whole, old, None, now_ms, week_key, {"chars": [], "banners": []})
    plan["whole"] = whole
    if base:
        eff = progress_since_base(old, base)
        if nothing_to_add(eff, old) and not (note.get("bonusLevels") or note.get("extra")):
            plan["nothing"] = True
            return plan
        if note.get("bonusLevels") or note.get("extra"):
            warnings.append("the note carries base AND bonus/extra: the fold that wrote the base may already have paid them")
            if not force:
                refusals.append("bonus/extra on a note that already has a base needs --force")
    else:
        eff = old
        if ev["present"] > 0 and not force:
            refusals.append("%d of the %d old tests that could still be in the target's history ARE there: the old "
                            "account looks already folded in, and a whole add would count it twice (--force overrides)"
                            % (ev["present"], ev["checkable"]))
        elif ev["old_tests"] == 0:
            warnings.append("the old account has no test history, so 'already folded in' cannot be checked")
    merged = json.loads(json.dumps(target))
    info = merge_leaving_account(merged, eff, note, now_ms, week_key, hold_sets)
    plan["hold_skipped"] = info["hold_skipped"]
    if info["hold_skipped"] and not allow_no_hold:
        refusals.append("no mergeHold was written: give --hold-file (from tools/merge-hold-probe.py) so what the merge "
                        "unlocks plays after the next test, or --no-hold to accept it being announced on Home")
    if info["week_skipped"]:
        warnings.append("the old account's weekly points were not carried (the target's week is stale; its own phone rolls it)")
    tally_normalize(merged)
    changed = [k for k in sorted(set(merged) | set(target)) if merged.get(k) != target.get(k) or (k in merged) != (k in target)]
    changed = [k for k in changed if k != "lastModified"] + (["lastModified"] if "lastModified" in changed else [])
    plan["merged"], plan["changed"] = merged, changed
    if floor and floor_is_ahead(floor, merged):
        refusals.append("the high-water mark holds progress the target lacks: open the target's app once so it heals, then re-run")
    plan["floor_doc"] = merged
    L, T = merged.get("lifetime") or {}, target.get("lifetime") or {}
    plan["added"] = {k: _num(L.get(k)) - _num(T.get(k)) for k in ("points", "correct", "answered", "perfectTests", "fullTests")}
    plan["note_new"] = {"base": base_of(old), "serverMergedAt": now_ms,
                        "serverMerged": {"points": plan["added"]["points"], "correct": plan["added"]["correct"]}}
    plan["note_drop"] = [k for k in ("bonusLevels", "extra") if k in note]
    return plan


def family_numbers(f):
    """The numbers worth comparing before and after, from one document."""
    L, up = f.get("lifetime") or {}, f.get("unitPerfects") or {}
    seen = f.get("unlocksShown") or {}
    return {"XP": _num(L.get("points")), "level": effective_level(f), "correct": _num(L.get("correct")),
            "answered": _num(L.get("answered")), "hundos": _num(L.get("perfectTests")),
            "badges": badges_of(f), "full tests": _num(L.get("fullTests")),
            "tests on record": len(f.get("testHistory") or []),
            "study min": round(sum(_num(v) for v in (f.get("studyLog") or {}).values()) / 60000),
            "longest streak": _num(L.get("longestStreak")), "current streak": _num(L.get("currentStreak")),
            "chars announced": len(seen.get("chars") or []), "banners announced": len(seen.get("banners") or [])}


def week_key_now(now_ms):
    """weekKeyNow(): the Monday of this week, in the class's own time zone."""
    import datetime
    try:
        import zoneinfo
        tz = zoneinfo.ZoneInfo(os.environ.get("NOVA_TZ") or "America/Chicago")
    except Exception:
        tz = datetime.timezone.utc
    d = datetime.datetime.fromtimestamp(now_ms / 1000.0, tz)
    d = (d - datetime.timedelta(days=(d.weekday()))).date()
    return d.isoformat()


def _print_family(labels, before, after, whole=None):
    keys = list(before)
    head = "    %-20s %12s %12s %12s" % ("", "before", "after", "change")
    if whole is not None:
        head += " %14s" % "naive whole add"
    print(head)
    for k in keys:
        row = "    %-20s %12s %12s %12s" % (k, "{:,}".format(before[k]), "{:,}".format(after[k]),
                                           "{:+,}".format(after[k] - before[k]) if after[k] != before[k] else "-")
        if whole is not None:
            row += " %14s" % "{:,}".format(whole[k])
        print(row)


def cmd_merge_now(argv):
    """FOLD A DUPLICATE ACCOUNT INTO THE REAL ONE FROM HERE (build 384 r4).

      merge-now <old public id | name:First> [...] [--yes] [--force]
                [--hold-file FILE | --no-hold] [--to PUBLIC-ID]

    Does what the phone would do when it follows the old account's
    progress/<old code>__merge note - mergeLeavingAccount in index.html - but
    on the server, so it no longer depends on that phone. The note is the
    authority: its `to` names the target, its `bonusLevels` and `extra` are
    applied, its `base` (if any) turns the merge into "add only what the old
    account holds beyond what was already folded in".

    DRY RUN BY DEFAULT: reads only, and prints a before/after for each family
    of numbers with accounts labelled acct1, acct2 ... (never a sync code).
    --yes writes, in ONE Firestore transaction (the old account, the target,
    its high-water mark and the note are all read inside it, and the commit
    carries each document's updateTime as a precondition, so any concurrent
    write aborts it and nothing is written):
      - the target's changed fields (every other field untouched);
      - the target's high-water mark (__floor) set to the merged document - it
        only ever rises: if it holds progress the merged account lacks the run
        refuses instead;
      - the note: `base` = the old account as just folded in, `serverMergedAt`,
        and the `bonusLevels`/`extra` already paid are removed. A phone that
        opens the old account later therefore adds only what it played since,
        and a second merge-now of the same pair finds nothing to add.
    The old account's own document is NEVER touched. Deleting it is a separate
    step (see `move --finish`).

    Refuses when: the target's public id is not on exactly one document; a
    note-less old account; a note with no base whose old tests are already in
    the target (it would count the account twice; --force overrides); a merge
    that unlocks something and no --hold-file / --no-hold; a stale
    high-water mark.
    Public ids and `name:` in, never codes."""
    if not admin_ready():
        print("merge-now needs the admin key: the codes are the progress document ids.")
        return 2
    specs, hold_file, to_pid, i = [], None, None, 0
    confirmed, force, no_hold = "--yes" in argv, "--force" in argv, "--no-hold" in argv
    rest = [a for a in argv if a not in ("--yes", "--force", "--no-hold")]
    while i < len(rest):
        if rest[i] == "--hold-file":
            hold_file = rest[i + 1]; i += 2; continue
        if rest[i] == "--to":
            to_pid = rest[i + 1]; i += 2; continue
        specs.append(rest[i]); i += 1
    if not specs or (to_pid and len(specs) != 1):
        print("usage: firestore-admin.py merge-now <old public id | name:First> [...] [--yes] [--force] "
              "[--hold-file FILE | --no-hold] [--to PUBLIC-ID]")
        return 2
    holds = {}
    if hold_file:
        with open(hold_file) as fh:
            holds = json.load(fh)
    rows = docs("progress", mask=["firstName", "publicId", "to"])
    by_pub = {}
    for code, f in rows:
        if "__" not in code and f.get("publicId"):
            by_pub.setdefault(f["publicId"], []).append(code)
    names = {code: f.get("firstName") for code, f in rows}
    status = 0
    for n, spec in enumerate(specs, 1):
        label = "pair %d" % n
        hit = _resolve_old(rows, spec)
        if len(hit) != 1:
            print("%s: %s names %d accounts with a merge note (need exactly one)" % (label, spec if spec.startswith("name:") else "that public id", len(hit)))
            status = 1
            continue
        old_code = hit[0][0]
        note_rows = {c: f for c, f in rows}
        note_stub = note_rows.get(old_code + MERGE_NOTE_SUFFIX) or {}
        to_code = note_stub.get("to")
        if not to_code or (to_code not in names):
            print("%s: the merge note points at an account that does not exist" % label)
            status = 1
            continue
        tgt_pid = (next(f for c, f in rows if c == to_code)).get("publicId")
        ids = {old_code: "acct%d" % (2 * n - 1), to_code: "acct%d" % (2 * n)}
        if to_pid and tgt_pid != to_pid:
            print("%s: the note points at a different account than --to" % label)
            status = 1
            continue
        refs = [("progress", old_code), ("progress", to_code), ("progress", old_code + MERGE_NOTE_SUFFIX),
                ("progress", to_code + FLOOR_SUFFIX)]
        tx = None
        try:
            if confirmed:
                st, text = _post(":beginTransaction", {"options": {"readWrite": {}}})
                if st != 200:
                    raise RuntimeError("beginTransaction failed: HTTP %s" % st)
                tx = json.loads(text)["transaction"]
            raw = _batch_get(refs, tx)
        except Exception as e:
            print("%s: %s" % (label, _scrub(e, ids)))
            status = 1
            continue
        old, target = _plain_doc(raw[refs[0]]), _plain_doc(raw[refs[1]])
        note, floor = _plain_doc(raw[refs[2]]) or {}, _plain_doc(raw[refs[3]])
        now_ms = int(time.time() * 1000)
        wk = week_key_now(now_ms)
        if any(_has_exotic(raw[r].get("fields")) for r in refs[:2] if raw[r]):
            print("%s: a document holds a timestamp/bytes/reference value this tool would flatten; refusing" % label)
            status = 1
            continue
        sets = holds.get(tgt_pid) if holds else None
        plan = plan_merge_now(target, old, note, floor, now_ms, wk, hold_sets=sets, force=force,
                              allow_no_hold=no_hold, target_pid_count=len(by_pub.get(tgt_pid, [])) if tgt_pid else 0)
        print("\n%s: %s (%s) -> %s (%s)   mode: %s" % (label, ids[old_code], names.get(old_code), ids[to_code],
                                                       names.get(to_code), plan["mode"] or "-"))
        _report(plan, old, target, note, raw, refs)
        if plan["refusals"]:
            for r in plan["refusals"]:
                print("  %s %s" % ("REFUSED:" if confirmed else "WOULD REFUSE --yes:", r))
            status = 1
        elif plan.get("nothing"):
            print("  nothing to add: the old account holds nothing beyond its note's base (already folded in).")
        elif not confirmed:
            print("  dry run: nothing written. Re-run with --yes to write.")
        else:
            try:
                ok = _commit_plan(plan, raw, refs, tx, old_code, to_code)
            except Exception as e:
                print("  NOT WRITTEN: %s" % _scrub(e, ids))
                ok = False
            status = status or (0 if ok else 1)
        if tx and (plan["refusals"] or plan.get("nothing")):
            _post(":rollback", {"transaction": tx})
    return status


def _report(plan, old, target, note, raw, refs):
    ev = plan.get("evidence")
    if ev:
        print("  fold check: %d of %d old tests that could still be in the target's history are there; "
              "target's answers cover %d of %d questions the old account saw"
              % (ev["present"], ev["checkable"], ev["stats_covered"], ev["stats_keys"]))
    base = note.get("base")
    print("  note: base %s, bonusLevels %s, extra %s, serverMergedAt %s" % (
        "yes" if isinstance(base, dict) else "no", note.get("bonusLevels", "-"),
        "yes" if note.get("extra") else "-", note.get("serverMergedAt", "-")))
    print("  old account written %s, target written %s" % (
        (raw[refs[0]] or {}).get("updateTime", "?"), (raw[refs[1]] or {}).get("updateTime", "?")))
    if plan.get("whole") is not None:
        before = family_numbers(target)
        after = family_numbers(plan["merged"]) if plan["merged"] else before
        whole = family_numbers(plan["whole"])
        _print_family(None, before, after, whole)
        if plan["mode"] == "delta" and whole["XP"] > before["XP"]:
            print("  FLAG: adding the old account whole (a merge with no base) would count %s XP twice, taking the level "
                  "%d -> %d; this run uses the note's base and adds only the difference."
                  % ("{:,}".format(whole["XP"] - before["XP"]), before["level"], whole["level"]))
    for w in plan["warnings"]:
        print("  note: " + w)


def _floor_fields(merged_fields, floor_raw):
    """What the high-water mark becomes: the merged document, as the app's own
    push writes it (tx.set(fref, doc)). A seam of its own so the self-test can
    prove a floor that is NOT raised gets caught."""
    return merged_fields


def _commit_plan(plan, raw, refs, tx, old_code, to_code):
    """The writes, in ONE commit inside the transaction the reads were made in."""
    t_raw, f_raw, n_raw = raw[refs[1]], raw[refs[3]], raw[refs[2]]
    changed = plan["changed"]
    merged_fields = dict(t_raw["fields"])
    for k in changed:
        if k in plan["merged"]:
            merged_fields[k] = _typed_value(plan["merged"][k])
        else:
            merged_fields.pop(k, None)
    writes = [{"update": {"name": _resource("progress", to_code),
                          "fields": {k: merged_fields[k] for k in changed if k in plan["merged"]}},
               "updateMask": {"fieldPaths": [_field_path(k) for k in changed]},
               "currentDocument": {"updateTime": t_raw["updateTime"]}},
              {"update": {"name": _resource("progress", to_code + FLOOR_SUFFIX), "fields": _floor_fields(merged_fields, f_raw)},
               "currentDocument": ({"updateTime": f_raw["updateTime"]} if f_raw else {"exists": False})}]
    note_fields = {k: _typed_value(v) for k, v in plan["note_new"].items()}
    writes.append({"update": {"name": _resource("progress", old_code + MERGE_NOTE_SUFFIX), "fields": note_fields},
                   "updateMask": {"fieldPaths": [_field_path(k) for k in list(plan["note_new"]) + plan["note_drop"]]},
                   "currentDocument": {"updateTime": n_raw["updateTime"]}})
    st, text = _post(":commit", {"writes": writes, "transaction": tx})
    if st != 200:
        print("  NOT WRITTEN: HTTP %s (a concurrent write aborts the transaction; nothing was changed)" % st)
        return False
    added = plan["added"]
    again = _batch_get([refs[1], refs[3]])
    now_t, now_f = _plain_doc(again[refs[1]]), _plain_doc(again[refs[3]])
    ok = (now_t["lifetime"].get("points") == plan["merged"]["lifetime"].get("points")
          and now_f and now_f["lifetime"].get("points") == plan["merged"]["lifetime"].get("points"))
    print("  WRITTEN: +%s XP, +%s correct, %s field(s) of the target, its high-water mark raised, the note carries the new base."
          % ("{:,}".format(added["points"]), "{:,}".format(added["correct"]), len(changed)))
    print("  read back: target and high-water mark %s" % ("hold the merged XP" if ok else "DO NOT MATCH - look at it"))
    return bool(ok)


# ---------------------------------------------------------------- audit
#
# "Check every single account and ensure everything is fixed and
# everyone's credit and stuff is there." Read-only, and it never prints a
# sync code: accounts are named by firstName, which is what anybody
# reporting a problem calls them by.
#
# What it looks for, each one a way an account has actually gone wrong:
#   - the high-water mark (progress/<code>__floor) holding MORE than the
#     account: an old build's overwrite that no launch has put back yet;
#   - the rankings row holding MORE XP or correct answers than the
#     account: a device that published without saving (build 313 - Rod713,
#     11,075 on the board, 9,070 saved) - that progress is on one phone;
#   - a row whose level does not match its own XP, a row with no account
#     behind it, an opted-in account with no row;
#   - with --backup, anything that has gone DOWN since that backup.
# A row slightly BEHIND its account is normal (rows wait up to 90s) and is
# not reported.

def _js_round(x):
    import math
    return int(math.floor(x + 0.5))


def _curve_level(points, step, late, steep_from=None, steep=None, ease_from=None, ease_step=None):
    p = max(0, float(points or 0))
    lvl, need, spent = 1, 300, 0
    def growth(l):
        if l <= 25: return 1.05
        if ease_from is not None and l > ease_from: return min(steep, 1 + ease_step * (l - ease_from))
        if steep_from is not None and l > steep_from: return steep
        if l == 26: return step
        return late
    def ceiling(l):
        return 9000 if l <= 25 else 150000
    while lvl < LEVEL_CAP and p >= spent + need:
        spent += need; lvl += 1
        need = min(ceiling(lvl + 1), _js_round(need * growth(lvl + 1)))
    return lvl


LEVEL_CAP = 80


def level_of(points):
    """levelProgress() in index.html, step for step - keep the two in step.
    Build 318: build 313's curve through level 50, then each level costs
    0.1% x (level - 50) more than the one before (LEVEL_EASE_FROM /
    LEVEL_EASE_STEP) - 217,910 to level 80, 409,117 to 100."""
    return _curve_level(points, 2.0, 1.0199, 45, 1.0835, 50, 0.001)


def legacy_level_of_points(points):
    """legacyLevelOfPoints(): build 313's curve, kept for one job - the
    grandfather floor is the level an account held on THIS curve."""
    return _curve_level(points, 2.0, 1.0199, 45, 1.0835)


# ---- THE BADGE WALL (build 314) ----
# A copy of what the page asks, so audit can work out the level a row
# MUST say. check-curve.py compares every table here with the page, so
# they cannot drift without a gate going red.
# Questions per unit (unitQuestionCount), the bands (BADGE_THRESHOLD_BANDS)
# and the ranks (TIER_UNLOCKS: level, badges).
UNIT_QUESTIONS = {
    "Professionalism and Ethics": 29, "Professional Policing": 19,
    "Fitness, Wellness, and Stress Management": 28, "TCOLE Rules": 20,
    "Multiculturalism and Human Relations": 35, "Racial Profiling": 13,
    "US and Texas Constitution and Rights": 77, "Penal Code": 340,
    "Code of Criminal Procedure and Bill of Rights": 35, "Arrest, Search, and Seizure": 120,
    "Victims of Crime": 15, "Missing and Exploited Children": 55, "Identity Crimes": 12,
    "Sexual Assault and Family Violence": 36, "Verbal Communication": 29,
    "Civil Process and Liability": 22,
    # build 328: the rest of Level 1
    "Consular Notification": 9, "Crisis Intervention Training": 67, "De-Escalation": 22,
    "Health and Safety Code": 26, "Interacting with Deaf or Hard-of-Hearing": 11,
    "Radio Communications, Alerts, and TCIC-TLETS": 15, "Traumatic Brain Injury": 12,
    "Phonetic Alphabet and Military Time": 39,
}
# build 328: "anything at 15 goes to 10. 12 will go to 8 and so on"
BADGE_BANDS = [(25, 10), (50, 8), (100, 6), (200, 3), (float("inf"), 2)]
# 384.88: Amethyst 16 and Supernova 25 badges (were 12 and 14). RANKS_PREV is the ladder before, for the
# rank floor the app keeps from it (academyLadderMigrate38488) on a copy without academyLadderRule.
RANKS = [(21, 1), (30, 3), (40, 5), (50, 7), (60, 9), (70, 16), (80, 25)]
RANKS_PREV = [(21, 1), (30, 3), (40, 5), (50, 7), (60, 9), (70, 12), (80, 14)]
ACADEMY_LADDER_RULE = 38488


def badge_threshold(unit):
    n = UNIT_QUESTIONS.get(unit, 0)
    if not n: return 35
    return next(h for mx, h in BADGE_BANDS if n <= mx)


def badges_of(f):
    up = f.get("unitPerfects") or {}
    return sum(1 for u in UNIT_QUESTIONS if (up.get(u) or 0) >= badge_threshold(u))


def badge_wall(badges, rank_floor=0, ranks=None):
    """badgeWallLevel() (build 325): the level of the next rank you do not
    hold - the first rank from the one past rank_floor whose badges you do
    not have. 0 badges caps at 21, 1-2 at 30, 3-4 at 40 ... 25 or more at
    the cap (384.88; 14 before)."""
    for lv, b in (ranks or RANKS)[max(0, int(rank_floor or 0)):]:
        if badges < b:
            return min(LEVEL_CAP, lv)
    return LEVEL_CAP


LEVEL_WALL_NO_GRANDFATHER = True


def badge_wall_324(badges):
    """Build 324's cap (the top of the NEXT rank's block - 29, 39, 49 ...),
    for the grandfather floor only (levelWallMigrate325)."""
    met = sum(1 for lv, b in RANKS if badges >= b)
    return min(LEVEL_CAP, RANKS[met + 1][0] - 1) if met + 1 < len(RANKS) else LEVEL_CAP


def effective_level(f):
    """levelStateFor(): min(curve level, max(cap, floor)). A copy without
    levelWallRule (one the app has not loaded since build 325) is read the
    way the app will load it: the level build 324 showed is kept as its
    floor wherever that is above the new cap."""
    pts = ((f.get("lifetime") or {}).get("points")) or 0
    fl = f.get("levelFloor")
    fl = int(fl) if isinstance(fl, (int, float)) else 0
    rf = f.get("rankFloor")
    rf = int(rf) if isinstance(rf, (int, float)) else 0
    b, curve = badges_of(f), level_of(pts)
    # 384.88: a copy the app has not loaded since keeps the rank it held on
    # the previous ladder as its rank floor (academyLadderMigrate38488)
    if pts > 0 and not (isinstance(f.get("academyLadderRule"), (int, float)) and f.get("academyLadderRule") >= ACADEMY_LADDER_RULE):
        lv_prev = min(curve, max(badge_wall(b, rf, RANKS_PREV), fl), LEVEL_CAP)
        held = 0
        for i, (lv, need) in enumerate(RANKS_PREV):
            if lv_prev >= lv and b >= need: held = i + 1
        rf = max(rf, held)
    rule = f.get("levelWallRule")
    # 327: no grandfather floor (the app's LEVEL_WALL_NO_GRANDFATHER) - the
    # branch below is kept only so the tool can be set back with the app.
    if LEVEL_WALL_NO_GRANDFATHER: rule = 325
    if pts > 0 and not (isinstance(rule, (int, float)) and rule >= 325):
        old = min(curve, max(badge_wall_324(b), fl), LEVEL_CAP)
        if old > min(curve, max(badge_wall(b, rf), fl), LEVEL_CAP):
            fl = max(fl, old)
    return min(curve, max(badge_wall(b, rf), fl), LEVEL_CAP)


def _acct_summary(f):
    L = f.get("lifetime") or {}
    up = f.get("unitPerfects") or {}
    return {"xp": L.get("points") or 0, "correct": L.get("correct") or 0,
            "answered": L.get("answered") or 0, "tests": L.get("fullTests") or 0,
            "hundos": sum(v for v in up.values() if isinstance(v, (int, float))),
            "chars": len(((f.get("seenUnlocks") or {}).get("chars")) or [])}


def cmd_audit(argv):
    if not admin_ready():
        print("audit needs the admin key (NOVA_ADMIN_EMAIL / NOVA_ADMIN_PRIVATE_KEY): progress cannot be listed without it")
        return 2
    prog = docs("progress"); lb = dict(docs("leaderboard"))
    main_docs, floors, notes = {}, {}, set()
    for code, f in prog:
        if code.endswith("__floor"): floors[code[:-7]] = f
        elif "__" in code: notes.add(code.split("__")[0])
        else: main_docs[code] = f
    old = {}
    if "--backup" in argv:
        B = json.load(open(argv[argv.index("--backup") + 1]))
        bp = B.get("progress") or []
        for code, f in (bp.items() if isinstance(bp, dict) else bp):
            if "__" not in code and f.get("publicId"): old[f["publicId"]] = _acct_summary(f)
    problems, pids = [], set()
    for code, f in main_docs.items():
        if not f.get("onboardingComplete") or not f.get("publicId"): continue
        pid = f["publicId"]; pids.add(pid)
        name = f.get("firstName") or "?"
        a = _acct_summary(f)
        fl = floors.get(code)
        if fl:
            b = _acct_summary(fl)
            for k in ("xp", "correct", "tests", "hundos"):
                if b[k] > a[k]: problems.append("%s: its high-water mark holds more %s (%s) than the account (%s)" % (name, k, b[k], a[k]))
        r = lb.get(pid)
        moved = code in notes
        if r:
            if (r.get("xp") or 0) > a["xp"] or (r.get("correct") or 0) > a["correct"]:
                problems.append("%s: the rankings row is AHEAD of the account - %s XP / %s correct on the board, %s / %s saved. A device has progress it has not saved."
                                % (name, r.get("xp"), r.get("correct"), a["xp"], a["correct"]))
            # build 314: the row publishes the EFFECTIVE level - the curve,
            # held at the badge wall, never below the grandfather floor -
            # worked out from the progress document's own XP, hundos and
            # floor. Only checked when the row is level with the account
            # (a row waits up to 90s, and an older build publishes the
            # ungated level until it updates).
            if r.get("level") is not None and (r.get("xp") or 0) == a["xp"] and r.get("level") != effective_level(f):
                problems.append("%s: the row says level %s for %s XP, %s badges (should be %s)"
                                % (name, r.get("level"), r.get("xp"), badges_of(f), effective_level(f)))
        elif f.get("leaderboardOptIn") and not moved:
            problems.append("%s: opted in to the rankings but has no row" % name)
        o = old.get(pid)
        if o:
            for k in ("xp", "correct", "answered", "tests", "hundos", "chars"):
                if o[k] > a[k]: problems.append("%s: %s went DOWN since the backup, %s -> %s" % (name, k, o[k], a[k]))
    for pid, r in lb.items():
        if pid not in pids and pid != "presence-v1":
            problems.append("row with no account behind it: %s (level %s)" % (r.get("firstName"), r.get("level")))
    print("%d accounts, %d rankings rows checked" % (len(pids), len(lb)))
    for line in problems: print("  - " + line)
    print("no problems found" if not problems else "%d problem(s)" % len(problems))
    return 1 if problems else 0


def cmd_fixlevels(argv):
    """Bring every rankings row's `level` to the level the app itself works
    out for that account (effective_level: the curve, held at the next
    rank's level by the badges, no grandfather floor since build 327).

    A row is published by the phone that owns the account, from that
    phone's own build, so after a rule change every row keeps its old
    level until that phone opens the new build. This corrects the ones
    that have not yet. It writes ONLY the `level` field (updateMask), and
    only on a row that is level with its account (same XP) - a row ahead
    of or behind its account belongs to a phone that has not saved, and is
    left for that phone. Dry run unless --yes; the rows are saved to a
    backup file first. A phone on the new build writes the same number, so
    nothing is ever fought over; a phone on an older build writes its old
    level back the next time it publishes, until it updates."""
    if not admin_ready():
        print("fixlevels needs the admin key (NOVA_ADMIN_EMAIL / NOVA_ADMIN_PRIVATE_KEY)")
        return 2
    prog = docs("progress"); lb = dict(docs("leaderboard"))
    todo, backup = [], {}
    for code, f in prog:
        if "__" in code or not f.get("onboardingComplete") or not f.get("publicId"):
            continue
        pid = f["publicId"]; r = lb.get(pid)
        if not r or r.get("level") is None:
            continue
        a = _acct_summary(f)
        if (r.get("xp") or 0) != a["xp"]:
            continue
        want = effective_level(f)
        if r.get("level") != want:
            todo.append((pid, r.get("firstName") or "?", r.get("level"), want))
            backup[pid] = {"firstName": r.get("firstName"), "level": r.get("level"), "xp": r.get("xp")}
    for pid, name, have, want in todo:
        print("  %-24s level %s -> %s" % (name, have, want))
    print("%d row(s) to correct" % len(todo))
    if not todo:
        return 0
    if "--yes" not in argv:
        print("dry run - nothing written. Re-run with --yes to write.")
        return 0
    path = "levels-backup-%s.json" % time.strftime("%Y%m%d-%H%M%S")
    with open(path, "w") as fh:
        json.dump(backup, fh, indent=1)
    print("backed up the old levels to %s" % path)
    bad = 0
    for pid, name, have, want in todo:
        st = _write_fields("leaderboard", pid, {"level": int(want)}, mask=["level"])
        if st != 200:
            bad += 1
            print("  %s: write failed (%s)" % (name, st))
    print("done, %d failed" % bad)
    return 1 if bad else 0


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
    if cmd == "audit":
        return cmd_audit(argv[2:])
    if cmd == "fixlevels":
        return cmd_fixlevels(argv[2:])
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
    if cmd == "move":
        return cmd_move(argv[2:])
    if cmd == "merge":
        return cmd_merge(argv[2:])
    if cmd == "credit":
        return cmd_credit(argv[2:])
    if cmd == "merge-now":
        return cmd_merge_now(argv[2:])
    print("Unknown command %r" % cmd)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
