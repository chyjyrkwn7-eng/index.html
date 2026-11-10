"""Build 384 r20: the Contributors list is short and even, and the Terms of Use ends with the app icon.
Madison: "Cameron Wharton has more listed things than me and I'm the creator.. remove 'the original idea for the app' and 'Virtual Room design'. Ensure the
way his stuff is listed is nice and simple, we want this screen and wording to have that iOS feel of simplicity. That goes for everyone's stuff under their name.
Update the terms of use screen, put the nova icon at the bottom."
 (1) on Contributors: neither removed line is anywhere on the page; Cameron Wharton lists no more rows than the founder; every row is a short phrase (<= 32 chars,
     no sentence, no full stop);
 (2) the founder is first and the co-founder second, as asked before;
 (3) Terms of Use: an image of the app icon, centred, 60-96px, is the last thing on the page, under the cards (and Legal / Privacy have none);
 (4) no page errors.
Run:  python3 tools/check-b384-credits2.py   (--against OLD/index.html must FAIL)"""
import os, sys, re, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
if "--against" in sys.argv:
    body = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
    cb.BODY = cb.INSET_RE.sub("0px", body).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
with sync_playwright() as pw:
    br = pw.chromium.launch()
    ctx, pg = cb.booted(br, 440, 956, seed=cb.USED_ACCOUNT, dpr=2)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:140]))
    pg.evaluate("()=>showCredits()"); pg.wait_for_timeout(1200)
    d = pg.evaluate("""()=>({ text: document.getElementById('stage').innerText, cards: [...document.querySelectorAll('#stage .credits-card')].map(c => ({ name: (c.querySelector('.credits-name')||{}).textContent, rows: [...c.querySelectorAll('.credits-item')].map(r => r.textContent.trim()) })) })""")
    chk("(1) 'the original idea' and 'Virtual Room design' are gone", not re.search(r"original idea|virtual room design", d["text"], re.I), d["text"][:200])
    by = {c["name"]: c["rows"] for c in d["cards"]}
    mad, cam = by.get("Madison Davis"), by.get("Cameron Wharton")
    chk("(1) Cameron Wharton lists no more rows than the founder (%s vs %s)" % (cam and len(cam), mad and len(mad)), mad and cam and len(cam) <= len(mad), [mad, cam])
    rows = [r for c in d["cards"] for r in c["rows"]]
    chk("(1) every row is a short phrase: <= 32 characters, no full stop (%s)" % [r for r in rows if len(r) > 32 or r.endswith(".")], rows and all(len(r) <= 32 and not r.endswith(".") for r in rows), rows)
    names = [c["name"] for c in d["cards"]]
    chk("(2) the founder first, the co-founder second (%s)" % names[:3], names[:2] == ["Madison Davis", "Cameron Wharton"], names)
    pg.evaluate("()=>showSettingsText('terms')"); pg.wait_for_timeout(1200)
    t = pg.evaluate("""()=>{ const st=document.getElementById('stage'); const img=st.querySelector('img.settings-text-appicon'); if(!img) return null; const r=img.getBoundingClientRect(), p=st.querySelector('.screen-settings-sub').getBoundingClientRect();
      const cards=[...st.querySelectorAll('.settings-card')]; const lastCard=cards[cards.length-1].getBoundingClientRect(); const all=[...st.querySelectorAll('.screen-settings-sub > *')]; 
      return { w: r.width, h: r.height, cx: r.left + r.width/2, pcx: p.left + p.width/2, below: r.top >= lastCard.bottom, last: all[all.length-1] === img, loaded: img.complete && img.naturalWidth > 0, src: img.src.slice(0, 30) }; }""")
    chk("(3) Terms of Use ends with the app icon, centred, under the cards (%s)" % t, t and 60 <= t["w"] <= 96 and abs(t["cx"] - t["pcx"]) <= 2 and t["below"] and t["last"] and t["loaded"], t)
    pg.screenshot(path="/tmp/claude-0/-home-user/920022cb-51dc-5785-b32b-503aff219f98/scratchpad/terms.png", full_page=True)
    pg.evaluate("()=>showSettingsText('legal')"); pg.wait_for_timeout(800)
    chk("(3) Legal has no icon", pg.evaluate("()=>!document.querySelector('#stage img.settings-text-appicon')"))
    chk("(4) no page errors", not errs, errs)
    br.close()
print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
