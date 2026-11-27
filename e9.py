p = '/tmp/claude-1000/-home-emoore-CIRISKernel/9f476e19-79a3-4f60-8019-6f13a6523575/scratchpad/pr.md'
s = open(p).read()
a = s.index('## 1. Deputy chains')
b = s.index('## 2. `standing::answers`')
new = '''## 1. Deputy chains and their gates (`conferral`)

The gates follow from the rows' `via` and nothing else (second commit; the first read a mark on the edge row).

- A row is a deputy edge exactly when another act's `via` names it. An edge that itself has a `via` is an onward hop.
- An act whose edge is an onward hop counts only if the edge above that one carries sub-delegation: rule `E6.no_sub`. The grantee's own edge needs none.
- No act counts more than `deputy_depth` `via` hops from the grantee's own edge: rule `E6.depth`. The cap is a parameter (reference: `deputy_depth=5`; crate: `Standing::deputy_depth`, `conferral::DEPUTY_DEPTH`).
- `sub_delegation` is a fact the edge row states (crate: `ConferralRow::sub_delegation()`, default false). There is no `deputy_edge()`, and the reference's `sub` field is gone from the fixture rows: nothing read it.
- The onward row itself is judged as its signer's own act, one hop higher, and counts there. Without a mark it is the same row as any other act of that deputy, which must count. The gate decides at the act under it.
- Seven cases in `conferral_end.py`: depth two before and after the end, no sub-delegation on the first edge, none on the second of three, a chain of six, the cap at 1, and a chain whose middle edge is receipted and whose top is not. `conferral_end.json`: 35 to 42 cases, 51 to 93 act answers, 12 to 14 rules.
- **Source-breaking:** `Standing` gains a field and `Rule` gains `Depth` and `NoSub`. **An answer changes** for a caller that already presented a chain two edges deep: the lower act now needs sub-delegation above its edge.

**The TLA+ cross-check.** `tools/conferral_xcheck.py` builds the spec's one deputy act (c1) with `via` one of B's acts, B's acts have no `via`, and it calls the reference with the default cap. In every state it compares, c1 is one hop down and its edge is not an onward hop, so neither gate can decide an answer. I believe the cross-check is unaffected. This is reasoned from the code; TLC was not run.

`conferral_end.orders` now stops at a limit: a case with many rows has too many arrival orders to list, and the check reads the first 200 as before.

'''
s = s[:a] + new + s[b:]
for x, y in [
 ('- `conferral_end.json`: 35 to 41 cases, 51 to 87 act answers, 12 to 14 rules', '- `conferral_end.json`: 35 to 42 cases, 51 to 93 act answers, 12 to 14 rules'),
 ('The eight new plants were each applied to a copy of the crate, and `cargo test --release` failed on a test for each.',
  'The eight new plants were each applied to a copy of the crate, and `cargo test --release` failed on a test for each. "An onward hop passes as its signer\'s plain act" is caught by `deputy_chain_no_sub` and `deputy_chain_no_sub_at_the_second_edge`.'),
]:
    assert s.count(x) == 1, x
    s = s.replace(x, y)
open(p, 'w').write(s)
