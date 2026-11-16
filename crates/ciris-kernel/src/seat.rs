//! **stands**: the seat as two consents, the bounded walk of live seats, and the members at the head a row
//! names (KERNEL.md sections 5 and 7; CC 2.7.5, 2.7.7, 2.7.8). `seat.py`.
//!
//! A seat of key k in scope s over object o is live iff a kept, concluded **offer** by a conferrer names
//! (k, s, o), a kept, concluded **acceptance** by k is paired with it, neither is withdrawn by its own
//! signer, and no counting cut removes it. The conferrer is one parameter with three values: the object's
//! own key, a key holding a live seat that may confer this one, or a group whose count is met over the head
//! the offer names. Which seat may confer which, what each holds, and every count are table data
//! ([`SeatLaw`]).
//!
//! When several counted acts on one object are concurrent, the holders of a scope over it are the keys
//! common to the tips, until a counted act names them all (tips wait). A counted act counts only if every
//! counted act it is built on counts, and a reader's own acknowledged line voids older-head acts for that
//! reader only ([`crate::line`]).
//!
//! Whether an offer or an unseat was validly made is concluded ([`seat_rule`]); whether a seat is live now
//! is derived ([`Seats`]). No instant, digest or list position is read.

use crate::cut::{Cut, CutSpec};
use crate::graph::Graph;
use crate::layers::{Concluded, Past};
use crate::line::{self, LineSpec};
use crate::ranked::ranked;
use crate::Row;
use alloc::collections::{BTreeMap, BTreeSet};
use alloc::string::String;
use alloc::vec::Vec;
use core::cell::RefCell;

/// What a seat is over: a row (a group is the row that founded it) or a key.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub enum Obj<I, K> {
    /// A row, by digest.
    Row(I),
    /// A key.
    Key(K),
}

/// A reference as the signed object writes it (CC 2.6.1.7; `manifests/signed_object_v2.cddl`, parent
/// repository): a row is named by its row id, a `hash-digest` `[-16, digest]` (inside a `row-ref` the
/// caller has read the edition); a key is named by its identity reference, the text
/// `urn:ietf:params:oauth:ckt:sha-256:` and 43 base64url characters.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Reference<'r> {
    /// A `hash-digest`: the algorithm and the digest.
    Digest {
        /// The COSE algorithm; -16 is SHA-256.
        alg: i64,
        /// The digest bytes.
        digest: &'r [u8],
    },
    /// A text reference.
    Text(&'r str),
}

/// The COSE algorithm of SHA-256, the one a row id uses.
pub const SHA_256: i64 = -16;
/// The prefix of an identity reference (RFC 9278 JWK thumbprint URI, SHA-256).
pub const IDENTITY_PREFIX: &str = "urn:ietf:params:oauth:ckt:sha-256:";

/// Whether a text is an identity reference: the prefix and exactly 43 base64url characters.
pub fn is_identity_reference(s: &str) -> bool {
    s.strip_prefix(IDENTITY_PREFIX)
        .is_some_and(|t| t.len() == 43 && t.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'-' || b == b'_'))
}

impl<I, K> Obj<I, K> {
    /// The object a reference names, read from its form alone: a SHA-256 `hash-digest` of 32 bytes is a row,
    /// an identity reference is a key, and anything else names nothing. `row` and `key` turn the reference
    /// into the caller's own id types.
    pub fn from_reference(r: Reference<'_>, row: impl FnOnce(&[u8]) -> I, key: impl FnOnce(&str) -> K) -> Option<Self> {
        match r {
            Reference::Digest { alg, digest } if alg == SHA_256 && digest.len() == 32 => Some(Obj::Row(row(digest))),
            Reference::Text(t) if is_identity_reference(t) => Some(Obj::Key(key(t))),
            _ => None,
        }
    }
}

/// Who confers a seat.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Conf {
    /// The object's own key.
    Own,
    /// A key holding a live seat that may confer this one (`under`).
    Seat,
    /// A group, whose count over the head the row names is met.
    Group,
}

/// What a row is, as the seat reads it.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum SeatKind {
    /// An offer of a seat.
    Offer,
    /// An acceptance of an offer.
    Accept,
    /// A withdrawal of a row by its own signer (or by the holder against the offer that seats it).
    Withdraw,
    /// An unseat: a cut on the seat slot.
    Unseat,
    /// A cosignature, a voice for a counted row.
    Cosign,
    /// A ranked ballot.
    Ballot,
    /// A reader's acknowledgement of a head.
    Ack,
    /// Anything else.
    Other,
}

/// The fields the seat reads. Every accessor has a default for a row that does not carry the field.
pub trait SeatRow: Row {
    /// A scope or policy name.
    type Word: Ord + Clone + AsRef<str>;
    /// What the row is.
    fn seat_kind(&self) -> SeatKind;
    /// The keys an offer or unseat names.
    fn to(&self) -> &[Self::Key] {
        &[]
    }
    /// Its scope (an offer, unseat, or a standing acceptance).
    fn scope(&self) -> Option<&Self::Word> {
        None
    }
    /// The object (an offer, unseat, or a standing acceptance).
    fn obj(&self) -> Option<Obj<Self::Id, Self::Key>> {
        None
    }
    /// Who confers.
    fn conf(&self) -> Option<Conf> {
        None
    }
    /// For a conferred seat, the offer whose seat it is under.
    fn under(&self) -> Option<&Self::Id> {
        None
    }
    /// Further signatures on the row itself.
    fn cosigners(&self) -> &[Self::Key] {
        &[]
    }
    /// The subjects a row names (their keys are the row's own keys).
    fn subjects(&self) -> &[Self::Key] {
        &[]
    }
    /// An offer that waives the acceptance (a node has no agency); refused under [`Conf::Seat`].
    fn consent_one(&self) -> bool {
        false
    }
    /// The grant carries sub-delegation: it may confer the same or narrower.
    fn sub(&self) -> bool {
        false
    }
    /// The heads a counted row is counted over.
    fn head(&self) -> &[Self::Id] {
        &[]
    }
    /// The policy row a count is read from.
    fn policy(&self) -> Option<&Self::Word> {
        None
    }
    /// The scope counted (default `member`).
    fn counted(&self) -> Option<&Self::Word> {
        None
    }
    /// The object counted over, when it is not the object.
    fn over(&self) -> Option<Obj<Self::Id, Self::Key>> {
        None
    }
    /// A declared threshold.
    fn need(&self) -> Option<usize> {
        None
    }
    /// An acceptance: the offer it accepts (none for a standing acceptance). A cosignature: the content
    /// it is a voice for.
    fn of(&self) -> Option<&Self::Id> {
        None
    }
    /// A withdrawal: the row it withdraws.
    fn target(&self) -> Option<&Self::Id> {
        None
    }
    /// The content a cosignature names (default the row's own id).
    fn content(&self) -> Option<&Self::Id> {
        None
    }
    /// The duties a founding row declares beside the four the law names.
    fn duties(&self) -> &[Self::Word] {
        &[]
    }
    /// The whole-number weights a `weighted` count reads, from the group's signed record.
    fn weights(&self) -> &[(Self::Key, u64)] {
        &[]
    }
    /// A ranked offer's options.
    fn options(&self) -> &[Self::Key] {
        &[]
    }
    /// A ballot's ranking.
    fn ranking(&self) -> &[Self::Key] {
        &[]
    }
    /// An acknowledgement: the object (room) whose head it acknowledges.
    fn room(&self) -> Option<Obj<Self::Id, Self::Key>> {
        None
    }
}

/// A count, read from the policy table.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Policy {
    /// `yes / n >= num / den`, and n > 0.
    AtLeast(u64, u64),
    /// `yes / n > num / den`.
    Strict(u64, u64),
    /// One voice.
    One,
    /// The threshold the row declares.
    Declared,
    /// The ranked tally: the ballots the row names, and the row seats the winner.
    Ranked,
    /// CC 4.5.4 (iv): conferral by a strict majority of the duty holders.
    DutyConfer,
    /// CC 4.5.4 (iv): withdrawal by a strict majority of the other duty holders.
    DutyWithdraw,
    /// CC 3.3.4 `unanimous`: every member at the head signs an admission; a removal is signed by every
    /// member but the one it names, and those signers are a strict majority of the roster.
    Unanimous,
    /// CC 4.4.3.6 `open:self_admit`: the group's side of a widening naming one NEW key is that key's own
    /// signature; a removal, or a widening naming a key already seated (a change of role), takes the floor
    /// of two voices besides the member named (CC 4.5.13).
    SelfAdmit,
    /// CC 3.3.4 `weighted:{rubric}`: the sum of the signing members' whole-number weights reaches the
    /// whole-number threshold, both carried on the group's signed record (here: the row's `weights` and
    /// `need`).
    Weighted,
    /// Not a count (a seat, not a threshold).
    NotACount,
}

/// Where a conferred scope lies.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Over {
    /// Over the same object as the seat that confers it.
    Same,
    /// Over the conferring holder's own key.
    Holder,
}

/// The table data the seat reads (CC 4.5.4 and the policy table). None of it is code.
#[derive(Clone, Debug, Default)]
pub struct SeatLaw {
    /// The duties the law names (`moderate`, `review`, `slash`, `takedown`).
    pub duties: Vec<String>,
    /// What a seat holds at zero hops, by scope.
    pub holds: BTreeMap<String, Vec<String>>,
    /// What a seat may confer, by scope, and over which object.
    pub confers: BTreeMap<String, (Vec<String>, Over)>,
    /// What the holder of a seat over an object may end over that object, by scope.
    pub ends: BTreeMap<String, Vec<String>>,
    /// Scopes whose ending is final: no offer re-seats the key once such an unseat is in its past.
    pub final_scopes: Vec<String>,
    /// The seats over a community its duty holders do not place (the roster's own: `member`).
    pub roster_seats: Vec<String>,
    /// The longest chain of conferred seats below a root.
    pub depth: usize,
    /// The count each policy row names.
    pub policy: BTreeMap<String, Policy>,
}

impl SeatLaw {
    fn is_duty(&self, scope: &str, declared: &[&str]) -> bool {
        let head = scope.split(':').next().unwrap_or(scope);
        scope == "duty" || self.duties.iter().any(|d| d == head) || declared.contains(&head)
    }
    fn policy_of(&self, p: Option<&str>) -> Option<Policy> {
        p.and_then(|p| self.policy.get(p).copied())
    }
}

/// Whether a scope held covers the scope wanted: equal, or the wanted one narrower by a `:` segment.
pub fn covers(have: &str, want: &str) -> bool {
    have == want || (want.len() > have.len() && want.starts_with(have) && want.as_bytes()[have.len()] == b':')
}

type ObjOf<R> = Obj<<R as Row>::Id, <R as Row>::Key>;
type Step<'r, R> = ((&'r <R as Row>::Id, &'r <R as Row>::Key), (usize, Root<<R as Row>::Id, <R as Row>::Key>));

/// The root a live seat is walked from.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub enum Root<I, K> {
    /// A key: the signer of a self-rooted offer.
    Key(K),
    /// A group: the object of a counted offer.
    Group(Obj<I, K>),
}

/// A live seat.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub struct Live<I, K, W> {
    /// The offer that seats it.
    pub offer: I,
    /// The key seated.
    pub k: K,
    /// Its scope.
    pub scope: W,
    /// What it is over.
    pub obj: Obj<I, K>,
    /// Links below its root.
    pub depth: usize,
    /// Its root.
    pub root: Root<I, K>,
}

/// Whether `k` signed row `r`: its signer or one of its cosigners (`signers(r).contains(k)`, with no set).
fn signed_by<R: SeatRow>(r: &R, k: &R::Key) -> bool {
    r.signer() == k || r.cosigners().contains(k)
}

fn signers<R: SeatRow>(r: &R) -> BTreeSet<R::Key> {
    let mut s: BTreeSet<R::Key> = r.cosigners().iter().cloned().collect();
    s.insert(r.signer().clone());
    s
}

/// The reader's line over seat rows: a counted act is an offer or unseat conferred by a group that names a
/// head; a reader's acknowledgement is an [`SeatKind::Ack`] with a room.
pub struct SeatLine;

impl<R: SeatRow> LineSpec<R> for SeatLine {
    type Obj = ObjOf<R>;
    fn counted_act<'r>(&self, r: &'r R) -> Option<(Self::Obj, &'r [R::Id])> {
        match r.seat_kind() {
            SeatKind::Offer | SeatKind::Unseat if r.conf() == Some(Conf::Group) && !r.head().is_empty() => {
                r.obj().map(|o| (o, r.head()))
            }
            _ => None,
        }
    }
    fn ack_by<'r>(&self, r: &'r R, own: &R::Key) -> Option<(Self::Obj, &'r [R::Id])> {
        if r.seat_kind() == SeatKind::Ack && r.signer() == own {
            r.room().map(|o| (o, r.head()))
        } else {
            None
        }
    }
}

fn row_of<'a, R: SeatRow>(by: &BTreeMap<&R::Id, &'a R>, o: &ObjOf<R>) -> Option<&'a R> {
    match o {
        Obj::Row(i) => by.get(i).copied(),
        Obj::Key(_) => None,
    }
}

/// A seat placed over a community by its duty holders: the object is a founding row seating duty holders,
/// and the scope is any but the roster's own.
fn duty_seat<R: SeatRow>(law: &SeatLaw, by: &BTreeMap<&R::Id, &R>, o: &R) -> bool {
    let Some(obj) = o.obj() else { return false };
    let Some(g) = row_of(by, &obj) else { return false };
    if g.seat_kind() != SeatKind::Offer
        || g.obj() != Some(Obj::Row(g.id().clone()))
        || g.id() == o.id()
        || g.scope().map(|s| s.as_ref()) != Some("duty")
    {
        return false;
    }
    o.scope().is_none_or(|s| !law.roster_seats.iter().any(|x| x == s.as_ref()))
}

fn founding_many<R: SeatRow>(by: &BTreeMap<&R::Id, &R>, obj: &ObjOf<R>) -> bool {
    row_of(by, obj).is_some_and(|g| {
        g.seat_kind() == SeatKind::Offer && g.obj() == Some(Obj::Row(g.id().clone())) && g.to().len() > 1
    })
}

fn own_keys<R: SeatRow>(by: &BTreeMap<&R::Id, &R>, obj: &ObjOf<R>) -> BTreeSet<R::Key> {
    match obj {
        Obj::Key(k) => core::iter::once(k.clone()).collect(),
        Obj::Row(_) => match row_of(by, obj) {
            Some(g) => {
                let mut s = signers(g);
                s.extend(g.subjects().iter().cloned());
                s
            }
            None => BTreeSet::new(),
        },
    }
}

fn declared<'a, R: SeatRow>(by: &BTreeMap<&R::Id, &'a R>, obj: &ObjOf<R>) -> Vec<&'a str> {
    row_of(by, obj).map_or(Vec::new(), |g| g.duties().iter().map(|d| d.as_ref()).collect())
}

/// The live seats over a concluded set, for reader `own` (the reader's line), with the cut the caller's
/// [`CutSpec`] states.
pub struct Seats<'c, 'a, R: SeatRow, S: CutSpec<R>> {
    /// The concluded set.
    pub c: &'c Concluded<'a, R>,
    /// The cut over it.
    pub cut: Cut<'c, 'a, R, S>,
    law: &'c SeatLaw,
    spec: &'c S,
    by: BTreeMap<&'a R::Id, &'a R>,
    /// The counted acts that do not count for this reader.
    pub stale: BTreeSet<usize>,
    /// Every live seat.
    pub recs: Vec<Live<R::Id, R::Key, R::Word>>,
    /// [`Seats::tips`] and [`Seats::tips_common`] by object (and scope), kept once asked: the seats are fixed
    /// when built, and no reader enters either (the reader's line is in `stale`).
    tips_memo: RefCell<BTreeMap<ObjOf<R>, Vec<usize>>>,
    common_memo: RefCell<BTreeMap<(String, ObjOf<R>), Option<BTreeSet<R::Key>>>>,
}

impl<'c, 'a, R: SeatRow, S: CutSpec<R>> Seats<'c, 'a, R, S> {
    /// Walk the live seats.
    pub fn new(c: &'c Concluded<'a, R>, law: &'c SeatLaw, spec: &'c S, own: Option<&R::Key>) -> Self {
        let cut = Cut::new(c, spec);
        let g = &c.g;
        let by: BTreeMap<&'a R::Id, &'a R> = g.rows().iter().map(|r| (r.id(), *r)).collect();
        let cs = c.cs();
        // the concluded withdrawals by the row they withdraw, and the concluded acceptances by their signer
        let mut wd: BTreeMap<&R::Id, Vec<&R>> = BTreeMap::new();
        let mut acc: BTreeMap<&R::Key, Vec<usize>> = BTreeMap::new();
        for &i in cs {
            let r = g.row(i);
            match r.seat_kind() {
                SeatKind::Withdraw => {
                    if let Some(t) = r.target() {
                        wd.entry(t).or_default().push(r);
                    }
                }
                SeatKind::Accept => acc.entry(r.signer()).or_default().push(i),
                _ => {}
            }
        }
        let none: Vec<&R> = Vec::new();
        let wd_of = |id: &R::Id| wd.get(id).unwrap_or(&none);
        let ended = |row: &R| !wd_of(row.id()).is_empty();
        let eq = |o: &R| duty_seat(law, &by, o);
        let off_ended = |o: &R, k: &R::Key| {
            wd_of(o.id()).iter().any(|w| {
                w.target() == Some(o.id())
                    && (w.signer() == k || (!o.to().contains(w.signer()) && o.conf() != Some(Conf::Group) && !eq(o)))
            })
        };
        let stale = line::void(c, &SeatLine, own, |i| cut.counts(i));
        // each unseat that counts, with its object read once
        let unseats: Vec<(usize, Option<ObjOf<R>>)> = cs
            .iter()
            .copied()
            .filter(|&i| g.row(i).seat_kind() == SeatKind::Unseat && cut.counts(i) && !stale.contains(&i))
            .map(|i| (i, g.row(i).obj()))
            .collect();
        let member = |s: Option<&R::Word>| s.map(|x| x.as_ref()) == Some("member");
        let unseated = |oi: usize, k: &R::Key| {
            if unseats.is_empty() {
                return false;
            }
            let o = g.row(oi);
            let dutyish = o.scope().is_some_and(|s| law.is_duty(s.as_ref(), &[])) || duty_seat(law, &by, o);
            let oo = o.obj();
            unseats.iter().any(|(u, uo)| {
                let (u, ur) = (*u, g.row(*u));
                let same = ur.to().contains(k) && *uo == oo;
                let held = same && (ur.scope() == o.scope() || (dutyish && member(ur.scope())));
                held && g.in_past(oi, u)
            })
        };
        let accepted = |o: &R, k: &R::Key| {
            if signed_by(o, k) {
                return true;
            }
            if o.consent_one() {
                return o.conf() != Some(Conf::Seat);
            }
            acc.get(k).is_some_and(|accs| accs.iter().any(|&a| {
                let ar = g.row(a);
                if ar.seat_kind() != SeatKind::Accept || ar.signer() != k {
                    return false;
                }
                let paired = ar.of() == Some(o.id())
                    || (ar.of().is_none()
                        && o.names().contains(ar.id())
                        && ar.scope() == o.scope()
                        && ar.obj().is_none_or(|x| Some(x) == o.obj()));
                paired && !ended(ar) && cut.counts(a)
            }))
        };
        // keys are borrowed from the rows through the walk, and copied once into each live seat
        let mut base: Vec<(usize, &'a R::Key)> = Vec::new();
        for &oi in cs {
            let o = g.row(oi);
            if o.seat_kind() != SeatKind::Offer || !cut.counts(oi) || stale.contains(&oi) {
                continue;
            }
            for k in o.to() {
                if !off_ended(o, k) && accepted(o, k) && !unseated(oi, k) {
                    base.push((oi, k));
                }
            }
        }
        // one link per pass: at most `depth` links below a root
        type At<'r, I, K> = BTreeMap<(&'r I, &'r K), (usize, Root<I, K>)>;
        let mut at: At<'a, R::Id, R::Key> = BTreeMap::new();
        for _ in 0..(law.depth + 1) {
            let mut add: Vec<Step<'a, R>> = Vec::new();
            for &(oi, k) in &base {
                let o = g.row(oi);
                let key = (o.id(), k);
                if at.contains_key(&key) {
                    continue;
                }
                let obj = o.obj();
                match o.conf() {
                    Some(Conf::Own) => {
                        let founding = obj == Some(Obj::Row(o.id().clone()));
                        let ok = founding
                            || !obj.as_ref().is_some_and(|x| founding_many(&by, x))
                            || matches!(&obj, Some(Obj::Row(f)) if at.contains_key(&(f, o.signer())));
                        if ok {
                            add.push((key, (0, Root::Key(o.signer().clone()))));
                        }
                    }
                    Some(Conf::Group) => {
                        if let Some(x) = obj {
                            add.push((key, (0, Root::Group(x))));
                        }
                    }
                    _ if eq(o) => {
                        if let Some(x) = obj {
                            add.push((key, (0, Root::Group(x))));
                        }
                    }
                    Some(Conf::Seat) => {
                        if let Some(u) = o.under() {
                            if let (Some(up), Some(hit)) = (by.get(u), at.get(&(u, o.signer()))) {
                                if may_confer(law, *up, o) {
                                    add.push((key, (hit.0 + 1, hit.1.clone())));
                                }
                            }
                        }
                    }
                    None => {}
                }
            }
            if add.is_empty() {
                break;
            }
            for (k, v) in add {
                at.entry(k).or_insert(v);
            }
        }
        let recs = at
            .into_iter()
            .filter_map(|((oid, k), (depth, root))| {
                let o = by[oid];
                Some(Live { offer: oid.clone(), k: k.clone(), scope: o.scope()?.clone(), obj: o.obj()?, depth, root })
            })
            .collect();
        Seats { c, cut, law, spec, by, stale, recs, tips_memo: RefCell::default(), common_memo: RefCell::default() }
    }

    fn has(&self, rec: &Live<R::Id, R::Key, R::Word>, s: &str) -> bool {
        let sc = rec.scope.as_ref();
        if s == "duty" && self.law.is_duty(sc, &declared(&self.by, &rec.obj)) {
            return true; // a holder of any one duty is a duty holder
        }
        covers(sc, s) || self.law.holds.get(sc).is_some_and(|h| h.iter().any(|x| x == s))
    }

    /// Whether key `k` stands in scope `s` over `o` (rooted at `root`, when given). While tips wait, a key
    /// stands only if every tip seats it.
    pub fn stands(&self, k: &R::Key, s: &str, o: &ObjOf<R>, root: Option<&Root<R::Id, R::Key>>) -> bool {
        let any =
            self.recs.iter().any(|r| r.k == *k && r.obj == *o && self.has(r, s) && root.is_none_or(|x| r.root == *x));
        any && self.tips_common(s, o).is_none_or(|c| c.contains(k))
    }

    /// The keys holding scope `s` over `o`.
    pub fn holders(&self, s: &str, o: &ObjOf<R>, root: Option<&Root<R::Id, R::Key>>) -> BTreeSet<R::Key> {
        let got: BTreeSet<R::Key> = self
            .recs
            .iter()
            .filter(|r| r.obj == *o && self.has(r, s) && root.is_none_or(|x| r.root == *x))
            .map(|r| r.k.clone())
            .collect();
        match self.tips_common(s, o) {
            None => got,
            Some(c) => got.intersection(&c).cloned().collect(),
        }
    }

    /// The single holder, where the seat is single-valued (an owner): two live holders is none.
    pub fn one(&self, s: &str, o: &ObjOf<R>) -> Option<R::Key> {
        crate::ops::one(self.recs.iter().filter(|r| r.obj == *o && self.has(r, s)).map(|r| r.k.clone()))
    }

    /// The frontier of the counted acts on `o` that count, with its founding row.
    pub fn tips(&self, o: &ObjOf<R>) -> Vec<usize> {
        if let Some(t) = self.tips_memo.borrow().get(o) {
            return t.clone();
        }
        let t = self.tips_of(o);
        self.tips_memo.borrow_mut().insert(o.clone(), t.clone());
        t
    }

    fn tips_of(&self, o: &ObjOf<R>) -> Vec<usize> {
        let g = &self.c.g;
        let acts: Vec<usize> = self
            .c
            .cs()
            .iter()
            .copied()
            .filter(|&i| {
                let r = g.row(i);
                matches!(r.seat_kind(), SeatKind::Offer | SeatKind::Unseat)
                    && r.obj().as_ref() == Some(o)
                    && (r.conf() == Some(Conf::Group) || Obj::Row(r.id().clone()) == *o)
                    && self.cut.counts(i)
                    && !self.stale.contains(&i)
            })
            .collect();
        g.frontier(&acts)
    }

    /// With several tips, the keys holding `s` over `o` common to all of them; `None` with one tip or none.
    pub fn tips_common(&self, s: &str, o: &ObjOf<R>) -> Option<BTreeSet<R::Key>> {
        let key = (String::from(s), o.clone());
        if let Some(t) = self.common_memo.borrow().get(&key) {
            return t.clone();
        }
        let t = self.common_of(s, o);
        self.common_memo.borrow_mut().insert(key, t.clone());
        t
    }

    fn common_of(&self, s: &str, o: &ObjOf<R>) -> Option<BTreeSet<R::Key>> {
        let tp = self.tips(o);
        if tp.len() <= 1 {
            return None;
        }
        let g = &self.c.g;
        let mut out: Option<BTreeSet<R::Key>> = None;
        for t in tp {
            let sub: Vec<&R> =
                self.c.cs().iter().copied().filter(|&q| q == t || g.in_past(q, t)).map(|q| g.row(q)).collect();
            let sc = Concluded::with(Graph::new(sub), None);
            let q = Seats::new(&sc, self.law, self.spec, None);
            let m: BTreeSet<R::Key> =
                q.recs.iter().filter(|r| r.obj == *o && q.has(r, s)).map(|r| r.k.clone()).collect();
            out = Some(match out {
                None => m,
                Some(x) => x.intersection(&m).cloned().collect(),
            });
        }
        out
    }
}

fn may_confer<R: SeatRow>(law: &SeatLaw, up: &R, o: &R) -> bool {
    let (Some(us), Some(os)) = (up.scope(), o.scope()) else { return false };
    if up.sub() && covers(us.as_ref(), os.as_ref()) && o.obj() == up.obj() {
        return true; // the grant carried sub-delegation: the same or narrower
    }
    let Some((scopes, over)) = law.confers.get(us.as_ref()) else { return false };
    let want = match over {
        Over::Same => up.obj(),
        Over::Holder => Some(Obj::Key(o.signer().clone())),
    };
    scopes.iter().any(|s| covers(s, os.as_ref())) && o.obj() == want
}

fn concluded_over<'a, R: Row>(rows: impl IntoIterator<Item = &'a R>) -> Concluded<'a, R> {
    Concluded::with(Graph::new(rows), None)
}

/// The live `scope` seats over `obj`, read from the rows in the past of the heads only (`p`: a row's
/// concluded ancestors). Several heads: the keys common to all of them (tips wait).
pub fn members_at<R: SeatRow, S: CutSpec<R>>(
    p: &Past<'_, '_, R>,
    law: &SeatLaw,
    spec: &S,
    obj: &ObjOf<R>,
    heads: &[R::Id],
    scope: &str,
) -> BTreeSet<R::Key> {
    // as members_in over p's rows with p's closure, read by index: a head's past is taken whole once
    let g = p.g;
    let mut out: Option<BTreeSet<R::Key>> = None;
    for h in heads {
        let Some(hi) = g.idx(h).filter(|hi| p.p.contains(hi)) else { return BTreeSet::new() };
        let past = g.ancestors(hi);
        let sc = concluded_over(p.p.iter().filter(|&&q| q == hi || past.has(q)).map(|&q| g.row(q)));
        let m = Seats::new(&sc, law, spec, None).holders(scope, obj, None);
        out = Some(match out {
            None => m,
            Some(x) => x.intersection(&m).cloned().collect(),
        });
    }
    out.unwrap_or_default()
}

/// [`members_at`] over any concluded rows, with the closure given as `past(a, b)`: a in the past of b.
pub fn members_in<R: SeatRow, S: CutSpec<R>>(
    rows: &[&R],
    past: &dyn Fn(&R::Id, &R::Id) -> bool,
    law: &SeatLaw,
    spec: &S,
    obj: &ObjOf<R>,
    heads: &[R::Id],
    scope: &str,
) -> BTreeSet<R::Key> {
    members_in_scopes(rows, past, law, spec, obj, heads, &[scope]).pop().unwrap_or_default()
}

/// [`members_in`] for several scopes at once, in the order given: the seats at each head are walked once and
/// read for every scope.
pub fn members_in_scopes<R: SeatRow, S: CutSpec<R>>(
    rows: &[&R],
    past: &dyn Fn(&R::Id, &R::Id) -> bool,
    law: &SeatLaw,
    spec: &S,
    obj: &ObjOf<R>,
    heads: &[R::Id],
    scopes: &[&str],
) -> Vec<BTreeSet<R::Key>> {
    let mut out: Vec<Option<BTreeSet<R::Key>>> = scopes.iter().map(|_| None).collect();
    for h in heads {
        let sub: Vec<&R> = rows.iter().copied().filter(|q| q.id() == h || past(q.id(), h)).collect();
        if !sub.iter().any(|q| q.id() == h) {
            return scopes.iter().map(|_| BTreeSet::new()).collect();
        }
        let sc = concluded_over(sub);
        let seats = Seats::new(&sc, law, spec, None);
        for (o, scope) in out.iter_mut().zip(scopes) {
            let m = seats.holders(scope, obj, None);
            *o = Some(match o.take() {
                None => m,
                Some(x) => x.intersection(&m).cloned().collect(),
            });
        }
    }
    out.into_iter().map(Option::unwrap_or_default).collect()
}

/// The keys whose own leaving is among `p`: a concluded withdrawal, signed by the key, of the acceptance or
/// offer that seats it in `scope` over `obj`. A version with a key's leaving in its own past does not count
/// that key (`RosterHead.leaving_binds_by_past`).
pub fn left_in_past<R: SeatRow>(p: &Past<'_, '_, R>, obj: &ObjOf<R>, scope: &str) -> BTreeSet<R::Key> {
    let mut out = BTreeSet::new();
    for w in p.rows() {
        if w.seat_kind() != SeatKind::Withdraw {
            continue;
        }
        let Some(t) = w.target().and_then(|t| p.get(t)) else { continue };
        if t.obj().is_some_and(|x| x != *obj) || t.scope().is_some_and(|s| s.as_ref() != scope) {
            continue;
        }
        let own = match t.seat_kind() {
            SeatKind::Accept => t.signer() == w.signer(),
            SeatKind::Offer => t.to().contains(w.signer()),
            _ => false,
        };
        if own {
            out.insert(w.signer().clone());
        }
    }
    out
}

/// The keys that signed a counted row: its signer, its cosigners, and the signers of the cosignatures it
/// names that themselves name every head it is counted over.
pub fn voices<R: SeatRow>(r: &R, p: &Past<'_, '_, R>) -> BTreeSet<R::Key> {
    let heads: BTreeSet<&R::Id> = r.head().iter().collect();
    let content = r.content().unwrap_or(r.id());
    let mut v = signers(r);
    for c in p.rows() {
        if c.seat_kind() == SeatKind::Cosign
            && c.of() == Some(content)
            && r.names().contains(c.id())
            && heads.iter().all(|h| c.names().contains(*h))
        {
            v.insert(c.signer().clone());
        }
    }
    v
}

/// Whether a count is met: `yes` voices of `n`, under `policy`.
pub fn met(policy: Option<Policy>, yes: usize, n: usize, declared: Option<usize>) -> bool {
    let (y, n) = (yes as u128, n as u128);
    match policy {
        Some(Policy::AtLeast(num, den)) => n > 0 && y * den as u128 >= num as u128 * n,
        Some(Policy::Strict(num, den)) => y * den as u128 > num as u128 * n,
        Some(Policy::One) => yes >= 1,
        Some(Policy::Declared) => declared.is_some_and(|d| yes >= d),
        _ => false,
    }
}

/// The conclusion rule of the seat: was an offer, unseat, acceptance or withdrawal validly made, at the
/// head it names. `p` gives the row's concluded ancestors; `other` concludes a row the seat does not read.
pub fn seat_rule<R: SeatRow, S: CutSpec<R>>(
    p: &Past<'_, '_, R>,
    law: &SeatLaw,
    spec: &S,
    other: &dyn Fn(&Past<'_, '_, R>) -> bool,
) -> bool {
    let r = p.row();
    let by: BTreeMap<&R::Id, &R> = p.rows().map(|q| (q.id(), q)).collect();
    match r.seat_kind() {
        SeatKind::Offer | SeatKind::Unseat => {
            let is_offer = r.seat_kind() == SeatKind::Offer;
            let conf = r.conf();
            if is_offer && revoked_before(law, r, p) {
                return false; // a revoked key does not re-seat itself
            }
            if is_offer
                && matches!(conf, Some(Conf::Own) | Some(Conf::Seat))
                && duty_seat(law, &by, r)
                && !lone(law, spec, r, p)
            {
                return false;
            }
            let Some(obj) = r.obj() else { return false };
            match conf {
                Some(Conf::Own) => {
                    if obj == Obj::Row(r.id().clone()) {
                        return is_offer; // a founding row is its own object
                    }
                    if !is_offer && founding_many(&by, &obj) {
                        return false; // among several founding keys, ending a seat takes the count
                    }
                    own_keys(&by, &obj).contains(r.signer())
                }
                Some(Conf::Seat) => {
                    if !is_offer {
                        return ender(law, spec, r, p, &by);
                    }
                    r.under().and_then(|u| by.get(u)).is_some_and(|u| u.to().contains(r.signer()))
                }
                Some(Conf::Group) => {
                    let over = r.over().unwrap_or(obj.clone());
                    let counted = r.counted().map(|c| c.as_ref()).unwrap_or("member");
                    let mut mem = members_at(p, law, spec, &over, r.head(), counted);
                    for k in left_in_past(p, &over, counted) {
                        mem.remove(&k);
                    }
                    let pol = law.policy_of(r.policy().map(|x| x.as_ref()));
                    if pol == Some(Policy::Ranked) {
                        let ballots: Vec<(R::Key, Vec<R::Key>)> = p
                            .rows()
                            .filter(|b| {
                                b.seat_kind() == SeatKind::Ballot
                                    && r.names().contains(b.id())
                                    && mem.contains(b.signer())
                            })
                            .map(|b| (b.signer().clone(), b.ranking().to_vec()))
                            .collect();
                        // the one ranked row is the election, which declares no order: a tie for weakest seats nobody
                        return is_offer
                            && !ballots.is_empty()
                            && ranked(&ballots, r.options(), 2, false).0.as_ref() == r.to().first();
                    }
                    let v = voices(r, p);
                    let count =
                        GroupCount { policy: pol, offer: is_offer, to: r.to(), members: &mem, voices: &v, need: r.need() };
                    group_count(&count, |k| r.weights().iter().find(|(w, _)| w == k).map_or(0, |(_, x)| *x))
                }
                None => false,
            }
        }
        SeatKind::Accept => match r.of() {
            None => true,
            Some(o) => by.get(o).is_some_and(|o| o.to().contains(r.signer())),
        },
        SeatKind::Withdraw => match r.target().and_then(|t| by.get(t)) {
            Some(t) => {
                signed_by(*t, r.signer()) || (t.seat_kind() == SeatKind::Offer && t.to().contains(r.signer()))
            }
            None => false,
        },
        SeatKind::Cosign => true,
        _ => other(p),
    }
}

/// What a group's count reads, once the caller has resolved it: the count the policy row names, whether the
/// row is an offer (else an unseat), the keys it seats or removes, the members of the counted scope at the head
/// it names less those whose own leaving is in its past ([`members_at`], [`left_in_past`]), and its voices
/// ([`voices`]). Keys are whatever the caller counts by (KERNEL.md 7b: persist counts persons).
#[derive(Clone, Copy, Debug)]
pub struct GroupCount<'a, K> {
    /// The count, from the policy table.
    pub policy: Option<Policy>,
    /// An offer (true) or an unseat (false).
    pub offer: bool,
    /// The keys the row seats or removes (`SeatRow::to`).
    pub to: &'a [K],
    /// The members at the head, less those whose own leaving is in the row's past.
    pub members: &'a BTreeSet<K>,
    /// The keys that signed the row (`voices`).
    pub voices: &'a BTreeSet<K>,
    /// The threshold the row declares (`SeatRow::need`).
    pub need: Option<usize>,
}

/// Whether a group's count is met: [`seat_rule`]'s `Conf::Group` arm after the members and voices are read,
/// and the very code that arm runs. `weight` is a key's whole-number weight (a `weighted` count). Every policy
/// but [`Policy::Ranked`], which is a tally of the ballots the row names (`ranked::ranked`), not a count of
/// voices: here, as in [`met`], it is false.
///
/// A caller that already holds the roster at the head (persist resolves a ballot's) answers here directly,
/// without presenting the roster as rows: the same answer as the seat rule over those rows, with no graph.
pub fn group_count<K: Ord>(c: &GroupCount<'_, K>, weight: impl Fn(&K) -> u64) -> bool {
    let GroupCount { policy: pol, offer: is_offer, to, members: mem, voices: v, need } = *c;
    if pol == Some(Policy::SelfAdmit) {
        // the joiner's own signature is the group's side; a removal takes two voices besides the member it names
        return if is_offer && to.len() == 1 && !mem.contains(&to[0]) {
            v.contains(&to[0])
        } else {
            v.iter().filter(|k| mem.contains(*k) && !to.contains(k)).count() >= 2
        };
    }
    if matches!(pol, Some(Policy::DutyConfer) | Some(Policy::DutyWithdraw)) {
        let yes: BTreeSet<&K> = v.iter().filter(|k| mem.contains(*k)).collect();
        return duty_count_keys(pol == Some(Policy::DutyWithdraw), to, &yes, mem);
    }
    // no key admits itself (CC 2.7.5): a key the row seats or removes is no voice of the count
    let yes: BTreeSet<&K> = v.iter().filter(|k| mem.contains(*k) && !to.contains(k)).collect();
    if pol == Some(Policy::Weighted) {
        let sum: u64 = yes.iter().map(|k| weight(k)).sum();
        return need.is_some_and(|t| t > 0 && sum >= t as u64);
    }
    if pol == Some(Policy::Unanimous) {
        let others = mem.iter().filter(|k| !to.contains(k)).count();
        return if is_offer {
            !mem.is_empty() && yes.len() == others && to.iter().all(|k| !mem.contains(k) || v.contains(k))
        } else {
            yes.len() == others && 2 * yes.len() > mem.len()
        };
    }
    met(pol, yes.len(), mem.len(), need)
}

fn duty_count_keys<K: Ord>(withdraw: bool, to: &[K], yes: &BTreeSet<&K>, mem: &BTreeSet<K>) -> bool {
    let mem_r: BTreeSet<&K> = mem.iter().collect();
    let to_r: BTreeSet<&K> = to.iter().collect();
    let base: BTreeSet<&K> = if withdraw { mem_r.difference(&to_r).copied().collect() } else { mem_r.clone() };
    let y = yes.intersection(&base).count();
    2 * y > base.len() && (y >= 2 || mem.len() < 2)
}

fn revoked_before<R: SeatRow>(law: &SeatLaw, r: &R, p: &Past<'_, '_, R>) -> bool {
    p.rows().any(|q| {
        q.seat_kind() == SeatKind::Unseat
            && q.scope().is_some_and(|s| law.final_scopes.iter().any(|f| f == s.as_ref()))
            && q.scope() == r.scope()
            && q.obj() == r.obj()
            && q.to().iter().any(|k| r.to().contains(k))
    })
}

fn lone<R: SeatRow, S: CutSpec<R>>(law: &SeatLaw, spec: &S, r: &R, p: &Past<'_, '_, R>) -> bool {
    let Some(obj) = r.obj() else { return false };
    let sc = concluded_over(p.rows());
    let held = Seats::new(&sc, law, spec, None).holders("duty", &obj, None);
    held.len() == 1 && held.contains(r.signer())
}

fn ender<R: SeatRow, S: CutSpec<R>>(
    law: &SeatLaw,
    spec: &S,
    r: &R,
    p: &Past<'_, '_, R>,
    by: &BTreeMap<&R::Id, &R>,
) -> bool {
    let Some(up) = r.under().and_then(|u| by.get(u)) else { return false };
    if up.seat_kind() != SeatKind::Offer || up.obj() != r.obj() || !up.to().contains(r.signer()) {
        return false;
    }
    let (Some(us), Some(rs), Some(obj)) = (up.scope(), r.scope(), r.obj()) else { return false };
    if !law.ends.get(us.as_ref()).is_some_and(|e| e.iter().any(|x| x == rs.as_ref())) {
        return false;
    }
    if r.to().len() != 1 || Obj::Key(r.to()[0].clone()) != obj {
        return false;
    }
    let sc = concluded_over(p.rows());
    let sole = Seats::new(&sc, law, spec, None);
    sole.one(us.as_ref(), &obj).as_ref() == Some(r.signer())
}
