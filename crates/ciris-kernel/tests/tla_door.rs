//! Replay of every reachable state of `models/tla/Door.tla`, as TLC dumped it (fixture `tla_door.json`, written
//! by `tools/tla_door_fixture.py`), through the crate's door: in each state the rows TLC holds are exactly
//! what `layers::kept` keeps of the rows offered, and what `layers::arrive` holds in two arrival orders of them.

mod common;
#[path = "common/dag.rs"]
mod dag;
use ciris_kernel::layers::{arrive, kept};
use common::*;
use dag::N;

#[test]
fn every_tlc_state_of_the_door() {
    let fx = fixture("tla_door.json");
    let names: std::collections::BTreeMap<u32, Vec<u32>> = fx
        .at("names")
        .obj()
        .iter()
        .map(|(k, v)| (k.parse().unwrap(), v.arr().iter().map(|x| x.i() as u32).collect()))
        .collect();
    let malformed: Vec<u32> = fx.at("malformed").arr().iter().map(|x| x.i() as u32).collect();
    let wf = |r: &N| !malformed.contains(&r.id);
    let (mut cases, mut bad) = (0, 0);
    for st in fx.at("states").arr() {
        let offered: Vec<N> = st
            .at("offered")
            .arr()
            .iter()
            .map(|x| x.i() as u32)
            .map(|i| N { id: i, names: names[&i].clone(), signer: 0 })
            .collect();
        let want: Vec<u32> = st.at("held").arr().iter().map(|x| x.i() as u32).collect();
        let mut got: Vec<u32> = kept(&offered, wf).iter().map(|r| r.id).collect();
        got.sort();
        cases += 1;
        bad += (got != want) as usize;
        for order in [offered.clone(), offered.iter().rev().cloned().collect()] {
            let a = arrive(&order, |_| true, None, wf);
            let mut h: Vec<u32> = a.g.rows().iter().map(|r| r.id).collect();
            h.sort();
            cases += 1;
            bad += (h != want) as usize;
        }
    }
    report("TLC's reachable states of Door.tla, replayed through the crate's door", cases, bad);
    assert_eq!(bad, 0);
}
