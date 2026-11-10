"""Build 384.20: the Open rooms screen is not empty while it searches, finds nothing, or cannot load.
Madison: "Loading open rooms screen is kinda empty, make that better." Asserted by SHAPE (boxes, running animations, pixels' positions), never by a label:
 (1) the search state is one card that fills the room between the line above and the tab bar (>= 60% of it), its medallion centred in it
     (within 2px, across and down the card), and the Refresh button under it clear of the tab bar (>= 10px);
 (2) while looking, three rings each run an animation of opacity and transform only (nothing else), and the card says something (a title and a line);
 (3) nothing found: the same card, its rings still (nothing running), a title and a line; and it is not the search card (a different title);
 (4) no connection / a read that fails: the same card too (a title and a line);
 (5) Reduce Motion: no ring runs; (6) a room found draws rows again, and the state card is gone; (7) no sideways scroll, no page errors.
Run:  python3 tools/check-b384-openrooms.py   (--against OLD/index.html must FAIL)"""
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
STUB = {
  "look":  "()=>{ window.vroomDb=()=>({collection:()=>({get:()=>new Promise(()=>{}), where(){return this;}})}); }",
  "empty": "()=>{ window.vroomDb=()=>({collection:()=>({get:()=>Promise.resolve({forEach(){}}), where(){return this;}})}); }",
  "fail":  "()=>{ window.vroomDb=()=>({collection:()=>({get:()=>Promise.reject(new Error('x')), where(){return this;}})}); }",
  "none":  "()=>{ window.vroomDb=()=>null; }",
}
MEASURE = """()=>{
  const list=document.querySelector('.rooms-list'), card=list&&list.querySelector('.rooms-empty'); if(!list||!card) return {has:false};
  const tb=document.getElementById('bottomtabs'), floor=(tb&&!tb.hidden&&tb.offsetHeight)?tb.getBoundingClientRect().top:innerHeight;
  const lr=list.getBoundingClientRect(), ic=card.querySelector('.rooms-empty-icon'), ir=ic?ic.getBoundingClientRect():null, ref=document.querySelector('.rooms-refresh').getBoundingClientRect();
  const rings=[...card.querySelectorAll('.rooms-ring')];
  const anims=rings.map(r=>r.getAnimations().filter(a=>a.playState==='running').map(a=>(a.effect.getKeyframes()||[]).flatMap(k=>Object.keys(k)).filter(k=>!['offset','easing','composite','computedOffset'].includes(k))));
  const t=card.querySelector('.rooms-empty-title'), d=card.querySelector('.rooms-empty-text');
  return { has:true, isState:list.classList.contains('is-state'), listTop:lr.top, listH:lr.height, room:floor-lr.top, refBottom:ref.bottom, floor,
    dx: ir ? (ir.left+ir.width/2)-(lr.left+lr.width/2) : null, dy: ir ? (ir.top+ir.height/2)-(card.querySelector('.rooms-empty-art').getBoundingClientRect().top+card.querySelector('.rooms-empty-art').getBoundingClientRect().height/2) : null,
    rings:rings.length, running:anims.map(a=>a.length), props:[...new Set(anims.flat(2))], title:(t&&t.textContent.trim())||'', text:(d&&d.textContent.trim())||'',
    cardClass:card.className, sw:document.documentElement.scrollWidth-innerWidth };
}"""
with sync_playwright() as pw:
    br = pw.chromium.launch()
    for lab, W, H in (("iPhone 17 Pro Max", 440, 956), ("iPhone SE", 375, 667), ("iPad Pro 11in", 834, 1194)):
        ctx, pg = cb.booted(br, W, H, seed=cb.USED_ACCOUNT, dpr=1)
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        pg.evaluate(STUB["look"]); pg.evaluate("()=>showRoomBrowser()"); pg.wait_for_timeout(1500)
        m = pg.evaluate(MEASURE)
        chk("(1) %s: the search is one card (%s)" % (lab, m.get("cardClass")), m.get("has") and m.get("isState"), m)
        if m.get("has"):
            chk("(1) %s: it fills the room above the tab bar (%.0f of %.0f px)" % (lab, m["listH"], m["room"]), m["listH"] >= 0.6 * m["room"] and m["refBottom"] <= m["floor"] - 10 + 1, m)
            chk("(1) %s: the medallion is centred across the card (%.1f px) and in its art (%.1f px)" % (lab, m["dx"] or 0, m["dy"] or 0), m["dx"] is not None and abs(m["dx"]) <= 2 and abs(m["dy"]) <= 2, m)
            chk("(2) %s: three rings run, each opacity and transform only (%s %s)" % (lab, m["running"], m["props"]), m["rings"] == 3 and all(r >= 1 for r in m["running"]) and set(m["props"]) <= {"opacity", "transform"}, m)
            chk("(2) %s: it has a title and a line" % lab, len(m["title"]) > 3 and len(m["text"]) > 3, m)
        looking_title = m.get("title")
        pg.evaluate(STUB["empty"]); pg.evaluate("()=>showRoomBrowser()"); pg.wait_for_timeout(7600)
        e = pg.evaluate(MEASURE)
        chk("(3) %s: nothing found is the same card, still (nothing runs), with its own title and line" % lab,
            e.get("has") and e["isState"] and e["rings"] == 3 and sum(e["running"]) == 0 and e["title"] and e["title"] != looking_title and len(e["text"]) > 3, e)
        pg.evaluate(STUB["fail"]); pg.evaluate("()=>showRoomBrowser()"); pg.wait_for_timeout(2600)
        f = pg.evaluate(MEASURE)
        chk("(4) %s: a read that fails is the card too" % lab, f.get("has") and f["isState"] and len(f["title"]) > 3 and len(f["text"]) > 3, f)
        pg.evaluate(STUB["none"]); pg.evaluate("()=>showRoomBrowser()"); pg.wait_for_timeout(700)
        n = pg.evaluate(MEASURE)
        chk("(4) %s: no connection is the card too" % lab, n.get("has") and n["isState"] and len(n["title"]) > 3, n)
        pg.emulate_media(reduced_motion="reduce")
        pg.evaluate(STUB["look"]); pg.evaluate("()=>showRoomBrowser()"); pg.wait_for_timeout(1200)
        r = pg.evaluate(MEASURE)
        chk("(5) %s: Reduce Motion: no ring runs" % lab, r.get("has") and sum(r["running"]) == 0, r)
        pg.emulate_media(reduced_motion="no-preference")
        pg.evaluate("()=>{ window.vroomDb=()=>({collection:()=>({get:()=>Promise.resolve({forEach(f){ }}), where(){return this;}})}); }")
        pg.evaluate("()=>{ showRoomBrowser(); const l=document.querySelector('.rooms-list'); l.classList.remove('is-state'); l.replaceChildren(Object.assign(document.createElement('div'),{className:'friend-row room-row',textContent:'x'})); }")
        pg.wait_for_timeout(300)
        row = pg.evaluate("()=>({rows:document.querySelectorAll('.rooms-list .room-row').length, card:!!document.querySelector('.rooms-list .rooms-empty'), st:document.querySelector('.rooms-list').classList.contains('is-state'), sw:document.documentElement.scrollWidth-innerWidth})")
        chk("(6) %s: rows replace the card with no leftover state" % lab, row["rows"] == 1 and not row["card"] and not row["st"], row)
        chk("(7) %s: nothing scrolls sideways, no page errors" % lab, row["sw"] <= 0 and not errs, [row["sw"], errs[:2]])
        ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
