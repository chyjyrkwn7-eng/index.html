#!/usr/bin/env python3
"""384 (profilerows, TEMPORARY): the comparison sheets from shoot-b384-profilerows.py's output.

  python3 tools/sheet-b384-profilerows.py RAW_DIR OUT_DIR

RAW_DIR holds shots.json and the full-page pictures. For each device and class it writes
  profile-<dev>-<class>.png   the person card to the end of the Next rank card, as it is (none) and options a, b, c side by side
  entries-<dev>-<class>.png   Customize / Badge case / Rank ladder, one row each, as it is and in a, b, c (c's tiles are one row, drawn once)
and then profilerows-sheet.png, the one sheet: the entry points, phone, both classes, then the iPad, both classes."""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont
RAW, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
shots = json.load(open(os.path.join(RAW, "shots.json")))
OPTS = ["none", "a", "b", "c"]
NAMES = {"none": "As it is", "a": "A  Preview strips", "b": "B  Compact rows", "c": "C  Three tiles"}
def font(sz, bold=False):
    for f in (["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"] if bold else ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]):
        if os.path.exists(f): return ImageFont.truetype(f, sz)
    return ImageFont.load_default()
BG = (18, 19, 24)

def crop(tag, box, pad=10):
    s = shots[tag]; d = s["dpr"]; im = Image.open(s["full"]).convert("RGB")
    x, y, w, h = box
    x0, y0 = max(0, int((x - pad) * d)), max(0, int((y - pad) * d))
    x1, y1 = min(im.width, int((x + w + pad) * d)), min(im.height, int((y + h + pad) * d))
    return im.crop((x0, y0, x1, y1))

def fit_w(im, w):
    return im.resize((w, max(1, round(im.height * w / im.width))), Image.LANCZOS)

def label(dr, xy, text, sz=26, bold=True, fill=(235, 238, 245)):
    dr.text(xy, text, font=font(sz, bold), fill=fill)

devs = sorted({t.rsplit("-", 2)[0] for t in shots}); out_entries = []
for dev in devs:
    for cls in ("academy", "ifc"):
        tags = {o: "%s-%s-%s" % (dev, cls, o) for o in OPTS if "%s-%s-%s" % (dev, cls, o) in shots}
        if not tags: continue
        # the whole of the card stack
        cols = []
        for o, t in tags.items():
            i = shots[t]["info"]; top = i["hero"][1]; bot = i["goal"][1] + i["goal"][3]
            cols.append((o, crop(t, [0, top, i["vw"], bot - top], pad=0)))
        cw = 560 if dev.startswith("phone") else 640
        cols = [(o, fit_w(c, cw)) for o, c in cols]
        H = max(c.height for _, c in cols) + 70
        sheet = Image.new("RGB", (len(cols) * (cw + 20) + 20, H), BG); dr = ImageDraw.Draw(sheet)
        for k, (o, c) in enumerate(cols):
            sheet.paste(c, (20 + k * (cw + 20), 60)); label(dr, (24 + k * (cw + 20), 14), NAMES[o], 28)
        sheet.save(os.path.join(OUT, "profile-%s-%s.png" % (dev, cls)))
        # the three entry points
        rows = ["customize", "case", "ladder"]; RN = {"customize": "Customize", "case": "Badge case", "ladder": "Rank ladder"}
        cw = 560 if dev.startswith("phone") else 640
        cell = {}
        for o, t in tags.items():
            i = shots[t]["info"]
            if o == "c":
                if i.get("trio"): cell[(o, "trio")] = fit_w(crop(t, i["trio"], 10), cw)
                continue
            for r in rows:
                b = i["entries"][r]
                if b: cell[(o, r)] = fit_w(crop(t, b, 10), cw)
        rh = {r: max([cell[k].height for k in cell if k[1] == r] + [60]) + 14 for r in rows}
        trio_h = cell[("c", "trio")].height if ("c", "trio") in cell else 0
        # c's tiles stand in one row: it gets the tallest of the three rows' height or its own
        total = sum(rh.values())
        if trio_h + 14 > total:
            rh[rows[-1]] += trio_h + 14 - total
        LM = 130
        W = len(tags) * (cw + 20) + 20 + LM
        sheet = Image.new("RGB", (W, 60 + sum(rh.values()) + 10), BG); dr = ImageDraw.Draw(sheet)
        y = 60; ys = {}
        for r in rows: ys[r] = y; y += rh[r]
        for k, o in enumerate(tags):
            x = 20 + LM + k * (cw + 20); label(dr, (x + 4, 14), NAMES[o], 28)
            if o == "c":
                if ("c", "trio") in cell:
                    ty = 60 + (sum(rh.values()) - trio_h) // 2 - 40
                    sheet.paste(cell[("c", "trio")], (x, max(60, ty)))
                    label(dr, (x + 4, max(60, ty) + trio_h + 6), "Customize, Badge case and Rank ladder, in one row", 20, False, (170, 176, 190))
                continue
            for r in rows:
                if (o, r) in cell:
                    sheet.paste(cell[(o, r)], (x, ys[r]))
                    if k == 0: label(dr, (14, ys[r] + rh[r] // 2 - 14), RN[r].replace(" ", "\n"), 22, True, (170, 176, 190))
        sheet.save(os.path.join(OUT, "entries-%s-%s.png" % (dev, cls)))
        out_entries.append((dev, cls, sheet))
# the one sheet
if out_entries:
    W = max(s.width for _, _, s in out_entries)
    Hs = [s.height + 70 for _, _, s in out_entries]
    # two per row would be too wide: stack them
    sheet = Image.new("RGB", (W, sum(Hs) + 20), BG); dr = ImageDraw.Draw(sheet); y = 10
    for dev, cls, s in out_entries:
        title = ("iPhone 17 Pro Max 440x956" if dev.startswith("phone") else "iPad Pro 11\" 834x1194") + "  -  " + ("Class 26E (academy)" if cls == "academy" else "Fire Code")
        label(dr, (24, y + 10), title, 32); sheet.paste(s, (0, y + 56)); y += s.height + 70
    sheet.save(os.path.join(OUT, "profilerows-sheet.png"))
print("done")
