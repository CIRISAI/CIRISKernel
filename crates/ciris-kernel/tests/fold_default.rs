//! The fold default of CC 3.5.1, against the section's own four rules, and in every order of its rows.

mod common;
#[path = "common/dag.rs"]
mod dag;
use ciris_kernel::derived::fold_default;
use ciris_kernel::graph::Graph;
use ciris_kernel::layers::Concluded;
use common::report;

#[derive(Clone, Debug, PartialEq)]
struct C {
    id: String,
    signer: String,
    kind: &'static str,
    target: &'static str,
    at: i64,
    names: Vec<String>,
}
impl ciris_kernel::Row for C {
    type Id = String;
    type Key = String;
    fn id(&self) -> &String {
        &self.id
    }
    fn names(&self) -> &[String] {
        &self.names
    }
    fn signer(&self) -> &String {
        &self.signer
    }
}
fn c(id: &str, signer: &str, kind: &'static str, target: &'static str, at: i64) -> C {
    C { id: id.into(), signer: signer.into(), kind, target, at, names: vec![] }
}
fn rank(r: &C) -> u8 {
    match r.kind {
        "recants" => 3,
        "withdraws" => 2,
        "supersedes" => 1,
        _ => 0,
    }
}
fn winners(rows: &[C]) -> Vec<(String, String, String)> {
    let cs = Concluded::with(Graph::new(rows.iter()), None);
    let all: Vec<usize> = (0..rows.len()).collect();
    let w = fold_default(&cs, &all, |r| Some(r.target), rank, |r| r.at);
    w.into_iter().map(|((s, t), i)| (s, t.to_string(), cs.g.row(i).id.clone())).collect()
}

#[test]
fn cc_3_5_1_rules() {
    let mut n = 0;
    let mut t = |got: Vec<(String, String, String)>, want: &[(&str, &str, &str)], rule: &str| {
        n += 1;
        let want: Vec<(String, String, String)> =
            want.iter().map(|(a, b, c)| (a.to_string(), b.to_string(), c.to_string())).collect();
        assert_eq!(got, want, "{rule}");
    };
    // rule 1: recants outranks withdraws outranks supersedes, whatever the instants
    t(
        winners(&[c("s", "A", "supersedes", "E", 9), c("w", "A", "withdraws", "E", 5), c("r", "A", "recants", "E", 1)]),
        &[("A", "E", "r")],
        "rule 1",
    );
    // rule 2: of one kind by one signer, the latest signed instant wins
    t(
        winners(&[c("s1", "A", "supersedes", "E", 3), c("s2", "A", "supersedes", "E", 7)]),
        &[("A", "E", "s2")],
        "rule 2",
    );
    // rule 3: an equal instant goes to the lowest row id
    t(
        winners(&[c("sb", "A", "supersedes", "E", 4), c("sa", "A", "supersedes", "E", 4)]),
        &[("A", "E", "sa")],
        "rule 3",
    );
    // rule 4: each signer's chain is its own; no row of B is ranked against A's
    t(
        winners(&[c("a", "A", "supersedes", "E", 9), c("b", "B", "recants", "E", 1)]),
        &[("A", "E", "a"), ("B", "E", "b")],
        "rule 4",
    );
    // every order of a mixed set gives one answer
    let rows = vec![
        c("1", "A", "supersedes", "E", 4),
        c("2", "A", "supersedes", "E", 4),
        c("3", "A", "withdraws", "E", 2),
        c("4", "B", "supersedes", "E", 8),
        c("5", "B", "supersedes", "F", 1),
        c("6", "A", "supersedes", "F", 6),
    ];
    let want = winners(&rows);
    let mut perm = rows.clone();
    let mut orders = 0;
    heap(&mut perm, rows.len(), &mut |p| {
        orders += 1;
        assert_eq!(winners(p), want);
    });
    report("fold default (CC 3.5.1 rules and every order of six rows)", n + orders, 0);
}

fn heap<T: Clone>(a: &mut Vec<T>, k: usize, f: &mut dyn FnMut(&[T])) {
    if k == 1 {
        f(a);
        return;
    }
    for i in 0..k {
        heap(a, k - 1, f);
        if k.is_multiple_of(2) {
            a.swap(i, k - 1)
        } else {
            a.swap(0, k - 1)
        }
    }
}
