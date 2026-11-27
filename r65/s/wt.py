exec(open(__file__.replace("wt.py","lib.py")).read())
DC = lambda i, to, heads=("aG",): ST.offer(i, "A", to, "moderate", OBJ, "group", tuple(heads), head=tuple(heads), policy="duty_confer", counted="duty", cosigners=())
acc = lambda i, k, of: ST.accept(i, k, of)
SIB = [DC("z"+k, k) for k in "CDE"] + [acc("k"+k, k, "z"+k) for k in "CDE"]
base = ROOM + [DC("d1","B"), acc("kB","B","d1")]
cl = [ST.offer("c","A","F","moderate",OBJ,"group",("d1","kB"),head=("d1",),policy="duty_confer",counted="duty",cosigners=("B",)), acc("kF","F","c")]
WB = ST.unseat("wb","A","B","moderate",OBJ,"group",("d1","zC","zD","zE","kB","kC","kD","kE"),head=("d1","zC","zD","zE"),policy="duty_withdraw",counted="duty",cosigners=("C","D","E"))
SC = ("moderate",)
run("WT1 closer signed by A and B; siblings; no wb", base + cl + SIB, ids=("zC",), scopes=SC)
posts = [CK.row("q"+k,"post",k,("zC","zD","zE"),room=OBJ) for k in "CDE"]
run("WT2 same + C,D,E each post a content row on the siblings' side", base + cl + SIB + posts, ids=("zC",), scopes=SC)
run("WT3 closer + siblings + wb (A,C,D,E)", base + cl + SIB + [WB], ids=("zC","wb"), scopes=SC)
hon = [CK.row("h"+k,"post",k,("c",),room=OBJ) for k in "FG"]
run("WT4 WT3 + honest F,G post after the closer", base + cl + SIB + [WB] + hon, ids=("zC","wb"), scopes=SC)
