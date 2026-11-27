R = "/home/emoore/CIRISKernel/.claude/worktrees/agent-ad781c03a48920203/crates/ciris-kernel/"
def edit(p, reps):
    s = open(p).read()
    for a, b in reps:
        assert s.count(a) == 1, (s.count(a), a)
        s = s.replace(a, b)
    open(p, "w").write(s)

edit(R + "src/window.rs", [
('''    /// The same, less the opener's signer: out of the voices and out of the size counted over.
    Others,
    /// The window's counted scope at the opener's head, counted over whole; the opener's signer is no voice
    /// among it (the members' check: a strict majority of the roster at the head the act names, the act's
    /// author no voice).
    AllOpenerMute,
''', '''    /// The same, less the opener's signer: out of the voices and out of the size counted over (the members'
    /// check: a strict majority of the members seated at the head the act names, the act's author apart).
    Others,
'''),
('''            Base::All | Base::AllOpenerMute => ("all", self.w.counted.as_str()),''', '''            Base::All => ("all", self.w.counted.as_str()),'''),
('''        // counted over all of them; the opener's signer no voice
        let voice = |s: &R::Key| keys.contains(s) && !(cl.over == Base::AllOpenerMute && *s == x.opener_signer);
        let yes = said
            .iter()
            .filter(|(s, v)| **v == cl.value && (voice(s) || (floor && tv.contains(*s) && cl.value == "approve")))
            .count() as u64;''', '''        let yes = said
            .iter()
            .filter(|(s, v)| {
                **v == cl.value && (keys.contains(*s) || (floor && tv.contains(*s) && cl.value == "approve"))
            })
            .count() as u64;'''),
('''                let no = said.iter().filter(|(s, v)| *v == against && voice(s)).count() as u64;''',
 '''                let no = said.iter().filter(|(s, v)| *v == against && keys.contains(*s)).count() as u64;'''),
])
edit(R + "tests/common/mod.rs", [('''                        "all_opener_mute" => Base::AllOpenerMute,
''', '')])
edit(R + "src/seat.rs", [
('''    /// author and the key it seats no voice; it is met by more than half of the members at the head the
    /// removal names, never fewer than two voices. A counted row of this policy that is no such re-seating
    /// concludes nothing.''', '''    /// author and the key it seats no voice; it is met by more than half of the members at the head the
    /// removal names, the removal's author apart, never fewer than two voices. A counted row of this policy
    /// that is no such re-seating concludes nothing.'''),
('''                let v = if pol == Some(Policy::Lift) {
                    lift_voices_with(&p, self.law, self.spec, Some(&members)).unwrap_or_default()
                } else {
                    voices(r, &p)
                };''', '''                let v = if pol == Some(Policy::Lift) {
                    let Some((author, v)) = lift_voices_with(&p, self.law, self.spec, Some(&members)) else {
                        return false;
                    };
                    mem.remove(&author); // the removal's author apart
                    v
                } else {
                    voices(r, &p)
                };'''),
('''/// cosignature. The removal's author is no voice. The row's own signers are no voices either.
pub fn lift_voices<R: SeatRow, S: CutSpec<R>>(
    p: &Past<'_, '_, R>,
    law: &SeatLaw,
    spec: &S,
) -> Option<BTreeSet<R::Key>> {''', '''/// cosignature. The removal's author is no voice. The row's own signers are no voices either.
///
/// Returns the removal's author and the voices. The count ([`Policy::Lift`]) is taken of the members at the
/// head less that author.
pub fn lift_voices<R: SeatRow, S: CutSpec<R>>(
    p: &Past<'_, '_, R>,
    law: &SeatLaw,
    spec: &S,
) -> Option<(R::Key, BTreeSet<R::Key>)> {'''),
('''    cache: Option<&MembersAt<R>>,
) -> Option<BTreeSet<R::Key>> {
    let r = p.row();
    let rem = p.get(r.content()?)?;''', '''    cache: Option<&MembersAt<R>>,
) -> Option<(R::Key, BTreeSet<R::Key>)> {
    let r = p.row();
    let rem = p.get(r.content()?)?;'''),
('''    v.remove(rem.signer());
    Some(v)''', '''    v.remove(rem.signer());
    Some((rem.signer().clone(), v))'''),
('''                        let Some(v) = lift_voices_with(p, law, spec, cache) else { return false };
                        let mem = members_at_with(p, law, spec, &obj, r.head(), "member", cache);
                        // a lift restores and does not admit: the key was on the roster at that head
                        return r.to().iter().all(|k| mem.contains(k))
                            && count_of(pol, is_offer, r.to(), &mem, &v, None, |_| 0);''', '''                        let Some((author, v)) = lift_voices_with(p, law, spec, cache) else { return false };
                        let mut mem = members_at_with(p, law, spec, &obj, r.head(), "member", cache);
                        // a lift restores and does not admit: the key was on the roster at that head
                        if !r.to().iter().all(|k| mem.contains(k)) {
                            return false;
                        }
                        mem.remove(&author); // the author is not among the members the majority is taken of
                        return count_of(pol, is_offer, r.to(), &mem, &v, None, |_| 0);'''),
('''/// - Under [`Policy::Lift`] the two are read otherwise: `voices` is [`lift_voices`] (the objections the row
///   names, the removal's author left out) and `members` is [`members_at`] at the head, with no leaving
///   subtracted. The seat rule asks besides that the key seated is among those members.''', '''/// - Under [`Policy::Lift`] the two are read otherwise: `voices` is [`lift_voices`] (the objections the row
///   names, the removal's author left out) and `members` is [`members_at`] at the head less that author,
///   with no leaving subtracted. The seat rule asks besides that the key seated is among those members.'''),
('''        // the members' check: more than half of the members, never fewer than two, the key seated no voice''',
 '''        // the members' check: more than half of the members (the caller has taken the act's author out of
        // them and out of the voices), never fewer than two; the key seated is counted over and is no voice'''),
])
