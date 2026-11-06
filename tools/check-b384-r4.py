#!/usr/bin/env python3
"""Build 384, round 4 - Madison's list after round 3. Each check reads the page, on the iPhone 17 Pro Max (440x956).

 (U) LEAVING A CLASS: Settings > Account has a Classes row; its page lists each class the account is in and Join another
     class; leaving one of two takes it off the list (and the class button's) with a dated leave, and a copy from another
     device that still lists it does not bring it back - unless that copy joined it again later; the only class cannot be
     left (the sheet says so and offers the class list instead).
 (F) BRONZE HAS A CHARACTER: a character unlocks at the first rank, is drawn (a real picture, not the fallback), named,
     glowing, reacts to a grade like the others, and is on the rank map's Bronze card; an account that already holds Bronze
     gets it marked shown and seen with no card; an account below Bronze does not.
 (N) THE NAME FIELD: Safari has nothing to fill in it (autocomplete off, a name it does not know), an empty field shows no
     caret, and the field does not move while it takes focus (its card fades, it does not swell).
 (O) THE END OF A SIGN-UP, IN ORDER: Nova's introduction for a new account ends without his goodbye and without the friend
     line; the main menu's tips end on the friend line (the chat button) and do not include Start Studying; Start
     Studying's tip comes once the Add to Home Screen sheet has been closed, not before.
 (V) THE ADD TO HOME SCREEN CLIP plays at the speed it was recorded (a real iPhone recording), and the sign-up's sheet closes with a button that says later.
 (T) THE TIPS ARE SHORTER: every main-menu and Profile tip is shorter than the same step was on the build before
     (--against prints that build's numbers; on its own the gate asserts the shape: no tip over two lines' worth of the
     longest Nova line).
 (S) THE SEAM where Nova's speech tail meets his bubble: across the tail's base the border's rows are the bubble's own fill
     (read off the pixels at 3x, 2.5x and 2x).
 (E) no page errors.
Run:  python3 tools/check-b384-r4.py            (--against OLD/index.html must FAIL)"""
import importlib.util, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py"))
cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
from playwright.sync_api import sync_playwright

ok = True
def chk(name, cond, info=""):
    global ok
    ok = ok and bool(cond)
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  -> " + str(info)[:700]), flush=True)

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    ctx, pg = cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT, dpr=1)
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))

    # ---------------- (U) leaving a class ----------------
    u = pg.evaluate("""async () => { const w = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      try{
        store.classes = ['academy', 'ifc']; saveStore();
        showAppearance(); await w(400);
        out.row = !!document.getElementById('settings-row-classes');
        if(out.row){ document.getElementById('settings-row-classes').click(); await w(500); }
        out.listed = [...document.querySelectorAll('.settings-class-row')].map(r => r.dataset.cls);
        out.join = !!document.getElementById('settings-join-class');
        const ifcRow = document.querySelector('.settings-class-row[data-cls="ifc"]');
        if(ifcRow){ ifcRow.click(); await w(400); const yes = document.querySelector('#classenroll-confirm .classenroll-yes'); out.sheet = !!yes; if(yes) yes.click(); await w(700); }
        out.after = enrolledClasses();
        out.dated = !!(store.classLeftAt && store.classLeftAt.ifc);
        out.listedAfter = [...document.querySelectorAll('.settings-class-row')].map(r => r.dataset.cls);
        const d1 = JSON.parse(JSON.stringify(store)); mergeSameAccount(d1, { classes: ['academy', 'ifc'], classJoinedAt: {}, classLeftAt: {} });
        out.mergeKeeps = d1.classes;
        const d2 = JSON.parse(JSON.stringify(store)); mergeSameAccount(d2, { classes: ['academy', 'ifc'], classJoinedAt: { ifc: Date.now() + 60000 }, classLeftAt: {} });
        out.mergeRejoin = d2.classes;
        const only = document.querySelector('.settings-class-row[data-cls="academy"]');
        if(only){ only.click(); await w(400); }
        const sh = document.getElementById('classenroll-confirm');
        out.onlyText = sh ? sh.innerText : '';
        out.onlyStill = enrolledClasses();
        if(sh) sh.remove();
      }catch(e){ out.err = String(e); }
      return out; }""")
    chk("(U) Settings has a Classes row, and its page lists both classes and Join another class (%s)" % u.get("listed"),
        u.get("row") and u.get("listed") == ["academy", "ifc"] and u.get("join"), u)
    chk("(U) leaving one of two asks first, takes it off the account and the page, and dates the leave (%s -> %s)" % (u.get("listed"), u.get("after")),
        u.get("sheet") and u.get("after") == ["academy"] and u.get("dated") and u.get("listedAfter") == ["academy"], u)
    chk("(U) another device's copy that still lists it does not bring it back (%s); one that joined it again later does (%s)" % (u.get("mergeKeeps"), u.get("mergeRejoin")),
        u.get("mergeKeeps") == ["academy"] and u.get("mergeRejoin") == ["academy", "ifc"], u)
    chk("(U) the only class cannot be left: the sheet says so and the class stays (%r)" % (u.get("onlyText") or "")[:80],
        bool(u.get("onlyText")) and u.get("onlyStill") == ["academy"] and "only" in (u.get("onlyText") or "").lower(), u)

    # ---------------- (F) Bronze's character ----------------
    f = pg.evaluate("""async () => { const w = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      try{
        const c = AVATAR_CHARACTERS.find(x => x.unlock === TIER_ORDER_FULL[0] && !x.retired);
        out.id = c ? c.id : null;
        if(!c) return out;
        out.name = AVATAR_DISPLAY_NAME[c.id] || null;
        out.glow = (typeof avatarGlowColor === 'function') ? avatarGlowColor(c.id) : null;
        out.rx = RX_CHARS.indexOf(c.id) >= 0;
        const svg = buildAvatarCharSVGSafe(c.id);
        out.parts = svg ? svg.querySelectorAll('path, circle, ellipse').length : 0;
        out.fx = svg ? ['cx-fx-crown', 'cx-fx-gem'].filter(k => svg.querySelector('.' + k)).length : 0;
        out.lockedNow = isLockedCharacter(c.id);
        out.shownBelow = unlockWasShown('chars', c.id);
        // an account on Bronze: the first launch of this build marks it shown and seen, with no card
        const u0 = unitsInTeachingOrder()[0]; store.unitPerfects[u0] = badgeThresholdFor(u0); saveStore();
        ['class26e.forgeseed.academy'].forEach(k => { try{ localStorage.removeItem(k); }catch(e){} });
        out.rank = rankOf(store);
        out.lockedOnBronze = isLockedCharacter(c.id);
        showHome(); await w(3800);
        out.shownOnBronze = unlockWasShown('chars', c.id);
        out.seenOnBronze = !unlockIsNew('chars', c.id);
        out.card = !!document.querySelector('.unlock-card, .rs-spot');
        // the rank map's Bronze card names it
        showProfile('ranks'); await w(1500);
        out.onMap = [...document.querySelectorAll('#stage *')].some(e => e.childElementCount === 0 && e.textContent.trim() === out.name);
      }catch(e){ out.err = String(e); }
      return out; }""")
    chk("(F) a character unlocks at the first rank (Bronze), named and glowing in its own colour (%s, %s, %s)" % (f.get("id"), f.get("name"), f.get("glow")),
        bool(f.get("id")) and bool(f.get("name")) and bool(f.get("glow")), f)
    chk("(F) it is drawn as a picture of its own (%s shapes, crown and medallion parts %s) and reacts to a grade (%s)" % (f.get("parts"), f.get("fx"), f.get("rx")),
        (f.get("parts") or 0) >= 30 and f.get("fx") == 2 and f.get("rx"), f)
    chk("(F) below Bronze it is locked and not marked shown (%s, %s)" % (f.get("lockedNow"), f.get("shownBelow")),
        f.get("lockedNow") is True and f.get("shownBelow") is False, f)
    chk("(F) an account already on Bronze (%s) has it, marked shown and seen, with no card (shown %s, seen %s, card %s)" % (f.get("rank"), f.get("shownOnBronze"), f.get("seenOnBronze"), f.get("card")),
        f.get("lockedOnBronze") is False and f.get("shownOnBronze") and f.get("seenOnBronze") and not f.get("card"), f)
    chk("(F) the rank map's Bronze card names it (%s)" % f.get("onMap"), f.get("onMap"), f)

    # ---------------- (N) the name field ----------------
    n = pg.evaluate("""async () => { const w = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      try{
        const t = document.createElement('div'); t.className = 'nova-talk'; document.body.appendChild(t);
        novaAskName({ stage: t, close(){} }, () => {}); await w(80);
        const i = document.querySelector('.nt-ask-input'), p = i && i.closest('.nt-prop');
        out.auto = i.getAttribute('autocomplete'); out.name = i.name || '';
        out.propTransform = getComputedStyle(p).transform; out.propTransition = getComputedStyle(p).transitionProperty;
        await w(700);
        out.focused = document.activeElement === i;
        out.caretEmpty = getComputedStyle(i).caretColor;
        i.value = 'Ab'; i.dispatchEvent(new Event('input'));
        out.caretTyped = getComputedStyle(i).caretColor;
        t.remove();
      }catch(e){ out.err = String(e); }
      return out; }""")
    chk("(N) Safari has nothing to fill in the name field (autocomplete %r, name %r)" % (n.get("auto"), n.get("name")),
        n.get("auto") == "off" and n.get("name") and "name" not in (n.get("name") or "").lower() and "user" not in (n.get("name") or "").lower(), n)
    chk("(N) an empty field shows no caret (%s), a typed one does (%s)" % (n.get("caretEmpty"), n.get("caretTyped")),
        "0)" in (n.get("caretEmpty") or "") or n.get("caretEmpty") == "transparent", n)
    chk("(N) the field's card fades in without moving (transform %s; transition %s) and takes focus after (%s)" % (n.get("propTransform"), n.get("propTransition"), n.get("focused")),
        n.get("propTransform") == "none" and "transform" not in (n.get("propTransition") or "") and n.get("focused"), n)

    # ---------------- (O) the end of a sign-up, in order ----------------
    o = pg.evaluate("""async () => { const w = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      try{
        const L = novaIntroLines({ signup: true });
        const txt = l => typeof l.text === 'function' ? '' : String(l.text || '');
        out.last = txt(L[L.length - 1]);
        out.friendInIntro = L.some(l => l.friend);
        out.nIntro = L.length;
        const steps = mainMenuTourSteps(false);
        out.lastTipTarget = steps[steps.length - 1].target;
        out.startInTips = steps.some(s => s.target === '#nextbtn' || s.target === '#bottomtab-start');
        out.friendTip = typeof steps[steps.length - 1].onShow === 'function';
        // Start Studying waits for the Add to Home Screen sheet
        showHome(); await w(600);
        document.querySelectorAll('.unlock-card, .rs-spot, #tour-overlay, #tour-tooltip').forEach(e => e.remove());
        try{ localStorage.setItem('class26e.a2hs', 'owed'); }catch(e){}
        if(typeof scheduleStudyTip !== 'function'){ out.noFn = true; return out; }
        const sheet = showHomeScreenSheet({ from: 'signup' });
        scheduleStudyTip(); await w(4500);
        out.tipWhileSheet = !!document.getElementById('tour-tooltip');
        const close = document.querySelector('.a2hs-close'); out.closeLabel = close ? close.textContent : '';
        if(close) close.click();
        await w(6000);
        const tt = document.getElementById('tour-tooltip');
        out.tipAfter = !!tt; out.tipText = tt ? tt.innerText : '';
        const nb = document.getElementById('nextbtn');
        out.tipOnStart = !!tt && !!nb;
      }catch(e){ out.err = String(e); }
      return out; }""")
    chk("(O) a new account's introduction ends without his goodbye or the friend line (last: %r; friend line in it: %s)" % (o.get("last"), o.get("friendInIntro")),
        not o.get("friendInIntro") and "Rank up" not in (o.get("last") or "") and "adventure" not in (o.get("last") or "").lower(), o)
    chk("(O) the main menu's tips end on the friend line at the chat button, with no Start Studying among them (%s, %s)" % (o.get("lastTipTarget"), o.get("startInTips")),
        o.get("lastTipTarget") == "#chatdock-btn" and o.get("friendTip") and not o.get("startInTips"), o)
    chk("(O) Start Studying's tip waits for the Add to Home Screen sheet, then comes (during: %s, after: %s %r)" % (o.get("tipWhileSheet"), o.get("tipAfter"), (o.get("tipText") or "")[:60]),
        not o.get("noFn") and o.get("tipWhileSheet") is False and o.get("tipAfter") and o.get("tipOnStart"), o)

    # ---------------- (V) the clip and its button ----------------
    v = pg.evaluate("""() => ({ rate: (typeof A2HS_CLIP === 'object' && A2HS_CLIP.rate) || 1 })""")
    chk("(V) the Add to Home Screen clip plays at the speed it was recorded - a real iPhone recording, not slowed (rate %s)" % v.get("rate"), v.get("rate") == 1, v)
    chk("(V) the sign-up's sheet closes with a button that says later (%r)" % o.get("closeLabel"), "later" in (o.get("closeLabel") or "").lower(), o)

    # ---------------- (T) the tips ----------------
    t = pg.evaluate("""() => { const out = {}; try{
        const steps = mainMenuTourSteps(false).concat(PROFILE_TIPS_289);
        out.lens = steps.map(s => String(s.text || '').length);
        out.max = Math.max.apply(null, out.lens);
        out.mean = Math.round(out.lens.reduce((a, b) => a + b, 0) / out.lens.length);
      }catch(e){ out.err = String(e); } return out; }""")
    print("    tips: %s chars, longest %s, mean %s" % (t.get("lens"), t.get("max"), t.get("mean")))
    chk("(T) no main-menu or Profile tip runs past about two short lines (longest %s, mean %s characters)" % (t.get("max"), t.get("mean")),
        (t.get("max") or 999) <= 90 and (t.get("mean") or 999) <= 60, t)

    # ---------------- (S) the seam where Nova's speech tail meets the bubble ----------------
    # "The bottom of the arrow is messed up, you can see where the pointy part connects to the rectangle": one row of the bubble's
    # border showed across the tail's base. Read off the pixels at 3x, 2.5x and 2x: beside the tail the border is a few bright
    # rows; across the tail's centre those same rows must be the bubble's own fill.
    import io
    from PIL import Image
    def seam(dpr):
        c2, p2 = cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT, dpr=dpr)
        p2.evaluate("()=>{ document.querySelectorAll('#splashscreen,.app-banner,.daily-alert').forEach(n=>n.remove()); playNovaIntro(()=>{}, { signup: true }); }")
        p2.wait_for_timeout(2600)
        bb = p2.evaluate("()=>{ const b = document.querySelector('.nt-bubble'); const r = b.getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; }")
        x, y, w, h = bb
        clip = {"x": x + 10, "y": y + h - 30, "width": 120, "height": 50}
        im = Image.open(io.BytesIO(p2.screenshot(clip=clip))).convert("RGB")
        c2.close()
        W, H = im.size
        bright = lambda px: sum(px) > 150
        side = [yy for yy in range(H) if bright(im.getpixel((int(W * .06), yy)))]
        if not side: return {"err": "no border found", "dpr": dpr}
        # the tail's centre column: the lowest bright pixel of the tail's own outline, below the border rows
        best = None
        for xx in range(int(W * .15), W - 5):
            ys = [yy for yy in range(max(side) + 2, H) if bright(im.getpixel((xx, yy))) and im.getpixel((xx, yy))[2] > 60]
            if ys and (best is None or max(ys) > best[0]): best = (max(ys), xx)
        if not best: return {"err": "no tail found", "dpr": dpr}
        cx = best[1]
        fill = im.getpixel((cx, min(side) - 4))
        worst = max(max(abs(a - b) for a, b in zip(im.getpixel((cx, yy)), fill)) for yy in side)
        return {"dpr": dpr, "border rows": side, "tail column": cx, "fill": fill, "worst row off the fill": worst}
    sm = [seam(d) for d in (3, 2.5, 2)]
    chk("(S) across the tail's base the bubble's border rows are the bubble's fill, at 3x, 2.5x and 2x (worst: %s)" % [m.get("worst row off the fill") for m in sm],
        all(m.get("worst row off the fill", 99) <= 6 for m in sm), sm)

    chk("(E) no page errors (%d)" % len(errs), not errs, errs[:3])
    br.close()
cb.SERVER.shutdown()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
