R = "/home/emoore/CIRISKernel/.claude/worktrees/agent-ad781c03a48920203/"
def edit(p, reps):
    s = open(R + p).read()
    for a, b in reps:
        assert s.count(a) == 1, (p, s.count(a), a)
        s = s.replace(a, b)
    open(R + p, "w").write(s)

edit("crates/ciris-kernel/CHANGELOG.md", [
('''  other key; the removal's author is no voice and is not counted over; the key seated is counted over and is no
  voice.''', '''  other key; the removal's author is no voice and is not counted over, and neither is the key seated (below).'''),
('''- No reading of the roster reads a window.''', '''- **The removed agent's key is apart from the lift of its own removal, on every path.** Ruled on 2026-11-25
  from the Constitution's sentence that an AI agent "acts under its own key and has no vote": the count is the
  members seated at the head the act names, the act's author apart and the removed key apart. In
  `window::rule` and `window::outcome`, `Base::Others` of a window whose opener is an unseat marked
  `removes_agent` leaves out the keys that opener removes, with its signer, so the count with no landing, a
  landing's own count and the recount all read it so. The re-seating row's members leave it out as well. A
  room of the moderator, the agent and two persons lifts on both persons (two of two) and not on one. This is
  for the lift of an agent's removal only: no other count of a room leaves agents' keys out, since the kernel
  sees no key record.
- No reading of the roster reads a window.'''),
('''Checked: `models/causal_kernel/check_agent_removal.py` (31 cases in 9,878 arrival orders, six planted breaks in
the seat rule, five in the window tables), whose rows are in the seat fixture and run the crate's rules; the
adversary table is 76 rows and 66 checks over five windows (recount breaks none, the voiding rule twelve, the
contesting rule two); nine planted breaks in the crate, each confirmed by hand. Not decided here, and stated in that file: the removed
key's own objection is no voice of the count with no landing (the ended-seat rule) nor of the re-seating, but a
landing that has it in its past counts it; and a moderator whose duty ended after the head the removal names
still removes at that head.''', '''Checked: `models/causal_kernel/check_agent_removal.py` (36 cases in 8,945 arrival orders, eight planted breaks
in the seat rule, five in the window tables), whose rows are in the seat fixture and run the crate's rules; the
adversary table is 76 rows and 66 checks over five windows (recount breaks none, the voiding rule twelve, the
contesting rule two); ten planted breaks in the crate, which CI's plants jobs run. Not decided here, and stated
in that file: a moderator whose duty ended after the head the removal names still removes at that head.'''),
])
edit("models/README.md", [
('''the re-seating is a counted row over the objections it names. 31 cases in arrival orders, six planted breaks in the seat rule;''',
 '''the removed agent's key is apart from that count on every path; the re-seating is a counted row over the objections it names. 36 cases in arrival orders, eight planted breaks in the seat rule;'''),
])
