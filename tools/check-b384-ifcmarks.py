#!/usr/bin/env python3
"""Build 384.56: what an IFC question's code picture MARKS must cover the words that decide the keyed answer - in the code box and on the whole page.

Madison (iPhone, Fire Code, Appendix C: "Average hydrant spacing is allowed to increase by _____ percent where the building is equipped throughout with an approved
automatic NFPA 13 sprinkler system", answer 50): "It doesn't even highlight the answer.. it's just highlighting the title of the table?? These need to be fixed."
The bank's pointer for it names Table C102.1 and nothing else, so the viewer marked the table's caption and not footnote f ("A 50-percent spacing increase shall be
permitted ..."). Three more in Appendix C and one in Chapter 61 were the same; a few sections marked the lead of a list and not the items that answer it.

What this reads, with the owner's own IFC PDF loaded the way a reader loads it (Load my IFC PDF), pdf.js served from a local copy, the app's own code path
(V.locate + V.computeClip with the citation the question carries, the pointer patches included):
  (1) EVERY Fire Code content question (1,270; the Finder's chapter questions are out of scope): the keyed answer's decisive words are inside a gold mark.
      A quantity answer ("50", "1,000 gpm", "4 1/2 inches"): its numbers are printed inside a mark (the book's spelled form counts) or can be worked out from
      the marked numbers and the stem's own (a worked example). Any other answer: every content word of the keyed option is inside the marked text (a plural, a
      spelled number, "annually" for "every year" are the same word), or its whole text is; a group or class named by a code ("R-1", "Class IV") must be printed as
      that code. A heading that is itself the answer (a standard's designation, a defined term, a group's name) is a mark of it. Anything the rule cannot read
      (a paraphrase: "monitoring company" for "the provider of the monitoring service"; a computed answer it cannot derive) is JUDGED BY HAND, one reason per id, in
      tools/b384-ifcmarks-judged.json - the list of exceptions; an id that is not mechanically covered and not in that list fails.
      Verdicts: OK / title only / marks nothing / wrong place (marks text, not the answer's, which is printed outside every mark) / answer not on page (judged).
  (2) THE PICTURES: for every pointer the patch table (IFC_POINTER_PATCH in index.html) gives keys, the decisive words are read off the PIXELS of both views - the
      whole book page (V.paintPages) and the code box (V.paint) - and the share of their box that is the strong gold is at least 0.6 (every printed copy of the
      number that is NOT marked reads 0, so a mark on the wrong copy fails); and the table is still shown, its notes inside the clipping.
  (3) the previous build's marks are reported beside, so a change of what is marked is seen (--diff REV).
  tools/check-b384-highlights.py --ifc-only is the companion: the highlight-end rules (a band from its first glyph to its last, the full stop inside it) for the
  same pointers.
The book never goes into the repo (it is public): its path is given when the gate is run.
Run:  PDFJS_DIR=<unpacked pdfjs-dist 5.4.149> IFC_BOOK=<the owner's 2021 IFC PDF> python3 tools/check-b384-ifcmarks.py [--against REV|FILE.html] [--quick] [--ids a,b]
          [--audit FILE.tsv]      writes the audit table: id, chapter, section, pointer keys, marked text, answer, verdict, what a fix would add
      --against REV (a commit: its index.html AND ifc/ifc-viewer.js are served; a FILE is an index.html and the viewer is origin/main's): against 384.48 (origin/main
      before this) (1) FAILS on 14 questions (4 title only, 10 wrong place) and (2) FAILS on all fifteen it reads (the patch table's fourteen and ch9b-120's table row; chAppC-003's row was accepted by the audit as a computed answer, but its footnote e, which makes it 10, was never marked). (384.71) ch22-014 (Table 2203.1, the answer 1/32, a stacked fraction) is asserted too: against 384.56 (06d2bc3, where it was judged and flagged NOT FIXED) (1) FAILS on it ("wrong place": the label cell and the sentence were marked, the answer cell was not), (2) FAILS (no gold on the lowered 32, in both views) and the centring check FAILS; the whole stacked 1/32 - the raised 1, the slash, the lowered 32 - stands inside the gold in both views with the print centred in it within 0.6 pt.
OUT_JSON=<file> writes every question's record (marks, text) - kept out of the repo like the book."""
import os, sys, json, subprocess, mimetypes, re, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
PDFJS = os.environ.get("PDFJS_DIR", "").rstrip("/") + "/"
BOOK = os.environ.get("IFC_BOOK", "")
if not os.path.exists(PDFJS + "build/pdf.min.mjs") or not os.path.isfile(BOOK):
    print("SKIP: set PDFJS_DIR to an unpacked pdfjs-dist@5.4.149 and IFC_BOOK to the owner's 2021 IFC PDF"); sys.exit(0)
import b384_ifcmarks_lib as L
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b384ifcmarks"}
_argv = sys.argv[:]
for flag in ("--against", "--ids", "--audit"):
    if flag in sys.argv:                                      # the harness reads --against as a file of its own; these are this gate's
        i = sys.argv.index(flag); sys.argv = sys.argv[:i] + sys.argv[i + 2:]
exec(src, G)
sys.argv = _argv
def arg(name): return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else None
AGAINST = VIEWER = None
a = arg("--against")
if a:
    if os.path.isfile(a):
        AGAINST = open(a, encoding="utf-8").read()
        VIEWER = subprocess.check_output(["git", "show", "origin/main:ifc/ifc-viewer.js"], cwd=ROOT).decode("utf-8")
    else:
        AGAINST = subprocess.check_output(["git", "show", a + ":index.html"], cwd=ROOT).decode("utf-8")
        VIEWER = subprocess.check_output(["git", "show", a + ":ifc/ifc-viewer.js"], cwd=ROOT).decode("utf-8")
IDS = arg("--ids").split(",") if arg("--ids") else None
QUICK = "--quick" in sys.argv
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:1500], flush=True)
def pdfjs_route(route, request):
    rel = request.url.split("pdfjs-dist@5.4.149/", 1)[1].split("?")[0]; p = PDFJS + rel
    if not os.path.exists(p): return route.fulfill(status=404, body="")
    ct = "application/wasm" if p.endswith(".wasm") else ("text/javascript" if p.endswith((".mjs", ".js")) else (mimetypes.guess_type(p)[0] or "application/octet-stream"))
    route.fulfill(status=200, body=open(p, "rb").read(), content_type=ct, headers={"access-control-allow-origin": "*"})
def body_for(ins):
    if AGAINST is None: return G["g"]["patched"](ins)
    t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
    return G["g"]["INSET_RE"].sub(lambda m: v[m.group(1)], AGAINST)
def open_app(br, w=440, h=956, dpr=2):
    ctx = br.new_context(viewport={"width": w, "height": h}, has_touch=True, device_scale_factor=dpr)
    ctx.route("**/pdfjs-dist@5.4.149/**", pdfjs_route)
    if VIEWER is not None:
        ctx.route("**/ifc/ifc-viewer.js*", lambda route, request: route.fulfill(status=200, body=VIEWER, content_type="text/javascript"))
    ctx.add_init_script("window.__cloudSeed = {};"); ctx.add_init_script(G["FAKE"]); ctx.add_init_script(G["g"]["STANDALONE"])
    ctx.add_init_script(G["init"](G["ifc"]))
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    if AGAINST is not None:                                       # (the old build is told it is the newest, so it does not reload itself into the current one)
        ob = re.search(r'const APP_BUILD = "([^"]+)"', AGAINST).group(1)
        pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"}, body=json.dumps({"build": ob, "force": False, "frameId": ""})))
    pg.route("**/index.html", lambda route, request, b=body_for((59, 0, 34, 0)): route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.goto(G["serve_url"]); pg.wait_for_timeout(3500)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); try{ homeUnlocksOwed=()=>false; }catch(e){} document.querySelectorAll('#tour-overlay, #tour-tooltip, #nova-intro, .rs-spot, .unlock-card').forEach(n=>n.remove()); }")
    return ctx, pg, errs
def load_book(pg):
    pg.evaluate("()=>{ ifcPickBook(); }"); pg.wait_for_timeout(300)
    pg.set_input_files("#ifc-book-input", BOOK)
    for _ in range(2400):
        if pg.evaluate("()=>!!document.querySelector('.ifc-analyze.is-ok, .ifc-analyze.is-bad')"): break
        pg.wait_for_timeout(250)
    acc = pg.evaluate("()=>{ const o=document.querySelector('.ifc-analyze'); return o ? o.classList.contains('is-ok') : null; }")
    pg.evaluate("()=>{ const b=document.querySelector('.ifc-analyze .ia-actions button'); if(b) b.click(); document.querySelector('.ifc-analyze')?.remove(); }")
    pg.wait_for_timeout(1200)
    return acc

# the pointers the 384.56 patch table gives keys to, and the printed words that decide each answer (regexes on the runs of the page's own text)
tree = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
blk = tree[tree.index("const IFC_POINTER_PATCH = {"):]; blk = blk[: blk.index("\n};")]
PATCHED = re.findall(r'^\s*"([A-Za-z0-9-]+)":\s*\{', blk, re.M)
DECIDING = {                                                  # id -> [(regex, how many printed copies must be gold: 'any' or 'all')]
    "chAppC-004": [(r"Reduce by 100 feet", "any")], "chAppC-005": [(r"50-percent spacing", "any")], "chAppC-009": [(r"hydrant spacing shall average 500|500 feet on each", "any")],
    "chAppC-003": [(r"One hydrant for each 1,000", "any")], "chAppB-011": [(r"not less than 1,000 gallons", "any")], "chAppB-012": [(r"not less than 1,500 gallons", "any")],
    "ch61-022": [(r"^20$", "any")], "ch57-066": [(r"KEEP", "any")], "ch66-712": [(r"not contain other storage", "any"), (r"hazardous material storage cabi", "any")],
    "ch7-009": [(r"KEEP CLOSED", "any")], "ch6-030": [(r"^1 month$", "any")], "ch62-702": [(r"^Class I\.", "any")],
    "ch62-703": [(r"^Class IV\.", "any")], "ch33-001": [(r"^site safety plan$", "any")],
    "ch9b-120": [(r"^75 feet$", "all")],                       # (the row's value cells: a row is marked whole)
    "ch22-014": [(r"^32$", "any")],                            # (384.71) the lowered 32 of the stacked 1/32 (the raised 1 and the slash are read by the centring check below)
}
judged = json.load(open(os.path.join(HERE, "b384-ifcmarks-judged.json"), encoding="utf-8"))
bs = open(os.path.join(ROOT, "ifc", "bank.js"), encoding="utf-8").read(); bank = json.loads(bs[bs.index("{"): bs.rindex("}") + 1])
SPAGE = 1.7
recs = {}
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"], args=["--disable-gpu", "--disable-dev-shm-usage"])
    ctx, pg, errs = open_app(br)
    acc = load_book(pg)
    chk("the owner's IFC PDF is accepted by the app", acc, acc)
    pg.evaluate(open(os.path.join(HERE, "b384-ifcmarks-page.js"), encoding="utf-8").read())
    ids = pg.evaluate("()=>__im.ids()")
    if IDS: ids = [i for i in ids if i in IDS]
    elif QUICK: ids = sorted(set(ids[::9]) | set(DECIDING))
    print("%d IFC content questions (%s); %d pointers carry a patch" % (len(ids), "the build under test" if AGAINST is None else "AGAINST " + a, len(PATCHED)), flush=True)
    for n, i in enumerate(ids):
        for attempt in range(3):
            try: recs[i] = pg.evaluate("(id)=>__im.rec(id)", i); break
            except Exception as e:
                recs[i] = {"id": i, "error": str(e)[:160]}
                if "closed" in str(e).lower() or "crash" in str(e).lower(): break
        if n % 300 == 299: print("  ... %d / %d" % (n + 1, len(ids)), flush=True)
    # ---- (2) the pictures
    pix = {}
    for i in DECIDING:
        if IDS and i not in IDS: continue
        for view in ("page", "clip"):
            for attempt in range(3):
                try:
                    pix[(i, view)] = pg.evaluate("([id, w, s, v]) => __im.pixels(id, w, s, v)", [i, [{"re": r, "label": r, "comp": True} for r, _ in DECIDING[i]], SPAGE, view]); break
                except Exception as e:
                    pix[(i, view)] = {"id": i, "err": str(e)[:160], "words": []}
                    if "closed" in str(e).lower() or "crash" in str(e).lower(): break
    # (384.71) the stacked 1/32 of ch22-014: the gold's box and the print's box inside it, in both views, at 4 px a point (a fraction is the one mark whose ink is not a line of letters)
    frac = {}
    if not IDS or "ch22-014" in IDS:
        for view in ("page", "clip"):
            try: frac[view] = pg.evaluate("([id, w, s, v]) => __im.pixels(id, w, s, v)", ["ch22-014", [{"re": r"^32$", "label": "32", "comp": True}], 4.0, view])
            except Exception as e: frac[view] = {"err": str(e)[:160], "words": []}
    br.close()
if os.environ.get("OUT_JSON"): json.dump(recs, open(os.environ["OUT_JSON"], "w"))

# ---- (1) the audit
verdicts = {i: L.verdict(r) for i, r in recs.items()}
cnt = collections.Counter(v[0] for v in verdicts.values())
print("\nVerdicts over %d questions: %s" % (len(recs), dict(cnt)))
bad = {i: v for i, v in verdicts.items() if v[0] != "OK" and i not in judged}
bad_status = collections.Counter(v[0] for v in bad.values())
print("judged by hand (the exception list, %d of %d): %d questions are in it and not mechanically covered" % (len(judged), len(recs), sum(1 for i, v in verdicts.items() if v[0] != "OK" and i in judged)))
chk("every one of the %d IFC content questions has the words that decide its keyed answer inside a gold mark (or is judged by hand, with a reason, in b384-ifcmarks-judged.json)" % len(recs),
    not bad, "%d fail: %s; first: %s" % (len(bad), dict(bad_status), "; ".join("%s %s" % (i, v[0]) for i, v in list(bad.items())[:14])))
for i, v in list(bad.items())[:40]:
    r = recs[i]; print("    %s [%s] %s: answer %r; marked: %s" % (i, v[0], r.get("section"), r.get("ans"), " / ".join(m["text"][:50] for m in r.get("marks", []))[:200]))
errs_rec = [i for i, r in recs.items() if r.get("error") or r.get("nobook")]
chk("every question was read (no harness error)", not errs_rec, errs_rec[:5])
nocl = [i for i, v in verdicts.items() if v[0] == "no clipping"]
chk("every pointer is found in the book and cut (no whole-page fallback)", not nocl, nocl[:8])
# a judged entry whose question the rule now covers is not wrong, only not needed: said, not failed
unused = [i for i in judged if i in verdicts and verdicts[i][0] == "OK"]
if unused: print("note: %d judged ids are mechanically covered now: %s" % (len(unused), unused[:8]))
# the patched pointers are all OK without being judged
pb = [i for i in PATCHED if i in verdicts and (verdicts[i][0] != "OK")]
chk("the %d patched pointers are covered mechanically, not by judgement" % len(PATCHED), not pb, [(i, verdicts[i][0]) for i in pb][:8])
# a table pointer's clipping still shows the table with its notes
tabs = [i for i in PATCHED if recs.get(i, {}).get("locKind") == "table"]
badtab = [i for i in tabs if not recs[i].get("clipOk") or "TABLE" not in (recs[i].get("clipText") or "").upper() or recs[i].get("whole")]
chk("the %d table pointers still show the table in the clipping (caption, cells, notes)" % len(tabs), not badtab, badtab)
notes_in = [i for i in tabs if re.search(r"(^|\s)[a-h]\.\s", recs[i].get("clipText") or "") or "For SI" in (recs[i].get("clipText") or "")]
chk("... and its notes are inside the clipping (the footnote that decides is shown, and is marked)", len(notes_in) == len(tabs) or not tabs, [i for i in tabs if i not in notes_in])
# ---- (2) the pictures
fails2 = []
for (i, view), r in pix.items():
    if r.get("err") or not r.get("words"): fails2.append((i, view, r.get("err") or "no run of the page's text matched"))
    else:
        mode = DECIDING[i][0][1]; shares = [w["share"] for w in r["words"]]
        if (mode == "all" and min(shares) < 0.6) or (mode == "any" and max(shares) < 0.6):
            fails2.append((i, view, "gold share %s" % [round(x, 2) for x in shares][:6]))
chk("the pictures: for each of the %d pointers fixed (the patch table's %d, and ch9b-120, a table row of a three-line label fixed in the viewer) the decisive words stand on the strong gold, in the whole book page AND the code box (share >= 0.6 of the box's non-print pixels)" % (len(DECIDING), len(PATCHED)), not fails2, fails2[:6])
# (384.71) THE FRACTION'S GOLD IS ROUND ITS WHOLE INK. ch22-014's answer is 1/32, printed stacked: a raised 1, a slash and a lowered 32 (no line of letters). The gold must hold
# all three, with the room round them even - the print's box centred in the gold's box within 0.6 pt each way (the card's own pixels are 3.4 to a point) - and clear of its edges
for view, r in frac.items():
    ws = [w for w in r.get("words", []) if w.get("comp")]
    if r.get("err") or not ws:
        chk("ch22-014 (%s): the stacked 1/32 stands inside a gold mark" % view, False, r.get("err") or "no gold on the lowered 32"); continue
    c = ws[0]["comp"]; sc = c["s"]
    if c["ix1"] < 0:
        chk("ch22-014 (%s): the stacked 1/32 stands inside a gold mark" % view, False, "no print inside the gold"); continue
    room = [(c["ix0"] - c["gx0"]) / sc, (c["gx1"] - c["ix1"]) / sc, (c["iy0"] - c["gy0"]) / sc, (c["gy1"] - c["iy1"]) / sc]   # left, right, top, bottom, in points
    off = [((c["ix0"] + c["ix1"]) - (c["gx0"] + c["gx1"])) / 2 / sc, ((c["iy0"] + c["iy1"]) - (c["gy0"] + c["gy1"])) / 2 / sc]
    wide = (c["ix1"] - c["ix0"]) / sc
    chk("ch22-014 (%s): the whole stacked 1/32 (raised 1, slash, lowered 32: %.1f pt wide, %.1f pt tall) is inside the gold, 0.4 pt clear on every side or more" % (view, wide, (c["iy1"] - c["iy0"]) / sc),
        wide >= 4.5 and min(room) >= 0.4, "room l/r/t/b %s pt, ink %.1f pt wide" % ([round(x, 2) for x in room], wide))
    chk("ch22-014 (%s): the print is centred in the gold within 0.6 pt (across %.2f, down %.2f)" % (view, off[0], off[1]), abs(off[0]) <= 0.6 and abs(off[1]) <= 0.6, "off x %.2f y %.2f pt; room l/r/t/b %s" % (off[0], off[1], [round(x, 2) for x in room]))
for (i, view), r in sorted(pix.items())[:8]: print("    %s %s: %s" % (i, view, [(w["hit"][:20], round(w["share"], 2)) for w in r.get("words", [])][:5]))
chk("no page errors", not errs, errs[:2])

# ---- the audit table
if arg("--audit"):
    def fix_for(i, v):
        r = recs[i]
        if v[0] == "OK": return ""
        if i in judged: return "none (judged: %s)" % judged[i]
        return "add `find` with the decisive words as printed, or `row` + `find` for a table row and its note"
    with open(arg("--audit"), "w", encoding="utf-8") as f:
        f.write("id\tunit\tsection\tpointer keys\tmarked text\tanswer\tverdict\tproposed fix\n")
        for i, r in recs.items():
            v = verdicts[i]
            marked = " | ".join(m["text"] for m in r.get("marks", []))[:160].replace("\t", " ").replace("\n", " ")
            keys = ",".join(r.get("keys", []) or []) or "-"
            f.write("\t".join([i, str(r.get("unit")), str(r.get("section")), keys, marked, str(r.get("ans")).replace("\t", " "), v[0] + (" (judged)" if v[0] != "OK" and i in judged else ""), fix_for(i, v)]) + "\n")
    print("audit table written: %s" % arg("--audit"))
print("\nALL PASS" if ok else "\nFAILURES"); sys.exit(0 if ok else 1)
