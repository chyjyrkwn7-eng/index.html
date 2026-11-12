#!/usr/bin/env python3
"""Question audit, step 3: one PDF per unit (chapter / appendix / exhibit / Chapter finder), phone-sized pages.

Per question, two pages: (1) the question, options and the marked key, the explanation, the reference line the app prints, the cropped picture
the app shows for the citation (with its highlight), and the audit verdict; (2) the whole cited book page with the same highlight.
Run:  python3 tools/qaudit-pdf.py --raw RAWDIR --verdicts verdicts.json --bank ifc/bank.js --out OUTDIR [--unit 1,2] [--max-mb 22]
verdicts.json: id -> {"verdict": "OK"|"FLAG", "severity": "HIGH|MEDIUM|LOW|", "kinds": [...], "reason": "...", "recommendation": "...", "basis": "read|mech", "evidence": "..."}
The pictures come from the owner's own copy of the IFC (tools/qaudit-render.py); the PDFs are the owner's to read and stay out of the repo."""
import os, sys, json, re, html
from reportlab.lib.pagesizes import portrait
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Image, PageBreak, Table, TableStyle, KeepTogether, Flowable
from PIL import Image as PI
from reportlab import rl_config
rl_config.useA85 = 0                     # binary streams: ASCII85 would make every picture a quarter bigger
def arg(n, d=None): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d
RAW, VERD, BANK, OUT = arg("--raw"), arg("--verdicts"), arg("--bank"), arg("--out")
MAXMB = float(arg("--max-mb", "22"))
AFTER = arg("--after")                 # a folder of pictures drawn by the unmerged build 384.56 (the pointer patch), shown under the shipped picture where it differs
os.makedirs(OUT, exist_ok=True)
for name, f in (("LS", "LiberationSans-Regular"), ("LS-B", "LiberationSans-Bold"), ("LS-I", "LiberationSans-Italic"), ("LS-BI", "LiberationSans-BoldItalic")):
    pdfmetrics.registerFont(TTFont(name, "/usr/share/fonts/truetype/liberation/%s.ttf" % f))
pdfmetrics.registerFontFamily("LS", normal="LS", bold="LS-B", italic="LS-I", boldItalic="LS-BI")
W, H = 380, 680; M = 14; CW = W - 2 * M
bs = open(BANK, encoding="utf-8").read(); bank = json.loads(bs[bs.index("{"): bs.rindex("}") + 1])
units = {u["id"]: u for u in bank["units"]}
verd = json.load(open(VERD))
SEV = {"OK": ("#1b7f3b", "OK"), "HIGH": ("#b3261e", "FLAG HIGH"), "MEDIUM": ("#c25e00", "FLAG MEDIUM"), "LOW": ("#8a6d00", "FLAG LOW")}
def st(name, **kw): return ParagraphStyle(name, fontName=kw.pop("fontName", "LS"), **kw)
S = {"h": st("h", fontSize=9, leading=11, textColor=colors.HexColor("#555555")), "q": st("q", fontName="LS-B", fontSize=11.5, leading=14.5, spaceAfter=4),
     "o": st("o", fontSize=10.5, leading=13.2, leftIndent=14, firstLineIndent=-14, spaceAfter=1.5), "ok": st("ok", fontName="LS-B", fontSize=10.5, leading=13.2, leftIndent=14, firstLineIndent=-14, spaceAfter=1.5, textColor=colors.HexColor("#0b5d2a"), backColor=colors.HexColor("#e3f4e8")),
     "s": st("s", fontSize=9, leading=11.2, textColor=colors.HexColor("#444444"), spaceAfter=3), "lab": st("lab", fontName="LS-B", fontSize=8.2, leading=10, textColor=colors.HexColor("#666666"), spaceBefore=5, spaceAfter=2),
     "v": st("v", fontSize=9.6, leading=12.2, spaceAfter=2), "m": st("m", fontName="LS-I", fontSize=8.8, leading=11, textColor=colors.HexColor("#555555")),
     "t": st("t", fontName="LS-B", fontSize=17, leading=21, spaceAfter=6), "tl": st("tl", fontSize=9.5, leading=12, spaceAfter=2)}
def esc(s): return html.escape(str(s), quote=False)
class Mark(Flowable):
    """a zero-height flowable that puts an outline entry (the phone's bookmarks list) and a link target here"""
    def __init__(self, key, title): super().__init__(); self.key, self.title = key, title; self.width = self.height = 0
    def draw(self):
        c = self.canv; c.bookmarkPage(self.key); c.addOutlineEntry(self.title, self.key, level=0, closed=True)
class Doc(BaseDocTemplate):
    def __init__(self, fn, **kw):
        super().__init__(fn, pagesize=(W, H), leftMargin=M, rightMargin=M, topMargin=M, bottomMargin=22, **kw)
        self.addPageTemplates([PageTemplate("p", frames=[Frame(M, 22, CW, H - M - 22, 0, 0, 0, 0)], onPage=self.foot), PageTemplate("full", frames=[Frame(0, 22, W, H - 22 - 4, 0, 0, 0, 0)], onPage=self.foot)])
    def foot(self, canv, doc):
        canv.setFont("LS", 7.5); canv.setFillColor(colors.HexColor("#888888")); canv.drawString(M, 9, self.title_); canv.drawRightString(W - M, 9, "%d" % doc.page)
def fit(path, maxw, maxh):
    w, h = PI.open(path).size
    s = min(maxw / w, maxh / h); return Image(path, w * s, h * s)
def add_crop(fl, path, label):
    """a picture up to 330 points tall sits under the text (label and picture kept together); a taller one (a whole table) gets a page to itself, so it is not shrunk to a sliver"""
    w, h = PI.open(path).size
    if CW * h / w <= 330 or 330 * w / h >= 0.62 * CW: fl.append(KeepTogether([Paragraph(label, S["lab"]), fit(path, CW, 330)])); return
    fl.append(PageBreak()); fl.append(Paragraph(label + " (larger: it is taller than the other pictures)", S["lab"])); fl.append(fit(path, CW, 590))
def qpages(qid):
    out = []; k = 0
    while os.path.exists(os.path.join(RAW, "%s.p%d.jpg" % (qid, k))): out.append(os.path.join(RAW, "%s.p%d.jpg" % (qid, k))); k += 1
    return out
def qsize(qid):
    t = 0
    for p in [os.path.join(RAW, qid + ".crop.jpg")] + qpages(qid):
        if os.path.exists(p): t += os.path.getsize(p)
    return t
def chip(sev, text):
    col, label = SEV.get(sev, SEV["OK"])
    t = Table([[Paragraph('<font color="white"><b>%s</b></font>' % esc(label), st("c", fontSize=8.6, leading=10))]], colWidths=[None])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(col)), ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return t
def build_question(q, n, total, rec):
    v = verd.get(q["id"], {"verdict": "OK", "severity": "", "kinds": [], "reason": "", "basis": "mech"})
    sev = "OK" if v["verdict"] == "OK" else (v.get("severity") or "LOW")
    key = "q_" + q["id"]; fl = []
    fl.append(Mark(key, "%s %s" % (q["id"], "" if sev == "OK" else "[" + sev + "] ") + q["question"][:60]))
    left = Paragraph("<b>%s</b>  &middot;  Q %d of %d" % (esc(q["id"]), n, total), S["h"])
    ht = Table([[left, chip(sev, "")]], colWidths=[CW - 86, 86])
    ht.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("ALIGN", (1, 0), (1, 0), "RIGHT")]))
    fl += [ht, Spacer(1, 4), Paragraph(esc(q["question"]), S["q"])]
    for l in "ABCD":
        txt = "%s&nbsp;&nbsp;%s" % (l, esc(q["options"][l]))
        if l == q["answer"]: fl.append(Paragraph("<b>%s</b>&nbsp;&nbsp;&mdash; marked answer" % txt, S["ok"]))
        else: fl.append(Paragraph(txt, S["o"]))
    fl.append(Paragraph("<b>Study-guide explanation:</b> " + esc(q["explanation"]), S["s"]))
    c = q["citation"]
    ptr = rec.get("ptr") or c.get("label", ""); pl = rec.get("pageLine") or ""
    fl.append(Paragraph("What the app prints under the answer", S["lab"]))
    fl.append(Paragraph("%s<br/>%s" % (esc(ptr), esc(pl)), S["s"]))
    crop = os.path.join(RAW, q["id"] + ".crop.jpg")
    if os.path.exists(crop): add_crop(fl, crop, "The cropped picture the app shows (highlight = the cited words)")
    else:
        fl.append(Paragraph("The cropped picture the app shows", S["lab"]))
        note = (rec.get("card") or {}).get("note") or "No cropped picture: the app shows the whole page instead (see the next page)."
        fl.append(Paragraph("<i>%s</i>" % esc(note), S["s"]))
    if AFTER and os.path.exists(os.path.join(AFTER, q["id"] + ".crop.jpg")):
        add_crop(fl, os.path.join(AFTER, q["id"] + ".crop.jpg"), "The same picture with the unmerged build 384.56 fix (what it would show)")
    mk = (rec.get("marks") or [])
    mtxt = " / ".join(m["text"] for m in mk if m["kind"] != "heading")[:420] or " / ".join(m["text"] for m in mk)[:420]
    if mtxt: fl.append(Paragraph("<b>Marked words (read from the picture's highlight):</b> " + esc(mtxt), S["m"]))
    col = SEV.get(sev, SEV["OK"])[0]
    head = "OK" if sev == "OK" else "FLAG &middot; %s &middot; %s" % (sev, esc(" / ".join(v.get("kinds") or [])))
    fl.append(KeepTogether([Paragraph("Audit verdict", S["lab"]), Paragraph('<font color="%s"><b>%s</b></font>' % (col, head), S["v"])]))
    if v.get("reason"): fl.append(Paragraph(esc(v["reason"]), S["v"]))
    if v.get("recommendation"): fl.append(Paragraph("<b>Recommendation:</b> " + esc(v["recommendation"]), S["v"]))
    if v.get("evidence"): fl.append(Paragraph("<b>Evidence:</b> " + esc(v["evidence"]), S["s"]))
    fl.append(Paragraph("<i>Checked by: %s</i>" % ("read by the auditor against the cited text" if v.get("basis") == "read" else "text match only (the marked words hold the key); not read in full"), S["s"]))
    pgs = qpages(q["id"])
    for k, p in enumerate(pgs):
        pm = (rec.get("pages_meta") or [{}] * (k + 1))[k] if rec.get("pages_meta") else {}
        fl.append(PageBreak())
        fl.append(Paragraph("<b>%s</b> &middot; the whole cited page%s: %s. Highlight as in the picture above." % (esc(q["id"]), "" if len(pgs) == 1 else " (%d of %d)" % (k + 1, len(pgs)), esc(("book " if c["source"] == "ifc" else "HC amendments ") + "PDF page %s" % pm.get("page", c.get("pdfPage", "")))), st("pc", fontSize=8, leading=10, leftIndent=M, rightIndent=M, textColor=colors.HexColor("#555555"))))
        fl.append(fit(p, CW, H - 70))
    if not pgs:
        fl.append(PageBreak()); fl.append(Paragraph("No whole-page picture could be made for this question.", S["s"]))
    return fl, sev
def main():
    want = set(arg("--unit").split(",")) if arg("--unit") else None
    order = [u["id"] for u in sorted(bank["units"], key=lambda u: u.get("order", 0))]
    made = []
    for uid in order:
        if want and uid not in want: continue
        qs = [q for q in bank["questions"] if q["unit"] == uid]
        if not qs: continue
        u = units[uid]
        parts = []; cur = []; sz = 0
        for q in qs:
            s = qsize(q["id"])
            if cur and sz + s > MAXMB * 1e6: parts.append(cur); cur = []; sz = 0
            cur.append(q); sz += s
        if cur: parts.append(cur)
        counts = {"OK": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for q in qs:
            v = verd.get(q["id"]); counts["OK" if (not v or v["verdict"] == "OK") else (v.get("severity") or "LOW")] += 1
        done = 0
        for pi, part in enumerate(parts):
            slug = re.sub(r"[^a-z0-9]+", "-", u["title"].lower()).strip("-")[:38].strip("-")
            head = ("ch%02d" % int(uid)) if str(uid).isdigit() else ("appendix-" + uid[3:] if uid.startswith("App") else ("exhibit-" + uid[3:] if uid.startswith("Exh") else "chapter-finder"))
            fname = "%s-%s%s.pdf" % (head, slug, "" if len(parts) == 1 else "-part%d-of-%d" % (pi + 1, len(parts)))
            doc = Doc(os.path.join(OUT, fname), title="%s - question audit" % u["label"], author="Question audit")
            doc.title_ = "%s %s%s" % (u["label"], u["title"][:40], "" if len(parts) == 1 else " - part %d of %d" % (pi + 1, len(parts)))
            fl = [Mark("top", u["label"] + " overview"), Paragraph(esc(u["label"] + ": " + u["title"]), S["t"]),
                  Paragraph("%d questions%s. OK %d &middot; FLAG HIGH %d &middot; MEDIUM %d &middot; LOW %d" % (len(qs), "" if len(parts) == 1 else " (this file: %d to %d)" % (done + 1, done + len(part)), counts["OK"], counts["HIGH"], counts["MEDIUM"], counts["LOW"]), S["tl"]),
                  Paragraph("Each question has two pages: the question, the answer, the picture the app shows and the audit verdict; then the whole book page with the same highlight. Tap a flagged line to jump to it.", S["s"])]
            flagged = [(q, verd[q["id"]]) for q in part if q["id"] in verd and verd[q["id"]]["verdict"] != "OK"]
            if flagged:
                fl.append(Paragraph("Flagged in this file", S["lab"]))
                for q, v in flagged:
                    fl.append(Paragraph('<a href="#q_%s" color="#1a4fa0"><b>%s</b></a> <font color="%s"><b>%s</b></font> %s' % (q["id"], esc(q["id"]), SEV[v.get("severity") or "LOW"][0], esc(v.get("severity") or "LOW"), esc((" / ".join(v.get("kinds") or []) + ": " if v.get("kinds") else "") + (v.get("reason") or "")[:150])), S["s"]))
            fl.append(PageBreak())
            for k, q in enumerate(part):
                rp = os.path.join(RAW, q["id"] + ".json"); rec = json.load(open(rp)) if os.path.exists(rp) else {}
                items, sev = build_question(q, done + k + 1, len(qs), rec)
                fl += items
                if k < len(part) - 1: fl.append(PageBreak())
            # a page-break inside the question, before the full page, goes to the wide template so the book page runs edge to edge
            doc.build(fl)
            sz = os.path.getsize(os.path.join(OUT, fname)); made.append((fname, sz, len(part)))
            print("%s  %.1f MB  %d questions" % (fname, sz / 1e6, len(part)), flush=True)
            done += len(part)
    json.dump(made, open(os.path.join(OUT, "_made.json"), "w"))
main()
