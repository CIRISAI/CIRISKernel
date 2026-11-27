import sys, itertools
sys.path.insert(0, sys.argv[1])
import seat as ST, window as WN, check_acts as AC
CK, R = ST.CK, ST.R
RULE = lambda r, P, past: WN.rule(r, P, past)
grp, OBJ = AC.grp, "g"
def run(name, rows, asks, orders=True):
    S = CK.concluded(CK.kept(list(rows)), RULE); Q = ST.Seats(S)
    got = [(k, s, Q.stands(k, s, OBJ)) for k, s in asks]
    bad = ""
    if orders:
        tail = rows[1:]
        for p in (itertools.permutations(tail) if len(tail) <= 6 else [tail[::-1]]):
            Q2 = ST.Seats(CK.arrive([rows[0]] + list(p), RULE))
            if [(k, s, Q2.stands(k, s, OBJ)) for k, s in asks] != got: bad = " ORDER-DIFF"; break
    print(name, "->", got, {r["id"]: bool(S.C.get(r["id"])) for r in rows[1:]}, bad)
GM4 = AC.GM4   # A,B,C,D founders, protocol two_thirds
# T1: one founder's own (not counted) offer of member / founder to X
for sc in ("member", "founder", "node", "agent"):
    o = ST.offer("o", "A", "X", sc, OBJ, "self", ("g",), cosigners=("X",))
    run("T1 founder A's own offer of %s to X" % sc, [GM4, o], [("X", "member"), ("X", sc)])
o = ST.offer("o", "A", "X", "founder", OBJ, "self", ("g",), cosigners=("X",))
run("T1b and X then votes: A+X admit Y under cosigned_act (2 of 5 < 2/3)?", [GM4, o, grp("ay", "offer", "Y", "member", "cosigned_act", heads=("o",), cosigners=("X", "Y"))], [("Y", "member")])
# T2: consent one on a counted admission
c = grp("r", "offer", "E", "member", "cosigned_act", cosigners=("B", "C"), consent="one")
run("T2 counted admission of E with consent=one, E never accepts", [GM4, c], [("E", "member")])
c2 = grp("r", "offer", "E", "agent", "cosigned_act", cosigners=("B", "C"), consent="one")
run("T2b same, agent", [GM4, c2], [("E", "agent")])
# T3: quorum protocol: the row's need
GQ = dict(GM4, consensus_protocol="quorum")
run("T3 room protocol quorum: A alone admits E with need=1", [GQ, grp("r", "offer", "E", "member", "cosigned_act", cosigners=("E",), need=1)], [("E", "member")])
run("T3b quorum: A alone removes B with need=1", [GQ, grp("r", "unseat", "B", "member", None, need=1)], [("B", "member")])
# T4: a record change installing other policy words as the protocol
for w in ("accord_halt", "quorum", "moderator_election", "self_roster_add"):
    am = grp("am", "offer", (), "record", "cosigned_act", cosigners=("B", "C"), consensus_protocol=w)
    run("T4 change protocol to %s; then A alone removes D (need=1)" % w, [GM4, am, grp("x", "unseat", "D", "member", None, heads=("am",), need=1)], [("D", "member")])
# record change by default_* policy
am = grp("am", "offer", (), "record", "default_content", cosigners=("B", "C"), consensus_protocol="one")
run("T4b change to one under default_content (3 of 4)", [GM4, am, grp("x", "unseat", "D", "member", None, heads=("am",))], [("D", "member")])
