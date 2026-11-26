import sys, os
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cases.py")).read().split('if __name__ == "__main__":')[0].replace('os.path.dirname(os.path.abspath(__file__))', repr(os.path.dirname(os.path.abspath(__file__)))))
src3 = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "round3.py")).read().split("def ans(S, a):")[0]
ns = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "round3.py")}; exec(src3, ns)
sib = ROOM + [T1r, T2r]
S = CK.concluded(CK.kept(sib), CH.RULE)
print("siblings: void for C", sorted(ST.reader_void(S, "C")), "for D", sorted(ST.reader_void(S, "D")))
one = [G1, N1, admit("n2", "N2", ("A",), ("g",))]
S = CK.concluded(CK.kept(one), CH.RULE)
print("room of one: void for N1", sorted(ST.reader_void(S, "N1")), "for N2", sorted(ST.reader_void(S, "N2")))
rows = ns["SA"] + [admit("rz", "Z", ("A", "B", "C"), ("q1b", "q2b"))]
S = CK.concluded(CK.kept(rows), CH.RULE)
P = [q for q in S.Cs if q["id"] in S.anc.get("rz", ())]
print("S against itself: S'' void for rz", sorted(ST.signers_void(rows[-1], P)))
