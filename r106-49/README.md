# r106-49: the r104 fix at election-close 6a49f09 (Python model)

Run as `python3 -I <script> <tree root> [orders]`. check_close.out: RESULT ok, 30 cases, 372 orders, 17 of 17 plants.
attack_block and attack_stale still hold.
- attack_line.py: the r104 world now behaves as stated (none: D; R@aG: A, not closed; R@ed: D, closed). (a) A lays
  the seat down again at aG and the honest election cites that lay-down: D for R@aG and R@ed, while a fresh reader
  waits (A's two lay-downs fork, and no counted end can resolve them, since no seat is left to end). (a') the same,
  with the honest election citing lm0: nobody for every reader. (b) R acknowledging the founders' stale seating eb
  seats nobody: holds.
- attack_regrind.py and dbg_b2.py: the HOLE. A stale opening is never behind a reader's line (reader_void holds eb
  but not opg). After the honest election closed, and R acknowledged ed, B and C write ONE stale opening at g citing
  lm0. D is unseated for every reader, R@ed included. It can be repeated after every re-run.
