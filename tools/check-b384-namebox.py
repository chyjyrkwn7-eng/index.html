#!/usr/bin/env python3
"""Build 384.109: the name editor's "weird white box", and every text field hardened against the same thing.

Madison, on his installed iPhone: "When clicking change on my name, a weird white box shows up, fix that."
The editor is Settings > Account > Name (buildCustomizeNameSect; Customize's summary handed it to Settings in 383): Change hides
the name row, shows a label, the field and Save / Cancel, and focuses the field. Chromium cannot draw what iOS draws natively
(a switch, a field's own look, AutoFill), so this measures what the page controls, on the evidence of what iOS paints white:
  - AutoFill. The name field was the ONE text field that told Safari it holds a person's name ("Your name", "First and last
    name", autocapitalised words, no autocomplete); every other live field is a code, a search or a message. A field
    AutoFill fills is painted by the browser's own sheet, !important, which no page rule can take back: WebKit's is a pale
    #FAFFBD with black letters whatever the page's scheme, Chromium's light one #E8F0FE with black letters. Here the field is
    forced into :autofill (CDP) and given the light scheme, so Chromium paints its pale fill - the page's answer has to
    cover it.
  - The field's own look (appearance, fill, 16px), and the haptic layer's native switches (.nova-hsw: opacity 0, never
    hidden any other way, or the tick dies) around the tap on Change.

  E  the editor, on the iPhone 17 Pro Max installed (the haptic layer is on) and the iPad Pro 11", the Police Academy (and
     Fire Code on the phone):
     E1 [fix]   the field names itself as nothing Safari fills: autocomplete off and a `name` without "name" in it
     E2 [fix]   the field has an edge in its card: its top edge a few levels off the card beside it (it was the card's colour
                exactly - the name and a caret floating in the card)
     E3 [guard] a finger on Change opens the editor with the field focused; Cancel puts the row back; a name typed and saved
                is kept and shown
     E4 [guard] the haptic layer in every frame from just before the finger lands to ~1.1s after (and on until 20 frames with
                the editor open): every native switch
                (.nova-hsw, .nova-hlb-sw, input.hsw-opt) at opacity 0, every label (.nova-hlb) painting nothing; on the phone
                Change carries a switch before the tap and Save and Cancel after it (so this is not a check of nothing)
     E5 [guard] the editor's label and field at four moments after the tap: no solid near-white area (the Save pill is the
                app's white primary button by design - "white and black" - and is left out)
     E6 [fix]   the same with AutoFill's paint on the field: no solid near-white area, and not one near-white pixel more than
                at rest (a box, or the 1px ring a cover leaves where the fill runs under a transparent border); the field
                keeps its own colour; its letters light
  F  every text field the app shows (the glitches gate's list of screens, the name field open, the starred list's search, the
     chat's field and the tab bar's search), the phone, both classes:
     F1 [fix]   appearance none (a type=search field without it is iOS's own search field)
     F2 [guard] dark: its fill over the page is dark and nothing solid near-white is painted in it
     F3 [guard] 16px+ on the glass
     F4 [fix]   AutoFill cannot paint it: forced :autofill with the light fill, no solid near-white area and no near-white
                pixel added (box or ring)
     F5 [fix]   Safari's AutoFill buttons (contacts card, key) are hidden in ANY field: unscoped rules, display none
"Solid near-white": a pixel whose 5x5 neighbourhood is all at luminance 224+ (~#E0E0E0), counted; letters and a caret are
strokes and never fill a 5x5 block, a box does. More than 25 fails.

  python3 tools/check-b384-namebox.py [--against REV|DIR] [--shots DIR [--shots-only]]
--against origin/main must FAIL E1, E2, E6, F1, F4 and F5. --shots saves the editor open (and with AutoFill's paint) at the
phone's and the iPad's own pixel ratio, named by build ("main-" for an --against build, "fix-" for this one).
"""
import importlib.util, io, json, os, sys, time
SHOTS = None; SHOTS_ONLY = "--shots-only" in sys.argv
if SHOTS_ONLY: sys.argv.remove("--shots-only")
if "--shots" in sys.argv:
    i = sys.argv.index("--shots"); SHOTS = sys.argv[i + 1]; del sys.argv[i:i + 2]
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("glitches", os.path.join(HERE, "check-b384-glitches.py"))
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)   # takes --against from sys.argv
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from PIL import Image
from playwright.sync_api import sync_playwright
chk = G.chk
SOLID_MAX = 25
LIGHT_ADD_MAX = 30   # near-white pixels AutoFill may add to a field (anti-aliasing of the same letters); a 1px ring round one is hundreds

def solid_white(png, masks=()):
    """pixels whose 5x5 block is all near-white (luminance >= 224), masks = [(x, y, w, h)] in image pixels left out"""
    a = np.asarray(Image.open(io.BytesIO(png)).convert("RGB")).astype(np.float32)
    light = (0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]) >= 224
    for (x, y, w, h) in masks:
        light[max(0, int(y)):max(0, int(y + h)), max(0, int(x)):max(0, int(x + w))] = False
    if light.shape[0] < 5 or light.shape[1] < 5: return 0
    return int(sliding_window_view(light, (5, 5)).all(axis=(2, 3)).sum())

def light_count(png):
    """every near-white pixel (luminance >= 224), strokes included: AutoFill must add none - not a box, and not a ring"""
    a = np.asarray(Image.open(io.BytesIO(png)).convert("RGB")).astype(np.float32)
    return int(((0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]) >= 224).sum())

def lum_at(png, x, y):
    a = np.asarray(Image.open(io.BytesIO(png)).convert("RGB")).astype(np.float32)
    y = min(max(0, int(y)), a.shape[0] - 1); x = min(max(0, int(x)), a.shape[1] - 1)
    p = a[y, x]; return round(float(0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2]), 1)

# the browser's own AutoFill fill in its light form (Chromium: #E8F0FE, black letters - as WebKit's #FAFFBD, black letters):
# a forced :autofill field is given the light scheme; nothing else is touched
AUTOFILL_LIGHT = """()=>{ if(document.getElementById('__gate-af')) return; const s = document.createElement('style'); s.id = '__gate-af';
  s.textContent = '@layer gate-autofill-light{ :where(input, textarea):autofill{ color-scheme:light !important; } }'; document.body.appendChild(s); }"""
TEXT_FIELDS = """(all)=>[...document.querySelectorAll('input, textarea')].filter(e => {
    if(e.closest('.nova-hsw, .nova-hlb') || /nova-hsw|nova-hlb-sw|hsw-opt/.test(e.className || '')) return false;
    const t = (e.getAttribute('type') || 'text').toLowerCase();
    if(e.tagName === 'INPUT' && !/^(text|search|email|number|tel|password|url)$/.test(t)) return false;
    if(all) return true;
    const r = e.getBoundingClientRect(), c = getComputedStyle(e);
    return r.width > 8 && r.height > 8 && c.visibility !== 'hidden' && parseFloat(c.opacity) > 0.05; })"""

def force_autofill(cdp, sel, on=True):
    """CDP's forced :autofill on the element `sel` matches. The document is asked for ONCE per session: a second
    DOM.getDocument hands out new node ids, and a state forced under the old id is then left on the element for good."""
    if not getattr(cdp, "_root", None):
        cdp.send("DOM.enable"); cdp.send("CSS.enable")
        cdp._root = cdp.send("DOM.getDocument", {"depth": 0})["root"]["nodeId"]
    nid = cdp.send("DOM.querySelector", {"nodeId": cdp._root, "selector": sel})["nodeId"]
    if not nid: return False
    cdp.send("CSS.forcePseudoState", {"nodeId": nid, "forcedPseudoClasses": ["autofill"] if on else []})
    return True

def rect(pg, sel):
    return pg.evaluate("(s)=>{ const e = document.querySelector(s); if(!e) return null; const r = e.getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height }; }", sel)

def shot(pg, r, pad=0):
    x = max(0, r["x"] - pad); y = max(0, r["y"] - pad)
    return pg.screenshot(clip={"x": x, "y": y, "width": r["w"] + 2 * pad, "height": r["h"] + 2 * pad}, animations="allow")

def tap(cdp, x, y, hold=0.06):
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]}); time.sleep(hold)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})

def open_account(pg, phone):
    pg.evaluate("()=>showAppearance({ page: 'account' })"); pg.wait_for_timeout(900); G.clear_popups(pg)
    if phone:   # the haptic layer arrives a beat after a screen (hswSchedule)
        for _ in range(30):
            if pg.evaluate("()=>!!document.querySelector('#stage .settings-namesect .profile-edit-btn > .nova-hsw')"): break
            pg.wait_for_timeout(200)
    pg.wait_for_timeout(300)

# every frame: every native switch at opacity 0, every label painting nothing
SAMPLER = r"""(ms)=>{ const alpha = c => { const m = /rgba?\(([^)]+)\)/.exec(c || ''); if(!m) return /transparent/.test(c) ? 0 : 1; const p = m[1].split(/[ ,\/]+/).filter(Boolean); return p.length > 3 ? parseFloat(p[3]) : 1; };
  /* at least `ms`, and on a busy machine on until 20 frames have been read with the editor open (8s at most) */
  const F = window.__hswFrames = []; window.__hswDone = false; const t0 = performance.now(), stop = t0 + ms;
  const more = () => performance.now() < stop || (F.filter(f => f.open).length < 20 && performance.now() < t0 + 8000);
  const one = () => { const bad = []; let sw = 0, lb = 0;
    document.querySelectorAll('.nova-hsw, .nova-hlb-sw, input.hsw-opt').forEach(s => { const c = getComputedStyle(s), r = s.getBoundingClientRect();
      if(c.display === 'none' || !r.width || !r.height) return; sw++;
      if(parseFloat(c.opacity) > 0 && c.visibility !== 'hidden') bad.push({ el: s.className, host: (s.parentElement && s.parentElement.className || '').toString().slice(0, 40), op: c.opacity }); });
    document.querySelectorAll('.nova-hlb').forEach(l => { const c = getComputedStyle(l), r = l.getBoundingClientRect();
      if(c.display === 'none' || !r.width || !r.height) return; lb++;
      const border = ['Top', 'Right', 'Bottom', 'Left'].some(k => parseFloat(c['border' + k + 'Width']) > 0 && alpha(c['border' + k + 'Color']) > 0);
      if(alpha(c.backgroundColor) > 0 || c.backgroundImage !== 'none' || border || c.boxShadow !== 'none' || (c.outlineStyle !== 'none' && parseFloat(c.outlineWidth) > 0))
        bad.push({ el: 'nova-hlb', host: (l.parentElement && l.parentElement.className || '').toString().slice(0, 40), bg: c.backgroundColor }); });
    const q = s => !!document.querySelector('#stage .settings-namesect ' + s);
    F.push({ t: Math.round(performance.now()), sw, lb, bad: bad.slice(0, 3), change: q('.profile-edit-btn > .nova-hsw'),
      save: q('.customize-namebtns > .next:not(.ghost) > .nova-hsw'), cancel: q('.customize-namebtns > .next.ghost > .nova-hsw'),
      open: !!document.querySelector('#stage .customize-nameedit:not([hidden])') });
    if(more()) requestAnimationFrame(one); else window.__hswDone = true; };
  requestAnimationFrame(one); }"""

def sec_editor(br):
    print("\nE: the name editor (Settings > Account > Name)")
    for cls, dev in [("academy", "promax"), ("academy", "ipad"), ("ifc", "promax")]:
        tag = "%s %s" % (cls, dev); phone = dev == "promax"
        pg = G.open_dev(br, dev, inits=[G.seed_init(cls)])
        cdp = pg.ctx.new_cdp_session(pg)
        layer = pg.evaluate("()=>NovaSound.canTaptic()")
        if phone: chk("[guard] %s: the haptic layer is on (an iPhone, Haptics on)" % tag, layer, layer)
        open_account(pg, phone)
        # E1
        a = pg.evaluate("()=>{ const i = document.getElementById('customize-name-input'); return i ? { ac: i.getAttribute('autocomplete'), name: i.getAttribute('name') } : null; }")
        chk("[fix] %s E1 the field names itself as nothing Safari fills: autocomplete=%r name=%r" % (tag, a and a["ac"], a and a["name"]),
            bool(a) and a["ac"] == "off" and bool(a["name"]) and "name" not in a["name"].lower(), a)
        # E4 + E3 (open): a finger on Change, the haptic layer sampled every frame around it
        pg.evaluate(SAMPLER, 1300); pg.wait_for_timeout(150)
        b = rect(pg, "#stage .settings-namesect .profile-edit-btn")
        tap(cdp, b["x"] + b["w"] / 2, b["y"] + b["h"] / 2)
        # E5: the editor's label and field (the Save pill left out) at four moments after the tap
        e5 = []
        for wait in (0, 80, 250, 650):
            if wait: pg.wait_for_timeout(wait)
            er = rect(pg, "#stage .settings-namesect .customize-nameedit")
            br_ = rect(pg, "#stage .settings-namesect .customize-namebtns")
            if not er or er["w"] < 10:
                e5.append({"at": wait, "open": False}); continue
            png = shot(pg, er)
            mask = [(br_["x"] - er["x"], br_["y"] - er["y"], br_["w"], br_["h"])] if br_ else []
            e5.append({"at": wait, "solid": solid_white(png, mask)})
        pg.wait_for_timeout(900)
        for _ in range(40):
            if pg.evaluate("()=>!!window.__hswDone"): break
            pg.wait_for_timeout(200)
        frames = pg.evaluate("()=>window.__hswFrames")
        st = pg.evaluate("""()=>({ open: !!document.querySelector('#stage .customize-nameedit:not([hidden])'), row: !document.querySelector('#stage .customize-namerow').hidden,
          focused: (document.activeElement || {}).id || '' })""")
        bad = [f for f in frames if f["bad"]]
        before = [f for f in frames if not f["open"]]; after = [f for f in frames if f["open"]]
        wired = (not phone) or (bool(before) and before[-1]["change"] and bool(after) and after[-1]["save"] and after[-1]["cancel"])
        chk("[guard] %s E4 the haptic layer in every frame around the tap (%d frames, %d before / %d after it opened, up to %d switches and %d labels on screen): no switch above opacity 0, no label painting"
            % (tag, len(frames), len(before), len(after), max([f["sw"] for f in frames] or [0]), max([f["lb"] for f in frames] or [0])),
            len(frames) >= 12 and bool(before) and bool(after) and not bad and wired,
            {"bad": bad[:3], "wired": wired, "last_before": before[-1:] , "last_after": after[-1:]})
        chk("[guard] %s E3 a finger on Change opens the editor with the field focused (open %s, row shown %s, focus %r)" % (tag, st["open"], st["row"], st["focused"]),
            st["open"] and not st["row"] and st["focused"] == "customize-name-input", st)
        chk("[guard] %s E5 no solid near-white area in the editor's label and field just after the tap (%s)" % (tag, e5),
            all(x.get("solid", 0) <= SOLID_MAX for x in e5) and sum(1 for x in e5 if "solid" in x) >= 3, e5)
        # E2: the field's top edge against the card beside it
        fr = rect(pg, "#customize-name-input"); er = rect(pg, "#stage .settings-namesect .customize-nameedit")
        png = pg.screenshot(animations="allow")
        mx = fr["x"] + fr["w"] / 2
        card = lum_at(png, mx, fr["y"] - 4); inside = lum_at(png, mx, fr["y"] + 8)
        # the field's top edge: its first four rows (a 1px border, then whatever the field draws inside it), the one furthest from the card
        edge = max((lum_at(png, mx, int(fr["y"]) + k) for k in range(4)), key=lambda v: abs(v - card))
        chk("[fix] %s E2 the field has an edge in its card: its top edge %.1f, the card beside it %.1f, inside it %.1f (6+ levels apart)" % (tag, edge, card, inside),
            abs(edge - card) >= 6 or abs(inside - card) >= 6, {"edge": edge, "card": card, "inside": inside})
        rest_inside = lum_at(png, fr["x"] + fr["w"] - 14, fr["y"] + fr["h"] / 2)
        # E6: AutoFill's paint on the field (the caret put away first: it blinks, and it is not what is measured)
        pg.evaluate("()=>document.activeElement && document.activeElement.blur()"); pg.wait_for_timeout(150)
        rest_light = light_count(shot(pg, fr, 3))
        pg.evaluate(AUTOFILL_LIGHT)
        ok = force_autofill(cdp, "#customize-name-input"); pg.wait_for_timeout(250)
        er = rect(pg, "#stage .settings-namesect .customize-nameedit"); br_ = rect(pg, "#stage .settings-namesect .customize-namebtns")
        png = shot(pg, er)
        s6 = solid_white(png, [(br_["x"] - er["x"], br_["y"] - er["y"], br_["w"], br_["h"])])
        af_light = light_count(shot(pg, fr, 3))
        full = pg.screenshot(animations="allow")
        af_inside = lum_at(full, fr["x"] + fr["w"] - 14, fr["y"] + fr["h"] / 2)
        tf = pg.evaluate("""()=>{ const i = document.getElementById('customize-name-input'); const c = getComputedStyle(i);
          const m = /(\\d+(?:\\.\\d+)?)[ ,]+(\\d+(?:\\.\\d+)?)[ ,]+(\\d+(?:\\.\\d+)?)/.exec(c.webkitTextFillColor) || [0, 0, 0, 0];
          return { af: i.matches(':autofill'), fill: c.webkitTextFillColor, lum: 0.2126 * m[1] + 0.7152 * m[2] + 0.0722 * m[3], bg: c.backgroundColor }; }""")
        chk("[fix] %s E6 with AutoFill's paint on the field (forced %s, the browser's fill %s): no solid near-white area (%d), no near-white pixel added - box or ring (%d -> %d), the field its own colour (%.1f, %.1f at rest), its letters light (%s)"
            % (tag, tf["af"], tf["bg"], s6, rest_light, af_light, af_inside, rest_inside, tf["fill"]),
            ok and tf["af"] and s6 <= SOLID_MAX and af_light - rest_light <= LIGHT_ADD_MAX and abs(af_inside - rest_inside) <= 6 and tf["lum"] >= 200,
            {"solid": s6, "light": [rest_light, af_light], "inside": [af_inside, rest_inside], "text": tf})
        force_autofill(cdp, "#customize-name-input", False)
        pg.evaluate("()=>document.getElementById('__gate-af')?.remove()")
        # E3 (the rest): Cancel, then a new name saved
        pg.evaluate("()=>document.querySelector('#stage .customize-namebtns > .next.ghost').click()"); pg.wait_for_timeout(300)
        c1 = pg.evaluate("()=>({ open: !document.querySelector('#stage .customize-nameedit').hidden, row: !document.querySelector('#stage .customize-namerow').hidden })")
        pg.evaluate("()=>document.querySelector('#stage .settings-namesect .profile-edit-btn').click()"); pg.wait_for_timeout(300)
        pg.fill("#customize-name-input", "Casey Quinn"); pg.wait_for_timeout(100)
        pg.evaluate("()=>document.querySelector('#stage .customize-namebtns > .next:not(.ghost)').click()"); pg.wait_for_timeout(400)
        c2 = pg.evaluate("()=>({ name: store.firstName, shown: document.querySelector('#stage .customize-namerow .profile-name-display').textContent, open: !document.querySelector('#stage .customize-nameedit').hidden })")
        chk("[guard] %s E3 Cancel puts the row back (%s); a name typed and saved is kept and shown (%s)" % (tag, c1, c2),
            not c1["open"] and c1["row"] and c2["name"] == "Casey Quinn" and c2["shown"] == "Casey Quinn" and not c2["open"], [c1, c2])
        chk("[guard] %s: no page errors" % tag, not pg.errs, pg.errs[:3])
        pg.ctx.close()

STARRED = """()=>{ const u = topicsIn(QUESTIONS)[0]; let k = 0;
  QUESTIONS.forEach((q, i) => { if((q.topic || '').trim() === u && k < 3){ store.flagged[KEYS[i]] = true; k++; } });
  cfg.mode = 'drill'; cfg.units = []; showSetup();
  setTimeout(() => { const row = [...document.querySelectorAll('.pick')].find(r => (r.querySelector('input') || {}).value === u);
    if(row) openUnitDetail(row, u, cfg.mode); setTimeout(() => document.querySelector('.unitdetail-door.is-flagged')?.click(), 700); }, 700); }"""
NAME_OPEN = "()=>{ showAppearance({ page: 'account' }); setTimeout(() => document.querySelector('#stage .settings-namesect .profile-edit-btn')?.click(), 400); }"
# the chat's field: the panel the chat and the Virtual Room lobby both build, on its own (a room's chat needs a live room)
CHAT_FIELD = ("()=>{ showHome(); const h = document.createElement('div'); h.id = '__gate-chat'; h.style.cssText = 'position:fixed;left:16px;right:16px;top:180px;height:420px;z-index:50;';"
              " document.body.appendChild(h); try{ window.__gateChat = buildVroomChatPanel(h); }catch(e){} }")
# the tab bar's search, opened over Review's list (that list's own search stays folded away until asked for)
TAB_SEARCH = ("()=>{ cfg.mode = 'review'; showAnswerReview([topicsIn(QUESTIONS)[0]], 'all'); let n = 0;"
              " const t = setInterval(() => { if(document.body.classList.contains('tabsearch-open') || ++n > 12){ clearInterval(t); return; }"
              " document.querySelector('#tabsearch .tabsearch-btn')?.click(); }, 700); }")

def sec_fields(br):
    print("\nF: every text field the app shows")
    screens = [s for s in G.FIELD_SCREENS if s[0] not in ("Account's name", "Review's list", "the chat")] + [
        ("Account's name (the editor open)", NAME_OPEN, "both"), ("the starred list's search", STARRED, "both"),
        ("the chat's field", CHAT_FIELD, "both"), ("the tab bar's search (Review's list)", TAB_SEARCH, "both")]
    # F5: the sheet itself
    for cls in ["academy", "ifc"]:
        pg = G.open_dev(br, "promax", inits=[G.seed_init(cls)])
        cdp = pg.ctx.new_cdp_session(pg)
        if cls == "academy":
            f5 = pg.evaluate(r"""()=>{ const out = {}; const walk = rs => { for(const r of rs){ if(r.cssRules && !r.selectorText){ walk(r.cssRules); continue; }
                const s = r.selectorText || ''; ['contacts', 'credentials'].forEach(k => { if(!s.includes('::-webkit-' + k + '-auto-fill-button')) return;
                  s.split(/,(?![^(]*\))/).map(x => x.trim()).filter(x => x.includes('::-webkit-' + k + '-auto-fill-button')).forEach(x => {
                    const subject = x.split('::')[0].trim();
                    if(/^(input|:where\([^)]*\)|)$/.test(subject) && r.style.display === 'none') out[k] = x; }); }); } };
              [...document.styleSheets].forEach(sh => { try{ walk(sh.cssRules); }catch(e){} }); return out; }""")
            chk("[fix] F5 the sheet hides Safari's AutoFill buttons in any field (%s)" % f5, "contacts" in f5 and "credentials" in f5, f5)
        pg.evaluate(AUTOFILL_LIGHT)
        got = []
        for label, js, where in screens:
            if where != "both" and where != cls: continue
            try:
                pg.evaluate(js); pg.wait_for_timeout(2400 if ("starred" in label or "tab bar" in label) else 900)
                for _ in range(20):   # a busy machine: the screen's field may still be on its way
                    if pg.evaluate("()=>(" + TEXT_FIELDS + ")(false).length > 0"): break
                    pg.wait_for_timeout(300)
                if "tab bar" in label:
                    for _ in range(20):
                        if pg.evaluate("()=>document.body.classList.contains('tabsearch-open')"): break
                        pg.wait_for_timeout(300)
                    pg.wait_for_timeout(500)
                pg.evaluate(AUTOFILL_LIGHT)
                n = pg.evaluate("(sel)=>{ const fs = (" + TEXT_FIELDS + ")(false); fs.forEach((f, i) => f.setAttribute('data-gate-f', String(i))); return fs.length; }", None)
                for i in range(n):
                    sel = '[data-gate-f="%d"]' % i
                    info = pg.evaluate("""(sel)=>{ const e = document.querySelector(sel); e.scrollIntoView({ block: 'center', behavior: 'instant' });
                      const c = getComputedStyle(e), r = e.getBoundingClientRect(), z = screen.width / innerWidth;
                      const m = /rgba?\\(([^)]+)\\)/.exec(c.backgroundColor); let lum = null;
                      if(m){ const p = m[1].split(/[ ,\\/]+/).filter(Boolean).map(Number), a = p.length > 3 ? p[3] : 1;
                        const mix = k => a * p[k] + (1 - a) * [18, 22, 27][k]; lum = 0.2126 * mix(0) + 0.7152 * mix(1) + 0.0722 * mix(2); }
                      else if(/color\\(srgb/.test(c.backgroundColor)){ const p = c.backgroundColor.match(/[\\d.]+/g).map(Number); const a = p.length > 3 ? p[3] : 1;
                        const mix = k => a * p[k] * 255 + (1 - a) * [18, 22, 27][k]; lum = 0.2126 * mix(0) + 0.7152 * mix(1) + 0.0722 * mix(2); }
                      const fs = parseFloat(c.fontSize);
                      return { f: (e.className || e.tagName).toString().slice(0, 44), app: c.appearance, bg: c.backgroundColor, lum,
                        glass: Math.round(fs * (e.currentCSSZoom || 1) * z * 10) / 10, x: r.left, y: r.top, w: r.width, h: r.height,
                        inview: r.top >= 0 && r.bottom <= innerHeight && r.left >= 0 && r.right <= innerWidth }; }""", sel)
                    pg.wait_for_timeout(120)
                    info["where"] = label
                    r = {"x": info["x"], "y": info["y"], "w": info["w"], "h": info["h"]}
                    if info["inview"]:
                        # AutoFill always leaves a value: the field holds one for both readings (put back after), its caret put away
                        pg.evaluate("""(sel)=>{ document.activeElement && document.activeElement.blur && document.activeElement.blur();
                          const e = document.querySelector(sel); e.dataset.gateWas = e.value; if(!e.value) e.value = 'Casey Quinn'; }""", sel)
                        png = shot(pg, r, 3)
                        info["rest"] = solid_white(png); info["rest_light"] = light_count(png)
                        try:
                            force_autofill(cdp, sel); pg.wait_for_timeout(160)
                            png = shot(pg, r, 3)
                            info["af"] = solid_white(png); info["af_light"] = light_count(png)
                        finally:
                            force_autofill(cdp, sel, False)
                            pg.evaluate("(sel)=>{ const e = document.querySelector(sel); if(e && 'gateWas' in e.dataset){ e.value = e.dataset.gateWas; delete e.dataset.gateWas; } }", sel)
                    got.append(info)
                pg.evaluate("()=>{ document.querySelectorAll('[data-gate-f]').forEach(e => e.removeAttribute('data-gate-f')); document.getElementById('__gate-nt')?.remove(); try{ closeChatDock(); }catch(e){} try{ typeof window.__gateChat === 'function' && window.__gateChat(); }catch(e){} document.getElementById('__gate-chat')?.remove(); try{ closeUnitDetail && closeUnitDetail(); }catch(e){} document.querySelectorAll('.unitdetail, .unitdetail-scrim').forEach(n => n.remove()); }")
            except Exception as ex:
                got.append({"where": label, "f": "error " + str(ex)[:120], "app": "?", "lum": 999, "glass": 0, "inview": False})
        seen = sorted({g["where"] for g in got})
        tag = "promax %s: %d fields on %d screens" % (cls, len(got), len(seen))
        chk("[guard] %s - every listed screen showed a field (%s)" % (tag, [s[0] for s in screens if (s[2] == 'both' or s[2] == cls) and s[0] not in seen]),
            all(s[0] in seen for s in screens if s[2] == "both" or s[2] == cls), seen)
        f1 = [(g["where"], g["f"], g["app"]) for g in got if g["app"] != "none"]
        chk("[fix] %s F1 appearance none on every one %s" % (tag, f1[:4]), not f1, f1)
        f2 = [(g["where"], g["f"], g.get("bg"), g.get("lum"), g.get("rest")) for g in got if (g.get("lum") is None or g["lum"] > 110) or g.get("rest", 0) > SOLID_MAX]
        chk("[guard] %s F2 every one dark: its fill over the page dark, nothing solid near-white in it %s" % (tag, f2[:4]), not f2, f2)
        f3 = [(g["where"], g["f"], g["glass"]) for g in got if g["glass"] < 16]
        chk("[guard] %s F3 16px+ on the glass %s" % (tag, f3[:4]), not f3, f3)
        read = [g for g in got if "af" in g]
        f4 = [(g["where"], g["f"], g["af"], g["af_light"] - g["rest_light"]) for g in read if g["af"] > SOLID_MAX or g["af_light"] - g["rest_light"] > LIGHT_ADD_MAX]
        chk("[fix] %s F4 AutoFill cannot paint any of the %d read on screen (forced :autofill, the browser's light fill): no solid near-white area, no near-white pixel added (box or ring) %s" % (tag, len(read), f4[:4]),
            not f4 and len(read) >= len(got) - 2, f4)
        chk("[guard] promax %s: no page errors" % cls, not pg.errs, pg.errs[:3])
        pg.ctx.close()

def sec_shots(br):
    os.makedirs(SHOTS, exist_ok=True)
    tagb = "main" if G.ROOT != G.REPO else "fix"
    for dev, dsf in [("promax", 3), ("ipad", 2)]:
        pg = G.open_dev(br, dev, inits=[G.seed_init("academy")], dsf=dsf)
        cdp = pg.ctx.new_cdp_session(pg)
        open_account(pg, dev == "promax")
        b = rect(pg, "#stage .settings-namesect .profile-edit-btn")
        tap(cdp, b["x"] + b["w"] / 2, b["y"] + b["h"] / 2); pg.wait_for_timeout(700)
        p1 = os.path.join(SHOTS, "%s-%s-%s-editor.png" % (tagb, G.BUILD, dev)); pg.screenshot(path=p1)
        pg.evaluate(AUTOFILL_LIGHT); force_autofill(cdp, "#customize-name-input"); pg.wait_for_timeout(300)
        p2 = os.path.join(SHOTS, "%s-%s-%s-autofill.png" % (tagb, G.BUILD, dev)); pg.screenshot(path=p2)
        print("  saved", p1, p2)
        pg.ctx.close()

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G.CHROME)
    if SHOTS: sec_shots(br)
    if not (SHOTS and SHOTS_ONLY):
        sec_editor(br)
        sec_fields(br)
    br.close()
print("\n%s - %d failed%s" % ("ALL PASS" if not G.fails else "FAIL", len(G.fails), "" if not G.fails else ": " + "; ".join(f[:90] for f in G.fails)))
sys.exit(1 if G.fails else 0)
