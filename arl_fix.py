R = "/home/emoore/CIRISKernel/.claude/worktrees/agent-ad781c03a48920203/"
def edit(p, reps):
    s = open(R + p).read()
    for a, b in reps:
        assert s.count(a) == 1, (p, s.count(a), a)
        s = s.replace(a, b)
    open(R + p, "w").write(s)
edit("tools/kernel_crate_plants.sh", [
('''plant "the author's voice counts in the re-seating"     src/seat.rs 'v.remove(rem.signer());' ''
plant "the re-seating counts the author over"           src/seat.rs''', '''plant "the re-seating counts the author over"           src/seat.rs'''),
])
edit("crates/ciris-kernel/CHANGELOG.md", [
("contesting rule two); ten planted breaks in the crate.", "contesting rule two); nine planted breaks in the crate, each confirmed by hand."),
])
edit("crates/ciris-kernel/src/seat.rs", [
('''    v.remove(rem.signer());
    Some((rem.signer().clone(), v))''', '''    // the seat rule also takes the author out of the members counted over, which alone would leave it no
    // voice there; it is taken out here too for a caller that counts these voices over members of its own
    v.remove(rem.signer());
    Some((rem.signer().clone(), v))'''),
])
