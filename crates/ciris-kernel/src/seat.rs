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
//!
//! **A duty seat stands only on a member** (CC 4.5.4, "a non-member holds no duty"). Over any community (an
//! object that is its own founding row), a seat that makes its holder a duty holder stands only where that holder
//! holds the roster's seat over the same community at the same reading: a member seat, or the founding seat
//! where it holds `member`. A conferral on a key that is not a member seats nobody and is no voice in a duty
//! count; when the key's widening lands the seat stands with no further row. An end of the holder's stay ends
//! the duty seats whose offers are in that end's past: a counted removal from the roster, or the holder's own
//! withdrawal of a seat that holds `member`. Nothing revives: a later admission does not seat an offer so
//! ended, and a conferral that is not in the end's past waits for the next admission. At tips the duty seat
//! follows the folded roster. A seat the duty holders place that is no duty (a node's detector seat) is not
//! asked for membership.
//!
//! **A moderator's lone removal is in force only while the end rule says so.** It is an act under the
//! moderator's `moderate` standing, and the seat walk counts it as a live unseat only where the end rule of
//! [`crate::conferral`] (E2 to E8), re-expressed over seat rows, gives it in force over the rows held: an end of
//! that standing (the moderator's own laying down, a counted removal of it, the other holders' counted
//! withdrawal of its duty) takes it out of force from the end's head on, unless another duty holder's receipt
//! of it is held. An AI agent's key is seated in [`AGENT`], on the roster and in no count.
//!
//! **A founding record seats its listed members and its named duty holders** (CC 4.5.4), each by its own
//! signature on it, with no count. A founding row with a [`SeatRow::duty_holders`] map seats each key of `to`
//! that signed it in the row's own scope (`member`) and in each duty whose entry names it; one offer then
//! gives a key several seats, and [`Live::scope`] is the seat's scope, not always the offer's. A withdrawal of
//! the founding row that names a scope ([`SeatRow::scope`]) ends that one seat; one that names none ends every
//! seat the row gives its signer, which is an end of its stay. A founding row of scope `duty` with no map is
//! read as before. The duty rules engage over either.

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
    /// A reader's acknowledgement of a head (with [`SeatRow::room`]). With [`SeatRow::of`] naming a
    /// moderator's lone removal instead, a receipt of that act by a duty holder, which keeps it in force after
    /// the moderator's standing ends.
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
    /// Its scope (an offer, unseat, or a standing acceptance). On a withdrawal: the one seat of the row it
    /// withdraws that it ends (a founder laying down one duty of a founding record), or `None` for every seat
    /// that row gives its signer.
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
    /// A counted act: the protocol and policy in force at it, as one value the caller compares by equality.
    /// Tips whose values differ do not fold ([`Seats::tips_fold`]). `None` where the caller states none.
    fn regime(&self) -> Option<&Self::Word> {
        None
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
    /// A founding record's duty holders (CC 4.5.4): per duty, the members who hold it. Read on a founding row
    /// only (an offer whose object is its own id). Where it is not empty, the row seats each key of
    /// [`SeatRow::to`] that signed it (signer or cosigner) in the row's own scope (`member`), and each such key
    /// an entry names in that entry's duty; a key of `to` that did not sign is seated in nothing, whatever it
    /// accepts later, and an entry's key that is not a listed signer is seated in nothing. Default empty: the
    /// founding row seats each key of `to` that signed it in its one scope (a founding row seats by the
    /// signatures on it, with or without a map). A withdrawal of the founding row that names a
    /// scope ([`SeatRow::scope`] on the withdrawal) ends that one seat of its signer's.
    fn duty_holders(&self) -> &[(Self::Word, Vec<Self::Key>)] {
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

/// The most keys an election's ballot ranks (CC 4.5.13: "Each person ranks up to three"); a ballot ranking more is
/// void, the whole ballot.
pub const ELECTION_RANKS: usize = 3;

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
    /// The ranked tally: the ballots the row names, and the row seats the winner. The election (CC 4.5.13): it
    /// seats nobody where a duty holder is live at the heads the row names; a ballot counts where its signer is
    /// counted over, its signer has not withdrawn it in the row's past, and every key it ranks holds the counted
    /// scope at those heads.
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
    /// CC 4.5.13, the members' check as a counted row: an offer that seats again an agent's key a moderator
    /// removed alone. Its voices are the signers of the objections it names ([`lift_voices`]), the removal's
    /// author and the key it seats no voice; it is met by more than half of the members at the head the
    /// removal names (persons: the key removed is an agent's, in no count), the removal's author apart, never
    /// fewer than two voices. A counted row of this policy that is no such re-seating concludes nothing.
    Lift,
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
/// One seat of an offer: the offer and the seat's scope.
type SeatOf<R> = (<R as Row>::Id, <R as SeatRow>::Word);
type MembersMemo<R> = BTreeMap<(Vec<<R as Row>::Id>, ObjOf<R>, String), BTreeSet<<R as Row>::Key>>;
/// One tip's line: the concluded rows in its past with it, and the offers that seat each key there.
type Line<R> = (Vec<usize>, BTreeMap<<R as Row>::Key, BTreeSet<<R as Row>::Id>>);
type CommonMemo<R> = RefCell<BTreeMap<(String, ObjOf<R>), Option<BTreeSet<<R as Row>::Key>>>>;
type Step<'r, R> = (
    (&'r <R as Row>::Id, &'r <R as Row>::Key, &'r <R as SeatRow>::Word),
    (usize, Root<<R as Row>::Id, <R as Row>::Key>),
);

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
    /// Its scope: the offer's own, or for a founding record the member seat or a duty its map names.
    pub scope: W,
    /// What it is over.
    pub obj: Obj<I, K>,
    /// Links below its root.
    pub depth: usize,
    /// Its root.
    pub root: Root<I, K>,
}

/// Up to how many keys an offer seats before [`Seats::new`] reads its signers as a set.
const SIGNERS_SCANNED: usize = 8;

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

/// The scope of an AI agent's seat over a room (CC 4.5.13): on the roster, and in no count.
pub const AGENT: &str = "agent";

/// `m` less the agents' keys: every count of a room is by person.
pub fn persons<K: Ord + Clone>(m: BTreeSet<K>, agents: &BTreeSet<K>) -> BTreeSet<K> {
    if agents.is_empty() {
        return m;
    }
    m.into_iter().filter(|k| !agents.contains(k)).collect()
}

fn row_of<'a, R: SeatRow>(by: &BTreeMap<&R::Id, &'a R>, o: &ObjOf<R>) -> Option<&'a R> {
    match o {
        Obj::Row(i) => by.get(i).copied(),
        Obj::Key(_) => None,
    }
}

/// A founding row whose `duty_holders` map names a holder.
fn lists_holders<R: SeatRow>(g: &R) -> bool {
    g.duty_holders().iter().any(|(_, ks)| !ks.is_empty())
}

/// Whether `o` is a founding row (its object is its own id).
fn founding<R: SeatRow>(o: &R) -> bool {
    o.obj() == Some(Obj::Row(o.id().clone()))
}

/// The scopes offer `o` seats key `k` in (`signed`: k signed it). One, the offer's own scope, for every offer
/// but a founding row. A founding row seats by the signatures on it (CC 3.1.3.2: a listed key that did not sign
/// is `membership_founding_member_unsigned`, and joins by an ordinary admission): a listed member who did not
/// sign it in nothing, whatever it accepts later; one who signed it in its own scope, and where it has a
/// `duty_holders` map, in each duty whose entry names it.
fn seat_scopes<'a, R: SeatRow>(o: &'a R, k: &R::Key, signed: bool) -> Vec<&'a R::Word> {
    let Some(own) = o.scope() else { return Vec::new() };
    if !founding(o) {
        return alloc::vec![own];
    }
    if !signed {
        return Vec::new();
    }
    if o.duty_holders().is_empty() {
        return alloc::vec![own];
    }
    let mut out = alloc::vec![own];
    out.extend(o.duty_holders().iter().filter(|(d, ks)| ks.contains(k) && d != own).map(|(d, _)| d));
    out
}

/// A duty seat a founding row gives by its `duty_holders` map: a seat of that row in a scope not its own.
fn founding_duty<R: SeatRow>(o: &R, sc: &R::Word) -> bool {
    !o.duty_holders().is_empty() && founding(o) && o.scope() != Some(sc)
}

/// A seat placed over a community by its duty holders: the object is a founding row seating duty holders,
/// and the scope is any but the roster's own.
fn duty_seat<R: SeatRow>(law: &SeatLaw, by: &BTreeMap<&R::Id, &R>, o: &R) -> bool {
    let Some(obj) = o.obj() else { return false };
    let Some(g) = row_of(by, &obj) else { return false };
    if g.id() == o.id() || !duty_room(by, &obj) {
        return false;
    }
    o.scope().is_none_or(|s| !law.roster_seats.iter().any(|x| x == s.as_ref()))
}

/// A community whose founding row seats duty holders: the only place the duty rules engage. A founding row
/// of scope `duty`, or one whose `duty_holders` map names a holder.
fn duty_room<R: SeatRow>(by: &BTreeMap<&R::Id, &R>, obj: &ObjOf<R>) -> bool {
    row_of(by, obj).is_some_and(|g| {
        g.seat_kind() == SeatKind::Offer
            && founding(g)
            && (g.scope().map(|s| s.as_ref()) == Some("duty") || lists_holders(g))
    })
}

/// A community: an object that is its own founding row. The duty-seat rule (a duty seat stands only on the
/// roster's seat; an end of the stay ends the duty seats before it) reaches every community, whatever its
/// founding row seats (CC 4.5.4: "a non-member holds no duty").
fn community<R: SeatRow>(by: &BTreeMap<&R::Id, &R>, obj: &ObjOf<R>) -> bool {
    row_of(by, obj).is_some_and(|g| g.seat_kind() == SeatKind::Offer && founding(g))
}

/// A duty seat proper, the seat of `o` in scope `sc`: over a community, a seat of another row whose scope is
/// no roster seat and makes its holder a duty holder, or a duty seat a founding row gives by its
/// `duty_holders` map. The seat the membership rule reaches, in every community. (Who may confer it is
/// [`duty_seat`]'s, and that is unchanged.)
fn duty_held<R: SeatRow>(law: &SeatLaw, by: &BTreeMap<&R::Id, &R>, o: &R, sc: &R::Word) -> bool {
    if founding_duty(o, sc) {
        return true;
    }
    let Some(obj) = o.obj() else { return false };
    let roster = o.scope().is_some_and(|s| law.roster_seats.iter().any(|x| x == s.as_ref()));
    community(by, &obj) && !founding(o) && !roster && law.is_duty(sc.as_ref(), &declared(by, &obj))
}

/// The seat of offer `o` in scope `s` is the roster's own over a community: a scope its duty holders do not
/// place, or the founding row's own scope where it holds `member`. Every other seat over the community is a
/// duty seat.
fn roster_seat<R: SeatRow>(law: &SeatLaw, o: &R, s: &str) -> bool {
    let roster = law.roster_seats.iter().any(|x| x == s);
    let own = (o.obj() == Some(Obj::Row(o.id().clone())) && o.scope().map(|x| x.as_ref()) == Some(s)) || roster;
    own && (roster || covers(s, "member") || law.holds.get(s).is_some_and(|h| h.iter().any(|x| x == "member")))
}

/// [`roster_seat`] in the offer's own scope.
fn roster_offer<R: SeatRow>(law: &SeatLaw, o: &R) -> bool {
    o.scope().is_some_and(|s| roster_seat(law, o, s.as_ref()))
}

/// Whether withdrawal `w` is its signer's own end of a stay as a member, and of which community: a withdrawal
/// by a key of an offer of the roster's seat that names it, or of its own acceptance of one (the offer the
/// acceptance names, or a standing acceptance's own scope and object). Read from the rows alone.
fn stay_end<R: SeatRow>(law: &SeatLaw, by: &BTreeMap<&R::Id, &R>, w: &R) -> Option<ObjOf<R>> {
    let k = w.signer();
    let mut t = *by.get(w.target()?)?;
    // a withdrawal that names a duty seat lays down that seat, and the stay goes on
    // and one naming a roster scope ends the stay only where its target gives the signer that seat
    if let Some(ws) = w.scope() {
        let offer = t.seat_kind() == SeatKind::Offer;
        if !(offer && roster_seat(law, t, ws.as_ref())) || !seat_scopes(t, k, signed_by(t, k)).contains(&ws) {
            return None;
        }
    }
    if t.seat_kind() == SeatKind::Accept && t.signer() == k {
        match t.of() {
            Some(of) => t = *by.get(of)?,
            None => {
                let (obj, s) = (t.obj()?, t.scope()?);
                let roster = law.roster_seats.iter().any(|x| x == s.as_ref());
                return (roster && community(by, &obj)).then_some(obj);
            }
        }
    }
    if t.seat_kind() != SeatKind::Offer || !t.to().contains(k) {
        return None;
    }
    let obj = t.obj()?;
    (community(by, &obj) && roster_offer(law, t)).then_some(obj)
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
/// [`CutSpec`] states. An immutable snapshot: what it reads is fixed when built, and its answers are kept
/// once asked, so its fields are read through methods.
pub struct Seats<'c, 'a, R: SeatRow, S: CutSpec<R>> {
    c: &'c Concluded<'a, R>,
    cut: Cut<'c, 'a, R, S>,
    law: &'c SeatLaw,
    spec: &'c S,
    by: BTreeMap<&'a R::Id, &'a R>,
    stale: BTreeSet<usize>,
    /// The moderators' lone removals the end rule holds out of force over this set ([`removal_in_force`]):
    /// they end nothing here, and a reading of one line of the set (a tip, the fold) leaves them out too.
    dropped: BTreeSet<R::Id>,
    recs: Vec<Live<R::Id, R::Key, R::Word>>,
    /// Per live seat, whether it is a duty seat proper ([`duty_held`]): such a seat follows the folded roster.
    duty: Vec<bool>,
    /// [`Seats::tips`] and [`Seats::tips_common`] by object (and scope), kept once asked: the seats are fixed
    /// when built, and no reader enters either (the reader's line is in `stale`).
    tips_memo: RefCell<BTreeMap<ObjOf<R>, Vec<usize>>>,
    common_memo: CommonMemo<R>,
    fold_memo: CommonMemo<R>,
}

impl<'c, 'a, R: SeatRow, S: CutSpec<R>> Seats<'c, 'a, R, S> {
    /// Walk the live seats.
    pub fn new(c: &'c Concluded<'a, R>, law: &'c SeatLaw, spec: &'c S, own: Option<&R::Key>) -> Self {
        Self::build(c, law, spec, own, None, None)
    }

    /// [`Seats::new`], with the lone removals out of force given (`drop`) instead of judged over `c`: a reading
    /// of one line of a larger set, or (`Some` of none) of the set with every removal taken as made. `cache`:
    /// the members at a head, kept for every build below this one (the heads' pasts are the same in each), so a
    /// chain of lone removals is read in polynomial time.
    fn build(
        c: &'c Concluded<'a, R>,
        law: &'c SeatLaw,
        spec: &'c S,
        own: Option<&R::Key>,
        drop: Option<&BTreeSet<R::Id>>,
        cache: Option<&MembersAt<R>>,
    ) -> Self {
        let cut = Cut::new(c, spec);
        let g = &c.g;
        let by: BTreeMap<&'a R::Id, &'a R> = g.rows().iter().map(|r| (r.id(), *r)).collect();
        let cs = c.cs();
        // the concluded withdrawals by the row they withdraw, and the concluded acceptances by their signer
        let mut wd: BTreeMap<&R::Id, Vec<&R>> = BTreeMap::new();
        let mut acc: BTreeMap<&R::Key, Vec<usize>> = BTreeMap::new();
        // the holders' own ends of a stay as a member: (withdrawal, key, community)
        let mut left: Vec<(usize, &R::Key, ObjOf<R>)> = Vec::new();
        for &i in cs {
            let r = g.row(i);
            match r.seat_kind() {
                SeatKind::Withdraw => {
                    if let Some(t) = r.target() {
                        wd.entry(t).or_default().push(r);
                    }
                    if let Some(room) = stay_end(law, &by, r) {
                        left.push((i, r.signer(), room));
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
        // a withdrawal that names a scope ends that one seat of the row it withdraws
        let off_ended = |o: &R, k: &R::Key, sc: &R::Word| {
            wd_of(o.id()).iter().any(|w| {
                w.target() == Some(o.id())
                    && (w.signer() == k || (!o.to().contains(w.signer()) && o.conf() != Some(Conf::Group) && !eq(o)))
                    && w.scope().is_none_or(|ws| ws == sc)
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
        // a moderator's lone removal is an act under its `moderate` standing, live only while the end rule
        // says it is in force
        let local = MembersAt::<R>::default();
        let dropped = match drop {
            Some(d) => d.clone(),
            None => out_of_force(c, law, spec, own, &by, &unseats, cache.unwrap_or(&local)),
        };
        let unseats: Vec<(usize, Option<ObjOf<R>>)> = if dropped.is_empty() {
            unseats
        } else {
            unseats.into_iter().filter(|(u, _)| !dropped.contains(g.row(*u).id())).collect()
        };
        // a removal from the roster: of a member's seat, or of any seat the law names the roster's own
        let member = |s: Option<&R::Word>| {
            s.is_some_and(|x| x.as_ref() == "member" || law.roster_seats.iter().any(|r| r == x.as_ref()))
        };
        let unseated = |oi: usize, k: &R::Key, sc: &R::Word| {
            if unseats.is_empty() {
                return false;
            }
            let o = g.row(oi);
            let dutyish = law.is_duty(sc.as_ref(), &[]) || duty_seat(law, &by, o) || founding_duty(o, sc);
            let oo = o.obj();
            unseats.iter().any(|(u, uo)| {
                let (u, ur) = (*u, g.row(*u));
                let same = ur.to().contains(k) && *uo == oo;
                let held = same
                    && (ur.scope() == Some(sc)
                        || (dutyish
                            && member(ur.scope())
                            && oo.as_ref().is_some_and(|x| holds_roster(c, law, u, k, x))));
                held && g.in_past(oi, u)
            })
        };
        // a duty seat whose offer is in the past of its holder's own end of its stay as a member is ended by it
        let resigned = |oi: usize, k: &R::Key, sc: &R::Word| {
            if left.is_empty() {
                return false;
            }
            let o = g.row(oi);
            let oo = o.obj();
            duty_held(law, &by, o, sc)
                && left.iter().any(|(w, k2, room)| *k2 == k && oo.as_ref() == Some(room) && g.in_past(oi, *w))
        };
        // `signed`: whether k signed the offer, read by the caller once per offer's signer set
        let accepted = |o: &R, k: &R::Key, signed: bool| {
            if signed {
                return true;
            }
            if o.consent_one() {
                return o.conf() != Some(Conf::Seat);
            }
            acc.get(k).is_some_and(|accs| {
                accs.iter().any(|&a| {
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
                })
            })
        };
        // keys and scopes are borrowed from the rows through the walk, and copied once into each live seat
        let mut base: Vec<(usize, &'a R::Key, &'a R::Word)> = Vec::new();
        for &oi in cs {
            let o = g.row(oi);
            if o.seat_kind() != SeatKind::Offer || !cut.counts(oi) || stale.contains(&oi) {
                continue;
            }
            // an offer seating many keys reads its signers as a set, built once (not once per key)
            let many = o.to().len() > SIGNERS_SCANNED;
            let sig: BTreeSet<&R::Key> =
                if many { o.cosigners().iter().chain(core::iter::once(o.signer())).collect() } else { BTreeSet::new() };
            for k in o.to() {
                let signed = if many { sig.contains(k) } else { signed_by(o, k) };
                if !accepted(o, k, signed) {
                    continue;
                }
                for sc in seat_scopes(o, k, signed) {
                    if !off_ended(o, k, sc) && !unseated(oi, k, sc) && !resigned(oi, k, sc) {
                        base.push((oi, k, sc));
                    }
                }
            }
        }
        // one link per pass: at most `depth` links below a root
        type At<'r, I, K, W> = BTreeMap<(&'r I, &'r K, &'r W), (usize, Root<I, K>)>;
        // per (offer, key), the least depth any of its seats is at: what a seat conferred under it reads
        type Held<'r, I, K> = BTreeMap<(&'r I, &'r K), (usize, Root<I, K>)>;
        let walk = |base: &[(usize, &'a R::Key, &'a R::Word)]| {
            let mut at: At<'a, R::Id, R::Key, R::Word> = BTreeMap::new();
            let mut held: Held<'a, R::Id, R::Key> = BTreeMap::new();
            for _ in 0..(law.depth + 1) {
                let mut add: Vec<Step<'a, R>> = Vec::new();
                for &(oi, k, sc) in base {
                    let o = g.row(oi);
                    let key = (o.id(), k, sc);
                    if at.contains_key(&key) {
                        continue;
                    }
                    let obj = o.obj();
                    match o.conf() {
                        Some(Conf::Own) => {
                            let founding = obj == Some(Obj::Row(o.id().clone()));
                            let ok = founding
                                || !obj.as_ref().is_some_and(|x| founding_many(&by, x))
                                || matches!(&obj, Some(Obj::Row(f)) if held.contains_key(&(f, o.signer())));
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
                                if let (Some(up), Some(hit)) = (by.get(u), held.get(&(u, o.signer()))) {
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
                for ((i, k, sc), v) in add {
                    held.entry((i, k))
                        .and_modify(|h| {
                            if v.0 < h.0 {
                                *h = v.clone()
                            }
                        })
                        .or_insert_with(|| v.clone());
                    at.entry((i, k, sc)).or_insert(v);
                }
            }
            at
        };
        let mut at = walk(&base);
        // a duty seat stands only where its holder holds the roster's seat over the same community at this
        // reading. The walk is run again without the duty seats of keys that are not members, until none is
        // left (a seat under one falls too). Where no offer is a duty seat proper, nothing is run again.
        let held: Vec<bool> = base.iter().map(|&(oi, _, sc)| duty_held(law, &by, g.row(oi), sc)).collect();
        if held.contains(&true) {
            let mut on: Vec<bool> = base.iter().map(|_| true).collect();
            loop {
                let mem: BTreeSet<(ObjOf<R>, &R::Key)> = at
                    .keys()
                    .filter_map(|&(oid, k, sc)| {
                        let o = by[oid];
                        if roster_seat(law, o, sc.as_ref()) {
                            o.obj().map(|x| (x, k))
                        } else {
                            None
                        }
                    })
                    .collect();
                let mut dropped = false;
                for (j, &(oi, k, _)) in base.iter().enumerate() {
                    if on[j] && held[j] && !g.row(oi).obj().is_some_and(|x| mem.contains(&(x, k))) {
                        on[j] = false;
                        dropped = true;
                    }
                }
                if !dropped {
                    break;
                }
                let kept: Vec<(usize, &'a R::Key, &'a R::Word)> =
                    base.iter().zip(&on).filter(|(_, keep)| **keep).map(|(b, _)| *b).collect();
                at = walk(&kept);
            }
        }
        let recs: Vec<Live<R::Id, R::Key, R::Word>> = at
            .into_iter()
            .filter_map(|((oid, k, sc), (depth, root))| {
                let o = by[oid];
                Some(Live { offer: oid.clone(), k: k.clone(), scope: sc.clone(), obj: o.obj()?, depth, root })
            })
            .collect();
        let duty = recs.iter().map(|r| by.get(&r.offer).is_some_and(|o| duty_held(law, &by, *o, &r.scope))).collect();
        Seats {
            c,
            cut,
            law,
            spec,
            by,
            stale,
            dropped,
            recs,
            duty,
            tips_memo: RefCell::default(),
            common_memo: RefCell::default(),
            fold_memo: RefCell::default(),
        }
    }

    /// The concluded set.
    pub fn c(&self) -> &'c Concluded<'a, R> {
        self.c
    }
    /// The cut over it.
    pub fn cut(&self) -> &Cut<'c, 'a, R, S> {
        &self.cut
    }
    /// The counted acts that do not count for this reader.
    pub fn stale(&self) -> &BTreeSet<usize> {
        &self.stale
    }
    /// Every live seat.
    pub fn recs(&self) -> &[Live<R::Id, R::Key, R::Word>] {
        &self.recs
    }

    fn has(&self, rec: &Live<R::Id, R::Key, R::Word>, s: &str) -> bool {
        let sc = rec.scope.as_ref();
        if s == "duty" && self.law.is_duty(sc, &declared(&self.by, &rec.obj)) {
            return true; // a holder of any one duty is a duty holder
        }
        covers(sc, s) || self.law.holds.get(sc).is_some_and(|h| h.iter().any(|x| x == s))
    }

    /// A duty seat follows the folded roster: with several tips, its holder is among the members, or the
    /// agents, the fold seats. Any other seat is not asked.
    fn member(&self, i: usize) -> bool {
        let r = &self.recs[i];
        !self.duty[i]
            || self.tips_fold("member", &r.obj).is_none_or(|c| c.contains(&r.k))
            || self.tips_fold(AGENT, &r.obj).is_some_and(|c| c.contains(&r.k))
    }

    /// The live seats that give scope `s` over `o` (rooted at `root`, when given), by index.
    fn giving<'s>(
        &'s self,
        s: &'s str,
        o: &'s ObjOf<R>,
        root: Option<&'s Root<R::Id, R::Key>>,
    ) -> impl Iterator<Item = &'s Live<R::Id, R::Key, R::Word>> + 's {
        self.recs
            .iter()
            .enumerate()
            .filter(move |(i, r)| r.obj == *o && self.has(r, s) && root.is_none_or(|x| r.root == *x) && self.member(*i))
            .map(|(_, r)| r)
    }

    /// Whether key `k` stands in scope `s` over `o` (rooted at `root`, when given). With several tips, a key
    /// stands only if the fold of their changes seats it ([`Seats::tips_fold`]).
    pub fn stands(&self, k: &R::Key, s: &str, o: &ObjOf<R>, root: Option<&Root<R::Id, R::Key>>) -> bool {
        let any = self.giving(s, o, root).any(|r| r.k == *k);
        any && self.tips_fold(s, o).is_none_or(|c| c.contains(k))
    }

    /// The room's whole roster over `o`: the keys holding `member` and the keys holding [`AGENT`] (CC 4.5.13).
    /// Content, wraps and audience read it. No count reads it: a count is taken of the members (or the scope
    /// it names) less the agents.
    pub fn roster(&self, o: &ObjOf<R>) -> BTreeSet<R::Key> {
        let mut m = self.holders("member", o, None);
        m.extend(self.holders(AGENT, o, None));
        m
    }

    /// The keys holding scope `s` over `o`.
    pub fn holders(&self, s: &str, o: &ObjOf<R>, root: Option<&Root<R::Id, R::Key>>) -> BTreeSet<R::Key> {
        let got: BTreeSet<R::Key> = self.giving(s, o, root).map(|r| r.k.clone()).collect();
        match self.tips_fold(s, o) {
            None => got,
            Some(c) => got.intersection(&c).cloned().collect(),
        }
    }

    /// The single holder, where the seat is single-valued (an owner): two live holders is none.
    pub fn one(&self, s: &str, o: &ObjOf<R>) -> Option<R::Key> {
        // the one distinct key, found by reference; only the answer is copied
        crate::ops::one(self.recs.iter().filter(|r| r.obj == *o && self.has(r, s)).map(|r| &r.k)).cloned()
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

    /// The seats read over one line of the concluded rows (the rows at `ids`), with the offers that seat each
    /// key in scope `s` over `o`.
    fn line_seats(&self, ids: &[usize], s: &str, o: &ObjOf<R>) -> BTreeMap<R::Key, BTreeSet<R::Id>> {
        let g = &self.c.g;
        let sc = Concluded::with(Graph::new(ids.iter().map(|&q| g.row(q))), None);
        let q = Seats::build(&sc, self.law, self.spec, None, Some(&self.dropped), None);
        let mut seated: BTreeMap<R::Key, BTreeSet<R::Id>> = BTreeMap::new();
        for r in q.recs.iter().filter(|r| r.obj == *o && q.has(r, s)) {
            seated.entry(r.k.clone()).or_default().insert(r.offer.clone());
        }
        seated
    }

    /// With several tips, the keys holding `s` over `o` when every tip's changes are folded (KERNEL.md section
    /// 7; `models/roster_fork/fold.py`); `None` with one tip or none.
    ///
    /// * A key every tip seats is in.
    /// * A key some tip's line removed is out, unless a later addition of it has that removal in its past. So a
    ///   key one tip admits and another removes is out.
    /// * A key some tip adds is in where the counted offer that adds it meets its count on the voices of keys
    ///   the fold seats, over the members at its heads that the fold seats: a least fixed point from the common
    ///   keys.
    /// * Tips that differ in protocol or policy ([`SeatRow::regime`]) do not fold: the answer is then the keys
    ///   common to them ([`Seats::tips_common`]).
    pub fn tips_fold(&self, s: &str, o: &ObjOf<R>) -> Option<BTreeSet<R::Key>> {
        let at = (String::from(s), o.clone());
        if let Some(t) = self.fold_memo.borrow().get(&at) {
            return t.clone();
        }
        let t = self.fold_of(s, o, &at);
        self.fold_memo.borrow_mut().insert(at, t.clone());
        t
    }

    fn fold_of(&self, s: &str, o: &ObjOf<R>, key: &(String, ObjOf<R>)) -> Option<BTreeSet<R::Key>> {
        let tp = self.tips(o);
        if tp.len() <= 1 {
            return None;
        }
        let g = &self.c.g;
        let lines: Vec<Line<R>> = tp
            .iter()
            .map(|&t| {
                let ids: Vec<usize> = self.c.cs().iter().copied().filter(|&q| q == t || g.in_past(q, t)).collect();
                let seated = self.line_seats(&ids, s, o);
                (ids, seated)
            })
            .collect();
        let mut common: BTreeSet<R::Key> = lines[0].1.keys().cloned().collect();
        let mut union: BTreeSet<R::Key> = BTreeSet::new();
        for (_, sd) in &lines {
            common.retain(|k| sd.contains_key(k));
            union.extend(sd.keys().cloned());
        }
        let regimes: BTreeSet<Option<&R::Word>> = tp.iter().map(|&t| g.row(t).regime()).collect();
        if regimes.len() > 1 {
            return Some(common); // tips that differ in protocol or policy wait
        }
        // k is seated at some tip by an offer that every other line either never held k against, or removed k
        // in that offer's past
        // per line, the keys any of its offers over `o` names: a line outside this set never seated k, so it
        // cannot have removed k, and no seats need reading for it
        let named: Vec<BTreeSet<&R::Key>> = lines
            .iter()
            .map(|(ids, _)| {
                ids.iter()
                    .map(|&q| g.row(q))
                    .filter(|r| r.seat_kind() == SeatKind::Offer && r.obj().as_ref() == Some(o))
                    .flat_map(|r| r.to().iter())
                    .collect()
            })
            .collect();
        let survives = |k: &R::Key| {
            lines.iter().any(|(_, sd)| {
                sd.get(k).is_some_and(|offs| {
                    offs.iter().any(|off| {
                        let Some(oi) = g.idx(off) else { return false };
                        lines.iter().zip(&named).all(|((ids2, sd2), named2)| {
                            if sd2.contains_key(k) || !named2.contains(k) {
                                return true;
                            }
                            if ids2.contains(&oi) {
                                return false; // this line ended the very seat
                            }
                            let seen: Vec<usize> = ids2.iter().copied().filter(|&q| g.in_past(q, oi)).collect();
                            !self.line_seats(&seen, s, o).contains_key(k) // else removed beside it
                        })
                    })
                })
            })
        };
        let cand: Vec<R::Key> = union.iter().filter(|k| !common.contains(*k) && survives(k)).cloned().collect();
        // every counted offer that adds k meets its count on the voices of keys the fold seats, over the
        // members at its heads that the fold seats
        let members: MembersAt<R> = MembersAt::default();
        let count_holds = |k: &R::Key, seated: &BTreeSet<R::Key>| {
            let offs: BTreeSet<&R::Id> = lines.iter().filter_map(|(_, sd)| sd.get(k)).flatten().collect();
            offs.into_iter().all(|off| {
                let Some(i) = g.idx(off) else { return false };
                let r = g.row(i);
                if r.conf() != Some(Conf::Group) {
                    return seated.contains(r.signer()) || !union.contains(r.signer());
                }
                if authored_head(self.law, r) {
                    return true; // an outsider's own admission: its own signature is its count
                }
                let anc: Vec<usize> = self.c.cs().iter().copied().filter(|&q| g.in_past(q, i)).collect();
                let p = Past::new(g, i, &anc);
                let Some(obj) = r.obj() else { return false };
                let over = r.over().unwrap_or(obj);
                let counted = r.counted().map(|c| c.as_ref()).unwrap_or("member");
                let ok = if over == *o && counted == s { Some(seated.clone()) } else { self.tips_fold(counted, &over) };
                let mut mem = count_members_with(&p, self.law, self.spec, Some(&members));
                if let Some(ok) = ok {
                    mem.retain(|m| ok.contains(m));
                }
                let pol = self.law.policy_of(r.policy().map(|x| x.as_ref()));
                // a re-seating's voices are the objections it names, counted over the members the fold seats
                let v = if pol == Some(Policy::Lift) {
                    let Some((author, v)) = lift_voices_with(&p, self.law, self.spec, Some(&members)) else {
                        return false;
                    };
                    mem.remove(&author); // the removal's author apart (the key removed is an agent's: in no count)
                    v
                } else {
                    voices(r, &p)
                };
                match pol {
                    Some(Policy::Ranked) => true, // an election's ballots are read by the seat rule alone
                    _ => count_of(pol, true, r.to(), &mem, &v, r.need(), |x| {
                        r.weights().iter().find(|(w, _)| w == x).map_or(0, |(_, n)| *n)
                    }),
                }
            })
        };
        // a count over this scope asked meanwhile reads the common keys
        self.fold_memo.borrow_mut().insert(key.clone(), Some(common.clone()));
        let mut got = common;
        loop {
            // least fixed point: a voice counts once its key is in
            let more: Vec<R::Key> =
                cand.iter().filter(|k| !got.contains(*k) && count_holds(k, &got)).cloned().collect();
            if more.is_empty() {
                break;
            }
            got.extend(more);
        }
        Some(got)
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
            let q = Seats::build(&sc, self.law, self.spec, None, Some(&self.dropped), None);
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

/// Seats read **at a held row** (0.3): the instant is the one row `at` states ([`crate::Dated`]), never a
/// clock. A seat counts at that instant only when the offer that seats it covers it: stated at or before it,
/// and not ended by it (`asserted_at <= t < valid_until`, [`crate::covers_at`]). An owner's standing judged at
/// the row being admitted is `holders_at(owner, node, None, admitted)`. The tip reading is the fold
/// ([`Seats::tips_fold`]).
///
/// Only the seating offer's own instants are read. A seat conferred under an offer whose own standing ended is
/// not ended by it here; that chain is the conferring offer's `valid_until`, which the caller states on the
/// conferred offer when it applies.
impl<'c, 'a, R: SeatRow + crate::Dated, S: CutSpec<R>> Seats<'c, 'a, R, S> {
    fn offer_covers(&self, offer: &R::Id, t: &R::Instant) -> bool {
        let g = &self.c.g;
        g.idx(offer).is_some_and(|i| {
            let r = g.row(i);
            crate::covers_at(r.asserted_at(), r.valid_until(), t)
        })
    }

    /// The keys holding scope `s` over `o` at the instant row `at` states; `None` when `at` is not held or
    /// states no instant.
    pub fn holders_at(
        &self,
        s: &str,
        o: &ObjOf<R>,
        root: Option<&Root<R::Id, R::Key>>,
        at: &R::Id,
    ) -> Option<BTreeSet<R::Key>> {
        let t = self.c.g.instant_of(at)?;
        let got: BTreeSet<R::Key> =
            self.giving(s, o, root).filter(|r| self.offer_covers(&r.offer, &t)).map(|r| r.k.clone()).collect();
        Some(match self.tips_fold(s, o) {
            None => got,
            Some(c) => got.intersection(&c).cloned().collect(),
        })
    }

    /// Whether key `k` stands in scope `s` over `o` at the instant row `at` states; `None` when `at` is not
    /// held or states no instant.
    pub fn stands_at(
        &self,
        k: &R::Key,
        s: &str,
        o: &ObjOf<R>,
        root: Option<&Root<R::Id, R::Key>>,
        at: &R::Id,
    ) -> Option<bool> {
        let t = self.c.g.instant_of(at)?;
        let any = self.giving(s, o, root).any(|r| r.k == *k && self.offer_covers(&r.offer, &t));
        Some(any && self.tips_fold(s, o).is_none_or(|c| c.contains(k)))
    }
}

/// Whether unseat `u` cuts a roster seat key `k` holds over `obj`: an offer in `u`'s past seats `k` in the
/// unseat's scope (or it is the founding row, holding `member`, and the scope is `member`). A cut of a roster
/// scope the key does not hold ends no stay, and so no duty seat.
fn holds_roster<R: SeatRow>(c: &Concluded<'_, R>, law: &SeatLaw, u: usize, k: &R::Key, obj: &ObjOf<R>) -> bool {
    let g = &c.g;
    let Some(us) = g.row(u).scope() else { return false };
    c.cs().iter().copied().any(|q| {
        let m = g.row(q);
        m.seat_kind() == SeatKind::Offer
            && m.obj().as_ref() == Some(obj)
            && m.to().contains(k)
            && g.in_past(q, u)
            && (m.scope() == Some(us) || (us.as_ref() == "member" && founding(m) && roster_offer(law, m)))
    })
}

/// Whether unseat `u` (a row of `c` that counts) is a moderator's lone removal of an agent's key made under the
/// remover's standing: it concludes as a lone removal, and the room's count of it is not met (a removal the
/// persons' count carries is the count's act, not the moderator's).
fn lone_act<R: SeatRow, S: CutSpec<R>>(
    c: &Concluded<'_, R>,
    u: usize,
    law: &SeatLaw,
    spec: &S,
    cache: &MembersAt<R>,
) -> bool {
    let g = &c.g;
    let r = g.row(u);
    if r.conf() != Some(Conf::Group) || r.to().len() != 1 || r.scope().map(|s| s.as_ref()) != Some(AGENT) {
        return false;
    }
    let anc: Vec<usize> = c.cs().iter().copied().filter(|&q| g.in_past(q, u)).collect();
    let p = Past::new(g, u, &anc);
    lone_removal(r, &p, law, spec, Some(cache)) && !count_met(&p, law, spec, Some(cache))
}

/// The lone removals among `unseats` that the end rule holds out of force over `c` ([`removal_in_force`]).
fn out_of_force<R: SeatRow, S: CutSpec<R>>(
    c: &Concluded<'_, R>,
    law: &SeatLaw,
    spec: &S,
    own: Option<&R::Key>,
    by: &BTreeMap<&R::Id, &R>,
    unseats: &[(usize, Option<ObjOf<R>>)],
    cache: &MembersAt<R>,
) -> BTreeSet<R::Id> {
    let g = &c.g;
    let acts: Vec<usize> = unseats.iter().map(|(u, _)| *u).filter(|&u| lone_act(c, u, law, spec, cache)).collect();
    if acts.is_empty() {
        return BTreeSet::new();
    }
    let none = BTreeSet::new();
    let now = Seats::build(c, law, spec, own, Some(&none), Some(cache));
    acts.into_iter()
        .filter(|&x| !removal_in_force(c, x, law, spec, by, unseats, &now, cache))
        .map(|x| g.row(x).id().clone())
        .collect()
}

/// CC 4.5.13 read with the end rule (CC 2.4.1.1, CC 4.5.5; `conferral`, rules E2 to E8, re-expressed over
/// seat rows): a moderator's lone removal `x` is an act under its `moderate` standing.
///
/// * E7: a seat that gave the remover `moderate` at the heads `x` names is live now (`now`, the seats with every
///   removal taken as made) and no end of it is held: in force. A seat taken up after `x`'s head authorises
///   nothing earlier, and nothing puts `x` back in force once each such seat has an end held (CC 2.4.1.1: "A
///   receipt ... revives no act"): not the same offer accepted again, not a new conferral. An end in the past
///   of the heads `x` names is not read (the seat was live there again).
/// * The ends of its standing held: a withdrawal of a standing offer by its holder (or by the conferrer of
///   an offer that is not counted), of the holder's acceptance of one, or of the holder's stay; a counted
///   unseat that cuts the holder's standing seat or its roster seat with a standing offer in its past. The
///   standing is the seats that give the remover `moderate` at the heads `x` names.
/// * E4: an end in `x`'s past: not in force (not counted). E3: `x` names a head that has every head of the
///   end's in its past (`h_e`: a counted end's heads; a withdrawal's newest counted acts on the room): not in
///   force (not counted).
/// * E8: otherwise in force only under a receipt of `x` (a [`SeatKind::Ack`] whose `of` is `x`) by a duty
///   holder at the heads `x` names other than the remover, without the end in its past. E2: else not in force.
///
/// With several ends held, in force only where each keeps it. Where the standing is gone and no end of it is
/// held, E2 and E8 with no end.
#[allow(clippy::too_many_arguments)]
fn removal_in_force<R: SeatRow, S: CutSpec<R>>(
    c: &Concluded<'_, R>,
    x: usize,
    law: &SeatLaw,
    spec: &S,
    by: &BTreeMap<&R::Id, &R>,
    unseats: &[(usize, Option<ObjOf<R>>)],
    now: &Seats<'_, '_, R, S>,
    cache: &MembersAt<R>,
) -> bool {
    let g = &c.g;
    let xr = g.row(x);
    let Some(obj) = xr.obj() else { return true };
    let m = xr.signer();
    // the standing at the heads x names, and the duty holders there
    let mut standing: BTreeSet<SeatOf<R>> = BTreeSet::new();
    let mut duty: Option<BTreeSet<R::Key>> = None;
    for h in xr.head() {
        let Some(hi) = g.idx(h) else { continue };
        // read once per (head, object, remover) for every build that shares the cache: the build of a head's
        // past holds lone removals of its own, each read here in turn, and unkept that is a doubling per row
        let key = (h.clone(), obj.clone(), m.clone());
        let known = cache.standing.borrow().get(&key).cloned();
        let (st, d) = match known {
            Some(v) => v,
            None => {
                let sub: Vec<&R> =
                    c.cs().iter().copied().filter(|&q| q == hi || g.in_past(q, hi)).map(|q| g.row(q)).collect();
                let sc = Concluded::with(Graph::new(sub), None);
                let q = Seats::build(&sc, law, spec, None, None, Some(cache));
                let st: BTreeSet<SeatOf<R>> = q
                    .recs
                    .iter()
                    .filter(|r| r.k == *m && r.obj == obj && q.has(r, "moderate"))
                    .map(|r| (r.offer.clone(), r.scope.clone()))
                    .collect();
                let v = (st, q.holders("duty", &obj, None));
                cache.standing.borrow_mut().insert(key, v.clone());
                v
            }
        };
        standing.extend(st);
        duty = Some(match duty {
            None => d,
            Some(before) => before.intersection(&d).cloned().collect(),
        });
    }
    let mut duty = duty.unwrap_or_default();
    duty.remove(m); // never the remover's own receipt
    let acks: Vec<usize> = c
        .cs()
        .iter()
        .copied()
        .filter(|&q| {
            let qr = g.row(q);
            qr.seat_kind() == SeatKind::Ack && qr.of() == Some(xr.id()) && duty.contains(qr.signer())
        })
        .collect();
    let kept = |e: Option<usize>| acks.iter().any(|&q| e.is_none_or(|e| !g.in_past(e, q)));
    // the ends of the standing held
    let ids: BTreeSet<&R::Id> = standing.iter().map(|(o, _)| o).collect();
    let after = |e: usize| ids.iter().any(|o| g.idx(o).is_some_and(|oi| g.in_past(oi, e)));
    let roster = |s: Option<&R::Word>| {
        s.is_some_and(|x| x.as_ref() == "member" || law.roster_seats.iter().any(|r| r == x.as_ref()))
    };
    // each end held, with the standing seats it ends
    let of = |pick: &dyn Fn(&SeatOf<R>) -> bool| -> BTreeSet<SeatOf<R>> {
        standing.iter().filter(|s| pick(s)).cloned().collect()
    };
    let before = |o: &R::Id, e: usize| g.idx(o).is_some_and(|oi| g.in_past(oi, e));
    let mut found: Vec<(usize, BTreeSet<SeatOf<R>>)> = Vec::new();
    for &w in c.cs() {
        let wr = g.row(w);
        if wr.seat_kind() != SeatKind::Withdraw {
            continue;
        }
        let Some(t) = wr.target().and_then(|t| by.get(t)) else { continue };
        let offer_end = t.seat_kind() == SeatKind::Offer
            && ids.contains(t.id())
            && wr.scope().is_none_or(|ws| standing.contains(&(t.id().clone(), ws.clone())))
            && (wr.signer() == m
                || (!t.to().contains(wr.signer()) && t.conf() != Some(Conf::Group) && !duty_seat(law, by, *t)));
        let accept_end = t.seat_kind() == SeatKind::Accept
            && t.signer() == m
            && wr.signer() == m
            && t.of().is_some_and(|o| ids.contains(o));
        let stay = wr.signer() == m && stay_end(law, by, wr).as_ref() == Some(&obj) && after(w);
        if offer_end {
            found.push((w, of(&|s| s.0 == *t.id() && wr.scope().is_none_or(|ws| *ws == s.1))));
        } else if accept_end {
            found.push((w, of(&|s| Some(&s.0) == t.of())));
        } else if stay {
            found.push((w, of(&|s| before(&s.0, w))));
        }
    }
    for (u, uo) in unseats {
        let ur = g.row(*u);
        if *u == x || !ur.to().contains(m) || uo.as_ref() != Some(&obj) || !after(*u) {
            continue;
        }
        if roster(ur.scope()) && holds_roster(c, law, *u, m, &obj) {
            found.push((*u, of(&|s| before(&s.0, *u))));
        } else if standing.iter().any(|(_, sc)| ur.scope() == Some(sc)) {
            found.push((*u, of(&|s| before(&s.0, *u) && ur.scope() == Some(&s.1))));
        }
    }
    // an end in the past of the head x names did not end the standing live there (a seat taken up again)
    found.retain(|(e, _)| !xr.head().iter().all(|h| g.idx(h).is_some_and(|hi| hi == *e || g.in_past(*e, hi))));
    // E7: a seat that gave the remover `moderate` at x's head is live and has no end held. Nothing else puts the
    // removal back in force: not the same offer accepted again, not a new conferral (CC 2.4.1.1)
    let ended: BTreeSet<&SeatOf<R>> = found.iter().flat_map(|(_, sc)| sc.iter()).collect();
    let live: BTreeSet<(&R::Id, &R::Word)> =
        now.recs.iter().filter(|r| r.k == *m && r.obj == obj).map(|r| (&r.offer, &r.scope)).collect();
    if now.stands(m, "moderate", &obj, None)
        && standing.iter().any(|s| live.contains(&(&s.0, &s.1)) && !ended.contains(s))
    {
        return true;
    }
    let ends: Vec<usize> = found.iter().map(|(e, _)| *e).collect();
    if ends.is_empty() {
        return kept(None);
    }
    // h_e: the heads a counted end names; for a withdrawal, the newest counted acts on the room in its past
    // (None where a head the end names is not held: that makes nothing later)
    let head_of = |e: usize| -> Option<Vec<usize>> {
        let er = g.row(e);
        if er.seat_kind() == SeatKind::Unseat {
            return er.head().iter().map(|h| g.idx(h)).collect();
        }
        let acts: Vec<usize> = c
            .cs()
            .iter()
            .copied()
            .filter(|&q| {
                let qr = g.row(q);
                g.in_past(q, e)
                    && matches!(qr.seat_kind(), SeatKind::Offer | SeatKind::Unseat)
                    && qr.obj().as_ref() == Some(&obj)
                    && (qr.conf() == Some(Conf::Group) || founding(qr))
            })
            .collect();
        Some(g.frontier(&acts))
    };
    let hx: Vec<usize> = xr.head().iter().filter_map(|h| g.idx(h)).collect();
    let later = |he: Option<Vec<usize>>| {
        he.is_some_and(|he| !he.is_empty() && hx.iter().any(|&h| he.iter().all(|&e| g.in_past(e, h))))
    };
    ends.iter().all(|&e| !g.in_past(e, x) && !later(head_of(e)) && kept(Some(e)))
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

/// A head one key wrote: an outsider's own admission to an open room (`open:self_admit`, signed by the key it
/// seats). It narrows no count but by its own signer.
fn authored_head<R: SeatRow>(law: &SeatLaw, r: &R) -> bool {
    r.seat_kind() == SeatKind::Offer
        && law.policy_of(r.policy().map(|x| x.as_ref())) == Some(Policy::SelfAdmit)
        && r.to().len() == 1
        && r.to()[0] == *r.signer()
}

/// The heads a count is read over: the heads named, with each authored head replaced by the heads it names in
/// turn, and then only the newest of them (one that is in another's past is dropped). Unchanged where no head
/// named is an authored one.
fn counted_heads<'r, 'h, R: SeatRow + 'r>(
    law: &SeatLaw,
    heads: &'h [R::Id],
    row: &dyn Fn(&R::Id) -> Option<&'r R>,
    past: &dyn Fn(&R::Id, &R::Id) -> bool,
) -> alloc::borrow::Cow<'h, [R::Id]> {
    if !heads.iter().any(|h| row(h).is_some_and(|r| authored_head(law, r))) {
        return alloc::borrow::Cow::Borrowed(heads); // the usual case: nothing is copied
    }
    let mut todo: Vec<R::Id> = heads.to_vec();
    let mut seen: BTreeSet<R::Id> = BTreeSet::new();
    let mut kept: Vec<R::Id> = Vec::new();
    while let Some(h) = todo.pop() {
        if !seen.insert(h.clone()) {
            continue;
        }
        match row(&h) {
            Some(r) if authored_head(law, r) => todo.extend(r.head().iter().cloned()),
            _ => kept.push(h),
        }
    }
    let newest: Vec<R::Id> = kept.iter().filter(|a| !kept.iter().any(|b| *a != b && past(a, b))).cloned().collect();
    alloc::borrow::Cow::Owned(newest)
}

fn concluded_over<'a, R: Row>(rows: impl IntoIterator<Item = &'a R>) -> Concluded<'a, R> {
    Concluded::with(Graph::new(rows), None)
}

/// The live `scope` seats over `obj`, read from the rows in the past of the heads only (`p`: a row's
/// concluded ancestors). Several heads: the keys common to the newest counted of them. A head one key wrote
/// (an outsider's own admission) is read through to the heads it names, so it narrows no count.
pub fn members_at<R: SeatRow, S: CutSpec<R>>(
    p: &Past<'_, '_, R>,
    law: &SeatLaw,
    spec: &S,
    obj: &ObjOf<R>,
    heads: &[R::Id],
    scope: &str,
) -> BTreeSet<R::Key> {
    members_at_c(p, law, spec, obj, heads, scope, None)
}

/// [`members_at`], each head's seats built with `cache` for the builds below it.
fn members_at_c<R: SeatRow, S: CutSpec<R>>(
    p: &Past<'_, '_, R>,
    law: &SeatLaw,
    spec: &S,
    obj: &ObjOf<R>,
    heads: &[R::Id],
    scope: &str,
    cache: Option<&MembersAt<R>>,
) -> BTreeSet<R::Key> {
    // as members_in over p's rows with p's closure, read by index: a head's past is taken whole once
    let g = p.graph();
    let anc = p.ancestors();
    let heads = counted_heads(law, heads, &|h| g.idx(h).map(|i| g.row(i)), &|a, b| match (g.idx(a), g.idx(b)) {
        (Some(a), Some(b)) => g.in_past(a, b),
        _ => false,
    });
    let mut out: Option<BTreeSet<R::Key>> = None;
    for h in heads.iter() {
        let Some(hi) = g.idx(h).filter(|hi| anc.binary_search(hi).is_ok()) else { return BTreeSet::new() };
        let past = g.ancestors(hi);
        let sc = concluded_over(anc.iter().filter(|&&q| q == hi || past.has(q)).map(|&q| g.row(q)));
        let m = Seats::build(&sc, law, spec, None, None, cache).holders(scope, obj, None);
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
    let heads = counted_heads(law, heads, &|h| rows.iter().copied().find(|q| q.id() == h), past);
    for h in heads.iter() {
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
/// that key (`RosterHead.leaving_binds_by_past`). A count over the duty holders also leaves out
/// [`stay_ended_in_past`], which [`count_members`] subtracts.
pub fn left_in_past<R: SeatRow>(p: &Past<'_, '_, R>, obj: &ObjOf<R>, scope: &str) -> BTreeSet<R::Key> {
    let mut out = BTreeSet::new();
    for w in p.rows() {
        if w.seat_kind() != SeatKind::Withdraw {
            continue;
        }
        let Some(t) = w.target().and_then(|t| p.get(t)) else { continue };
        // a withdrawal that names a scope leaves that one seat of the row it withdraws (a founder's duty laid down)
        let ts = w.scope().or(t.scope());
        if t.obj().is_some_and(|x| x != *obj) || ts.is_some_and(|s| s.as_ref() != scope) {
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

/// The keys whose own end of a stay as a member of `obj` is among `p` (a counted row's past) with no
/// admission of the key after it there: a count over the duty holders with such an end in its past does not
/// count that key, since the end ended its duty seats. Empty where `obj` is not a community. A counted removal needs no such reading: it is a head, read by [`members_at`].
pub fn stay_ended_in_past<R: SeatRow>(p: &Past<'_, '_, R>, law: &SeatLaw, obj: &ObjOf<R>) -> BTreeSet<R::Key> {
    let by: BTreeMap<&R::Id, &R> = p.rows().map(|q| (q.id(), q)).collect();
    let mut out = BTreeSet::new();
    if !community(&by, obj) {
        return out;
    }
    for w in p.rows().filter(|w| w.seat_kind() == SeatKind::Withdraw) {
        if stay_end(law, &by, w).as_ref() != Some(obj) {
            continue;
        }
        let k = w.signer();
        let back = p.rows().any(|m| {
            m.seat_kind() == SeatKind::Offer
                && m.obj().as_ref() == Some(obj)
                && m.to().contains(k)
                && roster_offer(law, m)
                && p.past(w.id(), m.id())
        });
        if !back {
            out.insert(k.clone());
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
    // a cosignature that is a voice is a row the counted row names: read those, not every row of its past
    for n in r.names() {
        let Some(c) = p.get(n) else { continue };
        if c.seat_kind() == SeatKind::Cosign && c.of() == Some(content) && heads.iter().all(|h| c.names().contains(*h))
        {
            v.insert(c.signer().clone());
        }
    }
    v
}

/// CC 4.5.13: a moderator of the room removes an AI agent's key alone. `r` (the row of `p`, or a row in its
/// past) is a counted unseat of one key's [`AGENT`] seat (the seat's scope says whose key it is), and its
/// signer holds `moderate` over the object at the head it names.
fn lone_removal<R: SeatRow, S: CutSpec<R>>(
    r: &R,
    p: &Past<'_, '_, R>,
    law: &SeatLaw,
    spec: &S,
    cache: Option<&MembersAt<R>>,
) -> bool {
    if r.seat_kind() != SeatKind::Unseat || r.conf() != Some(Conf::Group) || r.to().len() != 1 {
        return false;
    }
    let (Some(scope), Some(obj)) = (r.scope(), r.obj()) else { return false };
    // an unseat of an agent's seat, of a key that holds one at the head the row names: a person's key is not
    // removed so, whatever scope the row states. This is also what makes a lift restore and not admit.
    let agent = scope.as_ref() == AGENT;
    if !agent || !members_at_with(p, law, spec, &obj, r.head(), AGENT, cache).contains(&r.to()[0]) {
        return false;
    }
    members_at_with(p, law, spec, &obj, r.head(), "moderate", cache).contains(r.signer())
}

/// The voices of a re-seating row (`p.row()`, a counted offer of [`Policy::Lift`]), or `None` where it is
/// none. The row cites a removal ([`SeatRow::content`]) that is a moderator's lone removal of an agent's key
/// (an unseat of its [`AGENT`] seat), of the same key, scope and object, and names the head that removal names.
/// Its voices are the signers of the cosignatures it names whose `of` is the removal: the caller presents
/// each objection to the removal (an answer `object` in its `moderation_overturn` window) as such a
/// cosignature. The removal's author is no voice. The row's own signers are no voices either.
///
/// Returns the removal's author and the voices. The count ([`Policy::Lift`]) is taken of the members at the
/// head (persons: the agents apart) less that author. The key removed is an agent's, so it is in no count
/// (an agent "acts under its own key and has no vote").
pub fn lift_voices<R: SeatRow, S: CutSpec<R>>(
    p: &Past<'_, '_, R>,
    law: &SeatLaw,
    spec: &S,
) -> Option<(R::Key, BTreeSet<R::Key>)> {
    lift_voices_with(p, law, spec, None)
}

fn lift_voices_with<R: SeatRow, S: CutSpec<R>>(
    p: &Past<'_, '_, R>,
    law: &SeatLaw,
    spec: &S,
    cache: Option<&MembersAt<R>>,
) -> Option<(R::Key, BTreeSet<R::Key>)> {
    let r = p.row();
    let rem = p.get(r.content()?)?;
    if r.seat_kind() != SeatKind::Offer || !lone_removal(rem, p, law, spec, cache) {
        return None;
    }
    if rem.obj() != r.obj() || rem.scope() != r.scope() || rem.to() != r.to() || rem.head() != r.head() {
        return None; // the same seat, at the head the removal names
    }
    let mut v = BTreeSet::new();
    for n in r.names() {
        let Some(c) = p.get(n) else { continue };
        if c.seat_kind() == SeatKind::Cosign && c.of() == Some(rem.id()) {
            v.insert(c.signer().clone());
        }
    }
    // the seat rule also takes the author out of the members counted over, which alone would leave it no
    // voice there; it is taken out here too for a caller that counts these voices over members of its own
    v.remove(rem.signer());
    Some((rem.signer().clone(), v))
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
    seat_rule_with(p, law, spec, other, None)
}

/// Conclude every kept row by [`seat_rule`] (`other` for a row the seat does not read; `root` as in
/// [`layers::conclude`](crate::layers::conclude)): the same conclusions, with the members at a head read once
/// per (heads, object, scope) over the whole pass.
///
/// Within one pass that is sound: a row concludes on its ancestors alone, so the concluded rows in a head's
/// past are fixed before any row naming the head is read, and `law` and `spec` are fixed. The cache lives and
/// dies with the call; it is not kept across calls, nor shared between readers (it reads none).
pub fn conclude<'a, R: SeatRow, S: CutSpec<R>>(
    kept_rows: impl IntoIterator<Item = &'a R>,
    law: &SeatLaw,
    spec: &S,
    other: &dyn Fn(&Past<'_, '_, R>) -> bool,
    root: Option<&dyn Fn(&R) -> bool>,
) -> Concluded<'a, R> {
    let cache = MembersAt::<R>::default();
    crate::layers::conclude(kept_rows, |p| seat_rule_with(p, law, spec, other, Some(&cache)), root)
}

/// The members at a head, kept per (sorted heads, object, scope) for one [`conclude`].
struct MembersAt<R: SeatRow> {
    memo: RefCell<MembersMemo<R>>,
    // per (head, object, key): the seats that give the key `moderate` at the head, and the duty holders there
    standing: RefCell<StandingMemo<R>>,
}

/// What [`removal_in_force`] reads of the seats at one head.
type StandingAt<R> = (BTreeSet<SeatOf<R>>, BTreeSet<<R as Row>::Key>);
type StandingMemo<R> = BTreeMap<(<R as Row>::Id, ObjOf<R>, <R as Row>::Key), StandingAt<R>>;

impl<R: SeatRow> Default for MembersAt<R> {
    fn default() -> Self {
        MembersAt { memo: RefCell::default(), standing: RefCell::default() }
    }
}

/// [`members_at`], through the pass's cache when there is one. A head that is not among the row's concluded
/// ancestors makes the set empty for that row alone, so such a call is answered and not kept.
fn members_at_with<R: SeatRow, S: CutSpec<R>>(
    p: &Past<'_, '_, R>,
    law: &SeatLaw,
    spec: &S,
    obj: &ObjOf<R>,
    heads: &[R::Id],
    scope: &str,
    cache: Option<&MembersAt<R>>,
) -> BTreeSet<R::Key> {
    let Some(cache) = cache else { return members_at(p, law, spec, obj, heads, scope) };
    if !heads.iter().all(|h| p.graph().idx(h).is_some_and(|hi| p.ancestors().binary_search(&hi).is_ok())) {
        return BTreeSet::new();
    }
    let mut hs = heads.to_vec();
    hs.sort();
    hs.dedup();
    let key = (hs, obj.clone(), String::from(scope));
    if let Some(m) = cache.memo.borrow().get(&key) {
        return m.clone();
    }
    let m = members_at_c(p, law, spec, obj, heads, scope, Some(cache));
    cache.memo.borrow_mut().insert(key, m.clone());
    m
}

/// The members a group-conferred offer or unseat `p.row()` is counted over, exactly as [`seat_rule`] reads
/// them: the live seats of its counted scope (default `member`) over its object (or `over`), at every head it
/// names ([`members_at`]: read from the concluded rows in each head's past, intersected over the heads), less
/// the keys holding [`AGENT`] at those heads (every count of a room is by person), less
/// the keys whose own leaving is in the row's past ([`left_in_past`]; for a count over the duty holders, the
/// end of a holder's stay as a member too, [`stay_ended_in_past`]). With [`voices`], what
/// [`GroupCount`] needs. Empty for a row with no object.
pub fn count_members<R: SeatRow, S: CutSpec<R>>(p: &Past<'_, '_, R>, law: &SeatLaw, spec: &S) -> BTreeSet<R::Key> {
    count_members_with(p, law, spec, None)
}

/// The keys holding [`AGENT`] over `obj` at the heads: on the roster, and in no count. Empty with no row of that
/// scope among `p`'s.
fn agents_at_with<R: SeatRow, S: CutSpec<R>>(
    p: &Past<'_, '_, R>,
    law: &SeatLaw,
    spec: &S,
    obj: &ObjOf<R>,
    heads: &[R::Id],
    cache: Option<&MembersAt<R>>,
) -> BTreeSet<R::Key> {
    if !p.rows().any(|q| q.scope().is_some_and(|s| s.as_ref() == AGENT)) {
        return BTreeSet::new();
    }
    members_at_with(p, law, spec, obj, heads, AGENT, cache)
}

/// [`members_at`] of `scope` less the agents at the same heads: the keys a count of the room is taken of.
/// Every count of a room is by person (CC 4.5.13: an agent "has no vote"), so an agent's key is no voice and
/// is not counted over, whatever other seat it holds.
fn persons_at_with<R: SeatRow, S: CutSpec<R>>(
    p: &Past<'_, '_, R>,
    law: &SeatLaw,
    spec: &S,
    obj: &ObjOf<R>,
    heads: &[R::Id],
    scope: &str,
    cache: Option<&MembersAt<R>>,
) -> BTreeSet<R::Key> {
    let m = members_at_with(p, law, spec, obj, heads, scope, cache);
    if m.is_empty() || scope == AGENT {
        return m;
    }
    persons(m, &agents_at_with(p, law, spec, obj, heads, cache))
}

fn count_members_with<R: SeatRow, S: CutSpec<R>>(
    p: &Past<'_, '_, R>,
    law: &SeatLaw,
    spec: &S,
    cache: Option<&MembersAt<R>>,
) -> BTreeSet<R::Key> {
    let r = p.row();
    let Some(obj) = r.obj() else { return BTreeSet::new() };
    let over = r.over().unwrap_or(obj);
    let counted = r.counted().map(|c| c.as_ref()).unwrap_or("member");
    let mut mem = persons_at_with(p, law, spec, &over, r.head(), counted, cache);
    for k in left_in_past(p, &over, counted) {
        mem.remove(&k);
    }
    // a count over the duty holders: a holder whose own end of its stay as a member is in the row's past
    let duties: Vec<&str> = match &over {
        Obj::Row(i) => p.get(i).map_or(Vec::new(), |g| g.duties().iter().map(|d| d.as_ref()).collect()),
        Obj::Key(_) => Vec::new(),
    };
    if !mem.is_empty() && law.is_duty(counted, &duties) {
        for k in stay_ended_in_past(p, law, &over) {
            mem.remove(&k);
        }
    }
    mem
}

/// A counted row's count ([`Conf::Group`]), met over `p`: the lift, the ranked tally, the duty count, or the
/// policy's threshold over the persons at the heads the row names. [`seat_rule`]'s group arm, after a
/// moderator's lone removal is read.
fn count_met<R: SeatRow, S: CutSpec<R>>(
    p: &Past<'_, '_, R>,
    law: &SeatLaw,
    spec: &S,
    cache: Option<&MembersAt<R>>,
) -> bool {
    let r = p.row();
    let is_offer = r.seat_kind() == SeatKind::Offer;
    let Some(obj) = r.obj() else { return false };
    let pol = law.policy_of(r.policy().map(|x| x.as_ref()));
    if pol == Some(Policy::Lift) {
        // the overturn's count over the objections the row names, at the head the removal names
        // a lift restores and does not admit: the removal it cites is a lone removal, so the key held its
        // agent's seat at that head (lone_removal)
        let Some((author, v)) = lift_voices_with(p, law, spec, cache) else { return false };
        // the members are persons: the key removed is an agent's, no voice and not counted over
        let mut mem = persons_at_with(p, law, spec, &obj, r.head(), "member", cache);
        mem.remove(&author); // the author is not among the members the majority is taken of
        return count_of(pol, is_offer, r.to(), &mem, &v, None, |_| 0);
    }
    let mem = count_members_with(p, law, spec, cache);
    if pol == Some(Policy::Ranked) {
        // a ballot its signer withdrew in the row's past is none (CC 4.5.13: "Disagreeing ballots neither withdrawn
        // are no ballot until a withdrawal leaves one")
        let gone = |b: &R| {
            p.rows()
                .any(|w| w.seat_kind() == SeatKind::Withdraw && w.target() == Some(b.id()) && w.signer() == b.signer())
        };
        let over = r.over().unwrap_or(obj);
        // the members' count seats a holder only where none is left (CC 4.5.4 (v); rule 2: "While another duty
        // holder remains, a vacant seat is conferred under line (iv), and the community does not lock"): a duty
        // holder at the heads the row names, its own leaving not in the row's past, and the election seats nobody
        // read by person, as the duty counts are: an AI agent's key holding a duty is no holder here
        let mut holders = persons_at_with(p, law, spec, &over, r.head(), "duty", cache);
        for k in left_in_past(p, &over, "duty").into_iter().chain(stay_ended_in_past(p, law, &over)) {
            holders.remove(&k);
        }
        if !holders.is_empty() {
            return false;
        }
        let ballots: Vec<(R::Key, Vec<R::Key>)> = p
            .rows()
            .filter(|b| b.seat_kind() == SeatKind::Ballot && r.names().contains(b.id()) && mem.contains(b.signer()))
            .filter(|b| !gone(b))
            // a ballot ranking a key that is not counted over is not counted, the whole ballot (CC 3.1.4
            // `ballot:moderator`: "A ballot naming ... a non-member is kept and not counted"): the candidates are
            // the base, so an agent's key and a key whose own leaving is in the row's past are none
            .filter(|b| b.ranking().iter().all(|k| mem.contains(k)))
            .filter(|b| b.ranking().len() <= ELECTION_RANKS)
            .map(|b| (b.signer().clone(), b.ranking().to_vec()))
            .collect();
        // the one ranked row is the election, which declares no order: a tie for weakest seats nobody
        return is_offer && !ballots.is_empty() && ranked(&ballots, r.options(), 2, false).0.as_ref() == r.to().first();
    }
    let v = voices(r, p);
    let count = GroupCount { policy: pol, offer: is_offer, to: r.to(), members: &mem, voices: &v, need: r.need() };
    // a ranked count was answered above, so the count answers
    group_count(&count, |k| r.weights().iter().find(|(w, _)| w == k).map_or(0, |(_, x)| *x)).unwrap_or(false)
}

fn seat_rule_with<R: SeatRow, S: CutSpec<R>>(
    p: &Past<'_, '_, R>,
    law: &SeatLaw,
    spec: &S,
    other: &dyn Fn(&Past<'_, '_, R>) -> bool,
    cache: Option<&MembersAt<R>>,
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
                && !lone(law, spec, r, p, cache)
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
                    if !is_offer && lone_removal(r, p, law, spec, cache) {
                        return true; // CC 4.5.13: a moderator, an agent's key
                    }
                    count_met(p, law, spec, cache)
                }
                None => false,
            }
        }
        SeatKind::Accept => match r.of() {
            None => true,
            Some(o) => by.get(o).is_some_and(|o| o.to().contains(r.signer())),
        },
        SeatKind::Withdraw => match r.target().and_then(|t| by.get(t)) {
            Some(t) => signed_by(*t, r.signer()) || (t.seat_kind() == SeatKind::Offer && t.to().contains(r.signer())),
            None => false,
        },
        SeatKind::Cosign => true,
        _ => other(p),
    }
}

/// What a group's count reads, once the caller has resolved it: the count the policy row names, whether the
/// row is an offer (else an unseat), the keys it seats or removes, the members it is counted over and its
/// voices.
///
/// # Contract
///
/// [`group_count`] gives the seat rule's answer only for input read as the seat rule reads it. Nothing here
/// can check that without the rows, and a stale or partial roster is answered, not refused.
///
/// - `members` is [`count_members`]: the live seats of the counted scope read from the **concluded** rows in
///   each head's past, **intersected over every head** the row names (so tips wait and a waiting row counts
///   for nothing), **less the agents' keys at those heads** (the holders of [`AGENT`]; [`persons`]), **less
///   the keys whose own leaving is in the counted row's past** ([`left_in_past`]). It is
///   a function of the head *and the row*: cache [`members_at`] per head if you will, and subtract
///   `left_in_past` on every count (and, for a count over the duty holders, [`stay_ended_in_past`]).
/// - `voices` is [`voices`]: the row's signer, its cosigners, and the signers of the cosignatures it names
///   that name every head it is counted over.
/// - Under [`Policy::Lift`] the two are read otherwise: `voices` is [`lift_voices`] (the objections the row
///   names, the removal's author left out) and `members` is [`members_at`] at the head less the agents (the
///   key removed among them) and less that author, with no leaving subtracted. The seat rule asks besides
///   that the key seated held the seat it seats (`agent`) at that head.
/// - `to`, `members`, `voices` and the weights are in **one** key space. A caller counting persons (KERNEL.md
///   7b) collapses `to` the same way, once each: two devices of one person in `to` are one key.
#[derive(Clone, Copy, Debug)]
pub struct GroupCount<'a, K> {
    /// The count, from the policy table.
    pub policy: Option<Policy>,
    /// An offer (true) or an unseat (false).
    pub offer: bool,
    /// The keys the row seats or removes (`SeatRow::to`).
    /// A key the row seats is no voice of its count; a key it removes is a voice like any other, except
    /// under `unanimous`, `open:self_admit` and the duty withdrawal, whose text excludes it.
    pub to: &'a [K],
    /// The members at the head, less those whose own leaving is in the row's past.
    pub members: &'a BTreeSet<K>,
    /// The keys that signed the row (`voices`).
    pub voices: &'a BTreeSet<K>,
    /// The threshold the row declares (`SeatRow::need`).
    pub need: Option<usize>,
}

/// Whether a group's count is met: [`seat_rule`]'s `Conf::Group` arm after the members and voices are read,
/// and the very code that arm runs (see the contract on [`GroupCount`]). `weight` is a key's whole-number
/// weight (a `weighted` count), summed exactly. `None` for [`Policy::Ranked`] only: a ranked count is a tally
/// of the ballots the row names (`ranked::ranked`), which the seat rule reads before any count of voices. Any
/// other policy, a policy the table does not name included, is `Some`.
///
/// A caller that already holds the roster at the head (persist resolves a ballot's) answers here directly,
/// without presenting the roster as rows: the same answer as the seat rule over those rows, with no graph.
pub fn group_count<K: Ord>(c: &GroupCount<'_, K>, weight: impl Fn(&K) -> u64) -> Option<bool> {
    let GroupCount { policy: pol, offer: is_offer, to, members: mem, voices: v, need } = *c;
    if matches!(pol, Some(Policy::Ranked)) {
        return None;
    }
    Some(count_of(pol, is_offer, to, mem, v, need, weight))
}

fn count_of<K: Ord>(
    pol: Option<Policy>,
    is_offer: bool,
    to: &[K],
    mem: &BTreeSet<K>,
    v: &BTreeSet<K>,
    need: Option<usize>,
    weight: impl Fn(&K) -> u64,
) -> bool {
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
    if pol == Some(Policy::Lift) {
        // the members' check: more than half of the members (the caller has taken the act's author and the
        // key removed out of them, and the author out of the voices), never fewer than two; the key seated
        // is no voice
        let yes = v.iter().filter(|k| mem.contains(*k) && !to.contains(k)).count();
        return is_offer && 2 * yes > mem.len() && yes >= 2;
    }
    // no key admits itself (CC 2.7.5): a key the row seats is no voice of its count. On a removal the member
    // removed is a voice like any other unless the policy's own text excludes it: `unanimous` (below),
    // `open:self_admit` and the duty withdrawal (above) do. The voices that are members, ascending and each
    // once, read off the two sorted sets with no set built.
    let unanimous = pol == Some(Policy::Unanimous);
    let yes = || v.intersection(mem).filter(move |k| !(is_offer || unanimous) || !to.contains(k));
    if pol == Some(Policy::Weighted) {
        // in u128, so no further voice can lower the sum (`SeatCount.weighted_mono`, over Nat)
        let sum: u128 = yes().map(|k| weight(k) as u128).sum();
        return need.is_some_and(|t| t > 0 && sum >= t as u128);
    }
    let n_yes = yes().count();
    if unanimous {
        let others = mem.iter().filter(|k| !to.contains(k)).count();
        return if is_offer {
            !mem.is_empty() && n_yes == others && to.iter().all(|k| !mem.contains(k) || v.contains(k))
        } else {
            n_yes == others && 2 * n_yes > mem.len()
        };
    }
    met(pol, n_yes, mem.len(), need)
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

fn lone<R: SeatRow, S: CutSpec<R>>(
    law: &SeatLaw,
    spec: &S,
    r: &R,
    p: &Past<'_, '_, R>,
    cache: Option<&MembersAt<R>>,
) -> bool {
    let Some(obj) = r.obj() else { return false };
    let sc = concluded_over(p.rows());
    let seats = Seats::build(&sc, law, spec, None, None, cache);
    // the holders are persons: an agent holding a duty is no holder this count reads
    let held = persons(seats.holders("duty", &obj, None), &seats.holders(AGENT, &obj, None));
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
    // it ends another scope's seat of the object's own key, or (the same scope) the ender's own seat
    let own = us.as_ref() == rs.as_ref();
    if r.to().len() != 1 || if own { r.to()[0] != *r.signer() } else { Obj::Key(r.to()[0].clone()) != obj } {
        return false;
    }
    let sc = concluded_over(p.rows());
    let sole = Seats::new(&sc, law, spec, None);
    sole.one(us.as_ref(), &obj).as_ref() == Some(r.signer())
}

#[cfg(test)]
mod tests {
    use super::*;
    use alloc::vec;

    struct Lcg(u64);
    impl Lcg {
        fn next(&mut self, n: u64) -> u64 {
            self.0 = self.0.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
            (self.0 >> 33) % n.max(1)
        }
    }

    #[derive(Clone, Debug)]
    struct T {
        id: u32,
        names: Vec<u32>,
        signer: u32,
        kind: SeatKind,
        to: Vec<u32>,
        cosigners: Vec<u32>,
        scope: Option<String>,
        target: Option<u32>,
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

    impl SeatRow for T {
        type Word = String;
        fn seat_kind(&self) -> SeatKind {
            self.kind
        }
        fn to(&self) -> &[u32] {
            &self.to
        }
        fn cosigners(&self) -> &[u32] {
            &self.cosigners
        }
        fn scope(&self) -> Option<&String> {
            self.scope.as_ref()
        }
        fn obj(&self) -> Option<Obj<u32, u32>> {
            (self.kind == SeatKind::Offer).then_some(Obj::Row(0))
        }
        fn conf(&self) -> Option<Conf> {
            (self.kind == SeatKind::Offer).then_some(Conf::Own)
        }
        fn target(&self) -> Option<&u32> {
            self.target.as_ref()
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
            core::iter::once(r.signer).collect()
        }
        fn cuts_of(&self, _r: &T) -> BTreeSet<u32> {
            BTreeSet::new()
        }
        fn says(&self, _r: &T) {}
    }

    fn row(id: u32, names: Vec<u32>, signer: u32, kind: SeatKind) -> T {
        T { id, names, signer, kind, to: vec![], cosigners: vec![], scope: None, target: None }
    }

    /// Two versions that seat different keys (the second ends some seats the first holds, and seats others),
    /// read at every set of heads in a random order through one pass's cache: each answer is the members at
    /// those heads, as read with no cache.
    #[test]
    fn the_members_cache_answers_per_set_of_heads_and_scope() {
        let law = SeatLaw::default();
        let mut g = Lcg(5);
        let (mut cases, mut bad, mut differ) = (0usize, 0usize, 0usize);
        for _ in 0..2_000 {
            let n = 2 + g.next(6) as u32;
            let mut f = row(0, vec![], 1, SeatKind::Offer);
            f.to = vec![1];
            f.scope = Some("member".into());
            let mut rows = vec![f];
            let (mut v1, mut v2) = (vec![0u32], vec![]);
            for k in 2..=n {
                for (j, sc) in ["member", "founder"].iter().enumerate() {
                    if g.next(3) == 0 {
                        continue;
                    }
                    let id = 100 * (j as u32 + 1) + k;
                    let mut o = row(id, vec![0], 1, SeatKind::Offer);
                    o.to = vec![k];
                    o.cosigners = vec![k];
                    o.scope = Some((*sc).into());
                    rows.push(o);
                    if g.next(3) == 0 {
                        v2.push(id);
                    } else {
                        v1.push(id);
                        if g.next(2) == 0 {
                            // the key leaves at the second version
                            let mut w = row(300 + id, vec![id], k, SeatKind::Withdraw);
                            w.target = Some(id);
                            rows.push(w);
                            v2.push(300 + id);
                        }
                    }
                }
            }
            rows.push(row(1000, v1, 1, SeatKind::Other));
            v2.push(1000);
            rows.push(row(1001, v2, 1, SeatKind::Other));
            for j in 0..3 {
                rows.push(row(2000 + j, vec![1001], 1, SeatKind::Other));
            }
            let cache = MembersAt::<T>::default();
            let sets: [&[u32]; 6] = [&[1000], &[1001], &[1000, 1001], &[1001, 1000], &[1000, 1000], &[1001, 1001]];
            crate::layers::conclude(
                rows.iter(),
                |p| {
                    if p.row().id >= 2000 {
                        for _ in 0..8 {
                            let heads = sets[g.next(6) as usize];
                            let scope = ["member", "founder"][g.next(2) as usize];
                            let want = members_at(p, &law, &NoCut, &Obj::Row(0), heads, scope);
                            let got = members_at_with(p, &law, &NoCut, &Obj::Row(0), heads, scope, Some(&cache));
                            cases += 1;
                            bad += (got != want) as usize;
                            let first = members_at(p, &law, &NoCut, &Obj::Row(0), &heads[..1], scope);
                            differ += (want != first) as usize;
                        }
                    }
                    seat_rule(p, &law, &NoCut, &|_| true)
                },
                None,
            );
        }
        assert!(differ > 1_000, "only {differ} reads where a later head changes the members");
        assert_eq!(bad, 0, "{bad} of {cases} cached reads differ");
    }
}
