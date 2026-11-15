# Adopting `ciris-kernel` in persist

This note is for the persist refactor onto the kernel. It was written from a read of persist's worktree
`CIRISPersist-wkernel` at `8c011511` (version 61.3.0, branch `fsd/kernel-seams`). Persist anchors below are
`file:line` in that tree under `src/`. Nothing in persist was changed or run. Persist's own design for the seam
is `FSD/KERNEL_SEAMS.md` (§5); this crate is meant to sit under that interface, not to replace it.

## What persist implements

One trait, [`Row`](src/lib.rs), and for each answer persist asks, the spec trait of that answer.

| Trait | What persist supplies | From |
|---|---|---|
| `Row` | `Id` = `persist_row_hash` (or the `RowId([u8; 32])` of KERNEL_SEAMS §5.2); `Key` = key id; `names()` = every digest the row's signed bytes name; `signer()` = `attesting_key_id` | `Attestation` (`federation/types.rs:1632`): `persist_row_hash` `:1669`, `attesting_key_id` `:1636`; the named digests are `references_attestation_id` (`federation/precedence.rs:71`), `prev_head_digest` and `charter_digest` on a group version (`federation/types.rs:3191`, `:3200`) |
| `seat::SeatRow` | the kind (offer, accept, withdraw, unseat, cosign, ballot, ack), `to`, `scope`, `obj`, `conf`, `under`, `cosigners`, `subjects`, `head`, `policy` | `attestation_type` `:1642`; `subject_key_ids` `:1684`; `additional_scrubs` (verified cosignatures) `:1768`; the body members the family's grammar names |
| `cut::CutSpec` | the slots a row is on and cuts, and what it says | the family tables (`family_model.json`); the slot of a seat is `(seat, key, scope, object)` |
| `window::WindowRow` | the opener's window name, an answer's word, a landing's receipt and its signer's own instant | the window families; the instant is the signed `asserted_at` of one signer, compared only with that signer's own (`:1647`) |
| `key_end::KeyEndRow` | a key record's `valid_from`, `valid_until`, the old key of a rotation and the signatures it carries | `KeyRecord` (`federation/types.rs:1343`): `valid_from` `:1362`, `valid_until` `:1365`, `identity_type` `:1358` (persist maps it to `EndRule`) |
| `head::Entry` | the header a rule reads: kind, head, act, members and count of a roster version, a cut's signatures, a window's length and first-held instant, the duties that pin bytes | the same rows, plus `first_held_instant` (`federation/attestation_admit.rs:98`) for an opener |

`names()` returns a slice, so persist builds a small view per row that owns its named digests. The view is
the "one typed view of a verified, well-formed row" of KERNEL_SEAMS §5.2, with `refs` as `names`.

The tables are data persist passes in: [`SeatLaw`](src/seat.rs) (what a seat holds and may confer, the duties,
the policy counts, the depth) and [`WindowSpec`](src/window.rs) (the clauses, the default, the length). They
come from `governance_policy.json` and the family tables that persist already vendors.

## Which persist decisions map onto which kernel functions

| Persist today | Kernel | What changes |
|---|---|---|
| the door: `plan_put_attestation` (`federation/attestation_admit.rs:654`) and its gates | `layers::kept`, then `layers::conclude` with the family's rule | a row that names an unheld row waits; a check that reads another row becomes a conclusion, never a drop (KERNEL_SEAMS §0) |
| `owner_of` (`federation/admission.rs:12694`, fails closed on two owners) | `seat::Seats::one("owner", key)`; `reexpress.owner_of` is the same rule over `ops` | the same answer, read from the held set: two live owners give none |
| `consensus::evaluate`, `eligible`, `counted` (`federation/consensus.rs:213`, `:161`, `:180`) | `seat::members_at` (the members at the head the row names), `seat::voices`, `seat::met`, `ranked::ranked` | the count is over the head the row names, never the roster at receipt |
| `trust_root_valid` (`federation/trust_root.rs:1407`) and `check_federation` (`federation/replication/admission.rs:133`) | `trust::honours`, `trust::reaches`; `derived::reach` and `means` for a reader | the reader's view filters held rows; nothing is dropped at replication for trust |
| `check_delegation_cycle_admission` (`federation/admission.rs:18517`) | `trust::reaches` (a cycle is visited once) and the seat walk's depth | no edge is refused for closing a cycle |
| `is_roster_key_at` and `check_roster_act_fresh` (`federation/self_roster.rs:321`, `:553`) | `seat::members_at` at the head the act names; `window::rule` and `window::outcome` | standing is read at the named head, not at receipt; the lone eviction lands only under recount |
| `self_roster::execute_due` and `cosign::execute_due` (`federation/self_roster.rs:1408`, `federation/cosign.rs:1199`); `cosign::hold` (`federation/cosign.rs:853`) | `window::outcome` on this node's clock; `seat::voices` for the cosignatures | a lapse is an answer read at `now`, not a sweep that deletes pending rows |
| `held_head_verdict` (`federation/group_supersede_admit.rs:77`), which refuses a fork | `seat::Seats::tips`, `tips_common`; `line::settle`, `line::void` for a reader's own line | two versions of one head are both held and wait as tips |
| `stamp_entitles` and the `withdraws_admission_rule` stamp (`federation/precedence.rs:269`; `federation/types.rs:1702`) | `seat::seat_rule` on a withdrawal, read at every evaluation | the stamp goes |
| `purge_finalize` (`engine.rs:9415`, `federation/steward_purge.rs:2423`) | `head::purge` says which rows may become stubs; `head::View` answers over the stubs | persist keeps the bytes, the deletion and the duties' enforcement; the kernel says what a stub must keep |
| key liveness against `valid_until` (`KeyRecord`, `federation/types.rs:1365`) | `key_end::well_formed`, `conclude_rule`, `live`, `ended`, `retained` | a row of an ended key lapses only when no live row has it in its past |

## What persist would delete, and what it keeps

Delete, once each family's rule runs through the crate: the gates that refuse for what another row says (the
21 breakers of KERNEL_SEAMS §2.2); the `withdraws` stamp; the fork refusal in `held_head_verdict`; the
sweeps that delete pending cosign and self-roster rows; and the hand-rolled roster-at-receipt reads.

Keep, as KERNEL_SEAMS §8 already says: bytes at rest, the codec and `RowId`, hybrid verification and KEM,
replication and quotas, first-held stamping, the effect executor, SQL indexes and paging, schema and
migrations, and the local operational store.

## What the crate does not cover

- **Signature verification.** A row reaches the kernel verified (`verify_federation_tier_ingest`,
  `federation/attestation_admit.rs:1015`). `cosigners()` must list verified signatures only.
- **CBOR and COSE decoding, canonical bytes and hashing.** The kernel takes the digest persist computed
  (`compute_persist_row_hash`, `federation/types.rs:5138`). A checkpoint's digest of folded state is
  persist's to compute and sign; `head::purge` returns only what the checkpoint names.
- **Storage and incremental evaluation.** There is no `HeldSource`, no read set and no answer cache here
  (KERNEL_SEAMS §5.4). Persist calls the crate over the rows an answer reads. `graph::Graph` is quadratic in
  the rows it is built over, so a call over the whole store is the wrong shape.
- **Transport and routing.** `route` (hold, offer, serve, relay, park, discard) is not stated; KERNEL.md 9
  lists placement as table data not yet written.
- **The fold default** (CC 3.5.1), which `precedence_winner` (`federation/precedence.rs:145`) implements for
  one signer's chain. It stays persist's until the expression language is carried.
- **The key plane** (`community_dek.rs:545`, epoch identity) and **private-room bindings**.
- **Effects and drafts** (KERNEL_SEAMS §5.6, §5.7). The crate returns answers, not effects.
- **Classification of a raw row into a family**, and the table loader. The crate takes the tables as values.

## Points to settle before adoption

- **Persons and voices.** `eligible` collapses keys to one seat per person (`federation/consensus.rs:161`) and
  picks "the lowest key" among them. The kernel counts distinct signers and never picks by key id. Under
  KERNEL.md 7b the person's devices are one voice; persist's adapter must present that voice as the signer,
  or a count will count devices.
- **Objects that are rows and objects that are keys.** `seat::Obj::from_reference` types an object from the
  form of its reference in the signed object: a `[-16, digest]` row id is a row, an identity reference
  `urn:ietf:params:oauth:ckt:sha-256:…` is a key. Persist's adapter passes the reference as written. Today's
  `attested_key_id` and `references_attestation_id` are bare strings, so this holds from the rc20 wire on.
- **Instants.** `window::WindowRow::T` and `key_end::KeyEndRow::T` are any ordered type with subtraction.
  Persist's `Micros` (`i64`) fits. The crate never compares two signers' instants.

## Side by side with persist's own tests

The crate was run beside persist on persist's own test cases. A throwaway clone of persist at `8c011511` took
the crate as a path dev-dependency and a thin `Row` adapter. In test builds, it logged each call of the four
functions with the kernel's answer. The full lib suite ran with `--features sqlite`: 3,394 passed and 3 failed.
The three fail only because of the hooks (one counts directory reads, two scan the wrapped function's
source), and all three pass on the unhooked tree. The clone was then deleted.

| Function | Distinct calls | Agree | Differ | Why they differ |
|---|---|---|---|---|
| `consensus::evaluate` | 428 ballots | 283 | 20 | removals under `unanimous` exclude the member named, and the adapter's count does not (6); an `infrastructure` group counts founders only, and the kernel reads no role (8); persist counts persons, so two devices of one person are one voice (5); a seated member's self-signed re-admission is refused by persist and counted by the kernel (1). 125 ballots use a protocol with no kernel cell (`founder_only`, `open:self_admit`, `reverse_quorum`, `custom:`) |
| `owner_of` | 1,922 | 1,722 | 198 | in every one, persist names an owner from a binding the node's own key did not sign; under the seat as two consents the kernel names none. Of the agreements, 1,721 are "no owner" on both sides and only 1 names the same owner, so this mapping is barely exercised until bindings carry the node's signature. 2 more are persist's ambiguity error, where the kernel also names none |
| `trust_root_valid` (its edge leg) | 199 | 191 | 8 | 6: the edge carries no `trust:accepts` label, or no head, and persist refuses it; the adapter passed every `delegates_to`, so this is the adapter's filter, not the kernel's. 2: a superseded edge, which the fold default decides (CC 3.5.1); the crate does not carry that fold |
| `held_head_verdict` | 8 | by design | | persist refuses a version that does not name the held head; the kernel holds it, as a tip beside the head or waiting for the head it names. Where persist admits, the version names the held head and the kernel has one head, except a second founding version, where the kernel has two tips. Persist also refuses a supersede whose proof names another prior, which the kernel does not read |

## How persist would depend on it

Recommended: a git dependency on the kernel repository at a tag, the way persist already takes
`ciris-verify-core` (`Cargo.toml:581`):

```toml
ciris-kernel = { git = "https://github.com/CIRISAI/CIRISKernel", tag = "<tag>", version = "0.1" }
```

`deny.toml` has `[sources] allow-git = []` with `unknown-git = "warn"`, so the repository would be added to
`allow-git`. A path dependency through `[patch]` serves local work across the two trees. crates.io can wait
until the API settles; the crate is `publish = false`.

The crate declares `rust-version = "1.89"`, and CI builds and tests it on that toolchain. Persist pins
1.97.0 (`rust-toolchain.toml`), which is newer. The kernel repository's `deny.toml` holds persist's licence
allow-list, and `cargo deny check` passes under it.
