p = "/home/emoore/CIRISKernel/.claude/worktrees/agent-ad781c03a48920203/tools/kernel_crate_plants.sh"
s = open(p).read()
old = '''plant "a floored majority read without its floor"       src/window.rs 'How::MoreAtLeast(num, den, least) => yes * den > num * n && yes >= least,' 'How::MoreAtLeast(num, den, _) => yes * den > num * n,'
'''
assert s.count(old) == 1
new = '''plant "a floored majority read without its floor"       src/window.rs '&How::MoreAtLeast(num, den, least) => yes * den > num * n && yes >= least,' '&How::MoreAtLeast(num, den, _) => yes * den > num * n,'
plant "the fallback counted over silent members"        src/window.rs 'yes * den > num * (yes + no) && yes >= *least' 'yes * den > num * n && yes >= *least'
plant "the fallback read without its floor"             src/window.rs 'yes * den > num * (yes + no) && yes >= *least' 'yes * den > num * (yes + no)'
plant "a vote beside a moderator's answer unsays it"    src/window.rs 'let moot = |a: &R| acted.contains(a.signer()) && duty_word(a).is_none();' 'let moot = |_a: &R| false;'
plant "an act that opens its own window skips the seat" src/window.rs 'if matches!(r.seat_kind(), SeatKind::Offer | SeatKind::Unseat) && !seat_rule(p, law, spec, &|_| true) {' 'if false {'
plant "a moderator removes any key alone"               src/seat.rs '|| r.conf() != Some(Conf::Group) || !r.removes_agent() || r.to().len() != 1 {' '|| r.conf() != Some(Conf::Group) || r.to().len() != 1 {'
plant "any key removes an agent's key alone"            src/seat.rs '        && members_at_with(p, law, spec, &obj, r.head(), "moderate", cache).contains(r.signer())' ''
plant "the author's voice counts in the re-seating"     src/seat.rs 'v.remove(rem.signer());' ''
plant "the re-seating counts the author over"           src/seat.rs 'mem.remove(&author); // the author is not among the members the majority is taken of' ''
plant "the key seated is a voice of its re-seating"     src/seat.rs 'let yes = v.iter().filter(|k| mem.contains(*k) && !to.contains(k)).count();' 'let yes = v.iter().filter(|k| mem.contains(*k)).count();'
plant "a re-seating admits a key never seated"          src/seat.rs 'if !r.to().iter().all(|k| mem.contains(k)) {' 'if false {'
'''
s = s.replace(old, new)
open(p, "w").write(s)
