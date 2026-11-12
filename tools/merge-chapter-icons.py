#!/usr/bin/env python3
"""Copy the chapter icons into index.html (build 384.61).

Every file tools/chapter-icons/part-*.js holds plain statements of one shape, and only that shape:
    CHAPTER_ICON["Chapter 10: Means of Egress"] = (c) => { ... return `<path .../>...`; };
This script concatenates them (file name order) between the markers
    /* @@CHAPTER_ICON_BEGIN */   and   /* @@CHAPTER_ICON_END */
in index.html, so helpers can draw into separate files without ever editing index.html, and the merge is repeatable.
  python3 tools/merge-chapter-icons.py            write index.html
  python3 tools/merge-chapter-icons.py --check    exit 1 if index.html differs from what the part files would give
  python3 tools/merge-chapter-icons.py --out FILE write the merged page to FILE and leave index.html alone (a helper's scratch copy:
                                                  then  python3 tools/render-chapter-badges.py sheet.png --index FILE --only 3,4)
It refuses (exit 2) a part file that assigns a key twice or that assigns something that is not CHAPTER_ICON["<exact unit name>"],
and a key that is not one of Fire Code's 58 units (read from the unit list kept in tools/chapter-icons/units.json)."""
import glob, json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B, E = "/* @@CHAPTER_ICON_BEGIN */", "/* @@CHAPTER_ICON_END */"
def parts():
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, "tools", "chapter-icons", "part-*.js"))):
        out.append((os.path.basename(f), open(f, encoding="utf-8").read().rstrip() + "\n"))
    return out
def main():
    units = json.load(open(os.path.join(ROOT, "tools", "chapter-icons", "units.json"), encoding="utf-8"))
    names = [u[0] for u in units]
    seen = {}
    for fn, text in parts():
        for m in re.finditer(r'^CHAPTER_ICON\[("(?:[^"\\]|\\.)*")\]\s*=', text, re.M):
            k = json.loads(m.group(1))
            if k not in names: print("%s: %r is not a Fire Code unit" % (fn, k)); sys.exit(2)
            if k in seen: print("%s: %r is already drawn in %s" % (fn, k, seen[k])); sys.exit(2)
            seen[k] = fn
        stray = [l for l in text.split("\n") if l.startswith("CHAPTER_ICON") and not re.match(r'^CHAPTER_ICON\["', l)]
        if stray: print("%s: a CHAPTER_ICON line that is not CHAPTER_ICON[\"...\"] =: %r" % (fn, stray[0][:80])); sys.exit(2)
    body = "".join("/* ---- %s ---- */\n%s" % (fn, t) for fn, t in parts())
    p = os.path.join(ROOT, "index.html"); s = open(p, encoding="utf-8").read()
    i, j = s.index(B) + len(B), s.index(E)
    new = s[:i] + "\n" + body + s[j:]
    if "--check" in sys.argv:
        print("in step" if new == s else "index.html differs from the part files (run tools/merge-chapter-icons.py)")
        sys.exit(0 if new == s else 1)
    if "--out" in sys.argv:
        o = sys.argv[sys.argv.index("--out") + 1]; os.makedirs(os.path.dirname(os.path.abspath(o)), exist_ok=True)
        open(o, "w", encoding="utf-8").write(new); print("wrote %s (%d icon(s))" % (o, len(seen))); return
    open(p, "w", encoding="utf-8").write(new)
    print("merged %d icon(s) from %d file(s)" % (len(seen), len(parts())))
if __name__ == "__main__":
    main()
