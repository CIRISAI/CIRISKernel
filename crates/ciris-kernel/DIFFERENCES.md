# Where persist and the kernel differ, and why

The crate was run beside persist on persist's own tests. A throwaway clone of persist at `8c011511` (61.3.0)
took the crate as a path dev-dependency and a thin adapter, and logged each call of the four functions
ADOPTING.md maps with the kernel's answer. The full lib suite ran with `--features sqlite`. Each class of
difference found in round 2 is settled below as one of three verdicts:

- **persist departs**: the kernel's reading is the CC text's, and persist must change;
- **adapter artefact**: the adapter gave the kernel the wrong rows; it was fixed and the class re-run;
- **kernel lacked**: CC states a rule the kernel did not have; it is now in the crate, with cases.

Persist anchors are `src/federation/` at `8c011511`. CC sections are in `CIRISConstitution/constitution/`.

## Final counts

| Function | Distinct calls | Agree | Persist departs | Other |
|---|---|---|---|---|
| `consensus::evaluate` (`consensus.rs:213`) | 429 ballots | 394 | 22 (`custom:` 2, `reverse_quorum` 20, each admitted by persist) | 13 more ballots under those protocols and one malformed (`whatever`): persist refuses them, and the kernel has no cell, so neither admits |
| `owner_of` (`admission.rs:12694`) | 1,924 | 1,723 (1,720 no owner on both sides, 3 the same owner) | 199 | 2: persist's ambiguity error, where the kernel names no owner either |
| `trust_root_valid`, edge leg (`trust_root.rs:1407`) | 199 | 199 | 0 | |
| `held_head_verdict` (`group_supersede_admit.rs:77`) | 8 | 2 | 5 | 1: a supersede whose proof names another prior, which persist refuses and the kernel does not read |

For every function where the kernel has a cell, the count of disagreements that are not a named persist
change is **zero**. The suite ran 3,394 tests passing and 4 failing. All four fail only because of the
scratch hooks: one counts directory reads, two scan the wrapped function's source, and one flags the
scratch test that signs a cosignature in a backend file. Three of them were run on the unhooked tree in
round 2 and pass there.

## The classes

| # | Class | Minimal case | Persist | Kernel (round 2 → now) | The kernel's rule | Verdict and action |
|---|---|---|---|---|---|---|
| 1 | `unanimous` removal excludes the member named (6) | members {a, b, c}; removal of b signed by a and c | admits (`consensus.rs:247`) | did not → admits | CC 3.3.4, `unanimous`: "For a **removal**, every member other than the target signs *and* those signers are a strict majority of the roster"; CC 4.5.13: "at two coincide only if the one removed consents". Lean `SeatCount.unanimous_two_removes_nobody`, `unanimous_others_remove` | **kernel lacked**: `seat::Policy::Unanimous` added, with the removal reading; cases in `tests/policies.rs`. 0 left |
| 2 | founders-only infrastructure groups (8) | `infrastructure`, `quorum:1/2`, roster {human (founder), install (founder, node-bearing)}; signed by install | does not admit (`consensus.rs:162`, `eligible`) | admitted → does not | CC 3.2 *Infrastructure does not vote*: a `node`-bearing key "MUST NOT be counted in the community's `consensus_protocol`", and the founders sign; CC 6.1.8 N1: "its own roster count at the head the row names". The kernel counts the scope the row names (`counted`) over the head it names (`RosterHead.counted_over_named_head`) | **adapter artefact**: the adapter now counts the founder scope, seating only founders that are not node-bearing. 0 left |
| 3 | one voice per person (5) | `quorum:2/3`, roster {ann, ben, dan}; removal of dan signed by ann and by ann2, a second device of ann | does not admit: one person is one voice (`PersonsAt`, `consensus.rs:105`) | admitted (two keys) → does not | KERNEL.md 7b: "One person, one voice. A tally over voices equals the count of persons"; a person's devices are one voice (CC 2.7.8, a person's keys are one roster) | **adapter artefact**: the kernel counts voices, and presenting a device as its person's voice is the adapter's job under 7b. The adapter maps each key through `PersonsAt::voice` and each seat through `seat_person`. 0 left |
| 4 | self-signed re-admission (1) | `quorum:1/2`, roster {a (founder), b}; a widening naming a, signed by a | does not admit (`consensus.rs:223`) | admitted → does not | CC 2.7.5: "no key admits itself"; CC 3.3.4 `founder_only`: "cannot re-seat itself alone". Lean `SeatCount.no_key_admits_itself` | **kernel lacked**: in `seat_rule`, a key the counted row seats or removes is no voice of the count. The Python models' cases are unchanged by it. 0 left |
| 5a | `founder_only` (53) | roster {a (founder), b}; widening of j signed by a | admits | no cell → admits | CC 3.3.4: "new members proposed-and-admitted by any active founder" | **adapter artefact**: it is one voice over the founder scope (`Policy::One`, `counted = founder`), table data the kernel already reads. 52 agreed at once. The 53rd is a founder removing itself, which persist admits as a count and CC 3.3.4 makes the member's own `membership:resignation`. The adapter now gives the kernel the resignation (a withdrawal by the member, which ends its seat alone). 0 left |
| 5b | `open:self_admit` (29) | public group {a, b, c}; widening of j signed by j | admits (`evaluate_open_self_admit`, `consensus.rs:342`) | no cell → admits | CC 4.4.3.6: "a widening naming exactly one **new** K and K signed it … a removal under this protocol runs under the CC 4.5.13 floor, never one vote"; CC 3.2: admissible only on a `public` community | **kernel lacked**: `seat::Policy::SelfAdmit` added. A seated member naming itself is not a new K, so it is a change of role and takes two voices besides the one named. Lean `SeatCount.self_admit_one_never_removes`. 0 left |
| 5c | `weighted:{rubric}` (8) | rubric `votes`, weights a 2, b 1, c 1, d 1, threshold 3; signed by a and b | admits (`eval_weighted`, `consensus.rs:395`) | no cell → admits | CC 3.3.4: "The sum of the signing members' weights must reach a threshold. Each weight and the threshold is a whole number carried on the group's signed record" | **kernel lacked**: `seat::Policy::Weighted` and `SeatRow::weights` added. Lean `SeatCount.weighted_mono`. 0 left. Persist reads weights and `threshold_fraction` as `f64` (`consensus.rs:396-425`); CC states whole numbers, so a non-whole weight or a fraction is a persist departure the tests did not exercise |
| 5d | `reverse_quorum:*` (26) | 5 members; removal signed by one | admits a removal by one member (`consensus.rs:280`) | no cell | CC 3.2: "**Not a membership rule: reverse quorum.** … It admits no one and confers no consent on anyone's behalf"; CC 4.4.3.6 lists no such arm | **persist departs**: refuse `reverse_quorum` as a `consensus_protocol`. Persist admits 20 of these ballots. CC states the reading |
| 5e | `custom:{id}` (8) | `custom:elders`, a founder and an elder sign | admits from `policy_blob.custom` (`consensus.rs:317`) | no cell | CC 4.4.3.6's protocol table has six arms (`founder_only`, `open:self_admit`, `unanimous`, `majority`, `quorum:M/N`, `weighted:{rubric}`) and no `custom:`; CC 3.3.4's "canonical kinds" are those | **persist departs**: refuse `custom:` as malformed. Persist admits 2 of these ballots. CC states the closed list in 4.4.3.6; CC 3.3.4 still calls the vocabulary "open", which the owner may wish to align |
| 5f | a malformed protocol (1) | `whatever` | unevaluable (`consensus.rs:329`) | no cell | as 5e | agree: neither admits |
| 6 | `owner_of`: the seat as two consents (199) | node N, owner O; one `delegates_to(O → N)` owner-binding, signed by O only | names O | names none | CC 3.2, *The first binding (MUST)*: "an owner-binding counts toward ownership only when the node's own key cosigned it, or the node's genesis record carries it"; CC 2.7.5: a seat is two consents (`Consent.seat_is_two_consents`) | **persist departs**: `live_owner_binding_granters` (`admission.rs:12610`) must count a binding only when N's key cosigned it (an `additional_scrubs` entry by N) or N's genesis record carries it. The adapter does not read the genesis path, so some of the 199 may be bindings a genesis record carries; none of persist's fixtures it reached builds one. Real cases were added: a binding N cosigned names O on both sides (3 calls). A binding cosigned by a different key names O in persist and none in the kernel (in the 199) |
| 7 | trust root, the edge leg (8) | user U, root R; a `delegates_to(U → R)` with no `trust:accepts` label, written after the bundle-only migration | no edge | an edge → no edge | CC 3.2 T4a: a row with no job label "is not an acceptance edge at all"; CC 3.5.1 for a superseded edge | **adapter artefact**, in three parts: the adapter now passes only the family's rows (labelled, or held as acceptance from before the label, as the directory reports); it reads `supersedes` and retractions by the fold default (CC 3.5.1, now `derived::fold_default`); and an edge whose own signer's composer wins its chain is ended. 0 left |
| 8 | the fork (by design) | lineage head H held; a supersede naming H's predecessor, or a second founding version | refuses (`group_amendment.rs:600`, `check_prev_head_names_held`) | holds it: a tip beside H, or a row waiting for the head it names | CC 2.7.8: "Two versions of one head wait as tips. The roster is then the members common to all tips, until a version naming the tips makes one head again"; CC 3.3.4 for the head a removal is counted over; `SeatWalk.holder_every_tip`, `ReaderLine.tla` | **persist departs**: hold both versions and read the roster as the members common to the tips. KERNEL_SEAMS §2.2 row 27 already names this change. A supersede whose `supersede_proof` names another prior is a contradiction inside one row, a matter of its shape, refused before the kernel; that one case is outside the kernel |

## The sibling of the acknowledged head

The crate reads CC 2.7.8 one way for both of its line modules. A sibling of the act a reader acknowledged is
void for that reader ("holds void every counted act that names an older head and is not in that head's
past"). For a reader with no acknowledgement the two wait as tips ("Two versions of one head wait as tips").
See FORMAL_GAPS.md, *The sibling of the acknowledged head*, and `Reader.sibling_by_acknowledgement`. Persist's
reader line is not among the four functions run side by side. CC 3.3.4 (`part_3_the_namespace.md:1589`)
still reads "A sibling of the acknowledged head waits as a tip" without the reader's state, and so does
KERNEL.md 8a.

## The persist changes, each with its CC sentence

1. `consensus.rs:280`: refuse `reverse_quorum:*` as a membership protocol. CC 3.2: "Not a membership rule:
   reverse quorum … It admits no one."
2. `consensus.rs:317`: refuse `custom:{id}` as malformed. CC 4.4.3.6's protocol table has no such arm.
3. `consensus.rs:396-425`: read `weighted` weights and the threshold as whole numbers, and refuse
   `threshold_fraction`. CC 3.3.4: "Each weight and the threshold is a whole number carried on the group's
   signed record."
4. `admission.rs:12610`: count an owner-binding only when the node's own key cosigned it, or the node's
   genesis record carries it. CC 3.2, *The first binding (MUST)*.
5. `group_amendment.rs:600` and `group_supersede_admit.rs:77`: hold a version that does not name the held
   head, as a tip or a waiting row, and read the roster as the members common to the tips. CC 2.7.8.

## What the kernel gained

- `seat::Policy::Unanimous`, `SelfAdmit` and `Weighted`, and `SeatRow::weights`.
- In `seat_rule`, no key admits itself: a key the counted row seats is no voice of its count. On a removal the
  member removed is a voice unless the policy's own text excludes it, as `unanimous`, `open:self_admit` and the
  duty withdrawal do (CC 2.7.5; the Constitution's ruling of 2026-11-23).
- `derived::fold_default` (CC 3.5.1).

Each has cases from its CC sentence: `tests/policies.rs`, 24 cases, and `tests/fold_default.rs`, the four
rules and every order of six rows. Each also has a plant: `tools/kernel_crate_plants.sh`, 15 of 15 caught.
The Python models' 934,667 cases are unchanged by them.

## What was not verified

- The genesis-record path of CC 3.2's first binding, for `owner_of`.
- Persist's `weighted` with non-whole weights, which no persist test reached.
- That the 13 non-admitted `custom:` and `reverse_quorum` ballots fail for the CC's reason and not another.
- Postgres: only `--features sqlite` was run.
