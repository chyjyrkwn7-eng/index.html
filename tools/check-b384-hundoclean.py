"""Build 384, round 7 (r2-hundo): nothing of the OLD look is left on the hundo effects' small boxes.
Madison: "The hundo effects, their borders look like the version still? And some of it still looks like the old version?"
In both classes, for each effect: the small boxes the effect shows off in, read off the page -
 (C1) the stage (buildHundoFxStage) and the Customize tile (buildHundoFxTile): no border, no box-shadow, a solid card colour
      (the app's --clean-card), not a gradient fill - and, tinted, the light layer carries the colour (no box-shadow on it);
 (C2) the miniature results screen (buildHundoFxMock): the frame has no border and no gradient wash, and its grade and XP cards
      are the app's solid card with no border / shadow;
 (C3) the unlock pop-up (playUnlockSpotlight): its card has no border and no coloured shadow, no hazard stripe on its strip, its
      name is the app's sans (not the serif), its 'challenge' chip has no border;
 (C4) the effect's detail card (showUnlockDetail): its name is the app's sans too.
Run:  python3 tools/check-b384-hundoclean.py   (--against OLD/index.html must FAIL)"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b384-extspr.py")).read().split("\nsrv, port = serve()")[0]
G = {"__file__": os.path.join(HERE, "check-b384-extspr.py"), "__name__": "b384hundoclean"}
exec(src, G)
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:500], flush=True)
READ = r"""async (ids) => {
  document.getElementById('stage').replaceChildren(); document.body.classList.remove('sky-home');
  const host = document.createElement('div'); host.style.cssText = 'position:fixed;left:0;top:0;width:420px;z-index:9;display:flex;flex-direction:column;gap:12px'; document.body.appendChild(host);
  const rd = e => { const c = getComputedStyle(e); return { bw: parseFloat(c.borderTopWidth) || 0, bc: c.borderTopColor, shadow: c.boxShadow, img: c.backgroundImage, bg: c.backgroundColor }; };
  const out = {};
  for(const id of ids){
    const r = {};
    const st = buildHundoFxStage(id, { big: true }); host.appendChild(st);
    const tile = buildHundoFxTile(id); host.appendChild(tile);
    r.stage = rd(st); r.tile = rd(tile);
    const tn = st.querySelector(':scope > .hfx-tint'); r.stageTint = tn ? { shadow: getComputedStyle(tn).boxShadow, img: getComputedStyle(tn).backgroundImage } : null;
    const m = buildHundoFxMock(id, { delay: 99999 }); m.style.width = '240px'; host.appendChild(m);
    r.mock = rd(m); const cards = [...m.querySelectorAll(':scope > .rs-card')]; r.mockCards = cards.map(rd);
    const mt = m.querySelector('.rs-grade > .hfx-tint'); r.mockTint = mt ? { shadow: getComputedStyle(mt).boxShadow } : null;
    r.mockPct = !!m.querySelector('.rs-pct');
    [st, tile, m].forEach(e => { try{ e.stopFx && e.stopFx(); }catch(_){} ; e.remove(); });
    out[id] = r;
  }
  host.remove();
  return out;
}"""
SPOT = r"""async (id) => {
  document.querySelectorAll('.rs-spot').forEach(e => e.remove());
  playUnlockSpotlight(hundoFxUnlockItem(id), 1, 1, () => {});
  await new Promise(r => setTimeout(r, 3200));
  const sp = document.querySelector('.rs-spot'); if(!sp) return null;
  const q = s => sp.querySelector(s), cs = e => e ? getComputedStyle(e) : null;
  const card = cs(q('.rs-spot-card')), strip = cs(q('.rs-spot-strip')), name = cs(q('.rs-spot-name')), need = cs(q('.rs-spot-need'));
  const out = { bw: parseFloat(card.borderTopWidth) || 0, shadow: card.boxShadow, stripImg: strip ? strip.backgroundImage : 'none', stripShadow: strip ? strip.boxShadow : 'none',
    font: name.fontFamily, needBw: need ? parseFloat(need.borderTopWidth) || 0 : 0 };
  sp.remove(); return out;
}"""
srv, port = G["serve"]()
IDS = ["confetti", "fireworks", "underwater", "bubbles", "ufo"]
SH = lambda s: s in ("none", "", None)
with G["sync_playwright"]() as pw:
    br = pw.chromium.launch(executable_path=G["CHROME"])
    for cls in ("ifc", "academy"):
        init = G["INIT"] if cls == "ifc" else G["INIT"].replace("localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));localStorage.setItem('class26e.greet.ifc','done');", "")
        ctx = br.new_context(viewport={"width": 440, "height": 956}); pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:300])); pg.add_init_script(init)
        pg.route("**/index.html", lambda r: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=G["BODY"]))
        pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(2800)
        pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); }")
        R = pg.evaluate(READ, IDS)
        for id in IDS:
            r = R[id]
            for k in ("stage", "tile"):
                x = r[k]
                chk("(C1) %s %s %s: no border (%spx), no shadow, a solid card colour (%s), no gradient fill" % (cls, id, k, x["bw"], x["bg"]),
                    x["bw"] == 0 and SH(x["shadow"]) and x["img"] == "none" and "0, 0, 0, 0)" not in x["bg"], x)
            if r["stageTint"]: chk("(C1) %s %s: the light layer has no box-shadow (no rim, no glow off the edge)" % (cls, id), SH(r["stageTint"]["shadow"]), r["stageTint"])
            m = r["mock"]
            chk("(C2) %s %s mock: the frame has no border and no gradient wash" % (cls, id), m["bw"] == 0 and m["img"] == "none", m)
            chk("(C2) %s %s mock: its cards are solid, no border, no shadow" % (cls, id), r["mockCards"] and all(c["bw"] == 0 or c["bc"].endswith(", 0)") for c in r["mockCards"]) and all(SH(c["shadow"]) and c["img"] == "none" for c in r["mockCards"]), r["mockCards"])
        for id in IDS[1:]:
            s = pg.evaluate(SPOT, id)
            chk("(C3) %s %s pop-up: card with no border (%s) or shadow but its lift, strip without a hazard stripe, name in the sans (%s), chip without a border" % (cls, id, s and s["bw"], s and s["font"]),
                s and s["bw"] == 0 and "colo" not in (s["shadow"] or "").replace("rgba(0, 0, 0", "") and "repeating" not in s["stripImg"] and SH(s["stripShadow"]) and not s["font"].lower().lstrip('"').startswith(("georgia", "iowan", "ui-serif", "times", "palatino", "baskerville")) and s["needBw"] == 0, s)
        for id in IDS[1:]:
            f = pg.evaluate("(id) => { document.querySelectorAll('.invite-overlay').forEach(e => e.remove()); showUnlockDetail(hundoFxDetail(id)); const n = document.querySelector('.unlock-card-name'); const f = n ? getComputedStyle(n).fontFamily : ''; document.querySelectorAll('.invite-overlay').forEach(e => e.remove()); return f; }", id)
            chk("(C4) %s %s detail card: the name is the app's sans (%s)" % (cls, id, f[:40]), f and not f.lower().lstrip('"').startswith(("georgia", "iowan", "ui-serif", "times", "palatino", "baskerville")), f)
        chk("no page errors (%s)" % cls, not errs, errs[:2]); ctx.close()
    br.close()
print("ALL PASS" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)
