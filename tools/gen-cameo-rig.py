#!/usr/bin/env python3
"""Generates the cameo rig's pose CSS (384 cameo, round 2) and writes it into index.html between its two markers:
"  /* ---- the poses (generated: tools/gen-cameo-rig.py) ---- */" and "  /* ---- leaving (CAMEO_OUT_MS 240)".
Run:  python3 tools/gen-cameo-rig.py [index.html]   (then check-js and check-b384-cameo.py --only S,J).
The cameo rig: every limb segment's static angle or keyframes, per kind.
Angles are CSS rotate() (clockwise; 0 = hanging straight down). Arm poses are given as glove targets and solved (two-bone IK)."""
import math, sys
UA, FA = .17, .16          # joint lengths (em of the figure)
SH = (.2, .93)             # the typical left shoulder pivot (CAMEO_SHOULDER; the right is mirrored about .5)
def ik(S, G, bend):
    """(upper-arm angle, forearm angle relative) putting the glove at G from shoulder S; bend +1 elbow out-left, -1 out-right"""
    dx, dy = G[0] - S[0], G[1] - S[1]
    d = min(math.hypot(dx, dy), UA + FA - 1e-6)
    a = math.atan2(dy, dx)                                   # screen angle of S->G
    c = (UA * UA + d * d - FA * FA) / (2 * UA * d)
    t = math.acos(max(-1, min(1, c)))
    ua_dir = a + bend * t
    ex, ey = S[0] + UA * math.cos(ua_dir), S[1] + UA * math.sin(ua_dir)
    fa_dir = math.atan2(G[1] - ey, G[0] - ex)
    # CSS: a segment pointing down (screen angle 90deg) rotated by r points at screen angle 90 + r
    ua = math.degrees(ua_dir) - 90
    fa = math.degrees(fa_dir) - 90 - ua
    norm = lambda v: (v + 180) % 360 - 180
    return round(norm(ua), 1), round(norm(fa), 1)
def mirror(G): return (1 - G[0], G[1])
def arm(G, side, bend=None):
    if side == "l": return ik(SH, G, bend if bend is not None else 1)
    a, f = ik(SH, G, bend if bend is not None else 1)     # G is given as the left arm's (mirror image of the right's)
    return -a, -f

css = []
def rule(sel, decl): css.append("  %s{ %s }" % (sel, decl))
kf_n = [0]
def anim(kind, seg, frames, dur, extra="ease-in-out infinite", delay="0s"):
    """frames: [(pct, angle)]"""
    name = "cmr-%s-%s" % (kind, seg)
    body = " ".join("%s{ transform:rotate(%sdeg); }" % (", ".join("%d%%" % p for p in (pcts if isinstance(pcts, tuple) else (pcts,))), ang) for pcts, ang in frames)
    css.append("  @keyframes %s{ %s }" % (name, body))
    return "animation:%s %s %s %s both;" % (name, dur, extra, delay)
def seg(kind, part, decl):
    sel = {"ual": ".cm-arm-l > .cm-ua", "fal": ".cm-arm-l .cm-fa", "uar": ".cm-arm-r > .cm-ua", "far": ".cm-arm-r .cm-fa",
           "thl": ".cm-leg-l > .cm-th", "shl": ".cm-leg-l .cm-sh", "thr": ".cm-leg-r > .cm-th", "shr": ".cm-leg-r .cm-sh"}[part]
    ks = kind if isinstance(kind, (list, tuple)) else [kind]
    rule(", ".join(".cameo.cm-%s %s" % (k, sel) for k in ks) if len(ks) > 1 else ".cameo.cm-%s %s" % (ks[0], sel), decl)
def static(kind, part, ang): seg(kind, part, "transform:rotate(%sdeg);" % ang)

# ---- sit: gloves resting on the ledge beside the hips, a tap now and then; lower legs swinging out of step
a, f = arm((.0, 1.15), "l", 1)
static("sit", "ual", a)
seg("sit", "fal", anim("sit", "fal", [((0, 72, 100), f), (80, f - 16), (88, f)], "3.2s", "ease-in-out infinite", "1.2s"))
a, f = arm((.0, 1.15), "r", 1)
static("sit", "uar", a)
seg("sit", "far", anim("sit", "far", [((0, 60, 100), f), (68, f + 16), (76, f)], "3.2s", "ease-in-out infinite", "1.2s"))
static("sit", "thl", 7); static("sit", "thr", -7)
seg("sit", "shl", anim("sit", "shl", [(0, 20), (100, -10)], ".66s", "ease-in-out infinite alternate", ".4s"))
seg("sit", "shr", anim("sit", "shr", [(0, 10), (100, -20)], ".66s", "ease-in-out infinite alternate", "-.26s"))
# ---- sleepy: slack arms, legs barely moving
a, f = arm((.02, 1.18), "l", 1); static("sleepy", "ual", a); static("sleepy", "fal", f)
a, f = arm((.02, 1.18), "r", 1); static("sleepy", "uar", a); static("sleepy", "far", f)
static("sleepy", "thl", 6); static("sleepy", "thr", -6)
seg("sleepy", "shl", anim("sleepy", "shl", [(0, 6), (100, -3)], "2.4s", "ease-in-out infinite alternate"))
seg("sleepy", "shr", anim("sleepy", "shr", [(0, 3), (100, -6)], "2.4s", "ease-in-out infinite alternate", "-1.2s"))
# ---- tiptoe: creeping, gloves up at the shoulders, knees lifting in turn
a1, f1 = arm((-.02, .72), "l", 1); a2, f2 = arm((.0, .8), "l", 1)
seg("tiptoe", "ual", anim("tiptoe", "ual", [((0, 100), a1), (50, a2)], ".5s"))
seg("tiptoe", "fal", anim("tiptoe", "fal", [((0, 100), f1), (50, f2)], ".5s"))
a1, f1 = arm((-.02, .72), "r", 1); a2, f2 = arm((.0, .8), "r", 1)
seg("tiptoe", "uar", anim("tiptoe", "uar", [((0, 100), a2), (50, a1)], ".5s"))
seg("tiptoe", "far", anim("tiptoe", "far", [((0, 100), f2), (50, f1)], ".5s"))
seg("tiptoe", "thl", anim("tiptoe", "thl", [((0, 100), 4), (50, -16)], ".5s"))
seg("tiptoe", "shl", anim("tiptoe", "shl", [((0, 100), 0), (50, 30)], ".5s"))
seg("tiptoe", "thr", anim("tiptoe", "thr", [((0, 100), 16), (50, -4)], ".5s"))
seg("tiptoe", "shr", anim("tiptoe", "shr", [((0, 100), -30), (50, 0)], ".5s"))
# ---- run: a real stride - thighs swing, the trailing shin folds, arms swing against the legs, elbows bent (dir 1: running right;
#      the rig is mirrored for the other way)
seg("run", "thl", anim("run", "thl", [((0, 100), -34), (50, 30)], ".52s", "cubic-bezier(.45,0,.55,1) infinite"))
seg("run", "shl", anim("run", "shl", [((0, 100), 8), (40, 62), (60, 50)], ".52s", "cubic-bezier(.45,0,.55,1) infinite"))
seg("run", "thr", anim("run", "thr", [((0, 100), 30), (50, -34)], ".52s", "cubic-bezier(.45,0,.55,1) infinite"))
seg("run", "shr", anim("run", "shr", [((0, 100), 50), (10, 62), (50, 8)], ".52s", "cubic-bezier(.45,0,.55,1) infinite"))
seg("run", "ual", anim("run", "ual", [((0, 100), 40), (50, -30)], ".52s", "cubic-bezier(.45,0,.55,1) infinite"))
seg("run", "fal", anim("run", "fal", [((0, 100), -70), (50, -95)], ".52s", "cubic-bezier(.45,0,.55,1) infinite"))
seg("run", "uar", anim("run", "uar", [((0, 100), -30), (50, 40)], ".52s", "cubic-bezier(.45,0,.55,1) infinite"))
seg("run", "far", anim("run", "far", [((0, 100), -95), (50, -70)], ".52s", "cubic-bezier(.45,0,.55,1) infinite"))
# ---- dangle (a chin-up): both gloves on the ledge over the head's sides, legs kicking
a, f = arm((.07, .6), "l", 1); static("dangle", "ual", a); static("dangle", "fal", f)
a, f = arm((.07, .6), "r", 1); static("dangle", "uar", a); static("dangle", "far", f)
seg("dangle", "thl", anim("dangle", "thl", [(0, 12), (100, -10)], ".44s", "ease-in-out infinite alternate"))
seg("dangle", "shl", anim("dangle", "shl", [(0, -12), (100, 26)], ".44s", "ease-in-out infinite alternate"))
seg("dangle", "thr", anim("dangle", "thr", [(0, 10), (100, -12)], ".44s", "ease-in-out infinite alternate", "-.44s"))
seg("dangle", "shr", anim("dangle", "shr", [(0, -26), (100, 12)], ".44s", "ease-in-out infinite alternate", "-.44s"))
# ---- peek: both gloves on the ledge (the line is .72 down the figure)
a, f = arm((-.01, .67), "l", 1); static("peek", "ual", a); static("peek", "fal", f)
a, f = arm((-.01, .67), "r", 1); static("peek", "uar", a); static("peek", "far", f)
# ---- wave (risen .12 further: the line at .84): left glove on the ledge, the right waving beside the head
a, f = arm((-.02, .79), "l", 1); static("wave", "ual", a); static("wave", "fal", f)
a, f = arm((.0, .64), "r", 1)
static("wave", "uar", a)
seg("wave", "far", anim("wave", "far", [(0, f + 22), (100, f - 26)], ".28s", "ease-in-out 8 alternate", ".75s"))
# ---- cheer: both gloves up by the ears, shaking
a, f = arm((.04, .62), "l", 1); static("cheer", "ual", a)
seg("cheer", "fal", anim("cheer", "fal", [(0, f), (100, f - 18)], ".2s", "ease-in-out 8 alternate", ".5s"))
a, f = arm((.04, .62), "r", 1); static("cheer", "uar", a)
seg("cheer", "far", anim("cheer", "far", [(0, f), (100, f + 18)], ".2s", "ease-in-out 8 alternate", ".6s"))
# ---- oops (rises as peek does: the line at .72): left glove on the ledge; the right comes up for a fist pump
a, f = arm((-.01, .67), "l", 1); static("oops", "ual", a); static("oops", "fal", f)
a0, f0 = arm((-.01, .67), "r", 1); a1, f1 = arm((.04, .6), "r", 1); a2, f2 = arm((.05, .66), "r", 1)
seg("oops", "uar", anim("oops", "uar", [((0, 50), a0), ((58, 64, 72, 80, 86), a1), ((68, 76), a2), (100, a0)], "3.3s", "ease-in-out 1"))
seg("oops", "far", anim("oops", "far", [((0, 50), f0), ((58, 64, 72, 80, 86), f1), ((68, 76), f2), (100, f0)], "3.3s", "ease-in-out 1"))
for k in ("peek", "wave", "cheer", "oops"):
    pass

# ---- a held prop stays upright whatever the forearm does: turned back by the right forearm's own angle (its first frame)
def upright(kind, ua, fa): rule(".cameo.cm-%s .cm-hand-r > .cm-prop-art" % kind, "transform-origin:.14em .345em; transform:rotate(%sdeg);" % round(-(ua + fa), 1))
upright("sit", *arm((.0, 1.15), "r", 1))
upright("tiptoe", *arm((.0, .8), "r", 1))
upright("run", -30, -95)
a, f = arm((.0, .64), "r", 1); upright("wave", a, f)
upright("cheer", *arm((.04, .62), "r", 1))
# ---- the Sheriff tips his hat (the drawing's own hat group), with a little bow
rule(".cameo.cm-g-hattip .cm-bust .cx-fx-hat", "animation:cm-hattip 3.2s ease-in-out .9s infinite;")
css.append("  @keyframes cm-hattip{ 0%, 52%, 100%{ transform:none; } 62%, 78%{ transform:translateY(-1.8px) rotate(-14deg); } }")
out = "\n".join(css)
import os
path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "index.html")
src = open(path, encoding="utf-8").read()
A = "  /* ---- the poses (generated: tools/gen-cameo-rig.py) ---- */\n"; B = "  /* ---- leaving (CAMEO_OUT_MS 240)"
a = src.index(A) + len(A); b = src.index(B, a)
open(path, "w", encoding="utf-8").write(src[:a] + out + "\n\n" + src[b:])
print(len(css), "rules written into", path)
