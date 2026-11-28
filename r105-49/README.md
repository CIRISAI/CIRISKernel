# r105-49: re-attack at election-close 629bf3a (Python model)

The r103 and r104 scripts re-run unchanged (outputs beside them; check_close.out: RESULT ok, 27 cases, 336 orders,
15 of 15 plants).
- The r103 holes (attack_block, attack_stale) stay fixed.
- The r104 hole (attack_holder, dbg_holder) is still OPEN. A's lay-down with only g in its past is no vacancy for a
  reader that acknowledged aG (reader_ends holds lm0), yet that reader's roster takes it, so A is not moderator. The
  honest election seats D for a fresh reader and nobody, ever, for that reader.
- attack_open_kv.py: the opening's voices through the key view hold. A revocation that holds the opening, or holds
  the key's ballot (which names the opening), keeps the cosign. A revocation that holds only g drops it, and the
  opening falls to 2 of 5.
