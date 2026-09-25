import functools, http.server, os, re, socket, threading
from playwright.sync_api import sync_playwright
ROOT="/home/user/index.html"
_VR=open(os.path.join(ROOT,"tools","check-vroom.py"),encoding="utf-8").read()
FAKE=re.search(r'FAKE_FIRESTORE = """(.*?)"""',_VR,re.S).group(1)
s=socket.socket(); s.bind(("127.0.0.1",0)); port=s.getsockname()[1]; s.close()
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
srv=http.server.ThreadingHTTPServer(("127.0.0.1",port),functools.partial(Q,directory=ROOT))
threading.Thread(target=srv.serve_forever,daemon=True).start()
ok=True
def ck(n,c,d=""):
    global ok
    print(" ","PASS" if c else "FAIL",n,("-> "+str(d)) if d else "")
    if not c: ok=False
with sync_playwright() as pw:
    br=pw.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome",args=["--no-sandbox"])
    ctx=br.new_context(viewport={"width":440,"height":956})
    ctx.add_init_script(FAKE)
    ctx.add_init_script("try{localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');}catch(e){}")
    pg=ctx.new_page(); pg.goto("http://127.0.0.1:%d/index.html"%port); pg.wait_for_timeout(2500)
    pg.evaluate("""()=>{document.getElementById('splashscreen')?.remove(); __useFake();
      store.onboardingComplete=true; store.firstName='Madison'; store.publicId='me01'; store.tourRev=99;
      ['seenFirstResultsTour','seenModeSelectTour','seenProfileTour','seenRewardsTour','seenSettingsTour',
       'seenUnitOptionsTour','seenUnitSelectTour','seenMainMenuTour'].forEach(k=>store[k]=true);
      syncCode='AAAA-1111'; store.leaderboardOptIn=true; showHome();}""")
    pg.wait_for_timeout(300)
    r = pg.evaluate("""()=>{
      const mk=(pub,name,wp)=>({pub,firstName:name,avatarChar:'ninja',weekPoints:wp,week:weekKeyNow(),
                                level:5,badges:1,hundos:1,correct:wp});
      const rows=document.createElement('div');
      const board=RANKING_BOARDS.find(b=>b.key==='week');
      /* Day one: Ann 1st, Bo 2nd, Cy 3rd. */
      localStorage.removeItem(LB_TREND_KEY);
      renderRankingRows(rows,[mk('a','Ann',90),mk('b','Bo',80),mk('c','Cy',70)],board,{});
      const firstDay = JSON.parse(localStorage.getItem(LB_TREND_KEY));
      const noArrowsDay1 = rows.querySelectorAll('.rank-trend').length;
      /* Force the stored day to be yesterday, then re-render with Cy on top. */
      firstDay.curDay = '1999-1-1';
      localStorage.setItem(LB_TREND_KEY, JSON.stringify(firstDay));
      renderRankingRows(rows,[mk('c','Cy',99),mk('a','Ann',90),mk('b','Bo',80)],board,{});
      const marks=[...rows.querySelectorAll('.rank-row')].map(r=>({
        name:(r.querySelector('.rank-name')||{}).textContent,
        t:(r.querySelector('.rank-trend')||{}).textContent||'',
        up:!!r.querySelector('.rank-trend.is-up'),
        down:!!r.querySelector('.rank-trend.is-down')}));
      /* And a third render on the SAME day must not invent new arrows. */
      renderRankingRows(rows,[mk('c','Cy',99),mk('a','Ann',90),mk('b','Bo',80)],board,{});
      const stable=[...rows.querySelectorAll('.rank-row')].map(r=>(r.querySelector('.rank-trend')||{}).textContent||'');
      return {noArrowsDay1, marks, stable};}""")
    print("\n  leaderboard placement trend")
    ck("no arrows on the very first day", r["noArrowsDay1"]==0, r["noArrowsDay1"])
    m = {x["name"]: x for x in r["marks"]}
    ck("Cy moved up two and says so", m["Cy"]["up"] and "2" in m["Cy"]["t"], m["Cy"])
    ck("Ann moved down one", m["Ann"]["down"] and "1" in m["Ann"]["t"], m["Ann"])
    ck("Bo moved down one", m["Bo"]["down"] and "1" in m["Bo"]["t"], m["Bo"])
    ck("re-rendering the same day does not change the arrows",
       r["stable"]==[x["t"] for x in r["marks"]], r["stable"])
    br.close()
srv.shutdown()
print("\n" + ("ALL PASS" if ok else "FAILED"))
