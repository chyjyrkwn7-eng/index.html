"""Build 384.133: the Toxic Spill (Fire Code's `astronaut`, kind fcspill) with 384.113's closed-eye work taken out, so the old "byte for byte"
checks of the character-art gates (check-b384-r5-chars, r8-eyes, r9-chars) can keep holding everything ELSE of its drawing exact.

Why: 384.113 (closedeyes; Madison, on a classmate's card: "His eyes close just look missing. Fix that.") put each of the Spill's three eyes in its own
`cx-eyeball` group (so each blinks about its own middle) and redrew its CLOSED eyes as lids (a disc of the ooze's gradient, a rim, a gloss, a lash line) in
`.cx-eyes-closed`. That is the only difference from the drawing r5 / r8 / r9 pinned (c1d224b / cd34de2 / cd82880): read off the SVG, main 384.107 and this
build differ in nothing else. The three gates therefore compare the Spill by SPILL_NORM: the drawing with `.cx-eyes-closed` removed and the `cx-eyeball`
groups unwrapped (their children left where they were), hashed as the gates hash a drawing. The pins ("spillNorm" in each gate's .prev.json) are written by
tools/pin-b384-spillnorm.py from the three reference commits. check-b384-closedeyes.py holds the closed eyes themselves."""

SPILL_NORM = r"""() => {
  document.getElementById('splashscreen')?.remove();
  const hash = s => { let h = 2166136261; for(let i = 0; i < s.length; i++){ h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0).toString(16); };
  let s; try{ s = drawAvatarCharSVG('astronaut'); }catch(e){ return 'ERR ' + e.message; }
  if(!s) return 'none';
  s.setAttribute('width', 340); s.setAttribute('height', 340);
  const uid = s.getAttribute('data-cx-uid');
  const c = s.cloneNode(true);
  c.querySelectorAll('.cx-eyes-closed').forEach(e => e.remove());
  c.querySelectorAll('.cx-eyeball').forEach(g => { while(g.firstChild) g.parentNode.insertBefore(g.firstChild, g); g.remove(); });
  return hash(new XMLSerializer().serializeToString(c).split(uid).join('U'));
}"""
