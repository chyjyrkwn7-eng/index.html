#!/usr/bin/env python3
"""The Virtual Room chat: colours, the unread count, and the announcement.

Every check here is written against the build that did not have them, and
--against <dir> runs it there: it has to FAIL on that build or it is
measuring nothing.

The room document is driven directly rather than through Firestore - the
SDK is blocked in the sandbox - so what is exercised is the app's own
snapshot handler, the same path a real message arrives on.
"""
import argparse, functools, http.server, io, json, os, re, socket, sys, threading
from playwright.sync_api import sync_playwright

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def serve(path):
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=path))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{port}/index.html"

ROOM = """
window.__room = {
  participants: { me:{name:'Madison'}, ann:{name:'Ann'}, bo:{name:'Bo'}, cy:{name:'Cy'} },
  chatMessages: []
};
/* EVERY listener, not the last one. The lobby, the race and the chat all
   subscribe to the same room document, so a stub that kept one callback
   was driving whichever happened to subscribe last - which is how the
   first run of this check reported the chat rendering nothing at all. */
window.__snaps = [];
window.firebase = { apps: [], initializeApp(){ window.firebase.apps.push({}); return {}; },
  firestore(){ return { collection(){ return { doc(){ return {
    get(){ return Promise.resolve({exists:true, data:()=>window.__room, metadata:{fromCache:false}}); },
    set(){ return Promise.resolve(); }, update(){ return Promise.resolve(); },
    delete(){ return Promise.resolve(); },
    onSnapshot(cb){ window.__snaps.push(cb);
      cb({exists:true, data:()=>window.__room, metadata:{fromCache:false}});
      return function(){}; }
  };}, where(){return this;}, orderBy(){return this;}, limit(){return this;},
     get(){return Promise.resolve({docs:[],forEach(){}});}, onSnapshot(){return function(){};} };}};}
};
window.firebase.firestore.FieldValue = { serverTimestamp(){return Date.now();}, delete(){return null;},
  arrayUnion(v){ return v; } };
window.__push = function(key, name, text){
  window.__room.chatMessages = window.__room.chatMessages.concat([
    {id:key+'-'+Date.now()+'-'+Math.random(), key:key, name:name, text:text, ts:Date.now()}]);
  window.__snaps.forEach(function(cb){
    try{ cb({exists:true, data:()=>window.__room, metadata:{fromCache:false}}); }catch(e){}
  });
};
"""

def run(src_dir, label):
    srv, url = serve(src_dir); fails = []
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
            ctx = br.new_context(viewport={"width": 440, "height": 956}, is_mobile=True, has_touch=True)
            ctx.add_init_script(ROOM)
            pg = ctx.new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
            pg.goto(url); pg.wait_for_timeout(2400)
            pg.evaluate("document.getElementById('splashscreen')?.remove()")
            # a lobby, with this device as 'me'
            ok = pg.evaluate("""()=>{
              if(typeof showVirtualRoomLobby !== 'function') return false;
              vroomCode = 'TESTROOM'; vroomMyKey = 'me'; vroomIsHost = true;
              showVirtualRoomLobby(); return true; }""")
            if not ok:
                fails.append("showVirtualRoomLobby is not available")
                return fails
            pg.wait_for_timeout(700)
            # three people speak while the sheet is closed
            for k, n, t in [("ann","Ann","are we starting"),("bo","Bo","one sec"),("cy","Cy","ready")]:
                pg.evaluate("([k,n,t])=>window.__push(k,n,t)", [k,n,t]); pg.wait_for_timeout(260)
            out = pg.evaluate("""()=>{
              const dot=document.querySelector('.vroom-chat-dot');
              const alert=document.querySelector('.vroom-chat-alert');
              const names=[...document.querySelectorAll('.vroom-chat-msg-name')]
                .map(n=>({t:n.textContent.trim(), c:getComputedStyle(n).color,
                          me:n.classList.contains('is-me')}));
              return {dotHidden:dot?dot.hidden:null, dotText:dot?dot.textContent:null,
                      alert: alert?alert.textContent:null,
                      alertShown: alert?alert.classList.contains('show'):false,
                      names};}""")
            print(f"  [{label}] {json.dumps(out)[:300]}")
            if out["dotHidden"] is not False: fails.append("the unread badge is not showing")
            if out["dotText"] != "3": fails.append(f"the unread badge reads {out['dotText']!r}, not a count of 3")
            if not out["alert"]: fails.append("nothing announced who sent the message")
            elif "sent a message" not in out["alert"]: fails.append(f"the announcement reads {out['alert']!r}")
            if not out["alertShown"]: fails.append("the announcement never animated in")
            others = [n for n in out["names"] if not n["me"]]
            cols = set(n["c"] for n in others)
            if len(others) < 3: fails.append(f"only {len(others)} messages rendered from other people")
            elif len(cols) != len(others):
                fails.append(f"names are not each their own colour: {sorted(cols)}")
            real = [e for e in errs if not any(k in e.lower() for k in
                    ("firebase","firestore","gstatic","failed to fetch","net::"))]
            if real: fails.append(f"JS error {real[0]}")
            br.close()
    finally:
        srv.shutdown()
    return fails

ap = argparse.ArgumentParser(); ap.add_argument("--against")
a = ap.parse_args()
where = a.against or ROOT
label = os.path.basename(where.rstrip("/")) if a.against else "current"
fails = run(where, label)
if fails:
    print(f"\n{len(fails)} FAILURE(S) [{label}]")
    for f in fails: print("  *", f)
    sys.exit(1)
print(f"\nALL PASS [{label}] - names are coloured, unread is counted, the sender is announced")
