//! Differential: the reader's trust walk from acceptance edge rows and the issuer's standing, against
//! `models/causal_kernel/check_trust_rows.py` (fixture `trust_rows.json`), under the Constitution's rulings (a) to (d)
//! of 2026-11-27, with the rows as listed and in reverse.

mod common;
use ciris_kernel::layers::{conclude, kept};
use ciris_kernel::seat::{for_reader, seat_rule, Obj, Seats};
use ciris_kernel::trust::Charters;
use ciris_kernel::trust_rows::{read_licence, refusal};
use common::{fixture, law_of, report, rows_with_refs, DictCut, TRow, J};
use std::collections::BTreeMap;

fn refs_of(c: &J) -> BTreeMap<String, String> {
    c.at("refs").obj().iter().map(|(k, v)| (k.clone(), v.s().to_string())).collect()
}

fn obj(rows: &[TRow], n: &str) -> Obj<String, String> {
    if rows.iter().any(|r| r.id == n) {
        Obj::Row(n.to_string())
    } else {
        Obj::Key(n.to_string())
    }
}

#[test]
fn trust_rows_replay() {
    let fx = fixture("trust_rows.json");
    let law = law_of(fixture("seat.json").at("law"));
    let spec = DictCut;
    let (mut cases, mut bad) = (0, 0);
    for c in fx.at("cases").arr() {
        let rows = rows_with_refs(c.at("rows").arr(), &refs_of(c));
        let mut supplied = Charters::new();
        for (a, cs) in c.at("supplied").obj() {
            supplied.meet(obj(&rows, a), cs.strs());
        }
        let want = if c.at("honoured").b() { None } else { Some(c.at("reason").s().to_string()) };
        let reader = obj(&rows, c.at("reader").s());
        let lic = c.at("licence").s().to_string();
        for rev in [false, true] {
            let mut rs = rows.clone();
            if rev {
                rs.reverse();
            }
            let cc = conclude(kept(&rs, |_| true), |p| seat_rule(p, &law, &spec, &|_| true), None);
            let (rc, _) = for_reader(&cc, &law, &spec, None);
            let q = Seats::new(&rc, &law, &spec, None);
            let now: Option<i64> = c.get("now").filter(|x| !x.is_null()).map(|x| x.i());
            let got = read_licence(&q, &reader, &lic, &supplied, now.as_ref()).err().map(|u| u.word().to_string());
            cases += 2;
            if !cc.concluded_id(&lic) {
                bad += 1;
                eprintln!("{} (reversed: {rev}): the licence row is not admitted", c.at("name").s());
            }
            if got != want {
                bad += 1;
                eprintln!("{} (reversed: {rev}): got {got:?}, want {want:?}", c.at("name").s());
            }
        }
    }
    for c in fx.at("refusals").arr() {
        let rows = rows_with_refs(c.at("rows").arr(), &refs_of(c));
        let want = c.get("refusal").filter(|x| !x.is_null()).map(|x| x.s().to_string());
        let got = refusal(&rows[0]).map(str::to_string);
        cases += 1;
        if got != want {
            bad += 1;
            eprintln!("refusal {}: got {got:?}, want {want:?}", c.at("name").s());
        }
    }
    report("the trust walk from rows against check_trust_rows.py", cases, bad);
    assert_eq!(bad, 0);
}
