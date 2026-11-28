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

/// The protocol set: the kinds the crate parses are the Constitution's table's (`consensus_protocols.tsv`, as
/// `check_acts.py` reads it), and each word reads as seat.py's `protocol_rule` reads it, in a community and in an
/// infrastructure community (`infrastructure_rule`: a quorum of the founders' strict majority).
#[test]
fn protocol_set_replay() {
    use ciris_kernel::seat::{RoomProtocol, PROTOCOL_KINDS};
    let fx = fixture("acts.json");
    assert_eq!(fx.at("protocol_kinds").strs(), PROTOCOL_KINDS.map(String::from).to_vec());
    let (mut cases, mut bad) = (0, 0);
    for (list, infrastructure) in [("protocol_words", false), ("infrastructure_words", true)] {
        for w in fx.at(list).arr() {
            let a = w.arr();
            let word = a[0].s();
            let want = words_of(&a[1]);
            let got = RoomProtocol::parse_in(word, infrastructure).map(proto_words);
            cases += 1;
            if got != want {
                bad += 1;
                eprintln!("{list} {word:?}: got {got:?}, want {want:?}");
            }
        }
    }
    report("the protocol set against check_acts.py", cases, bad);
    assert_eq!(bad, 0);
}

type Words = (String, Option<u64>, Option<u64>);

/// seat.py's protocol_rule answer: (kind, m, n), or null.
fn words_of(j: &common::J) -> Option<Words> {
    (!j.is_null()).then(|| {
        let a = j.arr();
        let n = |x: &common::J| (!x.is_null()).then(|| x.i() as u64);
        (a[0].s().to_string(), n(&a[1]), n(&a[2]))
    })
}

fn proto_words(p: ciris_kernel::seat::RoomProtocol) -> Words {
    use ciris_kernel::seat::RoomProtocol;
    match p {
        RoomProtocol::FounderOnly => ("founder_only".to_string(), None, None),
        RoomProtocol::Unanimous => ("unanimous".to_string(), None, None),
        RoomProtocol::Majority => ("majority".to_string(), None, None),
        RoomProtocol::Quorum(m, n) => ("quorum".to_string(), Some(m), Some(n)),
        RoomProtocol::Weighted => ("weighted".to_string(), None, None),
        _ => ("?".to_string(), None, None),
    }
}

/// The recall is told by its act, not by the policy its fixed row maps to (the review of the binding): under a law
/// that maps `moderator_recall` to a plain threshold (`StrictFloor`, the recall's own numbers), a members' unseat of a
/// duty is still counted as the recall, over the members less the holder, the holder no voice. A, B and C of A, B,
/// C, D sign the recall of A: as the recall, two of the three others are not more than two thirds; as a plain count,
/// three of four would be.
#[test]
fn the_recall_is_told_by_its_act() {
    use ciris_kernel::layers::{conclude, kept};
    use ciris_kernel::seat::{seat_rule, Policy};
    use common::DictCut;
    let fx = fixture("acts.json");
    let fixed = law_of(fixture("seat.json").at("law"));
    let Some(Policy::Recall(n, d, l)) = fixed.policy.get("moderator_recall").copied() else {
        panic!("the fixture's law maps moderator_recall to the recall")
    };
    let mut plain = fixed.clone();
    plain.policy.insert("moderator_recall".into(), Policy::StrictFloor(n, d, l));
    let c = fx
        .at("conclude")
        .arr()
        .iter()
        .find(|c| c.at("name").s().starts_with("a members' unseat of a duty is the recall"))
        .expect("the recall case");
    let refs: BTreeMap<String, String> =
        c.at("refs").obj().iter().map(|(k, v)| (k.clone(), v.s().to_string())).collect();
    let mut rows = rows_with_refs(c.at("rows").arr(), &refs);
    let at = rows.iter().position(|r| r.id == "r").expect("the recall");
    for (signers, want) in [(["B", "C", "A"], false), (["B", "C", "D"], true)] {
        rows[at].signer = signers[0].into();
        rows[at].cosigners = signers[1..].iter().map(|k| k.to_string()).collect();
        for law in [&fixed, &plain] {
            let k = kept(&rows, |_| true);
            let cc = conclude(k, |p| seat_rule(p, law, &DictCut, &|_| true), None);
            let i = cc.g.rows().iter().position(|r| r.id == "r").expect("the recall");
            assert_eq!(cc.concluded(i), want, "the recall signed by {signers:?}");
        }
    }
}

/// A group is dissolved (`Seats::dissolved`): by a concluded dissolution, or with no signer when every member has
/// an end of their seat (`check_acts.py`'s DISSOLVED).
#[test]
fn dissolved_replay() {
    use ciris_kernel::layers::{conclude, kept};
    use ciris_kernel::seat::{seat_rule, Obj, Seats};
    use common::DictCut;
    let fx = fixture("acts.json");
    let law = law_of(fixture("seat.json").at("law"));
    let (mut cases, mut bad) = (0, 0);
    for c in fx.at("dissolved").arr() {
        let refs: BTreeMap<String, String> =
            c.at("refs").obj().iter().map(|(k, v)| (k.clone(), v.s().to_string())).collect();
        let rows = rows_with_refs(c.at("rows").arr(), &refs);
        let k = kept(&rows, |_| true);
        let cc = conclude(k, |p| seat_rule(p, &law, &DictCut, &|_| true), None);
        let q = Seats::new(&cc, &law, &DictCut, None);
        cases += 1;
        if q.dissolved(&Obj::Row(c.at("obj").s().to_string())) != c.at("dissolved").b() {
            bad += 1;
            eprintln!("dissolved {}: got {}", c.at("name").s(), !c.at("dissolved").b());
        }
    }
    report("a group's dissolution against check_acts.py", cases, bad);
    assert_eq!(bad, 0);
}

/// An infrastructure room's recovery widening while stalled is undecided, with its reason
/// (`seat::stalled_recovery`, `check_acts.py`'s UNDECIDED).
#[test]
fn undecided_replay() {
    use ciris_kernel::layers::{conclude, kept, Past};
    use ciris_kernel::seat::{seat_rule, stalled_recovery};
    use common::DictCut;
    let fx = fixture("acts.json");
    let law = law_of(fixture("seat.json").at("law"));
    let (mut cases, mut bad) = (0, 0);
    for c in fx.at("undecided").arr() {
        let refs: BTreeMap<String, String> =
            c.at("refs").obj().iter().map(|(k, v)| (k.clone(), v.s().to_string())).collect();
        let rows = rows_with_refs(c.at("rows").arr(), &refs);
        let k = kept(&rows, |_| true);
        let cc = conclude(k, |p| seat_rule(p, &law, &DictCut, &|_| true), None);
        let i = cc.g.rows().iter().position(|r| r.id == c.at("row").s()).expect("the row asked");
        let anc: Vec<usize> = cc.cs().iter().copied().filter(|&q| cc.g.in_past(q, i)).collect();
        let p = Past::new(&cc.g, i, &anc);
        let got = stalled_recovery(&p, &law, &DictCut);
        let want = c.get("reason").and_then(|r| r.opt_s());
        cases += 1;
        if got.map(String::from) != want {
            bad += 1;
            eprintln!("undecided {}: got {got:?}, want {want:?}", c.at("name").s());
        }
    }
    report("an infrastructure room's recovery widening against check_acts.py", cases, bad);
    assert_eq!(bad, 0);
}

/// An infrastructure room's liveness at a held row (`seat::infra_live`, `check_acts.py`'s INFRA_LIVE).
#[test]
fn infra_live_replay() {
    use ciris_kernel::layers::{conclude, kept};
    use ciris_kernel::seat::{infra_live, seat_rule, Liveness, Obj};
    use common::{DictCut, J};
    let fx = fixture("acts.json");
    let law = law_of(fixture("seat.json").at("law"));
    let (mut cases, mut bad) = (0, 0);
    for c in fx.at("infra_live").arr() {
        let refs: BTreeMap<String, String> =
            c.at("refs").obj().iter().map(|(k, v)| (k.clone(), v.s().to_string())).collect();
        let rows = rows_with_refs(c.at("rows").arr(), &refs);
        let k = kept(&rows, |_| true);
        let cc = conclude(k, |p| seat_rule(p, &law, &DictCut, &|_| true), None);
        let got = infra_live(&cc, &law, &DictCut, &Obj::Row(c.at("obj").s().to_string()), &c.at("at").s().to_string());
        let want = match c.at("live") {
            J::Null => None,
            J::Str(s) if s == "live" => Some(Liveness::Live),
            w => Some(Liveness::Stalled { active: w.at("active").i() as usize, m: w.at("m").i() as u64 }),
        };
        cases += 1;
        if got != want {
            bad += 1;
            eprintln!("infra_live {}: got {got:?}, want {want:?}", c.at("name").s());
        }
    }
    report("an infrastructure room's liveness against check_acts.py", cases, bad);
    assert!(cases > 0);
    assert_eq!(bad, 0);
}

#[test]
fn no_table_binds_nothing() {
    let law = SeatLaw::default();
    assert_eq!(policy_for(&law, Act::Admit, ScopeClass::Member, CommunityKind::Community), None);
}
