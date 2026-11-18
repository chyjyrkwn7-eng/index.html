"""384.134 prestige in Virtual Rooms: screenshots for Madison. Made-up classmates at prestige 0, 1, 2 and 3 in a Fire Code room (the lobby, its
chat, a person card, the race podium and the results board), the same room seen from the academy's page, and an academy room whose
entries all (wrongly) say III - which draws none.

  python3 tools/shoot-b384-vrprestige.py OUTDIR [--dev pm|ipad] [--file index.html]
Names are made up. Nothing is written anywhere but OUTDIR."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b384_prestige_lib as L
from playwright.sync_api import sync_playwright

ARGS = sys.argv[1:]
OUT = ARGS[0] if ARGS and not ARGS[0].startswith("--") else "/dev/shm/vrpg-shots"
def arg(n, d=None): return ARGS[ARGS.index(n) + 1] if n in ARGS else d
DEV = arg("--dev", "pm")
W, H = (440, 956) if DEV == "pm" else (834, 1194)
os.makedirs(OUT, exist_ok=True)
FILE = arg("--file", os.path.join(L.ROOT, "index.html"))

# reuse the gate's room builder
_src = open(os.path.join(HERE, "check-b384-vrprestige.py"), encoding="utf-8").read().rsplit("\nmain()", 1)[0]
G = {"__name__": "gate", "__file__": os.path.join(HERE, "check-b384-vrprestige.py")}
sys.argv = [sys.argv[0]]; exec(_src, G)
G["TEXT"] = open(FILE, encoding="utf-8").read()
room, boot, JOIN, SET_PG, pub_of = G["room"], G["boot"], G["JOIN"], G["SET_PG"], G["pub_of"]

CAST = [("Alexis", "pgstate", 3, 80, 40), ("Kimber", "pgmarshal", 2, 80, 38), ("Leeland", "pgdeputy", 1, 80, 38), ("Rosa", "grizzly", 0, 52, 20)]
CHAT = [0, 1, 2, 3, 0]

def shot(pg, name):
    p = os.path.join(OUT, "%s-%s.png" % (DEV, name))
    pg.screenshot(path=p)
    print("shot", p, flush=True)

with sync_playwright() as p:
    br = p.chromium.launch(executable_path=L.CHROME, args=["--no-sandbox"])
    # --- Fire Code's page, a Fire Code room: you hold Prestige II
    ctx, pg, errs = boot(br, "ifc", 2, {"FCROOM": room("ifc", CAST, chat=CHAT), "FCDONE": room("ifc", CAST, finished=True, chat=CHAT)}, w=W, h=H)
    pg.evaluate(JOIN, "FCROOM"); pg.wait_for_timeout(600)
    shot(pg, "1-fire-code-lobby")
    pg.evaluate("()=>{ const c = document.querySelector('.vroom-chat'); if(c) c.scrollIntoView({block:'end'}); }"); pg.wait_for_timeout(500)
    shot(pg, "2-fire-code-lobby-chat")
    pg.evaluate("()=>window.scrollTo(0, 0)")
    pg.evaluate("""()=>{ [...document.querySelectorAll('.vroom-roster .vroom-row')].find(r => /Alexis/.test(r.textContent)).click(); }"""); pg.wait_for_timeout(800)
    shot(pg, "3-fire-code-person-card")
    pg.evaluate("()=>document.querySelectorAll('.invite-overlay').forEach(o => o.remove())")
    pg.evaluate("""()=>{ const d = JSON.parse(JSON.stringify(__cloud.vrooms.FCDONE)); vroomMyKey = publicIdOf(); stage.replaceChildren(buildVroomRacePodium(d)); }""")
    pg.wait_for_timeout(700)
    shot(pg, "4-fire-code-podium")
    pg.evaluate("""()=>{ const d = JSON.parse(JSON.stringify(__cloud.vrooms.FCDONE)); stage.replaceChildren(); playVroomRaceCutscene(vroomRankedEntries(d), roomClassOf(d)); }""")
    pg.wait_for_timeout(6500)
    shot(pg, "5-fire-code-results-board")
    ctx.close()
    # --- the academy's page in the same Fire Code room
    ctx, pg, errs = boot(br, "academy", 3, {"FCROOM": room("ifc", CAST, chat=CHAT)}, w=W, h=H)
    pg.evaluate(JOIN, "FCROOM"); pg.wait_for_timeout(600)
    shot(pg, "6-fire-code-room-from-academy-page")
    ctx.close()
    # --- an academy room (entries wrongly say III): none
    ctx, pg, errs = boot(br, "ifc", 2, {"ACROOM": room(None, CAST, chat=CHAT, hostile=3)}, w=W, h=H)
    pg.evaluate(JOIN, "ACROOM"); pg.wait_for_timeout(600)
    shot(pg, "7-academy-room-lobby")
    ctx.close()
    ctx, pg, errs = boot(br, "academy", 3, {"ACROOM": room(None, CAST, chat=CHAT, hostile=3)}, w=W, h=H)
    pg.evaluate(JOIN, "ACROOM"); pg.wait_for_timeout(600)
    shot(pg, "8-academy-room-from-academy-page")
    ctx.close()
    br.close()
