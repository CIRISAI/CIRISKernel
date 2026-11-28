//! The key view (`CutSpec::key_view`): the end rule read at the voices step of every seat count, against
//! `models/causal_kernel/check_key_view.py` (fixture `key_end_counts.json`). Each case: `key_end::counts_by` per (row,
//! key) over one causal order of the seat and key lanes, and the voices and conclusion of the counted row `x` with
//! the key view or, for the documented default, without it.

mod common;
use ciris_kernel::cut::CutSpec;
use ciris_kernel::key_end::{conclude_rule, counts_by, KeyReading, KeyView};
use ciris_kernel::layers::{conclude, kept, Past};
use ciris_kernel::seat::{seat_rule, voices_with, SeatLaw};
use common::*;
use std::collections::{BTreeMap, BTreeSet};

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

#[test]
fn key_view_cases() {
    let fx = fixture("key_end_counts.json");
    let law: SeatLaw = law_of(fx.at("law"));
    let (mut cases, mut bad) = (0, 0);
    for c in fx.at("cases").arr() {
        let name = c.at("name").s();
        let refs: BTreeMap<String, String> =
            c.at("refs").obj().iter().map(|(k, v)| (k.clone(), v.s().to_string())).collect();
        let all = rows_with_refs(c.at("rows").arr(), &refs);
        let seat_ids: BTreeSet<String> = c.at("seat").strs().into_iter().collect();
        let seat_rows: Vec<TRow> = all.iter().filter(|r| seat_ids.contains(&r.id)).cloned().collect();
        // the key lane and the seat rows, in one causal order
        let kc = conclude(kept(&all, |_| true), conclude_rule, None);
        let mut cmp = |ok: bool, what: String| {
            cases += 1;
            if !ok {
                bad += 1;
                eprintln!("{name}: {what}");
            }
        };
        for e in c.at("counts").arr() {
            let (row, key, want) = (e.arr()[0].s().to_string(), e.arr()[1].s().to_string(), e.arr()[2].b());
            let got = kc.g.idx(&row).is_some_and(|i| counts_by(&kc, i, &key));
            cmp(got == want, format!("counts_by({row}, {key})"));
        }
        let reading = KeyReading { c: &kc };
        let spec = KeyCut { kv: if c.at("view").b() { Some(&reading) } else { None } };
        let sc = conclude(kept(&seat_rows, |_| true), |p| seat_rule(p, &law, &spec, &|_| true), None);
        let x = sc.g.idx(&"x".to_string()).expect("x");
        let anc: Vec<usize> = sc.cs().iter().copied().filter(|&q| sc.g.in_past(q, x)).collect();
        let p = Past::new(&sc.g, x, &anc);
        let v: Vec<String> = voices_with(sc.g.row(x), &p, &spec).into_iter().collect();
        cmp(v == c.at("voices").strs(), format!("voices of x: {v:?}"));
        cmp(sc.concluded(x) == c.at("concluded").b(), "x concluded".into());
    }
    report("the key view (check_key_view.py)", cases, bad);
    assert_eq!(bad, 0);
}
