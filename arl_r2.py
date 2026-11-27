R = "/home/emoore/CIRISKernel/.claude/worktrees/agent-ad781c03a48920203/crates/ciris-kernel/"
def edit(p, reps):
    s = open(p).read()
    for a, b in reps:
        assert s.count(a) == 1, (s.count(a), a)
        s = s.replace(a, b)
    open(p, "w").write(s)

edit(R + "src/seat.rs", [
('''    /// The policy row a count is read from.
    fn policy(&self) -> Option<&Self::Word> {''', '''    /// An unseat of the roster's seat: the key it removes is an AI agent's (CC 4.5.13). The kernel cannot see
    /// a key record, so the caller states it. Such a removal concludes on its signer's one voice where that
    /// signer holds `moderate` over the object at the head the row names; see [`lift_voices`] for its lift.
    /// Default `false`: the removal is counted as any removal is.
    fn removes_agent(&self) -> bool {
        false
    }
    /// The policy row a count is read from.
    fn policy(&self) -> Option<&Self::Word> {'''),
('''    /// Not a count (a seat, not a threshold).
    NotACount,''', '''    /// CC 4.5.13, the members' check as a counted row: an offer that seats again an agent's key a moderator
    /// removed alone. Its voices are the signers of the objections it names ([`lift_voices`]), the removal's
    /// author and the key it seats no voice; it is met by more than half of the members at the head the
    /// removal names, never fewer than two voices. A counted row of this policy that is no such re-seating
    /// concludes nothing.
    Lift,
    /// Not a count (a seat, not a threshold).
    NotACount,'''),
('''                let v = voices(r, &p);
                let pol = self.law.policy_of(r.policy().map(|x| x.as_ref()));
                match pol {''', '''                let pol = self.law.policy_of(r.policy().map(|x| x.as_ref()));
                // a re-seating's voices are the objections it names, counted over the members the fold seats
                let v = if pol == Some(Policy::Lift) {
                    lift_voices_with(&p, self.law, self.spec, Some(&members)).unwrap_or_default()
                } else {
                    voices(r, &p)
                };
                match pol {'''),
('''/// Whether a count is met: `yes` voices of `n`, under `policy`.''', '''/// CC 4.5.13: a moderator of the room removes an AI agent's key alone. `r` (the row of `p`, or a row in its
/// past) is an unseat of the roster's seat of one key, counted, that the caller marks
/// ([`SeatRow::removes_agent`]), and its signer holds `moderate` over the object at the head it names.
fn lone_removal<R: SeatRow, S: CutSpec<R>>(
    r: &R,
    p: &Past<'_, '_, R>,
    law: &SeatLaw,
    spec: &S,
    cache: Option<&MembersAt<R>>,
) -> bool {
    if r.seat_kind() != SeatKind::Unseat || r.conf() != Some(Conf::Group) || !r.removes_agent() || r.to().len() != 1 {
        return false;
    }
    let (Some(scope), Some(obj)) = (r.scope(), r.obj()) else { return false };
    law.roster_seats.iter().any(|s| s == scope.as_ref())
        && members_at_with(p, law, spec, &obj, r.head(), "moderate", cache).contains(r.signer())
}

/// The voices of a re-seating row (`p.row()`, a counted offer of [`Policy::Lift`]), or `None` where it is
/// none. The row cites a removal ([`SeatRow::content`]) that is a moderator's lone removal of an agent's key
/// ([`SeatRow::removes_agent`]), of the same key, scope and object, and names the head that removal names.
/// Its voices are the signers of the cosignatures it names whose `of` is the removal: the caller presents
/// each objection to the removal (an answer `object` in its `moderation_overturn` window) as such a
/// cosignature. The removal's author is no voice. The row's own signers are no voices either.
pub fn lift_voices<R: SeatRow, S: CutSpec<R>>(p: &Past<'_, '_, R>, law: &SeatLaw, spec: &S) -> Option<BTreeSet<R::Key>> {
    lift_voices_with(p, law, spec, None)
}

fn lift_voices_with<R: SeatRow, S: CutSpec<R>>(
    p: &Past<'_, '_, R>,
    law: &SeatLaw,
    spec: &S,
    cache: Option<&MembersAt<R>>,
) -> Option<BTreeSet<R::Key>> {
    let r = p.row();
    let rem = p.get(r.content()?)?;
    if r.seat_kind() != SeatKind::Offer || !lone_removal(rem, p, law, spec, cache) {
        return None;
    }
    if rem.obj() != r.obj() || rem.scope() != r.scope() || rem.to() != r.to() || rem.head() != r.head() {
        return None; // the same seat, at the head the removal names
    }
    let mut v = BTreeSet::new();
    for n in r.names() {
        let Some(c) = p.get(n) else { continue };
        if c.seat_kind() == SeatKind::Cosign && c.of() == Some(rem.id()) {
            v.insert(c.signer().clone());
        }
    }
    v.remove(rem.signer());
    Some(v)
}

/// Whether a count is met: `yes` voices of `n`, under `policy`.'''),
('''                Some(Conf::Group) => {
                    let mem = count_members_with(p, law, spec, cache);
                    let pol = law.policy_of(r.policy().map(|x| x.as_ref()));''', '''                Some(Conf::Group) => {
                    if !is_offer && lone_removal(r, p, law, spec, cache) {
                        return true; // CC 4.5.13: a moderator, an agent's key
                    }
                    let pol = law.policy_of(r.policy().map(|x| x.as_ref()));
                    if pol == Some(Policy::Lift) {
                        // the overturn's count over the objections the row names, at the head the removal names
                        let Some(v) = lift_voices_with(p, law, spec, cache) else { return false };
                        let mem = members_at_with(p, law, spec, &obj, r.head(), "member", cache);
                        // a lift restores and does not admit: the key was on the roster at that head
                        return r.to().iter().all(|k| mem.contains(k))
                            && count_of(pol, is_offer, r.to(), &mem, &v, None, |_| 0);
                    }
                    let mem = count_members_with(p, law, spec, cache);'''),
('''    if matches!(pol, Some(Policy::DutyConfer) | Some(Policy::DutyWithdraw)) {
        let yes: BTreeSet<&K> = v.iter().filter(|k| mem.contains(*k)).collect();
        return duty_count_keys(pol == Some(Policy::DutyWithdraw), to, &yes, mem);
    }''', '''    if matches!(pol, Some(Policy::DutyConfer) | Some(Policy::DutyWithdraw)) {
        let yes: BTreeSet<&K> = v.iter().filter(|k| mem.contains(*k)).collect();
        return duty_count_keys(pol == Some(Policy::DutyWithdraw), to, &yes, mem);
    }
    if pol == Some(Policy::Lift) {
        // the members' check: more than half of the members, never fewer than two, the key seated no voice
        let yes = v.iter().filter(|k| mem.contains(*k) && !to.contains(k)).count();
        return is_offer && 2 * yes > mem.len() && yes >= 2;
    }'''),
('''/// - `voices` is [`voices`]: the row's signer, its cosigners, and the signers of the cosignatures it names
///   that name every head it is counted over.''', '''/// - `voices` is [`voices`]: the row's signer, its cosigners, and the signers of the cosignatures it names
///   that name every head it is counted over.
/// - Under [`Policy::Lift`] the two are read otherwise: `voices` is [`lift_voices`] (the objections the row
///   names, the removal's author left out) and `members` is [`members_at`] at the head, with no leaving
///   subtracted. The seat rule asks besides that the key seated is among those members.'''),
])
edit(R + "tests/common/mod.rs", [
('''            "ack" => SeatKind::Ack,
            _ => SeatKind::Other,''', '''            "ack" => SeatKind::Ack,
            // an objection in a window is presented as a voice for the row it answers (seat::lift_voices)
            "answer" if self.says.as_deref() == Some("object") => SeatKind::Cosign,
            _ => SeatKind::Other,'''),
('''    fn head(&self) -> &[String] {
        &self.head
    }
    fn policy''', '''    fn head(&self) -> &[String] {
        &self.head
    }
    fn removes_agent(&self) -> bool {
        self.f("agent").is_some_and(|x| x.b())
    }
    fn policy'''),
('''            "open" => Some(WinKind::Open),''', '''            "open" => Some(WinKind::Open),
            // an act that names a window opens it (a moderator's lone removal of an agent's key)
            "unseat" if self.window.is_some() => Some(WinKind::Open),'''),
('''            "duty" if k == "duty_withdraw" => Policy::DutyWithdraw,''', '''            "duty" if k == "duty_withdraw" => Policy::DutyWithdraw,
            "lift" => Policy::Lift,'''),
('''                        J::Arr(t) if t[0].s() == "atleast" => {
                            How::AtLeast(t[1].i() as u64, t[2].i() as u64, t[3].i() as u64)
                        }''', '''                        J::Arr(t) if t[0].s() == "atleast" => {
                            How::AtLeast(t[1].i() as u64, t[2].i() as u64, t[3].i() as u64)
                        }
                        J::Arr(t) if t[0].s() == "voted" => {
                            How::MoreOfVoted(t[1].i() as u64, t[2].i() as u64, t[3].i() as u64, t[4].s().into())
                        }'''),
('''                        "others" => Base::Others,''', '''                        "others" => Base::Others,
                        "all_opener_mute" => Base::AllOpenerMute,'''),
])
