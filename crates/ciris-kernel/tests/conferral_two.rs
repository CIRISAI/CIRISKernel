//! Differential: one row that needs two standings, against the case table of
//! `models/causal_kernel/check_conferral_two.py` under its reading `acc` (fixture `conferral_two.json`): for
//! every act and owner whether it counts and is in force, and why (the binding it stands under and the rule
//! that decides under each record, or why it counts for nobody), with the rows as listed and in reverse; then
//! what a row that is not held does, and two re-bindings of one binding.

mod common;
use ciris_kernel::conferral::{Refused, Role, Standing, Who, DEPUTY_DEPTH};
use ciris_kernel::standing::{answers, Answer, Kind, StandingRow};
use common::*;
use std::collections::{BTreeMap, BTreeSet};

#[derive(Clone, Debug)]
struct SRow {
    id: String,
    kind: Kind,
    signer: String,
    names: Vec<String>,
    head: Option<String>,
    on: Option<String>,
    owner: Option<String>,
    via: Option<String>,
    sub_delegation: bool,
    // an acceptance's refs.also.cites, where the row states them (N7)
    cites: Option<Vec<String>>,
    // a binding's node, where the row states it
    node: Option<String>,
}

impl StandingRow for SRow {
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
    fn on(&self) -> Option<&String> {
        self.on.as_ref()
    }
    fn owner(&self) -> Option<&String> {
        self.owner.as_ref()
    }
    fn via(&self) -> Option<&String> {
        self.via.as_ref()
    }
    fn sub_delegation(&self) -> bool {
        self.sub_delegation
    }
    fn cites(&self) -> Option<&[String]> {
        self.cites.as_deref()
    }
    fn node(&self) -> Option<&String> {
        self.node.as_ref()
    }
}

fn row(j: &J) -> SRow {
    let opt = |k: &str| j.get(k).and_then(|v| v.opt_s());
    SRow {
        id: j.at("id").s().to_string(),
        kind: match j.at("kind").s() {
            "bundle" => Kind::Bundle,
            "binding" => Kind::Binding,
            "acceptance" => Kind::Acceptance,
            "act" => Kind::Act,
            "end" => Kind::GrantEnd,
            "receipt" => Kind::Receipt,
            k => panic!("kind {k}"),
        },
        signer: j.at("signer").s().to_string(),
        names: j.at("names").strs(),
        head: opt("head"),
        on: opt("on"),
        owner: opt("owner"),
        via: opt("via"),
        sub_delegation: j.get("sub_delegation").is_some_and(|x| x.b()),
        cites: j.get("cites").map(|x| x.strs()),
        node: opt("node"),
    }
}

// who a key is to the grant: the count confers it, the node holds it
#[allow(clippy::ptr_arg)] // the key type is String
fn role(k: &String) -> Role {
    match k.as_str() {
        "count" => Role::Conferrer,
        "N" => Role::Grantee,
        _ => Role::Other,
    }
}

/// The causal past by what the held rows name. `hidden` is a row the caller does not hold: a walk that reaches
/// it cannot tell, and says which row it needs.
fn in_past(by: &BTreeMap<&str, &SRow>, hidden: Option<&str>, a: &str, b: &str) -> Result<bool, String> {
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

type Got = BTreeMap<String, Answer<String, String>>;

fn run(rows: &[&SRow], acks: &[String], hidden: Option<&str>) -> Result<Got, Refused<String>> {
    let st =
        Standing { role: &role, other_standing: false, who: Who::All, reader_acks: acks, deputy_depth: DEPUTY_DEPTH };
    let by: BTreeMap<&str, &SRow> = rows.iter().map(|r| (r.id.as_str(), *r)).collect();
    answers(rows, &st, &|a: &String, b: &String| in_past(&by, hidden, a, b))
}

// per owner (counted, in force), and why: (reason, binding, the grant's rule, the binding's rule)
type Shown = (BTreeMap<String, (bool, bool)>, (String, Option<String>, Option<String>, Option<String>));

fn show(a: &Answer<String, String>) -> Shown {
    let mut per: BTreeMap<String, (bool, bool)> =
        ["O1", "O2"].iter().map(|o| (o.to_string(), (false, false))).collect();
    match a {
        Answer::Stands(s) => {
            per.insert(s.owner.clone(), (s.counted, s.in_force));
            let rule = |r: ciris_kernel::conferral::Rule| Some(r.as_str().to_string());
            (per, ("stands".into(), Some(s.binding.clone()), rule(s.grant.rule), rule(s.under.rule)))
        }
        Answer::Nobody(why) => (per, (why.as_str().into(), None, None, None)),
        // the row to fetch, as the reference names it
        Answer::Undecided(i) => (per, ("undecided".into(), Some(i.clone()), None, None)),
    }
}

fn want(c: &J) -> BTreeMap<String, Shown> {
    c.at("answers")
        .obj()
        .iter()
        .map(|(x, per)| {
            let w = c.at("why").at(x);
            let per = per.obj().iter().map(|(o, v)| (o.clone(), (v.at("counted").b(), v.at("in_force").b()))).collect();
            let opt = |k: &str| w.at(k).opt_s();
            (x.clone(), (per, (w.at("reason").s().to_string(), opt("binding"), opt("grant"), opt("under"))))
        })
        .collect()
}

#[test]
fn case_table() {
    let fx = fixture("conferral_two.json");
    let (mut n, mut bad) = (0, 0);
    for c in fx.at("cases").arr() {
        let rows: Vec<SRow> = c.at("rows").arr().iter().map(row).collect();
        let acks = c.at("reader_acks").strs();
        let want = want(c);
        for list in [rows.iter().collect::<Vec<_>>(), rows.iter().rev().collect()] {
            n += 1;
            let got: BTreeMap<String, Shown> =
                run(&list, &acks, None).expect("one end").iter().map(|(k, a)| (k.clone(), show(a))).collect();
            if got != want {
                bad += 1;
                eprintln!("{}: got {got:?}, want {want:?}", c.at("name").s());
            }
        }
    }
    report("one row under a root grant and an owner binding (check_conferral_two.py case table, acc)", n, bad);
    assert_eq!(bad, 0);
}

/// With one row not held, every act is either undecided, naming that row, or answered as it is over the rows
/// that are held: never a bit the missing row would change.
#[test]
fn a_row_not_held() {
    let fx = fixture("conferral_two.json");
    let (mut n, mut bad, mut undecided) = (0, 0, 0);
    for c in fx.at("cases").arr() {
        let rows: Vec<SRow> = c.at("rows").arr().iter().map(row).collect();
        let acks = c.at("reader_acks").strs();
        // any row withheld, a deputy edge among them
        for h in rows.iter() {
            let held: Vec<&SRow> = rows.iter().filter(|r| r.id != h.id).collect();
            let dark = run(&held, &acks, Some(&h.id)).expect("one end");
            // the same rows with a past that stops at the missing row and says no
            let plain = run(&held, &acks, None).expect("one end");
            for (x, a) in &dark {
                n += 1;
                match a {
                    Answer::Undecided(i) if *i == h.id => undecided += 1,
                    // answered as over the rows held (an edge the case itself does not hold stays undecided)
                    _ if plain.get(x) == Some(a) => {}
                    other => {
                        bad += 1;
                        eprintln!("{}: without {}, {x} is {other:?}; plain {:?}", c.at("name").s(), h.id, plain.get(x));
                    }
                }
            }
        }
    }
    assert!(undecided > 0, "no case left an act undecided");
    report("one row under a root grant and an owner binding, one row not held (undecided, never a wrong bit)", n, bad);
    assert_eq!(bad, 0);
}

#[test]
fn two_rebindings_of_one_binding_are_refused() {
    let fx = fixture("conferral_two.json");
    let c = fx.at("cases").arr().iter().find(|c| c.at("name").s() == "under_the_new_owner").expect("case");
    let mut rows: Vec<SRow> = c.at("rows").arr().iter().map(row).collect();
    // an act under the first binding, and a second re-binding of it
    let mut x = rows.iter().find(|r| r.kind == Kind::Act).expect("act").clone();
    (x.id, x.on) = ("x9".into(), Some("A0".into()));
    let mut b = rows.iter().find(|r| r.id == "B1").expect("B1").clone();
    b.id = "B1b".into();
    rows.extend([x, b]);
    let list: Vec<&SRow> = rows.iter().collect();
    assert!(matches!(run(&list, &[], None), Err(Refused::SeveralEnds(..))));
}
