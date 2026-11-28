# r90-49: the election close at release-0.5.0-wip 11804e1

Scripts take the tree root as their argument: `python3 -I <script> <tree root>` (run through grace).

- attack_g3.py: the G3c rows plus one receipt by C of B's seating. The close base is the intersection of the
  seatings' electorates, so it shrinks to {C}; B's seating closes against a 7-0 vote for D, and
  election_closed (no reader) reports it closed even for a reader whose line rejects it. Output: attack_g3.out.
- attack_close.py: decline after the close, ties, ballot stuffing, leavers, receipts across seatings, 40 arrival
  orders each; all as the rules say. Output: attack_close.out. (D3, D4 and R3 carry wrong expectations: a seating
  with a concluded seating in its past fails C2.)
- dbg.py: which rival seatings conclude (the C2 point above).
- check_election.out: the full run, RESULT ok, 0 pending.

## For the integrator: stale PENDING text in models/causal_kernel/check_election.py

PENDING is already folded in and emptied at line ~899: b5 went into CASES (~895), and H2b, G3c and G3b into
LINE_CASES (~898). Three places still describe it as waiting for the head rules:
- the docstring, line ~33 ("PENDING: a case the merged tree must pass once the head rules land; ...");
- the comment at line ~812 ("Kept as a case the merged tree must pass once `heads` lands: PENDING until then");
- lines ~837 to 889, which build PENDING only for 895 to 899 to fold and empty it, together with the PENDING loop
  in main() (~1045) and the "%d pending the head rules" count in the RESULT line.
These can be written as the cases they now are.

Leave the "must not rely on a ranked seating" lines in seat.rs and seat.py as they are: the election stays out of
0.5.0 (CIRISConstitution#241).
