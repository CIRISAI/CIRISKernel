//! The ranked count (`reexpress.ranked`, CC 4.5.13), written over the operators. With a declared order a
//! tie for weakest goes to the option listed later; with none (the election), a tie for weakest is refused
//! by the reducer and seats nobody (`Election.free_perm`, `free_agrees`, parent repository).

use crate::ops;
use alloc::collections::{BTreeMap, BTreeSet};
use alloc::vec::Vec;

/// The ranked count over `ballots` (one per person; a person with two different rankings has no ballot).
/// Returns the winner, if any, and the number of elimination rounds run. `floor` is the least number of
/// ballots (capped at the number of options).
pub fn ranked<P: Ord + Clone, O: Ord + Clone>(
    ballots: &[(P, Vec<O>)],
    options: &[O],
    floor: usize,
    declared: bool,
) -> (Option<O>, usize) {
    // one ranking per person: a voice that says two things says nothing
    let mut by: BTreeMap<&P, BTreeSet<&Vec<O>>> = BTreeMap::new();
    for (p, r) in ballots {
        by.entry(p).or_default().insert(r);
    }
    let one: Vec<(&P, &Vec<O>)> =
        by.into_iter().filter(|(_, s)| s.len() == 1).map(|(p, s)| (p, *s.iter().next().unwrap())).collect();
    let need = core::cmp::min(floor, core::cmp::max(options.len(), 1));
    if !ops::in_range(Some(&one.len()), Some(&need), None) {
        return (None, 0);
    }
    let index = |o: &O| options.iter().position(|x| x == o).unwrap_or(usize::MAX);
    #[derive(Clone, PartialEq)]
    struct St<O> {
        standing: Vec<O>,
        winner: Option<O>,
        done: bool,
        rounds: usize,
    }
    let start = St { standing: options.to_vec(), winner: None, done: false, rounds: 0 };
    let end = ops::fix(start, options.len() + 1, |s| {
        if s.done {
            return s.clone();
        }
        // each person's first choice among the options still standing
        let mut first: BTreeMap<&O, BTreeSet<&P>> = BTreeMap::new();
        let mut voters = 0usize;
        for (p, r) in &one {
            if let Some(o) = r.iter().find(|o| s.standing.contains(o)) {
                first.entry(o).or_default().insert(*p);
                voters += 1;
            }
        }
        if voters == 0 {
            return St { done: true, winner: None, ..s.clone() };
        }
        let n = |o: &O| first.get(o).map_or(0, |v| v.len());
        let top = s.standing.iter().map(&n).max().unwrap_or(0);
        if ops::in_range(Some(&(2 * top)), Some(&(voters + 1)), None) || s.standing.len() == 1 {
            let w = ops::one(s.standing.iter().filter(|o| n(o) == top).cloned());
            return St { done: true, winner: w, ..s.clone() };
        }
        // weakest by (first choices, declared order: the option listed later is weaker); a tie is refused
        #[derive(PartialEq)]
        struct T<'o, O> {
            o: &'o O,
            n: usize,
            back: i64,
        }
        let table: Vec<T<'_, O>> =
            s.standing.iter().map(|o| T { o, n: n(o), back: if declared { -(index(o) as i64) } else { 0 } }).collect();
        let refs: Vec<&T<'_, O>> = table.iter().collect();
        match ops::least(&refs, |t| (t.n, t.back)) {
            Ok(Some(w)) => {
                let weakest = w.o.clone();
                St {
                    standing: s.standing.iter().filter(|o| **o != weakest).cloned().collect(),
                    winner: None,
                    done: false,
                    rounds: s.rounds + 1,
                }
            }
            _ => St { done: true, winner: None, ..s.clone() },
        }
    });
    (end.winner, end.rounds)
}
