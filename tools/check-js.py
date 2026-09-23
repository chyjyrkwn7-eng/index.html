#!/usr/bin/env python3
"""Extract every inline <script> from index.html and run `node --check` on it.

HTML comments are stripped FIRST: the Firebase comment in this file contains
the literal text "<script>", so a naive regex matches inside it and reports a
phantom syntax error on prose.
"""
import sys, re, os, re, subprocess, io, os, sys, tempfile
path = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = io.open(path, encoding='utf-8').read()
s = re.sub(r'<!--.*?-->', '', s, flags=re.S)
blocks = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', s, re.S)
ok = True
for i, b in enumerate(blocks, 1):
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
        f.write(b); p = f.name
    r = subprocess.run(['node', '--check', p], capture_output=True, text=True)
    if r.returncode: ok = False
    print(f"  block {i}: {len(b.splitlines()):6d} lines  {'OK' if r.returncode == 0 else 'FAIL'}")
    if r.returncode: print(r.stderr[:600])
    os.unlink(p)
print(f"{len(blocks)} inline blocks — " + ("ALL PASS" if ok else "SYNTAX ERRORS"))


# ---------------------------------------------------------------- build guard
# TWO THINGS THIS CATCHES, AND BOTH HAVE ALREADY HAPPENED.
#   1. APP_BUILD and version.json's build are one comparison split across two
#      files: bump only version.json and everybody gets a banner reloading can
#      never clear; bump only APP_BUILD and nobody is ever told there is an
#      update. The rule was written down and enforced by nothing.
#   2. It PRINTS the build it just checked. Three tools spent 34 builds serving
#      a frozen copy of the app from a retired repo and passing every time,
#      because nothing they printed said which app they were looking at. A
#      number on screen that does not move when you change the app is the
#      cheapest possible alarm for that.
def _build_guard():
    import json
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    html = io.open(os.path.join(root, "index.html"), encoding="utf-8").read()
    m = re.search(r'const APP_BUILD = "([^"]+)"', html)
    app = m.group(1) if m else None
    try:
        ver = json.load(io.open(os.path.join(root, "version.json")))
        srv = ver.get("build")
    except Exception as e:
        print(f"  version.json unreadable: {e}")
        return 1
    print(f"\n  index.html  APP_BUILD = {app}")
    print(f"  version.json build     = {srv}")
    print(f"  repo                   = {root}")
    if app != srv:
        print("  MISMATCH - they are one comparison split across two files and must bump together")
        return 1
    return 0

sys.exit(0 if (ok and _build_guard() == 0) else 1)
