"""Build 382, Fire Code art: in the Fire Code class every character that is not a starter and not a rank
reward, and every banner but the three rank banners, is drawn differently from the academy's (a hash of
its drawing); the starters and the rank art are the academy's own; everything draws without an error;
Zeus is not in the Fire Code class's list (it is in the academy's), and a Fire Code account saved
wearing Zeus comes back on a character it holds, with nothing else lost.
Run:  python3 tools/check-b382-ifcart.py   (add --against old.html: copy it over index.html first, as the other checks do)"""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); H = ROOT + "/tools"
src = open(H + "/record-landing.py").read().split("\nSCENES = {")[0]
g = {"__file__": H + "/record-landing.py", "__name__": "rl"}; exec(src, g)
from playwright.sync_api import sync_playwright
rc = g["g"]; seed = dict(rc["SEED"]); seed["publicId"] = "xph5b57jbp5a"; seed["firstName"] = "Maddog"; seed["novaMet"] = 99
srv, port = rc["serve"]()
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else info)
STARTERS = ["ninja", "ghost", "wizard", "grizzly", "alien"]
RANK_CHARS = ["lunar", "solar", "tempest", "frost", "oracle", "inferno"]
RANK_BANNERS = ["adept_rank", "elite_rank", "titan_rank"]
# a Fire Code copy of the account, saved wearing Zeus, with a little progress that must survive
ifc_seed = dict(seed); ifc_seed["avatarChar"] = "zeus"; ifc_seed["lifetime"] = dict(seed["lifetime"], points=4321, correct=777); ifc_seed["pendingCharUnlocks"] = ["zeus"]
SNAP = """()=>{
  const hash = s => { let h = 2166136261; for(let i = 0; i < s.length; i++){ h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0).toString(16); };
  const errs = [];
  const chars = {}, banners = {};
  AVATAR_CHARACTERS.filter(c => !c.retired).forEach(c => {
    try{
      const s = drawAvatarCharSVG(c.id); const uid = s.getAttribute('data-cx-uid');
      chars[c.id] = hash(new XMLSerializer().serializeToString(s).split(uid).join('U'));
      const b = buildAvatarCharSVG(c.id); if(!b || !b.querySelector('.cx-fig')) errs.push('char ' + c.id + ' empty');
    }catch(e){ errs.push('char ' + c.id + ': ' + e); }
  });
  BANNERS.forEach(b => {
    try{
      banners[b.id] = hash(bannerStaticSVG(b.id) || '');
      const el = buildBannerArt(b.id); if(!el || !el.querySelector('svg')) errs.push('banner ' + b.id + ' empty');
      if(!bannerTintOf(b.id)) errs.push('banner ' + b.id + ' has no tint');
    }catch(e){ errs.push('banner ' + b.id + ': ' + e); }
  });
  return { chars, banners, errs, ids: AVATAR_CHARACTERS.map(c => c.id), avatar: store.avatarChar, xp: store.lifetime && [store.lifetime.points, store.lifetime.correct],
    pending: store.pendingCharUnlocks || [], zeusDraws: (() => { try{ const s = buildAvatarCharSVG('zeus'); return s ? s.getAttribute('data-char') : null; }catch(e){ return 'ERR'; } })(),
    cls: window.NOVA_CLASS };
}"""
res = {}
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    for ifc in (False, True):
        ctx, pg = rc["new_page"](br, port, 440, 956, seed)
        perr = []
        pg.on("pageerror", lambda e: perr.append(str(e)))
        if ifc:
            pg.add_init_script("try{ if(!localStorage.getItem('class26e.ifc.drill.v1')) localStorage.setItem('class26e.ifc.drill.v1', %s); }catch(e){}" % json.dumps(json.dumps(ifc_seed)))
            pg.evaluate("()=>{ localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done'); localStorage.setItem('class26e.activeclass','ifc'); }")
        pg.reload(); pg.wait_for_timeout(3500)
        r = pg.evaluate(SNAP); r["perr"] = perr
        res["ifc" if ifc else "academy"] = r
        ctx.close()
    br.close()
A, F = res["academy"], res["ifc"]
chk("the pages are the two classes (%s, %s)" % (A["cls"], F["cls"]), A["cls"] == "academy" and F["cls"] == "ifc")
chk("no page errors (%s)" % (A["perr"] + F["perr"])[:3], not A["perr"] and not F["perr"])
chk("every character and banner draws in both classes (%s)" % (A["errs"] + F["errs"])[:4], not A["errs"] and not F["errs"])
redo = [i for i in F["chars"] if i not in STARTERS and i not in RANK_CHARS]
same = [i for i in redo if F["chars"].get(i) == A["chars"].get(i)]
chk("Fire Code redraws all %d non-starter, non-rank characters (unchanged: %s)" % (len(redo), same), len(redo) >= 15 and not same, same)
kept = [i for i in STARTERS + RANK_CHARS if F["chars"].get(i) != A["chars"].get(i)]
chk("the starters and the rank characters are the academy's own (changed: %s)" % kept, not kept, kept)
bredo = [i for i in F["banners"] if i not in RANK_BANNERS]
bsame = [i for i in bredo if F["banners"].get(i) == A["banners"].get(i)]
chk("Fire Code redraws all %d non-rank banners (unchanged: %s)" % (len(bredo), bsame), len(bredo) >= 15 and not bsame, bsame)
bkept = [i for i in RANK_BANNERS if F["banners"].get(i) != A["banners"].get(i)]
chk("the rank banners are the academy's own (changed: %s)" % bkept, not bkept, bkept)
chk("Zeus is in the academy's list", "zeus" in A["ids"])
chk("Zeus is not in the Fire Code list", "zeus" not in F["ids"], F["ids"])
chk("a Fire Code account saved wearing Zeus wears a starter now (%s)" % F["avatar"], F["avatar"] in STARTERS, F["avatar"])
chk("...and Zeus is out of its unlocks to announce (%s)" % F["pending"], "zeus" not in F["pending"])
chk("...and nothing else was lost (xp %s)" % F["xp"], F["xp"] == [4321, 777], F["xp"])
chk("a stray Zeus id still draws, as a starter (%s)" % F["zeusDraws"], F["zeusDraws"] in STARTERS)
sys.exit(0 if ok else 1)
