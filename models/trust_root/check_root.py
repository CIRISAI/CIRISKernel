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

B, RV, GR, RD, AK, CS = RT.bundle, RT.revoke, RT.grant, RT.reader, RT.ack, RT.cosign
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
# a join of FORK's tips, counted by a strict majority of EACH predecessor's live holders: h1 h2 h3 are three of
# s1's four (h1..h4) and three of s2's four (h1 h2 h3 h5)
JOIN = FORK + [nxt("j", ("s1", "s2"), H3 + ("h4", "h5"), ("h1", "h2", "h3"), version=2)]
JOINC = FORKC + [nxt("j", ("s1", "s2"), H3 + ("h4", "h5"), ("h1", "h2", "h3"), version=2, charter=C1)]
# a forked join: two joins of FORK's tips, both by h1 and h2 (a strict majority of the common h1 h2 h3), under
# different charters: two tips whose regime differs, so the holders are again those common to them
C3 = {"name": "c3", "duties": ("infra",)}
FJ = lambda h1s, h2s: FORK + [nxt("j1", ("s1", "s2"), h1s, ("h1", "h2", "h3"), version=2),
                              nxt("j2", ("s1", "s2"), h2s, ("h1", "h2", "h3"), version=2, charter=C1)]
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
    ("fold", "rule 6 before the fold: s1 removes h3 (h1 h2), s2 keeps h3 and adds h5 (h2 h3); h2 signed both, one "
             "cutting a holder the other keeps, so h2 has no say on either: s1 and s2 are one of three, neither counts, "
             "and the reader is at b0", FORKR, (), (), RD(anchor="b0", acks=("s1", "s2")), {"heads": ("b0",), "holders": set(H3)}),
    ("fold", "two successors with different charters do not fold: the holders common to them (h1 h2 h3), waiting",
     FORKC, (), (), RD(anchor="b0", acks=("s1", "s2")), {"heads": ("s1", "s2"), "holders": {"h1", "h2", "h3"}}),
    ("fold", "the seats fold too: s1 seats n2, s2 seats n3 (same charter): n1, n2 and n3",
     [B0, nxt("s1", "b0", H3, ("h1", "h2"), seats=("n1", "n2")), nxt("s2", "b0", H3, ("h2", "h3"), seats=("n1", "n3"))],
     (), (), RD(anchor="b0", acks=("s1", "s2")), {"seats": {"n1", "n2", "n3"}}),
    ("fold", "and are common where charters differ: n1", [B0, nxt("s1", "b0", H3, ("h1", "h2"), seats=("n1", "n2")),
                                                         nxt("s2", "b0", H3, ("h2", "h3"), seats=("n1", "n3"), charter=C1)],
     (), (), RD(anchor="b0", acks=("s1", "s2")), {"seats": {"n1"}}),
    # the join (the Constitution's ruling): counted by a strict majority of EACH named predecessor's live holders,
    # each voice a key that predecessor seats under the same key, whatever the charters; prev is the greatest version
    # (least id among equals), further_prev the rest; a named predecessor in the past of another concludes nothing
    ("join", "a join of two tips, counted by a strict majority of each: h1, h2 and h3 are three of s1's four and of "
             "s2's four", JOIN, (), (), RD(anchor="b0", acks=("j",)),
     {"concluded": {"j": T}, "heads": ("j",), "holders": {"h1", "h2", "h3", "h4", "h5"}}),
    ("join", "the common holders' base (h1 h2 h3) would take h1 and h2 (two of three); each predecessor's does not: "
             "two of four, twice", FORK + [nxt("j", ("s1", "s2"), H3 + ("h4", "h5"), ("h1", "h2"), version=2)], (), (), ANC,
     {"concluded": {"j": Fa}}),
    ("join", "the same rule whatever the charters: h1, h2 and h3 join tips whose charters differ", JOINC, (), (),
     RD(anchor="b0", acks=("j",)), {"concluded": {"j": T}, "holders": {"h1", "h2", "h3", "h4", "h5"}}),
    ("join", "the wire: prev is the greatest version, least id among equals; naming s2 first is Invalid",
     FORK + [nxt("j", ("s2", "s1"), H3 + ("h4", "h5"), ("h1", "h2", "h3"), version=2)], (), (), ANC, {"concluded": {"j": Fa}}),
    ("join", "a join inherits the union of retired keys: rc rotates h3 to h3b, and am (h1 h2 add h4) still lists h3; "
             "joining them, h3 is no live holder of am for the count, so h1 and h2 are two of am's three and of rc's three",
     [B0, REC, AMD, nxt("j", ("am", "rc"), ("h1", "h2", "h3b", "h4"), ("h1", "h2"), version=2,
                        recovery={"h1": "r:h1", "h2": "r:h2", "h3b": "r:h3b", "h4": "r:h4"})], (), (), RD(anchor="b0", acks=("j",)),
     {"concluded": {"j": T}, "holders": {"h1", "h2", "h3b", "h4"}}),
    ("join", "and revives nothing: the retired h3 signing it is no voice (h3 alone with h4 on am)",
     [B0, REC, AMD, nxt("j", ("am", "rc"), ("h1", "h2", "h3b", "h4"), ("h3", "h4"), version=2,
                        recovery={"h1": "r:h1", "h2": "r:h2", "h3b": "r:h3b", "h4": "r:h4"})], (), (), ANC, {"concluded": {"j": Fa}}),
    ("join", "the wire: a named predecessor in the past of another concludes nothing (s1 and b0)",
     FORK + [nxt("j", ("s1", "b0"), H3 + ("h4",), ("h1", "h2", "h3"), version=2)], (), (), ANC, {"concluded": {"j": Fa}}),
    # the forked join (the Constitution's option (ii)): two joins of the same tips that do not fold with each other
    # (their charters differ), neither in the other's past, are contested: neither stands, and the reader keeps the
    # tips they tried to join; a bundle naming every one settles them, counted by a strict majority of those tips'
    # own count (each named join's majority). Two successors of one bundle are no joins and fold as tips; two joins
    # under the SAME charter fold as any tips do: concurrent successors are not contested
    ("join", "a forked join: two joins of s1 and s2 under different charters are contested: neither stands, and a "
             "reader that acknowledged both keeps s1 and s2 (their fold, h1..h5)",
     FJ(("h1", "h2", "h3", "h4", "h5"), ("h1", "h2", "h3", "h4")), (), (), RD(anchor="b0", acks=("j1", "j2")),
     {"concluded": {"j1": T, "j2": T}, "void": {"j1", "j2"}, "heads": ("s1", "s2"), "holders": {"h1", "h2", "h3", "h4", "h5"}}),
    ("join", "two joins with disjoint holders (h1 h4; h2 h5) leave no hole: they are contested, and the reader keeps "
             "s1 and s2", FJ(("h1", "h4"), ("h2", "h5")), (), (), RD(anchor="b0", acks=("j1", "j2")),
     {"void": {"j1", "j2"}, "heads": ("s1", "s2"), "holders": {"h1", "h2", "h3", "h4", "h5"}}),
    ("join", "a bundle naming both settles them, counted by each joined join's majority: h1 h4 and h2 h5",
     FJ(("h1", "h4"), ("h2", "h5")) + [nxt("j3", ("j1", "j2"), ("h1", "h2", "h4", "h5"), ("h1", "h2", "h4", "h5"), version=3, charter=C3)],
     (), (), RD(anchor="b0", acks=("j3",)), {"concluded": {"j3": T}, "void": set(), "heads": ("j3",),
                                             "holders": {"h1", "h2", "h4", "h5"}}),
    ("join", "h1 alone is no majority of either join's holders",
     FJ(("h1", "h4"), ("h1", "h5")) + [nxt("j3", ("j1", "j2"), ("h1", "h4", "h5"), ("h1",), version=3, charter=C3)], (), (),
     RD(anchor="b0", acks=("j3",)), {"concluded": {"j3": Fa}, "heads": ("b0",)}),
    ("join", "two joins under the same charter are no forked join, but each drops a holder the other keeps (j1 drops "
             "h5, j2 h4), and h1 h2 h3 signed both: rule 6, neither counts, and the reader is back at s1 and s2",
     FORK + [nxt("j1", ("s1", "s2"), ("h1", "h2", "h3", "h4"), ("h1", "h2", "h3"), version=2),
             nxt("j2", ("s1", "s2"), ("h1", "h2", "h3", "h5"), ("h1", "h2", "h3"), version=2)], (), (),
     RD(anchor="b0", acks=("j1", "j2")), {"void": set(), "heads": ("s1", "s2"), "holders": {"h1", "h2", "h3", "h4", "h5"}}),
    ("join", "three joins, pairwise differing: all contested, and the reader keeps s1 and s2",
     FJ(("h1", "h2", "h3"), ("h1", "h2", "h4")) + [nxt("j3", ("s1", "s2"), ("h1", "h2", "h5"), ("h1", "h2", "h3"), version=2, charter=C3)],
     (), (), RD(anchor="b0", acks=("j1", "j2", "j3")), {"void": {"j1", "j2", "j3"}, "heads": ("s1", "s2")}),
    ("join", "a bundle naming two of the three settles nothing, and is void with them",
     FJ(("h1", "h2", "h3"), ("h1", "h2", "h4")) + [nxt("j3", ("s1", "s2"), ("h1", "h2", "h5"), ("h1", "h2", "h3"), version=2, charter=C3),
                                                   nxt("k", ("j1", "j2"), ("h1", "h2", "h3"), ("h1", "h2"), version=3)],
     (), (), RD(anchor="b0", acks=("k",)), {"concluded": {"k": T}, "void": {"j1", "j2", "j3", "k"}, "heads": ("b0",)}),
    ("join", "one naming all three settles them", FJ(("h1", "h2", "h3"), ("h1", "h2", "h4"))
     + [nxt("j3", ("s1", "s2"), ("h1", "h2", "h5"), ("h1", "h2", "h3"), version=2, charter=C3),
        nxt("k", ("j1", "j2", "j3"), ("h1", "h2", "h3"), ("h1", "h2"), version=3)], (), (), RD(anchor="b0", acks=("k",)),
     {"concluded": {"k": T}, "void": set(), "heads": ("k",), "holders": {"h1", "h2", "h3"}}),
    ("join", "a join concurrent with an ordinary amend on one tip (a on s1, adding h6): for a reader that "
             "acknowledged a, s2 is behind its line (s2 names b0, strictly in the past of a's head s1), but the join "
             "is judged by its own heads (s1 is a's head, not strictly in its past): not behind, and acknowledgeable; "
             "the reader folds a and j1",
     FORK + [nxt("j1", ("s1", "s2"), H3 + ("h4", "h5"), ("h1", "h2", "h3"), version=2),
             nxt("a", "s1", H3 + ("h4", "h6"), ("h1", "h2", "h4"), version=2)], (), (),
     RD(anchor="b0", acks=("j1", "a")), {"void": set(), "heads": ("a", "j1"), "holders": {"h1", "h2", "h3", "h4", "h5", "h6"}}),
    ("join", "the same join read by a reader that acknowledged only j1: j1 and its holders", FORK + [
        nxt("j1", ("s1", "s2"), H3 + ("h4", "h5"), ("h1", "h2", "h3"), version=2),
        nxt("a", "s1", H3 + ("h4", "h6"), ("h1", "h2", "h4"), version=2)], (), (),
     RD(anchor="b0", acks=("j1",)), {"heads": ("j1",), "holders": {"h1", "h2", "h3", "h4", "h5"}}),
    ("join", "the settling bundle itself forked: two settlers of j1 and j2 under different charters are contested in "
             "turn, and the reader ends at s1 and s2, the same holders, never fewer",
     FJ(("h1", "h4"), ("h2", "h5")) + [nxt("k1", ("j1", "j2"), ("h1", "h2", "h4"), ("h1", "h2", "h4", "h5"), version=3),
                                       nxt("k2", ("j1", "j2"), ("h1", "h2", "h5"), ("h1", "h2", "h4", "h5"), version=3, charter=C1)],
     (), (), RD(anchor="b0", acks=("k1", "k2")),
     {"concluded": {"k1": T, "k2": T}, "void": {"j1", "j2", "k1", "k2"}, "heads": ("s1", "s2"),
      "holders": {"h1", "h2", "h3", "h4", "h5"}}),
    ("join", "and a bundle naming both settlers settles all, by each settler's majority (h1 and h2 of three)",
     FJ(("h1", "h4"), ("h2", "h5")) + [nxt("k1", ("j1", "j2"), ("h1", "h2", "h4"), ("h1", "h2", "h4", "h5"), version=3),
                                       nxt("k2", ("j1", "j2"), ("h1", "h2", "h5"), ("h1", "h2", "h4", "h5"), version=3, charter=C1),
                                       nxt("m", ("k1", "k2"), ("h1", "h2", "h3"), ("h1", "h2"), version=4, charter=C3)],
     (), (), RD(anchor="b0", acks=("m",)), {"concluded": {"m": T}, "void": set(), "heads": ("m",), "holders": {"h1", "h2", "h3"}}),
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
    ("S''", "the same where h3 did not sign b1: the same voices on both sides, a tie: s1 stands, and a reader at s1 "
            "holds it", SFT, (), (), RD(anchor="b0", acks=("s1",)), {"void": set(), "heads": ("s1",)}),
    ("S''", "a reader that acknowledged s1 and then b2: s1 is behind b2, so void for it (acknowledgements accumulate; "
            "an earlier one protects nothing)", SFT, (), (), RD(anchor="b0", acks=("s1", "b2")),
     {"void": set(), "heads": ("b2",)}),
    # ---- grants ----------------------------------------------------------------------------------------------------
    ("grant", "a root grant counted over the holders of the bundle it names, at a strict majority: h1 alone on b0 is "
              "one of three", LIN, (), (GR("gA", "b0", "uA", "room", ("h1",)),), ANC, {"row": {"gA": False}}),
    ("grant", "the same signed by h1 and h2: a row; for a reader whose bundle in force is b0, in force",
     LIN, (), (GR("gA", "b0", "uA", "room", ("h1", "h2")),), ANC, {"row": {"gA": True}, "grant": {"gA": (True, None)}}),
    ("grant", "a later bundle re-scopes existing grants with no re-issuance: a grant by h1 and h2 under b0, read by a "
              "reader at b2 (h1 h2 h4), resolves while its voices are a strict majority there (two of three)",
     LIN, (), (GR("gA", "b0", "uA", "room", ("h1", "h2")),), RD(anchor="b0", acks=("b2",)), {"grant": {"gA": (True, None)}}),
    ("grant", "the cost: a grant lapses when enough of its signers leave: at b1 (h1..h4) h1 and h2 are two of four",
     LIN, (), (GR("gA", "b0", "uA", "room", ("h1", "h2")),), RD(anchor="b0", acks=("b1",)),
     {"grant": {"gA": (False, "grant_voices_not_in_force")}}),
    ("grant", "growth lapses a grant: b1 adds h4 and h5 (by h1, h2 and h3); h1 and h2 are two of five",
     [B0, nxt("b1", "b0", H5, ("h1", "h2", "h3"))], (), (GR("gA", "b0", "uA", "room", ("h1", "h2")),),
     RD(anchor="b0", acks=("b1",)), {"row": {"gA": True}, "grant": {"gA": (False, "grant_voices_not_in_force")}}),
    ("grant", "voices are addable: h4 cosigns the same grant, and it resolves again (three of five); its existence "
              "stays the issuance count over b0", [B0, nxt("b1", "b0", H5, ("h1", "h2", "h3"))], (),
     (GR("gA", "b0", "uA", "room", ("h1", "h2")), CS("c4", "gA", "h4")), RD(anchor="b0", acks=("b1",)),
     {"row": {"gA": True}, "grant": {"gA": (True, None)}}),
    ("grant", "a recovered holder re-cosigns under its new key: h2 recovers to h2b, the grant lapses (h1 one of h1 "
              "h2b h3), and h2b cosigns it: two of three, it resolves", [B0, nxt("rc", "b0", ("h1", "h2b", "h3"), ("r:h2",),
                                                                         recovers=("h2", "h2b"), recovery={"h1": "r:h1", "h2b": "r:h2b", "h3": "r:h3"})],
     (), (GR("gA", "b0", "uA", "room", ("h1", "h2")), CS("c2", "gA", "h2b")), RD(anchor="b0", acks=("rc",)),
     {"grant": {"gA": (True, None)}}),
    ("grant", "the named-bundle hole stays shut: h1, the last survivor of b0's set, and the removed h2 grant naming b0 "
              "(two of b0's three, so it exists); after b1 grows to ten without h2, h1 is one of ten: refused",
     [B0, nxt("b1", "b0", ("h1", "h3") + tuple("h%d" % i for i in range(4, 12)), ("h1", "h3"))], (),
     (GR("gA", "b0", "uA", "room", ("h1", "h2")),), RD(anchor="b0", acks=("b1",)),
     {"row": {"gA": True}, "grant": {"gA": (False, "grant_voices_not_in_force")}}),
    ("grant", "an amend swapping one of three holders (h3 for h6) leaves a grant by the other two standing",
     [B0, nxt("b1", "b0", ("h1", "h2", "h6"), ("h1", "h2"))], (), (GR("gA", "b0", "uA", "room", ("h1", "h2")),),
     RD(anchor="b0", acks=("b1",)), {"grant": {"gA": (True, None)}}),
    ("grant", "at unjoined tips the majority is of the holders in force there: the fold (h1..h5), so h1, h2 and h4 "
              "on s1 are three of five", FORK, (), (GR("g1", "s1", "uA", "room", ("h1", "h2", "h4")),),
     RD(anchor="b0", acks=("s1", "s2")), {"grant": {"g1": (True, None)}}),
    ("grant", "and the common holders where charters differ (h1 h2 h3): h1, h2 and h4 on s1 are two of three",
     FORKC, (), (GR("g1", "s1", "uA", "room", ("h1", "h2", "h4")),), RD(anchor="b0", acks=("s1", "s2")),
     {"grant": {"g1": (True, None)}}),
    ("grant", "a voice under a key a recovery retired is no voice: h1 and h2 grant on b0, h2 recovers to h2b; at the "
              "recovery the holders are h1 h2b h3, and h1 alone is one of three: the grant lapses until re-issued",
     [B0, nxt("rc", "b0", ("h1", "h2b", "h3"), ("r:h2",), recovers=("h2", "h2b"),
              recovery={"h1": "r:h1", "h2b": "r:h2b", "h3": "r:h3"})], (), (GR("gA", "b0", "uA", "room", ("h1", "h2")),),
     RD(anchor="b0", acks=("rc",)), {"grant": {"gA": (False, "grant_voices_not_in_force")}}),
    ("grant", "the same after b2 drops the duty from its charter: the grant exists, and stops resolving",
     LIN[:2] + [dict(LIN[2], charter=C2)], (), (GR("gA", "b0", "uA", "room", ("h1", "h2")), AK("kr", "b2", names=("gA",))),
     RD(anchor="b0", acks=("b2",)),
     {"row": {"gA": True}, "grant": {"gA": (False, "grant_scope_not_in_force")}}),
    ("grant", "a grant under s2 read at s1: its voices h2 and h3 are two of s1's four, so it does not resolve there",
     FORK, (), (GR("g2", "s2", "uB", "room", ("h2", "h3", "h5")),),
     RD(anchor="b0", acks=("s1",)), {"row": {"g2": True}, "grant": {"g2": (False, "grant_voices_not_in_force")}}),
    ("grant", "a grant exists only where its bundle's charter carries its duty: a grant of `infra` under a bundle "
              "whose charter carries none", [dict(B0, charter=C2)], (), (GR("gA", "b0", "uA", "room", ("h1", "h2")),),
     ANC, {"row": {"gA": False}}),
    ("grant", "a grant made under either successor stands as a row: one on s1 by h1 h2, one on s2 by h2 h3",
     FORK, (), (GR("g1", "s1", "uA", "room", ("h1", "h2", "h4")), GR("g2", "s2", "uB", "room", ("h2", "h3", "h5"))),
     RD(anchor="b0", acks=("s1", "s2")), {"row": {"g1": True, "g2": True}, "grant": {"g1": (True, None), "g2": (True, None)}}),
    ("grant", "signers who hold only s1: a grant on s1 by h1, h2 and h4 is three of s1's four", FORK, (),
     (GR("g1", "s1", "uA", "room", ("h1", "h2", "h4")),), RD(anchor="b0", acks=("s1",)), {"row": {"g1": True},
                                                                                       "grant": {"g1": (True, None)}}),
    ("grant", "the head rule: signers who saw s2 but name only s1 conclude nothing (they must name both)", FORK, (),
     (AK("k2", "s2"), GR("g1", "s1", "uA", "room", ("h1", "h2", "h4"), names=("k2",))), RD(anchor="b0", acks=("s1",)),
     {"row": {"g1": False}}),
    ("grant", "the seen bundles are derived from the grant row's own past: an acceptance edge naming s2 there, and "
              "the grant naming only s1 concludes nothing", FORK, (),
     (AK("k1", "s1"), AK("k2", "s2", names=("k1",)), GR("g1", "s1", "uA", "room", ("h1", "h2", "h4"), names=("k2",))),
     RD(anchor="b0", acks=("s1",)),
     {"row": {"g1": False}}),
    ("grant", "the honest holder's acceptance edge: h2 signed s2 and its node wrote an acceptance edge to it (k2); "
              "h2's grant naming only s1, with k2 in its past, concludes nothing", FORK, (),
     (AK("k2", "s2"), GR("g1", "s1", "uA", "room", ("h2", "h1", "h4"), names=("k2",))), RD(anchor="b0", acks=("s1",)),
     {"row": {"g1": False}}),
    ("grant", "the residual, stated: the same grant with no row naming s2 in its past stands (h2's statement over s2 "
              "is not ordered against it, so it is not read)", FORK, (),
     (GR("g1", "s1", "uA", "room", ("h2", "h1", "h4")),), RD(anchor="b0", acks=("s1",)), {"row": {"g1": True}}),
    ("grant", "and from earlier grants in its past: one naming s2", FORK, (),
     (GR("g0", "s2", "uB", "room", ("h2", "h3", "h5")), AK("k1", "s1"),
      GR("g1", "s1", "uA", "room", ("h1", "h2", "h4"), names=("k1", "g0"))),
     RD(anchor="b0", acks=("s1",)), {"row": {"g1": False}}),
    ("grant", "a past that acknowledges s1 alone: the grant on s1 stands", FORK, (),
     (AK("k0", "b0"), AK("k1", "s1", names=("k0",)), GR("g1", "s1", "uA", "room", ("h1", "h2", "h4"), names=("k1",))),
     RD(anchor="b0", acks=("s1",)),
     {"row": {"g1": True}}),
    ("grant", "naming both, they are counted over the fold (h1..h5): h1, h2 and h4 are three of five", FORK, (),
     (AK("k2", "s2"), GR("g1", ("s1", "s2"), "uA", "room", ("h1", "h2", "h4"), names=("k2",))), RD(anchor="b0", acks=("s1", "s2")),
     {"row": {"g1": True}, "grant": {"g1": (True, None)}}),
    ("grant", "naming both under different charters, over the common holders (h1 h2 h3): h1 and h2", FORKC, (),
     (AK("k2", "s2"), GR("g1", ("s1", "s2"), "uA", "room", ("h1", "h2"), names=("k2",))), RD(anchor="b0", acks=("s1", "s2")),
     {"row": {"g1": True}}),
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

# ---- the root-fold attack (review-58b): rj, rs, g1, g2 -----------------------------------------------------------
H5 = ("h1", "h2", "h3", "h4", "h5")
RB1 = nxt("b1", "b0", H5, ("h1", "h2"))
RB2 = nxt("b2", "b1", ("h3", "h4", "h5"), ("h3", "h4", "h5"), version=2)      # h1 and h2 removed
RL = [B0, RB1, RB2]
RA = nxt("ra", "b0", ("h1x", "h2", "h3"), ("r:h1",), recovers=("h1", "h1x"), recovery={"h1x": "r:h1x", "h2": "r:h2", "h3": "r:h3"})
RJX = nxt("jx", ("b2", "ra"), ("h3",), ("h3",), version=3, recovery={"h3": "r:h3"})
_H = ("h1", "h2", "h3b")
SB2 = nxt("b2", "rc", _H + ("h4",), ("h1", "h2"), version=2, recovery={"h1": "r:h1", "h2": "r:h2", "h3b": "r:h3b", "h4": "r:h4"})
SB3 = nxt("b3", "b2", _H + ("h4", "h5"), ("h1", "h2", "h4"), version=3,
          recovery={"h1": "r:h1", "h2": "r:h2", "h3b": "r:h3b", "h4": "r:h4", "h5": "r:h5"})
SL = [B0, REC, SB2, SB3]
SRC2 = nxt("rc2", "b0", ("h1", "h2", "h3x"), ("r:h3",), recovers=("h3", "h3x"), recovery={"h1": "r:h1", "h2": "r:h2", "h3x": "r:h3x"})
SRC3 = nxt("rc3", "b0", ("h1", "h2", "h3y"), ("r:h3",), recovers=("h3", "h3y"), recovery={"h1": "r:h1", "h2": "r:h2", "h3y": "r:h3y"})
SJ = nxt("j", ("b3", "rc2"), _H + ("h4", "h5"), ("h1", "h2"), version=4,
         recovery={"h1": "r:h1", "h2": "r:h2", "h3b": "r:h3b", "h4": "r:h4", "h5": "r:h5"})
# a recovery behind a bundle its holder signed: h1, h2 and h3 sign b1 and b2 (on b1); r:h3 then recovers at b0
XB1 = nxt("b1", "b0", H3, ("h1", "h2", "h3"))
XB2 = nxt("b2", "b1", H3 + ("h4",), ("h1", "h2", "h3"), version=2)
XRC = nxt("rx", "b0", ("h1", "h2", "h3z"), ("r:h3",), recovers=("h3", "h3z"), recovery={"h1": "r:h1", "h2": "r:h2", "h3z": "r:h3z"})
CASES += [
    ("attack", "RJ0: a removed holder's recovery at b0 (h1, removed at b2, recovers to h1x) concludes, a sibling of b1, "
               "which h1 signed: no bundle it is behind, so S'' does not reach it (the statement residual's bundle form); "
               "a reader at b2 holds b2", RL + [RA], (), (), RD(anchor="b0", acks=("b2",)),
     {"concluded": {"ra": T}, "void": set(), "heads": ("b2",)}),
    ("attack", "RJ1: h3 alone joins b2 and ra (one charter): the join is counted over their fold (h3 and h1x), and h3 "
               "is one of two: refused", RL + [RA, RJX], (), (), RD(anchor="b0", acks=("jx",)),
     {"concluded": {"jx": Fa}, "heads": ("b0",)}),
    ("attack", "RS0: h3 recovers, and the room grows on it to five", SL, (), (), RD(anchor="b0", acks=("b3",)),
     {"void": set(), "heads": ("b3",), "holders": {"h1", "h2", "h3b", "h4", "h5"}}),
    ("attack", "RS1: r:h3 later signs a second recovery at b0: by T between the two, h1 and h2 built only on the first: "
               "the stale one is void, nothing is contested, and b3 stands", SL + [SRC2], (), (), RD(anchor="b0", acks=("b3",)),
     {"void": {"rc2"}, "heads": ("b3",), "holders": {"h1", "h2", "h3b", "h4", "h5"}}),
    ("attack", "RS2: h1 and h2 'settle' with a join naming b3 and the void rc2: a join of both lines is counted without "
               "the void bundle, over b3's five: two of five, void", SL + [SRC2, SJ], (), (), RD(anchor="b0", acks=("j",)),
     {"concluded": {"j": Fa}, "void": {"rc2"}, "heads": ("b0",)}),
    ("attack", "RS3: a third recovery at b0: void too", SL + [SRC2, SJ, SRC3], (), (), RD(anchor="b0", acks=("b3",)),
     {"void": {"rc2", "rc3"}, "heads": ("b3",)}),
    ("attack", "a join naming a self-forked (S'') predecessor: s1 (void by T) and b2, joined by majorities of both; "
               "the counts decide: the join stands, its payload states its holders outright, and s1 stays void", [B0, nxt("s1", "b0", H3 + ("h8", "h9"), ("h1", "h2")),
                                                                         nxt("b1", "b0", H3 + ("h4",), ("h1", "h2", "h3")),
      nxt("b2", "b1", H3 + ("h4", "h5"), ("h1", "h2", "h4"), version=2),
      nxt("m", ("b2", "s1"), H3 + ("h4", "h5", "h8", "h9"), ("h1", "h2", "h3", "h8", "h9"), version=3)], (), (),
     RD(anchor="b0", acks=("m",)), {"concluded": {"m": T}, "void": {"s1"}, "heads": ("m",),
                                    "holders": {"h1", "h2", "h3", "h4", "h5", "h8", "h9"}}),
    ("attack", "a recovery is not exempt from S'': h3 signed b1 and b2, then its recovery key recovers it at b0; behind "
               "b2, self-forked, and by T (h1 and h2 built only on b1 and b2) void", [B0, XB1, XB2, XRC], (), (),
     RD(anchor="b0", acks=("b2", "rx")), {"void": {"rx"}, "heads": ("b2",)}),
    ("attack", "G1: removed holders h1 and h2 grant on b0; at b2 (h3 h4 h5) they are no voices in force: refused",
     RL, (), (GR("g1", "b0", "uX", "room", ("h1", "h2")),), RD(anchor="b0", acks=("b2",)),
     {"grant": {"g1": (False, "grant_voices_not_in_force")}}),
    ("attack", "RJ0 read by both, ra acknowledged first: ra is behind b2 for every reader that acknowledged b2, "
               "whatever it acknowledged earlier: void, and the reader holds b2", RL + [RA], (), (),
     RD(anchor="b0", acks=("ra", "b2")), {"heads": ("b2",), "holders": {"h3", "h4", "h5"}}),
    ("attack", "RJ0 by a reader that acknowledged b2 first: ra is behind its line, void for it", RL + [RA], (), (),
     RD(anchor="b0", acks=("b2", "ra")), {"heads": ("b2",)}),
    ("attack", "a join heals the fork: jx joins b2 and ra by majorities of both; for a reader at b2 ra is void, but "
               "jx (naming b2, the reader's own newest) is not behind, and the reader that acknowledges it holds jx",
     RL + [RA, nxt("jx", ("b2", "ra"), ("h3", "h4", "h1x"), ("h3", "h4", "h1x"), version=3,
                   recovery={"h3": "r:h3", "h4": "r:h4", "h1x": "r:h1x"})], (), (), RD(anchor="b0", acks=("b2", "jx")),
     {"concluded": {"jx": T}, "heads": ("jx",), "holders": {"h3", "h4", "h1x"}}),
    ("attack", "RJ1 with ra under a different charter: h3 alone joins b2 and ra; one of b2's three: refused (only the "
               "per-predecessor count closes this cheap-tip shape)",
     RL + [dict(RA, charter=C1), nxt("jx", ("b2", "ra"), ("h3",), ("h3",), version=3, charter=C1, recovery={"h3": "r:h3"})],
     (), (), RD(anchor="b0", acks=("jx",)), {"concluded": {"jx": Fa}}),
    ("attack", "the mirror: b1 removes h3 (h1 h2), and a sibling recovery rotates h3 to h3b; read by both, the "
               "rotation follows the seat out", [B0, nxt("b1", "b0", ("h1", "h2"), ("h1", "h2")), REC], (), (),
     RD(anchor="b0", acks=("b1", "rc")), {"heads": ("b1", "rc"), "holders": {"h1", "h2"}}),
    ("attack", "a join naming both that seats the holder again is a new seating, by the join's own count, under the "
               "key its payload states (h3b): h1 and h2 of b1's two and of rc's three",
     [B0, nxt("b1", "b0", ("h1", "h2"), ("h1", "h2")), REC,
      nxt("j", ("b1", "rc"), ("h1", "h2", "h3b"), ("h1", "h2"), version=2, recovery={"h1": "r:h1", "h2": "r:h2", "h3b": "r:h3b"})],
     (), (), RD(anchor="b0", acks=("j",)), {"concluded": {"j": T}, "holders": {"h1", "h2", "h3b"}}),
    ("attack", "EDGE (the stated residual: a reader with no acknowledgement takes its first head from a member it "
               "trusts, CC 3.3.4): in the seizure world (b2, and the cheap tip ra under another charter), a reader with "
               "no acknowledgement is at its anchor, b0; h3's lone grant on b2 is not in its lineage and does not "
               "resolve", RL + [dict(RA, charter=C1)], (), (GR("g3", "b2", "uX", "room", ("h3",)),), ANC,
     {"heads": ("b0",), "holders": set(H3), "grant": {"g3": (False, "grant_count_short")}}),
    ("attack", "G2: a grant's named bundles are an antichain: h3 and h4 naming (b2, b0) conclude nothing",
     [B0, dict(RB1, charter=C1), dict(RB2, charter=C1)], (), (GR("g3", ("b2", "b0"), "uX", "room", ("h3", "h4")),),
     RD(anchor="b0", acks=("b2",)), {"row": {"g3": False}, "grant": {"g3": (False, "grant_bundles_not_antichain")}}),
]
# the re-attack on 272fcd6 (ao, g3, gl): the line is monotone, and grants resolve by the in-force count
AOS0 = nxt("s0", "b0", ("h1", "h2", "X"), ("h1", "h2"))             # removed h1 and h2's old-majority sibling at b0
AO = RL + [AOS0]
GLB1 = nxt("b1", "b0", ("h1", "h2", "h3", "h4"), ("h1", "h2", "h3"))
GLG = GR("g0", "b0", "uX", "room", ("h1", "h2", "h3"))
CASES += [
    ("attack", "AO1: a reader that acknowledged s0, then b2: s0 names b0, strictly in the past of b2's head b1, so it "
               "is behind b2 for every reader that acknowledged b2: void, and the reader holds b2", AO, (), (),
     RD(anchor="b0", acks=("s0", "b2")), {"heads": ("b2",), "holders": {"h3", "h4", "h5"}}),
    ("attack", "AO2: acknowledged b1, s0, then b2: the same", AO, (), (), RD(anchor="b0", acks=("b1", "s0", "b2")),
     {"heads": ("b2",), "holders": {"h3", "h4", "h5"}}),
    ("attack", "AO3: a reader that acknowledged only s0: h1 and h2 signed s0 (cutting h3) and b1 (keeping it) at b0, "
               "so by rule 6 they have no say on either; neither counts, and the reader is at b0 (the residual closes)",
     AO, (), (), RD(anchor="b0", acks=("s0",)), {"heads": ("b0",), "holders": set(H3)}),
    ("attack", "AO1h: an honest grant on b2 by h3 and h4 resolves for the reader at b2", AO, (),
     (GR("gh", "b2", "uY", "room", ("h3", "h4")),), RD(anchor="b0", acks=("s0", "b2")), {"grant": {"gh": (True, None)}}),
    ("attack", "G5: removed holders' grant on b0, the reader's later acceptance edge naming it: no voices in force at "
               "b2, refused", RL, (), (GR("g1", "b0", "uX", "room", ("h1", "h2")), AK("k2", "b2", names=("g1",))),
     RD(anchor="b0", acks=("b2",)), {"grant": {"g1": (False, "grant_voices_not_in_force")}}),
    ("attack", "GL1: an honest grant by h1, h2 and h3 on b0, the reader at b1 (h1..h4): three of four, it resolves",
     [B0, GLB1], (), (GLG,), RD(anchor="b0", acks=("b0", "b1")), {"grant": {"g0": (True, None)}}),
    ("attack", "GL4: the same for a reader that acknowledged b1 only", [B0, GLB1], (), (GLG,), RD(anchor="b0", acks=("b1",)),
     {"grant": {"g0": (True, None)}}),
    ("attack", "the turnover: b2 (by h1, h2 and h3 of b1's four) leaves h3 h4 h5; g0's voices are one of three, and it "
               "lapses", [B0, GLB1, nxt("b2", "b1", ("h3", "h4", "h5"), ("h1", "h2", "h3"), version=2)], (), (GLG,),
     RD(anchor="b0", acks=("b1", "b2")), {"heads": ("b2",), "grant": {"g0": (False, "grant_voices_not_in_force")}}),
]


# the third attack (dp.py): a sibling chain t1, t at b1 by h1, h2 (removed at b2) and the double-signing h3
DB1 = nxt("b1", "b0", H5, ("h1", "h2"))
DB2 = nxt("b2", "b1", ("h3", "h4", "h5"), ("h3", "h4", "h5"), version=2)
DT1 = nxt("t1", "b1", ("h1", "h2", "h3", "X"), ("h1", "h2", "h3"), version=2)
DT = nxt("t", "t1", ("h1", "h2", "h3", "X"), ("h1", "h2", "h3"), version=3)
DB3 = nxt("b3", "b2", ("h3", "h4", "h5", "h6"), ("h4", "h5", "h3"), version=3)
DL = [B0, DB1, DB2, DT1, DT]
DS = nxt("s", "b1", ("h3", "h4", "h5"), ("h3", "h4", "h5"), version=2, names=("b2", "t1"))   # rule 3: names both
CASES += [
    ("rules", "DP0: a reader that acknowledged b2: h3 signed b2 (cutting h1 h2) and t1 (keeping them) at b1: no say on "
              "either (rule 6), and b2 and t1 are two of b1's five: neither counts; the reader is at b1", DL, (), (),
     RD(anchor="b0", acks=("b2",)), {"heads": ("b1",), "holders": set(H5)}),
    ("rules", "DP1, EDGE (the stated residual: the swing holder h3 went over): acknowledging b2 then t: b2 is behind "
              "t, void by the reader's line and no input to rule 6, so t1 and t count for it (an acknowledgement "
              "settles, as b3's does in order case (1))", DL, (), (), RD(anchor="b0", acks=("b2", "t")),
     {"heads": ("t",), "holders": {"h1", "h2", "h3", "X"}}),
    ("rules", "DP2, the same edge: a new reader acknowledging only t holds t", DL, (), (), RD(anchor="b0", acks=("t",)),
     {"heads": ("t",)}),
    ("rules", "DP3: a reader acknowledging both b3 and t: each line holds the other side's base void (t1 behind b3, b2 "
              "behind t), so neither stands for it, and it falls back to b1 where they meet", DL + [DB3], (), (),
     RD(anchor="b0", acks=("b2", "b3", "t")), {"heads": ("b1",), "holders": set(H5)}),
    ("rules", "order case (1): the honest line advanced first (b3), a reader at b3: t1 is behind its line, and b2 and b3 "
              "stand", [B0, DB1, DB2, DB3, DT1], (), (), RD(anchor="b0", acks=("b3",)), {"heads": ("b3",)}),
    ("rules", "order case (2): a reader that acknowledged only b2, holding t1 and b3: t1 contests b2 (rule 6), and b3 "
              "is built on it: at b1, in any arrival order", [B0, DB1, DB2, DB3, DT1], (), (), RD(anchor="b0", acks=("b2",)),
     {"heads": ("b1",)}),
    ("rules", "and its own acknowledgement of b3 settles it (the store acknowledges the newest head it holds)",
     [B0, DB1, DB2, DB3, DT1], (), (), RD(anchor="b0", acks=("b2", "b3")), {"heads": ("b3",)}),
    ("rules", "rule 3: a bundle at b1 naming both b2 and t1 decides, counted over b1's five: h3, h4 and h5 (h3's voice "
              "counts on a row naming both)", DL + [DS], (), (), RD(anchor="b0", acks=("s",)),
     {"concluded": {"s": T}, "heads": ("s",), "holders": {"h3", "h4", "h5"}}),
    ("rules", "DP5, the control: h1 and h2 alone at b1 are two of five: t1 concludes nothing",
     [B0, DB1, DB2, nxt("t1", "b1", ("h1", "h2", "X"), ("h1", "h2"), version=2)], (), (), RD(anchor="b0", acks=("b2",)),
     {"concluded": {"t1": Fa}, "heads": ("b2",)}),
    ("rules", "the residual, stated: a five-holder roster split two against two: the swing holder decides, and if it "
              "has gone over, a majority of the holders at b1 is against the honest two; nothing in rows can do better "
              "(h3 signs t1 alone with h1 and h2: t1 counts, three of five)",
     [B0, DB1, DT1], (), (), RD(anchor="b0", acks=("t1",)), {"heads": ("t1",)}),
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
    ("stalled is read over the founders, whatever scope the widening states: live, counted `member`",
     [GI, RCV(names=("g",), counted="member")], ROOT_ROWS, (GOK,), ANC, False, "not_stalled", False),
    ("the grant names another room", STALLED + [RCV()], ROOT_ROWS, (dict(GOK, scope="other"),), ANC, False,
     "grant_scope_not_this_room", False),
    ("the grant names a node key", STALLED + [RCV()], ROOT_ROWS, (dict(GOK, identity=("user", "node")),), ANC, False,
     "grant_identity_not_user", False),
    ("the widening is signed by another key than the grant names", STALLED + [RCV()], ROOT_ROWS, (dict(GOK, to="f5"),),
     ANC, False, "not_signed_by_named_key", False),
    ("the grant's count is short: h1 alone of three", STALLED + [RCV()], ROOT_ROWS, (dict(GOK, signers=("h1",)),), ANC,
     False, "grant_count_short", False),
    ("the grant names b0, and this node's bundle in force is b1 (h1..h4): h1 and h2 are two of four, the grant lapses",
     STALLED + [RCV()], LIN, (GOK,), RD(anchor="b0", acks=("b1",)), False, "grant_voices_not_in_force", False),
    ("a grant by h1, h2 and h3 is three of four there, and the charter carries the duty: it resolves",
     STALLED + [RCV()], LIN, (dict(GOK, signers=("h1", "h2", "h3")),), RD(anchor="b0", acks=("b1",)), True, None, True),
    ("the same where b1's charter drops the duty", STALLED + [RCV()], [B0, dict(LIN[1], charter=C2)],
     (dict(GOK, signers=("h1", "h2", "h3")),), RD(anchor="b0", acks=("b1",)), False, "grant_scope_not_in_force", False),
    ("G4: a grant by removed holders h1 and h2 naming b0, the reader at b2: no voices in force, refused",
     STALLED + [RCV()], RL, (GOK,), RD(anchor="b0", acks=("b2",)), False, "grant_voices_not_in_force", False),
    ("the reader's anchor names no first bundle", STALLED + [RCV()], ROOT_ROWS, (GOK,), RD(anchor="zz"), False,
     "genesis_bundle_not_anchored", False),
    ("two tips: a grant on s1 by h1, h2 and h4, signers who hold only s1: three of s1's four",
     STALLED + [RCV()], FORK,
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
          "charter_folds", "anchor_unread", "inforce_global", "root_sf_unread", "root_t_unread",
          "grant_count_unread", "grant_charter_unread", "grant_scope_unread", "recovery_fork_both", "joins_fork_both",
          "grant_head_unread", "join_common_base", "recovery_exempt", "recovery_t_unread",
          "join_void_prev_blocks", "grant_antichain_unread", "regime_reads_commitments", "reader_line_unread",
          "rotation_outlives_seat", "retired_unread", "join_prev_unread", "cosign_unread", "double_signer_voices")


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


# sub_delegation from the root's charter (for the delegation gate): (name, bundles, grants, reader, grant, answer)
CSUB = {"name": "c0s", "duties": ("infra",), "sub_delegation": ("infra",)}
SUB_CASES = [
    ("the charter in force carries sub_delegation for the grant's duty", [dict(B0, charter=CSUB)],
     (GR("gA", "b0", "uA", "room", ("h1", "h2")),), ANC, "gA", True),
    ("it does not", [B0], (GR("gA", "b0", "uA", "room", ("h1", "h2")),), ANC, "gA", False),
    ("the grant does not resolve for the reader: None", [B0], (GR("gA", "b0", "uA", "room", ("h1",)),), ANC, "gA", None),
    ("the scope in force decides: a later bundle dropping it", [dict(B0, charter=CSUB), nxt("b1", "b0", H3, ("h1", "h2", "h3"))],
     (GR("gA", "b0", "uA", "room", ("h1", "h2")),), RD(anchor="b0", acks=("b1",)), "gA", False),
]


def run_sub():
    return ["sub %s: got %s" % (n, got) for n, bs, gs, rd, gid, want in SUB_CASES
            for got in [RT.Root(bs, (), gs).sub_delegation(gid, rd)] if got != want]


def reader_vectors():
    """For Verify: what a reader acts on at UNJOINED tips, per case: the bundles, the reader, the tips in force, and
    the holders and seats in force, with the reason (one regime: the guarded fold; regimes differ: the common holders
    and seats), and what intersecting would give, for contrast."""
    import json
    out = []
    for rule, name, bs, rv, gs, rd, _ in CASES:
        R = RT.Root(bs, rv, gs)
        hs = R.heads(rd)
        if hs is None or len(hs) < 2: continue
        f = R.in_force(rd)
        same = len({R.regime(t) for t in hs}) == 1
        meet = frozenset.intersection(*[frozenset(R.by[t]["holders"]) for t in hs])
        meet_s = frozenset.intersection(*[frozenset(R.by[t]["seats"]) for t in hs])
        out.append({"name": rule + ": " + name,
                    "bundles": [{"id": b["id"], "prev": list(b["prev"]), "version": b["version"], "family": b["family"],
                                 "holders": list(b["holders"]), "seats": list(b["seats"]),
                                 "charter": json.dumps(b["charter"], sort_keys=True), "recovers": list(b["recovers"]) if b.get("recovers") else None,
                                 "stmts": [[k, i] for k, i in b["stmts"]], "iat": b["iat"]} for b in bs],
                    "revokes": [{"key": r["key"], "bound": r["bound"]} for r in rv],
                    "reader": {"anchor": rd["anchor"], "acks": list(rd["acks"])},
                    "tips": list(hs), "holders": sorted(f[0]), "seats": sorted(f[1]),
                    "reason": "one regime: the guarded fold" if same else "regimes differ: the common holders and seats",
                    "intersect": {"holders": sorted(meet), "seats": sorted(meet_s)},
                    "intersect_differs": sorted(meet) != sorted(f[0]) or sorted(meet_s) != sorted(f[1])})
    return {"about": "what a reader acts on at unjoined tips (models/trust_root/check_root.py, root.py fold): the fold "
                     "where the tips' regimes (their charters, as one value, without recovery_commitments) are equal; "
                     "the common holders and seats where they differ", "cases": out}


import json
def benc(b):
    return {"id": b["id"], "family": b["family"], "version": b["version"], "prev": list(b["prev"]),
            "holders": list(b["holders"]), "seats": list(b["seats"]),
            "charter": json.dumps(b["charter"], sort_keys=True), "duties": sorted(RT.duties(b["charter"])),
            "sub_delegation": sorted(RT.sub_delegations(b["charter"])),
            "iat": b["iat"], "recovery": [[k, v] for k, v in sorted(b["recovery"].items())],
            "names": list(b.get("names", ())),
            "recovers": list(b["recovers"]) if b.get("recovers") else None,
            "stmts": [[k, i] for k, i in b["stmts"]]}
def genc(g):
    if g["kind"] == "ack": return {"id": g["id"], "kind": "ack", "head": g["head"], "names": list(g["names"])}
    if g["kind"] == "cosign": return {"id": g["id"], "kind": "cosign", "of": g["of"], "signers": [g["signer"]],
                                      "names": list(g["names"])}
    return {"id": g["id"], "kind": "grant", "bundles": list(g["bundles"]), "names": list(g["names"]), "to": g["to"], "scope": g["scope"], "signers": list(g["signers"]),
            "identity": list(g["identity"]), "duty": g["duty"]}
def renc(rd):
    if rd is None: return None
    return {"anchor": rd["anchor"], "thumbs": sorted(rd["thumbs"]) if rd["thumbs"] is not None else None,
            "acks": list(rd["acks"])}


def fixture(with_refs):
    """The cases as a fixture for the crate (tests/root.rs): every bundle's count, the void, and the reader's heads,
    holders, seats and grants, as the model gives them; and the stalled recoveries with their seat rows."""
    cases = []
    def one(rule, name, bs, rv, gs, rd, line):
        R = RT.Root(bs, rv, gs)
        f = R.in_force(rd)
        hs = R.heads(rd)
        cases.append({"name": rule + ": " + name, "bundles": [benc(b) for b in bs],
                      "revokes": [{"key": r["key"], "bound": r["bound"]} for r in rv], "grants": [genc(g) for g in gs],
                      "reader": renc(rd), "concluded": {b["id"]: R.counted(b["id"])[0] for b in bs},
                      "void": sorted(R.void()), "heads": list(hs) if hs is not None else None,
                      "holders": sorted(f[0]) if f else None, "seats": sorted(f[1]) if f else None,
                      "grant": {g["id"]: list(R.grant_in_force(g["id"], rd)) for g in gs if g["kind"] == "grant"},
                      "row": {g["id"]: R.grant_row(g["id"]) for g in gs if g["kind"] == "grant"}, "line": line})
    for rule, name, bs, rv, gs, rd, _ in CASES:
        one(rule, name, bs, rv, gs, rd, False)
    rec = []
    for name, rows, bs, gs, rd, c, why, f4 in RECOVERY:
        refs = {}
        rec.append({"name": name, "rows": with_refs(rows, refs), "refs": refs,
                    "bundles": [benc(b) for b in bs] if bs is not None else None, "grants": [genc(g) for g in gs],
                    "reader": renc(rd), "concluded": c, "reason": why, "f4": f4})
    sub = [{"name": n, "bundles": [benc(b) for b in bs], "grants": [genc(g) for g in gs], "reader": renc(rd),
            "grant": gid, "sub_delegation": want} for n, bs, gs, rd, gid, want in SUB_CASES]
    return {"cases": cases, "recovery": rec, "sub_delegation": sub}


def main():
    bad = run() + run_recovery() + run_sub()
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
