#!/usr/bin/env python3
"""The save-your-code banner, and the build number on Welcome.

Both exist because of one report - "got randomly signed out" - and both
were written against build 158, where they fail. Run it with --against
on that build and watch it go red; a check that passes on the build it
was written for is measuring nothing.

  python3 tools/check-save-code.py
  python3 tools/check-save-code.py --against /path/to/old-index.html

Taps are real hit-tested taps, never element.click(), which ignores
pointer-events and hit testing - the Join button on another banner
measured fine and was unpressable for exactly that reason.
"""
import sys
import functools, http.server, io, os, re, socket, threading, json
from playwright.sync_api import sync_playwright
CHROME="/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC=sys.argv[sys.argv.index("--against")+1] if "--against" in sys.argv else os.path.join(ROOT,"index.html")
OUT=os.environ.get("SAVECODE_OUT","")
if OUT: os.makedirs(OUT,exist_ok=True)
INSET={"top":"59px","bottom":"34px","left":"0px","right":"0px"}
HOOK='''
  window.__fake=function(){ fbDb={collection:function(n){return{doc:function(i){return{
    set:function(){return Promise.resolve();},get:function(){return Promise.resolve({exists:false});},
    delete:function(){return Promise.resolve();}};}};} };
    onSnapshotResilient=function(ref,onNext){ setTimeout(function(){onNext({forEach:function(){}});},20); return function(){}; };
    firebaseBecameReady(); };
'''
src=io.open(SRC,encoding="utf-8").read().replace("let fbDb = null;","let fbDb = null;"+HOOK,1)
BODY=re.sub(r"env\(safe-area-inset-(top|bottom|left|right)(?:\s*,[^()]*)?\)", lambda m: INSET[m.group(1)], src)

# VERSION.JSON HAS TO MATCH WHATEVER BUILD IS BEING SERVED. With
# --against, the served file is an older build while the repo's
# version.json is the current one - so the forced update fires, the page
# reloads under the harness, and the run dies on "execution context was
# destroyed". That is the update machinery working correctly and it has
# nothing to do with what this file checks, so the served build is
# echoed back instead.
m=re.search(r'APP_BUILD\s*=\s*"([^"]+)"', src)
SERVED_BUILD=m.group(1) if m else ""
VERSION_JSON=json.dumps({"build":SERVED_BUILD,"note":"","frameId":"","frameNote":"","force":False})
STORE='{"firstName":"Madison","avatarChar":"ninja","onboardingComplete":true,"leaderboardOptIn":true,"tourRev":999,"lastModified":1790400000000,"lifetime":{"points":420,"correct":88}}'
so=socket.socket(); so.bind(("127.0.0.1",0)); PORT=so.getsockname()[1]; so.close()
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
threading.Thread(target=http.server.ThreadingHTTPServer(("127.0.0.1",PORT),functools.partial(Q,directory=ROOT)).serve_forever,daemon=True).start()
URL="http://127.0.0.1:%d/index.html"%PORT
fails=[]
def ck(n,ok,d=""):
    print("  %-4s %s%s"%("PASS" if ok else "FAIL",n,("  -> "+str(d)) if d else ""))
    if not ok: fails.append(n)
DEV=[("17-pro-max",440,956),("ipad-pro-11",834,1194),("se2",375,667),("se1",320,568)]
with sync_playwright() as pw:
    br=pw.chromium.launch(executable_path=CHROME)

    print("\n1. the build label on Welcome")
    for name,w,h in DEV:
        ctx=br.new_context(viewport={"width":w,"height":h})
        pg=ctx.new_page(); errs=[]
        pg.on("pageerror",lambda e:errs.append(str(e)))
        pg.route("**/index.html", lambda r: r.fulfill(status=200,headers={"content-type":"text/html; charset=utf-8"},body=BODY))
        pg.route("**/version.json", lambda r: r.fulfill(status=200,headers={"content-type":"application/json"},body=VERSION_JSON))
        pg.goto(URL); pg.wait_for_timeout(3000)
        pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
        pg.wait_for_timeout(700)
        m=pg.evaluate("""()=>{const e=document.querySelector('.welcome-build');
          if(!e) return {missing:true};
          const b=e.getBoundingClientRect();
          const hero=document.querySelector('.cosmic-hero-wrap').getBoundingClientRect();
          const hint=[...document.querySelectorAll('.cosmic-welcome p')].pop().getBoundingClientRect();
          const d=document.documentElement;
          return {text:e.textContent, top:Math.round(b.top), bot:Math.round(b.bottom),
                  left:Math.round(b.left), clearOfHero:Math.round(hero.top-b.bottom),
                  overlapsHint: b.bottom>hint.top && b.top<hint.bottom,
                  hscroll:d.scrollWidth-d.clientWidth, vis:getComputedStyle(e).visibility};}""")
        ck("%s shows the build" % name, m.get("text","").startswith("Build "), m)
        ck("%s clears the hero" % name, not m.get("missing") and m["clearOfHero"]>0, m.get("clearOfHero"))
        ck("%s no overlap / no sideways scroll" % name,
           not m.get("missing") and not m["overlapsHint"] and m["hscroll"]==0, m)
        if errs: ck("%s no JS errors"%name, False, errs[:1])
        if OUT: pg.screenshot(path=os.path.join(OUT,name+"-welcome.png"))
        ctx.close()

    print("\n2. the save-your-code banner on Home")
    ctx=br.new_context(viewport={"width":440,"height":956},permissions=["clipboard-read","clipboard-write"])
    pg=ctx.new_page(); errs=[]
    pg.on("pageerror",lambda e:errs.append(str(e)))
    pg.route("**/index.html", lambda r: r.fulfill(status=200,headers={"content-type":"text/html; charset=utf-8"},body=BODY))
    pg.route("**/version.json", lambda r: r.fulfill(status=200,headers={"content-type":"application/json"},body=VERSION_JSON))
    pg.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.drill.v1','%s');localStorage.setItem('class26e.synccode','WXYZ-7777');}catch(e){}"%STORE)
    pg.goto(URL); pg.wait_for_timeout(3000)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __fake();}")
    pg.wait_for_timeout(1200)
    b=pg.evaluate("""()=>{const e=document.getElementById('save-code');
      if(!e) return {missing:true};
      const r=e.getBoundingClientRect(); const cs=getComputedStyle(e);
      const act=e.querySelector('.app-banner-act').getBoundingClientRect();
      return {tag:e.querySelector('.app-banner-tag').textContent,
              text:e.querySelector('.app-banner-text').textContent,
              top:Math.round(r.top), h:Math.round(r.height), pe:cs.pointerEvents,
              colour:cs.getPropertyValue('--banner-color').trim(),
              actH:Math.round(act.height), prompts:store.savedCodePrompts};}""")
    ck("the banner appears on Home", not b.get("missing"), b)
    ck("it is tagged YOUR ACCOUNT", b.get("tag")=="YOUR ACCOUNT", b.get("tag"))
    ck("its colour differs from friend/vroom", b.get("colour")=="#F5B54D", b.get("colour"))
    ck("it is tappable (pointer-events)", b.get("pe")=="auto", b.get("pe"))
    ck("the action button clears 44px", b.get("actH",0)>=44, b.get("actH"))
    ck("the show is counted", b.get("prompts")==1, b.get("prompts"))
    ck("it clears the top inset", b.get("top",0)>=59, b.get("top"))
    if OUT: pg.screenshot(path=os.path.join(OUT,"home-save-banner.png"))
    # A REAL hit-tested tap, not element.click(). Guarded, because on a
    # build without the banner this would otherwise die on a 30s
    # Playwright timeout and report a crash rather than a failure -
    # and --against on the old build is exactly when that happens.
    # THE LABEL IS NOT THE ASSERTION - the action button was "Copy code"
    # and is "Save it" now, and a check naming either would fail the app
    # for being right. What has to hold is that ONE tap puts the real
    # code somewhere and only then marks the prompt satisfied.
    if b.get("missing"):
        for n in ("one tap puts the code somewhere",
                  "and marks it saved", "and the banner goes",
                  "the share sheet is used where there is one",
                  "a cancelled share is not a save"):
            ck(n, False, "no banner to tap")
        after = {}
    else:
        pg.click("#save-code .app-banner-act"); pg.wait_for_timeout(600)
        after=pg.evaluate("""async ()=>({clip: await navigator.clipboard.readText(),
           saved: store.savedCodeSaved, gone: !document.getElementById('save-code'),
           toast: (document.querySelector('.toast')||{}).textContent||''})""")
        ck("one tap puts the code somewhere",
           (after.get("clip") or "") == "WXYZ-7777", after.get("clip"))
        ck("and marks it saved", after.get("saved") is True, after)
        ck("and the banner goes", after.get("gone") is True, after)

        # A CLIPBOARD DOES NOT SURVIVE THE NEXT COPY, which is the whole
        # problem with "save your code" being a copy button. Where a
        # share sheet exists the banner has to use it, and the code has
        # to be in the shared TEXT - a title alone saves nothing.
        # Stubbed: headless Chromium has no share sheet.
        pg.evaluate("""()=>{ window.__shared=null; store.savedCodeSaved=false;
          store.savedCodePrompts=0;
          navigator.share=(d)=>{ window.__shared=d; return Promise.resolve(); };
          showHome(); }""")
        pg.wait_for_timeout(700)
        if pg.query_selector("#save-code .app-banner-act"):
            pg.click("#save-code .app-banner-act"); pg.wait_for_timeout(600)
        sh = pg.evaluate("()=>window.__shared")
        ck("the share sheet is used where there is one",
           bool(sh) and "WXYZ-7777" in ((sh or {}).get("text") or ""),
           str(sh)[:140])

        # Backing out of the sheet saved nothing, so it must not silence
        # the reminder - the same rule the refused-clipboard path has.
        pg.evaluate("""()=>{ store.savedCodeSaved=false; store.savedCodePrompts=0;
          navigator.share=()=>Promise.reject(Object.assign(new Error("x"),{name:"AbortError"}));
          navigator.clipboard.writeText=()=>Promise.reject(new Error("no"));
          showHome(); }""")
        pg.wait_for_timeout(700)
        if pg.query_selector("#save-code .app-banner-act"):
            pg.click("#save-code .app-banner-act"); pg.wait_for_timeout(600)
        ck("a cancelled share is not a save",
           pg.evaluate("()=>!!store.savedCodeSaved") is False)
    if errs: ck("no JS errors", False, errs[:2])
    else: ck("no JS errors", True)
    ctx.close()

    print("\n3. it stops after three, and never for a device with no code")
    ctx=br.new_context(viewport={"width":440,"height":956})
    pg=ctx.new_page()
    pg.route("**/index.html", lambda r: r.fulfill(status=200,headers={"content-type":"text/html; charset=utf-8"},body=BODY))
    pg.route("**/version.json", lambda r: r.fulfill(status=200,headers={"content-type":"application/json"},body=VERSION_JSON))
    pg.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.drill.v1','%s');localStorage.setItem('class26e.synccode','WXYZ-7777');}catch(e){}"%STORE)
    pg.goto(URL); pg.wait_for_timeout(3000)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __fake();}")
    pg.wait_for_timeout(900)
    seen=[]
    for i in range(5):
        seen.append(pg.evaluate("()=>!!document.getElementById('save-code')"))
        pg.evaluate("()=>{document.getElementById('save-code')?.remove(); showHome();}")
        pg.wait_for_timeout(350)
    ck("shown exactly three times then stops", seen==[True,True,True,False,False], seen)
    off=pg.evaluate("""()=>{ store.savedCodePrompts=0; store.savedCodeSaved=false;
       syncOff=true; document.getElementById('save-code')?.remove(); showHome(); return true; }""")
    pg.wait_for_timeout(400)
    ck("never shown to a device that opted out of syncing",
       pg.evaluate("()=>!!document.getElementById('save-code')") is False)
    ctx.close()
    br.close()
print("\n%s (%d failure(s))"%("ALL PASS" if not fails else "FAILED: "+", ".join(fails),len(fails)))
raise SystemExit(1 if fails else 0)
