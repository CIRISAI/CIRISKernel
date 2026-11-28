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
    a second seat row   derived from CC 3.1.3.2 on #224: a second basis for the same seat (one key, one voice, no
                refusal). An end is the key's end of its stay in that scope, not of a row: one resignation or one
                counted removal ends every seating of the key in that scope in the end's past.
    two admissions      the kernel seats both (CC 3.1.3.2: "no door refuses a widening for either, since no rule of
                standing reads a binding"). A residual: the kernel counts voices as presented, and which keys are
                one person's is the binding, the caller's to collapse.

    the review  (derived from CC 3.1.3.2, CC 3.2 and CC 4.5.13 on #224) an ended stay bars every roster seat of the key
                in a private room (F1); a scope holding `member` is a roster seat (F2); seats are compared by what they
                hold (F3); a key's own end voids its own consents that do not have it in their past (F4); a decline
                is no end of a stay (F5), the consent read from the withdrawal's own concluded past (N1, N2); a roster seat over a community needs the key's own consent (RK1) and is
                placed only by a counted row, the founding record or the key's own end (RK2); a counted row concludes
                whole or not at all (R-a).

Part 1. Cases, each a hand-written answer: which rows conclude, the roster (members and agents), and standings asked
by name; every case is read in arrival orders. Each names the ledger row it closes.
Part 2. OPEN: rows the text does not decide, with the answer as built and the candidates. None is left: each was
ruled or derived from CC 3.1.3.2 on #224 and is a case of Part 1.
Part 3. Planted breaks (seat.MUT), each of which must change a case's answer:
    room_key_unread    room-key finality is not read: a removed room key is seated again
    public_final       finality reaches a public room: a counted re-admission there is refused
    lone_final         a moderator's lone removal is read as final: the members' lift is refused
    resign_not_final   a resignation is no end of the seat: a room key that left is seated again
    reaccept_reseats   the same offer accepted again after a resignation re-seats
    own_end_unread     a key's own end voids none of its concurrent voices: a re-admission racing a resignation seats
    own_end_any_seat   a key's own end of one seat voids its concurrent voices on its other roster seats too
    stay_one_row       a resignation ends the row it names only: a second seat row keeps the key seated
    class_by_name      seats compared by name: a founding `duty` seat and a member seat are two presences (F3)
    decline_ends_stay  a withdrawal of an offer the key never consented to is an end of its stay (F5)
    earlier_consent_kept  a consent before the key's own end survives it (F4)
    end_scope_bound    an end bars the same scope only: a removed member is admitted as an agent (F1)
    ended_unread       an unseat of a seat the key never held is read as an end
    (roster_by_name, retired: since the act-to-policy binding, a counted row of a scope that holds `member` but is
    no roster seat, `founder` included, is no act over a community and concludes nothing, so F2's routing has no
    row left to show; the routing stays, and the F2 case states the binding's answer)
    own_roster_row     one key's own row places a roster seat over a community (RK2)
    (retired at the merge: consent_one_any, an offer waiving the key's consent: no flag waives an acceptance in the
    seat walk (seat.py, A6), so RK1 holds without the branch it broke; RK1 stays a case)
    own_void_any_key   one key's end voids another key's concurrent voices
    resigned_any_key   one key's resignation ends another key's seats in its past
    second_row_refused a second seat row of a seated key is refused (K1)
    batch_by_key       one barred key does not bar a batch admission (R-a)
    consent_any_row    the consent a withdrawal ends is read from any row, not its own concluded past (N1, N2)

Not here: a room that moved from private to public (no seat row carries the move; a voice seated before it stays a
voice, and whether its end is then final is not stated); the key roster of a voice (#224's derived item "a device key
of a voice ended by the voice's own count is final for that device key": a voice is a key object with no founding
row, so nothing in the seat rows says it is a private room's). A room is private or public by its founding row, and no
record change moves it (a rule), so no later version is read. The text's refusal is `membership_room_key_ended`; the
kernel concludes nothing and names no refusal.

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
                    cosigners=(who,), cites=(removal,))


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


def merge(names, cite=()):
    """A later head with the named rows in its past: a counted row naming them as its heads, the four founders
    re-stating m1's seat (H8, the heads ruling of 2026-11-26: a row of no object is no head of a count, so a merge is a
    counted change; it was a note naming them, as persist's version row). `names` are its heads, the newest counted
    changes; `cite`, rows it names besides (a withdrawal, which is no head)."""
    h = admit("h", "m1", ("m1", "m2", "m3", "m4"), tuple(names))
    return dict(h, names=tuple(h["names"]) + tuple(cite)) if cite else h


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
     PV + [XQ, rejoin("aq2", "q", ("ag",)), merge(("xq", "aq2"))], {"xq": T, "aq2": T, "h": T},
     M4 | {"AG"}, [("q", "member", F)]),
    ("private: and a later admission of the key naming that row concludes nothing", FINAL_ROW,
     PV + [XQ, rejoin("aq2", "q", ("ag",)), merge(("xq", "aq2")), rejoin("aq3", "q", ("h",))],
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
    ("public: the same offer accepted again concludes and seats nothing: q's withdrawal of its acceptance ends its stay "
     "in that scope, and the offer is in that end's past (derived from CC 3.1.3.2 on #224: an end is of the stay, not of "
     "a row)", FINAL_ROW,
     [PB[0], admit("aq", "q", ("m1", "m2", "m3"), ("g",), joiner=False), ST.accept("acq", "q", "aq"),
      ST.withdraw("wa", "q", "acq"), ST.accept("acq2", "q", "aq", ("wa",))], {"acq2": T}, M4, [("q", "member", F)]),
    ("public: a new admission after it seats q again", FINAL_ROW,
     [PB[0], admit("aq", "q", ("m1", "m2", "m3"), ("g",), joiner=False), ST.accept("acq", "q", "aq"),
      ST.withdraw("wa", "q", "acq"), admit("aq2", "q", ("m1", "m2", "m3", "m4"), ("wa",))], {"aq2": T}, M4 | {"q"},
     [("q", "member", T)]),
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
     PV + [WQ, rejoin("aq2", "q", ("ag",)), merge(("aq2",), ("wq",))], {"h": T}, M4 | {"AG"},
     [("q", "member", F)]),
    ("private: and a later admission naming that row concludes nothing", OWN_ROW,
     PV + [WQ, rejoin("aq2", "q", ("ag",)), merge(("aq2",), ("wq",)), rejoin("aq3", "q", ("h",))],
     {"aq3": F}, M4 | {"AG"}, [("q", "member", F)]),
    ("private: q withdraws its acceptance beside a second acceptance of the same offer: the second concludes and seats "
     "nobody (omitting its own withdrawal does not dodge the end)", OWN_ROW,
     [PV[0], admit("aq", "q", ("m1", "m2", "m3", "m4"), ("g",), joiner=False), ST.accept("acq", "q", "aq"),
      ST.withdraw("wa", "q", "acq"), ST.accept("acq2", "q", "aq", ("acq",))], {"wa": T, "acq2": T}, M4, [("q", "member", F)]),
    ("public: the same race: the rule is every room's, and q is out", OWN_ROW,
     PB + [WQ, rejoin("aq2", "q", ("ag",))], {"wq": T, "aq2": T}, M4 | {"AG"}, [("q", "member", F)]),
    ("public: and after a row naming both, a later admission of q seats it (no finality in a public room)", OWN_ROW,
     PB + [WQ, rejoin("aq2", "q", ("ag",)), merge(("aq2",), ("wq",)), rejoin("aq3", "q", ("h",))],
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

# ---- the review of room-keys (derived from CC 3.1.3.2 and CC 4.5.13 on CIRISConstitution#224) ----------------------
REV = L + "review of room-keys: "
GD = ST.found("g", "m1", ("m1", "m2", "m3", "m4"), cosigners=("m2", "m3", "m4"), scope="duty", membership="private")
A3 = admit("a3", "m3", ("m1", "m2", "m4"), ("g",))                      # a founder of scope duty admitted as member too
SA = ST.accept("sa", "q", None, ("ag",), scope="member", obj=OBJ)        # q's standing acceptance, before its resignation
WQS = ST.withdraw("wq", "q", "aq", ("sa",))
RAS = ST.offer("ra", "m1", "q", "member", OBJ, "group", ("sa",), head=("sa",), policy="community_invite",
               cosigners=("m2", "m3", "m4"))                              # names sa, concurrent with wq; q does not cosign
G1 = ST.found("g", "f", ("f",), membership="private")                    # a room of one
CASES += [
    ("F1: the room's count removes q's member seat; an admission of q as an agent concludes nothing (a room key is one "
     "presence in one room)", REV + "F1", PV + [XQ, rejoin("ra", "q", ("xq",), "agent")], {"ra": F}, M4 | {"AG"},
     [("q", "agent", F)]),
    ("F1: the room's count removes the agent's key; an admission of it as a member concludes nothing", REV + "F1",
     PV + [XA, rejoin("am", "AG", ("xa",))], {"am": F}, M4 | {"q"}, [("AG", "member", F)]),
    ("F1: the agent's key resigns its agent seat; an admission of it as a member concludes nothing", REV + "F1",
     PV + [ST.withdraw("wg", "AG", "ag", ("ag",)), rejoin("am", "AG", ("wg",))], {"am": F}, M4 | {"q"}, [("AG", "member", F)]),
    ("F2: after the room's count removes q, a counted admission of q as `founder` concludes nothing (finality reads a "
     "scope that holds `member` as a roster seat; the binding gives a founder over a community no act as well)", REV + "F2",
     PV + [XQ, ST.offer("of", "m1", "q", "founder", OBJ, "group", ("xq",), head=("xq",), policy="community_invite",
                        cosigners=("m2", "m3", "m4", "q"))], {"of": F}, M4 | {"AG"}, [("q", "founder", F)]),
    ("F3: a founder of scope `duty` admitted as a member too: both are one presence (the founding duty seat holds "
     "`member`); its withdrawal of the founding row ends both", REV + "F3", [GD, A3, ST.withdraw("w3", "m3", "g", ("a3",))],
     {"w3": T}, {"m1", "m2", "m4"}, [("m3", "member", F), ("m3", "duty", F)]),
    ("F3: and its withdrawal of its member row ends both too; a later admission of it concludes nothing", REV + "F3",
     [GD, A3, ST.withdraw("w3", "m3", "a3", ("a3",)), admit("a4", "m3", ("m1", "m2", "m4"), ("w3",))], {"a4": F},
     {"m1", "m2", "m4"}, [("m3", "member", F), ("m3", "duty", F)]),
    ("F4: q's standing acceptance before its resignation is a consent its own end ends: a re-admission concurrent with "
     "the resignation that names it seats nobody (private)", REV + "F4", PV + [SA, WQS, RAS], {"sa": T, "wq": T, "ra": T},
     M4 | {"AG"}, [("q", "member", F)]),
    ("F4: the same in a public room: nobody", REV + "F4", PB + [SA, WQS, RAS], {"ra": T}, M4 | {"AG"}, [("q", "member", F)]),
    ("RK1: an admission waiving q's consent (`consent` `one`) concurrent with its resignation seats nobody: a roster "
     "seat over a community needs the key's own consent under every protocol (since the binding no flag waives an "
     "acceptance: the offer concludes as an offer and waits on q's acceptance, which q's own end voids)", REV + "RK1",
     PV + [WQ, ST.offer("c1", "m1", "q", "member", OBJ, "group", ("ag",), head=("ag",), policy="community_invite",
                        cosigners=("m2", "m3", "m4"), consent="one")], {"wq": T, "c1": T}, M4 | {"AG"}, [("q", "member", F)]),
    ("F5: z declines (withdraws an offer it never accepted): no end of a stay; a later admission seats it", REV + "F5",
     PV + [admit("oz", "z", ("m1", "m2", "m3", "m4"), ("ag",), joiner=False), ST.withdraw("wz", "z", "oz", ("oz",)),
           admit("oz2", "z", ("m1", "m2", "m3", "m4"), ("wz",))], {"wz": T, "oz2": T}, M4 | {"AG", "q", "z"},
     [("z", "member", T)]),
    ("F5: a listed founding member who did not sign withdraws the founding row: no end of a stay; a counted admission "
     "seats it", REV + "F5",
     [ST.found("g", "m1", ("m1", "m2", "m3", "m4", "u"), cosigners=("m2", "m3", "m4"), membership="private"),
      ST.withdraw("wu", "u", "g", ("g",)), admit("au", "u", ("m1", "m2", "m3", "m4"), ("wu",))], {"wu": T, "au": T},
     M4 | {"u"}, [("u", "member", T)]),
    ("RK2: a member's own row (`self`) admitting a fresh key concludes nothing: a roster seat over a community is placed "
     "by a counted row, the founding record or the key's own end", REV + "RK2",
     PV + [ST.offer("om", "m1", "z", "member", OBJ, "self", ("ag",), cosigners=("z",))], {"om": F}, M4 | {"AG", "q"},
     [("z", "member", F)]),
    ("RK2: a lone founder's own admission and own removal conclude nothing", REV + "RK2",
     [G1, ST.offer("a7", "f", "q", "member", OBJ, "self", ("g",), cosigners=("q",)),
      ST.unseat("x7", "f", "q", "member", OBJ, "self", ("a7",))], {"a7": F, "x7": F}, {"f"}, [("q", "member", F)]),
    ("RK2: a room of one grows by its member's counted proposal and the newcomer's acceptance (its cosignature)",
     REV + "RK2", [G1, ST.offer("a7", "f", "q", "member", OBJ, "group", ("g",), head=("g",), policy="community_invite",
                                cosigners=("q",))], {"a7": T}, {"f", "q"}, [("q", "member", T)]),
    ("R-a: a counted admission naming two keys, one of whose stays has ended, concludes nothing for either (private)",
     REV + "R-a", PV + [XQ, ST.offer("ab", "m1", ("q", "z"), "member", OBJ, "group", ("xq",), head=("xq",),
                                     policy="community_invite", cosigners=("m2", "m3", "m4", "q", "z"))], {"ab": F},
     M4 | {"AG"}, [("z", "member", F), ("q", "member", F)]),
    ("N1: m4 withdraws its standing acceptance that no offer used; an outsider's offer naming it, which concludes "
     "nothing, does not make that a resignation: m4 keeps its seats (private)", REV + "N1",
     PV + [ST.accept("sa", "m4", None, ("ag",), scope="member", obj=OBJ), ST.withdraw("w", "m4", "sa", ("sa",)),
           ST.offer("xo", "X", "m4", "member", OBJ, "self", ("sa",))], {"w": T, "xo": F}, M4 | {"AG", "q"},
     [("m4", "member", T), ("m4", "moderate", T)]),
    ("N1: the same in a public room", REV + "N1",
     PB + [ST.accept("sa", "m4", None, ("ag",), scope="member", obj=OBJ), ST.withdraw("w", "m4", "sa", ("sa",)),
           ST.offer("xo", "X", "m4", "member", OBJ, "self", ("sa",))], {"xo": F}, M4 | {"AG", "q"},
     [("m4", "member", T), ("m4", "moderate", T)]),
    ("N2: z declines an offer, then accepts it afterwards (it seats nothing): the decline is still no end, and a later "
     "admission seats z (private)", REV + "N2",
     PV + [admit("oz", "z", ("m1", "m2", "m3", "m4"), ("ag",), joiner=False), ST.withdraw("wz", "z", "oz", ("oz",)),
           ST.accept("az", "z", "oz", ("wz",)), admit("oz2", "z", ("m1", "m2", "m3", "m4"), ("az",))],
     {"wz": T, "oz2": T}, M4 | {"AG", "q", "z"}, [("z", "member", T)]),
    ("room of two: the founder alone cannot remove the other (a count needs two voices, and the removed member is a "
     "voice; the old one-key route is gone, RK2), the same edge as no lift in a room of two", REV + "RK2",
     [G1, ST.offer("a7", "f", "q", "member", OBJ, "group", ("g",), head=("g",), policy="community_invite", cosigners=("q",)),
      ST.unseat("x7", "f", "q", "member", OBJ, "group", ("a7",), head=("a7",), policy="community_remove")],
     {"a7": T, "x7": F}, {"f", "q"}, [("q", "member", T)]),
    ("R-a: the same batch with no ended key seats both", REV + "R-a",
     PV + [ST.offer("ab", "m1", ("y", "z"), "member", OBJ, "group", ("ag",), head=("ag",), policy="community_invite",
                    cosigners=("m2", "m3", "m4", "y", "z"))], {"ab": T}, M4 | {"AG", "q", "y", "z"}, [("z", "member", T)]),
]

# ---- OPEN: what the text does not decide. (name, ledger row, rows, {row: concludes}, roster, asks, candidates) ----
OPEN = []
# a second seat row of one room key (derived from CC 3.1.3.2 on #224): a second basis for the same seat, one key and
# one voice, no refusal; and an end is the key's end of its stay in that scope, not of a row: one resignation or one
# counted removal ends every seating of the key in that scope in the end's past
SR = PV + [admit("aq2", "q", ("m1", "m2", "m3", "m4"), ("ag",))]          # q's second seat row, while aq seats it
# a later head with both rows in its past: the four founders and q re-state m1's seat (no key admits itself, CC 2.7.5:
# m1's own signature is no voice of its own re-seating, so q's makes four of the five others' two thirds)
SR_H = dict(merge(("aq2",)), cosigners=("m2", "m3", "m4", "q"))
CASES += [
    ("a second seat row of a room key already seated is a second basis for the same seat: it concludes, and the key is "
     "one key and one voice", SECOND_ROW, SR, {"aq2": T}, M4 | {"q", "AG"}, [("q", "member", T)]),
    ("two seat rows, one resignation (q withdraws the first, with both in its past): q is out; the end is of its stay "
     "in that scope, not of a row", SECOND_ROW, SR + [ST.withdraw("wq", "q", "aq", ("aq2",))], {"aq2": T, "wq": T},
     M4 | {"AG"}, [("q", "member", F)]),
    ("two seat rows, one counted removal with both in its past: q is out (the cut reaches every offer on the slot)",
     SECOND_ROW, SR + [SR_H, remove("xq", "q", ("m1", "m2", "m3", "m4"), ("h",))], {"xq": T}, M4 | {"AG"}, [("q", "member", F)]),
    ("public: two seat rows, one resignation, then a re-admission naming it seats q again", SECOND_ROW,
     PB + [admit("aq2", "q", ("m1", "m2", "m3", "m4"), ("ag",)), ST.withdraw("wq", "q", "aq", ("aq2",)),
           rejoin("aq3", "q", ("wq",))], {"aq3": T}, M4 | {"AG", "q"}, [("q", "member", T)]),
    ("private: the same re-admission is refused (membership_room_key_ended)", SECOND_ROW,
     SR + [ST.withdraw("wq", "q", "aq", ("aq2",)), rejoin("aq3", "q", ("wq",))], {"aq3": F}, M4 | {"AG"}, [("q", "member", F)]),
]
# a seat is two consents (the ruling of 2026-11-26 on acceptances, (a)): an invitation of q that q does not sign, at
# the newest head, then q's resignation with the invitation in its past, then q's own acceptance of the invitation.
# A count of three at the invitation naming the acceptance: q does not count (its end ended every seating of it in the
# end's past; in a private room a key whose stay ended completes nothing), so three of four is met
def _late_accept(base):
    o2 = admit("o2", "q", ("m1", "m2", "m3", "m4"), ("ag",), joiner=False)
    return base + [o2, ST.withdraw("wq", "q", "aq", ("o2",)), ST.accept("acq", "q", "o2", ("wq",)),
                   ST.offer("az", "m1", "z", "member", OBJ, "group", ("o2", "acq"), head=("o2",), policy="community_invite",
                            cosigners=("m2", "m3", "z"))]


CASES += [
    ("private: q resigns with an invitation in its end's past and then accepts it: the acceptance completes nothing "
     "(bound (3)); a count of three at the invitation naming it is three of four", OWN_ROW, _late_accept(PV),
     {"wq": T, "az": T}, M4 | {"AG", "z"}, [("q", "member", F)]),
    ("public: the same: the end ended the invitation, which was in its past (bound (2))", OWN_ROW, _late_accept(PB),
     {"wq": T, "az": T}, M4 | {"AG", "z"}, [("q", "member", F)]),
]
# two admissions of one person at once (derived from CC 3.1.3.2 on #224, a residual): the kernel counts voices as
# presented; which keys are one person's is the binding, never a row, so the collapse is the caller's until the voice's
# own key roster is built ("no door refuses a widening for either, since no rule of standing reads a binding")
TWO = PV + [rejoin("ak1", "k1", ("ag",)), rejoin("ak2", "k2", ("ag",))]
# a later head with both admissions in its past (a count over two concurrent heads reads the keys common to both)
# (the four founders and both keys sign it: over the fold of the two tips, seven persons, four is short; the ruling of
# 2026-11-27)
HEAD = dict(merge(("ak1", "ak2")), cosigners=("m2", "m3", "m4", "k1", "k2"))
XQ2 = lambda signers: remove("xq", "q", signers, ("h",))
CASES += [
    ("two admissions of one person at once, under two room keys: both seat. No rule of standing reads a binding, so "
     "the kernel cannot tell them from two persons (a residual: the collapse is the caller's)", TWO_ROW, TWO, {"ak1": T, "ak2": T}, M4 | {"q", "AG", "k1", "k2"},
     [("k1", "member", T), ("k2", "member", T)]),
    ("each is a voice in the room's count: a removal signed by two members and both keys is met (4 of 7, the room's "
     "majority)", TWO_ROW, TWO + [HEAD, XQ2(("m1", "m2", "k1", "k2"))], {"xq": T}, M4 | {"AG", "k1", "k2"}, []),
    ("and without the second key's signature it is not (3 of 7)", TWO_ROW,
     TWO + [HEAD, XQ2(("m1", "m2", "k1"))], {"xq": F}, M4 | {"q", "AG", "k1", "k2"}, []),
]
PLANTS = ("room_key_unread", "public_final", "lone_final", "resign_not_final", "reaccept_reseats", "own_end_unread",
          "own_end_any_seat", "stay_one_row", "class_by_name", "decline_ends_stay", "earlier_consent_kept",
          "end_scope_bound", "ended_unread", "own_roster_row", "own_void_any_key",
          "resigned_any_key", "second_row_refused", "batch_by_key", "consent_any_row")


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


# every counted row and every seat's end of these cases names the newest counted changes over the room in its own
# past (H1, H4, the heads ruling of 2026-11-26): what a signer that holds its own past writes
CASES = [(c[0], c[1], ST.honest(c[2])) + tuple(c[3:]) for c in CASES]


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
