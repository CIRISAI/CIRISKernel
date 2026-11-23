//! A signer's claim for a key, by what its rows name and by no instant (`derived::claims`): the rule's own
//! cases, and every order of a mixed set of rows.

mod common;
use ciris_kernel::derived::{claims, Claim};
use ciris_kernel::graph::Graph;
use ciris_kernel::layers::Concluded;
use common::report;

#[derive(Clone, Debug, PartialEq)]
struct C {
    id: String,
    signer: String,
    kind: &'static str,
    key: Option<&'static str>,
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
fn c(id: &str, signer: &str, kind: &'static str, key: &'static str, names: &[&str]) -> C {
    let key = (!key.is_empty()).then_some(key);
    C { id: id.into(), signer: signer.into(), kind, key, names: names.iter().map(|n| n.to_string()).collect() }
}
/// (signer, key, answer): "stands x", "ended x" or "split x+y".
fn said(rows: &[C]) -> Vec<(String, String, String)> {
    let cs = Concluded::with(Graph::new(rows.iter()), None);
    let all: Vec<usize> = (0..rows.len()).collect();
    let id = |i: &usize| cs.g.row(*i).id.clone();
    claims(&cs, &all, |r| r.key, |r| matches!(r.kind, "recants" | "withdraws"))
        .into_iter()
        .map(|((s, k), a)| {
            let a = match a {
                Claim::Stands(i) => format!("stands {}", id(&i)),
                Claim::Ended(i) => format!("ended {}", id(&i)),
                Claim::Split(v) => format!("split {}", v.iter().map(id).collect::<Vec<_>>().join("+")),
            };
            (s, k.to_string(), a)
        })
        .collect()
}

#[test]
fn a_signers_claim() {
    let mut n = 0;
    let mut t = |rows: &[C], want: &[(&str, &str, &str)], rule: &str| {
        n += 1;
        let want: Vec<(String, String, String)> =
            want.iter().map(|(a, b, c)| (a.to_string(), b.to_string(), c.to_string())).collect();
        assert_eq!(said(rows), want, "{rule}");
    };
    t(&[c("a1", "A", "scores", "K", &[])], &[("A", "K", "stands a1")], "one row is the claim");
    t(
        &[c("a1", "A", "scores", "K", &[]), c("a2", "A", "supersedes", "K", &["a1"])],
        &[("A", "K", "stands a2")],
        "a superseding row replaces the row it names",
    );
    t(
        &[c("a1", "A", "scores", "K", &[]), c("r", "A", "recants", "K", &["a1"])],
        &[("A", "K", "ended r")],
        "a recanted claim is no claim",
    );
    t(
        &[c("a1", "A", "scores", "K", &[]), c("w", "A", "withdraws", "K", &["a1"])],
        &[("A", "K", "ended w")],
        "a withdrawn claim is no claim",
    );
    t(
        &[c("a1", "A", "scores", "K", &[]), c("a2", "A", "scores", "K", &[])],
        &[("A", "K", "split a1+a2")],
        "two rows, neither naming the other: the signer says two things",
    );
    t(
        &[
            c("a1", "A", "scores", "K", &[]),
            c("a2", "A", "scores", "K", &[]),
            c("a3", "A", "supersedes", "K", &["a1", "a2"]),
        ],
        &[("A", "K", "stands a3")],
        "a row naming both heals the split",
    );
    t(
        &[
            c("a1", "A", "scores", "K", &[]),
            c("a2", "A", "supersedes", "K", &["a1"]),
            c("r", "A", "recants", "K", &["a1"]),
        ],
        &[("A", "K", "split a2+r")],
        "a recant of the old row beside a row superseding it: two heads",
    );
    t(
        &[
            c("a1", "A", "scores", "K", &[]),
            c("w", "A", "withdraws", "K", &["a1"]),
            c("a2", "A", "scores", "K", &["w"]),
        ],
        &[("A", "K", "stands a2")],
        "a new claim that names the withdrawal stands",
    );
    t(
        &[c("a1", "A", "scores", "K", &[]), c("b", "B", "recants", "K", &["a1"])],
        &[("A", "K", "stands a1"), ("B", "K", "ended b")],
        "a row of another signer never voids a claim",
    );
    t(
        &[c("a1", "A", "scores", "K", &[]), c("b", "B", "supersedes", "K", &["a1"])],
        &[("A", "K", "stands a1"), ("B", "K", "stands b")],
        "nor replaces it: two signers are two claims",
    );
    t(
        &[c("a1", "A", "scores", "K", &[]), c("b", "B", "scores", "", &["a1"]), c("a2", "A", "scores", "K", &["b"])],
        &[("A", "K", "stands a2")],
        "a row has another in its past through a row of another signer",
    );
    t(
        &[c("a1", "A", "scores", "K", &[]), c("a2", "A", "scores", "L", &[])],
        &[("A", "K", "stands a1"), ("A", "L", "stands a2")],
        "two keys are two claims",
    );
    t(&[c("a1", "A", "scores", "", &[])], &[], "a row with no key is not read");
    // every order of a mixed set gives one answer
    let rows = vec![
        c("1", "A", "scores", "K", &[]),
        c("2", "A", "supersedes", "K", &["1"]),
        c("3", "A", "scores", "K", &[]),
        c("4", "B", "recants", "K", &["2"]),
        c("5", "A", "scores", "L", &[]),
        c("6", "A", "withdraws", "L", &["5"]),
        c("7", "B", "scores", "L", &["6"]),
    ];
    let want = said(&rows);
    assert_eq!(
        want,
        [("A", "K", "split 2+3"), ("A", "L", "ended 6"), ("B", "K", "ended 4"), ("B", "L", "stands 7")]
            .map(|(a, b, c)| (a.to_string(), b.to_string(), c.to_string()))
    );
    let mut perm = rows.clone();
    let mut orders = 0;
    heap(&mut perm, rows.len(), &mut |p| {
        orders += 1;
        assert_eq!(said(p), want);
    });
    report("a signer's claim by what its rows name (the rule's cases and every order of seven rows)", n + orders, 0);
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
