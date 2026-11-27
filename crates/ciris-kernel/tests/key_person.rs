//! Differential: a key's person at a row (`seat::person_at`), against `models/causal_kernel/check_key_person.py`
//! (fixture `key_person.json`): each case's rows concluded under the seat rule, the person read at the row `at`.

mod common;
use ciris_kernel::layers::{conclude, kept};
use ciris_kernel::seat::{person_at, seat_rule, Obj};
use common::*;
use std::collections::BTreeMap;

#[test]
fn a_key_to_its_person_at_a_row() {
    let fx = fixture("key_person.json");
    let law = law_of(fx.at("law"));
    let (mut cases, mut bad) = (0usize, 0usize);
    for case in fx.at("cases").arr() {
        let refs: BTreeMap<String, String> =
            case.at("refs").obj().iter().map(|(k, v)| (k.clone(), v.s().to_string())).collect();
        let rows = rows_with_refs(case.at("rows").arr(), &refs);
        let key = case.at("key").s().to_string();
        let want = case.at("person").opt_s().map(Obj::Row);
        for reversed in [false, true] {
            let mut rs = rows.clone();
            if reversed {
                rs.reverse();
            }
            let c = conclude(kept(&rs, |_| true), |p| seat_rule(p, &law, &DictCut, &|_| true), None);
            let i = c.g.idx(&"at".to_string()).expect("the row asked at");
            let got = person_at(&c, i, &law, &DictCut, &key);
            cases += 1;
            if got != want {
                bad += 1;
                eprintln!("  {}: got {got:?}, expected {want:?}", case.at("name").s());
            }
        }
    }
    report("a key's person at a row (check_key_person.py)", cases, bad);
    assert_eq!(bad, 0);
}
