"""Build 330: starred runs score, the retake pays for finishing, and the rest of the round.
Run:  python3 tools/check-b330.py [section ...]   (sections: starred retake first legal modes)"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
from playwright.sync_api import sync_playwright
srv, url = g["serve"]()
DEV = {"se1": (320, 568, (20, 0, 0, 0), True), "promax": (440, 956, (62, 0, 34, 0), True),
       "ipad11": (834, 1194, (24, 0, 20, 0), True), "mac": (1512, 982, (0, 0, 0, 0), False)}
def seed(pid="pubtest00330"):
    d = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]())); d["publicId"] = pid; d["firstName"] = "Casey"; d["novaMet"] = 99
    return json.dumps(d)
INIT = """(()=>{ if(localStorage.getItem('class26e.drill.v1')) return;
 localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-0330');
 ['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.getstarted'].forEach(k=>localStorage.setItem(k,'1'));
 localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.penal256578.seen','1'); })()"""
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else info)
def page_for(br, dev):
    w, h, ins, inst = DEV[dev]; g["new_page"].w, g["new_page"].h = w, h
    ctx, page = g["new_page"](br, ins, inst, False)
    page.add_init_script(INIT % json.dumps(seed()))
    page.goto(url); page.wait_for_timeout(3000)
    page.evaluate("document.getElementById('splashscreen')?.remove()")
    page.evaluate("()=>{ homeUnlocksOwed=()=>false; showHome(); }"); page.wait_for_timeout(1200)
    return ctx, page
# A run, answered in the page: right on the first try except the questions in `wrong`.
RUN = """async ([unit, source, starOnly, wrong])=>{
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const idx = QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === unit && inWholeUnit(QUESTIONS[i]));
  if(source === 'flagged'){ idx.forEach(i => { if(isFlagged(i)) setFlag(i, false); }); (starOnly ? idx.slice(0, starOnly) : idx).forEach(i => setFlag(i, true)); }
  cfg.source = source; cfg.mode = 'drill'; cfg.units = [unit];
  const pool = source === 'flagged' ? idx.filter(i => isFlagged(i)) : idx;
  const xp0 = store.lifetime.points, h0 = unitPerfectCount(unit);
  beginRun(pool); for(let t = 0; t < 80 && !document.querySelector('.qpanel .choice'); t++) await wait(100);
  /* a Drill's miss is a question that needed a second try */
  order.forEach((qi, k) => { attempts[qi] = k < wrong ? 2 : 1; picked[qi] = optionOrder(qi).indexOf(QUESTIONS[qi].answer); });
  stopQuestionTimer(); summarize(); await wait(500);
  return { n: order.length, xp: store.lifetime.points - xp0, hundos: unitPerfectCount(unit) - h0,
           lines: [] }; }"""
# Retake the misses from the results on screen, answering `wrongAgain` of them wrong.
RETAKE = """async (wrongAgain)=>{
  const wait = ms => new Promise(r => setTimeout(r, ms));
  for(let t = 0; t < 60 && !document.querySelector('.rs-continue'); t++) await wait(100);
  await wait(900); document.querySelector('.rs-continue') && document.querySelector('.rs-continue').click(); await wait(900);
  const b = [...document.querySelectorAll('#stage .actions button')].find(x => /Retake missed/.test(x.textContent));
  if(!b) return { err: 'no retake button', btns: [...document.querySelectorAll('#stage button')].map(x => x.textContent).slice(0, 8) };
  b.click(); for(let t = 0; t < 80 && !document.querySelector('.qpanel .choice'); t++) await wait(100);
  const xp0 = store.lifetime.points;
  order.forEach((qi, k) => { attempts[qi] = k < wrongAgain ? 2 : 1; picked[qi] = optionOrder(qi).indexOf(QUESTIONS[qi].answer); });
  stopQuestionTimer(); summarize(); await wait(500);
  return { n: order.length, retake: isMissedRetake, xp: store.lifetime.points - xp0 }; }"""
want = sys.argv[1:] or ["starred", "retake", "first", "legal", "modes"]
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    if "starred" in want:
        ctx, page = page_for(br, "promax")
        r = page.evaluate(RUN, ["Identity Crimes", "flagged", 4, 0])
        chk("a starred run of part of a unit earns its XP (10 a right answer at least)", r["xp"] >= r["n"] * 10 and r["n"] == 4, r)
        chk("...and is no hundo", r["hundos"] == 0, r)
        page.evaluate("()=>showHome()"); page.wait_for_timeout(600)
        r = page.evaluate(RUN, ["Identity Crimes", "flagged", 0, 0])
        chk("a starred run covering a whole unit, all right, is a hundo", r["hundos"] == 1 and r["xp"] > 0, r)
        page.evaluate("()=>showHome()"); page.wait_for_timeout(600)
        ctx.close()
    if "retake" in want:
        ctx, page = page_for(br, "promax")
        page.evaluate(RUN, ["Victims of Crime", "all", 0, 3])
        r = page.evaluate(RETAKE, 0)
        chk("the first retake of a test's misses, all right, pays 75 on top of its answers (3 x 10)", r.get("retake") and r.get("n") == 3 and r.get("xp") == 3 * 10 + 75, r)
        page.evaluate("()=>showHome()"); page.wait_for_timeout(600)
        page.evaluate(RUN, ["Victims of Crime", "all", 0, 3])
        r = page.evaluate(RETAKE, 1)
        chk("the first retake finished with a miss pays 25 on top of its answers (2 x 10)", r.get("n") == 3 and r.get("xp") == 2 * 10 + 25, r)
        r = page.evaluate(RETAKE, 0)
        chk("a retake of that retake pays only its answers - no farming the bonus", r.get("n") == 1 and r.get("xp") == 10, r)
        ctx.close()
    if "first" in want:
        # a first visit: no loading screen in front of Get Started, the button waits for the end
        w, h, ins, inst = DEV["promax"]; g["new_page"].w, g["new_page"].h = w, h
        ctx, page = g["new_page"](br, ins, inst, False)
        page.goto(url); page.wait_for_timeout(1500)
        r = page.evaluate("""()=>{ const sp = document.getElementById('splashscreen'); const vis = !!sp && getComputedStyle(sp).visibility !== 'hidden' && getComputedStyle(sp).opacity !== '0';
          return { gs: !!document.querySelector('.gs-page'), splash: vis }; }""")
        chk("first visit: Get Started is up 1.5s in, with no loading screen over it", r["gs"] and not r["splash"], r)
        page.wait_for_timeout(2500)
        before = page.evaluate("()=>{ const b=document.querySelector('.gs-bar'); return { ready: b.classList.contains('is-ready'), op: +getComputedStyle(b).opacity }; }")
        chk("the Let's get started button is not there until the end of the page", not before["ready"] and before["op"] < 0.1, before)
        page.evaluate("()=>{ const s=document.querySelector('.gs-scroll'); s.scrollTo(0, s.scrollHeight); }"); page.wait_for_timeout(1200)
        after = page.evaluate("""()=>{ const b=document.querySelector('.gs-bar'), go=document.querySelector('.gs-go').getBoundingClientRect(); const l=document.querySelector('.gs-end .gs-legal');
          return { ready: b.classList.contains('is-ready'), op: +getComputedStyle(b).opacity, h: go.height, legal: l ? l.textContent : '',
                   scenes: [...document.querySelectorAll('.gs-scene video')].map(v => v.dataset.gs) }; }""")
        chk("...and rises in at the end", after["ready"] and after["op"] > 0.9 and after["h"] >= 44, after)
        chk("the page's foot says it is independent and carries the copyright, with no name", "Not affiliated" in after["legal"] and "\u00a9" in after["legal"] and "Davis" not in after["legal"], after["legal"])
        chk("a Fire Code scene with its own clip", "ifc" in after["scenes"], after["scenes"])
        ctx.close()
    if "legal" in want:
        ctx, page = page_for(br, "promax")
        r = page.evaluate("""async ()=>{ showAppearance(); await new Promise(r => setTimeout(r, 700)); const n = document.querySelector('.affiliation-note.legal-settings');
          const settings = n ? n.textContent : ''; showClassSelection(); await new Promise(r => setTimeout(r, 500));
          const c = document.querySelector('.classselect-panel .affiliation-note'); return { settings, classes: c ? c.textContent : '' }; }""")
        chk("Settings: made by M. Davis, the copyright, and not affiliated with HCC, TCOLE or the ICC",
            all(x in r["settings"] for x in ("M. Davis", "\u00a9", "HCC", "TCOLE", "International Code Council", "study only")), r["settings"][:200])
        chk("the sign-up class screen says classes are study sets, not a real course", "not enroll you in a real course" in r["classes"], r["classes"])
        ctx.close()
    if "modes" in want:
        ctx, page = page_for(br, "promax")
        r = page.evaluate("""async ()=>{ const W = ms => new Promise(r => setTimeout(r, ms)); const xs = {};
          for(const [k, f] of [['modes', () => showModeSelect()], ['units', () => { cfg.mode = 'drill'; showSetup(); }], ['friends', () => showFriends()], ['ranks', () => showRanksScreen()],
                               ['check', () => showSignUpCheck()], ['classes', () => showClassSelection()]]){
            f(); await W(500); const b = document.querySelector('#stage .back-link'); xs[k] = b ? Math.round(b.getBoundingClientRect().left) : null; }
          showModeSelect(); await W(400);
          const descs = [...document.querySelectorAll('.modecard .modecarddesc')].map(d => d.textContent);
          return { xs, descs, classmates: /classmate/i.test(document.body.innerText) }; }""")
        chk("every Back button sits at the same left edge (the mode screen and sign-up included)", len(set(r["xs"].values())) == 1 and None not in r["xs"].values(), r["xs"])
        chk("the mode descriptions are short (70 characters or fewer) and none says classmates",
            r["descs"] and all(len(d) <= 70 for d in r["descs"]) and not any("classmate" in d.lower() for d in r["descs"]) and not r["classmates"], r["descs"])
        ctx.close()
    br.close()
print("\nALL PASS" if ok else "\nFAILED")
sys.exit(0 if ok else 1)
