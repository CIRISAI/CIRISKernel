#!/usr/bin/env python3
"""
check_key_person.py: a key's person at a row, as a function of rows, with no instant (seat.person_of).

A key's person at a row is the self roster (an object of kind `self`: a person's own key roster, CC 3.3.6.4, or a
voice's room keys in a private room, CC 3.1.3.2) in whose own scope the key holds a live seat over the row's
concluded past: admitted by the roster's own count, and not evicted, in that past. Two persons are none. The key
record's own end (its liveness) is the other half, kept behind seat.key_record_ended: until the Constitution rules
it, the key's own revocation (an unseat of its `registered` seat by the key) in the row's past.

Part 1. Cases: (name, rows, the row asked at, the key, the person expected), each in arrival orders.
Part 2. Planted breaks (seat.MUT), each of which must change a case's answer:
    person_evict_unread   an admission in the past is enough: an evicted key keeps its person
    person_first          two persons read as the first: a key in two self rosters gets one
    person_any_kind       any group is a person: a community's member seat makes the community a key's person
    person_end_unread     the key's own end is not read: a revoked key keeps its person

    python3 -I check_key_person.py      exit 1 on any difference
"""
import itertools
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import seat as ST  # noqa: E402
import roomkey as RK  # noqa: E402

CK, R = ST.CK, ST.R
RULE = lambda r, P, past: ST.seat_rule(r, P, past)
LEDGER = "a key to its person at a row, with no instant (0.5.0)"


def found(i, k, scope="self"):
    """A self roster founded by its first key."""
    return ST.offer(i, k, (k,), scope, "@", "self")


def add(i, roster, k, signers, heads, scope="self"):
    """A key added by the roster's own count (self_roster_add), the key signing its own seat."""
    return ST.offer(i, signers[0], k, scope, roster, "group", tuple(heads), head=tuple(heads), policy="self_roster_add",
                    counted=scope, cosigners=tuple(signers[1:]) + (k,))


def evict(i, roster, k, signers, heads, scope="self"):
    """A key evicted by the roster's own count (self_roster_evict)."""
    return ST.unseat(i, signers[0], k, scope, roster, "group", tuple(heads), head=tuple(heads), policy="self_roster_evict",
                     counted=scope, cosigners=tuple(signers[1:]))


def at(names):
    """The row asked at: a row naming `names`."""
    return R("at", "note", "x", tuple(names))


S = found("S", "k1")
A2 = add("a2", "S", "k2", ("k1",), ("S",))
A3 = add("a3", "S", "k3", ("k1", "k2"), ("a2",))
E3 = evict("e3", "S", "k3", ("k1", "k2"), ("a3",))
T = found("T", "t1")
T2 = add("b2", "T", "k2", ("t1",), ("T",))
REC = ST.offer("rec", "k1", "k1", "registered", "k1", "self")                  # k1's key record
RV = ST.unseat("rv", "k1", "k1", "registered", "k1", "self", ("rec", "S"))      # k1's own revocation
VA, HA = RK.voice_rows("vA", ["rk:a0", "rk:a1"])
G = ST.offer("g", "m1", ("m1", "m2"), "member", "@", "self", cosigners=("m2",))   # a community, no self roster

# (name, rows, key, person)
CASES = [
    ("the first key of a self roster, at a row naming the roster", [S, at(("S",))], "k1", "S"),
    ("a key added by the roster's count, at a row naming the addition", [S, A2, at(("a2",))], "k2", "S"),
    ("the same key at a row that does not have the addition in its past: no person yet", [S, A2, at(("S",))], "k2", None),
    ("a third key added by two, at a row naming its addition", [S, A2, A3, at(("a3",))], "k3", "S"),
    ("the third key evicted by the roster's count, at a row naming the eviction: no person", [S, A2, A3, E3, at(("e3",))],
     "k3", None),
    ("the other keys keep their person after the eviction", [S, A2, A3, E3, at(("e3",))], "k2", "S"),
    ("the evicted key at a row before its eviction: its person then", [S, A2, A3, E3, at(("a3",))], "k3", "S"),
    ("a key seated in two self rosters: two persons is none", [S, A2, T, T2, at(("a2", "b2"))], "k2", None),
    ("the same key with only one of the two in the row's past", [S, A2, T, T2, at(("a2",))], "k2", "S"),
    ("the key's own revocation in the row's past ends its person (the liveness half)", [S, REC, RV, at(("rv",))], "k1", None),
    ("the key's revocation not in the row's past", [S, REC, RV, at(("S",))], "k1", "S"),
    ("a room key of a voice: the voice is its person", VA + [at((HA,))], "rk:a1", "vA"),
    ("a member seat of a community is no person", [G, at(("g",))], "m1", None),
    ("a key no roster seats", [S, at(("S",))], "zz", None),
]
PLANTS = ("person_evict_unread", "person_first", "person_any_kind", "person_end_unread")


def answer(rows, k):
    S_ = CK.concluded(CK.kept(list(rows)), RULE)
    P = [q for q in S_.Cs if q["id"] in S_.anc["at"]] if S_.C.get("at") else []
    return ST.person_of(P, k)


def orders(rows):
    if len(rows) <= 6:
        return [list(p) for p in itertools.permutations(rows)]
    rnd = random.Random(len(rows))
    out = [rows[::-1]]
    for _ in range(40):
        p = list(rows)
        rnd.shuffle(p)
        out.append(p)
    return out


def answer_in(order, k):
    S_ = CK.arrive(order, RULE)
    P = [q for q in S_.Cs if q["id"] in S_.anc.get("at", ())] if S_.C.get("at") else []
    return ST.person_of(P, k)


def main():
    problems, n = [], 0
    for name, rows, k, want in CASES:
        got = answer(rows, k)
        if got != want:
            problems.append("%s: got %r, expected %r" % (name, got, want))
        for o in orders(rows):
            n += 1
            if answer_in(o, k) != got:
                problems.append("%s: order %s differs" % (name, [r["id"] for r in o]))
                break
    caught = 0
    for plant in PLANTS:
        ST.MUT.add(plant)
        try:
            hit = [c[0] for c in CASES if answer(c[1], c[2]) != c[3]]
        finally:
            ST.MUT.discard(plant)
        caught += bool(hit)
        print("  plant %-20s %s" % (plant, "caught by %d cases, first: %s" % (len(hit), hit[0]) if hit else "NOT CAUGHT"))
        if not hit:
            problems.append("plant %s not caught" % plant)
    for p in problems:
        print(p)
    print("RESULT: %s: %d cases, %d arrival orders, %d of %d planted breaks caught"
          % ("ok" if not problems else "%d problems" % len(problems), len(CASES), n, caught, len(PLANTS)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
