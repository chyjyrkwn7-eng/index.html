#!/usr/bin/env python3
"""384 (profilerows, TEMPORARY): Profile's Customize / Badge case / Rank ladder behind ?pfrows=a|b|c.

Per device (iPhone 17 Pro Max installed, iPad Pro 11" installed) and class (academy, Fire Code), for no switch and for a, b, c:
  P1 no parameter: no .pfx anywhere, the three entry points are the build's own (.profile-customize-btn, .pf-case-count, .pf-goal-foot).
  P2 with a parameter: exactly Customize, Badge case and Rank ladder as .pfx buttons (data-pfx cz / bc / ld), the old three gone.
  P3 each is at least 44px each way, inside the screen (no sideways overflow of the page), and its preview well sits inside it.
  P4 the previews are drawn: Customize holds a banner and a character, the case holds the pins (an earned pin has art, the rest are
     empty slots), the ladder holds all seven rank emblems with exactly one lit as yours and one dashed as the next.
  P5 the New dot: Customize and the case carry one when the account has something unseen, and only then (Fire Code is seeded with none).
  P6 a tap on each goes where the old row went (Customize, the badge case, the rank ladder: the Profile screen is replaced).
  P7 no page error, no console error or warning, whatever the option.
  python3 tools/check-b384-profilerows.py [--quick] [--against REV|FILE]   (against origin/main: P2 onward FAIL - it has no options)"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "shoot-b384-profilerows.py")).read().rsplit("\nmain()", 1)[0]
sys.argv_saved = sys.argv; sys.argv = [sys.argv[0], "/dev/shm/pfrows-check"] + [a for a in sys.argv[1:] if a not in ("--quick",)]
G = {"__file__": os.path.join(HERE, "shoot-b384-profilerows.py"), "__name__": "pfc"}; exec(src, G)
L = G["L"]
from playwright.sync_api import sync_playwright
QUICK = "--quick" in sys.argv_saved
DEVS = ["phone-installed"] if QUICK else ["phone-installed", "ipad-pro-11"]
fails = []; n = 0
def chk(name, ok, detail=None):
    global n; n += 1
    if not ok: fails.append((name, detail))
    print(("ok   " if ok else "FAIL ") + name + ("" if ok or detail is None else "   " + json.dumps(detail)[:400]), flush=True)

PROBE = """()=>{
  const q = s => [...document.querySelectorAll('#stage .screen-profile ' + s)];
  const R = e => { const r = e.getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; };
  const pf = q('.pfx');
  const info = pf.map(b => { const o = { kind: b.dataset.pfx, r: R(b), label: (b.querySelector('.pfx-label')||{}).textContent };
    const pv = b.querySelector('.pfx-prev > *'); o.pv = pv ? R(pv) : null;
    o.banner = !!b.querySelector('.pfx-banner .bnr'); o.char = !!b.querySelector('.pfx-char svg');
    o.pins = b.querySelectorAll('.pfx-pin').length; o.earned = [...b.querySelectorAll('.pfx-pin.is-earned')].filter(p => p.querySelector('svg')).length;
    o.empty = b.querySelectorAll('.pfx-pin.is-empty').length;
    o.nodes = b.querySelectorAll('.pfx-node').length; o.nodeSvgs = b.querySelectorAll('.pfx-node > svg').length;
    o.here = b.querySelectorAll('.pfx-node.is-here').length; o.next = b.querySelectorAll('.pfx-node.is-next').length;
    o.dot = !!b.querySelector('.new-dot'); return o; });
  return { pfx: info, old: { cz: q('.profile-customize-btn').length, bc: q('.pf-case-count').length, ld: q('.pf-goal-foot').length },
    sw: document.documentElement.scrollWidth, vw: innerWidth, fresh: { cz: customizeNewCount(), bc: badgeNewCount() }, stageKids: document.getElementById('stage').children.length,
    onProfile: !!document.querySelector('#stage .screen-profile') }; }"""

def main():
    srv, url = L.g["serve"]()
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=L.g["CHROME"])
        for dev in L.DEVICES:
            if dev["name"] not in DEVS: continue
            for cls in ("academy", "ifc"):
                for opt in ("none", "a", "b", "c"):
                    tag = "%s|%s|%s" % (dev["name"], cls, opt)
                    ctx, pg, errs = G["open_pf"](br, dev, cls, opt)
                    cons = []
                    pg.on("console", lambda m: cons.append(m.type + ": " + m.text[:160]) if m.type in ("error", "warning") else None)
                    pg.goto(url + ("?pfrows=" + opt if opt != "none" else ""), wait_until="load", timeout=180000); pg.wait_for_timeout(3500)
                    want = {"badges": 12 if cls == "ifc" else 7, "freshBadges": 2 if cls == "academy" else 0, "freshChar": cls == "academy", "level": 36 if cls == "academy" else 27, "banner": ""}
                    pg.evaluate(G["SETUP"], want); pg.wait_for_timeout(700)
                    s = pg.evaluate(PROBE)
                    if opt == "none":
                        chk(tag + " P1 no .pfx, the build's own three", not s["pfx"] and s["old"]["cz"] == 1 and s["old"]["bc"] == 1 and s["old"]["ld"] == 1, s["old"])
                    else:
                        kinds = sorted(p["kind"] for p in s["pfx"])
                        chk(tag + " P2 three .pfx (cz bc ld), the old three gone", kinds == ["bc", "cz", "ld"] and not any(s["old"].values()), {"kinds": kinds, "old": s["old"]})
                        P = {p["kind"]: p for p in s["pfx"]}
                        if kinds == ["bc", "cz", "ld"]:
                            chk(tag + " P3 each >= 44px, inside the screen, no sideways overflow",
                                all(p["r"][2] >= 44 and p["r"][3] >= 44 and p["r"][0] >= -0.5 and p["r"][0] + p["r"][2] <= s["vw"] + 0.5 for p in s["pfx"]) and s["sw"] <= s["vw"],
                                {"rects": [p["r"] for p in s["pfx"]], "sw": s["sw"], "vw": s["vw"]})
                            chk(tag + " P3b the preview inside its button",
                                all(p["pv"] and p["pv"][0] >= p["r"][0] - 1 and p["pv"][0] + p["pv"][2] <= p["r"][0] + p["r"][2] + 1 and p["pv"][1] >= p["r"][1] - 1 and p["pv"][1] + p["pv"][3] <= p["r"][1] + p["r"][3] + 1 for p in s["pfx"]))
                            nb = want["badges"]
                            chk(tag + " P4 previews drawn: banner + character, pins (earned with art, empties), seven emblems one yours one next",
                                P["cz"]["banner"] and P["cz"]["char"] and P["bc"]["earned"] >= min(3, nb) and P["bc"]["pins"] >= 3 and P["bc"]["earned"] + P["bc"]["empty"] == P["bc"]["pins"]
                                and P["ld"]["nodes"] == 7 and P["ld"]["nodeSvgs"] == 7 and P["ld"]["here"] == 1 and P["ld"]["next"] == 1, P)
                            chk(tag + " P5 New dots only where something is unseen", P["cz"]["dot"] == (s["fresh"]["cz"] > 0) and P["bc"]["dot"] == (s["fresh"]["bc"] > 0), {"fresh": s["fresh"], "cz": P["cz"]["dot"], "bc": P["bc"]["dot"]})
                            for k in ("cz", "bc", "ld"):
                                ok = False
                                try:
                                    pg.evaluate("()=>window.scrollTo(0,0)"); pg.wait_for_timeout(150)
                                    pg.evaluate("k=>document.querySelector('#stage .screen-profile [data-pfx=' + k + ']').click()", k); pg.wait_for_timeout(900)
                                    ok = not pg.evaluate("()=>!!document.querySelector('#stage .screen-profile')")
                                except Exception as e: ok = False
                                chk(tag + " P6 a tap on %s leaves Profile" % k, ok)
                                pg.evaluate("()=>showProfile('profile')"); pg.wait_for_timeout(900)
                    chk(tag + " P7 no page or console error", not errs and not cons, {"errs": errs, "console": cons[:4]})
                    ctx.close()
        br.close()
    print("\n%d checks, %d failed" % (n, len(fails)))
    for f in fails: print("  FAIL", f[0], json.dumps(f[1])[:300] if f[1] is not None else "")
    sys.exit(1 if fails else 0)
main()
