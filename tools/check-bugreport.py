#!/usr/bin/env python3
"""Reporting a bug: the Settings button through to what gets written.

The assertion that matters most here is the last one - THE SYNC CODE IS
NOWHERE IN IT. A report lands in `vrooms`, which is world-readable,
because these Firestore rules only allow listing `leaderboard` and
`vrooms`; a `bugs` collection comes back PERMISSION_DENIED on a list, so
reports written there would be write-only and nobody would ever read
them. That makes "what goes in the document" a security question rather
than a formatting one: the ANONYMOUS publicId identifies the reporter,
never the code that opens their account.

  python3 tools/check-bugreport.py
"""
import sys
import functools, http.server, io, os, re, socket, threading, json
from playwright.sync_api import sync_playwright
CHROME="/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC=sys.argv[sys.argv.index("--against")+1] if "--against" in sys.argv else os.path.join(ROOT,"index.html")
OUT=os.environ.get("BUGREPORT_OUT","")
INSET={"top":"59px","bottom":"34px","left":"0px","right":"0px"}
HOOK='''
  window.__wrote = null;
  window.__fake=function(){ fbDb={collection:function(n){return{doc:function(i){return{
    set:function(v){ window.__wrote={coll:n,id:i,data:v}; return Promise.resolve(); },
    get:function(){return Promise.resolve({exists:false});},
    delete:function(){return Promise.resolve();}};}};} };
    onSnapshotResilient=function(r,o){ setTimeout(function(){o({forEach:function(){}});},20); return function(){}; };
    firebaseBecameReady(); };
'''
src=io.open(SRC,encoding="utf-8").read().replace("let fbDb = null;","let fbDb = null;"+HOOK,1)
BODY=re.sub(r"env\(safe-area-inset-(top|bottom|left|right)(?:\s*,[^()]*)?\)", lambda m: INSET[m.group(1)], src)
m=re.search(r'APP_BUILD\s*=\s*"([^"]+)"', src)
VERSION_JSON=json.dumps({"build":m.group(1) if m else "","note":"","frameId":"","frameNote":"","force":False})
STORE=json.dumps({"firstName":"Madison","avatarChar":"ninja","onboardingComplete":True,"leaderboardOptIn":True,
  "tourRev":999,"lastModified":1790400000000,"publicId":"me01","savedCodeSaved":True,
  "lifetime":{"points":9000,"correct":1100,"answered":1300}})
so=socket.socket(); so.bind(("127.0.0.1",0)); PORT=so.getsockname()[1]; so.close()
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
threading.Thread(target=http.server.ThreadingHTTPServer(("127.0.0.1",PORT),functools.partial(Q,directory=ROOT)).serve_forever,daemon=True).start()
URL="http://127.0.0.1:%d/index.html"%PORT
fails=[]
def ck(n,ok,d=""):
    print("  %-4s %s%s"%("PASS" if ok else "FAIL",n,("  -> "+str(d)) if d else ""))
    if not ok: fails.append(n)
with sync_playwright() as pw:
    br=pw.chromium.launch(executable_path=CHROME)
    ctx=br.new_context(viewport={"width":440,"height":956}); pg=ctx.new_page()
    errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
    pg.route("**/index.html", lambda r: r.fulfill(status=200,headers={"content-type":"text/html; charset=utf-8"},body=BODY))
    pg.route("**/version.json", lambda r: r.fulfill(status=200,headers={"content-type":"application/json"},body=VERSION_JSON))
    pg.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.drill.v1',%s);localStorage.setItem('class26e.synccode','WXYZ-7777');}catch(e){}" % json.dumps(STORE))
    pg.goto(URL); pg.wait_for_timeout(3200)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __fake();}")
    pg.wait_for_timeout(600)
    pg.evaluate("()=>showAppearance()"); pg.wait_for_timeout(800)
    pg.evaluate("()=>[...document.querySelectorAll('.cal-profile-btn')].find(b=>/Report a bug/.test(b.textContent))?.scrollIntoView({block:'center',behavior:'instant'})")
    pg.wait_for_timeout(300)
    btn=[b for b in pg.query_selector_all(".cal-profile-btn") if "Report a bug" in (b.text_content() or "")]
    ck("the Settings button exists", len(btn)==1, len(btn))
    btn[0].click(); pg.wait_for_timeout(700)
    ck("it opens the report screen", pg.evaluate("()=>!!document.querySelector('.screen-bugreport')"))
    # empty send must not write. Cleared first: the app's own boot push
    # writes through the same stub, so a stale __wrote from that is not
    # evidence the report screen wrote anything.
    pg.evaluate("()=>{ window.__wrote = null; }")
    pg.click(".screen-bugreport .cal-profile-btn"); pg.wait_for_timeout(400)
    ck("an empty report is refused", pg.evaluate("()=>window.__wrote")is None)
    pg.fill(".bug-report-box", "The lobby jumps around when I open it.")
    pg.wait_for_timeout(200)
    if OUT: pg.screenshot(path=os.path.join(OUT,"bugreport.png"))
    pg.click(".screen-bugreport .cal-profile-btn"); pg.wait_for_timeout(900)
    w=pg.evaluate("()=>window.__wrote")
    ck("it writes somewhere listable", bool(w) and w["coll"]=="vrooms", w and w["coll"])
    ck("with a bug- id", bool(w) and w["id"].startswith("bug-"), w and w["id"])
    d=(w or {}).get("data") or {}
    ck("carrying the text", d.get("text","").startswith("The lobby jumps"), d.get("text"))
    ck("and the build", bool(d.get("build")), d.get("build"))
    ck("and the device", bool(d.get("ua")) and bool(d.get("viewport")), d.get("viewport"))
    ck("identified by the ANONYMOUS id", d.get("from")=="me01", d.get("from"))
    blob=json.dumps(d)
    ck("THE SYNC CODE IS NOWHERE IN IT", "WXYZ-7777" not in blob and "synccode" not in blob)
    ck("and it returns to Settings", pg.evaluate("()=>!!document.querySelector('.screen-bugreport')") is False)
    ck("no JS errors", not errs, errs[:1])
    ctx.close(); br.close()
print("\n%s (%d failure(s))"%("ALL PASS" if not fails else "FAILED: "+", ".join(fails),len(fails)))
raise SystemExit(1 if fails else 0)
