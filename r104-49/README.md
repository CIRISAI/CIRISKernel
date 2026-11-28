# r104-49: re-attack of the election close at election-close 7774f65 (Python model)

Run each as `python3 -I <script> <tree root> [orders]`.
- attack_block.py, attack_stale.py, attack_twokeys.py (from r103-49), re-run: fixed. Every variant, both readers,
  12 orders, no order differs. check_close.out: RESULT ok, 26 cases, 324 orders, 14 of 14 plants.
- attack_holder.py and dbg_holder.py: the NEW hole. A (moderate) lays the seat down from a stale device: lm0, with
  only g in its past. The honest room (D..G open 4 of 7 at aG citing lm0, D's seating, receipts) seats D for a
  fresh reader. For a reader that acknowledged aG, reader_ends holds lm0, a lay-down behind its line, so it is no
  vacancy: no election for that seat can ever stand for that reader, though its roster says A no longer holds
  moderate. Fresh and established readers disagree for good, and the established ones have no moderator and no way
  to elect one. The founders' own stale election (attack_holder rows 1, 2) seats nobody, as it should; with it held,
  the honest opening must hold opg to resolve the contest (row 3).
