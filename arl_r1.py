R = "/home/emoore/CIRISKernel/.claude/worktrees/agent-ad781c03a48920203/crates/ciris-kernel/"
def edit(p, reps):
    s = open(p).read()
    for a, b in reps:
        assert s.count(a) == 1, (s.count(a), a)
        s = s.replace(a, b)
    open(p, "w").write(s)

edit(R + "src/window.rs", [
('''use crate::seat::{members_in, members_in_scopes, Obj, SeatKind, SeatLaw, SeatRow};''',
 '''use crate::seat::{members_in, members_in_scopes, seat_rule, Obj, SeatKind, SeatLaw, SeatRow};'''),
('''    /// It opens a window.
    Open,''', '''    /// It opens a window. A row may be an act of the seat as well (an offer or an unseat that opens its own
    /// window: a moderator's lone removal of an agent's key): it then concludes only where the seat's rule
    /// concludes it too.
    Open,'''),
('''/// How a clause counts.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum How {''', '''/// How a clause counts.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum How {'''),
('''    MoreAtLeast(u64, u64, u64),
}''', '''    MoreAtLeast(u64, u64, u64),
    /// `MoreOfVoted(num, den, least, against)`: more than `num / den` of the keys of the base that voted, and
    /// never fewer than `least` voices. A key voted if it said the clause's value or `against`; a silent key
    /// is not counted over (the moderation fallback: "a strict majority of the members who voted, never fewer
    /// than two voices").
    MoreOfVoted(u64, u64, u64, String),
}'''),
('''    /// The same, less the opener's signer.
    Others,''', '''    /// The same, less the opener's signer: out of the voices and out of the size counted over.
    Others,
    /// The window's counted scope at the opener's head, counted over whole; the opener's signer is no voice
    /// among it (the members' check: a strict majority of the roster at the head the act names, the act's
    /// author no voice).
    AllOpenerMute,'''),
('''            Base::All => ("all", self.w.counted.as_str()),''', '''            Base::All | Base::AllOpenerMute => ("all", self.w.counted.as_str()),'''),
('''    // a voice that says two things says nothing
    let by = ops::group_by(answers.iter().copied().filter(|a| voters.contains(a.signer()) && !is_wd(a)), |a| {
        a.signer().clone()
    });''', '''    // a duty holder's single-signature answer (a value an at-once clause reads as one voice over a named scope,
    // said by a holder of that scope) is what that key said: a vote the same key also cast is moot
    let mut duty: BTreeMap<&str, &Base> = BTreeMap::new();
    for cl in &w.at_once {
        if cl.how == How::One && matches!(cl.over, Base::Scope(_)) {
            duty.insert(cl.value.as_str(), &cl.over);
        }
    }
    let duty_word = |a: &R| a.says().and_then(|s| duty.get(s.as_ref()).copied());
    let acted: BTreeSet<&R::Key> = answers
        .iter()
        .copied()
        .filter(|a| voters.contains(a.signer()) && !is_wd(a))
        .filter(|a| duty_word(a).is_some_and(|b| x.base(b).contains(a.signer())))
        .map(|a| a.signer())
        .collect();
    let moot = |a: &R| acted.contains(a.signer()) && duty_word(a).is_none();
    // a voice that says two things says nothing
    let by = ops::group_by(answers.iter().copied().filter(|a| voters.contains(a.signer()) && !is_wd(a) && !moot(a)), |a| {
        a.signer().clone()
    });'''),
('''        let keys = x.base(&cl.over);
        let yes = said
            .iter()
            .filter(|(s, v)| {
                **v == cl.value && (keys.contains(*s) || (floor && tv.contains(*s) && cl.value == "approve"))
            })
            .count() as u64;
        let n = keys.len() as u64;
        match cl.how {
            How::AtLeast(num, den, least) => yes >= core::cmp::max(least, (num * n).div_ceil(den)),
            How::More(num, den) => yes * den > num * n,
            How::MoreAtLeast(num, den, least) => yes * den > num * n && yes >= least,
            How::One => yes >= 1,
            How::Strict => 2 * yes > n,
        }''', '''        let keys = x.base(&cl.over);
        // counted over all of them; the opener's signer no voice
        let voice = |s: &R::Key| keys.contains(s) && !(cl.over == Base::AllOpenerMute && *s == x.opener_signer);
        let yes = said
            .iter()
            .filter(|(s, v)| **v == cl.value && (voice(s) || (floor && tv.contains(*s) && cl.value == "approve")))
            .count() as u64;
        let n = keys.len() as u64;
        match &cl.how {
            &How::AtLeast(num, den, least) => yes >= core::cmp::max(least, (num * n).div_ceil(den)),
            &How::More(num, den) => yes * den > num * n,
            &How::MoreAtLeast(num, den, least) => yes * den > num * n && yes >= least,
            How::MoreOfVoted(num, den, least, against) => {
                let no = said.iter().filter(|(s, v)| *v == against && voice(s)).count() as u64;
                yes * den > num * (yes + no) && yes >= *least
            }
            How::One => yes >= 1,
            How::Strict => 2 * yes > n,
        }'''),
('''        let scope = w.opener.as_ref().unwrap_or(&w.counted);
        return Some(members_in(&rows, &past, law, spec, &obj, r.head(), scope).contains(r.signer()));''',
 '''        // an act that opens its own window is validly made by the seat's rule too
        if matches!(r.seat_kind(), SeatKind::Offer | SeatKind::Unseat) && !seat_rule(p, law, spec, &|_| true) {
            return Some(false);
        }
        let scope = w.opener.as_ref().unwrap_or(&w.counted);
        return Some(members_in(&rows, &past, law, spec, &obj, r.head(), scope).contains(r.signer()));'''),
('''/// The conclusion rule for a window row; `None` for a row that is not one (conclude it by the seat).
pub fn rule''', '''/// The conclusion rule for a window row; `None` for a row that is not one (conclude it by the seat). An
/// opener that is also an offer or an unseat is concluded here by both rules.
pub fn rule'''),
])
