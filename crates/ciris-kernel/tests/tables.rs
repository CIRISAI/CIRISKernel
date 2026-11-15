//! Differential, for worlds whose conclusion rule belongs to the instance and not to the kernel: the 17
//! witnesses of `witnesses.py` with their variants and adversaries, every world `check_rosters.py`'s
//! unmutated properties conclude, and the attack scenarios concluded under a rule of their own (fixture
//! `tables.json`). The model's rule is recorded as a table, (row, its concluded ancestors) to a verdict. The
//! crate's own layers run over that table, as one set and as rows arrive in three orders, and must reach the
//! same kept set and conclusions without asking a question the table does not hold. Where a world has seat
//! rows, the derived answers (the cut, the holders of every scope over every object, the windows) are
//! compared too, computed from the model's conclusions. The roster worlds use roster.py's settled ones.
//! Also: `line::versions` over every set of `roster_fork`'s worlds (fixture `versions.json`).

mod common;
use ciris_kernel::cut::{Cut, Status};
use ciris_kernel::graph::Graph;
use ciris_kernel::layers::{arrive, conclude, kept, Concluded, Past};
use ciris_kernel::line;
use ciris_kernel::seat::{Obj, Seats};
use ciris_kernel::window::{self, Outcome};
use common::*;
use std::cell::Cell;
use std::collections::{BTreeMap, BTreeSet};

type Table = BTreeMap<(String, Vec<String>), bool>;

fn table_of(j: &J) -> Table {
    j.arr()
        .iter()
        .map(|e| {
            let a = e.arr();
            ((a[0].s().to_string(), a[1].strs()), a[2].b())
        })
        .collect()
}

fn wf(r: &TRow) -> bool {
    !r.f("malformed").is_some_and(|m| matches!(m, J::Bool(true)))
}

fn status_word(s: Status) -> &'static str {
    match s {
        Status::Counts => "counts",
        Status::Contested => "contested",
        Status::Void => "void",
        Status::ConcludesNothing => "concludes nothing",
    }
}

fn orders(rows: &[TRow]) -> Vec<Vec<TRow>> {
    let mut out = vec![rows.to_vec()];
    let mut r = rows.to_vec();
    r.reverse();
    out.push(r);
    if rows.len() > 2 {
        let mut x = rows.to_vec();
        x.rotate_left(1);
        out.push(x);
    }
    out
}

struct Tally {
    cases: usize,
    bad: usize,
}

impl Tally {
    fn cmp(&mut self, ok: bool, what: impl FnOnce() -> String) {
        self.cases += 1;
        if !ok {
            self.bad += 1;
            eprintln!("{}", what());
        }
    }
}

fn layers(w: &J, rows: &[TRow], t: &mut Tally, name: &str) {
    let table = table_of(w.at("table"));
    let miss = Cell::new(0usize);
    let rule = |p: &Past<'_, '_, TRow>| -> bool {
        let mut ps: Vec<String> = p.rows().map(|q| q.id.clone()).collect();
        ps.sort();
        match table.get(&(p.row().id.clone(), ps)) {
            Some(v) => *v,
            None => {
                miss.set(miss.get() + 1);
                false
            }
        }
    };
    let c = conclude(kept(rows, wf), &rule, None);
    let k: Vec<String> = c.g.rows().iter().map(|r| r.id.clone()).collect();
    let want_c: Vec<bool> = w.at("c").arr().iter().map(|x| x.b()).collect();
    t.cmp(k == w.at("kept").strs() && c.all() == &want_c[..], || format!("{name}: kept or concluded"));
    for (o, a) in orders(rows).iter().zip(w.at("arrivals").arr()) {
        let s = arrive(o, &rule, None, wf);
        let held: Vec<String> = s.g.rows().iter().map(|r| r.id.clone()).collect();
        let want: Vec<bool> = a.at("c").arr().iter().map(|x| x.b()).collect();
        t.cmp(held == a.at("held").strs() && s.all() == &want[..], || format!("{name}: an arrival order"));
    }
    t.cmp(miss.get() == 0, || format!("{name}: {} questions the model's rule was never asked", miss.get()));
}

fn derived(
    w: &J,
    rows: &[TRow],
    c_field: &str,
    law: &ciris_kernel::seat::SeatLaw,
    wins: &BTreeMap<String, ciris_kernel::window::WindowSpec<i64>>,
    t: &mut Tally,
    name: &str,
) {
    let k = kept(rows, wf);
    let c: Vec<bool> = w.at(c_field).arr().iter().map(|x| x.b()).collect();
    let cs = Concluded::with(Graph::new(k), Some(c));
    let d = w.at("d");
    let spec = DictCut;
    let cut = Cut::new(&cs, &spec);
    for (i, s) in d.at("cut").arr().iter().enumerate() {
        t.cmp(status_word(cut.status(i)) == s.s(), || format!("{name}: cut status of {}", cs.g.row(i).id));
    }
    let q = Seats::new(&cs, law, &spec, None);
    for (o, by) in d.at("holders").obj() {
        let ob = rows
            .iter()
            .filter_map(|r| r.obj.clone())
            .find(|x| matches!(x, Obj::Row(s) | Obj::Key(s) if s == o))
            .unwrap();
        for (sc, want) in by.obj() {
            let got = sorted_ids(&q.holders(sc, &ob, None));
            t.cmp(got == want.strs(), || {
                format!("{name}: holders of {sc} over {o}: {got:?} against {:?}", want.strs())
            });
        }
    }
    for (pid, want) in d.at("windows").obj() {
        let i = cs.g.idx(pid).unwrap();
        let got = window::outcome(&cs, i, &|x| wins.get(x).cloned(), law, &spec, &|j| cut.counts(j));
        let g = match got {
            Outcome::None => "none".into(),
            Outcome::Open => "open".into(),
            Outcome::Contested => "contested".into(),
            Outcome::Landed(s) => s,
        };
        t.cmp(g == want.s(), || format!("{name}: window {pid}"));
    }
}

fn refs_of(w: &J) -> BTreeMap<String, String> {
    w.at("refs").obj().iter().map(|(k, v)| (k.clone(), v.s().to_string())).collect()
}

#[test]
fn recorded_rule_worlds() {
    let fx = fixture("tables.json");
    let law = law_of(fx.at("law"));
    let wins = windows_of(fx.at("windows"));
    for (group, derive, cf) in [("witnesses", false, "c"), ("other_rules", true, "c"), ("rosters", true, "c_settled")] {
        let mut t = Tally { cases: 0, bad: 0 };
        let ws = fx.at(group).arr();
        for (i, w) in ws.iter().enumerate() {
            let rows = rows_with_refs(w.at("rows").arr(), &refs_of(w));
            let name = format!("{group} {i} {}", w.get("case").map(|c| c.s().to_string()).unwrap_or_default());
            layers(w, &rows, &mut t, &name);
            if derive {
                derived(w, &rows, cf, &law, &wins, &mut t, &name);
            }
        }
        eprintln!("  {group}: {} worlds", ws.len());
        report(&format!("recorded rules: {group}"), t.cases, t.bad);
        assert_eq!(t.bad, 0, "{group}");
    }
}

#[test]
fn roster_versions() {
    let fx = fixture("versions.json");
    let (mut cases, mut bad) = (0, 0);
    for s in fx.arr() {
        let vs = s.at("versions").arr();
        let e: Vec<Vec<usize>> = vs.iter().map(|v| v.at("E").arr().iter().map(|x| x.i() as usize).collect()).collect();
        let past: Vec<BTreeSet<usize>> =
            vs.iter().map(|v| v.at("past").arr().iter().map(|x| x.i() as usize).collect()).collect();
        let valid: Vec<bool> = vs.iter().map(|v| v.at("valid").b()).collect();
        for c in s.at("cases").arr() {
            let a = c.arr();
            let ids: Vec<usize> = a[0].arr().iter().map(|x| x.i() as usize).collect();
            let ack = if a[1].is_null() { None } else { Some(a[1].i() as usize) };
            let want: BTreeSet<usize> = a[2].arr().iter().map(|x| x.i() as usize).collect();
            let got = line::versions(&ids, &|i| e[i].clone(), &|i| past[i].clone(), &|i| valid[i], ack);
            cases += 1;
            if got != want {
                bad += 1;
                eprintln!("{}: {ids:?} ack {ack:?}: {got:?} against {want:?}", s.at("setting").s());
            }
        }
    }
    report("line::versions (roster_fork worlds, every set to three versions, every reader)", cases, bad);
    assert_eq!(bad, 0);
}
