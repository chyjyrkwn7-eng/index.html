#!/usr/bin/env python3
"""384 ui3 (profile rows, round three): the comparison sheet from shoot-b384-profilerows2.py's pictures.

  python3 tools/shoot-b384-profilerows2.py RAW --devs phone-installed --opts b,c,d,e --badge row
  python3 tools/sheet-b384-profilerows3.py RAW OUT.png

One sheet, iPhone 17 Pro Max 440x956 at 2x: a row per class, a column per Customize option (B, C, D, E), each cell the three rows
cut from Profile (Customize in the person card, the Badge case - the new row, the same in every column - and the Rank ladder at the
foot of the Next rank card), stacked."""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont
RAW, OUT = sys.argv[1], sys.argv[2]
res = json.load(open(os.path.join(RAW, "shots.json")))
def font(sz, bold=True):
    p = "/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if bold else "")
    return ImageFont.truetype(p, sz) if os.path.exists(p) else ImageFont.load_default()
K = 2.0
NAMES = {"b": "B: the next unlock, its name, its bar", "c": "C: a ring of the theme, the count",
         "d": "D (default): C's ring, the count, Next + a slim bar", "e": "E: B's unlock in a small frame, the count, the bar"}
CLS = {"academy": "Police Academy", "ifc": "Fire Code"}
def piece(r):
    im = Image.open(r["full"]); k = r["dpr"]; i = r["info"]; e = i["entries"]
    def cut(top, bot):
        c = im.crop((0, int(top * k), im.width, int(bot * k)))
        return c.resize((int(c.width / k * K), int(c.height / k * K)), Image.LANCZOS)
    a = cut(e["customize"][1] - 14, e["case"][1] + e["case"][3] + 10)
    b = cut(e["ladder"][1] - 30, i["goal"][1] + i["goal"][3] + 6)
    out = Image.new("RGB", (a.width, a.height + b.height + 16), (18, 18, 20)); out.paste(a, (0, 0)); out.paste(b, (0, a.height + 16))
    return out
cols = [o for o in "bcde"]; rows = ["academy", "ifc"]
cells = {(c, o): piece(res["phone-installed-%s-%s-mid" % (c, o)]) for c in rows for o in cols if "phone-installed-%s-%s-mid" % (c, o) in res}
cw = max(x.width for x in cells.values()); chs = {c: max(cells[(c, o)].height for o in cols if (c, o) in cells) for c in rows}
W = 60 + len(cols) * (cw + 40); H = 130 + sum(h + 170 for h in chs.values())
sh = Image.new("RGB", (W, H), (12, 12, 14)); d = ImageDraw.Draw(sh)
d.text((40, 30), "Profile rows, round three - iPhone 17 Pro Max 440x956 (2x). Badge case: B's words, the plain row icon. Customize: B, C, D, E.", fill=(240, 240, 245), font=font(40))
y = 120
for c in rows:
    d.text((40, y), CLS[c], fill=(235, 235, 245), font=font(36)); y += 56
    for j, o in enumerate(cols):
        x = 40 + j * (cw + 40)
        d.text((x, y), NAMES[o], fill=(255, 212, 59), font=font(26))
        if (c, o) in cells: sh.paste(cells[(c, o)], (x, y + 46))
    y += chs[c] + 110
sh.save(OUT); print("sheet", OUT, sh.size)
