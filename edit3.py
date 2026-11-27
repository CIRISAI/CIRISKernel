import sys
root = sys.argv[1]
p = root + '/models/causal_kernel/check_rosters.py'
s = open(p).read()


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a, s.count(a))
    s = s.replace(a, b)


rep('''    holder's acceptance. (iii) holders are equals. A removal from the roster ends the removed member's duty seats."""''',
    '''    holder's acceptance. (iii) holders are equals. A removal from the roster ends the removed member's duty seats.
    A duty seat stands only on a member (seat.py, `member`), so each world that confers one first admits the key it
    confers on, by the room's own count (`adm`); the conferral is then counted over that admission as its head. The
    worlds test the duty holders' count, and check_duty_seats.py tests the membership condition itself."""''')
rep('''    lone = lambda i, signer, k, under="g", names=("g",): [ST.offer(i, signer, k, "duty", "g", "seat", names, under=under), ST.accept("a" + i, k, i)]
''', '''    lone = lambda i, signer, k, under="g", names=("g",): [ST.offer(i, signer, k, "duty", "g", "seat", names, under=under), ST.accept("a" + i, k, i)]
    adm = lambda k, signers: [RS.accept(spec, "ac" + k, k), RS.add(spec, "m" + k, ("g",), k, signers, names=("ac" + k,))]   # the widening that makes k a member
''')
rep('''[found(("A",))] + lone("o", "A", "B"), frozenset({"A", "B"})),
         ("one holder of two confers alone", [found(("A", "B"))] + lone("o", "A", "C"), frozenset({"A", "B"}))]''',
    '''[found(("A",))] + adm("B", ("A",)) + lone("o", "A", "B"), frozenset({"A", "B"})),
         ("one holder of two confers alone", [found(("A", "B"))] + adm("C", ("A", "B")) + lone("o", "A", "C"), frozenset({"A", "B"}))]''')
rep('''[found(("A", "B", "C")), confer("o", ("A", "B"), "D")], frozenset({"A", "B", "C", "D"})),''',
    '''[found(("A", "B", "C"))] + adm("D", ("A", "B")) + [confer("o", ("A", "B"), "D", head=("mD",))], frozenset({"A", "B", "C", "D"})),''')
rep('''[found(("A",))] + lone("o", "A", "B") + [ST.withdraw("w", "A", "o", ("ao",))], frozenset({"A", "B"})),
         ("A confers alone, then leaves", [found(("A",))] + lone("o", "A", "B") + [ST.withdraw("w", "A", "g", ("ao",))], frozenset({"B"}))]''',
    '''[found(("A",))] + adm("B", ("A",)) + lone("o", "A", "B") + [ST.withdraw("w", "A", "o", ("ao",))], frozenset({"A", "B"})),
         ("A confers alone, then leaves", [found(("A",))] + adm("B", ("A",)) + lone("o", "A", "B") + [ST.withdraw("w", "A", "g", ("ao", "mB"))], frozenset({"B"}))]''')
rep('''[found(("A", "B"))] + own("o", "A", "C", "detect:x"), ("C", "detect:x", False)),
          ("one of two holders seats a declared duty alone", [gd(("A", "B"))] + own("o", "A", "C", "verify"), ("C", "verify", False)),
          ("the lone holder seats detect:x, the holder accepting", [found(("A",))] + own("o", "A", "C", "detect:x"), ("C", "detect:x", True)),''',
    '''[found(("A", "B"))] + adm("C", ("A", "B")) + own("o", "A", "C", "detect:x"), ("C", "detect:x", False)),
          ("one of two holders seats a declared duty alone", [gd(("A", "B"))] + adm("C", ("A", "B")) + own("o", "A", "C", "verify"), ("C", "verify", False)),
          ("the lone holder seats detect:x, the holder accepting", [found(("A",))] + adm("C", ("A",)) + own("o", "A", "C", "detect:x"), ("C", "detect:x", True)),''')
rep('''[gd(("A", "B", "D")), ST.offer("o", "A", "C", "verify", "g", "group", ("g",), head=("g",), policy="duty_confer", counted="duty", cosigners=("B", "C"))],''',
    '''[gd(("A", "B", "D"))] + adm("C", ("A", "B")) + [ST.offer("o", "A", "C", "verify", "g", "group", ("mC",), head=("mC",), policy="duty_confer", counted="duty", cosigners=("B", "C"))],''')
open(p, 'w').write(s)

p = root + '/models/causal_kernel/roster.py'
s = open(p).read()
rep('''        - ST.left_in_past(P, r.get("over", r["obj"]), r.get("counted", spec.counted))      # a key that left in the version's past''',
    '''        - ST.count_left(P, past, r.get("over", r["obj"]), r.get("counted", spec.counted))  # a key that left in the version's past''')
open(p, 'w').write(s)
