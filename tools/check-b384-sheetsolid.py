#!/usr/bin/env python3
"""Build 384.26: the Test settings sheet is SOLID on every device (384.25 frosted it on phones and tablets; Madison: "Change this back what the hell??").
(Kept as the gate that holds it solid; its old frosted description follows.)
Build 384.24: the Test settings sheet is frosted glass on a phone or tablet, solid on a big computer.
Madison: "The setting stuff we've talked about should have [the frosted glass]." The sheet was opaque on purpose (r15: a 4K monitor re-blurred a window-wide box on
every frame of its slide); that cost is a big computer's. Read off the page with the sheet open and settled:
 (1) PHONE (440x956), TABLET upright (834x1194), TABLET on its side with touch (1194x834): the sheet has a backdrop-filter that blurs, its fill is translucent (alpha < 1),
     neither it nor any ancestor carries a will-change naming opacity/filter/mask/backdrop-filter or is a backdrop root by value, and the page shows through (Chromium's
     picture: the page hidden and shown changes pixels inside the sheet);
 (2) LAPTOP with a mouse (1366x768) and DESKTOP (1920x1080): the sheet is still the solid one (no backdrop-filter): the r15 cost stays off the machines it was measured on;
 (3) the dim behind it is the pop-ups' (translucent, not the old .5) on the glass sheet; the Virtual Room's Match settings sheet is untouched (no .is-setup: still its own);
 (4) no page errors.
Run:  python3 tools/check-b384-sheetglass.py   (--against OLD/index.html must FAIL (1))"""
import io, os, sys, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
if "--against" in sys.argv:
    body = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
    cb.BODY = cb.INSET_RE.sub("0px", body).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
OPEN = """async(mode)=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms));
  try{ homeUnlocksOwed = () => false; }catch(e){}
  document.querySelectorAll('.unlock-card,.rs-spot,.rs-fly').forEach(n => n.remove()); document.body.classList.remove('cutscene-focus');
  theme.reduceMotion=false; try{ applyTheme(); }catch(e){}
  document.getElementById('unitoptions-modal')?.remove();
  cfg.mode=mode; cfg.source='all'; cfg.timer='off'; cfg.shuffle=true; cfg.recall=false; cfg.flashcards=false; showSetup(); await wait(900);
  const c=document.querySelector('.pick input'); if(!c) return 'nounit'; c.checked=true; c.dispatchEvent(new Event('change',{bubbles:true})); await wait(300);
  document.getElementById('nextbtn').click(); await wait(1600);
  return document.querySelector('.unitoptions-modal-sheet.is-setup') ? 'ok' : 'nosheet'; }"""
READ = """()=>{ const sh=document.querySelector('.unitoptions-modal-sheet.is-setup'); if(!sh) return null; const c=getComputedStyle(sh); const w=c.willChange||'';
  const rootOf=(e)=>{ const q=getComputedStyle(e); return /opacity|filter|backdrop-filter|mask|clip-path/.test(q.willChange||'') || parseFloat(q.opacity)<1 || q.filter!=='none' || (q.backdropFilter&&q.backdropFilter!=='none'); };
  const anc=[]; for(let e=sh.parentElement; e; e=e.parentElement){ if(rootOf(e)) anc.push(e.tagName+'.'+String(e.className||'').slice(0,30)); }
  const m=c.backgroundColor.match(/rgba?\\(([^)]+)\\)/); const alpha = m ? (m[1].split(',').length>3 ? parseFloat(m[1].split(',')[3]) : 1) : 1;
  const scrim=document.querySelector('.unitoptions-modal-scrim'); const sc=scrim?getComputedStyle(scrim).backgroundColor:'';
  const b=sh.getBoundingClientRect();
  return { bf:c.backdropFilter, own:/opacity|filter|mask|backdrop-filter/.test(w)?w:'', anc, alpha, bgImg:c.backgroundImage.slice(0,30), scrim:sc, box:{x:b.left,y:b.top,w:b.width,h:b.height} }; }"""
CASES = (("phone 440x956", 440, 956, False, False), ("tablet upright 834x1194", 834, 1194, True, False), ("tablet on its side 1194x834 (touch)", 1194, 834, True, False),
         ("laptop 1366x768 (mouse)", 1366, 768, False, False), ("desktop 1920x1080", 1920, 1080, False, False))
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    for lab, W, H, touch, frosted in CASES:
        ctx, pg = cb.booted(br, W, H, seed=cb.USED_ACCOUNT, dpr=1, touch=touch)
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        r = pg.evaluate(OPEN, "drill")
        if r != "ok": chk("%s: the sheet opens (%s)" % (lab, r), False, r); ctx.close(); continue
        d = pg.evaluate(READ)
        if frosted:
            chk("(1) %s: the sheet blurs what is behind it (%s), its fill is translucent (alpha %.2f / %s)" % (lab, d["bf"], d["alpha"], d["bgImg"]), "blur" in d["bf"] and (d["alpha"] < 1 or d["bgImg"].startswith("linear")), d)
            chk("(1) %s: no will-change group on the sheet (%r) and no backdrop root above it (%s)" % (lab, d["own"], d["anc"]), not d["own"] and not d["anc"], d)
            b = d["box"]; clip = {"x": b["x"] + 8, "y": b["y"] + 8, "width": b["w"] - 16, "height": min(b["h"] - 16, 260)}
            a = Image.open(io.BytesIO(pg.screenshot(clip=clip))).convert("RGB")
            pg.evaluate("()=>{ const r=document.querySelector('#stage'); if(r) r.style.visibility='hidden'; }"); pg.wait_for_timeout(250)
            c2 = Image.open(io.BytesIO(pg.screenshot(clip=clip))).convert("RGB")
            changed = sum(ImageChops.difference(a, c2).convert("L").histogram()[6:])
            chk("(1) %s: the page under the sheet shows through its glass (%d pixels change when the page is hidden)" % (lab, changed), changed > 300, changed)
        else:
            chk("(2) %s: the solid sheet is kept (no backdrop-filter: %s)" % (lab, d["bf"]), d["bf"] in ("none", ""), d)
        chk("%s: no page errors" % lab, not errs, errs[:2])
        ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILED"); sys.exit(0 if ok else 1)
