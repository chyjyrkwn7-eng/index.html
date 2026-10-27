"""Build 331: a forced update never lands inside the rank-up journey.
Run:  python3 tools/check-b331.py"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b330.py")).read().split("want = sys.argv")[0]
g = {"__file__": os.path.join(HERE, "check-b330.py"), "__name__": "b330"}; exec(src, g)
from playwright.sync_api import sync_playwright
RUN = """async ()=>{
  const W = ms => new Promise(r => setTimeout(r, ms));
  store.onboardingComplete = true;
  const held = TIER_ORDER_FULL.indexOf(rankOf(store)); store.rankUpShown = held; store.rankUpFrom = { r: held - 1, b: 0, p: 0 };
  store.rankMapSeen = held - 1; store.rankMapFx244 = false; saveStore();
  theme.reduceMotion = true; applyTheme && applyTheme();
  showProfile(); const open = {}; let seen = 0;
  for(let t = 0; t < 600; t++){
    await W(100);
    if(rankUpScene){ seen++; open[rankUpScene.phase] = forcedUpdateBlocked(); }
    else if(t > 20) break;
  }
  await W(1500); showHome(); await W(1500);
  return { seen, open, after: forcedUpdateBlocked() }; }"""
ok = True
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    ctx, page = g["page_for"](br, "promax")
    r = page.evaluate(RUN)
    phases = sorted(r["open"])
    g["chk"]("the journey ran through several phases", len(phases) >= 5, phases)
    g["chk"]("a forced update is held in every phase of the rank-up journey", all(r["open"].values()), r["open"])
    g["chk"]("and it is free again on Home once the journey is over", r["after"] is False, r["after"])
    ctx.close(); br.close()
sys.exit(0 if g["ok"] else 1)
