//! Differential: a key's person at a row (`seat::person_at`), against `models/causal_kernel/check_key_person.py`
//! (fixture `key_person.json`): each case's rows concluded under the seat rule, the person read at the row `at`.

mod common;
use ciris_kernel::cut::{Cut, CutSpec};
use ciris_kernel::key_end::KeyView;
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
        let want = case.at("person").opt_s().map(Obj::Key);
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

/// A key view given as a table: every (row, key) signature counts but those listed (the fixture's `uncounted`).
struct TableView(BTreeSet<(String, String)>);

impl KeyView<String, String> for TableView {
    fn counts(&self, row: &String, key: &String) -> bool {
        !self.0.contains(&(row.clone(), key.clone()))
    }
}

/// DictCut, with a key view.
struct KeyCut<'k> {
    kv: Option<&'k dyn KeyView<String, String>>,
}

impl CutSpec<TRow> for KeyCut<'_> {
    type Slot = J;
    type Say = J;
    fn key_slot(&self, k: &String) -> J {
        DictCut.key_slot(k)
    }
    fn on_slots(&self, r: &TRow) -> BTreeSet<J> {
        DictCut.on_slots(r)
    }
    fn cuts_of(&self, r: &TRow) -> BTreeSet<J> {
        DictCut.cuts_of(r)
    }
    fn says(&self, r: &TRow) -> J {
        DictCut.says(r)
    }
    fn need(&self, r: &TRow) -> usize {
        DictCut.need(r)
    }
    fn rejects(&self, r: &TRow) -> Vec<String> {
        DictCut.rejects(r)
    }
    fn is_voice_for(&self, cosign: &TRow, cut: &TRow) -> bool {
        DictCut.is_voice_for(cosign, cut)
    }
    fn key_view(&self) -> Option<&dyn KeyView<String, String>> {
        self.kv
    }
}

/// K1 on the person line (check_key_person.py's KV_LINE_CASES, fixture section `line_key_view`): the reader's own
/// rows seed its roster line only where its key's signature counts by the key view the spec carries. A thief's row
/// with p4's revoked key reaches the rival S1r: with the view (the table not counting p4 on it) p4's line takes up S1
/// and the admission concludes for p4; with no view, the thief's row seeds the line and p4 waits.
#[test]
fn the_person_line_reads_the_key_view() {
    let fx = fixture("key_person.json");
    let law = law_of(fx.at("law"));
    let (mut cases, mut bad) = (0usize, 0usize);
    for case in fx.at("line_key_view").arr() {
        let refs: BTreeMap<String, String> =
            case.at("refs").obj().iter().map(|(k, v)| (k.clone(), v.s().to_string())).collect();
        let rows = rows_with_refs(case.at("rows").arr(), &refs);
        let reader = case.at("reader").s().to_string();
        let rid = case.at("row").s().to_string();
        let want = case.at("concludes").b();
        let table = case.get("uncounted").filter(|u| !matches!(u, J::Null)).map(|u| {
            TableView(u.arr().iter().map(|x| (x.arr()[0].s().to_string(), x.arr()[1].s().to_string())).collect())
        });
        let spec = KeyCut { kv: table.as_ref().map(|t| t as &dyn KeyView<String, String>) };
        for reversed in [false, true] {
            let mut rs = rows.clone();
            if reversed {
                rs.reverse();
            }
            let c = conclude(kept(&rs, |_| true), |p| seat_rule(p, &law, &spec, &|_| true), None);
            let (rc, _) = ciris_kernel::seat::for_reader(&c, &law, &spec, Some(&reader));
            let got = rc.g.idx(&rid).is_some_and(|i| rc.concluded(i));
            cases += 1;
            if got != want {
                bad += 1;
                eprintln!("  {}: concluded {got}, expected {want}", case.at("name").s());
            }
        }
    }
    report("the person line reads the key view (check_key_person.py)", cases, bad);
    assert!(cases > 0);
    assert_eq!(bad, 0);
}
