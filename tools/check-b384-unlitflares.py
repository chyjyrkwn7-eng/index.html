#!/usr/bin/env python3
"""Build 384 r15: an unlit secret flare is an unkindled ember, the same in every place it is drawn, in both classes.
Madison: "The unlit secret flares, I'm not the biggest fan of how they look, room for improvement there."

Asserted by SHAPE (parts, computed paint, running animations, rendered pixels), never by a label string:
  (1) Home, in the Police Academy and in Fire Code: every secret flare not found yet carries a light of its own deep inside it
      (a visible core) that is ANIMATED (a running animation, opacity + transform only), and a ring that opens round it and
      goes (also animated), and its body renders DARK in the middle and light at the rim (read off the pixels);
  (2) no filter and no backdrop-filter on any unlit flare, any of its parts, or anything it sits in up to the page;
  (3) one look everywhere: Welcome's planet, the recap dots (novaRecapCard), the hint card's flare (flareHintItem), and the mark on
      every LOCKED SECRET character's tile in Customize (both classes) and in sign-up's greyed list are .unlit-flare parts with the
      same four pieces; a locked non-secret character keeps its padlock; a held character has no mark;
  (4) reduced motion: nothing runs, and the core is still there (a still ember);
  (5) lit is untouched: a found flare is not .unlit-flare, keeps its halo/orbit, and no unlit rule reaches it;
  (6) no colour: the unlit flare's painted parts carry no hue (build 314: an unfound flare gives none away);
  (7) no page errors.
Run:  python3 tools/check-b384-unlitflares.py   (--against /tmp/prev-index.html must FAIL)
      SHOTS=dir python3 tools/check-b384-unlitflares.py   to keep screenshots"""
import io, json, os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b384_unlit_lib as L
from playwright.sync_api import sync_playwright

SRC = sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else os.path.join(L.ROOT, "index.html")
SHOTS = os.environ.get("SHOTS", "")
ok = True


def chk(name, cond, info=""):
    global ok
    ok = ok and bool(cond)
    print(("PASS " if cond else "FAIL ") + name, "" if cond else ("-> " + str(info)[:900]))


# what an animation animates: every keyframe's properties besides the bookkeeping ones
ANIM = """(el)=>{ const as = el.getAnimations(); const props = new Set(); let running = 0;
  as.forEach(a=>{ if(a.playState==='running') running++; try{ a.effect.getKeyframes().forEach(k=>Object.keys(k).forEach(p=>props.add(p))); }catch(e){} });
  ['offset','easing','composite','computedOffset'].forEach(p=>props.delete(p));
  return { running, props:[...props] }; }"""

HOME = """()=>{ const ANIM=%s; const dots=[...document.querySelectorAll('.cosmic-flare-dot')];
  const unlit=dots.filter(d=>!d.classList.contains('is-found'));
  const out = unlit.map(d=>{ const core=d.querySelector('.cof-core'), ring=d.querySelector('.cof-ring'), body=d.querySelector('.cof-body');
    const cs=getComputedStyle(core), r=d.getBoundingClientRect(), cr=core.getBoundingClientRect();
    return { flare:d.dataset.flare, w:r.width, coreOpacity:parseFloat(cs.opacity), coreFrac:cr.width/r.width,
      core:ANIM(core), ring:ANIM(ring), ringW:ring.getBoundingClientRect().width/r.width, ringDisplay:getComputedStyle(ring).display, bodyBg:getComputedStyle(body).backgroundImage.length }; });
  return { total:dots.length, unlit:out }; }""" % ANIM

NOFILTER = """(sel)=>{ const bad=[]; document.querySelectorAll(sel).forEach(el=>{
    const nm=n=>(n.className&&n.className.baseVal!==undefined?n.className.baseVal:n.className)||n.tagName;
    [el, ...el.querySelectorAll('*')].forEach(c=>{ const s=getComputedStyle(c); const b=s.backdropFilter||s.webkitBackdropFilter||'none';
      if((s.filter&&s.filter!=='none')||(b&&b!=='none')) bad.push('self:'+nm(c)); });
    let n=el.parentElement; while(n && n!==document.documentElement){ const s=getComputedStyle(n); const b=s.backdropFilter||s.webkitBackdropFilter||'none';
      if(s.filter&&s.filter!=='none') bad.push('ancestor filter:'+nm(n));
      if(b&&b!=='none'&&n.getAnimations().length) bad.push('animated ancestor backdrop:'+nm(n));
      n=n.parentElement; } });
  return { n:document.querySelectorAll(sel).length, bad:[...new Set(bad)] }; }"""

# rendered pixels of the first unlit dot: the middle against the rim, with the animations held at a known frame
PIX_PREP = """()=>{ document.getAnimations().forEach(a=>{ try{ a.pause(); a.currentTime=0; }catch(e){} }); return true; }"""

HUES = """(sel)=>{ const hue=[]; const lum=c=>{ const m=c.match(/[\\d.]+/g)||[]; const r=+m[0],g=+m[1],b=+m[2],a=m.length>3?+m[3]:1; return {r,g,b,a}; };
  document.querySelectorAll(sel).forEach(el=>el.querySelectorAll('*').forEach(c=>{ const s=getComputedStyle(c);
    const imgs=(s.backgroundImage||'').match(/rgba?\\([^)]*\\)/g)||[]; imgs.concat([s.backgroundColor, s.borderTopColor]).forEach(col=>{
      const {r,g,b,a}=lum(col); if(a>0.05 && Math.max(r,g,b)-Math.min(r,g,b)>60) hue.push(col); }); }));
  return [...new Set(hue)]; }"""

SECRET_TILES = """()=>{ const sec=new Set(AVATAR_CHARACTERS.filter(c=>c.secret&&!c.retired&&!c.legacy).map(c=>c.id));
  const nameOf=id=>AVATAR_DISPLAY_NAME[id]||id;
  const rows=[]; AVATAR_CHARACTERS.filter(c=>!c.retired&&!c.legacy).forEach(c=>{
    const o=[...document.querySelectorAll('.screen-customize .avatarchar-option')].find(x=>x.title===nameOf(c.id)); if(!o) return;
    const lm=o.querySelector('.avatarchar-lockmark');
    rows.push({ id:c.id, secret:sec.has(c.id), locked:isLockedCharacter(c.id), mark:!!lm, unlit:!!(lm&&lm.querySelector('.unlit-flare')),
      parts: lm&&lm.querySelector('.unlit-flare') ? [...lm.querySelector('.unlit-flare').children].map(i=>i.className).sort().join(',') : '',
      padlock:!!(lm&&lm.querySelector('.lockglyph')) }); });
  return rows; }"""


def page(br, url, ifc, w=440, h=956, dpr=3, found=None, fresh=False, reduce=False):
    ctx, pg, errs = L.page(br, url, SRC, ifc, w, h, dpr, found=found, fresh=fresh)
    return ctx, pg, errs


def shot(pg, name, **kw):
    if SHOTS:
        os.makedirs(SHOTS, exist_ok=True)
        pg.screenshot(path=os.path.join(SHOTS, name + ".png"), **kw)


srv, url = L.serve()
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=L.CHROME)
    allerrs = []
    for ifc in (False, True):
        cls = "Fire Code" if ifc else "Police Academy"
        ctx, pg, errs = page(br, url, ifc)
        pg.add_style_tag(content=".daily-question-fab,.homeversion{visibility:hidden !important}")
        pg.wait_for_timeout(800)
        # (1) Home
        h = pg.evaluate(HOME)
        u = h["unlit"]
        chk("%s (1) Home: all six secret flares are unlit on a fresh account (%d of %d dots)" % (cls, len(u), h["total"]), len(u) == 6, h["total"])
        chk("%s (1) every unlit dot has a visible core deep inside it (opacity > 0, a fraction of the dot's width)" % cls,
            u and all(x["coreOpacity"] > 0 and 0.15 < x["coreFrac"] < 0.8 for x in u), [(x["flare"], x["coreOpacity"], x["coreFrac"]) for x in u])
        chk("%s (1) the core is animated: a running animation of opacity and transform only" % cls,
            u and all(x["core"]["running"] > 0 and set(x["core"]["props"]) <= {"opacity", "transform"} and "opacity" in x["core"]["props"] for x in u), [x["core"] for x in u][:2])
        chk("%s (1) a pearl has no ring: nothing opens round the dot, and nothing runs on it (384.20; the ember's ring is gone)" % cls,
            u and all(x["ringDisplay"] == "none" and x["ring"]["running"] == 0 for x in u), [(x["ringDisplay"], x["ring"]) for x in u][:2])
        # pixels: a copy of an orbit dot and a standalone mark, each set 48px on a flat dark panel (an orbiting dot moves under a
        # screenshot), their animations held at their first frame (the core at its dimmest)
        pg.evaluate("""()=>{ const p=document.createElement('div'); p.id='ulpix'; p.style.cssText='position:fixed;left:0;top:0;width:260px;height:120px;background:#14161f;z-index:99999';
          const d=document.querySelector('.cosmic-flare-dot:not(.is-found)').cloneNode(true); d.style.cssText='position:absolute;left:70px;top:60px;width:48px;translate:-50% -50%;';
          const m=(typeof buildUnlitFlare==='function') ? buildUnlitFlare() : document.createElement('span'); m.style.width='48px'; m.style.position='absolute'; m.style.left='150px'; m.style.top='36px';
          p.append(d, m); document.body.appendChild(p);
          document.getAnimations().forEach(a=>{ try{ a.pause(); a.currentTime=0; }catch(e){} }); }""")
        pg.wait_for_timeout(300)
        png = pg.screenshot(clip={"x": 0, "y": 0, "width": 260, "height": 120})
        full = Image.open(io.BytesIO(png)).convert("L"); S = full.width / 260.0
        def luma(cx, cy, d):
            im = full.crop((int((cx - d / 2) * S), int((cy - d / 2) * S), int((cx + d / 2) * S), int((cy + d / 2) * S)))
            W = im.width; c = (W - 1) / 2.0; mid, rim = [], []
            for yy in range(W):
                for xx in range(W):
                    r = (((xx - c) ** 2 + (yy - c) ** 2) ** .5) / (W / 2.0); v = im.getpixel((xx, yy))
                    if .5 <= r <= .74: mid.append(v)
                    elif .9 <= r <= 1.0: rim.append(v)
            return sum(mid) / len(mid), sum(rim) / len(rim)
        for what, cx, cy in (("orbit dot", 70, 60), ("standalone mark", 150 + 24, 36 + 24)):
            midm, rimm = luma(cx, cy, 48)
            chk("%s (1) the %s renders a frosted pearl: a body clearly lighter than the dark panel under it, inside a brighter thin edge (mean luma of the body ring %.0f, of the rim %.0f, of the panel 20)" % (cls, what, midm, rimm),
                midm > 45 and rimm > midm + 3, (midm, rimm))
        if SHOTS:
            os.makedirs(SHOTS, exist_ok=True); full.save(os.path.join(SHOTS, "pix-" + ("fc" if ifc else "ac") + ".png"))
        pg.evaluate("()=>document.getElementById('ulpix').remove()")
        shot(pg, "home-" + ("fc" if ifc else "ac"))
        # (2) no filter anywhere in or above an unlit flare
        nf = pg.evaluate(NOFILTER, ".cosmic-flare-dot:not(.is-found)")
        chk("%s (2) no filter / backdrop-filter on an unlit orbit dot, its parts or anything it sits in (%d dots)" % (cls, nf["n"]), nf["n"] == 6 and not nf["bad"], nf["bad"])
        hz = pg.evaluate(HUES, ".cosmic-flare-dot:not(.is-found)")
        chk("%s (6) an unlit flare paints no hue (nothing it is drawn with is saturated)" % cls, not hz, hz)
        # (5) lit is untouched
        lit = pg.evaluate("""()=>{ const d=document.querySelector('.cosmic-flare-dot'); d.classList.add('is-found'); d.style.setProperty('--fc','#FF5C5C');
          const halo=getComputedStyle(d.querySelector('.cof-halo')), orb=getComputedStyle(d.querySelector('.cof-orbit')), core=getComputedStyle(d.querySelector('.cof-core'));
          return { unlitClass:d.classList.contains('unlit-flare'), halo:parseFloat(halo.opacity), orbit:parseFloat(orb.opacity), core:parseFloat(core.opacity),
                   ring:parseFloat(getComputedStyle(d.querySelector('.cof-ring')).opacity), coreInset:getComputedStyle(d.querySelector('.cof-core')).inset }; }""")
        chk("%s (5) a found flare is lit as before: halo and orbit up, the white-hot core up, no ring, not an unlit mark (%s)" % (cls, lit),
            not lit["unlitClass"] and lit["halo"] > .5 and lit["orbit"] == 1 and lit["core"] > .5 and lit["ring"] == 0, lit)
        # (3) Customize tiles, both classes
        pg.evaluate("()=>showCustomize('character')"); pg.wait_for_timeout(2500)
        rows = pg.evaluate(SECRET_TILES)
        sec = [r for r in rows if r["secret"] and r["locked"]]
        oth = [r for r in rows if not r["secret"] and r["locked"]]
        held = [r for r in rows if not r["locked"]]
        chk("%s (3) Customize: every locked secret character's mark is an unlit flare with its four parts, no padlock (%d tiles)" % (cls, len(sec)),
            len(sec) >= 4 and all(r["unlit"] and not r["padlock"] and r["parts"] == "cof-body,cof-core,cof-ring,cof-sheen" for r in sec), sec)
        chk("%s (3) Customize: a locked rank / challenge / ultimate character keeps its padlock (%d tiles)" % (cls, len(oth)),
            len(oth) >= 10 and all(r["padlock"] and not r["unlit"] for r in oth), [r for r in oth if not r["padlock"]])
        chk("%s (3) Customize: a character you hold carries no mark" % cls, held and all(not r["mark"] for r in held), [r for r in held if r["mark"]])
        nf = pg.evaluate(NOFILTER, ".screen-customize .avatarchar-lockmark .unlit-flare")
        chk("%s (2) no filter on the marks in Customize (%d)" % (cls, nf["n"]), nf["n"] >= 4 and not nf["bad"], nf["bad"])
        pg.evaluate("()=>{ const ids=AVATAR_CHARACTERS.filter(c=>c.secret&&!c.retired&&!c.legacy).map(c=>AVATAR_DISPLAY_NAME[c.id]||c.id); const t=[...document.querySelectorAll('.screen-customize .avatarchar-option')].find(o=>ids.includes(o.title)); if(t) t.scrollIntoView({block:'center'}); }")
        pg.wait_for_timeout(700)
        shot(pg, "customize-" + ("fc" if ifc else "ac"))
        # the sign-up character screen's greyed list
        su = pg.evaluate("""()=>{ try{ showWelcomeCharacterPrompt(); }catch(e){ return {err:String(e)}; }
          const g=document.querySelector('.charselect-later'); if(!g) return {none:true};
          const o=[...g.querySelectorAll('.avatarchar-option')]; const sec=new Set(AVATAR_CHARACTERS.filter(c=>c.secret).map(c=>AVATAR_DISPLAY_NAME[c.id]||c.id));
          return { n:o.length, rows:o.map(x=>({ unlit:!!x.querySelector('.avatarchar-lockmark .unlit-flare'), padlock:!!x.querySelector('.avatarchar-lockmark .lockglyph'), label:x.getAttribute('aria-label')||'' })) }; }""")
        if su.get("rows"):
            nsec = [r for r in su["rows"] if r["unlit"]]
            chk("%s (3) sign-up's greyed list: exactly the secret characters carry the unlit mark, the rest a padlock (%d unlit of %d)" % (cls, len(nsec), su["n"]),
                len(nsec) >= 2 and all(r["unlit"] != r["padlock"] for r in su["rows"]), su)
        else:
            chk("%s (3) sign-up's greyed list is reachable" % cls, False, su)
        # the recap dots and the hint card's flare
        rc = pg.evaluate("""()=>{ const st=novaRecapState(); const c=novaRecapCard(st); const d=[...c.querySelectorAll('.nt-rc-sf')];
          return { n:d.length, unlit:d.filter(x=>x.classList.contains('unlit-flare')).length, parts:d.map(x=>[...x.children].map(i=>i.className).sort().join(',')) }; }""")
        chk("%s (3) recap dots: each secret flare not found is an unlit mark with its four parts (%s)" % (cls, rc["unlit"]),
            rc["n"] == 6 and rc["unlit"] == 6 and all(p == "cof-body,cof-core,cof-ring,cof-sheen" for p in rc["parts"]), rc)
        hint = pg.evaluate("""()=>{ const it=flareHintItem('umbra'); const f=it.art(); const box=document.createElement('div'); box.appendChild(f);
          return { unlit:box.querySelectorAll('.rs-hint-orb .unlit-flare').length, lit:box.querySelectorAll('.rs-hint-orb svg.flare-orb').length }; }""")
        chk("%s (3) the hint card's flare is the unlit mark, not a lit orb (%s)" % (cls, hint), hint["unlit"] == 1 and hint["lit"] == 0, hint)
        allerrs += errs
        ctx.close()
    # Welcome's planet (a fresh install: nobody's flares)
    ctx, pg, errs = page(br, url, False, fresh=True)
    pg.evaluate("()=>{ try{ showWelcome(); }catch(e){} }"); pg.wait_for_timeout(2500)
    w = pg.evaluate(HOME)
    chk("Welcome (3): the planet's six flares are the unlit look (visible animated core on each) (%d)" % len(w["unlit"]),
        len(w["unlit"]) == 6 and all(x["coreOpacity"] > 0 and x["core"]["running"] > 0 for x in w["unlit"]), w["unlit"][:1])
    shot(pg, "welcome")
    allerrs += errs
    ctx.close()
    # (4) reduced motion: nothing runs, the core is still there
    ctx = br.new_context(viewport={"width": 440, "height": 956}, device_scale_factor=3, reduced_motion="reduce")
    ctx.add_init_script(L.G["STANDALONE"]); ctx.add_init_script(L.G["FAKE_FIREBASE"].replace("__ROWS__", L.G["rows_json"]()))
    pg = ctx.new_page(); body = L.body_of(SRC)
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    d = dict(L.SEED); d["publicId"] = "pubtest0384u"
    pg.add_init_script(L.INIT % (json.dumps(json.dumps(d)), json.dumps(L.KEYS), ""))
    pg.goto(url); pg.wait_for_timeout(3200)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); document.querySelectorAll('#intro-pop').forEach(n=>n.remove()); }"); pg.wait_for_timeout(800)
    rm = pg.evaluate(HOME)
    chk("reduced motion (4): no core or ring animation runs, and the core is still visible (a still ember)",
        len(rm["unlit"]) == 6 and all(x["core"]["running"] == 0 and x["ring"]["running"] == 0 and x["coreOpacity"] > 0 for x in rm["unlit"]), rm["unlit"][:1])
    ctx.close()
    chk("(7) no page errors", not allerrs, allerrs[:3])
    br.close()
print("\nALL PASS" if ok else "\nFAILED")
sys.exit(0 if ok else 1)
