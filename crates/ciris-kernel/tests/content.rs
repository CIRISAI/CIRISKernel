//! Differential: room content after a member's seat ends, against the case table of
//! `models/causal_kernel/conferral_content.py` (fixture `conferral_content.json`, which persist also runs):
//! every content row's `counted`, `in_force` and deciding rule, with the rows listed in each arrival order the
//! fixture gives and in reverse; then what a past that cannot tell does.

mod common;
use ciris_kernel::content::{answers, changed, Answer, ContentRow, Kind, Seat};
use common::*;
use std::collections::{BTreeMap, BTreeSet};

#[derive(Clone, Debug)]
struct CRow {
    id: String,
    kind: Kind,
    signer: String,
    names: Vec<String>,
    head: Option<String>,
    prev: Vec<String>,
    tips: Vec<String>,
    retracts: Option<String>,
}

impl ContentRow for CRow {
    type Id = String;
    type Key = String;
    fn id(&self) -> &String {
        &self.id
    }
    fn kind(&self) -> Kind {
        self.kind
    }
    fn signer(&self) -> &String {
        &self.signer
    }
    fn head(&self) -> Option<&String> {
        self.head.as_ref()
    }
    fn prev(&self) -> &[String] {
        &self.prev
    }
    fn tips(&self) -> &[String] {
        &self.tips
    }
    fn retracts(&self) -> Option<&String> {
        self.retracts.as_ref()
    }
}

fn row(j: &J) -> CRow {
    let opt = |k: &str| j.get(k).and_then(|v| v.opt_s());
    let list = |k: &str| j.get(k).map(|v| v.strs()).unwrap_or_default();
    CRow {
        id: j.at("id").s().to_string(),
        kind: match j.at("kind").s() {
            "head" => Kind::Head,
            "act" => Kind::Content,
            "end" => Kind::End,
            "tips" => Kind::Tips,
            k => panic!("kind {k}"),
        },
        signer: j.at("signer").s().to_string(),
        names: j.at("names").strs(),
        head: opt("head"),
        prev: list("prev"),
        tips: list("trusted_through"),
        retracts: if opt("compose").as_deref() == Some("retract") { opt("target") } else { None },
    }
}

/// The causal past by what the held rows name for the door. `hidden` is a row the caller does not hold: a walk
/// that reaches it cannot tell, and says which row it needs.
fn in_past(by: &BTreeMap<&str, &CRow>, hidden: Option<&str>, a: &str, b: &str) -> Result<bool, String> {
    let (mut todo, mut seen, mut need) = (vec![b], BTreeSet::new(), None);
    while let Some(x) = todo.pop() {
        if Some(x) == hidden {
            need = Some(x.to_string());
            continue;
        }
        let Some(r) = by.get(x) else { continue };
        for n in &r.names {
            if n == a {
                return Ok(true);
            }
            if seen.insert(n.as_str()) {
                todo.push(n.as_str());
            }
        }
    }
    need.map_or(Ok(false), Err)
}

fn run(rows: &[&CRow], hidden: Option<&str>) -> BTreeMap<String, Answer<String>> {
    let seat = Seat { member: &|k: &String| k == "B" || k == "B2", counted: &|k: &String| k == "count" };
    let by: BTreeMap<&str, &CRow> = rows.iter().map(|r| (r.id.as_str(), *r)).collect();
    answers(rows, &seat, &|a: &String, b: &String| in_past(&by, hidden, a, b))
}

fn show(a: &Answer<String>) -> (bool, bool, String) {
    match a {
        Answer::Judged(j) => (j.counted, j.in_force, j.rule.as_str().to_string()),
        Answer::Undecided(i) => panic!("undecided, needs {i}"),
    }
}

/// The fixture's cases under `count_first`, the rule this crate implements. A case under another `merge`
/// states what a rejected reading gives, and is not run.
fn cases(fx: &J) -> Vec<&J> {
    let all = fx.at("cases").arr();
    let run: Vec<&J> = all.iter().filter(|c| c.at("merge").s() == "count_first").collect();
    assert!(run.len() + 1 >= all.len() && !run.is_empty(), "the fixture's merges changed");
    run
}

#[test]
fn case_table() {
    let fx = fixture("conferral_content.json");
    let (mut n, mut bad) = (0, 0);
    for c in cases(&fx) {
        let rows: Vec<CRow> = c.at("rows").arr().iter().map(row).collect();
        let by: BTreeMap<&str, &CRow> = rows.iter().map(|r| (r.id.as_str(), r)).collect();
        let want: BTreeMap<String, (bool, bool, String)> = c
            .at("answers")
            .obj()
            .iter()
            .map(|(k, v)| (k.clone(), (v.at("counted").b(), v.at("in_force").b(), v.at("rule").s().to_string())))
            .collect();
        let mut lists: Vec<Vec<&CRow>> = vec![rows.iter().collect(), rows.iter().rev().collect()];
        for o in c.at("orders").arr() {
            lists.push(o.strs().iter().map(|i| by[i.as_str()]).collect());
        }
        for list in lists {
            n += 1;
            let got: BTreeMap<String, (bool, bool, String)> =
                run(&list, None).iter().map(|(k, a)| (k.clone(), show(a))).collect();
            if got != want {
                bad += 1;
                eprintln!("{}: got {got:?}, want {want:?}", c.at("name").s());
            }
        }
    }
    report("room content after a seat ends (conferral_content.py case table)", n, bad);
    assert_eq!(bad, 0);
}

/// Every history of up to three rows and a sample of those of four, as `check_conferral_content.py` builds
/// them, against the reference's answers (fixture `conferral_content_worlds.json`).
#[test]
fn histories() {
    let fx = fixture("conferral_content_worlds.json");
    let heads: Vec<CRow> = fx.at("heads").arr().iter().map(row).collect();
    let (mut n, mut bad) = (0, 0);
    for w in fx.at("worlds").arr() {
        let rows: Vec<CRow> = w.at("rows").arr().iter().map(row).collect();
        let list: Vec<&CRow> = heads.iter().chain(rows.iter()).collect();
        let got = run(&list, None);
        for (x, v) in w.at("answers").obj() {
            n += 1;
            let want = (v.arr()[0].b(), v.arr()[1].b(), v.arr()[2].s().to_string());
            if got.get(x).map(show) != Some(want.clone()) {
                bad += 1;
                if bad <= 5 {
                    eprintln!("{x}: got {:?}, want {want:?}, rows {rows:?}", got.get(x));
                }
            }
        }
        if got.len() != w.at("answers").obj().len() {
            bad += 1;
        }
    }
    report("room content, histories built row by row (conferral_content.py)", n, bad);
    assert_eq!(bad, 0);
}

/// Folding row by row with `changed` ends at `answers` over the same rows: over every history of the worlds
/// fixture, in the order it was built and with its rows arriving in reverse where the door allows.
#[test]
fn the_fold_by_arrival() {
    let fx = fixture("conferral_content_worlds.json");
    let heads: Vec<CRow> = fx.at("heads").arr().iter().map(row).collect();
    let seat = Seat { member: &|k: &String| k == "B" || k == "B2", counted: &|k: &String| k == "count" };
    let (mut n, mut bad) = (0, 0);
    for w in fx.at("worlds").arr() {
        let rows: Vec<CRow> = w.at("rows").arr().iter().map(row).collect();
        // the build order, and the reverse order where no row then precedes a row it names for the door
        let mut orders: Vec<Vec<&CRow>> = vec![rows.iter().collect()];
        let rev: Vec<&CRow> = rows.iter().rev().collect();
        let ok = rev.iter().enumerate().all(|(i, r)| r.names.iter().all(|m| !rev[i + 1..].iter().any(|q| &q.id == m)));
        if ok {
            orders.push(rev);
        }
        for order in orders {
            n += 1;
            let mut held: Vec<&CRow> = heads.iter().collect();
            let mut kept: BTreeMap<String, Answer<String>> = BTreeMap::new();
            for r in order {
                held.push(r);
                let by: BTreeMap<&str, &CRow> = held.iter().map(|r| (r.id.as_str(), *r)).collect();
                kept.extend(changed(&held, &r.id, &seat, &|a: &String, b: &String| in_past(&by, None, a, b)));
            }
            if kept != run(&held, None) {
                bad += 1;
            }
        }
    }
    report("room content, folded row by row with changed", n, bad);
    assert_eq!(bad, 0);
}

/// With no end among the rows, every content row of the member is counted, and in force unless its author's
/// own retraction is held: a caller need not call this module before it holds an end of the member's seat.
/// Over every history of the worlds fixture, with its ends taken out.
#[test]
fn no_end_among_the_rows() {
    let fx = fixture("conferral_content_worlds.json");
    let heads: Vec<CRow> = fx.at("heads").arr().iter().map(row).collect();
    let (mut n, mut bad) = (0, 0);
    for w in fx.at("worlds").arr() {
        let rows: Vec<CRow> = w.at("rows").arr().iter().map(row).collect();
        let list: Vec<&CRow> = heads.iter().chain(rows.iter()).filter(|r| r.kind != Kind::End).collect();
        for (x, a) in run(&list, None) {
            n += 1;
            let own = |r: &&CRow| list.iter().any(|t| t.id == x && t.signer == r.signer);
            let retracted = list.iter().filter(|r| r.retracts.as_ref() == Some(&x)).any(own);
            let (counted, in_force, rule) = show(&a);
            if !(counted && in_force != retracted && rule == if retracted { "W.retracted" } else { "no_end" }) {
                bad += 1;
            }
        }
    }
    report("room content with no end held (every row counted; in force unless retracted)", n, bad);
    assert_eq!(bad, 0);
}

/// A past that cannot tell gives no bit: with one roster head or end not held, every content row is either
/// undecided, naming that row, or judged as it is over the rows that are held.
#[test]
fn a_past_that_cannot_tell() {
    let fx = fixture("conferral_content.json");
    let (mut n, mut bad, mut undecided) = (0, 0, 0);
    for c in cases(&fx) {
        let rows: Vec<CRow> = c.at("rows").arr().iter().map(row).collect();
        for h in rows.iter().filter(|r| r.kind != Kind::Content) {
            let held: Vec<&CRow> = rows.iter().filter(|r| r.id != h.id).collect();
            let (dark, plain) = (run(&held, Some(&h.id)), run(&held, None));
            for (x, a) in &dark {
                n += 1;
                match a {
                    Answer::Undecided(i) if *i == h.id => undecided += 1,
                    Answer::Judged(_) if plain.get(x) == Some(a) => {}
                    other => {
                        bad += 1;
                        eprintln!("{}: without {}, {x} is {other:?}; held: {:?}", c.at("name").s(), h.id, plain.get(x));
                    }
                }
            }
        }
    }
    assert!(undecided > 0, "no case left a row undecided");
    report("room content, one row not held (undecided, never a wrong bit)", n, bad);
    assert_eq!(bad, 0);
}
