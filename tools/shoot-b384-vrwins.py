"""The comparison sheet for the Virtual Room's top-tier banner (384.120 follow-up, banner id vrtop10): each of the four options in
tools/b384-vrwins-options.js drawn in the real app, in the three places a banner is seen - its tile on Customize's Banner page
(with the row it sits in), the person card (a classmate wearing it, opened from the Leaderboard) and the Leaderboard row's edge
(the still picture, 384.120) - on iPhone 17 Pro Max 440x956 and iPad Pro 11" 834x1194, labelled, one sheet per device.
The option is swapped into the page at run time (BANNER_ART.vrtop10, its name and its tint), so the shipped file carries one.
The harness is check-b384-unlocks.py's (an in-memory Firestore; made-up classmates; Rosa wears the banner).

  python3 tools/shoot-b384-vrwins.py OUTDIR [--src index.html] [--cls academy|ifc] [--dev pm|ipad] [--opts abcd]"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
G = os.path.join(HERE, "check-b384-unlocks.py")
sys_argv = sys.argv[:]
sys.argv = [G]
h = {"__file__": G, "__name__": "shoot"}
exec(open(G).read().split("\n# ---- the gate ----")[0], h)
sys.argv = sys_argv
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1]
def arg(n): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else None
SRC = arg("--src") or os.path.join(h["ROOT"], "index.html")
CLS = arg("--cls") or "academy"; DEV = arg("--dev"); OPTS = arg("--opts") or "abcd"
os.makedirs(OUT, exist_ok=True)
text = open(SRC, encoding="utf-8").read()
OPTJS = open(os.path.join(HERE, "b384-vrwins-options.js"), encoding="utf-8").read()
fx = h["fixtures"]()

SWAP = """(k)=>{ const o = VRW_OPTIONS[k]; BANNER_ART.vrtop10 = o.art; delete BANNER_TPL.vrtop10; delete bannerRowStillCache.vrtop10;
  try{ delete bannerVeilCache.vrtop10; }catch(e){} try{ delete bannerTintCache.vrtop10; }catch(e){}
  bannerDef('vrtop10').name = o.name; BANNER_TINT.vrtop10 = o.tint; store.vrWins = Math.max(10, Number(store.vrWins) || 0); return o.name; }"""
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT2 = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def shot_el(pg, sel_js, path, pad=0):
    r = pg.evaluate(sel_js)
    if not r: return None
    x, y, w, hh = r
    pg.screenshot(path=path, clip={"x": max(0, x - pad), "y": max(0, y - pad), "width": w + 2 * pad, "height": hh + 2 * pad})
    return path

TILE = """async ()=>{ const W = ms => new Promise(r => setTimeout(r, ms));
  const b = document.querySelector('.banner-opt .bnr-vrtop10'); if(!b) return null; const t = b.closest('.banner-opt');
  t.scrollIntoView({ block: 'center' }); await W(1400);
  const r = t.getBoundingClientRect(), g = t.parentElement.getBoundingClientRect();
  return [g.left, r.top - 6, g.width, r.height + 12]; }"""
CARD = """async ()=>{ const W = ms => new Promise(r => setTimeout(r, ms));
  document.querySelectorAll('.invite-overlay').forEach(o => o.remove());
  const e = ((window.NOVA_CLASS === "ifc" ? classBoardRows : leaderboardRows) || []).find(x => x.firstName === 'Rosa'); if(!e) return null;
  openPersonSheet(e); await W(1600);
  const s = document.querySelector('.person-card'); if(!s) return null; const r = s.getBoundingClientRect();
  return [r.left, r.top, r.width, Math.min(r.height, 520)]; }"""
ROW = """async ()=>{ const W = ms => new Promise(r => setTimeout(r, ms));
  document.querySelectorAll('.invite-overlay').forEach(o => o.remove());
  showRankings(); await W(2600);
  const row = [...document.querySelectorAll('.screen-rankings .rank-row')].find(r => (r.querySelector('.rank-name') || {}).textContent === 'Rosa');
  if(!row) return null; row.scrollIntoView({ block: 'center' }); await W(900);
  const r = row.getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; }"""

with sync_playwright() as p:
    br = p.chromium.launch(executable_path=h["g"]["CHROME"], args=["--no-sandbox"])
    for dev, w, hh in (("pm", 440, 956), ("ipad", 834, 1194)):
        if DEV and DEV != dev: continue
        seed, init = fx["rich_" + CLS]
        ctx, pg, errs = h["page"](br, text, seed, init, w=w, h=hh, scale=2)
        pg.wait_for_timeout(1500)
        h["quiet"](pg); h["load_board"](pg); h["quiet"](pg)
        pg.add_script_tag(content=OPTJS)
        cells = []
        for k in OPTS:
            name = pg.evaluate(SWAP, k)
            pg.evaluate("()=>{ document.querySelectorAll('.invite-overlay').forEach(o => o.remove()); showCustomize('banner'); }"); pg.wait_for_timeout(1500)
            pre = os.path.join(OUT, "%s-%s-%s-" % (CLS, dev, k))
            a = shot_el(pg, TILE, pre + "tile.png")
            b = shot_el(pg, CARD, pre + "card.png")
            c = shot_el(pg, ROW, pre + "row.png", pad=4)
            cells.append((k, name, a, c, b))   # tile, row, card
            print(dev, k, name, "tile" if a else "-", "card" if b else "-", "row" if c else "-", flush=True)
        print(dev, "errors:", errs[:3], flush=True)
        ctx.close()
        # the sheet: a row per option - label, the Customize tile row, the Leaderboard row, the person card
        ims = [[Image.open(x) if x else None for x in cell[2:]] for cell in cells]
        S = 1.0 if dev == "pm" else .62
        def sc(im): return im.resize((int(im.width * S), int(im.height * S))) if im and S != 1 else im
        ims = [[sc(x) for x in row] for row in ims]
        colw = [max((r[i].width for r in ims if r[i]), default=10) for i in range(3)]
        rowh = [max([x.height for x in r if x] + [10]) for r in ims]
        gap, lab, top = 36, 150, 118
        W = lab + colw[0] + colw[2] + gap * 3 + max(colw[1], 10)
        # tile and row stacked in the first column, the card in the second
        rowh = [max((r[0].height if r[0] else 0) + gap + (r[1].height if r[1] else 0), r[2].height if r[2] else 0) for r in ims]
        W = lab + max(colw[0], colw[1]) + gap * 3 + colw[2]
        H = top + sum(rowh) + gap * (len(ims) + 1)
        sheet = Image.new("RGB", (W, H), (18, 20, 26))
        d = ImageDraw.Draw(sheet)
        f1, f2, f3 = ImageFont.truetype(FONT, 34), ImageFont.truetype(FONT, 26), ImageFont.truetype(FONT2, 20)
        d.text((gap, 24), "Win 10 rooms - banner options (%s, %s)" % ("iPhone 17 Pro Max 440x956" if dev == "pm" else "iPad Pro 11\" 834x1194", "Fire Code" if CLS == "ifc" else "academy"), font=f1, fill=(240, 240, 245))
        y = top
        for (k, name, *_), row, rh in zip(cells, ims, rowh):
            d.text((gap, y + 4), k.upper(), font=ImageFont.truetype(FONT, 64), fill=(255, 211, 77))
            d.text((gap, y + 84), name, font=f3, fill=(220, 220, 230))
            x0 = lab + gap
            if row[0]:
                d.text((x0, y - 26), "Customize > Banner (tile row)", font=f3, fill=(150, 160, 175)); sheet.paste(row[0], (x0, y))
            if row[1]:
                yy = y + (row[0].height if row[0] else 0) + gap
                d.text((x0, yy - 26), "Leaderboard row (edge)", font=f3, fill=(150, 160, 175)); sheet.paste(row[1], (x0, yy))
            if row[2]:
                xc = x0 + max(colw[0], colw[1]) + gap
                d.text((xc, y - 26), "Person card", font=f3, fill=(150, 160, 175)); sheet.paste(row[2], (xc, y))
            y += rh + gap
        out = os.path.join(OUT, "SHEET-%s-%s.png" % (CLS, dev))
        sheet.save(out); print("sheet", out, sheet.size, flush=True)
    br.close()
