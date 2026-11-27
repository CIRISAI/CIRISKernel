import sys; sys.path.insert(0, ".")
from check_count_heads import *
P = [admit("p1", "X1", ("A", "B"), ("g",)), admit("p2", "X2", ("A", "B", "C", "X1"), ("p1",)),
     admit("p3", "X3", ("A", "B", "C", "X1", "X2"), ("p2",)), admit("p4", "X4", ("A", "B", "C", "X1", "X2", "X3"), ("p3",)),
     admit("p5", "X5", ("A", "B", "C", "X1", "X2", "X3", "X4"), ("p4",))]
W1 = ROOM + [invite("oX", "X", ("A", "B", "C"), ("g",)), ST.accept("acX", "X", "oX")]
W2 = ROOM + P + [invite("oX", "X", ("A", "B", "C", "X1", "X2", "X3", "X4", "X5"), ("p5",)), ST.accept("acX", "X", "oX")]
for nm, W in (("i", W1), ("ii", W2)):
    for own in ("X", None):
        S = CK.concluded(CK.kept(list(W)), RULE)
        Q = ST.Seats(S, own=own)
        print(nm, own, {i: bool(S.C.get(i)) for i in ("oX", "acX", "p1", "p5")}, sorted(Q.holders("member", OBJ)), sorted(Q.stale))
