"""b384_desktoplag_lib.py - shared by tools/profile-desktop.py and tools/check-b384-desktoplag.py (384.30, lag on a computer).
Page-side readers (they only count; nothing here writes to the page) and the trace reader for the main thread's CPU."""
import collections

# what is running and where: every running animation, split by whether its element is in the window (a screen's height of margin
# either side counts as near: that is the budget the app gives a tile), what it animates, and how many layers' worth of effect
# the page holds (backdrop filters, filters, blend modes, big shadows, will-change)
SHAPE_JS = """()=>{
  const vh = innerHeight, vw = innerWidth, A = document.getAnimations(), run = A.filter(a => a.playState === 'running');
  let inView = 0, near = 0, far = 0, detached = 0, noTarget = 0; const byName = {}, far_names = {}, props = {};
  run.forEach(a => {
    const t = a.effect && a.effect.target; const n = a.animationName || (t && t.tagName) || '?';
    byName[n] = (byName[n] || 0) + 1;
    try{ a.effect.getKeyframes().forEach(k => Object.keys(k).forEach(p => { if(!['offset','easing','composite','computedOffset'].includes(p)) props[p] = (props[p] || 0) + 1; })); }catch(e){}
    if(!t || !t.getBoundingClientRect){ noTarget++; return; }
    if(!t.isConnected){ detached++; return; }
    const r = t.getBoundingClientRect();
    if(r.width === 0 && r.height === 0){ far++; far_names[n] = (far_names[n] || 0) + 1; return; }
    if(r.bottom > 0 && r.top < vh && r.right > 0 && r.left < vw) inView++;
    else if(r.bottom > -vh && r.top < 2 * vh) near++;
    else { far++; far_names[n] = (far_names[n] || 0) + 1; }
  });
  const fx = { backdrop: 0, filter: 0, blend: 0, bigShadow: 0, willChange: 0, backdropArea: 0 };
  const all = document.querySelectorAll('#stage *, body > *');
  all.forEach(e => {
    const c = getComputedStyle(e);
    const bf = c.backdropFilter || c.webkitBackdropFilter;
    if(bf && bf !== 'none'){ fx.backdrop++; const r = e.getBoundingClientRect(); fx.backdropArea += Math.max(0, Math.min(r.right, vw) - Math.max(r.left, 0)) * Math.max(0, Math.min(r.bottom, vh) - Math.max(r.top, 0)); }
    if(c.filter && c.filter !== 'none') fx.filter++;
    if(c.mixBlendMode && c.mixBlendMode !== 'normal') fx.blend++;
    if(c.willChange && c.willChange !== 'auto') fx.willChange++;
    const m = (c.boxShadow || '').match(/(\\d+(?:\\.\\d+)?)px\\s+(\\d+(?:\\.\\d+)?)px\\s+(\\d+(?:\\.\\d+)?)px/g);
    if(m && m.some(s => parseFloat(s.split(/\\s+/)[2]) >= 20)) fx.bigShadow++;
  });
  fx.backdropArea = Math.round(fx.backdropArea / (vw * vh) * 100) / 100;
  return { running: run.length, all: A.length, inView, near, far, detached, noTarget, byName, far_names, props, fx, els: document.getElementsByTagName('*').length, vw, vh };
}"""


def thread_cpu(evs, thr=1.0):
    """main-thread CPU in ms (thread time of its tasks, in 1x-equivalent ms) and the number of tasks, from a CDP trace"""
    names = {}
    for e in evs:
        if e.get("name") == "thread_name": names[(e["pid"], e["tid"])] = e["args"]["name"]
    tasks = [e for e in evs if e.get("ph") == "X" and e.get("name") == "RunTask" and names.get((e.get("pid"), e.get("tid"))) == "CrRendererMain"]
    return sum(e.get("tdur", e["dur"]) / 1000.0 / thr for e in tasks), len(tasks)


def count_events(evs, name):
    return sum(1 for e in evs if e.get("name") == name)


# what a recorded frame costs the main thread, read off a trace: the isolated SVG document made and parsed for the frame's data: URL, the image's
# resource request and update, the canvas draw. Several nest (the load contains the request), so only the OUTERMOST event of a run counts.
REC_EVENTS = ("IsolatedSVGDocumentHost::IsolatedSVGDocumentHost::load", "IsolatedSVGDocumentHost::IsolatedSVGDocumentHost::createFrame", "SVGImage::DataChanged",
              "ResourceFetcher::requestResource", "ImageResourceContent::updateImage", "CanvasRenderingContext2D::FinalizeFrame")


def recorder_cost(evs, thr=1.0):
    """(ms of main-thread time in the recorders' own events, frames loaded)"""
    names = {}
    for e in evs:
        if e.get("name") == "thread_name": names[(e["pid"], e["tid"])] = e["args"]["name"]
    ev = sorted((e for e in evs if e.get("ph") == "X" and e.get("name") in REC_EVENTS and names.get((e.get("pid"), e.get("tid"))) == "CrRendererMain"), key=lambda e: (e["ts"], -e["dur"]))
    total, end = 0.0, -1
    for e in ev:
        if e["ts"] >= end:
            total += e["dur"]; end = e["ts"] + e["dur"]
        elif e["ts"] + e["dur"] > end:
            total += e["ts"] + e["dur"] - end; end = e["ts"] + e["dur"]
    n = sum(1 for e in ev if e["name"] == "IsolatedSVGDocumentHost::IsolatedSVGDocumentHost::load")
    return total / 1000.0 / thr, n
