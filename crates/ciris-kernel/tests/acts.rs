//! The act-to-policy binding, steps 1 and 2: the act each counted row is (`seat::act_of`) and the policy rows each
//! act may take (`seat::policy_for`), replayed from `models/causal_kernel/check_acts.py` (fixture `acts.json`).

mod common;
use ciris_kernel::seat::{act_of, policy_for, Act, Choice, CommunityKind, ScopeClass, SeatLaw};
use common::{fixture, law_of, report, rows_with_refs};
use std::collections::BTreeMap;

#[test]
fn acts_replay() {
    let fx = fixture("acts.json");
    // the seat fixture's law: its policy map (the one act read from a stated policy reads it), roster seats,
    // duties, and the acts and kinds tables
    let law = law_of(fixture("seat.json").at("law"));
    assert!(law.acts.is_some(), "the fixture's law carries the acts table");
    let (mut cases, mut bad) = (0, 0);
    for c in fx.at("cases").arr() {
        let refs: BTreeMap<String, String> =
            c.at("refs").obj().iter().map(|(k, v)| (k.clone(), v.s().to_string())).collect();
        let rows = rows_with_refs(c.at("rows").arr(), &refs);
        let by: BTreeMap<&String, &common::TRow> = rows.iter().map(|r| (&r.id, r)).collect();
        let get = |i: &String| by.get(i).copied();
        let r = rows.iter().find(|r| r.id == c.at("row").s()).expect("the row asked");
        let got = act_of(&law, &get, r)
            .map(|(a, s, k)| vec![a.word().to_string(), s.word().to_string(), k.word().to_string()]);
        let want = c.get("act").filter(|a| !a.is_null()).map(|a| a.strs());
        cases += 1;
        if got != want {
            bad += 1;
            eprintln!("act_of {}: got {:?}, want {:?}", c.at("name").s(), got, want);
        }
    }
    for q in fx.at("queries").arr() {
        let a = q.at("ask").strs();
        let (act, sc, kd) = (
            Act::from_word(&a[0]).expect("an act"),
            ScopeClass::from_word(&a[1]).expect("a scope class"),
            CommunityKind::from_word(&a[2]).expect("a kind"),
        );
        let got = policy_for(&law, act, sc, kd).map(|(p, ch)| (p.to_vec(), ch));
        let want = q
            .get("policies")
            .filter(|p| !p.is_null())
            .map(|p| (p.strs(), Choice::from_word(q.at("choice").s()).expect("a choice")));
        cases += 1;
        if got != want {
            bad += 1;
            eprintln!("policy_for {:?}: got {:?}, want {:?}", a, got, want);
        }
    }
    report("act_of and policy_for against check_acts.py", cases, bad);
    assert_eq!(bad, 0);
}

/// The refusal (step 3): a counted row whose act may not take the policy it states concludes nothing; a protocol
/// row is counted under the founding record's protocol. Each case under the seat fixture's law and under the same
/// law with no acts table.
#[test]
fn refusal_replay() {
    use ciris_kernel::layers::{conclude, kept};
    use ciris_kernel::seat::seat_rule;
    use common::DictCut;
    let fx = fixture("acts.json");
    let bound = law_of(fixture("seat.json").at("law"));
    let unbound = SeatLaw { acts: None, ..bound.clone() };
    let (mut cases, mut bad) = (0, 0);
    for c in fx.at("conclude").arr() {
        let refs: BTreeMap<String, String> =
            c.at("refs").obj().iter().map(|(k, v)| (k.clone(), v.s().to_string())).collect();
        let rows = rows_with_refs(c.at("rows").arr(), &refs);
        for (law, want) in [(&bound, c.at("bound").b()), (&unbound, c.at("unbound").b())] {
            let k = kept(&rows, |_| true);
            let cc = conclude(k, |p| seat_rule(p, law, &DictCut, &|_| true), None);
            let i = cc.g.rows().iter().position(|r| r.id == c.at("row").s()).expect("the row asked");
            cases += 1;
            if cc.concluded(i) != want {
                bad += 1;
                eprintln!("refusal {} (table: {}): got {}, want {}", c.at("name").s(), law.acts.is_some(), !want, want);
            }
        }
    }
    report("the act-to-policy refusal against check_acts.py", cases, bad);
    assert_eq!(bad, 0);
}

#[test]
fn no_table_binds_nothing() {
    let law = SeatLaw::default();
    assert_eq!(policy_for(&law, Act::Admit, ScopeClass::Member, CommunityKind::Community), None);
}
