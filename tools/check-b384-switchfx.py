#!/usr/bin/env python3
"""Build 384 r21: switching class (Police Academy <-> Fire Code) is one smooth motion from the tap to the new class's settled Home.

Madison: "There's a bad transition when switching between classes."

A switch is a reload into the other class's data (two class stores, themes, characters), so what is judged here is what a person
SEES between the tap and the settled Home, measured two ways at once on the wall clock (tools/b384_switchfx_lib.py): the compositor's
own frames (a CDP screencast: each frame's light and edges) and the page's own frames (an rAF log kept across the reload: the cover, the
splash, the word on each, Home's parts, the tab bar, the status bar's colour). The real switch is driven - the class button, its list,
the tap on the class - at an iPhone 17 Pro Max (440x956, installed), an iPhone SE (375x667, installed) and a laptop (1440x900, a browser
tab), both ways, then at 4x CPU, with reduced motion, from Settings, and with the reload that never comes.

What was wrong (build 384.6, measured):
  (1) the cover held 2.5s from the tap whatever Home was doing - Home was built at ~1s and waited 1.5s behind it - and lifted over .75s:
      3.3s+ from tap to Home on a fast machine;
  (2) the cover's word and bar came in at once over Home's own NOVA (the word twice) and, going out, the splash's NOVA faded over Home's
      NOVA again, drifting back 4% as it went (a scale, not just opacity);
  (3) the class list stayed open, under the cover, until the page went;
  (4) the splash's line changed under the planet ("syncing...", "booting...", "ready.") for a screen that was only waiting;
  (5) in a browser tab the bars kept the class left's tint under the cover until the reload;
  (6) from a sign-in or a sign-up (enterAccountClass) the screen was emptied FIRST and the cover faded in over a blank stage;
  (7) with reduced motion the cover and the lift were hard cuts (every transition is off), not a cross-fade;
  (8) Home was not eased in: it was simply there under a thinning splash.

  python3 tools/check-b384-switchfx.py                                   (all)
  python3 tools/check-b384-switchfx.py --against /path/to/old-index.html (must FAIL)
  ONLY=phone,laptop python3 tools/check-b384-switchfx.py                 (sections: phone se laptop cpu4 reduce settings giveup)
  SWITCHFX_SHOTS=/some/folder python3 tools/check-b384-switchfx.py       (a contact sheet of each switch)
"""
import os, sys, time, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b384_switchfx_lib as L
from playwright.sync_api import sync_playwright

ONLY = set(x for x in os.environ.get("ONLY", "").split(",") if x)
SHOTS = os.environ.get("SWITCHFX_SHOTS")
def want(sec): return not ONLY or sec in ONLY

fails = []
def chk(name, cond, info=""):
    print(("  PASS " if cond else "  FAIL ") + name + ("" if cond else "  -> " + str(info)[:500]), flush=True)
    if not cond: fails.append(name)

COVER_RGB = (10, 10, 10)
# the budgets: tap to the cover gone, and Home built to the cover gone (what the switch itself controls; the rest is the page loading,
# which a slower machine stretches). 4x CPU is what a phone is next to this machine.
BUDGET = {1: {"total": 2.8, "hold": 1.0, "lift": .6}, 4: {"total": 6.5, "hold": 2.0, "lift": .9},
          "laptop": {"total": 4.0, "hold": 1.5, "lift": 1.2}}       # a 1440x900 screencast through software rendering is the slowest thing here

def metrics(run, calm=False):
    """the switch as numbers, ms from the tap"""
    t0 = run["t_tap"] * 1000; to = run["to"]
    marks = {e["mark"]: e["t"] - t0 for e in run["log"] if "mark" in e and e["t"] - t0 > -50}
    E = [(e["t"] - t0, e) for e in run["log"] if "mark" not in e]
    old = [(t, e) for t, e in E if e["cls"] != to and t >= -50]
    new = [(t, e) for t, e in E if e["cls"] == to]
    m = {"old": old, "new": new, "marks": marks}
    m["cover_on"] = next((t for t, e in old if e["cover"] and (e["coverOp"] or 0) > .01), None)
    m["cover_full"] = next((t for t, e in old if e["cover"] and (e["coverOp"] or 0) >= .99), marks.get("coverend"))
    if m["cover_full"] is None and old: m["cover_full"] = old[-1][0]      # (the page went before a frame or the transition's end saw it whole)
    m["new_start"] = new[0][0] if new else None
    built = lambda e: e["home"] and e["hero"] and e["greet"] and e["start"] and e["tabs"] >= 1
    m["built"] = next((t for t, e in new if built(e)), None)
    # the lift, from the page's own event (a frame may not have sampled it), the end of the fade from its transitionend
    m["lift"] = marks.get("lift")
    if m["lift"] is None:
        m["lift"] = next((t for t, e in new if e["splash"] is not None and e["splash"] < .99 and (m["built"] is not None and t >= m["built"] - 5)), None)
    # where the fade is first SEEN under way (a frame): the first frames of a lift are a style pass on a big page, not the fade
    m["lift_seen"] = next((t for t, e in new if e["splash"] is not None and e["splash"] < .99 and m["lift"] is not None and t >= m["lift"] - 5), m["lift"])
    m["clear"] = marks.get("fadeend")
    if m["clear"] is None:
        m["clear"] = next((t for t, e in new if m["lift"] is not None and t >= m["lift"] and (e["splash"] is None or e["splash"] <= .02)), None)
    m["gone"] = marks.get("gone")
    if m["gone"] is None:
        m["gone"] = next((t for t, e in new if m["lift"] is not None and t >= m["lift"] and e["splash"] is None), None)
    m["final"] = new[-1][1] if new else {}
    return m

def light(run):
    t0 = run["t_tap"]; out = []
    for ts, jpg in run["frames"]:
        x = L.lum_of(jpg); x["dt"] = (ts - t0) * 1000; out.append(x)
    return out

def judge(tag, run, cpu=1, calm=False, laptop=False, via="sheet", expect_tabs=True):
    cpu = "laptop" if laptop else cpu
    m = metrics(run, calm); fr = light(run); f = m["final"]
    P = lambda s: "%s %s" % (tag, s)
    ok = m["cover_on"] is not None and m["built"] is not None and m["lift"] is not None and m["gone"] is not None
    chk(P("the switch ran end to end (cover on %s, new page %s, Home built %s, lift %s, cover gone %s ms)" % (
        m["cover_on"] and round(m["cover_on"]), m["new_start"] and round(m["new_start"]), m["built"] and round(m["built"]), m["lift"] and round(m["lift"]), m["gone"] and round(m["gone"]))), ok,
        {k: v for k, v in m.items() if k in ("cover_on", "cover_full", "new_start", "built", "lift", "clear", "gone")})
    if not ok: return m
    B = BUDGET[cpu]
    chk(P("(1) tap to the cover gone in %.2fs (budget %.1fs)" % (m["gone"] / 1000, B["total"])), m["gone"] / 1000 <= B["total"], m["gone"])
    chk(P("(1b) Home built to the cover lifting %.2fs (budget %.2fs): the cover does not wait on a clock" % ((m["lift"] - m["built"]) / 1000, B["hold"])), (m["lift"] - m["built"]) / 1000 <= B["hold"], (m["built"], m["lift"]))
    td = max([e["sd"] or 0 for t, e in m["new"] if m["lift"] is not None and t >= m["lift"] + 30 and e["splash"] is not None] or [0])
    chk(P("(1c) the lift is a %.2fs fade (at most %.2fs), seen through in %.2fs (budget %.2fs)" % (td, .35 if not calm else .2, (m["clear"] - m["lift_seen"]) / 1000, B["lift"] if not calm else .3)),
        m["clear"] is not None and 0 < td <= (.35 if not calm else .2) and (m["clear"] - m["lift_seen"]) / 1000 <= (B["lift"] if not calm else .3), (td, m["lift_seen"], m["clear"]))

    # (2) the word twice: the cover's mark ahead of its cover, coming in; the cover's mark over Home's own, going out
    ahead = max([e["grp"] or 0 for t, e in m["old"] if e["cover"] and (e["coverOp"] or 0) < .7] or [0])
    if not calm:
        chk(P("(2) the cover's mark does not come in ahead of its cover (mark %.2f while the cover is under .7)" % ahead), ahead <= .15, ahead)
    ink = [min((e["splash"] or 0) * (e["grp"] if e["grp"] is not None else 1), (e["greetOp"] or 0) * (1 - (e["splash"] or 0)))
           for t, e in m["new"] if e["splash"] is not None and e["splash"] < .99]
    if not calm:    # (reduced motion's plain cross-fade shows both for its .14s by design)
        chk(P("(2b) the cover's word and Home's word are never both on show (worst %.2f)" % max(ink or [0])), max(ink or [0]) <= .2, max(ink or [0]))
    sc = [float(e["grpScale"]) for t, e in m["new"] if e["grpScale"] not in (None, "none")]
    chk(P("(2c) the cover leaves in opacity alone: its mark never scales (largest scale %s)" % (max(sc) if sc else "none")), not sc or max(sc) <= 1.001, sc[:3])

    # (3) the list closes into the class button as the cover comes in
    if via == "sheet":
        open_late = [round(t) for t, e in m["old"] if e["cover"] and (e["coverOp"] or 0) >= .99 and e["sheet"]]
        chk(P("(3) the class list is shut by the time the cover is over the screen"), not open_late, open_late[:3])
        # and Home stays stepped back behind the cover: it does not brighten as the list folds (no frame brighter than the open list's)
        pre = [x["lum"] for x in fr if -900 <= x["dt"] < 20]
        up = [x["lum"] for x in fr if 20 <= x["dt"] < (m["cover_full"] or 400)]
        chk(P("(3b) Home does not brighten as the list folds into the button (open list %.1f, brightest after %.1f)" % (max(pre or [0]), max(up or [0]))), not up or not pre or max(up) <= max(pre) + 2, (max(pre or [0]), max(up or [0])))
    else:
        emptied = [round(t) for t, e in m["old"] if not e["stage"] and (e["coverOp"] or 0) < .99]
        chk(P("(6) the screen is never emptied before the cover is over it (a blank stage under the fade)"), not emptied, emptied[:3])

    # (4) one line on the splash: it never reads "ready."/"syncing" - that is checked as a fixed text in the source below

    # (5) the bars: in a browser tab the status bar's colour is the cover's from the cover on until the lift
    if laptop:
        # (the bars are handed back as the lift starts, in the same frame that the cover begins to thin: that frame is the lift's)
        under = [(round(t), e["tc"]) for t, e in m["old"] + m["new"] if (e["cover"] and (e["coverOp"] or 0) >= .98) or (e["splash"] is not None and e["splash"] >= .98 and t < m["lift"] - 40)]
        wrong = [x for x in under if (x[1] or "").upper() != "#0A0A0A"]
        chk(P("(5) the status bar is the cover's colour for as long as the cover is on (%d frames, %d other: %s)" % (len(under), len(wrong), wrong[:3])), under and not wrong, wrong[:4])
        chk(P("(5b) and the app's own once it lifts (%s)" % (f.get("tc"))), (f.get("tc") or "").upper() != "#0A0A0A", f.get("tc"))

    # (6b) nothing of the new page is on show before its cover lifts, and Home is whole in the first frame of the lift
    new_pre = [(round(t), e["tabs"], e["home"]) for t, e in m["new"] if m["lift"] is not None and t < m["lift"] and not (e["pre"] or (e["splash"] is not None and e["splash"] >= .98))]
    chk(P("(6b) every frame of the new page before the lift is under the cover"), not new_pre, new_pre[:3])
    first = next(e for t, e in m["new"] if t >= m["lift"])
    chk(P("(6c) in the first frame of the lift Home is whole: planet, greeting, button and %d tabs (%s)" % (first["tabs"], first["labels"])),
        bool(first["hero"] and first["greet"] and first["start"] and first["tabs"] == f.get("tabs") and first["labels"] == f.get("labels") and first["tabs"] >= 1), [first, f.get("labels")])
    pre_tabs = {(e["tabs"], e["labels"]) for t, e in m["new"] if e["tabs"] and t >= m["lift"] - 5}
    chk(P("(6d) the tab bar never shows any set but the new class's (%s)" % sorted(pre_tabs)[:2]), len(pre_tabs) <= 1, sorted(pre_tabs))

    # (7) Home eases in as the cover lifts: the parts start in turn (three steps), a fade and a few px; reduced motion: the cover alone
    lift_e = [e for t, e in m["new"] if m["lift"] is not None and (m["lift"] - 5 if not calm else m["lift"] + 30) <= t <= m["lift"] + 700]   # (Home is hidden, not faded, until the lift's own frame)
    ops = {k: [e[k] if e[k] is not None else 1 for e in lift_e] for k in ("heroOp", "greetOp", "tabsOp")}
    if not calm:
        eased = {k: min(v or [1]) < .9 for k, v in ops.items()}
        half = {}
        for k in ops:
            half[k] = next((t for t, e in m["new"] if m["lift"] is not None and t >= m["lift"] - 5 and e[k] is not None and e[k] >= .5), None)
        spread = (max(half.values()) - min(half.values())) if all(v is not None for v in half.values()) else None
        in_turn = spread is not None and half["heroOp"] <= half["greetOp"] <= half["tabsOp"]
        chk(P("(7) Home's parts ease in (hero, greeting, tab bar all start below full: %s), in turn (halfway at %s), within %sms" % (eased, {k[:-2]: round(v) for k, v in half.items() if v is not None}, spread and round(spread))),
            all(eased.values()) and in_turn and spread <= 450, [eased, half])
    else:
        solid = all(min(v or [1]) >= .99 for v in ops.values())
        chk(P("(7) reduced motion: Home is not animated in (the cover alone cross-fades)"), solid, {k: min(v or [1]) for k, v in ops.items()})
        fade_in = [(round(t), e["coverOp"]) for t, e in m["old"] if e["cover"] and .05 < (e["coverOp"] or 0) < .95]
        fade_out = [(round(t), e["splash"]) for t, e in m["new"] if e["splash"] is not None and .05 < e["splash"] < .95]
        # (the way out is .14s: a frame may not have fallen inside it, so what the page declared for it counts too - a cut is a 0s transition)
        chk(P("(7b) reduced motion: a plain cross-fade both ways, not a cut (%d frames on the way in, %d on the way out, the way out declared %.2fs)" % (len(fade_in), len(fade_out), td)),
            len(fade_in) >= 1 and (len(fade_out) >= 1 or td > 0), (fade_in[:3], fade_out[:3], td))

    # the compositor's frames: no flash, no seam
    hold = [x for x in fr if m["cover_full"] is not None and m["new_start"] is not None and x["dt"] >= m["cover_full"] + 60 and x["dt"] <= m["lift"] - 40]
    if hold:
        med = sorted(x["lum"] for x in hold)[len(hold) // 2]
        steps = [abs(b["lum"] - a["lum"]) for a, b in zip(hold, hold[1:])]
        esteps = [max(abs(p - q) for p, q in zip(a["edge"], b["edge"])) for a, b in zip(hold, hold[1:])]
        chk(P("(8) under the cover the picture is steady: light %.1f (%.0f to %.0f), no frame steps more than %.1f in light or %.1f in the edges from the one before" % (
            med, min(x["lum"] for x in hold), max(x["lum"] for x in hold), max(steps or [0]), max(esteps or [0]))),
            max(steps or [0]) <= 4 and max(esteps or [0]) <= 6 and 10 <= min(x["lum"] for x in hold) and max(x["lum"] for x in hold) <= 40, (max(steps or [0]), max(esteps or [0]), med))
        homes = [x["lum"] for x in fr if x["dt"] < 0]
        flash = [round(x["dt"]) for x in fr if 0 <= x["dt"] <= m["lift"] and x["lum"] > max(homes or [0]) + 3]
        black = [round(x["dt"]) for x in fr if m["cover_full"] + 60 <= x["dt"] <= m["lift"] - 40 and x["lum"] < 6]
        chk(P("(8b) no white flash (a frame brighter than the screen left) and no black one (the cover's own light is %.0f)" % med), not flash and not black, (flash[:4], black[:4]))
        # the seam across the reload: the last frame before the page goes against the first after it
        gap_a = [x for x in fr if x["dt"] <= (m["old"][-1][0] if m["old"] else 0) + 20 and x["dt"] >= (m["cover_full"] or 0)]
        gap_b = [x for x in fr if x["dt"] >= m["new_start"] + 40 and x["dt"] <= m["new_start"] + 400]
        if gap_a and gap_b:
            a, b = gap_a[-1], gap_b[0]
            d = max(abs(p - q) for p, q in zip(a["edge"], b["edge"]))
            chk(P("(8c) no seam across the reload: the cover's edges before the page goes and after the new one's first frames differ by %.1f levels" % d), d <= 8, (a["edge"], b["edge"]))
    else:
        chk(P("(8) frames under the cover were captured"), False, len(fr))
    # the settled Home does not move again once the cover is gone
    after = [x for x in fr if m["gone"] + 80 <= x["dt"] <= m["gone"] + 330]   # (the "Welcome back" banner drops in after this)
    if len(after) > 3:
        d = max(max(abs(p - q) for p, q in zip(after[0]["edge"], x["edge"])) for x in after)
        chk(P("(8d) once the cover is gone Home's edges hold still (%.1f levels)" % d), d <= 8, d)
    return m

SRC_TXT = L.SRC

def sheet(run, name):
    if SHOTS:
        os.makedirs(SHOTS, exist_ok=True)
        L.contact_sheet(run, os.path.join(SHOTS, name + ".sheet.png"), step=2, cols=12, tw=120, start_ms=-100)

print("check-b384-switchfx against", L.SRC_PATH, "(build %s)" % L.BUILD, flush=True)
srv = L.Server()
with sync_playwright() as pw:
    # --------------------------------------------------------------------------------------------------- every device, both ways
    for dev, desc in (("phone", "iPhone 17 Pro Max, installed, 440x956"), ("se", "iPhone SE, installed, 375x667"), ("laptop", "a laptop browser tab, 1440x900")):
        if not want(dev): continue
        print("\n%s (%s), academy -> Fire Code -> academy, 1x CPU" % (dev, desc), flush=True)
        try:
            s = L.Session(pw, srv, dev).boot()
            for to in ("ifc", "academy"):
                r = s.switch(to)
                sheet(r, "%s-%s" % (dev, to))
                judge("%s to %s:" % (dev, "Fire Code" if to == "ifc" else "the academy"), r, 1, laptop=(dev == "laptop"))
                s.pg.wait_for_timeout(1200)
            chk("%s no page errors" % dev, not s.errs, s.errs[:3])
            s.close()
        except Exception as e:
            chk("%s ran" % dev, False, repr(e)[:400])
    # --------------------------------------------------------------------------------------------------- 4x CPU
    if want("cpu4"):
        print("\niPhone 17 Pro Max at 4x CPU (a phone next to this machine)", flush=True)
        try:
            s = L.Session(pw, srv, "phone").boot(); s.throttle(4)
            for to in ("ifc", "academy"):
                r = s.switch(to, limit=60)
                sheet(r, "phone-cpu4-%s" % to)
                judge("cpu4 to %s:" % ("Fire Code" if to == "ifc" else "the academy"), r, 4)
                s.pg.wait_for_timeout(1500)
            chk("cpu4 no page errors", not s.errs, s.errs[:3])
            s.close()
        except Exception as e:
            chk("cpu4 ran", False, repr(e)[:400])
    # --------------------------------------------------------------------------------------------------- reduced motion
    if want("reduce"):
        print("\nreduced motion (the app's own switch on, and the system's)", flush=True)
        try:
            s = L.Session(pw, srv, "phone", reduce_motion=True).boot()
            for to in ("ifc", "academy"):
                r = s.switch(to)
                sheet(r, "phone-reduce-%s" % to)
                judge("reduce to %s:" % ("Fire Code" if to == "ifc" else "the academy"), r, 1, calm=True)
                s.pg.wait_for_timeout(1000)
            chk("reduce no page errors", not s.errs, s.errs[:3])
            s.close()
        except Exception as e:
            chk("reduce ran", False, repr(e)[:400])
    # --------------------------------------------------------------------------------------------------- from Settings, from sign-in
    if want("settings"):
        print("\nthe same switch from Settings (a join, a leave) and from a sign-in (enterAccountClass)", flush=True)
        for via in ("settings", "enter"):
            try:
                s = L.Session(pw, srv, "phone").boot()
                r = s.switch("ifc", via=via)
                sheet(r, "phone-%s-ifc" % via)
                judge("%s to Fire Code:" % via, r, 1, via=via)
                chk("%s no page errors" % via, not s.errs, s.errs[:3])
                s.close()
            except Exception as e:
                chk("%s ran" % via, False, repr(e)[:400])
    # --------------------------------------------------------------------------------------------------- a reload that never comes
    if want("giveup"):
        print("\na reload that never comes: the cover gives the screen back (the page's clock run on a minute)", flush=True)
        try:
            srv2 = L.Server(no_reload=True)       # the page's own reload call is a no-op: the switch is under way and the page never goes
            s = L.Session(pw, srv2, "phone").boot()
            pg = s.pg
            pg.evaluate("()=>{ window.__fx.length = 0; }")
            s.tap(".class-bubble"); pg.wait_for_timeout(900)
            s.tap(".class-stack-item.is-ifc"); pg.wait_for_timeout(1500)
            up = pg.evaluate("()=>({ cover: !!document.getElementById('class-switch-loader'), op: getComputedStyle(document.getElementById('class-switch-loader') || document.body).opacity })")
            chk("giveup the cover is up while the reload is awaited (%s)" % up, up["cover"] and float(up["op"]) >= .99, up)
            pg.wait_for_timeout(60500)
            st = pg.evaluate("()=>({ cover: !!document.getElementById('class-switch-loader'), sw: document.documentElement.classList.contains('class-switching'), open: !!document.querySelector('.class-bubble-wrap.is-open'), dim: document.getElementById('stage').classList.contains('class-list-open'), cls: window.NOVA_CLASS })")
            chk("giveup after a minute the cover is gone, the list is shut and Home is not left dimmed (%s)" % st, not st["cover"] and not st["sw"] and not st["open"] and not st["dim"] and st["cls"] == "academy", st)
            s.close(); srv2.close()
        except Exception as e:
            chk("giveup ran", False, repr(e)[:400])
    # --------------------------------------------------------------------------------------------------- the words
    print("\nthe source", flush=True)
    import re
    chk("(4) a switch's splash says one line (no rotating 'syncing / booting / ready' for a screen that is only waiting)",
        "messages = [String(arrive.line)]" in SRC_TXT, "arrive line kept as the only message")
srv.close()
print("\nALL PASS" if not fails else "\nFAILED: %d" % len(fails))
sys.exit(1 if fails else 0)
