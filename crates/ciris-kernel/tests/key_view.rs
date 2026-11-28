//! The key view (`CutSpec::key_view`): the end rule read at the voices step of every seat count, against
//! `models/causal_kernel/check_key_view.py` (fixture `key_end_counts.json`). Each case: `key_end::counts_by` per (row,
//! key) over one causal order of the seat and key lanes, and the voices and conclusion of the counted row `x` with
//! the key view or, for the documented default, without it.

mod common;
use ciris_kernel::cut::CutSpec;
use ciris_kernel::key_end::{conclude_rule, counts_by, counts_for, KeyEndRow, KeyReading, KeyView};
use ciris_kernel::layers::{conclude, kept, Concluded, Past};
use ciris_kernel::seat::{final_by_ack, seat_rule, voices_with, Obj, SeatLaw, Seats};
use ciris_kernel::window::{self, WindowSpec};
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

/// The seat rows concluded under the seat rule (or, for a window case, the window rule first) with `spec`.
fn conclude_rows<'r>(
    rows: &'r [TRow],
    win: bool,
    windows: &BTreeMap<String, WindowSpec<i64>>,
    law: &SeatLaw,
    spec: &KeyCut<'_>,
) -> Concluded<'r, TRow> {
    conclude(
        kept(rows, |_| true),
        |p| {
            if win {
                if let Some(v) = window::rule(p, &|w| windows.get(w).cloned(), law, spec) {
                    return v;
                }
            }
            seat_rule(p, law, spec, &|_| true)
        },
        None,
    )
}

#[test]
fn key_view_cases() {
    let fx = fixture("key_end_counts.json");
    let law: SeatLaw = law_of(fx.at("law"));
    let windows: BTreeMap<String, WindowSpec<i64>> = windows_of(fx.at("windows"));
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
        let win = c.at("rule").s() == "window";
        let conclude_with = |spec: &KeyCut<'_>| conclude_rows(&seat_rows, win, &windows, &law, spec);
        // the counts final by acknowledgement, over the rows as they conclude with no key view
        let plain = KeyCut { kv: None };
        let c0 = conclude_with(&plain);
        // the self roster's acts concluded under the roster's own count, and the counts final over clean receipts
        let roster: BTreeSet<String> =
            c0.cs().iter().map(|&i| c0.g.row(i)).filter(|r| r.roster_end().is_some()).map(|r| r.id.clone()).collect();
        let final_: BTreeSet<String> = (0..c0.g.len())
            .filter(|&i| final_by_ack(&c0, &law, &plain, i, Some((&kc, &roster))))
            .map(|i| c0.g.row(i).id.clone())
            .collect();
        if let Some(f) = c.get("final") {
            let want: BTreeSet<String> = f.strs().into_iter().collect();
            cmp(final_ == want, format!("final by acknowledgement: {final_:?}"));
        }
        let reader = c.get("reader").and_then(|r| r.opt_s());
        let reading = KeyReading { c: &kc, reader, final_, roster };
        let spec = KeyCut { kv: if c.at("view").b() { Some(&reading) } else { None } };
        let sc = conclude_with(&spec);
        // the row whose conclusion is read (x, or the case's probe), and a seat asked
        let probe = c.get("probe").map(|p| p.opt_s()).unwrap_or(Some("x".into()));
        if let Some(pr) = &probe {
            let i = sc.g.idx(pr).expect("the probe");
            cmp(sc.concluded(i) == c.at("concluded").b(), format!("{pr} concluded"));
        }
        if let Some(st) = c.get("stands") {
            let a = st.arr();
            let q = Seats::new(&sc, &law, &spec, None);
            let got = q.stands(&a[0].s().to_string(), a[1].s(), &Obj::Row(a[2].s().to_string()), None);
            cmp(got == a[3].b(), format!("{} stands in {} over {}", a[0].s(), a[1].s(), a[2].s()));
        }
        let Some(x) = sc.g.idx(&"x".to_string()) else { continue };
        if let Some(want) = c.get("voices").filter(|v| !v.is_null()) {
            let anc: Vec<usize> = sc.cs().iter().copied().filter(|&q| sc.g.in_past(q, x)).collect();
            let p = Past::new(&sc.g, x, &anc);
            let v: Vec<String> = voices_with(sc.g.row(x), &p, &spec).into_iter().collect();
            cmp(v == want.strs(), format!("voices of x: {v:?}"));
        }
    }
    // a voice valid when cast, whatever final set a caller gives (DIRECT)
    for d in fx.at("direct").arr() {
        let refs: BTreeMap<String, String> =
            d.at("refs").obj().iter().map(|(k, v)| (k.clone(), v.s().to_string())).collect();
        let rows = rows_with_refs(d.at("rows").arr(), &refs);
        let kc = conclude(kept(&rows, |_| true), conclude_rule, None);
        let final_: BTreeSet<String> = d.at("final").strs().into_iter().collect();
        let (row, key) = (d.at("row").s().to_string(), d.at("key").s().to_string());
        let got = kc.g.idx(&row).is_some_and(|i| counts_for(&kc, i, &key, None, &final_, &BTreeSet::new()));
        cases += 1;
        if got != d.at("want").b() {
            bad += 1;
            eprintln!("{}: counts_for = {got}", d.at("name").s());
        }
    }
    report("the key view (check_key_view.py)", cases, bad);
    assert_eq!(bad, 0);
}
