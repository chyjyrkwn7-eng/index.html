#!/usr/bin/env python3
"""The one input `firestore-admin.py merge-now --yes` cannot work out for itself.

A merge sets `mergeHold` on the target: the account as it stood before, so that whatever the
merge unlocks plays after that person's next test instead of landing on Home. The hold carries
the characters still LOCKED and the banners EARNED at that moment, and those come from the
app's own rules (lockedCharacterSet / earnedBannerSet) - hundreds of lines of unlock logic that
the tool does not copy. This script runs index.html in Chromium on the target's document, asks
the app, and writes the answer to a file for `merge-now --hold-file`. It also says what the
merge would newly unlock, so you can see whether a hold is needed at all (if nothing is
crossed, `merge-now --no-hold` is correct).

  python3 tools/merge-hold-probe.py OUT.json <old public id | name:First> [...] [--whole]

--whole ignores each note's base, to show what adding the old account WHOLE would unlock (the
double-count a naive merge would make); the hold file is the same either way.

READS ONLY. Needs the admin key (it reads `progress`). Prints accounts as acct1, acct2 ... and
public ids; never a sync code. OUT.json is keyed by the target's public id and holds character
and banner ids only.
"""
import copy
import functools
import http.server
import importlib.util
import json
import os
import socket
import sys
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"


def load_tool():
    spec = importlib.util.spec_from_file_location("fa", os.path.join(ROOT, "tools", "firestore-admin.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main(argv):
    whole = "--whole" in argv
    argv = [a for a in argv if a != "--whole"]
    if len(argv) < 3:
        print(__doc__)
        return 2
    out_path, specs = argv[1], argv[2:]
    fa = load_tool()
    if not fa.admin_ready():
        print("needs the admin key (NOVA_ADMIN_EMAIL / NOVA_ADMIN_PRIVATE_KEY)")
        return 2
    from playwright.sync_api import sync_playwright
    rows = fa.docs("progress", mask=["firstName", "publicId", "to"])
    names = {c: f.get("firstName") for c, f in rows}
    so = socket.socket(); so.bind(("127.0.0.1", 0)); port = so.getsockname()[1]; so.close()

    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    init = ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');"
            "localStorage.setItem('class26e.intro.seen','9');}catch(e){}")
    result = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME)
        ctx = br.new_context()
        ctx.add_init_script(init)
        pg = ctx.new_page()
        pg.goto("http://127.0.0.1:%d/index.html" % port)
        pg.wait_for_timeout(2500)
        for n, spec in enumerate(specs, 1):
            hit = fa._resolve_old(rows, spec)
            if len(hit) != 1:
                print("acct%d: %s names %d accounts with a merge note (need one)" % (n, spec, len(hit)))
                continue
            old_code = hit[0][0]
            note = dict(next(f for c, f in rows if c == old_code + fa.MERGE_NOTE_SUFFIX))
            to_code = note.get("to")
            refs = [("progress", old_code), ("progress", to_code), ("progress", old_code + fa.MERGE_NOTE_SUFFIX)]
            raw = fa._batch_get(refs)
            old, tgt, note = (fa._plain_doc(raw[r]) for r in refs)
            res = pg.evaluate("""(a)=>{
                applyLoadedData(JSON.parse(JSON.stringify(a.old)));
                let leaving = JSON.parse(JSON.stringify(store));
                if(a.note.base) leaving = progressSinceBase(leaving, a.note.base);
                applyLoadedData(JSON.parse(JSON.stringify(a.target)));
                const levelBefore = levelStateFor(store).level, rankBefore = rankOf(store);
                const before = { chars: [...lockedCharacterSet()], banners: [...earnedBannerSet()] };
                mergeLeavingAccount(leaving, a.note);
                const after = { chars: [...lockedCharacterSet()], banners: [...earnedBannerSet()] };
                return { before, after, levelBefore, levelAfter: levelStateFor(store).level,
                         rankBefore: JSON.stringify(rankBefore), rankAfter: JSON.stringify(rankOf(store)) };
            }""", {"old": old, "target": tgt, "note": {k: v for k, v in note.items() if k in ("base", "bonusLevels", "extra", "to", "at") and not (whole and k == "base")}})
            pid = tgt.get("publicId")
            result[pid] = {"chars": res["before"]["chars"], "banners": res["before"]["banners"]}
            unlocked = sorted(set(res["before"]["chars"]) - set(res["after"]["chars"]))
            newb = sorted(set(res["after"]["banners"]) - set(res["before"]["banners"]))
            print("acct%d (%s) -> %s: level %s -> %s, rank %s, characters newly unlocked %s, banners newly earned %s"
                  % (n, names.get(old_code), pid, res["levelBefore"], res["levelAfter"],
                     "changes" if res["rankBefore"] != res["rankAfter"] else "unchanged", unlocked or "none", newb or "none"))
        br.close()
    srv.shutdown()
    with open(out_path, "w") as fh:
        json.dump(result, fh, indent=1)
    print("wrote %s (character and banner ids only)" % out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
