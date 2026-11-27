def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, s.count(a), a)
        s = s.replace(a, b)
    open(p, 'w').write(s)

edit('models/tla/CONFERRAL_END.md', [
('''- **E6. Reach.** The end reaches only acts exercised under the target, deputies transitively. It never reaches
  the member set or n at any head (`Inv_MembersByPast`).
''','''- **E6. Reach.** The end reaches only acts exercised under the target, deputies transitively. It never reaches
  the member set or n at any head (`Inv_MembersByPast`).
  A deputy hangs from a deputy edge, itself an act under the standing, and ends with the seat: the edge passes
  both bits down, each to its own. The grantee's own edge (the first hop) needs no sub-delegation. An onward
  hop, a deputy's own deputy edge, counts only under an edge that carries sub-delegation (`E6.no_sub`), and
  no act counts more than five deputy edges from the seat (`E6.depth`; the cap is a parameter of the call).
  These two gates are in the reference and the crate and are checked by cases only: the spec has one deputy
  edge, where neither can apply (section H).
'''),
('''35 cases and 51 act answers. Each act has `counted`, `in_force` and the `rule` that decides it, and 12 rules
appear.
''','''41 cases and 87 act answers. Each act has `counted`, `in_force` and the `rule` that decides it, and 14 rules
appear.
'''),
('''The cases:
- persist's six;
''','''**The deputy gates and the cross-check.** `E6.no_sub` and `E6.depth` read two things the spec does not have: a
deputy edge that is itself under an edge, and the count of edges above an act. The spec has one deputy edge
(`sub` on one of B's acts) and one act under it (c1). `conferral_xcheck.py` builds c1 with `via` and never
marks a row as a deputy edge or as carrying sub-delegation, and it calls the reference with the default cap
of 5. In every state it compares, c1 is one edge from the seat and is not an onward hop, so neither gate can
decide an answer there: the reference's answers for those states are computed as before. This was reasoned
from the code and the six deputy cases; TLC was not run for this change.

The cases:
- deputy chains: depth two before and after the end, no sub-delegation on the first edge, a chain of six, the
  cap as a parameter, and a chain whose middle edge is receipted and whose top is not. A case with many rows
  is checked in its first 200 arrival orders;
- persist's six;
'''),
('''`models/causal_kernel/check_conferral_two.py` judges the act under each record with the reference of sections
A to H and joins the answers bit by bit: the act counts for an owner when it counts under the grant and under
a binding of that owner, and it is in force when it is in force under both.

- The grant: head G0 (the bundle in force) and the count's end EG.
''','''`models/causal_kernel/check_conferral_two.py` judges the act under each record with the reference of sections
A to H and joins the answers bit by bit: the act counts for an owner when it counts under the grant and under
a binding of that owner, and it is in force when it is in force under both.

- The grant: head G0 (the bundle in force) and the count's end EG. The case table also has G1, a later
  bundle version naming G0.
'''),
('''histories, 238,140 states over the five readings, about 12 s.
''','''histories, 238,140 states over the five readings, about 17 s.
'''),
('''**Fixture.** `crates/ciris-kernel/tests/fixtures/conferral_two.json` has 11 cases under `acc`, each with a
hand-written answer per act and owner that the run must give. No Rust test reads it. It is for Verify's
standing walk and an adopter's own code.

**For the crate.** No new code: a caller runs `conferral::answers` once for the grant and once per binding,
and joins the answers bit by bit.

**Limits.** This is a Python run over the reference, not a TLA+ configuration. It has one grant head, two
re-bindings, at most two acts, and one receipt per record (the first owner's, and the count's). Not modelled:
the new owner declining or withdrawing its acceptance, a grant end concurrent with a new bundle version, a
new bundle version at all, the reader's line, a receipt by the second owner.
''','''**The rule as one function of the held rows.** `chain_answers` in the same file follows the names (the act's
acceptance, the acceptance's binding), judges the act under the grant and under that binding with the
reference, and joins the bits. It gives, per act, the binding it stands under and that binding's owner, the
two bits, and the rule that decides under each record; or why the act counts for nobody (`no_acceptance`,
`names_binding`, `not_an_acceptance`, `acceptance_names_no_binding`, `not_the_owners_acceptance`). The crate's
`standing::answers` is the same function.

It reads the causal past from what the rows name. The run above builds each record's ledger from the act's
head alone. The two are compared on every state of `acc`, and differ on 2,268 answers, all of one kind: a
backdated act that names the first owner's acceptance and, as its previous act, an act signed under the new
owner. Through that act it has the re-binding in its past. The rule then gives E4 (an act with the end in its
past does not count), and the ledger, which does not carry the previous act, gives "counted, out of force".
Neither is in force. Only a backdating node signs such an act, and `backdated` holds under both. The fixture
case `backdated_after_an_act_under_the_new_owner` states it. **For the Constitution:** whether an act counts
at its binding when it reaches that binding's end only through its signer's previous act is E4 read literally
here; the recommended wire of sections A to H carries no `prev` on an act, and with none the question does
not arise.

**A later bundle version.** G1 names G0. The rules of sections A to H are applied as they are, and the cases
are hand-written from them (the act stands on A0 under B0, so the first owner's bits are the grant's):

| | Rows | What the rules give |
|---|---|---|
| (a) | the grant counted under G0; G1 exists; an act naming G1 and A0; no end held | counted and in force (`no_end`) |
| (b) | an act naming G0, at a reader that acknowledged G1; no end held | counted at G0 and in force. Nothing refuses a row for naming an older version, and the reader's line is not applied to an authored act (section C) |
| (c) | the grant's end naming G1; acts at G0 and at G1 | both counted, neither in force (E2); the one the count receipted is in force (E8) |
| (d) | the grant's end naming G0; acts at G0 and at G1 | the act at G0 counted, not in force (E2); the act at G1 not counted (E3), unless the count holds a clean receipt of it concurrent with its end: then counted, not in force (one say) |
| (d), a reader at G1 | the same rows, at a reader that acknowledged G1, which does not have the end in its past | the end is void for that reader (the line on the end), and both acts are counted and in force |
| | the grant's end naming G0 with G1 in its own past | the end concludes nothing (E1); both acts counted and in force |

**For the Constitution, on those answers.** None of these is a ruling; no rule was added to change one.
- (a) holds because no rule of sections A to H reads where a standing began: the reference has no row for
  the grant itself, only its heads and its end. A grant counted under G0 therefore stands under every later
  version until an end is held. If the text means a bundle version that no longer carries the grant to end
  it, or a grant to be counted again under a new version, that is a rule this model does not have.
- (b) with (c): a node that is behind, or says it is, keeps signing acts at G0 after the end at G1, and each
  counts at G0 and is never in force. That is the limit section A states for any act at an old head.
- (d), a reader at G1: the count's end at G0 is void for every reader that acknowledged a G1 the end is not
  in the past of, so the grant has not ended for them and an act at G1 is in force. That is CC 2.7.8 applied
  to the end as to any counted cut (`end_old_fork_for_reader`). For a grant it means an end signed at the
  earlier version, concurrent with the new version, ends nothing for readers of the new version: the count
  has to end the grant again at G1. Two readers of the same rows then differ on (d) by their own
  acknowledgement, as the line intends, and the difference lasts until that second end.

**Fixture.** `crates/ciris-kernel/tests/fixtures/conferral_two.json` has 21 cases under `acc` (the 11 of the
first round, two on the chain read from the rows, eight with the later bundle version), each with a
hand-written answer per act and owner that the rule must give. Each case also carries why: the binding and
the two deciding rules, or the reason the act counts for nobody. `tests/conferral_two.rs` replays it through
`standing::answers`. It is also for Verify's standing walk and an adopter's own code.

**For the crate.** `standing::answers` (`crates/ciris-kernel/src/standing.rs`): the caller gives the rows of
one node under one grant and its causal past, and gets the joined answer per act. It runs
`conferral::answers` once for the grant and once per binding an act stands under. It is checked by the 21
cases and by one row withheld at a time; no run of every state compares it with the reference.

**Limits.** This is a Python run over the reference, not a TLA+ configuration. The run of every state has one
grant head, two re-bindings, at most two acts, and one receipt per record (the first owner's, and the
count's); the later bundle version is in the case table only. Not modelled: the new owner declining or
withdrawing its acceptance, a row for the grant itself (so nothing about a grant counted again under a new
version), a bundle version that drops the grant, a key removal, a deputy under such an act, a receipt by the
second owner.
'''),
])

edit('crates/ciris-kernel/README.md', [
('''(`tests/fixtures/conferral_end.json`; 35 cases, each with its rows listed in every order the fixture gives
and in reverse).''','''(`tests/fixtures/conferral_end.json`; 41 cases, each with its rows listed in every order the fixture gives
and in reverse).'''),
('''`tools/kernel_crate_plants.sh` plants 69 breaks,''','''`tools/kernel_crate_plants.sh` plants 98 breaks,'''),
])
s = open('crates/ciris-kernel/README.md').read()
a = '''A second run withholds one row at a time from the caller's past. Every act is then either undecided, naming
the row that is missing, or judged exactly as it is over the rows that are held.
'''
assert s.count(a) == 1
s = s.replace(a, a + '''
The deputy gates (an onward hop needs sub-delegation on the edge above it; at most `Standing::deputy_depth`
edges from the seat) are in six of those cases. The TLA+ spec has one deputy edge and does not reach them.

### One row under a root grant and an owner binding

`standing::answers` is checked against the case table of `models/causal_kernel/check_conferral_two.py`
(`tests/fixtures/conferral_two.json`; 21 cases under its reading `acc`, rows as listed and in reverse): per
act and owner whether it counts and is in force, the binding it stands under and the rule that decides under
each record, or why it counts for nobody. A second run withholds one row at a time. Cases only: the Python
run of every state checks the reference, not the crate.
''')
open('crates/ciris-kernel/README.md', 'w').write(s)

edit('crates/ciris-kernel/CHANGELOG.md', [
('''# Changelog — ciris-kernel

''','''# Changelog — ciris-kernel

## Unreleased

Deputy chains in `conferral`, and a new module `standing`.

- `conferral::answers` reads two gates on a deputy's chain. An onward hop (a deputy edge that itself has a
  `via`) counts only under an edge that carries sub-delegation: rule `E6.no_sub`. No act counts more than
  `Standing::deputy_depth` deputy edges from the seat: rule `E6.depth`. The grantee's own edge needs no
  sub-delegation, and a deputy still ends with the seat (`E6.upstream`).
- **Source-breaking:** `conferral::Standing` gains the field `deputy_depth: usize`; a struct literal must
  state it. `conferral::DEPUTY_DEPTH` (5) is the text's cap. `conferral::Rule` gains `Depth` and `NoSub`; a
  `match` over it without a wildcard must name them.
- `ConferralRow` gains `deputy_edge()` and `sub_delegation()`, both defaulting to false. With the defaults and
  a cap of at least 1, every answer of 0.3.0 is unchanged: a row is an onward hop only where the caller says
  it is a deputy edge. A caller with chains of deputies must present both, or an onward hop is read as a
  deputy's plain act and counts.
- `standing::answers`: one row that needs two standings, a root grant and an owner binding (CC 3.1.2.1). The
  act names its bundle version and the owner's acceptance of the grant; the acceptance names its binding; a
  re-binding ends the binding before it. The function runs `conferral::answers` under the grant and under the
  binding and joins the bits, and returns per act the binding and its owner, `counted`, `in_force` and the
  rule under each record (`Answer::Stands`), or why the act counts for nobody (`Answer::Nobody`), or the row to
  fetch (`Answer::Undecided`). It reads the causal past as the rows name it.
- Fixtures: `conferral_end.json` has 41 cases and 87 act answers (six deputy-chain cases; each case states
  `deputy_depth`, and a row may state `sub_delegation`). `conferral_two.json` has 21 cases, each row states
  the fields a rule reads (`head`, `on`, `owner`), and each case states `reader_acks` and `why`.
  `tests/conferral_two.rs` replays it.
- Checked by cases only. The TLA+ spec has one deputy edge, where neither gate applies; TLC was not run for
  this change.

'''),
])

edit('crates/ciris-kernel/ADOPTING.md', [
('''**A removal in a room's content**, for `content::answers`.''','''**A deputy edge**, for `conferral::answers`. This is the deputy of an exercised standing, not the delegation
chain of `Seats::stands` above.
- The edge is a `Kind::Act` signed by whoever deputizes, naming the head it is at. `deputy_edge()` is true on
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

**A grant chain**, for `standing::answers`: the rows of one node under one root grant.
- Each bundle version: `Kind::Bundle`. The causal past must have an earlier version in a later one's past.
- Each owner binding: `Kind::Binding`, `owner()` the owner. A re-binding has `on()` the binding it ends. Two
  re-bindings of one binding are refused (`Refused::SeveralEnds`).
- Each owner's acceptance of the grant: `Kind::Acceptance`, signed by that owner, `on()` its binding. One
  signed by another key is nobody's acceptance.
- Each act: `Kind::Act`, `head()` the bundle version it names, `on()` the acceptance it stands on. An act
  with `on()` a binding, or none, counts for nobody.
- The grant's end: `Kind::GrantEnd`, `head()` its bundle version. A receipt: `Kind::Receipt`, `on()` the act.
  The grant's `Standing::role` says who receipts under the grant; under a binding only its owner does.
- Give the real past. An act that reaches a re-binding through any row it names has that end in its past and
  does not count under the binding it ended (`conferral_two.json`,
  `backdated_after_an_act_under_the_new_owner`).
- Not checked here: that the act's signer is the node the binding binds. Present one node's acts.

**A removal in a room's content**, for `content::answers`.'''),
])

edit('crates/ciris-kernel/FORMAL_GAPS.md', [
('''| `ops::rule`, `seat::covers`,''','''| `standing::answers` (built on `conferral::answers`; the deputy gates of `conferral::answers`, `E6.no_sub` and `E6.depth`, are in the same class) | | `ConferralEnd` has one deputy edge and no second record: it reaches neither | cases (`check_conferral_two.py`, 21 cases under `acc`, and one row withheld at a time; `conferral_end.py`, 6 deputy-chain cases). The Python run of every state checks the reference, not the crate |
| `ops::rule`, `seat::covers`,'''),
('''| cases only | 5 |''','''| cases only | 6 |'''),
])

edit('models/README.md', [
('''the end of a conferral (CC 2.4.1.1): 35 cases with a hand-written answer for every act, in every arrival order;''',
 '''the end of a conferral (CC 2.4.1.1): 41 cases with a hand-written answer for every act, in every arrival order (the first 200 of a case with many), deputy chains with their sub-delegation and depth gates included;'''),
('''seven properties, 1,344 histories, 11 cases;''','''seven properties, 1,344 histories, 21 cases (a later bundle version among them); the rule as one function of the held rows, compared with the per-record ledgers on every state;'''),
])
