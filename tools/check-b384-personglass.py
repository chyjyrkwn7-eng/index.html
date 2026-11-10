#!/usr/bin/env python3
"""Build 384.24: a person's card is frosted on an iPhone.
Madison, a leaderboard card over the board: "Where's the frosted glass? What's happening?" The card read as a flat dark pane. In Chromium it was always frosted
(the rows show blurred through it), so this reads the one thing WebKit is known to get wrong: the card carried `will-change: opacity, transform`, which makes
it a compositing group with an opacity effect, and WebKit draws a backdrop-filter on such an element against that group (empty), not the page. Read off the page,
with the card up and settled (a second after it opened), in both classes' pages:
 (1) the card has a backdrop-filter that blurs;
 (2) neither the card nor any ancestor carries a will-change that names opacity, filter, backdrop-filter, mask or clip-path (a backdrop root by hint);
 (3) no ancestor has opacity below 1, a filter, a mask or a backdrop-filter of its own (a backdrop root by value) - the page is what the card blurs;
 (4) the page under it shows through the glass (Chromium's picture: the board's rows hidden and shown change pixels inside the card: it is frosted, not flat).
Run:  python3 tools/check-b384-personglass.py   (--against OLD/index.html must FAIL (2))"""
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
BOARD = """(a)=>{ store.leaderboardOptIn=true; const docs=a.names.map((n,i)=>({id:'tstpub'+String(i).padStart(6,'0'), data:()=>Object.assign({}, boardNumbersOf(store), {firstName:n, avatarChar:a.chars[i], level:30-i, points:9000-i*300, weekPoints:100-i, badges:5-(i>>1)})}));
  onSnapshotResilient=function(r,on){ setTimeout(()=>on({metadata:{fromCache:false}, forEach:f=>docs.forEach(f)}),50); return function(){}; }; showRankings(); }"""
CHAIN = """()=>{ const sh=document.querySelector('.invite-sheet.person-card'); if(!sh) return null; const bad=[]; const root=document.documentElement;
  const root_of=(c)=>{ const w=c.willChange||''; const names=/opacity|filter|backdrop-filter|mask|clip-path/.test(w);
    return { hint:names?w:'', op:parseFloat(c.opacity)<1, filter:c.filter!=='none', mask:(c.maskImage&&c.maskImage!=='none')||(c.webkitMaskImage&&c.webkitMaskImage!=='none'), bf:(c.backdropFilter&&c.backdropFilter!=='none')||(c.webkitBackdropFilter&&c.webkitBackdropFilter!=='none') }; };
  const self=getComputedStyle(sh); const own=root_of(self); const anc=[];
  for(let e=sh.parentElement; e; e=e.parentElement){ const r=root_of(getComputedStyle(e)); if(r.hint||r.op||r.filter||r.mask||r.bf) anc.push(e.tagName+'.'+String(e.className||'').slice(0,40)+' '+JSON.stringify(r)); }
  const b=sh.getBoundingClientRect();
  return { bf:self.backdropFilter, ownHint:own.hint, anc, box:{x:b.left,y:b.top,w:b.width,h:b.height} }; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    ctx, pg = cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT, dpr=1)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    names = ["Avery", "Jordan", "Kim", "Lee", "Sam", "Pat", "Chris", "Dana", "Rowan", "Quinn"]; chars = ["alien", "ninja", "wizard", "grizzly", "ghost", "hacker", "zeus", "masked", "marksman", "timekeeper"]
    pg.evaluate(BOARD, {"names": names, "chars": chars}); pg.wait_for_timeout(2200)
    pg.evaluate("()=>{ openPersonSheet({ pub:'tstpub000001', firstName:'Dill Pickle', avatarChar:'alien', level:1, badges:0, points:100, correct:0, hundos:0 }); }")
    pg.wait_for_timeout(1500)
    c = pg.evaluate(CHAIN)
    chk("(1) the card blurs what is behind it (backdrop-filter %s)" % (c and c["bf"]), c and "blur" in c["bf"], c)
    chk("(2) neither the card nor an ancestor carries a will-change that makes a compositing group (card: %r)" % (c and c["ownHint"]), c and not c["ownHint"] and not [a for a in c["anc"] if '"hint": "' in a and '"hint": ""' not in a], c)
    chk("(3) no ancestor is a backdrop root by value (%s)" % (c and c["anc"]), c and not c["anc"], c)
    if c:
        b = c["box"]; clip = {"x": b["x"] + 10, "y": b["y"] + 10, "width": b["w"] - 20, "height": b["h"] - 20}
        a = Image.open(io.BytesIO(pg.screenshot(clip=clip))).convert("RGB")
        pg.evaluate("()=>{ const r=document.querySelector('#stage'); if(r) r.style.visibility='hidden'; }"); pg.wait_for_timeout(200)
        d = Image.open(io.BytesIO(pg.screenshot(clip=clip))).convert("RGB")
        diff = ImageChops.difference(a, d).convert("L"); h = diff.histogram(); changed = sum(h[8:])
        chk("(4) the page under the card shows through its glass (%d pixels change when the page is hidden)" % changed, changed > 400, changed)
    chk("no page errors", not errs, errs[:2])
    ctx.close(); br.close()
print("ALL PASS" if ok else "FAILED"); sys.exit(0 if ok else 1)
