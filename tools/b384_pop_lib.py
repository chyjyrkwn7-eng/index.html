"""Shared by check-b384-popglass.py: every pop-up in the app, opened for real by the app's own function.

INVENTORY lists each pop-up as (key, opener JS, sheet selector, kind, background screen). `kind`:
  confirm  - a question with two buttons over a dim; its overlay is the scrim; its title is the confirm family's
  card     - a centred card (person, unlock, What's new, a note...)
  sheet    - a bottom / list sheet
Anything not in here is either a full-screen takeover (cutscenes, loading, the update screen), a screen of its own (Pause,
Quit this test: panels in #stage), or a deliberately opaque popover (.under-note, .hundo-why: their arrow takes the body's
fill - see their CSS); the gate says which.
"""
import importlib.util, os

HERE = os.path.dirname(os.path.abspath(__file__))


def load_cb(against=None):
    spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py"))
    cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
    if against:
        OLD = open(against, encoding="utf-8").read(); IR = cb.INSET_RE
        cb.patched = lambda ins: IR.sub(lambda m: {"top": "%dpx" % ins[0], "right": "%dpx" % ins[1], "bottom": "%dpx" % ins[2], "left": "%dpx" % ins[3]}[m.group(1)], OLD)
    return cb


# an account in both classes (the second class needs a publicId and the list)
BOTH = ('{"firstName":"Lev","avatarChar":"ninja","onboardingComplete":true,"publicId":"bo0000000001","classes":["academy","ifc"],'
        '"leaderboardOptIn":true,"lastModified":1700000000000,"seenProfileTour":true,"tourRev":99,"rankMapFx244":true,'
        '"testHistory":[{"ts":1700000000000,"mode":"exam","label":"Practice test","score":92,"total":25,"correct":23,"units":["1"],"answers":[]}],'
        '"lifetime":{"points":14820,"answered":5400,"correct":4980,"drillPlays":64,"examPlays":22,"gamePlays":9,"perfectTests":141,"currentStreak":23,"longestStreak":57},'
        '"unlocksShown":{"chars":[],"banners":["hundos100"],"fx":["fireworks","blackhole","underwater","worldtree","bubbles","ufo"]}}')
SEEN_IFC = ("['class26e.ifc.freshstart','class26e.ifc.daily.seen','class26e.ifc.savecode.card','class26e.ifc.savecode.asked','class26e.ifc.getstarted',"
            "'class26e.ifc.a2hs','class26e.ifc.unithold.tip'].forEach(k=>localStorage.setItem(k,'1'));")

BGS = {
    "settings": "showAppearance()",
    "leaderboard": "showRankings()",
    "profile": "showProfile('profile')",
}

_LEAVE = ("showClassEnrollConfirm('Police Academy','',()=>{},{title:'Leave Police Academy?',body:'Police Academy comes off your classes and its "
          "leaderboard. Your progress in it is kept: join again any time and it\\u2019s all there. Nova opens Fire Code.',yes:'Leave Police Academy',back:'Cancel',danger:true})")
INVENTORY = [
    ("class-leave", _LEAVE, ".savecode-sheet", "confirm", "settings"),
    ("class-only", "showClassEnrollConfirm('Police Academy','',()=>{},{title:'Police Academy is your only class',body:'You need at least one class. To leave Police Academy, join another class first.',yes:'Join another class',back:'OK'})", ".savecode-sheet", "confirm", "settings"),
    ("class-enroll", "showClassEnrollConfirm('Fire Code','Fire Code Inspector',()=>{},{})", ".savecode-sheet", "confirm", "settings"),
    ("new-account", "showNewAccountConfirm()", ".savecode-sheet", "confirm", "settings"),
    ("sign-out", "showSignOutConfirm()", ".savecode-sheet", "confirm", "settings"),
    ("save-code", "syncCode = syncCode || 'TEST-0000-0000'; showSaveCodeCard({mode:'new'})", ".savecode-sheet", "confirm", "settings"),
    ("vroom-leave", "inVirtualRoom = true; confirmLeaveTeamMatch()", ".chatdock-confirm-card", "confirm", "leaderboard"),
    ("chat-leave", "confirmLeaveChat('TESTROOM', ()=>{})", ".chat-leavesheet-group", "sheet", "leaderboard"),
    ("resume-offer", "showRunOffer({cfg:{units:['Ethics'],versions:{}},order:[1,2,3,4,5,6,7,8,9,10],pos:4,runMode:'drill'},'start')", ".resume-card", "confirm", "leaderboard"),
    ("saved-test-dropped", "showSavedTestDropped()", ".resume-card", "confirm", "leaderboard"),
    ("friend-moment", "celebrateNewFriend('bo0000000042')", ".friend-moment-card", "card", "leaderboard"),
    ("a2hs", "showHomeScreenSheet({from:'signup'})", ".a2hs-sheet", "card", "settings"),
    ("whats-new", "showIntroPopup({})", ".intro-card", "card", "settings"),
    ("person", "openPersonSheet({pub:'bo0000000000',firstName:'Lev',avatarChar:'hacker',level:60,badges:7,hundos:78,xp:144000,correct:10563,banner:''})", ".invite-sheet.person-card", "card", "leaderboard"),
    ("unlock", "showUnlockDetail(characterDetail('poseidon'))", ".invite-sheet.unlock-card", "card", "profile"),
    ("rank-lore", "showRankLore('adept')", ".invite-sheet.ranklore-card", "card", "profile"),
    ("level-coming", "showLevelComingSheet(60)", ".invite-sheet.level-coming-sheet", "card", "profile"),
    ("install-picker", "showInstallPlatformPicker()", ".installguide-card", "card", "settings"),
    ("install-guide", "showInstallGuide('ios')", ".installguide-card", "card", "settings"),
    ("invite-chat", "chatRoomCode='TESTROOM'; openChatInviteSheet()", ".invite-overlay > .invite-sheet", "sheet", "leaderboard"),
    ("invite-friends", "openInviteFriendsSheet('TESTROOM')", ".invite-overlay > .invite-sheet", "sheet", "leaderboard"),
    ("chat-members", "openChatMembers()", ".invite-overlay.chat-members > .invite-sheet", "sheet", "leaderboard"),
]


def boot(br, cb, w, h, cls="academy", dpr=3):
    init = None
    if cls == "ifc":
        init = "try{localStorage.setItem('class26e.activeclass','ifc');" + SEEN_IFC + "}catch(e){}"
    ctx, pg = cb.booted(br, w, h, seed=BOTH, init=init, touch=True, dpr=dpr)
    pg.evaluate("document.querySelectorAll('#splashscreen').forEach(n=>n.remove())")
    return ctx, pg
