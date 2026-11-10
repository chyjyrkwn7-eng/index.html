"""Shared by tools/check-b384-classleave.py and tools/record-b384-leave.py: drive the REAL "leave a class" flow (Settings > Manage
classes > a class > the red button > the final confirm) for an account that is in both classes, in either class, and watch it.

It rides on tools/b384_switchfx_lib.py (the class switch's harness: the page served as GitHub Pages serves it, an in-memory Firestore
kept in the tab's sessionStorage so a reload sees it, a persistent profile on disk, the owner's account in both classes) and adds an
in-page witness that survives the reloads, kept in sessionStorage like the switch's own log:

  * every page load (which class the page is, and when), so "one reload at most" is a count;
  * every layout shift (PerformanceObserver "layout-shift") with how much of a cover was over the page at that moment, so a shift
    the person cannot see (under the cover) is told from one they can;
  * every long task (PerformanceObserver "longtask"), and every time Home is mounted into the stage (Home built twice).

Works against any index.html (`--against` in the gate): a build with one confirm is driven through its one, a build with two through
both - the driver clicks the red button and, if another sheet comes up, its red button too.
"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b384_switchfx_lib as L

WITNESS = r"""(()=>{ if(location.protocol !== 'http:') return;
  let log = []; try{ log = JSON.parse(sessionStorage.getItem('__lv') || '[]'); }catch(e){}
  window.__lv = log;
  const push = o => { o.t = Date.now(); try{ log.push(o); }catch(e){} };
  const cover = () => {
    // how much of a cover is over the page: the switch's loader or the splash, whichever is more opaque (0 when neither is up)
    let m = 0;
    for(const id of ['class-switch-loader', 'splashscreen']){
      const e = document.getElementById(id); if(!e) continue;
      const c = getComputedStyle(e); if(c.display === 'none' || c.visibility === 'hidden') continue;
      m = Math.max(m, +(+c.opacity).toFixed(2));
    }
    return m;
  };
  push({ k: 'load', cls: window.NOVA_CLASS || null, cover: cover() });
  try{ new PerformanceObserver(l => { for(const e of l.getEntries()){
    push({ k: 'ls', v: +e.value.toFixed(4), cover: cover(), input: !!e.hadRecentInput, st: Math.round(e.startTime),
      src: (e.sources || []).slice(0, 3).map(s => { const n = s.node; return n ? (n.id ? '#' + n.id : (n.className && String(n.className).split(' ')[0] ? '.' + String(n.className).split(' ')[0] : n.nodeName)) : '?'; }) });
  } }).observe({ type: 'layout-shift', buffered: true }); }catch(e){}
  try{ new PerformanceObserver(l => { for(const e of l.getEntries()) push({ k: 'lt', d: Math.round(e.duration), st: Math.round(e.startTime), cover: cover() }); }).observe({ type: 'longtask', buffered: true }); }catch(e){}
  // the cover (the switch's loader) going up, and the splash going away
  new MutationObserver(ms => { for(const m of ms){
    for(const n of m.addedNodes) if(n.id === 'class-switch-loader') push({ k: 'cover' });
    for(const n of m.removedNodes) if(n.id === 'splashscreen') push({ k: 'splashgone' });
    for(const n of m.addedNodes) if(n.id === 'toast') push({ k: 'toast', text: (n.textContent || '').trim() });
  } }).observe(document, { subtree: true, childList: true });
  const hook = () => {
    const st = document.getElementById('stage'); if(!st) return false;
    new MutationObserver(ms => { for(const m of ms) for(const n of m.addedNodes){
      if(n.nodeType === 1 && n.matches && n.matches('[data-screen="home"]')) push({ k: 'home', cls: window.NOVA_CLASS || null, cover: cover() });
      if(n.nodeType === 1 && n.matches && n.matches('.settings-page-classes')) push({ k: 'classespage', cover: cover() });
    } }).observe(st, { childList: true });
    return true;
  };
  if(!hook()){ const iv = setInterval(() => { if(hook()) clearInterval(iv); }, 5); }
  addEventListener('pagehide', () => { try{ sessionStorage.setItem('__lv', JSON.stringify(log.slice(-1500))); }catch(e){} });
})();"""

STATE = """()=>{ const g = f => { try{ return f(); }catch(e){ return null; } };
  return { cls: window.NOVA_CLASS, enrolled: g(() => enrolledClasses()), stage: g(() => store.classes), left: g(() => store.classLeftAt), joined: g(() => store.classJoinedAt),
    home: !!document.querySelector('#stage [data-screen="home"]'), splash: !!document.getElementById('splashscreen'), cover: !!document.getElementById('class-switch-loader'),
    bubble: [...document.querySelectorAll('.class-stack-item')].filter(b => !b.classList.contains('is-add')).map(b => b.className.replace('class-stack-item ', '').replace('is-', '')),
    cloud: g(() => { const p = (window.__cloud || {}).progress || {}; const a = p['TEST-SWCH'] || {}; return { classes: a.classes || null, left: a.classLeftAt || null, joined: a.classJoinedAt || null }; }) }; }"""

def cloud_now(pg):
    """what the in-memory cloud holds for the account right now (it lives in the tab's sessionStorage, so any page can read it)"""
    return L.ev(pg, "()=>{ try{ const c = JSON.parse(sessionStorage.getItem('__fakecloud') || 'null') || {}; const a = (c.progress || {})['TEST-SWCH'] || {}; "
                    "return { classes: a.classes || null, left: a.classLeftAt || null, joined: a.classJoinedAt || null, lb: Object.keys(c.leaderboard || {}) }; }catch(e){ return null; } }")

class Leave:
    """one device, the account in both classes, parked on Home of `start` (the class the person is in)"""
    def __init__(self, pw, server, start="academy", dev="phone", cpu=1):
        self.pw, self.server, self.start, self.dev, self.cpu = pw, server, start, dev, cpu
        self.S = L.Session(pw, server, dev, extra_init=WITNESS)
        self.pg = self.S.pg
    def boot(self):
        S = self.S
        S.boot()
        if self.start == "ifc":
            S.switch("ifc"); S.pg.wait_for_timeout(2200)
            self.quiet()
        return self
    def quiet(self):
        L.ev(self.pg, "()=>{ document.getElementById('splashscreen')?.remove(); document.querySelectorAll('.daily-alert,.app-banner,#classback-banner,.rs-spot').forEach(e=>e.remove()); }")
        self.pg.wait_for_timeout(600)
    def state(self): return L.ev(self.pg, STATE)
    def open_classes(self):
        """Settings > Classes, by the menu row a person taps"""
        L.ev(self.pg, "()=>showAppearance()"); self.pg.wait_for_timeout(1400)
        self.S.tap("#settings-row-classes"); self.pg.wait_for_timeout(900)
    def sheet(self):
        return L.ev(self.pg, "()=>{ const e = document.getElementById('classenroll-confirm'); if(!e) return null; return { title: (e.querySelector('h2')||{}).textContent, body: (e.querySelector('p')||{}).textContent, "
                             "yes: (e.querySelector('.classenroll-yes')||{}).textContent, danger: !!e.querySelector('.classenroll-yes.danger'), back: (e.querySelector('.classenroll-back')||{}).textContent, shown: e.classList.contains('show') }; }")
    def tap_row(self, k):
        self.S.tap('.settings-class-row[data-cls="%s"]' % k); self.pg.wait_for_timeout(700)
    def press(self, which):
        """the sheet's red button ('yes') or Cancel ('back'): a real tap; returns the wall-clock time of the tap"""
        t = self.S.tap("#classenroll-confirm .classenroll-" + which); self.pg.wait_for_timeout(500); return t
    def leave(self, k, stages=2, throttle=True):
        """the whole flow from the Classes page: the row, then the red button of each sheet that comes up (at most `stages`: a build with
        one confirm leaves at the first). -> (wall-clock time of the last tap, the sheets seen)"""
        self.open_classes()
        L.ev(self.pg, "()=>{ sessionStorage.removeItem('__lv'); window.__lv.length = 0; }")
        if throttle and self.cpu != 1: self.S.throttle(self.cpu)
        self.tap_row(k)
        sheets = []; t = None
        for i in range(stages):
            sh = self.sheet()
            if not sh: break
            sheets.append(sh)
            t = self.press("yes")
        return t, sheets
    def wait_settled(self, t0, want_cls, limit=40):
        """until `want_cls`'s Home is up, its splash and cover gone, and it has stayed so for 1.2s -> seconds from t0 (or None)"""
        pg = self.pg; ok_at = None
        while time.time() - t0 < limit:
            st = L.ev(pg, "()=>({ cls: window.NOVA_CLASS, home: !!document.querySelector('#stage [data-screen=\"home\"]'), sp: !!document.getElementById('splashscreen'), cv: !!document.getElementById('class-switch-loader') })")
            if st and st["cls"] == want_cls and st["home"] and not st["sp"] and not st["cv"]:
                ok_at = ok_at or time.time()
                if time.time() - ok_at > 1.2: return ok_at - t0
            else: ok_at = None
            pg.wait_for_timeout(100)
        return None
    def log(self):
        return L.ev(self.pg, "()=>window.__lv.slice()", default=[]) or []
    def close(self):
        self.S.close()

def summarise(log, t_tap):
    """the witness's log as numbers. t_tap: wall-clock seconds of the final tap."""
    t0 = t_tap * 1000
    loads = [e for e in log if e["k"] == "load" and e["t"] >= t0 - 200]
    ls = [e for e in log if e["k"] == "ls" and e["t"] >= t0 - 50]
    lt = [e for e in log if e["k"] == "lt" and e["t"] >= t0 - 50]
    homes = [e for e in log if e["k"] == "home" and e["t"] >= t0 - 50]
    cover = next((e["t"] - t0 for e in log if e["k"] == "cover" and e["t"] >= t0 - 50), None)
    reload1 = loads[0]["t"] - t0 if loads else None
    gone = next((e["t"] - t0 for e in log if e["k"] == "splashgone" and e["t"] >= t0 - 50), None)
    seen = [e for e in ls if e["cover"] < .5]                 # a shift with the cover mostly away: the person sees it
    return {
        "loads": len(loads), "load_classes": [e["cls"] for e in loads],
        "shift_all": round(sum(e["v"] for e in ls), 4), "shift_seen": round(sum(e["v"] for e in seen), 4),
        "shift_seen_n": len(seen), "shift_seen_src": sorted({s for e in seen for s in e["src"]})[:8],
        "longest_task": max([e["d"] for e in lt] or [0]), "tasks": len(lt), "tasks_uncovered": [e["d"] for e in lt if e["cover"] < .5],
        "homes": len(homes), "home_classes": [e["cls"] for e in homes], "covers": len([e for e in log if e["k"] == "cover" and e["t"] >= t0 - 50]),
        "splash_gones": len([e for e in log if e["k"] == "splashgone" and e["t"] >= t0 - 50]), "toasts": [e["text"] for e in log if e["k"] == "toast" and e["t"] >= t0 - 50],
        "cover_at": None if cover is None else round(cover), "first_reload_at": None if reload1 is None else round(reload1), "splash_gone_at": None if gone is None else round(gone),
    }
