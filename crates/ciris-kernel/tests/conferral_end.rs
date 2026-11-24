//! Differential: the end of a conferral, against the case table of `models/causal_kernel/conferral_end.py`
//! (fixture `conferral_end.json`, which persist also runs): every act's `counted`, `in_force` and deciding
//! rule, with the rows listed in each arrival order the fixture gives and in reverse; then what a past that
//! cannot tell does, and two ends.

mod common;
use ciris_kernel::conferral::{answers, Answer, ConferralRow, Kind, Refused, Role, Standing, Who};
use common::*;
use std::collections::{BTreeMap, BTreeSet};

#[derive(Clone, Debug)]
struct CRow {
    id: String,
    kind: Kind,
    signer: String,
    names: Vec<String>,
    head: Option<String>,
    of: Option<String>,
    target: Option<String>,
    via: Option<String>,
    lifts: bool,
}

impl ConferralRow for CRow {
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
    fn of(&self) -> Option<&String> {
        self.of.as_ref()
    }
    fn target(&self) -> Option<&String> {
        self.target.as_ref()
    }
    fn via(&self) -> Option<&String> {
        self.via.as_ref()
    }
    fn lifts(&self) -> bool {
        self.lifts
    }
}

fn row(j: &J) -> CRow {
    let opt = |k: &str| j.get(k).and_then(|v| v.opt_s());
    CRow {
        id: j.at("id").s().to_string(),
        kind: match j.at("kind").s() {
            "head" => Kind::Head,
            "act" => Kind::Act,
            "end" => Kind::End,
            "receipt" => Kind::Receipt,
            "removal" => Kind::Removal,
            "accept" => Kind::Accept,
            "receipter_end" => Kind::ReceipterEnd,
            // a row withdrawing a receipt: refused at the door, and read by nothing if held
            "withdrawal" => Kind::Other,
            k => panic!("kind {k}"),
        },
        signer: j.at("signer").s().to_string(),
        names: j.at("names").strs(),
        head: opt("head"),
        of: opt("of"),
        target: opt("target"),
        via: opt("via"),
        lifts: j.get("lifts").is_some_and(|v| v.b()),
    }
}

#[allow(clippy::ptr_arg)] // the key type is String
fn role(k: &String) -> Role {
    match k.as_str() {
        "A" => Role::Conferrer,
        "B" => Role::Grantee,
        "D" => Role::CoHolder,
        "R" => Role::Receipter,
        _ => Role::Other,
    }
}

/// The causal past by what the held rows name. `hidden` is a row the caller does not hold: a walk that reaches
/// it cannot tell, and says which row it needs.
struct Names<'a> {
    by: BTreeMap<&'a str, &'a CRow>,
    hidden: Option<&'a str>,
}

impl Names<'_> {
    fn in_past(&self, a: &str, b: &str) -> Result<bool, String> {
        let (mut todo, mut seen, mut need) = (vec![b], BTreeSet::new(), None);
        while let Some(x) = todo.pop() {
            if Some(x) == self.hidden {
                need = Some(x.to_string());
                continue;
            }
            let Some(r) = self.by.get(x) else { continue };
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
}

fn run(rows: &[&CRow], c: &J, hidden: Option<&str>) -> Result<BTreeMap<String, Answer<String>>, Refused<String>> {
    let acks = c.at("reader_acks").strs();
    let st = Standing {
        role: &role,
        other_standing: c.at("other_standing").b(),
        who: if c.at("who").s() == "none" { Who::ConferrerOnly } else { Who::All },
        reader_acks: &acks,
    };
    let past = Names { by: rows.iter().map(|r| (r.id.as_str(), *r)).collect(), hidden };
    answers(rows, &st, &|a: &String, b: &String| past.in_past(a, b))
}

fn show(a: &Answer<String>) -> (bool, bool, String) {
    match a {
        Answer::Judged(j) => (j.counted, j.in_force, j.rule.as_str().to_string()),
        Answer::Undecided(i) => panic!("undecided, needs {i}"),
    }
}

#[test]
fn case_table() {
    let fx = fixture("conferral_end.json");
    let (mut n, mut bad) = (0, 0);
    for c in fx.at("cases").arr() {
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
                run(&list, c, None).expect("one end").iter().map(|(k, a)| (k.clone(), show(a))).collect();
            if got != want {
                bad += 1;
                eprintln!("{}: got {got:?}, want {want:?}", c.at("name").s());
            }
        }
    }
    report("the end of a conferral (conferral_end.py case table)", n, bad);
    assert_eq!(bad, 0);
}

/// A past that cannot tell gives no bit: with one row not held, every act is either undecided, naming that
/// row, or judged as it is over the rows that are held (the walk never needed the missing one).
#[test]
fn a_past_that_cannot_tell() {
    let fx = fixture("conferral_end.json");
    let (mut n, mut bad, mut undecided) = (0, 0, 0);
    for c in fx.at("cases").arr() {
        let rows: Vec<CRow> = c.at("rows").arr().iter().map(row).collect();
        for h in rows.iter().filter(|r| r.kind != Kind::Act) {
            let held: Vec<&CRow> = rows.iter().filter(|r| r.id != h.id).collect();
            if held.iter().filter(|r| r.kind == Kind::End).count() > 1 {
                continue;
            }
            let dark = run(&held, c, Some(&h.id)).expect("one end");
            let plain = run(&held, c, None).expect("one end");
            for (x, a) in &dark {
                n += 1;
                match a {
                    Answer::Undecided(i) if *i == h.id => undecided += 1,
                    Answer::Judged(_) if plain.get(x) == Some(a) => {}
                    other => {
                        bad += 1;
                        eprintln!(
                            "{}: without {}, {x} is {other:?}; over the held rows {:?}",
                            c.at("name").s(),
                            h.id,
                            plain.get(x)
                        );
                    }
                }
            }
        }
    }
    assert!(undecided > 0, "no case left an act undecided");
    report("the end of a conferral, one row not held (undecided, never a wrong bit)", n, bad);
    assert_eq!(bad, 0);
}

#[test]
fn two_ends_are_refused() {
    let fx = fixture("conferral_end.json");
    let c = fx.at("cases").arr().iter().find(|c| c.at("name").s() == "forward_at_end_head").expect("case");
    let mut rows: Vec<CRow> = c.at("rows").arr().iter().map(row).collect();
    let mut e2 = rows.iter().find(|r| r.kind == Kind::End).expect("end").clone();
    e2.id = "E2".into();
    rows.push(e2);
    let list: Vec<&CRow> = rows.iter().collect();
    assert!(matches!(run(&list, c, None), Err(Refused::SeveralEnds(..))));
}

/// One wire receipt names many acts (`refs.also.ack`). A caller presents it as one row per act named, each
/// with `of` that act, and all of them carry the wire row's own id and names. The answers are those of
/// separate receipts: a bulk receipt keeps each act it names, an act it does not name is not kept, and one
/// that has the end in its past keeps nothing.
#[test]
fn one_receipt_naming_several_acts() {
    let mk = |id: &str, kind: Kind, signer: &str, names: &[&str], head: Option<&str>, of: Option<&str>| CRow {
        id: id.into(),
        kind,
        signer: signer.into(),
        names: names.iter().map(|n| n.to_string()).collect(),
        head: head.map(String::from),
        of: of.map(String::from),
        target: None,
        via: None,
        lifts: false,
    };
    let base = [
        mk("H0", Kind::Head, "count", &[], None, None),
        mk("H1", Kind::Head, "count", &["H0"], None, None),
        mk("b1", Kind::Act, "B", &["H0"], Some("H0"), None),
        mk("b2", Kind::Act, "B", &["H0"], Some("H0"), None),
        mk("b3", Kind::Act, "B", &["H0"], Some("H0"), None),
        mk("E", Kind::End, "A", &["H1"], Some("H1"), None),
    ];
    let st = Standing { role: &role, other_standing: false, who: Who::All, reader_acks: &[] };
    let judge = |extra: Vec<CRow>| {
        let rows: Vec<CRow> = base.iter().cloned().chain(extra).collect();
        let refs: Vec<&CRow> = rows.iter().collect();
        let past = Names { by: refs.iter().map(|r| (r.id.as_str(), *r)).collect(), hidden: None };
        let got = answers(&refs, &st, &|a: &String, b: &String| past.in_past(a, b)).expect("one end");
        ["b1", "b2", "b3"].map(|x| show(&got[x]))
    };
    let kept = (true, true, "E8.receipt".to_string());
    let out = (true, false, "E2.forward".to_string());
    // a co-holder's bulk receipt of b1 and b2, presented as two rows under one id
    let bulk = |names: &[&str]| {
        vec![mk("q", Kind::Receipt, "D", names, None, Some("b1")), mk("q", Kind::Receipt, "D", names, None, Some("b2"))]
    };
    assert_eq!(judge(bulk(&["b1", "b2"])), [kept.clone(), kept.clone(), out.clone()]);
    // the same answers as two receipts under two ids
    let two = vec![
        mk("q1", Kind::Receipt, "D", &["b1"], None, Some("b1")),
        mk("q2", Kind::Receipt, "D", &["b2"], None, Some("b2")),
    ];
    assert_eq!(judge(two), [kept.clone(), kept, out.clone()]);
    // a bulk receipt that has the end in its past keeps nothing
    assert_eq!(judge(bulk(&["b1", "b2", "E"])), [out.clone(), out.clone(), out]);
    report("the end of a conferral: one receipt naming several acts, presented as one row per act", 9, 0);
}
