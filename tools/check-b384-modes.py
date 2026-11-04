"""Build 384: Choose your mode - the cards in the middle, a little more said on each.
Madison, on Fire Code's three: "there's so much empty space on the bottom here and it feels super off.. should these 3 options be
centered, and for the police one you'd centered the 4 a little better? The wording within the boxes is a little too short. Could
we add a smidge more?"
Read off the page, both classes:
(1) iPhone 17 Pro Max (440x956): the cards sit in the middle of the room between the question under the title and the tab bar
    (16px above it) - the space above the first card and below the last within 2px of each other - Fire Code's three and the
    academy's four; the academy's four all above the tab bar;
(2) the question stays where it was, under the title;
(3) iPad (834x1194): the same middle;
(4) a small phone (375x667) with no room: nothing moved, the cards straight under the question as before;
(5) every card says a little more - a third sentence (its "best for") on each;
(6) no page errors;
(7) nothing on the page itself draws a glow (no radial gradient on the panel or anything in it, before or after) - the only
    light is the fixed sky behind, so nothing glows and moves with the scroll ("is there like a glow on this screen and it
    moves with the scroll but it's not on some of the other screens?").
Run:  python3 tools/check-b384-modes.py   (--against OLD/index.html must FAIL)"""
import json, os, sys, re
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b384md"}
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
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)
READ = """()=>{ const q=document.querySelector('#stage .modeselect-sub'), cards=[...document.querySelectorAll('#stage .modecard')], tb=document.getElementById('bottomtabs');
  const qr=q.getBoundingClientRect(), f=cards[0].getBoundingClientRect(), l=cards[cards.length-1].getBoundingClientRect(), tr=tb.getBoundingClientRect();
  const sentences = cards.map(c => (c.querySelector('.modecarddesc').textContent.match(/[.!?](\\s|$)/g) || []).length);
  const glows = [q.closest('.panel'), ...q.closest('.panel').querySelectorAll('*')].flatMap(e => ['', '::before', '::after'].map(pe => [e, pe, getComputedStyle(e, pe || null)]))
    .filter(([e, pe, s]) => (!pe || (s.content !== 'none' && s.content !== 'normal')) && s.display !== 'none' && /radial-gradient/.test(s.backgroundImage))
    .map(([e, pe]) => (e.className && e.className.baseVal !== undefined ? e.className.baseVal : e.className) + pe);
  return { glows, qTop: qr.top, qBot: qr.bottom, first: f.top, last: l.bottom, tab: tr.top, n: cards.length, above: f.top - qr.bottom, below: (tr.top - 16) - l.bottom, sentences }; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    out, errs_all = {}, []
    for cls in ("ifc", "academy"):
        for (w, h) in ((440, 956), (834, 1194), (375, 667)):
            ctx, pg, errs = G["page"](br, G["init"](G["ifc"] if cls == "ifc" else G["academy"], **({} if cls == "ifc" else {"active": "academy"})))
            pg.set_viewport_size({"width": w, "height": h})
            pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); store.seenModeSelectTour = true; showModeSelect(); }"); pg.wait_for_timeout(1400)
            out[(cls, w)] = pg.evaluate(READ); errs_all += errs; ctx.close()
    fmt = lambda r: "%d cards, %.0f above / %.0f below" % (r["n"], r["above"], r["below"])
    for cls in ("ifc", "academy"):
        r = out[(cls, 440)]
        chk("(1) %s, Pro Max: the cards in the middle under the question (%s), all above the tab bar" % (cls, fmt(r)),
            abs(r["above"] - r["below"]) <= 2 and r["last"] <= r["tab"] - 8 and r["above"] >= 12, r)
        chk("(2) %s, Pro Max: the question still under the title (top %.0f)" % (cls, r["qTop"]), r["qTop"] < 160, r)
        r = out[(cls, 834)]
        chk("(3) %s, iPad: the cards in the middle (%s)" % (cls, fmt(r)), abs(r["above"] - r["below"]) <= 2 and r["above"] > 30, r)
        r = out[(cls, 375)]
        chk("(4) %s, SE: no room, nothing moved (the first card %.0fpx under the question)" % (cls, r["above"]), 10 <= r["above"] <= 24, r)
    sents = {cls: out[(cls, 440)]["sentences"] for cls in ("ifc", "academy")}
    chk("(5) every card says a little more - three sentences each (%s)" % sents, all(min(v) >= 3 for v in sents.values()), sents)
    gl = {k: v["glows"] for k, v in out.items() if v["glows"]}
    chk("(7) nothing on the page draws a glow that would scroll with it (%s)" % (gl or "none, both classes, every size"), not gl, gl)
    chk("(6) no page errors", not errs_all, errs_all[:3])
    br.close()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
