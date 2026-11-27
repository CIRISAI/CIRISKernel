import sys
root = sys.argv[1]
p = root + '/tools/kernel_fixtures.py'
s = open(p).read()


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a, s.count(a))
    s = s.replace(a, b)


rep('''    seen, scen, skipped = {}, [], {"rules": 0}

    def record(rows, rule):
        name = rules.get(id(rule))
        if name is None:
            skipped["rules"] += 1
            return
        key = (name, json.dumps([row_enc(r) for r in rows], sort_keys=True))
        if key not in seen:
            seen[key] = True
            scen.append((name, list(rows)))
''', '''    seen, scen, skipped = {}, [], {"rules": 0}

    def record(rows, rule, asks=None, table=None):
        """`asks`: (key, scope, object) the scenario also states `stands` for. `table`: read under another HOLDS
        (check_duty_seats.py's `persist`); the scenario then carries its own `holds`."""
        name = rules.get(id(rule))
        if name is None:
            skipped["rules"] += 1
            return
        key = (name, table, json.dumps([row_enc(r) for r in rows], sort_keys=True))
        if key not in seen:
            seen[key] = True
            scen.append((name, list(rows), list(asks or ()), table))
''')
rep('''    for _name, rows, _asks in DG.CASES:
        record(rows, A.SEAT)
''', '''    for _name, rows, _asks in DG.CASES:
        record(rows, A.SEAT)
    # a duty seat stands only on a member: check_duty_seats.py's cases, under the seat rule, each with the standing
    # it asks for; the cases of persist's table carry that table
    import check_duty_seats as DS
    for _name, rows, asks, tab in DS.CASES:
        record(rows, A.SEAT, [(k, sc, DS.OBJ) for k, sc, _ in asks], tab)
''')
rep('''    for i, (name, rows) in enumerate(scen):
        check_rows(rows, problems, "scenario %d" % i)
        S = CK.concluded(CK.kept(list(rows)), rulefn[name])
        refs = {}
        out.append({"rule": name, "rows": with_refs(rows, refs), "refs": refs, "a": enc(seat_answers(S, ST, WN, CUT, CP))})
''', '''    for i, (name, rows, asks, tab) in enumerate(scen):
        check_rows(rows, problems, "scenario %d" % i)
        with DS.table(tab):
            S = CK.concluded(CK.kept(list(rows)), rulefn[name])
            refs = {}
            e = {"rule": name, "rows": with_refs(rows, refs), "refs": refs, "a": enc(seat_answers(S, ST, WN, CUT, CP))}
            if asks:
                Q = ST.Seats(S)
                e["stands"] = [[k, sc, o, Q.stands(k, sc, o)] for k, sc, o in asks]
            if tab:
                e["holds"] = enc(ST.HOLDS)
        out.append(e)
''')
open(p, 'w').write(s)

p = root + '/crates/ciris-kernel/tests/seat.rs'
s = open(p).read()
rep('''        let a = sc.at("a");
        let c = conclude(kept(&rows, |_| true), |p| w.rule(&name, p), None);''', '''        let a = sc.at("a");
        // a scenario read under another table of what a seat holds carries it (`holds`)
        let own_law = sc.get("holds").map(|h| World { law: SeatLaw { holds: holds_of(h), ..w.law.clone() }, windows: w.windows.clone() });
        let w = own_law.as_ref().unwrap_or(&w);
        let c = conclude(kept(&rows, |_| true), |p| w.rule(&name, p), None);''')
rep('''        for (pid, want) in a.at("windows").obj() {''', '''        // the standing a scenario asks for by name (check_duty_seats.py's cases)
        if let Some(asks) = sc.get("stands") {
            let q = Seats::new(&c, &w.law, &spec, None);
            for ask in asks.arr() {
                let (k, s, o, want) = (ask.arr()[0].s(), ask.arr()[1].s(), ask.arr()[2].s(), ask.arr()[3].b());
                let got = q.stands(&k.to_string(), s, &obj_named(&rows, o), None);
                cmp(got == want, format!("{k} stands in {s} over {o}"));
            }
        }
        for (pid, want) in a.at("windows").obj() {''')
open(p, 'w').write(s)
