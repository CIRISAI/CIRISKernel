import sys; sys.path.insert(0, ".")
import check_count_heads as CH, seat as ST, causal_kernel as CK
from check_count_heads import ROOM, OBJ, admit, ack, G
def conf(i, to, heads, cites=(), scope="moderate", signers=("A",), joins=True):
    to = (to,) if isinstance(to, str) else tuple(to)
    return ST.offer(i, signers[0], to, scope, OBJ, "group", tuple(heads) + tuple(cites), head=tuple(heads),
                    policy="duty_confer", counted="duty", cosigners=tuple(signers[1:]) + (to if joins else ()))
def show(name, rows, own=None, scopes=("moderate", "review", "member")):
    S = CK.concluded(CK.kept(list(rows)), CH.RULE)
    Q = ST.Seats(S, own=own)
    print(name, "| concl:", {r["id"]: bool(S.C.get(r["id"])) for r in rows[len(ROOM):] if r["kind"] in ("offer","unseat")},
          "|", {sc: sorted(Q.holders(sc, OBJ)) for sc in scopes}, "| stale", sorted(Q.stale))
show("LO1", ROOM + [conf("oB", "B", ("aG",), joins=False), conf("oC", "C", ("oB",))])
show("LO2", ROOM + [conf("oB", "B", ("aG",), joins=False), ST.withdraw("wB", "A", "oB", ("oB",)), conf("oC", "C", ("oB",), ("wB",))])
show("LO3", ROOM + [conf("oB", "B", ("aG",), scope="review", joins=False), conf("oC", "C", ("oB",))])
show("LO4", ROOM + [conf("oBC", ("B", "C"), ("aG",))])
show("LO5", ROOM + [conf("oB", "B", ("aG",)), conf("oC", "C", ("oB",))])
F1 = ROOM + [conf("oB", "B", ("aG",), joins=False), conf("oC", "C", ("aG",)), ST.accept("acB", "B", "oB")]
show("LO6", F1); show("LO6/B", F1, "B")
F2 = ROOM + [conf("oB", "B", ("aG",)), ack("kB", "B", "oB"), ack("kD", "D", "oB"), conf("oC", "C", ("aG",))]
for own in ("B", "D", None): show("LO7/%s" % own, F2, own)
F2b = ROOM + [conf("oB", "B", ("aG",)), conf("oC", "C", ("aG",))]
show("LO7 no acks/B", F2b, "B")
G1 = ST.found("g", "A", ("A",), {})
one = lambda i, k, heads, cites=(): ST.offer(i, "A", k, "member", OBJ, "group", tuple(heads)+tuple(cites), head=tuple(heads), policy="community_invite", cosigners=(k,))
show("ONE concurrent", [G1, one("n1", "N1", ("g",)), one("n2", "N2", ("g",))])
show("ONE sequential", [G1, one("n1", "N1", ("g",)), one("n2", "N2", ("n1",))])
show("ONE sequential +N1", [G1, one("n1", "N1", ("g",)), ST.offer("n2", "A", "N2", "member", OBJ, "group", ("n1",), head=("n1",), policy="community_invite", cosigners=("N1","N2"))])
show("ONE after concurrent: A alone admits N3 at both", [G1, one("n1", "N1", ("g",)), one("n2", "N2", ("g",)), one("n3","N3",("n1","n2"))])
L = ROOM + [conf("dB", "B", ("aG",)), conf("dCx", "C", ("dB",), signers=("A", "B")),
            conf("dA", "A", ("dCx",), signers=("A", "B", "C")), ST.withdraw("lm", "A", "g", ("dA",), scope="moderate"),
            conf("dD", "D", ("dA",), ("lm",), signers=("A", "B"))]
show("LEAVE", L)
ST.MUT.add("leaving_ends_key"); show("LEAVE plant", L); ST.MUT.discard("leaving_ends_key")
