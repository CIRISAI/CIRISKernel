#!/usr/bin/env python3
"""The trust root's fork fold (root.py): cases by rule, and a planted break for each rule.

Each case is (rule, name, bundles, revokes, grants, reader, want), want a dict over:
    concluded   {bundle: True|False}, the bundle's own count (its predecessors concluded)
    void        the set of bundles void by S'' and T
    heads       the reader's bundles in force (None: genesis_bundle_not_anchored)
    holders     the reader's in-force holders; seats likewise
    grant       {grant: (bool, reason)} read against the reader
    row         {grant: bool}, the grant as a row
Run: python3 -I models/trust_root/check_root.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
import root as RT  # noqa: E402

B, RV, GR, RD = RT.bundle, RT.revoke, RT.grant, RT.reader
F = "fam"
H3 = ("h1", "h2", "h3")
H5 = ("h1", "h2", "h3", "h4", "h5")
B0 = B("b0", F, 0, H3, seats=("n1",))
B0_5 = B("b0", F, 0, H5, seats=("n1",))
ANC = RD(anchor="b0")
C1 = {"name": "c1", "duties": ("infra",)}           # another charter carrying the same duty
C2 = {"name": "c2", "duties": ()}                   # a charter that drops the duty


def nxt(i, prev, holders, signers, version=None, charter=RT.C0, seats=("n1",), iat=0, family=F, recovers=None, **kw):
    """A later bundle on `prev` (one id, or a tuple for a join), signed by `signers`."""
    prev = (prev,) if isinstance(prev, str) else tuple(prev)
    return B(i, family, version if version is not None else 1, holders, prev=prev, charter=charter, seats=seats,
             stmts=[(k, iat) for k in signers], iat=iat, recovers=recovers, **kw)


# a linear lineage: b0 (h1 h2 h3) -> b1 (adds h4, by h1 h2) -> b2 (removes h3, by h1 h2 h4 of four)
LIN = [B0, nxt("b1", "b0", H3 + ("h4",), ("h1", "h2")),
       nxt("b2", "b1", ("h1", "h2", "h4"), ("h1", "h2", "h4"), version=2)]
# two successors of b0 with the same charter: s1 adds h4 (h1 h2), s2 adds h5 (h2 h3)
FORK = [B0, nxt("s1", "b0", H3 + ("h4",), ("h1", "h2")), nxt("s2", "b0", H3 + ("h5",), ("h2", "h3"))]
# the same, s2 under another charter
FORKC = [B0, nxt("s1", "b0", H3 + ("h4",), ("h1", "h2")), nxt("s2", "b0", H3 + ("h5",), ("h2", "h3"), charter=C1)]
# a removal on one tip and an addition on the other: s1 removes h3 (h1 h2), s2 adds h5 (h2 h3)
FORKR = [B0, nxt("s1", "b0", ("h1", "h2"), ("h1", "h2")), nxt("s2", "b0", H3 + ("h5",), ("h2", "h3"))]
# a join of FORK's tips, counted over the holders common to them (h1 h2 h3)
JOIN = FORK + [nxt("j", ("s1", "s2"), H3 + ("h4", "h5"), ("h1", "h2"), version=2)]
JOINC = FORKC + [nxt("j", ("s1", "s2"), H3 + ("h4", "h5"), ("h1", "h2"), version=2, charter=C1)]
# a holder's recovery: h3's recovery key r:h3 replaces h3 by h3b
REC = nxt("rc", "b0", ("h1", "h2", "h3b"), ("r:h3",), recovers=("h3", "h3b"),
          recovery={"h1": "r:h1", "h2": "r:h2", "h3b": "r:h3b"})
# an amend concurrent with it: h1 h2 add h4 (same charter), or change the charter
AMD = nxt("am", "b0", H3 + ("h4",), ("h1", "h2"))
AMDC = nxt("am", "b0", H3 + ("h4",), ("h1", "h2"), charter=C1)
# S'' on a forked bundle: h1 and h2 sign s1 at b0, then sign b1 (adds h4) at b0 and b2 on b1, without s1
SFW = [B0, nxt("s1", "b0", H3 + ("h9",), ("h1", "h2")), nxt("b1", "b0", H3 + ("h4",), ("h1", "h2", "h3")),
       nxt("b2", "b1", H3 + ("h4", "h5"), ("h1", "h2", "h4"), version=2)]
# the same where h3 did not sign b1 (b1 by h1 h2 alone): the same voices on both sides, a tie
SFT = [B0, nxt("s1", "b0", H3 + ("h9",), ("h1", "h2")), nxt("b1", "b0", H3 + ("h4",), ("h1", "h2")),
       nxt("b2", "b1", H3 + ("h4", "h5"), ("h1", "h2", "h4"), version=2)]

T, Fa = True, False
CASES = [
    # ---- the count ------------------------------------------------------------------------------------------------
    ("count", "a linear lineage: each bundle counted over its predecessor's holders; the reader that acknowledged b2 "
              "holds b2's holders", LIN, (), (), RD(anchor="b0", acks=("b2",)),
     {"concluded": {"b0": T, "b1": T, "b2": T}, "heads": ("b2",), "holders": {"h1", "h2", "h4"}}),
    ("count", "the first bundle is counted over every holder it lists: two of three do not make it",
     [B("b0", F, 0, H3, stmts=[("h1", 0), ("h2", 0)])], (), (), ANC, {"concluded": {"b0": Fa}, "heads": None}),
    ("count", "a later bundle over a strict majority of its predecessor's holders: one of three is short",
     [B0, nxt("b1", "b0", H3 + ("h4",), ("h1",))], (), (), RD(anchor="b0", acks=("b1",)), {"concluded": {"b1": Fa}}),
    ("count", "counted over the predecessor's holders, not its own: h1 and h4 of b1's four are no count over b0's "
              "three (one of three)", [B0, nxt("b1", "b0", H3 + ("h4", "h5"), ("h1", "h4", "h5"))], (), (), ANC,
     {"concluded": {"b1": Fa}}),
    ("count", "an iat mismatch is Invalid on its own, and the bundle is counted on the rest: h2's statement names "
              "another iat, so h1 alone is one of three", [B0, B("b1", F, 1, H3 + ("h4",), prev=("b0",), seats=("n1",),
                                                               stmts=[("h1", 7), ("h2", 8)], iat=7)], (), (), ANC,
     {"concluded": {"b1": Fa}}),
    ("count", "the same with h3 signing at the payload's iat: two of three", [B0, B("b1", F, 1, H3 + ("h4",), prev=("b0",),
                                                                                  seats=("n1",), stmts=[("h1", 7), ("h2", 8), ("h3", 7)], iat=7)], (), (), ANC,
     {"concluded": {"b1": T}}),
    ("count", "a holder revoked with no bound leaves the live holders: h3 revoked, b1 by h1 and h2 is two of two", [B0, nxt("b1", "b0", H3 + ("h4",), ("h1", "h2"))], (RV("h3"),), (),
     RD(anchor="b0", acks=("b1",)), {"concluded": {"b1": T}, "holders": {"h1", "h2", "h3", "h4"}}),
    ("count", "a revoked holder's statement does not count: h3 revoked, b1 by h1 and h3 is one of two (not more than half)",
     [B0, nxt("b1", "b0", H3 + ("h4",), ("h1", "h3"))], (RV("h3"),), (), ANC, {"concluded": {"b1": Fa}}),
    ("count", "a statement a holder's bound voids does not count: h2 bound at b0, so its statement on b1 is void: h1 "
              "alone is one of three", [B0, nxt("b1", "b0", H3 + ("h4",), ("h1", "h2"))], (RV("h2", bound="b0"),), (),
     ANC, {"concluded": {"b1": Fa}}),
    ("count", "a statement at the bound still counts: h2 bound at b1, b1 by h1 and h2", [B0, nxt("b1", "b0", H3 + ("h4",), ("h1", "h2"))],
     (RV("h2", bound="b1"),), (), ANC, {"concluded": {"b1": T}}),
    ("heads", "version is prev's plus one: a bundle on b0 at version 2 is Invalid", [B0, nxt("b1", "b0", H3, ("h1", "h2"), version=2)],
     (), (), ANC, {"concluded": {"b1": Fa}}),
    ("heads", "family is prev's: a bundle on b0 under another family_key_id is Invalid",
     [B0, nxt("b1", "b0", H3, ("h1", "h2"), family="other")], (), (), ANC, {"concluded": {"b1": Fa}}),
    ("count", "recovery_commitments are keys exactly the holders: a bundle missing h3's is Invalid",
     [B0, nxt("b1", "b0", H3, ("h1", "h2"), recovery={"h1": "r:h1", "h2": "r:h2"})], (), (), ANC, {"concluded": {"b1": Fa}}),
    # ---- recovery ---------------------------------------------------------------------------------------------------
    ("recovery", "a holder's own key recovery: h3's recovery key alone replaces h3 by h3b", [B0, REC], (), (),
     RD(anchor="b0", acks=("rc",)), {"concluded": {"rc": T}, "holders": {"h1", "h2", "h3b"}}),
    ("recovery", "a recovery that changes another seat concludes nothing (recovery_changes_other_seat)",
     [B0, nxt("rc", "b0", ("h1", "h3b"), ("r:h3",), recovers=("h3", "h3b"), recovery={"h1": "r:h1", "h3b": "r:h3b"})],
     (), (), ANC, {"concluded": {"rc": Fa}}),
    ("recovery", "a spent commitment concludes nothing: a second recovery under r:h3 on the first",
     [B0, dict(REC, recovery={"h1": "r:h1", "h2": "r:h2", "h3b": "r:h3"}),
      nxt("rc2", "rc", ("h1", "h2", "h3c"), ("r:h3",), version=2, recovers=("h3b", "h3c"),
          recovery={"h1": "r:h1", "h2": "r:h2", "h3c": "r:h3c"})], (), (), ANC, {"concluded": {"rc": T, "rc2": Fa}}),
    ("recovery", "concurrent with an amend under the same charter: both tips fold; h3 is out (the recovery removed it, "
                 "and no addition of h3 has that removal in its past), h3b is in (its own recovery), h4 is in (added by "
                 "h1 and h2, two of the fold's live h1 h2 h3b... over b0's holders the fold seats: h1 h2)",
     [B0, REC, AMD], (), (), RD(anchor="b0", acks=("rc", "am")),
     {"concluded": {"rc": T, "am": T}, "heads": ("am", "rc"), "holders": {"h1", "h2", "h3b", "h4"}}),
    ("recovery", "concurrent with an amend that changes the charter: the tips do not fold, and the holders are those "
                 "common to them: h1 and h2 (h3b and h4 wait for a bundle that names both)",
     [B0, REC, AMDC], (), (), RD(anchor="b0", acks=("rc", "am")), {"heads": ("am", "rc"), "holders": {"h1", "h2"}}),
    ("recovery", "two recoveries of one seat, neither in the other's past (h3 forks its own recovery to h3b and h3c): "
                 "contested, neither replaces the seat, and h3's seat stays as it was",
     [B0, REC, nxt("rc2", "b0", ("h1", "h2", "h3c"), ("r:h3",), recovers=("h3", "h3c"),
                   recovery={"h1": "r:h1", "h2": "r:h2", "h3c": "r:h3c"})], (), (), RD(anchor="b0", acks=("rc", "rc2")),
     {"void": {"rc", "rc2"}, "heads": ("b0",), "holders": set(H3)}),
    ("recovery", "until a bundle names both: h1 and h2 join them (over the holders common to them, h1 and h2), seating h3b",
     [B0, REC, nxt("rc2", "b0", ("h1", "h2", "h3c"), ("r:h3",), recovers=("h3", "h3c"),
                   recovery={"h1": "r:h1", "h2": "r:h2", "h3c": "r:h3c"}),
      nxt("j", ("rc", "rc2"), ("h1", "h2", "h3b"), ("h1", "h2"), version=2, recovery={"h1": "r:h1", "h2": "r:h2", "h3b": "r:h3b"})],
     (), (), RD(anchor="b0", acks=("j",)), {"concluded": {"j": True}, "void": set(), "holders": {"h1", "h2", "h3b"}}),
    # ---- the fold ---------------------------------------------------------------------------------------------------
    ("fold", "two successors with the same charter fold: h4 (s1, by h1 h2) and h5 (s2, by h2 h3) are both in",
     FORK, (), (), RD(anchor="b0", acks=("s1", "s2")), {"heads": ("s1", "s2"), "holders": {"h1", "h2", "h3", "h4", "h5"}}),
    ("fold", "a removal on one tip folds out: s1 removes h3, s2 adds h5 by h2 and h3; h3 is out, and h5's count over "
             "b0's holders the fold seats (h1 h2) is h2 alone, one of two: h5 is not in",
     FORKR, (), (), RD(anchor="b0", acks=("s1", "s2")), {"holders": {"h1", "h2"}}),
    ("fold", "two successors with different charters do not fold: the holders common to them (h1 h2 h3), waiting",
     FORKC, (), (), RD(anchor="b0", acks=("s1", "s2")), {"heads": ("s1", "s2"), "holders": {"h1", "h2", "h3"}}),
    ("fold", "the seats fold too: s1 seats n2, s2 seats n3 (same charter): n1, n2 and n3",
     [B0, nxt("s1", "b0", H3, ("h1", "h2"), seats=("n1", "n2")), nxt("s2", "b0", H3, ("h2", "h3"), seats=("n1", "n3"))],
     (), (), RD(anchor="b0", acks=("s1", "s2")), {"seats": {"n1", "n2", "n3"}}),
    ("fold", "and are common where charters differ: n1", [B0, nxt("s1", "b0", H3, ("h1", "h2"), seats=("n1", "n2")),
                                                         nxt("s2", "b0", H3, ("h2", "h3"), seats=("n1", "n3"), charter=C1)],
     (), (), RD(anchor="b0", acks=("s1", "s2")), {"seats": {"n1"}}),
    ("join", "a join of the two tips, counted over the holders common to them: h1 and h2 of h1 h2 h3", JOIN, (), (),
     RD(anchor="b0", acks=("j",)), {"concluded": {"j": T}, "heads": ("j",), "holders": {"h1", "h2", "h3", "h4", "h5"}}),
    ("join", "a join is counted over the common holders, not their union: h4 and h5 with h1 are one of three",
     FORK + [nxt("j", ("s1", "s2"), H3 + ("h4", "h5"), ("h1", "h4", "h5"), version=2)], (), (), ANC, {"concluded": {"j": Fa}}),
    ("join", "a join names both where charters differ, and ends the wait: its own holders", JOINC, (), (),
     RD(anchor="b0", acks=("j",)), {"concluded": {"j": T}, "holders": {"h1", "h2", "h3", "h4", "h5"}}),
    # ---- the reader ------------------------------------------------------------------------------------------------
    ("in force", "per reader: a reader that acknowledged s1 alone holds s1's holders; one that acknowledged nothing, "
                 "its anchor's", FORK, (), (), RD(anchor="b0", acks=("s1",)), {"heads": ("s1",), "holders": {"h1", "h2", "h3", "h4"}}),
    ("in force", "the same rows, a reader that acknowledged nothing: the anchor, b0", FORK, (), (), ANC,
     {"heads": ("b0",), "holders": set(H3)}),
    ("anchor", "the reader's anchor by the holders' thumbprints", LIN, (), (), RD(thumbs=H3, acks=("b1",)),
     {"heads": ("b1",)}),
    ("anchor", "no anchor: genesis_bundle_not_anchored", LIN, (), (), RD(acks=("b1",)), {"heads": None}),
    ("anchor", "any other first bundle is void for the reader: a second genesis x0 under the family, and a bundle on it "
               "the reader acknowledged: not in force", LIN + [B("x0", F, 0, ("x1", "x2")), nxt("x1b", "x0", ("x1", "x2"), ("x1", "x2"))],
     (), (), RD(anchor="b0", acks=("b2", "x1b")), {"heads": ("b2",)}),
    # ---- S'' and T on a forked bundle ------------------------------------------------------------------------------
    ("S''", "h1 and h2 sign s1 at b0, then b1 at b0 with h3 and b2 on b1, without s1: s1 is self-forked, and by T h3 "
            "(signed only b1) against none: s1 is void, and no reader holds it", SFW, (), (),
     RD(anchor="b0", acks=("s1", "b2")), {"void": {"s1"}, "heads": ("b2",)}),
    ("S''", "the same where h3 did not sign b1: the same voices on both sides, a tie: s1 stands, and the reader that "
            "acknowledged both folds them", SFT, (), (), RD(anchor="b0", acks=("s1", "b2")),
     {"void": set(), "heads": ("b2", "s1")}),
    # ---- grants ----------------------------------------------------------------------------------------------------
    ("grant", "a root grant counted over the holders of the bundle it names, at a strict majority: h1 alone on b0 is "
              "one of three", LIN, (), (GR("gA", "b0", "uA", "room", ("h1",)),), ANC, {"row": {"gA": False}}),
    ("grant", "the same signed by h1 and h2: a row; for a reader whose bundle in force is b0, in force",
     LIN, (), (GR("gA", "b0", "uA", "room", ("h1", "h2")),), ANC, {"row": {"gA": True}, "grant": {"gA": (True, None)}}),
    ("grant", "a later bundle re-scopes existing grants with no re-issuance: a grant under b0, read by a reader at b2 "
              "whose charter still carries the duty, resolves",
     LIN, (), (GR("gA", "b0", "uA", "room", ("h1", "h2")),), RD(anchor="b0", acks=("b2",)), {"grant": {"gA": (True, None)}}),
    ("grant", "the same after b2 drops the duty from its charter: the grant exists, and stops resolving",
     LIN[:2] + [dict(LIN[2], charter=C2)], (), (GR("gA", "b0", "uA", "room", ("h1", "h2")),), RD(anchor="b0", acks=("b2",)),
     {"row": {"gA": True}, "grant": {"gA": (False, "grant_scope_not_in_force")}}),
    ("grant", "a grant under a tip the reader's line is not on: a reader at s1, a grant under s2 (counted by h2, h3 and "
              "h5 of four) is void for it", FORK, (), (GR("g2", "s2", "uB", "room", ("h2", "h3", "h5")),),
     RD(anchor="b0", acks=("s1",)), {"row": {"g2": True}, "grant": {"g2": (False, "grant_not_in_reader_lineage")}}),
    ("grant", "a grant exists only where its bundle's charter carries its duty: a grant of `infra` under a bundle "
              "whose charter carries none", [dict(B0, charter=C2)], (), (GR("gA", "b0", "uA", "room", ("h1", "h2")),),
     ANC, {"row": {"gA": False}}),
    ("grant", "a grant made under either successor stands as a row: one on s1 by h1 h2, one on s2 by h2 h3",
     FORK, (), (GR("g1", "s1", "uA", "room", ("h1", "h2", "h4")), GR("g2", "s2", "uB", "room", ("h2", "h3", "h5"))),
     RD(anchor="b0", acks=("s1", "s2")), {"row": {"g1": True, "g2": True}, "grant": {"g1": (True, None), "g2": (True, None)}}),
    ("grant", "a grant is counted over its own bundle's live holders: on s1 (h1..h4), h1 and h2 are two of four, short",
     FORK, (), (GR("g1", "s1", "uA", "room", ("h1", "h2")),), RD(anchor="b0", acks=("s1", "s2")),
     {"grant": {"g1": (False, "grant_count_short")}}),
    ("grant", "where charters differ, the scope in force is what both carry: both carry the duty, so h1, h2 and h4 on "
              "s1 resolve", FORKC, (), (GR("g1", "s1", "uA", "room", ("h1", "h2", "h4")),), RD(anchor="b0", acks=("s1", "s2")),
     {"grant": {"g1": (True, None)}}),
    ("grant", "and where s2's charter drops the duty, the scope in force does not carry it: the grant on s1 stops resolving",
     [B0, nxt("s1", "b0", H3 + ("h4",), ("h1", "h2")), nxt("s2", "b0", H3 + ("h5",), ("h2", "h3"), charter=C2)], (),
     (GR("g1", "s1", "uA", "room", ("h1", "h2", "h4")),), RD(anchor="b0", acks=("s1", "s2")),
     {"grant": {"g1": (False, "grant_scope_not_in_force")}}),
]

# ---- stalled recovery, judged against the root (seat.recovery_verdict) ------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "causal_kernel"))
import seat as ST  # noqa: E402
import check_acts as AC  # noqa: E402
CK = ST.CK
GI, W3 = AC.GI, AC.W3                     # f1 f2 f3 found an infrastructure room under quorum:2/3; f3 leaves: stalled
RCV = lambda **kw: dict(AC.RECOVER(heads=("g",), cites=("w3",)), **kw)          # f4 widens itself, naming grant B1
STALLED = [GI, W3]
GOK = GR("B1", "b0", "f4", "g", ("h1", "h2"))
ROOT_ROWS = [B0]
# (name, room rows, root bundles, grants, reader, recovery concludes, reason, f4 a founder)
RECOVERY = [
    ("stalled, a grant on the bundle in force counted by h1 and h2 of three, scope this room, a user key, signed by "
     "it: the recovery concludes, and f4 is a founder", STALLED + [RCV()], ROOT_ROWS, (GOK,), ANC, True, None, True),
    ("no trust root read: undecided, and it concludes nothing", STALLED + [RCV()], None, (), None, False,
     "stalled_recovery_needs_bundle", False),
    ("live (no founder left): no recovery", [GI, RCV(names=("g",))], ROOT_ROWS, (GOK,), ANC, False, "not_stalled", False),
    ("the grant names another room", STALLED + [RCV()], ROOT_ROWS, (dict(GOK, scope="other"),), ANC, False,
     "grant_scope_not_this_room", False),
    ("the grant names a node key", STALLED + [RCV()], ROOT_ROWS, (dict(GOK, identity=("user", "node")),), ANC, False,
     "grant_identity_not_user", False),
    ("the widening is signed by another key than the grant names", STALLED + [RCV()], ROOT_ROWS, (dict(GOK, to="f5"),),
     ANC, False, "not_signed_by_named_key", False),
    ("the grant's count is short: h1 alone of three", STALLED + [RCV()], ROOT_ROWS, (dict(GOK, signers=("h1",)),), ANC,
     False, "grant_count_short", False),
    ("the grant names b0, and this node's bundle in force is b1, whose charter still carries the duty: it resolves",
     STALLED + [RCV()], LIN, (GOK,), RD(anchor="b0", acks=("b1",)), True, None, True),
    ("the same where b1's charter drops the duty", STALLED + [RCV()], [B0, dict(LIN[1], charter=C2)], (GOK,),
     RD(anchor="b0", acks=("b1",)), False, "grant_scope_not_in_force", False),
    ("the reader's anchor names no first bundle", STALLED + [RCV()], ROOT_ROWS, (GOK,), RD(anchor="zz"), False,
     "genesis_bundle_not_anchored", False),
    ("two tips: a grant on s1 by h1, h2 and h4 is three of s1's four", STALLED + [RCV()], FORK,
     (GR("B1", "s1", "f4", "g", ("h1", "h2", "h4")),), RD(anchor="b0", acks=("s1", "s2")), True, None, True),
    ("the same by h1 and h2 alone: two of four, short", STALLED + [RCV()], FORK, (GR("B1", "s1", "f4", "g", ("h1", "h2")),),
     RD(anchor="b0", acks=("s1", "s2")), False, "grant_count_short", False),
    ("charters differ, both carrying the duty: h1, h2 and h4 on s1 resolve", STALLED + [RCV()], FORKC,
     (GR("B1", "s1", "f4", "g", ("h1", "h2", "h4")),), RD(anchor="b0", acks=("s1", "s2")), True, None, True),
    ("one founder seat and nothing else: a widening that also changes the protocol", STALLED + [RCV(consensus_protocol="quorum:2/3")],
     ROOT_ROWS, (GOK,), ANC, False, "recovery_changes_more", False),
]
RECOVERY_PLANTS = ("recovery_inforce_unread", "recovery_scope_unread", "recovery_identity_unread", "recovery_signer_unread",
                   "recovery_stalled_unread", "recovery_more_unread")


def recovery_answer(rows, bs, gs, rd):
    view = (RT.Root(bs, (), gs), rd) if bs is not None else None
    ST.ROOT.append(view)
    try:
        S = CK.concluded(CK.kept(list(rows)), lambda r, P, past: ST.seat_rule(r, P, past))
        P = [q for q in S.Cs if q["id"] in S.anc["rv"]] if "rv" in S.anc else []
        why = ST.recovery_verdict(S.by["rv"], P, lambda a, b: a in S.anc.get(b, ()))[1]
        return (bool(S.C.get("rv")), why, "f4" in ST.Seats(S).holders("founder", "g"))
    finally:
        ST.ROOT.pop()


def run_recovery():
    return ["recovery %s: got %s" % (name, got) for name, rows, bs, gs, rd, c, why, f4 in RECOVERY
            for got in [recovery_answer(rows, bs, gs, rd)] if got != (c, why, f4)]


PLANTS = ("first_majority", "count_over_own", "iat_unread", "revoked_counts", "bound_unread", "version_unread",
          "family_unread", "commitments_unread", "recovery_other_seat", "spent_unread", "fold_common", "fold_union",
          "charter_folds", "join_union", "anchor_unread", "inforce_global", "root_sf_unread", "root_t_unread",
          "grant_any_bundle", "grant_charter_unread", "grant_scope_unread", "recovery_fork_both")


def answer(bs, rv, gs, rd, want):
    R = RT.Root(bs, rv, gs)
    got = {}
    if "concluded" in want: got["concluded"] = {i: R.counted(i)[0] for i in want["concluded"]}
    if "void" in want: got["void"] = set(R.void())
    if "heads" in want: got["heads"] = R.heads(rd)
    f = R.in_force(rd)
    if "holders" in want: got["holders"] = set(f[0]) if f else None
    if "seats" in want: got["seats"] = set(f[1]) if f else None
    if "grant" in want: got["grant"] = {g: R.grant_in_force(g, rd) for g in want["grant"]}
    if "row" in want: got["row"] = {g: R.grant_row(g) for g in want["row"]}
    return got


def norm(want):
    return {k: (set(v) if isinstance(v, (set, frozenset)) else v) for k, v in want.items()}


def run():
    bad = []
    for rule, name, bs, rv, gs, rd, want in CASES:
        got = answer(bs, rv, gs, rd, want)
        if got != norm(want): bad.append("%s %s: got %s" % (rule, name, got))
    return bad


def main():
    bad = run() + run_recovery()
    for b in bad: print(b)
    missed = []
    for p in PLANTS:
        RT.MUT.add(p)
        try:
            hit = next((name for rule, name, bs, rv, gs, rd, want in CASES
                        if not any(name in b for b in bad) and answer(bs, rv, gs, rd, want) != norm(want)), None)
        finally:
            RT.MUT.discard(p)
        print("  plant %-22s %s" % (p, ("caught by: " + hit[:90]) if hit else "NOT CAUGHT"))
        if not hit: missed.append(p)
    for p in RECOVERY_PLANTS:
        ST.MUT.add(p)
        try:
            hit = next((name for name, rows, bs, gs, rd, c, why, f4 in RECOVERY
                        if recovery_answer(rows, bs, gs, rd) != (c, why, f4)), None)
        finally:
            ST.MUT.discard(p)
        print("  plant %-22s %s" % (p, ("caught by: " + hit[:90]) if hit else "NOT CAUGHT"))
        if not hit: missed.append(p)
    ok = not bad and not missed
    n = len(PLANTS) + len(RECOVERY_PLANTS)
    print("RESULT: %s: %d cases, %d of stalled recovery, %d of %d planted breaks caught" % (
        "ok" if ok else "%d problems" % (len(bad) + len(missed)), len(CASES), len(RECOVERY), n - len(missed), n))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
