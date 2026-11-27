import sys
p = sys.argv[1]
s = open(p).read()


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a, s.count(a))
    s = s.replace(a, b)


rep('''def voices(r, P):''', '''def stay_ended_in_past(P, past, obj):
    """The keys whose own end of a stay as a member of obj is among P (a counted row's past) with no admission of the
    key after it there: a count over the duty holders that has such an end in its past does not count that key, since
    the end ended its duty seats. The counted removal needs no such reading: it is a head, read by members_at."""
    if "leaving_unread" in MUT or "resign_keeps_duty" in MUT: return frozenset()
    by = {q["id"]: q for q in P}
    if not duty_room(by, obj): return frozenset()
    back = lambda w, k: any(m["kind"] == "offer" and m["obj"] == obj and k in m["to"] and roster_seat(m) and past(w["id"], m["id"]) for m in P)
    return frozenset(k for w, k, g in stay_ends(P, by) if g == obj and not back(w, k))


def count_left(P, past, obj, scope):
    """The keys a count over `scope` at obj leaves out for a leaving in its row's past: the leaving of that seat, and for
    a seat the duty holders place, the end of the key's stay as a member."""
    out = left_in_past(P, obj, scope)
    return out if scope in ROSTER_SEATS else out | stay_ended_in_past(P, past, obj)


def voices(r, P):''')
rep('''                mem = members_at(P, past, over, r.get("head", ()), counted) - left_in_past(P, over, counted)''',
    '''                mem = members_at(P, past, over, r.get("head", ()), counted) - count_left(P, past, over, counted)''')
rep('''            mem = members_at(P, past, r.get("over", r["obj"]), heads, r.get("counted", "member")) \\
                - left_in_past(P, r.get("over", r["obj"]), r.get("counted", "member"))''',
    '''            mem = members_at(P, past, r.get("over", r["obj"]), heads, r.get("counted", "member")) \\
                - count_left(P, past, r.get("over", r["obj"]), r.get("counted", "member"))''')
open(p, 'w').write(s)
