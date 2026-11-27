//! The causal end of a conferral (CC 2.4.1.1, CC 4.5.5; `models/tla/CONFERRAL_END.md`, rules E1 to E8).
//!
//! From a set of held rows, for every act exercised under a standing: does it **count** at the head it names,
//! is it **in force** now, and which rule decides. No instant is read and no arrival order: the answer is a
//! function of the rows, the reader's own acknowledged heads, and two parameters of the standing.
//!
//! * `counted` is a fact about the head the act names. A tally at that head and an as-of answer read it.
//! * `in_force` is whether the act has effect from the end's head on. Anything a host does now on the act's
//!   strength (serving it as a present act of the standing, wrapping a key to its signer) reads it.
//! * An act that authorises a further row passes both down, each to its own (E6).
//! * A deputy hangs from an act of the grantee, its deputy edge ([`ConferralRow::via`]). Nothing marks a row
//!   as an edge: an act is one exactly when another act's `via` names it, and an edge that itself has a
//!   `via` is an onward hop, a deputy deputizing. The grantee's own edge needs nothing more. An act whose edge
//!   is an onward hop counts only if the edge above that one carries sub-delegation
//!   ([`ConferralRow::sub_delegation`]), and no act counts more than [`Standing::deputy_depth`] `via` hops
//!   from the grantee's edge. Both are read from the rows' `via`, so no presentation of the onward row passes
//!   them. A deputy ends with the seat: the end reaches the edge, and the edge passes it down.
//!
//! The caller supplies the rows through [`ConferralRow`], who each key is to the standing through
//! [`Standing::role`], and the causal past through a function, so that it need not materialise a lineage. That
//! function answers three ways: yes, no, or "cannot tell until this row is held" ([`Past`]). Where an answer
//! needs a row the caller does not hold, the act is [`Answer::Undecided`], never a wrong bit.
//!
//! The reference is `models/causal_kernel/conferral_end.py`, compared with `ConferralEnd.tla` state by state
//! (`tools/conferral_xcheck.py`);
//! `tests/conferral_end.rs` replays its case table (`tests/fixtures/conferral_end.json`) through this module.
//!
//! One end per call. Two ends of one standing held together are not covered by the model, and this module
//! refuses them ([`Refused::SeveralEnds`]) and does not guess.

use alloc::collections::BTreeMap;
use alloc::vec::Vec;
use core::fmt::Debug;

/// What a row is to the standing whose end is being read.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Kind {
    /// A head: a roster version, a bundle version, or an owner binding.
    Head,
    /// An act exercised under the standing, by the grantee or by a deputy.
    Act,
    /// The end of the standing: a withdrawal of the offer or of the acceptance, an unseating, a resignation.
    End,
    /// A clean acknowledgement of one act by the ender's side.
    Receipt,
    /// A removal of a key.
    Removal,
    /// The grantee's own acceptance again, after its own withdrawal: a second standing of its own.
    Accept,
    /// The body's end of the named receipter's seat.
    ReceipterEnd,
    /// Any other row. It is not read.
    Other,
}

/// Who a key is to the standing.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Role {
    /// The conferrer. Where the conferrer is a count, the counted row's signer.
    Conferrer,
    /// The grantee: the one the standing was conferred on.
    Grantee,
    /// A single co-holder of the body the acts were done for.
    CoHolder,
    /// A receipter the grant names.
    Receipter,
    /// Anyone else: a deputy, a member, a node.
    Other,
}

/// Who may receipt, beside the conferrer.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Who {
    /// A single co-holder and a named receipter may, unless a count end lifts their receipts.
    All,
    /// Only the conferrer's own receipts keep anything (a root grant read that way).
    ConferrerOnly,
}

/// A row as this module reads it. The caller has verified and decoded it.
pub trait ConferralRow {
    /// The row's digest.
    type Id: Ord + Clone + Debug;
    /// A key id.
    type Key: Ord + Clone + Debug;
    /// The row's own digest.
    fn id(&self) -> &Self::Id;
    /// What the row is to the standing.
    fn kind(&self) -> Kind;
    /// The key that signed it.
    fn signer(&self) -> &Self::Key;
    /// The head an act or an end names (`refs.head`). `None` on any other row, and on an act that names none.
    fn head(&self) -> Option<&Self::Id>;
    /// The act a receipt acknowledges.
    fn of(&self) -> Option<&Self::Id> {
        None
    }
    /// The key a removal removes.
    fn target(&self) -> Option<&Self::Key> {
        None
    }
    /// The deputy edge a deputy's act is under: itself an act of the grantee, or of a deputy above.
    fn via(&self) -> Option<&Self::Id> {
        None
    }
    /// On a deputy edge: the deputy may deputize onward. An act two hops below an edge without it does not
    /// count. A fact the edge row states; it is read only when a row under a row under this one is judged.
    fn sub_delegation(&self) -> bool {
        false
    }
    /// On a count end: it lifts the receipts of single co-holders and of the receipter (a compromise).
    fn lifts(&self) -> bool {
        false
    }
}

/// The caller's causal past. `in_past(a, b)`: is row `a` in the causal past of row `b` (does `b` name it, or
/// name a row that has it in its past). `Err(id)` says the caller cannot tell until it holds the row `id`.
pub trait Past<I> {
    /// Whether `a` is in the past of `b`, or the row that must be held to tell.
    fn in_past(&self, a: &I, b: &I) -> Result<bool, I>;
}

impl<I, F: Fn(&I, &I) -> Result<bool, I>> Past<I> for F {
    fn in_past(&self, a: &I, b: &I) -> Result<bool, I> {
        self(a, b)
    }
}

/// The standing's parameters and the reader's own acknowledgement.
pub struct Standing<'a, I, K> {
    /// Who each key is to the standing.
    pub role: &'a dyn Fn(&K) -> Role,
    /// Another live standing of the grantee authorises the same acts (a second grant): E7.
    pub other_standing: bool,
    /// Who may receipt beside the conferrer.
    pub who: Who,
    /// The heads the reader has acknowledged (CC 2.7.8). An end that a newer acknowledged head does not have in
    /// its past is void for this reader.
    pub reader_acks: &'a [I],
    /// The most `via` hops an act may be from the grantee's own edge (the text's cap is [`DEPUTY_DEPTH`]). An
    /// act further down does not count; at 0 no deputy's act counts.
    pub deputy_depth: usize,
}

/// The text's cap on a chain of deputies: at most this many `via` hops from the grantee's own edge.
pub const DEPUTY_DEPTH: usize = 5;

/// The rule that decides an act, in the order the rules decide. [`Rule::as_str`] is the name the reference and
/// the fixture use.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Rule {
    /// The act's signer's key is removed by a removal that does not have the act in its past.
    KeyRemoved,
    /// No end is held: counted and in force.
    NoEnd,
    /// E1: the end names a head older than one in its own past. It concludes nothing.
    EndVoidStaleHead,
    /// The end's signer's key is removed by a removal that does not have the end in its past.
    EndVoidKeyRemoved,
    /// CC 2.7.8: the reader acknowledged a newer head that does not have the end in its past.
    EndVoidLine,
    /// E7: another live standing of the grantee authorises the act.
    OtherStanding,
    /// E4: the act has the end in its past. Not counted.
    NamesEnd,
    /// E3: the act names a head that has the end's head in its past. Not counted.
    LaterHead,
    /// E3, one say: the ender holds a clean receipt of that act concurrent with the end. Counted, not in force.
    OneSay,
    /// E8: a clean receipt by the ender's side, without the end in its past, is held. Counted and in force.
    Receipt,
    /// E2: counted at its own head, not in force.
    Forward,
    /// E6: an act more than [`Standing::deputy_depth`] `via` hops from the grantee's own edge. Not counted.
    Depth,
    /// E6: an act whose deputy edge is an onward hop under an edge that does not carry sub-delegation. Not
    /// counted.
    NoSub,
    /// E6: a deputy's act whose deputy edge does not count, or is not in force.
    Upstream,
}

impl Rule {
    /// The rule's name in `models/causal_kernel/conferral_end.py` and the fixture.
    pub fn as_str(self) -> &'static str {
        match self {
            Rule::KeyRemoved => "key_removed",
            Rule::NoEnd => "no_end",
            Rule::EndVoidStaleHead => "end_void.stale_head",
            Rule::EndVoidKeyRemoved => "end_void.key_removed",
            Rule::EndVoidLine => "end_void.line",
            Rule::OtherStanding => "E7.other_standing",
            Rule::NamesEnd => "E4.names_end",
            Rule::LaterHead => "E3.later_head",
            Rule::OneSay => "E3.one_say",
            Rule::Receipt => "E8.receipt",
            Rule::Forward => "E2.forward",
            Rule::Depth => "E6.depth",
            Rule::NoSub => "E6.no_sub",
            Rule::Upstream => "E6.upstream",
        }
    }
}

/// What the rows conclude about one act.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Judged {
    /// It counts at the head it names.
    pub counted: bool,
    /// It is in force now.
    pub in_force: bool,
    /// The rule that decides it.
    pub rule: Rule,
}

/// The answer for one act.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Answer<I> {
    /// The rows decide it.
    Judged(Judged),
    /// The caller's past cannot tell until it holds this row.
    Undecided(I),
}

/// Why no answer is given.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Refused<I> {
    /// More than one end is among the rows. The model has one end of a standing; call once for each, and read
    /// the combination as unchecked.
    SeveralEnds(I, I),
}

// counted, in force and the rule; or the row that must be held to tell
type Bits<I> = Result<(bool, bool, Rule), I>;

/// The answer for every act, by the act's id.
pub type Answers<I> = BTreeMap<I, Answer<I>>;

// `any` over a three-way answer: yes if any is yes; else the first row that must be held; else no.
pub(crate) fn any3<T, I>(items: impl Iterator<Item = T>, mut f: impl FnMut(T) -> Result<bool, I>) -> Result<bool, I> {
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

// head `h` is later than head `he`: it has `he` in its past
pub(crate) fn later<I, P: Past<I>>(past: &P, h: Option<&I>, he: Option<&I>) -> Result<bool, I> {
    match (h, he) {
        (Some(h), Some(he)) => past.in_past(he, h),
        _ => Ok(false),
    }
}

// an end is stale: a head in its past is later than the head it names
pub(crate) fn stale_head<'i, I: 'i, P: Past<I>>(
    past: &P,
    heads: impl Iterator<Item = &'i I>,
    end: &I,
    end_head: Option<&I>,
) -> Result<bool, I> {
    any3(heads, |h| Ok(past.in_past(h, end)? && later(past, Some(h), end_head)?))
}

struct Ctx<'a, R: ConferralRow, P> {
    rows: &'a [&'a R],
    st: &'a Standing<'a, R::Id, R::Key>,
    past: &'a P,
    end: Option<&'a R>,
}

impl<'a, R: ConferralRow, P: Past<R::Id>> Ctx<'a, R, P> {
    fn of_kind(&self, k: Kind) -> impl Iterator<Item = &'a R> + '_ {
        self.rows.iter().copied().filter(move |r| r.kind() == k)
    }

    // the row's signer's key is removed by a removal that does not have the row in its past
    fn key_cut(&self, r: &R) -> Result<bool, R::Id> {
        any3(self.of_kind(Kind::Removal), |m| {
            if m.target() != Some(r.signer()) {
                return Ok(false);
            }
            Ok(!self.past.in_past(r.id(), m.id())?)
        })
    }

    // head `h` is later than head `he`: it has `he` in its past
    fn later(&self, h: Option<&R::Id>, he: Option<&R::Id>) -> Result<bool, R::Id> {
        later(self.past, h, he)
    }

    // the rule that makes the end conclude nothing for this reader, if one does
    fn end_void(&self, e: &R) -> Result<Option<Rule>, R::Id> {
        let stale = stale_head(self.past, self.of_kind(Kind::Head).map(|h| h.id()), e.id(), e.head())?;
        if stale {
            return Ok(Some(Rule::EndVoidStaleHead));
        }
        if self.key_cut(e)? {
            return Ok(Some(Rule::EndVoidKeyRemoved));
        }
        let held = |h: &R::Id| self.rows.iter().any(|r| r.id() == h);
        // the line is sibling-safe (the ruling of 2026-11-27, as the seat model's line): the end is behind an
        // acknowledged head only where the head it names is strictly in the past of a head that one extends; an
        // end at the head an acknowledged version directly extends is its sibling, not behind it
        let behind = |h: &R::Id| {
            any3(self.of_kind(Kind::Head), |g| {
                Ok(self.later(Some(g.id()), e.head())? && self.later(Some(h), Some(g.id()))?)
            })
        };
        let line =
            any3(self.st.reader_acks.iter().filter(|h| held(h)), |h| Ok(behind(h)? && !self.past.in_past(e.id(), h)?))?;
        Ok(line.then_some(Rule::EndVoidLine))
    }

    fn role(&self, r: &R) -> Role {
        (self.st.role)(r.signer())
    }

    // the clean receipts of act `x`
    fn receipts(&self, x: &'a R::Id) -> impl Iterator<Item = &'a R> + '_ {
        self.of_kind(Kind::Receipt).filter(move |q| q.of() == Some(x))
    }

    fn eligible(&self, q: &R, e: &R) -> Result<bool, R::Id> {
        let lifted = e.lifts() && self.role(e) == Role::Conferrer;
        match self.role(q) {
            Role::Conferrer => Ok(true),
            Role::CoHolder => Ok(self.st.who == Who::All && !lifted),
            Role::Receipter => {
                if self.st.who != Who::All || lifted {
                    return Ok(false);
                }
                Ok(!any3(self.of_kind(Kind::ReceipterEnd), |x| self.past.in_past(x.id(), q.id()))?)
            }
            Role::Grantee | Role::Other => Ok(false),
        }
    }

    // E8: a clean receipt by the ender's side that does not have the end in its past
    fn kept(&self, x: &'a R::Id, e: &R) -> Result<bool, R::Id> {
        any3(self.receipts(x), |q| {
            Ok(!self.key_cut(q)? && self.eligible(q, e)? && !self.past.in_past(e.id(), q.id())?)
        })
    }

    // one say: the ender's own clean receipt of the act, concurrent with the end
    fn say(&self, x: &'a R::Id, e: &R) -> Result<bool, R::Id> {
        any3(self.receipts(x), |q| {
            Ok(q.signer() == e.signer()
                && !self.key_cut(q)?
                && !self.past.in_past(e.id(), q.id())?
                && !self.past.in_past(q.id(), e.id())?)
        })
    }

    // E7: another live standing of the grantee authorises the act
    fn other(&self, x: &R, e: &R) -> bool {
        if self.role(x) != Role::Grantee {
            return false;
        }
        self.st.other_standing
            || (self.role(e) == Role::Grantee && self.of_kind(Kind::Accept).any(|a| self.role(a) == Role::Grantee))
    }

    fn end_rule(&self, x: &'a R, void: &Result<Option<Rule>, R::Id>) -> Bits<R::Id> {
        let Some(e) = self.end else { return Ok((true, true, Rule::NoEnd)) };
        if let Some(v) = void.clone()? {
            return Ok((true, true, v));
        }
        if self.other(x, e) {
            return Ok((true, true, Rule::OtherStanding));
        }
        if self.past.in_past(e.id(), x.id())? {
            return Ok((false, false, Rule::NamesEnd));
        }
        if self.later(x.head(), e.head())? {
            return Ok(if self.say(x.id(), e)? {
                (true, false, Rule::OneSay)
            } else {
                (false, false, Rule::LaterHead)
            });
        }
        if self.kept(x.id(), e)? {
            return Ok((true, true, Rule::Receipt));
        }
        Ok((true, false, Rule::Forward))
    }

    // the deputy edge `x` is under, where it is held
    fn edge(&self, x: &R) -> Option<&'a R> {
        x.via().and_then(|v| self.rows.iter().copied().find(|r| r.id() == v && r.kind() == Kind::Act))
    }

    // The `via` hops from `x` up to the grantee's own edge. The walk stops one past the cap, or past the rows
    // (a cycle of names): the count is then already over the cap, or the cycle is left to `judge`. An edge
    // that is not held is the row to fetch.
    fn edges(&self, x: &R) -> Result<usize, R::Id> {
        let mut n = 0;
        let mut at = x;
        while let Some(v) = at.via() {
            if n > self.st.deputy_depth || n > self.rows.len() {
                break;
            }
            at = self.edge(at).ok_or_else(|| v.clone())?;
            n += 1;
        }
        Ok(n)
    }

    fn judge(
        &self,
        x: &'a R,
        void: &Result<Option<Rule>, R::Id>,
        memo: &mut BTreeMap<R::Id, Bits<R::Id>>,
        depth: usize,
    ) -> Bits<R::Id> {
        if let Some(a) = memo.get(x.id()) {
            return a.clone();
        }
        let out = (|| {
            if self.key_cut(x)? {
                return Ok((false, false, Rule::KeyRemoved));
            }
            let (mut c, mut f, mut rule) = self.end_rule(x, void)?;
            if self.edges(x)? > self.st.deputy_depth {
                return Ok((false, false, if c { Rule::Depth } else { rule }));
            }
            // a deputy's act follows its deputy edge; a chain of edges longer than the rows is a cycle of names
            let up = self.edge(x);
            // the edge `x` is under is an onward hop where it has a `via` itself: the edge above must carry
            // sub-delegation. Read from the rows, whatever the onward row is presented as
            if let Some(above) = up.and_then(|u| self.edge(u)) {
                if !above.sub_delegation() {
                    return Ok((false, false, if c { Rule::NoSub } else { rule }));
                }
            }
            if let (Some(u), true) = (up, depth < self.rows.len()) {
                let (uc, uf, _) = self.judge(u, void, memo, depth + 1)?;
                if (c && !uc) || (c && f && !uf) {
                    rule = Rule::Upstream;
                }
                (c, f) = (c && uc, c && f && uf);
            } else if let Some(v) = x.via() {
                // the deputy edge is not held (or the names cycle): nothing says the act is under a standing
                if up.is_none() {
                    return Err(v.clone());
                }
                (c, f, rule) = (false, false, Rule::Upstream);
            }
            Ok((c, f, rule))
        })();
        memo.insert(x.id().clone(), out.clone());
        out
    }
}

/// For every act among `rows`: whether it counts at its own head, whether it is in force, and the rule that
/// decides. `rows` are the rows the caller holds that bear on one standing: its heads, the acts under it, its
/// end if one is held, receipts, key removals, the grantee's re-acceptance, the receipter's end.
///
/// `past` is asked only about ids of these rows and the heads they name. Where it cannot tell, the acts that
/// need the answer are [`Answer::Undecided`] with the row to fetch.
pub fn answers<R: ConferralRow, P: Past<R::Id>>(
    rows: &[&R],
    standing: &Standing<'_, R::Id, R::Key>,
    past: &P,
) -> Result<Answers<R::Id>, Refused<R::Id>> {
    let mut ends = rows.iter().copied().filter(|r| r.kind() == Kind::End);
    let end = ends.next();
    if let (Some(a), Some(b)) = (end, ends.next()) {
        return Err(Refused::SeveralEnds(a.id().clone(), b.id().clone()));
    }
    let cx = Ctx { rows, st: standing, past, end };
    let void = match end {
        Some(e) => cx.end_void(e),
        None => Ok(None),
    };
    let mut memo = BTreeMap::new();
    let mut out = BTreeMap::new();
    let acts: Vec<&R> = rows.iter().copied().filter(|r| r.kind() == Kind::Act).collect();
    for x in acts {
        let a = match cx.judge(x, &void, &mut memo, 0) {
            Ok((counted, in_force, rule)) => Answer::Judged(Judged { counted, in_force, rule }),
            Err(i) => Answer::Undecided(i),
        };
        out.insert(x.id().clone(), a);
    }
    Ok(out)
}
