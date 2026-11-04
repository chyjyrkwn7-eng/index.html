"""Build 383: Fire Code's flash cards - a control on the card is not a tap on the card.
Madison (a screen recording of Fire Code's Review flash cards): "Tapping certain stuff in the flash cards makes them flip when
I'm just trying to view them and use the drop down or whatever on some of it. Ensure this good to go."
In Fire Code, as an iPhone-sized touch screen, a flash card from the book (IFC) and one from the county's amendments:
(1) a tap on the card turns it to its answer side;
(2) a tap on "Show the code" opens the code and the card stays on its answer side;
(3) a button inside the code box (here "Load my IFC PDF" - no book in the sandbox) does its own thing and the card stays;
(4) the card grows to hold the opened code: nothing of the answer side hangs out of the card, and the arrows under it stay
    clear; "Hide the code" closes it, the card stays on its answer side and shrinks back;
(5) Enter on a focused "Show the code" opens it rather than flipping the card;
(6) a tap on the rest of the answer side (a choice) still turns the card back.
Run:  python3 tools/check-b383-flashcards.py   (--against OLD/index.html must FAIL)"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b383fc"}
exec(src, G)
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = G["g"]["INSET_RE"]
    def _old(ins):
        t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
        return IR.sub(lambda m: v[m.group(1)], OLD)
    G["g"]["patched"] = _old
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)

STATE = """()=>{ const c=document.querySelector('.fc-card'); const b=c.querySelector('.fc-back'); const d=b.querySelector('details.ifc-code');
  const cr=c.getBoundingClientRect(), nav=document.querySelector('.fc-back-btn, .fc-next-btn');
  return { flipped: c.classList.contains('is-flipped'), open: d ? d.open : null, faceH: b.scrollHeight, cardH: Math.round(cr.height),
           cardBottom: Math.round(cr.bottom), navTop: nav ? Math.round(nav.getBoundingClientRect().top) : null }; }"""
AT = """(sel)=>{ const e=document.querySelector(sel); if(!e) return null; e.scrollIntoView({block:'center'}); return true; }"""
XY = """(sel)=>{ const e=document.querySelector(sel); if(!e) return null; const r=e.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]; }"""

def tap(pg, sel):
    if not pg.evaluate(AT, sel): return False
    pg.wait_for_timeout(400)
    # the page may still be gliding from the scroll (or the card growing): tap once the target has stood still
    xy, prev = None, None
    for _ in range(20):
        xy = pg.evaluate(XY, sel)
        if xy and prev and abs(xy[0] - prev[0]) < .5 and abs(xy[1] - prev[1]) < .5: break
        prev = xy; pg.wait_for_timeout(120)
    if not xy: return False
    pg.touchscreen.tap(xy[0], xy[1]); return True

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    for kind in ("book", "amendment"):
        ctx, pg, errs = G["page"](br, G["init"](G["ifc"]))
        unit = pg.evaluate("""async(kind)=>{ const w=ms=>new Promise(r=>setTimeout(r,ms));
          const q = QUESTIONS.find(q=>q.ifc && q.ifc.citation && ((q.ifc.citation.source==='amendment') === (kind==='amendment')));
          if(!q) return null; showFlashcards([q.topic.trim()], 'all'); await w(1200);
          /* the deck is shuffled: deal the card that is this kind */
          const want = QUESTIONS.indexOf(q); const at = fc.deck.indexOf(want); if(at > 0){ fc.pos = at; showFlashcards(fc.units, fc.source, fc.versions); await w(900); }
          return q.topic.trim(); }""", kind)
        if not unit:
            chk("%s: a Fire Code card of this kind" % kind, False); ctx.close(); continue
        pg.evaluate("()=>{ window.ifcPickBook = () => { window.__picked = (window.__picked || 0) + 1; }; }")
        tap(pg, ".fc-card .fc-front .fc-fliphint"); pg.wait_for_timeout(900)
        s1 = pg.evaluate(STATE)
        chk("(1) %s: a tap on the card turns it to its answer" % kind, s1["flipped"] is True, s1)
        tap(pg, ".fc-card .fc-back summary.ifc-code-sum"); pg.wait_for_timeout(1800)
        s2 = pg.evaluate(STATE)
        chk("(2) %s: 'Show the code' opens the code and the card stays on its answer" % kind, s2["flipped"] is True and s2["open"] is True, s2)
        chk("(4) %s: the card holds the opened code (answer side %spx in a %spx card) and the arrows are below it (%s / %s)"
            % (kind, s2["faceH"], s2["cardH"], s2["cardBottom"], s2["navTop"]),
            s2["faceH"] <= s2["cardH"] + 2 and s2["navTop"] is not None and s2["navTop"] >= s2["cardBottom"] - 1, s2)
        if kind == "book":
            hit = tap(pg, ".fc-card .fc-back .ifc-code button"); pg.wait_for_timeout(900)
            s3 = pg.evaluate(STATE); picked = pg.evaluate("()=>window.__picked || 0")
            chk("(3) book: the code box's own button does its thing (%s) and the card stays on its answer" % picked, hit and picked >= 1 and s3["flipped"] is True, s3)
        tap(pg, ".fc-card .fc-back summary.ifc-code-sum"); pg.wait_for_timeout(1000)
        s4 = pg.evaluate(STATE)
        chk("(4) %s: 'Hide the code' closes it, the card stays on its answer and shrinks back (%s -> %s)" % (kind, s2["cardH"], s4["cardH"]),
            s4["flipped"] is True and s4["open"] is False and s4["cardH"] < s2["cardH"], s4)
        pg.evaluate("()=>{ const s=document.querySelector('.fc-card .fc-back summary.ifc-code-sum'); s.focus(); }")
        pg.keyboard.press("Enter"); pg.wait_for_timeout(900)
        s5 = pg.evaluate(STATE)
        chk("(5) %s: Enter on 'Show the code' opens it, no flip" % kind, s5["flipped"] is True and s5["open"] is True, s5)
        tap(pg, ".fc-card .fc-back .fc-choices li"); pg.wait_for_timeout(900)
        s6 = pg.evaluate(STATE)
        chk("(6) %s: a tap on a choice still turns the card back" % kind, s6["flipped"] is False, s6)
        chk("%s: no page errors" % kind, not errs, errs[:2])
        ctx.close()
    br.close()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
