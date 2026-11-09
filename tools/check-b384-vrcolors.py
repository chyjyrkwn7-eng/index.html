#!/usr/bin/env python3
"""Build 384 r8: no two people in one Virtual Room share a colour.
Madison, three markers on the race line, two of them violet: "Why are rings the same color".
Against the page's own vroomColorFor(key, participants) - the mapping both the room chat and the race line use:
(1) 400 rooms of 2-12 people (random keys, real join times): every person a different colour, and no near-twins (OKLab: up to
    five people at least .14 apart, six .12, eight .10, eleven .08 - the table's two violets are .08 apart, its two cyans .017); (2) the same room read from a differently
    ordered object gives every person the same colour (every device agrees); (3) a person joining later never changes the
    colour of anybody who joined before them; (4) the race line asks with the room's members (the same answer as its chat);
(5) no page errors.
  python3 tools/check-b384-vrcolors.py [--against OLD/index.html]   (must FAIL on the build before)"""
import os, sys, re, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
SRC = open(os.path.join(os.path.dirname(HERE), "index.html"), encoding="utf-8").read()
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = cb.INSET_RE; SRC = OLD
    cb.patched = lambda ins: IR.sub(lambda m: {"top": "%dpx" % ins[0], "right": "%dpx" % ins[1], "bottom": "%dpx" % ins[2], "left": "%dpx" % ins[3]}[m.group(1)], OLD)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
JS = r"""() => {
  const lab = h => { const n = parseInt(h.slice(1), 16), lin = c => { c /= 255; return c <= .04045 ? c / 12.92 : Math.pow((c + .055) / 1.055, 2.4); };
    const r = lin(n >> 16), g = lin((n >> 8) & 255), b = lin(n & 255);
    const l = Math.cbrt(.4122214708*r + .5363325363*g + .0514459929*b), m = Math.cbrt(.2119034982*r + .6806995451*g + .1073969566*b), q = Math.cbrt(.0883024619*r + .2817188376*g + .6299787005*b);
    return [.2104542553*l + .793617785*m - .0040720468*q, 1.9779984951*l - 2.428592205*m + .4505937099*q, .0259040371*l + .7827717662*m - .808675766*q]; };
  const gap = cols => { let g = 9; for(let i = 0; i < cols.length; i++) for(let j = i + 1; j < cols.length; j++){ const A = lab(cols[i]), B = lab(cols[j]); g = Math.min(g, Math.hypot(A[0]-B[0], A[1]-B[1], A[2]-B[2])); } return g; };
  const need = n => n <= 5 ? .14 : n <= 6 ? .12 : n <= 8 ? .1 : .08;   /* OKLab: the two violets are .08 apart, the two cyans .017 */
  let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  const key = () => Math.floor(rnd() * 1e12).toString(36) + Math.floor(rnd() * 1e9).toString(36);
  const out = { dup: [], famdup: [], order: [], moved: [], rooms: 0 };
  for(let t = 0; t < 400; t++){
    const n = 2 + (t % 11), parts = {};
    for(let i = 0; i < n; i++) parts[key()] = { name: "p" + i, joinedAt: 1000 + i * 37 };
    const ks = Object.keys(parts), cols = ks.map(k => vroomColorFor(k, parts));
    if(new Set(cols).size !== cols.length) out.dup.push([n, cols]);
    if(n <= 11 && gap(cols) < need(n) - 1e-9) out.famdup.push([n, +gap(cols).toFixed(3), cols]);
    const rev = {}; ks.slice().reverse().forEach(k => rev[k] = parts[k]);
    if(ks.some(k => vroomColorFor(k, rev) !== vroomColorFor(k, parts))) out.order.push(n);
    const before = {}; ks.forEach(k => before[k] = vroomColorFor(k, parts));
    const more = Object.assign({}, parts); more[key()] = { name: "late", joinedAt: 999999 };
    if(ks.some(k => vroomColorFor(k, more) !== before[k])) out.moved.push(n);
    out.rooms++;
  }
  out.dupN = out.dup.length; out.famdupN = out.famdup.length; out.dup = out.dup.slice(0, 2); out.famdup = out.famdup.slice(0, 2);
  return out; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    ctx, pg = cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT, dpr=1)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    r = pg.evaluate(JS)
    chk("(1) %d rooms of 2-12: every person a different colour (%d rooms with a repeat)" % (r["rooms"], r["dupN"]), r["dupN"] == 0, r["dup"])
    chk("(1) and no near-twins: up to five people at least .14 apart in OKLab, six .12, eight .10, eleven .08 (%d rooms closer)" % r["famdupN"], r["famdupN"] == 0, r["famdup"])
    chk("(2) every device agrees: the same room in another key order gives the same colours", not r["order"], r["order"][:5])
    chk("(3) a later joiner never changes an earlier person's colour", not r["moved"], r["moved"][:5])
    m = re.search(r"const color = (vroomColorFor\([^;]*?)\n?\s*\|\|\s*VROOM_RACE_COLORS\[i % VROOM_RACE_COLORS\.length\];", SRC, re.S)
    chk("(4) the race line asks with the room's members, as the chat does", bool(m) and "participants" in m.group(1), m.group(1) if m else None)
    chk("(5) no page errors", not errs, errs[:3])
    br.close()
print("ALL PASS" if ok else "FAILURES"); sys.exit(0 if ok else 1)
