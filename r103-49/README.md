# r103-49: the ruled election close at election-close 63ab34a (Python model)

Run each script as `python3 -I <script> <tree root> [orders]`, through grace. The outputs are beside them.

- attack_block.py: the HOLE. An honest election: 7-0 for D, and D's seating closed by A, E, F and G. Two founders
  then add ONE stale row: a recall of A at g (rcg), which only g precedes. It concludes, though no roster takes it
  (r93-49). end_fork reads it as a counted end concurrent with A's lay-down, so the lay-down is forked and rcg is the
  end. After that row, D is not moderator for ANY reader (Seats), including one that acknowledged aG.
  election_closed(ed) is False for a fresh reader and True for the reader that acknowledged aG. That reader's roster
  and its close disagree.
- attack_stale.py: the same founders run a whole election at g: recall, opening, removal of A after the recall,
  ballots, seating and C's receipt. For a fresh reader, election_closed(eb) is True while the roster keeps A
  (B not moderator). For the acknowledging reader it is False.
- orders_cases.py: check_election_close.py's 19 cases in 20 arrival orders each. All match their wanted answers,
  and no order differs.
- attack_twokeys.py: two keys of one person cast two ballots. They do not double-count: same ranking, one ballot;
  two rankings, no ballot.
