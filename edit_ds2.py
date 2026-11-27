import sys
p = sys.argv[1] + '/models/causal_kernel/check_duty_seats.py'
s = open(p).read()
a = '''    # ---- a conferral between the end and the re-admission'''
assert s.count(a) == 1
s = s.replace(a, '''    ("a holder admitted again and conferred on afresh is counted in a duty count that has its old resignation in its past: E's seat, signed by A and D of the three holders, is conferred",
     [G2, admit("me", "E", ("A", "B"), ("g",)), admit("md", "D", ("A", "B"), ("me",)), CD, WD, MD2, CD2, confer("ce", "E", "review", ("A", "D"), ("cd2",))],
     [("E", "review", T), ("D", "moderate", T)], None),
''' + a)
open(p, 'w').write(s)
p = sys.argv[1] + '/tools/kernel_crate_plants.sh'
s = open(p).read()
a = '''plant "the tips read as their common members" src/seat.rs'''
assert s.count(a) == 1
s = s.replace(a, '''plant "a duty seat stands on a key that is not a member" src/seat.rs 'if held.contains(&true) {' 'if false {'
plant "a resignation ends no duty seat by its past (revival)" src/seat.rs '&& !unseated(oi, k) && !resigned(oi, k) {' '&& !unseated(oi, k) {'
plant "a removal from the roster cuts the member seat only (revival)" src/seat.rs 'let held = same && (ur.scope() == o.scope() || (dutyish && member(ur.scope())));' 'let held = same && ur.scope() == o.scope();'
plant "a holder's end of its stay ends another key's duty seats" src/seat.rs '*k2 == k && oo.as_ref() == Some(room) && g.in_past(oi, *w)' 'oo.as_ref() == Some(room) && g.in_past(oi, *w)'
plant "at tips a duty seat does not follow the folded roster" src/seat.rs '!self.duty[i] || self.tips_fold("member", &r.obj).is_none_or(|c| c.contains(&r.k))' 'true'
plant "the founding seat is no member seat" src/seat.rs 'let own = o.obj() == Some(Obj::Row(o.id().clone())) || law.roster_seats.iter().any(|x| x == s);' 'let own = law.roster_seats.iter().any(|x| x == s);'
plant "every seat the duty holders place asks for membership" src/seat.rs 'duty_seat(law, by, o) && law.is_duty(s.as_ref(), &declared(by, &obj))' 'duty_seat(law, by, o)'
plant "a duty count counts a holder whose resignation is in its past" src/seat.rs 'if !mem.is_empty() && law.is_duty(counted, &duties) {' 'if false {'
plant "a holder admitted again stays out of the duty count" src/seat.rs 'if !back {' 'if true {'
''' + a)
open(p, 'w').write(s)
