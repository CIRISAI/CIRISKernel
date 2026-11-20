# How to review and attack

## Build and run

Install Lean 4.14.0 and Python 3.12 as [`README.md`](README.md) says, then from the repository root:

```
./check.sh                                                   # everything: one line per step, exit 1 on any failure
bash proofs/build.sh                                         # the proofs alone (about 20 s)
python3 -I models/causal_kernel/check_purge.py               # one model check; see models/README.md for each
```

`proofs/build.sh` compiles the nineteen files in dependency order and fails on a compile error, a `sorry`, or an
axiom beyond `propext`, `Quot.sound` and `Classical.choice`. It prints `proofs: 19 files, 548 theorems reported,
rc=0`: 548 is the number of `#print axioms` lines the files contain, one for each theorem they print, not every
lemma. `proofs/Audit.lean` then checks every declaration of the stack the same way, printed or not, and `build.sh` fails unless its planted `sorry` and axiom are caught. Each model check compares its verdicts with a recorded file and fails on any difference, any plant not
caught, or any set that gives two answers in two arrival orders. [`models/README.md`](models/README.md) lists the
ten checks and their last lines.

## The theorems in plain words

The full table, theorem by theorem, is [`proofs/README.md`](proofs/README.md). By file, in build order:

| File | What it proves |
|---|---|
| `Order.lean` | Judging each row on arrival gives two results from one set (`Two.arrival_not_a_function`); with a rank that is a property of the row there is one solution in every order (`adm_unique`, `adm_perm`); no kernel that treats two rows alike admits exactly one (`no_symmetric_choice`). |
| `Causal.lean` | The kept set is the least set closed under the door, reached in every order (`kept_is_least`, `door_any_order`, `close_saturated`, `door_spec`, `door_perm`); the conclusion is the unique solution and final for a rule that reads no concurrent row (`conclOf_unique`, `concl_final`, `concl_new_row`); meaning is a walk from the reader's own key (`two_readers`, `no_own_edge_no_reach`, `only_withdrawals_remove`); only a removal stops a row counting (`only_removals_stop_counting`, `sign_after_removal_never_counts`); conflict by a fixed order on kinds, else both or neither (`wins_unique`, `holder_both_or_neither`, `Slot.descendant_decides`). |
| `Seat.lean` | A seat needs an offer and an acceptance; either side ends it alone; no third key does without a cut; standing is a bounded walk of live seats; each cut counts, is void or is contested (`no_offer_no_seat`, `third_key_cannot_end`, `means_is_seat_walk`, `cut_status_function`, `two_cuts_contested`). |
| `Window.lean` | A window's landing under two rules; the roster's tips: several tips give the members common to them, and two strict-majority versions of one head share a signer (`rosterOf_function`, `fork_shares_signer`). |
| `Recount.lean` | Under recount a landing that states an outcome its past does not give never stands; a landing stands only if the table gives its outcome over every answer that does not name it (`dishonest_never_stands`, `stands_is_table_over_all_not_late`, `quorum_closed_final`). |
| `Harden.lean`, `Harden2.lean`, `Harden3.lean` | The rules added after attack runs: ended keys change nothing unseen; a cosignature is a voice only at a head it names; a proposer does not end a counted offer alone; audience is not widened by one's own rows. `Harden3` holds an earlier form of the reader's line, superseded by `Reader.lean`. |
| `SeatG.lean` | A refined seat for shared offers, equal to `Seat.lean`'s exactly where no offer is shared (`standsG_eq_stands`, `Witness.unshared_not_equal`). |
| `Terms.lean` | The cut's terms as the running model gives them meet the general theorems' hypotheses; a row by a key with no seat at the head changes no cut. |
| `Reader.lean` | A reader's acknowledged line voids, for that reader, any line from below it however long; a sibling waits; a counted row counts only if what it is built on counts (`line_voids_old_fork`, `old_fork_void_for_ever`, `built_on_void`). |
| `Merge.lean` | A version naming several heads is counted over the members common to them; a merge naming a void tip is void. |
| `Consent.lean` | The one act: a relation stands when every voice it binds has consented; a seat is two consents; a count once met is final against members (`seat_is_two_consents`, `count_is_final_against_members`, `only_holder_or_cut_ends`). |
| `Carry.lean` | A row leaves its room only by its own signer's act (`nothing_leaves`, `author_carries`). |
| `RosterHead.lean` | Members at a head are a function of the head, its signatures and its past; no self-admission; one signature never removes; re-admission needs a version that lists the key again; a member's leaving binds by causal past. |
| `TwoMechanisms.lean` | A claim is the reader's one-voice consents walked; content's audience is read off roster heads; the door reads `now` and is not a function of rows (`door_not_function_of_rows`). |
| `KeyEnd.lean` | A key's liveness is a function of its own records and `now`; with the same records an ended key stays ended. |
| `Duty.lean` | A community's duty seats: conferred by a strict majority of holders (or the lone holder with the new holder's yes), withdrawn by a strict majority of the others and at least two; `Rejected` keeps three readings the law rejects, with counter-models. |
| `Settled.lean` | The result. Parts 1–2: kept and concluded are final under every later set; counting is not (`count_not_monotone`). Parts 3–7: disarming, `settled`, necessity (`final_iff_settled`), three kinds (`three_ways_final`). Part 8: the exact threshold (`ack_blocking_quorum`, `five_three`). Part 9: clean receipts, row by row (`ack_finality_future_stable`, `effect_row_settled`, `fork_stands_on_row_count`, `unclean_ack_does_not_block`). Part 10: closure and witness pairs (`closed_iff_no_witness_pair`, `pruned_view_closed`, `count_view_not_closed`). Part 11: the checkpoint (`checkpoint_resume`, `concl_ext_local`). Part 12: answers by head and the say rule (`countsAt_local`, `later_head_changes_nothing`, `say_settled_final`, `countsAt_final`, `symmetric_say_forced`, `say3_not_closed`, `say4_closed`). |

## Assumptions

1. Signatures cannot be forged.
2. A row names its parents by digest, so naming is well-founded: no row names a row that names it back.
3. An edge of the meaning walk is withdrawn only by its own signer.
4. A conclusion rule reads only the row's own causal past. Where a rule reads concurrent rows, its conclusion is
   not final, and nothing built on it is.
5. Finality by acknowledgement rests on two rules the cut as stated does not contain: the voices and count of a
   cut are those at the head the act names, and a signature on a cut is not counted against an act its signer
   cleanly acknowledged in a concurrent row (the one say rule). The text states both (CC 2.7.7); the proofs show
   what fails without each.
6. Necessity (`final_iff_settled`) assumes each voice that may cut and has not acknowledged can still sign a cut
   (`havail`). That is about keys, not rows.
7. A withdrawn receipt is treated as still blocking. Not proved.
8. A theorem is about the definitions in its file. Whether the parent's rule tables instantiate those definitions
   is measured in the parent, not proved; several theorem names ending `_function` hold by definition, and the
   content is in the theorems that say which rows can change an answer.

## Open problems

- **The least retained set.** The pruned view is sufficient; the smallest set of rows a node must keep is not
  found.
- **A withdrawn receipt.** Whether it still blocks a cut.
- **Many acts purged at once, and repeated purges.** Run (`check_purge.py` purges once and again part way), not
  proved.
- **Stubs as the store.** The proof is over views of a full store; a store holding only stubs is not modelled.
  Own end, key end and `revoked_after` over stubs are not checked.
- **`settled` in the rule language.** The parent's expression language writes eight of the nine named answers;
  `settled` is not yet among them.
- **Conclusion rules that read concurrent rows.** Not final, and not covered by `concl_ext`.
- **Revocation back to a bound by signed instant** (`revoked_after`). The kernel gives it no meaning beyond one
  node's own reading.
- **The freshness-window readings the parent states as limits** (CC 2.7.9): a freshness window `W` and clock-skew
  check, the bound on a key that has lost standing, the attach window for cosignatures, a response bounded by
  `W`, an objection counted within `W`, a reserved family's instant. Each times a window from a signed instant and
  judges it at receipt, which is neither notion of time.
- **A roster version naming several heads**, on the wire.
- **A slot held on one signature.** Nothing checks the tables for one.
- **The fork result is reader-relative.** A reader with no acknowledgement of its own is exposed to a fork by keys
  that met a past count.
- **No independent implementation and no deployment** ([`OBJECT.md`](OBJECT.md), Move 8).

## Adversarial tests already run

As theorems (each a counterexample or a rejected rule kept with its witness): `Order.Two.arrival_not_a_function`;
`Settled.Rows.count_not_monotone`; `later_seat_defeats_acknowledged`, `fork_voids_acknowledged`,
`overrule_voids_acknowledged` (what fails without the two rules); `Rows2.fork_stands_on_row_count`,
`unclean_ack_does_not_block`; `sayA_not_safe`, `sayC_not_symmetric`, `say3_not_closed`; `count_view_not_closed`,
`Rows2.unsettled_drop_has_witness_pair`; `Harden.CP.checkpoint_voids_any_answer` (`Harden3.lean`) and `Reader.depth_race` (why no
line wins by being longer); `RosterHead.Rejected.Model.later_withdrawal_changes_members`; `Duty.Rejected`;
`ruleII_never_final` (`Window.lean`: under the rule not taken, any objector reopens any landing for ever).

As plants (a rule switched off or broken; the check must catch it): `check_purge.py`, eight plants
(`drop_unsettled`, `freeze_now`, `ck_acks`, `drop_duty`, `keep_deleted`, `no_say`, `narrow_eval`,
`freeze_carried`); `check.py`, mutations of the door and of tie-breaking; `check_rosters.py`, a break per property;
`check_key_end.py`, a plant per property; `check_time.py`, a plant comparing two signers' instants.

As attacks: `check_attacks.py`, thirty-four attacks in 126 scenarios, classed HOLDS 13, CONCEDED 15, NOT
EXPRESSIBLE 6, BROKEN 0 ([`CHARACTERISTICS.md`](CHARACTERISTICS.md), fault model). The classes were written by
the authors of the rules.

## Runs in the parent repository

These checks' dependencies reach the parent's rule tables, expression language or the text of its Parts, so they
are not carried. Run them in a clone of the parent at commit `60c741e`:

| Check | Command in the parent |
|---|---|
| one door, every policy row and clock | `python3 -I formal/causal_kernel/check_door.py` |
| a shape for every family | `python3 -I formal/causal_kernel/check_shapes.py` |
| seat, window, copying, writer's keys, role shapes | `python3 -I formal/causal_kernel/check_lock.py` |
| the shared operators agree with six models | `python3 -I formal/kernel_lib/kernel_lib_check.py --check` |
| the divergence list as runnable tests | `python3 tools/check_divergences.py` |
| the expression language over the rule tables | `python3 -B tools/kx_check.py --check` |
| the screen as a function of rows | `python3 -I formal/screen/check_screen.py` |
| the election's count is order-free | `lean -M 6000 -T 200000 formal/moderator_election/Election.lean` |

## How to return a counterexample

Send four things:

1. **A set of rows**, in the kernel's row form (`_meta.row_form` of [`data/divergences.json`](data/divergences.json)
   states it: each row has `id`, `kind`, `signer`, `names`, and the fields its kind reads), or as a Python list
   built with the constructors in `models/causal_kernel/` (`seat.py`'s `offer`, `accept`, `withdraw`, `unseat`,
   `cosign`).
2. **One named question**: one of the nine named answers (KERNEL.md section 5) about one row, key or act.
3. **The verdict the kernel gives**, with the command that printed it.
4. **The verdict you claim**, and the sentence of [`kernel/TEXT.md`](kernel/TEXT.md) or the theorem it contradicts.

A counterexample to a theorem is a mismatch between its statement and the text, since the statement compiles. A
counterexample to a run is a set of rows above or outside its bound. Either is most useful with the arrival
orders tried, since an answer that depends on order is itself a failure.
