"""Build 383: the switches, "a smidge better and smoother".
Madison sent his recording of Review's start sheet (the Flashcards switch) beside iOS's own Settings switch: "I feel like our
toggle switches look really good but they could behave a smidge better and smoother."
Read off his recording at 120fps: (a) the sheet's first frame after the tap was already 73% of the way to its new place (44
of 60px), then crept the rest - it read as a jump; (b) the knob landed and then sat at the end as a hollow dark ring for
~200ms before its white came back; iOS's is solid again almost as it lands.
As an iPhone (its user agent, real touches through CDP), Review's start sheet on a 440x956 phone, the Flashcards switch:
(1) the sheet's fold starts from where it was even when the animation clock runs as Safari's can - started when the
    animation is made - and the tap's task runs on 80ms after it (as a busy phone's does): the first frame drawn after the
    tap is at most 20% of the way, and it is home within 450ms;
(2) the knob is never a hollow ring: no frame where the glass has shrunk more than half-way back to the knob while the
    solid knob is under half shown;
(3) it is all over (the lens gone, the solid knob back) within 450ms of the finger lifting.
Run:  python3 tools/check-b383-toggles.py   (--against OLD/index.html must FAIL)"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b382-toggles.py")).read().split("\nwith sync_playwright() as pw:")[0]
g2 = {"__file__": os.path.join(HERE, "check-b382-toggles.py"), "__name__": "b383t"}
exec(src, g2)
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
    INSET_RE = g2["g"]["INSET_RE"]
    def patched_old(insets):
        t, r, b, l = insets; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
        return INSET_RE.sub(lambda m: v[m.group(1)], OLD)
    g2["g"]["patched"] = patched_old
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)

OPEN = """async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms));
  theme.reduceMotion=false; try{ applyTheme(); }catch(e){}
  cfg.mode='review'; cfg.source='all'; cfg.timer='off'; showSetup(); await wait(700);
  const c=document.querySelector('.pick input'); c.checked=true; c.dispatchEvent(new Event('change',{bubbles:true})); await wait(300);
  document.getElementById('nextbtn').click(); await wait(1500);
  const sh=document.querySelector('.unitoptions-modal-sheet.is-setup'); if(!sh) return null;
  const o=[...sh.querySelectorAll('.opt')].find(o=>/Flashcards/.test(o.textContent)); if(!o) return null;
  const cb=o.querySelector(':scope > input[type=checkbox]'); if(cb.checked){ cb.click(); await wait(600); }
  return { top: sh.getBoundingClientRect().top, capped: sh.scrollHeight > sh.clientHeight + 1 }; }"""
# Safari's clock: an animation's start time is the moment it is made; and the tap's task runs on 80ms after the row's handlers
SAFARI = """()=>{ if(window.__safariClock) return; window.__safariClock = 1;
  const A = Element.prototype.animate;
  Element.prototype.animate = function(k, o){ const a = A.call(this, k, o); try{ a.startTime = document.timeline.currentTime; }catch(e){} return a; };
  window.addEventListener('change', e => { if(!e.target.closest || !e.target.closest('.unitoptions-modal-sheet')) return;
    const t = performance.now(); while(performance.now() - t < 80){} }); }"""
REC = """()=>{ const sh=document.querySelector('.unitoptions-modal-sheet.is-setup');
  const box=[...sh.querySelectorAll('.opt')].find(o=>/Flashcards/.test(o.textContent)).querySelector(':scope > .box');
  const R={ fr:[], T0:performance.now(), change:null, up:null }; window.__rec=R; R.on=true;
  if(!window.__recHook){ window.__recHook=1;
    document.addEventListener('change', e=>{ const r=window.__rec; if(r && r.change==null && e.target.closest && e.target.closest('.unitoptions-modal-sheet')) r.change=performance.now()-r.T0; }, true);
    document.addEventListener('touchend', ()=>{ const r=window.__rec; if(r && r.up==null) r.up=performance.now()-r.T0; }, true); }
  const sc = el => { if(!el) return null; const m = new DOMMatrixReadOnly(getComputedStyle(el).transform); return Math.hypot(m.a, m.b); };
  const f=()=>{ const t=performance.now()-R.T0; const lens=box.querySelector('.nsw-lens');
    const body=lens && lens.querySelector('.nsw-lens-body'), solid=lens && lens.querySelector('.nsw-lens-solid');
    R.fr.push({ t, top: sh.getBoundingClientRect().top, lens: !!lens, sx: sc(body), solid: solid ? +getComputedStyle(solid).opacity : null });
    if(R.on) requestAnimationFrame(f); };
  R.on=false; f(); R.on=true; R.fr[0].t=-1; requestAnimationFrame(f); }"""
READ = """()=>{ const R=window.__rec; R.on=false; return { fr:R.fr, change:R.change, up:R.up }; }"""
CENTRE = g2["CENTRE"]

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g2["g"]["CHROME"])
    ctx, pg, cdp = g2["page"](br, 440, 956)
    info = pg.evaluate(OPEN)
    if not info:
        chk("Review's start sheet opens with its Flashcards switch", False)
    else:
        pg.wait_for_timeout(6000)
        pg.evaluate(SAFARI)
        rest = None
        for turn in ("on", "off"):
            xy = pg.evaluate(CENTRE, "Flashcards")
            pg.evaluate(REC)
            pg.wait_for_timeout(120)
            g2["tap"](cdp, xy[0], xy[1])
            pg.wait_for_timeout(900)
            r = pg.evaluate(READ)
            fr = r["fr"]; ch = r["change"]; up = r["up"]
            s0 = fr[0]["top"]; s1 = fr[-1]["top"]
            after = [x for x in fr if ch is not None and x["t"] > ch]
            first = after[0] if after else None
            frac = abs(first["top"] - s0) / abs(s1 - s0) if first and abs(s1 - s0) > .5 else None
            home = next((x["t"] for x in after if abs(x["top"] - s1) < .5), None)
            chk("(1) %s: the sheet moves (%.1fpx) and its first frame after the tap is where it was - %s of the way (at most 20%%)"
                % (turn, s1 - s0, "?" if frac is None else "%d%%" % round(frac * 100)),
                frac is not None and frac <= .2, {"first": first, "s0": s0, "s1": s1, "change": ch})
            chk("(1) %s: and home within 450ms of the tap (%s)" % (turn, None if home is None else "%dms" % (home - ch)),
                home is not None and home - ch <= 450, home)
            lensf = [x for x in fr if x["lens"] and x["sx"] is not None]
            if lensf:
                big = max(x["sx"] for x in lensf); small = min(x["sx"] for x in lensf)
                mid = (big + small) / 2
                after_up = [x for x in lensf if up is not None and x["t"] > up]
                hollow = [(round(x["t"] - up), round(x["sx"], 3), round(x["solid"], 2)) for x in after_up if x["sx"] < mid and (x["solid"] or 0) < .5]
                chk("(2) %s: never a hollow ring - no frame shrunk past half-way with the solid knob under half shown (%d such frames)" % (turn, len(hollow)),
                    not hollow, hollow[:6])
                gone = next((x["t"] for x in fr if up is not None and x["t"] > up and not x["lens"]), None)
                chk("(3) %s: the lens is gone, the solid knob back, within 450ms of the finger lifting (%s)" % (turn, None if gone is None else "%dms" % (gone - up)),
                    gone is not None and gone - up <= 450, {"gone": gone, "up": up})
            else:
                chk("(2) %s: the glass knob ran" % turn, False, "no lens frames")
            pg.wait_for_timeout(700)
    ctx.close()
    br.close()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
