"""L': an honest chain whose first change was signed only by keys that later fork. A room under a declared quorum of two
(policy `quorum`, need 2), founded by A, B, C: aD by A and B; aE..aG by C, D, E.. on top; A and B fork at g (dc, xd)."""
import sys, os, itertools, random
sys.path.insert(0, os.path.join(sys.argv[1], "models/causal_kernel"))
import seat as ST, check_count_heads as CH, checkpoint as CP
CK = ST.CK; OBJ = "g"
G = ST.found("g", "A", ("A", "B", "C"), {"moderate": ("A",)}, cosigners=("B", "C"), consensus_protocol="quorum")
def adm(i, k, sg, heads, cites=()):
    return ST.offer(i, sg[0], k, "member", OBJ, "group", tuple(heads) + tuple(cites), head=tuple(heads), policy="cosigned_act",
                    need=2, cosigners=tuple(sg[1:]) + (k,))
def rem(i, k, sg, heads, cites=()):
    return ST.unseat(i, sg[0], k, "member", OBJ, "group", tuple(heads) + tuple(cites), head=tuple(heads), policy="community_remove",
                     need=2, cosigners=tuple(sg[1:]))
DC = ST.offer("dc", "A", "B", "moderate", OBJ, "group", ("g",), head=("g",), policy="duty_confer", counted="duty", cosigners=("B",))
XD = adm("xd", "X", ("A", "B"), ("dc",))
def world(aD_by, aE_by):
    return [G, adm("aD", "D", aD_by, ("g",)), adm("aE", "E", aE_by, ("aD",)), adm("aF", "F", ("C", "D", "E"), ("aE",)),
            adm("aG", "G", ("C", "D", "E", "F"), ("aF",)), DC, XD]
W = {"L' (aD by A,B; aE by C,D)": world(("A", "B"), ("C", "D")),
     "L' variant: A,B signed aD and aE": world(("A", "B"), ("A", "B", "C", "D")),
     "L' variant: A,B,C signed aD": world(("A", "B", "C"), ("C", "D"))}
if __name__ == "__main__":
    for name, rows in W.items():
        r = rem("xa", "A", ("C", "D", "E", "F", "G"), ("xd", "aG"))
        S = CK.concluded(CK.kept(rows + [r]), CH.RULE)
        P = [q for q in S.Cs if q["id"] in S.anc["xa"]]
        print("%s | concluded %s | void for xa %s | xa %s" % (name, sorted(i for i in S.C if S.C[i]), sorted(ST.signers_void(r, P)), bool(S.C.get("xa"))))
