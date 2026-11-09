"""Build 384 r9: the Friends screen's "Enter a friend's code" field is centred.
Madison, the field circled: "This isn't centered". Measured from the pixels (dpr 2), on an iPhone 17 Pro Max, an iPhone SE and an
iPad Pro 11":
 (1) empty: the hint and the blinking cursor in front of it, as one group, are centred in the field (left and right space within 4px),
     and the cursor stands just before the hint (4-14px of gap);
 (2) a typed code ("ABC-123") is centred in the field (within 4px);
 (3) nothing scrolls sideways, and no page errors.
Run:  python3 tools/check-b384-friendfield.py   (--against OLD/index.html must FAIL)"""
import io, os, sys, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
if "--against" in sys.argv:
    body = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
    cb.BODY = cb.INSET_RE.sub("0px", body).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
from playwright.sync_api import sync_playwright
from PIL import Image
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
DPR = 2
def ink_cols(pg, box):
    # the middle band only, 4px in from the sides: the pill's rounded focus ring curves into the corners of anything taller
    png = pg.screenshot(clip={"x": box["x"] + 8, "y": box["y"] + box["h"] * .36, "width": box["w"] - 16, "height": box["h"] * .28})
    im = Image.open(io.BytesIO(png)).convert("L"); w, h = im.size; px = im.load()
    bg = sorted(px[x, h // 2] for x in range(w))[w // 4]
    cols = [x for x in range(w) if any(px[x, y] > bg + 45 for y in range(h))]
    if not cols: return None
    return ((cols[0] / DPR) + 8, (w - 1 - cols[-1]) / DPR + 8, cols)
with sync_playwright() as pw:
    br = pw.chromium.launch()
    for lab, W, H in (("iPhone 17 Pro Max", 440, 956), ("iPhone SE", 375, 667), ("iPad Pro 11in", 834, 1194)):
        ctx, pg = cb.booted(br, W, H, seed=cb.USED_ACCOUNT, dpr=DPR)
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        pg.evaluate("()=>showFriends()"); pg.wait_for_timeout(900)
        # the blinking cursor held lit, so it is in the picture
        pg.add_style_tag(content=".friend-add-field:has(> .friend-add-input:placeholder-shown:not(:focus))::before{ animation:none !important; opacity:.95 !important; }")
        pg.wait_for_timeout(150)
        box = pg.evaluate("()=>{ const b=document.querySelector('.friend-add-input').getBoundingClientRect(); return {x:b.left,y:b.top,w:b.width,h:b.height}; }")
        r = ink_cols(pg, box)
        if not r: chk("%s: the empty field shows a hint" % lab, False); ctx.close(); continue
        L, R, cols = r
        gaps = [cols[k + 1] - cols[k] for k in range(len(cols) - 1)]
        first_gap = next((g for g in gaps if g > 1), 0) / DPR
        chk("(1) %s: the hint and its cursor centred in the field (%.1f left / %.1f right)" % (lab, L, R), abs(L - R) <= 4, (L, R))
        chk("(1) %s: the cursor just before the hint (%.1fpx)" % (lab, first_gap), 4 <= first_gap <= 14, first_gap)
        pg.click(".friend-add-input"); pg.keyboard.type("ABC123"); pg.wait_for_timeout(200)
        pg.evaluate("()=>{ const i=document.querySelector('.friend-add-input'); i.style.caretColor='transparent'; }")
        pg.wait_for_timeout(100)
        r2 = ink_cols(pg, box)
        chk("(2) %s: a typed code centred in the field (%s)" % (lab, r2 and "%.1f / %.1f" % (r2[0], r2[1])), r2 and abs(r2[0] - r2[1]) <= 4, r2 and r2[:2])
        sw = pg.evaluate("()=>document.documentElement.scrollWidth - innerWidth")
        chk("(3) %s: nothing scrolls sideways (%d) and no page errors" % (lab, sw), sw <= 0 and not errs, [sw, errs[:2]])
        ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
