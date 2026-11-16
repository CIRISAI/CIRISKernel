# Performance: the paths persist calls

Persist moved its decisions onto this crate in its v62 slice C and measured its benches against its pre-kernel
baseline (v61.4.1). The vote count (`consensus_eval`) came out 16 to 66 times slower, with a floor of about 8 µs
at a roster of three. `owner_of`, `trust_root_valid`, the delegation walk and `held_head` came out 1.1 to 1.7
times slower. This note records what the kernel did on those paths, what changed, and the before/after for each
function persist calls, at sizes 3 to 16,384. No answer changed (section 4).

## 1. How it was measured

- `examples/persist_paths.rs` benches the functions persist calls, over rows shaped as persist's adapter
  presents them (`src/kernel/view.rs` in CIRISPersist: a 32-byte row id, a `String` key of 76 bytes, the
  seat fields; persist's `NoCut` and `law::seat_law()`). It has no dependency, as the crate has none and CI
  runs `--offline`. Each bench reports the median of nine samples of at least 20 ms each, and the allocations per call
  from a counting global allocator. It also checks that a repeated call gives the same answer.
  `seat::group_count=seat_rule/*` asserts in its timed loop that the direct count and the seat rule over the
  rows agree.
- `tools/kernel_bench_ab.py BEFORE AFTER` runs each bench at each size in a process of its own (`=name`
  runs one bench and only its own section's setup), the two binaries alternating, three rounds, and prints
  the median of the medians. In one shared process, one bench's setup moved another's time by 15%, by
  leaving the heap in a different state (`seat::voices`, whose code is unchanged, read 0.83×). Isolating
  each bench removed that.
- BEFORE is the library at `c20faf5` (= `kernel-v0.1.0`, plus the bench), built with this same harness less
  the benches of functions it does not have. AFTER is this branch's head. The final table ran pinned to one
  core (`taskset -c 31`) on a shared 32-core host. The load average is in the table's caption.
- `perf` is not permitted on this host (`perf_event_paranoid`). The profile is timing by part plus allocation
  counts. Each part of a path is its own bench (`members_at`, `voices`, `left_in_past`, `Seats::new`,
  `holders`, ...), so the share each part takes is read off the table.

    cargo run --release --example persist_paths -- --sizes 3,16,128     # one binary
    python3 -I tools/kernel_bench_ab.py before/persist_paths after/persist_paths --sizes 3,16,128,1024

## 2. Before and after

AFTER is `e3e2fa0`, the branch after the review's changes.

| bench | 3 | 16 | 128 | 1024 |
|---|---|---|---|---|
| `graph::Graph::new` | 196 ns → 160 ns (**1.22×**) | 1.2 µs → 552 ns (**2.19×**) | 16.8 µs → 5.9 µs (**2.87×**) | 244.9 µs → 66.2 µs (**3.70×**) |
| `graph::Graph::new+ancestors(last)` | 242 ns → 207 ns (**1.17×**) | 1.4 µs → 695 ns (**2.07×**) | 17.1 µs → 6.2 µs (**2.75×**) | 259.8 µs → 71.4 µs (**3.64×**) |
| `seat::seat_rule/ballot/majority` | 4.5 µs → 3.4 µs (**1.32×**) | 24.3 µs → 16.1 µs (**1.51×**) | 290.2 µs → 164.6 µs (**1.76×**) | 2.9 ms → 1.5 ms (**1.97×**) |
| `seat::seat_rule/ballot/founder_only` | 4.5 µs → 3.2 µs (**1.38×**) | 23.2 µs → 15.4 µs (**1.51×**) | 273.6 µs → 164.0 µs (**1.67×**) | 2.6 ms → 1.3 ms (**2.05×**) |
| `seat::seat_rule/ballot/unanimous` | 4.8 µs → 3.5 µs (**1.35×**) | 25.2 µs → 16.9 µs (**1.49×**) | 302.3 µs → 170.9 µs (**1.77×**) | 2.9 ms → 1.4 ms (**2.06×**) |
| `seat::group_count/majority` | — → 60 ns | — → 183 ns | — → 1.3 µs | — → 9.6 µs |
| `seat::group_count+sets/majority` | — → 163 ns | — → 548 ns | — → 4.4 µs | — → 34.9 µs |
| `seat::group_count=seat_rule/majority` | — → 3.6 µs | — → 16.4 µs | — → 161.1 µs | — → 1.4 ms |
| `seat::group_count/founder_only` | — → 32 ns | — → 37 ns | — → 39 ns | — → 39 ns |
| `seat::group_count+sets/founder_only` | — → 123 ns | — → 325 ns | — → 2.1 µs | — → 17.1 µs |
| `seat::group_count=seat_rule/founder_only` | — → 3.3 µs | — → 16.7 µs | — → 156.1 µs | — → 1.3 ms |
| `seat::group_count/unanimous` | — → 110 ns | — → 436 ns | — → 3.6 µs | — → 26.9 µs |
| `seat::group_count+sets/unanimous` | — → 227 ns | — → 882 ns | — → 7.8 µs | — → 59.6 µs |
| `seat::group_count=seat_rule/unanimous` | — → 3.8 µs | — → 16.6 µs | — → 172.1 µs | — → 1.5 ms |
| `seat::members_at` | 2.5 µs → 1.5 µs (**1.65×**) | 13.7 µs → 8.2 µs (**1.68×**) | 172.5 µs → 94.7 µs (**1.82×**) | 1.5 ms → 826.4 µs (**1.80×**) |
| `seat::voices` | 169 ns → 177 ns (0.96×) | 467 ns → 562 ns (0.83×) | 4.4 µs → 5.2 µs (0.85×) | 35.0 µs → 37.2 µs (0.94×) |
| `seat::left_in_past` | 10 ns → 12 ns (0.87×) | 16 ns → 17 ns (0.93×) | 111 ns → 115 ns (0.96×) | 1.3 µs → 1.2 µs (**1.05×**) |
| `seat::met` | 3 ns → 1 ns (**3.50×**) | 2 ns → 1 ns (**3.57×**) | 3 ns → 1 ns (**3.75×**) | 3 ns → 1 ns (**3.50×**) |
| `seat::Seats::new` | 2.4 µs → 1.1 µs (**2.15×**) | 10.6 µs → 4.9 µs (**2.17×**) | 109.4 µs → 60.2 µs (**1.82×**) | 953.3 µs → 538.5 µs (**1.77×**) |
| `seat::Seats::new/one_offer_seats_all` | 1.7 µs → 684 ns (**2.49×**) | 19.6 µs → 5.1 µs (**3.84×**) | 1.4 ms → 76.1 µs (**18.17×**) | 88.4 ms → 779.8 µs (**113.42×**) |
| `seat::Seats::holders` | 436 ns → 221 ns (**1.98×**) | 1.5 µs → 1.1 µs (**1.38×**) | 15.3 µs → 12.7 µs (**1.20×**) | 104.5 µs → 87.9 µs (**1.19×**) |
| `seat::Seats::one` | 168 ns → 106 ns (**1.59×**) | 877 ns → 455 ns (**1.93×**) | 8.9 µs → 3.9 µs (**2.30×**) | 77.9 µs → 33.2 µs (**2.35×**) |
| `owner/conclude+Seats::holders` | 2.9 µs → 2.4 µs (**1.21×**) | 15.4 µs → 11.5 µs (**1.34×**) | 197.7 µs → 115.6 µs (**1.71×**) | 3.2 ms → 1.0 ms (**3.12×**) |
| `owner/Seats::new+one` | 962 ns → 666 ns (**1.44×**) | 6.6 µs → 3.7 µs (**1.81×**) | 80.3 µs → 52.1 µs (**1.54×**) | 1.5 ms → 535.7 µs (**2.77×**) |
| `trust::reaches/hit` | 516 ns → 513 ns (**1.01×**) | 742 ns → 728 ns (**1.02×**) | 3.2 µs → 3.3 µs (0.97×) | 321.9 µs → 322.8 µs (**1.00×**) |
| `trust::reaches/miss` | 887 ns → 880 ns (**1.01×**) | 2.3 µs → 2.2 µs (**1.05×**) | 16.9 µs → 16.8 µs (**1.01×**) | 396.1 µs → 392.6 µs (**1.01×**) |
| `trust::honours` | 541 ns → 530 ns (**1.02×**) | 1.9 µs → 1.8 µs (**1.02×**) | 16.5 µs → 16.4 µs (**1.00×**) | 368.3 µs → 361.4 µs (**1.02×**) |
| `derived::reach/5` | 1.4 µs → 964 ns (**1.47×**) | 5.5 µs → 3.4 µs (**1.60×**) | 33.3 µs → 17.6 µs (**1.89×**) | 437.3 µs → 226.2 µs (**1.93×**) |
| `trust::EdgeIndex::reaches/hit` | — → 661 ns | — → 756 ns | — → 1.0 µs | — → 23.4 µs |
| `trust::EdgeIndex::reaches/miss` | — → 1.1 µs | — → 2.1 µs | — → 4.6 µs | — → 28.4 µs |
| `trust::EdgeIndex::new` | — → 333 ns | — → 1.4 µs | — → 14.2 µs | — → 188.4 µs |
| `line::settle` | 410 ns → 428 ns (0.96×) | 2.6 µs → 2.8 µs (0.94×) | 39.0 µs → 39.9 µs (0.98×) | 433.8 µs → 436.6 µs (0.99×) |
| `line::void` | 696 ns → 714 ns (0.98×) | 3.9 µs → 4.1 µs (0.96×) | 48.8 µs → 48.5 µs (**1.01×**) | 517.7 µs → 522.0 µs (0.99×) |
| `seat::Seats::tips` | 671 ns → 24 ns (**27.85×**) | 3.0 µs → 25 ns (**119.87×**) | 42.0 µs → 26 ns (**1647.60×**) | 1.6 ms → 26 ns (**62391.42×**) |
| `head::View::new` | 1.6 µs → 1.6 µs (0.98×) | 12.6 µs → 12.5 µs (**1.00×**) | 229.0 µs → 235.1 µs (0.97×) | 2.3 ms → 2.3 ms (**1.02×**) |
| `head::View::answers` | 3.5 µs → 3.6 µs (0.97×) | 52.5 µs → 54.4 µs (0.97×) | 2.7 ms → 792.0 µs (**3.36×**) | 164.2 ms → 42.1 ms (**3.90×**) |
| `head::View::settled(one act)` | 219 ns → 223 ns (0.98×) | 615 ns → 634 ns (0.97×) | 3.7 µs → 1.6 µs (**2.31×**) | 29.3 µs → 11.8 µs (**2.48×**) |
| `head::purge` | 4.4 µs → 4.4 µs (**1.01×**) | 48.1 µs → 47.0 µs (**1.02×**) | 1.7 ms → 814.2 µs (**2.07×**) | 91.8 ms → 30.7 ms (**2.99×**) |
| `window::rule/conclude` | 21.1 µs → 14.9 µs (**1.42×**) | 122.3 µs → 78.5 µs (**1.56×**) | 1.4 ms → 834.9 µs (**1.67×**) | 15.5 ms → 10.3 ms (**1.51×**) |
| `window::outcome` | 8.3 µs → 5.6 µs (**1.48×**) | 48.7 µs → 28.8 µs (**1.69×**) | 525.6 µs → 294.2 µs (**1.79×**) | 4.2 ms → 2.5 ms (**1.72×**) |
| `key_end::live` | 35 ns → 36 ns (0.97×) | 74 ns → 56 ns (**1.32×**) | 206 ns → 205 ns (**1.00×**) | 1.2 µs → 1.2 µs (**1.00×**) |
| `key_end::ended` | 35 ns → 36 ns (0.98×) | 76 ns → 57 ns (**1.33×**) | 189 ns → 191 ns (0.99×) | 1.2 µs → 1.2 µs (**1.00×**) |
| `key_end::retained` | 383 ns → 226 ns (**1.69×**) | 10.1 µs → 2.2 µs (**4.60×**) | 354.5 µs → 37.8 µs (**9.38×**) | 22.5 ms → 457.2 µs (**49.22×**) |
| `key_end::conclude` | 1.1 µs → 800 ns (**1.35×**) | 8.7 µs → 5.8 µs (**1.51×**) | 117.5 µs → 55.7 µs (**2.11×**) | 2.5 ms → 627.7 µs (**3.97×**) |

Three rounds, each bench in a process of its own, both binaries pinned to core 31. The load average was 12–16
at the start and 7–13 at the end, on 32 cores, with `check.sh` running alongside on other cores. Both binaries
alternate within each round, so the load falls on both.

A cell is before → after (before / after). A bench only AFTER has (a new entry point) shows "—" before.

At 16,384:

| bench | 16384 |
|---|---|
| `graph::Graph::new` | 4.5 ms → 1.7 ms (**2.70×**) |
| `graph::Graph::new+ancestors(last)` | 4.9 ms → 1.9 ms (**2.53×**) |
| `seat::seat_rule/ballot/majority` | 182.6 ms → 44.7 ms (**4.08×**) |
| `seat::group_count/majority` | — → 149.4 µs |
| `seat::group_count+sets/majority` | — → 613.4 µs |
| `seat::members_at` | 34.2 ms → 21.6 ms (**1.59×**) |
| `seat::voices` | 521.2 µs → 562.2 µs (0.93×) |
| `seat::Seats::new` | 23.2 ms → 16.0 ms (**1.45×**) |
| `seat::Seats::new/one_offer_seats_all` | 21.59 s → 16.5 ms (**1305.23×**) |
| `seat::Seats::one` | 1.1 ms → 503.0 µs (**2.23×**) |
| `owner/conclude+Seats::holders` | 791.6 ms → 78.7 ms (**10.06×**) |
| `owner/Seats::new+one` | 373.3 ms → 24.0 ms (**15.58×**) |
| `trust::reaches/miss` | 4.2 ms → 3.8 ms (**1.10×**) |
| `derived::reach/5` | 6.8 ms → 7.0 ms (0.98×) |
| `trust::EdgeIndex::reaches/miss` | — → 7.8 µs |
| `line::settle` | base not run (setup over 150 s) → 12.7 ms |
| `seat::Seats::tips` | base not run (setup over 150 s) → 21 ns |
| `window::outcome` | 98.0 ms → 56.0 ms (**1.75×**) |
| `key_end::retained` | 11.71 s → 16.2 ms (**722.98×**) |
| `key_end::conclude` | 513.8 ms → 129.0 ms (**3.98×**) |

One round, pinned as above. Notes on three cells:
- `one_offer_seats_all`: the base did not finish within the 150 s process limit in this run. The cell shows
  its 21.6 s per call from an earlier run of the same base binary.
- `line::settle` and `tips`: the section's setup, `conclude` over a ledger of 16,384 counted acts, takes
  about 2.5 minutes in the after binary. The base was not run past 150 s, so neither function was measured on
  it. The after binary's `settle` was measured alone: 12.7 ms per call.

The sub-microsecond cells (`seat::met`, `seat::left_in_past`, `key_end::live`, `key_end::ended`) are code
this branch leaves byte for byte as it was. Their ratios at that scale are timer and host noise of ±30%. Where
a cell below 1.0 is code this branch changed, it is listed in section 6.

## 3. Root causes

**The vote count (persist's `consensus_eval`, 16–66×).** The adapter presented a ballot as rows: a founding
row, one offer per member, the roster version and the counted row. It then concluded them all. For the
counted row, `seat_rule` ran `members_at`. That function builds a fresh `Graph` over the head's past, a fresh
`Seats` walk (with a `Cut` solved over it and the reader's line voided), then `holders` and `tips`. After it
come `left_in_past` and `voices`, each a scan of every row. At a roster of 1,024 that was 24,189 allocations
and 2.5–2.9 ms here (persist measured 2.6 ms); at a roster of three, 111 allocations and 4.5 µs (persist's 8 µs
floor). The count itself is a set intersection and a comparison. Inside the walk:

- `Seats::new` read every concluded row for an acceptance of each (offer, key) it seated: offers × rows.
  It also built the offer's signer set (`seat::signers`, a `BTreeSet` of cloned keys) once per key, which is
  quadratic when one offer seats every member (persist's first ballot shape).
- `Cut::status` read a row's slots (`on_slots`: persist's `NoCut` allocates a `String` and a set per call)
  on every `counts(i)`, even when no row is a cut. It is called for every offer, acceptance and tip.
- `Seats::tips` compared every pair of counted acts (`Graph::frontier`) and recomputed on every `holders`,
  `stands` and `tips_common` call. `tips_common` also rebuilt a graph and a walk per tip on every call.
- `Graph::new` kept its id index as a `BTreeMap` (an id copied into a tree node per row) and one `Vec` per
  row for its names. `Bits::iter` tested all 64 bits of every word.

**The other paths (1.1–1.7×).** In persist's production build the kernel is called from `src/kernel/` only:
`consensus` (now a direct count), `owner` (a `conclude` and a `Seats` over the node's few bindings) and the
trust edge leg (a `conclude`, `fold_default` and a one-hop `reaches`). `held_head` calls it only in a test
build (`kernel::witness::held_head` compiles to nothing otherwise), and `reachable_under_scope` (the
delegation walk bench) does not call it. At persist's sizes the kernel's share of `owner_of` is about 3 µs
(`owner/conclude+Seats::holders` at 3) of a 25 µs regression. Of `trust_root_valid`'s +145 µs to +1 ms, an estimate
from `key_end::conclude` at 128 (a `conclude` over 256 rows, about 60 µs before this branch) puts it under
60 µs at 128 rows. The rest is in the adapter (each row re-read as a `KRow` with its strings copied,
`RowId::of_hash` per row and again for `live_edges`, `direction_denied_ids`) or is noise. Persist should
measure those paths as an interleaved A/B in one binary before reading them as a kernel cost.

**Elsewhere, at scale.** `key_end::retained` read `ended` for each row's key (a scan of every row) per row:
quadratic. `head::View` scanned every entry for an act's receipts and cuts, once per answer per act. Each window
row walked the head's seats once per scope it read (concluder, counted, `moderate`, each clause's).
`derived::reach` copied the whole set and read every edge at every step.

## 4. What each change does, and why the answer is the same

| Change | Before | After | The same answer because |
|---|---|---|---|
| `seat::group_count` (new; `seat_rule`'s `Conf::Group` arm calls it) | the count inline in `seat_rule`, reachable only through rows | the count over a roster the caller resolved: `GroupCount { policy, offer, to, members, voices, need }` and a weight | it is the code of that arm, moved; the arm calls it. Tested against the seat rule over the ballot's rows and against the count as first written, 40,000 ballots, every policy met and missed |
| `group_count`'s member voices | a `BTreeSet` built of the voices that are members | `BTreeSet::intersection` of the two sets, counted (weighted: summed, ascending as before) | the same keys, each once, in the same order |
| `group_count`'s answer type and weighted sum (after review) | `bool`; the weights summed in `u64` | `Option<bool>`, `None` for `Policy::Ranked` only; the sum in `u128` | `seat_rule` answers a ranked count before it reaches the count, so it never reads `None`. The `u64` sum wrapped in a release build (before this branch too), so a further heavy voice could unmeet a count, against `SeatCount.weighted_mono`. A sum of 2^64 or more is the one input whose answer changes, now as the theorem states |
| `seat::count_members` (new; `seat_rule` reads it) | inline in `seat_rule` | the set `seat_rule` counts over: `members_at` at every head less `left_in_past` of the row | the code of that step, moved; tested against `members_at` minus `left_in_past` |
| `seat::conclude` (new) | | the seat rule over one pass, `members_at` kept per (sorted heads, object, scope) for that pass; a head outside the row's concluded past is answered, not kept | within one pass the concluded rows in a head's past are fixed before any row naming it is read; tested against `layers::conclude` with `seat_rule` over generated graphs, with plants for a key that drops the scope or a head |
| `layers::Past::get`; `members_at`'s head test | `contains` over `p` | binary search | `p` is in index order, ascending, as `conclude` builds it (its documented contract) |
| `seat::voices` (after review) | every row of the past read for a cosignature the row names | only the rows the counted row names, each by `Past::get` | a voice from a cosignature must be a row the counted row names, and `get` gives exactly the concluded ancestor with that id; tested against the voices as first written, over generated cosignatures named or only in the past |
| `Cut::status` | the slots read on every call | each row's status kept once asked (`OnceCell`); no cut among the concluded rows: every concluded row counts, slots unread | the cut is solved when built, so a status never changes; a concluded row that cuts a slot is among the cuts, so with none, `voided` finds nothing |
| `Seats::new` | every concluded row read per (offer, key); a signer set per key; each unseat's object copied per check; keys copied through the walk | acceptances indexed by signer, withdrawals by target; `signed_by` (or one signer set per offer seating more than 8); each unseat's object read once; keys borrowed until they enter a live seat | the indexes hold exactly the rows the scans filtered for; `any` over them is order-free |
| `Seats::tips`, `tips_common` | recomputed per call | kept per object (and scope) once asked | the seats are fixed when built; no reader enters either (the reader's line is in `stale`) |
| `seat::members_at` | each row's past tested by two id lookups and `in_past` | the head's past taken once from the closure (`ancestors`), by index | `in_past(a, b)` is `ancestors(b).has(a)` |
| `seat::members_in_scopes` (new); `window::rule`, `outcome` | one graph and seat walk per scope read | one per head, read for every scope the table names; a clause over a scope named `all` or `others` is left lazy, as its cache name collides with `Base::All`/`Others` | the same `holders` of the same walk |
| `Graph::new`, `idx` | `BTreeMap` index, a `Vec` per row's names | (id, row) pairs sorted in one buffer; names in one buffer (`named(i)` a slice) | the first row of each id is kept, in the order given; tested with duplicate ids against the eager closure |
| `Graph::frontier` | every pair | up to 16 rows pairwise; more by one walk down from all of them, through rows no lower than the lowest, taking a known past whole | a row of `of` is in another's past iff that walk reaches it; tested against the pairwise frontier, before and after pasts are known |
| `Bits::iter` | 64 tests per word | one step per set bit | |
| `key_end::retained` | `ended` per row (all rows each) and a whole past per seed | each key's end read in one pass; one walk marks every seed's past | `ended(k)` is "revoked by now, or no record of k open past now"; the union of pasts is what one walk reaches |
| `head::View` | every entry scanned per act and answer | above 64 entries: the entries by the act they name and the ids answers name, each one sorted buffer built in `new` (so `View` stays `Send + Sync`), and `tips` reads the named ids per call; member sets above 32 members; `acked` kept. Its fields, and `Seats`', are read through methods: both are snapshots whose answers are kept once asked | the indexes hold the entries the scans filtered for, in the same (id) order; tested by every purge history padded past 64 entries against itself unpadded, and by generated stores of every kind read through the indexes against the same view scanning (a unit test) |
| `trust::EdgeIndex` (new) | | the edges sorted by source once, for repeated walks | the walk of `reaches`, each key's edges read as their run in the index, in edge order |
| `derived::reach` | the set copied and every edge read at every step | a layered walk over the edges sorted by source | a key enters at the first step that reaches it; only new keys are read at the next |
| `line::settle` | `live.contains` per act of the reader's line | `cut_counts(i)` | `own_line` returns counted acts on the object only |

Kept as it was, after the A/B showed the change slower: `trust::reaches` (borrowed keys cost a pointer per map
comparison, more than the copies saved; sorting the edges inside one walk cost more than a short walk's
scans), and `key_end::live`/`ended` (one pass lost the early exit of `records().any`).

**Correctness.** After each change: `cargo test --release`. It now runs 27 conformance runs and the lib's
unit tests. The 18 runs the crate carried hold 937,355 cases against the Python models, the Lean worked worlds
and TLC's states. The nine new ones are in `tests/fast_paths.rs` and `tests/purge.rs`: each tests a faster path
against the definition it replaced, kept there as the oracle. Final: 7,084,046 cases, 0 disagreements.

`check.sh` on `e3e2fa0`: all 17 steps passed. That covers 602 Lean theorems, the model checks, the
no_std and wasm builds (0 dependencies), conformance (27 runs, 7,091,573 cases, 0 disagreements), 46 of 46
plants caught, and TLC (5 specs, each with its plant caught). The crate builds on MSRV 1.89, and `fmt --check`
and `clippy --all-targets -D warnings` are clean.

`tools/kernel_crate_plants.sh` has 46 plants. Fifteen are the plants it had; the two count plants follow the
code into `group_count`. The `open:self_admit` removal line, which the first of them used to hit, is planted
on its own. Thirty are new, one per faster path: a cache that answers for another object, scope or head;
an index filed under one key or never built; the frontier's walk cut short; the no-cut shortcut taken with
cuts; `members_at` reading unconcluded rows; a prefilled window scope that keeps the opener in `others` or lets
a scope named `all` take `Base::All`'s name; a weighted sum that wraps; a ranked count answered as a count; `voices` counting a cosignature the row does
not name.

The review found four of these unplanted or uncaught (the view's answer index, the two window prefill
guards, and `members_at` over unconcluded rows). Each now has a plant and a test that catches it. The first
full run after the review caught 44 of 45: a members cache keyed by its first head alone changed no
conclusion the generated worlds read. A lib unit test now reads the cache at every set of heads, in random
order, against the uncached reads, and catches it. The view
and window tests are unit tests: they compare the indexed or prefilled path with the scanning or lazy one in
the same build, over generated stores and windows.

No proof or model changed. `FORMAL_GAPS.md` lists `group_count` under the theorems of the counts it is the
code of, correct given members equal to `count_members` and voices equal to `voices`. `SeatCount`'s `yes`
counts over a list, which equals the Rust's set count when the list has no duplicates and holds every voice.
`wsum` is over `Nat`; the Rust sums in `u128`. The file also lists `count_members` and `seat::conclude` under
`members_at`'s theorems, `trust::EdgeIndex` under `reaches`', and the frontier's walk under the closure's
cases.

## 5. What persist's adapter should call

- **The vote count.** Replace `consensus::count`'s own arithmetic with `ciris_kernel::seat::group_count`:

  ```rust
  use ciris_kernel::seat::{group_count, GroupCount};
  let c = GroupCount { policy: seat_law().policy.get(arm.word).copied(), offer: is_offer,
                       to: to.as_slice(), members: &mem, voices: &v, need: arm.need };
  group_count(&c, |k| arm.weights.iter().find(|(w, _)| w == k).map_or(0, |(_, x)| *x))
      .expect("persist's six arms have no ranked count")
  ```

  `group_count` answers as the seat rule only for input read as the seat rule reads it (its `# Contract`):
  - `mem` is the members at **every** head the counted row names (from concluded rows only), **less every
    key whose own leaving is in the counted row's past**. That is a function of the head and the row, not of
    the head alone.
  - `v` is the row's signer, its cosigners, and the cosignatures it names that name every head.
  - `to`, `mem`, `v` and the weights are in one key space: if persons are counted, each in `to` once.

  An adapter that holds the rows takes `mem` from `seat::count_members(p, law, spec)` and `v` from
  `seat::voices(r, p)`. Persist's `count` builds `mem` from the roster it resolved for the ballot. That is
  right only while that roster already leaves out every member whose own leaving is in the counted row's past.
  The member's own leaving by a removal its subject alone signs stays the adapter's shortcut, as now.

  `group_count` is the code `seat_rule` runs for the `Conf::Group` arm, so the I1844 witness (`admits_by_rows`)
  keeps comparing it with the rows. At 1,024 members it takes 9.6 µs with the sets given (0 allocations), or
  35 µs building them per call from the roster's key slices. The seat rule over the rows took 2.9 ms before
  and 1.5 ms after (both under this run's load). At three members: 60 ns, against 4.5 µs → 3.4 µs.
- **The floor beyond that is the adapter's.** Building `mem` from the eligible seats per ballot costs more than
  the count (`group_count+sets`). A cache may hold the members at a head (`members_at`), which is a function
  of the head alone (CC 2.7.8). It must still subtract the leavings in each counted row's past on every count.
  A cache of `mem` per roster version gives a different answer: the review's case is a member who withdraws
  after the version, with a unanimous offer signed by the others. `seat::conclude`, for a caller that
  concludes rows, keeps `members_at` per head within one pass and subtracts per row. Counting by interned
  person ids (`u32`) instead of 76-byte strings would take the comparison cost out of the intersection.
- **Owner and edge leg.** Unchanged calls (`conclude`, `Seats::new`, `holders`, `fold_default`, `reaches`); they
  are faster here at every size (section 2). The remaining regressions in those benches are adapter work
  (section 3).
- **Repeated trust walks over one reader's edges** (`check_federation`, a licence check per row): build
  `trust::EdgeIndex::new(&edges)` once and call `index.honours(...)`.
- **Rows concluded by the seat rule**: `seat::conclude(kept, law, spec, other, root)` in place of
  `layers::conclude(kept, |p| seat_rule(p, ...), root)`. It gives the same conclusions, with each head's
  members read once per pass.
- **Renamed or made private by this branch**: `Seats`' `recs`, `stale`, `c` and `cut`, and `View`'s `rec`, `c`
  and `v`, are now methods of the same names. Persist's `owner_holders` reads `seats.recs()`.
- **Several scopes at one head**: `seat::members_in_scopes`, one walk for all.

## 6. Cells below 1.0, and what they are

In the final run, the only cells of changed code below 0.97× are these:

| Cell | Ratio | What it is |
|---|---|---|
| `seat::voices`, every size | 0.83–0.96× | `voices` now does strictly less work: it no longer reads the whole past. Its whole remaining cost is `signers(r)`, byte for byte as before: one copy per signer (513 at 1,024) into a set, with the same allocation count. The gap held at about 10% under two different glibc malloc settings. It is not in `voices`'s instructions. **Not proven:** that it comes from the heap the bench's setup leaves, whose `conclude` now allocates about half as much. The seat rule over a ballot, which calls `voices`, is 1.3–4.1× faster |
| `line::settle` at 16, `line::void` at 16 | 0.94–0.96× | `settle` reads `cut_counts(i)` for the reader's line, no more work than before |

Byte-identical code sits at 0.87–0.96× in the same run (`seat::left_in_past` at 10–17 ns), so
about ±5% is the host's noise under that load. Every `head::View` cell is now 0.97× or better: the eager
indexes cost 0.92× at 128 entries until they became one sorted buffer each.

Found by the A/B and taken back: `trust::reaches` with borrowed keys or a sort inside the walk (0.56–0.85×),
and `key_end::live`/`ended` in one pass (0.07–0.21×). Both are the base code again (section 4).

## 7. Questions, and how the review answered them

The constitution session's review of PR #3 answered the six questions put to it:

1. Names: `GroupCount`, `group_count` and `members_in_scopes` stand. `trust::Index` is now `trust::EdgeIndex`.
2. `group_count` returns `Option<bool>`, `None` for `Ranked` only. Done.
3. `SeatCount`'s `yes` is the set count under the list condition now stated in `FORMAL_GAPS.md`.
4. The plants are agreed, plus the four the review found uncaught and one for the weighted sum. Done; ten in
   all.
5. `Past::get` binary-searches now: `p` is already documented as in index order. Done. A lazy `Past` is
   left for a separate, versioned change.
6. The members-at-head cache belongs in the kernel, scoped to one `conclude`, keyed by (sorted heads, object,
   scope), with a plant. Done as `seat::conclude`.

The holon session answered its three on the PR. They are left for a later change: incremental seat state per
offer with grow-only sets, keys interned once in the kernel's index layer, and an A/B tool that hashes each
case's answers and refuses a mismatch.

Still open:

- The review's "not this PR": `Graph::new`'s level loop does not terminate on a cycle of names. Content-addressed
  ids make a cycle impossible, but `Row` does not promise it.
