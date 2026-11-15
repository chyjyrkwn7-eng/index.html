#!/usr/bin/env python3
"""Build 384.100: the daily question - a title at the top, and the result after answering rebuilt in the app's current look.
Madison: "The daily question is good but at the very top it needs like a 'daily question' word or something. I also don't like the
box at the bottom after you answer, I don't think it's been updated to the look either. But I also don't like it looks anyways.
Needs to be better. Ensure this is good to go."

Devices, installed: iPhone 17 Pro Max 440x956 (and on its side, 956x440), iPhone SE 375x667, iPad Pro 11" 834x1194 (and on its side);
the Police Academy and Fire Code; a right and a wrong answer to the real daily question (startDailyQuestion, a choice, Submit
answer); a rank theme (Sapphire) and reduce motion on the Pro Max. Everything is read off the page - no label strings:
  T1  THE TITLE: the largest text in the daily question's header row has the run screens' title treatment - the face, size, weight,
      colour and spacing of a results screen's title on the same device (read off a real one-question run's results first) - and
      sits where that one sits (left and top within 1px); below the safe area's line, above everything on the page, and clear of
      the chat button (no overlap).
  T2  THE HEADER HOLDS: answered, with the question scrolled up under the header, the band from under the title to the chat
      button's foot (left of the button and its shadow) is the page's own paper (--paper), solid - nothing of the question shows
      through under the title or beside the button. (The question is checked to be under the band, so this cannot pass empty.)
  B1  THE RESULT IS THE APP'S CARD: every card of the result paints var(--surface-1) as the page resolves it there (a probe), with
      no background image, no border, no shadow and no backdrop filter, and has a results card's radius and padding (a real
      .rs-screen .rs-card on the results screen read in T1).
  B2  IN THE VIEWPORT, THE BUTTON FREE: after the app's own scroll the result is inside the page's width and, where it fits between
      the header band (the title row, the chat button) and the Exit pill, whole there (its foot above the pill); where it is taller
      than that room (a phone on its side) its verdict card is on screen from just under the band. The pill is 44px+ tall, the
      topmost element at five points inside it is the pill (nothing covers it), and a click on it lands on Home.
  R1  RIGHT AND WRONG: the verdict's mark and its word are painted in the question screen's own colours - a right choice's rim on a
      right answer, a wrong pick's rim on a wrong one - and the two states' colours are far apart (a channel distance over 60).
  R2  WHAT IT SAYS: the result holds the answer given (the picked choice's own text) and, on a miss, the right one (the right
      choice's text); its XP figure is the XP booked (DAILY_XP, or 0 on a miss); and, as numbers, the streak after the answer (and
      on a miss the streak it ended), the count answered right (dailyCorrectCount) and the hours to the next one (nextDailyResetMs).
  M1  REDUCE MOTION: on, every part of the result is at full opacity 150ms after Submit, nothing animating.
  L1  ANSWERED ALREADY: opening the daily question again starts no question and puts up the done banner.
  E   no page errors.
Run:  python3 tools/check-b384-dailyq.py [--quick] [--only DEVICE-SUBSTR] [--against REV|DIR]
      (--quick: Pro Max and iPad Pro 11" upright, both classes. --against origin/main must FAIL T1, T2, B1, R1 and R2.)"""
import importlib.util, io, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
QUICK = "--quick" in sys.argv
if QUICK: sys.argv.remove("--quick")
ONLY = None
if "--only" in sys.argv:
    i = sys.argv.index("--only"); ONLY = sys.argv[i + 1]; del sys.argv[i:i + 2]
spec = importlib.util.spec_from_file_location("glitches", os.path.join(HERE, "check-b384-glitches.py"))
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)   # takes --against from sys.argv
from playwright.sync_api import sync_playwright
from PIL import Image
G.DEV.update({
    "promax-land": (956, 440, 956, 440, (0, 62, 21, 62), G.UA_IPHONE, True, True),
    "ipad-land": (1194, 834, 1194, 834, (24, 0, 20, 0), G.UA_IPAD, True, True),
})
chk = G.chk

# a real one-question run to its results: the results screen's title and card, as this build draws them
RESULTS = r"""async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
  document.querySelectorAll('#pushing-update,#intro-pop').forEach(n => n.remove());
  const u = topicsIn(QUESTIONS)[0]; const qi = QUESTIONS.findIndex(q => (q.topic || '').trim() === u);
  cfg.mode = 'drill'; cfg.units = [u]; cfg.source = 'all'; cfg.versions = {};
  beginRun([qi], null);
  for(let t = 0; t < 120 && !document.querySelector('.qpanel .choice'); t++) await wait(100);
  await wait(400);
  const r = correctSlot(order[pos]); [...document.querySelectorAll('.qpanel .choice')].find(c => +c.dataset.index === r).click();
  await wait(900); const n = document.getElementById('nextbtn'); if(n) n.click();
  for(let t = 0; t < 120 && !document.querySelector('#stage .rs-screen .rs-card'); t++) await wait(100);
  await wait(2500);
  const t = document.getElementById('testscopelabel'), c = document.querySelector('#stage .rs-screen .rs-card');
  if(!t || !c) return null;
  const ts = getComputedStyle(t), cs = getComputedStyle(c), tr = t.getBoundingClientRect();
  return { title: { font: ts.fontFamily, size: ts.fontSize, weight: ts.fontWeight, color: ts.color, ls: ts.letterSpacing, left: tr.left, top: tr.top + scrollY },
           card: { radius: cs.borderTopLeftRadius, pad: [cs.paddingTop, cs.paddingRight, cs.paddingBottom, cs.paddingLeft].join(' ') } }; }"""

# the daily question, asked: the header row's title, the chat button, the safe area
ASK = r"""async (o) => { const wait = ms => new Promise(r => setTimeout(r, ms));
  if(o.accent){ theme.accent = o.accent; applyTheme(); }
  theme.reduceMotion = !!o.reduce; applyTheme();
  store.dailyQuestionDate = null; store.dailyCorrectStreak = 3; store.dailyCorrectTotal = 6; saveStore();
  showHome(); await wait(700);
  document.querySelectorAll('#pushing-update,#intro-pop,.daily-alert').forEach(n => n.remove());
  window.scrollTo({ top: 0, behavior: 'instant' });
  startDailyQuestion();
  for(let t = 0; t < 120 && !document.querySelector('.qpanel .choice'); t++) await wait(100);
  await wait(900);
  const vis = e => { const r = e.getBoundingClientRect(), s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden' && +s.opacity > .05 && !/rgba\(0, 0, 0, 0\)|\/ 0\)$/.test(s.color); };
  const top = document.querySelector('.wrap > .top');
  const own = e => [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
  const texts = top ? [...top.querySelectorAll('*')].filter(e => own(e) && vis(e)) : [];
  texts.sort((a, b) => parseFloat(getComputedStyle(b).fontSize) - parseFloat(getComputedStyle(a).fontSize));
  const t = texts[0] || null, chat = document.getElementById('chatdock-btn');
  const R = e => { if(!e) return null; const r = e.getBoundingClientRect(); return { l: r.left, t: r.top, r: r.right, b: r.bottom, w: r.width, h: r.height }; };
  const content = [...document.querySelectorAll('#stage *')].filter(e => vis(e)).map(e => e.getBoundingClientRect().top);
  const ts = t ? getComputedStyle(t) : null;
  return { title: t ? { text: (t.textContent || '').trim().length, font: ts.fontFamily, size: ts.fontSize, weight: ts.fontWeight, color: ts.color, ls: ts.letterSpacing,
             rect: R(t), top: t.getBoundingClientRect().top + scrollY, words: (() => { const g = document.createRange(); g.selectNodeContents(t); const r = g.getBoundingClientRect();
               return { l: r.left, t: r.top, r: r.right, b: r.bottom }; })() } : null,
           chat: chat && vis(chat) ? R(chat) : null, sat: parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--sat')) || 0,
           contentTop: content.length ? Math.min(...content) : null, scrollY: scrollY }; }"""

# answer it (o.right: the right choice, else a wrong one) and submit
ANSWER = r"""async (o) => { const wait = ms => new Promise(r => setTimeout(r, ms));
  const r = correctSlot(order[pos]);
  const c = [...document.querySelectorAll('.qpanel .choice')].find(c => o.right ? +c.dataset.index === r : +c.dataset.index !== r);
  c.click(); await wait(250);
  document.getElementById('dailyq-submitbtn').click();
  if(o.reduce){
    await wait(150);
    const box = document.querySelector('.dailyq-outro');
    if(!box) return { box: false };
    const all = [box, ...box.querySelectorAll('*')];
    return { box: true, dim: all.filter(e => +getComputedStyle(e).opacity < .99).map(e => e.className.toString().slice(0, 40)).slice(0, 4),
             anims: all.reduce((n, e) => n + e.getAnimations().filter(a => a.playState === 'running').length, 0) };
  }
  await wait(1200);
  const ex = document.getElementById('dailyq-exitbtn');
  for(const e of [ex, ...document.querySelectorAll('.dailyq-outro, .dailyq-outro *')]){ if(e) await Promise.all(e.getAnimations().map(a => a.finished.catch(() => {}))); }
  await wait(500);
  return { box: !!document.querySelector('.dailyq-outro') }; }"""

READ_BOX = r"""() => {
  const box = document.querySelector('.dailyq-outro'); if(!box) return null;
  const R = e => { const r = e.getBoundingClientRect(); return { l: r.left, t: r.top, r: r.right, b: r.bottom, w: r.width, h: r.height }; };
  const probe = document.createElement('div'); probe.style.cssText = 'background:var(--surface-1);position:absolute;width:1px;height:1px;';
  box.appendChild(probe); const surface = getComputedStyle(probe).backgroundColor; probe.remove();
  const painted = e => { const s = getComputedStyle(e); return !/^(rgba\(0, 0, 0, 0\)|transparent)$/.test(s.backgroundColor) || s.backgroundImage !== 'none'; };
  const cards = [box, ...box.children].filter(painted).map(e => { const s = getComputedStyle(e);
    return { cls: e.className.toString().slice(0, 48), bg: s.backgroundColor, img: s.backgroundImage.slice(0, 60),
      border: [s.borderTopWidth, s.borderRightWidth, s.borderBottomWidth, s.borderLeftWidth].map(parseFloat).reduce((a, b) => a + b, 0),
      shadow: s.boxShadow, blur: (s.backdropFilter || s.webkitBackdropFilter || 'none'), radius: s.borderTopLeftRadius,
      pad: [s.paddingTop, s.paddingRight, s.paddingBottom, s.paddingLeft].join(' ') }; });
  const head = box.querySelector('.dailyq-outro-head'), mark = box.querySelector('.dailyq-outro-mark');
  const verdict = head ? ([...box.children].find(c => c.contains(head)) || box) : box;
  const ex = document.getElementById('dailyq-exitbtn');
  const exR = ex ? R(ex) : null;
  const pts = exR ? [[.5, .5], [.12, .3], [.88, .3], [.12, .7], [.88, .7]].map(([fx, fy]) => { const x = exR.l + exR.w * fx, y = exR.t + exR.h * fy;
    const t = document.elementFromPoint(x, y); return !!(t && t.closest('#dailyq-exitbtn')); }) : [];
  const right = document.querySelector('.qpanel .choice.is-right'), wrong = document.querySelector('.qpanel .choice.is-wrong-pick');
  const xpEl = box.querySelector('.dailyq-outro-xp');
  const nums = (box.innerText.match(/\d[\d,]*/g) || []).map(s => +s.replace(/,/g, ''));
  const hdr = document.querySelector('.wrap > .top'), chat = document.getElementById('chatdock-btn');
  let foot = hdr ? hdr.getBoundingClientRect().bottom : 0;
  if(chat){ const cr = chat.getBoundingClientRect(); if(cr.height > 0 && cr.top < foot + 96) foot = Math.max(foot, cr.bottom); }
  return { surface, cards, box: R(box), verdict: R(verdict), vw: innerWidth, vh: innerHeight, exit: exR, exitFree: pts, headerFoot: foot,
    markBg: mark ? getComputedStyle(mark).backgroundColor : null, headColor: head ? getComputedStyle(head).color : null,
    rightRim: right ? getComputedStyle(right).borderTopColor : null, wrongRim: wrong ? getComputedStyle(wrong).borderTopColor : null,
    rightText: right ? (right.querySelector('.text') || right).textContent.trim() : null,
    wrongText: wrong ? (wrong.querySelector('.text') || wrong).textContent.trim() : null,
    text: box.innerText.replace(/\s+/g, ' '), xp: xpEl ? xpEl.textContent.trim() : null, dailyXp: DAILY_XP, nums,
    streak: Number(store.dailyCorrectStreak) || 0, count: dailyCorrectCount(), hours: Math.floor(nextDailyResetMs() / 3600000) }; }"""

# put the question under the header band: the stage padded so the page can always scroll that far
UNDER = r"""async () => { const wait = ms => new Promise(r => setTimeout(r, ms));
  const chat = document.getElementById('chatdock-btn'), top = document.querySelector('.wrap > .top'), q = document.querySelector('.qpanel .qtext');
  if(!chat || !top || !q) return null;
  document.getElementById('stage').style.paddingBottom = '1400px';
  const c = chat.getBoundingClientRect(), t = top.getBoundingClientRect();
  const want = (t.bottom + c.bottom) / 2;
  window.scrollTo({ top: scrollY + q.getBoundingClientRect().top - want + 4, behavior: 'instant' }); await wait(350);
  const vis = e => { const s = getComputedStyle(e); return s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity > .05; };
  const tt = [...top.querySelectorAll('*')].filter(e => vis(e) && e.getBoundingClientRect().height > 0 && [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()));
  const tb = Math.max(t.bottom - 1, ...tt.map(e => e.getBoundingClientRect().bottom));
  const c2 = chat.getBoundingClientRect(), qr = q.getBoundingClientRect();
  const region = { x: Math.max(0, tt.length ? Math.min(...tt.map(e => e.getBoundingClientRect().left)) : 16), y: tb + 1, x2: c2.left - 30, y2: c2.bottom - 1 };
  const paper = getComputedStyle(document.documentElement).getPropertyValue('--paper').trim();
  const under = qr.top < region.y2 && qr.bottom > region.y;
  return { region, paper, under, qtop: qr.top }; }"""

def rgb(s):
    m = re.findall(r"[\d.]+", s or "")
    if s and s.startswith("color("):
        return tuple(round(float(x) * 255) for x in m[:3])
    return tuple(round(float(x)) for x in m[:3]) if len(m) >= 3 else None
def hexrgb(h):
    h = (h or "").strip().lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) if len(h) == 6 else None
def dist(a, b):
    return max(abs(x - y) for x, y in zip(a, b)) if a and b else 999
def near_px(a, b, t=1.01):
    return abs(float(str(a).replace("px", "")) - float(str(b).replace("px", ""))) <= t

class Patient:
    """the browser, with a page load allowed three minutes (the machine these run on is shared and often loaded)"""
    def __init__(self, b): self.b = b
    def new_context(self, **kw):
        c = self.b.new_context(**kw); c.set_default_navigation_timeout(180000); c.set_default_timeout(180000); return c

def run(br, dev, cls, accent="", reduce=False, states=("right", "wrong")):
    tag = "%s %s%s%s" % (cls, dev, " " + accent if accent else "", " reduce-motion" if reduce else "")
    pg = G.open_dev(Patient(br), dev, [G.seed_init(cls)], dsf=1)
    pg.wait_for_timeout(500); G.clear_popups(pg)
    ref = pg.evaluate(RESULTS)
    chk("[%s] a real results screen to read the run title and card off" % tag, bool(ref), ref)
    if not ref: pg.ctx.close(); return {}
    seen = {}
    for st in states:
        a = pg.evaluate(ASK, {"accent": accent, "reduce": reduce})
        t, c = a.get("title"), a.get("chat")
        if st == states[0] and not reduce:
            same = t and all(t[k] == ref["title"][k] for k in ("font", "size", "weight", "color", "ls"))
            chk("[%s] T1 the header row's title has the run screens' title treatment (results: %s %s %s)" % (tag, ref["title"]["size"], ref["title"]["weight"], ref["title"]["color"]),
                t and t["text"] > 0 and same, {"daily": t and {k: t[k] for k in ("font", "size", "weight", "color", "ls")}, "results": ref["title"]})
            chk("[%s] T1 ...where the results' title sits (left %.1f / %.1f, top %.1f / %.1f)" % (tag, t["rect"]["l"] if t else -1, ref["title"]["left"], t["top"] if t else -1, ref["title"]["top"]),
                t and near_px(t["rect"]["l"], ref["title"]["left"]) and near_px(t["top"], ref["title"]["top"]), [t, ref["title"]])
            ok_top = t and t["rect"]["t"] >= a["sat"] - .5 and (a["contentTop"] is None or a["contentTop"] >= t["rect"]["b"] - 1)
            chk("[%s] T1 ...below the safe area (%s >= %s), above everything on the page (content from %s)" % (tag, t and round(t["rect"]["t"], 1), a["sat"], a["contentTop"] and round(a["contentTop"], 1)),
                ok_top, a)
            w = t and t["words"]
            ov = w and c and not (w["r"] <= c["l"] or c["r"] <= w["l"] or w["b"] <= c["t"] or c["b"] <= w["t"])
            chk("[%s] T1 ...and its words are not under the chat button (%s px clear)" % (tag, w and c and round(c["l"] - w["r"], 1)), w and c and not ov, [w, c])
        res = pg.evaluate(ANSWER, {"right": st == "right", "reduce": reduce})
        if reduce:
            chk("[%s] M1 %s: the whole result is up 150ms after Submit, nothing animating" % (tag, st),
                res.get("box") and not res.get("dim") and res.get("anims") == 0, res)
            pg.wait_for_timeout(2500)
        b = pg.evaluate(READ_BOX)
        chk("[%s] %s: the result is up" % (tag, st), bool(b), b)
        if not b: continue
        seen[st] = b
        surf = rgb(b["surface"])
        bad = [x for x in b["cards"] if dist(rgb(x["bg"]), surf) > 1 or x["img"] != "none" or x["border"] > 0 or x["shadow"] != "none" or x["blur"] != "none"]
        chk("[%s] B1 %s: %d card(s), each the surface token (%s), no image, border, shadow or blur" % (tag, st, len(b["cards"]), b["surface"]),
            b["cards"] and not bad, bad[:2])
        shape = [x for x in b["cards"] if not (near_px(x["radius"], ref["card"]["radius"], .5) and x["pad"] == ref["card"]["pad"])]
        chk("[%s] B1 %s: ...a results card's radius and padding (%s / %s)" % (tag, st, ref["card"]["radius"], ref["card"]["pad"]),
            b["cards"] and not shape, [(x["radius"], x["pad"]) for x in shape][:2])
        bx, v, ex = b["box"], b["verdict"], b["exit"]
        # the room between the header band (the title row, the chat button) and the pill: a result that fits shows whole, its foot
        # above the pill; one taller than the room (a phone on its side) shows its verdict, from just under the band, and scrolls
        room = (ex["t"] - b["headerFoot"]) if ex else 0
        fits = ex and bx["h"] + 28 <= room
        placed = ex and ((v["t"] >= b["headerFoot"] - 1 and bx["b"] <= ex["t"] + 1) if fits
                         else (b["headerFoot"] - 1 <= v["t"] <= b["headerFoot"] + 24 and (v["h"] > room - 12 or v["b"] <= ex["t"] + 1)))
        chk("[%s] B2 %s: inside the page's width, %s" % (tag, st, "whole between the header and Exit" if fits else "taller than the room (%dpx): its verdict on screen from under the header" % room),
            ex and bx["l"] >= -.5 and bx["r"] <= b["vw"] + .5 and placed,
            {"box": bx, "verdict": v, "exit": ex, "headerFoot": b["headerFoot"], "vw": b["vw"], "vh": b["vh"]})
        chk("[%s] B2 %s: Exit is 44px+ and nothing covers it (%s)" % (tag, st, b["exitFree"]),
            ex and ex["h"] >= 44 and b["exitFree"] and all(b["exitFree"]), [ex, b["exitFree"]])
        rim = b["rightRim"] if st == "right" else b["wrongRim"]
        chk("[%s] R1 %s: the mark and the word in the question screen's %s colour (%s; mark %s, word %s)" % (tag, st, st, rim, b["markBg"], b["headColor"]),
            rim and dist(rgb(b["markBg"]), rgb(rim)) <= 2 and dist(rgb(b["headColor"]), rgb(rim)) <= 2, b)
        given = b["rightText"] if st == "right" else b["wrongText"]
        has = given and given in b["text"] and (st == "right" or (b["rightText"] and b["rightText"] in b["text"]))
        chk("[%s] R2 %s: the answer given%s, in the result" % (tag, st, "" if st == "right" else " and the right one"), has,
            {"given": given, "right": b["rightText"], "text": b["text"][:240]})
        xpn = [int(x) for x in re.findall(r"\d+", (b["xp"] or "").replace(",", ""))]
        want = b["dailyXp"] if st == "right" else 0
        chk("[%s] R2 %s: the XP figure is the XP booked (%s)" % (tag, st, b["xp"]), xpn == [want], [b["xp"], want])
        need = [b["streak"], b["count"]] + ([3] if st == "wrong" else []) + ([b["hours"]] if b["hours"] > 0 else [])
        chk("[%s] R2 %s: the streak, the count answered right and the hours to the next one are in it (%s)" % (tag, st, need),
            all(n in b["nums"] for n in need), {"need": need, "nums": b["nums"]})
        if not reduce:
            u = pg.evaluate(UNDER)
            ok = False; info = u
            if u and u["under"] and u["region"]["x2"] - u["region"]["x"] > 40 and u["region"]["y2"] - u["region"]["y"] > 4:
                r = u["region"]
                img = Image.open(io.BytesIO(pg.screenshot(clip={"x": r["x"], "y": r["y"], "width": r["x2"] - r["x"], "height": r["y2"] - r["y"]}))).convert("RGB")
                paper = hexrgb(u["paper"]) or (18, 22, 27)
                px = list(img.getdata())
                off = [p for p in px if dist(p, paper) > 6]
                ok = len(off) <= len(px) * .003
                info = {"region": r, "paper": u["paper"], "off": len(off), "of": len(px), "worst": max((dist(p, paper) for p in px), default=0)}
            chk("[%s] T2 %s: the question under the header band - solid paper from under the title to the chat button's foot" % (tag, st), ok, info)
            pg.evaluate("()=>{ document.getElementById('stage').style.paddingBottom=''; window.scrollTo({top:0, behavior:'instant'}); }")
    # B2 the way back, and L1 opening it again
    home = pg.evaluate("""async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const ex = document.getElementById('dailyq-exitbtn');
      if(!ex) return { exit: false }; ex.click(); await wait(1600);
      const home = !!document.querySelector('[data-screen="home"]');
      document.querySelectorAll('.daily-alert').forEach(n => n.remove());
      startDailyQuestion(); await wait(900);
      return { exit: true, home, again: !!document.querySelector('.qpanel'), banner: !!document.querySelector('.daily-alert') }; }""")
    chk("[%s] B2 Exit lands on Home" % tag, home.get("exit") and home.get("home"), home)
    chk("[%s] L1 opening it again starts nothing and puts up the done banner" % tag, home.get("home") and not home.get("again") and home.get("banner"), home)
    chk("[%s] E no page errors" % tag, not pg.errs, pg.errs[:3])
    pg.ctx.close()
    return seen

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G.CHROME)
    devs = ["promax", "ipad"] if QUICK else ["promax", "promax-land", "se", "ipad", "ipad-land"]
    if ONLY: devs = [d for d in devs if ONLY in d]
    for cls in ["academy", "ifc"]:
        for dev in devs:
            seen = run(br, dev, cls)
            if "right" in seen and "wrong" in seen:
                a, b = rgb(seen["right"]["markBg"]), rgb(seen["wrong"]["markBg"])
                chk("[%s %s] R1 right and wrong are far apart (%s vs %s)" % (cls, dev, a, b), dist(a, b) > 60, [a, b])
        if not QUICK and not ONLY:
            run(br, "promax", cls, accent="adept", states=("right",))
            run(br, "promax", cls, reduce=True, states=("right", "wrong"))
    br.close()
print("\n%s - %d failed" % ("ALL PASS" if not G.fails else "FAIL", len(G.fails)))
sys.exit(1 if G.fails else 0)
