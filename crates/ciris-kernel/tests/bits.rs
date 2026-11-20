//! `graph::Bits`: the compact form of a set is the same set as its dense form, under every operation.
#[path = "common/dag.rs"]
mod dag;

use ciris_kernel::graph::Bits;
use ciris_kernel::held::{Held, Rules};
use ciris_kernel::layers::Past;
use dag::Lcg;
use std::collections::BTreeSet;

/// A set over `n` indices: a full prefix up to `full`, then each later index with probability `p` in 1024.
fn sample(n: usize, full: usize, p: u64, g: &mut Lcg) -> (Bits, BTreeSet<usize>) {
    let mut b = Bits::new(n);
    let mut s = BTreeSet::new();
    for i in 0..n {
        if i < full || g.next() % 1024 < p {
            b.set(i);
            s.insert(i);
        }
    }
    (b, s)
}

#[test]
fn compact_is_the_same_set() {
    let mut g = Lcg(42);
    for (n, full, p) in [
        (0, 0, 0),
        (1, 1, 0),
        (63, 0, 512),
        (64, 64, 0),
        (65, 64, 1),
        (500, 300, 3),
        (4096, 4000, 2),
        (4096, 0, 5),
        (4096, 0, 1000),
        (10_000, 9_000, 0),
    ] {
        for _ in 0..4 {
            let (d, s) = sample(n, full, p, &mut g);
            let c = d.clone().compact();
            assert_eq!(c, d, "equality reads the set");
            assert_eq!(c.len(), s.len());
            assert_eq!(c.is_empty(), s.is_empty());
            assert_eq!(c.iter().collect::<Vec<_>>(), s.iter().copied().collect::<Vec<_>>());
            for i in 0..n + 130 {
                assert_eq!(c.has(i), s.contains(&i), "has({i}) n={n}");
            }
            // union, each way round: a dense set takes a compact one, and a compact one becomes dense
            let (e, t) = sample(n, full / 2, p, &mut g);
            let mut x = e.clone();
            x.union(&c);
            let mut y = c.clone();
            y.union(&e.clone().compact());
            let st: BTreeSet<usize> = s.union(&t).copied().collect();
            assert_eq!(x.iter().collect::<BTreeSet<_>>(), st);
            assert_eq!(y.iter().collect::<BTreeSet<_>>(), st);
            // set on a compact set
            if n > 0 {
                let mut z = c.clone();
                z.set(n - 1);
                assert!(z.has(n - 1));
                assert_eq!(z.len(), s.len() + usize::from(!s.contains(&(n - 1))));
            }
        }
    }
}

#[test]
fn compact_is_never_much_larger_and_a_prefix_past_is_small() {
    let mut g = Lcg(7);
    let (d, _) = sample(64_000, 63_000, 0, &mut g);
    let c = d.clone().compact();
    assert!(c.heap_bytes() * 50 < d.heap_bytes(), "{} vs {}", c.heap_bytes(), d.heap_bytes());
    let (d, _) = sample(64_000, 0, 600, &mut g);
    assert!(d.clone().compact().heap_bytes() <= d.heap_bytes());
}

#[test]
fn a_kept_past_is_never_larger_than_dense_and_a_chain_is_tiny() {
    // a dense past is n / 64 words whatever the row: compact never holds more
    for (k, w) in [(3, 64), (1, 1), (5, 8)] {
        let rows = dag::dag(4096, k, w, 7);
        let mut h = Held::empty(Rules { wf: |_: &dag::N| true, rule: |_: &Past<'_, '_, dag::N>| true });
        h.set_past_window(usize::MAX);
        for r in &rows {
            let _ = h.admit(r);
        }
        let gr = &h.concluded().g;
        let dense = gr.len() * gr.len().div_ceil(64) * 8;
        assert!(gr.past_bytes() <= dense, "k={k} w={w}: {} > {dense}", gr.past_bytes());
        if k == 1 && w == 1 {
            // a chain: every past is a run of whole words and one word
            assert!(gr.past_bytes() * 10 < dense, "chain: {} vs {dense}", gr.past_bytes());
        }
    }
}
