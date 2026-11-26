#!/usr/bin/env python3
"""
check_count_heads.py: the heads of a count, and the reader's line (the heads ruling of 2026-11-26, H1 to H8).

    H1  A count is read at the NEWEST of the heads it names (one in another named head's past is dropped), each a
        counted change over the row's own object or its founding row, and they must be exactly the newest counted
        changes over that object in the row's own past (seat.newer_head_in_past). Concurrent tips are intersected.
    H2  No `over`: a counted row is counted over its own object, and one stating another concludes nothing.
    H3  No read-through of an authored head: a self-admission (one key's row) is no head a count may name, and no
        counted change a count must name.
    H4  No exemption: every row that changes a roster names the newest counted changes over its object in its own
        past or concludes nothing: a moderator's lone removal (whose signer holds `moderate` at those heads, less a
        laying down of it in the removal's past), a self-admission, a resignation (a withdrawal of a seat over a
        room, among the rows it names), a lift (counted at the head its act names).
    H5  The text's reader's line: no test of concurrency (checkpoint.settle, checkpoint.versions); the line is read
        before the cut (seat.Seats).
    H6  A reader's own signed rows are its acknowledgements: every concluded row it signed or cosigned over the object
        (checkpoint.acknowledgements), each acknowledging the counted acts in its own past.
    H7  Retired (the tips ruling of 2026-11-27): the self-fork void (SF, below) subsumes it; its cases now read under
        that rule.
    H8  No caller-synthesised heads: a row of no object, a note, a cosignature naming itself is no head of a count.
    An election's seating (seat.is_election: an offer, conf group, policy ranked) is a roster change: it names the
    newest counted changes as its heads (H4) and sits on the line by them; only its count is not read at its heads
    (election2: its election fixes the electorate).
    A counted change is a roster-changing row that concludes under the policy the room's record binds to its act,
    however many voices that needs: a lone duty holder's conferral, and its own offer of a duty (`self`), are heads.
    A lone duty holder with an offer of a duty seat standing confers no other alone until that offer is accepted or
    withdrawn (LO). The lone-offer rule binds the honest line: A cannot confer alone twice without forking its own
    line. The reader's line covers the fork for every reader that acknowledged the first holder's seat. The two rows
    are the evidence a later count of the room can cite. Outside an election a fork has no automatic effect.

The tips ruling of 2026-11-27 (SF): the members at several heads are the fold of their lines, not the intersection;
a counted change all of whose counted voices acknowledged a change it is behind is void for the counting row (S'':
rescued by an honest continuation's single-chain member, kept on a tie), the ONLY automatic effect of a key signing
two things outside an election, and it voids a change, never a key; a protocol-change tip is under its new protocol;
the changes void for the reader leave a row's fold and heads too; and the line is sibling-safe (a change is behind an
acknowledged change only where every head it names is strictly in the past of that change's own heads).

Each case is read as one batch and in arrival orders of its rows (every order up to six rows above the founding one,
else the batch order, its reverse and forty shuffles). A case marked EDGE states what the rules give at the stated
weak-subjectivity edge: a reader with no row over the room (a member is never such a reader, by H6), and a count that
omits an acceptance its signers have seen (it does only what they could do a moment before the acceptance arrived).
The acceptance cases read the ruling of 2026-11-26 (a): the members at the newest named heads, plus each seat placed
by an offer in those heads' past whose holder's own acceptance of it is in the counted row's own past, less every
leaving in the row's past; the bounds (1) to (4) each have a case (bound (3), a private room, is check_room_keys').
Each rule has a planted break, which must change a case's answer.

    python3 -I check_count_heads.py      exit 1 on any difference
"""
import itertools
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import seat as ST  # noqa: E402
import checkpoint as CP  # noqa: E402

CK = ST.CK
OBJ = "g"
RULE = lambda r, P, past: ST.seat_rule(r, P, past)
T, F = True, False


def admit(i, k, signers, heads, cites=()):
    """A counted admission of k (k cosigning, its own yes), counted at `heads`, naming `cites` too."""
    return ST.offer(i, signers[0], k, "member", OBJ, "group", tuple(heads) + tuple(cites), head=tuple(heads),
                    policy="community_invite", cosigners=tuple(signers[1:]) + ((k,) if k not in signers else ()))


def remove(i, k, signers, heads, cites=(), scope="member"):
    return ST.unseat(i, signers[0], k, scope, OBJ, "group", tuple(heads) + tuple(cites), head=tuple(heads),
                     policy="community_remove", cosigners=tuple(signers[1:]))


def ack(i, reader, head):
    return CK.row(i, "ack", reader, (head,), room=OBJ, head=(head,))


# a room founded by A, B and C (A holds `moderate`), grown to seven by counted admissions, each at the one before
G = ST.found("g", "A", ("A", "B", "C"), {"moderate": ("A",)}, cosigners=("B", "C"))
ROOM = [G]
_mem, _prev = ["A", "B", "C"], "g"
for _k in "DEFG":
    ROOM.append(admit("a" + _k, _k, tuple(_mem), (_prev,)))
    _mem.append(_k)
    _prev = "a" + _k
SEVEN = frozenset("ABCDEFG")
FIVE = ("A", "B", "C", "D", "E")                         # five of the seven: at least two thirds
DC = lambda i, to, heads, cites=(): ST.offer(i, "A", to, "moderate", OBJ, "group", tuple(heads) + tuple(cites), head=tuple(heads),
                                             policy="duty_confer", counted="duty", cosigners=(to,))
RC = lambda heads, by, cites=(): ST.unseat("rc", by[0], "A", "moderate", OBJ, "group", tuple(heads) + tuple(cites), head=heads,
                                           policy="moderator_recall", cosigners=tuple(by[1:]))
SA = lambda i, k, heads, cites=(): ST.offer(i, k, k, "member", OBJ, "group", tuple(heads) + tuple(cites), head=tuple(heads),
                                            policy="open:self_admit")

# world M: m1 and m2 found the room (m1 its moderator), admit an agent's key AG and MOD; m1, the lone holder, confers
# `moderate` on MOD (md); the three admit N (an)
GM = ST.found("g", "m1", ("m1", "m2"), {"moderate": ("m1",)}, cosigners=("m2",))
AGM = dict(admit("ag", "AG", ("m1", "m2"), ("g",)), scope="agent", on=ST._slots("AG", "agent", OBJ))
AMM = admit("am", "MOD", ("m1", "m2"), ("ag",))
MDM = ST.offer("md", "m1", "MOD", "moderate", OBJ, "group", ("am",), head=("am",), policy="duty_confer", counted="duty",
               cosigners=("MOD",))
ANM = admit("an", "N", ("m1", "m2", "MOD"), ("md",))
WM = [GM, AGM, AMM, MDM, ANM]
LONE = lambda i, heads, cites=(), by="MOD": ST.unseat(i, by, "AG", "agent", OBJ, "group", tuple(heads) + tuple(cites), head=tuple(heads),
                                                      policy="community_remove")
WMD = ST.withdraw("wd", "MOD", "md", ("an",))                 # MOD lays its `moderate` seat down, naming the newest change
O1 = CK.row("o1", "answer", "m1", ("xl",), of="xl", says="object")
O2 = CK.row("o2", "answer", "m2", ("xl",), of="xl", says="object")
LIFT = lambda heads: ST.offer("lf", "m1", "AG", "agent", OBJ, "group", ("xl", "o1", "o2") + tuple(heads), head=tuple(heads),
                              content="xl", policy="moderation_overturn", cosigners=("m2", "AG"))


def elect(i, k, heads):
    """An election's seating of k to `moderate`: ballots of B and C ranking k first, and the offer counting them."""
    bs = [ST.R("b" + v + i, "ballot", v, tuple(heads), ranking=(k, "C")) for v in ("B", "C")]
    return bs + [ST.offer(i, "B", k, "moderate", OBJ, "group", tuple(heads) + tuple(b["id"] for b in bs), head=tuple(heads),
                          policy="moderator_election", options=(k, "C"), cosigners=(k,))]


H1, H2, H3, H4, H5, H6, H7, H8, EL, AC, LO, SF, EDGE = ("H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8", "election",
                                                       "acceptance", "lone offer", "self-fork", "EDGE")
SFB = "self-fork (binding off: the removal states `majority`)"


def conf(i, to, heads, cites=(), scope="moderate", signers=("A",), joins=True):
    """A duty conferral counted over the duty holders (`duty_confer`), signed by `signers` (A, the room's lone holder,
    by default); `joins`: each key it seats signs it too (its own yes), else its own acceptance completes the seat."""
    to = (to,) if isinstance(to, str) else tuple(to)
    return ST.offer(i, signers[0], to, scope, OBJ, "group", tuple(heads) + tuple(cites), head=tuple(heads),
                    policy="duty_confer", counted="duty", cosigners=tuple(signers[1:]) + (to if joins else ()))


# an infrastructure room: f1, f2 and f3 found it; the founders admit f4 and then f5 under the room's protocol
GI5 = [ST.offer("g", "f1", ("f1", "f2", "f3"), "member", "@", "self", cosigners=("f2", "f3"), cohort_subkind="infrastructure"),
       ST.offer("a4", "f1", "f4", "founder", OBJ, "group", ("g",), head=("g",), policy="cosigned_act", cosigners=("f2", "f3", "f4")),
       ST.offer("a5", "f1", "f5", "founder", OBJ, "group", ("a4",), head=("a4",), policy="cosigned_act",
                cosigners=("f2", "f3", "f4", "f5"))]
FIVE_F = frozenset(("f1", "f2", "f3", "f4", "f5"))
IX = lambda i, heads, signers, cites=(): ST.unseat(i, signers[0], "f3", "founder", OBJ, "group", tuple(heads) + tuple(cites),
                                                   head=tuple(heads), policy="cosigned_act", cosigners=tuple(signers[1:]))


# a room under the protocol `one` (L'): A, B and C found it
GQ = ST.found("g", "A", ("A", "B", "C"), {"moderate": ("A",)}, cosigners=("B", "C"), consensus_protocol="one")
QA = lambda i, k, sg, heads, cites=(): ST.offer(i, sg[0], k, "member", OBJ, "group", tuple(heads) + tuple(cites), head=tuple(heads),
                                                 policy="cosigned_act", cosigners=tuple(sg[1:]) + (k,))
QR = lambda i, k, sg, heads, cites=(): ST.unseat(i, sg[0], k, "member", OBJ, "group", tuple(heads) + tuple(cites),
                                                  head=tuple(heads), policy="community_remove", cosigners=tuple(sg[1:]))
QDC = ST.offer("dc", "A", "B", "moderate", OBJ, "group", ("g",), head=("g",), policy="duty_confer", counted="duty", cosigners=("B",))


def lprime(aD_by, aE_by):
    """L': the honest chain's first change signed by aD_by, then the honest C, D, E.. on top; A and B fork at g."""
    return [GQ, QA("aD", "D", aD_by, ("g",)), QA("aE", "E", aE_by, ("aD",)), QA("aF", "F", ("C", "D", "E"), ("aE",)),
            QA("aG", "G", ("C", "D", "E", "F"), ("aF",)), QDC, QA("xd", "X", ("A", "B"), ("dc",))]


# the protocol raised after g: a room under `one` founded by A..F; the honest C..F admit G and raise it to two_thirds;
# A and B (who signed nothing of it) pack X1..Xn from g under the old protocol
GQ6 = ST.found("g", "A", tuple("ABCDEF"), {"moderate": ("A",)}, cosigners=tuple("BCDEF"), consensus_protocol="one")
def raised(n, row):
    rows = [GQ6, QA("ag2", "G", ("C", "D", "E", "F"), ("g",)),
            ST.offer("amq", "C", (), "record", OBJ, "group", ("ag2",), head=("ag2",), policy="cosigned_act",
                     consensus_protocol="two_thirds", cosigners=("D", "E", "F", "G"))]
    sg, prev = ["A", "B"], "g"
    for i in range(1, n + 1):
        rows.append(QA("q%d" % i, "X%d" % i, tuple(sg), (prev,))); sg.append("X%d" % i); prev = "q%d" % i
    return rows + [row(tuple(sg), ("amq", prev))]


# the silent colluder: A signs the honest admissions with C; B signs nothing after g; A and B chain X1..Xn from g
def silent(n, row):
    rows, mem, prev = [G], ["A", "C"], "g"
    for k in "DEFG":
        rows.append(admit("a" + k, k, tuple(mem), (prev,))); mem.append(k); prev = "a" + k
    sg, fp = ["A", "B"], "g"
    for i in range(1, n + 1):
        rows.append(admit("p%d" % i, "X%d" % i, tuple(sg), (fp,))); sg.append("X%d" % i); fp = "p%d" % i
    return rows + [row(tuple(sg), fp)]


# the second review of 58b: a void change cuts nothing in a reader's roster (rd); a rescuer that signed both chains
G4 = ST.found("g", "A", ("A", "B", "C", "H"), {"moderate": ("A",)}, cosigners=("B", "C", "H"), consensus_protocol="one")
RD = [G, admit("aD", "D", ("A", "B", "C"), ("g",)), admit("aE", "E", ("A", "B", "C", "D"), ("aD",)),
      admit("aF", "F", ("A", "B", "C", "E"), ("aE",)), admit("aG", "G", ("A", "B", "C", "E", "F"), ("aF",)),
      remove("f", "E", ("A", "B", "C"), ("aD",))]


# a room of one: A founds it alone (its lone founder, holding `moderate`), and invites under `community_invite`
G1 = ST.found("g", "A", ("A",), {})
ONE = lambda i, k, heads, signers=("A",): ST.offer(i, signers[0], k, "member", OBJ, "group", tuple(heads), head=tuple(heads),
                                                   policy="community_invite", cosigners=tuple(signers[1:]) + (k,))

# world N: A, B and C found the room and admit D (four members); the four invite N by a counted offer N does not sign,
# at the newest head, and N accepts it by its own row. The invitation is the newest counted change; N's acceptance is no
# counted change and no head. A count of three: at least two thirds of four (3 of 4) is met, of five (3 of 5) is not.
WN = [G, admit("aD", "D", ("A", "B", "C"), ("g",)),
      ST.offer("oN", "A", "N", "member", OBJ, "group", ("aD",), head=("aD",), policy="community_invite", cosigners=("B", "C", "D"))]
ACN = ST.accept("acN", "N", "oN")
FOUR = frozenset("ABCD")


def invite(i, k, signers, heads, cites=()):
    """A counted invitation of k that k does not sign: a seat when k's own acceptance completes it."""
    return ST.offer(i, signers[0], k, "member", OBJ, "group", tuple(heads) + tuple(cites), head=tuple(heads),
                    policy="community_invite", cosigners=tuple(signers[1:]))
# (rule, name, rows, reader, {row: concludes}, {scope: holders}, stale)
CASES = [
    # ---- H1 ---------------------------------------------------------------------------------------------------------
    (H1, "a counted admission names the founding head and has the newest admission in its own past",
     ROOM + [admit("ax", "X", ("A", "B"), ("g",), ("aG",))], None, {"ax": F}, {"member": SEVEN}, set()),
    (H1, "the same admission at the newest head, by five of the seven",
     ROOM + [admit("ax", "X", FIVE, ("aG",))], None, {"ax": T}, {"member": SEVEN | {"X"}}, set()),
    (H1, "a counted removal names the founding head and has the newest admission in its own past",
     ROOM + [remove("xg", "G", ("A", "B"), ("g",), ("aG",))], None, {"xg": F}, {"member": SEVEN}, set()),
    (H1, "the same removal at the newest head, by five of the seven",
     ROOM + [remove("xg", "G", FIVE, ("aG",))], None, {"xg": T}, {"member": SEVEN - {"G"}}, set()),
    (H1, "a counted removal names the founding head and the newest admission together",
     ROOM + [remove("xg", "G", ("A", "B"), ("g", "aG"))], None, {"xg": F}, {"member": SEVEN}, set()),
    (H1, "a counted admission names the founding head and the newest admission together",
     ROOM + [admit("ax", "X", ("A", "B"), ("g", "aG"))], None, {"ax": F}, {"member": SEVEN}, set()),
    (H1, "the same removal, for a reader that acknowledged the newest admission",
     ROOM + [ack("ak", "R", "aG"), remove("xg", "G", ("A", "B"), ("g", "aG"))], "R", {"xg": F}, {"member": SEVEN}, set()),
    (H1, "a counted removal by three names the fourth member's admission and the newest admission together",
     ROOM + [remove("xg", "G", ("A", "B", "C"), ("aD", "aG"))], None, {"xg": F}, {"member": SEVEN}, set()),
    (H1, "a recall of the moderator names the founding head and the newest admission together",
     ROOM + [RC(("g", "aG"), ("B", "C"))], None, {"rc": F}, {"moderate": {"A"}}, set()),
    (H1, "a recall of the moderator names the founding head and has the newest admission in its own past",
     ROOM + [RC(("g",), ("B", "C"), ("aG",))], None, {"rc": F}, {"moderate": {"A"}}, set()),
    (H1, "the same recall at the newest head, by five of the seven",
     ROOM + [RC(("aG",), ("B", "C", "D", "E", "F"))], None, {"rc": T}, {"moderate": set()}, set()),
    (H1, "a duty conferral by the lone holder names the founding head and has the newest admission in its own past",
     ROOM + [DC("dc", "B", ("g",), ("aG",))], None, {"dc": F}, {"moderate": {"A"}}, set()),
    (H1, "the same duty conferral at the newest head",
     ROOM + [DC("dc", "B", ("aG",))], None, {"dc": T}, {"moderate": {"A", "B"}}, set()),
    (H1, "two admissions at the newest head, concurrent, and a removal by five naming both tips: the fold seats both "
         "newcomers, and five of nine is short",
     ROOM + [admit("aX", "X", FIVE, ("aG",)), admit("aY", "Y", FIVE, ("aG",)), remove("xg", "G", FIVE, ("aX", "aY"))], None,
     {"aX": T, "aY": T, "xg": F}, {"member": SEVEN | {"X", "Y"}}, set()),
    (H1, "the same removal by six of the nine, the newcomers among them: met",
     ROOM + [admit("aX", "X", FIVE, ("aG",)), admit("aY", "Y", FIVE, ("aG",)),
             remove("xg", "G", FIVE + ("X",), ("aX", "aY"))], None,
     {"xg": T}, {"member": (SEVEN | {"X", "Y"}) - {"G"}}, set()),
    (H1, "a removal at the founding head that has not seen the admissions (concurrent with them) concludes; no reader: "
         "A and B signed the admissions it is behind, so it is self-forked over the rows the roster holds, and G stays "
         "(a void change neither adds nor removes members)",
     ROOM + [remove("xg", "G", ("A", "B"), ("g",))], None, {"xg": T}, {"member": SEVEN}, {"xg"}),
    (H1, "a counted change of another room in a row's past moves no head of this one",
     ROOM + [ST.found("h", "A", ("A",), {}),
             ST.offer("ah", "A", "B", "member", "h", "group", ("h",), head=("h",), policy="community_invite", cosigners=("B",)),
             remove("xg", "G", FIVE, ("aG",), ("ah",))], None, {"ah": T, "xg": T}, {"member": SEVEN - {"G"}}, set()),
    # an infrastructure room, its founder body (the binding's: the founding record's members, then founders admitted
    # by the founders' count under the room's protocol), f1 to f5 (review-54, r59/tools/e2.py)
    (H1, "infrastructure: a removal of f3 by f1 and f2 at the old head g (three founders there), the newest admission "
         "in its past: it concludes nothing",
     GI5 + [IX("x", ("g",), ("f1", "f2"), ("a5",))], None, {"a4": T, "a5": T, "x": F}, {"member": FIVE_F}, set()),
    (H1, "infrastructure: the same removal naming both the current head a5 and the old head g: the named heads are no "
         "antichain (g is in a5's past), and it concludes nothing",
     GI5 + [IX("x", ("a5", "g"), ("f1", "f2"))], None, {"x": F}, {"member": FIVE_F}, set()),
    (H1, "infrastructure: four of the five naming a5 and g: met at a5, and still refused, the named heads no antichain",
     GI5 + [IX("x", ("a5", "g"), ("f1", "f2", "f4", "f5"))], None, {"x": F}, {"member": FIVE_F}, set()),
    (H1, "infrastructure: four of the five at a5 alone: it concludes",
     GI5 + [IX("x", ("a5",), ("f1", "f2", "f4", "f5"))], None, {"x": T}, {}, set()),
    # ---- H2 ---------------------------------------------------------------------------------------------------------
    (H2, "an admission in a second room stating that it is counted over the first room's roster",
     ROOM + [ST.found("h", "A", ("A",), {}),
             ST.offer("ox", "A", "X", "member", "h", "group", ("h", "aG"), head=("h",), over="g", policy="community_invite",
                      cosigners=("X",))], None, {"ox": F}, {}, set()),
    (H2, "a row counted over another object it writes itself (i3): an outsider's self-admission over its own note",
     ROOM + [ack("x", "Z", "g"), dict(SA("y", "Z", ("x",), ("aG",)), over="x")], None, {"y": F}, {"member": SEVEN}, set()),
    # ---- H3 ---------------------------------------------------------------------------------------------------------
    (H3, "an outsider admits itself at the newest head; a removal by five names that self-admission as its head",
     ROOM + [SA("sa", "Z", ("aG",)), remove("xg", "G", FIVE, ("sa",))], None, {"sa": T, "xg": F}, {"member": SEVEN | {"Z"}}, set()),
    (H3, "the same removal names the fourth member's admission and the self-admission together",
     ROOM + [SA("sa", "Z", ("aG",)), remove("xg", "G", FIVE, ("aD", "sa"))], None, {"sa": T, "xg": F}, {"member": SEVEN | {"Z"}}, set()),
    (H3, "the same removal at the newest admission, the self-admission in its past: the self-admitted key is no voice of it",
     ROOM + [SA("sa", "Z", ("aG",)), remove("xg", "G", FIVE, ("aG",), ("sa",))], None, {"sa": T, "xg": T},
     {"member": (SEVEN | {"Z"}) - {"G"}}, set()),
    (H3, "a founder's own 'self-admission' at the founding head (i1) is no head for a removal by two",
     ROOM + [SA("y", "A", ("g",), ("aG",)), remove("xg", "G", ("A", "B"), ("y",))], None, {"y": F, "xg": F}, {"member": SEVEN}, set()),
    # ---- H4 ---------------------------------------------------------------------------------------------------------
    (H4, "a moderator's lone removal of an agent's key at its seat's head, with a later admission in its own past",
     WM + [LONE("xl", ("md",), ("an",))], None, {"xl": F}, {"member": {"m1", "m2", "MOD", "N"}, "agent": {"AG"}}, set()),
    (H4, "the same lone removal at the newest head",
     WM + [LONE("xl", ("an",))], None, {"xl": T}, {"member": {"m1", "m2", "MOD", "N"}, "agent": set()}, set()),
    (H4, "a moderator lays its seat down and then removes an agent's key alone at the newest head",
     WM + [WMD, LONE("xl", ("an",), ("wd",))], None, {"wd": T, "xl": F}, {"moderate": {"m1"}, "agent": {"AG"}}, set()),
    (H4, "the same removal concurrent with the moderator's laying down: it concludes",
     WM + [WMD, LONE("xl", ("an",))], None, {"wd": T, "xl": T}, {"moderate": {"m1"}}, set()),
    (H4, "an outsider's self-admission at the founding head, with the newest admission in its own past",
     ROOM + [SA("sa", "Z", ("g",), ("aG",))], None, {"sa": F}, {"member": SEVEN}, set()),
    (H4, "a member resigns, its withdrawal naming its admission and a note with a later admission in its past",
     ROOM + [admit("aH", "H", tuple(sorted(SEVEN)), ("aG",)), CK.row("k", "note", "D", ("aH",)),
             ST.withdraw("wg", "G", "aG", ("aG", "k"))], None, {"wg": F}, {"member": SEVEN | {"H"}}, set()),
    (H4, "the same resignation naming the later admission: it concludes",
     ROOM + [admit("aH", "H", tuple(sorted(SEVEN)), ("aG",)), ST.withdraw("wg", "G", "aG", ("aG", "aH"))], None,
     {"wg": T}, {"member": (SEVEN | {"H"}) - {"G"}}, set()),
    (H4, "the members' lift at the head the removal names, older than the removal itself",
     WM + [LONE("xl", ("an",)), O1, O2, LIFT(("an",))], None, {"xl": T, "lf": F}, {"agent": set()}, set()),
    (H4, "the members' lift at the removal, the newest counted change in its past: the key is seated again",
     WM + [LONE("xl", ("an",)), O1, O2, LIFT(("xl",))], None, {"xl": T, "lf": T}, {"agent": {"AG"}}, set()),
    # ---- H5: the line before the cut --------------------------------------------------------------------------------
    (H5, "a removal at the founding head concurrent with the admissions, for a reader that acknowledged the newest: it is "
         "behind the line and cuts nothing for that reader",
     ROOM + [ack("ak", "R", "aG"), remove("xg", "G", ("A", "B"), ("g",))], "R", {"xg": T}, {"member": SEVEN}, {"xg"}),
    (H5, "a reader acknowledged an admission built on an admission of X; a removal of X at the head before it and a "
         "sibling admission there: every head each names is strictly in the past of the acknowledged admission's own "
         "heads, so the line holds both behind",
     ROOM + [admit("ax", "X", FIVE, ("aG",)), admit("ax2", "W", FIVE + ("X",), ("ax",)), remove("xx", "X", FIVE, ("aG",)),
             admit("ay", "Y", FIVE, ("aG",)), ack("ak", "R", "ax2")], "R", {"ax": T, "ax2": T, "xx": T, "ay": T},
     {"member": SEVEN | {"X", "W"}}, {"xx", "ay"}),
    (H5, "the line is sibling-safe (the ruling of 2026-11-27): a reader acknowledged one of two admissions at one head; "
         "the other is no change behind it, and both stand",
     ROOM + [admit("ax", "X", FIVE, ("aG",)), admit("ay", "Y", FIVE, ("aG",)), ack("ak", "R", "ax")], "R",
     {"ax": T, "ay": T}, {"member": SEVEN | {"X", "Y"}}, set()),
    # ---- H6 ---------------------------------------------------------------------------------------------------------
    (H6, "the same removal, for a founder that signed every admission and wrote no acknowledgement row",
     ROOM + [remove("xg", "G", ("A", "B"), ("g",))], "C", {"xg": T}, {"member": SEVEN}, {"xg"}),
    (H6, "a cheap concurrent tip (A's lone duty conferral at the founding head) and a removal by two naming it and the "
         "newest admission, for the newest member G (its own admission is its acknowledgement)",
     ROOM + [DC("dc", "B", ("g",)), remove("xg", "G", ("A", "B"), ("dc", "aG"))], "G", {"dc": T, "xg": F}, {"member": SEVEN}, {"dc"}),
    (H6, "a minority packs the room from the founding past (two admissions chained) and removes D with them, for D",
     ROOM + [admit("p1", "X1", ("A", "B"), ("g",)), admit("p2", "X2", ("A", "B", "X1"), ("p1",)),
             remove("xd", "D", ("A", "B", "X1", "X2"), ("aG", "p2"))], "D", {"p1": T, "p2": T, "xd": F}, {"member": SEVEN},
     {"p1"}),
    # ---- H7 ---------------------------------------------------------------------------------------------------------
    (H7, "the cheap tip in the past of an honest removal by five at the newest admission: behind its signers' "
         "acknowledgements, it need not be named",
     ROOM + [DC("dc", "B", ("g",)), remove("xg", "G", FIVE, ("aG",), ("dc",))], None, {"dc": T, "xg": T},
     {"member": SEVEN - {"G"}}, {"dc"}),
    (H7, "a row built on the cheap tip is no change behind an acknowledgement: the honest removal must name it",
     ROOM + [DC("dc", "B", ("g",)), ST.offer("dc2", "A", "C", "moderate", OBJ, "group", ("dc",), head=("dc",), policy="duty_confer",
                                             counted="duty", cosigners=("B", "C")), remove("xg", "G", FIVE, ("aG",), ("dc2",))], None,
     {"dc": T, "dc2": T, "xg": F}, {"member": SEVEN}, set()),
    # ---- H8 ---------------------------------------------------------------------------------------------------------
    (H8, "a removal by five names a note naming the newest admission as its head",
     ROOM + [CK.row("v", "note", "D", ("aG",)), remove("xg", "G", FIVE, ("v",))], None, {"xg": F}, {"member": SEVEN}, set()),
    (H8, "a removal by five names a cosignature whose `of` is itself",
     ROOM + [ST.R("v", "cosign", "D", ("aG",), of="v"), remove("xg", "G", FIVE, ("v",))], None, {"xg": F}, {"member": SEVEN}, set()),
    # ---- an election's seating --------------------------------------------------------------------------------------
    (EL, "an election's seating at the newest admission: it names its heads as any roster change (H4) and seats D",
     ROOM + [ST.withdraw("lm", "A", "g", ("g", "aG"), scope="moderate")] + elect("se", "D", ("aG",)), None,
     {"se": T}, {"moderate": {"D"}}, set()),
    (EL, "the same seating at the founding head, with the newest admission in its past: it concludes nothing (H4)",
     ROOM + [ST.withdraw("lm", "A", "g", ("g", "aG"), scope="moderate")] +
     [dict(q, names=tuple(q["names"]) + ("aG",), head=("g",)) if q["id"] == "se" else q for q in elect("se", "D", ("g",))],
     None, {"se": F}, {"moderate": set()}, set()),
    (EL, "the seating at the newest admission, a sibling of a later admission a reader acknowledged: not behind (the line "
         "is sibling-safe)",
     ROOM + [admit("aH", "H", tuple(sorted(SEVEN)), ("aG",)), ack("ak", "R", "aH"),
             ST.withdraw("lm", "A", "g", ("g", "aG"), scope="moderate")] + elect("se", "D", ("aG",)), "R",
     {"se": T}, {"moderate": set()}, set()),
    (EL, "the seating at the head before an admission built on a later one the reader acknowledged: behind that "
         "reader's line by its heads, as any roster change",
     ROOM + [admit("aH", "H", tuple(sorted(SEVEN)), ("aG",)), admit("aI", "I", tuple(sorted(SEVEN | {"H"})), ("aH",)),
             ack("ak", "R", "aI"), ST.withdraw("lm", "A", "g", ("g", "aG"), scope="moderate")] + elect("se", "D", ("aG",)), "R",
     {"se": T}, {"moderate": set()}, {"se"}),
    (EL, "a later admission at the newest admission, leaving the seating unnamed in its past (it names the ballots)",
     ROOM + [ST.withdraw("lm", "A", "g", ("g", "aG"), scope="moderate")] + elect("se", "D", ("aG",)) +
     [admit("ax", "X", FIVE, ("aG",), ("se",))], None, {"se": T, "ax": F}, {"moderate": {"D"}, "member": SEVEN}, set()),
    # ---- acceptances: the members at the heads, plus each seat placed by an offer in the heads' past whose holder's
    # own acceptance of it is in the counted row's own past (the ruling of 2026-11-26, (a)) ---------------------------
    (AC, "an invitation accepted, and a count by three at the invitation naming the acceptance: N counts, and three of "
         "five is short of two thirds",
     WN + [ACN, invite("aP", "P", ("A", "B", "C"), ("oN",), ("acN",))], None, {"oN": T, "acN": T, "aP": F},
     {"member": FOUR | {"N"}}, set()),
    (AC, "the same count by four of the five: met",
     WN + [ACN, invite("aP", "P", ("A", "B", "C", "D"), ("oN",), ("acN",))], None, {"aP": T}, {"member": FOUR | {"N"}}, set()),
    (AC, "the newcomer's acceptance completes its seat for its own count: N and three others, four of five",
     WN + [ACN, invite("aP", "P", ("N", "A", "B", "C"), ("oN",), ("acN",))], None, {"aP": T}, {"member": FOUR | {"N"}}, set()),
    (AC, "(1) two concurrent invitations, each accepted, and a count by three naming both tips: the fold seats both "
         "newcomers (each seat placed at its own tip and completed there), and three of six is short",
     WN[:2] + [invite("oN", "N", ("A", "B", "C", "D"), ("aD",)), invite("oM", "M", ("A", "B", "C", "D"), ("aD",)),
               ST.accept("acN", "N", "oN"), ST.accept("acM", "M", "oM"),
               invite("aP", "P", ("A", "B", "C"), ("oN", "oM"), ("acN", "acM"))], None, {"aP": F},
     {"member": FOUR | {"N", "M"}}, set()),
    (AC, "(1') an acceptance whose offer is at neither head completes nothing: the count by four at oM alone, N's "
         "acceptance in its past and oN not: N is not counted, four of five (A, B, C, D, M) is met. oN's voices then "
         "signed the count, which oN is behind (a sibling they built past): oN is void for the roster and N is not "
         "seated (a stale honest change is signed again forward)",
     WN[:2] + [invite("oN", "N", ("A", "B", "C", "D"), ("aD",)), invite("oM", "M", ("A", "B", "C", "D"), ("aD",)),
               ST.accept("acM", "M", "oM"), ST.accept("acN", "N", "oN"),
               invite("aP", "P", ("A", "B", "C", "D"), ("oM",), ("acM",))], None, {"aP": T},
     {"member": FOUR | {"M"}}, {"oN"}),
    (AC, "(2) the invitation withdrawn by its conferrer before the count, the acceptance in the count's past: the offer is "
         "ended there and completes nothing, three of four",
     WN + [ACN, ST.withdraw("wo", "A", "oN", ("acN",)), invite("aP", "P", ("A", "B", "C"), ("oN",), ("wo",))], None,
     {"aP": T}, {}, set()),
    (AC, "(4) a cosignature by N of the invitation is no acceptance: N is not seated and does not count, three of four",
     WN + [ST.R("csN", "cosign", "N", ("oN",), of="oN"), invite("aP", "P", ("A", "B", "C"), ("oN",), ("csN",))], None,
     {"aP": T}, {"member": FOUR}, set()),
    # ---- a lone duty holder's standing offer (the ruling of 2026-11-26): A lone duty holder with an offer of a duty
    # seat standing confers no other alone until that offer is accepted or withdrawn --------------------------------
    (LO, "A, the lone holder, offers moderate to B (no yes yet) and then confers moderate on C alone, the offer in its "
         "past: the second concludes nothing",
     ROOM + [conf("oB", "B", ("aG",), joins=False), conf("oC", "C", ("oB",))], None, {"oB": T, "oC": F},
     {"moderate": {"A"}}, set()),
    (LO, "the same after A withdraws its offer to B (its own end of its own offer): the lone conferral concludes",
     ROOM + [conf("oB", "B", ("aG",), joins=False), ST.withdraw("wB", "A", "oB", ("oB",)), conf("oC", "C", ("oB",), ("wB",))],
     None, {"oB": T, "oC": T}, {"moderate": {"A", "C"}}, set()),
    (LO, "any duty: A's standing offer of `review` to B stops its lone conferral of `moderate` on C",
     ROOM + [conf("oB", "B", ("aG",), scope="review", joins=False), conf("oC", "C", ("oB",))], None, {"oB": T, "oC": F},
     {"moderate": {"A"}, "review": set()}, set()),
    (LO, "the same on the lone holder's own path: A's own offer of moderate to B (no yes yet), then its own offer of "
         "moderate to C naming it: the second concludes nothing",
     ROOM + [ST.offer("s1", "A", "B", "moderate", OBJ, "self", ("aG",)), ST.offer("s2", "A", "C", "moderate", OBJ, "self", ("s1",),
                                                                                   cosigners=("C",))],
     None, {"s1": T, "s2": F}, {"moderate": {"A"}}, set()),
    (LO, "two new holders at once: one row naming both, each signing it, concludes whole",
     ROOM + [conf("oBC", ("B", "C"), ("aG",))], None, {"oBC": T}, {"moderate": {"A", "B", "C"}}, set()),
    (LO, "two rows: the first seats B (its yes on it), so the second is counted over A and B, and A alone is short",
     ROOM + [conf("oB", "B", ("aG",)), conf("oC", "C", ("oB",))], None, {"oB": T, "oC": F}, {"moderate": {"A", "B"}}, set()),
    # the self-fork (the window, stated): the lone-offer rule binds the honest line: A cannot confer alone twice
    # without forking its own line. The reader's line covers the fork for every reader that acknowledged the first
    # holder's seat. The two rows are the evidence a later count of the room can cite. Outside an election a fork has
    # no automatic effect
    (LO, "self-fork before B accepted: A's second lone conferral, to C, leaves its own offer to B out of its past and "
         "concludes; B accepts after. For a reader with no row: A, B and C hold (what one row naming both gives)",
     ROOM + [conf("oB", "B", ("aG",), joins=False), conf("oC", "C", ("aG",)), ST.accept("acB", "B", "oB")], None,
     {"oB": T, "oC": T, "acB": T}, {"moderate": {"A", "B", "C"}}, set()),
    (LO, "the same read by B: oC is a sibling of the offer B acknowledged (both at aG), so it is not behind B's line "
         "(the line is sibling-safe): A, B and C hold",
     ROOM + [conf("oB", "B", ("aG",), joins=False), conf("oC", "C", ("aG",)), ST.accept("acB", "B", "oB")], "B",
     {"oC": T}, {"moderate": {"A", "B", "C"}}, set()),
    (EDGE, "self-fork after B's seat exists (B signed it; B and D have acknowledged it since): the forked conferral to C "
           "at the same head is a sibling of B's seat and is behind no reader's line: A, B and C hold. The window, stated: "
           "a lone holder that forks at the head of its own first conferral is one key that said two things; the two "
           "rows are the evidence a later count can cite",
     ROOM + [conf("oB", "B", ("aG",)), ack("kB", "B", "oB"), ack("kD", "D", "oB"), conf("oC", "C", ("aG",))], "B",
     {"oB": T, "oC": T}, {"moderate": {"A", "B", "C"}}, set()),
    (LO, "the fork after a change built on B's seat that B signed (B's own conferral with A of review on E): the forked "
         "conferral at the older head is behind B's line, and void for B",
     ROOM + [conf("oB", "B", ("aG",)), conf("rE", "E", ("oB",), scope="review", signers=("A", "B")), conf("oC", "C", ("aG",))],
     "B", {"oB": T, "rE": T, "oC": T}, {"moderate": {"A", "B"}}, {"oC"}),
    # ---- a room of one invites two (probe, the answers as built): the newcomer's yes is the second voice ------------
    (LO, "a room of one invites N1 and N2 by two concurrent proposals at the founding head, each with the newcomer's "
         "yes: both conclude",
     [G1, ONE("n1", "N1", ("g",)), ONE("n2", "N2", ("g",))], None, {"n1": T, "n2": T}, {"member": {"A", "N1", "N2"}}, set()),
    (LO, "the same proposals in sequence, the second at the first: it is counted over A and N1, and A alone is short",
     [G1, ONE("n1", "N1", ("g",)), ONE("n2", "N2", ("n1",))], None, {"n1": T, "n2": F}, {"member": {"A", "N1"}}, set()),
    (LO, "after the two concurrent admissions, A alone admits N3 at both tips: the fold seats A, N1 and N2, so A alone is "
         "one of three and short",
     [G1, ONE("n1", "N1", ("g",)), ONE("n2", "N2", ("g",)), ONE("n3", "N3", ("n1", "n2"))], None, {"n3": F},
     {"member": {"A", "N1", "N2"}}, set()),
    (LO, "the same read by N1: N2's admission is a sibling of N1's own, not behind its line: the same roster",
     [G1, ONE("n1", "N1", ("g",)), ONE("n2", "N2", ("g",)), ONE("n3", "N3", ("n1", "n2"))], "N1", {"n3": F},
     {"member": {"A", "N1", "N2"}}, set()),
    # ---- S'': the self-fork void, its rescue and its tie (the ruling of 2026-11-27). This is the ONLY automatic effect of
    # a key signing two things outside an election, and it voids a change, never a key --------------------------------
    (SFB, "L': the honest chain's first change signed only by A and B, then C, D and the newcomers on it; A and B fork at "
         "g: aD is self-forked, and rescued by C (a member at g who signed only the honest chain): C..G remove A, five of the eight the fold seats",
     lprime(("A", "B"), ("C", "D")) + [dict(QR("xa", "A", ("C", "D", "E", "F", "G"), ("xd", "aG")), policy="majority")], None, {"xa": T},
     {"member": frozenset("BCDEFGX")}, set()),
    (SFB, "L' with A and B on aE too: the fork is self-forked and unrescued, and void for the removal; the honest chain "
         "is rescued by C",
     lprime(("A", "B"), ("A", "B", "C", "D")) + [dict(QR("xa", "A", ("C", "D", "E", "F", "G"), ("xd", "aG")), policy="majority")], None, {"xa": T},
     {"member": frozenset("BCDEFG")}, {"dc", "xd"}),
    (SF, "S'' against itself: A and B sign two chains at g, each first row behind the other's second; no single-chain "
         "member on either side: both are kept, and A, B and C admitting Z at both tips is a count over the fold",
     [G, admit("q1", "D", ("A", "B"), ("g",)), admit("q2", "X", ("A", "B"), ("g",)), admit("q1b", "E", ("A", "B", "D"), ("q1",)),
      admit("q2b", "Y", ("A", "B", "X"), ("q2",)), admit("rz", "Z", ("A", "B", "C", "D", "E", "X", "Y"), ("q1b", "q2b"))], None,
     {"rz": T}, {"member": frozenset("ABCDEXYZ")}, set()),
    (SF, "the protocol raised after g: A and B, who signed nothing of the honest line, pack X1 and X2 from g under the "
         "old protocol: a tip that is the protocol change is under its new protocol, so the tips are two regimes and fold "
         "to their common keys; C..G remove A",
     raised(2, lambda sg, heads: ST.unseat("xa", "C", "A", "member", OBJ, "group", heads, head=heads, policy="community_remove",
                                           cosigners=("D", "E", "F", "G"))), None, {"xa": T}, {}, set()),
    (SF, "the same: the packers A, B, X1, X2 remove C, and conclude nothing",
     raised(2, lambda sg, heads: ST.unseat("xc", "A", "C", "member", OBJ, "group", heads, head=heads, policy="community_remove",
                                           cosigners=sg[1:])), None, {"xc": F}, {}, set()),
    (SF, "the silent colluder: A signs the honest admissions with C, B signs nothing after g, and A and B chain X1 and X2 "
         "from g. Nothing is self-forked (B acknowledged nothing the chain is behind): for a reader with no row, C..G's "
         "removal of A is five of nine and short",
     silent(2, lambda sg, fp: remove("xr", "A", tuple("CDEFG"), ("aG", fp))), None, {"xr": F},
     {"member": frozenset("ABCDEFG") | {"X1", "X2"}}, set()),
    (SF, "the same read by D: X1's admission is behind D's line, so it and the chain on it leave the removal's fold for D "
         "(the reader-line exclusion): the removal concludes for D, and A is out of D's roster",
     silent(2, lambda sg, fp: remove("xr", "A", tuple("CDEFG"), ("aG", fp))), "D", {"xr": F},
     {"member": frozenset("BCDEFG")}, {"p1"}),
    (SF, "acknowledging never un-voids: the same rows read by C, whose own honest removal names p2 as a head (H1 asks it, "
         "it has seen p2): the chain stays behind C's line, and is no part of C's roster",
     silent(2, lambda sg, fp: remove("xr", "A", tuple("CDEFG"), ("aG", fp))), "C", {"xr": F},
     {"member": frozenset("BCDEFG")}, {"p1"}),
    (SF, "both ways: D's removal at aG alone (a client that does not build on a change void for it): concurrent with p1, "
         "no self-fork, and for D the same count as the removal naming p2: it concludes, and A is out",
     silent(2, lambda sg, fp: remove("xr", "A", tuple("CDEFG"), ("aG",))), "D", {"xr": T},
     {"member": frozenset("BCDEFG")}, {"p1"}),
    (EDGE, "both ways, for a reader with no row: the removal at aG alone concludes (five of seven), the one naming p2 is "
           "five of nine and does not (the case above): for that reader alone the two differ, as it holds the chain. Its "
           "roster is then the fold of the two tips, the removal's line and the chain's: A is out on one, so the admissions "
           "A signed meet no count on the voices the fold seats, and only B and C are common",
     silent(2, lambda sg, fp: remove("xr", "A", tuple("CDEFG"), ("aG",))), None, {"xr": T},
     {"member": frozenset("BC")}, set()),
    (SF, "acknowledging never un-voids: D, whose line holds the chain void, then writes an explicit acknowledgement "
         "naming p2 and the newest honest admission (its own earlier rows in its past): the chain stays void for D (an "
         "acknowledgement closes older heads and nothing reopens them, CC 2.7.9)",
     silent(2, lambda sg, fp: CK.row("kD", "ack", "D", ("aG", fp), room=OBJ, head=("aG", fp))), "D", {},
     {"member": frozenset("ABCDEFG")}, {"p1"}),
    (SF, "a counted row is no acknowledgement of a change void for it: Z, whose one row is its cosignature of C..G's "
         "removal of A naming the fork-built xd, holds the fork void (S'' voids dc and xd for that row)",
     ROOM + [DC("dc", "B", ("g",)), admit("xd", "X", ("A", "B"), ("dc",)),
             dict(remove("xa", "A", ("C", "D", "E", "F", "G"), ("xd", "aG")), cosigners=("D", "E", "F", "G", "Z"))], "Z",
     {"xa": T}, {"member": frozenset("BCDEFG")}, {"dc"}),
    (SF, "the line before the cut: A and B (B silent since g) remove E at the founding head; not self-forked (B "
         "acknowledged nothing it is behind), but behind D's line: it cuts nothing for D, and E stays",
     silent(0, lambda sg, fp: remove("xe", "E", ("A", "B"), ("g",))), "D", {"xe": T}, {"member": frozenset("ABCDEFG")}, {"xe"}),
    (EDGE, "the same for a reader with no row: the removal stands and cuts E's admission, and the admissions built on it "
           "with E's voice fall too (a silent colluder's old-head removal, for a reader with no row)",
     silent(0, lambda sg, fp: remove("xe", "E", ("A", "B"), ("g",))), None, {"xe": T},
     {"member": frozenset("ABCD")}, {"aF", "aG"}),
    (EDGE, "the silent colluder at n=8, for a reader with no row: A, B and X1..X8 remove C, ten of fifteen (the stated "
           "residual: a silent colluder's packing chain under one protocol)",
     silent(8, lambda sg, fp: remove("xr", "C", sg, ("aG", fp))), None, {"xr": T}, {}, set()),
    (SF, "the same read by D: the chain is behind D's line and leaves the fold, and the removal concludes nothing for D",
     silent(8, lambda sg, fp: remove("xr", "C", sg, ("aG", fp))), "D", {"xr": T}, {"member": frozenset("ABCDEFG")}, {"p1"}),
    # ---- the second review of 58b ----------------------------------------------------------------------------------
    (SF, "a void change cuts nothing in the roster: A, B and C remove E at aD, a sibling of aE, having signed aF: the "
         "removal is self-forked over the rows held, and E, F and G stay for a reader with no row",
     RD, None, {"f": T}, {"member": SEVEN}, {"f"}),
    (SF, "the same for D, an older reader", RD, "D", {"f": T}, {"member": SEVEN}, {"f"}),
    (SF, "the same for E, the key the void removal names", RD, "E", {"f": T}, {"member": SEVEN}, {"f"}),
    (SF, "a rescuer must have signed one chain only: C signed the honest admissions and cosigned the fork's second row "
         "(H, a founder, signed only the honest chain): the fork is void, and its keys are not listed",
     [G4, QA("aD", "D", ("A", "B", "C", "H"), ("g",)), QA("aE", "E", ("A", "B", "C", "H", "D"), ("aD",)),
      QA("p1", "X1", ("A", "B"), ("g",)), QA("p2", "X2", ("A", "B", "C", "X1"), ("p1",))], None, {"p1": T, "p2": T},
     {"member": frozenset("ABCDEH")}, {"p1", "p2"}),
    (EDGE, "a fork point with no member who signed only one chain (here C signed both, and every founder at g did), for "
           "a reader with no row: the tie keeps both, and the packers' removal of D stands",
     ROOM + [admit("p1", "X1", ("A", "B"), ("g",)), admit("p2", "X2", ("A", "B", "C", "X1"), ("p1",)),
             admit("p3", "X3", ("A", "B", "C", "X1", "X2"), ("p2",)), admit("p4", "X4", ("A", "B", "C", "X1", "X2", "X3"), ("p3",)),
             admit("p5", "X5", ("A", "B", "C", "X1", "X2", "X3", "X4"), ("p4",)),
             remove("xD", "D", ("A", "B", "C", "X1", "X2", "X3", "X4", "X5"), ("aG", "p5"))], None, {"xD": T},
     {"member": frozenset("ABCEFG") | {"X1", "X2", "X3", "X4", "X5"}}, set()),
    (SF, "the same read by D: the fork is behind D's line, and D keeps its seat",
     ROOM + [admit("p1", "X1", ("A", "B"), ("g",)), admit("p2", "X2", ("A", "B", "C", "X1"), ("p1",)),
             admit("p3", "X3", ("A", "B", "C", "X1", "X2"), ("p2",)), admit("p4", "X4", ("A", "B", "C", "X1", "X2", "X3"), ("p3",)),
             admit("p5", "X5", ("A", "B", "C", "X1", "X2", "X3", "X4"), ("p4",)),
             remove("xD", "D", ("A", "B", "C", "X1", "X2", "X3", "X4", "X5"), ("aG", "p5"))], "D", {"xD": T},
     {"member": SEVEN}, {"p1"}),
    # the lone holder's window, stated: a lone holder may add lone conferrals beside its first until the room's next
    # counted change; each is a row by one key that said two things at one head, and the two rows are the evidence a
    # recall cites (the members recall any duty holder, however seated, CC 4.5.13)
    (EDGE, "inside the window: A, the lone holder, confers moderate on B at aG and, as siblings, on C, D and E (each "
           "accepts): all four seat",
     ROOM + [conf("d1", "B", ("aG",), joins=False), ST.accept("kB", "B", "d1")] + [conf("z" + k, k, ("aG",), joins=False) for k in "CDE"]
     + [ST.accept("k" + k, k, "z" + k) for k in "CDE"], None, {"d1": T, "zC": T, "zD": T, "zE": T},
     {"moderate": frozenset("ABCDE")}, set()),
    (LO, "the window closes at the room's next counted change, by anyone: an ordinary admission built on B's conferral, "
         "B among its signers; A's further lone sibling at aG is then behind it for B",
     ROOM + [conf("oB", "B", ("aG",)), admit("aX", "X", tuple(sorted(SEVEN | {"B"})), ("oB",)), conf("oC", "C", ("aG",))], "B",
     {"oB": T, "aX": T, "oC": T}, {"moderate": {"A", "B"}}, {"oC"}),
    (LO, "the same read by D, who signed the admission: behind its line too",
     ROOM + [conf("oB", "B", ("aG",)), admit("aX", "X", tuple(sorted(SEVEN | {"B"})), ("oB",)), conf("oC", "C", ("aG",))], "D",
     {"oC": T}, {"moderate": {"A", "B"}}, {"oC"}),
    # a founder's seating is a regime of its own: two concurrent seatings of founders wait at their common members
    (SF, "two founders seated concurrently at g (f4 by one count, f5 by another): two regimes, so a count at both reads "
         "the common founders; f1 and f2 remove f3, two of three",
     [GI5[0], GI5[1], ST.offer("a5", "f1", "f5", "founder", OBJ, "group", ("g",), head=("g",), policy="cosigned_act",
                               cosigners=("f2", "f3", "f5")),
      IX("x", ("a4", "a5"), ("f1", "f2"))], None, {"a4": T, "a5": T, "x": T}, {}, set()),
    # ---- the edge: a count that omits an acceptance its signers have seen -----------------------------------------------
    (EDGE, "a count by three at the invitation that omits N's acceptance (its signers have seen it) and needs the smaller "
           "base: three of four is met. It is what they could do a moment before the acceptance arrived (the next case): "
           "the acceptance is no counted change and moves no head, so no rule tells the omission from not having seen it",
     WN + [ACN, invite("aP", "P", ("A", "B", "C"), ("oN",))], None, {"acN": T, "aP": T},
     {"member": FOUR | {"N"}}, set()),
    (EDGE, "the same count with no acceptance yet: the same answer",
     WN + [invite("aP", "P", ("A", "B", "C"), ("oN",))], None, {"aP": T}, {"member": FOUR}, set()),
    (EDGE, "the omitting count read by N, whose acceptance is its own acknowledgement (H6): the count names the newest "
           "counted change N acknowledged, so it is not behind N's line, and it stands for N too",
     WN + [ACN, invite("aP", "P", ("A", "B", "C"), ("oN",))], "N", {"acN": T, "aP": T},
     {"member": FOUR | {"N"}}, set()),
    # ---- the tips rule (the ruling of 2026-11-27): the fold, the self-fork void (S''), for a reader with no row too
    (H1, "the cheap tip and the removal by two at (tip, newest), for a reader with no row: the fork is self-forked (A "
         "and B acknowledged the newest admission it is behind), so it is void for the removal, which is two of seven",
     ROOM + [DC("dc", "B", ("g",)), remove("xg", "G", ("A", "B"), ("dc", "aG"))], None, {"dc": T, "xg": F},
     {"member": SEVEN}, {"dc"}),
    (H1, "the packed removal of D, for a reader with no row: the packing is self-forked and void for the removal",
     ROOM + [admit("p1", "X1", ("A", "B"), ("g",)), admit("p2", "X2", ("A", "B", "X1"), ("p1",)),
             remove("xd", "D", ("A", "B", "X1", "X2"), ("aG", "p2"))], None, {"p1": T, "p2": T, "xd": F},
     {"member": SEVEN}, {"p1", "p2"}),
]

# the reader's line over roster versions (checkpoint.versions, line::versions), on worlds of roster_fork's rule M
# (set-aside: a version may have in its past a version it does not extend). Each: (name, extends, past, roster of each
# version, the reader's acknowledged version, the versions that count, the roster of the tips).
VERSIONS = (
    ("a version extends the founding version with the acknowledged one in its past: a sibling of it, not behind (the "
     "line is sibling-safe)", ((), (0,), (0,)), ((), (0,), (0, 1)), ("0123", "012", "0124"), 1, {0, 1, 2}, "0124"),
    ("a version extends the founding version with the acknowledged one, which extends a later version, in its past: "
     "behind", ((), (0,), (1,), (0,)), ((), (0,), (0, 1), (0, 1, 2)), ("0123", "012", "012", "0124"), 2, {0, 1, 2}, "012"),
    ("the same, and a version over the one behind admits a member: built on it, behind too",
     ((), (0,), (1,), (0,), (3,)), ((), (0,), (0, 1), (0, 1, 2), (0, 1, 2, 3)), ("0123", "012", "012", "0124", "01245"), 2,
     {0, 1, 2}, "012"),
)
# the seat's line read directly (checkpoint.settle over concluded acts): an act with the acknowledged act in its past
# that names a head older than it. The rules above refuse such a row before the line reads it, so the line is read here
LINE = [G, admit("a1", "D", ("A", "B", "C"), ("g",)), admit("a1b", "E", ("A", "B", "C", "D"), ("a1",)),
        dict(admit("a2", "F", ("A", "B"), ("g",), ("a1b",)))]


def version_answer(E, past, ack):
    Tv, _ = CP.versions(list(range(len(E))), {i: E[i] for i in range(len(E))}, {i: set(past[i]) for i in range(len(E))},
                        lambda i: True, ack, False)
    return set(Tv)


def version_roster(past, R, Tv):
    covered = set().union(*[set(past[i]) for i in Tv]) if Tv else set()
    tips = [i for i in Tv if i not in covered]
    return "".join(sorted(set.intersection(*[set(R[i]) for i in tips]))) if tips else ""


def line_answer():
    S = CK.concluded(CK.kept(list(LINE) + [CK.row("ak", "ack", "R", ("a1b",), room=OBJ, head=("a1b",))]), lambda r, P, past: True)
    return frozenset(CP.void(S, CP.EVERY, "R"))


PLANTS = (("count_heads_unread", ST.MUT), ("all_heads_read", ST.MUT), ("head_any_row", ST.MUT), ("past_disjunct_off", ST.MUT),
          ("changes_any_object", ST.MUT), ("over_allowed", ST.MUT), ("authored_heads", ST.MUT), ("lone_exempt", ST.MUT),
          ("ends_at_heads_unread", ST.MUT), ("resign_exempt", ST.MUT), ("line_concurrent", CP.MUT), ("versions_concurrent", CP.MUT),
          ("cut_before_line", ST.MUT), ("line_void_unlisted", ST.MUT), ("acks_only", CP.MUT),
          ("line_not_sibling_safe", CP.MUT), ("election_exempt", ST.MUT),
          ("acceptance_unread", ST.MUT), ("acceptance_ends_unread", ST.MUT),
          ("lone_offer_unread", ST.MUT), ("lone_offer_same_scope", ST.MUT), ("fold_acceptance_unread", ST.MUT),
          ("heads_not_antichain", ST.MUT), ("window_opener_old_head", ST.MUT), ("lone_offer_self_path", ST.MUT),
          ("self_fork_unread", ST.MUT), ("rescue_unread", ST.MUT), ("tie_unread", ST.MUT), ("meet_tips", ST.MUT),
          ("regime_before_change", ST.MUT), ("reader_exclusion_unread", ST.MUT),           ("ack_unvoids", CP.MUT), ("void_cuts_in_roster", ST.MUT), ("rescuer_signed_both", ST.MUT),
          ("regime_protocol_only", ST.MUT))
# retired with the ruling of 2026-11-27: ack_excuses_none (H7, subsumed by the self-fork void), ack_reads_void (a
# counted row's own void is in the roster's S'' void, which holds every row), and line_after_cut (the
# line's first pass reads every row as counting; with the line sibling-safe and the reader's rows concluded again for
# it, no case here tells a first pass over the cut from one over every row)


import contextlib  # noqa: E402


@contextlib.contextmanager
def setting(rule):
    """H3's cases run with the act-to-policy binding off: the binding has no act for a self-admission (the acts
    table names none), so in the reference with it on a self-admission concludes nothing at all and H3 has nothing
    to read. The crate's own cases (tests/fold.rs) read H3 under the self-admit policy."""
    on = rule in (H3, SFB) and "binding_off" not in ST.MUT
    if on: ST.MUT.add("binding_off")
    try:
        yield
    finally:
        if on: ST.MUT.discard("binding_off")


def answer(S, own, concl, holds):
    Q = ST.Seats(S, own=own)
    return ({i: bool(S.C.get(i)) for i in concl}, {sc: frozenset(Q.holders(sc, OBJ)) for sc in holds}, frozenset(Q.stale))


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


def want(concl, holds, stale):
    return (dict(concl), {sc: frozenset(v) for sc, v in holds.items()}, frozenset(stale))


def read_case(rule, rows, own, concl, holds, arrive=None):
    with setting(rule):
        S = CK.arrive([rows[0]] + arrive, RULE) if arrive is not None else CK.concluded(CK.kept(list(rows)), RULE)
        return answer(S, own, concl, holds)


# a window's opening names the newest counted changes in its own past and is counted there (H1; the review of 58b):
# A opens ballot@once; A and B for, D to G against. (name, the opening's heads, the outcome under recount)
WINDOW = (("an opening at the newest admission: the seven decide it", ("aG",), "open"),
          ("an opening at the founding head naming the newest admission: it concludes nothing", ("g",), "none"))


def window_answer(heads):
    import window as WN
    p = WN.opener("p", "A", "ballot@once", OBJ, heads, names=("aG",))
    rows = ROOM + [p] + [WN.answer("v" + k, k, "p", "for") for k in "AB"] + [WN.answer("v" + k, k, "p", "against") for k in "DEFG"]
    return WN.outcome(CK.concluded(CK.kept(rows), WN.rule), "p", "recount")


def run_all():
    return [read_case(rule, rows, own, concl, holds) for rule, _, rows, own, concl, holds, _ in CASES] + \
        [(version_answer(E, past, a), version_roster(past, R, version_answer(E, past, a))) for _, E, past, R, a, *_ in VERSIONS] + \
        [line_answer()] + [window_answer(h) for _, h, _ in WINDOW]


def main():
    problems, n = [], 0
    for rule, name, rows, own, concl, holds, stale in CASES:
        got = read_case(rule, rows, own, concl, holds)
        if got != want(concl, holds, stale):
            problems.append("%s %s: got %s" % (rule, name, got))
        for p in orders(rows):
            n += 1
            if read_case(rule, rows, own, concl, holds, p) != got:
                problems.append("%s: order %s differs" % (name, [r["id"] for r in p]))
                break
    for name, E, past, R, a, want_t, want_r in VERSIONS:
        t = version_answer(E, past, a)
        if (t, version_roster(past, R, t)) != (want_t, want_r):
            problems.append("H5 %s: got %s, roster %s" % (name, t, version_roster(past, R, t)))
    if line_answer() != frozenset({"a2"}):
        problems.append("H5 the seat's line read directly: void %s" % sorted(line_answer()))
    for name, h, w in WINDOW:
        if window_answer(h) != w:
            problems.append("H1 window: %s: got %s" % (name, window_answer(h)))
    labels = ["%s %s" % (c[0], c[1]) for c in CASES] + ["H5 " + v[0] for v in VERSIONS] + ["H5 the seat's line read directly"] + \
        ["H1 window: " + w[0] for w in WINDOW]
    now, caught = run_all(), 0
    for p, m in PLANTS:
        m.add(p)
        try:
            hit = [lab for lab, a, b in zip(labels, now, run_all()) if a != b]
        finally:
            m.discard(p)
        caught += bool(hit)
        print("  plant %-22s %s" % (p, "caught by: %s" % hit[0][:120] if hit else "NOT CAUGHT"))
        if not hit:
            problems.append("plant %s not caught" % p)
    for p in problems:
        print(p)
    print("RESULT: %s: %d cases (%d EDGE), %d of roster versions, the line read directly, %d arrival orders, %d of %d planted "
          "breaks caught" % ("ok" if not problems else "%d problems" % len(problems), len(CASES),
                             sum(c[0] == EDGE for c in CASES), len(VERSIONS), n, caught, len(PLANTS)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
