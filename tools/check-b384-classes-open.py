#!/usr/bin/env python3
"""Build 384: Fire Code open to everyone, and at sign-up.

Madison: "everyone is gonna get the button" / "almost every single new account will be signing up and enrolling into fire
code from the beginning" / "a fire code only person can enroll into the police academy class if they wanted to" / "only
these people will get banner that it's available" / "Ensure that it has two types, new accounts, and existing enrolling into
an additional class" / "at the end of it, it didn't let me hit continue, I had to hit skip to get past it" / "After verified
shouldn't it say success ... the button makes more sense? Like it could say enroll and get started".

Walked as a person would, in an iPhone Safari tab (440x956) unless said, with an in-memory Firestore that keeps its
documents across reloads (check-b384-a2hs's harness). The IFC book's check is stood in (ifcAnalyzeBook - the screen, its
12-second floor and everything after it are the app's own). Codes are minted by the app; names and ids are made up.

  ifconly   - a sign-up for Fire Code alone, from Get Started: (1) the class step offers both classes as cards, each picked and
              unpicked with a tap, Continue only while one is picked; (2) the confirm sheet names Fire Code and the book;
              (3) the book step is the enrol screen; leaving it (Back) keeps the pick and nothing of an account exists; the
              next launch still has no account and the class step still has the pick; (4) the book checked: "Success", "Your
              IFC PDF is referenced", Continue; (5) Nova asks the name and the partner and gives the code (the save-code
              card), ends on "Open Fire Code", whose Continue (a mouse click) ends him; (6) the app opens Fire Code and Nova
              goes on there (Fire Code's welcome, three ways to train), Continue ends him; (7) the tips run on Fire Code's
              Home, then the +100 XP (Fire Code's), Add to Home Screen, "You're enrolled in Fire Code", Nova's good-luck
              message in Fire Code's chat; (7c) the tips include one on the class button, pointing at it ("Your classes");
              (8) no Police Academy / Class 26E word anywhere on that path; no What's New card,
              and the What's New mark at INTRO_REV; (9) the class button: Fire Code, its list has no academy; (10) the cloud:
              the account's classes ["ifc"], Fire Code's own document, NO row on the academy's board; (11) the next launch,
              even with the device's class setting gone, opens Fire Code again with nothing replayed; no page errors.
  newdevice - (12) signing in with that code on a fresh phone lands in Fire Code (welcomed back), with ["ifc"] and its 100 XP;
              a both-classes account signs in to the academy with both in its list.
  join      - (13) the Fire Code-only account joins Police Academy from the class list: the academy's card says Enroll (no
              book), asks once, the academy opens; Nova greets it as an account joining another class (no name or partner
              asked), his last Continue ends it, then "You're enrolled in Police Academy"; the account has both classes, the
              class button lists Fire Code and switches back to it; and the academy may now have its row.
  both      - (14) a sign-up for both: the confirm names both, the book step, then Police Academy's full sign-up, its tips
              naming the class button; "You're enrolled in Police Academy and Fire Code"; (14g) no class-button tip again on
              its own (a new account); both on the account, Fire Code in the class button; Fire Code's first visit greets it
              as an account joining another class, and its last Continue ends it.
  existing  - (15) an account from before 384 (not the owner) has the class button; Fire Code from the class list: the
              book's check says "Success" and "Enroll and get started", which enrols it and opens Fire Code; a class it is
              not in cannot be opened (the device's class setting alone is refused).
  banner    - (16) "Fire Code is open to join" and the button's pulse go to an account on NEW_CLASS_INVITES (a test hash patched
              into the list here - the real list is left alone) and only it: not an unlisted account, not a listed one
              already in Fire Code; tapping it opens the class list; once per device (not after a relaunch).
  tip       - (18) an account from before the class button (its tours at 383's revision, Version 10's card not seen): What's
              New first, and no tip under it; then one tip, on the class button, with nothing over it; Got it, and the
              account says so (synced); not again on the next launch.
  switch    - the owner's situation (the academy in Silver wearing Void; Fire Code's copy from before 384 carrying both, unlocked
              in neither), an iPhone with a disk cache as a phone has (a static server answering as GitHub Pages does), the
              class button both ways at 4x CPU on slow 3G (500 kbps, 2s round trips) once Home has been up a while:
              (19) each class shows its own theme - Fire Code its default, the academy Silver - and remembers it per class;
              (19b) the status bar's colour per class; (20) each class its own character - Void stays in the academy, never in
              Fire Code; (21) the loader starts in the colours of the class left and turns to the class opened's, through the
              colours between (an in-page log kept across the reload); (22) nothing big downloaded (Fire Code's questions
              already in the cache); (22b) the loader's bar keeps moving while the next page comes; (22c) each Home comes up
              and nothing on it moves after (the times are printed); (23) "Welcome back to Fire Code" / "...to the Police
              Academy" on arrival; (23b) not on a plain relaunch; no page errors.
  finals    - (17) every one of Nova's class walkthroughs ends on its last Continue, at 440x956 (tap) and 1536x864 (mouse):
              a new account's introduction (academy), Fire Code alone's two halves, Fire Code's and the academy's greeting
              for an account joining another class, and an existing account's meeting.

  python3 tools/check-b384-classes-open.py
  python3 tools/check-b384-classes-open.py --against /path/to/old-index.html     (must FAIL)
  ONLY=ifconly,banner python3 tools/check-b384-classes-open.py
"""
import hashlib, json, os, re, sys, tempfile, time
HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, "check-b384-a2hs.py"), encoding="utf-8").read().split('\nprint("check-b384-a2hs against"')[0]
G = {"__file__": os.path.join(HERE, "check-b384-a2hs.py"), "__name__": "b384co"}
exec(_src, G)
from playwright.sync_api import sync_playwright

SRC, SRC_PATH, BUILD, CHROME, ROOT = G["SRC"], G["SRC_PATH"], G["BUILD"], G["CHROME"], G["ROOT"]
ONLY = G["ONLY"]
def want(sec): return not ONLY or sec in ONLY

# --- the invite list gets a test account of its own (its hash), never one of the real ones ---------------------------
INVITED = "pubgate38401"
INV_HASH = hashlib.sha256(INVITED.encode()).hexdigest()[:16]
_orig_body = G["body"]
def body(ins):
    b = _orig_body(ins)
    return b.replace('const NEW_CLASS_INVITES = [', 'const NEW_CLASS_INVITES = [ "%s",' % INV_HASH, 1)
G["body"] = body

fails = []
def chk(name, cond, info=""):
    print(("  PASS " if cond else "  FAIL ") + name + ("" if cond else "  -> " + str(info)[:700]), flush=True)
    if not cond: fails.append(name)

class Sec:
    """a section's checks, declared up front: any not reached (an earlier step failed) is a FAIL"""
    def __init__(self, title, keys):
        self.keys = list(keys); self.done = set(); print("\n" + title, flush=True)
    def ck(self, key, label, cond, info=""):
        self.done.add(key); chk("(%s) %s" % (key, label), cond, info); return bool(cond)
    def finish(self, why=""):
        for k in self.keys:
            if k not in self.done: chk("(%s) not reached%s" % (k, (" - " + why) if why else ""), False)

POLICE = re.compile(r"police|26e|academy|penal|tcole", re.I)
SEEN = ("['class26e.freshstart','class26e.unithold.tip','class26e.getstarted','class26e.frame.ok','class26e.daily.seen','class26e.savecode.card',"
        "'class26e.savecode.asked','class26e.a2hs'].forEach(k=>localStorage.setItem(k, k==='class26e.frame.ok'?'go-live-1':'1'));"
        "localStorage.setItem('class26e.intro.seen','99');")
SEEN_IFC = ("['class26e.ifc.freshstart','class26e.ifc.daily.seen','class26e.ifc.savecode.card','class26e.ifc.savecode.asked','class26e.ifc.getstarted',"
            "'class26e.ifc.a2hs','class26e.ifc.unithold.tip'].forEach(k=>localStorage.setItem(k,'1'));")
def account(name, pub, pts=0, correct=0, **extra):
    d = {"firstName": name, "avatarChar": "ghost", "onboardingComplete": True, "publicId": pub, "leaderboardOptIn": True,
         "tourRev": 999, "novaMet": 99, "lastModified": 1790500000000, "novaHeard": {"@recap": 99991231}, "savedCodeSaved": True,
         "seenMainMenuTour": True, "seenProfileTour": True, "seenModeSelectTour": True, "seenUnitSelectTour": True,
         "seenRankingsTour": True, "seenAppearanceTour": True, "badgeBandsVersion": 99,
         "lifetime": {"points": pts, "answered": correct + 10, "correct": correct}}
    d.update(extra)
    return d
def seed_init(acct, code, extra=""):
    return SEEN + "localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode', '%s');" % (json.dumps(json.dumps(acct)), code) + extra

def open_page(br, dev="iphone", init="", seed=None, wait=3500):
    return G["open_page"](br, dev, init=init, seed=seed, wait=wait)

def ev(pg, js, arg=None, default=None):
    """evaluate, riding out a page that is reloading under it"""
    for _ in range(3):
        try: return pg.evaluate(js, arg) if arg is not None else pg.evaluate(js)
        except Exception as e:
            if "Execution context was destroyed" in str(e) or "navigation" in str(e).lower() or "Target closed" in str(e):
                pg.wait_for_timeout(600); continue
            raise
    return default

def wait_for(pg, js, secs=30, step=250):
    t0 = time.time()
    while time.time() - t0 < secs:
        try:
            v = pg.evaluate(js)
            if v: return v
        except Exception: pass
        pg.wait_for_timeout(step)
    return None

def screen(pg): return ev(pg, G["SCREEN"], default="")

NOVA_ST = r"""(id)=>{ const n=document.getElementById(id); if(!n||!n.__nova) return null;
  const go=n.querySelector('.nt-go'); const gs=go ? getComputedStyle(go) : null;
  return { asking:n.__nova.asking, typing:n.__nova.typing, i:n.__nova.index, count:n.__nova.count,
    name: !!n.querySelector('.nt-ask-name input'), char: !!n.querySelector('.nt-ask-char .avatarchar-option'),
    later: !!n.querySelector('.nt-ask-later'), card: !!document.getElementById('savecode-card'),
    text: (n.querySelector('.nt-text')||{}).textContent || '', stage: (n.querySelector('.nt-stage')||{}).innerText || '',
    go: !!go && gs.display !== 'none' && go.getBoundingClientRect().height > 30, goText: go ? go.textContent : '' }; }"""

def walk_nova(pg, talk="nova-intro", name="Casey Rivera", texts=None, secs=300, tap=False, pace=0):
    """taps through one of Nova's talks as a person would, answering what he asks; ends it with his last Continue
       (a real click, or a tap); returns what happened"""
    out = {"asked": set(), "final": None, "ended": False, "lines": [], "stuck": None, "later": False}
    t0 = time.time(); last_i = -1; same = 0
    while time.time() - t0 < secs:
        st = ev(pg, NOVA_ST, talk)
        if not st:
            if out["final"] is not None: out["ended"] = True; break
            pg.wait_for_timeout(200)
            if time.time() - t0 > 25 and out["final"] is None and not out["lines"]: break
            continue
        if st["later"]: out["later"] = True
        if texts is not None and not st["typing"]:
            for t in (st["text"], st["stage"]):
                if t and t not in texts: texts.append(t)
        if not st["typing"] and st["text"] and (not out["lines"] or out["lines"][-1] != st["text"]): out["lines"].append(st["text"])
        if st["card"] and "card" not in out["asked"]:
            out["asked"].add("card"); pg.wait_for_timeout(300)
            if texts is not None: texts.append(ev(pg, "()=>(document.getElementById('savecode-card')||{}).innerText||''", default=""))
            pg.click("#savecode-card .savecode-ack"); pg.wait_for_timeout(150)
            pg.click("#savecode-card .savecode-continue"); pg.wait_for_timeout(500); continue
        if st["asking"] and not st["typing"] and st["name"] and "name" not in out["asked"]:
            out["asked"].add("name")
            pg.click("#%s .nt-ask-input" % talk); pg.keyboard.type(name); pg.keyboard.press("Enter")
            for _ in range(60):
                if not ev(pg, "(id)=>!!document.querySelector('#'+id+' .nt-ask-name')", talk): break
                pg.wait_for_timeout(100)
            continue
        if st["asking"] and not st["typing"] and st["char"] and "char" not in out["asked"]:
            out["asked"].add("char")
            pg.click("#%s .nt-ask-char .avatarchar-option" % talk); pg.wait_for_timeout(300)
            pg.click("#%s .nt-ask-char .nt-ask-go" % talk); pg.wait_for_timeout(1200); continue
        if st["typing"]:
            if not pace: ev(pg, "(id)=>document.getElementById(id).__nova.advance()", talk)   # (a recording lets him finish)
        elif not st["asking"]:
            if st["i"] == st["count"] - 1:
                if st["go"]:
                    out["final"] = st["goText"]
                    try:
                        if tap: pg.tap("#%s .nt-go" % talk)
                        else: pg.click("#%s .nt-go" % talk)
                    except Exception: pass
                    pg.wait_for_timeout(900)
                    gone = ev(pg, "(id)=>{ const n=document.getElementById(id); return !n || n.classList.contains('leaving'); }", talk, default=True)
                    if gone: out["ended"] = True; break
                else:
                    same += 1
                    if same > 25: out["stuck"] = "last line: no Continue shown"; break
            else:
                if pace: pg.wait_for_timeout(pace)
                ev(pg, "(id)=>document.getElementById(id).__nova.advance()", talk)
        if st["i"] == last_i: pass
        last_i = st["i"]
        pg.wait_for_timeout(120)
    return out

TIP = r"""()=>{ const t=document.getElementById('tour-tooltip'); if(!t) return null; const d=document.getElementById('tour-line-dot');
  const b=document.querySelector('.class-bubble'); const dr=d && getComputedStyle(d).display!=='none' ? d.getBoundingClientRect() : null, br=b ? b.getBoundingClientRect() : null;
  const near = !!(dr && br) && Math.hypot((dr.left+dr.width/2)-(br.left+br.width/2), (dr.top+dr.height/2)-(br.top+br.height/2)) <= Math.max(br.width, br.height);
  return { text: (document.getElementById('tour-text')||{}).textContent || t.innerText, onBubble: near,
           banner: !!document.querySelector('.daily-alert'), whatsnew: !!document.getElementById('intro-pop') }; }"""
def tips(pg, texts=None, secs=40, steps=None):
    """the tips, tapped through; returns how many (each step's words and whether it points at the class button in `steps`)"""
    n = 0
    if not wait_for(pg, "()=>!!document.getElementById('tour-tooltip')", secs): return 0
    for _ in range(25):
        if not ev(pg, "()=>!!document.getElementById('tour-next')", default=False): break
        pg.wait_for_timeout(450)
        t = ev(pg, TIP)
        if t and steps is not None: steps.append(t)
        if texts is not None: texts.append(ev(pg, "()=>(document.getElementById('tour-tooltip')||{}).innerText||''", default=""))
        ev(pg, "()=>document.getElementById('tour-next').click()"); n += 1; pg.wait_for_timeout(380)
    return n
def class_tip_of(steps): return [s for s in steps if "Your classes" in s["text"] or "class button" in s["text"]]

STUB_BOOK = """()=>{ window.ifcAnalyzeBook = async (file, step) => { const W = ms => new Promise(r => setTimeout(r, ms));
  for(let i = 0; i <= 4; i++){ step('open', i / 4); await W(40); } for(let i = 0; i <= 10; i++){ step('index', i / 10); await W(60); }
  for(let i = 0; i <= 6; i++){ step('verify', i / 6); await W(60); } return { level: 'exact', kept: true, badIds: [] }; }; }"""
_pdf_dir = tempfile.mkdtemp(prefix="b384co-")
PDF = os.path.join(_pdf_dir, "2021 International Fire Code.pdf")
open(PDF, "wb").write(b"%PDF-1.4\n%stand-in for the gate\n")

def pick_book(pg):
    """the enrol screen's Choose my IFC PDF, a file, the check; returns the result screen"""
    ev(pg, STUB_BOOK)
    with pg.expect_file_chooser(timeout=8000) as fc:
        pg.click("#stage .class-enroll .ce-go")
    fc.value.set_files(PDF)
    if not wait_for(pg, "()=>!!document.querySelector('.ifc-analyze.is-ok, .ifc-analyze.is-bad')", 60): return None
    pg.wait_for_timeout(400)
    return ev(pg, """()=>{ const o=document.querySelector('.ifc-analyze'); const b=o.querySelector('.ia-actions button');
      return { ok: o.classList.contains('is-ok'), title: o.querySelector('.ia-title').textContent, result: o.querySelector('.ia-result').textContent,
               button: b ? b.textContent : '', text: o.innerText }; }""")

CLASSSTEP = """()=>{ const p=document.querySelector('#stage .classselect-panel'); if(!p) return null;
  const c=k=>p.querySelector('.class-card.is-'+k); const st=k=>c(k) ? { on: c(k).classList.contains('is-picked'), chip: c(k).querySelector('.cc-status').textContent } : null;
  const n=p.querySelector('#nextbtn');
  return { academy: st('academy'), ifc: st('ifc'), soon: !!p.querySelector('.class-card.is-soon'), cont: !!n && !n.hidden }; }"""

def to_class_step(pg):
    if screen(pg) == "getstarted":
        ev(pg, "()=>{ const s=document.querySelector('.gs-scroll'); s && s.scrollTo(0, s.scrollHeight); }"); pg.wait_for_timeout(1400)
        pg.click(".gs-go"); pg.wait_for_timeout(1000)
    pg.click(".welcome-new"); pg.wait_for_timeout(700)
    if ev(pg, "()=>!!document.getElementById('newacct-confirm')", default=False):
        pg.click("#newacct-confirm .newacct-new, #newacct-confirm .next.playbtn"); pg.wait_for_timeout(600)
    pg.click(".signupcheck-go"); pg.wait_for_timeout(700)
    return ev(pg, CLASSSTEP)

def confirm_text(pg):
    return ev(pg, "()=>{ const e=document.getElementById('classenroll-confirm'); return e ? e.innerText : null; }")

def cloud(pg): return ev(pg, "()=>window.__cloud", default={}) or {}

def visible_text(pg):
    return ev(pg, "()=>document.body.innerText", default="")

print("check-b384-classes-open against", SRC_PATH, "(build %s)" % BUILD)
state = {}
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME, args=["--autoplay-policy=no-user-gesture-required"])

    # ---------------------------------------------------------------------------------------------------------- ifconly
    if want("ifconly") or want("newdevice") or want("join"):
        S = Sec("A sign-up for Fire Code alone (iPhone, a Safari tab)", ["1", "2", "3", "3b", "4", "5", "6", "7", "7b", "7c", "8", "8b", "9", "10", "11", "11b"])
        ctx, pg = open_page(br, "iphone")
        path = []          # every word seen after Fire Code was picked
        try:
            s0 = to_class_step(pg)
            pg.click(".classselect-panel .class-card.is-academy"); pg.wait_for_timeout(300); a1 = ev(pg, CLASSSTEP)
            pg.click(".classselect-panel .class-card.is-ifc"); pg.wait_for_timeout(300); a2 = ev(pg, CLASSSTEP)
            pg.click(".classselect-panel .class-card.is-academy"); pg.wait_for_timeout(300); a3 = ev(pg, CLASSSTEP)
            pg.click(".classselect-panel .class-card.is-ifc"); pg.wait_for_timeout(300); a4 = ev(pg, CLASSSTEP)
            pg.click(".classselect-panel .class-card.is-ifc"); pg.wait_for_timeout(300); a5 = ev(pg, CLASSSTEP)
            S.ck("1", "the class step offers both classes and More classes; each is picked and unpicked by a tap; Continue only while one is (%s)" % [s0, a1, a2, a3, a4, a5],
                 s0 and s0["academy"] and s0["ifc"] and s0["soon"] and not s0["cont"] and a1["academy"]["on"] and a1["cont"] and a2["academy"]["on"] and a2["ifc"]["on"]
                 and not a3["academy"]["on"] and a3["ifc"]["on"] and a3["cont"] and not a4["ifc"]["on"] and not a4["cont"] and a5["ifc"]["on"] and not a5["academy"]["on"] and a5["cont"]
                 and a5["ifc"]["chip"] != a4["ifc"]["chip"], [s0, a5])
            pg.click(".classselect-panel #nextbtn"); pg.wait_for_timeout(700)
            ct = confirm_text(pg) or ""
            path.append(ct)
            S.ck("2", "Continue asks first, naming Fire Code and its book (%r)" % ct[:160], "Fire Code" in ct and "PDF" in ct and not POLICE.search(ct), ct)
            pg.click("#classenroll-confirm .classenroll-yes"); pg.wait_for_timeout(900)
            enr = ev(pg, "()=>{ const p=document.querySelector('#stage .class-enroll'); return p ? { text: p.innerText, go: !!p.querySelector('.ce-go') } : null; }")
            if enr: path.append(enr["text"])
            pg.click("#stage .class-enroll .ios-nav-bar .back-link, #stage .class-enroll .back-link"); pg.wait_for_timeout(800)
            back = ev(pg, CLASSSTEP)
            none = ev(pg, "()=>({ code: syncCode, pub: store.publicId || null, docs: Object.keys(window.__cloud.progress || {}) })")
            S.ck("3", "the book step is Fire Code's enrol screen; Back leaves it for the class step with Fire Code still picked, and no account exists (%s, %s)" % (back, none),
                 bool(enr) and enr["go"] and back and back["ifc"]["on"] and back["cont"] and not none["code"] and not none["docs"], [enr, back, none])
            G["relaunch"](pg); pg.wait_for_timeout(400)
            again = to_class_step(pg)
            none2 = ev(pg, "()=>({ code: syncCode, docs: Object.keys(window.__cloud.progress || {}) })")
            S.ck("3b", "the next launch: still no account, and the class step still has Fire Code picked (%s)" % again,
                 again and again["ifc"]["on"] and not again["academy"]["on"] and again["cont"] and not none2["code"] and not none2["docs"], [again, none2])
            pg.click(".classselect-panel #nextbtn"); pg.wait_for_timeout(700)
            pg.click("#classenroll-confirm .classenroll-yes"); pg.wait_for_timeout(900)
            res = pick_book(pg)
            if res: path.append(res["text"])
            S.ck("4", "the book checked: %r / %r / button %r" % (res and res["title"], res and res["result"][:60], res and res["button"]),
                 res and res["ok"] and res["title"] == "Success" and res["result"].startswith("Your IFC PDF is referenced") and res["button"] == "Continue", res)
            pg.click(".ifc-analyze .ia-actions button")
            wait_for(pg, "()=>!!document.getElementById('genprofile-overlay')", 8)
            pg.wait_for_selector("#genprofile-overlay", state="detached", timeout=30000)
            under = ev(pg, "()=>({ home: !!document.querySelector('#stage [data-screen=\"home\"]'), stage: document.getElementById('stage').innerText.trim().slice(0,80) })")
            p1 = walk_nova(pg, texts=path, name="Casey Rivera")
            S.ck("5", "Nova's first half: the name, the partner (no academy crew), the code's card; ends on %r, whose Continue ends him; no academy Home under him (%s)" % (p1["final"], under),
                 {"name", "char", "card"} <= p1["asked"] and not p1["later"] and p1["final"] == "Open Fire Code" and p1["ended"] and not under["home"], [p1["asked"], p1["final"], p1["ended"], p1["stuck"], under])
            state["code"] = None
            wait_for(pg, "()=>window.NOVA_CLASS === 'ifc' && !!document.getElementById('nova-intro')", 40)
            p2 = walk_nova(pg, texts=path, name="Casey Rivera")
            got = ev(pg, "()=>({ cls: window.NOVA_CLASS, code: shownSyncCode(), name: store.firstName })", default={}) or {}
            state["code"] = got.get("code")
            S.ck("6", "Fire Code opens and Nova goes on there (%r ... %r), Continue (%r) ends him" % ((p2["lines"] or [""])[0], (p2["lines"] or [""])[-1], p2["final"]),
                 got.get("cls") == "ifc" and p2["ended"] and any("Welcome to Fire Code" in l for l in p2["lines"]) and any("three ways to train" in l for l in p2["lines"])
                 and not any("Mock" in l for l in p2["lines"]) and not p2["asked"], [got, p2["lines"][:3], p2["final"], p2["stuck"]])
            steps = []
            n = tips(pg, path, steps=steps)
            home = ev(pg, "()=>({ cls: window.NOVA_CLASS, home: !!document.querySelector('#stage [data-screen=\"home\"]') })", default={})
            xp = wait_for(pg, "()=>document.getElementById('welcomebonus-banner') ? (store.lifetime||{}).points : 0", 15)
            S.ck("7", "the tips run on Fire Code's Home (%d), then +100 XP in Fire Code (%s)" % (n, xp), n >= 4 and home.get("cls") == "ifc" and home.get("home") and xp == 100, [n, home, xp])
            ct = class_tip_of(steps)
            S.ck("7c", "a new account's tips include the class button, pointing at it (%s)" % [(c["text"][:50], c["onBubble"]) for c in ct],
                 len(ct) == 1 and ct[0]["onBubble"] and ct[0]["text"].startswith("Your classes"), [s["text"][:40] for s in steps])
            sheet = wait_for(pg, "()=>{ const o=document.getElementById('a2hs-sheet'); return o && o.classList.contains('invite-overlay-show') ? o.innerText : null; }", 40)
            if sheet: path.append(sheet); pg.wait_for_timeout(600); pg.click("#a2hs-sheet .a2hs-foot button"); pg.wait_for_timeout(600)
            enrolled = wait_for(pg, "()=>{ const e=document.getElementById('enrolled-banner'); return e ? e.innerText : null; }", 20)
            if enrolled: path.append(enrolled)
            luck = wait_for(pg, "()=>{ const t=localStorage.getItem('class26e.nova')||''; return /Good luck on your learning adventure/.test(t) ? t : null; }", 40)
            if luck: path.append("Good luck on your learning adventure")
            state["late_tip"] = ev(pg, "()=>!!document.getElementById('tour-tooltip')", default=None)
            S.ck("7b", "then Add to Home Screen, \"You're enrolled in Fire Code\" (%r), and Nova's good-luck message in Fire Code's chat (%s)" % ((enrolled or "")[:60], bool(luck)),
                 bool(sheet) and bool(enrolled) and "enrolled in Fire Code" in enrolled and bool(luck), [bool(sheet), enrolled, bool(luck)])
            path.append(visible_text(pg))
            bad = sorted(set(m.group(0) for t in path for m in POLICE.finditer(t or "")))
            S.ck("8", "no Police Academy / Class 26E word anywhere on the way (%d pieces of text read: %s)" % (len(path), bad or "none"), len(path) > 20 and not bad,
                 [t[:120] for t in path if POLICE.search(t or "")][:4])
            wn = ev(pg, "()=>({ card: !!document.getElementById('intro-pop'), seen: Number(localStorage.getItem('class26e.intro.seen')) || 0, rev: INTRO_REV })", default={})
            S.ck("8b", "no What's New card, and its mark at INTRO_REV (%s)" % wn, wn and not wn["card"] and wn["seen"] >= wn["rev"] >= 7, wn)
            ev(pg, "()=>{ document.querySelectorAll('.daily-alert,.app-banner').forEach(e=>e.remove()); }")
            pg.click(".class-bubble"); pg.wait_for_timeout(700)
            cb = ev(pg, "()=>({ icon: document.querySelector('.class-bubble').className, items: [...document.querySelectorAll('.class-stack-item')].map(b=>b.className.replace('class-stack-item','').trim()), enrolled: enrolledClasses() })")
            S.ck("9", "the class button is Fire Code's, and its list has no academy, only Add a class (%s)" % cb,
                 "is-ifc" in cb["icon"] and cb["items"] == ["is-add"] and cb["enrolled"] == ["ifc"], cb)
            pg.click(".class-bubble"); pg.wait_for_timeout(400)
            ev(pg, "()=>{ try{ pushToCloud(true); }catch(e){} }"); pg.wait_for_timeout(2500)
            c = cloud(pg); code = state["code"]
            acad = (c.get("progress") or {}).get(code) or {}; ifcd = (c.get("progress") or {}).get((code or "") + "__ifc") or {}
            S.ck("10", "the cloud: the account (%s) says classes %s; Fire Code's document has the 100 XP; the academy's board has no row (%s)" % (code, acad.get("classes"), list((c.get("leaderboard") or {}).keys())),
                 bool(code) and acad.get("classes") == ["ifc"] and (ifcd.get("lifetime") or {}).get("points") == 100 and not (c.get("leaderboard") or {}),
                 [code, acad.get("classes"), (ifcd.get("lifetime") or {}).get("points"), c.get("leaderboard")])
            state["cloud"] = c
            G["relaunch"](pg, wait=4500)
            r1 = ev(pg, "()=>({ cls: window.NOVA_CLASS, screen: (document.querySelector('#stage [data-screen]')||{dataset:{}}).dataset.screen, nova: !!document.getElementById('nova-intro'), tour: !!document.getElementById('tour-tooltip') })")
            ev(pg, "()=>localStorage.removeItem('class26e.activeclass')")
            G["relaunch"](pg, wait=4500)
            r2 = ev(pg, "()=>({ cls: window.NOVA_CLASS, screen: (document.querySelector('#stage [data-screen]')||{dataset:{}}).dataset.screen, active: localStorage.getItem('class26e.activeclass') })")
            pg.wait_for_timeout(8000)
            r2["tour"] = ev(pg, "()=>!!document.getElementById('tour-tooltip')")
            S.ck("11", "the next launch opens Fire Code with nothing replayed - no Nova, no tip, the class button's own tip never on its own (%s); with the device's class setting gone, Fire Code still (%s)" % (r1, r2),
                 r1["cls"] == "ifc" and r1["screen"] == "home" and not r1["nova"] and not r1["tour"] and r2["cls"] == "ifc" and r2["screen"] == "home" and not r2["tour"]
                 and state.get("late_tip") is False, [r1, r2, state.get("late_tip")])
            G["relaunch"](pg, wait=4500)
            state["cloud"] = cloud(pg)
        except Exception as e:
            print("  INFO stopped:", str(e)[:300])
        S.ck("11b", "no page errors", not pg.errs, pg.errs[:3])
        S.finish("the walk stopped")
        state["ifc_ctx"] = (ctx, pg)

    # -------------------------------------------------------------------------------------------------------- newdevice
    if want("newdevice"):
        S = Sec("Signing in on a fresh phone", ["12", "12b"])
        try:
            code = state.get("code"); cl = state.get("cloud") or {}
            ctx2, p2 = open_page(br, "iphone", seed={"progress": cl.get("progress", {})})
            if screen(p2) == "getstarted":
                ev(p2, "()=>{ const s=document.querySelector('.gs-scroll'); s && s.scrollTo(0, s.scrollHeight); }"); p2.wait_for_timeout(1400); p2.click(".gs-go"); p2.wait_for_timeout(900)
            p2.click(".welcome-signin"); p2.wait_for_timeout(500)
            p2.fill(".synccode-entry-panel input:not([type=checkbox])", ""); p2.focus(".synccode-entry-panel input:not([type=checkbox])"); p2.keyboard.type(code or "")
            p2.click(".synccode-entry-panel #nextbtn"); p2.wait_for_timeout(900)
            p2.click(".synccode-confirm .next.playbtn")
            r = wait_for(p2, "()=>window.NOVA_CLASS === 'ifc' && document.querySelector('#stage [data-screen=\"home\"]') ? ({ cls: window.NOVA_CLASS, list: enrolledClasses(), pts: (store.lifetime||{}).points, name: store.firstName }) : null", 45)
            wb = wait_for(p2, "()=>{ const e=document.getElementById('welcome-banner'); return e ? e.innerText : null; }", 8)
            # its Fire Code progress comes down from Fire Code's own document a moment after the first Home
            if r and r["cls"] == "ifc": r["pts"] = wait_for(p2, "()=>((store.lifetime||{}).points === 100) ? 100 : 0", 25) or r["pts"]
            S.ck("12", "the code on a fresh phone opens Fire Code (%s), welcomed back (%r)" % (r, (wb or "")[:50]),
                 bool(r) and r["list"] == ["ifc"] and r["pts"] == 100 and r["name"] == "Casey Rivera" and bool(wb), [r, wb])
            S.ck("12b", "no page errors", not p2.errs, p2.errs[:3])
            ctx2.close()
        except Exception as e:
            print("  INFO stopped:", str(e)[:300])
        S.finish()
        # a both-classes account signs in to the academy, both in its list
        S = Sec("Signing in, an account in both classes", ["12c"])
        try:
            both = account("Robin Both", "pubgate38402", 40, 12, classes=["academy", "ifc"])
            ctx3, p3 = open_page(br, "iphone", seed={"progress": {"TEST-BOTH": both}})
            if screen(p3) == "getstarted":
                ev(p3, "()=>{ const s=document.querySelector('.gs-scroll'); s && s.scrollTo(0, s.scrollHeight); }"); p3.wait_for_timeout(1400); p3.click(".gs-go"); p3.wait_for_timeout(900)
            p3.click(".welcome-signin"); p3.wait_for_timeout(500)
            p3.focus(".synccode-entry-panel input:not([type=checkbox])"); p3.keyboard.type("TEST-BOTH")
            p3.click(".synccode-entry-panel #nextbtn"); p3.wait_for_timeout(900)
            p3.click(".synccode-confirm .next.playbtn")
            r = wait_for(p3, "()=>document.querySelector('#stage [data-screen=\"home\"]') && !document.getElementById('genprofile-overlay') ? ({ cls: window.NOVA_CLASS, list: enrolledClasses() }) : null", 40)
            p3.wait_for_timeout(1200)
            items = ev(p3, "()=>{ const b=document.querySelector('.class-bubble'); if(b) b.click(); return [...document.querySelectorAll('.class-stack-item')].map(x=>x.className); }", default=[])
            S.ck("12c", "it signs in to Police Academy with both classes, Fire Code in the class button (%s, %s)" % (r, items),
                 bool(r) and r["cls"] == "academy" and r["list"] == ["academy", "ifc"] and any("is-ifc" in i for i in items) and not p3.errs, [r, items, p3.errs[:2]])
            ctx3.close()
        except Exception as e:
            print("  INFO stopped:", str(e)[:300])
        S.finish()

    # ------------------------------------------------------------------------------------------------------------- join
    if want("join"):
        S = Sec("A Fire Code-only account joins Police Academy", ["13", "13b", "13c", "13d", "13e"])
        ctx, pg = state.get("ifc_ctx") or (None, None)
        try:
            if not pg: raise RuntimeError("no Fire Code-only account (the ifconly walk)")
            ev(pg, "()=>{ document.querySelectorAll('.daily-alert,.app-banner,#a2hs-sheet').forEach(e=>e.remove()); showClassCatalog(); }"); pg.wait_for_timeout(900)
            card = ev(pg, """()=>{ const c=document.querySelector('#stage .class-card.is-academy'); return c ? { status: c.querySelector('.cc-status').textContent, needs: !!c.querySelector('.cc-needs'),
                   ifc: (document.querySelector('#stage .class-card.is-ifc .cc-status')||{}).textContent } : null; }""")
            pg.click("#stage .class-card.is-academy"); pg.wait_for_timeout(700)
            ct = confirm_text(pg) or ""
            S.ck("13", "the class list: Police Academy says Enroll (no book), Fire Code Enrolled; it asks once (%s / %r)" % (card, ct[:80]),
                 card and card["status"] == "Enroll" and not card["needs"] and card["ifc"] == "Enrolled" and "Police Academy" in ct, [card, ct])
            pg.click("#classenroll-confirm .classenroll-yes")
            wait_for(pg, "()=>window.NOVA_CLASS === 'academy' && !!document.getElementById('nova-class-greet')", 45)
            g = walk_nova(pg, talk="nova-class-greet")
            S.ck("13b", "the academy opens and Nova greets an account joining another class (%r ... %r): nothing asked, his last Continue (%r) ends it" % ((g["lines"] or [""])[0], (g["lines"] or [""])[-1], g["final"]),
                 g["ended"] and not g["asked"] and any("Welcome to Police Academy" in l for l in g["lines"]) and any("class button" in l for l in g["lines"])
                 and not any("what should I call you" in l for l in g["lines"]), [g["lines"][:4], g["final"], g["stuck"]])
            eb = wait_for(pg, "()=>{ const e=document.getElementById('enrolled-banner'); return e ? e.innerText : null; }", 15)
            r = ev(pg, "()=>({ cls: window.NOVA_CLASS, list: enrolledClasses(), classes: store.classes, pts: (store.lifetime||{}).points })")
            S.ck("13c", "\"You're enrolled in Police Academy\" (%r); the account is in both (%s), the academy at zero" % ((eb or "")[:50], r),
                 bool(eb) and "enrolled in Police Academy" in eb and r["cls"] == "academy" and r["list"] == ["academy", "ifc"] and r["classes"] == ["academy", "ifc"] and (r["pts"] or 0) == 0, [eb, r])
            ev(pg, "()=>{ try{ pushToCloud(true); }catch(e){} }"); pg.wait_for_timeout(3000)
            c = cloud(pg); pub = ev(pg, "()=>store.publicId")
            acad = (c.get("progress") or {}).get(state.get("code")) or {}
            S.ck("13d", "its account says both classes (%s) and the academy may now have its row (%s)" % (acad.get("classes"), pub in (c.get("leaderboard") or {})),
                 acad.get("classes") == ["academy", "ifc"] and pub in (c.get("leaderboard") or {}), [acad.get("classes"), list((c.get("leaderboard") or {}).keys())])
            ev(pg, "()=>{ document.querySelectorAll('.daily-alert,.app-banner').forEach(e=>e.remove()); }")
            pg.click(".class-bubble"); pg.wait_for_timeout(700)
            items = ev(pg, "()=>[...document.querySelectorAll('.class-stack-item')].map(b=>b.className)", default=[])
            if any("is-ifc" in i for i in items): pg.click(".class-stack-item.is-ifc")
            back = wait_for(pg, "()=>window.NOVA_CLASS === 'ifc' && document.querySelector('#stage [data-screen=\"home\"]') ? enrolledClasses() : null", 40)
            S.ck("13e", "the class button lists Fire Code and switches back to it (%s -> %s); no page errors" % (items, back),
                 any("is-ifc" in i for i in items) and back == ["academy", "ifc"] and not pg.errs, [items, back, pg.errs[:3]])
        except Exception as e:
            print("  INFO stopped:", str(e)[:300])
        S.finish()
    if state.get("ifc_ctx"):
        try: state["ifc_ctx"][0].close()
        except Exception: pass

    # ------------------------------------------------------------------------------------------------------------- both
    if want("both"):
        S = Sec("A sign-up for both classes (iPhone, a Safari tab)", ["14", "14b", "14c", "14g", "14d", "14e", "14f"])
        ctx, pg = open_page(br, "iphone")
        try:
            to_class_step(pg)
            pg.click(".classselect-panel .class-card.is-academy"); pg.wait_for_timeout(250)
            pg.click(".classselect-panel .class-card.is-ifc"); pg.wait_for_timeout(250)
            pg.click(".classselect-panel #nextbtn"); pg.wait_for_timeout(700)
            ct = confirm_text(pg) or ""
            pg.click("#classenroll-confirm .classenroll-yes"); pg.wait_for_timeout(900)
            res = pick_book(pg)
            S.ck("14", "the confirm names both (%r); Fire Code's book step follows (%s)" % (ct[:120], res and res["title"]),
                 "Police Academy" in ct and "Fire Code" in ct and res and res["title"] == "Success" and res["button"] == "Continue", [ct, res])
            pg.click(".ifc-analyze .ia-actions button")
            wait_for(pg, "()=>!!document.getElementById('genprofile-overlay')", 8)
            pg.wait_for_selector("#genprofile-overlay", state="detached", timeout=30000)
            nv = walk_nova(pg, name="Robin Twoclass")
            S.ck("14b", "Police Academy's whole sign-up: Nova asks the name, the partner, the code, ends on %r" % nv["final"],
                 {"name", "char", "card"} <= nv["asked"] and nv["ended"] and ev(pg, "()=>window.NOVA_CLASS") == "academy"
                 and any("four ways to train" in l for l in nv["lines"]), [nv["asked"], nv["final"], nv["stuck"]])
            steps = []
            n = tips(pg, steps=steps)
            sheet = wait_for(pg, "()=>{ const o=document.getElementById('a2hs-sheet'); return o && o.classList.contains('invite-overlay-show'); }", 40)
            if sheet: pg.wait_for_timeout(500); pg.click("#a2hs-sheet .a2hs-foot button"); pg.wait_for_timeout(500)
            eb = wait_for(pg, "()=>{ const e=document.getElementById('enrolled-banner'); return e ? e.innerText : null; }", 20)
            ct = class_tip_of(steps)
            S.ck("14c", "the tips name the class button, pointing at it (%s); then \"You're enrolled in Police Academy and Fire Code\" (%r)" % ([(c["text"][:40], c["onBubble"]) for c in ct], (eb or "")[:90]),
                 n >= 4 and len(ct) == 1 and ct[0]["onBubble"] and bool(eb) and "Police Academy and Fire Code" in eb, [n, eb, [s["text"][:40] for s in steps]])
            pg.wait_for_timeout(9000)
            late = ev(pg, "()=>{ const t=document.getElementById('tour-text'); return t ? t.textContent : null; }")
            S.ck("14g", "a new account is not shown the class button's tip again on its own (%r)" % late, late is None and ev(pg, "()=>store.seenClassTip") is True, late)
            ev(pg, "()=>{ try{ pushToCloud(true); }catch(e){} }"); pg.wait_for_timeout(2500)
            r = ev(pg, "()=>({ list: enrolledClasses(), code: syncCode, pub: store.publicId })")
            c = cloud(pg)
            S.ck("14d", "both on the account (%s, cloud %s), the academy's row there" % (r["list"], ((c.get("progress") or {}).get(r["code"]) or {}).get("classes")),
                 r["list"] == ["academy", "ifc"] and ((c.get("progress") or {}).get(r["code"]) or {}).get("classes") == ["academy", "ifc"] and r["pub"] in (c.get("leaderboard") or {}), r)
            ev(pg, "()=>{ document.querySelectorAll('.daily-alert,.app-banner').forEach(e=>e.remove()); }")
            pg.click(".class-bubble"); pg.wait_for_timeout(700)
            items = ev(pg, "()=>[...document.querySelectorAll('.class-stack-item')].map(b=>b.className)", default=[])
            if any("is-ifc" in i for i in items): pg.click(".class-stack-item.is-ifc")
            wait_for(pg, "()=>window.NOVA_CLASS === 'ifc' && !!document.getElementById('nova-class-greet')", 45)
            g = walk_nova(pg, talk="nova-class-greet")
            S.ck("14e", "Fire Code's first visit: Nova greets an account joining another class (nothing asked), last Continue (%r) ends it" % g["final"],
                 g["ended"] and not g["asked"] and any("Welcome to Fire Code" in l for l in g["lines"]) and any("class button" in l for l in g["lines"]), [items, g["lines"][:3], g["final"], g["stuck"]])
            S.ck("14f", "no page errors", not pg.errs, pg.errs[:3])
        except Exception as e:
            print("  INFO stopped:", str(e)[:300])
        S.finish()
        ctx.close()

    # --------------------------------------------------------------------------------------------------------- existing
    if want("existing"):
        S = Sec("An existing account (not the owner) enrols in Fire Code from the class list", ["15", "15b", "15c", "15d"])
        acct = account("Jordan Oldtimer", "pubgate38403", 300, 90)
        ctx, pg = open_page(br, "iphone", init=seed_init(acct, "TEST-OLD1"), seed={"progress": {"TEST-OLD1": acct}})
        try:
            ev(pg, "()=>{ homeUnlocksOwed=()=>false; if(!document.querySelector('.screen-home-actual')) showHome(); }"); pg.wait_for_timeout(1500)
            b = ev(pg, "()=>({ bubble: !!document.querySelector('.class-bubble'), list: enrolledClasses() })")
            ev(pg, "()=>localStorage.setItem('class26e.activeclass','ifc')"); G["relaunch"](pg)
            refused = ev(pg, "()=>({ cls: window.NOVA_CLASS, active: localStorage.getItem('class26e.activeclass') })")
            S.ck("15", "it has the class button (%s); the device's class setting alone does not open Fire Code (%s)" % (b, refused),
                 b["bubble"] and b["list"] == ["academy"] and refused["cls"] == "academy" and refused["active"] is None, [b, refused])
            ev(pg, "()=>{ document.querySelectorAll('.daily-alert,.app-banner').forEach(e=>e.remove()); }")
            pg.click(".class-bubble"); pg.wait_for_timeout(700)
            pg.click(".class-stack-item.is-add"); pg.wait_for_timeout(900)
            pg.click("#stage .class-card.is-ifc"); pg.wait_for_timeout(900)
            res = pick_book(pg)
            S.ck("15b", "the book checked: %r, %r" % (res and res["title"], res and res["button"]),
                 res and res["title"] == "Success" and res["result"].startswith("Your IFC PDF is referenced") and res["button"] == "Enroll and get started", res)
            pg.click(".ifc-analyze .ia-actions button")
            wait_for(pg, "()=>window.NOVA_CLASS === 'ifc' && !!document.getElementById('nova-class-greet')", 45)
            g = walk_nova(pg, talk="nova-class-greet")
            r = ev(pg, "()=>({ cls: window.NOVA_CLASS, list: enrolledClasses() })", default={})
            S.ck("15c", "enrolled, Fire Code opens, and its greeting's last Continue (%r) ends it (%s)" % (g["final"], r),
                 r.get("cls") == "ifc" and r.get("list") == ["academy", "ifc"] and g["ended"], [r, g["final"], g["stuck"]])
            S.ck("15d", "no page errors", not pg.errs, pg.errs[:3])
        except Exception as e:
            print("  INFO stopped:", str(e)[:300])
        S.finish()
        ctx.close()

    # ----------------------------------------------------------------------------------------------------------- banner
    if want("banner"):
        S = Sec("\"Fire Code is open to join\": the listed accounts only, once per device", ["16", "16b", "16c", "16d"])
        BANNER = """()=>{ const b=document.getElementById('newclass-banner'); const w=document.querySelector('.class-bubble-wrap');
          return { banner: b ? b.innerText : null, pulse: !!w && w.classList.contains('has-new') }; }"""
        def home_for(acct, code, extra=""):
            c, p = open_page(br, "iphone", init=seed_init(acct, code, extra), seed={"progress": {code: acct}})
            ev(p, "()=>{ homeUnlocksOwed=()=>false; if(!document.querySelector('.screen-home-actual')) showHome(); }")
            return c, p
        try:
            listed = account("Avery Listed", INVITED, 200, 60)
            ctx, pg = home_for(listed, "TEST-INV1")
            seen = wait_for(pg, "()=>{ const b=document.getElementById('newclass-banner'); return b ? true : null; }", 20)
            r = ev(pg, BANNER)
            if r["banner"]:
                pg.click("#newclass-banner"); pg.wait_for_timeout(900)
            cat = ev(pg, "()=>({ catalog: !!document.querySelector('#stage .class-catalog'), ifc: (document.querySelector('#stage .class-card.is-ifc .cc-status')||{}).textContent, pulse: !!document.querySelector('.class-bubble-wrap.has-new') })")
            other = account("Sam Unlisted", "pubgate38404", 200, 60)
            c2, p2 = home_for(other, "TEST-INV2"); p2.wait_for_timeout(9000); r2 = ev(p2, BANNER); e2 = p2.errs[:]; c2.close()
            inifc = account("Lee Listed", INVITED, 200, 60, classes=["academy", "ifc"])
            c3, p3 = home_for(inifc, "TEST-INV3"); p3.wait_for_timeout(9000); r3 = ev(p3, BANNER); e3 = p3.errs[:]; c3.close()
            S.ck("16", "the listed account gets it with the pulse (%s); an unlisted one does not (%s); a listed one already in Fire Code does not (%s)" % (r, r2, r3),
                 bool(seen) and r["banner"] and "Fire Code is open to join" in r["banner"] and r["pulse"] and not r2["banner"] and not r2["pulse"] and not r3["banner"] and not r3["pulse"], [r, r2, r3])
            S.ck("16b", "tapping it opens the class list, Fire Code to enrol in (%s)" % cat, cat["catalog"] and cat["ifc"] == "Enroll", cat)
            G["relaunch"](pg)
            ev(pg, "()=>{ homeUnlocksOwed=()=>false; if(!document.querySelector('.screen-home-actual')) showHome(); }")
            pg.wait_for_timeout(9000)
            again = ev(pg, BANNER)
            S.ck("16c", "once per device: not after the next launch (%s)" % again, r["banner"] and not again["banner"] and not again["pulse"], again)
            S.ck("16d", "no page errors", not pg.errs and not e2 and not e3, [pg.errs[:2], e2[:2], e3[:2]])
            ctx.close()
        except Exception as e:
            print("  INFO stopped:", str(e)[:300])
        S.finish()

    # -------------------------------------------------------------------------------------------------------------- tip
    if want("tip"):
        S = Sec("The class button's tip for an account from before it (once, after What's New)", ["18", "18b", "18c", "18d"])
        try:
            # an account as 383 left it: its tours current then (tourRev 3), Version 10's card not seen yet (intro.seen 6)
            old = account("Taylor Before", "pubgate38407", 900, 300, tourRev=3)
            old.pop("seenClassTip", None)
            init = seed_init(old, "TEST-TIP1").replace("localStorage.setItem('class26e.intro.seen','99');", "localStorage.setItem('class26e.intro.seen','6');")
            ctx, pg = open_page(br, "iphone", init=init, seed={"progress": {"TEST-TIP1": old}})
            seen_states = []
            card = wait_for(pg, "()=>!!document.getElementById('intro-pop')", 25)
            for _ in range(10):
                seen_states.append(ev(pg, TIP)); pg.wait_for_timeout(500)
            under = [s for s in seen_states if s]
            if card:
                pg.click("#intro-pop .intro-go"); pg.wait_for_timeout(300)
            t = wait_for(pg, "()=>{ const x=document.getElementById('tour-text'); return x && x.textContent.length > 20 ? true : null; }", 40)
            pg.wait_for_timeout(900)
            tip = ev(pg, TIP)
            S.ck("18", "What's New first (%s), no tip under it (%s); then one tip on the class button (%r, on it %s), with no banner or card over it" % (bool(card), len(under), tip and tip["text"][:70], tip and tip["onBubble"]),
                 bool(card) and not under and bool(tip) and "class button" in tip["text"] and tip["onBubble"] and not tip["banner"] and not tip["whatsnew"], [card, under[:1], tip])
            if tip: ev(pg, "()=>document.getElementById('tour-next').click()"); pg.wait_for_timeout(600)
            ev(pg, "()=>{ try{ pushToCloud(true); }catch(e){} }"); pg.wait_for_timeout(2500)
            r = ev(pg, "()=>({ seen: store.seenClassTip, rev: store.tourRev, cloud: ((window.__cloud.progress||{})['TEST-TIP1']||{}).seenClassTip, tour: !!document.getElementById('tour-tooltip') })")
            S.ck("18b", "Got it closes it, and the account says it was shown (%s)" % r, r["seen"] is True and r["cloud"] is True and not r["tour"], r)
            G["relaunch"](pg); pg.wait_for_timeout(9000)
            again = ev(pg, "()=>{ const x=document.getElementById('tour-text'); return x ? x.textContent : null; }")
            S.ck("18c", "once per account: not on the next launch (%r)" % again, tip and again is None, again)
            S.ck("18d", "no page errors", not pg.errs, pg.errs[:3])
            ctx.close()
        except Exception as e:
            print("  INFO stopped:", str(e)[:300])
        S.finish()

    # ----------------------------------------------------------------------------------------------------------- switch
    if want("switch"):
        S = Sec("Switching classes, both ways (an iPhone, a disk cache as a phone has, 4x CPU)", ["19", "19b", "20", "21", "22", "22b", "22c", "23", "23b"])
        import functools, http.server, socket, threading, shutil
        # a static server as GitHub Pages answers (max-age=600, Last-Modified -> 304) and a profile on disk, so a reload
        # revalidates the 9MB page rather than fetching it again (an in-memory context's cache will not hold it)
        sroot = ROOT
        if SRC_PATH != os.path.join(ROOT, "index.html"):
            sroot = tempfile.mkdtemp(prefix="b384co-root-")
            for n in os.listdir(ROOT):
                if n != "index.html" and not n.startswith("."): os.symlink(os.path.join(ROOT, n), os.path.join(sroot, n))
            shutil.copy(SRC_PATH, os.path.join(sroot, "index.html"))
        _s = socket.socket(); _s.bind(("127.0.0.1", 0)); SPORT = _s.getsockname()[1]; _s.close()
        class GH(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *a): pass
            def end_headers(self):
                self.send_header("Cache-Control", "max-age=600"); super().end_headers()
        threading.Thread(target=http.server.ThreadingHTTPServer(("127.0.0.1", SPORT), functools.partial(GH, directory=sroot)).serve_forever, daemon=True).start()
        SURL = "http://127.0.0.1:%d/index.html" % SPORT
        # the owner's situation: the academy in Silver (Ranger's colour, its rank held) wearing Void (its three secret flares
        # found); Fire Code's copy from before 384 carrying both, with neither unlocked in Fire Code
        # the owner's own id (public: it keys his board row): the account 383 let switch, so the old build switches too
        sw = account("Riley Switch", "xph5b57jbp5a", 900, 250, classes=["academy", "ifc"], rankFloor=2, avatarChar="voidwalker",
                     theme={"accent": "ranger", "accentAt": 1}, mysteryColorsFound={"red": True, "orange": True, "yellow": True})
        swi = dict(sw); swi.pop("classes"); swi.pop("rankFloor"); swi["mysteryColorsFound"] = {}; swi["lifetime"] = {"points": 50, "answered": 10, "correct": 5}
        sinit = seed_init(sw, "TEST-SWCH", SEEN_IFC + "localStorage.setItem('class26e.greet.ifc','done'); localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.ifc.drill.v1', %s);" % json.dumps(json.dumps(swi)))
        SST = r"""()=>{ const h=document.querySelector('#stage [data-screen="home"]'); const sp=document.getElementById('splashscreen');
          const box=s=>{ const e=document.querySelector(s); if(!e) return null; const r=e.getBoundingClientRect(); return [Math.round(r.left),Math.round(r.top),Math.round(r.width),Math.round(r.height)]; };
          const L=document.getElementById('class-switch-loader'), F=L && L.querySelector('#csl-fill');
          const fx=F ? (getComputedStyle(F).transform.match(/matrix\(([-0-9.e]+)/)||[])[1] : null;
          return { cls: window.NOVA_CLASS, home: !!h, splash: !!sp && getComputedStyle(sp).display!=='none' && +getComputedStyle(sp).opacity>0.02,
            acc: document.documentElement.dataset.accent || 'ink', c1: getComputedStyle(document.documentElement).getPropertyValue('--theme-c1').trim(),
            loader: L ? getComputedStyle(L).getPropertyValue('--csw-c1').trim() : null, fill: fx == null ? null : +fx,
            boxes: { hero: box('#stage .cosmic-hero-wrap'), start: box('#nextbtn'), bubble: box('.class-bubble'), fab: box('.daily-question-fab'), tabs: box('.bottomtabs') },
            banner: (document.getElementById('classback-banner')||{}).innerText || null,
            char: (typeof store!=='undefined' && store) ? store.avatarChar : null, head: (document.querySelector('#bankavatar svg')||{}).outerHTML ? document.querySelector('#bankavatar svg').outerHTML.length : 0 }; }"""
        def rgb(s):
            m = re.match(r"rgba?\(([0-9.]+),\s*([0-9.]+),\s*([0-9.]+)", s or "")
            if m: return tuple(float(x) for x in m.groups())
            m = re.match(r"#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})", (s or "").lower())
            return tuple(int(x, 16) for x in m.groups()) if m else None
        def dist(a, b): return sum((x - y) ** 2 for x, y in zip(a, b)) ** .5 if a and b else 999
        try:
            prof = tempfile.mkdtemp(prefix="b384co-prof-")
            ctx = pw.chromium.launch_persistent_context(prof, executable_path=CHROME, viewport={"width": 440, "height": 956}, device_scale_factor=1,
                                                        has_touch=True, user_agent=G["UA"]["iphone"])
            ctx.add_init_script("window.__cloudSeed = %s;" % json.dumps({"progress": {"TEST-SWCH": sw, "TEST-SWCH__ifc": swi}}))
            ctx.add_init_script(G["FAKE"]); ctx.add_init_script(G["STANDALONE"])
            ctx.add_init_script("(()=>{ try{ if(location.protocol !== 'http:' || sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); " + sinit + " }catch(e){} })()")
            # an in-page log, every 100ms, of the loader (its bar and first colour) and the arriving page's switch colour - kept in
            # sessionStorage across the reload (the old page's timers run while the next page is still coming)
            ctx.add_init_script(r"""(()=>{ if(location.protocol !== 'http:') return;
              const put = o => { try{ const a = JSON.parse(sessionStorage.getItem('__cslog') || '[]'); a.push(o); sessionStorage.setItem('__cslog', JSON.stringify(a.slice(-600))); }catch(e){} };
              setInterval(() => { try{
                const L = document.getElementById('class-switch-loader');
                if(L){ const F = L.querySelector('#csl-fill'); const m = F && getComputedStyle(F).transform.match(/matrix\(([-0-9.e]+)/);
                  put({ t: Date.now(), w: 'old', c1: getComputedStyle(L).getPropertyValue('--csw-c1').trim(), fill: m ? +m[1] : null }); }
                else if(document.documentElement.classList.contains('class-arrive') && document.getElementById('splashscreen'))
                  put({ t: Date.now(), w: 'new', c1: getComputedStyle(document.documentElement).getPropertyValue('--csw-c1').trim() });
              }catch(e){} }, 100); })()""")
            pg = ctx.pages[0] if ctx.pages else ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
            cdp = ctx.new_cdp_session(pg); cdp.send("Network.enable")
            reqs = {}
            cdp.on("Network.requestWillBeSent", lambda p: reqs.__setitem__(p["requestId"], {"url": p["request"]["url"], "t0": time.time()}))
            cdp.on("Network.loadingFinished", lambda p: reqs.get(p["requestId"]) and reqs[p["requestId"]].update({"bytes": p.get("encodedDataLength") or 0}))
            pg.goto(SURL); pg.wait_for_timeout(5000)
            ev(pg, "()=>document.getElementById('splashscreen')?.remove()")
            acad0 = ev(pg, SST)
            # a while on Home (Fire Code's questions are fetched into the cache meanwhile), then a phone's slow connection
            warmed = wait_for(pg, "()=>performance.getEntriesByType('resource').some(e=>/ifc\\/bank\\.js/.test(e.name) && e.responseEnd > 0)", 40)
            cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
            cdp.send("Network.emulateNetworkConditions", {"offline": False, "latency": 2000, "downloadThroughput": 500000 / 8, "uploadThroughput": 500000 / 8})
            runs = {}
            for to in ("ifc", "academy"):
                ev(pg, "()=>{ document.querySelectorAll('.daily-alert,.app-banner').forEach(e=>e.remove()); }")
                pg.click(".class-bubble"); pg.wait_for_timeout(900)
                ev(pg, "()=>sessionStorage.removeItem('__cslog')")
                reqs.clear(); t_tap = time.time(); t_tap_ms = int(t_tap * 1000)
                pg.click(".class-stack-item.is-" + to)
                samples = []; home_at = None
                while time.time() - t_tap < 150:
                    st = ev(pg, SST)
                    if st:
                        st["dt"] = round((time.time() - t_tap) * 1000); samples.append(st)
                        if st["cls"] == to and st["home"] and not st["splash"] and home_at is None: home_at = st["dt"]
                        if home_at is not None and st["dt"] - home_at > 5000: break
                    pg.wait_for_timeout(80)
                after = [s for s in samples if home_at is not None and s["dt"] >= home_at]
                moves = 0
                if after:
                    last = after[-1]["boxes"]
                    for s in after:
                        for k, b in s["boxes"].items():
                            if b and last.get(k): moves = max(moves, max(abs(x - y) for x, y in zip(b, last[k])))
                big = [(r["url"].rsplit("/", 1)[-1][:30], r.get("bytes")) for r in reqs.values() if (r.get("bytes") or 0) > 50000]
                log = ev(pg, "()=>JSON.parse(sessionStorage.getItem('__cslog') || '[]')", default=[]) or []
                for e in log: e["dt"] = e["t"] - t_tap_ms
                runs[to] = {"home": home_at, "moves": moves, "samples": samples, "big": big, "final": samples[-1] if samples else {}, "log": log}
                print("  INFO switch to %s: Home in %.1fs on slow 3G at 4x CPU; big downloads %s" % (to, (home_at or 0) / 1000, big or "none"), flush=True)
                pg.wait_for_timeout(1200)
            fi, fa = runs["ifc"]["final"], runs["academy"]["final"]
            keys = ev(pg, "()=>({ a: localStorage.getItem('class26e.accentshown'), i: localStorage.getItem('class26e.ifc.accentshown'), sa: localStorage.getItem('class26e.statusbar.v1'), si: localStorage.getItem('class26e.ifc.statusbar.v1') })") or {}
            S.ck("19", "each class keeps its own theme: the academy in Silver (%s), Fire Code - which has not unlocked it - in its own default (%s); each remembers its own (%s)" % (acad0.get("acc"), fi.get("acc"), keys),
                 acad0.get("acc") == "ranger" and fi.get("acc") == "ink" and fa.get("acc") == "ranger" and keys.get("a") == "ranger" and keys.get("i") == "ink", [acad0.get("acc"), fi.get("acc"), fa.get("acc"), keys])
            S.ck("19b", "the status bar's colour is each class's own (academy %s, Fire Code %s)" % (keys.get("sa"), keys.get("si")), keys.get("sa") and keys.get("si") and keys.get("sa") != keys.get("si"), keys)
            S.ck("20", "each class keeps its own character: Void in the academy (%s), not in Fire Code, which has not unlocked it (%s)" % (fa.get("char"), fi.get("char")),
                 acad0.get("char") == "voidwalker" and fi.get("char") and fi.get("char") != "voidwalker" and fa.get("char") == "voidwalker", [acad0.get("char"), fi.get("char"), fa.get("char")])
            # the loader starts in the class left's colours and turns to the class opened's
            tint_ok = True; tint_info = {}
            for to, frm, dst in (("ifc", acad0.get("c1"), fi.get("c1")), ("academy", fi.get("c1"), fa.get("c1"))):
                seq = [(e["dt"], e["w"], rgb(e["c1"])) for e in runs[to]["log"] if e.get("c1")] + [(s["dt"], "home", rgb(s["c1"])) for s in runs[to]["samples"] if s["cls"] == to][-1:]
                a, b = rgb(frm), rgb(dst)
                first = seq[0][2] if seq else None
                mids = [x for x in seq if x[2] and dist(x[2], a) > 6 and dist(x[2], b) > 6]
                tint_info[to] = {"from": frm, "to": dst, "first": first, "between": [(t, w) for t, w, _ in mids][:4], "last": seq[-1][2] if seq else None}
                tint_ok = tint_ok and bool(seq) and dist(first, a) < dist(first, b) and dist(seq[-1][2], b) < 6 and len(mids) >= 1 and dist(a, b) > 20
            S.ck("21", "the loader starts in the colours of the class left and turns to the class opened's, through the colours between (%s)" % tint_info, tint_ok, tint_info)
            S.ck("22", "nothing big is downloaded on the way (Fire Code's questions were already in the cache): %s" % ({k: v["big"] for k, v in runs.items()}),
                 bool(warmed) and not runs["ifc"]["big"] and not runs["academy"]["big"], [warmed, runs["ifc"]["big"], runs["academy"]["big"]])
            fills = [(e["dt"], e["fill"]) for e in runs["ifc"]["log"] + runs["academy"]["log"] if e.get("w") == "old" and e.get("fill") is not None]
            late = [f for t, f in fills if t >= 2000]
            S.ck("22b", "while the next page is still coming, the loader's bar keeps moving, past where it used to hold (%s)" % [(t, round(f, 3)) for t, f in fills if t >= 1500][::4][:6],
                 len(late) >= 2 and max(late) > .686 and late[-1] > late[0], fills[-8:])
            S.ck("22c", "each class's Home comes up (to Fire Code %.1fs, to the academy %.1fs) and nothing on it moves after it shows (%spx, %spx)" % (
                 (runs["ifc"]["home"] or 0) / 1000, (runs["academy"]["home"] or 0) / 1000, runs["ifc"]["moves"], runs["academy"]["moves"]),
                 runs["ifc"]["home"] and runs["academy"]["home"] and runs["ifc"]["moves"] <= 2 and runs["academy"]["moves"] <= 2, {k: (v["home"], v["moves"]) for k, v in runs.items()})
            bi = next((s["banner"] for s in runs["ifc"]["samples"] if s.get("banner")), None)
            ba = next((s["banner"] for s in runs["academy"]["samples"] if s.get("banner")), None)
            S.ck("23", "arriving by the class button says so: %r / %r" % ((bi or "")[:60], (ba or "")[:60]),
                 bool(bi) and "Welcome back to Fire Code" in bi and bool(ba) and "Welcome back to the Police Academy" in ba, [bi, ba])
            cdp.send("Network.emulateNetworkConditions", {"offline": False, "latency": 0, "downloadThroughput": -1, "uploadThroughput": -1})
            cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
            pg.goto("about:blank"); pg.wait_for_timeout(300); pg.goto(SURL); pg.wait_for_timeout(7000)
            again = ev(pg, "()=>!!document.getElementById('classback-banner')")
            S.ck("23b", "once per switch: not on a plain relaunch (%s); no page errors (%s)" % (again, errs[:2]), again is False and not errs, [again, errs[:3]])
            ctx.close()
        except Exception as e:
            print("  INFO stopped:", str(e)[:300])
        S.finish()

    # ----------------------------------------------------------------------------------------------------------- finals
    if want("finals"):
        S = Sec("Every class walkthrough ends on its last Continue (phone tap, laptop mouse)", ["17", "17b"])
        results = {}
        try:
            for dev in ("iphone", "desktop"):
                tap = dev == "iphone"
                # the academy: an account joining it (its greeting), an existing account's meeting, a new account's introduction
                acct = account("Morgan Final", "pubgate38405", 50, 20, classes=["academy", "ifc"])
                ctx, pg = open_page(br, dev, init=seed_init(acct, "TEST-FIN1", "localStorage.setItem('class26e.greet.academy','pending');"), seed={"progress": {"TEST-FIN1": acct}})
                ev(pg, "()=>{ homeUnlocksOwed=()=>false; if(!document.querySelector('.screen-home-actual')) showHome(); }")
                wait_for(pg, "()=>!!document.getElementById('nova-class-greet')", 15)
                results[dev + " academy greeting"] = walk_nova(pg, talk="nova-class-greet", tap=tap)
                ev(pg, "()=>{ document.querySelectorAll('.daily-alert,.app-banner').forEach(e=>e.remove()); window.__closed = null; playNovaIntro(r => { window.__closed = r || 'done'; }, { existing: true }); }")
                results[dev + " existing meeting"] = walk_nova(pg, tap=tap)
                # a new account's introduction: a fresh device, from its first line, answered
                ctx.close()
                ctx, pg = open_page(br, dev)
                ev(pg, "()=>{ stage.replaceChildren(); signupInNova = true; playNovaIntro(r => { window.__closed = r || 'done'; signupInNova = false; }, { signup: true }); }")
                results[dev + " new account (academy)"] = walk_nova(pg, tap=tap, name="Final Newacad")
                ctx.close()
                # Fire Code alone, its first half (here) and its second (in Fire Code)
                ctx, pg = open_page(br, dev)
                ev(pg, "()=>{ stage.replaceChildren(); signupPicks = ['ifc']; signupInNova = true; signupPart = 1; playNovaIntro(r => { window.__closed = r || 'done'; signupInNova = false; signupPart = 0; }, { signup: true, part: 1 }); }")
                results[dev + " Fire Code alone, first half"] = walk_nova(pg, tap=tap, name="Final Newifc")
                ctx.close()
                ifcacct = account("Morgan Final", "pubgate38406", 50, 20, classes=["ifc"])
                ctx, pg = open_page(br, dev, init=seed_init(ifcacct, "TEST-FIN2", SEEN_IFC + "localStorage.setItem('class26e.greet.ifc','pending'); localStorage.setItem('class26e.activeclass','ifc');"),
                                    seed={"progress": {"TEST-FIN2": ifcacct}})
                ev(pg, "()=>{ homeUnlocksOwed=()=>false; if(!document.querySelector('.screen-home-actual')) showHome(); }")
                wait_for(pg, "()=>!!document.getElementById('nova-class-greet')", 15)
                results[dev + " Fire Code greeting"] = walk_nova(pg, talk="nova-class-greet", tap=tap)
                ev(pg, "()=>{ document.querySelectorAll('.daily-alert,.app-banner').forEach(e=>e.remove()); playNovaIntro(r => { window.__closed = r || 'done'; }, { signup: true, part: 2 }); }")
                results[dev + " Fire Code alone, second half"] = walk_nova(pg, tap=tap)
                errs = pg.errs[:]
                ctx.close()
                results[dev + " errors"] = errs
            names = [k for k in results if not k.endswith("errors")]
            bad = [k + ": " + str(results[k]["stuck"] or results[k]["final"]) for k in names if not results[k]["ended"] or not results[k]["final"]]
            S.ck("17", "every walkthrough's last Continue ends it - %d of %d (%s)" % (len(names) - len(bad), len(names), "; ".join(bad) or "all"), len(names) == 12 and not bad,
                 {k: (results[k]["final"], results[k]["ended"], results[k]["stuck"]) for k in names})
            S.ck("17b", "no page errors", not results.get("iphone errors") and not results.get("desktop errors"), [results.get("iphone errors"), results.get("desktop errors")])
        except Exception as e:
            print("  INFO stopped:", str(e)[:300])
        S.finish()

    br.close()
print("\nALL PASS" if not fails else "\nFAILED: %d" % len(fails))
sys.exit(1 if fails else 0)
