//! Differential: a window's table from its policy row (`window::spec_from_policy`), against `window.py`'s
//! `spec_from_policy` over every row of the governance policy table and every plant of `check_policy_spec.py`
//! (fixture `policy_spec.json`). The row is decoded here from the table's own JSON, unchanged, as a caller would.

mod common;
use ciris_kernel::window::{
    spec_from_policy, Active, Cell, Comparison, CountedCells, PolicyRefusal, PolicyRow, PolicyTable, RuleCell, Stated,
    Why, WindowSpec, Words,
};
use common::*;
use std::collections::BTreeMap;

fn opt_u(j: Option<&J>) -> Option<u64> {
    j.filter(|x| !x.is_null()).map(|x| x.i() as u64)
}

fn rule(j: &J) -> RuleCell {
    RuleCell {
        kind: j.at("kind").s().into(),
        num: opt_u(j.get("num")),
        den: opt_u(j.get("den")),
        count: opt_u(j.get("count")),
        roles: j.get("roles").map(|x| x.strs()).unwrap_or_default(),
        choices: opt_u(j.get("choices")),
    }
}

fn cell(j: &J) -> Cell {
    Cell { value: j.at("value").s().into(), cc_ref: j.get("cc_ref").and_then(|x| x.opt_s()) }
}

fn stated(j: &J) -> Stated {
    match j {
        J::Null => Stated::Null,
        J::Str(s) => Stated::Text(s.clone()),
        J::Obj(_) => Stated::Fraction(j.at("num").i() as u64, j.at("den").i() as u64),
        x => panic!("a prose cell {x:?}"),
    }
}

fn words(j: &J) -> Words {
    match j {
        J::Arr(_) => Words::Listed(j.strs()),
        J::Str(s) => Words::Word(s.clone()),
        x => panic!("a words cell {x:?}"),
    }
}

/// The row, every field of the table's JSON.
fn row_of(j: &J) -> PolicyRow {
    let c = j.at("counted");
    PolicyRow {
        family: j.at("family").s().into(),
        cc_ref: j.at("cc_ref").s().into(),
        kind: j.at("kind").s().into(),
        standing_set: j.at("standing_set").s().into(),
        base: j.at("base").s().into(),
        enact: stated(j.at("enact")),
        cancel: stated(j.at("cancel")),
        floor: stated(j.at("floor")),
        enact_rule: rule(j.at("enact_rule")),
        cancel_rule: rule(j.at("cancel_rule")),
        floor_rule: rule(j.at("floor_rule")),
        counted: CountedCells {
            count_set: cell(c.at("count_set")),
            voice: cell(c.at("voice")),
            counted_at: cell(c.at("counted_at")),
            voices: cell(c.at("voices")),
            target_silent: cell(c.at("target_silent")),
            changes_set: cell(c.at("changes_set")),
            target_voice: cell(c.at("target_voice")),
        },
        cancel_over: j.at("cancel_over").s().into(),
        at_window: j.at("at_window").s().into(),
        concluder: j.at("concluder").s().into(),
        opener: j.at("opener").s().into(),
        opener_says: j.at("opener_says").s().into(),
        outcome_words: words(j.at("outcome_words")),
        answer_words: words(j.at("answer_words")),
        default_at_close: j.at("default_at_close").s().into(),
        landed_means: j.at("landed_means").s().into(),
        refused_means: j.at("refused_means").s().into(),
        comparison: Comparison {
            enact: j.at("comparison").at("enact").s().into(),
            cancel: j.at("comparison").at("cancel").s().into(),
            floor: j.at("comparison").at("floor").s().into(),
        },
        stated_census: opt_u(j.get("stated_census")),
        window_secs: j.at("window_secs").i() as u64,
        window_class: j.at("window_class").s().into(),
        irreversible: j.at("irreversible").b(),
        reverse_path: j.at("reverse_path").b(),
        corridor: j.at("corridor").s().into(),
        model: j.at("model").strs(),
        status: j.at("status").s().into(),
        note: j.at("note").s().into(),
    }
}

fn table_of(j: &J) -> PolicyTable {
    let m = |k: &str| j.at(k).obj().iter().map(|(a, b)| (a.clone(), b.i() as u64)).collect::<BTreeMap<_, _>>();
    PolicyTable { min_count: m("min_count"), window_classes: m("window_classes") }
}

fn active_of(j: &J) -> Option<Active> {
    match j {
        J::Null => None,
        J::Str(s) if s == "within_k" => Some(Active::WithinK),
        J::Arr(a) if a[0].s() == "census" => Some(Active::Census(a[1].i() as u64)),
        x => panic!("active {x:?}"),
    }
}

/// A refusal as the model writes it: [cell, why, other].
fn refusal_word(r: &PolicyRefusal) -> (String, String, Option<String>) {
    let (w, o) = match r.why {
        Why::Unstated => ("unstated", None),
        Why::Unknown => ("unknown", None),
        Why::Disagrees(o) => ("disagrees", Some(o)),
        Why::NoWindow => ("no_window", None),
        Why::NotAWindow => ("not_a_window", None),
        Why::Local => ("local", None),
        Why::NoCell(o) => ("no_cell", Some(o)),
        Why::Caller(o) => ("caller", Some(o)),
    };
    (r.cell.into(), w.into(), o.map(String::from))
}

#[test]
fn policy_rows_give_the_models_tables() {
    let fx = fixture("policy_spec.json");
    let (mut cases, mut bad, mut specs) = (0usize, 0usize, 0usize);
    for c in fx.at("cases").arr() {
        let name = c.at("name").s();
        let got: Result<WindowSpec<i64>, Vec<PolicyRefusal>> = spec_from_policy(
            &row_of(c.at("row")),
            &table_of(c.at("table")),
            active_of(c.at("active")),
            c.at("seat").opt_s().as_deref(),
        );
        cases += 1;
        let ok = match (&got, c.at("spec")) {
            (Ok(s), J::Obj(_)) => {
                specs += 1;
                let mut m = BTreeMap::new();
                m.insert("w".to_string(), c.at("spec").clone());
                let want = windows_of(&J::Obj(m)).remove("w").unwrap();
                *s == want
            }
            (Err(rs), J::Null) => {
                let want: Vec<(String, String, Option<String>)> = c
                    .at("refusals")
                    .arr()
                    .iter()
                    .map(|r| {
                        let r = r.arr();
                        (r[0].s().into(), r[1].s().into(), r[2].opt_s())
                    })
                    .collect();
                // the order as returned: both languages sort by (cell, why's word, the cell it names)
                rs.iter().map(refusal_word).collect::<Vec<_>>() == want
            }
            _ => false,
        };
        if !ok {
            bad += 1;
            eprintln!("{name}: crate {got:?}");
        }
    }
    report("policy_spec", cases, bad);
    assert!(cases > 90 && specs > 30, "{cases} cases, {specs} tables");
    assert_eq!(bad, 0, "{bad} of {cases} differ");
}

/// A secs the caller's instant type cannot hold is refused, never truncated.
#[test]
fn a_length_the_instant_cannot_hold_is_refused() {
    let fx = fixture("policy_spec.json");
    let c = fx.at("cases").arr().iter().find(|c| c.at("name").s() == "default_content, its opener as member").unwrap();
    let mut row = row_of(c.at("row"));
    let mut table = table_of(c.at("table"));
    row.window_secs = 1 << 40;
    table.window_classes.insert(row.window_class.clone(), 1 << 40);
    let got: Result<WindowSpec<u32>, _> = spec_from_policy(&row, &table, Some(Active::WithinK), None);
    assert_eq!(got.unwrap_err(), vec![PolicyRefusal { cell: "window_secs", why: Why::Unknown }]);
    assert!(spec_from_policy::<u64>(&row, &table, Some(Active::WithinK), None).is_ok());
}

// ---- the seat law's table cells (`tables::law_from_tables`, fixture `law_tables.json`) ------------------------------
use ciris_kernel::seat::{Act, ActRule, Choice, CommunityKind, Policy, ScopeClass};
use ciris_kernel::tables::{held_shut, law_from_tables, ActsRow, LawRefusal, LawWhy, ProtocolRow};

fn policy_word(name: &str, a: &[J]) -> Policy {
    let n = |i: usize| a[i].i() as u64;
    match a[0].s() {
        "atleast" => Policy::AtLeast(n(1), n(2)),
        "strict" => Policy::Strict(n(1), n(2)),
        "recall" => Policy::Recall(n(1), n(2), n(3)),
        "one" => Policy::One,
        "declared" => Policy::Declared,
        "protocol" => Policy::Protocol,
        "ranked" => Policy::Ranked,
        "duty" if name == "duty_confer" => Policy::DutyConfer,
        "duty" if name == "duty_withdraw" => Policy::DutyWithdraw,
        "lift" => Policy::Lift,
        "unanimous" => Policy::Unanimous,
        "weighted" => Policy::Weighted,
        "not_a_count" => Policy::NotACount,
        x => panic!("a policy {x}"),
    }
}

fn law_why(w: LawWhy) -> &'static str {
    match w {
        LawWhy::Unknown => "unknown",
        LawWhy::Duplicate => "duplicate",
        LawWhy::NoRow => "no_row",
        LawWhy::Disagrees => "disagrees",
        LawWhy::Unstated => "unstated",
    }
}

#[test]
fn the_tables_give_the_models_seat_law() {
    let fx = fixture("law_tables.json");
    let (mut cases, mut bad) = (0usize, 0usize);
    for c in fx.at("cases").arr() {
        let acts: Vec<ActsRow> = c
            .at("acts")
            .arr()
            .iter()
            .map(|a| ActsRow {
                act: a.at("act").s().into(),
                scope: a.at("scope").s().into(),
                community_kind: a.at("community_kind").s().into(),
                policy: a.at("policy").s().into(),
                choice: a.at("choice").s().into(),
                cc_ref: a.at("cc_ref").s().into(),
            })
            .collect();
        let fams: Vec<PolicyRow> = c.at("families").arr().iter().map(row_of).collect();
        let protos: Vec<ProtocolRow> = c
            .at("protocols")
            .arr()
            .iter()
            .map(|p| ProtocolRow { kind: p.at("kind").s().into(), rule: p.at("rule").s().into() })
            .collect();
        let got = law_from_tables(&acts, &fams, &protos);
        cases += 1;
        let ok = match (&got, c.at("law")) {
            (Ok(l), J::Obj(_)) => {
                let w = c.at("law");
                let pol: BTreeMap<String, Policy> =
                    w.at("policy").obj().iter().map(|(k, v)| (k.clone(), policy_word(k, v.arr()))).collect();
                let rules: Vec<ActRule> = w
                    .at("acts")
                    .arr()
                    .iter()
                    .map(|r| {
                        let r = r.arr();
                        ActRule {
                            act: Act::from_word(r[0].s()).unwrap(),
                            scope: ScopeClass::from_word(r[1].s()).unwrap(),
                            kind: CommunityKind::from_word(r[2].s()).unwrap(),
                            policies: r[3].strs(),
                            choice: Choice::from_word(r[4].s()).unwrap(),
                        }
                    })
                    .collect();
                l.policy == pol
                    && l.acts.as_ref() == Some(&rules)
                    && l.removal_floor == w.at("removal_floor").i() as usize
            }
            (Err(rs), J::Null) => {
                let want: Vec<(String, String, String, String)> = c
                    .at("refusals")
                    .arr()
                    .iter()
                    .map(|r| {
                        let r = r.arr();
                        (r[0].s().into(), r[1].s().into(), r[2].s().into(), r[3].s().into())
                    })
                    .collect();
                let mine: Vec<(String, String, String, String)> = rs
                    .iter()
                    .map(|r: &LawRefusal| (r.table.into(), r.row.clone(), r.cell.into(), law_why(r.why).into()))
                    .collect();
                mine == want
            }
            _ => false,
        };
        if !ok {
            bad += 1;
            eprintln!("{}: crate {:?}", c.at("name").s(), got.as_ref().map(|l| (&l.policy, l.removal_floor)));
        }
    }
    report("law_tables", cases, bad);
    assert!(cases > 20, "{cases} cases");
    assert_eq!(bad, 0, "{bad} of {cases} differ");
}

/// A row's table in the reference's words: answers assent and raised as approve and object; the overturn's leaves as
/// its reading words (check_policy_spec.py, WORDS and READING).
fn in_words(mut d: WindowSpec<i64>, fam: &str) -> WindowSpec<i64> {
    let v = |w: &str| -> String {
        match w {
            "assent" => "approve".into(),
            "raised" => "object".into(),
            w => w.into(),
        }
    };
    let o = |w: &str| -> String {
        match (fam, w) {
            ("moderation_overturn", "landed") => "lifted".into(),
            ("moderation_overturn", "refused") => "stands".into(),
            (_, w) => w.into(),
        }
    };
    for cl in d.at_once.iter_mut().chain(d.at_close.iter_mut()) {
        cl.value = v(&cl.value);
        cl.out = o(&cl.out);
        if let ciris_kernel::window::How::MoreOfVoted(_, _, _, against) = &mut cl.how {
            *against = v(against);
        }
    }
    d.opener_says = d.opener_says.map(|w| v(&w));
    d.silent = d.silent.map(|w| o(&w));
    d.default = o(&d.default);
    d
}

// ---- the act binding (`window::rule_bound`, `window::outcome_bound`, fixture `window_bound.json`) -------------------
#[test]
fn bound_openers_take_the_models_tables() {
    use ciris_kernel::layers::{conclude, kept};
    use ciris_kernel::seat::seat_rule;
    use ciris_kernel::window::{outcome_bound, rule_bound, rule_bound_why, Outcome, WindowRow};
    let fx = fixture("window_bound.json");
    let law = law_of(fx.at("law"));
    let table = table_of(fx.at("table"));
    let rows: BTreeMap<String, PolicyRow> =
        fx.at("families").arr().iter().map(|f| (f.at("family").s().to_string(), row_of(f))).collect();
    // the row's table in the reference's words, as check_policy_spec.families gives it (its WORDS and READING)
    let families = |fam: &str, _obj: &ciris_kernel::seat::Obj<String, String>, seat: Option<&str>| {
        let row = rows.get(fam)?;
        let active = (row.base == "active" && row.stated_census.is_none()).then_some(Active::WithinK);
        let several = row.counted.count_set.value.split('-').next().unwrap_or("").contains('+');
        let d: WindowSpec<i64> = spec_from_policy(row, &table, active, seat.filter(|_| several)).ok()?;
        Some(in_words(d, fam))
    };
    let none = |_: &String| -> Option<WindowSpec<i64>> { None };
    let spec = DictCut;
    let (mut cases, mut bad) = (0usize, 0usize);
    let why_ok = std::cell::Cell::new(0usize);
    for c in fx.at("cases").arr() {
        let refs: BTreeMap<String, String> =
            c.at("refs").obj().iter().map(|(k, v)| (k.clone(), v.s().to_string())).collect();
        let rs = rows_with_refs(c.at("rows").arr(), &refs);
        let got = conclude(
            kept(&rs, |_| true),
            |p| {
                // rule_bound_why tells a wait from concluding nothing; read as rule_bound, it is rule_bound
                let why = rule_bound_why(p, &families, &none, &law, &spec);
                let plain = rule_bound(p, &families, &none, &law, &spec);
                assert_eq!(
                    why.as_ref().map(|r| *r.as_ref().unwrap_or(&false)),
                    plain,
                    "rule_bound_why and rule_bound differ"
                );
                assert_eq!(why.is_some(), p.row().win_kind().is_some(), "rule_bound_why answers a window row only");
                why_ok.set(why_ok.get() + why.is_some_and(|r| r.is_ok()) as usize);
                match plain {
                    Some(v) => v,
                    None => seat_rule(p, &law, &spec, &|_| true),
                }
            },
            None,
        );
        let ids: Vec<String> = got.g.rows().iter().map(|r| r.id.clone()).collect();
        let cs: Vec<bool> = (0..ids.len()).map(|i| got.concluded(i)).collect();
        let want_c: Vec<bool> = c.at("c").arr().iter().map(|x| x.b()).collect();
        let o = match got.g.idx(&"p".to_string()) {
            Some(pi) => match outcome_bound(&got, pi, &families, &none, &law, &spec, &|_| true) {
                Outcome::None => "none".to_string(),
                Outcome::Open => "open".into(),
                Outcome::Contested => "contested".into(),
                Outcome::Landed(s) => s,
            },
            None => "none".into(),
        };
        cases += 1;
        if ids != c.at("kept").strs() || cs != want_c || o != c.at("outcome").s() {
            bad += 1;
            eprintln!("{}: crate {o}, {cs:?}", c.at("name").s());
        }
    }
    report("window_bound", cases, bad);
    assert!(cases > 40, "{cases} cases");
    assert!(why_ok.get() > 40, "rule_bound_why answered {} window rows", why_ok.get());
    assert_eq!(bad, 0, "{bad} of {cases} differ");
}

/// A bound-path wait: a stalled infrastructure room's recovery widening (an offer) that opens a window, under a law
/// that binds no act (its table by name). The seat rule waits on the grant it names, with no trust root read, and
/// `rule_bound_why` passes the wait on as `Err(Wait(grant))`; `rule_bound` reads it as concluding nothing, as the
/// model does (`check_acts`: undecided).
#[test]
fn a_bound_opener_that_waits_says_on_what() {
    use ciris_kernel::layers::{conclude, kept};
    use ciris_kernel::seat::seat_rule;
    use ciris_kernel::window::{rule_bound, rule_bound_why};
    use ciris_kernel::Wait;
    let fx = fixture("window_bound.json");
    let w = fx.at("wait");
    let mut law = law_of(fx.at("law"));
    law.acts = None;
    let refs: BTreeMap<String, String> =
        w.at("refs").obj().iter().map(|(k, v)| (k.clone(), v.s().to_string())).collect();
    let rs = rows_with_refs(w.at("rows").arr(), &refs);
    let mut m = BTreeMap::new();
    m.insert(w.at("window").s().to_string(), w.at("spec").clone());
    let specs = windows_of(&J::Obj(m));
    let windows = |n: &String| specs.get(n).cloned();
    let families =
        |_: &str, _: &ciris_kernel::seat::Obj<String, String>, _: Option<&str>| -> Option<WindowSpec<i64>> { None };
    let spec = DictCut;
    let row = w.at("row").s().to_string();
    let seen = std::cell::RefCell::new(None);
    let c = conclude(
        kept(&rs, |_| true),
        |p| {
            let why = rule_bound_why(p, &families, &windows, &law, &spec);
            let plain = rule_bound(p, &families, &windows, &law, &spec);
            if p.row().id == row {
                *seen.borrow_mut() = Some((why.clone(), plain));
            }
            match plain {
                Some(v) => v,
                None => seat_rule(p, &law, &spec, &|_| true),
            }
        },
        None,
    );
    let (why, plain) = seen.into_inner().expect("the widening was read");
    assert_eq!(why, Some(Err(Wait(w.at("wait_on").s().to_string()))), "rule_bound_why names the grant it waits on");
    assert_eq!(plain, Some(false), "rule_bound reads a wait as concluding nothing");
    let i = c.g.idx(&row).unwrap();
    assert_eq!(c.concluded(i), w.at("concluded").b(), "the model's conclusion");
}

/// custodian_replace is held shut in 0.5.0 (the Constitution's ruling): its voice and counted_at are unstated, so its
/// count is no count; affiliation_member_action and cosigned_act, unstated too, are ruled and counted.
#[test]
fn custodian_replace_is_held_shut() {
    let fx = fixture("law_tables.json");
    let c = &fx.at("cases").arr()[0];
    let fams: Vec<PolicyRow> = c.at("families").arr().iter().map(row_of).collect();
    let shut: Vec<(String, &str)> = held_shut(&fams).into_iter().map(|r| (r.row, r.cell)).collect();
    assert_eq!(
        shut,
        vec![
            ("custodian_replace".to_string(), "counted.voice"),
            ("custodian_replace".to_string(), "counted.counted_at")
        ]
    );
    assert_eq!(c.at("law").at("policy").at("custodian_replace").arr()[0].s(), "not_a_count");
}
