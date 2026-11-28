#!/usr/bin/env python3
"""
check_consent.py: the consent peer set (consent.py; CC 3.3.7, CC 2.7.5, CC 5.2): which grant is in force, which peers
a principal's grants name, and whether a node may send a peer a row of a class, read at a row.

Every case is a hand-written answer, read over the rows as listed and in several arrival orders (every order of up
to six rows, a fixed sample of 240 above that). Each ask is one of
    ("send",  node, peer, class, at_row, now, the grant it moves under or None)
    ("peers", principal, at_row, now, the peer set)
    ("force", grant, at_row, now, whether it is in force)

The groups: a grant moves its classes and not others; a later grant from the same signer to the same peer replaces
the earlier (the default fold); a withdrawal ends it, as a cut (a concurrent withdrawal ends it too); its term ends
it, at the caller's instant; a grant from a key that does not own the node moves nothing; a node with two owners;
a grant by a revoked key (the end rule r86, a key end is a cut, read over the key's own revocation row: the key
view of origin/key-end-retained is not on this branch).

    python3 -I check_consent.py     exit 1 on any difference
"""
import itertools
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import consent as C  # noqa: E402
import key_end as KE  # noqa: E402

ST = C.ST
W, N_, B, AN = C.withdraws, C.note, C.binding, C.announce


def G(*a, fed=False, **kw):
    """A grant held between the two nodes (cohort_scope not federation), unless `fed`: the federation cases below
    announce both parties."""
    return C.grant(*a, fed=fed, **kw)
CAP = "capacity:cpu:v1"
TRC = "trace:complete:v1"


def ob(owner="O", i="b", node="N"):
    return B(i, node, owner)


def rev_by(id, signer, key, ra):
    """A revocation of `key` signed by another key: not the key's own."""
    return C.CK.row(id, "revoke", signer, (), key=key, ra=ra)


S_, P_, F_, BI = "send", "peers", "force", "bilateral"

CASES = [
    # ---- a grant moves its classes and not others ----
    ("a node's own grant moves the classes it names, by namespace prefix, and nothing else",
     [G("g", "N", "P", ("capacity:",), 1), N_("n", "N", ("g",))],
     [(S_, "N", "P", CAP, "n", None, "g"), (S_, "N", "P", TRC, "n", None, None),
      (S_, "N", "P", "capacity", "n", None, None), (S_, "N", "Q", CAP, "n", None, None),
      (P_, "N", "n", None, {"P"})]),
    ("the trailing colon is significant: 'trace:' does not cover trace_summary, and a corpus class covers itself only",
     [G("g", "N", "P", ("post", "trace:"), 1), N_("n", "N", ("g",))],
     [(S_, "N", "P", "trace_summary:v1", "n", None, None), (S_, "N", "P", "trace:complete:v1", "n", None, "g"),
      (S_, "N", "P", "post", "n", None, "g"), (S_, "N", "P", "posting", "n", None, None)]),
    ("a grant to P moves nothing to Q, and the reverse direction is a grant of its own",
     [G("g", "N", "P", ("capacity:",), 1), G("h", "P", "N", ("observation:",), 1), N_("n", "N", ("g", "h"))],
     [(S_, "N", "Q", CAP, "n", None, None), (S_, "P", "N", "observation:reachability:v1", "n", None, "h"),
      (S_, "P", "N", CAP, "n", None, None), (P_, "N", "n", None, {"P"}), (P_, "P", "n", None, {"N"})]),
    ("a grant whose classes are not a sorted set is malformed and concludes nothing",
     [G("g", "N", "P", ("trace:", "capacity:"), 1), N_("n", "N", ("g",))],
     [(S_, "N", "P", CAP, "n", None, None), (F_, "g", "n", None, False)]),
    ("a grant not in the reading row's past is not read there; it is at a row that has it",
     [N_("n0", "N"), G("g", "N", "P", ("capacity:",), 1, ("n0",)), N_("n1", "N", ("g",))],
     [(S_, "N", "P", CAP, "n0", None, None), (S_, "N", "P", CAP, "n1", None, "g"), (F_, "g", "n0", None, False)]),

    # ---- the default fold: a later grant from the same signer to the same peer replaces the earlier ----
    ("a narrowing supersedes the grant: the later grant's classes are the ones that move",
     [G("g1", "N", "P", ("capacity:", "trace:"), 1), G("g2", "N", "P", ("capacity:",), 2, ("g1",)),
      N_("n", "N", ("g2",))],
     [(S_, "N", "P", TRC, "n", None, None), (S_, "N", "P", CAP, "n", None, "g2"),
      (F_, "g1", "n", None, False), (F_, "g2", "n", None, True)]),
    ("before the narrowing is held, the earlier grant is in force",
     [G("g1", "N", "P", ("capacity:", "trace:"), 1), N_("n", "N", ("g1",)), G("g2", "N", "P", ("capacity:",), 2, ("g1",))],
     [(S_, "N", "P", TRC, "n", None, "g1"), (F_, "g1", None, None, False), (F_, "g2", None, None, True)]),
    ("two concurrent grants to one peer: the later asserted_at wins, whatever arrives first",
     [G("g1", "N", "P", ("trace:",), 3), G("g2", "N", "P", ("capacity:",), 2), N_("n", "N", ("g1", "g2"))],
     [(S_, "N", "P", TRC, "n", None, "g1"), (S_, "N", "P", CAP, "n", None, None)]),
    ("a tie on asserted_at goes to the lowest id",
     [G("ga", "N", "P", ("trace:",), 2), G("gb", "N", "P", ("capacity:",), 2), N_("n", "N", ("ga", "gb"))],
     [(S_, "N", "P", TRC, "n", None, "ga"), (S_, "N", "P", CAP, "n", None, None)]),
    ("causality beats the instant: a narrowing that names the grant replaces it though it states an earlier instant",
     [G("g1", "N", "P", ("capacity:", "trace:"), 5), G("g2", "N", "P", ("capacity:",), 1, ("g1",)),
      N_("n", "N", ("g2",))],
     [(S_, "N", "P", TRC, "n", None, None), (S_, "N", "P", CAP, "n", None, "g2"), (F_, "g1", "n", None, False)]),
    ("no silent drop: a narrower grant that names no grant and states an earlier instant narrows nothing",
     [G("g1", "N", "P", ("capacity:", "trace:"), 5), G("g2", "N", "P", ("capacity:",), 1), N_("n", "N", ("g1", "g2"))],
     [(S_, "N", "P", TRC, "n", None, "g1"), (F_, "g2", "n", None, False)]),
    ("a grant in another's past drops out before any instant is read; the instant orders what is left",
     [G("g1", "N", "P", ("post",), 9), G("g2", "N", "P", ("trace:",), 1, ("g1",)), G("g3", "N", "P", ("capacity:",), 3),
      N_("n", "N", ("g2", "g3"))],
     [(S_, "N", "P", CAP, "n", None, "g3"), (S_, "N", "P", "post", "n", None, None),
      (S_, "N", "P", TRC, "n", None, None)]),
    ("grants to two peers are two chains: neither replaces the other",
     [G("g1", "N", "P", ("trace:",), 1), G("g2", "N", "Q", ("capacity:",), 2), N_("n", "N", ("g1", "g2"))],
     [(S_, "N", "P", TRC, "n", None, "g1"), (S_, "N", "Q", CAP, "n", None, "g2"), (P_, "N", "n", None, {"P", "Q"})]),

    # ---- a withdrawal ends it, as a cut ----
    ("a withdrawal in the reading row's past ends the grant",
     [G("g", "N", "P", ("capacity:",), 1), W("w", "N", "g"), N_("n", "N", ("w",))],
     [(S_, "N", "P", CAP, "n", None, None), (P_, "N", "n", None, set()), (F_, "g", "n", None, False)]),
    ("a row before the withdrawal still reads the grant",
     [G("g", "N", "P", ("capacity:",), 1), N_("n", "N", ("g",)), W("w", "N", "g", ("n",))],
     [(S_, "N", "P", CAP, "n", None, "g"), (F_, "g", None, None, False)]),
    ("a withdrawal concurrent with the reading row ends the grant there too (the end is a cut, rule 4)",
     [G("g", "N", "P", ("capacity:",), 1), N_("n", "N", ("g",)), W("w", "N", "g")],
     [(S_, "N", "P", CAP, "n", None, None), (F_, "g", "n", None, False)]),
    ("a recants ends it as a withdraws does",
     [G("g", "N", "P", ("capacity:",), 1), W("w", "N", "g", kind="recants"), N_("n", "N", ("w",))],
     [(S_, "N", "P", CAP, "n", None, None)]),
    ("the peer's withdrawal ends the grant: stop sending to me (CC 2.4.1.1 rule 2)",
     [G("g", "N", "P", ("capacity:",), 1), W("wp", "P", "g"), N_("n", "N", ("wp",))],
     [(S_, "N", "P", CAP, "n", None, None), (F_, "g", "n", None, False)]),
    ("a third key's withdrawal concludes nothing and ends nothing",
     [G("g", "N", "P", ("capacity:",), 1), W("wx", "X", "g"), N_("n", "N", ("wx",))],
     [(S_, "N", "P", CAP, "n", None, "g"), (F_, "g", "n", None, True)]),
    ("the owner of the grant's signer withdraws the node's own grant (the owner's word governs)",
     ob() + [G("gn", "N", "P", ("capacity:",), 1), W("wo", "O", "gn", ("ab",)), N_("n", "N", ("wo",))],
     [(S_, "N", "P", CAP, "n", None, None), (F_, "gn", "n", None, False)]),
    ("the owner is read at the withdrawal: one that does not have the binding in its past concludes nothing",
     ob() + [G("gn", "N", "P", ("capacity:",), 1), W("wo", "O", "gn"), N_("n", "N", ("wo", "ab"))],
     [(S_, "N", "P", CAP, "n", None, "gn")]),
    ("a former owner's withdrawal ends nothing: its acceptance was withdrawn in the withdrawal's past",
     ob() + [ST.withdraw("wb", "O", "ab"), G("gn", "N", "P", ("capacity:",), 1), W("wo", "O", "gn", ("wb",)),
             N_("n", "N", ("wo",))],
     [(S_, "N", "P", CAP, "n", None, "gn")]),
    ("the owner withdraws its own grant for its node as its signer",
     ob() + [G("go", "O", "P", ("capacity:",), 1), W("wo", "O", "go"), N_("n", "N", ("ab", "wo"))],
     [(S_, "N", "P", CAP, "n", None, None)]),
    ("withdrawing the narrowing revives no earlier grant",
     [G("g1", "N", "P", ("capacity:", "trace:"), 1), G("g2", "N", "P", ("capacity:",), 2, ("g1",)),
      W("w", "N", "g2"), N_("n", "N", ("w",))],
     [(S_, "N", "P", TRC, "n", None, None), (S_, "N", "P", CAP, "n", None, None), (P_, "N", "n", None, set())]),
    ("a new grant after a withdrawal is in force",
     [G("g1", "N", "P", ("capacity:",), 1), W("w", "N", "g1"), G("g2", "N", "P", ("trace:",), 3, ("w",)),
      N_("n", "N", ("g2",))],
     [(S_, "N", "P", TRC, "n", None, "g2"), (S_, "N", "P", CAP, "n", None, None)]),
    ("withdrawing an earlier, replaced grant leaves the later one in force",
     [G("g1", "N", "P", ("capacity:",), 1), G("g2", "N", "P", ("capacity:",), 2, ("g1",)), W("w", "N", "g1", ("g2",)),
      N_("n", "N", ("w",))],
     [(S_, "N", "P", CAP, "n", None, "g2")]),

    # ---- the term ends it, at the caller's instant ----
    ("a term: in force before valid_until, ended at it (half-open), and not read without an instant",
     [G("g", "N", "P", ("capacity:",), 1, until=5), N_("n", "N", ("g",))],
     [(S_, "N", "P", CAP, "n", 4, "g"), (S_, "N", "P", CAP, "n", 5, None), (S_, "N", "P", CAP, "n", None, None),
      (P_, "N", "n", 4, {"P"}), (P_, "N", "n", 6, set())]),
    ("a lapsed latest grant revives no earlier one",
     [G("g1", "N", "P", ("trace:",), 1), G("g2", "N", "P", ("capacity:",), 2, ("g1",), until=4), N_("n", "N", ("g2",))],
     [(S_, "N", "P", TRC, "n", 3, None), (S_, "N", "P", CAP, "n", 3, "g2"), (S_, "N", "P", TRC, "n", 4, None),
      (S_, "N", "P", CAP, "n", 4, None)]),
    ("a term renewed by a later grant",
     [G("g1", "N", "P", ("capacity:",), 1, until=4), G("g2", "N", "P", ("capacity:",), 3, ("g1",), until=8),
      N_("n", "N", ("g2",))],
     [(S_, "N", "P", CAP, "n", 6, "g2"), (S_, "N", "P", CAP, "n", 8, None)]),

    # ---- the owner: a grant from a key that does not own the node moves nothing ----
    ("the owner's grant moves the node's rows; a third key's grant moves nothing",
     ob() + [G("go", "O", "P", ("capacity:",), 1), G("gx", "X", "Q", ("capacity:",), 1),
             N_("n", "N", ("ab", "go", "gx"))],
     [(S_, "N", "P", CAP, "n", None, "go"), (S_, "N", "Q", CAP, "n", None, None),
      (P_, "X", "n", None, {"Q"})]),
    ("with no owner binding, the would-be owner's grant moves nothing",
     [G("go", "O", "P", ("capacity:",), 1), N_("n", "N", ("go",))],
     [(S_, "N", "P", CAP, "n", None, None)]),
    ("an owner binding not accepted by the owner gives no owner",
     [ST.offer("b", "N", "O", "owner", "N", "self"), G("go", "O", "P", ("capacity:",), 1), N_("n", "N", ("b", "go"))],
     [(S_, "N", "P", CAP, "n", None, None)]),
    ("the owner's grant moves nothing at a row that does not have the binding in its past",
     ob() + [G("go", "O", "P", ("capacity:",), 1), N_("n0", "N", ("go",)), N_("n1", "N", ("n0", "ab"))],
     [(S_, "N", "P", CAP, "n0", None, None), (S_, "N", "P", CAP, "n1", None, "go")]),
    ("after the owner's acceptance is withdrawn, the former owner's grant moves nothing; the node's own still does",
     ob() + [G("go", "O", "P", ("capacity:",), 1), G("gn", "N", "Q", ("trace:",), 1),
             ST.withdraw("wb", "O", "ab"), N_("n", "N", ("wb", "go", "gn"))],
     [(S_, "N", "P", CAP, "n", None, None), (S_, "N", "Q", TRC, "n", None, "gn")]),
    ("a grant by the owner to the peer covers what the node's own grant to it does not",
     ob() + [G("go", "O", "P", ("capacity:",), 1), G("gn", "N", "P", ("trace:",), 1), N_("n", "N", ("ab", "go", "gn"))],
     [(S_, "N", "P", CAP, "n", None, "go"), (S_, "N", "P", TRC, "n", None, "gn"), (S_, "N", "P", "x:y", "n", None, None)]),

    # ---- a node owned by two principals: two owners is none ----
    ("two live owner bindings: neither owner's grant moves the node's rows; the node's own grant does",
     ob("O1", "b1") + ob("O2", "b2") + [G("g1", "O1", "P", ("capacity:",), 1), G("g2", "O2", "Q", ("capacity:",), 1),
                                         G("gn", "N", "R", ("capacity:",), 1), N_("n", "N", ("ab1", "ab2", "g1", "g2", "gn"))],
     [(S_, "N", "P", CAP, "n", None, None), (S_, "N", "Q", CAP, "n", None, None), (S_, "N", "R", CAP, "n", None, "gn")]),
    ("two owner bindings, one withdrawn by its owner: the other owner's grant moves the node's rows",
     ob("O1", "b1") + ob("O2", "b2") + [ST.withdraw("w2", "O2", "ab2"), G("g1", "O1", "P", ("capacity:",), 1),
                                         N_("n", "N", ("ab1", "w2", "g1"))],
     [(S_, "N", "P", CAP, "n", None, "g1")]),

    # ---- a grant by a revoked key (r86: a key end is a cut) ----
    ("the owner's grant before its key's revocation keeps its voice; one after it is no grant",
     ob() + [G("g1", "O", "P", ("capacity:",), 1), KE.revoke("rv", "O", 3), G("g2", "O", "Q", ("capacity:",), 5),
             N_("n", "N", ("ab", "g1", "g2", "rv"))],
     [(S_, "N", "P", CAP, "n", None, "g1"), (S_, "N", "Q", CAP, "n", None, None)]),
    ("a revoked key's grant that names its revocation is no grant, and does not displace the earlier one",
     [G("g1", "N", "P", ("capacity:",), 1), KE.revoke("rv", "N", 3), G("g2", "N", "P", ("trace:",), 2, ("rv",)),
      N_("n", "N", ("g1", "g2"))],
     [(S_, "N", "P", CAP, "n", None, "g1"), (S_, "N", "P", TRC, "n", None, None)]),
    ("a revocation by another key than the signer's does not end its voice",
     [G("g1", "N", "P", ("capacity:",), 5), rev_by("rv", "X", "N", 3), N_("n", "N", ("g1",))],
     [(S_, "N", "P", CAP, "n", None, "g1")]),

    # ---- G -> P and P -> G are independent; bilateral is both in force ----
    ("two directions, two grants: withdrawing N -> P leaves P -> N, and the peering is no longer bilateral",
     [G("gNP", "N", "P", ("capacity:",), 1), G("gPN", "P", "N", ("observation:",), 1), N_("n0", "N", ("gNP", "gPN")),
      W("w", "N", "gNP", ("n0",)), N_("n1", "N", ("w",))],
     [(BI, "N", "P", "n0", None, True), (BI, "N", "P", "n1", None, False),
      (S_, "P", "N", "observation:reachability:v1", "n1", None, "gPN"), (S_, "N", "P", CAP, "n1", None, None)]),
    ("one direction alone is not bilateral",
     [G("gNP", "N", "P", ("capacity:",), 1), N_("n", "N", ("gNP",))],
     [(BI, "N", "P", "n", None, False), (BI, "P", "N", "n", None, False), (S_, "N", "P", CAP, "n", None, "gNP")]),

    # ---- a grant an unannounced node signs or is named in is never at federation scope ----
    ("at federation scope, both parties announced in the grant's past: the grant concludes",
     [AN("aN", "N"), AN("aP", "P"), G("g", "N", "P", ("capacity:",), 1, ("aN", "aP"), fed=True), N_("n", "N", ("g",))],
     [(S_, "N", "P", CAP, "n", None, "g")]),
    ("at federation scope, signed by an unannounced node: the grant concludes nothing",
     [AN("aP", "P"), G("g", "N", "P", ("capacity:",), 1, ("aP",), fed=True), N_("n", "N", ("g",))],
     [(S_, "N", "P", CAP, "n", None, None), (F_, "g", "n", None, False)]),
    ("at federation scope, naming an unannounced peer: the grant concludes nothing; held between the two, it does",
     [AN("aN", "N"), G("gf", "N", "P", ("capacity:",), 1, ("aN",), fed=True),
      G("gt", "N", "Q", ("capacity:",), 1, ("aN",)), N_("n", "N", ("gf", "gt"))],
     [(S_, "N", "P", CAP, "n", None, None), (S_, "N", "Q", CAP, "n", None, "gt")]),
    ("an announcement that is not in the grant's past does not place it at federation",
     [G("g", "N", "P", ("capacity:",), 1, fed=True), AN("aN", "N", ("g",)), AN("aP", "P", ("g",)),
      N_("n", "N", ("aN", "aP"))],
     [(S_, "N", "P", CAP, "n", None, None)]),
]

PLANTS = ("classes_unread", "prefix_no_colon", "fold_earliest", "fold_highest_id", "fold_instant_first",
          "fold_live_only", "withdraw_any_signer", "withdraw_signer_only", "withdraw_owner_now", "withdraw_by_past", "term_unread", "term_closed", "owner_any", "owner_two_one",
          "revoked_unread", "revoked_backdated", "future_grant", "federation_unannounced")


def ask(S, a):
    k = a[0]
    if k == S_:
        _, node, peer, cls, at, now, _w = a
        return C.may_send(S, node, peer, cls, at, now)
    if k == P_:
        _, p, at, now, _w = a
        return set(C.peer_set(S, p, at, now))
    if k == BI:
        _, x, y, at, now, _w = a
        return C.bilateral(S, x, y, at, now)
    _, g, at, now, _w = a
    return C.in_force(S, g, at, now)


def want(a):
    return a[-1]


def answers(S, asks):
    return [ask(S, a) for a in asks]


def orders(rows, seed):
    if len(rows) <= 6:
        return itertools.permutations(rows)
    rnd = random.Random(seed)
    out = []
    for _ in range(240):
        p = list(rows)
        rnd.shuffle(p)
        out.append(p)
    return out


def run_case(name, rows, asks, plant=None, arrive_all=True):
    saved = set(C.MUT)
    if plant:
        C.MUT.add(plant)
    try:
        got = answers(C.state(rows), asks)
        bad, i = [], -1
        if arrive_all:
            for i, p in enumerate(orders(rows, len(name))):
                if answers(C.arrived(p), asks) != got:
                    bad.append([r["id"] for r in p])
                    break
        return got, bad, i + 1
    finally:
        C.MUT.clear(); C.MUT |= saved


def fixture():
    """The case table for the crate (tools/kernel_fixtures.py writes it to tests/fixtures/consent.json): each case's
    rows, and each ask with the model's answer. A send ask carries the node's one owner at its reading row as
    seat.Seats reads it (the crate takes the owner from the caller: Seats::one("owner", node) over that row's past)."""
    out = []
    for name, rows, asks in CASES:
        S = C.state(rows)
        js = []
        for a, got in zip(asks, answers(S, asks)):
            if a[0] == S_:
                _, node, peer, cls, at, now, _w = a
                js.append({"ask": "send", "node": node, "peer": peer, "class": cls, "at": at, "now": now,
                           "owner": C.owner(S, node, at), "want": got})
            elif a[0] == BI:
                _, x, y, at, now, _w = a
                js.append({"ask": "bilateral", "a": x, "b": y, "at": at, "now": now, "want": got})
            elif a[0] == P_:
                _, p, at, now, _w = a
                js.append({"ask": "peers", "principal": p, "at": at, "now": now, "want": sorted(got)})
            else:
                _, g, at, now, _w = a
                js.append({"ask": "force", "grant": g, "at": at, "now": now, "want": got})
        out.append({"name": name, "rows": [_row_json(r, S) for r in rows], "asks": js})
    return {"source": "models/causal_kernel/check_consent.py", "cases": out}


def _row_json(r, S):
    k = r["kind"]
    j = {"id": r["id"], "signer": r["signer"], "names": list(r["names"])}
    if k == "grant":
        j.update(kind="grant", peer=r["peer"], classes=list(r["classes"]), at=r["at"], until=r["until"],
                 federation=r.get("fed", True))
    elif k in C.ENDS:
        # the owner of the withdrawn grant's signer over the withdrawal's concluded past (the crate takes it from
        # the caller: Seats::one("owner", signer) over that past)
        g = S.by.get(r["of"])
        P = [q for q in S.rows if q["id"] in S.anc.get(r["id"], ()) and S.C.get(q["id"])]
        j.update(kind="withdrawal", of=r["of"], owner_of_signer=C._owner_over(P, g["signer"]) if g else None)
    elif k == "revoke":
        j.update(kind="revocation", key=r["key"], ra=r["ra"])
    elif k == "announce":
        j.update(kind="announcement")
    else:
        j.update(kind="other")
    return j


def main():
    problems, n_orders, n_asks = [], 0, 0
    for name, rows, asks in CASES:
        got, bad, n = run_case(name, rows, asks)
        n_orders += n
        n_asks += len(asks)
        exp = [want(a) for a in asks]
        if got != exp:
            problems.append("%s: got %s, expected %s" % (name, got, exp))
        if bad:
            problems.append("%s: order %s differs" % (name, bad[0]))
    caught = 0
    for plant in PLANTS:
        hit = [name for name, rows, asks in CASES
               if run_case(name, rows, asks, plant, arrive_all=False)[0] != [want(a) for a in asks]]
        caught += bool(hit)
        print("  plant %-20s %s" % (plant, "caught by %d cases, first: %s" % (len(hit), hit[0]) if hit else "NOT CAUGHT"))
        if not hit:
            problems.append("plant %s not caught" % plant)
    for p in problems:
        print(p)
    print("RESULT: %s: %d cases, %d answers, %d orders, %d of %d planted breaks caught"
          % ("ok" if not problems else "%d problems" % len(problems), len(CASES), n_asks, n_orders, caught, len(PLANTS)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
