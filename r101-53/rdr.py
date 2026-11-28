"""A reader's own first row (f0f3ff9: the line is only rows the reader signed itself), and its later rows chained to it
(an honest client names its own previous row). Rows in the anchor's own past are left as they are."""
def with_reader(ST, rows, rd):
    if rd is None: return list(rows)
    by = {r["id"]: r for r in rows}
    pref = {"p4": ("gc",), "m4": ("gr", "rm"), "x": ("S1r",), "x9": ("Sr", "S1r")}.get(rd, ())
    anchor = next((a for a in pref if a in by), None)
    if anchor is None: return list(rows)
    before, todo = set(), [anchor]
    while todo:
        i = todo.pop()
        if i in before or i not in by: continue
        before.add(i); todo += list(by[i]["names"])
    n = "rdr" + rd
    out = [dict(r, names=tuple(r["names"]) + (n,)) if r["signer"] == rd and r["id"] not in before else r for r in rows]
    return out + [ST.R(n, "note", rd, (anchor,))]
