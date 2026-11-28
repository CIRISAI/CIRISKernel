//! Differential: the seat, the reader's line, tips, members at a head and the window, against every scenario
//! `models/causal_kernel/attacks.py` concludes under the seat, window and route rules, and the window
//! adversary table of `window.py` (fixture `seat.json`).

mod common;
use ciris_kernel::cut::{Cut, Status};
use ciris_kernel::layers::{conclude, kept, Past};
use ciris_kernel::seat::{self, election_closed, members_at, seat_rule, Obj, Policy, Root, SeatLaw, Seats};
use ciris_kernel::window::{self, Outcome, WindowSpec};
use common::*;
use std::collections::{BTreeMap, BTreeSet};

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
                let why = window::rule_why(p, &|w| self.windows.get(w).cloned(), &self.law, &spec);
                if let Some(v) = window::rule(p, &|w| self.windows.get(w).cloned(), &self.law, &spec) {
                    // no window row of the fixtures reads past its concluded ancestors: none waits
                    assert_eq!(why, Some(Ok(v)), "window::rule_why disagrees with window::rule");
                    return v;
                }
                assert_eq!(why, None);
                let v = seat_rule(p, &self.law, &spec, &|_| true);
                assert_eq!(ciris_kernel::seat::seat_rule_why(p, &self.law, &spec, &|_| true), Ok(v));
                v
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

/// The object the model names `s`, as the rows' own references typed it.
fn obj_named(rows: &[TRow], s: &str) -> Obj<String, String> {
    rows.iter()
        .filter_map(|r| r.obj.clone())
        .find(|o| matches!(o, Obj::Row(x) | Obj::Key(x) if x == s))
        .expect("an object some row names")
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
        let refs: BTreeMap<String, String> =
            sc.at("refs").obj().iter().map(|(k, v)| (k.clone(), v.s().to_string())).collect();
        let rows = rows_with_refs(sc.at("rows").arr(), &refs);
        let a = sc.at("a");
        // a scenario read under another table of what a seat holds carries it (`holds`)
        let own_law = sc.get("holds").map(|h| World {
            law: SeatLaw { holds: h.obj().iter().map(|(k, v)| (k.clone(), v.strs())).collect(), ..w.law.clone() },
            windows: w.windows.clone(),
        });
        let w = own_law.as_ref().unwrap_or(&w);
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
        for (i, w) in want_c.iter().enumerate() {
            cmp(c.concluded(i) == *w, format!("concluded {}", c.g.row(i).id));
        }
        let spec = DictCut;
        let cut = Cut::new(&c, &spec);
        for (i, ws) in a.at("cut").arr().iter().enumerate() {
            cmp(status_word(cut.status(i)) == ws.s(), format!("cut status {}", c.g.row(i).id));
        }
        for (reader, rd) in a.at("readers").obj() {
            let own = if reader == "-" { None } else { Some(reader.clone()) };
            // a reader's roster is read over the rows as they conclude for it (the ruling of 2026-11-27); a reader with
            // no row holds the rows too (the concurrent founders' amendments it holds, C2)
            let (rc, rv) = ciris_kernel::seat::for_reader(&c, &w.law, &spec, own.as_ref());
            let q = match &own {
                Some(k) => Seats::for_reader(&rc, &w.law, &spec, k, &rv),
                None => Seats::new(&rc, &w.law, &spec, None),
            };
            let got: BTreeSet<J> = q
                .recs()
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
            let stale = sorted_ids(q.stale().iter().map(|&i| &c.g.row(i).id));
            cmp(stale == rd.at("stale").strs(), format!("stale for reader {reader}"));
            for (o, h) in rd.at("holders").obj() {
                let ob = obj_named(&rows, o);
                cmp(sorted_ids(&q.holders("member", &ob, None)) == h.strs(), format!("members of {o} for {reader}"));
                cmp(
                    sorted_ids(&q.holders("duty", &ob, None)) == rd.at("duty").at(o).strs(),
                    format!("duty holders of {o} for {reader}"),
                );
                // the whole roster: members and agents (CC 4.5.13)
                cmp(sorted_ids(&q.roster(&ob)) == rd.at("roster").at(o).strs(), format!("roster of {o} for {reader}"));
                let tips = sorted_ids(q.tips(&ob).iter().map(|&i| &c.g.row(i).id));
                cmp(tips == rd.at("tips").at(o).strs(), format!("tips of {o} for {reader}"));
            }
        }
        // the standing a scenario asks for by name (check_duty_seats.py's cases)
        if let Some(asks) = sc.get("stands") {
            let (rc, _) = ciris_kernel::seat::for_reader(&c, &w.law, &spec, None);
            let q = Seats::new(&rc, &w.law, &spec, None);
            for ask in asks.arr() {
                let (k, s, o, want) = (ask.arr()[0].s(), ask.arr()[1].s(), ask.arr()[2].s(), ask.arr()[3].b());
                let got = q.stands(&k.to_string(), s, &obj_named(&rows, o), None);
                cmp(got == want, format!("{k} stands in {s} over {o}"));
            }
        }
        // an election's close, asked by name (check_election.py's CLOSE_CASES)
        if let Some(cl) = sc.get("closed") {
            let (s, want) = (cl.arr()[0].s().to_string(), cl.arr()[1].b());
            cmp(election_closed(&c, &w.law, &spec, &s) == want, format!("election closed by {s}"));
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
    eprintln!(
        "  scenarios: {}; concluded under rules the fixture does not carry: {}",
        fx.at("scenarios").arr().len(),
        fx.at("skipped_other_rules").i()
    );
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

#[test]
fn a_reference_is_typed_by_its_form() {
    use ciris_kernel::seat::Reference;
    let d = [7u8; 32];
    let row = |b: &[u8]| b.len();
    let key = |t: &str| t.len();
    let ok_key = "urn:ietf:params:oauth:ckt:sha-256:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA";
    assert_eq!(Obj::from_reference(Reference::Digest { alg: -16, digest: &d }, row, key), Some(Obj::Row(32)));
    assert_eq!(Obj::from_reference(Reference::Text(ok_key), row, key), Some(Obj::Key(ok_key.len())));
    assert_eq!(Obj::<usize, usize>::from_reference(Reference::Digest { alg: -44, digest: &d }, row, key), None);
    assert_eq!(Obj::<usize, usize>::from_reference(Reference::Digest { alg: -16, digest: &d[..31] }, row, key), None);
    assert_eq!(Obj::<usize, usize>::from_reference(Reference::Text("g"), row, key), None);
    assert_eq!(Obj::<usize, usize>::from_reference(Reference::Text(&ok_key[..ok_key.len() - 1]), row, key), None);
    assert_eq!(Obj::<usize, usize>::from_reference(Reference::Text(&ok_key.replace('A', "+")), row, key), None);
}

/// A moderator's chain of lone removals, each naming the one before as its head (fixture `chain`, 32 of them):
/// concluded and read in polynomial time. Before the members at a head were kept for the builds below a build,
/// each removal re-read every earlier one, about six times the work per row.
#[test]
fn a_chain_of_lone_removals_is_read_in_time() {
    let fx = fixture("seat.json");
    let w = World { law: law_of(fx.at("law")), windows: windows_of(fx.at("windows")) };
    let ch = fx.at("chain");
    let refs: BTreeMap<String, String> =
        ch.at("refs").obj().iter().map(|(k, v)| (k.clone(), v.s().to_string())).collect();
    let rows = rows_with_refs(ch.at("rows").arr(), &refs);
    let t = std::time::Instant::now();
    let c = conclude(kept(&rows, |_| true), |p| w.rule("window", p), None);
    let want: Vec<bool> = ch.at("c").arr().iter().map(|x| x.b()).collect();
    assert_eq!((0..c.g.len()).map(|i| c.concluded(i)).collect::<Vec<_>>(), want);
    let q = Seats::new(&c, &w.law, &DictCut, None);
    assert_eq!(sorted_ids(&q.roster(&obj_named(&rows, "g"))), ch.at("roster").strs());
    let secs = t.elapsed().as_secs_f64();
    eprintln!("  a chain of {} lone removals: {secs:.2} s", ch.at("n").i());
    assert!(secs < 20.0, "{secs:.1} s for the chain");
}
