/* (384.120 follow-up) THE FOUR LOOKS DRAWN FOR THE VIRTUAL ROOM'S TOP TIER, "Win 10 rooms" (banner id vrwins10).
   Kept here, out of the shipped file, so the pick is a small change: index.html carries ONE of these as BANNER_ART.vrwins10
   (its name in BANNERS, its two colours in BANNER_TINT). To swap: copy the chosen function's body over BANNER_ART.vrwins10 in
   index.html, set the banner's `name` in BANNERS to the option's name and BANNER_TINT.vrwins10 to its `tint`, then run
   tools/check-b384-unlocks.py and tools/shoot-b384-vrwins.py.
   Every option is drawn the way the app's other moving banners are (see bnLayerHTML in index.html): a 480 x 180 scene of layers,
   each its own little svg, the motion a transform or an opacity on the layer's box (bl-* classes), no svg filters; glows are
   radial gradients. Loaded into a page by tools/shoot-b384-vrwins.py (it needs the page's bnRand / bnLin / bnRad / bnF /
   bnStarsSplit). Option A is the one shipped. */
window.VRW_OPTIONS = {
  /* A. WINNER'S CIRCLE - the Virtual Room's own results podium, as a stage: second, first and third under one spotlight, the cup
     on the top step, the stands either side with camera flashes, two searchlights sweeping behind and confetti coming down. */
  a: { name: "Winner's Circle", tint: ["#F2B636", "#6A4FD0"], art: function(u){
    const rnd = bnRand(1010);
    const st = bnStarsSplit(rnd, 34, 70);
    let crowd = "", flA = "", flB = "";
    [[-4, 176], [304, 484]].forEach(([x0, x1]) => {
      for(let row = 0; row < 3; row++){
        const y = 130 + row * 13;
        for(let x = x0 + (row % 2) * 5; x < x1; x += 10){
          const h = .85 + rnd() * .3;
          crowd += '<circle cx="' + bnF(x) + '" cy="' + bnF(y) + '" r="' + bnF(4.2 * h) + '"/><rect x="' + bnF(x - 5.5) + '" y="' + bnF(y + 3) + '" width="11" height="13" rx="4"/>';
          if(rnd() < .14){ const f = '<circle cx="' + bnF(x + 2) + '" cy="' + bnF(y - 1) + '" r="1.6"/>'; if(rnd() < .5) flA += f; else flB += f; }
        }
      }
    });
    const block = (x, y, w, h, g, top, num) =>
      '<path d="M' + x + ' ' + y + ' L' + (x + 5) + ' ' + (y - 5) + ' L' + (x + w - 5) + ' ' + (y - 5) + ' L' + (x + w) + ' ' + y + ' Z" fill="' + top + '"/>' +
      '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" fill="url(#' + u + g + ')"/>' +
      '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="2" fill="#FFFFFF" opacity=".35"/>' +
      '<text x="' + (x + w / 2) + '" y="' + (y + Math.min(h / 2 + 7, 24)) + '" text-anchor="middle" font-family="Arial Black, Arial, sans-serif" font-weight="900" font-size="18" fill="#FFFFFF" fill-opacity=".9">' + num + '</text>';
    let conf = "";
    const CC = ["#FFD34D", "#FFFFFF", "#5CE1FF", "#FF5CA8", "#9B7BFF", "#FFD34D"];
    for(let i = 0; i < 24; i++){
      const X = 96 + rnd() * 330, Y = -178 + rnd() * 176, r = Math.round(rnd() * 180), c = CC[i % CC.length];
      const p = (x, y) => '<rect x="' + bnF(x - 1.5) + '" y="' + bnF(y - 2.8) + '" width="3" height="5.6" rx=".6" fill="' + c + '" transform="rotate(' + r + ' ' + bnF(x) + ' ' + bnF(y) + ')"/>';
      conf += p(X, Y) + p(X - 40, Y + 180);
    }
    const defs = '<defs>' +
      bnLin(u + "sky", [[0, "#070A22"], [.6, "#1A1248"], [1, "#3A1E5E"]]) +
      bnRad(u + "halo", [[0, "#FFE7A0", .95], [.35, "#FFC94A", .42], [1, "#FFB020", 0]]) +
      bnLin(u + "beam", [[0, "#FFF4D0", .5], [1, "#FFF4D0", .04]]) +
      bnLin(u + "sl", [[0, "#BFD4FF", 0], [1, "#BFD4FF", .32]]) +
      bnLin(u + "g1", [[0, "#FFE58A"], [.5, "#F2B636"], [1, "#B07A12"]], 0, 0, 1, 1) +
      bnLin(u + "s2", [[0, "#F4F6FA"], [.5, "#B9BFC9"], [1, "#7C828C"]], 0, 0, 1, 1) +
      bnLin(u + "b3", [[0, "#F3B27A"], [.5, "#C27A3E"], [1, "#7E4519"]], 0, 0, 1, 1) +
      bnLin(u + "cup", [[0, "#FFF2B8"], [.45, "#F5C542"], [1, "#B9851A"]], 0, 0, 1, 0) +
      bnLin(u + "floor", [[0, "#2A1C5A"], [1, "#0B0820"]]) +
      bnRad(u + "pool", [[0, "#FFD37A", .55], [1, "#FFD37A", 0]]) +
      '</defs>';
    const cup = '<rect x="228" y="95" width="24" height="7" rx="1.5" fill="#6B4A10"/><rect x="231" y="91.5" width="18" height="4" rx="1" fill="url(#' + u + 'cup)"/>' +
      '<path d="M237 92 L238 82 L242 82 L243 92Z" fill="url(#' + u + 'cup)"/>' +
      '<path d="M226 60 Q214 60 216 70 Q218 77 229 76" fill="none" stroke="#E2AE2E" stroke-width="3" stroke-linecap="round"/>' +
      '<path d="M254 60 Q266 60 264 70 Q262 77 251 76" fill="none" stroke="#E2AE2E" stroke-width="3" stroke-linecap="round"/>' +
      '<path d="M223 55 L257 55 Q257 80 240 83 Q223 80 223 55Z" fill="url(#' + u + 'cup)"/>' +
      '<ellipse cx="240" cy="55" rx="17" ry="2.6" fill="#FFF6CF"/>' +
      '<path d="M240 61 L242.1 65.6 L247 66.1 L243.3 69.4 L244.4 74.2 L240 71.7 L235.6 74.2 L236.7 69.4 L233 66.1 L237.9 65.6Z" fill="#FFF8DC" opacity=".92"/>' +
      '<path d="M228 59 Q228 73 235 79" stroke="#FFFBEA" stroke-width="2" fill="none" opacity=".55" stroke-linecap="round"/>';
    const spark = (x, y, s) => '<path d="M' + x + ' ' + (y - s) + ' L' + (x + s * .22) + ' ' + (y - s * .22) + ' L' + (x + s) + ' ' + y + ' L' + (x + s * .22) + ' ' + (y + s * .22) + ' L' + x + ' ' + (y + s) + ' L' + (x - s * .22) + ' ' + (y + s * .22) + ' L' + (x - s) + ' ' + y + ' L' + (x - s * .22) + ' ' + (y - s * .22) + 'Z" fill="#FFFFFF"/>';
    return [
      { svg: defs + '<rect x="-10" y="-10" width="500" height="200" fill="url(#' + u + 'sky)"/><g>' + st.still + '</g>' },
      { svg: st.a, cls: "bl-tw", style: "animation-duration:2.9s" },
      { svg: st.b, cls: "bl-tw", style: "animation-duration:3.8s;animation-delay:-1.5s" },
      /* two searchlights from behind the stands, sweeping out of step */
      { svg: '<path d="M116 152 L58 -30 L86 -30 L124 152Z" fill="url(#' + u + 'sl)"/>', box: [40, -40, 100, 200], o: [120, 152], cls: "bl-sweep", style: "animation-duration:10s" },
      { svg: '<path d="M356 152 L394 -30 L422 -30 L364 152Z" fill="url(#' + u + 'sl)"/>', box: [340, -40, 100, 200], o: [360, 152], cls: "bl-sweep", style: "animation-duration:10s;animation-delay:-5s" },
      { svg: '<g fill="#0A0718">' + crowd + '</g>' +
          '<rect x="-10" y="158" width="500" height="32" fill="url(#' + u + 'floor)"/>' +
          '<ellipse cx="240" cy="159" rx="120" ry="12" fill="url(#' + u + 'pool)"/>' +
          block(168, 122, 46, 36, "s2", "#E9ECF2", "2") + block(214, 106, 52, 52, "g1", "#FFE9A6", "1") + block(266, 130, 46, 28, "b3", "#F1BF94", "3") },
      { svg: '<g fill="#FFFFFF">' + flA + '</g>', cls: "bl-tw", style: "animation-duration:1.3s" },
      { svg: '<g fill="#FFFFFF">' + flB + '</g>', cls: "bl-tw", style: "animation-duration:1.7s;animation-delay:-.8s" },
      /* the spotlight on the top step */
      { svg: '<path d="M222 -10 L258 -10 L304 160 L176 160Z" fill="url(#' + u + 'beam)"/>', box: [170, -10, 140, 172], o: [240, -10], cls: "bl-breathe", style: "animation-duration:4.2s" },
      { svg: '<circle cx="240" cy="70" r="56" fill="url(#' + u + 'halo)"/>', box: [184, 14, 112, 112], o: [240, 70], cls: "bl-pulse", style: "animation-duration:2.8s" },
      { svg: cup },
      { svg: spark(252, 57, 7), box: [244, 49, 16, 16], o: [252, 57], cls: "bl-spark", style: "animation-duration:2.6s" },
      { svg: spark(229, 78, 5), box: [223, 72, 12, 12], o: [229, 78], cls: "bl-spark", style: "animation-duration:2.6s;animation-delay:-1.3s" },
      /* confetti: one sheet, two tiles tall, falling exactly one tile (bl-fall: 40 left, 180 down of a 380 x 360 sheet) */
      { svg: '<g opacity=".9">' + conf + '</g>', box: [50, -180, 380, 360], cls: "bl-fall", style: "animation-duration:9s" }
    ];
  } },

  /* B. THE GRID - the room itself: a lit grid running to the horizon, a projector on the floor throwing up a hologram of a
     crown over a 10, two rings turning round it, a ring of light going out across the floor. */
  b: { name: "The Grid", tint: ["#3EF2FF", "#FF3EA5"], art: function(u){
    const rnd = bnRand(2020);
    const st = bnStarsSplit(rnd, 40, 96);
    const HY = 112, VX = 240;
    let hz = "", vt = "";
    for(let k = 1; k <= 9; k++){ const y = HY + 72 * Math.pow(k / 9, 2); hz += '<line x1="-10" y1="' + bnF(y) + '" x2="490" y2="' + bnF(y) + '" stroke-opacity="' + bnF(.25 + .5 * k / 9) + '"/>'; }
    for(let i = -12; i <= 12; i++){ vt += '<line x1="' + bnF(VX + i * 4) + '" y1="' + HY + '" x2="' + bnF(VX + i * 48) + '" y2="190"/>'; }
    let ridge = "M-10 " + HY;
    for(let x = -10; x <= 490; x += 20){ const d = Math.abs(x - VX); ridge += " L" + x + " " + bnF(HY - (d > 70 ? 6 + rnd() * 18 * Math.min(1, (d - 70) / 120) : 0)); }
    const defs = '<defs>' +
      bnLin(u + "sky", [[0, "#03051A"], [.7, "#140B3E"], [1, "#3B0F5C"]]) +
      bnRad(u + "hz", [[0, "#FF5CC8", .7], [1, "#FF5CC8", 0]]) +
      bnLin(u + "fl", [[0, "#1A0838"], [1, "#05020E"]]) +
      bnLin(u + "beam", [[0, "#5CF2FF", 0], [1, "#5CF2FF", .5]]) +
      bnRad(u + "core", [[0, "#BFFBFF", .9], [1, "#5CF2FF", 0]]) +
      '</defs>';
    const pylon = x => '<rect x="' + (x - 3) + '" y="' + (HY - 62) + '" width="6" height="62" fill="#0C0A26" stroke="#3EF2FF" stroke-opacity=".5" stroke-width="1"/>';
    const holo = '<g fill="#5CF2FF" fill-opacity=".16" stroke="#A8F9FF" stroke-width="1.6" stroke-linejoin="round">' +
      '<path d="M213 72 L217 48 L229 60 L240 42 L251 60 L263 48 L267 72 Z"/>' +
      '<text x="240" y="100" text-anchor="middle" font-family="Arial Black, Arial, sans-serif" font-weight="900" font-size="24" stroke-width="1.2">10</text></g>' +
      '<g fill="#E6FDFF"><circle cx="217" cy="47" r="2"/><circle cx="240" cy="41" r="2.4"/><circle cx="263" cy="47" r="2"/></g>' +
      '<g stroke="#A8F9FF" stroke-opacity=".35" stroke-width=".8">' + [56, 62, 68, 80, 86, 92].map(y => '<line x1="208" y1="' + y + '" x2="272" y2="' + y + '"/>').join("") + '</g>';
    const ring = (r, dash, w, op) => '<circle cx="0" cy="0" r="' + r + '" fill="none" stroke="#7FF6FF" stroke-width="' + w + '" stroke-dasharray="' + dash + '" opacity="' + op + '"/>';
    return [
      { svg: defs + '<rect x="-10" y="-10" width="500" height="200" fill="url(#' + u + 'sky)"/><g>' + st.still + '</g>' +
          '<ellipse cx="' + VX + '" cy="' + HY + '" rx="300" ry="34" fill="url(#' + u + 'hz)"/>' +
          '<path d="' + ridge + ' L490 ' + HY + 'Z" fill="#0C0A26" stroke="#FF3EA5" stroke-opacity=".7" stroke-width="1.2"/>' +
          pylon(70) + pylon(410) +
          '<rect x="-10" y="' + HY + '" width="500" height="80" fill="url(#' + u + 'fl)"/>' +
          '<g stroke="#FF3EA5" stroke-width="1">' + hz + '</g><g stroke="#3EF2FF" stroke-width=".9" stroke-opacity=".5">' + vt + '</g>' +
          '<rect x="-10" y="' + (HY - 1) + '" width="500" height="2" fill="#FF8AD8"/>' +
          '<ellipse cx="240" cy="152" rx="36" ry="7.5" fill="#0B1E3A" stroke="#5CF2FF" stroke-width="1.6"/><ellipse cx="240" cy="151" rx="20" ry="3.6" fill="#BFFBFF" opacity=".8"/>' },
      { svg: st.a, cls: "bl-tw", style: "animation-duration:2.6s" },
      { svg: st.b, cls: "bl-tw", style: "animation-duration:3.5s;animation-delay:-1.2s" },
      { svg: '<rect x="68" y="' + (HY - 58) + '" width="4" height="4" fill="#FF3EA5"/><rect x="408" y="' + (HY - 58) + '" width="4" height="4" fill="#FF3EA5"/>', cls: "bl-led", style: "animation-duration:1.6s" },
      { svg: '<ellipse cx="240" cy="152" rx="120" ry="22" fill="none" stroke="#FF5CC8" stroke-width="2"/>', box: [116, 128, 248, 48], o: [240, 152], cls: "bl-ping", style: "animation-duration:2.6s" },
      { svg: '<path d="M216 152 L264 152 L296 30 L184 30 Z" fill="url(#' + u + 'beam)"/>', box: [180, 28, 120, 126], o: [240, 152], cls: "bl-breathe", style: "animation-duration:3.2s" },
      { svg: '<circle cx="240" cy="72" r="46" fill="url(#' + u + 'core)" opacity=".5"/>' + holo, box: [190, 24, 100, 96], cls: "bl-float", style: "animation-duration:3s" },
      { svg: ring(48, "16 7.13", 1.4, ".85"), box: [188, 36, 104, 104], vb: [-52, -52, 104, 104], o: [240, 88], wrap: "scaleY(.24)", cls: "bl-spin", style: "animation-duration:6s" },
      { svg: ring(36, "3 4.54", 1.2, ".9"), box: [200, 60, 80, 80], vb: [-40, -40, 80, 80], o: [240, 100], wrap: "scaleY(.24)", cls: "bl-spin-r", style: "animation-duration:4s" }
    ];
  } },

  /* C. LAURELS - a ceremony's medal: a gold laurel wreath round a medallion with a star and a 10, the ribbon under it, light
     turning slowly behind, a sheen crossing the gold and a few sparkles. */
  c: { name: "Laurels", tint: ["#E8B531", "#2C3A8A"], art: function(u){
    const rnd = bnRand(3030);
    const st = bnStarsSplit(rnd, 30, 180);
    const CX = 240, CY = 82, R = 50;
    let rays = "";
    for(let i = 0; i < 18; i++){ const a = i / 18 * Math.PI * 2, b = a + Math.PI / 30;
      rays += '<path d="M' + CX + ' ' + CY + ' L' + bnF(CX + Math.cos(a) * 270) + ' ' + bnF(CY + Math.sin(a) * 270) + ' L' + bnF(CX + Math.cos(b) * 270) + ' ' + bnF(CY + Math.sin(b) * 270) + 'Z"/>'; }
    let leaves = "";
    for(let d = 104; d <= 250; d += 13){
      const t = d * Math.PI / 180;
      [[R + 5, 28], [R - 4, -28]].forEach(([rr, tilt], k) => {
        const x = CX + Math.cos(t) * rr, y = CY + Math.sin(t) * rr, rot = d + 90 + tilt;
        const lf = (xx, rt) => '<ellipse cx="' + bnF(xx) + '" cy="' + bnF(y) + '" rx="7.4" ry="3.1" transform="rotate(' + bnF(rt) + ' ' + bnF(xx) + ' ' + bnF(y) + ')" fill="' + (k ? "#C9921C" : "url(#" + u + "lf)") + '"/>';
        leaves += lf(x, rot) + lf(2 * CX - x, 180 - rot);
      });
    }
    const stem = '<path d="M' + bnF(CX + Math.cos(104 * Math.PI / 180) * R) + ' ' + bnF(CY + Math.sin(104 * Math.PI / 180) * R) + ' A' + R + ' ' + R + ' 0 0 1 ' + bnF(CX + Math.cos(250 * Math.PI / 180) * R) + ' ' + bnF(CY + Math.sin(250 * Math.PI / 180) * R) + '" fill="none" stroke="#A8770F" stroke-width="2"/>';
    const stemR = '<g transform="translate(' + (2 * CX) + ' 0) scale(-1 1)">' + stem + '</g>';
    const star = (x, y, r) => { let s = ""; for(let i = 0; i < 10; i++){ const a = -Math.PI / 2 + i * Math.PI / 5, q = i % 2 ? r * .45 : r; s += (i ? "L" : "M") + bnF(x + Math.cos(a) * q) + " " + bnF(y + Math.sin(a) * q) + " "; } return s + "Z"; };
    const spark = (x, y, s) => '<path d="M' + x + ' ' + (y - s) + ' L' + (x + s * .22) + ' ' + (y - s * .22) + ' L' + (x + s) + ' ' + y + ' L' + (x + s * .22) + ' ' + (y + s * .22) + ' L' + x + ' ' + (y + s) + ' L' + (x - s * .22) + ' ' + (y + s * .22) + ' L' + (x - s) + ' ' + y + ' L' + (x - s * .22) + ' ' + (y - s * .22) + 'Z" fill="#FFF6D0"/>';
    const defs = '<defs>' +
      bnRad(u + "bg", [[0, "#2A3474"], [.55, "#0F1436"], [1, "#05060F"]], "50%", "45%", "70%") +
      bnLin(u + "gd", [[0, "#FFF0B0"], [.45, "#F2C040"], [1, "#9C6A0E"]], 0, 0, 1, 1) +
      bnLin(u + "lf", [[0, "#FFE48A"], [1, "#D9A52A"]], 0, 0, 1, 1) +
      bnLin(u + "sh", [[0, "#FFFFFF", 0], [.5, "#FFFFFF", .75], [1, "#FFFFFF", 0]], 0, 0, 1, 0) +
      bnRad(u + "gl", [[0, "#FFD86A", .55], [1, "#FFD86A", 0]]) +
      '</defs>';
    const ribbon = '<path d="M228 104 L206 168 L214 162 L220 172 L240 112Z" fill="#C8283C"/><path d="M252 104 L274 168 L266 162 L260 172 L240 112Z" fill="#2C5BD8"/>' +
      '<path d="M228 104 L222 122 L240 112Z" fill="#000" opacity=".25"/>';
    const medal = '<circle cx="' + CX + '" cy="' + CY + '" r="34" fill="url(#' + u + 'gd)" stroke="#7A5310" stroke-width="2"/>' +
      '<circle cx="' + CX + '" cy="' + CY + '" r="27" fill="#18204E" stroke="#F6D267" stroke-width="1.6"/>' +
      '<path d="' + star(CX, CY - 13, 7.5) + '" fill="url(#' + u + 'gd)"/>' +
      '<text x="' + CX + '" y="' + (CY + 15) + '" text-anchor="middle" font-family="Arial Black, Arial, sans-serif" font-weight="900" font-size="21" fill="url(#' + u + 'gd)">10</text>';
    return [
      { svg: defs + '<rect x="-10" y="-10" width="500" height="200" fill="url(#' + u + 'bg)"/><g>' + st.still + '</g>' },
      { svg: st.a, cls: "bl-tw", style: "animation-duration:3s" },
      { svg: st.b, cls: "bl-tw", style: "animation-duration:3.9s;animation-delay:-1.6s" },
      { svg: '<g fill="#FFE7A0" opacity=".08">' + rays + '</g>', box: [CX - 270, CY - 270, 540, 540], o: [CX, CY], cls: "bl-spin", style: "animation-duration:60s" },
      { svg: '<circle cx="' + CX + '" cy="' + CY + '" r="80" fill="url(#' + u + 'gl)"/>', box: [CX - 80, CY - 80, 160, 160], o: [CX, CY], cls: "bl-breathe", style: "animation-duration:3.6s" },
      { svg: ribbon + stem + stemR + leaves + medal },
      /* the sheen across the medal, clipped to it; held out of the still picture (opacity 0 until it runs) */
      { svg: '<rect x="' + (CX - 10) + '" y="' + (CY - 40) + '" width="20" height="80" fill="url(#' + u + 'sh)" transform="rotate(20 ' + CX + ' ' + CY + ')"/>', box: [CX - 34, CY - 34, 68, 68],
        clip: "circle(50% at 50% 50%)", cls: "bl-glintx", style: "animation-duration:4.4s;opacity:0" },
      { svg: spark(196, 46, 6), box: [189, 39, 14, 14], o: [196, 46], cls: "bl-spark", style: "animation-duration:2.8s" },
      { svg: spark(287, 58, 5), box: [281, 52, 12, 12], o: [287, 58], cls: "bl-spark", style: "animation-duration:2.8s;animation-delay:-1s" },
      { svg: spark(276, 122, 4.5), box: [270, 116, 12, 12], o: [276, 122], cls: "bl-spark", style: "animation-duration:2.8s;animation-delay:-1.9s" }
    ];
  } },

  /* D. PENNANTS - ten pennants on a line across a stadium under its floodlights, numbered one to ten, each swinging on its own,
     and the gold championship flag hanging under the middle of them. */
  d: { name: "Pennants", tint: ["#FFD34D", "#3EC5FF"], art: function(u){
    const rnd = bnRand(4040);
    const st = bnStarsSplit(rnd, 26, 80);
    const P0 = [62, 30], PC = [240, 74], P1 = [418, 30];
    const at = t => [(1 - t) * (1 - t) * P0[0] + 2 * (1 - t) * t * PC[0] + t * t * P1[0], (1 - t) * (1 - t) * P0[1] + 2 * (1 - t) * t * PC[1] + t * t * P1[1]];
    const COL = ["#FFD34D", "#3EC5FF", "#FF5A7A", "#F4F6FA", "#9B7BFF"];
    const pen = [];
    for(let i = 0; i < 10; i++){
      const [x, y] = at((i + .5) / 10), c = COL[i % COL.length], ink = c === "#F4F6FA" || c === "#FFD34D" ? "#1A2238" : "#FFFFFF";
      pen.push({ svg: '<path d="M' + bnF(x - 9) + ' ' + bnF(y) + ' L' + bnF(x + 9) + ' ' + bnF(y) + ' L' + bnF(x) + ' ' + bnF(y + 30) + 'Z" fill="' + c + '" stroke="#0A1020" stroke-width=".8"/>' +
          '<text x="' + bnF(x) + '" y="' + bnF(y + 11.5) + '" text-anchor="middle" font-family="Arial Black, Arial, sans-serif" font-weight="900" font-size="8" fill="' + ink + '">' + (i + 1) + '</text>',
        box: [x - 12, y - 2, 24, 36], o: [x, y], cls: "bl-swing", style: "animation-duration:" + bnF(2.8 + rnd() * 1.4) + "s;animation-delay:-" + bnF(rnd() * 3) + "s" });
    }
    const tower = x => '<rect x="' + (x - 2) + '" y="30" width="4" height="150" fill="#0A1020"/>' +
      '<rect x="' + (x - 17) + '" y="14" width="34" height="18" rx="2" fill="#141C34" stroke="#2A3656"/>' +
      [0, 1, 2].map(r => [0, 1, 2, 3, 4].map(k => '<circle cx="' + (x - 12 + k * 6) + '" cy="' + (19 + r * 4.5) + '" r="1.7" fill="#FFF6D8"/>').join("")).join("");
    const defs = '<defs>' +
      bnLin(u + "sky", [[0, "#060C22"], [.7, "#16244C"], [1, "#24366A"]]) +
      bnRad(u + "lamp", [[0, "#FFF6D8", .8], [.4, "#FFE7A8", .25], [1, "#FFE7A8", 0]]) +
      bnLin(u + "shaft", [[0, "#FFF3D0", .28], [1, "#FFF3D0", 0]]) +
      bnLin(u + "flag", [[0, "#FFE58A"], [.5, "#F2B636"], [1, "#B07A12"]], 0, 0, 1, 0) +
      bnLin(u + "wall", [[0, "#101A36"], [1, "#060A16"]]) +
      bnRad(u + "field", [[0, "#3FAE6A", .45], [1, "#3FAE6A", 0]]) +
      '</defs>';
    let crowd = "";
    for(let x = -6; x < 490; x += 7){ crowd += '<circle cx="' + bnF(x + rnd() * 2) + '" cy="' + bnF(132 + rnd() * 3) + '" r="' + bnF(2.6 + rnd()) + '"/>'; }
    const flag = '<path d="M216 88 L264 88 L264 150 L240 138 L216 150Z" fill="url(#' + u + 'flag)" stroke="#7A5310" stroke-width="1.2"/>' +
      '<rect x="212" y="84" width="56" height="5" rx="2" fill="#5A4210"/>' +
      '<path d="M240 98 L242.9 104.2 L249.6 104.9 L244.6 109.4 L246.1 116 L240 112.6 L233.9 116 L235.4 109.4 L230.4 104.9 L237.1 104.2Z" fill="#FFF6D0"/>' +
      '<rect x="222" y="122" width="36" height="2" fill="#FFF6D0" opacity=".7"/>';
    return [
      { svg: defs + '<rect x="-10" y="-10" width="500" height="200" fill="url(#' + u + 'sky)"/><g>' + st.still + '</g>' +
          '<path d="M30 30 L190 180 L120 180Z" fill="url(#' + u + 'shaft)"/><path d="M450 30 L290 180 L360 180Z" fill="url(#' + u + 'shaft)"/>' +
          '<rect x="-10" y="128" width="500" height="62" fill="url(#' + u + 'wall)"/><g fill="#0A1124">' + crowd + '</g>' +
          '<rect x="-10" y="140" width="500" height="3" fill="#FFD34D" opacity=".55"/>' +
          '<ellipse cx="240" cy="180" rx="240" ry="26" fill="url(#' + u + 'field)"/>' +
          tower(46) + tower(434) +
          '<path d="M' + P0[0] + ' ' + P0[1] + ' Q' + PC[0] + ' ' + PC[1] + ' ' + P1[0] + ' ' + P1[1] + '" fill="none" stroke="#C9D3E6" stroke-width="1.2"/>' +
          '<line x1="240" y1="52" x2="240" y2="84" stroke="#C9D3E6" stroke-width="1"/>' },
      { svg: st.a, cls: "bl-tw", style: "animation-duration:3.1s" },
      { svg: '<circle cx="46" cy="23" r="46" fill="url(#' + u + 'lamp)"/>', box: [0, -23, 92, 92], o: [46, 23], cls: "bl-glow", style: "animation-duration:2.6s" },
      { svg: '<circle cx="434" cy="23" r="46" fill="url(#' + u + 'lamp)"/>', box: [388, -23, 92, 92], o: [434, 23], cls: "bl-glow", style: "animation-duration:3.2s;animation-delay:-1.2s" },
      { svg: flag, box: [208, 80, 64, 76], o: [240, 84], cls: "bl-swing", style: "animation-duration:4.2s" }
    ].concat(pen);
  } }
};
