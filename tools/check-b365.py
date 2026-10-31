"""Build 365: every tap's screen follows - tapping down the line (Home, Profile, Leaderboard, Calendar) 150ms apart builds all four and
the last is up soon after the last tap; a bare Leaderboard row is a soft disc, not an empty ring; the speed test reports a drag run with
effect-off variants ([d:base] ... [d:nolens]).
Run:  python3 tools/check-b365.py   (add --against old.html: copy it over index.html first, as the other checks do)"""
import os, sys, re
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(HERE + "/check-b330.py").read().split("want = sys.argv")[0]
g = {"__file__": HERE + "/check-b330.py", "__name__": "b330"}; exec(src, g)
from playwright.sync_api import sync_playwright
chk = g["chk"]
CLEAR = "()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }"
FILL = """()=>{ const n=AVATAR_CHARACTERS.length; const rows=[]; for(let i=0;i<42;i++){ rows.push(Object.assign({pub:'zz'+i, firstName:'Cadet'+i, avatarChar:AVATAR_CHARACTERS[i%n].id}, boardNumbersOf(store), {weekPoints:1000-i*17, hundos:60-i, correct:5000-i*70, level:40-(i>>1), badges:20-(i>>2)})); } leaderboardRows = rows; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    ctx, pg = g["page_for"](br, "promax")
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    pg.evaluate(FILL); pg.wait_for_timeout(2500)
    r = pg.evaluate("""async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const bar=document.getElementById('bottomtabs'); const SEL={profile:'.screen-profile',rewards:'.screen-rankings',calendar:'.screen-calendar-tab'};
      const tap=async(d)=>{ const el=document.getElementById('bottomtab-'+d); const b=el.getBoundingClientRect(); const x=b.left+b.width/2,y=b.top+b.height/2;
        const mk=t=>new PointerEvent(t,{bubbles:true,cancelable:true,pointerType:'touch',pointerId:84,isPrimary:true,clientX:x,clientY:y});
        el.dispatchEvent(mk('pointerdown')); await wait(35); el.dispatchEvent(mk('pointerup')); el.dispatchEvent(new MouseEvent('click',{bubbles:true,clientX:x,clientY:y})); };
      const b0=bar._navBuilds||0; const seen=[]; const t0=performance.now();
      const poll=setInterval(()=>{ for(const k in SEL){ if(!seen.some(s=>s[0]===k) && document.querySelector(SEL[k])) seen.push([k,Math.round(performance.now()-t0)]); } },5);
      for(const d of ['profile','rewards','calendar']){ await tap(d); await wait(115); }
      const tLast=performance.now()-t0; await wait(900); clearInterval(poll);
      return { builds:(bar._navBuilds||0)-b0, seen, tLast:Math.round(tLast) }; }""")
    last = [s for s in r["seen"] if s[0] == "calendar"]
    chk("tapping down the line 150ms apart builds all three screens (%s)" % (r,), r["builds"] == 3 and len(r["seen"]) == 3, r)
    chk("and the last is up within 300ms of the last tap (%s)" % (last,), bool(last) and last[0][1] - r["tLast"] <= 300, r)
    # bare rows are soft discs
    pg.evaluate("()=>showRankings()"); pg.wait_for_timeout(120)
    d = pg.evaluate("""()=>{ const av=document.querySelector('.rank-rows .rank-row[data-lazy-art] .rank-avatar-wrap[data-lazy-av] .rank-avatar'), mk=document.querySelector('.rank-rows .rank-row[data-lazy-art] .rank-mark.is-lazy');
      return { av: av ? getComputedStyle(av).backgroundImage.slice(0,45) : null, mk: mk ? getComputedStyle(mk).backgroundImage.slice(0,45) : null }; }""")
    chk("a bare row's character and flare frames are soft discs (%s)" % (d,), d["av"] and d["av"].startswith("radial-gradient(circle at 50% 40%") and d["mk"] and d["mk"].startswith("radial-gradient(circle at 50% 45%"), d)
    text = pg.evaluate("async()=>{ const x=await runLagTest(()=>{}); return x.text; }")
    ds = [p for p in text.split(" | ") if p.startswith("[d:")]
    names = [p[3:p.index("]")] for p in ds]
    chk("the speed test drags with variants (%s)" % (names,), names == ["base", "noblend", "nomask", "noshadow", "nobarblur", "nolens"] and all(len(re.findall(r"n\d+ w\d+ s\d+", p)) >= 2 for p in ds), text[-400:])
    br.close()
sys.exit(0 if g["ok"] else 1)
