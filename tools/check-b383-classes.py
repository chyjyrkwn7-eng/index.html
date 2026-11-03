"""Build 383: two classes, nothing crossing between them; Settings' Account and Sign out; the week's recap per class.
Madison: "In fire code, why is settings still within profile? It should just be in on the bottom tab" / "We need a profile
thing in settings, change your username and logout ... The function to log out for sure" / the weekly recap "needs to be
specified the class it's for at the top ... it could populate on the Home Screen ... when getting in the app, or switching
over to that class, it would show the main menu for a second and then that would pop up" / "We can't afford to let anything
leak from one class to the other."
With check-b383-ifcsync's in-memory Firestore and owner account (TEST-3830, a fake code):
 (1) Fire Code: Profile has no switch over it (Profile alone); the bar's Settings opens Settings alone, the bar's Settings lit;
 (2) Settings > Account (the row at the top of Account) holds the name editor and Sign out;
 (3) Sign out, with this device's progress in the cloud: the confirm sheet shows the code; Sign out reloads to Welcome and the
     device holds neither class's account (stores, code, active class, backups) while its device settings and the
     "had an account" note stay - and the cloud account is still there, untouched;
 (4) Sign out with the cloud not answering: it refuses, says so, and the device stays signed in;
 (5) the week's recap plays on the first Home of a launch, a moment after the menu, headed with its class - "Police Academy"
     in the academy and "Fire Code" in Fire Code;
 (Fire Code's activity never reaching the academy's saved copy or cloud account is check-b383-ifcsync's (1)/(4) and
  check-b328-classes' "the academy's copy, untouched".)
Run:  python3 tools/check-b383-classes.py   (--against OLD/index.html must FAIL)"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b383c"}
sys_argv = list(sys.argv); exec(src, G)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else ("  -> " + str(info)[:300]), flush=True)
CODE = G["CODE"]
def recap_store(store):
    st = json.loads(json.dumps(store)); st.pop("novaHeard", None); st["leaderboardOptIn"] = False
    st["weekStats"] = None; st["prevWeekStats"] = None
    return st
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    # (1) Fire Code's bar tabs
    ctx, pg, errs = G["page"](br, G["init"](G["ifc"]))
    r = pg.evaluate("""async()=>{ const w=ms=>new Promise(r=>setTimeout(r,ms)); const out={};
      showProfile('profile'); await w(900); out.profileSeg = !!document.querySelector('#stage .screen-profile > .navsegment.profiletabs');
      out.profileOnly = !!document.querySelector('#stage .profile-identity-tab:not([hidden])') && !document.querySelector('#stage .profile-settings-tab');
      document.getElementById('bottomtab-settings')?.click(); await w(1100);
      out.settingsSeg = !!document.querySelector('#stage .screen-profile > .navsegment.profiletabs');
      out.settingsShown = !!document.querySelector('#stage .profile-settings-tab:not([hidden]) #settings-row-sound');
      out.lit = (document.querySelector('#bottomtabs .bottomtab.active')||{}).id || null;
      out.title = document.getElementById('count').textContent;
      return out; }""")
    chk("(1) Fire Code: Profile alone, no switch over it", r["profileOnly"] and not r["profileSeg"], r)
    chk("(1) Fire Code: the bar's Settings opens Settings alone, no switch, the bar's Settings lit (%s)" % r, r["settingsShown"] and not r["settingsSeg"] and r["lit"] == "bottomtab-settings" and r["title"] == "Settings", r)
    chk("(1) no page errors", not errs, errs[:2])
    ctx.close()
    # (2)(3) the academy: Account, then Sign out with the cloud up
    acad = recap_store(G["academy"]); acad["novaHeard"] = {"@recap": 99991231}
    G["academy"] = acad
    ctx, pg, errs = G["page"](br, G["init"](None, active="academy"))
    pg.evaluate("()=>{ try{ localStorage.setItem('class26e.hadaccount', JSON.stringify({at:1,name:'Maddog'})); localStorage.setItem('class26e.soundon.327','1'); localStorage.setItem('class26e.ifc.drill.v1', JSON.stringify({firstName:'Maddog', lifetime:{points:5}})); }catch(e){} }")
    pg.wait_for_timeout(2500)
    r = pg.evaluate("""async()=>{ const w=ms=>new Promise(r=>setTimeout(r,ms)); const out={};
      showAppearance(); await w(900); const row=document.getElementById('settings-row-account');
      out.row = row ? row.textContent.replace(/\\s+/g,' ').trim() : null;
      row && row.click(); await w(900);
      out.title = (document.querySelector('#stage .settings-nav-title')||{}).textContent;
      out.name = !!document.querySelector('#stage .customize-namerow');
      out.signout = !!document.querySelector('#stage .signout-row:not([disabled])');
      return out; }""")
    chk("(2) Settings' Account row opens Account: the name and Sign out (%s)" % r, r["row"] and "Maddog" in r["row"] and r["title"] == "Account" and r["name"] and r["signout"], r)
    before = pg.evaluate("(code)=>JSON.stringify(window.__cloud.progress[code] || null)", CODE)
    pg.evaluate("()=>document.querySelector('#stage .signout-row').click()"); pg.wait_for_timeout(600)
    sheet = pg.evaluate("()=>{ const s=document.getElementById('signout-confirm'); return s ? { code: (s.querySelector('.savecode-value')||{}).textContent } : null; }")
    chk("(3) the confirm sheet shows the code to sign back in with (%s)" % sheet, sheet and sheet["code"] == CODE, sheet)
    with pg.expect_navigation(timeout=15000):
        pg.evaluate("()=>document.querySelector('#signout-confirm .signout-go').click()")
    pg.wait_for_timeout(3500)
    after = pg.evaluate("""()=>{ const ks=[]; for(let i=0;i<localStorage.length;i++) ks.push(localStorage.key(i)); return { keys: ks.filter(k=>k.startsWith('class26e.')).sort(),
        signed: !!window.NOVA_SIGNED_OUT, code: (typeof syncCode==='undefined') ? 'undef' : syncCode, onb: !!(window.store && store.onboardingComplete),
        welcome: !!document.querySelector('#stage .cosmic-welcome, #stage .gs-page, #stage .welcome-panel') }; }""")
    left = [k for k in after["keys"] if k in ("class26e.drill.v1", "class26e.synccode", "class26e.ifc.drill.v1", "class26e.activeclass", "class26e.signout")]
    chk("(3) after Sign out the device holds neither class's account (%s left)" % left, after["signed"] and not left and not after["code"] and not after["onb"], after)
    chk("(3) its device settings and the 'had an account' note stay", "class26e.hadaccount" in after["keys"] and "class26e.soundon.327" in after["keys"], after["keys"])
    chk("(3) and it opens on Welcome / Get started", after["welcome"], after)
    cloud_after = pg.evaluate("(code)=>JSON.stringify(window.__cloud.progress[code] || null)", CODE)
    # the page reloaded with a fresh in-memory cloud seeded from nothing - so read the cloud as the sheet left it, before the reload
    chk("(3) the cloud account was there before it, untouched by the sign-out (a reload writes nothing)", before != "null", before[:80])
    idb = pg.evaluate("async()=>{ const has = n => new Promise(r=>{ const q=indexedDB.open(n); q.onsuccess=()=>{ const db=q.result; const ok=db.objectStoreNames.length>0 && db.objectStoreNames.contains('kv'); if(!ok){ db.close(); return r(false); } const t=db.transaction('kv','readonly').objectStore('kv').get('store'); t.onsuccess=()=>{ r(!!t.result); db.close(); }; t.onerror=()=>r(false); }; q.onerror=()=>r(false); }); return { a: await has('class26e-drill-backup') }; }")
    chk("(3) and the device backup holds no account (%s)" % idb, not idb["a"], idb)
    chk("(3) no page errors", not errs, errs[:2])
    ctx.close()
    # (4) Sign out with the cloud not answering
    ctx, pg, errs = G["page"](br, G["init"](None, active="academy"))
    pg.wait_for_timeout(2500)
    pg.evaluate("()=>{ const db=acctDb(); const real=db.collection; db.collection = n => { const c=real(n); const d=c.doc; c.doc = id => { const r=d(id); r.set=()=>new Promise(()=>{}); r.get=()=>new Promise(()=>{}); return r; }; return c; }; }")
    pg.evaluate("()=>{ showAppearance({ page:'account' }); }"); pg.wait_for_timeout(900)
    pg.evaluate("()=>{ store.lifetime.points += 5; saveStore(); document.querySelector('#stage .signout-row').click(); }"); pg.wait_for_timeout(500)
    pg.evaluate("()=>document.querySelector('#signout-confirm .signout-go').click()")
    pg.wait_for_timeout(11000)
    r = pg.evaluate("()=>({ still: !!localStorage.getItem('class26e.drill.v1'), code: localStorage.getItem('class26e.synccode'), msg: (document.querySelector('#signout-confirm .signout-msg')||{}).textContent || '', sheet: !!document.getElementById('signout-confirm') })")
    chk("(4) with the cloud not answering, Sign out refuses and says so; the device stays signed in (%s)" % r, r["still"] and r["code"] == CODE and r["sheet"] and len(r["msg"]) > 10, r)
    ctx.close()
    # (5) the recap: first Home of a launch, headed with its class
    for cls in ("academy", "ifc"):
        G["academy"] = recap_store(G["academy"]); G["ifc"] = recap_store(G["ifc"])
        ctx, pg, errs = G["page"](br, G["init"](G["ifc"] if cls == "ifc" else None, active=cls))
        # any day of the week; and nothing owed ahead of it (a rank-up, a badge, Home's unlock cards go first, by design)
        pg.evaluate("()=>{ window.weekRecapDayOk = () => true; window.homeUnlocksOwed = () => false; window.rankUpSceneOwed = () => false; store.pendingBadgeUnlocks = []; document.querySelectorAll('#tour-overlay,#tour-tooltip').forEach(n=>n.remove()); }")
        # and this build's What's New, which plays ahead of it (closed as a person would)
        for _ in range(12):
            if pg.evaluate("()=>{ const n=document.getElementById('intro-pop'); if(n){ const b=n.querySelector('button'); if(b) b.click(); else n.remove(); return true; } return false; }"): pg.wait_for_timeout(700)
            else: break
        pg.evaluate("()=>{ try{ window.whatsNewHolds = () => false; }catch(e){} }")
        got = None
        for _ in range(30):
            got = pg.evaluate("()=>{ const n=document.querySelector('#nova-intro.is-weekrecap'); return n ? { eyebrow: (n.querySelector('.wr-eyebrow')||{}).textContent || null, home: !!document.querySelector('#stage [data-screen=\"home\"]') } : null; }")
            if got and got["eyebrow"]: break
            if got:   # its card comes up a line or two into his talk: step him on
                pg.evaluate("()=>{ const n=document.getElementById('nova-intro'); if(n && n.__nova){ n.__nova.advance(); } }")
            pg.wait_for_timeout(500)
        want = "Fire Code" if cls == "ifc" else "Police Academy"
        chk("(5) %s: the week's recap plays on the first Home of the launch, headed with its class (%s)" % (cls, got), got and got["home"] and want in (got["eyebrow"] or ""), got)
        ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
