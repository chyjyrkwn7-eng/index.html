"""Build 384: Fire Code's 25 and 50 - the Extinguisher (fireworks) and the Sprinklers (underwater), tightened.
Madison: "The extinguisher one is super cool. Tighten it up though, maybe it better. Tighten up all of them where you can to
ensure they perfect." (383: "The sprinklers is my favorite one but it could be better...")
Each effect plays in the Fire Code class on a stand-in 100% card, every animation paused and seeked, and everything is read off
the page (rects, computed transforms and opacities, the sprites' own raster sizes, the score rendered offline by NovaSound):
Extinguisher (iPhone 17 Pro Max 440x956 and iPad 834x1194)
 (E1) AIM: the nozzle turns at least 90 degrees from where it hangs to where it fires (round 4: 3 on a phone, 17 on an iPad);
 (E2) PULL: the pin rises at least 70px (phone) over its seat and never leaves the screen on the left (it slid off the edge);
 (E3) SET DOWN: the cylinder squashes on landing (its height under 97.5% of rest within a quarter second of setting down);
 (E4) SPUTTER: in the stream's last .45s its length dips at least 3 times by a quarter or more, and the score has a cough
      onset within 40ms of each spurt;
 (E5) FLOW: at least two looping layers of streaks inside the stream, each moving outward along it;
 (E6) SETTLING: billows that have hung a while sink (their mean centre moves DOWN over the second after the blast stops);
 (E7) the 100% comes clear sooner: lit by 3.3s (3.55s), the whole effect at most 5.4s (5.8s), and the cloud leaves the far
      corner of the screen as it was (the bottom-right fifth no brighter than before it, +0.02 luminance);
Sprinklers (both sizes)
 (S1) no hanging: the heads start back up within .8s of the spray stopping (round 4: 1.6s), the effect at most 5.6s (6.8s);
 (S2) the payoff on the fire going out: the 100% is lit within .35s of 90% of the flames being out, and the score's D5 chime
      starts within 60ms of it (round 4's came with the drips, two seconds later);
 (S3) steam: each plume rises at least a quarter of the fire's height and is gone within 1.4s of appearing (round 4's hung 2s);
Both
 (C1) crisp on a 3x phone: the hard-edged art (cylinder, nozzle, lever, pin, head, bulb, rain, spray) rasterised at least .95
      of its displayed size x3, the flames at least .8;
 (C2) ...and still: only transform and opacity animate, no ifx sprite carries an svg filter, at most 170 pieces on a phone,
      the tile's box alone plays and lights its 100%, nothing fully shown when the layer goes, both scores render heard and
      unclipped (peak between .02 and 1, offline, no limiter), and no page errors.
Run:  python3 tools/check-b384-extspr.py   (--against OLD/index.html must FAIL)"""
import functools, http.server, json, os, socket, sys, threading
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
AGAINST = sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else None
BODY = open(AGAINST or os.path.join(ROOT, "index.html"), encoding="utf-8").read()
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:600], flush=True)
SEED = {"onboardingComplete": True, "firstName": "Madison", "avatarChar": "ninja", "tourRev": 99, "rankMapFx244": True, "publicId": "xph5b57jbp5a", "novaMet": 99,
        "lifetime": {"points": 41000, "answered": 2100, "correct": 1980, "drillPlays": 60, "examPlays": 12, "gamePlays": 8, "perfectTests": 0, "longestStreak": 44, "currentStreak": 12}}
S = json.dumps(json.dumps(SEED))
INIT = ("Object.defineProperty(navigator,'standalone',{get:()=>true});try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');"
        "localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.daily.seen','x');localStorage.setItem('class26e.drill.v1',%s);"
        "localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));localStorage.setItem('class26e.greet.ifc','done');"
        "localStorage.setItem('class26e.weekrecap.v1','9999-12-31');localStorage.setItem('class26e.savecode.card','1');"
        "['intro.seen','unithold.tip','daily.seen','weekrecap.v1','savecode.card'].forEach(k=>localStorage.setItem('class26e.ifc.'+k, k==='weekrecap.v1'?'9999-12-31':'9'));"
        "if(!localStorage.getItem('class26e.ifc.drill.v1')) localStorage.setItem('class26e.ifc.drill.v1', %s);}catch(e){}") % (S, S)

# The page's own helpers for the gate: a stand-in results screen and card, the effect played and every animation paused, a
# seek, and the pieces by the sprite they show (the sprite functions are called here, so a redraw of a sprite is still found).
LAB = r"""() => {
  const U = u => { const m = /url\("?(.*?)"?\)\s*$/.exec(u || ''); return m ? m[1] : ''; };
  const G = window.__G = {};
  G.setup = (W, H) => {
    document.querySelectorAll('#gate').forEach(e => e.remove());
    [...document.body.children].forEach(e => { if(e.tagName !== 'SCRIPT') e.style.visibility = 'hidden'; });
    const lab = document.createElement('div'); lab.id = 'gate'; lab.style.cssText = 'visibility:visible;position:fixed;inset:0;z-index:2147480000;background:#0E1118;';
    const cw = Math.min(W - 40, 560), cx = (W - cw) / 2, cy = H < 1000 ? 171 : 150;
    const card = document.createElement('div'); card.className = 'rs-card rs-grade is-perfect';
    card.style.cssText = 'position:absolute;left:' + cx + 'px;top:' + cy + 'px;width:' + cw + 'px;height:181px;margin:0;box-sizing:border-box;padding:18px;z-index:2147480002';
    const pct = document.createElement('span'); pct.className = 'rs-pct pct perfect'; gradePctMarkup(pct, 100); card.appendChild(pct);
    lab.appendChild(card); document.body.appendChild(lab);
    new MutationObserver(ms => ms.forEach(m => m.addedNodes.forEach(n => { if(n.nodeType === 1 && n !== lab && !(n.classList && n.classList.contains('hfx-layer')) && n.tagName !== 'SCRIPT') n.style.visibility = 'hidden'; }))).observe(document.body, { childList: true });
    G.card = card; G.pct = pct; G.lab = lab;
  };
  G.roles = () => {
    const R = {}, add = (k, u) => { const x = U(u); if(x) R[x] = k; };
    const S = ifxSpr;
    add('ext', S.ext()); add('nozzle', S.nozzle()); add('lever', S.lever()); add('pin', S.pin()); add('jet', S.jet());
    [0, 1, 2].forEach(k => add('cloud', S.cloud(k)));
    [0, 1, 2, 3].forEach(k => add('flame', S.flame(k))); [0, 1, 2].forEach(k => add('rain', S.rain(k))); [0, 1].forEach(k => add('spray', S.spray(k)));
    add('head', S.head()); add('bulb', S.bulb());
    if(S.steam){ [0, 1].forEach(k => add('steam', S.steam(k))); } else add('steam', S.puff('#E8EEF2'));
    return R;
  };
  G.keyOf = url => { for(const k in hfxSprites){ const s = hfxSprites[k]; if(U(s.png) === url || U(s.svg) === url) return k; } return null; };
  G.raster = key => { const sp = hfxSprites[key]; const vb = /viewBox="([-\d.]+) ([-\d.]+) ([\d.]+) ([\d.]+)"/.exec(sp.text); const ar = vb ? (+vb[4]) / (+vb[3]) : 1;
    const W = Math.max(8, Math.round(ar > 1 ? sp.px / ar : sp.px)); return [W, Math.round(W * ar)]; };
  G.warm = id => { try{ hfxWarm(id); }catch(e){} };
  G.warmed = id => ifxWarmList(id).every(u => { const k = G.keyOf(U(u)); return !k || !!hfxSprites[k].png; });
  G.play = (id, small) => {
    if(G.h && G.h.stop) try{ G.h.stop(); }catch(e){}
    document.querySelectorAll('.hfx-layer, .hfx-dim').forEach(e => e.remove());
    let h;
    if(small){
      const st = buildHundoFxStage(id, { big: true }); st.style.width = '100%'; G.card.replaceChildren(st); G.card.style.padding = '0'; G.card.style.height = 'auto';
      h = playHundoFx(id, { box: st, pct: st.querySelector('.hfx-stage-pct'), boxOnly: true });
    } else {
      h = playHundoFx(id, { box: G.card, pct: G.pct, preview: true });
      if(h && h.screen){ h.screen.style.zIndex = 2147480001; h.screen.style.visibility = 'visible'; G.lab.appendChild(h.screen); }
    }
    if(h) clearTimeout(h.timer);
    G.h = h;
    G.anims = document.getAnimations().filter(a => { const t = a.effect && a.effect.target; return t && ((h.screen && h.screen.contains(t)) || (h.box && h.box.contains(t))); });
    G.anims.forEach(a => { try{ a.pause(); a.currentTime = 0; }catch(e){} });
    const R = G.roles();
    G.parts = {}; const all = [...(h.screen ? h.screen.querySelectorAll('*') : []), ...(h.box ? h.box.querySelectorAll('*') : [])];
    all.forEach(e => { const r = R[U(e.style.backgroundImage)]; if(r) (G.parts[r] = G.parts[r] || []).push(e); });
    return { screen: h.screen ? h.screen.querySelectorAll('*').length : 0, box: h.box ? h.box.querySelectorAll('*').length : 0,
      props: [...new Set(G.anims.flatMap(a => a.effect.getKeyframes ? a.effect.getKeyframes().flatMap(k => Object.keys(k)) : []))].filter(p => ['offset', 'computedOffset', 'easing', 'composite'].indexOf(p) < 0).sort(),
      roles: Object.fromEntries(Object.entries(G.parts).map(([k, v]) => [k, v.length])), total: IFX_DEF[id].total / 1000, tail: IFX_DEF[id].tail / 1000 };
  };
  G.seek = t => { G.anims.forEach(a => { try{ a.currentTime = t * 1000; }catch(e){} }); };
  G.op = e => { let o = 1; for(let a = e; a && a !== document.body; a = a.parentElement) o *= +getComputedStyle(a).opacity; return o; };
  G.ang = e => { const m = getComputedStyle(e).transform; if(!m || m === 'none') return 0; const v = m.slice(m.indexOf('(') + 1, -1).split(',').map(Number); return Math.atan2(v[1], v[0]) * 180 / Math.PI; };
  G.sx = e => { const m = getComputedStyle(e).transform; if(!m || m === 'none') return 1; const v = m.slice(m.indexOf('(') + 1, -1).split(',').map(Number); return Math.hypot(v[0], v[1]); };
  G.rect = e => { const r = e.getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; };
  /* the lit 100%: its CSS flash's start (seconds) */
  G.lit = () => { const l = G.h && G.h.box && G.h.box.querySelector('.hfx-lit'); return l ? parseFloat(getComputedStyle(l).animationDelay) : null; };
  /* the score, rendered offline: loudness onsets (5ms hops, a 6dB rise over the 30ms before) and a D5 band's onsets */
  G.score = async (id, f0) => {
    const buf = await NovaSound.render('hundo.' + id, { sr: 44100 }); const sr = buf.sampleRate, L = buf.getChannelData(0), R2 = buf.getChannelData(1), n = L.length, hop = Math.round(sr * .005);
    const db = []; for(let i = 0; i + hop <= n; i += hop){ let s = 0; for(let j = i; j < i + hop; j++){ const m = (L[j] + R2[j]) / 2; s += m * m; } db.push(10 * Math.log10(s / hop + 1e-12)); }
    const on = []; for(let i = 6; i < db.length; i++){ const lo = Math.min(...db.slice(i - 6, i)); if(db[i] - lo >= 6 && db[i] > -60 && (!on.length || i * .005 - on[on.length - 1] > .025)) on.push(+(i * .005).toFixed(3)); }
    /* a narrow band at f0 (Goertzel, 40ms windows every 10ms) */
    const win = Math.round(sr * .04), hp = Math.round(sr * .01), w = 2 * Math.cos(2 * Math.PI * f0 / sr), band = [];
    for(let i = 0; i + win <= n; i += hp){ let s1 = 0, s2 = 0; for(let j = 0; j < win; j++){ const x = (L[i + j] + R2[i + j]) / 2 * (.5 - .5 * Math.cos(2 * Math.PI * j / (win - 1))); const s0 = x + w * s1 - s2; s2 = s1; s1 = s0; }
      band.push(10 * Math.log10(s1 * s1 + s2 * s2 - w * s1 * s2 + 1e-12)); }
    let peak = 0; for(let i = 0; i < n; i++) peak = Math.max(peak, Math.abs(L[i]), Math.abs(R2[i]));
    return { on, band, peak };
  };
  return true;
}"""

srv_port = None
def serve():
    so = socket.socket(); so.bind(("127.0.0.1", 0)); port = so.getsockname()[1]; so.close()
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, port

def open_page(br, port, W, H):
    ctx = br.new_context(viewport={"width": W, "height": H}, device_scale_factor=1)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:300]))
    pg.add_init_script(INIT)
    pg.route("**/index.html", lambda r: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(2800)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); }")
    pg.evaluate(LAB)
    return ctx, pg, errs

def frames(pg, js, t0, t1, st):
    """js(t) evaluated after a seek to each t in [t0, t1]."""
    return pg.evaluate("""async ([t0, t1, st, body]) => { const f = eval(body); const out = []; for(let t = t0; t <= t1 + 1e-9; t = Math.round((t + st) * 1000) / 1000){ __G.seek(t); out.push([t, f(t)]); } return out; }""", [t0, t1, st, js])

def lum(pg, rect):
    """mean luminance (0-1) of a screen rect"""
    from PIL import Image, ImageStat
    import io
    b = pg.screenshot(clip={"x": rect[0], "y": rect[1], "width": rect[2], "height": rect[3]})
    return ImageStat.Stat(Image.open(io.BytesIO(b)).convert("L")).mean[0] / 255

srv, port = serve()
R = {}
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME)
    for W, H in ((440, 956), (834, 1194)):
        phone = W == 440
        ctx, pg, errs = open_page(br, port, W, H)
        cls = pg.evaluate("() => window.NOVA_CLASS")
        if cls != "ifc": chk("the page is in the Fire Code class (%s)" % cls, False); break
        for fx in ("fireworks", "underwater"):
            pg.evaluate("(id) => __G.warm(id)", fx)
            for _ in range(40):
                if pg.evaluate("(id) => __G.warmed(id)", fx): break
                pg.wait_for_timeout(150)
        pg.evaluate("([W, H]) => __G.setup(W, H)", [W, H])
        r = R[W] = {"errs": errs}
        # ---------------- the Extinguisher ----------------
        info = r["ext"] = pg.evaluate("() => __G.play('fireworks')")
        jet = "__G.parts.jet[0]"
        vis = frames(pg, "t => +getComputedStyle(%s).opacity" % jet, .2, 4.0, .01)
        on = next((t for t, o in vis if o > .5), None); end = max((t for t, o in vis if o > .05), default=None)
        r["ext_on"], r["ext_end"] = on, end
        # E1: the nozzle's turn from where it hangs to where it fires
        a_rest = frames(pg, "t => __G.ang(__G.parts.nozzle[0])", .3, .3, .1)[0][1]
        a_fire = frames(pg, "t => __G.ang(__G.parts.nozzle[0])", on + .02, on + .02, .1)[0][1]
        d = abs(a_fire - a_rest) % 360; r["aim"] = min(d, 360 - d)
        # E2: the pin's flight
        pin = frames(pg, "t => { const e = __G.parts.pin[0]; return [__G.rect(e), __G.op(e)]; }", .3, 2.2, .02)
        seat = [p for t, p in pin if t >= .44][0][0]
        live = [p[0] for t, p in pin if t >= .44 and p[1] > .1 and p[0][1] < H]
        r["pin_rise"] = round(seat[1] - min(q[1] for q in live), 1) if live else 0
        r["pin_left"] = round(min(q[0] for q in live), 1) if live else -999
        # E3: the squash as it is set down
        hts = frames(pg, "t => __G.rect(__G.parts.ext[0])[3]", .25, .75, .01)
        rest_h = frames(pg, "t => __G.rect(__G.parts.ext[0])[3]", 1.4, 1.4, .1)[0][1]
        r["squash"] = round(min(h for t, h in hts) / rest_h, 3)
        # E4: the sputter - dips in the stream's length in its last .45s, and the score's coughs on its spurts
        sx = frames(pg, "t => __G.sx(%s)" % jet, round(end - .45, 2), end, .005)
        # the spurts: the stream's length peaking again a fifth or more over the low before it
        dips, peaks, lo = 0, [], sx[0][1]
        for i in range(1, len(sx) - 1):
            v = sx[i][1]; lo = min(lo, v)
            if sx[i - 1][1] < v >= sx[i + 1][1]:
                if v - lo >= .2: peaks.append(sx[i][0])
                lo = v
        # count a dip each time the length falls a quarter or more below the last high, then rises again
        hi = sx[0][1]; low = None
        for t, v in sx:
            if low is None:
                if v <= hi - .25: low = v
                else: hi = max(hi, v)
            else:
                if v < low: low = v
                elif v >= low + .15: dips += 1; hi = v; low = None
        if low is not None: dips += 1
        r["dips"] = dips
        surge = [t for t in peaks if t > end - .4]
        sc = pg.evaluate("() => __G.score('fireworks', 587.33)")
        r["ext_onsets"] = [t for t in sc["on"] if end - .5 <= t <= end + .1]
        r["spurts"] = surge
        r["spurt_hits"] = sum(1 for t in surge if any(abs(t - o) <= .04 for o in sc["on"]))
        # E5: the flow
        r["flow"] = pg.evaluate(r"""() => { const nz = __G.parts.nozzle[0]; const jet = __G.parts.jet[0];
          return __G.anims.filter(a => { const t = a.effect.target; if(!nz.contains(t) || t === nz || t === jet) return false;
            const it = a.effect.getTiming().iterations; const k = a.effect.getKeyframes(); const tx = s => { const m = /translateX\(([-\d.]+)px\)/.exec(s || ''); return m ? +m[1] : 0; };
            return it > 1 && tx(k[k.length - 1].transform) > tx(k[0].transform); }).length; }""")
        # E6: billows that have hung a while settle
        def clouds(t):
            return frames(pg, "t => __G.parts.cloud.map(e => [__G.op(e), __G.rect(e)])", t, t, .1)[0][1]
        c0, c1, c2 = clouds(end - .8), clouds(end), clouds(end + 1.0)
        dys = [(b[1][1] + b[1][3] / 2) - (a[1][1] + a[1][3] / 2) for p, a, b in zip(c0, c1, c2) if p[0] > .3 and a[0] > .2 and b[0] > .05]
        r["settle"] = round(sum(dys) / len(dys), 1) if dys else None
        # E7: the payoff time, the length, the far corner
        r["ext_lit"] = pg.evaluate("() => __G.lit()")
        corner = [W * .8, H * .8, W * .2 - 1, H * .2 - 1]
        pg.evaluate("() => __G.seek(.05)"); l0 = lum(pg, corner)
        pg.evaluate("(t) => __G.seek(t)", on + 1.6); l1 = lum(pg, corner)
        r["corner"] = round(l1 - l0, 3)
        # the never-cut tail (C2), and the screen's pieces
        r["ext_cut"] = pg.evaluate("""(T) => { __G.seek(T - .05); return [...__G.h.screen.querySelectorAll('*')].filter(e => !e.children.length && __G.op(e) >= .98 && e.getBoundingClientRect().width > 0).length; }""", info["total"])
        # C1: crispness of the hard-edged art at 3x
        crisp_js = """(roles) => { const out = {}; roles.forEach(r => { (__G.parts[r] || []).forEach(e => { const k = __G.keyOf((/url\\("?(.*?)"?\\)\\s*$/.exec(e.style.backgroundImage) || [])[1]); if(!k) return;
          const [rw, rh] = __G.raster(k), q = Math.min(rw / (e.offsetWidth * 3), rh / (e.offsetHeight * 3)); out[r] = Math.min(out[r] == null ? 9 : out[r], +q.toFixed(3)); }); }); return out; }"""
        r["crisp_ext"] = pg.evaluate(crisp_js, ["ext", "nozzle", "lever", "pin"])
        # ---------------- the Sprinklers ----------------
        info2 = r["spr"] = pg.evaluate("() => __G.play('underwater')")
        sp = frames(pg, "t => [__G.parts.spray.map(e => __G.op(e)), __G.parts.head.map(e => __G.op(e)), __G.parts.flame.map(e => __G.op(e))]", .0, info2["total"], .02)
        spray_on = [t for t, v in sp if max(v[0]) > .05]
        spray_off = max(spray_on) if spray_on else None
        head_up = next((t for t, v in sp if spray_off and t > spray_off - 1 and t > 1.5 and min(v[1]) < .95), None)
        r["hang"] = round(head_up - spray_off, 2) if head_up and spray_off else None
        lit_flames = [t for t, v in sp if sum(1 for o in v[2] if o > .05) > .1 * len(v[2])]
        r["fire_out"] = round(max(lit_flames) + .02, 2) if lit_flames else None
        r["spr_lit"] = pg.evaluate("() => __G.lit()")
        sc2 = pg.evaluate("() => __G.score('underwater', 587.33)")
        band = sc2["band"]
        def band_onset(t):
            """the D5 band's strongest 8dB rise within .3s of t (its time) - or None"""
            best = None
            for i in range(max(5, int((t - .3) / .01)), min(len(band), int((t + .3) / .01))):
                rise = band[i] - min(band[i - 5:i])
                if rise >= 8 and (best is None or rise > best[1]): best = (round(i * .01 + .02, 3), round(rise, 1))
            return best
        r["chime"] = band_onset(r["spr_lit"]) if r["spr_lit"] is not None else None
        r["peaks"] = [sc["peak"], sc2["peak"]]
        # S3: steam
        st = frames(pg, "t => __G.parts.steam.map(e => [__G.op(e), __G.rect(e)])", .0, info2["total"], .02)
        lives, rises = [], []
        for j in range(len(st[0][1])):
            seen = [(t, v[j]) for t, v in st if v[j][0] > .05]
            if not seen: continue
            lives.append(round(seen[-1][0] - seen[0][0], 2))
            cy = [s[1][1] + s[1][3] / 2 for t, s in seen]
            rises.append(round(cy[0] - min(cy), 1))
        fh = min(H * .27, W * .62, 280)
        r["steam"] = {"n": len(lives), "life": max(lives) if lives else None, "rise": min(rises) if rises else None, "fh": round(fh, 1)}
        r["spr_cut"] = pg.evaluate("""(T) => { __G.seek(T - .05); return [...__G.h.screen.querySelectorAll('*')].filter(e => !e.children.length && __G.op(e) >= .98 && e.getBoundingClientRect().width > 0).length; }""", info2["total"])
        r["crisp_spr"] = pg.evaluate(crisp_js, ["head", "bulb", "rain", "spray", "flame"])
        if phone:
            r["filters"] = pg.evaluate("() => Object.keys(hfxSprites).filter(k => /^ifx-/.test(k) && /<filter|filter=/.test(hfxSprites[k].text || ''))")
            # the tile's box alone: plays and lights its 100%
            r["small"] = {}
            for fx in ("fireworks", "underwater"):
                si = pg.evaluate("(id) => __G.play(id, true)", fx)
                r["small"][fx] = [si["box"], pg.evaluate("() => __G.lit()")]
                pg.evaluate("([W, H]) => __G.setup(W, H)", [W, H])
        r["errs"] = list(errs)
        ctx.close()
    br.close()
srv.shutdown()
P, I = R[440], R[834]
print("phone:", json.dumps({k: v for k, v in P.items() if k not in ("errs",)}))
print("ipad: ", json.dumps({k: v for k, v in I.items() if k not in ("errs",)}))
for tag, r in (("phone", P), ("iPad", I)):
    chk("(E1 %s) AIM: the nozzle turns %.0f degrees from where it hangs to where it fires (at least 90)" % (tag, r["aim"]), r["aim"] >= 90, r["aim"])
chk("(E2) PULL: the pin rises %.0fpx over its seat (at least 70) and its left edge stays at %.0fpx (on screen)" % (P["pin_rise"], P["pin_left"]), P["pin_rise"] >= 70 and P["pin_left"] >= 0 and I["pin_left"] >= 0, (P["pin_rise"], P["pin_left"], I["pin_left"]))
chk("(E3) SET DOWN: the cylinder squashes to %.3f of its height on landing (under .975)" % P["squash"], P["squash"] < .975 and I["squash"] < .975, (P["squash"], I["squash"]))
chk("(E4) SPUTTER: the stream's length dips %d times in its last .45s (at least 3), the score coughs on %d of its %d spurts (all, at least 3)" % (P["dips"], P["spurt_hits"], len(P["spurts"])),
    P["dips"] >= 3 and len(P["spurts"]) >= 3 and P["spurt_hits"] == len(P["spurts"]), (P["dips"], P["spurts"], P["ext_onsets"]))
chk("(E5) FLOW: %d looping layers of streaks pour out along the stream (at least 2)" % P["flow"], P["flow"] >= 2, P["flow"])
chk("(E6) SETTLING: billows that have hung a while move %s px over the second after the blast (down, on both)" % [P["settle"], I["settle"]], (P["settle"] or -1) > 2 and (I["settle"] or -1) > 2, (P["settle"], I["settle"]))
chk("(E7) the 100%% lit at %.2fs (by 3.3), the effect %.1fs (at most 5.4), the far corner %+.3f brighter mid-cloud (at most +.02)" % (P["ext_lit"] or -1, P["ext"]["total"], P["corner"]),
    P["ext_lit"] is not None and P["ext_lit"] <= 3.3 and P["ext"]["total"] <= 5.4 and P["corner"] <= .02 and I["corner"] <= .02, (P["ext_lit"], P["ext"]["total"], P["corner"], I["corner"]))
for tag, r in (("phone", P), ("iPad", I)):
    chk("(S1 %s) no hanging: the heads start up %.2fs after the spray stops (at most .8), the effect %.1fs (at most 5.6)" % (tag, r["hang"] if r["hang"] is not None else -1, r["spr"]["total"]),
        r["hang"] is not None and r["hang"] <= .8 and r["spr"]["total"] <= 5.6, (r["hang"], r["spr"]["total"]))
    chk("(S2 %s) the 100%% lit at %.2fs, 90%% of the fire out at %.2fs (within .35)" % (tag, r["spr_lit"] or -1, r["fire_out"] or -1),
        r["spr_lit"] is not None and r["fire_out"] is not None and abs(r["spr_lit"] - r["fire_out"]) <= .35, (r["spr_lit"], r["fire_out"]))
chk("(S2) ...and the score's D5 chime starts with it (%s, within 60ms of %.2fs)" % (P["chime"], P["spr_lit"] or -1), P["chime"] is not None and abs(P["chime"][0] - P["spr_lit"]) <= .06, P["chime"])
for tag, r in (("phone", P), ("iPad", I)):
    s = r["steam"]
    chk("(S3 %s) steam: %d plumes, each rising at least %.0fpx (a quarter of the fire, %.0f), gone within %.2fs (at most 1.4)" % (tag, s["n"], s["rise"] or -1, s["fh"] / 4, s["life"] or -1),
        s["n"] >= 5 and s["rise"] is not None and s["rise"] >= s["fh"] / 4 and s["life"] <= 1.4, s)
hard = dict(P["crisp_ext"]); hard.update({k: v for k, v in P["crisp_spr"].items() if k != "flame"})
chk("(C1) crisp at 3x: the hard-edged art at %s of its displayed size (at least .95), the flames %.2f (at least .8)" % (hard, P["crisp_spr"].get("flame", 0)),
    hard and min(hard.values()) >= .95 and len(hard) >= 8 and P["crisp_spr"].get("flame", 0) >= .8, (hard, P["crisp_spr"]))
props = sorted(set(P["ext"]["props"]) | set(P["spr"]["props"]))
small = P["small"]
pk = P["peaks"]
chk("(C2) ...and still: only %s animate, no filters (%s), %d / %d pieces on a phone (at most 170), the tile's box plays and lights (%s), nothing fully shown as the layer goes (%s), the two scores heard and unclipped (peaks %s), no page errors (%s)" % (
    props, P["filters"], P["ext"]["screen"], P["spr"]["screen"], small, [P["ext_cut"], P["spr_cut"], I["ext_cut"], I["spr_cut"]], [round(p, 3) for p in pk], (P["errs"] + I["errs"])[:2]),
    props == ["opacity", "transform"] and not P["filters"] and P["ext"]["screen"] <= 170 and P["spr"]["screen"] <= 170 and all(v[0] >= 6 and v[1] is not None for v in small.values())
    and not (P["ext_cut"] or P["spr_cut"] or I["ext_cut"] or I["spr_cut"]) and all(.02 < p < 1 for p in pk) and not (P["errs"] + I["errs"]) and hard and min(hard.values()) >= .95,
    (props, P["filters"], small, P["ext_cut"], P["spr_cut"], pk))
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
