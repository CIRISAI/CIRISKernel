//! Differential: an affiliation's charter (the licence classes its record in force declares) and whether a reader
//! honours a licence, against `models/causal_kernel/check_charter.py` (fixture `charter.json`), with the rows as
//! listed and in reverse.

mod common;
use ciris_kernel::charter::{declared, read_licence};
use ciris_kernel::layers::{conclude, kept};
use ciris_kernel::seat::{for_reader, seat_rule, Obj, Seats};
use ciris_kernel::trust::{Accepts, Charters};
use common::{fixture, law_of, report, rows_with_refs, DictCut, TRow, J};
use std::collections::BTreeMap;

fn refs_of(c: &J) -> BTreeMap<String, String> {
    c.at("refs").obj().iter().map(|(k, v)| (k.clone(), v.s().to_string())).collect()
}

/// A name of the case as an object: a row where a row of the case has that id, a key otherwise.
fn obj(rows: &[TRow], n: &str) -> Obj<String, String> {
    if rows.iter().any(|r| r.id == n) {
        Obj::Row(n.to_string())
    } else {
        Obj::Key(n.to_string())
    }
}

#[test]
fn charter_replay() {
    let fx = fixture("charter.json");
    let law = law_of(fixture("seat.json").at("law"));
    let spec = DictCut;
    let (mut cases, mut bad) = (0, 0);
    for c in fx.at("declared").arr() {
        let rows = rows_with_refs(c.at("rows").arr(), &refs_of(c));
        let want: Option<Vec<String>> = c.get("declared").filter(|x| !x.is_null()).map(|x| x.strs());
        let own: Option<String> = c.get("own").filter(|x| !x.is_null()).map(|x| x.s().to_string());
        for rev in [false, true] {
            let mut rs = rows.clone();
            if rev {
                rs.reverse();
            }
            let cc = conclude(kept(&rs, |_| true), |p| seat_rule(p, &law, &spec, &|_| true), None);
            let (rc, rv) = for_reader(&cc, &law, &spec, own.as_ref());
            let q = match &own {
                Some(k) => Seats::for_reader(&rc, &law, &spec, k, &rv),
                None => Seats::new(&rc, &law, &spec, None),
            };
            let got = declared(&q, &c.at("aff").s().to_string()).map(|d| d.into_iter().collect::<Vec<_>>());
            cases += 1;
            if got != want {
                bad += 1;
                eprintln!("declared {} (reversed: {rev}): got {got:?}, want {want:?}", c.at("name").s());
            }
        }
    }
    for c in fx.at("licences").arr() {
        let rows = rows_with_refs(c.at("rows").arr(), &refs_of(c));
        let edges: Vec<Accepts<Obj<String, String>, String>> = c
            .at("edges")
            .arr()
            .iter()
            .map(|e| {
                let e = e.arr();
                Accepts {
                    src: obj(&rows, e[0].s()),
                    dst: obj(&rows, e[1].s()),
                    classes: e[2].strs(),
                    depth: e[3].i() as u32,
                }
            })
            .collect();
        let mut supplied = Charters::new();
        for (a, cs) in c.at("supplied").obj() {
            supplied.meet(obj(&rows, a), cs.strs());
        }
        let want = if c.at("honoured").b() { None } else { Some(c.at("reason").s().to_string()) };
        let reader = obj(&rows, c.at("reader").s());
        let auth = obj(&rows, c.at("authority").s());
        let cls = c.at("class").s().to_string();
        for rev in [false, true] {
            let mut rs = rows.clone();
            if rev {
                rs.reverse();
            }
            let cc = conclude(kept(&rs, |_| true), |p| seat_rule(p, &law, &spec, &|_| true), None);
            let (rc, _) = for_reader(&cc, &law, &spec, None);
            let q = Seats::new(&rc, &law, &spec, None);
            let got = read_licence(&q, &edges, &reader, &auth, &cls, &supplied).err().map(|u| u.word().to_string());
            // the licence row is admitted, whatever the reading
            let lic = cc.g.idx(&c.at("licence").s().to_string()).expect("the licence row is kept");
            cases += 2;
            if !cc.concluded(lic) || !c.at("admitted").b() {
                bad += 1;
                eprintln!("licence {} (reversed: {rev}): the licence row is not admitted", c.at("name").s());
            }
            if got != want {
                bad += 1;
                eprintln!("licence {} (reversed: {rev}): got {got:?}, want {want:?}", c.at("name").s());
            }
        }
    }
    report("charter coverage against check_charter.py", cases, bad);
    assert_eq!(bad, 0);
}
