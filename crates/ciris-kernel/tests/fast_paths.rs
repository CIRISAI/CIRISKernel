//! Differential: each path made faster for persist (PERF.md) against the definition it replaced, over
//! generated cases. The definitions are kept here, as written before, as the oracles.
//!
//! * `seat::group_count` over a resolved roster against the seat rule over the same roster as rows (the graph
//!   path persist's adapter first took: a founding row, one offer per seat, the version, the counted row);
//! * `graph::Graph::frontier` against the pairwise frontier, before and after pasts are known, and a graph
//!   given duplicate ids against the eager closure;
//! * `trust::reaches`, `trust::EdgeIndex::reaches` and `honours`, and `derived::reach`, against the walks they
//!   replaced;
//! * `key_end::retained` against the per-row reading of `key_end::ended`.

mod common;
#[path = "common/dag.rs"]
mod dag;
use ciris_kernel::cut::CutSpec;
use ciris_kernel::graph::Graph;
use ciris_kernel::key_end::{self, EndRule, KeyEndRow, Record};
use ciris_kernel::layers::{conclude, Concluded};
use ciris_kernel::seat::{group_count, seat_rule, Conf, GroupCount, Obj, Policy, SeatKind, SeatLaw, SeatRow};
use ciris_kernel::trust::{self, Accepts};
use ciris_kernel::{derived, ops, Row};
use common::eager::EagerGraph;
use common::report;
use dag::{dag, Lcg};
use std::collections::{BTreeMap, BTreeSet};

#[derive(Clone, Debug, PartialEq)]
struct S {
    id: u32,
    names: Vec<u32>,
    signer: u32,
    kind: SeatKind,
    to: Vec<u32>,
    scope: Option<String>,
    obj: Option<Obj<u32, u32>>,
    conf: Option<Conf>,
    cosigners: Vec<u32>,
    head: Vec<u32>,
    policy: Option<String>,
    counted: Option<String>,
    need: Option<usize>,
    of: Option<u32>,
    target: Option<u32>,
    weights: Vec<(u32, u64)>,
    rec: Option<(u32, i64, Option<i64>)>,
    revokes: Option<(u32, i64)>,
    room: Option<Obj<u32, u32>>,
}

impl S {
    fn new(id: u32, names: Vec<u32>, signer: u32, kind: SeatKind) -> S {
        S {
            id,
            names,
            signer,
            kind,
            to: Vec::new(),
            scope: None,
            obj: None,
            conf: None,
            cosigners: Vec::new(),
            head: Vec::new(),
            policy: None,
            counted: None,
            need: None,
            of: None,
            target: None,
            weights: Vec::new(),
            rec: None,
            revokes: None,
            room: None,
        }
    }
}

impl Row for S {
    type Id = u32;
    type Key = u32;
    fn id(&self) -> &u32 {
        &self.id
    }
    fn names(&self) -> &[u32] {
        &self.names
    }
    fn signer(&self) -> &u32 {
        &self.signer
    }
}

impl SeatRow for S {
    type Word = String;
    fn word(s: &'static str) -> String {
        s.into()
    }
    fn seat_kind(&self) -> SeatKind {
        self.kind
    }
    fn to(&self) -> &[u32] {
        &self.to
    }
    fn scope(&self) -> Option<&String> {
        self.scope.as_ref()
    }
    fn obj(&self) -> Option<Obj<u32, u32>> {
        self.obj.clone()
    }
    fn conf(&self) -> Option<Conf> {
        self.conf
    }
    fn cosigners(&self) -> &[u32] {
        &self.cosigners
    }
    fn head(&self) -> &[u32] {
        &self.head
    }
    fn policy(&self) -> Option<&String> {
        self.policy.as_ref()
    }
    fn counted(&self) -> Option<&String> {
        self.counted.as_ref()
    }
    fn need(&self) -> Option<usize> {
        self.need
    }
    fn of(&self) -> Option<&u32> {
        self.of.as_ref()
    }
    fn target(&self) -> Option<&u32> {
        self.target.as_ref()
    }
    fn weights(&self) -> &[(u32, u64)] {
        &self.weights
    }
    fn room(&self) -> Option<Obj<u32, u32>> {
        self.room.clone()
    }
}

impl KeyEndRow for S {
    type T = i64;
    fn record(&self) -> Option<Record<'_, u32, i64>> {
        self.rec.as_ref().map(|(k, from, until)| Record {
            key: k,
            from: *from,
            until: *until,
            succ_of: None,
            at_old: None,
            sigs: &self.cosigners,
            end: EndRule::Optional,
        })
    }
    fn revocation(&self) -> Option<(&u32, i64)> {
        self.revokes.as_ref().map(|(k, a)| (k, *a))
    }
}

struct NoCut;
impl CutSpec<S> for NoCut {
    type Slot = u32;
    type Say = ();
    fn key_slot(&self, k: &u32) -> u32 {
        *k
    }
    fn on_slots(&self, r: &S) -> BTreeSet<u32> {
        std::iter::once(r.signer).collect()
    }
    fn cuts_of(&self, _r: &S) -> BTreeSet<u32> {
        BTreeSet::new()
    }
    fn says(&self, _r: &S) {}
}

const POLICIES: &[(&str, Policy)] = &[
    ("one", Policy::One),
    ("strict", Policy::Strict(1, 2)),
    ("atleast", Policy::AtLeast(2, 3)),
    ("declared", Policy::Declared),
    ("unanimous", Policy::Unanimous),
    ("self_admit", Policy::SelfAdmit),
    ("weighted", Policy::Weighted),
    ("duty_confer", Policy::DutyConfer),
    ("duty_withdraw", Policy::DutyWithdraw),
    ("not_a_count", Policy::NotACount),
];

fn law() -> SeatLaw {
    SeatLaw {
        roster_seats: vec!["member".into(), "founder".into()],
        depth: 1,
        policy: POLICIES.iter().map(|(w, p)| (w.to_string(), *p)).collect(),
        ..Default::default()
    }
}

fn pick(g: &mut Lcg, n: u64) -> u64 {
    g.next() % n
}

/// One generated ballot: the rows, and what a caller that resolved the roster would hold.
struct Ballot {
    rows: Vec<S>,
    policy: Option<Policy>,
    offer: bool,
    to: Vec<u32>,
    members: BTreeSet<u32>,
    voices: BTreeSet<u32>,
    need: Option<usize>,
    weights: Vec<(u32, u64)>,
}

fn ballot(g: &mut Lcg) -> Ballot {
    let n = 1 + pick(g, 9) as u32; // members 1..=n; key 1 founds the group
    let founders: BTreeSet<u32> = (1..=n).filter(|_| pick(g, 3) == 0).collect();
    let counted = if pick(g, 3) == 0 { "founder" } else { "member" };
    let mut rows = Vec::new();
    let mut gr = S::new(0, Vec::new(), 1, SeatKind::Offer);
    gr.to = vec![1];
    gr.scope = Some("member".into());
    gr.obj = Some(Obj::Row(0));
    gr.conf = Some(Conf::Own);
    rows.push(gr);
    // the founding record seats key 1; every other seat is a counted admission of one voice, the key cosigning
    // (its own consent): a roster seat over a group is placed by the founding record or a counted row
    let seat = |id: u32, k: u32, scope: &str| {
        let mut o = S::new(id, vec![0], 1, SeatKind::Offer);
        o.to = vec![k];
        o.scope = Some(scope.into());
        o.obj = Some(Obj::Row(0));
        o.conf = Some(Conf::Group);
        o.head = vec![0];
        o.policy = Some("one".into());
        if k != 1 {
            o.cosigners = vec![k];
        }
        o
    };
    for k in 2..=n {
        rows.push(seat(100 + k, k, "member"));
    }
    for &f in &founders {
        rows.push(seat(200 + f, f, "founder"));
    }
    let mut version: Vec<u32> = rows.iter().map(|r| r.id).collect();
    let mut in_c: Vec<u32> = Vec::new();
    // some keys leave a seat: a withdrawal by the key of the offer that seats it, in the head's past or only
    // in the counted row's
    let mut left: BTreeSet<u32> = BTreeSet::new();
    for k in 1..=n {
        if pick(g, 5) != 0 {
            continue;
        }
        let founder_seat = founders.contains(&k) && pick(g, 2) == 0;
        let t = if founder_seat {
            200 + k
        } else if k == 1 {
            0
        } else {
            100 + k
        };
        let mut w = S::new(300 + k, vec![t], k, SeatKind::Withdraw);
        w.target = Some(t);
        rows.push(w);
        if (founder_seat && counted == "founder") || (!founder_seat && counted == "member") {
            left.insert(k);
        }
        if pick(g, 2) == 0 {
            version.push(300 + k);
        } else {
            in_c.push(300 + k);
        }
    }
    rows.push(S::new(1000, version, 1, SeatKind::Other));
    // the voices: members and keys of no seat (50, 51)
    let mut voices: Vec<u32> = (1..=n).chain([50, 51]).filter(|_| pick(g, 2) == 0).collect();
    // a cosignature row naming the head, a voice for the counted row
    let mut cosig = None;
    if pick(g, 3) == 0 {
        let k = 1 + pick(g, n as u64 + 1) as u32;
        let mut c = S::new(3000, vec![1000], k, SeatKind::Cosign);
        c.of = Some(2000);
        rows.push(c);
        in_c.push(3000);
        cosig = Some(k);
    }
    let signer = if voices.is_empty() { 99 } else { voices.remove(0) };
    let to: Vec<u32> = match pick(g, 5) {
        0 => Vec::new(),
        1 => vec![50],
        2 => vec![1 + pick(g, n as u64) as u32, 1 + pick(g, n as u64) as u32],
        _ => vec![1 + pick(g, n as u64) as u32],
    };
    let to: Vec<u32> = {
        let mut seen = BTreeSet::new();
        to.into_iter().filter(|k| seen.insert(*k)).collect()
    };
    let (word, policy) = POLICIES[pick(g, POLICIES.len() as u64) as usize];
    let need = if pick(g, 4) == 0 { None } else { Some(pick(g, n as u64 + 2) as usize) };
    let mut weights: Vec<(u32, u64)> = Vec::new();
    for k in (1..=n).chain([50]) {
        if pick(g, 4) != 0 {
            weights.push((k, pick(g, 4)));
        }
    }
    let offer = pick(g, 3) != 0;
    let mut c =
        S::new(2000, [vec![1000], in_c].concat(), signer, if offer { SeatKind::Offer } else { SeatKind::Unseat });
    c.to = to.clone();
    c.scope = Some("member".into());
    c.obj = Some(Obj::Row(0));
    c.conf = Some(Conf::Group);
    c.cosigners = voices.clone();
    c.head = vec![1000];
    c.policy = Some(word.into());
    c.counted = Some(counted.into());
    c.need = need;
    c.weights = weights.clone();
    rows.push(c);
    let seated: BTreeSet<u32> = if counted == "founder" { founders } else { (1..=n).collect() };
    let mut vs: BTreeSet<u32> = voices.into_iter().collect();
    vs.insert(signer);
    vs.extend(cosig);
    Ballot {
        rows,
        policy: Some(policy),
        offer,
        to,
        members: seated.difference(&left).copied().collect(),
        voices: vs,
        need,
        weights,
    }
}

/// The seat rule's `Conf::Group` arm written a second time, inline over the counted row, from its voices on.
fn count_before(r: &S, is_offer: bool, pol: Option<Policy>, mem: &BTreeSet<u32>, v: &BTreeSet<u32>) -> bool {
    if pol == Some(Policy::SelfAdmit) {
        return if is_offer && r.to().len() == 1 && !mem.contains(&r.to()[0]) {
            v.contains(&r.to()[0])
        } else {
            v.iter().filter(|k| mem.contains(*k) && !r.to().contains(k)).count() >= 2
        };
    }
    if matches!(pol, Some(Policy::DutyConfer) | Some(Policy::DutyWithdraw)) {
        let yes: BTreeSet<&u32> = v.iter().filter(|k| mem.contains(*k)).collect();
        let withdraw = pol == Some(Policy::DutyWithdraw);
        let mem_r: BTreeSet<&u32> = mem.iter().collect();
        let to_r: BTreeSet<&u32> = r.to().iter().collect();
        let base: BTreeSet<&u32> = if withdraw { mem_r.difference(&to_r).copied().collect() } else { mem_r.clone() };
        let y = yes.intersection(&base).count();
        return 2 * y > base.len() && (y >= 2 || mem.len() < 2);
    }
    // on a removal the member removed is a voice unless the policy's text excludes it (CC 2.7.5)
    let yes: BTreeSet<&u32> = v
        .iter()
        .filter(|k| mem.contains(*k) && !((is_offer || pol == Some(Policy::Unanimous)) && r.to().contains(k)))
        .collect();
    if pol == Some(Policy::Weighted) {
        let sum: u64 = yes.iter().map(|k| r.weights().iter().find(|(w, _)| w == *k).map_or(0, |(_, x)| *x)).sum();
        return r.need().is_some_and(|t| t > 0 && sum >= t as u64);
    }
    if pol == Some(Policy::Unanimous) {
        let others = mem.iter().filter(|k| !r.to().contains(k)).count();
        return if is_offer {
            !mem.is_empty() && yes.len() == others && r.to().iter().all(|k| !mem.contains(k) || v.contains(k))
        } else {
            yes.len() == others && 2 * yes.len() > mem.len()
        };
    }
    ciris_kernel::seat::met(pol, yes.len(), mem.len(), r.need())
}

#[test]
fn group_count_equals_the_seat_rule_over_the_rows() {
    let law = law();
    let mut g = Lcg(11);
    let (mut cases, mut bad) = (0usize, 0usize);
    let mut by: BTreeMap<String, (usize, usize)> = BTreeMap::new();
    for _ in 0..40_000 {
        let b = ballot(&mut g);
        let c = conclude(b.rows.iter(), |p| seat_rule(p, &law, &NoCut, &|_| true), None);
        let rows_say = c.concluded_id(&2000);
        let count = GroupCount {
            policy: b.policy,
            offer: b.offer,
            to: &b.to,
            members: &b.members,
            voices: &b.voices,
            need: b.need,
        };
        let direct = group_count(&count, |k| b.weights.iter().find(|(w, _)| w == k).map_or(0, |(_, x)| *x))
            .expect("no generated ballot is ranked");
        let before = count_before(b.rows.last().unwrap(), b.offer, b.policy, &b.members, &b.voices);
        cases += 1;
        bad += (before != direct) as usize;
        let e = by.entry(format!("{:?}/{}", b.policy.unwrap(), rows_say)).or_default();
        e.0 += 1;
        if rows_say != direct {
            bad += 1;
            e.1 += 1;
        }
    }
    for (k, (n, x)) in &by {
        eprintln!("  {k}: {n} cases, {x} differ");
    }
    // every policy is met in some case and missed in another
    for (w, p) in POLICIES {
        if *p == Policy::NotACount {
            continue;
        }
        for v in [true, false] {
            assert!(by.contains_key(&format!("{p:?}/{v}")), "no case of {w} answering {v}");
        }
    }
    report("group_count against the seat rule over the ballot's rows and the count it replaced", cases, bad);
    assert_eq!(bad, 0);
}

#[test]
fn frontier_equals_the_pairwise_frontier() {
    let (mut cases, mut bad) = (0usize, 0usize);
    for (n, k, w, seed) in [(60, 1, 1, 1), (200, 3, 8, 2), (300, 2, 300, 3), (500, 4, 20, 4), (90, 2, 3, 5)] {
        let rows = dag(n, k, w, seed);
        let m = rows.len();
        let mut g = Lcg(seed + 40);
        for warm in [false, true] {
            let lazy = Graph::new(rows.iter());
            if warm {
                // some pasts known, so the walk takes them whole
                for i in (0..m).step_by(7) {
                    lazy.ancestors(i);
                }
            }
            for size in [0usize, 1, 2, 16, 17, 18, 40, 100, m] {
                for _ in 0..(if size >= 100 { 2 } else { 20 }) {
                    let mut of: Vec<usize> = (0..size).map(|_| (g.next() as usize) % m).collect();
                    if size == m {
                        of = (0..m).rev().collect();
                    }
                    let pairwise: Vec<usize> =
                        of.iter().copied().filter(|&r| !of.iter().any(|&q| lazy.in_past(r, q))).collect();
                    cases += 1;
                    bad += (lazy.frontier(&of) != pairwise) as usize;
                }
            }
        }
    }
    // a later row with an id already present is ignored, whatever order the rows come in
    let mut rows = dag(150, 3, 10, 9);
    let mut g = Lcg(5);
    for i in 0..60 {
        let mut r = rows[(g.next() as usize) % 150].clone();
        // it names only lower ids, as every row of `dag` does: a kept set has no cycle
        r.names = if r.id == 0 { Vec::new() } else { vec![(g.next() % r.id as u64) as u32] };
        r.signer = 1000 + i;
        let at = (g.next() as usize) % rows.len();
        rows.insert(at, r);
    }
    let lazy = Graph::new(rows.iter());
    let eager = EagerGraph::new(rows.iter());
    for a in 0..lazy.len() {
        cases += 1;
        bad += (lazy.row(a) != eager.row(a) || lazy.depth(a) != eager.depth(a)) as usize;
        for b in 0..lazy.len() {
            cases += 1;
            bad += (lazy.in_past(a, b) != eager.in_past(a, b)) as usize;
        }
    }
    for r in &rows {
        cases += 1;
        bad += (lazy.idx(&r.id) != eager.idx(&r.id)) as usize;
    }
    cases += 1;
    bad += lazy.idx(&9999).is_some() as usize;
    report("the frontier's walk against the pairwise frontier; duplicate ids", cases, bad);
    assert_eq!(bad, 0);
}

/// `trust::reaches` as first written: every key and edge copied, every edge read at every key.
fn reaches_before(edges: &[Accepts<u32, u8>], from: &u32, c: &u8, budget: u32, a: &u32) -> bool {
    let mut best: BTreeMap<u32, u32> = BTreeMap::new();
    best.insert(*from, budget);
    let mut todo: Vec<u32> = vec![*from];
    while let Some(k) = todo.pop() {
        let b = best[&k];
        if b == 0 {
            continue;
        }
        for e in edges.iter().filter(|e| e.src == k && e.admits(c)) {
            if e.dst == *a {
                return true;
            }
            let nb = std::cmp::min(b - 1, e.depth);
            if best.get(&e.dst).is_none_or(|&o| nb > o) {
                best.insert(e.dst, nb);
                todo.push(e.dst);
            }
        }
    }
    false
}

/// `derived::reach` as first written: the bounded repeat over every edge.
fn reach_before(own: &u32, depth: usize, edges: &[(u32, u32)]) -> BTreeSet<u32> {
    let start: BTreeSet<u32> = std::iter::once(*own).collect();
    ops::fix(start, depth, |ks| {
        let mut n = ks.clone();
        for (s, t) in edges {
            if ks.contains(s) {
                n.insert(*t);
            }
        }
        n
    })
}

#[test]
fn the_walks_equal_the_walks_they_replaced() {
    let (mut cases, mut bad) = (0usize, 0usize);
    let mut g = Lcg(21);
    for _ in 0..4_000 {
        let keys = 1 + pick(&mut g, 12) as u32;
        let ne = pick(&mut g, 3 * keys as u64 + 1) as usize;
        let edges: Vec<Accepts<u32, u8>> = (0..ne)
            .map(|_| Accepts {
                src: pick(&mut g, keys as u64) as u32,
                dst: pick(&mut g, keys as u64) as u32,
                classes: (0..pick(&mut g, 3)).map(|_| pick(&mut g, 3) as u8).collect(),
                depth: pick(&mut g, 4) as u32,
            })
            .collect();
        let pairs: Vec<(u32, u32)> = edges.iter().map(|e| (e.src, e.dst)).collect();
        let index = trust::EdgeIndex::new(&edges);
        for from in 0..keys {
            for depth in 0..5 {
                cases += 1;
                bad += (derived::reach(&from, depth, &pairs) != reach_before(&from, depth, &pairs)) as usize;
            }
            for a in 0..keys {
                for c in 0..3u8 {
                    for budget in [0, 1, 2, trust::HOP_CAP] {
                        let want = reaches_before(&edges, &from, &c, budget, &a);
                        cases += 2;
                        bad += (trust::reaches(&edges, &from, &c, budget, &a) != want) as usize;
                        bad += (index.reaches(&from, &c, budget, &a) != want) as usize;
                    }
                    let charter = |k: &u32, c: &u8| !(*k + *c as u32).is_multiple_of(3);
                    cases += 1;
                    bad += (index.honours(&from, charter, &a, &c) != trust::honours(&edges, &from, charter, &a, &c))
                        as usize;
                }
            }
        }
    }
    report("trust::reaches and derived::reach against the walks they replaced", cases, bad);
    assert_eq!(bad, 0);
}

/// `key_end::retained` as first written: each concluded row reads `ended` for its key.
fn retained_before(c: &Concluded<'_, S>, now: i64) -> BTreeSet<usize> {
    let mut out = BTreeSet::new();
    for &i in c.cs() {
        let r = c.g.row(i);
        let seed = r.revocation().is_some() || {
            let k = r.record().map(|x| x.key).unwrap_or(r.signer());
            !key_end::ended(c, k, now)
        };
        if seed {
            out.insert(i);
            out.extend(c.g.ancestors(i).iter());
        }
    }
    out
}

#[test]
fn retained_equals_the_per_row_reading() {
    let (mut cases, mut bad) = (0usize, 0usize);
    let mut g = Lcg(31);
    for _ in 0..3_000 {
        let keys = 1 + pick(&mut g, 5) as u32;
        let mut rows: Vec<S> = Vec::new();
        for i in 0..(1 + pick(&mut g, 14)) as u32 {
            let names: Vec<u32> =
                if i == 0 { Vec::new() } else { (0..pick(&mut g, 3)).map(|_| pick(&mut g, i as u64) as u32).collect() };
            let k = pick(&mut g, keys as u64) as u32;
            let mut r = S::new(i, names, k, SeatKind::Other);
            match pick(&mut g, 4) {
                0 => {
                    let from = pick(&mut g, 20) as i64;
                    let until = if pick(&mut g, 3) == 0 { None } else { Some(from + pick(&mut g, 30) as i64) };
                    r.rec = Some((if pick(&mut g, 5) == 0 { (k + 1) % keys } else { k }, from, until));
                }
                1 => {
                    let rk = if pick(&mut g, 4) == 0 { (k + 1) % keys } else { k };
                    r.revokes = Some((rk, pick(&mut g, 40) as i64));
                }
                _ => {}
            }
            rows.push(r);
        }
        let c = conclude(rows.iter(), |_| pick(&mut Lcg(0), 1) == 0, None);
        for now in [0i64, 5, 10, 20, 30, 45] {
            cases += 1;
            bad += (key_end::retained(&c, now) != retained_before(&c, now)) as usize;
        }
    }
    report("key_end::retained against the per-row reading of ended", cases, bad);
    assert_eq!(bad, 0);
}

/// One founding offer seating many keys (more than `Seats::new` scans its signers for): a key is seated iff it
/// signed the offer. A founding row seats by the signatures on it: a listed key's acceptance by a row of its own
/// does not seat it (CC 3.1.3.2, `membership_founding_member_unsigned`).
#[test]
fn an_offer_seating_many_seats_exactly_its_consenting_keys() {
    let law = law();
    let mut g = Lcg(41);
    let (mut cases, mut bad) = (0usize, 0usize);
    for _ in 0..2_000 {
        let n = 1 + pick(&mut g, 20) as u32;
        let mut o = S::new(0, Vec::new(), 1, SeatKind::Offer);
        o.to = (1..=n).collect();
        o.scope = Some("member".into());
        o.obj = Some(Obj::Row(0));
        o.conf = Some(Conf::Own);
        o.cosigners = (2..=n).filter(|_| pick(&mut g, 2) == 0).collect();
        let mut rows = vec![o.clone()];
        let want: BTreeSet<u32> = o.cosigners.iter().copied().chain([1]).collect();
        for k in 2..=n {
            if pick(&mut g, 3) == 0 {
                let mut a = S::new(100 + k, vec![0], k, SeatKind::Accept);
                a.of = Some(0);
                rows.push(a);
            }
        }
        let c = conclude(rows.iter(), |p| seat_rule(p, &law, &NoCut, &|_| true), None);
        let got = ciris_kernel::seat::Seats::new(&c, &law, &NoCut, None).holders("member", &Obj::Row(0), None);
        cases += 1;
        bad += (got != want) as usize;
    }
    report("one offer seating many: its consenting keys", cases, bad);
    assert_eq!(bad, 0);
}

/// `line::settle` as first written: an act of the reader's line is live when the live list contains it.
fn settle_before<L: ciris_kernel::line::LineSpec<S>>(
    c: &Concluded<'_, S>,
    spec: &L,
    obj: &L::Obj,
    own: Option<&u32>,
    cut_counts: impl Fn(usize) -> bool,
) -> BTreeSet<usize> {
    use ciris_kernel::line::{counted_acts, own_line};
    let older = |heads: &[u32], than: &[u32]| {
        !heads.is_empty() && heads.iter().all(|h| than.iter().any(|t| c.g.idx(t).is_some_and(|t| c.g.id_in_past(h, t))))
    };
    let acts = counted_acts(c, spec, obj);
    let line: BTreeSet<&u32> = acts.iter().map(|&i| c.g.row(i).id()).collect();
    let mut live: Vec<usize> = acts.iter().copied().filter(|&i| cut_counts(i)).collect();
    live.sort_by_key(|&i| c.g.level(i));
    let mine: BTreeSet<usize> = own_line(c, spec, own, obj).into_iter().filter(|i| live.contains(i)).collect();
    let heads = |i: usize| spec.counted_act(c.g.row(i)).map(|(_, h)| h).unwrap_or(&[]);
    let behind =
        |r: usize, m: usize| m != r && c.g.concurrent(r, m) && older(heads(r), std::slice::from_ref(c.g.row(m).id()));
    let mut out: BTreeSet<usize> = BTreeSet::new();
    let mut out_ids: BTreeSet<&u32> = BTreeSet::new();
    for &r in &live {
        let built_ok = heads(r).iter().filter(|h| line.contains(h)).all(|h| out_ids.contains(h));
        if mine.contains(&r) || (built_ok && !mine.iter().any(|&m| behind(r, m))) {
            out.insert(r);
            out_ids.insert(c.g.row(r).id());
        }
    }
    out
}

/// A group's ledger with forks, a reader's acknowledgements of some acts, and the cut letting a random subset
/// count: `line::settle` answers as first written, for that reader and for none.
#[test]
fn settle_equals_the_settle_it_replaced() {
    use ciris_kernel::seat::SeatLine;
    let mut g = Lcg(51);
    let (mut cases, mut bad) = (0usize, 0usize);
    for _ in 0..6_000 {
        let mut f = S::new(0, Vec::new(), 1, SeatKind::Offer);
        f.to = vec![1];
        f.obj = Some(Obj::Row(0));
        f.conf = Some(Conf::Own);
        let mut rows = vec![f];
        let m = 1 + pick(&mut g, 9) as u32;
        for i in 1..=m {
            // each act at the head of one or two earlier rows: a chain with forks
            let mut heads: Vec<u32> = (0..1 + pick(&mut g, 2)).map(|_| pick(&mut g, i as u64) as u32).collect();
            heads.sort_unstable();
            heads.dedup();
            let mut a = S::new(i, heads.clone(), 1 + pick(&mut g, 3) as u32, SeatKind::Offer);
            a.obj = Some(Obj::Row(0));
            a.conf = Some(Conf::Group);
            a.head = heads;
            rows.push(a);
        }
        for j in 0..pick(&mut g, 3) as u32 {
            let h = 1 + pick(&mut g, m as u64) as u32;
            let mut k = S::new(100 + j, vec![h], if pick(&mut g, 4) == 0 { 8 } else { 7 }, SeatKind::Ack);
            k.room = Some(Obj::Row(0));
            k.head = vec![h];
            rows.push(k);
        }
        let c = conclude(rows.iter(), |_| true, None);
        let counts: Vec<bool> = (0..c.g.len()).map(|_| pick(&mut g, 4) != 0).collect();
        for own in [None, Some(7u32)] {
            let cut = |i: usize| counts[i];
            cases += 1;
            bad += (ciris_kernel::line::settle(&c, &SeatLine, &Obj::Row(0), own.as_ref(), cut)
                != settle_before(&c, &SeatLine, &Obj::Row(0), own.as_ref(), cut)) as usize;
        }
    }
    report("line::settle against the settle it replaced", cases, bad);
    assert_eq!(bad, 0);
}

/// A group with member and founder seats (some offers by a key that is no own key of the group, which do not
/// conclude), two versions, leavings in a version's past or only in a counted row's, and up to four counted
/// rows over one or both versions in either order, counting either scope.
fn seat_world(g: &mut Lcg) -> Vec<S> {
    let n = 2 + pick(g, 7) as u32;
    let mut f = S::new(0, Vec::new(), 1, SeatKind::Offer);
    f.to = vec![1];
    f.scope = Some("member".into());
    f.obj = Some(Obj::Row(0));
    f.conf = Some(Conf::Own);
    let mut rows = vec![f];
    // a counted admission of one voice, the key cosigning: by 1, a member, it concludes; by 7, no member, its count
    // is not met and it does not conclude (a roster seat over a group is placed by a counted row)
    let seat = |id: u32, k: u32, scope: &str, by: u32| {
        let mut o = S::new(id, vec![0], by, SeatKind::Offer);
        o.to = vec![k];
        o.scope = Some(scope.into());
        o.obj = Some(Obj::Row(0));
        o.conf = Some(Conf::Group);
        o.head = vec![0];
        o.policy = Some("one".into());
        if k != by {
            o.cosigners = vec![k];
        }
        o
    };
    for k in 2..=n {
        // by 1, a member; or by 7, no member: that offer does not conclude
        rows.push(seat(100 + k, k, "member", if pick(g, 5) == 0 { 7 } else { 1 }));
        if pick(g, 2) == 0 {
            rows.push(seat(200 + k, k, "founder", if pick(g, 6) == 0 { 7 } else { 1 }));
        }
    }
    let (mut v1, mut v2, mut late): (Vec<u32>, Vec<u32>, Vec<u32>) = (vec![0], vec![], vec![]);
    for r in rows.iter().skip(1) {
        if pick(g, 3) == 0 {
            v2.push(r.id)
        } else {
            v1.push(r.id)
        }
    }
    for k in 2..=n {
        if pick(g, 4) != 0 {
            continue;
        }
        let t = if rows.iter().any(|r| r.id == 200 + k) && pick(g, 2) == 0 { 200 + k } else { 100 + k };
        let mut w = S::new(300 + k, vec![t], k, SeatKind::Withdraw);
        w.target = Some(t);
        rows.push(w);
        match pick(g, 3) {
            0 => v1.push(300 + k),
            1 => v2.push(300 + k),
            _ => late.push(300 + k),
        }
    }
    rows.push(S::new(1000, v1, 1, SeatKind::Other));
    v2.push(1000);
    rows.push(S::new(1001, v2, 1, SeatKind::Other));
    // cosignatures for the counted rows: at one version, both, or none; some for another row
    let mut cosigs: Vec<u32> = Vec::new();
    for i in 0..pick(g, 6) as u32 {
        let names = match pick(g, 3) {
            0 => vec![1000],
            1 => vec![1001],
            _ => vec![1000, 1001],
        };
        let mut c = S::new(1500 + i, names, 1 + pick(g, n as u64 + 1) as u32, SeatKind::Cosign);
        c.of = Some(2000 + pick(g, 5) as u32);
        rows.push(c);
        cosigs.push(1500 + i);
    }
    // a further row naming some cosignatures, so they are in a counted row's past without being named by it
    rows.push(S::new(
        1002,
        [vec![1001], cosigs.iter().copied().filter(|_| pick(g, 2) == 0).collect()].concat(),
        1,
        SeatKind::Other,
    ));
    for j in 0..1 + pick(g, 4) as u32 {
        let heads: Vec<u32> = match pick(g, 4) {
            0 => vec![1000],
            1 => vec![1001],
            2 => vec![1000, 1001],
            _ => vec![1001, 1000],
        };
        let mut names: Vec<u32> = heads.clone();
        for &x in late.iter().chain(&cosigs) {
            if pick(g, 2) == 0 {
                names.push(x);
            }
        }
        if pick(g, 2) == 0 {
            names.push(1002);
        }
        let voices: Vec<u32> = (1..=n + 1).filter(|_| pick(g, 2) == 0).collect();
        let signer = voices.first().copied().unwrap_or(99);
        let mut c = S::new(2000 + j, names, signer, if pick(g, 3) == 0 { SeatKind::Unseat } else { SeatKind::Offer });
        c.to = vec![1 + pick(g, n as u64 + 1) as u32];
        c.scope = Some("member".into());
        c.obj = Some(Obj::Row(0));
        c.conf = Some(Conf::Group);
        c.cosigners = voices.iter().copied().skip(1).collect();
        c.head = heads;
        c.policy = Some(POLICIES[pick(g, POLICIES.len() as u64) as usize].0.into());
        c.counted = Some(if pick(g, 2) == 0 { "founder".into() } else { "member".into() });
        c.need = Some(pick(g, n as u64 + 1) as usize);
        rows.push(c);
    }
    rows
}

/// members_at reads only the concluded rows of the row's past (as members_in over them does), for every
/// scope at once as for each alone; count_members is members_at less the leavings in the row's past; and
/// seat::conclude, which reads the members at a head once per pass, concludes as the seat rule does.
#[test]
fn members_at_a_head_as_the_rows_give_them() {
    use ciris_kernel::seat::{self, count_members, left_in_past, members_at, members_in, members_in_scopes};
    let law = law();
    let mut g = Lcg(61);
    let (cases, bad) = (std::cell::Cell::new(0usize), std::cell::Cell::new(0usize));
    let cmp = |ok: bool| {
        cases.set(cases.get() + 1);
        bad.set(bad.get() + (!ok) as usize);
    };
    let mut unconcluded = 0usize;
    for _ in 0..3_000 {
        let rows = seat_world(&mut g);
        let obj = Obj::Row(0);
        let plain = conclude(
            rows.iter(),
            |p| {
                let r = p.row();
                if r.conf == Some(Conf::Group) {
                    let mine: Vec<&S> = p.rows().collect();
                    let past = |a: &u32, b: &u32| p.past(a, b);
                    let scopes = ["member", "founder"];
                    let each: Vec<BTreeSet<u32>> =
                        scopes.iter().map(|s| members_at(p, &law, &NoCut, &obj, &r.head, s)).collect();
                    for (s, m) in scopes.iter().zip(&each) {
                        cmp(*m == members_in(&mine, &past, &law, &NoCut, &obj, &r.head, s));
                    }
                    cmp(members_in_scopes(&mine, &past, &law, &NoCut, &obj, &r.head, &scopes) == each);
                    let counted = r.counted.as_deref().unwrap_or("member");
                    let mut want = members_at(p, &law, &NoCut, &obj, &r.head, counted);
                    for k in left_in_past(p, &obj, counted) {
                        want.remove(&k);
                    }
                    cmp(count_members(p, &law, &NoCut) == want);
                    cmp(seat::voices(r, p) == voices_before(r, p));
                }
                seat_rule(p, &law, &NoCut, &|_| true)
            },
            None,
        );
        let cached = seat::conclude(rows.iter(), &law, &NoCut, &|_| true, None);
        cmp(plain.all() == cached.all());
        unconcluded += plain.all().iter().filter(|c| !**c).count();
    }
    assert!(unconcluded > 1_000, "the worlds hold rows that do not conclude");
    report("members at a head, count_members and seat::conclude against the rows", cases.get(), bad.get());
    assert_eq!(bad.get(), 0);
}

/// A further voice never lowers a weighted count (`SeatCount.weighted_mono`), however large the weights.
#[test]
fn a_further_voice_never_unmeets_a_weighted_count() {
    let mem: BTreeSet<u32> = [1, 2, 3].into_iter().collect();
    let w = |k: &u32| match k {
        1 => u64::MAX,
        2 => 1,
        _ => u64::MAX / 2,
    };
    let (mut cases, mut bad) = (0usize, 0usize);
    for need in [1, usize::MAX / 2, usize::MAX] {
        let mut voices: BTreeSet<u32> = BTreeSet::new();
        let mut was = false;
        for k in [1, 2, 3] {
            voices.insert(k);
            let c = GroupCount {
                policy: Some(Policy::Weighted),
                offer: true,
                to: &[],
                members: &mem,
                voices: &voices,
                need: Some(need),
            };
            let now = group_count(&c, w).expect("weighted is a count");
            cases += 1;
            bad += (was && !now) as usize;
            was = now;
        }
        cases += 1;
        bad += !was as usize; // every weight together meets any threshold
    }
    report("a weighted count with a further voice", cases, bad);
    assert_eq!(bad, 0);
}

/// `group_count` is `None` for a ranked count only; any other policy, or none, is a count.
#[test]
fn group_count_is_none_for_ranked_only() {
    let mem: BTreeSet<u32> = [1, 2].into_iter().collect();
    let c = |policy| GroupCount { policy, offer: true, to: &[], members: &mem, voices: &mem, need: Some(1) };
    assert_eq!(group_count(&c(Some(Policy::Ranked)), |_| 1), None);
    assert_eq!(group_count(&c(None), |_| 1), Some(false));
    for (_, p) in POLICIES {
        assert!(group_count(&c(Some(*p)), |_| 1).is_some());
    }
}

/// `seat::voices` as first written: every row of the past read for a cosignature the row names.
fn voices_before(r: &S, p: &ciris_kernel::layers::Past<'_, '_, S>) -> BTreeSet<u32> {
    let heads: BTreeSet<&u32> = r.head().iter().collect();
    let content = r.content().unwrap_or(r.id());
    let mut v: BTreeSet<u32> = r.cosigners().iter().copied().collect();
    v.insert(r.signer);
    for c in p.rows() {
        if c.seat_kind() == SeatKind::Cosign
            && c.of() == Some(content)
            && r.names().contains(c.id())
            && heads.iter().all(|h| c.names().contains(*h))
        {
            v.insert(c.signer);
        }
    }
    v
}
