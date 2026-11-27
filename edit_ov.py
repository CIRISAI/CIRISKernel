import sys
root = sys.argv[1]


def edit(path, pairs):
    p = root + '/' + path
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (path, a, s.count(a))
        s = s.replace(a, b)
    open(p, 'w').write(s)


edit('models/causal_kernel/window.py', [('''        ("objection signed just after, naming the landing: a member objects late and honestly",
         base + [o1, o3, r3, stands2,''', '''        ("a member who holds no duty opens the check on an act of its own, and three of four object and land the lift",
         [g, am, opener("p", "MOD", "moderation_overturn", "g", ("am",)), o1, o2, o3, r1, landing("L", "m1", "p", "r", "lifted", 0, ("o1", "o2", "o3"))],
         "only a duty holder's act opens the members' check", "not lifted"),
        ("objection signed just after, naming the landing: a member objects late and honestly",
         base + [o1, o3, r3, stands2,''')])
edit('models/causal_kernel/README.md', [('recount breaks none of fifty checks', 'recount breaks none of fifty-one checks')])
edit('kernel/KERNEL.md', [('fifty checks of what each exis', 'fifty-one checks of what each exis')])
edit('crates/ciris-kernel/CHANGELOG.md', [('table is 61 rows and 50 checks (recount breaks none).', '''table is 62 rows and 51 checks (recount breaks none). With the duty holder a member, the overturn world no
longer told the opener's scope from the counted one, so it gains a case: a member who holds no duty opens the
check, and nothing is opened.''')])
