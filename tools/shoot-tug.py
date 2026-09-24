#!/usr/bin/env python3
"""Screenshots of a Tug of War match, taken by PLAYING one.

The same rule as tools/shoot-flow.py, for the same reason: a screen
that is mounted by name is not the screen somebody reaches, and the
difference has put a tab bar into screenshots twice. So this borrows
check-vroom's fake Firestore, opens two tabs, creates a tug lobby,
readies both up, and answers questions on one of them until the rope
has moved - then photographs it.

  python3 tools/shoot-tug.py [outdir]

Writes tug-<device>-match.png, -wait.png and -result.png per reference
device. Two devices by default, the same two shoot-flow.py sends.
"""
import importlib.util
import io
import functools
import http.server
import json
import os
import re
import socket
import sys
import threading

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

# One source of truth for the fake Firestore and the seed: a second copy
# here would drift from the gate's, and then the pictures would be of a
# different app from the one the gate passed.
_spec = importlib.util.spec_from_file_location(
    "check_vroom", os.path.join(ROOT, "tools", "check-vroom.py"))
_cv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cv)

DEVICES = [("iphone-17-pro-max", 440, 956), ("ipad-pro-11", 834, 1194)]


def shoot(outdir, name, w, h):
    body = _cv.INSET_RE.sub(lambda m: "0px",
                            io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read())
    m = re.search(r'APP_BUILD\s*=\s*"([^"]+)"', body)
    vj = json.dumps({"build": m.group(1) if m else "", "note": "",
                     "frameId": "", "frameNote": "", "force": False})

    sock = socket.socket(); sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]; sock.close()

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    srv = http.server.ThreadingHTTPServer(
        ("127.0.0.1", port), functools.partial(Quiet, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = "http://127.0.0.1:%d/index.html" % port

    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME)
        ctx = br.new_context(viewport={"width": w, "height": h},
                             device_scale_factor=2)
        ctx.add_init_script("window.__fakeLatency = 60;")
        ctx.add_init_script(_cv.FAKE_FIRESTORE)
        ctx.add_init_script(
            "try{localStorage.setItem('class26e.freshstart','1');"
            "localStorage.setItem('class26e.frame.ok','go-live-1');"
            "localStorage.setItem('class26e.drill.v1', '%s');}catch(e){}" % _cv.SEED)

        def tab(who, avatar, code):
            pg = ctx.new_page()
            pg.route("**/index.html", lambda r: r.fulfill(
                status=200, headers={"content-type": "text/html; charset=utf-8"},
                body=body))
            pg.route("**/version.json", lambda r: r.fulfill(
                status=200, headers={"content-type": "application/json"}, body=vj))
            pg.goto(url)
            pg.wait_for_timeout(2600)
            pg.evaluate("""(a)=>{
              document.getElementById('splashscreen')?.remove();
              __useFake();
              store.firstName = a.who; store.avatarChar = a.avatar;
              store.lifetime.points = 4200; syncCode = a.code;
            }""", {"who": who, "avatar": avatar, "code": code})
            ctx.new_cdp_session(pg).send("Page.setWebLifecycleState", {"state": "active"})
            return pg

        a = tab("Madison", "cadet", "AAAA-1111")
        b = tab("Devonte", "ghost", "BBBB-2222")

        a.evaluate("""()=>{ createVirtualRoomLobby(topicsIn(QUESTIONS).slice(0,1), null, "tug"); }""")
        a.wait_for_function("() => typeof vroomCode === 'string' && vroomCode", timeout=20000)
        code = a.evaluate("()=>vroomCode")
        b.evaluate("(c)=>joinVirtualRoomLobby(c)", code)
        for pg in (a, b):
            pg.wait_for_selector(".vroom-readyup-btn", state="visible", timeout=20000)
        b.click(".vroom-readyup-btn"); b.wait_for_timeout(400)
        a.click(".vroom-readyup-btn")
        for pg in (a, b):
            pg.wait_for_selector(".screen-tug", timeout=25000)

        def answer(pg, right=True):
            """Returns False once there is nothing left to answer. The
            match can end UNDER you - the host writes `over` the moment
            one side is clear - so every tap has to check the screen is
            still there rather than assume the bank runs out first."""
            if not pg.query_selector(".screen-tug .choices .choice"):
                return False
            i = pg.evaluate("""(w)=>{
              const q = QUESTIONS[tugPool[tugMyPos % tugPool.length]];
              return w ? q.answer : (q.answer + 1) % q.choices.length; }""", right)
            try:
                pg.click(".screen-tug .choices .choice:nth-child(%d)" % (i + 1), timeout=5000)
            except Exception:
                return False
            pg.wait_for_timeout(1350)
            return True

        # A rope at dead centre is a rope with nothing to say, so the
        # picture is taken with the match under way - but STAYING UNDER
        # THE WIN GAP, or the match is over before the shutter. Seven
        # against one is six clear, which is the whole match for a
        # 29-question bank; three against one is a lead you can see and
        # a match still running.
        gap = a.evaluate("()=>tugWinGap(tugCount)")
        for _ in range(3):
            answer(a, True)
        answer(b, True)
        a.wait_for_timeout(700)
        assert a.query_selector(".screen-tug"), "the match ended before the picture (gap %s)" % gap
        a.screenshot(path=os.path.join(outdir, "tug-%s-match.png" % name))

        # The waiting screen: run one side out of questions. It may not
        # be reachable at all - the rope can be pulled clear first, which
        # is the match working as designed - so this stops when the
        # questions stop rather than insisting on a picture.
        n = a.evaluate("()=>tugCount")
        for _ in range(n + 2):
            if a.evaluate("()=>tugMyDone") or not answer(a, True):
                break
        a.wait_for_timeout(900)
        if a.query_selector(".screen-tug-wait"):
            a.screenshot(path=os.path.join(outdir, "tug-%s-wait.png" % name))
        got_wait = bool(a.query_selector(".screen-tug-wait"))
        a.wait_for_selector(".screen-tug-result", timeout=60000)
        a.wait_for_timeout(700)
        a.screenshot(path=os.path.join(outdir, "tug-%s-result.png" % name))
        # Say what was actually taken. The waiting screen is only
        # reachable when the bank runs out before anybody pulls clear,
        # which is not the usual way a match ends.
        print("  %s: match, result%s" % (name, ", wait" if got_wait else " (no wait screen - the rope was pulled clear first)"))
        ctx.close(); br.close()
    srv.shutdown()


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "shots-tug")
    os.makedirs(outdir, exist_ok=True)
    for name, w, h in DEVICES:
        shoot(outdir, name, w, h)
    print("-> %s" % outdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
