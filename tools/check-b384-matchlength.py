#!/usr/bin/env python3
"""Build 384: a Tug of War or Battle match cannot be called over in its first five minutes.

Madison: "those matches can't end really quick? We gotta ensure those matches can last at least 5 minutes ... any virtual room match".
Drives the host's own end-of-match test (tugCheckOver / battleCheckOver) with a rope already pulled clear / a side already at 0 HP,
at 1 minute and at 6 minutes in, with NO test hook, and records whether the room was marked over. A forfeit (a side with nobody left)
must still end it at once. Also: a tug room set to 5 questions still plays 50.
  python3 tools/check-b384-matchlength.py [--against OLD/index.html]   (must FAIL on the build before)"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
import importlib.util
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = cb.INSET_RE
    cb.patched = lambda ins: IR.sub(lambda m: {"top": "%dpx" % ins[0], "right": "%dpx" % ins[1], "bottom": "%dpx" % ins[2], "left": "%dpx" % ins[3]}[m.group(1)], OLD)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
JS = """([kind, ageMs, gone])=>{
  window.__upd = [];
  window.vroomDb = () => ({collection:()=>({doc:()=>({update:(u)=>{ window.__upd.push(u); return Promise.resolve(); }})})});
  vroomIsHost = true; vroomCode = 'TEST-0001';
  const now = Date.now();
  const here = gone ? {a1:true, a2:true} : {a1:true, a2:true, b1:true, b2:true};
  window.vroomMatchHere = () => here;
  const teams = {a1:'a', a2:'a', b1:'b', b2:'b'};
  let d;
  if(kind === 'tug'){
    d = {startAt: now - ageMs, count: 50, tug:{teams, progress:{}}};
    window.tugRopePos = () => 12;   /* pulled clear past any win gap */
    tugCheckOver(d);
  } else {
    d = {startAt: now - ageMs, participants:{a1:{},a2:{},b1:{},b2:{}}, battle:{count: 50, teams, progress:{}}};
    window.vroomLateFor = () => false;
    window.battleReplay = () => ({downed:'b', hp:{a:50, b:0}});
    battleCheckOver(d);
  }
  return window.__upd.length;
}"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    for kind in ("tug", "battle"):
        for age, label, want in ((60_000, "one minute in", 0), (6 * 60_000, "six minutes in", 1)):
            ctx, pg = cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT, dpr=1)
            n = pg.evaluate(JS, [kind, age, False])
            chk("%s: a decided match %s is %s" % (kind, label, "not called over" if want == 0 else "called over"), n == want, n)
            ctx.close()
        ctx, pg = cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT, dpr=1)
        n = pg.evaluate(JS, [kind, 60_000, True])
        chk("%s: a side with nobody left still ends it at once" % kind, n == 1, n)
        ctx.close()
    ctx, pg = cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT, dpr=1)
    r = pg.evaluate("()=>({fast: !!window.__vroomFast, minMs: typeof vroomMinMs==='function' ? vroomMinMs() : 0, minQ: typeof tugMinQ==='function' ? tugMinQ() : 0})")
    chk("the floors are live in a normal run: five minutes and fifty questions", r["minMs"] >= 5 * 60_000 and r["minQ"] >= 50, r)
    ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILURES"); sys.exit(0 if ok else 1)
