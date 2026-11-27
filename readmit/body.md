A member who resigned and was re-admitted was in no count's base and no voice of any count, for ever: `seat::left_in_past` read the leaving and ignored a later admission (a 0.4.0 answer; CIRISConstitution#218, pin list: a re-admitted member counts).

- The fix, in both languages: a key is out of a count by its leaving only while no seating of it in that scope after the leaving is in the counted row's past. It is one test, `seated_after`, shared with `stay_ended_in_past`.
- `models/causal_kernel/check_readmit.py` has 10 hand-written cases, run in every arrival order and all in the `seat` fixture. No existing scenario's answer moves.
- Plants: one in `seat.py` and two in the crate; one existing crate plant is re-pointed.
- Answers change only where a member resigned and was re-admitted before the counted row. A counted removal followed by re-admission, and a window's clause, were never affected.

No public name changes.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_019ZeGbVtHk7SfQWmSp2eLxD
