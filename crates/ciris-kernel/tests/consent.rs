//! Differential: the consent peer set, against the case table of `models/causal_kernel/check_consent.py`
//! (fixture `consent.json`): for every ask, whether a grant is in force, a principal's peer set, and the grant a
//! node may send a peer a row of a class under, read at a held row, with the rows concluded as listed and in
//! reverse and admitted one at a time in both orders. The owner of a send ask is the one the model's seat walk
//! gives at the reading row (the crate takes it from the caller).

mod common;
use ciris_kernel::consent::{self, ConsentRow, Kind};
use ciris_kernel::key_end::KeyView;
use ciris_kernel::layers::{arrive, conclude, kept, Concluded, Past};
use common::*;
use std::collections::BTreeSet;

#[derive(Clone, Debug)]
struct CRow {
    id: String,
    kind: Kind,
    signer: String,
    names: Vec<String>,
    peer: Option<String>,
    classes: Vec<String>,
    at: Option<i64>,
    until: Option<i64>,
    of: Option<String>,
    federation: bool,
    // on a withdrawal: the owner of the withdrawn grant's signer over the withdrawal's past, as the model reads it
    owner_of_signer: Option<String>,
}

impl ciris_kernel::Row for CRow {
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

impl ConsentRow for CRow {
    type Class = String;
    type T = i64;
    fn kind(&self) -> Kind {
        self.kind
    }
    fn peer(&self) -> Option<&String> {
        self.peer.as_ref()
    }
    fn classes(&self) -> &[String] {
        &self.classes
    }
    fn at(&self) -> Option<i64> {
        self.at
    }
    fn until(&self) -> Option<i64> {
        self.until
    }
    fn federation(&self) -> bool {
        self.federation
    }
    fn withdraws(&self) -> Option<&String> {
        self.of.as_ref()
    }
}

fn opt_i(j: &J, k: &str) -> Option<i64> {
    j.get(k).filter(|v| !v.is_null()).map(|v| v.i())
}

fn row(j: &J) -> CRow {
    let kind = match j.at("kind").s() {
        "grant" => Kind::Grant,
        "withdrawal" => Kind::Withdrawal,
        "announcement" => Kind::Announcement,
        "other" => Kind::Other,
        k => panic!("kind {k}"),
    };
    CRow {
        id: j.at("id").s().to_string(),
        kind,
        signer: j.at("signer").s().to_string(),
        names: j.at("names").strs(),
        peer: j.get("peer").and_then(|v| v.opt_s()),
        classes: j.get("classes").map(|v| v.strs()).unwrap_or_default(),
        at: opt_i(j, "at"),
        until: opt_i(j, "until"),
        of: j.get("of").and_then(|v| v.opt_s()),
        federation: j.get("federation").is_some_and(|v| v.b()),
        owner_of_signer: j.get("owner_of_signer").and_then(|v| v.opt_s()),
    }
}

// the caller's owner reading at a withdrawal: here, the model's, carried on the withdrawal row
fn rule(p: &Past<'_, '_, CRow>) -> bool {
    consent::conclude_rule(p, |_, p| p.row().owner_of_signer.clone())
}

// the key view as the model reads it (key_end.counts_by for the case's reader): the (grant, key) pairs that count
struct Voiced(BTreeSet<(String, String)>);
impl KeyView<String, String> for Voiced {
    fn counts(&self, row: &String, key: &String) -> bool {
        self.0.contains(&(row.clone(), key.clone()))
    }
}

fn ask(c: &Concluded<'_, CRow>, a: &J, kv: &Voiced) -> J {
    let kv: Option<&dyn KeyView<String, String>> = Some(kv);
    let at = a.get("at").and_then(|v| v.opt_s());
    let now = opt_i(a, "now");
    match a.at("ask").s() {
        "send" => {
            let owner = a.get("owner").and_then(|v| v.opt_s());
            let g = consent::may_send(
                c,
                &a.at("node").s().to_string(),
                owner.as_ref(),
                &a.at("peer").s().to_string(),
                a.at("class").s(),
                at.as_ref(),
                now,
                kv,
            );
            g.map_or(J::Null, |g| J::Str(g.clone()))
        }
        "peers" => {
            let ps = consent::peer_set(c, &a.at("principal").s().to_string(), at.as_ref(), now, kv);
            J::Arr(ps.into_iter().map(J::Str).collect())
        }
        "bilateral" => {
            J::Bool(consent::bilateral(c, &a.at("a").s().to_string(), &a.at("b").s().to_string(), at.as_ref(), now, kv))
        }
        "force" => J::Bool(consent::in_force(c, &a.at("grant").s().to_string(), at.as_ref(), now, kv)),
        k => panic!("ask {k}"),
    }
}

#[test]
fn case_table() {
    let fx = fixture("consent.json");
    let (mut n, mut bad) = (0, 0);
    for case in fx.at("cases").arr() {
        let rows: Vec<CRow> = case.at("rows").arr().iter().map(row).collect();
        let rev: Vec<CRow> = rows.iter().rev().cloned().collect();
        let kv = Voiced(
            case.at("voiced").arr().iter().map(|p| (p.arr()[0].s().to_string(), p.arr()[1].s().to_string())).collect(),
        );
        let held = [
            conclude(kept(&rows, |_| true), rule, None),
            conclude(kept(&rev, |_| true), rule, None),
            arrive(&rows, rule, None, |_| true),
            arrive(&rev, rule, None, |_| true),
        ];
        for c in &held {
            for a in case.at("asks").arr() {
                n += 1;
                let got = ask(c, a, &kv);
                if &got != a.at("want") {
                    bad += 1;
                    eprintln!("{}: {a:?}: got {got:?}", case.at("name").s());
                }
            }
        }
    }
    report("the consent peer set (check_consent.py case table)", n, bad);
    assert_eq!(bad, 0);
}

#[test]
fn classes_and_fan_out() {
    // covers: a namespace prefix by its trailing colon, a corpus class by itself
    assert!(consent::covers(&["capacity:"], "capacity:cpu:v1"));
    assert!(!consent::covers(&["trace:"], "trace_summary:v1"));
    assert!(!consent::covers(&["capacity"], "capacity:cpu:v1"));
    assert!(consent::covers(&["post"], "post"));
    assert!(!consent::covers(&["post"], "posting"));
    // Edge's fan-out: the addressed peers in the principals' peer sets
    let g = |id: &str, s: &str, p: &str| CRow {
        id: id.into(),
        kind: Kind::Grant,
        signer: s.into(),
        names: vec![],
        peer: Some(p.into()),
        classes: vec!["capacity:".into()],
        at: Some(1),
        until: None,
        of: None,
        federation: false,
        owner_of_signer: None,
    };
    let rows = vec![g("g1", "N", "P"), g("g2", "O", "Q"), g("g3", "X", "R")];
    let c = conclude(kept(&rows, |_| true), rule, None);
    let addressed: BTreeSet<String> = ["P", "Q", "R", "S"].iter().map(|s| s.to_string()).collect();
    let set = consent::replication_set(&c, &"N".into(), Some(&"O".into()), &addressed, None, None, None);
    assert_eq!(set, ["P", "Q"].iter().map(|s| s.to_string()).collect());
    let set = consent::replication_set(&c, &"N".into(), None, &addressed, None, None, None);
    assert_eq!(set, ["P"].iter().map(|s| s.to_string()).collect());
}
