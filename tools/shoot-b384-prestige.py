"""384.126 prestige: screenshots for Madison. Fire Code, a real-shaped account at each stage (tools/b384_prestige_lib.py), classmates on
the board holding Prestige I, II and III.

  python3 tools/shoot-b384-prestige.py OUTDIR [--dev pm|ipad] [--theme dark|light] [--only name,name]

Shots: the Prestige screen not eligible / eligible / taken (I) / max (III), the confirm step, the ceremony (its build and the reward
cards), Profile, the Leaderboard, a person card and a friend's profile with each emblem, Customize's Prestige groups (character and
banner), the art sheet (the three characters live and greyed, three banners as a Customize tile / the person card's cover / a
Leaderboard row's edge, three emblems large and at name size)."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b384_prestige_lib as L
from playwright.sync_api import sync_playwright

ARGS = sys.argv[1:]
OUT = ARGS[0] if ARGS and not ARGS[0].startswith("--") else "/dev/shm/pg-shots"
def arg(n, d=None): return ARGS[ARGS.index(n) + 1] if n in ARGS else d
DEV = arg("--dev", "pm"); THEME = arg("--theme", "dark"); ONLY = set((arg("--only") or "").split(",")) - {""}
W, H = (440, 956) if DEV == "pm" else (834, 1194)
os.makedirs(OUT, exist_ok=True)
def want(n): return not ONLY or n in ONLY

text = open(arg("--file", os.path.join(L.ROOT, "index.html")), encoding="utf-8").read()
FRIENDS = ["pgmate00000", "pgmate00001", "pgmate00002"]

def shot(pg, name, full=False):
    p = os.path.join(OUT, "%s-%s-%s.png" % (DEV, THEME, name))
    pg.screenshot(path=p, full_page=full)
    print("shot", p, flush=True)

def settle(pg, ms=900):
    pg.wait_for_timeout(ms)

SET_THEME = """(t)=>{ try{ theme.mode = t; }catch(e){} try{ document.documentElement.setAttribute('data-theme', t); }catch(e){} try{ saveTheme(); applyTheme(); }catch(e){} }"""

with sync_playwright() as p:
    br = p.chromium.launch(executable_path=L.CHROME, args=["--no-sandbox"])
    fc = L.account(ifc=True, extra={"theme": THEME})
    seed, init = L.ifc_seed(fc, friends=FRIENDS)
    ctx, pg, errs = L.page(br, text, seed, init, w=W, h=H, scale=2, color_scheme=THEME)
    pg.evaluate(SET_THEME, THEME)
    L.quiet(pg)
    print("class", pg.evaluate("window.NOVA_CLASS"), flush=True)
    pg.evaluate("()=>{ try{ showRankings(); }catch(e){} }"); settle(pg, 2500)
    # ---- not eligible
    L.build(pg, "none"); L.quiet(pg)
    if want("req"):
        pg.evaluate("()=>showPrestige()"); settle(pg); shot(pg, "prestige-0-not-eligible")
        pg.evaluate("()=>showUnlockTracks()"); settle(pg); shot(pg, "tracks-entry-not-eligible")
    # ---- eligible for I
    L.build(pg, "one"); L.quiet(pg)
    if want("req"):
        pg.evaluate("()=>showPrestige()"); settle(pg); shot(pg, "prestige-1-eligible")
        pg.evaluate("()=>showCustomize()"); settle(pg, 1400); shot(pg, "customize-nextup-entry")
    if want("confirm"):
        pg.evaluate("()=>{ showPrestige(); confirmPrestige(1); }"); settle(pg, 1200); shot(pg, "confirm-1")
        pg.evaluate("()=>document.querySelectorAll('.invite-overlay').forEach(n=>n.remove())")
    if want("scene"):
        pg.evaluate("()=>{ showPrestige(); if(takePrestige(1)) playPrestigeScene(1); }")
        pg.wait_for_timeout(1500); shot(pg, "scene-1-flash")
        pg.wait_for_timeout(3600); shot(pg, "scene-1-cards")
        pg.evaluate("()=>{ const s = document.querySelector('.pg-scene'); if(s) s.__nova.skip(); }"); settle(pg, 1200)
    else:
        pg.evaluate("()=>takePrestige(1)")
    if want("taken"):
        pg.evaluate("()=>showPrestige()"); settle(pg); shot(pg, "prestige-2-taken-I")
        pg.evaluate("()=>{ const c = document.querySelector('.pg-card-2'); if(c) c.scrollIntoView({ block: 'start' }); }"); settle(pg, 400); shot(pg, "prestige-2-taken-I-next")
    if want("names"):
        pg.evaluate("()=>{ store.avatarChar = 'pgdeputy'; store.banner = 'pgoath'; saveStore(); showProfile(); }"); settle(pg, 1600); shot(pg, "profile-I")
        pg.evaluate("()=>{ showRankings(); }"); settle(pg, 2600); shot(pg, "leaderboard")
        pg.evaluate("()=>{ const e = (classBoardRows || []).find(r => r.firstName === 'Alexis'); if(e) openPersonSheet(Object.assign({}, e, { boardCls: ART_PAGE })); }"); settle(pg, 1500); shot(pg, "personcard-III")
        pg.evaluate("()=>document.querySelectorAll('.invite-overlay').forEach(n=>n.remove())")
        pg.evaluate("()=>{ const e = (classBoardRows || []).find(r => r.firstName === 'Kimber'); if(e) openPersonSheet(Object.assign({}, e, { boardCls: ART_PAGE })); }"); settle(pg, 1500); shot(pg, "personcard-II")
        pg.evaluate("()=>document.querySelectorAll('.invite-overlay').forEach(n=>n.remove())")
        pg.evaluate("()=>{ const e = (classBoardRows || []).find(r => r.pub === publicIdOf()) || { pub: publicIdOf(), firstName: store.firstName, avatarChar: store.avatarChar, banner: store.banner, level: 80, badges: 58 }; openPersonSheet(Object.assign({}, e, { boardCls: ART_PAGE })); }"); settle(pg, 1500); shot(pg, "personcard-own-I")
        pg.evaluate("()=>document.querySelectorAll('.invite-overlay').forEach(n=>n.remove())")
        for nm, tag in (("Alexis", "III"), ("Kimber", "II"), ("Leeland", "I")):
            pg.evaluate("(n)=>{ const e = (classBoardRows || []).find(r => r.firstName === n); if(e) showFriendProfile(e); }", nm); settle(pg, 1800); shot(pg, "friendprofile-" + tag)
    if want("custom"):
        pg.evaluate("()=>showCustomize('character')"); settle(pg, 1500)
        pg.evaluate("()=>{ const t = [...document.querySelectorAll('.cz-group-title, .avatarchar-group-title')].find(n => /Prestige/.test(n.textContent)); if(t) t.scrollIntoView({ block: 'center' }); }"); settle(pg, 900); shot(pg, "customize-characters")
        pg.evaluate("()=>showCustomize('banner')"); settle(pg, 1800)
        pg.evaluate("()=>{ const t = [...document.querySelectorAll('.cz-group-title, h3, h2')].find(n => /^Prestige/.test(n.textContent)); if(t) t.scrollIntoView({ block: 'center' }); }"); settle(pg, 1500); shot(pg, "customize-banners")
    # ---- max: everything, then II and III taken
    L.build(pg, "all"); L.quiet(pg)
    pg.evaluate("()=>{ takePrestige(2); }")
    if want("req"):
        pg.evaluate("()=>showPrestige()"); settle(pg)
        pg.evaluate("()=>{ const c = document.querySelector('.pg-card-3'); if(c) c.scrollIntoView({ block: 'start' }); }"); settle(pg, 500); shot(pg, "prestige-3-eligible-III")
    if want("confirm"):
        pg.evaluate("()=>{ confirmPrestige(3); }"); settle(pg, 1200); shot(pg, "confirm-3")
        pg.evaluate("()=>document.querySelectorAll('.invite-overlay').forEach(n=>n.remove())")
    if want("scene"):
        pg.evaluate("()=>{ if(takePrestige(3)) playPrestigeScene(3); }")
        pg.wait_for_timeout(1500); shot(pg, "scene-3-flash")
        pg.wait_for_timeout(3600); shot(pg, "scene-3-cards")
        pg.evaluate("()=>{ const s = document.querySelector('.pg-scene'); if(s) s.__nova.skip(); }"); settle(pg, 1200)
    else:
        pg.evaluate("()=>takePrestige(3)")
    if want("req"):
        pg.evaluate("()=>showPrestige()"); settle(pg); shot(pg, "prestige-4-max")
    if want("names"):
        pg.evaluate("()=>{ store.avatarChar = 'pgstate'; store.banner = 'pglaurel'; saveStore(); showProfile(); }"); settle(pg, 1600); shot(pg, "profile-III")
        pg.evaluate("()=>{ showRankings(); }"); settle(pg, 2600); shot(pg, "leaderboard-max")
    if want("art"):
        pg.evaluate("""()=>{ const box = document.createElement('div'); box.id='pgsheet';
          box.style.cssText='position:fixed;inset:0;z-index:99999;background:var(--bg,#111);overflow:auto;padding:12px;display:grid;gap:10px;align-content:start;font-family:system-ui;color:var(--ink,#fff)';
          const lab = t => { const p = document.createElement('div'); p.textContent = t; p.style.cssText='font:700 12px system-ui;opacity:.8'; return p; };
          const row = () => { const r = document.createElement('div'); r.style.cssText='display:flex;flex-wrap:wrap;gap:10px;align-items:center'; box.appendChild(r); return r; };
          box.appendChild(lab('Characters: live (as Customize and the person card draw them), then not yet taken (greyed, as Customize shows a locked one)'));
          let r = row();
          ['pgdeputy','pgmarshal','pgstate'].forEach(id => { const s = document.createElement('span'); s.className='rank-avatar'; s.style.cssText='width:116px;height:116px;display:block;border-radius:50%;overflow:hidden;background:radial-gradient(circle at 50% 60%,'+avatarGlowColor(id)+'55,#0B0E14 74%)'; const w = document.createElement('span'); w.style.cssText='display:block;width:100%;height:100%'; w.appendChild(buildAvatarCharSVGSafe(id)); s.appendChild(w); setCharState(s, 'live'); r.appendChild(s); });
          ['pgdeputy','pgmarshal','pgstate'].forEach(id => { const s = document.createElement('span'); s.style.cssText='width:76px;height:76px;display:block;border-radius:50%;overflow:hidden;background:#0B0E14'; const svg = buildAvatarCharSVGSafe(id); svg.classList.add('char-locked-grey'); svg.style.cssText='width:100%;height:100%'; s.appendChild(svg); r.appendChild(s); });
          box.appendChild(lab('Emblems: large, then at name size (17px) on dark and light'));
          r = row();
          [1,2,3].forEach(n => { const s = document.createElement('span'); s.style.cssText='width:96px;height:96px;display:block'; const e = buildPrestigeEmblemSVG(n); e.style.cssText='width:100%;height:100%'; s.appendChild(e); r.appendChild(s); });
          ['#0B0E14','#F4F5F7'].forEach(bg => { const t = document.createElement('span'); t.style.cssText='padding:6px 10px;border-radius:10px;font:700 16px system-ui;background:'+bg+';color:'+(bg==='#F4F5F7'?'#10131A':'#FFFFFF'); t.textContent='Alexis'; [1,2,3].forEach(n => t.appendChild(prestigeMark(n))); r.appendChild(t); });
          box.appendChild(lab('Banners: Customize tile, the person card cover (with the character circle), a Leaderboard row edge (the still picture)'));
          ['pgoath','pgcommand','pglaurel'].forEach((id, i) => { const rr = row();
            const tile = document.createElement('div'); tile.style.cssText='width:170px;height:64px;position:relative;overflow:hidden;border-radius:12px'; const a = buildBannerArt(id); a.style.cssText='position:absolute;inset:0'; tile.appendChild(a); rr.appendChild(tile);
            const cov = document.createElement('div'); cov.style.cssText='width:300px;height:112px;position:relative;overflow:hidden;border-radius:14px'; const b = buildBannerArt(id); b.style.cssText='position:absolute;inset:0'; cov.appendChild(b);
            const c = document.createElement('span'); c.style.cssText='position:absolute;left:50%;bottom:-34px;width:84px;height:84px;margin-left:-42px;border-radius:50%;overflow:hidden;background:#0B0E14;box-shadow:0 0 0 3px #0B0E14'; const sv = buildAvatarCharSVGSafe(['pgdeputy','pgmarshal','pgstate'][i]); sv.style.cssText='width:100%;height:100%'; c.appendChild(sv); cov.appendChild(c); rr.appendChild(cov);
            const edge = document.createElement('div'); edge.style.cssText='width:400px;height:56px;border-radius:14px;background-size:cover;background-position:center;background-image:url("'+bannerRowStillURL(id)+'")'; rr.appendChild(edge); });
          document.body.appendChild(box); }""")
        settle(pg, 2200); shot(pg, "artsheet")
    print("errors", errs, flush=True)
    br.close()
