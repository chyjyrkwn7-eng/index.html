"""Build 384.108: every place a class is shown or picked has Home's class button's mark and circle (option A, the lit ring).
Madison: "When selecting classes, ensure the two classes are updated (the logos and circles) to match what the Home Screen has now."

The places, each rendered in both classes (the academy and Fire Code) on an iPhone 17 Pro Max (installed) and an iPad Pro 11":
  signup   - the sign-up's Select your classes cards (showClassSelection: .class-card .cc-emblem), both classes' cards;
  catalog  - Classes / Add a class (showClassCatalog: .class-card .cc-emblem), both classes' cards;
  enroll   - Fire Code's enroll page (showIfcEnroll: .ce-emblem);
  list     - the class button's own list (the other class's .csi-bubble);
  enrolled - the You're enrolled banner (showEnrolledBanner, each class): its face;
  back     - the Welcome back to banner after a class switch (maybeSwitchWelcome): its face;
  newclass - the "Fire Code is open to join" banner (maybeNewClassBanner, the academy): its face.
For each class circle found there, against Home's class button drawn for the same class (a probe .class-bubble.is-<key> of the
button's 54px, read off the same page):
  M  the mark is classBtnIcon's drawing for that class (its svg, ids normalised), and NOT NOVA_CLASSES' old icon;
  R  the circle is the button's lit ring: the same --cb-ring colour, the ring's four stops at the same share of the circle's radius
     (within 2 points), the same pool and rim colours, and the button's two glows (the outer and the inset one) in the same colours,
     their blur the same share of the circle's size (within 25%);
  O  nowhere on the page is NOVA_CLASSES' old icon markup (its gradient ids);
  S  the states still read: on the sign-up a picked card's edge and light differ from an unpicked one's; on Classes the class you
     are in ("you are here") is drawn apart from the other (its edge, light or fill).
Run:  python3 tools/check-b384-classmarks.py [--against REV|DIR]   (--against the 384.98 head must FAIL M, R and O)"""
import importlib.util, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("glitches", os.path.join(HERE, "check-b384-glitches.py"))
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)   # takes --against from sys.argv
from playwright.sync_api import sync_playwright
chk = G.chk

QUIET = "()=>{ theme.reduceMotion = true; try{ applyTheme(); }catch(e){} try{ homeUnlocksOwed=()=>false; }catch(e){} }"
# everything about one circle, and the same for a probe of Home's button for that class
READ = r"""(args)=>{ const [sel, key] = args;
  const px = v => parseFloat(v) || 0;
  const norm = h => String(h || '').replace(/cbx\d+-/g, 'cbx-');
  /* the drawing as the page itself writes it out (parsed, so <stop/> reads <stop></stop> on both sides) */
  const expect = (() => { if(typeof classBtnIcon !== 'function') return ''; const t = document.createElement('span'); t.innerHTML = classBtnIcon(key);
    return t.firstElementChild ? norm(t.firstElementChild.outerHTML) : ''; })();
  const old = ((typeof NOVA_CLASSES !== 'undefined' ? NOVA_CLASSES : []).find(c => c.key === key) || {}).icon || '';
  const one = el => { if(!el) return null; const cs = getComputedStyle(el); const r = el.getBoundingClientRect();
    const svg = el.matches('svg') ? el : el.querySelector(':scope > svg');
    const inner = el.clientWidth / 2;   /* the padding box's radius: what closest-side measures */
    return { w: Math.round(r.width * 10) / 10, R: inner, ring: cs.getPropertyValue('--cb-ring').trim(), bg: cs.backgroundImage, border: cs.borderTopColor,
      shadow: cs.boxShadow, svg: svg ? norm(svg.outerHTML) : '', vis: r.width > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' }; };
  const el = typeof sel === 'string' ? document.querySelector(sel) : null;
  const probe = document.createElement('span'); probe.className = 'class-bubble is-' + key;
  probe.style.cssText = 'position:fixed;left:-300px;top:0;width:54px;height:54px;box-sizing:border-box';
  document.body.appendChild(probe); const ref = one(probe); probe.remove();
  return { el: one(el), ref, expect, oldSvg: old ? norm(old).slice(0, 60) : '' }; }"""
OLDIDS = r"""()=>{ const ids = []; (typeof NOVA_CLASSES !== 'undefined' ? NOVA_CLASSES : []).forEach(c => { const m = String(c.icon || '').match(/id="([^"]+)"/g) || []; m.forEach(x => ids.push(x.slice(4, -1))); });
  return ids.filter(id => document.getElementById(id)); }"""

def stops(bg, R):
    """the first radial-gradient's four stop positions, as a share of the radius from the edge"""
    m = re.search(r"radial-gradient\((.*?)\)\s*(?:padding-box)?\s*,\s*radial-gradient", bg)
    first = bg.split("radial-gradient(", 1)[1] if "radial-gradient(" in bg else ""
    pos = re.findall(r"(calc\(100% - [\d.]+px\)|[\d.]+%)", first)[:4]
    out = []
    for p in pos:
        mm = re.match(r"calc\(100% - ([\d.]+)px\)", p)
        out.append(round(float(mm.group(1)) / R, 3) if mm else round(1 - float(p[:-1]) / 100, 3))
    return out
def colours(s): return re.findall(r"(?:rgba?|color|oklab|color-mix)\([^()]*(?:\([^()]*\)[^()]*)*\)", s)
def glows(shadow):
    """(blur, colour) of the outer zero-offset glow and of the inset glow"""
    parts = re.split(r",(?![^(]*\))", shadow); outer = inset = None
    for p in parts:
        cols = colours(p); rest = p
        for c in cols: rest = rest.replace(c, "")
        nums = [float(x[:-2]) for x in re.findall(r"-?[\d.]+px", rest)]
        if "inset" in p and len(nums) >= 3: inset = (nums[2], cols[0] if cols else "")
        elif len(nums) >= 3 and nums[0] == 0 and nums[1] == 0 and nums[2] > 0: outer = (nums[2], cols[0] if cols else "")
    return outer, inset

def judge(tag, place, key, d):
    e, ref = d["el"], d["ref"]
    if not e or not e["vis"]:
        chk("[%s] %s %s: the place is drawn" % (tag, place, key), False, d); return
    chk("[%s] M %s %s: the mark is classBtnIcon's drawing, not the old icon" % (tag, place, key),
        bool(d["expect"]) and e["svg"] == d["expect"], {"svg": e["svg"][:120], "expect": d["expect"][:120]})
    sr, se = stops(ref["bg"], ref["R"]), stops(e["bg"], e["R"]) if e["R"] else []
    go, gi = glows(ref["shadow"]); eo, ei = glows(e["shadow"])
    ref_cols = colours(ref["bg"]); e_cols = colours(e["bg"])
    ok_ring = bool(ref["ring"]) and e["ring"] == ref["ring"] and len(se) == 4 and all(abs(a - b) <= .02 for a, b in zip(se, sr))
    ok_cols = e_cols[:4] == ref_cols[:4] and e["border"] == ref["border"]
    ok_glow = bool(go and gi and eo and ei) and eo[1] == go[1] and ei[1] == gi[1] and \
        abs(eo[0] / max(e["w"], 1) - go[0] / ref["w"]) <= .25 * go[0] / ref["w"] and abs(ei[0] / max(e["w"], 1) - gi[0] / ref["w"]) <= .25 * gi[0] / ref["w"]
    chk("[%s] R %s %s: Home's lit ring at %spx (ring stops %s vs the button's %s; glows %s/%s vs %s/%s)" % (
        tag, place, key, e["w"], se, sr, eo and eo[0], ei and ei[0], go and go[0], gi and gi[0]), ok_ring and ok_cols and ok_glow,
        {"ring": [e["ring"], ref["ring"]], "cols": [e_cols[:4], ref_cols[:4]], "border": [e["border"], ref["border"]], "glow": [eo, ei, go, gi]})

def place_read(pg, sel, key): return pg.evaluate(READ, [sel, key])

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G.CHROME)
    for cls in ["academy", "ifc"]:
        for dev in ["promax", "ipad"]:
            tag = "%s %s" % (cls, dev)
            pg = G.open_dev(br, dev, inits=[G.seed_init(cls)], dsf=2)
            pg.evaluate(QUIET); pg.evaluate("()=>showHome()"); pg.wait_for_timeout(1500); G.clear_popups(pg)
            pg.add_style_tag(content="#intro-pop, .intro-pop{ display:none !important; }")
            old_left = []
            # the sign-up's cards
            pg.evaluate("()=>{ try{ showClassSelection(); }catch(e){ window.__err = String(e); } }"); pg.wait_for_timeout(1300)
            for key in ("academy", "ifc"): judge(tag, "signup", key, place_read(pg, ".classselect-panel .class-card.is-%s .cc-emblem" % key, key))
            st = pg.evaluate("""()=>{ const a = document.querySelector('.classselect-panel .class-card.is-academy'), b = document.querySelector('.classselect-panel .class-card.is-ifc');
              if(!a || !b) return null; const before = [getComputedStyle(a).borderTopColor, getComputedStyle(a).boxShadow];
              a.click(); const after = [getComputedStyle(a).borderTopColor, getComputedStyle(a).boxShadow];
              return { before, after, picked: a.classList.contains('is-picked'), other: [getComputedStyle(b).borderTopColor, getComputedStyle(b).boxShadow] }; }""")
            chk("[%s] S signup: a picked card's edge and light differ from an unpicked one's" % tag,
                st and st["picked"] and st["after"] != st["other"] and st["after"] != st["before"], st)
            old_left += pg.evaluate(OLDIDS)
            # Classes (Add a class)
            pg.evaluate("()=>showClassCatalog('home')"); pg.wait_for_timeout(1300)
            for key in ("academy", "ifc"): judge(tag, "catalog", key, place_read(pg, ".class-catalog .class-card.is-%s .cc-emblem" % key, key))
            here = pg.evaluate("""()=>{ const h = document.querySelector('.class-catalog .class-card.is-here'), o = document.querySelector('.class-catalog .class-card:not(.is-here):not(.is-soon)');
              const look = el => { const c = getComputedStyle(el); return [c.borderTopColor, c.boxShadow, c.backgroundImage, c.backgroundColor].join(' | '); };
              return h && o ? { here: look(h), other: look(o) } : null; }""")
            chk("[%s] S catalog: the class you are in is drawn apart from the other (its edge, light or fill)" % tag, here and here["here"] != here["other"], here)
            old_left += pg.evaluate(OLDIDS)
            # Fire Code's enroll page
            pg.evaluate("()=>showIfcEnroll()"); pg.wait_for_timeout(1100)
            judge(tag, "enroll", "ifc", place_read(pg, ".class-enroll .ce-emblem", "ifc"))
            old_left += pg.evaluate(OLDIDS)
            # the class button's list (the other class)
            other = "ifc" if cls == "academy" else "academy"
            pg.evaluate("()=>{ showHome(); }"); pg.wait_for_timeout(1500); G.clear_popups(pg)
            pg.evaluate("()=>{ const b = document.querySelector('.class-bubble'); b && b.click(); }"); pg.wait_for_timeout(1100)
            judge(tag, "list", other, place_read(pg, ".class-stack-item.is-%s .csi-bubble" % other, other))
            old_left += pg.evaluate(OLDIDS)
            pg.evaluate("()=>{ try{ classListClose && classListClose(); }catch(e){} document.querySelectorAll('.daily-alert').forEach(n => n.remove()); showHome(); }"); pg.wait_for_timeout(1300)
            # the banners
            for key in ("academy", "ifc"):
                pg.evaluate("(k)=>{ document.querySelectorAll('.daily-alert').forEach(n => n.remove()); try{ a2hsHolds = () => false; }catch(e){} showEnrolledBanner([k]); }", key)
                pg.wait_for_timeout(1500)
                judge(tag, "enrolled", key, place_read(pg, "#enrolled-banner .app-banner-face > *", key))
                old_left += pg.evaluate(OLDIDS)
            pg.evaluate("""()=>{ document.querySelectorAll('.daily-alert').forEach(n => n.remove()); try{ localStorage.removeItem('class26e.greet.' + (window.NOVA_CLASS === 'ifc' ? 'ifc' : 'academy')); }catch(e){}
              window.NOVA_CLASS_ARRIVE = { to: window.NOVA_CLASS === 'ifc' ? 'ifc' : 'academy' }; switchWelcomeDone = false; switchWelcomeTimer = 0;
              try{ whatsNewHolds = () => false; a2hsBusy = () => false; a2hsHolds = () => false; }catch(e){} maybeSwitchWelcome(); }""")
            pg.wait_for_timeout(3200)
            judge(tag, "back", cls, place_read(pg, "#classback-banner .app-banner-face > *", cls))
            old_left += pg.evaluate(OLDIDS)
            if cls == "academy":
                pg.evaluate("""()=>{ document.querySelectorAll('.daily-alert').forEach(n => n.remove()); try{ localStorage.removeItem(NEW_CLASS_SEEN_KEY); }catch(e){}
                  enrolledClasses = () => ['academy']; newClassBannerDue = () => Promise.resolve(true); newClassTimer = 0; newClassPulseOn = false;
                  try{ whatsNewHolds = () => false; a2hsBusy = () => false; a2hsHolds = () => false; }catch(e){} maybeNewClassBanner(); }""")
                pg.wait_for_timeout(5200)
                judge(tag, "newclass", "ifc", place_read(pg, "#newclass-banner .app-banner-face > *", "ifc"))
                old_left += pg.evaluate(OLDIDS)
            chk("[%s] O no place showed NOVA_CLASSES' old icon markup (its gradient ids found: %s)" % (tag, sorted(set(old_left))), not old_left, sorted(set(old_left)))
            chk("[%s] no page errors" % tag, not pg.errs and not pg.evaluate("()=>window.__err || null"), pg.errs[:3])
            pg.ctx.close()
    br.close()
print("\n%s - %d failed" % ("ALL PASS" if not G.fails else "FAIL", len(G.fails)))
sys.exit(1 if G.fails else 0)
