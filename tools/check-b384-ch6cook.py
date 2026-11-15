#!/usr/bin/env python3
"""Build 384.130: every row of IFC 2021 Table 606.3.3.1 asked in Chapter 6 (Fire Code). Madison (he/him), on the picture of ch6-029: "Chapter 6,
idk how many questions are from this table already, but we need a question over each frequency type of cooking."

THE TABLE (book page 6-8, PDF page 127), under 606.3.3.1 Inspection ("Hoods, grease-removal devices, fans, ducts and other appurtenances shall
be inspected at intervals specified in Table 606.3.3.1 or as approved by the fire code official. Inspections shall be completed by qualified
individuals."), TABLE 606.3.3.1 COMMERCIAL COOKING SYSTEM INSPECTION FREQUENCY:
    High-volume cooking operations such as 24-hour cooking, charbroiling or wok cooking            | 3 months
    Low-volume cooking operations such as places of religious worship, seasonal businesses and senior centers | 12 months
    Cooking operations utilizing solid fuel-burning cooking appliances                              | 1 month
    All other cooking operations                                                                    | 6 months
Before this build: ch6-029 (high-volume, 3 months) and ch6-030 (solid fuel, 1 month), both fill-ins; low-volume and "all other" had none.
This build (tools/gen-ifc-bank.py QUESTION_ADDS `_cook`; ifc/bank.js regenerated): ch6-622 .. ch6-627 - fill-ins for low-volume and all other,
and every row the other way round (the interval given, the operation asked).

WHAT IT HOLDS (this build's index.html + ifc/bank.js against BASE's, the commit this branch was cut from: origin/claude/b384-occload):
 (1) THE BANK: the six are in Chapter 6 after its last question, in order; ids continue past every ch6 id the bank, the app or the notes ever
     named; the schema-5 shape with ch6-029's pointer (section / heading / label / pdfPage / printedPage) plus the row's `find` and `rows: true`;
     a fill-in's options are the table's four intervals ascending, a reverse question's the four row labels as printed in the table's order;
     every other question byte-identical and in BASE's order; the counts are the bank's own (Chapter 6 +6, the bank +6); answer letters spread.
 (2) THE TABLE: every one of its four rows is asked at least twice (a question's row is the one its pointer lights: the row label holding its
     `find` phrase and the row's interval), in two forms (a fill-in and a reverse); each key is the table's value for the row (a fill-in: the
     interval; a reverse: the label, the stem naming that row's interval and no other); a fill-in's stem names its own row and no other one
     (all other's names the three it is not, after "not"); no distractor is a reading of the stem.
 (2b) WITH THE BOOK (PDFJS_DIR + IFC_BOOK, as check-b384-occload; SKIPPED without): each new question's picture lights ONE row, the row it
     asks (its text starts with the row's label and ends with its interval), and verifyCopy finds every new reference.
 (3) IDENTITY: every BASE key unchanged; all keys unique; the new ones take Chapter 6's positions after its last; the identity tables BASE's.
 (4) NOTHING LOST: an account that has MASTERED Chapter 6 (35 hundos: badge, star, "Advanced"), booted on BASE and then on this build, keeps
     every stored field, the badge, star, level, hundos, badge count, rank, level and published row; nothing lowered or owed; merges either way
     lower nothing; the chapter card still shows the badge (novaHeard, the clock-stamped record of Nova's broadcasts, is held to "not lowered").
 (5) COUNTS: Chapter 6 is 47 everywhere (bank, unitQuestionCount, a full run, its card); the class card reads the bank's total.
 (6) THE APP: each new question opened in a Drill at 440x956 shows its stem and four options as the bank has them (no option wider than the
     screen, each 44 px or taller), takes the right answer, and shows the reference line and the code drop-down (Show the code opens, naming
     606.3.3.1 and page 6-8); no page errors.
Run:  [PDFJS_DIR=<pdfjs-dist 5.4.149> IFC_BOOK=<the owner's 2021 IFC PDF>] python3 tools/check-b384-ch6cook.py [--against REV] [--shots DIR] [--pics DIR]
      --against REV: REV's index.html and ifc/bank.js are "this build". Against origin/claude/b384-occload (1), (2), (5) and (6) FAIL (the low-volume
      and all other rows have no question); (3) and (4) hold on both by design. --shots DIR saves each drill (answered, code open) as a PNG.
The book never goes into the repo (it is public): its path is given when the gate is run."""
import os, sys, json, re, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import b384_qfix_lib as L

AGAINST = sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else None
SHOTS = sys.argv[sys.argv.index("--shots") + 1] if "--shots" in sys.argv else None
PICS = sys.argv[sys.argv.index("--pics") + 1] if "--pics" in sys.argv else None     # with the book: each picture as a PNG (keep it OUT of the repo)
def git(*a): return subprocess.run(["git", "-C", ROOT] + list(a), capture_output=True, text=True).stdout
def git_show(rev, path): return git("show", rev + ":" + path)
BASE = os.environ.get("BASE") or git("merge-base", "HEAD", "origin/claude/b384-occload").strip() or "origin/claude/b384-occload"
OLD_HTML, OLD_BANK = git_show(BASE, "index.html"), git_show(BASE, "ifc/bank.js")
OLD_NOTES = git_show(BASE, "docs/notes-archive.md")
assert OLD_HTML and OLD_BANK, "git show %s failed" % BASE
if AGAINST:
    NEW_HTML, NEW_BANK, NEW_VIEW = git_show(AGAINST, "index.html"), git_show(AGAINST, "ifc/bank.js"), git_show(AGAINST, "ifc/ifc-viewer.js")
    assert NEW_HTML and NEW_BANK, "git show %s failed" % AGAINST
else:
    rd = lambda p: open(os.path.join(ROOT, p), encoding="utf-8").read()
    NEW_HTML, NEW_BANK, NEW_VIEW = rd("index.html"), rd("ifc/bank.js"), rd("ifc/ifc-viewer.js")
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:1500], flush=True)
def nz(s): return re.sub(r"[^a-z0-9]", "", str(s).lower())

NEW = ["ch6-%03d" % n for n in range(622, 628)]
CH6 = "6"
# the table as printed (row key, label, interval); a fill-in's stem must name its row by MARK
TABLE = [("high", "High-volume cooking operations such as 24-hour cooking, charbroiling or wok cooking", "3 months"),
         ("low", "Low-volume cooking operations such as places of religious worship, seasonal businesses and senior centers", "12 months"),
         ("solid", "Cooking operations utilizing solid fuel-burning cooking appliances", "1 month"),
         ("other", "All other cooking operations", "6 months")]
MARK = {"high": "high-volume", "low": "low-volume", "solid": "solid fuel-burning", "other": "all other cooking operations"}
INTERVALS = ["1 month", "3 months", "6 months", "12 months"]
LABELS = [t[1] for t in TABLE]
POINTER = {"source": "ifc", "section": "606.3.3.1", "heading": "Inspection", "label": "IFC 2021 606.3.3.1", "pdfPage": 127, "printedPage": "6-8"}

ob, nb = L.bank_of(OLD_BANK), L.bank_of(NEW_BANK)
oq = {q["id"]: q for q in ob["questions"]}; nq = {q["id"]: q for q in nb["questions"]}
# the pointer patch of the build under test (ch6-029's `rows: true` lives there), read as the app reads it: the patch's keys over the bank's
def patch_of(html, qid):
    m = re.search(r'\n  "%s": (\{[^\n]*\}),?\n' % re.escape(qid), html[html.index("const IFC_POINTER_PATCH"):])
    return json.loads(re.sub(r"(\w+):", r'"\1":', m.group(1))) if m else {}
def cited(q, html): return dict(q["citation"], **patch_of(html, q["id"]))

# =========================================================== (1) the bank
SCHEMA = ["id", "unit", "type", "question", "options", "answer", "explanation", "topic", "kind", "citation"]
present = [i for i in NEW if i in nq]
old6 = [q["id"] for q in ob["questions"] if q["unit"] == CH6]
new6 = [q["id"] for q in nb["questions"] if q["unit"] == CH6]
placed = new6 == old6 + NEW
seen = set(int(n) for n in re.findall(r"\bch6-(\d{3})\b", OLD_NOTES + OLD_BANK + OLD_HTML))
top_ever = max(seen)
fresh = [int(i.split("-")[1]) for i in NEW] == list(range(top_ever + 1, top_ever + 1 + len(NEW)))
shape_bad = []
for i in present:
    q = nq[i]; c = q["citation"]; opts = [q["options"].get(k) for k in "ABCD"]; why = []
    if list(q) != SCHEMA: why.append("fields %s" % list(q))
    if q["unit"] != CH6 or q["type"] != "content" or q["kind"] not in ("measure", "other"): why.append("unit/type/kind")
    if sorted(q["options"]) != list("ABCD") or q["answer"] not in "ABCD" or len(set(opts)) != 4: why.append("options")
    if opts not in (INTERVALS, LABELS): why.append("options are not the table's intervals ascending or its labels in order")
    if q["question"].count("_____") > 1 or not q["explanation"].strip() or not q["topic"].strip(): why.append("stem/explanation/topic")
    if {k: v for k, v in c.items() if k not in ("find", "rows")} != POINTER or set(c) != set(POINTER) | {"find", "rows"} or c.get("rows") is not True \
       or not (isinstance(c.get("find"), list) and len(c["find"]) == 2): why.append("pointer is not ch6-029's + find + rows")
    if why: shape_bad.append((i, why))
p29 = {k: v for k, v in oq["ch6-029"]["citation"].items() if k != "find"}
others_bad = [i for i in oq if nq.get(i) != oq[i]]
order_kept = [q["id"] for q in nb["questions"] if q["id"] in oq] == [q["id"] for q in ob["questions"]]
units_ok = all(u["questionCount"] == sum(1 for q in nb["questions"] if q["unit"] == u["id"]) for u in nb["units"]) and nb["meta"]["questionCount"] == len(nb["questions"])
sizes = {u["id"]: u["questionCount"] for u in nb["units"]}; osizes = {u["id"]: u["questionCount"] for u in ob["units"]}
size_ok = sizes.get(CH6) == osizes[CH6] + len(NEW) and all(sizes[u] == osizes[u] for u in osizes if u != CH6) and len(nb["questions"]) == len(ob["questions"]) + len(NEW)
letters = [nq[i]["answer"] for i in present]
from collections import Counter
lc = Counter(letters)
mix_ok = len(present) == len(NEW) and len(lc) >= 3 and max(lc.values()) <= 2
chk("(1) the bank: %d of the %d new questions are in Chapter 6 after its last question, in order (%s); ids continue from the highest ch6 id ever named (ch6-%03d); the shape and ch6-029's pointer (%s) with find + rows (%d bad: %s)" % (
    len(present), len(NEW), placed, top_ever, p29 == POINTER, len(shape_bad), shape_bad[:2]),
    len(present) == len(NEW) and placed and fresh and not shape_bad and p29 == POINTER, {"placed": placed, "fresh": fresh, "bad": shape_bad[:4]})
chk("(1) every other question (%d) is byte-identical to %s's and in the same order (%d differ); counts are the bank's own: Chapter 6 %s -> %s, the bank %d -> %d, every other chapter its size" % (
    len(oq), BASE[:7], len(others_bad), osizes[CH6], sizes.get(CH6), len(ob["questions"]), len(nb["questions"])),
    not others_bad and order_kept and units_ok and size_ok, {"others": others_bad[:4], "order": order_kept, "units": units_ok, "size": size_ok})
chk("(1) answer letters spread: the new six %s (%s); Chapter 6 %s" % ("".join(letters), dict(sorted(lc.items())),
    dict(sorted(Counter(q["answer"] for q in nb["questions"] if q["unit"] == CH6).items()))), mix_ok, letters)

# =========================================================== (2) the table: every row, twice, each key the table's
def row_of(q, html):
    """the row of Table 606.3.3.1 a question's pointer lights: a `find` phrase inside the row's label and one that is its interval"""
    c = cited(q, html)
    if c.get("source") != "ifc" or c.get("section") != "606.3.3.1": return None
    fs = [nz(f) for f in c.get("find") or []]
    hit = [k for k, lab, iv in TABLE if any(f and f in nz(lab) for f in fs)]
    if len(hit) != 1: return ("?", fs)
    k = hit[0]; iv = dict((t[0], t[2]) for t in TABLE)[k]
    return k if (nz(iv) in fs or len(fs) == 1) else ("?", fs)
asked = {k: [] for k, _, _ in TABLE}; strays = []
for q in nb["questions"]:
    r = row_of(q, NEW_HTML)
    if r is None: continue
    if isinstance(r, tuple): strays.append((q["id"], r)); continue
    asked[r].append(q["id"])
wrong = []
for k, lab, iv in TABLE:
    for i in asked[k]:
        q = nq[i]; key = q["options"][q["answer"]]; stem = q["question"].lower(); opts = list(q["options"].values())
        named_iv = [v for v in INTERVALS if re.search(r"(?<!\d)" + re.escape(v) + r"\b", q["question"])]
        if opts == LABELS or (i in present and nq[i]["kind"] == "other"):
            # reverse: the key is the row's label, the stem names its interval and no other one
            if key != lab or named_iv != [iv]: wrong.append((i, "reverse", key[:30], named_iv))
        else:
            # forward: the key is the row's interval; the stem names its own row and no other (all other's names them after "not")
            others = [MARK[o] for o, _, _ in TABLE if o != k and MARK[o] in stem]
            own = MARK[k] in stem or (k == "high" and ("charbroiling" in stem or "wok" in stem)) or (k == "solid" and "solid fuel" in stem)
            if not others: neg = True                                     # it names no other row
            elif k == "other" and " not " in stem: neg = all(stem.index(m) > stem.index(" not ") for m in others)   # all other: the rows it is not
            else: neg = False
            if key != iv or not own or not neg or named_iv: wrong.append((i, "forward", key, own, others))
forms = {k: sorted(set("reverse" if list(nq[i]["options"].values()) == LABELS else "fill-in" for i in v)) for k, v in asked.items()}
chk("(2) every row of Table 606.3.3.1 is asked at least twice (%s), in two forms (%s); no 606.3.3.1 pointer outside a row (%s)" % (
    ", ".join("%s %d: %s" % (k, len(v), " ".join(v)) for k, v in asked.items()), forms, strays or "none"),
    all(len(v) >= 2 for v in asked.values()) and all(f == ["fill-in", "reverse"] for f in forms.values()) and not strays, {"asked": asked, "forms": forms, "strays": strays})
chk("(2) each key is the table's value for its row (a fill-in: the row's interval, its stem naming its row and no other; a reverse: the row's label, its stem naming that row's interval and no other) (%d wrong: %s)" % (
    len(wrong), wrong[:3]), not wrong and sum(len(v) for v in asked.values()) >= 8, wrong[:5])

# =========================================================== the pages
from playwright.sync_api import sync_playwright
PDFJS = os.environ.get("PDFJS_DIR", "").rstrip("/") + "/"; BOOK = os.environ.get("IFC_BOOK", "")
HAVE_BOOK = os.path.exists(PDFJS + "build/pdf.min.mjs") and os.path.isfile(BOOK)
if HAVE_BOOK:
    saved_argv = sys.argv; sys.argv = [saved_argv[0]]
    src = open(os.path.join(HERE, "check-b384-ifcmarks.py"), encoding="utf-8").read().split("SPAGE = 1.7")[0]
    G0 = {"__file__": os.path.join(HERE, "check-b384-ifcmarks.py"), "__name__": "b384ch6cook"}
    exec(src, G0)
    sys.argv = saved_argv
    G = G0["G"]
else:
    G = L.fixture()
IR = G["g"]["INSET_RE"]
def insets(h): return IR.sub(lambda m: {"top": "59px", "right": "0px", "bottom": "34px", "left": "0px"}[m.group(1)], h)
OLD_PAGE, NEW_PAGE = insets(OLD_HTML), insets(NEW_HTML)
errs_all = []

# ---- (2b) with the book: the lit row is the row asked
if not HAVE_BOOK:
    print("SKIP (2b): no book here (PDFJS_DIR / IFC_BOOK not set or not found): the pictures and verifyCopy are not read; (2) holds the keys against the table as printed", flush=True)
else:
    VERIFY = r"""async (ids) => { const V = await ifcViewer(); const book = await ifcEnsureBook();
      const qs = ids.map(id => (QUESTIONS.find(x => x.ifc && x.ifc.id === id) || {}).ifc).filter(Boolean);
      const r = await V.verifyCopy(book.doc, book.index, qs, { sample: Infinity, cache: book.opts.cache, fontBold: book.opts.fontBold });
      return { level: r.level, n: qs.length, differences: r.differences }; }"""
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=G["g"]["CHROME"], args=["--disable-gpu", "--disable-dev-shm-usage"])
        ctx = br.new_context(viewport={"width": 440, "height": 956}, has_touch=True, device_scale_factor=2)
        ctx.route("**/pdfjs-dist@5.4.149/**", G0["pdfjs_route"])
        ctx.route("**/ifc/ifc-viewer.js*", lambda route, request: route.fulfill(status=200, body=NEW_VIEW, content_type="text/javascript"))
        ctx.route("**/ifc/bank.js*", lambda route, request: route.fulfill(status=200, body=NEW_BANK, content_type="text/javascript; charset=utf-8"))
        ctx.add_init_script("window.__cloudSeed = {};"); ctx.add_init_script(G["FAKE"]); ctx.add_init_script(G["g"]["STANDALONE"]); ctx.add_init_script(G["init"](G["ifc"]))
        pg = ctx.new_page(); pg.set_default_timeout(180000); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
        v = re.search(r'const APP_BUILD = "([^"]+)"', NEW_HTML).group(1)
        pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"}, body=json.dumps({"build": v, "force": False, "frameId": ""})))
        pg.route("**/index.html", lambda route, request: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=NEW_PAGE))
        pg.goto(G["serve_url"]); pg.wait_for_timeout(3500)
        acc = G0["load_book"](pg)
        pg.evaluate(open(os.path.join(HERE, "b384-ifcmarks-page.js"), encoding="utf-8").read())
        chk("the owner's IFC PDF is accepted by the app", acc, acc)
        bad = []; seen_rows = {}
        for k, lab, iv in TABLE:
            for i in asked[k]:
                r = pg.evaluate("(id)=>__im.rec(id)", i) or {}
                rm = [m for m in (r.get("marks") or []) if m.get("kind") == "row"]
                t = rm[0]["text"] if len(rm) == 1 else ""
                seen_rows[i] = t[:50]
                if len(rm) != 1 or not nz(t).startswith(nz(lab)[:20]) or not nz(t).endswith(nz(iv)): bad.append((i, len(rm), t[:80]))
                if r.get("pdfPage") != 127 or 127 not in (r.get("pages") or []): bad.append((i, "page", r.get("pdfPage"), r.get("pages")))
                if PICS:
                    import base64
                    os.makedirs(PICS, exist_ok=True)
                    sh = pg.evaluate("([id, v, s]) => __im.shot(id, v, s)", [i, "clip", 2]) or {}
                    for n_, u in enumerate(sh.get("imgs") or []):
                        open(os.path.join(PICS, "%s-%d.png" % (i, n_)), "wb").write(base64.b64decode(u.split(",", 1)[1]))
        ver = pg.evaluate(VERIFY, present) if present else {"level": None, "n": 0, "differences": []}
        errs_all += errs; br.close()
    chk("(2b) each question on the table lights ONE row in its picture, the row it asks (%d bad: %s)" % (len(bad), bad[:3]), not bad and all(asked.values()), {"bad": bad, "rows": seen_rows})
    chk("(2b) verifyCopy finds every new reference where the bank says (%s, %d of %d)" % (ver["level"], ver["n"], len(NEW)), ver["n"] == len(NEW) and ver["level"] == "exact" and not ver["differences"], ver)

# ---- (3)-(6): BASE's app + bank against this build's
STORE_KEY = "class26e.ifc.drill.v1"
def seed_js(fields):
    return ";(()=>{ try{ const k='%s'; const s=JSON.parse(localStorage.getItem(k)||'{}'); Object.assign(s, %s); localStorage.setItem(k, JSON.stringify(s)); }catch(e){} })();" % (STORE_KEY, json.dumps(fields))
SNAP = """(T)=>{
  const answered = QUESTIONS.filter((q, i) => (q.topic || '').trim() === T && store.stats[KEYS[i]] && (store.stats[KEYS[i]].n || 0) > 0).length;
  const right = QUESTIONS.filter((q, i) => (q.topic || '').trim() === T && store.stats[KEYS[i]] && (store.stats[KEYS[i]].n || 0) > (store.stats[KEYS[i]].m || 0)).length;
  let ring = 0; const bk = [...new Set(KEYS)]; bk.forEach(k => { const st = store.stats && store.stats[k]; if(st && (Number(st.n) || 0) > (Number(st.m) || 0)) ring++; });
  const strip = o => { const c = JSON.parse(JSON.stringify(o)); delete c.lastModified; delete c.badgeScenePlayed; delete c.badgeSceneOwed; return c; };
  let row = null; try{ row = JSON.parse(JSON.stringify(buildLeaderboardRow())); ['at','updatedAt','ts','lastModified','seenAt'].forEach(k => delete row[k]); }catch(e){ row = String(e); }
  let rank = null; try{ rank = JSON.stringify(rankOf(store)); }catch(e){ rank = String(e); }
  let lvl = null; try{ lvl = JSON.stringify(levelProgress(store.lifetime.points)); }catch(e){ lvl = null; }
  let pend = null; try{ const p = pendingHomeUnlocks(); pend = { owed: homeUnlocksOwed(p), n: [p.chars.length, p.banners.length, (p.hints||[]).length, (p.fx||[]).length, (p.finds||[]).length] }; }catch(e){ pend = String(e); }
  return { rest: strip(store), perf: unitPerfectCount(T), earned: unitBadgeEarned(T), star: unitDrillStarEarned(T), level: unitLevel(T), size: unitQuestionCount(T), answered, right,
    ring, ringOf: bk.length, ringPct: Math.floor(ring / bk.length * 100), badges: badgesEarnedList(), badgeCount: badgeCountOf(store), hundos: hundosOf(store), row, rank, lvl, pend,
    pending: JSON.parse(JSON.stringify(store.pendingBadgeUnlocks || [])), stats: JSON.parse(JSON.stringify(store.stats)),
    overlay: !!document.querySelector('.cutscene, .tier-cutscene, .badge-cutscene, .unlock-card, .rankup, #tour-overlay') }; }"""
CARDS = """()=>{ cfg.mode = 'drill'; cfg.units = []; showSetup(); return new Promise(r => setTimeout(() => r([...document.querySelectorAll('.picks > label.pick')].map(c => ({
  name: c.querySelector('.pname') && c.querySelector('.pname').textContent, count: c.querySelector('.pcount') && c.querySelector('.pcount').textContent,
  earned: !!c.querySelector('.pick-badge.earned') }))), 1200)); }"""
FULLRUN = """(args)=>{ const t = args.t, n = args.n; cfg.mode = 'drill'; cfg.units = [t]; const idx = []; QUESTIONS.forEach((q, i) => { if((q.topic || '').trim() === t && inWholeUnit(q)) idx.push(i); });
  order = idx.slice(0, n); const part = isFullUnitRun(); order = idx.slice(); return { part, full: isFullUnitRun(), n: idx.length }; }"""
MERGE = """(args)=>{ const a = args.a, b = args.b; const C = o => JSON.parse(JSON.stringify(o));
  const nums = o => { const out = {}; const walk = (p, v) => { if(typeof v === 'number') out[p] = v; else if(v && typeof v === 'object' && !Array.isArray(v)) Object.keys(v).forEach(k => walk(p + '/' + k, v[k])); };
    walk('perf', o.unitPerfects || {}); walk('life', o.lifetime || {}); walk('best', o.unitBestPct || {}); walk('runs', o.unitRuns || {});
    Object.keys(o.stats || {}).forEach(k => { out['n:' + k] = (o.stats[k] || {}).n || 0; out['m:' + k] = (o.stats[k] || {}).m || 0; }); return out; };
  const lower = (m, x, y) => { const ex = nums(x), ey = nums(y), em = nums(m); const bad = []; Object.keys(ex).concat(Object.keys(ey)).forEach(k => { if((em[k] || 0) < Math.max(ex[k] || 0, ey[k] || 0)) bad.push(k); }); return bad; };
  const d1 = C(a); mergeSameAccount(d1, C(b)); const d2 = C(b); mergeSameAccount(d2, C(a)); return { ab: lower(d1, a, b), ba: lower(d2, a, b) }; }"""
OPEN = """(id)=>{ const i = QUESTIONS.findIndex(q=>q.ifc && q.ifc.id===id); if(i < 0) return false; cfg.source='all'; cfg.mode='drill'; cfg.units=[QUESTIONS[i].topic]; beginRun([i]); return true; }"""
SHOWN = """()=>{ const t = document.querySelector('.qpanel .qtext'); const ch = [...document.querySelectorAll('.qpanel .choice')];
  return { stem: t && t.textContent.trim(), choices: ch.map(c => { const b = c.getBoundingClientRect(); return { text: (c.querySelector('.text') || c).textContent.trim(), l: b.left, r: b.right, h: b.height }; }),
    vw: document.documentElement.clientWidth, sw: document.documentElement.scrollWidth }; }"""
TAP_RIGHT = """()=>{ const r=correctSlot(order[pos]); const el=document.querySelector('.qpanel .choice[data-index="'+r+'"]'); if(!el) return null; el.scrollIntoView({block:'center',behavior:'instant'}); const b=el.getBoundingClientRect(); return [b.left+b.width/2, b.top+b.height/2]; }"""
REF = """async ()=>{ const box = document.querySelector('.qpanel .ifc-ref'); if(!box) return null; const lab = box.querySelector('.ifc-label') || document.querySelector('.qpanel .ref:not([hidden])');   /* the bank's ref line sits under the stem (item.ref); else Ref. in the box */ const det = box.querySelector('details.ifc-code');
  const sum = det && det.querySelector('summary'); if(sum && !det.open){ sum.scrollIntoView({block:'center',behavior:'instant'}); sum.click(); }
  await new Promise(r => setTimeout(r, 1200)); const b = det ? det.getBoundingClientRect() : null;
  return { label: lab && lab.textContent.trim(), open: !!(det && det.open), sum: sum && sum.textContent.trim(), ptr: (box.querySelector('.ifc-ptr') || {}).textContent || '',
    pages: (box.querySelector('.ifc-pages') || {}).textContent || '', body: ((box.querySelector('.ifc-code-body') || {}).textContent || '').trim().slice(0, 120), h: b ? b.height : 0,
    expl: ((box.querySelector('.ifc-expl') || {}).textContent || '').trim() }; }"""
with sync_playwright() as pw:
    rig = L.Rig(G, pw)
    _nc = rig.br.new_context
    def _patient(**kw):
        c = _nc(**kw); c.set_default_timeout(180000); c.set_default_navigation_timeout(180000); return c
    rig.br.new_context = _patient
    try:
        old, e0 = rig.read(OLD_PAGE, OLD_BANK); new, e1 = rig.read(NEW_PAGE, NEW_BANK)
        errs_all += e0 + e1
        O = {r["id"]: r for r in old["rows"] if r["id"]}; N = {r["id"]: r for r in new["rows"] if r["id"]}
        # ---- (3) identity
        moved = [i for i in O if i in N and O[i]["key"] != N[i]["key"]]
        allk = [r["key"] for r in new["rows"]]
        T6 = next(s["topic"] for s in new["sizes"] if s["id"] == CH6)
        last_old = max(O[i]["src"] for i in O if O[i]["topic"] == T6)
        new_src = [N[i]["src"] for i in NEW if i in N]
        tabs_same = json.dumps(old["tables"], sort_keys=True) == json.dumps(dict(new["tables"], countText=old["tables"]["countText"]), sort_keys=True)
        chk("(3) identity: all %d of %s's questions keep their exact key (%d moved: %s); all %d keys unique; the new ones take Chapter 6's positions after its last (%s, its last was %d); the identity tables are %s's" % (
            len(O), BASE[:7], len(moved), moved[:3], len(allk), (str(new_src[0]) + "-" + str(new_src[-1])) if new_src else "none", last_old, BASE[:7]),
            not moved and set(O) <= set(N) and len(set(allk)) == len(allk) and tabs_same and new_src == list(range(last_old + 1, last_old + 1 + len(new_src))),
            {"moved": moved[:5], "missing": [i for i in O if i not in N][:4], "tables": tabs_same, "src": new_src[:4]})
        # ---- (4) nothing lost: an account that has mastered Chapter 6
        ch6_keys = [O[i]["key"] for i in O if O[i]["topic"] == T6]
        others = [s["topic"] for s in old["sizes"] if s["id"] in ("1", "2", "10")]
        stats = {k: {"n": 2, "m": 0, "r": [1790000000001, 1790000000002]} for k in ch6_keys}
        for t in others:
            for r in [x for x in old["rows"] if x["topic"] == t][:20]: stats[r["key"]] = {"n": 3, "m": 1, "r": []}
        flagged = {k: 1790000000123 + n for n, k in enumerate(ch6_keys[:5])}
        perf = dict({T6: 35}, **{t: 1 for t in others})
        fields = {"unitPerfects": perf, "stats": stats, "pendingBadgeUnlocks": [], "flagged": flagged, "unitBestPct": {t: 100 for t in perf}, "unitRuns": {t: 4 for t in perf},
                  "lifetime": {"points": 61000, "perfectTests": 38, "answered": 6000, "correct": 5800}}
        ctx, pg, e = rig.open(OLD_PAGE, OLD_BANK, seed_js(fields))
        pg.evaluate("()=>{ try{ const p=pendingHomeUnlocks(); markUnlocksShown(p.chars,p.banners,p.fx); }catch(e){} }")
        before = pg.evaluate(SNAP, T6); saved = pg.evaluate("()=>JSON.parse(JSON.stringify(store))"); errs_all += e; ctx.close()
        ctx, pg, e = rig.open(NEW_PAGE, NEW_BANK, seed_js(saved))
        pg.evaluate("()=>{ try{ const p=pendingHomeUnlocks(); markUnlocksShown(p.chars,p.banners,p.fx); }catch(e){} }")
        after = pg.evaluate(SNAP, T6)
        merged = pg.evaluate(MERGE, {"a": pg.evaluate("()=>JSON.parse(JSON.stringify(store))"), "b": saved})
        cards = {c["name"]: c for c in pg.evaluate(CARDS)}
        run_old = pg.evaluate(FULLRUN, {"t": T6, "n": len(ch6_keys)})
        cls_text = pg.evaluate("()=>ifcQuestionCountText()")
        errs_all += e; ctx.close()
        # novaHeard is the record of Nova's broadcasts the account has had (time stamps, max-merged), written by novaTick while a page is open: it moves
        # with the clock between the two boots, not with the bank. It is held to "nothing lowered" instead of "identical".
        # (384.133 combined) prestige and rim are persisted fields added by other builds (a default each, applyLoadedData): the baseline has neither
        rest_diff = [k for k in set(before["rest"]) | set(after["rest"]) if k not in ("novaHeard", "prestige", "rim") and json.dumps(before["rest"].get(k), sort_keys=True) != json.dumps(after["rest"].get(k), sort_keys=True)]
        nh_b, nh_a = before["rest"].get("novaHeard") or {}, after["rest"].get("novaHeard") or {}
        if any((nh_a.get(k) or 0) < v for k, v in nh_b.items()): rest_diff.append("novaHeard lowered")
        held = all(before[k] == after[k] for k in ("perf", "earned", "star", "level", "badges", "badgeCount", "hundos", "rank", "lvl", "pend")) and \
            json.dumps(before["row"], sort_keys=True) == json.dumps(after["row"], sort_keys=True)
        chk("(4a) an account that has MASTERED Chapter 6 (badge, star, '%s', %d hundos there) keeps all of it on this build: badge, star, level, hundos %s -> %s, badges %s -> %s, rank, level and the published row the same; every stored field identical (%d differ: %s); nothing owed or re-fired" % (
            before["level"], before["perf"], before["hundos"], after["hundos"], before["badgeCount"], after["badgeCount"], len(rest_diff), rest_diff[:4]),
            held and before["earned"] and before["star"] and before["level"] == "mastery" and not rest_diff and after["pending"] == [] and not after["overlay"],
            {"held": held, "rest": rest_diff[:5], "b": {k: before[k] for k in ("perf", "earned", "star", "level", "badgeCount", "hundos")}, "a": {k: after[k] for k in ("perf", "earned", "star", "level", "badgeCount", "hundos")}})
        lowered = [k for k, v in before["stats"].items() if after["stats"].get(k, {}).get("n", 0) < v.get("n", 0) or after["stats"].get(k, {}).get("m", 0) < v.get("m", 0)]
        card = next((c for n, c in cards.items() if n and (n == T6 or n == T6.split(": ", 1)[-1])), None)
        chk("(4b) no answer tally lowered (%d entries, %d lowered); Chapter 6 answered right %d -> %d of %d -> %d questions; the Stats ring's count %d -> %d (share %d%% -> %d%%: %d more questions in the bank, nothing taken); the chapter card still shows the badge (%s)" % (
            len(before["stats"]), len(lowered), before["right"], after["right"], before["size"], after["size"], before["ring"], after["ring"], before["ringPct"], after["ringPct"], after["ringOf"] - before["ringOf"], card and card["earned"]),
            not lowered and after["right"] == before["right"] == len(ch6_keys) and after["ring"] == before["ring"] and card and card["earned"], {"lowered": lowered[:4], "card": card})
        chk("(4c) two devices of one account (%s's bank and this one), merged either way, lower nothing (%s / %s)" % (BASE[:7], merged["ab"][:2] or "ok", merged["ba"][:2] or "ok"),
            not merged["ab"] and not merged["ba"], merged)
        # ---- (5) counts
        S = {s["id"]: s for s in new["sizes"]}; Sb = {s["id"]: s for s in old["sizes"]}
        want6 = Sb[CH6]["n"] + len(NEW)
        chk("(5) Chapter 6 is %d in the bank, unitQuestionCount, a full run and its card (%s) (%s: %d); the class card reads %s; a run of the old %d is a partial run now (%s)" % (
            S[CH6]["n"], card and card["count"], BASE[:7], Sb[CH6]["n"], cls_text, len(ch6_keys), not run_old["part"]),
            S[CH6]["n"] == S[CH6]["cache"] == S[CH6]["run"] == run_old["n"] == want6 and card and card["count"] == "%d questions" % want6
            and cls_text == "{:,}".format(len(nb["questions"])) and new["meta"] == len(nb["questions"]) == len(ob["questions"]) + len(NEW) and run_old["part"] is False and run_old["full"] is True,
            {"sizes": S[CH6], "card": card, "cls": cls_text, "run": run_old})
        # ---- (6) each new question in a Drill at 440x956
        bad6, seen6 = [], []
        for i in NEW:
            ctx, pg, e = rig.open(NEW_PAGE, NEW_BANK)
            pg.evaluate("()=>{ try{ homeUnlocksOwed=()=>false; }catch(e){} document.querySelectorAll('#tour-overlay, #tour-tooltip, #nova-intro, .rs-spot, .unlock-card').forEach(n=>n.remove()); }")
            if not pg.evaluate(OPEN, i): bad6.append((i, "not in the app")); errs_all += e; ctx.close(); continue
            try: pg.wait_for_selector(".qpanel .choice", timeout=60000)
            except Exception: bad6.append((i, "no drill")); errs_all += e; ctx.close(); continue
            pg.wait_for_timeout(900)
            sh = pg.evaluate(SHOWN); q = nq[i]
            texts = [c["text"] for c in sh["choices"]]
            fit = all(c["l"] >= 0 and c["r"] <= sh["vw"] + 0.5 and c["h"] >= 44 for c in sh["choices"]) and sh["sw"] <= sh["vw"]
            ok_stem = nz(sh["stem"]) == nz(q["question"]); ok_opts = sorted(map(nz, texts)) == sorted(map(nz, q["options"].values())) and len(texts) == 4
            ref = None
            for _ in range(6):
                c = pg.evaluate(TAP_RIGHT)
                if c: pg.touchscreen.tap(c[0], c[1])
                pg.wait_for_timeout(1300)
                if pg.evaluate("()=>!!document.querySelector('.qpanel .ifc-ref')"): break
            ref = pg.evaluate(REF)
            good_ref = bool(ref) and "606.3.3.1" in (ref["label"] or "") and ref["open"] and "606.3.3.1" in ref["ptr"] and "6-8" in ref["pages"] and ref["h"] > 40 and nz(ref["expl"]) == nz(q["explanation"])
            if SHOTS:
                os.makedirs(SHOTS, exist_ok=True)
                pg.evaluate("()=>window.scrollTo(0,0)"); pg.screenshot(path=os.path.join(SHOTS, i + "-answered.png"), full_page=True)
            seen6.append((i, round(min([c["h"] for c in sh["choices"]] or [0])), ref and ref["sum"]))
            if not (ok_stem and ok_opts and fit and good_ref): bad6.append((i, ok_stem, ok_opts, fit, ref))
            errs_all += e; ctx.close()
        chk("(6) each new question in a Drill at 440x956: its stem and four options as the bank has them, none wider than the screen, each 44 px or taller; the right answer taken; the reference line and the code drop-down (opened: 606.3.3.1, page 6-8) (%d of %d; %s)" % (
            len(NEW) - len(bad6), len(NEW), seen6[:2]), not bad6, bad6[:3])
    finally:
        rig.close()
chk("no page errors (%s)" % (errs_all[:2] or "none"), not errs_all, errs_all[:4])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
