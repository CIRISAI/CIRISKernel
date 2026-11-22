//! # ciris-kernel
//!
//! The CIRIS causal kernel (`kernel/KERNEL.md`; CC 2.7 "The kernel") as pure functions over an abstract
//! row graph. A node gives it the rows it holds or has been offered, the present instant where an answer
//! reads one, and its own key. It returns what the rows conclude. There is no I/O, no clock, no
//! cryptography and no serialisation here: signature verification, decoding, storage and transport are the
//! caller's.
//!
//! The caller supplies rows through [`Row`] (id, the ids it names, its signer) and, for each answer, the
//! fields that answer reads, as small spec traits or closures. Ties are refused, never broken by position.
//!
//! | Module | KERNEL.md | What |
//! |---|---|---|
//! | [`ops`] | 4 | select, group and reduce, interval, table cell, bounded repeat |
//! | [`graph`] | 2, 4 | the closure over what rows name: past, concurrency, frontier |
//! | [`layers`] | 3 | kept (the monotone door) and concluded |
//! | [`derived`] | 5, 6 | the order on kinds, the slot, removal by causal past, reach, tally |
//! | [`cut`] | 6 | the cut, by the well-founded fixed point |
//! | [`line`] | 7, 8a | built on, and the reader's own acknowledged line |
//! | [`seat`] | 5 (stands), 7 | the seat: two consents, the bounded walk, members at a head, tips wait |
//! | [`window`] | 5 (window) | a window as rows: receipt, landing and recount |
//! | [`head`] | 3, 3a | answers by head: receipts, one say, settled, missing; checkpoint and purge |
//! | [`held`] | 3 | the two layers held across admissions: one row admitted at a time, only what it releases recomputed |
//! | [`key_end`] | 5 (two notions of time) | a key's own end and the rows that lapse |
//! | [`trust`] | 5 (stands), CC 4.4.3.34 | the reader's trust walk over acceptance edges |
//! | [`ranked`] | 5 (the door's parameters) | the ranked count, with and without a declared order |
#![no_std]
#![forbid(unsafe_code)]
#![warn(missing_docs)]

extern crate alloc;

pub mod cut;
pub mod derived;
pub mod graph;
pub mod head;
pub mod held;
pub mod key_end;
pub mod layers;
pub mod line;
pub mod ops;
pub mod ranked;
pub mod seat;
pub mod trust;
pub mod window;

/// A signed row, as the kernel reads it: its digest, the digests it names, and the key that signed it.
/// The caller has verified the signature and decoded the bytes; the kernel never hashes or verifies.
pub trait Row {
    /// The row's digest (persist: `RowId`, `persist_row_hash`).
    type Id: Ord + Clone + core::fmt::Debug;
    /// A key id.
    type Key: Ord + Clone + core::fmt::Debug;
    /// The row's own digest.
    fn id(&self) -> &Self::Id;
    /// The digests it names: the row it answers, the head it extends, the proposal it votes on.
    fn names(&self) -> &[Self::Id];
    /// The key that signed it.
    fn signer(&self) -> &Self::Key;
}

/// A row's signed instants, for the answers read **at a held row** (the `_at` forms: [`seat::Seats::holders_at`],
/// [`key_end::live_at`], [`head::View::window_at`], ...). An answer read at a row takes its instant from that
/// row, never from a clock, so two nodes holding the same rows give the same answer (CC 2.7.9: a reading at a
/// node's own present binds only that node).
pub trait Dated: Row {
    /// An instant (persist: `Micros`).
    type Instant: Ord + Copy;
    /// The instant the row's signer states for it (persist: `asserted_at`), when it states one.
    fn asserted_at(&self) -> Option<Self::Instant>;
    /// The instant the row's standing ends, when it states one (persist: `expires_at`, `valid_until`).
    fn valid_until(&self) -> Option<Self::Instant> {
        None
    }
}

/// Whether a row stated from `from` until `until` covers `t`: `from <= t < until`, half-open; a missing bound
/// does not limit.
pub fn covers_at<T: Ord>(from: Option<T>, until: Option<T>, t: &T) -> bool {
    from.is_none_or(|f| f <= *t) && until.is_none_or(|u| *t < u)
}
