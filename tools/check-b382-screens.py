"""Build 382: three things from Madison's iPhone 17 Pro Max.
(a) "The scroll back to top button randomly disappears when you are at the bottom." It stepped aside over any
    control in the last 260px. Now it stays whenever the page is scrolled down, and the screen gets measured room
    at its foot so the last control clears it at the end.
(b) "the background goes from dark to light too late ... When you put the start menu away it happens." The swiped
    sheet left and the dim behind it stayed until the modal was hidden, then went in one frame. Now the scrim follows
    the finger, fades with the slide (same moment, same time) and fades in with the sheet's rise.
(c) "This also looks a little laggy" (a unit's details card: Starred, then Back). Back left a tall empty card for
    320ms before the shrink, and the list was re-laid every frame of the card's grow. Now the shrink starts on the
    tap and the panes keep their own height while the card moves.
Shape only: numbers are read off the page.
Run:  python3 tools/check-b382-screens.py   (--against: copy the old index.html over first)"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
from playwright.sync_api import sync_playwright
srv, url = g["serve"]()
INIT = """(()=>{ if(localStorage.getItem('class26e.drill.v1')) return;
 localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-0382');
 ['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.getstarted'].forEach(k=>localStorage.setItem(k,'1'));
 localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.penal256578.seen','1'); })()"""
d = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]())); d["publicId"] = "pubtest0382s"; d["novaMet"] = 99
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1"
UNIT = "Arrest, Search, and Seizure"
ok = True
errors = []
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else info)

def page(br, w, h, ins, installed=True, touch=True):
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=3 if w < 600 else 2,
                         has_touch=touch, is_mobile=touch, user_agent=UA if touch else None)
    if installed: ctx.add_init_script(g["STANDALONE"])
    ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]()))
    pg = ctx.new_page(); body = g["patched"](ins)
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.add_init_script(INIT % json.dumps(json.dumps(d)))
    pg.on("pageerror", lambda e: errors.append(str(e)[:200]))
    pg.goto(url); pg.wait_for_timeout(3000); pg.evaluate("document.getElementById('splashscreen')?.remove()")
    pg.evaluate("()=>{ homeUnlocksOwed=()=>false; }")
    pg.wait_for_timeout(5000)   # the boot's idle warm-ups, so frames are frames
    return ctx, pg

# ---------------------------------------------------------------- (a)
BTT = """async (scr)=>{
  const wait = ms => new Promise(r => setTimeout(r, ms));
  document.querySelectorAll('#pushing-update,#intro-pop').forEach(n => n.remove());
  ({ topics: () => showSetup(), stats: () => showProfile('stats'), calendar: () => showCalendar(),
     review: () => showTestReviewList(), leaderboard: () => showRankings('week'), settings: () => showAppearance() })[scr]();
  await wait(1200);
  const de = document.documentElement, btn = document.getElementById('backtotop');
  const T = 'button, a[href], [role="button"], input, select, textarea, label, .is-tappable';
  const room = parseFloat(getComputedStyle(document.getElementById('stage')).paddingBottom) || 0;
  const maxBase = de.scrollHeight - innerHeight - room;
  const samples = [];
  const end = de.scrollHeight - innerHeight;
  for(const f of [0.5, 0.8, 0.95, 1]){
    window.scrollTo({ top: Math.round(end * f), behavior: 'instant' }); await wait(500);
    /* its fade can be slow on a loaded first frame: up to a second more */
    let shown = false;
    for(let i = 0; i < 10 && !shown; i++){ shown = btn.classList.contains('show') && parseFloat(getComputedStyle(btn).opacity) > 0.9; if(!shown) await wait(100); }
    samples.push({ y: Math.round(scrollY), shown });
  }
  window.scrollTo({ top: de.scrollHeight, behavior: 'instant' }); await wait(500);
  const b = btn.getBoundingClientRect();
  const under = btn.classList.contains('show') ? [...document.querySelectorAll('#stage ' + T.split(', ').join(', #stage '))].filter(e => {
    const r = e.getBoundingClientRect(); return r.width && r.left < b.right && r.right > b.left && r.top < b.bottom && r.bottom > b.top; })
    .map(e => (e.textContent || e.className).trim().slice(0, 24)) : [];
  const atEnd = { y: Math.round(scrollY), shown: btn.classList.contains('show') && parseFloat(getComputedStyle(btn).opacity) > 0.9 };
  window.scrollTo({ top: 0, behavior: 'instant' }); await wait(200);
  return { maxBase: Math.round(maxBase), room: Math.round(room), samples, atEnd, under };
}"""

def check_a(br):
    for label, w, h, ins in (("Pro Max", 440, 956, (62, 0, 34, 0)), ("iPhone 15", 393, 852, (59, 0, 34, 0)),
                             ("SE", 375, 667, (20, 0, 0, 0)), ("iPad 11", 834, 1194, (24, 0, 20, 0))):
        ctx, pg = page(br, w, h, ins)
        for scr in ("topics", "stats", "calendar", "review", "leaderboard", "settings"):
            r = pg.evaluate(BTT, scr)
            if r["maxBase"] <= 320:
                chk("%s %s: a screen too short to show the arrow gets no room (%s)" % (label, scr, r["room"]), r["room"] == 0, r)
                continue
            missing = [s for s in r["samples"] + [r["atEnd"]] if s["y"] > 320 and not s["shown"]]
            chk("%s %s: back-to-top stays up all the way to the bottom (%d samples, room %dpx)" % (label, scr, len(r["samples"]) + 1, r["room"]),
                not missing, r)
            chk("%s %s: and at the very end it sits on no control" % (label, scr), not r["under"], r)
        ctx.close()

# ---------------------------------------------------------------- (b)
FRAMES = """()=>{ window.__fr = []; let on = true; window.__stopFr = () => { on = false; return window.__fr; };
  const m = document.getElementById('unitoptions-modal');
  const tick = t => { const sh = m.querySelector('.unitoptions-modal-sheet'), sc = m.querySelector('.unitoptions-modal-scrim');
    const vis = !m.hidden && getComputedStyle(m).display !== 'none';
    window.__fr.push({ t, ev: window.__ev || '', vis, top: vis ? sh.getBoundingClientRect().top : innerHeight,
      o: vis ? parseFloat(getComputedStyle(sc).opacity) : 0 }); window.__ev = '';
    if(on) requestAnimationFrame(tick); };
  requestAnimationFrame(tick); }"""

def check_b(br):
    for label, w, h, ins in (("Pro Max", 440, 956, (62, 0, 34, 0)), ("iPad 11", 834, 1194, (24, 0, 20, 0))):
        ctx, pg = page(br, w, h, ins)
        pg.evaluate("()=>{ showSetup(); }"); pg.wait_for_timeout(1500)
        pg.evaluate("""(u)=>{ const row = [...document.querySelectorAll('#stage .pname')].find(p => p.textContent.startsWith(u.split(',')[0])).closest('label');
          const cb = row.querySelector('input'); if(!cb.checked) cb.click(); }""", UNIT)
        pg.wait_for_timeout(500)
        cdp = ctx.new_cdp_session(pg)
        pg.evaluate(FRAMES)
        pg.evaluate("()=>{ window.__ev = 'OPEN'; document.getElementById('nextbtn').click(); }")
        pg.wait_for_timeout(900)
        # the sheet's own head: a drag from there pulls the sheet
        hx, hy, sheetH = pg.evaluate("()=>{ const s = document.querySelector('#unitoptions-modal .unitoptions-modal-head'); const r = s.getBoundingClientRect(); return [r.left + 60, r.top + r.height / 2, document.querySelector('#unitoptions-modal .unitoptions-modal-sheet').offsetHeight]; }")
        y = hy
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": hx, "y": y}]})
        pull = sheetH * 0.55
        for i in range(1, 25):
            y = hy + pull * i / 24
            cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": hx, "y": y}]}); time.sleep(0.016)
        time.sleep(0.15)   # held: a slow pull, not a flick
        pg.evaluate("()=>{ window.__ev = 'RELEASE'; }")
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        pg.wait_for_timeout(900)
        fr = pg.evaluate("()=>window.__stopFr()")
        hidden = pg.evaluate("()=>document.getElementById('unitoptions-modal').hidden")
        oi = next(i for i, f in enumerate(fr) if f["ev"] == "OPEN")
        first = next((f for f in fr[oi:] if f["vis"]), None)
        chk("%s: opening, the dim rises with the sheet (first frame opacity %.2f)" % (label, first["o"] if first else -1),
            first is not None and first["o"] < 0.6, first)
        ri = next(i for i, f in enumerate(fr) if f["ev"] == "RELEASE")
        held = fr[ri - 1]
        chk("%s: pulled down %.0f%%, the dim follows the finger (opacity %.2f)" % (label, 100 * (held["top"] - fr[ri - 30]["top"]) / sheetH if ri >= 30 else 0, held["o"]),
            held["o"] < 0.75, held)
        # the slide out: first frame the sheet moves past where it was let go
        si = next((i for i in range(ri, len(fr)) if fr[i]["top"] > held["top"] + 1), None)
        oi2 = next((i for i in range(ri, len(fr)) if fr[i]["o"] < held["o"] - 0.02), None)
        off = next((i for i in range(ri, len(fr)) if fr[i]["top"] >= h - 1), None)
        gone = next((i for i in range(ri, len(fr)) if fr[i]["o"] <= 0.05), None)
        lag = (fr[oi2]["t"] - fr[si]["t"]) if (si is not None and oi2 is not None) else None
        chk("%s: the dim starts lifting in step with the slide (%s ms after the sheet starts to go)" % (label, None if lag is None else round(lag)),
            lag is not None and lag <= 20, {"slide": si, "dim": oi2})
        late = (fr[gone]["t"] - fr[off]["t"]) if (off is not None and gone is not None) else None
        chk("%s: and is gone by the time the sheet is off the screen (%s ms after)" % (label, None if late is None else round(late)),
            late is not None and late <= 20, {"off": off, "gone": gone, "o_at_off": fr[off]["o"] if off is not None else None})
        chk("%s: the swipe still closes the sheet" % label, hidden is True, hidden)
        # let go early: it springs back and the dim comes back with it
        pg.evaluate("()=>{ document.getElementById('nextbtn').click(); }"); pg.wait_for_timeout(700)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": hx, "y": hy}]})
        for i in range(1, 8):
            cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": hx, "y": hy + 80 * i / 7}]}); time.sleep(0.016)
        time.sleep(0.15)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        pg.wait_for_timeout(700)
        s = pg.evaluate("()=>{ const m = document.getElementById('unitoptions-modal'); const sc = m.querySelector('.unitoptions-modal-scrim'); return { hidden: m.hidden, o: parseFloat(getComputedStyle(sc).opacity), inline: sc.getAttribute('style') || '' }; }")
        chk("%s: a short pull springs back with the dim whole again (%s)" % (label, s), (not s["hidden"]) and s["o"] > 0.99 and "opacity" not in s["inline"], s)
        ctx.close()

# ---------------------------------------------------------------- (c)
# what the card and its panes are doing, read the moment after a tap and on each frame after it
OPEN_LIST = """async ()=>{
  const card = document.querySelector('.unitdetail');
  document.querySelector('.unitdetail-door').click();
  const out = [];
  for(let i = 0; i < 40; i++){
    await new Promise(r => requestAnimationFrame(r));
    const p = card.querySelector('.unitdetail-list');
    const run = card.getAnimations().some(a => a.transitionProperty === 'height' && a.playState === 'running');
    out.push({ run, ph: p ? p.offsetHeight : null });
  }
  await new Promise(r => setTimeout(r, 400));
  const p = card.querySelector('.unitdetail-list');
  return { frames: out, finalPh: p ? p.offsetHeight : null, h: card.getBoundingClientRect().height };
}"""
BACK = """()=>{
  const card = document.querySelector('.unitdetail'), main = card.querySelector('.unitdetail-main');
  document.querySelector('.unitdetail-back').click();
  getComputedStyle(card).height; getComputedStyle(main).opacity;
  const hT = card.getAnimations().find(a => a.transitionProperty === 'height');
  const mT = main.getAnimations().find(a => a.transitionProperty === 'opacity');
  return { shrinking: !!hT, mainDelay: mT ? mT.effect.getTiming().delay : null };
}"""

def check_c(br):
    for label, w, h, ins in (("Pro Max", 440, 956, (62, 0, 34, 0)), ("iPhone 15", 393, 852, (59, 0, 34, 0)), ("SE", 375, 667, (20, 0, 0, 0))):
        ctx, pg = page(br, w, h, ins)
        pg.evaluate("""(u)=>{ let n = 0; QUESTIONS.forEach((q, i) => { if((q.topic || '').trim() === u && n < 8){ setFlag(i, true); n++; } }); showSetup(); }""", UNIT)
        pg.wait_for_timeout(1500)
        pg.evaluate("""(u)=>{ const row = [...document.querySelectorAll('#stage .pname')].find(p => p.textContent.startsWith(u.split(',')[0])).closest('label');
          row.scrollIntoView({ block: 'center' }); row.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true })); }""", UNIT)
        pg.wait_for_timeout(1500)
        rest = pg.evaluate("()=>document.querySelector('.unitdetail').getBoundingClientRect().height")
        o = pg.evaluate(OPEN_LIST)
        listH = o["h"]
        grows = listH - rest >= 2
        if not grows:
            print("  (%s: the card is %.0fpx for the list too - nothing grows or shrinks)" % (label, rest))
        else:
            mid = [f for f in o["frames"] if f["run"] and f["ph"] is not None]
            off = [f for f in mid if abs(f["ph"] - o["finalPh"]) > 1]
            chk("%s: while the card grows to the list (%d frames), the list stands at its own height, not re-laid with the card (%s)" % (label, len(mid), sorted({round(f["ph"]) for f in mid})[:5]),
                len(mid) >= 1 and not off, {"final": o["finalPh"], "off": off[:4]})
        b = pg.evaluate(BACK)
        if grows:
            chk("%s: Back starts the card's shrink on the tap (was a 320ms wait)" % label, b["shrinking"], b)
        chk("%s: and the unit's numbers come back with the list's slide, no .16s wait (delay %s)" % (label, b["mainDelay"]), b["mainDelay"] == 0, b)
        pg.wait_for_timeout(900)
        back = pg.evaluate("()=>({ h: document.querySelector('.unitdetail').getBoundingClientRect().height, panes: document.querySelectorAll('.unitdetail-list').length, mainH: document.querySelector('.unitdetail-main').style.height })")
        chk("%s: the card is back at its own size (rest %.0f, now %.0f), the list removed, no pinned height left" % (label, rest, back["h"]),
            abs(back["h"] - rest) < 1 and back["panes"] == 0 and not back["mainH"], back)
        # quick in-and-out leaves exactly one list
        pg.evaluate("()=>{ document.querySelector('.unitdetail-door').click(); }"); pg.wait_for_timeout(500)
        pg.evaluate("()=>{ document.querySelector('.unitdetail-back').click(); }"); pg.wait_for_timeout(120)
        pg.evaluate("()=>{ document.querySelector('.unitdetail-door').click(); }"); pg.wait_for_timeout(1000)
        q = pg.evaluate("()=>({ panes: document.querySelectorAll('.unitdetail-list').length, h: document.querySelector('.unitdetail').getBoundingClientRect().height })")
        chk("%s: Starred straight after Back shows one list at the list's size (%s)" % (label, q), q["panes"] == 1 and abs(q["h"] - listH) < 1, q)
        ctx.close()

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    check_a(br)
    check_b(br)
    check_c(br)
    br.close()
chk("no page errors", not errors, errors[:5])
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
