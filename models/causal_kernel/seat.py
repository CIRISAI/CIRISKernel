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
A node's seat (scope `node`) over an infrastructure community, placed by the founders' count, needs no acceptance (a
node has no agency): by its scope and the object's kind alone. Every other seat needs the seated key's own consent; no
flag on a row waives it.

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
                  the removal (`content`), names the newest counted changes in its own past (H4, no exemption), and
                  names objections (answers `object` to the removal). Its voices are the signers of those objections
                  and no other key; the removal's author is no voice, and the key it seats is an agent's, so it is
                  in no count. It concludes when those voices are a strict majority of the persons seated at BOTH
                  the removal's head and the lift's own heads (lift_base), the removal's author apart, never fewer
                  than two: the overturn's count. It restores and does not admit: the key it seats held its `agent`
                  seat at the removal's head.
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
            out[f["family"]] = ("protocol", 0, 0)               # the room's declared protocol: its founding record's
        elif e.get("kind") == "ranked_irv":
            out[f["family"]] = ("ranked", 0, 0)                  # the count is the ranked tally (formal/ranked_choice)
        else:
            out[f["family"]] = ("not_a_count", 0, 0)             # role_at: a seat, not a threshold
    return out


POLICY = policy_table()


def acts_table(path=None):
    """The act-to-policy binding (data/governance_policy_acts.tsv): one row per (act, scope, community kind), the policy
    rows it may take, and whether the counted row states one of them (`row`) or the act fixes it (`fixed`: the row
    states it or none, and a row stating another policy concludes nothing)."""
    path = path or os.path.join(ROOT, "data", "governance_policy_acts.tsv")
    out = []
    for line in open(path, encoding="utf-8"):
        if line.startswith("#") or not line.strip() or line.startswith("act\t"): continue
        act, scope, kind, policy, choice = line.rstrip("\n").split("\t")[:5]
        out.append((act, scope, kind, tuple(policy.split("|")), choice))
    return tuple(out)


# A row the model reads before the Constitution's table carries it, read only where the table has no row for its (act,
# scope, kind): a community's onward acceptance edge (trust_rows.py) is counted over its authority set as a duty
# conferral is (CC 4.5.4's authority_set(C), the ruling of 2026-11-27), being added to rc23-next. Drop it when it lands.
# A community's license seat (trust_rows.py, the issuer's standing) is conferred and withdrawn by its duty holders, as a
# detector seat is (the ruling of 2026-11-27): seat_confer / seat_withdraw of scope `license`. An affiliation's is its
# officers' act under its protocol (the officers ruling, built on persist-gaps).
# An affiliation's license seat is its body's act under its declared protocol (the ruling: its officers; until the
# officer body lands, body_of reads its members).
ACTS = acts_table()     # read by policy_in_force (the refusal), with the binding on (BOUND); policy pin 8ec76cce

# The kind of an object (the acts table's `community_kind`, the policy table's `corridor` reading), from its founding row's
# scope: the scopes named here found an accord or a self roster; every other founding row founds a community. A key
# object is a self roster. An object with no founding row has no kind and no act.
# a founding row of scope `key` founds a voice's roster of room keys (CC 3.1.3.2): the table's kind `voice`, bound to the
# self roster's rows; a self roster's founding scope is `self`
KINDS = {"member": "community", "duty": "community", "holder": "accord", "self": "self", "key": "voice"}


def kind_of(by, obj, is_key=False):
    """The kind of obj: `self` for a key object; else, for a founding row, its scope read through KINDS, a community
    where KINDS names none (the binding reaches every room, whatever scope founds it); None for an object with no
    founding row held."""
    if is_key: return "self" if "key_kind_unread" not in MUT else None
    g = by.get(obj)
    if g is None or g["kind"] != "offer" or g.get("obj") != g["id"]: return None
    if "kind_unread" in MUT: return "community"                  # MUTATION: every founding row a community
    # the group kind of the founding record (a family record carries `family_key_id`): `family` or `community`; a
    # community's cohort_subkind then splits off an infrastructure community
    if g.get("group_kind") == "family": return "family"
    k = KINDS.get(g["scope"]) if "kind_partial" in MUT else KINDS.get(g["scope"], "community")   # MUTATION kind_partial
    # a community's record says whether it is an infrastructure community: `cohort_subkind` (any other value, or none,
    # is a community)
    if k == "community" and g.get("cohort_subkind") == "infrastructure" and "subkind_unread" not in MUT:
        return "infrastructure"
    # an affiliation (CC 3.4.7, CC 4.4.3.12: a licensing authority) is a community record whose `declared_cohort` is
    # `affiliations`
    if k == "community" and g.get("declared_cohort") == "affiliations" and "affiliation_unread" not in MUT:
        return "affiliation"
    return k


def act_of(r, by, is_key=False):
    """The act a counted row is, decided from its kind, its scope and its object, never from the policy it states:
    (act, scope class, kind) as the acts table writes them, or None (not a counted act, or an object with no kind).
        community  an offer whose `content` names an unseat of the same seat (object, scope, keys) is the lift, of
                   that seat's scope (the table binds the agent's); an offer or unseat of a roster seat is an admission
                   or a removal of that seat; one of a detector seat (`detect:*`) is the holders' conferral or
                   withdrawal of that seat; an offer of `moderate` under the ranked count is the election's seating
                   (THE ONE ACT READ FROM THE STATED POLICY, for this tag: the election is not answered safely by it);
                   another offer of a duty is the duty holders' conferral; an unseat of a duty counted over all the
                   duty holders (`counted` `duty`) is their withdrawal, one counted over the members (`member`, or
                   none) is the recall, and one counting any other body is no act. Any other scope, or none, is no
                   act.
        accord     a counted row over the selection (`selection`) is a steward purge; any other is a standing act.
        self, voice  an offer or unseat of a key, or of the roster's own seat, admits or removes a key (a voice's room
                   keys: a founding scope `key`, CC 3.1.3.2).
    election_open (the members' opening of an election) has a row in the acts table and no arm here: its row's shape is
    the election-close lane's.
    A moderator's lone removal is a removal by its shape; whether it is counted at all is the seat rule's."""
    # the halt's confirmation (the ruling of 2026-11-28): a cosigned accord:lifecycle:confirmed row naming a halt of the
    # accord it is over is halt_confirm, counted by accord_halt (MUTATION confirmation_no_act)
    if r["kind"] == CONFIRMED and "confirmation_no_act" not in MUT:
        return ("halt_confirm", "halt", "accord") if confirmed_halt(r, by) is not None and kind_of(by, r.get("obj")) == "accord" else None
    if r["kind"] not in ("offer", "unseat") or r.get("conf") != "group": return None
    obj, sc, offer = r.get("obj"), r.get("scope"), r["kind"] == "offer"
    kind = kind_of(by, obj, is_key)
    if kind is None: return None
    if sc is None and kind != "accord": return None    # no scope: no act (as the crate)
    if kind == "family":
        # a family's acts (the table's family rows): an admission and a removal of a member, a promotion to and a
        # demotion from the founder role (counted as an admission and as a removal: F1), a change of the record and its
        # dissolution. No duty seat, no moderator, no agent (F4)
        if sc == "record" and offer:
            return ("dissolve" if r.get("dissolved_at") is not None else "record_change", "record", kind)
        if sc in ("member", "founder"): return ("admit" if offer else "remove", "member", kind)
        return None
    if kind == "community":
        c = lifted(r, by)
        if offer and sc == "act" and c is not None and family(c) in LONE_ACTS and c.get("obj") == obj:
            return ("lift", "act", kind)                     # the lift of a duty holder's lone act
        if offer and c is not None and c["kind"] == "unseat" and c.get("obj") == obj and c.get("scope") == sc \
                and tuple(c.get("to", ())) == tuple(r.get("to", ())) and "lift_unread" not in MUT:
            return ("lift", sc, kind)                        # the seat re-seated: the table's row is of scope `agent`
        if sc in ROSTER_SEATS: return ("admit" if offer else "remove", sc, kind)
        # a license seat (the issuer's standing over the community, trust_rows.py): conferred and withdrawn by the duty
        # holders' count; its holder is no duty holder
        if sc == "license" and "license_seat_unread" not in MUT:
            return ("seat_confer" if offer else "seat_withdraw", "license", kind)
        # a detector seat (CC 4.5.7: `detect:{list id}`, conferred and "withdrawn by the count of (iv)"): no declared duty
        if (sc == "detect" or sc.startswith("detect:")) and "detect_unread" not in MUT:
            return ("seat_confer" if offer else "seat_withdraw", "detect", kind)
        # a change of the community's record (its consensus_protocol, say): the act record_change
        if sc == "record" and offer and r.get("dissolved_at") is not None: return ("dissolve", "record", kind)
        if sc == "record" and offer and "record_unread" not in MUT: return ("record_change", "record", kind)
        dec = declared(by, obj)
        if not is_duty(sc, dec): return None
        if offer:
            # THE ONE ACT READ FROM THE STATED POLICY: the election is not answered safely by this tag, and a caller must
            # not rely on a ranked seating (CIRISConstitution#241: the election is out of 0.5.0)
            # the election seats `moderate` alone (CC 4.5.13): a ranked offer of another duty is that duty's conferral
            if K.rule(POLICY, r.get("policy"), ("unknown",))[0] == "ranked" and "election_unread" not in MUT \
                    and (sc == "moderate" or "election_any_duty" in MUT):
                return ("election_seating", "moderate", kind)
            return ("duty_confer", "duty", kind)
        if "recall_by_policy" in MUT:
            holders = K.rule(POLICY, r.get("policy"), ("unknown",))[0] == "duty"
            return ("duty_withdraw" if holders else "recall", "duty", kind)
        # the body counted is the act's (CC 4.5.4 (iv), 4.5.13): the duty holders exactly (`duty`) withdraw a duty, the
        # members exactly (persons: agents and nodes are in no base) recall its holder; any other body is no act
        counted = r.get("counted", "member")
        if "body_free" in MUT: return ("duty_withdraw" if is_duty(counted, dec) else "recall", "duty", kind)
        if counted == "duty": return ("duty_withdraw", "duty", kind)
        if counted == "member": return ("recall", "duty", kind)
        return None
    if kind == "infrastructure":
        # the founders' own roster, and a node's seat (placed and removed by the founders' count; no voice, no base)
        if sc == "record" and offer and "record_unread" not in MUT and "infra_record_frozen" not in MUT:
            return ("record_change", "record", kind)
        return ("admit" if offer else "remove", sc, kind) if sc in ("founder", NODE) else None
    if kind == "accord":
        # a steward purge (CC 2.4.1.1, CC 3.3.2): a counted row over the selection the trust root's holders count
        if sc == "selection" and "purge_unread" not in MUT: return ("purge", "selection", kind)
        return ("standing_act", "any", kind)
    if kind == "affiliation":
        # an affiliation's acts (the table's affiliation rows, CC 4.4.3.12): an appointment of a member (the appointee's
        # acceptance is the second consent), a removal of one (affiliation_removal), a promotion to and a demotion from
        # the officer role (counted as an appointment and as a removal, as a family's founder role), a change of the
        # record and its dissolution. No duty seat
        if sc == "record" and offer:
            return ("dissolve" if r.get("dissolved_at") is not None else "record_change", "record", kind)
        if sc in ("member", OFFICER) and (not offer or "affiliation_admit_unread" not in MUT):
            return ("admit" if offer else "remove", "member", kind)
        if sc == "license" and "license_seat_unread" not in MUT:
            return ("seat_confer" if offer else "seat_withdraw", "license", kind)
        return None
    if kind in ("self", "voice"):
        # a self roster's keys, and a voice's room keys (CC 3.1.3.2: the self roster's door, kind `voice`)
        own = by.get(obj, {}).get("scope")
        return ("admit" if offer else "remove", "key", kind) if sc is not None and sc in ("key", own) else None
    return None


# The closed set of protocols a community's record may declare (CC 3.3.4; data/consensus_protocols.tsv, its `kind`
# column): each a count over a body, for an admission and for a removal. A word outside the set is no protocol. A
# quorum's number, and a weighted count's weights and threshold, are the RECORD's (the word, and the record row that
# states it), never a counted row's. The kind each word parses to, read by met()/count_of() as a policy row is.
PROTOCOL_KINDS = ("founder_only", "unanimous", "majority", "quorum:{m}/{n}", "weighted:{rubric}", "open:self_admit")


def protocol_sheet(path=None):
    """data/consensus_protocols.tsv as data: the head of each kind (protocol_rule's kind) -> its row's cells."""
    path = path or os.path.join(ROOT, "data", "consensus_protocols.tsv")
    out = {}
    for line in open(path, encoding="utf-8"):
        if line.startswith("#") or not line.strip() or line.startswith("kind\t"): continue
        kind, count_set, rule, removal_set, removal_rule = line.rstrip("\n").split("\t")[:5]
        head = kind.split(":")[0] if kind.split(":")[0] in ("quorum", "weighted") else kind
        out[head] = dict(count_set=count_set, rule=rule, removal_set=removal_set, removal_rule=removal_rule)
    return out


SHEET = protocol_sheet()
# the community floor of voices (the policy table's min_count): a count under a policy row alone never takes fewer
COMMUNITY_FLOOR = json.load(open(os.path.join(ROOT, "data", "governance_policy.json"), encoding="utf-8"))["min_count"]["community"]


def removal_floor(path=None):
    """A community's removal floor, read from the policy table's community_remove row (its floor cell, `2 voices` at
    pin 6b7471d6: "never fewer than two voices, so a room of two removes nobody"); 0 where the cell states none."""
    path = path or os.path.join(ROOT, "data", "governance_policy.json")
    for f in json.load(open(path, encoding="utf-8"))["families"]:
        if f["family"] == "community_remove":
            fl = f.get("floor_rule") or {}
            return fl.get("count", 0) if fl.get("kind") == "voices" else 0
    return 0


REMOVAL_FLOOR = removal_floor()


# The protocol sheet has no column for a change of the record (or any act but an admission and a removal): the column
# is DERIVED from the count set. A protocol whose count set is the members states a rule for it; open:self_admit (the
# joiner's own signature) and founder_only (the founder role) do not (ruled with the reading of `&`).
def protocol_states(kind, act):
    """Whether protocol `kind` (protocol_rule's) states a rule for `act`, read from the sheet: an admission by its
    `rule` cell, a removal by its `removal_rule` cell (`unstated` states none); any other act counted under the
    protocol (a change of the record) by its count set: a count of the members states one, the joiner's own
    signature (open:self_admit) and the founder role (founder_only) do not."""
    row = SHEET.get(kind)
    if row is None: return False
    if act == "admit": return row["rule"] != "unstated"
    if act == "remove": return row["removal_rule"] != "unstated"
    return row["count_set"] == "member"


def _count(w):
    """A whole number of the protocol word: one to nine digits, no leading zero (one spelling per number)."""
    return int(w) if 1 <= len(w) <= 9 and w.isascii() and w.isdigit() and w[0] != "0" else None


def protocol_rule(word):
    """The protocol a record's word names: (kind, m, n) with kind one of PROTOCOL_KINDS' heads and m, n a quorum's
    numbers (None otherwise), or None for a word outside the set."""
    if not isinstance(word, str): return None
    if word in ("founder_only", "unanimous", "majority", "open:self_admit"): return (word, None, None)
    if "protocol_set_open" in MUT: return (word, None, None)     # MUTATION: any word is a protocol (read as majority)
    if word.startswith("quorum:") and word.count("/") == 1:
        m, n = (_count(x) for x in word[len("quorum:"):].split("/"))
        if m is not None and n is not None and m <= n: return ("quorum", m, n)
        return None
    if word.startswith("weighted:") and len(word) > len("weighted:"): return ("weighted", None, None)
    return None


def founders_of(by, obj):
    """The founders an infrastructure community's founding row seats: its signers that are among its `to` (a founding
    row seats the keys that signed it; a signer it does not name is seated in nothing, and is no founder). Its own word
    is checked against their number; every later count reads the founder seats at its own heads (P1, Q5)."""
    g = by.get(obj)
    if g is None: return 0
    return len(signers(g) if "founders_all_signers" in MUT else signers(g) & frozenset(g["to"]))   # MUTATION


def infrastructure_rule(word):
    """The word an infrastructure community's record may state (CC 3.2, "Live and stalled"): `quorum:M/N`, M an
    absolute count of founder voices, at least 2, and the strict majority of N (N // 2 + 1); N the cap on its active
    founders. The rule (kind, m, n), or None for any other word (`quorum:1/1`, `quorum:2/5`, `quorum:3/3`, `majority`:
    federation_community_consensus_protocol_violation, the kernel concludes nothing under it). M is never recomputed
    from the founders held, and a leaving never lowers it."""
    pr = protocol_rule(word)
    if pr is None or pr[0] != "quorum" or pr[1] < 2: return None
    if pr[1] != pr[2] // 2 + 1 and "infra_any_quorum" not in MUT: return None   # MUTATION: any quorum
    return pr


def stalled_recovery(r, P, past):
    """The one row an infrastructure room admits without its founders' count while stalled (CC 3.2): a widening whose
    only change is one added founder seat, for a key named by a row (`bundle`) counted at a strict majority over the
    holders of the bundle in force of the root the room stands under, whose `scope` names this room, signed by the
    named key. With no trust root read (ROOT), the kernel holds no bundle holders, so such a row is UNDECIDED: the
    reason `stalled_recovery_needs_bundle`
    (the seat rule concludes nothing for it), or None for a row of another shape. The checks for when the trust root's
    fold is in the kernel: the counted row names the bundle in force; its `scope` names this room; the key's identity
    type includes `user` and excludes `node`; the widening is signed by the named key; only while stalled; only one
    founder seat; nothing else changed."""
    by = {q["id"]: q for q in P}
    if r["kind"] != "offer" or r.get("bundle") is None or r.get("scope") != "founder": return None
    if kind_of(by, r.get("obj")) != "infrastructure" or len(r.get("to", ())) != 1 or r["to"][0] not in signers(r): return None
    rec = protocol_record(by, r["obj"])
    pr = infrastructure_rule(rec.get("consensus_protocol")) if rec is not None else None
    if pr is None: return None
    founders = members_at(P, past, r["obj"], r.get("head", ()), "founder") - count_left(P, past, r["obj"], "founder")
    return "stalled_recovery_needs_bundle" if len(founders) < pr[1] + 1 else None


def affiliation_removal(r, by):
    """A counted removal of a member of an affiliation (the acts row remove / member / affiliation:
    affiliation_member_action | cosigned_act)."""
    return r["kind"] == "unseat" and r.get("conf") == "group" and r.get("scope") in ("member", OFFICER) \
        and kind_of(by, r.get("obj")) == "affiliation"


# ---- the countersign of a one-seat affiliation's act against a member (CC 4.4.3.12; the Constitution's
# formal/affiliation/Affiliation.lean, `admitted` and `validCountersign`) -----------------------------------------
# the record member that names the body that conferred or oversees the affiliation (the Constitution's ruled name:
# optional, one group id, changed like any record member; absent, only the designated official countersigns)
OVERSEEN_BY = "overseen_by"
OFFICER = "officer"     # the canonical MemberRole of an affiliation's deciding seat (CC 4.4.3.12)


def authority_body(Q, obj):
    """The keys a group's own authority is counted over (one source of the body rule, for the seat rule's readers):
    an affiliation's officers (CC 4.4.3.12, the ruling on officers; MUTATION affiliation_body_members: its members);
    any other community's duty holders (CC 4.5.4). `Q` a Seats reading."""
    if kind_of(Q.S.by, obj) == "affiliation":
        return Q.holders("member" if "affiliation_body_members" in MUT else OFFICER, obj)
    return Q.holders("duty", obj)


def protocol_body(Q, obj):
    """The keys a group's declared protocol is counted over: an affiliation's officers, any other community's members."""
    if kind_of(Q.S.by, obj) == "affiliation" and "affiliation_body_members" not in MUT: return Q.holders(OFFICER, obj)
    return Q.holders("member", obj)


def record_value(by, obj, field):
    """The value a field of obj's record in force has over `by` (the concluded rows of a row's past): the newest
    versions of the record there (its counted changes, scope `record`; the founding row where there is none), each a
    whole record. None where they disagree, or where the record states none."""
    g = by.get(obj)
    if g is None or g["kind"] != "offer" or g.get("obj") != g["id"]: return None
    vs = [q for q in by.values() if q["kind"] == "offer" and q.get("conf") == "group" and q.get("obj") == obj
          and q.get("scope") == "record" and in_force_change(q, by)]
    if not vs or "official_at_founding" in MUT: return g.get(field)      # MUTATION: the founding record alone
    anc = {q["id"]: K.ancestors(by, q["id"]) for q in vs}
    newest = [q for q in vs if not any(q["id"] in anc[x["id"]] for x in vs)]
    vals = {q.get(field) for q in newest}
    return vals.pop() if len(vals) == 1 else None


def deciding_seats(P, past, obj, heads):
    """An affiliation's deciding seats at the heads: its officers (CC 4.4.3.12, the ruling on officers), the members
    whose seat carries the `officer` role there (the founding record's signers listed with it, and those appointed or
    promoted with it since, less demotions, lay-downs and leavings). A member with no role is subject to the body's
    power and no voice (a charter granting one is not read: a gap). MUTATION officer_from_founders: the founding
    record's seated signers, while members (the reading before the ruling)."""
    if "officer_from_founders" in MUT:
        g = {q["id"]: q for q in P}.get(obj)
        if g is None: return frozenset()
        return (signers(g) & frozenset(g["to"])) & members_at(P, past, obj, heads, "member")
    return members_at(P, past, obj, heads, OFFICER)


def affiliation_count(r, P, past):
    """Affiliation.lean `admitted` for a removal: the body's own signature (every voice a deciding seat, at least
    one), and where the body has one deciding seat, the act stands as a PROPOSAL (CC 4.5.5's reconsideration path):
    it concludes, and is in force only where a countersign names it (Seats); a body of two or more seats decides on
    two voices at least, the member removed not counted (CC 4.5.13; MUTATION two_voices_unread: on one)."""
    obj = r["obj"]
    seats = deciding_seats(P, past, obj, r.get("head", ()))
    vs = voices(r, P)
    off = frozenset(k for k in vs if officer_key(P, k, seats, obj))     # the officers' voices, by person
    if not off: return False
    if len(as_persons(seats, P, obj)) == 1:
        # the officer's voice, and any outside voice on the row an eligible countersigner (G15): its decision
        # (MUTATION outside_voice_taken: any outside voice taken)
        return "outside_voice_taken" in MUT or vs - off <= countersigners(r, P, past)
    if off != vs: return False
    targets = act_targets(r, {q["id"]: q for q in P})
    yes = persons_of(vs, seats, P, obj) - as_persons(targets, P, obj) - frozenset(rep_of(P, t) for t in targets)
    return len(yes) >= (1 if "two_voices_unread" in MUT else 2)


def officer_key(P, k, seats, obj):
    """Key k is one of the officers' keys over P, BY PERSON (ruled on CIRISConstitution#224, as every count): a key
    of the deciding seats, or another live key of an officer's person (its own device). The person is read in P, the
    act's own past, as every count reads it (the rival foundings are read at the row too): a verdict for a presented
    row is fixed by its past, so a binding concurrent with the act, or written after it, does not make an outside
    voice the officer's own (the unlinked-keys residual, stated once). MUTATION officers_by_key: the seats' keys
    alone."""
    if k in seats: return True
    if "officers_by_key" in MUT: return False
    op = as_persons(seats, P, obj)
    return rep_of(P, k) in op or rep_of(P, k, member=True) in op


def against_member(u, by):
    """u is one of the four acts against a member of an affiliation (CC 4.4.3.12): a removal, a quarantine, a slashing
    verdict, a takedown of the member's content (the table's affiliation rows, policy pin 8ec76cce)."""
    return affiliation_removal(u, by) or (family(u) in LONE_ACTS and kind_of(by, u.get("obj")) == "affiliation")


def regrown_fails(S, q, void=frozenset()):
    """The r81 B2 rule, read over the rows the reader holds: q, a lone holder's own conferral of a duty over a room
    (own_conferral), concurrent with growth of the room's body (a counted act of conf `group` over it, the acceptance
    completing one, or the countersign deciding one, neither in the other's past, none void), fails where re-counted
    over its own past with that growth and their pasts (the body at the newest counted changes the reader holds): its
    signer is no more the lone holder there (authority_gate). A holder's own concurrent lone conferrals are one batch,
    no growth against each other (own conferrals are no counted act of conf group)."""
    obj = q.get("obj")
    if not own_conferral(q, obj, S.by): return False
    counted = lambda x: x is not None and x.get("conf") == "group" and x.get("obj") == obj and CP.is_counted_act(x, obj)
    growth = [x for x in S.Cs if x["id"] not in void and x["id"] != q["id"] and x["id"] not in S.anc[q["id"]]
              and q["id"] not in S.anc[x["id"]]
              and (counted(x) or (x["kind"] == "accept" and counted(S.by.get(x.get("of")))))]
    if not growth: return False
    ids = set(S.anc[q["id"]])
    for x in growth:
        ids |= {x["id"]} | set(S.anc[x["id"]])
    T = [x for x in S.Cs if x["id"] in ids]
    return not authority_gate(q, T, {x["id"]: x for x in T})


def affiliation_act(u, by):
    """u is a counted act of an affiliation that needs the countersign while the body has ONE officer (the
    Constitution's ruling on item 8): every counted act but the admission of a member, so the four acts against a
    member, an officer's appointment or removal, a change of the record (the official, overseen_by, the protocol, the
    licence classes; a dissolution), a license seat's conferral or withdrawal. An officer's own lay-down is no counted
    act and needs none (MUTATION countersign_against_member_only: only the four acts against a member, the reading
    before the ruling)."""
    if u["kind"] in ("delegates_to", "licensure"):              # an onward trust edge it signs, or its own licence
        return kind_of(by, act_obj(u)) == "affiliation" and "edge_countersign_unread" not in MUT
    if kind_of(by, u.get("obj")) != "affiliation": return False
    if "countersign_against_member_only" in MUT: return against_member(u, by)
    if family(u) in LONE_ACTS: return True
    if u["kind"] not in ("offer", "unseat") or u.get("conf") != "group": return False
    return not (u["kind"] == "offer" and u.get("scope") == "member" and u.get("role") != OFFICER)   # an admission


def act_obj(u):
    """The affiliation a counted act is of: its `obj`; for an onward trust edge (`delegates_to`) its `on_behalf`; for
    a licence (`licensure`) its `authority`."""
    if u["kind"] == "delegates_to": return u.get("on_behalf")
    if u["kind"] == "licensure": return u.get("authority")
    return u.get("obj")


def act_heads(u, P, past):
    """The heads an act's deciding seats are read at: those it states, or (an edge, which states none) the newest
    counted changes over its affiliation in its own past P."""
    return tuple(u.get("head", ())) or newest_changes(P, past, act_obj(u), {q["id"]: q for q in P})


def needs_countersign(u, P, past):
    """u, a concluded counted act of a one-officer affiliation (affiliation_act), is a proposal until countersigned."""
    by = {q["id"]: q for q in P}
    if not affiliation_act(u, by): return False
    obj = act_obj(u)
    seats = deciding_seats(P, past, obj, act_heads(u, P, past))
    # officers are counted by person: two keys of one person in the roster are one officer (MUTATION officers_by_key)
    return len(seats if "officers_by_key" in MUT else as_persons(seats, P, obj)) == 1


def countersigned(S, r):
    """The one reading trust_rows takes of the countersign (an onward edge, or any counted act of an affiliation): row
    r of state S stands for S's reader where it needs no countersign (no one-officer affiliation's act at its own past)
    or is decided over S's concluded rows (decided_in: a countersign naming it, rule 4, overseer_cut)."""
    by = {q["id"]: q for q in S.rows if S.C.get(q["id"])}
    past = lambda a, b: a in K.ancestors(S.by, b)
    Pr = [q for q in by.values() if past(q["id"], r["id"])]
    return not needs_countersign(r, Pr, past) or decided_in(r, by, past)


def countersigners(u, Pu, past):
    """The eligible outside voices on act u's OWN row (the Constitution's G15: a countersign is the outside key's voice
    on the act, its own statement over the act's row, not a separate row naming it): u's signers outside its deciding
    seat that are the designated official of the record in force in u's own past Pu, or a review holder of the body
    the record's overseen_by names, at the newest counted changes over it there. The seat is read by person (officer_key)
    (MUTATIONS countersign_inside_seat, overseers_unread)."""
    byu = {q["id"]: q for q in Pu}
    obj = act_obj(u)
    seats = deciding_seats(Pu, past, obj, act_heads(u, Pu, past))
    # outside the seat by person: another key of the officer's own person is the officer (MUTATION countersign_inside_seat)
    outside = signers(u) if "countersign_inside_seat" in MUT else \
        frozenset(k for k in signers(u) if not officer_key(Pu, k, seats, obj))
    off = record_value(byu, obj, "official")
    body = record_value(byu, obj, OVERSEEN_BY)
    ov = overseers(Pu, past, body) if body is not None and "overseers_unread" not in MUT else frozenset()
    return frozenset(k for k in outside if k == off or k in ov)


def decided_in(u, by, past):
    """A proposal u (a one-officer affiliation's act) is decided over the rows `by` (a row's concluded past, or a
    reader's): an eligible outside voice is on u's own row (countersigners), and no end of that voice's overseer seat
    there lacks u in its past (overseer_cut). The decision and its countersign are one row, so a later withdrawal
    naming the act has both in its past: an act held on the officer's voice alone is decided by no other row."""
    Pu = [q for q in by.values() if past(q["id"], u["id"])]
    byu = {q["id"]: q for q in Pu}
    off = record_value(byu, act_obj(u), "official")
    body = record_value(byu, act_obj(u), OVERSEEN_BY)
    return any(k == off or not overseer_cut(u, by, past, body, k) for k in countersigners(u, Pu, past))


def in_force_change(q, by):
    """A change of a record read in a row's past (`by`): a one-officer affiliation's change is in force there only once
    decided there (its countersign in that past: a later row's own past decides whether it reads the change)."""
    if "countersign_unread" in MUT: return True
    past = lambda a, b: a in K.ancestors(by, b)
    Pq = [x for x in by.values() if past(x["id"], q["id"])]
    return not needs_countersign(q, Pq, past) or decided_in(q, by, past)


def overseer_cut(c, rows, past, body, k=None):
    """By the end rule, an end of countersigner k's `review` seat over the overseeing body (its withdrawal naming the
    scope, or an unseat of it) that does not have the countersigned act c in its past cuts k's voice on it: an
    ex-overseer countersigns nothing (MUTATION overseer_end_unread)."""
    if "overseer_end_unread" in MUT or body is None: return False
    k = c["signer"] if k is None else k
    return any((w["kind"] == "withdraw" and w["signer"] == k and w.get("scope") == "review"
                and (rows.get(w.get("target")) or {}).get("obj") == body or
                w["kind"] == "unseat" and k in w.get("to", ()) and w.get("scope") == "review" and w.get("obj") == body)
               and not past(c["id"], w["id"]) for w in rows.values())


def overseers(P, past, body):
    """The review holders of the overseeing body, at the newest counted changes over it in P (the act's own past)."""
    by = {q["id"]: q for q in P}
    if by.get(body) is None: return frozenset()
    return members_at(P, past, body, newest_changes(P, past, body, by), "review")


# the trust root this node reads (models/trust_root/root.py): (Root, reader), or None. With none, a stalled recovery is
# undecided; with one, it is judged (recovery_verdict)
ROOT = [None]


class root_view:
    """`with root_view(R, rd):` the seat rule judges a stalled recovery against root R as reader rd reads it."""
    def __init__(self, R, rd): self.v = (R, rd)
    def __enter__(self): ROOT.append(self.v)
    def __exit__(self, *a): ROOT.pop()


def root_seat_rule(r):
    """The seat a root grant gives (CC 3.2, cross-object rest 5): an offer of conf `root`, naming the grant (`bundle`),
    of the grant's duty (its scope), over the room the grant names, to and signed by the key the grant names. It
    stands while the grant resolves at the reader of the root view (root.grant_in_force: its voices a strict majority
    of the holders in force there, and the scope in force carrying its duty); with no root read it seats nothing.
    MUTATIONS root_seat_unchecked (no grant read), root_seat_any_duty (the duty not read)."""
    if "root_seat_unchecked" in MUT: return True
    view = ROOT[-1]
    if view is None: return False
    Rt, rd = view
    g = Rt.grants.get(r.get("bundle"))
    if g is None or not Rt.grant_in_force(r["bundle"], rd)[0]: return False
    if tuple(r.get("to", ())) != (g["to"],) or r["signer"] != g["to"] or g["scope"] != r.get("obj"): return False
    return g["duty"] == r.get("scope") or "root_seat_any_duty" in MUT


def recovery_verdict(r, P, past):
    """A stalled infrastructure room's recovery widening (CC 3.2), judged against the trust root this node reads:
    (True, None), or (False, reason). The six checks:
        1  the grant it names (`bundle`) resolves for this node (root.grant_in_force): it exists, counted at a strict
           majority of the live holders of the bundle it names under a charter carrying its duty, that bundle is in
           this node's lineage, and the scope in force here still carries the duty (MUTATION
           recovery_inforce_unread: any grant that exists as a row);
        2  the grant's `scope` names this room (MUTATION recovery_scope_unread);
        3  the key's identity type includes `user` and excludes `node` (MUTATION recovery_identity_unread);
        4  the widening is signed by the key the grant names (MUTATION recovery_signer_unread);
        5  only while stalled: fewer than M + 1 founders at its heads (MUTATION recovery_stalled_unread);
        6  one founder seat, and nothing else changed (MUTATION recovery_more_unread)."""
    view = ROOT[-1]
    if view is None: return (False, "stalled_recovery_needs_bundle")
    Rt, rd = view
    by = {q["id"]: q for q in P}
    if r["kind"] != "offer" or r.get("scope") != "founder" or kind_of(by, r.get("obj")) != "infrastructure":
        return (False, "not_a_recovery")
    rec = protocol_record(by, r["obj"])
    pr = infrastructure_rule(rec.get("consensus_protocol")) if rec is not None else None
    if pr is None: return (False, "not_a_recovery")
    if "recovery_more_unread" not in MUT and (len(r.get("to", ())) != 1 or r.get("consensus_protocol") is not None
                                               or r.get("cosigners")):
        return (False, "recovery_changes_more")
    founders = members_at(P, past, r["obj"], r.get("head", ()), "founder") - count_left(P, past, r["obj"], "founder")
    if len(founders) >= pr[1] + 1 and "recovery_stalled_unread" not in MUT: return (False, "not_stalled")
    gid = r.get("bundle")
    g = Rt.grants.get(gid)
    if g is None: return (False, "grant_unknown")
    if "recovery_inforce_unread" in MUT:
        if not Rt.grant_row(gid): return (False, "grant_count_short")
    else:
        ok, why = Rt.grant_in_force(gid, rd)
        if not ok: return (False, why)
    if g["scope"] != r["obj"] and "recovery_scope_unread" not in MUT: return (False, "grant_scope_not_this_room")
    if ("user" not in g["identity"] or "node" in g["identity"]) and "recovery_identity_unread" not in MUT:
        return (False, "grant_identity_not_user")
    if "recovery_signer_unread" not in MUT and (r["to"][0] != g["to"] or r["signer"] != g["to"]):
        return (False, "not_signed_by_named_key")
    return (True, None)


def is_amendment(q, obj):
    """A change of community obj's record that states its consensus_protocol: a counted offer of scope `record` over
    obj (the act record_change), carrying the new protocol."""
    return q["kind"] == "offer" and q.get("conf") == "group" and q.get("obj") == obj and q.get("scope") == "record" \
        and q.get("consensus_protocol") is not None


def protocol_record(by, obj):
    """The record row whose consensus_protocol is in force in a row's past (`by`: the concluded rows of that past, and
    the order among them read over those rows alone: a row not concluded carries nothing): the newest amendment of the
    record there (a counted change of the object, so a row that has it in its past has it in force), or the founding
    record. None where obj has no founding row, or where the newest amendments disagree (two concurrent changes naming
    different protocols: none is in force). A seat outlasts a change of protocol: no seat is judged again under the new
    one (CC 4.5.4)."""
    g = by.get(obj)
    if g is None or g["kind"] != "offer" or g.get("obj") != g["id"]: return None
    am = [q for q in by.values() if is_amendment(q, obj) and in_force_change(q, by)] if "amendment_unread" not in MUT else []
    if not am: return g
    if "any_amendment" in MUT: return am[0]                    # MUTATION: any change in the past, not the newest
    anc = {q["id"]: K.ancestors(by, q["id"]) for q in am}
    newest = [q for q in am if not any(q["id"] in anc[x["id"]] for x in am)]
    # the newest changes agree when they state the same protocol, with the same numbers (a weighted count's own)
    words = {(q["consensus_protocol"], q.get("need"), frozenset(tuple(p) for p in (q.get("weights") or ()))) for q in newest}
    if len(words) != 1 and "disagreeing_first" not in MUT: return None   # MUTATION: one of the disagreeing changes
    return min(newest, key=lambda q: q["id"])


def protocol_of(by, obj):
    """The room's declared protocol in force in a row's past: protocol_record's consensus_protocol (None where it is
    none, or where no record is in force)."""
    rec = protocol_record(by, obj)
    return None if rec is None else rec.get("consensus_protocol")


def regime_of(r, by):
    """The regime a counted row is counted under, once the binding reads it: the room's protocol in force in its past
    (protocol_of). Each act's own policy is fixed by the acts table, so it is no part of the room's regime: tips of an
    admission and a conferral fold, and tips on either side of a change of protocol do not. With the binding off, the
    row's stated `regime`."""
    if not BOUND or "regime_stated" in MUT: return r.get("regime")
    return protocol_of(by, r.get("obj"))


BOUND = True            # the seat rule reads the acts table (roster.py runs its instances with it off: Spec.bound)
REFUSED = object()      # policy_in_force: the row concludes nothing


class binding:
    """`with binding(flag):` the seat rule reads the acts table (True) or not (False) inside the block, as it was after."""
    def __init__(self, flag): self.flag = flag
    def __enter__(self):
        global BOUND
        self.saved, BOUND = BOUND, self.flag
    def __exit__(self, *a):
        global BOUND
        BOUND = self.saved


def community_rule(word, need=None, weights=None):
    """The protocol a community's record may declare (CC 3.3.4, closed by CC 4.5.13 and the Constitution's Q1, Q3): a
    word of the set (protocol_rule) under which no one voice admits or removes, and not founder_only (a family's, not a
    community's). None for any other: `quorum:1/{n}`, `founder_only`, a weighted record one of whose weights reaches
    its threshold (federation_community_consensus_protocol_violation)."""
    pr = protocol_rule(word)
    if pr is None: return None
    if pr[0] == "founder_only" and "founder_only_community" not in MUT: return None
    if "one_voice_community_protocol" in MUT: return pr                      # MUTATION: a one-voice protocol is one
    if pr[0] == "quorum" and pr[1] == 1: return None
    if pr[0] == "weighted":
        keys = [k for k, _ in (weights or ())]
        if len(keys) != len(set(keys)) and "weights_twice_at_change" not in MUT: return None   # a key weighed twice
        # a weight is a whole number: a negative one states no weights (the crate's u64 cannot express one)
        if any(w < 0 for _, w in (weights or ())) and "negative_weight" not in MUT: return None
        if need is not None and any(w >= need for _, w in (weights or ())): return None
    return pr


def _protocol_part(r, by, need, weights):
    """The room's protocol in force at r (a protocol row): {policy, need, weights} or REFUSED. See in_force."""
    obj = r.get("obj")
    rec = protocol_record(by, obj)
    if "record_by_founding" in MUT and r.get("scope") == "record": rec = by.get(obj)   # MUTATION
    if rec is None: return REFUSED
    w = rec.get("consensus_protocol")
    infra = kind_of(by, obj) == "infrastructure" and not ("infra_record_simple_majority" in MUT and r.get("scope") == "record")
    if infra:
        # CC 3.1.3.2 and 3.2 read through: the record's M founder voices (absolute, never lowered), over the `founder`
        # seats held at the row's heads; live while they number at least M + 1. Its record MUST be entrenched (no
        # weakening), and its founding word states N = the founders it seats and M their strict majority. A founder
        # seat is added only by a founders' amendment (a change of the record seating the key, below) or the stalled
        # recovery widening (undecided): a plain founder widening concludes nothing
        g = by[obj]
        pr = infrastructure_rule(w)
        if pr is None: return REFUSED
        if not g.get("consensus_protocol_entrenched") and "infra_unentrenched" not in MUT: return REFUSED
        if rec is g and pr[2] != founders_of(by, obj) and "infra_word_n_free" not in MUT: return REFUSED   # founding N
        if r["kind"] == "offer" and r.get("scope") == "founder" and "infra_founder_by_widening" not in MUT: return REFUSED
        if r.get("counted", "member") != "founder" and "infra_body_members" not in MUT and "protocol_body_free" not in MUT:
            return REFUSED
        out = dict(policy="P:quorum", need=pr[1], weights=None, infra_mn=(pr[1], pr[2]))
        if r["kind"] == "unseat": out["base_excludes_target"] = True   # the founder removed is not counted
        return out
    family = kind_of(by, obj) == "family"
    if family:
        # a family (CC 3.3.4, 3.1.3.2, 4.5.12.5): every protocol of the set, founder_only and quorum:1/n included, and no
        # floor of two voices; its record carries no duty map (F4: duty_holders_on_family), its founder roles apart
        if any(d != "founder" for d, _ in (by[obj].get("duty_holders") or ())): return REFUSED
        pr = protocol_rule(w) if "family_floor_two" not in MUT else community_rule(w, rec.get("need"), rec.get("weights"))
    else:
        pr = community_rule(w, rec.get("need"), rec.get("weights"))
    if pr is None: return REFUSED
    kind, m, _n = pr
    # the body: a family under founder_only counts its active founders (the `founder` role standing at the row's
    # heads: the founding roles and later conferred ones, less demotions and leavings); every other count its members
    body = "founder" if family and kind == "founder_only" else "member"
    # an affiliation's body for every counted act is its officers under its declared protocol (CC 4.4.3.12: its members
    # are subjects and no voice; a charter granting them one is not read). MUTATION affiliation_body_members
    if kind_of(by, obj) == "affiliation" and "affiliation_body_members" not in MUT: body = OFFICER
    if r.get("counted", "member") != body and "protocol_body_free" not in MUT: return REFUSED
    if family and kind == "founder_only":
        # each act takes one active founder; a removal (a demotion too) one other than the one it names
        out = dict(policy="P:founder_only", need=None, weights=None)
        if r["kind"] == "unseat": out["exclude_target"] = True
        if "family_founders_fixed" in MUT: out["founders_fixed"] = True
        return out
    # open:self_admit governs admissions alone (an offer of the member seat): the set states no removal under it, and
    # a removal concludes nothing (Q2: an explicit exception, not the `&` reading, until Eric answers whether an open
    # room may remove anyone); a change of the record is never counted as an admission
    if kind == "open:self_admit":
        if r["kind"] != "offer":
            if "self_admit_removal_counted" not in MUT: return REFUSED
        elif r.get("scope") != "member" and "record_change_as_admission" not in MUT: return REFUSED
    need, weights = None, None
    if "row_need" in MUT: need = r.get("need")                 # MUTATION: the row's need, not the record's number
    elif kind == "quorum": need = m
    elif kind == "weighted":
        need, weights = rec.get("need"), rec.get("weights")
        keys = [k for k, _ in (weights or ())]
        if len(keys) != len(set(keys)): return REFUSED          # a record weighing one key twice states no weights
        if any(w < 0 for _, w in (weights or ())) and "negative_weight" not in MUT: return REFUSED
    out = dict(policy="P:" + kind, need=need, weights=weights)
    # a removal under the room's protocol (community_remove: "the member being removed is not counted"; the sheet's
    # removal rules for quorum and weighted are the admission rule over the other members): the key it removes is
    # neither counted over nor a voice (unanimous reads its own rule, count_of)
    if r["kind"] == "unseat" and kind != "unanimous" and "removal_counts_target" not in MUT: out["base_excludes_target"] = True
    # in a community the floor is never fewer than two voices, so one voice never decides who is in a room, whatever
    # its size (CC 4.5.13): a counted removal takes two voices besides the member it removes (a family has no floor)
    if r["kind"] == "unseat" and not family and "removal_floor_unread" not in MUT:
        out["floor"] = REMOVAL_FLOOR
    # a family's removal naming only its own signer, on that signature alone, is no leaving (F3: the resignation is)
    if family and r["kind"] == "unseat" and "self_removal_as_leave" not in MUT: out["no_self_removal"] = True
    return out


def in_force(r, by):
    """What a counted row is counted under: {policy, need, weights} (a word of POLICY, the threshold a declared count
    reads, the weights a weighted count reads), {policy, all: [those]} for policies joined by `&` (every one met), or
    REFUSED.
    With the binding on (BOUND), the policy is the row's act's (act_of) in the acts table: a fixed act refuses a
    different stated policy and accepts its own or none; a row's choice is one of those listed, stated. A counted row
    over an object with a kind whose act has no row, or that states another policy, is REFUSED; so is a change of the
    record naming a word its room may not declare (community_rule, infrastructure_rule), and a row whose body
    (`counted`, `over`) is not its act's own (body_of). A protocol row (cosigned_act, community_remove,
    wa_adjudication) is counted under the room's protocol in force in the row's past (protocol_record), never one the
    row states, over the protocol's own body and with the record's numbers, never the row's `need`
    (_protocol_part). With the binding off, the row's own policy and need, a protocol row read the same way."""
    stated = r.get("policy")
    word, need, weights = stated, r.get("need"), r.get("weights")
    if BOUND and "binding_off" not in MUT:
        is_key = r.get("obj") is not None and r.get("obj") not in by
        a = act_of(r, by, is_key)
        if a is None:
            return REFUSED if kind_of(by, r.get("obj"), is_key) is not None else dict(policy=stated, need=need, weights=weights)
        rule = policy_for(*a)
        if rule is None: return REFUSED
        pols, choice = rule
        if choice == "fixed":
            if stated not in (None, pols[0]) and "stated_policy_free" not in MUT: return REFUSED
            word = pols[0]
        else:
            if stated not in pols and "stated_policy_free" not in MUT: return REFUSED
            word = stated
        # a stated regime is a consistency check: it must be the room's protocol in force in the row's past
        if r.get("regime") is not None and r.get("regime") != protocol_of(by, r.get("obj")) and "regime_unread" not in MUT:
            return REFUSED
        # a change of the record that states a protocol names one its room may declare, or concludes nothing (an
        # infrastructure community's: its founders' strict majority, checked by the count at the change's heads)
        if a[0] == "record_change" and r.get("consensus_protocol") is not None and "protocol_set_open" not in MUT:
            w = r["consensus_protocol"]
            ok = infrastructure_rule(w) if a[2] == "infrastructure" and "infra_record_simple_majority" not in MUT \
                else community_rule(w, r.get("need"), r.get("weights"))
            if ok is None: return REFUSED
        # `role: founder` is read on a family's admission of the member seat and on an infrastructure community's
        # founders' amendment, and nowhere else
        if r.get("role") is not None and not ((a[2] == "family" and r.get("scope") == "member" and r["role"] == "founder") or (
                a[2] == "infrastructure" and r.get("scope") == "record") or (
                a[2] == "affiliation" and r.get("scope") == "member" and r["role"] == OFFICER)) and "role_on_own_offer" not in MUT:
            return REFUSED
        # an entrenched record (`consensus_protocol_entrenched`): a change of its protocol, or of the flag itself,
        # concludes nothing (F5); every other amendment concludes under the protocol
        if a[0] == "record_change" and not entrenchment_allows(r, by): return REFUSED
        # the body an act counts is the act's own (body_of), over its own object: never one the row states. A
        # protocol row's is its protocol's (_protocol_part); a duty's conferral, withdrawal and recall are read by
        # their own gates (duty_gate, duty_over, act_of's body)
        if "body_from_row" not in MUT and K.rule(POLICY, word, ("unknown",))[0] != "protocol" \
                and a[0] not in ("duty_confer", "duty_withdraw", "recall"):
            # (`over`, another object: H2 in seat_rule refuses it for every count)
            if r.get("counted", "member") != body_of(a, by, r.get("obj")):
                return REFUSED
    parts = word.split("&") if isinstance(word, str) and "&" in word else [word]
    out, dropped = [], False
    for w in parts:
        if K.rule(POLICY, w, ("unknown",))[0] == "protocol" and "protocol_unread" not in MUT:
            # the reading of `&` (the Constitution's ruling): where the protocol in force states no rule for the act
            # (the sheet: protocol_states), the cosigned_act half is no condition, and the other policy governs alone,
            # with the community floor of voices
            if len(parts) > 1 and "unstated_cosigned_blocks" not in MUT:
                rec = protocol_record(by, r.get("obj"))
                # (a protocol its room may declare: one it may not, founder_only say, leaves no protocol in force)
                pr = community_rule(rec.get("consensus_protocol"), rec.get("need"), rec.get("weights")) \
                    if rec is not None else None
                act = "admit" if r["kind"] == "offer" and r.get("scope") in ROSTER_SEATS else \
                    "remove" if r["kind"] == "unseat" else "other"
                if pr is not None and kind_of(by, r.get("obj")) != "infrastructure" and not protocol_states(pr[0], act):
                    dropped = True
                    continue
            f = _protocol_part(r, by, need, weights)
        else:
            f = dict(policy=w, need=need, weights=weights)
        if f is not REFUSED: out.append(f)
        elif "record_change_either_policy" not in MUT: return REFUSED   # MUTATION: one joined policy is enough
    if not out: return REFUSED
    if dropped and "unstated_floor_unread" not in MUT:
        out = [dict(f, floor=COMMUNITY_FLOOR) for f in out]
    if len(out) == 1 and len(parts) == 1: return out[0]
    return dict(policy=word, all=out, any="record_change_either_policy" in MUT)


def entrenchment_allows(r, by):
    """Whether change r of the record is allowed by its entrenchment (F5, the one place it is read): on a record in
    force carrying `consensus_protocol_entrenched` true, a change stating another protocol, or one stating a protocol
    without the flag (a change of the flag), concludes nothing; a change that states no protocol (a rename, a role,
    metadata) is allowed. A record not entrenched allows every change."""
    if "entrenched_amendable" in MUT: return True
    rec = protocol_record(by, r.get("obj"))
    if rec is None or not rec.get("consensus_protocol_entrenched"): return True
    if kind_of(by, r.get("obj")) == "infrastructure":
        # an infrastructure record's entrenchment means no WEAKENING (CC 3.2): its basis stays `founders`, the flag stays,
        # and M is never lowered (the count checks M against the present one, with the founders it reads)
        if r.get("admission_quorum_basis", "founders") != "founders": return False
        return r.get("consensus_protocol") is None or r.get("consensus_protocol_entrenched") is True
    if "entrenched_whole_record" in MUT: return False             # MUTATION: every amendment refused
    if r.get("consensus_protocol") is None: return r.get("consensus_protocol_entrenched", True) is True
    # under `weighted`, the weights and threshold are the protocol: restating either is a change of it
    pr = protocol_rule(rec.get("consensus_protocol"))
    if pr is not None and pr[0] == "weighted" and "entrenched_weights_free" not in MUT and (
            r.get("need") != rec.get("need") or frozenset(map(tuple, r.get("weights") or ())) !=
            frozenset(map(tuple, rec.get("weights") or ()))):
        return False
    return r["consensus_protocol"] == rec.get("consensus_protocol") and r.get("consensus_protocol_entrenched") is True


def is_dissolve(q):
    """A dissolution of the group: a counted offer of scope `record` carrying `dissolved_at` (the act dissolve)."""
    return q["kind"] == "offer" and q.get("conf") == "group" and q.get("scope") == "record" and \
        q.get("dissolved_at") is not None


def dissolved_in(P, obj):
    """A concluded dissolution of obj is among P (a row's concluded past): the group's record is withdrawn, every seat
    over it ends, and no row over it concludes after (the text's refusal `group_dissolved`)."""
    return "dissolve_unread" not in MUT and any(is_dissolve(q) and q.get("obj") == obj for q in P)


def body_of(a, by, obj):
    """The body an act counts (N2: the act's own, never the row's `counted`): an infrastructure community's founders;
    the duty holders (`duty`) for the duty holders' acts (a duty's conferral and withdrawal, a detector seat's); an
    accord's holders; a self roster's own seat (its founding row's scope; `key` for a key object); the members for
    every other act of a community (an admission, a removal, the recall, the lift, the election, a change of the
    record)."""
    act, _sc, kind = a
    if kind == "affiliation": return "member" if "affiliation_body_members" in MUT else OFFICER   # its officers, every act
    if kind == "infrastructure": return "founder"
    if kind == "accord": return "holder"
    if kind == "family": return "member"
    if kind in ("self", "voice"): return by[obj]["scope"] if obj in by else "key"
    if act in ("duty_confer", "duty_withdraw", "seat_confer", "seat_withdraw"): return "duty"
    return "member"


def policy_in_force(r, by):
    """The policy a counted row is counted under (a word of POLICY), or REFUSED: in_force's policy."""
    f = in_force(r, by)
    return REFUSED if f is REFUSED else f["policy"]


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
# The count each protocol of the set is read as (in_force names it `P:{kind}`): the protocol rows of the table
# (`protocol` in their enact cell: cosigned_act, community_remove, wa_adjudication) are counted under the room's protocol
# in force, never one a row states. A quorum's m and a weighted count's threshold reach met()/count_of() as `need`.
PROTOCOLS = {"P:majority": ("strict", 1, 2), "P:unanimous": ("unanimous", 0, 0), "P:quorum": ("declared", 0, 0),
             "P:weighted": ("weighted", 0, 0), "P:open:self_admit": ("self_admit", 0, 0), "P:founder_only": ("one", 1, 1)}
POLICY.update(PROTOCOLS)
# a count a row may state under a law that binds no act (roster.py's instances, the head rules' binding-off cases):
# a strict majority. With the binding on no act takes it
POLICY["majority"] = ("strict", 1, 2)
# the cases' communities declare a strict majority on their founding records (the builders' default below)
DEFAULT_PROTOCOL = "majority"


def count_of(policy, is_offer, to, mem, v, need=None, weights=None, table=None, signed=None):
    """A count met by voices v (read over the voters) over the members mem, under policy: the crate's count_of. The
    protocols' own kinds (unanimous, open:self_admit, weighted) are read here; every other kind by met(). `signed`: every
    key that signed the row (open:self_admit reads the joiner's own signature, the joiner no member yet)."""
    kind = K.rule(table or POLICY, policy, ("unknown", 0, 0))[0]
    to = tuple(to)
    if kind == "self_admit":
        # the joiner's own signature is the group's side; a removal takes two voices besides the member it names
        if is_offer and len(to) == 1 and to[0] not in mem: return to[0] in (v if signed is None else signed)
        return len([k for k in v if k in mem and k not in to]) >= 2
    if kind in ("unanimous", "weighted"):
        # no key admits itself; under unanimous the member a removal names is no voice either
        yes = [k for k in v & mem if not (is_offer or kind == "unanimous") or k not in to]
        if kind == "weighted":
            w = dict(weights or ())                              # (key, weight) pairs; a key twice is refused before
            return need is not None and need > 0 and sum(w.get(k, 0) for k in yes) >= need
        others = len([k for k in mem if k not in to])
        if is_offer: return bool(mem) and len(yes) == others and all(k not in mem or k in v for k in to)
        return len(yes) == others and 2 * len(yes) > len(mem)
    # no key admits itself (CC 2.7.5), under every count: a key an offer seats is no voice of it, a member re-seated in
    # another role included (the crate's count_of reads the same; MUTATION self_voice_on_offer: it is one)
    if is_offer and "self_voice_on_offer" not in MUT: v = frozenset(k for k in v if k not in to)
    return met(policy, len(v), len(mem), need, table)              # the caller has read v over its voters

# CC 4.4.3.6 `open:self_admit`: an outsider's own admission to an open room. The group's side of a widening naming one
# new key is that key's own signature; a removal, or a widening naming a key already seated, takes two voices besides
# the member named. A head it writes narrows no count: a count naming it is read at the heads it names (count_heads)
POLICY["open:self_admit"] = ("self_admit", 0, 0)


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
    if obj == "@" and KINDS.get(scope) == "community":
        kw.setdefault("consensus_protocol", DEFAULT_PROTOCOL)   # a community's record declares its protocol (CC 3.3.4)
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
ROSTER_SEATS = ("member", "agent", "node")
# CC 4.5.13: an AI agent "acts under its own key and has no vote"; "a recall and an election count its persons alone".
# An agent's key is seated in a scope of its own: on the roster (content, wraps, audience), and in no count.
AGENT = "agent"
NODE = "node"           # a node's seat over an infrastructure community: no voice and in no base, as an agent's


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
        and signers(o) == frozenset(o["to"]) and "lone_founder_unread" not in MUT and o.get("group_kind") != "family"


def seat_scopes(o, k):
    """The scopes offer `o` seats key k in. One, the offer's own scope, for every offer but a founding row. A founding
    row seats by the signatures on it, with or without a map: a listed member who did not sign it is seated in nothing,
    whatever it accepts later (CC 3.1.3.2, `membership_founding_member_unsigned`); one who signed it in its own scope,
    and where it carries a `duty_holders` map, in each duty whose entry names it."""
    if o["obj"] != o["id"]:
        # an admission carrying `role: founder` (a family's one-row founder admission) seats the founder role too
        # (only on a counted row: an own or uncounted offer's role seats nothing, MUTATION role_on_own_offer)
        counted = o.get("conf") == "group" or "role_on_own_offer" in MUT
        if o.get("role") == "founder" and o["scope"] == "member" and counted and "role_unread" not in MUT:
            return ("member", "founder")
        # an affiliation's appointment carrying `role: officer` seats the officer role too (CC 4.4.3.12)
        if o.get("role") == OFFICER and o["scope"] == "member" and counted and "role_unread" not in MUT:
            return ("member", OFFICER)
        # a founders' amendment of an infrastructure record seats its keys as founders (CC 3.1.3.2)
        if o.get("role") == "founder" and o["scope"] == "record" and counted: return ("founder",)
        return (o["scope"],)
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


def seat_class(o, sc, holds=None):
    """The presence a seat sc of offer o is in its room, compared by what the scopes hold and not by name: AGENT for an
    agent's seat; `member` for a roster seat that is or holds membership (`member`, a founding scope holding it, as the
    founding `duty` seat does, `founder`); another roster seat's own name; None for a seat that is no presence (a duty,
    a detector)."""
    if sc == AGENT: return AGENT
    held = "member" in K.rule(HOLDS if holds is None else holds, sc, ())
    holds_member = covers(sc, "member") or (held and "class_by_name" not in MUT)   # MUTATION class_by_name: scopes compared by name
    if roster_seat(o, holds, sc): return "member" if holds_member else sc
    if holds_member and not is_duty(sc): return "member"
    return None


def consented(by, t, k, before):
    """Key k consented to offer t: it signed it, or an acceptance of it by k is in the withdrawal's own concluded past
    (`before`: one naming it, or a standing acceptance it names, of its scope and object). A withdrawal of an offer k
    never consented to is a decline: it ends that offer for k and nothing else, and is no end of a stay."""
    if k in signers(t): return True
    return any(a["kind"] == "accept" and a["signer"] == k and before(a) and (a.get("of") == t["id"] or (
        a.get("of") is None and a["id"] in t.get("names", ()) and a.get("scope") == t.get("scope")
        and a.get("obj") in (None, t.get("obj")))) for a in by.values())


def stay_ends(rows, by, before, holds=None):
    """The holders' own ends of a stay as a member, among `rows`: (withdrawal, key, community) for each withdrawal by a
    key of an offer of the roster's seat that names it, or of its own acceptance of one (the offer the acceptance
    names, or a standing acceptance's own scope and object). `before(a, w)`: row a is concluded and in w's past; the
    consent a withdrawal ends is read there only (a row written after it, or one that concludes nothing, is none)."""
    out = []
    for w in rows:
        bw = (lambda a, w=w: True) if "consent_any_row" in MUT else (lambda a, w=w: before(a, w))   # MUTATION consent_any_row
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
                # a standing acceptance withdrawn ends a stay only where an offer seating k named it (F5)
                if "decline_ends_stay" in MUT or any(m["kind"] == "offer" and m.get("obj") == t["obj"] and k in m["to"]
                                                     and m.get("scope") == t.get("scope") and t["id"] in m["names"]
                                                     and bw(m) for m in by.values()):
                    out.append((w, k, t["obj"]))
                continue
            else: continue
        if t is None or t["kind"] != "offer" or k not in t["to"]: continue
        # a key that never consented to the offer it withdraws declines it: no end of a stay (MUTATION decline_ends_stay)
        if "decline_ends_stay" not in MUT and not consented(by, t, k, bw): continue
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


def family_role_seat(by, o, sc):
    """A family's founder role, or an affiliation's officer role, conferred after founding (a promotion, or an admission
    carrying the role): a seat of scope `founder` over a family, or `officer` over an affiliation, that stands only on
    the member's seat, and ends with the member's stay (F1; CC 4.4.3.12)."""
    g = by.get(o.get("obj"))
    if g is None or o["id"] == o["obj"]: return False
    return (sc == "founder" and g.get("group_kind") == "family") or (sc == OFFICER and kind_of(by, o["obj"]) == "affiliation")


def duty_held(by, o, sc=None):
    """A duty seat proper: a seat the duty holders place over their community (duty_seat) whose scope makes its holder a
    duty holder, or a duty seat a founding row gives by its `duty_holders` map. The seat the membership rule reaches."""
    sc = o["scope"] if sc is None else sc
    if founding_duty(o, sc) or family_role_seat(by, o, sc): return True
    # over any community, a seat whose scope makes its holder a duty holder (who may confer it is duty_seat's)
    g = by.get(o["obj"])
    return community(by, o["obj"]) and g["id"] != o["id"] and o["scope"] not in ROSTER_SEATS and is_duty(sc, declared(by, o["obj"]))


def _lone(r, P, by):
    """CC 4.5.4 (iv): a duty conferred by one key stands only if that key is then the one duty holder over the object
    (a person: an agent holding a duty is no holder this count reads)."""
    if "lone_any" in MUT: return True
    Q = seats_of(P)
    held = Q.holders("duty", r["obj"]) - Q.holders(AGENT, r["obj"])
    # and a lone holder with an offer of a duty seat standing confers no other alone (MUTATION lone_offer_self_path:
    # the standing offer unread on this path)
    return held == frozenset({r["signer"]}) and ("lone_offer_self_path" in MUT or not lone_offer_stands(r, P, held))


def authority_gate(r, P, by):
    """THE ONE GATE (the r73 attack) on a single key's offer (conf `self` or `seat`, not a founding row) of a group's
    authority seat over a group: an act of its AUTHORITY BODY (authority_body), concluded only where its signer alone is
    that body, whether or not the founding row names holders. A duty seat: the lone duty holder (_lone, CC 4.5.4 (iv)).
    An officer seat or a license seat over a community record (a community, an infrastructure community, an
    affiliation): its signer alone is the body. So a locked or dissolved group (no body) signs nothing, and a founding
    signer's own offer does not revive it. Any other offer: True."""
    obj, sc = r.get("obj"), r.get("scope")
    # the one other path to a seat of a group's authority: a root grant's seat (conf `root`), only where the grant
    # resolves at the reader of the root view, its scope carrying the duty, for this room and this key (root_seat_rule)
    if r.get("conf") == "root" and "root_through_lone_gate" not in MUT: return root_seat_rule(r)   # MUTATION: none
    if duty_seat(by, r) or ("own_duty_ungated" not in MUT and community(by, obj) and is_duty(sc, declared(by, obj))):
        return _lone(r, P, by)
    if sc in (OFFICER, "license") and founding_row(by, obj) and \
            kind_of(by, obj) in ("community", "infrastructure", "affiliation") and "self_seat_ungated" not in MUT:
        return authority_body(seats_of(P), obj) == frozenset({r["signer"]})
    return True


def duty_count(r, P, yes, mem):
    """CC 4.5.4 (iv) over the duty holders at the head: conferral by a strict majority of them, withdrawal by a strict
    majority of the others (the holder concerned not counted); never fewer than two voices where there are two holders.
    A lone duty holder with an offer of a duty seat standing confers no other alone until that offer is accepted or
    withdrawn (lone_offer_stands)."""
    withdraw = DUTY_POLICY[r["policy"]] == "withdraw"
    base = mem - set(r["to"]) if withdraw and "count_target" not in MUT else mem
    y = yes & base
    lone = len(mem) < 2 and (withdraw or not lone_offer_stands(r, P, mem))
    return 2 * len(y) > len(base) and (len(y) >= 2 or lone or "no_duty_floor" in MUT)


def lone_offer_stands(r, P, mem):
    """The lone holder's own conferral of any duty over r's room still standing in r's past P: an offer of a duty
    scope, signed by a holder in mem, to a key not among them that has not consented to it (neither signed it nor
    accepted it there), not withdrawn there (by its conferrer or the key offered). An offer the key accepted, and then left, is consumed. It counts for the lone test only: the key offered holds nothing until it accepts. MUTATIONS
    lone_offer_unread (never read); lone_offer_same_scope (read for r's own scope only)."""
    if "lone_offer_unread" in MUT: return False
    by = {q["id"]: q for q in P}
    obj = r.get("obj")
    gone = {w["target"] for w in P if w["kind"] == "withdraw"}
    dec = declared(by, obj)
    # an offer the key once accepted is consumed, though the key then withdrew its acceptance (it left the seat): rule
    # (2) makes the conferrer's withdrawal of it no end of the ended seat, so it is no standing offer either (MUTATION
    # left_offer_stands: a withdrawn acceptance leaves the offer standing, and the lone holder can never confer again)
    accepted = {(a["of"], a["signer"]) for a in P if a["kind"] == "accept" and ("left_offer_stands" not in MUT or a["id"] not in gone)}
    unaccepted = lambda o: any(k not in mem and k not in signers(o) and (o["id"], k) not in accepted for k in o.get("to", ()))
    return any(o["kind"] == "offer" and o["id"] != r["id"] and o.get("obj") == obj and o["id"] != obj
               and o["signer"] in mem and is_duty(o.get("scope"), dec) and unaccepted(o)
               and o["id"] not in gone and ("lone_offer_same_scope" not in MUT or o.get("scope") == r.get("scope"))
               for o in P)


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
    # the signer holds `moderate` at the newest heads it names, read with the withdrawals in the row's own past (its
    # laying down of the seat there: members_at, MUTATION ends_at_heads_unread)
    return r["signer"] in members_at(P, past, r["obj"], heads, "moderate")


def lift_voices(r, P, past, by):
    """The voices of a re-seating row, or None where it is none: the signers of the objections it names to the lone
    removal it cites, less that removal's author."""
    rem = lifted(r, by)
    if r["kind"] == "offer" and rem is not None and family(rem) in LONE_ACTS and r.get("scope") == "act" \
            and rem.get("obj") == r.get("obj") and "lone_act_lift_unread" not in MUT:
        # the lift of a duty holder's lone act (quarantine, slash, takedown): the objections it names to that act
        v = frozenset(a["signer"] for a in P if a["kind"] == "answer" and a.get("of") == rem["id"]
                      and a.get("says") == "object" and a["id"] in r["names"])
        return v if "author_voice" in MUT else v - {rem["signer"]}
    if r["kind"] != "offer" or rem is None or rem["kind"] != "unseat" or not lone_removal(rem, P, past): return None
    # the same seat. The re-seating names the newest counted changes in its own past, as every roster row does (H4),
    # so it no longer names the removal's head; its base is the members at both heads (lift_base)
    if (rem["obj"], rem["scope"], tuple(rem["to"])) != (r["obj"], r["scope"], tuple(r["to"])):
        return None
    v = frozenset(a["signer"] for a in P if a["kind"] == "answer" and a.get("of") == rem["id"] and a.get("says") == "object"
                  and a["id"] in r["names"])
    return v if "author_voice" in MUT else v - {rem["signer"]}      # MUTATION author_voice: the author's objection counts


def room_count(yes, base):
    """The members' check of one member's act (the overturn, the lift, the count's receipt of a lone removal): more
    than half of the base, never fewer than two voices (MUTATION lift_no_floor: no floor). Whatever policy or need a
    row states, these counts are read by this rule alone."""
    return 2 * len(yes) > len(base) and (len(yes) >= 2 or "lift_no_floor" in MUT)


def lift_base(r, P, past, by):
    """(over, voters) of a lift: the persons seated at BOTH the removal's head and the lift's own heads (the newest
    counted changes in the lift's past, H4). A member removed, or that left, since the removal is out of it; one
    admitted since is out of it too, so a room that grows after a removal cannot pack its lift; a member removed and
    re-admitted is in it. The removal's author is taken apart by the caller. A lift restores: the key held its
    `agent` seat at the removal's head (lone_removal), so a moderator's "removal" of a key never seated, and a strict
    majority's objections, admit nothing past the room's own protocol. The members are persons: the key removed is an
    agent's, no voice and not counted over. MUTATIONS lift_base_lift_head (the base read at the lift's heads alone)
    and lift_base_removal_head (at the removal's head alone)."""
    rem_heads = lifted(r, by).get("head", ())
    if "lift_base_removal_head" in MUT: return counted_keys(P, past, r["obj"], rem_heads)
    mem, vot = counted_keys(P, past, r["obj"], r.get("head", ()))
    if "lift_base_lift_head" in MUT: return mem, vot
    mr, vr = counted_keys(P, past, r["obj"], rem_heads)
    return mem & mr, vot & vr


def lift_count(r, P, past, by):
    """The overturn's count (window.py, moderation_overturn) over the objections a re-seating row names: a strict
    majority of the members at the head, the removal's author apart and the key seated apart (each no voice, and
    not counted over); never fewer than two."""
    v = lift_voices(r, P, past, by)
    if v is None: return False
    # the base is the persons at BOTH heads (lift_base: the removal's and the lift's own); the author apart by person
    # (KP1). A lift restores: the key held its `agent` seat at the head the removal names (lone_removal), so a
    # moderator's "removal" of a key never seated, and a strict majority's objections, admit nothing past the room's
    # own protocol; the key removed is an agent's, no voice and not counted over
    mem, vot = lift_base(r, P, past, by)
    author = lifted(r, by)["signer"]
    # the author's own keys are the author (KP1): base and objections by person, the author apart by person
    # (MUTATION lift_author_device, author_voice: the author's keys voices of it; lift_over_all: the author counted over)
    odd = MUT & {"author_voice", "lift_over_all", "lift_author_device"}
    mem, yes = count_persons(P, r["obj"], mem, v, vot, apart=None if odd else author)
    if odd:
        a = {author, rep_of(P, author), rep_of(P, author, member=True)}
        if "lift_over_all" not in MUT: mem = mem - a
        if not MUT & {"author_voice", "lift_author_device"}: yes = yes - a
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
    """A seating by the election: a counted offer under the ranked count (`moderator_election`). A roster change: it
    names the newest counted changes over the room as its heads (H4) and sits on the reader's line by them; its count
    is its election's (C1 to C5: the electorate its id and vacancy fix), never read at its heads."""
    return o.get("kind") == "offer" and o.get("conf") == "group" and \
        K.rule(table or POLICY, o.get("policy"), ("unknown",))[0] == "ranked"


def _memo(tag, row, f, rows=()):
    # keyed by the row and the rows it is read over (one row object may stand in two sets of rows)
    key = (tag, id(row), frozenset(MUT), frozenset(id(x) for x in rows), _RENDS[-1])
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
        if w["id"] in _RENDS[-1]: continue          # a lay-down behind the reader's line is no vacancy end for it (H4)
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
    # the members at EVERY end, each end read alone: since the head rules several heads are folded (members_at), so
    # the persons common to the ends are taken here (MUTATION electorate_folded: the ends read as one fold)
    if "electorate_folded" in MUT: return counted_keys(P, past, obj, v)[0]
    # each end read over its own past only (C1, F1, F2: the electorate and the leavings come from the seating's named
    # set; a withdrawal in the seating's past that the seating does not name strikes nobody, though members_at reads
    # every withdrawal of a counting row's past for a roster count; MUTATION electorate_reads_past: over the seating's
    # whole past)
    at = (lambda e: P) if "electorate_reads_past" in MUT else (lambda e: [q for q in P if q["id"] == e or past(q["id"], e)])
    return frozenset.intersection(*[frozenset(counted_keys(at(e), past, obj, (e,))[0]) for e in v])


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
    if q["kind"] == "withdraw" and obj is not None and any(g == obj and k in elect for _, k, g in stay_ends([q], by, lambda a, w: a["id"] in by and past(a["id"], w["id"]))):
        return window
    # signed by a member of the electorate, or by a live key of one (counts over persons; ruled on #224)
    signer_in = q["signer"] in elect or ("persons_unread" not in MUT and person_for(q["signer"], elect, rows, by) is not None)
    if not signer_in and "set_any_signer" not in MUT: return False
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
            for _, k, g in stay_ends([w], by, lambda a, w: a["id"] in by and past(a["id"], w["id"])):
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
    left = {k for w in named if w["kind"] == "withdraw" for _, k, g in stay_ends([w], by, lambda a, w: a["id"] in by and past(a["id"], w["id"])) if g == obj} | \
        {k for u in named if u["kind"] == "unseat" and u.get("conf") == "group" and u.get("obj") == obj
         and u.get("scope") in ROSTER_SEATS for k in u["to"]}
    voters = el - (frozenset() if "leaver_voice" in MUT else left)
    # (2): a key whose two forked rows are both in the set is no ballot (the set alone decides: F1)
    voters = voters - forkers(Ek, named, past, obj, by, mine_ends)
    gone = {w["target"] for w in named if w["kind"] == "withdraw" and w["target"] in by
            and by[w["target"]]["kind"] == "ballot" and w["signer"] == by[w["target"]]["signer"]}
    declined = {d["signer"] for d in K.sel(P, kind="decline") if d["id"] in mine and d["signer"] in el}
    # one ballot per person (ruled on CIRISConstitution#224): a ballot counts for the voter its key speaks for; the
    # tally takes one ranking a voter, and a voter whose keys cast two says nothing (MUTATION persons_unread: the key)
    who = lambda b: b["signer"] if "persons_unread" in MUT else person_for(b["signer"], voters, P, by)
    ballots = [(who(b), b["ranking"]) for b in K.sel(P, kind="ballot")
               if b["id"] in mine and who(b) is not None and b["id"] not in gone
               and (set(b["ranking"]) <= voters or "ballot_nonmember_ranked" in MUT)
               and (len(b["ranking"]) <= ELECTION_RANKS or "ballot_ranks_unbounded" in MUT)]
    if not ballots: return False                    # (the ranked tally groups the ballots by voter: one says two, nothing)
    won = RANKED(ballots, sorted(voters - declined), 2, declared=False)[0]
    return won == r["to"][0] and (r["signer"] == won or "seating_any_signer" in MUT)


# ---- derived: the live seats ---------------------------------------------------------------------------
class Seats:
    def __init__(self, S, holds=HOLDS, confers=CONFERS, depth=DEPTH, by_arrival=False, own=None, checkpoint=False, drop=None,
                 roster=True, pairs=True):
        """`roster`: a reader's roster (the public reading): S'' is read over the rows it holds, as if a row had them all
        in its past, and a change void there neither adds nor removes members (the second review of 58b). The readings
        of a line inside the kernel (one tip, a head's past) pass False."""
        # the reader's roster is read over the rows as they conclude FOR THIS READER (reader_state)
        # and over the concurrent founders' amendments it holds (C2)
        if roster and (getattr(S, "_reader", None) != own or (pairs and not getattr(S, "_paired", False))) and (
                own is not None or (pairs and "wait_reader_unread" not in MUT and held_pairs(S))):
            S = reader_state(S, own)
        self.S, self.holds, self.confers, self.own = S, holds, confers, own
        # the reader's line is read before the cut: a counted act void for this reader cuts nothing for it (CC 2.7.8).
        # L: the acts behind the reader's line and those built on them, every row taken as counting; then the cut
        # without them, and the acts built on one the cut voids (MUTATION cut_before_line: the cut reads them too)
        # an election's seating sits on the line by the heads it names, as any roster change (the ruling of
        # 2026-11-26: no special placement)
        # (MUTATION line_after_cut: the first pass reads the cut, not every row as counting)
        first = CUT.Cut(S) if "line_after_cut" in MUT else CP.EVERY
        L = CP.void(S, first, own, checkpoint) if own is not None and "cut_before_line" not in MUT else frozenset()
        # the roster's own S'' void: the changes self-forked over the rows held cut nothing and seat nothing (MUTATION
        # void_cuts_in_roster: they do)
        if roster and "void_cuts_in_roster" not in MUT:
            L = L | roster_void(S)
        self.cut = C = CUT.Cut(S, without=L)
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
        # (MUTATION line_void_unlisted: the acts of the first pass not listed as void)
        self.stale = V = (frozenset() if "line_void_unlisted" in MUT else L) | CP.void(S, C, own, checkpoint)     # counted acts built on one that does not count, or behind the reader's line
        # the election's seatings that do not stand (C4, C5): read over the concluded rows, as the fold at tips is
        _RENDS.append(reader_ends(S, own) if roster else frozenset())     # the seat ends behind the reader's line
        try:
            self.beaten = beaten = election_beaten(Cs, past_, V) if any(is_election(o) for o in Cs) else frozenset()
        finally:
            _RENDS.pop()
        unseats = [u for u in K.sel(Cs, kind="unseat") if C.counts(u) and u["id"] not in V]

        def decided(u):
            """A one-seat affiliation's removal is a proposal: in force only where a countersign naming it counts for
            the reader, and no withdrawal of it by the acting seat that does not have that countersign in its past is
            held (the seat's withdrawal clears the proposal; MUTATION countersign_unread: no countersign asked)."""
            if "countersign_unread" in MUT: return True
            Pu = [q for q in Cs if q["id"] in S.anc[u["id"]]]
            if not needs_countersign(u, Pu, past_): return True
            return decided_in(u, {q["id"]: q for q in Cs}, past_)
        unseats = [u for u in unseats if decided(u)]
        # every other undecided proposal of a one-officer affiliation (an officer's appointment, a license seat, a change
        # of its record, a dissolution) is void for this reading as a row behind the line is: it seats, cuts and
        # declares nothing until a countersign naming it counts here
        undecided = frozenset(q["id"] for q in Cs if q["kind"] == "offer" and C.counts(q) and q["id"] not in V
                              and not decided(q))
        self.stale = V = V | undecided
        # r81 B2: a lone holder's own duty conferral concurrent with a counted act of the grown body is re-counted
        # against it (regrown_fails); one that fails seats nothing, and every row built on it is void with it
        regrown = frozenset(q["id"] for q in Cs if C.counts(q) and q["id"] not in V and regrown_fails(S, q, V)) \
            if "lone_regrowth_unread" not in MUT else frozenset()
        if regrown:
            self.stale = V = V | regrown | frozenset(q["id"] for q in Cs if S.anc[q["id"]] & regrown)
        # a moderator's lone removal is an act under its `moderate` standing, in force only while the end rule says so
        # (out_of_force). `drop`: the lone removals already judged out of force over the whole set, for a reading of
        # one line of it (the tips, the fold) or of the set with every removal taken as made (`frozenset()`)
        if drop is None:
            drop = out_of_force(S, unseats, holds, confers, depth, own, checkpoint) if "end_unread" not in MUT else frozenset()
        unseats = [u for u in unseats if u["id"] not in drop]
        # CC 2.7.7 rule 5: counted removals that remove each other's voices concurrently are contested, and neither is
        # in force (a voice concurrent with its own removal is no voice). Judged over the whole set, and carried with
        # the lone removals out of force into a reading of one line of it (the tips, the fold)
        # a dissolution is a cut over every seat of its group, so it is contested as a removal is (the ruling on FA6;
        # MUTATION dissolve_uncontested: a dissolution is read apart from rule 5)
        dis = [q for q in Cs if is_dissolve(q) and C.counts(q) and q["id"] not in V and q["id"] not in drop] \
            if "dissolve_uncontested" not in MUT else []
        contested = contested_out(S, unseats + dis)
        unseats = [u for u in unseats if u["id"] not in contested]
        self.dropped = drop | contested
        # a self roster's lone-path eviction that LANDED (its `landed` landing concluded: the window's outcome, as every
        # window) ends the target's seat as a counted eviction does: one ends reading (MUTATION landed_eviction_unread)
        if "landed_eviction_unread" not in MUT:
            unseats = unseats + landed_evictions(S, Cs, V)

        left = stay_ends(wd, S.by, lambda a, w: bool(S.C.get(a["id"])) and a["id"] in S.anc[w["id"]], holds)   # the holders' own ends of a stay as a member
        gone = {(k, g) for _, k, g in left}

        def same_class(w, o, sc):
            """End w (a key's own end of its stay) ends o's seat sc: the two seats are the same presence (seat_class)."""
            t = S.by.get(w.get("target"))
            t = S.by.get(t["of"]) if t is not None and t["kind"] == "accept" and t.get("of") is not None else t
            es = end_scope(S.by, w)
            return es is not None and seat_class(t or o, es, holds) == seat_class(o, sc, holds) is not None

        def resigned(o, k, sc):
            """A seat whose offer is in the past of its holder's own end of its stay is ended by it: a duty seat (the end
            of the stay as a member ends it), and every seat of the key in the roster scope the end ends, whatever row
            seated it (an end is of the key's stay in that scope, not of a row; as a counted removal's cut reaches
            every offer on the slot in its past)."""
            duty = duty_held(S.by, o, sc) and not ("duty_revives" in MUT or "resign_keeps_duty" in MUT)
            stay = "stay_one_row" not in MUT                  # MUTATION stay_one_row: a resignation ends the row it names only
            if not duty and not stay: return False
            return any((k2 == k or ("resigned_any_key" in MUT and not duty)) and g == o["obj"]
                       and ((pos[o["id"]] < pos[w["id"]]) if by_arrival else (o["id"] in S.anc[w["id"]]))
                       and (duty or same_class(w, o, sc)) for w, k2, g in left)

        def unseated(o, k, sc):
            for u in unseats:
                # a removal from the roster ends the removed member's duty seats too, "since a non-member holds no duty" (CC 4.5.4)
                held = ("seat", k, sc, o["obj"]) in u["cuts"] or (
                    "member_cut_only" not in MUT and (is_duty(sc) or duty_seat(S.by, o) or founding_duty(o, sc)
                                                       or family_role_seat(S.by, o, sc))
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
            if "own_end_unread" in MUT or seat_class(o, o["scope"], holds) is None: return False   # MUTATION: the key's own end voids nothing
            # a consent that does not have the end in its past: concurrent with it, or before it (a standing acceptance
            # given earlier is a consent like any other; F4). MUTATION earlier_consent_kept: only a concurrent one is void
            before = lambda w: "earlier_consent_kept" not in MUT and row["id"] in S.anc[w["id"]]
            return any((k2 == k or "own_void_any_key" in MUT) and g == o["obj"] and ("own_end_any_seat" in MUT or same_class(w, o, o["scope"]))
                       and (S.concurrent(w["id"], row["id"]) or before(w)) for w, k2, g in left)

        def accepted(o, k):
            if k in signers(o): return not own_void(o, o, k)
            # a node's seat over an infrastructure community stands on the founders' count alone (a node has no agency):
            # by its scope and the object's kind; every other seat needs the seated key's own acceptance
            if o["scope"] == NODE and o.get("conf") == "group" and "node_consent_asked" not in MUT \
                    and kind_of(S.by, o["obj"]) == "infrastructure":
                return True
            if o.get("consent") == "one" and "consent_one_waives" in MUT: return o["conf"] != "seat"   # MUTATION
            for a in K.sel(Cs, kind="accept", signer=k):
                paired = (a["of"] == o["id"]) or (a["of"] is None and a["id"] in o["names"] and a["scope"] == o["scope"]
                                                 and a["obj"] in (None, o["obj"]))
                if paired and not ended(a) and C.counts(a) and not own_void(a, o, k): return True
            return False

        # a concluded dissolution of a group ends every seat over it (it reads as the withdrawal of the group's record)
        gone = frozenset(q["obj"] for q in Cs if is_dissolve(q) and C.counts(q) and q["id"] not in self.dropped
                         and q["id"] not in V) \
            if "dissolve_leaves_seats" not in MUT else frozenset()
        # a root grant's seat is re-read at the reader: held only while its grant resolves in the reader's root view
        # now, whatever it concluded under (MUTATION root_seat_stored)
        base = [(o, k, sc) for o in K.sel(Cs, kind="offer") if C.counts(o) and o["id"] not in V and o["obj"] not in gone
                and o["id"] not in beaten and (o.get("conf") != "root" or "root_seat_stored" in MUT or root_seat_rule(o))
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
                elif o["conf"] == "root": out.add((o["id"], k, sc, 0, ("root", o.get("bundle"))))   # a root grant's seat
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
            # an agent's key holds a duty "by its own statement and its owner's signature" (CC 4.5.4, an agent's key):
            # the one live owner of the agent's key, by an owner-binding in the conferral's past, signed it; the
            # duty seat stands while that binding does (an end of the binding stops the seat, which has it in its
            # past; two owners are none). MUTATIONS agent_duty_owner_unread, agent_owner_end_unread
            # an agent is recognised by its agent seat (over any room) or its agent registration, whatever scope it was
            # admitted under (as ruled for KP5; MUTATION agent_by_seat_only: only an agent seat in that room)
            agent_keys_ = {k for oid, k, sc, _, _ in self.live if sc == AGENT} | registered_agents(Cs)
            agents = {(S.by[oid]["obj"], k) for oid, k, sc, _, _ in self.live
                      if (sc == AGENT if "agent_by_seat_only" in MUT else k in agent_keys_)}
            owners = {}
            for oid, k2, sc2, _, _ in self.live:
                if sc2 == "owner": owners.setdefault(S.by[oid]["obj"], set()).add((k2, oid))
            # the owner's signature on the seating, carried either way (the Constitution's answer): the owner cosigns
            # the conferral row, or the owner cosigns the agent's own acceptance of it (that acceptance names the
            # conferral); the binding in the signed row's past. A row that only cites the binding is no signature
            # (MUTATION owner_acceptance_unread: only the conferral carries it)
            carriers = lambda o, k: [o] + ([] if "owner_acceptance_unread" in MUT else [
                a for a in Cs if a["kind"] == "accept" and a["signer"] == k and a.get("of") == o["id"]])
            # the duty is tied to the binding: the binding is in the CONFERRAL's own past (a new binding revives no old
            # conferral, and the end of the one it stands on ends it for good), and the binding's owner signed the
            # seating, on the conferral or on the agent's acceptance (MUTATION binding_on_carrier: any carrier's past)
            tied = lambda o, row, b: b in S.anc[(row if "binding_on_carrier" in MUT else o)["id"]]
            bound = lambda o, k: "agent_duty_owner_unread" in MUT or (lambda ws: len({w for w, _ in ws}) == 1 and any(
                w in signers(row) and tied(o, row, b) for w, b in ws for row in carriers(o, k)))(
                owners.get(k, set()) if "agent_owner_end_unread" not in MUT else owner_bindings(S, k, o))
            # MUTATION resign_keeps_duty: a key that ended its own stay still reads as a member for its duty seats
            keep = [(o, k, sc) for o, k, sc in base if not duty_held(S.by, o, sc) or (
                ((o["obj"], k) in mem or ("resign_keeps_duty" in MUT and (k, o["obj"]) in gone))
                and ((o["obj"], k) not in agents or bound(o, k)))]
            if len(keep) == len(base): break
            base[:] = keep
            self.live = K.fix(step, frozenset(), depth + 1)
        # an affiliation with no officer is dissolved at that point (CC 4.4.3.12): every seat over it ends (MUTATION
        # no_officer_locks: it locks, its members kept)
        if "no_officer_locks" not in MUT:
            objs = {S.by[oid]["obj"] for oid, _, _, _, _ in self.live}
            with_officer = {S.by[oid]["obj"] for oid, _, sc, _, _ in self.live if sc == OFFICER}
            ended = {o for o in objs if o not in with_officer and kind_of(S.by, o) == "affiliation"}
            if ended: self.live = frozenset(x for x in self.live if S.by[x[0]]["obj"] not in ended)
        self.recs = [{"id": "%s/%s/%s" % (oid, k, sc), "offer": oid, "k": k, "scope": sc, "obj": S.by[oid]["obj"],
                      "depth": d, "root": root} for oid, k, sc, d, root in self.live]
        # a self roster's lone-path addition that LANDED seats its key, as a counted addition does, and the same ends
        # reading ends it (a later counted or landed eviction, with the landing in its past) (MUTATION
        # landed_add_unread)
        if "landed_add_unread" not in MUT:
            for L, k, sc, obj in landed_adds(S, Cs, V):
                if unseated({"id": L["id"], "obj": obj, "scope": sc}, k, sc): continue
                self.recs.append({"id": "%s/%s/%s" % (L["id"], k, sc), "offer": L["id"], "k": k, "scope": sc, "obj": obj,
                                  "depth": 0, "root": ("group", obj), "landed": True})

    def may_confer(self, up, o):
        """May the holder of the seat offered by `up` confer the seat `o` offers? A chain from a root grant (its top seat
        a `root` seat naming the grant, `bundle`) passes on only where the charter in force at the reader carries
        sub_delegation for the grant's duty (Root.sub_delegation through the root view; with no root read the gate is
        closed), every hop bearing a scope the one above covers; the row's own `sub` mark is not read for it (MUTATION
        root_gate_unread: the row's mark read as for any chain)."""
        top, seen = up, set()
        while top.get("conf") == "seat" and top.get("under") in self.S.by and top["id"] not in seen:
            seen.add(top["id"])
            top = self.S.by[top["under"]]
        if top.get("conf") == "root" and top.get("bundle") is not None and "root_gate_unread" not in MUT:
            view = ROOT[-1]
            if view is None: return False
            return bool(view[0].sub_delegation(top["bundle"], view[1])) and covers(up["scope"], o["scope"]) \
                and o["obj"] == up["obj"]
        if up.get("sub") and covers(up["scope"], o["scope"]) and o["obj"] == up["obj"]:
            return True                                            # the grant carried sub-delegation: the same or narrower
        scopes, over = K.rule(self.confers, up["scope"], ((), "same"))
        return any(covers(s, o["scope"]) for s in scopes) and o["obj"] == (up["obj"] if over == "same" else o["signer"])

    def _has(self, rec, s):
        if s == "duty" and is_duty(rec["scope"], declared(self.S.by, rec["obj"])): return True   # a holder of any one duty is a duty holder
        return covers(rec["scope"], s) or s in K.rule(self.holds, rec["scope"], ())

    def _member(self, rec):
        """A duty seat follows the folded roster: with several tips, its holder is among the members the fold seats."""
        if rec.get("landed") or "duty_no_member" in MUT or "duty_fold_unread" in MUT \
                or not duty_held(self.S.by, self.S.by[rec["offer"]], rec["scope"]): return True
        fold = self.tips_fold("member", rec["obj"])
        return fold is None or rec["k"] in fold or rec["k"] in (self.tips_fold(AGENT, rec["obj"]) or ())

    def stands(self, k, s, o, root=None):
        if not any(self._has(r, s) and (root is None or r["root"] == root) and self._member(r) for r in K.sel(self.recs, k=k, obj=o)): return False
        fold = self.tips_fold(s, o)                             # with several tips, the fold of their changes
        return fold is None or k in fold

    def dissolved(self, o):
        """Group o is dissolved: a concluded dissolution of it is held, or, with no signer, every member it seated has
        an end of their seat (its roster empty, folded at tips, and its founding row held): no row over it concludes."""
        if any(is_dissolve(q) and q.get("obj") == o and q["id"] not in self.dropped and q["id"] not in self.stale
               for q in self.S.Cs): return True
        # an affiliation with no officer is dissolved at that point (CC 4.4.3.12): not locked, and no election
        # (MUTATION no_officer_locks)
        if kind_of(self.S.by, o) == "affiliation" and "no_officer_locks" not in MUT and not self.holders(OFFICER, o):
            return True
        return founding_row(self.S.by, o) and not self.roster(o) and any(
            g == o for _, _, g in stay_ends(self.S.Cs, self.S.by,
                                          lambda a, w: bool(self.S.C.get(a["id"])) and a["id"] in self.S.anc[w["id"]]))

    def roster(self, o):
        """The room's whole roster over o: its members, its agents (CC 4.5.13) and its nodes (an infrastructure community). Content, wraps and audience read it;
        no count does (a count reads `member`, or the scope it names, less the agents)."""
        return self.holders("member", o) | self.holders(AGENT, o) | self.holders(NODE, o)

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
            sub = self._tip_rows(t, o)                                                          # one tip: no further recursion
            Q = Seats(CK.State(sub, {q["id"]: True for q in sub}), self.holds, self.confers, drop=self.dropped, roster=False)
            m = frozenset(r["k"] for r in K.sel(Q.recs, obj=o) if Q._has(r, s))
            out = m if out is None else out & m
        return out

    def _tip_rows(self, t, o):
        """A tip's line: the concluded rows in its past, with the acceptances held that complete an offer there (a seat
        is two consents, (a): an acceptance concluded after the tip completes the seat its offer places at the tip;
        MUTATION fold_acceptance_unread)."""
        S = self.S
        sub = [q for q in S.Cs if q["id"] == t["id"] or q["id"] in S.anc[t["id"]]]
        if "fold_acceptance_unread" in MUT: return sub
        ids = {q["id"] for q in sub}
        return sub + [S.by[a] for a in completing(ids, S.Cs, S.by, o, lambda a, b: a in S.anc.get(b, ()))]

    def _at(self, rows):
        """The seats read over a sub-set of the concluded rows (one line: no further recursion into tips)."""
        return Seats(CK.State(rows, {q["id"]: True for q in rows}), self.holds, self.confers, drop=self.dropped, roster=False)

    def tips_fold(self, s, o):
        """KERNEL.md section 7, the fold at tips (models/roster_fork/fold.py): with several tips, the keys holding
        `s` over `o` when every tip's changes are folded. None with one tip or none.
            common   a key every tip seats is in;
            out      a key some tip's line removed is out, unless a later addition of it has that removal in its
                     past. So a key one tip admits and another removes is out;
            in       a key some tip adds is in where the counted offer that adds it meets its count on the voices
                     of keys the fold seats, over the members at its heads that the fold seats: a least fixed
                     point from the common keys;
            wait     tips that differ in protocol or policy (regime_of: the protocol in force in a tip's past and its
                     policy in force, once the binding reads them; with the binding off, a row's stated `regime`)
                     do not fold: the answer is then the common keys, as tips_common gives."""
        tp = self.tips(o)
        if len(tp) <= 1: return None
        if "fold_off" in MUT: return self.tips_common(s, o)
        S = self.S
        memo = self.__dict__.setdefault("_fold_memo", {})
        if (s, o) in memo: return memo[(s, o)]
        lines = []
        for t in tp:
            sub = self._tip_rows(t, o)
            Q = self._at(sub)
            seated = {}                                         # key -> the offers that seat it at this tip
            for r in K.sel(Q.recs, obj=o):
                if Q._has(r, s): seated.setdefault(r["k"], set()).add(r["offer"])
            lines.append((t, sub, {q["id"] for q in sub}, seated))
        common = frozenset.intersection(*[frozenset(sd) for _, _, _, sd in lines])
        union = frozenset.union(*[frozenset(sd) for _, _, _, sd in lines])
        # a tip that is itself a change of the record's protocol is under its new protocol (MUTATION
        # regime_before_change: read in its past, so tips on either side of the change fold)
        own = lambda t: "regime_before_change" not in MUT and t.get("scope") == "record" and t.get("consensus_protocol")
        # a tip that changes the record's founder set (a founder's seating) is a regime of its own too: tips on either
        # side of it wait at their common members (MUTATION regime_protocol_only: only the protocol splits regimes)
        # (a founders' amendment of an infrastructure record, scope `record` with role founder, is such a seating too)
        founders = lambda t: "regime_protocol_only" not in MUT and t["kind"] in ("offer", "unseat") and (
            t.get("scope") == "founder" or (t.get("scope") == "record" and t.get("role") == "founder" and t.get("to")))
        regime = lambda t, sub: (regime_of(t, {q["id"]: q for q in sub if q["id"] != t["id"] or own(t)}),
                                 t["id"] if founders(t) else None)
        if len({regime(t, sub) for t, sub, _, _ in lines}) > 1 \
                and "regime_folds" not in MUT:
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
                f = in_force(r, {q["id"]: q for q in P})
                if f is REFUSED: return False
                if "all" in f:                                       # joined policies: a record change, no seat
                    continue
                r = dict(r, **f)                                     # the count reads the policy in force
                over, counted = r["obj"], r.get("counted", "member")          # H2: no `over`
                if (over, counted) == (o, s): ok = seated if "one_step" not in MUT else (union - out_keys)
                else: ok = self.tips_fold(counted, over)                 # another scope's own fold; None: one tip there
                mem = counted_keys(P, past, over, r.get("head", ()), counted)[0] - count_left(P, past, over, counted)
                if ok is not None: mem = mem & ok
                key_mem = mem
                mem, yes = count_persons(P, over, key_mem, voices(r, P))
                if is_election(r) and "fold_ranked_counted" not in MUT:
                    continue                    # an election's seating is read by C1 to C5 alone (beaten, the seat rule)
                if r.get("policy") in DUTY_POLICY:
                    if not duty_count(r, P, yes, mem): return False
                elif (lambda a: a[0] == "lift" if a is not None else K.rule(POLICY, r.get("policy"), ("unknown",))[0] == "lift")(
                        act_of(r, {q["id"]: q for q in P}, r.get("obj") not in {q["id"] for q in P}) if BOUND else None):
                    # a re-seating (its act the lift): its voices are the objections it names, over the members the fold seats
                    v = lift_voices(r, P, past, {q["id"]: q for q in P}) or frozenset()
                    # its objections and the members by person over the base at both heads (lift_base), the author
                    # apart by person (KP-A; MUTATION fold_lift_by_key: the objections and the author read by key over
                    # the persons; fold_author_by_key: the author taken out by key before the base is read by person)
                    author = lifted(r, S.by)["signer"] if v else None
                    if v: key_mem = key_mem & lift_base(r, P, past, {q["id"]: q for q in P})[0]
                    if "fold_lift_by_key" in MUT:
                        yes = v & mem
                        if v: mem = mem - {author}
                    elif "fold_author_by_key" in MUT:
                        mem, yes = count_persons(P, over, key_mem - ({author} if v else set()), v)
                    else:
                        mem, yes = count_persons(P, over, key_mem, v, apart=author)
                    if not room_count(yes, mem): return False
                elif not count_of(r.get("policy"), True, r.get("to", ()), mem, yes, r.get("need"), r.get("weights"),
                                  signed=voices(r, P)):
                    return False
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
            sub = self._tip_rows(t, o)
            Q = self._at(sub)
            sets.append(frozenset(r["k"] for r in K.sel(Q.recs, obj=o) if Q._has(r, s)))
        return frozenset.union(*sets) - frozenset.intersection(*sets) - (self.tips_fold(s, o) or frozenset())

    def one(self, s, o):
        """The single holder, where the seat is single-valued (an owner): two live holders is none."""
        return K.group([r for r in K.sel(self.recs, obj=o) if self._has(r, s)], None, "one", "k")

    def owner(self, node):
        """THE ONE OWNER READING (CC 3.2), for every caller (consent, the node arm, audience; nodes_of is its inverse):
        the one holder of the `owner` seat over key `node` (one(): two live owners is none), after the re-binding rule
        of standing.answers: a concluded owner offer over the node that has an earlier binding's offer in its past
        re-binds it and ends it (a stint, not a rival), whether or not the new owner has accepted yet. Read over the
        rows the caller gives (a reading row's past). MUTATION rebinding_unread: one() alone."""
        recs = [r for r in K.sel(self.recs, obj=node) if self._has(r, "owner")]
        if "rebinding_unread" not in MUT:
            S = self.S
            rebinds = [q["id"] for q in S.Cs if q["kind"] == "offer" and q.get("scope") == "owner" and q.get("obj") == node]
            recs = [r for r in recs if not any(q != r["offer"] and r["offer"] in S.anc[q] for q in rebinds)]
        return K.group(recs, None, "one", "k")

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
    stay = {w["id"] for w, k, g in stay_ends(K.sel(S.Cs, kind="withdraw"), by,
                                             lambda a, w: bool(S.C.get(a["id"])) and a["id"] in S.anc[w["id"]]) if k == M and g == obj}
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
    if "count_receipt_unchecked" in MUT: yes = persons_of(voices(q, P), vot, P, over)
    # the room less the remover, in the base as in the voices (R5: one rule for a count that judges one member's act,
    # as the overturn and the lift; MUTATION remover_counted_over)
    if "count_receipt_unchecked" in MUT: mem = as_persons(mem, P, over)
    elif "remover_counted_over" in MUT:
        mem, yes = as_persons(mem, P, over), count_persons(P, over, mem, voices(q, P), vot, apart=x["signer"])[1]
    else:
        # the room less the remover, by person, in the base as in the voices (KP-C)
        mem, yes = count_persons(P, over, mem, voices(q, P), vot, apart=x["signer"])
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


def removal_in_force(S, x, unseats, now, not_ends=frozenset(), lone_ids=frozenset(), scope="moderate"):
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
    # the seats at each head x names, with the acceptances in x's own past that complete an offer there (a seat is
    # two consents: the ruling of 2026-11-26 on acceptances, (a))
    Px = [q for q in S.Cs if q["id"] in S.anc.get(x["id"], ())]
    for h in x.get("head", ()):
        sub = [q for q in S.Cs if q["id"] == h or q["id"] in S.anc.get(h, ())]
        ids = frozenset(q["id"] for q in sub)
        # and the withdrawals of x's past, as members_at reads them (MUTATION ends_at_heads_unread)
        ends = [] if "ends_at_heads_unread" in MUT else [w for w in Px if w["kind"] == "withdraw" and w["id"] not in ids]
        Q = seats_of(sub + ends + [S.by[a] for a in completing(ids, Px, S.by, obj, lambda a, b: a in S.anc.get(b, ()))])
        standing |= {(r["offer"], r["scope"]) for r in Q.recs if r["k"] == M and r["obj"] == obj and Q._has(r, scope)}
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
    # and an end that the remover's own acceptance in x's past has in its past did not end the seat that acceptance
    # takes up again (MUTATION reaccept_unread)
    again = lambda E, sc: "reaccept_unread" not in MUT and any(
        a["kind"] == "accept" and a["signer"] == M and E["id"] in S.anc.get(a["id"], ()) and any(a.get("of") == o for o, _ in sc)
        for a in Px)
    found = [(E, sc) for E, sc in standing_ends(S, x, standing, unseats, not_ends)
             if not all(E["id"] == h or E["id"] in S.anc.get(h, ()) for h in x.get("head", ())) and not again(E, sc)]
    ended = frozenset().union(*(sc for _, sc in found)) if found else frozenset()
    live = {(r["offer"], r["scope"]) for r in now.recs if r["k"] == M and r["obj"] == obj}
    if now.stands(M, scope, obj) and ("reseat_revives" in MUT or any(s in live and s not in ended for s in standing)):
        return True                                             # MUTATION reseat_revives: any standing now keeps it
    ends = [E for E, _ in found]
    if not ends: return kept(None)
    for E in ends:
        if E["id"] in S.anc[x["id"]] or later(S, x.get("head", ()), head_of_end(S, E, obj)) or not kept(E):
            return False
    return True


# ---- the duty holders' lone acts against a key or content (CC 4.5.5; CC 3.1.9.2; CC 4.4.3.12) ------------------------
# The act each row kind is, and the duty that authorises it: a quarantine marker (`quarantine:{state}`, of a KEY: in a
# private room a room key) and a slashing verdict (`slashing:{outcome}`, about a KEY) under `slash`; a takedown
# notice (of a CONTENT row) under `takedown`. There is no quarantine duty.
# The row families (the Constitution's registered names): `quarantine:{state}`, `slashing:{outcome}`,
# `takedown_notice:{basis}`, `reconsideration:{grounds}`. The family parameter is the kind's suffix (family_param):
# a marker's state, a verdict's outcome, a notice's legal basis (an opaque word of a closed set the kernel does not
# read), a reconsideration's grounds. A reconsideration's outcome is a row member (`outcome`).
LONE_ACTS = {"quarantine": "slash", "slashing": "slash", "takedown_notice": "takedown"}
QUARANTINE_STATES = ("withhold", "release")
SLASH_OUTCOMES = ("proven_rogue", "not_proven")       # a verdict fires only on a proven ground
RECONSIDERATION_GROUNDS = ("new_evidence", "procedural_error", "quorum_compromise")
RECONSIDERATION_OUTCOMES = ("reversed", "partial", "upheld")    # only `reversed` fells a notice on one content row
# PROVISIONAL: the member a release, a takedown notice and a reconsideration name their target row by (the table's
# name follows with the placement cells); read here and nowhere else
ACT_OF = "of"          # a takedown notice's content row
CITES = "cites"        # the wire's refs.also.cites (G23, G24)


def cites(r):
    """The rows a row cites (the wire's `refs.also.cites`; the Constitution's G23, G24): a reconsideration names its
    takedown notice, and a lift the act it lifts, by citing it. (A release is no citation: it names its withhold by
    `target`, G21 as re-ruled.)"""
    c = r.get(CITES, ())
    return (c,) if isinstance(c, str) else tuple(c)


def the_cite(r):
    """The one row r cites, or None: a reconsideration names ITS notice and a lift THE act, so a row whose cites are
    not exactly one names nothing (r98; MUTATION first_cite: the first of several). The one accessor: the rule that
    validates the row and every reader of what it acts on (act_in_force) read the same id."""
    c = cites(r)
    if "first_cite" in MUT: return c[0] if c else None
    return c[0] if len(c) == 1 else None


def cited(r, by, pick=lambda q: True):
    """The row among `by` that r cites (the_cite) where `pick` takes it, or None."""
    q = by.get(the_cite(r))
    return q if q is not None and pick(q) else None


def lifted(r, by):
    """The act a lift cites: a duty holder's lone act, or a lone removal (an unseat)."""
    return cited(r, by, lambda q: family(q) in LONE_ACTS or q["kind"] == "unseat")


def family(r):
    """A row's family: its kind before the parameter (`slashing:proven_rogue` -> `slashing`)."""
    return r["kind"].split(":", 1)[0]


def family_param(r):
    """A row's family parameter: its kind after the family (`slashing:proven_rogue` -> `proven_rogue`), or None."""
    parts = r["kind"].split(":", 1)
    return parts[1] if len(parts) == 2 and parts[1] else None
# the halt and its confirmation (CC 4.2.1.1, the Constitution's ruling of 2026-11-28): the halt is one holder's
# `accord:invoke:constitutional:{halt_id}` row, which fires and is no voice; a strict majority of the standing holders
# confirms it by one cosigned `accord:lifecycle:confirmed` row naming (`cites`) the halt
HALT, CONFIRMED = "accord:invoke:constitutional", "accord:lifecycle:confirmed"


def is_halt(q):
    return q["kind"].startswith(HALT + ":")


def confirmed_halt(r, by):
    """The halt a confirmation names, over the confirmation's own object, or None."""
    if r["kind"] != CONFIRMED: return None
    h = cited(r, by, is_halt)
    return h if h is not None and h.get("obj") == r.get("obj") else None


def confirmation_rule(r, P, past):
    """An `accord:lifecycle:confirmed` row concludes where it names a halt of the accord it is over, at the newest
    counted changes in its past, and its signers (signer and cosigners) are a strict majority of the standing holders
    there (accord_halt's cancel cell; the halting holder may sign it as anyone; MUTATION confirmation_one_voice: one
    holder confirms)."""
    by = {q["id"]: q for q in P}
    obj, heads = r.get("obj"), r.get("head", ())
    if confirmed_halt(r, by) is None or kind_of(by, obj) != "accord": return False
    if not heads or newer_head_in_past(heads, None, P, past, obj, signers(r)): return False
    holders = members_at(P, past, obj, heads, "holder")
    v = signers(r) & holders
    return bool(v) if "confirmation_one_voice" in MUT else 2 * len(v) > len(holders)


def marker_key(r, by):
    """The key a quarantine marker or a slashing verdict is about: its `target`; for a release, its withhold's (a
    release names its withhold, not a key)."""
    if r["kind"] == "quarantine:release":
        w = by.get(r.get("target"))
        return None if w is None else w.get("target")
    return r.get("target")


def act_targets(r, by):
    """The keys an act is against: an unseat's `to`; a quarantine marker's or a slashing verdict's `target`; a takedown
    notice's content row's signer (the member whose content it takes down)."""
    if family(r) in ("quarantine", "slashing"): return frozenset((marker_key(r, by),)) - {None}
    if family(r) == "takedown_notice":
        c = by.get(r.get(ACT_OF))
        return frozenset((c["signer"],)) if c is not None else frozenset()
    return frozenset(r.get("to", ()))


def lone_act_rule(r, P, past):
    """A quarantine marker, a slashing verdict or a takedown notice concludes where its shape holds and:
        in a community   it is one duty holder's signature (CC 4.5.4 (iii)): its signer holds the duty that authorises it
                         (`slash`, `takedown`) at the heads it names, the newest counted changes over the room in its own
                         past (H4, as every act read on a seat); never counted (MUTATION lone_act_counted: a count asked);
        in an affiliation  the body's act, counted over its officers (affiliation_count): one officer makes it a proposal,
                         in force only with a countersign (act_in_force).
    Shapes: a marker's state is withhold or release, and a release is its withholder's `supersedes` of the withhold, named by `target` (G21), of the same key,
    in its past; a verdict's outcome is proven_rogue or not_proven; a takedown names (`of`) a content row in its past."""
    by = {q["id"]: q for q in P}
    obj, k, param = r.get("obj"), family(r), family_param(r)
    if k == "quarantine":
        if param not in QUARANTINE_STATES or r.get("target") is None: return False
        if param == "release":
            # a release is the withholding holder's `supersedes` of its own withhold, named by `target` (the
            # Constitution's G21 as re-ruled: the quarantine fold ranks withhold over release, and "released
            # supersedes withheld"); a release of anything else concludes nothing
            w = by.get(r["target"])
            if w is None or w["kind"] != "quarantine:withhold" or w.get("obj") != obj or w.get("target") is None:
                return False
            # only the holder that withheld releases it: another holder's release does nothing (its routes are the
            # members' lift, which cites the act, or a review; MUTATION release_by_any_holder)
            if w["signer"] != r["signer"] and "release_by_any_holder" not in MUT: return False
    if k == "slashing" and (param not in SLASH_OUTCOMES or r.get("target") is None): return False
    if k == "takedown_notice" and (param is None or r.get(ACT_OF) not in by): return False
    # the target is the room's: a takedown's content row is of obj (its `room`, or its object), and a marker's or a
    # verdict's key is seated over obj at the act's heads (MUTATION target_any_room)
    if k == "takedown_notice" and by[r[ACT_OF]].get("room", by[r[ACT_OF]].get("obj")) != obj \
            and "target_any_room" not in MUT:
        return False
    kind = kind_of(by, obj)
    heads = r.get("head", ())
    if not heads or newer_head_in_past(heads, None, P, past, obj, signers(r)): return False
    if k in ("quarantine", "slashing") and "target_any_room" not in MUT and marker_key(r, by) not in (
            members_at(P, past, obj, heads, "member") | members_at(P, past, obj, heads, AGENT)):
        return False
    if kind == "affiliation":
        return affiliation_count(r, P, past)
    if not community(by, obj): return False
    if "lone_act_counted" in MUT: return count_met(dict(r, counted="duty", policy="duty_confer"), P, past)
    return r["signer"] in members_at(P, past, obj, heads, LONE_ACTS[k]) and (len(signers(r)) == 1 or "lone_act_cosigned" in MUT)


def reconsidered(r):
    """A reconsideration's shape: grounds (its family parameter) of the closed set, an outcome of the three."""
    return family_param(r) in RECONSIDERATION_GROUNDS and r.get("outcome") in RECONSIDERATION_OUTCOMES


def reconsideration_rule(r, P, past):
    """A `reconsideration:{grounds}` row (the review duty's act, CC 4.5.5): one review holder's signature, at the newest
    counted changes in its past, citing (`cites`, G23) a takedown notice in its past, with outcome `reversed` or not. A
    concluded reversal takes the takedown down (act_in_force)."""
    by = {q["id"]: q for q in P}
    t = cited(r, by, lambda q: family(q) == "takedown_notice")
    if t is None or family(t) != "takedown_notice" or not reconsidered(r): return False
    # no act is reversed by its own target: the author of the content taken down never reconsiders it (self_release)
    if r["signer"] in act_targets(t, by) and "self_release" not in MUT: return False
    obj, heads = t.get("obj"), r.get("head", ())
    if not heads or newer_head_in_past(heads, None, P, past, obj, signers(r)): return False
    return r["signer"] in members_at(P, past, obj, heads, "review")


def end_never_revived(S, r, scope, counts):
    """THE end reading, as key ends and withdrawals read it: an end, once in a row's past, is never revived, and an
    end concurrent with a row cuts it (rule 4). For an act that is itself an END (a release, its withhold's end):
    whether an end of its author's `scope` seat over its room (ends_of: a lay-down, an unseat, the end of its stay)
    that counts is concurrent with r, neither in the other's past, and so cuts it. An end in r's past left r's author
    no standing to make it (the act's own rule refuses it); an end with r in its past cuts nothing (MUTATION
    release_concurrent_kept: no concurrent end read)."""
    if "release_concurrent_kept" in MUT: return False
    obj, k = r.get("obj"), r["signer"]
    for e in S.Cs:
        if e["id"] == r["id"] or e["id"] in S.anc[r["id"]] or r["id"] in S.anc[e["id"]] or not counts(e): continue
        if any(kk == k and ob == obj and (sc is None or sc == scope or sc in ROSTER_SEATS) for kk, sc, ob in ends_of(e, S.by)):
            return True
    return False


def act_in_force(S, act, own=None):
    """Whether act `act` (a quarantine marker, a slashing verdict or a takedown notice; or any counted row) is in force
    for the reader holding S (`own`: its key, for its line). A lone act of a community: concluded, and in force by the
    end rule (removal_in_force read for its duty: its signer's standing live, or a receipt by another duty holder
    keeping it); not lifted by the members (a concluded lift, `moderation_overturn` of scope `act`, naming it); a
    takedown not reversed by a concluded reconsideration naming it; a quarantine withhold not lifted by a release in
    force that names it (a withhold outranks a release whatever their instants: only a release naming it lifts it);
    a slashing verdict fires only on a proven ground (`not_proven` is in force as a verdict and fires nothing: False).
    In an affiliation the act is the body's, counted over its officers; with one officer it is decided only by a
    countersign naming it (rule 4: a concurrent withdrawal by the acting seat leaves nothing decided)."""
    r = S.by.get(act)
    if r is None or not S.C.get(act): return False
    if family(r) not in LONE_ACTS: return bool(S.C.get(act))
    Q = Seats(S, own=own)
    if act in Q.stale: return False
    obj = r.get("obj")
    P = [q for q in S.Cs if q["id"] in S.anc[act]]
    past = lambda a, b: a in S.anc[b]
    held = lambda kind, pred: [q for q in S.Cs if q["kind"] == kind and pred(q) and Q.cut.counts(q) and q["id"] not in Q.stale]
    if kind_of(S.by, obj) == "affiliation":
        if needs_countersign(r, P, past) and "countersign_unread" not in MUT \
                and not decided_in(r, {q["id"]: q for q in S.Cs}, past):
            return False
    else:
        unseats = [u for u in S.Cs if u["kind"] == "unseat" and Q.cut.counts(u) and u["id"] not in Q.stale]
        # a release is an END of its withhold (it supersedes it), not a standing act: it is read by the one end reading
        # (end_never_revived), not by the E rules a standing lone act is read by (live standing, or a receipt). So it
        # stands where its author's end has it in its past, and an end concurrent with it cuts it (rule 4). MUTATION
        # release_end_read: the E rules read the release too (review-58's n1: the withhold comes back)
        standing = r["kind"] != "quarantine:release" or "release_end_read" in MUT
        if standing and "lone_act_end_unread" not in MUT and not removal_in_force(
                S, r, unseats, Seats(S, own=own, roster=False), scope=LONE_ACTS[family(r)]):
            return False
        counts = lambda e: Q.cut.counts(e) and e["id"] not in Q.stale
        if not standing and end_never_revived(S, r, LONE_ACTS[family(r)], counts):
            return False
        lifted = held("offer", lambda q: q.get("scope") == "act" and the_cite(q) == act and q.get("conf") == "group")
        if lifted and "lone_act_lift_unread" not in MUT: return False
        if family(r) == "takedown_notice" and "reconsideration_unread" not in MUT and [
                q for q in S.Cs if family(q) == "reconsideration" and the_cite(q) == act and q.get("outcome") == "reversed"
                and Q.cut.counts(q) and q["id"] not in Q.stale]:
            return False
    if r["kind"] == "quarantine:withhold" and "release_unread" not in MUT:
        if any(act_in_force(S, q["id"], own) for q in S.Cs if q["kind"] == "quarantine:release" and q.get("target") == act):
            return False
    if family(r) == "slashing" and family_param(r) != "proven_rogue" and "unproven_fires" not in MUT: return False
    return True


def contested_out(S, unseats):
    """The counted removals among `unseats` that are out of force as contested (CC 2.7.7 rule 5: "Two cuts by keys of
    equal standing that undo each other stay contested. A voice that the other cannot remove settles them"; CC 2.6.1.9,
    2.6.1.11). A voice of a counted removal u is no voice where another counted removal over the same group, concurrent
    with u (neither in the other's past) and in force, removes it; u is in force only if its count is still met
    without those voices. Read as the well-founded fixed point: two removals that each need a voice the other
    removes are both out of force (the roster stays as it was, and a later count that names both decides); one that
    needs nothing the other removes stands, and the other falls (the one-sided case). Nothing here is special: it is
    the end rule (a removed key's voice counts only where its removal is in that row's past) read for counted rows."""
    if "contested_both_out" in MUT: return frozenset()
    # every group (CC 2.7.7 is not scoped by kind; MUTATION contested_scoped_to_kinds: the old family/infrastructure scope)
    # a moderator's lone removal is judged by the end rule and its receipts (out_of_force), not here
    grp_u = [u for u in unseats if u.get("conf") == "group" and not lone_act(u, S) and (
        "contested_scoped_to_kinds" not in MUT or kind_of(S.by, u.get("obj")) in ("family", "infrastructure"))]
    if len(grp_u) < 2: return frozenset()
    conc = lambda a, b: a["id"] not in S.anc[b["id"]] and b["id"] not in S.anc[a["id"]]
    # a removed key's concurrent voice counts at its own head and is not in force from the removal's head on: u2's
    # removal voids a voice of u only where u counts from u2's heads on (each head of u2 is a head of u or in its past)
    at_or_after = lambda u, u2: "contested_voice_everywhere" in MUT or all(
        any(h2 == h or h2 in S.anc.get(h, ()) for h in u.get("head", ())) for h2 in u2.get("head", ()))
    pasts = {u["id"]: [q for q in S.Cs if q["id"] in S.anc[u["id"]]] for u in grp_u}
    # the keys a cut removes: an unseat's `to`; a dissolution's, every key holding a seat over its group in its past
    cut_keys = {u["id"]: (frozenset(x["k"] for x in seats_of(pasts[u["id"]]).recs if x["obj"] == u.get("obj"))
                          if is_dissolve(u) else frozenset(u["to"])) for u in grp_u}
    threats = {}
    for u in grp_u:
        vs = voices(u, pasts[u["id"]])
        t = [(u2["id"], cut_keys[u2["id"]] & vs) for u2 in grp_u
             if u2 is not u and u2.get("obj") == u.get("obj") and conc(u, u2) and at_or_after(u, u2)
             and cut_keys[u2["id"]] & vs]
        if t: threats[u["id"]] = t
    if not threats: return frozenset()
    # MUTATION contested_one_sided: every cut in a threat, threatened or threatening, contested (rule 5 read too widely:
    # only mutual dependence is contested, and a one-sided cut stands, rule 4 from the head it names)
    if "contested_one_sided" in MUT:
        return frozenset(threats) | frozenset(i for t in threats.values() for i, _ in t)
    past = lambda a, b: a in S.anc[b]
    memo = {}

    def holds(u, live):
        if u["id"] not in threats: return True
        void = frozenset(k for i, ks in threats[u["id"]] if i in live for k in ks)
        key = (u["id"], void)
        if key not in memo: memo[key] = still_met(u, pasts[u["id"]], past, void)
        return memo[key]
    d, pos = frozenset(), frozenset(u["id"] for u in grp_u)
    while True:
        d2 = frozenset(u["id"] for u in grp_u if holds(u, pos))
        p2 = frozenset(u["id"] for u in grp_u if holds(u, d))
        if (d2, p2) == (d, pos): break
        d, pos = d2, p2
    return frozenset(u["id"] for u in grp_u if u["id"] not in d)


def out_of_force(S, unseats, holds, confers, depth, own, checkpoint):
    """The lone removals among `unseats` the end rule holds out of force over S."""
    acts = [u for u in unseats if u.get("scope") == AGENT and lone_act(u, S)]
    if not acts: return frozenset()
    nows = {}

    def now(drop):
        if drop not in nows: nows[drop] = Seats(S, holds, confers, depth, own=own, checkpoint=checkpoint, drop=drop, roster=False)
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
# ---- a counting row's past: the changes void for it, and the fold of its heads (the ruling of 2026-11-27) ----------
# A counted change in a counting row's past is void for that row where it is self-forked (S''), or where it is void for
# the reader the row is read for (the reader-line exclusion). A void change is no head of the row, need not be named,
# and adds nothing to its members. The members at several heads are the fold of their lines (Seats.tips_fold, the
# guarded fold of CC 2.7.8), not their intersection.
_VOID = [frozenset()]        # the changes void for the counting row being read
_RVOID = [frozenset()]       # the changes void for the reader that row is read for
_RPAIRS = [frozenset()]      # the concurrent founders' amendments the reader holds: (a, b, the keys the two seat)
_RENDS = [frozenset()]       # the seat ends (lay-downs, leavings) behind the reader's line: no vacancy end for it
_RRIVAL = [frozenset()]      # the rival self-roster foundings for the reader: its line took up another of the identity's


def _built_closure(acts, void, stop=lambda q: False):
    """void, and every counted change of acts built on one in it (a head it names in it), but those `stop` keeps."""
    out = set(void)
    changed = True
    while changed:
        changed = False
        for q in acts:
            if q["id"] not in out and any(h in out for h in q["head"]) and not stop(q):
                out.add(q["id"]); changed = True
    return out


def void_changes(r, P):
    """S'': the counted changes over r's object in r's past P void for r. The only automatic effect of a key signing two
    things outside an election; it voids a change, never a key.
        self-forked  every counted voice of q (its signers who are members at its heads) has, in P, acknowledged a
                     counted change q is behind (checkpoint.behind: every head q names strictly in the past of that
                     change's own heads, q not in its past); MUTATION self_fork_unread: nothing is void
        T            a self-forked q is void only where, of the members seated at its fork point (its heads), those
                     who signed only the other side outnumber those who signed only q's side (t_void); equal, none on
                     either side included, neither is void: depth decides nothing; MUTATION t_unread: a self-forked
                     change is void; MUTATION fork_by_depth: the S' form, void unless a change it is behind is
                     self-forked too
        built on     a counted change naming a void head is void, but a merge of both lines."""
    if not P or "self_fork_unread" in MUT: return frozenset()
    key = (r["id"], r.get("obj"), frozenset(id(q) for q in P), frozenset(MUT), _RVOID[-1])
    got = _VOID_MEMO.get(key)
    if got is None:
        got = _VOID_MEMO[key] = (tuple(P), _void_changes(r, P))
    return got[1]


_VOID_MEMO = {}


def _void_changes(r, P):
    S = CK.State(list(P), {q["id"]: True for q in P})
    obj = r["obj"]
    acts = CP.counted_acts(S, obj)
    if not acts: return frozenset()
    past = lambda a, b: a in S.anc.get(b, ())
    info = {}
    for q in acts:
        qP = [x for x in P if past(x["id"], q["id"])]
        mem_q = members_at(qP, past, obj, q["head"])
        info[q["id"]] = (voices(q, qP) & mem_q, mem_q)
    # each voice's rows in P over obj; a voice k of q forked against q where a row k signed WITHOUT q in its past
    # acknowledges a change q is behind (a row with q in its past, a merge of both lines, is no fork)
    signed_rows = {}
    def signed(k):
        if k not in signed_rows:
            signed_rows[k] = [a for a in P if (a["signer"] == k or k in a.get("cosigners", ())) and CP.object_of(a, S.by) == obj]
        return signed_rows[k]
    def forked_by(q, k):
        """The changes q is behind that k acknowledged by a row without q in its past."""
        return [c for a in signed(k) if a["id"] != q["id"] and not past(q["id"], a["id"])
                for c in acts if (c["id"] == a["id"] or c["id"] in S.anc[a["id"]]) and CP.behind(S, q, c)]
    def forked(q):
        v = info[q["id"]][0]
        return bool(v) and all(forked_by(q, k) for k in v)
    out = {q["id"] for q in acts if forked(q)}
    if not out: return frozenset()
    if "fork_by_depth" in MUT:
        # the S' form (MUTATION): a self-forked change is void unless a change it is behind is self-forked too, so the
        # side with the longer chain wins where the same voices signed both
        tv = {i for i in out if not any(c["id"] in out for c in acts if CP.behind(S, S.by[i], c))}
    else:
        tv = {i for i in out if t_void(S, P, obj, acts, past, info, S.by[i], out)}
    # a change built on a void one is void, but a merge of both lines (a change the void one is behind in its past
    # too), which reads its count without the void change, as any counting row does
    line = {i: [c["id"] for c in acts if c["id"] != i and not past(i, c["id"]) and CP.behind(S, S.by[i], c)] for i in tv}
    merge = lambda b: any(past(f, b["id"]) and any(past(c, b["id"]) for c in line[f]) for f in tv)
    return frozenset(_built_closure(acts, tv, merge))


def _tuple(x):
    return () if x is None else (x,) if isinstance(x, str) else tuple(x)


def t_void(S, P, obj, acts, past, info, q, forked=frozenset()):
    """T at q's fork point (CC: "where two changes at one fork point would each be void by voices that signed both
    chains, the chain stands that the members seated at the fork point who signed only one chain built on; where there
    are none, neither is void"). The fork point is q's heads; its members are those seated there. q is void where the
    fork-point members who signed only the other side outnumber those who signed only q's side; equal (none on either
    side included), neither is void. What counts (the fourth attack):
        counted      a member counts for a side only through a counted change it voiced: posts, acknowledgements,
                     content and acceptances count for nothing (MUTATION t_counts_posts: every row's signers count)
        on the side  q's side is q and the counted changes built on it; the other side is the competing line (the
                     changes q is behind, and the changes they name as heads back to the fork point) and the counted
                     changes built on them, never a row a side merely cites (what a row cites is its author's choice:
                     a member is not recruited by being named); a merge of both lines (a change with q and a change q is behind in its
                     past) is on neither
        standing     a voice counts for a side only where the key held, at the fork point, the seat the voice relies
                     on (a member's seat, or for a duty-counted change a duty), or holds it by a change
                     that is neither on q's side nor itself self-forked: a seat from the self-forked side, or from a
                     sibling fork, is no evidence, and a seat granted by the other line's own non-forked change
                     gives standing (MUTATION t_counts_sided_seat: every seat counts; MUTATION t_strict_standing:
                     only a seat held at the fork point)
        beneficiary  a key's yes on an offer seating it counts it for neither (MUTATION t_counts_beneficiary: it does)
    MUTATION t_unread: a self-forked change is void."""
    if "t_unread" in MUT: return True
    qid = q["id"]
    mem = info[qid][1]
    fp = set(q["head"]) | {x for h in q["head"] for x in S.anc.get(h, ())}
    posts = "t_counts_posts" in MUT
    pool = [a for a in P if CP.object_of(a, S.by) == obj] if posts else list(acts)
    rows = [a for a in pool if a["id"] not in fp]
    behind = [c for c in acts if c["id"] != qid and not past(qid, c["id"]) and CP.behind(S, q, c)]
    # the competing line: each change q is behind and the changes it names as heads back to the fork point (a row it
    # merely cites is not on it)
    chain = set()
    todo = [c["id"] for c in behind]
    while todo:
        x = todo.pop()
        if x in chain or x in fp or x not in S.by: continue
        chain.add(x)
        todo.extend(S.by[x].get("head", ()))
    def on_line(a):
        return a["id"] in chain or any(past(c["id"], a["id"]) for c in behind)
    mine = [a for a in rows if (a["id"] == qid or past(qid, a["id"])) and not any(past(c["id"], a["id"]) for c in behind)]
    other = [a for a in rows if a["id"] != qid and not past(qid, a["id"]) and not past(a["id"], qid) and on_line(a)]
    qP = [x for x in P if past(x["id"], qid)]
    held = {}
    def held_fp(sc):
        if sc not in held:
            held[sc] = mem if sc == "member" else members_at(qP, past, obj, q["head"], sc)
        return held[sc]
    def standing(k, a):
        """k's voice on a relies on a seat it held at the fork point, or one seated by a change that is neither on q's
        side nor self-forked."""
        if "t_counts_sided_seat" in MUT: return True
        sc = "duty" if a.get("counted") == "duty" else "member"
        if k in held_fp(sc): return True
        if "t_strict_standing" in MUT: return False
        dec = declared(S.by, obj)
        fits = (lambda x: x is not None and is_duty(x, dec)) if sc == "duty" else (lambda x: x == "member")
        return any(o.get("kind") == "offer" and fits(o.get("scope")) and k in _tuple(o.get("to"))
                   and o["id"] != qid and not past(qid, o["id"]) and o["id"] not in forked and past(o["id"], a["id"])
                   for o in P)
    def keys(rs):
        ben = "t_counts_beneficiary" not in MUT
        out = set()
        for a in rs:
            if ben and a.get("kind") == "accept": continue
            ks = (set(info[a["id"]][0]) if not posts and a["id"] in info else {a["signer"], *a.get("cosigners", ())})
            ks -= set(_tuple(a.get("to"))) if ben and a.get("kind") == "offer" else set()
            out |= {k for k in ks & mem if standing(k, a)}
        return out
    km, ko = keys(mine), keys(other)
    return len(ko - km) > len(km - ko)


def roster_void(S):
    """S'' over the rows S holds, for each room a counted act is over, as if one row had them all in its past: the
    changes a reader's roster leaves out (they neither add nor remove members)."""
    out = set()
    # over the rows concluded for a reader, its line's void is in force (the crate's roster_void reads the same)
    _RVOID.append(frozenset(getattr(S, "_rvoid", frozenset())))
    try:
        for obj in sorted({r["obj"] for r in S.Cs if CP.is_counted_act(r, r.get("obj"))}, key=str):
            out |= void_changes({"id": ("roster", obj), "obj": obj, "kind": "roster"}, S.Cs)
    finally:
        _RVOID.pop()
    return frozenset(out)


def _ack_void(S, a):
    """The counted acts void for a reader's own counted row a (checkpoint.own_line)."""
    P = [q for q in S.Cs if q["id"] in S.anc.get(a["id"], ())]
    # in the rows concluded for a reader, the changes its line voided are left out of its own counted rows too, and the
    # row's own void is read with them (the crate's ack_void reads the same)
    rv = getattr(S, "_rvoid", frozenset())
    _RVOID.append(frozenset(rv))
    try:
        return (void_changes(a, P) if a.get("obj") is not None else frozenset()) | rv
    finally:
        _RVOID.pop()


CP.ACK_VOID = _ack_void


def reader_void(S, own):
    """The counted changes void for reader `own` by its line (checkpoint.void, every row taken as counting)."""
    return CP.void(S, CP.EVERY, own)


def reader_ends(S, own):
    """The seat ends behind reader `own`'s line (the Constitution's ruling on H4: a lay-down is a roster change: it
    names the newest counted changes over its room and sits on the reader's line by them): each withdrawal of a seat
    over a community whose newest named counted changes (its room's founding row where it names none) are all strictly
    in the past of the own heads of a counted act on the reader's line, it not in that act's past (checkpoint.behind,
    sibling-safe). Such an end is no vacancy end for that reader (MUTATION laydown_off_line: none is)."""
    if own is None or "laydown_off_line" in MUT: return frozenset()
    past = lambda a, b: a in S.anc[b]
    out, lines = set(), {}
    for w in S.Cs:
        if w["kind"] != "withdraw": continue
        t = S.by.get(w.get("target"))
        room = CP.object_of(t, S.by) if t is not None and t["kind"] in ("offer", "accept") else None
        if room is None or room not in S.by or not community(S.by, room): continue
        if room not in lines: lines[room] = CP.own_line(S, own, room)
        if not lines[room]: continue
        hs = newest(tuple(n for n in w["names"] if n in S.by and change(S.by[n], room, S.by)), past) or (room,)
        if any(CP.behind(S, dict(w, head=hs), c) for c in lines[room]): out.add(w["id"])
    return frozenset(out)


def held_pairs(S):
    """The concurrent founders' amendments the rows S holds (CC 2.7.8's wait, read for the reader holding them): pairs
    of concluded record versions seating founders over one room, neither in the other's past, with no record version
    of that room naming both. (a, b, the keys the two seat, the room)."""
    vs = [q for q in S.Cs if q["kind"] == "offer" and q.get("conf") == "group" and q.get("scope") == "record"
          and q.get("obj") is not None]
    seating = [q for q in vs if q.get("role") == "founder" and q.get("to")]
    if len(seating) < 2: return frozenset()
    past = lambda a, b: a in S.anc[b]
    return frozenset((a["id"], b["id"], frozenset(a["to"]) | frozenset(b["to"]), a["obj"])
                     for i, a in enumerate(seating) for b in seating[i + 1:]
                     if a["obj"] == b["obj"] and not past(a["id"], b["id"]) and not past(b["id"], a["id"])
                     and not any(q["obj"] == a["obj"] and past(a["id"], q["id"]) and past(b["id"], q["id"]) for q in vs))


def reader_rivals(S, own):
    """The rival self-roster foundings for reader `own` (the ruling on one self roster per identity): of an identity's
    foundings held, the one the reader's LINE takes up (checkpoint.takes_up) is its roster, and the others are rivals
    for it. Where the line takes up neither or both, none is chosen: the reader waits (rosters_of). MUTATION
    rival_line_unread: no reader's line is read."""
    if own is None or "rival_line_unread" in MUT: return frozenset()
    mine = {}
    for g in S.Cs:
        if is_self_founding(g): mine.setdefault(g["signer"], []).append(g)
    out = set()
    for fs in mine.values():
        if len(fs) < 2: continue
        t = CP.takes_up(S, own, [f["id"] for f in fs], MUT | CP.MUT, voices)
        if len(t) == 1: out |= {f["id"] for f in fs if f["id"] not in t}
    return frozenset(out)


def rival_row(r, by, rivals):
    """Row r is a rival founding, or built on one: a row over it, or the acceptance or withdrawal of a row over it."""
    if r["id"] in rivals or r.get("obj") in rivals: return True
    for f in ("of", "target"):
        q = by.get(r.get(f))
        if q is not None and (q["id"] in rivals or q.get("obj") in rivals): return True
    return False


def reader_state(S, own, rule=None):
    """The rows concluded again for reader `own`: the changes void for it by its line (over the rows as concluded for
    every reader) are left out of every counting row's fold and heads, so a count that stands for this reader and not
    for a reader with no row is in its roster, and one refused for it is not (CC 2.7.9: "A reader's own acknowledged
    head closes older heads for that reader only"). MUTATION reader_exclusion_unread: the rows as for every reader."""
    if "reader_exclusion_unread" in MUT: return S
    key = (frozenset(id(q) for q in S.rows), frozenset(S.C.items()), own, frozenset(MUT))
    got = _READER_MEMO.get(key)
    if got is not None: return got[1]
    RV = reader_void(S, own) if own is not None else frozenset()
    # the concurrent founders' amendments the reader holds are read into every founders' count (C2)
    PR = held_pairs(S) if "wait_reader_unread" not in MUT else frozenset()
    # the seat ends behind its line are no vacancy ends for it (H4, the election)
    RE = reader_ends(S, own)
    # the rival self-roster foundings for it: its line took up another of the identity's
    RR = reader_rivals(S, own)
    if not RV and not PR and not RE and not RR:
        _READER_MEMO[key] = (tuple(S.rows), S)
        return S
    _RVOID.append(frozenset(RV)); _RPAIRS.append(PR); _RENDS.append(RE); _RRIVAL.append(RR)
    try:
        R = CK.concluded(CK.kept(list(S.rows)), rule or (lambda r, P, past: seat_rule(r, P, past)))
    finally:
        _RVOID.pop(); _RPAIRS.pop(); _RENDS.pop(); _RRIVAL.pop()
    R._reader, R._rvoid, R._paired = own, frozenset(RV), True
    _READER_MEMO[key] = (tuple(S.rows), R)
    return R


_READER_MEMO = {}


def members_at(P, past, obj, heads, scope="member"):
    """The live `scope` seats over obj at the newest of the heads named, the changes void for the row being read apart
    (they are no heads): read over the union of the heads' pasts, with the withdrawals of P and the acceptances in P
    that complete a seat placed there. One head reads its own line; several are folded (Seats.tips_fold, the guarded
    fold of CC 2.7.8; MUTATION meet_tips: the keys common to every head, as before the ruling of 2026-11-27)."""
    if "meet_tips" in MUT: return _members_meet(P, past, obj, heads, scope)
    void = _VOID[-1] | _RVOID[-1]
    hs = tuple(h for h in count_heads(heads, P, past) if h not in void)
    if not hs: return frozenset()
    ids = {q["id"] for q in P}
    if any(h not in ids for h in hs): return frozenset()
    sub = [q for q in P if q["id"] not in void and any(q["id"] == h or past(q["id"], h) for h in hs)]
    sids = {q["id"] for q in sub}
    by = {q["id"]: q for q in P}
    ends = [] if "ends_at_heads_unread" in MUT else [w for w in P if w["kind"] == "withdraw" and w["id"] not in sids]
    return seats_of(sub + ends + [by[a] for a in completing(sids, P, by, obj, past)]).holders(scope, obj)


def _members_meet(P, past, obj, heads, scope="member"):
    """The live `scope` seats over obj, read from the rows in the past of the heads only. Several heads: the
    keys common to all of them (KERNEL.md section 7)."""
    out = None
    by = None
    for h in count_heads(heads, P, past):              # the count is read at the newest heads named
        sub = [q for q in P if q["id"] == h or past(q["id"], h)]
        if not any(q["id"] == h for q in sub): return frozenset()
        by = by or {q["id"]: q for q in P}
        ids = {q["id"] for q in sub}
        # a lone removal at the heads that the remover's own ending, in the counted row's past, puts out of force is
        # read so there: the withdrawals in that past are read with the heads (a withdrawal is no counted change, so
        # no head is read through; MUTATION ends_at_heads_unread)
        ends = [] if "ends_at_heads_unread" in MUT else [w for w in P if w["kind"] == "withdraw" and w["id"] not in ids]
        m = seats_of(sub + ends + [by[a] for a in completing(ids, P, by, obj, past)]).holders(scope, obj)
        out = m if out is None else out & m
    return out or frozenset()


def completing(sub_ids, P, by, obj, past):
    """The acceptances in a counted row's own past P that complete a seat placed at its heads (a seat is two
    consents: the ruling of 2026-11-26 on acceptances, (a)), read with the heads' rows: each signed by the key the
    offer seats (bound (4): never a cosignature, never another key's row), of an offer in the heads' past (bound (1):
    no seat is created from outside the heads), the offer not ended in P (bound (2): a withdrawal of it or of the
    acceptance, a counted removal of the key with the offer in its past, or the key's own end of its stay with the
    offer in its past; bound (3): in a private room a key whose stay ended completes nothing). The leavings in P are
    read with the heads too (members_at). MUTATIONS acceptance_unread; acceptance_ends_unread (an ended offer
    completed)."""
    if "acceptance_unread" in MUT: return []
    stays = None
    out = set()
    for a in P:
        if a["id"] in sub_ids: continue
        if a["kind"] != "accept": continue
        o = by.get(a.get("of"))
        if o is None or o["kind"] != "offer": continue
        if o["id"] not in sub_ids: continue
        for k in ([a["signer"]] if a["signer"] in o["to"] else []):
            if "acceptance_ends_unread" not in MUT:
                if any(w["kind"] == "withdraw" and w["target"] in (o["id"], a["id"]) for w in P): continue
                if any(u["kind"] == "unseat" and k in u["to"] and u.get("obj") == o.get("obj") and past(o["id"], u["id"])
                       for u in P): continue
                stays = stay_ends(P, by, lambda x, w: x["id"] in by and past(x["id"], w["id"])) if stays is None else stays
                # the key's own end of its stay ends every seating of it in that scope in the end's past (check_room_keys,
                # a second seat row); in a private room a key whose stay ended completes nothing at all
                private = private_room(by, obj)
                if any(k2 == k and g == obj and (private or past(o["id"], w["id"])) for w, k2, g in stays): continue
            out.add(a["id"])
    return sorted(out)


_SEATS_OF = {}


def key_record_ended(P, k):
    """The key's own end in a row's past, for its person (ruled on CIRISConstitution#224): the key's own revocation
    (CC 2.4.1.1: "only the key's own revocation ends its liveness"), an unseat of its `registered` seat by the key
    itself, is in P (the row's concluded past). The key record's stated end is read against the key's own instant on
    the key's own rows (key_end.covers, the half-open end), never here: no foreign clock is read."""
    if "person_end_unread" in MUT: return False                    # MUTATION: the key's own end is not read
    return any(q["kind"] == "unseat" and q.get("scope") == "registered" and q.get("obj") == k and k in q["to"]
               and q["signer"] == k for q in P)


def evicted_from(S, rid, g, k):
    """Rule 4 for an eviction concurrent with the row: an eviction of k from self roster g (a counted unseat of its own
    scope over g) that concluded, neither in the row's past nor having the row in its own, counts at its own head and
    is out of force from that head on: the key is out for a row that has every head the eviction names in its past."""
    if "concurrent_eviction_unread" in MUT: return False          # MUTATION: a concurrent eviction is not read
    anc = S.anc[rid]
    landed = landed_evictions(S, S.Cs) if "landed_eviction_unread" not in MUT else []
    for e in list(S.Cs) + landed:
        if e["kind"] != "unseat" or e.get("obj") != g["id"] or e.get("scope") != g["scope"] or k not in e["to"]: continue
        if e["id"] in anc or rid in S.anc[e["id"]]: continue       # in the row's past (read by the walk), or after it
        heads = e.get("head", ())
        if heads and all(h == rid or h in anc for h in heads): return True
    return False


def rosters_of(P, k, keep=lambda g: True):
    """The self rosters k holds a live seat of over P (a row's concluded past), in their own scope: their ids, sorted.
    `keep(g)`: a self roster still in play (person_of's rule 4). A key that revoked itself is in none."""
    if key_record_ended(P, k): return []
    by = {q["id"]: q for q in P}
    selves = [g for g in P if g["kind"] == "offer" and g.get("obj") == g["id"]
              and (kind_of(by, g["id"]) == "self" or "person_any_kind" in MUT)]   # MUTATION person_any_kind: any group
    # one self roster per identity (G1, as ruled): a reader's roster for an identity is the founding its LINE takes up
    # (reader_rivals: the other foundings, and every row over them, conclude nothing for that reader, so they are not
    # in P). Two foundings by one identity still in P are held by a reader whose line takes up neither (a fresh
    # reader) or both: it waits and never picks, and neither is that identity's roster (MUTATION rival_roster_kept)
    if "rival_roster_kept" not in MUT:
        n = {}
        for g in selves: n[g["signer"]] = n.get(g["signer"], 0) + 1
        selves = [g for g in selves if n[g["signer"]] == 1]
    if "person_evict_unread" in MUT:                              # MUTATION: an admission in the past is enough
        return sorted({g["id"] for g in selves if any(q["kind"] == "offer" and q.get("obj") == g["id"] and k in q["to"]
                                                      for q in P)})
    Q = seats_of(P)
    return sorted({g["id"] for g in selves if k in Q.holders(g["scope"], g["id"]) and keep(g)})


def person_in(P, k, keep=lambda g: True):
    """The person key k is over P (a row's concluded past) alone: person_of with no rule 4 (a conclusion reads its
    row's past only; a concurrent eviction is no part of it). `keep(g)`: a self roster g still in play (person_of's
    rule 4). The person is named by its identity key (person_key: the genesis key that signed its rosters' founding
    records). None for no person or two."""
    hit = rosters_of(P, k, keep)
    # a person is its IDENTITY key (the self roster's object is the identity key, never one roster row or one key
    # record): two rosters founded by one genesis key are one person (MUTATION genesis_unread: each roster a person)
    names = sorted(set(hit)) if "genesis_unread" in MUT else sorted({person_key(P, g) for g in hit})
    if len(names) == 1 or ("person_first" in MUT and names): return names[0]   # MUTATION person_first: the first
    return None


def person_of(S, rid, k):
    """The person key k is at row rid, as a function of rows (ruled on CIRISConstitution#224), with no instant: the
    self roster (an object of kind `self`: a person's own key roster, or a voice's room keys in a private room) where,
    in the row's own past, k is the genesis key (it signed the founding record) or was seated by a counted addition
    (an `identity:occurrence` that landed, self_roster_add), no eviction of it has landed (self_roster_evict), and
    an eviction concurrent with the row follows rule 4 (evicted_from); and the key's own revocation is not in the
    row's past (key_record_ended). The answer is the person's IDENTITY key (the self roster's object is the identity
    key, the genesis key that signed the founding record, never one roster row or one key record), so two rosters
    founded by one genesis key are one person. None where no self roster has k live there, or where rosters of
    several identity keys do (two persons is none, as two owners are). A count is then over persons: one voice,
    however many live keys sign (persons_of)."""
    if not S.C.get(rid): return None
    anc = S.anc[rid]
    P = [q for q in S.Cs if q["id"] in anc]
    return person_in(P, k, keep=lambda g: not evicted_from(S, rid, g, k))


_PERSON_IN = {}


def person_key(P, g):
    """The key a person is named by in a room: its self roster's genesis key, the key that signed the roster's
    founding record (CC 3.1.3.2: "a voice is named by the identity reference of its first room key"; a fedID by its
    genesis key, CC 3.3.6.4)."""
    row = next((q for q in P if q["id"] == g), None)
    return None if row is None else row["signer"]


def registered_agents(P):
    """The keys an agent registration names over P: a `registered` offer whose identity says `agent`. With
    agent_keys, THE ONE agent recognition (an agent seat, over any room, or an agent registration, whatever scope the
    key was admitted under): Seats' duty reading and the person map both read it (MUTATION agent_by_seat_only: the
    registration unread)."""
    if "agent_by_seat_only" in MUT: return frozenset()
    return frozenset(q["obj"] for q in P if q["kind"] == "offer" and q.get("scope") == "registered"
                     and "agent" in (q.get("identity") or ()))


def agent_keys(P):
    """The keys of AI agents over P (CC 4.5.13: "an agent has no vote"): an agent seat over any room, or an agent
    registration, whatever scope the key was admitted under. They are in no count and never speak for a person."""
    return frozenset(x["k"] for x in seats_of(P).recs if x["scope"] == AGENT) | registered_agents(P)


def rep_of(P, k, member=False):
    """The one voice and one member key k counts as in a count read over P (ruled on CIRISConstitution#224: "one
    voice however many live keys sign", one member however many keys are seated): the key its person is named by
    (its self roster's genesis key, person_key) where k is a live key of exactly one self roster; k itself where k is
    a live key of none (a key that has no roster of its own is its own person). None, no voice and no member: a key
    of two persons; a key that revoked itself (KP6); a key whose person's genesis key revoked itself (its devices
    then speak for no one); an agent's key (KP5: never for its owner). `member`: the member k counts as in a base,
    where none of those ends a seat: a key of one self roster is its person, any other key itself. Kept per (P, k)."""
    key = (frozenset(id(q) for q in P), k, member, frozenset(MUT))
    if key not in _PERSON_IN:
        _PERSON_IN[key] = (tuple(P), _rep(P, k) if not member else _member_rep(P, k))
    return _PERSON_IN[key][1]


def is_self_founding(g):
    """g is the founding record of a self roster (its founding scope read through KINDS as `self`)."""
    return g["kind"] == "offer" and g.get("obj") == g["id"] and KINDS.get(g.get("scope")) == "self" \
        and (g.get("group_kind") != "family" or "self_founding_family" in MUT)   # MUTATION: a family read as a self roster


def founded_self(P, k):
    """k signed the founding record of a self roster over P: it is a person's genesis key (its identity)."""
    by = {q["id"]: q for q in P}
    return any(g["kind"] == "offer" and g.get("obj") == g["id"] and g["signer"] == k and kind_of(by, g["id"]) == "self"
               for g in P)


def persons_named(P, k):
    """The persons key k is a live key of over P: the genesis keys (person_key) of the self rosters it holds a live
    seat of, one each. A person is NAMED by its genesis key, so two rosters founded by the same key are one person."""
    if "genesis_unread" in MUT: return list(rosters_of(P, k))      # MUTATION genesis_unread: each roster a person
    return sorted({person_key(P, g) for g in rosters_of(P, k)})


def _member_rep(P, k):
    names = persons_named(P, k) if not key_record_ended(P, k) else []
    if len(names) != 1:                                           # a revoked key, a key of two persons: still a member
        return k
    return names[0] if "genesis_unread" not in MUT else person_key(P, names[0])


def _rep(P, k):
    if key_record_ended(P, k) and "revoked_voice_kept" not in MUT: return None     # MUTATION: a revoked key keeps its voice
    # an agent's key (CC 4.5.13: "an agent has no vote") is out before the map: never its owner's voice, whatever
    # roster lists it. It stays its own key, and is no voice of its own because no count's base holds an agent (a
    # clause one holder's act resolves still reads an agent holder's act). MUTATION agent_speaks
    if k in agent_keys(P) and "agent_speaks" not in MUT: return k
    names = persons_named(P, k)
    # a genesis key its own roster evicted is no voice of its person (G33: an eviction ends a key AS THE PERSON'S;
    # the person is its identity, and only a live key of its roster speaks for it). Its own rows read as a bare key's,
    # and the identity the room seats is no voice of it (MUTATION evicted_genesis_speaks)
    if not names: return None if founded_self(P, k) and "evicted_genesis_speaks" not in MUT else k
    if len(names) > 1 and "person_first" not in MUT: return None   # a key of two persons (two genesis keys)
    g = names[0] if "genesis_unread" not in MUT else person_key(P, names[0])
    if key_record_ended(P, g) and "revoked_voice_kept" not in MUT: return None
    return g


def keys_counted(P, obj):
    """A count over obj is a count of keys, not persons, where obj is a self roster (its own keys are what it counts:
    self_roster_add, self_roster_evict) or a key object."""
    if obj is None: return False
    by = {q["id"]: q for q in P}
    return obj not in by or kind_of(by, obj) == "self"


def as_persons(keys, P, obj=None):
    """The persons a set of keys counts as (rep_of), one each, a key that counts as none left out: one member per
    person however many of its keys are seated. A count over a self roster (keys_counted) reads the keys themselves.
    MUTATION persons_unread: the keys themselves."""
    if "persons_unread" in MUT or keys_counted(P, obj): return frozenset(keys)
    if "base_by_key" in MUT: return frozenset(keys)              # MUTATION base_by_key: the base read by key
    return frozenset(rep_of(P, k, member=True) for k in keys)


def person_for(k, base, P, by=None, obj=None):
    """The member key k speaks for in a count over `base` read over P: its person (rep_of) where that is one of the
    persons `base` counts as; else None (no voice). Over a self roster, k itself where it is in base."""
    if "persons_unread" in MUT or keys_counted(P, obj): return k if k in base else None
    r = rep_of(P, k)
    return r if r is not None and r in as_persons(base, P, obj) else None


def persons_of(vs, base, P, obj=None):
    """A count over persons (ruled on CIRISConstitution#224): the persons of `base` (as_persons) that the keys `vs`
    speak for, one voice each, however many of their live keys sign. A key with no person (two persons, revoked, an
    agent's) is no voice. A count over a self roster's own keys stays a count of keys (keys_counted)."""
    if "persons_unread" in MUT or keys_counted(P, obj): return frozenset(vs) & frozenset(base)
    b = as_persons(base, P, obj)
    return frozenset(x for x in (rep_of(P, v) for v in vs) if x is not None and x in b)


def person_keys(S, person):
    """A person's live keys over the concluded set S, with no instant: the inverse of persons_of. The keys of the self
    rosters founded by the person's genesis key `person` (Seats.holders over each in its own scope, read by
    rosters_of) that count as that person (rep_of: a key of two persons, an agent's key, a key that revoked itself,
    are none of its keys), and the genesis key itself while it counts as itself. A person whose genesis key revoked
    itself has no live key. With audience.audiences and nodes_of, the keys a row reaches:
    the node set = audiences o person_keys o nodes_of (ADOPTING.md)."""
    P = list(S.Cs)
    by = {q["id"]: q for q in P}
    selves = [g["id"] for g in P if g["kind"] == "offer" and g.get("obj") == g["id"] and g["signer"] == person
              and kind_of(by, g["id"]) == "self"]
    cand = {person} | {k for q in P if q["kind"] == "offer" and q.get("obj") in selves for k in q.get("to", ())}
    Q = seats_of(P)
    cand |= {k for g in selves for k in Q.holders(by[g]["scope"], g)}      # a landed lone-path addition seats no offer
    if "person_keys_by_offer" in MUT:                               # MUTATION: every key ever offered, no live read
        return frozenset(cand)
    return frozenset(k for k in cand if rep_of(P, k) == person)


def nodes_of(S, owner):
    """The node keys `owner` owns over the concluded set S, with no instant: the inverse of THE ONE OWNER READING,
    Seats.owner (a key holds the owner seat only by its own signature or acceptance; the binding's withdrawal or the
    owner seat's unseat ends it; two live owners is none; a re-binding ends the binding before it). Every key object
    of an owner offer whose owner is `owner`, where neither the node key nor the owner revoked itself. Which keys are
    nodes is the key records' (the caller's: identity_type `node`)."""
    P = list(S.Cs)
    objs = {q["obj"] for q in P if q["kind"] == "offer" and q.get("scope") == "owner" and isinstance(q.get("obj"), str)
            and q["obj"] not in S.by}
    if key_record_ended(P, owner) and "nodes_revocation_unread" not in MUT: return frozenset()
    Q = Seats(S)
    out = set()
    for n in objs:
        if "nodes_by_offer" in MUT:                                       # MUTATION: the offers, not the owner seat
            held = frozenset(k for q in P if q["kind"] == "offer" and q.get("scope") == "owner" and q.get("obj") == n
                             for k in q["to"])
            if owner not in held or len(held) != 1: continue
        elif "nodes_two_owners_kept" in MUT:                              # MUTATION: each live holder an owner
            if owner not in Q.holders("owner", n): continue
        elif Q.owner(n) != owner:
            continue
        if key_record_ended(P, n) and "nodes_revocation_unread" not in MUT: continue
        out.add(n)
    return frozenset(out)


def count_persons(P, obj, base, vs, voters=None, apart=None):
    """The one reading of a count by person (ruled on CIRISConstitution#224): (the base, the voices), the base
    counted by member (as_persons), the voices mapped to persons and held to the voting base (`voters`, else the
    base), and a named key set apart BY PERSON from both (`apart`: a lift's author, a receipt's remover), so its own
    devices are it. Every count reads it: the seat rule's count and lift, the fold, the count's receipt."""
    b = as_persons(base, P, obj)
    v = persons_of(vs, base if voters is None else voters, P, obj)
    if apart is None: return b, v
    ks = frozenset({apart}) if isinstance(apart, str) else frozenset(apart)
    if not keys_counted(P, obj) and "apart_by_key" not in MUT:   # MUTATION apart_by_key: only the key itself apart
        ks = ks | {rep_of(P, k) for k in ks} | {rep_of(P, k, member=True) for k in ks}
    return b - ks, v - ks


def landed_windows(S, Cs, window, V=frozenset()):
    """THE ONE READING of a self roster's lone-path window that LANDED (CC 3.3.6.4, 4.5.13; the `self_roster_evict` and
    `self_roster_add` windows): each concluded landing that says `landed` of a concluded opener of `window`, with the
    roster's own scope: (landing, opener, scope, roster)."""
    out = []
    for L in Cs:
        if L["kind"] != "landing" or L.get("says") != "landed" or L["id"] in V: continue
        p = S.by.get(L.get("of"))
        if p is None or p.get("window") != window or not S.C.get(p["id"]): continue
        g = S.by.get(p.get("obj"))
        if g is None: continue
        out.append((L, p, g.get("scope"), p["obj"]))
    return out


def landed_adds(S, Cs, V=frozenset()):
    """The keys a landed self_roster_add seats: the opener's `to` (one shape: a `target` alone seats nothing), each that
    consented by its own
    signature on the opener (a seat is two consents)."""
    out = []
    for L, p, sc, obj in landed_windows(S, Cs, "self_roster_add", V):
        for k in tuple(p.get("to") or ()):                         # the opener's `to` alone (no `target` fallback)
            if k in signers(p): out.append((L, k, sc, obj))            # its own signature on the opener
    return out


def landed_evictions(S, Cs, V=frozenset()):
    """The self rosters' lone-path evictions that landed (CC 3.3.6.4, 4.5.13: the `self_roster_evict` window): each
    concluded landing that says `landed` of a concluded opener with a target, read as the counted eviction it is, an
    unseat of the target's seat in the roster's own scope (its `cuts`), at the landing."""
    ws = [(L, p, sc, obj) for L, p, sc, obj in landed_windows(S, Cs, "self_roster_evict", V) if p.get("target") is not None]
    # two concurrent landed evictions of each other (each one's target the other's opener, over one roster) are
    # contested (rule 4, CC 2.7.7 rule 5): neither lands, as where both object (MUTATION mutual_evictions_land)
    def mutual(L, p, obj):
        return "mutual_evictions_land" not in MUT and any(
            L2["id"] != L["id"] and o2 == obj and p2["target"] == p["signer"] and p["target"] == p2["signer"]
            and L["id"] not in S.anc.get(L2["id"], ()) and L2["id"] not in S.anc.get(L["id"], ())
            for L2, p2, _, o2 in ws)
    return [dict(L, kind="unseat", to=(p["target"],), scope=sc, obj=obj, head=tuple(L.get("names", ())),
                 cuts=(("seat", p["target"], sc, obj),))
            for L, p, sc, obj in ws if not mutual(L, p, obj)]


def seats_of(rows):
    """The seats over a set of rows, each taken as concluded, kept once built: a head's past is read again by every
    row that names it, and a chain of lone removals reads every earlier one's (the run is polynomial in the chain,
    not exponential). The key is the rows themselves (by identity, held in the value so none is reused), the planted
    breaks switched on, and the tables a check may change (what a seat holds, the policies, the enders)."""
    key = (frozenset(id(q) for q in rows), frozenset(MUT), repr(sorted(HOLDS.items())), repr(sorted(POLICY.items())),
           repr(sorted(ENDS.items())))
    got = _SEATS_OF.get(key)
    if got is None:
        got = _SEATS_OF[key] = (tuple(rows), Seats(CK.State(list(rows), {q["id"]: True for q in rows}), roster=False))
    return got[1]


def agents_at(P, past, obj, heads):
    """The keys holding an AI agent's seat over obj at the heads (`agent`), or a node's seat (`node`, over an
    infrastructure community): on the roster, in no count."""
    out = frozenset()
    for sc in (AGENT, NODE):
        if any(q.get("scope") == sc for q in P):
            out |= members_at(P, past, obj, heads, sc)
    # an agent registered, whatever scope it was admitted under, is in no count either (the one recognition)
    return out | registered_agents(P)


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
            k = w["signer"]
            if seated_after(P, past, obj, k, w, lambda m: m["scope"] == scope): continue
            out.add(k)
    return frozenset(out)


def stay_ended_in_past(P, past, obj):
    """The keys whose own end of a stay as a member of obj is among P (a counted row's past) with no admission of the
    key after it there: a count over the duty holders that has such an end in its past does not count that key, since
    the end ended its duty seats. The counted removal needs no such reading: it is a head, read by members_at."""
    if "leaving_unread" in MUT or "resign_keeps_duty" in MUT: return frozenset()
    by = {q["id"]: q for q in P}
    if not community(by, obj): return frozenset()
    return frozenset(k for w, k, g in stay_ends(P, by, lambda a, w: a["id"] in by and past(a["id"], w["id"]))
                     if g == obj and not seated_after(P, past, obj, k, w, roster_seat))


def count_left(P, past, obj, scope):
    """The keys a count over `scope` at obj leaves out for a leaving in its row's past: the leaving of that seat, and for
    a count over duty holders, the end of the key's stay as a member. A count over another scope is as it was."""
    out = left_in_past(P, obj, scope, past)
    by = {q["id"]: q for q in P}
    # a family's founder role ends with any leaving of the key (its member seat, or the founding row) in the row's
    # past, whatever head that row names (MUTATION founder_role_survives_leave)
    role = ((scope == "founder" and kind_of(by, obj) == "family") or (scope == OFFICER and kind_of(by, obj) == "affiliation")) \
        and "founder_role_survives_leave" not in MUT
    return out | stay_ended_in_past(P, past, obj) if is_duty(scope, declared(by, obj)) or role else out


def owner_bindings(S, k, o):
    """The owner-bindings of key k in row o's past, as made (MUTATION agent_owner_end_unread: an end of a binding not
    read): (owner, binding row) for every offer of scope `owner` over k in o's past."""
    return {(w, q["id"]) for q in S.Cs if q["kind"] == "offer" and q.get("scope") == "owner" and q.get("obj") == k
            and q["id"] in S.anc[o["id"]] for w in q["to"]}


def newest_changes(P, past, obj, by):
    """The newest counted changes over obj among P (a row's concluded past), or obj's founding row where there is
    none: the heads a row naming none is read at."""
    chs = [q for q in P if change(q, obj, by)]
    return tuple(q["id"] for q in chs if not any(q is not q2 and past(q["id"], q2["id"]) for q2 in chs)) or (obj,)


def is_founder(S, key, obj, at_row):
    """Whether key is a founder of obj at row `at_row` (an id or a row of S), for a family or an infrastructure
    community (False for any other object): by the reading a count uses, over the row's own concluded past. The
    `founder` seats over obj at the heads the row names, or, for a row naming none, at the newest counted changes
    over obj in its past (the founding row where there is none); persons only. members_at reads every withdrawal in
    the row's past with the heads, so a key whose own leaving is there is no founder, and a family's founder role,
    which stands on the member seat, ends with any leaving of it (count_left's subtraction finds nothing more here).
    The founding row itself has no past: no founder at it. MUTATIONS founder_at_tips (read at the tips of everything
    held, not at the row) and founder_leavings_unread (the withdrawals of the row's past not read)."""
    r = S.by[at_row] if isinstance(at_row, str) else at_row
    if "founder_at_tips" in MUT:
        return kind_of(S.by, obj) in ("family", "infrastructure") and key in Seats(S).holders("founder", obj)
    P = [q for q in S.Cs if q["id"] in S.anc[r["id"]]]
    past = lambda a, b: a in S.anc[b]
    by = {q["id"]: q for q in P}
    if kind_of(by, obj) not in ("family", "infrastructure"): return False
    # read at the newest counted changes in the row's own past, never at the heads it states: a stale head is read
    # past, as newer_head_in_past refuses it for a count (MUTATION founder_raw_head)
    heads = (tuple(r.get("head", ())) if "founder_raw_head" in MUT else ()) or newest_changes(P, past, obj, by)
    unread = "founder_leavings_unread" in MUT and "ends_at_heads_unread" not in MUT
    if unread: MUT.add("ends_at_heads_unread")
    try:
        founders = counted_keys(P, past, obj, heads, "founder")[0]
    finally:
        if unread: MUT.discard("ends_at_heads_unread")
    return key in founders


def voices(r, P, past=None):
    """The keys that signed r: its signer, its cosigners, and the signers of the cosign rows it names that themselves
    name every head r is counted over. (A cosign row counts only where r names it, so r's own past holds the cosign's:
    a cosign whose past holds a newer counted head than r names leaves r itself with that head in its past, and r then
    concludes nothing by newer_head_in_past. No separate reading of the cosign's past is needed.)"""
    heads = set(r.get("head", ()))
    v = signers(r) | frozenset(c["signer"] for c in K.sel(P, kind="cosign", of=r.get("content", r["id"]))
                               if c["id"] in r["names"] and heads <= set(c["names"]))
    return v


def newest(heads, past):
    """The newest of the heads named: a head in the past of another named head is not a head of the count
    (MUTATION all_heads_read: every named head read). Several concurrent newest heads (tips) stay, intersected."""
    hs = tuple(dict.fromkeys(heads))
    if "all_heads_read" in MUT: return hs
    return tuple(h for h in hs if not any(h != o and past(h, o) for o in hs))


def authored_head(r):
    """A head one key wrote: an outsider's own admission to an open room (`open:self_admit`, signed by the key it
    seats). It narrows no count but by its own signer."""
    return r["kind"] == "offer" and K.rule(POLICY, r.get("policy"), ("unknown",))[0] == "self_admit" \
        and len(r["to"]) == 1 and r["to"][0] == r["signer"]


def count_heads(heads, P, past):
    """The heads a count is read over (seat.rs counted_heads): the newest of the heads named. An authored head is
    no head a count may name (H3): it is not read through, and newer_head_in_past refuses a count naming one."""
    return newest(heads, past)


def landed_change(q, obj, by):
    """A self roster's landed lone-path window over obj is a counted change of it, as the counted eviction or addition
    it is (a head a later count names, H1): a landing that says `landed` of a self_roster_evict or self_roster_add
    opener over obj (MUTATION landed_eviction_unread)."""
    if "landed_eviction_unread" in MUT or q["kind"] != "landing" or q.get("says") != "landed": return False
    p = by.get(q.get("of"))
    return p is not None and p.get("window") in ("self_roster_evict", "self_roster_add") and p.get("obj") == obj


def change(q, obj, by=None):
    """A counted change of obj's roster, q concluded: a roster-changing row that concludes under the policy the room's
    record binds to its act, however many voices that policy needs (the ruling of 2026-11-26). The line's counted act
    (checkpoint.is_counted_act), not an authored row under a policy it states itself (a self-admission with the binding
    off, H3: no head a count may name; MUTATION authored_heads: it is one); and a duty holder's own conferral of a
    duty over the room (an offer `self` or `seat`, the lone holder's: it concludes on one voice; MUTATION
    own_conferral_no_change: it is none)."""
    if CP.is_counted_act(q, obj):
        return "authored_heads" in MUT or not authored_head(q) or (BOUND and "binding_off" not in MUT)
    return by is not None and own_conferral(q, obj, by) and "own_conferral_no_change" not in MUT


def own_conferral(q, obj, by):
    """A one-key conferral of a duty over room obj (a community, `by` holding its founding row): an offer of conf
    `self` or `seat` over obj, not its founding row, of a duty scope (an own offer of any other scope is no counted
    change)."""
    return q["kind"] == "offer" and q.get("conf") in ("self", "seat") and q.get("obj") == obj and q["id"] != obj \
        and q.get("scope") not in ROSTER_SEATS and community(by, obj) and is_duty(q.get("scope"), declared(by, obj))


def honest(rows, ids=None):
    """Cases' helper: the rows with each counted row of `ids` (every counted row, an election's seating apart, where
    `ids` is None) written at the newest counted changes over its object in its own past (H1), naming them: what a
    signer that holds its own past writes. Its past is what it names, read through the rows given."""
    by = {r["id"]: r for r in rows}
    anc = {}
    def up(i):
        if i not in anc:
            anc[i] = set()
            for n in (by[i]["names"] if i in by else ()):
                anc[i] |= {n} | up(n)
        return anc[i]
    def newest_in(r, obj):
        past = [by[i] for i in up(r["id"]) if i in by]
        ch = [q for q in past if change(q, obj, by)]
        return tuple(sorted(q["id"] for q in ch if not any(q["id"] in up(o["id"]) for o in ch)))
    out = []
    for r in rows:
        if ids is None or r["id"] in ids:
            if r["kind"] in ("offer", "unseat") and r.get("conf") == "group" and r.get("head"):
                hs = newest_in(r, r["obj"]) or (r["obj"],)
                r = dict(r, head=hs, names=tuple(dict.fromkeys(tuple(r["names"]) + hs)))
            elif r["kind"] == "withdraw" and by.get(r["target"], {}).get("kind") in ("offer", "accept"):
                room = CP.object_of(by[r["target"]], by)
                if room is not None:                   # a seat's end names the newest counted changes over its room (H4)
                    r = dict(r, names=tuple(dict.fromkeys(tuple(r["names"]) + newest_in(r, room))))
            by[r["id"]] = r
        out.append(r)
    return out


def newer_head_in_past(heads, of, P, past, obj, keys=frozenset()):
    """Whether the newest heads named are not the newest counted changes over obj in the row's own past (H1): a
    counted change over obj (`change`) among P, in the past of row `of` (every row of P where `of` is None), that is
    neither one of them nor in the past of one, nor behind an acknowledgement by one of `keys` (H7); or one of them
    that is neither such a counted change nor obj's founding row (H3, H8: no other row is a head of a count)."""
    if "count_heads_unread" in MUT: return False
    # the named heads are an antichain: a named head in another named head's past is refused, not dropped (MUTATION
    # heads_not_antichain: it is dropped, and the count read at the newest)
    if "heads_not_antichain" not in MUT and any(h != o and past(h, o) for h in heads for o in heads): return True
    void = _VOID[-1] | _RVOID[-1]
    hs = tuple(h for h in newest(heads, past) if h not in void)
    by = {q["id"]: q for q in P}
    # MUTATION head_any_row: a named head may be any row
    if "head_any_row" not in MUT and any(h != obj and not (h in by and (change(by[h], obj, by) or landed_change(by[h], obj, by)))
                                        for h in hs):
        return True
    # MUTATION changes_any_object: a counted change of any object moves the head; past_disjunct_off: a change behind a
    # named head moves it too
    of_obj = (lambda q: CP.is_counted_act(q, q.get("obj"))) if "changes_any_object" in MUT else \
        (lambda q: change(q, obj, by) or landed_change(q, obj, by))
    behind = (lambda q: False) if "past_disjunct_off" in MUT else (lambda q: any(past(q["id"], h) for h in hs))
    return any(of_obj(q) and (of is None or past(q["id"], of)) and q["id"] not in hs and not behind(q)
               and q["id"] not in void for q in P)




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
        if q["kind"] != "unseat" or q.get("obj") != obj or k not in q["to"]: continue
        # a room key is one presence in one room: an ended stay in any roster seat bars every roster seat of it (F1;
        # MUTATION end_scope_bound: only the same scope)
        if (q.get("scope") != sc) if "end_scope_bound" in MUT else seat_class(q, q.get("scope")) is None: continue
        Pq = [x for x in P if past(x["id"], q["id"])]
        if "ended_unread" not in MUT and not seated_before(Pq, k, obj, q["scope"]): continue   # it ended no seat of k's (MUTATION ended_unread)
        # every roster unseat over a community that concludes is counted (RK2), so only a lone removal is not final
        if "lone_final" in MUT or count_met(q, Pq, past):   # MUTATION lone_final: a lone removal is final
            return True
    if "second_row_refused" in MUT and any(m["kind"] == "offer" and m.get("obj") == obj and k in m["to"] and m["id"] != obj
                                           for m in P):
        return True                                               # MUTATION: a second seat row of a seated key is refused
    if "resign_not_final" in MUT: return False                   # MUTATION: a resignation is no end of the seat
    return any(k2 == k and g == obj for _, k2, g in stay_ends(P, by, lambda a, w: a["id"] in by and past(a["id"], w["id"])))


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
        # a scope that holds a roster seat is read as one (F2; MUTATION roster_by_name: only member and agent by name)
        presence = r["scope"] in ROSTER_SEATS if "roster_by_name" in MUT else seat_class(r, r["scope"]) is not None
        if not presence:
            return any(q["kind"] == "unseat" and q["scope"] in FINAL and set(q["cuts"]) & set(r.get("on", ())) for q in P)
        obj, seats = r["obj"], [(k, r["scope"]) for k in r["to"]]
    if "room_key_unread" in MUT or not private_room(by, obj): return False     # MUTATION: room-key finality unread
    each = all if "batch_by_key" in MUT else any                 # MUTATION batch_by_key: one barred key does not bar the batch
    return each(seat_class(o if r["kind"] == "accept" else r, sc) in FINAL and room_key_ended(k, sc, obj, P, past, by)
                for k, sc in seats)


def roster_placement(r, by):
    """Over a group (an object that is its own founding row) a member or agent seat (seat_class not None) is placed or
    removed only by a counted row, the founding record, the key's own end, or (an agent's key) a moderator's lone
    removal, itself a counted row (CC 3.1.3.2, CC 4.5.13, derived on CIRISConstitution#224, RK2): a one key's own row
    (`self`) or a row under a seat (`seat`) of such a seat concludes nothing. A roster seat needs the key's own consent
    under every protocol (RK1): no flag on a row waives it (the Seats walk asks each key's acceptance, a node's seat
    over an infrastructure community alone excepted, by its scope and the kind). Whether a counted row meets the room's
    declared protocol is the binding's read (`act_of`), not this one."""
    obj = r.get("obj")
    if not community(by, obj) or seat_class(r, r.get("scope")) is None: return True
    if r.get("conf") in ("self", "seat") and "own_roster_row" not in MUT: return False   # MUTATION own_roster_row: RK2 unread
    return True


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
    sole = Seats(CK.State(P, {q["id"]: True for q in P}), roster=False)
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


def duty_gate(r, by, table=None):
    """CC 4.5.4: a duty seat is placed only by the founding record, by "the duty holders of C, counted under line
    (iv)", or by "the members' count under line (v)", which "is the election of rule 2". So a counted offer of a duty
    scope over a community concludes only where it is the duty holders' count, or is an election's acceptance (the
    ranked tally). The duty holders' count is the count over all the duty holders of the room it confers in:
    `counted` the duty holders' scope itself (`duty`; one duty's holders are not all of them), under the duty policy
    `duty_confer` (a strict majority of the holders, never fewer than two unless one; a policy the row states
    otherwise, `accord_halt` say, is not that count),. (A count over another room, `over`, concludes nothing for any count: H2.) A members'
    count under an admission-style policy confers no duty, whether or not a duty holder lives (CIRISConstitution#241).
    A seat that makes its holder no duty holder (a node's detector seat) is not reached. (MUTATIONS duty_gate_off;
    duty_gate_wrong_row: `counted` read off the room; gate_counted_any_duty: one duty's holders pass.)"""
    if "duty_gate_off" in MUT or not community(by, r["obj"]) or not is_duty(r["scope"], declared(by, r["obj"])): return True
    # the gate reads the policy in force (the acts table's, where it binds: a fixed act's row may state none)
    pol = policy_in_force(r, by) if "gate_reads_stated" not in MUT else r.get("policy")
    if pol is REFUSED: return False
    r = dict(r, policy=pol)
    if K.rule(table or POLICY, r.get("policy"), ("unknown",))[0] == "ranked": return True
    src = by.get(r["obj"], {}) if "duty_gate_wrong_row" in MUT else r
    counted = src.get("counted", "member")
    if not (counted == "duty" or ("gate_counted_any_duty" in MUT and is_duty(counted, declared(by, r["obj"])))): return False
    # a law with the acts table refuses every other policy first (policy_in_force); with none, the gate does
    return r.get("policy") == "duty_confer"


def still_met(r, P, past, voices_out):
    """Counted row r's count is still met over P with the voices `voices_out` taken out: the one re-count for a voice
    a concurrent end or removal discounts (contested_out here; trust_rows' discounted voice of an ended key). It reads
    the seat model's voices path (voices, the persons counted, the agents apart)."""
    return count_met(dict(r, void_voices=frozenset(voices_out)), P, past)


def count_met(r, P, past, table=None):
    """A counted row's count (conf=group), met over its concluded ancestors P: the lift, the ranked tally, the duty
    count, or the policy's threshold over the persons at the heads it names."""
    by = {q["id"]: q for q in P}
    f = in_force(r, by)
    if f is REFUSED: return False                    # its act may not take the policy it states (the acts table)
    if "all" in f:                                   # policies joined by `&`: every one met (Q1)
        got = [_count_under(dict(r, **g), P, past, by, table) for g in f["all"]]
        return any(got) if f["any"] else all(got)
    return _count_under(dict(r, **f), P, past, by, table)


def _count_under(r, P, past, by, table=None):
    """count_met's count, r carrying the policy in force (in_force) in place of the one it states."""
    k, heads = r["kind"], r.get("head", ())
    # the lift is told by its act where the object has a kind (act_of), by its policy otherwise
    a = act_of(r, by, r.get("obj") is not None and r.get("obj") not in by) if BOUND else None
    if (a[0] == "lift" if a is not None else K.rule(table or POLICY, r.get("policy"), ("unknown",))[0] == "lift"):
        return lift_count(r, P, past, by)
    # H2: a counted row is counted over its own object (MUTATION over_read: over `over`, the field before 0.5.0)
    obj = r.get("over", r["obj"]) if "over_read" in MUT else r["obj"]
    mem, vot = counted_keys(P, past, obj, heads, r.get("counted", "member"))
    left = count_left(P, past, obj, r.get("counted", "member"))
    mem, vot = mem - left, vot - left
    vot = vot - r.get("void_voices", frozenset())    # voices voided by a concurrent counted removal (contested_out)
    if r.get("infra_mn") is not None:
        m, n = r["infra_mn"]
        # CC 2.7.8's wait for founders' amendments: two concurrent ones are concurrent versions of the record. Until a
        # version names both (and restates the word for the founders it leaves), no founders' count concludes over a
        # past holding both; that version is itself a founders' amendment, counted at the present M over the founders
        # common to the two (the founders at its heads) and signed by every key the two seated
        versions = [q for q in P if q["kind"] == "offer" and q.get("conf") == "group" and q.get("obj") == r["obj"]
                    and q.get("scope") == "record"]
        seating = [q for q in versions if q.get("role") == "founder" and q.get("to")]
        pairs = [(a, b) for i, a in enumerate(seating) for b in seating[i + 1:]
                 if not past(a["id"], b["id"]) and not past(b["id"], a["id"])
                 and not any(past(a["id"], q["id"]) and past(b["id"], q["id"]) for q in versions)]
        if pairs and "concurrent_amendments_free" not in MUT:
            if r.get("scope") != "record": return False
            pair_keys = frozenset(k for a, b in pairs for q in (a, b) for k in q["to"])
            if not pair_keys <= voices(r, P): return False
            mem, vot = mem - pair_keys, vot - pair_keys
            union = mem | pair_keys
            pr = infrastructure_rule(r.get("consensus_protocol")) if r.get("consensus_protocol") else None
            new_r = frozenset(r.get("to", ())) - union if k == "offer" else frozenset()
            if pr is None or pr[2] != len(union) + len(new_r) or pr[1] < m: return False
            if not new_r <= voices(r, P): return False
            b, y = count_persons(P, obj, mem, voices(r, P), vot)
            return met("P:quorum", len(y), len(b), m)
        # C2 (the ruling on reader_state): for a reader holding two concurrent founders' amendments, a founders' count
        # whose own past holds only one of them reads the founders common to the two: neither line's later count is
        # counted over the keys one line alone seated (MUTATION wait_reader_unread: read over its own past only)
        if "wait_reader_unread" not in MUT:
            ids = {q["id"] for q in P}
            held = frozenset(k for a, b, ks, o in _RPAIRS[-1] if o == r["obj"] and ((a in ids) != (b in ids)) for k in ks)
            if held: mem, vot = mem - held, vot - held
        if "infra_m_recomputed" in MUT: r = dict(r, need=len(mem) // 2 + 1)   # MUTATION: M computed from the founders
        # stalled (fewer than M + 1 active founders): the founders' count admits and removes nothing
        if r.get("scope") != "record" and len(mem) < m + 1 and "infra_stalled_admits" not in MUT: return False
        new = frozenset(r.get("to", ())) - mem if k == "offer" else frozenset()
        if r.get("scope") == "record":
            # a founders' amendment: it seats its new keys, signed by each, and is a widening by the founders' count,
            # so a stalled room makes none
            if not new <= voices(r, P): return False
            if new and len(mem) < m + 1 and "infra_stalled_admits" not in MUT: return False
            # the word (the Constitution's narrowing): a version leaving the founders at or below the word's N keeps it
            # (counted at the present M); one leaving more must name a new word, N the founders it leaves and M its
            # strict majority. No version names a word whose M is below the present M, or is not its N's strict
            # majority; a new word other than the one in force states the founders the version leaves
            n_after = len(mem) + len(new)
            w = r.get("consensus_protocol")
            pr = infrastructure_rule(w) if w is not None else None
            if w is not None and pr is None: return False
            unchanged = pr is None or (pr[1], pr[2]) == (m, n)
            if "infra_word_restated_always" in MUT and new and unchanged: return False   # MUTATION
            if unchanged and n_after > n: return False             # above N, the version names a new word
            if not unchanged:
                if pr[1] < m and "infra_m_lowered" not in MUT: return False
                if pr[2] != n_after and "infra_word_n_free" not in MUT: return False
    if r.get("founders_fixed"):                      # MUTATION family_founders_fixed: the founding row's founders only
        g = by.get(r["obj"]) or {}
        mem = vot = frozenset(k for d, ks in (g.get("duty_holders") or ()) if d == "founder" for k in ks) & signers(g)
    # a family under founder_only: a removal takes an active founder other than the one it names
    if r.get("exclude_target"): vot = vot - frozenset(r.get("to", ()))
    # an eviction from a self roster: the key evicted is no voice of it (no key keeps itself in by its own signature;
    # a roster whose only live key is the one evicted cannot evict it: the one-key residual) (MUTATION
    # evicted_key_votes)
    if k == "unseat" and r.get("policy") == "self_roster_evict" and "evicted_key_votes" not in MUT:
        vot = vot - frozenset(r.get("to", ()))
    if r.get("base_excludes_target"):
        mem, vot = mem - frozenset(r.get("to", ())), vot - frozenset(r.get("to", ()))
    # one member per person, as one voice (ruled on CIRISConstitution#224): the base counted by person (as_persons)
    key_mem = mem
    mem, yes = count_persons(P, obj, key_mem, voices(r, P), vot)
    # a family's removal naming only its own signer, on that signature alone, concludes nothing (F3)
    if r.get("no_self_removal") and voices(r, P) - r.get("void_voices", frozenset()) <= frozenset(r.get("to", ())):
        return False
    # the community floor, where a policy row governs alone in place of a protocol that states no rule (the `&` reading)
    if r.get("floor") is not None and len(yes - frozenset(r.get("to", ()))) < r["floor"]: return False
    if K.rule(table or POLICY, r.get("policy"), ("unknown",))[0] == "ranked":
        # the election's seating (C1 to C5): its electorate read at its election's vacancy, not at a head
        return election_count(r, P, past, by)
    if r.get("policy") in DUTY_POLICY: return duty_count(r, P, yes, mem)
    # the recall is told by its act where the binding reads one (act_of: an unseat of a duty counted over the
    # members), by its policy otherwise; Policy::Recall is only the threshold its fixed row maps to
    is_recall = (a[0] == "recall") if a is not None else \
        K.rule(table or POLICY, r.get("policy"), ("unknown",))[0] == "recall"
    if k == "unseat" and is_recall and "recall_as_strictfloor" not in MUT:
        # the recall judges one holder: counted over the members less the holder it recalls, and that holder no voice
        # of it, as the lift is counted over the room less the one it judges
        judged = frozenset(r["to"])
        base, yes_j = count_persons(P, obj, key_mem, voices(r, P), vot, apart=judged)
        if "recall_holder_in_base" in MUT: base = mem
        if "recall_holder_voice" in MUT: yes_j = yes
        yes = yes_j
        return met(r.get("policy"), len(yes), len(base), r.get("need"), table)
    return count_of(r.get("policy"), k == "offer", r.get("to", ()), mem, yes, r.get("need"),
                    r.get("weights"), table, signed=voices(r, P))


def ends_of(r, by):
    """The seats (key, scope, object) row r ends: an unseat, each key it names in its scope; a withdrawal, of the seat
    its target gives (its signer's own where it holds it, else every key the target seats), in end_scope's scope.
    A removal of an agent's key is none here: a lone one may be lifted or fall out of force, and then it ended nothing."""
    if r["kind"] == "unseat":
        return () if r["scope"] == AGENT else tuple((k, r["scope"], r["obj"]) for k in r["to"])
    if r["kind"] != "withdraw": return ()
    t = by.get(r.get("target"))
    if t is None: return ()
    sc = end_scope(by, r)
    if t["kind"] == "accept":
        o = by.get(t["of"]) if t.get("of") is not None else t
        return ((r["signer"], sc, o.get("obj")),) if o is not None and t["signer"] == r["signer"] else ()
    if t["kind"] != "offer": return ()
    return tuple((k, sc, t["obj"]) for k in ((r["signer"],) if r["signer"] in t["to"] else t["to"]))


def end_of_ended(r, P, past, by):
    """(2): an end of a seat that has an end of that seat in its own past is no end, whoever signed either: a lay-down,
    a counted unseat, a withdrawal of the offer. Every seat r ends has a concluded end in r's past with no seating of
    the key in that scope after it there (MUTATION end_of_ended_seat; end_reseat_unread: a re-seating not read, so a
    re-admitted key's second leaving ends nothing)."""
    seats = ends_of(r, by)
    if not seats or "end_of_ended_seat" in MUT: return False
    # only an end IN FORCE is an earlier end: a counted removal rule 5 holds contested out (or a lone removal out of
    # force) ended nothing, and leaves the seat to a later end (the ruling on S4; MUTATION end_of_contested_end)
    out = []
    def in_force(q):
        if q["kind"] != "unseat" or "end_of_contested_end" in MUT: return True
        if not out: out.append(seats_of(P).dropped)
        return q["id"] not in out[0]
    return all(any((k, sc, o) in ends_of(q, by) and ("end_reseat_unread" in MUT or not seated_after(
        P, past, o, k, q, lambda m: sc in seat_scopes(m, k))) and in_force(q) for q in P) for k, sc, o in seats)


def seat_rule(r, P, past, table=None, other=None):
    """The conclusion rule. P: r's concluded ancestors."""
    k, by = r["kind"], {q["id"]: q for q in P}
    # a rival founding concludes nothing for the reader whose line took up another of the identity's, and neither does
    # everything built on it (a row over it, or accepting or withdrawing one over it) (reader_rivals)
    if _RRIVAL[-1] and rival_row(r, by, _RRIVAL[-1]): return False
    if k in ("unseat", "withdraw") and end_of_ended(r, P, past, by): return False   # (2): no second end of a seat
    if k in ("offer", "unseat"):
        conf = r["conf"]
        # after a group's dissolution no row over it concludes (group_dissolved)
        if r.get("obj") != r["id"] and dissolved_in(P, r.get("obj")): return False
        # a dissolution is counted at the newest heads in its own past: every counted row over the group there is a
        # head or in a head's past
        if is_dissolve(r) and "dissolve_any_heads" not in MUT and any(
                q.get("conf") == "group" and q.get("obj") == r["obj"] and q["kind"] in ("offer", "unseat")
                and q["id"] not in r.get("head", ()) and not any(past(q["id"], h) for h in r.get("head", ())) for q in P):
            return False
        if k == "offer" and _revoked_before(r, P, past): return False   # a revoked key does not re-seat itself (FINAL)
        # a single key's own offer of a duty (or one under its seat) concludes only where that key is the lone person
        # duty holder: "by a strict majority of the duty holders, or by the lone holder with the new holder's
        # acceptance" (CC 4.5.4), in every community (CIRISConstitution#241; MUTATION own_duty_ungated: duty rooms only)
        if k == "offer" and conf in ("self", "seat", "root") and r["obj"] != r["id"] and not authority_gate(r, P, by):
            return False
        # H2: a counted row is counted over its own object; one stating another (`over`) concludes nothing (MUTATION
        # over_allowed). Its heads are its own object's counted changes (H1, newer_head_in_past), so a head of another
        # object's line is refused there
        if conf == "group" and r.get("over", r["obj"]) != r["obj"] and "over_allowed" not in MUT: return False
        if r["obj"] != r["id"] and not roster_placement(r, by): return False   # RK1, RK2: who places a roster seat
        if k == "offer" and conf == "group" and not duty_gate(r, by): return False   # CC 4.5.4: who places a duty
        if conf == "root":
            return k == "offer"                              # read by the one gate (authority_gate: root_seat_rule)
        if conf == "self":
            if r["obj"] == r["id"]:                              # a founding row is its own object
                # one self roster per identity (G1, ruled): a second founding of a self roster by an identity whose
                # roster is in the row's past is a rival founding and concludes nothing; no key re-founds itself, or
                # adds a device, by founding (MUTATION rival_roster_kept)
                if k == "offer" and is_self_founding(r) and "rival_roster_kept" not in MUT and any(
                        is_self_founding(q) and q["signer"] == r["signer"] for q in P): return False
                return k == "offer"
            # over infrastructure a founder seat comes only by a founders' amendment: an own offer of one seats nothing
            if r.get("scope") == "founder" and kind_of(by, r["obj"]) == "infrastructure" and "role_on_own_offer" not in MUT:
                return False
            if k == "unseat" and founding_many(by, r["obj"]): return False    # among several founding keys, ending a seat takes the count
            return r["signer"] in own_keys(by, r["obj"])
        if conf == "seat":
            if k == "unseat": return _ender(r, P, by)
            return k == "offer" and r.get("under") in by and r["signer"] in by[r["under"]]["to"]
        if conf == "group":
            # an infrastructure room's recovery widening while stalled: judged against the trust root this node reads
            # (recovery_verdict); with none read, undecided (stalled_recovery), and it concludes nothing
            if r.get("bundle") is not None:
                return ROOT[-1] is not None and recovery_verdict(r, P, past)[0]
            # H1, H4: every counted row names the newest counted changes over its object in its own past, a lone removal,
            # a self-admission, a lift and an election's seating included (a seating's count reads its election, never
            # its heads: its heads place it; MUTATION election_exempt: a seating names no head)
            # (MUTATION lone_exempt: a lone removal read before the rule, as before 0.5.0)
            # (the prototype: the row's signers' lines void, for it, the changes behind them)
            _VOID.append(void_changes(r, P))
            try:
                if not ("election_exempt" in MUT and is_election(r)) \
                        and not ("lone_exempt" in MUT and k == "unseat" and lone_removal(r, P, past)) \
                        and newer_head_in_past(r.get("head", ()), None, P, past, r["obj"], signers(r)): return False
                if k == "unseat" and lone_removal(r, P, past): return True          # CC 4.5.13: a moderator, an agent's key
                if affiliation_removal(r, by):                # CC 4.4.3.12: the body's signature, its seats' floor
                    f = in_force(r, by)
                    return f is not REFUSED and affiliation_count(r, P, past)
                return count_met(r, P, past, table)
            finally:
                _VOID.pop()
        return False
    if k == "accept":
        if _revoked_before(r, P, past): return False           # a room key whose seat's end stands is not seated again (FINAL)
        o = by.get(r.get("of"))
        if dissolved_in(P, o.get("obj") if o is not None else r.get("obj")): return False   # group_dissolved
        return r["of"] is None or (r["of"] in by and r["signer"] in by[r["of"]].get("to", ()))
    if k == "withdraw":
        t = by.get(r["target"])
        # MUTATION family_last_founder_refused: a family's last active founder may not leave (no such rule: a
        # resignation is never refused for leaving the group without a founder)
        if "family_last_founder_refused" in MUT and t is not None and kind_of(by, t.get("obj")) == "family" and \
                seats_of(P).holders("founder", t["obj"]) == frozenset((r["signer"],)):
            return False
        if t is None or not (r["signer"] in signers(t) or (t["kind"] == "offer" and r["signer"] in t["to"])): return False
        # H4: a withdrawal of a seat over a community (a resignation, a laying down) names the newest counted changes
        # over the room in its own past among the rows it names (MUTATION resign_exempt: it need not)
        room = CP.object_of(t, by) if t["kind"] in ("offer", "accept") else None     # a seat's end, not a ballot's
        if room is not None and room in by and community(by, room) and "resign_exempt" not in MUT:
            # (the rows a withdrawal names are no declared heads: the newest of them are read, as a count's heads)
            named = newest(tuple(n for n in r["names"] if n == room or (n in by and change(by[n], room, by))), past)
            if newer_head_in_past(named, None, P, past, room, signers(r)): return False
        return True
    if k == "cosign":
        return True
    if family(r) in LONE_ACTS:
        return lone_act_rule(r, P, past)
    if family(r) == "reconsideration":
        return reconsideration_rule(r, P, past)
    if k == CONFIRMED:
        return confirmation_rule(r, P, past)
    return other(r, P, past) if other else True
