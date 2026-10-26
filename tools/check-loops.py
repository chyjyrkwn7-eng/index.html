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
    "ru-tab-ring": "a ripple, invisible at both ends of its cycle - it grows and fades, then the next one fades in",
    # Build 325: Nova's signal beacon (an existing account's meeting) - fades in at 14%, so it is invisible at both ends.
    "nt-sig-ring": "the signal's ripple, invisible at both ends - it fades in, grows and fades out",
    "avatar-scan": "a visor sweep that rests, then restarts under the mask",
    "bnr-grid": "shifted by exactly one 16px grid cell",
    "bnr-holo": "shifted by whole periods of a 300% background",
    "bnr-sheen": "a sweep from off one edge to off the other",
    # 327z15: the unfound flare bubble's shine and the rank lore dots' shine - each starts wholly off the
    # left edge of a clipped box (left -80% / -90%, skewed) and ends wholly off the right (420% of its width)
    "cof-sweep": "a sweep from off one edge to off the other",
    "ranklore-sweep": "a sweep from off one edge to off the other",
    "cosmic-orbit-spin": "a full turn",
    # Build 326: the Supernova crack's motes (scarMotes) - three nested loops on one clock; the mote itself
    # (csc-mote-look / csc-mote-chip) is at opacity 0 at both ends, so where the outer two jump it cannot be seen.
    "csc-mote-turn": "the angle of a mote that is invisible (opacity 0) at both ends of its loop (csc-mote-look)",
    "csc-mote-out": "the radius of a mote that is invisible (opacity 0) at both ends of its loop (csc-mote-look)",
    "csc-mote-look": "a mote of light: opacity 0 at both ends - it leaves the crack and fades out on the ring",
    "csc-mote-chip": "a chip off the crack: opacity 0 at both ends - it leaves the crack and fades out on the ring",
    "nv-mote": "stardust on Nova's coat: rises and fades to nothing at both ends (build 320)",
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
    "lb-podium-sheen": "first place's band of light, from off one edge (-130%, clear of the skew) to off the other (300%) inside an overflow:hidden row (build 324)",
    "vrc-drift": "stars drifting, respawned off-screen",
    "vroom-prep-bar": "a highlight from off one edge to off the other",
    "xp-sheen": "shifted by whole periods of a 200% background",
    # Build 304 layered banners (bnLayerHTML).
    "bl-blink": "a beacon blinking - steps(1), on then off, a flash by design",
    "bl-cross": "a plane from off the right edge to off the left (-1150% of its 48px box)",
    "bl-in": "a ring that closes in from large to small and fades to nothing at both ends",
    "bl-slide": "fog drawn as copies one 480 period apart in a 960 box, moved by exactly one period (-50%)",
    "bl-fall": "petals moved by exactly one tile (40 across, 180 down) of a tile stacked over itself",
    "bl-meteor": "a streak that is invisible at both ends",
    "bl-pour": "streaks moved by exactly one 14px period (20% of a 70px box)",
    "bl-rise": "motes moved up by exactly one 180px tile; every mote's copy sits straight below it",
    "bl-spin": "a full turn",
    "bl-steam": "fades to nothing at both ends",
    "bl-trailmet": "a meteor that is invisible at both ends",
    "cosmic-smoke-a": "a full turn - the translate and scale are the same at both ends",
    "cosmic-smoke-b": "a full turn the other way - translate and scale the same at both ends",
    "cosmic-smoke-c": "the mirrored smoke layer: a full turn - translate and scale the same at both ends",
    "cosmic-smoke-d": "the large smoke layer: a full turn - translate and scale the same at both ends",
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
    # Build 313: the secret flares.
    "cof-call": "the hunted flare's ring: fades to nothing at the end, restarts from small",
    # Build 329.
    "cb-new": "the class bubble's new-class ring: fades to nothing as it spreads, restarts from the bubble",
    "ia-shine": "the IFC analysis bar's shine: a 220% band swept from 120% to -120%, off the bar at both ends",
    "gs-drift": "Get Started's stars: each layer shifted by exactly one of its own tiles (--gs-tile)",
    "cx-gn-spin": "Genesis's moon round its ring - a full turn",
    "cx-gn-back": "Genesis's moon kept upright - a full turn the other way",
    "cx-gn-drift": "Genesis's weather bands: shifted by exactly one 8-unit period of bands drawn twice",
    "cx-gn-erupt": "Genesis's eruption: invisible at both ends",
    "xs-turn": "the secret flare scenes' orbits, corona and disc - a full turn",
    "xs-turnback": "a rider on a scene's orbit kept upright - a full turn the other way",
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
    # Build 308: Horizon's rising light and Zenith's corona.
    "cx-sg-rise": "light rising up Horizon's hair - invisible at both ends",
    "cx-za-dust": "Zenith's stardust - each mote fades to nothing at both ends",
    "cx-za-rays": "Zenith's corona turns 30deg - it has twelve rays, so 30deg is a whole step",
    "cx-za-wave": "Zenith's shockwave - fades to nothing as it spreads (retired in 312; kept so an old build's file still reads)",
    # Build 312 character pass.
    "cx-fr-spin": "Frost's six-armed sigil: a sixth of a turn lands on the same picture",
    "cx-sg-spark": "a spark off Horizon's hair that is invisible at both ends of its rise",
    "cx-wf-ring": "a ring off a worn flare that fades to nothing as it spreads",
    "cx-za-pour": "light poured down Zenith's halo: invisible at both ends of its run",
    "cx-za-rays8": "Zenith's eight rays, long and short: a quarter turn lands on the same picture",
    # Build 313 characters.
    "cx-sa5-drift": "Orion's cloak stars: laid on a 12-unit tile drawn four times, moved exactly one tile",
    "cx-zb2-trails": "Celestial's star trails are laid out six-fold, so a sixth of a turn lands on the same picture",
    "cx-zc2-flow": "Astral's plasma in its veins: a .6 1.8 dash moved by exactly one period (2.4)",
    "cx-za2-dots": "the dots along Zenith's orbit: a .2 .9 dash moved by exactly one period (1.1)",
    "char-emote-spin": "a 100's gold rays: a 30deg repeating conic, so 30deg lands on the same picture",
    # Build 314: the ultimates a smidge calmer, Celestial redrawn.
    "cx-zb4-dust": "Zenith's stardust, softer - each mote fades to nothing at both ends",
    # Build 317: loops with a cubic-bezier() curve were never read (its own
    # commas split the shorthand); found once top_level() split it right.
    # Each was checked by hand: invisible at both ends of its cycle.
    "bl-out": "a ring that grows and fades to nothing at both ends",
    "bn-fly": "a mote flung out, invisible at both ends",
    "bn-shock": "a shockwave that fades to nothing at both ends",
    "rk-nova-frag": "a Supernova emblem fragment flung out, invisible at both ends",
    "rk-nova-shock": "the Supernova emblem's shockwave, invisible at both ends",
    "xp-glide": "a band of light from off one end of the lit bar to off the other, resting between",
    "csc-drift": "a Supernova scar fragment drifting off the burn - fades to nothing at both ends",
    "crf-tumble": "a shard of debris on Home's rings tumbling - a full turn",
    # (rk-nova-frag-soft and rk-nova-shock-soft need no entry: since
    # b317-cut2 their last frame is their first)
}
s = open(SRC, encoding="utf-8").read()
kf = {}
for m in re.finditer(r"@keyframes\s+([\w-]+)\s*\{", s):
    i = j = m.end(); depth = 1
    while depth:
        depth += {"{": 1, "}": -1}.get(s[j], 0); j += 1
    kf.setdefault(m.group(1), s[i:j - 1])
loops = set()
def top_level(v):
    """Split a shorthand on its top-level commas only: a cubic-bezier()'s
    own commas used to cut a layer in two, and a loop with an eased curve
    went unread."""
    out, depth, cur = [], 0, ""
    for ch in v:
        depth += {"(": 1, ")": -1}.get(ch, 0)
        if ch == "," and depth == 0:
            out.append(cur); cur = ""
        else:
            cur += ch
    return out + [cur]
for m in re.finditer(r"animation(?:-name)?\s*:\s*([^;}{]+)", s):
    for part in top_level(m.group(1)):
        if "infinite" in part and "alternate" not in part:
            loops.update(t for t in part.split() if t in kf)
def ends(body):
    out = {}
    for m in re.finditer(r"([\w%.,\s]+)\{([^}]*)\}", body):
        for k in m.group(1).split(","):
            k = {"from": "0%", "to": "100%"}.get(k.strip(), k.strip())
            out[k] = out.get(k, "") + re.sub(r"\s+", "", m.group(2))
    return out
def whole_turn(a, b):
    """Build 314's reactions (tools/gen-reactions.py) name a loop that
    turns once `rx-...-turn`. Accepted only when it IS one whole turn: the
    two ends identical but for their last rotate(), which differs by
    exactly 360deg either way."""
    ma = re.search(r"rotate\((-?[\d.]+)deg\);?$", a)
    mb = re.search(r"rotate\((-?[\d.]+)deg\);?$", b)
    return bool(ma and mb and a[:ma.start()] == b[:mb.start()]
                and abs(abs(float(mb.group(1)) - float(ma.group(1))) - 360) < 1e-6)
bad = []
for n in sorted(loops):
    e = ends(kf[n])
    if re.match(r"rx-.+-turn$", n) and "0%" in e and "100%" in e and whole_turn(e["0%"], e["100%"]):
        continue
    if "0%" in e and "100%" in e and e["0%"] != e["100%"] and n not in KNOWN:
        bad.append((n, e["0%"][:80], e["100%"][:80]))
for n, a, b in bad:
    print("  FAIL %s jumps each cycle: %s  ->  %s" % (n, a, b))
print("%d looping animations, %d with a seam" % (len(loops), len(bad)))
sys.exit(1 if bad else 0)
