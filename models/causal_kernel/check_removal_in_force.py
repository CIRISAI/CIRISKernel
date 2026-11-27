#!/usr/bin/env python3
"""
check_removal_in_force.py: a moderator's lone removal of an AI agent's key is in force only while the end rule says
so (CC 4.5.13 with CC 2.4.1.1 and CC 4.5.5), as seat.py reads it.

A moderator's lone removal is an act under a standing, its `moderate` seat. The end rule of conferral_end.py
(models/tla/CONFERRAL_END.md, E2 to E8) answers it as it answers any act of a holder whose seat then ends. seat.py
re-expresses that rule over seat rows (seat.removal_in_force), and the seat walk counts a lone removal as a live
unseat only where it is in force over the rows held:

    the act     the removal, at the head it names
    the end     a row held that ends the remover's standing: its own laying down of the duty (a withdrawal of
                the offer, of its acceptance, or of its stay), a counted removal of it from the roster, or the
                other holders' counted withdrawal of its duty. Its head h_e: the heads a counted end names; for a
                withdrawal, the newest counted acts on the room in its past
    E7          a seat that gave the remover `moderate` at the act's head is live and has no end held: in force.
                A seat taken up after the act's head authorises nothing earlier, and nothing puts the act back in
                force once each such seat has an end: not the same offer accepted again, not a new conferral
                (CC 2.4.1.1: "from the end's head on it is not in force"; "A receipt ... revives no act"). A
                moderator seated again signs the removal again
    E4          the act has the end in its past: not counted
    E3          the act names a head later than h_e: not counted
    E8          otherwise counted at its own head, and in force only under a receipt of it, an `ack` row naming it,
                by a duty holder at its head other than the remover, that does not have the end in its past
    E2          and with no such receipt, not in force from h_e on
Out of force, the removal ends nothing for that reader: the agent's key is seated again. The answer is a function of
the set (every case is read in arrival orders), and at tips the lines read the removal as the whole set judges it.

Part 1. Cases, each a hand-written answer: which rows conclude, the roster (members and agents), and standings asked
by name. Each kind of end is a case with and without a receipt, and the three kinds answer alike: out of force
unless receipted, and for good (the remover's own laying down, the room's counted removal of it, the other holders'
counted withdrawal of its duty).
Part 2. Planted breaks (seat.MUT), each of which must change a case's answer:
    end_unread       the end is not read: a lone removal stays in force whatever ends its standing
    remover_receipt  a receipt by the remover itself keeps its own removal in force
    cascade          a lone removal out of force is still an end of the standing of the key it removes
    count_receipt_unread  the room's counted receipt is not read
    removed_receipt_kept  a receipt by a key whose seat a counted unseat beside it ends still keeps
    lifts_unread     a count end's `lifts` is not read
    conferrer_lift_unread  a conferrer's withdrawal of its own offer stating `lifts` lifts nothing
    cycle_one_then_other   a mutual pair of lone removals decided one after the other, not together
    count_unread_lone a removal the room's count carries is read as the moderator's lone act
    reseat_revives   the remover holding `moderate` again (its re-acceptance, a new conferral) puts its removal
                     back in force

    count_receipt_unchecked  the count's receipt read over any room, at any head, with the remover a voice
    founding_duty_unread     a receipter's duty from a founding record not read as a seat a counted unseat ends
    agent_receipt_kept       an agent duty holder's receipt keeps a lone removal (ruled: an agent's receipt is no receipt)
    remover_counted_over     the remover left in the denominator of the count's receipt (ruled R5: the room less it)
    lone_lifts / own_end_lifts  a lone removal, or the holder's own end, lifts receipts
    receipt_before_kept      a receipt made after a counted unseat of its signer's seat keeps
    failed_count_is_signers  a counted receipt that fails its count is read as its signer's own
    ordered_pair_cascade     an act decided before the verdict of an earlier act in its past that could end its
                             standing, that earlier act read as an end (cascade through an ordered pair)
    lone_any_object          a moderator's lone removal read over an object that is no community (a key's own)
    lift_no_floor            the members' check of one member's act (the lift, the count's receipt) with no floor
                             of two voices
    receipt_row_policy       the count's receipt read by the policy and need its row states (ruled: one fixed rule,
                             more than half of the persons of the room less the remover, never fewer than two)

Not here: a lone removal of a receipter voiding a receipt does not arise: a receipter is a person, and a lone
removal removes only an agent.

    python3 -I check_removal_in_force.py      exit 1 on any difference
"""
import itertools
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import seat as ST  # noqa: E402
import window as WN  # noqa: E402

CK, R = ST.CK, ST.R
OBJ, OV = "g", "moderation_overturn"
RULE = lambda r, P, past: WN.rule(r, P, past)
T, F = True, False


def admit(i, who, signers, heads, scope="member", cites=()):
    return ST.offer(i, signers[0], who, scope, OBJ, "group", tuple(heads) + tuple(cites), head=tuple(heads),
                    policy="community_invite", cosigners=tuple(signers[1:]) + ((who,) if who not in signers else ()))


def lone(i, by, who, heads, cites=()):
    """A moderator's lone removal of an agent's key, naming the overturn's window."""
    return ST.unseat(i, by, who, "agent", OBJ, "group", tuple(heads) + tuple(cites), head=tuple(heads),
                     policy="community_remove", window=OV)


def remove(i, who, signers, heads, cites=()):
    """The room's counted removal of a person."""
    return ST.unseat(i, signers[0], who, "member", OBJ, "group", tuple(heads) + tuple(cites), head=tuple(heads),
                     policy="community_remove", cosigners=tuple(signers[1:]))


def unduty(i, who, scope, signers, heads):
    """The other holders' counted withdrawal of a duty seat (CC 4.5.4 (iv))."""
    return ST.unseat(i, signers[0], who, scope, OBJ, "group", tuple(heads), head=tuple(heads), policy="duty_withdraw",
                     counted="duty", cosigners=tuple(signers[1:]))


def receipt(i, by, act, names=()):
    """A clean receipt of an act: an `ack` row naming it (`of`)."""
    return R(i, "ack", by, tuple(names) + (act,), of=act)


# three persons, each a founding moderator, and an agent's key admitted at "ag"
G = ST.found("g", "p1", ("p1", "p2", "p3"), {"moderate": ("p1", "p2", "p3")}, cosigners=("p2", "p3"))
W = [G, admit("ag", "AG", ("p1", "p2", "p3"), ("g",), "agent")]
X = lone("x", "p1", "AG", ("ag",))
P3, P23 = {"p1", "p2", "p3"}, {"p2", "p3"}
LAY = ST.withdraw("wm", "p1", "g", ("x",), scope="moderate")             # p1 lays down moderate, after its removal
OUT = remove("xp", "p1", ("p2", "p3"), ("x",))                            # the room's count removes p1
UND = unduty("xm", "p1", "moderate", ("p2", "p3"), ("x",))                # p2 and p3 withdraw p1's moderate
# a moderator by a conferred seat, accepted by its own row: q, admitted and conferred `moderate` by the holders
WQ = W + [admit("aq", "q", ("p1", "p2", "p3"), ("ag",)),
          ST.offer("cq", "p1", "q", "moderate", OBJ, "group", ("aq",), head=("aq",), policy="duty_confer", counted="duty",
                   cosigners=("p2",)),
          ST.accept("acq", "q", "cq"), lone("x", "q", "AG", ("acq",))]
PQ = P3 | {"q"}

PIN = "CIRISConstitution#218, pin list: "
# two agents' keys, A1 and A2, admitted by one row; A1 (and in the mutual case A2) conferred `moderate`, each by its own
# statement and its owner's signature (CC 4.5.4): OWN holds each agent key's registration and owner-binding (to "O" + key)


def owned(k):
    return [ST.offer("r" + k, k, k, "registered", k, "self"), ST.offer("o" + k, k, "O" + k, "owner", k, "self", ("r" + k,),
                                                                      cosigners=("O" + k,))]


OWN = owned("A1") + owned("A2") + owned("A3")
AGS = ST.offer("ags", "p1", ("A1", "A2"), "agent", OBJ, "group", ("g",), head=("g",), policy="community_invite",
               cosigners=("p2", "p3", "A1", "A2"))
CM1 = ST.offer("cm1", "p1", "A1", "moderate", OBJ, "group", ("ags", "oA1"), head=("ags",), policy="duty_confer",
               counted="duty", cosigners=("p2", "A1", "OA1"))
CM2 = ST.offer("cm2", "p1", "A2", "moderate", OBJ, "group", ("cm1", "oA2"), head=("cm1",), policy="duty_confer",
               counted="duty", cosigners=("p2", "A2", "OA2"))
WA = [G, AGS, *OWN, CM1]
B2 = [G, AGS, *OWN, CM1, CM2]                                    # both agents moderators
XA = lone("x", "A1", "A2", ("cm1",))                      # the agent moderator A1 removes A2 alone
YA = lone("y", "p1", "A1", ("x",))                        # p1 removes A1 alone, after x
LAYY = ST.withdraw("wm", "p1", "g", ("y",), scope="moderate")


def counted_receipt(i, signers, act, head):
    """The room's count's receipt of an act: an `ack` naming it, counted over the persons at its head."""
    return R(i, "ack", signers[0], (act,) + tuple(h for h in head if h != act), of=act, conf="group", obj=OBJ,
             head=tuple(head), policy="accord_majority", cosigners=tuple(signers[1:]))


RV = "CIRISConstitution#218, review of #48: "
AGS3 = ST.offer("ags", "p1", ("A1", "A2", "A3"), "agent", OBJ, "group", ("g",), head=("g",), policy="community_invite",
                cosigners=("p2", "p3", "A1", "A2", "A3"))
CM3 = ST.offer("cm3", "p1", "A3", "moderate", OBJ, "group", ("cm2", "oA3"), head=("cm2",), policy="duty_confer",
               counted="duty", cosigners=("p2", "A3", "OA3"))
W3A = [G, AGS3, *OWN, CM1, CM2]
# V1: a room p1 founded alone, p2 and p3 admitted after
G1 = ST.found("g", "p1", ("p1",), {"moderate": ("p1",)})
V1 = [G1, admit("a2", "p2", ("p1",), ("g",)), admit("a3", "p3", ("p1", "p2"), ("a2",)),
      admit("ag", "AG", ("p1", "p2", "p3"), ("a3",), "agent"), lone("x", "p1", "AG", ("ag",))]
# D: p2's moderate given by the founding record (D1) or by an offer (D4)
GD4 = ST.found("g", "p1", ("p1", "p2", "p3"), {"moderate": ("p1", "p3")}, cosigners=("p2", "p3"))
CD4 = ST.offer("cd", "p1", "p2", "moderate", OBJ, "group", ("g",), head=("g",), policy="duty_confer", counted="duty",
               cosigners=("p3", "p2"))


# (name, rows, {row: concludes}, roster, [(key, scope, stands)])
CASES = [
    # ---- the review of #48 (CIRISConstitution#218) -------------------------------------------------------------------
    (RV + "V1, the count's receipt at an old head: p1, alone in the room at g, writes a counted receipt there; after "
     "the count removes p1 stating lifts it keeps nothing (its head is older than the removal's)",
     V1 + [counted_receipt("qc", ("p1",), "x", ("g",)), dict(remove("xp", "p1", ("p2", "p3"), ("x",)), lifts=True)],
     {"x": T, "xp": T}, {"p2", "p3", "AG"}, []),
    (RV + "V1, the remover is no voice of the count's receipt: p1's counted receipt at the removal's head keeps nothing",
     V1 + [counted_receipt("qc", ("p1",), "x", ("x",)), ST.withdraw("wm", "p1", "g", ("x",), scope="moderate")],
     {"x": T}, {"p1", "p2", "p3", "AG"}, []),
    (RV + "V3, the count's receipt over another room: p2's counted receipt over a room it founded alone keeps nothing",
     W + [ST.offer("h", "p2", ("p2",), "member", "@", "self"), lone("x", "p1", "AG", ("ag",), ("h",)),
          dict(counted_receipt("qc", ("p2",), "x", ("x",)), obj="h"), LAY], {"x": T}, P3 | {"AG"}, []),
    (RV + "V4, an agent in no count: the one agent left writes a counted receipt over `agent`; it keeps nothing",
     W + [admit("a9", "A9", ("p1", "p2", "p3"), ("ag",), "agent"), lone("x", "p1", "AG", ("a9",)),
          dict(counted_receipt("qc", ("A9",), "x", ("x",)), counted="agent"), LAY], {"x": T}, P3 | {"AG", "A9"}, []),
    (RV + "O2, a mutual pair decided alone: A1 and A2 remove each other, and A1 removes A3 too, all at one head; the "
     "pair stays contested, so A1's removal of A3 is in force",
     W3A + [CM3, lone("x1", "A1", "A2", ("cm3",)), lone("x2", "A2", "A1", ("cm3",)), lone("w", "A1", "A3", ("cm3",))],
     {"x1": T, "x2": T, "w": T}, P3 | {"A1", "A2"}, [("A1", "moderate", T), ("A2", "moderate", T)]),
    (RV + "O4, an ordered pair: A1 removes A2, then A2 removes A1 with that removal in its past at the older head: A1's "
     "removal is in force and A2's is not counted (E4)",
     W3A + [lone("x1", "A1", "A2", ("cm2",)), lone("x2", "A2", "A1", ("cm2",), ("x1",))], {"x1": T, "x2": T},
     P3 | {"A1", "A3"}, [("A1", "moderate", T), ("A2", "agent", F)]),
    (RV + "K2, an agent's receipt is no receipt (ruled, CC 2.4.1.1): A3, an agent moderator, receipts p1's removal; "
     "A1 removes A3 beside it and then lays down its own moderate, so A1's removal is out of force, A3 stays, and "
     "A3's receipt keeps nothing: p1's removal is out of force",
     [G, ST.offer("ags", "p1", ("A1", "A3", "AG"), "agent", OBJ, "group", ("g",), head=("g",), policy="community_invite",
                  cosigners=("p2", "p3", "A1", "A3", "AG")), *OWN, CM1,
      ST.offer("cm3", "p1", "A3", "moderate", OBJ, "group", ("cm1", "oA3"), head=("cm1",), policy="duty_confer",
               counted="duty", cosigners=("p2", "A3", "OA3")),
      lone("x", "p1", "AG", ("cm3",)), receipt("q3", "A3", "x"), ST.withdraw("wm", "p1", "g", ("x",), scope="moderate"),
      lone("y", "A1", "A3", ("cm3",)), ST.withdraw("wa", "A1", "cm1", ("y",))],
     {"x": T, "y": T}, P3 | {"A1", "A3", "AG"}, [("A3", "moderate", T)]),
    (RV + "an agent's receipt is no receipt, alone: A3's receipt of p1's removal keeps nothing once p1 lays down "
     "moderate; p2's would",
     W3A + [CM3, lone("x", "p1", "A2", ("cm3",)), receipt("q3", "A3", "x"),
            ST.withdraw("wm", "p1", "g", ("x",), scope="moderate")], {"x": T}, P3 | {"A1", "A2", "A3"}, []),
    (RV + "D1, a receipter removed at the same time, its duty from the founding record: the count withdraws p2's "
     "moderate beside its receipt: void",
     W + [X, receipt("q2", "p2", "x"), unduty("xm", "p2", "moderate", ("p1", "p3"), ("x",)), LAY], {"x": T, "xm": T},
     P3 | {"AG"}, [("p2", "moderate", F)]),
    (RV + "D4, the same with p2's moderate conferred by an offer: void",
     [GD4, CD4, admit("ag", "AG", ("p1", "p2", "p3"), ("cd",), "agent"), lone("x", "p1", "AG", ("ag",)),
      receipt("q2", "p2", "x"), unduty("xm", "p2", "moderate", ("p1", "p3"), ("x",)), LAY], {"x": T, "xm": T},
     P3 | {"AG"}, [("p2", "moderate", F)]),
    (RV + "O5, an agent's receipt is no receipt, so it settles no pair: A3, an agent moderator, receipts x1; the "
     "pair stays contested",
     W3A + [CM3, lone("x1", "A1", "A2", ("cm3",)), lone("x2", "A2", "A1", ("cm3",)), receipt("q3", "A3", "x1")],
     {"x1": T, "x2": T}, P3 | {"A1", "A2", "A3"}, [("A1", "moderate", T), ("A2", "moderate", T)]),
    (RV + "a ring of three (ruled, CC 2.7.7 rule 5 read for a set): A1 removes A2, A2 removes A3, A3 removes A1, "
     "all at one head: all three out of force, all three seated, until a person's receipt or the count's settles it",
     W3A + [CM3, lone("x1", "A1", "A2", ("cm3",)), lone("x2", "A2", "A3", ("cm3",)), lone("x3", "A3", "A1", ("cm3",))],
     {"x1": T, "x2": T, "x3": T}, P3 | {"A1", "A2", "A3"}, []),
    (RV + "a lone removal lifts nothing: p1 removes A1 alone stating lifts; p2's receipt of A1's removal of A2 keeps it",
     WA + [XA, receipt("q2", "p2", "x"), dict(YA, lifts=True)], {"x": T, "y": T}, P3, []),
    (RV + "a receipt after the unseat is void: the count removes p2, and p2 then receipts the removal",
     W + [X, remove("xp2", "p2", ("p1", "p3"), ("x",)), receipt("q2", "p2", "x", ("xp2",)), LAY], {"x": T, "xp2": T},
     {"p1", "p3", "AG"}, []),
    # ---- CIRISConstitution#218, pin list -----------------------------------------------------------------------------
    (PIN + "no cascade: p1 removes the agent moderator A1 alone, then lays down moderate: that removal is out of "
     "force and ends no standing, so A1's own removal of A2 stays in force",
     WA + [XA, YA, LAYY], {"x": T, "y": T}, P3 | {"A1"}, [("A1", "moderate", T), ("A2", "agent", F)]),
    (PIN + "no cascade: the same with p1's removal of A1 in force: A1's standing ended at it, and A1's removal of A2 is "
     "out of force", WA + [XA, YA], {"x": T, "y": T}, P3 | {"A2"}, [("A1", "agent", F), ("A2", "agent", T)]),
    (PIN + "no cascade, a mutual pair (CC 2.7.7 rule 5: two cuts by keys of equal standing that undo each other stay "
     "contested): two agent moderators remove each other concurrently, unreceipted. Each counts at its own head, "
     "neither is in force: both agents stay seated and keep moderate",
     [G, AGS, *OWN, CM1, CM2, lone("x1", "A1", "A2", ("cm2",)), lone("x2", "A2", "A1", ("cm2",))], {"x1": T, "x2": T},
     P3 | {"A1", "A2"}, [("A1", "moderate", T), ("A2", "moderate", T)]),
    (PIN + "the mutual pair for a reader with an acknowledgement (CC 4.5.13; CC 2.7.7 rule 5): p3 has acknowledged the "
     "pair's common head (cm2), and reads as one with none: neither removal in force, both agent seats kept",
     [G, AGS, *OWN, CM1, CM2, lone("x1", "A1", "A2", ("cm2",)), lone("x2", "A2", "A1", ("cm2",)), receipt("k3", "p3", "cm2")],
     {"x1": T, "x2": T}, P3 | {"A1", "A2"}, [("A1", "moderate", T), ("A2", "moderate", T)], "p3"),
    (PIN + "an agent's receipt is no receipt: A1 receipts its own removal of A2; the pair stays contested",
     [G, AGS, *OWN, CM1, CM2, lone("x1", "A1", "A2", ("cm2",)), lone("x2", "A2", "A1", ("cm2",)), receipt("q1", "A1", "x1")],
     {"x1": T, "x2": T}, P3 | {"A1", "A2"}, [("A1", "moderate", T), ("A2", "moderate", T)]),
    (PIN + "a person's receipt settles it for that one, for a reader with an acknowledgement too",
     [G, AGS, *OWN, CM1, CM2, lone("x1", "A1", "A2", ("cm2",)), lone("x2", "A2", "A1", ("cm2",)), receipt("q1", "p2", "x1"),
      receipt("k3", "p3", "cm2")],
     {"x1": T, "x2": T}, P3 | {"A1"}, [("A1", "moderate", T), ("A2", "moderate", F), ("A2", "agent", F)], "p3"),
    (PIN + "no cascade, a mutual pair settled by a voice neither can remove: a person moderator receipts x1 only. x1 is in "
     "force, A2's agent seat and its duty end, and x2 is out of force",
     [G, AGS, *OWN, CM1, CM2, lone("x1", "A1", "A2", ("cm2",)), lone("x2", "A2", "A1", ("cm2",)), receipt("q1", "p2", "x1")],
     {"x1": T, "x2": T}, P3 | {"A1"}, [("A1", "moderate", T), ("A2", "moderate", F), ("A2", "agent", F)]),
    (PIN + "a count's own receipt: the room's count (p2 and p3 of three) receipts the removal; it stays in force after "
     "p1 lays down moderate", W + [X, counted_receipt("qc", ("p2", "p3"), "x", ("x",)), LAY], {"x": T}, P3, []),
    (PIN + "a count's own receipt: one person's counted receipt is no count (one of three), and keeps nothing",
     W + [X, counted_receipt("qc", ("p2",), "x", ("x",)), LAY], {"x": T}, P3 | {"AG"}, []),
    (PIN + "a receipt by a key removed at the same time: p2's receipt, and the room's removal of p2 beside it: void",
     W + [X, receipt("q2", "p2", "x"), LAY, remove("xp2", "p2", ("p1", "p3"), ("x",))], {"x": T, "xp2": T}, {"p1", "p3", "AG"},
     []),
    (PIN + "a receipt by a key removed later: p2's removal has the receipt in its past, and the receipt keeps",
     W + [X, receipt("q2", "p2", "x"), LAY, remove("xp2", "p2", ("p1", "p3"), ("q2",))], {"x": T, "xp2": T}, {"p1", "p3"}, []),
    (PIN + "a count end that lifts receipts: the room's count removes p1 stating `lifts`: p2's receipt keeps nothing",
     W + [X, receipt("q2", "p2", "x"), dict(OUT, lifts=True)], {"x": T, "xp": T}, P23 | {"AG"}, []),
    (PIN + "a count end that lifts receipts: the count's own receipt still keeps",
     W + [X, counted_receipt("qc", ("p2", "p3"), "x", ("x",)), dict(OUT, lifts=True)], {"x": T, "xp": T}, P23, []),
    (PIN + "a self end cannot lift (`lifts_on_own_end`, refused at the door; read as no lift): p1's laying down "
     "stating `lifts` leaves p2's receipt keeping",
     W + [X, receipt("q2", "p2", "x"), dict(LAY, lifts=True)], {"x": T}, P3, []),
    ("the removal with no end held: in force, the agent out", W + [X], {"x": T}, P3, [("p1", "moderate", T)]),
    # ---- the remover lays down its duty ---------------------------------------------------------------------------
    ("the remover lays down moderate after its removal: out of force, the agent seated again",
     W + [X, LAY], {"x": T, "wm": T}, P3 | {"AG"}, [("p1", "moderate", F), ("p1", "member", T)]),
    ("the same with a receipt of the removal by another holder: in force",
     W + [X, receipt("q2", "p2", "x"), LAY], {"x": T}, P3, [("p1", "moderate", F)]),
    ("a receipt that has the end in its past keeps nothing", W + [X, LAY, receipt("q2", "p2", "x", ("wm",))], {"x": T},
     P3 | {"AG"}, []),
    ("a receipt by the remover itself keeps nothing", W + [X, receipt("q1", "p1", "x"), LAY], {"x": T}, P3 | {"AG"}, []),
    ("a receipt by a key that holds no duty keeps nothing",
     W + [admit("an", "n", ("p1", "p2", "p3"), ("ag",)), lone("x", "p1", "AG", ("an",)), receipt("qn", "n", "x"), LAY],
     {"x": T}, P3 | {"n", "AG"}, []),
    ("the remover lays down moderate beside its removal (neither names the other): out of force",
     W + [X, ST.withdraw("wm", "p1", "g", ("ag",), scope="moderate")], {"x": T}, P3 | {"AG"}, []),
    ("the removal names the remover's laying down, at the head before it: it concludes, and is not counted (E4)",
     W + [ST.withdraw("wm", "p1", "g", ("ag",), scope="moderate"), lone("x", "p1", "AG", ("ag",), ("wm",))],
     {"x": T}, P3 | {"AG"}, []),
    ("the same with another holder's receipt of it: still not counted (E4); the receipt has the end in its past through "
     "the removal it names, so it keeps nothing either (E8), and no case can tell E4 from E8 here",
     W + [ST.withdraw("wm", "p1", "g", ("ag",), scope="moderate"), lone("x", "p1", "AG", ("ag",), ("wm",)),
          receipt("q2", "p2", "x")], {"x": T}, P3 | {"AG"}, []),
    ("the removal at a head with the laying down in its past does not conclude (no standing there)",
     W + [ST.withdraw("wm", "p1", "g", ("ag",), scope="moderate"), admit("j", "n", ("p2", "p3"), ("ag",), cites=("wm",)),
          lone("x", "p1", "AG", ("j",))], {"x": F}, P3 | {"n", "AG"}, []),
    ("the remover ends its stay after its removal: out of force",
     W + [X, ST.withdraw("wa", "p1", "g", ("x",))], {"x": T}, P23 | {"AG"}, [("p1", "member", F)]),
    ("a moderator by a conferred seat withdraws its acceptance after its removal: out of force",
     WQ + [ST.withdraw("wq", "q", "acq", ("x",))], {"x": T}, PQ | {"AG"}, [("q", "moderate", F)]),
    ("and accepts the same offer again: it holds moderate, and its removal stays out of force (nothing revives it)",
     WQ + [ST.withdraw("wq", "q", "acq", ("x",)), ST.accept("acq2", "q", "cq", ("wq",))], {"x": T}, PQ | {"AG"}, [("q", "moderate", T)]),
    ("seated again, it signs the removal again: the new removal is in force, the old one is not",
     WQ + [ST.withdraw("wq", "q", "acq", ("x",)), ST.accept("acq2", "q", "cq", ("wq",)), lone("x2", "q", "AG", ("acq2",))],
     {"x": T, "x2": T}, PQ, [("q", "moderate", T)]),
    ("another standing live at the removal's head: p1 holds a conferred moderate seat beside its founding one, lays "
     "the founding one down, then removes the agent: in force (E7)",
     W + [ST.offer("cm", "p2", "p1", "moderate", OBJ, "group", ("ag",), head=("ag",), policy="duty_confer", counted="duty",
                   cosigners=("p3", "p1")), ST.withdraw("wm", "p1", "g", ("cm",), scope="moderate"),
          lone("x", "p1", "AG", ("cm",), ("wm",))], {"cm": T, "x": T}, P3, [("p1", "moderate", T)]),
    # ---- the room's count removes the remover -----------------------------------------------------------------------
    ("the room's count removes the remover after its removal: out of force",
     W + [X, OUT], {"x": T, "xp": T}, P23 | {"AG"}, [("p1", "moderate", F)]),
    ("the same with a receipt by another holder: in force", W + [X, receipt("q2", "p2", "x"), OUT], {"x": T}, P23, []),
    ("the counted removal of a conferred moderator, and its acceptance again: the offer is cut, out of force",
     WQ + [remove("xq", "q", ("p1", "p2", "p3"), ("x",)), ST.accept("acq2", "q", "cq", ("xq",))], {"x": T, "xq": T}, P3 | {"AG"},
     [("q", "moderate", F)]),
    ("re-admitted and conferred `moderate` again: a seat taken up after the removal's head authorises nothing earlier; out of force",
     WQ + [remove("xq", "q", ("p1", "p2", "p3"), ("x",)), admit("aq2", "q", ("p1", "p2", "p3"), ("xq",)),
           ST.offer("cq2", "p1", "q", "moderate", OBJ, "group", ("aq2",), head=("aq2",), policy="duty_confer", counted="duty",
                    cosigners=("p2", "q"))],
     {"x": T, "cq2": T}, PQ | {"AG"}, [("q", "moderate", T)]),
    # ---- the other holders withdraw its duty --------------------------------------------------------------------------
    ("the other holders withdraw the remover's moderate after its removal: out of force",
     W + [X, UND], {"x": T, "xm": T}, P3 | {"AG"}, [("p1", "moderate", F), ("p1", "member", T)]),
    ("the same with a receipt by another holder: in force", W + [X, receipt("q3", "p3", "x"), UND], {"x": T}, P3, []),
    ("a removal the room's count carries, signed by the moderator with another: the count's act, not the moderator's; "
     "the moderator's laying down leaves it in force",
     W + [ST.unseat("x", "p1", "AG", "agent", OBJ, "group", ("ag",), head=("ag",), policy="community_remove",
                    cosigners=("p2",), window=OV), LAY], {"x": T}, P3, [("p1", "moderate", F)]),
    # ---- a removal at a later head than the end ---------------------------------------------------------------------------
    ("the removal names a head later than the end's, without the end in its past: not counted (E3), the agent seated",
     W + [remove("xp", "p1", ("p2", "p3"), ("ag",)), admit("j", "n", ("p2", "p3"), ("ag",)), lone("x", "p1", "AG", ("j",))],
     {"xp": T, "j": T, "x": T}, P23 | {"n", "AG"}, [("p1", "member", F)]),
    ("and a receipt does not bring it back",
     W + [remove("xp", "p1", ("p2", "p3"), ("ag",)), admit("j", "n", ("p2", "p3"), ("ag",)), lone("x", "p1", "AG", ("j",)),
          receipt("q2", "p2", "x")], {"x": T}, P23 | {"n", "AG"}, []),
    # ---- two tips --------------------------------------------------------------------------------------------------------
    ("two tips: the removal and the room's removal of the remover, both at the agent's admission: out of force, the agent seated",
     W + [X, remove("xp", "p1", ("p2", "p3"), ("ag",))], {"x": T, "xp": T}, P23 | {"AG"}, []),
    ("two tips with a receipt of the removal by another holder: in force",
     W + [X, receipt("q2", "p2", "x"), remove("xp", "p1", ("p2", "p3"), ("ag",))], {"x": T, "xp": T}, P23, []),
]


R5 = [ST.found("g", "p1", ("p1", "p2", "p3", "p4"), {"moderate": ("p1",)}, cosigners=("p2", "p3", "p4")),
      admit("ag", "AG", ("p1", "p2", "p3", "p4"), ("g",), "agent"), lone("x", "p1", "AG", ("ag",))]


# The reviewer's rows for the review of #48 (its script, s48/cases.py), each a case named with its ledger row.
def _review():
    Gv = ST.found("g", "p1", ("p1",), {"moderate": ("p1",)})
    A2v = ST.offer("a2", "p1", ("p2", "p3"), "member", OBJ, "group", ("g",), head=("g",), policy="community_invite",
                   cosigners=("p2", "p3"))
    AGv = ST.offer("ag", "p1", "AG", "agent", OBJ, "group", ("a2",), head=("a2",), policy="community_invite",
                   cosigners=("p2", "p3", "AG"))
    xv = lone("x", "p1", "AG", ("ag",))
    outv = dict(remove("xp", "p1", ("p2", "p3"), ("x",)), lifts=True)
    qg = R("qc", "ack", "p1", ("x", "g"), of="x", conf="group", obj=OBJ, head=("g",), policy="accord_majority")
    H = ST.found("h", "p1", ("p1",), {})
    qh = R("qh", "ack", "p1", ("x", "h"), of="x", conf="group", obj="h", head=("h",), policy="accord_majority")
    qo = R("qo", "ack", "p1", ("x", "h"), of="x", conf="group", obj=OBJ, over="h", head=("h",), policy="accord_majority")
    AGB = ST.offer("ag2", "p1", "B", "agent", OBJ, "group", ("ag",), head=("ag",), policy="community_invite",
                   cosigners=("p2", "p3", "B"))
    xb = lone("x", "p1", "AG", ("ag2",))
    qa = R("qa", "ack", "B", ("x",), of="x", conf="group", obj=OBJ, head=("x",), policy="accord_majority", counted="agent")
    B3 = [G, AGS3, *OWN, CM1, CM2]
    x1, x2, w = lone("x1", "A1", "A2", ("cm2",)), lone("x2", "A2", "A1", ("cm2",)), lone("w", "A1", "A3", ("cm2",))
    x2o = ST.unseat("x2", "A2", "A1", "agent", OBJ, "group", ("cm2", "x1"), head=("cm2",), policy="community_remove", window=OV)
    AGS13 = ST.offer("ags", "p1", ("A1", "A3"), "agent", OBJ, "group", ("g",), head=("g",), policy="community_invite",
                     cosigners=("p2", "p3", "A1", "A3"))
    cA1 = ST.offer("cmA1", "p1", "A1", "moderate", OBJ, "group", ("ags", "oA1"), head=("ags",), policy="duty_confer",
                   counted="duty", cosigners=("p2", "A1", "OA1"))
    cA3 = ST.offer("cmA3", "p1", "A3", "moderate", OBJ, "group", ("cmA1", "oA3"), head=("cmA1",), policy="duty_confer",
                   counted="duty", cosigners=("p2", "A3", "OA3"))
    AGk = ST.offer("ag", "p1", "AG", "agent", OBJ, "group", ("cmA3",), head=("cmA3",), policy="community_invite",
                   cosigners=("p2", "p3", "AG"))
    B5 = [G, AGS13, *OWN, cA1, cA3, AGk, lone("x", "p1", "AG", ("ag",)), receipt("q3", "A3", "x"),
          ST.withdraw("wm", "p1", "g", ("x", "q3"), scope="moderate")]
    y = lone("y", "A1", "A3", ("ag",))
    q2 = receipt("q2", "p2", "x")
    WQ0 = WQ[:-1]
    xq = lone("x", "p1", "AG", ("acq",))
    S3 = {"p1", "p2", "p3"}
    return [
        ("V1 base", [Gv, A2v, AGv, xv, outv], S3 - {"p1"} | {"AG"}, []),
        ("V1, p1's counted receipt at the old head g", [Gv, A2v, AGv, xv, qg, outv], {"p2", "p3", "AG"}, []),
        ("V3 base", W + [H, X, OUT], {"p2", "p3", "AG"}, []),
        ("V3, a counted receipt with obj another room", W + [H, X, qh, OUT], {"p2", "p3", "AG"}, []),
        ("V3b, a counted receipt over another room", W + [H, X, qo, OUT], {"p2", "p3", "AG"}, []),
        ("V4 base", W + [AGB, xb, LAY], S3 | {"AG", "B"}, []),
        ("V4, an agent's counted receipt over `agent`", W + [AGB, xb, qa, LAY], S3 | {"AG", "B"}, []),
        ("O1, x2 and w: x2 in force, w out", B3 + [x2, w], S3 | {"A2", "A3"}, [("A3", "agent", T)]),
        ("O2, x1, x2 and w: the pair contested, w in force", B3 + [x1, x2, w], S3 | {"A1", "A2"}, [("A3", "agent", F)]),
        ("O3, x1 alone", B3 + [x1], S3 | {"A1", "A3"}, [("A2", "agent", F), ("A2", "moderate", F)]),
        ("O4, x1 then x2 naming it at the older head: x1 in force", B3 + [x1, x2o], S3 | {"A1", "A3"},
         [("A2", "agent", F), ("A2", "moderate", F)]),
        ("K0, an agent's receipt keeps nothing", B5, S3 | {"A1", "A3", "AG"}, []),
        ("K1, and A1's removal of A3 in force", B5 + [y], S3 | {"A1", "AG"}, [("A3", "agent", F)]),
        ("K2, and A1 lays down its moderate: A1's removal out of force; x still out", B5 + [y, ST.withdraw("wa1", "A1", "cmA1", ("y",))],
         S3 | {"A1", "A3", "AG"}, [("A3", "agent", T), ("A1", "moderate", F)]),
        ("D0, p2's receipt keeps x", W + [X, q2, LAY], S3, []),
        ("D1, p2's founding moderate withdrawn beside its receipt: void", W + [X, q2, LAY, unduty("xm2", "p2", "moderate", ("p1", "p3"), ("x",))],
         S3 | {"AG"}, [("p2", "moderate", F)]),
        ("D3, q's receipt keeps x", WQ0 + [xq, receipt("qq", "q", "x"), LAY], S3 | {"q"}, []),
        ("D4, q's conferred moderate withdrawn beside its receipt: void",
         WQ0 + [xq, receipt("qq", "q", "x"), LAY, unduty("xmq", "q", "moderate", ("p1", "p2", "p3"), ("x",))],
         S3 | {"AG", "q"}, [("q", "moderate", F)]),
    ]


CASES += [
    (RV + "R5, the count's receipt is the room less the remover: four persons, two of the other three confirm",
     R5 + [counted_receipt("qc", ("p2", "p3"), "x", ("x",)), ST.withdraw("wm", "p1", "g", ("x",), scope="moderate")],
     {"x": T}, {"p1", "p2", "p3", "p4"}, []),
    (RV + "R5, one of the other three does not",
     R5 + [counted_receipt("qc", ("p2",), "x", ("x",)), ST.withdraw("wm", "p1", "g", ("x",), scope="moderate")],
     {"x": T}, {"p1", "p2", "p3", "p4", "AG"}, []),
]
CASES += [(RV + "the reviewer's rows: " + n, rows, {}, roster, asks) for n, rows, roster, asks in _review()]
# The review of #54 (CIRISConstitution#218, pin list: a count's own receipt): the count's receipt is read under one
# rule, the members' check of one member's act (more than half of the persons of the room less the remover, never
# fewer than two), whatever policy or need the row states
RV54 = "CIRISConstitution#218, pin list: a count's own receipt (review of #54): "
UNDL = dict(UND, lifts=True)
CR1 = dict(counted_receipt("qc", ("p2",), "x", ("x",)), policy="accord_halt")
CR2 = dict(counted_receipt("qc", ("p1",), "x", ("x",)), policy="cosigned_act", need=0)
CR2b = dict(counted_receipt("qc", ("AG",), "x", ("x",)), policy="cosigned_act", need=0)
CASES += [
    (RV54 + "R1, one person's counted ack under `accord_halt` (one of n) is no count's receipt: the lifting end puts "
     "the removal out of force", W + [X, CR1, dict(UNDL, names=("x", "qc"))], {"x": T, "qc": T}, P3 | {"AG"}, [("AG", "agent", T)]),
    (RV54 + "R2, the remover's own counted ack with a declared need of none is no count's receipt",
     W + [X, CR2, dict(UNDL, names=("x", "qc"))], {"x": T, "qc": T}, P3 | {"AG"}, [("AG", "agent", T)]),
    (RV54 + "R2b, the agent's own counted ack with a declared need of none is no receipt: the laying down puts the "
     "removal out of force", W + [X, CR2b, dict(LAY, names=("x", "qc"))], {"x": T}, P3 | {"AG"}, [("AG", "agent", T)]),
    (RV54 + "two persons of the other two, under `accord_halt`: the count's receipt keeps the removal through the "
     "lifting end", W + [X, dict(counted_receipt("qc", ("p2", "p3"), "x", ("x",)), policy="accord_halt"),
                         dict(UNDL, names=("x", "qc"))], {"x": T}, P3, [("AG", "agent", F)]),
    (RV54 + "two of the other three under `unanimous`: the row's own policy is not read, the count's receipt keeps",
     R5 + [dict(counted_receipt("qc", ("p2", "p3"), "x", ("x",)), policy="unanimous"),
           ST.withdraw("wm", "p1", "g", ("x",), scope="moderate")], {"x": T}, {"p1", "p2", "p3", "p4"}, []),
    (RV54 + "the remover and one of the other three: the remover no voice, one is not more than half",
     R5 + [counted_receipt("qc", ("p1", "p2"), "x", ("x",)), ST.withdraw("wm", "p1", "g", ("x",), scope="moderate")],
     {"x": T}, {"p1", "p2", "p3", "p4", "AG"}, []),
    (RV54 + "the other two's counted ack at the room's founding head, older than the removal's: no receipt",
     W + [X, counted_receipt("qc", ("p2", "p3"), "x", ("g",)), OUT], {"x": T}, P23 | {"AG"}, []),
    (RV54 + "the other two's counted ack stating another room (one p2 founded alone): no receipt",
     W + [ST.found("h", "p2", ("p2",), {}), X, dict(counted_receipt("qc", ("p2", "p3"), "x", ("x",)), obj="h"), OUT],
     {"x": T}, P23 | {"AG"}, []),
    (RV54 + "the other two's counted ack counted over another room: no receipt",
     W + [ST.found("h", "p2", ("p2",), {}), X, dict(counted_receipt("qc", ("p2", "p3"), "x", ("x",)), over="h"), OUT],
     {"x": T}, P23 | {"AG"}, []),
    (RV54 + "two persons: the other one's counted ack is all of the room less the remover, but never fewer than two "
     "voices: no count's receipt", [ST.found("g", "p1", ("p1", "p2"), {"moderate": ("p1",)}, cosigners=("p2",)),
                                    admit("ag", "AG", ("p1", "p2"), ("g",), "agent"), X,
                                    counted_receipt("qc", ("p2",), "x", ("x",)), LAY], {"x": T}, {"p1", "p2", "AG"}, []),
]
# CC 2.4.1.1 (iii), a conferrer that ends its own offer may lift (CIRISConstitution#218, pin list: a count end that
# lifts receipts; review of #54): a room founded with members only (no duty holder), an election seats p2 to
# moderate, and p2, then the lone person duty holder, confers moderate on p3 by its own offer. That room's record
# seats no duty holder, so the conferrer's withdrawal ends p3's seat
MG3 = ST.offer("g", "p1", ("p1", "p2", "p3"), "member", "@", "self", cosigners=("p2", "p3"))
EL = [MG3, R("b1", "ballot", "p1", ("g",), ranking=("p2", "p3"), of="g"), R("b3", "ballot", "p3", ("g",), ranking=("p2", "p3"), of="g"),
      ST.offer("el", "p2", "p2", "moderate", OBJ, "group", ("b1", "b3"), policy="moderator_election", of="g"),
      admit("ag", "AG", ("p1", "p2", "p3"), ("el",), "agent"),
      ST.offer("oc", "p2", "p3", "moderate", OBJ, "self", ("ag",), cosigners=("p3",)),
      lone("x", "p3", "AG", ("oc",)), receipt("q2", "p2", "x")]
CASES += [
    (PIN + "a conferrer that ends its own offer may lift (CC 2.4.1.1 (iii)): an elected p2 confers moderate on p3 by "
     "its own offer; p3 removes the agent alone, p2 receipts it, and p2 withdraws p3's offer stating `lifts`: the "
     "receipt keeps nothing", EL + [dict(ST.withdraw("wo", "p2", "oc", ("x", "q2")), lifts=True)],
     {"el": T, "oc": T, "x": T, "wo": T}, P3 | {"AG"}, [("p3", "moderate", F), ("p2", "moderate", T)]),
    (PIN + "the same withdrawal not stating `lifts`: p2's receipt keeps the removal in force",
     EL + [ST.withdraw("wo", "p2", "oc", ("x", "q2"))], {"x": T, "wo": T}, P3, [("p3", "moderate", F)]),
    (PIN + "p3's own withdrawal of the offer stating `lifts` is the holder's own end and lifts nothing",
     EL + [dict(ST.withdraw("wo", "p3", "oc", ("x", "q2")), lifts=True)], {"x": T, "wo": T}, P3, [("p3", "moderate", F)]),
]
# The review of #54, item 5 (ruled: a moderator's lone removal exists only over a community; CC 4.5.13 speaks of a
# room's moderator and an agent's key in that room): the reviewer's a6 rows over a key's own object `g` (no row is
# named g, so g is a key, and its own offers seat what it likes). There a "lone removal" is an ordinary counted unseat
# whose count is not met (no member seat over g): neither concludes, and nothing is removed
KO = [R("k0", "note", "g", ()),
      ST.offer("oa", "g", ("AG", "Z"), "agent", OBJ, "self", ("k0",)),
      ST.offer("om", "g", ("p1", "Z"), "moderate", OBJ, "self", ("k0",), sub=True),
      ST.accept("a1", "AG", "oa"), ST.accept("a2", "Z", "oa"), ST.accept("a3", "p1", "om"), ST.accept("a4", "Z", "om"),
      ST.offer("mz", "Z", "M", "moderate", OBJ, "seat", ("a4",), under="om"), ST.accept("a5", "M", "mz"),
      R("hd", "ack", "g", ("a1", "a2", "a3", "a4", "a5"), of="oa")]            # a head on g's own line
KX = ST.unseat("x", "M", "AG", "agent", OBJ, "group", ("hd",), head=("hd",), policy="community_remove", window=OV)
KY = ST.unseat("y", "p1", "Z", "agent", OBJ, "group", ("hd",), head=("hd",), policy="community_remove", window=OV)
CASES += [
    ("review of #54, item 5: over a key's own object a moderator's unseat of an agent's key is no lone removal; its "
     "count is not met, so it does not conclude", KO + [KX], {"x": F}, {"AG", "Z"}, [("AG", "agent", T), ("M", "moderate", T)]),
    ("review of #54, item 5: the reviewer's x and y, and p1's laying down: none removes anything",
     KO + [KX, KY, ST.withdraw("lp", "p1", "a3", ("y",))], {"x": F, "y": F}, {"AG", "Z"},
     [("AG", "agent", T), ("Z", "agent", T), ("M", "moderate", T)]),
]
# The review of #54 (CIRISConstitution#218, pin list: no cascade): an act decided before an earlier act's own verdict
# is known reads that earlier act as an end; x, out of force, ends nothing, so an act after it that it would end is in
# force. A1 and A2 are agent moderators; A1 lays its moderate down after x
NC = "CIRISConstitution#218, pin list: no cascade (review of #54): "
X12 = lone("x", "A1", "A2", ("cm2",))
LAY1 = ST.withdraw("la1", "A1", "cm1", ("x",), scope="moderate")
CASES += [
    (NC + "x, A1's removal of A2, and A1's laying down after it: x out of force, A2 seated",
     B2 + [X12, LAY1], {"x": T}, P3 | {"A1", "A2"}, [("A1", "moderate", F)]),
    (NC + "an ordered pair: A2's removal of A1 has x in its past and not A1's laying down (concurrent with it): it "
     "concludes nothing, since the laying down that puts x out of force is not in the row's past, and at x, the newest "
     "counted change it names, A2 is removed (the heads ruling of 2026-11-26, B)",
     B2 + [X12, LAY1, lone("y", "A2", "A1", ("cm2",), cites=("x",))],
     {"x": T, "y": F}, P3 | {"A1", "A2"}, [("A1", "agent", T), ("A2", "moderate", T)]),
    (NC + "the ordered pair with A1's laying down in y's past: x is out of force there, A2's standing stands, and A2's "
     "removal of A1 is in force", B2 + [X12, LAY1, lone("y", "A2", "A1", ("cm2",), cites=("x", "la1"))],
     {"x": T, "y": T}, P3 | {"A2"}, [("A1", "agent", F), ("A2", "moderate", T)]),
    (NC + "the ordered pair with no laying down: x in force ends A2's standing, so A2's removal of A1 is out of force",
     B2 + [X12, lone("y", "A2", "A1", ("cm2",), cites=("x",))], {"x": T, "y": T}, P3 | {"A1"}, [("A2", "agent", F)]),
    (NC + "no pair: A2's removal of A3 has x in its past and not A1's laying down: it concludes nothing (the laying "
     "down that puts x out of force is not in the row's past; the heads ruling of 2026-11-26, B)",
     W3A + [X12, LAY1, lone("z", "A2", "A3", ("cm2",), cites=("x",))], {"x": T, "z": F}, P3 | {"A1", "A2", "A3"},
     [("A3", "agent", T)]),
    (NC + "no pair, with A1's laying down in z's past: x out of force ended nothing, so A2's removal is in force",
     W3A + [X12, LAY1, lone("z", "A2", "A3", ("cm2",), cites=("x", "la1"))], {"x": T, "z": T}, P3 | {"A1", "A2"},
     [("A3", "agent", F)]),
    (NC + "the same with x in force: A2's standing ended in its past, its removal of A3 out of force",
     W3A + [X12, lone("z", "A2", "A3", ("cm2",), cites=("x",))], {"x": T, "z": T}, P3 | {"A1", "A3"}, [("A2", "agent", F)]),
]
PLANTS = ("end_unread", "remover_receipt", "reseat_revives", "count_unread_lone", "cascade", "count_receipt_unread",
          "removed_receipt_kept", "lifts_unread", "conferrer_lift_unread", "cycle_one_then_other", "count_receipt_unchecked",
          "founding_duty_unread", "agent_receipt_kept", "remover_counted_over", "lone_lifts", "own_end_lifts", "receipt_before_kept",
          "failed_count_is_signers", "receipt_row_policy", "ordered_pair_cascade",
          "lift_no_floor", "reaccept_unread", "own_conferral_no_change")
# lone_any_object (a lone removal read over a key's own object) is retired: over a key's own object no row is a counted
# change and no head is a row (H1, H8), so the heads hold no `moderate` there and the planted break changes no answer


def read(S, case):
    _, _, concl, _, asks = case[:5]
    Q = ST.Seats(S, own=case[5] if len(case) > 5 else None)     # a sixth element: the reader, with its acknowledgements
    return {i: bool(S.C.get(i)) for i in concl}, set(Q.roster(OBJ)), [Q.stands(k, sc, OBJ) for k, sc, _ in asks]


def want(case):
    _, _, concl, roster, asks = case[:5]
    return concl, set(roster), [x for _, _, x in asks]


# every counted row of these cases names the newest counted changes over the room in its own past (H1, H4, the heads
# ruling of 2026-11-26): what a signer that holds its own past writes. Rows written at an older head conclude nothing.
CASES = [(c[0], ST.honest(c[1])) + tuple(c[2:]) for c in CASES]

# Rows that now conclude nothing, the roster unchanged. Each names the newest counted change in its own past (H1, H4),
# and at that head its signer holds no `moderate`: its own laying down is in the removal's own past (the two E4
# cases), or the newest counted change is a lone removal of the signer's own seat in force there (O4, and the ordered
# pairs with no laying down). Before the heads ruling these rows named an older head and concluded, uncounted (E4) or
# out of force; either way they change no seat.
NOW_NOTHING = {
    "the removal names the remover's laying down, at the head before it": "x",
    "the same with another holder's receipt of it: still not counted (E4)": "x",
    "CIRISConstitution#218, review of #48: O4, an ordered pair": "x2",
    "CIRISConstitution#218, pin list: no cascade (review of #54): the ordered pair with no laying down": "y",
    "CIRISConstitution#218, pin list: no cascade (review of #54): the same with x in force": "z",
}


def _now_nothing(c):
    hit = [i for n, i in NOW_NOTHING.items() if c[0].startswith(n)]
    return c if not hit else (c[0], c[1], {**c[2], **{i: F for i in hit}}) + tuple(c[3:])


assert all(sum(c[0].startswith(n) for c in CASES) == 1 for n in NOW_NOTHING)
CASES = [_now_nothing(c) for c in CASES]


def answers(case):
    return read(CK.concluded(CK.kept(list(case[1])), RULE), case)


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


def main():
    problems, n_orders = [], 0
    for case in CASES:
        got = answers(case)
        if got != want(case):
            problems.append("%s: got %s, expected %s" % (case[0], got, want(case)))
        for p in orders(case[1]):
            n_orders += 1
            if read(CK.arrive([case[1][0]] + p, RULE), case) != got:
                problems.append("%s: order %s differs" % (case[0], [r["id"] for r in p]))
                break
    caught = 0
    for plant in PLANTS:
        ST.MUT.add(plant)
        try:
            hit = [c[0] for c in CASES if answers(c) != want(c)]
        finally:
            ST.MUT.discard(plant)
        caught += bool(hit)
        print("  plant %-16s %s" % (plant, "caught by %d cases, first: %s" % (len(hit), hit[0]) if hit else "NOT CAUGHT"))
        if not hit:
            problems.append("plant %s not caught" % plant)
    for p in problems:
        print(p)
    print("RESULT: %s: %d cases, %d arrival orders, %d of %d planted breaks caught"
          % ("ok" if not problems else "%d problems" % len(problems), len(CASES), n_orders, caught, len(PLANTS)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
