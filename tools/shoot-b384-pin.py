#!/usr/bin/env python3
"""384 pin: screenshots for Madison - a badge pinned to your profile, in both classes.

  python3 tools/shoot-b384-pin.py OUTDIR [--dev pm|ipad] [--file index.html] [--zoom 85|100|135]

Per class (academy, ifc): Profile with the pin; Profile with nothing pinned (the spot); the badge's own page with Pin to profile; the
Leaderboard with several classmates' pins; the person card; a friend's profile; somebody's pin opened (read-only); a Virtual Room.
Names are made up. Nothing is written anywhere but OUTDIR."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import b384_pin_lib as P
from playwright.sync_api import sync_playwright

ARGS = sys.argv[1:]
OUT = ARGS[0] if ARGS and not ARGS[0].startswith("--") else "/dev/shm/pin-shots"
def arg(n, d=None): return ARGS[ARGS.index(n) + 1] if n in ARGS else d
DEV = arg("--dev", "pm")
ZOOM = int(arg("--zoom", "100"))
W, H = (440, 956) if DEV == "pm" else (834, 1194)
FILE = arg("--file", os.path.join(P.L.ROOT, "index.html"))
os.makedirs(OUT, exist_ok=True)
SRC = open(FILE, encoding="utf-8").read()
FRIEND = "%s%04d" % (P.MATE_PREFIX, 0)
TAG = DEV + ("" if ZOOM == 100 else "-z%d" % ZOOM)

def shot(pg, name):
    p = os.path.join(OUT, "%s-%s.png" % (TAG, name))
    pg.screenshot(path=p)
    print("shot", p, flush=True)

def settle(pg, ms=1600):
    pg.wait_for_timeout(ms); P.quiet(pg)

ROWS_OF = "()=>(window.NOVA_CLASS === 'ifc' ? (typeof classBoardRows !== 'undefined' ? classBoardRows : []) : leaderboardRows) || []"

rooms = {"PINAC1": P.room("academy", P.ACAD_UNITS, P.IFC_UNITS), "PINFC1": P.room("ifc", P.IFC_UNITS, P.ACAD_UNITS)}
seed, acad, ifc = P.seed(P.ACAD_UNITS, P.IFC_UNITS, friends=[FRIEND])
seed["vrooms"].update(rooms)
cloud, srv, url = P.start(SRC, seed)

with sync_playwright() as p:
    br = p.chromium.launch(executable_path=P.CHROME)
    for cls in ("academy", "ifc"):
        ctx, pg, errs = P.device(br, url, "A" + cls, P.init_js(acad, ifc, cls), w=W, h=H, zoom=None if ZOOM == 100 else ZOOM)
        P.quiet(pg); P.hold(pg, 6)
        # nothing pinned: the spot
        pg.evaluate("()=>{ setPinnedBadge(''); showProfile(); }"); settle(pg)
        shot(pg, cls + "-1-profile-spot")
        # the badge's own page, from the case: Pin to profile
        pg.evaluate("()=>showRanksScreen('badges')"); settle(pg, 3500)
        pg.evaluate("()=>{ const t = [...document.querySelectorAll('.ncase-cell.is-earned')][1]; t.scrollIntoView({block:'center'}); }"); pg.wait_for_timeout(600)
        pg.evaluate("()=>{ [...document.querySelectorAll('.ncase-cell.is-earned')][1].click(); }"); pg.wait_for_timeout(2600)
        shot(pg, cls + "-2-badge-page-pin")
        pg.click(".binspect-pin"); pg.wait_for_timeout(900)
        shot(pg, cls + "-3-badge-page-pinned")
        pg.evaluate("()=>{ try{ badgeInspectNow && badgeInspectNow.teardown(); }catch(e){} showProfile(); }"); settle(pg, 2200)
        shot(pg, cls + "-4-profile-pinned")
        pg.evaluate("()=>showRankings()"); settle(pg, 3000)
        shot(pg, cls + "-5-leaderboard")
        # somebody's pin, read-only
        pg.evaluate("()=>{ const b = [...document.querySelectorAll('.rank-row .pin-mark')].find(b => !b.closest('[data-me]')); b && b.click(); }"); pg.wait_for_timeout(2400)
        shot(pg, cls + "-6-their-pin")
        pg.evaluate("()=>{ try{ badgeInspectNow && badgeInspectNow.teardown(); }catch(e){} }"); pg.wait_for_timeout(300)
        # the person card, then the friend's profile
        pg.evaluate("(pub)=>{ const e = (" + ROWS_OF + ")().find(r => r.pub === pub); openPersonSheet(Object.assign({}, e, { boardCls: ART_PAGE })); }", FRIEND); pg.wait_for_timeout(1200)
        shot(pg, cls + "-7-person-card")
        pg.evaluate("()=>document.querySelectorAll('.invite-overlay').forEach(o => o.remove())")
        pg.evaluate("(pub)=>{ const e = (" + ROWS_OF + ")().find(r => r.pub === pub); showFriendProfile(Object.assign({}, e, { boardCls: ART_PAGE })); }", FRIEND); settle(pg, 2200)
        shot(pg, cls + "-8-friend-profile")
        # a Virtual Room of this class
        pg.evaluate(P.JOIN, "PINAC1" if cls == "academy" else "PINFC1"); settle(pg, 1200)
        shot(pg, cls + "-9-virtual-room")
        print(cls, "page errors:", errs, flush=True)
        ctx.close()
    br.close()
