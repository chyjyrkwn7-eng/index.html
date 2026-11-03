"""Build 383, Madison after 382 went live:
  1. "The save your sync code pop up, don't do that for the existing accounts."
  2. "the weekly news popup. I don't like how it pops up forced like that ... that only pops up if you
     select leaderboard that week"
  3. "The leaderboard, why is the top 3 disconnected from the rest, fix that"
Checks: an existing account that never saved its code sees no card on Home (the sign-up card is
check-b382-savecode's "signup"); the week's recap does not play on Home, does play once the Leaderboard
is opened, and not a second time that week; the top three and the rest are one grouped card (no gap,
no corners between rows, one card's left and right edges).
Run:  python3 tools/check-b383-feedback.py   (--against OLD/index.html must FAIL)"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b382-savecode.py")).read().split("\nwith sync_playwright() as pw:")[0]
g = {"__file__": os.path.join(HERE, "check-b382-savecode.py"), "__name__": "b383"}
exec(src, g)
from playwright.sync_api import sync_playwright
fails = g["fails"] = []
ck = g["ck"]
def recap_up(pg): return pg.evaluate("()=>!!document.querySelector('#nova-intro.is-weekrecap')")
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])

    print("\n1. an existing account that never saved its code")
    errs = []
    st = g["store"]()
    ctx, pg = g["open_page"](br, g["init_account"]("TEST-3831", st), errs=errs)
    g["connect"](pg, "TEST-3831", st)
    ck("no save-your-code card on Home after the server copy is read (9s)", not g["wait_card"](pg, 9000))
    pg.evaluate("()=>{ showHome(); setTimeout(checkSaveCodeReminder, 50); }"); pg.wait_for_timeout(2500)
    ck("nor when Home is shown again", not g["card_up"](pg))
    pg.evaluate("()=>showAppearance({page:'sync'})"); pg.wait_for_timeout(900)
    ck("Settings > Sync still has the code and Save it", pg.evaluate("""()=>!!document.querySelector('#stage .sync-code-row') &&
        [...document.querySelectorAll('#stage .settings-row')].some(r=>/Save it/.test(r.textContent))"""))
    ck("no page errors", not errs, errs[:2])
    ctx.close()

    print("\n2. the week's recap: on the Leaderboard, not Home")
    errs = []
    st = g["store"](leaderboardOptIn=True); st.pop("novaHeard", None)   # last week's recap NOT yet heard
    ctx, pg = g["open_page"](br, g["init_account"]("TEST-3832", st), errs=errs)
    pg.evaluate("()=>{ weekRecapDayOk = () => true; }")   # any day of the week this runs on
    g["connect"](pg, "TEST-3832", st)
    # a class that earned points last week (a real board always has rows; an empty one never recaps)
    pg.evaluate("""()=>{ const lw=lastWeekKey(), wk=weekKeyNow();
      const rows=['Lee','Pat','Alex','Jose'].map((n,i)=>({ id:'pub'+(i+20), d:{ firstName:n, avatarChar:'ghost', level:40-i, badges:5, hundos:9, correct:900,
        week:wk, weekPoints:50, prevWeek:lw, prevWeekPoints:900-i*150 } }));
      const real = onSnapshotResilient;
      onSnapshotResilient = function(ref, onNext){ if(ref && ref.where === undefined && !ref.get) return real(ref, onNext);
        setTimeout(()=>{ try{ onNext({ metadata:{fromCache:false}, forEach(cb){ rows.forEach(r=>cb({ id:r.id, data:()=>r.d })); }, docs:[] }); }catch(e){} }, 30); return function(){}; };
      fetchBoardForInvites = function(){ leaderboardRows = rows.map(r=>Object.assign({pub:r.id}, r.d)); leaderboardRowsFromServer = true; }; }""")
    pg.evaluate("()=>{ try{ showHome(); }catch(e){} }")
    t = 0; home_recap = False
    while t < 9000:
        if recap_up(pg): home_recap = True; break
        pg.wait_for_timeout(300); t += 300
    ck("Home: nothing plays by itself (9s)", not home_recap)
    if home_recap: pg.evaluate("()=>document.getElementById('nova-intro').__nova.close()"); pg.wait_for_timeout(600)
    pg.evaluate("()=>{ document.getElementById('bottomtab-rewards')?.click(); }")
    t = 0; board_recap = False
    while t < 9000:
        if recap_up(pg): board_recap = True; break
        pg.wait_for_timeout(300); t += 300
    ck("the Leaderboard tab: the week's recap plays (within %.1fs)" % (t / 1000), board_recap and not home_recap)
    if board_recap:
        pg.evaluate("()=>document.getElementById('nova-intro').__nova.close()"); pg.wait_for_timeout(800)
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(900)
    pg.evaluate("()=>{ document.getElementById('bottomtab-rewards')?.click(); }"); pg.wait_for_timeout(5000)
    ck("opening the Leaderboard again that week: it does not play again", not recap_up(pg))
    ck("no page errors", not errs, errs[:2])
    ctx.close()

    print("\n3. the top three and the rest: one grouped card")
    for (w, h, dev) in [(440, 956, "phone"), (834, 1194, "iPad")]:
        errs = []
        st = g["store"](leaderboardOptIn=True, publicId="pub00")
        ctx, pg = g["open_page"](br, g["init_account"]("TEST-3833", st), w=w, h=h, errs=errs)
        g["connect"](pg, "TEST-3833", st)
        pg.evaluate("""()=>{ weekRecapDayOk = () => false;
          const names=['Lee','Pat','Alex','Jose','Devonte','Brooke','Tara','Kim','Ray'];
          const rows = names.map((n,i)=>({ id:'pub'+(i+10), d:{ firstName:n, avatarChar:'ghost', level:70-i*6, badges:15-i, hundos:90-i*8, correct:3000-i*200, xp:90000-i*8000 } }));
          onSnapshotResilient = function(ref, onNext){ setTimeout(()=>{ try{ onNext({ metadata:{fromCache:false}, forEach(cb){ rows.forEach(r=>cb({ id:r.id, data:()=>r.d })); }, docs:[] }); }catch(e){} }, 30); return function(){}; };
          showRankings('overall'); }""")
        pg.wait_for_timeout(2500)
        r = pg.evaluate("""()=>{ const rows=[...document.querySelectorAll('#stage .rank-rows > .rank-row:not(.rank-row-head)')];
          const b=rows.slice(0,6).map(e=>{ const q=e.getBoundingClientRect(), c=getComputedStyle(e);
            return {top:Math.round(q.top), bot:Math.round(q.bottom), l:Math.round(q.left), r:Math.round(q.right),
                    tl:parseFloat(c.borderTopLeftRadius), bl:parseFloat(c.borderBottomLeftRadius), pod:/rank-podium-/.test(e.className)}; });
          return {n:rows.length, b}; }""")
        b = r["b"]
        ck("%s: the board has its podium and more under it (%d rows)" % (dev, r["n"]), r["n"] >= 6 and b[0]["pod"] and b[2]["pod"] and not b[3]["pod"], r)
        if r["n"] >= 6:
            gaps = [b[i + 1]["top"] - b[i]["bot"] for i in range(5)]
            ck("%s: no gap between any two rows, first place to sixth (%s)" % (dev, gaps), all(abs(x) <= 1 for x in gaps), gaps)
            ck("%s: one card's edges - every row the same left and right" % dev, len({x["l"] for x in b}) == 1 and len({x["r"] for x in b}) == 1, b)
            ck("%s: rounded at the top of first place only - no corners at 1st/2nd/3rd's bottoms or 4th's top" % dev,
               b[0]["tl"] > 4 and all(x["bl"] < 1 for x in b[:5]) and all(x["tl"] < 1 for x in b[1:6]), b)
        ck("%s: no page errors" % dev, not errs, errs[:2])
        ctx.close()
    br.close()
print("\n%s  (%d failure(s))" % ("ALL PASS" if not fails else "FAILED: " + ", ".join(fails[:6]), len(fails)))
sys.exit(1 if fails else 0)
