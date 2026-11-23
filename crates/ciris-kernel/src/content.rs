//! Room content after a member's seat ends (CC 2.4.1.1; `models/tla/CONFERRAL_END.md`, section I).
//!
//! A content row (a message, a file placement, a reaction, an edit or a retraction of one) is an act under its
//! signer's membership. It names its roster head and its author's current newest content rows in the room, its
//! predecessors. The row that ends a member's seat names the newest rows of that member it holds good: the
//! tips. After the end, a content row of that member is in the room's content when it is a held tip or an
//! ancestor of one along its predecessors; every other row of theirs counts at its own head and is not in the
//! content. A later counted row may name further tips: tips only grow.
//!
//! [`answers`] gives, for every content row of the member among the rows: does it **count** at the head it
//! names, is it **in force** (in the room's content now), and which rule decides. The answer is a function of
//! the held rows: no instant and no arrival order is read.
//!
//! Nothing waits on content. A tip that is not held keeps nothing until it arrives, and a predecessor that is
//! not held is not followed, so what lies behind it is not kept until it arrives. The kept set only fills in.
//!
//! Whose tips are read (the reference's `count_first`):
//! * where a counted end counts, only counted rows' tips: the union over every counted end that is not stale
//!   and every counted row adding tips;
//! * the member's own ends are read only where no counted end counts, and then a row stays only where every
//!   one of them holds it good. A further resignation can take rows out and never add one;
//! * a row adding tips that the member signs is never read.
//!
//! So once an end counts, nothing the member signs afterwards puts a row into the room's content.
//!
//! An author's retraction of its own row takes effect whenever it is signed, whether or not the retraction
//! itself counts or is kept; a retraction of a retraction restores nothing. An edit is a content row like any
//! other and is kept only where a tip holds it good: it does not follow its target into the content.
//!
//! The reference is `models/causal_kernel/conferral_content.py`, checked by `check_conferral_content.py` over
//! every history to a bound. It is checked by run, not by a TLA+ model. `tests/content.rs` replays its case
//! table (`tests/fixtures/conferral_content.json`) through this module.
//!
//! Not covered: receipts together with tips, a re-admission of the member, the reader's line on an end, key
//! removals, more than one room.

use crate::conferral::Past;
use alloc::collections::{BTreeMap, BTreeSet};
use alloc::vec::Vec;
use core::fmt::Debug;

/// What a row is to the room's content and the member's seat.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Kind {
    /// A roster version.
    Head,
    /// A content row: a message, a file placement, a reaction, an edit, a retraction.
    Content,
    /// An end of the member's seat: a counted removal, or the member's own resignation.
    End,
    /// A later row naming further tips for the member.
    Tips,
    /// Any other row. It is not read.
    Other,
}

/// A row as this module reads it. The caller has verified and decoded it.
pub trait ContentRow {
    /// The row's digest.
    type Id: Ord + Clone + Debug;
    /// A key id.
    type Key: Ord + Clone + Debug;
    /// The row's own digest.
    fn id(&self) -> &Self::Id;
    /// What the row is.
    fn kind(&self) -> Kind;
    /// The key that signed it.
    fn signer(&self) -> &Self::Key;
    /// The roster head a content row or an end names (`refs.head`).
    fn head(&self) -> Option<&Self::Id>;
    /// A content row's predecessors: its author's rows it follows (`refs.prev` and any further ones).
    fn prev(&self) -> &[Self::Id] {
        &[]
    }
    /// The tips an end or a tips row holds good (`refs.trusted_through`).
    fn tips(&self) -> &[Self::Id] {
        &[]
    }
    /// The row a retraction retracts. `None` on every other row, an edit included.
    fn retracts(&self) -> Option<&Self::Id> {
        None
    }
}

/// Who signs: the member whose seat ends, and the room's count.
pub struct Seat<'a, K> {
    /// The key is one of the member's.
    pub member: &'a dyn Fn(&K) -> bool,
    /// The key is the signer of a counted row of the room (a removal, a row adding tips).
    pub counted: &'a dyn Fn(&K) -> bool,
}

/// The rule that decides a content row, in the order the rules decide. [`Rule::as_str`] is the name the
/// reference and the fixture use.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Rule {
    /// E4: the row has a counting end in its past. Not counted.
    NamesEnd,
    /// E3: the row names a head that has a counting end's head in its past. Not counted.
    LaterHead,
    /// A retraction of the row by its own key is held. Counted, not in force.
    Retracted,
    /// No end counts. Counted and in force.
    NoEnd,
    /// A held tip that is read, or its ancestor along predecessors of the same key. Counted and in force.
    HeldGood,
    /// E2: counted at its own head, not in force: not held good.
    Forward,
}

impl Rule {
    /// The rule's name in `models/causal_kernel/conferral_content.py` and the fixture.
    pub fn as_str(self) -> &'static str {
        match self {
            Rule::NamesEnd => "E4.names_end",
            Rule::LaterHead => "E3.later_head",
            Rule::Retracted => "W.retracted",
            Rule::NoEnd => "no_end",
            Rule::HeldGood => "T.held_good",
            Rule::Forward => "E2.forward",
        }
    }
}

/// What the rows conclude about one content row.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Judged {
    /// It counts at the head it names.
    pub counted: bool,
    /// It is in the room's content now.
    pub in_force: bool,
    /// The rule that decides it.
    pub rule: Rule,
}

/// The answer for one content row.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Answer<I> {
    /// The rows decide it.
    Judged(Judged),
    /// The caller's past cannot tell until it holds this row.
    Undecided(I),
}

/// The answer for every content row of the member, by the row's id.
pub type Answers<I> = BTreeMap<I, Answer<I>>;

// `any` over a three-way answer: yes if any is yes; else the first row that must be held; else no.
fn any3<T, I>(items: impl Iterator<Item = T>, mut f: impl FnMut(T) -> Result<bool, I>) -> Result<bool, I> {
    let mut need = None;
    for t in items {
        match f(t) {
            Ok(true) => return Ok(true),
            Ok(false) => {}
            Err(i) => need = need.or(Some(i)),
        }
    }
    match need {
        Some(i) => Err(i),
        None => Ok(false),
    }
}

// why an end concludes nothing
#[derive(Clone, Copy, PartialEq, Eq)]
enum Void {
    StaleHead,
    SeatEnded,
}

struct Ctx<'a, R: ContentRow, P> {
    rows: &'a [&'a R],
    by: BTreeMap<&'a R::Id, &'a R>,
    seat: &'a Seat<'a, R::Key>,
    past: &'a P,
}

impl<'a, R: ContentRow, P: Past<R::Id>> Ctx<'a, R, P> {
    fn of_kind(&self, k: Kind) -> impl Iterator<Item = &'a R> + '_ {
        self.rows.iter().copied().filter(move |r| r.kind() == k)
    }

    fn later(&self, h: Option<&R::Id>, he: Option<&R::Id>) -> Result<bool, R::Id> {
        match (h, he) {
            (Some(h), Some(he)) => self.past.in_past(he, h),
            _ => Ok(false),
        }
    }

    // Whether an end counts is decided by its own causal past alone: E1 (a head later than its own in its
    // past), or a counting end of the seat in its past. No row signed later changes it.
    fn void(
        &self,
        e: &'a R,
        memo: &mut BTreeMap<R::Id, Result<Option<Void>, R::Id>>,
        depth: usize,
    ) -> Result<Option<Void>, R::Id> {
        if let Some(v) = memo.get(e.id()) {
            return v.clone();
        }
        let out = (|| {
            let stale = any3(self.of_kind(Kind::Head), |h| {
                Ok(self.past.in_past(h.id(), e.id())? && self.later(Some(h.id()), e.head())?)
            })?;
            if stale {
                return Ok(Some(Void::StaleHead));
            }
            // ends in e's own past; a chain longer than the rows is a cycle of names, which ends nothing
            let earlier: Vec<&R> = self.of_kind(Kind::End).filter(|o| o.id() != e.id()).collect();
            let seated = any3(earlier.into_iter(), |o| {
                if depth >= self.rows.len() || !self.past.in_past(o.id(), e.id())? {
                    return Ok(false);
                }
                Ok(self.void(o, memo, depth + 1)?.is_none())
            })?;
            Ok(seated.then_some(Void::SeatEnded))
        })();
        memo.insert(e.id().clone(), out.clone());
        out
    }

    // the content rows a row's tips hold good: each held tip that is a content row of the member, and its
    // ancestors along every predecessor that is a held row of the same key
    fn held_good(&self, r: &R, out: &mut BTreeSet<&'a R::Id>) {
        let mut todo: Vec<&R::Id> = r.tips().iter().collect();
        while let Some(t) = todo.pop() {
            let Some((id, x)) = self.by.get_key_value(t) else { continue };
            if x.kind() != Kind::Content || !(self.seat.member)(x.signer()) || !out.insert(id) {
                continue;
            }
            for q in x.prev() {
                if self.by.get(q).is_some_and(|p| p.signer() == x.signer()) {
                    todo.push(q);
                }
            }
        }
    }

    // the rows held good by the tips that are read, given why each end is void or not
    fn kept(&self, void: &BTreeMap<&'a R::Id, Option<Void>>) -> BTreeSet<&'a R::Id> {
        let is_count = |r: &R| (self.seat.counted)(r.signer());
        let is_member = |r: &R| (self.seat.member)(r.signer());
        let ends: Vec<&R> = self.of_kind(Kind::End).collect();
        let counts = |e: &R| void[e.id()].is_none();
        let mut good = BTreeSet::new();
        for t in self.of_kind(Kind::Tips).filter(|t| is_count(t)) {
            self.held_good(t, &mut good);
        }
        if ends.iter().any(|e| counts(e) && is_count(e)) {
            for e in ends.iter().filter(|e| is_count(e) && void[e.id()] != Some(Void::StaleHead)) {
                self.held_good(e, &mut good);
            }
            return good;
        }
        let mut own: Option<BTreeSet<&R::Id>> = None;
        for e in ends.iter().filter(|e| counts(e) && is_member(e)) {
            let mut g = BTreeSet::new();
            self.held_good(e, &mut g);
            own = Some(match own {
                Some(o) => o.intersection(&g).copied().collect(),
                None => g,
            });
        }
        good.extend(own.unwrap_or_default());
        good
    }
}

/// For every content row of the member among `rows`: whether it counts at its own head, whether it is in the
/// room's content, and the rule that decides. `rows` are the rows the caller holds that bear on one member's
/// seat in one room: the roster heads, the member's content rows, the ends of the seat, rows adding tips.
///
/// `past` is asked whether an end or a head is in the past of a row; a predecessor and a tip are read from the
/// rows themselves and never asked of it. Where it cannot tell, the rows that need the answer are
/// [`Answer::Undecided`] with the row to fetch.
pub fn answers<R: ContentRow, P: Past<R::Id>>(rows: &[&R], seat: &Seat<'_, R::Key>, past: &P) -> Answers<R::Id> {
    let cx = Ctx { rows, by: rows.iter().map(|r| (r.id(), *r)).collect(), seat, past };
    let content: Vec<&R> = cx.of_kind(Kind::Content).filter(|r| (seat.member)(r.signer())).collect();
    let mut memo = BTreeMap::new();
    let mut void = BTreeMap::new();
    for e in cx.of_kind(Kind::End) {
        match cx.void(e, &mut memo, 0) {
            Ok(v) => void.insert(e.id(), v),
            // whether an end counts cannot be told: nothing about the member's content can be
            Err(i) => return content.iter().map(|x| (x.id().clone(), Answer::Undecided(i.clone()))).collect(),
        };
    }
    let ends: Vec<&R> = cx.of_kind(Kind::End).filter(|e| void[e.id()].is_none()).collect();
    let good = cx.kept(&void);
    let retracted: BTreeSet<&R::Id> = content
        .iter()
        .filter_map(|w| w.retracts().map(|t| (w, t)))
        .filter(|(w, t)| cx.by.get(t).is_some_and(|x| x.signer() == w.signer()))
        .map(|(_, t)| t)
        .collect();
    let judge = |x: &R| -> Result<Judged, R::Id> {
        let j = |counted, in_force, rule| Ok(Judged { counted, in_force, rule });
        if any3(ends.iter(), |e| cx.past.in_past(e.id(), x.id()))? {
            return j(false, false, Rule::NamesEnd);
        }
        if any3(ends.iter(), |e| cx.later(x.head(), e.head()))? {
            return j(false, false, Rule::LaterHead);
        }
        if retracted.contains(x.id()) {
            return j(true, false, Rule::Retracted);
        }
        if ends.is_empty() {
            return j(true, true, Rule::NoEnd);
        }
        if good.contains(x.id()) {
            return j(true, true, Rule::HeldGood);
        }
        j(true, false, Rule::Forward)
    };
    content
        .iter()
        .map(|x| {
            let a = match judge(x) {
                Ok(v) => Answer::Judged(v),
                Err(i) => Answer::Undecided(i),
            };
            (x.id().clone(), a)
        })
        .collect()
}

/// What the arrival of one row changes: the content rows of the member whose answer over `rows` differs from
/// their answer over `rows` without the row `arrived`, each with its new answer. A content row that arrives is
/// among them with its first answer. `rows` holds the arrived row.
///
/// A store that folds row by row keeps the answers it was last given and applies these. Folding every arrival
/// this way ends at [`answers`] over the same rows, in every arrival order.
///
/// This is the definition of the step, computed by reading the rows twice. It is linear in the rows of the
/// member in the room for every arrival; a form that visits only what can change is not written yet, and when
/// it is, it must give exactly this.
pub fn changed<R: ContentRow, P: Past<R::Id>>(
    rows: &[&R],
    arrived: &R::Id,
    seat: &Seat<'_, R::Key>,
    past: &P,
) -> Answers<R::Id> {
    let before: Vec<&R> = rows.iter().copied().filter(|r| r.id() != arrived).collect();
    let was = answers(&before, seat, past);
    let mut now = answers(rows, seat, past);
    now.retain(|x, a| was.get(x) != Some(a));
    now
}
