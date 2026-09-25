#!/usr/bin/env python3
"""The Profile card, the Friends screen and the calendar's list view.

Every check in here was written against the build it failed on - build
188 - which is the only thing that makes a green run mean anything:

    python3 tools/check-profilecard.py --against old-index.html

Three devices rather than the whole matrix, because none of these is a
layout decision that varies by device: they are "is this fix in effect",
and the SE is in the list because it is the one width where the two stat
plates and the two code groups have no slack to hide a mistake in.
"""
import argparse, functools, http.server, os, re, shutil, socket, tempfile, threading, json
from playwright.sync_api import sync_playwright
ROOT="/home/user/index.html"
ap=argparse.ArgumentParser()
ap.add_argument("--against", help="run the same checks against another index.html; they are SUPPOSED to fail there")
A=ap.parse_args()
SERVE=ROOT
if A.against:
    other=A.against if os.path.isabs(A.against) else os.path.join(ROOT, A.against)
    SERVE=tempfile.mkdtemp(prefix="profilecard-")
    shutil.copy(other, os.path.join(SERVE,"index.html"))
    for extra in ("version.json",):
        p=os.path.join(ROOT,extra)
        if os.path.exists(p): shutil.copy(p, SERVE)
    print("against:", other)
_VR=open(os.path.join(ROOT,"tools","check-vroom.py"),encoding="utf-8").read()
FAKE=re.search(r'FAKE_FIRESTORE = """(.*?)"""',_VR,re.S).group(1)
s=socket.socket(); s.bind(("127.0.0.1",0)); port=s.getsockname()[1]; s.close()
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
srv=http.server.ThreadingHTTPServer(("127.0.0.1",port),functools.partial(Q,directory=SERVE))
threading.Thread(target=srv.serve_forever,daemon=True).start()
ok=True
def ck(n,c,d=""):
    global ok
    print(" ","PASS" if c else "FAIL",n,("-> "+str(d)) if d else "")
    if not c: ok=False
SEED="""()=>{document.getElementById('splashscreen')?.remove(); __useFake();
  store.onboardingComplete=true; store.firstName='Madison'; store.publicId='me01'; store.tourRev=99;
  store.avatarChar='wizard'; store.lifetime={points:4200}; store.points=4200;
  ['seenFirstResultsTour','seenModeSelectTour','seenProfileTour','seenRewardsTour','seenSettingsTour',
   'seenUnitOptionsTour','seenUnitSelectTour','seenMainMenuTour','seenFriendsTour','seenCalendarTour'].forEach(k=>store[k]=true);
  syncCode='AAAA-1111'; store.leaderboardOptIn=true; showHome();}"""
with sync_playwright() as pw:
    br=pw.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome",args=["--no-sandbox"])
    for label,vp in [("phone 440x956",{"width":440,"height":956}),("ipad 834x1194",{"width":834,"height":1194}),("SE 320x568",{"width":320,"height":568})]:
        print("==",label)
        ctx=br.new_context(viewport=vp)
        ctx.add_init_script(FAKE)
        ctx.add_init_script("try{localStorage.setItem('class26e.frame.ok','go-live-1');}catch(e){}")
        pg=ctx.new_page()
        errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto("http://127.0.0.1:%d/index.html"%port); pg.wait_for_timeout(2200)
        pg.evaluate(SEED); pg.wait_for_timeout(200)
        # ---- Profile card ----
        pg.evaluate("()=>showProfile('identity')"); pg.wait_for_timeout(700)
        r=pg.evaluate("""()=>{
          const av=document.querySelector('.profile-hero-avatar');
          const cs=av?getComputedStyle(av,'::before'):null;
          const svg=av?av.querySelector('svg'):null;
          const plates=[...document.querySelectorAll('.profile-statplate')];
          const tr=document.querySelector('.profile-xpbar');
          const fill=tr?tr.querySelector('.xpbar-fill'):null;
          const pct=document.querySelector('.profile-xp-pct');
          const panel=document.querySelector('.panel');
          return {
            hasGlow: av?av.classList.contains('has-glow'):null,
            charGlow: av?av.style.getPropertyValue('--char-glow'):null,
            beforeW: cs?cs.width:null,
            svgFilter: svg?getComputedStyle(svg).filter.slice(0,40):null,
            plates: plates.length,
            plateRects: plates.map(p=>{const b=p.getBoundingClientRect();return [Math.round(b.width),Math.round(b.height)];}),
            plateBg: plates[0]?getComputedStyle(plates[0]).backgroundColor:null,
            trackH: tr?Math.round(tr.getBoundingClientRect().height):null,
            fillW: fill?fill.style.width:null,
            fillTarget: fill?fill.dataset.target:null,
            ticks: tr?getComputedStyle(tr,'::before').backgroundSize:null,
            pct: pct?pct.textContent:null,
            scrollX: document.documentElement.scrollWidth - document.documentElement.clientWidth
          };}""")
        print("   profile:", json.dumps(r))
        ck("glow on hero + colour set", bool(r["hasGlow"]) and (r["charGlow"] or "").strip()=="#6C5BD4", r["charGlow"])
        ck("glow pool drawn", r["beforeW"] not in (None,"auto","0px"), r["beforeW"])
        ck("drop-shadow on the character", r["svgFilter"] and "drop-shadow" in r["svgFilter"])
        ck("two plates, equal width", r["plates"]==2 and abs(r["plateRects"][0][0]-r["plateRects"][1][0])<=1, r["plateRects"])
        ck("plates >=44px tall", bool(r["plateRects"]) and min(h for _,h in r["plateRects"])>=44, r["plateRects"])
        ck("bar filled to target", r["fillW"] not in (None,"0%"), (r["fillW"],r["fillTarget"]))
        # ---- THIS ENCODED A DECISION, AND IT REVERSED ----
        # The three quarter marks across the XP track were asked for,
        # and are now read as damage: "the xp bar has lines through it,
        # obviously bugged". A decoration that reads as a defect is
        # worse than no decoration, so they came off - and this asked
        # for them by their exact background-size, which is the tightest
        # possible coupling to a look.
        # What is still worth holding is that the bar is ONE length
        # against ONE track, which is what the ticks were interrupting.
        ck("no ticks across the XP track", r["ticks"] in (None, "auto", "0px"), r["ticks"])
        ck("percentage shown", r["pct"] and r["pct"].endswith("%"), r["pct"])
        ck("no horizontal page scroll (profile)", r["scrollX"]<=0, r["scrollX"])
        # ---- Friends ----
        pg.evaluate("""()=>{
          leaderboardRows=[{pub:'f1',firstName:'Alex',avatarChar:'dragon',level:12,badges:2,hundos:3,
                            seenAt:Date.now(),lastModified:Date.now()}];
          store.friendsOut=[]; store.friendsIn=['f1'];
          showFriends();}""")
        pg.wait_for_timeout(500)
        f=pg.evaluate("""()=>{
          const pill=document.querySelector('.friend-mycode');
          const wrap=document.querySelector('.friend-mycode-wrap');
          const inp=document.querySelector('.friend-add-input');
          const addRow=document.querySelector('.friend-add-row');
          const art=document.querySelector('.friend-row .friend-row-art');
          const lvl=document.querySelector('.friend-row-lvl');
          const copy=[...document.querySelectorAll('.friend-act')].find(b=>b.textContent==='Copy');
          const sect=document.querySelector('.friend-sect-mine');
          const ir=inp?inp.getBoundingClientRect():null, ar=addRow?addRow.getBoundingClientRect():null;
          const pr=pill?pill.getBoundingClientRect():null, wr=wrap?wrap.getBoundingClientRect():null;
          const ics=inp?getComputedStyle(inp):null;
          return {
            pillBg: pill?getComputedStyle(pill).backgroundColor:null,
            /* The GROUP is what is centred - the pill plus its Copy
               button - so measure the wrap inside the card, not the pill
               inside the wrap. */
            wrapCentredInCard: wr&&sect?Math.round((wr.left-sect.getBoundingClientRect().left)-(sect.getBoundingClientRect().right-wr.right)):null,
            rowCentredInCard: (()=>{const a=document.querySelector('.friend-sect:not(.friend-sect-mine)');
              return ar&&a?Math.round((ar.left-a.getBoundingClientRect().left)-(a.getBoundingClientRect().right-ar.right)):null;})(),
            wrapJustify: wrap?getComputedStyle(wrap).justifyContent:null,
            rowJustify: addRow?getComputedStyle(addRow).justifyContent:null,
            inpPadL: ics?ics.paddingLeft:null, inpPadR: ics?ics.paddingRight:null,
            inpFont: ics?ics.fontSize:null,
            inpClass: inp?inp.className:null,
            artGlow: art?[art.classList.contains('has-glow'),art.style.getPropertyValue('--char-glow')]:null,
            artBefore: art?getComputedStyle(art,'::before').width:null,
            lvlColor: lvl?getComputedStyle(lvl).color:null,
            lvlText: lvl?lvl.textContent:null,
            copyClass: copy?copy.className:null,
            copyBg: copy?getComputedStyle(copy).backgroundColor:null,
            copyH: copy?Math.round(copy.getBoundingClientRect().height):null,
            scrollX: document.documentElement.scrollWidth - document.documentElement.clientWidth
          };}""")
        print("   friends:", json.dumps(f))
        ck("code pill darker than the card", f["pillBg"]=="rgba(0, 0, 0, 0.34)", f["pillBg"])
        ck("code group centred in its card", f["wrapCentredInCard"] is not None and abs(f["wrapCentredInCard"])<=1, f["wrapCentredInCard"])
        ck("add-a-code group centred in its card", f["rowCentredInCard"] is not None and abs(f["rowCentredInCard"])<=1, f["rowCentredInCard"])
        ck("both boxes centred", f["wrapJustify"]=="center" and f["rowJustify"]=="center", (f["wrapJustify"],f["rowJustify"]))
        ck("input padding symmetric", f["inpPadL"]==f["inpPadR"], (f["inpPadL"],f["inpPadR"]))
        ck("input >=16px", bool(f["inpFont"]) and float(f["inpFont"].replace("px",""))>=16, f["inpFont"])
        # ---- AND SO DID THIS PAIR ----
        # The per-character halo on a friends row was built from the
        # picker's own AVATAR_GLOW table so a classmate's light was the
        # one they chose. Asked against now: "remove the glow from
        # behind the friends list character, and ensure it's removed
        # from the characters on the leaderboard." In a list of rows it
        # reads as a smear rather than as people.
        # It stays where a character is drawn big and alone - the
        # Profile hero above, which this same file still checks, and the
        # person card. So the assertion flips rather than disappearing:
        # the hero glows, a row does not.
        ck("no glow behind a friends-list character",
           not (f["artGlow"] and f["artGlow"][0]), f["artGlow"])
        ck("and no glow pool drawn on a row",
           f["artBefore"] in (None, "auto", "0px"), f["artBefore"])
        ck("level in the xp bar's blue", f["lvlColor"]=="rgb(111, 194, 255)", (f["lvlColor"],f["lvlText"]))
        ck("Copy is the standard button", f["copyClass"] and "friend-send" in f["copyClass"] and "ghost" not in f["copyClass"], f["copyClass"])
        ck("Copy is 44px", (f["copyH"] or 0)>=44, f["copyH"])
        ck("no horizontal page scroll (friends)", f["scrollX"]<=0, f["scrollX"])
        # ---- Calendar: list view ----
        pg.evaluate("()=>showCalendar()"); pg.wait_for_timeout(600)
        c=pg.evaluate("""()=>{
          const btns=[...document.querySelectorAll('.cal-view-tab, .navsegment .iconbtn, button')];
          const lt=btns.find(b=>/^list$/i.test((b.textContent||'').trim()));
          if(lt) lt.click();
          return !!lt;}""")
        pg.evaluate("""()=>{ document.querySelectorAll('.cal-month-head').forEach(h=>h.click()); }""")
        pg.wait_for_timeout(500)
        cal=pg.evaluate("""()=>{
          const testRows=[...document.querySelectorAll('.cal-row-test')];
          const lastRows=[...document.querySelectorAll('.cal-row-last')];
          const testCells=[...document.querySelectorAll('.cal-cell-test')];
          const dots=[...document.querySelectorAll('.cal-cell-dot-test')];
          return {
            listedTest: testRows.length, listedLast: lastRows.length,
            testChips: document.querySelectorAll('.cal-row-chip-test').length,
            lastChips: document.querySelectorAll('.cal-row-chip-last').length,
            lastChipText: (document.querySelector('.cal-row-chip-last')||{}).textContent||null,
            scrollX: document.documentElement.scrollWidth - document.documentElement.clientWidth
          };}""")
        print("   calendar list:", json.dumps(cal), "(list tab found:", c, ")")
        ck("test days marked in the list", cal["listedTest"]>0 and cal["testChips"]==cal["listedTest"], cal)
        ck("exactly one last day in the list", cal["listedLast"]==1 and cal["lastChips"]==1, (cal["listedLast"],cal["lastChips"]))
        ck("no horizontal page scroll (calendar list)", cal["scrollX"]<=0, cal["scrollX"])
        ck("no uncaught JS errors", not errs, errs[:3])
        ctx.close()
    br.close()
srv.shutdown()
print("\nRESULT:", "ALL PASS" if ok else "FAILURES")
raise SystemExit(0 if ok else 1)
