//! 0.3, slice 3 of issue #4 (`HELD.md`): answers read at a held row equal the `now` forms at that row's
//! instant; a recording `Past` logs what a rule reads; a conclusion is unchanged by rows outside its read set;
//! registered reads wake exactly the answers a new row touches; and a read no row can carry is reported.
#[path = "common/dag.rs"]
mod dag;

use ciris_kernel::cut::CutSpec;
use ciris_kernel::head::{self, Entry, Kind, Reading};
use ciris_kernel::held::{AnswerId, Held, HeldSpec, Reads, Rules};
use ciris_kernel::key_end::{self, EndRule, KeyEndRow, Record};
use ciris_kernel::layers::{self, Past};
use ciris_kernel::seat::{Conf, Obj, SeatKind, SeatLaw, SeatRow, Seats};
use ciris_kernel::{Dated, Row};
use dag::{dag, N};
use std::collections::{BTreeMap, BTreeSet};

/// A row with seat, key-end and signed-instant fields.
#[derive(Clone, Debug)]
struct T {
    id: u32,
    names: Vec<u32>,
    signer: u32,
    kind: SeatKind,
    to: Vec<u32>,
    obj: Option<Obj<u32, u32>>,
    cosigners: Vec<u32>,
    target: Option<u32>,
    at: Option<i64>,
    until: Option<i64>,
    rec: bool,
}

impl T {
    fn plain(id: u32, names: Vec<u32>, signer: u32, at: i64) -> T {
        T {
            id,
            names,
            signer,
            kind: SeatKind::Other,
            to: vec![],
            obj: None,
            cosigners: vec![],
            target: None,
            at: Some(at),
            until: None,
            rec: false,
        }
    }
}

impl Row for T {
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

const OWNER: &str = "owner";

impl SeatRow for T {
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
        match self.kind {
            SeatKind::Offer => Some(owner_word()),
            _ => None,
        }
    }
    fn obj(&self) -> Option<Obj<u32, u32>> {
        self.obj.clone()
    }
    fn conf(&self) -> Option<Conf> {
        match self.kind {
            SeatKind::Offer => Some(Conf::Own),
            _ => None,
        }
    }
    fn cosigners(&self) -> &[u32] {
        &self.cosigners
    }
    fn target(&self) -> Option<&u32> {
        self.target.as_ref()
    }
}

fn owner_word() -> &'static String {
    use std::sync::OnceLock;
    static W: OnceLock<String> = OnceLock::new();
    W.get_or_init(|| OWNER.to_string())
}

impl KeyEndRow for T {
    type T = i64;
    fn record(&self) -> Option<Record<'_, u32, i64>> {
        if !self.rec {
            return None;
        }
        Some(Record {
            key: &self.signer,
            from: self.at.unwrap(),
            until: self.until,
            succ_of: None,
            at_old: None,
            sigs: &[],
            end: EndRule::Optional,
        })
    }
}

impl Dated for T {
    type Instant = i64;
    fn asserted_at(&self) -> Option<i64> {
        self.at
    }
    fn valid_until(&self) -> Option<i64> {
        self.until
    }
}

struct NoCut;
impl CutSpec<T> for NoCut {
    type Slot = u32;
    type Say = ();
    fn key_slot(&self, k: &u32) -> u32 {
        *k
    }
    fn on_slots(&self, r: &T) -> BTreeSet<u32> {
        std::iter::once(r.signer).collect()
    }
    fn cuts_of(&self, _r: &T) -> BTreeSet<u32> {
        BTreeSet::new()
    }
    fn says(&self, _r: &T) {}
}

const NODE: u32 = 1_000;

/// Owner bindings over the node's key: offer `i` seats owner `i`, stated at `10 i`, some ending at `10 i + 25`;
/// one withdrawn by its owner; and probe rows (plain) stated at every fifth instant, to read at.
fn owners() -> (Vec<T>, Vec<u32>) {
    let mut rows = Vec::new();
    for i in 0..6u32 {
        rows.push(T {
            id: 100 + i,
            names: vec![],
            signer: NODE,
            kind: SeatKind::Offer,
            to: vec![i],
            obj: Some(Obj::Key(NODE)),
            cosigners: vec![i],
            target: None,
            at: Some(10 * i as i64),
            until: if i % 2 == 0 { Some(10 * i as i64 + 25) } else { None },
            rec: false,
        });
    }
    rows.push(T {
        id: 200,
        names: vec![103],
        signer: 3,
        kind: SeatKind::Withdraw,
        to: vec![],
        obj: None,
        cosigners: vec![],
        target: Some(103),
        at: Some(55),
        until: None,
        rec: false,
    });
    let mut probes = Vec::new();
    for t in (0..90).step_by(5) {
        let id = 300 + t as u32;
        rows.push(T::plain(id, vec![], 7, t));
        probes.push(id);
    }
    (rows, probes)
}

fn law() -> SeatLaw {
    SeatLaw { roster_seats: vec!["member".into()], depth: 1, ..Default::default() }
}

#[test]
fn holders_at_equals_holders_over_the_offers_standing_at_that_instant() {
    let (rows, probes) = owners();
    let law = law();
    let c = layers::conclude(rows.iter(), |_| true, None);
    let s = Seats::new(&c, &law, &NoCut, None);
    for &p in &probes {
        let t = c.g.instant_of(&p).unwrap();
        // the now form, as persist reads it today: drop every binding not standing at t, then read
        let at_t: Vec<T> = rows
            .iter()
            .filter(|r| r.kind != SeatKind::Offer || ciris_kernel::covers_at(r.at, r.until, &t))
            .cloned()
            .collect();
        let ct = layers::conclude(at_t.iter(), |_| true, None);
        let st = Seats::new(&ct, &law, &NoCut, None);
        let want = st.holders(OWNER, &Obj::Key(NODE), None);
        assert_eq!(s.holders_at(OWNER, &Obj::Key(NODE), None, &p), Some(want.clone()), "at {t}");
        for k in 0..8u32 {
            assert_eq!(
                s.stands_at(&k, OWNER, &Obj::Key(NODE), None, &p),
                Some(st.stands(&k, OWNER, &Obj::Key(NODE), None)),
                "key {k} at {t}"
            );
        }
    }
    // a row not held, or held with no instant, reads nothing
    assert_eq!(s.holders_at(OWNER, &Obj::Key(NODE), None, &9_999), None);
}

#[test]
fn key_end_at_a_row_is_key_end_at_its_instant() {
    let mut rows = vec![
        T { rec: true, until: Some(40), ..T::plain(1, vec![], 50, 10) },
        T { rec: true, until: None, ..T::plain(2, vec![], 51, 30) },
    ];
    for t in (0..70).step_by(5) {
        rows.push(T::plain(400 + t as u32, vec![], 9, t));
    }
    let c = layers::conclude(rows.iter(), key_end::conclude_rule, None);
    for t in (0..70).step_by(5) {
        let at = 400 + t as u32;
        for k in [50u32, 51] {
            assert_eq!(key_end::live_at(&c, &k, &at), Some(key_end::live(&c, &k, t)));
            assert_eq!(key_end::ended_at(&c, &k, &at), Some(key_end::ended(&c, &k, t)));
        }
        assert_eq!(key_end::retained_at(&c, &at), Some(key_end::retained(&c, t)));
    }
    assert_eq!(key_end::live_at(&c, &50, &12_345), None);
}

#[test]
fn a_view_at_a_row_is_the_view_at_its_instant() {
    let mut store: head::Store<u32, u32, i64> = BTreeMap::new();
    let mut open = Entry::new(1u32, Kind::Open, 1u32, vec![]).with_at(0);
    open.length = Some(20);
    open.receipt = Some(5);
    store.insert(1, open);
    for t in (0..60).step_by(5) {
        let id = 100 + t as u32;
        store.insert(id, Entry::new(id, Kind::Act, 2u32, vec![1]).with_at(t));
    }
    let v = head::View::new(&store, &[], 0u32, Reading::Broad, true);
    for t in (0..60).step_by(5) {
        let at = 100 + t as u32;
        assert_eq!(v.window_at(&1, &at), Some(v.window(&1, t)));
        assert_eq!(v.answers_at(&at), Some(v.answers(t)));
    }
    let mut no_at = store.clone();
    no_at.insert(999, Entry::new(999, Kind::Act, 2u32, vec![1]));
    let v = head::View::new(&no_at, &[], 0u32, Reading::Broad, true);
    assert_eq!(v.window_at(&1, &999), None, "an entry with no instant reads nothing");
}

fn parity(p: &Past<'_, '_, N>) -> bool {
    let me = p.row().signer;
    p.rows().filter(|r| r.signer == me).count().is_multiple_of(2)
}

#[test]
fn a_recording_past_logs_what_the_rule_reads_within_the_sound_set() {
    let rows = dag(300, 3, 20, 5);
    let h = Held::new(Rules { wf: |_: &N| true, rule: parity }, rows.iter());
    for r in &rows {
        let sound = h.reads_of(&r.id).unwrap();
        let l = h.recorded_reads(&r.id).unwrap();
        let (rec, complete) = (l.reads, l.complete);
        assert!(complete, "parity reads only through methods");
        assert!(rec.ids().iter().all(|i| sound.reads_id(i)), "the log is within the sound set");
        assert!(rec.reads_id(&r.id), "the rule read its own row");
    }
    // a rule that takes the whole graph escapes the log
    let esc = Held::new(
        Rules { wf: |_: &N| true, rule: |p: &Past<'_, '_, N>| p.graph().len().is_multiple_of(2) || p.row().id == 0 },
        rows.iter(),
    );
    assert!(!esc.recorded_reads(&rows[100].id).unwrap().complete);
}

#[test]
fn a_conclusion_is_unchanged_by_rows_outside_its_reads() {
    let rows = dag(400, 3, 30, 11);
    let full = Held::new(Rules { wf: |_: &N| true, rule: parity }, rows.iter());
    for r in rows.iter().step_by(7) {
        // keep only the row and its past: every row outside its reads (descendants, concurrent rows) gone
        let g = &full.concluded().g;
        let i = g.idx(&r.id).unwrap();
        let keep: BTreeSet<u32> = g.past(i, true).into_iter().map(|q| g.row(q).id).collect();
        let reads = full.reads_of(&r.id).unwrap();
        assert!(reads.ids().iter().all(|x| keep.contains(x)));
        let sub: Vec<N> = rows.iter().filter(|x| keep.contains(&x.id)).cloned().collect();
        let small = Held::new(Rules { wf: |_: &N| true, rule: parity }, sub.iter());
        assert_eq!(small.concluded_id(&r.id), full.concluded_id(&r.id), "row {}", r.id);
    }
}

/// Rows carry their signer as a key, and only keys below 100 can be carried.
#[derive(Clone, Copy)]
struct Keyed;
impl HeldSpec<N> for Keyed {
    fn well_formed(&self, _r: &N) -> bool {
        true
    }
    fn conclude(&self, _p: &Past<'_, '_, N>) -> bool {
        true
    }
    fn keys(&self, r: &N) -> Vec<u32> {
        vec![r.signer]
    }
    fn can_carry(&self, k: &u32) -> bool {
        *k < 100
    }
}

#[test]
fn registered_reads_wake_exactly_the_answers_a_new_row_touches() {
    let rows = dag(50, 2, 10, 3);
    let mut h = Held::new(Keyed, rows.iter());
    let a = h.register(Reads::of([10u32], []));
    let b = h.register(Reads::of([], [7u32]));
    let c = h.register(Reads::of([20u32, 21], [500u32]));
    // a new row naming 10, signed by 7: wakes a (its name) and b (its key), not c
    let x = N { id: 50, names: vec![10, 49], signer: 7 };
    let got = h.admit(&x).unwrap();
    assert_eq!(got.wake, vec![a, b]);
    assert_eq!(got.dirty, vec![50], "the concluded layer's dirty set is unchanged");
    // a row naming 21, by key 3: wakes c only
    let y = N { id: 51, names: vec![21], signer: 3 };
    assert_eq!(h.admit(&y).unwrap().wake, vec![c]);
    // re-registered with other reads, and forgotten
    assert!(h.update(a, Reads::of([30u32], [])));
    let z = N { id: 52, names: vec![10], signer: 4 };
    assert_eq!(h.admit(&z).unwrap().wake, Vec::<AnswerId>::new());
    assert!(h.unregister(b).is_some());
    let w = N { id: 53, names: vec![30], signer: 7 };
    assert_eq!(h.admit(&w).unwrap().wake, vec![a]);
    // the by-name index
    assert_eq!(h.named_by(&10), {
        let mut v: Vec<&u32> = rows.iter().filter(|r| r.names.contains(&10)).map(|r| &r.id).collect();
        v.push(&50);
        v.push(&52);
        v.sort();
        v
    });
    // a waiting row wakes nothing until it is kept; then the row it waited on and it wake their readers
    let d = h.register(Reads::of([61u32], []));
    let late = N { id: 61, names: vec![60], signer: 7 };
    let got = h.admit(&late).unwrap();
    assert!(got.waiting && got.wake.is_empty());
    let first = N { id: 60, names: vec![], signer: 8 };
    let got = h.admit(&first).unwrap();
    assert_eq!(got.kept, vec![60, 61]);
    assert_eq!(got.wake, vec![d]);
}

#[test]
fn a_read_no_row_can_carry_is_reported() {
    let rows = dag(10, 1, 1, 1);
    let mut h = Held::new(Keyed, rows.iter());
    let ok = h.register(Reads::of([], [7u32]));
    let bad = h.register(Reads::of([1u32], [500u32, 900]));
    assert_eq!(h.unwritable(), vec![(bad, 500), (bad, 900)]);
    let _ = ok;
    h.unregister(bad);
    assert!(h.unwritable().is_empty());
}

#[test]
fn the_differential_still_holds() {
    let rows = dag(120, 3, 16, 9);
    ciris_kernel::held::differential(Rules { wf: |_: &N| true, rule: parity }, &rows).unwrap();
    ciris_kernel::held::differential(Keyed, &rows).unwrap();
}
