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
  python3 tools/firestore-admin.py purge --yes
"""

import json
import base64
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
    """The service account JSON, or None for an anonymous run."""
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
        sys.stderr.write("NOVA_ADMIN_KEY is set but is not valid JSON.\n")
        return None
    if not key.get("client_email") or not key.get("private_key"):
        sys.stderr.write("NOVA_ADMIN_KEY has no client_email/private_key.\n")
        return None
    return key


def _sign_rs256(message, pem):
    """RS256 over `message`. openssl first, cryptography if it is absent."""
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
            sys.stderr.write(proc.stderr.decode("utf-8", "replace"))
        finally:
            os.unlink(keyfile)
    except FileNotFoundError:
        pass
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    loaded = serialization.load_pem_private_key(pem.encode("utf-8"), password=None)
    return loaded.sign(message, padding.PKCS1v15(), hashes.SHA256())


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


def _plain(fields):
    """Firestore's typed values, flattened to something printable."""
    out = {}
    for key, val in (fields or {}).items():
        if "stringValue" in val:
            out[key] = val["stringValue"]
        elif "integerValue" in val:
            out[key] = int(val["integerValue"])
        elif "doubleValue" in val:
            out[key] = float(val["doubleValue"])
        elif "booleanValue" in val:
            out[key] = val["booleanValue"]
        elif "nullValue" in val:
            out[key] = None
        else:
            out[key] = "<%s>" % ",".join(val.keys())
    return out


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
            stamp = ""
            if isinstance(when, (int, float)) and when:
                stamp = time.strftime("last used %Y-%m-%d",
                                      time.localtime(when / 1000.0))
            print("  %-16s %-11s %s  %s"
                  % (fields.get("firstName", "?"), code,
                     fields.get("lifetime", ""), stamp))
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
    if cmd == "purge":
        return cmd_purge("--yes" in argv)
    print("Unknown command %r" % cmd)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
