#!/usr/bin/env python3
"""384 (profilerows2, options to pick from): Profile's three entry rows - the Rank ladder (finished), the Badge case (options a|b|c)
and Customize (options a|b|c) - on an iPhone 17 Pro Max (440x956, installed, 3x) and an iPad Pro 11" (834x1194, installed, 2x), in
both classes.

  python3 tools/shoot-b384-profilerows2.py OUT_DIR [--devs phone-installed,ipad-pro-11] [--classes academy,ifc]
         [--opts a,b,c]          # the badge / customize option shown (both rows take the same letter in one shot; customize also d|e)
         [--badge row|a|b|c]     # (384 ui3) the Badge case whatever --opts says (row = the default, B's words beside the row icon)
         [--rank none|first|mid|last]   # where the account stands on the ladder (default: a middle rank)
         [--video] [--video-only]  # also (only) record each option animating in (Playwright's recorder, then H.264 with ffmpeg)
         [--against REV|FILE]    # the build to render (default: this tree's index.html)

Options are chosen by the address: ?pfbadge=a|b|c&pfcz=a|b|c (the head script puts html[data-pfrow-badge] / [data-pfrow-cz]).
For each device, class and option it opens Profile on a fixed account and cuts out the three rows
(rows-<dev>-<class>-<opt>-<rank>.png) and the page from the person card to the Next rank card (profile-....png)."""
import json, os, re, shutil, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b384_seg_lib as L
from playwright.sync_api import sync_playwright

def _pos():
    out, skip = [], False
    for i, a in enumerate(sys.argv[1:]):
        if skip: skip = False; continue
        if a in ("--devs", "--classes", "--opts", "--rank", "--against", "--badge"): skip = True; continue
        if a.startswith("--"): continue
        out.append(a)
    return out
P = _pos()
if not P: sys.exit(__doc__)
OUT = P[0]; os.makedirs(OUT, exist_ok=True)
DEVS = (L.arg("--devs") or "phone-installed,ipad-pro-11").split(",")
CLASSES = (L.arg("--classes") or "academy,ifc").split(",")
OPTS = (L.arg("--opts") or "a,b,c").split(",")
RANKS = (L.arg("--rank") or "mid").split(",")
VIDEO = "--video" in sys.argv
BADGE = L.arg("--badge")   # (384 ui3) the Badge case shown whatever the Customize option: "row" = the default (no ?pfbadge=), or a|b|c
def query(opt):
    b = BADGE or opt
    return "?pfcz=%s" % opt + ("" if b == "row" else "&pfbadge=%s" % b)

def open_pf(br, dev, cls, video_dir=None):
    kw = dict(viewport={"width": dev["w"], "height": dev["h"]}, device_scale_factor=dev["dpr"], user_agent=dev["ua"])
    if dev["touch"]: kw.update(has_touch=True, is_mobile=True)
    if video_dir:
        kw.update(record_video_dir=video_dir, record_video_size={"width": dev["w"] * 2, "height": dev["h"] * 2})
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
    cons = []; pg.on("console", lambda m: cons.append(m.text[:200]) if m.type == "error" and "net::ERR" not in m.text and "Failed to load resource" not in m.text else None)
    pg.set_default_timeout(180000)
    return ctx, pg, errs, cons

# The fixed account. want.rank: none (below the first rank), first, mid (a rank in the middle), last (the top; 384.135 retired
# Fire Code's prestige position). The rank is set the way the app reads it: level and badges, and rankFloor (the app's own floor) for the
# ends, so every position is a real account's.
SETUP = """async(want)=>{
  const wait = ms => new Promise(r => setTimeout(r, ms));
  document.getElementById('splashscreen')?.remove();
  try{ homeUnlocksOwed=()=>false; scheduleWeekRecap=()=>{}; maybeShowWeekRecap=()=>{}; playUnlockSpotlight=(it,n,of,release)=>{ try{ release && release(); }catch(e){} }; }catch(e){}
  store.novaMet = 99;
  document.querySelectorAll('#tour-overlay, #tour-tooltip, #nova-intro, .rs-spot, .unlock-card').forEach(n=>n.remove());
  const topics = classTopics();
  topics.forEach(u => { store.unitPerfects[u] = 0; });
  const nb = want.rank === 'last' ? topics.length : want.rank === 'none' ? 0 : want.badges;
  topics.slice(0, nb).forEach(u => { store.unitPerfects[u] = badgeThresholdFor(u); });
  const lvl = want.rank === 'none' ? 2 : want.rank === 'first' ? 22 : want.rank === 'last' ? 80 : want.level;
  store.lifetime.points = 0;
  for(let p = 0; p < 2000000; p += 1500){ store.lifetime.points = p; if(levelStateFor(store).level >= lvl) break; }
  store.rankFloor = want.rank === 'last' ? 7 : 0;
  const s = ensureSeenUnlocks();
  s.badges = badgesEarnedList().slice(0, Math.max(0, badgesEarnedList().length - want.freshBadges));
  s.chars = unlockedIdsNow().chars.slice(); if(want.freshChar && s.chars.length > 1) s.chars.pop();
  s.banners = unlockedIdsNow().banners.slice(); s.themes = unlockedIdsNow().themes.slice(); s.fx = unlockedIdsNow().fx.slice();
  const st = document.createElement('style'); st.textContent = '.bottomtabs, #bottomtabs, .bottomtab-bar{ display:none !important; }'; document.body.appendChild(st);
  showProfile('profile'); await wait(want.settle);
  return { rank: rankOf(store), level: levelStateFor(store).level, badges: badgeCountOf(store), of: topics.length, pageH: document.documentElement.scrollHeight, vw: innerWidth,
           badge: document.documentElement.getAttribute('data-pfrow-badge'), cz: document.documentElement.getAttribute('data-pfrow-cz') };
}"""

RECTS = """()=>{
  const r = e => { if(!e) return null; const q = e.getBoundingClientRect(); return [q.left, q.top + scrollY, q.width, q.height]; };
  const q = sel => document.querySelector('#stage .screen-profile ' + sel);
  return { hero: r(q('.profile-hero')), goal: r(q('.pf-goal')),
    entries: { customize: r(q('.profile-customize-btn')), case: r(q('.pf-case')), ladder: r(q('.pf-goal-foot')) } };
}"""

def want_for(cls, rank, settle):
    return {"badges": 12 if cls == "ifc" else 7, "freshBadges": 2 if cls == "academy" else 0, "freshChar": cls == "academy",
            "level": 36 if cls == "academy" else 45, "rank": rank, "settle": settle}

def mp4(src, dst, start=0):
    ff = shutil.which("ffmpeg") or "/usr/bin/ffmpeg"
    subprocess.run([ff, "-y", "-loglevel", "error", "-ss", "%.2f" % start, "-i", src, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-movflags", "+faststart", dst], check=True)
    os.remove(src)

def main():
    srv, url = L.g["serve"]()
    res = json.load(open(os.path.join(OUT, "shots.json"))) if "--video-only" in sys.argv and os.path.exists(os.path.join(OUT, "shots.json")) else {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=L.g["CHROME"])
        for dev in L.DEVICES:
            if dev["name"] not in DEVS: continue
            for cls in CLASSES:
                for opt in OPTS:
                    for rank in ([] if "--video-only" in sys.argv else RANKS):
                        tag = "%s-%s-%s-%s" % (dev["name"], cls, opt, rank)
                        ctx, pg, errs, cons = open_pf(br, dev, cls)
                        pg.goto(url + query(opt), wait_until="load", timeout=180000)
                        pg.wait_for_timeout(3500)
                        info = pg.evaluate(SETUP, want_for(cls, rank, 2500))
                        pg.evaluate("()=>window.scrollTo({top:0, behavior:'instant'})"); pg.wait_for_timeout(400)
                        pg.set_viewport_size({"width": dev["w"], "height": min(int(info["pageH"]) + 40, 3600)}); pg.wait_for_timeout(2600)
                        info.update(pg.evaluate(RECTS))
                        full = os.path.join(OUT, "full-%s.png" % tag)
                        pg.screenshot(path=full)
                        res[tag] = {"info": info, "errors": errs, "console": cons, "full": full, "dpr": dev["dpr"]}
                        print(tag, json.dumps({k: info[k] for k in ("rank", "level", "badges", "of", "badge", "cz")}), "errors:", errs, cons[:3], flush=True)
                        ctx.close()
                    if VIDEO:
                        vd = os.path.join(OUT, "_vid"); os.makedirs(vd, exist_ok=True)
                        t_ctx = time.time()
                        ctx, pg, errs, cons = open_pf(br, dev, cls, vd)
                        pg.goto(url + query(opt), wait_until="load", timeout=180000)
                        pg.wait_for_timeout(3500)
                        # the account set up (Profile once, off camera), then the Leaderboard, then Profile again: the rows play as it opens.
                        # The clip is cut from just before that second open (the boot and any pop-up are left out).
                        pg.evaluate(SETUP, want_for(cls, "mid", 1500))
                        pg.evaluate("()=>{ try{ showRankings(); }catch(e){} document.querySelectorAll('#tour-overlay, #tour-tooltip, .rs-spot, .unlock-card').forEach(n=>n.remove()); }")
                        pg.wait_for_timeout(1200)
                        t_open = time.time() - t_ctx
                        pg.evaluate("()=>{ showProfile('profile'); window.scrollTo({top:0, behavior:'instant'}); }")
                        pg.wait_for_timeout(3600)
                        # down to the Next rank card's foot: its line draws when it comes on screen
                        pg.evaluate("()=>{ const f=document.querySelector('#stage .pf-goal-foot'); if(f) window.scrollTo({top: Math.max(0, f.getBoundingClientRect().bottom + scrollY - innerHeight + 40), behavior:'smooth'}); }")
                        pg.wait_for_timeout(5200)
                        v = pg.video; ctx.close()
                        dst = os.path.join(OUT, "anim-%s-%s-%s.mp4" % (dev["name"], cls, opt))
                        mp4(v.path(), dst, max(0, t_open - .4)); print("video", dst, errs, flush=True)
        br.close()
    json.dump(res, open(os.path.join(OUT, "shots.json"), "w"), indent=1)

main()
