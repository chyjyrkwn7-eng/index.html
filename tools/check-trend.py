import functools, http.server, os, re, socket, sys, threading
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
AGAINST = sys.argv[sys.argv.index("--against")+1] if "--against" in sys.argv else None
def ck(n,c,d=""):
    global ok
    print(" ","PASS" if c else "FAIL",n,("-> "+str(d)) if d else "")
    if not c: ok=False
with sync_playwright() as pw:
    br=pw.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome",args=["--no-sandbox"])
    ctx=br.new_context(viewport={"width":440,"height":956})
    ctx.add_init_script(FAKE)
    ctx.add_init_script("try{localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');}catch(e){}")
    pg=ctx.new_page()
    if AGAINST:
        _html=open(AGAINST,encoding="utf-8").read()
        pg.route("**/index.html",lambda r,q=None:r.fulfill(status=200,content_type="text/html",body=_html))
    pg.goto("http://127.0.0.1:%d/index.html"%port); pg.wait_for_timeout(2500)
    pg.evaluate("""()=>{document.getElementById('splashscreen')?.remove(); __useFake();
      store.onboardingComplete=true; store.firstName='Madison'; store.publicId='me01'; store.tourRev=99;
      ['seenFirstResultsTour','seenModeSelectTour','seenProfileTour','seenRewardsTour','seenSettingsTour',
       'seenUnitOptionsTour','seenUnitSelectTour','seenMainMenuTour'].forEach(k=>store[k]=true);
      syncCode='AAAA-1111'; store.leaderboardOptIn=true; showHome();}""")
    pg.wait_for_timeout(300)
    r = pg.evaluate("""()=>{
      const mk=(pub,name,wp)=>({pub,firstName:name,avatarChar:'ninja',weekPoints:wp,week:weekKeyNow(),
                                level:5,badges:1,hundos:1,correct:wp});
      const board=RANKING_BOARDS.find(b=>b.key==='week');
      const KEY = (typeof LB_TREND2_KEY !== 'undefined') ? LB_TREND2_KEY : LB_TREND_KEY;
      /* Age whatever is stored so the next render treats it as the
         earlier snapshot, under either the old (curDay) or new (curAt) scheme. */
      const age=()=>{ const st=JSON.parse(localStorage.getItem(KEY)||'{}'); st.curDay='1999-1-1'; st.curAt=1;
                      localStorage.setItem(KEY, JSON.stringify(st)); };
      const read=rows=>[...rows.querySelectorAll('.rank-row')].filter(r=>r.querySelector('.rank-name')).map(r=>{
        const t=r.querySelector('.rank-trend'); const n=t?Number((t.querySelector('.rank-trend-n')||t).textContent.replace(/\D/g,''))||0:0;
        return {name:r.querySelector('.rank-name').textContent, t:t?t.textContent:'',
                up:!!r.querySelector('.rank-trend.is-up'), down:!!r.querySelector('.rank-trend.is-down'),
                signed: t ? (t.classList.contains('is-up')?n:-n) : 0};});
      /* Scenario 1: Ann, Bo, Cy; then Cy overtakes both. */
      localStorage.removeItem(KEY);
      let rows=document.createElement('div');
      renderRankingRows(rows,[mk('a','Ann',90),mk('b','Bo',80),mk('c','Cy',70)],board,{});
      const noArrowsDay1 = rows.querySelectorAll('.rank-trend').length;
      age();
      renderRankingRows(rows,[mk('c','Cy',99),mk('a','Ann',90),mk('b','Bo',80)],board,{});
      const marks=read(rows);
      renderRankingRows(rows,[mk('c','Cy',99),mk('a','Ann',90),mk('b','Bo',80)],board,{});
      const stable=read(rows).map(x=>x.t);
      /* Scenario 2: nobody moved relative to anybody, but a newcomer
         joined at the top. Nobody went down under anyone, so nobody
         may be told they did - this is the "why is everyone +1" report. */
      localStorage.removeItem(KEY);
      rows=document.createElement('div');
      renderRankingRows(rows,[mk('a','Ann',90),mk('b','Bo',80),mk('c','Cy',70)],board,{});
      age();
      renderRankingRows(rows,[mk('d','Dee',120),mk('a','Ann',91),mk('b','Bo',81),mk('c','Cy',71)],board,{});
      const joiner=read(rows);
      /* Scenario 3: someone below everyone leaves. Same answer. */
      localStorage.removeItem(KEY);
      rows=document.createElement('div');
      renderRankingRows(rows,[mk('a','Ann',90),mk('b','Bo',80),mk('c','Cy',70),mk('e','Ed',10)],board,{});
      age();
      renderRankingRows(rows,[mk('a','Ann',90),mk('b','Bo',80),mk('c','Cy',70)],board,{});
      const leaver=read(rows);
      /* Every board shows arrows, not just some of them. */
      const perBoard={};
      RANKING_BOARDS.forEach(b=>{
        localStorage.removeItem(KEY);
        const rr=document.createElement('div');
        const A=[{pub:'a',firstName:'Ann',avatarChar:'ninja',weekPoints:90,week:weekKeyNow(),level:30,badges:5,hundos:40,correct:900},
                 {pub:'b',firstName:'Bo',avatarChar:'ninja',weekPoints:80,week:weekKeyNow(),level:20,badges:3,hundos:30,correct:800}];
        renderRankingRows(rr,A,b,{}); age();
        const B=[Object.assign({},A[1],{weekPoints:99,level:40,badges:9,hundos:60,correct:1200}),A[0]];
        renderRankingRows(rr,B,b,{});
        perBoard[b.key]=rr.querySelectorAll('.rank-trend').length;
      });
      return {noArrowsDay1, marks, stable, joiner, leaver, perBoard};}""")
    print("\n  leaderboard placement trend")
    ck("no arrows on the very first look", r["noArrowsDay1"]==0, r["noArrowsDay1"])
    m = {x["name"]: x for x in r["marks"]}
    ck("Cy moved up two and says so", m["Cy"]["up"] and "2" in m["Cy"]["t"], m["Cy"])
    ck("Ann moved down one", m["Ann"]["down"] and "1" in m["Ann"]["t"], m["Ann"])
    ck("Bo moved down one", m["Bo"]["down"] and "1" in m["Bo"]["t"], m["Bo"])
    ck("the arrows balance: every place gained is a place somebody lost",
       sum(x["signed"] for x in r["marks"])==0, [x["signed"] for x in r["marks"]])
    ck("re-rendering inside the same window does not change the arrows",
       r["stable"]==[x["t"] for x in r["marks"]], r["stable"])
    ck("a newcomer joining above everybody puts an arrow on nobody",
       all(not x["t"] for x in r["joiner"]), [(x["name"],x["t"]) for x in r["joiner"]])
    ck("somebody leaving from below puts an arrow on nobody",
       all(not x["t"] for x in r["leaver"]), [(x["name"],x["t"]) for x in r["leaver"]])
    ck("every board shows movement, not only some of them",
       all(v==2 for v in r["perBoard"].values()) and len(r["perBoard"])>=3, r["perBoard"])
    br.close()
srv.shutdown()
print("\n" + ("ALL PASS" if ok else "FAILED"))
