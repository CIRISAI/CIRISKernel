#!/usr/bin/env python3
"""
check_count_heads.py: the heads of a count, and the reader's line (the heads ruling of 2026-11-26, H1 to H8).

    H1  A count is read at the NEWEST of the heads it names (one in another named head's past is dropped), each a
        counted change over the row's own object or its founding row, and they must be exactly the newest counted
        changes over that object in the row's own past (seat.newer_head_in_past). Concurrent tips are intersected.
    H2  No `over`: a counted row is counted over its own object, and one stating another concludes nothing.
    H3  (retired with the open:self_admit cut, Eric for 1.0: a self-admission, the one head a single key wrote, is no
        row any room may make, so H3 has nothing left to read)
    H4  No exemption: every row that changes a roster names the newest counted changes over its object in its own
        past or concludes nothing: a moderator's lone removal (whose signer holds `moderate` at those heads, less a
        laying down of it in the removal's past), a resignation (a withdrawal of a seat over a
        room, among the rows it names), a lift (counted at the head its act names).
    H5  The text's reader's line: no test of concurrency (checkpoint.settle, checkpoint.versions); the line is read
        before the cut (seat.Seats).
    H6  A reader's own signed rows are its acknowledgements: every concluded row it signed or cosigned over the object
        (checkpoint.acknowledgements), each acknowledging the counted acts in its own past.
    H7  Retired (the tips ruling of 2026-11-27): the self-fork void (SF, below) subsumes it; its cases now read under
        that rule.
    H8  No caller-synthesised heads: a row of no object, a note, a cosignature naming itself is no head of a count.
    R5  CC 2.7.7 rule 5 for every counted act (item 13 (b), ruled R2): a voice of a key concurrent with a counted
        removal of that key is not in force from the head the removal names, on any counted act (seat.contested_out):
        contested where each needs a voice the other ends, the dependent one falling where one-sided; only a removal
        in force and not void takes a voice, and none that has the act in its past or sits at a newer head.
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
a counted change all of whose counted voices acknowledged a change it is behind is self-forked, and void for the
counting row by T at its fork point (S'': where the members seated at its heads who signed only the other side
outnumber those who signed only its side; equal, none on either side included, neither is void, so depth decides
nothing; a key's own acceptance, or its yes on a change seating it, counts it for neither side; a member that has since
left still counts by what it signed while seated), the ONLY automatic effect of a key signing
two things outside an election, and it voids a change, never a key; a protocol-change tip is under its new protocol;
the changes void for the reader leave a row's fold and heads too; and the line is sibling-safe (a change is behind an
acknowledged change only where every head it names is strictly in the past of that change's own heads).

Each case is read as one batch and in arrival orders of its rows (every order up to six rows above the founding one,
else the batch order, its reverse and forty shuffles). A case marked EDGE states what the rules give at the stated
residual: ONE residual, in three shapes, each only for a reader with no row of its own (a member is never such a
reader, by H6): (1) no member seated at the fork point signed exactly one chain (a room founded by one key; every
founder colluding); (2) a silent colluder's packing chain under the same protocol; (3) a newcomer admitted on the fork, which
takes its past from its admitter (CC 3.3.4). Marked EDGE beside it: a count that omits an acceptance its signers have
seen (it does only what they could do a moment before the acceptance arrived), and the lone holder's window.
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


def elect(i, k, heads, vac=("lm",)):
    """An election's seating of k to `moderate` (election2's C1 to C5, merged): ballots of B and C ranking k first,
    each naming its election (the founding row, `of`) and the vacancy end `vac`; the seating signed by k itself, `to`
    k, `of` the founding row, naming its set (the ballots and the end) and its heads, which place it (H4)."""
    bs = [ST.R("b" + v + i, "ballot", v, tuple(vac), ranking=(k, "C"), of="g") for v in ("B", "C")]
    return bs + [ST.offer(i, k, k, "moderate", OBJ, "group", tuple(b["id"] for b in bs) + tuple(vac) + tuple(heads),
                          head=tuple(heads), policy="moderator_election", of="g")]


R5 = "rule 5, every act"
H1, H2, H3, H4, H5, H6, H7, H8, EL, AC, LO, SF, EDGE = ("H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8", "election",
                                                       "acceptance", "lone offer", "self-fork", "EDGE")
SFB = "self-fork (binding off: the removal states `majority`)"


def conf(i, to, heads, cites=(), scope="moderate", signers=("A",), joins=True):
    """A duty conferral counted over the duty holders (`duty_confer`), signed by `signers` (A, the room's lone holder,
    by default); `joins`: each key it seats signs it too (its own yes), else its own acceptance completes the seat."""
    to = (to,) if isinstance(to, str) else tuple(to)
    return ST.offer(i, signers[0], to, scope, OBJ, "group", tuple(heads) + tuple(cites), head=tuple(heads),
                    policy="duty_confer", counted="duty", cosigners=tuple(signers[1:]) + (to if joins else ()))


# an infrastructure room on the founder-scope shape (CC 3.1.3.2, 3.2): f1, f2 and f3 found it in scope `founder`
# under quorum:2/3, entrenched; founders' amendments seat f4 (restating 3/4) and then f5 (restating 3/5), each counted
# at the present M and signed by the key it seats
GI5 = [ST.offer("g", "f1", ("f1", "f2", "f3"), "founder", "@", "self", cosigners=("f2", "f3"), cohort_subkind="infrastructure",
                consensus_protocol="quorum:2/3", consensus_protocol_entrenched=True),
       ST.offer("a4", "f1", "f4", "record", OBJ, "group", ("g",), head=("g",), counted="founder", role="founder",
                cosigners=("f2", "f4"), consensus_protocol="quorum:3/4", consensus_protocol_entrenched=True),
       ST.offer("a5", "f1", "f5", "record", OBJ, "group", ("a4",), head=("a4",), counted="founder", role="founder",
                cosigners=("f2", "f3", "f5"), consensus_protocol="quorum:3/5", consensus_protocol_entrenched=True)]
FIVE_F = frozenset(("f1", "f2", "f3", "f4", "f5"))
IX = lambda i, heads, signers, cites=(): ST.unseat(i, signers[0], "f3", "founder", OBJ, "group", tuple(heads) + tuple(cites),
                                                   head=tuple(heads), counted="founder", cosigners=tuple(signers[1:]))


# a room under quorum:2/3 (L'; any two admit: the closed protocol set has no one-voice word): A, B and C found it
GQ = ST.found("g", "A", ("A", "B", "C"), {"moderate": ("A",)}, cosigners=("B", "C"), consensus_protocol="quorum:2/3")
QA = lambda i, k, sg, heads, cites=(): ST.offer(i, sg[0], k, "member", OBJ, "group", tuple(heads) + tuple(cites), head=tuple(heads),
                                                 policy="cosigned_act", cosigners=tuple(sg[1:]) + (k,))
QR = lambda i, k, sg, heads, cites=(): ST.unseat(i, sg[0], k, "member", OBJ, "group", tuple(heads) + tuple(cites),
                                                  head=tuple(heads), policy="community_remove", cosigners=tuple(sg[1:]))
QDC = ST.offer("dc", "A", "B", "moderate", OBJ, "group", ("g",), head=("g",), policy="duty_confer", counted="duty", cosigners=("B",))


def lprime(aD_by, aE_by):
    """L': the honest chain's first change signed by aD_by, then the honest C, D, E.. on top; A and B fork at g."""
    return [GQ, QA("aD", "D", aD_by, ("g",)), QA("aE", "E", aE_by, ("aD",)), QA("aF", "F", ("C", "D", "E"), ("aE",)),
            QA("aG", "G", ("C", "D", "E", "F"), ("aF",)), QDC, QA("xd", "X", ("A", "B"), ("dc",))]


# the protocol raised after g: a room under quorum:2/6 founded by A..F; the honest C..F admit G and raise it to majority;
# A and B (who signed nothing of it) pack X1..Xn from g under the old protocol
GQ6 = ST.found("g", "A", tuple("ABCDEF"), {"moderate": ("A",)}, cosigners=tuple("BCDEF"), consensus_protocol="quorum:2/6")
def raised(n, row):
    rows = [GQ6, QA("ag2", "G", ("C", "D", "E", "F"), ("g",)),
            ST.offer("amq", "C", (), "record", OBJ, "group", ("ag2",), head=("ag2",),
                     consensus_protocol="majority", cosigners=("D", "E", "F", "G"))]
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


# the second review of 58b: a void change cuts nothing in a reader's roster (rd); a key that signed both chains is in
# neither side of T
G4 = ST.found("g", "A", ("A", "B", "C", "H"), {"moderate": ("A",)}, cosigners=("B", "C", "H"), consensus_protocol="quorum:2/4")
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


# the residual (1) chain: A and B fork at g, and A, B and C (every founder) build five admissions on it
PACK = [admit("p1", "X1", ("A", "B"), ("g",)), admit("p2", "X2", ("A", "B", "C", "X1"), ("p1",)),
        admit("p3", "X3", ("A", "B", "C", "X1", "X2"), ("p2",)), admit("p4", "X4", ("A", "B", "C", "X1", "X2", "X3"), ("p3",)),
        admit("p5", "X5", ("A", "B", "C", "X1", "X2", "X3", "X4"), ("p4",))]


# T at the fork point: HC (A..D admit E at aD; on another device, H at aD and J at c1), HC4 (the same by A, B and C
# alone), HC6 (HC4's c1 and c2 written after aK and xD), PK8 (A and B pack X1..X8 from g)
_aD = admit("aD", "D", ("A", "B", "C"), ("g",))
HC = [G, _aD, admit("aE", "E", ("A", "B", "C", "D"), ("aD",)), admit("c1", "H", ("A", "B", "C", "D"), ("aD",)),
      admit("c2", "J", ("A", "B", "C", "D", "H"), ("c1",))]
_c34 = [admit("c1", "H", ("A", "B", "C"), ("aD",)), admit("c2", "J", ("A", "B", "C", "H"), ("c1",))]
HC4 = [G, _aD, admit("aE", "E", ("A", "B", "C"), ("aD",))] + _c34
HC6 = [G, _aD, admit("aE", "E", ("A", "B", "C"), ("aD",)), admit("aK", "K", ("A", "B", "C", "E"), ("aE",)),
       remove("xD", "D", ("A", "B", "C", "E", "K"), ("aK",))] + _c34
PK8, _m, _pv = [], ["A", "B"], "g"
for _i in range(1, 9):
    PK8.append(admit("p%d" % _i, "X%d" % _i, tuple(_m), (_pv,))); _m.append("X%d" % _i); _pv = "p%d" % _i
PK8S = tuple(_m)

# the window's closers (the third attack's wc.py): A, the lone holder, confers moderate on B at aG (d1, B accepts); the
# siblings zC..zE (A alone, at aG, each accepted) are written after the closer and do not name it; wb (A, C, D and E)
# withdraws B's seat naming the siblings. The window is closed for a reader by any later counted change that reader has
# acknowledged, and for every reader once the lone holder itself signs a later change; a concurrent change closes nothing
_WDC = lambda i, to, heads=("aG",): ST.offer(i, "A", to, "moderate", OBJ, "group", tuple(heads), head=tuple(heads),
                                             policy="duty_confer", counted="duty", cosigners=())
WSIB = [_WDC("z" + k, k) for k in "CDE"] + [ST.accept("k" + k, k, "z" + k) for k in "CDE"]
WBASE = ROOM + [_WDC("d1", "B"), ST.accept("kB", "B", "d1")]
WWB = ST.unseat("wb", "A", "B", "moderate", OBJ, "group", ("d1", "zC", "zD", "zE", "kB", "kC", "kD", "kE"),
                head=("d1", "zC", "zD", "zE"), policy="duty_withdraw", counted="duty", cosigners=("C", "D", "E"))
WCL = {"none": [],
       "concurrent": [admit("c", "H", ("B", "C", "D", "E", "F"), ("aG",))],
       "notA": [admit("c", "H", ("B", "C", "D", "E", "F"), ("d1",), ("kB",))],
       "AB": [ST.offer("c", "A", "F", "moderate", OBJ, "group", ("d1", "kB"), head=("d1",), policy="duty_confer",
                       counted="duty", cosigners=("B",)), ST.accept("kF", "F", "c")],
       "A5": [admit("c", "H", ("A", "B", "C", "D", "E"), ("d1",), ("kB",))]}
WC = lambda n: WBASE + WCL[n] + WSIB + [WWB]
# the fourth attack's wt.py: the closer by A and B, the siblings, and C, D and E posting on the siblings' side (WT2)
# or withdrawing B's seat (WT3), honest F and G posting after the closer (WT4)
WT1 = WBASE + WCL["AB"] + WSIB
WPOSTS = [CK.row("q" + k, "post", k, ("zC", "zD", "zE"), room=OBJ) for k in "CDE"]
WHON = [CK.row("h" + k, "post", k, ("c",), room=OBJ) for k in "FG"]

# the fourth attack's rc.py: A, B and C found; D, F and G admitted (six at aG); A, B, C and D admit E at aG (4 of 6).
# F posts at aG, concurrently (fp); c1 (A, B, C and D admit H at aG) and c2 (J at c1) are written without aE
_rD = admit("aD", "D", ("A", "B", "C"), ("g",))
_rF = admit("aF", "F", ("A", "B", "C", "D"), ("aD",))
_rG = admit("aG", "G", ("A", "B", "C", "D", "F"), ("aF",))
RCB = [G, _rD, _rF, _rG, admit("aE", "E", ("A", "B", "C", "D"), ("aG",))]
RFP = CK.row("fp", "post", "F", ("aG",), room=OBJ)
RC1_ = admit("c1", "H", ("A", "B", "C", "D"), ("aG",))
RC1P = admit("c1", "H", ("A", "B", "C", "D"), ("aG",), ("fp",))
RC2_ = admit("c2", "J", ("A", "B", "C", "D", "H"), ("c1",))
RCQ = admit("cq", "Q", ("B", "C", "D", "F", "G"), ("aG",))       # RC7: B, C, D, F and G admit Q at aG, honestly
RC7 = RCB + [RCQ, admit("c1", "H", ("A", "B", "C", "D", "Q"), ("cq",)), admit("c2", "J", ("A", "B", "C", "D", "H", "Q"), ("c1",))]
RC7G = RCB + [RCQ, admit("c1", "H", ("A", "B", "C", "Q", "F"), ("cq",)), ack("kd", "D", "aE")]
# BN: the founders give A moderate and B review; A confers moderate on B at g with B's yes (B holds a duty at g, so
# only the beneficiary rule takes B's yes out of T's count); A and B then admit D and E without it
GBN = ST.found("g", "A", ("A", "B", "C"), {"moderate": ("A",), "review": ("B",)}, cosigners=("B", "C"))
BN = [GBN, admit("aD", "D", ("A", "B"), ("g",)), admit("aE", "E", ("A", "B", "D"), ("aD",)), conf("cf", "B", ("g",))]


# item 13: a room of four (A, B, C, and D admitted), the takedown at aD, and two later versions
SV = [G, admit("aD", "D", ("A", "B", "C"), ("g",)),
      ST.unseat("tk", "B", "A", "moderate", OBJ, "group", ("aD",), head=("aD",), policy="moderator_recall",
                cosigners=("C", "D")),
      admit("v1", "Y", ("A", "B", "D"), ("aD",)), admit("v2", "X", ("A", "B", "D", "Y"), ("v1",))]


# item 13 (b): a room of four (A, B, C, and D admitted); tk the admission of Z by B, C and D at aD; V1B C's removal at aD
TB = [G, admit("aD", "D", ("A", "B", "C"), ("g",))]
TKB = admit("tk", "Z", ("B", "C", "D"), ("aD",))
V1B = remove("v1", "C", ("A", "B", "D"), ("aD",))
# the room of five with a contested pair (v1 removes C, v2 removes D, each needing a voice the other ends), and the
# count naming both that settles it by removing C
TP5 = TB + [admit("aE", "E", ("A", "B", "C", "D"), ("aD",)), remove("v1", "C", ("A", "B", "D"), ("aE",)),
            remove("v2", "D", ("A", "B", "C"), ("aE",))]
SP5 = remove("s", "C", ("A", "B", "D", "E"), ("v1", "v2"))


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
         "newcomers, and four of the eight others is short (the member removed is not counted)",
     ROOM + [admit("aX", "X", FIVE, ("aG",)), admit("aY", "Y", FIVE, ("aG",)), remove("xg", "G", FIVE[:4], ("aX", "aY"))], None,
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
     GI5 + [IX("x", ("g",), ("f1", "f2"), ("a5",))], None, {"a4": T, "a5": T, "x": F}, {"founder": FIVE_F}, set()),
    (H1, "infrastructure: the same removal naming both the current head a5 and the old head g: the named heads are no "
         "antichain (g is in a5's past), and it concludes nothing",
     GI5 + [IX("x", ("a5", "g"), ("f1", "f2"))], None, {"x": F}, {"founder": FIVE_F}, set()),
    (H1, "infrastructure: four of the five naming a5 and g: met at a5, and still refused, the named heads no antichain",
     GI5 + [IX("x", ("a5", "g"), ("f1", "f2", "f4", "f5"))], None, {"x": F}, {"founder": FIVE_F}, set()),
    (H1, "infrastructure: four of the five at a5 alone: it concludes",
     GI5 + [IX("x", ("a5",), ("f1", "f2", "f4", "f5"))], None, {"x": T}, {}, set()),
    # ---- H2 ---------------------------------------------------------------------------------------------------------
    (H2, "an admission in a second room stating that it is counted over the first room's roster",
     ROOM + [ST.found("h", "A", ("A",), {}),
             ST.offer("ox", "A", "X", "member", "h", "group", ("h", "aG"), head=("h",), over="g", policy="community_invite",
                      cosigners=("X",))], None, {"ox": F}, {}, set()),
    # ---- H4 ---------------------------------------------------------------------------------------------------------
    (H4, "a moderator's lone removal of an agent's key at its seat's head, with a later admission in its own past",
     WM + [LONE("xl", ("md",), ("an",))], None, {"xl": F}, {"member": {"m1", "m2", "MOD", "N"}, "agent": {"AG"}}, set()),
    (H4, "the same lone removal at the newest head",
     WM + [LONE("xl", ("an",))], None, {"xl": T}, {"member": {"m1", "m2", "MOD", "N"}, "agent": set()}, set()),
    (H4, "a moderator lays its seat down and then removes an agent's key alone at the newest head",
     WM + [WMD, LONE("xl", ("an",), ("wd",))], None, {"wd": T, "xl": F}, {"moderate": {"m1"}, "agent": {"AG"}}, set()),
    (H4, "the same removal concurrent with the moderator's laying down: it concludes",
     WM + [WMD, LONE("xl", ("an",))], None, {"wd": T, "xl": T}, {"moderate": {"m1"}}, set()),
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
    # ---- H5, the superseded version (persist's item 13 (a)): the room's roster versions play the bundle versions, and
    # a counted takedown (B, C and D's recall of A's `moderate`, three of four) is at version aD; v1 (Y admitted at aD)
    # and v2 (X admitted at v1) are later versions. No voice of the takedown is dropped (that is (b), held for a ruling)
    (H5, "item 13 (a): a counted takedown at an older version, two versions behind the one a reader acknowledged "
         "(v2, built on v1, built on the takedown's own head): void for that reader, and A keeps the seat",
     SV + [ack("ak", "R", "v2")], "R", {"tk": T, "v1": T, "v2": T}, {"moderate": {"A"}}, {"tk"}),
    (H5, "item 13 (a): the same rows for a reader with no row: the takedown stands, and the seat is ended",
     SV, None, {"tk": T, "v1": T, "v2": T}, {"moderate": set()}, set()),
    (H5, "item 13 (a): the same rows for Y, which signed v2 (its own rows are its acknowledgements, H6): void for it",
     SV, "Y", {"tk": T, "v1": T, "v2": T}, {"moderate": {"A"}}, {"tk"}),
    (H5, "item 13 (a), the sibling: a reader acknowledged v1, the version right after the takedown's own head. The "
         "takedown is v1's sibling, not behind it (the line is sibling-safe, the ruling of 2026-11-27): it stands for "
         "that reader, and the seat is ended",
     SV + [ack("ak", "R", "v1")], "R", {"tk": T, "v1": T, "v2": T}, {"moderate": set()}, set()),
    # ---- rule 5 for every counted act (item 13 (b), ruled R2): a voice of a key concurrent with a counted removal of
    # that key is not in force from the head the removal names. tk, standing in for the takedown notice, is a counted
    # act that is no removal: the admission of Z at aD by B, C and D (three of four, C's voice needed)
    (R5, "item 13 (b): v1, the version that drops C, is C's counted removal at aD, concurrent with tk: C's voice on tk "
         "is not in force from aD on, so tk falls (two of four) and v1 stands: Z is not seated, C is out",
     TB + [V1B, TKB], None, {"tk": T, "v1": T}, {"member": {"A", "B", "D"}}, set()),
    (R5, "item 13 (b), mutual: in a room of five, v1 removes C (A, B and D) and tk is itself a removal, of D (A, B and "
         "C): each needs a voice the other ends, so they are contested and neither counts: nobody is removed",
     TB + [admit("aE", "E", ("A", "B", "C", "D"), ("aD",)), remove("v1", "C", ("A", "B", "D"), ("aE",)),
           remove("tk", "D", ("A", "B", "C"), ("aE",))], None, {"tk": T, "v1": T}, {"member": set("ABCDE")}, set()),
    (R5, "item 13 (b): a contested removal takes nothing: in the room of five, the two removals contest each other, "
         "and tk (Z admitted by A, C, D and E at aE, four of five, needing both C and D) stands: Z is seated",
     TB + [admit("aE", "E", ("A", "B", "C", "D"), ("aD",)), remove("v1", "C", ("A", "B", "D"), ("aE",)),
           remove("v2", "D", ("A", "B", "C"), ("aE",)), admit("tk", "Z", ("A", "C", "D", "E"), ("aE",))], None,
     {"tk": T, "v1": T, "v2": T}, {"member": set("ABCDEZ")}, set()),
    (R5, "item 13 (b), the settled pair: the two contested removals of the room of five, and an act at their two "
         "heads (Z admitted by A, B, C and E, four of five, C's voice needed): the contested rows never reach it, and "
         "it stands", TP5 + [admit("tk", "Z", ("A", "B", "C", "E"), ("v1", "v2"))], None,
     {"tk": T, "v1": T, "v2": T}, {"member": set("ABCDEZ")}, set()),
    (R5, "item 13 (b), the settled pair: a count naming both (s, by A, B, D and E) settles it by removing C; the same "
         "act, concurrent with s and at s's own heads, is judged by s like any other act: C's voice is not in force "
         "from those heads on, and the act falls: C is out, Z is not seated",
     TP5 + [SP5, admit("tk", "Z", ("A", "B", "C", "E"), ("v1", "v2"))], None,
     {"tk": T, "v1": T, "v2": T, "s": T}, {"member": set("ABDE")}, set()),
    (R5, "item 13 (b), the settled pair: an act with the settling removal in its past (Z admitted by A, B, D and E at "
         "s): it stands", TP5 + [SP5, admit("tk", "Z", ("A", "B", "D", "E"), ("s",))], None,
     {"tk": T, "v1": T, "v2": T, "s": T}, {"member": set("ABDEZ")}, set()),
    (R5, "item 13 (b): the removal at a newer head than the act (E admitted at aD, C removed at aE): C stood at tk's "
         "own head, so its voice counts there and tk stands: Z is seated, C is out",
     TB + [admit("aE", "E", ("A", "B", "D"), ("aD",)), remove("v1", "C", ("A", "B", "D", "E"), ("aE",)), TKB], None,
     {"tk": T, "v1": T, "aE": T}, {"member": set("ABDEZ")}, set()),
    (R5, "item 13 (b): the removal with the act in its own past (v1 at tk): the voice counted before the end, and tk "
         "stands", TB + [TKB, remove("v1", "C", ("A", "B", "D"), ("tk",))], None, {"tk": T, "v1": T},
     {"member": set("ABDZ")}, set()),
    (R5, "item 13 (b): a void removal takes nothing: v1 removes C at the founding head (A and B, two of three), "
         "concurrent with aD and tk; for a reader that acknowledged tk it is behind the line, so tk stands for it and C "
         "stays", TB + [remove("v1", "C", ("A", "B"), ("g",)), TKB, ack("ak", "R", "tk")], "R",
     {"tk": T, "v1": T}, {"member": set("ABCDZ")}, {"v1"}),
    (R5, "item 13 (b): the same removal for a reader with no row: it counts and is not void, so tk falls by it",
     TB + [remove("v1", "C", ("A", "B"), ("g",)), TKB], None, {"tk": T, "v1": T}, {"member": {"A", "B", "D"}}, set()),
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
    (H7, "a row built on the cheap tip, signed on that side only by A and by the keys it seats (B's yes on dc, C's on "
         "dc2): the beneficiary of a change is no evidence for it, so by T the cheap tip is void (C signed only the honest "
         "chain), and the honest removal by five at aG concludes without naming it",
     ROOM + [DC("dc", "B", ("g",)), ST.offer("dc2", "A", "C", "moderate", OBJ, "group", ("dc",), head=("dc",), policy="duty_confer",
                                             counted="duty", cosigners=("B", "C")), remove("xg", "G", FIVE, ("aG",), ("dc2",))], None,
     {"dc": T, "dc2": T, "xg": T}, {"member": SEVEN - {"G"}}, {"dc", "dc2"}),
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
         "is sibling-safe), and at the two tips the fold seats D (an election's seating is read by C1 to C5, not counted "
         "as a plain count: election2's fold, merged)",
     ROOM + [admit("aH", "H", tuple(sorted(SEVEN)), ("aG",)), ack("ak", "R", "aH"),
             ST.withdraw("lm", "A", "g", ("g", "aG"), scope="moderate")] + elect("se", "D", ("aG",)), "R",
     {"se": T}, {"moderate": {"D"}}, set()),
    # restated at the batch merge (the Constitution's ruling on H4, 2026-11-27): the lay-down lm the seating reads as its
    # vacancy, at aG, is itself a roster change behind this reader's line, so it is no vacancy end for the reader, and
    # for it the seating concludes nothing at all (no longer a concluded act its line voids: stale is empty)
    (EL, "the seating at the head before an admission built on a later one the reader acknowledged: its vacancy end, "
         "the lay-down at the same head, is behind that reader's line (a lay-down is a roster change, H4), so for that "
         "reader the seating reads no vacancy and seats nobody",
     ROOM + [admit("aH", "H", tuple(sorted(SEVEN)), ("aG",)), admit("aI", "I", tuple(sorted(SEVEN | {"H"})), ("aH",)),
             ack("ak", "R", "aI"), ST.withdraw("lm", "A", "g", ("g", "aG"), scope="moderate")] + elect("se", "D", ("aG",)), "R",
     {"se": T}, {"moderate": set()}, set()),
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
         "signed the count, which oN is behind (a sibling they built past): oN is self-forked, but the same four signed "
         "both sides, so T is a tie (honest concurrency): oN stands and N is seated",
     WN[:2] + [invite("oN", "N", ("A", "B", "C", "D"), ("aD",)), invite("oM", "M", ("A", "B", "C", "D"), ("aD",)),
               ST.accept("acM", "M", "oM"), ST.accept("acN", "N", "oN"),
               invite("aP", "P", ("A", "B", "C", "D"), ("oM",), ("acM",))], None, {"aP": T},
     {"member": FOUR | {"M", "N"}}, set()),
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
    # ---- S'': the self-fork void, read by T at the fork point (the ruling of 2026-11-27; T, the third attack). This is the ONLY automatic effect of
    # a key signing two things outside an election, and it voids a change, never a key --------------------------------
    (SFB, "L': the honest chain's first change signed only by A and B, then C, D and the newcomers on it; A and B fork at "
         "g: aD is self-forked, and T keeps it (C, a member at g, signed only the honest chain): C..G remove A, five of the eight the fold seats",
     lprime(("A", "B"), ("C", "D")) + [dict(QR("xa", "A", ("C", "D", "E", "F", "G"), ("xd", "aG")), policy="majority")], None, {"xa": T},
     {"member": frozenset("BCDEFGX")}, set()),
    (SFB, "L' with A and B on aE too: the fork is self-forked and void by T (C signed only the honest chain), and the "
         "removal, a merge of both lines naming xd, reads its count without it",
     lprime(("A", "B"), ("A", "B", "C", "D")) + [dict(QR("xa", "A", ("C", "D", "E", "F", "G"), ("xd", "aG")), policy="majority")], None, {"xa": T},
     {"member": frozenset("BCDEFG")}, {"dc", "xd"}),
    (SF, "S'' against itself: A and B sign two chains at g, each first row behind the other's second; no single-chain "
         "member on either side: both are kept, and A, B and C admitting Z at both tips is a count over the fold",
     [G, admit("q1", "D", ("A", "B"), ("g",)), admit("q2", "X", ("A", "B"), ("g",)), admit("q1b", "E", ("A", "B", "D"), ("q1",)),
      admit("q2b", "Y", ("A", "B", "X"), ("q2",)), admit("rz", "Z", ("A", "B", "C", "D", "E", "X", "Y"), ("q1b", "q2b"))], None,
     {"rz": T}, {"member": frozenset("ABCDEXYZ")}, set()),
    (SF, "the protocol raised after g: A and B, who signed nothing of the honest line, pack X1 and X2 from g under the "
         "old protocol: a tip that is the protocol change is under its new protocol, so the tips are two regimes and fold "
         "to their common keys; C, D, E and F remove A (four of the six others there; of the eight the union holds, short)",
     raised(2, lambda sg, heads: ST.unseat("xa", "C", "A", "member", OBJ, "group", heads, head=heads, policy="community_remove",
                                           cosigners=("D", "E", "F"))), None, {"xa": T}, {}, set()),
    (SF, "the same: the packers A, B, X1, X2 remove C, and conclude nothing",
     raised(2, lambda sg, heads: ST.unseat("xc", "A", "C", "member", OBJ, "group", heads, head=heads, policy="community_remove",
                                           cosigners=sg[1:])), None, {"xc": F}, {}, set()),
    (SF, "the silent colluder: A signs the honest admissions with C, B signs nothing after g, and A and B chain X1 and X2 "
         "from g. Nothing is self-forked (B acknowledged nothing the chain is behind): for a reader with no row, C..G's "
         "removal of A by C, D, E and F is four of the eight others and short (the member removed is not counted)",
     silent(2, lambda sg, fp: remove("xr", "A", tuple("CDEF"), ("aG", fp))), None, {"xr": F},
     {"member": frozenset("ABCDEFG") | {"X1", "X2"}}, set()),
    (SF, "the same read by D: X1's admission is behind D's line, so it and the chain on it leave the removal's fold for D "
         "(the reader-line exclusion): the removal concludes for D, and A is out of D's roster",
     silent(2, lambda sg, fp: remove("xr", "A", tuple("CDEF"), ("aG", fp))), "D", {"xr": F},
     {"member": frozenset("BCDEFG")}, {"p1"}),
    (SF, "acknowledging never un-voids: the same rows read by C, whose own honest removal names p2 as a head (H1 asks it, "
         "it has seen p2): the chain stays behind C's line, and is no part of C's roster",
     silent(2, lambda sg, fp: remove("xr", "A", tuple("CDEF"), ("aG", fp))), "C", {"xr": F},
     {"member": frozenset("BCDEFG")}, {"p1"}),
    (SF, "both ways: D's removal at aG alone (a client that does not build on a change void for it): concurrent with p1, "
         "no self-fork, and for D the same count as the removal naming p2: it concludes, and A is out",
     silent(2, lambda sg, fp: remove("xr", "A", tuple("CDEFG"), ("aG",))), "D", {"xr": T},
     {"member": frozenset("BCDEFG")}, {"p1"}),
    (EDGE, "residual (2): both ways, for a reader with no row: the removal at aG alone concludes (five of seven), the one naming p2 is "
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
    (EDGE, "residual (2): the same for a reader with no row: the removal stands and cuts E's admission, and the admissions built on it "
           "with E's voice fall too (a silent colluder's old-head removal, for a reader with no row)",
     silent(0, lambda sg, fp: remove("xe", "E", ("A", "B"), ("g",))), None, {"xe": T},
     {"member": frozenset("ABCD")}, {"aF", "aG"}),
    (EDGE, "residual (2): the silent colluder at n=8, for a reader with no row: A, B and X1..X8 remove C, ten of fifteen (a silent "
           "colluder's packing chain under one protocol)",
     silent(8, lambda sg, fp: remove("xr", "C", sg, ("aG", fp))), None, {"xr": T}, {}, set()),
    (SF, "the same read by D: the chain is behind D's line and leaves the fold, and the removal concludes nothing for D",
     silent(8, lambda sg, fp: remove("xr", "C", sg, ("aG", fp))), "D", {"xr": T}, {"member": frozenset("ABCDEFG")}, {"p1"}),
    # ---- the second review of 58b ----------------------------------------------------------------------------------
    (SF, "a void change cuts nothing in the roster: A, B and C remove E at aD, a sibling of aE, having signed aF: the "
         "removal is self-forked over the rows held, and E, F and G stay for a reader with no row",
     RD, None, {"f": T}, {"member": SEVEN}, {"f"}),
    (SF, "the same for D, an older reader", RD, "D", {"f": T}, {"member": SEVEN}, {"f"}),
    (SF, "the same for E, the key the void removal names", RD, "E", {"f": T}, {"member": SEVEN}, {"f"}),
    (SF, "a key that signed both chains is in neither side of T: C signed the honest admissions and cosigned the fork's "
         "second row (H, a founder, signed only the honest chain): the fork is void, and its keys are not listed",
     [G4, QA("aD", "D", ("A", "B", "C", "H"), ("g",)), QA("aE", "E", ("A", "B", "C", "H", "D"), ("aD",)),
      QA("p1", "X1", ("A", "B"), ("g",)), QA("p2", "X2", ("A", "B", "C", "X1"), ("p1",))], None, {"p1": T, "p2": T},
     {"member": frozenset("ABCDEH")}, {"p1", "p2"}),
    (EDGE, "residual (1): no member seated at the fork point signed exactly one chain (here C signed both, and every founder at g "
           "did), for a reader with no row: T is a tie and keeps both, and the packers' removal of D stands",
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
    # residual (3): a newcomer admitted on the fork, reading as itself, its only row its acceptance of the fork's offer
    (SF, "a newcomer on a fork S'' voids: A and B invite X at g (two of three), after signing the honest admissions, and "
         "C signed only the honest chain; X accepts. Read by X: the invitation is self-forked over the rows X holds and "
         "void by T (C against none), so X reads the honest roster and its own seat is void (seated by nothing)",
     ROOM + [invite("oX", "X", ("A", "B"), ("g",)), ST.accept("acX", "X", "oX")], "X", {"oX": T, "acX": T},
     {"member": SEVEN}, {"oX"}),
    (EDGE, "residual (1): the same with A, B and C inviting X: every member seated at g signed both chains, so T is a tie "
           "and keeps both: X holds its seat, and reads the fold",
     ROOM + [invite("oX", "X", ("A", "B", "C"), ("g",)), ST.accept("acX", "X", "oX")], "X", {"oX": T, "acX": T},
     {"member": SEVEN | {"X"}}, set()),
    (EDGE, "residual (3): a newcomer admitted on the fork in the residual (1) world (no single-chain member, both kept): "
           "the eight on the chain invite X at p5, and X accepts. Read by X: the honest admissions are behind X's line "
           "(the reader-line exclusion), so X reads the fork's roster alone, not the fold; it takes its past from its "
           "admitter (CC 3.3.4)",
     ROOM + PACK + [invite("oX", "X", ("A", "B", "C", "X1", "X2", "X3", "X4", "X5"), ("p5",)), ST.accept("acX", "X", "oX")],
     "X", {"oX": T, "acX": T}, {"member": frozenset("ABCX") | {"X1", "X2", "X3", "X4", "X5"}}, {"aD"}),
    (EDGE, "the same rows for a reader with no row: the fold of both chains, with X",
     ROOM + PACK + [invite("oX", "X", ("A", "B", "C", "X1", "X2", "X3", "X4", "X5"), ("p5",)), ST.accept("acX", "X", "oX")],
     None, {"oX": T, "acX": T}, {"member": SEVEN | {"X", "X1", "X2", "X3", "X4", "X5"}}, set()),
    # ---- T at the fork point (the third attack): depth decides nothing; the same voices on both sides is a tie
    (SF, "HC1, honest concurrency: A..D admit E at aD and, on another device that has not seen aE, admit H at aD and J at "
         "c1: aE is self-forked (behind c2, which its voices signed), but the same four signed both sides: a tie, and both "
         "stand, however long either side is",
     HC, None, {"aE": T, "c1": T, "c2": T}, {"member": FOUR | {"E", "H", "J"}}, set()),
    (SF, "the same read by E", HC, "E", {"aE": T}, {"member": FOUR | {"E", "H", "J"}}, set()),
    (SF, "the same read by D", HC, "D", {"aE": T}, {"member": FOUR | {"E", "H", "J"}}, set()),
    (SF, "HC2: HC1 and an honest merge admitting K at (aE, c2): it concludes, and both sides stand",
     HC + [admit("m", "K", ("A", "B", "C", "D", "E", "H", "J"), ("aE", "c2"))], None, {"m": T},
     {"member": FOUR | {"E", "H", "J", "K"}}, set()),
    (SF, "HC4: three keys write a longer side to erase an admission: A, B and C admit E at aD (3 of 4) and write c1 (H at "
         "aD) and c2 (J at c1) without aE: the same three on both sides, a tie, and E stays (a removal of E by the three at "
         "aE is three of five, and short)",
     HC4, None, {"aE": T, "c1": T, "c2": T}, {"member": FOUR | {"E", "H", "J"}}, set()),
    (SF, "the same read by E", HC4, "E", {"aE": T}, {"member": FOUR | {"E", "H", "J"}}, set()),
    (SF, "HC6: A, B and C admit E, then A, B, C and E admit K and remove D; A, B and C later write c1 and c2 from aD "
         "without aE (backdated): a tie at aD, and for a reader with no row the fold holds both",
     HC6, None, {"aK": T, "xD": T, "c1": T, "c2": T}, {"member": frozenset("ABCEHJK")}, set()),
    (SF, "the same read by E: c1 and c2 are behind E's line, and leave E's roster",
     HC6, "E", {"xD": T}, {"member": frozenset("ABCEK")}, {"c1"}),
    (SF, "the same read by K", HC6, "K", {"xD": T}, {"member": frozenset("ABCEK")}, {"c1"}),
    (SF, "the same read by D, the key removed: the fold holds both",
     HC6, "D", {"xD": T}, {"member": frozenset("ABCEHJK")}, set()),
    (SF, "packed keys on a long fork: A and B pack X1..X8 from g, each row signed by them and the keys before it; the "
         "packed keys were not seated at g and are no part of T: C against none, the chain is void, and the packers' "
         "removal of C at (aG, p8) concludes nothing",
     ROOM + PK8 + [remove("xr", "C", PK8S, ("aG", "p8"))], None, {"p1": T, "xr": F}, {"member": SEVEN},
     {"p%d" % i for i in range(1, 9)}),
    (SF, "the same read by D", ROOM + PK8 + [remove("xr", "C", PK8S, ("aG", "p8"))], "D", {"xr": F}, {"member": SEVEN}, {"p1"}),
    (SF, "a single-chain member that has since left still counts: C resigns at aG; A and B pack X1..X8 from g and the "
         "packers remove D at (aG, p8): C was seated at g and signed only the honest chain (leaving does not unsay it), "
         "so the chain is void and D stays",
     ROOM + [ST.withdraw("wc", "C", "g", ("aG",))] + PK8 + [remove("xr", "D", PK8S, ("aG", "p8"))], None,
     {"wc": T, "xr": F}, {"member": SEVEN - {"C"}}, {"p%d" % i for i in range(1, 9)}),
    (SF, "the same read by D", ROOM + [ST.withdraw("wc", "C", "g", ("aG",))] + PK8 + [remove("xr", "D", PK8S, ("aG", "p8"))], "D",
     {"xr": F}, {"member": SEVEN - {"C"}}, {"p1"}),
    # ---- the window's closers (wc.py), each read by a reader with no row and by B
    (EDGE, "the window, no closer: the siblings stand, and wb ends B's seat", WC("none"), None, {"zC": T, "wb": T},
     {"moderate": frozenset("ACDE"), "member": SEVEN}, set()),
    (EDGE, "the same read by B", WC("none"), "B", {"zC": T, "wb": T}, {"moderate": frozenset("ACDE"), "member": SEVEN}, set()),
    (EDGE, "a concurrent change closes nothing: five admit H at aG", WC("concurrent"), None, {"zC": T, "wb": T, "c": T},
     {"moderate": frozenset("ACDE"), "member": SEVEN | {"H"}}, set()),
    (EDGE, "the same read by B", WC("concurrent"), "B", {"zC": T, "wb": T, "c": T},
     {"moderate": frozenset("ACDE"), "member": SEVEN | {"H"}}, set()),
    (EDGE, "a later change the lone holder did not sign (B..F admit H at d1) does not close it for a reader with no row",
     WC("notA"), None, {"zC": T, "wb": T, "c": T}, {"moderate": frozenset("ACDE"), "member": SEVEN | {"H"}}, set()),
    (LO, "the same read by B, who signed it: closed for B, the siblings are void for it and B keeps its seat",
     WC("notA"), "B", {"zC": T, "wb": T, "c": T}, {"moderate": frozenset("AB"), "member": SEVEN | {"H"}}, {"zC", "zD", "zE"}),
    (LO, "the lone holder signs a later change with B (A and B confer moderate on F at d1): closed for every reader. The "
         "siblings are self-forked (A signed the closer); by T, C, D and E's voices on wb rest on the siblings' own "
         "seats and count for nothing, while B's on the closer rests on d1, the other line's own non-forked change: "
         "B against none, and the siblings and wb are void",
     WC("AB"), None, {"zC": T, "wb": T, "c": T}, {"moderate": frozenset("ABF"), "member": SEVEN}, {"wb", "zC", "zD", "zE"}),
    (LO, "the same read by B, who signed it: closed for B", WC("AB"), "B", {"zC": T, "wb": T, "c": T},
     {"moderate": frozenset("ABF"), "member": SEVEN}, {"zC", "zD", "zE"}),
    (LO, "the lone holder signs a later change (A among five admit H at d1): closed for every reader, the siblings void "
         "and wb with them",
     WC("A5"), None, {"zC": T, "wb": T, "c": T}, {"moderate": frozenset("AB"), "member": SEVEN | {"H"}},
     {"wb", "zC", "zD", "zE"}),
    (LO, "the same read by B", WC("A5"), "B", {"zC": T, "wb": T, "c": T}, {"moderate": frozenset("AB"), "member": SEVEN | {"H"}},
     {"zC", "zD", "zE"}),
    # ---- what T counts (the fourth attack): only counted changes, only rows on the side, only standing held at the
    # fork point or granted by the other line's own non-forked change
    (LO, "WT1: the closer by A and B at d1, the siblings at aG: B's voice on the closer rests on d1, the other line's "
         "own non-forked change, so B counts; the siblings are void and the window is closed for every reader",
     WT1, None, {"zC": T}, {"moderate": frozenset("ABF")}, {"zC", "zD", "zE"}),
    (LO, "WT2: C, D and E post on the siblings' side: a post is no voice, and counts for nothing", WT1 + WPOSTS, None,
     {"zC": T}, {"moderate": frozenset("ABF")}, {"zC", "zD", "zE"}),
    (LO, "WT3: C, D and E cosign wb: their moderate voices rest on the siblings' own seats, held by none of them at "
         "aG, and count for nothing: the siblings and wb are void", WT1 + [WWB], None, {"zC": T, "wb": T},
     {"moderate": frozenset("ABF")}, {"wb", "zC", "zD", "zE"}),
    (LO, "the same read by C", WT1 + [WWB], "C", {"wb": T}, {"moderate": frozenset("ABF")}, {"wb", "zC", "zD", "zE"}),
    (LO, "WT4: WT3 and honest F and G posting after the closer: the same", WT1 + [WWB] + WHON, None, {"zC": T, "wb": T},
     {"moderate": frozenset("ABF")}, {"wb", "zC", "zD", "zE"}),
    (SF, "RC0: A, B, C and D remove E by count at aE, four of the six others (the member removed is not counted): met",
     RCB + [remove("xE", "E", tuple("ABCD"), ("aE",))], None, {"xE": T}, {"member": frozenset("ABCDFG")}, set()),
    (SF, "RC1: c1 and c2 beside aE, by the same four: a tie, and E stays", RCB + [RC1_, RC2_], None,
     {"aE": T, "c1": T, "c2": T}, {"member": frozenset("ABCDEFGHJ")}, set()),
    (SF, "RC2: c1 cites F's concurrent post: what a row cites is its author's choice, and a member is not recruited by "
         "being named: a tie, and E stays", RCB + [RFP, RC1P, RC2_], None, {"aE": T, "c1": T, "c2": T},
     {"member": frozenset("ABCDEFGHJ")}, set()),
    (SF, "the same read by E", RCB + [RFP, RC1P, RC2_], "E", {"aE": T}, {"member": frozenset("ABCDEFGHJ")}, set()),
    (SF, "the same read by F", RCB + [RFP, RC1P, RC2_], "F", {"aE": T}, {"member": frozenset("ABCDEFGHJ")}, set()),
    (SF, "RC5: F, a colluder, acknowledges c2: an acknowledgement is no voice: a tie, and E stays",
     RCB + [RC1_, RC2_, ack("af", "F", "c2")], None, {"aE": T}, {"member": frozenset("ABCDEFGHJ")}, set()),
    (EDGE, "RC7, beside the residual and not part of it: B, C, D, F and G admit Q at aG, honestly; A, B, C and D, every "
           "voice of aE, then admit H at cq with Q, and J on it, without aE. A counted change is void where every voice "
           "that made it has gone on to build without it and the members who built only on the other line outnumber "
           "those who built only on this one (F and G, against none). Those voices could have removed what the change "
           "seated by their own count",
     RC7, None, {"aE": T, "cq": T, "c1": T, "c2": T}, {"member": frozenset("ABCDFGHJQ")}, {"aE"}),
    (EDGE, "RC7 read by E: the same", RC7, "E", {"aE": T}, {"member": frozenset("ABCDFGHJQ")}, {"aE"}),
    (SF, "RC7's guard: only three of aE's four voices (A, B and C, with Q and F) build c1 at cq without aE, and D "
         "acknowledges aE: not every voice built without it, so aE is not self-forked, and E stays",
     RC7G, None, {"aE": T, "c1": T}, {"member": frozenset("ABCDEFGHQ")}, set()),
    (SF, "BN: B, who holds review at g, takes moderate at g by its own yes with A; A and B then admit D and E without "
         "it: the beneficiary is no evidence for its side, so A alone against A and B: void, and only A holds moderate",
     BN, None, {"cf": T, "aE": T}, {"member": frozenset("ABCDE"), "moderate": frozenset("A")}, {"cf"}),
    (SF, "one rule for bundles and rosters: an explicit acknowledgement settles only what counts over its own past. "
         "R's ack names the cheap tip's xd as its head and aG beside it: over that past dc is self-forked, so xd is no "
         "part of R's line (R acknowledges the honest line only)",
     ROOM + [DC("dc", "B", ("g",)), admit("xd", "X", ("A", "B"), ("dc",)), CK.row("k", "ack", "R", ("xd", "aG"), room=OBJ, head=("xd",))],
     "R", {"xd": T}, {"member": SEVEN}, {"dc"}),
    # the lone holder's window, stated: closed for a reader by any later counted change that reader has acknowledged,
    # and for every reader once the lone holder itself signs a later change; each sibling is a row by one key that said
    # two things at one head, and the two rows are the evidence a recall cites (the members recall any duty holder,
    # however seated, CC 4.5.13)
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
    (SF, "two founders seated concurrently at g (f4 by one founders' amendment, f5 by another, each restating 3/4): "
         "concurrent versions of the record wait (CC 2.7.8): no founders' count concludes over a past holding both until a "
         "version names both, so f1 and f2's removal of f3 concludes nothing",
     [GI5[0], GI5[1], ST.offer("a5", "f1", "f5", "record", OBJ, "group", ("g",), head=("g",), counted="founder",
                               role="founder", cosigners=("f2", "f5"), consensus_protocol="quorum:3/4",
                               consensus_protocol_entrenched=True),
      IX("x", ("a4", "a5"), ("f1", "f2"))], None, {"a4": T, "a5": T, "x": F}, {"founder": frozenset(("f1", "f2", "f3"))}, set()),
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
          ("changes_any_object", ST.MUT), ("over_allowed", ST.MUT), ("lone_exempt", ST.MUT),
          ("ends_at_heads_unread", ST.MUT), ("resign_exempt", ST.MUT), ("line_concurrent", CP.MUT), ("versions_concurrent", CP.MUT),
          ("cut_before_line", ST.MUT), ("line_void_unlisted", ST.MUT), ("acks_only", CP.MUT),
          ("line_not_sibling_safe", CP.MUT), ("election_exempt", ST.MUT), ("contested_unseats_only", ST.MUT), ("contested_takes_voice", ST.MUT),
          ("acceptance_unread", ST.MUT), ("acceptance_ends_unread", ST.MUT),
          ("lone_offer_unread", ST.MUT), ("lone_offer_same_scope", ST.MUT), ("fold_acceptance_unread", ST.MUT),
          ("heads_not_antichain", ST.MUT), ("window_opener_old_head", ST.MUT), ("lone_offer_self_path", ST.MUT),
          ("self_fork_unread", ST.MUT), ("t_unread", ST.MUT), ("fork_by_depth", ST.MUT), ("meet_tips", ST.MUT),
          ("regime_before_change", ST.MUT), ("reader_exclusion_unread", ST.MUT),           ("ack_unvoids", CP.MUT), ("void_cuts_in_roster", ST.MUT),
          ("t_counts_beneficiary", ST.MUT), ("ack_self_fork_unread", CP.MUT), ("t_counts_posts", ST.MUT), ("t_counts_sided_seat", ST.MUT),
          ("t_strict_standing", ST.MUT), ("regime_protocol_only", ST.MUT))
# retired with T at the fork point (the third attack): rescue_unread, tie_unread and rescuer_signed_both (S' 's rescue
# and tie, which T replaces; fork_by_depth plants the S' form whole)
# retired with the ruling of 2026-11-27: ack_excuses_none (H7, subsumed by the self-fork void), ack_reads_void (a
# counted row's own void is in the roster's S'' void, which holds every row), and line_after_cut (the
# line's first pass reads every row as counting; with the line sibling-safe and the reader's rows concluded again for
# it, no case here tells a first pass over the cut from one over every row)


import contextlib  # noqa: E402


@contextlib.contextmanager
def setting(rule):
    """SFB's cases run with the act-to-policy binding off (their removal states `majority`)."""
    on = rule == SFB and "binding_off" not in ST.MUT
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
