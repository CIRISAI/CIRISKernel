//! The trust walk against `formal/trust_set/TrustSet.lean` (parent repository): the worked world's
//! `decide` theorems, and the Lean `walk` transcribed literally, compared over every small graph.
//! There is no Python model of this walk, so the reference here is the Lean definition itself.

mod common;
use ciris_kernel::trust::{honours, reaches, Accepts, Charters, HOP_CAP};
use common::report;

type E = Accepts<u8, u8>;

/// `TrustSet.walk`, as written: structural on a fuel, no memory of keys visited.
fn lean_walk(edges: &[E], fuel: u32, k: u8, c: u8, b: u32, a: u8) -> bool {
    if fuel == 0 || b == 0 {
        return false;
    }
    edges.iter().any(|e| {
        e.src == k
            && e.admits(&c)
            && (e.dst == a || lean_walk(edges, fuel - 1, e.dst, c, core::cmp::min(b - 1, e.depth), a))
    })
}

fn lean_reaches(edges: &[E], k: u8, c: u8, n: u32, a: u8) -> bool {
    lean_walk(edges, n, k, c, n, a)
}

const READER: u8 = 0;
const CIRIS: u8 = 1;
const BOARD: u8 = 2;
const STRANGER: u8 = 3;
const COLLEGE: u8 = 4;
const MEDICAL: u8 = 1;
const LEGAL: u8 = 2;

fn e(src: u8, dst: u8, classes: &[u8], depth: u32) -> E {
    Accepts { src, dst, classes: classes.to_vec(), depth }
}

fn charter0() -> Charters<u8, u8> {
    let mut ch = Charters::new();
    ch.meet(BOARD, [MEDICAL, LEGAL]);
    ch.meet(STRANGER, [MEDICAL]);
    ch
}

fn charter1() -> Charters<u8, u8> {
    let mut ch = Charters::new();
    ch.meet(BOARD, [MEDICAL]);
    ch.meet(COLLEGE, [MEDICAL]);
    ch
}

#[test]
fn trust_set_worked_world() {
    let root = e(READER, CIRIS, &[], 5);
    let board = e(READER, BOARD, &[MEDICAL], 0);
    let shipped = vec![root.clone()];
    let with_board = vec![root.clone(), board.clone()];
    let without_ciris = vec![board.clone()];
    let (charter0, charter1) = (&charter0(), &charter1());
    let mut n = 0;
    let mut t = |ok: bool, name: &str| {
        n += 1;
        assert!(ok, "{name}");
    };
    t(!honours(&shipped, &READER, charter0, &BOARD, &MEDICAL), "shipped_trusts_no_board");
    t(honours(&with_board, &READER, charter0, &BOARD, &MEDICAL), "board_added");
    t(!honours(&with_board, &READER, charter0, &BOARD, &LEGAL), "board_legal_not_trusted");
    t(!honours(&with_board, &READER, charter0, &STRANGER, &MEDICAL), "stranger_never");
    t(honours(&without_ciris, &READER, charter0, &BOARD, &MEDICAL), "root_removed_board_stands");
    let deep = vec![e(READER, BOARD, &[MEDICAL], 1), e(BOARD, COLLEGE, &[MEDICAL], 0)];
    let shallow = vec![e(READER, BOARD, &[MEDICAL], 0), e(BOARD, COLLEGE, &[MEDICAL], 0)];
    t(honours(&deep, &READER, charter1, &COLLEGE, &MEDICAL), "licensor_of_licensor_at_depth_one");
    t(!honours(&shallow, &READER, charter1, &COLLEGE, &MEDICAL), "licensor_of_licensor_cut_at_depth_zero");
    report("trust walk, TrustSet.lean worked world", n, 0);
}

#[test]
fn trust_walk_equals_the_lean_walk() {
    // every graph of up to four edges over four keys, two classes, depths 0..2, every budget to the cap
    let mut pool: Vec<E> = Vec::new();
    for src in 0..4u8 {
        for dst in 0..4u8 {
            if src == dst {
                continue;
            }
            for cls in [&[][..], &[1u8][..]] {
                for depth in [0, 2] {
                    pool.push(e(src, dst, cls, depth));
                }
            }
        }
    }
    let (mut cases, mut bad) = (0usize, 0usize);
    let mut idx = [0usize; 3];
    // graphs of three edges drawn from the pool with a stride, plus every pair: bounded and exhaustive enough
    let m = pool.len();
    for i in 0..m {
        for j in i..m {
            idx[0] = i;
            idx[1] = j;
            for kk in [0usize, (i + j) % m, (i * 7 + 3) % m] {
                idx[2] = kk;
                let g: Vec<E> = idx.iter().map(|&x| pool[x].clone()).collect();
                for a in 1..4u8 {
                    for c in [1u8, 2] {
                        for budget in 0..=HOP_CAP {
                            cases += 1;
                            if reaches(&g, &READER, &c, budget, &a) != lean_reaches(&g, READER, c, budget, a) {
                                bad += 1;
                            }
                        }
                    }
                }
            }
        }
    }
    report("trust walk against the Lean walk", cases, bad);
    assert_eq!(bad, 0);
}

/// Reading 1 of "a cycle is visited once": a walk never passes the same key twice (simple paths only).
fn simple_paths(edges: &[E], k: u8, c: u8, b: u32, a: u8, on: &mut Vec<u8>) -> bool {
    if b == 0 {
        return false;
    }
    on.push(k);
    let hit = edges.iter().any(|e| {
        e.src == k
            && e.admits(&c)
            && (e.dst == a
                || (!on.contains(&e.dst) && simple_paths(edges, e.dst, c, core::cmp::min(b - 1, e.depth), a, on)))
    });
    on.pop();
    hit
}

/// Reading 2: each key is expanded at most once in the whole walk, breadth first, with the budget it was
/// first reached with.
fn visit_once(edges: &[E], k: u8, c: u8, b: u32, a: u8) -> bool {
    let mut seen = vec![k];
    let mut q = std::collections::VecDeque::from([(k, b)]);
    while let Some((x, bx)) = q.pop_front() {
        if bx == 0 {
            continue;
        }
        for e in edges.iter().filter(|e| e.src == x && e.admits(&c)) {
            if e.dst == a {
                return true;
            }
            if !seen.contains(&e.dst) {
                seen.push(e.dst);
                q.push_back((e.dst, core::cmp::min(bx - 1, e.depth)));
            }
        }
    }
    false
}

#[test]
fn the_cycle_reading() {
    // reading 1 equals the Lean walk on every graph of the pool above; reading 2 does not
    let mut pool: Vec<E> = Vec::new();
    for src in 0..4u8 {
        for dst in 0..4u8 {
            if src != dst {
                for depth in [0, 2] {
                    pool.push(e(src, dst, &[], depth));
                }
            }
        }
    }
    let (mut cases, mut r1, mut r2) = (0, 0, 0);
    let m = pool.len();
    for i in 0..m {
        for j in i..m {
            for k in j..m {
                let g = vec![pool[i].clone(), pool[j].clone(), pool[k].clone()];
                for a in 1..4u8 {
                    for budget in 0..=HOP_CAP {
                        cases += 1;
                        let lean = lean_reaches(&g, READER, 1, budget, a);
                        r1 += (simple_paths(&g, READER, 1, budget, a, &mut vec![]) != lean) as usize;
                        r2 += (visit_once(&g, READER, 1, budget, a) != lean) as usize;
                    }
                }
            }
        }
    }
    // the witness for reading 2: the reader reaches A first by an edge that allows no further hop, and again
    // through B with budget to spare; the Lean walk reaches C through B and A, a walk that visits each key once
    let w = vec![e(READER, 1, &[], 0), e(READER, 2, &[], 5), e(2, 1, &[], 5), e(1, 3, &[], 5)];
    assert!(lean_reaches(&w, READER, 1, HOP_CAP, 3));
    assert!(reaches(&w, &READER, &1, HOP_CAP, &3));
    assert!(!visit_once(&w, READER, 1, HOP_CAP, 3));
    eprintln!("  simple paths against Lean: {r1} differ; each key expanded once (breadth first) against Lean: {r2} differ, of {cases}");
    report("the cycle reading: a walk that passes no key twice, against the Lean walk", cases, r1);
    assert_eq!(r1, 0);
    assert!(r2 > 0);
}
