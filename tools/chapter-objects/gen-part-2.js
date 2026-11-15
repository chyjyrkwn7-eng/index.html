#!/usr/bin/env node
/* Fire Code chapter objects, part 2 (Chapters 22-31): the outlines that are organic unions - a hand of bananas, a beetle and its legs, a
   stack of logs, a grain bin, a fuel dispenser's hose loop, a paint can and its run of paint - built from signed distance fields and
   written into tools/chapter-objects/part-2.js as plain path strings (between its @@P2_SHAPES markers), so the page never traces anything
   (traced at load, the ten took most of a second).
     node tools/chapter-objects/gen-part-2.js            rewrite the block
     node tools/chapter-objects/gen-part-2.js --check    exit 1 if the block is stale
   The parts are capsules, tapered capsules, circles, ellipses, boxes and polygons, joined with a smooth minimum (every join filleted,
   never a hard notch); the zero line is traced by marching squares on a half-unit grid (linear edge points), simplified to 0.04 units,
   into ONE closed M L .. Z path (and, with trace(), any holes as their own paths). Not a part file (the merge reads part-*.js only). */
const fs = require("fs"), path = require("path");
/* (384.68) the toolkit is tools/chapter-objects/sdf.js now (OBJ_SDF), shared with every part file at merge time */
const { len, circle, ellipse, capsule, cone, box, poly, tube, smin, union, minus, inter, grow, loops, trace, shape } = require("./sdf.js");
const OUT = {};

/* Chapter 22: the grain bin (a cylinder: a curved foot and a curved eave), its cone roof and cap, and on its RIGHT the elevator leg,
   head and boot, with the spout running down from the head into the cap (on the left, the leg's long side wall pulled the pin's wall
   up-left of its face) */
{
  const bin = union([box(12, 48, 54, 42, 0), ellipse(39, 90, 27, 5)], 0);
  const eave = ellipse(39, 47, 31, 4.5);
  const roof = poly([[46, 22], [32, 22], [9, 45], [69, 45]]);
  const cap = box(31, 14, 16, 9, 2);
  const leg = box(80, 12, 10, 72, 0), head = box(77, 4, 16, 10, 2), boot = box(75, 82, 20, 12, 2);
  const spout = poly([[78, 6.5], [46, 16], [46, 22.5], [78, 13.5]]);
  OUT.c22 = { d: shape(union([bin, eave, roof, cap, leg, head, boot, spout], 1.6), [2, 1, 98, 99]), bin: shape(bin, [8, 44, 70, 99]),
    eave: shape(eave, [4, 40, 74, 54]) };
}
/* Chapter 23: the dispenser, its plinth, the hose loop (a hole) and the nozzle hung in its holster */
{
  const hose = union([capsule(66, 71.5, 80, 71.5, 3.6), capsule(83.5, 40, 83.5, 64, 3.6), tube([78, 71.5], [83.5, 71.5], [83.5, 64], () => 3.6, 6)], 0);
  const nozzle = union([box(75, 22, 17, 11, 3), capsule(83.5, 30, 83.5, 41, 3.6), capsule(77, 26, 68, 33, 2.8)], 2);
  const body = union([box(20, 12, 48, 76, 3), box(15, 3, 58, 13, 4), box(14, 86, 60, 9, 2.5)], 1.5);
  const sil = trace(union([body, hose, nozzle], 2.4), [10, 2, 96, 98]);
  OUT.c23 = { d: sil.d, holes: sil.holes, hose: shape(hose, [60, 36, 90, 78]), nozzle: shape(nozzle, [58, 18, 94, 44]) };
}
/* Chapter 25: three fingers fanning from the crown */
{
  const rf = R => t => t < .1 ? 3 + 8 * t : 3.8 + (R - 3.8) * Math.pow(Math.sin(Math.PI * Math.min(1, (t - .1) / .95)), .55);
  const B1 = tube([20, 20], [56, 42], [92, 16], rf(9.4), 20), B2 = tube([18, 24], [46, 62], [88, 46], rf(10), 20), B3 = tube([16, 28], [28, 82], [70, 84], rf(10.6), 20);
  const crown = capsule(11, 12, 19, 23, 5), bb = [2, 2, 98, 98];
  OUT.c25 = { d: shape(union([B1, B2, B3, crown], 3), bb),
    b1: shape(minus(B1, grow(union([B2, B3, crown], 0), .4)), bb), b2: shape(minus(B2, grow(union([B3, crown], 0), .4)), bb),
    b3: shape(minus(B3, grow(crown, .4)), bb), crown: shape(crown, bb) };
}
/* Chapter 26: the beetle (legs and antennae as capsules; part-2.js strokes the same polylines, P2B, for their parts) */
{
  const legs = [[[37, 34], [26, 30], [20, 18]], [[30, 52], [16, 50], [9, 62]], [[32, 70], [20, 78], [16, 92]]], ant = [[45, 13], [40, 7], [32, 4]];
  const mir = p => [100 - p[0], p[1]], caps = [];
  const chain = (pts, r) => { for(let i = 0; i < pts.length - 1; i++) caps.push(capsule(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], r)); };
  legs.forEach(l => { chain(l, 2.7); chain(l.map(mir), 2.7); }); chain(ant, 2.5); chain(ant.map(mir), 2.5);
  OUT.c26 = { d: shape(union([ellipse(50, 62, 24, 31), box(33, 26, 34, 16, 6), ellipse(50, 18, 10, 8.5)].concat(caps), 2.6), [2, 0, 98, 98]) };
}
/* Chapter 27: the package and its sixteen pins */
{
  const pins = []; [31, 43, 57, 69].forEach(c => { pins.push(box(c - 3, 6, 6, 18, 1.5), box(c - 3, 76, 6, 18, 1.5), box(6, c - 3, 18, 6, 1.5), box(76, c - 3, 18, 6, 1.5)); });
  OUT.c27 = { d: shape(union([box(20, 20, 60, 60, 4)].concat(pins), 1.6), [2, 2, 98, 98]) };
}
/* Chapter 28: six log ends, three, two, one */
{
  const L = [[22, 78], [50, 78], [78, 78], [36, 53.75], [64, 53.75], [50, 29.5]];
  OUT.c28 = { d: shape(union(L.map(c => circle(c[0], c[1], 14)), 4), [4, 12, 96, 96]) };
}
/* Chapter 29: the can, the bail (a hole under it) and the paint run over the rim, down the side and into a pool */
{
  const can = union([box(18, 30, 64, 60, 5), box(14, 25, 72, 9, 3)], 1.2);
  const bail = minus(inter(ellipse(50, 30, 35, 27), (x, y) => y - 30), ellipse(50, 30, 29.5, 21.5));
  const paint = union([box(13, 24, 74, 11, 4), capsule(26, 30, 26, 52, 5), capsule(44, 30, 44, 44, 4.4), capsule(66, 30, 66, 58, 4.8),
    capsule(19, 30, 17, 88, 4.4), ellipse(30, 91, 22, 5)], 3);
  const all = union([can, bail, paint], 2), sil = trace(all, [4, 0, 96, 99]);
  OUT.c29 = { d: sil.d, holes: sil.holes, can: shape(can, [10, 20, 90, 94]), bail: shape(bail, [10, 0, 90, 34]),
    paint: shape(inter(paint, grow(all, -.01)), [4, 18, 96, 99]) };
}

const P = path.join(__dirname, "part-2.js"), src = fs.readFileSync(P, "utf8");
const B = "/* @@P2_SHAPES_BEGIN (generated by tools/chapter-objects/gen-part-2.js: never edit by hand) */", E = "/* @@P2_SHAPES_END */";
const i = src.indexOf(B), j = src.indexOf(E);
if(i < 0 || j < 0){ console.error("part-2.js has no @@P2_SHAPES block"); process.exit(2); }
const block = "\n  const P2S = {\n" + Object.keys(OUT).map(k => "    " + k + ": " + JSON.stringify(OUT[k]) + ",\n").join("") + "  };\n  ";
const out = src.slice(0, i + B.length) + block + src.slice(j);
if(process.argv.includes("--check")){ console.log(out === src ? "in step" : "part-2.js's shapes are stale (run node tools/chapter-objects/gen-part-2.js)"); process.exit(out === src ? 0 : 1); }
fs.writeFileSync(P, out); console.log("wrote", Object.keys(OUT).length, "shape sets,", block.length, "chars");
