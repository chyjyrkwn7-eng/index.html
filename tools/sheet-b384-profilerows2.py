#!/usr/bin/env python3
"""384 profilerows2: the comparison sheet from shoot-b384-profilerows2.py's pictures.

  python3 tools/sheet-b384-profilerows2.py RAW_DIR OUT_DIR

Writes, per device: sheet-<dev>.png - a row per class, a column per option (a, b, c), each the three entry rows cut from Profile
(Customize in the person card, the Badge case, the Rank ladder at the foot of the Next rank card), at 1.2x CSS pixels; and
ladder-<dev>.png - the Rank ladder for every rank position shot (none, first, mid, last, prestige), both classes."""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont
RAW, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
res = json.load(open(os.path.join(RAW, "shots.json")))
def font(sz, bold=True):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if bold else ""),):
        if os.path.exists(p): return ImageFont.truetype(p, sz)
    return ImageFont.load_default()
K = 1.2
NAMES = {"a": ("Badge case: a shut case, its front fills", "Customize: palette tile, count + next"),
         "b": ("Badge case: a tick per badge round a ring", "Customize: the next unlock + its bar"),
         "c": ("Badge case: newest coin + a segment per badge", "Customize: a ring of the theme + count")}
CLS = {"academy": "Class 26E (academy)", "ifc": "Fire Code"}
DEVN = {"phone-installed": "iPhone 17 Pro Max 440x956", "ipad-pro-11": "iPad Pro 11\" 834x1194"}

def piece(r, which):
    im = Image.open(r["full"]); k = r["dpr"]; i = r["info"]; e = i["entries"]
    def cut(top, bot):
        c = im.crop((0, int(top * k), im.width, int(bot * k)))
        return c.resize((int(c.width / k * K), int(c.height / k * K)), Image.LANCZOS)
    if which == "rows":
        # Customize's row, the case card, and the ladder (the foot of the goal card), stacked with a small gap
        hero, goal = i["hero"], i["goal"]
        a = cut(e["customize"][1] - 14, e["case"][1] + e["case"][3] + 10)
        b = cut(e["ladder"][1] - 14, goal[1] + goal[3] + 6)
        out = Image.new("RGB", (a.width, a.height + b.height + 10), (18, 18, 20)); out.paste(a, (0, 0)); out.paste(b, (0, a.height + 10))
        return out
    return cut(e["ladder"][1] - 14, i["goal"][1] + i["goal"][3] + 6)

for dev in ("phone-installed", "ipad-pro-11"):
    tags = [t for t in res if t.startswith(dev + "-")]
    if not tags: continue
    # options sheet (rank = mid)
    cols = ["a", "b", "c"]; rows = ["academy", "ifc"]
    cells = {(c, o): piece(res["%s-%s-%s-mid" % (dev, c, o)], "rows") for c in rows for o in cols if "%s-%s-%s-mid" % (dev, c, o) in res}
    if cells:
        cw = max(x.width for x in cells.values()); chs = {c: max(cells[(c, o)].height for o in cols if (c, o) in cells) for c in rows if any((c, o) in cells for o in cols)}
        W = 40 + len(cols) * (cw + 30); H = 70 + sum(h + 130 for h in chs.values())
        sh = Image.new("RGB", (W, H), (12, 12, 14)); d = ImageDraw.Draw(sh)
        d.text((24, 18), "Profile entry rows, round two - " + DEVN[dev], fill=(240, 240, 245), font=font(30))
        y = 70
        for c, h in chs.items():
            d.text((24, y), CLS[c], fill=(235, 235, 245), font=font(26)); y += 40
            for j, o in enumerate(cols):
                x = 30 + j * (cw + 30)
                d.text((x, y), "Option " + o.upper(), fill=(255, 212, 59), font=font(22))
                d.text((x, y + 30), NAMES[o][0], fill=(180, 180, 190), font=font(15, False))
                d.text((x, y + 50), NAMES[o][1], fill=(180, 180, 190), font=font(15, False))
                if (c, o) in cells: sh.paste(cells[(c, o)], (x, y + 80))
            y += h + 90
        sh.save(os.path.join(OUT, "sheet-%s.png" % dev)); print("sheet", dev, sh.size)
    # ladder positions
    lad = [(t, piece(res[t], "ladder")) for t in sorted(tags) if not t.endswith("-mid") or True]
    lad = [(t, p) for t, p in lad if t.split("-")[-2] == "a" or t.endswith("-mid")]
    if lad:
        order = ["none", "first", "mid", "last", "prestige"]
        lad.sort(key=lambda tp: (tp[0].split("-")[-3], order.index(tp[0].split("-")[-1])))
        seen = set(); lad = [tp for tp in lad if (tp[0].split("-")[-3], tp[0].split("-")[-1]) not in seen and not seen.add((tp[0].split("-")[-3], tp[0].split("-")[-1]))]
        cw = max(p.width for _, p in lad); ch = max(p.height for _, p in lad)
        W = 40 + 2 * (cw + 30); per = {"academy": [p for t, p in lad if "-academy-" in t], "ifc": [p for t, p in lad if "-ifc-" in t]}
        labs = {"academy": [t.split("-")[-1] for t, p in lad if "-academy-" in t], "ifc": [t.split("-")[-1] for t, p in lad if "-ifc-" in t]}
        H = 80 + max(len(v) for v in per.values()) * (ch + 40)
        sh = Image.new("RGB", (W, H), (12, 12, 14)); d = ImageDraw.Draw(sh)
        d.text((24, 18), "Rank ladder, every position - " + DEVN[dev], fill=(240, 240, 245), font=font(30))
        for j, c in enumerate(("academy", "ifc")):
            x = 30 + j * (cw + 30); y = 70
            d.text((x, y), CLS[c], fill=(235, 235, 245), font=font(22)); y += 34
            for lb, p in zip(labs[c], per[c]):
                d.text((x, y), lb, fill=(255, 212, 59), font=font(16)); sh.paste(p, (x, y + 22)); y += ch + 40
        sh.save(os.path.join(OUT, "ladder-%s.png" % dev)); print("ladder", dev, sh.size)
