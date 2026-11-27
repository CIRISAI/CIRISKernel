//! The fold at tips (`Seats::tips_fold`; KERNEL.md section 7; `models/roster_fork/fold.py`), on cases the
//! Python seat model does not hold: tips that differ in policy. (Its cases of a head one key wrote, an outsider's
//! own admission under `open:self_admit`, are retired with the cut of open admission: the one-key counted change
//! left, a lone duty holder's own conferral, places a duty seat and no member, so it shows nothing of the members'
//! fold.)
//! The seat fixture (`tests/seat.rs`) carries the fold's other cases, from `attacks.py`.

mod common;
use ciris_kernel::cut::CutSpec;
use ciris_kernel::layers::{conclude, kept};
use ciris_kernel::seat::{seat_rule, Conf, Obj, Policy, SeatKind, SeatLaw, SeatRow, Seats};
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
    conf: Option<Conf>,
    head: Vec<String>,
    policy: Option<String>,
    need: Option<usize>,
    regime: Option<String>,
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
        static M: std::sync::OnceLock<String> = std::sync::OnceLock::new();
        Some(M.get_or_init(|| "member".into()))
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
    fn regime(&self) -> Option<&String> {
        self.regime.as_ref()
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
/// The founding row of g, seating `members`.
fn found(members: &[&str]) -> K {
    let m = s(members);
    K {
        id: "g".into(),
        signer: m[0].clone(),
        kind: Some(SeatKind::Offer),
        to: m.clone(),
        cosigners: m[1..].to_vec(),
        conf: Some(Conf::Own),
        ..Default::default()
    }
}
/// A counted change on `heads`: it adds or removes `to`, signed by `signers` (a key it adds cosigns, as its yes).
fn change(id: &str, heads: &[&str], add: bool, to: &[&str], signers: &[&str], policy: &str, need: Option<usize>) -> K {
    let sg = s(signers);
    let mut co = sg[1..].to_vec();
    if add {
        co.extend(s(to));
    }
    K {
        id: id.into(),
        names: s(heads),
        signer: sg[0].clone(),
        kind: Some(if add { SeatKind::Offer } else { SeatKind::Unseat }),
        to: s(to),
        cosigners: co,
        conf: Some(Conf::Group),
        head: s(heads),
        policy: Some(policy.into()),
        need,
        ..Default::default()
    }
}
fn law() -> SeatLaw {
    let mut law = SeatLaw { depth: 5, roster_seats: s(&["member"]), ..Default::default() };
    law.policy.insert("maj".into(), Policy::Strict(1, 2));
    law.policy.insert("three".into(), Policy::Declared);
    law
}
/// (the fold's members, the keys common to the tips, whether row `x` concluded)
fn read(rows: &[K], x: &str) -> (String, String, bool) {
    let law = law();
    let c = conclude(kept(rows, |_| true), |q| seat_rule(q, &law, &Slots, &|_| true), None);
    let seats = Seats::new(&c, &law, &Slots, None);
    let g = Obj::Row("g".to_string());
    let join = |m: BTreeSet<String>| m.into_iter().collect::<Vec<_>>().join("");
    let common = seats.tips_common("member", &g).map(join).unwrap_or_else(|| "one tip".into());
    let done = c.g.idx(&x.to_string()).is_some_and(|i| c.concluded(i));
    (join(seats.holders("member", &g, None)), common, done)
}

#[test]
fn the_fold_at_tips() {
    let mut n = 0;
    let mut t = |got: (String, String, bool), want: (&str, &str, bool), what: &str| {
        n += 1;
        assert_eq!((got.0.as_str(), got.1.as_str(), got.2), want, "{what}");
    };
    let g = found(&["a", "b", "c"]);
    let x1 = change("x1", &["g"], true, &["j"], &["a", "b"], "maj", None);
    let x2 = change("x2", &["g"], true, &["k"], &["a", "c"], "maj", None);
    t(
        read(&[g.clone(), x1.clone(), x2.clone()], "x2"),
        ("abcjk", "abc", true),
        "two additions of different members both seat",
    );
    let r2 = change("x2", &["g"], false, &["b"], &["a", "c"], "maj", None);
    t(
        read(&[g.clone(), x1.clone(), r2.clone()], "x2"),
        ("ac", "ac", true),
        "an addition that needed the voice of a member another tip removes waits",
    );
    let x3 = change("x1", &["g"], true, &["j"], &["a", "c"], "maj", None);
    t(
        read(&[g.clone(), x3, r2], "x2"),
        ("acj", "ac", true),
        "an addition and a removal of different members both take effect where the count holds without the removed voice",
    );
    let mut p2 = x2.clone();
    p2.regime = Some("two thirds".into());
    t(read(&[g, x1, p2], "x2"), ("abc", "abc", true), "tips that differ in policy wait: the common members");
    report("the fold at tips: tips that differ in policy", n, 0);
}
