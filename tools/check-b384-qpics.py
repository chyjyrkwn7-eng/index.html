#!/usr/bin/env python3
"""Build 384.72: every PICTURE issue of the question audit - the highlight that lands on the wrong words, the table picture that is a title only or too tall, the
county table row that does not say what the table is - holds, in the code box and on the whole page, with the owner's own IFC PDF loaded the way a reader loads it
(Load my IFC PDF), pdf.js served from a local copy, the app's own code path (V.locate + V.computeClip / V.countyClip with the citation the question carries,
IFC_POINTER_PATCH included) and the app's own painters (V.paint, V.paintPages).

  (1) THE HIGHLIGHT COVERS WHAT PROVES THE ANSWER (24 book questions: the 17 the audit listed, ch2-610 / -616 / -618 whose marks ran over their neighbours, and the
      four definitions whose marks changed with the list rule): the text under the gold is the deciding sentence / note / row / list item, whole (every `cover`
      phrase is under a gold mark, letters only), and none of its neighbours is (every `not` phrase is not); the words that decide stand on the strong gold in the
      pixels of BOTH views (share >= 0.6 of the box's non-print pixels, the code box as V.paint lays it and the whole page as V.paintPages does);
      and the gold holds its ink with room on every side (0.3 pt or more, read off the code box at 6 px a point; that it is CENTRED on it is check-b384-onepicture's
      (1e), which is run on these ids).
  (2) THE TALL TABLES ARE WINDOWED (Table 1004.5, 20 questions of Chapter 10): the picture is one sheet of the table's title and column headings, the rows around the
      row asked about (four lines each way) and the table's notes, with a gap that carries the dots of an omission where rows are left out - never taller than 330 pt
      (it was 665) - and holds the table's title, its column headings, the row's label and its value (in the gold, both views), the note that gives the unit; a table
      of few rows with long notes (Table 1017.2) and Table 3206.2 (notes as tall as its rows) are shown whole, as they were.
  (3) THE COUNTY TABLES SAY WHAT THEY ARE (13): the clipping holds the table's title, its subtitle, its column headings, the group the row is under and the row,
      marked: Table 105.5.22 (title and headings on PDF page 17, the rows on 18: both pages are cut, the page line says "PDF pages 17-18"), Exhibit B's Table 1004.5
      (the title and headings, and 801's row from the next page, 90-91, set where the pages print them: a row does not move out of its table).
  (4) NOTHING ELSE MOVES: the segments and marks of all of the bank's content questions (1,657: the book's, the county booklet's) are read on this build and on
      the base (origin/main, or --base REV); the ids that differ are exactly the ones this build set out to change (EXPECTED), and each of them does differ.
Run:  PDFJS_DIR=<unpacked pdfjs-dist 5.4.149> IFC_BOOK=<the owner's 2021 IFC PDF> python3 tools/check-b384-qpics.py [--against REV|FILE] [--base REV] [--only 1,2,3,4]
      (--against origin/main: (1)-(3) FAIL on every id this build fixes; (4) is not run.)
The book never goes into the repo (it is public): its path is given when the gate is run."""
import os, sys, json, re, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
_argv = sys.argv[:]
BASE = "origin/main"
if "--base" in _argv:
    i = _argv.index("--base"); BASE = _argv[i + 1]; _argv = _argv[:i] + _argv[i + 2:]
ONLY = None
if "--only" in _argv:
    i = _argv.index("--only"); ONLY = set(_argv[i + 1].split(",")); _argv = _argv[:i] + _argv[i + 2:]
sys.argv = _argv
src = open(os.path.join(HERE, "check-b384-ifcmarks.py"), encoding="utf-8").read().split("SPAGE = 1.7")[0]
G0 = {"__file__": os.path.join(HERE, "check-b384-ifcmarks.py"), "__name__": "b384qpics"}
exec(src, G0)                                                  # the harness: open_app, load_book, the --against machinery, the book's path
sync_playwright = G0["sync_playwright"]; AGAINST = G0["AGAINST"]
def want(k): return ONLY is None or k in ONLY
passed = [True]
def chk(name, cond, info=""):
    passed[0] = passed[0] and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:1800], flush=True)
def nz(s): return re.sub(r"[^a-z0-9]", "", str(s).lower())
SP = {"page": 2.5, "clip": 6.0}                                # picture pixels a point: the code box is a column (6 reads a row's room), a whole page at 6 is 4,000 px a side

# ---- (1) the highlight: id -> cover (phrases that must be under the gold), not (phrases that must not), words (the printed runs whose gold share is read)
HL = {
    "chAppC-004": dict(cover=["Reduce by 100 feet for dead-end streets or roads"], words=[r"Reduce by 100 feet"]),
    "chAppC-005": dict(cover=["A 50-percent spacing increase shall be permitted where the building is equipped throughout with an approved automatic sprinkler system"], words=[r"50-percent spacing"]),
    "chAppC-009": dict(cover=["hydrant spacing shall average 500 feet on each side of the street"], words=[r"hydrant spacing shall average 500|500 feet on each"]),
    "chAppC-003": dict(cover=["7,001 or more", "One hydrant for each 1,000 gallons per minute or fraction thereof"], words=[r"One hydrant for each 1,000"]),
    "chAppB-011": dict(cover=["The reduced fire flow shall be not less than 1,000 gallons per minute"], words=[r"not less than 1,000 gallons"]),
    "chAppB-012": dict(cover=["The reduced fire flow shall be not less than 1,500 gallons per minute"], words=[r"not less than 1,500 gallons"]),
    "ch61-022": dict(cover=["Motor vehicle", "fuel dispenser", "20"], words=[r"^20$"]),
    "ch57-066": dict(cover=["a conspicuous label in red letters", "FLAMMABLE KEEP FIRE AWAY"], words=[r"KEEP"]),
    "ch66-712": dict(cover=["Class 3 and 4 unstable (reactive) materials shall be stored in hazardous material storage cabinets", "The hazardous material storage cabinets shall not contain other storage"], words=[r"not contain other storage", r"hazardous material storage cabi"]),
    "ch7-009": dict(cover=["For doors designed to be kept normally closed", "FIRE DOOR KEEP CLOSED"], words=[r"KEEP CLOSED"]),
    "ch6-030": dict(cover=["Cooking operations utilizing solid fuel-burning cooking appliances", "1 month"], words=[r"^1 month$"]),
    "ch62-702": dict(cover=["Class I. Describes those formulations that are capable of deflagration but not detonation"], words=[r"^Class I\."]),
    "ch62-703": dict(cover=["Class IV. Describes those formulations that burn in the same manner as ordinary combustibles and that pose a minimal reactivity hazard"], words=[r"^Class IV\."]),
    "ch33-001": dict(cover=["site safety plan", "The plan shall be submitted and approved before a building permit is issued"], words=[r"^site safety plan$"]),
    "ch22-014": dict(cover=["All other dusts", "critical depth layer specified in Table 2203.1", "1 / 32"], words=[r"^32$"]),
    "ch9b-120": dict(cover=["Maximum distance of travel to extinguisher 75 feet"], words=[r"^75 feet$"]),
    "ch32-052": dict(cover=["I–IV", "Open to the public Yes"], words=[r"^2,501.12,000$", r"^Yes$"]),
    "ch2-610": dict(cover=["Food processing establishments and commercial kitchens not associated with restaurants, cafeterias and similar dining facilities not more than 2,500 square feet (232 m 2 ) in area"],
                    not_=["Educational occupancies", "Electronic data processing", "Dry cleaning", "pick-up and delivery", "Laboratories"], words=[r"^Food processing", r"2,500$"]),
    "ch2-616": dict(cover=["Corrosives", "Highly toxic materials", "Toxic materials"], not_=["Such materials shall include"], words=[r"^Corrosives$", r"^Highly toxic materials$", r"^Toxic materials$"]),
    "ch2-618": dict(cover=["Beverages over 16-percent alcohol content"], not_=["Aerosols", "Baskets", "Belting", "Books and paper", "Dry boat storage"], words=[r"^Beverages over 16-percent"]),
    "ch2-084": dict(cover=["Banquet halls", "Night clubs", "Taverns and bars"], not_=["Casinos", "Restaurants"], words=[r"^Banquet halls$", r"^Night clubs$", r"^Taverns and bars$"]),
    "ch2-094": dict(cover=["Congregate living facilities (transient) with more than 10 occupants"], not_=["Boarding houses", "Hotels", "Motels"], words=[r"^Congregate living"]),
    "ch2-079": dict(cover=["Hotels (nontransient)"], not_=["Apartment houses", "Congregate living", "Boarding houses", "Convents", "Dormitories", "Monasteries", "Live/work", "Motels", "Vacation timeshare"], words=[r"^Hotels \(nontransient"]),
    "ch2-607": dict(cover=["of 13 percent or less by volume with air"], not_=["Has a flammable range"], words=[r"13 percent"]),
}
# ---- (2) Table 1004.5 (Chapter 10): the rows asked about
TABLE_IDS = ["ch10-%03d" % n for n in list(range(142, 155)) + list(range(156, 163))]
ROWVAL = {"Business areas": "150 gross", "Courtrooms\u2014other than fixed seating areas": "40 net", "Day care": "35 net", "Dormitories": "50 gross", "Classroom area": "20 net",
          "Shops and other vocational room areas": "50 net", "Exercise rooms": "50 gross", "Industrial areas": "100 gross", "Inpatient treatment areas": "240 gross",
          "Kitchens, commercial": "200 gross", "Reading rooms": "50 net", "Mercantile": "60 gross", "Parking garages": "200 gross", "Residential": "200 gross",
          "Rink and pool": "50 gross", "Decks": "15 gross", "Stages and platforms": "15 net", "Warehouses": "500 gross"}      # the label of each row the Chapter 10 questions cite, and the value printed beside it
# ---- (3) the county tables
T105 = ["TABLE 105.5.22", "PERMIT AMOUNTS FOR HAZARDOUS MATERIALS", "TYPE OF MATERIAL", "AMOUNT"]
T1004 = ["TABLE 1004.5", "MAXIMUM FLOOR AREA ALLOWANCES PER OCCUPANT", "FUNCTION OF SPACE", "OCCUPANT LOAD FACTOR"]
COUNTY = {
    "ch63-702": (T105, [17, 18], ["Oxidizing materials", "Liquids", "Class 2", "10 gallons"]),
    "ch63-703": (T105, [17, 18], ["Oxidizing materials", "Solids", "Class 1", "500 pounds"]),
    "ch63-704": (T105, [17, 18], ["Oxidizing materials", "Class 4", "Any Amount"]),
    "ch66-701": (T105, [17, 18], ["Unstable (reactive) materials", "Liquids", "Class 2", "5 gallons"]),
    "ch66-702": (T105, [17, 18], ["Unstable (reactive) materials", "Solids", "Class 1", "100 pounds"]),
    "ch66-703": (T105, [17, 18], ["Unstable (reactive) materials", "Class 3", "Any Amount"]),
    "ch66-704": (T105, [17, 18], ["Unstable (reactive) materials", "Class 2", "50 pounds"]),
    "ch67-711": (T105, [17, 18], ["Water-reactive materials", "Solids", "Class 3", "Any Amount"]),
    "ch67-712": (T105, [17, 18], ["Water-reactive materials", "Liquids", "Class 2", "5 gallons"]),
    "ch67-713": (T105, [17, 18], ["Water-reactive materials", "Solids", "Class 1", "500 pounds"]),
    "chExhB-701": (T1004, [90], ["Concentrated (chairs only", "7 net"]),
    "chExhB-702": (T1004, [90], ["Standing space", "5 net"]),
    "chExhB-801": (T1004, [90, 91], ["Assembly without fixed seats", "Unconcentrated (tables and chairs)", "15 net"]),
}
# ids this build sets out to change (relative to origin/main 384.70): the pointers above, ch22-014's 384.71 mark (already in this branch's base build), and the tables of Chapter 10
EXPECTED = set(HL) | set(TABLE_IDS) | set(COUNTY)
ALREADY = {"chAppC-003", "chAppC-004", "chAppC-005", "chAppC-009", "chAppB-011", "chAppB-012", "ch61-022", "ch57-066", "ch66-712", "ch7-009", "ch6-030", "ch62-702", "ch62-703", "ch33-001", "ch9b-120", "ch2-616"}

JS_COUNTY = """async (id) => {
  const V = await ifcViewer(); const doc = await ifcCountyDoc(); const q = QUESTIONS.find(x => x.ifc && x.ifc.id === id), c = q.ifc.citation;
  const clip = await V.countyClip(doc, c, ifcCountyOpts); if (!clip || !clip.ok) return { id, err: 'noclip' };
  const items = {}; for (const p of clip.pages) { const pg = await doc.getPage(p); const tc = await pg.getTextContent(); items[p] = tc.items.filter(i => i.str && i.str.trim()).map(i => ({ s: i.str, x: i.transform[4], y: i.transform[5], w: i.width })); }
  const inSeg = (it, sg) => it.x + it.w / 2 >= sg.x0 && it.x + it.w / 2 <= sg.x1 && it.y >= sg.y0 - 1 && it.y <= sg.y1 + 1;
  const text = clip.segments.map(sg => (items[sg.page] || []).filter(it => inSeg(it, sg)).sort((a, b) => b.y - a.y || a.x - b.x).map(it => it.s).join(' ')).join(' | ');
  const marks = (clip.marks || []).filter(m => m.kind === 'cite' || m.kind === 'row').map(m => {
    const y0 = (m.i0 != null ? m.i0 : m.y0) - 2, y1 = (m.i1 != null ? m.i1 : m.y1) + 2;
    return (items[m.page] || []).filter(it => it.y >= y0 && it.y <= y1 && it.x + it.w / 2 >= m.x0 - 1 && it.x + it.w / 2 <= m.x1 + 1).sort((a, b) => b.y - a.y || a.x - b.x).map(it => it.s).join(' '); });
  return { id, pages: clip.pages.slice(), segs: clip.segments.map(sg => ({ page: sg.page, x0: sg.x0, x1: sg.x1, y0: sg.y0, y1: sg.y1 })), text, marks, pageLine: ifcPageLine(c) };
}"""
JS_SIZE = """async (id) => { const V = await ifcViewer(); const book = await ifcEnsureBook(); const q = QUESTIONS.find(x => x.ifc && x.ifc.id === id), c = q.ifc.citation;
  const loc = V.locate(book.index, c); const clip = await V.computeClip(book.doc, book.index, loc, c, book.opts); const box = document.createElement('div'); document.body.appendChild(box);
  await V.paint(book.doc, clip, box, { scale: 1.7 }); const cv = box.querySelector('canvas'); const r = { w: cv.width, h: cv.height, n: box.querySelectorAll('canvas').length }; box.remove(); return r; }"""
JS_ALL = """async (ids) => {
  const V = await ifcViewer(); const book = await ifcEnsureBook(); const cdoc = await ifcCountyDoc(); const out = {}; const r1 = (v) => v == null ? null : +(+v).toFixed(1);
  for (const id of ids) {
    try {
      const q = QUESTIONS.find(x => x.ifc && x.ifc.id === id), c = q.ifc.citation; let clip;
      if (c.source === 'amendment') clip = await V.countyClip(cdoc, c, ifcCountyOpts);
      else { const loc = V.locate(book.index, c); if (!loc.ok) { out[id] = 'noloc'; continue; } clip = await V.computeClip(book.doc, book.index, loc, c, book.opts); }
      out[id] = (!clip || !clip.ok) ? 'noclip' : JSON.stringify({ pages: clip.pages, segs: (clip.segments || []).map(s => [s.page, r1(s.x0), r1(s.x1), r1(s.y0), r1(s.y1), s.whole ? 1 : 0]),
        marks: (clip.marks || []).map(m => [m.kind, m.page, r1(m.x0), r1(m.x1), r1(m.i0 != null ? m.i0 : m.y0), r1(m.i1 != null ? m.i1 : m.y1)]) });
    } catch (e) { out[id] = 'err ' + String(e).slice(0, 80); }
  }
  return out; }"""

def read_all(base_rev=None):
    """every content question's segments and marks, on this build or on a commit's index.html + viewer"""
    saved = (G0["AGAINST"], G0["VIEWER"])
    if base_rev:
        G0["VIEWER"] = subprocess.check_output(["git", "-C", ROOT, "show", base_rev + ":ifc/ifc-viewer.js"]).decode("utf-8")
        G0["AGAINST"] = subprocess.check_output(["git", "-C", ROOT, "show", base_rev + ":index.html"]).decode("utf-8")
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(executable_path=G0["G"]["g"]["CHROME"], args=["--disable-gpu", "--disable-dev-shm-usage"])
            ctx, pg, errs = G0["open_app"](br, 440, 956, 2)
            G0["load_book"](pg)
            ids = pg.evaluate("()=>QUESTIONS.filter(q => q.ifc && q.ifc.type === 'content').map(q => q.ifc.id)")
            res = {}
            for k in range(0, len(ids), 60): res.update(pg.evaluate(JS_ALL, ids[k:k + 60]))
            br.close()
        return res
    finally:
        G0["AGAINST"], G0["VIEWER"] = saved

# ================================================================== this build
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G0["G"]["g"]["CHROME"], args=["--disable-gpu", "--disable-dev-shm-usage"])
    ctx, pg, errs = G0["open_app"](br, 440, 956, 2)
    acc = G0["load_book"](pg)
    chk("the owner's IFC PDF is accepted by the app", acc, acc)
    pg.evaluate(open(os.path.join(HERE, "b384-ifcmarks-page.js"), encoding="utf-8").read())
    ALLB = list(HL) + TABLE_IDS
    rec, pix = {}, {}
    def rows_of(i): return [x for x in ([rec[i].get("row")] if not isinstance(rec[i].get("row"), list) else rec[i]["row"]) if x]
    for i in ALLB:
        rec[i] = pg.evaluate("(id)=>__im.rec(id)", i)
        if i in HL: words = [{"re": r, "label": r, "comp": True} for r in HL[i]["words"]]
        else: words = [{"re": "^" + re.escape(l) + "$", "label": l, "comp": True} for l in rows_of(i)] + [{"re": "^" + re.escape(ROWVAL[l]) + "$", "label": l + " = " + ROWVAL[l], "comp": True} for l in rows_of(i)]
        for view in ("page", "clip"): pix[(i, view)] = pg.evaluate("([id, w, s, v]) => __im.pixels(id, w, s, v)", [i, words, SP[view], view])
    size = {i: pg.evaluate(JS_SIZE, i) for i in TABLE_IDS}
    county = {i: pg.evaluate(JS_COUNTY, i) for i in COUNTY}
    br.close()

def under(r):                                                  # the text under the gold of a question's clipping, one string per mark
    return [m["text"] for m in r.get("marks", []) if m["kind"] in ("cite", "row")]

# ---- (1) the highlight
if want("1"):
    bad_cov, bad_not, bad_pix, bad_cen, cen = [], [], [], [], {}
    for i, sp in HL.items():
        r = rec[i]; marked = nz(" ".join(under(r)))
        miss = [c for c in sp["cover"] if nz(c) not in marked]
        if miss: bad_cov.append((i, miss))
        extra = [c for c in sp.get("not_", []) if nz(c) in marked]
        if extra: bad_not.append((i, extra))
        for view in ("page", "clip"):
            pr = pix[(i, view)]; ws = pr.get("words", [])
            if pr.get("err") or not ws: bad_pix.append((i, view, pr.get("err") or "no run matched")); continue
            # every word of the spec must stand on gold when allwords, else at least one copy of each regex
            per = {}
            for w in ws: per.setdefault(w["label"], []).append(w["share"])
            low = [(lab, [round(x, 2) for x in sh]) for lab, sh in per.items() if max(sh) < 0.6]
            if low: bad_pix.append((i, view, low))
            c = next((w["comp"] for w in ws if w.get("comp") and w["share"] >= 0.6 and w["comp"]["ix1"] >= 0), None)
            if c:
                top = (c["iy0"] - c["gy0"]) / c["s"]; bot = (c["gy1"] - c["iy1"]) / c["s"]
                if view == "clip" and i != "ch32-052":                 # (a table row's gold is filled to the row's own rules, the table's ink is in the same shape)
                    room = [(c["ix0"] - c["gx0"]) / c["s"], (c["gx1"] - c["ix1"]) / c["s"], top, bot]
                    cen[(i, view)] = round(min(room), 2)
                    if min(room) < 0.3: bad_cen.append((i, view, [round(x, 2) for x in room]))
    chk("(1) the text under the gold holds the whole deciding sentence / note / row / list item, in all %d questions" % len(HL), not bad_cov, bad_cov[:8])
    chk("(1) ... and none of its neighbours (the list items and lines round it are not under the gold)", not bad_not, bad_not[:8])
    chk("(1) the deciding words stand on the strong gold in the pixels of the whole page AND the code box (share >= 0.6)", not bad_pix, bad_pix[:8])
    chk("(1) the gold holds its ink with room on every side (code box, 6 px a point: at least 0.3 pt each way; least %s pt over %d readings). Whether it is CENTRED is check-b384-onepicture's (1e), run on these ids" % (min(cen.values() or [0]), len(cen)), not bad_cen and len(cen) >= 20, (bad_cen[:6], len(cen)))

# ---- (2) Table 1004.5
if want("2"):
    badsheet, badtext, badpix, badsize = [], [], [], []
    for i in TABLE_IDS:
        r = rec[i]; t = nz(r.get("clipText") or ""); segs = r.get("segs") or []
        h = sum(s["y1"] - s["y0"] for s in segs)
        if not (len(segs) >= 2 and h <= 330 and all(s["omit"] for s in segs[1:])): badsheet.append((i, len(segs), round(h), [s["omit"] for s in segs]))
        need = ["MAXIMUM FLOOR AREA ALLOWANCES PER OCCUPANT", "FUNCTION OF SPACE", "OCCUPANT LOAD FACTOR", "Floor area in square feet per occupant"]
        marked = nz(" ".join(under(r)))
        miss = [n for n in need if nz(n) not in t] + ["the label %r under the gold" % l for l in rows_of(i) if nz(l)[:10] not in marked]
        if miss: badtext.append((i, miss))
        for view in ("page", "clip"):
            pr = pix[(i, view)]; ws = pr.get("words", []); per = {}
            for w in ws: per.setdefault(w["label"], []).append(w["share"])
            want_l = [l for l in rows_of(i)] + [l + " = " + ROWVAL[l] for l in rows_of(i)]
            low = [(l, [round(x, 2) for x in per.get(l, [])]) for l in want_l if not per.get(l) or max(per[l]) < 0.6]
            if pr.get("err") or low: badpix.append((i, view, low[:3]))
        sz = size[i]
        if sz["n"] != 1 or sz["h"] > 1.5 * sz["w"]: badsize.append((i, sz))
    chk("(2) Table 1004.5, %d questions: one sheet of title and headings, the rows round the row asked about and the notes, with the gap of an omission between them, <= 330 pt (it was 665)" % len(TABLE_IDS), not badsheet, badsheet[:5])
    chk("(2) ... the picture holds the table's title, its column headings, the note that gives the unit, and the row's label under the gold", not badtext, badtext[:5])
    chk("(2) ... the row's value stands on the gold in the whole page AND in the code box", not badpix, badpix[:5])
    chk("(2) ... the code box is one picture no taller than 1.5 times its width (it was 2.8)", not badsize, badsize[:3])

# ---- (3) the county tables
if want("3"):
    badtitle, badrow, badpages, badline = [], [], [], []
    for i, (title, pages, rowwords) in COUNTY.items():
        r = county[i]
        if r.get("err"): badpages.append((i, r["err"])); continue
        t = nz(r["text"])
        miss = [w for w in title if nz(w) not in t]
        if miss: badtitle.append((i, miss))
        marked = nz(" ".join(r["marks"]))
        missr = [w for w in rowwords if nz(w) not in t] + [w for w in rowwords[-2:] if nz(w) not in marked]
        if missr: badrow.append((i, missr))
        if r["pages"] != pages: badpages.append((i, r["pages"]))
        if len(pages) > 1 and ("PDF pages %d–%d" % (pages[0], pages[-1])) not in r["pageLine"]: badline.append((i, r["pageLine"]))
    chk("(3) the %d county table rows show the table's title, subtitle and column headings" % len(COUNTY), not badtitle, badtitle[:5])
    chk("(3) ... the group the row is under and the row, and the row's own words are under the gold", not badrow, badrow[:5])
    chk("(3) ... cut from the pages that print them (105.5.22: 17-18; 1004.5: 90, and 90-91 for the banquet room)", not badpages, badpages[:5])
    chk("(3) ... and the page line names both pages (\"PDF pages 17–18\")", not badline, badline[:5])

# ---- (4) nothing else moves
if want("4") and AGAINST is None:
    new = read_all(); old = read_all(BASE)
    diff = sorted(k for k in set(new) | set(old) if new.get(k) != old.get(k))
    extra = [k for k in diff if k not in EXPECTED and k != "ch22-014"]
    never = [k for k in EXPECTED if k not in diff and k not in ALREADY]
    moved = [k for k in ALREADY if k in diff]
    chk("(4) of %d content questions only the ones this build set out to change differ from %s (%d differ)" % (len(new), BASE, len(diff)), not extra, extra[:10])
    chk("(4) ... each of the %d it set out to change does differ (the fix is in the pictures, not only in the table)" % len(EXPECTED - ALREADY), not never, never[:10])
    chk("(4) ... and the %d that origin/main already fixes (the 384.56 patches, ch9b-120) and ch2-616 (its patch keeps the three items main marked) are NOT moved" % len(ALREADY), not moved, moved[:10])
    print("    changed: %d of %d; unchanged by design: %d" % (len([k for k in diff if k in EXPECTED]), len(EXPECTED), len(ALREADY)))

chk("no page errors", not errs, errs[:2])
print("\nALL PASS" if passed[0] else "\nFAILURES"); sys.exit(0 if passed[0] else 1)
