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
use crate::Row;
use alloc::collections::{BTreeMap, BTreeSet};
use alloc::string::String;
use alloc::vec::Vec;
use core::cell::RefCell;

mod election;
pub use election::{election_closed, ELECTION_RANKS};

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
    /// A ranked ballot ([`SeatRow::ranking`], best first), naming its election by [`SeatRow::of`].
    Ballot,
    /// A member's decline of the election its [`SeatRow::of`] names: the count is read with its signer struck.
    Decline,
    /// A reader's acknowledgement of a head (with [`SeatRow::room`]). With [`SeatRow::of`] naming a
    /// moderator's lone removal instead, a receipt of that act, which keeps it in force after the moderator's
    /// standing ends: a duty holder's, or with [`Conf::Group`] the room's count's, met over the persons at the
    /// heads it names.
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
    /// The caller's word for scope `s`. **Required.** The crate names one scope itself: `moderate`, which the
    /// lone signer of a founding record with no `duty_holders` map holds (CC 4.5.4: "A record one person signs
    /// MAY name none, and that person then holds every declared duty"; `moderate` is a duty every record
    /// declares). For a `String` word: `fn word(s: &'static str) -> String { s.into() }`; for a `&'a str` word:
    /// `fn word(s: &'static str) -> &'a str { s }`.
    fn word(s: &'static str) -> Self::Word;
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
    /// The grant carries sub-delegation: it may confer the same or narrower.
    fn sub(&self) -> bool {
        false
    }
    /// The heads a counted row is counted over.
    fn head(&self) -> &[Self::Id] {
        &[]
    }
    /// A community's record: the protocol it declares (CC 3.3.4: its `consensus_protocol`), a word of the closed
    /// set ([`RoomProtocol::parse`]; a word outside it is no protocol). Read on the founding record and on a change
    /// of the record (a counted offer of scope `record`). The protocol rows of the policy table (`cosigned_act`,
    /// `community_remove`, `wa_adjudication`: [`Policy::Protocol`]) are counted under the one in force
    /// ([`protocol_record`]). An adopter MUST implement it: with the default `None` no room has a protocol, so no
    /// removal and no admission under the room's protocol concludes in any room.
    fn consensus_protocol(&self) -> Option<&Self::Word> {
        None
    }
    /// A community's founding record: its `cohort_subkind`. `infrastructure` makes the object an
    /// [`CommunityKind::Infrastructure`] community ([`kind_of`]); any other value, or none, a community.
    fn cohort_subkind(&self) -> Option<&Self::Word> {
        None
    }
    /// A group's founding record: its group kind (`family` for a family record, which carries a `family_key_id`;
    /// `community` or none for a community). `family` makes the object a [`CommunityKind::Family`] ([`kind_of`]),
    /// whatever its scope or `cohort_subkind`. Default `None`: a community.
    fn group_kind(&self) -> Option<&Self::Word> {
        None
    }
    /// A group's record: `consensus_protocol_entrenched`, or `None` where the row states none (a change that
    /// states none leaves the flag as it is). On the record in force, a change of its `consensus_protocol`, or of
    /// this flag, concludes nothing (F5); every other amendment concludes under the protocol. Default `None`.
    fn protocol_entrenched(&self) -> Option<bool> {
        None
    }
    /// An infrastructure record's `admission_quorum_basis` (`founders`): a change moving it away concludes nothing
    /// (no weakening, CC 3.2). Default `None`, read as `founders`.
    fn admission_quorum_basis(&self) -> Option<&Self::Word> {
        None
    }
    /// A counted version of the group's record carrying `dissolved_at`: the act `dissolve`, after which no row over
    /// the group concludes and every seat over it ends. Default `false`.
    fn dissolves(&self) -> bool {
        false
    }
    /// An infrastructure room's recovery widening (CC 3.2): the row, counted at a strict majority over the holders
    /// of the bundle in force of the room's root, that names the key a stalled room's widening seats. Such a widening
    /// is undecided ([`stalled_recovery`]); the seat rule concludes nothing for it. Default `None`.
    fn bundle(&self) -> Option<&Self::Id> {
        None
    }
    /// An admission's role: `founder` on an offer of the member seat over a family seats the founder role too (a
    /// family's one-row founder admission, F1); on a change of an infrastructure community's record (scope
    /// `record`), the keys it names are seated as founders (a founders' amendment, CC 3.1.3.2). Default `None`.
    fn role(&self) -> Option<&Self::Word> {
        None
    }
    /// A counted act: the protocol and policy in force at it, as one value the caller compares by equality.
    /// Tips whose values differ do not fold ([`Seats::tips_fold`]). `None` where the caller states none.
    fn regime(&self) -> Option<&Self::Word> {
        None
    }
    /// On an end of a moderator's standing: it lifts the receipts of acts under the ended standing, so only the
    /// count's own receipt keeps such an act in force (conferral's [`crate::conferral::ConferralRow::lifts`]).
    /// Honoured on a counted unseat and on a conferrer's withdrawal of its own offer that seats another (CC
    /// 2.4.1.1 (i) and (iii)); the holder's own end never lifts (`lifts_on_own_end`) and a lone removal lifts
    /// nothing. Default `false`.
    fn lifts(&self) -> bool {
        false
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
    /// A declared threshold: a counted row's, read under a policy row it states with the binding off; on a record
    /// declaring a `weighted:{rubric}` protocol, that protocol's threshold. Never read from a row counted under the
    /// room's protocol (a quorum's number is its word's).
    fn need(&self) -> Option<usize> {
        None
    }
    /// An acceptance: the offer it accepts (none for a standing acceptance). A cosignature: the content
    /// it is a voice for.
    fn of(&self) -> Option<&Self::Id> {
        None
    }
    /// A window's landing: the opener it lands and the outcome it states. A self roster's lone-path eviction that
    /// lands `landed` ends the target's seat as a counted eviction does ([`SeatRow::evicts`]). Default `None`.
    fn landing(&self) -> Option<(&Self::Id, &Self::Word)> {
        None
    }
    /// An opener of a self roster's eviction window (`self_roster_evict`, CC 3.3.6.4): the key it proposes to evict.
    /// Default `None`.
    fn evicts(&self) -> Option<&Self::Key> {
        None
    }
    /// An opener of a self roster's addition window (`self_roster_add`): the keys it proposes to add. A landed addition
    /// seats each that signed the opener (its own consent). Default `None`.
    fn adds(&self) -> Option<&[Self::Key]> {
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
    /// A record's whole-number weights, read by a `weighted:{rubric}` protocol on the record that declares it
    /// ([`protocol_record`]; a counted row's own weights are read only under a policy row the row states, binding
    /// off).
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
    /// The key whose signature verified this row, as checked by the door (the room key a voice signed through in a
    /// private room); never a value the row states. The election reads a fork per signing key: two keys of one voice
    /// are two keys. `None`: the signer is read as the signing key, so two concurrent rows of one signer are a fork
    /// unless chained.
    fn signing_key(&self) -> Option<&Self::Key> {
        None
    }
    /// An acknowledgement: the object (room) whose head it acknowledges.
    fn room(&self) -> Option<Obj<Self::Id, Self::Key>> {
        None
    }
    /// A founding row that declares its community's `membership` `private` (CC 3.1.3.2): a private room, whose
    /// roster seats room keys. Read on a founding row only. Default false: a founding row with no `membership`
    /// reads public. A room is private or public by its founding row, and no record change moves it (people
    /// found a new room). A seating finality refuses there is the text's `membership_room_key_ended`.
    fn private_room(&self) -> bool {
        false
    }
}

/// A count, read from the policy table.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Policy {
    /// `yes / n >= num / den`, and n > 0.
    AtLeast(u64, u64),
    /// `yes / n > num / den`.
    Strict(u64, u64),
    /// `yes / n > num / den`, and never fewer than `least` voices (`StrictFloor(num, den, least)`): a plain
    /// threshold with a floor; the member a removal names is a voice of it, as on any plain count.
    StrictFloor(u64, u64, u64),
    /// The recall (CC 4.5.13: "A recall is one row cosigned by more than two thirds of the standing roster ... The
    /// floor is two voices"): [`Policy::StrictFloor`]'s comparison and floor, counted over the base less the key it
    /// removes, that key no voice (it judges one holder, as the lift does).
    Recall(u64, u64, u64),
    /// One voice.
    One,
    /// The threshold the row declares.
    Declared,
    /// The room's declared protocol: the count its record in force declares ([`protocol_record`],
    /// [`RoomProtocol`]); the policy table's protocol rows (`cosigned_act`, `community_remove`, `wa_adjudication`).
    /// Met by nothing where no protocol of the set is in force.
    Protocol,
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
    /// CC 4.5.13, the members' check as a counted row: an offer that seats again an agent's key a moderator
    /// removed alone. Its voices are the signers of the objections it names ([`lift_voices`]), the removal's
    /// author and the key it seats no voice; it is met by more than half of the members at the head the
    /// removal names (persons: the key removed is an agent's, in no count), the removal's author apart, never
    /// fewer than two voices. A counted row of this policy that is no such re-seating concludes nothing.
    Lift,
    /// Not a count (a seat, not a threshold).
    NotACount,
}

/// A room's declared protocol (CC 3.3.4: its record's `consensus_protocol`), one of the closed set of the
/// Constitution's `consensus_protocols.tsv` (copied into `data/`): who is counted and the rule the count meets. A word
/// outside the set is no protocol: a protocol row counted under it concludes nothing, and a change of the record naming
/// it changes nothing. A quorum's number, and a weighted count's weights and threshold, are the record's (the word, and
/// the record row that states it: [`SeatRow::weights`], [`SeatRow::need`]), never a counted row's.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
#[non_exhaustive]
pub enum RoomProtocol {
    /// `founder_only`: one founder signs an admission, counted over the founders (scope `founder`); the set states no
    /// removal under it, so a removal concludes nothing.
    FounderOnly,
    /// `unanimous`: every member signs an admission; a removal is signed by every member but the one it names, and
    /// those signers are a strict majority of the roster ([`Policy::Unanimous`]).
    Unanimous,
    /// `majority`: more than half of the members sign.
    Majority,
    /// `quorum:{m}/{n}`: any `m` members sign, `m` an absolute count, `1 <= m <= n`.
    Quorum(u64, u64),
    /// `weighted:{rubric}`: the sum of the signing members' weights reaches the threshold, both on the record.
    Weighted,
    /// `open:self_admit`: an admission is the joiner's own signature ([`Policy::SelfAdmit`]).
    SelfAdmit,
}

/// The kinds of the protocol set, as `consensus_protocols.tsv` writes them, in its order.
pub const PROTOCOL_KINDS: [&str; 6] =
    ["founder_only", "unanimous", "majority", "quorum:{m}/{n}", "weighted:{rubric}", "open:self_admit"];

/// A whole number of a protocol word: one to nine digits, no leading zero (one spelling per number).
fn protocol_count(w: &str) -> Option<u64> {
    let ok = (1..=9).contains(&w.len()) && w.bytes().all(|b| b.is_ascii_digit()) && !w.starts_with('0');
    if ok {
        w.parse().ok()
    } else {
        None
    }
}

impl RoomProtocol {
    /// The protocol a record's word names, or `None` for a word outside the set.
    pub fn parse(w: &str) -> Option<RoomProtocol> {
        match w {
            "founder_only" => return Some(RoomProtocol::FounderOnly),
            "unanimous" => return Some(RoomProtocol::Unanimous),
            "majority" => return Some(RoomProtocol::Majority),
            "open:self_admit" => return Some(RoomProtocol::SelfAdmit),
            _ => {}
        }
        if let Some(q) = w.strip_prefix("quorum:") {
            let (m, n) = q.split_once('/')?;
            let (m, n) = (protocol_count(m)?, protocol_count(n)?);
            return (m <= n).then_some(RoomProtocol::Quorum(m, n));
        }
        match w.strip_prefix("weighted:") {
            Some(rubric) if !rubric.is_empty() => Some(RoomProtocol::Weighted),
            _ => None,
        }
    }
    /// The protocol a record's word names (`infrastructure` false), or the word an infrastructure community's
    /// record may state (CC 3.2, "Live and stalled"): `quorum:{M}/{N}`, M an absolute count of founder voices, at
    /// least 2 and the strict majority of N (`N / 2 + 1`), N the cap on its active founders. Any other word there
    /// (`quorum:1/1`, `quorum:2/5`, `quorum:3/3`, `majority`) is none, the text's
    /// `federation_community_consensus_protocol_violation`. M is never recomputed from the founders held.
    pub fn parse_in(w: &str, infrastructure: bool) -> Option<RoomProtocol> {
        let p = RoomProtocol::parse(w)?;
        if !infrastructure {
            return Some(p);
        }
        match p {
            RoomProtocol::Quorum(m, n) if m >= 2 && m == n / 2 + 1 => Some(p),
            _ => None,
        }
    }
    /// Whether the protocol states a rule for an act, as the protocol sheet (`consensus_protocols.tsv`) gives it:
    /// an admission by its `rule` cell, a removal by its `removal_rule` cell (`unstated` for `open:self_admit` alone),
    /// and
    /// any other act counted under it (a change of the record) by a DERIVED column, as the sheet has none: a
    /// protocol whose count set is the members states a rule; the joiner's own signature (`open:self_admit`) and the
    /// founder role (`founder_only`) do not. Where the protocol states none,
    /// the `cosigned_act` half of an `&` is no condition, and the other policy governs alone, with
    /// [`SeatLaw::community_floor`] (the Constitution's reading of `&`).
    pub fn states(self, act: Act) -> bool {
        match act {
            Act::Admit => true,
            // the sheet at rc23 2b509c8 gives founder_only a removal rule (`founder-target`, `role_at:founder:1`)
            Act::Remove => self != RoomProtocol::SelfAdmit,
            _ => !matches!(self, RoomProtocol::FounderOnly | RoomProtocol::SelfAdmit),
        }
    }
    /// The body a count under it is taken over: the founders for `founder_only` (a family's protocol, Q3: the
    /// founders its record names; no family is built, and no community may declare it: [`community_protocol`]), the
    /// members otherwise.
    pub fn body(self) -> &'static str {
        match self {
            RoomProtocol::FounderOnly => "founder",
            _ => "member",
        }
    }
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
    /// Scopes whose ending is final: no offer re-seats the key once such an unseat is in its past. A roster
    /// seat named here (`member`, [`AGENT`]: a room key's seat) is final over a private room only
    /// ([`SeatRow::private_room`]), by any end that stands: a counted removal of the seat, or the key's own end
    /// of its stay; an acceptance of an offer seating the key is refused as the offer is. A moderator's lone
    /// removal is never final.
    pub final_scopes: Vec<String>,
    /// The seats over a community its duty holders do not place (the roster's own: `member`).
    pub roster_seats: Vec<String>,
    /// The longest chain of conferred seats below a root.
    pub depth: usize,
    /// The count each policy row names.
    pub policy: BTreeMap<String, Policy>,
    /// The act-to-policy binding (the Constitution's `governance_policy_acts.tsv`): which policy rows each counted
    /// act may take. `None`: this law binds no act to a policy, and the binding is the caller's (the behaviour
    /// before it). `Some(rows)`: the binding is on: a counted row whose stated policy its act may not take
    /// concludes nothing, and one over an object with a kind whose act has no row concludes nothing. The seat
    /// fixture's law carries `Some`.
    pub acts: Option<Vec<ActRule>>,
    /// The community floor of voices (the policy table's `min_count.community`): a policy row that governs alone
    /// where the room's protocol states no rule for the act (the reading of `&`, [`RoomProtocol::states`]) is met by
    /// no fewer voices. 0: no floor.
    pub community_floor: usize,
    /// A community's removal floor: the policy table's `community_remove` floor cell (`2 voices`): a counted removal
    /// takes that many voices besides the member it removes (CC 4.5.13, CC 3.1.3.2), under any community protocol. 0:
    /// no floor.
    pub removal_floor: usize,
    /// The kind of an object, from its founding row's scope (`holder`: an accord; `self`: a self roster; `member`,
    /// `duty`, and every scope the map does not name: a community). A key object is a self roster. An object with no
    /// founding row has no kind and no act.
    pub kinds: BTreeMap<String, CommunityKind>,
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

macro_rules! words {
    ($(#[$m:meta])* $name:ident { $($(#[$vm:meta])* $v:ident = $w:literal),* $(,)? }) => {
        $(#[$m])*
        #[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
        #[non_exhaustive]
        pub enum $name { $($(#[$vm])* $v),* }
        impl $name {
            /// The word the acts table writes.
            pub fn word(self) -> &'static str {
                match self { $($name::$v => $w),* }
            }
            /// The value the acts table's word names.
            pub fn from_word(w: &str) -> Option<Self> {
                match w { $($w => Some($name::$v),)* _ => None }
            }
        }
    };
}

words! {
    /// A counted act of the acts table (`act`).
    Act {
        /// A widening of a roster seat.
        Admit = "admit",
        /// A removal of a roster seat.
        Remove = "remove",
        /// The duty holders' conferral of a duty (CC 4.5.4 (iv)).
        DutyConfer = "duty_confer",
        /// The other duty holders' withdrawal of a duty (CC 4.5.4 (iv)).
        DutyWithdraw = "duty_withdraw",
        /// The duty holders' conferral of a detector seat (CC 4.5.7).
        SeatConfer = "seat_confer",
        /// The duty holders' withdrawal of a detector seat (CC 4.5.7).
        SeatWithdraw = "seat_withdraw",
        /// The members' recall of a duty holder (CC 4.5.13).
        Recall = "recall",
        /// The members' lift of a moderator's act: the seat re-seated (CC 4.5.13).
        Lift = "lift",
        /// The members' fallback on a moderation action (a window).
        ModerationFallback = "moderation_fallback",
        /// The election's seating (CC 4.5.13).
        ElectionSeating = "election_seating",
        /// A poll.
        Poll = "poll",
        /// A change of the community's record.
        RecordChange = "record_change",
        /// The accord's confirmation of a halt (a window).
        HaltConfirm = "halt_confirm",
        /// The accord's resumption.
        Resume = "resume",
        /// An act of the accord's standing majority.
        StandingAct = "standing_act",
        /// A body's finding.
        Finding = "finding",
        /// A custodian's replacement.
        Replace = "replace",
        /// A change of content of a class the table names (`content`, `irreversible`): its default policy.
        Change = "change",
        /// The group's dissolution: a terminal version of its record carrying `dissolved_at`.
        Dissolve = "dissolve",
    }
}

words! {
    /// The scope class of a counted act (the acts table's `scope`).
    ScopeClass {
        /// A member's seat.
        Member = "member",
        /// An AI agent's seat.
        Agent = "agent",
        /// A founder's seat over an infrastructure community.
        Founder = "founder",
        /// A node's seat over an infrastructure community (no voice, in no base).
        Node = "node",
        /// A duty seat.
        Duty = "duty",
        /// A detector seat (`detect:{list id}`, CC 4.5.7): no declared duty.
        Detect = "detect",
        /// The seat of `moderate`, by election.
        Moderate = "moderate",
        /// A key of a self roster.
        Key = "key",
        /// The seat a moderator's act took: the lift re-seats it.
        Act = "act",
        /// Content.
        Content = "content",
        /// The community's record.
        Record = "record",
        /// A halt.
        Halt = "halt",
        /// An irreversible change of content.
        Irreversible = "irreversible",
        /// A custodian.
        Custodian = "custodian",
        /// Any scope.
        Any = "any",
    }
}

words! {
    /// The kind of an object (the acts table's `community_kind`).
    CommunityKind {
        /// A community.
        Community = "community",
        /// An infrastructure community (its record's `cohort_subkind`): founders and nodes' seats.
        Infrastructure = "infrastructure",
        /// A family (CC 3.3.4, 3.1.3.2, 4.5.12.5): its founding record's group kind ([`SeatRow::group_kind`]).
        /// Keyless; no duty seats; its protocol any of the set, `founder_only` and `quorum:1/{n}` included.
        Family = "family",
        /// A self roster.
        SelfRoster = "self",
        /// The accord.
        Accord = "accord",
        /// An affiliation.
        Affiliation = "affiliation",
        /// A body.
        Body = "body",
        /// A custody.
        Custody = "custody",
    }
}

words! {
    /// Whether the counted row states its policy (`row`, one of those listed) or the act fixes it (`fixed`).
    Choice {
        /// The act takes its one row: the counted row states it or none, and a row stating another policy
        /// concludes nothing.
        Fixed = "fixed",
        /// The counted row states one of the rows listed.
        Row = "row",
    }
}

/// One row of the acts table: an act over a scope class and a kind of object, the policy rows it may take, and
/// whether the counted row chooses.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ActRule {
    /// The act.
    pub act: Act,
    /// Its scope class.
    pub scope: ScopeClass,
    /// The kind of object.
    pub kind: CommunityKind,
    /// The policy rows it may take.
    pub policies: Vec<String>,
    /// Whether the row states one of them, or the act fixes its one (stated or not; another stated is refused).
    pub choice: Choice,
}

/// The kind of `obj`: a self roster for a key object; otherwise, for a founding row, its scope read through
/// [`SeatLaw::kinds`], a community where the map names none (the binding reaches every room, whatever scope founds
/// it); `None` where no founding row of it is held.
pub fn kind_of<'r, R: SeatRow + 'r>(
    law: &SeatLaw,
    get: &dyn Fn(&R::Id) -> Option<&'r R>,
    obj: &ObjOf<R>,
) -> Option<CommunityKind> {
    let id = match obj {
        Obj::Key(_) => return Some(CommunityKind::SelfRoster),
        Obj::Row(i) => i,
    };
    let g = get(id)?;
    if g.seat_kind() != SeatKind::Offer || !founding(g) {
        return None;
    }
    // the group kind of the founding record: `family` or `community`; a community's cohort_subkind then splits off an
    // infrastructure community
    if g.group_kind().is_some_and(|k| k.as_ref() == "family") {
        return Some(CommunityKind::Family);
    }
    let kind = g.scope().and_then(|sc| law.kinds.get(sc.as_ref()).copied()).unwrap_or(CommunityKind::Community);
    // a community's record says whether it is an infrastructure community: `cohort_subkind`
    if kind == CommunityKind::Community && g.cohort_subkind().is_some_and(|c| c.as_ref() == "infrastructure") {
        return Some(CommunityKind::Infrastructure);
    }
    Some(kind)
}

/// The act a counted row is, decided from its kind, its scope and its object, never from the policy it states:
/// (act, scope class, kind) as the acts table writes them, or `None` (not a counted act, or an object with no
/// kind). `get` looks a row up among those the caller holds (the row's past).
///
/// - Over a community: an offer whose `content()` names an unseat of the same seat (object, scope, keys) is the
///   lift, of that seat's scope class (the table binds the agent's); an offer or unseat of a roster seat
///   ([`SeatLaw::roster_seats`]) is an admission or a removal of that seat; one of a detector seat
///   (`detect:*`) is the holders' conferral or withdrawal of that seat; an offer of a duty under the ranked count
///   ([`Policy::Ranked`]) of `moderate` is the election's seating, THE ONE ACT READ FROM THE STATED POLICY in this
///   tag (the election is not answered safely by it: a caller must not rely on a ranked seating); another offer of
///   a duty is the duty holders' conferral; an unseat of a duty counted over all the duty holders (`counted()`
///   `duty`) is their withdrawal, and one counted over the members (`member`, or none) is the recall; an unseat of
///   a duty counting any other body is no act. Any other scope, or none, is no act.
/// - Over an accord: any counted row is a standing act.
/// - Over a self roster: an offer or unseat of a key, or of the roster's own seat, admits or removes a key.
///
/// A moderator's lone removal is a removal by its shape; whether it is counted at all is the seat rule's.
pub fn act_of<'r, R: SeatRow + 'r>(
    law: &SeatLaw,
    get: &dyn Fn(&R::Id) -> Option<&'r R>,
    r: &R,
) -> Option<(Act, ScopeClass, CommunityKind)> {
    let offer = match r.seat_kind() {
        SeatKind::Offer => true,
        SeatKind::Unseat => false,
        _ => return None,
    };
    if r.conf() != Some(Conf::Group) {
        return None;
    }
    let obj = r.obj()?;
    let kind = kind_of(law, get, &obj)?;
    let sc = r.scope().map(|s| s.as_ref());
    match kind {
        CommunityKind::Community => {
            if offer {
                let lift = r.content().and_then(get).is_some_and(|c| {
                    c.seat_kind() == SeatKind::Unseat
                        && c.obj().as_ref() == Some(&obj)
                        && c.scope().map(|s| s.as_ref()) == sc
                        && c.to() == r.to()
                });
                if lift {
                    // the seat re-seated: the table binds the agent's
                    return Some((Act::Lift, ScopeClass::from_word(sc?)?, kind));
                }
            }
            let sc = sc?;
            if law.roster_seats.iter().any(|x| x == sc) {
                let class = ScopeClass::from_word(sc)?;
                return Some((if offer { Act::Admit } else { Act::Remove }, class, kind));
            }
            // a change of the community's record (its consensus_protocol, say): the act record_change; one carrying
            // `dissolved_at`, the act dissolve
            if offer && sc == "record" {
                let act = if r.dissolves() { Act::Dissolve } else { Act::RecordChange };
                return Some((act, ScopeClass::Record, kind));
            }
            // a detector seat (CC 4.5.7: `detect:{list id}`, conferred and "withdrawn by the count of (iv)")
            if sc == "detect" || sc.starts_with("detect:") {
                return Some((if offer { Act::SeatConfer } else { Act::SeatWithdraw }, ScopeClass::Detect, kind));
            }
            let declared: Vec<&str> = match &obj {
                Obj::Row(i) => get(i).map_or(Vec::new(), |g| g.duties().iter().map(|d| d.as_ref()).collect()),
                Obj::Key(_) => Vec::new(),
            };
            if !law.is_duty(sc, &declared) {
                return None;
            }
            if offer {
                // THE ONE ACT READ FROM THE STATED POLICY: the election is not answered safely by this tag, and a
                // caller must not rely on a ranked seating. The election seats `moderate` alone (CC 4.5.13): a ranked
                // offer of another duty is that duty's conferral
                if sc == "moderate" && law.policy_of(r.policy().map(|x| x.as_ref())) == Some(Policy::Ranked) {
                    return Some((Act::ElectionSeating, ScopeClass::Moderate, kind));
                }
                return Some((Act::DutyConfer, ScopeClass::Duty, kind));
            }
            // the body counted is the act's (CC 4.5.4 (iv), 4.5.13): the duty holders exactly (`duty`) withdraw a
            // duty, the members exactly (persons: agents and nodes are in no base) recall its holder; any other body
            // is no act
            match r.counted().map_or("member", |c| c.as_ref()) {
                "duty" => Some((Act::DutyWithdraw, ScopeClass::Duty, kind)),
                "member" => Some((Act::Recall, ScopeClass::Duty, kind)),
                _ => None,
            }
        }
        CommunityKind::Infrastructure => {
            // the founders' own roster, a node's seat (placed and removed by the founders' count), and a change of
            // the record (under the founders' protocol)
            let class = match sc? {
                "record" if offer => return Some((Act::RecordChange, ScopeClass::Record, kind)),
                "founder" => ScopeClass::Founder,
                "node" => ScopeClass::Node,
                _ => return None,
            };
            Some((if offer { Act::Admit } else { Act::Remove }, class, kind))
        }
        CommunityKind::Family => {
            // a family's acts (the table's family rows): an admission and a removal of a member, a promotion to and a
            // demotion from the founder role (counted as an admission and as a removal: F1), a change of the record
            // and its dissolution. No duty seat, no moderator, no agent (F4)
            match sc? {
                "record" if offer => {
                    Some((if r.dissolves() { Act::Dissolve } else { Act::RecordChange }, ScopeClass::Record, kind))
                }
                "member" | "founder" => Some((if offer { Act::Admit } else { Act::Remove }, ScopeClass::Member, kind)),
                _ => None,
            }
        }
        CommunityKind::Accord => Some((Act::StandingAct, ScopeClass::Any, kind)),
        CommunityKind::SelfRoster => {
            let sc = sc?;
            let own = match &obj {
                Obj::Row(i) => get(i).and_then(|g| g.scope()).map(|s| s.as_ref() == sc),
                Obj::Key(_) => None,
            };
            if sc == "key" || own == Some(true) {
                Some((if offer { Act::Admit } else { Act::Remove }, ScopeClass::Key, kind))
            } else {
                None
            }
        }
        _ => None,
    }
}

/// A change of community `obj`'s record that states its `consensus_protocol`: a counted offer of scope `record`
/// over `obj` (the act `record_change`), carrying the new protocol.
fn is_amendment<R: SeatRow>(q: &R, obj: &ObjOf<R>) -> bool {
    q.seat_kind() == SeatKind::Offer
        && q.conf() == Some(Conf::Group)
        && q.obj().as_ref() == Some(obj)
        && q.scope().is_some_and(|s| s.as_ref() == "record")
        && q.consensus_protocol().is_some()
}

/// The ids row `from` names, and those they name, through the rows of `by` alone: an id named and not held is in
/// the answer and is followed no further (a row not concluded carries nothing).
fn concluded_anc<'a, R: SeatRow>(by: &BTreeMap<&'a R::Id, &'a R>, from: &'a R) -> BTreeSet<&'a R::Id> {
    let mut out: BTreeSet<&'a R::Id> = BTreeSet::new();
    let mut stack: Vec<&'a R::Id> = from.names().iter().collect();
    while let Some(i) = stack.pop() {
        if out.insert(i) {
            if let Some(&q) = by.get(i) {
                stack.extend(q.names().iter());
            }
        }
    }
    out
}

/// The record row whose `consensus_protocol` is in force in a row's past `p`: the newest change of the record there
/// (a counted change of the object: a row with it in its past has it in force), or the founding record. The order
/// among the changes is read over the concluded rows of `p` alone (a row not concluded carries nothing: a change
/// naming only such a row is concurrent with what that row names). `None` where `obj` has no founding row, or where
/// the newest changes disagree (two concurrent changes stating different protocols, or the same with different
/// numbers: none is in force). A seat outlasts a change of protocol: no seat is judged again under the new one (CC
/// 4.5.4). The one read of a room's protocol: the binding's refusal, the count and the room-key rules call it.
pub fn protocol_record<'a, R: SeatRow>(p: &Past<'_, 'a, R>, obj: &ObjOf<R>) -> Option<&'a R> {
    let Obj::Row(i) = obj else { return None };
    let g = p.get(i)?;
    if g.seat_kind() != SeatKind::Offer || !founding(g) {
        return None;
    }
    let am: Vec<&'a R> = p.rows().filter(|q| is_amendment(*q, obj)).collect();
    if am.is_empty() {
        return Some(g);
    }
    let by: BTreeMap<&'a R::Id, &'a R> = p.rows().map(|q| (q.id(), q)).collect();
    let anc: Vec<BTreeSet<&'a R::Id>> = am.iter().map(|&q| concluded_anc(&by, q)).collect();
    let newest: Vec<&'a R> = am.iter().copied().filter(|q| !anc.iter().any(|a| a.contains(q.id()))).collect();
    let first = newest.iter().copied().min_by(|a, b| a.id().cmp(b.id()))?;
    let stated = |q: &'a R| {
        let w: BTreeSet<(&'a R::Key, u64)> = q.weights().iter().map(|(k, n)| (k, *n)).collect();
        (q.consensus_protocol().map(|x| x.as_ref()), q.need(), w)
    };
    let one = stated(first);
    newest.iter().all(|q| stated(*q) == one).then_some(first)
}

/// The room's declared protocol in force in a row's past `p`: [`protocol_record`]'s `consensus_protocol` (`None`
/// where it states none, or where no record is in force).
pub fn protocol_of<'a, R: SeatRow>(p: &Past<'_, 'a, R>, obj: &ObjOf<R>) -> Option<&'a R::Word> {
    protocol_record(p, obj).and_then(|g| g.consensus_protocol())
}

/// The founders an infrastructure community's founding row seats: its distinct signers that are among its `to()` (a
/// signer it does not name is seated in nothing, and no founder). The founding record's word is checked against their
/// number; every later count reads the founder seats at its own heads (P1, Q5).
pub fn founders_of<'r, R: SeatRow + 'r>(get: &dyn Fn(&R::Id) -> Option<&'r R>, obj: &ObjOf<R>) -> usize {
    let Obj::Row(i) = obj else { return 0 };
    // a founding row seats the keys that signed it: a signer it does not name is seated in nothing, and no founder
    get(i).map_or(0, |g| {
        core::iter::once(g.signer()).chain(g.cosigners()).filter(|k| g.to().contains(*k)).collect::<BTreeSet<_>>().len()
    })
}

/// The body an act counts (the act's own, never the row's `counted()`): an infrastructure community's founders;
/// all the duty holders (`duty`) for the duty holders' acts (a duty's conferral and withdrawal, a detector seat's);
/// an accord's holders; a self roster's own seat (its founding row's scope; `key` for a key object); the members for
/// every other act of a community (an admission, a removal, the recall, the lift, the election, a change of the
/// record).
fn body_of<'r, R: SeatRow + 'r>(
    get: &dyn Fn(&R::Id) -> Option<&'r R>,
    (act, _, kind): (Act, ScopeClass, CommunityKind),
    obj: &ObjOf<R>,
) -> &'r str {
    match kind {
        CommunityKind::Infrastructure => "founder",
        CommunityKind::Accord => "holder",
        CommunityKind::Family => "member",
        CommunityKind::SelfRoster => match obj {
            Obj::Row(i) => {
                let key: &'r str = "key";
                get(i).and_then(|g| g.scope()).map_or(key, |s| s.as_ref())
            }
            Obj::Key(_) => "key",
        },
        _ if matches!(act, Act::DutyConfer | Act::DutyWithdraw | Act::SeatConfer | Act::SeatWithdraw) => "duty",
        _ => "member",
    }
}

/// The protocol a community's record may declare (CC 3.3.4, closed by CC 4.5.13 and the Constitution's Q1 and Q3): a
/// word of the set under which no one voice admits or removes, and not `founder_only` (a family's, not a
/// community's). `None` for any other: `quorum:1/{n}`, `founder_only`, a `weighted:{rubric}` record one of whose
/// `weights` reaches its threshold `need` (the text's `federation_community_consensus_protocol_violation`).
pub fn community_protocol<K: PartialEq>(w: &str, need: Option<usize>, weights: &[(K, u64)]) -> Option<RoomProtocol> {
    let p = RoomProtocol::parse(w)?;
    match p {
        RoomProtocol::FounderOnly | RoomProtocol::Quorum(1, _) => None,
        // a record weighing one key twice states no weights (refused at the change, as at use)
        RoomProtocol::Weighted
            if weights.iter().enumerate().any(|(i, (k, _))| weights[..i].iter().any(|(j, _)| j == k)) =>
        {
            None
        }
        RoomProtocol::Weighted if need.is_some_and(|t| weights.iter().any(|(_, x)| *x as u128 >= t as u128)) => None,
        _ => Some(p),
    }
}

/// What a counted row is counted under ([`policy_in_force`]).
struct InForce<'a, R: SeatRow> {
    /// The policy.
    pol: Option<Policy>,
    /// The threshold a declared or weighted count reads: the record's under the room's protocol (a quorum's `m`, a
    /// weighted count's threshold), the row's own otherwise.
    need: Option<usize>,
    /// The row whose weights a weighted count reads: the record under the room's protocol, `None` for the row's own.
    weights: Option<&'a R>,
    /// An infrastructure community's (M, N) (CC 3.2): the count is live while the founder seats at the row's heads
    /// number at least M + 1, and N caps them (read by the count, which counts them).
    infra: Option<(usize, usize)>,
    /// The community floor of voices, where this policy governs alone in place of a protocol that states no rule.
    floor: usize,
    /// A family under `founder_only`: a removal (a demotion too) takes an active founder other than the one it
    /// names, so the keys it names are no voice of it.
    exclude_target: bool,
    /// A family's removal: one naming only its own signer, on that signature alone, concludes nothing (F3: the
    /// resignation is the leaving).
    no_self_removal: bool,
    /// A removal under the room's protocol (`community_remove`: "the member being removed is not counted"): the key
    /// it removes is neither counted over nor a voice.
    base_excludes_target: bool,
}

impl<'a, R: SeatRow> InForce<'a, R> {
    fn plain(pol: Option<Policy>, need: Option<usize>) -> Self {
        InForce {
            pol,
            need,
            weights: None,
            infra: None,
            floor: 0,
            exclude_target: false,
            no_self_removal: false,
            base_excludes_target: false,
        }
    }
}

/// The policy a counted row is counted under: one [`InForce`], or several for policies the table joins by `&`
/// (every one must be met), or `Err(())`: the row concludes nothing. With the binding on ([`SeatLaw::acts`] `Some`),
/// from the row's act ([`act_of`]) and the acts table: a fixed act refuses a different stated policy and accepts its
/// own or none; a row's choice is one of those listed, stated. A counted row over an object with a kind whose act
/// has no row, or that states a policy its act may not take, concludes nothing; so does a change of the record naming
/// a word its room may not declare ([`community_protocol`]; an infrastructure community's must be a quorum), and a
/// row whose body (`counted()`, `over()`) is not its act's own. A protocol row ([`Policy::Protocol`]) is counted under
/// the room's protocol in force in the row's past ([`protocol_record`]), never one the row states, over the
/// protocol's own body and with the record's numbers, never the row's `need()` ([`protocol_part`]). With the binding
/// off, the row's own policy and need, a protocol row read the same way.
fn policy_in_force<'a, R: SeatRow>(law: &SeatLaw, p: &Past<'_, 'a, R>, r: &R) -> Result<Vec<InForce<'a, R>>, ()> {
    let get = |i: &R::Id| p.get(i);
    let get: &dyn Fn(&R::Id) -> Option<&'a R> = &get;
    let stated = r.policy().map(|x| x.as_ref());
    let mut word = stated;
    if law.acts.is_some() {
        match (act_of(law, get, r), r.obj()) {
            (None, Some(obj)) => {
                if kind_of(law, get, &obj).is_some() {
                    return Err(());
                }
            }
            (None, None) => {}
            (Some((act, sc, kind)), _) => {
                let (pols, choice) = policy_for(law, act, sc, kind).ok_or(())?;
                match choice {
                    Choice::Fixed => {
                        let one = pols.first().ok_or(())?;
                        if stated.is_some_and(|s| s != one.as_str()) {
                            return Err(());
                        }
                        word = Some(one.as_str());
                    }
                    Choice::Row => {
                        if !stated.is_some_and(|s| pols.iter().any(|p| p == s)) {
                            return Err(());
                        }
                    }
                }
                // a stated regime is a consistency check: it must be the room's protocol in force in the row's past
                if r.regime().is_some_and(|g| r.obj().and_then(|o| protocol_of(p, &o)) != Some(g)) {
                    return Err(());
                }
                // a change of the record that states a protocol names one its room may declare, or concludes nothing
                // (an infrastructure community's: its founders' strict majority, checked by the count at its heads)
                if act == Act::RecordChange {
                    if let Some(w) = r.consensus_protocol() {
                        let ok = if kind == CommunityKind::Infrastructure {
                            RoomProtocol::parse_in(w.as_ref(), true).is_some()
                        } else {
                            community_protocol(w.as_ref(), r.need(), r.weights()).is_some()
                        };
                        if !ok {
                            return Err(());
                        }
                    }
                }
                // `role: founder` is read on a family's admission of the member seat and on an infrastructure
                // community's founders' amendment, and nowhere else
                if r.role().is_some()
                    && !matches!(
                        (kind, r.scope().map(|s| s.as_ref())),
                        (CommunityKind::Family, Some("member")) | (CommunityKind::Infrastructure, Some("record"))
                    )
                {
                    return Err(());
                }
                // an entrenched record: a change of its protocol, or of the flag, concludes nothing (F5)
                if act == Act::RecordChange && !entrenchment_allows(law, p, r) {
                    return Err(());
                }
                // the body an act counts is the act's own, over its own object, never one the row states; a
                // protocol row's is its protocol's (`protocol_part`); a duty's conferral, withdrawal and recall are
                // read by their own gates (`duty_gate`, `duty_over`, `act_of`'s body)
                if law.policy_of(word) != Some(Policy::Protocol)
                    && !matches!(act, Act::DutyConfer | Act::DutyWithdraw | Act::Recall)
                {
                    let obj = r.obj().ok_or(())?;
                    let counted = r.counted().map_or("member", |c| c.as_ref());
                    // (`over`, another object: H2 in the seat rule refuses it for every count)
                    if counted != body_of(get, (act, sc, kind), &obj) {
                        return Err(());
                    }
                }
            }
        }
    }
    let Some(w) = word.filter(|w| w.contains('&')) else {
        let pol = law.policy_of(word);
        if pol != Some(Policy::Protocol) {
            return Ok(alloc::vec![InForce::plain(pol, r.need())]);
        }
        return Ok(alloc::vec![protocol_part(law, p, r)?]);
    };
    // policies joined by `&` (a change of the record: the protocol in force and the standing default): each is met.
    // Where the protocol in force states no rule for the act (RoomProtocol::states, the protocol sheet), the
    // cosigned_act half is no condition and the other governs alone, with the community floor (the Constitution's
    // reading of `&`)
    let unstated = || {
        let obj = r.obj()?;
        if kind_of(law, get, &obj) == Some(CommunityKind::Infrastructure) {
            return None;
        }
        let rec = protocol_record(p, &obj)?;
        let proto = community_protocol(rec.consensus_protocol()?.as_ref(), rec.need(), rec.weights())?;
        let act = match r.seat_kind() {
            SeatKind::Offer if r.scope().is_some_and(|s| law.roster_seats.iter().any(|x| x == s.as_ref())) => {
                Act::Admit
            }
            SeatKind::Unseat => Act::Remove,
            _ => Act::RecordChange,
        };
        (!proto.states(act)).then_some(())
    };
    let dropped = unstated().is_some();
    let mut out: Vec<InForce<'a, R>> = Vec::new();
    for part in w.split('&') {
        match law.policy_of(Some(part)) {
            Some(Policy::Protocol) if dropped => {}
            Some(Policy::Protocol) => out.push(protocol_part(law, p, r)?),
            pol => out.push(InForce {
                floor: if dropped { law.community_floor } else { 0 },
                ..InForce::plain(pol, r.need())
            }),
        }
    }
    Ok(out)
}

/// Whether change `r` of the record is allowed by its entrenchment (F5, the one place it is read): on a record in
/// force ([`protocol_record`]) carrying [`SeatRow::protocol_entrenched`], a change stating another protocol, or one
/// stating a protocol without the flag (a change of the flag), concludes nothing; a change that states no protocol (a
/// rename, a role, metadata) is allowed. A record not entrenched allows every change.
fn entrenchment_allows<R: SeatRow>(law: &SeatLaw, p: &Past<'_, '_, R>, r: &R) -> bool {
    let Some(obj) = r.obj() else { return true };
    let Some(rec) = protocol_record(p, &obj) else { return true };
    if rec.protocol_entrenched() != Some(true) {
        return true;
    }
    if kind_of(law, &|i| p.get(i), &obj) == Some(CommunityKind::Infrastructure) {
        // an infrastructure record's entrenchment means no WEAKENING (CC 3.2): its basis stays `founders`, the flag
        // stays, and M is never lowered (the count checks M against the present one, with the founders it reads)
        if r.admission_quorum_basis().is_some_and(|b| b.as_ref() != "founders") {
            return false;
        }
        return r.consensus_protocol().is_none() || r.protocol_entrenched() == Some(true);
    }
    let Some(w) = r.consensus_protocol() else { return r.protocol_entrenched() != Some(false) };
    // under `weighted`, the weights and threshold are the protocol: restating either is a change of it
    let set = |q: &R| q.weights().iter().map(|(k, n)| (k.clone(), *n)).collect::<BTreeSet<_>>();
    let weighted =
        rec.consensus_protocol().and_then(|x| RoomProtocol::parse(x.as_ref())) == Some(RoomProtocol::Weighted);
    if weighted && (r.need() != rec.need() || set(r) != set(rec)) {
        return false;
    }
    rec.consensus_protocol().map(|x| x.as_ref()) == Some(w.as_ref()) && r.protocol_entrenched() == Some(true)
}

/// A dissolution of the group: a counted offer of scope `record` carrying `dissolved_at` (the act dissolve).
fn is_dissolve<R: SeatRow>(q: &R) -> bool {
    q.seat_kind() == SeatKind::Offer
        && q.conf() == Some(Conf::Group)
        && q.scope().is_some_and(|s| s.as_ref() == "record")
        && q.dissolves()
}

/// A concluded dissolution of `obj` is in past `p`: the group's record is withdrawn, every seat over it ends, and no
/// row over it concludes after (the text's refusal `group_dissolved`).
fn dissolved_in<R: SeatRow>(p: &Past<'_, '_, R>, obj: &ObjOf<R>) -> bool {
    p.rows().any(|q| is_dissolve(q) && q.obj().as_ref() == Some(obj))
}

/// The one row an infrastructure room admits without its founders' count while stalled (CC 3.2): a widening whose only
/// change is one added founder seat, for a key named by a row ([`SeatRow::bundle`]) counted at a strict majority over
/// the holders of the bundle in force of the root the room stands under, whose `scope` names this room, signed by the
/// named key. The kernel holds no bundle holders, so `p.row()` of that shape is UNDECIDED: the reason
/// `stalled_recovery_needs_bundle` (the seat rule concludes nothing for it); `None` for a row of another shape, or
/// in a room that is live. The checks for when the trust root's fold is in the kernel: the counted row names the
/// bundle in force; its `scope` names this room; the key's identity type includes `user` and excludes `node`; the
/// widening is signed by the named key; only while stalled; only one founder seat; nothing else changed.
pub fn stalled_recovery<R: SeatRow, S: CutSpec<R>>(
    p: &Past<'_, '_, R>,
    law: &SeatLaw,
    spec: &S,
) -> Option<&'static str> {
    let r = p.row();
    if r.seat_kind() != SeatKind::Offer || r.bundle().is_none() || r.scope().is_none_or(|s| s.as_ref() != "founder") {
        return None;
    }
    let obj = r.obj()?;
    let get = |i: &R::Id| p.get(i);
    if kind_of(law, &get, &obj) != Some(CommunityKind::Infrastructure) || r.to().len() != 1 || !signed_by(r, &r.to()[0])
    {
        return None;
    }
    let rec = protocol_record(p, &obj)?;
    let Some(RoomProtocol::Quorum(m, _)) = RoomProtocol::parse_in(rec.consensus_protocol()?.as_ref(), true) else {
        return None;
    };
    let founders = count_members_with(p, law, spec, None).len() as u64;
    (founders < m + 1).then_some("stalled_recovery_needs_bundle")
}

/// The room's protocol in force at protocol row `r` ([`policy_in_force`]): in a community, the record's protocol
/// ([`community_protocol`]) over the members, with the record's numbers; in an infrastructure community, a strict
/// majority of the `founder` seats at the row's heads (CC 3.2, the Constitution's P1 and Q5: N counted by the kernel,
/// M = N / 2 + 1; the founding record's word is checked against its signers, [`founders_of`], and a change's word
/// against the founders at its own heads). `open:self_admit` governs admissions alone (an offer of the member seat):
/// the set states no removal under it, and a change of the record is never counted as an admission.
fn protocol_part<'a, R: SeatRow>(law: &SeatLaw, p: &Past<'_, 'a, R>, r: &R) -> Result<InForce<'a, R>, ()> {
    let get = |i: &R::Id| p.get(i);
    let get: &dyn Fn(&R::Id) -> Option<&'a R> = &get;
    let obj = r.obj().ok_or(())?;
    let rec = protocol_record(p, &obj).ok_or(())?;
    let counted = r.counted().map_or("member", |c| c.as_ref());
    if kind_of(law, get, &obj) == Some(CommunityKind::Infrastructure) {
        // CC 3.2, "Live and stalled": the record's M founder voices (absolute, never recomputed), over the `founder`
        // seats held at the row's heads; live while they number at least M + 1, and N caps them (both read by the
        // count). A founding row seating more founders than N founds no protocol that concludes
        let Obj::Row(i) = &obj else { return Err(()) };
        let founding = p.get(i).ok_or(())?;
        let word = rec.consensus_protocol().ok_or(())?;
        let Some(RoomProtocol::Quorum(m, n)) = RoomProtocol::parse_in(word.as_ref(), true) else { return Err(()) };
        let (m, n) = (usize::try_from(m).map_err(|_| ())?, usize::try_from(n).map_err(|_| ())?);
        // its record MUST be entrenched; its founding word states N = the founders it seats; and a founder seat is
        // added only by a founders' amendment (or the stalled recovery widening): a plain founder widening is none
        if founding.protocol_entrenched() != Some(true) {
            return Err(());
        }
        if core::ptr::eq(rec, founding) && founders_of(get, &obj) != n {
            return Err(());
        }
        if r.seat_kind() == SeatKind::Offer && r.scope().is_some_and(|s| s.as_ref() == "founder") {
            return Err(());
        }
        if counted != "founder" {
            return Err(());
        }
        // the founder removed is not counted
        let base_excludes_target = r.seat_kind() == SeatKind::Unseat;
        return Ok(InForce {
            infra: Some((m, n)),
            base_excludes_target,
            ..InForce::plain(Some(Policy::Declared), Some(m))
        });
    }
    let word = rec.consensus_protocol().ok_or(())?;
    let family = kind_of(law, get, &obj) == Some(CommunityKind::Family);
    let proto = if family {
        // a family (CC 3.3.4, 3.1.3.2, 4.5.12.5): every protocol of the set, founder_only and quorum:1/n included, and
        // no floor of two voices; its record carries no duty map, its founder roles apart (F4: duty_holders_on_family)
        let Obj::Row(i) = &obj else { return Err(()) };
        if p.get(i).ok_or(())?.duty_holders().iter().any(|(d, _)| d.as_ref() != "founder") {
            return Err(());
        }
        RoomProtocol::parse(word.as_ref()).ok_or(())?
    } else {
        community_protocol(word.as_ref(), rec.need(), rec.weights()).ok_or(())?
    };
    // the body: a family under founder_only counts its active founders (the `founder` role standing at the row's
    // heads: the founding roles and later conferred ones, less demotions and leavings); every other count its members
    let body = if family && proto == RoomProtocol::FounderOnly { "founder" } else { "member" };
    if counted != body {
        return Err(());
    }
    if family && proto == RoomProtocol::FounderOnly {
        // each act takes one active founder; a removal (a demotion too) one other than the one it names
        let exclude_target = r.seat_kind() == SeatKind::Unseat;
        return Ok(InForce { exclude_target, ..InForce::plain(Some(Policy::One), None) });
    }
    if proto == RoomProtocol::SelfAdmit
        && (r.seat_kind() != SeatKind::Offer || !r.scope().is_some_and(|s| s.as_ref() == "member"))
    {
        return Err(());
    }
    // a record weighing one key twice states no weights
    if proto == RoomProtocol::Weighted {
        let w = rec.weights();
        if w.iter().map(|(k, _)| k).collect::<BTreeSet<_>>().len() != w.len() {
            return Err(());
        }
    }
    let (pol, need) = match proto {
        RoomProtocol::Unanimous => (Policy::Unanimous, None),
        RoomProtocol::Majority => (Policy::Strict(1, 2), None),
        RoomProtocol::Quorum(m, _) => (Policy::Declared, Some(usize::try_from(m).map_err(|_| ())?)),
        RoomProtocol::Weighted => (Policy::Weighted, rec.need()),
        RoomProtocol::SelfAdmit => (Policy::SelfAdmit, None),
        // a family's protocol: no community declares it (community_protocol), so this arm is not reached
        RoomProtocol::FounderOnly => (Policy::One, None),
    };
    Ok(InForce {
        weights: Some(rec),
        no_self_removal: family && r.seat_kind() == SeatKind::Unseat,
        // a removal under the room's protocol counts the other members (the sheet's removal rules for quorum and
        // weighted are the admission rule over them; unanimous reads its own rule)
        base_excludes_target: r.seat_kind() == SeatKind::Unseat && proto != RoomProtocol::Unanimous,
        // in a community the floor is never fewer than two voices, so one voice never decides who is in a room,
        // whatever its size (CC 4.5.13): a counted removal takes two voices besides the member it removes (a family
        // has no floor)
        floor: if r.seat_kind() == SeatKind::Unseat && !family { law.removal_floor } else { 0 },
        ..InForce::plain(Some(pol), need)
    })
}

/// Whether counted row `r` is the members' lift: its act ([`act_of`]) where the binding is on and the object has a
/// kind, its policy in force (`pol`, [`Policy::Lift`]) otherwise.
fn is_lift<'r, R: SeatRow + 'r>(
    law: &SeatLaw,
    get: &dyn Fn(&R::Id) -> Option<&'r R>,
    r: &R,
    pol: Option<Policy>,
) -> bool {
    match law.acts.as_ref().and_then(|_| act_of(law, get, r)) {
        Some((act, _, _)) => act == Act::Lift,
        None => pol == Some(Policy::Lift),
    }
}

/// The policy rows an act may take over a scope class and a kind of object, and whether the counted row chooses
/// one of them ([`Choice::Row`]) or the act fixes it ([`Choice::Fixed`]): the acts table's row, or `None` (no row,
/// or a law that binds no act: [`SeatLaw::acts`] `None`). What a store asks so that it keeps no list of its own.
pub fn policy_for(law: &SeatLaw, act: Act, scope: ScopeClass, kind: CommunityKind) -> Option<(&[String], Choice)> {
    law.acts
        .as_ref()?
        .iter()
        .find(|a| a.act == act && a.scope == scope && a.kind == kind)
        .map(|a| (a.policies.as_slice(), a.choice))
}

/// Whether a scope held covers the scope wanted: equal, or the wanted one narrower by a `:` segment.
pub fn covers(have: &str, want: &str) -> bool {
    have == want || (want.len() > have.len() && want.starts_with(have) && want.as_bytes()[have.len()] == b':')
}

type ObjOf<R> = Obj<<R as Row>::Id, <R as Row>::Key>;
/// One seat of an offer: the offer and the seat's scope.
type SeatOf<R> = (<R as Row>::Id, <R as SeatRow>::Word);
/// Keyed by the heads, the acceptances and withdrawals of the row's own past read with them, the changes void for
/// the row being read, the object and the scope.
type MembersMemo<R> = BTreeMap<
    (Vec<<R as Row>::Id>, Vec<<R as Row>::Id>, Vec<<R as Row>::Id>, ObjOf<R>, String),
    BTreeSet<<R as Row>::Key>,
>;
/// One tip's line: the concluded rows in its past with it, and the offers that seat each key there.
type Line<R> = (Vec<usize>, BTreeMap<<R as Row>::Key, BTreeSet<<R as Row>::Id>>);
type CommonMemo<R> = RefCell<BTreeMap<(String, ObjOf<R>), Option<BTreeSet<<R as Row>::Key>>>>;
type Step<'r, R> = (
    (&'r <R as Row>::Id, &'r <R as Row>::Key, Sc<'r, <R as SeatRow>::Word>),
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

pub(crate) fn signers<R: SeatRow>(r: &R) -> BTreeSet<R::Key> {
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
    /// H6: every row `own` signed or cosigned (its seating or acceptance, a counted row, a cosignature, its
    /// withdrawal, a window's row, an acknowledgement, content) is over the object [`object_of`] reads.
    fn acknowledges<'r>(&self, r: &'r R, own: &R::Key, get: &dyn Fn(&R::Id) -> Option<&'r R>) -> Option<Self::Obj> {
        if r.signer() == own || r.cosigners().contains(own) {
            object_of(r, get)
        } else {
            None
        }
    }
}

/// The scope of an AI agent's seat over a room (CC 4.5.13): on the roster, and in no count.
pub const AGENT: &str = "agent";
/// The seat of a node over an infrastructure community: on the roster, no voice and in no base, as an agent's
/// seat ([`persons`] leaves its holders out of every count).
pub const NODE: &str = "node";

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

/// The scope of a seat the walk holds: a word a row carries, or `moderate`, which the lone signer of a founding
/// record holds whatever the record carries ([`SeatRow::word`] makes it when a seat is read out).
#[derive(Debug, PartialEq, Eq, PartialOrd, Ord)]
enum Sc<'a, W> {
    /// A word of a row.
    Row(&'a W),
    /// `moderate`, held by a lone founder.
    Moderate,
}

/// A seat the walk starts from: the offer's index, the key it seats, and the scope.
type BaseSeat<'a, R> = (usize, &'a <R as Row>::Key, Sc<'a, <R as SeatRow>::Word>);

impl<W> Clone for Sc<'_, W> {
    fn clone(&self) -> Self {
        *self
    }
}
impl<W> Copy for Sc<'_, W> {}

impl<W: AsRef<str>> Sc<'_, W> {
    fn s(&self) -> &str {
        match self {
            Sc::Row(w) => w.as_ref(),
            Sc::Moderate => "moderate",
        }
    }
}

/// A founding record one person signs with no `duty_holders` map (CC 4.5.4): a community's founding row (scope
/// `member`) whose `to` is one key, signed by that key and by no other. The older presentation, a lone
/// founder's row of scope `duty`, is read as before.
fn lone_founding<R: SeatRow>(o: &R) -> bool {
    // a family holds no duty seat (F4)
    founding(o)
        && !o.group_kind().is_some_and(|k| k.as_ref() == "family")
        && o.duty_holders().is_empty()
        && o.scope().map(|s| s.as_ref()) == Some("member")
        && o.to().len() == 1
        && *o.signer() == o.to()[0]
        && o.cosigners().iter().all(|c| c == o.signer())
}

/// The scopes offer `o` seats key `k` in (`signed`: k signed it). One, the offer's own scope, for every offer
/// but a founding row. A founding row seats by the signatures on it (CC 3.1.3.2: a listed key that did not sign
/// is `membership_founding_member_unsigned`, and joins by an ordinary admission): a listed member who did not
/// sign it in nothing, whatever it accepts later; one who signed it in its own scope, and where it has a
/// `duty_holders` map, in each duty whose entry names it. The lone signer of a record with no map holds
/// `moderate` and each duty its record declares ([`SeatRow::duties`]), not the law's other named duties.
fn seat_scopes<'a, R: SeatRow>(o: &'a R, k: &R::Key, signed: bool) -> Vec<Sc<'a, R::Word>> {
    let Some(own) = o.scope() else { return Vec::new() };
    if !founding(o) {
        // an admission carrying `role: founder` (a family's one-row founder admission) seats the founder role too; a
        // founders' amendment of an infrastructure record (scope `record`) seats its keys as founders
        // (only on a counted row: an own or uncounted offer's role seats nothing)
        if let Some(role) = o.role().filter(|x| x.as_ref() == "founder" && o.conf() == Some(Conf::Group)) {
            match own.as_ref() {
                "member" => return alloc::vec![Sc::Row(own), Sc::Row(role)],
                "record" => return alloc::vec![Sc::Row(role)],
                _ => {}
            }
        }
        return alloc::vec![Sc::Row(own)];
    }
    if !signed {
        return Vec::new();
    }
    if lone_founding(o) {
        let mut out = alloc::vec![Sc::Row(own), Sc::Moderate];
        out.extend(
            o.duties()
                .iter()
                .filter(|d| *d != own && d.as_ref() != "moderate" && !roster_word(d.as_ref()))
                .map(Sc::Row),
        );
        return out;
    }
    if o.duty_holders().is_empty() {
        return alloc::vec![Sc::Row(own)];
    }
    let mut out = alloc::vec![Sc::Row(own)];
    out.extend(o.duty_holders().iter().filter(|(d, ks)| ks.contains(k) && d != own).map(|(d, _)| Sc::Row(d)));
    out
}

/// A family's founder role conferred after founding (a promotion, or an admission carrying the role): a seat of scope
/// `founder` over a family that stands only on the member's seat, and ends with the member's stay (F1).
fn family_role_seat<R: SeatRow>(by: &BTreeMap<&R::Id, &R>, o: &R, sc: &str) -> bool {
    sc == "founder"
        && !founding(o)
        && o.obj()
            .and_then(|ob| row_of(by, &ob))
            .is_some_and(|g| g.group_kind().is_some_and(|k| k.as_ref() == "family"))
}

/// A duty seat a founding row gives by its `duty_holders` map, or to its lone signer: a seat of that row in a
/// scope not its own.
fn founding_duty<R: SeatRow>(o: &R, sc: &str) -> bool {
    (!o.duty_holders().is_empty() || lone_founding(o)) && founding(o) && o.scope().map(|x| x.as_ref()) != Some(sc)
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
    community(by, obj)
        && row_of(by, obj)
            .is_some_and(|g| g.scope().map(|s| s.as_ref()) == Some("duty") || lists_holders(g) || lone_founding(g))
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
fn duty_held<R: SeatRow>(law: &SeatLaw, by: &BTreeMap<&R::Id, &R>, o: &R, sc: &str) -> bool {
    if founding_duty(o, sc) || family_role_seat(by, o, sc) {
        return true;
    }
    let Some(obj) = o.obj() else { return false };
    let roster = o.scope().is_some_and(|s| law.roster_seats.iter().any(|x| x == s.as_ref()));
    community(by, &obj) && !founding(o) && !roster && law.is_duty(sc, &declared(by, &obj))
}

/// The seat of offer `o` in scope `s` is the roster's own over a community: a scope its duty holders do not
/// place, or the founding row's own scope where it holds `member`. Every other seat over the community is a
/// duty seat.
fn roster_seat<R: SeatRow>(law: &SeatLaw, o: &R, s: &str) -> bool {
    let roster = law.roster_seats.iter().any(|x| x == s);
    let own = (o.obj() == Some(Obj::Row(o.id().clone())) && o.scope().map(|x| x.as_ref()) == Some(s)) || roster;
    own && (roster || covers(s, "member") || law.holds.get(s).is_some_and(|h| h.iter().any(|x| x == "member")))
}

/// The presence a seat `sc` of offer `o` is in its room, compared by what the scopes hold and not by name:
/// [`AGENT`] for an agent's seat; `member` for a roster seat that is or holds membership (`member`, a founding
/// scope holding it, as the founding `duty` seat does, `founder` where it holds `member`); another roster seat's
/// own name; `None` for a seat that is no presence (a duty, a detector).
fn seat_class<'s, R: SeatRow>(law: &SeatLaw, o: &R, sc: &'s str) -> Option<&'s str> {
    if sc == AGENT {
        return Some(AGENT);
    }
    let holds_member = covers(sc, "member") || law.holds.get(sc).is_some_and(|h| h.iter().any(|x| x == "member"));
    if roster_seat(law, o, sc) {
        return Some(if holds_member { "member" } else { sc });
    }
    (holds_member && !law.is_duty(sc, &[])).then_some("member")
}

/// Key `k` consented to offer `t`: it signed it, or an acceptance of it by `k` is in the withdrawal's own
/// concluded past (`before`: one naming it, or a standing acceptance the offer names, of its scope and object). A
/// withdrawal of an offer `k` never consented to is a decline: it ends that offer for `k` and nothing else, and is
/// no end of a stay.
fn consented<R: SeatRow>(by: &BTreeMap<&R::Id, &R>, t: &R, k: &R::Key, before: &dyn Fn(&R) -> bool) -> bool {
    signed_by(t, k)
        || by.values().any(|a| {
            a.seat_kind() == SeatKind::Accept
                && a.signer() == k
                && before(*a)
                && (a.of() == Some(t.id())
                    || (a.of().is_none()
                        && t.names().contains(a.id())
                        && a.scope() == t.scope()
                        && a.obj().is_none_or(|x| Some(x) == t.obj())))
        })
}

/// [`roster_seat`] in the offer's own scope.
fn roster_offer<R: SeatRow>(law: &SeatLaw, o: &R) -> bool {
    o.scope().is_some_and(|s| roster_seat(law, o, s.as_ref()))
}

/// Whether withdrawal `w` is its signer's own end of a stay as a member, and of which community: a withdrawal
/// by a key of an offer of the roster's seat that names it, or of its own acceptance of one (the offer the
/// acceptance names, or a standing acceptance's own scope and object). `before(a)`: row `a` is concluded and in
/// `w`'s past; the consent a withdrawal ends is read there only (a row written after it, or one that concludes
/// nothing, is none).
pub(crate) fn stay_end<R: SeatRow>(
    law: &SeatLaw,
    by: &BTreeMap<&R::Id, &R>,
    w: &R,
    before: &dyn Fn(&R) -> bool,
) -> Option<ObjOf<R>> {
    let k = w.signer();
    let mut t = *by.get(w.target()?)?;
    // a withdrawal that names a duty seat lays down that seat, and the stay goes on
    // and one naming a roster scope ends the stay only where its target gives the signer that seat
    if let Some(ws) = w.scope() {
        let offer = t.seat_kind() == SeatKind::Offer;
        if !(offer && roster_seat(law, t, ws.as_ref()))
            || !seat_scopes(t, k, signed_by(t, k)).iter().any(|s| s.s() == ws.as_ref())
        {
            return None;
        }
    }
    if t.seat_kind() == SeatKind::Accept && t.signer() == k {
        match t.of() {
            Some(of) => t = *by.get(of)?,
            None => {
                let (obj, s) = (t.obj()?, t.scope()?);
                let roster = law.roster_seats.iter().any(|x| x == s.as_ref());
                // a standing acceptance withdrawn ends a stay only where an offer seating k named it
                let used = by.values().any(|m| {
                    m.seat_kind() == SeatKind::Offer
                        && m.obj().as_ref() == Some(&obj)
                        && m.to().contains(k)
                        && m.scope() == Some(s)
                        && m.names().contains(t.id())
                        && before(*m)
                });
                return (roster && community(by, &obj) && used).then_some(obj);
            }
        }
    }
    if t.seat_kind() != SeatKind::Offer || !t.to().contains(k) || !consented(by, t, k, before) {
        return None; // a key that never consented to the offer it withdraws declines it
    }
    let obj = t.obj()?;
    (community(by, &obj) && roster_offer(law, t)).then_some(obj)
}

/// The roster seat a key's own end of its stay ([`stay_end`]) ends: the scope the withdrawal names, or else the
/// scope of the offer it withdraws (through an acceptance, the offer accepted, or a standing acceptance's own).
fn end_scope<'a, R: SeatRow>(by: &BTreeMap<&R::Id, &'a R>, w: &'a R) -> Option<&'a R::Word> {
    if let Some(s) = w.scope() {
        return Some(s);
    }
    let t = *by.get(w.target()?)?;
    match (t.seat_kind(), t.of()) {
        (SeatKind::Accept, Some(of)) => {
            let o: &'a R = *by.get(of)?;
            o.scope()
        }
        _ => t.scope(),
    }
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
    let Some(g) = row_of(by, obj) else { return Vec::new() };
    // `moderate` is "a duty every community's record declares" (CC 4.5.4), whatever the law's own list names: the
    // one-founder room's founder holds it, and holds it as a duty
    let every = community(by, obj).then_some("moderate");
    every.into_iter().chain(g.duties().iter().map(|d| d.as_ref()).filter(|d| !roster_word(d))).collect()
}

/// A roster scope (a member's, an agent's): never a duty a record declares, so a record's entry naming one is
/// ignored.
fn roster_word(d: &str) -> bool {
    d == "member" || d == AGENT
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
    /// The election's seatings that do not stand (C4, C5): they seat nobody and are no tip.
    beaten: BTreeSet<usize>,
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
        Self::build_r(c, law, spec, own, None, None, None, true)
    }

    /// The reader's roster (the ruling of 2026-11-27): [`Seats::new`] over the rows as they conclude for reader
    /// `own` ([`for_reader`] gives them, and the changes void for that reader, `reader`). A count that stands for
    /// this reader and not for a reader with no row is in its roster; one refused for it is not (CC 2.7.9).
    pub fn for_reader(
        c: &'c Concluded<'a, R>,
        law: &'c SeatLaw,
        spec: &'c S,
        own: &R::Key,
        reader: &BTreeSet<R::Id>,
    ) -> Self {
        Self::build_r(c, law, spec, Some(own), None, None, Some(reader), true)
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
        Self::build_r(c, law, spec, own, drop, cache, None, false)
    }

    #[allow(clippy::too_many_arguments)]
    fn build_r(
        c: &'c Concluded<'a, R>,
        law: &'c SeatLaw,
        spec: &'c S,
        own: Option<&R::Key>,
        drop: Option<&BTreeSet<R::Id>>,
        cache: Option<&MembersAt<R>>,
        reader: Option<&BTreeSet<R::Id>>,
        roster: bool,
    ) -> Self {
        // the reader's line is read before the cut: a counted act void for this reader (behind its line, or built
        // on such an act, every row taken as counting) cuts nothing for it (CC 2.7.8). A counted row the reader
        // signed acknowledges the changes in its past but those void for it ([`ack_void`]), and, over the rows
        // concluded for the reader, those void for the reader
        // an election's seating sits on the line by the heads it names, as any roster change
        let except = |a: usize| -> BTreeSet<usize> { ack_void(c, law, spec, a, reader) };
        let mut behind = if own.is_some() {
            line::void_except(c, &SeatLine, own, |_| true, |_| false, &except)
        } else {
            BTreeSet::new()
        };
        // a reader's roster reads S'' over the rows it holds: a change self-forked there cuts nothing and seats
        // nothing (a void change neither adds nor removes members); the readings of a line inside the kernel do not
        if roster {
            behind.extend(roster_void(c, law, spec, reader));
        }
        let cut = Cut::new_without(c, spec, &behind);
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
                    if let Some(room) = stay_end(law, &by, r, &|a| c.concluded_id(a.id()) && g.id_in_past(a.id(), i)) {
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
        // the election (C4, C5): the seatings that do not stand, and per seating its twins (the seatings over its
        // set of its election: one seat, so its holder's withdrawal of any of them ends it)
        let local_e = MembersAt::<R>::default();
        let elections = cs.iter().any(|&i| election::is_election(law, g.row(i)));
        // for a reader, the seat ends behind its line are no vacancy ends ([`reader_ends`])
        if let (true, Some(k)) = (elections, own) {
            *local_e.rends.borrow_mut() = reader_ends(c, law, spec, k, reader);
        }
        let memo_e = if own.is_some() { &local_e } else { cache.unwrap_or(&local_e) };
        let ecx = election::Ctx { c, law, spec, memo: memo_e };
        let twins = if elections { ecx.twins() } else { BTreeMap::new() };
        let twin_ids: BTreeMap<&R::Id, Vec<&R::Id>> = twins
            .iter()
            .map(|(&q, ts)| (g.row(q).id(), ts.iter().filter(|&&t| t != q).map(|&t| g.row(t).id()).collect()))
            .collect();
        let none_ids: Vec<&R::Id> = Vec::new();
        // a withdrawal that names a scope ends that one seat of the row it withdraws
        let off_ended = |o: &R, k: &R::Key, sc: Sc<'a, R::Word>| {
            let own = |w: &&R| {
                w.target() == Some(o.id())
                    && (w.signer() == k || (!o.to().contains(w.signer()) && o.conf() != Some(Conf::Group) && !eq(o)))
                    && w.scope().is_none_or(|ws| ws.as_ref() == sc.s())
            };
            // the holder's withdrawal of a twin seating ends this one
            let twin = |t: &&R::Id| wd_of(t).iter().any(|w| w.signer() == k && o.to().contains(w.signer()));
            wd_of(o.id()).iter().any(own) || twin_ids.get(o.id()).unwrap_or(&none_ids).iter().any(twin)
        };
        // the changes void in the first pass and the roster's S'' void cut nothing (`cut` is built without them),
        // and still count for the line's settle, so a merge of both lines built on one of them is not void, as the
        // reference's checkpoint.void over Cut(S, without=L) reads it
        let mut stale = line::void_except(c, &SeatLine, own, |i| cut.counts(i), |_| false, &except);
        stale.extend(behind.iter().copied());
        // a seating behind the reader's line does not stand for it and takes no part in C4
        let beaten = if elections { ecx.beaten(&stale) } else { BTreeSet::new() };
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
        let mut dropped = match drop {
            Some(d) => d.clone(),
            None => out_of_force(c, law, spec, own, &by, &unseats, cache.unwrap_or(&local)),
        };
        let unseats: Vec<(usize, Option<ObjOf<R>>)> = if dropped.is_empty() {
            unseats
        } else {
            unseats.into_iter().filter(|(u, _)| !dropped.contains(g.row(*u).id())).collect()
        };
        // CC 2.7.7 rule 5: counted removals that remove each other's voices concurrently are contested, and neither
        // is in force (a voice concurrent with its own removal is no voice). Judged over the whole set, and carried
        // with the lone removals out of force into a reading of one line of it (the tips, the fold)
        // a dissolution is a cut over every seat of its group, so it is contested as a removal is (the ruling on FA6)
        let cuts: Vec<(usize, Option<ObjOf<R>>)> = unseats
            .iter()
            .cloned()
            .chain(
                cs.iter()
                    .copied()
                    .filter(|&i| {
                        let q = g.row(i);
                        is_dissolve(q) && cut.counts(i) && !stale.contains(&i) && !dropped.contains(q.id())
                    })
                    .map(|i| (i, g.row(i).obj())),
            )
            .collect();
        let contested = contested_out(c, law, spec, &cuts, cache.unwrap_or(&local));
        let unseats: Vec<(usize, Option<ObjOf<R>>)> = if contested.is_empty() {
            unseats
        } else {
            unseats.into_iter().filter(|(u, _)| !contested.contains(g.row(*u).id())).collect()
        };
        dropped.extend(contested);
        // a removal from the roster: of a member's seat, or of any seat the law names the roster's own
        let member = |s: Option<&R::Word>| {
            s.is_some_and(|x| x.as_ref() == "member" || law.roster_seats.iter().any(|r| r == x.as_ref()))
        };
        // a self roster's lone-path eviction that LANDED (its `landed` landing concluded: the window's outcome, as
        // every window) ends the target's seat as a counted eviction does: one ends reading
        let landed0: Vec<(usize, &R::Key, ObjOf<R>, &R::Word, &R::Key)> = cs
            .iter()
            .copied()
            .filter(|i| !stale.contains(i))
            .filter_map(|i| {
                let (op, says) = g.row(i).landing()?;
                if says.as_ref() != "landed" {
                    return None;
                }
                let p = *by.get(op)?;
                if !c.concluded_id(p.id()) {
                    return None;
                }
                let t = p.evicts()?;
                let o = p.obj()?;
                let sc = match &o {
                    Obj::Row(gid) => by.get(gid)?.scope()?,
                    Obj::Key(_) => return None,
                };
                Some((i, t, o, sc, p.signer()))
            })
            .collect();
        // two concurrent landed evictions of each other (each one's target the other's opener, over one roster) are
        // contested (rule 4, CC 2.7.7 rule 5): neither lands, as where both object
        let landed: Vec<(usize, &R::Key, ObjOf<R>, &R::Word)> = landed0
            .iter()
            .filter(|(i, t, o, _, s)| {
                !landed0
                    .iter()
                    .any(|(j, t2, o2, _, s2)| j != i && o2 == o && t2 == s && t == s2 && g.concurrent(*i, *j))
            })
            .map(|(i, t, o, sc, _)| (*i, *t, o.clone(), *sc))
            .collect();
        let unseated = |oi: usize, k: &R::Key, sc: Sc<'a, R::Word>| {
            if landed.iter().any(|(l, t, lo, lsc)| {
                *t == k && g.row(oi).obj().as_ref() == Some(lo) && lsc.as_ref() == sc.s() && g.in_past(oi, *l)
            }) {
                return true;
            }
            if unseats.is_empty() {
                return false;
            }
            let o = g.row(oi);
            let dutyish = law.is_duty(sc.s(), &[])
                || duty_seat(law, &by, o)
                || founding_duty(o, sc.s())
                || family_role_seat(&by, o, sc.s());
            let oo = o.obj();
            unseats.iter().any(|(u, uo)| {
                let (u, ur) = (*u, g.row(*u));
                let same = ur.to().contains(k) && *uo == oo;
                let held = same
                    && (ur.scope().map(|x| x.as_ref()) == Some(sc.s())
                        || (dutyish
                            && member(ur.scope())
                            && oo.as_ref().is_some_and(|x| holds_roster(c, law, u, k, x))));
                held && g.in_past(oi, u)
            })
        };
        // a duty seat whose offer is in the past of its holder's own end of its stay as a member is ended by it
        // and so is every seat of the key in the roster scope its end ends, whatever row seated it: an end is of the
        // key's stay in that scope, not of a row, as a counted removal's cut reaches every offer on the slot in its past
        // end `w` (a key's own end of its stay) ends `o`'s seat `sc`: the two seats are the same presence
        let same_class = |w: usize, o: &R, sc: &str| {
            let wr = g.row(w);
            let mut t = wr.target().and_then(|t| by.get(t)).copied();
            if let Some(a) = t.filter(|a| a.seat_kind() == SeatKind::Accept) {
                if let Some(of) = a.of() {
                    t = by.get(of).copied();
                }
            }
            end_scope(&by, wr).is_some_and(|es| {
                let a = seat_class(law, t.unwrap_or(o), es.as_ref());
                a.is_some() && a == seat_class(law, o, sc)
            })
        };
        let resigned = |oi: usize, k: &R::Key, sc: Sc<'a, R::Word>| {
            if left.is_empty() {
                return false;
            }
            let o = g.row(oi);
            let oo = o.obj();
            let duty = duty_held(law, &by, o, sc.s());
            left.iter().any(|(w, k2, room)| {
                *k2 == k && oo.as_ref() == Some(room) && g.in_past(oi, *w) && (duty || same_class(*w, o, sc.s()))
            })
        };
        // a key's own row on a roster seat concurrent with its own end of its stay there (neither in the other's
        // past) is no voice: its signature on the offer, or its acceptance of it (CIRISConstitution#224, ruled: the
        // rule a removed key's concurrent rows have, read for the key's own end). Other keys' rows are untouched.
        // and so is one before the end: a consent that does not have the end in its past (a standing acceptance given
        // earlier is a consent like any other)
        let own_void = |row: usize, o: &R, k: &R::Key| {
            let Some(os) = o.scope() else { return false };
            if left.is_empty() || seat_class(law, o, os.as_ref()).is_none() {
                return false;
            }
            let oo = o.obj();
            left.iter().any(|(w, k2, room)| {
                *k2 == k
                    && oo.as_ref() == Some(room)
                    && same_class(*w, o, os.as_ref())
                    && (g.concurrent(row, *w) || g.in_past(row, *w))
            })
        };
        // `signed`: whether k signed the offer, read by the caller once per offer's signer set
        let by_get = |i: &R::Id| by.get(i).copied();
        let accepted = |oi: usize, o: &R, k: &R::Key, signed: bool| {
            if signed {
                return !own_void(oi, o, k);
            }
            // a node's seat over an infrastructure community stands on the founders' count alone (a node has no
            // agency): by its scope and the object's kind; every other seat needs the seated key's own acceptance
            if o.conf() == Some(Conf::Group)
                && o.scope().is_some_and(|x| x.as_ref() == NODE)
                && o.obj().is_some_and(|ob| kind_of(law, &by_get, &ob) == Some(CommunityKind::Infrastructure))
            {
                return true;
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
                    paired && !ended(ar) && cut.counts(a) && !own_void(a, o, k)
                })
            })
        };
        // keys and scopes are borrowed from the rows through the walk, and copied once into each live seat
        let mut base: Vec<BaseSeat<'a, R>> = Vec::new();
        // a concluded dissolution of a group ends every seat over it (it reads as the withdrawal of the group's record)
        // (one contested by rule 5, or carried out of force into this line's reading, ends nothing)
        let gone: Vec<ObjOf<R>> = cs
            .iter()
            .filter(|&&i| cut.counts(i))
            .map(|&i| g.row(i))
            .filter(|q| is_dissolve(*q) && !dropped.contains(q.id()))
            .filter_map(|q| q.obj())
            .collect();
        for &oi in cs {
            let o = g.row(oi);
            if o.seat_kind() != SeatKind::Offer || !cut.counts(oi) || stale.contains(&oi) || beaten.contains(&oi) {
                continue;
            }
            if !gone.is_empty() && o.obj().is_some_and(|ob| gone.contains(&ob)) {
                continue;
            }
            // an offer seating many keys reads its signers as a set, built once (not once per key)
            let many = o.to().len() > SIGNERS_SCANNED;
            let sig: BTreeSet<&R::Key> =
                if many { o.cosigners().iter().chain(core::iter::once(o.signer())).collect() } else { BTreeSet::new() };
            for k in o.to() {
                let signed = if many { sig.contains(k) } else { signed_by(o, k) };
                if !accepted(oi, o, k, signed) {
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
        type At<'r, I, K, W> = BTreeMap<(&'r I, &'r K, Sc<'r, W>), (usize, Root<I, K>)>;
        // per (offer, key), the least depth any of its seats is at: what a seat conferred under it reads
        type Held<'r, I, K> = BTreeMap<(&'r I, &'r K), (usize, Root<I, K>)>;
        let walk = |base: &[BaseSeat<'a, R>]| {
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
        let held: Vec<bool> = base.iter().map(|&(oi, _, sc)| duty_held(law, &by, g.row(oi), sc.s())).collect();
        if held.contains(&true) {
            let mut on: Vec<bool> = base.iter().map(|_| true).collect();
            loop {
                let mem: BTreeSet<(ObjOf<R>, &R::Key)> = at
                    .keys()
                    .filter_map(|&(oid, k, sc)| {
                        let o = by[oid];
                        if roster_seat(law, o, sc.s()) {
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
                let kept: Vec<BaseSeat<'a, R>> =
                    base.iter().zip(&on).filter(|(_, keep)| **keep).map(|(b, _)| *b).collect();
                at = walk(&kept);
            }
        }
        let recs: Vec<Live<R::Id, R::Key, R::Word>> = at
            .into_iter()
            .filter_map(|((oid, k, sc), (depth, root))| {
                let o = by[oid];
                let scope = match sc {
                    Sc::Row(w) => w.clone(),
                    Sc::Moderate => R::word("moderate"),
                };
                Some(Live { offer: oid.clone(), k: k.clone(), scope, obj: o.obj()?, depth, root })
            })
            .collect();
        let mut duty: Vec<bool> =
            recs.iter().map(|r| by.get(&r.offer).is_some_and(|o| duty_held(law, &by, *o, r.scope.as_ref()))).collect();
        // a self roster's lone-path addition that LANDED seats each key that signed its opener, as a counted addition
        // does, and the same ends reading ends it (a later counted or landed eviction, with the landing in its past)
        let mut recs = recs;
        for i in cs.iter().copied().filter(|i| !stale.contains(i)) {
            let Some((op, says)) = g.row(i).landing() else { continue };
            if says.as_ref() != "landed" {
                continue;
            }
            let Some(p) = by.get(op).copied() else { continue };
            if !c.concluded_id(p.id()) {
                continue;
            }
            let Some(keys) = p.adds() else { continue };
            let Some(o) = p.obj() else { continue };
            let Some(sc) = (match &o {
                Obj::Row(gid) => by.get(gid).and_then(|f| f.scope()),
                Obj::Key(_) => None,
            }) else {
                continue;
            };
            for k in keys.iter().filter(|k| p.signer() == *k || p.cosigners().contains(*k)) {
                let ended = unseats.iter().any(|(u, uo)| {
                    let ur = g.row(*u);
                    ur.to().contains(k)
                        && uo.as_ref() == Some(&o)
                        && ur.scope().is_some_and(|x| x.as_ref() == sc.as_ref())
                        && g.in_past(i, *u)
                }) || landed
                    .iter()
                    .any(|(l, t, lo, lsc)| *t == k && *lo == o && lsc.as_ref() == sc.as_ref() && g.in_past(i, *l));
                if !ended {
                    recs.push(Live {
                        offer: g.row(i).id().clone(),
                        k: k.clone(),
                        scope: sc.clone(),
                        obj: o.clone(),
                        depth: 0,
                        root: Root::Group(o.clone()),
                    });
                    duty.push(false);
                }
            }
        }
        Seats {
            c,
            cut,
            law,
            spec,
            by,
            stale,
            beaten,
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
    /// The cut over it. For a reader (`own` set) it is that reader's: solved without the counted acts behind
    /// the reader's line, which cut nothing for it (0.5.0). With no reader it is the cut over the set.
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

    /// Group `o` is dissolved: a concluded dissolution of it is held ([`SeatRow::dissolves`]), or, with no signer,
    /// every member it seated has an end of their seat (its roster empty, folded at tips, its founding row held, and
    /// a member's own end of its stay among the rows): no row over it concludes.
    pub fn dissolved(&self, o: &ObjOf<R>) -> bool {
        let g = &self.c.g;
        let rows = || self.c.cs().iter().map(|&i| g.row(i));
        if rows().any(|q| is_dissolve(q) && q.obj().as_ref() == Some(o) && !self.dropped.contains(q.id())) {
            return true;
        }
        community(&self.by, o)
            && self.roster(o).is_empty()
            && self.c.cs().iter().any(|&i| {
                let q = g.row(i);
                stay_end(self.law, &self.by, q, &|a| self.c.concluded_id(a.id()) && g.id_in_past(a.id(), i))
                    .is_some_and(|room| room == *o)
            })
    }

    /// The room's whole roster over `o`: the keys holding `member`, [`AGENT`] (CC 4.5.13) and [`NODE`].
    /// Content, wraps and audience read it. No count reads it: a count is taken of the members (or the scope
    /// it names) less the agents.
    pub fn roster(&self, o: &ObjOf<R>) -> BTreeSet<R::Key> {
        let mut m = self.holders("member", o, None);
        m.extend(self.holders(AGENT, o, None));
        m.extend(self.holders(NODE, o, None));
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

    /// **The one owner reading** (CC 3.2), for every caller (`consent`, the node arm, audience; `nodes_of` is its
    /// inverse): the one holder of the `owner` seat over key `node` ([`Seats::one`]: two live owners is none), after
    /// the re-binding rule of [`crate::standing::answers`]: a concluded `owner` offer over the node that has an
    /// earlier binding's offer in its past re-binds it and ends it (a stint, not a rival), whether or not the new
    /// owner has accepted yet. Read over the rows the caller concluded (a reading row's past). `seat.Seats.owner`.
    pub fn owner(&self, node: &R::Key) -> Option<R::Key> {
        let o: ObjOf<R> = Obj::Key(node.clone());
        let c = self.c;
        let rebinds: Vec<usize> = c
            .cs()
            .iter()
            .copied()
            .filter(|&q| {
                let r = c.g.row(q);
                r.seat_kind() == SeatKind::Offer
                    && r.scope().is_some_and(|w| w.as_ref() == "owner")
                    && r.obj().as_ref() == Some(&o)
            })
            .collect();
        let rebound =
            |offer: &R::Id| c.g.idx(offer).is_some_and(|oi| rebinds.iter().any(|&q| q != oi && c.g.in_past(oi, q)));
        crate::ops::one(
            self.recs.iter().filter(|r| r.obj == o && self.has(r, "owner") && !rebound(&r.offer)).map(|r| &r.k),
        )
        .cloned()
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
                    && !self.beaten.contains(&i)
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
    /// A tip's line: the concluded rows in its past, with the acceptances held that complete an offer there (a seat
    /// is two consents, (a): an acceptance concluded after the tip completes the seat its offer places at the tip).
    fn tip_ids(&self, t: usize, o: &ObjOf<R>) -> Vec<usize> {
        let g = &self.c.g;
        let mut ids: Vec<usize> = self.c.cs().iter().copied().filter(|&q| q == t || g.in_past(q, t)).collect();
        let rows: Vec<&R> = self.c.cs().iter().map(|&q| g.row(q)).collect();
        let by: BTreeMap<&R::Id, &R> = rows.iter().map(|q| (q.id(), *q)).collect();
        let at = |q: &R| g.idx(q.id()).is_some_and(|i| i == t || g.in_past(i, t));
        let in_past = |a: &R::Id, b: &R::Id| match (g.idx(a), g.idx(b)) {
            (Some(a), Some(b)) => g.in_past(a, b),
            _ => false,
        };
        ids.extend(completing(&rows, self.law, &by, o, &at, &in_past).iter().filter_map(|q| g.idx(q.id())));
        ids.sort_unstable();
        ids
    }
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
                let ids = self.tip_ids(t, o);
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
        // the regime: once the binding reads it, the room's protocol in force in each tip's past (each act's own
        // policy is fixed by the table and no part of it); with no acts table, the row's stated regime
        // a tip that changes the record's founder set (a founder's seating) is a regime of its own too: tips on either
        // side of it wait at their common members
        // (a founders' amendment of an infrastructure record, scope `record` with role founder, is such a seating too)
        let founders = |t: usize| {
            let r = g.row(t);
            matches!(r.seat_kind(), SeatKind::Offer | SeatKind::Unseat)
                && (r.scope().is_some_and(|s| s.as_ref() == "founder")
                    || (r.scope().is_some_and(|s| s.as_ref() == "record")
                        && r.role().is_some_and(|x| x.as_ref() == "founder")
                        && !r.to().is_empty()))
        };
        let regimes: BTreeSet<(Option<&R::Word>, Option<usize>)> = tp
            .iter()
            .map(|&t| {
                let own = founders(t).then_some(t);
                if self.law.acts.is_none() {
                    return (g.row(t).regime(), own);
                }
                // a tip that is itself a change of the record's protocol is under its NEW protocol, so tips on either
                // side of the change are two regimes and wait (the text's wait rule, the ruling of 2026-11-27)
                if is_amendment(g.row(t), o) {
                    return (g.row(t).consensus_protocol(), own);
                }
                let anc: Vec<usize> = self.c.cs().iter().copied().filter(|&q| g.in_past(q, t)).collect();
                let pt = Past::new(g, t, &anc);
                (protocol_of(&pt, o), own)
            })
            .collect();
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
                let over = obj; // H2: a counted row is counted over its own object
                let counted = r.counted().map(|c| c.as_ref()).unwrap_or("member");
                let ok = if over == *o && counted == s { Some(seated.clone()) } else { self.tips_fold(counted, &over) };
                let mut mem = count_members_with(&p, self.law, self.spec, Some(&members));
                if let Some(ok) = ok {
                    mem.retain(|m| ok.contains(m));
                }
                let Ok(fs) = policy_in_force(self.law, &p, r) else { return false };
                // joined policies are a change of the record's, which seats no key
                let [f] = fs.as_slice() else { return true };
                let pol = f.pol;
                // a re-seating's voices (its act the lift) are the objections it names, counted over the members
                // the fold seats
                let (apart, v) = if is_lift(self.law, &|i| p.get(i), r, pol) {
                    let Some((author, v)) = lift_voices_with(&p, self.law, self.spec, Some(&members)) else {
                        return false;
                    };
                    // the removal's author apart by person (the key removed is an agent's: in no count)
                    (vec![author], v)
                } else {
                    (Vec::new(), voices(r, &p))
                };
                if pol == Some(Policy::DutyConfer) && mem.len() < 2 && lone_offer_stands(self.law, &p, r, &mem) {
                    return false;
                }
                match pol {
                    Some(Policy::Ranked) => true, // an election's ballots are read by the seat rule alone
                    _ => {
                        // the threshold and the weights in force (the record's under the room's protocol)
                        let wr: &R = f.weights.unwrap_or(r);
                        let rows: Vec<&R> = p.rows().collect();
                        let pp = Persons::over(&rows, self.law, self.spec, r.obj().as_ref());
                        let (mem, v) = pp.count(&mem, &v, None, &apart);
                        count_of(pol, true, r.to(), &mem, &v, f.need, |x| {
                            wr.weights().iter().find(|(w, _)| w == x).map_or(0, |(_, n)| *n)
                        })
                    }
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
            let sub: Vec<&R> = self.tip_ids(t, o).into_iter().map(|q| g.row(q)).collect();
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
    c.cs().iter().copied().any(|q| seated_by(law, g.row(q), us, k, obj) && g.in_past(q, u))
}

/// Offer `m` seats key `k` over `obj` in roster scope `us` ([`holds_roster`] of one row): one of the scopes it
/// gives `k` (a founding record's several seats included), or the founding row holding `member`.
fn seated_by<R: SeatRow>(law: &SeatLaw, m: &R, us: &R::Word, k: &R::Key, obj: &ObjOf<R>) -> bool {
    m.seat_kind() == SeatKind::Offer
        && m.obj().as_ref() == Some(obj)
        && m.to().contains(k)
        && (seat_scopes(m, k, signed_by(m, k)).iter().any(|s| s.s() == us.as_ref())
            || (us.as_ref() == "member" && founding(m) && roster_offer(law, m)))
}

/// The room's count's receipt `q` of lone removal `x` (CIRISConstitution#218): a count over the persons of
/// `x`'s room, whatever room or counted scope the row states, at heads none older than `x`'s (each is `x`'s
/// head or has it in its past), the remover no voice of it and not counted over. Its count is [`room_count`]:
/// more than half of the persons of the room less the remover, never fewer than two, whatever policy or need the
/// row states (one key's `accord_halt`, or a declared need of none, is no receipt).
fn count_receipt<R: SeatRow, S: CutSpec<R>>(
    c: &Concluded<'_, R>,
    q: usize,
    x: usize,
    law: &SeatLaw,
    spec: &S,
    cache: &MembersAt<R>,
) -> bool {
    let g = &c.g;
    let (qr, xr) = (g.row(q), g.row(x));
    let Some(obj) = xr.obj() else { return false };
    if qr.obj().as_ref() != Some(&obj) || qr.over().is_some_and(|o| o != obj) {
        return false;
    }
    let hx: Vec<usize> = xr.head().iter().filter_map(|h| g.idx(h)).collect();
    let fresh = |h: &R::Id| g.idx(h).is_some_and(|hi| hx.iter().any(|&e| hi == e || g.in_past(e, hi)));
    if qr.head().is_empty() || !qr.head().iter().all(fresh) {
        return false;
    }
    let anc: Vec<usize> = c.cs().iter().copied().filter(|&a| g.in_past(a, q)).collect();
    let p = Past::new(g, q, &anc);
    let mut mem = persons_at_with(&p, law, spec, &obj, qr.head(), "member", Some(cache));
    for k in left_in_past(&p, &obj, "member") {
        mem.remove(&k);
    }
    // the room less the remover by person, in the base as in the voices (R5: one rule for a count that judges one
    // member's act, as the overturn and the lift)
    let rows: Vec<&R> = p.rows().collect();
    let pp = Persons::over(&rows, law, spec, Some(&obj));
    let (mem, v) = pp.count(&mem, &voices(qr, &p), None, &[xr.signer().clone()]);
    let yes = v.iter().filter(|k| mem.contains(*k)).count();
    // the members' check of one member's act, whatever policy or need the row states
    room_count(yes, mem.len())
}

/// The members' check of one member's act (the overturn's lift, the count's receipt of a lone removal): more than
/// half of the base, never fewer than two voices. Whatever policy or need a row states, these counts are read by
/// this rule alone.
fn room_count(yes: usize, base: usize) -> bool {
    2 * yes > base && yes >= 2
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
    let lone: BTreeSet<usize> = acts.iter().copied().collect();
    // No cascade (CIRISConstitution#218): a lone removal out of force ends no standing (and voids no receipt: a
    // receipter is a person, and a lone removal removes only an agent). So an act's verdict waits for the verdict
    // of every other lone removal y that could end its remover's standing (y removes the remover), whether y is
    // in its past (an end it reads under E4 only if y is in force), concurrent with it, or after it (E8). One
    // exception, an ordered pair: where y has x in its past and x could end y's standing too, y is in
    // force only if x is not, so y cannot be what puts x out of force: x is decided first, without y (no end of
    // it and no cut in its reading), and y then reads x's verdict. The acts are decided one strongly connected
    // component at a time, in rounds: every component whose waits are decided, against what the rounds before
    // decided out of force. A component of two or more (agent moderators removing each other at one head, a pair
    // or a ring) is decided together, each read as an end of another's: CC 2.7.7 rule 5, read for a set, two cuts
    // by keys of equal standing that undo each other stay contested, until a voice none of them can remove
    // settles them (a person's receipt, or the count's).
    let n = acts.len();
    // act j could end the standing of act i's remover: it removes that remover
    let dep = |i: usize, j: usize| {
        let (xr, yr) = (g.row(acts[i]), g.row(acts[j]));
        i != j && yr.obj() == xr.obj() && yr.to().first() == Some(xr.signer())
    };
    // the ordered pairs act i opens: a later act it could end, which could end it
    let after: Vec<BTreeSet<usize>> =
        (0..n).map(|i| (0..n).filter(|&j| dep(i, j) && dep(j, i) && g.in_past(acts[i], acts[j])).collect()).collect();
    let waits: Vec<BTreeSet<usize>> =
        (0..n).map(|i| (0..n).filter(|&j| dep(i, j) && !after[i].contains(&j)).collect()).collect();
    let mut nows: BTreeMap<BTreeSet<R::Id>, Seats<'_, '_, R, S>> = BTreeMap::new();
    let mut decided: BTreeMap<usize, bool> = BTreeMap::new();
    let mut out: BTreeSet<usize> = BTreeSet::new();
    while decided.len() < n {
        let pend: Vec<usize> = (0..n).filter(|j| !decided.contains_key(j)).collect();
        let reach: Vec<BTreeSet<usize>> = (0..n)
            .map(|i| {
                let mut seen: BTreeSet<usize> = BTreeSet::new();
                if decided.contains_key(&i) {
                    return seen;
                }
                let mut todo = alloc::vec![i];
                while let Some(t) = todo.pop() {
                    for &j in &waits[t] {
                        if !decided.contains_key(&j) && seen.insert(j) {
                            todo.push(j);
                        }
                    }
                }
                seen
            })
            .collect();
        let mut comps: Vec<BTreeSet<usize>> = Vec::new();
        for &i in &pend {
            let mut comp: BTreeSet<usize> = reach[i].iter().copied().filter(|&j| reach[j].contains(&i)).collect();
            comp.insert(i);
            let ready = comp.iter().all(|&m| waits[m].iter().all(|j| decided.contains_key(j) || comp.contains(j)));
            if ready && !comps.contains(&comp) {
                comps.push(comp);
            }
        }
        let excl: BTreeSet<usize> = out.iter().map(|&j| acts[j]).collect();
        let mut got: Vec<(usize, bool)> = Vec::new();
        for comp in &comps {
            for &j in comp {
                // an ordered pair's later act is no end of the earlier, and no cut in its reading
                let ex: BTreeSet<usize> = excl.iter().copied().chain(after[j].iter().map(|&k| acts[k])).collect();
                let drop: BTreeSet<R::Id> = ex.iter().map(|&y| g.row(y).id().clone()).collect();
                let now = nows
                    .entry(drop.clone())
                    .or_insert_with(|| Seats::build(c, law, spec, own, Some(&drop), Some(cache)));
                let v = removal_in_force(c, acts[j], law, spec, by, unseats, now, cache, &ex, &lone);
                got.push((j, v));
            }
        }
        for (j, v) in got {
            decided.insert(j, v);
            if !v {
                out.insert(j);
            }
        }
    }
    let decided: BTreeMap<usize, bool> = decided.into_iter().map(|(j, v)| (acts[j], v)).collect();
    decided.into_iter().filter(|(_, v)| !*v).map(|(x, _)| g.row(x).id().clone()).collect()
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
    not_ends: &BTreeSet<usize>,
    lone: &BTreeSet<usize>,
) -> bool {
    let g = &c.g;
    let xr = g.row(x);
    let Some(obj) = xr.obj() else { return true };
    let m = xr.signer();
    // the standing at the heads x names, and the duty holders there
    let mut standing: BTreeSet<SeatOf<R>> = BTreeSet::new();
    let mut duty: Option<BTreeSet<R::Key>> = None;
    let mut agents: Option<BTreeSet<R::Key>> = None;
    // x's own past: its acceptances that complete a seat at a head it names are read with that head (a seat is two
    // consents: the ruling of 2026-11-26 on acceptances, (a))
    let px: Vec<usize> = c.cs().iter().copied().filter(|&q| g.in_past(q, x)).collect();
    let px_rows: Vec<&R> = px.iter().map(|&q| g.row(q)).collect();
    let in_past = |a: &R::Id, b: &R::Id| match (g.idx(a), g.idx(b)) {
        (Some(a), Some(b)) => g.in_past(a, b),
        _ => false,
    };
    for h in xr.head() {
        let Some(hi) = g.idx(h) else { continue };
        let at = |q: usize| q == hi || g.in_past(q, hi);
        let at_row = |q: &R| g.idx(q.id()).is_some_and(at);
        let acc: Vec<usize> =
            completing(&px_rows, law, by, &obj, &at_row, &in_past).iter().filter_map(|q| g.idx(q.id())).collect();
        // read once per (head, acceptances, object, remover) for every build that shares the cache: the build of a
        // head's past holds lone removals of its own, each read here in turn, and unkept that is a doubling per row
        let mut acc_ids: Vec<R::Id> = acc
            .iter()
            .copied()
            .chain(px.iter().copied().filter(|&q| g.row(q).seat_kind() == SeatKind::Withdraw))
            .map(|a| g.row(a).id().clone())
            .collect();
        acc_ids.sort();
        let key = (h.clone(), acc_ids, obj.clone(), m.clone());
        let known = cache.standing.borrow().get(&key).cloned();
        let (st, d, ag) = match known {
            Some(v) => v,
            None => {
                // and the withdrawals of x's past, as members_at reads them
                let sub: Vec<&R> = c
                    .cs()
                    .iter()
                    .copied()
                    .filter(|&q| {
                        at(q) || acc.contains(&q) || (g.in_past(q, x) && g.row(q).seat_kind() == SeatKind::Withdraw)
                    })
                    .map(|q| g.row(q))
                    .collect();
                let sc = Concluded::with(Graph::new(sub), None);
                let q = Seats::build(&sc, law, spec, None, None, Some(cache));
                let st: BTreeSet<SeatOf<R>> = q
                    .recs
                    .iter()
                    .filter(|r| r.k == *m && r.obj == obj && q.has(r, "moderate"))
                    .map(|r| (r.offer.clone(), r.scope.clone()))
                    .collect();
                let v = (st, q.holders("duty", &obj, None), q.holders(AGENT, &obj, None));
                cache.standing.borrow_mut().insert(key, v.clone());
                v
            }
        };
        standing.extend(st);
        duty = Some(match duty {
            None => d,
            Some(before) => before.intersection(&d).cloned().collect(),
        });
        agents = Some(match agents {
            None => ag,
            Some(before) => before.intersection(&ag).cloned().collect(),
        });
    }
    let agents = agents.unwrap_or_default();
    let mut duty = duty.unwrap_or_default();
    // never the remover's own receipt, and never an agent's: an agent's receipt is no receipt (CC 2.4.1.1;
    // keeping another's act in force is a voice, which an agent does not have), for every lone removal
    duty.remove(m);
    duty.retain(|k| !agents.contains(k));
    // the receipts of x that may keep it: a duty holder's other than the remover's, void where a counted
    // unseat of a seat that key holds over the room does not have the receipt in its past (conferral's
    // key_cut); and the room's own, a counted ack met over the persons at its heads (CIRISConstitution#218)
    let acks: Vec<(usize, bool)> = c
        .cs()
        .iter()
        .copied()
        .filter_map(|q| {
            let qr = g.row(q);
            if qr.seat_kind() != SeatKind::Ack || qr.of() != Some(xr.id()) {
                return None;
            }
            if qr.conf() == Some(Conf::Group) {
                return count_receipt(c, q, x, law, spec, cache).then_some((q, true));
            }
            if !duty.contains(qr.signer()) {
                return None;
            }
            let cut = unseats.iter().any(|(u, uo)| {
                g.row(*u).to().contains(qr.signer())
                    && uo.as_ref() == Some(&obj)
                    && !not_ends.contains(u)
                    && !g.in_past(q, *u)
                    && holds_roster(c, law, *u, qr.signer(), &obj)
            });
            (!cut).then_some((q, false))
        })
        .collect();
    // an end stating `lifts` lifts every receipt but the count's own, in CC 2.4.1.1's cases: (i) a counted end;
    // (iii) a conferrer ending its own offer (its withdrawal of an offer seating another), counted or not: the
    // lone person duty holder's own offer of `moderate` in a room whose record seats no duty holder, ended by its
    // withdrawal. (ii) The holder's own end never lifts (`lifts_on_own_end`, refused at the door; handed one, no
    // lift is read), and a moderator's lone removal lifts nothing.
    let lifts = |e: usize| {
        let er = g.row(e);
        if !er.lifts() {
            return false;
        }
        match er.seat_kind() {
            SeatKind::Unseat => er.conf() == Some(Conf::Group) && !lone.contains(&e),
            SeatKind::Withdraw => er
                .target()
                .and_then(|t| by.get(t))
                .is_some_and(|t| t.seat_kind() == SeatKind::Offer && !t.to().contains(er.signer())),
            _ => false,
        }
    };
    let kept = |e: Option<usize>| {
        acks.iter().any(|&(q, counted)| e.is_none_or(|e| !g.in_past(e, q)) && (counted || e.is_none_or(|e| !lifts(e))))
    };
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
        let held = |a: &R| c.concluded_id(a.id()) && g.id_in_past(a.id(), w);
        let stay = wr.signer() == m && stay_end(law, by, wr, &held).as_ref() == Some(&obj) && after(w);
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
        if *u == x || !ur.to().contains(m) || uo.as_ref() != Some(&obj) || !after(*u) || not_ends.contains(u) {
            continue; // (a lone removal out of force ends no standing: no cascade)
        }
        if roster(ur.scope()) && holds_roster(c, law, *u, m, &obj) {
            found.push((*u, of(&|s| before(&s.0, *u))));
        } else if standing.iter().any(|(_, sc)| ur.scope() == Some(sc)) {
            found.push((*u, of(&|s| before(&s.0, *u) && ur.scope() == Some(&s.1))));
        }
    }
    // an end in the past of the head x names did not end the standing live there (a seat taken up again); nor did
    // one that the remover's own acceptance, in x's past, of a standing offer has in its past
    let again = |e: usize, sc: &BTreeSet<SeatOf<R>>| {
        px.iter().any(|&a| {
            let ar = g.row(a);
            ar.seat_kind() == SeatKind::Accept
                && ar.signer() == m
                && g.in_past(e, a)
                && sc.iter().any(|(o, _)| ar.of() == Some(o))
        })
    };
    found.retain(|(e, sc)| {
        !xr.head().iter().all(|h| g.idx(h).is_some_and(|hi| hi == *e || g.in_past(*e, hi))) && !again(*e, sc)
    });
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
    // read with the binding off only (a stated policy): with the acts table no row states `open:self_admit`'s
    // count, and the reference reads no authored head
    law.acts.is_none()
        && r.seat_kind() == SeatKind::Offer
        && law.policy_of(r.policy().map(|x| x.as_ref())) == Some(Policy::SelfAdmit)
        && r.to().len() == 1
        && r.to()[0] == *r.signer()
}

/// The heads a count is read over: the newest of the heads named (one in another named head's past is
/// dropped). Several concurrent newest heads (tips) stay, and are intersected. An authored head is no head a
/// count may name (H3, the heads ruling of 2026-11-26): it is not read through, and [`newer_head_in_past`]
/// refuses a count naming one.
fn counted_heads<'r, 'h, R: SeatRow + 'r>(
    _law: &SeatLaw,
    heads: &'h [R::Id],
    _row: &dyn Fn(&R::Id) -> Option<&'r R>,
    past: &dyn Fn(&R::Id, &R::Id) -> bool,
) -> alloc::borrow::Cow<'h, [R::Id]> {
    let behind_another = |a: &R::Id| heads.iter().any(|b| a != b && past(a, b));
    if !heads.iter().any(behind_another) {
        return alloc::borrow::Cow::Borrowed(heads); // the usual case: nothing is copied
    }
    alloc::borrow::Cow::Owned(heads.iter().filter(|a| !behind_another(a)).cloned().collect())
}

/// An election's seating: an offer conferred by a count ([`Conf::Group`]) whose policy reads as
/// [`Policy::Ranked`]. A roster change: it names the newest counted changes over the room as its heads (H4) and
/// sits on the reader's line by them. Its count is its election's (roster-kinds' election2: the electorate its
/// id and vacancy fix), never read at its heads; it is a counted change every later counted row must name.
pub fn is_election<R: SeatRow>(law: &SeatLaw, r: &R) -> bool {
    r.seat_kind() == SeatKind::Offer
        && r.conf() == Some(Conf::Group)
        && law.policy_of(r.policy().map(|x| x.as_ref())) == Some(Policy::Ranked)
}

/// The object a row is over: its object, its room, or the object of the row its `of` or `target` names (an
/// acceptance, a cosignature, a withdrawal, a window's answer). `None` where none is read.
pub(crate) fn object_of<'r, R: SeatRow + 'r>(r: &'r R, get: &dyn Fn(&R::Id) -> Option<&'r R>) -> Option<ObjOf<R>> {
    let mut r = r;
    for _ in 0..8 {
        if let Some(o) = r.obj().or_else(|| r.room()) {
            return Some(o);
        }
        let next = if r.seat_kind() == SeatKind::Withdraw { r.target() } else { r.of() };
        match next.filter(|t| *t != r.id()).and_then(get) {
            Some(n) => r = n,
            None => return None,
        }
    }
    None
}

fn concluded_over<'a, R: Row>(rows: impl IntoIterator<Item = &'a R>) -> Concluded<'a, R> {
    Concluded::with(Graph::new(rows), None)
}

/// The key's own end in a row's past, for its person (ruled on CIRISConstitution#224): the key's own revocation
/// (CC 2.4.1.1: "only the key's own revocation ends its liveness"), an unseat of its `registered` seat by the key
/// itself, is among `p` (the row's concluded past). The key record's stated end is read against the key's own
/// instant on the key's own rows ([`crate::key_end`], the half-open end), never here: no foreign clock is read.
pub fn key_record_ended<R: SeatRow>(p: &Past<'_, '_, R>, k: &R::Key) -> bool {
    revoked_itself(p.rows(), k)
}

fn revoked_itself<'r, R: SeatRow + 'r>(rows: impl IntoIterator<Item = &'r R>, k: &R::Key) -> bool {
    rows.into_iter().any(|q| {
        q.seat_kind() == SeatKind::Unseat
            && q.scope().is_some_and(|s| s.as_ref() == "registered")
            && q.obj() == Some(Obj::Key(k.clone()))
            && q.to().contains(k)
            && q.signer() == k
    })
}

/// Rule 4 for an eviction concurrent with row `at`: an eviction of `k` from self roster `g` (an unseat of its own
/// scope `s` over `g`) that concluded, neither in the row's past nor having the row in its own, counts at its own
/// head and is out of force from that head on: the key is out for a row that has every head the eviction names in
/// its past.
fn evicted_from<R: SeatRow>(c: &Concluded<'_, R>, at: usize, g: &ObjOf<R>, s: &str, k: &R::Key) -> bool {
    c.cs().iter().copied().any(|e| {
        let er = c.g.row(e);
        er.seat_kind() == SeatKind::Unseat
            && er.obj().as_ref() == Some(g)
            && er.scope().is_some_and(|x| x.as_ref() == s)
            && er.to().contains(k)
            && c.g.concurrent(e, at)
            && !er.head().is_empty()
            && er.head().iter().all(|h| c.g.idx(h).is_some_and(|h| h == at || c.g.in_past(h, at)))
    })
}

/// `g` is the founding record of a self roster: its founding scope read through [`SeatLaw::kinds`] as
/// [`CommunityKind::SelfRoster`].
fn self_founding<R: SeatRow>(law: &SeatLaw, g: &R) -> bool {
    let get = |i: &R::Id| if i == g.id() { Some(g) } else { None };
    g.seat_kind() == SeatKind::Offer
        && founding(g)
        && kind_of(law, &get, &Obj::Row(g.id().clone())) == Some(CommunityKind::SelfRoster)
}

/// The self rosters each key is live in over `rows` (a row's concluded past): for every key a live seat of a self
/// roster's own scope holds there (an object of kind [`CommunityKind::SelfRoster`] through [`SeatLaw::kinds`],
/// admitted by its count and not evicted), the founding rows of the rosters `keep` keeps; and the keys holding an
/// AI agent's seat there. A key that revoked itself among `rows` is in none.
#[allow(clippy::type_complexity)]
fn rosters_by_key<'r, R: SeatRow + 'r, S: CutSpec<R>>(
    rows: &[&'r R],
    law: &SeatLaw,
    spec: &S,
    keep: &dyn Fn(&ObjOf<R>, &str, &R::Key) -> bool,
) -> (BTreeMap<R::Key, Vec<&'r R>>, BTreeSet<R::Key>) {
    let by: BTreeMap<&R::Id, &R> = rows.iter().map(|q| (q.id(), *q)).collect();
    let get = |i: &R::Id| by.get(i).copied();
    let sc = concluded_over(rows.iter().copied());
    let seats = Seats::build(&sc, law, spec, None, None, None);
    let agents: BTreeSet<R::Key> =
        seats.recs().iter().filter(|x| x.scope.as_ref() == AGENT).map(|x| x.k.clone()).collect();
    let mut out: BTreeMap<R::Key, Vec<&'r R>> = BTreeMap::new();
    // one self roster per identity (G1), judged in the row's own past `rows` (r99 D1): of an identity's foundings
    // there, the one TAKEN UP (named, or counted over, by another row of `rows`) is its roster; a rival nothing takes
    // up is no part of it (a stolen genesis key's bare founding silences no one); where several are taken up, or none
    // of several, the reader waits and never picks, and none is
    let mut founded: BTreeMap<&R::Key, Vec<&R>> = BTreeMap::new();
    for g in rows.iter().copied().filter(|g| self_founding(law, *g)) {
        founded.entry(g.signer()).or_default().push(g);
    }
    // TAKEN UP means COUNTED (r99 D8 to D10): a counted row over the founding (an addition, an eviction, or a landed
    // self-roster window) signed by a LIVE voice of the identity, a key no counted or landed eviction from any of the
    // identity's rosters has ended (an evicted genesis key is no voice anywhere); a key's own consent to its seat is
    // no voice. A founding only named, or counted over only by such keys, takes up nothing
    let by_id: BTreeMap<&R::Id, &R> = rows.iter().map(|q| (q.id(), *q)).collect();
    let in_rosters = |q: &R, ids: &BTreeSet<&R::Id>| matches!(q.obj(), Some(Obj::Row(o)) if ids.contains(&o));
    let evicted = |gs: &[&R]| -> BTreeSet<R::Key> {
        let ids: BTreeSet<&R::Id> = gs.iter().map(|g| g.id()).collect();
        let mut out: BTreeSet<R::Key> = BTreeSet::new();
        for q in rows.iter().copied() {
            if q.seat_kind() == SeatKind::Unseat && in_rosters(q, &ids) {
                out.extend(q.to().iter().cloned());
            }
            if let Some((op, says)) = q.landing() {
                if let Some(o) = by_id.get(op).filter(|_| says.as_ref() == "landed") {
                    if let Some(t) = o.evicts().filter(|_| in_rosters(o, &ids)) {
                        out.insert(t.clone());
                    }
                }
            }
        }
        out
    };
    let taken = |g: &R, gone: &BTreeSet<R::Key>| {
        let at = Some(Obj::Row(g.id().clone()));
        rows.iter().copied().filter(|q| q.id() != g.id()).any(|q| {
            let voices: Vec<&R::Key> = if matches!(q.seat_kind(), SeatKind::Offer | SeatKind::Unseat)
                && q.conf() == Some(Conf::Group)
                && q.obj() == at
            {
                core::iter::once(q.signer()).chain(q.cosigners().iter()).filter(|k| !q.to().contains(k)).collect()
            } else if let Some((op, says)) = q.landing() {
                match by_id.get(op) {
                    Some(o)
                        if says.as_ref() == "landed"
                            && (o.evicts().is_some() || o.adds().is_some())
                            && o.obj() == at =>
                    {
                        core::iter::once(o.signer()).chain(o.cosigners().iter()).collect()
                    }
                    _ => Vec::new(),
                }
            } else {
                Vec::new()
            };
            voices.iter().any(|k| !gone.contains(*k))
        })
    };
    // a founding that seats only its genesis key adds no device: untaken, it is no rival (K7)
    let bare = |g: &R| g.to().iter().all(|k| k == g.signer()) || g.cosigners().iter().all(|k| k == g.signer());
    let mut rosters: BTreeSet<&R::Id> = BTreeSet::new();
    for gs in founded.values() {
        if gs.len() == 1 {
            rosters.insert(gs[0].id());
            continue;
        }
        let gone = evicted(gs);
        let t: Vec<&R> = gs.iter().copied().filter(|g| taken(g, &gone) || !bare(g)).collect();
        match t.as_slice() {
            [g] => {
                rosters.insert(g.id());
            }
            [] => rosters.extend(gs.iter().map(|g| g.id())),
            _ => {}
        }
    }
    for g in rows.iter().copied() {
        if g.seat_kind() != SeatKind::Offer || !founding(g) {
            continue;
        }
        if self_founding(law, g) && !rosters.contains(g.id()) {
            continue;
        }
        let o = Obj::Row(g.id().clone());
        if kind_of(law, &get, &o) != Some(CommunityKind::SelfRoster) {
            continue;
        }
        let Some(s) = g.scope() else { continue };
        for k in seats.holders(s.as_ref(), &o, None) {
            if keep(&o, s.as_ref(), &k) && !revoked_itself(rows.iter().copied(), &k) {
                let v = out.entry(k).or_default();
                if !v.iter().any(|x| x.id() == g.id()) {
                    v.push(g);
                }
            }
        }
    }
    (out, agents)
}

/// The person key `k` is at row `at` of `c`, as a function of rows (ruled on CIRISConstitution#224), with no
/// instant: the self roster (an object of kind [`CommunityKind::SelfRoster`]: a person's own key roster, CC
/// 3.3.6.4, or a voice's room keys in a private room, CC 3.1.3.2) where, in the row's own past, `k` is the genesis
/// key (it signed the founding record) or was seated by a counted addition that landed (`self_roster_add`), no
/// eviction of it has landed (`self_roster_evict`), and an eviction concurrent with the row follows rule 4 (it
/// counts at its own head and is out of force from that head on); and the key's own revocation is not in the row's
/// past ([`key_record_ended`]). The answer is the person's identity key, `Obj::Key` of the genesis key that signed
/// the founding record (the self roster's object is the identity key, never one roster row or one key record), so
/// two rosters founded by one genesis key are one person. `None` where `at` did not conclude, where no self roster
/// has `k` live there, or where rosters of several identity keys do (two persons is none, as two owners are). The kind is read through [`SeatLaw::kinds`]: a law
/// with no kinds names no person. A count is then over persons ([`persons_of`]).
pub fn person_at<R: SeatRow, S: CutSpec<R>>(
    c: &Concluded<'_, R>,
    at: usize,
    law: &SeatLaw,
    spec: &S,
    k: &R::Key,
) -> Option<ObjOf<R>> {
    if !c.concluded(at) {
        return None;
    }
    let rows: Vec<&R> = c.cs().iter().copied().filter(|&q| c.g.in_past(q, at)).map(|q| c.g.row(q)).collect();
    let keep = |g: &ObjOf<R>, s: &str, key: &R::Key| key != k || !evicted_from(c, at, g, s, k);
    let hit = rosters_by_key(&rows, law, spec, &keep).0.remove(k).unwrap_or_default();
    // the person is its IDENTITY key, the genesis key that signed its rosters' founding records (the self roster's
    // object is the identity key, never one roster row or one key record): two rosters of one genesis key are one
    let names: BTreeSet<&R::Key> = hit.iter().map(|g| g.signer()).collect();
    if names.len() == 1 {
        names.into_iter().next().map(|g| Obj::Key(g.clone()))
    } else {
        None
    }
}

/// A person's live keys over the concluded set `c`, with no instant: the inverse of [`persons_of`]. The keys of the
/// self rosters founded by the person's genesis key `person` (live seats of each in its own scope, as
/// [`person_at`] reads them) that count as that person ([`Persons`]: a key of two persons, an agent's key, a key
/// that revoked itself are none of its keys), and the genesis key itself while it counts as itself. A person whose
/// genesis key revoked itself has no live key. With `audience::audiences` and [`nodes_of`] it gives the keys a row
/// reaches: the node set = audiences ∘ person_keys ∘ nodes_of (ADOPTING.md). The reference is `seat.person_keys`.
pub fn person_keys<R: SeatRow, S: CutSpec<R>>(
    c: &Concluded<'_, R>,
    law: &SeatLaw,
    spec: &S,
    person: &R::Key,
) -> BTreeSet<R::Key> {
    let rows: Vec<&R> = c.cs().iter().map(|&q| c.g.row(q)).collect();
    let pp = Persons::over(&rows, law, spec, None);
    let mut cand: BTreeSet<R::Key> =
        pp.rosters.iter().filter(|(_, gs)| gs.iter().any(|g| g.signer() == person)).map(|(k, _)| k.clone()).collect();
    cand.insert(person.clone());
    cand.into_iter().filter(|k| pp.voice(k).as_ref() == Some(person)).collect()
}

/// The node keys `owner` owns over the concluded set `c`, with no instant: the inverse of a node's owner-binding.
/// The inverse of the one owner reading, [`Seats::owner`]: every key object whose owner is `owner` (a key holds the
/// owner seat only by its own signature or acceptance; the binding's withdrawal or the owner seat's unseat ends it;
/// two live owners is none; a re-binding ends the binding before it), where neither the node key nor the owner
/// revoked itself.
/// Which keys are nodes is the key records' (the caller's: `identity_type` `node`). The reference is
/// `seat.nodes_of`.
pub fn nodes_of<R: SeatRow, S: CutSpec<R>>(
    c: &Concluded<'_, R>,
    law: &SeatLaw,
    spec: &S,
    owner: &R::Key,
) -> BTreeSet<R::Key> {
    let rows: Vec<&R> = c.cs().iter().map(|&q| c.g.row(q)).collect();
    if revoked_itself(rows.iter().copied(), owner) {
        return BTreeSet::new();
    }
    let seats = Seats::new(c, law, spec, None);
    let objs: BTreeSet<R::Key> = rows
        .iter()
        .filter(|q| q.seat_kind() == SeatKind::Offer && q.scope().is_some_and(|s| s.as_ref() == "owner"))
        .filter_map(|q| match q.obj() {
            Some(Obj::Key(k)) => Some(k),
            _ => None,
        })
        .collect();
    // the inverse of the one owner reading ([`Seats::owner`]: two live owners is none, a re-binding ends the
    // binding before it)
    objs.into_iter()
        .filter(|n| seats.owner(n).as_ref() == Some(owner) && !revoked_itself(rows.iter().copied(), n))
        .collect()
}

/// The persons a count reads over `rows` (a counted row's concluded past), ruled on CIRISConstitution#224: one voice
/// and one member per person, however many of its keys sign or are seated. A person is named by its self roster's
/// genesis key, the founding record's signer ("a voice is named by the identity reference of its first room key",
/// CC 3.1.3.2). Built once per count, and only where `rows` hold a self roster or a key's own revocation; otherwise
/// every key is its own person. A count over a self roster (or a key object) reads keys ([`Persons::keys`]).
pub struct Persons<'r, R: SeatRow> {
    rosters: BTreeMap<R::Key, Vec<&'r R>>,
    revoked: BTreeSet<R::Key>,
    agents: BTreeSet<R::Key>,
    // the genesis keys: the signers of the self rosters' founding records
    founders: BTreeSet<R::Key>,
    keys: bool,
}

impl<'r, R: SeatRow + 'r> Persons<'r, R> {
    /// The persons over `rows` for a count over `obj` (`None`: no object read).
    pub fn over<S: CutSpec<R>>(rows: &[&'r R], law: &SeatLaw, spec: &S, obj: Option<&ObjOf<R>>) -> Self {
        let by: BTreeMap<&R::Id, &R> = rows.iter().map(|q| (q.id(), *q)).collect();
        let get = |i: &R::Id| by.get(i).copied();
        let keys = obj.is_some_and(|o| match o {
            Obj::Key(_) => true,
            Obj::Row(_) => kind_of(law, &get, o) == Some(CommunityKind::SelfRoster),
        });
        let none = Persons {
            rosters: BTreeMap::new(),
            revoked: BTreeSet::new(),
            agents: BTreeSet::new(),
            founders: BTreeSet::new(),
            keys,
        };
        let any_self = rows.iter().any(|g| {
            g.seat_kind() == SeatKind::Offer
                && founding(g)
                && kind_of(law, &get, &Obj::Row(g.id().clone())) == Some(CommunityKind::SelfRoster)
        });
        let revoked: BTreeSet<R::Key> = rows
            .iter()
            .filter(|q| {
                q.seat_kind() == SeatKind::Unseat
                    && q.scope().is_some_and(|s| s.as_ref() == "registered")
                    && q.to().contains(q.signer())
                    && q.obj() == Some(Obj::Key(q.signer().clone()))
            })
            .map(|q| q.signer().clone())
            .collect();
        if keys || (!any_self && revoked.is_empty()) {
            return Persons { revoked, ..none };
        }
        let (rosters, agents) = rosters_by_key(rows, law, spec, &|_, _, _| true);
        let founders: BTreeSet<R::Key> = rows
            .iter()
            .filter(|g| {
                g.seat_kind() == SeatKind::Offer
                    && founding(g)
                    && kind_of(law, &get, &Obj::Row(g.id().clone())) == Some(CommunityKind::SelfRoster)
            })
            .map(|g| g.signer().clone())
            .collect();
        Persons { rosters, revoked, agents, founders, keys }
    }

    /// Whether this count reads keys, not persons (a self roster's own count).
    pub fn keys(&self) -> bool {
        self.keys
    }

    /// The voice key `k` counts as, or `None` (no voice): a key of exactly one self roster counts as its person
    /// (the genesis key), a key of none as itself; none for a key of two persons (two genesis keys), a key that
    /// revoked itself, and a key whose person's genesis key revoked itself (its devices then speak for no one). An
    /// agent's key is itself, never its owner (CC 4.5.13).
    pub fn voice(&self, k: &R::Key) -> Option<R::Key> {
        if self.keys {
            return Some(k.clone());
        }
        if self.revoked.contains(k) {
            return None;
        }
        // an agent's key is out before the map: never its owner's voice, whatever roster lists it; it stays its own
        // key, which no count's base holds (CC 4.5.13: "an agent has no vote")
        if self.agents.contains(k) {
            return Some(k.clone());
        }
        let names = self.named(k);
        match names.as_slice() {
            // a genesis key its own roster evicted is no voice of its person (G33: an eviction ends a key AS THE
            // PERSON'S); its own rows read as a bare key's, and the identity the room seats is no voice of it
            [] if self.founders.contains(k) => None,
            [] => Some(k.clone()),
            [g] if !self.revoked.contains(g) => Some(g.clone()),
            _ => None,
        }
    }

    /// The persons key `k` is a live key of: the genesis keys of its self rosters, one each. A person is NAMED by its
    /// genesis key, so two rosters founded by the same key are one person.
    fn named(&self, k: &R::Key) -> Vec<R::Key> {
        let names: BTreeSet<R::Key> =
            self.rosters.get(k).map(|v| v.iter().map(|g| g.signer().clone()).collect()).unwrap_or_default();
        names.into_iter().collect()
    }

    /// The member key `k` counts as in a base: a key of exactly one self roster is its person, any other key
    /// itself (a revoked key, a key of two rosters, are still members; they are no voice).
    pub fn member(&self, k: &R::Key) -> R::Key {
        if self.keys || self.revoked.contains(k) {
            return k.clone();
        }
        match self.named(k).as_slice() {
            [g] => g.clone(),
            _ => k.clone(),
        }
    }

    /// The persons a base counts as, one member each.
    pub fn base(&self, keys: &BTreeSet<R::Key>) -> BTreeSet<R::Key> {
        keys.iter().map(|k| self.member(k)).collect()
    }

    /// The one reading of a count by person (ruled on CIRISConstitution#224): `(the base, the voices)`, the base
    /// counted by member ([`Persons::base`]), the voices mapped to persons and held to the voting base (`voters`,
    /// else the base), and the named keys `apart` (a lift's author, a receipt's remover, a recall's holder) set
    /// apart BY PERSON from both, so their own devices are them. Every count reads it: the seat rule's count and
    /// lift, the fold and its lift, the count's receipt.
    pub fn count(
        &self,
        base: &BTreeSet<R::Key>,
        voices: &BTreeSet<R::Key>,
        voters: Option<&BTreeSet<R::Key>>,
        apart: &[R::Key],
    ) -> (BTreeSet<R::Key>, BTreeSet<R::Key>) {
        let mut b = self.base(base);
        let mut v = self.voices(voices, voters.unwrap_or(base));
        for k in apart {
            let mut ks = vec![k.clone()];
            if !self.keys {
                ks.push(self.member(k));
                ks.extend(self.voice(k));
            }
            for x in &ks {
                b.remove(x);
                v.remove(x);
            }
        }
        (b, v)
    }

    /// The persons of `base` the keys `voices` speak for, one voice each.
    pub fn voices(&self, voices: &BTreeSet<R::Key>, base: &BTreeSet<R::Key>) -> BTreeSet<R::Key> {
        let b = self.base(base);
        voices.iter().filter_map(|v| self.voice(v)).filter(|p| b.contains(p)).collect()
    }
}

/// A count over persons ([`Persons`]): the persons of `base` that the keys `voices` speak for, one voice each,
/// read over `rows` for a count over `obj`.
pub fn persons_of<'r, R: SeatRow + 'r, S: CutSpec<R>>(
    rows: &[&'r R],
    law: &SeatLaw,
    spec: &S,
    voices: &BTreeSet<R::Key>,
    base: &BTreeSet<R::Key>,
) -> BTreeSet<R::Key> {
    Persons::over(rows, law, spec, None).voices(voices, base)
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
    let void = cache.map(|c| c.current_void()).unwrap_or_default();
    let heads = counted_heads(law, heads, &|h| g.idx(h).map(|i| g.row(i)), &|a, b| match (g.idx(a), g.idx(b)) {
        (Some(a), Some(b)) => g.in_past(a, b),
        _ => false,
    });
    // the void changes are no heads (the ruling of 2026-11-27)
    let mut hs: Vec<usize> = Vec::new();
    for h in heads.iter().filter(|h| !void.contains(*h)) {
        let Some(hi) = g.idx(h).filter(|hi| anc.binary_search(hi).is_ok()) else { return BTreeSet::new() };
        hs.push(hi);
    }
    if hs.is_empty() {
        return BTreeSet::new();
    }
    let rows: Vec<&R> = anc.iter().map(|&q| g.row(q)).collect();
    let by: BTreeMap<&R::Id, &R> = rows.iter().map(|q| (q.id(), *q)).collect();
    let in_past = |a: &R::Id, b: &R::Id| match (g.idx(a), g.idx(b)) {
        (Some(a), Some(b)) => g.in_past(a, b),
        _ => false,
    };
    // the union of the heads' pasts, the void changes apart: several heads are folded by the seats over it
    // (Seats::tips_fold, the guarded fold of CC 2.7.8), not intersected
    let at = |q: usize| !void.contains(g.row(q).id()) && hs.iter().any(|&hi| q == hi || g.ancestors(hi).has(q));
    // read with the heads' rows: the acceptances in the row's own past that complete a seat placed there (a seat is
    // two consents: the ruling of 2026-11-26 on acceptances, (a)), and the withdrawals in that past (a leaving, a
    // laying down: a withdrawal is no counted change, so no head is read through)
    let at_row = |q: &R| g.idx(q.id()).is_some_and(at);
    let acc: BTreeSet<&R::Id> = completing(&rows, law, &by, obj, &at_row, &in_past).iter().map(|q| q.id()).collect();
    let read = |q: usize| at(q) || g.row(q).seat_kind() == SeatKind::Withdraw || acc.contains(g.row(q).id());
    let sc = concluded_over(anc.iter().filter(|&&q| read(q)).map(|&q| g.row(q)));
    Seats::build(&sc, law, spec, None, None, cache).holders(scope, obj, None)
}

/// The acceptances among `rows` (a counted row's own past, by index) that complete a seat placed at a head
/// (`at`: in that head's past), read with the head's rows (a seat is two consents: the ruling of 2026-11-26 on
/// acceptances, (a)). Each is signed by the key its offer seats (never a cosignature, never another key's row),
/// of an offer at the head (no seat is created from outside the heads), the offer not ended among `rows`: a
/// withdrawal of it or of the acceptance, a counted removal of the key with the offer in its past, or the key's
/// own end of its stay with the offer in its past. In a private room a key whose stay ended completes nothing.
fn completing<'a, R: SeatRow>(
    rows: &[&'a R],
    law: &SeatLaw,
    by: &BTreeMap<&R::Id, &R>,
    obj: &ObjOf<R>,
    at: &dyn Fn(&R) -> bool,
    past: &dyn Fn(&R::Id, &R::Id) -> bool,
) -> Vec<&'a R> {
    let private = row_of(by, obj).is_some_and(|f| community(by, obj) && f.private_room());
    let mut out = Vec::new();
    for &a in rows {
        if at(a) || a.seat_kind() != SeatKind::Accept {
            continue;
        }
        let Some(&o) = a.of().and_then(|o| by.get(o)) else { continue };
        let k = a.signer();
        if !at(o) || o.seat_kind() != SeatKind::Offer || !o.to().contains(k) {
            continue;
        }
        let ended = rows.iter().any(|q| match q.seat_kind() {
            SeatKind::Withdraw => {
                q.target().is_some_and(|t| t == o.id() || t == a.id())
                    || (q.signer() == k
                        && stay_end(law, by, q, &|x: &R| by.contains_key(x.id()) && past(x.id(), q.id())).as_ref()
                            == Some(obj)
                        && (private || past(o.id(), q.id())))
            }
            SeatKind::Unseat => q.to().contains(k) && q.obj() == o.obj() && past(o.id(), q.id()),
            _ => false,
        });
        if !ended {
            out.push(a);
        }
    }
    out
}

/// `void`, and every counted change of `acts` built on one in it (a head it names in it), but those `stop` keeps.
fn built_closure<R: SeatRow>(
    g: &Graph<'_, R>,
    acts: &[usize],
    void: &BTreeSet<usize>,
    stop: &dyn Fn(usize) -> bool,
) -> BTreeSet<usize> {
    let mut out = void.clone();
    loop {
        let more: Vec<usize> = acts
            .iter()
            .copied()
            .filter(|&q| {
                !out.contains(&q)
                    && g.row(q).head().iter().any(|h| g.idx(h).is_some_and(|hi| out.contains(&hi)))
                    && !stop(q)
            })
            .collect();
        if more.is_empty() {
            return out;
        }
        out.extend(more);
    }
}

/// S'' (the ruling of 2026-11-27): the counted changes over the row's object in its past `p` void for it. The only
/// automatic effect of a key signing two things outside an election; it voids a change, never a key.
/// - self-forked: every counted voice of `q` (its signers who are members at its heads) has, in `p`, acknowledged a
///   counted change `q` is behind (every head `q` names strictly in the past of that change's own heads, `q` not in
///   its past);
/// - T at the fork point: a self-forked `q` is void only where, of the members seated at its heads, those who
///   signed only the other side (the rows without `q` in their past on a line through a change `q` is behind)
///   outnumber those who signed only `q`'s side (`q` and the rows built on it); equal, none on either side included,
///   neither is void, so depth decides nothing; only counted changes count, through their counted voices; only
///   changes on a side (the competing line by heads back to the fork point, and what is built on it; never a row a
///   side merely cites); only a voice resting on a seat held at the fork point, or granted by an offer not on `q`'s
///   side and not self-forked; a key's yes on an offer seating it counts for neither side; a merge of both lines is
///   on neither;
/// - built on: a counted change naming a void head is void, but a merge of both lines.
fn void_changes<R: SeatRow, S: CutSpec<R>>(
    p: &Past<'_, '_, R>,
    law: &SeatLaw,
    spec: &S,
    cache: Option<&MembersAt<R>>,
) -> BTreeSet<R::Id> {
    let Some(obj) = p.row().obj() else { return BTreeSet::new() };
    void_changes_in(p.graph(), p.ancestors(), &obj, law, spec, cache)
}

/// [`void_changes`] over the rows `anc` (by index, concluded, closed under their pasts) for object `obj`: the past
/// of a counting row, or the rows a reader's roster holds ([`roster_void`]).
fn void_changes_in<R: SeatRow, S: CutSpec<R>>(
    g: &Graph<'_, R>,
    anc: &[usize],
    obj: &ObjOf<R>,
    law: &SeatLaw,
    spec: &S,
    cache: Option<&MembersAt<R>>,
) -> BTreeSet<R::Id> {
    let counted = |q: usize| LineSpec::<R>::counted_act(&SeatLine, g.row(q)).is_some_and(|(o, _)| o == *obj);
    let acts: Vec<usize> = anc.iter().copied().filter(|&q| counted(q)).collect();
    if acts.is_empty() {
        return BTreeSet::new();
    }
    let held: BTreeSet<usize> = anc.iter().copied().collect();
    let by: BTreeMap<&R::Id, &R> = anc.iter().map(|&q| (g.row(q).id(), g.row(q))).collect();
    // per change: its counted voices, and the members at its heads
    let mut info: BTreeMap<usize, (BTreeSet<R::Key>, BTreeSet<R::Key>)> = BTreeMap::new();
    for &q in &acts {
        let qa: Vec<usize> = anc.iter().copied().filter(|&x| g.in_past(x, q)).collect();
        let pq = Past::new(g, q, &qa);
        let qr = g.row(q);
        let mem = members_at_with(&pq, law, spec, obj, qr.head(), "member", cache);
        let v: BTreeSet<R::Key> = voices(qr, &pq).into_iter().filter(|k| mem.contains(k)).collect();
        info.insert(q, (v, mem));
    }
    // heads strictly in the past of a held row's (a head not held is in no row's past here)
    let older = |hs: &[R::Id], than: &[R::Id]| {
        !hs.is_empty()
            && hs
                .iter()
                .all(|h| than.iter().any(|t| g.idx(t).is_some_and(|ti| held.contains(&ti) && g.id_in_past(h, ti))))
    };
    let behind = |q: usize, c: usize| c != q && !g.in_past(q, c) && older(g.row(q).head(), g.row(c).head());
    // each voice's rows over the object
    let keys: BTreeSet<&R::Key> = info.values().flat_map(|(v, _)| v.iter()).collect();
    let mut signed: BTreeMap<&R::Key, Vec<usize>> = BTreeMap::new();
    for k in keys {
        let rows: Vec<usize> = anc
            .iter()
            .copied()
            .filter(|&a| signed_by(g.row(a), k) && object_of(g.row(a), &|i| by.get(i).copied()).as_ref() == Some(obj))
            .collect();
        signed.insert(k, rows);
    }
    let none = Vec::new();
    // the changes q is behind that k acknowledged by a row without q in its past (a merge of both lines is no fork)
    let forked_by = |q: usize, k: &R::Key| -> Vec<usize> {
        signed
            .get(k)
            .unwrap_or(&none)
            .iter()
            .copied()
            .filter(|&a| a != q && !g.in_past(q, a))
            .flat_map(|a| acts.iter().copied().filter(move |&c| (c == a || g.in_past(c, a)) && behind(q, c)))
            .collect()
    };
    let forked = |q: usize| {
        let v = &info[&q].0;
        !v.is_empty() && v.iter().all(|k| !forked_by(q, k).is_empty())
    };
    let out: BTreeSet<usize> = acts.iter().copied().filter(|&q| forked(q)).collect();
    if out.is_empty() {
        return BTreeSet::new();
    }
    // the changes q is behind (the other side's line)
    let line = |q: usize| -> Vec<usize> { acts.iter().copied().filter(|&c| behind(q, c)).collect() };
    // T at q's fork point: of the members seated at q's heads, those who voiced only the other side against those who
    // voiced only q's side (the fourth attack's tightening, the Constitution's reading of T):
    // - only counted changes count, through their counted voices (a post, an acknowledgement or an acceptance is no
    //   voice);
    // - only changes on a side: q's side is q and the changes built on it; the other side is the competing line (the
    //   changes q is behind and those they name as heads, back to the fork point) and the changes built on it; a row a
    //   side merely cites is not on it; a merge of both lines is on neither;
    // - only standing: a voice counts where the key held the seat it rests on (a member's seat; a duty for a
    //   duty-counted change) at the fork point, or holds it by an offer that is not on q's side and not self-forked;
    // - the beneficiary of an offer (its yes on the offer seating it) counts for neither side.
    let declared_here = declared(&by, obj);
    let t_void = |q: usize| {
        let mem = &info[&q].1;
        let qr = g.row(q);
        let hs: Vec<usize> = qr.head().iter().filter_map(|h| g.idx(h)).collect();
        let at_fp = |a: usize| hs.iter().any(|&h| a == h || g.in_past(a, h));
        let lq = line(q);
        let qa: Vec<usize> = anc.iter().copied().filter(|&x| g.in_past(x, q)).collect();
        let pq = Past::new(g, q, &qa);
        let duty_fp = members_at_with(&pq, law, spec, obj, qr.head(), "duty", cache);
        // the competing line, by heads, back to the fork point
        let mut chain: BTreeSet<usize> = BTreeSet::new();
        let mut todo: Vec<usize> = lq.clone();
        while let Some(x) = todo.pop() {
            if at_fp(x) || !held.contains(&x) || !chain.insert(x) {
                continue;
            }
            todo.extend(g.row(x).head().iter().filter_map(|h| g.idx(h)));
        }
        let pool: &[usize] = &acts;
        let rows: Vec<usize> = pool
            .iter()
            .copied()
            .filter(|&a| !at_fp(a) && object_of(g.row(a), &|i| by.get(i).copied()).as_ref() == Some(obj))
            .collect();
        let standing = |k: &R::Key, a: usize| -> bool {
            let duty = g.row(a).counted().is_some_and(|c| c.as_ref() == "duty");
            if (duty && duty_fp.contains(k)) || (!duty && mem.contains(k)) {
                return true;
            }
            anc.iter().copied().any(|o| {
                let or = g.row(o);
                let fits = or.scope().is_some_and(|s| {
                    if duty {
                        law.is_duty(s.as_ref(), &declared_here)
                    } else {
                        s.as_ref() == "member"
                    }
                });
                or.seat_kind() == SeatKind::Offer
                    && fits
                    && or.to().contains(k)
                    && (o != q && !g.in_past(q, o) && !out.contains(&o) && g.in_past(o, a))
            })
        };
        let keys = |a: usize| -> BTreeSet<R::Key> {
            let r = g.row(a);
            if r.seat_kind() == SeatKind::Accept {
                return BTreeSet::new();
            }
            let mut ks = match info.get(&a) {
                Some((v, _)) => v.clone(),
                None => signers(r),
            };
            if r.seat_kind() == SeatKind::Offer {
                ks.retain(|k| !r.to().contains(k)); // the beneficiary is no evidence for its side
            }
            ks.into_iter().filter(|k| mem.contains(k) && standing(k, a)).collect()
        };
        let mut km: BTreeSet<R::Key> = BTreeSet::new();
        let mut ko: BTreeSet<R::Key> = BTreeSet::new();
        for &a in &rows {
            let mine = (a == q || g.in_past(q, a)) && !lq.iter().any(|&c| g.in_past(c, a));
            let other = a != q
                && !g.in_past(q, a)
                && !g.in_past(a, q)
                && (chain.contains(&a) || lq.iter().any(|&c| g.in_past(c, a)));
            if mine {
                km.extend(keys(a));
            } else if other {
                ko.extend(keys(a));
            }
        }
        ko.difference(&km).count() > km.difference(&ko).count()
    };
    let tv: BTreeSet<usize> = out.iter().copied().filter(|&q| t_void(q)).collect();
    // a change built on a void one is void, but a merge of both lines (a change the void one is behind in its past
    // too), which reads its count without the void change, as any counting row does
    let lines: BTreeMap<usize, Vec<usize>> = tv.iter().map(|&f| (f, line(f))).collect();
    let merge = |b: usize| lines.iter().any(|(&f, l)| g.in_past(f, b) && l.iter().any(|&c| g.in_past(c, b)));
    built_closure(g, &acts, &tv, &merge).into_iter().map(|i| g.row(i).id().clone()).collect()
}

/// S'' over the rows a reader's roster holds (`c`'s concluded rows), for each object a counted act is over, as if
/// one row had them all in its past: the changes the roster leaves out (they neither add nor remove members).
fn roster_void<R: SeatRow, S: CutSpec<R>>(
    c: &Concluded<'_, R>,
    law: &SeatLaw,
    spec: &S,
    reader: Option<&BTreeSet<R::Id>>,
) -> BTreeSet<usize> {
    let objs: BTreeSet<ObjOf<R>> =
        c.cs().iter().filter_map(|&i| LineSpec::<R>::counted_act(&SeatLine, c.g.row(i)).map(|(o, _)| o)).collect();
    let cache = MembersAt::<R>::default();
    if let Some(rv) = reader {
        *cache.rvoid.borrow_mut() = rv.clone();
    }
    let mut out = BTreeSet::new();
    for obj in &objs {
        for id in void_changes_in(&c.g, c.cs(), obj, law, spec, Some(&cache)) {
            if let Some(i) = c.g.idx(&id) {
                out.insert(i);
            }
        }
    }
    out
}

/// The counted changes void for a reader's own counted row `a` (index in `c`): the line does not take them as
/// acknowledged by it (a fork head it had to name).
fn ack_void<R: SeatRow, S: CutSpec<R>>(
    c: &Concluded<'_, R>,
    law: &SeatLaw,
    spec: &S,
    a: usize,
    reader: Option<&BTreeSet<R::Id>>,
) -> BTreeSet<usize> {
    // in the rows concluded for a reader, the changes its line voided are left out of its own counted rows too, and
    // the row's own void is read with them (the reference's _ack_void reads the same)
    let mut out: BTreeSet<usize> = reader.map(|rv| rv.iter().filter_map(|i| c.g.idx(i)).collect()).unwrap_or_default();
    let ar = c.g.row(a);
    if LineSpec::<R>::counted_act(&SeatLine, ar).is_none() {
        return out;
    }
    let anc: Vec<usize> = c.cs().iter().copied().filter(|&q| c.g.in_past(q, a)).collect();
    let pa = Past::new(&c.g, a, &anc);
    let cache = MembersAt::<R>::default();
    if let Some(rv) = reader {
        *cache.rvoid.borrow_mut() = rv.clone();
    }
    out.extend(void_changes(&pa, law, spec, Some(&cache)).iter().filter_map(|i| c.g.idx(i)));
    out
}

/// The rows as they conclude for reader `own` (the ruling of 2026-11-27, the reader-line exclusion): the changes
/// void for it by its line are left out of every counting row's fold and heads, so a count that stands for this
/// reader and not for a reader with no row concludes, and one refused for it does not (CC 2.7.9: "A reader's own
/// acknowledged head closes older heads for that reader only"). Returns the rows so concluded and the changes void
/// for the reader; build its roster with [`Seats::for_reader`].
///
/// With `own` `None`, the rows as they conclude for a reader with no row of its own: only the concurrent founders'
/// amendments it holds are read in ([`held_pairs`], C2). Every reader holds the rows it is given, so a roster is
/// built over what this returns (with [`Seats::new`] where `own` is `None`).
pub fn for_reader<'a, R: SeatRow, S: CutSpec<R>>(
    c: &Concluded<'a, R>,
    law: &SeatLaw,
    spec: &S,
    own: Option<&R::Key>,
) -> (Concluded<'a, R>, BTreeSet<R::Id>) {
    let rv: BTreeSet<R::Id> = match own {
        Some(own) => {
            line::void_except(c, &SeatLine, Some(own), |_| true, |_| false, &|a: usize| ack_void(c, law, spec, a, None))
                .into_iter()
                .map(|i| c.g.row(i).id().clone())
                .collect()
        }
        None => BTreeSet::new(),
    };
    let pairs = held_pairs(c);
    let ends = own.map(|k| reader_ends(c, law, spec, k, None)).unwrap_or_default();
    if rv.is_empty() && pairs.is_empty() && ends.is_empty() {
        return (c.clone(), rv);
    }
    let cache = MembersAt::<R>::default();
    *cache.rvoid.borrow_mut() = rv.clone();
    *cache.rpairs.borrow_mut() = pairs;
    *cache.rends.borrow_mut() = ends;
    let rows: Vec<&'a R> = c.g.rows().to_vec();
    let rc = crate::layers::conclude(rows, |p| seat_rule_with(p, law, spec, &|_| true, Some(&cache)), None);
    (rc, rv)
}

/// The concurrent founders' amendments the rows `c` hold (CC 2.7.8's wait, read for the reader holding them): pairs
/// of concluded record versions seating founders over one room ([`SeatRow::role`] `founder`, a `to`), neither in
/// the other's past, with no record version of that room naming both.
fn held_pairs<R: SeatRow>(c: &Concluded<'_, R>) -> Vec<HeldPair<R>> {
    let g = &c.g;
    let vs: Vec<usize> = c
        .cs()
        .iter()
        .copied()
        .filter(|&i| {
            let q = g.row(i);
            q.seat_kind() == SeatKind::Offer
                && q.conf() == Some(Conf::Group)
                && q.scope().is_some_and(|s| s.as_ref() == "record")
                && q.obj().is_some()
        })
        .collect();
    let seating: Vec<usize> = vs
        .iter()
        .copied()
        .filter(|&i| g.row(i).role().is_some_and(|x| x.as_ref() == "founder") && !g.row(i).to().is_empty())
        .collect();
    let mut out = Vec::new();
    for (n, &a) in seating.iter().enumerate() {
        for &b in &seating[n + 1..] {
            let (ra, rb) = (g.row(a), g.row(b));
            if ra.obj() != rb.obj() || g.in_past(a, b) || g.in_past(b, a) {
                continue;
            }
            if vs.iter().any(|&q| g.row(q).obj() == ra.obj() && g.in_past(a, q) && g.in_past(b, q)) {
                continue;
            }
            let ks: BTreeSet<R::Key> = ra.to().iter().chain(rb.to().iter()).cloned().collect();
            let Some(o) = ra.obj() else { continue };
            out.push((ra.id().clone(), rb.id().clone(), ks, o));
        }
    }
    out
}

/// The seat ends behind reader `own`'s line (the Constitution's ruling on H4: a lay-down is a roster change: it
/// names the newest counted changes over its room and sits on the reader's line by them): each withdrawal of a
/// seat over a community whose newest named counted changes (the room's founding row where it names none) are all
/// strictly in the past of the own heads of a counted act on the reader's line, it not in that act's past (the
/// sibling-safe line). Such an end is no vacancy end for that reader. The line is read as the reader's roster
/// reads it: a counted row the reader signed does not acknowledge the changes void for it ([`ack_void`], with
/// `reader` the changes void for the reader where `c` holds the rows concluded for it).
pub(crate) fn reader_ends<R: SeatRow, S: CutSpec<R>>(
    c: &Concluded<'_, R>,
    law: &SeatLaw,
    spec: &S,
    own: &R::Key,
    reader: Option<&BTreeSet<R::Id>>,
) -> BTreeSet<R::Id> {
    let g = &c.g;
    let by: BTreeMap<&R::Id, &R> = c.cs().iter().map(|&i| (g.row(i).id(), g.row(i))).collect();
    let mut lines: BTreeMap<ObjOf<R>, Vec<usize>> = BTreeMap::new();
    let mut out = BTreeSet::new();
    for &w in c.cs() {
        let wr = g.row(w);
        if wr.seat_kind() != SeatKind::Withdraw {
            continue;
        }
        let Some(t) = wr.target().and_then(|t| by.get(t)).copied() else { continue };
        if !matches!(t.seat_kind(), SeatKind::Offer | SeatKind::Accept) {
            continue;
        }
        let Some(room) = object_of(t, &|i| by.get(i).copied()) else { continue };
        if !community(&by, &room) {
            continue;
        }
        let line = lines.entry(room.clone()).or_insert_with(|| {
            line::own_line_with(c, &SeatLine, Some(own), &room, &|a: usize| ack_void(c, law, spec, a, reader))
        });
        if line.is_empty() {
            continue;
        }
        // its heads: the newest counted changes among the rows it names, else the room's founding row
        let declared_r = declared(&by, &room);
        let named: Vec<usize> = wr
            .names()
            .iter()
            .filter_map(|n| g.idx(n))
            .filter(|&q| change(law, g.row(q), &room, Some(declared_r.as_slice())))
            .collect();
        let mut hs: Vec<usize> =
            named.iter().copied().filter(|&a| !named.iter().any(|&b| a != b && g.in_past(a, b))).collect();
        if hs.is_empty() {
            match &room {
                Obj::Row(id) => hs.extend(g.idx(id)),
                Obj::Key(_) => continue,
            }
        }
        let behind = line.iter().any(|&a| {
            !g.in_past(w, a)
                && w != a
                && hs.iter().all(|&h| g.row(a).head().iter().any(|ah| g.idx(ah).is_some_and(|ai| g.in_past(h, ai))))
        });
        if behind {
            out.insert(wr.id().clone());
        }
    }
    out
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
    let heads = counted_heads(law, heads, &|h| rows.iter().copied().find(|q| q.id() == h), past);
    if heads.is_empty() || !heads.iter().all(|h| rows.iter().any(|q| q.id() == h)) {
        return scopes.iter().map(|_| BTreeSet::new()).collect();
    }
    let by: BTreeMap<&R::Id, &R> = rows.iter().map(|q| (q.id(), *q)).collect();
    // as members_at: the union of the heads' pasts, folded (not intersected), with the acceptances of the rows
    // given that complete a seat there and their withdrawals
    let at = |q: &R| heads.iter().any(|h| q.id() == h || past(q.id(), h));
    let acc: BTreeSet<&R::Id> = completing(rows, law, &by, obj, &at, past).iter().map(|q| q.id()).collect();
    let sub: Vec<&R> =
        rows.iter().copied().filter(|q| at(q) || q.seat_kind() == SeatKind::Withdraw || acc.contains(q.id())).collect();
    let sc = concluded_over(sub);
    let seats = Seats::build(&sc, law, spec, None, None, None);
    scopes.iter().map(|scope| seats.holders(scope, obj, None)).collect()
}

/// The keys whose own leaving is among `p`: a concluded withdrawal, signed by the key, of the acceptance or
/// offer that seats it in `scope` over `obj`, with no seating of the key in that scope after it among `p`. A
/// version with a key's leaving in its own past does not count that key (`RosterHead.leaving_binds_by_past`),
/// unless a re-admission of the key that has the leaving in its own past is there too. A count over the duty
/// holders also leaves out
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
        if own && !seated_after(p, obj, w.signer(), w.id(), |m| m.scope().is_some_and(|s| s.as_ref() == scope)) {
            out.insert(w.signer().clone());
        }
    }
    out
}

/// Whether `p` (a counted row's past) holds an offer over `obj` seating `k`, by `seats`, that has the leaving
/// `w` in its own past: a seating of the key after its leaving. The one test of a re-admission, read by
/// [`left_in_past`] and [`stay_ended_in_past`].
fn seated_after<R: SeatRow>(
    p: &Past<'_, '_, R>,
    obj: &ObjOf<R>,
    k: &R::Key,
    w: &R::Id,
    seats: impl Fn(&R) -> bool,
) -> bool {
    p.rows().any(|m| {
        m.seat_kind() == SeatKind::Offer
            && m.obj().as_ref() == Some(obj)
            && m.to().contains(k)
            && seats(m)
            && p.past(w, m.id())
    })
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
        if stay_end(law, &by, w, &|a| p.get(a.id()).is_some() && p.past(a.id(), w.id())).as_ref() != Some(obj) {
            continue;
        }
        let k = w.signer();
        if !seated_after(p, obj, k, w.id(), |m| roster_offer(law, m)) {
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
    // a room's moderator, over the room (CC 4.5.13): over an object that is no community (a key's own roster) an
    // unseat is an ordinary counted row
    let by: BTreeMap<&R::Id, &R> = p.rows().map(|q| (q.id(), q)).collect();
    if !community(&by, &obj) {
        return false;
    }
    // an unseat of an agent's seat, of a key that holds one at the head the row names: a person's key is not
    // removed so, whatever scope the row states. This is also what makes a lift restore and not admit.
    let agent = scope.as_ref() == AGENT;
    if !agent || !members_at_with(p, law, spec, &obj, r.head(), AGENT, cache).contains(&r.to()[0]) {
        return false;
    }
    // the signer holds `moderate` at the newest heads it names, read with the withdrawals in the row's own past (its
    // laying down of the seat there: members_at)
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
    // the same seat; the re-seating names the newest counted changes in its own past as every roster row does (H4),
    // so it no longer names the removal's head
    if rem.obj() != r.obj() || rem.scope() != r.scope() || rem.to() != r.to() {
        return None;
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
    met_wide(policy, yes as u128, n as u128, declared.map(|d| d as u128))
}

/// [`met`] over counts wider than a `usize`: a base a caller states as a `u64` (`window::Base::Stated`) is
/// read whole on every target, 32-bit ones included. `usize` and `u64` widen to `u128` without loss, so the
/// answer is the same on every target.
pub fn met_wide(policy: Option<Policy>, y: u128, n: u128, declared: Option<u128>) -> bool {
    // the recall's threshold is the strict fraction with a floor; its base is read by the count
    if let Some(Policy::Recall(num, den, least)) = policy {
        return met_wide(Some(Policy::StrictFloor(num, den, least)), y, n, declared);
    }
    // strictly more than `num / den` of n
    let strict = |num: u64, den: u64| y * den as u128 > num as u128 * n;
    match policy {
        Some(Policy::AtLeast(num, den)) => n > 0 && y * den as u128 >= num as u128 * n,
        Some(Policy::Strict(num, den)) => strict(num, den),
        Some(Policy::StrictFloor(num, den, least)) => strict(num, den) && y >= least as u128,
        Some(Policy::One) => y >= 1,
        Some(Policy::Declared) => declared.is_some_and(|d| y >= d),
        _ => false,
    }
}

/// The counted removals among `unseats` that are out of force as contested (CC 2.7.7 rule 5: "Two cuts by keys of equal
/// standing that undo each other stay contested. A voice that the other cannot remove settles them"; CC 2.6.1.9,
/// 2.6.1.11). A voice of a counted removal `u` is no voice where another counted removal over the same group,
/// concurrent with `u` and in force, removes it; `u` is in force only if its count is still met without those voices.
/// Read as the well-founded fixed point: two removals that each need a voice the other removes are both out of force
/// (the roster stays as it was); one that needs nothing the other removes stands, and the other falls. It is the end
/// rule (a removed key's voice counts only where its removal is in that row's past) read for counted rows.
fn contested_out<'a, R: SeatRow, S: CutSpec<R>>(
    c: &Concluded<'a, R>,
    law: &SeatLaw,
    spec: &S,
    unseats: &[(usize, Option<ObjOf<R>>)],
    cache: &MembersAt<R>,
) -> BTreeSet<R::Id> {
    let g = &c.g;
    // every group (CC 2.7.7 is not scoped by kind); a moderator's lone removal is judged by the end rule and its
    // receipts (out_of_force), not here
    let grp: Vec<usize> = unseats
        .iter()
        .map(|(u, _)| *u)
        .filter(|&u| g.row(u).conf() == Some(Conf::Group) && !lone_act(c, u, law, spec, cache))
        .collect();
    if grp.len() < 2 {
        return BTreeSet::new();
    }
    let past_of = |u: usize| -> Vec<usize> { c.cs().iter().copied().filter(|&q| g.in_past(q, u)).collect() };
    // the keys a cut removes: an unseat's `to`; a dissolution's, every key holding a seat over its group in its past
    let cut_keys: BTreeMap<usize, BTreeSet<R::Key>> = grp
        .iter()
        .map(|&u| {
            let ur = g.row(u);
            let ks: BTreeSet<R::Key> = if is_dissolve(ur) {
                let anc = past_of(u);
                let sc = concluded_over(anc.iter().map(|&q| g.row(q)));
                let obj = ur.obj();
                Seats::build(&sc, law, spec, None, None, None)
                    .recs
                    .iter()
                    .filter(|x| obj.as_ref() == Some(&x.obj))
                    .map(|x| x.k.clone())
                    .collect()
            } else {
                ur.to().iter().cloned().collect()
            };
            (u, ks)
        })
        .collect();
    let mut threats: BTreeMap<usize, Vec<(usize, BTreeSet<R::Key>)>> = BTreeMap::new();
    for &u in &grp {
        let ur = g.row(u);
        let anc = past_of(u);
        let vs = voices(ur, &Past::new(g, u, &anc));
        let t: Vec<(usize, BTreeSet<R::Key>)> = grp
            .iter()
            .copied()
            .filter(|&u2| u2 != u && g.row(u2).obj() == ur.obj() && !g.in_past(u, u2) && !g.in_past(u2, u))
            // a removed key's concurrent voice counts at its own head and is not in force from the removal's head
            // on: u2 voids a voice of u only where u counts from u2's heads on (each head of u2 a head of u, or in
            // the past of one)
            .filter(|&u2| {
                g.row(u2).head().iter().all(|h2| {
                    ur.head().iter().any(|h| h == h2 || g.idx(h2).zip(g.idx(h)).is_some_and(|(a, b)| g.in_past(a, b)))
                })
            })
            .map(|u2| (u2, cut_keys[&u2].iter().filter(|k| vs.contains(*k)).cloned().collect::<BTreeSet<_>>()))
            .filter(|(_, ks)| !ks.is_empty())
            .collect();
        if !t.is_empty() {
            threats.insert(u, t);
        }
    }
    if threats.is_empty() {
        return BTreeSet::new();
    }
    let holds = |u: usize, live: &BTreeSet<usize>| -> bool {
        let Some(t) = threats.get(&u) else { return true };
        let void: BTreeSet<R::Key> =
            t.iter().filter(|(u2, _)| live.contains(u2)).flat_map(|(_, ks)| ks.iter().cloned()).collect();
        let anc = past_of(u);
        count_met_void(&Past::new(g, u, &anc), law, spec, None, &void)
    };
    let (mut d, mut pos): (BTreeSet<usize>, BTreeSet<usize>) = (BTreeSet::new(), grp.iter().copied().collect());
    loop {
        let d2: BTreeSet<usize> = grp.iter().copied().filter(|&u| holds(u, &pos)).collect();
        let p2: BTreeSet<usize> = grp.iter().copied().filter(|&u| holds(u, &d)).collect();
        if d2 == d && p2 == pos {
            break;
        }
        d = d2;
        pos = p2;
    }
    grp.iter().copied().filter(|u| !d.contains(u)).map(|u| g.row(u).id().clone()).collect()
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
    // the changes void for the counting rows being read (innermost last; [`void_changes`]), and for the reader the
    // rows are concluded for ([`for_reader`])
    void: RefCell<Vec<BTreeSet<<R as Row>::Id>>>,
    rvoid: RefCell<BTreeSet<<R as Row>::Id>>,
    // per election seating: its election's key, its electorate and its set, read over its own past
    views: RefCell<BTreeMap<<R as Row>::Id, election::View<R>>>,
    // the concurrent founders' amendments the reader holds ([`held_pairs`]): each line's later founders' count reads
    // the founders common to the two (C2)
    rpairs: RefCell<Vec<HeldPair<R>>>,
    // the seat ends behind the reader's line ([`reader_ends`]): no vacancy end for it (H4, the election)
    pub(crate) rends: RefCell<BTreeSet<<R as Row>::Id>>,
}

/// Two concurrent founders' amendments a reader holds: their ids, the keys the two seat, and the room.
type HeldPair<R> = (<R as Row>::Id, <R as Row>::Id, BTreeSet<<R as Row>::Key>, ObjOf<R>);

impl<R: SeatRow> MembersAt<R> {
    /// The changes void for the row being read: its own (S'') and its reader's.
    fn current_void(&self) -> BTreeSet<R::Id> {
        let mut v = self.void.borrow().last().cloned().unwrap_or_default();
        v.extend(self.rvoid.borrow().iter().cloned());
        v
    }
}

/// What [`removal_in_force`] reads of the seats at one head: the remover's standing seats, the duty holders,
/// and the agents.
type StandingAt<R> = (BTreeSet<SeatOf<R>>, BTreeSet<<R as Row>::Key>, BTreeSet<<R as Row>::Key>);
type StandingMemo<R> = BTreeMap<(<R as Row>::Id, Vec<<R as Row>::Id>, ObjOf<R>, <R as Row>::Key), StandingAt<R>>;

impl<R: SeatRow> Default for MembersAt<R> {
    fn default() -> Self {
        MembersAt {
            memo: RefCell::default(),
            standing: RefCell::default(),
            void: RefCell::default(),
            rvoid: RefCell::default(),
            views: RefCell::default(),
            rpairs: RefCell::default(),
            rends: RefCell::default(),
        }
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
    // a head void for the row or its reader is no head (members_at_c leaves it out): only the others must be among
    // the row's concluded ancestors
    let cv = cache.current_void();
    if !heads
        .iter()
        .filter(|h| !cv.contains(*h))
        .all(|h| p.graph().idx(h).is_some_and(|hi| p.ancestors().binary_search(&hi).is_ok()))
    {
        return BTreeSet::new();
    }
    let mut hs = heads.to_vec();
    hs.sort();
    hs.dedup();
    // the heads' seats are read with the acceptances and withdrawals of the row's own past (members_at_c): those
    // rows are part of the key
    let g = p.graph();
    let mut own: Vec<R::Id> = p
        .ancestors()
        .iter()
        .map(|&q| g.row(q))
        .filter(|q| matches!(q.seat_kind(), SeatKind::Accept | SeatKind::Withdraw))
        .map(|q| q.id().clone())
        .collect();
    own.sort();
    let void: Vec<R::Id> = cache.current_void().into_iter().collect();
    let key = (hs, own, void, obj.clone(), String::from(scope));
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
    let mut out = BTreeSet::new();
    for sc in [AGENT, NODE] {
        if p.rows().any(|q| q.scope().is_some_and(|s| s.as_ref() == sc)) {
            out.extend(members_at_with(p, law, spec, obj, heads, sc, cache));
        }
    }
    out
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
    let over = obj; // H2: a counted row is counted over its own object
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
    // and a family's founder role ends with any leaving of the key (its member seat, or the founding row) in the
    // row's past, whatever head that row names
    let role = counted == "founder"
        && match &over {
            Obj::Row(i) => p.get(i).is_some_and(|g| g.group_kind().is_some_and(|k| k.as_ref() == "family")),
            Obj::Key(_) => false,
        };
    if !mem.is_empty() && (law.is_duty(counted, &duties) || role) {
        for k in stay_ended_in_past(p, law, &over) {
            mem.remove(&k);
        }
    }
    mem
}

/// CC 4.5.4: a duty seat is placed only by the founding record, by "the duty holders of C, counted under line
/// (iv)", or by "the members' count under line (v)", which "is the election of rule 2". So a counted offer of a
/// duty scope over a community concludes only where it is the duty holders' count or an election's acceptance
/// ([`Policy::Ranked`]). The duty holders' count is over all the duty holders of the room it confers in:
/// [`SeatRow::counted`] the duty holders' scope itself (`duty`), under [`Policy::DutyConfer`], with
/// [`SeatRow::over`] absent or the room. A members' count under an admission-style policy, one duty's holders, a
/// policy such as `accord_halt`, or a count over another room confers no duty (CIRISConstitution#241). A seat
/// that makes its holder no duty holder (a node's detector seat) is not reached.
fn duty_gate<R: SeatRow>(law: &SeatLaw, by: &BTreeMap<&R::Id, &R>, p: &Past<'_, '_, R>, r: &R) -> bool {
    let (Some(obj), Some(s)) = (r.obj(), r.scope()) else { return true };
    let declared = declared(by, &obj);
    if !community(by, &obj) || !law.is_duty(s.as_ref(), &declared) {
        return true;
    }
    // the gate reads the policy in force (the acts table's, where it binds: a fixed act's row may state none)
    let Ok(fs) = policy_in_force(law, p, r) else { return false };
    let pol = fs.first().and_then(|f| f.pol);
    if pol == Some(Policy::Ranked) {
        return true;
    }
    // over all the duty holders (one duty's holders are not all of them), under the duty policy
    r.counted().is_some_and(|c| c.as_ref() == "duty") && pol == Some(Policy::DutyConfer)
}

/// A counted change of `obj`'s roster, `q` concluded: a roster-changing row that concludes under the policy the
/// room's record binds to its act, however many voices that policy needs (the ruling of 2026-11-26). The line's
/// counted act, not a self-admission under a policy it states itself (with the binding off, H3: no head a count
/// may name; with the acts table on, a self-admission concluded under the room's declared protocol is one); and,
/// where `room` (`obj` is a community), a duty holder's own conferral of a duty over it (an offer `Conf::Own` or
/// `Conf::Seat`, not the founding row, of a scope that is no roster seat: the lone holder's, on one voice).
fn change<R: SeatRow>(law: &SeatLaw, q: &R, obj: &ObjOf<R>, room: Option<&[&str]>) -> bool {
    if LineSpec::<R>::counted_act(&SeatLine, q).is_some_and(|(o, _)| o == *obj) {
        return law.acts.is_some() || !authored_head(law, q);
    }
    room.is_some_and(|declared| own_conferral(law, q, obj, declared))
}

/// A self roster's landed lone-path window over `obj` is a counted change of it, as the counted eviction or addition
/// it is (a head a later count names, H1): a landing that says `landed` of a [`SeatRow::evicts`] or [`SeatRow::adds`]
/// opener over `obj`, held in `p`.
fn landed_change<R: SeatRow>(p: &Past<'_, '_, R>, q: &R, obj: &ObjOf<R>) -> bool {
    q.landing().is_some_and(|(op, says)| {
        says.as_ref() == "landed"
            && p.get(op).is_some_and(|o| (o.evicts().is_some() || o.adds().is_some()) && o.obj().as_ref() == Some(obj))
    })
}

/// A one-key conferral of a duty over a room: an offer of `Conf::Own` or `Conf::Seat` over `obj`, not its founding
/// row, of a duty scope (`declared`: the room's declared duties). An own offer of any other scope is no counted
/// change.
fn own_conferral<R: SeatRow>(law: &SeatLaw, q: &R, obj: &ObjOf<R>, declared: &[&str]) -> bool {
    q.seat_kind() == SeatKind::Offer
        && matches!(q.conf(), Some(Conf::Own) | Some(Conf::Seat))
        && q.obj().as_ref() == Some(obj)
        && !founding(q)
        && q.scope().is_some_and(|s| {
            !roster_word(s.as_ref())
                && s.as_ref() != NODE
                && !law.roster_seats.iter().any(|x| x == s.as_ref())
                && law.is_duty(s.as_ref(), declared)
        })
}

/// The declared duties of `obj` where it is a community among `p` (its founding row is there), else `None`.
fn room_in<'a, R: SeatRow>(p: &Past<'_, 'a, R>, obj: &ObjOf<R>) -> Option<Vec<&'a str>> {
    let by: BTreeMap<&R::Id, &R> = p.rows().map(|q| (q.id(), q)).collect();
    community(&by, obj).then(|| declared(&by, obj))
}

/// Whether the newest heads named are not the newest counted changes over `obj` in `p`, a counted row's
/// concluded past (H1): a counted change over `obj` ([`change`]) in `p` that is neither one of them nor in the
/// past of one (the void changes apart: [`newer_head_in_past_v`]); or one of them that is
/// neither such a change nor `obj`'s founding row (H3, H8: no other row, a version row, a note or a row
/// naming itself, is a head of a count). A counted row over a roster concludes only at the newest counted
/// changes over it in its own past (CC 2.7.8). A cosignature needs no reading of its own: it is a voice only
/// where the row names it, so the row's past holds the cosignature's.
pub(crate) fn newer_head_in_past<R: SeatRow>(
    p: &Past<'_, '_, R>,
    law: &SeatLaw,
    obj: &ObjOf<R>,
    heads: &[R::Id],
    keys: &BTreeSet<R::Key>,
) -> bool {
    newer_head_in_past_v(p, law, obj, heads, keys, &BTreeSet::new())
}

/// [`newer_head_in_past`], the changes in `void` (void for the row being read: [`void_changes`], and its reader's)
/// apart: a void change is no head of the row and need not be named.
fn newer_head_in_past_v<R: SeatRow>(
    p: &Past<'_, '_, R>,
    law: &SeatLaw,
    obj: &ObjOf<R>,
    heads: &[R::Id],
    _keys: &BTreeSet<R::Key>,
    void: &BTreeSet<R::Id>,
) -> bool {
    // the named heads are an antichain: a named head in another named head's past is refused, not dropped
    if heads.iter().any(|a| heads.iter().any(|b| a != b && p.past(a, b))) {
        return true;
    }
    let heads: Vec<&R::Id> = heads.iter().filter(|h| !void.contains(*h)).collect();
    let room = room_in(p, obj);
    if heads.iter().any(|&h| {
        *obj != Obj::Row(h.clone())
            && !p.get(h).is_some_and(|q| change(law, q, obj, room.as_deref()) || landed_change(p, q, obj))
    }) {
        return true;
    }
    p.rows().any(|q| {
        (change(law, q, obj, room.as_deref()) || landed_change(p, q, obj))
            && !heads.iter().any(|&h| h == q.id() || p.past(q.id(), h))
            && !void.contains(q.id())
    })
}

/// A lone duty holder with an offer of a duty seat standing confers no other alone until that offer is accepted or
/// withdrawn: whether `p` (a conferral's past) holds an offer over the conferral's room of any duty scope, signed by
/// a holder in `mem` (the duty holders at its heads), to a key not among them that has not consented to it (neither
/// signed it nor accepted it in `p`), that no withdrawal in `p` ends. It
/// counts for the lone test only: the key offered holds nothing until it accepts.
fn lone_offer_stands<R: SeatRow>(law: &SeatLaw, p: &Past<'_, '_, R>, r: &R, mem: &BTreeSet<R::Key>) -> bool {
    let Some(obj) = r.obj() else { return false };
    let by: BTreeMap<&R::Id, &R> = p.rows().map(|q| (q.id(), q)).collect();
    let declared = declared(&by, &obj);
    let gone: BTreeSet<&R::Id> =
        p.rows().filter(|w| w.seat_kind() == SeatKind::Withdraw).filter_map(|w| w.target()).collect();
    p.rows().any(|o| {
        o.seat_kind() == SeatKind::Offer
            && o.id() != r.id()
            && o.obj().as_ref() == Some(&obj)
            && !founding(o)
            && mem.contains(o.signer())
            && o.scope().is_some_and(|s| law.is_duty(s.as_ref(), &declared))
            && o.to().iter().any(|k| {
                !mem.contains(k)
                    && !signed_by(o, k)
                    // an offer the key once accepted is consumed, though it then withdrew the acceptance (left
                    // the seat): rule (2) makes the conferrer's withdrawal of it no end of the ended seat
                    && !p.rows().any(|a| a.seat_kind() == SeatKind::Accept && a.signer() == k && a.of() == Some(o.id()))
            })
            && !gone.contains(o.id())
    })
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
    count_met_void(p, law, spec, cache, &BTreeSet::new())
}

/// [`count_met`] with the voices `void` taken out (a concurrent counted removal's: [`contested_out`]).
fn count_met_void<R: SeatRow, S: CutSpec<R>>(
    p: &Past<'_, '_, R>,
    law: &SeatLaw,
    spec: &S,
    cache: Option<&MembersAt<R>>,
    void: &BTreeSet<R::Key>,
) -> bool {
    // the count reads the policy in force (the acts table, the room's protocol), never the stated one; policies the
    // table joins by `&` are each met (a change of the record: the protocol in force and the standing default)
    let Ok(fs) = policy_in_force(law, p, p.row()) else { return false };
    !fs.is_empty() && fs.iter().all(|f| count_under(p, law, spec, cache, f, void))
}

/// [`count_met`]'s count under one policy in force `f`.
fn count_under<R: SeatRow, S: CutSpec<R>>(
    p: &Past<'_, '_, R>,
    law: &SeatLaw,
    spec: &S,
    cache: Option<&MembersAt<R>>,
    f: &InForce<'_, R>,
    void: &BTreeSet<R::Key>,
) -> bool {
    let r = p.row();
    let is_offer = r.seat_kind() == SeatKind::Offer;
    let Some(obj) = r.obj() else { return false };
    let pol = f.pol;
    // the lift is told by its act where the binding is on and the object has a kind, by its policy otherwise
    if is_lift(law, &|i| p.get(i), r, pol) {
        // the overturn's count over the objections the row names, at the head the removal names
        // a lift restores and does not admit: the removal it cites is a lone removal, so the key held its
        // agent's seat at that head (lone_removal)
        let Some((author, v)) = lift_voices_with(p, law, spec, cache) else { return false };
        // the members are persons: the key removed is an agent's, no voice and not counted over (the base, the
        // members at both heads, is roster-kinds' follow-up)
        let mem = persons_at_with(p, law, spec, &obj, r.head(), "member", cache);
        // the author is not among the members the majority is taken of, and its own keys are the author: the
        // objections and the members by person, the author apart by person
        let rows: Vec<&R> = p.rows().collect();
        let pp = Persons::over(&rows, law, spec, Some(&obj));
        let (mem, v) = pp.count(&mem, &v, None, &[author]);
        return count_of(pol, is_offer, r.to(), &mem, &v, None, |_| 0);
    }
    if pol == Some(Policy::Ranked) {
        // the election's seating (C1 to C5): its electorate read at its election's vacancy, not at a head
        return is_offer && election::count(p, law, spec, cache);
    }
    let mut mem = count_members_with(p, law, spec, cache);
    if let Some((m, n)) = f.infra {
        // CC 2.7.8's wait for founders' amendments: two concurrent ones are concurrent versions of the record. Until a
        // version names both (and restates the word for the founders it leaves), no founders' count concludes over a
        // past holding both; that version is itself a founders' amendment, counted at the present M over the
        // founders common to the two (the founders at its heads) and signed by every key the two seated
        let amends: Vec<&R> = p
            .rows()
            .filter(|q| {
                q.seat_kind() == SeatKind::Offer
                    && q.conf() == Some(Conf::Group)
                    && q.obj().as_ref() == Some(&obj)
                    && q.scope().is_some_and(|s| s.as_ref() == "record")
            })
            .collect();
        let seating: Vec<&R> = amends
            .iter()
            .copied()
            .filter(|q| q.role().is_some_and(|x| x.as_ref() == "founder") && !q.to().is_empty())
            .collect();
        let mut pair_keys: BTreeSet<R::Key> = BTreeSet::new();
        for (i, a) in seating.iter().enumerate() {
            for b in &seating[i + 1..] {
                let (ai, bi) = (a.id(), b.id());
                if p.past(ai, bi) || p.past(bi, ai) || amends.iter().any(|q| p.past(ai, q.id()) && p.past(bi, q.id())) {
                    continue;
                }
                pair_keys.extend(a.to().iter().cloned());
                pair_keys.extend(b.to().iter().cloned());
            }
        }
        if !pair_keys.is_empty() {
            if !r.scope().is_some_and(|s| s.as_ref() == "record") {
                return false;
            }
            let v = voices(r, p);
            if !pair_keys.iter().all(|k| v.contains(k)) {
                return false;
            }
            let common: BTreeSet<R::Key> = mem.iter().filter(|k| !pair_keys.contains(*k)).cloned().collect();
            let union: BTreeSet<R::Key> = common.iter().chain(pair_keys.iter()).cloned().collect();
            let new_r: Vec<&R::Key> =
                if is_offer { r.to().iter().filter(|k| !union.contains(*k)).collect() } else { Vec::new() };
            let Some(RoomProtocol::Quorum(m2, n2)) =
                r.consensus_protocol().and_then(|w| RoomProtocol::parse_in(w.as_ref(), true))
            else {
                return false;
            };
            if usize::try_from(n2) != Ok(union.len() + new_r.len()) || !usize::try_from(m2).is_ok_and(|m2| m2 >= m) {
                return false;
            }
            if !new_r.iter().all(|k| v.contains(*k)) {
                return false;
            }
            // one voice per person, as every count ([`Persons::count`])
            let rows: Vec<&R> = p.rows().collect();
            let pp = Persons::over(&rows, law, spec, Some(&obj));
            let vot: BTreeSet<R::Key> = common.iter().filter(|k| !void.contains(*k)).cloned().collect();
            return pp.count(&common, &v, Some(&vot), &[]).1.len() >= m;
        }
        // C2 (the ruling on reader_state): for a reader holding two concurrent founders' amendments, a founders' count
        // whose own past holds only one of them reads the founders common to the two
        if let Some(cache) = cache {
            let held: BTreeSet<R::Key> = cache
                .rpairs
                .borrow()
                .iter()
                .filter(|(a, b, _, o)| *o == obj && p.get(a).is_some() != p.get(b).is_some())
                .flat_map(|(_, _, ks, _)| ks.iter().cloned())
                .collect();
            if !held.is_empty() {
                mem.retain(|k| !held.contains(k));
            }
        }
        // stalled (fewer than M + 1 active founders): the founders' count admits and removes nothing
        if !r.scope().is_some_and(|s| s.as_ref() == "record") && mem.len() < m + 1 {
            return false;
        }
        // N in the word is documentary once a removal leaves it stale; M binds
        if r.scope().is_some_and(|s| s.as_ref() == "record") {
            // a founders' amendment: it seats its new keys, signed by each, and is a widening by the founders'
            // count, so a stalled room makes none
            let new: Vec<&R::Key> =
                if is_offer { r.to().iter().filter(|k| !mem.contains(*k)).collect() } else { Vec::new() };
            let v = voices(r, p);
            if !new.iter().all(|k| v.contains(*k)) {
                return false;
            }
            if !new.is_empty() && mem.len() < m + 1 {
                return false;
            }
            // the word (the Constitution's narrowing): a version leaving the founders at or below the word's N keeps
            // it (counted at the present M); one leaving more names a new word, N the founders it leaves and M its
            // strict majority. No version names a word whose M is below the present M or is not its N's strict
            // majority; a new word other than the one in force states the founders the version leaves
            let n_after = mem.len() + new.len();
            let stated = match r.consensus_protocol() {
                None => None,
                Some(w) => match RoomProtocol::parse_in(w.as_ref(), true) {
                    Some(RoomProtocol::Quorum(m2, n2)) => Some((m2, n2)),
                    _ => return false,
                },
            };
            let unchanged = stated.is_none_or(|(m2, n2)| usize::try_from(m2) == Ok(m) && usize::try_from(n2) == Ok(n));
            if unchanged && n_after > n {
                return false;
            }
            if let Some((m2, n2)) = stated.filter(|_| !unchanged) {
                if !usize::try_from(m2).is_ok_and(|m2| m2 >= m) {
                    return false;
                }
                if usize::try_from(n2) != Ok(n_after) {
                    return false;
                }
            }
        }
    }
    // a family under founder_only: a removal takes an active founder other than the one it names
    // voices voided by a concurrent counted removal ([`contested_out`]) are none; under the room's protocol the key a
    // removal removes is neither counted over nor a voice
    // an eviction from a self roster: the key evicted is no voice of it (a roster whose only live key is the one
    // evicted cannot evict it: the one-key residual)
    let evicts = r.seat_kind() == SeatKind::Unseat && r.policy().is_some_and(|w| w.as_ref() == "self_roster_evict");
    let drop_to = f.exclude_target || f.base_excludes_target || evicts;
    let mem: BTreeSet<R::Key> =
        if f.base_excludes_target { mem.into_iter().filter(|k| !r.to().contains(k)).collect() } else { mem };
    // a count over persons, one voice and one member per person (ruled on CIRISConstitution#224): the voices are
    // mapped to persons first and then held to the voting base (the members less the voided and the excluded
    // target), so a device of the target or of a voided member is no voice; the base is counted by person
    let rows: Vec<&R> = p.rows().collect();
    let pp = Persons::over(&rows, law, spec, Some(&obj));
    let vot: BTreeSet<R::Key> =
        mem.iter().filter(|k| !void.contains(*k) && !(drop_to && r.to().contains(*k))).cloned().collect();
    let key_mem = mem;
    let (mem, v) = pp.count(&key_mem, &voices(r, p), Some(&vot), &[]);
    // a family's removal naming only its own signer, on that signature alone, concludes nothing (F3)
    if f.no_self_removal && v.iter().all(|k| r.to().contains(k)) {
        return false;
    }
    // the community floor, where a policy row governs alone in place of a protocol that states no rule (`&`)
    if f.floor > 0 && v.iter().filter(|k| mem.contains(*k) && !r.to().contains(k)).count() < f.floor {
        return false;
    }
    // the recall is told by its act where the binding reads one (an unseat of a duty counted over the members), by
    // its policy otherwise: the base exclusion of the holder follows Act::Recall, and Policy::Recall is only the
    // threshold its fixed row maps to
    let pol = match (law.acts.as_ref().and_then(|_| act_of(law, &|i| p.get(i), r)), pol) {
        (Some((Act::Recall, _, _)), Some(Policy::StrictFloor(n, d, l))) => Some(Policy::Recall(n, d, l)),
        (Some((a, _, _)), Some(Policy::Recall(n, d, l))) if a != Act::Recall => Some(Policy::StrictFloor(n, d, l)),
        (_, pol) => pol,
    };
    // the recall judges one holder: the holder apart by person, from the base and the voices
    let (mem, v) = if !is_offer && matches!(pol, Some(Policy::Recall(..))) {
        pp.count(&key_mem, &voices(r, p), Some(&vot), r.to())
    } else {
        (mem, v)
    };
    if pol == Some(Policy::DutyConfer) && mem.len() < 2 && lone_offer_stands(law, p, r, &mem) {
        return false; // a lone holder with a duty offer of its own standing confers no other alone
    }
    // the threshold and the weights in force: the record's under the room's protocol, the row's otherwise
    let count = GroupCount { policy: pol, offer: is_offer, to: r.to(), members: &mem, voices: &v, need: f.need };
    let wr: &R = f.weights.unwrap_or(r);
    // a ranked count was answered above, so the count answers
    group_count(&count, |k| wr.weights().iter().find(|(w, _)| w == k).map_or(0, |(_, x)| *x)).unwrap_or(false)
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
    if end_of_ended(p, law, spec, &by, r) {
        return false; // (2): no second end of a seat
    }
    match r.seat_kind() {
        SeatKind::Offer | SeatKind::Unseat => {
            let is_offer = r.seat_kind() == SeatKind::Offer;
            let conf = r.conf();
            // after a group's dissolution no row over it concludes (group_dissolved)
            if !founding(r) && r.obj().is_some_and(|o| dissolved_in(p, &o)) {
                return false;
            }
            // a dissolution is counted at the newest heads in its own past: every counted row over the group there
            // is a head or in a head's past
            if is_dissolve(r) {
                let obj = r.obj();
                let stale = p.rows().any(|q| {
                    q.conf() == Some(Conf::Group)
                        && matches!(q.seat_kind(), SeatKind::Offer | SeatKind::Unseat)
                        && q.obj() == obj
                        && !r.head().contains(q.id())
                        && !r.head().iter().any(|h| p.past(q.id(), h))
                });
                if stale {
                    return false;
                }
            }
            if is_offer && revoked_before(law, spec, r, p, &by, cache) {
                return false; // a revoked key does not re-seat itself; a room key whose seat's end stands is not seated again
            }
            if !founding(r) && !roster_placement(law, r, &by) {
                return false; // who places a roster seat over a group
            }
            // a single key's own offer of a duty (or one under its seat) concludes only where that key is the lone
            // person duty holder: "or by the lone holder with the new holder's acceptance" (CC 4.5.4), in every
            // community (CIRISConstitution#241)
            let own_duty = || {
                r.obj().is_some_and(|o| {
                    !founding(r)
                        && community(&by, &o)
                        && r.scope().is_some_and(|s| law.is_duty(s.as_ref(), &declared(&by, &o)))
                })
            };
            if is_offer
                && matches!(conf, Some(Conf::Own) | Some(Conf::Seat))
                && (duty_seat(law, &by, r) || own_duty())
                && !lone(law, spec, r, p, cache)
            {
                return false;
            }
            let Some(obj) = r.obj() else { return false };
            match conf {
                Some(Conf::Own) => {
                    if obj == Obj::Row(r.id().clone()) {
                        // one self roster per identity (G1, ruled): a second founding of a self roster by an identity
                        // whose roster is in the row's past is a rival founding and concludes nothing; no key
                        // re-founds itself, or adds a device, by founding
                        if is_offer
                            && self_founding(law, r)
                            && p.rows().any(|q| q.signer() == r.signer() && self_founding(law, q))
                        {
                            return false;
                        }
                        return is_offer; // a founding row is its own object
                    }
                    // over infrastructure a founder seat comes only by a founders' amendment: an own offer seats none
                    if r.scope().is_some_and(|s| s.as_ref() == "founder")
                        && kind_of(law, &|i| p.get(i), &obj) == Some(CommunityKind::Infrastructure)
                    {
                        return false;
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
                    // an infrastructure room's recovery widening while stalled is undecided ([`stalled_recovery`]): the
                    // kernel holds no bundle holders, so it concludes nothing
                    if r.bundle().is_some() {
                        return false;
                    }
                    // H2: a counted row is counted over its own object; one stating another concludes nothing
                    if r.over().is_some_and(|o| o != obj) {
                        return false;
                    }
                    if is_offer && !duty_gate(law, &by, p, r) {
                        return false; // CC 4.5.4: a duty is placed by its holders' count or an election
                    }
                    // the changes void for this row (S'') are no heads of it and add nothing to its members; the
                    // pass's cache carries them down (a cache of its own where the caller gave none)
                    let local = MembersAt::<R>::default();
                    let cache = cache.unwrap_or(&local);
                    let void = void_changes(p, law, spec, Some(cache));
                    cache.void.borrow_mut().push(void);
                    // H1, H4: every counted row names the newest counted changes over its object in its own past, a
                    // lone removal, a self-admission, a lift and an election's seating included
                    let ok = if newer_head_in_past_v(p, law, &obj, r.head(), &signers(r), &cache.current_void()) {
                        false
                    } else if !is_offer && lone_removal(r, p, law, spec, Some(cache)) {
                        true // CC 4.5.13: a moderator, an agent's key
                    } else {
                        count_met(p, law, spec, Some(cache))
                    };
                    cache.void.borrow_mut().pop();
                    ok
                }
                None => false,
            }
        }
        SeatKind::Accept if revoked_before(law, spec, r, p, &by, cache) => false, // the same offer accepted again
        // an acceptance of an offer over a dissolved group seats nothing (group_dissolved)
        SeatKind::Accept
            if r.of()
                .and_then(|o| by.get(o))
                .and_then(|o| o.obj())
                .or_else(|| r.obj())
                .is_some_and(|o| dissolved_in(p, &o)) =>
        {
            false
        }
        SeatKind::Accept => match r.of() {
            None => true,
            Some(o) => by.get(o).is_some_and(|o| o.to().contains(r.signer())),
        },
        SeatKind::Withdraw => match r.target().and_then(|t| by.get(t)) {
            Some(t) => {
                if !(signed_by(*t, r.signer()) || (t.seat_kind() == SeatKind::Offer && t.to().contains(r.signer()))) {
                    return false;
                }
                // H4: a withdrawal of a seat over a community (a resignation, a laying down) names the newest
                // counted changes over the room in its own past among the rows it names
                if !matches!(t.seat_kind(), SeatKind::Offer | SeatKind::Accept) {
                    return true;
                }
                let Some(room) = object_of(*t, &|i| by.get(i).copied()) else { return true };
                if !community(&by, &room) {
                    return true;
                }
                let named: Vec<R::Id> = r
                    .names()
                    .iter()
                    .filter(|n| {
                        room == Obj::Row((*n).clone())
                            || by.get(*n).is_some_and(|q| change(law, *q, &room, Some(declared(&by, &room).as_slice())))
                    })
                    .cloned()
                    .collect();
                // the rows a withdrawal names are no declared heads: the newest of them are read, as a count's heads
                let named: Vec<R::Id> =
                    named.iter().filter(|a| !named.iter().any(|b| *a != b && p.past(a, b))).cloned().collect();
                !newer_head_in_past_v(
                    p,
                    law,
                    &room,
                    &named,
                    &signers(r),
                    &cache.map(|c| c.current_void()).unwrap_or_default(),
                )
            }
            None => false,
        },
        SeatKind::Cosign => true,
        _ => other(p),
    }
}

/// A seat a row ends, for rule (2): the key, the scope, the object.
type EndedSeat<'a, R> = (&'a <R as Row>::Key, Option<&'a str>, Option<ObjOf<R>>);

/// The seats row `r` ends (rule (2)): an unseat, each key it names in its scope; a withdrawal, the seat its
/// target gives (its signer's own where it holds it, else every key the target seats), in [`end_scope`]'s
/// scope. A removal of an agent's key is none here: a lone one may be lifted or fall out of force, and then it
/// ended nothing.
fn ends_of<'a, R: SeatRow>(by: &BTreeMap<&R::Id, &'a R>, r: &'a R) -> Vec<EndedSeat<'a, R>> {
    match r.seat_kind() {
        SeatKind::Unseat => {
            let sc = r.scope().map(|s| s.as_ref());
            if sc == Some(AGENT) {
                return Vec::new();
            }
            r.to().iter().map(|k| (k, sc, r.obj())).collect()
        }
        SeatKind::Withdraw => {
            let Some(t) = r.target().and_then(|t| by.get(t)).copied() else { return Vec::new() };
            let sc = end_scope(by, r).map(|s| s.as_ref());
            match t.seat_kind() {
                SeatKind::Accept if t.signer() == r.signer() => {
                    let o = match t.of() {
                        Some(of) => by.get(of).copied(),
                        None => Some(t),
                    };
                    o.map(|o| alloc::vec![(r.signer(), sc, o.obj())]).unwrap_or_default()
                }
                SeatKind::Offer if t.to().contains(r.signer()) => alloc::vec![(r.signer(), sc, t.obj())],
                SeatKind::Offer => t.to().iter().map(|k| (k, sc, t.obj())).collect(),
                _ => Vec::new(),
            }
        }
        _ => Vec::new(),
    }
}

/// (2): an end of a seat that has an end of that seat in its own past is no end, whoever signed either (a
/// lay-down, a counted unseat, a withdrawal of the offer): every seat `r` ends has a concluded end in `r`'s
/// past with no seating of the key in that scope after it there.
///
/// Only an end in force is an earlier end: a counted removal rule 5 holds contested out (or a lone removal out
/// of force) ended nothing, and leaves the seat to a later end (the ruling on S4).
fn end_of_ended<R: SeatRow, S: CutSpec<R>>(
    p: &Past<'_, '_, R>,
    law: &SeatLaw,
    spec: &S,
    by: &BTreeMap<&R::Id, &R>,
    r: &R,
) -> bool {
    let seats = ends_of(by, r);
    if seats.is_empty() {
        return false;
    }
    // the removals out of force over the row's past, read once and only where an unseat is a candidate end
    let out: RefCell<Option<BTreeSet<R::Id>>> = RefCell::new(None);
    let in_force = |q: &R| {
        if q.seat_kind() != SeatKind::Unseat {
            return true;
        }
        let mut o = out.borrow_mut();
        let dropped = o.get_or_insert_with(|| {
            let sc = concluded_over(p.rows());
            Seats::build(&sc, law, spec, None, None, None).dropped
        });
        !dropped.contains(q.id())
    };
    seats.iter().all(|(k, sc, obj)| {
        p.rows().any(|q| {
            ends_of(by, q).iter().any(|e| e.0 == *k && e.1 == *sc && e.2 == *obj)
                && !obj.as_ref().is_some_and(|o| {
                    seated_after(p, o, k, q.id(), |m| {
                        seat_scopes(m, k, signed_by(m, k)).iter().any(|x| Some(x.s()) == *sc)
                    })
                })
                && in_force(q)
        })
    })
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
/// - `voices` is [`voices`] read as **persons** ([`persons_of`] over the row's past and `members`): the row's
///   signer, its cosigners, and the signers of the cosignatures it names that name every head it is counted
///   over, each key a member or speaking for the member its person is named by, one voice per person however many
///   live keys of it sign; a key with no person, or two, is no voice.
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
    /// under `unanimous`, `open:self_admit`, the duty withdrawal and the recall (`Policy::Recall`), whose
    /// text excludes it.
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
        return is_offer && room_count(yes, mem.len());
    }
    // the recall judges one holder: it is counted over the members less the holder it recalls, and that holder
    // is no voice of it, as the lift is counted over the room less the one it judges. A row is a recall when its
    // policy reads as `Policy::Recall` (the table's `moderator_recall`)
    if !is_offer && matches!(pol, Some(Policy::Recall(..))) {
        let base = mem.iter().filter(|k| !to.contains(k)).count();
        let yes = v.intersection(mem).filter(|k| !to.contains(k)).count();
        return met(pol, yes, base, need);
    }
    // no key admits itself (CC 2.7.5): a key the row seats is no voice of its count. On a removal the member
    // removed is a voice like any other unless the policy's own text excludes it: `unanimous` (below),
    // `open:self_admit`, the duty withdrawal and the recall (above) do. The voices that are members, ascending
    // and each once, read off the two sorted sets with no set built.
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

/// Who places a roster seat over a group (an object that is its own founding row): a member or agent seat
/// ([`seat_class`]) is placed or removed only by a counted row, the founding record, the key's own end, or (an
/// agent's key) a moderator's lone removal, itself a counted row (CC 3.1.3.2, CC 4.5.13, derived on
/// CIRISConstitution#224): one key's own row ([`Conf::Own`]) or a row under a seat ([`Conf::Seat`]) of such a seat
/// concludes nothing. A roster seat needs the key's own consent under every protocol: no flag on a row waives it (the
/// seat walk asks each key's acceptance, a node's seat over an infrastructure community alone excepted, by its scope
/// and the kind). Whether a counted row meets the room's declared protocol is [`act_of`]'s read, not this one.
fn roster_placement<R: SeatRow>(law: &SeatLaw, r: &R, by: &BTreeMap<&R::Id, &R>) -> bool {
    let (Some(obj), Some(sc)) = (r.obj(), r.scope()) else { return true };
    if !community(by, &obj) || seat_class(law, r, sc.as_ref()).is_none() {
        return true;
    }
    if matches!(r.conf(), Some(Conf::Own) | Some(Conf::Seat)) {
        return false;
    }
    true
}

/// Finality ([`SeatLaw::final_scopes`]): offer or acceptance `r` would seat a key again in a scope whose end is
/// final, with that end in its past. A scope that is no roster seat (`registered`): a concluded unseat of the same
/// key, scope and object in the offer's past. A roster seat, a room key's seat over a private room
/// ([`SeatRow::private_room`]): [`room_key_ended`] (the text's refusal `membership_room_key_ended`); an acceptance of
/// an offer seating the key is read as the offer is. A row concurrent with the end is not refused (a removal's cut voids it; a resignation does not reach it).
fn revoked_before<R: SeatRow, S: CutSpec<R>>(
    law: &SeatLaw,
    spec: &S,
    r: &R,
    p: &Past<'_, '_, R>,
    by: &BTreeMap<&R::Id, &R>,
    cache: Option<&MembersAt<R>>,
) -> bool {
    let fin = |s: &str| law.final_scopes.iter().any(|f| f == s);
    let (o, keys): (&R, Vec<&R::Key>) = match r.seat_kind() {
        SeatKind::Accept => match r.of().and_then(|o| by.get(o)) {
            Some(o) if o.seat_kind() == SeatKind::Offer => (*o, alloc::vec![r.signer()]),
            _ => return false,
        },
        _ => {
            if founding(r) {
                return false; // a founding row has no past
            }
            // a scope that holds a roster seat is read as one (`founder` included)
            if !r.scope().is_some_and(|s| seat_class(law, r, s.as_ref()).is_some()) {
                return p.rows().any(|q| {
                    q.seat_kind() == SeatKind::Unseat
                        && q.scope().is_some_and(|s| fin(s.as_ref()))
                        && q.scope() == r.scope()
                        && q.obj() == r.obj()
                        && q.to().iter().any(|k| r.to().contains(k))
                });
            }
            (r, r.to().iter().collect())
        }
    };
    let Some(obj) = o.obj() else { return false };
    if !row_of(by, &obj).is_some_and(|g| community(by, &obj) && g.private_room()) {
        return false;
    }
    keys.into_iter().any(|k| {
        // a roster seat is a word the row carries (the lone founder's `moderate` is no roster seat)
        seat_scopes(o, k, signed_by(o, k))
            .into_iter()
            .any(|sc| seat_class(law, o, sc.s()).is_some_and(fin) && room_key_ended(law, spec, p, by, k, &obj, cache))
    })
}

/// The end of key `k`'s stay over `obj` is among `p` (a row's concluded past), and it stands: a removal that is no
/// moderator's lone act (an unseat of a roster seat whose count is met over its own past, or that is not counted
/// at all) with an offer seating `k` in that seat in its past; or `k`'s own end of its stay ([`stay_end`]). A room
/// key is one presence in one room: an end of any of its roster seats bars every roster seat of it. A moderator's
/// lone removal is never final: the members may lift it, and out of force it ends nothing.
fn room_key_ended<R: SeatRow, S: CutSpec<R>>(
    law: &SeatLaw,
    spec: &S,
    p: &Past<'_, '_, R>,
    by: &BTreeMap<&R::Id, &R>,
    k: &R::Key,
    obj: &ObjOf<R>,
    cache: Option<&MembersAt<R>>,
) -> bool {
    let removed = p.rows().any(|q| {
        let Some(qs) = q.scope() else { return false };
        if q.seat_kind() != SeatKind::Unseat
            || q.obj().as_ref() != Some(obj)
            || seat_class(law, q, qs.as_ref()).is_none()
            || !q.to().contains(k)
        {
            return false;
        }
        if !p.rows().any(|m| seated_by(law, m, qs, k, obj) && p.past(m.id(), q.id())) {
            return false; // it ended no seat of k's
        }
        // every roster unseat over a community that concludes is counted ([`roster_placement`]): only a moderator's
        // lone removal, whose count is not met, is no final end
        let g = p.graph();
        let Some(u) = g.idx(q.id()) else { return false };
        let anc: Vec<usize> = p.ancestors().iter().copied().filter(|&x| g.in_past(x, u)).collect();
        count_met(&Past::new(g, u, &anc), law, spec, cache)
    });
    removed
        || p.rows().any(|w| {
            w.seat_kind() == SeatKind::Withdraw
                && w.signer() == k
                && stay_end(law, by, w, &|a| p.get(a.id()).is_some() && p.past(a.id(), w.id())).as_ref() == Some(obj)
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
    // and a lone holder with an offer of a duty seat standing confers no other alone
    held.len() == 1 && held.contains(r.signer()) && !lone_offer_stands(law, p, r, &held)
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
    let sole = Seats::build(&sc, law, spec, None, None, None);
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
        obj: Option<Obj<u32, u32>>,
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
        fn word(s: &'static str) -> String {
            s.into()
        }
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
            (self.kind == SeatKind::Offer).then(|| self.obj.clone().unwrap_or(Obj::Row(0)))
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
        T { id, names, signer, kind, to: vec![], cosigners: vec![], scope: None, target: None, obj: None }
    }

    // node 7's owner binding to `owner`, accepted by its cosignature, naming `names`
    fn binding(id: u32, owner: u32, names: Vec<u32>) -> T {
        let mut b = row(id, names, 7, SeatKind::Offer);
        b.to = vec![owner];
        b.cosigners = vec![owner];
        b.scope = Some("owner".into());
        b.obj = Some(Obj::Key(7));
        b
    }

    /// The one owner reading: one binding gives its owner; a re-binding (a binding with the earlier one in its
    /// past) moves the owner; two concurrent bindings are two owners, none (the consent cases in check_consent.py
    /// read the same rule through `seat.Seats.owner`).
    #[test]
    fn a_rebinding_moves_the_owner() {
        let law = SeatLaw::default();
        let owner = |rows: &[T]| {
            let c = Concluded::with(Graph::new(rows.iter()), None);
            Seats::new(&c, &law, &NoCut, None).owner(&7)
        };
        assert_eq!(owner(&[binding(1, 8, vec![])]), Some(8), "one binding");
        assert_eq!(owner(&[binding(1, 8, vec![]), binding(2, 9, vec![1])]), Some(9), "a re-binding moves it");
        assert_eq!(owner(&[binding(1, 8, vec![]), binding(2, 9, vec![])]), None, "two owners is none");
        assert_eq!(owner(&[binding(1, 8, vec![]), binding(2, 8, vec![1])]), Some(8), "a re-binding to the same owner");
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
                // scopes that are no roster seat: one key's own row places them (a member or agent seat over a group
                // is placed only by the founding record or a counted row)
                for (j, sc) in ["guest", "founder"].iter().enumerate() {
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
                            let scope = ["guest", "founder"][g.next(2) as usize];
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
