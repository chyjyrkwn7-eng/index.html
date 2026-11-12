"""Build 384.73 (the audit fixes): load the Fire Code or the academy class from a given index.html and a given ifc/bank.js and
read what the app itself makes of them (every question's key, wording, choices, the sizes, the identity tables).

Used by tools/check-b384-qfix.py and, to dump main's keys, by hand:
    python3 tools/b384_qfix_lib.py dump OUT.json [--html FILE] [--bank FILE] [--class ifc|academy]
The fixture is the one the other Fire Code gates use (check-b383-ifcsync's prefix: an in-memory Firestore, a seeded finished account)."""
import os, sys, json, re, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)

def fixture():
    src = open(os.path.join(HERE, "check-b383-ifcsync.py"), encoding="utf-8").read().split("\nwith sync_playwright() as pw:")[0]
    G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b384qfix"}
    saved = sys.argv
    sys.argv = [saved[0]]                      # check-b383-ifcsync reads --against from argv; this lib never wants it
    try:
        exec(src, G)
    finally:
        sys.argv = saved
    return G

def git_show(rev, path):
    return subprocess.run(["git", "-C", ROOT, "show", rev + ":" + path], capture_output=True, text=True).stdout

def bank_of(js):
    return json.loads(js[js.index("window.IFC_BANK = ") + 18:].rstrip().rstrip(";"))

# what the page itself says about its questions, in whichever class it is
READ = """()=>({ cls: window.NOVA_CLASS, build: typeof APP_BUILD !== 'undefined' ? APP_BUILD : null,
  rows: QUESTIONS.map((q,i)=>({ id: q.ifc && q.ifc.id, key: KEYS[i], topic: q.topic, src: q.src, q: q.q, ch: q.choices, ans: q.answer,
    expl: q.explanation, keyText: q.keyText == null ? null : q.keyText, keyChoices: q.keyChoices || null, ifc: q.ifc ? JSON.stringify(q.ifc) : null })),
  sizes: window.NOVA_CLASS === 'ifc' ? (window.IFC_BANK.units||[]).map(u=>({ id: u.id, topic: ifcUnitTopic(u), n: u.questionCount, cache: unitQuestionCount(ifcUnitTopic(u)),
    run: QUESTIONS.filter(q => (q.topic || '').trim() === ifcUnitTopic(u) && inWholeUnit(q)).length })) : [],
  meta: window.NOVA_CLASS === 'ifc' ? window.IFC_BANK.meta.questionCount : null,
  tables: window.NOVA_CLASS === 'ifc' ? { moved: IFC_MOVED_KEYS, retired: IFC_RETIRED_KEYS, gaps: IFC_SRC_GAPS, keyText: IFC_KEY_TEXT, keyChoices: IFC_KEY_CHOICES,
    countText: ifcQuestionCountText() } : null })"""

class Rig:
    """One browser, opened once; open() gives a page on `html` (a string, or a function of the safe-area insets) and `bank`."""
    def __init__(self, G, pw):
        self.G = G; self.br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    def close(self):
        try: self.br.close()
        except Exception: pass
    def open(self, html, bank, init_extra="", klass="ifc"):
        G = self.G
        ctx = self.br.new_context(viewport={"width": 440, "height": 956}, has_touch=True)
        ctx.add_init_script("window.__cloudSeed = {};"); ctx.add_init_script(G["FAKE"]); ctx.add_init_script(G["g"]["STANDALONE"])
        ctx.add_init_script(G["init"](G["ifc"], klass) + init_extra)
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
        pg.on("console", lambda m: errs.append("console: " + m.text[:200]) if m.type == "error" and "firebase" not in m.text.lower() and "ERR_" not in m.text and "Failed to load resource" not in m.text else None)
        body = html((59, 0, 34, 0)) if callable(html) else html
        pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
        pg.route("**/ifc/bank.js*", lambda route, request, b=bank: route.fulfill(status=200, headers={"content-type": "text/javascript; charset=utf-8"}, body=b))
        m = re.search(r'const APP_BUILD = "([^"]+)"', body)
        if m:   # the page's own build is the one version.json names, so an older build is not sent off to update itself mid-check
            pg.route("**/version.json*", lambda route, request, v=m.group(1): route.fulfill(status=200, headers={"content-type": "application/json"},
                     body=json.dumps({"build": v, "force": False, "frameId": "", "safariSound": True})))
        pg.goto(G["serve_url"]); pg.wait_for_timeout(3500); pg.evaluate("document.getElementById('splashscreen')?.remove()")
        return ctx, pg, errs
    def read(self, html, bank, init_extra="", klass="ifc"):
        ctx, pg, errs = self.open(html, bank, init_extra, klass)
        out = pg.evaluate(READ); ctx.close()
        return out, errs

def main():
    from playwright.sync_api import sync_playwright
    a = sys.argv[1:]
    if not a or a[0] != "dump" or len(a) < 2:
        print(__doc__); sys.exit(2)
    out = a[1]; html = open(a[a.index("--html") + 1], encoding="utf-8").read() if "--html" in a else open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    bank = open(a[a.index("--bank") + 1], encoding="utf-8").read() if "--bank" in a else open(os.path.join(ROOT, "ifc", "bank.js"), encoding="utf-8").read()
    klass = a[a.index("--class") + 1] if "--class" in a else "ifc"
    G = fixture(); IR = G["g"]["INSET_RE"]
    body = IR.sub(lambda m: {"top": "59px", "right": "0px", "bottom": "34px", "left": "0px"}[m.group(1)], html)
    with sync_playwright() as pw:
        rig = Rig(G, pw)
        res, errs = rig.read(body, bank, "", klass); rig.close()
    json.dump(res, open(out, "w"), ensure_ascii=False)
    print("wrote", out, len(res["rows"]), "questions; page errors:", errs[:3])

if __name__ == "__main__":
    main()
