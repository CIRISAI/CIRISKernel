import sys, itertools
sys.path.insert(0, sys.argv[1])
exec(open(sys.argv[2]).read().split("GM4 = AC.GM4")[0])
K7 = tuple("ABCDEFG"); T = tuple("CDEFG")
def room(proto):
    return ST.offer("g", "A", K7, "member", "@", "self", cosigners=K7[1:], consensus_protocol=proto)
def multi(i, to, signers, heads=("g",)):
    r = grp(i, "unseat", to[0], "member", None, heads=heads, signer=signers[0], cosigners=tuple(signers[1:]))
    return dict(r, to=tuple(to), cuts=tuple(("seat", k, "member", "g") for k in to))
def show(name, rows, ids):
    S = CK.concluded(CK.kept(rows), RULE); Q = ST.Seats(S)
    past = lambda a, b: a in S.anc[b]
    info = []
    for i in ids:
        r = S.by[i]; P = [q for q in S.Cs if q["id"] in S.anc[i]]
        f = ST.in_force(r, {q["id"]: q for q in P})
        mem, vot = ST.counted_keys(P, past, "g", r["head"])
        if f is not ST.REFUSED and f.get("base_excludes_target"): mem = mem - set(r["to"]); vot = vot - set(r["to"])
        info.append("%s: base %d, voices %d, policy %s need %s -> %s" % (i, len(mem), len(ST.voices(r, P) & vot), None if f is ST.REFUSED else f.get("policy"), None if f is ST.REFUSED else f.get("need"), S.C.get(i)))
    print(name, "|", "; ".join(info), "| roster:", "".join(sorted(Q.roster("g"))), "| contested/out:", sorted(Q.dropped))
for proto in ("majority", "two_thirds", "quorum:2/7", "quorum:3/7", "unanimous"):
    print("==", proto)
    G = room(proto)
    show("Q1 one row, A,B remove C-G", [G, multi("x", T, ("A", "B"))], ["x"])
    rows = [G] + [multi("x" + k, (k,), ("A", "B")) for k in T]
    show("Q2 five rows at g", rows, ["x" + k for k in T])
    cr = [multi("y" + k, ("A",), (k,) + tuple(j for j in T if j != k)) for k in T[:1]]
    show("Q3 Q1 + C..G remove A (one row, five voices)", [G, multi("x", T, ("A", "B")), multi("y", ("A",), T)], ["x", "y"])
    show("Q3b Q2 + C..G remove A", rows + [multi("y", ("A",), T)], ["x" + k for k in T] + ["y"])
