#!/usr/bin/env python3
"""
check_window_rows.py: the moderation windows land by signed rows (CIRISConstitution#221).

The ruling on #221: a member's vote on a moderation action where no moderator acts is a ballot of
`ballot:moderation_action` (dimension `ballot:moderation_action:v1`). It names the proposal it answers and carries
`for` or `against`; a contrary voice is a vote against. One ballot a person, folded as `ballot:moderator` is: agreeing
ballots are one, and disagreeing unwithdrawn ballots are none until a withdrawal.

    the ballot     an answer a "voted" clause reads (window.ballot_words: its value `for` and its `against`)
    the fold       window.table_outcome's K.group(..., "one", ...): a voice that says two things says nothing (the
                   crate's ops::one). It is the same rule the ranked count reads for `ballot:moderator`
                   (ranked.rs: "a person with two different rankings has no ballot"); this file adds no second fold
    a withdrawal   window.unwithdrawn: a `withdraw` row naming a ballot, signed by that ballot's signer, makes it no
                   ballot (CC 2.4.1.1 rule 1; `ballot:moderator`'s undo is its signer's withdrawal). Another key's
                   withdrawal of it does not conclude (seat.seat_rule), so it withdraws nothing. A withdrawal
                   concurrent with a landing is recounted with it, as an answer is (CC 2.7.5)
    the landing    a `window:landed` row naming the signer's `window:held` row (W1), of a key of the concluder's
                   scope at the opener's head; a key with no seat there lands nothing; the overturn's author is no
                   concluder (W2: out of its count)

Part 1. The window adversary table's rows that name #221 (window.adversary_table), each read once as a batch and
again in arrival orders of its rows (every order up to six rows above the founding one, else the batch order, its
reverse and forty shuffles): the property holds under recount, and every order gives the batch's answer.

Part 2. Planted breaks, each of which must break a row of Part 1:
    ballot_withdrawal_unread   a withdrawn ballot is still a ballot
    withdrawal_not_recounted   a withdrawal concurrent with a landing is not read with it
    author_concludes           the act's author signs the overturn's receipt and landing (W2: it is no concluder)
    ballot_word_act            the fallback's ballot says `act` (the word before the ruling)

Part 3. What #221 and the text do not decide, printed as OPEN with the candidate answers. The adversary table's OPEN
rows have no property (`-`): they show what is built.

    python3 -I check_window_rows.py      exit 1 on any difference
"""
import copy
import itertools
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import window as WN  # noqa: E402

CK, K = WN.CK, WN.K
LEDGER = "CIRISConstitution#221"

OPEN = (
    ("a withdrawn objection or approval", "whether an answer that is no ballot (the overturn's objection, the self "
     "roster's approval or objection) is still a voice once its signer withdrew it. (a) it is: only a ballot is read "
     "as withdrawn; built. (b) it is not, as a ballot (objection:{state} is withdrawn by its signer)"),
    ("W4, the landing binds its objections", "derived, not built: switch `landing_binds_objections` (an overturn "
     "objection concurrent with the landing is not recounted). The rows it changes are printed above"),
    ("the door model", "formal/causal_kernel/door.py and door_text.tsv are the Constitution's, not this repository's"),
)


def mine(table):
    return [t for t in table if LEDGER in t["property"]]


def rows_of():
    out = {}
    for world in WN.WORLDS:
        title, cases = world()
        for name, rows, prop, need in cases:
            if LEDGER in prop:
                out[(title, name)] = (rows, need)
    return out


def read(S):
    return ({r["id"]: bool(S.C.get(r["id"])) for r in S.rows}, WN.outcomes(S, "p"))


def orders(rows):
    tail = rows[1:]
    if len(tail) <= 6:
        return [list(p) for p in itertools.permutations(tail)]
    rnd = random.Random(len(tail))
    out = [tail[::-1]]
    for _ in range(40):
        p = list(tail)
        rnd.shuffle(p)
        out.append(p)
    return out


def broken(table):
    return [t for t in mine(table) if t["needs"] is not None and not t["holds"]["recount"]]


PLANTS = (
    ("ballot_withdrawal_unread", lambda: WN.MUT.add("ballot_withdrawal_unread")),
    ("withdrawal_not_recounted", lambda: WN.MUT.add("withdrawal_not_recounted")),
    ("author_concludes", lambda: WN.MUT.add("author_concludes")),
    ("ballot_word_act", lambda: WN.WINDOWS["moderation_fallback"].update(
        at_close=tuple(("act",) + c[1:] for c in WN.WINDOWS["moderation_fallback"]["at_close"]))),
)


def main():
    problems, n_orders = [], 0
    table = WN.adversary_table()
    rows = rows_of()
    for t in mine(table):
        if t["needs"] is not None and not t["holds"]["recount"]:
            problems.append("recount BROKEN: %s: %s" % (t["window"], t["case"]))
        rs, _ = rows[(t["window"], t["case"])]
        want = read(CK.concluded(CK.kept(list(rs)), WN.rule))
        for p in orders(rs):
            n_orders += 1
            if read(CK.arrive([rs[0]] + p, WN.rule)) != want:
                problems.append("%s: order %s differs" % (t["case"], [r["id"] for r in p]))
                break
    caught = 0
    for name, plant in PLANTS:
        saved, mut = copy.deepcopy(WN.WINDOWS), set(WN.MUT)
        try:
            plant()
            hit = broken(WN.adversary_table())
        finally:
            WN.WINDOWS.clear(); WN.WINDOWS.update(saved)
            WN.MUT.clear(); WN.MUT.update(mut)
        caught += bool(hit)
        print("  plant %-26s %s" % (name, "caught by %d rows, first: %s" % (len(hit), hit[0]["case"]) if hit else "NOT CAUGHT"))
        if not hit:
            problems.append("plant %s not caught" % name)
    # W4 (derived): the rows of the whole table whose recount outcome changes if the overturn's landing binds its objections
    before = {(t["window"], t["case"]): t for t in table}
    WN.MUT.add("landing_binds_objections")
    try:
        after = WN.adversary_table()
    finally:
        WN.MUT.discard("landing_binds_objections")
    for t in after:
        b = before[(t["window"], t["case"])]
        if t["outcome"]["recount"] != b["outcome"]["recount"]:
            print("  W4 changes: %s: %s -> %s (%s)" % (t["case"], b["outcome"]["recount"], t["outcome"]["recount"],
                  "holds" if t["holds"]["recount"] else "BROKEN" if t["needs"] else "no property"))
    for what, why in OPEN:
        print("  OPEN %s: %s: %s" % (LEDGER, what, why))
    for p in problems:
        print(p)
    n = len(mine(table))
    print("RESULT: %s: %d rows of the adversary table name %s (%d with a property, %d OPEN), %d arrival orders, "
          "%d of %d planted breaks caught; %d OPEN questions"
          % ("ok" if not problems else "%d problems" % len(problems), n, LEDGER,
             sum(t["needs"] is not None for t in mine(table)), sum(t["needs"] is None for t in mine(table)), n_orders,
             caught, len(PLANTS), len(OPEN)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
