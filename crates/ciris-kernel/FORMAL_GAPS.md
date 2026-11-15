# What closes the model: the crate's formal gaps

Each public function of the crate falls in one of three classes:

- **(a)** its behaviour is stated and proved in Lean, with the theorem named. The proof is over the Lean
  definition. The Rust is tied to that definition only through the Python model's cases, which is the gap
  the last section addresses.
- **(b)** it is checked only by cases: the Python models' own, or a reference in the tests.
- **(c)** neither: unit tests only.

Lean files are in [`proofs/`](../../proofs) unless marked "parent".

## The classification

| Function | Class | Lean theorem, or what checks it |
|---|---|---|
| `layers::kept` | a | `kept_is_least`, `door_any_order`, `close_saturated`, `door_spec`, `door_perm` (Causal) |
| `layers::conclude` | a | `conclOf_unique`, `concl_final`, `concl_new_row` (Causal) |
| `layers::arrive` | a | `door_any_order`, `door_perm` (Causal) |
| `derived::wins` | a | `wins_unique` (Causal) |
| `derived::slot` | a | `holder_both_or_neither`, `Slot.descendant_decides` (Causal) |
| `derived::counts` | a | `only_removals_stop_counting`, `sign_after_removal_never_counts` (Causal) |
| `derived::live_edges`, `reach`, `means` | a | `two_readers`, `no_own_edge_no_reach` (Causal) |
| `line::settle`, `void`, `own_line` | a | `line_voids_old_fork`, `old_fork_void_for_ever` (Reader); built on: `Harden3` |
| `seat::Seats::new`, `stands` | a | `seat_is_two_consents`, `holder_first_stands`, `only_bound_voices_end` (Consent); `means_is_seat_walk`, `no_acceptance_no_seat`, `third_key_cannot_end` (Seat); `Duty.lean` |
| `seat::members_at`, `members_in` | a | `membersAt_function`, `counted_over_named_head` (RosterHead) |
| `seat::left_in_past` | a | `leaving_binds_by_past` (RosterHead) |
| `seat::voices` | a | the cosignature rule of `Harden.lean`; `countedE_sub`, `seen_counted` |
| `window::rule`, `outcome` | a | `dishonest_never_stands`, `stands_is_table_over_all_not_late`, `quorum_closed_final` (Recount) |
| `head::View::counts_at`, `settled`, `missing`, `receipts`, `carried` | a | `ack_blocking_quorum`, `say_settled_final`, `countsAt_final`, `countsAt_local`, `symmetric_say_forced`, `say4_closed`, `later_head_changes_nothing` (Settled) |
| `head::purge` | a | `checkpoint_conclusions`, `checkpoint_resume`, `pruned_view_closed`, `pruned_view_answers` (Settled), for a sufficient set |
| `key_end::live`, `ended` | a | `live_own_rows`, `live_perm`, `ended_not_live`, `ended_stays_ended` (KeyEnd) |
| `key_end::well_formed` | a | `bound_reads_row`, `live_le_ceiling` (KeyEnd) |
| `trust::reaches`, `honours` | a | `reaches_mono_budget`, `verdict_is_the_capped_walk` (TrustSet, parent); the crate's walk equals the Lean `walk` on 127,008 generated cases |
| `ranked::ranked` (no declared order) | a | `Election.free_perm`, `free_agrees` (parent) |
| `ops::sel`, `sel_before`, `group_by`, `least`, `greatest`, `min_of`, `max_of`, `one`, `count`, `sum_per`, `in_range`, `fix` | b | `kernel_lib.py` over 7,968 inputs; the six `reexpress.py` decisions over 17,886 |
| `graph::Graph` (`in_past`, `concurrent`, `frontier`, `past`, `ancestors`, `depth`, `level`) | b | the eager closure as oracle, 301,219 cases; every conformance run uses it |
| `graph::ancestor_ids` | b | `kernel_lib.ancestors` through the causal worlds |
| `derived::tally` | b | `check.py` and `check_cut.py` worlds |
| `cut::Cut` (`status`, `counts`, `holder`) | b | `check_cut.py`, 20,985 cases; 3,556 seat scenarios; 2,009 recorded-rule worlds. The fixed point is run, not proved |
| `line::versions` | b | `roster_fork` worlds and the attack tests' calls, 77,402 cases |
| `line::counted_acts` | b | through `settle` |
| `seat::Seats::holders`, `one`, `tips`, `tips_common` | b | 134 seat scenarios and 2,009 recorded-rule worlds; tips wait is run in `fork_check.py`, not proved over this function |
| `seat::seat_rule` (with the tables) | b | the 134 scenarios; parts proved (`count_is_final_against_members`, `one_signature_never_removes`, `Duty.lean`), the composite with `SeatLaw` not |
| `seat::met` | b | through `seat_rule`; `Duty.majority_iff` proves one threshold |
| `window` table reading (`at_once`, `at_close`, the target's silence) | b | the 27 adversary rows and the window scenarios |
| `head::View::window`, `answers`, `tips` | b | `check_purge.py`, 400 replays |
| `key_end::conclude_rule`, `retained`, `successor` | b | `check_key_end.py`, 5,670 worlds at six instants |
| `ranked::ranked` (declared order) | b | `reexpress.py` cases |
| `trust::Accepts::admits` | b | through `reaches` |
| `ops::rule` | c | a map lookup |
| `seat::covers` | c | unit tests |
| `seat::Obj::from_reference`, `is_identity_reference` | c | unit tests and the reference forms of the seat fixtures |
| `SeatLaw`, `WindowSpec` tables as data | c | no check that a table states what the text says, beyond the rows the models carry |

**Counts.** 19 entries in (a), 15 in (b), 4 in (c).

## The smallest statement that closes each, ranked by risk

The rank weighs how much depends on the function and how far its cases are from covering it.

| Rank | Gap | Proposed statement | Meaning |
|---|---|---|---|
| 1 | `cut::Cut` | `theorem cut_wfs (S : Rows) : let L := lfp (T S ∘ T S); L ⊆ T S L ∧ ∀ A, L ⊆ A → A ⊆ T S L → ∀ c ∈ L, c ∈ T S A` | what counts, counts whatever the undecided cuts do; together with `cut_perm : S ≃ S' → status S = status S'` it is order-free |
| 2 | `seat::Seats` with `tips_common` and the table | `theorem stands_iff_chain (law : SeatLaw) (S) (k s o) : stands S k s o ↔ ∃ ch : Chain S, ch.root ∈ roots o ∧ ch.last = (k, s) ∧ ch.len ≤ law.depth ∧ ∀ t ∈ tips S o, holds (S.past t) k s o` | a key stands iff a bounded chain of live seats leads to it and every tip seats it |
| 3 | `seat::seat_rule` composite | `theorem seat_rule_reads_past (r P P') (h : P ≈ P') : seatRule r P = seatRule r P'` and `theorem group_offer_needs_count : seatRule r P → r.conf = group → met r.policy (voices r P ∩ membersAt P r.head) (membersAt P r.head)` | the rule reads the row's past only, and a counted offer concludes only on its count |
| 4 | `window` table reading | `theorem table_outcome_monotone_close : ¬elapsed → tableOutcome .. = .open ∨ ∃ c ∈ atOnce, met c` | before its close a window gives only an at-once outcome; with `recount_reads_landing_past` it fixes what the landing may state |
| 5 | `key_end::retained` | `theorem retained_down_closed : x ∈ retained S now → y ∈ S.past x → y ∈ retained S now` and `theorem compact_answers (S now) : answers (compact S now) now' = answers S now'` for `now' ≥ now` | dropping lapsed rows changes no answer then or later (property P3a, run today) |
| 6 | `graph::Graph` | `theorem in_past_iff (G) (a b) : G.in_past a b = true ↔ TransGen G.parent a b` | the lazy, budgeted search computes the closure the Lean files reason about |
| 7 | `line::versions` | `theorem versions_perm (h : ids.Perm ids') : versions ids = versions ids'` and G3 below | a function of the set, and built on |
| 8 | `head::View::window` and the purge of an open window | `theorem purge_keeps_open (now) : window S o now = .open → whole (purge S now) o` | a window open at the checkpoint keeps its bytes, so nothing that reads now is frozen |
| 9 | `ops::least` / `greatest` | G1, G2 below | a tie is refused, and refusal means a real tie |
| 10 | `ranked::ranked` with a declared order | `theorem ranked_declared_function (h : opts fixed) : ballots.Perm b' → ranked ballots opts = ranked b' opts` | the count is a function of the ballots as a set |
| 11 | `derived::tally` | `theorem tally_two_say_nothing : (∃ v w ∈ votes k, v.choice ≠ w.choice) → k ∉ counted` | a voice that says two things says nothing |
| 12 | `seat::met` | `theorem met_atleast_iff : met (atLeast n d) y m ↔ 0 < m ∧ n * m ≤ d * y` (and one each for the others) | the integer threshold is the fraction the table states, with no rounding |
| 13 | `key_end::successor` | `theorem successor_both_or_neither : two concurrent rotations name different keys → successor = none` | property P5a, run today |
| 14 | `Obj::from_reference` | a model, not a theorem: test vectors generated from `signed_object_v2.cddl` (parent), every `hash-digest` and identity reference form, valid and not | the row-or-key reading is the CDDL's |
| 15 | tables as data | a model: a check that every `SeatLaw` and `WindowSpec` cell traces to a table cell or a quoted sentence (the parent's `family_shapes.tsv` method) | the data the kernel reads is the text's |

**Stated in Lean with `sorry`.** [`proofs/proposed/Proposed.lean`](../../proofs/proposed/Proposed.lean) holds three
statements. Lean 4.14 accepts the file, with a warning for each `sorry`. `proofs/build.sh` compiles a fixed
list of files and does not build it.

- G1 `leastNoTie_perm`: the least element does not depend on the order of the list.
- G2 `leastNoTie_none_iff`: a refused tie is a real tie.
- G3 `counts_built_on`: a version that counts has every version it extends counting.

## Tying the Rust to the Lean

| Way | What it gives | Cost | Fit to this crate |
|---|---|---|---|
| Differential tests generated from the Lean definitions | the Rust agrees with the definitions the theorems are about, case by case, to a bound | days per module: the definitions are already `Bool`-valued and many are `decide`d; a Lean `main` prints the same JSON the Python generator prints | good: the test side exists, so only a second generator is new |
| Aeneas (Charon to Lean) | a proof that the Rust is a Lean function, so the theorems transfer | months: closures, `dyn Fn`, `OnceCell`, `BTreeMap` and associated types are outside or at the edge of its subset; the crate would be rewritten to a restricted style | poor today |
| hax (to F* or Lean) | as Aeneas, with a different subset | months; its Lean back end is young | poor today |
| Verus | proofs about the Rust itself, in Rust syntax | months: every theorem proved again in a second system, not linked to the Lean | poor: two proof bases |
| Kani | bounded model checking of the Rust | days: harnesses for equivalences inside the crate (the lazy closure against the eager one, the fixed point of `fix`, `from_reference`) | good for the (b) items internal to the Rust; says nothing about the Lean |

**Recommendation: differential tests generated from the Lean definitions.** Today the Rust is compared with
the Python, and the Python is a third implementation beside the Lean. A Lean generator removes that third
party: the theorems and the cases are about one definition. It reuses the fixtures' format and the Rust
tests unchanged. The cost is one executable Lean reference per module. `Causal`, `Settled`, `Recount`,
`KeyEnd` and `TrustSet` are closest, at a few days each. The seat and the cut, ranks 1 and 2 above, need their
Lean definitions written first. Kani is worth adding beside it for gap 6, at a day or two. Aeneas is the way
to a proof, and is not worth its cost until the crate's interface settles.
