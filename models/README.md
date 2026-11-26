# `models/` — the kernel, running

Python 3.12, standard library only. Each check enumerates small worlds of signed rows, runs the kernel over
every arrival order of each (or a fixed sample above a stated size), and compares its verdicts with a recorded
file. Most checks also carry **plants**: deliberate breaks of one rule that the check must catch. A check exits 1
on any difference, any plant not caught, or any world that gives two answers in two arrival orders.

These are runs to a bound over models the authors of the rules wrote. They are not proofs, and a run cannot show
what happens above its bound.

| Folder | What | From (parent repository) |
|---|---|---|
| `causal_kernel/` | the kernel's three layers, the cut, the seat, the window, copying, the roster, checkpoint and purge, a key's own end, private rooms, and the attack runs | `formal/causal_kernel/` |
| `kernel_lib/` | the shared operators the models are written in (`kernel_lib.py`, `reexpress.py`) | `formal/kernel_lib/` |
| `roster_fork/` | two versions of one roster head: tips wait | `formal/roster_fork/` |
| `key_plane/` | the writer's key plane; `causal_kernel/keyplane.py` re-reads it as a fold and compares | `formal/key_plane/` |

## The checks carried, and what each prints last

Each is run by `./check.sh` at the top of the repository. The last line is what `check.sh` prints for it.

| Command (from the repository root) | Checks | Last line |
|---|---|---|
| `python3 -I models/causal_kernel/check_purge.py` | checkpoint and purge (CC 2.7.10): eleven histories, every extension to four late rows, purged once and again part way, at each `now`; nine plants, and the rule's plant `own_head_only` (a cut at an older head not read) | `RESULT: ok` |
| `python3 -I models/causal_kernel/check_time.py` | two notions of time over 86 worlds of two rows; readings not covered are reported with witness pairs | `RESULT: ok` |
| `python3 -I models/causal_kernel/check_key_end.py` | a key's own end: ten properties, plants, ten attacks (two workers) | `RESULT: ok` |
| `python3 -I models/causal_kernel/check_conferral_end.py` | the end of a conferral (CC 2.4.1.1): 42 cases with a hand-written answer for every act, in every arrival order (the first 200 of a case with many), deputy chains with their sub-delegation and depth gates included; the fixture for persist gives the same answers | `RESULT: ok` |
| `python3 -I models/causal_kernel/check_conferral_content.py` | room content after a member's seat ends, where the end names the rows held good (a proposal for CC 2.4.1.1): 56 cases in every arrival order; every history of up to four rows, with what the member alone and one counted row can change; three plants (three workers) | `RESULT: ok` |
| `python3 -I models/causal_kernel/check_conferral_two.py` | one row that needs two standings (an owner binding and a root grant): five ways to place the act against the binding, seven properties, 1,344 histories, 21 cases (a later bundle version among them) and six of two owners (two live bindings to different owners are no owner); the rule as one function of the held rows, compared with the per-record ledgers on every state; naming the grant's head and the owner's acceptance of the grant, which names its binding, holds all seven, and the other readings break what is expected of them | `RESULT: ok` |
| `python3 -I models/causal_kernel/check_duty_seats.py` | a duty seat stands only on a member (CC 4.5.4), read by the seat walk: a conferral on a non-member seats nobody and is no voice in a duty count, and stands when the widening lands; a resignation or a counted removal ends the duty seats in its past; nothing revives; a conferral between the end and a re-admission waits; the founding record (CC 4.5.4) seating its listed members and its named duty holders with one, two and three founders, a duty laid down by a withdrawal naming it, the stay ended by one naming no seat, an unsigned listed member and an entry naming no listed signer seated in nothing; two tips; what the rule does not reach. 58 hand-written cases in every arrival order (a sample above six rows), ten planted breaks caught; the rule reaches a room founded with members only | `RESULT: ok` |
| `python3 -I models/causal_kernel/check_delegation.py` | a delegation chain from a counted grant (CC 4.1.1, CC 3.4.7), read by the seat walk: the depth cap, attenuation, the sub-delegation gate, two consents, an end by withdrawal, a cycle, a self-edge; 14 cases in every arrival order, four planted breaks | `RESULT: ok` |
| `python3 -I models/causal_kernel/check_agent_removal.py` | a moderator's lone removal of an AI agent's key and the members' lift of it (CC 4.5.13), with the two counts of that clause: the removal concludes on one voice of a holder of `moderate` and opens its own `moderation_overturn` window; the lift is a strict majority of the members at the head the act names, the author apart, floor two; the removed agent's key, seated in scope `agent`, is apart from that count on every path; the re-seating is a counted row over the objections it names. 40 cases in arrival orders, eight planted breaks in the seat rule; the window adversary table read under recount (107 rows, 96 checks, none broken) and five planted breaks in the tables (the fallback counted over all members, the author's objection a voice, the author counted over) |
| `python3 -I models/causal_kernel/check_window_rows.py` | the moderation windows land by signed rows (CIRISConstitution#221): a member's vote on the fallback is a ballot of `ballot:moderation_action`, `for` or `against`, one ballot a person folded as `ballot:moderator` is (agreeing ballots are one, disagreeing ones none), and a ballot its own signer withdrew is no ballot, a withdrawal concurrent with a landing recounted with it; the landing is a signed row of a member at the opener's head. the overturn's landing signed by any member but the act's author. The 26 rows of the window adversary table that name #221 in arrival orders, eight planted breaks, and the base `active` as a stated count above k |
| `python3 -I models/causal_kernel/check_agent_seat.py` | an AI agent's key has a seat of its own kind, `agent` (CC 4.5.13): on the roster (`Seats.roster`: content, wraps, audience) and in no count; its signature on an admission, a removal, a duty conferral or a window answer is no voice, and it is not counted over (numbers chosen so that counting it changes the answer); an agent holding a conferred duty acts within it; a moderator removes an agent alone and not a person; the room's count removes an agent; an agent resigns. 28 cases in arrival orders (a chain of twelve lone removals among them), seven planted breaks caught | `RESULT: ok` |
| `python3 -I models/causal_kernel/check_removal_in_force.py` | a moderator's lone removal of an agent's key is an act under its `moderate` standing, in force only while the end rule (E2 to E8 of `conferral_end.py`, re-expressed over seat rows) says so: the remover's own laying down, the room's counted removal of it and the other holders' counted withdrawal of its duty each take the removal out of force unless another holder's receipt of it is held; a receipt by the remover, or one with the end in its past, keeps nothing; a removal at a later head than the end, or naming it, does not count; another standing live at the removal's head keeps it in force (E7), and nothing else does: neither the remover's re-acceptance nor a new conferral revives it, and a removal signed again after re-seating is in force; two tips. 26 cases in arrival orders, four planted breaks caught | `RESULT: ok` |
| `python3 -I models/causal_kernel/check_resignation.py` | a resignation in a count, the wrap set and dissolution (CC 2.4.1.1, CC 2.7.8), as the seat rules read them: a resigner is counted until a counted row cites its resignation, is wrapped to by no node that holds the resignation, and a group is dissolved where the wrap set is empty; 8 cases, every name-closed set of rows of a room of three (152), six properties, three planted breaks. It needs the fold at tips | `RESULT: ok` |
| `python3 -I models/causal_kernel/check_rosters.py` | one roster mechanism, five instances: 90 properties, each with a break (three workers) | `90 properties, verdicts as recorded: True` |
| `python3 -I models/causal_kernel/check_attacks.py` | thirty-four attacks, 126 scenarios, classed HOLDS / CONCEDED / NOT EXPRESSIBLE / BROKEN (three workers) | `RESULT: ok in …s` |
| `python3 -I models/causal_kernel/check.py` | order-freeness: every set of up to six rows from two pools in every arrival order; the seventeen witnesses (three workers) | `RESULT: ok` |
| `python3 -I models/causal_kernel/check_cut.py` | the cut: order-freeness and that only a key that may cut a slot changes it (three workers) | `RESULT: ok` |
| `python3 -I models/causal_kernel/check_roomkey.py` | private rooms: voices, bindings, symbolic deniability (three workers) | `RESULT: ok in …s (77 facts)` |
| `python3 -I models/roster_fork/fork_check.py --check` | tips wait, under several counting protocols | `roster_fork: with tips waiting …` |
| `python3 -I models/roster_fork/fold_check.py` | a proposed fold at tips (not the rule of the text, which is that tips wait): commuting membership changes seat at once, an addition only where it still meets its count without the voices any tip removed, tips that differ in policy wait; with a policy change and with heads one key can write (an outsider's own admission, a resignation); six properties over nine settings, six planted breaks | `RESULT: ok` |
| `python3 -I models/key_plane/key_plane_model.py --check` | the key effects of the transitions table | `key_plane: …` |

Each of these was run in the parent repository at commit `60c741e` and here; apart from lines that print elapsed
time, the two outputs are identical line for line.

`check.py` rewrites `causal_kernel/witness_runs.tsv` on every run; the content is the same each time, so the
working tree stays clean. `check.py` and `check_cut.py` also write a results file to `$GATES_TMP` (default `/tmp`);
`check.sh` points that at a temporary directory.

## Changes from the parent

Paths only. Where a model read a file from the parent's `manifests/`, `formal/kernel_lib/`,
`formal/roster_fork/`, `formal/key_plane/` or `formal/derivation/order/`, the path now points at `data/` or the
sibling folder here. Nine lines changed, listed in [`../PROVENANCE.md`](../PROVENANCE.md). No model logic was
changed. Comments, docstrings and printed source strings still name the parent's paths, so the verdict lines are
the parent's verbatim.

## Not carried

Checks whose dependency closure reaches most of the parent's toolchain (the rule tables, the expression language
and the text of the Parts) run in the parent repository. [`../REVIEW.md`](../REVIEW.md) lists each with its command.
