#!/usr/bin/env python3
"""Build 384.22: a launch that never finishes says so, and offers Try again.
The owner, after an update that "took forever": "I closed the app and went to open it again. Now the app isn't loading when I open it." Nothing
on screen said what was wrong. A plain script in the head now shows a page of its own if, 25 seconds in, the app has not put a screen on the stage
or its splash is still up. Read off the page (real time, so ~1.5 minutes):
 (1) a normal launch (a seeded account and a fresh install): 32 seconds on there is NO #launch-trouble, the app is up (a screen on the stage, no splash);
 (2) a launch whose main script dies on its first line (the page simulated broken): nothing of it shows before 20 seconds, and by 32 the
     #launch-trouble page is up, covering the screen, with a Try again button at least 44px tall and a plain line that says progress is saved;
 (3) Try again fetches the page afresh (cache bypassed: the request carries the reload cache mode) and reloads it;
 (4) when the app does come up late (a launch that was only slow), the page takes itself away.
Run:  python3 tools/check-b384-launchtrouble.py   (--against OLD/index.html must FAIL: 384.21 has no such page)"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
from playwright.sync_api import sync_playwright
args = sys.argv[1:]
PATH = args[args.index("--against") + 1] if "--against" in args else os.path.join(HERE, "..", "index.html")
HTML = open(PATH, encoding="utf-8").read()
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
BROKEN = HTML.replace('const APP_BUILD = "', 'throw new Error("simulated broken launch");\nconst APP_BUILD = "', 1)
assert BROKEN != HTML
STATE = """()=>{ const t=document.getElementById('launch-trouble'); const st=document.getElementById('stage'); const b=t&&t.querySelector('button'); const r=b&&b.getBoundingClientRect();
  return { trouble:!!t, up:!!(st&&st.children.length)&&!document.getElementById('splashscreen'), splash:!!document.getElementById('splashscreen'), btnH:r?r.height:0, text:t?t.textContent:'',
           cover:t?(()=>{ const q=t.getBoundingClientRect(); return q.width>=innerWidth&&q.height>=innerHeight; })():false }; }"""
srv, PORT = rc["serve"]()
try:
  with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    seed = json.dumps(json.dumps(dict(rc["SEED"])))
    for lab, store in (("a seeded account", True), ("a fresh install", False)):
        ctx = br.new_context(viewport={"width": 440, "height": 956}); pg = ctx.new_page()
        pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8", "cache-control": "no-store"}, body=HTML))
        if store: pg.add_init_script("try{localStorage.setItem('class26e.drill.v1',%s);localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');}catch(e){}" % seed)
        pg.goto("http://127.0.0.1:%d/index.html" % PORT); pg.wait_for_timeout(32000)
        s = pg.evaluate(STATE)
        chk("(1) %s: a normal launch shows no trouble page and the app is up (%s)" % (lab, {k: s[k] for k in ("trouble", "up", "splash")}), not s["trouble"] and s["up"], s)
        ctx.close()
    # (2) and (3): a broken launch
    ctx = br.new_context(viewport={"width": 440, "height": 956}); pg = ctx.new_page(); reqs = []
    pg.route("**/index.html", lambda r, q: (reqs.append(q.headers.get("cache-control", "")), r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8", "cache-control": "no-store"}, body=BROKEN))[1])
    pg.on("pageerror", lambda e: None)
    pg.goto("http://127.0.0.1:%d/index.html" % PORT); pg.wait_for_timeout(20000)
    early = pg.evaluate(STATE)
    pg.wait_for_timeout(12000); late = pg.evaluate(STATE)
    chk("(2) a broken launch: nothing at 20 seconds, the trouble page at 32 (%s then %s)" % (early["trouble"], late["trouble"]), not early["trouble"] and late["trouble"], [early, late])
    chk("(2) ...it covers the screen, its button is at least 44px, and it says progress is saved", late["cover"] and late["btnH"] >= 44 and "saved" in late["text"], late)
    n0 = len(reqs)
    pg.evaluate("()=>document.querySelector('#launch-trouble button').click()"); pg.wait_for_timeout(4000)
    chk("(3) Try again fetches the page afresh and reloads it (%d requests after, %d before)" % (len(reqs), n0), len(reqs) >= n0 + 2, reqs)
    ctx.close()
    # (4) a slow launch: the page comes up late and the trouble page goes
    ctx = br.new_context(viewport={"width": 440, "height": 956}); pg = ctx.new_page()
    pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8", "cache-control": "no-store"}, body=HTML))
    pg.goto("http://127.0.0.1:%d/index.html" % PORT); pg.wait_for_timeout(1500)
    pg.evaluate("""()=>{ window.__keep=[...document.getElementById('stage').children]; document.getElementById('stage').replaceChildren(); const sp=document.createElement('div'); sp.id='splashscreen'; document.body.appendChild(sp); }""")
    pg.wait_for_timeout(27000); a = pg.evaluate(STATE)
    pg.evaluate("()=>{ document.getElementById('splashscreen').remove(); document.getElementById('stage').replaceChildren(...window.__keep); }"); pg.wait_for_timeout(5000); b = pg.evaluate(STATE)
    chk("(4) a slow launch: the page shows (%s), and goes when the app comes up (%s)" % (a["trouble"], b["trouble"]), a["trouble"] and not b["trouble"], [a, b])
    ctx.close(); br.close()
finally:
    srv.shutdown()
print("ALL PASS" if ok else "FAILED"); sys.exit(0 if ok else 1)
