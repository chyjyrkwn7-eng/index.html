#!/usr/bin/env python3
"""Build 325 gate: the Penal Code slides 256-578 version and two re-keyed answers.

1. Before 8:00 PM Central on Mon Oct 19 the Penal Code short version is slides
   124-256 (116 questions); from 8:00 PM it is slides 256-578 (132), with the
   seven version-only entries 358-364 in it and none of them in the whole unit,
   which stays 340. Every src in the table names exactly one Penal question.
2. The "Penal Code updated" note's seen-key follows the live range.
3. The daily question never deals a version-only question (pools unchanged).
4. Arrest, Search and Seizure #31 keys the same choice as its twin #55, and
   Sexual Assault #30 the same as Penal Code #243.
5. Monday's and the next Monday's tests have their topics posted.

Run `--against /tmp/claude-0/wbase325/index.html` (6fc16b7): 9 of 13 fail there. The four that
pass hold what must STAY (124-256 before 8 PM, the whole unit, one question per
src, no version-only daily question) rather than show the change.
"""
import sys, os, datetime, subprocess, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
target = os.path.join(ROOT, "index.html")
if "--against" in sys.argv:
    target = os.path.abspath(sys.argv[sys.argv.index("--against") + 1])

from playwright.sync_api import sync_playwright

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
fails = 0
def check(name, ok, detail=""):
    global fails
    print(("  PASS " if ok else "  FAIL ") + name + ("" if ok else "  -> " + str(detail)[:200]))
    if not ok: fails += 1

STATE = """() => {
  const v = UNIT_TEST_VERSIONS['Penal Code'];
  const bySrc = {}; QUESTIONS.forEach(q => { if(q.topic === 'Penal Code') bySrc[q.src] = (bySrc[q.src] || 0) + 1; });
  const verIds = QUESTIONS.map((q, i) => i).filter(i => QUESTIONS[i].topic === 'Penal Code' && inChosenVersion(i, {'Penal Code': 'test'}));
  return {
    label: v ? v.label : null,
    n: unitVersionCount('Penal Code', 'test'),
    whole: unitVersionCount('Penal Code', null),
    bad: v ? [...v.srcs].filter(s => bySrc[s] !== 1) : ['no version'],
    newIn: verIds.filter(i => QUESTIONS[i].src >= 358).map(i => QUESTIONS[i].src).sort((a, b) => a - b),
    newWhole: QUESTIONS.filter(q => q.topic === 'Penal Code' && q.src >= 358 && inWholeUnit(q)).length,
    key: typeof penalVersionNoteKey === 'function' ? penalVersionNoteKey() : null,
  };
}"""

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    def page_at(when):
        ctx = b.new_context(viewport={"width": 440, "height": 956})
        pg = ctx.new_page()
        pg.clock.install(time=datetime.datetime.fromisoformat(when))
        pg.goto("file://" + target); pg.wait_for_timeout(1500)
        return ctx, pg

    print("\n325pc. Penal Code slides 256-578 from 8 PM Monday Oct 19 (Central)")
    ctx, pg = page_at("2026-10-19T19:59:30-05:00"); pre = pg.evaluate(STATE); ctx.close()
    ctx, pg = page_at("2026-10-19T20:00:05-05:00"); post = pg.evaluate(STATE)
    check("at 7:59 PM the version is slides 124-256, 116 questions", pre["n"] == 116 and "124" in (pre["label"] or "") and "256" in (pre["label"] or ""), pre)
    check("at 8:00 PM the version is slides 256-578, 132 questions", post["n"] == 132 and "578" in (post["label"] or ""), post)
    check("358-364 are all in the 256-578 version", post["newIn"] == list(range(358, 365)), post["newIn"])
    check("none of 358-364 is in the whole unit, which stays 340", post["newWhole"] == 0 and post["whole"] == 340 and pre["whole"] == 340, post)
    check("every src in both tables names exactly one Penal Code question", pre["bad"] == [] and post["bad"] == [], [pre["bad"][:5], post["bad"][:5]])
    check("the updated-note key follows the live range", pre["key"] == "class26e.penal124256.seen" and post["key"] == "class26e.penal256578.seen", [pre["key"], post["key"]])

    print("\n325pc. the daily question never deals a version-only question")
    r = pg.evaluate("""() => {
      const out = []; const d0 = new Date(2026, 9, 18, 12);
      for(let k = 0; k < 400; k++){ const d = new Date(d0.getTime() + k * 86400000);
        const key = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
        const q = QUESTIONS[dailyQuestionIndexFor(key)]; if(q.versionOnly) out.push(key + ':' + q.src); }
      return out; }""")
    check("400 days of daily questions, none version-only", r == [], r[:5])
    # the guard must exist, not merely be lucky: a version-only question with no repeatOf is in the bank
    lone = pg.evaluate("() => QUESTIONS.filter(q => q.versionOnly && q.repeatOf == null).length")
    check("version-only questions with no repeatOf exist (the guard is what keeps them out)", lone >= 4, lone)

    print("\n325pc. one question, one answer")
    ans = pg.evaluate("""() => { const f = (t, s) => QUESTIONS.find(q => q.topic === t && q.src === s && q.repeatOf == null);
      const a31 = f('Arrest, Search, and Seizure', 31), a55 = f('Arrest, Search, and Seizure', 55),
            s30 = f('Sexual Assault and Family Violence', 30), p243 = f('Penal Code', 243);
      return { a31: a31.choices[a31.answer], a55: a55.choices[a55.answer], s30: s30.choices[s30.answer], p243: p243.choices[p243.answer] }; }""")
    check("Arrest, Search and Seizure #31 keys what #55 keys (mere acquiescence)", ans["a31"] == ans["a55"] and "acquiescence" in ans["a31"], ans)
    check("Sexual Assault #30 keys what Penal Code #243 keys (Terroristic Threat)", ans["s30"] == ans["p243"] == "Terroristic Threat", ans)

    print("\n325pc. the next two tests' topics are posted")
    tp = pg.evaluate("() => [testTopicsFor('2026-10-19'), testTopicsFor('2026-10-26')]")
    check("Oct 19 is Penal Code slides 124-256", bool(tp[0]) and any("124" in t and "256" in t for t in tp[0]["topics"]), tp[0])
    check("Oct 26 is Penal Code slides 256-578", bool(tp[1]) and any("256" in t and "578" in t for t in tp[1]["topics"]), tp[1])
    ctx.close(); b.close()

print("\nALL PASS" if not fails else "\n%d FAILURE(S)" % fails)
sys.exit(1 if fails else 0)
