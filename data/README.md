# `data/` — what the kernel is run on

Every file here is copied unchanged from the parent repository at commit `60c741e`, except `family_placement.json`
(derived by `tools/family_placement.py`, its pin below) and the five policy files
(`governance_policy.tsv`, `governance_policy.json`, `governance_policy_vectors.json`, `governance_policy_acts.tsv`,
`consensus_protocols.tsv`), copied unchanged from the Constitution's `rc23` at commit
`76965eb434b24663e50dc04c9387ef713a87c69b` (`constitution/` for the tables, `manifests/` for the two JSON files). The
table's own pin, `policy_sha256` in the two manifests, is `a304b48583c14acd283ab4dce4dbdfe0bceb9e6f2a566da95e95b37447cafec0`:
a content hash of the table, not a commit. The steps that brought the acts table there: an infrastructure community's
kind and a node's seat (4c165f8); its record changes under its founders' protocol (6c60be9); a record change meets the
protocol in force and the standing default together, and a family has its rows (682e9e4); the reading of `&` where a
protocol states no rule, the group kind, and `dissolve` (2b509c8); a community's removal never takes fewer than two
voices and the member removed is no voice in it, and a founder seat over infrastructure is added only by a record
change (8c75ae7); open admission removed (`open:self_admit` and the sheet's `joiner` and `unstated` words gone), and
`community_invite`'s base `standing` (76965eb). `consensus_protocols.tsv` at 2b509c8 gives
`founder_only` a removal rule (`founder-target`, `role_at:founder:1`). The parent generates most
of them from its rule tables; the generators are not carried, so treat these as fixed inputs. **Except, for now:**
`governance_policy_acts.tsv` is copied unchanged from the Constitution's holding branch `rc23-next` at commit
`68eb8d1f7b14ef8e5c46a90dce9a9ca3dc3376f7` (the affiliation's `admit`, `record_change` and `dissolve` rows; an
affiliation is a community record whose `declared_cohort` is `affiliations`), to be re-pinned when `rc23` moves.

| File | What it is | Read by | From (parent) |
|---|---|---|---|
| `family_placement.json` | the family model's placement cells, derived: per family the placements its rows may take (the default, or the placements the CC table pins), or undecided where the cell is not table data; the table's `scopes`, `reach` and `copy`. **Provisional pin**: derived from the Constitution's `rc23-next` at commit `d5d42bfb789f8ca62ba1e82a79cbac6f0bd01fc2` (its placement lane: all 189 placements from the text), `manifests/family_model.json` sha256 `94a6ac96a22338752716bce35caa44e50e471479fc01bae5f1a553076a31499f`; provisional until it reaches `rc23` unchanged, then final (`--final`). The pin before it, final: `rc23` `d103e60`, sha256 `f5a38b47`. `python3 -I tools/family_placement.py <path to family_model.json> [--branch B --commit C]` rewrites it and `crates/ciris-kernel/src/audience_table.rs`; `--check` holds the two together | `audience.py`, `check_audience.py`; the crate's `audience::FAMILIES` | `manifests/family_model.json` (Constitution), through `tools/family_placement.py` |
| `governance_policy.tsv` | the governance policy table: one row per decision family (who may decide, the counts to enact, cancel and floor, the window and its length, whether the act is irreversible). The authored source | people | `constitution/governance_policy.tsv` |
| `governance_policy.json` | the same table as data, with each rule parsed | `seat.py`, `window.py`, `roster.py` | `manifests/governance_policy.json` |
| `governance_policy_acts.tsv` | which row of the policy table governs which counted act: one row per (act, scope, community kind), the policy rows it may take and whether the row chooses (`row`) or the act fixes it (`fixed`: the counted row states it or none; another stated policy concludes nothing). The authored source | `seat.py` (`ACTS`), into the seat fixture's law | `constitution/governance_policy_acts.tsv` |
| `consensus_protocols.tsv` | the closed set of `consensus_protocol` words a community's record may declare (CC 3.3.4): per kind, who is counted and the rule the count meets, for an admission and for a removal. A word outside it is no protocol | `seat.py` (`PROTOCOL_KINDS`, checked by `check_acts.py`); the crate's `seat::RoomProtocol` | `constitution/consensus_protocols.tsv` |
| `governance_policy_vectors.json` | test vectors for the policy table: inputs and the verdict each row gives | the parent's `check_door.py` (not carried); here for reading | `manifests/governance_policy_vectors.json` |
| `transitions.json` | the transition table: for each family, the acts, the scopes and what each does, including the key effect of each membership act | `key_plane_model.py` | `manifests/transitions.json` |
| `witnesses.tsv` | seventeen cases where judging each row on arrival gives two results from one set of rows, with both orders and both results | `check.py` | `formal/derivation/order/witnesses.tsv` |
| `divergences.json`, `divergences.tsv`, `divergences/` | the divergence list (below) | `tools/divergence_counts.py` (counts only) | `manifests/divergences.json`, `manifests/divergences.tsv`, `manifests/divergences/` |

## The divergence list

Each entry is a test: a place where the behaviour of a shipped implementation differs from the text. An entry
gives a set of rows in the kernel's row form (`case`), one named question (`ask`), the verdict the text gives
(`expect_kernel`) and the verdict the shipped code gives today (`expect_shipped`). Implementer names (`persist`,
`edge`, `agent`, `tooling`) appear in it as they do in the parent; they name the components of the parent
project whose shipped behaviour was compared. `_meta` in the JSON states the row form and the contract.

`python3 -I tools/divergence_counts.py` prints the counts. At this commit it prints `divergences: 87 entries; 72
runnable, 11 stated, 4 wording-only`. "Runnable" entries are run under the text's rule and under the shipped rule
by the parent's `tools/check_divergences.py`, which needs the parent's toolchain and is not carried; "stated"
entries cannot be expressed as rows, each with its reason; "wording-only" entries differ in words and in no
behaviour.

The per-implementer Markdown files in `divergences/` are generated views of the same entries. They mention a
returns file in the parent (`formal/derivation/divergence_returns.tsv`): an implementer that holds a verdict
wrong returns the entry there with its own case. A counterexample from a reviewer of this repository goes the
way [`../REVIEW.md`](../REVIEW.md) describes.

Nothing from the parent's vendored evidence (`constitution/vendor/`) is carried.

## `ui_primitives.json`

The screen standard as the parent carries it (a draft): twenty-four primitives, the states they are drawn in,
and the laws a screen keeps. A screen is a function of the rows a node holds, the viewer's key and the clock;
the checks that hold a screen to the kernel run in the parent repository (`formal/screen`,
`tools/check_ui_primitives.py`).
