//! Rows whose names close a cycle are not a kept set (`layers::kept` never keeps them). `graph::Graph` still
//! ends on them: a row on a cycle, or naming one, waits, and `layers::conclude` concludes nothing for it, as
//! it would for those rows left out by `kept`.

mod common;
#[path = "common/dag.rs"]
mod dag;
use ciris_kernel::graph::Graph;
use ciris_kernel::layers::{conclude, kept};
use common::report;
use dag::{Lcg, N};
use std::collections::BTreeSet;

fn n(id: u32, names: &[u32]) -> N {
    N { id, names: names.to_vec(), signer: 0 }
}

fn concluded_ids(rows: &[N]) -> BTreeSet<u32> {
    let c = conclude(rows.iter(), |_| true, None);
    c.cs().iter().map(|&i| c.g.row(i).id).collect()
}

fn waiting_ids(rows: &[N]) -> BTreeSet<u32> {
    let g = Graph::new(rows.iter());
    (0..g.len()).filter(|&i| g.waiting(i)).map(|i| g.row(i).id).collect()
}

#[test]
fn a_cycle_ends_and_concludes_nothing() {
    // two rows naming each other
    let two = [n(1, &[2]), n(2, &[1])];
    assert_eq!(waiting_ids(&two), [1, 2].into());
    assert!(concluded_ids(&two).is_empty());
    // three, a row naming into the cycle, a row the cycle names, and one apart
    let three = [n(1, &[2]), n(2, &[3]), n(3, &[1, 5]), n(4, &[2]), n(5, &[]), n(6, &[5])];
    assert_eq!(waiting_ids(&three), [1, 2, 3, 4].into());
    assert_eq!(concluded_ids(&three), [5, 6].into());
    // a row naming its own id is a cycle of one
    let own = [n(1, &[1]), n(2, &[1]), n(3, &[])];
    assert_eq!(waiting_ids(&own), [1, 2].into());
    assert_eq!(concluded_ids(&own), [3].into());
    // the closure's other questions end on them too
    let g = Graph::new(three.iter());
    for a in 0..g.len() {
        let _ = g.ancestors(a).len();
        for b in 0..g.len() {
            let _ = g.in_past(a, b) || g.concurrent(a, b);
        }
    }
    let all: Vec<usize> = (0..g.len()).collect();
    let _ = g.frontier(&all);
}

/// Over generated rows that name any row, cycles included: what `conclude` concludes over all of them is
/// what it concludes over the rows `kept` keeps, under a rule that reads the past.
#[test]
fn conclude_over_cycles_is_conclude_over_what_kept_keeps() {
    let (mut cases, mut bad) = (0usize, 0usize);
    let mut g = Lcg(17);
    for _ in 0..4_000 {
        let m = 1 + (g.next() % 24) as u32;
        let mut rows: Vec<N> = Vec::new();
        for i in 0..m {
            let mut names = Vec::new();
            for _ in 0..g.next() % 3 {
                // mostly an earlier row, sometimes any row (a later one, or itself)
                let x = if g.next().is_multiple_of(5) { g.next() % m as u64 } else { g.next() % (i as u64 + 1) } as u32;
                if x != i || g.next().is_multiple_of(2) {
                    names.push(x);
                }
            }
            rows.push(N { id: i, names, signer: (g.next() % 4) as u32 });
        }
        let rule = |p: &ciris_kernel::layers::Past<'_, '_, N>| (p.ancestors().len() + p.row().signer as usize) % 3 != 1;
        let all = conclude(rows.iter(), rule, None);
        let held = kept(&rows, |_| true);
        let some = conclude(held.iter().copied(), rule, None);
        let ids = |c: &ciris_kernel::layers::Concluded<'_, N>| -> BTreeSet<u32> {
            c.cs().iter().map(|&i| c.g.row(i).id).collect()
        };
        cases += 1;
        bad += (ids(&all) != ids(&some)) as usize;
        // and a row waits exactly when kept leaves it out
        let kept_ids: BTreeSet<u32> = held.iter().map(|r| r.id).collect();
        let gr = Graph::new(rows.iter());
        for i in 0..gr.len() {
            cases += 1;
            bad += (gr.waiting(i) == kept_ids.contains(&gr.row(i).id)) as usize;
        }
    }
    report("conclude over rows with cycles of names, against conclude over what kept keeps", cases, bad);
    assert_eq!(bad, 0);
}

type E = ciris_kernel::head::Entry<u32, u32, i64>;

fn store(rows: &[N]) -> std::collections::BTreeMap<u32, E> {
    rows.iter()
        .map(|r| {
            let kind = if r.signer == 0 { ciris_kernel::head::Kind::Other } else { ciris_kernel::head::Kind::Seat };
            (r.id, E::new(r.id, kind, r.signer, r.names.clone()))
        })
        .collect()
}

fn viewed(rows: &[N]) -> BTreeSet<u32> {
    use ciris_kernel::head::{purge, Reading, View};
    let s = store(rows);
    let v = View::new(&s, &[], 0, Reading::Broad, true);
    let _ = v.answers(10);
    let _ = v.tips();
    let (p, _) = purge(&s, 0, 10, Reading::Broad);
    let held: BTreeSet<u32> = v.rec().keys().copied().collect();
    assert_eq!(p.keys().copied().collect::<BTreeSet<u32>>(), held, "the purge keeps what the view holds");
    held
}

#[test]
fn a_view_of_a_store_with_a_cycle_ends_and_leaves_it_out() {
    assert!(viewed(&[n(1, &[2]), n(2, &[1])]).is_empty());
    let three = [n(1, &[2]), n(2, &[3]), n(3, &[1, 5]), n(4, &[2]), n(5, &[]), n(6, &[5])];
    assert_eq!(viewed(&three), [5, 6].into());
    assert_eq!(viewed(&[n(1, &[1]), n(2, &[1]), n(3, &[])]), [3].into());
}

/// Over generated stores whose entries name any entry: the view holds exactly the entries `kept` keeps.
#[test]
fn a_view_holds_what_kept_keeps() {
    let (mut cases, mut bad) = (0usize, 0usize);
    let mut g = Lcg(23);
    for _ in 0..3_000 {
        let m = 1 + (g.next() % 20) as u32;
        let mut rows: Vec<N> = Vec::new();
        for i in 0..m {
            let mut names = Vec::new();
            for _ in 0..g.next() % 3 {
                let x = if g.next().is_multiple_of(4) { g.next() % m as u64 } else { g.next() % (i as u64 + 1) } as u32;
                if x != i || g.next().is_multiple_of(2) {
                    names.push(x);
                }
            }
            names.sort_unstable();
            names.dedup();
            rows.push(N { id: i, names, signer: (g.next() % 2) as u32 });
        }
        let want: BTreeSet<u32> = kept(&rows, |_| true).iter().map(|r| r.id).collect();
        cases += 1;
        bad += (viewed(&rows) != want) as usize;
    }
    report("a view of a store with cycles of names, against what kept keeps", cases, bad);
    assert_eq!(bad, 0);
}
