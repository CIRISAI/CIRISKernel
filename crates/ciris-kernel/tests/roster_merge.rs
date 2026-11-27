//! The roster merge (`seat::merge_concludes`, the text's `group:roster` version), replayed from
//! `models/causal_kernel/check_roster_merge.py` (fixture `roster_merge.json`): each merge's conclusion, and the
//! reader's roster after it (members and `moderate`), for a reader with no row and for R1 and R2.

mod common;
use ciris_kernel::layers::{conclude, kept};
use ciris_kernel::seat::{for_reader, seat_rule, Obj, Seats};
use common::{fixture, law_of, report, rows_with_refs, DictCut};
use std::collections::BTreeMap;

#[test]
fn roster_merge_replay() {
    let fx = fixture("roster_merge.json");
    let law = law_of(fixture("seat.json").at("law"));
    let spec = DictCut;
    let obj = Obj::Row("g".to_string());
    let (mut cases, mut bad) = (0, 0);
    for c in fx.at("cases").arr() {
        let refs: BTreeMap<String, String> =
            c.at("refs").obj().iter().map(|(k, v)| (k.clone(), v.s().to_string())).collect();
        let rows = rows_with_refs(c.at("rows").arr(), &refs);
        let k = kept(&rows, |_| true);
        let cc = conclude(k, |p| seat_rule(p, &law, &spec, &|_| true), None);
        let name = c.at("name").s();
        let mut wrong = |what: &str| {
            bad += 1;
            eprintln!("roster merge {name}: {what}");
        };
        for (id, want) in c.at("concluded").obj() {
            let got = cc.g.idx(id).is_some_and(|i| cc.cs().contains(&i));
            if got != want.b() {
                wrong(&format!("{id} concluded {got}"));
            }
        }
        let own = c.get("reader").and_then(|r| r.opt_s());
        let (rc, rv) = for_reader(&cc, &law, &spec, own.as_ref());
        let q = match &own {
            Some(k) => Seats::for_reader(&rc, &law, &spec, k, &rv),
            None => Seats::new(&rc, &law, &spec, None),
        };
        let mut members: Vec<String> = q.holders("member", &obj, None).into_iter().collect();
        members.sort();
        if members != c.at("members").strs() {
            wrong(&format!("members {members:?}"));
        }
        let mut moderate: Vec<String> = q.holders("moderate", &obj, None).into_iter().collect();
        moderate.sort();
        if moderate != c.at("moderate").strs() {
            wrong(&format!("moderate {moderate:?}"));
        }
        cases += 1;
    }
    report("the roster merge against check_roster_merge.py", cases, bad);
    assert_eq!(bad, 0);
}
