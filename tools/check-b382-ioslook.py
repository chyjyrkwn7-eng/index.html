"""Build 382: the iOS look app-wide, with the new Settings as the reference.
Madison: "clean clean clean CLEAN iOS Apple look" - Profile, Stats, Customize, Friends, the rank ladder and the
badge case in Settings' family. Every number is read off the page; the reference numbers are read off Settings'
own pushed page (showAppearance({page:'sound'})) in the same run, never typed in here.
(1) A pushed screen (Customize, a Customize page, Friends, Rank, Badges) opens with Settings' nav bar: its first
    button is round, the size of Settings' back button and in the same place; a title on the same line, centred
    on the column, Settings' title size and weight; the button still goes back where it went.
(2) Headings are Settings': no surface behind them, no capitals forced, Settings' size and grey. On Friends and
    Stats each heading sits above its card, not inside it.
(3) Cards are Settings' inset group: its radius, on the surface token (--surface-1 as the card itself resolves it).
    Customize's four rows are ONE group: no gap between them, the corners only on the first and the last.
(4) Rows are 44px+ (Customize's rows and name row, Friends' rows, the back button).
    (The header's small word above the bar is out of sight, so the bar sits at Settings' height.)
(5) No sideways scroll and nothing past the edge at 320x568, and on an iPad (834x1194) every card is no wider than
    Settings' card and centred like it, the back button where Settings' is.
Academy and Fire Code.
Run:  python3 tools/check-b382-ioslook.py   (--against: copy the old index.html over first)"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
from playwright.sync_api import sync_playwright
srv, url = g["serve"]()
BUILD = re.search(r'APP_BUILD\s*=\s*"([^"]+)"', open(os.path.join(HERE, "..", "index.html"), encoding="utf-8").read()).group(1)
INIT = """(()=>{ if(localStorage.getItem('class26e.drill.v1')) return;
 localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-0382');
 ['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.getstarted'].forEach(k=>localStorage.setItem(k,'1'));
 localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.penal256578.seen','1'); })()"""
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else info)

def page(br, w, h, cls):
    d = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]()))
    # Fire Code opens only for the class owner's publicId (a public row id, not a sync code)
    d.update(publicId="xph5b57jbp5a" if cls == "ifc" else "pubtest0382l", novaMet=99, firstName="Casey", seenSettingsTour=True)
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=1)
    ctx.add_init_script(g["STANDALONE"])
    ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]()))
    pg = ctx.new_page(); body = g["patched"]((62, 0, 34, 0) if w < 600 else (24, 0, 20, 0))
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"}, body=json.dumps({"build": BUILD, "force": True})))
    pg.add_init_script(INIT % json.dumps(json.dumps(d)))
    pg.goto(url); pg.wait_for_timeout(3200)
    if cls == "ifc":
        pg.evaluate("()=>{ const d=JSON.parse(localStorage.getItem('class26e.drill.v1')); d.unitPerfects={}; localStorage.setItem('class26e.ifc.drill.v1', JSON.stringify(d));"
                    " localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done'); localStorage.setItem('class26e.activeclass','ifc'); }")
        pg.reload(); pg.wait_for_timeout(3200)
        pg.evaluate("()=>{ ['class26e.ifc.intro.seen','class26e.ifc.unithold.tip','class26e.ifc.daily.seen'].forEach(k=>localStorage.setItem(k,'1')); }")
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); try{ homeUnlocksOwed=()=>false; store.novaMet=99; }catch(e){} document.querySelectorAll('#tour-overlay,#tour-tooltip,.rs-spot,.unlock-card,.nova-talk,#nova-intro').forEach(n=>n.remove()); }")
    return ctx, pg

def go(pg, js, wait=1500):
    pg.evaluate("()=>{ %s }" % js); pg.wait_for_timeout(wait)
    pg.evaluate("()=>{ document.querySelectorAll('#tour-overlay,#tour-tooltip,.rs-spot,.unlock-card,.nova-talk,#nova-intro').forEach(n=>n.remove()); scrollTo(0,0); }")

LIB = r"""
window.__io = {
  r: e => { const b = e.getBoundingClientRect(); return { l: b.left, t: b.top, w: b.width, h: b.height, r: b.right, b: b.bottom, cx: b.left + b.width / 2, cy: b.top + b.height / 2 }; },
  shown: e => !!e && e.getClientRects().length > 0 && getComputedStyle(e).visibility !== 'hidden',
  px: (v, w) => /%$/.test(v) ? parseFloat(v) / 100 * w : parseFloat(v),
  rad: e => { const c = getComputedStyle(e), w = e.getBoundingClientRect().width;
    return ['borderTopLeftRadius','borderTopRightRadius','borderBottomRightRadius','borderBottomLeftRadius'].map(k => Math.round(__io.px(c[k], w) * 10) / 10); },
  tok: e => { const p = document.createElement('i'); p.style.cssText = 'position:absolute;width:1px;height:1px;background-color:var(--surface-1)'; e.appendChild(p);
    const v = getComputedStyle(p).backgroundColor; p.remove(); return v; },
  head: e => { const c = getComputedStyle(e); return { fs: parseFloat(c.fontSize), fw: c.fontWeight, col: c.color, tt: c.textTransform, bg: c.backgroundColor, bi: c.backgroundImage, ls: c.letterSpacing }; },
  panel: () => document.querySelector('#stage > .panel, #stage > section'),
  col: P => { const c = getComputedStyle(P), b = P.getBoundingClientRect(); const l = b.left + parseFloat(c.paddingLeft), r = b.right - parseFloat(c.paddingRight); return { l, r, cx: (l + r) / 2 }; }
};"""

REF = """()=>{ const P=__io.panel(); const b=P.querySelector('.settings-nav-back'), t=P.querySelector('.settings-nav-title'), c=P.querySelector('.settings-card'),
  h=P.querySelector('.slab.motion-summary, .settings-group-head');
  return { back: b && Object.assign(__io.r(b), { pt: b.getBoundingClientRect().top + scrollY }), title: t && Object.assign(__io.head(t), __io.r(t)), card: c && Object.assign({ rad: __io.rad(c) }, __io.r(c)), head: h && __io.head(h), col: __io.col(P) }; }"""

NAV = """()=>{ const P=__io.panel(); if(!P) return null;
  const btn=[...P.querySelectorAll('button')].find(__io.shown); if(!btn) return null;
  const br=__io.r(btn), c=getComputedStyle(btn); br.pt=br.t+scrollY;  /* its place on the page (the road map scrolls to you) */
  const hs=[...P.querySelectorAll('h1, h2, .cal-title, .settings-nav-title')].filter(__io.shown).map(e=>Object.assign(__io.head(e), __io.r(e)));
  const title=hs.find(x=>Math.abs(x.cy-br.cy)<=4) || null;
  return { btn: br, rad: __io.px(c.borderTopLeftRadius, br.w), title, col: __io.col(P) }; }"""

# per screen: headings, cards, a single group of rows, rows to measure, heading-over-card pairs
SPEC = {
  # (383) the name row moved to Settings > Account > Name; Customize is the one group of rows
  "customize": dict(heads=".screen-customize .slab.motion-summary", group=".screen-customize .cz-row",
                    rows=".screen-customize .cz-row"),
  "czpage":    dict(heads=".screen-customize .slab.motion-summary", rows=".screen-customize .settings-nav .back-link"),
  "friends":   dict(heads=".screen-friends .friend-sect > .sect-label", cards=".screen-friends > .friend-sect", rows=".screen-friends .friend-row, .screen-friends .friend-act, .screen-friends .friend-add-input, .screen-friends .settings-nav .back-link",
                    over=(".screen-friends > .friend-sect", ".sect-label")),
  "ranks":     dict(heads=".screen-ranks .ranks-tab > .slab", art=".screen-ranks .rankhero"),
  "badges":    dict(art=".screen-ranks .badges-head"),
  "stats":     dict(heads=".profile-stats-tab > .points-progress-sect .slab", cards=".profile-stats-tab > .points-progress-sect",
                    over=(".profile-stats-tab > .points-progress-sect", ".slab")),
  # Profile's blocks keep the badge case's 22px corner (the case is art); its labels are Settings' headings
  "profile":   dict(heads=".profile-identity-tab .pf-goal > .pf-tasks-kick, .profile-identity-tab .pf-goal > .pf-rewards-kick"),
}
MEASURE = """(s)=>{ const q=sel=>sel?[...document.querySelectorAll(sel)].filter(__io.shown):[];
  const out={};
  out.heads=q(s.heads).map(e=>Object.assign(__io.head(e), { t: (e.textContent||'').trim().slice(0,24) }));
  out.cards=q(s.cards).map(e=>{ const c=getComputedStyle(e); return Object.assign({ rad: __io.rad(e), bg: c.backgroundColor, tok: __io.tok(e), cls: e.className.slice(0,40) }, __io.r(e)); });
  out.art=q(s.art).map(e=>Object.assign({ rad: __io.rad(e), cls: e.className.slice(0,40) }, __io.r(e)));
  const gr=q(s.group); out.group=gr.map(e=>Object.assign({ rad: __io.rad(e) }, __io.r(e)));
  /* a row's height, or its invisible 44px target (::after) where the visible pill is smaller; a field's text size */
  out.rows=q(s.rows).map(e=>{ const a=getComputedStyle(e,'::after'); const ah=a.content!=='none'&&a.position==='absolute'?parseFloat(a.height)||0:0;
    return { h: Math.round(Math.max(e.getBoundingClientRect().height, ah)*10)/10, fs: e.tagName==='INPUT'?parseFloat(getComputedStyle(e).fontSize):null, cls: e.className.slice(0,30) }; });
  if(s.over){ out.over=q(s.over[0]).map(card=>{ const h=[...card.querySelectorAll(s.over[1])].find(__io.shown); if(!h) return null; const a=__io.r(h), b=__io.r(card); return { hb: a.b, ct: b.t, t: (h.textContent||'').trim().slice(0,20) }; }).filter(Boolean); }
  return out; }"""

PAST = """()=>{ const de=document.documentElement; const P=__io.panel();
  const els=[...P.querySelectorAll('.settings-nav, .back-link, .cz-row, .customize-namerow, .friend-sect, .friend-row, .points-progress-sect, .profile-hero, .pf-goal, .rankhero, .badges-head, .slab, .stat-card')].filter(__io.shown).map(__io.r);
  return { hscroll: de.scrollWidth - innerWidth, past: els.filter(r=>r.r > innerWidth + 1 || r.l < -1).length, n: els.length }; }"""
WIDE = """(sel)=>{ const els=[...document.querySelectorAll(sel)].filter(__io.shown).map(__io.r); return els; }"""

PUSHED = [
    ("customize", "Customize", "showProfile('profile'); setTimeout(()=>showCustomize(), 400)", ".screen-profile"),
    ("czpage", "a Customize page", "showCustomize(); setTimeout(()=>showCustomize('character'), 400)", ".screen-customize.cz-summary"),
    ("friends", "Friends", "showProfile('profile'); setTimeout(()=>showFriends(), 400)", ".screen-profile"),
    ("ranks", "Rank", "showProfile('profile'); setTimeout(()=>showRanksScreen('ranks'), 400)", ".screen-profile"),
    ("badges", "Badges", "showProfile('profile'); setTimeout(()=>showRanksScreen('badges'), 400)", ".screen-profile"),
]
TABS = [("stats", "Stats", "showProfile('stats')"), ("profile", "Profile", "showProfile('profile')")]

TITLE_FS = [None]
def near(a, b, tol): return a is not None and b is not None and abs(a - b) <= tol

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    for cls in ("academy", "ifc"):
        tag = "[%s]" % cls
        ctx, pg = page(br, 440, 956, cls)
        pg.add_init_script(LIB); pg.evaluate(LIB)
        chk("%s the page is in its class" % tag, pg.evaluate("()=>window.NOVA_CLASS") == cls, pg.evaluate("()=>window.NOVA_CLASS"))
        go(pg, "showAppearance({page:'sound'})")
        ref = pg.evaluate(REF)
        chk("%s Settings' reference read off its page (back %s, title %s, card radius %s, heading %s)" % (tag,
            ref["back"] and round(ref["back"]["w"]), ref["title"] and ref["title"]["fs"], ref["card"] and ref["card"]["rad"], ref["head"] and ref["head"]["fs"]),
            ref["back"] and ref["title"] and ref["card"] and ref["head"], ref)
        if not (ref["back"] and ref["title"] and ref["card"] and ref["head"]):
            ctx.close(); continue
        RAD = ref["card"]["rad"][0]
        def heads_ok(name, m):
            bad = [x for x in m["heads"] if not (x["bg"] in ("rgba(0, 0, 0, 0)", "transparent") and x["bi"] == "none" and x["tt"] == "none"
                   and near(x["fs"], ref["head"]["fs"], .6) and x["col"] == ref["head"]["col"] and x["fw"] == ref["head"]["fw"])]
            chk("%s %s: %d heading(s), each Settings' (no surface, no forced capitals, %.1fpx, its grey and weight)" % (tag, name, len(m["heads"]), ref["head"]["fs"]),
                m["heads"] and not bad, bad)
        def cards_ok(name, m):
            bad = [x for x in m["cards"] if not (all(near(r, RAD, .6) for r in x["rad"]) and x["bg"] == x["tok"])]
            chk("%s %s: %d card(s) at Settings' %.0fpx radius on the surface token" % (tag, name, len(m["cards"]), RAD), m["cards"] and not bad,
                [(x["cls"], x["rad"], x["bg"], x["tok"]) for x in bad])
        def art_ok(name, m):
            # cards that carry their own art (the hero, the next rank, the ladder's head, the case's head): the radius only
            bad = [x for x in m["art"] if not all(near(r, RAD, .6) for r in x["rad"])]
            chk("%s %s: %d showcase card(s) at Settings' %.0fpx radius, their own art kept" % (tag, name, len(m["art"]), RAD), m["art"] and not bad,
                [(x["cls"], x["rad"]) for x in bad])
        def over_ok(name, m):
            bad = [x for x in m["over"] if x["hb"] > x["ct"] + 1]
            chk("%s %s: every heading sits above its card (%d)" % (tag, name, len(m["over"])), m["over"] and not bad, bad)

        for key, name, js, dest in PUSHED:
            go(pg, js, 2200)
            nav = pg.evaluate(NAV)
            if not nav:
                chk("%s %s: has a nav bar" % (tag, name), False, "no button"); continue
            b, rb, t = nav["btn"], ref["back"], nav["title"]
            round_ = near(b["w"], b["h"], 1) and near(b["w"], rb["w"], 1) and nav["rad"] >= b["w"] / 2 - 1
            chk("%s %s: the first button is Settings' round back button (%.0fx%.0f, radius %.0f; Settings %.0f), where Settings' is (left %.0f vs %.0f, top %.0f vs %.0f)"
                % (tag, name, b["w"], b["h"], nav["rad"], rb["w"], b["l"], rb["l"], b["pt"], rb["pt"]), round_ and near(b["l"], rb["l"], 2) and near(b["pt"], rb["pt"], 2) and b["h"] >= 44, nav)
            chk("%s %s: a title on its line, centred on the column (%s), Settings' size and weight"
                % (tag, name, t and round(t["cx"] - nav["col"]["cx"], 1)),
                t and near(t["cx"], nav["col"]["cx"], 3) and near(t["fs"], ref["title"]["fs"], .6) and t["fw"] == ref["title"]["fw"], t)
            m = pg.evaluate(MEASURE, SPEC[key])
            if SPEC[key].get("heads"): heads_ok(name, m)
            if SPEC[key].get("cards"): cards_ok(name, m)
            if SPEC[key].get("art"): art_ok(name, m)
            if SPEC[key].get("over"): over_ok(name, m)
            if SPEC[key].get("group"):
                gp = m["group"]
                gaps = [round(gp[i + 1]["t"] - gp[i]["b"], 1) for i in range(len(gp) - 1)]
                corners = len(gp) >= 2 and near(gp[0]["rad"][0], RAD, .6) and near(gp[0]["rad"][1], RAD, .6) and gp[0]["rad"][2] == 0 \
                    and near(gp[-1]["rad"][2], RAD, .6) and near(gp[-1]["rad"][3], RAD, .6) and gp[-1]["rad"][0] == 0 \
                    and all(max(x["rad"]) == 0 for x in gp[1:-1])
                chk("%s %s: its %d rows are one inset group (gaps %s; corners on the first and last only)" % (tag, name, len(gp), gaps),
                    len(gp) >= 4 and all(abs(x) <= 1 for x in gaps) and corners, [x["rad"] for x in gp])
            if SPEC[key].get("rows"):
                short = [x for x in m["rows"] if x["h"] < 44 or (x["fs"] is not None and x["fs"] < 16)]
                chk("%s %s: rows are 44px+ (%d)" % (tag, name, len(m["rows"])), not short, short)
            # the button still goes back
            pg.evaluate("()=>{ const P=__io.panel(); const b=[...P.querySelectorAll('button')].find(__io.shown); b.click(); }"); pg.wait_for_timeout(1300)
            chk("%s %s: the round button goes back" % (tag, name), pg.evaluate("(s)=>!!document.querySelector('#stage '+s)", dest), dest)

        # (6) the page title on Profile's segments: the header's own word, as big as the Leaderboard's, naming the picked segment
        if cls == "academy":
            go(pg, "showRankings()", 1800)
            TITLE_FS[0] = pg.evaluate("()=>{ const c=document.getElementById('count'); return c && c.textContent ? parseFloat(getComputedStyle(c).fontSize) : null; }")
        go(pg, "showProfile('profile')", 1800)
        segs = pg.evaluate("()=>[...document.querySelectorAll('#stage > .screen-profile > .navsegment .iconbtn')].filter(__io.shown).length")
        for i in range(max(segs, 1)):
            t = pg.evaluate("""async (i)=>{ const b=[...document.querySelectorAll('#stage > .screen-profile > .navsegment .iconbtn')].filter(__io.shown)[i];
              if(b){ b.click(); await new Promise(r=>setTimeout(r,900)); }
              const c=document.getElementById('count'), a=document.querySelector('#stage > .screen-profile > .navsegment .iconbtn.active');
              const word=(c.textContent||'').trim(), cs=getComputedStyle(c);
              const dup=[...document.querySelectorAll('#stage *')].filter(e=>__io.shown(e)&&e.children.length===0&&(e.textContent||'').trim()===word&&parseFloat(getComputedStyle(e).fontSize)>=20).length;
              return { word, seg: a ? a.textContent.trim() : null, fs: parseFloat(cs.fontSize), fw: cs.fontWeight, shown: __io.shown(c), dup }; }""", i)
            chk("%s Profile segment %d: the big title is the picked segment's name (%s / %s), %.1fpx like the Leaderboard's (%s), no second heading"
                % (tag, i + 1, t["word"], t["seg"], t["fs"], TITLE_FS[0]),
                t["shown"] and t["word"] and t["word"] == t["seg"] and TITLE_FS[0] and near(t["fs"], TITLE_FS[0], .6) and int(t["fw"]) >= 700 and t["dup"] == 0, t)
        if cls == "ifc":
            go(pg, "showProfile('stats')", 1600)
            t = pg.evaluate("()=>{ const c=document.getElementById('count'); return { word: c.textContent.trim(), fs: parseFloat(getComputedStyle(c).fontSize), lit: (document.querySelector('.bottomtab.active')||{}).textContent }; }")
            chk("%s Fire Code's Stats tab: the big title (%s, %.1fpx) names its bar tab (%s)" % (tag, t["word"], t["fs"], (t["lit"] or "").strip()),
                t["word"] and t["word"] in (t["lit"] or "") and TITLE_FS[0] and near(t["fs"], TITLE_FS[0], .6), t)

        for key, name, js in TABS:
            go(pg, js, 1800)
            m = pg.evaluate(MEASURE, SPEC[key])
            heads_ok(name, m)
            if SPEC[key].get("cards"): cards_ok(name, m)
            if SPEC[key].get("art"): art_ok(name, m)
            if SPEC[key].get("over"): over_ok(name, m)
        ctx.close()

        # (5) a 320px phone
        ctx, pg = page(br, 320, 568, cls)
        pg.add_init_script(LIB); pg.evaluate(LIB)
        for key, name, js, _ in PUSHED:
            go(pg, js, 2000); r = pg.evaluate(PAST)
            chk("%s 320px %s: no sideways scroll, nothing past the edge (%d measured)" % (tag, name, r["n"]), r["hscroll"] <= 0 and r["past"] == 0, r)
        for key, name, js in TABS:
            go(pg, js, 1600); r = pg.evaluate(PAST)
            chk("%s 320px %s: no sideways scroll, nothing past the edge (%d measured)" % (tag, name, r["n"]), r["hscroll"] <= 0 and r["past"] == 0, r)
        ctx.close()

        # (5) the iPad: capped and centred like Settings
        ctx, pg = page(br, 834, 1194, cls)
        pg.add_init_script(LIB); pg.evaluate(LIB)
        go(pg, "showAppearance({page:'sound'})"); iref = pg.evaluate(REF)
        CARDS = ".cz-row, .customize-namerow, .screen-friends > .friend-sect, .rankhero, .badges-head, .profile-stats-tab > .points-progress-sect, .profile-identity-tab > .profile-hero, .profile-identity-tab > .pf-goal, .screen-customize .avatarchar-grid"
        for key, name, js, _ in PUSHED + [(k, n, j, None) for k, n, j in TABS]:
            go(pg, js, 2000)
            els = pg.evaluate(WIDE, CARDS)
            wide = [round(e["w"]) for e in els if e["w"] > iref["card"]["w"] + 1]
            off = [round(e["cx"] - iref["card"]["cx"], 1) for e in els if abs(e["cx"] - iref["card"]["cx"]) > 2]
            chk("%s iPad %s: %d card(s) no wider than Settings' (%.0fpx) and centred like it" % (tag, name, len(els), iref["card"]["w"]), els and not wide and not off, {"wide": wide, "off": off})
            if _ is not None:
                nav = pg.evaluate(NAV)
                chk("%s iPad %s: the back button where Settings' is (%.0f vs %.0f)" % (tag, name, nav["btn"]["l"] if nav else -1, iref["back"]["l"]),
                    nav and near(nav["btn"]["l"], iref["back"]["l"], 2) and near(nav["btn"]["w"], iref["back"]["w"], 1), nav)
        ctx.close()
    br.close()
srv.shutdown()
print("\nALL PASS" if ok else "\nSOME CHECKS FAILED")
sys.exit(0 if ok else 1)
