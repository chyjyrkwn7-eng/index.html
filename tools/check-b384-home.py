"""Build 384: Home's small buttons, the chat sheet, Nova's tag and Manage friends.
Madison: "The fire in the ifc class, it's not centered, nearly but it's not." / "The class button, I like the fire and police icon
but I don't think I love them." / "The daily question button ... The ready version is it just spinning and that's distracting, the
loading version is kinda lame and it's not much." / "When you hit the chat button and it pulls up ... the background behind the
chat is see through and then you see it change to blurry." / "the spot that says instructor on the right, center that." / "where
it has your code and the copy button, remove the copy button and just put that copy button you see. The word copy don't need to be
there." / "The 'enter a friends code' doesn't come off as a text box ... give it a more 'type here' vibe?"
iPhone 17 Pro Max (440x956), dark:
(1) the class button's icon, in both classes, is a SOLID shape (its main fill opaque) and mirror-symmetric about the button's
    middle (the left and right halves of its pixels differ by under 6 levels on average), its ink centred within 1px across;
(2) the daily question ready: nothing on it turns (no running rotation on any part), its ring is drawn whole and lit;
(3) answered: the middle says the time to the next question (the app's own 5pm, "Nh" / "Nm"), the "?" is not shown, and a lit
    head sits at the end of the arc (its angle the arc's, within 3 degrees);
(4) the chat sheet as it opens and once open: no backdrop blur at 0, 120, 320 and 700ms, its fill opaque (alpha >= .9);
(5) Nova's "Instructor" tag on the chat's Friends tab is on his row's middle (within 1.5px) and at its right edge;
(6) Manage friends: the code's copy control is an icon button - no word, an svg, 44px+ - and a tap turns it to a tick; the
    friend-code field has an inner edge, and a cursor blinking in it while it is empty and untapped, gone once tapped;
(7) no page errors;
(8) (Madison: "the chat button on home looks amazing, revert the chat button it looks like that everywhere ... the new back button
    needs to match it as well") the chat button and the round back buttons on Settings, Account, Mode select, Customize and Profile
    are Home's chat button - the same body, gradient, rim, frost and shadow.
Run:  python3 tools/check-b384-home.py   (--against OLD/index.html must FAIL)"""
import os, sys, io, re, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b384h"}
exec(src, G)
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = G["g"]["INSET_RE"]
    def _old(ins):
        t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
        return IR.sub(lambda m: v[m.group(1)], OLD)
    G["g"]["patched"] = _old
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
# (384 full check) and no unlock cards: the shared seed has 234 hundos and no seenUnlocks, so Home owes it Fireworks and Underwater
# (383 the same) and their dim lands over the corners this measures
CLEAN = ("try{ homeUnlocksOwed = () => false; }catch(e){} "
         "document.querySelectorAll('.intro-popup,.daily-alert,#intro-pop,.nova-talk,.app-banner,.unlock-card,.rs-spot,.rs-fly').forEach(e=>e.remove());")
def icon_shape(pg):
    r = pg.evaluate("""()=>{ const b=document.querySelector('.class-bubble'); const s=b && b.querySelector('svg'); if(!s) return null;
      const p=s.querySelector('path'); const c=getComputedStyle(p); const br=b.getBoundingClientRect(), sr=s.getBoundingClientRect();
      return { fillOp: +c.fillOpacity, fill: c.fill, b:[br.x,br.y,br.width,br.height], s:[sr.x,sr.y,sr.width,sr.height] }; }""")
    if not r: return None
    x, y, w, h = r["b"]
    png = pg.screenshot(clip={"x": x, "y": y, "width": w, "height": h}, scale="device")
    a = np.asarray(Image.open(io.BytesIO(png)).convert("RGB")).astype(float)
    k = a.shape[1] / w
    # the icon's box only (the svg), mirrored about the BUTTON's middle
    sx0 = int((r["s"][0] - x) * k); sx1 = int((r["s"][0] + r["s"][2] - x) * k); sy0 = int((r["s"][1] - y) * k); sy1 = int((r["s"][1] + r["s"][3] - y) * k)
    mid = a.shape[1] / 2; half = min(mid - sx0, sx1 - mid)
    L = a[sy0:sy1, int(mid - half):int(mid)]; R = a[sy0:sy1, int(mid):int(mid + half)][:, ::-1]
    n = min(L.shape[1], R.shape[1]); asym = float(np.abs(L[:, -n:] - R[:, -n:]).mean())
    sat = a.max(2) - a.min(2); m = sat > 50; ys, xs = np.nonzero(m)
    cx = (xs.mean() / k - w / 2) if len(xs) else 99
    r.update({"asym": round(asym, 2), "cx": round(float(cx), 2)})
    return r
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    errs_all = []
    for cls in ("academy", "ifc"):
        ctx, pg, errs = G["page"](br, G["init"](G["ifc"] if cls == "ifc" else G["academy"], active=cls))
        pg.evaluate("()=>{ %s showHome(); }" % CLEAN); pg.wait_for_timeout(1800)
        ic = icon_shape(pg)
        chk("(1) %s: the class icon is solid and symmetric, centred across (%s)" % (cls, ic and {k: ic[k] for k in ("fillOp", "asym", "cx")}),
            ic and ic["fillOp"] >= .9 and ic["asym"] < 6 and abs(ic["cx"]) <= 1, ic)
        errs_all += errs
        if cls == "ifc":
            ctx.close(); continue
        # (2) ready
        pg.evaluate("()=>{ %s store.dailyQuestionDate = null; showHome(); }" % CLEAN); pg.wait_for_timeout(2200)
        rd = pg.evaluate("""()=>{ const b=document.querySelector('.daily-question-fab'); if(!b) return null;
          const turning = b.getAnimations({ subtree: true }).filter(a => { try{ const kf = a.effect.getKeyframes(); return kf.some(f => /rotate/.test(f.transform || '')); }catch(e){ return false; } }).map(a => a.animationName || a.transitionProperty);
          const svg=b.querySelector('.dq-ring > svg'); return { ready: b.classList.contains('is-ready'), turning, ringVis: svg ? getComputedStyle(svg).visibility : null,
            ringOp: +getComputedStyle(b.querySelector('.dq-ring')).opacity }; }""")
        chk("(2) the daily question ready: nothing turns (%s), the ring whole and lit" % (rd and rd["turning"]),
            rd and rd["ready"] and not rd["turning"] and rd["ringVis"] == "visible" and rd["ringOp"] > .9, rd)
        # (3) answered
        pg.evaluate("()=>{ %s store.dailyQuestionDate = dailyPeriodKey(); showHome(); }" % CLEAN); pg.wait_for_timeout(2200)
        wt = pg.evaluate("""()=>{ const b=document.querySelector('.daily-question-fab'); if(!b) return null; const L=b.querySelector('.dq-left'), g=b.querySelector('.dq-glyph');
          const ring=b.querySelector('.dq-ring'); const head=b.querySelector('.dq-ring-head');
          const now=Date.now(), nx=new Date(now); nx.setHours(17,0,0,0); if(nx.getTime() <= now) nx.setDate(nx.getDate()+1);
          const mins=Math.ceil((nx.getTime()-now)/60000), want = mins >= 60 ? Math.floor(mins/60)+'h' : mins+'m';
          let ang=null; if(head){ const hr=head.getBoundingClientRect(), rr=ring.getBoundingClientRect(); ang = Math.atan2((hr.y+hr.height/2)-(rr.y+rr.height/2), (hr.x+hr.width/2)-(rr.x+rr.width/2)) * 180 / Math.PI; }
          const p = ring ? parseFloat(ring.dataset.p || '0') : 0;
          return { done: b.classList.contains('is-done'), left: L ? L.textContent : null, leftShown: !!L && getComputedStyle(L).display !== 'none', want,
                   glyphShown: !!g && getComputedStyle(g).display !== 'none', headOp: head ? +getComputedStyle(head).opacity : 0, ang, wantAng: p * 360 - 90, p }; }""")
        da = wt and wt["ang"] is not None and min(abs((wt["ang"] - wt["wantAng"] + 540) % 360 - 180), 999)
        chk("(3) answered: the middle says the time left (%s, %s), no '?', a lit head at the arc's end (%s vs %s deg)" % (wt and wt["left"], wt and wt["want"], wt and wt["ang"] and round(wt["ang"], 1), wt and round(wt["wantAng"], 1)),
            wt and wt["done"] and wt["leftShown"] and wt["left"] == wt["want"] and not wt["glyphShown"] and wt["headOp"] > .9 and da is not None and da <= 3, wt)
        # (4) the chat sheet opening
        samples = pg.evaluate("""async ()=>{ const w=ms=>new Promise(r=>setTimeout(r,ms)); const out=[]; chatDockTab='friends'; const t0=performance.now(); openChatDock();
          for(const t of [0,120,320,700]){ const now=performance.now()-t0; if(t>now) await w(t-now); const p=document.querySelector('.chatdock-panel'); const c=getComputedStyle(p);
            const bg=c.backgroundColor; const m=(c.backgroundImage + ' ' + bg).match(/rgba?\\([^)]*\\)/g) || []; const last = m.length ? m[m.length-1] : bg;
            const a = (last.match(/[\\d.]+/g) || []); out.push({ t, bf: c.backdropFilter || c.webkitBackdropFilter || 'none', alpha: a.length > 3 ? +a[3] : 1 }); }
          return out; }""")
        chk("(4) the chat sheet never blurs what is behind it as it opens or after (%s), its fill opaque" % [(s["t"], s["bf"], s["alpha"]) for s in samples],
            all(s["bf"] in ("none", "") for s in samples) and all(s["alpha"] >= .9 for s in samples), samples)
        # (5) Nova's tag
        pg.evaluate("()=>{ try{ window.novaIsFriend = () => true; }catch(e){} closeChatDock(); }"); pg.wait_for_timeout(500)
        pg.evaluate("()=>{ chatDockTab='friends'; openChatDock(); }"); pg.wait_for_timeout(1100)
        nv = pg.evaluate("""()=>{ const k=document.querySelector('.chatdock-chatrow.is-nova .chatdock-chatrow-kind'); if(!k) return null; const row=k.closest('.chatdock-chatrow');
          const a=k.getBoundingClientRect(), b=row.getBoundingClientRect(); return { dy: (a.top + a.height/2) - (b.top + b.height/2), dr: b.right - a.right, w: b.width }; }""")
        chk("(5) Nova's 'Instructor' tag on his row's middle (%s px) and at its right edge (%s px in)" % (nv and round(nv["dy"], 2), nv and round(nv["dr"], 1)),
            nv and abs(nv["dy"]) <= 1.5 and 8 <= nv["dr"] <= 32, nv)
        pg.evaluate("()=>closeChatDock()"); pg.wait_for_timeout(500)
        # (6) Manage friends
        pg.evaluate("()=>{ %s showFriends(); }" % CLEAN); pg.wait_for_timeout(1300)
        cp = pg.evaluate("""()=>{ const w=document.querySelector('.friend-mycode-wrap'); const b=w && w.querySelector('button'); if(!b) return null; const r=b.getBoundingClientRect();
          return { text: b.textContent.trim(), svg: !!b.querySelector('svg'), w: r.width, h: r.height, label: b.getAttribute('aria-label') }; }""")
        pg.evaluate("()=>{ try{ navigator.clipboard.writeText = () => Promise.resolve(); }catch(e){} document.querySelector('.friend-mycode-wrap button').click(); }"); pg.wait_for_timeout(300)
        tick = pg.evaluate("()=>{ const b=document.querySelector('.friend-mycode-wrap button'); const t=b && b.querySelector('.friend-copy-tick'); return { copied: !!b && b.classList.contains('is-copied'), tickOp: t ? +getComputedStyle(t).opacity : 0 }; }")
        chk("(6) the code's copy control is an icon button - no word, an svg, 44px+ (%s), and a tap turns it to a tick (%s)" % (cp, tick),
            cp and cp["text"] == "" and cp["svg"] and cp["w"] >= 44 and cp["h"] >= 44 and cp["label"] and tick["copied"] and tick["tickOp"] > .5, [cp, tick])
        f1 = pg.evaluate("""()=>{ const i=document.querySelector('.friend-add-input'); const f=i.parentElement; const be=getComputedStyle(f,'::before');
          return { edge: getComputedStyle(i).boxShadow, caret: be.content !== 'none' && be.animationName !== 'none' ? be.animationName : null }; }""")
        pg.evaluate("()=>document.querySelector('.friend-add-input').focus()"); pg.wait_for_timeout(300)
        f2 = pg.evaluate("()=>{ const f=document.querySelector('.friend-add-input').parentElement; const be=getComputedStyle(f,'::before'); return { caret: be.animationName !== 'none' ? be.animationName : null }; }")
        chk("(6) the friend-code field: an inner edge (%s), a cursor blinking while empty and untapped (%s), gone once tapped (%s)" % (f1["edge"][:40], f1["caret"], f2["caret"]),
            "inset" in (f1["edge"] or "") and f1["caret"] and not f2["caret"], [f1, f2])
        errs_all += errs
        ctx.close()
    # (8) the chat button and the round back buttons on every screen are Home's chat button
    ctx, pg, errs = G["page"](br, G["init"](G["academy"], active="academy"))
    ST = """(sel)=>{ const e=document.querySelector(sel); if(!e) return null; const c=getComputedStyle(e); return [c.backgroundColor, c.backgroundImage, c.borderTopColor, c.backdropFilter || c.webkitBackdropFilter, c.boxShadow].join(' | '); }"""
    pg.evaluate("()=>{ %s showHome(); }" % CLEAN); pg.wait_for_timeout(1200)
    home = pg.evaluate(ST, "#chatdock-btn")
    diff = []
    for name, js in (("Settings", "showAppearance()"), ("Account", "showAppearance({ page: 'account' })"), ("Mode select", "showModeSelect()"), ("Customize", "showCustomize()"), ("Profile", "showProfile('profile')")):
        pg.evaluate("()=>{ %s %s; }" % (CLEAN, js)); pg.wait_for_timeout(1100)
        for what, sel in (("chat", "#chatdock-btn"), ("back", "#stage .ios-nav > .back-link.ios-nav-back, #stage .settings-nav-back")):
            v = pg.evaluate(ST, sel)
            if v is not None and v != home: diff.append((name, what, v[:90]))
    chk("(8) the chat button and the round back buttons on every screen are Home's chat button (%d differ)" % len(diff), not diff and home and "blur" in home, [home[:90] if home else None] + diff[:4])
    errs_all += errs; ctx.close()
    chk("(7) no page errors", not errs_all, errs_all[:3])
    br.close()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
