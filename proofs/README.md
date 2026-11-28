# `proofs/` — what a node concludes is a function of the rows it holds, with no rank

> This folder is `formal/causal_order` of the parent specification at commit `60c741e`, carried unchanged: the nineteen `.lean` files are byte-for-byte the parent's, `build.sh` differs only in the label of its last line, and this README only in its title, file pointers and the run line.

**The question.** Two nodes are offered the same signed rows in different orders. Do they conclude the same?
A node that judges each row as it arrives, against what it has admitted so far, does not. The question is what
rule makes the answer yes without a sequencer, a shared clock or a ranking by signed instant.

**The answer.** Three layers over the rows a node was offered.

| Layer | Reads | Property |
|---|---|---|
| kept | the row alone, and whether the rows it names are kept | the least set closed under the door; the same for every arrival order |
| concluded | the row against its ancestors, the rows it names and theirs | the only solution of its equation, negation and counts allowed; final once the row is kept |
| derived | conclusions over a set of rows: a slot, a count, a conflict, what a row means to this reader | a function of the kept set and the reader's own key |

A row names the rows it extends or answers by digest. That is the only order. Two rows where neither names
the other are concurrent, and a rule that treats them alike names both or neither. A row that names both
may decide between them.

Every reader is its own seed. A row means something to a reader when it is concluded and a bounded walk of
live edges from the reader's own rows reaches its signer. Meaning is lost only through a withdrawal, by its
own signer, of an edge on that walk.

A removal by others reaches the rows of the removed signer that are not in its past. A row is in the past of
a removal when a chain of rows leads from the removal back to it: an acknowledgement, a census, a roster
version, a reply. No instant is compared.

**What is proved.** `Order.lean` (the rank case and the failure of judging on arrival), `Causal.lean` (no
rank), `Seat.lean` (standing as one shape, and the cut), `Window.lean` (a window's signed outcome under two rules,
and the roster's tips), `Recount.lean` (the window's rule as taken) and `Harden.lean`, `Harden2.lean`,
`Harden3.lean` (the rules added after the kernel was attacked), and `SeatG.lean`, `Terms.lean`, `Reader.lean`,
`Merge.lean` (the refined seat, the cut's terms, a reader's own line and a version naming several heads), and
`Consent.lean` (the one act beneath the seat), `Carry.lean` (a row leaves its room only by its own signer's act), `RosterHead.lean` (the members at the head a counted row names) `TwoMechanisms.lean` (claim and content carried by consent; the door and consent apart), `KeyEnd.lean` (a key's own end, read from its records and now), `Duty.lean` (the duty seat of a community) and `Settled.lean` (which answers no later row changes, and what makes a count one of them). Core Lean 4.14, no Mathlib, no `sorry`, no axioms beyond core.

| Theorem | What it says |
|---|---|
| `Order.Two.arrival_not_a_function`, `Order.Roster.standing_arrival` | judging on arrival gives two results from one set; on a roster of eight rows, three results from three orders, and in one a removed member keeps standing |
| `Order.adm_unique`, `Order.adm_perm` | with a rank that is a property of the row, any rule has one solution and it is the same for every order |
| `Order.no_symmetric_choice` | no kernel that treats two rows alike admits exactly one of them |
| `Causal.kept_is_least`, `door_any_order`, `close_saturated`, `door_spec` | the kept set is the least set closed under the door; any order with waiting ends at it; on a finite list the door stops within one step for each row |
| `Causal.concl_function`, `conclOf_unique` | the conclusion is a function of the kept set and the only solution of its equation |
| `Causal.concl_final`, `concl_new_row` | a rule that reads no concurrent row never changes a kept row's conclusion; a new row reaches only itself, its descendants, and rows in concurrent conflict with those |
| `Causal.holder_both_or_neither`, `Slot.descendant_decides`, `Slot.two_decisions_empty` | a contested slot is empty under a symmetric rule; a row naming both claims decides it; a second, concurrent decision empties it again |
| `Causal.means_function`, `two_readers`, `no_own_edge_no_reach` | meaning is a function of the offered set and the reader's key; two readers differ only through rows of their own; a reader with no edge of its own reaches only itself |
| `Causal.acceptance_gives_meaning`, `only_withdrawals_remove` | the reader's later acceptance gives meaning to rows already kept; no row but a withdrawal removes meaning from any row for any reader |
| `Causal.reaches_standing_irrelevant` | with an edge withdrawn only by its own signer, reach never depends on reach through negation |
| `Kernel.no_offer_no_seat`, `no_acceptance_no_seat`, `one_row_only_to_self` | a seat needs two voices, the conferrer's offer and the holder's acceptance; one row is both voices only when a key seats itself |
| `Kernel.Consent.silent_voice_not_bound`, `unbound_rows_change_nothing`, `only_bound_voices_end` | a relation stands when every voice it binds has consented; nobody is bound by the rows of others, rows by an unbound voice change nothing, and only a bound voice's own withdrawal or a cut ends it |
| `Kernel.Consent.one_voice_one_row`, `two_voices_two_rows`, `seat_is_two_consents`, `holder_first_stands` | with one voice bound one row is enough; with two it is two rows, one naming the other, in either order; the seat conferred by one key is exactly that act with the conferrer's row first |
| `Kernel.Consent.count_needs_holder`, `one_voice_is_not_a_count`, `nonmember_rows_change_nothing`, `count_of_one_is_one_row` | where a body places a duty its consent is a count of its members' signatures on the row; the holder's own yes is still needed, one voice is never a count of two, non-members change nothing, and a body of one is the one-key case |
| `Kernel.Consent.count_is_final_against_members`, `only_holder_or_cut_ends`, `holder_still_ends_its_own` | a count once met is final against every later row, withdrawals included; a counted duty ends only by its holder's own withdrawal or a cut |
| `Kernel.RosterHead.membersAt_function`, `standing_final` | the members at a roster head are a function of the head, the signatures it carries and its past, and no concurrent or later row changes them |
| `Kernel.RosterHead.counted_over_named_head`, `rows_outside_change_nothing` | whether a version stands is decided by the members at the heads it names and the signatures on it, and rows outside its past change nothing |
| `Kernel.RosterHead.no_self_admission`, `outsiders_admit_nothing` | a key that is not a member at the heads a version names gives no voice to its count, and keys outside the roster admit nobody however much they sign |
| `Kernel.RosterHead.removed_voice_does_not_count`, `readmission_needed` | a key a version leaves out is no voice of a version naming it, and further down the line is a member only if a version counted without it lists it again |
| `Kernel.RosterHead.leaving_binds_by_past`, `left_head` | a member's own leaving is a fact for the rows that have it in their past and for no others, as a removal is |
| `Kernel.RosterHead.Retro.retro_agrees`, `Retro.Model.retro_reaches_back` | the rejected reading through every held withdrawal agrees where each leaving is in the version's past, and otherwise lets a later leaving change the members at an older head |
| `Kernel.RosterHead.old_head_still_counts` | by definition, a key that is a member at an older head is a voice of a version naming only that head |
| `Kernel.RosterHead.one_signature_never_removes`, `one_key_alone_stands_nothing` | where the count asks two or more, a member leaves a standing version only by its own withdrawal or by the signatures of two distinct members |
| `Kernel.RosterHead.voters_is_common` | a version naming several heads is counted over the members common to them, which is the common list of `Merge.lean` |
| `Kernel.RosterHead.Rejected.Model.later_withdrawal_changes_members`, `head_withdrawal_ends_version` | under the rejected rule of withdrawable votes, one later withdrawal removes every member at a head and ends a version naming it |
| `Kernel.TwoMechanisms.edge_is_one_voice_consent`, `claim_is_one_voice_consent` | an edge of the meaning walk is a relation binding one voice, so what a row means to a reader is a bounded walk of one-voice consents from the reader's key |
| `Kernel.TwoMechanisms.claim_lost_only_by_walk_voice` | a row loses its meaning for a reader only through a withdrawal signed by a key on that reader's walk |
| `Kernel.TwoMechanisms.content_holders_are_consents`, `content_audience_function`, `content_audience_final` | with each row's own audience a roster's members, everyone or one key, who may hold a row is read off roster heads, their pasts and naming rows alone |
| `Kernel.TwoMechanisms.door_not_function_of_rows` | a window the reader closes on its own clock, with no answer held, is open at one instant and closed at a later one over the same rows |
| `Kernel.TwoMechanisms.SeatModel.consent_not_door`, `offer_alone_never_stands` | whatever answers a window an offer opens, its outcome at every instant does not say whether the seat stands, and an offer alone stands at no instant |
| `Kernel.Carry.nothing_leaves`, `others_elsewhere_change_nothing`, `author_carries`, `same_room_unchanged` | a naming row carries only from the same room or under the named row's own signer; then no key outside a room's own audiences is in the audience of its rows unless an author carried a row of its own out, rows by others elsewhere change no audience, and inside one room the rule is the earlier one |
| `KeyEnd.bound_reads_row`, `live_perm`, `live_mono` | a key record's bound is a function of the record alone; whether a key is live does not depend on the order its records are held in; a further record never ends a live key |
| `KeyEnd.live_own_rows`, `live_le_ceiling` | records of other keys change nothing, and a live key is within the ceiling of the instant of some record it signed |
| `KeyEnd.ended_not_live`, `ended_stays_ended` | with the same records, a key ended at an instant is live at no later instant |
| `Kernel.offer_withdrawal_ends`, `acceptance_withdrawal_ends`, `third_key_cannot_end`, `only_withdrawals_and_cuts_end` | either side ends a seat alone by its own withdrawal; no third key ends it without a cut |
| `Kernel.stands_function`, `stands_mono`, `means_is_seat_walk` | standing is a bounded walk of live seats and a function of the set; it grows with offers and acceptances and shrinks only with withdrawals and cuts; what a row means to a reader is that walk from the reader's own key |
| `Kernel.cut_status_function`, `unique_when_uncontested`, `two_cuts_contested`, `winner_counts` | each cut counts, is void or is contested, as the least solution of its equations; two concurrent cuts that undo each other are both contested, and a row naming both settles it |
| `Kernel.outsider_changes_no_cut`, `outsider_row_never_counts` | a row by a key with no entitlement on a slot changes no cut and never counts on it |
| `Kernel.cannot_land_inside`, `ruleI_only_concluder_undoes`, `ruleII_never_final` | a window's landing cannot stand over an objection its signer acknowledged; under the rule taken only the concluder's own key undoes a landing; under the other rule any objector reopens any landing for ever |
| `Kernel.Recount.dishonest_never_stands`, `stands_is_table_over_all_not_late`, `unnamed_gains_nothing` | under recount a landing that states an outcome its own past does not give never stands, and a landing stands only if it states the table's outcome over every answer that does not name it |
| `Kernel.Recount.undone_only_by_counted_answer`, `naming_answer_changes_nothing`, `count_door_final`, `quorum_closed_final` | only a newly counted concurrent answer that moves the table undoes a landing; an answer naming the landing changes nothing; a landing with a strict majority behind it is final, against every key but one that has answered both ways (`quorum_closed_final` assumes no key of the roster answered both ways) |
| `Kernel.Harden.F1.ended_keys_change_nothing`, `F2.rival_cannot_move` | rows by a key whose seat was ended, unseen by the ending, neither unseat nor rescue a landing; a landing that does not stand moves no outcome |
| `Kernel.Harden.F3.no_replay`, `F4.proposer_cannot_end` | a cosignature in the past of a head is no voice for a row counted over that head; the proposer of a counted offer does not end it alone |
| `Kernel.Harden.F5.no_single_founder_removes`, `removed_cannot_reseat`, `no_row_restores_a_founder` | among several founders one removes no other, and a removed founder seats itself again by no row; over founding seats, once every founder has withdrawn no later row restores one; `Duty.lean` states each against the community law |
| `Kernel.Duty.lone_holder_confers`, `lone_count_is_own` | with one duty holder at the head a row names, that holder's signature and the new holder's yes seat, and no other key's signature is a voice |
| `Kernel.Duty.one_of_several_confers_nothing`, `one_of_several_rows` | with two or more duty holders, a row carrying one holder's signature alone seats nobody, and so does any number of such rows |
| `Kernel.Duty.majority_confers`, `confers_only_by_majority` | a duty seat stands exactly when more than half the holders at the head have signed the row and the new holder has said yes |
| `Kernel.Duty.withdrawal_needs_two_others`, `two_holders_neither_unseats`, `lone_holder_not_unseated` | a withdrawal counts exactly on more than half of the other holders and at least two of them; of two holders neither unseats the other, and no holder unseats a lone one |
| `Kernel.Duty.conferrer_cannot_end`, `conferrer_cannot_lower_count` | once a duty seat stands, a withdrawal signed by any key but its holder, a conferrer's included, ends nothing |
| `Kernel.Duty.equals_perm`, `equals_rename` | every duty count reads the holders as a set: the answer is the same whatever order they were seated in, and under any renaming of keys |
| `Kernel.Duty.removal_ends_duty`, `removed_confers_nothing`, `removal_cuts_duty` | a key a standing roster version leaves out holds no duty at that version or below it until it is listed again, its signatures confer nothing there, and the removal ends each conferral of its seat in its past |
| `Kernel.Duty.none_left_members_seat`, `holders_left_members_do_not`, `one_member_seats_nothing` | with no duty holder at the head a row names, only the members' count confers a duty seat; while a holder remains, only the holders' count does |
| `Kernel.Duty.Rejected.three_holders_lone_grant`, `lone_grant_outlives_conferrer`, `members_restore` | three readings of F5 the community law rejects: one of three holders' own grant seats nobody, a lone holder's grant outlives its conferrer's withdrawal, and the members' count seats a holder when none is left |
| `Kernel.Harden.F6.rows_of_one_key`, `no_self_service`, `member_can_widen` | a key enters a row's audience by no rows of its own; a key already inside widens it by one concluded naming row |
| `Kernel.Harden.F7.backdated_conferral_seats_no_one` | while two tips wait a seat with no offer under one of them is not held |
| `Kernel.Harden.CP.checkpoint_voids_any_answer`, `without_checkpoint_fixed` | under the rejected rule: were a counted row to leave older acts behind, two counted rows would void any answer in a window; without that rule nothing later changes whether a concluded answer is counted |
| `Kernel.Reader.line_voids_old_fork`, `old_fork_void_for_ever`, `sibling_waits`, `merge_accepted` | over the cut alone, a reader's acknowledged line voids, for that reader, any line from below it however long; a sibling on the same head waits; a row naming the acknowledged head is judged like any other |
| `Kernel.Reader.built_on_void`, `line_void`, `no_line_is_plain`, `rd_unique` | a counted row counts for a reader only if every counted row it is built on does, down the whole line; a reader with no acknowledgement has the cut and that clause and nothing that ranks lines; the answer is unique |
| `Kernel.Reader.depth_race`, `race_one_way` | were a counted row to leave older acts behind, of two lines from one head the deeper would leave the other behind, and never the reverse |
| `Kernel.Terms.entK_anti`, `entK_single`, `iter_bound`, `cut_iter_bound` | the cut's terms as the running kernel gives them (what clashes, what overrules, a tally of live seated voices at the head named) meet what the general theorems ask; the iteration reaches what counts within one round for each concluded cut |
| `Kernel.Terms.outsider_changes_no_cutK`, `outsider_row_never_countsK` | a row none of whose voices is by a key seated to it at the head it names changes no cut; where the conclusion rule asks a seat of the signer, its row on the slot never counts |
| `Kernel.Terms.removal_voids_row`, `removals_agree`, `mutual_removal_contested`, `deciders_clash`, `two_deciders_contested`, `decider_voids_named` | a removal voids its key's concurrent rows; two removals of one key agree; two that remove each other's signers are contested; deciders that pick differently are contested, and a decider voids the claims it names |
| `Kernel.SeatG.standsG_mono`, `standsG_eq_stands`, `seatedG_eq_seated`, `Witness.unshared_not_equal` | the refined walk grows with offers and acceptances and shrinks with withdrawals and cuts; it is the walk of `Seat.lean` exactly where no offer is shared and no holder withdraws against an offer it did not sign, and not otherwise |
| `Kernel.SeatG.count_not_sole`, `only_withdrawals_and_cuts_endG`, `third_key_cannot_endG` | a count of two or more has a voice that is not the proposer's; the two-voice floor and the rules of ending hold for the refined walk |
| `Kernel.Merge.merge_counted_one_tip`, `common_is_waiting_roster`, `merges_share_signer` | a version naming several heads is counted over the members common to them, which is the roster while they wait; a merge of every tip is the one tip with the roster it states; two merges of one set of heads counted by strict majorities share a signer |
| `Kernel.Merge.merge_on_void_tip_void`, `merge_counts` | a merge naming a tip that does not count for the reader is void, and one whose tips all count counts |
| `Kernel.rosterOf_function`, `merge_one_tip`, `fork_shares_signer` | with several tips the roster is the members common to them; a version naming every tip makes one tip; two versions of one head each counted by a strict majority share a signer |
| `Causal.wins_unique`, `higher_kind_decides`, `same_kind_both_or_neither` | concurrent rows on one target that differ in kind are decided by a fixed order on kinds; rows of one kind are still both or neither |
| `Kernel.Settled.kept_ext`, `concl_ext`, `grows_extends` | a later set holds every row held now and changes no row's past; under any such set, of any size, a kept row stays kept and, for a rule that reads no concurrent row, its conclusion is unchanged |
| `Kernel.Settled.Rows.count_not_monotone` | under the cut, an act that counts where a grant and the act are held no longer counts once a concurrent cut on its slot is also held; it is concluded in both, so its conclusion is final and its counting is not |
| `Kernel.Settled.counts_final_of_disarmed` | a concluded act counts in every later set when every cut that could void it there is disarmed against it |
| `Kernel.Settled.settled_mono`, `settled_final` | an act every voice that may cut it has acknowledged stays so in every later set; if those voices are fixed by the act and an acknowledgement disarms its signer's cuts against the act, the act counts in every later set |
| `Kernel.Settled.unsettled_defeated`, `final_iff_settled` | one row by a voice that may cut and has not acknowledged defeats the act; where each such voice can sign that row, an act counts in every later set exactly when every voice that may cut it has acknowledged it |
| `Kernel.Settled.body_settled_disarms`, `body_unsettled_majority_free`, `half_disarms_majority`, `count_disarmed` | where a body cuts by a strict majority and an acknowledging member's voice is not counted against what it acknowledged, acknowledgements by half the members disarm every cut, and with fewer than half the rest are a strict majority; for a count of `t` of `n`, it takes `n - t + 1` |
| `Kernel.Settled.Rows.fork_voids_acknowledged`, `overrule_voids_acknowledged` | under the cut as stated, a voice that acknowledged an act still voids it by a cut that leaves its acknowledgement unnamed, or by a deciding row that names it; neither does once an acknowledgement disarms its signer |
| `Kernel.Settled.Rows.later_seat_defeats_acknowledged`, `seat_at_head_restores` | a voice seated at a later head voids an act every voice at the act's head acknowledged; read at the act's own head, the right to cut leaves it counting in every later set |
| `Kernel.Settled.three_ways_final` | a row is kept for good, its conclusion is final, and whether it counts is final exactly when every voice that may cut it has acknowledged it; otherwise it is provisional |
| `Kernel.Settled.blocking_set_blocks_all_cuts`, `ack_blocking_quorum`, `five_three` | acknowledgements that meet every coalition able to cut an act leave no cut; for a count of q of n members that takes exactly n − q + 1, so three of five where three cut |
| `Kernel.Settled.ack_cut_three_cases`, `ack_blocks_cut`, `cut_with_ack_is_ancestor` | an acknowledgement is clean when no cut of the act by the same key is in its own past; then a cut by that key either has the act in its past or is concurrent with the acknowledgement, and the fork rule leaves the key no counted voice |
| `Kernel.Settled.ack_finality_future_stable`, `ack_counts_future_stable` | with the voices and the count read at the head the act names and a forked signature not counted against it, clean acknowledgements by n − q + 1 members make the act count in every later set |
| `Kernel.Settled.effect_row_settled` | a row whose own past holds those acknowledgements is, wherever it is kept, proof that no cut voids the act in that set or any later one |
| `Kernel.Settled.Rows2.fork_recount_falls`, `acknowledged_fork_fails`, `unclean_ack_does_not_block`, `fork_stands_on_row_count` | a reader without a key's concurrent acknowledgement sees that key's cut met until the acknowledgement arrives; with three clean acknowledgements of five a forked cut signed by every other voice fails; an acknowledgement signed after the key's own cut blocks nothing; and read from the cut row's signatures alone, as a count is today, the fork still cuts |
| `Kernel.Settled.closed_iff_no_witness_pair`, `full_view_closed`, `pruned_view_closed`, `pruned_view_answers` | a view is closed under adding rows when its next value is a function of its value, exactly when no two states with one view part after one step; rows with answers are closed, and so is a view that keeps an unblocked act's rows and only the fact for a blocked one |
| `Kernel.Repurge.closedBy_comp`, `closedBy_run`, `purge_closedBy`, `prunedView_is_purgeView`, `pruned_view_closed_again` | closed views compose, and along any list of steps the coarse run is the fine run read through the view; one purge of the rows behind any monotone answer is closed under adding rows, and `pruned_view_closed` is its instance (`Repurge.lean`, native to this repository) |
| `Kernel.Repurge.repurge_purgeView`, `any_schedule`, `schedule_answers` | purging a purged store again changes nothing, so under every schedule of arrivals and repeated purges the stub is the purge of the full store and gives its answers |
| `Kernel.Repurge.second_closedBy`, `two_purges_closedBy`, `two_purges_run`, `two_purges_read`, `two_purges_commute` | a second act's purge, taken on the first one's stub, is closed under the first one's law when each act's answer reads no row the other's purge may drop; the two together are closed under adding rows, read what the full store reads, and commute |
| `Kernel.Repurge.shared_not_blind`, `shared_drop_misreads` | the condition is needed: where the second act's answer reads a receipt the first act's purge drops, the second purge reads the act unsettled while the full store reads it settled |
| `Kernel.Settled.Rows2.unsettled_drop_has_witness_pair`, `count_view_not_closed` | "the act counts" with the rows dropped is not closed: two unsettled histories with that answer part when the same cut arrives |
| `Kernel.Settled.concl_ext_local`, `derived_ext_local`, `kept_sub` | under any later set a conclusion changes only where a newly kept row is in concurrent conflict with the row or an ancestor, so a node recomputes only what the new rows touch |
| `Kernel.Settled.checkpoint_resume`, `checkpoint_conclusions` | every held set is a checkpoint row's past and the rest, and the conclusions folded over that past alone are those over every later set |
| `Kernel.Settled.countsAt_local`, `later_head_changes_nothing`, `carried_to_head` | whether an act counts at a head reads only the rows naming that head; rows naming a later head change what the act carries to that head and never whether it counted at its own |
| `Kernel.Settled.Rows.later_seat_is_forward`, `fork_has_no_say`, `overrule_is_no_vote` | read by head, a voice seated later moderates forward, a voice that acknowledged and forked has no say, and a deciding row with the act in its past is no vote against it; the timeless readings of the same rows are the three theorems above |
| `Kernel.Settled.ack_never_yes`, `say_settled_final`, `countsAt_final`, `say_unblocked_can_cut`, `sole_cutter_fork_stands` | within one head a voice that has acknowledged never says cut again; acknowledgements by n − t + 1 members at the head leave no cut count met there in any later set, and members that have not acknowledged meet it when they are t |
| `Kernel.Settled.symmetric_say_forced`, `say4_symmetric`, `sayC_not_symmetric`, `say4_closed`, `say3_not_closed`, `say4_absorbing`, `sayA_not_safe` | a reading that treats a voice's two opposite rows alike gives a voice that said both no say; that say is closed only with "said both" kept apart from "said nothing"; once a voice has acknowledged it never says cut, which fails where any cut vote counts and holds, asymmetrically, where an acknowledgement binds |
| `Causal.counts_function`, `only_removals_stop_counting` | a row of a removed signer counts when it lies in the past of the removal; that is a function of the offered set, and only a removal of its signer can stop a row counting |
| `Causal.sign_after_removal_never_counts`, `Removal.acknowledged_counts`, `Removal.honest_but_unnamed` | a row first held after the removal is kept never counts; a row the removal's past had named counts, and one it had not named does not |

**What it assumes.** The naming relation is well-founded: a digest cannot name a row that names it back.
An edge is withdrawn only by its own signer.

**What it does not show.**

- A removal that extends an older head leaves more rows out of its past (`Removal.stale_head_voids_more`).
  The roster chain's rule for two versions of one head must bound that, and that rule is not modelled.
- Re-admission of a removed key and a contested removal are not modelled.
- The same reach for a retirement, a revocation or a withdrawn grant is the same rule under another name,
  and is proved here only for a removal.
- A contested slot may stay empty; nothing here ends a dispute.
- A window's length is not in the rows. No theorem says a landing came late enough.
- A theorem named `…_function` says that an answer depends only on the set it is defined over, which follows
  from its definition. The content is elsewhere: `door_perm`, `adm_perm`, `close_saturated`, `conclOf_unique` and
  the theorems that say which rows can change an answer.
- A reader's line is applied over the cut, as the running kernel applies it: an act left behind by a reader's
  line still voids, inside the cut, what it clashes with. `Reader.lean` proves that form. `Harden3.lean` still
  holds an earlier form with the line inside the cut's operator and the rejected rule beside it; those theorems
  are superseded, and the two forms are not proved equal.
- The rules of `Harden` are proved over the definitions of the earlier files. The form of the kernel each
  attack succeeded against is a reconstruction, not an earlier version of the code.
- The refined seat equals the seat of `Seat.lean` only where no offer is shared and no holder withdraws against
  an offer it did not sign (`SeatG.standsG_eq_stands`). Otherwise the two are different rules
  (`Witness.unshared_not_equal`). The mark of a shared offer is derived for a count of two or more; for a count
  of one it is a rule.
- A cosignature that names two heads is a voice at both. What is proved is that one naming a single head is a
  voice at that head only.
- Under recount a lone landing is final only against keys whose answers cannot move the count. A key whose
  answer would move it can unseat the landing at any later time by leaving it unnamed
  (`unnamed_answer_unseats`). Which of two standing landings wins is not modelled.
- The cut's terms are transcribed for a removal and for a deciding row (`Terms.lean`). Finality against an
  outsider assumes that the conclusion rule refuses a row on a slot by a key with no seat at its head, and it
  concerns voices, not the signer: a cut carried by an outsider with enough seated cosignatures is entitled.
  The instances are proved for two cuts that are the only concluded cuts.
- A voice counted by a group is a signature on the row and is not withdrawn. A member who changes its mind signs a
  new counted act, or answers through a window under recount. A version naming several heads is counted over the
  members common to them (`Merge.lean`, `RosterHead.voters_is_common`).
- Concurrent versions of one head are not decided in `RosterHead.lean`; they wait as tips (`Window.lean`, `Merge.lean`).
- A conclusion from silence, such as a window closing unopposed, cannot be drawn from rows and is not here.
- The walk has one depth for all edges; the classes and budgets of `formal/trust_set` (parent repository) are not carried over.
- Whether an act counts is final only under two rules the cut does not state: the voices that may cut an act are
  those with standing at the head the act names, and a voice's acknowledgement disarms its own cuts against what it
  acknowledges (`Settled.lean`). Without the first a later seat defeats an acknowledged act
  (`later_seat_defeats_acknowledged`); without the second the acknowledging voice does (`fork_voids_acknowledged`,
  `overrule_voids_acknowledged`). That every such voice can sign a cut is assumed in `final_iff_settled`, not proved.
- `Settled.lean` Part 12 reads only cuts naming the head an act is judged at. A cut naming an older head is void for a
  reader that acknowledged the newer head (`Reader.line_voids_old_fork`); for any other reader it is the fork on a
  past head of [`kernel/KERNEL.md`](../kernel/KERNEL.md) 8a. Its say rule reads a voice's rows at a head whatever their order; where a voice's cut
  is in the past of its own later acknowledgement at the same head, the text's count once met keeps the cut, and
  only Part 9's clean acknowledgement reads it so.
- Finality by acknowledgement in `Settled.lean` Part 9 rests on two rules the text does not state: the voices and
  count of a cut are those at the head the act names, and a signature on a cut is not counted against an act its
  signer cleanly acknowledged in a concurrent row. It is final against cuts only; a key revoked back to a bound,
  an end read against now, and a reader's own trust are outside it. The pruned view keeps every row of an act not
  yet blocked; the least set of rows that suffices is not found.
- `Settled.lean` reads the cut over a conclusion rule that reads no concurrent row. Where the conclusion itself reads
  concurrent rows, it is not final, and neither is anything built on it.
- The rule tables are not read. `formal/derivation/order/` (parent repository; its `witnesses.tsv` is [`data/witnesses.tsv`](../data/witnesses.tsv) here) holds the measure of the tables against this form:
  seventeen cases run through the guard cells in every arrival order, and each family's verdict.

Run: `bash proofs/build.sh`, with Lean 4.14.0 on the path (installed as the top-level README says). It compiles the thirty-three files in order and exits on a compile error,
a `sorry`, or an axiom beyond the three of core Lean.

Then it runs `Audit.lean`, the semantic audit. That file imports the whole stack and asks Lean which axioms every declaration depends on (`collectAxioms`). This covers every declaration, not only the theorems a `#print axioms` line reports. A `sorry` leaves `sorryAx` behind, and an `axiom` declared here names itself, so either fails the build, even in a lemma no printed theorem uses. The audit has a plant every run. `build.sh` writes a module with an unused `sorry` and a minted axiom, audits it with the stack, and fails unless both are refused. `build.sh` also fails on any "declaration uses 'sorry'" the compiler reports. The run line adds `N declarations audited, plant caught`.

Output of the run in this repository: `proofs: 33 files, 754 theorems reported, 5022 declarations audited, plant caught, rc=0`. The nineteen files carried from the parent print 556 (548 at the commit they were carried at, two more since `Reader.lean` states `sibling_by_acknowledgement`, and six since `Settled.lean` states rule 4 from the head the cut names, `countsFrom`); the seven added for the crate (`CutFix`, `SeatWalk`, `SeatCount`, `WindowTable`, `Retained`, `Versions`, `Ops`) print 52; `Repurge.lean` prints 13; `Admission.lean` prints 76; `MinorVoid.lean` prints 15; `KeyOfIssuer.lean` prints 16; `DerivedCircle.lean` prints 12; `Held.lean` prints 7; `TipsFold.lean` prints 7. The count is of lines reporting the axioms a declaration depends on (`#print axioms`), one per theorem the files print, not of every lemma.

`Repurge.lean` is written for this repository and has no counterpart in the parent or in the crate's gaps.

## Added for the crate

Seven files prove the gaps that `crates/ciris-kernel/FORMAL_GAPS.md` ranked, and an eighth, `MinorVoid.lean`, a rule of
the Constitution that `models/tla/MinorVoid.tla` also model-checks. They state the crate's functions
over Lean definitions of the same shape, and are built by `build.sh` like the rest.

| File | What it proves |
|---|---|
| `CutFix.lean` | the cut's well-founded fixed point: for any antitone step, what it reports as counting counts whatever the undecided cuts do; the cut's step is antitone |
| `SeatWalk.lean` | the bounded walk of live seats is exactly the chains of at most `depth` links from a root; tips wait |
| `SeatCount.lean` | no key admits itself; counts never fall; each policy's arithmetic, `unanimous` at two, the duty floor, `weighted` |
| `WindowTable.lean` | a window's table before and at its close |
| `Retained.lean` | the rows that have not lapsed are closed downwards; revocations are kept |
| `Versions.lean` | built on, for roster versions |
| `Ops.lean` | the reducer that refuses a tie is a function of the set, and refuses only a real tie |

## Added for the Constitution

Rules of the CIRIS Constitution, proved at its request and vendored by it by commit and hash. Each cites its
CC section at v1.0-rc21 (commit `b016df4`).

| File | What it proves |
|---|---|
| `Admission.lean` | CC 2.7.11 (Constitution v1.0-rc21, commit b016df4): code, profile and action admission, transcribed from `formal/admission/admission.py`, are each one walk (`Causal.reaches` to the stander, `Consent.bodyConsents` on the row) and differ in the body: one voice for profile and one person's code row, a count of two or more for a counted code row, the four faculties at four for an action (`three_admissions_one_walk`); the fourteen properties of `admission_expected.tsv` as theorems over every world; and, by the Constitution's rc22 (commit `4040d0b`, CC 2.7.11 "Derived trust", CC 4.5.5 (b)), the effect gate's two arms: an act that needs a role is licensed by a live delegation onto this agent, signed by a person seated over it, whose scope names the duty, with no approval of the act (`p11_delegation_needs_no_approval`, `p11_delegation_licenses`); a scope that does not name the duty licenses nothing, refuting the plant `delegation_any_scope` (`p11_scope_must_name_duty`, `delegation_any_scope_differs`); a withdrawn delegation, a program's and one onto another agent license nothing; only an act no delegation covers needs the approving row, and since rc22 commit `bdb10ee` that row must be about the acting agent: an approval of another agent's call licenses nothing here, refuting the plant `approval_any_agent` (`p11_approval_other_agent`, `approval_any_agent_differs`) |
| `MinorVoid.lean` | CC 3.2 (Constitution v1.0-rc21, commit b016df4), as ruled on 2026-11-20: the void of a duty appointment `D` made to a minor (a minor row held, live or retracted, and no un-retracted assured adult proof dated before `D`) is a function of the held rows (`void_of_same_rows`, `incremental_is_void`, `any_order`); backdating `D` only voids it; a retraction of a minor row changes nothing (`minor_retraction_changes_nothing`); a retracted adult proof lifts nothing (`retracted_proof_lifts_nothing`, `retracted_proof_voids_example`); a self-declared adult lifts nothing; a minor row superseded by its own signer's newer row still voids; `expiry_backdate_lifts`, kept as a regression plant, shows that an expiry clause would let backdating lift a void. Model-checked with plants in `models/tla/MinorVoid.tla` and `MinorSuspend.tla` |
| `KeyOfIssuer.lean` | step 8 of CC 2.6.1.8, the rule of CC 2.6.1.7 (Constitution v1.0-rc21, commit `b016df4`): a statement is Valid exactly when its key is a key of its `iss` by one of the four ways, genesis, a held rotation chain, the seat of the bundle in force, or a live occurrence (`verdict_valid_iff`); a missing link, voice or bundle answers Waiting, never Invalid; Waiting turns Valid only by a way the earlier rows did not give, and with the link still missing and no other way offered never does (`stays_waiting_without_link`; the literal form without that proviso is false, `other_way_counterexample`); the verdict is a function of the set held (`verdict_perm`) |
| `DerivedCircle.lean` | CC 1.13.3.4 (Constitution rc22, commit `09c8b4f`, which adds the three sentences the proof matches: every owner releases, the rule is read at each serving, a check reads only the piece placed at its seam), "Derived content keeps its circle": under the door, what an agent derives is shown only within the intersection of its sources' audiences unless every person whose piece it is signed a release naming it (`door_within_inter`, `door_two_rooms`); by induction over derivation chains of any depth, `self` content reaches no reader outside that `self` without its owner's release on the chain (`chain_or_release`, `self_stays_self`); composed with the audience rule transcribed from `formal/audience_view`, a reader served a derived output is served every row it derives from and is in the audience of a held row of each one's cohort (`seen_derived_every_source`); a check, a read of a row at one of the three seams, never reads a `self` row, and lawful access never reaches one (`no_check_on_self`, `no_check_on_derived_self`); the release is live (`release_lifts`); the plant, showing an output to the union of its sources' audiences, lets `self` content reach an outsider (`union_plant`, `union_breaks_chain`) |
| `Held.lean` | the crate's held view (issue #4, slice 4): an admission that recomputes only the dirty cone (rows not kept before, and rows with themselves or an ancestor in concurrent conflict with a newly kept row) and keeps every other answer gives the full fold's conclusions (`admit_eq`, from `Settled.concl_ext_local` and so `Causal.conclOf_local`), after every admission of any chain (`admits_eq`); a newly kept row is dirty (`admit_dirty_new`); a derived answer over parties outside the cone is unchanged (`admit_derived`, from `derived_ext_local`); a resumed checkpoint gives every answer of the view it came from (`resume_eq`, `resume_concl`, from `checkpoint_resume`), and admitting after it gives the fold over the prefix (`resume_admits_eq`) |
| `TipsFold.lean` | the fold at tips (KERNEL.md section 7; `seat::Seats::tips_fold`): as passes from the keys common to the tips, the common keys are in at every pass, a pass only adds, nothing outside the common keys and the candidates is in, a key that is out is never in, with no candidate the fold is the common keys, a pass that adds nothing is the last, and a key the fold never seats is a voice for nobody. It states the fold's bounds, not the count |

### `Admission.lean`: what the claim needs

The Constitution's `formal/admission/README.md` (v1.0-rc21) says that code and profile admission are the kernel's
seat walk at one voice and action admission the same walk at a count, "argued here and run, not proved in Lean".
`Admission.lean` proves it with two qualifications, each a theorem:

- Code admission is at one voice only for a unit that names no effect, or for the host owner's own row on its own
  host, whose walk has depth 0 (`code_effect_body`). Any other unit that names an effect is the walk at a count of
  at least two persons (`p4_effect_needs_count_or_owner`), as CC 2.7.11's own table says.
- The action scope differs in more than the count. Its root and stander are the agent's own key at depth 0, and its
  voices are the four faculties, which are not persons. A dispatch can pass in a world with no person in it
  (`action_needs_no_person`), and so can an effect that needs no role (`effect_needs_no_person`). An action is
  rooted in a person only where an objection is discharged (`p9_discharge_by_person`) or the act claims authority.
  Since the Constitution's rc22 (commit `4040d0b`) it claims authority by one of two arms
  (`p11_authority_rooted_in_person`). One is a live delegation whose scope names the act's duty, signed by a person
  seated over this agent, who approves no single act under it (`p11_delegation_needs_no_approval`). The other, for
  an act no delegation covers, is an approving row naming the fingerprint, about this agent and signed by a person
  seated over it. At `4040d0b` the model read the approval's own agent; the Constitution fixed that at `bdb10ee`
  (`p11_approval_other_agent`). The ruling leaves `action_needs_no_person`
  as it was: the same dispatches need no person. It moves a role act's person from each act to the grant.

All fourteen properties are stated and proved for every world (P1–P14, theorem names in the file header). P2 and P9
assume the unit digest and the call fingerprint are injective, and P10 reads the profile digest as the list of link
digests, which is the same assumption. That is SHA-256's collision resistance, which a Lean proof cannot give, so it
is a hypothesis of those theorems. P12 is proved for every permutation, where the model runs twelve. In seven places
`admission.py` takes the first matching row in the list. The Lean reads any held row instead, so it agrees with the
model wherever one such row is held (every case of `check_admission.py`) and is independent of order where two are.
