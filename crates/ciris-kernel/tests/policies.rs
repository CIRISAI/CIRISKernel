//! The counts CC 3.3.4 and CC 4.4.3.6 state, each on the sentence's own case: `unanimous` (with its removal
//! reading), `weighted`, `founder_only` (as a count over the founder scope), and "no key
//! admits itself" (CC 2.7.5). These rules are not in the Python models; the cases are the text's.

mod common;
use ciris_kernel::cut::CutSpec;
use ciris_kernel::layers::{conclude, kept};
use ciris_kernel::seat::{seat_rule, Conf, Obj, Policy, SeatKind, SeatLaw, SeatRow};
use ciris_kernel::Row;
use common::report;
use std::collections::BTreeSet;

#[derive(Clone, Debug, Default)]
struct K {
    id: String,
    names: Vec<String>,
    signer: String,
    kind: Option<SeatKind>,
    to: Vec<String>,
    cosigners: Vec<String>,
    scope: Option<String>,
    conf: Option<Conf>,
    head: Vec<String>,
    policy: Option<String>,
    need: Option<usize>,
    counted: Option<String>,
    weights: Vec<(String, u64)>,
}
impl Row for K {
    type Id = String;
    type Key = String;
    fn id(&self) -> &String {
        &self.id
    }
    fn names(&self) -> &[String] {
        &self.names
    }
    fn signer(&self) -> &String {
        &self.signer
    }
}
impl SeatRow for K {
    type Word = String;
    fn word(s: &'static str) -> String {
        s.into()
    }
    fn seat_kind(&self) -> SeatKind {
        self.kind.unwrap_or(SeatKind::Other)
    }
    fn to(&self) -> &[String] {
        &self.to
    }
    fn scope(&self) -> Option<&String> {
        self.scope.as_ref()
    }
    fn obj(&self) -> Option<Obj<String, String>> {
        Some(Obj::Row("g".into()))
    }
    fn conf(&self) -> Option<Conf> {
        self.conf
    }
    fn cosigners(&self) -> &[String] {
        &self.cosigners
    }
    fn head(&self) -> &[String] {
        &self.head
    }
    fn policy(&self) -> Option<&String> {
        self.policy.as_ref()
    }
    fn need(&self) -> Option<usize> {
        self.need
    }
    fn counted(&self) -> Option<&String> {
        self.counted.as_ref()
    }
    fn weights(&self) -> &[(String, u64)] {
        &self.weights
    }
}
struct Slots;
impl CutSpec<K> for Slots {
    type Slot = String;
    type Say = String;
    fn key_slot(&self, k: &String) -> String {
        format!("key|{k}")
    }
    fn on_slots(&self, r: &K) -> BTreeSet<String> {
        [self.key_slot(&r.signer)].into()
    }
    fn cuts_of(&self, _: &K) -> BTreeSet<String> {
        BTreeSet::new()
    }
    fn says(&self, r: &K) -> String {
        r.id.clone()
    }
}

fn s(v: &[&str]) -> Vec<String> {
    v.iter().map(|x| x.to_string()).collect()
}

#[allow(clippy::too_many_arguments)]
/// A group of `members` (and `founders` among them, seated in the founder scope as well); a change under
/// `policy` that adds (`add`) or removes the keys `to`, signed by `signers`. Does the change conclude?
fn admits(
    policy: Policy,
    need: Option<usize>,
    counted: &str,
    members: &[&str],
    founders: &[&str],
    add: bool,
    to: &[&str],
    signers: &[&str],
    weights: &[(&str, u64)],
) -> bool {
    let m = s(members);
    let mut rows = vec![K {
        id: "g".into(),
        signer: m[0].clone(),
        kind: Some(SeatKind::Offer),
        to: m.clone(),
        cosigners: m[1..].to_vec(),
        scope: Some("member".into()),
        conf: Some(Conf::Own),
        ..Default::default()
    }];
    if !founders.is_empty() {
        // the founders' seats, placed by a counted change of the room (a head of a count is a counted change or
        // the founding row: the heads ruling of 2026-11-26), every member signing and each founder its own yes
        let f = s(founders);
        let mut co: Vec<String> = m[1..].to_vec();
        co.extend(f.iter().filter(|k| !m[..1].contains(k)).cloned());
        rows.push(K {
            id: "gf".into(),
            names: s(&["g"]),
            signer: m[0].clone(),
            kind: Some(SeatKind::Offer),
            to: f.clone(),
            cosigners: co,
            scope: Some("founder".into()),
            conf: Some(Conf::Group),
            head: s(&["g"]),
            policy: Some("all".into()),
            counted: Some("member".into()),
            ..Default::default()
        });
    }
    let head = rows.last().unwrap().id.clone();
    let sg = s(signers);
    rows.push(K {
        id: "x".into(),
        names: vec![head.clone()],
        signer: sg[0].clone(),
        kind: Some(if add { SeatKind::Offer } else { SeatKind::Unseat }),
        to: s(to),
        cosigners: sg[1..].to_vec(),
        scope: Some("member".into()),
        conf: Some(Conf::Group),
        head: vec![head],
        policy: Some("p".into()),
        need,
        counted: Some(counted.into()),
        weights: weights.iter().map(|(k, w)| (k.to_string(), *w)).collect(),
    });
    let mut law = SeatLaw { depth: 5, roster_seats: s(&["member"]), ..Default::default() };
    law.holds.insert("founder".into(), s(&["member"]));
    law.policy.insert("p".into(), policy);
    // the founders' seating counts every member but the keys it seats (no key admits itself, CC 2.7.5): a strict
    // majority of the members, each founder already a member re-seated in the founder role
    law.policy.insert("all".into(), Policy::AtLeast(1, 2));
    let c = conclude(kept(&rows, |_| true), |q| seat_rule(q, &law, &Slots, &|_| true), None);
    c.concluded(c.g.idx(&"x".to_string()).unwrap())
}

#[test]
fn the_counts_the_text_states() {
    let abc = ["a", "b", "c"];
    let cases: Vec<(&str, bool, bool)> = vec![
        // CC 3.3.4 unanimous: "Every current member must sign the admission"
        (
            "unanimous: all three admit j",
            admits(Policy::Unanimous, None, "member", &abc, &[], true, &["j"], &["a", "b", "c"], &[]),
            true,
        ),
        (
            "unanimous: two of three do not",
            admits(Policy::Unanimous, None, "member", &abc, &[], true, &["j"], &["a", "b"], &[]),
            false,
        ),
        // "For a removal, every member other than the target signs and those signers are a strict majority"
        (
            "unanimous: the two others remove b",
            admits(Policy::Unanimous, None, "member", &abc, &[], false, &["b"], &["a", "c"], &[]),
            true,
        ),
        (
            "unanimous: one other does not",
            admits(Policy::Unanimous, None, "member", &abc, &[], false, &["b"], &["a"], &[]),
            false,
        ),
        (
            "unanimous: the target is no voice",
            admits(Policy::Unanimous, None, "member", &abc, &[], false, &["b"], &["a", "b"], &[]),
            false,
        ),
        // "a two-member group therefore removes nobody by this door"
        (
            "unanimous: at two nobody is removed",
            admits(Policy::Unanimous, None, "member", &["a", "b"], &[], false, &["b"], &["a"], &[]),
            false,
        ),
        // CC 4.5.13: "At two members nobody is removed", the consent of the one removed included
        (
            "unanimous: at two the consent of the one removed removes nobody",
            admits(Policy::Unanimous, None, "member", &["a", "b"], &[], false, &["b"], &["a", "b"], &[]),
            false,
        ),
        // CC 2.7.5: on a plain count the member removed is a voice of its removal
        (
            "majority: the member removed is a voice of its removal",
            admits(
                Policy::Strict(1, 2),
                None,
                "member",
                &["a", "b", "c", "d"],
                &[],
                false,
                &["d"],
                &["a", "b", "d"],
                &[],
            ),
            true,
        ),
        (
            "majority: two of four do not remove",
            admits(Policy::Strict(1, 2), None, "member", &["a", "b", "c", "d"], &[], false, &["d"], &["a", "b"], &[]),
            false,
        ),
        (
            "majority: a member seated again is still no voice of its own seating",
            admits(
                Policy::Strict(1, 2),
                None,
                "member",
                &["a", "b", "c", "d"],
                &[],
                true,
                &["d"],
                &["a", "b", "d"],
                &[],
            ),
            false,
        ),
        // CC 2.7.5 "no key admits itself"; CC 3.3.4 founder_only "cannot re-seat itself alone"
        (
            "quorum 1: a member does not re-seat itself",
            admits(Policy::Declared, Some(1), "member", &["a", "b"], &[], true, &["a"], &["a"], &[]),
            false,
        ),
        (
            "quorum 1: a member seats another",
            admits(Policy::Declared, Some(1), "member", &["a", "b"], &[], true, &["j"], &["a"], &[]),
            true,
        ),
        // CC 3.3.4 founder_only: "new members proposed-and-admitted by any active founder"
        (
            "founder_only: a founder admits",
            admits(Policy::One, None, "founder", &abc, &["a"], true, &["j"], &["a"], &[]),
            true,
        ),
        (
            "founder_only: a member who is no founder does not",
            admits(Policy::One, None, "founder", &abc, &["a"], true, &["j"], &["b"], &[]),
            false,
        ),
        // CC 3.3.4 weighted: "The sum of the signing members' weights must reach a threshold", whole numbers
        (
            "weighted: 2 + 1 reaches 3",
            admits(
                Policy::Weighted,
                Some(3),
                "member",
                &abc,
                &[],
                true,
                &["j"],
                &["a", "b"],
                &[("a", 2), ("b", 1), ("c", 1)],
            ),
            true,
        ),
        (
            "weighted: 1 + 1 does not",
            admits(
                Policy::Weighted,
                Some(3),
                "member",
                &abc,
                &[],
                true,
                &["j"],
                &["b", "c"],
                &[("a", 2), ("b", 1), ("c", 1)],
            ),
            false,
        ),
        (
            "weighted: a non-member's weight is no weight",
            admits(Policy::Weighted, Some(3), "member", &abc, &[], true, &["j"], &["a", "z"], &[("a", 2), ("z", 5)]),
            false,
        ),
    ];
    let mut bad = 0;
    for (name, got, want) in &cases {
        if got != want {
            bad += 1;
            eprintln!("{name}: got {got}, the text gives {want}");
        }
    }
    report("the counts CC 3.3.4 and CC 4.4.3.6 state, on their own cases", cases.len(), bad);
    assert_eq!(bad, 0);
}
