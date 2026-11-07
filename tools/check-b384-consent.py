"""Build 384: the two "Consent is considered involuntary ..." questions (Arrest, Search, and Seizure #31 and #55) both count
"Revoked by the person granting consent", and neither carries the "An admin is confirming this answer" note.
Madison: "Arrest search and seizure duplicate questions, the answer is revoked, remove the warning ... make the answer for
both woukd be the 'revoked by the person granting consent'".
Read off the page (the academy):
(1) both questions' answer is the choice "Revoked by the person granting consent";
(2) no question in the bank has a verifyNote (the red note under the answer) - those two were the only ones;
(3) their identity is unchanged: each question's key (KEYS, from topic/src/text/choices) is the same as on the build before,
    so everyone's history on them carries over; and the bank's size and every other answer are unchanged;
(4) the answer screen for #55 answered "Revoked" marks it right, with no note under it; no page errors.
Run:  python3 tools/check-b384-consent.py   (--against: copy the old index.html over first, as check-b382-board)"""
import os, sys, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
_s = open(HERE + "/check-b382-board.py").read()
G = {"__file__": HERE + "/check-b382-board.py", "__name__": "b384cons"}
exec(_s[:_s.index("\nwith sync_playwright() as pw:")], G)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:500], flush=True)
READ = """()=>{ const qs = QUESTIONS.map((q,i)=>[q,i]).filter(([q])=>/^Consent is considered involuntary/.test(q.q||''));
  return { two: qs.map(([q,i])=>({ src:q.src, ans:q.choices[q.answer], note:q.verifyNote||null, key:KEYS[i] })),
    notes: QUESTIONS.filter(q=>q.verifyNote).length, n: QUESTIONS.length,
    others: QUESTIONS.filter(q=>!/^Consent is considered involuntary/.test(q.q||'')).map(q=>q.answer).join('') }; }"""
def read(html_path=None):
    with sync_playwright() as pw:
        br, ctx, pg = G["load"](pw, "promax")
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        r = pg.evaluate(READ)
        # (4) the answer screen: #55 drilled and answered "Revoked"
        shot = pg.evaluate("""async ()=>{ const i = QUESTIONS.findIndex(q=>/^Consent is considered involuntary/.test(q.q||'') && q.src===55);
          cfg.mode='drill'; cfg.units=[QUESTIONS[i].topic]; cfg.source='all'; beginRun([i], null, null);
          for(let k=0;k<40 && !document.querySelector('#stage .choice');k++) await new Promise(r=>setTimeout(r,250));
          await new Promise(r=>setTimeout(r,600)); const all=[...document.querySelectorAll('#stage .choice')]; const oo=optionOrder(i);
          const pick = all[oo.indexOf(QUESTIONS[i].choices.indexOf('Revoked by the person granting consent'))]; if(pick) pick.click();
          await new Promise(r=>setTimeout(r,1300));
          return { right: !!document.querySelector('#stage .choice.is-right, #stage .choice.correct') && !document.querySelector('#stage .choice.is-wrong, #stage .choice.wrong'),
                   note: /admin is confirming/i.test(document.getElementById('stage').textContent) }; }""")
        br.close()
        return r, shot, errs
r, shot, errs = read()
# the build before, for identity
SP = os.environ.get("OLD_HTML")
old = None
if SP and os.path.exists(SP):
    cur = open(os.path.join(os.path.dirname(HERE), "index.html"), encoding="utf-8").read()
    try:
        open(os.path.join(os.path.dirname(HERE), "index.html"), "w", encoding="utf-8").write(open(SP, encoding="utf-8").read())
        old, _, _ = read()
    finally:
        open(os.path.join(os.path.dirname(HERE), "index.html"), "w", encoding="utf-8").write(cur)
REV = "Revoked by the person granting consent"
chk("(1) both consent questions count '%s' (%s)" % (REV, [(q["src"], q["ans"]) for q in r["two"]]), len(r["two"]) == 2 and all(q["ans"] == REV for q in r["two"]), r["two"])
chk("(2) no question carries an 'admin is confirming' note (%d)" % r["notes"], r["notes"] == 0, r["notes"])
if old:
    same_keys = [q["key"] for q in r["two"]] == [q["key"] for q in old["two"]]
    chk("(3) their keys are the build before's (%s), the bank's size (%d) and every other answer unchanged" % ([q["key"] for q in r["two"]], r["n"]),
        same_keys and r["n"] == old["n"] and r["others"] == old["others"], {"now": r["two"], "old": old["two"], "n": [r["n"], old["n"]]})
else:
    print("(3) skipped: set OLD_HTML to the build before's index.html to compare keys")
chk("(4) #55 answered 'Revoked' is marked right, with no note under it (%s); no page errors (%s)" % (shot, errs[:2]), shot["right"] and not shot["note"] and not errs, [shot, errs])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
