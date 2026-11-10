"""Build 384 r17: the Sync page's note under the code names no class (the code is the account's).
Madison, the Fire Code Sync page circled ("The same code as your Police Academy account. Fire Code saves to the cloud under it..."):
"I'm not sure what's up with this sync code description, needs to be fixed though. Shouldn't specific stuff about either class not be there?"
With an account that has a sync code, in the academy and in Fire Code: the note under the code (.sync-note-plain) names neither "Police Academy",
"Fire Code" nor "26E", says it is the account's code, and is the same line in both classes.
Run:  python3 tools/check-b384-syncnote.py   (--against OLD/index.html must FAIL)"""
import os, sys, json, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
if "--against" in sys.argv:
    body = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
    cb.BODY = cb.INSET_RE.sub("0px", body).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
from playwright.sync_api import sync_playwright
import re
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
texts = {}
with sync_playwright() as pw:
    br = pw.chromium.launch()
    for cls in ("academy", "ifc"):
        init = ""
        acct = json.loads(cb.USED_ACCOUNT)
        if cls == "ifc":
            acct["publicId"] = "xph5b57jbp5a"
            init = ("try{localStorage.setItem('class26e.synccode','TEST-3840');localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['academy','ifc']));localStorage.setItem('class26e.greet.ifc','done');"
                    "['intro.seen','unithold.tip','daily.seen','weekrecap.v1','savecode.card'].forEach(k=>localStorage.setItem('class26e.ifc.'+k, k==='weekrecap.v1'?'9999-12-31':'9'));"
                    "localStorage.setItem('class26e.ifc.drill.v1', %s);}catch(e){}" % json.dumps(json.dumps(acct)))
        ctx, pg = cb.booted(br, 440, 956, seed=json.dumps(acct), init=init or None)
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:140]))
        pg.evaluate("()=>{ try{ if(!syncCode) setSyncCode(generateSyncCode()); }catch(e){} showAppearance({page:'sync'}); }"); pg.wait_for_timeout(1500)
        t = pg.evaluate("()=>{ const n=document.querySelector('#stage .sync-note-plain'); return { cls: window.NOVA_CLASS, text: n ? n.textContent : null, code: typeof syncCode === 'string' && !!syncCode }; }")
        texts[cls] = t["text"]
        chk("%s: the note under the sync code names no class (%s)" % (cls, (t["text"] or "")[:90]), t["text"] and not re.search(r"police academy|fire code|26e|academy", t["text"], re.I) and re.search(r"account", t["text"], re.I), t)
        chk("%s: no page errors" % cls, not errs, errs)
        ctx.close()
    chk("the same line in both classes", texts.get("academy") and texts.get("academy") == texts.get("ifc"), texts)
    br.close()
print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
