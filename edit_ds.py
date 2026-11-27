import sys
p = sys.argv[1] + '/models/causal_kernel/check_duty_seats.py'
s = open(p).read()


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a, s.count(a))
    s = s.replace(a, b)


rep('''The founding, as rows. A founding row of scope `duty` seats the keys it names as duty holders, and that seat holds
`member`: a founding holder's membership is its founding duty seat, and its withdrawal of the founding row ends both.
Where a founding holder is to lay down its duty and stay a member, the founding is presented as the founding row and
one chained counted row of scope `member` that seats the same keys over the founding row as its head: each holder then
has a member seat beside its duty seat, its withdrawal of the founding row ends its duty seat, and it stays a member.
That withdrawal ends the duty seats conferred on it in its past as well (it is the holder's own withdrawal of a seat
that holds `member`). Persist's table gives the duty seat `member` and no named duty (HOLDS.duty = ("member",)), with
each named duty a chained counted row; the cases run that table too.
''', '''The founding, as rows. A founding row of scope `duty` seats the keys it names as duty holders, and that seat holds
`member`: a founding holder's membership is its founding duty seat, and its withdrawal of the founding row ends both.
Where a founding holder is to lay down its duty and stay a member, it needs a member seat beside its duty seat, and
what runs depends on how many found the community:
    three or more   the founding row, then one chained counted row of scope `member` per founding holder, signed by
                    the other holders (the crate holds that no key admits itself, CC 2.7.5: a key a counted row
                    seats is no voice of its count, so one row seating every founder on the founders' own voices
                    concludes nothing there; this reference does not have that rule, and the cases here use only
                    rows the two agree on). Each holder then has a member seat beside its duty seat: its withdrawal
                    of the founding row ends its duty seat, and it stays a member.
    one             the founding row, then the founder's own offer of `member` to itself over the founding row
                    (conferrer: the object's own key). Over a founding row that seats one key that offer stands on
                    its own, so it outlives the founder's withdrawal of the founding row.
    two             neither runs: one voice of two meets no count here, and over a founding row that seats several
                    keys an own offer stands only while its signer's founding seat does. Two founders have no
                    presentation in which either lays down its duty and stays a member. This is open.
The withdrawal of the founding row ends the duty seats conferred on that holder in its past as well: it is the
holder's own withdrawal of a seat that holds `member`. Persist's table gives the duty seat `member` and no named duty
(HOLDS.duty = ("member",)), with each named duty a chained counted row; the cases run that table too.
''')
rep('''MF = admit("mf", ("A", "B", "C"), ("A", "B", "C"), ("g",))
WA = ST.withdraw("wa", "A", "g", ("mf",))                               # A lays down its founding duty seat
CM = confer("cm", "A", "moderate", ("B", "C"), ("mf",))                  # persist's table: a named duty is a chained row
''', '''# (one chained counted row per founding holder, signed by the others: no key admits itself)
MFA = admit("mfa", "A", ("B", "C"), ("g",))
MFB = admit("mfb", "B", ("A", "C"), ("mfa",))
MFC = admit("mfc", "C", ("A", "B"), ("mfb",))
WA = ST.withdraw("wa", "A", "g", ("mfa",))                              # A lays down its founding duty seat
CM = confer("cm", "A", "moderate", ("B", "C"), ("mfa",))                 # persist's table: a named duty is a chained row
G1 = ST.offer("g", "A", ("A",), "duty", "@", "self")                     # a lone founder
MS1 = ST.offer("ms", "A", "A", "member", OBJ, "self", ("g",))            # and its own offer of `member` to itself
''')
rep('''    ("the founding as two rows: each founding holder has a member seat beside its founding duty seat",
     [G, MF], [("A", "member", T), ("A", "duty", T), ("A", "moderate", T)], None),
    ("a founding holder lays down its duty (it withdraws the founding row) and stays a member",
     [G, MF, WA], [("A", "member", T), ("A", "duty", F), ("A", "moderate", F), ("B", "duty", T), ("B", "member", T)], None),
''', '''    ("the founding as chained rows: each founding holder has a member seat beside its founding duty seat",
     [G, MFA, MFB, MFC], [("A", "member", T), ("A", "duty", T), ("A", "moderate", T), ("C", "member", T), ("C", "duty", T)], None),
    ("each of the three lays down its duty in turn (it withdraws the founding row) and all stay members; nobody holds a duty",
     [G, MFA, MFB, MFC, ST.withdraw("wa", "A", "g", ("mfc",)), ST.withdraw("wb", "B", "g", ("mfc",)), ST.withdraw("wc", "C", "g", ("mfc",))],
     [("A", "member", T), ("B", "member", T), ("C", "member", T), ("A", "duty", F), ("B", "duty", F), ("C", "duty", F)], None),
    ("a founding holder lays down its duty (it withdraws the founding row) and stays a member",
     [G, MFA, WA], [("A", "member", T), ("A", "duty", F), ("A", "moderate", F), ("B", "duty", T), ("B", "member", T)], None),
    ("a lone founder with its own offer of `member` to itself lays down its duty and stays a member",
     [G1, MS1, ST.withdraw("wa", "A", "g", ("ms",))], [("A", "member", T), ("A", "duty", F)], None),
    ("two founders: an own offer of `member` stands only on its signer's founding seat, so it does not outlive that seat",
     [G2, ST.offer("ms", "A", "A", "member", OBJ, "self", ("g",)), ST.withdraw("wa", "A", "g", ("ms",))],
     [("A", "member", F), ("A", "duty", F), ("B", "member", T)], None),
''')
rep('''     [G, MF, CM], [("A", "duty", T)''', '''     [G, MFA, CM], [("A", "duty", T)''')
rep('''     [G, MF, CM, ST.withdraw("wm", "A", "cm", ("cm",))]''', '''     [G, MFA, CM, ST.withdraw("wm", "A", "cm", ("cm",))]''')
rep('''     [G, MF, CM, ST.withdraw("wa", "A", "g", ("cm",))], [''', '''     [G, MFA, CM, ST.withdraw("wa", "A", "g", ("cm",))], [''')
rep('''     [G, MF, CM, ST.withdraw("wa", "A", "g", ("cm",)), confer''', '''     [G, MFA, CM, ST.withdraw("wa", "A", "g", ("cm",)), confer''')
open(p, 'w').write(s)
