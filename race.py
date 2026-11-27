import sys; sys.path.insert(0, '.')
import check_room_keys as C, seat as ST
CK=ST.CK
def show(name, rows):
    S = CK.concluded(CK.kept(rows), C.RULE)
    Q = ST.Seats(S)
    print(name)
    print("   concluded:", {r["id"]: bool(S.C.get(r["id"])) for r in rows[3:]})
    print("   roster:", sorted(Q.roster("g")), "| tips:", [t["id"] for t in Q.tips("g")])
    print("   tips_fold member:", Q.tips_fold("member","g") and sorted(Q.tips_fold("member","g")), "| tips_common:", Q.tips_common("member","g") and sorted(Q.tips_common("member","g")))
PV=C.PV; XQ=C.XQ; WQ=C.WQ
aq2=C.rejoin("aq2","q",("ag",))
h=ST.cosign("h","m1","h",("xq","aq2"))
hw=ST.cosign("h","m1","h",("wq","aq2"))
show("A removal || readmit", PV+[XQ,aq2])
show("B + head naming both", PV+[XQ,aq2,h])
show("C + later offer of q", PV+[XQ,aq2,h,C.rejoin("aq3","q",("h",))])
show("D resign || readmit", PV+[WQ,aq2])
show("E + head naming both", PV+[WQ,aq2,hw])
show("F + later offer of q", PV+[WQ,aq2,hw,C.rejoin("aq3","q",("h",))])
# acceptance concurrent with end
base=[PV[0], C.admit("aq","q",("m1","m2","m3","m4"),("g",),joiner=False), ST.accept("acq","q","aq")]
show("G accept withdrawn || re-accept", base+[ST.withdraw("wa","q","acq",("acq",)), ST.accept("acq2","q","aq",("acq",))])
oq=C.admit("oq","q",("m1","m2","m3","m4"),("acq",),joiner=False)
show("H counted removal || accept of a fresh offer", base+[remove:=C.remove("xq","q",("m1","m2","m3","m4"),("acq",)), oq, ST.accept("acq2","q","oq",("oq",))] )
