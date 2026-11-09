#!/usr/bin/env python3
"""Build 384 review: ONE Nova for every class - never two of his messages in a day because a person is in two classes, and a
class's news says which class it is from when there is more than one.

Madison: "let's ensure that nova messages you as broad guy? Because if you are enrolled into multiple classes it could overlap,
absolutely don't allow that to happen." His thread (class26e.nova) is the device's, shared by the academy and Fire Code; novaHeard
is each class's own, so each copy kept its own "last said" and both could message in a day.
(1) the academy has just heard from him (the shared thread's lastAt, an hour ago): Fire Code's own copy (empty novaHeard) does not
    open a day - and nor does the academy's after a message sent from Fire Code;
(2) a day with nothing said by either does open;
(3) enrolled in two classes, his rank / progress / challenge / vr lines open with the class's name; a tip, hello, broadcast and
    reply do not; enrolled in one, nothing is prefixed.
  python3 tools/check-b384-novabroad.py [--against OLD/index.html]   (must FAIL on the build before)"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b384nb"}
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
GAP = """(ago)=>{ const now = Date.now();
  localStorage.setItem('class26e.nova', JSON.stringify({ since: now - 30 * 864e5, pub: store.publicId || undefined, thread: [], sent: {}, lastAt: ago == null ? 0 : now - ago }));
  store.novaHeard = { '@base': now - 20 * 864e5 };
  return novaDayOpen(store.novaHeard, now); }"""
TAGS = """(n)=>{ localStorage.setItem('class26e.nova', JSON.stringify({ since: Date.now() - 30 * 864e5, pub: store.publicId || undefined, thread: [], sent: {} }));
  if(n === 2){ enrolledClasses = () => ['academy', 'ifc']; } else { enrolledClasses = () => [window.NOVA_CLASS === 'ifc' ? 'ifc' : 'academy']; }
  const out = {}; ['rank', 'progress', 'challenge', 'vr', 'tip', 'broadcast', 'reply', 'hello'].forEach(k => { const m = novaSendDM('Something ' + k, { kind: k }); out[k] = m && m.text; });
  return out; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    errs_all = []
    for cls, init in (("academy", lambda: G["init"](G["academy"], active="academy")), ("ifc", lambda: G["init"](G["ifc"]))):
        ctx, pg, errs = G["page"](br, init())
        pg.wait_for_timeout(800)
        a = pg.evaluate(GAP, 3600 * 1000)
        b = pg.evaluate(GAP, None)
        chk("(1/2) %s: a message from either class an hour ago keeps the day shut (%s); nothing said by either, it opens (%s)" % (cls, a, b), a is False and b is True, [a, b])
        two = pg.evaluate(TAGS, 2)
        title = pg.evaluate("()=>classTitle(ownClass())")
        chk("(3) %s, two classes: rank / progress / challenge / vr open with %r; tip / broadcast / reply / hello do not (%s)" % (cls, title, two),
            all((two[k] or "").startswith(title + ": ") for k in ("rank", "progress", "challenge", "vr")) and not any((two[k] or "").startswith(title) for k in ("tip", "broadcast", "reply", "hello")), two)
        one = pg.evaluate(TAGS, 1)
        chk("(3) %s, one class: nothing is prefixed (%s)" % (cls, one), not any((v or "").startswith(title) for v in one.values()), one)
        errs_all += errs; ctx.close()
    chk("no page errors", not errs_all, errs_all[:3])
    br.close()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
