import sys
p = sys.argv[1] + '/models/causal_kernel/attacks.py'
s = open(p).read()


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a, s.count(a))
    s = s.replace(a, b)


rep('''    cr = ST.cosign("cr", "f3", "g2", ("xf", "d2"))
    g2 = ST.offer("g2", "f2", "f1", "duty", "g", "group", ("xf", "d2", "cr"), head=("xf", "d2"), policy="duty_confer", content="g2", counted="duty", cosigners=("f1",))
    ref, bad = free([g, mk, d, ak, d2, c3, xf, cr, g2], SEAT, ans); t.order(bad)
    t.fact("a version naming both tips (f2 and f3 confer f1's duty again): f1, K, J stand = %s; the grants were never ended, since holders are equals (CC 4.5.4 (iii))" % (ref,),
           ref == (True, True, True))''',
    '''    # f1's membership was its founding duty seat, which the withdrawal ended: a duty seat stands only on a member, so f1 is
    # admitted again by the version that names both tips (counted over the four members common to them), and its duty is
    # then conferred over that version by three of the four duty holders
    cm = [ST.cosign("cm3", "f3", "m2", ("xf", "d2")), ST.cosign("cmk", "K", "m2", ("xf", "d2"))]
    m2 = ST.offer("m2", "f2", "f1", "member", "g", "group", ("xf", "d2", "cm3", "cmk"), head=("xf", "d2"), policy="community_invite", content="m2", cosigners=("f1",))
    ref, bad = free([g, mk, d, ak, d2, c3, xf] + cm + [m2], SEAT, ans); t.order(bad)
    t.fact("a version naming both tips (f2, f3 and K admit f1 again): f1, K, J stand = %s; the grants were never ended, since holders are equals (CC 4.5.4 (iii)), "
           "and f1's ended duty seat is not revived by its admission" % (ref,), ref == (False, True, True))
    cr = [ST.cosign("cr", "f3", "g2", ("m2",)), ST.cosign("crk", "K", "g2", ("m2",))]
    g2 = ST.offer("g2", "f2", "f1", "duty", "g", "group", ("m2", "cr", "crk"), head=("m2",), policy="duty_confer", content="g2", counted="duty", cosigners=("f1",))
    ref, bad = free([g, mk, d, ak, d2, c3, xf] + cm + [m2] + cr + [g2], SEAT, ans); t.order(bad)
    t.fact("then f2, f3 and K confer f1's duty again over that version: f1, K, J stand = %s" % (ref,), ref == (True, True, True))''')
rep('''once a version names both, K and J stand and f1 stands only if re-conferred.''', '''once a version names both, K and J stand and f1 stands only if admitted again and re-conferred.''')
open(p, 'w').write(s)
