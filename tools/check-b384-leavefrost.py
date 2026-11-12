#!/usr/bin/env python3
"""Build 384.52: the leave-chat sheet is frosted glass (it sat inside a backdrop root), and nothing else is hiding in one.

Madison, the chat's "Leave this group chat?" action sheet on his iPhone 17 Pro Max: "Ensure this is updated to the frost look?"
It read as a flat dark slab. The shared glass rule already styled it, but confirmLeaveChat() mounted it INSIDE #chatdock-panel and the panel
carries will-change:backdrop-filter, which makes it a BACKDROP ROOT: a backdrop-filter inside it can only blur what the panel itself
contains, never the page behind. tools/check-b384-popglass.py reads computed styles and cannot see that (and exempted this sheet); this reads
PIXELS.

THE PIXEL TEST (Chromium renders backdrop-filter, so this is measured, not reasoned). For every pop-up in b384_pop_lib.INVENTORY, opened by
the app's own function over its background screen: a bright black/white stripe pattern (6px period) is put on <body> just BELOW the pop-up's
outermost layer, and the backgrounds of the sheet's ancestors are made clear (so what is measured is whether the sheet's blur CAN reach the
page, not how opaque an ancestor happens to be). A text-free strip inside the sheet is then screenshotted twice: as it is, and with the sheet's
own backdrop-filter forced off. ratio = luminance spread with the blur / spread without it. A sheet that really blurs what is behind it
smears the stripes (ratio near 0); one whose backdrop root cuts it off from the page keeps them (ratio near the tint's 0.6-0.7).
  (1) every pop-up: the blur reaches what is behind it (ratio < .35, and the un-blurred strip must have real contrast, so a test that sees
      nothing cannot pass);
  (2) the chat's leave sheet, phone and iPad: it is a child of <body> (not of the chat panel), exactly the panel's rectangle and corner radius,
      above the panel, with the shared dim (--pop-scrim as its ::before, the overlay itself clear) and no flat rgba of its own;
  (3) it clears itself: gone when the dock closes, when the chat is closed or left, on Escape, on a tap of the dim, on Cancel; it follows the
      panel when the window is resized (a rotation); a screen change under it leaves it glued to the panel; two opens never stack;
  (4) the sheet keeps its shape: a group (title, body, red Leave) and a separate Cancel, both at least 44px tall, labels centred, the slide-up
      animation on, and none of it under [data-reduce-motion];
  (5) no page errors.
  python3 tools/check-b384-leavefrost.py [--against OLD/index.html]   (must FAIL on the build before)
  python3 tools/check-b384-leavefrost.py --shots DIR                  (before/after frames: DIR/<key>-<size>.png)"""
import io, os, statistics, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import b384_pop_lib as L
from playwright.sync_api import sync_playwright
from PIL import Image

against = sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else None
shots = sys.argv[sys.argv.index("--shots") + 1] if "--shots" in sys.argv else None
only = set(os.environ.get("ONLY", "").split(",")) - {""}
cb = L.load_cb(against)
if shots: os.makedirs(shots, exist_ok=True)
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:500], flush=True)

STRIPES = "repeating-linear-gradient(90deg,#fff 0 6px,#000 6px 12px)"
CLEAR = """()=>{ document.querySelectorAll('.savecode-card,.chatdock-confirm,.resume-offer,.friend-moment,.invite-overlay,.intro-pop,.installguide-overlay,.unitver,.__stripes').forEach(n=>n.remove());
  try{ closeLeaveChatConfirm(); }catch(e){} }"""

# the sheet to sample for each inventory key (the same selectors as check-b384-popglass)
def spread(png, box):
    im = Image.open(io.BytesIO(png)).convert("L")
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    return statistics.pstdev(list(im.crop((x0, y0, x1, y1)).getdata()))

SETUP = """(arg)=>{ const [sel, under] = arg; const sh = document.querySelector(sel); if(!sh) return null;
  let top = sh; const chain = []; while(top.parentElement && top.parentElement !== document.body){ top = top.parentElement; chain.push(top); }
  // `under`: a layer the stripes go beneath instead (the chat's whole dock, so the stripes are on the PAGE behind the panel, and the panel's own
  // fill is cleared too: what is asked is whether the sheet's blur CAN reach the page through the chat, not how opaque the panel happens to be)
  if(under){ const u = document.querySelector(under); if(u){ top = u; const p = document.getElementById('chatdock-panel'); if(p) p.style.setProperty('background', 'transparent', 'important'); } }
  chain.forEach(a => a.style.setProperty('background', 'transparent', 'important'));
  const z = parseInt(getComputedStyle(top).zIndex, 10);
  const d = document.createElement('div'); d.className = '__stripes';
  d.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:' + (isNaN(z) ? 0 : z - 1) + ';background:' + arguments[0];
  top.parentElement.insertBefore(d, top);
  const r = sh.getBoundingClientRect();
  return { z: isNaN(z) ? 'auto' : z, top: top.className || top.tagName, inBody: top.parentElement === document.body, r: [r.left, r.top, r.width, r.height], depth: chain.length }; }"""

def pixel_ratio(pg, sel, under=None):
    """The stripe test for the sheet `sel`. Returns (ratio, spread_with_blur, spread_without, info) or None."""
    # the stripes' pattern is passed in by string replace (evaluate takes one arg)
    info = pg.evaluate(SETUP.replace("arguments[0]", repr(STRIPES)), [sel, under])
    if not info: return None
    pg.wait_for_timeout(250)
    r = info["r"]; vw, vh = pg.evaluate("()=>[innerWidth, innerHeight]")
    # a text-free strip down the sheet's left edge, inside its border and clear of the corners, clamped to the screen
    x0 = max(r[0], 0) + 5; x1 = x0 + 12
    y0 = max(r[1], 0) + min(r[3], vh - r[1]) * .30; y1 = max(r[1], 0) + min(r[3], vh - r[1]) * .70
    on = spread(pg.screenshot(), (x0, y0, x1, y1))
    pg.evaluate("(s)=>{ const e=document.querySelector(s); e.style.setProperty('backdrop-filter','none','important'); e.style.setProperty('-webkit-backdrop-filter','none','important'); }", sel)
    pg.wait_for_timeout(200)
    off = spread(pg.screenshot(), (x0, y0, x1, y1))
    pg.evaluate("(s)=>{ const e=document.querySelector(s); e.style.removeProperty('backdrop-filter'); e.style.removeProperty('-webkit-backdrop-filter'); }", sel)
    return on / max(off, .01), on, off, info

SEL = {k: s for k, _j, s, _kd, _b in L.INVENTORY}
SEL["chat-leave"] = ".chat-leavesheet-group"
SEL["vroom-leave"] = ".chatdock-confirm-card"

def open_chat_leave(pg):
    pg.evaluate("()=>{ openChatDock(); }"); pg.wait_for_timeout(1000)
    pg.evaluate("()=>{ confirmLeaveChat('TESTROOM', ()=>{}); }"); pg.wait_for_timeout(900)

def run(br, w, h, tag):
    box = {}
    errs = []
    def fresh():
        # headless Chromium sometimes loses its renderer under many full-size backdrop blurs (TargetClosedError / "Unable to capture
        # screenshot"): a fresh context per retry, never a skipped check
        try: box["ctx"].close()
        except Exception: pass
        box["ctx"], box["pg"] = L.boot(br, cb, w, h, "academy", dpr=1)
        box["pg"].on("pageerror", lambda e: errs.append(str(e)[:160]))
    fresh()
    print("\n== %s ==" % tag)
    # ---- (1) every pop-up: can its blur reach what is behind it? ----
    def one(key, js, sel, bg):
        pg = box["pg"]
        pg.evaluate(CLEAR); pg.evaluate("()=>{ closeChatDock(); }"); pg.evaluate("()=>{ " + L.BGS[bg] + "; }"); pg.wait_for_timeout(500)
        if key == "chat-leave": open_chat_leave(pg)
        else:
            pg.evaluate("()=>{ " + js + "; }"); pg.wait_for_timeout(1100)
        try: pg.wait_for_function("(s)=>{ const e=document.querySelector(s); return !!e && parseFloat(getComputedStyle(e).opacity) >= 1; }", arg=sel, timeout=6000)
        except Exception as e:
            if "closed" in str(e).lower(): raise
        if shots and key == "chat-leave":
            pg.screenshot(path=os.path.join(shots, "%s-%s.png" % (key, "tablet" if w > 600 else "phone")))
        # the chat's leave sheet: stripes on the PAGE, under the whole dock (panel fill cleared), so a sheet stuck in the panel's backdrop root fails
        return pixel_ratio(pg, sel, "#chatdock" if key == "chat-leave" else None)
    for key, js, sel, kind, bg in L.INVENTORY:
        if only and key not in only: continue
        res = None
        for attempt in range(3):
            try: res = one(key, js, sel, bg); break
            except Exception as e:
                print("     (retry %s: %s)" % (key, str(e).splitlines()[0][:80]), flush=True); fresh()
        if not res: chk("%s %-18s the sheet is on screen and measurable (%s)" % (tag, key, sel), False); continue
        ratio, on, off, info = res
        chk("%-13s %-18s (1) its blur reaches what is behind it: stripes %.1f -> %.1f, ratio %.2f < .35 (stripes under %s, z %s)" % (tag, key, off, on, ratio, info["top"], info["z"]),
            off >= 20 and ratio < .35, {"off": off, "on": on, "ratio": ratio, "info": info})
    fresh(); pg = box["pg"]
    pg.evaluate(CLEAR); pg.evaluate("()=>{ closeChatDock(); }")

    # ---- (2)-(4) the chat's leave sheet ----
    pg.evaluate("()=>{ " + L.BGS["leaderboard"] + "; }"); pg.wait_for_timeout(500)
    open_chat_leave(pg)
    G = pg.evaluate("""()=>{ const s=document.querySelector('.chat-leavesheet'), p=document.getElementById('chatdock-panel'); if(!s||!p) return null;
      const a=s.getBoundingClientRect(), b=p.getBoundingClientRect(), cs=getComputedStyle(s), pcs=getComputedStyle(p), b4=getComputedStyle(s,'::before');
      const A=c=>{const m=(c||'').match(/rgba?\\(([^)]+)\\)/); if(!m) return 0; const q=m[1].split(',').map(parseFloat); return q.length>3?q[3]:1;};
      const g=document.querySelector('.chat-leavesheet-group'), c=document.querySelector('.chat-leavesheet-cancel'), l=document.querySelector('.chat-leavesheet-leave');
      const R=e=>{const r=e.getBoundingClientRect(); return {l:r.left,t:r.top,w:r.width,h:r.height};};
      const inner=document.querySelector('.chat-leavesheet-inner');
      return { onBody: s.parentElement===document.body, inPanel: p.contains(s), rect:[a.left,a.top,a.width,a.height].map(Math.round), prect:[b.left,b.top,b.width,b.height].map(Math.round),
        radius: cs.borderTopLeftRadius, pradius: pcs.borderTopLeftRadius, z: cs.zIndex, pz: pcs.zIndex, dockz: getComputedStyle(document.getElementById('chatdock')).zIndex,
        own: A(cs.backgroundColor), scrim: b4.content!=='none' && b4.content!=='normal' ? A(b4.backgroundColor) : 0, bf: cs.backdropFilter,
        group: R(g), cancel: R(c), leave: R(l), leaveColor: getComputedStyle(l).color, anim: getComputedStyle(inner).animationName,
        title: !!g.querySelector('.chat-leavesheet-title'), body: !!g.querySelector('.chat-leavesheet-body'), cancelInGroup: g.contains(c), safe: cs.paddingBottom }; }""")
    if not G: chk("%s the leave sheet opens over the open chat" % tag, False); return
    chk("%s (2) the sheet is a child of <body>, not of the chat panel" % tag, G["onBody"] and not G["inPanel"], G)
    chk("%s (2) it is exactly the panel's rectangle %s and corner radius %s" % (tag, G["prect"], G["pradius"]),
        all(abs(a - b) <= 1 for a, b in zip(G["rect"], G["prect"])) and G["radius"] == G["pradius"], G)
    chk("%s (2) it sits above the chat (z %s over the dock's %s)" % (tag, G["z"], G["dockz"]), int(G["z"]) > int(G["dockz"]), G)
    chk("%s (2) the dim is the shared scrim layer (%.2f) and the overlay itself is clear (%.2f)" % (tag, G["scrim"], G["own"]), 0 < G["scrim"] <= .5 and G["own"] == 0 and (G["bf"] in ("none", "")), G)
    # (4) shape
    gr, cr, lr = G["group"], G["cancel"], G["leave"]
    chk("%s (4) a group with title, body and Leave, and a separate Cancel (not in the group), both rows >= 44px (%d, %d)" % (tag, lr["h"], cr["h"]),
        G["title"] and G["body"] and not G["cancelInGroup"] and lr["h"] >= 44 and cr["h"] >= 44 and cr["t"] > gr["t"] + gr["h"], G)
    chk("%s (4) Leave is red and the slide-up is on (%s)" % (tag, G["anim"]), G["leaveColor"].replace(" ", "") in ("rgb(255,90,82)",) and "leavesheet" in G["anim"], G)
    # labels centred on their rows
    cen = pg.evaluate("""()=>{ const o={}; for(const k of ['leave','cancel']){ const b=document.querySelector('.chat-leavesheet-'+k); const rg=document.createRange(); rg.selectNodeContents(b);
      const t=rg.getBoundingClientRect(), r=b.getBoundingClientRect(); o[k]=[Math.abs((t.left+t.right)/2-(r.left+r.right)/2), Math.abs((t.top+t.bottom)/2-(r.top+r.bottom)/2)]; } return o; }""")
    chk("%s (4) the labels are centred in their rows (dx, dy %s)" % (tag, cen), all(v[0] <= 1 and v[1] <= 2 for v in cen.values()), cen)
    pad = pg.evaluate("()=>parseFloat(getComputedStyle(document.querySelector('.chat-leavesheet')).paddingBottom)")
    chk("%s (4) it keeps the .75rem + safe-area bottom padding (%spx)" % (tag, pad), pad >= 12 - .5, pad)
    # reduced motion
    pg.evaluate("()=>document.documentElement.setAttribute('data-reduce-motion','true')"); pg.wait_for_timeout(100)
    an = pg.evaluate("()=>getComputedStyle(document.querySelector('.chat-leavesheet-inner')).animationName")
    pg.evaluate("()=>document.documentElement.removeAttribute('data-reduce-motion')")
    chk("%s (4) under reduce-motion there is no slide (%s)" % (tag, an), an == "none", an)

    # (3) lifecycle
    cnt = lambda: pg.evaluate("()=>document.querySelectorAll('.chatdock-confirm').length")
    pg.evaluate("()=>{ confirmLeaveChat('TESTROOM', ()=>{}); confirmLeaveChat('TESTROOM', ()=>{}); }"); pg.wait_for_timeout(300)
    chk("%s (3) two opens never stack (%d)" % (tag, cnt()), cnt() == 1)
    # a screen change under it: it stays glued to the panel
    pg.evaluate("()=>{ showProfile('profile'); }"); pg.wait_for_timeout(700)
    glued = pg.evaluate("""()=>{ const s=document.querySelector('.chat-leavesheet'), p=document.getElementById('chatdock-panel'); if(!s) return 'gone'; const a=s.getBoundingClientRect(), b=p.getBoundingClientRect(); return [a.left-b.left,a.top-b.top,a.width-b.width,a.height-b.height].map(Math.round); }""")
    chk("%s (3) a screen change under it leaves it glued to the panel (%s)" % (tag, glued), glued == [0, 0, 0, 0], glued)
    # a resize (rotation): it follows the panel
    pg.set_viewport_size({"width": h, "height": w}); pg.wait_for_timeout(700)
    rot = pg.evaluate("""()=>{ const s=document.querySelector('.chat-leavesheet'), p=document.getElementById('chatdock-panel'); if(!s) return 'gone'; const a=s.getBoundingClientRect(), b=p.getBoundingClientRect(); return {d:[a.left-b.left,a.top-b.top,a.width-b.width,a.height-b.height].map(Math.round), panel:[b.left,b.top,b.width,b.height].map(Math.round)}; }""")
    chk("%s (3) rotated, it follows the panel (%s)" % (tag, rot), isinstance(rot, dict) and rot["d"] == [0, 0, 0, 0], rot)
    pg.set_viewport_size({"width": w, "height": h}); pg.wait_for_timeout(600)
    for how, js in [("the dock is closed", "()=>{ closeChatDock(); }"),
                    ("the chat is closed", "()=>{ chatRoomCode='TESTROOM'; closeChatRoom(); }"),
                    ("Escape", "()=>{ document.querySelector('.chatdock-confirm').dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true})); }"),
                    ("the dim is tapped", "()=>{ const s=document.querySelector('.chatdock-confirm'); s.dispatchEvent(new MouseEvent('click',{bubbles:true})); }"),
                    ("Cancel is tapped", "()=>{ document.querySelector('.chat-leavesheet-cancel').click(); }"),
                    ("Leave is tapped (and the leave runs)", "()=>{ window.__left = 0; document.querySelector('.chat-leavesheet-leave').click(); }")]:
        pg.evaluate("()=>{ openChatDock(); }"); pg.wait_for_timeout(700)
        pg.evaluate("()=>{ confirmLeaveChat('TESTROOM', ()=>{ window.__left = (window.__left||0) + 1; }); }"); pg.wait_for_timeout(500)
        pg.evaluate(js); pg.wait_for_timeout(450)
        left = pg.evaluate("()=>window.__left || 0")
        chk("%s (3) gone when %s (%d left)%s" % (tag, how, cnt(), ", onLeave ran %d" % left if "Leave is" in how else ""), cnt() == 0 and (left == 1 if "Leave is" in how else left == 0), cnt())
    # the dock itself still works after all that, and a second leave sheet opens once more
    pg.evaluate("()=>{ openChatDock(); }"); pg.wait_for_timeout(700)
    pg.evaluate("()=>{ confirmLeaveChat('TESTROOM', ()=>{}); }"); pg.wait_for_timeout(400)
    chk("%s (3) it opens again after all of that (%d)" % (tag, cnt()), cnt() == 1)
    pg.evaluate("()=>{ closeChatDock(); }")
    chk("%s (5) no page errors (%s)" % (tag, errs[:2]), not errs)
    box["ctx"].close()

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    run(br, 440, 956, "phone")
    run(br, 834, 1194, "tablet")
    br.close()
cb.SERVER.shutdown()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
