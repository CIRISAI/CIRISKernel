# `data/` — what the kernel is run on

Every file here is copied unchanged from the parent repository at commit `60c741e`, except the four policy files
(`governance_policy.tsv`, `governance_policy.json`, `governance_policy_vectors.json`, `governance_policy_acts.tsv`),
copied unchanged from the Constitution's `rc23` at commit `f1773bf7684ebc29cfbe971474bc4064ea1de348` (the last commit
touching `constitution/governance_policy.tsv`; the branch head was `efc31033dbf1ff51a1236ddba17cd68caa11c6f5`). The
table's own pin, `policy_sha256` in the two manifests, is `8d58a472cc09beda6a962a4f579da6d5fcf5a3c63fbcd62f8db81aa84c20b873`:
a content hash of the table, not a commit. `governance_policy_acts.tsv` is copied from rc23 at commit
`4c165f86dcb1b47aba48e6fd59985e51ebd0f9ae` (an infrastructure community's kind and a node's seat); the other three
are unchanged there. The parent generates most
of them from its rule tables; the generators are not carried, so treat these as fixed inputs.

| File | What it is | Read by | From (parent) |
|---|---|---|---|
| `governance_policy.tsv` | the governance policy table: one row per decision family (who may decide, the counts to enact, cancel and floor, the window and its length, whether the act is irreversible). The authored source | people | `constitution/governance_policy.tsv` |
| `governance_policy.json` | the same table as data, with each rule parsed | `seat.py`, `window.py`, `roster.py` | `manifests/governance_policy.json` |
| `governance_policy_acts.tsv` | which row of the policy table governs which counted act: one row per (act, scope, community kind), the policy rows it may take and whether the row chooses (`row`) or the act fixes it (`fixed`). The authored source | `seat.py` (`ACTS`), into the seat fixture's law | `constitution/governance_policy_acts.tsv` |
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
