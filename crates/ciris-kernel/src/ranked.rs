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
    let (winner, rounds, _) = count(ballots, options, floor, declared, false);
    (winner, rounds)
}

/// The runoff order of the same count (CC 4.5.13: a decline "passes the duty to the next in runoff order"): the
/// winner, then the options in the reverse of the order they were eliminated, the count run on past a majority
/// "until one remains". Only the part a tie leaves known: a tie for weakest after a majority leaves the winner
/// alone; one before it, or no count, leaves nothing. Its first is [`ranked`]'s winner.
pub fn runoff<P: Ord + Clone, O: Ord + Clone>(
    ballots: &[(P, Vec<O>)],
    options: &[O],
    floor: usize,
    declared: bool,
) -> Vec<O> {
    count(ballots, options, floor, declared, true).2
}

/// The one count. `to_end`: run on past a majority, eliminating, until one option stands or a tie for weakest.
fn count<P: Ord + Clone, O: Ord + Clone>(
    ballots: &[(P, Vec<O>)],
    options: &[O],
    floor: usize,
    declared: bool,
    to_end: bool,
) -> (Option<O>, usize, Vec<O>) {
    // one ranking per person: a voice that says two things says nothing
    let mut by: BTreeMap<&P, BTreeSet<&Vec<O>>> = BTreeMap::new();
    for (p, r) in ballots {
        by.entry(p).or_default().insert(r);
    }
    let one: Vec<(&P, &Vec<O>)> =
        by.into_iter().filter(|(_, s)| s.len() == 1).map(|(p, s)| (p, *s.iter().next().unwrap())).collect();
    let need = core::cmp::min(floor, core::cmp::max(options.len(), 1));
    if !ops::in_range(Some(&one.len()), Some(&need), None) {
        return (None, 0, Vec::new());
    }
    let index = |o: &O| options.iter().position(|x| x == o).unwrap_or(usize::MAX);
    #[derive(Clone, PartialEq)]
    struct St<O> {
        standing: Vec<O>,
        winner: Option<O>,
        done: bool,
        rounds: usize,
        // the options eliminated, in turn
        out: Vec<O>,
        // the top of the order the count leaves known
        top: Vec<O>,
    }
    let start =
        St { standing: options.to_vec(), winner: None, done: false, rounds: 0, out: Vec::new(), top: Vec::new() };
    let end = ops::fix(start, options.len() + 1, |s| {
        if s.done {
            return s.clone();
        }
        let known = |w: &Option<O>| w.iter().cloned().collect::<Vec<O>>();
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
            return St { done: true, top: known(&s.winner), ..s.clone() };
        }
        let n = |o: &O| first.get(o).map_or(0, |v| v.len());
        let top = s.standing.iter().map(&n).max().unwrap_or(0);
        let mut winner = s.winner.clone();
        if winner.is_none() && (ops::in_range(Some(&(2 * top)), Some(&(voters + 1)), None) || s.standing.len() == 1) {
            let w = ops::one(s.standing.iter().filter(|o| n(o) == top).cloned());
            if !to_end || s.standing.len() == 1 {
                return St { done: true, top: known(&w), winner: w, ..s.clone() };
            }
            winner = w;
        }
        if s.standing.len() == 1 {
            return St { done: true, top: s.standing.clone(), winner, ..s.clone() };
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
                let mut out = s.out.clone();
                out.push(weakest.clone());
                St {
                    standing: s.standing.iter().filter(|o| **o != weakest).cloned().collect(),
                    rounds: s.rounds + usize::from(winner.is_none()),
                    winner,
                    done: false,
                    out,
                    top: s.top.clone(),
                }
            }
            // no declared order: a tie for weakest seats nobody, or (past a majority) leaves the order below the
            // winner unknown
            _ => St { done: true, top: known(&winner), winner, ..s.clone() },
        }
    });
    let order = if end.top.len() == 1 && end.standing.len() == 1 {
        end.top.iter().cloned().chain(end.out.iter().rev().cloned()).collect()
    } else {
        end.top
    };
    (end.winner, end.rounds, order)
}
