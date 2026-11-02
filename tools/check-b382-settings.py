"""Build 382: Report a bug is just the report, and the bottom of Settings is rows.
Madison: "Ensure to remove the stuff from report a bug so it's not there anymore." and "I really dislike this part
of settings, please get all these buttons and things looking better".
(1) Report a bug carries no diagnostics controls (tab speed / tab timings / Leaderboard speed / drag test): the
    form's only button is the send.
(2) Share this app, Add to Home Screen, Check for update, Report a bug, Version history and Advanced settings are
    each a full-width row of its card, 44px+, with a label; all but Support's two word rows (Report a bug, Version
    history) with an icon. Since Settings became a menu (382), Share this app and Add to Home Screen are on the Share &
    Install page; the rest are on the menu.
(3) Every one still does what it did (spied): share, the install walkthrough, the version check, the report screen,
    the release history, Advanced opening (its own page since the colour redesign).
(4) No horizontal overflow, and no row past the screen edge, on iPhone 440x956, Pro Max at 85% 518x1125, SE 375x667,
    iPad 834x1194 and a laptop, in the academy and in Fire Code.
Run:  python3 tools/check-b382-settings.py   (--against: copy the old index.html over first)"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
from playwright.sync_api import sync_playwright
srv, url = g["serve"]()
OWNER = "xph5b57jbp5a"
import re
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
    d.update(publicId=OWNER if cls == "ifc" else "pubtest0382s", novaMet=99, firstName="Casey")
    extra = ""
    if cls == "ifc":
        extra = ("localStorage.setItem('class26e.activeclass','ifc'); localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc']));"
                 " localStorage.setItem('class26e.ifc.drill.v1', %s);"
                 " ['freshstart','intro.seen','unithold.tip','daily.seen','savecode.asked','getstarted'].forEach(k=>localStorage.setItem('class26e.ifc.'+k,'1'));"
                 " localStorage.setItem('class26e.ifc.frame.ok','go-live-1');" % json.dumps(json.dumps(dict(d, publicId="ifcpub0382s"))))
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

LABELS = ["Share this app", "Add to Home Screen", "Check for update", "Report a bug", "Version history", "Advanced settings"]
WHERE = {"Share this app": "share", "Add to Home Screen": "share", "Check for update": "", "Report a bug": "",
         "Version history": "", "Advanced settings": ""}
WORDS = ("Report a bug", "Version history")   # Support's word rows: no icon by design
def open_for(pg, label):
    pg.evaluate("(k)=>{ k ? showAppearance({ page: k }) : showAppearance(); }", WHERE[label]); pg.wait_for_timeout(900)
def rows_ok(sh, t):
    v = sh.get(t)
    # and on the screen it belongs to: its category page, or the menu (382)
    return bool(v) and v["h"] >= 44 and v["full"] and v["label"] and (v["icon"] or t in WORDS) and v["onPage"] == bool(WHERE[t])
SHAPE = """(labels)=>{ const out={};
  const all=[...document.querySelectorAll('#stage .screen-settings button, #stage .screen-settings-sub button')].filter(b=>b.offsetParent);
  for(const t of labels){
    const b=all.find(x=>(x.textContent||'').trim().startsWith(t));
    if(!b){ out[t]=null; continue; }
    const r=b.getBoundingClientRect(), p=b.parentElement.getBoundingClientRect();
    const icon=b.querySelector('svg'); const ir=icon?icon.getBoundingClientRect():null;
    const col=b.closest('.screen-settings, .screen-settings-sub').getBoundingClientRect();
    out[t]={ h:Math.round(r.height), full: r.width >= p.width - 2 && p.width >= col.width*0.85,
      icon: !!ir && ir.width>=12 && ir.right <= r.left + r.width*0.25, label: (b.textContent||'').trim().length>0,
      onPage: !!b.closest('.screen-settings-page') };
  }
  return out; }"""
GEOM = """()=>{ const de=document.documentElement;
  const rows=[...document.querySelectorAll('#stage .screen-settings button, #stage .screen-settings-sub button')].filter(b=>b.offsetParent).map(b=>b.getBoundingClientRect());
  return { hscroll: de.scrollWidth - innerWidth, past: rows.filter(r=>r.right > innerWidth + 1 || r.left < -1).length }; }"""

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    # (1) Report a bug is just the report
    ctx, pg = page(br, 440, 956, (62, 0, 34, 0), True)
    pg.evaluate("()=>showBugReport()"); pg.wait_for_timeout(700)
    rb = pg.evaluate("""()=>{ const f=document.querySelector('.screen-bugreport'); if(!f) return null;
      const b=[...f.querySelectorAll('button')].filter(x=>!x.closest('.back-link') && !x.classList.contains('back-link')).map(x=>x.textContent.trim());
      return { buttons:b, box: !!f.querySelector('textarea') }; }""")
    diag = [b for b in (rb or {}).get("buttons", []) if any(w in b.lower() for w in ("speed", "timing", "drag", "test"))]
    chk("Report a bug has no diagnostics controls (%s)" % (rb,), rb and not diag, rb)
    chk("its form is the text field and one send button", rb and rb["box"] and len(rb["buttons"]) == 1, rb)

    # (2) rows
    for t in LABELS:
        open_for(pg, t)
        sh = pg.evaluate(SHAPE, [t])
        chk("%s is a full-width row, 44px+, with a label%s (%s)" % (t, "" if t in WORDS else " and an icon", sh.get(t)), rows_ok(sh, t), sh.get(t))

    # (3) every action still does what it did
    def fresh(spies, label=""):
        pg.evaluate("(a)=>{ window.__hit=[]; (new Function(a[0]))(); a[1] ? showAppearance({ page: a[1] }) : showAppearance(); }", [spies, WHERE.get(label, "")]); pg.wait_for_timeout(900)
    def tap(label):
        pg.evaluate("(t)=>{ const b=[...document.querySelectorAll('#stage .screen-settings button, #stage .screen-settings-sub button')].find(x=>x.offsetParent&&(x.textContent||'').trim().startsWith(t)); b && b.click(); }", label)
    fresh("""window.__realShare = window.__realShare || navigator.share;
      Object.defineProperty(navigator, 'share', { configurable:true, value: d => { __hit.push('share:' + (d && d.url ? 'url' : '')); return Promise.resolve(); } });""", "Share this app")
    tap("Share this app"); pg.wait_for_timeout(1200)
    chk("Share this app opens the share sheet with the link", "share:url" in pg.evaluate("__hit"), pg.evaluate("__hit"))
    fresh("window.__realInstall = window.__realInstall || handleInstallTap; window.handleInstallTap = () => __hit.push('install');", "Add to Home Screen")
    tap("Add to Home Screen"); pg.wait_for_timeout(400)
    chk("Add to Home Screen runs the install walkthrough", "install" in pg.evaluate("__hit"), pg.evaluate("__hit"))
    pg.evaluate("()=>{ window.handleInstallTap = window.__realInstall; }")
    fresh("""window.__realFetch = window.__realFetch || window.fetch; window.fetch = function(u){ __hit.push('fetch:' + String(u)); return window.__realFetch.apply(this, arguments); };""")
    tap("Check for update"); pg.wait_for_timeout(1500)
    up = pg.evaluate("""()=>({ hit: __hit, line: [...document.querySelectorAll('#stage .settings-buildline')].map(e=>e.textContent).join('|') })""")
    chk("Check for update asks for version.json and says the result on the build line (%s)" % (up,),
        any(h.startswith("fetch:version.json") for h in up["hit"]) and "up to date" in up["line"], up)
    pg.evaluate("()=>{ window.fetch = window.__realFetch; }")
    fresh("window.__realBug = window.__realBug || showBugReport; window.showBugReport = () => __hit.push('bug');")
    tap("Report a bug"); pg.wait_for_timeout(400)
    chk("Report a bug opens the report screen", "bug" in pg.evaluate("__hit"), pg.evaluate("__hit"))
    pg.evaluate("()=>{ window.showBugReport = window.__realBug; }")
    fresh("window.__realRel = window.__realRel || showReleaseHistory; window.showReleaseHistory = f => __hit.push('rel:' + f);")
    tap("Version history"); pg.wait_for_timeout(400)
    chk("Version history opens the release history from Settings", "rel:settings" in pg.evaluate("__hit"), pg.evaluate("__hit"))
    pg.evaluate("()=>{ window.showReleaseHistory = window.__realRel; }")
    fresh("")
    tap("Advanced settings"); pg.wait_for_timeout(1200)
    # since the colour redesign (382) Advanced is a page of its own (check-b382-credits covers it in full)
    adv = pg.evaluate("""()=>{ const p=document.querySelector('#stage .screen-advsettings');
      return { page: !!p, reset: !!p && !!document.getElementById('resetbtn') && document.getElementById('resetbtn').getBoundingClientRect().height > 0 }; }""")
    chk("Advanced settings opens its page, Reset on it (%s)" % (adv,), adv["page"] and adv["reset"], adv)
    ctx.close()

    # (4) no overflow anywhere
    for label, (w, h, ins, inst), cls in (("iPhone 440", (440, 956, (62, 0, 34, 0), True), "academy"),
                                          ("iPhone 440, Fire Code", (440, 956, (62, 0, 34, 0), True), "ifc"),
                                          ("Pro Max at 85%", (518, 1125, (73, 0, 40, 0), True), "academy"),
                                          ("SE 375", (375, 667, (20, 0, 0, 0), False), "academy"),
                                          ("SE 375, Fire Code", (375, 667, (20, 0, 0, 0), False), "ifc"),
                                          ("iPad 834", (834, 1194, (24, 0, 20, 0), True), "academy"),
                                          ("laptop", (1512, 852, (0, 0, 0, 0), False), "academy")):
        ctx, pg = page(br, w, h, ins, inst, cls)
        geos, shs = {}, {}
        for key in ("", "share"):
            pg.evaluate("(k)=>{ k ? showAppearance({ page: k }) : showAppearance(); }", key); pg.wait_for_timeout(1100)
            geos[key or "menu"] = pg.evaluate(GEOM)
            shs.update({k: v for k, v in pg.evaluate(SHAPE, LABELS).items() if v})
        cl = pg.evaluate("window.NOVA_CLASS")
        all_rows = all(rows_ok(shs, t) for t in LABELS)
        chk("%s (%s): no sideways scroll, nothing past the edge, every action a row (%s)" % (label, cl, geos),
            all(g_["hscroll"] <= 0 and g_["past"] == 0 for g_ in geos.values()) and all_rows and cl == cls, {"geo": geos, "rows": shs})
        ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
