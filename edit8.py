import sys
p = sys.argv[1] + '/models/causal_kernel/attacks.py'
s = open(p).read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a, s.count(a))
    s = s.replace(a, b)
rep('''    hostile = [gm, md, pm, An, WN.answer("x2", "m2", "p", "act"), WN.answer("x3", "m3", "p", "act"), WN.receipt("r", "m2", "p", 0), WN.landing("L", "m2", "p", "r", "fallback", Wm, ("x2", "x3"))]
    s1 = ST.offer("s1", "m2", "S1", "member", "g", "group", ("g", "p", "s1c"), head=("g",), policy="community_invite", content="s1", cosigners=("S1",))
    s2 = ST.offer("s2", "m2", "S2", "member", "g", "group", ("s1", "s2c", "s2d"), head=("s1",), policy="community_invite", content="s2", cosigners=("S2",))
    cps = [ST.cosign("s1c", "m3", "s1", ("g", "p")), s1, ST.cosign("s2c", "m3", "s2", ("s1",)), ST.cosign("s2d", "S1", "s2", ("s1",)), s2]''',
'''    # four members (m1, m2, m3 and MOD): the fallback takes three acts, and the two counted rows are counted over the appointment
    hostile = [gm, am, md, pm, An, WN.answer("x1", "m1", "p", "act"), WN.answer("x2", "m2", "p", "act"), WN.answer("x3", "m3", "p", "act"),
               WN.receipt("r", "m2", "p", 0), WN.landing("L", "m2", "p", "r", "fallback", Wm, ("x1", "x2", "x3"))]
    s1 = ST.offer("s1", "m2", "S1", "member", "g", "group", ("md", "p", "s1b", "s1c"), head=("md",), policy="community_invite", content="s1", cosigners=("S1",))
    s2 = ST.offer("s2", "m2", "S2", "member", "g", "group", ("s1", "s2b", "s2c", "s2d"), head=("s1",), policy="community_invite", content="s2", cosigners=("S2",))
    cps = [ST.cosign("s1b", "m1", "s1", ("md", "p")), ST.cosign("s1c", "m3", "s1", ("md", "p")), s1,
           ST.cosign("s2b", "m1", "s2", ("s1",)), ST.cosign("s2c", "m3", "s2", ("s1",)), ST.cosign("s2d", "S1", "s2", ("s1",)), s2]''')
rep('''"AND FOR WINDOWS. Two hostile members of three land''', '''"AND FOR WINDOWS. Three hostile members of four land''')
rep('''    rows = [gm, am, md, WN.opener("p", "m2", "moderation_fallback", "g", ("md",)), WN.receipt("r", "m2", "p", 0), WN.answer("x3", "m3", "p", "act"),
            WN.answer("x2", "m2", "p", "act"), WN.landing("L", "m2", "p", "r", "fallback", Wm, ("x2", "x3"))]''',
'''    rows = [gm, am, md, WN.opener("p", "m2", "moderation_fallback", "g", ("md",)), WN.receipt("r", "m2", "p", 0), WN.answer("x1", "m1", "p", "act"),
            WN.answer("x3", "m3", "p", "act"), WN.answer("x2", "m2", "p", "act"), WN.landing("L", "m2", "p", "r", "fallback", Wm, ("x1", "x2", "x3"))]''')
rep('''"two members act over a present moderator without waiting 48 h''', '''"three members of four act over a present moderator without waiting 48 h''')
# t33: H is admitted first
rep('''    dm = ST.offer("dm", "F", "H", "duty", "g", "seat", ("g",), under="g")
    ahm = ST.accept("ahm", "H", "dm")
    onem = ST.offer("sybm", "H", syb, "moderate", "g", "seat", ("ahm",), under="dm", cosigners=syb)
    S = conc([g, dm, ahm, onem], SEAT)''', '''    # H is admitted to the roster first: a duty seat stands only on a member (seat.py, `member`)
    mh = ST.offer("mh", "F", "H", "member", "g", "group", ("g",), head=("g",), policy="community_invite", cosigners=("H",))
    dm = ST.offer("dm", "F", "H", "duty", "g", "seat", ("mh",), under="g")
    ahm = ST.accept("ahm", "H", "dm")
    onem = ST.offer("sybm", "H", syb, "moderate", "g", "seat", ("ahm",), under="dm", cosigners=syb)
    S = conc([g, mh, dm, ahm, onem], SEAT)''')
open(p, 'w').write(s)
