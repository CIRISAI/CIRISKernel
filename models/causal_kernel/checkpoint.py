"""
checkpoint.py: which counted rows of a group's ledger count for a reader.

    built on            A counted act (an offer or an unseat conferred by a count, naming the head it is counted over)
                        counts only if every counted act among the heads it names itself counts. A row built on a
                        counted act that does not count is void, down the whole line. This is a rule in its own right,
                        whatever else is on or off: nothing is built on a void row. "Does not count" is one thing here:
                        the cut voids it (cut.py), the reader's line leaves it behind, or it is itself built on such a
                        row. There is no other way for a head act to fail.
    the reader's line   A reader's own acknowledgement of a head (an `ack` row under its key, with `room` and `head`)
                        makes the acknowledged act, and every counted act in its past, that reader's line. For that
                        reader the line counts, and a counted act concurrent with an act of the line that names only
                        heads strictly in that act's past does not count (CC 2.7.8: "holds void every counted act
                        that names an older head and is not in that head's past"). So a line grown from below what
                        the reader acknowledged is void for it, however long it is, and so is a SIBLING of the
                        acknowledged act (it names their common predecessor), and a row built on either. For a reader
                        with no acknowledgement on that line two versions of one head wait as tips (CC 2.7.8: "Two
                        versions of one head wait as tips"), and a counted row naming both makes one head again.
                        This is relative to the reader and binds nobody else. It ranks no line above another.

Both are functions of (rows, own key). No instant, no arrival order and no digest is compared.

    the group checkpoint   OFF. `group=True` makes every counting counted act a checkpoint for everyone: an act
                        concurrent with it and counted over older heads does not count. It is a rank by depth of line,
                        and this kernel orders nothing except by what rows name. With it on, keys that met the count at
                        the head the newest honest row is counted over sign two rows, the second over the first, are one
                        row deeper than the honest line, and leave the honest row behind: a removed member is listed
                        again (attacks.py, test 4 and checkpoint_price). Honest concurrency on one head behaves the same
                        way. The parameter exists only to show that witness, and the one in window.py (a majority
                        voiding one voice). With it on, "counts" refers to itself through negation and is solved as the
                        cut is, by the well-founded fixed point; with it off there is no negation and one answer.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import causal_kernel as CK  # noqa: E402

K = CK.K
MUT = set()            # planted breaks, switched on by a check


def older(S, heads, than):
    """Every row of `heads` is strictly in the past of one of `than`. (Read over the newest of the heads it is the
    same: a named head in the past of another named head is in the past of whatever that one is.)"""
    return bool(heads) and all(any(h in S.anc.get(t, ()) for t in than) for h in heads)


def behind(S, r, c):
    """The line (the ruling of 2026-11-27, CC 2.7.8 as amended): counted act r is behind act c where every head r names
    is strictly in the past of c's OWN heads and r is not in c's past. A sibling at c's own head is not behind it.
    MUTATION line_not_sibling_safe: every head r names strictly in the past of c itself (the text until the ruling)."""
    if c["id"] == r["id"] or r["id"] in S.anc[c["id"]]: return False
    if "line_not_sibling_safe" in MUT: return older(S, r["head"], [c["id"]])
    return older(S, r["head"], c.get("head", ()))


def is_counted_act(r, obj):
    """A counted act on obj: an offer or an unseat conferred by a count, naming the head it is counted over. The one
    definition of a counted change of obj's roster: the reader's line reads it, and so does seat.newer_head_in_past."""
    return r["kind"] in ("offer", "unseat") and r.get("conf") == "group" and r.get("obj") == obj and bool(r.get("head"))


def counted_acts(S, obj):
    return [r for r in S.Cs if is_counted_act(r, obj)]


def object_of(r, by, n=0):
    """The object a row is over: its `obj` (a founding row, `@`, is its own), its `room`, or the object of the row its
    `of` or `target` names (an acceptance, a cosignature, a withdrawal, a window's answer, receipt or landing)."""
    if n > 8: return None
    if r.get("obj") == "@": return r["id"]
    if r.get("obj") is not None: return r["obj"]
    if r.get("room") is not None: return r["room"]
    t = by.get(r.get("of")) if r.get("of") is not None else by.get(r.get("target"))
    return object_of(t, by, n + 1) if t is not None and t is not r else None


def acknowledgements(S, own, obj, rows=None):
    """A reader's acknowledgements over obj (the ruling of 2026-11-26, H6): every concluded row `own` signed or
    cosigned over obj, of any kind (its own seating or acceptance, a counted row it signed or cosigned, a
    cosignature, its withdrawal, a window's opener, answer, receipt or landing, its explicit `ack`, a row of content).
    Each acknowledges the counted acts in its own past. MUTATION acks_only: explicit `ack` rows only (before 0.5.0)."""
    rows = S.Cs if rows is None else rows
    if "acks_only" in MUT:
        return [a for a in rows if a["kind"] == "ack" and a["signer"] == own and a.get("room") == obj]
    return [a for a in rows if (a["signer"] == own or own in a.get("cosigners", ())) and object_of(a, S.by) == obj]


def takes_up(S, own, f):
    """THE READER'S LINE taking up row f (the ruling on one self roster per identity: a reader's roster for an identity
    is the founding its line takes up): a concluded row `own` signed or cosigned is f or has f in its past, the row
    counting only where own's key stands there (its own revocation, a `registered` unseat by it, not in that row's
    past: the K1 rule). A reader with no rows takes up nothing. MUTATION line_takes_nothing."""
    if own is None or "line_takes_nothing" in MUT: return False
    def stands(a):
        return not any(S.by[x]["kind"] == "unseat" and S.by[x].get("scope") == "registered" and S.by[x]["signer"] == own
                       and own in S.by[x].get("to", ()) for x in S.anc[a["id"]] if x in S.by)
    return any((a["signer"] == own or own in a.get("cosigners", ())) and (a["id"] == f or f in S.anc[a["id"]]) and stands(a)
               for a in S.Cs)


def own_line(S, own, obj):
    """The counted acts on obj this reader has acknowledged, with the counted acts in their past: those in the past of
    (or equal to) any of its acknowledgements, and any head an explicit `ack` names.

    Acknowledging never un-voids (the ruling of 2026-11-27, CC 2.7.9: an acknowledgement closes older heads and nothing
    reopens them): a row the reader signed acknowledges the counted acts in its past that are not already void for the
    line its earlier rows (those in its own past) drew, nor void for the row itself (a counted row's S'' void, seat sets
    ACK_VOID). So a change behind the reader's line stays behind it even after the reader signs a row naming it as a head.
    MUTATIONS ack_unvoids (every act in a row's past acknowledged, whatever its earlier line held void); ack_reads_void (a
    counted row acknowledges its own void changes too)."""
    if own is None: return []
    acks = sorted(acknowledgements(S, own, obj), key=lambda a: (len(S.anc[a["id"]]), a["id"]))
    acts = counted_acts(S, obj)
    def covered(a):
        """The counted acts a row acknowledges before any exclusion: it, its past, and the heads an `ack` names."""
        named = set(a.get("head", ())) if a["kind"] == "ack" else set()
        return {r["id"] for r in acts if r["id"] == a["id"] or r["id"] in S.anc[a["id"]] or r["id"] in named
                or any(r["id"] in S.anc[h] for h in named if h in S.anc)}
    by = {r["id"]: r for r in acts}
    def void_for(line):
        """The counted acts behind a line (sibling-safe), and those built on them, the line's own acts apart."""
        out = {r["id"] for r in acts if r["id"] not in line and any(behind(S, r, by[c]) for c in line)}
        changed = True
        while changed:
            changed = False
            for r in acts:
                if r["id"] not in out and r["id"] not in line and any(h in out for h in r["head"]):
                    out.add(r["id"]); changed = True
        return out
    got = {}
    for a in acks:
        ex = ACK_VOID(S, a) if ACK_VOID and is_counted_act(a, obj) and "ack_reads_void" not in MUT else frozenset()
        cov = covered(a)
        if "ack_unvoids" in MUT:
            got[a["id"]] = {r for r in cov if r == a["id"] or r not in ex}
            continue
        # the line the reader's rows in a's own past drew, and what it holds void
        prior = set().union(*[got[b["id"]] for b in acks if b["id"] in S.anc[a["id"]]])
        held = void_for(prior)
        got[a["id"]] = {r for r in cov if r == a["id"] or (r not in ex and r not in held)}
    mine = set().union(*got.values()) if got else set()
    return [r for r in acts if r["id"] in mine]


ACK_VOID = None     # seat.void_changes, read for a reader's own counted rows


def settle(S, C, obj, own=None, group=False, never_behind=lambda r: False):
    """(certain, possible): the ids of the counted acts on obj that count for reader `own`.

    A counted act counts iff the cut lets it count, EVERY COUNTED ACT AMONG THE HEADS IT NAMES ITSELF COUNTS, and no
    act of the reader's own acknowledged line leaves it behind. The reader's line counts for that reader.
    With group=False (the rule) nothing here is negated and certain == possible.
    With group=True (the refused group checkpoint, kept to show why) every act that certainly counts also leaves
    older-head acts behind; an act in `possible` and not in `certain` is then undecided: not void, and no checkpoint."""
    acts = counted_acts(S, obj)
    live = sorted((r for r in acts if C.counts(r)), key=lambda r: len(S.anc[r["id"]]))
    line = {r["id"] for r in acts}
    built = {r["id"]: [h for h in r["head"] if h in line] for r in live}          # the counted acts it is built on
    mine = {r["id"] for r in own_line(S, own, obj)} & {r["id"] for r in live}
    # the reader's line: r names only heads strictly in the past of the line's act c (CC 2.7.8)
    # CC 2.7.8: "holds void every counted act that names an older head and is not in that head's past, however many rows
    # it has": no test of concurrency, so a row with c in its own past that names a head older than c is void too
    # (MUTATION line_concurrent: the line voids only rows concurrent with c, the rule until 0.5.0)
    # `never_behind(r)`: an act the line never leaves behind (an election's seating, read at its election's vacancy;
    # seat.Seats passes it)
    # the ruling of 2026-11-27: behind() is sibling-safe (r's heads strictly in the past of c's own heads)
    line_behind = lambda r, c: behind(S, r, c) and not never_behind(r) \
        and ("line_concurrent" not in MUT or S.concurrent(r["id"], c["id"]))
    # the refused group checkpoint (group=True only): r's heads strictly older than the heads c names
    group_behind = lambda r, c: c["id"] != r["id"] and S.concurrent(r["id"], c["id"]) and older(S, r["head"], c["head"])

    def gamma(I):
        """The acts that count if exactly the acts in I (and the reader's line) are the checkpoints."""
        marks = [c for c in live if group and c["id"] in I and c["id"] not in mine]
        line = [c for c in live if c["id"] in mine]
        out = set()
        for r in live:                                                  # ancestors first
            if r["id"] in mine or (all(h in out for h in built[r["id"]]) and not any(line_behind(r, c) for c in line)
                                   and not any(group_behind(r, c) for c in marks)):
                out.add(r["id"])
        return frozenset(out)
    T = frozenset()
    while True:
        U = gamma(T); T2 = gamma(U)
        if T2 == T: return T, U
        T = T2


def checkpoints(S, C, obj, own=None, group=False):
    """The counted acts on obj that certainly count."""
    T, _ = settle(S, C, obj, own, group)
    return [r for r in counted_acts(S, obj) if r["id"] in T]


class EVERY:
    """A cut under which every row counts: the reader's line read before the cut (seat.Seats)."""
    counts = staticmethod(lambda r: True)


def void(S, C, own=None, group=False, never_behind=lambda r: False):
    """The ids of the counted acts the cut lets count that do not count for reader `own`: left behind by its
    acknowledged line, or built on a counted act that does not count."""
    out = set()
    for obj in {r["obj"] for r in S.Cs if r["kind"] in ("offer", "unseat") and r.get("conf") == "group" and r.get("head")}:
        _, U = settle(S, C, obj, own, group, never_behind)
        out |= {r["id"] for r in counted_acts(S, obj) if C.counts(r) and r["id"] not in U}
    return frozenset(out)


def stale_answer(S, cps, p, r):
    """Only for window.outcome(..., checkpoint=True), which is off: a row r answering window p is left behind by a
    checkpoint of p's object that names a newer head than p was opened on and has everything r names in its past."""
    return any(S.concurrent(r["id"], c["id"]) and older(S, p["head"], c["head"]) and all(n in S.anc[c["id"]] for n in r["names"]) for c in cps)


def versions(ids, builds_on, past, valid, ack=None, group=False):
    """The same two rules for roster versions (formal/roster_fork's shape). ids: the versions held; builds_on[i]: the
    heads version i extends; past[i]: every version in its past; valid(i): counted over the heads it extends. ack: the
    version this reader has acknowledged, or None. Returns (certain, possible); they differ only with group=True."""
    conc = lambda i, j: i != j and i not in past[j] and j not in past[i]
    # the refused group checkpoint (group=True only): i's heads strictly older than the heads j extends
    stale = lambda i, j: conc(i, j) and bool(builds_on[j]) and bool(builds_on[i]) and all(any(e in past[h] for h in builds_on[j]) for e in builds_on[i])
    # the reader's line: i is not in the past of j, an act of the line, and extends only versions strictly in j's past
    # (CC 2.7.8; no test of concurrency, as settle; MUTATION versions_concurrent: only versions concurrent with j)
    # sibling-safe (the ruling of 2026-11-27): every version i extends strictly in the past of a version j extends
    # (MUTATION line_not_sibling_safe: in the past of j itself)
    behind = lambda i, j: i != j and i not in past[j] and ("versions_concurrent" not in MUT or j not in past[i]) \
        and bool(builds_on[i]) and all((e in past[j]) if "line_not_sibling_safe" in MUT else any(e in past[h] for h in builds_on[j])
                                       for e in builds_on[i])
    P = [i for i in ids if valid(i)]
    mine = frozenset() if ack is None else frozenset({ack}) | frozenset(past[ack])       # the reader checkpoint: its acknowledged line
    P = sorted((i for i in P if i in mine or not any(behind(i, a) for a in mine)), key=lambda i: len(past[i]))

    def gamma(I):
        out = set()
        for i in P:
            if all(e in out for e in builds_on[i]) and (i in mine or not (group and any(stale(i, j) for j in I))): out.add(i)
        return out
    T = set()
    while True:
        U = gamma(T); T2 = gamma(U)
        if T2 == T: return frozenset(T), frozenset(U)
        T = T2
