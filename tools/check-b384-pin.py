#!/usr/bin/env python3
"""384 pin: A BADGE PINNED TO YOUR PROFILE, AND SEEN BY THE CLASS.

Madison: "adding a badge to your profile to flex ... You can equip a badge on your profile, and people can see this badge, you are
flexing that you have the badge. That's any class ... It'd be like an emblem in Call of Duty."

Every device is a browser context on ONE in-memory Firestore (tools/b384_cloud_lib.py, every write logged with its device), the
account seeded in both classes, the board holding made-up classmates whose rows pin a real badge, a badge of the other class, junk,
a badge their own row does not hold, nothing, or carry no `pb` at all (a row from before this build). Read off the pages, by shape.

  (1) PIN AND UNPIN, both classes: a held badge's own page (the case's tap) has Pin to profile; a tap pins it (the store, the button
      says Unpin, Profile's medallion is that badge); a second tap unpins (Profile shows the spot, which opens the Badges screen); a
      badge not held has no Pin; one pin per class (pinning in one class leaves the other's).
  (2) PERSISTENCE: pinned, then the app is opened again - the pin is there, on Profile and in the cloud copy of the account.
  (3) TWO DEVICES OF ONE ACCOUNT, NEWEST WINS (each on the account's own cadence: a write waits out 60s since the last): A pins,
      B (already open) gets it; B pins another, A gets that; a copy whose pick is
      OLDER never undoes a newer one (mergeSameAccount, both ways round; mergeLeavingAccount).
  (4) NO EXTRA WRITE: the row's `pb` rides on writes that already happen. A pin and then a 20-question drill write no more documents
      than the build before (counted by the cloud), the board row is written as often as there, never per answer, and the row the
      drill's end writes carries the pin. A room's entry carries it in the join write and the presence beat - the beat writes as often
      as before.
  (5) OTHER PEOPLE'S PINS: the Leaderboard rows, the person card, a friend's profile and a Virtual Room's roster draw exactly the
      real ones (a badge of this class the row says they hold); the other class's badge, junk, a non-string, "" and an older row draw
      nothing; a tap on one opens that badge read-only, with its name and whose it is, and no Pin. A room of the other class draws
      none and is not written one.
  (6) A BADGE NO LONGER HELD NEVER SHOWS: pinned, then not held - nothing on Profile (the spot), nothing in the row this device
      would write, nothing in a room entry, nothing on your own Leaderboard row; and a pin of a badge not held is never stored.
  (7) LAYOUT, iPhone 17 Pro Max and iPad Pro 11", text size 85 / 100 / 135, both classes: the medallion sits on the plate's ring
      (45 degrees) inside the card, its target at least 44px; a row's badge is beside the name, the same size on every row, never
      squeezed, inside its row; the long name ellipsizes; rows with and without a pin are the same height; the art is rendered for
      the pixels it is shown at (crisp); no sideways scroll.
  (8) No page error on any load (the sandbox's blocked network aside).

  python3 tools/check-b384-pin.py [--against REV|FILE] [--baseline REV|FILE] [--only 1,2,...]
--against must FAIL (0b21215 has no pin); --baseline is the build the write cost is compared with (default 0b21215)."""
import json, os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import b384_pin_lib as P
from playwright.sync_api import sync_playwright

ARGS = sys.argv[1:]
def arg(n): return ARGS[ARGS.index(n) + 1] if n in ARGS else None
ONLY = set((arg("--only") or "").split(",")) - {""}
def wanted(n): return not ONLY or str(n) in ONLY
def src_of(x):
    if not x: return open(os.path.join(P.L.ROOT, "index.html"), encoding="utf-8").read()
    if os.path.isfile(x): return open(x, encoding="utf-8").read()
    return subprocess.check_output(["git", "-C", P.L.ROOT, "show", x + ":index.html"]).decode("utf-8")
TEXT = src_of(arg("--against"))
BASE = src_of(arg("--baseline") or "0b21215")

N = [0]; FAILS = []
def chk(name, cond, info=""):
    N[0] += 1
    if not cond: FAILS.append(name)
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  -> " + str(info)[:600]), flush=True)
class sect:
    def __init__(self, name): self.name = name
    def __enter__(self): return self
    def __exit__(self, t, e, tb):
        if t is not None: chk(self.name + " runs", False, repr(e)[:500]); return True

def until(pg, js, arg=None, tries=40, step=300):
    v = None
    for _ in range(tries):
        v = pg.evaluate(js, arg) if arg is not None else pg.evaluate(js)
        if v: return v
        pg.wait_for_timeout(step)
    return v

FRIEND = "%s%04d" % (P.MATE_PREFIX, 0)
UNITS = P.UNITS
# what each made-up classmate's row must draw (lib's mates(): index -> unit index, or None)
WANT_ROW = {0: 3, 1: 0, 2: 2, 3: 4, 4: None, 5: None, 6: None, 7: None, 8: None, 9: None}
WANT_VR = {0: 3, 1: 0, 2: 2, 3: 4, 4: None, 5: None}

ROWS_OF = "(window.NOVA_CLASS === 'ifc' ? (typeof classBoardRows !== 'undefined' ? classBoardRows : []) : leaderboardRows) || []"
PIN_STATE = """()=>{ const has = typeof setPinnedBadge === 'function';
  return { has, stored: has ? (store.pinnedBadge || null) : null, mine: has ? myPinnedBadge() : null }; }"""
PROFILE = """()=>{ const h = document.querySelector('#stage .screen-profile .pin-host');
  const m = h && h.querySelector(':scope > .pin-mark'), s = h && h.querySelector(':scope > .pin-spot');
  return { host: !!h, unit: m ? m.dataset.unit : null, spot: !!s, label: m ? m.getAttribute('aria-label') : s ? s.getAttribute('aria-label') : null }; }"""
OPEN_TILE = """async (n)=>{ const W = ms => new Promise(r => setTimeout(r, ms));
  showRanksScreen('badges'); await W(2500);
  const tiles = [...document.querySelectorAll('.badges-tab .ncase-cell')];
  const t = n >= 0 ? tiles.filter(x => x.classList.contains('is-earned'))[n] : tiles.find(x => x.classList.contains('is-locked'));
  if(!t) return { none: true };
  t.click(); await W(1800);
  const ov = document.querySelector('.binspect'); const b = ov && ov.querySelector('.binspect-pin');
  return { unit: t.dataset.unit, open: !!ov, pin: !!b, text: b ? b.textContent : null }; }"""
CLOSE = "()=>{ try{ badgeInspectNow && badgeInspectNow.teardown(); }catch(e){} document.querySelectorAll('.binspect, .invite-overlay').forEach(n => n.remove()); }"

DRILL = """async ()=>{ const wait = ms => new Promise(r => setTimeout(r, ms));
  setInterval(()=>[...document.body.children].forEach(n=>{ if(getComputedStyle(n).position==='fixed' && /challenge complete|character unlocked/i.test(n.textContent||'')) n.remove(); }), 40);
  document.querySelectorAll('#pushing-update,#intro-pop').forEach(n=>n.remove()); theme.reduceMotion = true; applyTheme();
  const U = topicsIn(QUESTIONS).find(t => QUESTIONS.filter(q => q.topic === t).length >= 20);
  cfg.mode='drill'; cfg.units=[U]; cfg.versions={}; cfg.source='all'; cfg.size=0; cfg.timer='off'; cfg.flashcards=false;
  const ix = QUESTIONS.map((q,i)=>i).filter(i=>QUESTIONS[i].topic===U).slice(0, 20);
  beginRun(freshOrder(ix), null);
  for(let i = 0; i < 80 && !document.querySelector('.qpanel .choice'); i++) await wait(150);
  const n0 = order.length, a0 = (store.lifetime||{}).answered || 0;
  for(let i = 0; i < 60; i++){
    if(document.querySelector('.rs-rewards')) break;
    const p = pos; const r = correctSlot(order[pos]);
    const b = document.querySelector('.qpanel .choice[data-index="' + r + '"]'); if(b) b.click();
    await wait(200);
    const n = document.getElementById('nextbtn'); if(n && !n.hidden) n.click();
    for(let k = 0; k < 40; k++){ await wait(60); if(pos !== p || document.querySelector('.rs-rewards')) break; }
  }
  for(let i = 0; i < 80 && !document.querySelector('.rs-rewards'); i++) await wait(150);
  await wait(2500);
  return { results: !!document.querySelector('.rs-rewards'), questions: n0, answered: ((store.lifetime||{}).answered || 0) - a0 }; }"""

def fresh(text, rooms=None, friends=(FRIEND,), acad=None, ifc=None):
    seed, a, f = P.seed(P.ACAD_UNITS, P.IFC_UNITS, acad=acad, ifc=ifc, friends=list(friends))
    if rooms: seed["vrooms"].update(rooms)
    cloud, srv, url = P.start(text, seed)
    return cloud, srv, url, a, f

ALL_ERRS = []
def dev(br, url, a, f, cls, name="A", **kw):
    ctx, pg, errs = P.device(br, url, name, P.init_js(a, f, cls), **kw)
    ALL_ERRS.append((cls, name, errs))
    P.quiet(pg)
    return ctx, pg

def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=P.CHROME)

        # ---------------------------------------------------------------- (1) pin and unpin
        if wanted(1):
            for cls in ("academy", "ifc"):
                with sect("(1) %s" % cls):
                    cloud, srv, url, a, f = fresh(TEXT)
                    ctx, pg = dev(br, url, a, f, cls)
                    held = P.hold(pg, 6)
                    o = pg.evaluate(OPEN_TILE, 1)
                    chk("(1) %s: a held badge's own page has Pin to profile (%s)" % (cls, o.get("text")), o.get("open") and o.get("pin"), o)
                    if o.get("pin"):
                        pg.click(".binspect-pin"); pg.wait_for_timeout(500)
                        st = pg.evaluate(PIN_STATE)
                        txt = pg.evaluate("()=>document.querySelector('.binspect-pin').textContent")
                        chk("(1) %s: the tap pins it - stored by its unit name with a time, and the button now unpins (%s)" % (cls, txt),
                            st["stored"] and st["stored"].get("u") == o["unit"] and st["stored"].get("at", 0) > 0 and st["mine"] == o["unit"] and txt != o["text"], st)
                    pg.evaluate(CLOSE); pg.evaluate("()=>showProfile()"); pg.wait_for_timeout(1500)
                    pr = pg.evaluate(PROFILE)
                    chk("(1) %s: Profile's person card shows that badge as its medallion" % cls, pr["unit"] == o.get("unit") and not pr["spot"], pr)
                    # the other class's pin is untouched (one per class)
                    other = "ifc" if cls == "academy" else "academy"
                    okey = "class26e.ifc.drill.v1" if other == "ifc" else "class26e.drill.v1"
                    # (the bracket read: Fire Code's page maps getItem's academy keys onto its own)
                    ot = pg.evaluate("(k)=>{ try{ const o = JSON.parse(localStorage[k] || 'null'); return o && o.pinnedBadge ? o.pinnedBadge.u : ''; }catch(e){ return 'x'; } }", okey)
                    chk("(1) %s: one pin per class - the other class's saved copy has none (%r)" % (cls, ot), ot == "", ot)
                    # unpin from the medallion itself (your own: in your hand, with Unpin)
                    pg.evaluate("()=>{ const m = document.querySelector('#stage .pin-host > .pin-mark'); m && m.click(); }"); pg.wait_for_timeout(1500)
                    b = pg.evaluate("()=>{ const b = document.querySelector('.binspect .binspect-pin'); return b ? b.textContent : null; }")
                    chk("(1) %s: your own medallion opens the badge in your hand, with Unpin" % cls, bool(b), b)
                    if b: pg.click(".binspect-pin"); pg.wait_for_timeout(400)
                    st = pg.evaluate(PIN_STATE)
                    pg.evaluate(CLOSE); pg.evaluate("()=>showProfile()"); pg.wait_for_timeout(1500)
                    pr = pg.evaluate(PROFILE)
                    chk("(1) %s: unpinned - stored as none, and Profile shows the spot to pin one" % cls, st["has"] and st["stored"]["u"] == "" and pr["spot"] and not pr["unit"], [st, pr])
                    pg.evaluate("()=>{ const s = document.querySelector('#stage .pin-spot'); s && s.click(); }"); pg.wait_for_timeout(1500)
                    onb = pg.evaluate("()=>!!document.querySelector('#stage .badges-tab .ncase')")
                    chk("(1) %s: the spot leads to the badges to choose from" % cls, onb)
                    o2 = pg.evaluate(OPEN_TILE, -1)
                    chk("(1) %s: a badge not held has no Pin on its page" % cls, o2.get("open") and not o2.get("pin"), o2)
                    pg.evaluate(CLOSE)
                    ctx.close(); srv.shutdown()

        # ---------------------------------------------------------------- (2) persistence across reload
        if wanted(2):
            for cls in ("academy", "ifc"):
                with sect("(2) %s" % cls):
                    cloud, srv, url, a, f = fresh(TEXT)
                    ctx, pg = dev(br, url, a, f, cls)
                    held = P.hold(pg, 6)
                    u = held[2] if len(held) > 2 else None
                    pg.evaluate("(u)=>{ try{ setPinnedBadge(u); }catch(e){} }", u)
                    doc = "progress/" + P.CODE + ("__ifc" if cls == "ifc" else "")
                    t0 = time.time(); cu = None
                    while time.time() - t0 < 90:   # an account write waits out the 60s gap since the last one (CLOUD_PUSH_MIN_GAP_MS)
                        d = cloud.data["progress"].get(P.CODE + ("__ifc" if cls == "ifc" else ""), {})
                        cu = (d.get("pinnedBadge") or {}).get("u")
                        if cu == u: break
                        time.sleep(.3)
                    chk("(2) %s: the pin reaches the account's cloud copy (%s)" % (cls, doc), cu == u and u, cu)
                    pg.reload(); pg.wait_for_timeout(3800)
                    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); }"); P.quiet(pg)
                    pg.evaluate("()=>showProfile()"); pg.wait_for_timeout(1500)
                    st = pg.evaluate(PIN_STATE); pr = pg.evaluate(PROFILE)
                    chk("(2) %s: opened again, the pin is there - stored and on Profile" % cls, st["mine"] == u and pr["unit"] == u, [st, pr])
                    ctx.close(); srv.shutdown()

        # ---------------------------------------------------------------- (3) two devices, newest wins
        if wanted(3):
            with sect("(3)"):
                cloud, srv, url, a, f = fresh(TEXT)
                ctxA, A = dev(br, url, a, f, "academy", "A")
                held = P.hold(A, 6)
                A.wait_for_timeout(4000)
                ctxB, B = dev(br, url, a, f, "academy", "B")
                B.wait_for_timeout(1500)
                ux, uy = held[1], held[4]
                A.evaluate("(u)=>{ try{ setPinnedBadge(u); }catch(e){} }", ux)
                got = until(B, "(u)=>typeof myPinnedBadge === 'function' && myPinnedBadge() === u", ux, tries=110, step=1000)
                chk("(3) A pins %s: B, already open, gets it" % ux, got, B.evaluate(PIN_STATE))
                B.wait_for_timeout(1500)
                B.evaluate("(u)=>{ try{ setPinnedBadge(u); }catch(e){} }", uy)
                got = until(A, "(u)=>typeof myPinnedBadge === 'function' && myPinnedBadge() === u", uy, tries=110, step=1000)
                chk("(3) B then pins %s: the newer pick wins on A too" % uy, got, A.evaluate(PIN_STATE))
                A.wait_for_timeout(1500)
                A.evaluate("()=>{ try{ setPinnedBadge(''); }catch(e){} }")
                got = until(B, "()=>typeof myPinnedBadge === 'function' && myPinnedBadge() === '' && store.pinnedBadge.u === ''", tries=110, step=1000)
                chk("(3) A unpins: B follows (an unpin is a pick too)", got, B.evaluate(PIN_STATE))
                m = A.evaluate("""([x, y])=>{ if(typeof pinnedBadgeOf !== 'function') return null;
                  const r = {};
                  let d = { pinnedBadge: { u: x, at: 2000 } }, s = { pinnedBadge: { u: y, at: 1000 } }; mergeSameAccount(d, s); r.olderSrc = d.pinnedBadge.u;
                  d = { pinnedBadge: { u: x, at: 1000 } }; s = { pinnedBadge: { u: y, at: 2000 } }; let res = mergeSameAccount(d, s); r.newerSrc = d.pinnedBadge.u; r.gained = res.gained;
                  d = { pinnedBadge: { u: x, at: 3000 } }; s = { pinnedBadge: { u: '', at: 2000 } }; mergeSameAccount(d, s); r.olderUnpin = d.pinnedBadge.u;
                  d = {}; s = { pinnedBadge: { u: y, at: 5 } }; mergeSameAccount(d, s); r.fromNone = d.pinnedBadge.u;
                  const keep = JSON.parse(JSON.stringify(store.pinnedBadge));
                  store.pinnedBadge = { u: x, at: 9000 }; mergeLeavingAccount({ pinnedBadge: { u: y, at: 100 } }, null); r.leavingOlder = store.pinnedBadge.u;
                  store.pinnedBadge = { u: x, at: 100 }; mergeLeavingAccount({ pinnedBadge: { u: y, at: 9000 } }, null); r.leavingNewer = store.pinnedBadge.u;
                  store.pinnedBadge = keep;
                  r.defaulted = JSON.stringify(pinnedBadgeOf(undefined)); r.junk = JSON.stringify(pinnedBadgeOf({ u: 7, at: 'x' }));
                  return r; }""", [ux, uy])
                chk("(3) merge rules: an older copy never undoes a newer pick (pin or unpin), a newer one wins and counts as gained, none takes any",
                    m and m["olderSrc"] == ux and m["newerSrc"] == uy and m["gained"] and m["olderUnpin"] == ux and m["fromNone"] == uy, m)
                chk("(3) the leaving account's merge takes the later pick too", m and m["leavingOlder"] == ux and m["leavingNewer"] == uy, m)
                chk("(3) a copy with none or junk reads as nothing pinned", m and json.loads(m["defaulted"]) == {"u": "", "at": 0} and json.loads(m["junk"]) == {"u": "", "at": 0}, m)
                ctxA.close(); ctxB.close(); srv.shutdown()

        # ---------------------------------------------------------------- (4) no extra write
        if wanted(4):
            with sect("(4)"):
                def drill_cost(text, pin):
                    cloud, srv, url, a, f = fresh(text)
                    ctx, pg = dev(br, url, a, f, "academy", "D")
                    held = P.hold(pg, 6)
                    pg.wait_for_timeout(9000)   # boot's own writes (the account read, the launch's row) are over
                    k0 = len(cloud.writes)
                    # the same account write on both builds: the pick saved (this build's setPinnedBadge does exactly this)
                    pg.evaluate("(u)=>{ store.pinnedBadge = { u: u, at: Date.now() }; saveStore(); }", held[2] if pin else "")
                    pg.wait_for_timeout(66000)   # the account's own write comes within the 60s gap (CLOUD_PUSH_MIN_GAP_MS)
                    k1 = len(cloud.writes)
                    r = pg.evaluate(DRILL)
                    pg.wait_for_timeout(4000)
                    ws = cloud.writes[k0:]
                    row = cloud.data["leaderboard"].get(P.OWNER, {})
                    ctx.close(); srv.shutdown()
                    by = {}
                    for w in ws:
                        kind = w["path"].split("/")[0] + ("/row" if w["path"] == "leaderboard/" + P.OWNER else "")
                        by[kind] = by.get(kind, 0) + 1
                    rows_at_pin = sum(1 for w in cloud.writes[k0:k1] if w["path"] == "leaderboard/" + P.OWNER)
                    acct_at_pin = sum(1 for w in cloud.writes[k0:k1] if w["path"] == "progress/" + P.CODE)
                    return r, by, row, (rows_at_pin, acct_at_pin), held[2]
                r1, c1, row1, rp1, u1 = drill_cost(TEXT, True)
                r0, c0, row0, rp0, _ = drill_cost(BASE, True)
                tot1, tot0 = sum(c1.values()), sum(c0.values())
                chk("(4) the drill ran to its results on both builds (%s / %s)" % (r1, r0), r1.get("results") and r0.get("results"), [r1, r0])
                chk("(4) a pin and a 20-question drill write no more documents than the build before: this build %s, before %s" % (c1, c0), tot1 <= tot0, [c1, c0])
                chk("(4) the board row is written as often as before (%d / %d), never per answer (%s answers)" % (c1.get("leaderboard/row", 0), c0.get("leaderboard/row", 0), r1.get("answered")),
                    c1.get("leaderboard/row", 0) <= c0.get("leaderboard/row", 0) and c1.get("leaderboard/row", 0) < max(2, (r1.get("answered") or 20) // 4))
                chk("(4) the pin alone: the account's own write (%d) and no row write of its own (%d) in the minute after it" % (rp1[1], rp1[0]), rp1[0] == 0 and rp1[1] >= 1, rp1)
                chk("(4) the row the drill's end wrote carries the pin as `pb` (%r) - and no sync code" % row1.get("pb"), row1.get("pb") == u1 and P.CODE not in json.dumps(row1), {k: row1.get(k) for k in ("pb", "badges")})
                # a room: the join write and the beat carry it; the beat writes as often as before
                def room_cost(text):
                    rooms = {"PINAC1": P.room("academy", P.ACAD_UNITS, P.IFC_UNITS)}
                    cloud, srv, url, a, f = fresh(text, rooms=rooms)
                    ctx, pg = dev(br, url, a, f, "academy", "R", extra_init=P.FAST)
                    held = P.hold(pg, 6)
                    pg.evaluate("(u)=>{ store.pinnedBadge = { u: u, at: Date.now() }; saveStore(); }", held[3])
                    pg.evaluate(P.JOIN, "PINAC1")
                    me = P.OWNER
                    ent = (cloud.data["vrooms"]["PINAC1"]["participants"].get(me) or {})
                    joined_pb = ent.get("pb")
                    k0 = len(cloud.writes); pg.wait_for_timeout(3000)
                    beats = sum(1 for w in cloud.writes[k0:] if w["path"] == "vrooms/PINAC1")
                    pg.evaluate("()=>{ try{ setPinnedBadge(''); }catch(e){ store.pinnedBadge = { u: '', at: Date.now() }; } }")
                    pg.wait_for_timeout(1500)
                    after = (cloud.data["vrooms"]["PINAC1"]["participants"].get(me) or {}).get("pb")
                    ctx.close(); srv.shutdown()
                    return joined_pb, beats, after, held[3]
                jp1, b1, af1, u3 = room_cost(TEXT)
                jp0, b0, af0, _ = room_cost(BASE)
                chk("(4) a room's join write carries the pin (%r)" % jp1, jp1 == u3, jp1)
                chk("(4) the presence beat writes as often as before (%d / %d in 3s at the gate's fast beat)" % (b1, b0), b1 <= b0 + 1 and b1 > 0, [b1, b0])
                chk("(4) an unpin reaches the room by the next beat (%r)" % af1, af1 == "", af1)

        # ---------------------------------------------------------------- (5) other people's pins
        if wanted(5):
            for cls in ("academy", "ifc"):
                with sect("(5) %s" % cls):
                    U = UNITS[cls]
                    rooms = {"PINAC1": P.room("academy", P.ACAD_UNITS, P.IFC_UNITS), "PINFC1": P.room("ifc", P.IFC_UNITS, P.ACAD_UNITS)}
                    cloud, srv, url, a, f = fresh(TEXT, rooms=rooms)
                    ctx, pg = dev(br, url, a, f, cls)
                    P.hold(pg, 6)
                    pg.evaluate("()=>showRankings()"); pg.wait_for_timeout(3500); P.quiet(pg)
                    rows = pg.evaluate("""(pre)=>[...document.querySelectorAll('#stage .rank-row[data-pub]')].filter(r => r.dataset.pub.startsWith(pre))
                      .map(r => { const m = r.querySelector('.pin-mark'); return [r.dataset.pub, m ? m.dataset.unit : null, m ? !!m.querySelector('svg.badge-art') : null]; })""", P.MATE_PREFIX)
                    got = {int(p[-4:]): (u, art) for p, u, art in rows}
                    want = {i: (U[j] if j is not None else None) for i, j in WANT_ROW.items()}
                    bad = {i: (got.get(i, ("missing",))[0], want[i]) for i in want if got.get(i, ("missing",))[0] != want[i]}
                    chk("(5) %s: the Leaderboard draws exactly the real pins (%d rows; other class, junk, a non-string, none, an older row, not held: nothing)" % (cls, len(rows)),
                        len(got) == len(want) and not bad, bad or len(rows))
                    chk("(5) %s: each is the badge's own art" % cls, all(v[1] for v in got.values() if v[0]), got)
                    # tap one: read-only, its name, whose
                    v = pg.evaluate("""async ()=>{ const W = ms => new Promise(r => setTimeout(r, ms));
                      const row = [...document.querySelectorAll('#stage .rank-row')].find(r => r.dataset.pub === '%s'); const m = row && row.querySelector('.pin-mark');
                      if(!m) return null; m.click(); await W(1500);
                      const ov = document.querySelector('.binspect'); const sheet = document.querySelector('.person-card');
                      return { open: !!ov, view: ov && ov.classList.contains('is-view'), name: ov && ov.querySelector('.binspect-name').textContent,
                        whose: ov && ov.querySelector('.binspect-whose') ? ov.querySelector('.binspect-whose').textContent : null, pin: !!(ov && ov.querySelector('.binspect-pin')),
                        title: unitTitle(m.dataset.unit), sheet: !!sheet }; }""" % FRIEND)
                    chk("(5) %s: a tap on a classmate's pin opens that badge read-only - its name, whose it is, no Pin, not the person card" % cls,
                        v and v["open"] and v["view"] and v["title"] in (v["name"] or "") and v["whose"] and "Alexis" in v["whose"] and not v["pin"] and not v["sheet"], v)
                    pg.evaluate(CLOSE)
                    # the person card and the friend's profile
                    pc = pg.evaluate("""(pub)=>{ const e = (%s).find(r => r.pub === pub); openPersonSheet(Object.assign({}, e, { boardCls: ART_PAGE }));
                      const m = document.querySelector('.person-card .pin-mark'); return m ? m.dataset.unit : null; }""" % ROWS_OF, FRIEND)
                    chk("(5) %s: the person card shows their pin" % cls, pc == U[3], pc)
                    pg.evaluate(CLOSE)
                    for i in (4, 5, 6, 9):
                        pub = "%s%04d" % (P.MATE_PREFIX, i)
                        x = pg.evaluate("""(pub)=>{ const e = (%s).find(r => r.pub === pub); if(!e) return 'norow'; openPersonSheet(Object.assign({}, e, { boardCls: ART_PAGE }));
                          const m = document.querySelector('.person-card .pin-mark'); const r = m ? m.dataset.unit : null; document.querySelectorAll('.invite-overlay').forEach(o => o.remove()); return r; }""" % ROWS_OF, pub)
                        chk("(5) %s: no pin on the card of classmate %d (%s)" % (cls, i, P.mates(U, U)[i][0]), x is None, x)
                    fp = pg.evaluate("""async (pub)=>{ const e = (%s).find(r => r.pub === pub); showFriendProfile(Object.assign({}, e, { boardCls: ART_PAGE }));
                      await new Promise(r => setTimeout(r, 1500)); const m = document.querySelector('#stage .screen-friendprofile .pin-host > .pin-mark');
                      return m ? m.dataset.unit : null; }""" % ROWS_OF, FRIEND)
                    chk("(5) %s: a friend's profile shows their pin on the plate" % cls, fp == U[3], fp)
                    # a room of this class, then one of the other
                    room = "PINAC1" if cls == "academy" else "PINFC1"
                    pg.evaluate(P.JOIN, room); pg.wait_for_timeout(600)
                    vr = pg.evaluate("""()=>[...document.querySelectorAll('.vroom-roster .vroom-row')].map(r => { const m = r.querySelector('.pin-mark'); const n = r.querySelector('.lb-name');
                      return [n ? n.firstChild.textContent.trim() : '', m ? m.dataset.unit : null]; })""")
                    names = [m[0] for m in P.mates(U, U)]
                    gotv = {names.index(n): u for n, u in vr if n in names}
                    wantv = {i: (U[j] if j is not None else None) for i, j in WANT_VR.items()}
                    badv = {i: (gotv.get(i, "missing"), wantv[i]) for i in wantv if gotv.get(i, "missing") != wantv[i]}
                    chk("(5) %s: a %s room's roster draws exactly the real pins" % (cls, cls), not badv and len(gotv) == len(wantv), badv or vr)
                    ent = cloud.data["vrooms"][room]["participants"].get(P.OWNER) or {}
                    chk("(5) %s: your entry in your class's room carries your pin field" % cls, "pb" in ent, ent.keys())
                    pg.evaluate("()=>{ try{ leaveVirtualRoomLobby && leaveVirtualRoomLobby(); }catch(e){} }"); pg.wait_for_timeout(800)
                    ctx.close(); srv.shutdown()
                    # the other class's room, from this page: nothing drawn, nothing written
                    cloud, srv, url, a, f = fresh(TEXT, rooms=rooms)
                    ctx, pg = dev(br, url, a, f, cls, "O")
                    P.hold(pg, 6)
                    pg.evaluate("()=>{ try{ setPinnedBadge(badgesEarnedList()[0]); }catch(e){} }")
                    oroom = "PINFC1" if cls == "academy" else "PINAC1"
                    pg.evaluate(P.JOIN, oroom); pg.wait_for_timeout(1500)
                    n = pg.evaluate("()=>document.querySelectorAll('.vroom-roster .vroom-row').length")
                    k = pg.evaluate("()=>document.querySelectorAll('.vroom-roster .pin-mark').length")
                    ent = cloud.data["vrooms"][oroom]["participants"].get(P.OWNER) or {}
                    chk("(5) %s: the other class's room draws no pin (%d rows) and gets none of yours" % (cls, n), n > 0 and k == 0 and "pb" not in ent, [n, k, ent.get("pb")])
                    ctx.close(); srv.shutdown()

        # ---------------------------------------------------------------- (6) a badge no longer held never shows
        if wanted(6):
            for cls in ("academy", "ifc"):
                with sect("(6) %s" % cls):
                    cloud, srv, url, a, f = fresh(TEXT)
                    ctx, pg = dev(br, url, a, f, cls)
                    held = P.hold(pg, 6)
                    u = held[0]
                    pg.evaluate("(u)=>{ try{ setPinnedBadge(u); }catch(e){} }", u)
                    # no longer held (in memory: a band raised, a badge hidden) - the stored pick stays, nothing shows
                    r = pg.evaluate("""async (u)=>{ const W = ms => new Promise(r => setTimeout(r, ms));
                      store.unitPerfects[u] = 0;
                      showProfile(); await W(1200);
                      const h = document.querySelector('#stage .pin-host');
                      const out = { stored: store.pinnedBadge && store.pinnedBadge.u, mine: typeof myPinnedBadge === 'function' ? myPinnedBadge() : 'nofn',
                        drawn: h && h.querySelector('.pin-mark') ? h.querySelector('.pin-mark').dataset.unit : null, spot: !!(h && h.querySelector('.pin-spot')) };
                      try{ out.row = (window.NOVA_CLASS === 'ifc' ? buildClassBoardRow() : buildLeaderboardRow()).pb; }catch(e){ out.row = 'err'; }
                      try{ const e = vroomMeEntry(ownClass()); if(typeof vroomPinIntoEntry === 'function') vroomPinIntoEntry(e, ownClass()); out.entry = e.pb; }catch(e){ out.entry = 'err'; }
                      showRankings(); await W(2500);
                      const me = document.querySelector('#stage .rank-row[data-me="1"]'); out.meRow = !!me; out.meRowPin = me && me.querySelector('.pin-mark') ? me.querySelector('.pin-mark').dataset.unit : null;
                      return out; }""", u)
                    chk("(6) %s: not held - nothing on Profile (the spot), your row and your room entry publish none, your own row draws none" % cls,
                        r["stored"] == u and r["mine"] == "" and r["drawn"] is None and r["spot"] and r["row"] == "" and r["entry"] == "" and r["meRow"] and r["meRowPin"] is None, r)
                    s = pg.evaluate("""(u)=>{ if(typeof setPinnedBadge !== 'function') return 'nofn'; const back = setPinnedBadge(u); return [back, store.pinnedBadge.u]; }""", u)
                    chk("(6) %s: a badge not held is never stored as the pin" % cls, s == ["", ""], s)
                    ctx.close(); srv.shutdown()

        # ---------------------------------------------------------------- (7) layout
        if wanted(7):
            LAYOUT = """async ()=>{ const W = ms => new Promise(r => setTimeout(r, ms)); const out = {};
              const R = el => { const r = el.getBoundingClientRect(); return { l: r.left, t: r.top, r: r.right, b: r.bottom, w: r.width, h: r.height, cx: (r.left + r.right) / 2, cy: (r.top + r.bottom) / 2 }; };
              const hits = (el, cx, cy, d) => [[d, 0], [-d, 0], [0, d], [0, -d]].every(([dx, dy]) => { const t = document.elementFromPoint(cx + dx, cy + dy); return t && (t === el || el.contains(t)); });
              const crisp = el => { const im = el.querySelector('image.badge-raster'); if(!im || !im.__strike) return false; const r = el.querySelector('.pin-mark-art').getBoundingClientRect();
                return im.__strike.W >= Math.floor(Math.max(r.width, r.height) * (window.devicePixelRatio || 1)) * .95; };
              showProfile(); await W(2200);
              const host = document.querySelector('#stage .pin-host'), m = host && host.querySelector(':scope > .pin-mark'), plate = host && host.querySelector('.profile-hero-avatar');
              const card = document.querySelector('#stage .profile-hero');
              if(m && plate){ const a = R(m), p = R(plate), c = R(card);
                const rad = Math.hypot(a.cx - p.cx, a.cy - p.cy), ang = Math.atan2(a.cy - p.cy, a.cx - p.cx) * 180 / Math.PI;
                m.scrollIntoView({ block: 'center' }); await W(300); const a2 = R(m);
                out.hero = { size: Math.round(a.w), onRing: Math.abs(rad - p.w / 2) <= 3, ang: Math.round(ang), inCard: a.l >= c.l && a.r <= c.r && a.t >= c.t && a.b <= c.b,
                  target: hits(m, a2.cx, a2.cy, 21), crisp: crisp(m), still: getComputedStyle(m).animationName }; }
              showRankings(); await W(3000);
              const rows = [...document.querySelectorAll('#stage .rank-rows > .rank-row')].filter(r => r.querySelector('.rank-name'));
              const rh = rows.map(r => Math.round(r.getBoundingClientRect().height));
              const pinned = rows.filter(r => r.querySelector('.pin-mark'));
              out.rows = { n: rows.length, pinned: pinned.length, heights: [...new Set(rh)], sizes: [...new Set(pinned.map(r => Math.round(R(r.querySelector('.pin-mark')).w * 10) / 10))],
                beside: pinned.every(r => { const nm = R(r.querySelector('.pin-line > .rank-name')), pm = R(r.querySelector('.pin-mark')); return pm.l >= nm.r - .5 && pm.l - nm.r < 14 && Math.abs(pm.cy - nm.cy) < 4; }),
                inside: pinned.every(r => { const rr = R(r), pm = R(r.querySelector('.pin-mark')), cols = r.querySelector('.rank-cols'); const cc = cols ? R(cols) : null;
                  return pm.l >= rr.l && pm.r <= rr.r && pm.t >= rr.t && pm.b <= rr.b && (!cc || pm.r <= cc.l + .5); }),
                crisp: pinned.every(r => crisp(r.querySelector('.pin-mark'))),
                minSize: Math.min.apply(null, pinned.map(r => R(r.querySelector('.pin-mark')).w)) };
              const long = rows.find(r => /Montgomery/.test(r.textContent)); const ln = long && long.querySelector('.rank-name');
              out.longName = ln ? { ellipsis: ln.scrollWidth > ln.clientWidth + 1, pin: !!long.querySelector('.pin-mark'), pinW: Math.round(R(long.querySelector('.pin-mark')).w * 10) / 10 } : null;
              const first = pinned[0] && pinned[0].querySelector('.pin-mark');
              if(first){ first.scrollIntoView({ block: 'center' }); await W(300); const a = R(first); out.rows.target = hits(first, a.cx, a.cy, 20); }
              out.overflow = document.documentElement.scrollWidth > innerWidth + 1;
              return out; }"""
            DEVS = [("Pro Max", 440, 956), ("iPad", 834, 1194)]
            for cls in ("academy", "ifc"):
                for dname, w, h in DEVS:
                    for z in ((85, 100, 135) if dname == "Pro Max" else (100,)):
                        tag = "%s %s %d%%" % (cls, dname, z)
                        with sect("(7) " + tag):
                            cloud, srv, url, a, f = fresh(TEXT)
                            ctx, pg = dev(br, url, a, f, cls, w=w, h=h, zoom=z)
                            held = P.hold(pg, 6)
                            pg.evaluate("(u)=>{ try{ setPinnedBadge(u); }catch(e){} }", held[1])
                            L = pg.evaluate(LAYOUT)
                            hh = L.get("hero") or {}
                            chk("(7) %s: the medallion sits on the plate's ring at 45 degrees (%s deg), inside the card" % (tag, hh.get("ang")),
                                hh.get("onRing") and hh.get("ang") in range(40, 51) and hh.get("inCard"), hh)
                            chk("(7) %s: the medallion is a target of 44px or more and its art is drawn for its pixels (%spx)" % (tag, hh.get("size")), hh.get("target") and hh.get("crisp"), hh)
                            rr = L.get("rows") or {}
                            chk("(7) %s: on the Leaderboard %d rows carry a pin, beside the name, inside the row, the same size on each (%s)" % (tag, rr.get("pinned", 0), rr.get("sizes")),
                                rr.get("pinned", 0) >= 5 and rr.get("beside") and rr.get("inside") and len(rr.get("sizes") or [0, 0]) == 1 and rr.get("minSize", 0) >= 20, rr)
                            chk("(7) %s: rows with and without a pin are one height (%s); a pin's target is 44px; its art is crisp" % (tag, rr.get("heights")),
                                len(rr.get("heights") or []) == 1 and rr.get("target") and rr.get("crisp"), rr)
                            ln = L.get("longName") or {}
                            # the phone's row is too narrow for it (it must ellipsize); the iPad's may hold it whole
                            chk("(7) %s: the long name %s and its badge is whole (%s)" % (tag, "ellipsizes" if ln.get("ellipsis") else "fits", ln.get("pinW")),
                                (ln.get("ellipsis") or dname == "iPad") and ln.get("pin") and rr.get("sizes") and abs(ln.get("pinW", 0) - rr["sizes"][0]) < .5, ln)
                            chk("(7) %s: no sideways scroll" % tag, not L.get("overflow"), L.get("overflow"))
                            ctx.close(); srv.shutdown()

        # ---------------------------------------------------------------- (8) errors
        errs = [(c, n, e) for c, n, es in ALL_ERRS for e in es]
        chk("(8) no page error on any of the %d loads" % len(ALL_ERRS), not errs, errs[:6])
        br.close()
    print("\n%d checks, %d failed" % (N[0], len(FAILS)))
    for f in FAILS: print("  FAIL", f)
    sys.exit(1 if FAILS else 0)

main()
