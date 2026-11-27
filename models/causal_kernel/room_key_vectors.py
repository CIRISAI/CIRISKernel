#!/usr/bin/env python3
"""
room_key_vectors.py: the door of a private room's row, as vectors for a verifier (CIRISConstitution#224, CC 3.1.3.2).

The check a verifier builds first is pure. Given a row of the room, the key records it holds and the caller's roster
view at the head the row names, it answers:
    1. the signer is a room key at all: its key record names a room. A row of a private room signed under an identity
       key or a node key is refused, `room_row_signer_not_room_key`.
    2. the signer's key record names this room. A row of another room signed under a room key is refused,
       `room_key_other_room`.
    3. the row names the head of the voice's key roster under the `refs.also` role `voice`, exactly one row. A row
       naming none, or several, is malformed and refused, `room_row_voice_head_malformed` (CC 2.7.3; ruled on #224).
    4. the room key is a live key of the voice at that head. "A row concludes only if the room key that signed it is a
       live key of the voice at that head." The text names no refusal: such a row concludes nothing (`refusal` null).
The order 1, 2, 3, 4 is the check's (the Constitution states it; no case here meets two). A public room seats
identity keys and the check is not engaged.

The roster fold stays the kernel's: `view` is the voice's live room keys at the head the row names, computed by
seat.members_at over the voice's roster rows (roomkey.py: a voice is a small counted roster of room keys, scope
`key`, over the voice). Each case's `kernel` field records the kernel's own reading of check 4 (roomkey.rule's
device clause), which must equal the verdict's.

    python3 -I room_key_vectors.py      prints the cases; exit 1 if the reference check and the kernel disagree
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import roomkey as RK  # noqa: E402

ST, CK, RT, R = RK.ST, RK.CK, RK.RT, RK.R
ROOM, OTHER = RK.ROOM, "g2"
LEDGER = "CIRISConstitution#224: a room row's signer and its voice (CC 3.1.3.2)"
NODE_LEDGER = "CIRISConstitution#224: a node's row in a private room (ruled)"

# the voices of the room: vA with three device keys, the second and third added by the voice's own count; vB with one
DEVS_A = ("rk:a0", "rk:a1", "rk:a2")
VA, HA = RK.voice_rows("vA", list(DEVS_A))
VB, HB = RK.voice_rows("vB", ["rk:b0"])
HA1 = "vA+1"                                                 # vA's roster head before its third key was added
# rk:a2 is evicted from vA by the voice's own count (a strict majority of its three keys)
EV = ST.unseat("ev", "rk:a0", "rk:a2", "key", "vA", "group", (HA,), head=(HA,), policy="self_roster_evict", counted="key",
               cosigners=("rk:a1",), room=ROOM)
ROSTER = VA + VB + [EV]

# the key records a caller holds: a room key's record names its one room; an identity key's and a node key's name none
RECORDS = {k: {"key": k, "room": ROOM, "identity_type": "person"} for k in DEVS_A + ("rk:b0",)}
RECORDS["rk:x0"] = {"key": "rk:x0", "room": OTHER, "identity_type": "person"}     # a room key of another room
RECORDS["rk:n0"] = {"key": "rk:n0", "room": ROOM, "identity_type": "person"}      # a room key no voice seats
RECORDS["id:A"] = {"key": "id:A", "room": None, "identity_type": "person"}        # an identity key
RECORDS["node:nA"] = {"key": "node:nA", "room": None, "identity_type": "node"}    # a node key
NODE, NODE2 = "rk:node", "rk:node2"
RECORDS[NODE] = {"key": NODE, "room": ROOM, "identity_type": "node"}             # a node's room key
RECORDS[NODE2] = {"key": NODE2, "room": ROOM, "identity_type": "node"}           # another node's room key
NODE_X, NODE_0 = "rk:nodex", "rk:node0"
RECORDS[NODE_X] = {"key": NODE_X, "room": OTHER, "identity_type": "node"}        # a node's room key of another room
# (NODE_0 has no key record at all)

# ---- a node's row (ruled on CIRISConstitution#224): the room, its voices, and the node's in-room owner-binding --------
VC, HC = RK.voice_rows("vC", ["rk:c0"])
GR = ST.offer("g", "vA", ("vA", "vB", "vC"), "member", "@", "self", cosigners=("vB", "vC"), membership="private",
              names=(HA, HB, HC))
OB = ST.offer("ob", NODE, "rk:a0", "owner", NODE, "self", ("g",), cosigners=("rk:a0",))      # rk:a0 (of vA) owns the node
OB2 = ST.offer("ob2", NODE, "rk:b0", "owner", NODE, "self", ("g",), cosigners=("rk:b0",))    # a second owner, rk:b0 (of vB)
OB3 = ST.offer("ob3", NODE, NODE2, "owner", NODE, "self", ("g",), cosigners=(NODE2,))       # a node's key owning the node
M1 = R("m1", "note", "vB", ("ob",))                                                           # a later row of the room
WOB_C = ST.withdraw("wob", "rk:a0", "ob", ("ob", "m1"))         # the owner ends the binding, at the head m1
EVO = ST.unseat("evo", "rk:a1", "rk:a0", "key", "vA", "group", (HA,), head=(HA,), policy="self_roster_evict",
                counted="key", cosigners=("rk:a2",))            # the owning key evicted from its voice
XV = ST.unseat("xv", "vB", "vA", "member", "g", "group", ("g",), head=("g",), policy="community_remove",
               cosigners=("vC",))                                # the room's count removes vA
AN2 = ST.offer("an2", "rk:a0", NODE2, "key", "vA", "group", (HA,), head=(HA,), policy="self_roster_add", counted="key",
               cosigners=("rk:a1", NODE2))                       # a node's room key seated in vA's own roster
VD, HD = RK.voice_rows("vD", ["rk:d0"])
AD = ST.offer("ad", "vB", "vD", "member", "g", "group", ("g", HD), head=("g",), policy="community_invite",
              cosigners=("vC", "vD"))                            # the room admits vD: a counted change after g
XV_OLD = ST.unseat("xvo", "vB", "vA", "member", "g", "group", ("g", "ad"), head=("g",), policy="community_remove",
                   cosigners=("vC",))                            # vA's removal naming the old head g, with ad in its past
# the review r74's rows (RV1 to RV4)
OBX = ST.offer("obx", NODE, "rk:b0", "owner", NODE, "self", ("g",))                       # rk:b0 never signed it
UO = ST.unseat("uo", "rk:a0", "rk:a0", "owner", NODE, "seat", ("ob",), under="ob")         # the owner revokes the binding
RECN = ST.offer("recn", NODE, NODE, "registered", NODE, "self", ("g",))
RVN = ST.unseat("rvn", NODE, NODE, "registered", NODE, "self", ("recn", "ob"))           # the node key revokes itself
OB2T = ST.offer("obt", NODE, ("rk:b0", "rk:a0"), "owner", NODE, "self", ("g",), cosigners=("rk:a0",))
RECA = ST.offer("reca", "rk:a0", "rk:a0", "registered", "rk:a0", "self", ("g",))
RVA = ST.unseat("rva", "rk:a0", "rk:a0", "registered", "rk:a0", "self", ("reca", "ob"))  # the owning key revokes itself
NODE_BASE = VA + VB + VC + [GR]


def node_row(i, under, voice_heads, cites=(), kid=NODE, iss=None):
    """A node's row as the wire states it: iss = kid = the node's room key; refs.also.under its owner-binding,
    refs.also.voice the owning voice's key-roster head."""
    return {"id": i, "kind": "detection", "room": ROOM, "iss": iss or kid, "kid": kid,
            "refs": {"also": {"under": list(under), "voice": list(voice_heads)}}, "cites": list(cites)}


def kernel_row(r):
    """The same row for the kernel: signed by the node's key, naming what it refers to."""
    also = r["refs"]["also"]
    return R(r["id"], r["kind"], r["kid"], tuple(dict.fromkeys(also.get("under", []) + also.get("voice", []) + r["cites"])),
             room=ROOM)


# (name, extra rows, row, verdict, refusal)
NODE_CASES = [
    ("a node's row under a live owner-binding, the owner live in its voice at the head named", [OB],
     node_row("n1", ["ob"], [HA]), "admitted", None),
    ("the binding withdrawn concurrently, the row before the withdrawal's head: it counts at its own head", [OB, M1, WOB_C],
     node_row("n2", ["ob"], [HA]), "admitted", None),
    ("the binding withdrawn concurrently, the row at the withdrawal's head: out of force from that head on",
     [OB, M1, WOB_C], node_row("n3", ["ob"], [HA], ("m1",)), "concludes_nothing", None),
    ("the binding withdrawn before the row (the withdrawal in its past)", [OB, M1, WOB_C],
     node_row("n4", ["ob"], [HA], ("wob",)), "concludes_nothing", None),
    ("two live owner-bindings of the node key in the row's past", [OB, OB2], node_row("n5", ["ob"], [HA], ("ob2",)),
     "concludes_nothing", None),
    ("the owning key evicted from its voice, the eviction in the row's past", [OB, EVO],
     node_row("n6", ["ob"], [HA], ("evo",)), "concludes_nothing", None),
    ("the owning voice removed from the room, the removal in the row's past", [OB, XV],
     node_row("n7", ["ob"], [HA], ("xv",)), "concludes_nothing", None),
    ("the owning voice's removal names an old head while a newer counted change is in its own past: the removal "
     "concludes nothing (H1), so the node's row stands", VD + [OB, AD, XV_OLD], node_row("n15", ["ob"], [HA], ("xvo",)),
     "admitted", None),
    ("a node owned by another node's room key, that key even seated in a voice (no chains)", [OB3, AN2],
     node_row("n8", ["ob3"], ["an2"]), "concludes_nothing", None),
    ("the owning key's eviction concurrent with the row, the row at its head: out of force from that head on", [OB, EVO],
     node_row("n13", ["ob"], [HA]), "concludes_nothing", None),
    ("the owning voice's removal concurrent with the row, the row at its head: out of force from that head on",
     [OB, XV], node_row("n14", ["ob"], [HA]), "concludes_nothing", None),
    ("the head named is another voice's, not the owner's", [OB], node_row("n9", ["ob"], [HB]), "concludes_nothing", None),
    ("RV1: a binding the owner never signed (the node's own offer of the owner seat to rk:b0) is no owner seat",
     [OBX], node_row("n16", ["obx"], [HB]), "concludes_nothing", None),
    ("RV4: a binding naming two owners, one of whom did not sign: none (each must sign for itself)", [OB2T],
     node_row("n17", ["obt"], [HA]), "concludes_nothing", None),
    ("RV4: the same, the row naming the other owner's voice head", [OB2T], node_row("n18", ["obt"], [HB]),
     "concludes_nothing", None),
    ("RV2: the owner revokes the owner seat (an unseat of it), the revocation in the row's past", [OB, UO],
     node_row("n19", ["ob"], [HA], ("uo",)), "concludes_nothing", None),
    ("RV2: the owner's revocation concurrent with the row, the row at its head: out of force from that head on",
     [OB, UO], node_row("n25", ["ob"], [HA]), "concludes_nothing", None),
    ("RV3: the node key revoked itself, in the row's past", [OB, RECN, RVN], node_row("n20", ["ob"], [HA], ("rvn",)),
     "concludes_nothing", None),
    ("RV3: the owning key revoked itself, in the row's past", [OB, RECA, RVA], node_row("n21", ["ob"], [HA], ("rva",)),
     "concludes_nothing", None),
    ("RV3: the node key's record names another room", [OB], node_row("n22", ["ob"], [HA], kid=NODE_X), "refused",
     "room_key_other_room"),
    ("RV3: the node key has no record", [OB], node_row("n23", ["ob"], [HA], kid=NODE_0), "refused",
     "room_row_signer_not_room_key"),
    ("RV3: iss names a voice, not the node key (a voice's row, and the node key no key of that voice)", [OB],
     node_row("n24", ["ob"], [HA], iss="vA"), "concludes_nothing", None),
    ("no owner-binding named", [OB], node_row("n10", [], [HA]), "refused", "room_row_owner_binding_malformed"),
    ("two owner-bindings named", [OB, OB2], node_row("n11", ["ob", "ob2"], [HA]), "refused",
     "room_row_owner_binding_malformed"),
    ("no voice head named", [OB], node_row("n12", ["ob"], []), "refused", "room_row_voice_head_malformed"),
]
NODE_PLANTS = ("node_rule4_unread", "node_binding_end_unread", "node_two_owners_kept", "node_owner_kind_unread",
               "node_owner_eviction_unread", "node_voice_removal_unread", "node_owner_seat_unread",
               "node_owner_revocation_unread", "node_key_end_unread", "node_record_unread")


def row(i, voice, kid, voice_refs, room=ROOM):
    """A row of the room as the wire states it: `iss` the voice, `kid` the key that signed, `refs.also.voice` the
    head(s) of the voice's key roster it names."""
    return {"id": i, "kind": "msg", "room": room, "iss": voice, "kid": kid, "refs": {"also": {"voice": list(voice_refs)}}}


# (name, membership, row, expected verdict, refusal)
CASES = [
    ("a room key live in its voice at the head named", "private", row("r1", "vA", "rk:a0", [HA]), "admitted", None),
    ("the voice's second key, added by the voice's count, at the head that adds it", "private",
     row("r2", "vA", "rk:a1", [HA1]), "admitted", None),
    ("the third key at the head that adds it", "private", row("r3", "vA", "rk:a2", [HA]), "admitted", None),
    ("the third key at a head before it was added: not a live key there", "private",
     row("r4", "vA", "rk:a2", [HA1]), "concludes_nothing", None),
    ("the third key at the head of its eviction: not a live key there", "private",
     row("r5", "vA", "rk:a2", ["ev"]), "concludes_nothing", None),
    ("a key of the voice still live after another key's eviction", "private", row("r6", "vA", "rk:a1", ["ev"]), "admitted", None),
    ("a room key of this room that no voice seats", "private", row("r7", "vA", "rk:n0", [HA]), "concludes_nothing", None),
    ("a key of another voice, presented as this voice's", "private", row("r8", "vA", "rk:b0", [HA]), "concludes_nothing", None),
    ("a voice head that is another voice's roster head", "private", row("r9", "vA", "rk:a0", [HB]), "concludes_nothing", None),
    ("the one key of a voice of one key", "private", row("r10", "vB", "rk:b0", [HB]), "admitted", None),
    ("no head of the voice's roster named", "private", row("r11", "vA", "rk:a0", []), "refused",
     "room_row_voice_head_malformed"),
    ("two heads named under `voice` (exactly one row)", "private", row("r12", "vA", "rk:a0", [HA, HA1]), "refused",
     "room_row_voice_head_malformed"),
    ("a room key whose record names another room", "private", row("r13", "vA", "rk:x0", [HA]), "refused", "room_key_other_room"),
    ("a row of the private room signed under an identity key", "private", row("r14", "vA", "id:A", [HA]), "refused",
     "room_row_signer_not_room_key"),
    ("a row of the private room signed under a node key", "private", row("r15", "vA", "node:nA", [HA]), "refused",
     "room_row_signer_not_room_key"),
    ("a public room: a row under an identity key, the check not engaged", "public", row("r16", "id:A", "id:A", []), "admitted", None),
]


def view_at(voice, heads):
    """The caller's roster view: the voice's live room keys at the head named, as the kernel folds them. With no head,
    or several, the voice names no one head and the view is empty."""
    if len(heads) != 1: return []
    S = CK.concluded(CK.kept(list(ROSTER)), RK.rule)
    past = lambda a, b: a in S.anc[b]
    if heads[0] not in S.C or not S.C[heads[0]]: return []
    return sorted(ST.members_at(S.Cs, past, voice, tuple(heads), "key"))


def check(membership, r, records, view):
    """The reference verdict, from the row, the records and the view alone: (verdict, refusal)."""
    if membership != "private": return "admitted", None
    rec = records.get(r["kid"])
    if rec is None or rec.get("room") is None: return "refused", "room_row_signer_not_room_key"
    if rec["room"] != r["room"]: return "refused", "room_key_other_room"
    heads = r["refs"]["also"]["voice"]
    if len(heads) != 1: return "refused", "room_row_voice_head_malformed"
    return ("admitted", None) if r["kid"] in view else ("concludes_nothing", None)


def kernel_reading(r):
    """The kernel's device clause (roomkey.rule): the signing key is among the voice's live keys at the head named."""
    heads = r["refs"]["also"]["voice"]
    if len(heads) != 1: return None
    return r["kid"] in view_at(r["iss"], heads)


def node_state(extra, r):
    rows = NODE_BASE + list(extra) + [kernel_row(r)]
    return CK.concluded(CK.kept(rows), lambda q, P, past: ST.seat_rule(q, P, past))


def node_verdict(extra, r):
    """A node's row: the facts the kernel folds over its rows, and the verdict the pure check gives from them."""
    f = RK.node_row_facts(node_state(extra, r), r, RECORDS)
    return f, RK.node_row_check(r, RECORDS, f)


def cases():
    out = []
    for name, membership, r, verdict, refusal in CASES:
        view = view_at(r["iss"], r["refs"]["also"]["voice"])
        out.append({"name": name, "ledger": LEDGER, "arm": "voice", "membership": membership, "room": ROOM, "row": r,
                    "records": [RECORDS[r["kid"]]] if r["kid"] in RECORDS else [],
                    "view": {"voice": r["iss"], "heads": r["refs"]["also"]["voice"], "live_keys": view},
                    "verdict": verdict, "refusal": refusal,
                    "kernel": kernel_reading(r) if membership == "private" else None})
    for name, extra, r, verdict, refusal in NODE_CASES:
        f, _ = node_verdict(extra, r)
        out.append({"name": name, "ledger": NODE_LEDGER, "arm": "node", "membership": "private", "room": ROOM, "row": r,
                    "rows": list(extra), "records": [RECORDS[k] for k in dict.fromkeys((r["kid"], f["owner"])) if k in RECORDS],
                    "view": f, "verdict": verdict, "refusal": refusal, "kernel": None})
    return out


def fixture():
    """The vector file: the voice rosters the views are folded from, the key records, and the cases."""
    return {"about": "CIRISConstitution#224, CC 3.1.3.2: a private room's row door (signer a room key, its record's room, "
                     "one voice head, a live key of the voice there); views folded by seat.members_at",
            "room": ROOM, "roster_rows": ROSTER, "node_rows": NODE_BASE,
            "records": sorted(RECORDS.values(), key=lambda x: x["key"]), "cases": cases()}


def main():
    bad = 0
    for c in cases():
        if c["arm"] == "node":
            got = RK.node_row_check(c["row"], RECORDS, c["view"])
            ok = got == (c["verdict"], c["refusal"])
            bad += not ok
            print("  %s %-70s %s %s" % ("ok  " if ok else "FAIL", c["name"][:70], c["verdict"], c["refusal"] or ""))
            continue
        got = check(c["membership"], c["row"], {x["key"]: x for x in c["records"]}, c["view"]["live_keys"])
        ok = got == (c["verdict"], c["refusal"])
        # the kernel's device clause agrees wherever the check reaches it (a room key of this room, one voice head)
        rec = c["records"][0] if c["records"] else None
        if c["membership"] == "private" and rec and rec.get("room") == ROOM and len(c["view"]["heads"]) == 1:
            ok &= c["kernel"] == (c["verdict"] == "admitted")
        bad += not ok
        print("  %s %-70s %s %s view=%s" % ("ok  " if ok else "FAIL", c["name"][:70], c["verdict"], c["refusal"] or "",
                                           c["view"]["live_keys"]))
    caught = 0
    for plant in NODE_PLANTS:
        ST.MUT.add(plant)
        try:
            hit = [n for n, extra, r, v, ref in NODE_CASES if node_verdict(extra, r)[1] != (v, ref)]
        finally:
            ST.MUT.discard(plant)
        caught += bool(hit)
        print("  plant %-28s %s" % (plant, "caught by %d cases, first: %s" % (len(hit), hit[0]) if hit else "NOT CAUGHT"))
        bad += not hit
    print("RESULT: %s: %d cases (%d of a voice, %d of a node), %d of %d planted breaks caught"
          % ("ok" if not bad else "%d problems" % bad, len(CASES) + len(NODE_CASES), len(CASES), len(NODE_CASES), caught,
             len(NODE_PLANTS)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
