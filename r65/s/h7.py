exec(open(__file__.replace("h7.py","lib.py")).read())
DCg = ST.offer("dc", "A", "B", "moderate", OBJ, "group", ("g",), head=("g",), policy="duty_confer", counted="duty", cosigners=("B",))
XD = admit("xd","X",("A","B"),("dc",))           # built on the tip
CG = ("C","D","E","F","G")
run("H7a honest C..G remove A head (aG), naming dc only (dc excused)", ROOM + [DCg, remove("xa","A",CG,("aG",),("dc",))], ids=("dc","xa"))
run("H7b honest C..G remove A head (aG), naming xd (built on dc)", ROOM + [DCg, XD, remove("xa","A",CG,("aG",),("xd",))], ids=("dc","xd","xa"))
run("H7c honest C..G remove A heads (xd,aG)", ROOM + [DCg, XD, remove("xa","A",CG,("xd","aG"))], ids=("dc","xd","xa"))
run("H7d control: honest C..G remove A head (aG), no fork", ROOM + [remove("xa","A",CG,("aG",))], ids=("xa",))
# H6 kinds: reader K's only own row, of each kind, naming aG; scenario T1a
T1 = ROOM + [DCg, remove("xg","G",("A","B"),("dc","aG"))]
kinds = {
 "ack": CK.row("k","ack","K",("aG",),room=OBJ,head=("aG",)),
 "cosign": ST.cosign("k","K","aG",("aG",)),
 "accept-standing": ST.accept("k","K",None,("aG",),scope="member",obj=OBJ),
 "content(room)": CK.row("k","post","K",("aG",),room=OBJ),
 "withdraw(of aG)": ST.withdraw("k","K","aG",("aG",)),
}
for n, kr in kinds.items():
    run("H6 reader K, own row %s naming aG" % n, T1 + [kr], own="K", ids=("xg","k"))
run("H6 reader G (signed aG as newcomer)", T1, own="G", ids=("xg",))
