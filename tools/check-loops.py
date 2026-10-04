#!/usr/bin/env python3
"""Every infinite, non-alternating CSS animation must end where it starts.

"I can tell when the animation cycle stops and restarts - it should be
seamless, this goes for any animation across the app." A loop whose last
keyframe differs from its first jumps once a cycle. Some differ on
purpose - a full rotation, a tile moved by whole periods, a pulse that
fades to nothing at both ends, a sweep that starts and ends off its
element - and those are listed in KNOWN with the reason. Anything new
that differs fails until it is either fixed or added there with a reason.

  python3 tools/check-loops.py [path/to/index.html]
"""
import re, sys
SRC = sys.argv[1] if len(sys.argv) > 1 else __file__.rsplit("/tools/", 1)[0] + "/index.html"
KNOWN = {
    "avatar-scan": "a visor sweep that rests, then restarts under the mask",
    "bnr-grid": "shifted by exactly one 16px grid cell",
    "bnr-holo": "shifted by whole periods of a 300% background",
    "bnr-sheen": "a sweep from off one edge to off the other",
    "cosmic-orbit-spin": "a full turn",
    "bn-beam": "a spotlight on a pendulum - played alternate, so it swings back instead of jumping",
    "bn-sweep": "a band of light from off one edge to off the other, invisible at both ends",
    "cx-embers": "an ember that rises and fades to nothing at both ends",
    "cx-infall": "shifted by exactly two periods of a .2 1.3 dash (1.5 each)",
    "cosmic-pulse-out": "fades to nothing at both ends",
    "daily-ready": "fades to nothing at both ends",
    "mystery-halo": "fades to nothing at the end, restarts from small",
    "pushsweep": "a sweep from off one edge to off the other",
    "rankmap-here": "a ping that fades to nothing",
    "rankmap-tip-ping": "a ping off the road's progress light that fades to nothing",
    "stat-shine": "shifted by exactly one period of a 200% background",
    "swatch-sheen": "a sweep from off one edge to off the other",
    "vrc-drift": "stars drifting, respawned off-screen",
    "vroom-prep-bar": "a highlight from off one edge to off the other",
    "xp-sheen": "shifted by whole periods of a 200% background",
    # Build 225 banner scenes.
    "bn-fall": "a petal fades in at the top and out at the bottom",
    "bn-lantern": "a lantern fades in low and out high",
    "bn-meteor": "a streak that is invisible for most of its cycle",
    "bn-orbit": "a full turn",
    "bn-rain": "0.7s streaks over a random field; the reset lands on more rain",
    "bn-ripple": "a ring that fades to nothing as it spreads",
    "bn-rise": "an ember fades in low and out high",
    # Build 244 characters.
    "cx-cinder": "Inferno's cinder: invisible at both ends of the rise",
    "cx-code": "Hacker's visor code: shifted by exactly six rows (6 x .72)",
    # Build 266 characters.
    "cx-hk3-rain": "Hacker's code rain: shifted by exactly one glyph pattern (4 x 1.5)",
    "cx-hk3-code": "Hacker's lens code: shifted by exactly eight rows (8 x .72) of a pattern drawn twice",
    "cx-kr-bubble": "the Koi's bubble (the Kraken's first): invisible at both ends of the rise",
    # Build 271: the scene behind every character.
    "cx-bg-fall": "shifted by exactly one 12-unit period of the falling layout",
    "cx-bg-rise": "shifted by exactly one 12-unit period of the rising layout",
    "cx-bg-ripple": "a ring that fades to nothing as it spreads",
    "cx-sand": "Timekeeper's sand: shifted by exactly one grain pitch (.5)",
    # Build 304.
    "cx-sg3-orbit": "Horizon's disk: shifted by exactly one lap (18.78 = the ellipse's circumference = its dash + gap)",
    # Build 235: the sleeping character's Zzz.
    "char-zzz": "a letter fades in beside the head and out as it drifts up",
    # Build 235: the characters' own motion (all invisible at both ends, or a whole turn).
    "cx-burst": "sparkles that fade to nothing at both ends",
    "cx-fire": "a breath of fire, invisible at both ends",
    "cx-lockon": "the Marksman's reticle turns a quarter - it has four-fold symmetry",
    "cx-sheen": "a sweep of light, invisible at both ends",
    "cx-sheen-idle": "a sweep of light, invisible at both ends",
    "cx-slash": "a blade glint, invisible at both ends",
    "cx-smoke": "a wisp of smoke, invisible at both ends",
    "cx-spin": "a full turn",
    "cx-spin-back": "a full turn the other way",
    # Build 232: Sky Temple's waterfalls.
    "bn-pour": "streaks 14px apart sliding exactly 14px",
    # Build 244: the new and redrawn banners.
    "bn-depth": "Hall of Fame's depth - 0% and 100% are the same scale; the 0% frame also carries its easing",
    "bn-steam": "Midnight Oil's steam, a wisp that fades to nothing at both ends",
}
s = open(SRC, encoding="utf-8").read()
kf = {}
for m in re.finditer(r"@keyframes\s+([\w-]+)\s*\{", s):
    i = j = m.end(); depth = 1
    while depth:
        depth += {"{": 1, "}": -1}.get(s[j], 0); j += 1
    kf.setdefault(m.group(1), s[i:j - 1])
loops = set()
for m in re.finditer(r"animation(?:-name)?\s*:\s*([^;}{]+)", s):
    for part in m.group(1).split(","):
        if "infinite" in part and "alternate" not in part:
            loops.update(t for t in part.split() if t in kf)
def ends(body):
    out = {}
    for m in re.finditer(r"([\w%.,\s]+)\{([^}]*)\}", body):
        for k in m.group(1).split(","):
            k = {"from": "0%", "to": "100%"}.get(k.strip(), k.strip())
            out[k] = out.get(k, "") + re.sub(r"\s+", "", m.group(2))
    return out
bad = []
for n in sorted(loops):
    e = ends(kf[n])
    if "0%" in e and "100%" in e and e["0%"] != e["100%"] and n not in KNOWN:
        bad.append((n, e["0%"][:80], e["100%"][:80]))
for n, a, b in bad:
    print("  FAIL %s jumps each cycle: %s  ->  %s" % (n, a, b))
print("%d looping animations, %d with a seam" % (len(loops), len(bad)))
sys.exit(1 if bad else 0)
