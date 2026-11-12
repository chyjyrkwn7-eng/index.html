#!/usr/bin/env python3
"""Build 384.92: the Leaderboard without the crown, and with lines that mean something.

Madison, on 384.86, circling the crown on first place's medal and then the left ends of the lines between rows 3-6: "No crown. Also, why
are there weird lines? Fix that". Measured on his screenshot: the line under each row started at the name (x~265 of 921) and stopped short
of the card's right edge, and under it a ~1px dark seam ran the full width at every boundary (25-31, nearly the page's 19/21/25, between
rows of 35/37/42: the page showing through where two rows meet on a fractional y, which WebKit antialiases and Chromium does not - so it is
held here by what is UNDER each boundary, not by a picture of the seam). The podium rows' light also repeated into their 1px side border,
a lit line down the card's right edge.

On an iPhone 17 Pro Max (440x956 at 3x) and an iPad Pro 11" (834x1194 at 2x), installed, in BOTH classes (the academy and Fire Code), on
EVERY board each class has (read off the page: rankingBoardsFor()), with eight people on the board like his (the viewer on it, washed):
 (1) NO CROWN: first place's medal is there (a circle, "1"), and nothing sits on it - no element inside the place marker, no ::before or
     ::after with content on it or on the medal, no .lb-crown (or anything named crown) anywhere on the board;
 (2) ONE CARD: the rows touch (each row's top on the one above's bottom, within .5px) and share one left and right edge, and no row has
     a top or bottom border inside the card; and UNDER EVERY BOUNDARY IS THE CARD, NOT THE PAGE: with the rows pulled 4px apart, the
     first pixel row under each row but the last is the list's own cell colour (a plain row's, within 3 levels), and under the last
     row is the page;
 (3) THE LINES: one line (a 1px pseudo-element in a colour you can see) per boundary between two rows - rows-1 of them, each on a
     boundary, none above the first row or under the last, no two within 2px of each other - and every one runs from the card's inner
     left edge to its inner right edge, within 1px;
 (4) SEEN ON SCREEN: on the screenshot, every line on screen is lighter than the row above it near the card's left edge, in the middle
     and near its right edge alike (a line that starts at the name is not there at the left);
 (5) THE SIDES: on every row on screen, the card's outermost pixel column at each side is the row's own colour (the pixel 4px inside it,
     within 6 levels) - no lit line down an edge;
 (6) no page errors.
  python3 tools/check-b384-lbclean.py [--against OLD/index.html]     (origin/main 384.86 must FAIL (1), (2), (3), (4), (5))
  LBCLEAN_CLASSES=ifc runs one class."""
import io, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
from playwright.sync_api import sync_playwright
from PIL import Image
SRC = sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else os.path.join(ROOT, "index.html")
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:600], flush=True)

ME = "pubme000lbc1"
PEOPLE = [("pubaaa000001", "Avery", "detective", 40, 10), (ME, "Casey", "ninja", 27, 10), ("pubaaa000003", "Logan", "wizard", 25, 9),
          ("pubaaa000004", "Sam", "ghost", 10, 0), ("pubaaa000005", "Matt", "grizzly", 5, 0), ("pubaaa000006", "Cody", "ghost", 1, 0),
          ("pubaaa000007", "Dana", "alien", 1, 0), ("pubaaa000008", "Rookie", "ghost", 1, 0)]
WK = g["week_key_now"]()
ROWS = [{"code": p, "pub": p, "publicId": p, "firstName": n, "avatarChar": a, "level": lv, "badges": bd, "hundos": 40 - i * 5, "correct": 3000 - i * 300,
         "week": WK, "weekPoints": 900 - i * 110} for i, (p, n, a, lv, bd) in enumerate(PEOPLE)]
# a Firestore that answers offline: the academy's board in `leaderboard`, Fire Code's in vrooms/lb-ifc-v1
FAKE = """(function(){ var ROWS = %s; var MAP = {}; ROWS.forEach(function(r){ MAP[r.pub] = r; });
  function docRef(id){ var has = id === 'lb-ifc-v1'; var snap = { exists: has, id: id, metadata:{fromCache:false}, data: function(){ return has ? { kind:'board', cls:'ifc', rows: MAP } : null; } };
    return { get: function(){ return Promise.resolve(snap); }, set: function(){ return Promise.resolve(); }, update: function(){ return Promise.resolve(); }, delete: function(){ return Promise.resolve(); },
      collection: function(){ return collRef('sub'); }, onSnapshot: function(a, b){ var next = typeof a === 'function' ? a : b; setTimeout(function(){ next(snap); }, 40); return function(){}; } }; }
  function collRef(name){ var rows = name === 'leaderboard' ? ROWS : [];
    var s = { forEach: function(cb){ rows.forEach(function(r){ cb({ id: r.code, data: function(){ return r; } }); }); }, size: rows.length, docs: [], metadata: { fromCache:false } };
    var c = { doc: function(id){ return docRef(id); }, where: function(){ return c; }, orderBy: function(){ return c; }, limit: function(){ return c; }, get: function(){ return Promise.resolve(s); },
      onSnapshot: function(a, b){ var next = typeof a === 'function' ? a : b; setTimeout(function(){ next(s); }, 60); return function(){}; } }; return c; }
  window.firebase = { apps: [], initializeApp: function(){ this.apps.push({}); }, firestore: Object.assign(function(){ return { collection: collRef, doc: function(p){ return docRef(String(p).split('/').pop()); }, runTransaction: function(){ return Promise.resolve(); }, enablePersistence: function(){ return Promise.resolve(); } }; }, { FieldValue: { serverTimestamp: function(){ return 0; }, delete: function(){ return null; }, increment: function(n){ return n; }, arrayUnion: function(){ return []; }, arrayRemove: function(){ return []; } } }) };
})();""" % json.dumps(ROWS)
DEVS = [("promax", 440, 956, (62, 0, 34, 0), 3), ("ipad11", 834, 1194, (24, 0, 20, 0), 2)]
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1"
def seed(cls):
    d = json.loads(g["SEED"].replace("__WEEK__", WK)); d["publicId"] = ME; d["firstName"] = "Casey"
    d["classes"] = ["academy", "ifc"] if cls == "ifc" else ["academy"]
    return json.dumps(d)

READ = r"""()=>{ const out = { errs: [] }; const rowsEl = document.querySelector('#stage .screen-rankings .rank-rows'); if(!rowsEl) return null;
  const rows = [...rowsEl.children].filter(r => r.classList.contains('rank-row') && !r.classList.contains('rank-row-head'));
  const R = e => e.getBoundingClientRect(), cs = (e, p) => getComputedStyle(e, p || null), px = v => parseFloat(v) || 0;
  const pseudoOn = (e, p) => { const s = cs(e, p); return !(s.content === 'none' || s.content === 'normal' || s.display === 'none'); };
  /* (1) the crown */
  const first = rowsEl.querySelector('.rank-row.lb-place-1 .rank-place') || (rows[0] && rows[0].querySelector('.rank-place'));
  const medal = first && (first.classList.contains('lb-rank-1') ? first : first.querySelector('.lb-rank-1'));
  out.medal = medal ? { text: medal.textContent.trim(), w: Math.round(R(medal).width * 10) / 10, h: Math.round(R(medal).height * 10) / 10, round: px(cs(medal).borderTopLeftRadius) >= R(medal).width / 2 - 1 } : null;
  out.crownKids = first ? first.children.length : -1;
  out.crownPseudo = first ? [first, medal].filter(Boolean).flatMap(e => ['::before', '::after'].filter(p => pseudoOn(e, p))) : ['no marker'];
  out.crownNamed = document.querySelectorAll('#stage .screen-rankings .lb-crown, #stage .screen-rankings [class*="crown"]').length;
  /* (2) one card */
  out.n = rows.length;
  out.rows = rows.map(r => { const b = R(r), s = cs(r); return { t: b.top, b: b.bottom, l: b.left, r: b.right, il: b.left + px(s.borderLeftWidth), ir: b.right - px(s.borderRightWidth),
    bt: px(s.borderTopWidth), bb: px(s.borderBottomWidth), me: r.classList.contains('lb-row-me'), pod: /rank-podium-[123]/.test(r.className) }; });
  /* (3) every thin line any row draws */
  out.lines = [];
  rows.forEach((r, i) => { const b = R(r), s = cs(r);
    for(const p of ['::before', '::after']){ if(!pseudoOn(r, p)) continue; const q = cs(r, p); if(q.position !== 'absolute') continue;
      const h = px(q.height), w = px(q.width); if(!(h > 0 && h <= 1.6 && w > 20)) continue;
      const bg = q.backgroundColor; let al = 1, m = /rgba\([^)]*,\s*([\d.]+)\)/.exec(bg); if(m) al = +m[1]; else { m = /color\([^)]*\/\s*([\d.]+)\)/.exec(bg); if(m) al = +m[1]; }
      if(!(al > .03) && q.backgroundImage === 'none') continue;
      const x0 = b.left + px(s.borderLeftWidth) + px(q.left), y0 = q.top !== 'auto' && Math.abs(px(q.top)) < 2 ? b.top + px(s.borderTopWidth) + px(q.top) : b.bottom - px(s.borderBottomWidth) - px(q.bottom) - h;
      out.lines.push({ row: i, pe: p, x0, x1: x0 + w, y0, y1: y0 + h, alpha: al }); } });
  const tb = document.querySelector('.bottomtabs'); out.tabTop = tb && R(tb).height ? R(tb).top : innerHeight;
  const top = document.querySelector('.wrap > .top'); out.headBottom = top ? R(top).bottom : 0;
  return out; }"""

# anything that lands over the board while it is measured (a challenge's unlock card arrives on its own a few seconds in), with its dim
CLEAR = """()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click());
  document.querySelectorAll('.rs-spot,.unlock-card,.week-recap,.nova-say,.daily-alert,.toast').forEach(n=>n.remove()); }"""
def lum(p): return (p[0] * 299 + p[1] * 587 + p[2] * 114) / 1000

def measure(br, raw, dev, cls, mine):
    dn, W, H, ins, dpr = dev
    ctx = br.new_context(viewport={"width": W, "height": H}, device_scale_factor=dpr, has_touch=True, is_mobile=True, user_agent=UA)
    ctx.add_init_script(g["STANDALONE"]); ctx.add_init_script(FAKE)
    ctx.add_init_script("try{ if(!localStorage.getItem('class26e.drill.v1')){ localStorage.setItem('class26e.freshstart','1'); localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-LBCL');"
                        "['class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card','class26e.getstarted','class26e.penal256578.seen','class26e.penal55124.seen','class26e.penal124256.seen'].forEach(k=>localStorage.setItem(k,'9'));"
                        "localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.weekrecap.v1','9999-12-31'); localStorage.setItem('class26e.a2hs','1790500000000'); %s } }catch(e){}"
                        % (json.dumps(seed(cls)), "localStorage.setItem('class26e.activeclass','ifc');" if cls == "ifc" else ""))
    pg = ctx.new_page(); errs = []
    if mine: pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    t, r, b, l = ins; v = {"top": f"{t}px", "right": f"{r}px", "bottom": f"{b}px", "left": f"{l}px"}
    body = g["INSET_RE"].sub(lambda m: v[m.group(1)], raw)
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    # version.json says the build under test is current, so an --against build is not pushed to reload into the repo's
    bm = re.search(r'const APP_BUILD = "([^"]+)"', raw); vj = json.dumps({"build": bm.group(1) if bm else "", "note": "", "frameId": "", "force": True})
    pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"}, body=vj))
    pg.goto(URL); pg.wait_for_timeout(4500)
    pg.evaluate("document.getElementById('splashscreen')?.remove()")
    pg.evaluate("()=>{ try{ homeUnlocksOwed=()=>false; }catch(e){} showHome(); }"); pg.wait_for_timeout(1000)
    got = {"cls": pg.evaluate("()=>window.NOVA_CLASS"), "boards": {}}
    keys = pg.evaluate("()=>rankingBoardsFor().map(b=>b.key)")
    for k in keys:
        pg.evaluate("(k)=>{ store.seenRewardsTour = true; showRankings(k); }", k)
        # a challenge's unlock card (an .invite-overlay sheet) can arrive on its own a few seconds in: kept out of the pictures, not removed
        pg.evaluate("()=>{ if(!document.getElementById('lbclean-quiet')){ const st=document.createElement('style'); st.id='lbclean-quiet'; st.textContent='.invite-overlay{display:none !important}'; document.body.appendChild(st); } }")
        pg.wait_for_function("()=>document.querySelectorAll('#stage .rank-rows > .rank-row[data-pub]').length >= 8", timeout=15000)
        pg.wait_for_timeout(1500)
        pg.evaluate(CLEAR); pg.evaluate("()=>window.scrollTo({top:0, behavior:'instant'})")
        pg.wait_for_timeout(700)
        rd = pg.evaluate(READ)
        # only the band between the header and the tab bar (a whole 3x page is a lot to ask of a loaded sandbox, and nothing else is read)
        y0c = max(0, int(rd["headBottom"])); CLIP = {"x": 0, "y": y0c, "width": W, "height": max(10, min(H, rd["tabTop"]) - y0c)}
        for attempt in range(4):   # a loaded sandbox sometimes refuses a capture; the page is still and a second ask is the same picture
            try: im = Image.open(io.BytesIO(pg.screenshot(clip=CLIP))).convert("RGB"); break
            except Exception:
                if attempt == 3: raise
                pg.wait_for_timeout(1500)
        Q = lambda ix, y: im.getpixel((min(im.width - 1, max(0, ix)), min(im.height - 1, max(0, int((y - y0c) * dpr)))))   # a device pixel column
        P = lambda x, y: Q(int(x * dpr), y)
        vis = lambda y: rd["headBottom"] + 2 < y < rd["tabTop"] - 4
        # (4) every line on screen, lighter than the row above it near the left edge, in the middle and near the right
        seen = []
        if rd["rows"]:
            il, ir = max(x["il"] for x in rd["rows"]), min(x["ir"] for x in rd["rows"])
            for ln in rd["lines"]:
                y = (ln["y0"] + ln["y1"]) / 2
                if not vis(y): continue
                d = [round(lum(P(x, y)) - lum(P(x, ln["y0"] - 3)), 1) for x in (il + 2, (il + ir) / 2, ir - 2)]
                seen.append({"row": ln["row"], "d": d})
        # (5) the outermost pixel column at each side is the row's own colour
        sides = []
        for i, x in enumerate(rd["rows"]):
            y = (x["t"] + x["b"]) / 2
            if not vis(y): continue
            import math
            el, er = math.ceil(x["l"] * dpr - .01), math.floor(x["r"] * dpr + .01) - 1   # the row's first and last device pixel columns
            dl = max(abs(a - c) for a, c in zip(Q(el, y), P(x["l"] + 4, y))); dr = max(abs(a - c) for a, c in zip(Q(er, y), P(x["r"] - 4, y)))
            sides.append({"row": i, "dl": dl, "dr": dr})
        rd["seen"], rd["sides"] = seen, sides
        # (2) under each boundary: the rows pulled 4px apart for one picture, then put back
        pg.evaluate("()=>document.querySelectorAll('#stage .rank-rows > .rank-row:not(.rank-row-head)').forEach(r=>r.style.setProperty('margin-bottom','4px','important'))")
        pg.evaluate(CLEAR); pg.wait_for_timeout(250)
        apart = pg.evaluate("""()=>[...document.querySelectorAll('#stage .rank-rows > .rank-row:not(.rank-row-head)')].map(r=>{ const b=r.getBoundingClientRect(), s=getComputedStyle(r);
          return { b: b.bottom, mid: (b.top + b.bottom) / 2, il: b.left + parseFloat(s.borderLeftWidth), x: (b.left + b.right) / 2, plain: !r.classList.contains('lb-row-me') && !/rank-podium-[123]/.test(r.className) }; })""")
        for attempt in range(4):
            try: im2 = Image.open(io.BytesIO(pg.screenshot(clip=CLIP))).convert("RGB"); break
            except Exception:
                if attempt == 3: raise
                pg.wait_for_timeout(1500)
        pg.evaluate("()=>document.querySelectorAll('#stage .rank-rows > .rank-row').forEach(r=>r.style.removeProperty('margin-bottom'))")
        if os.environ.get("LBCLEAN_SHOTS"):
            os.makedirs(os.environ["LBCLEAN_SHOTS"], exist_ok=True)
            im.save(os.path.join(os.environ["LBCLEAN_SHOTS"], "%s-%s-%s.png" % (dn, cls, k))); im2.save(os.path.join(os.environ["LBCLEAN_SHOTS"], "%s-%s-%s-apart.png" % (dn, cls, k)))
        Q2 = lambda x, y: im2.getpixel((min(im2.width - 1, max(0, int(x * dpr))), min(im2.height - 1, max(0, int((y - y0c) * dpr)))))
        ref = next((Q2(a["il"] + 3, a["mid"]) for a in apart if a["plain"] and vis(a["mid"])), None)
        under = []
        for i, a in enumerate(apart):
            if not vis(a["b"] + 4) or ref is None: continue
            # walk down the column from 2.5px inside the row's bottom: past the row's own colour and then its line (lighter), and read the
            # first device pixel after them - what lies under the boundary. (Chromium snaps a row's edge to a whole CSS pixel, so the
            # boundary is found in the picture, not computed from the fractional layout.)
            ix = int((a["x"] - 40) * dpr); y0 = int((a["b"] - 2.5 - y0c) * dpr); y1 = y0 + int(5 * dpr)
            G2 = lambda iy: im2.getpixel((min(im2.width - 1, ix), min(im2.height - 1, iy)))
            cell = G2(y0); iy = y0
            while iy < y1 and max(abs(c - e) for c, e in zip(G2(iy), cell)) <= 3: iy += 1      # the row
            while iy < y1 and lum(G2(iy)) > lum(cell) + 4: iy += 1                              # its line, if it has one
            p1 = G2(iy); page = Q2(a["x"] - 40, a["b"] + 3)
            under.append({"row": i, "px": p1, "ref": ref, "last": i == len(apart) - 1, "d": max(abs(c - e) for c, e in zip(p1, ref)), "page": max(abs(c - e) for c, e in zip(p1, page))})
        rd["under"] = under
        got["boards"][k] = rd
    got["errs"] = errs
    ctx.close()
    return got

srv, URL = g["serve"]()
RAW = io.open(SRC, encoding="utf-8").read()
with sync_playwright() as pw:
    errs_all = []
    if True:
        for dev in DEVS:
            for cls in os.environ.get("LBCLEAN_CLASSES", "academy,ifc").split(","):
                # a browser of its own for each device and class: one browser through all four crashed its page under the sandbox's load
                br = pw.chromium.launch(executable_path=g["CHROME"])
                try: got = measure(br, RAW, dev, cls, True)
                except Exception as e:
                    chk("%s %s: measured (%s)" % (dev[0], cls, str(e).splitlines()[0][:160]), False); continue
                finally: br.close()
                errs_all += got["errs"]
                tag = "%s %s" % (dev[0], cls)
                chk("%s: the page is that class (%s), with its boards %s" % (tag, got["cls"], list(got["boards"])), got["cls"] == cls and len(got["boards"]) >= 1, got["cls"])
                for k, rd in got["boards"].items():
                    t = "%s %s" % (tag, k)
                    if not rd: chk(t + ": the board is up", False); continue
                    md = rd["medal"]
                    chk("(1) %s: first place's medal is there (%s) and wears nothing - children %d, pseudo %s, crowns %d" % (t, md, rd["crownKids"], rd["crownPseudo"], rd["crownNamed"]),
                        md and md["text"] == "1" and md["round"] and abs(md["w"] - md["h"]) <= 1 and rd["crownKids"] == 0 and not rd["crownPseudo"] and rd["crownNamed"] == 0, rd)
                    rs = rd["rows"]
                    gaps = [round(b["t"] - a["b"], 2) for a, b in zip(rs, rs[1:])]
                    edges = sorted(set((round(x["il"], 1), round(x["ir"], 1)) for x in rs))
                    inner = [(i, "top", x["bt"]) for i, x in enumerate(rs) if i > 0 and x["bt"] > 0] + [(i, "bottom", x["bb"]) for i, x in enumerate(rs) if i < len(rs) - 1 and x["bb"] > 0]
                    un = rd.get("under") or []; mid = [u for u in un if not u["last"]]; bad = [u for u in mid if u["d"] > 3]; last = [u for u in un if u["last"]]
                    chk("(2) %s: %d rows are one card - gaps %s, inner edges %s, borders inside %s; under %d boundaries the card (worst %s off the cell), under the last the page (%s)"
                        % (t, len(rs), sorted(set(gaps)), edges, inner, len(mid), max([u["d"] for u in mid] or [None]), [u["page"] for u in last]),
                        len(rs) >= 8 and all(abs(x) <= .5 for x in gaps) and len(edges) == 1 and not inner and len(mid) >= 4 and not bad
                        and all(u["page"] <= 3 for u in last), {"bad": bad[:3], "last": last})
                    L = rd["lines"]
                    il, ir = edges[0] if edges else (0, 0)
                    bounds = [x["b"] for x in rs[:-1]]
                    on = [ln for ln in L if any(abs(ln["y1"] - y) <= 1 for y in bounds)]
                    outer = [ln for ln in L if abs(ln["y0"] - rs[0]["t"]) <= 1.5 or abs(ln["y1"] - rs[-1]["b"]) <= 1.5]
                    ys = sorted(ln["y0"] for ln in L); close = [(a, b) for a, b in zip(ys, ys[1:]) if b - a < 2]
                    span = sorted(set((round(ln["x0"] - il, 1), round(ir - ln["x1"], 1)) for ln in L))
                    chk("(3) %s: %d lines for %d boundaries, all on one, none on the card's outer edges (%d), none doubled (%s); each from the inner left to the inner right (off by %s)"
                        % (t, len(L), len(bounds), len(outer), close, span),
                        len(L) == len(bounds) and len(on) == len(L) and not outer and not close and span and all(abs(a) <= 1 and abs(b) <= 1 for a, b in span), L[:3])
                    s = rd["seen"]; faint = [x for x in s if min(x["d"]) < 2]
                    chk("(4) %s: on screen, all %d lines show at the left, middle and right (lighter by %s)" % (t, len(s), [x["d"] for x in s][:4]), len(s) >= 4 and not faint, faint[:4])
                    sd = rd["sides"]; lit = [x for x in sd if x["dl"] > 6 or x["dr"] > 6]
                    chk("(5) %s: on screen, all %d rows' side columns are the row's own colour (worst %s)" % (t, len(sd), max([max(x["dl"], x["dr"]) for x in sd] or [None])), len(sd) >= 5 and not lit, lit[:4])
chk("(6) no page errors (%d)" % len(errs_all), not errs_all, errs_all[:3])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
