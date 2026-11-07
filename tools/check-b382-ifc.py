"""Build 382: the Fire Code bar, Stats' buttons, a quieter Nova, the instructor first, and Fire Code's own rules.
  1. Fire Code's Settings tab is a gear with a hub: solid ring, a hole in the hub, three openings between the spokes,
     a dozen-plus teeth (isPointInFill on the tab's own path).
  2. Stats' "All N tests" / Test history pill and the This week / Last week switch: 44px boxes, a pill you can see that
     is near that size, words no smaller than Profile's own tabs - on a 440x956 iPhone, a Pro Max at 85% (518x1125), an
     SE (375x667) and an 11" iPad (834x1194); the test history's filters the same.
  3. Nova: no challenge within 7 days of the last one (novaPending, his own draw forced on), one after; an ended
     challenge's message has no button.
  4. The instructor heads the chat's Friends list and Manage friends, even away and with friends on.
  5. Fire Code: Home, Profile, Stats, Settings on the bar (no Leaderboard), Stats is its own screen and lights its tab,
     Profile has no Stats tab, anything sent to the board lands on Stats. The academy keeps its Leaderboard.
  6. Fire Code's ladder: badge counts rise, the top rank is reachable (no more than the chapters there are) and grows
     with the chapter count; the academy's is unchanged.
  7. Fire Code: one 100% earns a chapter's badge; no hundo bar on the card or the hold card; the academy keeps its bar.
  8. Fire Code never says "unit": Home, the chapters screen, the hold card, Profile, Stats, the badge case, the road
     map, a test, its pause and its results. The book's own words stay. The academy still says "unit".
Run:  python3 tools/check-b382-ifc.py   (--against: copy the old index.html over first)"""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); H = ROOT + "/tools"
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else str(info)[:600])

# ---- the cutscene harness (real index.html from the repo; Fire Code by activeclass + reload, as check-b363-ifc)
# (384) record-landing.py no longer loads the cutscene harness (Get Started round 2 made it self-contained), so the harness
# it used to hand over - record-cutscenes.py's, at 1.5x - is loaded here the way it loaded it
src = open(H + "/record-cutscenes.py").read().split("\nSCENES = [")[0]
src = src.replace("device_scale_factor=1)", "device_scale_factor=1.5)")
rc = {"__file__": H + "/record-cutscenes.py", "__name__": "rc"}; exec(src, rc)
# ---- the layout harness (patched page, fake Firebase), for the four devices
sfsrc = open(os.path.join(H, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
sf = {"__file__": os.path.join(H, "shoot-flow.py"), "__name__": "sf"}; exec(sfsrc, sf)
from playwright.sync_api import sync_playwright

KEYS = "['class26e.ifc.intro.seen','class26e.ifc.unithold.tip','class26e.ifc.daily.seen','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen']"
CALM = ("()=>{ document.getElementById('splashscreen')?.remove(); try{ homeUnlocksOwed=()=>false; }catch(e){} store.novaMet=99; "
        + KEYS + ".forEach(k=>localStorage.setItem(k,'1')); document.querySelectorAll('#tour-overlay,.rs-spot,.unlock-card,.nova-talk').forEach(n=>n.remove()); }")
TAP = "(d)=>{ document.getElementById('nova-intro')?.remove(); const el=document.getElementById('bottomtab-'+d); const b=el.getBoundingClientRect(); const x=b.left+b.width/2,y=b.top+b.height/2; const mk=t=>new PointerEvent(t,{bubbles:true,cancelable:true,pointerType:'touch',pointerId:71,isPrimary:true,clientX:x,clientY:y}); el.dispatchEvent(mk('pointerdown')); setTimeout(()=>{ el.dispatchEvent(mk('pointerup')); el.dispatchEvent(new MouseEvent('click',{bubbles:true,clientX:x,clientY:y})); },60); }"

# every visible "unit" on the page: text nodes and the labels a reader or a screen reader gets, minus the book's own words
UNIT_WORDS = r"""()=>{
  const RX=/\bunits?\b/i;
  const book=[]; const add=v=>{ if(typeof v==='string'){ if(RX.test(v)) book.push(v); } else if(Array.isArray(v)) v.forEach(add); else if(v&&typeof v==='object') Object.keys(v).forEach(k=>add(v[k])); };
  QUESTIONS.forEach(q=>add([q.q,q.choices,q.explanation,q.ref,q.ifc]));
  const isBook=t=>{ t=String(t).trim(); return book.some(b=>b===t||(t.length>=12&&b.indexOf(t)>=0)); };
  const shown=el=>{ for(let e=el;e&&e.nodeType===1;e=e.parentElement){ if(e.hidden) return false; const cs=getComputedStyle(e); if(cs.display==='none'||cs.visibility==='hidden') return false; } return true; };
  const out=[]; const tw=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT|NodeFilter.SHOW_ELEMENT); let n;
  while((n=tw.nextNode())){
    if(n.nodeType===3){ const p=n.parentElement; if(!p||/^(SCRIPT|STYLE)$/.test(p.tagName)) continue; if(RX.test(n.nodeValue)&&!isBook(n.nodeValue)&&shown(p)) out.push(n.nodeValue.trim().slice(0,70)); }
    else ['aria-label','placeholder','title'].forEach(a=>{ const v=n.getAttribute(a); if(v&&RX.test(v)&&!isBook(v)&&shown(n)) out.push('['+a+'] '+v.slice(0,70)); });
  }
  return out; }"""

def ifc_page(br, port, w=440, h=956, seed=None):
    s = dict(rc["SEED"]); s["publicId"] = "xph5b57jbp5a"; s["firstName"] = "Maddog"; s["novaMet"] = 99
    if seed: s.update(seed)
    ctx, pg = rc["new_page"](br, port, w, h, s)
    pg.evaluate("()=>{ localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done'); localStorage.setItem('class26e.activeclass','ifc'); }")
    pg.reload(); pg.wait_for_timeout(3200)
    pg.evaluate(CALM); pg.wait_for_timeout(1200)
    return ctx, pg

def academy_page(br, port, w=440, h=956):
    s = dict(rc["SEED"]); s["publicId"] = "pubtest0382a"; s["novaMet"] = 99
    ctx, pg = rc["new_page"](br, port, w, h, s)
    pg.wait_for_timeout(1000); pg.evaluate(CALM); pg.wait_for_timeout(800)
    return ctx, pg

srv, port = rc["serve"]()
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])

    # ================= Fire Code =================
    ctx, pg = ifc_page(br, port)
    chk("the page is in the Fire Code class", pg.evaluate("()=>window.NOVA_CLASS") == "ifc", pg.evaluate("()=>window.NOVA_CLASS"))

    # ---- 1. the gear
    gear = pg.evaluate(r"""()=>{
      const svg=document.querySelector('#bottomtab-settings .bottomtab-icon svg'); if(!svg) return null;
      const p=[...svg.querySelectorAll('path')]; if(p.length!==1) return {paths:p.length};
      const path=p[0], fill=getComputedStyle(path).fill, pt=new DOMPoint();
      const at=(x,y)=>{ pt.x=x; pt.y=y; return path.isPointInFill(pt); };
      const pol=(r,a)=>[12+r*Math.cos(a),12+r*Math.sin(a)];
      // the teeth: in/out changes round a circle just outside the ring
      let flips=0, prev=null, R=9.4; for(let i=0;i<=1440;i++){ const [x,y]=pol(R,i/1440*2*Math.PI); const v=at(x,y); if(prev!==null&&v!==prev) flips++; prev=v; }
      // the spokes: in/out changes round a circle between the hub and the ring
      let sflips=0; prev=null; for(let i=0;i<=1440;i++){ const [x,y]=pol(4.6,i/1440*2*Math.PI); const v=at(x,y); if(prev!==null&&v!==prev) sflips++; prev=v; }
      const ring=[0,1,2,3,4,5,6,7].every(k=>{ const [x,y]=pol(7.8,k*Math.PI/4+.1); return at(x,y); });
      const box=svg.getBoundingClientRect();
      return {paths:1, fill, stroke:getComputedStyle(path).stroke, centreHole:!at(12,12), hubRing:at(12+1.85,12)&&at(12,12-1.85), ring,
              teeth:flips/2, spokes:sflips/2, box:[Math.round(box.width),Math.round(box.height)]};
    }""")
    print("  gear:", gear)
    chk("1. Fire Code's Settings tab is one filled path (%s)" % (gear and gear.get("paths")), gear and gear.get("paths") == 1 and gear.get("fill") not in ("none", None), gear)
    chk("1. a ring all the way round", gear and gear.get("ring"), gear)
    chk("1. a hub with a hole: solid round the centre, open at it", gear and gear.get("hubRing") and gear.get("centreHole"), gear)
    chk("1. three spokes from the hub to the ring", gear and gear.get("spokes") == 3, gear)
    chk("1. many short teeth round the ring (%s)" % (gear and gear.get("teeth")), gear and 14 <= (gear.get("teeth") or 0) <= 24, gear)

    # ---- 5. the bar and Stats
    bar = pg.evaluate("()=>[...document.querySelectorAll('#bottomtabs .bottomtab')].filter(b=>!b.hidden&&b.getBoundingClientRect().width>0).map(b=>b.dataset.dest)")
    chk("5. Fire Code's bar is Home, Profile, Stats, Settings (%s)" % bar, bar == ["home", "profile", "stats", "settings"], bar)
    glyph = pg.evaluate("()=>{ const s=document.querySelector('#bottomtab-stats .bottomtab-icon svg'); return s ? s.getAttribute('class') : null; }")
    chk("5. the Stats tab has a filled glyph like its neighbours (%s)" % glyph, glyph and "tab-glyph" in glyph, glyph)
    if "stats" in bar:
        pg.evaluate(TAP, "stats"); pg.wait_for_timeout(2000)
        st = pg.evaluate("()=>({stats:!!document.querySelector('#stage .screen-stats'), dots:!!document.querySelector('#stage .stx-dots'), recent:!!document.querySelector('#stage .stx-recent'), tabs:!!document.querySelector('#stage .profiletabs'), lit:[...document.querySelectorAll('#bottomtabs .bottomtab.active')].map(b=>b.id).join(',')})")
        chk("5. the Stats tab opens Stats on its own and lights only Stats (%s)" % st, st["stats"] and st["dots"] and st["recent"] and not st["tabs"] and st["lit"] == "bottomtab-stats", st)
        words8 = pg.evaluate(UNIT_WORDS)
        chk("8. Stats never says unit (%s)" % words8[:4], not words8, words8)
    pg.evaluate(TAP, "profile"); pg.wait_for_timeout(2000)
    pf = pg.evaluate("()=>({tabs:[...document.querySelectorAll('#stage .profiletabs .iconbtn')].map(b=>b.textContent.trim()), lit:[...document.querySelectorAll('#bottomtabs .bottomtab.active')].map(b=>b.id).join(',')})")
    chk("5. Profile has no Stats tab and lights Profile (%s)" % pf, "Stats" not in pf["tabs"] and "Profile" in pf["tabs"] and pf["lit"] == "bottomtab-profile", pf)
    words8 = pg.evaluate(UNIT_WORDS)
    chk("8. Profile never says unit (%s)" % words8[:4], not words8, words8)
    pg.evaluate("()=>{ try{ showRankings(); }catch(e){} }"); pg.wait_for_timeout(1500)
    rk = pg.evaluate("()=>({board:!!document.querySelector('#stage .screen-rankings'), stats:!!document.querySelector('#stage .screen-stats')})")
    chk("5. anything sent to the leaderboard lands on Stats (%s)" % rk, rk["stats"] and not rk["board"], rk)

    # ---- 6. the ladder
    lad = pg.evaluate("()=>({n:topicsIn(QUESTIONS).length, b:TIER_ORDER_FULL.map(k=>TIER_UNLOCKS[k].badges), l:TIER_ORDER_FULL.map(k=>TIER_UNLOCKS[k].level), lab:TIER_UNLOCKS.titan.label})")
    print("  Fire Code ladder:", lad)
    b = lad["b"]
    chk("6. every rank's badges fit in Fire Code's %d chapters and rise rank by rank (%s)" % (lad["n"], b), all(x <= lad["n"] for x in b) and all(b[i] < b[i + 1] for i in range(len(b) - 1)), lad)
    chk("6. the top rank asks for nearly every chapter, not the academy's 14 (%s of %d)" % (b[-1], lad["n"]), b[-1] >= lad["n"] - 4, lad)
    chk("6. the labels say the new counts (%s)" % lad["lab"], str(b[-1]) in lad["lab"], lad)
    flo = pg.evaluate("""()=>{ if(typeof ifcLadderFloorOnce!=='function') return null;
      const t=topicsIn(QUESTIONS).filter(u=>unitQuestionCount(u)<=25).slice(0,3);  // 3 badges at the old bands' 10 hundos
      const was={perf:store.unitPerfects, floor:store.rankFloor, pts:store.lifetime.points};
      store.unitPerfects={}; t.forEach(u=>{ store.unitPerfects[u]=10; }); store.rankFloor=0; store.lifetime.points=1e7;
      localStorage.removeItem('class26e.ifcladder382');
      ifcLadderFloorOnce(); const f=store.rankFloor, rank=rankOf(store);
      store.unitPerfects=was.perf; store.rankFloor=was.floor; store.lifetime.points=was.pts;
      return {floor:f, rank}; }""")
    chk("6. a rank held on the old ladder is kept as a floor (%s)" % flo, flo and flo["floor"] >= 2 and flo["rank"] == "ranger", flo)

    # ---- 7. one hundo, and no bar
    hb = pg.evaluate("""()=>{ const ts=topicsIn(QUESTIONS); const a=ts[0], b2=ts[1];
      store.unitPerfects=Object.assign({}, store.unitPerfects||{}); store.unitPerfects[a]=1; delete store.unitPerfects[b2];
      const card=document.createElement('label'); appendUnitProgress(card, b2);
      const card2=document.createElement('label'); appendUnitProgress(card2, a);
      return {thr:badgeThresholdFor(a), earned:unitBadgeEarned(a), count:badgeCountOf(store), barNot:!!card.querySelector('.pick-bar-track'), textNot:card.textContent.trim(), barYes:!!card2.querySelector('.pick-bar-track')}; }""")
    chk("7. one 100%% earns a Fire Code badge (%s)" % hb, hb["thr"] == 1 and hb["earned"] and hb["count"] >= 1, hb)
    chk("7. a chapter without its badge has no hundo bar, and says what it takes (%r)" % hb["textNot"], not hb["barNot"] and "100%" in hb["textNot"], hb)

    # ---- 8 + 7: the chapters screen, the hold card
    pg.evaluate("()=>{ cfg.mode='drill'; showSetup(); }"); pg.wait_for_timeout(1800)
    pg.evaluate(CALM); pg.wait_for_timeout(300)
    words8 = pg.evaluate(UNIT_WORDS)
    chk("8. the chapters screen never says unit (%s)" % words8[:4], not words8, words8)
    bars = pg.evaluate("()=>document.querySelectorAll('#stage .pick-bar-track').length")
    chk("7. no hundo bars on the chapter cards (%d)" % bars, bars == 0, bars)
    hold = pg.evaluate("""()=>{ const row=document.querySelector('#stage .pick'); if(!row) return null; const name=topicsIn(QUESTIONS)[1];
      openUnitDetail(row, name, 'drill'); const c=document.querySelector('.unitdetail'); if(!c) return null;
      return {bar:!!c.querySelector('.pick-bar-track'), cap:(c.querySelector('.unitdetail-badgecap')||{}).textContent||''}; }""")
    pg.wait_for_timeout(900)
    chk("7. the hold card has no hundo bar and says one 100%% earns it (%s)" % hold, hold and not hold["bar"] and "100%" in hold["cap"], hold)
    words8 = pg.evaluate(UNIT_WORDS)
    chk("8. the hold card never says unit (%s)" % words8[:4], not words8, words8)
    pg.evaluate("()=>{ document.querySelectorAll('.unitdetail-scrim,.unitdetail').forEach(n=>n.remove()); try{ unitDetailOpen=false; }catch(e){} }")
    for name, js in (("Home", "showHome()"), ("the badge case", "showRanksScreen('badges')"), ("the road map", "showRanksScreen('ranks')")):
        pg.evaluate("()=>{ try{ " + js + "; }catch(e){ console.error(e); } }"); pg.wait_for_timeout(1800); pg.evaluate(CALM); pg.wait_for_timeout(300)
        words8 = pg.evaluate(UNIT_WORDS)
        chk("8. %s never says unit (%s)" % (name, words8[:4]), not words8, words8)
    # a test: the question, its pause, its results
    unit = pg.evaluate("()=>topicsIn(QUESTIONS).filter(u=>unitQuestionCount(u)<=12)[0]")
    rc["start_unit_run"](pg, unit)
    try:
        pg.wait_for_selector(".choice", timeout=25000); pg.wait_for_timeout(600)
        words8 = pg.evaluate(UNIT_WORDS)
        chk("8. a Fire Code test never says unit (%s)" % words8[:4], not words8, words8)
        pg.evaluate("()=>{ const b=document.getElementById('pausebtn')||document.querySelector('.pausebtn'); if(b) b.click(); }"); pg.wait_for_timeout(900)
        paused = pg.evaluate("()=>!!document.querySelector('.pausepanel, .pause-sheet, #pausepanel')")
        words8 = pg.evaluate(UNIT_WORDS)
        chk("8. its pause never says unit (paused: %s; %s)" % (paused, words8[:4]), not words8, words8)
        pg.evaluate("()=>{ const r=document.querySelector('.pausepanel .resume, #resumebtn, [data-act=resume]'); if(r) r.click(); }"); pg.wait_for_timeout(700)
        rc["answer_all"](pg)
        pg.wait_for_timeout(4500)
        res = pg.evaluate("()=>!!document.querySelector('#stage .screen-results, #stage .results, #stage [class*=results]')")
        words8 = pg.evaluate(UNIT_WORDS)
        chk("8. its results never say unit (results up: %s; %s)" % (res, words8[:4]), not words8, words8)
    except Exception as e:
        chk("8. a Fire Code test runs (%s)" % e, False)
    # the helper leaves the book's own words alone
    book = pg.evaluate(r"""()=>{ const q=QUESTIONS.find(q=>/\bunits?\b/i.test(q.q)); if(!q) return null;
      const p=document.createElement('p'); p.textContent=q.q; document.body.appendChild(p);
      return new Promise(r=>setTimeout(()=>{ const same=p.textContent===q.q; p.remove(); r({same, q:q.q.slice(0,60)}); },150)); }""")
    chk("8. a question's own \"unit\" stays as the book wrote it (%s)" % book, book and book["same"], book)
    ctx.close()

    # ================= the academy =================
    ctx, pg = academy_page(br, port)
    bar = pg.evaluate("()=>[...document.querySelectorAll('#bottomtabs .bottomtab')].filter(b=>!b.hidden&&b.getBoundingClientRect().width>0).map(b=>b.dataset.dest)")
    chk("5. the academy's bar is unchanged: Home, Profile, Leaderboard, Calendar (%s)" % bar, bar == ["home", "profile", "rewards", "calendar"], bar)
    lad = pg.evaluate("()=>TIER_ORDER_FULL.map(k=>TIER_UNLOCKS[k].badges)")
    chk("6. the academy's ladder is unchanged (%s)" % lad, lad == [1, 3, 5, 7, 9, 12, 14], lad)
    ac = pg.evaluate("""()=>{ const t=topicsIn(QUESTIONS).find(u=>!unitBadgeEarned(u)); const c=document.createElement('label'); appendUnitProgress(c, t);
      return {thr:badgeThresholdFor(t), bar:!!c.querySelector('.pick-bar-track')}; }""")
    chk("7. the academy keeps its hundo bands and bar (%s)" % ac, ac["thr"] > 1 and ac["bar"], ac)
    pg.evaluate("()=>{ cfg.mode='drill'; showSetup(); }"); pg.wait_for_timeout(1800)
    says = pg.evaluate("()=>/\\bunits?\\b/i.test(document.body.innerText) || /\\bunits?\\b/i.test((document.querySelector('#stage input[type=search], #stage .searchbox')||{}).placeholder||'')")
    chk("8. the academy still says unit", says, says)
    pg.evaluate("()=>showProfile('stats')"); pg.wait_for_timeout(1500)
    pf = pg.evaluate("()=>[...document.querySelectorAll('#stage .profiletabs .iconbtn')].map(b=>b.textContent.trim())")
    chk("5. the academy's Profile keeps its Stats tab (%s)" % pf, "Stats" in pf, pf)

    # ---- 3. Nova
    nv = pg.evaluate("""()=>{ if(typeof novaPending!=='function') return null;
      const was=window.novaChallengeDue; window.novaChallengeDue=()=>true;
      const now=Date.now(), wk=weekKeyNow(), out={ready: typeof NOVA_VR_READY!=='undefined' && !!NOVA_VR_READY};
      const h1={ "@base":1 }; h1["wk:2000-01-03"]=now-2*864e5; out.two=novaPending(h1, now).weekly;
      const h2={ "@base":1 }; h2["wk:2000-01-03"]=now-8*864e5; out.eight=novaPending(h2, now).weekly;
      const h3={ "@base":1 }; out.never=novaPending(h3, now).weekly;
      window.novaChallengeDue=was; out.wk=wk;
      const act=novaMsgAction({kind:'challenge', wk:'2000-01-03', text:'x'});
      out.ended = act ? act.textContent.trim() : null;
      const live=novaMsgAction({kind:'challenge', wk:wk, text:'x'});
      out.live = live ? live.textContent.trim() : null;
      return out; }""")
    print("  Nova:", nv)
    if nv and nv.get("ready"):
        chk("3. no challenge two days after the last one (%s)" % nv.get("two"), nv.get("two") is None, nv)
        chk("3. a challenge again after seven days (%s)" % nv.get("eight"), nv.get("eight") == nv.get("wk") and nv.get("never") == nv.get("wk"), nv)
    else:
        chk("3. Nova's challenges are on in this build", False, nv)
    chk("3. an ended challenge's message has no button (%s)" % (nv and nv.get("ended")), nv and nv.get("ended") is None, nv)
    chk("3. a live one still has Accept (%s)" % (nv and nv.get("live")), nv and nv.get("live") == "Accept", nv)

    # ---- 4. the instructor first (he is away, both friends are on: the old order put him last)
    fr = pg.evaluate("""()=>{
      window.novaIsFriend=()=>true; window.novaAway=()=>true; window.novaUnread=()=>false;
      window.friendPublicIds=()=>['fra000000001','frb000000002'];
      const rows={ fra000000001:{pub:'fra000000001', firstName:'Alex', avatarChar:'ninja', level:30}, frb000000002:{pub:'frb000000002', firstName:'Blake', avatarChar:'ninja', level:31} };
      window.rowsByPublicId=()=>rows; window.isOnline=e=>!!e && e.pub!=='nova';
      store.leaderboardOptIn=true;
      try{ openChatDock(); }catch(e){}
      try{ chatDockTab='friends'; chatRoomCode=null; }catch(e){}
      const body=document.querySelector('.chatdock-body, #chatdock .chatdock-tabbody') ;
      try{ renderChatDock(); }catch(e){ try{ renderFriendChatList(); }catch(e2){} }
      const chat=[...((document.querySelector('.chatdock-chatlist.is-friends')||document.body).querySelectorAll('.chatdock-chatrow'))].map(r=>r.classList.contains('is-nova')?'Nova':(r.querySelector('.chatdock-chatrow-name')||{}).textContent);
      try{ closeChatDock(); }catch(e){}
      showFriends();
      const manage=[...document.querySelectorAll('#stage .friend-sect .friend-row')].map(r=>r.classList.contains('is-nova')?'Nova':(r.querySelector('.friend-row-name')||{}).textContent);
      return {chat, manage}; }""")
    pg.wait_for_timeout(500)
    chk("4. the chat's Friends list starts with the instructor (%s)" % fr["chat"], len(fr["chat"]) == 3 and fr["chat"][0] == "Nova", fr)
    chk("4. Manage friends starts with the instructor (%s)" % fr["manage"], len(fr["manage"]) == 3 and fr["manage"][0] == "Nova", fr)
    ctx.close()

    # ================= 2. the buttons, four devices =================
    surl = sf["serve"]()[1]
    INIT = """(()=>{ if(localStorage.getItem('class26e.drill.v1')) return;
     localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-0382');
     ['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card','class26e.getstarted'].forEach(k=>localStorage.setItem(k,'1'));
     localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.penal256578.seen','1'); })()"""
    d = json.loads(sf["SEED"].replace("__WEEK__", sf["week_key_now"]())); d["publicId"] = "pubtest0382b"; d["firstName"] = "Casey"; d["novaMet"] = 99
    MEAS = """()=>{ const r=el=>el?el.getBoundingClientRect():null; const fs=el=>el?parseFloat(getComputedStyle(el).fontSize):0;
      /* (384) Test history is a row under the last test (Madison: "a bigger button under the last test"), not the heading's pill */
      const all=document.querySelector('#stage .stx-histrow, #stage .stx-allbtn.stx-allpill'), allIn=all&&(all.querySelector('.pf-act-label')?all:all.querySelector('span'));
      const wk=[...document.querySelectorAll('#stage .stx-dots-switch > button')];
      const tab=document.querySelector('#stage .profiletabs .iconbtn');
      return {allH:all?r(all).height:0, allVis:allIn?r(allIn).height:0, allFs:fs(all&&(all.querySelector('.pf-act-label')||all.querySelector('b'))||all),
              wkH:wk.length?Math.min(...wk.map(b=>r(b).height)):0, wkFs:wk.length?fs(wk[0]):0, wkN:wk.length, tabFs:fs(tab)}; }"""
    for (w, h, ins, lab) in ((440, 956, (62, 0, 34, 0), "iPhone 440x956"), (518, 1125, (73, 0, 40, 0), "Pro Max at 85%, 518x1125"),
                             (375, 667, (20, 0, 0, 0), "SE 375x667"), (834, 1194, (24, 0, 20, 0), "iPad 834x1194")):
        c2 = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=2, has_touch=True, is_mobile=True)
        c2.add_init_script(sf["STANDALONE"]); c2.add_init_script(sf["FAKE_FIREBASE"].replace("__ROWS__", sf["rows_json"]()))
        p2 = c2.new_page(); body = sf["patched"](ins)
        p2.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
        p2.add_init_script(INIT % json.dumps(json.dumps(d)))
        p2.goto(surl); p2.wait_for_timeout(3000); p2.evaluate("document.getElementById('splashscreen')?.remove()")
        p2.evaluate("()=>{ try{homeUnlocksOwed=()=>false;}catch(e){} showProfile('stats'); }"); p2.wait_for_timeout(1600)
        m = p2.evaluate(MEAS)
        print("  %s:" % lab, {k: round(v, 1) for k, v in m.items()})
        chk("2. %s: Test history is a 44px button you can see (box %.0f, pill %.0f)" % (lab, m["allH"], m["allVis"]), m["allH"] >= 44 and m["allVis"] >= 36, m)
        chk("2. %s: This week / Last week are 44px buttons (%.0f)" % (lab, m["wkH"]), m["wkN"] == 2 and m["wkH"] >= 44, m)
        chk("2. %s: their words are no smaller than Profile's tabs (pill %.1f, week %.1f, tabs %.1f)" % (lab, m["allFs"], m["wkFs"], m["tabFs"]),
            m["allFs"] >= m["tabFs"] - .01 and m["wkFs"] >= m["tabFs"] - .01, m)
        p2.evaluate("()=>{ store.testHistory=[{units:['Penal Code'],mode:'drill',pct:90,playedAt:Date.now()-3e5,n:10,c:9},{units:['TCOLE Rules'],mode:'exam',pct:80,playedAt:Date.now()-6e5,n:10,c:8}]; showTestReviewList(); }"); p2.wait_for_timeout(1200)
        fl = p2.evaluate("()=>[...document.querySelectorAll('#stage .thx-filter-btn')].map(b=>b.getBoundingClientRect().height)")
        if True:
            chk("2. %s: the test history's filters are 44px (%s)" % (lab, [round(x) for x in fl]), len(fl) >= 2 and min(fl) >= 44, fl)
        c2.close()
    br.close()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
