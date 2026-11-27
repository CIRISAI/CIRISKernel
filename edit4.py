import sys
p = sys.argv[1]
s = open(p).read()


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a, s.count(a))
    s = s.replace(a, b)


rep('''               Only where the community's founding row is of scope `duty`.
''', '''               Only where the community's founding row is of scope `duty`, and only a seat that makes its holder
               a duty holder (`duty`, a named duty, a duty the record declares): another seat the duty holders
               place, a node's detector seat for one, is not asked for membership.
''')
rep('''def _lone(r, P, by):
    """CC''', '''def duty_held(by, o):
    """A duty seat proper: a seat the duty holders place over their community (duty_seat) whose scope makes its holder a
    duty holder. The seat the membership rule reaches."""
    return duty_seat(by, o) and is_duty(o["scope"], declared(by, o["obj"]))


def _lone(r, P, by):
    """CC''')
rep('''"resign_keeps_duty" in MUT or not duty_seat(S.by, o): return False''', '''"resign_keeps_duty" in MUT or not duty_held(S.by, o): return False''')
rep('''not in u["cuts"] and duty_seat(S.by, o): continue''', '''not in u["cuts"] and duty_held(S.by, o): continue''')
rep('''            keep = [(o, k) for o, k in base if not duty_seat(S.by, o) or (o["obj"], k) in mem''', '''            keep = [(o, k) for o, k in base if not duty_held(S.by, o) or (o["obj"], k) in mem''')
rep('''"duty_fold_unread" in MUT or not duty_seat(self.S.by, self.S.by[rec["offer"]]): return True''', '''"duty_fold_unread" in MUT or not duty_held(self.S.by, self.S.by[rec["offer"]]): return True''')
rep('''    out = left_in_past(P, obj, scope)
    return out if scope in ROSTER_SEATS else out | stay_ended_in_past(P, past, obj)''', '''    out = left_in_past(P, obj, scope)
    by = {q["id"]: q for q in P}
    return out | stay_ended_in_past(P, past, obj) if is_duty(scope, declared(by, obj)) else out''')
rep('''    """The keys a count over `scope` at obj leaves out for a leaving in its row's past: the leaving of that seat, and for
    a seat the duty holders place, the end of the key's stay as a member."""''', '''    """The keys a count over `scope` at obj leaves out for a leaving in its row's past: the leaving of that seat, and for
    a count over duty holders, the end of the key's stay as a member. A count over another scope is as it was."""''')
open(p, 'w').write(s)
