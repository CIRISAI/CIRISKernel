# r107-49: the final confirmation, at election-close 6a49f09 (the models of election-close-rust d0b9c9f are the same)

The r103 to r106 scripts were re-run, with no new families; the outputs are here. check_close.out: ok, 30 cases.
- BLOCKER (attack_regrind.out): one stale opening at g by two founders, citing a stale lay-down, still unseats the
  closed election for every reader, including one that acknowledged its seating.
- Residuals: attack_line (a) and (a'): after a holder's second lay-down, a fresh reader waits with no counted way out,
  and an election citing the older lay-down is dead for every reader.
- Held: r103 (attack_block, attack_stale), r104 (dbg_holder), two keys of one person, and the opening's key view;
  no order differs.
