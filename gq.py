import sys
sys.path.insert(0, sys.argv[1])
import seat as ST, window as WN, check_duty_seats as CD
CK = ST.CK
RULE = lambda r, P, past: ST.seat_rule(r, P, past)
O = "g"
GA, MDA = CD.GA, CD.MDA
tests = [
 ("admission of E by A alone under accord_halt", [GA, ST.offer("me", "A", "E", "member", O, "group", ("g",), head=("g",), policy="accord_halt", cosigners=("E",))], ("E", "member")),
 ("removal of C by A alone under accord_halt", [GA, ST.unseat("xc", "A", "C", "member", O, "group", ("g",), head=("g",), policy="accord_halt")], ("C", "member")),
 ("withdrawal of A's moderate by B alone, counted duty, accord_halt", [GA, ST.unseat("u", "B", "A", "moderate", O, "group", ("g",), head=("g",), policy="accord_halt", counted="duty")], ("A", "moderate")),
 ("recall of A's moderate by B alone, counted member, accord_halt", [GA, ST.unseat("u", "B", "A", "moderate", O, "group", ("g",), head=("g",), policy="accord_halt")], ("A", "moderate")),
 ("withdrawal of A's moderate by B alone, counted moderate (A the only holder), duty_withdraw", [GA, ST.unseat("u", "B", "A", "moderate", O, "group", ("g",), head=("g",), policy="duty_withdraw", counted="moderate")], ("A", "moderate")),
 ("withdrawal of A's moderate under moderator_election", [GA, ST.unseat("u", "B", "A", "moderate", O, "group", ("g",), head=("g",), policy="moderator_election", options=("A",))], ("A", "moderate")),
 ("admission under duty_confer counted duty by A,B", [GA, ST.offer("me", "A", "E", "member", O, "group", ("g",), head=("g",), policy="duty_confer", counted="duty", cosigners=("B", "E"))], ("E", "member")),
]
for n, rows, (k, s) in tests:
    S = CK.concluded(CK.kept(rows), RULE); Q = ST.Seats(S)
    print("%-90s concluded=%s %s %s=%s" % (n, bool(S.C.get(rows[-1]["id"])), k, s, Q.stands(k, s, O)))
