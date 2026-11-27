exec(open(__file__.replace("a3.py","lib.py")).read())
glic = C.glic; GD = C.GD; GLO, GLA = C.GLO, C.GLA
NA = (False, "licensure_delegator_not_authority")
LDA = ST.withdraw("lda","A","g",(),scope="moderate"); LDB = ST.withdraw("ldb","B","g",(),scope="moderate")
run("B1 A,B lay down (locked); A,B confer license seat on X naming only g; X licenses", [GD,LDA,LDB,A("e","RD","g"),GLO,GLA,glic("l","g","X")|{"names":("gla","lda","ldb")}], "RD","l", want=NA)
run("B1c control: the seat names lda,ldb", [GD,LDA,LDB,A("e","RD","g"),dict(GLO,names=("g","lda","ldb")),GLA,glic("l","g","X")|{"names":("gla",)}], "RD","l", want=NA)
# officer self-seating on a no-officer affiliation (AF, dissolved)
AF = C.AF
SELF = ST.offer("so","B","B",ST.OFFICER,"af","self",("af",))
run("O1 dissolved AF; founder B seats itself officer (conf self); B's licence", [AF,SELF,A("e","RD","af"),glic("l","af","B")|{"names":("so",)}], "RD","l", want=NA,
    extra=lambda S: (bool(S.C.get("so")), sorted(ST.Seats(S).holders(ST.OFFICER,"af")), ST.Seats(S).dissolved("af")))
AFD1 = C.AFD1
SELF2 = ST.offer("so","B","B",ST.OFFICER,"af","self",("af",))
run("O2 one-officer AFD1; member B seats itself officer (conf self)", [AFD1,SELF2,A("e","RD","af"),glic("l","af","B")|{"names":("so",)}], "RD","l", want=NA,
    extra=lambda S: (bool(S.C.get("so")), sorted(ST.Seats(S).holders(ST.OFFICER,"af"))))
SELF3 = ST.offer("so","B","B","license","af","self",("af",))
run("O3 AFD1: member B confers license on itself (conf self)", [AFD1,SELF3,A("e","RD","af"),glic("l","af","B")|{"names":("so",)}], "RD","l", want=NA,
    extra=lambda S: bool(S.C.get("so")))
GN = C.GN
SELF4 = ST.offer("so","B","B","license","g","self",("g",))
run("O4 locked GN (no map): founder B confers license on itself (conf self)", [GN,SELF4,A("e","RD","g"),glic("l","g","B")|{"names":("so",)}], "RD","l", want=NA,
    extra=lambda S: bool(S.C.get("so")))
SELF5 = ST.offer("so","B","B","duty","g","self",("g",))
run("O5 locked GN: founder B seats itself duty (conf self), then B alone confers license on X", [GN,SELF5,A("e","RD","g"),dict(C.GLO1,signer="B",names=("so",)),GLA,glic("l","g","X")|{"names":("gla",)}], "RD","l", want=NA,
    extra=lambda S: (bool(S.C.get("so")), sorted(ST.Seats(S).holders("duty","g"))))
