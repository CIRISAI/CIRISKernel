//! Differential: the three layers, the derived answers and the cut, against `models/causal_kernel/check.py`
//! and `check_cut.py` over every world of their pools (fixtures `causal.json`, `cut.json`).

mod common;
use ciris_kernel::cut::{Cut, Holder, Status};
use ciris_kernel::derived;
use ciris_kernel::layers::{arrive, conclude, kept, Concluded, Past};
use ciris_kernel::Row;
use common::*;
use std::collections::BTreeSet;

/// `check.world_rule`: membership of the genesis it descends from, and no removal of its signer in its past.
fn world_rule(p: &Past<'_, '_, TRow>) -> bool {
    let r = p.row();
    let k = r.kind.as_str();
    if k == "genesis" {
        return r.signer == "admin";
    }
    if matches!(k, "edge" | "withdraw" | "free") {
        return true;
    }
    let g: Vec<&TRow> = p.rows().filter(|q| q.kind == "genesis").collect();
    if g.is_empty() || !g[0].f("members").map_or(false, |m| m.str_set().contains(&r.signer)) {
        return false;
    }
    if p.rows().any(|q| q.kind == "removal" && q.fs("removes") == Some(r.signer.as_str())) {
        return false;
    }
    match k {
        "removal" => r.signer == "admin",
        "decider" => p.rows().any(|q| Some(q.id.as_str()) == r.fs("picks")),
        "retract" => p.rows().any(|q| Some(q.id.as_str()) == r.fs("target") && q.signer == r.signer),
        _ => true,
    }
}

fn root(r: &TRow) -> bool {
    r.kind == "genesis" || r.signer == "me"
}

fn removes(r: &TRow) -> Option<String> {
    r.fs("removes").map(String::from)
}

fn ids(c: &Concluded<'_, TRow>, v: impl IntoIterator<Item = usize>) -> Vec<String> {
    sorted_ids(v.into_iter().map(|i| &c.g.row(i).id).collect::<Vec<_>>())
}

fn strs(j: &J) -> Vec<String> {
    let mut v = j.strs();
    v.sort();
    v
}

/// `check.answers`, compared field by field. Returns the number of answers compared and those that differ.
fn causal_answers(c: &Concluded<'_, TRow>, want: &J, members: &BTreeSet<String>, readers: &[String], depth: usize) -> (usize, usize) {
    let (mut n, mut bad) = (0, 0);
    let mut cmp = |ok: bool, what: &str| {
        n += 1;
        if !ok {
            bad += 1;
            eprintln!("  differs: {what}");
        }
    };
    let cl: Vec<usize> = c.cs().iter().copied().filter(|&i| matches!(c.g.row(i).kind.as_str(), "claim" | "decider")).collect();
    for s in ["s", "s2"] {
        let on: Vec<usize> = cl.iter().copied().filter(|&i| c.g.row(i).fs("slot") == Some(s)).collect();
        let (h, k) = derived::slot(c, &on, |r| r.fs("picks").map(String::from), |r| r.id.clone());
        let w = want.at(&format!("slot:{s}")).arr();
        cmp(w[0].opt_s() == h && w[1].i() as usize == k, &format!("slot:{s}"));
    }
    let wins = derived::wins(c, c.cs(), |r| r.fs("target").map(String::from), |r| r.fi("level").unwrap_or(0));
    cmp(ids(c, wins) == strs(want.at("wins")), "wins");
    let counting: Vec<usize> = (0..c.g.len()).filter(|&i| derived::counts(c, i, |r| Some(r.signer.clone()), removes)).collect();
    cmp(ids(c, counting.iter().copied()) == strs(want.at("counts")), "counts");
    let edges = derived::live_edges(c, |r| r.fs("to").map(String::from), |r| r.kind == "withdraw");
    for own in readers {
        let reach = derived::reach(own, depth, &edges);
        cmp(sorted_ids(&reach) == strs(want.at(&format!("reach:{own}"))), "reach");
        let means: Vec<usize> = (0..c.g.len()).filter(|&i| derived::means(c, i, &reach)).collect();
        cmp(ids(c, means) == strs(want.at(&format!("means:{own}"))), "means");
    }
    for &pr in c.cs() {
        if c.g.row(pr).kind != "proposal" {
            continue;
        }
        let t = derived::tally(
            c,
            pr,
            |r| r.kind == "vote",
            |k| members.contains(k),
            |r| r.fs("choice").map(String::from),
            &Some("yes".to_string()),
            |v| derived::counts(c, v, |r| Some(r.signer.clone()), removes),
        );
        cmp(want.at(&format!("tally|{}", c.g.row(pr).id)).i() as usize == t, "tally");
    }
    (n, bad)
}

fn layers_agree(c: &Concluded<'_, TRow>, set: &J) -> bool {
    let kept_ids: Vec<String> = c.g.rows().iter().map(|r| r.id.clone()).collect();
    let want_k: Vec<String> = set.at("kept").strs();
    let want_c: Vec<bool> = set.at("c").arr().iter().map(|x| x.b()).collect();
    kept_ids == want_k && c.all() == &want_c[..]
}

#[test]
fn causal_kernel_worlds() {
    let fx = fixture("causal.json");
    let members = fx.at("members").str_set();
    let readers = fx.at("readers").strs();
    let depth = fx.at("depth").i() as usize;
    let (mut cases, mut bad, mut sets, mut orders_bad) = (0, 0, 0, 0);
    for (name, pool) in fx.at("pools").obj() {
        let rows = rows_of(pool.at("rows").arr());
        for set in pool.at("sets").arr() {
            sets += 1;
            let sel: Vec<TRow> = set.at("idx").arr().iter().map(|i| rows[i.i() as usize].clone()).collect();
            let k: Vec<&TRow> = kept(&sel, |_| true);
            let c = conclude(k, world_rule, Some(&root));
            cases += 1;
            if !layers_agree(&c, set) {
                bad += 1;
                eprintln!("{name} {:?}: kept or concluded differs", set.at("idx"));
            }
            let (n, b) = causal_answers(&c, set.at("a"), &members, &readers, depth);
            cases += n;
            bad += b;
            // the same set in the reverse arrival order, and rotated, as the door runs it
            for shift in [0, 1] {
                let mut order = sel.clone();
                order.reverse();
                if !order.is_empty() {
                    let n = order.len();
                    order.rotate_left(shift % n);
                }
                let a = arrive(&order, world_rule, Some(&root), |_| true);
                let mut held: Vec<(String, bool)> = (0..a.g.len()).map(|i| (a.g.row(i).id.clone(), a.concluded(i))).collect();
                let mut want: Vec<(String, bool)> = (0..c.g.len()).map(|i| (c.g.row(i).id.clone(), c.concluded(i))).collect();
                held.sort();
                want.sort();
                if held != want {
                    orders_bad += 1;
                }
            }
        }
    }
    report("causal (check.py worlds)", cases, bad);
    eprintln!("  {sets} sets; arrival orders that differ from the set function: {orders_bad}");
    assert_eq!(bad, 0);
    assert_eq!(orders_bad, 0);
}

/// `check_cut.rule`: a decider or a landing by a key that may not cut concludes nothing.
fn cut_rule(p: &Past<'_, '_, TRow>) -> bool {
    let r = p.row();
    if matches!(r.kind.as_str(), "decider" | "landing") && !["admin", "co"].contains(&r.signer.as_str()) {
        return false;
    }
    world_rule(p)
}

fn status_word(s: Status) -> &'static str {
    match s {
        Status::Counts => "counts",
        Status::Contested => "contested",
        Status::Void => "void",
        Status::ConcludesNothing => "concludes nothing",
    }
}

#[test]
fn cut_worlds() {
    let fx = fixture("cut.json");
    let members = fx.at("members").str_set();
    let (mut cases, mut bad) = (0, 0);
    for (name, pool) in fx.at("pools").obj() {
        let rows = rows_of(pool.at("rows").arr());
        for set in pool.at("sets").arr() {
            let sel: Vec<TRow> = set.at("idx").arr().iter().map(|i| rows[i.i() as usize].clone()).collect();
            let c = conclude(kept(&sel, |_| true), cut_rule, Some(&root));
            let a = set.at("a");
            let mut cmp = |ok: bool, what: &str| {
                cases += 1;
                if !ok {
                    bad += 1;
                    eprintln!("{name} {:?}: {what} differs", set.at("idx"));
                }
            };
            cmp(layers_agree(&c, set), "kept/concluded");
            let spec = DictCut;
            let cut = Cut::new(&c, &spec);
            for i in 0..c.g.len() {
                let w = a.at("status").at(&c.g.row(i).id).s();
                cmp(status_word(cut.status(i)) == w, "status");
            }
            for s in ["s", "s2"] {
                let slot = J::Str(s.into());
                let h = cut.holder(
                    |r| {
                        r.f("slot") == Some(&slot)
                            || r.f("on").map_or(false, |o| o.arr().contains(&slot))
                            || spec_cuts(r).contains(&slot)
                    },
                    |r| r.fs("picks").map(String::from),
                    |r| r.fs("says").map(String::from).unwrap_or_else(|| r.id.clone()),
                );
                let got = match h {
                    Holder::Held(v) => v,
                    Holder::Empty => "empty".into(),
                    Holder::Conflict => "conflict".into(),
                };
                cmp(a.at(&format!("slot:{s}")).s() == got, "holder");
            }
            for &l in c.cs() {
                let lr = c.g.row(l);
                if lr.kind != "landing" || !cut.counts(l) {
                    continue;
                }
                let voices: BTreeSet<&String> = lr
                    .names()
                    .iter()
                    .filter_map(|n| c.g.idx(n))
                    .map(|q| c.g.row(q))
                    .filter(|q| q.kind == "vote")
                    .map(|q| &q.signer)
                    .collect();
                cmp(a.at("landed").at(&lr.id).i() as usize == voices.len(), "landed");
            }
            for &pr in c.cs() {
                if c.g.row(pr).kind != "proposal" {
                    continue;
                }
                let t = derived::tally(
                    &c,
                    pr,
                    |r| r.kind == "vote",
                    |k| members.contains(k),
                    |r| r.fs("choice").map(String::from),
                    &Some("yes".to_string()),
                    |v| cut.counts(v),
                );
                cmp(a.at(&format!("tally|{}", c.g.row(pr).id)).i() as usize == t, "tally");
            }
        }
    }
    report("cut (check_cut.py worlds)", cases, bad);
    assert_eq!(bad, 0);
}

fn spec_cuts(r: &TRow) -> BTreeSet<J> {
    use ciris_kernel::cut::CutSpec;
    DictCut.cuts_of(r)
}
