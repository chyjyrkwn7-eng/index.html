"""Build 381: the link that is shared is a small page an iPhone can read, and the icon is fetched fresh.
Madison: "Sharing the link doesn't give it the nova look and the description needs to be updated ...
Why isn't the picture there? Also when bookmarking the app the old icon is there".
Run:  python3 tools/check-b381-share.py   (--against: run it on a checkout of the old build)"""
import http.server, os, re, socketserver, sys, threading
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else info)
app = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
page_path = os.path.join(ROOT, "share", "index.html")
page = open(page_path, encoding="utf-8").read() if os.path.exists(page_path) else ""
m = re.search(r'const SHARE_URL = "([^"]+)"', app)
share_url = m.group(1) if m else ""
# (384) one link for everyone, carrying the build (?v=) so a cached copy of the share page is fetched again
chk("the Share button sends the share page (%s)" % share_url, share_url.split("?")[0].endswith("/share/"), share_url)
chk("the share page exists and is small (%d bytes)" % len(page.encode()), 0 < len(page.encode()) <= 8000)
og_img = re.search(r'property="og:image" content="([^"]+)"', page)
desc = re.search(r'name="description" content="([^"]+)"', app)
chk("the share page names the card picture and the app's own description (%s)" % (og_img and og_img.group(1)),
    bool(og_img) and os.path.exists(os.path.join(ROOT, "share", og_img.group(1).rsplit("/share/", 1)[-1].split("?")[0]))
    and bool(desc) and ('content="%s"' % desc.group(1)) in page)
icon_app = re.search(r'<link rel="apple-touch-icon"[^>]*href="([^"]+)"', app)
icon_page = re.search(r'<link rel="apple-touch-icon"[^>]*href="([^"]+)"', page)
chk("the app's and the share page's touch icon carry a version, so a cached old icon is fetched again (%s, %s)" % (icon_app and icon_app.group(1), icon_page and icon_page.group(1)),
    bool(icon_app) and "?v=" in icon_app.group(1) and bool(icon_page) and icon_page.group(1) == icon_app.group(1))
# the share page forwards into the app, keeping what follows the link
class H(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, p):
        p = p.split("?")[0].split("#")[0]
        if p.startswith("/index.html/"): p = p[len("/index.html"):]
        return os.path.join(ROOT, p.lstrip("/"))
    def log_message(self, *a): pass
srv = socketserver.TCPServer(("127.0.0.1", 0), H); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
landed = None
if page:
    with sync_playwright() as pw:
        br = pw.chromium.launch(); pg = br.new_page()
        pg.route(re.compile(r"firebase|gstatic|googleapis"), lambda r: r.abort())
        pg.goto("http://127.0.0.1:%d/index.html/share/?from=link#x" % port); pg.wait_for_timeout(3000)
        landed = [pg.url, pg.evaluate("()=>typeof APP_BUILD==='string' ? APP_BUILD : null")]
        br.close()
srv.shutdown()
chk("opening the shared link lands in the app with what followed it (%s)" % (landed,),
    bool(landed) and landed[0].endswith("/index.html/?from=link#x") and bool(landed[1]), landed)
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
