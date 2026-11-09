"""Build 384 r9: Settings is Delta's size ON THE GLASS at the owner's page zoom (and untouched at 100%).
Madison, Delta's Settings beside ours: "Why are our icons and sections not the same size, ours are much smaller and it looks bad."
His phone runs Safari's page zoom at ~85%: the page lays out 518 CSS px wide on a 440pt screen, so every CSS px is 0.85pt. Ours drew
23.4pt tiles / 43.5pt rows against Delta's 27pt / 51pt. Here the page is served at 518 CSS px with a 440pt screen (as his is) and the
glass size is read as CSS px x (screen / layout width):
 (1) the Settings menu: tiles 26.5-29pt, row pitch 49-53pt, the card as wide as the screen's grouped list (edge inset 15-19pt);
 (2) a word's line box 18-21pt (15.5pt type) and a section heading's 17-22pt line (15pt type);
 (3) on a page Settings opens (Sound & Haptics, Study): every row is the height on the glass it has at 100% (within 1.5pt);
 (4) at 100% (440 CSS px on a 440pt screen) nothing is scaled: tile 28px, pitch 51px, and page-zoomed is not set;
 (5) nothing scrolls sideways at either, and no page errors.
Run:  python3 tools/check-b384-settingszoom.py   (--against OLD/index.html must FAIL)"""
import os, sys, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
if "--against" in sys.argv:
    body = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
    cb.BODY = cb.INSET_RE.sub("0px", body).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
def boot(br, W, H, SW, SH):
    ctx = br.new_context(viewport={"width": W, "height": H}, screen={"width": SW, "height": SH}, device_scale_factor=2, has_touch=True, is_mobile=False)
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
                        "localStorage.setItem('class26e.weekrecap.v1','9999-12-31');localStorage.setItem('class26e.savecode.card','1');localStorage.setItem('class26e.drill.v1','%s');}catch(e){}" % cb.USED_ACCOUNT)
    pg = cb.open_page(ctx); pg.goto(cb.URL); pg.wait_for_timeout(2800)
    return ctx, pg
READ = """(k)=>{ const R=e=>e.getBoundingClientRect(); const rows=[...document.querySelectorAll('.screen-settings .settings-row')];
  const t=R(document.querySelector('.screen-settings .settings-row-icon')), c=R(document.querySelector('.screen-settings .settings-card'));
  const lab=document.querySelector('.screen-settings .settings-row-label'), rg=document.createRange(); rg.selectNodeContents(lab);
  const hd=document.querySelector('.screen-settings .slab.motion-summary'), hg=document.createRange(); hg.selectNodeContents(hd);
  return { zoomed: document.documentElement.classList.contains('page-zoomed'), tile:t.width*k, pitch:(R(rows[1]).top-R(rows[0]).top)*k, inset:c.left*k,
           word:rg.getBoundingClientRect().height*k, head:hg.getBoundingClientRect().height*k, sw:document.documentElement.scrollWidth-innerWidth }; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch()
    ctx, pg = boot(br, 518, 1126, 440, 956)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    k = 440 / 518
    pg.evaluate("()=>showAppearance()"); pg.wait_for_timeout(1300)
    r = pg.evaluate(READ, k)
    chk("(1) at his zoom the tile is 26.5-29pt on the glass (%.1f) and the row pitch 49-53pt (%.1f)" % (r["tile"], r["pitch"]), 26.5 <= r["tile"] <= 29 and 49 <= r["pitch"] <= 53, r)
    chk("(1) the grouped list is inset 15-19pt from the screen's edge (%.1f)" % r["inset"], 15 <= r["inset"] <= 19, r)
    chk("(2) a word's line box is 18-21pt (%.1f) and a section heading's 17-22pt (%.1f)" % (r["word"], r["head"]), 18 <= r["word"] <= 21 and 17 <= r["head"] <= 22, r)
    chk("(5) nothing scrolls sideways at his zoom (%d)" % r["sw"], r["sw"] <= 0, r)
    SUB = "(k)=>[...document.querySelectorAll('.screen-settings-sub .settings-card > *')].map(o=>o.getBoundingClientRect().height*k)"
    zoomed = {}
    for pgname in ("sound", "study"):
        pg.evaluate("(p)=>showAppearance({page:p})", pgname); pg.wait_for_timeout(1100)
        zoomed[pgname] = pg.evaluate(SUB, k)
    chk("(5) no page errors at his zoom", not errs, errs)
    ctx.close()
    ctx, pg = boot(br, 440, 956, 440, 956)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    pg.evaluate("()=>showAppearance()"); pg.wait_for_timeout(1300)
    r = pg.evaluate(READ, 1)
    chk("(4) at 100%% nothing is scaled: page-zoomed off, tile %.0fpx, pitch %.0fpx" % (r["tile"], r["pitch"]), (not r["zoomed"]) and abs(r["tile"] - 28) < .6 and abs(r["pitch"] - 51) < .6, r)
    chk("(5) nothing scrolls sideways at 100%% (%d) and no page errors" % r["sw"], r["sw"] <= 0 and not errs, [r["sw"], errs])
    for pgname in ("sound", "study"):
        pg.evaluate("(p)=>showAppearance({page:p})", pgname); pg.wait_for_timeout(1100)
        base = pg.evaluate(SUB, 1); z = zoomed[pgname]
        chk("(3) %s: every row is its 100%% height on the glass at his zoom (%s vs %s)" % (pgname, [round(v) for v in z], [round(v) for v in base]),
            base and len(base) == len(z) and all(abs(a_ - b_) <= 1.5 for a_, b_ in zip(z, base)), [z, base])
    ctx.close(); br.close()
print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
