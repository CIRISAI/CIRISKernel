def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, s.count(a), a)
        s = s.replace(a, b)
    open(p, 'w').write(s)

edit('models/tla/CONFERRAL_END.md', [
('''  both bits down, each to its own. The grantee's own edge (the first hop) needs no sub-delegation. An onward
  hop, a deputy's own deputy edge, counts only under an edge that carries sub-delegation (`E6.no_sub`), and
  no act counts more than five deputy edges from the seat (`E6.depth`; the cap is a parameter of the call).
  These two gates are in the reference and the crate and are checked by cases only: the spec has one deputy
  edge, where neither can apply (section H).
''','''  both bits down, each to its own. Nothing marks a row as a deputy edge: an act is one exactly when another
  act names it as the edge it is under (`via`), and an edge that itself has a `via` is an onward hop, a
  deputy deputizing. The grantee's own edge (the first hop) needs no sub-delegation. An act whose edge is an
  onward hop counts only if the edge above that one carries sub-delegation (`E6.no_sub`), and no act counts
  more than five `via` hops from the grantee's edge (`E6.depth`; the cap is a parameter of the call). Both
  are read from the rows' `via` alone, so no presentation of the onward row passes them. The onward row
  itself, judged as an act, is its signer's own act one hop higher: it counts there and confers nothing.
  These two gates are in the reference and the crate and are checked by cases only: the spec has one deputy
  edge, where neither can apply (section H).
'''),
('''41 cases and 87 act answers.''', '''42 cases and 92 act answers.'''),
('''**The deputy gates and the cross-check.** `E6.no_sub` and `E6.depth` read two things the spec does not have: a
deputy edge that is itself under an edge, and the count of edges above an act. The spec has one deputy edge
(`sub` on one of B's acts) and one act under it (c1). `conferral_xcheck.py` builds c1 with `via` and never
marks a row as a deputy edge or as carrying sub-delegation, and it calls the reference with the default cap
of 5. In every state it compares, c1 is one edge from the seat and is not an onward hop, so neither gate can
decide an answer there: the reference's answers for those states are computed as before. This was reasoned
from the code and the six deputy cases; TLC was not run for this change.
''','''**The deputy gates and the cross-check.** `E6.no_sub` and `E6.depth` read two things the spec does not have: a
deputy edge that is itself under an edge, and the count of `via` hops above an act. The spec has one deputy
edge (`sub` on one of B's acts) and one act under it (c1). `conferral_xcheck.py` builds c1 with `via` one of
B's acts, and B's acts have no `via`; it calls the reference with the default cap of 5. In every state it
compares, c1 is one hop from the grantee's edge and its edge is not an onward hop, so neither gate can decide
an answer there: the reference's answers for those states are computed as before. The reference reads no
mark of a deputy edge. This was reasoned from the code and the seven deputy-chain cases; TLC was not run for
this change.
'''),
('''- deputy chains: depth two before and after the end, no sub-delegation on the first edge, a chain of six, the
  cap as a parameter, and a chain whose middle edge is receipted and whose top is not. A case with many rows
  is checked in its first 200 arrival orders;
''','''- deputy chains: depth two before and after the end, no sub-delegation on the first edge (the onward row is
  a row like any act of the deputy's, and the act under it does not count), none on the second edge of
  three, a chain of six, the cap as a parameter, and a chain whose middle edge is receipted and whose top is
  not. A case with many rows is checked in its first 200 arrival orders;
'''),
])
edit('crates/ciris-kernel/README.md', [
('''(`tests/fixtures/conferral_end.json`; 41 cases,''', '''(`tests/fixtures/conferral_end.json`; 42 cases,'''),
('''The deputy gates (an onward hop needs sub-delegation on the edge above it; at most `Standing::deputy_depth`
edges from the seat) are in six of those cases.''','''The deputy gates (an act under an onward hop needs sub-delegation on the edge above that hop; at most
`Standing::deputy_depth` `via` hops from the grantee's edge; both read from the rows' `via`, with no mark of
an edge) are in seven of those cases.'''),
])
edit('crates/ciris-kernel/CHANGELOG.md', [
('''- `conferral::answers` reads two gates on a deputy's chain. An onward hop (a deputy edge that itself has a
  `via`) counts only under an edge that carries sub-delegation: rule `E6.no_sub`. No act counts more than
  `Standing::deputy_depth` deputy edges from the seat: rule `E6.depth`. The grantee's own edge needs no
  sub-delegation, and a deputy still ends with the seat (`E6.upstream`).
''','''- `conferral::answers` reads two gates on a deputy's chain, both from the rows' `via` and nothing else. A row
  is a deputy edge exactly when another act's `via` names it, and an edge that itself has a `via` is an
  onward hop. An act whose edge is an onward hop counts only if the edge above that one carries
  sub-delegation: rule `E6.no_sub`. No act counts more than `Standing::deputy_depth` `via` hops from the
  grantee's own edge: rule `E6.depth`. The grantee's own edge needs no sub-delegation, and a deputy still
  ends with the seat (`E6.upstream`). No mark of an edge is read, so no presentation of the onward row passes
  a gate. The onward row itself is its signer's own act one hop higher and counts as that.
'''),
('''- `ConferralRow` gains `deputy_edge()` and `sub_delegation()`, both defaulting to false. With the defaults and
  a cap of at least 1, every answer of 0.3.0 is unchanged: a row is an onward hop only where the caller says
  it is a deputy edge. A caller with chains of deputies must present both, or an onward hop is read as a
  deputy's plain act and counts.
''','''- `ConferralRow` gains `sub_delegation()`, defaulting to false: a fact the edge row states. **An answer of
  0.3.0 changes** where a caller already presented a chain two edges deep: an act whose `via` names a row
  that has a `via` itself counted in 0.3.0, and now counts only if the row above carries `sub_delegation()`
  and the chain is within the cap. A chain one edge deep is unchanged at a cap of at least 1.
'''),
('''- Fixtures: `conferral_end.json` has 41 cases and 87 act answers (six deputy-chain cases; each case states
  `deputy_depth`, and a row may state `sub_delegation`).''','''- Fixtures: `conferral_end.json` has 42 cases and 92 act answers (seven deputy-chain cases; each case states
  `deputy_depth`, and a row may state `sub_delegation`; rows no longer state `sub`, which marked a deputy
  edge and was read by nothing).'''),
])
edit('crates/ciris-kernel/ADOPTING.md', [
('''- The edge is a `Kind::Act` signed by whoever deputizes, naming the head it is at. `deputy_edge()` is true on
  it. `sub_delegation()` is true where the deputy may deputize onward.
- The grantee's own edge has no `via`. An onward edge, signed by a deputy, has `via` the edge that deputy is
  under, and counts only if that edge has `sub_delegation()`.
- A deputy's act has `via` its edge and `deputy_edge()` false.
- An onward edge presented without `deputy_edge()` is read as a deputy's plain act: it counts with no
  sub-delegation above it, and so does everything under it, with no error
  (`conferral_end.json`, `deputy_chain_no_sub`).
- `Standing::deputy_depth` is the cap, `conferral::DEPUTY_DEPTH` (5) by the text. The depth is the `via` hops
  above a row, plus one if the row is itself an edge. Every edge of the chain must be among the rows; one
  that is not is the row an `Undecided` names.
- In the fixture a deputy edge is `sub: true` and one that may be passed on is `sub_delegation: true`.
''','''- The edge is a `Kind::Act` signed by whoever deputizes, naming the head it is at. Nothing marks it: a row is
  an edge exactly when another act's `via` names it. `sub_delegation()` is true on it where the deputy may
  deputize onward.
- The grantee's own edge has no `via`. An onward edge, signed by a deputy, has `via` the edge that deputy is
  under. A deputy's act has `via` its edge.
- The gates are read from `via` alone. An act whose edge has a `via` itself counts only if the row above
  that edge has `sub_delegation()`, however the onward row is presented
  (`conferral_end.json`, `deputy_chain_no_sub`).
- The onward row itself is judged as its signer's own act, one hop higher, and counts there. Do not read its
  `counted` as "this deputation stands": ask about an act under it.
- What the crate cannot check is the `via` itself. An act presented with a `via` nearer the seat than the
  edge it was made under passes: derive `via` from the signed row, never from the caller's own reckoning.
- `Standing::deputy_depth` is the cap, `conferral::DEPUTY_DEPTH` (5) by the text. The depth is the `via` hops
  from a row up to the grantee's own edge. Every edge of the chain must be among the rows; one that is not
  is the row an `Undecided` names.
- In the fixture an edge that may be passed on is `sub_delegation: true`.
'''),
])
edit('crates/ciris-kernel/FORMAL_GAPS.md', [
('''`conferral_end.py`, 6 deputy-chain cases)''', '''`conferral_end.py`, 7 deputy-chain cases)'''),
])
edit('models/README.md', [
('''the end of a conferral (CC 2.4.1.1): 41 cases''', '''the end of a conferral (CC 2.4.1.1): 42 cases'''),
])
