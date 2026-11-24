#!/usr/bin/env python3
"""
kernel_fixtures.py: write the Python models' own cases, with every answer the models give, as JSON fixtures for
the Rust crate's differential tests (crates/ciris-kernel/tests/).

    python3 -I tools/kernel_fixtures.py           write crates/ciris-kernel/tests/fixtures/*.json
    python3 -I tools/kernel_fixtures.py --check   regenerate in memory and exit 1 if any committed fixture differs

Each fixture holds rows as the models build them and the answers the models compute over them. The Rust tests
rebuild the same rows, run the crate, and compare answer by answer. Nothing here changes a model; it imports them.

Sources (all under models/):
    lib       kernel_lib.py: the reducers and the interval over every small input (generated here)
    reexpress kernel_lib/reexpress.py: the six re-expressed decisions over small input spaces (generated here)
    causal    causal_kernel/check.py: every set of up to six rows of its two pools (its section 1 worlds)
    cut       causal_kernel/check_cut.py: its section 1 worlds, at its own bounds
    seat      causal_kernel/attacks.py (every scenario its 34 tests conclude, with the seat, window and route rules)
              and causal_kernel/window.py (the adversary table): conclusions, the cut, live seats, the reader's
              line, holders, tips and window outcomes
    purge     causal_kernel/purge.py: every replay check_purge.py runs, under both readings
    key_end   causal_kernel/check_key_end.py: every generated world at every instant
    conferral_end causal_kernel/conferral_end.py: the case table of the end of a conferral (CC 2.4.1.1, CC 4.5.5),
              with every act's `counted`, `in_force` and deciding `rule`. tests/conferral_end.rs replays it
              through conferral::answers, and an adopter may run it against its own code.
    conferral_content causal_kernel/conferral_content.py: room content after a member's seat ends, where the end
              names the rows held good: its case table, and (conferral_content_worlds) histories built row by
              row as check_conferral_content.py builds them. tests/content.rs replays both through content::answers.
    conferral_two causal_kernel/check_conferral_two.py: one row that needs two standings (an owner binding and a
              root grant): its case table, per act and owner. No Rust test reads it; it is for Verify's
              standing walk and an adopter's own code.
"""
import base64
import hashlib
import itertools
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CK_DIR = os.path.join(ROOT, "models", "causal_kernel")
LIB_DIR = os.path.join(ROOT, "models", "kernel_lib")
OUT = os.path.join(ROOT, "crates", "ciris-kernel", "tests", "fixtures")
sys.path.insert(0, CK_DIR)
sys.path.insert(0, LIB_DIR)
sys.dont_write_bytecode = True
os.environ.setdefault("GATES_TMP", os.environ.get("TMPDIR", "/tmp"))

import kernel_lib as KL  # noqa: E402
import reexpress as RX   # noqa: E402
import causal_kernel as CK  # noqa: E402


# ---- encoding ----------------------------------------------------------------------------------------------
def enc(v):
    if v is None or isinstance(v, (bool, str)):
        return v
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        raise ValueError("a float in a fixture: %r" % v)
    if isinstance(v, (tuple, list)):
        return [enc(x) for x in v]
    if isinstance(v, (set, frozenset)):
        return sorted((enc(x) for x in v), key=lambda x: json.dumps(x, sort_keys=True))
    if isinstance(v, dict):
        return {str(k) if not isinstance(k, tuple) else "|".join(map(str, k)): enc(x) for k, x in v.items()}
    raise TypeError(type(v))


def row_enc(r):
    return {k: enc(v) for k, v in r.items()}


def dump(name, obj, out):
    text = json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n"
    out[name] = text


# ---- lib: the reducers ---------------------------------------------------------------------------------------
def lib_cases():
    cases = []
    vals = (0, 1, 2)
    pool = [{"id": i, "v": v, "p": p, "t": 0} for i in ("x", "y", "z") for v in vals for p in ("a", "b")]
    for n in range(0, 4):
        for rows in itertools.combinations(pool, n):
            rows = list(rows)
            c = {"rows": [row_enc(r) for r in rows]}
            for how in ("least", "greatest"):
                try:
                    got = KL.group(rows, None, how, "v")
                    c[how] = None if got is None else row_enc(got)
                except KL.Tie:
                    c[how] = "Tie"
            for how in ("min", "max", "one", "count"):
                c[how] = KL.group(rows, None, how, "v")
            c["sum"] = KL.group(rows, None, "sum", "v", per="p")
            c["by_id_count"] = enc(KL.group(rows, "id", "count", "v"))
            cases.append(c)
    rng = (None, 0, 1, 2)
    intervals = [[x, lo, hi, KL.in_range(x, lo, hi)] for x in rng for lo in rng for hi in rng]
    return {"reduce": cases, "in_range": intervals}


# ---- reexpress: the six decisions over small input spaces -----------------------------------------------------
def reexpress_cases():
    out = {"takedown": [], "deletion": [], "owner_of": [], "guardianship": [], "ranked": [], "set_item": []}
    kinds = ("hold", "hold_lifted", "notice", "reversal", "lift")
    basis = {"imm": "immediate", "win": "windowed"}
    for n in range(0, 4):
        for combo in itertools.product(kinds, repeat=n):
            for ts in itertools.product((0, 3, 6), repeat=n):
                H = []
                for i, (k, t) in enumerate(zip(combo, ts)):
                    r = {"k": k, "t": t, "id": "r%d" % i}
                    if k == "notice":
                        r["basis"] = "imm" if i % 2 == 0 else "win"
                    H.append(r)
                for now in (2, 9):
                    for hw in (False, True):
                        out["takedown"].append({"H": H, "now": now, "W": 4, "hold_wins": hw,
                                                "got": RX.takedown(H, now, basis, 4, hw)})
    table = {"starts": {"start"}, "excuses": {"excuse"}}
    for n in range(0, 4):
        for combo in itertools.product(("start", "excuse", "other"), repeat=n):
            for ts in itertools.product((0, 2, 5), repeat=n):
                H = [{"k": k, "t": t} for k, t in zip(combo, ts)]
                for now in (1, 4, 8):
                    out["deletion"].append({"H": H, "now": now, "W": 3, "got": RX.deletion(H, now, table, 3)})
    rows_pool = [("bind", "A", True), ("bind", "B", True), ("bind", "A", False), ("withdraw", "A", None), ("withdraw", "B", None)]
    for n in range(0, 4):
        for combo in itertools.combinations(rows_pool, n):
            H = [{"k": k, "x": x, "cos": c, "t": 0} for k, x, c in combo]
            out["owner_of"].append({"H": [{k: v for k, v in r.items() if v is not None} for r in H], "got": RX.owner_of(H)})
    gk = ("order_named", "order_minor", "order_displaced", "step_down", "bind_named", "refusal", "act_displaced", "act_named")
    for n in range(0, 4):
        for combo in itertools.combinations(gk, n):
            H = [{"k": k, "t": 0} for k in combo]
            for band in ("under_13", None, "13_15", "16_17"):
                g = RX.guardianship(H, band)
                out["guardianship"].append({"H": H, "band": band, "got": enc(g)})
    opts = ["a", "b", "c"]
    rankings = [("a",), ("b",), ("c",), ("a", "b"), ("b", "a"), ("c", "a"), ("b", "c", "a")]
    for n in range(0, 4):
        for combo in itertools.combinations_with_replacement(range(len(rankings)), n):
            for dup in (False, True):
                rows = [("p%d" % i, list(rankings[j])) for i, j in enumerate(combo)]
                if dup and rows:
                    rows.append((rows[0][0], list(rankings[(combo[0] + 1) % len(rankings)])))
                for declared in (True, False):
                    w, rounds = RX.ranked([(p, tuple(r)) for p, r in rows], opts, 2, declared)
                    out["ranked"].append({"rows": rows, "options": opts, "declared": declared, "winner": w, "rounds": rounds})
    hk = [("header", "i1", "d1", 0), ("header", "i1", "d2", 1), ("header", "i2", "d1", 5)]
    lk = [("leaf", "i1", "d1", 2), ("leaf", "i1", "d2", 3), ("leaf", "i2", "d1", 9)]
    for n in range(0, 4):
        for combo in itertools.combinations(hk + lk, n):
            H = [{"k": k, "item": it, "digest": d, "t": t, "n": "L"} for k, it, d, t in combo]
            for A in (0, 4):
                out["set_item"].append({"H": H, "leaf": "L", "A": A, "W": 3, "got": RX.set_item(H, "L", A, 3)})
    return out


# ---- causal: check.py's worlds ---------------------------------------------------------------------------------
def causal_cases():
    import check as BASE
    pools = {}
    for name, pool in BASE.POOLS.items():
        sets = []
        for idx in BASE.subsets(range(len(pool)), BASE.BOUND):
            rows = [pool[i] for i in idx]
            S = BASE.batch(rows)
            A = BASE.answers(S)
            sets.append({"idx": list(idx), "kept": [r["id"] for r in S.rows],
                         "c": [S.C[r["id"]] for r in S.rows], "a": enc(A)})
        pools[name] = {"rows": [row_enc(r) for r in pool], "sets": sets}
    return {"members": list(BASE.G["members"]), "readers": list(BASE.READERS), "depth": BASE.DEPTH, "pools": pools}


# ---- cut: check_cut.py's worlds ----------------------------------------------------------------------------------
def cut_cases():
    import check as BASE
    import check_cut as CC
    bounds = {"contest": 6, "votes_and_removal": 6, "slots_and_kinds": 5, "removal_reach_tally": 5}
    pools = {}
    for name, b in bounds.items():
        pool = CC.ALL_POOLS[name]
        sets = []
        for idx in BASE.subsets(range(len(pool)), b):
            rows = [pool[i] for i in idx]
            S = CK.concluded(CK.kept(rows), CC.rule, BASE.ROOT)
            A = CC.answers(S)
            sets.append({"idx": list(idx), "kept": [r["id"] for r in S.rows],
                         "c": [S.C[r["id"]] for r in S.rows], "a": enc(A)})
        pools[name] = {"rows": [row_enc(r) for r in pool], "sets": sets}
    return {"members": list(CC.G["members"]), "cutters": list(CC.CUTTERS), "pools": pools}


# ---- seat: every scenario attacks.py concludes, and the window adversary table --------------------------------------
KEYFIELDS = ("signer", "to", "cosigners", "subjects", "options", "ranking", "target")


def check_rows(rows, problems, where):
    """The Rust adapter types an `obj` as a row when the string is a row id of the scenario. Refuse a scenario
    where a key is spelled like a row id, and check the builders' slot fields are what the adapter derives."""
    ids = {r["id"] for r in rows}
    for r in rows:
        for f in KEYFIELDS:
            v = r.get(f)
            vs = [v] if isinstance(v, str) else list(v) if isinstance(v, (tuple, list)) else []
            if r["kind"] == "withdraw" and f == "target":
                continue
            for x in vs:
                if x in ids:
                    problems.append("%s: key %r of %s is also a row id" % (where, x, r["id"]))
        if r["kind"] in ("offer", "unseat"):
            o = r["id"] if r.get("obj") == "@" else r.get("obj")
            want = tuple(("seat", k, r["scope"], o) for k in r["to"])
            got = tuple(r.get("on", ())) if r["kind"] == "offer" else tuple(r.get("cuts", ()))
            if got != want:
                problems.append("%s: %s %s slots %r, builder gives %r" % (where, r["kind"], r["id"], got, want))


def seat_answers(S, ST, WN, CUT, CP):
    C = CUT.Cut(S)
    readers = [None] + sorted({r["signer"] for r in S.rows if r["kind"] == "ack"})
    objs = sorted({r["obj"] for r in S.rows if r["kind"] in ("offer", "unseat") and isinstance(r.get("obj"), str)})
    out = {"kept": [r["id"] for r in S.rows], "c": [S.C[r["id"]] for r in S.rows],
           "cut": [C.status(r) for r in S.rows], "readers": {}}
    for own in readers:
        Q = ST.Seats(S, own=own)
        rd = {"recs": sorted([[r["offer"], r["k"], r["scope"], r["obj"], r["depth"],
                               r["root"] if isinstance(r["root"], str) else ["group", r["root"][1]]] for r in Q.recs]),
              "stale": sorted(Q.stale), "holders": {}, "tips": {}, "duty": {}}
        for o in objs:
            rd["holders"][o] = sorted(Q.holders("member", o))
            rd["duty"][o] = sorted(Q.holders("duty", o))
            rd["tips"][o] = sorted(x["id"] for x in Q.tips(o))
        out["readers"]["-" if own is None else own] = rd
    wins = {}
    for p in K_sel(S.Cs, "open"):
        if p.get("window") in WN.WINDOWS:
            wins[p["id"]] = WN.outcome(S, p["id"], "recount")
    out["windows"] = wins
    return out


REF_FIELDS = ("obj", "over", "room")


def row_ref(i):
    """A row id in the signed object's form: [-16, digest], the digest written as hex here."""
    return [-16, hashlib.sha256(("row:" + i).encode()).hexdigest()]


def key_ref(k):
    """An identity reference: the thumbprint URN of a key, 43 base64url characters."""
    d = base64.urlsafe_b64encode(hashlib.sha256(("key:" + k).encode()).digest()).decode().rstrip("=")
    return "urn:ietf:params:oauth:ckt:sha-256:" + d


def with_refs(rows, table):
    """The rows with every object written as a reference, row or key by its form; `table` collects the names
    the references stand for, so the Rust side can turn a reference back into the model's own name."""
    ids = {r["id"] for r in rows}
    out = []
    for r in rows:
        e = row_enc(r)
        for f in REF_FIELDS:
            v = r.get(f)
            if isinstance(v, str):
                ref = row_ref(v) if v in ids else key_ref(v)
                table["|".join(map(str, ref)) if isinstance(ref, list) else ref] = v
                e[f] = ref
        out.append(e)
    return out


def K_sel(rows, kind):
    return [r for r in rows if r["kind"] == kind]


def seat_cases():
    import attacks as A
    import seat as ST
    import window as WN
    import cut as CUT
    import checkpoint as CP
    import route as RT
    rules = {id(A.SEAT): "seat", id(A.WIN): "window", id(A.ROUTE): "route"}
    seen, scen, skipped = {}, [], {"rules": 0}

    def record(rows, rule):
        name = rules.get(id(rule))
        if name is None:
            skipped["rules"] += 1
            return
        key = (name, json.dumps([row_enc(r) for r in rows], sort_keys=True))
        if key not in seen:
            seen[key] = True
            scen.append((name, list(rows)))

    orig_conc = A.conc

    def conc(rows, rule):
        record(rows, rule)
        return orig_conc(rows, rule)

    def free(rows, rule, answer, cap=1000):
        return answer(conc(rows, rule)), 0
    A.conc, A.free = conc, free
    for n in sorted(x[0] for x in A.TESTS):
        A.run_one(n)
    A.conc, A.free = orig_conc, A.free
    for world in WN.WORLDS:
        title, cases = world()
        for name, rows, prop, need in cases:
            record(rows, A.WIN)
    # a delegation chain from a counted grant: check_delegation.py's cases, under the seat rule
    import check_delegation as DG
    for _name, rows, _asks in DG.CASES:
        record(rows, A.SEAT)
    rulefn = {"seat": A.SEAT, "window": A.WIN, "route": A.ROUTE}
    problems, out = [], []
    for i, (name, rows) in enumerate(scen):
        check_rows(rows, problems, "scenario %d" % i)
        S = CK.concluded(CK.kept(list(rows)), rulefn[name])
        refs = {}
        out.append({"rule": name, "rows": with_refs(rows, refs), "refs": refs, "a": enc(seat_answers(S, ST, WN, CUT, CP))})
    law = {"duties": list(ST.DUTIES), "holds": enc(ST.HOLDS), "confers": enc(ST.CONFERS), "ends": enc(ST.ENDS),
           "final": list(ST.FINAL), "roster_seats": list(ST.ROSTER_SEATS), "depth": ST.DEPTH,
           "policy": {k: list(v) for k, v in ST.POLICY.items()}}
    windows = {k: dict(enc(v), secs=WN.secs(k)) for k, v in WN.WINDOWS.items()}
    adversary = []
    for t in WN.adversary_table():
        adversary.append({"window": t["window"], "case": t["case"], "recount": t["outcome"]["recount"],
                          "landing_concluded": t["landing_concluded"]})
    return {"law": law, "windows": windows, "scenarios": out, "adversary": adversary,
            "skipped_other_rules": skipped["rules"], "problems": problems}


# ---- tables: worlds whose conclusion rule is the instance's own --------------------------------------------------
def orders_of(rows):
    """The orders the Rust side replays: as written, reversed, and rotated by one."""
    rows = list(rows)
    out = [rows, list(reversed(rows))]
    if len(rows) > 2:
        out.append(rows[1:] + rows[:1])
    return out


def recorded(rows, rule):
    """The rule's verdict for every (row, concluded ancestors) the batch and the replayed orders ask, the kept
    set and the conclusions of the batch, and those of each replayed order."""
    table = {}

    def rec(r, P, past, *a):
        key = (r["id"], tuple(sorted(q["id"] for q in P)))
        if key not in table:
            table[key] = bool(rule(r, P, past))
        return table[key]
    S = CK.concluded(CK.kept(list(rows)), rec)
    arrivals = []
    for o in orders_of(rows):
        A = CK.arrive(o, rec)
        arrivals.append({"held": [r["id"] for r in A.rows], "c": [A.C[r["id"]] for r in A.rows]})
    return S, [[k[0], list(k[1]), v] for k, v in sorted(table.items())], arrivals


def derived_of(S, ST, WN, CUT):
    """The seat, the cut and the windows over a concluded set, as seat_answers reads them (reader none)."""
    C = CUT.Cut(S)
    Q = ST.Seats(S)
    objs = sorted({r["obj"] for r in S.rows if r["kind"] in ("offer", "unseat") and isinstance(r.get("obj"), str)})
    scopes = sorted({r["scope"] for r in S.rows if r["kind"] in ("offer", "unseat") and isinstance(r.get("scope"), str)} | {"member", "duty"})
    out = {"cut": [C.status(r) for r in S.rows], "holders": {}, "windows": {}}
    for o in objs:
        out["holders"][o] = {sc: sorted(Q.holders(sc, o)) for sc in scopes}
    for p in K_sel(S.Cs, "open"):
        if p.get("window") in WN.WINDOWS:
            out["windows"][p["id"]] = WN.outcome(S, p["id"], "recount")
    return out


def table_cases():
    import witnesses as WIT
    import seat as ST
    import window as WN
    import cut as CUT
    out = {"witnesses": [], "rosters": [], "other_rules": []}
    for c in WIT.CASES:
        worlds = [("main", c["rows"])] + [("variant " + v[0], v[1]) for v in c["variants"]] + \
                 [(f"adversary {a[0]} {w}", rows) for a in c["adversaries"] for w, rows in (("base", a[1]), ("attacked", a[2]))]
        for name, rows in worlds:
            S, table, arr = recorded(rows, c["rule"])
            refs = {}
            out["witnesses"].append({"case": c["id"], "world": name, "rows": with_refs(rows, refs), "refs": refs, "table": table,
                                     "kept": [r["id"] for r in S.rows], "c": [S.C[r["id"]] for r in S.rows], "arrivals": arr})
    # the 34 attack tests: scenarios concluded under a rule other than the seat, window and route rules
    import attacks as A
    known = {id(A.SEAT), id(A.WIN), id(A.ROUTE)}
    seen, scen = set(), []
    orig_conc = A.conc

    def conc(rows, rule):
        if id(rule) not in known:
            key = json.dumps([row_enc(r) for r in rows], sort_keys=True)
            if key not in seen:
                seen.add(key); scen.append((rows, rule))
        return orig_conc(rows, rule)
    orig_free = A.free
    A.conc, A.free = conc, (lambda rows, rule, answer, cap=1000: (answer(conc(rows, rule)), 0))
    for n in sorted(x[0] for x in A.TESTS):
        A.run_one(n)
    A.conc, A.free = orig_conc, orig_free
    for rows, rule in scen:
        S, table, arr = recorded(rows, rule)
        refs = {}
        out["other_rules"].append({"rows": with_refs(rows, refs), "refs": refs, "table": table, "kept": [r["id"] for r in S.rows],
                                   "c": [S.C[r["id"]] for r in S.rows], "arrivals": arr, "d": enc(derived_of(S, ST, WN, CUT))})
    # check_rosters: every world its unmutated properties conclude (roster.py's rule, then its settle stage)
    import check_rosters as CR
    RS = CR.RS
    depth = {"n": 0}
    orig_mut = CR.mutated

    @__import__("contextlib").contextmanager
    def mutated(*a, **kw):
        depth["n"] += 1
        try:
            with orig_mut(*a, **kw):
                yield
        finally:
            depth["n"] -= 1
    worlds, wseen = [], set()
    orig_state = RS.state

    def state(rows):
        if depth["n"] == 0 and not RS.MUT and not RS.PARAMS:
            key = json.dumps([row_enc(r) for r in rows], sort_keys=True)
            if key not in wseen:
                wseen.add(key); worlds.append(list(rows))
        return orig_state(rows)
    orig_run = CR.run
    CR.mutated, RS.state = mutated, state
    CR.run = lambda spec, worlds_, pred, orders=True, windows=lambda rows: (): orig_run(spec, worlds_, pred, False, windows)
    for name in CR.TASKS:
        if name.startswith("fork_"):
            continue
        RS.MUT.clear(); RS.PARAMS.clear()
        CR.TASKS[name](RS.instances())
    CR.mutated, RS.state, CR.run = orig_mut, orig_state, orig_run
    RS.MUT.clear(); RS.PARAMS.clear()
    RS.instances()
    for rows in worlds:
        S, table, arr = recorded(rows, RS.rule)
        P = RS.settle(S)
        refs = {}
        out["rosters"].append({"rows": with_refs(rows, refs), "refs": refs, "table": table, "kept": [r["id"] for r in S.rows],
                               "c": [S.C[r["id"]] for r in S.rows], "c_settled": [P.C[r["id"]] for r in P.rows],
                               "arrivals": arr, "d": enc(derived_of(P, ST, WN, CUT))})
    out["law"] = {"duties": list(ST.DUTIES), "holds": enc(ST.HOLDS), "confers": enc(ST.CONFERS), "ends": enc(ST.ENDS),
                  "final": list(ST.FINAL), "roster_seats": list(ST.ROSTER_SEATS), "depth": ST.DEPTH,
                  "policy": {k: list(v) for k, v in ST.POLICY.items()}}
    out["windows"] = windows_now(WN)
    return out


def windows_now(WN):
    out = {}
    for k, v in WN.WINDOWS.items():
        try:
            secs = WN.secs(k)
        except KeyError:
            secs = v.get("secs")
        e = enc(v)
        e["secs"] = secs
        out[k] = e
    return out


# ---- versions: the roster versions rule over roster_fork's worlds --------------------------------------------------
def versions_cases():
    sys.path.insert(0, os.path.join(ROOT, "models", "roster_fork"))
    import fork as FK
    import fork_check as FC
    import checkpoint as CP
    out = []
    for name, proto, n, r0, f, fo in FC.SETTINGS:
        W = FK.world("M0", n, FC.m(r0), FC.m(f), proto, FC.m(fo))
        cases = []
        for k, level in FK.enumerate_sets(W, 3):
            for S in sorted(level, key=sorted):
                for ack in [None] + sorted(S):
                    T, _ = CP.versions(sorted(S), {i: W.vs[i]["E"] for i in S}, {i: W.vs[i]["past"] for i in S}, W.valid, ack, False)
                    cases.append([sorted(S), ack, sorted(T)])
        vs = [{"E": list(v["E"]), "past": sorted(v["past"]), "valid": bool(W.valid(v["id"]))} for v in W.vs]
        out.append({"setting": name, "versions": vs, "cases": cases})
    # every call the attack tests make (their forged lines, the reader's acknowledged head), each with its world
    import attacks as A
    calls = []
    orig = A.cp_versions

    def cp_versions(W, S, ack=None, group=False):
        if not group:
            T, _ = CP.versions(sorted(S), {i: W.vs[i]["E"] for i in S}, {i: W.vs[i]["past"] for i in S}, W.valid, ack, False)
            calls.append({"setting": "attacks.py", "versions": [{"E": list(v["E"]), "past": sorted(v["past"]), "valid": bool(W.valid(v["id"]))} for v in W.vs],
                          "cases": [[sorted(S), ack, sorted(T)]]})
        return orig(W, S, ack, group)
    orig_free, orig_conc = A.free, A.conc
    A.cp_versions = cp_versions
    A.free = lambda rows, rule, answer, cap=1000: (answer(orig_conc(rows, rule)), 0)
    for n in sorted(x[0] for x in A.TESTS):
        A.run_one(n)
    A.cp_versions, A.free = orig, orig_free
    return out + calls


# ---- purge: every replay check_purge.py runs ----------------------------------------------------------------------
def purge_cases():
    import purge as P
    out = []
    for reading in ("broad", "narrow"):
        for h in P.HISTORIES:
            own, nows = h["own"], h["nows"]
            base = P.full_store(h["rows"])
            first = P.purge(base, own, h["now"], reading)
            replays = []
            for X in P.extensions(h["pool"]):
                cases = [((), first)]
                for k in range(1, len(X)):
                    for X1 in itertools.combinations(X, k):
                        cases.append((X1, P.purge(dict(P.View(first, X1, own, reading).rec), own, h["now"], reading)))
                for X1, store in cases:
                    rest = [r for r in X if r["id"] not in store]
                    for now in nows:
                        want = P.View(base, X, own, reading).answers(now)
                        got = P.View(store, rest, own, reading).answers(now)
                        replays.append({"x": [r["id"] for r in X], "x1": [r["id"] for r in X1], "now": now,
                                        "want": enc(want), "got": enc(got)})
            whole, stub = P.measure(first)
            store = {i: {"stub": bool(s.get("stub")), "final": s.get("final"), "settled_stub": bool(s.get("settled_stub")),
                         "dropped": bool(s.get("dropped")), "ackers": enc(s.get("ackers", ())), "acks": enc(s.get("acks", ()))}
                     for i, s in first.items() if i != "ck"}
            out.append({"reading": reading, "name": h["name"], "own": own, "now": h["now"], "nows": list(nows),
                        "rows": [row_enc(r) for r in h["rows"]], "pool": [row_enc(r) for r in h["pool"]],
                        "first": store, "tips": sorted(first["ck"]["names"]), "whole": whole, "stubs": stub,
                        "replays": replays})
    return out


# ---- key_end: every generated world at every instant ----------------------------------------------------------------
def key_end_cases():
    import check_key_end as CKE
    KE = CKE.KE
    worlds, pool, at = [], [], {}

    def ref(r):
        k = json.dumps(row_enc(r), sort_keys=True)
        if k not in at:
            at[k] = len(pool); pool.append(row_enc(r))
        return at[k]
    for args, rows in CKE.worlds():
        S = KE.state(rows)
        ans = []
        for now in CKE.NOWS:
            a = KE.answers(S, now, CKE.KEYS, CKE.PARTIES, CKE.SUBJECTS)
            assert all(c == bool(S.C.get(i)) for i, c, _ in a["rows"])        # "rows" repeats c; keep the retained ids
            ans.append({"live": "".join(sorted(a["live"])), "ended": "".join(sorted(a["ended"])),
                        "succ": [[k, s] for k, s in a["succ"] if s is not None],
                        "reach": [[p, "".join(sorted(r))] for p, r in a["reach"]],
                        "score": [[x, "".join(sorted(v))] for x, v in a["score"]],
                        "ret": sorted(i for i, _, _ in a["rows"])})
        worlds.append({"rows": [ref(r) for r in rows], "kept": [r["id"] for r in S.rows],
                       "c": [S.C[r["id"]] for r in S.rows], "a": ans})
    return {"ceil": KE.CEIL, "keys": list(CKE.KEYS), "parties": list(CKE.PARTIES), "subjects": list(CKE.SUBJECTS),
            "nows": list(CKE.NOWS), "required": sorted(KE.END_REQUIRED), "forbidden": sorted(KE.END_FORBIDDEN),
            "pool": pool, "worlds": worlds}


def main():
    out = {}
    dump("lib.json", lib_cases(), out)
    dump("reexpress.json", reexpress_cases(), out)
    dump("causal.json", causal_cases(), out)
    dump("cut.json", cut_cases(), out)
    seat = seat_cases()
    if seat["problems"]:
        for p in seat["problems"]:
            print("problem:", p)
        return 1
    dump("seat.json", seat, out)
    dump("purge.json", purge_cases(), out)
    dump("tables.json", table_cases(), out)
    dump("versions.json", versions_cases(), out)
    dump("key_end.json", key_end_cases(), out)
    import conferral_end as CE
    dump("conferral_end.json", CE.fixture(), out)
    out["conferral_end.tsv"] = CE.table()          # the same cases as a plain table, for the Constitution
    import conferral_content as CN
    dump("conferral_content.json", CN.fixture(), out)
    import check_conferral_content as CK
    dump("conferral_content_worlds.json", CK.worlds_fixture(), out)
    import check_conferral_two as C2
    dump("conferral_two.json", C2.fixture(), out)
    if "--check" in sys.argv:
        bad = 0
        for name, text in out.items():
            path = os.path.join(OUT, name)
            have = open(path, encoding="utf-8").read() if os.path.exists(path) else None
            if have != text:
                print("fixture out of date: %s" % name)
                bad += 1
        print("kernel_fixtures: %d fixtures, %d out of date" % (len(out), bad))
        return 1 if bad else 0
    os.makedirs(OUT, exist_ok=True)
    for name, text in out.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print("%-16s %9d bytes" % (name, len(text)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
