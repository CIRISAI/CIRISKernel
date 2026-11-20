//! `held`: the layers held across admissions equal the whole fold after every admission, in every order
//! tried (`held::differential`), and a refused admission changes nothing.
mod common;
#[path = "common/dag.rs"]
mod dag;

use ciris_kernel::held::{differential, Held, HeldSpec, Refused, Rules};
use ciris_kernel::layers::{self, Past};
use ciris_kernel::Row;
use dag::{dag, Lcg, N};

/// A rule that reads the concluded past: a row concludes unless an odd number of its concluded ancestors
/// share its signer.
fn parity(p: &Past<'_, '_, N>) -> bool {
    let me = p.row().signer;
    p.rows().filter(|r| r.signer == me).count() % 2 == 0
}

/// Rows whose id is 7 more than a multiple of 11 are not well formed.
fn wf(r: &N) -> bool {
    r.id % 11 != 7
}

#[derive(Clone)]
struct Seeded;
impl HeldSpec<N> for Seeded {
    fn well_formed(&self, r: &N) -> bool {
        wf(r)
    }
    fn conclude(&self, p: &Past<'_, '_, N>) -> bool {
        parity(p)
    }
    fn seeded(&self) -> bool {
        true
    }
    fn root(&self, r: &N) -> bool {
        r.signer == 3
    }
}

fn shuffled(rows: &[N], seed: u64) -> Vec<N> {
    let mut v = rows.to_vec();
    let mut g = Lcg(seed);
    for i in (1..v.len()).rev() {
        let j = (g.next() as usize) % (i + 1);
        v.swap(i, j);
    }
    v
}

fn orders(rows: &[N]) -> Vec<Vec<N>> {
    let mut rev = rows.to_vec();
    rev.reverse();
    vec![rows.to_vec(), rev, shuffled(rows, 1), shuffled(rows, 2), shuffled(rows, 3)]
}

#[test]
fn equals_the_fold_after_every_admission() {
    for (n, k, w, seed) in [(40, 1, 1, 1), (60, 3, 8, 2), (60, 4, 60, 3), (120, 2, 16, 4), (200, 5, 30, 5)] {
        let rows = dag(n, k, w, seed);
        for o in orders(&rows) {
            differential(Rules { wf, rule: parity }, &o).unwrap();
            differential(Seeded, &o).unwrap();
            differential(Rules { wf: |_: &N| true, rule: |_: &Past<'_, '_, N>| true }, &o).unwrap();
        }
    }
}

#[test]
fn names_not_in_the_store_and_self_names_wait() {
    // 5 names 99, never offered; 6 names 5; 7 names itself
    let mut rows = dag(8, 2, 4, 9);
    rows[5].names.push(99);
    rows[7].names.push(7);
    for o in orders(&rows) {
        differential(Rules { wf: |_: &N| true, rule: parity }, &o).unwrap();
        let h = Held::new(Rules { wf: |_: &N| true, rule: parity }, o.iter());
        assert!(!h.holds(&5) && h.waits(&5));
        assert!(!h.holds(&7) && h.waits(&7));
    }
}

#[test]
fn matches_arrive_by_id() {
    let rows = dag(300, 3, 20, 7);
    for o in orders(&rows) {
        let full = layers::arrive(&o, parity, None, wf);
        let h = Held::new(Rules { wf, rule: parity }, o.iter());
        assert_eq!(h.len(), full.g.len());
        for i in 0..full.g.len() {
            assert_eq!(h.concluded_id(full.g.row(i).id()), full.concluded(i));
        }
    }
}

#[test]
fn a_refusal_changes_nothing_and_a_clone_rolls_back() {
    let rows = dag(50, 3, 10, 11);
    let below_1000 = |r: &N| r.id < 1000;
    let mut h = Held::new(Rules { wf: below_1000, rule: parity }, rows[..30].iter());
    let len = h.len();
    assert_eq!(len, 30);
    let bad = N { id: 1000, names: vec![3], signer: 0 };
    assert_eq!(h.admit(&rows[0]), Err(Refused::Duplicate));
    assert_eq!(h.admit(&bad), Err(Refused::NotWellFormed));
    assert_eq!(h.len(), len);

    let saved = h.clone();
    let a = h.admit_all(rows[30..].iter());
    assert!(!a.kept.is_empty());
    let mut d = a.dirty.clone();
    d.dedup();
    assert_eq!(d, a.dirty, "dirty is sorted and each id once");
    assert!(a.dirty.windows(2).all(|w| w[0] < w[1]));
    // the transaction rolled back: the saved value is the state before
    let h = saved;
    assert_eq!(h.len(), len);
    for r in &rows[30..] {
        assert!(!h.holds(r.id()));
    }
}

#[test]
fn releasing_waiters_keeps_them_and_only_them() {
    // a chain offered tip first: every row waits until the root arrives, then one admission keeps them all
    let rows = dag(64, 1, 1, 1);
    let mut h = Held::empty(Rules { wf: |_: &N| true, rule: parity });
    for r in rows[1..].iter().rev() {
        let a = h.admit(r).unwrap();
        assert!(a.waiting && a.kept.is_empty());
    }
    let a = h.admit(&rows[0]).unwrap();
    assert_eq!(a.kept.len(), 64);
    assert_eq!(a.dirty, (0..64).collect::<Vec<u32>>());
    // the work is the rows kept plus what they name: 64 rows, 63 names, the root's none
    assert_eq!(a.visited, 64 + 63);
}

#[test]
fn one_admission_visits_its_cone_not_the_store() {
    let rows = dag(4096, 3, 64, 13);
    let mut h = Held::new(Rules { wf: |_: &N| true, rule: |_: &Past<'_, '_, N>| true }, rows.iter());
    let n = rows.len() as u32;
    let x = N { id: n, names: vec![n - 1, n - 7, n - 100], signer: 0 };
    let a = h.admit(&x).unwrap();
    assert_eq!(a.kept, vec![n]);
    assert_eq!(a.visited, 1 + 3);
}

#[test]
fn the_past_window_changes_no_answer() {
    let rows = dag(600, 3, 40, 21);
    for o in orders(&rows) {
        let views: Vec<Held<'_, N, _>> = [0usize, 1, 7, 64, usize::MAX]
            .into_iter()
            .map(|w| {
                let mut h = Held::empty(Rules { wf, rule: parity });
                h.set_past_window(w);
                for r in &o {
                    let _ = h.admit(r);
                }
                h
            })
            .collect();
        let base = &views[4];
        for h in &views[..4] {
            assert_eq!(h.len(), base.len());
            for r in &rows {
                assert_eq!(h.concluded_id(r.id()), base.concluded_id(r.id()));
                let (Some(a), Some(b)) = (h.concluded().g.idx(r.id()), base.concluded().g.idx(r.id())) else {
                    continue;
                };
                assert_eq!(h.concluded().g.depth(a), base.concluded().g.depth(b));
            }
        }
        // a window of w keeps at most w pasts computed after admission
        let mut h = Held::empty(Rules { wf, rule: parity });
        h.set_past_window(7);
        for r in &o {
            let _ = h.admit(r);
        }
        assert!(h.concluded().g.past_bytes() <= 7 * h.len().div_ceil(64) * 8 + 7 * 64);
    }
}

#[test]
fn the_window_s_price_is_counted() {
    // a new row naming a recent row and an OLD row outside the recent row's past (a side branch, such as a receipt
    // no later row named): with every past kept the walk takes the old row's past whole; with a small window it
    // walks it. An old row inside the recent row's past costs nothing either way.
    let rows = dag(2000, 3, 20, 3);
    let all = |w: usize| {
        let mut h = Held::empty(Rules { wf: |_: &N| true, rule: parity });
        h.set_past_window(w);
        for r in &rows {
            let _ = h.admit(r);
        }
        assert_eq!(h.len(), rows.len());
        h
    };
    let probe = all(usize::MAX);
    let g = &probe.concluded().g;
    let tip = g.idx(&1999).unwrap();
    let side = (500..1500u32)
        .rev()
        .find(|&o| !g.in_past(g.idx(&o).unwrap(), tip) && g.depth(g.idx(&o).unwrap()) > 100)
        .expect("a side branch with a deep past");
    let x = N { id: 2000, names: vec![1999, side], signer: 0 };
    let walked = |w: usize| {
        let mut h = all(w);
        let before = h.past_counts();
        h.admit(&x).unwrap();
        let after = h.past_counts();
        assert_eq!(after.computed, before.computed + 1);
        after.walked - before.walked
    };
    let (every, small) = (walked(usize::MAX), walked(4));
    assert!(every < small, "every past kept walks {every}, a window of 4 walks {small} (side branch {side})");
}
