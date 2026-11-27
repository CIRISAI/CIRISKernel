import sys
root = sys.argv[1]
p = root + '/models/causal_kernel/window.py'
s = open(p).read()


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a, s.count(a))
    s = s.replace(a, b)


# keep the cases' positions: the new case goes last
short = '''        ("false landing, short of the count: two members of four act and one of them lands the fallback",
         [g, am, md, p, receipt("r", "m2", "p", 0), acts[0], acts[1], landing("L", "m2", "p", "r", "fallback", W, ("x1", "x2"))],
         "the fallback needs the members' majority", "not fallback"),
'''
rep(short, '')
rep('''         "a duty seat stands only on a member", "fallback"),
    ]
    return "moderation fallback''', '''         "a duty seat stands only on a member", "fallback"),
''' + short + '''    ]
    return "moderation fallback''')
open(p, 'w').write(s)

p = root + '/models/causal_kernel/attacks.py'
s = open(p).read()

# t01: the appointment's withdrawal
rep('''    o2, bad = win(fb[:-1] + [Ain, dict(um, names=("md", "A"), target="md"), fb[-1]]); t.order(bad)''',
    '''    o2, bad = win(fb[:-1] + [Ain, dict(um, names=("md", "A"), target="md"), fb[-1]]); t.order(bad)''')
rep('''witness="g(m1,m2,m3) md(m1 appoints MOD) p x1,x3 L(m2 lands 'fallback') um''', '''witness="g(m1,m2,m3) am(MOD admitted) md(m1 appoints MOD) p x1,x2,x3 L(m2 lands 'fallback') um''')

# t03: K is admitted first, and the conferral is counted over the admission
rep('''    ref, bad = free([g, ST.offer("d1", "f1", "K", "moderate", "g", "seat", ("g",), under="g"), ST.accept("ak", "K", "d1")], SEAT,
                    lambda S: ST.Seats(S).stands("K", "moderate", "g")); t.order(bad)''',
    '''    # a duty seat stands only on a member (seat.py, `member`): K is admitted to the roster first, so each answer below is the count's
    mk = ST.offer("mk", "f1", "K", "member", "g", "group", ("g",), head=("g",), policy="community_invite", cosigners=("f2", "f3", "K"))
    c3 = dict(c3, names=("mk",))
    xf = dict(xf, names=("mk", "c3"), head=("mk",))
    ref, bad = free([g, mk, ST.offer("d1", "f1", "K", "moderate", "g", "seat", ("mk",), under="g"), ST.accept("ak", "K", "d1")], SEAT,
                    lambda S: ST.Seats(S).stands("K", "moderate", "g")); t.order(bad)''')
rep('''    d = ST.offer("d", "f1", "K", "moderate", "g", "group", ("g",), head=("g",), policy="duty_confer", counted="duty", cosigners=("f2",))
    ak = ST.accept("ak", "K", "d")
    xf_after = dict(xf, names=("g", "c3", "ak"))
    for label, rows, want in (("conferred by the count, then f1 withdrawn by the others, naming it", [g, d, ak, c3, xf_after], True),
                              ("conferred by the count, backdated, concurrent with f1's withdrawal", [g, d, ak, c3, xf], False)):''',
    '''    d = ST.offer("d", "f1", "K", "moderate", "g", "group", ("mk",), head=("mk",), policy="duty_confer", counted="duty", cosigners=("f2",))
    ak = ST.accept("ak", "K", "d")
    xf_after = dict(xf, names=("mk", "c3", "ak"))
    ref, bad = free([g, dict(d, names=("g",), head=("g",)), ak], SEAT, lambda S: ST.Seats(S).stands("K", "moderate", "g")); t.order(bad)
    t.fact("conferred by the count on a key that is not a member: K holds moderate = %s (a duty seat stands only on a member)" % ref, ref is False)
    for label, rows, want in (("conferred by the count, then f1 withdrawn by the others, naming it", [g, mk, d, ak, c3, xf_after], True),
                              ("conferred by the count, backdated, concurrent with f1's withdrawal", [g, mk, d, ak, c3, xf], False)):''')

# t06: K is a member of A's room before it is seated to moderate
rep('''    g = ST.offer("g", "A", "A", "duty", "@", "self")
    o1 = ST.offer("o1", "A", "K", "moderate", "g", "seat", ("g",), under="g")
    a1 = ST.accept("a1", "K", "o1")''',
    '''    g = ST.offer("g", "A", "A", "duty", "@", "self")
    # a duty seat stands only on a member (seat.py, `member`): K is admitted to the roster first, and stays a member throughout
    mk = ST.offer("mk", "A", "K", "member", "g", "group", ("g",), head=("g",), policy="community_invite", cosigners=("K",))
    o1 = ST.offer("o1", "A", "K", "moderate", "g", "seat", ("mk",), under="g")
    a1 = ST.accept("a1", "K", "o1")''')
rep('''    ref, bad = free([g, o1, a1, wd1, o2, a2, wd3], SEAT, ans); t.order(bad)''', '''    ref, bad = free([g, mk, o1, a1, wd1, o2, a2, wd3], SEAT, ans); t.order(bad)''')
rep('''    ref, bad = free([g, o1, a1, wd1, o2, a2, wd3, ST.withdraw("wd4", "K", "a2")], SEAT, ans); t.order(bad)''',
    '''    ref, bad = free([g, mk, o1, a1, wd1, o2, a2, wd3, ST.withdraw("wd4", "K", "a2")], SEAT, ans); t.order(bad)''')
rep('''    ref, bad = free([g, o1, a1, wd1, ST.offer("o3", "A", "K", "moderate", "g", "seat", ("wd1",), under="g", consent="one")], SEAT, ans); t.order(bad)''',
    '''    ref, bad = free([g, mk, o1, a1, wd1, ST.offer("o3", "A", "K", "moderate", "g", "seat", ("wd1",), under="g", consent="one")], SEAT, ans); t.order(bad)''')

# t07: K and J are admitted first
rep('''    d = ST.offer("d", "f1", "K", "duty", "g", "group", ("g",), head=("g",), policy="duty_confer", counted="duty", cosigners=("f2",))
    ak = ST.accept("ak", "K", "d")
    d2 = ST.offer("d2", "K", "J", "moderate:spam", "g", "group", ("ak",), head=("ak",), policy="duty_confer", counted="duty", cosigners=("J", "f2", "f3"))
    c3 = ST.cosign("c3", "f3", "xf", ("g",))
    xf = ST.unseat("xf", "f2", "f1", "duty", "g", "group", ("g", "c3"), head=("g",), policy="duty_withdraw", content="xf", counted="duty")''',
    '''    # a duty seat stands only on a member (seat.py, `member`): K and J are admitted to the roster by one counted row first,
    # and every counted row below is counted over that admission where it was counted over the founding row
    mk = ST.offer("mk", "f1", ("K", "J"), "member", "g", "group", ("g",), head=("g",), policy="community_invite", cosigners=("f2", "f3", "K", "J"))
    d = ST.offer("d", "f1", "K", "duty", "g", "group", ("mk",), head=("mk",), policy="duty_confer", counted="duty", cosigners=("f2",))
    ak = ST.accept("ak", "K", "d")
    d2 = ST.offer("d2", "K", "J", "moderate:spam", "g", "group", ("ak",), head=("ak",), policy="duty_confer", counted="duty", cosigners=("J", "f2", "f3"))
    c3 = ST.cosign("c3", "f3", "xf", ("mk",))
    xf = ST.unseat("xf", "f2", "f1", "duty", "g", "group", ("mk", "c3"), head=("mk",), policy="duty_withdraw", content="xf", counted="duty")''')
rep('''    ref, bad = free([g, d, ak, d2], SEAT, ans); t.order(bad)''', '''    ref, bad = free([g, mk, d, ak, d2], SEAT, ans); t.order(bad)''')
rep('''    ref, bad = free([g, d, ak, d2, c3, xf], SEAT, ans); t.order(bad)''', '''    ref, bad = free([g, mk, d, ak, d2, c3, xf], SEAT, ans); t.order(bad)''')
rep('''    ref, bad = free([g, d, ak, d2, c3, xf, cr, g2], SEAT, ans); t.order(bad)''', '''    ref, bad = free([g, mk, d, ak, d2, c3, xf, cr, g2], SEAT, ans); t.order(bad)''')
rep('''    ds = ST.offer("ds", "f1", "K", "moderate", "g", "self", ("g",), sub=True)
    aks = ST.accept("aks", "K", "ds")
    ref, bad = free([g, ds, aks], SEAT, ans); t.order(bad)''', '''    ds = ST.offer("ds", "f1", "K", "moderate", "g", "self", ("mk",), sub=True)
    aks = ST.accept("aks", "K", "ds")
    ref, bad = free([g, mk, ds, aks], SEAT, ans); t.order(bad)''')
rep('''witness="g(f1,f2,f3 found) d(f1+f2 -> K)''', '''witness="g(f1,f2,f3 found) mk(K and J admitted) d(f1+f2 -> K)''')

# window_bases
rep('''    gm = ST.offer("g", "m1", ("m1", "m2", "m3"), "duty", "@", "self", cosigners=("m2", "m3"))     # three duty holders (CC 4.5.4)
    md = ST.offer("md", "m1", "MOD", "moderate", "g", "group", ("g",), head=("g",), policy="duty_confer", counted="duty",
                  cosigners=("m3", "MOD"))                                     # two of the three confer, MOD accepting
    gh = ST.offer("g", "h1", ("h1", "h2", "h3"), "holder", "@", "self", cosigners=("h2", "h3"))
    pm = WN.opener("p", "m2", "moderation_fallback", "g", ("md",))''',
    '''    # three duty holders (CC 4.5.4); MOD is admitted to the roster and then seated to moderate (a duty seat stands only on a
    # member), so the room has four members and a strict majority of them is three
    gm, am = WN.admitted("MOD")
    md = ST.offer("md", "m1", "MOD", "moderate", "g", "group", ("am",), head=("am",), policy="duty_confer", counted="duty",
                  cosigners=("m3", "MOD"))                                     # two of the three confer, MOD accepting
    gh = ST.offer("g", "h1", ("h1", "h2", "h3"), "holder", "@", "self", cosigners=("h2", "h3"))
    pm = WN.opener("p", "m2", "moderation_fallback", "g", ("md",))''')
rep('''            [gm, md, pm, WN.receipt("r", "m2", "p", 0), WN.answer("x1", "m1", "p", "act"), WN.answer("x3", "m3", "p", "act"),
             WN.landing("L", "m2", "p", "r", "fallback", Wm, ("x1", "x3"))],''',
    '''            [gm, am, md, pm, WN.receipt("r", "m2", "p", 0), WN.answer("x1", "m1", "p", "act"), WN.answer("x2", "m2", "p", "act"), WN.answer("x3", "m3", "p", "act"),
             WN.landing("L", "m2", "p", "r", "fallback", Wm, ("x1", "x2", "x3"))],''')
rep('''            [gm, md, WN.opener("p", "MOD", "moderation_overturn", "g", ("md",)), WN.answer("o1", "m1", "p", "object"), WN.receipt("r", "m3", "p", 0),
             WN.landing("L", "m3", "p", "r", "stands", Wo, ("o1",))],
            {"a second member objects": WN.answer("n", "m2", "p", "object")}, "lifted", "m1"),''',
    '''            [gm, am, md, WN.opener("p", "MOD", "moderation_overturn", "g", ("md",)), WN.answer("o1", "m1", "p", "object"), WN.answer("o3", "m3", "p", "object"),
             WN.receipt("r", "m3", "p", 0), WN.landing("L", "m3", "p", "r", "stands", Wo, ("o1", "o3"))],
            {"a third member objects": WN.answer("n", "m2", "p", "object")}, "lifted", "m1"),''')
rep('''            [gm, md, WN.opener("p", "MOD", "moderation_overturn", "g", ("md",)), WN.answer("o1", "m1", "p", "object"), WN.answer("o2", "m2", "p", "object"),
             WN.receipt("r", "m1", "p", 0), WN.landing("L", "m1", "p", "r", "lifted", 0, ("o1", "o2"))],''',
    '''            [gm, am, md, WN.opener("p", "MOD", "moderation_overturn", "g", ("md",)), WN.answer("o1", "m1", "p", "object"), WN.answer("o2", "m2", "p", "object"),
             WN.answer("o3", "m3", "p", "object"), WN.receipt("r", "m1", "p", 0), WN.landing("L", "m1", "p", "r", "lifted", 0, ("o1", "o2", "o3"))],''')
rep('''and the members' check (a second member objects: lifted).''', '''and the members' check (a third member objects: lifted).''')

# checkpoint_price: the hostile members, and the two who act without waiting
rep('''    gm = ST.offer("g", "m1", ("m1", "m2", "m3"), "duty", "@", "self", cosigners=("m2", "m3"))     # three duty holders (CC 4.5.4)
    md = ST.offer("md", "m1", "MOD", "moderate", "g", "group", ("g",), head=("g",), policy="duty_confer", counted="duty",
                  cosigners=("m3", "MOD"))                                     # two of the three confer, MOD accepting
    Wm = WN.secs("moderation_fallback")''', '''    gm, am = WN.admitted("MOD")                                               # three duty holders (CC 4.5.4), and MOD a member
    md = ST.offer("md", "m1", "MOD", "moderate", "g", "group", ("am",), head=("am",), policy="duty_confer", counted="duty",
                  cosigners=("m3", "MOD"))                                     # two of the three confer, MOD accepting
    Wm = WN.secs("moderation_fallback")''')
rep('''    gm = ST.offer("g", "m1", ("m1", "m2", "m3"), "duty", "@", "self", cosigners=("m2", "m3"))     # three duty holders (CC 4.5.4)
    md = ST.offer("md", "m1", "MOD", "moderate", "g", "group", ("g",), head=("g",), policy="duty_confer", counted="duty",
                  cosigners=("m3", "MOD"))                                     # two of the three confer, MOD accepting
    rows = [gm, md, WN.opener''', '''    gm, am = WN.admitted("MOD")                                               # three duty holders (CC 4.5.4), and MOD a member
    md = ST.offer("md", "m1", "MOD", "moderate", "g", "group", ("am",), head=("am",), policy="duty_confer", counted="duty",
                  cosigners=("m3", "MOD"))                                     # two of the three confer, MOD accepting
    rows = [gm, am, md, WN.opener''')
open(p, 'w').write(s)
