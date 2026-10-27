"""Build 337: no cracked planet - not on Home (any rank, Supernova included), not in the rank-up scenes, not in Nova's story.
Run:  python3 tools/check-b337.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b330.py")).read().split("want = sys.argv")[0]
g = {"__file__": os.path.join(HERE, "check-b330.py"), "__name__": "b330"}; exec(src, g)
from playwright.sync_api import sync_playwright
HOME = """async ()=>{ const W = ms => new Promise(r => setTimeout(r, ms)); const out = [];
  for(const sn of [false, true]){ store.supernovaAchieved = sn; showHome(); await W(700);
    const h = document.querySelector('.panel.home .cosmic-hero-wrap');
    out.push({ sn, hero: !!h, bad: h ? h.querySelectorAll('.cosmic-scar, [class*="csc-"], .sn-fracture').length : -1, scarred: h ? h.classList.contains('is-scarred') : null,
      orange: h ? h.querySelectorAll('.cosmic-orbit-ring-supernova').length : 0 }); }
  store.supernovaAchieved = false; showHome();
  const gone = ['cosmicScarArt', 'heroCrackStage', 'crackFormArm', 'decorateSupernovaHero', 'addRingDebris', 'scarPassEffects', 'buildNovaWreck', 'novaStrainPlanet']
    .filter(n => { try{ return typeof eval(n) !== 'undefined'; }catch(e){ return false; } });
  const texts = [];
  try{ NOVA_RANK_HEAD.forEach(f => texts.push(f('Casey'))); }catch(e){}
  try{ Object.values(NOVA_RANK_BEATS).forEach(a => texts.push(...a)); }catch(e){}
  try{ Object.values(RANK_LORE).forEach(t => texts.push(t)); }catch(e){}
  try{ [false, true].forEach(ex => novaIntroLines({ existing: ex }).forEach(l => texts.push(typeof l.text === 'function' ? l.text() : l.text))); }catch(e){}
  try{ ['why is my planet cracking', 'what are badges', 'tell me about the planet', 'what do i get', 'flares', 'what is a badge'].forEach(q => texts.push(novaReplyFor(q))); }catch(e){}
  return { out, gone, hits: texts.filter(t => /crack|strain|hold it together|holding it/i.test(String(t))), n: texts.length }; }"""
SCENE = """async ()=>{ const W = ms => new Promise(r => setTimeout(r, ms)); theme.reduceMotion = true; applyTheme && applyTheme();
  const out = []; for(const [k, from] of [['veteran', 'ranger'], ['titan', 'elite']]){ let fin = false;
    const o = { from, onDone: () => { fin = true; } }; if(k === 'titan') playSupernovaCutscene(o); else playTierCutscene(k, o);
    await W(700); const mid = document.querySelectorAll('.cosmic-scar, .sn-fracture, [class*="csc-"]').length;
    for(let t = 0; t < 120 && !fin; t++) await W(100);
    out.push({ k, fin, mid }); document.querySelectorAll('#supernova-cutscene, .tier-cutscene').forEach(n => n.remove()); }
  return out; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    ctx, page = g["page_for"](br, "promax")
    errs = []; page.on("pageerror", lambda e: errs.append(str(e)[:160]))
    for _ in range(3):
        page.evaluate("()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }"); page.wait_for_timeout(400)
    r = page.evaluate(HOME)
    g["chk"]("Home's planet carries no crack, scar, debris or soot - on any account, Supernova included", all(x["hero"] and x["bad"] == 0 and not x["scarred"] for x in r["out"]), r["out"])
    g["chk"]("a Supernova account's Home still has its orange rings", r["out"][1]["orange"] > 0, r["out"][1])
    g["chk"]("the crack, scar, wreck and strain-planet code is gone", not r["gone"], r["gone"])
    g["chk"]("no line of Nova's story, his rank messages, the rank lore or his chat says a planet cracks (%d texts read)" % r["n"], r["n"] > 30 and not r["hits"], r["hits"][:3])
    s = page.evaluate(SCENE)
    g["chk"]("the Gold and Supernova rank-up scenes play through (Reduce motion) with nothing cracked in them", all(x["fin"] and x["mid"] == 0 for x in s), s)
    g["chk"]("no page errors", not errs, errs[:3])
    ctx.close(); br.close()
sys.exit(0 if g["ok"] else 1)
