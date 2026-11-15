#!/usr/bin/env python3
"""Fire Code chapter objects (384.90): SNAP every part to what it meets, and write tools/chapter-objects/snaps.json, which the merge bakes.

Madison: "I still see a few spots on some where the connections of pieces aren't right. Ensure all the edges are perfect." A part meant to
meet the outline or its neighbour but stopping a fraction short leaves a sliver of the base showing between them, in the base's colour,
with the part's bevel standing a hair inside the edge. tools/chapter-objects/snap.js (run in the page, on the part files as written)
finds every sliver 0.8 units wide or less between a fill part and the outline or another part, gives it to the nearest part, and traces it
to a polygon in that part's own units, overlapping the part and wound with it. tools/merge-chapter-icons.py appends each to its part's
path when it bakes the entries - only to the exact path it was traced for (a hash), so a part file edited since is baked unsnapped until
this is run again (the gate, check-b384-objbadges' joins, reports what is left).
  python3 tools/chapter-objects/snap.py           rewrite snaps.json (after editing a part file; then merge)
  python3 tools/chapter-objects/snap.py --check   exit 1 if snaps.json is stale for the part files
Playwright + /opt/pw-browsers Chromium (the canvas draws the parts exactly as the page does)."""
import json, os, sys, subprocess, tempfile, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__)); TOOLS = os.path.dirname(HERE); ROOT = os.path.dirname(TOOLS)
OUT = os.path.join(HERE, "snaps.json")
def main():
    tmp = tempfile.mkdtemp(prefix="snap-")
    page = os.path.join(tmp, "index.html")
    env = dict(os.environ, NOVA_NO_SNAP="1")
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "merge-chapter-icons.py"), "--out", page], capture_output=True, text=True, env=env)
    if r.returncode != 0:
        print(r.stdout, r.stderr)
        try: os.path.exists(page) and os.remove(page); os.rmdir(tmp)
        except OSError: pass
        sys.exit(2)
    spec = importlib.util.spec_from_file_location("rcb", os.path.join(TOOLS, "render-chapter-badges.py"))
    saved = sys.argv[:]; sys.argv = [saved[0]]
    R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R); sys.argv = saved
    from playwright.sync_api import sync_playwright
    js = open(os.path.join(HERE, "snap.js"), encoding="utf-8").read()
    body = open(page, encoding="utf-8").read()
    try: os.remove(page); os.rmdir(tmp)
    except OSError: pass
    srv, port = R.serve()
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=R.CHROME, args=["--disable-dev-shm-usage"])
        ctx, pg, errs = R.open_page(br, port, R.SEED, 440, 956, 2, "ifc", body)
        res = pg.evaluate(js, {"units": None})
        br.close()
    if errs: print("page errors:", errs[:3]); sys.exit(2)
    text = json.dumps({k: res[k] for k in sorted(res)}, ensure_ascii=False, indent=0, sort_keys=True) + "\n"
    if "--check" in sys.argv:
        old = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
        print("in step" if old == text else "snaps.json is stale (run python3 tools/chapter-objects/snap.py, then merge)")
        sys.exit(0 if old == text else 1)
    open(OUT, "w", encoding="utf-8").write(text)
    n = sum(len(v["plates"]) for v in res.values())
    print("snapped %d part(s) on %d of %d chapter(s)" % (n, sum(1 for v in res.values() if v["plates"]), len(res)))
if __name__ == "__main__":
    main()
