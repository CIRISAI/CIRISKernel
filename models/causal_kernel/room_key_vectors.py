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

ST, CK, RT = RK.ST, RK.CK, RK.RT
ROOM, OTHER = RK.ROOM, "g2"
LEDGER = "CIRISConstitution#224: a room row's signer and its voice (CC 3.1.3.2)"

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


def cases():
    out = []
    for name, membership, r, verdict, refusal in CASES:
        view = view_at(r["iss"], r["refs"]["also"]["voice"])
        out.append({"name": name, "ledger": LEDGER, "membership": membership, "room": ROOM, "row": r,
                    "records": [RECORDS[r["kid"]]] if r["kid"] in RECORDS else [],
                    "view": {"voice": r["iss"], "heads": r["refs"]["also"]["voice"], "live_keys": view},
                    "verdict": verdict, "refusal": refusal,
                    "kernel": kernel_reading(r) if membership == "private" else None})
    return out


def fixture():
    """The vector file: the voice rosters the views are folded from, the key records, and the cases."""
    return {"about": "CIRISConstitution#224, CC 3.1.3.2: a private room's row door (signer a room key, its record's room, "
                     "one voice head, a live key of the voice there); views folded by seat.members_at",
            "room": ROOM, "roster_rows": ROSTER, "records": sorted(RECORDS.values(), key=lambda x: x["key"]), "cases": cases()}


def main():
    bad = 0
    for c in cases():
        got = check(c["membership"], c["row"], {x["key"]: x for x in c["records"]}, c["view"]["live_keys"])
        ok = got == (c["verdict"], c["refusal"])
        # the kernel's device clause agrees wherever the check reaches it (a room key of this room, one voice head)
        rec = c["records"][0] if c["records"] else None
        if c["membership"] == "private" and rec and rec.get("room") == ROOM and len(c["view"]["heads"]) == 1:
            ok &= c["kernel"] == (c["verdict"] == "admitted")
        bad += not ok
        print("  %s %-70s %s %s view=%s" % ("ok  " if ok else "FAIL", c["name"][:70], c["verdict"], c["refusal"] or "",
                                           c["view"]["live_keys"]))
    print("RESULT: %s: %d cases" % ("ok" if not bad else "%d differ" % bad, len(CASES)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
