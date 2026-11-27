exec(open(__file__.replace("ll.py","lib.py")).read())
N=20; V=("today","L'","L")
ACKS = [ack("k"+k, k, "aG") for k in "ABCDEFG"]
DC0 = ST.offer("dc","A","B","moderate",OBJ,"group",("g",),head=("g",),policy="duty_confer",counted="duty",cosigners=("B",))
run("La five (all acked aG) remove G head aG citing dc", ROOM+ACKS+[DC0, remove("xg","G",FIVE,("aG",),("dc","kA"))], ids=("dc","xg"), scopes=("member","moderate"), n=N, vars=V)
run("La' same, reader R acked aG", ROOM+ACKS+[ack("ak","R","aG"),DC0, remove("xg","G",FIVE,("aG",),("dc","kA"))], own="R", ids=("dc","xg"), scopes=("member","moderate"), n=N, vars=V)
Q=[]; mm=["A","B"]; pv="g"
for i in range(1,9): k="X%d"%i; Q.append(admit("p%d"%i,k,tuple(mm),(pv,))); mm.append(k); pv="p%d"%i
run("Lb A,B pack X1..X8; all seven (acked aG) admit H head aG citing p8", ROOM+ACKS+Q+[admit("ah","H",tuple("ABCDEFG"),("aG",),("p8","kA"))], ids=("p8","ah"), n=N, vars=V)
run("Lb' same, reader acked aG", ROOM+ACKS+Q+[ack("ak","R","aG"), admit("ah","H",tuple("ABCDEFG"),("aG",),("p8","kA"))], own="R", ids=("p8","ah"), n=N, vars=V)
# L abuse: attacker A acked an OLD head and is a signer: its own ack makes the honest newer change "behind"? A acks aD; then A,B,C,D,E? Use: A acks aD, then A,B (+?) remove G head aD citing aG and kA
KA = ack("kA2","A","aD")
run("Lc A acks aD; A,B,C remove G head aD citing aE..aG? (aG in past)", ROOM+[KA, remove("xg","G",("A","B","C"),("aD",),("aG","kA2"))], ids=("xg",), n=N, vars=V)
