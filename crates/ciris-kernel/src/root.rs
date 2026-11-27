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
    type Word: Ord + Clone;
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
    /// The recovery commitments: (holder, its recovery key), keys exactly the holders.
    fn recovery(&self) -> &[(Self::Key, Self::Key)];
    /// For a holder's own key recovery: (the holder, its new key).
    fn recovers(&self) -> Option<(&Self::Key, &Self::Key)>;
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
    /// A duty, as the bundles' words.
    type Word: Ord + Clone;
    /// The row is a root grant (else an acceptance edge, or another row of the lane).
    fn is_grant(&self) -> bool;
    /// For an acceptance edge: the bundle its attached_head_digest names.
    fn attached_head(&self) -> Option<&Self::Id> {
        None
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
    /// The bundles it acknowledged (they accumulate: its own line).
    pub acks: Vec<I>,
}

/// Why a bundle or a grant does not stand.
pub type Reason = &'static str;

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
        for b in bundles {
            let Some((h, new)) = b.recovers() else { continue };
            if b.prev().len() != 1 {
                continue;
            }
            let Some(p) = by.get(&b.prev()[0]) else { continue };
            let rk = Self::commitment(p, h);
            for k in [Some(new.clone()), rk].into_iter().flatten() {
                let (ra, rb) = (find(&own, h), find(&own, &k));
                if ra != rb {
                    let (lo, hi) = if ra < rb { (ra, rb) } else { (rb, ra) };
                    own.insert(hi, lo);
                }
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

    fn consistent(&self, b: &B) -> bool {
        let ps: Vec<&B> = b.prev().iter().filter_map(|p| self.b(p)).collect();
        if ps.len() != b.prev().len() {
            return false;
        }
        let rk: BTreeSet<&B::Key> = b.recovery().iter().map(|(h, _)| h).collect();
        let hk: BTreeSet<&B::Key> = b.holders().iter().collect();
        if rk != hk {
            return false; // recovery_commitments are keys exactly the holders
        }
        if ps.is_empty() {
            return true;
        }
        let top = ps.iter().map(|p| p.version()).max().unwrap_or(0);
        if b.version() != top + 1 {
            return false;
        }
        if !ps.iter().all(|p| p.family() == b.family()) {
            return false;
        }
        if ps.len() >= 2 {
            // the join's wire: refs.prev is the greatest version, least id among equals; refs.further_prev the
            // rest; a named predecessor in the past of another concludes nothing
            let first = ps.iter().min_by(|x, y| (y.version(), x.id()).cmp(&(x.version(), y.id())));
            if first.map(|q| q.id()) != Some(&b.prev()[0]) {
                return false;
            }
            if b.prev().iter().any(|a| b.prev().iter().any(|c| self.in_past(a, c))) {
                return false;
            }
        }
        true
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
        })
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
        let Some(rk) = Self::commitment(p, h) else { return Some(Err("recovery_not_signed")) };
        if !b.statements().iter().any(|(k, iat)| *k == rk && *iat == b.iat()) {
            return Some(Err("recovery_not_signed"));
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

    /// The bundle's own count, its predecessors concluded.
    pub fn counted(&self, i: &B::Id) -> Result<(), Reason> {
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
        if !self.consistent(b) {
            return Err("invalid");
        }
        if b.prev().iter().any(|p| self.counted(p).is_err()) {
            return Err("prev_not_concluded");
        }
        let v = self.voices(b);
        if b.prev().is_empty() {
            let all = !b.holders().is_empty() && b.holders().iter().all(|k| v.contains(k));
            return if all { Ok(()) } else { Err("count_short") };
        }
        if let Some(r) = self.recovery_ok(b) {
            return r;
        }
        if self.meets(b, &v, None) {
            Ok(())
        } else {
            Err("count_short")
        }
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

    /// Built on: void, a join naming a void predecessor included.
    fn close(&self, cs: &[&'a B], tv: &mut BTreeSet<B::Id>) {
        loop {
            let mut changed = false;
            for c in cs {
                if tv.contains(c.id()) || !c.prev().iter().any(|p| tv.contains(p)) {
                    continue;
                }
                tv.insert(c.id().clone()); // a join naming a void predecessor concludes nothing
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
            if first {
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

    /// The reader's first bundle; None: `genesis_bundle_not_anchored`.
    pub fn first(&self, rd: &Reader<B::Id, B::Key>) -> Option<B::Id> {
        let mut firsts: Vec<&B::Id> =
            self.valid().into_iter().filter(|b| b.prev().is_empty()).map(|b| b.id()).collect();
        firsts.sort();
        firsts
            .into_iter()
            .find(|i| {
                rd.anchor.as_ref() == Some(*i)
                    || rd.thumbs.as_ref().is_some_and(|t| {
                        self.b(i).is_some_and(|b| b.holders().iter().cloned().collect::<BTreeSet<_>>() == *t)
                    })
            })
            .cloned()
    }

    /// The reader's own line: every bundle it acknowledged (they accumulate, in any order), and the bundles void
    /// for the reader by it: every bundle behind ANY acknowledged bundle, an acknowledged one included, and every
    /// bundle built on one, a join included (a join naming a predecessor void for a reader concludes nothing for
    /// it). Acknowledging never revives.
    pub fn reader_line(&self, rd: &Reader<B::Id, B::Key>) -> (Vec<B::Id>, BTreeSet<B::Id>) {
        let valid: Vec<&'a B> = self.valid();
        let acked: Vec<B::Id> = rd.acks.iter().filter(|a| valid.iter().any(|b| b.id() == *a)).cloned().collect();
        let mut out: BTreeSet<B::Id> = valid
            .iter()
            .filter(|b| acked.iter().any(|a| self.b(a).is_some_and(|ba| self.behind(b, ba))))
            .map(|b| b.id().clone())
            .collect();
        loop {
            let mut changed = false;
            for b in &valid {
                if !out.contains(b.id()) && b.prev().iter().any(|p| out.contains(p)) {
                    out.insert(b.id().clone());
                    changed = true;
                }
            }
            if !changed {
                break;
            }
        }
        (acked, out)
    }

    /// The bundles in force for the reader: the newest it acknowledged, read by its line; none, its anchor.
    /// None: `genesis_bundle_not_anchored`.
    pub fn heads(&self, rd: &Reader<B::Id, B::Key>) -> Option<Vec<B::Id>> {
        let f = self.first(rd)?;
        let (accepted, rv) = self.reader_line(rd);
        let held: Vec<B::Id> = self
            .valid()
            .into_iter()
            .map(|b| b.id().clone())
            .filter(|i| (*i == f || self.in_past(&f, i)) && !rv.contains(i))
            .collect();
        let mut acked: BTreeSet<B::Id> = held.iter().filter(|i| accepted.contains(*i)).cloned().collect();
        // a contested bundle the reader acknowledged leaves it at the bundles it extends, and so on down
        let contest = self.void_and_contested().1;
        let held: BTreeSet<B::Id> = held.into_iter().collect();
        let mut todo: Vec<B::Id> = rd.acks.iter().filter(|i| contest.contains(*i)).cloned().collect();
        while let Some(x) = todo.pop() {
            for p in self.b(&x).map(|b| b.prev().to_vec()).unwrap_or_default() {
                if held.contains(&p) {
                    acked.insert(p);
                } else if contest.contains(&p) {
                    todo.push(p);
                }
            }
        }
        if acked.is_empty() {
            return Some(Vec::from([f]));
        }
        Some(acked.iter().filter(|i| !acked.iter().any(|j| self.in_past(i, j))).cloned().collect())
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
        // (i) its voices are a strict majority of the holders in force at this reader (live, under the same key)
        let held = self.live(self.fold(&hs).0);
        let voices = g.signers().iter().collect::<BTreeSet<_>>().into_iter().filter(|k| held.contains(*k)).count();
        if 2 * voices <= held.len() {
            return Err("grant_voices_not_in_force");
        }
        if !self.scope_in_force(rd).contains(g.duty()) {
            return Err("grant_scope_not_in_force");
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
}
