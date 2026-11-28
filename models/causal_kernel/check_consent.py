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
a grant by a revoked, stolen or rotated key, read through the key view (key_end.counts_by, the end rule every count
reads: a key end is a cut), for no reader or for the reader a case names (READERS). The instant a grant states
never helps it against an end.

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


def rev(id, key, ra, names=()):
    """A key's own revocation naming the key's last rows (the caller duty of an honest revocation)."""
    return C.CK.row(id, "revoke", key, tuple(names), key=key, ra=ra)


def found_self(i, k):
    """A self roster founded by its first key (seat: a person's own key roster)."""
    return ST.offer(i, k, (k,), "self", "@", "self")


def add_self(i, roster, k, signer, heads):
    """A key added to a self roster by its count (self_roster_add), the key signing its own seat."""
    return ST.offer(i, signer, k, "self", roster, "group", tuple(heads), head=tuple(heads), policy="self_roster_add",
                    counted="self", cosigners=(k,))


def evict_self(i, roster, k, signers, heads):
    """A key evicted from a self roster by its count (self_roster_evict)."""
    return ST.unseat(i, signers[0], k, "self", roster, "group", tuple(heads), head=tuple(heads), policy="self_roster_evict",
                     counted="self", cosigners=tuple(signers[1:]))


def rev_by(id, signer, key, ra):
    """A revocation of `key` signed by another key: not the key's own."""
    return C.CK.row(id, "revoke", signer, (), key=key, ra=ra)


S_, P_, F_, BI = "send", "peers", "force", "bilateral"

# A3: N owned by O; O's key stolen and revoked (its last row g0 named); the thief's grant gt to A, concurrent with the
# revocation, taken up by N's row n. A3 with O's self roster and a second device O2; A3_ONE with O's key alone.
_A3 = lambda: [G("g0", "O", "Q", ("x:",), 1, ("ab",)), rev("rv", "O", 3, ("g0",)), G("gt", "O", "A", ("trace:",), 1, ("g0",)),
               N_("n", "N", ("ab", "gt"))]

PE = [found_self("SO", "O"), add_self("aO2", "SO", "O2", "O", ("SO",)),
      ST.offer("aO3", "O", "O3", "self", "SO", "group", ("aO2",), head=("aO2",), policy="self_roster_add", counted="self",
               cosigners=("O2", "O3")), G("g", "O", "P", ("trace:",), 1, ("aO3",))]
PE_EV = evict_self("ev", "SO", "O2", ("O", "O3"), ("aO3",))
A3_ONE = C.binding("b", "N", "O") + _A3()
A3 = C.binding("b", "N", "O") + [found_self("SO", "O"), add_self("aO2", "SO", "O2", "O", ("SO",))] + _A3()

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
    ("a row beats what its past beat: g1 beat the concurrent g3 by instant, so g2, which names g1, beats g3 too",
     [G("g1", "N", "P", ("post",), 9), G("g2", "N", "P", ("trace:",), 1, ("g1",)), G("g3", "N", "P", ("capacity:",), 3),
      N_("n", "N", ("g2", "g3"))],
     [(S_, "N", "P", TRC, "n", None, "g2"), (S_, "N", "P", "post", "n", None, None),
      (S_, "N", "P", CAP, "n", None, None)]),
    ("r97 CF1: a fork, the winner withdrawn, and a regrant naming the withdrawal: the beaten branch is not revived",
     [G("g3", "N", "P", ("capacity:", "trace:"), 4), G("g2", "N", "P", ("capacity:",), 5), W("w", "N", "g2"),
      G("g4", "N", "P", ("capacity:",), 3, ("w",)), N_("n", "N", ("g3", "g4"))],
     [(S_, "N", "P", TRC, "n", None, None), (S_, "N", "P", CAP, "n", None, "g4")]),
    ("CF2: the same before the regrant: nothing moves (the withdrawn winner revives no beaten branch)",
     [G("g3", "N", "P", ("capacity:", "trace:"), 4), G("g2", "N", "P", ("capacity:",), 5), W("w", "N", "g2"),
      N_("n", "N", ("g3", "w"))],
     [(S_, "N", "P", TRC, "n", None, None), (S_, "N", "P", CAP, "n", None, None)]),
    ("A6b: a far-future instant on a grant concurrent with another, neither named nor withdrawn, wins among them "
     "(asserted_at orders concurrent rows of one signer: the signer's own word)",
     [G("g9", "N", "P", ("x:",), 10 ** 18), G("g2", "N", "P", ("capacity:",), 7), N_("n", "N", ("g2", "g9"))],
     [(S_, "N", "P", CAP, "n", None, None), (S_, "N", "P", "x:y", "n", None, "g9")]),
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
    ("A5: an honest regrant after a withdrawal takes effect though it states an earlier instant than the withdrawn grant",
     [G("g1", "N", "P", ("capacity:",), 5), W("w", "N", "g1"), G("g2", "N", "P", ("trace:",), 3, ("w",)),
      N_("n", "N", ("g2",))],
     [(S_, "N", "P", TRC, "n", None, "g2"), (S_, "N", "P", CAP, "n", None, None)]),
    ("A6: a regrant after the peer's withdrawal takes effect whatever its instant",
     [G("g1", "N", "P", ("capacity:",), 5), W("wp", "P", "g1"), G("g2", "N", "P", ("capacity:",), 1, ("wp",)),
      N_("n", "N", ("g2",))],
     [(S_, "N", "P", CAP, "n", None, "g2")]),
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
    ("A7: the owner is read at the reading row: a grant O made before it owned N moves nothing at a row without the "
     "binding, and moves N's rows once the binding is in the reading row's past",
     ob() + [G("go", "O", "P", ("capacity:",), 1), N_("n0", "N", ("go",)), N_("n1", "N", ("n0", "ab"))],
     [(S_, "N", "P", CAP, "n0", None, None), (S_, "N", "P", CAP, "n1", None, "go")]),
    ("after the owner's acceptance is withdrawn, the former owner's grant moves nothing; the node's own still does",
     ob() + [G("go", "O", "P", ("capacity:",), 1), G("gn", "N", "Q", ("trace:",), 1),
             ST.withdraw("wb", "O", "ab"), N_("n", "N", ("wb", "go", "gn"))],
     [(S_, "N", "P", CAP, "n", None, None), (S_, "N", "Q", TRC, "n", None, "gn")]),
    ("a grant by the owner to the peer covers what the node's own grant to it does not",
     ob() + [G("go", "O", "P", ("capacity:",), 1), G("gn", "N", "P", ("trace:",), 1), N_("n", "N", ("ab", "go", "gn"))],
     [(S_, "N", "P", CAP, "n", None, "go"), (S_, "N", "P", TRC, "n", None, "gn"), (S_, "N", "P", "x:y", "n", None, None)]),

    # ---- a re-binding moves the owner (the one owner reading, seat.Seats.owner) ----
    ("a re-binding moves the owner: O2's grant moves N's rows and O1's no longer does",
     ob("O1", "b1") + [ST.offer("b2", "N", "O2", "owner", "N", "self", ("ab1",)), ST.accept("ab2", "O2", "b2"),
                       G("g1", "O1", "P", ("capacity:",), 1), G("g2", "O2", "Q", ("capacity:",), 1),
                       N_("n", "N", ("ab2", "g1", "g2"))],
     [(S_, "N", "P", CAP, "n", None, None), (S_, "N", "Q", CAP, "n", None, "g2")]),
    ("before the re-binding is in the reading row's past, the first owner's grant moves N's rows",
     ob("O1", "b1") + [G("g1", "O1", "P", ("capacity:",), 1), N_("n0", "N", ("ab1", "g1")),
                       ST.offer("b2", "N", "O2", "owner", "N", "self", ("n0",)), ST.accept("ab2", "O2", "b2"),
                       N_("n1", "N", ("ab2",))],
     [(S_, "N", "P", CAP, "n0", None, "g1"), (S_, "N", "P", CAP, "n1", None, None)]),
    ("a re-binding not yet accepted ends the first binding: no owner until the new owner accepts",
     ob("O1", "b1") + [ST.offer("b2", "N", "O2", "owner", "N", "self", ("ab1",)), G("g1", "O1", "P", ("capacity:",), 1),
                       G("g2", "O2", "P", ("trace:",), 1), N_("n", "N", ("b2", "g1", "g2"))],
     [(S_, "N", "P", CAP, "n", None, None), (S_, "N", "P", TRC, "n", None, None)]),
    ("the re-bound owner withdraws the node's grant; the former owner's withdrawal concludes nothing",
     ob("O1", "b1") + [ST.offer("b2", "N", "O2", "owner", "N", "self", ("ab1",)), ST.accept("ab2", "O2", "b2"),
                       G("gn", "N", "P", ("capacity:",), 1), G("gm", "N", "Q", ("capacity:",), 1),
                       W("w2", "O2", "gn", ("ab2",)), W("w1", "O1", "gm", ("ab2",)), N_("n", "N", ("w1", "w2"))],
     [(S_, "N", "P", CAP, "n", None, None), (S_, "N", "Q", CAP, "n", None, "gm")]),

    # ---- a node owned by two principals: two owners is none ----
    ("two live owner bindings: neither owner's grant moves the node's rows; the node's own grant does",
     ob("O1", "b1") + ob("O2", "b2") + [G("g1", "O1", "P", ("capacity:",), 1), G("g2", "O2", "Q", ("capacity:",), 1),
                                         G("gn", "N", "R", ("capacity:",), 1), N_("n", "N", ("ab1", "ab2", "g1", "g2", "gn"))],
     [(S_, "N", "P", CAP, "n", None, None), (S_, "N", "Q", CAP, "n", None, None), (S_, "N", "R", CAP, "n", None, "gn")]),
    ("two owner bindings, one withdrawn by its owner: the other owner's grant moves the node's rows",
     ob("O1", "b1") + ob("O2", "b2") + [ST.withdraw("w2", "O2", "ab2"), G("g1", "O1", "P", ("capacity:",), 1),
                                         N_("n", "N", ("ab1", "w2", "g1"))],
     [(S_, "N", "P", CAP, "n", None, "g1")]),

    # ---- a grant by a revoked, stolen or rotated key: the key view (a key end is a cut) ----
    ("an honest revocation names the key's last rows: the owner's grant in its past keeps its voice; one after it is "
     "no grant",
     ob() + [G("g1", "O", "P", ("capacity:",), 1), rev("rv", "O", 3, ("g1",)), G("g2", "O", "Q", ("capacity:",), 5, ("rv",)),
             N_("n", "N", ("ab", "g1", "g2"))],
     [(S_, "N", "P", CAP, "n", None, "g1"), (S_, "N", "Q", CAP, "n", None, None)]),
    ("A1: a thief's grant concurrent with the revocation, back-dated before revoked_after, is no grant",
     [G("g1", "N", "P", ("capacity:",), 1), rev("rv", "N", 3, ("g1",)),
      G("gt", "N", "A", ("capacity:", "trace:"), 2), N_("n", "P", ("rv", "gt"))],
     [(S_, "N", "A", TRC, "n", None, None), (S_, "N", "P", CAP, "n", None, "g1"), (P_, "N", "n", None, {"P"})]),
    ("A2: a thief's back-dated grant to the same peer neither broadens nor displaces the honest one",
     [G("g1", "N", "P", ("capacity:",), 1), rev("rv", "N", 3, ("g1",)),
      G("gt", "N", "P", ("capacity:", "trace:"), 2), N_("n", "P", ("rv", "gt"))],
     [(S_, "N", "P", TRC, "n", None, None), (S_, "N", "P", CAP, "n", None, "g1")]),
    ("A3: the owner's key revoked: its thief's grant concurrent with the revocation moves none of the node's rows",
     ob() + [KE.revoke("rv", "O", 3), G("gt", "O", "A", ("trace:",), 1), N_("n", "N", ("ab", "gt", "rv"))],
     [(S_, "N", "A", TRC, "n", None, None)]),
    ("a grant the reader took up before it held the revocation stands for that reader (taken up on its line)",
     [G("gt", "N", "P", ("capacity:",), 2), N_("n0", "P", ("gt",)), KE.revoke("rv", "N", 3), N_("n", "P", ("n0", "rv"))],
     [(S_, "N", "P", CAP, "n", None, "gt")]),
    ("the same grant for a reader that never took it up: no grant",
     [G("gt", "N", "P", ("capacity:",), 2), N_("n0", "P", ("gt",)), KE.revoke("rv", "N", 3), N_("n", "P", ("n0", "rv"))],
     [(S_, "N", "P", CAP, "n", None, None)]),
    ("a rotation ends the old key: its grant in the rotation's past stands, one concurrent with it is no grant",
     [KE.rec("r1", "N", 0, None, typ="pseudonym"), G("g1", "N", "P", ("capacity:",), 1, ("r1",)),
      KE.rec("r2", "N2", 2, None, names=("r1", "g1"), succ_of="N", at_old=2, typ="pseudonym"),
      G("gt", "N", "Q", ("capacity:",), 3, ("r1",)), N_("n", "P", ("r2", "gt"))],
     [(S_, "N", "P", CAP, "n", None, "g1"), (S_, "N", "Q", CAP, "n", None, None)]),
    ("the owner withdraws a revoked node's grant, and it ends",
     ob() + [G("gn", "N", "P", ("capacity:",), 1), rev("rv", "N", 3, ("gn",)),
             W("wo", "O", "gn", ("ab", "rv")), N_("n", "O", ("wo",))],
     [(S_, "N", "P", CAP, "n", None, None), (F_, "gn", "n", None, False)]),
    ("a revocation by another key than the signer's does not end its voice",
     [G("g1", "N", "P", ("capacity:",), 5), rev_by("rv", "X", "N", 3), N_("n", "N", ("g1",))],
     [(S_, "N", "P", CAP, "n", None, "g1")]),

    # ---- r97: the reader's own line (K1), a former owner (F1 to F3), named parties (P1, P2), announcements (AN) ----
    ("r97 K1: a thief holding N's key grants and signs a note as N naming it: for reader N the note is no row of its "
     "line, and the grant moves nothing",
     [G("g1", "N", "P", ("capacity:",), 1), rev("rv", "N", 3, ("g1",)), G("gt", "N", "A", ("trace:",), 2, ("g1",)),
      N_("nt", "N", ("gt",)), N_("n", "P", ("rv", "nt"))],
     [(S_, "N", "A", TRC, "n", None, None), (S_, "N", "P", CAP, "n", None, "g1")]),
    ("F0: the owner gave up ownership; N's grant still moves N's rows",
     ob() + [G("gn", "N", "P", ("trace:",), 1, ("ab",)), ST.withdraw("wb", "O", "ab", ("gn",)), N_("n", "N", ("wb",))],
     [(S_, "N", "P", TRC, "n", None, "gn")]),
    ("r97 F1: a former owner withdraws N's grant from a past without its own end: the end cuts it, nothing ends",
     ob() + [G("gn", "N", "P", ("trace:",), 1, ("ab",)), ST.withdraw("wb", "O", "ab", ("gn",)), W("wo", "O", "gn"),
             N_("n", "N", ("wb", "wo"))],
     [(S_, "N", "P", TRC, "n", None, "gn")]),
    ("F2: the same withdrawal naming the end: O owns nothing there, nothing ends",
     ob() + [G("gn", "N", "P", ("trace:",), 1, ("ab",)), ST.withdraw("wb", "O", "ab", ("gn",)), W("wo", "O", "gn", ("wb",)),
             N_("n", "N", ("wb", "wo"))],
     [(S_, "N", "P", TRC, "n", None, "gn")]),
    ("r97 F3: N's later grant, not naming O's end, withdrawn by the former owner: cut by the end, it stands",
     ob() + [G("gn", "N", "P", ("trace:",), 1, ("ab",)), ST.withdraw("wb", "O", "ab", ("gn",)),
             G("gn2", "N", "Q", ("trace:",), 2, ("gn",)), W("wo", "O", "gn2"), N_("n", "N", ("wb", "wo", "gn2"))],
     [(S_, "N", "Q", TRC, "n", None, "gn2")]),
    ("the owner's withdrawal before its ownership ends (the end has it in its past) ends the grant",
     ob() + [G("gn", "N", "P", ("trace:",), 1, ("ab",)), W("wo", "O", "gn", ("ab",)),
             ST.withdraw("wb", "O", "ab", ("wo",)), N_("n", "N", ("wb",))],
     [(S_, "N", "P", TRC, "n", None, None)]),
    ("P1: a peer withdraws a grant naming another peer: it is no party of it, nothing ends",
     [G("gq", "N", "Q", ("trace:",), 1), W("wp", "P", "gq"), N_("n", "N", ("wp",))],
     [(S_, "N", "Q", TRC, "n", None, "gq")]),
    ("P2: the peer withdraws the owner's grant to it: it ends for every node the owner owns",
     ob() + ob("O", "c", "M") + [G("go", "O", "P", ("trace:",), 1), W("wp", "P", "go"), N_("n", "N", ("ab", "ac", "wp"))],
     [(S_, "N", "P", TRC, "n", None, None), (S_, "M", "P", TRC, "n", None, None)]),
    ("AN2: a federation grant to a peer revoked after announcing: the announcement is in the end's past and counts",
     [AN("aN", "N"), AN("aP", "P"), rev("rvp", "P", 1, ("aP",)),
      G("g", "N", "P", ("trace:",), 2, ("aN", "aP", "rvp"), fed=True), N_("n", "N", ("g",))],
     [(S_, "N", "P", TRC, "n", None, "g")]),
    ("r97 AN4: an announcement by a thief of P's key, concurrent with P's revocation, places nothing at federation",
     [AN("aN", "N"), rev("rvp", "P", 1), AN("aP", "P"), G("g", "N", "P", ("trace:",), 2, ("aN", "aP"), fed=True),
      N_("n", "N", ("g",))],
     [(S_, "N", "P", TRC, "n", None, None)]),

    # ---- A3 ruled: the withdrawers are one rule (the signer as a person, any named party, the owner) ----
    ("A3: O's key stolen and revoked; N took up the thief's grant; O's other live device withdraws it, and it ends",
     A3 + [W("w2", "O2", "gt", ("aO2", "n")), N_("n2", "N", ("n", "w2"))],
     [(S_, "N", "A", TRC, "n", None, "gt"), (S_, "N", "A", TRC, "n2", None, None)]),
    ("A3: N's own withdrawal of a grant for N ends it (N a named party: the node the grant is for)",
     A3 + [W("wn", "N", "gt", ("n",)), N_("n2", "N", ("wn",))],
     [(S_, "N", "A", TRC, "n2", None, None)]),
    ("A3, the residual: O with no other live key; the thief's grant stands for the reader that took it up",
     A3_ONE, [(S_, "N", "A", TRC, "n", None, "gt")]),
    ("a key of another person withdraws O's grant: no party of it, nothing ends",
     A3 + [W("wx", "X", "gt", ("aO2", "n")), N_("n2", "N", ("n", "wx"))],
     [(S_, "N", "A", TRC, "n2", None, "gt")]),

    # ---- r103: the person arm is cut by the end of the key as the person's (PE1, PR1) ----
    ("r103 PE1: an evicted device withdraws the person's grant from a past without its eviction: cut, it stands",
     PE + [PE_EV, W("w2", "O2", "g"), N_("n", "O", ("ev", "w2"))],
     [(S_, "O", "P", TRC, "n", None, "g")]),
    ("PE2: the same withdrawal naming its eviction: O2 is no device of O there, it stands",
     PE + [PE_EV, W("w2", "O2", "g", ("ev",)), N_("n", "O", ("ev", "w2"))],
     [(S_, "O", "P", TRC, "n", None, "g")]),
    ("an honest device's withdrawal made before its eviction (the eviction names it) ends the grant",
     PE + [W("w2", "O2", "g", ("g",)), evict_self("ev", "SO", "O2", ("O", "O3"), ("aO3", "w2")), N_("n", "O", ("ev",))],
     [(S_, "O", "P", TRC, "n", None, None)]),
    ("r103 PR1: a device's key revoked; its withdrawal concurrent with the revocation is cut by the key view",
     PE + [rev("rv2", "O2", 5, ("aO3",)), W("w2", "O2", "g"), N_("n", "O", ("rv2", "w2"))],
     [(S_, "O", "P", TRC, "n", None, "g")]),
    ("r103 FD1, the residual: the signer's own concurrent regrants, each naming one fork, settle nothing (fail closed)",
     [G("g1", "N", "P", ("capacity:",), 10), G("h1", "N", "P", ("capacity:",), 10), G("g2", "N", "P", ("capacity:",), 1, ("g1",)),
      G("h2", "N", "P", ("capacity:",), 1, ("h1",)), N_("n", "N", ("g2", "h2"))],
     [(S_, "N", "P", CAP, "n", None, None)]),
    ("and the next regrant naming both settles it",
     [G("g1", "N", "P", ("capacity:",), 10), G("h1", "N", "P", ("capacity:",), 10), G("g2", "N", "P", ("capacity:",), 1, ("g1",)),
      G("h2", "N", "P", ("capacity:",), 1, ("h1",)), G("k", "N", "P", ("trace:",), 1, ("g2", "h2")), N_("n", "N", ("k",))],
     [(S_, "N", "P", TRC, "n", None, "k")]),

    # ---- drift: no instant, a reading row not held ----
    ("a grant stating no asserted_at ranks below one that states one, among concurrent grants",
     [G("ga", "N", "P", ("trace:",)), G("gb", "N", "P", ("capacity:",), 1), N_("n", "N", ("ga", "gb"))],
     [(S_, "N", "P", CAP, "n", None, "gb"), (S_, "N", "P", TRC, "n", None, None)]),
    ("a grant stating no asserted_at, alone, is in force",
     [G("ga", "N", "P", ("trace:",)), N_("n", "N", ("ga",))],
     [(S_, "N", "P", TRC, "n", None, "ga"), (F_, "ga", None, None, True)]),
    ("a reading row that is not held reads nothing",
     [G("g", "N", "P", ("capacity:",), 1)],
     [(S_, "N", "P", CAP, "zz", None, None), (P_, "N", "zz", None, set()), (F_, "g", "zz", None, False),
      (BI, "N", "P", "zz", None, False)]),

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

READERS = {
    "r97 K1: a thief holding N's key grants and signs a note as N naming it: for reader N the note is no row of its "
    "line, and the grant moves nothing": "N",
    "A3: O's key stolen and revoked; N took up the thief's grant; O's other live device withdraws it, and it ends": "N",
    "A3: N's own withdrawal of a grant for N ends it (N a named party: the node the grant is for)": "N",
    "A3, the residual: O with no other live key; the thief's grant stands for the reader that took it up": "N",
    "a key of another person withdraws O's grant: no party of it, nothing ends": "N",
    "a grant the reader took up before it held the revocation stands for that reader (taken up on its line)": "P",
}

PLANTS = ("classes_unread", "prefix_no_colon", "fold_earliest", "fold_highest_id", "fold_instant_first",
          "fold_live_only", "withdraw_any_signer", "withdraw_signer_only", "withdraw_owner_now", "withdraw_by_past", "term_unread", "term_closed", "owner_any", "owner_two_one",
          "revoked_unread", "voice_wrong_key", "withdrawn_none_unread", "future_grant", "federation_unannounced",
          "rebinding_unread", "fold_inherit_unread", "withdraw_person_unread", "withdraw_node_unread",
          "ownership_end_unread", "announcement_unviewed", "person_end_unread")
SEAT_PLANTS = ("rebinding_unread",)       # planted in seat.py: the one owner reading


def ask(S, a, kv):
    k = a[0]
    if k == S_:
        _, node, peer, cls, at, now, _w = a
        return C.may_send(S, node, peer, cls, at, now, kv)
    if k == P_:
        _, p, at, now, _w = a
        return set(C.peer_set(S, p, at, now, kv))
    if k == BI:
        _, x, y, at, now, _w = a
        return C.bilateral(S, x, y, at, now, kv)
    _, g, at, now, _w = a
    return C.in_force(S, g, at, now, kv)


def want(a):
    return a[-1]


def answers(S, asks, reader=None):
    kv = C.key_view(S, reader)
    return [ask(S, a, kv) for a in asks]


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
    saved, saved_st = set(C.MUT), set(ST.MUT)
    if plant in SEAT_PLANTS:
        ST.MUT.add(plant)
    elif plant:
        C.MUT.add(plant)
    try:
        got = answers(C.state(rows), asks, READERS.get(name))
        bad, i = [], -1
        if arrive_all:
            for i, p in enumerate(orders(rows, len(name))):
                if answers(C.arrived(p), asks, READERS.get(name)) != got:
                    bad.append([r["id"] for r in p])
                    break
        return got, bad, i + 1
    finally:
        C.MUT.clear(); C.MUT |= saved
        ST.MUT.clear(); ST.MUT |= saved_st


def readings(S, rows, reader):
    """The readings the crate takes from the caller (consent::Reading), as the model reads them, for every row and
    key of a case: `voiced` [row, signer] where the key view counts the signer's signature on a concluded grant or
    announcement; `persons` "key|row|0" the person map over the row's past, "key|row|1" with the row (seat.rep_of;
    none left out); `owners`
    "key|row|0" over the row's past, "key|row|1" with the row, "key||1" over every held row (seat.Seats.owner; none
    left out)."""
    kv = C.key_view(S, reader)
    voiced = sorted([q["id"], q["signer"]] for q in S.Cs if q["kind"] in ("grant", "announce") and kv(q["id"], q["signer"]))
    keys = sorted({r["signer"] for r in rows} | {r["peer"] for r in rows if r.get("peer")}
                  | {k for r in rows for k in r.get("to", ())} | {k for r in rows for k in r.get("cosigners", ())})
    persons, owners = {}, {}
    for r in S.rows:
        before, incl = C._rows_before(S, r["id"]), C._rows_before(S, r["id"], True)
        for k in keys:
            for f, rs in (("0", before), ("1", incl)):
                p = C.person_over(rs, k)
                if p is not None:
                    persons["%s|%s|%s" % (k, r["id"], f)] = p
                o = C.owner_over(rs, k)
                if o is not None:
                    owners["%s|%s|%s" % (k, r["id"], f)] = o
    for k in keys:
        o = C.owner_over(list(S.Cs), k)
        if o is not None:
            owners["%s||1" % k] = o
    return voiced, persons, owners


def fixture():
    """The case table for the crate (tools/kernel_fixtures.py writes it to tests/fixtures/consent.json): each case's
    rows (`rows`, as the consent view reads them; `model_rows`, the model's own rows, for the end-to-end test over
    the crate's KeyReading, Persons and Seats::owner), the case's reader, the readings the model gives (readings),
    and each ask with the model's answer."""
    out = []
    for name, rows, asks in CASES:
        S = C.state(rows)
        reader = READERS.get(name)
        voiced, persons, owners = readings(S, rows, reader)
        js = []
        for a, got in zip(asks, answers(S, asks, reader)):
            if a[0] == S_:
                _, node, peer, cls, at, now, _w = a
                js.append({"ask": "send", "node": node, "peer": peer, "class": cls, "at": at, "now": now, "want": got})
            elif a[0] == BI:
                _, x, y, at, now, _w = a
                js.append({"ask": "bilateral", "a": x, "b": y, "at": at, "now": now, "want": got})
            elif a[0] == P_:
                _, p, at, now, _w = a
                js.append({"ask": "peers", "principal": p, "at": at, "now": now, "want": sorted(got)})
            else:
                _, g, at, now, _w = a
                js.append({"ask": "force", "grant": g, "at": at, "now": now, "want": got})
        out.append({"name": name, "rows": [_row_json(r) for r in rows], "model_rows": list(rows), "reader": reader,
                    "voiced": voiced, "persons": persons, "owners": owners, "asks": js})
    return {"source": "models/causal_kernel/check_consent.py", "cases": out}


def _row_json(r):
    k = r["kind"]
    j = {"id": r["id"], "signer": r["signer"], "names": list(r["names"])}
    if k == "grant":
        j.update(kind="grant", peer=r["peer"], classes=list(r["classes"]), at=r["at"], until=r["until"],
                 federation=r.get("fed", True))
    elif k in C.ENDS:
        j.update(kind="withdrawal", of=r["of"])
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
