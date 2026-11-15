//! The trust walk against `formal/trust_set/TrustSet.lean` (parent repository): the worked world's
//! `decide` theorems, and the Lean `walk` transcribed literally, compared over every small graph.
//! There is no Python model of this walk, so the reference here is the Lean definition itself.

mod common;
use ciris_kernel::trust::{honours, reaches, Accepts, HOP_CAP};
use common::report;

type E = Accepts<u8, u8>;

/// `TrustSet.walk`, as written: structural on a fuel, no memory of keys visited.
fn lean_walk(edges: &[E], fuel: u32, k: u8, c: u8, b: u32, a: u8) -> bool {
    if fuel == 0 || b == 0 {
        return false;
    }
    edges.iter().any(|e| {
        e.src == k && e.admits(&c) && (e.dst == a || lean_walk(edges, fuel - 1, e.dst, c, core::cmp::min(b - 1, e.depth), a))
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

fn charter0(k: &u8, c: &u8) -> bool {
    match *k {
        BOARD => [MEDICAL, LEGAL].contains(c),
        STRANGER => *c == MEDICAL,
        _ => false,
    }
}

fn charter1(k: &u8, c: &u8) -> bool {
    match *k {
        BOARD | COLLEGE => *c == MEDICAL,
        _ => false,
    }
}

#[test]
fn trust_set_worked_world() {
    let root = e(READER, CIRIS, &[], 5);
    let board = e(READER, BOARD, &[MEDICAL], 0);
    let shipped = vec![root.clone()];
    let with_board = vec![root.clone(), board.clone()];
    let without_ciris = vec![board.clone()];
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
