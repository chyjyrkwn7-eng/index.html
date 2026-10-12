#!/usr/bin/env python3
"""Every character's own reaction to a grade (build 314).

"I was hoping for more of a character animation, something the character
does so it's cooler, all the characters can have somewhat different ones,
and the reaction is based on the grade." Until build 314 every character
did the same hop, nod or slump and wore a sign round its circle. Now each
one ACTS, in its own way, four ways over:

  perfect  (100)    its biggest, proudest move, ~2s, then a happy loop
  great    (90-99)  a pleased version of the same personality
  pass     (70-89)  a small satisfied gesture
  fail     (<70)    its own disappointed reaction

The moves are written down in one place, the table in
tools/reactions-table.py (read by this file - P, R and the drawing helpers
below are in scope there). This turns it into two marked blocks in
index.html:

  /* RX:CSS:BEGIN */ ... /* RX:CSS:END */   the keyframes and the rules
  /* RX:JS:BEGIN */  ... /* RX:JS:END */    RX_PROPS (the extra pieces a
                                            move needs - Zeus's bolt, the
                                            Hacker's ACCESS) and RX_FLASH

  python3 tools/gen-reactions.py           rewrite both blocks
  python3 tools/gen-reactions.py --check   fail if index.html has drifted

HOW A MOVE IS WRITTEN. A part names a piece of the drawing (`head`,
`fx-gem`, ...) or a prop (`p-bolt`), its final POSE, and the keyframes that
get it there. The generator fills in the ends, so nothing can jump:
  - an intro starts at the part's resting state and ends ON its pose;
  - a loop starts and ends on the pose (a `turn` loop is the pose plus one
    whole turn, which check-loops accepts for names ending in -turn);
  - the pose is ALSO written as a plain rule, outside the motion query, so
    with motion off every grade still lands on its final picture.
Only transform and opacity move. No SVG filter anywhere.
"""
import io, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "index.html")
BANDS = ("perfect", "great", "pass", "fail")

# Parts a still drawing keeps hidden (opacity 0) until a state shows them -
# their resting opacity is 0, not 1.
HIDDEN = {
    "fx-slash", "fx-spell", "fx-eyeglow", "fx-mk3flash", "fx-mk3fork", "fx-mk3bolt", "fx-slotglow",
    "fx-zs3eyes", "fx-strike", "fx-sh3glint", "fx-sh4weed", "fx-cl3balls", "fx-mk3lock", "fx-mk3glint",
    "fx-sa5meteor", "fx-sa5surge", "fx-sa5ring", "fx-sa5visor", "fx-hk2slice", "fx-ronin2slash",
    "fx-ronin2slash2", "fx-ronin2glint", "fx-ronin2brim", "fx-ronin2petals", "fx-umrim", "fx-umcglow",
    "fx-umcglint", "fx-wforbit", "fx-sgwave", "fx-sgsurgeb", "fx-sgsurgew", "fx-sgsparks", "fx-sgrise",
    "fx-gnerupt", "fx-cloudflash", "fx-frglint", "fx-frtip", "fx-frcheek", "fx-zc2arcs", "fx-zc2shard",
    "fx-zc2pulse", "fx-zb2met", "fx-zb2line", "fx-zadust", "fx-za2far", "fx-zapour", "fx-za2near",
    "fx-zasats", "fx-sparkles",
}
# Parts that stand at a transform of their own when still.
BASE_TRANSFORM = {"fx-gnspin": "rotate(38deg)"}


def cls(name):
    if name.startswith("."):
        return name
    if name.startswith("p-"):
        return ".cx-rx-" + name[2:]
    return ".cx-" + name


def decls(s):
    out = {}
    for d in (s or "").split(";"):
        d = d.strip()
        if not d:
            continue
        k, v = d.split(":", 1)
        out[k.strip()] = v.strip()
    return out


def fmt(d):
    return ";".join("%s:%s" % (k, v) for k, v in d.items())


class P:
    """One part of one reaction."""
    def __init__(self, sel, pose="", intro=None, loop=None, raw=None, at=0.0, turn=None):
        self.sel = [s.strip() for s in sel.split(",")]
        self.pose = decls(pose)
        self.intro = intro          # (dur, ease, {pct: decls})
        self.loop = loop            # (dur, ease, {pct: decls})
        self.turn = turn            # (dur, +1/-1) - the pose plus a whole turn, linear
        self.raw = raw or []        # whole animation strings, used as they are
        self.at = at

    def rest(self, prop):
        s = self.sel[0]
        if prop == "opacity":
            return "0" if (s.startswith("p-") or s in HIDDEN) else "1"
        if prop == "transform":
            return BASE_TRANSFORM.get(s, "none")
        return "initial"


# ---------------------------------------------------------------------------
# Drawing helpers for the props. Coordinates are the drawing's own (viewBox
# 3 3 34 34). Every prop is a <g class="cx-rx cx-rx-NAME" opacity="0">, so a
# prop nobody animates draws nothing.
def f2(v):
    return ("%.2f" % v).rstrip("0").rstrip(".")


def star4(cx, cy, r, fill, op=1, w=.32):
    a = r * w
    return ('<path d="M%s %s Q%s %s %s %s Q%s %s %s %s Q%s %s %s %s Q%s %s %s %sZ" fill="%s"%s/>' % (
        f2(cx), f2(cy - r), f2(cx + a), f2(cy - a), f2(cx + r), f2(cy), f2(cx + a), f2(cy + a), f2(cx), f2(cy + r),
        f2(cx - a), f2(cy + a), f2(cx - r), f2(cy), f2(cx - a), f2(cy - a), f2(cx), f2(cy - r), fill,
        "" if op == 1 else ' opacity="%s"' % f2(op)))


def circ(cx, cy, r, fill, op=1, stroke=None, sw=None):
    s = '<circle cx="%s" cy="%s" r="%s" fill="%s"' % (f2(cx), f2(cy), f2(r), fill)
    if stroke:
        s += ' stroke="%s" stroke-width="%s"' % (stroke, f2(sw or .3))
    if op != 1:
        s += ' opacity="%s"' % f2(op)
    return s + "/>"


def ell(cx, cy, rx, ry, fill, op=1, stroke=None, sw=None, rot=None):
    s = '<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s"' % (f2(cx), f2(cy), f2(rx), f2(ry), fill)
    if stroke:
        s += ' stroke="%s" stroke-width="%s"' % (stroke, f2(sw or .3))
    if op != 1:
        s += ' opacity="%s"' % f2(op)
    if rot is not None:
        s += ' transform="rotate(%s %s %s)"' % (f2(rot), f2(cx), f2(cy))
    return s + "/>"


def path(d, fill="none", stroke=None, sw=None, op=1, cap=True):
    s = '<path d="%s" fill="%s"' % (d, fill)
    if stroke:
        s += ' stroke="%s" stroke-width="%s"' % (stroke, f2(sw or .35))
        if cap:
            s += ' stroke-linecap="round" stroke-linejoin="round"'
    if op != 1:
        s += ' opacity="%s"' % f2(op)
    return s + "/>"


def line(x1, y1, x2, y2, stroke, sw=.35, op=1):
    return path("M%s %sL%s %s" % (f2(x1), f2(y1), f2(x2), f2(y2)), stroke=stroke, sw=sw, op=op)


def pivot(cx, cy, r):
    """An invisible disc that centres a group's box on (cx, cy), so the
    group scales and turns about that point."""
    return '<circle class="rxpv" cx="%s" cy="%s" r="%s" fill="none"/>' % (f2(cx), f2(cy), f2(r))


def drop(cx, cy, r, fill, op=1):
    """A teardrop with its point up; (cx, cy) is the round end's centre."""
    return path("M%s %s C%s %s %s %s %s %s A%s %s 0 1 1 %s %s C%s %s %s %s %s %sZ" % (
        f2(cx), f2(cy - r * 2.3), f2(cx + r * .3), f2(cy - r * 1.5), f2(cx + r), f2(cy - r * .7), f2(cx + r), f2(cy),
        f2(r), f2(r), f2(cx - r), f2(cy), f2(cx - r), f2(cy - r * .7), f2(cx - r * .3), f2(cy - r * 1.5), f2(cx), f2(cy - r * 2.3)),
        fill=fill, op=op)


def heart(cx, cy, s, fill, op=1):
    return path("M%s %s C%s %s %s %s %s %s C%s %s %s %s %s %sZ" % (
        f2(cx), f2(cy + s * .9), f2(cx - s * 1.4), f2(cy - s * .1), f2(cx - s * .7), f2(cy - s * 1.1), f2(cx), f2(cy - s * .45),
        f2(cx + s * .7), f2(cy - s * 1.1), f2(cx + s * 1.4), f2(cy - s * .1), f2(cx), f2(cy + s * .9)), fill=fill, op=op)


def puff(parts, fill, op=1):
    """Overlapping discs as ONE shape: each disc is opaque and the opacity
    goes on the group, so an overlap is never a darker lens (build 318 -
    each disc carrying its own opacity is what made the Ninja's smoke a
    heap of grey bubbles)."""
    body = "".join(circ(x, y, r, fill) for x, y, r in parts)
    return body if op == 1 else '<g opacity="%s">%s</g>' % (f2(op), body)


def bolt(x, y, k, fill, stroke, sw=.3, flip=False):
    """A lightning bolt, top at (x, y), k high-ish units per step."""
    pts = [(0, 0), (2.6, 0), (1.2, 3.6), (3.3, 3.6), (-.6, 10.2), (.6, 5.2), (-1.4, 5.2)]
    if flip:
        pts = [(-px, py) for px, py in pts]
    d = "M" + " L".join("%s %s" % (f2(x + px * k), f2(y + py * k)) for px, py in pts) + "Z"
    return path(d, fill=fill, stroke=stroke, sw=sw)


def text(x, y, s, size, fill, weight=800, spacing=.12, op=1):
    return ('<text x="%s" y="%s" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" '
            'font-size="%s" font-weight="%s" letter-spacing="%s" fill="%s"%s>%s</text>' % (
                f2(x), f2(y), f2(size), weight, f2(spacing), fill, "" if op == 1 else ' opacity="%s"' % f2(op), s))


def rect(x, y, w, h, rx, fill, stroke=None, sw=None, op=1):
    s = '<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s"' % (f2(x), f2(y), f2(w), f2(h), f2(rx), fill)
    if stroke:
        s += ' stroke="%s" stroke-width="%s"' % (stroke, f2(sw or .3))
    if op != 1:
        s += ' opacity="%s"' % f2(op)
    return s + "/>"


# ---------------------------------------------------------------------------
# Building blocks every character draws on - each still named per character
# and band, so no two reactions share a keyframe name.
EASE_OUT = "cubic-bezier(.22,.8,.3,1)"
EASE_IO = "ease-in-out"
SPRING = "cubic-bezier(.3,1.35,.5,1)"


def joy(at=.3):
    """Happy eyes: the open eyes go, the closed ones turn up into arcs."""
    return [P("eyes", "opacity:0", (.28, "ease-out", {}), at=at),
            P("eyes-closed", "opacity:1; transform:scaleY(-1)", (.28, "ease-out", {0: "opacity:0; transform:scaleY(-1)"}), at=at)]


def joy_blink(at=.2, dur=1.2):
    """Eyes squeeze happily shut for a moment and open again."""
    return [P("eyes", "", (dur, EASE_IO, {14: "opacity:0", 80: "opacity:0"}), at=at),
            P("eyes-closed", "", (dur, EASE_IO, {0: "opacity:0; transform:scaleY(-1)", 14: "opacity:1; transform:scaleY(-1)",
                                                 80: "opacity:1; transform:scaleY(-1)", 100: "opacity:0; transform:scaleY(-1)"}), at=at)]


def face_arc(cx, cy, w, k=.75):
    """One happy eye: an arch (^), its middle well above its ends."""
    return "M%s %s Q%s %s %s %s" % (f2(cx - w), f2(cy + w * .35), f2(cx), f2(cy - w * k), f2(cx + w), f2(cy + w * .35))


def glee(eyes, col, core=None, sw=.42, halo=None):
    """HAPPY EYES THAT ARE LIGHT (build 321): a character whose eyes glow -
    slits of light in a dark face, a visor - smiles with two arches of
    that light (^ ^), a soft wide one under a bright core. Drawn on the
    face (front=2: inside the group that holds the eyes, so the head's
    fit and every head move carry it). eyes: [(cx, cy, halfWidth)]."""
    out = ""
    for cx, cy, w in eyes:
        d = face_arc(cx, cy, w)
        out += path(d, stroke=col, sw=sw * (halo or 2.6), op=.45)
        out += path(d, stroke=core or col, sw=sw).replace("<path ", '<path data-face="eye" ', 1)
    return out


def grin(cx, cy, w, col, sw=.45, k=.55):
    """A smile drawn on the face: the middle well below the corners."""
    return path("M%s %s Q%s %s %s %s" % (f2(cx - w), f2(cy), f2(cx), f2(cy + w * k * 2), f2(cx + w), f2(cy)),
                stroke=col, sw=sw).replace("<path ", '<path data-face="mouth" ', 1)


def cheer(at=.3, hide=("eyes",), extra=()):
    """THE 100 IS HAPPY ON EVERY FACE (build 321): "the alien still looks
    mad even after the hundred.. ensure all characters are happy when they
    get the 100." The open eyes (and anything else named) go, and the
    face's own happy pieces (the prop `glee`, drawn by glee()/grin()) come
    in and stay - the pose every later loop and the hundo effect's own
    reaction come back to."""
    return ([P(h, "opacity:0", (.3, "ease-out", {}), at=at) for h in hide] +
            [P("p-glee", "opacity:1", (.3, "ease-out", {0: "opacity:0"}), at=at)] + list(extra))


def nod(dur=1.1, at=.1, k=1.0):
    """A satisfied double nod."""
    return P("head", "", (dur, EASE_IO, {22: "transform:translateY(%spx) rotate(%sdeg)" % (f2(1.1 * k), f2(3 * k)),
                                          46: "transform:none",
                                          68: "transform:translateY(%spx) rotate(%sdeg)" % (f2(.8 * k), f2(2 * k))}), at=at)


def slump(deg=-10, dy=1.7, dur=1.3, sigh=3.6, at=0):
    """Head goes down, and sighs."""
    pose = "transform:translateY(%spx) rotate(%sdeg)" % (f2(dy), f2(deg))
    return P("head", pose, (dur, EASE_OUT, {55: "transform:translateY(%spx) rotate(%sdeg)" % (f2(dy + .4), f2(deg - 1.5))}),
             (sigh, EASE_IO, {50: "transform:translateY(%spx) rotate(%sdeg)" % (f2(dy + .5), f2(deg - 1.4))}), at=at)


def eyes_down(dy=.7, sy=.7, at=.2, op=None):
    pose = "transform:translateY(%spx) scaleY(%s)" % (f2(dy), f2(sy)) + ("; opacity:%s" % f2(op) if op is not None else "")
    return P("eyes", pose, (.8, "ease-out", {}), at=at)


def sink(dy=1.4, s=.97, at=0, dur=1.3):
    return P("fig", "transform:translateY(%spx) scale(%s)" % (f2(dy), f2(s)), (dur, EASE_OUT, {}), at=at)


def flash_parts(sel, at, dur, pattern, loop=None, pose=""):
    """A part that flickers on and off (hidden at rest)."""
    return P(sel, pose, (dur, "linear", pattern), loop, at=at)


# ---------------------------------------------------------------------------
# THE TABLE. RX[char][band] = {"parts": [...], "props": [(name, front, svg)], "flash": (colour, at_s)}
RX = {}


def R(cid, band, parts, props=(), flash=None):
    RX.setdefault(cid, {})[band] = {"parts": [p for p in parts if p], "props": list(props), "flash": flash}


exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "reactions-table.py"), encoding="utf-8").read())


# ---------------------------------------------------------------------------
def slug(s):
    return re.sub(r"[^a-z0-9]+", "", s.replace("fx-", "").replace("p-", "p").replace("eyes-closed", "shut").lower())


def build():
    kf, motion, still = [], [], []
    names_seen = set()
    for cid in RX:
        for band in BANDS:
            spec = RX[cid].get(band)
            if not spec:
                continue
            b2 = {"perfect": "pf", "great": "gr", "pass": "ps", "fail": "fl"}[band]
            for p in spec["parts"]:
                # THE SELECTOR CHROMIUM CAN FILE (build 315). This was
                # `.rx-<id>.rx-<band> :is(#rx,.part)` - the #rx (nothing has
                # that id) only lifts the rule to id weight, over the idle
                # loops. But a rule that ends in :is() of several things has
                # no class to be filed under, so Chromium tested all ~800 of
                # them against every element of every screen it drew: measured
                # at 4x CPU, tab switches went from 230ms to 262ms median.
                # `.part:not(#rx)` ends in a class, and :where() makes the
                # band free, so the weight is still (1,2,0) and the same
                # elements match. Several parts make a list of the same rule.
                scope = ", ".join(".rx-%s:where(.rx-%s) %s:not(#rx)" % (cid, band, cls(s)) for s in p.sel)
                base = "rx-%s-%s-%s" % (cid, b2, slug(p.sel[0]))
                while base in names_seen:
                    base += "x"
                names_seen.add(base)
                anims = []
                end = p.at
                if p.intro:
                    dur, ease, frames = p.intro
                    props = list(p.pose)
                    for pct in sorted(frames):
                        props += [k for k in decls(frames[pct]) if k not in props]
                    rest = {k: p.rest(k) for k in props}
                    fr0 = dict(rest)
                    fr0.update(decls(frames.get(0, "")))
                    fr100 = dict(rest)
                    fr100.update(p.pose)
                    if 100 in frames:
                        fr100.update(decls(frames[100]))
                    rows = ["0%%{%s}" % fmt(fr0)]
                    for pct in sorted(k for k in frames if k not in (0, 100)):
                        rows.append("%s%%{%s}" % (f2(pct), fmt(decls(frames[pct]))))
                    rows.append("100%%{%s}" % fmt(fr100))
                    kf.append("@keyframes %s{%s}" % (base, "".join(rows)))
                    anims.append("%s %ss %s %ss both" % (base, f2(dur), ease, f2(p.at)))
                    end = p.at + dur
                if p.loop:
                    dur, ease, frames = p.loop
                    props = list(p.pose)
                    for pct in sorted(frames):
                        props += [k for k in decls(frames[pct]) if k not in props]
                    rest = {k: p.rest(k) for k in props}
                    ends = dict(rest)
                    ends.update(p.pose)
                    rows = ["0%%,100%%{%s}" % fmt(ends)]
                    for pct in sorted(k for k in frames if k not in (0, 100)):
                        rows.append("%s%%{%s}" % (f2(pct), fmt(decls(frames[pct]))))
                    kf.append("@keyframes %s-l{%s}" % (base, "".join(rows)))
                    anims.append("%s-l %ss %s %ss infinite" % (base, f2(dur), ease, f2(end)))
                if p.turn:
                    dur, sense = p.turn
                    t = p.pose.get("transform", "none")
                    if t in ("none", ""):
                        a, b = "rotate(0deg)", "rotate(%ddeg)" % (360 * sense)
                    else:
                        m = re.search(r"rotate\((-?[\d.]+)deg\)\s*$", t)
                        assert m, "a turn needs a pose ending in rotate(): %s %s" % (cid, t)
                        a = t
                        b = t[:m.start()] + "rotate(%sdeg)" % f2(float(m.group(1)) + 360 * sense)
                    kf.append("@keyframes %s-turn{from{transform:%s}to{transform:%s}}" % (base, a, b))
                    anims.append("%s-turn %ss linear %ss infinite" % (base, f2(dur), f2(end)))
                anims += p.raw
                if anims:
                    motion.append("  %s{animation:%s}" % (scope, ",".join(anims)))
                else:
                    motion.append("  %s{animation:none}" % scope)
                if p.pose:
                    still.append("%s{%s}" % (scope, fmt(p.pose)))
    css = ["/* RX:CSS:BEGIN - written by tools/gen-reactions.py; edit the table there, not here */",
           "@media (prefers-reduced-motion:no-preference){"] + motion + ["}"] + still + kf + ["/* RX:CSS:END */"]
    # The props, as JS.
    js = ["/* RX:JS:BEGIN - written by tools/gen-reactions.py; edit the table there, not here */",
          "const RX_PROPS = {"]
    for cid in RX:
        bands = []
        for band in BANDS:
            spec = RX[cid].get(band)
            if not spec or not spec["props"]:
                continue
            items = ", ".join("[%s, %d, %s]" % (jsq(n), 2 if front == 2 else (1 if front else 0), jsq(svg)) for n, front, svg in spec["props"])
            bands.append("    %s: [%s]" % (band, items))
        if bands:
            js.append("  %s: {\n%s\n  }," % (cid, ",\n".join(bands)))
    js.append("};")
    fl = []
    for cid in RX:
        for band in BANDS:
            spec = RX[cid].get(band)
            if spec and spec["flash"]:
                fl.append('"%s/%s": [%s, %s]' % (cid, band, jsq(spec["flash"][0]), f2(spec["flash"][1])))
    js.append("const RX_FLASH = { %s };" % ", ".join(fl))
    js.append("const RX_CHARS = %s;" % ("[" + ", ".join(jsq(c) for c in RX) + "]"))
    js.append("/* RX:JS:END */")
    return "\n".join("  " + l if l and not l.startswith("@keyframes") else l for l in css), "\n".join(js)


def jsq(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def splice(src, begin, end, block):
    i = src.index(begin)
    j = src.index(end, i) + len(end)
    # keep the indentation of the line the marker sits on
    ls = src.rfind("\n", 0, i) + 1
    return src[:ls] + block + src[j:]


def main():
    css, js = build()
    src = io.open(INDEX, encoding="utf-8").read()
    out = splice(src, "/* RX:CSS:BEGIN", "/* RX:CSS:END */", css)
    out = splice(out, "/* RX:JS:BEGIN", "/* RX:JS:END */", js)
    if "--check" in sys.argv:
        if out != src:
            print("index.html's reaction blocks are stale - run python3 tools/gen-reactions.py")
            sys.exit(1)
        print("reaction blocks up to date (%d characters)" % len(RX))
        return
    if out != src:
        io.open(INDEX, "w", encoding="utf-8").write(out)
    n = sum(len(v) for v in RX.values())
    print("wrote %d characters, %d reactions, %d bytes of CSS" % (len(RX), n, len(css)))


if __name__ == "__main__":
    main()
