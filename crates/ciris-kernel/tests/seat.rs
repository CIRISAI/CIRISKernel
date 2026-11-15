//! Differential: the seat, the reader's line, tips, members at a head and the window, against every scenario
//! `models/causal_kernel/attacks.py` concludes under the seat, window and route rules, and the window
//! adversary table of `window.py` (fixture `seat.json`).

mod common;
use ciris_kernel::cut::{Cut, Status};
use ciris_kernel::layers::{conclude, kept, Concluded, Past};
use ciris_kernel::seat::{self, members_at, seat_rule, Obj, Over, Policy, Root, SeatLaw, Seats};
use ciris_kernel::window::{self, Base, Clause, How, Outcome, WindowSpec};
use common::*;
use std::collections::{BTreeMap, BTreeSet};

fn law_of(j: &J) -> SeatLaw {
    let mut law = SeatLaw {
        duties: j.at("duties").strs(),
        final_scopes: j.at("final").strs(),
        roster_seats: j.at("roster_seats").strs(),
        depth: j.at("depth").i() as usize,
        ..Default::default()
    };
    for (k, v) in j.at("holds").obj() {
        law.holds.insert(k.clone(), v.strs());
    }
    for (k, v) in j.at("ends").obj() {
        law.ends.insert(k.clone(), v.strs());
    }
    for (k, v) in j.at("confers").obj() {
        let a = v.arr();
        let over = if a[1].s() == "same" { Over::Same } else { Over::Holder };
        law.confers.insert(k.clone(), (a[0].strs(), over));
    }
    for (k, v) in j.at("policy").obj() {
        let a = v.arr();
        let (num, den) = (a[1].i() as u64, a[2].i() as u64);
        let p = match a[0].s() {
            "atleast" => Policy::AtLeast(num, den),
            "strict" => Policy::Strict(num, den),
            "one" => Policy::One,
            "declared" => Policy::Declared,
            "ranked" => Policy::Ranked,
            "duty" if k == "duty_confer" => Policy::DutyConfer,
            "duty" if k == "duty_withdraw" => Policy::DutyWithdraw,
            _ => Policy::NotACount,
        };
        law.policy.insert(k.clone(), p);
    }
    law
}

fn windows_of(j: &J) -> BTreeMap<String, WindowSpec<i64>> {
    let clauses = |a: &J| -> Vec<Clause> {
        a.arr()
            .iter()
            .map(|c| {
                let c = c.arr();
                Clause {
                    value: c[0].s().into(),
                    how: if c[1].s() == "one" { How::One } else { How::Strict },
                    over: match c[2].s() {
                        "all" => Base::All,
                        "others" => Base::Others,
                        s => Base::Scope(s.into()),
                    },
                    out: c[3].s().into(),
                }
            })
            .collect()
    };
    j.obj()
        .iter()
        .map(|(k, w)| {
            (
                k.clone(),
                WindowSpec {
                    counted: w.at("counted").s().into(),
                    concluder: w.at("concluder").s().into(),
                    opener_says: w.at("opener_says").opt_s(),
                    at_once: clauses(w.at("at_once")),
                    silent: w.at("silent").opt_s(),
                    at_close: clauses(w.at("at_close")),
                    default: w.at("default").s().into(),
                    target_votes: w.get("target_votes").map_or(false, |x| x.b()),
                    secs: w.at("secs").i(),
                },
            )
        })
        .collect()
}

struct World {
    law: SeatLaw,
    windows: BTreeMap<String, WindowSpec<i64>>,
}

impl World {
    fn rule(&self, name: &str, p: &Past<'_, '_, TRow>) -> bool {
        let r = p.row();
        let spec = DictCut;
        match name {
            "window" => {
                if let Some(v) = window::rule(p, &|w| self.windows.get(w).cloned(), &self.law, &spec) {
                    return v;
                }
                seat_rule(p, &self.law, &spec, &|_| true)
            }
            "route" => {
                if matches!(r.kind.as_str(), "msg" | "ack") {
                    if r.kind == "ack" && !p.rows().any(|q| Some(&q.id) == r.of.as_ref() && q.kind == "msg") {
                        return false;
                    }
                    let Some(room) = r.room.clone() else { return false };
                    return members_at(p, &self.law, &spec, &room, &r.head, "member").contains(&r.signer);
                }
                seat_rule(p, &self.law, &spec, &|_| true)
            }
            _ => seat_rule(p, &self.law, &spec, &|_| true),
        }
    }
}

fn obj_s(o: &Obj<String, String>) -> J {
    match o {
        Obj::Row(s) | Obj::Key(s) => J::Str(s.clone()),
    }
}

fn status_word(s: Status) -> &'static str {
    match s {
        Status::Counts => "counts",
        Status::Contested => "contested",
        Status::Void => "void",
        Status::ConcludesNothing => "concludes nothing",
    }
}

fn outcome_word(o: &Outcome) -> String {
    match o {
        Outcome::None => "none".into(),
        Outcome::Open => "open".into(),
        Outcome::Contested => "contested".into(),
        Outcome::Landed(s) => s.clone(),
    }
}

fn obj_named(c: &Concluded<'_, TRow>, s: &str) -> Obj<String, String> {
    if c.g.idx(&s.to_string()).is_some() {
        Obj::Row(s.into())
    } else {
        Obj::Key(s.into())
    }
}

#[test]
fn seat_scenarios() {
    let fx = fixture("seat.json");
    let w = World { law: law_of(fx.at("law")), windows: windows_of(fx.at("windows")) };
    assert!(fx.at("problems").arr().is_empty());
    let (mut cases, mut bad) = (0, 0);
    let mut by_rule: BTreeMap<String, (usize, usize)> = BTreeMap::new();
    for (si, sc) in fx.at("scenarios").arr().iter().enumerate() {
        let name = sc.at("rule").s().to_string();
        let rows = rows_of(sc.at("rows").arr());
        let a = sc.at("a");
        let c = conclude(kept(&rows, |_| true), |p| w.rule(&name, p), None);
        let mut cmp = |ok: bool, what: String| {
            cases += 1;
            let e = by_rule.entry(name.clone()).or_default();
            e.0 += 1;
            if !ok {
                bad += 1;
                e.1 += 1;
                eprintln!("scenario {si} ({name}): {what}");
            }
        };
        let kept_ids: Vec<String> = c.g.rows().iter().map(|r| r.id.clone()).collect();
        cmp(kept_ids == a.at("kept").strs(), "kept".into());
        let want_c: Vec<bool> = a.at("c").arr().iter().map(|x| x.b()).collect();
        for i in 0..c.g.len() {
            cmp(c.concluded(i) == want_c[i], format!("concluded {}", c.g.row(i).id));
        }
        let spec = DictCut;
        let cut = Cut::new(&c, &spec);
        for (i, ws) in a.at("cut").arr().iter().enumerate() {
            cmp(status_word(cut.status(i)) == ws.s(), format!("cut status {}", c.g.row(i).id));
        }
        for (reader, rd) in a.at("readers").obj() {
            let own = if reader == "-" { None } else { Some(reader.clone()) };
            let q = Seats::new(&c, &w.law, &spec, own.as_ref());
            let got: BTreeSet<J> = q
                .recs
                .iter()
                .map(|r| {
                    J::Arr(vec![
                        J::Str(r.offer.clone()),
                        J::Str(r.k.clone()),
                        J::Str(r.scope.clone()),
                        obj_s(&r.obj),
                        J::Int(r.depth as i64),
                        match &r.root {
                            Root::Key(k) => J::Str(k.clone()),
                            Root::Group(o) => J::Arr(vec![J::Str("group".into()), obj_s(o)]),
                        },
                    ])
                })
                .collect();
            let want: BTreeSet<J> = rd.at("recs").arr().iter().cloned().collect();
            cmp(got == want, format!("live seats for reader {reader}"));
            let stale = sorted_ids(q.stale.iter().map(|&i| &c.g.row(i).id));
            cmp(stale == rd.at("stale").strs(), format!("stale for reader {reader}"));
            for (o, h) in rd.at("holders").obj() {
                let ob = obj_named(&c, o);
                cmp(sorted_ids(&q.holders("member", &ob, None)) == h.strs(), format!("members of {o} for {reader}"));
                cmp(
                    sorted_ids(&q.holders("duty", &ob, None)) == rd.at("duty").at(o).strs(),
                    format!("duty holders of {o} for {reader}"),
                );
                let tips = sorted_ids(q.tips(&ob).iter().map(|&i| &c.g.row(i).id));
                cmp(tips == rd.at("tips").at(o).strs(), format!("tips of {o} for {reader}"));
            }
        }
        for (pid, want) in a.at("windows").obj() {
            let i = c.g.idx(pid).unwrap();
            let got = window::outcome(&c, i, &|x| w.windows.get(x).cloned(), &w.law, &spec, &|j| cut.counts(j));
            cmp(outcome_word(&got) == want.s(), format!("window {pid}"));
        }
    }
    for (k, (n, b)) in &by_rule {
        eprintln!("  rule {k}: {n} answers, {b} differ");
    }
    eprintln!("  scenarios: {}; concluded under rules the fixture does not carry: {}", fx.at("scenarios").arr().len(), fx.at("skipped_other_rules").i());
    report("seat, line, tips, window (attacks.py and window.py scenarios)", cases, bad);
    assert_eq!(bad, 0);
}

#[test]
fn covers_and_met() {
    assert!(seat::covers("infra", "infra:attest"));
    assert!(!seat::covers("infra", "infrastructure"));
    assert!(seat::met(Some(Policy::Strict(1, 2)), 2, 3, None));
    assert!(!seat::met(Some(Policy::Strict(1, 2)), 1, 2, None));
    assert!(seat::met(Some(Policy::AtLeast(2, 3)), 2, 3, None));
    assert!(!seat::met(Some(Policy::AtLeast(2, 3)), 0, 0, None));
}
