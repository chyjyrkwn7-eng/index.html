import math
# The table read by gen-reactions.py (exec'd there, so P, R, the drawing
# helpers and the building blocks are in scope). One block per character,
# four bands each: perfect, great, pass, fail. Coordinates are the
# drawing's own (viewBox 3 3 34 34) and nothing may leave 3.5..36.5 - the
# drawing's edges feather out and clip, so a flame scaled past the top
# comes out cut flat.

# ============================================================== STARTERS ===

# ---- NINJA: a smoke bomb - gone, and back --------------------------------
# Build 318: "I don't like the ninja things it gets a hundred." The smoke
# was eleven pale discs each at half opacity, so every overlap printed a
# darker lens and the cloud read as a heap of grey bubbles; then a small
# shuriken parked in the corner. Now: a flash at the chest, ONE cloud (its
# lobes opaque, faded as a group, so it has a single outline) with a lit
# top and a shadowed underside, wisps and the scene's own leaves thrown
# out of it, the ninja gone inside it and back on top of it, and a glint
# off the plate on the band. The blade is its special, 2.6s later.
SHURIKEN = (lambda cx, cy, r: path(
    "M%s %s L%s %s L%s %s L%s %s L%s %s L%s %s L%s %s L%s %sZ" % (
        f2(cx), f2(cy - r), f2(cx + r * .28), f2(cy - r * .28), f2(cx + r), f2(cy), f2(cx + r * .28), f2(cy + r * .28),
        f2(cx), f2(cy + r), f2(cx - r * .28), f2(cy + r * .28), f2(cx - r), f2(cy), f2(cx - r * .28), f2(cy - r * .28)),
    fill="#DCE2EA", stroke="#58616F", sw=.28) + circ(cx, cy, r * .2, "#262B33"))
NJ_LOBES = [(11.6, 26.6, 4.2), (14.8, 19.4, 4.4), (20.4, 16.2, 4.7), (26, 19.2, 4.4), (28.6, 26.2, 4.2),
            (24.6, 30.4, 4.3), (15.8, 30.6, 4.3), (20, 23.8, 6.6)]
NJ_SMOKE = (pivot(20, 23.2, 13.6)
            + puff([(x + .5, y + 1.15, r) for x, y, r in NJ_LOBES], "#727C8C")
            + puff(NJ_LOBES, "#C5CCD6")
            + puff([(x - .4, y - .75, r * .8) for x, y, r in NJ_LOBES], "#DCE1E8"))
NJ_WISP = lambda x, y, k: pivot(x, y, 2.4 * k) + puff([(x - .9 * k, y + .3 * k, 1.1 * k), (x + .2 * k, y - .4 * k, 1.4 * k), (x + 1.2 * k, y + .4 * k, 1 * k)], "#C5CCD6")
NJ_LEAVES = pivot(20, 22, 13) + "".join(ell(x, y, 1.05, .45, c, rot=r) for x, y, c, r in [
    (8.6, 16.4, "#E0453F", -30), (12.4, 9.6, "#FF8A5B", 40), (27.4, 9.2, "#E0453F", -50), (31.6, 16, "#FF8A5B", 20),
    (7.8, 24.6, "#FF8A5B", 70), (32.4, 23.8, "#E0453F", -70)])
# the bang: eight tapered rays of uneven length round a white core
NJ_RAYS = "".join(path("M%s %s L%s %s L%s %sZ" % (
    f2(20 + math.cos(a + .09) * 2.4), f2(24 + math.sin(a + .09) * 2.4), f2(20 + math.cos(a) * L), f2(24 + math.sin(a) * L),
    f2(20 + math.cos(a - .09) * 2.4), f2(24 + math.sin(a - .09) * 2.4)), fill="#FFF6E6", op=.9)
    for a, L in [(i * math.pi / 4 + .2, 7.6 if i % 2 else 5.6) for i in range(8)])
R("ninja", "perfect", [
    P("fig", "", (2.0, EASE_IO, {6: "transform:translateY(.6px) scale(.95)", 15: "transform:translateY(.6px) scale(.93); opacity:1",
                                 19: "transform:scale(.9); opacity:0", 50: "transform:translateY(-1.6px) scale(.9); opacity:0",
                                 57: "transform:translateY(-2.4px) scale(1.06); opacity:1", 68: "transform:translateY(.4px) scale(.98)",
                                 80: "transform:none"}), at=.05),
    P("p-flash", "", (.5, EASE_OUT, {0: "opacity:0; transform:scale(.2) rotate(0deg)", 25: "opacity:1; transform:scale(1) rotate(20deg)",
                                     100: "opacity:0; transform:scale(1.45) rotate(45deg)"}), at=.26),
    P("p-smoke", "", (1.9, EASE_OUT, {0: "opacity:0; transform:scale(.25)", 13: "opacity:1; transform:scale(.95)",
                                      38: "opacity:1; transform:translateY(-.3px) scale(1.05)",
                                      50: "opacity:.2; transform:translateY(-1px) scale(1.12)",
                                      100: "opacity:0; transform:translateY(-2px) scale(1.16)"}), at=.28),
    P("p-w1", "", (1.2, EASE_OUT, {0: "opacity:0; transform:none", 15: "opacity:1", 100: "opacity:0; transform:translate(-2.6px,-2.4px) scale(1.35)"}), at=.42),
    P("p-w2", "", (1.2, EASE_OUT, {0: "opacity:0; transform:none", 15: "opacity:1", 100: "opacity:0; transform:translate(2.6px,-2.6px) scale(1.35)"}), at=.46),
    P("p-w3", "", (1.2, EASE_OUT, {0: "opacity:0; transform:none", 15: "opacity:1", 100: "opacity:0; transform:translate(-2.6px,1.2px) scale(1.3)"}), at=.5),
    P("p-w4", "", (1.2, EASE_OUT, {0: "opacity:0; transform:none", 15: "opacity:1", 100: "opacity:0; transform:translate(2.6px,1.4px) scale(1.3)"}), at=.44),
    P("p-leaves", "", (1.5, EASE_OUT, {0: "opacity:0; transform:scale(.4) rotate(-40deg)", 16: "opacity:1",
                                       75: "opacity:.9", 100: "opacity:0; transform:scale(1.14) rotate(22deg)"}), at=.3),
    P("p-glint", "", (.7, EASE_OUT, {0: "opacity:0; transform:scale(.1) rotate(0deg)", 35: "opacity:1; transform:scale(1.2) rotate(45deg)",
                                     100: "opacity:0; transform:scale(.4) rotate(90deg)"}), at=1.32),
    P("fx-tail1", "", raw=["cx-flutter .42s ease-in-out infinite"]),
    P("fx-tail2", "", raw=["cx-flutter-b .42s ease-in-out -.2s infinite"]),
] + joy(1.2), props=[
    ("leaves", 0, NJ_LEAVES),
    ("flash", 1, pivot(20, 24, 8.5) + NJ_RAYS + circ(20, 24, 3.4, "#FFE7C7", .55) + circ(20, 24, 2.1, "#FFFFFF")),
    ("smoke", 1, NJ_SMOKE),
    ("w1", 1, NJ_WISP(10.2, 13.6, 1)), ("w2", 1, NJ_WISP(29.8, 13.2, 1)),
    ("w3", 1, NJ_WISP(8.4, 30.4, .9)), ("w4", 1, NJ_WISP(31.6, 30.6, .9)),
    ("glint", 1, pivot(20, 14.35, 2.4) + star4(20, 14.35, 2.4, "#FFFFFF"))])
R("ninja", "great", [
    P("p-star2", "opacity:1", (.8, SPRING, {0: "opacity:0; transform:scale(0) rotate(-200deg)"}), turn=(.8, 1), at=.25),
    P("head", "transform:rotate(-2deg)", (1.0, EASE_OUT, {40: "transform:translateY(-.6px) rotate(-4deg)"})),
    P("fx-tail1", "", raw=["cx-flutter .8s ease-in-out infinite"]),
    P("fx-tail2", "", raw=["cx-flutter-b .8s ease-in-out -.4s infinite"]),
] + joy(.3), props=[("star2", 1, SHURIKEN(31.3, 27.6, 2.1))])
R("ninja", "pass", [
    P("head", "", (1.2, EASE_IO, {30: "transform:translateY(1.5px) scaleY(.97) rotate(3deg)", 62: "transform:none"}), at=.1),
    P("fx-tail1", "", (.9, EASE_IO, {40: "transform:rotate(-26deg)"}), at=.25),
    P("fx-tail2", "", (.9, EASE_IO, {40: "transform:rotate(22deg)"}), at=.3),
])
R("ninja", "fail", [
    slump(-11, 1.9),
    eyes_down(.7, .62),
    P("fx-tail1", "transform:rotate(38deg)", (1.0, EASE_OUT, {})),
    P("fx-tail2", "transform:rotate(44deg)", (1.0, EASE_OUT, {})),
    P("p-sweat", "", None, (3.2, EASE_IO, {12: "opacity:1", 80: "opacity:.9; transform:translate(.3px,3.6px)", 92: "opacity:0; transform:translate(.3px,4.2px)"}), at=.8),
], props=[("sweat", 1, drop(12.4, 15.6, .75, "#A9D8FF"))])

# ---- GHOST: spins, fades in and out, floats up ------------------------------
R("ghost", "perfect", [
    P("head", "transform:translateY(-1.8px)", (2.2, EASE_IO, {
        0: "transform:none; opacity:1",
        10: "transform:translateY(-1.4px) scaleX(.04); opacity:.75",
        20: "transform:translateY(-2.6px) scaleX(-1); opacity:.35",
        30: "transform:translateY(-3.2px) scaleX(.04); opacity:.8",
        40: "transform:translateY(-3.4px) scaleX(1); opacity:1",
        52: "transform:translateY(-3.4px); opacity:.18",
        64: "transform:translateY(-3.1px); opacity:1",
        76: "transform:translateY(-2.8px); opacity:.28",
        88: "transform:translateY(-2.2px); opacity:1",
        100: "opacity:1"}),
      (2.8, EASE_IO, {50: "transform:translateY(-3.2px); opacity:.7"})),
    P("mouth", "transform:scale(1.25, 1.4)", (.6, SPRING, {}), at=.3),
] + joy(.45))
R("ghost", "great", [
    P("head", "transform:translateY(-1px)", (1.5, EASE_IO, {
        15: "transform:translateY(-1px) rotate(-8deg)", 30: "transform:translateY(-1.6px) rotate(7deg)",
        45: "transform:translateY(-1.8px) rotate(-6deg)", 60: "transform:translateY(-1.6px) rotate(5deg)",
        80: "transform:translateY(-1.2px) rotate(-1.5deg)"}),
      (2.4, EASE_IO, {50: "transform:translateY(-2.1px)"})),
] + joy(.25))
R("ghost", "pass", [
    P("head", "", (1.0, EASE_IO, {40: "transform:translateY(-1.9px)", 75: "transform:translateY(.3px)"}), at=.1),
] + joy_blink(.2, 1.3))
R("ghost", "fail", [
    P("head", "transform:translateY(2.4px) scale(.95); opacity:.45", (1.7, EASE_OUT, {
        0: "transform:none; opacity:1", 35: "opacity:.5", 55: "opacity:.75", 75: "transform:translateY(2.8px) scale(.94); opacity:.35"}),
      (3.6, EASE_IO, {50: "transform:translateY(2.9px) scale(.95); opacity:.3"})),
    eyes_down(.9, .62),
    P("mouth", "transform:scale(.72, .55)", (.9, EASE_OUT, {}), at=.3),
])

# ---- WIZARD: raises the orb and casts a spray of sparks ---------------------
SPARKS_W = pivot(31.8, 10, 23) + "".join(star4(x, y, r, c) for x, y, r, c in [
    (25.5, 5.4, 1.25, "#FFE08A"), (21.4, 7.4, 1.0, "#D7B8FF"), (16.6, 5.2, 1.3, "#FFFFFF"), (12.4, 8.4, 1.0, "#FFE08A"),
    (9.6, 13.2, 1.15, "#B8F0FF"), (27.4, 13.6, .85, "#FFFFFF"), (19.2, 11.8, .7, "#FFE08A")])
R("wizard", "perfect", [
    P("fx-gem", "transform:scale(1.12)", (1.9, EASE_OUT, {14: "transform:scale(1.45)", 24: "transform:scale(1.08)", 38: "transform:scale(1.45)", 52: "transform:scale(1.15)"}),
      (1.6, EASE_IO, {50: "transform:scale(1.3)"})),
    P("p-sparks", "", (1.5, EASE_OUT, {0: "opacity:0; transform:scale(.08)", 16: "opacity:1; transform:scale(.55)", 62: "opacity:1; transform:scale(1)",
                                       100: "opacity:0; transform:scale(1.1)"}),
      (2.4, EASE_OUT, {8: "opacity:1; transform:scale(.45)", 55: "opacity:.9; transform:scale(1)", 80: "opacity:0; transform:scale(1.08)"}), at=.25),
    P("head", "transform:rotate(-2.5deg)", (1.4, EASE_OUT, {30: "transform:translateY(-.7px) rotate(-5deg)"})),
    P("fx-wz3orbit", "", raw=["cx-spin 1.1s linear infinite"]),
    P("fx-star, fx-star2", "", raw=["cx-twinkle .7s ease-in-out infinite"]),
] + joy(.5), props=[("sparks", 1, SPARKS_W)])
R("wizard", "great", [
    P("fx-gem", "transform:scale(1.1)", (1.2, EASE_OUT, {30: "transform:scale(1.55)", 60: "transform:scale(1.05)"}), (2.0, EASE_IO, {50: "transform:scale(1.3)"})),
    P("p-sparks3", "", (1.0, EASE_OUT, {0: "opacity:0; transform:scale(.1)", 25: "opacity:1; transform:scale(.7)", 100: "opacity:0; transform:scale(1.1)"}),
      (3.0, EASE_OUT, {10: "opacity:1; transform:scale(.5)", 45: "opacity:0; transform:scale(1.1)"}), at=.3),
    P("fx-wz3orbit", "", raw=["cx-spin 2.2s linear infinite"]),
] + joy(.3), props=[("sparks3", 1, pivot(31.8, 10, 10) + star4(26.8, 6.2, 1.0, "#FFE08A") + star4(23.4, 9.8, .8, "#FFFFFF") + star4(28.6, 3.8, .75, "#D7B8FF"))])
R("wizard", "pass", [
    P("fx-gem", "", (1.0, EASE_IO, {35: "transform:scale(1.35)"}), at=.2),
    P("fx-tip", "", (1.0, EASE_IO, {40: "transform:scale(1.6) rotate(30deg)"}), at=.35),
    nod(1.1, .1, .9),
])
R("wizard", "fail", [
    P("fx-gem", "opacity:.35; transform:scale(.8)", (1.1, EASE_OUT, {20: "transform:scale(1.3); opacity:1", 45: "transform:scale(.7); opacity:.5"}), at=.15),
    P("p-fizzle", "", (1.6, EASE_OUT, {15: "opacity:.9; transform:translateY(1.6px) scale(.5)", 70: "opacity:.5; transform:translateY(-.6px)",
                                       100: "opacity:0; transform:translateY(-1px) scale(1.1)"}),
      (3.2, EASE_OUT, {18: "opacity:.6; transform:translateY(1.5px) scale(.6)", 80: "opacity:0; transform:translateY(-1px) scale(1.08)"}), at=.35),
    P("fx-wz3orbit", "opacity:.3", (1.0, EASE_OUT, {})),
    slump(-6, .8),
    eyes_down(.6, .7),
], props=[("fizzle", 1, puff([(31.6, 8.4, 1.35), (30.6, 6.4, 1.05), (32.4, 5.6, .8)], "#8E97A6", .85))])

# ---- BEAR: a belly laugh, ears wiggling, hearts ------------------------------
HEARTS = pivot(20, 12, 13) + heart(8.6, 14.4, 1.7, "#FF7EB3") + heart(31.4, 11.4, 1.5, "#FF9CC6") + heart(25.8, 7.4, 1.2, "#FFB3D2")
R("grizzly", "perfect", [
    P("head", "transform:translateY(-.3px) rotate(-3deg)", (2.0, "linear", {
        6: "transform:translateY(-1.1px) rotate(-3deg)", 12: "transform:translateY(.4px) rotate(-2deg)", 18: "transform:translateY(-1.1px) rotate(-4deg)",
        24: "transform:translateY(.4px) rotate(-2deg)", 30: "transform:translateY(-1.1px) rotate(-4deg)", 36: "transform:translateY(.4px) rotate(-2deg)",
        42: "transform:translateY(-1.1px) rotate(-4deg)", 50: "transform:translateY(.2px) rotate(-3deg)", 62: "transform:translateY(-.8px) rotate(-4deg)"}),
      (1.5, EASE_IO, {25: "transform:translateY(-1px) rotate(-3.5deg)", 50: "transform:translateY(-.1px) rotate(-3deg)", 75: "transform:translateY(-.8px) rotate(-2.5deg)"})),
    P("mouth", "transform:translateY(.3px) scale(1.4, 2)", (.5, SPRING, {}), at=.1),
    P("fx-ear-l", "", raw=["cx-twitch-l .5s ease-in-out infinite"]),
    P("fx-ear-r", "", raw=["cx-twitch-r .5s ease-in-out -.25s infinite"]),
    P("p-hearts", "", (1.7, EASE_OUT, {0: "opacity:0; transform:translateY(2.5px) scale(.4)", 22: "opacity:1; transform:translateY(.5px) scale(1)",
                                       100: "opacity:0; transform:translateY(-2px) scale(1.05)"}),
      (2.2, EASE_OUT, {15: "opacity:1; transform:translateY(1.5px) scale(.85)", 85: "opacity:0; transform:translateY(-1.8px)"}), at=.6),
] + joy(.15), props=[("hearts", 1, HEARTS)])
R("grizzly", "great", [
    P("fx-ear-l", "", raw=["cx-twitch-l .8s ease-in-out infinite"]),
    P("fx-ear-r", "", raw=["cx-twitch-r .8s ease-in-out -.4s infinite"]),
    P("head", "transform:rotate(-4deg) translateY(-.3px)", (1.0, SPRING, {})),
    P("mouth", "transform:scale(1.2, 1.3)", (.6, SPRING, {}), at=.2),
    P("p-heart1", "", (1.4, EASE_OUT, {0: "opacity:0; transform:translateY(2px) scale(.4)", 25: "opacity:1; transform:scale(1)", 100: "opacity:0; transform:translateY(-3px)"}),
      (2.8, EASE_OUT, {15: "opacity:1; transform:translateY(1.4px) scale(.85)", 70: "opacity:0; transform:translateY(-2.4px)"}), at=.5),
] + joy(.25), props=[("heart1", 1, pivot(30.6, 9.4, 2) + heart(30.6, 9.4, 1.2, "#FF8CBB"))])
R("grizzly", "pass", [
    P("fx-ear-r", "", (.9, EASE_IO, {30: "transform:rotate(16deg)", 60: "transform:rotate(-6deg)"}), at=.3),
    P("mouth", "transform:scale(1.15, 1.2)", (.5, SPRING, {}), at=.2),
    nod(1.1, .1, .9),
])
R("grizzly", "fail", [
    P("fx-ear-l", "transform:translateY(.7px) rotate(-30deg)", (1.0, EASE_OUT, {})),
    P("fx-ear-r", "transform:translateY(.7px) rotate(30deg)", (1.0, EASE_OUT, {})),
    slump(-8, 1.5),
    eyes_down(.6, .62),
    P("mouth", "transform:scale(.75, .6)", (.8, EASE_OUT, {}), at=.3),
    P("p-sigh", "", None, (3.6, EASE_OUT, {10: "opacity:.75; transform:translate(0,0) scale(.5)", 55: "opacity:0; transform:translate(-2.6px,1.4px) scale(1.2)"}), at=1.0),
], props=[("sigh", 1, pivot(15.2, 29.2, 1.6) + puff([(15.2, 29.2, .9), (13.8, 29.8, .7)], "#C9D1DC", .8))])

# ---- ALIEN: beamed up by its ship, eyes blazing ------------------------------
UFO = (ell(20, 6.2, 6, 1.5, "#9AA6B8") + ell(20, 5.8, 6, .9, "#C7D0DC") + ell(20, 5.2, 2.6, 1.6, "#BFF5D0", .95) +
       circ(16.2, 6.6, .42, "#7CFF9E") + circ(20, 7.1, .42, "#FFFFFF") + circ(23.8, 6.6, .42, "#7CFF9E"))
BEAM = (path("M17.6 7.4 L22.4 7.4 L31.5 37 L8.5 37Z", fill="#B4FFD0", op=.16) +
        ell(20, 14, 3.2, .8, "none", .55, "#D8FFE6", .3) + ell(20, 22, 5.6, 1.2, "none", .45, "#D8FFE6", .3) + ell(20, 30, 8, 1.5, "none", .35, "#D8FFE6", .3))
R("alien", "perfect", [
    P("p-ufo", "opacity:1", (2.2, EASE_OUT, {0: "opacity:0; transform:translateY(-3px) scale(.6)", 16: "opacity:1; transform:none"}),
      (2.4, EASE_IO, {50: "transform:translateY(.6px)"})),
    P("p-beam", "", (2.2, "linear", {0: "opacity:0; transform:scaleY(.08)", 18: "opacity:0; transform:scaleY(.08)", 28: "opacity:1; transform:scaleY(1)",
                                     78: "opacity:1; transform:scaleY(1)", 92: "opacity:0; transform:scaleY(1)"})),
    P("fig", "", (2.2, EASE_IO, {26: "transform:none", 44: "transform:translateY(-3.6px) rotate(-3deg)", 58: "transform:translateY(-4.2px) rotate(3deg)",
                                 72: "transform:translateY(-3.8px) rotate(-2deg)", 90: "transform:translateY(-.4px)"})),
    P("fx-eyeglow", "opacity:.85", (2.0, "linear", {30: "opacity:0", 38: "opacity:1", 46: "opacity:.4", 54: "opacity:1"}), (1.8, EASE_IO, {50: "opacity:.4"})),
    P("fx-tip", "", None, (.6, "steps(1,end)", {50: "opacity:.25"}), at=.6),
], props=[("beam", 1, BEAM), ("ufo", 1, UFO)])
R("alien", "great", [
    P("fx-tip", "", None, (.45, "steps(1,end)", {50: "opacity:.2"}), at=.2),
    P("fx-eyeglow", "opacity:.7", (1.0, EASE_OUT, {30: "opacity:1"}), (2.0, EASE_IO, {50: "opacity:.3"})),
    P("fig", "", (1.1, EASE_IO, {40: "transform:translateY(-2px)", 75: "transform:translateY(.3px)"}), at=.1),
])
R("alien", "pass", [
    P("fx-tip", "", (1.0, "steps(1,end)", {20: "opacity:.2", 40: "opacity:1", 60: "opacity:.2", 80: "opacity:1"}), at=.25),
    nod(1.1, .1, .9),
])
R("alien", "fail", [
    P("eyes", "opacity:.5; transform:translateY(.6px) scaleY(.82)", (1.2, EASE_OUT, {})),
    P("fx-tip", "opacity:.3; transform:translateY(.9px)", (1.0, EASE_OUT, {}), at=.2),
    P("mouth", "transform:scale(.7, 1)", (.8, EASE_OUT, {}), at=.3),
    P("p-ufo2", "", (2.6, EASE_IO, {0: "opacity:0; transform:translateX(-14px)", 30: "opacity:.9; transform:translateX(-4px)", 70: "opacity:.9; transform:translateX(5px)",
                                    100: "opacity:0; transform:translateX(15px)"}), at=.5),
    slump(-7, 1.6),
], props=[("ufo2", 1, ell(20, 5.2, 4.2, 1.05, "#7E8898") + ell(20, 4.6, 1.9, 1.2, "#9FB3A8", .8))])

# ---- DETECTIVE: tips the hat, the magnifier glints ---------------------------
GLASS = (line(32, 34.4, 27.6, 29.6, "#6E4B2D", 1.3) + circ(24.6, 26.4, 3.7, "#CDEBFF", .3) +
         circ(24.6, 26.4, 3.7, "none", 1, "#D9DEE6", .85) + path("M22.4 24.4 Q23.6 23.1 25.4 23.1", stroke="#FFFFFF", sw=.45, op=.85))
R("detective", "perfect", [
    P("fx-hat", "", (1.6, EASE_IO, {18: "transform:translateY(-3.1px) rotate(-15deg)", 36: "transform:translateY(-3.3px) rotate(-16deg)",
                                    54: "transform:translateY(-.3px) rotate(2deg)", 66: "transform:none"})),
    P("p-glass", "opacity:1", (2.0, EASE_OUT, {0: "opacity:0; transform:translate(7px,6px) rotate(35deg)", 30: "opacity:0; transform:translate(7px,6px) rotate(35deg)",
                                               55: "opacity:1; transform:rotate(-7deg)", 72: "transform:rotate(4deg)", 86: "transform:none"}),
      (3.0, EASE_IO, {50: "transform:translate(-.5px,-.4px) rotate(-3deg)"}), at=.2),
    P("p-glint", "", (2.2, "linear", {58: "opacity:0", 64: "opacity:1; transform:scale(1.4) rotate(45deg)", 72: "opacity:0; transform:scale(.4)",
                                      80: "opacity:1; transform:scale(1.15) rotate(90deg)", 90: "opacity:0"}),
      (3.0, "linear", {40: "opacity:0", 47: "opacity:1; transform:scale(1.3) rotate(45deg)", 58: "opacity:0; transform:scale(.5)"}), at=.2),
    P("eyes", "transform:scale(1.15)", (.8, SPRING, {}), at=.3),
    P("head", "transform:rotate(-2.5deg)", (1.6, EASE_OUT, {30: "transform:rotate(-4deg) translateY(-.4px)"})),
], props=[("glass", 1, GLASS), ("glint", 1, pivot(23.2, 24.8, 2.4) + star4(23.2, 24.8, 2.2, "#FFFFFF"))])
R("detective", "great", [
    P("fx-hat", "", (1.2, EASE_IO, {30: "transform:translateY(-2px) rotate(-10deg)", 62: "transform:none"}), at=.1),
    P("p-hglint", "", (1.4, "linear", {40: "opacity:0", 50: "opacity:1; transform:scale(1.3) rotate(45deg)", 64: "opacity:0"}),
      (3.4, "linear", {40: "opacity:0", 48: "opacity:1; transform:scale(1.2) rotate(45deg)", 58: "opacity:0"}), at=.3),
    P("eyes", "", None, (1.6, EASE_IO, {50: "transform:scale(1.2)"}), at=.2),
], props=[("hglint", 1, pivot(28.6, 14.6, 1.5) + star4(28.6, 14.6, 1.25, "#FFFFFF"))])
R("detective", "pass", [
    P("fx-hat", "", (1.0, EASE_IO, {35: "transform:translateY(-1.3px) rotate(-6deg)"}), at=.15),
    P("eyes", "", (1.0, EASE_IO, {40: "transform:scale(1.25)"}), at=.25),
])
R("detective", "fail", [
    P("fx-hat", "transform:translateY(2.3px) scale(1.03)", (1.1, EASE_OUT, {}), at=.25),
    P("eyes", "opacity:.15; transform:translateY(.5px)", (1.0, EASE_OUT, {}), at=.3),
    P("mouth", "transform:scaleX(.7)", (.8, EASE_OUT, {}), at=.3),
    slump(-6, 1.3),
])

# ---- ALIEN-ish done; THE CHALLENGE CHARACTERS ======================================

# ---- MASKED ONE: the red mark flashes like lightning --------------------------
FLICK = {6: "opacity:1", 10: "opacity:.15", 15: "opacity:1", 22: "opacity:0", 38: "opacity:0", 42: "opacity:1", 50: "opacity:0"}
R("masked", "perfect", [
    P("fx-mk3flash, fx-mk3bolt, fx-mk3fork", "", (2.0, "linear", FLICK),
      (2.6, "linear", {80: "opacity:0", 84: "opacity:.9", 88: "opacity:.1", 92: "opacity:.8", 96: "opacity:0"})),
    P(".cx-mkmark", "transform:scale(1.05)", (2.0, EASE_OUT, {6: "transform:scale(1.14)", 22: "transform:scale(1.02)", 42: "transform:scale(1.12)"})),
    P("fx-slotglow", "opacity:1", (1.0, "linear", {12: "opacity:1", 20: "opacity:.4", 28: "opacity:1"}), (1.4, EASE_IO, {50: "opacity:.55"})),
    P("head", "transform:translateY(-.6px)", (1.4, EASE_OUT, {8: "transform:translateY(-1.2px) rotate(3deg)", 16: "transform:translateY(-1.1px) rotate(-3deg)",
                                                            24: "transform:translateY(-1px) rotate(2deg)", 34: "transform:translateY(-.7px)"})),
], flash=("rgba(255,50,80,.9)", .05))
R("masked", "great", [
    P("fx-mk3flash, fx-mk3bolt", "", (1.6, "linear", {12: "opacity:1", 22: "opacity:0", 40: "opacity:.8", 52: "opacity:0"}), at=.2),
    P("fx-slotglow", "opacity:.8", (.8, EASE_OUT, {30: "opacity:1"}), (1.8, EASE_IO, {50: "opacity:.4"}), at=.2),
    P("head", "transform:translateY(-.4px)", (.8, SPRING, {})),
])
R("masked", "pass", [
    P("fx-slotglow", "", (1.1, EASE_IO, {30: "opacity:1", 70: "opacity:.8"}), at=.25),
    nod(1.1, .1, .9),
])
R("masked", "fail", [
    P(".cx-mkmark", "opacity:.28", (1.3, EASE_OUT, {15: "opacity:1", 30: "opacity:.5", 40: "opacity:.9"})),
    P("head", "transform:translate(-1.1px,1.4px) rotate(9deg)", (1.3, EASE_OUT, {}),
      (3.8, EASE_IO, {50: "transform:translate(-1.2px,1.6px) rotate(10deg)"})),
    P("eyes", "opacity:.55; transform:translateY(.4px) scaleY(.8)", (1.0, EASE_OUT, {}), at=.3),
    P("fx-mk2crack", "transform:scaleY(1.12)", (1.2, EASE_OUT, {}), at=.2),
])

# ---- ZEUS: throws a bolt that flashes the circle ---------------------------
BOLT_Z = bolt(19.2, 8.2, 1.25, "#FFF4C2", "#FFC93A", .35)
R("zeus", "perfect", [
    P("p-bolt", "", (2.1, "linear", {
        0: "opacity:0; transform:translate(6px,-7px) scale(.35) rotate(-14deg)",
        12: "opacity:1; transform:translate(6px,-7px) scale(.5) rotate(-14deg)",
        20: "opacity:.55; transform:translate(6.2px,-7.2px) scale(.56) rotate(-12deg)",
        27: "opacity:1; transform:translate(5.6px,-6.6px) scale(.62) rotate(-16deg)",
        33: "opacity:1; transform:translate(-5px,4px) scale(1.15) rotate(10deg)",
        40: "opacity:.9; transform:translate(-5.4px,4.4px) scale(1.12) rotate(10deg)",
        48: "opacity:0; transform:translate(-5.6px,4.6px) scale(1.1) rotate(10deg)"})),
    P("p-zap", "", (2.1, "linear", {32: "opacity:0; transform:scale(.3)", 36: "opacity:1; transform:scale(1.15)",
                                    52: "opacity:0; transform:scale(1.5) rotate(30deg)"})),
    P("fx-zs3eyes", "opacity:1", (2.1, "linear", {30: "opacity:0", 34: "opacity:1"}), (1.8, EASE_IO, {50: "opacity:.5"})),
    P("head", "transform:translateY(-.6px) rotate(-2deg)", (2.1, EASE_OUT, {
        24: "transform:translateY(-.9px) rotate(-4deg)", 34: "transform:translateY(.5px) rotate(3deg)", 46: "transform:translateY(-.4px) rotate(-1deg)"}),
      (2.6, EASE_IO, {50: "transform:translateY(-1px) rotate(-2.5deg)"})),
    P("fx-bolt", "", None, (1.4, EASE_IO, {50: "transform:scale(1.25)"}), at=.7),
], props=[("bolt", 1, BOLT_Z),
          ("zap", 1, pivot(13, 28, 4) + star4(13, 28, 3.6, "#FFF7D1") + star4(13, 28, 2, "#FFFFFF", w=.4) +
           star4(10.4, 25.2, 1.1, "#FFE27A") + star4(16, 30.6, .9, "#FFE27A"))],
  flash=("rgba(255,244,190,.95)", .72))
R("zeus", "great", [
    P("fx-strike", "", (1.4, "linear", {18: "opacity:0", 22: "opacity:1", 27: "opacity:.2", 32: "opacity:1", 44: "opacity:0"}), at=.1),
    P("fx-zs3eyes", "opacity:.85", (1.2, EASE_OUT, {25: "opacity:1"}), (2.2, EASE_IO, {50: "opacity:.45"}), at=.25),
    P("head", "transform:translateY(-.5px) rotate(-1.5deg)", (1.2, EASE_OUT, {35: "transform:translateY(-.9px) rotate(-3deg)"})),
    P("fx-bolt", "", None, (2, EASE_IO, {50: "transform:scale(1.18)"}), at=.6),
])
R("zeus", "pass", [
    P("fx-zs3eyes", "", (1.3, EASE_IO, {30: "opacity:1", 60: "opacity:.9"}), at=.2),
    P("fx-bolt", "", (1.0, EASE_IO, {40: "transform:scale(1.35)"}), at=.35),
    nod(1.1, .1, .9),
])
R("zeus", "fail", [
    P("p-cloud", "opacity:1", (1.1, EASE_OUT, {0: "opacity:0; transform:translateY(-.5px)"}), (3.4, EASE_IO, {50: "transform:translateX(-.7px)"}), at=.3),
    P("p-rain", "", None, (.9, "linear", {12: "opacity:.95", 80: "opacity:0; transform:translateY(3.6px)"}), at=1.0),
    P("fx-bolt", "opacity:.3; transform:scale(.85)", (1.2, EASE_OUT, {25: "transform:scale(1.2); opacity:1"}), at=.2),
    slump(-8, 1.5),
    eyes_down(.5, .8),
], props=[("cloud", 1, puff([(18.6, 6.2, 2.2), (22.2, 5.6, 2.5), (25.6, 6.4, 2.1), (21.8, 7.4, 2.3)], "#6F7887") +
           puff([(21.4, 5.2, 1.4)], "#8B94A3")),
          ("rain", 1, line(18.6, 9.4, 18.2, 11, "#A8CBFF", .4) + line(22.2, 10, 21.8, 11.6, "#A8CBFF", .4) +
           line(25.4, 9.3, 25, 10.9, "#A8CBFF", .4))])

# ---- SHERIFF (the poseidon id): tosses the hat, the star gleams --------------
R("poseidon", "perfect", [
    P("fx-shhat", "transform-origin:50% 60%", (1.9, EASE_IO, {0: "transform:none; transform-origin:50% 60%", 12: "transform:translateY(-2px) scaleX(.08)", 26: "transform:translateY(-2.6px) scaleX(-1)",
                                                           40: "transform:translateY(-2.6px) scaleX(.08)", 54: "transform:translateY(-2.2px) scaleX(1)",
                                                           66: "transform:translateY(.4px)", 76: "transform:none"})),
    P("fx-shstar", "", (1.8, EASE_OUT, {25: "transform:scale(1.25) rotate(25deg)", 50: "transform:none"}), (2.6, EASE_IO, {50: "transform:scale(1.08)"}), at=.6),
    P("fx-sh3glint", "", (1.6, "linear", {30: "opacity:0", 40: "opacity:1; transform:scale(1.4) rotate(45deg)", 55: "opacity:0"}),
      (2.6, "linear", {40: "opacity:0", 48: "opacity:1; transform:scale(1.3) rotate(45deg)", 58: "opacity:0"}), at=.6),
    P("fx-sh4weed", "", raw=["cx-sh4-weed 2.4s linear .2s infinite"]),
    P("fx-sh4roll", "", raw=["cx-spin-back .35s linear infinite"]),
    P("eyes", "transform:scaleY(.5)", (.6, EASE_OUT, {}), at=.7),
])
R("poseidon", "great", [
    P("fx-shhat", "", (1.3, EASE_IO, {28: "transform:translateY(-2.2px) rotate(-9deg)", 62: "transform:none"}), at=.1),
    P("fx-sh3glint", "", (1.4, "linear", {30: "opacity:0", 42: "opacity:1; transform:scale(1.35) rotate(45deg)", 58: "opacity:0"}),
      (3.0, "linear", {40: "opacity:0", 48: "opacity:1; transform:scale(1.25) rotate(45deg)", 58: "opacity:0"}), at=.4),
    P("eyes", "transform:scaleY(.6)", (.6, EASE_OUT, {}), at=.5),
])
R("poseidon", "pass", [
    P("fx-sh3glint", "", (1.2, "linear", {25: "opacity:0", 40: "opacity:1; transform:scale(1.3) rotate(45deg)", 60: "opacity:0"}), at=.3),
    P("fx-shstar", "", (1.0, EASE_IO, {40: "transform:scale(1.25)"}), at=.3),
    nod(1.1, .1, .9),
])
R("poseidon", "fail", [
    P("fx-shhat", "transform:translateY(2px)", (1.1, EASE_OUT, {}), at=.2),
    P("eyes", "opacity:.4; transform:translateY(.4px) scaleY(.6)", (1.0, EASE_OUT, {}), at=.3),
    P("fx-sh4weed", "", raw=["cx-sh4-weed 10s linear .6s infinite"]),
    P("fx-sh4roll", "", raw=["cx-spin-back 2.2s linear infinite"]),
    slump(-7, 1.4),
])

# ---- CLOWN: honks its nose and juggles; a fail drops the ball -----------------
HONK = (pivot(20, 22.8, 7.4) + line(15.6, 21.2, 14.1, 20.5, "#FFE36E", .5) + line(15.3, 22.8, 13.6, 22.8, "#FFE36E", .5) +
        line(15.6, 24.4, 14.1, 25.1, "#FFE36E", .5) + line(24.4, 21.2, 25.9, 20.5, "#FFE36E", .5) +
        line(24.7, 22.8, 26.4, 22.8, "#FFE36E", .5) + line(24.4, 24.4, 25.9, 25.1, "#FFE36E", .5))
JUGGLE = pivot(20, 9.4, 5.6) + circ(20, 4.4, 1.15, "#FF4D5E") + circ(24.3, 11.9, 1.15, "#FFD23A") + circ(15.7, 11.9, 1.15, "#4DB8FF") + \
    circ(19.7, 4.1, .35, "#FFFFFF", .7) + circ(24, 11.6, .35, "#FFFFFF", .7) + circ(15.4, 11.6, .35, "#FFFFFF", .7)
R("clown", "perfect", [
    P("fx-nose", "", (1.4, EASE_IO, {10: "transform:scale(1.65, 1.3)", 20: "transform:scale(.82)", 30: "transform:scale(1.15)", 42: "transform:none",
                                     52: "transform:scale(1.65, 1.3)", 62: "transform:scale(.82)", 72: "transform:scale(1.1)", 82: "transform:none"}), at=.1),
    P("p-honk", "", (1.4, "linear", {8: "opacity:0; transform:scale(.6)", 14: "opacity:1; transform:scale(1.15)", 28: "opacity:0; transform:scale(1.3)",
                                     50: "opacity:0; transform:scale(.6)", 56: "opacity:1; transform:scale(1.15)", 70: "opacity:0; transform:scale(1.3)"}), at=.1),
    P("fx-cl3balls", "opacity:0", (.4, "linear", {0: "opacity:1"}), at=.7),
    P("p-juggle", "opacity:1", (.5, SPRING, {0: "opacity:0; transform:scale(.3)"}), turn=(1.0, 1), at=.8),
    P("fx-cl2bells", "", (1.6, EASE_IO, {15: "transform:rotate(-7deg)", 35: "transform:rotate(6deg)", 55: "transform:rotate(-4deg)", 75: "transform:rotate(3deg)"}),
      (1.2, EASE_IO, {25: "transform:rotate(-4deg)", 75: "transform:rotate(4deg)"}), at=.9),
    P("head", "", (1.6, EASE_IO, {25: "transform:rotate(-6deg)", 50: "transform:rotate(5deg)", 75: "transform:rotate(-3deg)"}),
      (1.6, EASE_IO, {25: "transform:rotate(-4deg)", 75: "transform:rotate(4deg)"}), at=.9),
] + joy(1.0), props=[("honk", 1, HONK), ("juggle", 1, JUGGLE)])
R("clown", "great", [
    P("fx-cl3wink", "", (1.6, EASE_IO, {15: "transform:scaleY(.15)", 60: "transform:scaleY(.15)", 75: "transform:none"}), at=.2),
    P("fx-nose", "", (.9, EASE_IO, {20: "transform:scale(1.5, 1.25)", 40: "transform:scale(.88)", 60: "transform:scale(1.08)"}), at=.9),
    P("fx-cl3jx", "", raw=["cx-cl3-jx .7s ease-in-out infinite alternate"]),
    P("fx-cl3jy", "", raw=["cx-cl3-jy .35s ease-in-out infinite alternate"]),
    P("fx-cl2bells", "", (1.2, EASE_IO, {20: "transform:rotate(-6deg)", 45: "transform:rotate(5deg)", 70: "transform:rotate(-2deg)"}), at=.3),
])
R("clown", "pass", [
    P("fx-nose", "", (.9, EASE_IO, {22: "transform:scale(1.4, 1.2)", 45: "transform:scale(.9)", 65: "transform:scale(1.05)"}), at=.25),
    nod(1.1, .1, .8),
])
R("clown", "fail", [
    P("p-ball", "opacity:1; transform:translateY(30.4px)", (1.4, "cubic-bezier(.55,0,1,.45)", {0: "opacity:1; transform:none", 62: "transform:translateY(30.4px)",
                                                                                              74: "transform:translateY(27.6px)", 86: "transform:translateY(30.4px)",
                                                                                              93: "transform:translateY(29.6px)"}), at=.2),
    P("fx-cl3balls", "opacity:0", (.3, "linear", {0: "opacity:1"}), at=.2),
    P("p-tear", "", None, (2.6, EASE_IO, {15: "opacity:1", 80: "opacity:.8; transform:translateY(3px)", 92: "opacity:0; transform:translateY(3.4px)"}), at=1.2),
    P("fx-cl2hat", "transform:translateY(.8px) rotate(6deg)", (1.2, EASE_OUT, {}), at=.3),
    P("mouth", "transform:scaleY(-.8) translateY(-.4px)", (.9, EASE_OUT, {}), at=.5),
    slump(-6, 1.2),
], props=[("ball", 1, circ(26.4, 4, 1.25, "#FF4D5E") + circ(26, 3.6, .4, "#FFFFFF", .7)),
          ("tear", 1, drop(16.4, 24.4, .55, "#9FD0FF"))])

# ---- KOI: a koi leaps out of the bowl and splashes back -----------------------
KOI = ('<g transform="translate(20 20) rotate(0)">' +
       path("M0 2.7 Q2 4.2 1.6 5.8 Q.6 4.8 0 4.4 Q-.6 4.8 -1.6 5.8 Q-2 4.2 0 2.7 Z", fill="#FF8A4A") +
       path("M0 -3.6 Q1.9 -2 1.6 .6 Q1.2 2.4 0 3 Q-1.2 2.4 -1.6 .6 Q-1.9 -2 0 -3.6 Z", fill="#FFF4EC", stroke="rgba(0,0,0,.35)", sw=.2) +
       path("M0 -3.4 Q1.4 -2.2 1.2 -.6 Q.2 -.2 -.6 -1.6 Q-.6 -2.8 0 -3.4 Z", fill="#FF5A2A") +
       circ(.8, -2.3, .38, "#1A0A08") + circ(-.8, -2.3, .38, "#1A0A08") + "</g>")
SPLASH = pivot(20, 14.4, 6) + "".join(circ(x, y, r, "#B8ECFF") for x, y, r in [(15.2, 13.2, .6), (17.4, 11.6, .5), (22.8, 11.4, .55), (25, 13, .6), (20, 10.8, .45)])
R("valkyrie", "perfect", [
    P("p-koi", "", (2.2, EASE_IO, {0: "opacity:0; transform:translate(-5px,4px) rotate(-60deg) scale(.8)",
                                   14: "opacity:1; transform:translate(-5px,1px) rotate(-40deg) scale(.85)",
                                   34: "opacity:1; transform:translate(-2.5px,-8px) rotate(-10deg) scale(.95)",
                                   48: "opacity:1; transform:translate(1px,-10px) rotate(40deg) scale(.95)",
                                   62: "opacity:1; transform:translate(4px,-5px) rotate(120deg) scale(.9)",
                                   72: "opacity:0; transform:translate(5px,-1px) rotate(160deg) scale(.85)"}), at=.15),
    P("p-splash", "", (2.2, "linear", {16: "opacity:0; transform:translateY(1px) scale(.4)", 22: "opacity:1; transform:translateY(-.6px) scale(1)",
                                       34: "opacity:0; transform:translateY(-2.2px) scale(1.1)", 66: "opacity:0; transform:translateY(1px) scale(.4)",
                                       72: "opacity:1; transform:translateY(-.6px) scale(1.15)", 86: "opacity:0; transform:translateY(-2.4px) scale(1.2)"}), at=.15),
    P("fx-koiwater", "", (2.2, EASE_IO, {20: "transform:translateY(-.6px)", 30: "transform:translateY(.4px)", 72: "transform:translateY(-.9px)", 82: "transform:translateY(.5px)", 92: "transform:translateY(-.2px)"}), at=.15),
    P("fx-koiswim", "", raw=["cx-spin 1.6s linear infinite"]),
    P("fx-koibubble", "", raw=["cx-kr-bubble .9s ease-out infinite"]),
], props=[("koi", 1, KOI), ("splash", 1, SPLASH)])
R("valkyrie", "great", [
    P("fx-koiswim", "", raw=["cx-spin 2.2s linear infinite"]),
    P("p-bubbles", "", None, (1.8, EASE_OUT, {15: "opacity:1", 90: "opacity:0; transform:translateY(-7px)"}), at=.2),
    P("fx-koiwater", "", (1.2, EASE_IO, {30: "transform:translateY(-.5px)", 60: "transform:translateY(.3px)"}), at=.1),
], props=[("bubbles", 1, "".join(circ(x, y, r, "none", .9, "#E8FAFF", .22) for x, y, r in [(17.6, 23.4, .7), (20.6, 25, .5), (23, 22.6, .6), (19.4, 21, .4)]))])
R("valkyrie", "pass", [
    P("p-bubbles2", "", (1.8, EASE_OUT, {15: "opacity:1", 90: "opacity:0; transform:translateY(-6px)"}), at=.3),
    P("fx-koiswim", "", raw=["cx-spin 3.6s linear infinite"]),
], props=[("bubbles2", 1, circ(18.6, 24, .6, "none", .9, "#E8FAFF", .22) + circ(21.8, 25.2, .45, "none", .9, "#E8FAFF", .22))])
R("valkyrie", "fail", [
    P("fx-koiswim", "transform:translateY(3.6px) rotate(25deg); opacity:.75", (1.8, EASE_OUT, {})),
    P("fx-koiwater", "opacity:.72", (1.4, EASE_OUT, {})),
    P("fx-koibubble", "opacity:0", (.8, EASE_OUT, {})),
    P("p-onebubble", "", None, (4.2, EASE_OUT, {10: "opacity:.9", 90: "opacity:0; transform:translateY(-8px)"}), at=1.0),
], props=[("onebubble", 1, circ(21, 25.6, .55, "none", .9, "#E8FAFF", .22))])

# ---- MARKSMAN: locks on and fires ----------------------------------------------
R("marksman", "perfect", [
    P("fx-reticle", "", (1.8, EASE_OUT, {0: "transform:scale(2.6) rotate(-120deg)", 40: "transform:none", 48: "transform:scale(1.3)", 56: "transform:none"})),
    P("fx-mk3lock", "opacity:1", (1.8, "linear", {40: "opacity:0", 44: "opacity:1; transform:scale(1.5)", 56: "transform:none"}), (1.6, EASE_IO, {50: "opacity:.55"})),
    P("fx-mkrifle", "", (1.8, "linear", {56: "transform:none", 60: "transform:translate(-1.1px,1.3px)", 72: "transform:none"})),
    P("p-muzzle", "", (1.8, "linear", {55: "opacity:0; transform:scale(.3)", 59: "opacity:1; transform:scale(1.15)", 68: "opacity:0; transform:scale(1.25) rotate(20deg)"})),
    P("p-ping", "", (1.8, "linear", {44: "opacity:0; transform:scale(.5)", 48: "opacity:1; transform:scale(.8)", 72: "opacity:0; transform:scale(2.3)"}),
      (2.4, "ease-out", {6: "opacity:.8; transform:scale(.8)", 50: "opacity:0; transform:scale(2.2)"})),
    P("fx-led", "", raw=["cx-led .5s steps(1, end) infinite"]),
    P("eyes", "transform:scaleY(.55)", (.6, EASE_OUT, {}), at=.9),
], props=[("muzzle", 1, pivot(34.2, 8.8, 2.2) + star4(34.2, 8.8, 1.9, "#FFE07A") + star4(34.2, 8.8, 1.0, "#FFFFFF", w=.45)),
          ("ping", 1, circ(17.3, 21.5, 2.4, "none", 1, "#7CFF9E", .4))])
R("marksman", "great", [
    P("fx-reticle", "", (1.2, EASE_OUT, {0: "transform:scale(1.9) rotate(-80deg)", 55: "transform:none", 70: "transform:scale(1.15)"})),
    P("fx-mk3lock", "opacity:.8", (1.2, "linear", {50: "opacity:0", 55: "opacity:1; transform:scale(1.3)", 75: "transform:none"}), (2.0, EASE_IO, {50: "opacity:.4"})),
    P("fx-mk3glint", "", None, (2.6, "linear", {40: "opacity:0", 48: "opacity:1; transform:scale(1.3) rotate(45deg)", 58: "opacity:0"}), at=.8),
])
R("marksman", "pass", [
    P("fx-mk3glint", "", (1.2, "linear", {30: "opacity:0", 45: "opacity:1; transform:scale(1.3) rotate(45deg)", 65: "opacity:0"}), at=.25),
    nod(1.1, .1, .8),
])
R("marksman", "fail", [
    P("fx-reticle", "transform:translate(2.6px,2.2px) rotate(38deg); opacity:.4", (1.8, EASE_IO, {25: "transform:translate(-1px,.6px) rotate(10deg)",
                                                                                                 55: "transform:translate(1.8px,-.8px) rotate(24deg)"})),
    P("fx-led", "opacity:.25", (1.0, "steps(4, end)", {25: "opacity:1", 50: "opacity:.2", 75: "opacity:1"}), at=.2),
    P("eyes", "transform:translateY(.4px) scaleY(.7)", (.8, EASE_OUT, {}), at=.3),
    slump(-7, 1.4),
])

# ---- ORION (the astronaut id): draws the blade of light -------------------------
R("astronaut", "perfect", [
    P("fx-sablade", "transform:translate(-3px,-4px) rotate(-35deg)", (2.0, EASE_IO, {18: "transform:translateY(1.2px)", 38: "transform:translate(-1px,-5px) rotate(-10deg)",
                                                                                     54: "transform:translate(-3.4px,-4.6px) rotate(-44deg)", 70: "transform:translate(-3px,-4.2px) rotate(-33deg)"}),
      (2.2, EASE_IO, {50: "transform:translate(-3px,-4.4px) rotate(-37deg)"})),
    P("p-tip", "", (2.0, "linear", {56: "opacity:0; transform:scale(.3)", 62: "opacity:1; transform:scale(1.3) rotate(45deg)", 80: "opacity:0; transform:scale(.6) rotate(90deg)"}),
      (2.2, "linear", {40: "opacity:0; transform:scale(.4)", 50: "opacity:1; transform:scale(1.1) rotate(45deg)", 70: "opacity:0; transform:scale(.5) rotate(90deg)"})),
    P("fx-saglow", "", raw=["cx-mk2-pulse .7s ease-in-out infinite"]),
    P("fx-sa5surge", "opacity:.85", (2.0, "linear", {38: "opacity:0", 46: "opacity:1", 60: "opacity:.6"}), (1.2, EASE_IO, {50: "opacity:.45"})),
    P("fx-sa5meteor", "", (1.4, "linear", {0: "opacity:0; transform:translate(3px,-2px)", 10: "opacity:1; transform:translate(3px,-2px)",
                                            62: "opacity:1; transform:translate(-14px,9px)", 72: "opacity:0; transform:translate(-16px,10px)"}),
      (3.4, "linear", {62: "opacity:0; transform:translate(3px,-2px)", 66: "opacity:1; transform:translate(3px,-2px)", 92: "opacity:0; transform:translate(-14px,9px)"}), at=.7),
    P("fx-sa5visor", "opacity:1", (1.0, "linear", {30: "opacity:1", 40: "opacity:.3", 55: "opacity:1"}), (1.6, EASE_IO, {50: "opacity:.55"}), at=.6),
    P("fx-sascarf", "", raw=["cx-flutter .5s ease-in-out infinite"]),
    P("fx-sa3line", "", raw=["cx-glow .8s ease-in-out infinite"]),
], props=[("tip", 1, pivot(24.4, 11.7, 2.4) + star4(24.4, 11.7, 2.3, "#D8F6FF") + star4(24.4, 11.7, 1.0, "#FFFFFF", w=.45))],
  flash=("rgba(150,220,255,.8)", .85))
R("astronaut", "great", [
    P("fx-sa5surge", "opacity:.6", (1.2, EASE_OUT, {40: "opacity:1"}), (1.6, EASE_IO, {50: "opacity:.3"}), at=.2),
    P("fx-sablade", "transform:translateY(-1.2px)", (1.0, SPRING, {}), at=.2),
    P("fx-sascarf", "", raw=["cx-flutter .9s ease-in-out infinite"]),
    P("fx-sa5visor", "", (1.2, "linear", {30: "opacity:1", 60: "opacity:.2", 80: "opacity:.8"}), at=.3),
])
R("astronaut", "pass", [
    P("fx-sa5visor", "", (1.1, EASE_IO, {30: "opacity:1", 65: "opacity:.7"}), at=.25),
    nod(1.1, .1, .8),
])
R("astronaut", "fail", [
    P("fx-sablade", "transform:translateY(3px); opacity:.45", (1.4, EASE_OUT, {})),
    P("fx-saglow", "opacity:.25", (1.2, EASE_OUT, {})),
    P("fx-saeye", "opacity:.45", (1.0, EASE_OUT, {}), at=.3),
    P("fx-sascarf", "transform:rotate(7deg)", (1.2, EASE_OUT, {})),
    slump(-8, 1.5),
])

# ---- HACKER: the code floods and the screen flashes ACCESS ---------------------
ACCESS = rect(12.6, 29, 14.8, 4.6, .8, "#04240F", "#3DFF8B", .35) + text(20, 32.4, "ACCESS", 2.9, "#8CFFB8", 800, .05)
DENIED = rect(12.6, 29, 14.8, 4.6, .8, "#2A0610", "#FF4D6A", .35) + text(20, 32.4, "DENIED", 2.9, "#FF9AAB", 800, .05)
R("hacker", "perfect", [
    P("fx-hk3rain", "", raw=["cx-hk3-rain .45s linear infinite"]),
    P("fx-hk3code", "", raw=["cx-hk3-code .5s linear infinite"]),
    P("fx-hk3glow", "", None, (1.2, EASE_IO, {50: "opacity:.6"}), at=.3),
    P("p-access", "opacity:1", (2.0, "linear", {25: "opacity:0; transform:scale(.6)", 31: "opacity:1; transform:scale(1.08)", 36: "opacity:.15; transform:none",
                                                41: "opacity:1", 46: "opacity:.15", 52: "opacity:1"}), (1.8, EASE_IO, {50: "opacity:.7"})),
    P("head", "transform:translateY(-.5px) rotate(-2deg)", (1.6, EASE_OUT, {40: "transform:translateY(-.8px) rotate(-3deg)"}), at=.4),
], props=[("access", 1, ACCESS)], flash=("rgba(70,255,140,.55)", .55))
R("hacker", "great", [
    P("fx-hk3code", "", raw=["cx-hk3-code .9s linear infinite"]),
    P("fx-hk3rain", "", raw=["cx-hk3-rain .9s linear infinite"]),
    P("fx-hk2slice", "", (1.3, "linear", {12: "opacity:1; transform:translateY(-4px)", 70: "opacity:1; transform:translateY(4px)", 85: "opacity:0"}), at=.2),
    P("fx-hk3glow", "", None, (1.4, EASE_IO, {50: "opacity:.5"}), at=.2),
])
R("hacker", "pass", [
    P("fx-hk2slice", "", (1.2, "linear", {15: "opacity:1; transform:translateY(-4px)", 70: "opacity:1; transform:translateY(4px)", 85: "opacity:0"}), at=.2),
    nod(1.1, .1, .8),
])
R("hacker", "fail", [
    P("p-denied", "opacity:.9", (1.4, "linear", {10: "opacity:1", 18: "opacity:.1", 26: "opacity:1", 34: "opacity:.1", 42: "opacity:1"}), at=.2),
    P("fig", "", (.9, "steps(1, end)", {10: "transform:translateX(-1px)", 20: "transform:translateX(1px)", 30: "transform:translateX(-.6px)", 40: "transform:none"}), at=.2),
    P("fx-hk3glow", "opacity:.25", (1.2, EASE_OUT, {})),
    P("fx-hk3rain", "opacity:.35", (1.2, EASE_OUT, {})),
    slump(-7, 1.4, at=.5),
], props=[("denied", 1, DENIED)])

# ---- TIMEKEEPER: the hands race round and chime at twelve ---------------------
R("timekeeper", "perfect", [
    P("fx-hand-m", "", (2.0, "cubic-bezier(.25,.55,.25,1)", {0: "transform:rotate(-1080deg)"}), raw=["cx-spin 5s linear 2s infinite"]),
    P("fx-hand-h", "", (2.0, "cubic-bezier(.25,.55,.25,1)", {0: "transform:rotate(-360deg)"}), raw=["cx-spin 60s linear 2s infinite"]),
    P("p-chime", "", (2.3, "linear", {84: "opacity:0; transform:scale(.88)", 88: "opacity:1; transform:scale(.97)", 99: "opacity:0; transform:scale(1.08)"}),
      (2.5, "ease-out", {5: "opacity:.75; transform:scale(.97)", 40: "opacity:0; transform:scale(1.07)"})),
    P("fx-dial", "", (2.3, "linear", {84: "transform:none", 88: "transform:scale(1.05)", 96: "transform:none"})),
    P("fx-sand", "", raw=["cx-sand .35s linear infinite"]),
    P("p-twelve", "", (2.3, "linear", {84: "opacity:0; transform:scale(.3)", 89: "opacity:1; transform:scale(1.3) rotate(45deg)", 100: "opacity:0; transform:scale(.6) rotate(90deg)"}),
      (2.5, "linear", {3: "opacity:1; transform:scale(1.1) rotate(45deg)", 22: "opacity:0; transform:scale(.6) rotate(90deg)"})),
    P("p-dialglow", "", (2.3, "linear", {84: "opacity:0", 88: "opacity:.9", 100: "opacity:0"}), (2.5, "ease-out", {4: "opacity:.55", 40: "opacity:0"})),
    P("p-sweep", "", (2.0, "cubic-bezier(.25,.55,.25,1)", {0: "opacity:0; transform:rotate(-1080deg)", 8: "opacity:.95", 82: "opacity:.85", 100: "opacity:0; transform:none"})),
] + joy(1.9), props=[("sweep", 0, pivot(20, 17, 12.2) + path("M20 17 L20 5.2 A11.8 11.8 0 0 1 27.6 8 Z", fill="#FFD86B", op=.5) +
                                path("M20 17 L20 5.2", stroke="#FFF3C4", sw=.6)),
                      ("dialglow", 0, circ(20, 17, 12, "#FFD86B", .32)),
                      ("chime", 0, circ(20, 17, 11.8, "none", 1, "#FFE08A", .7) + circ(20, 17, 12.8, "none", .6, "#FFE08A", .4)),
                      ("twelve", 1, pivot(20, 5.6, 2.4) + star4(20, 5.6, 2.3, "#FFF3C4") + star4(20, 5.6, 1.1, "#FFFFFF", w=.45))])
R("timekeeper", "great", [
    P("fx-hand-m", "", (1.4, "cubic-bezier(.3,.6,.3,1)", {0: "transform:rotate(-360deg)"}), raw=["cx-spin 8s linear 1.4s infinite"]),
    P("fx-dial", "", (1.4, "linear", {80: "transform:none", 86: "transform:scale(1.04)", 94: "transform:none"})),
] + joy(1.2))
R("timekeeper", "pass", [
    P("fx-hand-m", "transform:rotate(30deg)", (.6, "cubic-bezier(.3,1.6,.5,1)", {}), at=.35),
    nod(1.1, .1, .8),
])
R("timekeeper", "fail", [
    P("fx-hand-m", "transform:rotate(120deg)", (1.6, "cubic-bezier(.6,0,.8,.6)", {})),
    P("fx-hand-h", "transform:rotate(-120deg)", (1.6, "cubic-bezier(.6,0,.8,.6)", {})),
    P("fx-sand", "opacity:.15", (1.0, EASE_OUT, {})),
    P("fx-dial", "opacity:.55", (1.4, EASE_OUT, {})),
    slump(-7, 1.4),
    eyes_down(.5, .7),
])

# ---- RONIN: draws and flicks the blade, petals burst ----------------------------
SLASH = path("M6.6 30.6 Q16 12.6 34.2 8.6 Q19.6 15.2 8.6 31.6Z", fill="#FFE6F2", op=.95)
R("ronin", "perfect", [
    P("fx-roninblade", "", (2.0, EASE_IO, {16: "transform:translate(-1px,-3.6px)", 32: "transform:translate(-2px,-4.6px) rotate(-38deg)",
                                           44: "transform:translate(-1px,-3.8px) rotate(22deg)", 60: "transform:translate(0,-1px) rotate(-6deg)", 74: "transform:none"})),
    P("p-slash", "", (2.0, "linear", {38: "opacity:0; transform:scale(.7)", 42: "opacity:1; transform:scale(1)", 54: "opacity:0; transform:scale(1.06)"})),
    P("fx-ronin2slash, fx-ronin2slash2", "", (2.0, "linear", {40: "opacity:0", 44: "opacity:1", 60: "opacity:0"})),
    P("fx-ronin2petals", "opacity:.9; transform:translateY(-.6px)", (2.0, EASE_OUT, {44: "opacity:0; transform:scale(.6)", 52: "opacity:1; transform:scale(1.1) translateY(-2px)",
                                                                                  80: "opacity:.9; transform:translateY(-1.4px) rotate(8deg)"}),
      (3.0, EASE_IO, {50: "transform:translate(.6px,.4px) rotate(5deg)"})),
    P("fx-ronineye", "", (2.0, "linear", {42: "transform:none", 46: "transform:scale(1.5, 1.3)", 60: "transform:none"})),
    P("fx-ronin2glint", "", (2.0, "linear", {14: "opacity:0", 20: "opacity:1; transform:scale(1.4) rotate(45deg)", 30: "opacity:0"})),
    P("fx-roninscarf", "", raw=["cx-ronin-scarf .45s ease-in-out infinite alternate"]),
], props=[("slash", 1, SLASH)], flash=("rgba(255,70,150,.75)", .85))
R("ronin", "great", [
    P("fx-ronin2glint", "", (1.2, "linear", {20: "opacity:0", 30: "opacity:1; transform:scale(1.4) rotate(45deg)", 45: "opacity:0"}), at=.1),
    P("p-slash", "", (1.4, "linear", {40: "opacity:0; transform:scale(.7)", 46: "opacity:.85; transform:scale(1)", 60: "opacity:0; transform:scale(1.05)"}), at=.1),
    P("fx-roninblade", "", (1.4, EASE_IO, {30: "transform:translate(-.6px,-2.4px) rotate(-14deg)", 60: "transform:none"}), at=.1),
    P("fx-roninscarf", "", raw=["cx-ronin-scarf .8s ease-in-out infinite alternate"]),
], props=[("slash", 1, SLASH)])
R("ronin", "pass", [
    P("fx-ronin2brim", "", (1.2, "linear", {25: "opacity:0", 40: "opacity:1", 70: "opacity:0"}), at=.2),
    P("head", "", (1.1, EASE_IO, {30: "transform:translateY(1.3px) rotate(2deg)", 62: "transform:none"}), at=.1),
])
R("ronin", "fail", [
    P("head", "transform:translateY(2.3px) rotate(-5deg)", (1.4, EASE_OUT, {}), (3.8, EASE_IO, {50: "transform:translateY(2.6px) rotate(-6deg)"})),
    P("fx-roninblade", "transform:translateY(2.6px); opacity:.45", (1.4, EASE_OUT, {})),
    P("fx-ronineye", "opacity:.4", (1.0, EASE_OUT, {}), at=.3),
    P("fx-ronin2petals", "opacity:.6; transform:translateY(.9px)", (2.2, EASE_OUT, {0: "opacity:0; transform:translateY(-3px)", 30: "opacity:.8"})),
    P("fx-roninscarf", "transform:rotate(14deg)", (1.2, EASE_OUT, {})),
])

# ---- HIVE: the swarm comes out and circles ---------------------------------------
BEE = lambda x, y, k=1: (ell(x, y, .9 * k, .62 * k, "#FFC93A") + line(x - .15 * k, y - .55 * k, x - .15 * k, y + .55 * k, "#3A2A10", .26 * k) +
                         line(x + .35 * k, y - .5 * k, x + .35 * k, y + .5 * k, "#3A2A10", .22 * k) + ell(x - .1 * k, y - .8 * k, .5 * k, .32 * k, "#FFFFFF", .8))
SWARM = pivot(20, 18, 15.6) + "".join(BEE(20 + 15 * __import__("math").cos(a), 18 + 13 * __import__("math").sin(a), .95)
                                      for a in [i * 1.2566 + .4 for i in range(5)])
R("hive", "perfect", [
    P("fx-hivebees", "", (2.0, EASE_OUT, {0: "transform:rotate(-720deg)"}),
      raw=["cx-spin 1.9s linear 2s infinite"]),
    P("p-swarm", "opacity:1", (2.0, EASE_OUT, {0: "opacity:0; transform:scale(.3) rotate(450deg)", 25: "opacity:1; transform:scale(1.05) rotate(300deg)"}),
      turn=(2.6, -1)),
    P("mouth", "transform:scaleY(1.5)", (.8, SPRING, {}), at=.3),
] + joy(.4), props=[("swarm", 1, SWARM)])
R("hive", "great", [
    P("fx-hivebees", "", (1.4, EASE_OUT, {0: "transform:rotate(-360deg)"}), raw=["cx-spin 3s linear 1.4s infinite"]),
    P("mouth", "transform:scaleY(1.25)", (.8, SPRING, {}), at=.3),
] + joy(.3))
R("hive", "pass", [
    P("fx-hivebees", "", (1.0, "linear", {10: "transform:translate(.5px,-.4px)", 20: "transform:translate(-.5px,.4px)", 30: "transform:translate(.4px,.3px)",
                                          40: "transform:translate(-.4px,-.3px)", 50: "transform:none"}), at=.2),
    P("mouth", "", (1.0, EASE_IO, {40: "transform:scaleY(1.3)"}), at=.3),
    nod(1.1, .1, .8),
])
R("hive", "fail", [
    P("fx-hivebees", "opacity:.45; transform:translateY(2.2px) scale(.9)", (1.8, EASE_OUT, {})),
    P("p-honey", "", None, (3.0, "cubic-bezier(.5,0,1,.6)", {10: "opacity:1", 62: "opacity:1; transform:translateY(5.6px)", 72: "opacity:0; transform:translateY(6.4px)"}), at=.8),
    P("mouth", "transform:scaleY(.7)", (.8, EASE_OUT, {}), at=.3),
    eyes_down(.5, .7, op=.7),
    slump(-6, 1.3),
], props=[("honey", 1, drop(19.6, 27.4, .6, "#FFB82E"))])

# ================================================================= SECRETS ===

# ---- VOID: the flares whip into orbit, a ring bursts off the face ---------------
R("voidwalker", "perfect", [
    P("fx-flares", "", (2.0, "cubic-bezier(.2,.6,.3,1)", {0: "transform:rotate(-720deg)", 35: "transform:rotate(-300deg) scale(1.35)", 70: "transform:rotate(-40deg) scale(1.1)"}),
      turn=(7, 1)),
    P("fx-starfield", "", (2.0, EASE_OUT, {0: "transform:rotate(180deg)"}), raw=["cx-spin 14s linear 2s infinite"]),
    P("p-burst", "", (2.0, "linear", {28: "opacity:0; transform:scale(.6)", 36: "opacity:1; transform:scale(1)", 64: "opacity:0; transform:scale(2.3)"}),
      (2.8, "ease-out", {8: "opacity:.85; transform:scale(1)", 55: "opacity:0; transform:scale(2.3)"})),
], props=[("burst", 0, circ(20, 20, 5.6, "none", 1, "#FFB86B", .55) + circ(20, 20, 3.8, "none", .9, "#FF5D8F", .4))],
  flash=("rgba(255,150,90,.7)", .6))
R("voidwalker", "great", [
    P("fx-flares", "", (1.4, EASE_OUT, {0: "transform:rotate(-360deg)", 40: "transform:rotate(-120deg) scale(1.2)"}), (2.0, EASE_IO, {50: "transform:scale(1.12)"})),
    P("fx-starfield", "", raw=["cx-spin 20s linear infinite"]),
])
R("voidwalker", "pass", [
    P("fx-flares", "", (1.1, EASE_IO, {40: "transform:scale(1.22)"}), at=.2),
    nod(1.1, .1, .8),
])
R("voidwalker", "fail", [
    P("fx-flares", "transform:translateY(1.9px) scale(.74); opacity:.38", (1.8, EASE_OUT, {})),
    P("fx-starfield", "opacity:.4", (1.6, EASE_OUT, {})),
    slump(-7, 1.5),
])

# ---- UMBRA: the moon comes full, the shadow flames rise --------------------------
R("umbra", "perfect", [
    P("fx-umdark", "transform:scaleX(0)", (1.6, EASE_IO, {0: "transform:scaleX(.8)"})),
    P("fx-umlit", "transform:scaleX(1)", (1.6, EASE_IO, {0: "transform:scaleX(0)"})),
    P("fx-umcglow", "opacity:1", (1.6, EASE_OUT, {50: "opacity:.4", 70: "opacity:1"}), (1.6, EASE_IO, {50: "opacity:.5"})),
    P("fx-umaura", "transform:scaleX(1.1); opacity:.95", (1.8, EASE_OUT, {35: "transform:scaleX(1.2); opacity:1"}),
      (1.4, EASE_IO, {50: "transform:scaleX(1.14); opacity:.7"})),
    P("eyes", "transform:scale(1.12, 1.25)", (.9, SPRING, {}), at=.5),
    P("fx-umflare", "", raw=["cx-mk2-pulse .9s ease-in-out infinite"]),
    P("fx-wfring", "", raw=["cx-wf-ring 1.2s ease-out infinite"]),
], flash=("rgba(170,120,255,.75)", 1.0))
R("umbra", "great", [
    P("fx-umaura", "transform:scaleX(1.06); opacity:.85", (1.2, EASE_OUT, {}), (1.8, EASE_IO, {50: "transform:scaleX(1.1); opacity:.6"})),
    P("eyes", "transform:scale(1.08, 1.15)", (.8, SPRING, {}), at=.3),
    P("fx-umflare", "", raw=["cx-mk2-pulse 1.4s ease-in-out infinite"]),
    P("fx-umcglow", "", (1.2, EASE_IO, {45: "opacity:1"}), at=.2),
])
R("umbra", "pass", [
    P("fx-umcglint", "", (1.2, "linear", {25: "opacity:0", 40: "opacity:1; transform:scale(1.5) rotate(45deg)", 65: "opacity:0"}), at=.3),
    nod(1.1, .1, .8),
])
R("umbra", "fail", [
    P("fx-umaura, fx-umaura2", "transform:scale(.92, .55); opacity:.45", (1.6, EASE_OUT, {})),
    P("fx-umlit", "transform:scaleX(0)", (1.4, EASE_OUT, {})),
    P("fx-umdark", "transform:scaleX(.95)", (1.4, EASE_OUT, {})),
    P("eyes", "opacity:.45; transform:translateY(.5px) scaleY(.75)", (1.0, EASE_OUT, {}), at=.3),
    slump(-7, 1.5),
])

# ---- HORIZON (the singularity id): the sun rises in it -----------------------------
R("singularity", "perfect", [
    P("fx-sgsurgeb, fx-sgsurgew", "", (1.8, "linear", {20: "opacity:0", 28: "opacity:1", 50: "opacity:.4", 64: "opacity:.9", 82: "opacity:0"})),
    P("fx-sgrise", "opacity:.85", (1.8, EASE_OUT, {25: "opacity:0", 45: "opacity:1"}), (1.6, EASE_IO, {50: "opacity:.45"})),
    P("fx-sghair", "transform:scale(1.05, 1.08)", (1.8, EASE_OUT, {35: "transform:scale(1.1, 1.16)"}), (2.0, EASE_IO, {50: "transform:scale(1.08, 1.13)"})),
    P("fx-sgstar", "transform:scale(1.15)", (1.8, EASE_OUT, {30: "transform:scale(1.8) rotate(45deg)", 55: "transform:scale(1.1) rotate(90deg)"}),
      (1.6, EASE_IO, {50: "transform:scale(1.35)"})),
    P("fx-sgsparks", "opacity:1", (1.0, EASE_OUT, {}), raw=["cx-flicker-soft 1.2s ease-in-out 1s infinite"], at=.5),
], flash=("rgba(150,200,255,.75)", .4))
R("singularity", "great", [
    P("fx-sghair", "transform:scale(1.03, 1.05)", (1.2, EASE_OUT, {}), (2.2, EASE_IO, {50: "transform:scale(1.05, 1.09)"})),
    P("fx-sgstar", "", (1.2, EASE_OUT, {35: "transform:scale(1.5) rotate(45deg)"}), (1.8, EASE_IO, {50: "transform:scale(1.22)"})),
    P("fx-sgsparks", "opacity:.8", (1.0, EASE_OUT, {})),
])
R("singularity", "pass", [
    P("fx-sgstar", "", (1.1, EASE_IO, {40: "transform:scale(1.4) rotate(45deg)"}), at=.25),
    nod(1.1, .1, .8),
])
R("singularity", "fail", [
    P("fx-sghair", "transform:scale(.94, .8); opacity:.55", (1.6, EASE_OUT, {})),
    P("fx-sglight", "opacity:.15", (1.4, EASE_OUT, {})),
    P("fx-sgstar", "transform:scale(.7); opacity:.3", (1.4, EASE_OUT, {})),
    P("fx-sgvisor", "opacity:.45", (1.0, EASE_OUT, {}), at=.3),
    slump(-7, 1.5),
])

# ---- GENESIS: the planet wakes - the moon whips round, the world erupts ------------
R("genesis", "perfect", [
    P("fx-gnspin", "", (2.0, "cubic-bezier(.2,.6,.3,1)", {0: "transform:rotate(-682deg)"}), raw=["cx-gn-spin 3s linear 2s infinite"]),
    P("fx-gnmoonfront", "", raw=["cx-gn-front .667s linear infinite"]),
    P("fx-gnerupt", "", (2.0, "linear", {20: "opacity:0; transform:scaleY(.3)", 30: "opacity:1; transform:scaleY(1.2)", 55: "opacity:.8; transform:none", 75: "opacity:0"}),
      (2.4, "ease-out", {15: "opacity:.9; transform:scaleY(1.1)", 50: "opacity:0; transform:none"})),
    P("fx-gnatm", "transform:scale(1.05)", (2.0, EASE_OUT, {35: "transform:scale(1.15)"}), (2.0, EASE_IO, {50: "transform:scale(1.1)"})),
    P("fx-gnheart", "transform:scale(1.1)", (1.6, EASE_OUT, {30: "transform:scale(1.45)"}), (.9, EASE_IO, {30: "transform:scale(1.28)", 55: "transform:scale(1.12)"})),
    P("fx-gnbands", "", raw=["cx-gn-drift 4s linear infinite"]),
    P("eyes", "transform:scale(1.1, 1.18)", (.8, SPRING, {}), at=.5),
], flash=("rgba(255,140,200,.75)", .55))
R("genesis", "great", [
    P("fx-gnspin", "", raw=["cx-gn-spin 4s linear infinite"]),
    P("fx-gnmoonfront", "", raw=["cx-gn-front 4s linear infinite"]),
    P("fx-gnheart", "", (1.0, EASE_OUT, {35: "transform:scale(1.35)"}), (1.2, EASE_IO, {30: "transform:scale(1.2)", 55: "transform:none"}), at=.2),
])
R("genesis", "pass", [
    P("fx-gnheart", "", (1.1, EASE_IO, {40: "transform:scale(1.35)"}), at=.25),
    nod(1.1, .1, .8),
])
R("genesis", "fail", [
    P("fx-gnatm", "opacity:.25", (1.6, EASE_OUT, {})),
    P("fx-gnbands", "opacity:.55", (1.6, EASE_OUT, {})),
    P("fx-gnheart", "opacity:.35; transform:scale(.85)", (1.4, EASE_OUT, {})),
    P("fx-gnspin", "", raw=["cx-gn-spin 30s linear infinite"]),
    P("eyes", "opacity:.5; transform:translateY(.5px) scaleY(.7)", (1.0, EASE_OUT, {}), at=.3),
    slump(-6, 1.3),
])

# ============================================================ RANK REWARDS ===

# ---- LUNAR: her two moons trade places round her head ----------------------------
R("lunar", "perfect", [
    P("fx-moon1", "transform:translate(24px,7px)", (2.2, EASE_IO, {30: "transform:translate(6px,-7px) scale(1.7)", 60: "transform:translate(16px,-6px) scale(1.7)"}),
      (3.0, EASE_IO, {50: "transform:translate(24.5px,6px)"})),
    P("fx-moon2", "transform:translate(-24px,-7px)", (2.2, EASE_IO, {30: "transform:translate(-4px,8px) scale(1.7)", 60: "transform:translate(-15px,7px) scale(1.7)"}),
      (3.4, EASE_IO, {50: "transform:translate(-24.4px,-7.8px)"})),
    P("fx-moonstar", "transform:scale(1.15)", (2.0, EASE_OUT, {30: "transform:scale(1.9) rotate(45deg)", 60: "transform:scale(1.2) rotate(90deg)"}),
      (1.4, EASE_IO, {50: "transform:scale(1.45) rotate(20deg)"})),
    P("fx-dust", "", raw=["cx-dust .9s ease-in-out infinite"]),
    P("fx-crown", "", (2.0, "linear", {30: "opacity:1", 40: "opacity:.6", 55: "opacity:1"})),
] + joy(.6), flash=("rgba(220,230,255,.7)", .65))
R("lunar", "great", [
    P("fx-moon1", "transform:translate(2.4px,-1.4px)", (1.4, EASE_IO, {}), (2.6, EASE_IO, {50: "transform:translate(3px,-2.2px)"})),
    P("fx-moon2", "transform:translate(-2.2px,-1.2px)", (1.4, EASE_IO, {}), (2.9, EASE_IO, {50: "transform:translate(-2.8px,-2px)"})),
    P("fx-moonstar", "", (1.2, EASE_OUT, {35: "transform:scale(1.6) rotate(45deg)"}), (1.8, EASE_IO, {50: "transform:scale(1.3) rotate(20deg)"})),
] + joy(.4))
R("lunar", "pass", [
    P("fx-moonstar", "", (1.1, EASE_IO, {40: "transform:scale(1.5) rotate(45deg)"}), at=.25),
    nod(1.1, .1, .8),
])
R("lunar", "fail", [
    P("fx-moon1", "transform:translateY(3.2px); opacity:.32", (1.6, EASE_OUT, {})),
    P("fx-moon2", "transform:translateY(3px); opacity:.32", (1.6, EASE_OUT, {}), at=.15),
    P("fx-moonstar", "opacity:.35; transform:scale(.8)", (1.2, EASE_OUT, {})),
    P("fx-dust", "opacity:.3", (1.2, EASE_OUT, {})),
    eyes_down(.6, .7),
    slump(-7, 1.4),
])

# ---- SOLAR: the corona flares out; a fail clouds the sun over ---------------------
RAYS = pivot(20, 15.6, 13) + "".join(
    path("M%s %s L%s %s L%s %sZ" % (f2(20 + 9.6 * __import__("math").cos(a - .07)), f2(15.6 + 9.6 * __import__("math").sin(a - .07)),
                                    f2(20 + 12 * __import__("math").cos(a)), f2(15.6 + 12 * __import__("math").sin(a)),
                                    f2(20 + 9.6 * __import__("math").cos(a + .07)), f2(15.6 + 9.6 * __import__("math").sin(a + .07))), fill="#FFD54A", op=.7)
    for a in [i * 0.5236 for i in range(12)])
R("solar", "perfect", [
    P("fx-corona", "transform:scale(1.05) rotate(60deg)", (2.0, EASE_OUT, {28: "transform:scale(1.13) rotate(25deg)", 60: "transform:scale(1.09) rotate(50deg)"}),
      turn=(14, 1)),
    P("p-rays", "", (2.0, EASE_OUT, {18: "opacity:0; transform:scale(.6)", 32: "opacity:1; transform:scale(1)", 75: "opacity:0; transform:scale(1.04) rotate(15deg)"}),
      (3.0, EASE_OUT, {10: "opacity:.7; transform:scale(.85)", 70: "opacity:0; transform:scale(1.03) rotate(12deg)"})),
    P("fx-crown", "", (2.0, EASE_OUT, {25: "transform:scale(1.12)", 45: "transform:none"})),
    P("fx-gem", "", None, (1.2, EASE_IO, {50: "transform:scale(1.25)"}), at=.6),
] + joy(.5), props=[("rays", 0, RAYS)], flash=("rgba(255,214,90,.9)", .45))
R("solar", "great", [
    P("fx-corona", "transform:scale(1.03)", (1.2, EASE_OUT, {35: "transform:scale(1.08) rotate(20deg)", 100: "transform:scale(1.03) rotate(30deg)"}),
      raw=["cx-spin 8s linear 1.2s infinite"]),
    P("fx-crown", "", (1.2, EASE_OUT, {35: "transform:scale(1.08)"})),
] + joy(.35))
R("solar", "pass", [
    P("p-glint", "", (1.2, "linear", {25: "opacity:0", 40: "opacity:1; transform:scale(1.4) rotate(45deg)", 65: "opacity:0"}), at=.3),
    nod(1.1, .1, .8),
], props=[("glint", 1, pivot(20, 10.6, 1.8) + star4(20, 10.6, 1.6, "#FFFFFF"))])
R("solar", "fail", [
    P("fx-corona", "transform:scale(.8); opacity:.45", (1.6, EASE_OUT, {})),
    P("p-cloud", "opacity:1", (1.6, EASE_OUT, {0: "opacity:0; transform:translateX(-9px)"}), (5.0, EASE_IO, {50: "transform:translateX(1.2px)"})),
    eyes_down(.6, .7),
    slump(-7, 1.4),
], props=[("cloud", 1, puff([(14.4, 7.6, 2.3), (17.6, 6.4, 2.7), (21.2, 7.6, 2.2), (17.4, 8.6, 2.4)], "#7C8594", .95))])

# ---- TEMPEST: the storm breaks - lightning, wind, the circle flashes --------------
BOLTS_T = bolt(6.2, 4.6, 1.05, "#E9FDFF", "#7DF0FF", .3) + bolt(33.4, 5.4, 1.0, "#E9FDFF", "#7DF0FF", .3, flip=True)
R("tempest", "perfect", [
    P("fx-arc1, fx-arc2", "", (1.8, "linear", {5: "opacity:.2", 10: "opacity:1", 15: "opacity:.3", 20: "opacity:1", 30: "opacity:.2", 35: "opacity:1"}),
      raw=["cx-crackle 1s linear 1.8s infinite"]),
    P("fx-cloudflash", "", (1.8, "linear", {8: "opacity:1", 12: "opacity:.1", 18: "opacity:.9", 26: "opacity:0", 44: "opacity:.8", 50: "opacity:0"}),
      raw=["cx-cloudflash 1s linear 1.8s infinite"]),
    P("p-bolts", "", (1.8, "linear", {40: "opacity:0", 43: "opacity:1", 47: "opacity:.2", 51: "opacity:1", 60: "opacity:0"})),
    P("fx-crown", "", (1.8, "linear", {8: "opacity:.5", 16: "opacity:1", 44: "opacity:.5", 52: "opacity:1"})),
    P("fx-wind", "", raw=["cx-gust .7s ease-in-out infinite"]),
    P("fx-wind2", "", raw=["cx-gust .7s ease-in-out -.35s infinite"]),
    P("eyes", "transform:scale(1.1, 1.2)", (.8, SPRING, {}), at=.3),
], props=[("bolts", 1, BOLTS_T)], flash=("rgba(130,240,255,.85)", .72))
R("tempest", "great", [
    P("fx-arc1, fx-arc2", "", raw=["cx-crackle 1.3s linear infinite"]),
    P("fx-cloudflash", "", (1.2, "linear", {15: "opacity:1", 22: "opacity:.1", 30: "opacity:.8", 40: "opacity:0"}), at=.2),
    P("fx-wind", "", raw=["cx-gust 1.1s ease-in-out infinite"]),
    P("fx-wind2", "", raw=["cx-gust 1.1s ease-in-out -.55s infinite"]),
])
R("tempest", "pass", [
    P("fx-arc1", "", (1.0, "linear", {20: "opacity:.2", 30: "opacity:1", 40: "opacity:.3", 50: "opacity:1"}), at=.2),
    P("fx-crown", "", (1.0, EASE_IO, {40: "transform:scale(1.06)"}), at=.25),
    nod(1.1, .1, .8),
])
R("tempest", "fail", [
    P("fx-arc1, fx-arc2", "opacity:.12", (1.2, EASE_OUT, {})),
    P("fx-wind, fx-wind2", "opacity:0", (1.0, EASE_OUT, {})),
    P("fx-crown", "opacity:.6", (1.2, EASE_OUT, {})),
    P("p-drizzle", "", None, (1.0, "linear", {12: "opacity:.9", 80: "opacity:0; transform:translateY(3px)"}), at=.8),
    P("p-dcloud", "opacity:.95", (1.2, EASE_OUT, {0: "opacity:0; transform:translateY(-2px)"}), at=.3),
    slump(-7, 1.4),
], props=[("dcloud", 1, puff([(26.6, 6.2, 1.7), (29, 5.6, 2), (31.2, 6.4, 1.6)], "#6F7887")),
          ("drizzle", 1, line(27, 8.6, 26.7, 9.8, "#A8E6FF", .35) + line(29.4, 9, 29.1, 10.2, "#A8E6FF", .35) + line(31.4, 8.5, 31.1, 9.7, "#A8E6FF", .35))])

# ---- FROST: breathes a cloud of frost ----------------------------------------------
BREATH = (pivot(23.2, 24.2, 1) + puff([(24.6, 24.6, 1.25), (27.4, 24.0, 1.65), (30.8, 23.2, 2.05)], "#DDF4FF", .85) +
          star4(29.4, 21.4, .7, "#FFFFFF") + star4(32.4, 25.4, .55, "#FFFFFF") + star4(26.4, 22.2, .5, "#FFFFFF"))
R("frost", "perfect", [
    P("p-breath", "", (2.0, EASE_OUT, {0: "opacity:0; transform:scale(.25)", 20: "opacity:1; transform:scale(.8)", 55: "opacity:.9; transform:translateX(1.5px) scale(1.15)",
                                       85: "opacity:0; transform:translateX(3px) scale(1.3)"}),
      (3.2, EASE_OUT, {15: "opacity:.9; transform:scale(.75)", 60: "opacity:0; transform:translateX(3px) scale(1.3)"}), at=.4),
    P("fx-frflake", "transform:rotate(60deg)", (2.0, EASE_OUT, {}), turn=(10, 1)),
    P("fx-frflakeglow", "", None, (1.4, EASE_IO, {50: "opacity:.5"}), at=.4),
    P("fx-frglint", "", (2.0, "linear", {20: "opacity:0", 30: "opacity:1", 45: "opacity:0"}), (2.6, "linear", {40: "opacity:0", 50: "opacity:1", 62: "opacity:0"})),
    P("head", "transform:rotate(-2deg)", (1.0, EASE_OUT, {30: "transform:translateY(-.4px) rotate(-3deg)"}), at=.2),
    P("fx-freye", "transform:scale(1.15)", (.8, SPRING, {}), at=.3),
], props=[("breath", 1, BREATH)], flash=("rgba(190,235,255,.75)", .45))
R("frost", "great", [
    P("fx-frflake", "transform:rotate(60deg)", (1.6, EASE_OUT, {}), raw=["cx-fr-spin 4s linear 1.6s infinite"]),
    P("fx-frglint", "", (1.4, "linear", {25: "opacity:0", 38: "opacity:1", 55: "opacity:0"}), at=.2),
    P("p-puff", "", (1.6, EASE_OUT, {0: "opacity:0; transform:scale(.3)", 25: "opacity:.9; transform:scale(.85)", 90: "opacity:0; transform:translateX(2px) scale(1.2)"}), at=.5),
], props=[("puff", 1, pivot(23.2, 24.2, 1) + puff([(24.8, 24.4, 1), (27.2, 23.9, 1.3)], "#DDF4FF", .8))])
R("frost", "pass", [
    P("fx-frglint", "", (1.2, "linear", {25: "opacity:0", 40: "opacity:1", 60: "opacity:0"}), at=.25),
    nod(1.1, .1, .8),
])
R("frost", "fail", [
    P("p-drips", "", None, (2.4, "cubic-bezier(.5,0,1,.6)", {10: "opacity:1", 60: "opacity:1; transform:translateY(4.6px)", 70: "opacity:0; transform:translateY(5.2px)"}), at=.6),
    P("fx-frflake", "opacity:.28", (1.6, EASE_OUT, {})),
    P("fx-frflakeglow", "opacity:.2", (1.6, EASE_OUT, {})),
    P("fx-crown", "opacity:.75; transform:translateY(.5px)", (1.4, EASE_OUT, {})),
    eyes_down(.5, .72),
    slump(-7, 1.4),
], props=[("drips", 1, drop(13.6, 14.6, .5, "#A9DBFF") + drop(26.4, 14.2, .45, "#A9DBFF"))])

# ---- ORACLE: the third eye opens, the crystals whirl ------------------------------
VISION = pivot(20, 15.6, 1) + circ(20, 15.6, 1.6, "none", 1, "#EBCBFF", .35) + circ(20, 15.6, 3.1, "none", .8, "#C79BFF", .3)
R("oracle", "perfect", [
    P("fx-mark", "transform:scale(1.5)", (1.8, EASE_OUT, {25: "transform:scale(2.3)", 40: "transform:scale(1.6)"}), (1.6, EASE_IO, {50: "transform:scale(1.8)"})),
    P("p-vision", "", (1.8, "linear", {20: "opacity:0; transform:scale(.4)", 30: "opacity:1; transform:scale(.8)", 70: "opacity:0; transform:scale(2.8)"}),
      (2.0, "ease-out", {8: "opacity:.9; transform:scale(.6)", 70: "opacity:0; transform:scale(2.8)"})),
    P("fx-crystals", "", (2.0, "cubic-bezier(.2,.6,.3,1)", {0: "transform:rotate(-240deg)"}), turn=(9, 1)),
    P("fx-gem", "", None, (1.2, EASE_IO, {50: "transform:scale(1.2)"}), at=.5),
] + joy(.4), flash=("rgba(200,150,255,.75)", .4))
R("oracle", "great", [
    P("fx-mark", "transform:scale(1.25)", (1.2, EASE_OUT, {35: "transform:scale(1.7)"}), (1.8, EASE_IO, {50: "transform:scale(1.45)"})),
    P("fx-crystals", "", (1.4, EASE_OUT, {0: "transform:rotate(-120deg)"}), raw=["cx-spin 12s linear 1.4s infinite"]),
] + joy(.3))
R("oracle", "pass", [
    P("fx-mark", "", (1.1, EASE_IO, {40: "transform:scale(1.6)"}), at=.25),
    nod(1.1, .1, .8),
])
R("oracle", "fail", [
    P("fx-mark", "transform:scaleY(.12)", (1.0, EASE_OUT, {}), at=.2),
    P("fx-crystals", "transform:translateY(2.2px) scale(.96); opacity:.5", (1.6, EASE_OUT, {})),
    P("fx-gem", "opacity:.5", (1.2, EASE_OUT, {})),
    eyes_down(.6, .7),
    slump(-7, 1.4),
])

# ---- INFERNO: flares up; a fail shrinks him to an ember ---------------------------
EMBERS = pivot(20, 16, 15) + "".join(circ(x, y, r, c) for x, y, r, c in [
    (8.6, 13, .6, "#FFB347"), (11.6, 8.4, .5, "#FFE07A"), (16.4, 7.2, .55, "#FF8A3D"), (23.8, 7.4, .5, "#FFE07A"),
    (28.6, 8.8, .6, "#FFB347"), (31.6, 13.4, .5, "#FF8A3D"), (14.4, 10.6, .38, "#FFFFFF"), (26.2, 10.8, .38, "#FFFFFF"),
    (7.4, 19, .45, "#FF8A3D"), (32.6, 19.4, .45, "#FFE07A")])
R("inferno", "perfect", [
    P("fx-flame", "transform:scale(1.06, 1.02)", (1.9, EASE_OUT, {
        18: "transform:scale(1.14, 1.04) skewX(-3deg)", 32: "transform:scale(1.08, 1.02) skewX(2deg)", 48: "transform:scale(1.15, 1.04) skewX(-2deg)"}),
      (.8, EASE_IO, {50: "transform:scale(1.1, 1.03) skewX(-1.5deg)"})),
    P("fx-flame2", "transform:scale(1.14, 1.12)", (1.9, EASE_OUT, {22: "transform:scale(1.28, 1.22)", 40: "transform:scale(1.16, 1.12)", 56: "transform:scale(1.3, 1.22)"}),
      (.6, EASE_IO, {50: "transform:scale(1.2, 1.18)"})),
    P("fx-flame3", "transform:scale(1.25, 1.15)", (1.9, EASE_OUT, {28: "transform:scale(1.45, 1.22)", 60: "transform:scale(1.4, 1.2)"}),
      (.5, EASE_IO, {50: "transform:scale(1.35, 1.2)"})),
    P("fx-shflame", "transform:scale(1.12)", (1.4, EASE_OUT, {30: "transform:scale(1.3)"}), (.7, EASE_IO, {50: "transform:scale(1.22)"})),
    P("fx-crowngem", "transform:scale(1.15)", (1.4, EASE_OUT, {25: "transform:scale(1.9)"}), (.9, EASE_IO, {50: "transform:scale(1.35)"})),
    P("fx-lava", "", None, (.7, EASE_IO, {50: "opacity:.55"}), at=.3),
    P("eyes", "transform:scale(1.12, 1.3)", (.9, SPRING, {}), at=.2),
    P("p-embers", "", (1.6, EASE_OUT, {12: "opacity:1; transform:translateY(3px) scale(.45)", 100: "opacity:0; transform:translateY(-1.6px) scale(1.08)"}),
      (1.4, "ease-out", {10: "opacity:1; transform:translateY(2px) scale(.55)", 90: "opacity:0; transform:translateY(-1.6px) scale(1.06)"}), at=.25),
], props=[("embers", 1, EMBERS)], flash=("rgba(255,110,40,.95)", .25))
R("inferno", "great", [
    P("fx-flame2", "transform:scale(1.08, 1.06)", (1.2, EASE_OUT, {40: "transform:scale(1.2, 1.15)"}), (.85, EASE_IO, {50: "transform:scale(1.14, 1.1)"})),
    P("fx-flame3", "transform:scale(1.15, 1.08)", (1.2, EASE_OUT, {35: "transform:scale(1.3, 1.16)"}), (.65, EASE_IO, {50: "transform:scale(1.22, 1.12)"})),
    P("fx-crowngem", "", (1.1, EASE_OUT, {35: "transform:scale(1.45)"})),
    P(".cx-ember-dot", "", raw=["cx-cinder 1.2s ease-out infinite"]),
])
R("inferno", "pass", [
    P("fx-flame3", "", (1.2, EASE_IO, {35: "transform:scale(1.25, 1.14)"}), at=.15),
    P("fx-crowngem", "", (1.0, EASE_IO, {40: "transform:scale(1.3)"}), at=.2),
    nod(1.1, .1, .8),
])
R("inferno", "fail", [
    P("fx-flame", "transform:scale(.5, .4); opacity:.55", (1.6, EASE_OUT, {20: "transform:scale(1.04, 1.02)", 60: "transform:scale(.56, .46)"}),
      (2.2, EASE_IO, {50: "transform:scale(.54, .45); opacity:.45"})),
    P("fx-flame2", "transform:scale(.4); opacity:.4", (1.6, EASE_OUT, {25: "transform:scale(1.05)"})),
    P("fx-flame3", "transform:scale(.3); opacity:.2", (1.4, EASE_OUT, {})),
    P("fx-shflame", "transform:scale(.6); opacity:.5", (1.5, EASE_OUT, {})),
    P("fx-lava", "opacity:.35", (1.5, EASE_OUT, {})),
    P("fx-crowngem", "opacity:.45", (1.2, EASE_OUT, {})),
    P("p-smoke", "", None, (2.8, "ease-out", {12: "opacity:.75; transform:translateY(1.5px) scale(.6)", 90: "opacity:0; transform:translateY(-2.2px) scale(1.15)"}), at=1.1),
    eyes_down(.5, .75, op=.6),
    slump(-8, 1.4),
], props=[("smoke", 1, puff([(19.4, 11.4, 1.2), (21, 9.6, 1.5), (19.8, 7.6, 1.1)], "#8D8F97", .85))])

# =============================================================== ULTIMATES ===

# ---- ASTRAL: the wings beat wide, the plasma core blazes ---------------------------
R("astral", "perfect", [
    P("fx-wing-l", "transform:rotate(-8deg)", (2.0, EASE_IO, {15: "transform:rotate(-22deg)", 30: "transform:rotate(8deg)", 45: "transform:rotate(-24deg)",
                                                            60: "transform:rotate(8deg)", 76: "transform:rotate(-16deg)"}), (1.6, EASE_IO, {50: "transform:rotate(-13deg)"})),
    P("fx-wing-r", "transform:rotate(8deg)", (2.0, EASE_IO, {15: "transform:rotate(22deg)", 30: "transform:rotate(-8deg)", 45: "transform:rotate(24deg)",
                                                           60: "transform:rotate(-8deg)", 76: "transform:rotate(16deg)"}), (1.6, EASE_IO, {50: "transform:rotate(13deg)"})),
    P("fx-zccore", "transform:scale(1.15)", (2.0, EASE_OUT, {30: "transform:scale(1.65)", 50: "transform:scale(1.2)", 64: "transform:scale(1.55)"}),
      (1.2, EASE_IO, {50: "transform:scale(1.35)"})),
    P("fx-zc2pulse", "", (2.0, "linear", {28: "opacity:0; transform:scale(.5)", 34: "opacity:1; transform:scale(1)", 60: "opacity:0; transform:scale(3)"}),
      (1.2, "ease-out", {6: "opacity:.9; transform:scale(1)", 70: "opacity:0; transform:scale(2.6)"})),
    P("fx-zc2ringa", "", raw=["cx-spin 2.5s linear infinite"]),
    P("fx-zc2ringb", "", raw=["cx-spin-back 3.5s linear infinite"]),
    P("fx-zceyeglow", "", None, (1.0, EASE_IO, {50: "opacity:.5"}), at=.6),
], flash=("rgba(110,255,240,.8)", .6))
R("astral", "great", [
    P("fx-wing-l", "", (1.4, EASE_IO, {30: "transform:rotate(-14deg)", 65: "transform:rotate(4deg)"})),
    P("fx-wing-r", "", (1.4, EASE_IO, {30: "transform:rotate(14deg)", 65: "transform:rotate(-4deg)"})),
    P("fx-zccore", "transform:scale(1.1)", (1.2, EASE_OUT, {35: "transform:scale(1.4)"}), (1.6, EASE_IO, {50: "transform:scale(1.25)"})),
])
R("astral", "pass", [
    P("fx-zc2pulse", "", (1.2, "ease-out", {10: "opacity:.9; transform:scale(1)", 75: "opacity:0; transform:scale(2.6)"}), at=.25),
    nod(1.1, .1, .8),
])
R("astral", "fail", [
    P("fx-wing-l", "transform:rotate(16deg) scale(.88); opacity:.55", (1.6, EASE_OUT, {})),
    P("fx-wing-r", "transform:rotate(-16deg) scale(.88); opacity:.55", (1.6, EASE_OUT, {})),
    P("fx-zccore", "transform:scale(.8); opacity:.35", (1.4, EASE_OUT, {})),
    P("fx-zc2ringa, fx-zc2ringb", "opacity:.3", (1.4, EASE_OUT, {})),
    P("fx-zceyeglow", "opacity:.2", (1.0, EASE_OUT, {}), at=.3),
    slump(-7, 1.4),
])

# ---- CELESTIAL: the halo blazes and a meteor shower falls ---------------------------
MET = lambda x, y: line(x, y, x + 5.2, y - 3.8, "#DDE4FF", .5, .7) + line(x, y, x + 2.4, y - 1.75, "#FFFFFF", .6) + circ(x, y, .55, "#FFFFFF")
METP = lambda name, at: P("p-" + name, "", (1.2, "linear", {0: "opacity:0", 12: "opacity:1; transform:translate(-1px,.7px)",
                                                             70: "opacity:1; transform:translate(-7px,5px)", 82: "opacity:0; transform:translate(-8.5px,6px)"}), at=at)
R("celestial", "perfect", [
    METP("met1", .2), METP("met2", .45), METP("met3", .7), METP("met4", .95),
    P("p-met1", "", None, (3.0, "linear", {58: "opacity:0", 64: "opacity:1; transform:translate(-1px,.7px)", 88: "opacity:1; transform:translate(-7px,5px)", 92: "opacity:0; transform:translate(-8.5px,6px)"}), at=1.4),
    P("fx-zb3halo", "transform:scale(1.03)", (2.0, EASE_OUT, {30: "transform:scale(1.08); opacity:1"}), (2.4, EASE_IO, {50: "transform:scale(1.06)"})),
    P("fx-zb2wingl", "transform:rotate(-8deg)", (1.8, EASE_OUT, {35: "transform:rotate(-17deg)"}), (2.2, EASE_IO, {50: "transform:rotate(-12deg)"})),
    P("fx-zb2wingr", "transform:rotate(8deg)", (1.8, EASE_OUT, {35: "transform:rotate(17deg)"}), (2.2, EASE_IO, {50: "transform:rotate(12deg)"})),
    P("fx-zbstar", "", raw=["cx-twinkle .7s ease-in-out infinite"]),
    P("fx-zb2line", "opacity:1", (1.2, EASE_OUT, {}), (1.4, EASE_IO, {50: "opacity:.5"}), at=.3),
    P("fx-zbeyeglow", "", None, (1.4, EASE_IO, {50: "opacity:.45"}), at=.6),
], props=[("met1", 1, MET(29, 8.6)), ("met2", 1, MET(30.5, 12.8)), ("met3", 1, MET(25, 8.2)), ("met4", 1, MET(30.6, 17.4))],
  flash=("rgba(160,180,255,.7)", .5))
R("celestial", "great", [
    METP("met1", .4),
    P("fx-zb3halo", "transform:scale(1.02)", (1.2, EASE_OUT, {35: "transform:scale(1.06)"}), (2.4, EASE_IO, {50: "transform:scale(1.05)"})),
    P("fx-zb2wingl", "", (1.4, EASE_IO, {35: "transform:rotate(-12deg)"})),
    P("fx-zb2wingr", "", (1.4, EASE_IO, {35: "transform:rotate(12deg)"})),
], props=[("met1", 1, MET(29, 8.6))])
R("celestial", "pass", [
    P("fx-zbstar", "", (1.1, EASE_IO, {40: "transform:scale(1.7) rotate(45deg)"}), at=.25),
    nod(1.1, .1, .8),
])
R("celestial", "fail", [
    P("fx-zb3halo", "transform:scale(.92); opacity:.25", (1.6, EASE_OUT, {})),
    P("fx-zbcapestars", "opacity:.2", (1.4, EASE_OUT, {})),
    P("fx-zb2wingl", "transform:rotate(12deg)", (1.4, EASE_OUT, {})),
    P("fx-zb2wingr", "transform:rotate(-12deg)", (1.4, EASE_OUT, {})),
    P("fx-zbeyeglow", "opacity:.2", (1.0, EASE_OUT, {}), at=.3),
    slump(-7, 1.4),
])

# ---- ZENITH: the rays burst, the orbit whips, the star blazes -----------------------
R("zenith", "perfect", [
    P("fx-zarays", "transform:scale(1.02) rotate(30deg)", (2.0, EASE_OUT, {28: "transform:scale(1.06) rotate(12deg)", 60: "transform:scale(1.04) rotate(24deg)"}),
      raw=["cx-za-rays 4s linear 2s infinite"]),
    P("fx-zastar", "transform:scale(1.1) rotate(45deg)", (2.0, EASE_OUT, {30: "transform:scale(1.35) rotate(45deg)", 55: "transform:scale(1.15) rotate(45deg)"}),
      (1.4, EASE_IO, {50: "transform:scale(1.25) rotate(45deg)"})),
    P("fx-zaorbit", "", (2.0, "cubic-bezier(.2,.6,.3,1)", {0: "transform:rotate(-720deg)"}), raw=["cx-spin 2s linear 2s infinite"]),
    P("fx-zaorbit2", "", raw=["cx-spin-back 3s linear infinite"]),
    P("fx-zaring", "", (2.0, EASE_OUT, {30: "transform:scale(1.06)"}), (1.6, EASE_IO, {50: "opacity:.7"})),
    P("fx-zaeyeglow", "", None, (1.0, EASE_IO, {50: "opacity:.5"}), at=.6),
    P("p-burst", "", (2.0, "linear", {26: "opacity:0; transform:scale(.3)", 31: "opacity:1; transform:scale(1)", 50: "opacity:0; transform:scale(1.25) rotate(45deg)"})),
], props=[("burst", 1, pivot(20, 7.6, 3.4) + star4(20, 7.6, 3.4, "#E9E4FF") + star4(20, 7.6, 2.4, "#FFFFFF", w=.4) +
           '<g transform="rotate(45 20 7.6)">' + star4(20, 7.6, 2.2, "#C9BDFF", .8) + '</g>')],
  flash=("rgba(220,210,255,.85)", .55))
R("zenith", "great", [
    P("fx-zaorbit", "", (1.4, EASE_OUT, {0: "transform:rotate(-360deg)"}), raw=["cx-spin 3s linear 1.4s infinite"]),
    P("fx-zastar", "", (1.2, EASE_OUT, {35: "transform:scale(1.3) rotate(45deg)"}), (1.8, EASE_IO, {50: "transform:scale(1.15)"})),
    P("fx-zarays", "transform:scale(1.02)", (1.2, EASE_OUT, {35: "transform:scale(1.05)"})),
])
R("zenith", "pass", [
    P("fx-zastar", "", (1.1, EASE_IO, {40: "transform:scale(1.25) rotate(45deg)"}), at=.25),
    nod(1.1, .1, .8),
])
R("zenith", "fail", [
    P("fx-zarays", "transform:scale(.75); opacity:.35", (1.6, EASE_OUT, {})),
    P("fx-zastar", "transform:scale(.6); opacity:.25", (1.4, EASE_OUT, {})),
    P("fx-zaring", "opacity:.4", (1.4, EASE_OUT, {})),
    P("fx-zaorbit, fx-zaorbit2", "opacity:.3", (1.4, EASE_OUT, {})),
    P("fx-zaeyeglow", "opacity:.2", (1.0, EASE_OUT, {}), at=.3),
    slump(-7, 1.4),
])

# ================================================== BUILD 321: THE MOOD OF THE GRADE ===
# "Ensure the characters expression change on the mood of the grade, the
# alien still looks mad even after the hundred.. ensure all characters are
# happy when they get the 100 ... Ensure this is every character not just
# the starters." Measured (check-behaviour 321b: brow and eye slant, mouth
# curve), sixteen of the thirty were not happy at a 100: slanted eyes of
# light that read as a scowl (the Masked One, Ronin, Umbra, Inferno,
# Astral, Zenith, Celestial, Orion's visor), the Alien's brow and frown,
# a squint or a stare where a smile should be. Their 100 and their 90+
# now end on a happy face - the character's own closed eyes turned up
# (joy) where they show on its face, or two arches of the eyes' own light
# (glee) where its eyes are light in a dark face - and the moves before it
# are untouched. A pass keeps the face it rests in; a fail is let down,
# never cross (the Alien's scowl comes off for every grade).
def happy(cid, glee_svg=None, hide=("eyes",), drop=(), extra=(), bands=("perfect", "great"), at=.3, use_joy=False):
    for band in bands:
        spec = RX[cid][band]
        gone = set(hide) | set(drop) | ({"eyes", "eyes-closed"} if use_joy else set())
        spec["parts"] = [p for p in spec["parts"] if p.sel[0] not in gone]
        a = at if band == "perfect" else max(.2, at - .1)
        if use_joy:
            spec["parts"] += joy(a)
        if glee_svg:
            spec["parts"] += cheer(a, hide=tuple(h for h in hide if not (use_joy and h == "eyes")))
            spec["props"] = [x for x in spec["props"] if x[0] != "glee"] + [("glee", 2, glee_svg)]
        else:
            spec["parts"] += [P(h, "opacity:0", (.3, "ease-out", {}), at=a) for h in hide if h != "eyes" or not use_joy]
        spec["parts"] += [P(*x[:3], at=a) if len(x) == 3 else P(x[0], x[1], (.4, SPRING, {}), at=a) for x in extra]


# the Alien: the scowl lifts off, the eyes turn up, the frown turns over
happy("alien", glee([(14.4, 20.4, 3.2), (25.6, 20.4, 3.2)], "#8CFFB8", core="#0E1116", sw=.95, halo=2.4),
      hide=("eyes", "fx-eyeglow"), extra=[("brow", "opacity:0; transform:translateY(-1.6px)"), ("mouth", "transform:scale(1.4, -2.2)")])
# ...and no grade wears it: a pass is level, a fail let down
for band in ("pass", "fail"):
    RX["alien"][band]["parts"] += [P("brow", "opacity:0; transform:translateY(-1px)", (.6, EASE_OUT, {}), at=.15)]
RX["alien"]["pass"]["parts"] += [P("mouth", "transform:scaleY(.2)", (.6, EASE_OUT, {}), at=.2)]
happy("detective", glee([(16.7, 20.1, 1.15), (23.3, 20.1, 1.15)], "#F2B84B", core="#FFE7B0", sw=.4),
      extra=[("mouth", "transform:scale(1.3, 2.4)")])
happy("masked", glee([(16.6, 20.1, 2.1), (23.4, 20.1, 2.1)], "#FF3B4E", core="#FFE1E4", sw=.5),
      hide=("eyes", "fx-slotglow"), extra=[("mouth", "transform:scale(1.15, 2.8)")])
happy("zeus", grin(20, 20.6, 1.5, "#8C8478", sw=.4), hide=("fx-zs3eyes",), use_joy=True)
happy("poseidon", glee([(16.8, 19, 1.4), (23.2, 19, 1.4)], "#FFB347", core="#FFE6B0", sw=.42))
happy("marksman", None, use_joy=True, extra=[("mouth", "transform:scale(1.35, 3.2)")])
happy("astronaut", glee([(17.2, 17.7, 2.0), (22.8, 17.7, 2.0)], "#5CE1FF", core="#E6FBFF", sw=.45), hide=("eyes", "fx-saeye"))
happy("hacker", None, use_joy=True, extra=[("mouth", "transform:scale(1.2, 1.6)")])
happy("ronin", glee([(16.9, 18.5, 1.6), (23.1, 18.5, 1.6)], "#FF3D8E", core="#FFE6F2", sw=.42), drop=("fx-ronineye",))
happy("umbra", glee([(16.8, 20.3, 2.0), (23.2, 20.3, 2.0)], "#8B5CF6", core="#F1EAFF", sw=.45))
happy("singularity", glee([(17.5, 19.4, 1.7), (22.5, 19.4, 1.7)], "#7FB8E8", core="#EAF8FF", sw=.42))
happy("genesis", glee([(16.6, 19.8, 1.9), (23.4, 19.8, 1.9)], "#FF5CA8", core="#FFF6E6", sw=.48) + grin(20, 22.9, 1.5, "#FFE0C0", sw=.4))
happy("tempest", None, use_joy=True, extra=[("brow", "transform:translateY(-.7px) scaleY(.1)"), ("mouth", "transform:scale(1.3, 2.6)")])
happy("frost", None, use_joy=True, drop=("fx-freye",), extra=[("brow", "transform:translateY(-.7px) scaleY(.1)"), ("mouth", "transform:scale(1.3, 2.6)")])
happy("inferno", glee([(16.6, 18.9, 1.6), (23.4, 18.9, 1.6)], "#FF4A2A", core="#FFF2EE", sw=.45))
happy("astral", glee([(17.2, 18.9, 1.6), (22.8, 18.9, 1.6)], "#3EF0FF", core="#EFFFFF", sw=.42), hide=("eyes", "fx-zceyeglow"))
happy("celestial", grin(20, 23.5, 1.25, "#8E9AB4", sw=.3), use_joy=True)
happy("zenith", glee([(17.5, 18.9, 1.5), (22.5, 18.9, 1.5)], "#8FCBFF", core="#FFFFFF", sw=.42), hide=("eyes", "fx-zaeyeglow"))
