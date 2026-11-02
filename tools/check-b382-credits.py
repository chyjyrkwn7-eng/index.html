"""Build 382: Settings in colour, Advanced as its own page, and Contributors.
Madison: "Here are two great inspirations for the settings menu, I love how they have color ... I also really like
credits section where it has the contributors. Contributors will be me, (Madison Davis) Cameron Wharton, Alexis
Sauceda, Bryan Darjean."
(1) Every row of Settings (switch rows, list rows, the sync code) has an icon tile in a real colour (not grey: its
    channels differ by 40+), a white glyph in it, the colours differ inside every card and across the screen
    (8+ different), and every row is 44px+.
(2) What the rows did they still do (spied): share, the install walkthrough, the version check, the report screen,
    the release history, a switch changes its setting, the sync code reveals.
(3) Advanced settings opens a page of its own (a back button, a title) with Reset starred questions, Clear analytics
    and Reset as red word rows; Reset still opens the warning; back is Settings.
(4) The Contributors row opens Contributors: the four people, Madison Davis first, each with 1+ contribution row,
    the tab bar keeps Settings' tab lit (Profile, or the Fire Code bar's Settings), back is Settings, a tab tap
    clears the page. The foot of Settings names the four too, Madison first.
(5) No sideways scroll and nothing past the edge on Settings, Advanced and Contributors at 440x956, 518x1125,
    375x667, iPad 834x1194 and a laptop; academy and Fire Code.
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
 ['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.getstarted'].forEach(k=>localStorage.setItem(k,'1'));
 localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.penal256578.seen','1'); %s })()"""
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else info)

def seed(cls):
    d = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]()))
    d.update(publicId="pubtest0382c", novaMet=99, firstName="Casey", seenSettingsTour=True)
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

# every row of Settings, its tile, the tile's colour and glyph colour
TILES = """()=>{
  const S=document.querySelector('#stage .screen-settings'); if(!S) return null;
  const rows=[...S.querySelectorAll('button.settings-row, .settings-card > label.opt, .sync-code-row')].filter(r=>r.offsetParent);
  const rgb=s=>(s.match(/[\\d.]+/g)||[]).slice(0,3).map(Number);
  return rows.map(r=>{
    const t=r.querySelector('.settings-row-icon'); const card=r.closest('.settings-card');
    const title=((r.querySelector('.settings-row-label, .otext, .sync-code-label')||r).firstChild||{}).textContent||'';
    const out={ title: title.trim().slice(0,40), h: Math.round(r.getBoundingClientRect().height), card: [...S.querySelectorAll('.settings-card')].indexOf(card) };
    if(!t){ out.tile=null; return out; }
    const cs=getComputedStyle(t), c=rgb(cs.backgroundColor), svg=t.querySelector('svg');
    out.tile=c; out.chroma=Math.max(...c)-Math.min(...c);
    out.glyph=svg ? getComputedStyle(svg).color : null; out.tw=Math.round(t.getBoundingClientRect().width);
    out.opaque=!/rgba\\([^)]*,\\s*0?\\.\\d+\\)/.test(cs.backgroundColor) && !/transparent/.test(cs.backgroundColor);
    return out; }); }"""
GEOM = """()=>{ const de=document.documentElement; const P=document.querySelector('#stage > .panel, #stage > section, #stage > div');
  const els=[...document.querySelectorAll('#stage .settings-card, #stage .settings-row, #stage label.opt, #stage .settings-nav, #stage .settings-credits-footer')].filter(e=>e.offsetParent).map(e=>e.getBoundingClientRect());
  return { hscroll: de.scrollWidth - innerWidth, past: els.filter(r=>r.right > innerWidth + 1 || r.left < -1).length, n: els.length }; }"""
def tap(pg, label):
    return pg.evaluate("(t)=>{ const b=[...document.querySelectorAll('#stage button')].find(x=>x.offsetParent&&(x.textContent||'').trim().startsWith(t)); if(!b) return false; b.scrollIntoView({block:'center'}); b.click(); return true; }", label)
def settings(pg):
    pg.evaluate("()=>showAppearance()"); pg.wait_for_timeout(1300)

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    for cls in ("academy", "ifc"):
        ctx, pg = page(br, 440, 956, (62, 0, 34, 0), True, cls)
        tag = "[%s]" % cls
        settings(pg)
        rows = pg.evaluate(TILES) or []
        untiled = [r["title"] for r in rows if not r.get("tile")]
        grey = [(r["title"], r["tile"]) for r in rows if r.get("tile") and (r["chroma"] < 40 or not r["opaque"])]
        notwhite = [(r["title"], r["glyph"]) for r in rows if r.get("tile") and r["glyph"] != "rgb(255, 255, 255)"]
        short = [(r["title"], r["h"]) for r in rows if r["h"] < 44]
        chk("%s Settings has its rows (%d)" % (tag, len(rows)), len(rows) >= 14, [r["title"] for r in rows])
        chk("%s every row has an icon tile" % tag, rows and not untiled, untiled)
        chk("%s every tile is a real colour, solid, not grey" % tag, rows and not grey, grey)
        chk("%s every glyph is white" % tag, rows and not notwhite, notwhite)
        chk("%s every row is 44px+" % tag, rows and not short, short)
        bycard = {}
        for r in rows:
            if r.get("tile"): bycard.setdefault(r["card"], []).append(tuple(r["tile"]))
        dup = {k: v for k, v in bycard.items() if len(set(v)) != len(v)}
        distinct = len({tuple(r["tile"]) for r in rows if r.get("tile")})
        chk("%s colours differ inside every card, %d different on the screen" % (tag, distinct), rows and not dup and distinct >= 8, dup)

        # (2) the rows still do what they did
        def fresh(spies):
            pg.evaluate("(src)=>{ window.__hit=[]; (new Function(src))(); showAppearance(); }", spies); pg.wait_for_timeout(900)
        fresh("""window.__realShare = window.__realShare || navigator.share;
          Object.defineProperty(navigator, 'share', { configurable:true, value: d => { __hit.push('share:' + (d && d.url ? 'url' : '')); return Promise.resolve(); } });""")
        tap(pg, "Share this app"); pg.wait_for_timeout(1200)
        chk("%s Share this app opens the share sheet" % tag, "share:url" in pg.evaluate("__hit"), pg.evaluate("__hit"))
        fresh("window.__realInstall = window.__realInstall || handleInstallTap; window.handleInstallTap = () => __hit.push('install');")
        tap(pg, "Add to Home Screen"); pg.wait_for_timeout(400)
        chk("%s Add to Home Screen runs the walkthrough" % tag, "install" in pg.evaluate("__hit"), pg.evaluate("__hit"))
        pg.evaluate("()=>{ window.handleInstallTap = window.__realInstall; }")
        fresh("window.__realFetch = window.__realFetch || window.fetch; window.fetch = function(u){ __hit.push('fetch:' + String(u)); return window.__realFetch.apply(this, arguments); };")
        tap(pg, "Check for update"); pg.wait_for_timeout(1500)
        chk("%s Check for update asks for version.json" % tag, any(h.startswith("fetch:version.json") for h in pg.evaluate("__hit")), pg.evaluate("__hit"))
        pg.evaluate("()=>{ window.fetch = window.__realFetch; }")
        fresh("window.__realBug = window.__realBug || showBugReport; window.showBugReport = () => __hit.push('bug');")
        tap(pg, "Report a bug"); pg.wait_for_timeout(400)
        chk("%s Report a bug opens the report" % tag, "bug" in pg.evaluate("__hit"), pg.evaluate("__hit"))
        pg.evaluate("()=>{ window.showBugReport = window.__realBug; }")
        fresh("window.__realRel = window.__realRel || showReleaseHistory; window.showReleaseHistory = f => __hit.push('rel:' + f);")
        tap(pg, "Version history"); pg.wait_for_timeout(400)
        chk("%s Version history opens the release history" % tag, "rel:settings" in pg.evaluate("__hit"), pg.evaluate("__hit"))
        pg.evaluate("()=>{ window.showReleaseHistory = window.__realRel; }")
        settings(pg)
        sw = pg.evaluate("""async ()=>{ const row=[...document.querySelectorAll('#stage .screen-settings label.opt')].find(r=>/^Reduce motion/.test((r.querySelector('.otext')||r).textContent.trim()));
          if(!row) return null; const was=theme.reduceMotion; row.querySelector('.otext').click(); await new Promise(r=>setTimeout(r,500));
          const now=theme.reduceMotion; row.querySelector('.otext').click(); await new Promise(r=>setTimeout(r,500)); return { was, now, back: theme.reduceMotion }; }""")
        chk("%s a switch row still changes its setting (%s)" % (tag, sw), sw and sw["was"] != sw["now"] and sw["back"] == sw["was"], sw)
        rv = pg.evaluate("""async ()=>{ const r=document.querySelector('#stage .sync-code-row'); if(!r) return null; const a=r.querySelector('.sync-code-value').textContent;
          r.click(); await new Promise(x=>setTimeout(x,300)); const b=r.querySelector('.sync-code-value').textContent; r.click(); return { a, b }; }""")
        chk("%s the sync code still reveals" % tag, rv and rv["a"] != rv["b"] and "•" not in rv["b"], rv)

        # (3) Advanced is a page
        settings(pg)
        tap(pg, "Advanced settings"); pg.wait_for_timeout(1200)
        adv = pg.evaluate("""()=>{ const p=document.querySelector('#stage .screen-advsettings'); if(!p) return null;
          const rows=[...p.querySelectorAll('.settings-row')].map(b=>({ t:b.textContent.trim(), c:getComputedStyle(b).color, h:Math.round(b.getBoundingClientRect().height) }));
          const back=p.querySelector('.settings-nav-back'), bb=back&&back.getBoundingClientRect();
          return { title:(p.querySelector('.settings-nav-title')||{}).textContent, back: bb ? [Math.round(bb.width), Math.round(bb.height)] : null, rows,
                   settingsGone: !document.querySelector('#stage .screen-settings') }; }""")
        def red(c):
            v = [float(x) for x in re.findall(r"[\d.]+", c or "")[:3]]
            if "srgb" in (c or ""): v = [x * 255 for x in v]
            return len(v) == 3 and v[0] > 180 and v[1] < 140 and v[2] < 140
        need = ["Reset starred questions", "Clear analytics", "Reset"]
        have = {r["t"]: r for r in (adv or {}).get("rows", [])}
        chk("%s Advanced settings opens its own page with a back button and its title (%s)" % (tag, adv and adv["title"]),
            adv and adv["title"] and adv["back"] and min(adv["back"]) >= 44 and adv["settingsGone"], adv)
        chk("%s its three resets are red word rows, 44px+" % tag, adv and all(t in have and red(have[t]["c"]) and have[t]["h"] >= 44 for t in need), have)
        pg.evaluate("()=>{ window.__realRW = window.__realRW || showResetWarning; window.__hit=[]; }")
        hit = pg.evaluate("""()=>{ const b=document.getElementById('resetbtn'); if(!b) return null; b.click();
          return !!document.querySelector('#stage .resetwarning-panel'); }""")
        chk("%s Reset still opens the warning" % tag, hit is True, hit)
        settings(pg); tap(pg, "Advanced settings"); pg.wait_for_timeout(1000)
        pg.evaluate("()=>document.querySelector('#stage .settings-nav-back')?.click()"); pg.wait_for_timeout(1300)
        bk = pg.evaluate("()=>({ s: !!document.querySelector('#stage .screen-settings'), a: !!document.querySelector('.screen-advsettings') })")
        chk("%s back from Advanced is Settings" % tag, bk["s"] and not bk["a"], bk)

        # (4) Contributors
        settings(pg)
        litSettings = pg.evaluate("()=>[...document.querySelectorAll('#bottomtabs .bottomtab.active')].filter(b=>b.offsetParent).map(b=>b.id)")
        foot = pg.evaluate("()=>[...document.querySelectorAll('#stage .settings-credits-footer .settings-credits-name')].map(e=>e.textContent.trim())")
        chk("%s the foot of Settings names the four, Madison first (%s)" % (tag, foot), len(foot) == 4 and foot[0] == "Madison Davis", foot)
        opened = tap(pg, "Contributors"); pg.wait_for_timeout(1300)
        cr = pg.evaluate("""()=>{ const p=document.querySelector('#stage .screen-credits'); if(!p) return null;
          const cards=[...p.querySelectorAll('.credits-card')].map(c=>({ name:(c.querySelector('.credits-name')||{}).textContent,
             items:[...c.querySelectorAll('.credits-item')].map(i=>({ t:i.textContent.trim(), h:Math.round(i.getBoundingClientRect().height) })) }));
          const lit=[...document.querySelectorAll('#bottomtabs .bottomtab.active')].filter(b=>b.offsetParent).map(b=>b.id);
          return { title:(p.querySelector('.settings-nav-title')||{}).textContent, intro:(p.querySelector('.credits-intro')||{}).textContent, cards, lit,
                   back: !!p.querySelector('.settings-nav-back') }; }""")
        names = [c["name"] for c in (cr or {}).get("cards", [])]
        chk("%s the Contributors row opens Contributors (%s)" % (tag, cr and cr["title"]), opened and cr and cr["title"] and cr["intro"] and cr["back"], cr)
        chk("%s it lists the four, Madison Davis first (%s)" % (tag, names),
            names[:1] == ["Madison Davis"] and sorted(names) == sorted(["Madison Davis", "Cameron Wharton", "Alexis Sauceda", "Bryan Darjean"]), names)
        chk("%s each has a contribution row or more, 44px+" % tag,
            cr and all(c["items"] and all(i["t"] and i["h"] >= 44 for i in c["items"]) for c in cr["cards"]), cr and cr["cards"])
        chk("%s the tab bar keeps Settings' tab lit (%s, as on Settings %s)" % (tag, cr and cr["lit"], litSettings),
            cr and cr["lit"] and cr["lit"] == litSettings, cr and cr["lit"])
        pg.evaluate("()=>document.querySelector('#stage .settings-nav-back')?.click()"); pg.wait_for_timeout(1300)
        bk = pg.evaluate("()=>({ s: !!document.querySelector('#stage .screen-settings'), c: !!document.querySelector('.screen-credits'), row: !!document.getElementById('settings-contributors') })")
        chk("%s back from Contributors is Settings" % tag, bk["s"] and bk["row"] and not bk["c"], bk)
        tap(pg, "Contributors"); pg.wait_for_timeout(1000)
        pg.evaluate("()=>document.querySelector('#bottomtab-home')?.click()"); pg.wait_for_timeout(1500)
        gone = pg.evaluate("()=>!document.querySelector('.screen-credits')")
        chk("%s a tab tap clears Contributors" % tag, gone, gone)
        ctx.close()

    # (5) sizes
    for label, (w, h, ins, inst), cls in (("iPhone 440", (440, 956, (62, 0, 34, 0), True), "academy"),
                                          ("iPhone 440, Fire Code", (440, 956, (62, 0, 34, 0), True), "ifc"),
                                          ("Pro Max at 85%", (518, 1125, (73, 0, 40, 0), True), "academy"),
                                          ("SE 375", (375, 667, (20, 0, 0, 0), False), "academy"),
                                          ("SE 375, Fire Code", (375, 667, (20, 0, 0, 0), False), "ifc"),
                                          ("iPad 834", (834, 1194, (24, 0, 20, 0), True), "academy"),
                                          ("laptop", (1512, 852, (0, 0, 0, 0), False), "academy")):
        ctx, pg = page(br, w, h, ins, inst, cls)
        res = {}
        settings(pg); res["settings"] = pg.evaluate(GEOM)
        tap(pg, "Advanced settings"); pg.wait_for_timeout(1000); res["advanced"] = pg.evaluate(GEOM)
        settings(pg); tap(pg, "Contributors"); pg.wait_for_timeout(1000); res["contributors"] = pg.evaluate(GEOM)
        good = all(v["hscroll"] <= 0 and v["past"] == 0 and v["n"] > 0 for v in res.values())
        chk("%s: Settings, Advanced and Contributors fit (%s)" % (label, res), good, res)
        ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
