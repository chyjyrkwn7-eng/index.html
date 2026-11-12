#!/usr/bin/env node
/* Fire Code chapter objects (build 384.65): evaluate tools/chapter-objects/part-*.js and measure every silhouette.
   node tools/chapter-objects/measure.js [--index FILE]    prints one JSON line:  { bbox: { title: [x, y, w, h] }, errors: [..] }
   The part files are JavaScript (they call the helpers OBJ_circle, OBJ_rrect, OBJ_poly ... that index.html defines), so the box of
   a silhouette can only be known by running them: the helpers are lifted out of index.html (from `const CHAPTER_OBJ = {}` up to the
   merge marker), the part files are run after them, and each silhouette's path is walked and measured numerically.
   A path may use M L H V Q C A Z (either case). Anything else is an error (S and T are not supported on purpose: write the curve out). */
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
let OBJ;
try{ OBJ = new Function(src + "\n;return CHAPTER_OBJ;")(); }catch(e){ console.log(JSON.stringify({ bbox: {}, errors: ["evaluating the part files: " + e.message] })); process.exit(0); }
/* ---- path walking ---- */
function tokens(d){
  const out = [], re = /([MmLlHhVvCcQqAaZz])|(-?\d*\.?\d+(?:e[-+]?\d+)?)/gi;
  let m; while((m = re.exec(d))){ out.push(m[1] ? m[1] : parseFloat(m[2])); }
  return out;
}
function arcPoints(x1, y1, rx, ry, phi, fa, fs, x2, y2, n){
  rx = Math.abs(rx); ry = Math.abs(ry);
  if(!rx || !ry) return [[x2, y2]];
  const c = Math.cos(phi * Math.PI / 180), s = Math.sin(phi * Math.PI / 180);
  const dx = (x1 - x2) / 2, dy = (y1 - y2) / 2, x1p = c * dx + s * dy, y1p = -s * dx + c * dy;
  const lam = x1p * x1p / (rx * rx) + y1p * y1p / (ry * ry);
  if(lam > 1){ const q = Math.sqrt(lam); rx *= q; ry *= q; }
  const sign = fa === fs ? -1 : 1;
  const num = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p, den = rx * rx * y1p * y1p + ry * ry * x1p * x1p;
  const co = sign * Math.sqrt(Math.max(0, num / den));
  const cxp = co * rx * y1p / ry, cyp = -co * ry * x1p / rx;
  const cx = c * cxp - s * cyp + (x1 + x2) / 2, cy = s * cxp + c * cyp + (y1 + y2) / 2;
  const ang = (ux, uy, vx, vy) => { const a = Math.atan2(ux * vy - uy * vx, ux * vx + uy * vy); return a; };
  const th1 = ang(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry);
  let dth = ang((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry);
  if(!fs && dth > 0) dth -= 2 * Math.PI; else if(fs && dth < 0) dth += 2 * Math.PI;
  const pts = [];
  for(let i = 1; i <= n; i++){ const t = th1 + dth * i / n; pts.push([cx + c * rx * Math.cos(t) - s * ry * Math.sin(t), cy + s * rx * Math.cos(t) + c * ry * Math.sin(t)]); }
  return pts;
}
/* the path's points, densely, or an error string */
function walk(d){
  const t = tokens(d), pts = []; let i = 0, cmd = "", x = 0, y = 0, sx = 0, sy = 0;
  const num = () => { const v = t[i++]; if(typeof v !== "number") throw new Error("a number was expected near token " + i + " of " + d.slice(0, 40)); return v; };
  while(i < t.length){
    if(typeof t[i] === "string") cmd = t[i++]; else if(cmd === "M") cmd = "L"; else if(cmd === "m") cmd = "l";
    const rel = cmd === cmd.toLowerCase(), C = cmd.toUpperCase(), ox = rel ? x : 0, oy = rel ? y : 0;
    if(C === "M"){ x = ox + num(); y = oy + num(); sx = x; sy = y; pts.push([x, y]); }
    else if(C === "L"){ x = ox + num(); y = oy + num(); pts.push([x, y]); }
    else if(C === "H"){ x = ox + num(); pts.push([x, y]); }
    else if(C === "V"){ y = oy + num(); pts.push([x, y]); }
    else if(C === "Q"){ const a = ox + num(), b = oy + num(), ex = ox + num(), ey = oy + num();
      for(let k = 1; k <= 40; k++){ const u = k / 40; pts.push([(1 - u) * (1 - u) * x + 2 * (1 - u) * u * a + u * u * ex, (1 - u) * (1 - u) * y + 2 * (1 - u) * u * b + u * u * ey]); } x = ex; y = ey; }
    else if(C === "C"){ const a = ox + num(), b = oy + num(), c2 = ox + num(), d2 = oy + num(), ex = ox + num(), ey = oy + num();
      for(let k = 1; k <= 40; k++){ const u = k / 40, v = 1 - u; pts.push([v * v * v * x + 3 * v * v * u * a + 3 * v * u * u * c2 + u * u * u * ex, v * v * v * y + 3 * v * v * u * b + 3 * v * u * u * d2 + u * u * u * ey]); } x = ex; y = ey; }
    else if(C === "A"){ const rx = num(), ry = num(), phi = num(), fa = num(), fs = num(), ex = ox + num(), ey = oy + num();
      arcPoints(x, y, rx, ry, phi, fa, fs, ex, ey, 60).forEach(p => pts.push(p)); x = ex; y = ey; }
    else if(C === "Z"){ x = sx; y = sy; pts.push([x, y]); }
    else throw new Error("unsupported command " + cmd);
  }
  return pts;
}
const bbox = {};
Object.keys(OBJ).forEach(k => {
  const e = OBJ[k];
  try{
    if(!e || typeof e.d !== "string") throw new Error("no d");
    const pts = walk(e.d);
    let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
    pts.forEach(p => { if(p[0] < x0) x0 = p[0]; if(p[0] > x1) x1 = p[0]; if(p[1] < y0) y0 = p[1]; if(p[1] > y1) y1 = p[1]; });
    if(!(x1 > x0 && y1 > y0)) throw new Error("empty path");
    bbox[k] = [x0, y0, x1 - x0, y1 - y0].map(v => Math.round(v * 100) / 100);
    (e.plates || []).forEach((q, n) => { try{ walk(q[1]); }catch(err){ errors.push(k + " plate " + n + ": " + err.message); } });
  }catch(err){ errors.push(k + ": " + err.message); }
});
console.log(JSON.stringify({ bbox, errors }));
