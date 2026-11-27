p = "/home/emoore/CIRISKernel/.claude/worktrees/agent-ad781c03a48920203/models/causal_kernel/window.py"
s = open(p).read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a)
    s = s.replace(a, b)

rep('''    answer    a row naming p that says something the window's table counts: approve, object, confirm, answered, act.
''', '''    answer    a row naming p that says something the window's table counts: approve, object, confirm, answered, act,
              against (a vote against the act proposed: the same row as `act` with the other polarity).
''')
rep('''The five windows are data (WINDOWS): the policy row of manifests/governance_policy.json, the clauses that close
the window at once, the clauses read at the close, and the default.
"""''', '''The five windows are data (WINDOWS): the policy row of manifests/governance_policy.json, the clauses that close
the window at once, the clauses read at the close, and the default.

A clause is (value said, threshold, base, outcome). The bases:
    all               the window's counted scope at the opener's head
    others            the same, less the opener's signer: out of the voices and out of the size counted over
    all_opener_mute   the same as `all` in size; the opener's signer is no voice among it (the members' check:
                      "a strict majority of the roster at the head the act names", the act's author no voice)
    opener            the opener's signer alone
    any other word    that scope at the opener's head
The thresholds: "strict", "one", ("atleast", n, d, min), ("more", n, d, min), and
    ("voted", n, d, min, against)   more than n/d of the keys of the base that VOTED, and at least min voices: a key
                      voted if it said the clause's value or `against`. A silent key is not counted over.

A duty holder's single-signature answer (a value an at-once clause reads as "one" over a named scope, said by a
holder of that scope) is what that key said: a vote the same key also cast is moot, and does not make its answer
two things said.

An opener is a row of kind `open`, or a counted act that names a window (`window` on an unseat: a moderator's lone
removal of an agent's key, seat.py). Such an act is concluded by the seat's rule and the opener's together.
"""''')
rep('''                            "silent": None, "at_close": (("act", "strict", "all", "fallback"),), "default": "lapsed"},''',
    '''                            "silent": None, "at_close": (("act", ("voted", 1, 2, 2, "against"), "all", "fallback"),), "default": "lapsed"},''')
rep('''    # CC 4.5.13: a moderator answers within 48 h; on their absence a live majority of the members acts
''', '''    # CC 4.5.13: a moderator answers within 48 h; on their absence the members act: "a strict majority of the members
    # who voted, never fewer than two voices" (data/governance_policy.tsv, moderation_action). `act` is a vote for,
    # `against` a vote against, a silent member is not counted over. A moderator's answer is no vote
''')
rep('''    # that at the close it stands. The duty holder has no say in the lift of its own act
''', '''    # that at the close it stands. The duty holder has no say in the lift of its own act: where it is itself on the
    # roster it is counted over and its objection is no voice (all_opener_mute)
''')
rep('''"at_once": (("object", ("more", 1, 2, 2), "all", "lifted"),),''', '''"at_once": (("object", ("more", 1, 2, 2), "all_opener_mute", "lifted"),),''')
rep('''MUT = set()            # planted breaks, switched on by a check
''', '''MUT = set()            # planted breaks, switched on by a check
BASES = ("all", "others", "all_opener_mute", "opener")


def is_opener(r):
    """A row that opens a window: an `open` row, or a counted act that names a window."""
    return r["kind"] == "open" or (r["kind"] == "unseat" and r.get("window") in WINDOWS)
''')
rep('''    said = K.group([a for a in answers if a["signer"] in base("all") | base("moderate") | tv
                    and not (a["signer"] == p["signer"] and a["says"] == "withdraw")], "signer", "one", "says")
''', '''    heard = [a for a in answers if a["signer"] in base("all") | base("moderate") | tv
             and not (a["signer"] == p["signer"] and a["says"] == "withdraw")]
    # a duty holder's single-signature answer is what that key said: its vote is moot
    duty = {value: over for value, how, over, _ in spec["at_once"] if how == "one" and over not in BASES}
    acted = {a["signer"] for a in heard if a["says"] in duty and a["signer"] in base(duty[a["says"]])}
    if "vote_beside_answer" in MUT: acted = set()
    said = K.group([a for a in heard if a["signer"] not in acted or a["says"] in duty], "signer", "one", "says")
''')
rep('''        keys = base(over)
        yes = K.group([{"k": s} for s, v in said.items() if v == value and (s in keys or (floor and s in tv and value == "approve"))], None, "count", "k")
        if isinstance(how, tuple):               # a threshold read off the policy table
            kind, num, den, least = how          # ("atleast", n, d, min): >= max(min, ceil(n*N/d)); ("more", n, d, min): > n/d and >= min
            if kind == "atleast": return yes >= max(least, -(-num * len(keys) // den))
''', '''        keys = base(over)
        voice = keys - {p["signer"]} if over == "all_opener_mute" else keys     # counted over all; the opener's signer no voice
        yes = K.group([{"k": s} for s, v in said.items() if v == value and (s in voice or (floor and s in tv and value == "approve"))], None, "count", "k")
        if isinstance(how, tuple):               # a threshold read off the policy table
            kind, num, den, least = how[:4]      # ("atleast", n, d, min): >= max(min, ceil(n*N/d)); ("more", n, d, min): > n/d and >= min
            if kind == "voted":                  # ("voted", n, d, min, against): > n/d of those of the base who voted, and >= min
                no = K.group([{"k": s} for s, v in said.items() if v == how[4] and s in voice], None, "count", "k")
                return yes * den > num * (yes + no) and yes >= least
            if kind == "atleast": return yes >= max(least, -(-num * len(keys) // den))
''')
rep('''            scope = spec["counted"] if name in ("all", "others") else name''', '''            scope = spec["counted"] if name in ("all", "others", "all_opener_mute") else name''')
rep('''    if k not in ("open", "answer", "receipt", "landing"):
        return ST.seat_rule(r, P, past)
    by = {q["id"]: q for q in P}
    if k == "open":
        w = WINDOWS[r["window"]]                               # the opener's signer holds the opener's scope, by default the counted one
        return r["signer"] in ST.members_at(P, past, r["obj"], r["head"], w.get("opener", w["counted"]))
    p = by.get(r["of"])
    if p is None or p["kind"] != "open": return False''', '''    if k not in ("open", "answer", "receipt", "landing") and not is_opener(r):
        return ST.seat_rule(r, P, past)
    by = {q["id"]: q for q in P}
    if is_opener(r):
        w = WINDOWS[r["window"]]                               # the opener's signer holds the opener's scope, by default the counted one
        if k != "open" and not ST.seat_rule(r, P, past): return False     # an act that opens its own window: validly made, by the seat
        return r["signer"] in ST.members_at(P, past, r["obj"], r["head"], w.get("opener", w["counted"]))
    p = by.get(r["of"])
    if p is None or not is_opener(p): return False''')
rep('''    tv = {p["target"]} if spec.get("target_votes") else set()''', '''    tv = {p.get("target")} if spec.get("target_votes") else set()''')
rep('''({p["target"]} if spec.get("target_votes") else set())]''', '''({p.get("target")} if spec.get("target_votes") else set())]''')
rep('''K.sel(inside, signer=p["target"])''', '''K.sel(inside, signer=p.get("target"))''')
rep('''K.sel(conc, signer=p["target"])''', '''K.sel(conc, signer=p.get("target"))''')
open(p, "w").write(s)
