#!/usr/bin/env node
/* Fire Code chapter objects (build 384.65): evaluate tools/chapter-objects/part-*.js and measure every silhouette.
   node tools/chapter-objects/measure.js [--index FILE]    prints one JSON line:  { bbox: { title: [x, y, w, h] }, errors: [..] }
   The part files are JavaScript (they call the helpers OBJ_circle, OBJ_rrect, OBJ_poly ... that index.html defines), so the box of
   a silhouette can only be known by running them: the helpers (and OBJ_walk, the one path walker the page uses too) are lifted out of
   index.html (from `const CHAPTER_OBJ = {}` up to the merge marker), the part files are run after them, and each silhouette's path is
   walked and measured. A path may use M L H V C Q A Z (either case). Anything else is an error (S and T are not supported on purpose:
   write the curve out). The box is the OUTLINE's (d), never the holes'.
   (384.67) It also prints `baked`: every entry as the part files leave it, as plain data, file by file ([[file, [[key, entry], ...]], ...]).
   The merge writes THAT into index.html, not the part files' code: whatever a part file computes (an arc traced into points, a ring of
   teeth, a curve offset) is computed once here, at merge time, and the page only reads finished strings - nothing a helper writes costs
   anything at boot. */
const fs = require("fs"), path = require("path");
const ROOT = path.resolve(__dirname, "..", "..");
const ai = process.argv.indexOf("--index");
const index = fs.readFileSync(ai > 0 ? process.argv[ai + 1] : path.join(ROOT, "index.html"), "utf8");
const i0 = index.indexOf("const CHAPTER_OBJ = {};"), i1 = index.indexOf("/* @@CHAPTER_OBJ_BEGIN */");
if(i0 < 0 || i1 < 0){ console.log(JSON.stringify({ bbox: {}, errors: ["index.html has no chapter-object block"] })); process.exit(0); }
const helpers = index.slice(i0, i1);
const files = fs.readdirSync(__dirname).filter(f => /^part-.*\.js$/.test(f)).sort();
const errors = [];
/* (384.68) OBJ_SDF (sdf.js), the signed-distance toolkit, is there for every part file: it runs here, at merge, never in the page */
let src = helpers + "\n" + fs.readFileSync(path.join(__dirname, "sdf.js"), "utf8") + "\nconst __FILES = [];";
/* each file in its own block, so one file's consts cannot meet another's; the keys it added are noted after it */
files.forEach(f => { src += "\n{\nconst __k0 = Object.keys(CHAPTER_OBJ);\n" + fs.readFileSync(path.join(__dirname, f), "utf8") +
  "\n;__FILES.push([" + JSON.stringify(f) + ", Object.keys(CHAPTER_OBJ).filter(k => __k0.indexOf(k) < 0)]);\n}"; });
let OBJ, walk, FILES;
try{ const r = new Function(src + "\n;return { O: CHAPTER_OBJ, w: OBJ_walk, F: __FILES };")(); OBJ = r.O; walk = r.w; FILES = r.F; }
catch(e){ console.log(JSON.stringify({ bbox: {}, errors: ["evaluating the part files: " + e.message] })); process.exit(0); }
const bbox = {};
Object.keys(OBJ).forEach(k => {
  const e = OBJ[k];
  try{
    if(!e || typeof e.d !== "string") throw new Error("no d");
    const pts = walk(e.d, 40);
    let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
    pts.forEach(p => { if(p[0] < x0) x0 = p[0]; if(p[0] > x1) x1 = p[0]; if(p[1] < y0) y0 = p[1]; if(p[1] > y1) y1 = p[1]; });
    if(!(x1 > x0 && y1 > y0)) throw new Error("empty path");
    bbox[k] = [x0, y0, x1 - x0, y1 - y0].map(v => Math.round(v * 100) / 100);
    (e.plates || []).forEach((q, n) => { try{ walk(q[1], 8); }catch(err){ errors.push(k + " plate " + n + ": " + err.message); } });
    (e.holes || []).forEach((h, n) => { try{ walk(h, 8); }catch(err){ errors.push(k + " hole " + n + ": " + err.message); } });
  }catch(err){ errors.push(k + ": " + err.message); }
});
const baked = FILES.map(([f, keys]) => [f, keys.map(k => [k, OBJ[k]])]);
console.log(JSON.stringify({ bbox, errors, baked }));
