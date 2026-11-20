# ciris-kernel 0.3: held views (issue #4)

The design agreed with CIRISPersist, then what has landed and what it measured. Status, 2026-11-20: slice 1
(the concluded layer, `src/held.rs`) is in; `HeldView`, the checkpoint and `Held.lean` are not yet.

## Proposal

Additive only. Nothing existing changes signature or answer. New module `held`. no_std, sync, no I/O, clock or globals.

## What the proofs give, and therefore what each layer must recompute

- kept + concluded (`layers`): a conclusion reads only the row and its concluded ancestors, and is final once
  the row is kept (`Causal.concl_final`, T6 ii). A new row x leaves every held conclusion as it was. Admit
  computes x, plus any waiting rows that x releases (rows naming x that were blocked on it), in level order. This
  layer is append-only; nothing is invalidated.
- Derived answers that read concurrency (slot, cut, `head::View` counts_at / carried / settled / missing / void):
  T6 iii (`conclOf_local`, `concl_ext_local`, `derived_ext_local`, `countsAt_local`). x changes the answer
  about r only if r is x or a descendant of x, or r or an ancestor of r is in concurrent conflict with x or with a
  descendant of x. That is the dirty cone. Only this layer holds an answer cache.

## Types

```rust
/// Rows by handle: &'a R, Rc<R>, Arc<R> or R itself, so persist need not build a Vec<KRow> per call.
pub struct Held<R: Row, H: Borrow<R>, S: HeldSpec<R>> { /* graph, levels, conclusions, waiting set, spec */ }

/// The rules, as a value the Held owns (no borrowed FnMut), so a Held can live across transactions.
pub trait HeldSpec<R: Row> {
    fn well_formed(&self, r: &R) -> bool;
    fn conclude(&self, p: &Past<'_, '_, R>) -> bool;
    fn root(&self, r: &R) -> Option<bool> { None }      // None = no seed (as conclude's root: None)
    fn conflict(&self, a: &R, b: &R) -> bool { false }  // T6 iii's `conflict`; false = concluded layer only
}

pub struct Admitted<I> {
    pub kept: Vec<I>,      // newly kept: the row and the rows it released, in admission order
    pub waiting: bool,     // the row itself waits on a name not held
    pub dirty: Vec<I>,     // held rows whose derived answers must be re-read: the cone ∪ conflict, sorted, dedup
}

impl Held<R, H, S> {
    pub fn new(spec: S, rows: impl IntoIterator<Item = H>) -> Self;   // == layers::arrive over rows
    pub fn admit(&mut self, row: H) -> Admitted<R::Id>;                // amortised O(cone + names), not O(n)
    pub fn admit_all(&mut self, rows: impl IntoIterator<Item = H>) -> Admitted<R::Id>;
    pub fn graph(&self) -> GraphRef<'_, R>;      // the same queries as Graph: idx, in_past, concurrent, frontier, past
    pub fn concluded(&self, id: &R::Id) -> bool;
    pub fn into_rows(self) -> Vec<H>;            // dropping or taking apart is the caller's choice
}
```

`Graph` grows to support append: the sorted index becomes a `BTreeMap` (or sorted Vec with insertion), pasts
become per-row bit sets that grow on read, and levels are computed for x and its released rows only. The
existing `Graph::new` / `conclude` / `arrive` are untouched; `Held` has its own graph type, so `Graph`'s
performance and answers cannot move.

## The head layer (persist's re-fold fan-out)

```rust
pub struct HeldView<I, K, T> { /* head::View's indexes, kept incrementally, plus an answer cache */ }
impl HeldView {
    pub fn new(store: &Store<I,K,T>, own: K, reading: Reading, say: bool) -> Self;   // == View::new(store, &[], ..)
    pub fn admit(&mut self, e: Entry<I,K,T>) -> Admitted<I>;   // dirty = acts whose answers may change
    pub fn view(&self) -> &View<I,K,T>;                        // every existing View method, unchanged
}
```

Persist's use: admit the row, re-run the door only for `Admitted.dirty` (sorted, deduplicated, like `Answer.reads`),
not for every dependent. That is the "one new row with N dependents" shape.

## Checkpoint (CC 2.7.10), veto 4

```rust
pub const CHECKPOINT_VERSION: u16 = 1;
impl HeldView { pub fn checkpoint(&self) -> Vec<u8>; }        // canonical: same view, same bytes
pub fn resume(bytes: &[u8], extra: impl IntoIterator<Item = Entry<..>>, own: K, ..) -> Result<HeldView, CheckpointError>;
pub enum CheckpointError { Version(u16), NotCanonical, Truncated, Names(I) }
```

The kernel has no serialisation today, so the encoding is generic: the caller supplies `I`, `K` and `T` encoders
through a small `Encode` trait (fixed-width or length-prefixed, big-endian, entries in id order). The bytes cover
the purged store (the output of `head::purge`) plus the conclusions and the acked set, which is what
`checkpoint_resume` says suffices. Keyed by persist as (family or group, head row id), stored as one blob. Decode
refuses unknown versions, non-canonical bytes (re-encodes and compares) and any entry naming an id not held.

## Equality (veto 1)

- `held::check::differential(spec, rows, order) -> Result<(), Mismatch>`, a pub fn (no test cfg, so persist
  calls it from its own tests on its own row mixes). After every admit it asserts that Held's kept set,
  conclusions and every graph answer equal `layers::arrive` over the prefix, and that HeldView's
  `answers(now)` equals `View::new` over the prefix. It returns the first mismatch with the prefix length.
- The crate's tests run it over every fixture and the proptest-style DAG generator in `tests/common/dag.rs`, in
  order, reversed and shuffled.
- Lean: `Held.lean` states admit as the dirty-cone update and proves it equal to the full fold from
  `conclOf_local` / `concl_ext_local`; `resume_eq` from `checkpoint_resume`. TLA+: one spec, admit vs. full fold.

## Benches (examples/persist_paths.rs, the existing harness)

- `held::admit` at stores of 1,024 and 64,000 rows: in order, reversed and shuffled arrivals.
- `held::admit_dependents`: one new row with N = 1, 16, 256 dependents, against the same full re-fold.
- `held_view::admit` vs `View::new`, at 1,024 and 64,000.
- CC 2.7.10: `cold` (`View::new` over the whole store) vs `resume(checkpoint) + admit(rows since)`, after a
  `head::purge` cut, at 1,024 and 64,000. Plus `checkpoint` encode and decode time and size.
- Rows shaped as today: 32-byte id, 76-byte `String` key.

## Bounds

`admit` holds no lock and allocates only for x, the rows it releases and the dirty list. The head call under
persist's sqlite writer lock stays `View`'s existing query (`frontier` / `tips`) on held state, so no rebuild.

## Not in this proposal

- Nothing in `seat`, `trust`, `key_end` or `window` changes. `owner_of` (persist's hottest path) goes through
  `layers::conclude` + `Seats::holders`; a `Held` gives it the concluded layer without a rebuild, and
  `Seats` over a held view is a follow-up once the shape here is agreed.
- Persist's own `fold_reads` stay persist's. `Admitted.dirty` is what can replace them.

## Revision 1, after persist's answers (2026-11-20)

Agreed with persist (cirispersist-e7): the two-layer split, handle-based `Held`, admit then re-run only `dirty`,
and a non-test `differential`. Persist adopts after v62.0 ships. Changes:

1. **Checkpoint carries ids, not row content.** `checkpoint()` encodes kernel-side structure only (held ids,
   conclusions, acked set, the purge cut's stub fields), with ids through `Encode`. A fixed-width
   `[u8; N]` encoder is provided, so 32-byte digests need no code. `resume(bytes, rows: impl Fn(&I) -> Option<H>)`
   re-attaches rows by id from the caller's store, so a checkpoint cannot disagree with stored row bytes. A named
   id the closure does not supply fails with `CheckpointError::Missing(I)`, never a partial view.
2. **Scoped views, open world.** A view is keyed by the caller as (scope id, head row id). Rows outside the scope
   that a gate reads (owner_of from a group gate, trust_root from anywhere) may be supplied as foreign rows:
   `Held::admit_foreign(h)` holds them for reads without making them members of the scope. `Admitted` gains
   `foreign: Vec<I>` (sorted, dedup), the foreign rows the dirty set's answers read. The view never assumes the
   world is closed; a named id neither held nor supplied leaves its namer waiting, as the door does now.
3. **Transactional admit.** `admit(&mut self, h) -> Result<Admitted, Refused>` either commits whole or leaves the
   Held unchanged. A row not well formed, a duplicate, or one on a cycle of names is `Refused` with no change.
   Internally it computes the update first and then applies it, with no panic between. `Held` and `HeldView` are
   `Clone`, so a caller inside a DB transaction that may roll back can also keep the prior value and drop the new
   one. The differential checks the unchanged-on-refusal property too.
4. **The complexity bound, stated and benched.** For the concluded layer:
   O((|released| + 1) · (names + log n)), plus the new row's past as one bit-set union over what it names.
   For the head layer: O((|cone(x)| + |conflict(x)|) · log n). That needs conflicts found by index, not by
   pairwise scan, so `HeldSpec::conflict(a, b)` becomes `conflict_key(&R) -> Option<Self::Key>`: two rows
   conflict iff they share a key and are concurrent. The bench asserts the bound by counting rows visited per
   admit (a pub `Admitted::visited`) against cone + conflict, at 1,024 and 64,000, not by wall time alone. Caveat
   to measure: a past stored as a dense bit set costs n/64 words, so the past of x is O(n/64) to build. The bench
   reports that term separately, and a sparse past for deep stores is a fallback if it shows.
5. `dirty`, `kept`, `foreign`: owned `Vec<I>`, sorted and deduplicated.

## Slice 1: what landed

`src/held.rs`: `Held<'a, R, S: HeldSpec<R>>`, `Rules`, `Admitted`, `Refused`, `differential`. Additive:
`Graph::push` and `Graph::reserve` are new methods; `Graph` and `Concluded` gained `Clone`. Nothing else in the
crate moved. Every existing test, conformance run and plant passes unchanged.

**One departure from the proposal:** rows are borrowed as `&'a R`, not through a `H: Borrow<R>` handle. `Held`
holds a `Concluded`, which holds a `Graph`, so every existing conclusion rule that takes a `Past`
(`seat::seat_rule`, `key_end::conclude_rule`, `window::rule`) runs on a held view unchanged. A handle type would
have meant a second graph and a second `Past`, so every rule would have needed rewriting. A caller that wants a
`Held` to outlive one call keeps its rows in storage that does not move (a boxed slice, an arena).

`differential` compares the held layers with `conclude(kept(prefix))` after every admission: the kept set, each
row's conclusion, level, names and past size, and every in-past and concurrency question up to 64 rows. It also
checks that a refusal changes nothing and that `dirty` is exactly the rows newly kept. `tests/held.rs` runs it over
five generated graphs, in order, reversed and three shuffles, with a rule that reads the concluded past, a seeded
rule and a trivial one. It compares with `kept` rather than `arrive`, because they differ in one case: two rows
with the same id but different well-formedness. That cannot happen when ids are digests.

### Measured (examples/persist_paths.rs `held::`; rows shaped as persist's KRow; `dag(n, 3, 64, 7)`; seat_rule)

| bench | 1,024 | 16,384 | 64,000 |
|---|---|---|---|
| `held::admit(one)` | 17 µs | 0.36 ms | 2.0 ms |
| `held::admit(one)/rule_reads_nothing` | 3.2 µs | 32 µs | 112 µs |
| `held::refold(one)` (today: conclude over n + 1) | 3.3 ms | 1.63 s | skipped (quadratic, ~25 s) |
| `held::admit_dependents/1` | 29 µs | 0.53 ms | 3.0 ms |
| `held::admit_dependents/16` | 0.20 ms | 3.8 ms | 16.5 ms |
| `held::admit_dependents/256` | 3.0 ms | 66 ms | 236 ms |
| `held::refold_dependents/256` | 5.1 ms | 1.78 s | skipped |
| `held::clone` | 37 µs | 2.7 ms | 30 ms |

The admit benches clone a held view outside the timing and reserve room in it (`Held::reserve`). A clone has no
spare capacity, so its first push would copy every buffer, which a caller holding one view never pays.

### What the bound is, measured

`Admitted::visited` is cone-sized, and the bench asserts it exactly: (d + 1) rows kept plus what they name. Wall
time is not cone-sized, for two reasons that the numbers separate:

1. **The rule reads the whole concluded past.** That is the `Past` contract (`p` is every concluded ancestor),
   and `seat_rule` reads it. In this graph, a new row naming recent tips has almost the whole store in its past,
   so admission at 64,000 costs 2.0 ms, of which 1.9 ms is the rule. Admission is still 4,500× a re-fold at
   16,384, because it runs the rule once and not n times. Making the rule itself cone-sized means an incremental
   seat count (members at a head kept across admissions). That is the follow-up the proposal names for `Seats`.
2. **The kernel's own part is O(|past(x)|), not O(cone).** It builds the new row's past as a bit set of n / 64
   words and materialises `p` as a `Vec<usize>`: 112 µs at 64,000 with a rule that reads nothing. A sparse past,
   or a lazy `p`, would remove it. A lazy `p` changes `Past`, so it is not additive.

**Memory:** every held row's past is a dense bit set, so a held view of n rows holds about n² / 128 words
(~256 MB at 64,000). `layers::conclude` holds the same pasts while it runs, but a held view keeps them, which is
why `held::clone` is 30 ms at 64,000. This is the quadratic term issue #4 names, and the sparse past is now the
first thing to measure.

### Next, in persist's order (cirispersist-e7, 2026-11-20)

1. **A sparse past.** The dense past (~n² / 128 words) must go before a node can hold a 64,000-row view in
   memory.
2. **A cheap `resume`.** Persist rebuilds its rows per transaction, so a borrowing `Held` lives only as long as
   that row arena. The checkpoint is how a held view crosses transactions: `resume` plus rows re-attached by id
   from persist's store. Its cost against a fold is the number persist cares about most, and the bench reports
   it first.
3. Persist accepts `&'a R` in place of a handle type. It runs `held::differential` on its own row mixes after
   v62.0 is tagged.

### Not yet

`HeldView` (the head layer and its conflict cone), the checkpoint (`checkpoint` / `resume`, ids only), foreign
rows, and `Held.lean`.
