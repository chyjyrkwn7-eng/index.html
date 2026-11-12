#!/usr/bin/env node
/* Fire Code chapter objects (build 384.65): evaluate tools/chapter-objects/part-*.js and measure every silhouette.
   node tools/chapter-objects/measure.js [--index FILE]    prints one JSON line:  { bbox: { title: [x, y, w, h] }, errors: [..] }
   The part files are JavaScript (they call the helpers OBJ_circle, OBJ_rrect, OBJ_poly ... that index.html defines), so the box of
   a silhouette can only be known by running them: the helpers (and OBJ_walk, the one path walker the page uses too) are lifted out of
   index.html (from `const CHAPTER_OBJ = {}` up to the merge marker), the part files are run after them, and each silhouette's path is
   walked and measured. A path may use M L H V C Q A Z (either case). Anything else is an error (S and T are not supported on purpose:
   write the curve out). The box is the OUTLINE's (d), never the holes'. */
const fs = require("fs"), path = require("path");
const ROOT = path.resolve(__dirname, "..", "..");
const ai = process.argv.indexOf("--index");
const index = fs.readFileSync(ai > 0 ? process.argv[ai + 1] : path.join(ROOT, "index.html"), "utf8");
const i0 = index.indexOf("const CHAPTER_OBJ = {};"), i1 = index.indexOf("/* @@CHAPTER_OBJ_BEGIN */");
if(i0 < 0 || i1 < 0){ console.log(JSON.stringify({ bbox: {}, errors: ["index.html has no chapter-object block"] })); process.exit(0); }
const helpers = index.slice(i0, i1);
const files = fs.readdirSync(__dirname).filter(f => /^part-.*\.js$/.test(f)).sort();
const errors = [];
let src = helpers;
files.forEach(f => { src += "\n" + fs.readFileSync(path.join(__dirname, f), "utf8"); });
let OBJ, walk;
try{ const r = new Function(src + "\n;return { O: CHAPTER_OBJ, w: OBJ_walk };")(); OBJ = r.O; walk = r.w; }
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
console.log(JSON.stringify({ bbox, errors }));
