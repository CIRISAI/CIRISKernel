R = "/home/emoore/CIRISKernel/.claude/worktrees/agent-ad781c03a48920203/"
def edit(p, reps):
    s = open(R + p).read()
    for a, b in reps:
        assert s.count(a) == 1, (p, s.count(a), a)
        s = s.replace(a, b)
    open(R + p, "w").write(s)

C = "crates/ciris-kernel/"
edit(C + "src/window.rs", [
('''    opener_signer: R::Key,
    w: &'x WindowSpec<R::T>,
    cache: core::cell::RefCell<BTreeMap<String, BTreeSet<R::Key>>>,
}
''', '''    opener_signer: R::Key,
    /// The key the opener removes, where the opener is a removal of an AI agent's key: apart from
    /// [`Base::Others`] with the opener's signer.
    removed: &'x [R::Key],
    w: &'x WindowSpec<R::T>,
    cache: core::cell::RefCell<BTreeMap<String, BTreeSet<R::Key>>>,
}

/// The key an opener removes, where the opener is a removal of an AI agent's key
/// ([`SeatRow::removes_agent`]). An agent "acts under its own key and has no vote" (CC 4.5.13): in the lift of
/// its own removal it is no voice and is not counted over.
fn removed_agent<R: WindowRow>(o: &R) -> &[R::Key] {
    if o.seat_kind() == SeatKind::Unseat && o.removes_agent() {
        o.to()
    } else {
        &[]
    }
}
'''),
('''        if matches!(b, Base::Others) {
            m.remove(&self.opener_signer);
        }''', '''        if matches!(b, Base::Others) {
            m.remove(&self.opener_signer);
            m.retain(|k| !self.removed.contains(k));
        }'''),
('''        others.remove(&self.opener_signer);
''', '''        others.remove(&self.opener_signer);
        others.retain(|k| !self.removed.contains(k));
'''),
('''        head: o.head(),
        opener_signer: o.signer().clone(),
''', '''        head: o.head(),
        opener_signer: o.signer().clone(),
        removed: removed_agent(o),
'''),
('''        head: p.head(),
        opener_signer: p.signer().clone(),
''', '''        head: p.head(),
        opener_signer: p.signer().clone(),
        removed: removed_agent(p),
'''),
('''    /// The same, less the opener's signer: out of the voices and out of the size counted over (the members'
    /// check: a strict majority of the members seated at the head the act names, the act's author apart).
    Others,''', '''    /// The same, less the opener's signer: out of the voices and out of the size counted over (the members'
    /// check: a strict majority of the members seated at the head the act names, the act's author apart).
    /// Where the opener is a removal of an AI agent's key ([`SeatRow::removes_agent`]), the key it removes is
    /// apart too, on every path: the count with no landing, a landing's, and the recount.
    Others,'''),
])
edit(C + "src/seat.rs", [
('''                    mem.remove(&author); // the removal's author apart
''', '''                    mem.remove(&author); // the removal's author apart
                    mem.retain(|k| !r.to().contains(k)); // and the key removed
'''),
('''                        mem.remove(&author); // the author is not among the members the majority is taken of
''', '''                        mem.remove(&author); // the author is not among the members the majority is taken of
                        mem.retain(|k| !r.to().contains(k)); // nor is the key removed: an agent has no vote
'''),
('''    /// author and the key it seats no voice; it is met by more than half of the members at the head the
    /// removal names, the removal's author apart, never fewer than two voices.''', '''    /// author and the key it seats no voice; it is met by more than half of the members at the head the
    /// removal names, the removal's author and the key removed apart, never fewer than two voices.'''),
('''///   names, the removal's author left out) and `members` is [`members_at`] at the head less that author,
///   with no leaving subtracted. The seat rule asks besides that the key seated is among those members.''',
 '''///   names, the removal's author left out) and `members` is [`members_at`] at the head less that author and
///   less the key removed, with no leaving subtracted. The seat rule asks besides that the key seated was
///   among the members at that head.'''),
('''/// Returns the removal's author and the voices. The count ([`Policy::Lift`]) is taken of the members at the
/// head less that author.''', '''/// Returns the removal's author and the voices. The count ([`Policy::Lift`]) is taken of the members at the
/// head less that author and less the key removed (an agent "acts under its own key and has no vote").'''),
('''        // the members' check: more than half of the members (the caller has taken the act's author out of
        // them and out of the voices), never fewer than two; the key seated is counted over and is no voice''',
 '''        // the members' check: more than half of the members (the caller has taken the act's author and the
        // key removed out of them, and the author out of the voices), never fewer than two; the key seated
        // is no voice'''),
])
edit("tools/kernel_crate_plants.sh", [
('''plant "the key seated is a voice of its re-seating"     src/seat.rs 'let yes = v.iter().filter(|k| mem.contains(*k) && !to.contains(k)).count();' 'let yes = v.iter().filter(|k| mem.contains(*k)).count();'
''', '''plant "the removed key is counted over in its re-seating" src/seat.rs 'mem.retain(|k| !r.to().contains(k)); // nor is the key removed: an agent has no vote' ''
plant "the removed key is counted over in the lift"     src/window.rs 'others.retain(|k| !self.removed.contains(k));' ''
'''),
])
