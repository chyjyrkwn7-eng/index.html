"""Build 332: in the Fire Code class the leaderboard, Virtual Room and Chat say they are for the
Police Academy class instead of asking for a connection.   Run:  python3 tools/check-b332.py"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b330.py")).read().split("want = sys.argv")[0]
g = {"__file__": os.path.join(HERE, "check-b330.py"), "__name__": "b330"}; exec(src, g)
from playwright.sync_api import sync_playwright
OWNER = "xph5b57jbp5a"
READ = """async (cls)=>{
  const W = ms => new Promise(r => setTimeout(r, ms));
  store.leaderboardOptIn = true; showRankings(); await W(3500);
  const lb = (document.querySelector('#stage .info-note') || {}).textContent || '';
  return { cls: window.NOVA_CLASS, fb: !!fbDb, lb, scr: (document.querySelector('#stage > *')||{}).className, txt: document.getElementById('stage').innerText.slice(0,200) }; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    # the owner's account, in the Fire Code class
    g["seed"].__globals__["json"] = json
    orig = g["seed"]
    g["seed"] = lambda pid="pubtest00330": orig(OWNER)
    g["page_for"].__globals__["seed"] = g["seed"]
    ctx, page = g["page_for"](br, "promax")
    page.evaluate("()=>localStorage.setItem('class26e.activeclass','ifc')"); page.reload(); page.wait_for_timeout(3500)
    page.evaluate("document.getElementById('splashscreen')?.remove()")
    r = page.evaluate(READ, "ifc")
    g["chk"]("this device is in the Fire Code class with no cloud", r["cls"] == "ifc" and r["fb"] is False, r)
    g["chk"]("the leaderboard says it is for the Police Academy class, not that it needs a connection",
             "Police Academy" in r["lb"] and "connection" not in r["lb"], r["lb"])
    ctx.close(); br.close()
sys.exit(0 if g["ok"] else 1)
