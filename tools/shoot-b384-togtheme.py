"""Build 384.107: the toggles' ON colour in every theme, as one sheet for Madison.
One Settings toggle group (Settings > Study: three switches, set ON / OFF / ON) for the default theme and each rank colour,
on an iPhone 17 Pro Max (440x956, installed, 3x), cut to the card and laid out in a grid with each theme's name.
Also prints, per theme, the luminance of the ON track, the OFF track and the card behind them, read off the pixels.
Run:  python3 tools/shoot-b384-togtheme.py OUT.png [--against REV|DIR]"""
import importlib.util, io, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = next((a for a in sys.argv[1:] if a.endswith(".png")), None)
if OUT: sys.argv.remove(OUT)
spec = importlib.util.spec_from_file_location("glitches", os.path.join(HERE, "check-b384-glitches.py"))
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw, ImageFont

THEMES = ["ink", "rookie", "ranger", "veteran", "vanguard", "adept", "elite", "titan"]
SET = """async(k)=>{ const wait = ms => new Promise(r => setTimeout(r, ms));
  theme.accent = k; applyTheme(); showAppearance({ page: 'study' }); await wait(900);
  const rows = [...document.querySelectorAll('#stage .opt')].filter(r => r.querySelector(':scope > input[type=checkbox]') && r.querySelector(':scope > .box'));
  rows.forEach((r, i) => { const c = r.querySelector(':scope > input'); c.checked = i % 2 === 0; });
  await wait(700);
  const card = rows[0].closest('.settings-card') || rows[0].parentElement;
  card.scrollIntoView({ block: 'center', behavior: 'instant' }); await wait(300);
  const R = e => { const q = e.getBoundingClientRect(); return [q.left, q.top, q.width, q.height]; };
  const name = k === 'ink' ? 'Default' : (typeof RANK_DISPLAY_NAME !== 'undefined' && RANK_DISPLAY_NAME[k]) || k;
  return { name, card: R(card), boxes: rows.map(r => ({ on: r.querySelector(':scope > input').checked, r: R(r.querySelector(':scope > .box')) })) }; }"""

def lum(rgb):
    def ch(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb[:3]
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)

def mean(img, box):
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    px = list(img.crop((x0, y0, x1, y1)).getdata())
    return tuple(sum(p[i] for p in px) / len(px) for i in range(3))

def read_tracks(img, info, dpr):
    """the bare track beside the knob: an ON track's left part, an OFF track's right part; the card a little left of the track"""
    out = {"on": [], "off": [], "card": []}
    for b in info["boxes"]:
        x, y, w, h = [v * dpr for v in b["r"]]
        if b["on"]: seg = (x + 0.12 * w, y + 0.32 * h, x + 0.26 * w, y + 0.68 * h)
        else:       seg = (x + 0.74 * w, y + 0.32 * h, x + 0.88 * w, y + 0.68 * h)
        out["on" if b["on"] else "off"].append(mean(img, seg))
        out["card"].append(mean(img, (x - 14 * dpr, y + 0.3 * h, x - 6 * dpr, y + 0.7 * h)))
    avg = lambda L: tuple(sum(c[i] for c in L) / len(L) for i in range(3)) if L else None
    return {k: avg(v) for k, v in out.items()}

def cr(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)

def measure(pg, dpr):
    rows = []
    for k in THEMES:
        info = pg.evaluate(SET, k)
        img = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
        t = read_tracks(img, info, dpr)
        rows.append({"key": k, "name": info["name"], "img": img, "info": info, "on": t["on"], "off": t["off"], "card": t["card"],
                     "cr_on_off": round(cr(t["on"], t["off"]), 2), "cr_on_card": round(cr(t["on"], t["card"]), 2), "cr_off_card": round(cr(t["off"], t["card"]), 2)})
    return rows

if __name__ == "__main__":
    DPR = 3
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=G.CHROME)
        _nc = br.new_context      # a busy machine: three minutes for the page to load
        def _new_context(**kw):
            c = _nc(**kw); c.set_default_navigation_timeout(180000); return c
        br.new_context = _new_context
        pg = G.open_dev(br, "promax", inits=[G.seed_init("academy")], dsf=DPR)
        pg.evaluate("()=>{ theme.reduceMotion = false; try{ applyTheme(); }catch(e){} }")
        rows = measure(pg, DPR)
        for r in rows:
            print("%-10s on %s off %s card %s | on:off %.2f  on:card %.2f  off:card %.2f" % (r["name"], tuple(round(c) for c in r["on"]), tuple(round(c) for c in r["off"]),
                  tuple(round(c) for c in r["card"]), r["cr_on_off"], r["cr_on_card"], r["cr_off_card"]))
        if OUT:
            crops = []
            for r in rows:
                x, y, w, h = r["info"]["card"]
                pad = 10
                crops.append((r, r["img"].crop((int((x - pad) * DPR), int((y - pad) * DPR), int((x + w + pad) * DPR), int((y + h + pad) * DPR)))))
            cw = max(c.width for _, c in crops); ch = max(c.height for _, c in crops)
            label_h = 70; cols = 2; gap = 24
            rows_n = (len(crops) + cols - 1) // cols
            sheet = Image.new("RGB", (cols * cw + (cols + 1) * gap, rows_n * (ch + label_h) + (rows_n + 1) * gap + 90), (10, 12, 16))
            d = ImageDraw.Draw(sheet)
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
                small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
            except Exception:
                font = small = ImageFont.load_default()
            d.text((gap, 24), "Toggles in every theme: ON / OFF / ON (Settings > Study, iPhone 17 Pro Max)", fill=(235, 238, 242), font=small)
            for n, (r, c) in enumerate(crops):
                cx = gap + (n % cols) * (cw + gap); cy = 90 + gap + (n // cols) * (ch + label_h + gap)
                d.text((cx, cy + 8), r["name"], fill=(255, 255, 255), font=font)
                d.text((cx + 330, cy + 16), "on:off %.1f   on:card %.1f" % (r["cr_on_off"], r["cr_on_card"]), fill=(160, 170, 182), font=small)
                sheet.paste(c, (cx, cy + label_h))
            os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
            sheet.save(OUT)
            print("sheet:", OUT, sheet.size)
        print("errors:", pg.errs[:3])
        pg.ctx.close(); br.close()
