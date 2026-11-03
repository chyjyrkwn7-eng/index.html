"""Build 382: every character and every banner can be seen again, locked ones greyed.
Madison: "we made the character unlocks hidden, we can remove that, that would be removed during the
intro and stuff too, just make it on the intro like greyed out ya know. Anyways yeah, they are gonna be
viewable again." and "Change app wide, all the banners will be viewable some of them you can't see till
they are unlocked.. remove that."

On a near-fresh account, in the Police Academy class and in Fire Code (NOVA_CLASS "ifc"):
  A. Customize > Characters: every character the table lists (bar retired/kept ones nobody holds) has a
     tile; a locked one is its real drawing (no cut-out, the drawing's own coloured paints are on it),
     greyed (a desaturating filter), with a padlock, and a tap does not pick it (it opens its card).
  B. Customize > Banners: every banner in BANNERS has a tile; none is veiled ("Unlock to see"); a locked
     one shows its art (an svg scene or a loaded still picture), greyed, with a visible padlock; a tap
     does not put it on. A locked secret flare banner's card shows the art too, and a secret
     character's card is no cut-out.
  C. The rank road map: every rank's character and banner chip is drawn (no cut-out).
  D. Sign-up (academy): Nova's "My crew" parade draws every missing crewman as his own drawing, greyed
     (no cut-out), and his character question shows the starters to pick plus every other character
     greyed and not pickable; the older sign-up screen (showWelcomeCharacterPrompt) does the same.
Screenshots go to $SHOTS (default: no screenshots).
Run:  python3 tools/check-b382-unhide.py   (--against: copy the old index.html over first, then restore)"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
from playwright.sync_api import sync_playwright
SHOTS = os.environ.get("SHOTS", "")
srv, url = g["serve"]()
OWNER = "xph5b57jbp5a"
KEYS = ['class26e.freshstart', 'class26e.intro.seen', 'class26e.unithold.tip', 'class26e.daily.seen', 'class26e.savecode.asked','class26e.savecode.card',
        'class26e.getstarted', 'class26e.weekrecap.v1', 'class26e.penal55124.seen', 'class26e.penal124256.seen', 'class26e.penal256578.seen']
INIT = """(()=>{ if(localStorage.getItem('class26e.drill.v1')) return;
 localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-0382');
 %s.forEach(k=>localStorage.setItem(k, k==='class26e.weekrecap.v1' ? '9999-12-31' : '1'));
 localStorage.setItem('class26e.frame.ok','go-live-1'); %s })()"""
# a near-fresh account: a starter on, a little XP, nothing earned
SEED = {"firstName": "Casey", "avatarChar": "ninja", "onboardingComplete": True, "leaderboardOptIn": True, "lastModified": 1700000000000,
        "tourRev": 99, "rankMapFx244": True, "seenProfileTour": True, "seenModeSelectTour": True, "seenUnitSelectTour": True,
        "seenMainMenuTour": True, "seenRankingsTour": True, "seenAppearanceTour": True, "novaMet": 99,
        "lifetime": {"points": 150, "answered": 40, "correct": 30}}
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else ("-> " + str(info)[:900]))
def shot(pg, name):
    if SHOTS:
        os.makedirs(SHOTS, exist_ok=True); pg.screenshot(path=os.path.join(SHOTS, name + ".png"))
def page(br, ifc, fresh=False, w=440, h=956):
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=2)
    ctx.add_init_script(g["STANDALONE"])
    ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]()))
    pg = ctx.new_page(); body = g["patched"]((62, 0, 34, 0))
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    if not fresh:
        d = dict(SEED); d["publicId"] = OWNER if ifc else "pubtest0382u"
        extra = ("localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done');"
                 "localStorage.setItem('class26e.activeclass','ifc');" + "".join("localStorage.setItem('%s','1');" % k.replace("class26e.", "class26e.ifc.") for k in KEYS)) if ifc else ""
        pg.add_init_script(INIT % (json.dumps(json.dumps(d)), json.dumps(KEYS), extra))
    pg.goto(url); pg.wait_for_timeout(3200)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); }")
    if not fresh:
        pg.evaluate("()=>{ try{ homeUnlocksOwed=()=>false; }catch(e){} document.querySelectorAll('.rs-spot,.unlock-card,.nova-talk,.invite-overlay').forEach(n=>n.remove()); }")
        pg.wait_for_timeout(600)
    return ctx, pg
CLOSE = "()=>{ document.querySelectorAll('.invite-overlay, .unlock-card').forEach(n=>n.remove()); }"
# the paints a drawing carries: a cut-out has only black/grey ones on its figure
PAINTS = """(svg)=>{ let hue=0; svg.querySelectorAll('*').forEach(n=>{ const f=(n.getAttribute('fill')||'')+' '+(n.getAttribute('stroke')||'')+' '+(n.style&&n.style.fill||'');
  const m=f.match(/#([0-9a-f]{6}|[0-9a-f]{3})\\b/ig)||[]; m.forEach(c=>{ let h=c.slice(1); if(h.length===3) h=h.split('').map(x=>x+x).join('');
  const r=parseInt(h.slice(0,2),16),g=parseInt(h.slice(2,4),16),b=parseInt(h.slice(4,6),16); if(Math.max(r,g,b)-Math.min(r,g,b)>40) hue++; }); }); return hue; }"""
CHARS = """()=>{ const PAINTS=%s; const exp=AVATAR_CHARACTERS.filter(c=>!(c.retired&&store.avatarChar!==c.id)&&!(c.legacy&&isLockedCharacter(c.id))).map(c=>c.id);
  const opts=[...document.querySelectorAll('.screen-customize .avatarchar-option')];
  const byId={}; opts.forEach(o=>{ const id=(AVATAR_CHARACTERS.find(c=>(AVATAR_DISPLAY_NAME[c.id]||c.id)===o.title)||{}).id; if(id) byId[id]=o; });
  const bad=[]; let locked=0;
  exp.forEach(id=>{ const o=byId[id]; if(!o){ bad.push(id+': no tile'); return; }
    if(!isLockedCharacter(id)) return; locked++;
    const svg=o.querySelector('svg:not(.avatarchar-lockmark svg)');
    if(o.classList.contains('is-silhouette')||o.querySelector('.char-sil')) bad.push(id+': cut-out');
    if(!svg){ bad.push(id+': no drawing'); return; }
    if(/~sil/.test(svg.getAttribute('data-char')||'')) bad.push(id+': silhouette drawing');
    if(PAINTS(svg)<3) bad.push(id+': no colour paints ('+PAINTS(svg)+')');
    const f=getComputedStyle(svg).filter+' '+getComputedStyle(o).filter;
    if(!/saturate|grayscale/.test(f)) bad.push(id+': not greyed ('+f+')');
    if(!o.classList.contains('locked')||!o.querySelector('.avatarchar-lockmark')) bad.push(id+': no padlock');
  });
  return {expected:exp.length, tiles:opts.length, locked, bad}; }""" % PAINTS
BANNERS = """()=>{ const tiles=[...document.querySelectorAll('.screen-customize .banner-opt')]; const bad=[]; let locked=0;
  BANNERS.forEach(d=>{ const t=tiles.find(x=>x.dataset.banner===d.id); if(!t){ bad.push(d.id+': no tile'); return; }
    if(bannerEarned(d.id)) return; locked++;
    const art=t.querySelector('.banner-opt-art');
    if(art.classList.contains('is-veiled')||art.querySelector('.bnr-veil')||t.classList.contains('is-secret')) bad.push(d.id+': veiled');
    const b=art.querySelector(':scope > .bnr'); if(!b){ bad.push(d.id+': no art'); return; }
    const img=b.querySelector('img');
    if(!(b.querySelectorAll('svg path, svg rect, svg circle, svg ellipse, svg polygon').length>3) && !(img && img.complete && img.naturalWidth>0)) bad.push(d.id+': art empty');
    if(!/grayscale/.test(getComputedStyle(b).filter)) bad.push(d.id+': not greyed');
    const lk=t.querySelector('.banner-opt-lock'); if(!lk||getComputedStyle(lk).display==='none') bad.push(d.id+': no padlock');
  });
  return {n:BANNERS.length, locked, bad}; }"""
def customize(pg, label, tag):
    pg.evaluate("()=>showCustomize('character')"); pg.wait_for_timeout(2500)
    r = pg.evaluate(CHARS)
    chk("%s A: every character has a Customize tile, every locked one its own drawing, greyed, padlocked (%d tiles, %d locked)" % (label, r["tiles"], r["locked"]),
        r["locked"] >= 15 and not r["bad"], r["bad"])
    shot(pg, tag + "-customize-characters")
    pg.evaluate("()=>{ const s=[...document.querySelectorAll('.avatarchar-group-title')].find(h=>/Secrets/.test(h.textContent)); if(s) s.scrollIntoView(); }"); pg.wait_for_timeout(600)
    shot(pg, tag + "-customize-characters-secrets")
    t = pg.evaluate("""()=>{ const before=store.avatarChar; const o=[...document.querySelectorAll('.screen-customize .avatarchar-option')].find(o=>o.title===(AVATAR_DISPLAY_NAME.umbra||'umbra'));
      if(!o) return {found:false}; o.click(); const art=document.querySelector('.unlock-card-art');
      return {found:true, same:store.avatarChar===before, card:!!document.querySelector('.unlock-card'), cut:!!art&&(art.classList.contains('is-silhouette')||!!art.querySelector('.char-sil')||art.classList.contains('is-hidden-art')),
        hidden:/hidden/i.test((document.querySelector('.unlock-card')||{}).textContent||'')}; }""")
    chk("%s A: a locked secret character is not picked by a tap; its card shows it, no cut-out, never says hidden (%s)" % (label, t),
        t.get("found") and t["same"] and t["card"] and not t["cut"] and not t["hidden"], t)
    pg.wait_for_timeout(500); shot(pg, tag + "-card-umbra"); pg.evaluate(CLOSE)
    pg.evaluate("()=>showCustomize('banner')"); pg.wait_for_timeout(2000)
    # the scenes are drawn in the frames after the screen (fillDeferredBannerArt): wait for them all
    try: pg.wait_for_function("()=>[...document.querySelectorAll('.screen-customize .banner-opt:not(.is-none) .banner-opt-art')].every(a=>a.querySelector(':scope > .bnr, .bnr-veil'))", timeout=20000)
    except Exception: pass
    pg.evaluate("()=>{ const t=document.querySelector('.banner-opt[data-banner=\"flare_void\"]'); if(t) t.scrollIntoView({block:'center'}); }"); pg.wait_for_timeout(1500)
    r = pg.evaluate(BANNERS)
    chk("%s B: every banner has a tile, none veiled, every locked one its art, greyed, padlocked (%d banners, %d locked)" % (label, r["n"], r["locked"]),
        r["locked"] >= 10 and not r["bad"], r["bad"])
    shot(pg, tag + "-customize-banners-secret")
    t = pg.evaluate("""()=>{ const before=store.banner; const b=document.querySelector('.banner-opt[data-banner="flare_umbra"]'); if(!b) return {found:false};
      b.click(); const card=document.querySelector('.unlock-card'), art=card&&card.querySelector('.unlock-card-art');
      return {found:true, same:store.banner===before, card:!!card, veiled:!!art&&(art.classList.contains('is-veiled')||!!art.querySelector('.bnr-veil')), drawn:!!art&&!!art.querySelector('.bnr svg, .bnr img')}; }""")
    chk("%s B: a locked secret flare banner is not put on by a tap; its card shows the banner, unveiled (%s)" % (label, t),
        t.get("found") and t["same"] and t["card"] and not t["veiled"] and t["drawn"], t)
    pg.wait_for_timeout(500); shot(pg, tag + "-card-flare-umbra"); pg.evaluate(CLOSE)
def roadmap(pg, label, tag):
    pg.evaluate("()=>showRanksScreen('ranks')"); pg.wait_for_timeout(2000)
    try: pg.wait_for_function("()=>{ const a=[...document.querySelectorAll('.rankmap-giftav:not(.rankmap-giftbubble), .rankmap-giftbanner')]; return a.length && a.every(x=>x.querySelector('svg, .bnr')); }", timeout=20000)
    except Exception: pass
    r = pg.evaluate("""()=>{ const want=AVATAR_CHARACTERS.filter(c=>c.unlock&&!c.retired).length;
      const av=[...document.querySelectorAll('.rankmap-giftav:not(.rankmap-giftbubble)')]; const bn=[...document.querySelectorAll('.rankmap-giftbanner')];
      return {want, chars:av.length, drawn:av.filter(a=>a.querySelector('svg')&&!a.querySelector('.char-sil')).length, banners:bn.length,
        bdrawn:bn.filter(b=>b.querySelector('.bnr')&&!b.querySelector('.bnr-veil')).length, wantB:BANNERS.filter(b=>b.rank&&!b.retired).length}; }""")
    chk("%s C: the road map draws every rank's character and banner (%s)" % (label, r), r["chars"] >= r["want"] and r["drawn"] == r["chars"] and r["bdrawn"] == r["banners"] and r["banners"] >= r["wantB"], r)
    pg.evaluate("()=>{ const s=document.querySelector('.rankmap-stop .rankmap-giftav:not(.rankmap-giftbubble)'); if(s) s.scrollIntoView({block:'center'}); }"); pg.wait_for_timeout(1200)
    shot(pg, tag + "-roadmap")
ADV = """() => { const el = document.getElementById('nova-intro'); if(!el || !el.__nova) return 'gone';
  if(el.__nova.typing){ el.__nova.advance(); return 'typing'; }
  if(el.__nova.asking) return el.querySelector('.nt-ask-name') ? 'name' : el.querySelector('.nt-ask-char') ? 'char' : 'ask';
  if(el.querySelector('.nt-prop.is-in:not(.is-prepped) .nt-crewpar:not(.nt-laterpar)') && !window.__crewSeen){ window.__crewSeen = true; return 'crew'; }
  if(el.__nova.index === el.__nova.count - 1){ el.querySelector('.nt-go').click(); return 'next'; }
  el.__nova.advance(); return 'next'; }"""
CREW = """(sel)=>{ const PAINTS=%s; const tiles=[...document.querySelectorAll(sel)]; const lost=tiles.filter(t=>t.classList.contains('is-lost'));
  const bad=[]; lost.forEach((t,i)=>{ const svg=t.querySelector('svg'); if(t.querySelector('.char-sil')||(svg&&/~sil/.test(svg.getAttribute('data-char')||''))) bad.push(i+': cut-out');
    else if(!svg||PAINTS(svg)<3) bad.push(i+': no drawing'); else if(!/saturate|grayscale/.test(getComputedStyle(svg).filter)) bad.push(i+': not greyed'); });
  return {tiles:tiles.length, lost:lost.length, bad}; }""" % PAINTS
def signup(br):
    ctx, pg = page(br, False, fresh=True)
    if not pg.evaluate("() => !!document.querySelector('.cosmic-welcome-btn.welcome-new')"):
        pg.evaluate("() => showWelcome()"); pg.wait_for_timeout(600)
    for sel in (".cosmic-welcome-btn.welcome-new", ".signupcheck-panel .signupcheck-go", ".classselect-panel .class-card.is-academy", ".classselect-panel .next.playbtn"):
        try: pg.click(sel, timeout=4000)
        except Exception: pass
        pg.wait_for_timeout(600)
    try:
        pg.wait_for_selector("#genprofile-overlay", state="detached", timeout=25000); pg.wait_for_selector("#nova-intro", timeout=8000)
    except Exception: pass
    pg.wait_for_timeout(1200)
    def until(kinds, n=260):
        for _ in range(n):
            k = pg.evaluate(ADV)
            if k in kinds or k == "gone": return k
            pg.wait_for_timeout(110)
        return None
    k = until(("name",))
    if k == "name":
        pg.fill(".nt-ask-input", "J.Smith"); pg.click(".nt-ask-name .nt-ask-go"); pg.wait_for_timeout(900)
    k = until(("crew", "char"))
    pg.wait_for_timeout(1500)
    r = pg.evaluate(CREW, "#nova-intro .nt-prop.is-in:not(.is-prepped) .nt-crewpar:not(.nt-laterpar) .nt-crewman")
    chk("D: the intro's crew parade draws every missing crewman as his own drawing, greyed (%s)" % ({"at": k, **r},), k == "crew" and r["lost"] >= 15 and not r["bad"], r)
    shot(pg, "intro-crew")
    k = until(("char",)); pg.wait_for_timeout(1600)
    r = pg.evaluate("""()=>{ const c=document.querySelector('.nt-ask-char'); if(!c) return null;
      const pick=c.querySelectorAll('.nt-ask-grid .avatarchar-option').length; const later=[...c.querySelectorAll('.nt-ask-later .nt-crewman')];
      const want=novaCrewShown().filter(x=>isLockedCharacter(x.id)).length;
      return {pick, later:later.length, want, buttons:c.querySelectorAll('.nt-ask-later button').length}; }""")
    g2 = pg.evaluate(CREW, ".nt-ask-char .nt-ask-later .nt-crewman")
    chk("D: his character question: the starters to pick, every other character shown greyed and not pickable (%s %s)" % (r, g2),
        k == "char" and r and r["pick"] >= 4 and r["later"] == r["want"] and r["want"] >= 15 and r["buttons"] == 0 and not g2["bad"], [r, g2])
    shot(pg, "intro-choose")
    # the older sign-up character screen
    pg.evaluate("()=>{ document.getElementById('nova-intro')?.remove(); showWelcomeCharacterPrompt(); }"); pg.wait_for_timeout(1500)
    r = pg.evaluate("""()=>{ const PAINTS=%s; const p=document.querySelector('.charselect-panel'); if(!p) return null; const lk=[...p.querySelectorAll('.avatarchar-option.locked')];
      const want=AVATAR_CHARACTERS.filter(c=>!c.retired&&!c.legacy&&isLockedCharacter(c.id)).length; const before=store.avatarChar; if(lk[0]) lk[0].click();
      return {locked:lk.length, want, greyed:lk.filter(o=>{ const s=o.querySelector('svg'); return s&&PAINTS(s)>=3&&/saturate|grayscale/.test(getComputedStyle(s).filter)&&o.querySelector('.avatarchar-lockmark'); }).length,
        notPicked:!p.querySelector('.avatarchar-option.locked.selected'), cont:p.querySelector('.next.playbtn').hidden}; }""" % PAINTS)
    chk("D: the sign-up character screen shows every other character greyed, padlocked, not pickable (%s)" % (r,),
        r and r["locked"] == r["want"] and r["want"] >= 15 and r["greyed"] == r["locked"] and r["notPicked"] and r["cont"], r)
    pg.evaluate("()=>{ const l=document.querySelector('.charselect-later'); if(l) l.scrollIntoView({block:'center'}); }"); pg.wait_for_timeout(500)
    shot(pg, "signup-charselect")
    ctx.close()
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    for ifc in (False, True):
        label = "Fire Code:" if ifc else "Academy:"
        ctx, pg = page(br, ifc)
        cls = pg.evaluate("()=>window.NOVA_CLASS")
        chk("%s the page runs as that class (%s)" % (label, cls), cls == ("ifc" if ifc else "academy"), cls)
        customize(pg, label, "ifc" if ifc else "academy")
        roadmap(pg, label, "ifc" if ifc else "academy")
        ctx.close()
    signup(br)
    br.close()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
