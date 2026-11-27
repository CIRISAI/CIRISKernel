import sys, os
R = sys.argv[1]; sys.path.insert(0, os.path.join(R, "models/causal_kernel")); sys.dont_write_bytecode = True
import seat as ST
CK = ST.CK
RULE = lambda r, P, past: ST.seat_rule(r, P, past)
OBJ = "g"
def admit(i, k, signers, heads):
    return ST.offer(i, signers[0], k, "member", OBJ, "group", tuple(heads), head=tuple(heads), policy="community_invite",
                    cosigners=tuple(signers[1:]) + ((k,) if k not in signers else ()))
def remove(i, k, signers, heads):
    return ST.unseat(i, signers[0], k, "member", OBJ, "group", tuple(heads), head=tuple(heads), policy="community_remove",
                     cosigners=tuple(signers[1:]))
G6 = ST.offer("g", "A", tuple("ABCDEF"), "member", "@", "self", cosigners=tuple("BCDEF"))
wc = ST.withdraw("wc", "C", "g", ("g",))                 # C resigns
ac = admit("ac", "C", ("A", "B", "D", "E"), ("wc",))      # re-admitted by the room's count (4 of 5)
xc = remove("xc", "C", ("A", "B", "D", "E"), ("g",))      # or: C removed by the room's count
ac2 = admit("ac", "C", ("A", "B", "D", "E"), ("xc",))
def run(name, rows, ask):
    S = CK.concluded(CK.kept(list(rows)), RULE); Q = ST.Seats(S)
    ordok = True
    import itertools
    for p in itertools.islice(itertools.permutations(rows[1:]), 0, 720):
        S2 = CK.arrive([rows[0]] + list(p), RULE)
        if {r["id"]: S2.C[r["id"]] for r in rows} != {r["id"]: S.C[r["id"]] for r in rows}: ordok = False; break
    last = rows[-1]
    print("%-70s concludes=%s  %s  orders-agree=%s" % (name, S.C[last["id"]], ask(Q), ordok))
for path, pre in (("resigned+readmitted", [G6, wc, ac]), ("removed+readmitted", [G6, xc, ac2])):
    print("--", path)
    run("C a member at ac", pre, lambda Q: {"C member": Q.stands("C", "member", OBJ)})
    # (a) admission of X: base with C is 6, 2/3 needs 4. A,B,C,D sign (4 of 6: valid); without C counted: 3 of 5: not
    run("(a1) X admitted by A,B,C,D (4 of 6 if C counts)", pre + [admit("ax", "X", ("A","B","C","D"), ("ac",))], lambda Q: {"X": Q.stands("X","member",OBJ)})
    # (a2) A,B,D sign: 3 of 6 invalid; if C out of base: 3 of 5 = 0.6 <2/3 invalid too; use A,B,D,E: 4/6 valid either way
    run("(a2) X admitted by A,B,D,E (4 of 6; 4 of 5 if C out)", pre + [admit("ax", "X", ("A","B","D","E"), ("ac",))], lambda Q: {"X": Q.stands("X","member",OBJ)})
    # (b) removal of F by A,B,C,D: 4 of 6 valid
    run("(b) F removed by A,B,C,D (4 of 6 if C counts)", pre + [remove("xf", "F", ("A","B","C","D"), ("ac",))], lambda Q: {"F": Q.stands("F","member",OBJ)})
    # base test: 7th member? removal of F by A,B,D,E: with C in base 4/6 valid; C out 4/5 valid. use admission by A,B,D (3): 3/6 no, 3/5 no.
G4 = ST.offer("g", "A", tuple("ABCD"), "member", "@", "self", cosigners=tuple("BCD"))
ac4 = admit("ac", "C", ("A", "B", "D"), ("wc",))
xc4 = remove("xc", "C", ("A", "B", "D"), ("g",)); ac4x = admit("ac", "C", ("A", "B", "D"), ("xc",))
for path, pre in (("room of 4, resigned+readmitted", [G4, wc, ac4]), ("room of 4, removed+readmitted", [G4, xc4, ac4x])):
    print("--", path)
    run("(base) X admitted by A,B only (2 of 4: invalid; 2 of 3 if C out of base)", pre + [admit("ax", "X", ("A","B"), ("ac",))], lambda Q: {"X": Q.stands("X","member",OBJ)})
    run("(base) D removed by A,B (2 of 4 invalid; 2 of 3 if C out)", pre + [remove("xd", "D", ("A","B"), ("ac",))], lambda Q: {"D": Q.stands("D","member",OBJ)})
