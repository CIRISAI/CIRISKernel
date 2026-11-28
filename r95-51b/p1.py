import sys, os, random
sys.path.insert(0, os.path.join(sys.argv[1], "models/causal_kernel"))
import check_key_person as KP
ST, CK = KP.ST, KP.CK
def run(name, rows, n=30):
    def ans(rs):
        for m in ("_READER_MEMO", "_VOID_MEMO", "_EMEMO", "_SEATS_OF", "_PERSON_IN"): getattr(ST, m).clear()
        S = CK.concluded(CK.kept(list(rs)), KP.RULE)
        return bool(S.C.get("az"))
    a = ans(rows); rnd = random.Random(2); d = 0
    for _ in range(n):
        t = list(rows[1:]); rnd.shuffle(t)
        for m in ("_READER_MEMO", "_VOID_MEMO", "_EMEMO", "_SEATS_OF", "_PERSON_IN"): getattr(ST, m).clear()
        if bool(CK.arrive([rows[0]] + t, KP.RULE).C.get("az")) != a: d += 1
    print(name); print("   z admitted: %s | orders differing %d of %d" % (a, d, n))
B = KP.BASE + [KP.P1C]
run("P1a control: p1 (genesis key of person S1), p2, p3 admit z: three persons of four", B + [KP.admit_z(("p1", "p2", "p3"), ("a1c",))])
EV1 = KP.evict("e1", "S1", "p1", ("p1b", "p1c"), ("a1c",))          # the person's other devices evict its genesis key
run("P1b p1 evicted from S1 by p1b and p1c; the stolen p1, p2, p3 sign", B + [EV1, KP.admit_z(("p1", "p2", "p3"), ("e1",))])
run("P1c control: an evicted DEVICE key: p1b evicted (e1b), then p1b, p2, p3 sign", KP.BASE + [KP.P1C, KP.EV1B, KP.admit_z(("p1b", "p2", "p3"), ("e1b",))])
rows = B + [EV1, KP.admit_z(("p1", "p2", "p3"), ("e1",))]
S_ = CK.concluded(CK.kept(rows), KP.RULE)
P = [q for q in S_.Cs if q["id"] in S_.anc["az"]]
print("   e1 concluded:", bool(S_.C.get("e1")), "| rosters_of(p1):", ST.rosters_of(P, "p1"), "| rep_of(p1):", ST.rep_of(P, "p1"),
      "| rep_of(p1b):", ST.rep_of(P, "p1b"), "| person_key(S1):", ST.person_key(P, "S1"))
