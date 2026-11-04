"""Build 384: Fire Code's badge case - no open spot, the badges bigger.
Madison: "The badge case for the ifc. Is there a better layout? If you are looking at the entire case, there's an entire open spot
on the bottom right, when looking at the entire case too, if they could be just a smidge bigger too, that'd be great."
iPhone 17 Pro Max (440x956), the Badges page, read off the page:
(1) Fire Code (58 badges): every row but the last is full, and the last row is centred in the case's well - the room left of its
    first badge equals the room right of its last (within 1px) - so no open corner;
(2) its badges are the academy case's size (within 1px), bigger than the eight-across they were;
(3) the academy's case is unchanged: six by four, every row full, nothing moved;
(4) the 3D badge scene's grid (badgeCaseGrid) is unchanged for both (it stands the case upright);
(6) "The badge one isn't the same size, ensure it's the same size": the Badges box over the case is the case's width, edge for
    edge (within 1px), at a smaller and a larger text size (the root at 13.6px and 19px - the box's old rem cap followed the
    phone's text size, the case doesn't) and on an iPad;
(5) no page errors.
Run:  python3 tools/check-b384-case.py   (--against OLD/index.html must FAIL)"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b384case"}
exec(src, G)
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = G["g"]["INSET_RE"]
    def _old(ins):
        t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
        return IR.sub(lambda m: v[m.group(1)], OLD)
    G["g"]["patched"] = _old
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)
READ = """()=>{ const well=document.querySelector('#stage .badge-case .bcs-well, #stage .badge-case .badge-case-lining'); if(!well) return null;
  const cs=getComputedStyle(well); const wr=well.getBoundingClientRect();
  const inL=wr.left+parseFloat(cs.paddingLeft)+parseFloat(cs.borderLeftWidth), inR=wr.right-parseFloat(cs.paddingRight)-parseFloat(cs.borderRightWidth);
  const cells=[...well.children].filter(c=>c.getBoundingClientRect().width>0).map(c=>{ const r=c.getBoundingClientRect(); return [r.left, r.top, r.right, r.width]; });
  const rows={}; cells.forEach(c=>{ const k=Math.round(c[1]); (rows[k]=rows[k]||[]).push(c); });
  const ks=Object.keys(rows).map(Number).sort((a,b)=>a-b);
  return { n: cells.length, inL, inR, w: cells.length ? cells[0][3] : 0, rows: ks.map(k=>({ n: rows[k].length, l: Math.min(...rows[k].map(c=>c[0])), r: Math.max(...rows[k].map(c=>c[2])) })),
           scene: (n => badgeCaseGrid(n))(badgeCaseUnits(BADGE_CASES[0]).length), units: badgeCaseUnits(BADGE_CASES[0]).length }; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    out = {}
    allerrs = []
    for cls in ("academy", "ifc"):
        ctx, pg, errs = G["page"](br, G["init"](G["ifc"] if cls == "ifc" else G["academy"], **({} if cls == "ifc" else {"active": "academy"})))
        pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); showRanksScreen('badges'); }"); pg.wait_for_timeout(1800)
        out[cls] = pg.evaluate(READ); allerrs += errs
        ctx.close()
    a, f = out["academy"], out["ifc"]
    full = max(r["n"] for r in f["rows"]) if f and f["rows"] else 0
    body = f and all(r["n"] == full for r in f["rows"][:-1])
    last = f and f["rows"][-1]
    centred = last and abs((last["l"] - f["inL"]) - (f["inR"] - last["r"])) <= 1
    ck1 = f and f["n"] == f["units"] and body and centred
    chk("(1) Fire Code (%s badges): rows %s, the last centred (room %.1f / %.1f)" % (f and f["units"], [r["n"] for r in f["rows"]] if f else None,
        (last["l"] - f["inL"]) if last else -1, (f["inR"] - last["r"]) if last else -1), ck1, f)
    chk("(2) its badges the academy's size (%.1f / %.1f)" % (f["w"] if f else 0, a["w"] if a else 0), f and a and abs(f["w"] - a["w"]) <= 1, [f and f["w"], a and a["w"]])
    afull = a and all(r["n"] == a["rows"][0]["n"] for r in a["rows"]) and len(a["rows"]) == 4 and a["rows"][0]["n"] == 6 and abs(a["rows"][0]["l"] - a["inL"]) <= 1
    chk("(3) the academy's case: six by four, full, unmoved (%s)" % ([r["n"] for r in a["rows"]] if a else None,), afull, a)
    chk("(4) the 3D scene's grid unchanged: academy %s, Fire Code %s" % (a and a["scene"], f and f["scene"]),
        a and f and a["scene"] == {"cols": 6, "rows": 4} and f["scene"] == {"cols": 8, "rows": 8}, [a and a["scene"], f and f["scene"]])
    sizes = []
    for vw, vh, px in ((440, 956, 13.6), (440, 956, 19), (834, 1194, 16)):
        ctx, pg, errs = G["page"](br, G["init"](G["ifc"]))
        pg.set_viewport_size({"width": vw, "height": vh})
        pg.evaluate("(px)=>{ document.documentElement.style.fontSize = px + 'px'; document.getElementById('splashscreen')?.remove(); showRanksScreen('badges'); }", px)
        pg.wait_for_timeout(1500)
        sizes.append((vw, px, pg.evaluate("""()=>{ const R=s=>{ const e=document.querySelector(s); if(!e) return null; const r=e.getBoundingClientRect(); return [r.left, r.right]; };
          return { head: R('#stage .badges-tab > .badges-head'), kase: R('#stage .badges-tab .badge-case') }; }""")))
        allerrs += errs; ctx.close()
    same = all(s and s["head"] and s["kase"] and abs(s["head"][0] - s["kase"][0]) <= 1 and abs(s["head"][1] - s["kase"][1]) <= 1 for _, _, s in sizes)
    chk("(6) the Badges box is the case's width at every text size and on an iPad: %s" % [(vw, px, s and s["head"] and [round(x) for x in s["head"]], s and s["kase"] and [round(x) for x in s["kase"]]) for vw, px, s in sizes],
        same, sizes)
    chk("(5) no page errors", not allerrs, allerrs[:3])
    br.close()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
