import sys
p = sys.argv[1] + '/models/causal_kernel/check_rosters.py'
s = open(p).read()
for a, b in (('[found(("A", "B"))] + adm("C", ("A", "B")) + own("o", "A", "C", "detect:x")', '[found(("A", "B"))] + own("o", "A", "C", "detect:x")'),
             ('[found(("A",))] + adm("C", ("A",)) + own("o", "A", "C", "detect:x")', '[found(("A",))] + own("o", "A", "C", "detect:x")')):
    assert s.count(a) == 1
    s = s.replace(a, b)
open(p, 'w').write(s)
