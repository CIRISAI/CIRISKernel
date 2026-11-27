"""Proposal (c) for the copy rule, as simulated before it was built (kept so the comparison is not lost).

It ran (c) beside the reference as it then stood (proposal a: the copy rule bounded by place(), and history_on_join
narrowing the served audience) over review r79's leak.py rows 1 to 5 and every case of check_audience.py, and
printed the answers that differ. audience.py now builds (c) (audience.carried), so run against the current
reference every row prints "same as built".

    python3 -I models/causal_kernel/proto/sim_c.py models/causal_kernel
"""
import sys
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import audience as AU, check_audience as CA

TARGETED = AU.TARGETED


def audiences_c(rows, roster, person, joins=AU.NO_JOINS):
    out = {r["id"]: AU.place(r, roster, person, joins) for r in rows}
    by = {r["id"]: r for r in rows}
    namers = {i: [] for i in by}
    for d in rows:
        for n in d.get("names", ()):
            if n in namers:
                namers[n].append(d)
    changed = True
    while changed:
        changed = False
        for i, a in out.items():
            if a[0] != "placed":
                continue
            r = by[i]
            if r["family"].startswith("key_grant:"):
                continue                                   # a key grant is never carried
            for d in namers[i]:
                ad = out[d["id"]]
                if ad[0] != "placed" or not d.get("concluded"):
                    continue
                if not AU._within(d["signer"], out[i][2]):
                    continue
                if a[1] in TARGETED:
                    # (c.1) a concluded room row carries the room rows it names, to keys owed it and on the
                    # room's current roster
                    if not (ad[1] in TARGETED and d.get("room") == r.get("room")):
                        continue
                    add = AU._meet(ad[2], frozenset(roster(r["room"])))
                else:
                    # (c.3) a self or addressed row: only by a concluded row of its own signer (or person)
                    if d["signer"] != r["signer"] and d["signer"] not in person(r["signer"]):
                        continue
                    add = ad[2] if ad[1] not in TARGETED else AU._meet(ad[2], frozenset(roster(d["room"])))
                grown = AU._union(out[i][2], add)
                if grown != out[i][2]:
                    out[i] = ("placed", out[i][1], grown); changed = True
    return out


def run(tag, rows, w=None, want=None):
    j = CA.joins_of(w)
    a = {i: CA.enc(x) for i, x in AU.audiences(rows, CA.roster, CA.person, j).items()}
    c = {i: CA.enc(x) for i, x in audiences_c(rows, CA.roster, CA.person, j).items()}
    diff = {i: (a[i], c[i]) for i in a if a[i] != c[i]}
    print("%-34s %s" % (tag, "same as built" if not diff else ""))
    for i, (x, y) in diff.items():
        print("     %s: built %s -> (c) %s" % (i, x[2] if x[0] == "placed" else x, y[2] if y[0] == "placed" else y))
    if want is not None:
        bad = {i: (c.get(i), v) for i, v in want.items() if c.get(i) != v}
        return bad
    return {}


row = CA.row
w = {"joined": {"r3": {"j": "adm"}}, "before": [["m0", "adm"], ["m1", "adm"], ["m0", "m1"], ["m0", "d"], ["m1", "d"], ["adm", "d"]]}
m0 = row("m0", "chat:general", "community", signer="a", room="r3")
m1 = row("m1", "chat:general", "community", signer="b", room="r3", names=["m0"])
d = row("d", "chat:general", "community", signer="b", room="r3", names=["m1"])
adm = row("adm", "partner_role:member", "community", signer="a", room="r3", named=["j"], seats=["j"], names=["m1"])
o = row("o", "partner_role:member", "community", signer="a", room="r1", named=["z"], seats=["z"], names=["h1"])
h1 = row("h1", "chat:general", "community", signer="b", room="r1", names=["h0"])
h0 = row("h0", "chat:general", "community", signer="c", room="r1")
g0 = row("g0", "chat:general", "community", signer="e", room="r2")
g1 = row("g1", "chat:general", "community", signer="a", room="r2", names=["g0"])
x = row("x", "partner_role:member", "community", signer="a", room="r2", named=["c"], seats=["c"], names=["g1"])
print("== leak.py rows 1 to 5")
run("1 baseline", [m0, m1], w)
run("2 reply after the join", [m0, m1, d], w)
run("3 the admission names m1", [m0, m1, adm], w)
run("4 un-accepted offer to z", [h0, h1, o])
run("5 removal of c", [g0, g1, x])
print("== a key grant named by a reply")
kg = row("kg", "key_grant:content", "community", signer="a", room="r3")
run("key grant", [kg, row("d2", "chat:general", "community", signer="b", room="r3", names=["kg"])], w)
print("== every audience case")
for name, _, rows, want, *ww in CA.cases_now():
    run(name, rows, ww[0] if ww else None)
