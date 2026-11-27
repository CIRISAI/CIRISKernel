import sys; sys.path.insert(0,'models/causal_kernel'); sys.dont_write_bytecode=True
import seat as ST
CK=ST.CK
import sys as _s
NARROW = len(_s.argv) > 1
if NARROW:   # the caller's table: a founding duty seat holds membership, not every named duty
    H = dict(ST.HOLDS, duty=("member",)); d = list(ST.Seats.__init__.__defaults__); d[0] = H; ST.Seats.__init__.__defaults__ = tuple(d)
print("holds.duty =", ST.Seats.__init__.__defaults__[0]["duty"])
ST.POLICY["maj"] = ("strict", 1, 2)
def st(rows):
    return CK.concluded(CK.kept(list(rows)), lambda r,P,past: ST.seat_rule(r,P,past))
def show(name, rows, extra=()):
    S=st(rows); Q=ST.Seats(S)
    h=lambda s: "".join(sorted(Q.holders(s,"g")))
    nc=[r["id"] for r in rows if not S.C[r["id"]]]
    print("%-58s moderate=%-4s review=%-3s duty=%-4s member=%-5s tips=%d%s" % (name,h("moderate"),h("review"),h("duty"),h("member"),len(Q.tips("g")), "  NOT CONCLUDED: %s"%nc if nc else ""))
    return S,Q
g  = ST.offer("g","a",("a","b"),"duty","@","self",cosigners=("b",))                      # the duty holders the record names
gm = ST.offer("gm","a","c","member","g","group",("g",),head=("g",),policy="maj",cosigners=("b","c"))   # c, a founding member with no duty
fm = ST.offer("fm","a",("a","b"),"moderate","g","group",("gm",),head=("gm",),policy="duty_confer",counted="duty",cosigners=("b",))
fr = ST.offer("fr","a",("a",),"review","g","group",("fm",),head=("fm",),policy="duty_confer",counted="duty",cosigners=("b",))
wd = ST.offer("wd","a","d","member","g","group",("fr",),head=("fr",),policy="maj",cosigners=("b","d"))
mc = ST.offer("mc","a","c","moderate","g","group",("wd",),head=("wd",),policy="duty_confer",counted="duty",cosigners=("b","c"))
base=[g,gm,fm,fr,wd,mc]
show("KQ1 the founding, a widening of d, moderate conferred on c", base)
show("  + a's lone Withdraw of c's moderate offer", base+[ST.withdraw("w1","a","mc",("mc",))])
show("  + a counted Unseat of member c (a, b sign)", base+[ST.unseat("xc","a","c","member","g","group",("mc",),head=("mc",),policy="maj",cosigners=("b","d"))])
show("  founding as three concurrent rows on g (not chained)", [g, gm, dict(fm,names=("g",),head=("g",)), dict(fr,names=("g",),head=("g",))])
show("  one of two duty holders confers moderate alone", [g,gm,ST.offer("fx","a","c","moderate","g","group",("gm",),head=("gm",),policy="duty_confer",counted="duty",cosigners=("c",))])
show("  a member with no duty confers review on itself (own)", [g,gm,ST.offer("fy","c","c","review","g","self",("gm",))])
show("  a duty holder confers review on c alone (own, c accepts)", [g,gm,ST.offer("fz","a","c","review","g","self",("gm",),cosigners=("c",))])
# KQ3 leaving
g2 = ST.offer("g","a",("a","b"),"duty","@","self",cosigners=("b",))
h1 = ST.offer("h1","a","e","member","g","group",("g",),head=("g",),policy="maj",cosigners=("b","e"))
wb = ST.withdraw("wb","b","g",("h1",))                 # b withdraws its own founding seat (a duty seat that holds membership)
h2 = ST.offer("h2","a","f","member","g","group",("h1","wb"),head=("h1",),policy="maj",cosigners=("e","f"))
show("KQ3 b withdraws its founding seat; h2 names it", [g2,h1,wb,h2])
bm = ST.offer("bm","a","b","moderate","g","group",("h1",),head=("h1",),policy="duty_confer",counted="duty",cosigners=("b",))
wb2= ST.withdraw("wb2","b","g",("bm",))
show("  b also holds a conferred moderate seat; b withdraws only its founding seat", [g2,h1,bm,wb2])
show("  ... and also withdraws the moderate offer", [g2,h1,bm,wb2,ST.withdraw("wb3","b","bm",("bm",))])

# KQ2 deputies presented as Conf::Seat offers under the holder's seat
dep = lambda i,by,to,under,sub=False: ST.offer(i,by,to,"moderate","g","seat",(under,),under=under,sub=sub,cosigners=(to,))
show("KQ2 a (moderate, by the count) deputizes d by a seat offer, no sub on a's grant", [g,gm,fm,dep("dd","a","d","fm")])
fm_sub = dict(fm, sub=True)
show("  a's own grant carries sub: d is seated, as a HOLDER", [g,gm,fm_sub,dep("dd","a","d","fm")])
show("  d passes it on to e without sub on d's", [g,gm,fm_sub,dep("dd","a","d","fm"),dep("de","d","e","dd")])
show("  d passes it on to e with sub on d's", [g,gm,fm_sub,dep("dd","a","d","fm",True),dep("de","d","e","dd")])
