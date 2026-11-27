import sys
sys.path.insert(0, sys.argv[1])
import seat as ST, window as WN, check_duty_seats as CD
CK = ST.CK
RULE = lambda r, P, past: WN.rule(r, P, past)
for name, G in (("lone founder", ST.found("g", "A", ("A",), {})),
                ("map, A lone holder, signed alone", ST.found("g", "A", ("A",), {"moderate": ("A",)})),
                ("map A,B; A holder", ST.found("g", "A", ("A", "B"), {"moderate": ("A",)}, cosigners=("B",))),
                ("A,B no map", ST.found("g", "A", ("A", "B"), {}, cosigners=("B",)))):
    MB = CD.admit("mb", "B", ("A",), ("g",)) if len(G["to"]) == 1 else None
    pre = [G] + ([MB] if MB else [])
    h = (pre[-1]["id"],)
    au = ST.offer("au", "A", "B", "author", "g", "self", h, cosigners=("B",))
    for rows in (pre + [au], pre + [au, ST.withdraw("wa", "A", "au", ("au",))]):
        S = CK.concluded(CK.kept(rows), RULE); Q = ST.Seats(S)
        print(name, [r["id"] for r in rows[len(pre):]], {r["id"]: bool(S.C.get(r["id"])) for r in rows}, "B author", Q.stands("B", "author", "g"))
