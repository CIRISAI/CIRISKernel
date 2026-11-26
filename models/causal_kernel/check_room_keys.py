#!/usr/bin/env python3
"""
check_room_keys.py: the membership plane of a private room (CC 3.1.3.2), as seat.py reads it. The ledger is
CIRISConstitution#224.

A private room is a community whose founding row declares `membership` `private`; its roster seats room keys (a
voice, named by its first room key; an agent's voice is one room key). A founding row with no `membership` reads
public, and seats identity keys.

    finality    the steward's decision of 2026-11-25: "a removed room key is not seated again. A person removed from
                a private room returns only under a new room key, by a new admission." With the readings settled the
                same day: the rule is of ANY end of the seat, a resignation included; it reaches private rooms only;
                what is refused is a new seating of "a room key whose seat's end stands and is in force". A counted
                removal, of a person's or an agent's room key, is final at once. A moderator's lone removal of an
                agent's key is never final by time: the members' re-seating row (the lift) restores the same key and
                is no new seating; out of force (its remover's standing ended, no receipt), the key is seated with
                no row, and that is the end ceasing, not a seating.
                seat.py: FINAL names `member` and `agent`; _revoked_before refuses an offer that seats such a key, and
                an acceptance of an offer that seats it, with the end in its past. The end is a counted unseat of
                that seat (its count met over its own past, or no count at all) with an offer seating the key in
                its past, or the key's own end of its stay (stay_ends). A row concurrent with the end concludes (the rule is by
                past). Beside a counted removal it does not seat: the cut voids it, and a later row adding the key is
                refused. Beside a resignation the key's own signature or acceptance on it is no voice (ruled: a key's own
                rows concurrent with its own end of the seat are no voice, in every room), so it seats nobody.
    a second seat row   OPEN (#224: "what a second seat row of one room key does"). The text does not say.
    two admissions      the kernel seats both (CC 3.1.3.2: "no door refuses a widening for either, since no rule of
                standing reads a binding"). What the text owes about it is OPEN (#224).

Part 1. Cases, each a hand-written answer: which rows conclude, the roster (members and agents), and standings asked
by name; every case is read in arrival orders. Each names the ledger row it closes.
Part 2. OPEN: rows the text does not decide. Each records the kernel's answer as built and the candidate answers; the
check asserts the answer as built only so that a change to it is seen, and decides nothing.
Part 3. Planted breaks (seat.MUT), each of which must change a case's answer:
    room_key_unread    room-key finality is not read: a removed room key is seated again
    public_final       finality reaches a public room: a counted re-admission there is refused
    lone_final         a moderator's lone removal is read as final: the members' lift is refused
    resign_not_final   a resignation is no end of the seat: a room key that left is seated again
    reaccept_reseats   the same offer accepted again after a resignation re-seats
    own_end_unread     a key's own end voids none of its concurrent voices: a re-admission racing a resignation seats
    own_end_any_seat   a key's own end of one seat voids its concurrent voices on its other roster seats too

Not here: a room that moved from private to public (no seat row carries the move; a voice seated before it stays a
voice, and whether its end is then final is not stated); the key roster of a voice (#224's derived item "a device key
of a voice ended by the voice's own count is final for that device key": a voice is a key object with no founding
row, so nothing in the seat rows says it is a private room's); the name of the refusal (the text's to give).

    python3 -I check_room_keys.py      exit 1 on any difference
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
L = "CIRISConstitution#224: "
FINAL_ROW = L + "whether a removed room key can be seated again"
SECOND_ROW = L + "what a second seat row of one room key does"
TWO_ROW = L + "two admissions of one person at once both seat"


def admit(i, who, signers, heads, scope="member", joiner=True):
    """An admission by the room's count; the joiner cosigns it (its own yes) unless `joiner` is false."""
    return ST.offer(i, signers[0], who, scope, OBJ, "group", tuple(heads), head=tuple(heads), policy="community_invite",
                    cosigners=tuple(signers[1:]) + ((who,) if joiner else ()))


def remove(i, who, signers, heads, scope="member"):
    """The room's counted removal."""
    return ST.unseat(i, signers[0], who, scope, OBJ, "group", tuple(heads), head=tuple(heads), policy="community_remove",
                     cosigners=tuple(signers[1:]))


def lone(i, by, who, heads):
    """A moderator's lone removal of an agent's key, naming the overturn's window."""
    return ST.unseat(i, by, who, "agent", OBJ, "group", tuple(heads), head=tuple(heads), policy="community_remove", window=OV)


def lift(i, by, who, removal, heads, objections):
    """The members' re-seating of the key a lone removal removed: it cites the removal and names the objections."""
    return ST.offer(i, by, who, "agent", OBJ, "group", (removal,) + tuple(objections), head=tuple(heads), policy=OV,
                    cosigners=(who,), content=removal)


def world(private):
    """Four founding duty holders (each a member and a moderator), a person q and an agent's key AG admitted by the
    room's count. `private`: the founding row declares `membership` `private`."""
    kw = {"membership": "private"} if private else {}
    g = ST.found("g", "m1", ("m1", "m2", "m3", "m4"), {"moderate": ("m1", "m2", "m3", "m4")}, cosigners=("m2", "m3", "m4"), **kw)
    return [g, admit("aq", "q", ("m1", "m2", "m3"), ("g",)), admit("ag", "AG", ("m1", "m2", "m3", "m4"), ("aq",), "agent")]


PV, PB = world(True), world(False)
M4 = {"m1", "m2", "m3", "m4"}
XQ = remove("xq", "q", ("m1", "m2", "m3", "m4"), ("ag",))                    # the room's count removes q
XA = remove("xa", "AG", ("m1", "m2", "m3", "m4"), ("ag",), "agent")                 # the room's count removes the agent's key
XL = lone("x", "m1", "AG", ("ag",))                                           # a moderator removes it alone
OBJS = [WN.answer("o%d" % n, "m%d" % n, "x", "object") for n in (2, 3, 4)]
WQ = ST.withdraw("wq", "q", "aq", ("ag",))                                    # q resigns: it withdraws the offer that seats it


def rejoin(i, who, heads, scope="member"):
    return admit(i, who, ("m1", "m2", "m3", "m4"), heads, scope)


# (name, ledger row, rows, {row: concludes}, roster, [(key, scope, stands)])
CASES = [
    # ---- a counted removal ----------------------------------------------------------------------------------------
    ("private: the room's count removes q, and an admission of the same room key with the removal in its past concludes "
     "nothing", FINAL_ROW, PV + [XQ, rejoin("aq2", "q", ("xq",))], {"xq": T, "aq2": F}, M4 | {"AG"}, [("q", "member", F)]),
    ("private: q returns under a new room key by a new admission: seated", FINAL_ROW,
     PV + [XQ, rejoin("aq2", "q2", ("xq",))], {"aq2": T}, M4 | {"AG", "q2"}, [("q2", "member", T)]),
    ("public: the same re-admission of the same key stands as it runs", FINAL_ROW,
     PB + [XQ, rejoin("aq2", "q", ("xq",))], {"xq": T, "aq2": T}, M4 | {"AG", "q"}, [("q", "member", T)]),
    ("private: an admission of the same key concurrent with the removal is void by the cut, not refused", FINAL_ROW,
     PV + [XQ, rejoin("aq2", "q", ("ag",))], {"xq": T, "aq2": T}, M4 | {"AG"}, [("q", "member", F)]),
    ("private: then a row names both (the removal and the concurrent re-admission): the key stays out", FINAL_ROW,
     PV + [XQ, rejoin("aq2", "q", ("ag",)), ST.cosign("h", "m1", "h", ("xq", "aq2"))], {"xq": T, "aq2": T, "h": T},
     M4 | {"AG"}, [("q", "member", F)]),
    ("private: and a later admission of the key naming that row concludes nothing", FINAL_ROW,
     PV + [XQ, rejoin("aq2", "q", ("ag",)), ST.cosign("h", "m1", "h", ("xq", "aq2")), rejoin("aq3", "q", ("h",))],
     {"aq2": T, "aq3": F}, M4 | {"AG"}, [("q", "member", F)]),
    ("private: the room's count removes the agent's key; its admission again concludes nothing", FINAL_ROW,
     PV + [XA, rejoin("ag2", "AG", ("xa",), "agent")], {"xa": T, "ag2": F}, M4 | {"q"}, [("AG", "agent", F)]),
    ("public: the same admission of the agent's key again stands", FINAL_ROW,
     PB + [XA, rejoin("ag2", "AG", ("xa",), "agent")], {"ag2": T}, M4 | {"q", "AG"}, []),
    ("private: a counted unseat of a seat the key never held ends nothing, and is no end the admission reads", FINAL_ROW,
     PV + [remove("xz", "z", ("m1", "m2", "m3", "m4"), ("ag",)), rejoin("az", "z", ("xz",))], {"az": T}, M4 | {"q", "AG", "z"},
     []),
    # ---- a resignation ------------------------------------------------------------------------------------------------
    ("private: q resigns (it withdraws the offer that seats it); an admission of the same key after it concludes nothing",
     FINAL_ROW, PV + [WQ, rejoin("aq2", "q", ("wq",))], {"wq": T, "aq2": F}, M4 | {"AG"}, [("q", "member", F)]),
    ("public: the same admission after a resignation stands", FINAL_ROW,
     PB + [WQ, rejoin("aq2", "q", ("wq",))], {"aq2": T}, M4 | {"AG", "q"}, []),
    ("private: q accepts its admission by its own row and withdraws that acceptance; accepting the same offer again "
     "concludes nothing", FINAL_ROW,
     [PV[0], admit("aq", "q", ("m1", "m2", "m3"), ("g",), joiner=False), ST.accept("acq", "q", "aq"),
      ST.withdraw("wa", "q", "acq"), ST.accept("acq2", "q", "aq", ("wa",))], {"acq": T, "wa": T, "acq2": F}, M4, [("q", "member", F)]),
    ("public: the same offer accepted again seats", FINAL_ROW,
     [PB[0], admit("aq", "q", ("m1", "m2", "m3"), ("g",), joiner=False), ST.accept("acq", "q", "aq"),
      ST.withdraw("wa", "q", "acq"), ST.accept("acq2", "q", "aq", ("wa",))], {"acq2": T}, M4 | {"q"}, [("q", "member", T)]),
    ("private: a founder ends its stay (withdraws the founding row naming no seat); its admission again concludes nothing",
     FINAL_ROW, PV + [ST.withdraw("w4", "m4", "g", ("ag",)), admit("a4", "m4", ("m1", "m2", "m3"), ("w4",))],
     {"w4": T, "a4": F}, {"m1", "m2", "m3", "q", "AG"}, [("m4", "member", F), ("m4", "moderate", F)]),
    ("private: the agent's key resigns; its admission again concludes nothing", FINAL_ROW,
     PV + [ST.withdraw("wg", "AG", "ag", ("ag",)), rejoin("ag2", "AG", ("wg",), "agent")], {"ag2": F}, M4 | {"q"}, []),
    ("private: a founder lays down `moderate` and the holders confer it again: a duty seat is no room key's seat in the "
     "room, and the conferral stands", FINAL_ROW,
     PV + [ST.withdraw("wm", "m4", "g", ("ag",), scope="moderate"),
           ST.offer("cm", "m1", "m4", "moderate", OBJ, "group", ("wm",), head=("wm",), policy="duty_confer", counted="duty",
                    cosigners=("m2", "m4"))], {"cm": T}, M4 | {"q", "AG"}, [("m4", "moderate", T)]),
    # ---- a moderator's lone removal of an agent's key -----------------------------------------------------------------
    ("private: a moderator removes the agent's key alone and the members lift it: the re-seating restores the same key "
     "and is no new seating", FINAL_ROW, PV + [XL] + OBJS + [lift("rs", "m2", "AG", "x", ("ag",), ("o2", "o3", "o4"))],
     {"x": T, "rs": T}, M4 | {"q", "AG"}, [("AG", "agent", T)]),
    ("private: the lone removal goes out of force (its remover lays down `moderate`, no receipt): the key is seated with no "
     "row", FINAL_ROW, PV + [XL, ST.withdraw("wm", "m1", "g", ("x",), scope="moderate")], {"x": T}, M4 | {"q", "AG"}, []),
    ("private: a moderator's lone removal in force and not lifted, then the room's count admits the same agent's key "
     "again: it seats (a lone removal is no counted end and bars nothing; ruled on #224)", FINAL_ROW,
     PV + [XL, rejoin("ag2", "AG", ("x",), "agent")], {"x": T, "ag2": T}, M4 | {"q", "AG"}, [("AG", "agent", T)]),
    ("private: a lift of a counted removal is no lift and seats nothing", FINAL_ROW,
     PV + [XA] + [WN.answer("o%d" % n, "m%d" % n, "xa", "object") for n in (2, 3, 4)]
     + [lift("rs", "m2", "AG", "xa", ("ag",), ("o2", "o3", "o4"))], {"xa": T, "rs": F}, M4 | {"q"}, []),
]

# a key's own end voids its own concurrent voices (ruled on #224, the rule a removed key's concurrent rows have, read
# for the key's own end; stated for every room): its signature on an offer, or its acceptance, that is concurrent with
# its own end of its stay is no voice. Rows of other keys are untouched.
OWN_ROW = FINAL_ROW + "; a key's own end voids its own concurrent voices"
CASES += [
    ("private: q resigns beside a re-admission of the same key (neither names the other): both conclude, and q's "
     "signature on the re-admission is concurrent with its own end, so the re-admission lacks its consent and seats nobody",
     OWN_ROW, PV + [WQ, rejoin("aq2", "q", ("ag",))], {"wq": T, "aq2": T}, M4 | {"AG"}, [("q", "member", F)]),
    ("private: then a row names both: q stays out", OWN_ROW,
     PV + [WQ, rejoin("aq2", "q", ("ag",)), ST.cosign("h", "m1", "h", ("wq", "aq2"))], {"h": T}, M4 | {"AG"},
     [("q", "member", F)]),
    ("private: and a later admission naming that row concludes nothing", OWN_ROW,
     PV + [WQ, rejoin("aq2", "q", ("ag",)), ST.cosign("h", "m1", "h", ("wq", "aq2")), rejoin("aq3", "q", ("h",))],
     {"aq3": F}, M4 | {"AG"}, [("q", "member", F)]),
    ("private: q withdraws its acceptance beside a second acceptance of the same offer: the second concludes and seats "
     "nobody (omitting its own withdrawal does not dodge the end)", OWN_ROW,
     [PV[0], admit("aq", "q", ("m1", "m2", "m3", "m4"), ("g",), joiner=False), ST.accept("acq", "q", "aq"),
      ST.withdraw("wa", "q", "acq"), ST.accept("acq2", "q", "aq", ("acq",))], {"wa": T, "acq2": T}, M4, [("q", "member", F)]),
    ("public: the same race: the rule is every room's, and q is out", OWN_ROW,
     PB + [WQ, rejoin("aq2", "q", ("ag",))], {"wq": T, "aq2": T}, M4 | {"AG"}, [("q", "member", F)]),
    ("public: and after a row naming both, a later admission of q seats it (no finality in a public room)", OWN_ROW,
     PB + [WQ, rejoin("aq2", "q", ("ag",)), ST.cosign("h", "m1", "h", ("wq", "aq2")), rejoin("aq3", "q", ("h",))],
     {"aq3": T}, M4 | {"AG", "q"}, [("q", "member", T)]),
    ("private: another key's admission concurrent with q's resignation is untouched: it seats", OWN_ROW,
     PV + [WQ, rejoin("az", "z", ("ag",))], {"az": T}, M4 | {"AG", "z"}, [("z", "member", T)]),
    ("private: the end is of one seat: q's resignation of its member seat leaves its own concurrent consent to a seat "
     "in another roster scope (an agent's seat) a voice, and that seat stands", OWN_ROW,
     PV + [WQ, rejoin("ax", "q", ("ag",), "agent")], {"ax": T}, M4 | {"AG", "q"}, [("q", "agent", T), ("q", "member", F)]),
    ("private: q's acceptance of a duty conferral concurrent with its resignation: the duty is no roster seat, and it "
     "waits on a member seat q no longer holds", OWN_ROW,
     PV + [WQ, ST.offer("cq", "m1", "q", "moderate", OBJ, "group", ("ag",), head=("ag",), policy="duty_confer",
                        counted="duty", cosigners=("m2", "m3", "q"))], {"cq": T}, M4 | {"AG"}, [("q", "moderate", F)]),
]

# ---- OPEN: what the text does not decide. (name, ledger row, rows, {row: concludes}, roster, asks, candidates) ----
OPEN = []
# a second seat row of one room key
OPEN += [
    ("a second seat row of a room key already seated: as built it concludes, and the key is one key on the roster",
     SECOND_ROW, PV + [admit("aq2", "q", ("m1", "m2", "m3", "m4"), ("ag",))], {"aq2": T}, M4 | {"q", "AG"}, [("q", "member", T)],
     ("the second row concludes nothing: a room key has one seat row, its own record (a refusal the text would name)",
      "it stands, and a binding is taken that opens either commitment (formal/binding_carriage finding 3: the fork the "
      "commitment was added to stop returns)",
      "it stands, and the key takes no binding: nothing forks, no node counts persons, and the key's holder stalls every "
      "count alone (the same finding)")),
    ("a second seat row, then the key withdraws its first: as built the second still seats it, so the resignation ends "
     "nothing for the roster", SECOND_ROW,
     PV + [admit("aq2", "q", ("m1", "m2", "m3", "m4"), ("ag",)), ST.withdraw("wq", "q", "aq", ("aq2",))], {"aq2": T, "wq": T},
     M4 | {"q", "AG"}, [("q", "member", T)],
     ("the second row is refused, so the case does not arise",
      "a withdrawal of one seat row by its key ends the key's stay, and every seat row of it",
      "each seat row is a stay of its own, as built")),
]
# two admissions of one person at once: the kernel's answer is decided (CC 3.1.3.2: "Both checks are the cosigner's
# own, and no door refuses a widening for either, since no rule of standing reads a binding"); what the text says of
# the second voice is not
TWO = PV + [rejoin("ak1", "k1", ("ag",)), rejoin("ak2", "k2", ("ag",))]
# a later head with both admissions in its past (a count over two concurrent heads reads the keys common to both)
HEAD = ST.cosign("h", "m1", "h", ("ak1", "ak2"))
XQ2 = lambda signers: remove("xq", "q", signers, ("h",))
CASES += [
    ("two admissions of one person at once, under two room keys: both seat. No rule of standing reads a binding, so "
     "the kernel cannot tell them from two persons", TWO_ROW, TWO, {"ak1": T, "ak2": T}, M4 | {"q", "AG", "k1", "k2"},
     [("k1", "member", T), ("k2", "member", T)]),
    ("each is a voice in the room's count: a removal signed by three members and both keys is met (5 of 7)", TWO_ROW,
     TWO + [HEAD, XQ2(("m1", "m2", "m3", "k1", "k2"))], {"xq": T}, M4 | {"AG", "k1", "k2"}, []),
    ("and without the second key's signature it is not (4 of 7)", TWO_ROW,
     TWO + [HEAD, XQ2(("m1", "m2", "m3", "k1"))], {"xq": F}, M4 | {"q", "AG", "k1", "k2"}, []),
]
OPEN += [
    ("two admissions of one person at once both seat (the case above): what the text says of the second voice", TWO_ROW,
     TWO, {"ak1": T, "ak2": T}, M4 | {"q", "AG", "k1", "k2"}, [],
     ("the sentence 'a person gains a second voice only where every signer of that admission failed to check' is restated: "
      "it does not hold for two admissions at once (formal/binding_carriage finding 2)",
      "a checking signer refuses a person it holds another binding of, seated or not (a cosigner's duty, read by no door; "
      "a checking duty holder then closes it, and without one two admissions whose checkers share no binding still seat)",
      "a residual named in the ledger")),
]
PLANTS = ("room_key_unread", "public_final", "lone_final", "resign_not_final", "reaccept_reseats", "own_end_unread",
          "own_end_any_seat")


def read(S, case):
    concl, asks = case[3], case[5]
    Q = ST.Seats(S)
    return {i: bool(S.C.get(i)) for i in concl}, set(Q.roster(OBJ)), [Q.stands(k, sc, OBJ) for k, sc, _ in asks]


def want(case):
    return case[3], set(case[4]), [x for _, _, x in case[5]]


def answers(case):
    return read(CK.concluded(CK.kept(list(case[2])), RULE), case)


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
    for kind, cases in (("case", CASES), ("OPEN", OPEN)):
        for case in cases:
            assert case[1].startswith(L), case[0]
            got = answers(case)
            if got != want(case):
                problems.append("%s %s: got %s, expected %s" % (kind, case[0], got, want(case)))
            for p in orders(case[2]):
                n_orders += 1
                if read(CK.arrive([case[2][0]] + p, RULE), case) != got:
                    problems.append("%s: order %s differs" % (case[0], [r["id"] for r in p]))
                    break
    for name, row, _, _, _, _, cands in OPEN:
        print("  OPEN  %s\n        %s" % (row, name))
        for c in cands:
            print("        candidate: %s" % c)
    caught = 0
    for plant in PLANTS:
        ST.MUT.add(plant)
        try:
            hit = [c[0] for c in CASES if answers(c) != want(c)]
        finally:
            ST.MUT.discard(plant)
        caught += bool(hit)
        print("  plant %-17s %s" % (plant, "caught by %d cases, first: %s" % (len(hit), hit[0]) if hit else "NOT CAUGHT"))
        if not hit:
            problems.append("plant %s not caught" % plant)
    for p in problems:
        print(p)
    print("RESULT: %s: %d cases, %d OPEN, %d arrival orders, %d of %d planted breaks caught"
          % ("ok" if not problems else "%d problems" % len(problems), len(CASES), len(OPEN), n_orders, caught, len(PLANTS)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
