# r91-49: the proposed election close, attacked before it is built

The proposal: (1) the base is the electorate at the vacancy the id row names (one head); a seating that reads
another vacancy is of another election. (2) A lay-down outside the id row's past changes nothing there. (3) The close
is read on the reader's line. (4) Every input goes through persons and the key view.

Probes run on release-0.5.0-wip 11804e1 (seat.py's own C1 reading for the electorates), as
`python3 -I <probe> <tree root>`; the outputs are beside them.

- probe_rule1.py: the G3 rows under (1) and (2). B's seating states lm1, A's backdated lay-down. Its election's
  electorate is ABC and its base AC, and A is no forker there because lm2 changes nothing in it (2). A and C
  receipt it: CLOSED. D's election (lm2, 7-0 for D) has base ABCEFG, and E, F, G make 3 of 6: open. The G3c attack
  survives, and it is cleaner than today's.
- probe_recall.py: no holder needed. B and C (two of the three founders) recall A and remove A at the founding row
  (past only g). Both conclude. Their seating's vacancy has electorate BC and base C, and C's receipt closes it.
  D's election closes too in this probe (the probe reads departures as today does; see the next probe). That is two
  closed elections for one seat.
- probe_departed.py: today's close, not the proposal. A counted removal that the roster does not take (A is still a
  member for every reader) still drops A from the close base, because `departures` reads the raw concluded unseats.
  closed(ed) flips from False to True for both readers.
