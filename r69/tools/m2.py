import sys
sys.path.insert(0, sys.argv[1])
exec(open(sys.argv[2]).read().split("GM4 = AC.GM4")[0])
G4 = ST.offer("g", "A", tuple("ABCD"), "member", "@", "self", cosigners=tuple("BCD"), consensus_protocol="majority")
adm = grp("ad", "offer", ("X", "Y", "Z", "W"), "member", "cosigned_act", signer="A", cosigners=("B", "C", "X", "Y", "Z", "W"))
rm = grp("x", "unseat", "X", "member", None, heads=("ad",), signer="A", cosigners=("B", "C"))
rm = dict(rm, to=("X", "Y", "Z", "W"), cuts=tuple(("seat", k, "member", "g") for k in "XYZW"))
G6 = ST.offer("g", "A", tuple("ABCDEF"), "member", "@", "self", cosigners=tuple("BCDEF"), consensus_protocol="majority")
for name, rows, rid in (("R1 A,B,C (3 of 4) admit X,Y,Z,W in one row", [G4, adm], "ad"),
                        ("R2 then A,B,C remove X,Y,Z,W in one row", [G4, adm, rm], "x"),
                        ("S6a room of six, B,C,D remove A (3 of the 5 others)", [G6, grp("x", "unseat", "A", "member", None, signer="B", cosigners=("C", "D"))], "x"),
                        ("S6b room of six, B,C,D,E remove A (4)", [G6, grp("x", "unseat", "A", "member", None, signer="B", cosigners=("C", "D", "E"))], "x")):
    S = CK.concluded(CK.kept(rows), RULE)
    print(name, "->", S.C.get(rid), "| roster", "".join(sorted(ST.Seats(S).roster("g"))))
