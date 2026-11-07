#!/usr/bin/env python3
"""Build 384 review: Nova's "Hello again ... You'll find me here now" comes once per ACCOUNT, not once per device, sign-in or class.

Madison: "the nova instructor will keep messaging me, he keeps sending me the 'hello Maddog, it's nova, you'll find me here now'
even though I've already seen that message multiple times and I've had an account for a while."
Being friends with him was remembered only on the device (class26e.nova): a sign-out wipes it, a Safari tab beside the
installed app never had it, and Fire Code keeps its own copy. So:
(1) an account that has heard from him before (novaHeard has entries), on a device with no class26e.nova (a sign-in, a second
    jar): he becomes a friend with no hello, and the account records the hello as had;
(2) the same in Fire Code, where the account's academy copy is the one that has heard from him;
(3) an account that has never heard from him: the hello once - and after its device memory is wiped (a sign-out), not again;
(4) a new account's introduction still says his hello;
(5) no page errors.
  python3 tools/check-b384-novahello.py [--against OLD/index.html]   (must FAIL on the build before)"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b384nh"}
exec(src, G)
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = G["g"]["INSET_RE"]
    def _old(ins):
        t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
        return IR.sub(lambda m: v[m.group(1)], OLD)
    G["g"]["patched"] = _old
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
HELLOS = "()=>{ try{ return novaThread().filter(m=>m.kind==='hello' || /You.ll find me here|This is where you.ll find me/.test(m.text||'')).length; }catch(e){ return -1; } }"
BEFRIEND = """(heard)=>{ try{ localStorage.removeItem('class26e.nova'); }catch(e){}
  store.novaHeard = heard; novaBefriend({ quiet: true });
  return { friend: novaIsFriend(), hellos: novaThread().filter(m=>m.kind==='hello').length, had: !!(store.novaHeard||{}).hello }; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    errs_all = []
    # academy
    ctx, pg, errs = G["page"](br, G["init"](G["academy"], active="academy"))
    pg.wait_for_timeout(800)
    r1 = pg.evaluate(BEFRIEND, {"@last": 1730000000000, "@rank": 3})
    chk("(1) an account that has heard from him, on a fresh device: friends, no hello, the hello recorded (%s)" % r1,
        r1["friend"] and r1["hellos"] == 0 and r1["had"], r1)
    r3 = pg.evaluate(BEFRIEND, {})
    r3b = pg.evaluate("""()=>{ try{ localStorage.removeItem('class26e.nova'); }catch(e){} novaBefriend({ quiet: true });
      return { friend: novaIsFriend(), hellos: novaThread().filter(m=>m.kind==='hello').length }; }""")
    chk("(3) never heard from him: the hello once (%s); after a sign-out wipes the device's memory, not again (%s)" % (r3, r3b),
        r3["hellos"] == 1 and r3b["friend"] and r3b["hellos"] == 0, [r3, r3b])
    r4 = pg.evaluate("""()=>{ try{ localStorage.removeItem('class26e.nova'); }catch(e){} store.novaHeard = {}; novaBefriend({ intro: true, quiet: true });
      return { hellos: novaThread().filter(m=>m.kind==='hello').length }; }""")
    chk("(4) a new account's introduction still says hello (%s)" % r4, r4["hellos"] == 1, r4)
    errs_all += errs; ctx.close()
    # Fire Code: the academy copy has heard from him, this class's copy has not
    ctx, pg, errs = G["page"](br, G["init"](G["ifc"]))
    pg.wait_for_timeout(800)
    r2 = pg.evaluate("""()=>{ const a = academyCopyNow(); if(a){ a.novaHeard = { '@last': 1730000000000 }; }
      try{ localStorage.removeItem('class26e.nova'); }catch(e){} store.novaHeard = {}; novaBefriend({ quiet: true });
      return { cls: window.NOVA_CLASS, academy: !!a, friend: novaIsFriend(), hellos: novaThread().filter(m=>m.kind==='hello').length }; }""")
    chk("(2) Fire Code, the academy account has heard from him: friends, no hello (%s)" % r2,
        r2["cls"] == "ifc" and r2["academy"] and r2["friend"] and r2["hellos"] == 0, r2)
    errs_all += errs; ctx.close()
    chk("(5) no page errors", not errs_all, errs_all[:3])
    br.close()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
