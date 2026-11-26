"""
seat.py: STANDING AS ONE SHAPE, over the causal kernel (kept, concluded, the cut) and kernel_lib.

A seat of key k in scope s over object o is live iff
    a kept, concluded OFFER by a conferrer names (k, s, o),
    a kept, concluded ACCEPTANCE by k is paired with that offer,
    neither is withdrawn by its own signer,
    and no counting cut removes it.

The conferrer is one parameter with three values (`conf` on the offer):
    self    the offer is signed by the object's own key: the object itself when it is a key, the signers or
            the named subjects of the row when it is a row (a group is the row that founded it)
    seat    the offer is signed by a key holding a live seat that may confer this one, and names that seat
            (`under`). Bounded depth. What a seat may confer is table data (CONFERS) or the `sub` mark.
    group   the offer counts when a tally of the live seats (`counted`, over `over`) at the head it names is
            met. The threshold is a row of manifests/governance_policy.json; a ranked row is the ranked tally.

Pairing. The acceptance names the offer (`of`), or the offer names the acceptance: the text has both orders
(a widening names the joiner's acceptance; a trust acceptance names the root's charter). A key that signed the
offer itself, as signer or as one of `cosigners` (several signatures on one row), has accepted by that.
`consent="one"` on an offer waives the acceptance (a node has no agency); it is refused under conf=seat.

A cosignature is a voice for an offer or an unseat only when it names every head that row is counted over. A
voice given once is not a voice for a later row of the same content at another head.

What ends a seat.
    withdraw   a row naming the offer or the acceptance, signed by the signer of what it names, or by the
               holder against the offer that seats it. Read at the concluded layer: no standing is needed.
               A holder's withdrawal ends its own seat only; the conferrer's ends the offer for all it seats.
               The conferrer of a counted offer (conf=group) is the count, not the key that signed the row: that
               key's lone withdrawal ends nothing. A counted seat ends by its holder's withdrawal or a counted unseat.
    unseat     a CUT on the slot ("seat", k, s, o), by the object's own key (self) or by a count (group). Every
               offer on the slot in its past is ended, every offer and acceptance on the slot concurrent with
               it is void (cut.py), and an offer that names it is a new seat.
               Over a founding row that seats several keys no one of them is "the object's own key" against the
               others: a `self` unseat there concludes nothing, and ending such a seat takes the count.
    upstream   a seat conferred under another falls with it (the walk is run again on every read). A `self` offer
               over a founding row that seats several keys, signed by one of them, is live only while that
               signer's own founding seat is: it falls with it like any seat conferred under it.
    founding   a founding record (CC 4.5.4; `found`) lists its members in `to` and names its duty holders in
               `duty_holders`, a map from a duty to the members who hold it. It seats each listed member who signed
               it in `member`, and each holder an entry names, when a listed signer, in that duty: one row, no
               count, however many found it. A listed member who did not sign any founding row, with a map or without, is seated in nothing (a later
               acceptance does not seat it), and an entry naming a key that is no listed signer seats nothing. The
               seats end separately: a withdrawal of the founding row that names a duty (`scope`) ends that seat
               only; one that names no seat ends every seat the row gives its signer (an end of its stay).
               A founding row of scope `duty` with no map seats every key it names as a duty holder (HOLDS gives
               that seat `member`), as before.
    duty       over a community the founding record seats duty holders (a `duty_holders` map, or scope `duty`),
               who are equals (CC 4.5.4).
               A duty seat is conferred by a strict majority of the holders or by the lone holder, withdrawn by a
               strict majority of the others, never on fewer than two voices where there are two holders, and
               ended by a removal from the roster. A seat so conferred is rooted in the group: its conferrer's
               withdrawal or departure does not end it.
    member     a duty seat stands only where its holder holds the roster's seat over the same community at the
               same reading (a member seat, or the founding seat, which holds `member`). A conferral on a key that
               is not a member seats nobody, is no voice in a duty count, and stands with no further row once the
               key's widening lands. An end of the holder's stay ends the duty seats whose offers are in that
               end's past: a counted removal from the roster, or the holder's own withdrawal of a seat that holds
               `member` over the community. Nothing revives: a later admission does not seat an offer so ended. A
               conferral that is not in the end's past (made after it, or beside it) waits for the next admission
               like any conferral on a non-member. At tips the duty seat follows the folded roster.
               Over every community, whatever its founding row seats, and only a seat that makes its holder a duty
               holder (`duty`, a named duty, a duty the record declares): another seat, a node's detector seat for
               one, is not asked for membership. Who may place a duty (CC 4.5.4): the founding record, the duty
               holders' count (or the lone holder, duty_seat), or the members' election (the ranked tally); a
               members' admission count places none (duty_gate, CIRISConstitution#241).

An AI agent's key (CC 4.5.13). An agent "acts under its own key and has no vote"; "a recall and an election count
its persons alone". "No single key removes a member alone, and no duty holder removes another from the roster
alone. ... An AI agent's key is the exception. A moderator of the room MAY remove it alone and at once, and the
members may lift that act as they may any act of a moderator."
    the seat      an agent's key is seated over the room in scope `agent` (AGENT), a roster seat (ROSTER_SEATS) the
                  room's persons admit by their count. `Seats.roster(o)` is the whole roster, members and agents,
                  which content, wraps and audience read; `holders("member", o)` holds no agent. Every count of the
                  room is taken of persons (counted_keys): an agent's key is no voice and is not counted over,
                  whatever other seat it holds. An agent may hold a duty by its own duty seat, which stands on its
                  `agent` seat as a person's stands on its member seat, and acts alone within it.
    the removal   a counted unseat of one key's `agent` seat concludes on its signer's one voice where that signer
                  holds `moderate` over the object at the head the row names, whatever the room's protocol and
                  however many holders. The seat's scope says the key is an agent's. An unseat of a person's seat
                  so signed is counted as any removal is.
    the lift      the removal opens a `moderation_overturn` window (window.py: `window` on the row). The lift's
                  effect is a row: a counted offer of policy `moderation_overturn` that seats the key again, cites
                  the removal (`content`), names the head the removal names, and names objections (answers
                  `object` to the removal). Its voices are the signers of those objections and no other key; the
                  removal's author is no voice, and the key it seats is an agent's, so it is in no count. It
                  concludes when those voices are a strict majority of the members (persons) at that head, the
                  removal's author apart, never fewer than two: the overturn's count.
                  It restores and does not admit: the key it seats held its `agent` seat at that head.
                  No reading of the roster reads a window: until that row is written the key is out.
    in force      the removal is an act under the remover's `moderate` standing, and the seat walk counts it as a
                  live unseat only where the end rule (conferral_end.py, E2 to E8) gives it in force over the rows
                  held (removal_in_force, re-expressed over seat rows): an end of that standing, its own laying
                  down, a counted removal of it, or the other holders' counted withdrawal of its duty, takes it out
                  of force from the end's head on unless another duty holder's receipt of it (an `ack` naming it)
                  is held; a removal naming a head later than the end's, or having the end in its past, does not
                  count. Out of force, it ends nothing and the agent's key is seated again for that reader. Only another
                  standing live at the removal's head keeps it; nothing revives it (a moderator seated again signs
                  the removal again).

Tips wait (KERNEL.md section 7). When several counted acts on one object are concurrent, the holders of a scope
over it are the keys common to the tips, until a counted act names them all.

Built on, and the reader's line (checkpoint.py). A counted act counts only if every counted act among the heads it
names counts. With `own`, the counted acts that reader has acknowledged are its line: a counted act concurrent with
the line and counted over older heads does not count for that reader; one counted over the same head waits as a tip.
`checkpoint=True` turns on the group checkpoint, which is refused (it ranks lines by depth) and kept only to show why.

Layers. Whether an offer or an unseat was validly made is CONCLUDED: it reads the row and its concluded
ancestors only (the object's own key; the count over the head it names). Whether the seat is live now is
DERIVED: pairing, withdrawals, the cut and the walk. No instant, digest or list position is read.

stands(S, root, k, s, o): the bounded walk. A self-rooted seat has its offer's signer as root, a counted seat
has ("group", o), a conferred seat has the root of the seat it is under.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import causal_kernel as CK  # noqa: E402
import cut as CUT           # noqa: E402
import checkpoint as CP     # noqa: E402

K, R = CK.K, CK.row
sys.path.insert(0, os.path.join(ROOT, "models", "kernel_lib"))
from reexpress import ranked as RANKED  # noqa: E402   the ranked count, already written over the library
DEPTH = 5                                       # CC 3.4.7: a delegation chain is at most five links

# ---- table data ----------------------------------------------------------------------------------------
# what a seat holds at zero hops (the root holds what it may confer), and what it may confer over which object
# CC 4.5.4 community law: "A community has members and duty holders, and no other tier." A founding record seats the
# duty holders it names, each by its own signature on it (scope `duty`); "Whoever founds a community alone is its first
# duty holder." A holder of any one duty is a duty holder. `founder` is kept only in the infrastructure community's
# sense (its operators, CC 3.2 T7), where it holds membership and no duty.
DUTIES = ("moderate", "review", "slash", "takedown")
HOLDS = {"duty": ("member",) + DUTIES, "founder": ("member",), "owner": ("steward",)}
CONFERS = {  # scope held -> (scopes it may confer, "same": over the same object | "holder": over the holder's own key)
    "duty": (("duty",) + DUTIES, "same"),     # alone only while the one duty holder (LONE); otherwise by the count
    "owner": (("wa", "infra:attest", "operator"), "same"),
    "self": (("wa", "takedown", "author", "custodian", "operator"), "same"),
    "root": (("attest", "infra:attest", "assure:age", "assure:capacity", "infra:attest_assurance", "infra:detect"), "holder"),
}
# what the holder of a seat over an object may end over that same object by a row of its own (a cut, so it takes
# standing). CC 2.4.1.1: "Its owner revokes it under the owner-binding, and that ends the owner-binding's standing.
# ... Only the key's own revocation ends its liveness, and neither of the others does" (the sentence of 2026-11-16;
# until 2026-11-23 this table read the owner's revocation as ending the key's registration). So the owner's
# revocation ends the owner's OWN seat, the binding, and nothing of the key's. The owner seat is the owner-binding: the
# owner's row and the key's own signature on it (CC 3.2, The first binding). The ender must be the ONE live owner
# over the ender's own past: `owner_of` "resolves to at most one key", and with two the key "MUST NOT be treated as
# owned by any of them" (CC 3.2), so with two live owners neither alone revokes (derived from those two sentences).
ENDS = {"owner": ("owner",)}
# seats whose ending is final: a revocation is "never withdrawn" (CC 2.4.1.1), so no offer re-seats the same key in the
# same scope over the same object once a concluded revocation of that slot is in its past.
# A roster seat named here (a room key's seat: `member`, `agent`) is final over a private room only (CC 3.1.3.2: "a
# member admitted again makes a fresh one"; the steward's decision of 2026-11-25 on CIRISConstitution#224: "a removed
# room key is not seated again", of any end of the seat, a resignation included). See _revoked_before.
FINAL = ("registered", "member", "agent")
# CC 4.5.4 (iv): "A duty seat is conferred by a strict majority of the duty holders, and withdrawn by a strict majority
# of the other duty holders, the holder concerned not counted. Where there are two holders or more, neither takes fewer
# than two voices. A lone duty holder confers alone, with the new holder's acceptance." Two policy names, counted
# over the duty holders at the head the row names; a seat conferred alone stands only if its signer was then the
# one duty holder, read over the offer's own past.
DUTY_POLICY = {"duty_confer": "confer", "duty_withdraw": "withdraw"}
MUT = set()       # named mutations, switched on by a check (formal/causal_kernel/check_rosters.py, the key instance)


def policy_table(path=None):
    """policy row -> a predicate met(yes, n), from the enact rule of manifests/governance_policy.json."""
    path = path or os.path.join(ROOT, "data", "governance_policy.json")
    out = {}
    for f in json.load(open(path, encoding="utf-8"))["families"]:
        e = f.get("enact_rule") or {}
        if e.get("kind") == "fraction":
            num, den = e["num"], e["den"]
            # the table writes self_roster_* as 1/2; the text and formal/self_roster say a strict majority
            out[f["family"]] = ("strict", 1, 2) if (num, den) == (1, 2) else ("atleast", num, den)
        elif e.get("kind") == "strict_majority":
            out[f["family"]] = ("strict", 1, 2)
        elif e.get("kind") == "one_of_n":
            out[f["family"]] = ("one", 1, 1)
        elif e.get("kind") == "protocol":
            out[f["family"]] = ("declared", 0, 0)
        elif e.get("kind") == "ranked_irv":
            out[f["family"]] = ("ranked", 0, 0)                  # the count is the ranked tally (formal/ranked_choice)
        else:
            out[f["family"]] = ("not_a_count", 0, 0)             # role_at: a seat, not a threshold
    return out


POLICY = policy_table()


def acts_table(path=None):
    """The act-to-policy binding (data/governance_policy_acts.tsv): one row per (act, scope, community kind), the policy
    rows it may take, and whether the counted row states one of them (`row`) or the act fixes it (`fixed`)."""
    path = path or os.path.join(ROOT, "data", "governance_policy_acts.tsv")
    out = []
    for line in open(path, encoding="utf-8"):
        if line.startswith("#") or not line.strip() or line.startswith("act\t"): continue
        act, scope, kind, policy, choice = line.rstrip("\n").split("\t")[:5]
        out.append((act, scope, kind, tuple(policy.split("|")), choice))
    return tuple(out)


ACTS = acts_table()     # read by no rule yet: the binding is built in steps (CIRISConstitution: the act-to-policy table)

# The kind of an object (the acts table's `community_kind`, the policy table's `corridor` reading), from its founding row's
# scope. A key object is a self roster. An object with no kind has no act.
KINDS = {"member": "community", "duty": "community", "holder": "accord", "self": "self", "key": "self"}


def kind_of(by, obj, is_key=False):
    """The kind of obj: `self` for a key object; else its founding row's scope read through KINDS; None otherwise."""
    if is_key: return "self" if "key_kind_unread" not in MUT else None
    g = by.get(obj)
    if g is None or g["kind"] != "offer" or g.get("obj") != g["id"]: return None
    if "kind_unread" in MUT: return "community"                  # MUTATION: every founding row a community
    return KINDS.get(g["scope"])


def act_of(r, by, is_key=False):
    """The act a counted row is, decided from its kind, its scope and its object, never from the policy it states:
    (act, scope class, kind) as the acts table writes them, or None (not a counted act, or an object with no kind).
        community  an offer whose `content` names an unseat of the same seat (object, scope, keys) is the lift, of
                   that seat's scope (the table binds the agent's); an offer or unseat of a roster seat is an admission
                   or a removal of that seat; one of a detector seat (`detect:*`) is the holders' conferral or
                   withdrawal of that seat; an offer of a duty under the ranked count is the election's seating (THE
                   ONE ACT READ FROM THE STATED POLICY, for this tag: the election is not answered safely by it);
                   another offer of a duty is the duty holders' conferral; an unseat of a duty counted over a duty
                   (`counted`, the body the row counts) is their withdrawal, and one counted over the members is the
                   recall. Any other scope is no act.
        accord     any counted row is a standing act.
        self       an offer or unseat of a key, or of the roster's own seat, admits or removes a key.
    A moderator's lone removal is a removal by its shape; whether it is counted at all is the seat rule's."""
    if r["kind"] not in ("offer", "unseat") or r.get("conf") != "group": return None
    obj, sc, offer = r.get("obj"), r.get("scope"), r["kind"] == "offer"
    kind = kind_of(by, obj, is_key)
    if kind is None: return None
    if kind == "community":
        c = by.get(r.get("content"))
        if offer and c is not None and c["kind"] == "unseat" and c.get("obj") == obj and c.get("scope") == sc \
                and tuple(c.get("to", ())) == tuple(r.get("to", ())) and "lift_unread" not in MUT:
            return ("lift", sc, kind)                        # the seat re-seated: the table's row is of scope `agent`
        if sc in ROSTER_SEATS: return ("admit" if offer else "remove", sc, kind)
        # a detector seat (CC 4.5.7: `detect:{list id}`, conferred and "withdrawn by the count of (iv)"): no declared duty
        if (sc == "detect" or sc.startswith("detect:")) and "detect_unread" not in MUT:
            return ("seat_confer" if offer else "seat_withdraw", "detect", kind)
        dec = declared(by, obj)
        if not is_duty(sc, dec): return None
        if offer:
            # THE ONE ACT READ FROM THE STATED POLICY: the election is not answered safely by this tag, and a caller must
            # not rely on a ranked seating (CIRISConstitution#241: the election is out of 0.5.0)
            if K.rule(POLICY, r.get("policy"), ("unknown",))[0] == "ranked" and "election_unread" not in MUT:
                return ("election_seating", "moderate", kind)
            return ("duty_confer", "duty", kind)
        holders = is_duty(r.get("counted", "member"), dec) if "recall_by_policy" not in MUT else \
            K.rule(POLICY, r.get("policy"), ("unknown",))[0] == "duty"
        return ("duty_withdraw" if holders else "recall", "duty", kind)
    if kind == "accord": return ("standing_act", "any", kind)
    if kind == "self":
        own = by.get(obj, {}).get("scope")
        return ("admit" if offer else "remove", "key", kind) if sc in ("key", own) else None
    return None


def policy_for(act, scope, kind, acts=ACTS):
    """The policy rows an act may take, and whether the counted row chooses (`row`) or the act fixes it (`fixed`):
    the acts table's row for (act, scope class, kind), or None."""
    for a, sc, kd, pol, ch in acts:
        if (a, sc, kd) == (act, scope, kind): return pol, ch
    return None
# A removal runs under the room's own declared protocol (CC 3.3.4; the table's cell is `protocol`). The rooms of
# these scenarios declare two thirds. roster.py runs the other protocols.
POLICY.update({k: ("duty", 0, 0) for k in DUTY_POLICY})          # CC 4.5.4 (iv), read by duty_count, not by met()
# CC 4.5.13, the members' check as a counted row: the re-seating of an agent's key a moderator removed alone. Read by
# lift_count, not by met(): a counted row of this policy that is no such re-seating concludes nothing.
POLICY["moderation_overturn"] = ("lift", 1, 2)
# CC 4.5.13: "A recall is one row cosigned by more than two thirds of the standing roster ... The floor is two voices"
# (the table's cell reads 2/3): strictly more, with the floor, counted over the roster less the holder it recalls
POLICY["moderator_recall"] = ("recall", 2, 3, 2)
if POLICY.get("community_remove", ("", 0, 0))[0] == "declared":
    POLICY["community_remove"] = ("atleast", 2, 3)


def met(policy, yes, n, declared=None, table=None):
    e = K.rule(table or POLICY, policy, ("unknown", 0, 0))
    kind, num, den = e[:3]
    if kind == "atleast": return n > 0 and yes * den >= num * n
    if kind == "strict": return yes * den > num * n
    # strictly more than a fraction and never fewer than `least` voices; the recall's threshold (its base, less the
    # holder it recalls, is read by count_met)
    if kind in ("strictfloor", "recall"): return yes * den > num * n and (yes >= e[3] or "floor_unread" in MUT)
    if kind == "one": return yes >= 1
    if kind == "declared": return declared is not None and yes >= declared
    return False


# ---- rows ----------------------------------------------------------------------------------------------
def _slots(to, scope, obj):
    return tuple(("seat", k, scope, obj) for k in ((to,) if isinstance(to, str) else to))


def offer(id, signer, to, scope, obj, conf, names=(), **kw):
    obj = id if obj == "@" else obj                 # "@": the object is this row (a group is its founding row)
    return R(id, "offer", signer, names, to=(to,) if isinstance(to, str) else tuple(to), scope=scope, obj=obj,
             conf=conf, on=_slots(to, scope, obj), **kw)


def accept(id, signer, of, names=(), scope=None, obj=None):
    """An acceptance of offer `of`, or (of=None) a standing acceptance of any offer of `scope` that names it."""
    names = tuple(names) + ((of,) if of and of not in names else ())
    kw = {"on": _slots(signer, scope, obj)} if obj is not None else {}
    return R(id, "accept", signer, names, of=of, scope=scope, obj=obj, **kw)


def withdraw(id, signer, target, names=(), scope=None):
    """A withdrawal of row `target`. `scope`, where given, names the one seat of a founding row it ends (the
    duty a founding holder lays down); with none it ends every seat the target gives its signer."""
    kw = {} if scope is None else {"scope": scope}
    return R(id, "withdraw", signer, tuple(names) + ((target,) if target not in names else ()), target=target, **kw)


def found(id, signer, to, duty_holders=None, cosigners=(), scope="member", **kw):
    """A founding record (CC 4.5.4): `to` its listed members, each seated `member` by its own signature on it;
    `duty_holders` a map from a duty to the members who hold it, each seated in that duty by the same signature.
    The map is carried as sorted (duty, keys) pairs."""
    dh = tuple(sorted((d, tuple(ks)) for d, ks in (duty_holders or {}).items()))
    return offer(id, signer, to, scope, "@", "self", cosigners=tuple(cosigners), duty_holders=dh, **kw)


def unseat(id, signer, k, scope, obj, conf, names=(), **kw):
    return R(id, "unseat", signer, names, to=(k,), scope=scope, obj=obj, conf=conf, cuts=_slots(k, scope, obj),
             says="out", **kw)


def cosign(id, signer, of, names=()):
    return R(id, "cosign", signer, names, of=of)


signers = lambda r: frozenset((r["signer"],) + tuple(r.get("cosigners", ())))
covers = lambda have, want: have == want or want.startswith(have + ":")


def is_duty(scope, declared=()):
    """A duty: the four the law names, or one the community's record declares (CC 4.5.4 (i): "a record MAY declare
    others"). `declared` is the record's own list (the founding row's `duties`)."""
    return scope == "duty" or scope.split(":")[0] in DUTIES or scope.split(":")[0] in declared


def declared(by, obj):
    """The duties the community's record declares (its founding row's `duties`). A record's declared duty is never a
    roster scope (`member`, `agent`): such an entry is ignored (MUTATION declared_roster_kept)."""
    g = by.get(obj)
    # `moderate` is "a duty every community's record declares" (CC 4.5.4), whatever the law's list names (the crate
    # reads a law; here DUTIES names it already)
    return (("moderate",) if community(by, obj) else ()) + record_duties(g or {})


def record_duties(g):
    return tuple(d for d in g.get("duties", ()) if d not in ("member", "agent") or "declared_roster_kept" in MUT)


# the seats over a community its duty holders do NOT place: membership is the roster's own seat, placed by the count
# of the group's consensus_protocol and the joiner's yes (CC 3.1.3.2, CC 3.3.4). Every other seat they place over the
# community is placed by them under CC 4.5.4 (iv), whatever its scope.
ROSTER_SEATS = ("member", "agent")
# CC 4.5.13: an AI agent "acts under its own key and has no vote"; "a recall and an election count its persons alone".
# An agent's key is seated in a scope of its own: on the roster (content, wraps, audience), and in no count.
AGENT = "agent"


def lists_holders(g):
    """A founding row that names its duty holders (CC 4.5.4): a `duty_holders` map that names at least one key."""
    return any(ks for _, ks in g.get("duty_holders") or ())


def lone_founding(o):
    """A founding record one person signs with no `duty_holders` map (CC 4.5.4: "A record one person signs MAY name
    none, and that person then holds every declared duty"): a community's founding row (scope `member`; a key's or a
    voice's own roster founded alone is no community) whose `to` is one key, signed by that key, no other key signing
    it. The older presentation, a lone founder's row of scope `duty`, holds the law's duties through HOLDS and is read
    as before."""
    return o.get("obj") == o["id"] and not o.get("duty_holders") and len(o["to"]) == 1 and o["scope"] == "member" \
        and signers(o) == frozenset(o["to"]) and "lone_founder_unread" not in MUT


def seat_scopes(o, k):
    """The scopes offer `o` seats key k in. One, the offer's own scope, for every offer but a founding row. A founding
    row seats by the signatures on it, with or without a map: a listed member who did not sign it is seated in nothing,
    whatever it accepts later (CC 3.1.3.2, `membership_founding_member_unsigned`); one who signed it in its own scope,
    and where it carries a `duty_holders` map, in each duty whose entry names it."""
    if o["obj"] != o["id"]: return (o["scope"],)
    # a founding row seats by the signatures on it, with or without a map (CC 3.1.3.2: a listed key that did not sign
    # is `membership_founding_member_unsigned`; it joins by an ordinary admission)
    if "unsigned_no_map" in MUT and not o.get("duty_holders"): return (o["scope"],)   # MUTATION: the old exception
    if k not in signers(o) and "unsigned_seated" not in MUT: return ()       # MUTATION: a listed member who did not sign is seated
    if lone_founding(o):
        # the lone signer holds `moderate` always ("a duty every community's record declares") and each duty its record
        # declares (`duties`); not the law's other named duties (CIRISConstitution#241)
        return (o["scope"], "moderate") + tuple(d for d in record_duties(o) if d not in (o["scope"], "moderate"))
    if not o.get("duty_holders") or "holders_unread" in MUT: return (o["scope"],)
    return (o["scope"],) + tuple(d for d, ks in o["duty_holders"] if k in ks and d != o["scope"])


def founding_duty(o, sc):
    """A duty seat a founding row gives by its `duty_holders` map."""
    return (bool(o.get("duty_holders")) or lone_founding(o)) and o["obj"] == o["id"] and sc != o["scope"]


def duty_seat(by, o):
    """A seat placed over a community by its duty holders (an object that is a founding row seating duty holders):
    every scope but the roster's own, so a scope the record declares, or any other, follows the holders' count."""
    g = by.get(o["obj"])
    if g is None or g["id"] == o["id"] or not duty_room(by, o["obj"]): return False
    if "duty_list_only" in MUT: return is_duty(o["scope"])      # MUTATION: only the named duties follow the count
    return o["scope"] not in ROSTER_SEATS


def community(by, obj):
    """obj is a community: an object that is its own founding row. The duty-seat rule (a duty seat stands only on
    the roster's seat; an end of the stay ends the duty seats before it) reaches every community, whatever its
    founding row seats (CC 4.5.4: "a non-member holds no duty")."""
    if "member_rule_duty_rooms_only" in MUT: return duty_room(by, obj)   # MUTATION: the rule reaches duty rooms only
    return founding_row(by, obj)


def founding_row(by, obj):
    """The one test of a community: obj names a held offer whose object is itself (a founding row), whatever its scope."""
    g = by.get(obj)
    return g is not None and g["kind"] == "offer" and g["obj"] == g["id"]


def duty_room(by, obj):
    """obj is a community whose founding row seats duty holders (the only place the duty rules engage): a founding row
    of scope `duty`, or one whose `duty_holders` map names a holder."""
    g = by.get(obj)
    return founding_row(by, obj) and (g["scope"] == "duty" or lists_holders(g) or lone_founding(g))


def roster_seat(o, holds=None, sc=None):
    """A seat of the roster's own over a community, given by offer `o` in scope `sc` (default the offer's): a scope
    its duty holders do not place (ROSTER_SEATS: a member's, an agent's), or a founding row's own scope where it holds
    `member`. Every other seat over the community is a duty seat."""
    sc = o["scope"] if sc is None else sc
    if not ((o["id"] == o["obj"] and sc == o["scope"]) or sc in ROSTER_SEATS): return False
    return sc in ROSTER_SEATS or covers(sc, "member") or "member" in K.rule(HOLDS if holds is None else holds, sc, ())


def stay_ends(rows, by, holds=None):
    """The holders' own ends of a stay as a member, among `rows`: (withdrawal, key, community) for each withdrawal by a
    key of an offer of the roster's seat that names it, or of its own acceptance of one (the offer the acceptance
    names, or a standing acceptance's own scope and object). Read from the rows alone."""
    out = []
    for w in rows:
        if w["kind"] != "withdraw": continue
        t, k = by.get(w.get("target")), w["signer"]
        if t is None: continue
        # a withdrawal that names a scope ends the stay only where the target gives the signer that seat and it is a
        # roster seat; one naming a duty lays that seat down, and the stay goes on (MUTATION stay_scope_ungated: a
        # roster scope is taken at its word)
        if w.get("scope") is not None and "scope_unread" not in MUT and not (
                t["kind"] == "offer" and roster_seat(t, holds, w["scope"])
                and ("stay_scope_ungated" in MUT or w["scope"] in seat_scopes(t, k))):
            continue
        if t["kind"] == "accept" and t["signer"] == k:
            if t["of"] is not None: t = by.get(t["of"])
            elif t.get("obj") is not None and t.get("scope") in ROSTER_SEATS and community(by, t["obj"]):
                out.append((w, k, t["obj"])); continue
            else: continue
        if t is None or t["kind"] != "offer" or k not in t["to"]: continue
        if community(by, t["obj"]) and roster_seat(t, holds): out.append((w, k, t["obj"]))
    return out


def end_scope(by, w):
    """The roster seat a key's own end of its stay (stay_ends) ends: the scope the withdrawal names, or else the scope
    of the offer it withdraws (through an acceptance, the offer accepted, or a standing acceptance's own)."""
    if w.get("scope") is not None: return w["scope"]
    t = by.get(w.get("target"))
    if t is None: return None
    if t["kind"] == "accept" and t.get("of") is not None: return (by.get(t["of"]) or {}).get("scope")
    return t.get("scope")


def duty_held(by, o, sc=None):
    """A duty seat proper: a seat the duty holders place over their community (duty_seat) whose scope makes its holder a
    duty holder, or a duty seat a founding row gives by its `duty_holders` map. The seat the membership rule reaches."""
    sc = o["scope"] if sc is None else sc
    if founding_duty(o, sc): return True
    # over any community, a seat whose scope makes its holder a duty holder (who may confer it is duty_seat's)
    g = by.get(o["obj"])
    return community(by, o["obj"]) and g["id"] != o["id"] and o["scope"] not in ROSTER_SEATS and is_duty(sc, declared(by, o["obj"]))


def _lone(r, P, by):
    """CC 4.5.4 (iv): a duty conferred by one key stands only if that key is then the one duty holder over the object
    (a person: an agent holding a duty is no holder this count reads)."""
    if "lone_any" in MUT: return True
    Q = seats_of(P)
    return Q.holders("duty", r["obj"]) - Q.holders(AGENT, r["obj"]) == frozenset({r["signer"]})


def duty_count(r, P, yes, mem):
    """CC 4.5.4 (iv) over the duty holders at the head: conferral by a strict majority of them, withdrawal by a strict
    majority of the others (the holder concerned not counted); never fewer than two voices where there are two holders."""
    base = mem - set(r["to"]) if DUTY_POLICY[r["policy"]] == "withdraw" and "count_target" not in MUT else mem
    y = yes & base
    return 2 * len(y) > len(base) and (len(y) >= 2 or len(mem) < 2 or "no_duty_floor" in MUT)


def agent_removal(r):
    """A removal of an agent's key from the roster: an unseat of one key's `agent` seat. The seat's scope says whose it is."""
    if r["kind"] != "unseat" or len(r["to"]) != 1: return False
    return r["scope"] == AGENT or ("agent_unread" in MUT and r["scope"] in ROSTER_SEATS)   # MUTATION: it reaches a person


def lone_removal(r, P, past):
    """CC 4.5.13: a moderator of the room removes an agent's key alone. The signer holds `moderate` over the object at
    the head the row names."""
    if not agent_removal(r) or r.get("conf") != "group": return False
    if "moderator_unread" in MUT: return True                       # MUTATION: any key removes an agent's key alone
    # a room's moderator, over the room (CC 4.5.13): over an object that is no community (a key's own roster) an unseat
    # is an ordinary counted row (MUTATION lone_any_object)
    if "lone_any_object" not in MUT and not community({q["id"]: q for q in P}, r["obj"]): return False
    heads = r.get("head", ())
    # the key removed holds an agent's seat at the head the row names: a person's key is not removed so, whatever
    # scope the unseat states (MUTATION lone_any_key: the key's seat not read)
    # This is also what makes a lift restore and not admit: its re-seating stands on such a removal (MUTATION
    # restores_unseated, the same break seen from the lift)
    if not MUT & {"lone_any_key", "restores_unseated"} and r["to"][0] not in members_at(P, past, r["obj"], heads, AGENT):
        return False
    return r["signer"] in members_at(P, past, r["obj"], heads, "moderate")


def lift_voices(r, P, past, by):
    """The voices of a re-seating row, or None where it is none: the signers of the objections it names to the lone
    removal it cites, less that removal's author."""
    rem = by.get(r.get("content"))
    if r["kind"] != "offer" or rem is None or rem["kind"] != "unseat" or not lone_removal(rem, P, past): return None
    if (rem["obj"], rem["scope"], tuple(rem["to"]), tuple(rem.get("head", ()))) != (r["obj"], r["scope"], tuple(r["to"]), tuple(r.get("head", ()))):
        return None                                                 # the same seat, at the head the removal names
    v = frozenset(a["signer"] for a in P if a["kind"] == "answer" and a.get("of") == rem["id"] and a.get("says") == "object"
                  and a["id"] in r["names"])
    return v if "author_voice" in MUT else v - {rem["signer"]}      # MUTATION author_voice: the author's objection counts


def room_count(yes, base):
    """The members' check of one member's act (the overturn, the lift, the count's receipt of a lone removal): more
    than half of the base, never fewer than two voices (MUTATION lift_no_floor: no floor). Whatever policy or need a
    row states, these counts are read by this rule alone."""
    return 2 * len(yes) > len(base) and (len(yes) >= 2 or "lift_no_floor" in MUT)


def lift_count(r, P, past, by):
    """The overturn's count (window.py, moderation_overturn) over the objections a re-seating row names: a strict
    majority of the members at the head, the removal's author apart and the key seated apart (each no voice, and
    not counted over); never fewer than two."""
    v = lift_voices(r, P, past, by)
    if v is None: return False
    heads = r.get("head", ())
    # a lift restores: the key held its `agent` seat at the head the removal names, since the removal is a lone
    # removal only of such a key (lone_removal). So a moderator's "removal" of a key never seated, and a strict
    # majority's objections, admit nothing past the room's own protocol
    # the members are persons: the key removed is an agent's, so it is no voice and is not counted over
    mem, vot = counted_keys(P, past, r["obj"], heads)
    yes = v & vot
    if "lift_over_all" not in MUT: mem = mem - {by[r["content"]]["signer"]}    # MUTATION lift_over_all: the author counted over
    return room_count(yes, mem)


def founding_many(by, obj):
    """obj is a founding row that seats several keys."""
    g = by.get(obj)
    return g is not None and g["kind"] == "offer" and g["obj"] == g["id"] and len(g["to"]) > 1


def own_keys(by, obj):
    """The object's own key: the object when it is a key; the signers and named subjects of the row when a row."""
    if obj in by:
        return signers(by[obj]) | frozenset(by[obj].get("subjects", ()))
    return frozenset({obj})


# ---- the moderator election (CC 4.5.13, CC 4.5.4 (v) and rule 2), as ruled C1 to C5 ---------------------------
# The rows. An election is named by its id row E: the room's founding row, or the closed seating of the election
# before (C5). A ballot (kind `ballot`, `ranking` best first) and a decline (kind `decline`) are a member's own rows,
# each naming its election by `of`. The seating is a counted offer of `moderate` over the room under the ranked
# count (`moderator_election`), signed by the winner (its acceptance), `to` the winner, `of` its election, naming
# the rows it is counted over (its set); it names no head. A receipt of a seating is an `ack` whose `of` is it.
#   C1  the electorate (persons) and the candidates are read at the VACANCY its id row defines: every end of a seat E
#       gave (the end of its holder; for the founding row, of each duty seat it gives), in the reading row's past, the
#       members at all of them; the founding row itself where it gives no duty seat. A member admitted after the
#       vacancy neither votes nor stands. A leaver (its own leaving in the reading row's past) is no voice and no
#       candidate.
#   C2  a seating concludes only where no person holds a duty over the room in the seats read over its whole past,
#       and no row of a later election (one whose id is a seating of this election) is in its past.
#   C3  an id row's standing is read in the naming row's past.
#   C4  CONTAINS: a seating stands only where its set strictly contains every other seating's set of its election
#       (seatings over equal sets are one seat); sets not nested: nobody, until a seating over the union.
#   C5  the CAUSAL CLOSE: an election is closed when a strict majority of its electorate, the winner apart (and a
#       leaver apart, read in the receipts' past), has receipted one seating, each receipt counting only where that
#       seating stood under C4 in the receipt's own past; one say per person, read causally. Once closed, no rival
#       seating counts.
ELECTION_RANKS = 3               # "Each person ranks up to three": a ballot ranking more is void, the whole ballot
#   E3  once its holder's seat has ended, a seating that stood (C4) and never closed names the next election, C3
#       deciding between rival ids by past.
#   F1  every input to a seating's count comes from the set it names: its ballots, the withdrawals of them, the
#       declines, the leavings it reads, and (F2) the end or ends of the seat it reads the electorate at. Seatings
#       over equal sets count alike.
#   F3  a next election stands only while its id row stands, for the rows held: beating or un-standing a seating
#       takes with it every election named on it.
_EMEMO = {}


def is_election(o, table=None):
    """A seating by the election: a counted offer under the ranked count (`moderator_election`)."""
    return o.get("kind") == "offer" and o.get("conf") == "group" and \
        K.rule(table or POLICY, o.get("policy"), ("unknown",))[0] == "ranked"


def _memo(tag, row, f, rows=()):
    # keyed by the row and the rows it is read over (one row object may stand in two sets of rows)
    key = (tag, id(row), frozenset(MUT), frozenset(id(x) for x in rows))
    got = _EMEMO.get(key)
    if got is None or got[0] is not row:
        got = _EMEMO[key] = (row, f())
    return got[1]


def id_seats(E):
    """The seats id row E gave: for a founding row, each duty seat it gives a signer (its map's, the one-founder's
    `moderate`, the older presentation's `duty`); for a seating, its winner's `moderate`. [(offer, key, scope)]."""
    if E.get("obj") == E["id"]:
        return [(E["id"], k, sc) for k in E["to"] for sc in seat_scopes(E, k)
                if (sc != E["scope"] or sc == "duty") and is_duty(sc, record_duties(E))]
    return [(E["id"], E["to"][0], "moderate")] if E.get("to") else []


def vacancy(E, P, past, named=None):
    """C1: the rows of P that end a seat E gave (each row whose own past holds that seat live and whose past with it
    does not), or (E's id,) where E gives no seat; None while a seat E gave has no end in P. `named` (F2): only the
    rows a seating names are read as ends. Only a holder's own withdrawal, or an unseat naming a holder, can end one."""
    seats = id_seats(E)
    if not seats or "vacancy_founding" in MUT: return (E["id"],)
    live = lambda rows: {(r["offer"], r["k"], r["scope"]) for r in seats_of(rows).recs}
    holders = {k for _, k, _ in seats}
    ends, ended = [], set()
    for w in P:
        if w["kind"] not in ("withdraw", "unseat") or not past(E["id"], w["id"]): continue
        if named is not None and w["id"] not in named and "vacancy_unnamed" not in MUT: continue
        if not (w["signer"] in holders if w["kind"] == "withdraw" else set(w["to"]) & holders): continue
        pre = [q for q in P if past(q["id"], w["id"])]
        gone = {s for s in seats if s in live(pre) and s not in live(pre + [w])}
        if gone:
            ends.append(w["id"]); ended |= gone
    if ended != set(seats): return None
    if "vacancy_first_end" in MUT: ends = sorted(ends)[-1:]        # MUTATION: one end read, the others not
    return tuple(ends)


def electorate(E, P, past, obj, named=None):
    """C1: the persons seated at every row of E's vacancy (the agents apart), or empty where E has no vacancy in P."""
    v = vacancy(E, P, past, named)
    if v is None: return frozenset()
    if "electorate_at_seating" in MUT:                              # MUTATION: the persons seated over the whole past
        Q = seats_of(P)
        return Q.holders("member", obj) - Q.holders(AGENT, obj)
    return counted_keys(P, past, obj, v)[0]


def _past_of(rows, past, q):
    return [x for x in rows if past(x["id"], q["id"])]


def ekey(E, rows, past):
    """The election id row E names, as a key: the row's id for a founding row (or any row that is no seating); for a
    seating, (room, its own election's key, its set). Seatings over equal sets of one election are one seat (C4), so
    an election named by either is one election. rows: a set holding E's past."""
    if not is_election(E) or "twin_ids_apart" in MUT: return ("id", E["id"])
    v = seating_view(E, _past_of(rows, past, E), past)
    return ("s", E["obj"], v[0], v[2])


def election_rows(q, Ek, elect, by, rows, past, obj=None, ends=()):
    """q is a row of election Ek's set: a ballot or decline naming that election, a withdrawal of such a ballot by
    its own signer, or a leaving (its own end of its stay, or a counted removal from the roster) of a member of the
    electorate in the election's window (F1, N2: not in the past of the vacancy end the seating reads, which already
    settled every leaving and re-admission before it); signed by a member of the electorate (a removal: of one)."""
    if q is None: return False
    window = "leaving_before_vacancy_read" in MUT or not any(past(q["id"], e) for e in ends)
    if q["kind"] == "unseat" and q.get("conf") == "group" and q.get("obj") == obj and q.get("scope") in ROSTER_SEATS:
        return bool(set(q["to"]) & elect) and window
    if q["kind"] == "withdraw" and obj is not None and any(g == obj and k in elect for _, k, g in stay_ends([q], by)):
        return window
    if q["signer"] not in elect and "set_any_signer" not in MUT: return False
    named = lambda b: b.get("of") in by and ekey(by[b["of"]], rows, past) == Ek
    if q["kind"] in ("ballot", "decline"): return named(q)
    if q["kind"] == "withdraw":
        t = by.get(q.get("target"))
        return t is not None and t["kind"] == "ballot" and named(t) and t["signer"] == q["signer"]
    return False


def seating_view(S, P, past):
    """(its election's key, the electorate, the set) of seating S, read over its own past P."""
    def f():
        by = {q["id"]: q for q in P}
        E = by.get(S.get("of"))
        if E is None: return (None, frozenset(), frozenset(), frozenset())
        Ek = ekey(E, P, past)
        named = frozenset(S["names"])
        # (3): an end of the seat is in the set only where a ballot of the set names it, the ballot's signer a member
        # there (it votes on that end); an end no such ballot names is part of no set (MUTATION end_unnamed_by_ballot)
        if "end_unnamed_by_ballot" not in MUT:
            bal = [by[n] for n in named if n in by and by[n]["kind"] == "ballot" and by[n].get("of") == E["id"]]
            cand = vacancy(E, P, past, named) or ()
            named = frozenset(n for n in named if n not in cand or n == E["id"] or any(
                n in b["names"] and b["signer"] in counted_keys(P, past, S["obj"], (n,))[0] for b in bal))
        el = electorate(E, P, past, S["obj"], named)
        v = vacancy(E, P, past, named) or ()
        rows = {n for n in S["names"] if election_rows(by.get(n), Ek, el, by, P, past, S["obj"], v)}
        ends = frozenset(set(v) & named)
        return (Ek, el, frozenset(rows | ends), ends)
    return _memo("view", S, f, P)


def c4_standing(seatings, sets):
    """C4 over one election's seatings: the ids that stand (the seatings over the one set that strictly contains every
    other set, equal sets one seat), empty where the sets are not so nested."""
    if not seatings: return frozenset()
    if "contains_unread" in MUT: return frozenset(x["id"] for x in seatings)
    groups = {sets[x["id"]] for x in seatings}
    top = [g for g in groups if all(h <= g for h in groups)]
    if len(top) != 1: return frozenset()
    return frozenset(x["id"] for x in seatings if sets[x["id"]] == top[0])


def _view(rows, past, q):
    return seating_view(q, _past_of(rows, past, q), past)


def _seatings_of(Ek, rows, past, obj):
    return [q for q in rows if is_election(q) and q.get("obj") == obj and _view(rows, past, q)[0] == Ek]


def closure(Ek, rows, past, obj):
    """C5 over rows (a causally closed set): the set of the seatings that closed election Ek, or None. A receipt is an
    `ack` whose `of` is a seating of the election; it counts where that seating stood under C4 in the receipt's own
    past. A person's say: its earliest receipts of the election's seatings (none of the others in their past); where
    those are of different sets, no say; a later one counts for nothing."""
    if "close_unread" in MUT: return None
    seat_ids = {q["id"]: q for q in _seatings_of(Ek, rows, past, obj)}
    if not seat_ids: return None
    view = lambda q: _view(rows, past, q)
    acks = [a for a in rows if a["kind"] == "ack" and a.get("of") in seat_ids]
    # (2): a key that said two things in the election, for this reader, is no voice and is out of the base
    fork = forkers(Ek, rows, past, obj, {q["id"]: q for q in rows})
    if fork and "fork_reopens_close" in MUT: return None      # MUTATION: the old E2, a fork reopens the close for all
    by_p = {}
    for a in acks: by_p.setdefault(a["signer"], []).append(a)
    says = {}
    for p, rs in by_p.items():
        first = rs if "say_any_receipt" in MUT else [a for a in rs if not any(past(b["id"], a["id"]) for b in rs if b is not a)]
        if p in fork or (len({view(seat_ids[a["of"]])[2] for a in first}) != 1 and "say_any_receipt" not in MUT):
            continue
        for a in first:
            A = _past_of(rows, past, a)
            here = _seatings_of(Ek, A, past, obj)
            st = c4_standing(here, {x["id"]: view(x)[2] for x in here})
            if a["of"] in st or "receipt_standing_unread" in MUT:
                says.setdefault(view(seat_ids[a["of"]])[2], []).append(a)
                if "say_any_receipt" not in MUT: break
    # E1 (the fifth read, G2): one base per election for a reader: a key departed (left, or removed, not seated
    # again) over the rows held is out of it for every group alike, and its receipts count for nothing; H1: unless
    # its leaving (or removal) holds its receipt, which then counts, the key staying in the base (MUTATION
    # leaving_after_receipt_voids)
    def held_receipt(k, d):
        return "leaving_after_receipt_voids" not in MUT and any(past(a["id"], d["id"]) for a in by_p.get(k, ()))
    gone = frozenset() if "close_leavers_kept" in MUT else frozenset(
        k for k, d in departures(rows, past, obj) if not any(held_receipt(k, d2) for k2, d2 in departures(rows, past, obj) if k2 == k))
    # the base is the INTERSECTION of the members at every end any seating of the election names, over the rows held:
    # C1 applied election-wide (each seating still counts its own electorate, C1/F2). A lay-down that does not stand
    # for the reader (H4: behind its line) is no end for it; that comes with the head rules (MUTATIONS
    # base_per_seating_electorate: each group its own seating's electorate; close_base_union: the union)
    els = [frozenset(view(q)[1]) for q in seat_ids.values()]
    union = frozenset().union(*els) if "close_base_union" in MUT else frozenset.intersection(*els)
    met_ = []
    for group, rs in sorted(says.items(), key=lambda x: sorted(x[0])):
        S = next(q for q in seat_ids.values() if view(q)[2] == group)
        el, winner = (view(S)[1] if "base_per_seating_electorate" in MUT else union), S["to"][0]
        base = el - {winner} - gone
        if "base_per_group" in MUT:              # MUTATION: departed read per group, over its receipts' pasts
            base = el - {winner} - set().union(*[departed(_past_of(rows, past, a), past, obj) for a in rs])
        if "fork_base_kept" not in MUT: base = base - fork
        yes = {a["signer"] for a in rs} & base
        if 2 * len(yes) > len(base) or not base: met_.append(group)
    # (ii), the rule: where more than one group meets its close over the rows held, none is closed; nothing is picked
    # by order (MUTATION two_closes_both_stand: the first met)
    if len(met_) == 1 or (met_ and "two_closes_both_stand" in MUT): return met_[0]
    if len(met_) > 1: return None
    # a room of one, or one whose every other elector has departed (E1, the limit): a standing seating closes itself
    here = list(seat_ids.values())
    st = c4_standing(here, {x["id"]: view(x)[2] for x in here})
    if "fork_base_kept" not in MUT: gone = gone | fork
    for q in here:
        el = view(q)[1]
        if q["id"] in st and el and not (el - {q["to"][0]} - gone):
            return view(q)[2]
    return None


def forkers(Ek, rows, past, obj, by, ends0=frozenset()):
    """(2): the keys that said two things in election Ek among rows: two rows of the election's own, signed by the key,
    neither in the other's past. The election's own rows: a ballot or decline naming it, a withdrawal of such a
    ballot, a receipt of one of its seatings, one of its seatings, a lay-down read as its vacancy (an end in a set of
    one of its seatings). Rows in two rooms, or of two elections, are never a fork (MUTATION fork_across_objects: any
    two rows of these kinds by the key)."""
    across = "fork_across_objects" in MUT
    seats = [q for q in rows if is_election(q) and (across or (q.get("obj") == obj and _view(rows, past, q)[0] == Ek))]
    sids = {q["id"] for q in seats}
    ends = set(ends0).union(*[_view(rows, past, q)[3] for q in seats])
    # G1: a counted unseat (a room act others cosign) is never its signer's election row: only a holder's own
    # lay-down of the seat is (MUTATION counted_end_forks_signer)
    if "counted_end_forks_signer" not in MUT:
        ends = {e for e in ends if e in by and by[e]["kind"] == "withdraw"}
    named = lambda b: across or (b.get("of") in by and ekey(by[b["of"]], rows, past) == Ek)
    if "seating_not_a_say" in MUT: sids = set()        # MUTATION: a seating is no say of its signer's
    mine = {}
    # (4): the fork is per key: a voice's rows signed through two room or device keys are two keys' rows. The key is the
    # VERIFIED signing key (`dev` in these models: the room key whose signature the door checked; roomkey.by_dev), never
    # a value the row states; with none, the signer (MUTATIONS fork_per_voice: one voice, one key; fork_by_stated_device:
    # a device label the row body states read as the key)
    if "fork_per_voice" in MUT: key = lambda q: q["signer"]
    elif "fork_by_stated_device" in MUT: key = lambda q: (q["signer"], q.get("device_label") or q.get("dev") or q["signer"])
    else: key = lambda q: (q["signer"], q.get("dev") or q["signer"])
    for q in rows:
        own = (q["kind"] in ("ballot", "decline") and named(q)) or q["id"] in sids or q["id"] in ends or \
            (q["kind"] == "ack" and (q.get("of") in sids or (across and q.get("of") in by and is_election(by[q["of"]])))) or \
            (q["kind"] == "withdraw" and q.get("target") in by and by[q["target"]]["kind"] == "ballot"
             and by[q["target"]]["signer"] == q["signer"] and named(by[q["target"]]))
        if own: mine.setdefault(key(q), []).append(q)
        # a row the key only cosigns is never part of a fork (MUTATION fork_cosigned: it is)
        if "fork_cosigned" in MUT and q.get("obj") == obj:
            for c in q.get("cosigners", ()):
                mine.setdefault(c if "fork_per_voice" in MUT else (c, c), []).append(q)
    out = {k for k, rs in mine.items()
           if any(not past(a["id"], b["id"]) and not past(b["id"], a["id"]) for i, a in enumerate(rs) for b in rs[i + 1:])}
    return frozenset(k if isinstance(k, str) else k[0] for k in out)


def departures(P, past, obj):
    """[(key, row)]: each leaving of the room (the key's own end of its stay) or counted removal from its roster in P,
    the key not seated again after it there."""
    by = {q["id"]: q for q in P}
    out = []
    again = lambda k, d: any(m["kind"] == "offer" and m.get("obj") == obj and k in m["to"] and roster_seat(m)
                             and past(d["id"], m["id"]) for m in P)
    for w in P:
        if w["kind"] == "withdraw":
            for _, k, g in stay_ends([w], by):
                if g == obj and not again(k, w): out.append((k, w))
        elif w["kind"] == "unseat" and w.get("obj") == obj and w.get("scope") in ROSTER_SEATS and w.get("conf") == "group":
            out += [(k, w) for k in w["to"] if not again(k, w)]
    return out


def departed(P, past, obj):
    """The keys that have left the room (their own leaving) or been removed from its roster (a counted unseat of
    their roster seat) in P, and not been seated again after it there."""
    out = set(count_left(P, past, obj, "member"))
    for u in P:
        if u["kind"] == "unseat" and u.get("obj") == obj and u.get("scope") in ROSTER_SEATS and u.get("conf") == "group":
            for k in u["to"]:
                if not any(m["kind"] == "offer" and m.get("obj") == obj and k in m["to"] and roster_seat(m)
                           and past(u["id"], m["id"]) for m in P):
                    out.add(k)
    return frozenset(out)


def valid_id(E, r, P, past, by):
    """C3 and C5: id row E names an election for row r, read in r's past P: the room's founding row, or a seating of
    the room that closed its own election in r's past, or (E3) a seating of the room that stood under C4 in r's past
    and whose seat has ended there."""
    e = by.get(E)
    obj = r.get("obj")
    if e is None or "election_id_any" in MUT: return e is not None
    if e["id"] == obj: return True
    if not (is_election(e) and e.get("obj") == obj): return False
    v = _view(P, past, e)
    if closure(v[0], P, past, obj) == v[2]: return True
    if "wait_close" not in MUT:                  # MUTATION: the candidate rule E3 replaced (closed seatings only)
        here = _seatings_of(v[0], P, past, obj)
        return e["id"] in c4_standing(here, {x["id"]: _view(P, past, x)[2] for x in here}) and vacancy(e, P, past) is not None
    return False


def superseded(E, r, P, past, by):
    """E3, C3: election E is no longer the room's for row r where a seating of it that stood (C4) in r's past, and
    whose seat has ended there, names the next election (r must name that one)."""
    e = by.get(E)
    obj = r.get("obj")
    if e is None or "superseded_unread" in MUT: return False
    Ek = ekey(e, P, past)
    if "wait_close" in MUT: return closure(Ek, P, past, obj) is not None
    here = _seatings_of(Ek, P, past, obj)
    st = c4_standing(here, {x["id"]: _view(P, past, x)[2] for x in here})
    return any(vacancy(x, P, past) is not None for x in here if x["id"] in st)


def election_beaten(rows, past, void=frozenset()):
    """The seatings among rows (a causally closed set) that do not stand: per election, every one but the closed set's
    where it closed (C5), else every one but those C4 stands. `void`: the counted acts behind the reader's line; a
    seating among them does not stand for that reader and takes no part in C4 (MUTATION void_seating_read)."""
    if "void_seating_read" in MUT: void = frozenset()
    out = {q["id"] for q in rows if is_election(q) and q["id"] in void}
    groups = {}
    for q in rows:
        if is_election(q) and q["id"] not in void: groups.setdefault((q.get("obj"), _view(rows, past, q)[0]), []).append(q)
    for (obj, Ek), el in groups.items():
        sets = {x["id"]: _view(rows, past, x)[2] for x in el}
        grp = closure(Ek, rows, past, obj)
        if grp is not None and "closed_rivals_count" not in MUT:
            out |= {x["id"] for x in el if sets[x["id"]] != grp}
        else:
            st = c4_standing(el, sets)
            out |= {x["id"] for x in el if x["id"] not in st}
    # F3: a next election stands only while its id row stands, for the rows held (MUTATION id_cascade_unread)
    more = "id_cascade_unread" not in MUT
    every = [q for q in rows if is_election(q)]
    while more:
        add = {q["id"] for q in every if q["id"] not in out and q.get("of") in out}
        more = bool(add); out |= add
    return frozenset(out)


def election_count(r, P, past, by):
    """The seating's count (C1, C2, C5 and the carried-over ballot rules), over its concluded past P."""
    E, obj = r.get("of"), r["obj"]
    if r["kind"] != "offer" or not r.get("to") or E not in by: return False
    if not valid_id(E, r, P, past, by) or superseded(E, r, P, past, by): return False
    # C2: no person holds a duty over the room in the seats over the whole past
    Q = seats_of(P)
    if "c2_holder_unread" not in MUT and Q.holders("duty", obj) - Q.holders(AGENT, obj): return False
    Ek, el, mine, mine_ends = seating_view(r, P, past)
    # C2: no row of a later election (one named by a seating of this election) in the past
    later = {ekey(q, P, past) for q in _seatings_of(Ek, P, past, obj)}
    if "c2_later_unread" not in MUT and any(q.get("of") in by and ekey(by[q["of"]], P, past) in later
                                            for q in P if q["kind"] in ("ballot", "decline") or is_election(q)):
        return False
    # C5: an election closed in the past takes no further seating but its own
    grp = closure(Ek, P, past, obj)
    if grp is not None and grp != mine and "closed_rivals_count" not in MUT: return False
    if not el: return False
    # F1: the leavings and the withdrawals read are the set's
    named = [q for q in P if q["id"] in mine] if "set_inputs_unread" not in MUT else P
    left = {k for w in named if w["kind"] == "withdraw" for _, k, g in stay_ends([w], by) if g == obj} | \
        {k for u in named if u["kind"] == "unseat" and u.get("conf") == "group" and u.get("obj") == obj
         and u.get("scope") in ROSTER_SEATS for k in u["to"]}
    voters = el - (frozenset() if "leaver_voice" in MUT else left)
    # (2): a key whose two forked rows are both in the set is no ballot (the set alone decides: F1)
    voters = voters - forkers(Ek, named, past, obj, by, mine_ends)
    gone = {w["target"] for w in named if w["kind"] == "withdraw" and w["target"] in by
            and by[w["target"]]["kind"] == "ballot" and w["signer"] == by[w["target"]]["signer"]}
    declined = {d["signer"] for d in K.sel(P, kind="decline") if d["id"] in mine and d["signer"] in el}
    ballots = [(b["signer"], b["ranking"]) for b in K.sel(P, kind="ballot")
               if b["id"] in mine and b["signer"] in voters and b["id"] not in gone
               and (set(b["ranking"]) <= voters or "ballot_nonmember_ranked" in MUT)
               and (len(b["ranking"]) <= ELECTION_RANKS or "ballot_ranks_unbounded" in MUT)]
    if not ballots: return False
    won = RANKED(ballots, sorted(voters - declined), 2, declared=False)[0]
    return won == r["to"][0] and (r["signer"] == won or "seating_any_signer" in MUT)


# ---- derived: the live seats ---------------------------------------------------------------------------
class Seats:
    def __init__(self, S, holds=HOLDS, confers=CONFERS, depth=DEPTH, by_arrival=False, own=None, checkpoint=False, drop=None):
        self.S, self.holds, self.confers, self.own = S, holds, confers, own
        self.cut = C = CUT.Cut(S)
        Cs = S.Cs
        wd = K.sel(Cs, kind="withdraw")
        pos = {r["id"]: i for i, r in enumerate(S.rows)}
        ended = lambda row: any(w["target"] == row["id"] for w in wd)        # the concluded layer checked who signed it
        # a holder's withdrawal ends its own seat; the conferrer's (a signer who is not seated by the row) ends the offer
        # MUTATION by_arrival: a withdrawal held after the offer's acceptance comes too late (first held wins)
        late = lambda w, o: by_arrival and any(pos[a["id"]] < pos[w["id"]] for a in K.sel(Cs, kind="accept", of=o["id"]))
        # the conferrer of a counted offer is the count: the lone withdrawal of the key that signed the row ends nothing
        # a duty seat over a community: duty holders are equals (CC 4.5.4 (iii)), so the key that conferred it does not end it
        # alone; it ends by its holder's withdrawal or a count (duty_withdraw, or the members' recall)
        eq = lambda o: duty_seat(S.by, o) and "duty_ranked" not in MUT
        # a withdrawal that names a scope ends that one seat of the row it withdraws (a founding holder lays down a duty)
        # the election (C4): seatings over equal sets of one election are one seat, so the holder's withdrawal of any
        # of them ends it (MUTATION twin_withdrawal_unread)
        past_ = lambda a, b: a in S.anc[b]
        twins = {}
        if any(is_election(o) for o in Cs) and "twin_withdrawal_unread" not in MUT:
            el = [o for o in Cs if is_election(o)]
            key = {o["id"]: ekey(o, Cs, past_) for o in el}
            for o in el: twins[o["id"]] = {x["id"] for x in el if key[x["id"]] == key[o["id"]]}
        tgt = lambda w, o: w["target"] == o["id"] or (w["target"] in twins.get(o["id"], ()) and w["signer"] in o["to"])
        off_ended = lambda o, k, sc: any(tgt(w, o) and (w["signer"] == k or (w["signer"] not in o["to"] and o["conf"] != "group" and not eq(o)))
                                         and (w.get("scope") in (None, sc) or "scope_unread" in MUT) and not late(w, o) for w in wd)
        self.stale = V = CP.void(S, C, own, checkpoint)         # counted acts built on one that does not count, or behind the reader's line
        # the election's seatings that do not stand (C4, C5): read over the concluded rows, as the fold at tips is
        self.beaten = beaten = election_beaten(Cs, past_, V) if any(is_election(o) for o in Cs) else frozenset()
        unseats = [u for u in K.sel(Cs, kind="unseat") if C.counts(u) and u["id"] not in V]
        # a moderator's lone removal is an act under its `moderate` standing, in force only while the end rule says so
        # (out_of_force). `drop`: the lone removals already judged out of force over the whole set, for a reading of
        # one line of it (the tips, the fold) or of the set with every removal taken as made (`frozenset()`)
        if drop is None:
            drop = out_of_force(S, unseats, holds, confers, depth, own, checkpoint) if "end_unread" not in MUT else frozenset()
        self.dropped = drop
        unseats = [u for u in unseats if u["id"] not in drop]

        left = stay_ends(wd, S.by, holds)                       # the holders' own ends of a stay as a member
        gone = {(k, g) for _, k, g in left}

        def resigned(o, k, sc):
            """A seat whose offer is in the past of its holder's own end of its stay is ended by it: a duty seat (the end
            of the stay as a member ends it), and every seat of the key in the roster scope the end ends, whatever row
            seated it (an end is of the key's stay in that scope, not of a row; as a counted removal's cut reaches
            every offer on the slot in its past)."""
            duty = duty_held(S.by, o, sc) and not ("duty_revives" in MUT or "resign_keeps_duty" in MUT)
            stay = "stay_one_row" not in MUT                  # MUTATION stay_one_row: a resignation ends the row it names only
            if not duty and not stay: return False
            return any(k2 == k and g == o["obj"] and ((pos[o["id"]] < pos[w["id"]]) if by_arrival else (o["id"] in S.anc[w["id"]]))
                       and (duty or end_scope(S.by, w) == sc) for w, k2, g in left)

        def unseated(o, k, sc):
            for u in unseats:
                # a removal from the roster ends the removed member's duty seats too, "since a non-member holds no duty" (CC 4.5.4)
                held = ("seat", k, sc, o["obj"]) in u["cuts"] or (
                    "member_cut_only" not in MUT and (is_duty(sc) or duty_seat(S.by, o) or founding_duty(o, sc))
                    and any(("seat", k, r, o["obj"]) in u["cuts"] and holds_roster(S, u, k, o["obj"], r) for r in ROSTER_SEATS))
                if not held: continue
                # MUTATION duty_revives: a removal from the roster ends no duty seat by its past, so the next admission seats the old offer
                if "duty_revives" in MUT and ("seat", k, sc, o["obj"]) not in u["cuts"] and duty_held(S.by, o, sc): continue
                # MUTATION by_arrival: an unseat ends the offers that were held before it, by list position
                if (pos[o["id"]] < pos[u["id"]]) if by_arrival else (o["id"] in S.anc[u["id"]]): return True
            return False

        def own_void(row, o, k):
            """A key's own row on a roster seat that is concurrent with its own end of its stay there (neither in the
            other's past) is no voice: its signature on the offer or its acceptance of it (CIRISConstitution#224, ruled:
            the rule a removed key's concurrent rows have, read for the key's own end). Rows of other keys are untouched."""
            if "own_end_unread" in MUT or not roster_seat(o, holds): return False   # MUTATION: the key's own end voids nothing
            return any(k2 == k and g == o["obj"] and ("own_end_any_seat" in MUT or end_scope(S.by, w) == o["scope"]) and S.concurrent(w["id"], row["id"])
                       for w, k2, g in left)

        def accepted(o, k):
            if k in signers(o): return not own_void(o, o, k)
            if o.get("consent") == "one": return o["conf"] != "seat"
            for a in K.sel(Cs, kind="accept", signer=k):
                paired = (a["of"] == o["id"]) or (a["of"] is None and a["id"] in o["names"] and a["scope"] == o["scope"]
                                                 and a["obj"] in (None, o["obj"]))
                if paired and not ended(a) and C.counts(a) and not own_void(a, o, k): return True
            return False

        base = [(o, k, sc) for o in K.sel(Cs, kind="offer") if C.counts(o) and o["id"] not in V and o["id"] not in beaten
                for k in o["to"] if accepted(o, k) for sc in seat_scopes(o, k)
                if not off_ended(o, k, sc) and not unseated(o, k, sc) and not resigned(o, k, sc)]

        def step(live):
            at = {(oid, k, sc): (d, root) for oid, k, sc, d, root in live}
            held = {(oid, k): v for (oid, k, _), v in sorted(at.items(), key=lambda x: x[1][0], reverse=True)}
            out = set(live)
            for o, k, sc in base:
                if (o["id"], k, sc) in at: continue
                if o["conf"] == "self":
                    # over a founding row that seats several keys, a signer's own offer stands on that signer's founding seat
                    if o["obj"] == o["id"] or not founding_many(S.by, o["obj"]) or (o["obj"], o["signer"]) in held:
                        out.add((o["id"], k, sc, 0, o["signer"]))
                elif o["conf"] == "group": out.add((o["id"], k, sc, 0, ("group", o["obj"])))
                elif eq(o): out.add((o["id"], k, sc, 0, ("group", o["obj"])))     # validly made by the lone holder: it stands as an equal
                elif o["conf"] == "seat":
                    up = S.by.get(o.get("under"))
                    hit = held.get((o.get("under"), o["signer"]))
                    if up is not None and hit is not None and self.may_confer(up, o):
                        out.add((o["id"], k, sc, hit[0] + 1, hit[1]))
            return frozenset(out)

        self.live = K.fix(step, frozenset(), depth + 1)       # one link per pass: at most `depth` links below a root
        # a duty seat stands only where its holder holds the roster's seat over the same community at this reading. The
        # walk is run again without the duty seats of keys that are not members, until none is left (a seat under one falls too)
        while "duty_no_member" not in MUT:
            mem = {(S.by[oid]["obj"], k) for oid, k, sc, _, _ in self.live if roster_seat(S.by[oid], holds, sc)}
            # MUTATION resign_keeps_duty: a key that ended its own stay still reads as a member for its duty seats
            keep = [(o, k, sc) for o, k, sc in base if not duty_held(S.by, o, sc) or (o["obj"], k) in mem
                    or ("resign_keeps_duty" in MUT and (k, o["obj"]) in gone)]
            if len(keep) == len(base): break
            base[:] = keep
            self.live = K.fix(step, frozenset(), depth + 1)
        self.recs = [{"id": "%s/%s/%s" % (oid, k, sc), "offer": oid, "k": k, "scope": sc, "obj": S.by[oid]["obj"],
                      "depth": d, "root": root} for oid, k, sc, d, root in self.live]

    def may_confer(self, up, o):
        """May the holder of the seat offered by `up` confer the seat `o` offers?"""
        if up.get("sub") and covers(up["scope"], o["scope"]) and o["obj"] == up["obj"]:
            return True                                            # the grant carried sub-delegation: the same or narrower
        scopes, over = K.rule(self.confers, up["scope"], ((), "same"))
        return any(covers(s, o["scope"]) for s in scopes) and o["obj"] == (up["obj"] if over == "same" else o["signer"])

    def _has(self, rec, s):
        if s == "duty" and is_duty(rec["scope"], declared(self.S.by, rec["obj"])): return True   # a holder of any one duty is a duty holder
        return covers(rec["scope"], s) or s in K.rule(self.holds, rec["scope"], ())

    def _member(self, rec):
        """A duty seat follows the folded roster: with several tips, its holder is among the members the fold seats."""
        if "duty_no_member" in MUT or "duty_fold_unread" in MUT or not duty_held(self.S.by, self.S.by[rec["offer"]], rec["scope"]): return True
        fold = self.tips_fold("member", rec["obj"])
        return fold is None or rec["k"] in fold or rec["k"] in (self.tips_fold(AGENT, rec["obj"]) or ())

    def stands(self, k, s, o, root=None):
        if not any(self._has(r, s) and (root is None or r["root"] == root) and self._member(r) for r in K.sel(self.recs, k=k, obj=o)): return False
        fold = self.tips_fold(s, o)                             # with several tips, the fold of their changes
        return fold is None or k in fold

    def roster(self, o):
        """The room's whole roster over o: its members and its agents (CC 4.5.13). Content, wraps and audience read it;
        no count does (a count reads `member`, or the scope it names, less the agents)."""
        return self.holders("member", o) | self.holders(AGENT, o)

    def holders(self, s, o, root=None):
        got = frozenset(r["k"] for r in K.sel(self.recs, obj=o) if self._has(r, s) and (root is None or r["root"] == root) and self._member(r))
        fold = self.tips_fold(s, o)
        return got if fold is None else got & fold

    def tips(self, o):
        """The frontier of the counted acts on o that count, with its founding row."""
        acts = [r for r in self.S.Cs if r["kind"] in ("offer", "unseat") and r.get("obj") == o and (r.get("conf") == "group" or r["id"] == o)
                and self.cut.counts(r) and r["id"] not in self.stale and r["id"] not in self.beaten]
        return K.frontier(self.S.anc, acts)

    def tips_common(self, s, o):
        """KERNEL.md section 7: with several tips, the keys common to all of them. None with one tip or none."""
        tp = self.tips(o)
        if len(tp) <= 1: return None
        S, out = self.S, None
        for t in tp:
            sub = [q for q in S.Cs if q["id"] == t["id"] or q["id"] in S.anc[t["id"]]]          # one tip: no further recursion
            Q = Seats(CK.State(sub, {q["id"]: True for q in sub}), self.holds, self.confers, drop=self.dropped)
            m = frozenset(r["k"] for r in K.sel(Q.recs, obj=o) if Q._has(r, s))
            out = m if out is None else out & m
        return out

    def _at(self, rows):
        """The seats read over a sub-set of the concluded rows (one line: no further recursion into tips)."""
        return Seats(CK.State(rows, {q["id"]: True for q in rows}), self.holds, self.confers, drop=self.dropped)

    def tips_fold(self, s, o):
        """KERNEL.md section 7, the fold at tips (models/roster_fork/fold.py): with several tips, the keys holding
        `s` over `o` when every tip's changes are folded. None with one tip or none.
            common   a key every tip seats is in;
            out      a key some tip's line removed is out, unless a later addition of it has that removal in its
                     past. So a key one tip admits and another removes is out;
            in       a key some tip adds is in where the counted offer that adds it meets its count on the voices
                     of keys the fold seats, over the members at its heads that the fold seats: a least fixed
                     point from the common keys;
            wait     tips that differ in protocol or policy (a counted row's `regime`, where the caller states one)
                     do not fold: the answer is then the common keys, as tips_common gives."""
        tp = self.tips(o)
        if len(tp) <= 1: return None
        if "fold_off" in MUT: return self.tips_common(s, o)
        S = self.S
        memo = self.__dict__.setdefault("_fold_memo", {})
        if (s, o) in memo: return memo[(s, o)]
        lines = []
        for t in tp:
            sub = [q for q in S.Cs if q["id"] == t["id"] or q["id"] in S.anc[t["id"]]]
            Q = self._at(sub)
            seated = {}                                         # key -> the offers that seat it at this tip
            for r in K.sel(Q.recs, obj=o):
                if Q._has(r, s): seated.setdefault(r["k"], set()).add(r["offer"])
            lines.append((t, sub, {q["id"] for q in sub}, seated))
        common = frozenset.intersection(*[frozenset(sd) for _, _, _, sd in lines])
        union = frozenset.union(*[frozenset(sd) for _, _, _, sd in lines])
        if len({t.get("regime") for t, _, _, _ in lines}) > 1 and "regime_folds" not in MUT:
            memo[(s, o)] = common
            return common

        def survives(k):
            """k is seated at some tip by an offer that every other line either never held k against, or removed k
            in that offer's past."""
            for _, _, _, sd in lines:
                for off in sd.get(k, ()):
                    ok = True
                    for _, sub2, ids2, sd2 in lines:
                        if k in sd2: continue
                        if off in ids2: ok = False; break       # this line ended the very seat
                        seen = [q for q in sub2 if q["id"] in S.anc[off]]
                        Q2 = self._at(seen)
                        if any(Q2._has(r, s) for r in K.sel(Q2.recs, obj=o, k=k)): ok = False; break   # removed beside it
                    if ok: return True
            return False

        cand = [k for k in sorted(union - common, key=str) if survives(k) or "keeps_removed" in MUT]
        out_keys = union - common - frozenset(cand)             # removed on a line and not added again after it

        def count_holds(k, seated):
            """Every counted offer that adds k meets its count on the voices of keys the fold seats, over the
            members at its heads that the fold seats."""
            if "plain_fold" in MUT: return True
            offs = set()
            for _, _, _, sd in lines: offs |= sd.get(k, set())
            for off in offs:
                r = S.by[off]
                if r.get("conf") != "group":
                    if r["signer"] not in seated and r["signer"] in union: return False
                    continue
                P = [q for q in S.Cs if q["id"] in S.anc[off]]
                past = lambda a, b: a in S.anc[b]
                over, counted = r.get("over", r["obj"]), r.get("counted", "member")
                if (over, counted) == (o, s): ok = seated if "one_step" not in MUT else (union - out_keys)
                else: ok = self.tips_fold(counted, over)                 # another scope's own fold; None: one tip there
                mem = counted_keys(P, past, over, r.get("head", ()), counted)[0] - count_left(P, past, over, counted)
                if ok is not None: mem = mem & ok
                yes = voices(r, P) & mem
                if is_election(r) and "fold_ranked_counted" not in MUT:
                    continue                    # an election's seating is read by C1 to C5 alone (beaten, the seat rule)
                if r.get("policy") in DUTY_POLICY:
                    if not duty_count(r, P, yes, mem): return False
                elif K.rule(POLICY, r.get("policy"), ("unknown",))[0] == "lift":
                    # a re-seating: its voices are the objections it names, over the members the fold seats
                    v = lift_voices(r, P, past, {q["id"]: q for q in P}) or frozenset()
                    yes = v & mem
                    if v: mem = mem - {S.by[r["content"]]["signer"]}   # the author apart (the key removed is an agent's: in no count)
                    if not room_count(yes, mem): return False
                elif not met(r.get("policy"), len(yes), len(mem), r.get("need")): return False
            return True

        memo[(s, o)] = common                                   # a count over this scope asked meanwhile reads the common keys
        got = common
        while True:                                             # least fixed point: a voice counts once its key is in
            more = got | frozenset(k for k in cand if k not in got and count_holds(k, got))
            if more == got: break
            got = more
        memo[(s, o)] = got
        return got

    def _out(self, s, o):
        """The keys the fold holds out of scope `s` over `o`: seated at some tip, removed on another line, and not
        added again after that removal. Empty with one tip."""
        tp = self.tips(o)
        if len(tp) <= 1: return frozenset()
        S, sets = self.S, []
        for t in tp:
            sub = [q for q in S.Cs if q["id"] == t["id"] or q["id"] in S.anc[t["id"]]]
            Q = self._at(sub)
            sets.append(frozenset(r["k"] for r in K.sel(Q.recs, obj=o) if Q._has(r, s)))
        return frozenset.union(*sets) - frozenset.intersection(*sets) - (self.tips_fold(s, o) or frozenset())

    def one(self, s, o):
        """The single holder, where the seat is single-valued (an owner): two live holders is none."""
        return K.group([r for r in K.sel(self.recs, obj=o) if self._has(r, s)], None, "one", "k")

    def snapshot(self):
        return frozenset((r["k"], r["scope"], r["obj"], r["depth"], r["root"]) for r in self.recs)


# ---- a lone removal in force: the end rule (conferral_end.py, E2 to E8) re-expressed over seat rows ----------------
def holds_roster(S, u, k, obj, r):
    """Unseat u cuts a roster seat key k holds: an offer in u's past seats k over obj in roster scope r (a member's
    seat, the founding seat where it holds `member`, an agent's seat). A cut of a roster scope the key does not hold
    ends no stay, and so no duty seat. (MUTATION roster_cut_any_scope: not read.)"""
    return seated_before([m for m in S.Cs if m["id"] in S.anc[u["id"]]], k, obj, r)


def seated_before(rows, k, obj, r):
    """holds_roster over `rows`, the concluded rows in the unseat's past."""
    if "roster_cut_any_scope" in MUT: return True
    return any(m["kind"] == "offer" and m.get("obj") == obj and k in m["to"]
               and ((m["scope"] == r if "founding_duty_unread" in MUT else r in seat_scopes(m, k))   # MUTATION: the offer's scope
                    or (r == "member" and m["id"] == obj and roster_seat(m))) for m in rows)


def lone_act(u, S):
    """u (a counted unseat that counts) is a moderator's lone removal of an agent's key made under the remover's
    standing: it concludes as a lone removal, and the room's count of it is not met (a removal the persons' count
    carries is the count's act, not the moderator's)."""
    if not agent_removal(u) or u.get("conf") != "group": return False
    P = [q for q in S.Cs if q["id"] in S.anc[u["id"]]]
    past = lambda a, b: a in S.anc[b]
    return lone_removal(u, P, past) and ("count_unread_lone" in MUT or not count_met(u, P, past))   # MUTATION: the count unread


def head_of_end(S, E, obj):
    """h_e, the head an end acts from (E1): the heads a counted end names; for a withdrawal, the newest counted acts
    on obj in its past (the newest roster heads its signer holds)."""
    if E["kind"] == "unseat": return tuple(E.get("head", ()))
    acts = [q for q in S.Cs if q["id"] in S.anc[E["id"]] and q["kind"] in ("offer", "unseat") and q.get("obj") == obj
            and (q.get("conf") == "group" or q["id"] == obj)]
    return tuple(a["id"] for a in K.frontier(S.anc, acts))


def later(S, hx, he):
    """A head x names has every head of h_e in its past: x is at a later head than the end (E3). A head of h_e that
    is not held makes nothing later."""
    if any(e not in S.by for e in he): return False
    return bool(he) and any(h in S.anc and all(e in S.anc[h] for e in he) for h in hx)


def standing_ends(S, x, standing, unseats, not_ends=frozenset()):
    """The rows held that end the remover's standing: a withdrawal of a standing offer by its holder (or by the
    conferrer of an offer that is not counted), of the holder's acceptance of one, or of the holder's stay; a counted
    unseat that cuts the holder's standing seat or its roster seat with a standing offer in its past. Each with the
    standing seats it ends: [(row, seats)]."""
    M, obj, by = x["signer"], x["obj"], S.by
    ids = {o for o, _ in standing}
    of = lambda oids: frozenset(s for s in standing if s[0] in oids)
    out = []
    stay = {w["id"] for w, k, g in stay_ends(K.sel(S.Cs, kind="withdraw"), by) if k == M and g == obj}
    for w in K.sel(S.Cs, kind="withdraw"):
        t = by.get(w["target"])
        if t is None: continue
        if t["kind"] == "offer" and t["id"] in ids and (w.get("scope") is None or (t["id"], w["scope"]) in standing) and (
                w["signer"] == M or (w["signer"] not in t["to"] and t["conf"] != "group" and not duty_seat(by, t))):
            out.append((w, frozenset(s for s in standing if s[0] == t["id"] and w.get("scope") in (None, s[1]))))
        elif t["kind"] == "accept" and t["signer"] == M and w["signer"] == M and t.get("of") in ids:
            out.append((w, of({t["of"]})))
        elif w["id"] in stay and any(o in S.anc[w["id"]] for o in ids):
            out.append((w, of({o for o in ids if o in S.anc[w["id"]]})))
    for u in unseats:
        if u["id"] == x["id"] or M not in u["to"] or u["obj"] != obj or not any(o in S.anc[u["id"]] for o in ids): continue
        if u["id"] in not_ends: continue                    # a lone removal out of force ends no standing (no cascade)
        if any(("seat", M, r, obj) in u["cuts"] and holds_roster(S, u, M, obj, r) for r in ROSTER_SEATS):
            out.append((u, of({o for o in ids if o in S.anc[u["id"]]})))
        elif any(("seat", M, sc, obj) in u["cuts"] for _, sc in standing):
            out.append((u, frozenset(s for s in standing if s[0] in S.anc[u["id"]] and ("seat", M, s[1], obj) in u["cuts"])))
    return out


def count_receipt(S, q, x):
    """The room's count's receipt of lone removal x (CIRISConstitution#218): a count over the persons of x's room,
    whatever room or scope the row states otherwise, at heads none older than x's (each is x's head or has it in its
    past), the remover no voice of it (as it is no receipter). Its count is the members' check of one member's act
    (room_count): more than half of the persons of the room less the remover, never fewer than two, whatever policy or
    need the row states (a row's own `accord_halt`, or a declared need of none, is no receipt; MUTATION
    receipt_row_policy: the row's policy read)."""
    obj, hx = x["obj"], tuple(x.get("head", ()))
    if "count_receipt_unchecked" not in MUT:                    # MUTATION: room, heads and remover not read
        if q.get("obj") != obj or q.get("over", obj) != obj: return False
        if not q.get("head") or not all(any(h == e or e in S.anc.get(h, ()) for e in hx) for h in q["head"]): return False
    P = [r for r in S.Cs if r["id"] in S.anc[q["id"]]]
    past = lambda a, b: a in S.anc[b]
    over = q.get("obj") if "count_receipt_unchecked" in MUT else obj
    scope = q.get("counted", "member") if "count_receipt_unchecked" in MUT else "member"
    mem, vot = counted_keys(P, past, over, tuple(q.get("head", ())), scope)
    left = left_in_past(P, over, scope)
    mem, vot = mem - left, vot - left
    yes = voices(q, P) & vot
    if "count_receipt_unchecked" not in MUT: yes = yes - {x["signer"]}
    # the room less the remover, in the base as in the voices (R5: one rule for a count that judges one member's act,
    # as the overturn and the lift; MUTATION remover_counted_over)
    if "remover_counted_over" not in MUT: mem = mem - {x["signer"]}
    if "receipt_row_policy" in MUT: return met(q.get("policy"), len(yes), len(mem), q.get("need"))
    return room_count(yes, mem)


def receipts_of(S, x, duty, unseats, not_ends):
    """The receipts of lone removal x held that may keep it in force, each with whether it is the count's: an `ack`
    whose `of` is x, by a duty holder at x's head other than the remover, or counted (`conf` group) and met over the
    persons at the heads it names (the room's count, the conferrer: CIRISConstitution#218, pin list: a count's own
    receipt). A single key's receipt is void where a counted unseat of a seat that key holds over the room does not
    have the receipt in its past (concurrent with it, or before it): conferral's key_cut (CIRISConstitution#218, pin
    list: a receipt by a key removed at the same time)."""
    out = []
    for q in S.Cs:
        if q["kind"] != "ack" or q.get("of") != x["id"]: continue
        if q.get("conf") == "group":
            if "count_receipt_unread" in MUT: continue          # MUTATION: the count's receipt is not read
            if count_receipt(S, q, x): out.append((q, True))
            elif "failed_count_is_signers" in MUT and q["signer"] in duty: out.append((q, False))   # MUTATION
            continue
        if q["signer"] not in duty: continue
        cut = any(q["signer"] in u["to"] and u.get("obj") == x["obj"] and u["id"] not in not_ends
                  and q["id"] not in S.anc[u["id"]] and ("receipt_before_kept" not in MUT or u["id"] not in S.anc[q["id"]])
                  and holds_roster(S, u, q["signer"], x["obj"], u["scope"])
                  for u in unseats)
        if cut and "removed_receipt_kept" not in MUT: continue   # MUTATION: a removed key's receipt keeps
        out.append((q, False))
    return out


def lifts_receipts(E, lone_ids, by):
    """An end that states it lifts the receipts of acts under the ended standing (`lifts`; conferral's word): then only
    the count's own receipt keeps (CIRISConstitution#218, pin list: a count end that lifts receipts). CC 2.4.1.1, "What
    stays in force", names three cases: (i) a counted end may lift; (iii) a conferrer that ends its own offer may lift,
    counted or not (its withdrawal of an offer that seats another); (ii) the holder's own end never lifts (its own
    withdrawal, its resignation; the text refuses such a row at the door, `lifts_on_own_end`, and the kernel, handed
    one, reads no lift). A moderator's lone removal lifts nothing."""
    if not E.get("lifts") or "lifts_unread" in MUT: return False
    if E["kind"] == "unseat": return E.get("conf") == "group" and (E["id"] not in lone_ids or "lone_lifts" in MUT)
    # (iii): in a room whose record seats duty holders they are equals and a conferrer's withdrawal ends no duty seat;
    # in one whose record seats none, the lone person duty holder's own offer of `moderate` (an elected moderator's,
    # say) is ended by its withdrawal, and that withdrawal may lift
    t = by.get(E.get("target")) if E["kind"] == "withdraw" else None
    return t is not None and t["kind"] == "offer" and (E["signer"] not in t["to"] or "own_end_lifts" in MUT) \
        and "conferrer_lift_unread" not in MUT


def removal_in_force(S, x, unseats, now, not_ends=frozenset(), lone_ids=frozenset()):
    """CC 4.5.13 read with the end rule (CC 2.4.1.1, CC 4.5.5; conferral_end.py): a moderator's lone removal x is an
    act under its `moderate` standing.
        E7      a seat that gave the remover `moderate` at the head x names is live now (`now`, the seats with every
                removal made) and no end of it is held: in force. A seat taken up after x's head authorises nothing
                earlier, and nothing puts the removal back in force once every such seat has an end held: not the
                same offer accepted again, not a new conferral (CC 2.4.1.1: "A receipt ... revives no act")
        E4      an end of its standing is in x's past: not counted, not in force
        E3      x names a head later than the end's head h_e: not counted, not in force
        E8      x is at h_e or before, or concurrent with it: counted, and in force only under a receipt of it that
                does not have the end in its past, by a duty holder at the head x names other than the remover
                (an `ack` row whose `of` is x); never by the remover itself
        E2      otherwise counted at its own head and not in force
    With several ends held, in force only where each keeps it. Where the standing is gone and no end of it is held
    (it fell with a seat above it), E2 and E8 with no end."""
    M, obj = x["signer"], x["obj"]
    standing, duty, agents = set(), None, None
    for h in x.get("head", ()):
        sub = [q for q in S.Cs if q["id"] == h or q["id"] in S.anc.get(h, ())]
        Q = seats_of(sub)
        standing |= {(r["offer"], r["scope"]) for r in Q.recs if r["k"] == M and r["obj"] == obj and Q._has(r, "moderate")}
        d = Q.holders("duty", obj)
        duty = d if duty is None else duty & d
        a = Q.holders(AGENT, obj)
        agents = a if agents is None else agents & a
    duty = (duty or frozenset()) - (frozenset() if "remover_receipt" in MUT else {M})
    # an agent's receipt is no receipt (CC 2.4.1.1: never the act's own signer's and never a node's; keeping
    # another's act in force is a voice, which an agent does not have): only a person duty holder receipts, for
    # every lone removal, a mutual pair's included (MUTATION agent_receipt_kept)
    if "agent_receipt_kept" not in MUT: duty = duty - (agents or frozenset())
    acks = receipts_of(S, x, duty, unseats, not_ends)
    kept = lambda E: any((E is None or E["id"] not in S.anc[q["id"]]) and (counted or E is None or not lifts_receipts(E, lone_ids, S.by))
                         for q, counted in acks)
    # an end in the past of the head x names did not end the standing live there (a seat taken up again after it)
    found = [(E, sc) for E, sc in standing_ends(S, x, standing, unseats, not_ends)
             if not all(E["id"] == h or E["id"] in S.anc.get(h, ()) for h in x.get("head", ()))]
    ended = frozenset().union(*(sc for _, sc in found)) if found else frozenset()
    live = {(r["offer"], r["scope"]) for r in now.recs if r["k"] == M and r["obj"] == obj}
    if now.stands(M, "moderate", obj) and ("reseat_revives" in MUT or any(s in live and s not in ended for s in standing)):
        return True                                             # MUTATION reseat_revives: any standing now keeps it
    ends = [E for E, _ in found]
    if not ends: return kept(None)
    for E in ends:
        if E["id"] in S.anc[x["id"]] or later(S, x.get("head", ()), head_of_end(S, E, obj)) or not kept(E):
            return False
    return True


def out_of_force(S, unseats, holds, confers, depth, own, checkpoint):
    """The lone removals among `unseats` the end rule holds out of force over S."""
    acts = [u for u in unseats if u.get("scope") == AGENT and lone_act(u, S)]
    if not acts: return frozenset()
    nows = {}

    def now(drop):
        if drop not in nows: nows[drop] = Seats(S, holds, confers, depth, own=own, checkpoint=checkpoint, drop=drop)
        return nows[drop]
    lone_ids = frozenset(x["id"] for x in acts)
    by = {x["id"]: x for x in acts}
    # No cascade (CIRISConstitution#218, pin list: no cascade): a lone removal out of force ends no standing. (It
    # voids no receipt either, since a receipter is a person and a lone removal removes only an agent.) So an act's
    # verdict waits for the verdict of every other lone removal y that could end its remover's standing (y removes
    # its signer), whether y is in its past (an end it reads under E4 only if y is in force), concurrent
    # with it, or after it (E8). One exception, an ordered pair: where y has x in its past and x could end y's
    # standing too, y is in force only if x is not (x, in force, is an end in y's past), so y cannot be what puts x
    # out of force. x is decided first, without y (y no end of it and no cut in its reading), and y then reads x's
    # verdict: x in force ends y's standing; x out of force ends nothing (MUTATION ordered_pair_cascade: the old
    # order, y decided first with x read as an end before x's own verdict was known). The acts are decided one
    # strongly connected component at a time, in rounds: every component whose waits are decided, against what the
    # rounds before decided out of force. A component of two or more (agent moderators removing each other at one
    # head, a pair or a ring) is decided together, each read as an end of another's: CC 2.7.7 rule 5, "Two cuts by
    # keys of equal standing that undo each other stay contested. A voice that the other cannot remove settles them",
    # read for a set (a person's receipt, or the count's).
    dep = lambda x, y: y is not x and y["obj"] == x["obj"] and y["to"][0] == x["signer"]     # y could end x's standing
    after = {x["id"]: frozenset(y["id"] for y in acts if dep(x, y) and dep(y, x) and x["id"] in S.anc[y["id"]])
             for x in acts}                                       # the ordered pairs x opens
    if "ordered_pair_cascade" in MUT:
        waits = {x["id"]: {y["id"] for y in acts if dep(x, y) and y["id"] not in S.anc[x["id"]]} for x in acts}
        after = {i: frozenset() for i in after}
    else:
        waits = {x["id"]: {y["id"] for y in acts if dep(x, y) and y["id"] not in after[x["id"]]} for x in acts}
    decided, out = {}, set()
    while len(decided) < len(acts):
        pend = [x["id"] for x in acts if x["id"] not in decided]
        reach = {}
        for i in pend:
            seen, todo = set(), [i]
            while todo:
                for j in waits[todo.pop()]:
                    if j not in decided and j not in seen:
                        seen.add(j); todo.append(j)
            reach[i] = seen
        comps = []
        for i in pend:
            comp = frozenset({i} | {j for j in reach[i] if i in reach[j]})
            if comp not in comps and all(j in decided or j in comp for m in comp for j in waits[m]):
                comps.append(comp)
        excl = frozenset() if "cascade" in MUT else frozenset(out)
        got = {}
        for comp in comps:
            for i in sorted(comp):
                if "cycle_one_then_other" in MUT:                    # MUTATION: a component decided in turn
                    excl = frozenset(out | {k for k, v in got.items() if not v})
                ex = excl | after[i]                                 # an ordered pair's later act is no end of the earlier
                got[i] = removal_in_force(S, by[i], unseats, now(ex), ex, lone_ids)
        decided.update(got)
        out |= {i for i, v in got.items() if not v}
    return frozenset(i for i, v in decided.items() if not v)


def stands(S, root, k, s, o, **kw):
    return Seats(S, **kw).stands(k, s, o, root)


# ---- concluded: was the offer, the unseat, the withdrawal validly made, at the head it names -------------
def members_at(P, past, obj, heads, scope="member"):
    """The live `scope` seats over obj, read from the rows in the past of the heads only. Several heads: the
    keys common to all of them (KERNEL.md section 7)."""
    out = None
    for h in heads:
        sub = [q for q in P if q["id"] == h or past(q["id"], h)]
        if not any(q["id"] == h for q in sub): return frozenset()
        m = seats_of(sub).holders(scope, obj)
        out = m if out is None else out & m
    return out or frozenset()


_SEATS_OF = {}


def seats_of(rows):
    """The seats over a set of rows, each taken as concluded, kept once built: a head's past is read again by every
    row that names it, and a chain of lone removals reads every earlier one's (the run is polynomial in the chain,
    not exponential). The key is the rows themselves (by identity, held in the value so none is reused), the planted
    breaks switched on, and the tables a check may change (what a seat holds, the policies, the enders)."""
    key = (frozenset(id(q) for q in rows), frozenset(MUT), repr(sorted(HOLDS.items())), repr(sorted(POLICY.items())),
           repr(sorted(ENDS.items())))
    got = _SEATS_OF.get(key)
    if got is None:
        got = _SEATS_OF[key] = (tuple(rows), Seats(CK.State(list(rows), {q["id"]: True for q in rows})))
    return got[1]


def agents_at(P, past, obj, heads):
    """The keys holding an AI agent's seat over obj at the heads (`agent`): on the roster, in no count."""
    if not any(q.get("scope") == AGENT for q in P): return frozenset()
    return members_at(P, past, obj, heads, AGENT)


def counted_keys(P, past, obj, heads, scope="member"):
    """(over, voters): the keys a count over `scope` at the heads is taken of, and those whose signatures are its
    voices. Every count of a room is by person (CC 4.5.13: an agent "has no vote"; "a recall and an election count its
    persons alone"), so an agent's key is in neither, whatever scope it holds besides."""
    m = members_at(P, past, obj, heads, scope)
    if scope == AGENT: return m, m
    a = agents_at(P, past, obj, heads)
    over = m | a if "agent_counted_over" in MUT else m - a      # MUTATION: the agent is counted over (no voice)
    voters = m | a if "agent_voice" in MUT else m - a           # MUTATION: the agent's signature is a voice
    return over, voters


def seated_after(P, past, obj, k, w, seats):
    """Whether P (a counted row's past) holds an offer over obj seating k, by `seats`, that has the leaving w in its own
    past: a seating of the key after its leaving. The one test of a re-admission, read by left_in_past and
    stay_ended_in_past."""
    if "readmit_unread" in MUT: return False
    return any(m["kind"] == "offer" and m.get("obj") == obj and k in m.get("to", ()) and seats(m) and past(w["id"], m["id"])
               for m in P)


def _past_in(P):
    by = {q["id"]: q for q in P}
    return lambda a, b: a in K.ancestors(by, b)


def left_in_past(P, obj, scope="member", past=None):
    """The keys whose own leaving is among P (a version's past) with no seating of the key in that scope after it
    there: a concluded withdrawal, signed by the key, of the acceptance or offer that seats it in `scope` over obj.
    KERNEL.md 6 and 7; RosterHead.lean leaving_binds_by_past: a version that has a key's leaving in its own past does
    not count that key, whatever head it names, unless a re-admission of the key after that leaving is in that past
    too (CIRISConstitution#218, pin list: a re-admitted member counts)."""
    if "leaving_unread" in MUT: return frozenset()
    by = {q["id"]: q for q in P}
    past = past or _past_in(P)
    out = set()
    for w in P:
        if w["kind"] != "withdraw": continue
        t = by.get(w["target"])
        # a withdrawal that names a scope leaves that one seat of the row it withdraws (a founder's duty laid down)
        ts = w["scope"] if w.get("scope") is not None and "scope_unread" not in MUT else t.get("scope") if t else None
        if t is None or t.get("obj") not in (obj, None) or ts not in (scope, None): continue
        if (t["kind"] == "accept" and t["signer"] == w["signer"]) or (t["kind"] == "offer" and w["signer"] in t["to"]):
            if not seated_after(P, past, obj, w["signer"], w, lambda m: m["scope"] == scope):
                out.add(w["signer"])
    return frozenset(out)


def stay_ended_in_past(P, past, obj):
    """The keys whose own end of a stay as a member of obj is among P (a counted row's past) with no admission of the
    key after it there: a count over the duty holders that has such an end in its past does not count that key, since
    the end ended its duty seats. The counted removal needs no such reading: it is a head, read by members_at."""
    if "leaving_unread" in MUT or "resign_keeps_duty" in MUT: return frozenset()
    by = {q["id"]: q for q in P}
    if not community(by, obj): return frozenset()
    return frozenset(k for w, k, g in stay_ends(P, by) if g == obj and not seated_after(P, past, obj, k, w, roster_seat))


def count_left(P, past, obj, scope):
    """The keys a count over `scope` at obj leaves out for a leaving in its row's past: the leaving of that seat, and for
    a count over duty holders, the end of the key's stay as a member. A count over another scope is as it was."""
    out = left_in_past(P, obj, scope, past)
    by = {q["id"]: q for q in P}
    return out | stay_ended_in_past(P, past, obj) if is_duty(scope, declared(by, obj)) else out


def voices(r, P):
    """The keys that signed r: its signer, its cosigners, and the signers of the cosign rows it names that themselves
    name every head r is counted over."""
    heads = set(r.get("head", ()))
    return signers(r) | frozenset(c["signer"] for c in K.sel(P, kind="cosign", of=r.get("content", r["id"]))
                                  if c["id"] in r["names"] and heads <= set(c["names"]))


def private_room(by, obj):
    """obj is a private room: a community whose founding row declares `membership` `private` (CC 3.1.3.2). A founding
    row with no `membership` reads public. A room is private or public by its founding row, and no record change moves
    it (people found a new room). A seating this refuses is the text's `membership_room_key_ended`."""
    if "public_final" in MUT: return community(by, obj)          # MUTATION: room-key finality reaches a public room
    return community(by, obj) and by[obj].get("membership") == "private"


def room_key_ended(k, sc, obj, P, past, by):
    """The end of key k's roster seat sc over obj is among P (a row's concluded past), and it stands: a removal that
    is no moderator's lone act (an unseat of that seat whose count is met over its own past, or not counted at all),
    with an offer seating k in sc in its past; or k's own end of its stay (stay_ends: its withdrawal of the offer, of
    its acceptance, or of the founding row). A moderator's lone removal is never final (the members may lift it; out
    of force it ends nothing), so a re-seating with one in its past is a lift or a seating, never refused here."""
    for q in P:
        if q["kind"] != "unseat" or q.get("obj") != obj or q.get("scope") != sc or k not in q["to"]: continue
        Pq = [x for x in P if past(x["id"], q["id"])]
        if not seated_before(Pq, k, obj, sc): continue           # it ended no seat of k's
        if q.get("conf") != "group" or "lone_final" in MUT or count_met(q, Pq, past):   # MUTATION lone_final: a lone removal is final
            return True
    if "resign_not_final" in MUT: return False                   # MUTATION: a resignation is no end of the seat
    return any(k2 == k and g == obj for _, k2, g in stay_ends(P, by))


def _revoked_before(r, P, past):
    """Finality (FINAL): offer or acceptance r would seat a key again in a scope whose end is final, with that end in
    its past. A scope that is no roster seat (`registered`): a concluded unseat of the slot in r's past. A roster seat
    (a room key's seat in a private room): room_key_ended, and an acceptance of an offer seating the key is read as
    the offer is (accepting the same offer again after a resignation seats nothing). A row concurrent with the end is
    not refused: the cut voids it (a removal), or it seats (a resignation it does not have in its past)."""
    if "reseat" in MUT: return False
    by = {q["id"]: q for q in P}
    if r["kind"] == "accept":
        if "reaccept_reseats" in MUT: return False              # MUTATION: the same offer accepted again re-seats
        o = by.get(r.get("of"))
        if o is None or o["kind"] != "offer": return False
        obj, seats = o["obj"], [(r["signer"], sc) for sc in seat_scopes(o, r["signer"])]
    else:
        if r["obj"] == r["id"]: return False                    # a founding row has no past
        if r["scope"] not in ROSTER_SEATS:
            return any(q["kind"] == "unseat" and q["scope"] in FINAL and set(q["cuts"]) & set(r.get("on", ())) for q in P)
        obj, seats = r["obj"], [(k, r["scope"]) for k in r["to"]]
    if "room_key_unread" in MUT or not private_room(by, obj): return False     # MUTATION: room-key finality unread
    return any(sc in ROSTER_SEATS and sc in FINAL and room_key_ended(k, sc, obj, P, past, by) for k, sc in seats)


def _ender(r, P, by):
    """An unseat by the holder of a seat over the same object (ENDS). Read over the unseat's own past only: the
    ender's seat stands there, and it is the one live holder of that scope over the object."""
    if "any_key_revokes" in MUT: return True
    up = by.get(r.get("under"))
    if up is None or up["kind"] != "offer" or up["obj"] != r["obj"] or r["signer"] not in up["to"]: return False
    if r["scope"] not in ENDS.get(up["scope"], ()): return False
    # it ends another scope's seat of the object's own key, or (the same scope) the ender's own seat
    if tuple(r["to"]) != ((r["signer"],) if r["scope"] == up["scope"] else (r["obj"],)): return False
    if "owner_unread" in MUT: return True                         # MUTATION: the binding named is enough
    sole = Seats(CK.State(P, {q["id"]: True for q in P}))
    if "owner_any_live" in MUT: return sole.stands(r["signer"], up["scope"], r["obj"])
    return sole.one(up["scope"], r["obj"]) == r["signer"]


def on_object(by, h, obj, n=0):
    """Row h is a row of object obj's own line: obj's founding row, a row whose object is obj (an offer, an unseat,
    a standing acceptance, a counted receipt), a withdrawal, acceptance, receipt, answer, ballot or cosignature of
    such a row, or a row of no object of its own that names one (a version of the roster, as persist presents a
    ballot's head: `consensus::ballot_rows`). A row whose object is another is of that other's line."""
    if h is None or n > 8: return False
    if h["id"] == obj or h.get("obj") == obj: return True
    if h.get("obj") is not None: return False
    ref = h.get("target") if h["kind"] == "withdraw" else h.get("of")
    # a row whose `of` names itself (a merge head presented as its own cosignature) refers to nothing else: read it
    # by the rows it names
    if ref is not None and ref != h["id"]: return on_object(by, by.get(ref), obj, n + 1)
    return any(on_object(by, by.get(m), obj, n + 1) for m in h.get("names", ()))


def heads_on_object(r, by):
    """A counted row's heads are heads of its own object (CC 4.5.4 and the review of #54: a count is over the room
    it acts in, so it names that room's heads): each head a row of the object's own line (on_object). MUTATION
    heads_any_object: a head of another object's line counts."""
    if "heads_any_object" in MUT: return True
    return all(on_object(by, by.get(h), r["obj"]) for h in r.get("head", ()))


def duty_gate(r, by, table=None):
    """CC 4.5.4: a duty seat is placed only by the founding record, by "the duty holders of C, counted under line
    (iv)", or by "the members' count under line (v)", which "is the election of rule 2". So a counted offer of a duty
    scope over a community concludes only where it is the duty holders' count, or is an election's acceptance (the
    ranked tally). The duty holders' count is the count over all the duty holders of the room it confers in:
    `counted` the duty holders' scope itself (`duty`; one duty's holders are not all of them), under the duty policy
    `duty_confer` (a strict majority of the holders, never fewer than two unless one; a policy the row states
    otherwise, `accord_halt` say, is not that count), over the room itself (`over` absent or the room). A members'
    count under an admission-style policy confers no duty, whether or not a duty holder lives (CIRISConstitution#241).
    A seat that makes its holder no duty holder (a node's detector seat) is not reached. (MUTATIONS duty_gate_off;
    duty_gate_wrong_row: `counted` read off the room; gate_counted_any_duty: one duty's holders pass; gate_policy_unread:
    any policy passes; duty_over_unread: a count over another room passes.)"""
    if "duty_gate_off" in MUT or not community(by, r["obj"]) or not is_duty(r["scope"], declared(by, r["obj"])): return True
    if r.get("over", r["obj"]) != r["obj"] and "duty_over_unread" not in MUT: return False
    if K.rule(table or POLICY, r.get("policy"), ("unknown",))[0] == "ranked": return True
    src = by.get(r["obj"], {}) if "duty_gate_wrong_row" in MUT else r
    counted = src.get("counted", "member")
    if not (counted == "duty" or ("gate_counted_any_duty" in MUT and is_duty(counted, declared(by, r["obj"])))): return False
    return r.get("policy") == "duty_confer" or "gate_policy_unread" in MUT


def duty_over(r, by):
    """A counted unseat of a duty scope over a community (the holders' withdrawal of a duty, the members' recall) is
    counted over the room it ends the seat in: `over` absent or the room (MUTATION duty_over_unread)."""
    if "duty_over_unread" in MUT or not community(by, r["obj"]) or not is_duty(r["scope"], declared(by, r["obj"])): return True
    return r.get("over", r["obj"]) == r["obj"]


def count_met(r, P, past, table=None):
    """A counted row's count (conf=group), met over its concluded ancestors P: the lift, the ranked tally, the duty
    count, or the policy's threshold over the persons at the heads it names."""
    k, by, heads = r["kind"], {q["id"]: q for q in P}, r.get("head", ())
    if K.rule(table or POLICY, r.get("policy"), ("unknown",))[0] == "lift": return lift_count(r, P, past, by)
    mem, vot = counted_keys(P, past, r.get("over", r["obj"]), heads, r.get("counted", "member"))
    left = count_left(P, past, r.get("over", r["obj"]), r.get("counted", "member"))
    mem, vot = mem - left, vot - left
    if K.rule(table or POLICY, r.get("policy"), ("unknown",))[0] == "ranked":
        # the election's seating (C1 to C5): its electorate read at its election's vacancy, not at a head
        return election_count(r, P, past, by)
    if r.get("policy") in DUTY_POLICY: return duty_count(r, P, voices(r, P) & vot, mem)
    if k == "unseat" and K.rule(table or POLICY, r.get("policy"), ("unknown",))[0] == "recall" and "recall_as_strictfloor" not in MUT:
        # the recall judges one holder: counted over the members less the holder it recalls, and that holder no voice
        # of it, as the lift is counted over the room less the one it judges. A row is a recall when its policy reads
        # as the `recall` count (the table's `moderator_recall`)
        judged = frozenset(r["to"])
        base = mem if "recall_holder_in_base" in MUT else mem - judged
        yes = (voices(r, P) & vot) - (frozenset() if "recall_holder_voice" in MUT else judged)
        return met(r.get("policy"), len(yes), len(base), r.get("need"), table)
    return met(r.get("policy"), len(voices(r, P) & vot), len(mem), r.get("need"), table)


def seat_rule(r, P, past, table=None, other=None):
    """The conclusion rule. P: r's concluded ancestors."""
    k, by = r["kind"], {q["id"]: q for q in P}
    if k in ("offer", "unseat"):
        conf = r["conf"]
        if k == "offer" and _revoked_before(r, P, past): return False   # a revoked key does not re-seat itself (FINAL)
        # a single key's own offer of a duty (or one under its seat) concludes only where that key is the lone person
        # duty holder: "by a strict majority of the duty holders, or by the lone holder with the new holder's
        # acceptance" (CC 4.5.4), in every community (CIRISConstitution#241; MUTATION own_duty_ungated: duty rooms only)
        if k == "offer" and conf in ("self", "seat") and r["obj"] != r["id"] and (duty_seat(by, r) or (
                "own_duty_ungated" not in MUT and community(by, r["obj"]) and is_duty(r["scope"], declared(by, r["obj"])))) \
                and not _lone(r, P, by): return False
        if conf == "group" and not heads_on_object(r, by): return False       # a count names its own room's heads
        if k == "offer" and conf == "group" and not duty_gate(r, by): return False   # CC 4.5.4: who places a duty
        if k == "unseat" and conf == "group" and not duty_over(r, by): return False  # and over which room
        if conf == "self":
            if r["obj"] == r["id"]: return k == "offer"          # a founding row is its own object
            if k == "unseat" and founding_many(by, r["obj"]): return False    # among several founding keys, ending a seat takes the count
            return r["signer"] in own_keys(by, r["obj"])
        if conf == "seat":
            if k == "unseat": return _ender(r, P, by)
            return k == "offer" and r.get("under") in by and r["signer"] in by[r["under"]]["to"]
        if conf == "group":
            if k == "unseat" and lone_removal(r, P, past): return True          # CC 4.5.13: a moderator, an agent's key
            return count_met(r, P, past, table)
        return False
    if k == "accept":
        if _revoked_before(r, P, past): return False           # a room key whose seat's end stands is not seated again (FINAL)
        return r["of"] is None or (r["of"] in by and r["signer"] in by[r["of"]].get("to", ()))
    if k == "withdraw":
        t = by.get(r["target"])
        # (2): an end of a seat that has an end of that seat in its own past is no end: a second withdrawal by its
        # signer of the same row and the same seat concludes nothing (MUTATION end_of_ended_seat)
        if "end_of_ended_seat" not in MUT and any(
                w["kind"] == "withdraw" and w["signer"] == r["signer"] and w.get("target") == r["target"]
                and w.get("scope") == r.get("scope") for w in P):
            return False
        return t is not None and (r["signer"] in signers(t) or (t["kind"] == "offer" and r["signer"] in t["to"]))
    if k == "cosign":
        return True
    return other(r, P, past) if other else True
