"""Build 382: Settings as a menu of categories (each its own page), Credits and Support, and Contributors.
Madison: "they all are there own tab where you click and get more information? Why are contributors being shown at the
bottom? All the copyright stuff? That shouldn't be there at the bottom, that should be in another thing towards the
bottom similar to the screenshot how it has a support section" / "Contributors section needs something like this. You
can add Logan Preston" / "made by M. Davis and then the word nova in a nice cool way under it".
(1) The menu: every card group under a grey label (General, Account, App, Credits, Support); category rows only (Sound & Haptics, Study, Motion & Effects, Sync, Leaderboard & Privacy - not in Fire
    Code -, Share & Install), each with a solid, non-grey tile, a chevron, 44px+, colours differing in a card; no switch,
    slider or legal paragraph on it; Credits = Contributors and Legal (words and a chevron, no tile); Support = Report a
    bug, Version history, Terms of Use, Privacy (coloured words, no tile, no chevron); no names at the foot (that is
    Contributors' job), only "Made by Davis" (383: the name plain, small capitals like "Made by") and a NOVA wordmark in
    gradient text, last on the screen.
(2) Every category opens its own page (round back button, title) holding its settings - (384 r8) with NO tile on any row ("when
    you click a section and open it, there are icons within them? But there shouldn't be..": Delta's pages are plain lists; only
    the menu has tiles); a page lights the tab Settings lights; back is the menu.
(3) Every handler still fires (spied): share, install walkthrough, version check, report screen, release history, a
    switch, the sync code reveal; the new switch (Tap sounds) saves to the theme; (383) Study has no Longer pause switch.
(4) Advanced settings opens its page: red word rows, Reset opens the warning.
(5) Legal holds every line of the old foot word for word; Terms of Use and Privacy open.
(6) Contributors (round 3, "Not sure why ours has numbers"): five people, Madison Davis first, Logan Preston there;
    no counts anywhere; each card's first row is the name with a role and no chevron, then its rows; a chevron only
    on a row that opens something - in the academy the chat and the Virtual Room, opened; the foot's five in
    Madison's order; the tab bar lights what Settings lights; back is the menu; a tab tap clears it.
(7) No sideways scroll, nothing past the edge, on the menu and the pages at 440x956, 518x1125, 375x667, iPad 834x1194
    and a laptop; academy and Fire Code.
Run:  python3 tools/check-b382-credits.py   (--against: copy the old index.html over first)"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
from playwright.sync_api import sync_playwright
srv, url = g["serve"]()
BUILD = re.search(r'APP_BUILD\s*=\s*"([^"]+)"', open(os.path.join(HERE, "..", "index.html"), encoding="utf-8").read()).group(1)
INIT = """(()=>{ if(localStorage.getItem('class26e.drill.v1')) return;
 localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-0382');
 ['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card','class26e.getstarted'].forEach(k=>localStorage.setItem(k,'1'));
 localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.penal256578.seen','1'); %s })()"""
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else info)

def seed(cls):
    d = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]()))
    # the Fire Code class runs only for the class owner's account (NOVA_CLASS, build 328)
    d.update(publicId="xph5b57jbp5a" if cls == "ifc" else "pubtest0382c", novaMet=99, firstName="Casey", seenSettingsTour=True)
    extra = ""
    if cls == "ifc":
        extra = ("localStorage.setItem('class26e.activeclass','ifc'); localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc']));"
                 " localStorage.setItem('class26e.ifc.drill.v1', %s);"
                 " ['freshstart','intro.seen','unithold.tip','daily.seen','savecode.asked','getstarted'].forEach(k=>localStorage.setItem('class26e.ifc.'+k,'1'));"
                 " localStorage.setItem('class26e.ifc.frame.ok','go-live-1');" % json.dumps(json.dumps(dict(d, publicId="ifcpub0382c"))))
    return INIT % (json.dumps(json.dumps(d)), extra)

def page(br, w, h, ins, installed, cls="academy"):
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=2)
    if installed: ctx.add_init_script(g["STANDALONE"])
    ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]()))
    pg = ctx.new_page(); body = g["patched"](ins)
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"},
             body=json.dumps({"build": BUILD, "force": True})))
    pg.add_init_script(seed(cls))
    pg.goto(url); pg.wait_for_timeout(3200); pg.evaluate("document.getElementById('splashscreen')?.remove()")
    pg.evaluate("()=>{ try{ homeUnlocksOwed=()=>false; }catch(e){} }")
    return ctx, pg


ROWS = """()=>{
  const S=document.querySelector('#stage .screen-settings, #stage .screen-settings-sub'); if(!S) return null;
  const rgb=s=>(s.match(/[\\d.]+/g)||[]).slice(0,3).map(Number);
  const cards=[...S.querySelectorAll('.settings-card')];
  const rows=[...S.querySelectorAll('button.settings-row, .settings-card > label.opt, .sync-code-row')].filter(r=>r.offsetParent);
  return rows.map(r=>{
    const t=r.querySelector('.settings-row-icon'); const card=r.closest('.settings-card');
    const lab=r.querySelector('.settings-row-label, .otext, .sync-code-label');
    const title=((lab||r).firstChild||{}).textContent||'';
    const cs=getComputedStyle(r);
    const out={ title: title.trim().slice(0,40), h: Math.round(r.getBoundingClientRect().height), card: cards.indexOf(card),
      cat: r.classList.contains('settings-cat'), page: r.dataset.page||'', chev: !!r.querySelector('.settings-row-chev'),
      color: cs.color, cardCls: card ? card.className : '' };
    if(t){ const own=getComputedStyle(t); const ts=/rgba\([^)]*,\s*0\)$|transparent/.test(own.backgroundColor) ? getComputedStyle(t,'::after') : own;   /* (384 r8) the fill can be the tile's ::after (Delta's material: a rim, then the fill) */
      const c=rgb(ts.backgroundColor), svg=t.querySelector('svg');
      out.tile=c; out.chroma=Math.max(...c)-Math.min(...c); out.glyph=svg?getComputedStyle(svg).color:null;
      out.opaque=!/rgba\\([^)]*,\\s*0?\\.\\d+\\)/.test(ts.backgroundColor) && !/transparent/.test(ts.backgroundColor); }
    else out.tile=null;
    return out; }); }"""
MENU = """()=>{ const S=document.querySelector('#stage .screen-settings'); if(!S) return null;
  const txt=S.textContent;
  const foot=S.querySelector('.settings-foot');
  const wm=S.querySelector('.settings-wordmark-text'); const ws=wm?getComputedStyle(wm):null;
  const shown=[...S.children].filter(e=>e.offsetParent);
  return { switches: S.querySelectorAll('label.opt, .box, input[type=range], .nsw').length,
    legal: /not affiliated|All rights reserved|trademark of the International/i.test(txt),
    /* the foot is a signature and the wordmark only: no names grid, no names but the signature's */
    footNames: foot ? [...foot.querySelectorAll('.settings-credits-name, .settings-credits-cell')].length : -1,
    footText: foot ? foot.textContent.replace(/\\s+/g, ' ').trim() : '',
    madeBy: (S.querySelector('.settings-madeby')||{}).textContent||'',
    /* 383: "Don't make Davis look like that" - the name is plain: no gradient, no serif italic, the same small capitals as
       "Made by", a step heavier */
    madeByPlain: (()=>{ const e=S.querySelector('.settings-madeby-name'), b=S.querySelector('.settings-madeby-by'); if(!e || !b) return false;
      const c=getComputedStyle(e), d=getComputedStyle(b);
      return !/gradient/.test(c.backgroundImage) && c.fontStyle === 'normal' && c.textTransform === d.textTransform && c.fontSize === d.fontSize
        && c.fontFamily === d.fontFamily && parseInt(c.fontWeight) > parseInt(d.fontWeight); })(),
    /* every card group on the menu has a grey label straight above it */
    unlabelled: [...S.querySelectorAll(':scope > .settings-card')].filter(c=>{ const p=c.previousElementSibling; return !(p && p.classList.contains('slab') && p.textContent.trim()); }).length,
    cards: S.querySelectorAll(':scope > .settings-card').length,
    word: wm ? wm.textContent.trim() : '',
    wordGrad: ws ? (/gradient/.test(ws.backgroundImage) && (/text/.test(ws.webkitBackgroundClip||'') || /text/.test(ws.backgroundClip||''))) : false,
    footLast: !!foot && foot === shown[shown.length - 1] }; }"""
GEOM = """()=>{ const de=document.documentElement;
  const els=[...document.querySelectorAll('#stage .settings-card, #stage .settings-row, #stage label.opt, #stage .settings-nav, #stage .settings-credits-footer, #stage .settings-foot')].filter(e=>e.offsetParent).map(e=>e.getBoundingClientRect());
  return { hscroll: de.scrollWidth - innerWidth, past: els.filter(r=>r.right > innerWidth + 1 || r.left < -1).length, n: els.length }; }"""
LIT = "()=>[...document.querySelectorAll('#bottomtabs .bottomtab.active')].filter(b=>b.offsetParent).map(b=>b.id)"
def tap(pg, label):
    return pg.evaluate("(t)=>{ const b=[...document.querySelectorAll('#stage button')].find(x=>x.offsetParent&&(x.textContent||'').trim().startsWith(t)); if(!b) return false; b.scrollIntoView({block:'center'}); b.click(); return true; }", label)
def settings(pg):
    pg.evaluate("()=>showAppearance()"); pg.wait_for_timeout(1300)
def chans(c):
    v = [float(x) for x in re.findall(r"[\d.]+", c or "")[:3]]
    if "srgb" in (c or ""): v = [x * 255 for x in v]
    return v
def chroma(c):
    v = chans(c)
    return (max(v) - min(v)) if len(v) == 3 else 0
def red(c):
    v = chans(c)
    return len(v) == 3 and v[0] > 180 and v[1] < 140 and v[2] < 140
PAGES = {"sound": ["Sound effects", "Tap sounds"],
         "study": ["Swipe to next question", "Auto-advance", "Auto-star questions you keep missing"],   # (383: the longer pause is gone)
         "motion": ["Reduce motion", "Skip celebrations and pop-ups"],
         "sync": ["Your sync code"], "rankings": ["Show me in the rankings"], "share": ["Share this app", "Add to Home Screen"],
         "account": [],   # (383) Settings > Account: the name editor and Sign out (no switches)
         "classes": ["Join another class"]}   # (384 r4) the classes you are in, and joining another
# (384) "Cameron Wharton started the idea of this entire app. He made the beta ... He should be second on the list under me"
# (384, round 2) "Robert Morgan can be included in the contributor list" - by surname, after Darjean
# (384) "Add Durrell Kennedy as a contributor as well. He helped with creation of the question bank" - by surname, after Darjean
PEOPLE = ["Madison Davis", "Cameron Wharton", "Bryan Darjean", "Durrell Kennedy", "Alexis Sauceda"]
# the foot of Settings, in Madison's order (round 3): creator, chat, Virtual Room, testing, feedback
FOOT = ["Madison Davis", "Bryan Darjean", "Cameron Wharton", "Alexis Sauceda"]

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    for cls in ("academy", "ifc"):
        ctx, pg = page(br, 440, 956, (62, 0, 34, 0), True, cls)
        tag = "[%s]" % cls
        chk("%s the page is in that class" % tag, pg.evaluate("()=>window.NOVA_CLASS") == cls, pg.evaluate("()=>window.NOVA_CLASS"))
        want = list(PAGES)   # (384 r5: Fire Code keeps a read-only Leaderboard & Privacy page - which class has one)
        # (1) the menu
        settings(pg)
        litSettings = pg.evaluate(LIT)
        rows = pg.evaluate(ROWS) or []
        cats = [r for r in rows if r["cat"]]
        chk("%s the menu's category rows are %s (%s)" % (tag, want, [r["page"] for r in cats]), sorted(r["page"] for r in cats) == sorted(want), cats)
        # (384 r8) a tile need not be a colour any more: Delta's utility card is grey, and so is ours (check-b384-tilematerial (7))
        bad = [(r["title"], r.get("tile"), r["h"]) for r in cats if not (r.get("tile") and r["opaque"] and r["glyph"] == "rgb(255, 255, 255)" and r["chev"] and r["h"] >= 44)]
        chk("%s every category row: a solid tile, a white glyph, a chevron, 44px+" % tag, cats and not bad, bad)
        print("  SKIP %s tile colours differ inside every card  -- superseded: 384 r8 gives each card ONE colour family, as Delta's are (\"Do you see how their grouped up stuff has the same color icons?\"); check-b384-tilematerial (7) holds it" % tag)
        m = pg.evaluate(MENU) or {}
        chk("%s no switch, slider or legal paragraph on the menu (%s)" % (tag, {k: m.get(k) for k in ("switches", "legal")}), m and m["switches"] == 0 and not m["legal"], m)
        cred = [r for r in rows if "settings-credits-card" in r["cardCls"]]
        chk("%s Credits: Contributors and Legal, words and a chevron, no tile (%s)" % (tag, [r["title"] for r in cred]),
            [r["title"] for r in cred] == ["Contributors", "Legal"] and all(r["chev"] and not r["tile"] and r["h"] >= 44 for r in cred), cred)
        sup = [r for r in rows if "settings-support-card" in r["cardCls"]]
        chk("%s Support: coloured words only, no tile, no chevron, 44px+ (%s)" % (tag, [r["title"] for r in sup]),
            [r["title"] for r in sup][:2] == ["Report a bug", "Version history"] and len(sup) >= 3
            and all(not r["chev"] and not r["tile"] and r["h"] >= 44 and chroma(r["color"]) >= 40 for r in sup), sup)
        chk("%s every group on the menu has its label (%s cards, %s without)" % (tag, m.get("cards"), m.get("unlabelled")),
            m.get("cards", 0) >= 5 and m.get("unlabelled") == 0, m)
        chk("%s the foot has no names grid, no contributors' names (%s)" % (tag, m.get("footText")),
            m.get("footNames") == 0 and not any(n.split()[1] in m.get("footText", "") for n in PEOPLE[1:]), m)
        chk("%s it ends on 'Made by Davis' (383: the name plain, in the signature's own capitals) and a NOVA wordmark" % tag,
            m.get("madeBy").replace(" ", "").lower() == "madebydavis" and m.get("madeByPlain") and m.get("word") == "NOVA" and m.get("wordGrad") and m.get("footLast"), m)

        # (2) each category is a page
        for k in want:
            settings(pg)
            opened = pg.evaluate("(k)=>{ const b=document.getElementById('settings-row-'+k); if(!b) return false; b.click(); return true; }", k)
            pg.wait_for_timeout(1000)
            pr = pg.evaluate("""()=>{ const p=document.querySelector('#stage .screen-settings-page'); if(!p) return null;
              return { title:(p.querySelector('.settings-nav-title')||{}).textContent, back: !!p.querySelector('.settings-nav-back'), menuGone: !document.querySelector('#stage .screen-settings') }; }""")
            prow = pg.evaluate(ROWS) or []
            unl = pg.evaluate("""()=>{ const p=document.querySelector('#stage .screen-settings-page'); if(!p) return -1;
              return [...p.querySelectorAll('.settings-card')].filter(c=>{ let e=c.previousElementSibling; while(e && !e.classList.contains('slab')) e=e.previousElementSibling;
                const host=c.parentElement; const lab=e || (host && host.querySelector(':scope > .slab'));
                return !lab; }).length; }""")
            chk("%s %s page: every group has a label (%s without)" % (tag, k, unl), unl == 0, unl)
            titles = [r["title"] for r in prow]
            if k == "sync" and cls == "ifc":
                # Fire Code has no cloud (initFirebase stands down there): its Sync page is the unreachable status
                titles += [t for t in pg.evaluate("()=>[...document.querySelectorAll('#stage .sync-status-row')].length ? ['Your sync code'] : []")]
            need = [] if (cls == "ifc" and k == "rankings") else PAGES[k]   # Fire Code's page is a read-only list of classes, no switch
            chk("%s %s opens its page (%s) with %s, and no row on it carries a tile (384 r8)" % (tag, k, pr and pr["title"], need),
                opened and pr and pr["title"] and pr["back"] and pr["menuGone"] and all(t in titles for t in need)
                and not any(r.get("tile") for r in prow), {"page": pr, "titles": titles, "tiled": [r["title"] for r in prow if r.get("tile")]})
            if k == "sound":
                lit = pg.evaluate(LIT)
                chk("%s a category page lights what Settings lights (%s)" % (tag, lit), lit == litSettings, lit)
        pg.evaluate("()=>document.querySelector('#stage .settings-nav-back')?.click()"); pg.wait_for_timeout(1200)
        chk("%s back from a page is the menu" % tag, pg.evaluate("()=>!!document.querySelector('#stage .screen-settings #settings-row-sound')"))

        # (3) handlers
        def fresh(spies, pagekey=""):
            pg.evaluate("(a)=>{ window.__hit=[]; (new Function(a[0]))(); a[1] ? showAppearance({ page: a[1] }) : showAppearance(); }", [spies, pagekey]); pg.wait_for_timeout(900)
        fresh("""window.__realShare = window.__realShare || navigator.share;
          Object.defineProperty(navigator, 'share', { configurable:true, value: d => { __hit.push('share:' + (d && d.url ? 'url' : '')); return Promise.resolve(); } });""", "share")
        tap(pg, "Share this app"); pg.wait_for_timeout(1200)
        chk("%s Share this app opens the share sheet" % tag, "share:url" in pg.evaluate("__hit"), pg.evaluate("__hit"))
        fresh("window.__realInstall = window.__realInstall || handleInstallTap; window.handleInstallTap = () => __hit.push('install');", "share")
        tap(pg, "Add to Home Screen"); pg.wait_for_timeout(400)
        chk("%s Add to Home Screen runs the walkthrough" % tag, "install" in pg.evaluate("__hit"), pg.evaluate("__hit"))
        pg.evaluate("()=>{ window.handleInstallTap = window.__realInstall; }")
        fresh("window.__realFetch = window.__realFetch || window.fetch; window.fetch = function(u){ __hit.push('fetch:' + String(u)); return window.__realFetch.apply(this, arguments); };")
        tap(pg, "Check for update"); pg.wait_for_timeout(1500)
        up = pg.evaluate("()=>({ hit: __hit, line: [...document.querySelectorAll('#stage .settings-buildline')].map(e=>e.textContent).join('|') })")
        chk("%s Check for update asks for version.json and says so on its line" % tag, any(h.startswith("fetch:version.json") for h in up["hit"]) and "up to date" in up["line"], up)
        pg.evaluate("()=>{ window.fetch = window.__realFetch; }")
        fresh("window.__realBug = window.__realBug || showBugReport; window.showBugReport = () => __hit.push('bug');")
        tap(pg, "Report a bug"); pg.wait_for_timeout(400)
        chk("%s Report a bug opens the report" % tag, "bug" in pg.evaluate("__hit"), pg.evaluate("__hit"))
        pg.evaluate("()=>{ window.showBugReport = window.__realBug; }")
        fresh("window.__realRel = window.__realRel || showReleaseHistory; window.showReleaseHistory = f => __hit.push('rel:' + f);")
        tap(pg, "Version history"); pg.wait_for_timeout(400)
        chk("%s Version history opens the release history from Settings" % tag, "rel:settings" in pg.evaluate("__hit"), pg.evaluate("__hit"))
        pg.evaluate("()=>{ window.showReleaseHistory = window.__realRel; }")
        # (383: "The longer pause setting, we don't need that" - gone from Study; asserted absent below)
        pg.evaluate("()=>showAppearance({ page: 'study' })"); pg.wait_for_timeout(900)
        gone = pg.evaluate("()=>![...document.querySelectorAll('#stage label.opt .otext')].some(t=>/Longer pause/.test(t.textContent))")
        chk("%s Study has no Longer pause switch any more" % tag, gone, gone)
        for pk, title, field in (("motion", "Reduce motion", "reduceMotion"), ("sound", "Tap sounds", "tapSounds")):
            pg.evaluate("(k)=>showAppearance({ page: k })", pk); pg.wait_for_timeout(900)
            r = pg.evaluate("""async (a)=>{ const row=[...document.querySelectorAll('#stage label.opt')].find(r=>((r.querySelector('.otext')||r).textContent||'').trim().startsWith(a[0]));
              if(!row) return null; const was=theme[a[1]]; row.querySelector('.otext').click(); await new Promise(r=>setTimeout(r,500));
              const now=theme[a[1]], saved=store.theme && store.theme[a[1]]; row.querySelector('.otext').click(); await new Promise(r=>setTimeout(r,500));
              return { was, now, saved, back: theme[a[1]] }; }""", [title, field])
            chk("%s %s flips theme.%s and saves it (%s)" % (tag, title, field, r), r and r["was"] != r["now"] and r["saved"] == r["now"] and r["back"] == r["was"], r)
        pg.evaluate("()=>showAppearance({ page: 'sync' })"); pg.wait_for_timeout(900)
        rv = {"a": "x", "b": "fire code: no cloud"} if cls == "ifc" else pg.evaluate("""async ()=>{ const r=document.querySelector('#stage .sync-code-row'); if(!r) return null; const a=r.querySelector('.sync-code-value').textContent;
          r.click(); await new Promise(x=>setTimeout(x,300)); const b=r.querySelector('.sync-code-value').textContent; r.click(); return { a, b }; }""")
        chk("%s the sync code still reveals on its page" % tag, rv and rv["a"] != rv["b"] and "•" not in rv["b"], rv)

        # (4) Advanced
        settings(pg)
        tap(pg, "Advanced settings"); pg.wait_for_timeout(1200)
        adv = pg.evaluate("""()=>{ const p=document.querySelector('#stage .screen-advsettings'); if(!p) return null;
          return { rows:[...p.querySelectorAll('.settings-row')].map(b=>({ t:b.textContent.trim(), c:getComputedStyle(b).color, h:Math.round(b.getBoundingClientRect().height) })) }; }""")
        have = {r["t"]: r for r in (adv or {}).get("rows", [])}
        chk("%s Advanced settings opens its page with three red reset rows" % tag,
            adv and all(t in have and red(have[t]["c"]) and have[t]["h"] >= 44 for t in ("Reset starred questions", "Clear analytics", "Reset")), adv)
        hit = pg.evaluate("()=>{ const b=document.getElementById('resetbtn'); if(!b) return null; b.click(); return !!document.querySelector('#stage .resetwarning-panel'); }")
        chk("%s Reset still opens the warning" % tag, hit is True, hit)

        # (5) Legal, Terms of Use, Privacy
        settings(pg)
        tap(pg, "Legal"); pg.wait_for_timeout(1000)
        lg = pg.evaluate("""()=>{ const p=document.querySelector('#stage .screen-settings-text'); if(!p) return null;
          const want=[...buildLegalNote('settings').querySelectorAll('p')].map(e=>e.textContent);
          const have=[...p.querySelectorAll('.settings-prose p')].map(e=>e.textContent);
          return { title:(p.querySelector('.settings-nav-title')||{}).textContent, all: want.length >= 4 && want.every(t=>have.includes(t)) }; }""")
        chk("%s Legal holds every line of the old foot, word for word" % tag, lg and lg["all"] and lg["title"] == "Legal", lg)
        for t in ("Terms of Use", "Privacy"):
            settings(pg); tap(pg, t); pg.wait_for_timeout(900)
            tp = pg.evaluate("()=>{ const p=document.querySelector('#stage .screen-settings-text'); return p ? { title:(p.querySelector('.settings-nav-title')||{}).textContent, n:p.querySelectorAll('.settings-prose p').length } : null; }")
            chk("%s %s opens its page (%s)" % (tag, t, tp), tp and tp["title"] == t and tp["n"] >= 2, tp)

        # (6) Contributors
        settings(pg)
        opened = tap(pg, "Contributors"); pg.wait_for_timeout(1300)
        cr = pg.evaluate("""()=>{ const p=document.querySelector('#stage .screen-credits'); if(!p) return null;
          const cards=[...p.querySelectorAll('.credits-card')].map(c=>{ const first=c.firstElementChild;
             return { name:(c.querySelector('.credits-name')||{}).textContent, nameFirst: !!first && !!first.querySelector('.credits-name'),
               nameChev: !!first && !!first.querySelector('.settings-row-chev'),
               role:(first && first.querySelector('.credits-role')||{}).textContent,
               items:[...c.children].slice(1).map(i=>({ t:i.textContent.trim(), h:Math.round(i.getBoundingClientRect().height), link: i.tagName==='BUTTON', chev: !!i.querySelector('.settings-row-chev') })) }; });
          /* no counts anywhere: no badge, no pill, no element whose words are only a number */
          const numbers=[...p.querySelectorAll('*')].filter(e=>!e.children.length && /^\\s*\\d+\\s*$/.test(e.textContent||'')).length
             + p.querySelectorAll('.credits-count, .credits-stat, .credits-stats').length;
          return { title:(p.querySelector('.settings-nav-title')||{}).textContent, intro:(p.querySelector('.credits-intro')||{}).textContent, cards, numbers,
                   introNum: /\\d+ contribut/i.test((p.querySelector('.credits-intro')||{}).textContent||''),
                   lit: [...document.querySelectorAll('#bottomtabs .bottomtab.active')].filter(b=>b.offsetParent).map(b=>b.id) }; }""")
        names = [c["name"] for c in (cr or {}).get("cards", [])]
        chk("%s Contributors opens (%s)" % (tag, cr and cr["title"]), opened and cr and cr["title"] == "Contributors" and cr["intro"], cr)
        chk("%s five people, Madison Davis first, (384) Cameron Wharton second, Durrell Kennedy there; (384 r5) Robert Morgan and Logan Preston are not on the list (%s)" % (tag, names), names == PEOPLE, names)
        chk("%s no counts: no badge, no totals, no bare numbers (%s)" % (tag, cr and cr["numbers"]), cr and cr["numbers"] == 0 and not cr["introNum"], cr and cr["numbers"])
        chk("%s each card: the name row first (a role, no chevron), then its rows, 44px+" % tag,
            cr and all(c["nameFirst"] and c["role"] and not c["nameChev"] and c["items"] and all(i["h"] >= 44 for i in c["items"]) for c in cr["cards"]), cr and cr["cards"])
        links = [i for c in (cr or {}).get("cards", []) for i in c["items"] if i["link"]]
        chk("%s a chevron only on a row that opens something (%d linked rows)" % (tag, len(links)),
            cr and all(i["chev"] == i["link"] for c in cr["cards"] for i in c["items"]) and len(links) == (0 if cls == "ifc" else 2), [c["items"] for c in (cr or {}).get("cards", [])])
        if cls != "ifc":
            got = []
            for n in range(len(links)):
                pg.evaluate("()=>showCredits()"); pg.wait_for_timeout(900)
                got.append(pg.evaluate("""async (n)=>{ const b=[...document.querySelectorAll('#stage .screen-credits button.credits-item')][n]; if(!b) return null;
                  b.click(); await new Promise(r=>setTimeout(r,1200));
                  const out = { chat: typeof chatDockOpen !== 'undefined' && chatDockOpen === true, room: !!document.querySelector('#stage .screen-vroom-choice') };
                  try{ if(chatDockOpen) closeChatDock(); }catch(e){} return out; }""", n))
            chk("%s the two linked rows open the chat and the Virtual Room (%s)" % (tag, got),
                len(got) == 2 and sorted([bool(x and x["chat"]) for x in got]) == [False, True] and sorted([bool(x and x["room"]) for x in got]) == [False, True], got)
            pg.wait_for_timeout(600)
            settings(pg); tap(pg, "Contributors"); pg.wait_for_timeout(1300)
        chk("%s the tab bar lights what Settings lights (%s / %s)" % (tag, cr and cr["lit"], litSettings), cr and cr["lit"] and cr["lit"] == litSettings, cr and cr["lit"])
        pg.evaluate("()=>document.querySelector('#stage .settings-nav-back')?.click()"); pg.wait_for_timeout(1300)
        chk("%s back from Contributors is the menu" % tag, pg.evaluate("()=>!!document.getElementById('settings-contributors') && !document.querySelector('.screen-credits')"))
        tap(pg, "Contributors"); pg.wait_for_timeout(1000)
        pg.evaluate("()=>document.querySelector('#bottomtab-home')?.click()"); pg.wait_for_timeout(1500)
        chk("%s a tab tap clears Contributors" % tag, pg.evaluate("()=>!document.querySelector('.screen-credits')"))
        ctx.close()

    # (7) sizes
    for label, (w, h, ins, inst), cls in (("iPhone 440", (440, 956, (62, 0, 34, 0), True), "academy"),
                                          ("iPhone 440, Fire Code", (440, 956, (62, 0, 34, 0), True), "ifc"),
                                          ("Pro Max at 85%", (518, 1125, (73, 0, 40, 0), True), "academy"),
                                          ("SE 375", (375, 667, (20, 0, 0, 0), False), "academy"),
                                          ("SE 375, Fire Code", (375, 667, (20, 0, 0, 0), False), "ifc"),
                                          ("iPad 834", (834, 1194, (24, 0, 20, 0), True), "academy"),
                                          ("laptop", (1512, 852, (0, 0, 0, 0), False), "academy")):
        ctx, pg = page(br, w, h, ins, inst, cls)
        res = {"cls": {"hscroll": 0, "past": 0 if pg.evaluate("()=>window.NOVA_CLASS") == cls else 1, "n": 1}}
        settings(pg); res["menu"] = pg.evaluate(GEOM)
        for k in ("sound", "study", "sync"):
            pg.evaluate("(k)=>{ try{ showAppearance({ page: k }); }catch(e){} }", k); pg.wait_for_timeout(800); res[k] = pg.evaluate(GEOM)
        for fn, key in (("showAdvancedSettings()", "advanced"), ("showSettingsText('legal')", "legal"), ("showCredits()", "contributors")):
            pg.evaluate("()=>{ try{ " + fn + "; }catch(e){} }"); pg.wait_for_timeout(800); res[key] = pg.evaluate(GEOM)
        good = all(v["hscroll"] <= 0 and v["past"] == 0 and v["n"] > 0 for v in res.values())
        chk("%s: the menu and its pages fit (%s)" % (label, {k: (v["hscroll"], v["past"], v["n"]) for k, v in res.items()}), good, res)
        ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
