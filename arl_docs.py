R = "/home/emoore/CIRISKernel/.claude/worktrees/agent-ad781c03a48920203/"
def edit(p, reps):
    s = open(R + p).read()
    for a, b in reps:
        assert s.count(a) == 1, (p, s.count(a), a)
        s = s.replace(a, b)
    open(R + p, "w").write(s)

edit("check.sh", [('''step "check_resignation (wrap, dissolved)" resign   python3 -I models/causal_kernel/check_resignation.py
''', '''step "check_resignation (wrap, dissolved)" resign   python3 -I models/causal_kernel/check_resignation.py
step "check_agent_removal (the lift)"     agent     python3 -I models/causal_kernel/check_agent_removal.py
''')])
edit("README.md", [("all 24 steps passed", "all 25 steps passed")])
edit("models/README.md", [('''| `python3 -I models/causal_kernel/check_resignation.py` |''', '''| `python3 -I models/causal_kernel/check_agent_removal.py` | a moderator's lone removal of an AI agent's key and the members' lift of it (CC 4.5.13), with the two counts of that clause: the removal concludes on one voice of a holder of `moderate` and opens its own `moderation_overturn` window; the lift is a strict majority of the members at the head the act names, the author apart, floor two; the re-seating is a counted row over the objections it names. 31 cases in arrival orders, six planted breaks in the seat rule; the window adversary table read under recount (76 rows, 66 checks, none broken) and five planted breaks in the tables (the fallback counted over all members, the author's objection a voice, the author counted over) |
| `python3 -I models/causal_kernel/check_resignation.py` |''')])
edit("models/causal_kernel/README.md", [('''  recount breaks none of forty-seven checks over five windows (the members' check of CC 4.5.13 and the self roster's addition were added).''',
 '''  recount breaks none of sixty-six checks over five windows (the members' check of CC 4.5.13 and the self roster's addition were added;
  the members' check is counted over the members less the act's author, and the fallback over the members who voted).
  `check_agent_removal.py` reads the table and plants the clauses these replaced.''')])
edit("kernel/KERNEL.md", [
('''(the members' check of CC 4.5.13 and the self roster's addition were added on 2026-11-23), forty-seven checks of what each exists to prevent.''',
 '''(the members' check of CC 4.5.13 and the self roster's addition were added on 2026-11-23; on 2026-11-25 the members' check was counted over the members less the act's author and the moderation fallback over the members who voted), sixty-six checks of what each exists to prevent.'''),
('''answers breaks eleven, a thief evicting alone among them.''', '''answers breaks twelve, a thief evicting alone among them.'''),
])
edit("crates/ciris-kernel/CHANGELOG.md", [('''## [0.3.0]
''', '''## Unreleased

**Answers change in two windows; a moderator's lone removal of an AI agent's key and its lift (CC 4.5.13).**
Three public types change, and one trait gains a method.

What a caller must change to compile:
- `window::How` is no longer `Copy` (it is `Clone`), and gains `How::MoreOfVoted(num, den, least, against)`: an
  exhaustive `match` adds an arm, and code that copied a `How` clones it;
- an exhaustive `match` on `seat::Policy` adds `Policy::Lift`.
`window::Base`, `window::Clause` and `window::WindowSpec` are unchanged.

Answers that change:
- **The members' check (`moderation_overturn`) is counted over the members less the act's author.** The
  reference's clause is now `("object", ("more", 1, 2, 2), "others", "lifted")`; it was over `all`. This is the
  Constitution's rc22 text, ruled by Eric on 2026-11-25: "The act is lifted when a strict majority of the members
  seated at the head the act names, the act's author apart, has objected within the 48-hour window. ... The floor
  is two voices. The author's own objection is no voice, and the author is not among the members the majority is
  taken of. Where the author is one of two members no lift is possible." Where the moderator is not on the roster
  nothing changes. Where it is: its objection no longer counts, and the majority is of one member fewer. A room
  of three with the moderator a member lifts on both others (two of two) and not on one other with the moderator;
  a room of four lifts on two of the three others; a room of two cannot lift. This is table data: the crate's
  `Base::Others` already said it, and a caller's own `WindowSpec` for this window moves to `Base::Others`.
- **The moderation fallback (`moderation_fallback`) is a strict majority of the members who voted, floor two.**
  The reference's at-close clause is now `("act", ("voted", 1, 2, 2, "against"), "all", "fallback")`; it was a
  strict majority of all members. `act` is a vote for; the new answer word `against` is a vote against (the same
  row with the other polarity, not an objection); a silent member is not counted over. Ruled by the Constitution
  session on 2026-11-25; `data/governance_policy.tsv`, row `moderation_action`, already said it. Four members
  with two votes for and none against now fall back, where they did not; two for and two against do not; one
  vote for alone does not (the floor). In the crate this is `How::MoreOfVoted`.
- **`window::rule` and `window::outcome`: a duty holder's answer is what that key said.** A value that an
  at-once clause reads as `How::One` over a `Base::Scope`, said by a holder of that scope, is that key's voice,
  and any other answer of the same key is moot. Before, a moderator who was also a member and both answered and
  voted had said two things and so nothing. Tables with no such clause are read as before. A moderator's answer
  that names the fallback's landing changes nothing (a row of the table now says so).
- **`window::rule`: an opener that is also an offer or an unseat** (`win_kind() == Some(Open)` and
  `seat_kind()` `Offer` or `Unseat`) concludes only where `seat::seat_rule` concludes it too. Before, the
  opener's rule alone was read for such a row. A row that is only an opener is read as before.
- **`seat::seat_rule`: a counted row of a policy the table reads as `Policy::Lift`** concludes only as a
  re-seating (below). The reference's table reads `moderation_overturn` so; a counted row of that policy was a
  strict majority of the members before, and no fixture or check had one.

New:
- `SeatRow::removes_agent` (default `false`). An unseat of a roster seat (`SeatLaw::roster_seats`) of one key,
  `Conf::Group`, that the caller marks so concludes on its signer's one voice where that signer holds `moderate`
  over the object at the head the row names, whatever the room's protocol and however many holders. The kernel
  cannot see a key record, so the caller states the mark. Unmarked, or signed by a key that is no moderator
  there, the row is counted as any removal is and fails where it failed.
- That removal is the opener of a `moderation_overturn` window: the caller presents it with
  `win_kind() == Some(WinKind::Open)` and `window()` naming the table.
- `Policy::Lift` and `seat::lift_voices`: the lift's effect is a counted row. An offer of this policy that seats
  the key again, cites the removal (`SeatRow::content`), names the head the removal names and names objections,
  each presented as a cosignature whose `of` is the removal. Its voices are those objections' signers and no
  other key; the removal's author is no voice and is not counted over; the key seated is counted over and is no
  voice. It concludes on more than half of those members, never fewer than two, and only where the key was on
  the roster at that head (it restores and does not admit). `lift_voices` returns the author and the voices;
  `GroupCount`'s contract says what `members` and `voices` are under this policy. `Seats::tips_fold` reads the
  same count over the members the fold seats.
- No reading of the roster reads a window. Until that row is written the window reads `lifted` and the key is
  out. That gap is accepted.

Checked: `models/causal_kernel/check_agent_removal.py` (31 cases in 9,878 arrival orders, six planted breaks in
the seat rule, five in the window tables), whose rows are in the seat fixture and run the crate's rules; the
adversary table is 76 rows and 66 checks over five windows (recount breaks none, the voiding rule twelve, the
contesting rule two); ten planted breaks in the crate. Not decided here, and stated in that file: the removed
key's own objection is no voice of the count with no landing (the ended-seat rule) nor of the re-seating, but a
landing that has it in its past counts it; and a moderator whose duty ended after the head the removal names
still removes at that head.

## [0.3.0]
''')])
