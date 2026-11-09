"""Build 384 r13: the Hive / Sprinkler Head challenge is a hundo on the class's biggest unit. Madison: "Do the biggest unit one.
Score a 100 on the biggest unit". In both classes (academy: the Hive; Fire Code: the Sprinkler Head):
 (1) the challenge names the unit with the most questions in the class (worked out from the bank here, independently);
 (2) locked with no hundo there, unlocked with one - and a hundo on some other unit does not open it;
 (3) its note on the unlock card names the size of that unit; no page errors.
Run:  python3 tools/check-b384-hivechallenge.py   (--against OLD/index.html must FAIL)"""
import os, sys, json, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
if "--against" in sys.argv:
    body = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
    cb.BODY = cb.INSET_RE.sub("0px", body).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
a = json.loads(cb.USED_ACCOUNT); a["publicId"] = "xph5b57jbp5a"; a["novaMet"] = 99; IACCT = json.dumps(a)
IINIT = ("try{localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));localStorage.setItem('class26e.greet.ifc','done');"
         "['intro.seen','unithold.tip','daily.seen','weekrecap.v1','savecode.card'].forEach(k=>localStorage.setItem('class26e.ifc.'+k, k==='weekrecap.v1'?'9999-12-31':'9'));"
         "localStorage.setItem('class26e.ifc.drill.v1', %s);}catch(e){}" % json.dumps(IACCT))
R = """()=>{ const counts={}; QUESTIONS.forEach(q=>{ const t=(q.topic||'').trim(); if(t) counts[t]=(counts[t]||0)+1; });
  const ts = topicsIn(QUESTIONS); let big=null; ts.forEach(t=>{ if(!big || counts[t]>counts[big]) big=t; });
  const other = ts.find(t=>t!==big);
  const f = CHARACTER_FEATS.busyday300; const keep = Object.assign({}, store.unitPerfects);
  ts.forEach(t=>store.unitPerfects[t]=0);
  const locked0 = isLockedCharacter('hive');
  store.unitPerfects[other]=1; const lockedOther = isLockedCharacter('hive');
  store.unitPerfects[other]=0; store.unitPerfects[big]=1; const openBig = !isLockedCharacter('hive');
  store.unitPerfects = keep;
  let note = ''; try{ note = unlockNoteFor({kind:'character', id:'hive'}); }catch(e){ note = 'ERR ' + e; }
  return { big, n: counts[big], label: String(f.label), locked0, lockedOther, openBig, note, name: AVATAR_DISPLAY_NAME.hive }; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch()
    for cls in ("academy", "ifc"):
        ctx, pg = (cb.booted(br, 440, 956, seed=IACCT, dpr=1, init=IINIT) if cls == "ifc" else cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT, dpr=1))
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        r = pg.evaluate(R); tag = "%s (%s)" % (cls, r["name"])
        chk("(1) %s: the challenge names the biggest unit, %s (%d questions): %r" % (tag, r["big"], r["n"], r["label"]), r["big"] and r["big"] in r["label"] and "hundo" in r["label"].lower(), r)
        chk("(2) %s: locked with no hundo, still locked with a hundo elsewhere, open with one on %s" % (tag, r["big"]), r["locked0"] and r["lockedOther"] and r["openBig"], r)
        chk("(3) %s: the unlock card's note gives the unit's size (%r) and no page errors" % (tag, r["note"]), ("{:,}".format(r["n"]) in r["note"]) and not errs, [r["note"], errs[:2]])
        ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
