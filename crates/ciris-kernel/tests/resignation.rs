//! The wrap set: the keys a node wraps a room's key to and serves its rows to, `Seats::holders` over the fold of
//! the tips less every member whose own end of its seat the node holds, at once and with no counted row
//! (CC 2.4.1.1). Replayed from `models/causal_kernel/check_resignation.py` (fixture `resignation.json`): its
//! hand-written cases and every set of its rows, each with the rows that conclude, the wrap set, the room's whole
//! roster (`Seats::roster`) and its dissolution (`Seats::dissolved`), in two rooms: `member`, a community whose
//! roster is the wrap set (what a store reads), and `holder`, an accord's holders, a seat that is no roster seat.

mod common;
use ciris_kernel::layers::{conclude, kept};
use ciris_kernel::seat::{seat_rule, Obj, Seats};
use common::{fixture, law_of, report, rows_with_refs, sorted_ids, DictCut};
use std::collections::BTreeMap;

#[test]
fn wrap_set_replay() {
    let fx = fixture("resignation.json");
    let law = law_of(fixture("seat.json").at("law"));
    let obj = Obj::Row(fx.at("obj").s().to_string());
    let (mut cases, mut bad) = (0, 0);
    for c in fx.at("cases").arr() {
        let (name, scope) = (c.at("name").s(), c.at("scope").s());
        let refs: BTreeMap<String, String> =
            c.at("refs").obj().iter().map(|(k, v)| (k.clone(), v.s().to_string())).collect();
        let rows = rows_with_refs(c.at("rows").arr(), &refs);
        let cc = conclude(kept(&rows, |_| true), |p| seat_rule(p, &law, &DictCut, &|_| true), None);
        let mut cmp = |ok: bool, what: String| {
            cases += 1;
            if !ok {
                bad += 1;
                eprintln!("{name}: {what}");
            }
        };
        for (i, w) in c.at("c").arr().iter().enumerate() {
            cmp(cc.concluded(i) == w.b(), format!("concluded {}", cc.g.row(i).id));
        }
        let q = Seats::new(&cc, &law, &DictCut, None);
        let wrap = sorted_ids(&q.holders(scope, &obj, None));
        cmp(wrap == c.at("wrap").strs(), format!("wrap set {wrap:?}"));
        let roster = sorted_ids(&q.roster(&obj));
        cmp(roster == c.at("roster").strs(), format!("roster {roster:?}"));
        // in the community, persist's read: the roster is the wrap set
        if c.at("room").s() == "member" {
            cmp(roster == wrap, format!("roster {roster:?} is not the wrap set {wrap:?}"));
        }
        cmp(q.dissolved(&obj) == c.at("dissolved").b(), format!("dissolved {}", q.dissolved(&obj)));
    }
    report("the wrap set against check_resignation.py", cases, bad);
    assert_eq!(bad, 0);
}
