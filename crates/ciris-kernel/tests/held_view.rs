//! `held_view`: the head layer held across admissions answers as `head::View::new` over the prefix after every
//! admission, in order, reversed and shuffled (`held_view::differential`), over `purge.json`'s histories and over
//! stores generated on `tests/common/dag.rs`; a refusal changes nothing; the checkpoint resumes to the view it
//! came from, canonically; and the work of one admission is counted, not proportional to the store.
mod common;
#[path = "common/dag.rs"]
mod dag;

use ciris_kernel::head::{purge, Entry, Kind, Reading, Store, View};
use ciris_kernel::held::Refused;
use ciris_kernel::held_view::{differential, CheckpointError, HeldView, CHECKPOINT_VERSION};
use common::*;
use dag::{dag, Lcg};
use std::collections::BTreeMap;

type E = Entry<u32, u32, i64>;

fn shuffled<X: Clone>(v: &[X], seed: u64) -> Vec<X> {
    let mut v = v.to_vec();
    let mut g = Lcg(seed);
    for i in (1..v.len()).rev() {
        v.swap(i, (g.next() as usize) % (i + 1));
    }
    v
}

fn orders<X: Clone>(v: &[X]) -> Vec<Vec<X>> {
    let mut r = v.to_vec();
    r.reverse();
    vec![v.to_vec(), r, shuffled(v, 1), shuffled(v, 2)]
}

/// A store of every kind over `dag(n, k, w, seed)`'s names: roster versions (some above 32 members), acts at
/// them, receipts and cuts, the reader's acknowledgements, windows and answers. Most entries name the head they
/// are at; `far` in 8 do not (an act at a head it does not name, a reader acknowledging a head it does not
/// name), which takes the view's whole-void path.
fn gen(n: u32, k: u32, w: u32, seed: u64, far: u64) -> Vec<E> {
    let mut g = Lcg(seed ^ 0x9e37);
    let pick = |g: &mut Lcg, v: &[u32]| v[(g.next() as usize) % v.len()];
    let (mut seats, mut acts, mut opens): (Vec<u32>, Vec<u32>, Vec<u32>) = (vec![], vec![], vec![]);
    let mut out: Vec<E> = Vec::new();
    for d in dag(n, k, w, seed) {
        let i = d.id;
        let mut names = d.names.clone();
        let kind = match g.next() % 10 {
            _ if seats.is_empty() => Kind::Seat,
            0 | 1 => Kind::Seat,
            2 | 3 => Kind::Act,
            4 if !acts.is_empty() => Kind::Ack,
            5 if !acts.is_empty() => Kind::Cut,
            6 => Kind::ReaderAck,
            7 => Kind::Open,
            8 if !opens.is_empty() => Kind::Answer,
            _ => Kind::Other,
        };
        let mut e = Entry::new(i, kind, (g.next() % 12) as u32, vec![]);
        let named = g.next() % 8 >= far;
        match kind {
            Kind::Seat => {
                let m = if g.next().is_multiple_of(3) { 33 + g.next() % 8 } else { g.next() % 8 };
                e.members = (0..m as u32).collect();
                e.q = 1 + (g.next() % (1 + m / 2)) as usize;
                seats.push(i);
            }
            Kind::Act | Kind::ReaderAck => {
                // a head at or after this one when not named: it may arrive later
                let h = if named { pick(&mut g, &seats) } else { (i + 1 + (g.next() as u32 % 4)).min(n - 1) };
                e.head = Some(h);
                if named {
                    names.push(h);
                }
                if kind == Kind::Act {
                    acts.push(i);
                } else if g.next().is_multiple_of(2) {
                    e.signer = [0, 3, 5][(g.next() % 3) as usize]; // a reader's own acknowledgement
                }
            }
            Kind::Ack | Kind::Cut => {
                let a = pick(&mut g, &acts);
                e.of = Some(a);
                if kind == Kind::Ack && !g.next().is_multiple_of(4) {
                    names.push(a);
                }
                if kind == Kind::Cut {
                    let h = out[a as usize].head.unwrap();
                    let h = if g.next().is_multiple_of(2) && h < i { h } else { pick(&mut g, &seats) };
                    e.head = Some(h);
                    names.push(h);
                    e.sigs = (0..g.next() % 6).map(|_| (g.next() % 12) as u32).collect();
                }
            }
            Kind::Open => {
                e.length = Some(10 + (g.next() % 40) as i64);
                e.receipt = Some((g.next() % 30) as i64);
                opens.push(i);
            }
            Kind::Answer => names.push(pick(&mut g, &opens)),
            _ => {}
        }
        names.sort_unstable();
        names.dedup();
        e.names = names;
        out.push(e);
    }
    out
}

fn readers() -> [(Reading, bool, u32); 3] {
    [(Reading::Broad, true, 0), (Reading::Narrow, false, 3), (Reading::Broad, false, 5)]
}

/// The view's own entries, with every stub field reset: the row content a caller's store gives back.
fn content<I: Clone, K, T: Clone>(e: &Entry<I, K, T>) -> Entry<I, K, T>
where
    K: Clone,
{
    let mut e = e.clone();
    e.stub = false;
    e.concl = false;
    e.final_counts = None;
    e.settled_stub = false;
    e.ackers = Vec::new();
    e.acks = Vec::new();
    e.dropped = false;
    e
}

/// A view resumes from its checkpoint to itself, and writes the same bytes again.
fn round_trip(h: &HeldView<u32, u32, i64>, all: &BTreeMap<u32, E>) {
    let cp = h.checkpoint();
    let back = HeldView::resume(&cp, |i| all.get(i).map(content)).expect("resumes");
    assert!(back == *h, "resume(checkpoint) is the view it came from");
    assert_eq!(back.checkpoint(), cp);
}

#[test]
fn generated_stores_equal_the_view_after_every_admission() {
    let nows = [0i64, 25, 80];
    let mut cases = 0;
    for (n, k, w, seed, far) in [(40, 2, 8, 1, 0), (90, 3, 16, 2, 1), (120, 2, 40, 3, 2), (80, 4, 80, 4, 0)] {
        let es = gen(n, k, w, seed, far);
        let all: BTreeMap<u32, E> = es.iter().map(|e| (e.id, e.clone())).collect();
        for (reading, say, own) in readers() {
            for o in orders(&es) {
                differential(&Store::new(), own, reading, say, &o, &nows).unwrap();
                cases += 1;
            }
            // half as a store, the rest offered
            let half: Store<u32, u32, i64> = es[..es.len() / 2].iter().map(|e| (e.id, e.clone())).collect();
            for o in orders(&es[es.len() / 2..]) {
                differential(&half, own, reading, say, &o, &nows).unwrap();
            }
            // and every prefix's checkpoint
            let mut h = HeldView::empty(own, reading, say);
            for e in shuffled(&es, 9) {
                let _ = h.admit(e);
                round_trip(&h, &all);
            }
            // a purged store resumes with its whole rows re-attached (a stub's signatures dropped)
            let whole: Store<u32, u32, i64> = es.iter().map(|e| (e.id, e.clone())).collect();
            let v = View::new(&whole, &[], own, reading, say);
            let cut = purge(v.rec(), own, 30, reading).0;
            let p = HeldView::new(&cut, own, reading, say);
            round_trip(&p, &all);
            for (o, e) in [(&p, &cut), (&HeldView::new(v.rec(), own, reading, say), v.rec())] {
                assert_eq!(o.view().answers(30), View::new(e, &[], own, reading, say).answers(30));
            }
        }
    }
    assert!(cases > 0);
}

#[test]
fn purge_histories_equal_the_view_after_every_admission() {
    let fx = fixture("purge.json");
    let (mut cases, mut bad) = (0usize, 0usize);
    for hst in fx.arr() {
        let reading = if hst.at("reading").s() == "broad" { Reading::Broad } else { Reading::Narrow };
        let own = hst.at("own").s().to_string();
        let now0 = hst.at("now").i();
        let nows: Vec<i64> = hst.at("nows").arr().iter().map(|t| t.i()).collect();
        let rows: Vec<Entry<String, String, i64>> = hst.at("rows").arr().iter().map(head_entry).collect();
        let pool: Vec<Entry<String, String, i64>> = hst.at("pool").arr().iter().map(head_entry).collect();
        let base: Store<String, String, i64> = rows.iter().map(|e| (e.id.clone(), e.clone())).collect();
        let first = purge(&base, own.clone(), now0, reading).0;
        let mut every = rows.clone();
        every.extend(pool.iter().cloned());
        let all: BTreeMap<String, Entry<String, String, i64>> =
            every.iter().map(|e| (e.id.clone(), e.clone())).collect();
        for say in [true, false] {
            for o in orders(&every) {
                cases += 1;
                bad += differential(&Store::new(), own.clone(), reading, say, &o, &nows).is_err() as usize;
            }
            for store in [&base, &first] {
                for o in orders(&pool) {
                    cases += 1;
                    bad += differential(store, own.clone(), reading, say, &o, &nows).is_err() as usize;
                    // resumed from the purged store's checkpoint, the caller's whole rows re-attached by id
                    let mut h = HeldView::new(store, own.clone(), reading, say);
                    for e in &o {
                        let _ = h.admit(e.clone());
                        let cp = h.checkpoint();
                        let back = HeldView::resume(&cp, |i| all.get(i).map(content));
                        cases += 1;
                        bad += !matches!(&back, Ok(b) if *b == h && b.checkpoint() == cp) as usize;
                    }
                }
            }
        }
    }
    report("held_view::differential over purge.json histories (in order, reversed, shuffled; resumed)", cases, bad);
    assert_eq!(bad, 0);
}

#[test]
fn a_refusal_changes_nothing_and_a_clone_answers_alike() {
    let es = gen(70, 3, 16, 5, 1);
    let mut h = HeldView::empty(0u32, Reading::Broad, true);
    h.admit_all(es.iter().cloned());
    let before = h.clone();
    for e in es.iter().take(20) {
        assert_eq!(h.admit(e.clone()), Err(Refused::Duplicate));
    }
    assert!(h == before);
    let full = View::new(&Store::new(), &es, 0u32, Reading::Broad, true);
    assert_eq!(h.view().answers(25), full.answers(25));
    assert_eq!(before.view().answers(25), full.answers(25));
    // one waiting entry, refused again while it waits
    let mut w = Entry::new(1000u32, Kind::Other, 1u32, vec![2000]);
    w.of = Some(3);
    assert!(h.admit(w.clone()).unwrap().waiting);
    let mid = h.clone();
    assert_eq!(h.admit(w), Err(Refused::Duplicate));
    assert!(h == mid && h.waits(&1000));
}

#[test]
fn the_checkpoint_is_canonical_and_refuses_what_it_is_not() {
    let es = gen(90, 3, 16, 7, 1);
    let all: BTreeMap<u32, E> = es.iter().map(|e| (e.id, e.clone())).collect();
    let mut a = HeldView::empty(0u32, Reading::Broad, true);
    let mut b = HeldView::empty(0u32, Reading::Broad, true);
    a.admit_all(es.iter().cloned());
    b.admit_all(shuffled(&es, 4));
    let cp = a.checkpoint();
    assert_eq!(cp, b.checkpoint(), "the same view gives the same bytes, whatever the order of arrival");
    assert_eq!(u16::from_be_bytes([cp[0], cp[1]]), CHECKPOINT_VERSION);
    let rows = |i: &u32| all.get(i).map(content);
    // every strict prefix ends early
    for k in 0..cp.len() {
        assert_eq!(HeldView::resume(&cp[..k], rows).err(), Some(CheckpointError::Truncated), "prefix {k}");
    }
    let mut v = cp.clone();
    v[1] ^= 0x7;
    assert!(matches!(HeldView::resume(&v, rows), Err(CheckpointError::Version(_))));
    let mut t = cp.clone();
    t.push(0);
    assert_eq!(HeldView::resume(&t, rows).err(), Some(CheckpointError::NotCanonical));
    let mut s = cp.clone();
    s[3] = 2; // say is 0 or 1
    assert_eq!(HeldView::resume(&s, rows).err(), Some(CheckpointError::NotCanonical));
    // the first entry's flags (version 2, reading 1, say 1, own 4, count 8, id 4): an unknown bit
    let mut f = cp.clone();
    f[2 + 1 + 1 + 4 + 8 + 4] |= 0x80;
    assert_eq!(HeldView::resume(&f, rows).err(), Some(CheckpointError::NotCanonical));
    // a row the caller does not supply, and one that concludes otherwise
    let gone = es[40].id;
    let r = HeldView::resume(&cp, |i| if *i == gone { None } else { all.get(i).map(content) });
    assert_eq!(r.err(), Some(CheckpointError::Missing(gone)));
    let act = es.iter().find(|e| e.kind == Kind::Act && a.view().c()[&e.id]).unwrap().id;
    let r = HeldView::resume(&cp, |i| {
        all.get(i).map(|e| {
            let mut e = content(e);
            if *i == act {
                e.signer = 999; // a member at no head
            }
            e
        })
    });
    assert_eq!(r.err(), Some(CheckpointError::Differs(act)));
}

/// One admission's work is the entries kept and the ids they name, not the store: the same count at 1,024
/// and 8,192 entries, on a store where every entry names its head (the bench asserts it at 64,000).
#[test]
fn an_admission_is_counted_by_its_cone() {
    for n in [1024u32, 8192] {
        let mut s: Store<u32, u32, i64> = BTreeMap::new();
        let mut v = Entry::new(0u32, Kind::Seat, 0u32, Vec::new());
        v.members = (0..n).collect();
        v.q = n as usize / 3 + 1;
        s.insert(0, v);
        for i in 0..n {
            let a = 1 + 2 * i;
            let mut e = Entry::new(a, Kind::Act, i, vec![0]);
            e.head = Some(0);
            s.insert(a, e);
            let mut k = Entry::new(a + 1, Kind::Ack, (i + 1) % n, vec![a]);
            k.of = Some(a);
            s.insert(a + 1, k);
        }
        let mut h = HeldView::new(&s, 0u32, Reading::Broad, true);
        // a receipt of act 1: kept, names one; dirty is it and the act it names as its own
        let mut k = Entry::new(10 * n, Kind::Ack, 5, vec![1]);
        k.of = Some(1);
        let a = h.admit(k).unwrap();
        assert_eq!(a.visited, 1 + 1, "{n}");
        assert_eq!(a.dirty, vec![1, 10 * n]);
        // a new act, and one receipt of it waiting on it: released together
        let mut r = Entry::new(10 * n + 2, Kind::Ack, 7, vec![10 * n + 1]);
        r.of = Some(10 * n + 1);
        assert!(h.admit(r).unwrap().waiting);
        let mut x = Entry::new(10 * n + 1, Kind::Act, 3, vec![0]);
        x.head = Some(0);
        let a = h.admit(x).unwrap();
        assert_eq!(a.kept, vec![10 * n + 1, 10 * n + 2]);
        assert_eq!(a.visited, (1 + 1) + (1 + 1), "{n}");
        assert_eq!(a.dirty, vec![10 * n + 1, 10 * n + 2]);
        assert_eq!(h.past_len(&(10 * n + 2)), Some(2));
    }
}

/// A head that arrives after an act at it that does not name it, and is void when it arrives: the act becomes
/// void too (it comes after the head in the fold's order), so the void set is read again whole.
#[test]
fn a_late_void_head_voids_the_act_that_did_not_name_it() {
    let seat = |id: u32, names: Vec<u32>| {
        let mut e = Entry::new(id, Kind::Seat, 9u32, names);
        e.members = vec![1];
        e.q = 1;
        e
    };
    let mut rk = Entry::new(4u32, Kind::ReaderAck, 0u32, vec![3]);
    // the reader acknowledges 3, built on 10, a fork of 2 from 1: 2's head 1 is strictly in the past of 3's own head
    // 10, so 2 is behind it and void (the line is sibling-safe: a sibling of 3 at 10 would not be)
    rk.head = Some(3);
    let mut r = Entry::new(8u32, Kind::Act, 1u32, vec![7]);
    r.head = Some(9); // its head, 9, is not named, and arrives last
    let es: Vec<E> = vec![
        seat(1, vec![]),
        seat(2, vec![1]),
        seat(10, vec![1]),
        seat(3, vec![10]),
        rk,
        Entry::new(5, Kind::Other, 2, vec![1]),
        Entry::new(6, Kind::Other, 2, vec![5]),
        Entry::new(7, Kind::Other, 2, vec![6]),
        r,
        seat(9, vec![2]), // void: it names 2
    ];
    differential(&Store::new(), 0u32, Reading::Broad, true, &es, &[0]).unwrap();
    let mut h = HeldView::empty(0u32, Reading::Broad, true);
    h.admit_all(es[..9].iter().cloned());
    assert!(!h.view().c()[&8]);
    let a = h.admit(es[9].clone()).unwrap();
    assert!(h.view().c()[&8] && h.view().v().contains(&8) && h.view().v().contains(&9));
    assert_eq!(a.dirty, vec![8, 9]);
    assert!(a.visited > h.len(), "the void set read whole is counted");
}
