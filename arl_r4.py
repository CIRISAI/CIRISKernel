p = "/home/emoore/CIRISKernel/.claude/worktrees/agent-ad781c03a48920203/crates/ciris-kernel/src/window.rs"
s = open(p).read()
for a, b in [
('''    let by =
        ops::group_by(answers.iter().copied().filter(|a| voters.contains(a.signer()) && !is_wd(a) && !moot(a)), |a| {
            a.signer().clone()
        });
''', '''    let by = ops::group_by(answers.iter().copied().filter(|a| voters.contains(a.signer()) && !is_wd(a)), |a| {
        a.signer().clone()
    });
'''),
('''        if let Some(v) = ops::one(rs.iter().filter_map(|a| a.says().map(|w| String::from(w.as_ref())))) {''',
 '''        let heard = rs.iter().filter(|a| !moot(a));
        if let Some(v) = ops::one(heard.filter_map(|a| a.says().map(|w| String::from(w.as_ref())))) {'''),
]:
    assert s.count(a) == 1, a
    s = s.replace(a, b)
open(p, "w").write(s)
