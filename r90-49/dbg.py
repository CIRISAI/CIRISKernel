import sys
sys.path.insert(0, sys.argv[1] + "/models/causal_kernel")
import check_election as EL
ST=EL.ST
G5, LM, H5, IDS5, EC = EL.G5, EL.LM, EL.H5, EL.IDS5, EL.EC
for name, rows in [("D3", [G5, LM] + H5 + [EC, EL.decline("dc", "C", names=("ec",)), EL.elect("eb", "B", IDS5 + ("dc",))]),
                   ("D3b no ec", [G5, LM] + H5 + [EL.decline("dc", "C", names=("lm",)), EL.elect("eb", "B", IDS5 + ("dc",))]),
                   ("D3c dc names lm, ec concurrent", [G5, LM] + H5 + [EC, EL.decline("dc", "C", names=("lm",)), EL.elect("eb", "B", IDS5 + ("dc",))]),
                   ("R3 ex", [G5, LM] + H5 + [EC, EL.decline("dd", "D", names=("ec",)), EL.elect("ex", "C", IDS5 + ("dd",))])]:
    rows = EL.at_newest(rows)
    S = ST.CK.concluded(ST.CK.kept(list(rows)), EL.RULE)
    print(name, {r["id"]: bool(S.C.get(r["id"])) for r in rows if r["id"] in ("ec","eb","ex","dc","dd")})
    for r in rows:
        if r["id"] in ("eb","ex","dc","dd"): print("   ", r["id"], r["names"], r.get("head"))
