"""Build 384.38: the link preview's description is the real sentence, and a crawler that reads only the START of the page finds it.

Madison: "Sharing link wrong description. When sharing the link, the link is there, but the description that comes with it is random
letters and numbers for some reason."

Cause (measured, see docs/notes-archive.md "384.38"): index.html is 10.5MB with a 140KB <head>. Its og:/twitter:/description tags
started at byte 45,280 (behind ~45KB of inline scripts and comments) and its <title> at byte 140,069 (behind a 78KB base64 manifest
and a 3KB base64 favicon). A link-preview crawler reads the first part of the page and stops: one that stops before ~46KB finds no
description at all and falls back to what it did read.

This gate emulates that crawler. It serves the document from a local HTTP server and reads it through a TRUNCATING reader at
1, 2, 4, 16, 64, 256KB and 1MB, parsing what is read the way a scraper does (title, og:*, twitter:*, description), for BOTH documents
a preview can land on: the app's own address (what the install page and a copied address send, and where the share page's
<noscript> meta refresh leads) and the share page (what Settings > Share sends).

Run:  python3 tools/check-b384-sharemeta.py
      python3 tools/check-b384-sharemeta.py --against OLD-index.html [--against-share OLD-share-index.html]
(--against runs it on another build's files and must FAIL there.)"""
import base64, http.server, json, os, re, socketserver, sys, threading, urllib.request
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default
APP_FILE = arg("--against", os.path.join(ROOT, "index.html"))
SHARE_FILE = arg("--against-share", os.path.join(ROOT, "share", "index.html") if "--against" not in sys.argv else None)
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:380], flush=True)

APP = open(APP_FILE, "rb").read()
SHARE = open(SHARE_FILE, "rb").read() if SHARE_FILE else b""
SRC = APP.decode("utf-8", "replace")
LIMITS = [1024, 2048, 4096, 16384, 65536, 262144, 1048576]
NEEDED_TEXT = ["title", "og:title", "og:description", "description", "og:image", "twitter:card", "twitter:title", "twitter:description", "twitter:image"]


class Scraper(HTMLParser):
    """What a link-preview crawler keeps: <title>, every meta name/property, and the visible text outside script and style."""
    def __init__(s):
        super().__init__(convert_charrefs=True)
        s.f = {}; s.text = []; s.in_title = False; s.skip = 0; s.refresh = None
    def handle_starttag(s, t, a):
        a = dict(a)
        if t == "meta":
            k = a.get("property") or a.get("name")
            if k and "content" in a: s.f.setdefault(k, a["content"])
            if (a.get("http-equiv") or "").lower() == "refresh": s.refresh = a.get("content")
        elif t == "title": s.in_title = True
        elif t in ("script", "style"): s.skip += 1
    def handle_endtag(s, t):
        if t == "title": s.in_title = False
        elif t in ("script", "style") and s.skip: s.skip -= 1
    def handle_data(s, d):
        if s.in_title: s.f.setdefault("title", d)
        elif not s.skip and d.strip(): s.text.append(d.strip())


def scrape(raw, limit):
    p = Scraper(); p.feed(raw[:limit].decode("utf-8", "replace")); return p


class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        body = APP if path in ("/", "/index.html/") else SHARE if path.startswith("/share") else None
        if body is None: self.send_response(404); self.end_headers(); return
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body))); self.end_headers()
        try: self.wfile.write(body)
        except Exception: pass
    def log_message(self, *a): pass

class S(socketserver.ThreadingMixIn, socketserver.TCPServer): allow_reuse_address = True; daemon_threads = True
srv = S(("127.0.0.1", 0), H); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()

def fetch_prefix(path, limit):
    """The crawler's read: open the address over HTTP and take only the first `limit` bytes."""
    with urllib.request.urlopen("http://127.0.0.1:%d%s" % (port, path), timeout=20) as r:
        return r.read(limit)

DOCS = [("the app's address", "/", APP, "root"), ("the share page", "/share/?v=1", SHARE, "share")]
sentences = {}
for label, path, whole, kind in DOCS:
    if not whole:
        chk("%s: the file is there" % label, False, "no file"); continue
    print("-- %s (%d bytes) --" % (label, len(whole)))
    seen_at = {}
    for lim in LIMITS:
        got = fetch_prefix(path, lim)
        assert got == whole[:lim], "the truncating reader returned something else"
        p = scrape(got, lim)
        have = [k for k in NEEDED_TEXT if p.f.get(k)]
        seen_at[lim] = (have, p)
        print("   first %7d bytes: %d of %d tags found%s" % (lim, len(have), len(NEEDED_TEXT), "" if len(have) == len(NEEDED_TEXT) else "  (missing: %s)" % ", ".join(k for k in NEEDED_TEXT if k not in have)))
    # the bar: the whole set is found inside the first 2KB, which every limit above that also satisfies
    have2, p2 = seen_at[2048]
    chk("%s: title, og:title, og:description, description, og:image and all four twitter tags are found in the first 2KB" % label,
        len(have2) == len(NEEDED_TEXT), [k for k in NEEDED_TEXT if k not in have2])
    chk("%s: ...and at every larger read too (%s)" % (label, ", ".join("%dK" % (l // 1024) for l in LIMITS[2:])),
        all(len(seen_at[l][0]) == len(NEEDED_TEXT) for l in LIMITS[1:]))
    full = scrape(whole, len(whole)); sentences[kind] = full.f.get("og:description") or ""
    # the words are the intended sentence: one text, the same in all four places, plain ASCII, a sentence and not a blob
    texts = [full.f.get(k) for k in ("og:description", "description", "twitter:description")]
    chk("%s: og:description, description and twitter:description are one text (%r)" % (label, (texts[0] or "")[:50]),
        texts[0] and len(set(texts)) == 1, texts)
    d = texts[0] or ""
    chk("%s: the description is a plain-ASCII sentence: %d chars, words with spaces, capital first, full stop last, no token over 24 chars, no base64 run" % (label, len(d)),
        20 <= len(d) <= 300 and d.isascii() and d[:1].isupper() and d.endswith(".") and " " in d and max(map(len, d.split())) <= 24
        and not re.search(r"[A-Za-z0-9+/=]{40,}", d) and not re.search(r"&[#a-z0-9]+;", d), d)
    t = full.f.get("title") or ""
    chk("%s: title and og:title are the app's name, short (%r, %r)" % (label, t, full.f.get("og:title")),
        t == full.f.get("og:title") == full.f.get("twitter:title") and 0 < len(t) <= 30 and t.isascii())
    # a scraper's fall-back, when it finds no description: the text it can read. Shown, not asserted (what each messenger really does is
    # unknowable from here); on the old app it is stylesheet and script text, and a read that ends inside the manifest ends in base64.
    for lim in (2048, 65536):
        raw = whole[:lim].decode("utf-8", "replace")
        naive = re.sub(r"\s+", " ", re.sub(r"<[^>]*>?", " ", re.sub(r"<!--.*?-->", " ", raw, flags=re.S))).strip()
        print("   naive fall-back text (tags stripped, nothing else understood), first 90 chars of a %dK read: %r" % (lim // 1024, naive[:90]))
        print("   ...and a read cut at %dK ends with: %r" % (lim // 1024, raw[-40:].replace("\n", " ")))
    chk("%s: the image is the real card file and carries the same ?v= as the Share address" % label,
        bool(re.search(r'og:image" content="https://[^"]+/share/og-card\.png\?v=(\d+)"', whole.decode("utf-8", "replace")))
        and os.path.exists(os.path.join(ROOT, "share", "og-card.png")))
    if kind == "share":
        print("   (a crawler that honours the <noscript> meta refresh: %r - it lands on the app's address, scraped above)" % scrape(whole, 4096).refresh)

# --- the app's address and the share page say the same thing, and the address the Share button sends is the share page ---
chk("the app's description and the share page's are the same sentence", sentences.get("root") and sentences.get("root") == sentences.get("share"), sentences)
m = re.search(r'const SHARE_URL = "([^"]+)";', SRC)
v_app = re.search(r'og:image" content="[^"]*og-card\.png\?v=(\d+)"', SRC)
chk("the Share button sends the share page, versioned with the card (%s)" % (m and m.group(1)),
    bool(m) and v_app and m.group(1).split("?")[0].endswith("/share/") and m.group(1).endswith("?v=" + v_app.group(1)))
# what the Share sheet adds beside the link: plain, no address in it, no odd characters
sd = re.search(r"const shareData = \{ title: \"([^\"]*)\", text: \"([^\"]*)\", url: SHARE_URL \}", SRC)
chk("Settings > Share passes a plain title and text beside the link (no address, ASCII)", bool(sd) and sd.group(2).isascii() and "http" not in sd.group(2)
    and sd.group(1).isascii() and sd.group(2).endswith("."), sd and sd.groups())

# --- the head's start: nothing that paints or blocks was pushed back, and nothing heavy sits ahead of the block ---
head = APP[:APP.find(b"</head>")]
pre_style = head[:head.find(b"<style")]
cs = head.find(b'name="color-scheme"')
chk("the colour-scheme meta is still inside the first ~300 bytes (at %d)" % cs, 0 < cs < 300)
chk("before the first <style>, only charset, colour-scheme, comments, title and the share block's meta/link tags (no script, no data: URI, no base64)",
    not re.search(rb"<script|data:|[A-Za-z0-9+/]{80,}", pre_style) and len(pre_style) < 2200, (len(pre_style), pre_style[:60]))
chk("the first <style> still carries the html background rule (the launch's first frame)", b"html{background:var(--splash-bg)" in head[len(pre_style):len(pre_style) + 200])
chk("exactly one <title> in the document's head, and it is not behind the manifest", head.count(b"<title") == 1 and head.find(b"<title") < 2048, (head.count(b"<title"), head.find(b"<title")))
# two places declare theme-color and must agree (CLAUDE.md)
mt = re.search(r'<meta name="theme-color" id="themecolor" content="(#[0-9A-Fa-f]{6})"', SRC)
mm = re.search(r'<link rel="manifest" href="data:application/manifest\+json;base64,([A-Za-z0-9+/=]+)"', SRC)
mc = json.loads(base64.b64decode(mm.group(1))).get("theme_color") if mm else None
chk("theme-color in the meta tag and in the manifest still agree (%s, %s)" % (mt and mt.group(1), mc), bool(mt) and bool(mc) and mt.group(1).lower() == mc.lower())

# --- in a real browser: the page still loads, one title, the head's description is the scraped one ---
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br = pw.chromium.launch(); pg = br.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:120]))
        pg.route("**/*", lambda r: r.abort() if "gstatic.com" in r.request.url else r.continue_())
        pg.goto("http://127.0.0.1:%d/" % port, wait_until="domcontentloaded"); pg.wait_for_timeout(800)
        r = pg.evaluate("""()=>({ titles: document.querySelectorAll('title').length, title: document.title,
            og: (document.querySelector('meta[property="og:description"]')||{}).content, first: [...document.head.children].slice(0,3).map(e=>e.tagName+(e.name?':'+e.name:'')) })""")
        chk("in Chromium: one <title>, document.title is the name, og:description is the scraped sentence, and the head still opens with meta, comment-less children (%s)" % r["first"],
            r["titles"] == 1 and r["title"] == "Nova" and r["og"] == sentences.get("root") and r["first"][0] == "META", r)
        chk("in Chromium: no uncaught page errors on load (%s)" % errs[:1], not errs, errs)
        br.close()
except Exception as e:
    chk("in Chromium: the page loads", False, repr(e))

print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
