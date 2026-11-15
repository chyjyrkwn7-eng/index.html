#!/usr/bin/env python3
"""384 (profilerows, TEMPORARY): Profile's Customize / Badge case / Rank ladder, as built now and as the three options behind
?pfrows=a|b|c, on an iPhone 17 Pro Max (440x956, installed, 3x) and an iPad Pro 11" (834x1194, installed, 2x), in both classes.

  python3 tools/shoot-b384-profilerows.py OUT_DIR [--devs phone-installed,ipad-pro-11] [--classes academy,ifc] [--opts none,a,b,c]
         [--against REV|FILE]     # the build to render (default: this tree's index.html)

For each device, class and option it opens Profile on a fixed account (a level with a rank and a next rank, badges held, the newest not yet
looked at, a banner worn, one Customize item unseen), takes the full page, and cuts out the person card to the end of the Next rank card
(profile-<dev>-<class>-<opt>.png) and each entry point on its own (entry-<dev>-<class>-<opt>-<customize|case|ladder>.png).
Without --opts it renders none, a, b and c.  `none` is the page with no ?pfrows (the build as it is)."""
import io, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b384_seg_lib as L
from playwright.sync_api import sync_playwright

OUT = next((a for a in sys.argv[1:] if not a.startswith("--") and not (sys.argv[sys.argv.index(a) - 1].startswith("--") if sys.argv.index(a) else False)), None)
if not OUT: sys.exit(__doc__)
os.makedirs(OUT, exist_ok=True)
DEVS = (L.arg("--devs") or "phone-installed,ipad-pro-11").split(",")
CLASSES = (L.arg("--classes") or "academy,ifc").split(",")
OPTS = (L.arg("--opts") or "none,a,b,c").split(",")

def open_pf(br, dev, cls, opt):
    """L.open_page, but its index.html route also matches an address with a query (?pfrows=a)"""
    kw = dict(viewport={"width": dev["w"], "height": dev["h"]}, device_scale_factor=dev["dpr"], user_agent=dev["ua"])
    if dev["touch"]: kw.update(has_touch=True, is_mobile=True)
    ctx = br.new_context(**kw)
    if dev["installed"]: ctx.add_init_script(L.g["STANDALONE"])
    ctx.add_init_script(L.g["FAKE_FIREBASE"].replace("__ROWS__", L.g["rows_json"]()))
    pg = ctx.new_page(); b = L.body_for(dev["ins"])
    pg.route(re.compile(r".*/index\.html(\?.*)?$"), lambda route, request: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    m = re.search(r'const APP_BUILD = "([^"]+)"', b); bld = m.group(1) if m else ""
    pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"},
             body=json.dumps({"build": bld, "note": "", "frameId": "", "force": True, "safariSound": True})))
    d = json.loads(L.g["SEED"].replace("__WEEK__", L.g["week_key_now"]())); d["publicId"] = L.OWNER; d["firstName"] = "Casey"; d["novaMet"] = 99
    pg.add_init_script(L.INIT % (json.dumps(json.dumps(d)), L.IFC if cls == "ifc" else ""))
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.set_default_timeout(180000)
    return ctx, pg, errs

# the fixed account: a rank and a next rank, a dozen badges (the newest not looked at yet), a banner worn, one Customize item unseen
SETUP = """async(want)=>{
  const wait = ms => new Promise(r => setTimeout(r, ms));
  document.getElementById('splashscreen')?.remove();
  try{ homeUnlocksOwed=()=>false; scheduleWeekRecap=()=>{}; maybeShowWeekRecap=()=>{}; playUnlockSpotlight=(it,n,of,release)=>{ try{ release && release(); }catch(e){} }; }catch(e){}
  store.novaMet = 99;
  document.querySelectorAll('#tour-overlay, #tour-tooltip, #nova-intro, .rs-spot, .unlock-card').forEach(n=>n.remove());
  const topics = classTopics();
  topics.forEach(u => { store.unitPerfects[u] = 0; });
  topics.slice(0, want.badges).forEach(u => { store.unitPerfects[u] = badgeThresholdFor(u); });
  for(let p = 4000; p < 400000; p += 1500){ store.lifetime.points = p; if(levelStateFor(store).level >= want.level) break; }
  const s = ensureSeenUnlocks();
  s.badges = badgesEarnedList().slice(0, Math.max(0, want.badges - want.freshBadges));
  s.chars = unlockedIdsNow().chars.slice(); if(want.freshChar && s.chars.length > 1) s.chars.pop();
  s.banners = unlockedIdsNow().banners.slice(); s.themes = unlockedIdsNow().themes.slice(); s.fx = unlockedIdsNow().fx.slice();
  const bn = BANNERS.filter(b => bannerEarned(b.id)).map(b => b.id);
  store.banner = bn.indexOf(want.banner) >= 0 ? want.banner : (bn[0] || '');
  const st = document.createElement('style'); st.textContent = '.bottomtabs, #bottomtabs, .bottomtab-bar{ display:none !important; }'; document.body.appendChild(st);
  showProfile('profile'); await wait(2500);
  window.scrollTo({ top: 0, behavior: 'instant' }); await wait(500);
  return { rank: rankOf(store), level: levelStateFor(store).level, badges: badgeCountOf(store), of: topics.length, banner: store.banner, pageH: document.documentElement.scrollHeight, vw: innerWidth };
}"""

RECTS = """()=>{
  const r = e => { if(!e) return null; const q = e.getBoundingClientRect(); return [q.left, q.top + scrollY, q.width, q.height]; };
  const q = sel => document.querySelector('#stage .screen-profile ' + sel);
  const trio = q('.pfx-trio');
  return { hero: r(q('.profile-hero')), goal: r(q('.pf-goal')), caseBox: r(trio || q('.pf-case')), trio: r(trio),
    entries: { customize: r(q('[data-pfx=cz]') || q('.profile-customize-btn')), case: r(q('[data-pfx=bc]') || q('.pf-case')), ladder: r(q('[data-pfx=ld]') || q('.pf-goal-foot')) },
    pageH: document.documentElement.scrollHeight, vw: innerWidth, sw: document.documentElement.scrollWidth, err: document.querySelectorAll('.pfx').length };
}"""

def main():
    srv, url = L.g["serve"]()
    res = json.load(open(os.path.join(OUT, "shots.json"))) if os.path.exists(os.path.join(OUT, "shots.json")) else {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=L.g["CHROME"])
        for dev in L.DEVICES:
            if dev["name"] not in DEVS: continue
            for cls in CLASSES:
                for opt in OPTS:
                    ctx, pg, errs = open_pf(br, dev, cls, opt)
                    pg.goto(url + ("?pfrows=" + opt if opt != "none" else ""), wait_until="load", timeout=180000)
                    pg.wait_for_timeout(3500)
                    want = {"badges": 12 if cls == "ifc" else 7, "freshBadges": 2 if cls == "academy" else 0, "freshChar": cls == "academy",
                            "level": 36 if cls == "academy" else 27, "banner": ""}
                    info = pg.evaluate(SETUP, want)
                    pg.wait_for_timeout(700)
                    tag = "%s-%s-%s" % (dev["name"], cls, opt)
                    png = os.path.join(OUT, "full-%s.png" % tag)
                    # a full-page picture of the build as it is comes back unpainted; the window is made as tall as the page instead
                    pg.set_viewport_size({"width": dev["w"], "height": min(int(info["pageH"]) + 40, 3600)}); pg.wait_for_timeout(1200)
                    info.update(pg.evaluate(RECTS)); pg.wait_for_timeout(300)
                    pg.screenshot(path=png)
                    res[tag] = {"info": info, "errors": errs, "full": png, "dpr": dev["dpr"]}
                    print(tag, json.dumps({k: info[k] for k in ("rank", "level", "badges", "of", "pageH", "vw", "sw", "err")}), "errors:", errs, flush=True)
                    ctx.close()
        br.close()
    json.dump(res, open(os.path.join(OUT, "shots.json"), "w"), indent=1)

main()
