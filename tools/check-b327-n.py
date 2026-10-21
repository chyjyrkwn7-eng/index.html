#!/usr/bin/env python3
"""Build 327 unlock audit: a Virtual Room match recorded live is not
backfilled again, and "this card was shown" is merged across devices.
Usage: check-b327-n.py [--against OTHER.html]"""
import sys, os, asyncio
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC=os.path.abspath(sys.argv[sys.argv.index("--against")+1]) if "--against" in sys.argv else os.path.join(ROOT,"index.html")
JS=r"""async () => {
  const out = {};
  store.onboardingComplete = true;
  const me = publicIdOf();
  store.vrCounted = ["ROOM1@1700000000000"]; store.vrTop3Rooms = ["ROOM1@1700000000000"];
  store.vrMatches = 1; store.vrWins = 1; store.vrTop3 = 1;
  store.vrRetroDone = false; store.vrTop3RetroDone = false;
  const parts = {}; parts[me] = {finished:true, xp:500, correct:10};
  ["a","b","c"].forEach((k,i)=>parts[k]={finished:true,xp:100*i,correct:i});
  const docs = [{id:"ROOM1", data:()=>({status:"finished", participants:parts})}];
  window.fbDb = { collection: () => ({ get: () => Promise.resolve({ forEach: f => docs.forEach(f) }) }) };
  try{ fbDb = window.fbDb; }catch(e){}
  seedVroomHistory(); seedVroomTop3();
  await new Promise(r=>setTimeout(r,200));
  out.vr = [store.vrMatches, store.vrWins, store.vrTop3];
  const a = JSON.parse(JSON.stringify(store)), b = JSON.parse(JSON.stringify(store));
  a.unlocksShown = {chars:["zeus"], banners:["sakura"], fx:[]};
  b.unlocksShown = {chars:["koi"], banners:[], fx:["fireworks"]};
  a.vrRetroDone = false; b.vrRetroDone = true;
  mergeSameAccount(a, b);
  out.u = a.unlocksShown; out.retro = a.vrRetroDone;
  return out;
}"""
async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
    pg = await br.new_page()
    await pg.goto("file://"+SRC); await pg.wait_for_timeout(3000)
    r = await pg.evaluate(JS)
    fails = 0
    def chk(name, ok, got):
      nonlocal fails
      print(("  PASS " if ok else "  FAIL ") + name + "  -> " + str(got)); fails += 0 if ok else 1
    chk("a room raced live is not counted again by the backfill", r["vr"] == [1, 1, 1], r["vr"])
    chk("unlock cards shown on either device stay shown", r["u"]["chars"] == ["zeus", "koi"] and r["u"]["fx"] == ["fireworks"], r["u"])
    chk("the backfill's done flag merges", r["retro"] is True, r["retro"])
    print("\nALL PASS" if not fails else "\n%d failure(s)" % fails)
    if fails: await br.close(); sys.exit(1)
    await br.close()
asyncio.run(main())

