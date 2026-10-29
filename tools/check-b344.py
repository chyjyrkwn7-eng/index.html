"""Build 344: the daily question, the class button and its list wear one Liquid Glass recipe; the tab bar keeps what a phone
does on a tap (frame gaps and build time), and a bug report carries it.
Run:  python3 tools/check-b344.py"""
import os, sys, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H = ROOT + "/tools"
src = open(H + "/record-landing.py").read().split("\nSCENES = {")[0]
g = {"__file__": H + "/record-landing.py", "__name__": "rl"}; exec(src, g)
rl_main = open(H + "/record-landing.py").read()
exec(rl_main[rl_main.index("def encode("):rl_main.index("\ndef main(") if "\ndef main(" in rl_main else None], g)
from playwright.sync_api import sync_playwright
rc = g["g"]; seed = dict(rc["SEED"]); seed["publicId"] = "xph5b57jbp5a"; seed["firstName"] = "Maddog"; seed["novaMet"] = 99
srv, port = rc["serve"]()
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else info)
CLEAR = "()=>{ for(let i=0;i<3;i++){ [...document.querySelectorAll('button')].filter(b=>/^(Got it|Continue|Close|Done|Skip|Not now)$/.test(b.textContent.trim())).forEach(b=>b.click()); } document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }"
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    ctx, pg = rc["new_page"](br, port, 440, 956, seed); pg.reload(); pg.wait_for_timeout(3000)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); store.novaMet=99; ['class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen'].forEach(k=>localStorage.setItem(k,'1')); store.dailyQuestionDate=''; showHome(); }"); pg.wait_for_timeout(1500)
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(400)
    d = pg.evaluate("""()=>{ const q=document.querySelector('.daily-question-fab'), b=document.querySelector('.class-bubble');
      document.querySelector('.class-bubble').click(); return null; }""")
    pg.wait_for_timeout(900)
    r = pg.evaluate("""()=>{ const q=document.querySelector('.daily-question-fab'), b=document.querySelector('.class-bubble'), l=document.querySelector('.csi-bubble');
      const cs = e => getComputedStyle(e);
      const hi = bg => (bg.match(/radial-gradient\\([^)]*\\)\\s*,?/)||[''])[0];
      return { qClass:q.className, qBg:cs(q).backgroundImage, bBg:cs(b).backgroundImage, qBorder:cs(q).borderTopColor, bBorder:cs(b).borderTopColor, lBg: l ? cs(l).backgroundImage : '', qBlur: cs(q).backdropFilter, bBlur: cs(b).backdropFilter, qWill: cs(q).willChange, bWill: cs(b).willChange,
        qSvg: (q.querySelector('svg')||q).innerHTML.slice(0,80), bSvg: b.querySelector('svg').innerHTML.slice(0,80), lSvg: l ? l.querySelector('svg').innerHTML.slice(0,80) : '' }; }""")
    chk("the daily question is ready in this check", "is-ready" in r["qClass"], r["qClass"])
    chk("the daily question and the class button share the glass's top light (the same first gradient)", r["qBg"].split("radial-gradient")[1][:60] == r["bBg"].split("radial-gradient")[1][:60], (r["qBg"][:140], r["bBg"][:140]))
    chk("ready adds the rank's colour wash (a second radial gradient the class button does not have)", r["qBg"].count("radial-gradient") >= 2 and r["bBg"].count("radial-gradient") == 1, (r["qBg"][:200], r["bBg"][:200]))
    chk("the class button's list buttons wear the glass too (a highlight gradient in their body)", "radial-gradient" in r["lBg"], r["lBg"][:140])
    chk("the glass blurs a little and holds no will-change layer of its own", "blur" in r["qBlur"] and "blur" in r["bBlur"] and r["qWill"] in ("auto", "") and r["bWill"] in ("auto", ""), r)
    chk("the same glass, a different thing in the middle (their icons differ)", r["qSvg"] != r["bSvg"] and r["bSvg"] != r["lSvg"], (r["qSvg"], r["bSvg"], r["lSvg"]))
    # the tab bar's record of what a tap did
    tabs = {t[0]: t for t in pg.evaluate("()=>[...document.querySelectorAll('.bottomtabs-navrow .bottomtab')].map(t=>{const r=t.getBoundingClientRect(); return [t.id, r.left+r.width/2, r.top+r.height/2]})")}
    pg.evaluate("()=>{ try{ localStorage.removeItem('class26e.tabperf'); }catch(e){} }")
    for sid in ("bottomtab-profile", "bottomtab-rewards", "bottomtab-home"):
        t = tabs[sid]; pg.mouse.click(t[1], t[2]); pg.wait_for_timeout(1700)
    txt = pg.evaluate("()=>tabPerfText()")
    #print("DBG", pg.evaluate("()=>({chat:document.body.classList.contains('chatdock-open'), barHidden:document.getElementById('bottomtabs').hidden, op:getComputedStyle(document.getElementById('bottomtabs')).opacity, stack:document.querySelector('.class-bubble-wrap').classList.contains('is-open'), ls:localStorage.getItem('class26e.tabperf')})"), tabs)
    chk("after tab taps the device has a record: frames, worst gap, counts over 34/50/100ms and the screen's build time", re.search(r"rewards.*f\d+ worst\d+ >34:\d+ >50:\d+ >100:\d+ build\d+x\d+", txt) is not None, txt)
    chk("a bug report would carry it (tabPerfText is wired into the report)", "perf: (typeof tabPerfText" in open(ROOT + "/index.html", encoding="utf-8").read())
    # the marks are silver, tinted by the theme (not a lilac shield / an orange flame)
    def stops(accent):
        return pg.evaluate("""(a)=>{ document.documentElement.dataset.accent=a; return [...document.querySelectorAll('.class-bubble svg stop')].map(s=>getComputedStyle(s).stopColor); }""", accent)
    def rgb(c):
        m = [float(x) for x in re.findall(r"[\d.]+", c)[:3]]
        return [v * 255 for v in m] if c.startswith("color(") else m
    silver = [rgb(c) for c in stops("ranger")]
    chroma = max(max(c) - min(c) for c in silver) if silver else 999
    chk("on the silver theme the class button's mark is plain silver (largest colour spread %d, 40 allowed)" % chroma, silver and chroma <= 40, silver)
    red = [rgb(c) for c in stops("titan")]
    chk("on a colour theme the silver leans towards the theme's colour (red over blue on Titan)", red and all(c[0] - c[2] >= 12 for c in red), red)
    pg.evaluate("()=>{ document.documentElement.dataset.accent='ink'; }")
    # whole pixels, so the 1px rim is not drawn between two rows
    px = pg.evaluate("""()=>{ const f=e=>{ const r=e.getBoundingClientRect(); return [r.width, r.height, r.bottom]; }; return { q:f(document.querySelector('.daily-question-fab')), b:f(document.querySelector('.class-bubble')) }; }""")
    frac = [abs(v - round(v)) for v in px["q"] + px["b"]]
    chk("the daily question and the class button sit on whole pixels (size and foot) so their rim is not broken (%s)" % (px,), max(frac) < .06, px)
    # the class button is under an open chat, not over it
    pg.evaluate("()=>{ document.querySelector('.class-bubble').click(); }"); pg.wait_for_timeout(500)
    cb = pg.evaluate("()=>{ const b=document.querySelector('.class-bubble').getBoundingClientRect(); return [b.left+b.width/2, b.top+b.height/2]; }")
    pg.evaluate("()=>{ const c=document.querySelector('.chatdock-btn'); if(c) c.click(); }"); pg.wait_for_timeout(1500)
    top = pg.evaluate("(p)=>{ const e=document.elementFromPoint(p[0],p[1]); return { inWrap: !!(e && e.closest('.class-bubble-wrap')), tag: e ? (e.className||e.tagName).toString().slice(0,40) : null, chat: document.body.classList.contains('chatdock-open') }; }", cb)
    chk("with the chat open nothing of the class button is over it", top["chat"] and not top["inWrap"], top)
    pg.evaluate("()=>{ try{ closeChatDock && closeChatDock(); }catch(e){} document.querySelectorAll('.chatdock-close, .chatdock-panel .back-link').forEach(b=>b.click()); }"); pg.wait_for_timeout(800)
    ctx.close(); br.close()
sys.exit(0 if ok else 1)
