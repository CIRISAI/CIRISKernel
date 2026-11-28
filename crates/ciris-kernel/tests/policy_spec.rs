//! Differential: a window's table from its policy row (`window::spec_from_policy`), against `window.py`'s
//! `spec_from_policy` over every row of the governance policy table and every plant of `check_policy_spec.py`
//! (fixture `policy_spec.json`). The row is decoded here from the table's own JSON, unchanged, as a caller would.

mod common;
use ciris_kernel::window::{
    spec_from_policy, Active, Cell, CountedCells, PolicyRefusal, PolicyRow, PolicyTable, RuleCell, Stated, Why,
    WindowSpec,
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
        let got: Result<WindowSpec<i64>, Vec<PolicyRefusal>> =
            spec_from_policy(&row_of(c.at("row")), &table_of(c.at("table")), active_of(c.at("active")));
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
    let c = fx.at("cases").arr().iter().find(|c| c.at("name").s() == "default_content").unwrap();
    let mut row = row_of(c.at("row"));
    let mut table = table_of(c.at("table"));
    row.window_secs = 1 << 40;
    table.window_classes.insert(row.window_class.clone(), 1 << 40);
    let got: Result<WindowSpec<u32>, _> = spec_from_policy(&row, &table, Some(Active::WithinK));
    assert_eq!(got.unwrap_err(), vec![PolicyRefusal { cell: "window_secs", why: Why::Unknown }]);
    assert!(spec_from_policy::<u64>(&row, &table, Some(Active::WithinK)).is_ok());
}
