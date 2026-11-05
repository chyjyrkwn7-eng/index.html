#!/usr/bin/env python3
"""Build 384 full check: Fire Code's secret characters are named as Fire Code names them.

The locked card of the three hidden secrets reads "Unlock X to see how to unlock Y", and the note under Umbra's and Whiteout's
tile "once you have X". Both were written with the academy's names (Void, Umbra, Horizon, Genesis) and read that way in Fire
Code too, where the four are the Breacher, Recon, Whiteout and Flashbang. Each class's names now come from
AVATAR_DISPLAY_NAME, which Fire Code rewrites with its own.

  python3 tools/check-b384-secretnames.py [--against OLD/index.html]   (must FAIL on the build before)
"""
import os, sys, re
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b384sn"}
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
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)
# every secret still locked, so each card asks for the one before it
READ = """()=>{ const s = store.seenUnlocks || (store.seenUnlocks = {}); store.mysteryColorsFound = {};
  ['voidwalker','umbra','singularity','genesis'].forEach(k => { try{ if(store.unlockedChars) delete store.unlockedChars[k]; }catch(e){} });
  const m = k => { try{ return characterLockMessage(k); }catch(e){ return 'ERR ' + e; } };
  const n = k => { try{ return unlockNoteFor({ kind: 'character', id: k }); }catch(e){ return 'ERR ' + e; } };
  return { names: ['voidwalker','umbra','singularity','genesis'].map(k => AVATAR_DISPLAY_NAME[k]),
           msgs: ['umbra','singularity','genesis'].map(m), notes: ['umbra','singularity'].map(n) }; }"""
ACADEMY = re.compile(r"\b(Void|Umbra|Horizon|Genesis)\b")
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    errs_all = []
    for cls in ("ifc", "academy"):
        ctx, pg, errs = G["page"](br, G["init"](G["ifc"] if cls == "ifc" else G["academy"], **({} if cls == "ifc" else {"active": "academy"})))
        r = pg.evaluate(READ); errs_all += errs; ctx.close()
        names = r["names"]
        if cls == "ifc":
            chk("(1) Fire Code names its four secrets its own way (%s)" % names, not any(ACADEMY.search(x or "") for x in names), names)
            bad = [x for x in r["msgs"] + r["notes"] if ACADEMY.search(x or "")]
            chk("(2) Fire Code: no locked secret's card or note names an academy character (%s)" % (r["msgs"] + r["notes"]), not bad, bad)
            chk("(3) Fire Code: each card names the one before and itself, by Fire Code's names",
                all(m and names[i] in m and names[i + 1] in m for i, m in enumerate(r["msgs"]) if m.startswith("Unlock ")) and
                any(m.startswith("Unlock ") for m in r["msgs"]), r["msgs"])
        else:
            chk("(4) the academy keeps Void, Umbra, Horizon and Genesis on its cards (%s)" % r["msgs"],
                all(m and ACADEMY.search(m) for m in r["msgs"] if m.startswith("Unlock ")) and any(m.startswith("Unlock ") for m in r["msgs"]), r["msgs"])
            chk("(5) the academy's notes name Void and Umbra (%s)" % r["notes"], "Void" in (r["notes"][0] or "") and "Umbra" in (r["notes"][1] or ""), r["notes"])
    chk("(6) no page errors", not errs_all, errs_all[:3])
    br.close()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
