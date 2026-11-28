//! The trust root's fork fold (persist's item 15; the model is `models/trust_root/root.py`, its cases
//! `check_root.py`, replayed by `tests/root.rs`).
//!
//! A root is the lineage of a genesis bundle, named by its family key id. A bundle is a signed object, not a row:
//! the store presents it as a [`RootBundle`], its signatures already checked, and the kernel reads the count, the
//! heads, the fold at tips, the bundles in force for one reader, and the root grants counted over them.
//!
//! - **The count.** The first bundle is counted over every holder it lists; a later one over a strict majority of
//!   its predecessor's live holders; a join (two predecessors) over a strict majority of the live holders common to
//!   them. A statement whose iat disagrees with the payload's is Invalid on its own, and the bundle is counted on the
//!   rest. A key revoked with no bound leaves the live holders; a statement on a bundle that is not at or before its
//!   key's bound does not count. A holder's own key recovery (a bundle under its recovery key changing only its own
//!   seat) concludes on that key alone; one changing another seat concludes nothing
//!   (`recovery_changes_other_seat`), nor does a spent commitment.
//! - **The heads.** `version` is the predecessor's plus one (a join: the greater plus one) and `family` is its: a
//!   consistency check, never ranked. A later bundle is a counted change of the holders' roster, and S'' and T at
//!   the fork point apply to it as to a roster change. Two recoveries of one seat, neither in the other's past, are
//!   contested: neither replaces the seat until a bundle names both.
//! - **The fold.** Several tips' holders and seats are the guarded fold (CC 2.7.8); tips whose charters differ (the
//!   whole charter, compared as one value) do not fold, and the holders and seats are those common to them.
//! - **In force**, per reader: its anchor names its first bundle (else `genesis_bundle_not_anchored`); the bundles
//!   in force are the newest it acknowledged, folded where several; none acknowledged, the anchor.
//! - **Grants.** A grant exists where it is counted at a strict majority over the live holders of the bundles it
//!   names (their fold where several), under charters carrying its duty, naming the newest bundles in its signers'
//!   own past. It resolves for a reader while its bundle is in the reader's lineage
//!   and the scope in force there (what every tip carries) still carries the duty.
//!
//! The costs, stated: a recovery concurrent with an amend that changes the charter leaves the recovering holder no
//! seat in force until a bundle names both tips (it gives a holder majority nothing it lacks: the same majority
//! could remove that holder by an amend). Two joins of the same tips under different charters, neither in the
//! other's past, are contested: neither stands, a reader keeps the tips they tried to join, and a bundle naming
//! every one settles them, counted over those tips' common holders. Two successors of one bundle, and two joins
//! under the same charter, fold as tips: concurrent successors are not contested.
//!
//! The residual, stated: a holder's statement over a sibling bundle is not ordered against its grant, so it is not read; a grant on one tip is judged by the rows in its own past. It can matter only where that
//! holder's voice is the deciding one of an exact majority, and the statement and the grant are held evidence the
//! other holders can cite when they name both tips.
//!
//! Receipts, equivocation records and fork-attempt records move no head and are not read here.

use alloc::collections::{BTreeMap, BTreeSet};
use alloc::vec::Vec;
use core::cell::RefCell;

/// A genesis bundle (`ceg-genesis-bundle/2`) as the store presents it, its statements' signatures checked.
pub trait RootBundle {
    /// A bundle's id (and the family key id's type).
    type Id: Ord + Clone;
    /// A key: a holder, a seat, a recovery key.
    type Key: Ord + Clone;
    /// A charter, compared as one value, and a duty it carries.
    type Word: Ord + Clone + AsRef<str>;
    /// The bundle's id.
    fn id(&self) -> &Self::Id;
    /// The family key id: the lineage's name.
    fn family(&self) -> &Self::Id;
    /// The version: the predecessor's plus one.
    fn version(&self) -> u64;
    /// The bundles it extends: none (a first bundle), one, or two (a join).
    fn prev(&self) -> &[Self::Id];
    /// The holders.
    fn holders(&self) -> &[Self::Key];
    /// The seats (serve_nodes).
    fn seats(&self) -> &[Self::Key];
    /// The charter, whole.
    fn charter(&self) -> &Self::Word;
    /// The duties the charter carries (its scope).
    fn duties(&self) -> &[Self::Word];
    /// The duties for which the charter carries sub_delegation.
    fn sub_delegation(&self) -> &[Self::Word] {
        &[]
    }
    /// The bundles it names besides those it extends (rule 3: a bundle at a head naming two siblings decides).
    fn names(&self) -> &[Self::Id] {
        &[]
    }
    /// The recovery commitments: (holder, its recovery key), keys exactly the holders.
    fn recovery(&self) -> &[(Self::Key, Self::Key)];
    /// For a settler at a head: the one contested sibling there it names as the one that stands
    /// ([`Root::bounded_settler`]). Default: none.
    fn settles(&self) -> Option<&Self::Id> {
        None
    }
    /// For a holder's own key recovery: (the holder, its new key).
    fn recovers(&self) -> Option<(&Self::Key, &Self::Key)>;
    /// For a holder's routine rotation by an ordinary counted bundle: (its old key, its new key). The old key is
    /// LEFT: no later bundle seats a holder at it ([`Root::counted`], `holder_key_retired`). Default: none.
    fn rotates(&self) -> Option<(&Self::Key, &Self::Key)> {
        None
    }
    /// The payload's iat.
    fn iat(&self) -> u64;
    /// The statements over the payload: (key, the iat it states), signatures checked by the store.
    fn statements(&self) -> &[(Self::Key, u64)];
}

/// A row of the root's lane, as the store presents it: a root grant (counted over the holders of the bundles it
/// names), or an acceptance edge (whose attached_head_digest names a bundle). The kernel reads each grant's own
/// causal past through these rows' names ([`crate::graph::Graph`]), so the bundles a grant's signers had seen are
/// derived from rows, never stated: a bundle is in a row's past only by being named there. For a row that is no
/// grant, the grant accessors are not read.
pub trait RootGrant: crate::Row {
    /// A duty, as the bundles' words (read as text where a seat names the grant's duty: [`RootView::seat_grant`]).
    type Word: Ord + Clone + AsRef<str>;
    /// The row is a root grant (else an acceptance edge, or another row of the lane).
    fn is_grant(&self) -> bool;
    /// For an acceptance edge: the bundle its attached_head_digest names.
    fn attached_head(&self) -> Option<&Self::Id> {
        None
    }
    /// For a later cosignature of a grant (under the grant's own family and row id, CC 3.3.4): the grant it
    /// cosigns. Its signer ([`crate::Row::signer`]) is the voice it adds.
    fn cosigns(&self) -> Option<&Self::Id> {
        None
    }
    /// The row is a holder's halt (CC 4.2.1): one holder's row that counts nobody, its signer
    /// ([`crate::Row::signer`]) the holder. Default: not a halt.
    fn halts(&self) -> bool {
        false
    }
    /// The bundles a grant names, and is counted over: one, or several.
    fn bundles(&self) -> &[Self::Id];
    /// The key a grant names.
    fn to(&self) -> &Self::Key;
    /// The room a grant's scope names.
    fn scope(&self) -> &Self::Id;
    /// A grant's signers.
    fn signers(&self) -> &[Self::Key];
    /// The duty a grant grants, which the bundles' charters must carry.
    fn duty(&self) -> &Self::Word;
}

/// A revocation of a holder's key: `bound` the last bundle its statements are good on (None: no bound).
#[derive(Clone, Debug)]
pub struct Revocation<I, K> {
    /// The key revoked.
    pub key: K,
    /// The bound.
    pub bound: Option<I>,
}

/// A reader: its anchor (a first bundle's id, or the holders' thumbprints) and the bundles it acknowledged
/// (acceptance edges with attached_head_digest).
#[derive(Clone, Debug)]
pub struct Reader<I: Ord, K: Ord> {
    /// A first bundle's id.
    pub anchor: Option<I>,
    /// The holders' thumbprints.
    pub thumbs: Option<BTreeSet<K>>,
    /// The bundle each of its acknowledgement rows acknowledges, in a causal order (no row before one in its past).
    pub acks: Vec<I>,
    /// Per acknowledgement row, the positions in `acks` of the reader's earlier rows its own causal past names (a
    /// person's devices sign concurrently: two rows neither naming the other). None: one chain, each row with every
    /// earlier one in its past.
    pub after: Option<Vec<Vec<usize>>>,
}

impl<I: Ord, K: Ord> Reader<I, K> {
    /// Per acknowledgement row, the positions of the reader's rows in its own causal past (closed).
    pub fn ack_pasts(&self) -> Vec<BTreeSet<usize>> {
        let mut out: Vec<BTreeSet<usize>> = Vec::new();
        for i in 0..self.acks.len() {
            let direct: Vec<usize> = match &self.after {
                None => (0..i).collect(),
                Some(a) => a.get(i).cloned().unwrap_or_default(),
            };
            let mut got = BTreeSet::new();
            for j in direct.into_iter().filter(|&j| j < i) {
                got.insert(j);
                got.extend(out[j].iter().copied());
            }
            out.push(got);
        }
        out
    }
}

/// Why a bundle or a grant does not stand.
pub type Reason = &'static str;

/// The refusal a detail is a detail of (the Constitution's token table, `manifests/refusal_tokens.tsv`, and CC
/// 2.6.1.11's table of a malformed bundle's details); None for a refusal name.
pub fn detail_of(d: Reason) -> Option<Reason> {
    match d {
        // further_prev_not_newest: a detail, as CIRISVerify returns it (the Constitution's commit after rc23-next
        // 0e80f21; that table still lists it as a refusal of its own: re-pin the table at the tag)
        "version_prev_mismatch"
        | "further_prev_not_newest"
        | "holder_key_retired"
        | "family_key_id_changed"
        | "recovery_commitments_not_holders"
        | "recovery_changes_other_seat" => Some("genesis_bundle_malformed"),
        "recovery_commitment_mismatch" | "recovery_commitment_spent" => Some("genesis_bundle_count_unmet"),
        _ => None,
    }
}

/// One root: its bundles, revocations, and the rows of its lane (grants and acceptance edges).
pub struct Root<'a, B: RootBundle, G: RootGrant> {
    by: BTreeMap<&'a B::Id, &'a B>,
    order: Vec<&'a B::Id>,
    revs: &'a [Revocation<B::Id, B::Key>],
    grants: BTreeMap<&'a B::Id, &'a G>,
    lane: crate::graph::Graph<'a, G>,
    own: BTreeMap<B::Key, B::Key>,
    past_memo: RefCell<BTreeMap<B::Id, BTreeSet<B::Id>>>,
    counted_memo: RefCell<BTreeMap<B::Id, Result<(), Reason>>>,
    void_memo: RefCell<Option<(BTreeSet<B::Id>, BTreeSet<B::Id>)>>,
}

impl<'a, B, G> Root<'a, B, G>
where
    B: RootBundle,
    G: RootGrant<Id = B::Id, Key = B::Key, Word = B::Word>,
{
    /// A root over these bundles, revocations, and rows of its lane (grants and acceptance edges).
    pub fn new(bundles: &'a [B], revs: &'a [Revocation<B::Id, B::Key>], grants: &'a [G]) -> Self {
        Root {
            by: bundles.iter().map(|b| (b.id(), b)).collect(),
            order: bundles.iter().map(|b| b.id()).collect(),
            revs,
            grants: grants.iter().filter(|g| g.is_grant()).map(|g| (g.id(), g)).collect(),
            lane: crate::graph::Graph::new(grants.iter()),
            own: Self::owners_of(bundles),
            past_memo: RefCell::new(BTreeMap::new()),
            counted_memo: RefCell::new(BTreeMap::new()),
            void_memo: RefCell::new(None),
        }
    }

    /// The union of a holder's keys: its key, its recovery key, and the key a recovery seats.
    fn owners_of(bundles: &'a [B]) -> BTreeMap<B::Key, B::Key> {
        let by: BTreeMap<&B::Id, &B> = bundles.iter().map(|b| (b.id(), b)).collect();
        let mut own: BTreeMap<B::Key, B::Key> = BTreeMap::new();
        fn find<K: Ord + Clone>(own: &BTreeMap<K, K>, k: &K) -> K {
            let mut k = k.clone();
            while let Some(n) = own.get(&k) {
                if *n == k {
                    break;
                }
                k = n.clone();
            }
            k
        }
        let union = |own: &mut BTreeMap<B::Key, B::Key>, a: &B::Key, b: &B::Key| {
            let (ra, rb) = (find(own, a), find(own, b));
            if ra != rb {
                let (lo, hi) = if ra < rb { (ra, rb) } else { (rb, ra) };
                own.insert(hi, lo);
            }
        };
        for b in bundles {
            if let Some((h, new)) = b.recovers() {
                if let Some(p) = b.prev().first().filter(|_| b.prev().len() == 1).and_then(|x| by.get(x)) {
                    let rk = Self::commitment(p, h);
                    for k in [Some(new.clone()), rk].into_iter().flatten() {
                        union(&mut own, h, &k);
                    }
                }
            }
            // a routine rotation: the same holder under its new key
            if let Some((old, new)) = b.rotates() {
                union(&mut own, old, new);
            }
        }
        own
    }

    fn b(&self, i: &B::Id) -> Option<&'a B> {
        self.by.get(i).copied()
    }

    // ---- the lineage --------------------------------------------------------------------------------------
    /// The bundles in i's past (by prev), not i.
    pub fn past(&self, i: &B::Id) -> BTreeSet<B::Id> {
        if let Some(p) = self.past_memo.borrow().get(i) {
            return p.clone();
        }
        let mut out = BTreeSet::new();
        if let Some(b) = self.b(i) {
            for p in b.prev() {
                if self.by.contains_key(p) {
                    out.insert(p.clone());
                    out.extend(self.past(p));
                }
            }
        }
        self.past_memo.borrow_mut().insert(i.clone(), out.clone());
        out
    }

    fn line(&self, i: &B::Id) -> BTreeSet<B::Id> {
        let mut l = self.past(i);
        l.insert(i.clone());
        l
    }

    fn in_past(&self, a: &B::Id, b: &B::Id) -> bool {
        self.past(b).contains(a)
    }

    // ---- the count ----------------------------------------------------------------------------------------
    fn unbounded(&self) -> BTreeSet<B::Key> {
        self.revs.iter().filter(|r| r.bound.is_none()).map(|r| r.key.clone()).collect()
    }

    fn live(&self, hs: impl IntoIterator<Item = B::Key>) -> BTreeSet<B::Key> {
        let un = self.unbounded();
        hs.into_iter().filter(|k| !un.contains(k)).collect()
    }

    /// The keys whose statement on b counts: iat agreeing, not voided by a bound.
    fn voices(&self, b: &B) -> BTreeSet<B::Key> {
        let mut out = BTreeSet::new();
        for (k, iat) in b.statements() {
            if *iat != b.iat() {
                continue; // Invalid on its own
            }
            let bounds: Vec<&B::Id> =
                self.revs.iter().filter(|r| &r.key == k).filter_map(|r| r.bound.as_ref()).collect();
            if !bounds.is_empty() && !bounds.iter().any(|x| self.by.contains_key(*x) && self.line(x).contains(b.id())) {
                continue; // after the bound
            }
            out.insert(k.clone());
        }
        out
    }

    /// Why b is Invalid or waits, by the text's tokens (CC 2.6.1.11, CC 3.2), or None: a refusal name, or a detail
    /// ([`detail_of`]), which [`Root::counted`] reports under its refusal name and [`Root::refusal`] gives apart.
    fn inconsistency(&self, b: &B) -> Option<Reason> {
        let ps: Vec<&B> = b.prev().iter().filter_map(|p| self.b(p)).collect();
        if ps.len() != b.prev().len() {
            return Some("waiting"); // one not held: the verdict Waiting, no token ([`Root::waits_on`])
        }
        let rk: BTreeSet<&B::Key> = b.recovery().iter().map(|(h, _)| h).collect();
        let hk: BTreeSet<&B::Key> = b.holders().iter().collect();
        if rk != hk {
            return Some("recovery_commitments_not_holders"); // a detail of genesis_bundle_malformed
        }
        if ps.is_empty() {
            return None;
        }
        let top = ps.iter().map(|p| p.version()).max().unwrap_or(0);
        if b.version() != top + 1 {
            return Some("version_prev_mismatch");
        }
        if !ps.iter().all(|p| p.family() == b.family()) {
            return Some("family_key_id_changed");
        }
        if ps.len() >= 2 {
            // the join's wire: refs.prev is the greatest version, least id among equals; refs.further_prev the
            // rest; a named predecessor in the lineage past of another is Invalid
            let first = ps.iter().min_by(|x, y| (y.version(), x.id()).cmp(&(x.version(), y.id())));
            if first.map(|q| q.id()) != Some(&b.prev()[0]) {
                return Some("version_prev_mismatch");
            }
            if b.prev().iter().any(|a| b.prev().iter().any(|c| self.in_past(a, c))) {
                return Some("further_prev_not_newest");
            }
        }
        // a join inherits the union of its branches, and any later bundle reads its predecessors' lines: a key retired
        // by a counted recovery or left by a routine rotation on any of them stays so; seating a holder at it is
        // Invalid, holder_key_retired. The holder comes back only under a new key
        let retired = self.retired(b.prev());
        let left = self.left(b.prev());
        if b.holders().iter().any(|k| retired.contains(k) || left.contains(k)) {
            return Some("holder_key_retired");
        }
        None
    }

    /// The keys retired across the branches of `prevs`: every key a recovery in their lines rotated out. A join
    /// inherits the union, and revives nothing.
    fn retired(&self, prevs: &[B::Id]) -> BTreeSet<B::Key> {
        let mut out = BTreeSet::new();
        for p in prevs {
            for x in self.line(p) {
                if let Some((h, _)) = self.b(&x).and_then(|q| q.recovers()) {
                    out.insert(h.clone());
                }
            }
        }
        out
    }

    /// The recovery commitments spent across the branches of `prevs`: for each recovery in their lines, the
    /// commitment its predecessor carried for the holder it recovers.
    fn spent(&self, prevs: &[B::Id]) -> BTreeSet<B::Key> {
        let mut out = BTreeSet::new();
        for p in prevs {
            for x in self.line(p) {
                let Some(q) = self.b(&x) else { continue };
                let Some((h, _)) = q.recovers() else { continue };
                if q.prev().len() != 1 {
                    continue;
                }
                if let Some(c) = self.b(&q.prev()[0]).and_then(|pq| Self::commitment(pq, h)) {
                    out.insert(c);
                }
            }
        }
        out
    }

    /// The keys a routine rotation left across the branches of `prevs`: each key a bundle in their lines rotated a
    /// holder away from ([`RootBundle::rotates`]).
    fn left(&self, prevs: &[B::Id]) -> BTreeSet<B::Key> {
        let mut out = BTreeSet::new();
        for p in prevs {
            for x in self.line(p) {
                if let Some((old, _)) = self.b(&x).and_then(|q| q.rotates()) {
                    out.insert(old.clone());
                }
            }
        }
        out
    }

    /// b's count on `voices`: one predecessor, a strict majority of its live holders; a JOIN, a strict majority of
    /// EACH named predecessor's live holders, each voice a key that predecessor seats under the same key, less the
    /// keys retired across its branches, whatever the charters. `within`: only these holders (the fold's).
    fn meets(&self, b: &B, voices: &BTreeSet<B::Key>, within: Option<&BTreeSet<B::Key>>) -> bool {
        let prevs = b.prev();
        if prevs.is_empty() {
            return false;
        }
        let gone = if prevs.len() >= 2 { self.retired(prevs) } else { BTreeSet::new() };
        prevs.iter().all(|p| {
            let Some(q) = self.b(p) else { return false };
            let base: BTreeSet<B::Key> = self
                .live(q.holders().iter().cloned())
                .into_iter()
                .filter(|k| !gone.contains(k) && within.is_none_or(|w| w.contains(k)))
                .collect();
            2 * voices.intersection(&base).count() > base.len()
        // each holder a later bundle adds signs it too, as does each holder whose recovery commitment it changes (CC
        // 2.6.1.11, "How a bundle is counted"; a join reads it over each predecessor)
        }) && self.join_signers(b).iter().all(|(_, ks)| ks.iter().any(|k| voices.contains(k)))
    }

    /// The holders of later bundle `b` (a join or not) that must sign it, each with the keys its statement may be under (CIRISVerify's
    /// per-bundle read, the Constitution's reading 1): a holder no named predecessor seats, under its own key; a
    /// holder whose recovery commitment in `b` differs from the one any named predecessor seating it carries, under
    /// a key some predecessor seats it at and no recovery in the join's branches retired. So after a recovery on one
    /// branch, the join carries the recovered holder's voice. In `b`'s holder order.
    pub fn join_signers(&self, b: &B) -> Vec<(B::Key, BTreeSet<B::Key>)> {
        let prevs = b.prev();
        let gone = self.retired(prevs);
        let mut out = Vec::new();
        for h in b.holders() {
            let at: Vec<(&B, &B::Key)> = prevs
                .iter()
                .filter_map(|p| self.b(p))
                .flat_map(|p| p.holders().iter().filter(|k| self.owner(k) == self.owner(h)).map(move |k| (p, k)))
                .collect();
            if at.is_empty() {
                out.push((h.clone(), BTreeSet::from([h.clone()])));
            } else if at.iter().any(|(p, k)| Self::commitment(p, k) != Self::commitment(b, h)) {
                out.push((h.clone(), at.iter().map(|(_, k)| (*k).clone()).filter(|k| !gone.contains(k)).collect()));
            }
        }
        out
    }

    /// A join contested by a rival: a concluded join of the same predecessors under another charter, neither in
    /// the other's past. Joins that do not fold with each other may not both stand. Two successors of one bundle
    /// are no joins and fold as tips; two joins under the same charter fold as any tips do.
    fn contested_join(&self, i: &B::Id) -> bool {
        let Some(b) = self.b(i) else { return false };
        if b.prev().len() < 2 || self.counted(i).is_err() {
            return false;
        }
        let ps: BTreeSet<&B::Id> = b.prev().iter().collect();
        self.by.values().any(|x| {
            x.id() != i
                && x.prev().len() >= 2
                && x.prev().iter().collect::<BTreeSet<_>>() == ps
                && x.charter() != b.charter()
                && !self.in_past(x.id(), i)
                && !self.in_past(i, x.id())
                && self.counted(x.id()).is_ok()
        })
    }

    /// The live holders whose statements on b are voices: its predecessor's; a join's, each named predecessor's
    /// (the union, less the keys retired across its branches; its count is per predecessor, `meets`).
    fn base(&self, b: &B) -> BTreeSet<B::Key> {
        let ps: Vec<&B> = b.prev().iter().filter_map(|p| self.b(p)).collect();
        match ps.len() {
            0 => BTreeSet::new(),
            1 => self.live(ps[0].holders().iter().cloned()),
            _ => {
                let gone = self.retired(b.prev());
                self.live(ps.iter().flat_map(|p| p.holders().iter().cloned()))
                    .into_iter()
                    .filter(|k| !gone.contains(k))
                    .collect()
            }
        }
    }

    fn commitment(p: &B, h: &B::Key) -> Option<B::Key> {
        p.recovery().iter().find(|(x, _)| x == h).map(|(_, r)| r.clone())
    }

    /// A holder's own key recovery: None where b is none.
    fn recovery_ok(&self, b: &B) -> Option<Result<(), Reason>> {
        let (h, new) = b.recovers()?;
        if b.prev().len() != 1 {
            return Some(Err("recovery_changes_other_seat"));
        }
        let p = self.b(&b.prev()[0])?;
        let Some(rk) = Self::commitment(p, h) else { return Some(Err("recovery_commitment_mismatch")) };
        if !b.statements().iter().any(|(k, iat)| *k == rk && *iat == b.iat()) {
            return Some(Err("recovery_commitment_mismatch"));
        }
        // a recovery behind a bundle its holder signed (as a holder, under either key; `behind`: its prev strictly in
        // the past of what that bundle extends, so a sibling on the same predecessor is a fork, both valid) concludes
        // nothing
        let behind_head = self.by.values().any(|x| {
            x.id() != b.id()
                && !self.in_past(b.id(), x.id())
                && x.recovers().is_none()
                && self.behind(b, x)
                && x.statements().iter().any(|(k, _)| self.owner(k) == self.owner(h))
        });
        if behind_head {
            return Some(Err("recovery_behind_head"));
        }
        let want: Vec<B::Key> = p.holders().iter().map(|k| if k == h { new.clone() } else { k.clone() }).collect();
        let others = |r: &[(B::Key, B::Key)], skip: &B::Key| -> BTreeSet<(B::Key, B::Key)> {
            r.iter().filter(|(k, _)| k != skip).cloned().collect()
        };
        let same = b.holders() == want.as_slice()
            && b.seats() == p.seats()
            && b.charter() == p.charter()
            && others(b.recovery(), new) == others(p.recovery(), h);
        if !same {
            return Some(Err("recovery_changes_other_seat"));
        }
        for x in self.past(b.id()) {
            let q = self.b(&x)?;
            if let Some((qh, _)) = q.recovers() {
                if self.b(&q.prev()[0]).and_then(|qp| Self::commitment(qp, qh)).as_ref() == Some(&rk) {
                    return Some(Err("recovery_commitment_spent"));
                }
            }
        }
        Some(Ok(()))
    }

    /// The bundle's own count, its predecessors concluded; refused, the refusal NAME (the detail, where the token
    /// table gives the refusal one, is [`Root::refusal`]'s).
    pub fn counted(&self, i: &B::Id) -> Result<(), Reason> {
        self.counted_raw(i).map_err(|why| detail_of(why).unwrap_or(why))
    }

    /// The predecessors bundle `i` names that are not held: it is Waiting on them (CC 2.6.1.11, the order of
    /// verification, step 3). Empty where it waits on none; [`Root::counted`] gives `waiting` (the verdict, no token).
    pub fn waits_on(&self, i: &B::Id) -> Vec<B::Id> {
        self.b(i).map(|b| b.prev().iter().filter(|p| self.b(p).is_none()).cloned().collect()).unwrap_or_default()
    }

    /// None where bundle `i` counts; else its refusal name and its detail, the detail None where the refusal carries
    /// none: a malformed bundle's (`genesis_bundle_malformed`, `version_prev_mismatch`), a recovery's statement that
    /// does not count (`genesis_bundle_count_unmet`, `recovery_commitment_mismatch`), as the Constitution's token
    /// table names them; `further_prev_not_newest` and `holder_key_retired` are details of the malformed bundle.
    pub fn refusal(&self, i: &B::Id) -> Option<(Reason, Option<Reason>)> {
        let why = self.counted_raw(i).err()?;
        Some(match detail_of(why) {
            Some(name) => (name, Some(why)),
            None => (why, None),
        })
    }

    fn counted_raw(&self, i: &B::Id) -> Result<(), Reason> {
        if let Some(c) = self.counted_memo.borrow().get(i) {
            return *c;
        }
        self.counted_memo.borrow_mut().insert(i.clone(), Err("cycle"));
        let out = match self.b(i) {
            None => Err("unknown"),
            Some(b) => self.counted_of(b),
        };
        self.counted_memo.borrow_mut().insert(i.clone(), out);
        out
    }

    fn counted_of(&self, b: &B) -> Result<(), Reason> {
        if let Some(why) = self.inconsistency(b) {
            return Err(why);
        }
        if b.prev().iter().any(|p| self.counted(p).is_err()) {
            return Err("genesis_bundle_prev_not_valid");
        }
        let v = self.voices(b);
        if b.prev().is_empty() {
            let all = !b.holders().is_empty() && b.holders().iter().all(|k| v.contains(k));
            return if all { Ok(()) } else { Err("genesis_bundle_count_unmet") };
        }
        if let Some(r) = self.recovery_ok(b) {
            return r;
        }
        // a recovery commitment spent on any branch stays so: a later bundle (a join included) carrying it for a holder
        // concludes nothing, genesis_bundle_count_unmet with the detail recovery_commitment_spent
        let spent = self.spent(b.prev());
        if b.recovery().iter().any(|(_, c)| spent.contains(c)) {
            return Err("recovery_commitment_spent");
        }
        if self.bounded_settler(b) {
            // the bounded settler (the ruling on the genesis stall): counted over the head's holders who have a say
            // there, rule 6's double signers at that head (over the siblings it names) out of the base for this one
            // count, by strict majority of them. Each sibling it can choose was already signed by a strict
            // majority, so the reduced base only decides which majority-signed bundle stands, and a holder cannot be
            // made a double signer against its will. Every holder double-signed: an empty base, nothing settles.
            // Its target must be one of the CONTESTED siblings at that head that concluded on its own count, else it
            // concludes nothing (a target that did not conclude would wipe the head).
            let kids = self.head_successors(b.prev());
            let target = b.settles().and_then(|x| kids.iter().copied().find(|k| k.id() == x));
            let Some(x) = target else { return Err("genesis_bundle_count_unmet") };
            if !kids.iter().any(|c| self.siblings(x, c) && (self.cuts_kept(x, c) || self.cuts_kept(c, x))) {
                return Err("genesis_bundle_count_unmet");
            }
            // the double signers at that head, over every successor there that concluded (one base per head: two
            // settlers toward different siblings cannot both conclude, whatever order they are read in)
            let ds = self.double_signers(&kids);
            let p: BTreeSet<B::Id> = b.prev().iter().cloned().collect();
            let none = BTreeSet::new();
            let mut d: BTreeSet<B::Key> = ds.get(&p).unwrap_or(&none).clone();
            d.extend(self.settler_double_signers(b.prev()));
            let head = self.b(&b.prev()[0]).map(|h| h.holders().to_vec()).unwrap_or_default();
            let base: BTreeSet<B::Key> = self.live(head).into_iter().filter(|k| !d.contains(&self.owner(k))).collect();
            return if !base.is_empty() && self.meets(b, &v, Some(&base)) {
                Ok(())
            } else {
                Err("genesis_bundle_count_unmet")
            };
        }
        if self.meets(b, &v, None) {
            Ok(())
        } else {
            Err("genesis_bundle_count_unmet")
        }
    }

    /// Rule 6 read over settlers: the holders (owner classes) that signed two bounded settlers at head `prev` naming
    /// different siblings. Such a holder has no say in settling that head: both its settler signatures count for
    /// nothing.
    /// The successors at head `prev` that concluded on their own count, settlers apart, in id order.
    fn head_successors(&self, prev: &[B::Id]) -> Vec<&'a B> {
        self.by
            .values()
            .copied()
            .filter(|x| x.prev() == prev && !self.bounded_settler(x) && self.counted(x.id()).is_ok())
            .collect()
    }

    fn settler_double_signers(&self, prev: &[B::Id]) -> BTreeSet<B::Key> {
        let ss: Vec<&B> = self.by.values().copied().filter(|x| x.prev() == prev && self.bounded_settler(x)).collect();
        let mut out = BTreeSet::new();
        for a in &ss {
            for c in &ss {
                if a.settles() != c.settles() {
                    let oc: BTreeSet<B::Key> = self.voices(c).iter().map(|k| self.owner(k)).collect();
                    out.extend(self.voices(a).iter().map(|k| self.owner(k)).filter(|k| oc.contains(k)));
                }
            }
        }
        out
    }

    /// A settler at a head that names one contested sibling there ([`RootBundle::settles`]) as the one that stands
    /// and states nothing of its own: its holders, seats, charter and recovery commitments are that sibling's. One
    /// stating anything else is counted over the full base, as any bundle is.
    pub fn bounded_settler(&self, b: &B) -> bool {
        let Some(x) = b.settles().and_then(|x| self.b(x)) else { return false };
        // it states something of its own: holders, seats, charter or recovery commitments not the sibling's
        let states = x.holders() != b.holders()
            || x.seats() != b.seats()
            || x.charter() != b.charter()
            || x.recovery() != b.recovery();
        b.prev().len() == 1 && x.prev() == b.prev() && b.names().contains(x.id()) && !states
    }

    fn concluded(&self) -> Vec<&'a B> {
        self.order.iter().filter(|i| self.counted(i).is_ok()).filter_map(|i| self.b(i)).collect()
    }

    // ---- S'' and T on a forked bundle ----------------------------------------------------------------------
    /// b is behind c: every bundle b extends is strictly in the past of a bundle c extends, b not in c's past.
    fn behind(&self, b: &B, c: &B) -> bool {
        if c.id() == b.id() || self.in_past(b.id(), c.id()) || b.prev().is_empty() {
            return false;
        }
        let mut cp: BTreeSet<B::Id> = BTreeSet::new();
        for p in c.prev() {
            cp.extend(self.line(p));
        }
        b.prev().iter().all(|p| cp.contains(p) && !c.prev().contains(p))
    }

    /// The holder a key speaks for: a holder's key, its recovery key, and the key a recovery seats are one voice.
    fn owner(&self, k: &B::Key) -> B::Key {
        let mut k = k.clone();
        while let Some(n) = self.own.get(&k) {
            if *n == k {
                break;
            }
            k = n.clone();
        }
        k
    }

    fn owners<'k>(&self, ks: impl IntoIterator<Item = &'k B::Key>) -> BTreeSet<B::Key>
    where
        B::Key: 'k,
    {
        ks.into_iter().map(|k| self.owner(k)).collect()
    }

    /// b's counted voices, as the holders they speak for: a recovery's is the recovering holder.
    fn voices_of(&self, b: &B) -> BTreeSet<B::Key> {
        if let Some((h, _)) = b.recovers() {
            return BTreeSet::from([self.owner(h)]);
        }
        let base: BTreeSet<B::Key> =
            if b.prev().is_empty() { b.holders().iter().cloned().collect() } else { self.base(b) };
        self.owners(self.voices(b).intersection(&base))
    }

    /// Why bundle `i` is void, where it is: `genesis_join_contested` for a join a rival under another charter
    /// contests (the text's report token, CC 3.2), `void` otherwise; None where it is not void.
    pub fn void_reason(&self, i: &B::Id) -> Option<Reason> {
        if !self.void().contains(i) {
            return None;
        }
        Some(if self.contested_join(i) { "genesis_join_contested" } else { "void" })
    }

    /// S'' and T: the bundles void (and contested recoveries).
    pub fn void(&self) -> BTreeSet<B::Id> {
        self.void_and_contested().0
    }

    /// The void, and of it the contested bundles (a forked join's joins, a double recovery's recoveries), which
    /// leave a reader that acknowledged them at the bundles they extend.
    fn void_and_contested(&self) -> (BTreeSet<B::Id>, BTreeSet<B::Id>) {
        if let Some(v) = self.void_memo.borrow().as_ref() {
            return v.clone();
        }
        let v = self.void_of();
        *self.void_memo.borrow_mut() = Some(v.clone());
        v
    }

    /// Built on: void, but a join: a join is judged by its own count (a strict majority of each named predecessor's
    /// live holders) and its payload states its holders, seats and charter outright, so a void predecessor it names
    /// does not stop it and is not revived.
    fn close(&self, cs: &[&'a B], tv: &mut BTreeSet<B::Id>) {
        loop {
            let mut changed = false;
            for c in cs {
                if tv.contains(c.id()) || !c.prev().iter().any(|p| tv.contains(p)) {
                    continue;
                }
                if c.prev().len() >= 2 {
                    continue; // a join is judged by its own count, and heals the fork
                }
                tv.insert(c.id().clone());
                changed = true;
            }
            if !changed {
                break;
            }
        }
    }

    fn void_of(&self) -> (BTreeSet<B::Id>, BTreeSet<B::Id>) {
        let mut contest: BTreeSet<B::Id> = BTreeSet::new();
        let cs = self.concluded();
        let forked = |b: &B| {
            let first = b.prev().is_empty(); // a recovery is no exemption
                                             // a bounded settler states nothing of its own: it decides its head, and is no fork of the lines on it
            if first || self.bounded_settler(b) {
                return false;
            }
            let v = self.voices_of(b);
            !v.is_empty()
                && v.iter().all(|k| cs.iter().any(|c| self.owners(&self.voices(c)).contains(k) && self.behind(b, c)))
        };
        let out: Vec<&B> = cs.iter().copied().filter(|b| forked(b)).collect();
        let mut tv: BTreeSet<B::Id> = BTreeSet::new();
        for b in &out {
            let i = b.id();
            let mem = self.owners(&self.base(b));
            let beh: Vec<&B> = cs.iter().copied().filter(|c| self.behind(b, c)).collect();
            let fp = self.line(&b.prev()[0]);
            let mut chain: BTreeSet<B::Id> = BTreeSet::new();
            let mut todo: Vec<B::Id> = beh.iter().map(|c| c.id().clone()).collect();
            while let Some(x) = todo.pop() {
                if chain.contains(&x) || fp.contains(&x) || !self.by.contains_key(&x) {
                    continue;
                }
                todo.extend(self.b(&x).map(|q| q.prev().to_vec()).unwrap_or_default());
                chain.insert(x);
            }
            let mut km: BTreeSet<B::Key> = BTreeSet::new();
            let mut ko: BTreeSet<B::Key> = BTreeSet::new();
            for c in &cs {
                let pc = self.past(c.id());
                let mine = (c.id() == i || pc.contains(i)) && !beh.iter().any(|x| pc.contains(x.id()));
                let other = c.id() != i
                    && !pc.contains(i)
                    && (chain.contains(c.id()) || beh.iter().any(|x| pc.contains(x.id())));
                let vs: BTreeSet<B::Key> = self.voices_of(c).intersection(&mem).cloned().collect();
                if mine {
                    km.extend(vs);
                } else if other {
                    ko.extend(vs);
                }
            }
            if ko.difference(&km).count() > km.difference(&ko).count() {
                tv.insert(i.clone());
            }
        }
        self.close(&cs, &mut tv);
        // two recoveries of one seat, neither in the other's past: settled by T between them (of the live holders at
        // their predecessor, those who built only on one recovery's line); short of the most, void; a tie at the
        // most is contested, and neither replaces the seat until a bundle names both
        let recs: Vec<&B> = cs.iter().copied().filter(|c| c.recovers().is_some() && !tv.contains(c.id())).collect();
        let seat = |c: &B| (c.prev()[0].clone(), c.recovers().map(|(h, _)| h.clone()));
        let mut groups: BTreeMap<(B::Id, Option<B::Key>), BTreeSet<B::Id>> = BTreeMap::new();
        for c in &recs {
            let rivals: Vec<B::Id> = recs
                .iter()
                .filter(|x| {
                    x.id() != c.id()
                        && seat(x) == seat(c)
                        && !self.in_past(x.id(), c.id())
                        && !self.in_past(c.id(), x.id())
                })
                .map(|x| x.id().clone())
                .collect();
            if !rivals.is_empty() {
                let g = groups.entry(seat(c)).or_default();
                g.extend(rivals);
                g.insert(c.id().clone());
            }
        }
        for ((pv, _), g) in &groups {
            if cs.iter().any(|c| !tv.contains(c.id()) && g.is_subset(&self.past(c.id()))) {
                continue; // a bundle names both
            }
            let mem = self.owners(&self.live(self.b(pv).map(|b| b.holders().to_vec()).unwrap_or_default()));
            let mut side: BTreeMap<B::Id, BTreeSet<B::Key>> = BTreeMap::new();
            for r in g {
                let mut ks = BTreeSet::new();
                for x in &cs {
                    let line = self.line(x.id());
                    if line.contains(r) && !g.iter().any(|q| q != r && line.contains(q)) {
                        ks.extend(self.voices_of(x).intersection(&mem).cloned());
                    }
                }
                side.insert(r.clone(), ks);
            }
            let only: BTreeMap<B::Id, usize> = g
                .iter()
                .map(|r| {
                    let others: BTreeSet<B::Key> =
                        g.iter().filter(|q| *q != r).flat_map(|q| side[q].iter().cloned()).collect();
                    (r.clone(), side[r].difference(&others).count())
                })
                .collect();
            let top = only.values().copied().max().unwrap_or(0);
            let tied: BTreeSet<B::Id> = g.iter().filter(|r| only[*r] == top).cloned().collect();
            for r in g {
                if only[r] < top {
                    tv.insert(r.clone()); // short of the most: void
                }
            }
            if tied.len() < 2 {
                continue;
            }
            for c in &cs {
                let line = self.line(c.id());
                if !line.is_disjoint(&tied) && !tied.is_subset(&line) {
                    tv.insert(c.id().clone());
                    if tied.contains(c.id()) {
                        contest.insert(c.id().clone());
                    }
                }
            }
        }
        self.close(&cs, &mut tv);
        // a forked join: joins of the same tips under different charters are contested, neither stands, and a reader
        // keeps the tips they tried to join; a bundle naming every one settles them (counted over those tips' fold,
        // own count, each named join's majority); one built on some and not all is void with them
        let mut jgroups: BTreeMap<BTreeSet<B::Id>, BTreeSet<B::Id>> = BTreeMap::new();
        for c in &cs {
            if self.contested_join(c.id()) {
                jgroups.entry(c.prev().iter().cloned().collect()).or_default().insert(c.id().clone());
            }
        }
        loop {
            let mut changed = false;
            for g in jgroups.values() {
                if cs.iter().any(|c| !tv.contains(c.id()) && g.is_subset(&self.past(c.id()))) {
                    continue; // settled
                }
                for c in &cs {
                    let line = self.line(c.id());
                    if !tv.contains(c.id()) && !line.is_disjoint(g) && (g.contains(c.id()) || !g.is_subset(&line)) {
                        tv.insert(c.id().clone());
                        changed = true;
                        if g.contains(c.id()) {
                            contest.insert(c.id().clone());
                        }
                    }
                }
            }
            if !changed {
                break;
            }
        }
        self.close(&cs, &mut tv);
        (tv, contest)
    }

    // ---- for one reader ----------------------------------------------------------------------------------
    fn valid(&self) -> Vec<&'a B> {
        let v = self.void();
        self.concluded().into_iter().filter(|b| !v.contains(b.id())).collect()
    }

    /// The reader's first bundle; None: `genesis_bundle_not_anchored`. Its anchor by id names that first bundle;
    /// by the holders' thumbprints, the one first bundle whose holders they are: two or more that match give
    /// neither (CIRISVerify v23.8.0).
    pub fn first(&self, rd: &Reader<B::Id, B::Key>) -> Option<B::Id> {
        let firsts: Vec<&B::Id> = self.valid().into_iter().filter(|b| b.prev().is_empty()).map(|b| b.id()).collect();
        if let Some(a) = rd.anchor.as_ref().filter(|a| firsts.contains(a)) {
            return Some(a.clone());
        }
        let t = rd.thumbs.as_ref()?;
        let m: Vec<&B::Id> = firsts
            .into_iter()
            .filter(|i| self.b(i).is_some_and(|b| b.holders().iter().cloned().collect::<BTreeSet<_>>() == *t))
            .collect();
        (m.len() == 1).then(|| m[0].clone())
    }

    /// The reader's own line, and the bundles void for the reader by it. Its acknowledgements are its own rows, each
    /// later one with the earlier ones in its past ([`Reader::acks`], in that causal order); an acknowledgement
    /// settles only if the acknowledged bundle counts over that acknowledgement row's OWN PAST (the bundle's past, the
    /// reader's earlier acknowledgement rows and the line they drew). The void: every bundle behind ANY settled
    /// bundle, a settled one included, and every bundle built on one but a join (a join is behind an acknowledged c only where every predecessor it names is
    /// strictly in the past of c's heads; a void predecessor it names does not stop it). Acknowledging never
    /// revives.
    pub fn reader_line(&self, rd: &Reader<B::Id, B::Key>) -> (Vec<B::Id>, BTreeSet<B::Id>) {
        let valid: BTreeSet<B::Id> = self.valid().into_iter().map(|b| b.id().clone()).collect();
        // each row judged over its OWN causal past; two concurrent rows (a person's two devices) each without the
        // other, and the reader's line drawn over their union
        let pasts = rd.ack_pasts();
        let mut won: BTreeMap<usize, B::Id> = BTreeMap::new();
        // what the bundles settled at `rows` close among `ids`: each closes what is behind it, a bundle settled by a
        // row not in its own row's past apart (a row closes nothing a row concurrent with it settled, so depth between
        // a person's two devices decides nothing)
        let closes = |won: &BTreeMap<usize, B::Id>, rows: &mut dyn Iterator<Item = usize>, ids: &BTreeSet<B::Id>| {
            let mut out = BTreeSet::new();
            for j in rows {
                let Some(a) = won.get(&j) else { continue };
                // a concurrent row's settled bundle and its whole line: the line it settled onto
                let keep: BTreeSet<B::Id> = won
                    .iter()
                    .filter(|(m, _)| **m != j && !pasts[j].contains(*m))
                    .flat_map(|(_, x)| self.line(x))
                    .collect();
                out.extend(self.rv_of(core::slice::from_ref(a), ids, &keep));
            }
            out
        };
        for (i, a) in rd.acks.iter().enumerate() {
            if !valid.contains(a) {
                continue;
            }
            let mut seen: BTreeSet<B::Id> = self.line(a).into_iter().collect();
            for &j in &pasts[i] {
                if valid.contains(&rd.acks[j]) {
                    seen.extend(self.line(&rd.acks[j]));
                }
            }
            let pool: BTreeSet<B::Id> = seen.intersection(&valid).cloned().collect();
            let rv = closes(&won, &mut pasts[i].iter().copied(), &pool);
            let rest: Vec<B::Id> = pool.iter().filter(|x| !rv.contains(*x)).cloned().collect();
            if !rv.contains(a) && !self.contested(&rest).contains(a) {
                won.insert(i, a.clone()); // it counts over its own acknowledgement row's past: it settles
            }
        }
        let settled: Vec<B::Id> = won.values().cloned().collect();
        let out = closes(&won, &mut won.keys().copied(), &valid);
        (settled, out)
    }

    /// The bundles of `ids` behind any of the bundles `settled`, and every bundle built on one but a join; `keep`
    /// (bundles a concurrent row of the reader settled) apart.
    fn rv_of(&self, settled: &[B::Id], ids: &BTreeSet<B::Id>, keep: &BTreeSet<B::Id>) -> BTreeSet<B::Id> {
        // A bounded settler states nothing of its own and decides its head: a line closes it exactly when the sibling
        // it names is one that line holds void. So it rescues a stalled reader and never overturns a reader that
        // already settled past the contest.
        let st: BTreeSet<B::Id> =
            ids.iter().filter(|i| self.b(i).is_some_and(|b| self.bounded_settler(b))).cloned().collect();
        let mut rest: BTreeSet<B::Id> = ids.difference(&st).cloned().collect();
        rest.extend(st.iter().filter_map(|i| self.b(i).and_then(|b| b.settles()).cloned()));
        let mut out: BTreeSet<B::Id> = rest
            .iter()
            .filter(|i| {
                !keep.contains(*i)
                    && self
                        .b(i)
                        .is_some_and(|bi| settled.iter().any(|a| self.b(a).is_some_and(|ba| self.behind(bi, ba))))
            })
            .cloned()
            .collect();
        loop {
            let mut changed = false;
            for i in &rest {
                if out.contains(i) || keep.contains(i) {
                    continue;
                }
                if self.b(i).is_some_and(|b| b.prev().len() < 2 && b.prev().iter().any(|p| out.contains(p))) {
                    out.insert(i.clone());
                    changed = true;
                }
            }
            if !changed {
                break;
            }
        }
        for i in &st {
            if self.b(i).and_then(|b| b.settles()).is_some_and(|x| out.contains(x)) {
                out.insert(i.clone());
            }
        }
        out.intersection(ids).cloned().collect()
    }

    /// The bundles in force for the reader: the newest it acknowledged, read by its line; none, its anchor.
    /// None: `genesis_bundle_not_anchored`.
    pub fn heads(&self, rd: &Reader<B::Id, B::Key>) -> Option<Vec<B::Id>> {
        let f = self.first(rd)?;
        let (accepted, rv) = self.reader_line(rd);
        let base = self.lineage_base(rd)?;
        // rules 5 and 6 over what the reader's line leaves (a row void by the line is no input to them)
        let ct = self.contested(&base);
        let held: BTreeSet<B::Id> = base.into_iter().filter(|i| !ct.contains(i)).collect();
        let mut acked: BTreeSet<B::Id> = held.iter().filter(|i| accepted.contains(*i)).cloned().collect();
        // a bundle the reader acknowledged that does not count for it (contested, or held void by its own line)
        // leaves it at the bundles it extends, and so on down
        let mut down = self.void_and_contested().1;
        down.extend(ct.iter().cloned());
        down.extend(rd.acks.iter().filter(|a| rv.contains(*a)).cloned());
        let mut todo: Vec<B::Id> = rd.acks.iter().filter(|i| down.contains(*i)).cloned().collect();
        while let Some(x) = todo.pop() {
            for p in self.b(&x).map(|b| b.prev().to_vec()).unwrap_or_default() {
                if held.contains(&p) {
                    acked.insert(p);
                } else if down.contains(&p) {
                    todo.push(p);
                }
            }
        }
        // a bounded settler is no head of its own: the reader is at the sibling it names
        let acked: BTreeSet<B::Id> = acked
            .into_iter()
            .map(|i| match self.b(&i) {
                Some(b) if self.bounded_settler(b) => b.settles().cloned().unwrap_or(i),
                _ => i,
            })
            .collect();
        if acked.is_empty() {
            return Some(Vec::from([f]));
        }
        Some(acked.iter().filter(|i| !acked.iter().any(|j| self.in_past(i, j))).cloned().collect())
    }

    /// The bundles of the reader's anchored lineage its line does not hold void: the input to rules 5 and 6.
    fn lineage_base(&self, rd: &Reader<B::Id, B::Key>) -> Option<Vec<B::Id>> {
        let f = self.first(rd)?;
        let (_, rv) = self.reader_line(rd);
        Some(
            self.valid()
                .into_iter()
                .map(|b| b.id().clone())
                .filter(|i| (*i == f || self.in_past(&f, i)) && !rv.contains(i))
                .collect(),
        )
    }

    /// RULE 6's double signers, per head: the head (a successor's prev, as a set) to the holders (owner classes, so
    /// under either key) that signed two successors of it, one cutting a holder the other keeps, neither naming the
    /// other; over the bundles `bs` a reader holds.
    fn double_signers(&self, bs: &[&B]) -> BTreeMap<BTreeSet<B::Id>, BTreeSet<B::Key>> {
        let mut out: BTreeMap<BTreeSet<B::Id>, BTreeSet<B::Key>> = BTreeMap::new();
        for b in bs {
            for c in bs {
                if self.siblings(b, c) && (self.cuts_kept(b, c) || self.cuts_kept(c, b)) {
                    // the holder is the voice, under its key or its recovery key
                    let oc: BTreeSet<B::Key> = self.voices(c).iter().map(|k| self.owner(k)).collect();
                    let ks: Vec<B::Key> =
                        self.voices(b).iter().map(|k| self.owner(k)).filter(|k| oc.contains(k)).collect();
                    out.entry(b.prev().iter().cloned().collect()).or_default().extend(ks);
                }
            }
        }
        out
    }

    /// The holders (owner classes) with no say in any count at the reader's heads in force: rule 6's double signers
    /// at those heads, over what the reader holds. Only at that head: at a later head where the signer did not
    /// double-sign, it counts as any holder (nothing is carried forward as a mark on the key).
    pub fn no_say(&self, rd: &Reader<B::Id, B::Key>) -> BTreeSet<B::Key> {
        let (Some(hs), Some(base)) = (self.heads(rd), self.lineage_base(rd)) else { return BTreeSet::new() };
        let hs: BTreeSet<B::Id> = hs.into_iter().collect();
        let bs: Vec<&B> = base.iter().filter_map(|i| self.b(i)).collect();
        self.double_signers(&bs).into_iter().filter(|(p, _)| p.is_subset(&hs)).flat_map(|(_, ks)| ks).collect()
    }

    /// b and c extend the same bundles, neither in the other's past, and neither names the other.
    fn siblings(&self, b: &B, c: &B) -> bool {
        b.id() != c.id()
            && !b.prev().is_empty()
            && b.prev().iter().collect::<BTreeSet<_>>() == c.prev().iter().collect::<BTreeSet<_>>()
            && !self.in_past(b.id(), c.id())
            && !self.in_past(c.id(), b.id())
            && !c.names().contains(b.id())
            && !b.names().contains(c.id())
    }

    /// b removes holder k: a predecessor seats k, and b does not.
    fn removes(&self, b: &B, k: &B::Key) -> bool {
        !b.holders().contains(k) && b.prev().iter().any(|p| self.b(p).is_some_and(|q| q.holders().contains(k)))
    }

    fn cuts_kept(&self, b: &B, c: &B) -> bool {
        self.b(&b.prev()[0]).is_some_and(|p| p.holders().iter().any(|k| self.removes(b, k) && c.holders().contains(k)))
    }

    /// Of the bundles `ids`, the ones that do not count. RULE 6: on one slot at one head, a voice that acknowledged
    /// an act and voted to cut it, in two rows neither of which names the other, has no say there and stays among the
    /// holders the count is over (a key that signed two siblings, one cutting a holder the other keeps). RULE 5:
    /// siblings that each remove a holder whose voice the other needs are contested; one-sided, the dependent one
    /// falls. And every bundle built on one but a join. RULE 3: a bundle at that head naming both decides.
    pub fn contested(&self, ids: &[B::Id]) -> BTreeSet<B::Id> {
        // a total order: nothing may depend on the order the caller lists the bundles in
        let ids: Vec<B::Id> = ids.iter().cloned().collect::<BTreeSet<_>>().into_iter().collect();
        let ids = &ids[..];
        let bs: Vec<&'a B> = ids.iter().filter_map(|i| self.b(i)).filter(|b| !b.prev().is_empty()).collect();
        let mut out: BTreeSet<B::Id> = BTreeSet::new();
        let mut no: BTreeMap<B::Id, BTreeSet<B::Key>> = BTreeMap::new();
        // rule 6: a double signer at a head has no say in ANY count at that head: the two successors it signed, a
        // third, and a rule-3 bundle naming both
        let ds = self.double_signers(&bs);
        let none = BTreeSet::new();
        for b in &bs {
            if self.bounded_settler(b) {
                no.insert(b.id().clone(), BTreeSet::new()); // counted by its own rule
                continue;
            }
            let p: BTreeSet<B::Id> = b.prev().iter().cloned().collect();
            let d = ds.get(&p).unwrap_or(&none);
            let ks: BTreeSet<B::Key> = self.voices(b).into_iter().filter(|k| d.contains(&self.owner(k))).collect();
            if !ks.is_empty() {
                let v: BTreeSet<B::Key> = self.voices(b).difference(&ks).cloned().collect();
                if b.recovers().is_some() || !self.meets(b, &v, None) {
                    out.insert(b.id().clone());
                }
            }
            no.insert(b.id().clone(), ks);
        }
        // rule 5
        let live: Vec<&'a B> =
            bs.iter().copied().filter(|b| !out.contains(b.id()) && !self.bounded_settler(b)).collect();
        let needs = |y: &B, k: &B::Key| {
            let v: BTreeSet<B::Key> = self.voices(y).difference(&no[y.id()]).cloned().collect();
            let mut less = v.clone();
            less.remove(k);
            v.contains(k) && self.meets(y, &v, None) && !self.meets(y, &less, None)
        };
        let mut dep: Vec<B::Id> = Vec::new();
        for x in &live {
            for y in &live {
                if self.siblings(x, y)
                    && self
                        .b(&x.prev()[0])
                        .is_some_and(|p| p.holders().iter().any(|k| self.removes(x, k) && needs(y, k)))
                {
                    dep.push(y.id().clone());
                }
            }
        }
        out.extend(dep);
        // a bounded settler held (it concluded) decides its head: the sibling it names stands, the others at that head
        // fall (and what is built on them)
        for b in &bs {
            if !self.bounded_settler(b) || out.contains(b.id()) {
                continue;
            }
            let Some(x) = b.settles().and_then(|x| self.b(x)) else { continue };
            out.remove(x.id());
            for c in &bs {
                if c.id() != x.id() && c.id() != b.id() && self.siblings(x, c) && !self.bounded_settler(c) {
                    out.insert(c.id().clone());
                }
            }
        }
        loop {
            let mut changed = false;
            for i in ids {
                if out.contains(i) {
                    continue;
                }
                if let Some(b) = self.b(i) {
                    if b.prev().len() < 2 && b.prev().iter().any(|p| out.contains(p)) {
                        out.insert(i.clone());
                        changed = true;
                    }
                }
            }
            if !changed {
                break;
            }
        }
        out
    }

    /// (holders, seats) in force for the reader; None: `genesis_bundle_not_anchored`.
    pub fn in_force(&self, rd: &Reader<B::Id, B::Key>) -> Option<(BTreeSet<B::Key>, BTreeSet<B::Key>)> {
        let hs = self.heads(rd)?;
        Some(self.fold(&hs))
    }

    // ---- the fold ----------------------------------------------------------------------------------------
    /// The holders and seats at the tips: one tip, its own; several, the guarded fold; charters differing, those
    /// common to them.
    pub fn fold(&self, tips: &[B::Id]) -> (BTreeSet<B::Key>, BTreeSet<B::Key>) {
        let bs: Vec<&B> = tips.iter().filter_map(|t| self.b(t)).collect();
        let set = |x: &[B::Key]| x.iter().cloned().collect::<BTreeSet<B::Key>>();
        if bs.len() == 1 {
            return (set(bs[0].holders()), set(bs[0].seats()));
        }
        let common = |f: &dyn Fn(&B) -> &[B::Key]| {
            let mut it = bs.iter();
            let mut c = it.next().map(|b| set(f(b))).unwrap_or_default();
            for b in it {
                c = c.intersection(&set(f(b))).cloned().collect();
            }
            c
        };
        let holders: &dyn Fn(&B) -> &[B::Key] = &holders_of::<B>;
        let seats: &dyn Fn(&B) -> &[B::Key] = &seats_of::<B>;
        let ch = common(holders);
        let cs = common(seats);
        let charters: BTreeSet<&B::Word> = bs.iter().map(|b| b.charter()).collect();
        if charters.len() > 1 {
            return (ch, cs); // tips whose charters differ wait
        }
        let h = self.fold_field(tips, holders, &ch, None);
        let s = self.fold_field(tips, seats, &cs, Some(&h));
        (h, s)
    }

    fn adding(&self, t: &B::Id, k: &B::Key, field: &dyn Fn(&B) -> &[B::Key]) -> Vec<B::Id> {
        self.line(t)
            .into_iter()
            .filter(|i| {
                self.b(i).is_some_and(|b| {
                    field(b).contains(k)
                        && (b.prev().is_empty()
                            || b.prev().iter().all(|p| self.b(p).is_some_and(|q| !field(q).contains(k))))
                })
            })
            .collect()
    }

    fn removals(&self, t: &B::Id, k: &B::Key, field: &dyn Fn(&B) -> &[B::Key]) -> Vec<B::Id> {
        self.line(t)
            .into_iter()
            .filter(|i| {
                self.b(i).is_some_and(|b| {
                    !b.prev().is_empty()
                        && !field(b).contains(k)
                        && b.prev().iter().any(|p| self.b(p).is_some_and(|q| field(q).contains(k)))
                })
            })
            .collect()
    }

    fn fold_field(
        &self,
        tips: &[B::Id],
        field: &dyn Fn(&B) -> &[B::Key],
        common: &BTreeSet<B::Key>,
        holders: Option<&BTreeSet<B::Key>>,
    ) -> BTreeSet<B::Key> {
        let at = |t: &B::Id, k: &B::Key| self.b(t).is_some_and(|b| field(b).contains(k));
        let rotates = holders.is_none(); // the holders' field; seats are no seats a recovery rotates
        let union: BTreeSet<B::Key> =
            tips.iter().filter_map(|t| self.b(t)).flat_map(|b| field(b).iter().cloned()).collect();
        let survives = |k: &B::Key| {
            tips.iter().filter(|t| at(t, k)).any(|t| {
                let a = self
                    .adding(t, k, field)
                    .into_iter()
                    .max_by(|x, y| (self.b(x).map(|b| b.version()), x).cmp(&(self.b(y).map(|b| b.version()), y)));
                // a recovery is a rotation of an existing seat, not an addition (CC 2.6.1.11): the key it seats is in
                // only where the holder's seat itself is in
                let rot = a
                    .as_ref()
                    .and_then(|a| self.b(a))
                    .and_then(|q| q.recovers())
                    .filter(|(_, n)| *n == k && rotates)
                    .map(|(h, _)| h.clone());
                tips.iter().filter(|t2| !at(t2, k)).all(|t2| {
                    self.removals(t2, k, field).iter().all(|r| a.as_ref().is_some_and(|a| self.in_past(r, a)))
                        && rot.as_ref().is_none_or(|h| {
                            self.removals(t2, h, field).iter().all(|r| {
                                self.b(r).and_then(|q| q.recovers()).is_some_and(|(rh, _)| rh == h)
                                    || a.as_ref().is_some_and(|a| self.in_past(r, a))
                            })
                        })
                })
            })
        };
        let cand: Vec<B::Key> = union.iter().filter(|k| !common.contains(*k) && survives(k)).cloned().collect();
        let mut f = common.clone();
        let mut h = holders.cloned().unwrap_or_else(|| common.clone());
        loop {
            let mut changed = false;
            for k in &cand {
                if f.contains(k) {
                    continue;
                }
                let ok = tips.iter().filter(|t| at(t, k)).all(|t| {
                    self.adding(t, k, field).iter().filter_map(|a| self.b(a)).all(|b| {
                        if b.prev().is_empty() || b.recovers().is_some_and(|(_, n)| n == k) {
                            return true; // a first bundle; its own recovery
                        }
                        self.meets(b, &self.voices(b), Some(&h))
                    })
                });
                if ok {
                    f.insert(k.clone());
                    if holders.is_none() {
                        h.insert(k.clone());
                    }
                    changed = true;
                }
            }
            if !changed {
                break;
            }
        }
        f
    }

    // ---- grants ------------------------------------------------------------------------------------------
    /// A grant EXISTS: counted at a strict majority over the live holders of the bundles it names (one: its
    /// holders; several: their fold, the common holders where the charters differ), those bundles concluded and not
    /// void, their charters carrying its duty; and it names the newest bundles in its signers' own past.
    pub fn grant_row(&self, gid: &B::Id) -> bool {
        let Some(g) = self.grants.get(gid) else { return false };
        let valid: BTreeSet<&B::Id> = self.valid().into_iter().map(|b| b.id()).collect();
        let named = g.bundles();
        if named.is_empty() || named.iter().any(|n| !valid.contains(n)) {
            return false;
        }
        if !self.antichain(named) {
            return false;
        }
        if named.iter().any(|n| self.b(n).is_none_or(|b| !b.duties().contains(g.duty()))) {
            return false;
        }
        let lines: BTreeSet<B::Id> = named.iter().flat_map(|n| self.line(n)).collect();
        if self.seen_of(gid).iter().any(|x| !lines.contains(x)) {
            return false; // the head rule
        }
        let base = self.live(self.fold(named).0);
        2 * g.signers().iter().collect::<BTreeSet<_>>().into_iter().filter(|k| base.contains(*k)).count() > base.len()
    }

    /// The bundles a grant names are an antichain: none in another's past.
    fn antichain(&self, named: &[B::Id]) -> bool {
        !named.iter().any(|a| named.iter().any(|b| self.in_past(a, b)))
    }

    /// The bundles a grant's signers had seen, derived from the rows in the grant row's own causal past: those
    /// acknowledged there (acceptance edges' attached_head_digest) and those earlier grants name. A named bundle
    /// brings its whole prev chain, so the head rule reads the bundle itself.
    pub fn seen_of(&self, gid: &B::Id) -> BTreeSet<B::Id> {
        let Some(i) = self.lane.idx(gid) else { return BTreeSet::new() };
        let mut out = BTreeSet::new();
        for p in self.lane.past(i, false) {
            let r = self.lane.row(p);
            if let Some(h) = r.attached_head() {
                out.insert(h.clone());
            } else if r.is_grant() {
                out.extend(r.bundles().iter().cloned());
            }
        }
        out
    }

    /// Every voice a grant holds: its own signers (its issuance, which its existence is counted on over the bundles
    /// it names) and the signers of the cosignatures of it held since. A retired key is no voice where it is not in
    /// force; a recovered holder cosigns again under its new key.
    pub fn grant_voices(&self, gid: &B::Id) -> BTreeSet<B::Key> {
        let Some(g) = self.grants.get(gid) else { return BTreeSet::new() };
        let mut out: BTreeSet<B::Key> = g.signers().iter().cloned().collect();
        for i in 0..self.lane.len() {
            let r = self.lane.row(i);
            if r.cosigns() == Some(gid) {
                out.insert(r.signer().clone());
            }
        }
        out
    }

    /// Whether the scope in force at the reader carries sub_delegation for the grant's duty (what every bundle in
    /// force carries); None: the grant does not resolve for this reader.
    pub fn sub_delegation(&self, gid: &B::Id, rd: &Reader<B::Id, B::Key>) -> Option<bool> {
        self.grant_in_force(gid, rd).ok()?;
        let g = self.grants.get(gid)?;
        let hs = self.heads(rd)?;
        Some(hs.iter().all(|h| self.b(h).is_some_and(|b| b.sub_delegation().contains(g.duty()))))
    }

    /// The duties the reader's bundles in force carry: what every head's charter carries.
    pub fn scope_in_force(&self, rd: &Reader<B::Id, B::Key>) -> BTreeSet<B::Word> {
        let Some(hs) = self.heads(rd) else { return BTreeSet::new() };
        let mut out: Option<BTreeSet<B::Word>> = None;
        for h in &hs {
            let d: BTreeSet<B::Word> = self.b(h).map(|b| b.duties().iter().cloned().collect()).unwrap_or_default();
            out = Some(match out {
                None => d,
                Some(o) => o.intersection(&d).cloned().collect(),
            });
        }
        out.unwrap_or_default()
    }

    /// The grant exists and resolves for the reader only while its voices are a strict majority of the holders in
    /// force at that reader (the fold at unjoined tips, the common holders where charters differ; live, under the
    /// same key) and the scope in force there carries its duty. A grant lapses when enough of its signers leave,
    /// and is re-issued.
    pub fn grant_in_force(&self, gid: &B::Id, rd: &Reader<B::Id, B::Key>) -> Result<(), Reason> {
        let Some(g) = self.grants.get(gid) else { return Err("grant_unknown") };
        let hs = self.heads(rd).ok_or("genesis_bundle_not_anchored")?;
        let valid: BTreeSet<&B::Id> = self.valid().into_iter().map(|b| b.id()).collect();
        if g.bundles().iter().any(|n| !valid.contains(n)) {
            return Err("grant_bundle_void");
        }
        if !self.antichain(g.bundles()) {
            return Err("grant_bundles_not_antichain");
        }
        if !self.grant_row(gid) {
            return Err("grant_count_short");
        }
        // (i) its voices (its issuance and every cosignature since) are a strict majority of ALL the holders in force
        // at this reader (live, under the same key)
        // rule 6: a double signer at the reader's head has no say in a count there, under either key
        let held = self.live(self.fold(&hs).0);
        let ns = self.no_say(rd);
        let voices =
            self.grant_voices(gid).into_iter().filter(|k| held.contains(k) && !ns.contains(&self.owner(k))).count();
        if 2 * voices <= held.len() {
            return Err("grant_voices_not_in_force");
        }
        if !self.scope_in_force(rd).contains(g.duty()) {
            return Err("grant_scope_not_in_force");
        }
        Ok(())
    }

    /// A halt halts for the reader where its signer is a holder in force there (live, under the same key). A halt
    /// counts nobody, so a double signer's halt at that head still halts: losing a say never removes the stop.
    pub fn halt_in_force(&self, hid: &B::Id, rd: &Reader<B::Id, B::Key>) -> Result<(), Reason> {
        let h = self.lane.idx(hid).map(|i| self.lane.row(i)).filter(|r| r.halts()).ok_or("halt_unknown")?;
        let hs = self.heads(rd).ok_or("genesis_bundle_not_anchored")?;
        if !self.live(self.fold(&hs).0).contains(h.signer()) {
            return Err("halt_signer_not_in_force");
        }
        Ok(())
    }

    /// The grant of this id, whether or not it stands.
    pub fn grant(&self, gid: &B::Id) -> Option<&'a G> {
        self.grants.get(gid).copied()
    }
}

fn holders_of<B: RootBundle>(b: &B) -> &[B::Key] {
    b.holders()
}

fn seats_of<B: RootBundle>(b: &B) -> &[B::Key] {
    b.seats()
}

/// A key's identity type, as the store's key record states it (a fact about a key, not a rule over rows).
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct Identity {
    /// The type includes `user`.
    pub user: bool,
    /// The type includes `node`.
    pub node: bool,
}

/// The trust root as one node reads it: the kernel's [`RootView`] over a [`Root`], for the seat rule's stalled
/// recovery. The store supplies only the reader (its anchor and acknowledgements) and each key's identity type; the
/// grant's resolution, its room scope and the identity rule are the kernel's.
pub struct RootReading<'r, 'a, B: RootBundle, G: RootGrant> {
    /// The root.
    pub root: &'r Root<'a, B, G>,
    /// This node, as a reader of it.
    pub reader: Reader<B::Id, B::Key>,
    /// A key's identity type, from the store's key record.
    pub identity: &'r dyn Fn(&B::Key) -> Identity,
}

impl<B, G> RootView<B::Id, B::Key, crate::seat::Obj<B::Id, B::Key>> for RootReading<'_, '_, B, G>
where
    B: RootBundle,
    G: RootGrant<Id = B::Id, Key = B::Key, Word = B::Word>,
{
    fn recovery_grant(&self, grant: &B::Id, room: &crate::seat::Obj<B::Id, B::Key>) -> Result<B::Key, Reason> {
        self.root.grant_in_force(grant, &self.reader)?;
        let g = self.root.grant(grant).ok_or("grant_unknown")?;
        if *room != crate::seat::Obj::Row(g.scope().clone()) {
            return Err("grant_scope_not_this_room");
        }
        let id = (self.identity)(g.to());
        if !id.user || id.node {
            return Err("grant_identity_not_user");
        }
        Ok(g.to().clone())
    }

    fn sub_delegation(&self, grant: &B::Id) -> Option<bool> {
        self.root.sub_delegation(grant, &self.reader)
    }

    fn seat_grant(&self, grant: &B::Id, room: &crate::seat::Obj<B::Id, B::Key>, duty: &str) -> Result<B::Key, Reason> {
        self.root.grant_in_force(grant, &self.reader)?;
        let g = self.root.grant(grant).ok_or("grant_unknown")?;
        if *room != crate::seat::Obj::Row(g.scope().clone()) {
            return Err("grant_scope_not_this_room");
        }
        if g.duty().as_ref() != duty {
            return Err("grant_duty_not_this_seat");
        }
        Ok(g.to().clone())
    }
}

/// What the seat rule asks of the trust root a node reads, for a stalled recovery
/// ([`crate::seat::recovery_verdict`]): the key a grant names, where the grant resolves for this node, names this
/// room in its scope, and names a key whose identity type includes `user` and excludes `node`. The kernel's
/// implementation is [`RootReading`].
pub trait RootView<I, K, O> {
    /// The key grant `grant` names for room `room`, or why it does not stand: `grant_unknown`,
    /// `genesis_bundle_not_anchored`, `grant_bundle_void`, `grant_count_short`, `grant_voices_not_in_force`,
    /// `grant_scope_not_in_force`, `grant_scope_not_this_room`, `grant_identity_not_user`.
    fn recovery_grant(&self, grant: &I, room: &O) -> Result<K, Reason>;
    /// Whether the charter in force at this node carries sub_delegation for the grant's duty (the delegation
    /// gate's question for a chain from a root grant); None: the grant does not resolve here, or no root is read.
    fn sub_delegation(&self, _grant: &I) -> Option<bool> {
        None
    }
    /// The key a root grant seats in room `room` for duty `duty` (the seat a root grant gives, cross-object rest 5),
    /// where the grant resolves here, names this room and this duty; or why not. Default: no root is read.
    fn seat_grant(&self, _grant: &I, _room: &O, _duty: &str) -> Result<K, Reason> {
        Err("no_root_read")
    }
}
