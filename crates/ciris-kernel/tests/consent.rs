//! Differential: the consent peer set, against the case table of `models/causal_kernel/check_consent.py`
//! (fixture `consent.json`): for every ask, whether a grant is in force, a principal's peer set, a bilateral peering,
//! and the grant a node may send a peer a row of a class under, read at a held row.
//!
//! Twice: (1) with the model's readings (the key view's verdicts, the person map, the one owner reading), the rows
//! concluded as listed and in reverse and admitted one at a time in both orders; (2) END TO END, with the crate's
//! own readings over the model's rows: `key_end::KeyReading` over the key lane, `seat::Persons::voice` and
//! `seat::Seats::owner` over the seat rows, each over the past the call names.

mod common;
use ciris_kernel::consent::{self, ConsentRow, Kind, Reading};
use ciris_kernel::graph::Graph;
use ciris_kernel::key_end::{self, KeyReading, KeyView};
use ciris_kernel::layers::{arrive, conclude, kept, Concluded};
use ciris_kernel::seat::{seat_rule, Persons, SeatLaw, Seats};
use common::*;
use std::collections::{BTreeMap, BTreeSet};

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

// a row as the consent view reads it: `kind` is the view's word (rows) or the model's (model_rows)
fn row(j: &J) -> CRow {
    let kind = match j.at("kind").s() {
        "grant" => Kind::Grant,
        "withdrawal" | "withdraws" | "recants" => Kind::Withdrawal,
        "announcement" | "announce" => Kind::Announcement,
        _ => Kind::Other,
    };
    let grant = kind == Kind::Grant;
    CRow {
        id: j.at("id").s().to_string(),
        kind,
        signer: j.at("signer").s().to_string(),
        names: j.at("names").strs(),
        peer: if grant { j.get("peer").and_then(|v| v.opt_s()) } else { None },
        classes: if grant { j.get("classes").map(|v| v.strs()).unwrap_or_default() } else { vec![] },
        at: if grant { opt_i(j, "at") } else { None },
        until: if grant { opt_i(j, "until") } else { None },
        of: if kind == Kind::Withdrawal { j.get("of").and_then(|v| v.opt_s()) } else { None },
        federation: j.get("federation").or_else(|| j.get("fed")).is_none_or(|v| v.b()),
    }
}

fn rule(p: &ciris_kernel::layers::Past<'_, '_, CRow>) -> bool {
    consent::conclude_rule(p)
}

// (1) the model's readings, carried in the fixture
struct Tables {
    voiced: BTreeSet<(String, String)>,
    persons: BTreeMap<String, String>,
    owners: BTreeMap<String, String>,
}

impl Tables {
    fn of(case: &J) -> Tables {
        let pairs = |p: &J| (p.arr()[0].s().to_string(), p.arr()[1].s().to_string());
        let map = |k: &str| -> BTreeMap<String, String> {
            case.at(k).obj().iter().map(|(a, b)| (a.clone(), b.s().to_string())).collect()
        };
        Tables {
            voiced: case.at("voiced").arr().iter().map(pairs).collect(),
            persons: map("persons"),
            owners: map("owners"),
        }
    }
}

impl Reading<String, String> for Tables {
    fn counts(&self, row: &String, key: &String) -> bool {
        self.voiced.contains(&(row.clone(), key.clone()))
    }
    fn person(&self, key: &String, row: &String) -> Option<String> {
        self.persons.get(&format!("{key}|{row}")).cloned()
    }
    fn owner(&self, node: &String, row: Option<&String>, inclusive: bool) -> Option<String> {
        let at = row.map_or(String::new(), |r| r.clone());
        self.owners.get(&format!("{node}|{at}|{}", if inclusive { 1 } else { 0 })).cloned()
    }
}

// (2) the crate's own readings over the model's rows: the key lane concluded by key_end's rule, the seat rows by the
// seat rule, each read over the past a call names
struct Crate<'c, 'a> {
    key: KeyReading<'c, 'a, TRow>,
    seats: &'c Concluded<'a, TRow>,
    law: &'c SeatLaw,
}

impl<'a> Crate<'_, 'a> {
    // the concluded seat rows in `row`'s past (with `row` where `inclusive`); every concluded row with no row
    fn past(&self, row: Option<&String>, inclusive: bool) -> Vec<&'a TRow> {
        let c = self.seats;
        match row.map(|r| c.g.idx(r)) {
            None => c.cs().iter().map(|&q| c.g.row(q)).collect(),
            Some(None) => vec![],
            Some(Some(i)) => c
                .cs()
                .iter()
                .copied()
                .filter(|&q| c.g.in_past(q, i) || (inclusive && q == i))
                .map(|q| c.g.row(q))
                .collect(),
        }
    }
}

impl Reading<String, String> for Crate<'_, '_> {
    fn counts(&self, row: &String, key: &String) -> bool {
        self.key.counts(row, key)
    }
    fn person(&self, key: &String, row: &String) -> Option<String> {
        let rows = self.past(Some(row), false);
        Persons::over(&rows, self.law, &DictCut, None).voice(key)
    }
    fn owner(&self, node: &String, row: Option<&String>, inclusive: bool) -> Option<String> {
        let rows = self.past(row, inclusive);
        let c = Concluded::with(Graph::new(rows.iter().copied()), None);
        Seats::new(&c, self.law, &DictCut, None).owner(node)
    }
}

fn ask(c: &Concluded<'_, CRow>, a: &J, rd: &dyn Reading<String, String>) -> J {
    let at = a.get("at").and_then(|v| v.opt_s());
    let now = opt_i(a, "now");
    let s = |k: &str| a.at(k).s().to_string();
    match a.at("ask").s() {
        "send" => consent::may_send(c, &s("node"), &s("peer"), a.at("class").s(), at.as_ref(), now, rd)
            .map_or(J::Null, |g| J::Str(g.clone())),
        "peers" => {
            J::Arr(consent::peer_set(c, &s("principal"), at.as_ref(), now, rd).into_iter().map(J::Str).collect())
        }
        "bilateral" => J::Bool(consent::bilateral(c, &s("a"), &s("b"), at.as_ref(), now, rd)),
        "force" => J::Bool(consent::in_force(c, &s("grant"), at.as_ref(), now, rd)),
        k => panic!("ask {k}"),
    }
}

fn run(case: &J, c: &Concluded<'_, CRow>, rd: &dyn Reading<String, String>, n: &mut usize, bad: &mut usize, how: &str) {
    for a in case.at("asks").arr() {
        *n += 1;
        let got = ask(c, a, rd);
        if &got != a.at("want") {
            *bad += 1;
            eprintln!("{} ({how}): {a:?}: got {got:?}", case.at("name").s());
        }
    }
}

#[test]
fn case_table() {
    let fx = fixture("consent.json");
    let (mut n, mut bad) = (0, 0);
    for case in fx.at("cases").arr() {
        let rows: Vec<CRow> = case.at("rows").arr().iter().map(row).collect();
        let rev: Vec<CRow> = rows.iter().rev().cloned().collect();
        let rd = Tables::of(case);
        let held = [
            conclude(kept(&rows, |_| true), rule, None),
            conclude(kept(&rev, |_| true), rule, None),
            arrive(&rows, rule, None, |_| true),
            arrive(&rev, rule, None, |_| true),
        ];
        for c in &held {
            run(case, c, &rd, &mut n, &mut bad, "the model's readings");
        }
    }
    report("the consent peer set (check_consent.py case table)", n, bad);
    assert_eq!(bad, 0);
}

#[test]
fn end_to_end() {
    let fx = fixture("consent.json");
    let law: SeatLaw = law_of(fx.at("law"));
    let (mut n, mut bad) = (0, 0);
    for case in fx.at("cases").arr() {
        let refs: BTreeMap<String, String> =
            case.at("refs").obj().iter().map(|(k, v)| (k.clone(), v.s().to_string())).collect();
        let model = case.at("model_rows").arr();
        let trows = rows_with_refs(model, &refs);
        let rows: Vec<CRow> = model.iter().map(row).collect();
        let kc = conclude(kept(&trows, |_| true), key_end::conclude_rule, None);
        let sc = conclude(kept(&trows, |_| true), |p| seat_rule(p, &law, &DictCut, &|_| true), None);
        let reader = case.get("reader").and_then(|r| r.opt_s());
        let rd = Crate {
            key: KeyReading { c: &kc, reader, final_: BTreeSet::new(), roster: BTreeSet::new() },
            seats: &sc,
            law: &law,
        };
        let c = conclude(kept(&rows, |_| true), rule, None);
        run(case, &c, &rd, &mut n, &mut bad, "end to end");
    }
    report("the consent peer set end to end (KeyReading, Persons, Seats::owner)", n, bad);
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
    };
    let rows = vec![g("g1", "N", "P"), g("g2", "O", "Q"), g("g3", "X", "R")];
    let c = conclude(kept(&rows, |_| true), rule, None);
    let owned = |o: Option<&str>| Tables {
        voiced: rows.iter().map(|r| (r.id.clone(), r.signer.clone())).collect(),
        persons: BTreeMap::new(),
        owners: o.map(|o| [("N||1".to_string(), o.to_string())].into_iter().collect()).unwrap_or_default(),
    };
    let addressed: BTreeSet<String> = ["P", "Q", "R", "S"].iter().map(|s| s.to_string()).collect();
    let set = consent::replication_set(&c, &"N".into(), &addressed, None, None, &owned(Some("O")));
    assert_eq!(set, ["P", "Q"].iter().map(|s| s.to_string()).collect());
    let set = consent::replication_set(&c, &"N".into(), &addressed, None, None, &owned(None));
    assert_eq!(set, ["P"].iter().map(|s| s.to_string()).collect());
}
