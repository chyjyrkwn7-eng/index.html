"""Build 384: a hundo effect stopped part way leaves every piece where it was for its fade, in both classes.
The cutscene audit: "Academy Underwater: tapping its card away mid-showcase throws about 20 pieces toward the left edge as
it fades" - the same fault as Fire Code's Thermal Camera, fixed there for its reticle alone. The stop (a card tapped away,
the screen changing) cancelled every animation and then faded the layers for .6s, so each piece went back to where it rests
- the corner of the screen - for the fade. Now the pieces in the fading layers are held where they are and let go after.
Read off the page, iPhone 17 Pro Max, the academy's five effects and Fire Code's five, each on a results card and in a tile
(the card's showcase), stopped at two moments:
(1) the academy: no piece still showing moves more than 4px, or appears, when it is stopped;
(2) Fire Code: the same (it was clean for the Thermal Camera's reticle; now for every piece);
(3) everything it put up is gone after the fade, and no page errors.
Run:  python3 tools/check-b384-fxstop.py   (--against OLD/index.html must FAIL)"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b384stop"}
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
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:500], flush=True)
JUMP = r"""async (a) => {
  const card = document.createElement('div'); card.className = 'rs-card rs-grade is-perfect __probe';
  card.style.cssText = 'position:fixed;left:30px;top:170px;width:380px;height:185px';
  const pct = document.createElement('span'); pct.className = 'rs-pct pct perfect'; pct.style.cssText = 'position:absolute;left:24px;top:44px;font-size:67px;line-height:.95';
  gradePctMarkup(pct, 100); card.appendChild(pct); document.body.appendChild(card);
  let h, st = null;
  if(a.box){ st = buildHundoFxStage(a.id, { big: true }); st.classList.add('__probe'); st.style.cssText = 'position:fixed;left:20px;top:420px;width:400px'; document.body.appendChild(st);
    h = playHundoFx(a.id, { box: st, pct: st.querySelector('.hfx-stage-pct'), boxOnly: true }); }
  else h = playHundoFx(a.id, { box: card, pct, preview: true });
  if(!h){ card.remove(); if(st) st.remove(); return 'skip'; }
  await new Promise(r => setTimeout(r, a.at));
  const roots = [h.screen, h.box].filter(Boolean), leaves = [];
  roots.forEach(r => r.querySelectorAll('*').forEach(e => { if(!e.children.length) leaves.push(e); }));
  const eff = el => { let o = 1; for(let e = el; e && roots.indexOf(e) < 0; e = e.parentElement) o *= +getComputedStyle(e).opacity; return o; };
  const snap = () => leaves.map(e => { const r = e.getBoundingClientRect(); return { o: eff(e), x: r.left, y: r.top, w: r.width }; });
  const before = snap(); h.stop(); const after = snap();
  const bad = after.filter((q, i) => q.o > .05 && q.w > 0 && (before[i].o < .05 || Math.abs(q.x - before[i].x) > 4 || Math.abs(q.y - before[i].y) > 4)).map(q => [Math.round(q.x), Math.round(q.y)]);
  await new Promise(r => setTimeout(r, 800)); card.remove(); if(st) st.remove();
  return bad; }"""
LEFT = "()=>document.querySelectorAll('.hfx-layer, .hfx-screen, .hfx-dim, .__probe').length"
errs_all, res, left = [], {}, {}
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    for cls in ("academy", "ifc"):
        ctx, pg, errs = G["page"](br, G["init"](G["ifc"] if cls == "ifc" else G["academy"], **({} if cls == "ifc" else {"active": "academy"})))
        pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); }")
        ids = pg.evaluate("()=>HUNDO_FX.map(f => f.id)")
        jumps, skipped, played = [], [], set()
        for fid in ids:
            for box in (False, True):
                for at in (1400, 3000):
                    b = pg.evaluate(JUMP, {"id": fid, "box": box, "at": at})
                    if b == "skip": skipped.append((fid, "tile" if box else "card")); continue
                    played.add(fid)
                    if b: jumps.append((fid, "tile" if box else "card", at, len(b), b[:2]))
        res[cls] = (sorted(played), jumps, sorted(set(skipped)))
        pg.wait_for_timeout(900); left[cls] = pg.evaluate(LEFT)
        errs_all += errs; ctx.close()
    br.close()
for n, cls in ((1, "academy"), (2, "ifc")):
    ids, jumps, skipped = res[cls]
    chk("(%d) %s: %s stopped part way, on a card and in a tile, twice each - no piece moves or appears (%s; not played: %s)" % (n, cls, ids, jumps[:3] or "none", skipped),
        len(ids) >= 4 and not jumps, jumps)
chk("(3) nothing left after the fades (%s) and no page errors (%s)" % (left, errs_all[:2]), not any(left.values()) and not errs_all, [left, errs_all])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
