#!/usr/bin/env python3
"""Build 385 r17: one privacy switch per class, under the master.

Madison: "The words Fire Code and Police Academy aren't centered right, they are too high." / "Shouldn't each class get its own toggle though
to be shown? The toggles would disappear if you turn off the top toggle? Or they would be greyed out in the off position. If you turn the
toggle on, they both turn on automatically."

Settings > Leaderboard & Privacy, for an account in both classes, in each class's Settings:
 (1) a section "Shown in" with one REAL switch row per class the account is in (same markup as the master row and the other Settings pages'
     switches), the Police Academy and Fire Code, each a 44px+ target;
 (2) the master reads on while any class is on; OFF turns both off and greys them (disabled, in the off position, still visible); ON turns
     both on at once; one class's switch off leaves the other as it was; the master goes off, and the rows grey, once the last one is;
 (3) each switch adds or removes only that class's board row (the in-memory cloud): Fire Code's from either class, the academy's when the
     academy next opens (a choice for the other class is applied when its page loads, and the row says so until then);
 (4) the words are centred in their rows: the label and the switch on the row's middle line, at the phone's size, on a tablet and at his
     page zoom (html.page-zoomed, --zc), with the class switches on and with them greyed;
 (5) one class: no list (the master alone), as before; no page errors.
Labels are read off the page; shapes are asserted.

  python3 tools/check-b384-privacy.py [--against OLD/index.html]      (must FAIL on the build before)"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ARGV = list(sys.argv)
src = open(os.path.join(HERE, "check-b384-fcboard.py")).read().split("\nwith sync_playwright() as pw:")[0]
F = {"__file__": os.path.join(HERE, "check-b384-fcboard.py"), "__name__": "b385pv"}
exec(src, F)
G, g = F["G"], F["g"]
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:500], flush=True)
class section:
    def __init__(self, name): self.name = name
    def __enter__(self): return self
    def __exit__(self, t, v, tb):
        if v is not None: chk(self.name + ": raised %s: %s" % (t.__name__, str(v)[:200]), False)
        return True
OWNER, CODE = G["OWNER"], G["CODE"]
BOARD = "lb-ifc-v1"
PENDING = "class26e.ifc.pendingboard."
TWO = "()=>{ enrolledClasses = () => ['academy', 'ifc']; }"
OPEN = "()=>{ showAppearance({ page: 'rankings' }); }"
READ = """()=>{ const s = document.querySelector('#stage'); const M = s.querySelector('.settings-card > label.opt:not(.settings-lb-class)');
  const sig = l => l ? [l.tagName, l.className.replace(/ ?(is-locked|settings-lb-class)/g, '').trim(), [...l.children].map(c => c.tagName + '.' + c.className).join(','), l.querySelector('input').type].join('|') : null;
  const rows = [...s.querySelectorAll('.settings-lb-class')].map(r => { const i = r.querySelector('input'); const q = r.getBoundingClientRect(); const n = r.querySelector('.ohint');
    return { cls: r.dataset.cls, label: r.querySelector('.otext').firstChild.textContent, checked: i.checked, disabled: i.disabled, locked: r.classList.contains('is-locked'),
             opacity: +getComputedStyle(r).opacity, h: q.height, w: q.width, shown: q.width > 0 && q.height > 0, note: n ? n.textContent : '', sig: sig(r) }; });
  const head = s.querySelector('#settings-rankings-classes');
  return { master: { checked: M.querySelector('input').checked, disabled: M.querySelector('input').disabled, sig: sig(M), hint: (M.querySelector('.ohint')||{}).textContent || '' },
           head: head ? head.textContent : null, rows, text: s.innerText }; }"""
# the ink of each row: its label's text and its switch against the row's middle line (CSS px), and the 44px target
CENTRE = """()=>{ return [...document.querySelectorAll('#stage .settings-lb-class')].map(r => { const q = r.getBoundingClientRect(), mid = q.top + q.height / 2;
    const t = r.querySelector('.otext'), rg = document.createRange(); rg.selectNodeContents(r.querySelector('.ohint') ? t : t.firstChild); const L = rg.getBoundingClientRect();   /* a row with a note: its two lines together */
    const b = r.querySelector('.box').getBoundingClientRect(); const z = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--zc')) || 1;
    const hit = document.elementFromPoint(q.left + q.width / 2, mid); return { cls: r.dataset.cls, dLabel: (L.top + L.height / 2) - mid, dBox: (b.top + b.height / 2) - mid, h: q.height, z,
      hit: !!hit && !!hit.closest('.settings-lb-class') }; }); }"""
def toggle(pg, which):
    """a tap on a switch: 'master' or a class key"""
    pg.evaluate("""(w)=>{ const s = document.querySelector('#stage'); const i = w === 'master' ? s.querySelector('.settings-card > label.opt:not(.settings-lb-class) input') : s.querySelector('.settings-lb-class[data-cls=' + w + '] input'); i.click(); }""", which)
    pg.wait_for_timeout(900)
def fire_rows(pg): return (pg.evaluate("()=>window.__cloud.vrooms['%s']" % BOARD) or {}).get("rows") or {}
def acad_row(pg): return pg.evaluate("(p)=>(window.__cloud.leaderboard || {})[p] || null", OWNER)
def pend(pg, k):
    return pg.evaluate("(a)=>{ try{ return JSON.parse(localStorage.getItem(a) || 'null'); }catch(e){ return null; } }", PENDING + k)
def wait_for(pg, js, arg=None, tries=40):
    for _ in range(tries):
        v = pg.evaluate(js, arg) if arg is not None else pg.evaluate(js)
        if v: return v
        pg.wait_for_timeout(300)
    return v

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    errs_all = []
    F["ifc_copy"](True)
    # ================= Fire Code's Settings, in both classes =================
    ctx, pg, errs = F["new_ctx"](br, G["init"]("ifc"), F["cloud0"]())
    pg.wait_for_timeout(2400)
    with section("Fire Code"):
        pg.evaluate(TWO); pg.evaluate(OPEN); pg.wait_for_timeout(1200)
        r = pg.evaluate(READ)
        chk("(1) Fire Code's page: a 'Shown in' section with a switch row for each class the account is in, in order (%s)" % [x["label"] for x in r["rows"]],
            r["head"] and len(r["rows"]) == 2 and [x["cls"] for x in r["rows"]] == ["academy", "ifc"] and all(x["sig"] == r["master"]["sig"] for x in r["rows"]), r)
        chk("(1) ...each a 44px+ target with the switch in it (%s)" % [round(x["h"]) for x in r["rows"]], all(x["h"] >= 44 and x["w"] >= 200 for x in r["rows"]), r["rows"])
        chk("(2) both classes on: the master reads on, the class switches are on and live",
            r["master"]["checked"] and all(x["checked"] and not x["disabled"] and not x["locked"] for x in r["rows"]), r)
        chk("(2) the hint explains it in one sentence (%s)" % r["master"]["hint"][:120], len(re.findall(r"[.!?](\s|$)", r["master"]["hint"].strip())) == 1 and "below" in r["master"]["hint"], r["master"]["hint"])
        # Fire Code off on its own: the other as it was, the master still on, Fire Code's row off the board, the academy's untouched
        toggle(pg, "ifc"); r = pg.evaluate(READ)
        gone = wait_for(pg, "(o)=>!(window.__cloud.vrooms['%s'].rows || {})[o]" % BOARD, OWNER)
        chk("(2)(3) Fire Code's switch off: only it is off, the master stays on, and only Fire Code's row comes off its board (%s)" % sorted(fire_rows(pg)),
            r["master"]["checked"] and [x["checked"] for x in r["rows"]] == [True, False] and not any(x["disabled"] for x in r["rows"]) and gone
            and set(fire_rows(pg)) == set(F["FIRE_ROWS"]) and not pend(pg, "academy"), r)
        # the academy off as well (the other class's page: a pending choice), the master off and both greyed
        toggle(pg, "academy"); r = pg.evaluate(READ); pa = pend(pg, "academy")
        chk("(2) the last class off: the master goes off, both class switches are off and greyed - disabled, in the off position, still shown (opacity %s)" % [round(x["opacity"], 2) for x in r["rows"]],
            not r["master"]["checked"] and all((not x["checked"]) and x["disabled"] and x["locked"] and x["opacity"] < .6 and x["shown"] for x in r["rows"]), r)
        chk("(3) the academy's choice is left for the academy's page, and the row says so until then (%s / %s)" % (pa, [x["note"] for x in r["rows"]]),
            pa and pa["on"] is False and r["rows"][0]["note"] and not r["rows"][1]["note"], (pa, r["rows"]))
        chk("(3) nothing of the academy's board is touched from Fire Code: its row is where it was",
            acad_row(pg) is not None and not [w for w in G["writes_of"](pg) if w.startswith("leaderboard/")], G["writes_of"](pg))
        # the master on: both on at once
        toggle(pg, "master"); r = pg.evaluate(READ)
        back = wait_for(pg, "(o)=>!!(window.__cloud.vrooms['%s'].rows || {})[o]" % BOARD, OWNER)
        chk("(2)(3) the master on: both on, live again, Fire Code's row is back and the academy's pending 'off' is cleared (%s)" % pend(pg, "academy"),
            r["master"]["checked"] and all(x["checked"] and not x["disabled"] and not x["locked"] for x in r["rows"]) and back and not pend(pg, "academy"), r)
        # the master off: both off at once, Fire Code's row off, the academy's off pending
        toggle(pg, "master"); r = pg.evaluate(READ)
        gone = wait_for(pg, "(o)=>!(window.__cloud.vrooms['%s'].rows || {})[o]" % BOARD, OWNER)
        chk("(2)(3) the master off: both off and greyed, Fire Code's row off its board, the academy's choice pending off",
            not r["master"]["checked"] and all(x["disabled"] and not x["checked"] for x in r["rows"]) and gone and (pend(pg, "academy") or {}).get("on") is False, r)
        errs_all += errs
        # centring: phone, a tablet, and his page zoom; with the switches live and greyed
        for tag, w, h, zoom in (("phone", 440, 956, 1), ("tablet", 834, 1194, 1), ("his page zoom", 518, 1125, 518 / 440)):
            pg.set_viewport_size({"width": w, "height": h}); pg.wait_for_timeout(500)
            for state in ("greyed", "live"):
                if pg.evaluate(READ)["master"]["checked"] != (state == "live"): toggle(pg, "master")
                pg.evaluate("(z)=>{ const r = document.documentElement; if(z > 1.02){ r.classList.add('page-zoomed'); r.style.setProperty('--zc', z.toFixed(3)); } else { r.classList.remove('page-zoomed'); r.style.setProperty('--zc', '1'); } }", zoom)
                pg.wait_for_timeout(500)
                c = pg.evaluate(CENTRE)
                worst = max([abs(x["dLabel"]) for x in c] + [abs(x["dBox"]) for x in c]) if c else 99
                chk("(4) %s, switches %s: the label and the switch are on each row's middle line (worst %.2f px) and the row is a 44px+ target (%s)" % (tag, state, worst, [round(x["h"]) for x in c]),
                    len(c) == 2 and worst <= 1.0 and all(x["h"] >= 44 and x["hit"] for x in c), c)
        ctx.close()

    # ================= the academy's Settings: its own switch live, Fire Code's from here, and the pending choice applied =================
    ifcs = None
    ctx, pg, errs = F["new_ctx"](br, G["init"]("academy"), F["cloud0"]())
    pg.wait_for_timeout(2400)
    with section("academy"):
        pg.evaluate(TWO)
        # Fire Code has a row of its own on its board (as its page would have written it)
        pg.evaluate("(a)=>{ window.__cloud.vrooms['%s'].rows[a.o] = { firstName: 'Maddox', level: 20, hundos: 5 }; }" % BOARD, {"o": OWNER})
        pg.evaluate(OPEN); pg.wait_for_timeout(1200)
        r = pg.evaluate(READ)
        chk("(1) the academy's page: the same section, both classes, switches on (%s)" % [(x["label"], x["checked"]) for x in r["rows"]],
            r["head"] and [x["cls"] for x in r["rows"]] == ["academy", "ifc"] and all(x["checked"] and x["sig"] == r["master"]["sig"] for x in r["rows"]) and r["master"]["checked"], r)
        toggle(pg, "ifc"); r = pg.evaluate(READ)
        gone = wait_for(pg, "(o)=>!(window.__cloud.vrooms['%s'].rows || {})[o]" % BOARD, OWNER)
        pf = pend(pg, "ifc")
        chk("(2)(3) Fire Code's switch off from the academy: only it is off, the master stays on, Fire Code's row comes off at once and its page is told (%s)" % pf,
            [x["checked"] for x in r["rows"]] == [True, False] and r["master"]["checked"] and gone and pf and pf["on"] is False and set(fire_rows(pg)) == set(F["FIRE_ROWS"]) and r["rows"][1]["note"], r)
        chk("(3) ...and the academy's own row is still on its board", acad_row(pg) is not None)
        toggle(pg, "academy"); r = pg.evaluate(READ)
        chk("(2) the academy's own switch off too: the master off, both greyed", not r["master"]["checked"] and all(x["disabled"] and x["locked"] and not x["checked"] for x in r["rows"]), r)
        st = pg.evaluate("()=>({ opt: store.leaderboardOptIn, changed: store.leaderboardOptInChanged })")
        pg.evaluate("()=>{ pushToCloud(true); }")
        gone = wait_for(pg, "(o)=>!(window.__cloud.leaderboard || {})[o]", OWNER)
        chk("(3) the academy's switch off takes the academy's row off its board, as an opt-out always has (%s)" % st, st["opt"] is False and gone, st)
        toggle(pg, "master"); r = pg.evaluate(READ)
        pf = pend(pg, "ifc")
        chk("(2) the master on from the academy: both on; Fire Code's pending 'off' is cleared (its saved copy is on)", r["master"]["checked"] and all(x["checked"] and not x["disabled"] for x in r["rows"]) and pf is None, (r, pf))
        # Fire Code off again from here, to be applied by its page
        toggle(pg, "ifc"); wait_for(pg, "(o)=>!(window.__cloud.vrooms['%s'].rows || {})[o]" % BOARD, OWNER)
        state = ctx.storage_state()
    errs_all += errs; ctx.close()
    # ---- Fire Code's page loads: it applies what the academy chose for it, and does not publish ----
    with section("applied"):
        for o in state.get("origins", []):
            o["localStorage"] = [kv for kv in o.get("localStorage", []) if kv["name"] != "class26e.activeclass"] + [{"name": "class26e.activeclass", "value": "ifc"}]
        ctx = br.new_context(viewport={"width": 440, "height": 956}, has_touch=True, storage_state=state)
        ctx.add_init_script("window.__cloudSeed = %s;" % json.dumps(F["cloud0"]())); ctx.add_init_script(G["FAKE"]); ctx.add_init_script(g["STANDALONE"])
        pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
        pg.route("**/index.html", lambda route, request, b=(open(os.path.join(os.path.dirname(HERE), "index.html"), encoding="utf-8").read() if "--against" not in ARGV else open(ARGV[ARGV.index("--against") + 1], encoding="utf-8").read()): route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=g["INSET_RE"].sub("0px", b)))
        pg.goto(F["G"]["serve_url"]); pg.wait_for_timeout(3800); pg.evaluate("document.getElementById('splashscreen')?.remove()")
        s = pg.evaluate("()=>({ cls: window.NOVA_CLASS, opt: store.leaderboardOptIn, changed: store.leaderboardOptInChanged })")
        pg.wait_for_timeout(2500)
        chk("(3) Fire Code's page applies the academy's choice as it loads: off, the pending note cleared, nothing published (%s)" % s,
            s["cls"] == "ifc" and s["opt"] is False and pend(pg, "ifc") is None and OWNER not in fire_rows(pg), (s, fire_rows(pg).keys()))
        errs_all += errs; ctx.close()

    # ================= one class: the master alone =================
    F["ifc_copy"](True)
    ctx, pg, errs = F["new_ctx"](br, G["init"]("ifc"), F["cloud0"]())
    pg.wait_for_timeout(2200)
    with section("one class"):
        pg.evaluate("()=>{ enrolledClasses = () => ['ifc']; }"); pg.evaluate(OPEN); pg.wait_for_timeout(1200)
        r = pg.evaluate(READ)
        chk("(5) in one class there is the master and no list", r["head"] is None and not r["rows"] and r["master"]["checked"], r)
    errs_all += errs; ctx.close()
    chk("no page errors", not errs_all, errs_all[:3])
    br.close()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
