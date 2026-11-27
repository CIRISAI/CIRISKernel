import sys, itertools
sys.path.insert(0, sys.argv[1])
exec(open(sys.argv[2]).read().split("GM4 = AC.GM4")[0])
FAM, FAM2, FAMJ, FADM, FREM, FREC, FDIS = AC.FAM, AC.FAM2, AC.FAMJ, AC.FADM, AC.FREM, AC.FREC, AC.FDIS
# 1a self-promotion by own (uncounted) offer: B is a founding signer, not a founder
own = ST.offer("o", "B", "B", "founder", OBJ, "self", ("g",))
run("FA1 B (no founder) own offer of founder to itself; then B alone admits D (founder_only)", [FAM, own, FADM("r", "D", signer="B", heads=("o",))], [("B", "founder"), ("D", "member")])
own2 = dict(ST.offer("o", "B", "X", "member", OBJ, "self", ("g",), cosigners=("X",)), role="founder")
run("FA1b B's own offer of member with role founder to X; X alone admits D", [FAM, own2, FADM("r", "D", signer="X", heads=("o",))], [("X", "founder"), ("D", "member")])
# 1b role founder on a counted admission by a non-founder member under founder_only
ad = dict(FADM("r", "X", signer="B", counted="founder"), role="founder")
run("FA2 B (no founder) admits X with role founder", [FAM, ad], [("X", "founder")])
# 1c demotion passed as a record change (metadata)
md = FREC("am", None, signer="A", duty_holders=(("founder", ()),))
run("FA3 A changes the record's founder map to none", [FAM2, md], [("B", "founder"), ("A", "founder")])
# 1d resigned founder acts: A2 founders A,B; B leaves the family, then B admits D naming its leaving
lv = ST.withdraw("lv", "B", "g", ("g",))
run("FA4 B leaves, then admits D at head lv", [FAM2, lv, FADM("r", "D", signer="B", heads=("lv",))], [("D", "member"), ("B", "founder")])
run("FA4b B leaves (after), admits D at head g with its leaving in its past", [FAM2, lv, dict(FADM("r", "D", signer="B", heads=("g",)), names=("g", "lv"))], [("D", "member")])
# 1e contested pair: A demotes B, B demotes A, concurrently
dA = FREM("da", "B", signer="A", scope="founder"); dB = FREM("db", "A", signer="B", scope="founder")
run("FA5 contested demotions A->B, B->A", [FAM2, dA, dB], [("A", "founder"), ("B", "founder"), ("A", "member"), ("B", "member")])
run("FA5b then C (member) ... A admits D naming both", [FAM2, dA, dB, FADM("r", "D", signer="A", heads=("da", "db"))], [("D", "member")])
# 1f dissolution from an old head by a founder later demoted
dm = FREM("dm", "B", signer="A", scope="founder")
ds = FDIS("d", signer="B", heads=("g",))
run("FA6 A demotes B; B dissolves the family at old head g", [FAM2, dm, ds], [("A", "member"), ("C", "member")], orders=False)
