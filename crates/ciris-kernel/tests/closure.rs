//! The lazy closure of `graph::Graph` against the eager one the crate first shipped (`tests/common/eager.rs`):
//! every pair, every frontier and every depth over generated graphs, and rows given out of order.

mod common;
#[path = "common/dag.rs"]
mod dag;
use ciris_kernel::graph::Graph;
use common::eager::EagerGraph;
use common::report;
use dag::{dag, Lcg};

#[test]
fn lazy_closure_equals_the_eager_one() {
    let (mut cases, mut bad) = (0usize, 0usize);
    for (n, k, w, seed) in
        [(1, 1, 1, 1), (40, 1, 1, 2), (120, 3, 8, 3), (200, 2, 200, 4), (300, 4, 20, 5), (64, 2, 3, 6)]
    {
        let mut rows = dag(n, k, w, seed);
        if seed % 2 == 0 {
            rows.reverse(); // the closure must not depend on the order rows are given in
        }
        let lazy = Graph::new(rows.iter());
        let eager = EagerGraph::new(rows.iter());
        let m = rows.len();
        // ask in a scrambled order so the memo is filled from the middle
        let mut g = Lcg(seed);
        for _ in 0..m {
            let b = (g.next() as usize) % m;
            for a in 0..m {
                cases += 1;
                bad += (lazy.in_past(a, b) != eager.in_past(a, b)) as usize;
                bad += (lazy.concurrent(a, b) != eager.concurrent(a, b)) as usize;
            }
        }
        for a in 0..m {
            for b in 0..m {
                cases += 1;
                bad += (lazy.in_past(a, b) != eager.in_past(a, b)) as usize;
            }
            cases += 1;
            bad += (lazy.depth(a) != eager.depth(a)) as usize;
            bad += (lazy.past(a, true) != eager.past(a, true)) as usize;
        }
        for _ in 0..50 {
            let of: Vec<usize> = (0..8).map(|_| (g.next() as usize) % m).collect();
            cases += 1;
            bad += (lazy.frontier(&of) != eager.frontier(&of)) as usize;
        }
    }
    report("lazy closure against the eager closure", cases, bad);
    assert_eq!(bad, 0);
}
