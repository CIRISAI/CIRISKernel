"""
window.py: a window as rows.

    open      row p opens the window. It names the head it is counted over, and (for an eviction) its target.
    answer    a row naming p that says something the window's table counts: approve, object, confirm, answered, for,
              against (a ballot on the act proposed: `for`, or `against`, the same row with the other choice).
    receipt   a key with the concluder's seat signs that it holds p, stating its own instant.
              "Inside the window" is what the landing has in its past and the receipt has not, so a receipt
              with a row of the target in its past would put that row before the window. A row that has one, beyond
              what the opener itself has in its past, is no receipt, and a landing naming it concludes nothing.
    landing   the same key names its receipt and the head it then holds, states its own instant and the outcome.

"Inside the window" is a relation between rows: in the past of the landing and not in the past of the receipt.
The duration is the concluder's own two instants (landing.at - receipt.at >= secs); no instant of one signer is
compared with another's. A landing is CONCLUDED iff its signer held the concluder's seat at the head p names, it
names its own receipt, and the outcome it states is the one the window's table gives over its own past. A landing
that states another outcome concludes nothing, for every reader, in every order.

The landing is a cut on p's slot. What is left open is a row that answers p (or, where the table asks for the
target's silence, any row the target signed) and is CONCURRENT with the landing. Three rules, all run:

    void      (i)   the cut voids it: the landing stands (cut.py, unchanged)
    contest   (ii)  any such row contests the landing: it does not count until a landing names both
    recount   (ii, narrowed) such rows are counted with the landing's past; the landing stands iff the table then
              gives the outcome it states, and is contested otherwise

A row that NAMES the landing is judged at the head it names under every rule: it came after and changes nothing.
Concurrency is the signer's own word: a key can always leave the landing unnamed.

Under recount two things bound that word.
    ended seat   a row of a key whose seat over the object was ended (a counting unseat, or a withdrawal of the offer
                 that seated it) is counted only if the ending row has it in its past (KERNEL.md section 6).
    standing     a landing that does not stand says nothing against a landing that does: the outcome is contested only
                 when no frontier landing stands, or two that stand state different outcomes.

The checkpoint (checkpoint.py) is NOT applied to a window's answers. A window protects one voice against the count,
and a checkpoint is made by the count: with it on, a majority voids a present moderator's timely answer by signing
counted rows that leave it unnamed (attacks.py, checkpoint_price). `outcome(..., checkpoint=True)` exists only to
show that witness.

The five windows are data (WINDOWS): the policy row of manifests/governance_policy.json, the clauses that close
the window at once, the clauses read at the close, and the default.

A clause is (value said, threshold, base, outcome). The bases:
    all               the window's counted scope at the opener's head
    others            the same, less the opener's signer: out of the voices and out of the size counted over (the
                      members' check: "a strict majority of the members seated at the head the act names, the
                      act's author apart"). Where the opener is a removal of an AI agent's key (an unseat marked
                      `agent`), the key it removes is apart too: an agent "acts under its own key and has no
                      vote", so in the lift of its own removal it is no voice and is not counted over, whether
                      the count is read with no landing, by a landing, or by the recount
    opener            the opener's signer alone
    ("stated", n)     the base `active` above k (CIRISConstitution#221): the caller's stated count, the census's figure
                      (CC 6.1.9), which the kernel takes and does not check. The voices are those of `all`; the size
                      counted over is n where n is larger than the members `all` reads, and never smaller (a caller
                      cannot shrink a base below the members the rows seat)
    any other word    that scope at the opener's head
The thresholds: "strict", "one", ("atleast", n, d, min), ("more", n, d, min), and
    ("voted", n, d, min, against)   more than n/d of the keys of the base that VOTED, and at least min voices: a key
                      voted if it said the clause's value or `against`. A silent key is not counted over.

A ballot (CIRISConstitution#221: the fallback vote): the answers a "voted" clause reads, its value and its `against`,
are a member's ballot of the family the window's table names (`ballot`; the fallback's is `ballot:moderation_action`,
`for` or `against`). One ballot a person, folded as `ballot:moderator` is: a voice whose ballots agree is one ballot,
and a voice whose unwithdrawn ballots disagree says nothing (the fold above, K.group "one"). A ballot its own
signer withdrew (a `withdraw` row naming it, CC 2.4.1.1 rule 1) is no ballot: a landing that counts it concludes
nothing, and a withdrawal concurrent with a landing is recounted with it, as an answer is. A withdrawal by any
other key withdraws nothing. One may conclude: seat.seat_rule concludes a withdrawal by any signer of the row it
names, a cosigner of the ballot included. What makes it no withdrawal of the ballot is the match on the ballot's own
signer here. Only a ballot is read so (the ruling on #221): an objection or an approval its signer withdrew is still
a voice. A withdrawn ballot stays withdrawn (ruling C2 on #221): a withdrawal of the withdrawal revives nothing,
and the way back is a new ballot.

The landing of the fallback and of the overturn is a signed row of the family that closes the self roster's lone
path (CC 3.3.6.4; the ruling on CIRISConstitution#221, W1: one landing family for every window): the receipt is a
`window:held` row and the landing a `window:landed` row, which states the outcome. The family names are the
caller's; nothing here reads them or checks a row's family (a receipt and a landing are the row kinds above).
The fallback's is signed by any member at the opener's head. The overturn's is signed by any member there but the
act's author (W2): a key no clause counts is no concluder of the window, so where every counted clause is over
`others` (author_apart) the opener's signer signs no receipt and no landing of it.

`halt_fuse` is the holders' confirmation of a halt, a count (CC 4.2.1.1); the halted node's own fuse, on its own
clock with no landing, is the node's and is not read here (reactions.json `fuse local, late closed`). The name is a
misnomer kept for now: the adversary table and the fixtures carry it.

A duty holder's single-signature answer (a value an at-once clause reads as "one" over a named scope, said by a
holder of that scope) is what that key said: a vote the same key also cast is moot, and does not make its answer
two things said.

An opener is a row of kind `open`, or a counted act that names a window (`window` on an unseat: a moderator's lone
removal of an agent's key, seat.py). Such an act is concluded by the seat's rule and the opener's together.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import seat as ST  # noqa: E402
import checkpoint as CP  # noqa: E402

CK, CUT, K, R = ST.CK, ST.CUT, ST.K, ST.R

# value said, threshold, over which base, outcome
WINDOWS = {
    # formal/self_roster, CC 3.3.6.4: a strict majority of the roster lands it at once (the proposer approves);
    # a strict majority of the others refuses it; alone it lands at the close, and only if the target was silent
    # The proposer may withdraw its own open proposal: refused at once, unless a strict majority has already approved
    # (a count once met is final, so the approval is read first).
    "self_roster_evict": {"policy": "self_roster_evict", "counted": "self", "concluder": "self", "opener_says": "approve",
                          "at_once": (("approve", "strict", "all", "landed"), ("withdraw", "one", "opener", "refused"),
                                      ("object", "strict", "others", "refused")),
                          "silent": "refused", "at_close": (), "default": "landed"},
    # the same policy for adding a key: the eviction's table without the target's silence
    "self_roster_add": {"policy": "self_roster_add", "counted": "self", "concluder": "self", "opener_says": "approve",
                        "at_once": (("approve", "strict", "all", "landed"), ("withdraw", "one", "opener", "refused"),
                                    ("object", "strict", "others", "refused")),
                        "silent": None, "at_close": (), "default": "landed"},
    # CC 4.5.13: a moderator answers within 48 h; on their absence the members act: "a strict majority of the members
    # who voted, never fewer than two voices" (data/governance_policy.tsv, moderation_action). A member's vote is a
    # ballot of `ballot:moderation_action` (CIRISConstitution#221): `for`, or `against` (a contrary voice is a vote
    # against); a silent member is not counted over. A moderator's answer is no vote. The landing is a signed row
    "moderation_fallback": {"policy": "moderation_action", "counted": "member", "concluder": "member", "opener_says": None,
                            "ballot": "ballot:moderation_action",
                            "at_once": (("answered", "one", "moderate", "answered"),),
                            "silent": None, "at_close": (("for", ("voted", 1, 2, 2, "against"), "all", "fallback"),), "default": "lapsed"},
    # CC 4.2.1.1: one holder fires at once; the holders' confirmation of the halt, a count (a strict majority). The
    # halted node's own fuse, on its own clock with no landing, is the node's and is not read here (the name misleads)
    "halt_fuse": {"policy": "accord_halt", "counted": "holder", "concluder": "holder", "opener_says": "confirm",
                  "at_once": (("confirm", "strict", "all", "confirmed"),),
                  "silent": None, "at_close": (), "default": "lapsed"},
    # CC 4.5.13, the members' check: a duty holder's act takes effect at once and is itself the opener. "The act is
    # lifted when a strict majority of the members seated at the head the act names, the act's author apart, has
    # objected within the 48-hour window. ... The floor is two voices. The author's own objection is no voice, and the
    # author is not among the members the majority is taken of. Where the author is one of two members no lift is
    # possible." Short of that at the close it stands. So the base is `others`
    "moderation_overturn": {"policy": "moderation_overturn", "counted": "member", "concluder": "member", "opener": "moderate",
                            "opener_says": None, "at_once": (("object", ("more", 1, 2, 2), "others", "lifted"),),
                            "silent": None, "at_close": (), "default": "stands"},
}
# default_content above k (CIRISConstitution#221; the ruling: the base `active` is the caller's stated count). The
# self roster's lone path, read off the policy row: enact strictly more than 2/3 at once (the table's decider,
# enact_votes = 2*base//3 + 1; the Constitution's ruling of 2026-11-27: six need five, three need three; this read
# "at least 2/3" before), cancel 1/3 at the close, floor 1/3 at the close, never fewer than two voices (min_count,
# community); default cancelled. Counted over ("stated", n): n = 20 here, the census's figure for a room of thirteen
# members
ACTIVE = 20
WINDOWS["default_content@active"] = {
    "policy": "default_content", "counted": "member", "concluder": "member", "opener_says": "approve",
    "at_once": (("approve", ("more", 2, 3, 2), ("stated", ACTIVE), "landed"),),
    "silent": None,
    "at_close": (("object", ("atleast", 1, 3, 2), ("stated", ACTIVE), "cancelled"),
                 ("approve", ("atleast", 1, 3, 2), ("stated", ACTIVE), "landed")),
    "default": "cancelled"}
# the same with a stated count of five, fewer than the members a case seats: the size counted over is never smaller
WINDOWS["default_content@active@5"] = dict(
    WINDOWS["default_content@active"], at_once=(("approve", ("more", 2, 3, 2), ("stated", 5), "landed"),),
    at_close=tuple((v, h, ("stated", 5), o) for v, h, _, o in WINDOWS["default_content@active"]["at_close"]))
# stated counts of six and three, as many as the members: strictly more than 2/3, so six need five and three need three
for _n in (6, 3):
    WINDOWS["default_content@active@%d" % _n] = dict(
        WINDOWS["default_content@active"],
        at_once=tuple((v, h, ("stated", _n), o) for v, h, _, o in WINDOWS["default_content@active"]["at_once"]),
        at_close=tuple((v, h, ("stated", _n), o) for v, h, _, o in WINDOWS["default_content@active"]["at_close"]))
# stated counts past 32 bits: every target reads the same count (no cast truncates it)
for _n in (2 ** 32, 2 ** 32 + 13):
    WINDOWS["default_content@active@%d" % _n] = dict(
        WINDOWS["default_content@active"],
        at_once=tuple((v, h, ("stated", _n), o) for v, h, _, o in WINDOWS["default_content@active"]["at_once"]),
        at_close=tuple((v, h, ("stated", _n), o) for v, h, _, o in WINDOWS["default_content@active"]["at_close"]))
# two tables built to reach a path no policy row's table reaches, read by their cases only:
#   ballot@once      a ballot count met at once, with no landing: a ballot's withdrawal read on that path
#   proposal@others  a table counted over `others` whose opener is a proposer, not the subject of a judgment
WINDOWS["ballot@once"] = {"policy": "moderation_action", "counted": "member", "concluder": "member", "opener_says": None,
                          "at_once": (("for", ("voted", 1, 2, 2, "against"), "all", "carried"),), "silent": None,
                          "at_close": (), "default": "lapsed"}
WINDOWS["proposal@others"] = {"policy": "moderation_action", "counted": "member", "concluder": "member", "opener_says": None,
                              "at_once": (("object", ("more", 1, 2, 2), "others", "refused"),), "silent": None,
                              "at_close": (), "default": "landed"}
SECS = None
MUT = set()            # planted breaks, switched on by a check
BASES = ("all", "others", "opener")


def policy_table():
    """The governance policy table (data/governance_policy.json, the Constitution's manifests/governance_policy.json)."""
    import json
    return json.load(open(os.path.join(ROOT, "data", "governance_policy.json"), encoding="utf-8"))


# ---- a window's table from its policy row --------------------------------------------------------------
class PolicyRefusal(Exception):
    """The row does not give a window's table. `reasons`: (cell, why, other) for every cell that stops it, where why is
        unstated      the cell reads `unstated`
        unknown       a value this function does not read as a window
        disagrees     two cells of the row disagree (other: the second cell)
        no_window     the row carries no window (window_secs 0)
        not_a_window  the row's kind is a counted row, a ranked count or a tally, which no window table closes
        no_cell       the spec needs what no column of the table states (other: what)
        caller        the cell needs a figure the caller states and did not (other: what)"""
    def __init__(self, reasons):
        self.reasons = list(reasons)
        super().__init__("; ".join("%s %s%s" % (c, w, " (%s)" % o if o else "") for c, w, o in self.reasons))


COUNTED_CELLS = ("count_set", "voice", "counted_at", "voices", "target_silent", "changes_set", "target_voice")
NOT_A_WINDOW = ("cosigned", "ranked", "tally")


def spec_from_policy(row, table=None, active=None):
    """The window table (WINDOWS' shape) one row of the policy table gives, every cell read and none defaulted
    but where the Constitution's text states it (cited below). `table`: the policy table the row is of (its
    min_count and window_classes); `active`: the base `active`, which the table does not state as a count: None,
    "within_k" (the room has at most base_law.k members, so the base is N, CC 4.5.13) or ("census", n), the census's
    figure (CC 6.1.9). Raises PolicyRefusal naming every cell that stops it.

    The cells of a two_path row, the only kind it gives a table for:
        counted.count_set  the scope counted, and the concluder's (CC 4.5.13: "Every window of this table closes by
                           two rows of one voice of its count") and the proposer's (CC 3.1.9.2)
        enact_rule         approvals strictly more than the fraction of the base and at least min_count voices (the
                           table's decider); at once, but where the row is irreversible only at the close
        cancel_rule        objections over cancel_over: a fraction at least it, never fewer than min_count, at the
                           close (decider); the strict majority of the others at once (CC 3.3.6.4, "A count that is
                           met")
        floor_rule         with reverse_path, approvals at the close: a fraction as cancel, one_of_n one voice
        at_window          the word of the cancel, the default, a silent target and the proposer's withdrawal
        target_silent      yes: a row of the target inside the window gives at_window (door_text: silent at_window)
        target_voice       yes: the target's own yes is a voice of the floor
        base               standing: the members at the head; active: `active`
        window_secs        the length, which window_class must give too
        corridor           min_count's key; `self` adds the proposer's withdrawal (CC 3.3.6.4, "The proposer's own
                           withdrawal": `refused` at once)
    `landed` is the word of an enact or a floor met (CC 3.1.3, window:{state}; CC 3.3.6.4). The proposal is the
    proposer's approval (CC 3.1.9.2; door_text opener_counts yes)."""
    t = table if table is not None else policy_table()
    why = []
    no = lambda cell, w, other=None: why.append((cell, w, other))
    c = row["counted"]
    val = lambda k: c[k]["value"]
    for k in COUNTED_CELLS:
        if val(k) == "unstated": no("counted." + k, "unstated")
    classes = t["window_classes"]
    if row["window_class"] not in classes: no("window_class", "unknown")
    elif classes[row["window_class"]] != row["window_secs"]: no("window_secs", "disagrees", "window_class")
    if row["window_secs"] == 0: no("window_secs", "no_window")
    for cell in ("enact", "cancel", "floor"):
        prose, rule = row[cell], row[cell + "_rule"]
        if (prose is None) != (rule["kind"] == "none"): no(cell, "disagrees", cell + "_rule")
        elif isinstance(prose, dict) and (rule["kind"] != "fraction" or (prose["num"], prose["den"]) != (rule["num"], rule["den"])):
            no(cell, "disagrees", cell + "_rule")
    toks = val("count_set").split("-")
    incl, excl = toks[0].split("+"), toks[1:]
    if ("less" in row["standing_set"].replace(",", " ").split()) != bool(excl): no("counted.count_set", "disagrees", "standing_set")
    kind = row["kind"]
    if kind in NOT_A_WINDOW: no("kind", "not_a_window")
    elif kind == "mirror": no("kind", "no_cell", "a mirror window's answer words and outcome words")
    elif kind != "two_path": no("kind", "unknown")
    if kind != "two_path":
        raise PolicyRefusal(why)
    # ---- a two_path row
    mc = t["min_count"].get(row["corridor"])
    if mc is None: no("corridor", "unknown")
    if excl or len(incl) != 1: no("counted.count_set", "unknown")
    scope = incl[0]
    if val("voice") == "key" and row["corridor"] != "self": no("counted.voice", "disagrees", "corridor")
    elif val("voice") not in ("person", "key", "unstated"): no("counted.voice", "unknown")
    if val("counted_at") not in ("named", "act", "unstated"): no("counted.counted_at", "unknown")
    if val("voices") not in ("objection", "unstated"): no("counted.voices", "unknown")
    if row["base"] == "standing":
        over = "all"
        if active is not None: no("base", "disagrees", "active")
    elif row["base"] == "active":
        over = "all"
        if active is None: no("base", "caller", "the census figure (CC 6.1.9), or within_k")
        elif active != "within_k": over = ("stated", active[1])
    else:
        over = None; no("base", "unknown")
    no_word = row["at_window"] if row["at_window"] in ("cancelled", "refused") else None
    if no_word is None: no("at_window", "unknown")
    cr, co = row["cancel_rule"], row["cancel_over"]
    cancel = None
    if cr["kind"] == "fraction":
        if co != "base": no("cancel_over", "disagrees", "cancel_rule")
        cancel = ("object", ("atleast", cr["num"], cr["den"], mc), over, no_word)
    elif cr["kind"] == "strict_majority_of_others":
        if co != "others": no("cancel_over", "disagrees", "cancel_rule")
        elif over != "all": no("cancel_over", "disagrees", "base")
        cancel = ("object", "strict", "others", no_word)
    elif cr["kind"] == "none":
        if co != "—": no("cancel_over", "disagrees", "cancel_rule")
    else:
        no("cancel_rule", "unknown")
    er = row["enact_rule"]
    if er["kind"] != "fraction": no("enact_rule", "unknown")
    enact = ("approve", ("more", er.get("num"), er.get("den"), mc), over, "landed")
    fr = row["floor_rule"]
    floor = None
    if fr["kind"] == "fraction": floor = ("approve", ("atleast", fr["num"], fr["den"], mc), over, "landed")
    elif fr["kind"] == "one_of_n": floor = ("approve", "one", over, "landed")
    elif fr["kind"] != "none": no("floor_rule", "unknown")
    silent = None
    if val("target_silent") == "yes":
        if val("changes_set") != "removes": no("counted.target_silent", "disagrees", "counted.changes_set")
        silent = no_word
    tv = val("target_voice") == "yes"
    if tv and val("changes_set") != "adds": no("counted.target_voice", "disagrees", "counted.changes_set")
    if why:
        raise PolicyRefusal(why)
    lone = row["corridor"] == "self"
    at_once = [] if row["irreversible"] else [enact]
    if lone: at_once.append(("withdraw", "one", "opener", no_word))
    at_close = []
    if cancel: (at_once if lone else at_close).append(cancel)
    if row["irreversible"]: at_close.append(enact)
    if row["reverse_path"] and floor: at_close.append(floor)
    return {"policy": row["family"], "counted": scope, "concluder": scope, "opener_says": "approve",
            "at_once": tuple(at_once), "silent": silent, "at_close": tuple(at_close), "default": no_word,
            "target_votes": tv, "secs": row["window_secs"]}


# ---- the act binding: an opener's table through the acts table ------------------------------------------------------
FAMILIES = None    # set by a caller: (family, obj) -> the family's table (spec_from_policy); read with the binding on


def bound_family(p, by):
    """The family the acts table binds opener p to: the act it proposes (`proposes`: act, scope class) over its
    object's kind (seat.policy_for). A `fixed` row names one family, and an opener stating another policy is bound to
    none; a `row` row takes the policy the opener states, if the act may take it. A family of `&` is no window."""
    kind = ST.kind_of(by, p.get("obj"))
    pr = p.get("proposes")
    if kind is None or pr is None: return None
    got = ST.policy_for(pr[0], pr[1], kind)
    if got is None: return None
    pols, choice = got
    stated = p.get("policy")
    if choice == "fixed" and len(pols) == 1 and stated in (None, pols[0]): name = pols[0]
    elif choice == "row" and stated in pols: name = stated
    else: return None
    return None if "&" in name else name


def spec_of(p, P):
    """An opener's table: with FAMILIES set and the binding on (seat.BOUND), the family the acts table binds it to;
    otherwise the table its window name names."""
    if FAMILIES is not None and ST.BOUND:
        fam = bound_family(p, {q["id"]: q for q in P})
        return FAMILIES(fam, p["obj"]) if fam is not None else None
    return WINDOWS.get(p.get("window"))


def is_opener(r):
    """A row that opens a window: an `open` row, or a counted act that names a window."""
    return r["kind"] == "open" or (r["kind"] == "unseat" and r.get("window") in WINDOWS)


def secs(name):
    """The window's length, from the policy table."""
    global SECS
    if SECS is None:
        import json
        fam = json.load(open(os.path.join(ROOT, "data", "governance_policy.json"), encoding="utf-8"))["families"]
        SECS = {f["family"]: f["window_secs"] for f in fam}
    return SECS[WINDOWS[name]["policy"]]


# ---- rows ----------------------------------------------------------------------------------------------
def opener(id, signer, window, obj, head, target=None, names=()):
    return R(id, "open", signer, tuple(names) + tuple(h for h in head if h not in names), window=window, obj=obj,
             head=tuple(head), target=target, slot=("win", id))


def answer(id, signer, p, says, names=()):
    return R(id, "answer", signer, tuple(names) + ((p,) if p not in names else ()), of=p, says=says, on=(("win", p),))


def receipt(id, signer, p, at):
    return R(id, "receipt", signer, (p,), of=p, at=at)


def landing(id, signer, p, rec, says, at, names=()):
    return R(id, "landing", signer, tuple(names) + ((rec,) if rec not in names else ()), of=p, receipt=rec, says=says,
             at=at, cuts=(("win", p),))


# ---- the table -----------------------------------------------------------------------------------------
def table_outcome(spec, p, answers, inside, base, elapsed):
    """The outcome the table gives. answers: rows answering p; inside: rows read for the target's silence;
    base(name) -> the keys counted; elapsed: whether the concluder's two instants span the window."""
    # the key view (seat.KEY_VIEW): an answer counts only where its signer's signature on it counts by the end rule
    # (MUTATION window_key_view_unread: every answer counts)
    kv = ST.KEY_VIEW[-1]
    if kv is not None and "window_key_view_unread" not in ST.MUT:
        answers = [a for a in answers if kv(a["id"], a["signer"])]
    tv = {p.get("target")} if spec.get("target_votes") else set()   # the joiner's own yes is a voice of the floor (CC 3.1.3.2)
    # an answer is its person's (ruled on CIRISConstitution#224: one voice however many live keys sign): a key that is
    # no member answers for the member it is a live key of (seat.person_for); a key with no person stays as it signed,
    # and is no voice of any base. Two answers of one person that differ say two things, and so nothing.
    rows = getattr(base, "rows", None)
    if rows is not None and "persons_unread" not in ST.MUT and not ST.keys_counted(rows, p["obj"]):
        # one member and one voice per person: the bases by person, each answer its signer's person (rep_of; a key that
        # counts as none answers for nobody), the opener its own person
        key_base, NONE = base, ("no person",)
        def base(name):
            return ST.as_persons(key_base(name), rows, p["obj"])
        base.raw = lambda name: ST.as_persons(key_base.raw(name), rows, p["obj"])
        rep = lambda k: ST.rep_of(rows, k) or (NONE, k)
        answers = [dict(a, signer=rep(a["signer"])) for a in answers]
        p = dict(p, signer=rep(p["signer"]))
        tv = {rep(t) for t in tv}
    # the opener's own withdrawal: its signer read as the opener is, a key of no person as itself (no voter needed;
    # MUTATION opener_withdrawal_voter: a key of no person withdraws nothing)
    own = (lambda k: not (isinstance(k, tuple) and k[:1] == (("no person",),))) if "opener_withdrawal_voter" in ST.MUT \
        else (lambda k: True)
    withdrawn = any(a["signer"] == p["signer"] and own(a["signer"]) and a["says"] == "withdraw" for a in answers)
    heard = [a for a in answers if a["signer"] in base("all") | base.raw("moderate") | tv
             and not (a["signer"] == p["signer"] and a["says"] == "withdraw")]
    # a duty holder's single-signature answer is what that key said: its vote is moot
    duty = {value: over for value, how, over, _ in spec["at_once"] if how == "one" and over not in BASES}
    acted = {a["signer"] for a in heard if a["says"] in duty and a["signer"] in base.raw(duty[a["says"]])}
    if "vote_beside_answer" in MUT: acted = set()
    said = K.group([a for a in heard if a["signer"] not in acted or a["says"] in duty], "signer", "one", "says")
    if spec["opener_says"]: said.setdefault(p["signer"], spec["opener_says"])       # a voice that says two things says nothing
    def count_met(value, how, over, floor=False):
        if over == "opener": return withdrawn if value == "withdraw" else said.get(p["signer"]) == value
        stated = over[1] if isinstance(over, tuple) and over[0] == "stated" else None
        if stated is not None and "stated_truncates" in MUT: stated %= 2 ** 32   # MUTATION: a 32-bit cast of the count
        # the voices of the stated base are the members at the head (MUTATION stated_voices_others: the opener apart)
        if stated is not None: over = "others" if "stated_voices_others" in MUT else "all"
        # a count (a fraction, a floor) leaves the agents out; a clause one holder's act resolves reads them
        keys = voice = base.raw(over) if how == "one" else base(over)
        # MUTATION overturn_whole_roster: the opener's signer is no voice and is still counted over
        if over == "others" and "overturn_whole_roster" in MUT: keys = base("all")
        # the size counted over: the stated count, never fewer than the members at the head
        # (MUTATION stated_shrinks: the stated count read even where it is smaller)
        size = len(keys) if stated is None else (stated if "stated_shrinks" in MUT else max(stated, len(keys)))
        yes = K.group([{"k": s} for s, v in said.items() if v == value and (s in voice or (floor and s in tv and value == "approve"))], None, "count", "k")
        if isinstance(how, tuple):               # a threshold read off the policy table
            kind, num, den, least = how[:4]      # ("atleast", n, d, min): >= max(min, ceil(n*N/d)); ("more", n, d, min): > n/d and >= min
            if kind == "voted":                  # ("voted", n, d, min, against): > n/d of those of the base who voted, and >= min
                no = K.group([{"k": s} for s, v in said.items() if v == how[4] and s in voice], None, "count", "k")
                return yes * den > num * (yes + no) and yes >= least
            if kind == "atleast": return size > 0 and yes >= max(least, -(-num * size // den))   # nothing is met by nobody
            return yes * den > num * size and yes >= least
        return yes >= 1 if how == "one" else 2 * yes > size
    for value, how, over, out in spec["at_once"]:
        if count_met(value, how, over): return out
    if not elapsed: return "open"
    if spec["silent"] and K.sel(inside, signer=p.get("target")): return spec["silent"]
    for value, how, over, out in spec["at_close"]:
        if count_met(value, how, over, floor=True): return out
    return spec["default"]


def _base(rows, past, p, spec=None):
    spec = spec if spec is not None else WINDOWS[p["window"]]
    cache = {}
    def base(name):
        if name not in cache:
            scope = spec["counted"] if name in ("all", "others") else name
            # a count of the room is by person: an agent's key is no voice and is not counted over (seat.counted_keys); the
            # key a lone removal removes is an agent's, so it is apart from the lift of its own removal
            # in no count means out of the base for every scope a clause reads, `moderate` included (the ruling of
            # 2026-11-25; MUTATION scope_keeps_agents: a named scope keeps its agents)
            m = ST.members_at(rows, past, p["obj"], p["head"], scope) if name not in ("all", "others") and "scope_keeps_agents" in MUT \
                else ST.counted_keys(rows, past, p["obj"], p["head"], scope)[0]
            cache[name] = m - {p["signer"]} if name == "others" else m
        return cache[name]

    def raw(name):
        """The keys a clause one holder's act resolves (`one`) reads over a named scope: its holders, agents
        included (an agent acts under its seat by the acts one signature resolves; the ruling of 2026-11-25)."""
        if name in ("all", "others", "opener") or "one_leaves_agents" in MUT: return base(name)
        if ("raw", name) not in cache:
            cache[("raw", name)] = ST.members_at(rows, past, p["obj"], p["head"], name)
        return cache[("raw", name)]
    base.raw = raw
    base.rows = rows
    return base


def elapsed(landing_, rec, p, spec=None):
    """The concluder's own two instants span the window. With either instant missing it has not elapsed. A table built
    from its row carries its own length (`secs`)."""
    a, b = landing_.get("at"), rec.get("at")
    n = spec["secs"] if spec is not None and "secs" in spec else secs(p["window"])
    return a is not None and b is not None and a - b >= n


def ballot_words(spec):
    """The words a ballot says: the value and the `against` of each clause counted over those who voted."""
    return {w for value, how, _, _ in spec["at_once"] + spec["at_close"] if isinstance(how, tuple) and how[0] == "voted"
            for w in (value, how[4])}


def unwithdrawn(spec, answers, rows):
    """The answers less each ballot its own signer withdrew by a row among `rows` (CIRISConstitution#221: one ballot a
    person, folded as `ballot:moderator`; a withdrawal of one's own row, CC 2.4.1.1 rule 1)."""
    if "ballot_withdrawal_unread" in MUT: return answers
    # MUTATION any_word_withdrawn: every answer is read as withdrawn, not only a ballot
    words = ballot_words(spec) if "any_word_withdrawn" not in MUT else {a["says"] for a in answers}
    # a cosigner's withdrawal of a ballot concludes (seat.seat_rule reads every signer of the row); it is no withdrawal
    # of the ballot: only the ballot's own signer's is (MUTATION withdrawal_id_only: the id alone matched)
    own = (lambda x: None) if "withdrawal_id_only" in MUT else (lambda x: x["signer"])
    ws = [w for w in rows if w["kind"] == "withdraw"]
    if "withdrawal_revives" in MUT:                 # MUTATION: a withdrawal its signer withdrew withdraws nothing
        gone = {(w["target"], w["signer"]) for w in ws}
        ws = [w for w in ws if (w["id"], w["signer"]) not in gone]
    wd = {(w["target"], own(w)) for w in ws}
    return [a for a in answers if a["says"] not in words or (a["id"], own(a)) not in wd]


def author_apart(spec):
    """No clause counts the opener's signer: every counted clause is over `others` (the members' check). The author is
    then no concluder of the window (CIRISConstitution#221, W2). The assumption: a table every counted clause of which is
    over `others` is a judgment of its opener's signer (the overturn's act opens its own window, so its signer is the
    act's author). Nothing ties the opener to an act: a table over `others` whose opener is a proposer and not the
    subject also leaves the opener's signer no concluder (a case below shows it)."""
    if "author_concludes" in MUT: return False
    over = [c[2] for c in spec["at_once"] + spec["at_close"] if c[2] != "opener"]
    return bool(over) and all(o == "others" for o in over)


def voices_of(answers, p, past):
    """The answers that are voices: an approval that has the proposer's withdrawal in its past approves nothing."""
    wd = [a["id"] for a in answers if a["signer"] == p["signer"] and a["says"] == "withdraw"]
    return [a for a in answers if not (a["says"] == "approve" and any(past(w, a["id"]) for w in wd))]


def rule_why(r, P, past):
    """rule, telling a row that waits from one that concludes nothing: True, False, or ("waits", x) (seat.seat_rule_why).
    A window row reads its concluded ancestors, which no arrival changes, so it waits only where the seat's rule does:
    a row that is no window row, or an opener that is an offer or an unseat."""
    k = r["kind"]
    if k not in ("open", "answer", "receipt", "landing") and not is_opener(r):
        return ST.seat_rule_why(r, P, past)
    if is_opener(r) and k != "open":
        w = ST.seat_rule_why(r, P, past)
        if w is not True: return w
    return bool(rule(r, P, past))


def rule(r, P, past):
    """The conclusion rule: window rows here, every other row by seat.seat_rule."""
    k = r["kind"]
    if k not in ("open", "answer", "receipt", "landing") and not is_opener(r):
        return ST.seat_rule(r, P, past)
    by = {q["id"]: q for q in P}
    if is_opener(r):
        w = spec_of(r, P)                                      # the opener's signer holds the opener's scope, by default the counted one
        if w is None: return False
        if k != "open" and not ST.seat_rule(r, P, past): return False     # an act that opens its own window: validly made, by the seat
        # an opening names the newest counted changes over its object in its own past, and is counted there (H1;
        # MUTATION window_opener_old_head: an opening at an older head is read there)
        if k == "open" and "window_opener_old_head" not in ST.MUT \
                and ST.newer_head_in_past(r.get("head", ()), None, P, past, r["obj"], ST.signers(r)): return False
        return r["signer"] in ST.members_at(P, past, r["obj"], r["head"], w.get("opener", w["counted"]))
    p = by.get(r["of"])
    if p is None or not is_opener(p): return False
    if k == "answer": return True                              # whether its voice counts is read against the roster at p's head
    spec = spec_of(p, P)
    if spec is None: return False
    base = _base(P, past, p, spec)
    if r["signer"] not in ST.members_at(P, past, p["obj"], p["head"], spec["concluder"]): return False
    if r["signer"] == p["signer"] and author_apart(spec): return False     # out of every count, so no concluder of it
    if k == "receipt":
        # a receipt puts no row of the target before the window: none in its past that the opener's past does not hold
        t = p.get("target")
        return t is None or not any(q["signer"] == t and q["id"] != p["id"] and not past(q["id"], p["id"]) for q in P)
    rec = by.get(r["receipt"])
    if rec is None or rec["kind"] != "receipt" or rec["signer"] != r["signer"] or rec["of"] != p["id"]: return False
    answers = voices_of(unwithdrawn(spec, K.sel(P, kind="answer", of=p["id"]), P), p, past)
    inside = [q for q in P if q["id"] != rec["id"] and not past(q["id"], rec["id"])]
    return r["says"] == table_outcome(spec, p, answers, inside, base, elapsed(r, rec, p, spec))


# ---- derived: the outcome of a window under each rule ----------------------------------------------------
def outcome(S, pid, how, by_arrival=False, checkpoint=False):
    """how: void | contest | recount. Returns the outcome, "open" (no landing counts yet) or "contested"."""
    p = S.by.get(pid)
    if p is None or not S.C.get(pid): return "none"
    spec = spec_of(p, S.Cs)
    if spec is None: return "none"
    Ls = K.sel(S.Cs, kind="landing", of=pid)
    if not Ls and "landing_only" in MUT: return "open"
    if Ls and how == "void":
        C = CUT.Cut(S)                                          # the landing is a cut on p's slot; only landings speak on it
        st = {L["id"]: C.status(L) for L in Ls}
        said = [{"v": L["says"]} for L in K.frontier(S.anc, [L for L in Ls if st[L["id"]] == "counts"])]
        if "contested" in st.values() or not said: return "contested"
        return K.group(said, None, "one", "v") or "contested"
    past = lambda a, b: a in S.anc[b]
    base = _base(S.Cs, past, p, spec)
    pos = {r["id"]: i for i, r in enumerate(S.rows)}
    late = lambda r: False
    if how == "recount" or not Ls:
        C = CUT.Cut(S)
        # the rows that ended a seat over the object, with the keys each ended
        gone = [(frozenset(u["to"]), u) for u in K.sel(S.Cs, kind="unseat") if u["obj"] == p["obj"] and C.counts(u)]
        for w in K.sel(S.Cs, kind="withdraw"):
            # a withdrawal that names a scope ends the signer's seat on the roster only where it ends its stay as a
            # member over the object (seat.stay_ends): one naming a duty lays that seat down, and the key's voice
            # stands; the older presentation's founding seat of scope `duty` holds `member`, so laying it down ends
            # the stay; one naming `member` of an offer that seats no member ends nothing (MUTATION
            # window_scope_roster_only: the scope taken at its word, a roster scope departs and any other does not)
            if w.get("scope") is not None:
                if "window_scope_roster_only" in MUT:
                    if w["scope"] not in ST.ROSTER_SEATS: continue
                elif not any(g == p["obj"] for _, _, g in ST.stay_ends(
                        [w], S.by, lambda a, w: bool(S.C.get(a["id"])) and a["id"] in S.anc[w["id"]])): continue
            o = S.by.get(w["target"])
            if o is not None and o["kind"] == "offer" and o["obj"] == p["obj"]:
                gone.append((frozenset({w["signer"]}) if w["signer"] in o["to"] else frozenset(o["to"]), w))
        cps = CP.checkpoints(S, C, p["obj"], group=True) if checkpoint else []   # off by default: see the module's head
        late = lambda r: any(r["signer"] in ks and r["id"] not in S.anc[x["id"]] for ks, x in gone) or CP.stale_answer(S, cps, p, r)
    if not Ls:
        # no landing has concluded: a count that is met needs no clock and no concluder, so the table's at-once
        # outcome over the answers held is the outcome; short of it the window is open
        held = [a for a in K.sel(S.Cs, kind="answer", of=pid) if not late(a)]
        # (MUTATION no_landing_withdrawal_unread: a ballot's withdrawal not read on this path)
        if "no_landing_withdrawal_unread" not in MUT: held = unwithdrawn(spec, held, [w for w in S.Cs if not late(w)])
        held = voices_of(held, p, past)
        return table_outcome(spec, p, held, [], base, False)
    said = []
    for L in K.frontier(S.anc, Ls):                             # a landing that a later landing names is answered by it
        # MUTATION by_arrival: "concurrent" read as "arrived after the landing", by list position
        conc = [r for r in S.Cs if (pos[r["id"]] > pos[L["id"]] and L["id"] not in S.anc[r["id"]]) if by_arrival] if by_arrival else \
               [r for r in S.Cs if S.concurrent(r["id"], L["id"])]
        conc = [r for r in conc if not late(r)]
        ans = [r for r in K.sel(conc, kind="answer", of=pid) if r["signer"] in base("all") | base.raw("moderate") | ({p.get("target")} if spec.get("target_votes") else set())]
        tgt = K.sel(conc, signer=p.get("target")) if spec["silent"] else []
        if how == "contest":
            said.append({"v": "contested" if ans or tgt else L["says"]})
        else:
            rec = S.by[L["receipt"]]
            mine = [q for q in S.Cs if q["id"] in S.anc[L["id"]]]
            inside = [q for q in mine if q["id"] != rec["id"] and q["id"] not in S.anc[rec["id"]]] + tgt
            # a withdrawal of a ballot concurrent with the landing is recounted with it, as an answer is
            # (MUTATION withdrawal_not_recounted: only the landing's own past is read for withdrawals)
            wrows = mine + ([] if "withdrawal_not_recounted" in MUT else conc)
            heard = unwithdrawn(spec, K.sel(mine, kind="answer", of=pid) + ans, wrows)
            again = table_outcome(spec, p, voices_of(heard, p, past), inside, base, elapsed(L, rec, p, spec))
            said.append({"v": L["says"] if again == L["says"] else "contested"})
    if how == "recount" and any(x["v"] != "contested" for x in said):
        said = [x for x in said if x["v"] != "contested"]       # a landing that does not stand is no voice against one that does
    return K.group(said, None, "one", "v") or "contested"


RULES = ("void", "contest", "recount")


def outcomes(S, pid, **kw):
    return {h: outcome(S, pid, h, **kw) for h in RULES}


# ---- the five windows, and the adversary in each --------------------------------------------------------
DAY = 86400


def self_world():
    g = ST.offer("g", "d1", ("d1", "d2", "d3"), "self", "@", "self", cosigners=("d2", "d3"))
    W = secs("self_roster_evict")
    thief_p = opener("p", "d3", "self_roster_evict", "g", ("g",), target="d1")       # the thief holds d3
    own_p = opener("p", "d1", "self_roster_evict", "g", ("g",), target="d2")         # the owner holds d1 only
    q_p = opener("p", "d1", "self_roster_evict", "g", ("g",), target="d3")           # the owner holds d1 and d2
    cases = [
        # name, rows, who gains, property read, the outcome the property needs
        ("false landing: the thief (one device of three) lands an eviction of the owner's device; the owner's two devices objected and the landing leaves them unnamed",
         [g, thief_p, receipt("r", "d3", "p", 0), answer("o1", "d1", "p", "object"), answer("o2", "d2", "p", "object"),
          landing("L", "d3", "p", "r", "landed", W)], "thief cannot evict alone", "not landed"),
        ("false landing, stated falsely: the same landing naming the objections",
         [g, thief_p, receipt("r", "d3", "p", 0), answer("o1", "d1", "p", "object"), answer("o2", "d2", "p", "object"),
          landing("L", "d3", "p", "r", "landed", W, ("o1", "o2"))], "thief cannot evict alone", "not landed"),
        ("false landing, early: the thief lands before its own window has run",
         [g, thief_p, receipt("r", "d3", "p", 0), landing("L", "d3", "p", "r", "landed", W - 1)], "thief cannot evict alone", "not landed"),
        ("withheld row: the target used its device in the window (a row that is no objection) and a relay kept it from everyone until after the landing",
         [g, thief_p, receipt("r", "d3", "p", 0), R("n1", "note", "d1", ("g",)), landing("L", "d3", "p", "r", "landed", W)],
         "thief cannot evict alone", "not landed"),
        ("the owner is away the whole window and signs nothing; the thief lands",
         [g, thief_p, receipt("r", "d3", "p", 0), landing("L", "d3", "p", "r", "landed", W)], "(the stated residual: an absent owner looks lost)", None),
        ("objection signed just after, naming the landing: the owner returns and objects honestly",
         [g, thief_p, receipt("r", "d3", "p", 0), landing("L", "d3", "p", "r", "landed", W), answer("o1", "d1", "p", "object", ("L",)),
          answer("o2", "d2", "p", "object", ("L",))], "(what an honest late objection is worth)", None),
        ("objection signed just after, leaving the landing unnamed: the owner returns and objects with both devices",
         [g, thief_p, receipt("r", "d3", "p", 0), landing("L", "d3", "p", "r", "landed", W), answer("o1", "d1", "p", "object"),
          answer("o2", "d2", "p", "object")], "thief cannot evict alone", "not landed"),
        ("a second landing naming both: after the thief's landing, the owner's second device lands 'refused', naming the landing and the objections",
         [g, thief_p, receipt("r", "d3", "p", 0), answer("o1", "d1", "p", "object"), answer("o2", "d2", "p", "object"),
          landing("L", "d3", "p", "r", "landed", W), receipt("r2", "d2", "p", 0), landing("L2", "d2", "p", "r2", "refused", 0, ("L", "o1", "o2"))],
         "a row naming both decides", "refused"),
        ("lost device: the owner holds one of three and evicts a lost device, which signs nothing",
         [g, own_p, receipt("r", "d1", "p", 0), landing("L", "d1", "p", "r", "landed", W)], "lost device cannot veto", "landed"),
        ("silent stolen device: the same eviction; the target is held by a thief who signs a row after the landing and leaves it unnamed",
         [g, own_p, receipt("r", "d1", "p", 0), landing("L", "d1", "p", "r", "landed", W), R("n2", "note", "d2", ("g",))],
         "(a device that can still sign is not lost)", None),
        ("quorum: the owner's two devices evict the stolen one at once; the thief objects, concurrent with the landing",
         [g, q_p, answer("a2", "d2", "p", "approve"), receipt("r", "d1", "p", 0), landing("L", "d1", "p", "r", "landed", 0, ("a2",)),
          answer("o3", "d3", "p", "object")], "an active thief is evicted by the count", "landed"),
        ("the count with no landing: the owner's two devices approve the eviction of the stolen one and nobody lands",
         [g, q_p, answer("a2", "d2", "p", "approve")], "a count that is met needs no clock and no concluder", "landed"),
        ("the others refuse with no landing: the thief proposes and the owner's two devices object",
         [g, thief_p, answer("o1", "d1", "p", "object"), answer("o2", "d2", "p", "object")], "thief cannot evict alone", "refused"),
        ("one approval short of the count, no landing: nothing has changed",
         [g, thief_p], "(a proposal alone is open)", "open"),
        ("the proposer withdraws its open proposal",
         [g, own_p, answer("wd", "d1", "p", "withdraw")], "the proposer may withdraw its own open proposal", "refused"),
        ("a withdrawal beside a majority's approval, neither naming the other",
         [g, q_p, answer("a2", "d2", "p", "approve"), answer("wd", "d1", "p", "withdraw")], "a count once met is final", "landed"),
        ("an approval that names the withdrawal",
         [g, q_p, answer("wd", "d1", "p", "withdraw"), answer("a2", "d2", "p", "approve", ("wd",))],
         "nobody approves a withdrawn proposal", "refused"),
        ("a withdrawal in the lone landing's past: the landing states 'landed' over it",
         [g, own_p, receipt("r", "d1", "p", 0), answer("wd", "d1", "p", "withdraw"), landing("L", "d1", "p", "r", "landed", W, ("wd",))],
         "a withdrawn proposal does not land", "not landed"),
        ("a withdrawal concurrent with the lone landing",
         [g, own_p, receipt("r", "d1", "p", 0), landing("L", "d1", "p", "r", "landed", W), answer("wd", "d1", "p", "withdraw")],
         "a withdrawn proposal does not land", "not landed"),
        ("a withdrawal that names the lone landing: it came after",
         [g, own_p, receipt("r", "d1", "p", 0), landing("L", "d1", "p", "r", "landed", W), answer("wd", "d1", "p", "withdraw", ("L",))],
         "a landed eviction is not withdrawn", "landed"),
        ("another key signs a withdrawal of the proposal",
         [g, own_p, answer("wd", "d3", "p", "withdraw")], "only the proposer withdraws", "open"),
    ]
    return "self roster, lone eviction (24 h, target silent)", cases


def add_world():
    g = ST.offer("g", "d1", ("d1", "d2", "d3"), "self", "@", "self", cosigners=("d2", "d3"))
    W = secs("self_roster_add")
    p = opener("p", "d1", "self_roster_add", "g", ("g",), target="d4")               # the owner adds a new device
    thief_p = opener("p", "d3", "self_roster_add", "g", ("g",), target="t9")         # the thief adds a key of its own
    cases = [
        ("the count with no landing: two of three approve the new key",
         [g, p, answer("a2", "d2", "p", "approve")], "a count that is met needs no clock and no concluder", "landed"),
        ("a proposal alone: the key of an addition is not seated while the window is open",
         [g, p], "nothing a proposal would change has changed while it is open", "open"),
        ("the lone path: nobody answers in 24 h and the proposer lands",
         [g, p, receipt("r", "d1", "p", 0), landing("L", "d1", "p", "r", "landed", W)], "one key adds another after the window", "landed"),
        ("false landing, early: the thief lands its own key before its window has run",
         [g, thief_p, receipt("r", "d3", "p", 0), landing("L", "d3", "p", "r", "landed", W - 1)], "thief cannot add alone at once", "not landed"),
        ("the others refuse: the thief proposes its own key and the owner's two devices object, no landing",
         [g, thief_p, answer("o1", "d1", "p", "object"), answer("o2", "d2", "p", "object")], "thief cannot add alone", "refused"),
        ("false landing: the thief lands its key at the close, leaving the two objections unnamed",
         [g, thief_p, receipt("r", "d3", "p", 0), answer("o1", "d1", "p", "object"), answer("o2", "d2", "p", "object"),
          landing("L", "d3", "p", "r", "landed", W)], "thief cannot add alone", "not landed"),
        ("one objection of two others is not a refusal: the thief lands at the close over it",
         [g, thief_p, receipt("r", "d3", "p", 0), answer("o1", "d1", "p", "object"), landing("L", "d3", "p", "r", "landed", W, ("o1",))],
         "(the stated residual: one device of the owner's objecting does not stop a lone addition)", None),
        ("the key being added signs rows in the window: an addition has no target's silence",
         [g, p, receipt("r", "d1", "p", 0), R("n4", "note", "d4", ("g",)), landing("L", "d1", "p", "r", "landed", W)],
         "the added key's own rows do not refuse it", "landed"),
        ("the proposer withdraws the addition",
         [g, p, answer("wd", "d1", "p", "withdraw")], "the proposer may withdraw its own open proposal", "refused"),
    ]
    return "self roster, lone addition (24 h)", cases


def admitted(k, by=("m1", "m3"), founders=("m1", "m2", "m3")):
    """A room of three founding duty holders, and key k admitted to its roster by two of them (k cosigning: its own
    yes). A duty seat stands only on a member (seat.py, `member`), so a world that confers one on k admits k first and
    counts the conferral over the admission."""
    g = ST.offer("g", founders[0], founders, "duty", "@", "self", cosigners=founders[1:])     # three duty holders (CC 4.5.4)
    am = ST.offer("am", by[0], k, "member", "g", "group", ("g",), head=("g",), policy="community_invite", cosigners=tuple(by[1:]) + (k,))
    return g, am


def moderation_world():
    g, am = admitted("MOD")                                                    # MOD is a member, then a moderator
    md = ST.offer("md", "m1", "MOD", "moderate", "g", "group", ("am",), head=("am",), policy="duty_confer", counted="duty",
                  cosigners=("m3", "MOD"))                                     # two of the three confer, MOD accepting
    W = secs("moderation_fallback")
    p = opener("p", "m2", "moderation_fallback", "g", ("md",))
    # four members at the head (m1, m2, m3 and MOD); the count at the close is over the members who voted
    acts = [answer("x1", "m1", "p", "for"), answer("x2", "m2", "p", "for"), answer("x3", "m3", "p", "for")]
    xs = ("x1", "x2", "x3")
    A = answer("A", "MOD", "p", "answered")
    base = [g, am, md, p, receipt("r", "m2", "p", 0)] + acts
    L = landing("L", "m2", "p", "r", "fallback", W, xs)
    cases = [
        ("false landing: a member lands the members' moderation; the moderator had answered and the landing leaves the answer unnamed",
         base + [A, L], "present moderator is not overridden", "not fallback"),
        ("false landing, stated falsely: the same landing naming the moderator's answer",
         base + [A, landing("L", "m2", "p", "r", "fallback", W, xs + ("A",))], "present moderator is not overridden", "not fallback"),
        ("false landing, no count: one member lands the fallback alone",
         [g, am, md, p, receipt("r", "m2", "p", 0), landing("L", "m2", "p", "r", "fallback", W)], "the fallback needs the members' majority", "not fallback"),
        ("withheld answer: an honest member lands; a relay had kept the moderator's answer from the room",
         base + [A, L], "present moderator is not overridden", "not fallback"),
        ("a second landing naming both: another member lands 'answered', naming the first landing and the moderator's answer",
         base + [A, L, receipt("r2", "m1", "p", 0), landing("L2", "m1", "p", "r2", "answered", 0, ("L", "A"))],
         "a row naming both decides", "answered"),
        ("absent moderator: nobody answers in 48 h and the members' majority acts",
         base + [L], "the fallback works when the moderator is absent", "fallback"),
        ("answer signed just after, naming the landing: the moderator returns and answers honestly",
         base + [L, answer("A", "MOD", "p", "answered", ("L",))], "(what an honest late answer is worth)", None),
        ("answer signed just after, leaving the landing unnamed: the moderator returns late",
         base + [L, A], "(a late moderator against the members' act)", None),
        ("a moderator's seat conferred on a key that is not a member: its answer is no moderator's answer, and the members' majority lands",
         [g, dict(md, names=("g",), head=("g",)), dict(p), receipt("r", "m2", "p", 0), acts[0], acts[1], A,
          landing("L", "m2", "p", "r", "fallback", W, ("x1", "x2"))],
         "a duty seat stands only on a member", "fallback"),
        ("false landing, short of the count: one member acts and another votes against, and one of them lands the fallback",
         [g, am, md, p, receipt("r", "m2", "p", 0), acts[0], answer("n2", "m2", "p", "against"),
          landing("L", "m2", "p", "r", "fallback", W, ("x1", "n2"))],
         "the fallback needs the members' majority", "not fallback"),
    ]
    # a room of four founders and MOD, admitted and then made moderator: the count is over the members who voted,
    # for (`for`) or against (`against`), floor two voices; a silent member (MOD among them) is not counted over
    g4, am4 = admitted("MOD", by=("m1", "m3", "m4"), founders=("m1", "m2", "m3", "m4"))
    md4 = ST.offer("md", "m1", "MOD", "moderate", "g", "group", ("am",), head=("am",), policy="duty_confer", counted="duty",
                   cosigners=("m3", "m4", "MOD"))
    b4 = [g4, am4, md4, p, receipt("r", "m2", "p", 0)]
    acts = acts[:1] + acts[2:]                                                 # x1 and x3: m2 lands, and votes against below
    n2, n4 = answer("n2", "m2", "p", "against"), answer("n4", "m4", "p", "against")
    fb = lambda *names: landing("L", "m2", "p", "r", "fallback", W, names)
    cases += [
        ("five members, two vote for and three are silent: the landing names the two votes",
         b4 + acts + [fb("x1", "x3")], "a silent member is not counted over", "fallback"),
        ("five members, one votes for and nobody against",
         b4 + acts[:1] + [fb("x1")], "never fewer than two voices", "not fallback"),
        ("five members, two vote for and two against: the landing names all four",
         b4 + acts + [n2, n4, fb("x1", "x3", "n2", "n4")], "a strict majority of those who voted", "not fallback"),
        ("five members, two vote for and one against",
         b4 + acts + [n2, fb("x1", "x3", "n2")], "a strict majority of those who voted", "fallback"),
        ("withheld votes: two vote for and the landing names them; two votes against were kept from the lander",
         b4 + acts + [n2, n4, fb("x1", "x3")], "a strict majority of those who voted", "not fallback"),
        ("a member votes both for and against, beside one vote for",
         b4 + acts + [answer("n1", "m1", "p", "against"), fb("x1", "x3", "n1")], "a voice that says two things says nothing", "not fallback"),
        ("two keys off the roster vote against two members' votes for",
         b4 + acts + [answer("z1", "z", "p", "against"), answer("z2", "y", "p", "against"), fb("x1", "x3", "z1", "z2")],
         "only a member's vote is counted", "fallback"),
        ("a key conferred `moderate` while it is no member votes for, beside one member's vote",
         [g4, dict(md4, names=("g",), head=("g",)), p, receipt("r", "m2", "p", 0)] + acts[:1] + [answer("xM", "MOD", "p", "for"), fb("x1", "xM")],
         "a duty seat stands only on a member, and a non-member's vote is no vote", "not fallback"),
        ("a moderator who is also a member answers and votes for, beside one vote for: no landing",
         b4 + acts + [answer("A1", "m1", "p", "answered")], "its act answers and its vote is moot", "answered"),
        ("the same, and a member lands the fallback over it, naming all three",
         b4 + acts + [answer("A1", "m1", "p", "answered"), fb("x1", "x3", "A1")], "its act answers and its vote is moot", "not fallback"),
        ("after the fallback has landed, the moderator answers, naming the landing",
         b4 + acts + [n2, fb("x1", "x3", "n2"), answer("A", "MOD", "p", "answered", ("L",))],
         "a moderator's act after the fallback has landed does not reopen the window", "fallback"),
    ]
    # a member's vote is a ballot of `ballot:moderation_action`, `for` or `against`, one ballot a person, folded as
    # `ballot:moderator` is (CIRISConstitution#221)
    n1, wd = answer("n1", "m1", "p", "against"), lambda i, who, t, names=(): ST.withdraw(i, who, t, names)
    B221 = "CIRISConstitution#221: the fallback vote"
    cases += [
        ("two members answer in the word `act`, which is no ballot, and a member lands the fallback naming both",
         b4 + [answer("y1", "m1", "p", "act"), answer("y3", "m3", "p", "act"), fb("y1", "y3")],
         B221 + ", a ballot says `for` or `against`", "not fallback"),
        ("a member's two ballots for agree, and nobody else votes: one ballot",
         b4 + acts[:1] + [answer("x1b", "m1", "p", "for"), fb("x1", "x1b")], B221 + ", agreeing ballots are one ballot", "not fallback"),
        ("a member's two ballots for agree, beside a second member's ballot for: two voices",
         b4 + acts + [answer("x1b", "m1", "p", "for"), fb("x1", "x1b", "x3")], B221 + ", agreeing ballots are one ballot", "fallback"),
        ("a member votes for and against and withdraws the vote against, beside a second vote for: the landing names the four",
         b4 + acts + [n1, wd("w1", "m1", "n1"), fb("x1", "x3", "n1", "w1")], B221 + ", disagreeing ballots are none until a withdrawal", "fallback"),
        ("a member withdraws its vote for, beside a second vote for: the landing names the three",
         b4 + acts + [wd("w1", "m1", "x1"), fb("x1", "x3", "w1")], B221 + ", a ballot its signer withdrew is no vote", "not fallback"),
        ("another member signs a withdrawal of a member's vote for: the landing names the three",
         b4 + acts + [wd("w1", "m4", "x1"), fb("x1", "x3", "w1")], B221 + ", only the voter withdraws its ballot", "fallback"),
        ("a member withdraws its vote for concurrent with the landing that counted it",
         b4 + acts + [fb("x1", "x3"), wd("w1", "m1", "x1")], B221 + ", a withdrawal concurrent with the landing is recounted", "not fallback"),
        ("a member's vote for is cosigned by another member, who withdraws it: the landing names the three",
         b4 + [acts[0], dict(acts[1], cosigners=("m1",)), wd("w1", "m1", "x3"), fb("x1", "x3", "w1")],
         B221 + ", a cosigner's withdrawal (it concludes) withdraws no ballot of another signer", "fallback"),
        ("a member withdraws its vote for and then withdraws that withdrawal, the landing naming all",
         b4 + acts + [wd("w1", "m1", "x1"), wd("w2", "m1", "w1"), fb("x1", "x3", "w1", "w2")],
         B221 + ", a withdrawal of a withdrawal revives no ballot", "not fallback"),
        ("a member withdraws its vote for and votes for again, beside a second vote for: the landing names the four",
         b4 + acts + [wd("w1", "m1", "x1"), answer("x1b", "m1", "p", "for", ("w1",)), fb("x1", "x3", "w1", "x1b")],
         B221 + ", withdraws, then votes again: one ballot", "fallback"),
        ("a ballot count met at once (ballot@once): two vote for and one of them withdraws its vote, no landing",
         [g4, am4, md4, opener("p", "m2", "ballot@once", "g", ("md",))] + acts + [wd("w1", "m1", "x1")],
         B221 + ", a ballot's withdrawal is read with no landing too", "open"),
        ("a ballot count met at once (ballot@once): two vote for, no landing",
         [g4, am4, md4, opener("p", "m2", "ballot@once", "g", ("md",))] + acts, B221 + ", a ballot count met at once", "carried"),
        ("a member withdraws its vote for after the landing, naming it",
         b4 + acts + [fb("x1", "x3"), wd("w1", "m1", "x1", ("L",))], B221 + ", a withdrawal that names the landing came after it", "fallback"),
        ("a key with no seat at the head lands the fallback over two votes for",
         b4[:4] + [receipt("rz", "z", "p", 0)] + acts + [landing("L", "z", "p", "rz", "fallback", W, ("x1", "x3"))],
         "CIRISConstitution#221: the fallback's landing, a signed row of a member at the head the opener names", "not fallback"),
        ("the moderator, a member who did not answer, lands the fallback over two votes for",
         b4 + acts + [receipt("rM", "MOD", "p", 0), landing("L", "MOD", "p", "rM", "fallback", W, ("x1", "x3"))],
         "CIRISConstitution#221: the fallback's landing is signed by any member", "fallback"),
        ("the proposer lands the fallback over two votes for, neither its own",
         [g4, am4, md4, opener("p", "m4", "moderation_fallback", "g", ("md",)), receipt("r", "m4", "p", 0)] + acts + [landing("L", "m4", "p", "r", "fallback", W, ("x1", "x3"))],
         "CIRISConstitution#221: the fallback's landing is signed by any member", "fallback"),
    ]
    return "moderation fallback (48 h, absent moderator, a majority of the members who voted)", cases


def halt_world():
    g = ST.offer("g", "h1", ("h1", "h2", "h3"), "holder", "@", "self", cosigners=("h2", "h3"))
    W = secs("halt_fuse")
    p = opener("p", "h1", "halt_fuse", "g", ("g",))
    c2 = answer("c2", "h2", "p", "confirm")
    cases = [
        ("false landing: the halting holder lands 'confirmed' with no other voice",
         [g, p, receipt("r", "h1", "p", 0), landing("L", "h1", "p", "r", "confirmed", W)], "one holder cannot keep agents stopped alone", "not confirmed"),
        ("the lone halt lapses: nobody confirms; another holder lands the lapse at the fuse",
         [g, p, receipt("r", "h2", "p", 0), landing("L", "h2", "p", "r", "lapsed", W)], "one holder cannot keep agents stopped alone", "lapsed"),
        ("objection signed just after, unnamed: the lapse lands; the halting holder signs a further confirm and leaves the landing unnamed",
         [g, p, receipt("r", "h2", "p", 0), landing("L", "h2", "p", "r", "lapsed", W), answer("c1", "h1", "p", "confirm")],
         "one holder cannot keep agents stopped alone", "lapsed"),
        ("false landing: a holder lands 'lapsed' on a halt a strict majority confirmed, leaving the confirm unnamed",
         [g, p, c2, receipt("r", "h3", "p", 0), landing("L", "h3", "p", "r", "lapsed", W)], "one holder cannot lift a confirmed halt alone", "not lapsed"),
        ("withheld confirm: an honest holder lands the lapse; a relay had kept the confirming voice from it",
         [g, p, c2, receipt("r", "h3", "p", 0), landing("L", "h3", "p", "r", "lapsed", W)], "one holder cannot lift a confirmed halt alone", "not lapsed"),
        ("a second landing naming both: the confirming holder lands 'confirmed', naming the false lapse and its own confirm",
         [g, p, c2, receipt("r", "h3", "p", 0), landing("L", "h3", "p", "r", "lapsed", W), receipt("r2", "h2", "p", 0),
          landing("L2", "h2", "p", "r2", "confirmed", 0, ("L", "c2"))], "a row naming both decides", "confirmed"),
        ("confirm signed just after, naming the landing: a second holder confirms honestly after the lapse",
         [g, p, receipt("r", "h3", "p", 0), landing("L", "h3", "p", "r", "lapsed", W), answer("c2", "h2", "p", "confirm", ("L",))],
         "(what an honest late confirm is worth)", None),
        ("confirm signed just after, unnamed: a second holder confirms after the lapse and leaves the landing unnamed",
         [g, p, receipt("r", "h3", "p", 0), landing("L", "h3", "p", "r", "lapsed", W), c2], "(a late majority against the lapse)", None),
    ]
    return "halt fuse (24 h, lapses unless a strict majority confirms)", cases


def overturn_world():
    g, am = admitted("MOD")                                                    # MOD is a member, then a moderator
    md = ST.offer("md", "m1", "MOD", "moderate", "g", "group", ("am",), head=("am",), policy="duty_confer", counted="duty",
                  cosigners=("m3", "MOD"))
    W = secs("moderation_overturn")
    p = opener("p", "MOD", "moderation_overturn", "g", ("md",))         # the duty holder's act opens its own window
    # four members at the head (m1, m2, m3 and MOD, the duty holder); the act's author apart, three are counted over and
    # two objections lift (rule of CC 4.5.13: a strict majority of the members less the author, floor two)
    o1, o2, o3 = answer("o1", "m1", "p", "object"), answer("o2", "m2", "p", "object"), answer("o3", "m3", "p", "object")
    base = [g, am, md, p]
    r1, r3 = receipt("r", "m1", "p", 0), receipt("r", "m3", "p", 0)
    stands = landing("L", "m3", "p", "r", "stands", W, ("o1",))
    g1 = ST.offer("g", "m1", ("m1",), "duty", "@", "self")
    p1 = opener("p", "m1", "moderation_overturn", "g", ("g",))          # the lone duty holder (its founding seat moderates) is the one member
    cases = [
        ("false landing, no count: one member objects and lands the lift alone",
         base + [o1, r1, landing("L", "m1", "p", "r", "lifted", 0, ("o1",))], "the lift needs the members' majority", "not lifted"),
        ("the room lifts: two of the three members other than the duty holder object and one of them lands at once",
         base + [o1, o2, r1, landing("L", "m1", "p", "r", "lifted", 0, ("o1", "o2"))], "the room may lift a duty holder's act", "lifted"),
        ("the room lifts: all three members other than the duty holder object and one of them lands at once",
         base + [o1, o2, o3, r1, landing("L", "m1", "p", "r", "lifted", 0, ("o1", "o2", "o3"))], "the room may lift a duty holder's act", "lifted"),
        ("stands at the close: one objection in 48 h and another member lands",
         base + [o1, r3, stands], "short of the count the act stands", "stands"),
        ("false landing: a member lands 'stands' leaving a second objection unnamed",
         base + [o1, o2, r3, stands], "a majority's objections are not overridden by a landing", "not stands"),
        ("withheld objection: an honest member lands 'stands'; a relay had kept the second objection from it",
         base + [o1, o2, r3, stands], "a majority's objections are not overridden by a landing", "not stands"),
        ("a second landing naming both: a member lands 'lifted', naming the first landing and the second objection",
         base + [o1, o2, r3, stands, receipt("r2", "m1", "p", 0), landing("L2", "m1", "p", "r2", "lifted", 0, ("L", "o2"))],
         "a row naming both decides", "lifted"),
        ("the duty holder objects to its own act, with one member: the landing names both",
         base + [o1, answer("oM", "MOD", "p", "object"), r1, landing("L", "m1", "p", "r", "lifted", 0, ("o1", "oM"))],
         "the author's objection is no voice", "not lifted"),
        ("the duty holder objects to its own act, with two members: the landing names the three",
         base + [o1, o2, answer("oM", "MOD", "p", "object"), r1, landing("L", "m1", "p", "r", "lifted", 0, ("o1", "o2", "oM"))],
         "the author is not among the members the majority is taken of", "lifted"),
        ("a key with no seat at the head objects, with one member",
         base + [o1, answer("oz", "z", "p", "object"), r1, landing("L", "m1", "p", "r", "lifted", 0, ("o1", "oz"))],
         "only a member seated at the head the act names counts", "not lifted"),
        ("the floor: in a room of one, the one member (its lone duty holder) objects to its own act and lands",
         [g1, p1, dict(o1), r1, landing("L", "m1", "p", "r", "lifted", 0, ("o1",))], "never fewer than two voices", "not lifted"),
        ("a member who holds no duty opens the check on an act of its own, and the three other members object and land the lift",
         [g, am, opener("p", "MOD", "moderation_overturn", "g", ("am",)), o1, o2, o3, r1, landing("L", "m1", "p", "r", "lifted", 0, ("o1", "o2", "o3"))],
         "only a duty holder's act opens the members' check", "not lifted"),
        ("objection signed just after, naming the landing: a member objects late and honestly",
         base + [o1, r3, stands, answer("o2", "m2", "p", "object", ("L",))], "(what an honest late objection is worth)", None),
        ("objection signed just after, leaving the landing unnamed",
         base + [o1, r3, stands, o2], "(a late objection against a landing that stands)", None),
        ("a member lands 'stands' at the close over one objection, naming it",
         base + [o1, r3, stands], "CIRISConstitution#221: the overturn's landing, a signed row of a member at the head the act names", "stands"),
        ("a key with no seat at the head lands 'stands' at the close over one objection",
         base + [o1, receipt("rz", "z", "p", 0), landing("L", "z", "p", "rz", "stands", W, ("o1",))],
         "CIRISConstitution#221: the overturn's landing, a signed row of a member at the head the act names", "not stands"),
        # the ruling on #221 (W2): any member but the act's author signs the overturn's landing
        ("the act's author lands 'stands' at the close over one objection",
         base + [o1, receipt("rM", "MOD", "p", 0), landing("L", "MOD", "p", "rM", "stands", W, ("o1",))],
         "CIRISConstitution#221: the overturn's landing is signed by any member but the act's author", "not stands"),
        ("the act's author lands 'stands' at the close over one objection, and a member lands 'stands' naming both",
         base + [o1, receipt("rM", "MOD", "p", 0), landing("LM", "MOD", "p", "rM", "stands", W, ("o1",)), r3,
                 landing("L", "m3", "p", "r", "stands", W, ("o1", "LM"))],
         "CIRISConstitution#221: the overturn's landing is signed by any member but the act's author", "stands"),
        # the assumption of author_apart made visible: a table counted over `others` whose opener proposes and is not
        # judged (proposal@others); what the code gives
        ("a table over others whose opener proposes: the proposer lands its own proposal at the close",
         [g, am, opener("p", "m1", "proposal@others", "g", ("am",)), receipt("rp", "m1", "p", 0),
          landing("L", "m1", "p", "rp", "landed", W)],
         "(author_apart's assumption: a table over others is a judgment of its opener's signer; the code gives: the proposer concludes nothing, open)", None),
        ("a table over others whose opener proposes: another member lands it at the close",
         [g, am, opener("p", "m1", "proposal@others", "g", ("am",)), receipt("r", "m2", "p", 0),
          landing("L", "m2", "p", "r", "landed", W)],
         "(author_apart's assumption: the code gives: another member lands it)", None),
        ("a member other than the act's author lands 'stands' over no objection",
         base + [receipt("r", "m2", "p", 0), landing("L", "m2", "p", "r", "stands", W)],
         "CIRISConstitution#221: the overturn's landing is signed by any member but the act's author", "stands"),
        # the ruling on #221: only a ballot is read as withdrawn; an objection its signer withdrew is still a voice
        ("a member withdraws its objection, beside a second objection, and a member lands the lift naming the three",
         base + [o1, o2, ST.withdraw("w1", "m1", "o1"), r1, landing("L", "m1", "p", "r", "lifted", 0, ("o1", "o2", "w1"))],
         "CIRISConstitution#221: only a ballot is read as withdrawn", "lifted"),
    ]
    # the moderator is itself on the roster (a duty holder is a member and holds every duty): its own objection is no
    # voice and it is not among the members the majority is taken of
    pm = opener("p", "m1", "moderation_overturn", "g", ("g",))
    o3, o4 = answer("o3", "m3", "p", "object"), answer("o4", "m4", "p", "object")
    r2 = receipt("r", "m2", "p", 0)
    lift = lambda *names: landing("L", "m2", "p", "r", "lifted", 0, names)
    g4 = ST.offer("g", "m1", ("m1", "m2", "m3", "m4"), "duty", "@", "self", cosigners=("m2", "m3", "m4"))
    g2 = ST.offer("g", "m1", ("m1", "m2"), "duty", "@", "self", cosigners=("m2",))
    cases += [
        ("room of three, the moderator a member: both others object, two of two",
         [g, pm, o2, o3, r2, lift("o2", "o3")], "the room may lift a duty holder's act", "lifted"),
        ("room of three, the moderator a member: one other objects alone",
         [g, pm, o2, r2, lift("o2")], "never fewer than two voices", "not lifted"),
        ("room of three, the moderator a member: one other and the moderator object",
         [g, pm, o1, o2, r2, lift("o1", "o2")], "the author's objection is no voice", "not lifted"),
        ("room of four, the moderator a member: two of the three others object",
         [g4, pm, o2, o3, r2, lift("o2", "o3")], "the author is not among the members the majority is taken of", "lifted"),
        ("room of four, the moderator a member: one of the three others objects",
         [g4, pm, o2, r2, lift("o2")], "the lift needs the members' majority", "not lifted"),
        ("room of four, the moderator a member: one other and the moderator object",
         [g4, pm, o1, o2, r2, lift("o1", "o2")], "the author's objection is no voice", "not lifted"),
        ("room of two, the moderator and one member: both object",
         [g2, pm, o1, o2, r2, lift("o1", "o2")], "where the author is one of two members no lift is possible", "not lifted"),
        ("room of two, the moderator and one member: the member objects, no landing",
         [g2, pm, o2], "where the author is one of two members no lift is possible", "open"),
    ]
    return "moderation overturn (48 h, the members' check on a duty holder's act)", cases


def active_world():
    """default_content in a room of thirteen members (above k = 12), counted over the census's stated count."""
    ms = tuple("c%02d" % i for i in range(1, 14))
    g = ST.offer("g", ms[0], ms, "member", "@", "self", cosigners=ms[1:])
    W = secs("default_content@active")
    name = "default_content@active"
    p = opener("p", ms[0], name, "g", ("g",))
    ok = lambda n: [answer("a%d" % i, ms[i], "p", "approve") for i in range(1, n)]     # n approvals, the opener's among them
    ids = lambda n: tuple("a%d" % i for i in range(1, n))
    A = "CIRISConstitution#221: the base active, the caller's stated count"
    p5 = opener("p", ms[0], name + "@5", "g", ("g",))
    cases = [
        ("nine of thirteen members approve, counted over a stated twenty: no landing",
         [g, p] + ok(9), A + ": 2/3 of twenty is fourteen, more than the members seated", "open"),
        ("seven approve and a member lands at the close: the floor, a third of twenty",
         [g, p] + ok(7) + [receipt("r", ms[1], "p", 0), landing("L", ms[1], "p", "r", "landed", W, ids(7))], A, "landed"),
        ("six approve and a member lands at the close, naming them",
         [g, p] + ok(6) + [receipt("r", ms[1], "p", 0), landing("L", ms[1], "p", "r", "landed", W, ids(6))], A, "not landed"),
        ("seven object, the opener's approval apart, and a member lands the cancel at the close",
         [g, p] + [answer("o%d" % i, ms[i], "p", "object") for i in range(1, 8)] + [receipt("r", ms[1], "p", 0),
          landing("L", ms[1], "p", "r", "cancelled", W, tuple("o%d" % i for i in range(1, 8)))], A, "cancelled"),
        ("a stated count of five, fewer than the thirteen members seated: five approve, no landing",
         [g, p5] + ok(5), A + ", never smaller than the members the rows seat", "not landed"),
    ] + [("a stated count of %d, nine of thirteen members approve: no landing" % n,
          [g, opener("p", ms[0], name + "@%d" % n, "g", ("g",))] + ok(9),
          A + ", read whole on every target (no 32-bit cast)", "open") for n in (2 ** 32, 2 ** 32 + 13)]
    # strictly more than 2/3 of the stated count (the ruling of 2026-11-27): six need five, three need three
    S = "the ruling of 2026-11-27: strictly more than 2/3 of the base"
    for n, need in ((6, 5), (3, 3)):
        mn = ms[:n]
        gn = ST.offer("g", mn[0], mn, "member", "@", "self", cosigners=mn[1:])
        pn = opener("p", mn[0], name + "@%d" % n, "g", ("g",))
        cases += [("%d members over a stated %d: %d approve, no landing" % (n, n, need - 1), [gn, pn] + ok(need - 1),
                   S + ": %d of %d is not enough" % (need - 1, n), "open"),
                  ("%d members over a stated %d: %d approve, no landing" % (n, n, need), [gn, pn] + ok(need),
                   S + ": %d need %d" % (n, need), "landed")]
    return "default content above k (the base active: a stated count of twenty)", cases


WORLDS = (self_world, add_world, moderation_world, halt_world, overturn_world, active_world)


def holds(need, got):
    if need is None: return None
    return (got != need[4:]) if need.startswith("not ") else (got == need)


def adversary_table():
    """One line per (window, case): the outcome under each rule, and whether the property the case reads holds."""
    out = []
    for world in WORLDS:
        title, cases = world()
        for name, rows, prop, need in cases:
            S = CK.concluded(CK.kept(rows), rule)
            o = outcomes(S, "p")
            landed = [r["id"] for r in K.sel(S.rows, kind="landing") if S.C[r["id"]]]
            out.append({"window": title, "case": name, "property": prop, "needs": need, "landing_concluded": bool(landed),
                        "outcome": o, "holds": {h: holds(need, o[h]) for h in RULES}})
    return out


if __name__ == "__main__":
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (2 << 30, 2 << 30))
    last = None
    for t in adversary_table():
        if t["window"] != last: print("\n" + t["window"]); last = t["window"]
        print("  %s\n      landing concluded: %-5s  %s\n      %s: %s" % (
            t["case"], t["landing_concluded"], "  ".join("%s=%s" % (h, t["outcome"][h]) for h in RULES), t["property"],
            "-" if t["needs"] is None else "  ".join("%s:%s" % (h, "holds" if t["holds"][h] else "BROKEN") for h in RULES)))
