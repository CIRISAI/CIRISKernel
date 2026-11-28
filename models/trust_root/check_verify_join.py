#!/usr/bin/env python3
"""A differential against CIRISVerify's join vectors (genesis_join_v1.json, 46 cases): each case translated into the
root model's bundles, and the model's verdict, token, detail and placement (the holders seated and the holders whose
statements counted) compared with Verify's.

The vector file is read only, from a CIRISVerify checkout ($CIRISVERIFY, default ~/CIRISVerify, or the path given as the
first argument), and pinned by its sha256. Without it this check reports itself skipped.

The translation (Verify's generator, gen_genesis_join_v1.py, read case by case): holders A, B, C, D are the model's
keys a, b, c, d; A's key after its rotation or recovery is `an`, A's other key `a2`; a holder n's recovery commitment
is r:n, A's next one r2:a, the WRONG commitment `w`. A routine rotation is `rotates`, a recovery `recovers`. Versions
are Verify's less one (the model's first bundle is version 0). Five cases are of the wire alone (further_prev's
encoding: absent prev, an empty set, prev again, out of order, a bare digest); the model reads bundles, not bytes, and
those are reported as not modelled. Verify refuses a statement under a key no predecessor seats alone
(statement_kid_not_iss); the model counts no such statement, and the verdict is compared.

Run: python3 -I models/trust_root/check_verify_join.py [path to genesis_join_v1.json]
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import root as RT  # noqa: E402

SHA = "a39d354da9c4efb5585b031a31c56ee9d8d04f731b91775cdb2ffd64ae8da37c"
DEFAULT = os.path.join(os.environ.get("CIRISVERIFY", os.path.expanduser("~/CIRISVerify")), "src", "ciris-verify-core",
                       "tests", "vectors", "edition2", "genesis", "genesis_join_v1.json")
F, OTHER = "humanity-accord", "another-accord"
WHO = {"a": "A", "an": "A", "a2": "A", "r:a": "A", "r2:a": "A", "b": "B", "c": "C", "d": "D"}
WIRE = {"further_prev_without_prev", "further_prev_empty", "further_prev_names_prev", "further_prev_unsorted",
        "further_prev_bare_digest"}


def B(i, prev, holders, signers, version, family=F, recovery=None, **kw):
    rec = {k: "r:" + ("a" if k == "an" else k) for k in holders}
    rec.update(recovery or {})
    return RT.bundle(i, family, version, holders, prev=prev, stmts=[(k, 0) for k in signers], recovery=rec, **kw)


FIRST = B("first", (), ("a", "b", "c"), ("a", "b", "c"), 0)
S1 = B("swap_1", ("first",), ("a", "b", "d"), ("a", "b", "d"), 1)
S2 = B("swap_2", ("first",), ("a", "b", "d"), ("a", "b", "d"), 1)
ROT = B("rotation", ("first",), ("an", "b", "c"), ("a", "b", "c"), 1, rotates=("a", "an"))
REC = B("recovery", ("first",), ("an", "b", "c"), ("r:a",), 1, recovery={"an": "r2:a"}, recovers=("a", "an"))
W3 = {"a": "r:a", "b": "w", "d": "r:d"}
T_AB = B("third_signed_by_a", ("swap_1",), ("a", "b", "d"), ("a", "b"), 2, recovery=W3)
T_BD = B("third_not_signed_by_a", ("swap_1",), ("a", "b", "d"), ("b", "d"), 2, recovery=W3)
OF = B("first_of_another_lineage", (), ("a", "b", "c"), ("a", "b", "c"), 0, family=OTHER)
S2_BAD = B("swap_2", ("first",), ("a", "b", "d"), ("a",), 1)           # held, and not Valid
COM_J = {"an": "r2:a"}
ONE = B("first_of_one_holder", (), ("a",), ("a",), 0)
ONE_R = B("one_holder_recovery", ("first_of_one_holder",), ("an",), ("r:a",), 1, recovery={"an": "r2:a"},
          recovers=("a", "an"))
ONE_F = B("one_holder_fuse", ("first_of_one_holder",), ("a",), ("a",), 1, charter={"name": "c0", "duties": ("infra",),
                                                                                     "fuse": 3600})
J5 = B("join_on_the_recovery", ("third_not_signed_by_a", "recovery"), ("an", "b", "c", "d"), ("an", "b", "d"), 3,
       recovery={"an": "r2:a", "b": "w"})
JR = ("rotation", "swap_1")
JC = ("recovery", "swap_1")


def j(i, prev, holders, signers, version, **kw):
    return B(i, prev, holders, signers, version, **kw)


# case id -> (the bundles held besides the one asked, the bundle asked)
CASES = {
    "first": ([], FIRST),
    "swap_1": ([FIRST], S1),
    "swap_2": ([FIRST], S2),
    "rotation": ([FIRST], ROT),
    "recovery": ([FIRST], REC),
    "third_signed_by_a": ([FIRST, S1], T_AB),
    "third_not_signed_by_a": ([FIRST, S1], T_BD),
    "join_valid": ([FIRST, S1, S2], j("x", ("swap_1", "swap_2"), ("a", "b", "d"), ("a", "b"), 2)),
    "join_prev_not_least_id": ([FIRST, S1, S2], j("x", ("swap_2", "swap_1"), ("a", "b", "d"), ("a", "b"), 2)),
    "join_version_not_greatest_plus_one": ([FIRST, S1, S2], j("x", ("swap_1", "swap_2"), ("a", "b", "d"), ("a", "b"), 3)),
    "join_unequal_versions": ([FIRST, S1, S2, T_AB],
                              j("x", ("third_signed_by_a", "swap_2"), ("a", "b", "d"), ("a", "b"), 3, recovery=W3)),
    "join_prev_not_greatest_version": ([FIRST, S1, S2, T_AB],
                                       j("x", ("swap_2", "third_signed_by_a"), ("a", "b", "d"), ("a", "b"), 3,
                                         recovery=W3)),
    "join_names_a_predecessor_in_anothers_past": ([FIRST, S1, T_AB],
                                                  j("x", ("third_signed_by_a", "swap_1"), ("a", "b", "d"),
                                                    ("a", "b", "d"), 3, recovery=W3)),
    "join_further_predecessor_not_held": ([FIRST, S1], j("x", ("swap_1", "swap_2"), ("a", "b", "d"), ("a", "b"), 2)),
    "join_prev_not_held": ([FIRST, S2], j("x", ("swap_1", "swap_2"), ("a", "b", "d"), ("a", "b"), 2)),
    "join_no_predecessor_held": ([FIRST], j("x", ("swap_1", "swap_2"), ("a", "b", "d"), ("a", "b"), 2)),
    "join_predecessor_not_valid": ([FIRST, S1, S2_BAD], j("x", ("swap_1", "swap_2"), ("a", "b", "d"), ("a", "b"), 2)),
    "first_of_another_lineage": ([], OF),
    "join_across_lineages": ([FIRST, S1, OF],
                             j("x", ("swap_1", "first_of_another_lineage"), ("a", "b", "d"), ("a", "b", "d"), 2)),
    "join_rotated_holder_signs_under_each_key": ([FIRST, S1, ROT], j("x", JR, ("an", "b", "c", "d"), ("a", "an", "b"), 2)),
    "join_counted_without_the_rotated_holder": ([FIRST, S1, ROT], j("x", JR, ("an", "b", "c", "d"), ("b", "c", "d"), 2)),
    "join_majority_of_one_predecessor_only": ([FIRST, S1, ROT], j("x", JR, ("an", "b", "c", "d"), ("a", "b", "d"), 2)),
    "join_voice_under_a_key_no_predecessor_seats": ([FIRST, S1, ROT], j("x", JR, ("an", "b", "c", "d"), ("a2", "b"), 2)),
    "join_revives_a_key_one_branch_retired": ([FIRST, S1, ROT], j("x", JR, ("a", "b", "c", "d"), ("a", "an", "b"), 2)),
    "join_added_holder_unsigned": ([FIRST, S1, S2], j("x", ("swap_1", "swap_2"), ("a", "b", "c", "d"), ("a", "b", "d"), 2)),
    "join_added_holder_signs": ([FIRST, S1, S2], j("x", ("swap_1", "swap_2"), ("a", "b", "c", "d"), ("a", "b", "c"), 2)),
    "join_over_a_recovery": ([FIRST, S1, REC], j("x", JC, ("an", "b", "c", "d"), ("an", "b", "d"), 2, recovery=COM_J)),
    "join_replaced_key_is_no_voice": ([FIRST, S1, REC],
                                      j("x", JC, ("an", "b", "c", "d"), ("a", "an", "b", "c"), 2, recovery=COM_J)),
    "join_changed_commitment_holder_unsigned": ([FIRST, S1, REC],
                                                j("x", JC, ("an", "b", "c", "d"), ("b", "c", "d"), 2, recovery=COM_J)),
    "join_names_a_commitment_one_branch_spent": ([FIRST, S1, REC], j("x", JC, ("an", "b", "c", "d"), ("an", "b", "d"), 2)),
    "join_seats_the_key_a_recovery_replaced": ([FIRST, S1, REC],
                                               j("x", JC, ("a", "b", "c", "d"), ("an", "b", "d"), 2,
                                                 recovery={"a": "r2:a"})),
    "recovery_with_further_prev": ([FIRST, S1, S2],
                                   j("x", ("swap_1", "swap_2"), ("an", "b", "d"), ("r:a",), 2, recovery={"an": "r2:a"},
                                     recovers=("a", "an"))),
    "first_of_one_holder": ([], ONE),
    "one_holder_recovery": ([ONE], ONE_R),
    "one_holder_fuse": ([ONE], ONE_F),
    "join_predecessor_with_no_live_holder": ([ONE, ONE_R, ONE_F],
                                             j("x", ("one_holder_fuse", "one_holder_recovery"), ("an",), ("an",), 2,
                                               recovery={"an": "r2:a"})),
    "recovery_beside_a_sibling": ([FIRST, S1], REC),
    "recovery_behind_head": ([FIRST, S1, T_AB], REC),
    "recovery_behind_a_bundle_its_holder_did_not_sign": ([FIRST, S1, T_BD], REC),
    "join_on_the_recovery": ([FIRST, S1, T_BD, REC], J5),
    "recovery_read_again_under_its_own_successor": ([FIRST, S1, T_BD, J5], REC),
}


def model(case_id):
    """The model's verdict for one case: (verdict, token, detail, holders, counted)."""
    held, b = CASES[case_id]
    R = RT.Root(held + [b])
    if R.waits_on(b["id"]):
        assert R.refusal(b["id"]) == ("waiting", None)
        return ("waiting", None, None, (), ())
    r = R.refusal(b["id"])
    if r is not None:
        name, detail = r
        verdict = "invalid" if name == "genesis_bundle_malformed" else "nothing"
        return (verdict, name, detail, (), ())
    if b.get("recovers") is not None:
        voices = {b["recovers"][0]}
    elif not b["prev"]:
        voices = R.voices(b) & frozenset(b["holders"])
    else:
        req = set().union(*[ks for _, ks in R.join_signers(b)])
        voices = R.voices(b) & (R.base(b) | req)
    return ("valid", None, None, tuple(sorted({WHO[k] for k in b["holders"]})), tuple(sorted({WHO[k] for k in voices})))


def verify(c, who):
    e = c["expect"][0]
    pl = e.get("placement") or {}
    hs = tuple(sorted(who[x["identity_ref"]] for x in pl.get("holders", [])))
    ct = tuple(sorted({who[x] for x in pl.get("counted", [])}))
    return (e["verdict"], e.get("token"), e.get("detail"), hs, ct)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    if not os.path.exists(path):
        print("RESULT: skipped: no CIRISVerify vector file at %s" % path)
        return 0
    raw = open(path, "rb").read()
    if hashlib.sha256(raw).hexdigest() != SHA:
        print("RESULT: 1 problem: %s is not the pinned file (sha256 %s)" % (path, SHA))
        return 1
    d = json.loads(raw)
    who = {p["iss"]: n for n, p in d["parties"].items()}
    agree, differ, wire = 0, [], []
    for c in d["cases"]:
        if c["id"] in WIRE:
            wire.append(c["id"])
            continue
        if c["id"] not in CASES:
            differ.append("%s: no translation" % c["id"])
            continue
        m, v = model(c["id"]), verify(c, who)
        if m == v:
            agree += 1
        else:
            differ.append("%s: model %s, Verify %s" % (c["id"], m, v))
    for x in differ:
        print(x)
    print("RESULT: %s: %d of %d cases agree, %d of the wire alone (not modelled), %d differ" % (
        "ok" if not differ else "%d problems" % len(differ), agree, len(d["cases"]), len(wire), len(differ)))
    return 1 if differ else 0


if __name__ == "__main__":
    sys.exit(main())
