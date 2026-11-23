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
| `python3 -I models/causal_kernel/check_purge.py` | checkpoint and purge (CC 2.7.10): nine histories, every extension to four late rows, purged once and again part way, at each `now`; eight plants | `RESULT: ok` |
| `python3 -I models/causal_kernel/check_time.py` | two notions of time over 86 worlds of two rows; readings not covered are reported with witness pairs | `RESULT: ok` |
| `python3 -I models/causal_kernel/check_key_end.py` | a key's own end: ten properties, plants, ten attacks (two workers) | `RESULT: ok` |
| `python3 -I models/causal_kernel/check_conferral_end.py` | the end of a conferral (CC 2.4.1.1): 33 cases with a hand-written answer for every act, in every arrival order; the fixture for persist gives the same answers | `RESULT: ok` |
| `python3 -I models/causal_kernel/check_conferral_content.py` | room content after a member's seat ends, where the end names the rows held good (a proposal for CC 2.4.1.1): 35 cases in every arrival order; every history of up to four rows, with what the member alone and one counted row can change; three plants (three workers) | `RESULT: ok` |
| `python3 -I models/causal_kernel/check_rosters.py` | one roster mechanism, five instances: 90 properties, each with a break (three workers) | `90 properties, verdicts as recorded: True` |
| `python3 -I models/causal_kernel/check_attacks.py` | thirty-four attacks, 126 scenarios, classed HOLDS / CONCEDED / NOT EXPRESSIBLE / BROKEN (three workers) | `RESULT: ok in …s` |
| `python3 -I models/causal_kernel/check.py` | order-freeness: every set of up to six rows from two pools in every arrival order; the seventeen witnesses (three workers) | `RESULT: ok` |
| `python3 -I models/causal_kernel/check_cut.py` | the cut: order-freeness and that only a key that may cut a slot changes it (three workers) | `RESULT: ok` |
| `python3 -I models/causal_kernel/check_roomkey.py` | private rooms: voices, bindings, symbolic deniability (three workers) | `RESULT: ok in …s (77 facts)` |
| `python3 -I models/roster_fork/fork_check.py --check` | tips wait, under several counting protocols | `roster_fork: with tips waiting …` |
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
