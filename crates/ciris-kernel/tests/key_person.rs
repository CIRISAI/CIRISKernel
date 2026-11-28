//! Differential: a key's person at a row (`seat::person_at`), against `models/causal_kernel/check_key_person.py`
//! (fixture `key_person.json`): each case's rows concluded under the seat rule, the person read at the row `at`.

mod common;
use ciris_kernel::cut::Cut;
use ciris_kernel::layers::{conclude, kept};
use ciris_kernel::seat::{nodes_of, person_at, person_keys, seat_rule, Obj};
use ciris_kernel::window::{self, Outcome};
use common::*;
use std::collections::{BTreeMap, BTreeSet};

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

#[test]
fn a_count_is_over_persons() {
    let fx = fixture("key_person.json");
    let law = law_of(fx.at("law"));
    let (mut cases, mut bad) = (0usize, 0usize);
    for case in fx.at("counts").arr() {
        let refs: BTreeMap<String, String> =
            case.at("refs").obj().iter().map(|(k, v)| (k.clone(), v.s().to_string())).collect();
        let rows = rows_with_refs(case.at("rows").arr(), &refs);
        let rid = case.at("row").s().to_string();
        let want = case.at("concludes").b();
        for reversed in [false, true] {
            let mut rs = rows.clone();
            if reversed {
                rs.reverse();
            }
            let c = conclude(kept(&rs, |_| true), |p| seat_rule(p, &law, &DictCut, &|_| true), None);
            let got = c.g.idx(&rid).is_some_and(|i| c.concluded(i));
            cases += 1;
            if got != want {
                bad += 1;
                eprintln!("  {}: concluded {got}, expected {want}", case.at("name").s());
            }
        }
    }
    report("a count over persons (check_key_person.py)", cases, bad);
    assert_eq!(bad, 0);
}

/// The opener's own withdrawal (the review r78k): a window table entry of the fixture's own that reads the opener's
/// withdrawal over a member count; an opener whose key revoked itself (a key of no person) still withdraws as itself,
/// with no voter needed, as `window.py` reads it.
#[test]
fn the_openers_own_withdrawal() {
    let fx = fixture("key_person.json");
    let law = law_of(fx.at("law"));
    let windows = windows_of(fx.at("windows"));
    let tables = |w: &String| windows.get(w).cloned();
    let spec = DictCut;
    let (mut cases, mut bad) = (0usize, 0usize);
    for case in fx.at("window_cases").arr() {
        let refs: BTreeMap<String, String> =
            case.at("refs").obj().iter().map(|(k, v)| (k.clone(), v.s().to_string())).collect();
        let rows = rows_with_refs(case.at("rows").arr(), &refs);
        let want = case.at("outcome").s().to_string();
        for reversed in [false, true] {
            let mut rs = rows.clone();
            if reversed {
                rs.reverse();
            }
            let c = conclude(
                kept(&rs, |_| true),
                |p| window::rule(p, &tables, &law, &spec).unwrap_or_else(|| seat_rule(p, &law, &spec, &|_| true)),
                None,
            );
            let cut = Cut::new(&c, &spec);
            let i = c.g.idx(&case.at("opener").s().to_string()).expect("the opener");
            let got = match window::outcome(&c, i, &tables, &law, &spec, &|j| cut.counts(j)) {
                Outcome::None => "none".to_string(),
                Outcome::Open => "open".to_string(),
                Outcome::Contested => "contested".to_string(),
                Outcome::Landed(s) => s,
            };
            cases += 1;
            if got != want {
                bad += 1;
                eprintln!("  {}: got {got}, expected {want}", case.at("name").s());
            }
        }
    }
    report("the opener's own withdrawal (check_key_person.py)", cases, bad);
    assert_eq!(bad, 0);
}

/// The keys a row reaches, for persist (the node set = audiences ∘ person_keys ∘ nodes_of): a person's live keys
/// (`seat::person_keys`) and an owner's nodes (`seat::nodes_of`) over the concluded set, against `seat.person_keys`
/// and `seat.nodes_of` (fixture sections `person_keys` and `nodes_of`), the rows as listed and in reverse.
#[test]
fn a_persons_keys_and_an_owners_nodes() {
    let fx = fixture("key_person.json");
    let law = law_of(fx.at("law"));
    let (mut cases, mut bad) = (0usize, 0usize);
    for (section, who, what) in [("person_keys", "person", "keys"), ("nodes_of", "owner", "nodes")] {
        for case in fx.at(section).arr() {
            let refs: BTreeMap<String, String> =
                case.at("refs").obj().iter().map(|(k, v)| (k.clone(), v.s().to_string())).collect();
            let rows = rows_with_refs(case.at("rows").arr(), &refs);
            let k = case.at(who).s().to_string();
            let want: BTreeSet<String> = case.at(what).strs().into_iter().collect();
            for reversed in [false, true] {
                let mut rs = rows.clone();
                if reversed {
                    rs.reverse();
                }
                let c = conclude(kept(&rs, |_| true), |p| seat_rule(p, &law, &DictCut, &|_| true), None);
                let got = if section == "person_keys" {
                    person_keys(&c, &law, &DictCut, &k)
                } else {
                    nodes_of(&c, &law, &DictCut, &k)
                };
                cases += 1;
                if got != want {
                    bad += 1;
                    eprintln!("  {section} {}: got {got:?}, expected {want:?}", case.at("name").s());
                }
            }
        }
    }
    report("a person's keys and an owner's nodes (check_key_person.py)", cases, bad);
    assert_eq!(bad, 0);
}
