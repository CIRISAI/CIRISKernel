#!/usr/bin/env bash
# Plant one break at a time in a copy of crates/ciris-kernel (never in the working tree) and check that the
# differential tests catch each. Exits 1 if a plant is not caught or the unbroken copy fails.
#
# PLANTS_SHARD=k/n runs only the plants whose place in the list below is k modulo n (k from 1 to n), so that n
# runs with k = 1..n between them run every plant once. CI runs the shards as separate jobs (crate.yml): each
# plant is a release rebuild and the whole test suite, about 41 s on a runner, and 54 of them one after another
# took the check job past its time limit. Without PLANTS_SHARD every plant runs, as ./check.sh does locally.
set -u
root="$(cd "$(dirname "$0")/.." && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
cp -a "$root/crates/ciris-kernel" "$work/ciris-kernel"
export CARGO_TARGET_DIR="$work/target"
caught=0; total=0; seen=0
shard="${PLANTS_SHARD:-1/1}"
k="${shard%/*}"; n="${shard#*/}"
case "$k$n" in *[!0-9]*|"") echo "PLANTS_SHARD=$shard: want k/n"; exit 1 ;; esac
[ "$n" -ge 1 ] && [ "$k" -ge 1 ] && [ "$k" -le "$n" ] || { echo "PLANTS_SHARD=$shard: want 1 <= k <= n"; exit 1; }
mine() {  # true when the next plant in the list belongs to this shard
  seen=$((seen + 1))
  [ $(( (seen - 1) % n )) -eq $((k - 1)) ]
}
plant() {  # plant <name> <file> <old> <new>
  mine || return 0
  local name="$1" f="$work/ciris-kernel/$2"
  cp "$f" "$f.orig"
  python3 -I -c 'import sys; p,a,b=sys.argv[1:4]; s=open(p).read(); assert a in s, a; open(p,"w").write(s.replace(a,b,1))' "$f" "$3" "$4" || { echo "plant $name: text not found"; exit 1; }
  total=$((total + 1))
  if (cd "$work/ciris-kernel" && cargo test --offline --release -q > "$work/log" 2>&1); then
    echo "NOT CAUGHT  $name"
  else
    caught=$((caught + 1)); echo "caught      $name"
  fi
  mv "$f.orig" "$f"
}
plant_run() {  # plant_run <name> <file> <old> <new>: the conformance step must fail on the copy
  mine || return 0
  local name="$1" f="$work/ciris-kernel/$2"
  cp "$f" "$f.orig"
  python3 -I -c 'import sys; p,a,b=sys.argv[1:4]; s=open(p).read(); assert a in s, a; open(p,"w").write(s.replace(a,b,1))' "$f" "$3" "$4" || { echo "plant $name: text not found"; exit 1; }
  total=$((total + 1))
  if KERNEL_CRATE_DIR="$work/ciris-kernel" bash "$root/tools/kernel_conformance.sh" > "$work/log" 2>&1; then
    echo "NOT CAUGHT  $name"
  else
    caught=$((caught + 1)); echo "caught      $name"
  fi
  mv "$f.orig" "$f"
}
(cd "$work/ciris-kernel" && cargo test --offline --release -q > "$work/log" 2>&1) || { echo "the unbroken copy fails"; exit 1; }
plant "a removal voids rows in its own past"          src/derived.rs '|| c.g.in_past(i, x))' ')'
plant "two cuts saying the same thing contest"         src/cut.rs 'if as_cut && self.spec.says(xr) == self.spec.says(rr) {' 'if false {'
plant "a counted offer's proposer ends it alone"      src/seat.rs '&& o.conf() != Some(Conf::Group) && !eq(o)' '&& !eq(o)'
plant "acts: an affiliation's stated path unread" src/seat.rs '    if !matches!(word, Some("affiliation_member_action" | "cosigned_act")) {' '    if true {'
plant "acts: a purge read as a standing act" src/seat.rs 'CommunityKind::Accord if sc == Some("selection") =>' 'CommunityKind::Accord if false =>'
plant "acts: a voice's room keys no act" src/seat.rs '        CommunityKind::SelfRoster | CommunityKind::Voice => {' '        CommunityKind::SelfRoster => {'
plant "acts: a confirmation by one voice" src/seat.rs '    2 * v > holders.len()' '    v > 0'
plant "acts: a confirmation naming no halt" src/seat.rs '    cited(r, get, &|q: &R| q.seat_kind() == SeatKind::Halt).filter(|h| h.obj().is_some() && h.obj() == r.obj())' '    cited(r, get, &|_: &R| true)'
plant "one say switched off"                           src/head.rs '.filter(|k| !(self.say && rcpts' '.filter(|k| !(false && rcpts'
plant "a cut at an older head is not read"              src/head.rs 'self.counts_own(a) && !self.cuts(a).iter().any(|c| self.voids_from(c, a))' 'self.counts_own(a)'
plant "one say unread on a cut at an older head"       src/head.rs 'let rc = if self.say { self.say_receipts(a) } else { BTreeMap::new() };' 'let rc: BTreeMap<K, Vec<I>> = BTreeMap::new();'
plant "a cut at a concurrent head reaches the act"     src/head.rs 'if !self.later(&act.head, &c.head) || !self.conc(&c.id, a) {' 'if c.head == act.head || !self.conc(&c.id, a) {'
plant "a key's end read inclusively"                   src/lib.rs 'until.is_none_or(|u| *t < u)' 'until.is_none_or(|u| *t <= u)'
plant "a record whose end is its own instant is kept"    src/key_end.rs 'x.from >= u || u - x.from > ceil' 'x.from > u || u - x.from > ceil'
plant "the reader's line ignored"                      src/line.rs '(built_ok && !mine.iter().any(|&m| behind(r, m)))' 'built_ok'
plant "a count read at its named heads whatever is in its past (H1)" src/seat.rs 'if newer_head_in_past_v(p, law, &obj, r.head(), &signers(r), &cache.current_void()) {' 'if false {'
plant "an election's seating names no head (H4)" src/seat.rs 'if newer_head_in_past_v(p, law, &obj, r.head(), &signers(r), &cache.current_void()) {' 'if !is_election(law, r) && newer_head_in_past_v(p, law, &obj, r.head(), &signers(r), &cache.current_void()) {'
plant "named heads that are no antichain: the older dropped, not refused (H1)" src/seat.rs '    if heads.iter().any(|a| heads.iter().any(|b| a != b && p.past(a, b))) {
        return true;
    }
    let heads: Vec<&R::Id> = heads.iter().filter(|h| !void.contains(*h)).collect();' '    let heads: Vec<&R::Id> = heads.iter().filter(|&a| !heads.iter().any(|b| a != b && p.past(a, b))).filter(|h| !void.contains(*h)).collect();'
plant "a lone holder's own conferral reads no standing offer" src/seat.rs '    held.len() == 1 && held.contains(r.signer()) && !lone_offer_stands(law, p, r, &held)' '    held.len() == 1 && held.contains(r.signer())'
plant "a window opened at an old head (H1)" src/window.rs '            && seat::newer_head_in_past(p, law, &obj, r.head(), &seat::signers(r))' '            && false'
plant "the line not sibling-safe (H5)" src/line.rs 'm != r && beside && !never_behind(r) && older(c, heads(r), heads(m))' 'm != r && beside && !never_behind(r) && older(c, heads(r), core::slice::from_ref(c.g.row(m).id()))'
plant "versions behind not sibling-safe (H5)" src/line.rs 'bi.iter().all(|e| bj.iter().any(|&h| past(h).contains(e)))' 'bi.iter().all(|e| past(j).contains(e))'
plant "no change self-forked (S'')" src/seat.rs '    let out: BTreeSet<usize> = acts.iter().copied().filter(|&q| forked(q)).collect();' '    let out: BTreeSet<usize> = acts.iter().copied().filter(|&q| false && forked(q)).collect();'
plant "a self-forked change void, T unread (S'')" src/seat.rs '    let tv: BTreeSet<usize> = out.iter().copied().filter(|&q| t_void(q)).collect();' '    let tv: BTreeSet<usize> = out.clone();'
plant "the fork decided by depth (S' form)" src/seat.rs '    let tv: BTreeSet<usize> = out.iter().copied().filter(|&q| t_void(q)).collect();' '    let tv: BTreeSet<usize> = out.iter().copied().filter(|&q| !acts.iter().any(|&c| behind(q, c) && out.contains(&c))).collect();'
plant "a beneficiary counted for its side (T)" src/seat.rs '                ks.retain(|k| !r.to().contains(k)); // the beneficiary is no evidence for its side' ''
plant "T counts posts and acknowledgements" src/seat.rs '        let pool: &[usize] = &acts;' '        let pool: &[usize] = anc;'
plant "T counts a seat from the forked side" src/seat.rs '            ks.into_iter().filter(|k| mem.contains(k) && standing(k, a)).collect()' '            ks.into_iter().filter(|k| mem.contains(k) && (standing(k, a) || mem.contains(k))).collect()'
plant "T reads only seats held at the fork point" src/seat.rs '                    && (o != q && !g.in_past(q, o) && !out.contains(&o) && g.in_past(o, a))' '                    && false'
plant "the tips intersected, not folded" src/seat.rs 'hs.iter().any(|&hi| q == hi || g.ancestors(hi).has(q))' 'hs.iter().all(|&hi| q == hi || g.ancestors(hi).has(q))'
plant "a record-change tip read in its past (regime)" src/seat.rs '                if is_amendment(g.row(t), o) {' '                if false {'
plant "no reader exclusion" src/seat.rs '    *cache.rvoid.borrow_mut() = rv.clone();' ''
plant "acknowledging un-voids (the line not monotone)" src/line.rs '            .filter(|&r| r == *a || (!ex.contains(&r) && !held.contains(&r)))' '            .filter(|&r| r == *a || !ex.contains(&r))'
plant "a void change cuts in the roster" src/seat.rs '            behind.extend(roster_void(c, law, spec, reader));' ''
plant "only the protocol splits regimes" src/seat.rs '                let own = founders(t).then_some(t);' '                let own: Option<usize> = None;'
plant "a lone holder's standing duty offer unread" src/seat.rs '    if pol == Some(Policy::DutyConfer) && mem.len() < 2 && lone_offer_stands(law, p, r, &mem) {' '    if false {'
plant "a lone holder's standing duty offer read for its own scope only" src/seat.rs '            && o.scope().is_some_and(|s| law.is_duty(s.as_ref(), &declared))' '            && o.scope() == r.scope()'
plant "a duty holder's own conferral is no counted change" src/seat.rs '    room.is_some_and(|declared| own_conferral(law, q, obj, declared))' '    room.is_some_and(|declared| false && own_conferral(law, q, obj, declared))'
plant "the fold at tips reads no later acceptance" src/seat.rs '        ids.extend(completing(&rows, self.law, &by, o, &at, &in_past).iter().filter_map(|q| g.idx(q.id())));' ''
plant "a count read at every head it names, not the newest (H1)" src/seat.rs '    if !heads.iter().any(behind_another) {' '    if true {'
plant "a named head may be any row (H1, H3, H8)" src/seat.rs '            && !p.get(h).is_some_and(|q| change(law, q, obj, room.as_deref()) || landed_change(p, q, obj))' '            && false'
plant "a counted change of any object moves the head (H1)" src/seat.rs '    if LineSpec::<R>::counted_act(&SeatLine, q).is_some_and(|(o, _)| o == *obj) {' '    if LineSpec::<R>::counted_act(&SeatLine, q).is_some() {'
plant "a counted change behind a named head moves it (H1)" src/seat.rs '&& !heads.iter().any(|&h| h == q.id() || p.past(q.id(), h))' '&& !heads.iter().any(|&h| h == q.id())'
# retired with the open:self_admit cut (Eric, for 1.0; the sheet at a304b485): "a self-admission is a counted change (H3)" (the code it broke is gone)
plant "a count over another room concludes (H2)"       src/seat.rs '                    if r.over().is_some_and(|o| o != obj) {
                        return false;
                    }' ''
plant "a lone removal read before the newest-heads rule (H4)" src/seat.rs 'if newer_head_in_past_v(p, law, &obj, r.head(), &signers(r), &cache.current_void()) {' 'if !(!is_offer && lone_removal(r, p, law, spec, Some(cache))) && newer_head_in_past_v(p, law, &obj, r.head(), &signers(r), &cache.current_void()) {'
plant "the withdrawals of a row's past not read with its heads (H4)" src/seat.rs 'at(q) || g.row(q).seat_kind() == SeatKind::Withdraw || acc.contains(g.row(q).id());' 'at(q) || acc.contains(g.row(q).id());'
plant "a holder's own acceptance in a row's past not read (acceptances, (a))" src/seat.rs 'at(q) || g.row(q).seat_kind() == SeatKind::Withdraw || acc.contains(g.row(q).id());' 'at(q) || g.row(q).seat_kind() == SeatKind::Withdraw;'
plant "an ended offer completed by an acceptance (acceptances, bound 2)" src/seat.rs '        if !ended {
            out.push(a);' '        if true {
            out.push(a);'
plant "a remover's re-acceptance of its standing unread" src/seat.rs '&& !again(*e, sc)' ''
plant "a resignation that names no newest change (H4)" src/seat.rs '                !newer_head_in_past_v(
                    p,
                    law,
                    &room,
                    &named,' '                true || !newer_head_in_past_v(
                    p,
                    law,
                    &room,
                    &named,'
plant "the reader's line voids only concurrent acts (H5)" src/line.rs '        let beside = !c.g.in_past(r, m);' '        let beside = c.g.concurrent(r, m);'
plant "a roster version behind the line only where concurrent (H5)" src/line.rs 'let beside = i != j && !past(j).contains(&i);' 'let beside = i != j && !past(j).contains(&i) && !past(i).contains(&j);'
plant "the acts behind the line not listed as void (H5)" src/seat.rs 'stale.extend(behind.iter().copied());' ''
plant "the line's first pass reads the cut (H5)"       src/seat.rs 'line::void_except(c, &SeatLine, own, |_| true, |_| false, &except)' '{ let c0 = Cut::new(c, spec); line::void_except(c, &SeatLine, own, |i| c0.counts(i), |_| false, &except) }'
plant "a reader's line read from explicit acks only (H6)" src/line.rs '        if !named.is_empty() || spec.acknowledges(r, own, &get).is_some_and(|o| o == *obj) {' '        if !named.is_empty() {'
plant "the cut read before the reader's line"          src/seat.rs 'let cut = Cut::new_without(c, spec, &behind);' 'let cut = Cut::new(c, spec);'
plant "a met count is read only by a landing" src/window.rs 'return if got == "open" { Outcome::Open } else { Outcome::Landed(got) };' 'return Outcome::Open;'
plant "a withdrawal takes back the proposer's approval" src/window.rs 'let by = ops::group_by(answers.iter().copied().filter(|a| person(a).is_some() && !is_wd(a)), |a| {' 'let by = ops::group_by(answers.iter().copied().filter(|a| person(a).is_some()), |a| {'
plant "an approval that names the withdrawal still approves" src/window.rs 'answers.iter().copied().filter(|a| !(says(a, "approve") && wd.iter().any(|w| past(w, a.id())))).collect()' 'answers.iter().copied().collect()'
plant "concurrent answers not recounted"               src/window.rs 'answers.extend(ans);' ''
plant "policy row: a policy cell read unstated is no refusal" src/window.rs 'if cell.value == "unstated" {' 'if false {'
plant "policy row: a window_secs its class does not give" src/window.rs 'Some(&s) if s != row.window_secs => no(' 'Some(&s) if false && s != row.window_secs => no('
plant "policy row: a row of no window gives one" src/window.rs 'if row.window_secs == 0 {' 'if false {'
plant "policy row: a prose fraction unread against its rule" src/window.rs 'Stated::Fraction(n, d) => rule.kind == "fraction" && rule.num == Some(*n) && rule.den == Some(*d),' 'Stated::Fraction(..) => true,'
plant "policy row: the standing set's exclusion unread" src/window.rs 'if less == excl.is_empty() {' 'if false {'
plant "policy row: a local concluder unrefused" src/window.rs '    if row.concluder == "local" {
' '    if false {
'
plant "policy row: the default leaf unread against the outcome words" src/window.rs 'if !has(&default) {' 'if false {'
plant "policy row: the seat unread" src/window.rs 'let scope = String::from(seat.filter(|s| incl.contains(s)).unwrap_or(incl[0]));' 'let scope = String::from(incl[0]);'
plant "policy row: the opener cell unread" src/window.rs 'let opener = if named(&row.opener) { None } else { Some(row.opener.clone()) };' 'let opener: Option<String> = None;'
plant "policy row: a key voice off a self corridor" src/window.rs '"key" if row.corridor != "self" => no(' '"key" if false => no('
plant "policy row: the answer words unread" src/window.rs '"objection" if !aw.is_empty() && all_in(&["assent", "raised"]) => ("assent", "raised"),' '"objection" => ("approve", "object"),'
plant "policy row: opener_says unread" src/window.rs '"approve" => Some(String::from(yes_w)),' '"approve" => None,'
plant "policy row: the census figure unread" src/window.rs '(None, "active", Some(Active::Census(n))) => Base::Stated(n),' '(None, "active", Some(Active::Census(_))) => Base::All,'
plant "policy row: the proposer apart unread" src/window.rs '        over = Base::Others;
' '
'
plant "policy row: min_count unread by corridor" src/window.rs '        mc_.unwrap_or(0)
' '        mc_.unwrap_or(0).max(2)
'
plant "policy row: the comparison read as at least" src/window.rs '_ => How::AtLeast(n, d, least),' '_ => How::MoreAtLeast(n, d, least),'
plant "policy row: a strict half read with a floor" src/window.rs '"more_than" if (n, d) == (1, 2) && least <= 1 => How::Strict,' '"more_than" if false => How::Strict,'
plant "policy row: the self corridor's withdrawal and at-once cancel unread" src/window.rs 'let lone = row.corridor == "self";' 'let lone = false;'
plant "policy row: irreversible unread" src/window.rs 'if !row.irreversible {' 'if true {'
plant "policy row: the others' cancel over the whole base" src/window.rs 'Some(clause(no_w, How::Strict, Base::Others, leaf("refused")))' 'Some(clause(no_w, How::Strict, Base::All, leaf("refused")))'
plant "policy row: reverse_path unread" src/window.rs '        if row.reverse_path {
' '        if true {
'
plant "policy row: a one_of_n floor unread" src/window.rs '"one_of_n" => Some(clause(yes_w, How::One, over.clone(), leaf("landed"))),' '"one_of_n" => None,'
plant "policy row: a floor that gives the default kept" src/window.rs 'if let (Some(f), false) = (floor, default == "landed") {' 'if let (Some(f), _) = (floor, default == "landed") {'
plant "policy row: a mirror's floor voices unread" src/window.rs 'How::MoreAtLeast(1, 2, k) } else { How::AtLeast(1, 2, k) };' 'How::MoreAtLeast(1, 2, 0) } else { How::AtLeast(1, 2, 0) };'
plant "policy row: changes_set unread for a silent target" src/window.rs 'if c.changes_set.value != "removes" {' 'if false {'
plant "policy row: target_silent unread" src/window.rs 'silent = Some(leaf("refused"));' 'silent = None;'
plant "policy row: target_voice unread" src/window.rs 'let tv = c.target_voice.value == "yes";' 'let tv = false;'
plant "policy row: window_secs not the length" src/window.rs 'let secs = T::try_from(row.window_secs).ok();' 'let secs = T::try_from(row.window_secs / 2).ok();'
plant "window binding: the binding unread: the opener's name names its table" src/window.rs 'f(bound_family(law, get, o)?, &obj, founding.and_then(|g| g.scope()).map(|w| w.as_ref()))' 'o.window().and_then(windows)'
plant "window: a local concluder lands" src/window.rs '    if w.concluder == "local" {' '    if false {'
plant "window: two holders' disagreeing acts resolve" src/window.rs '        if !(one_over(cl) && disagree(cl)) {' '        if true {'
plant "policy row: a role holder's ballot unread" src/window.rs '([role], Some(1), "ballot") => {' '([role], Some(9), "ballot") => {'
plant "window binding: a fixed row's other stated policy unread" src/window.rs 'Choice::Fixed if pols.len() == 1 && stated.is_none_or(|s| s == pols[0]) => pols[0].as_str(),' 'Choice::Fixed if pols.len() == 1 => pols[0].as_str(),'
plant "window binding: a row row's stated policy unread" src/window.rs 'Choice::Row => pols.iter().map(|p| p.as_str()).find(|p| Some(*p) == stated)?,' 'Choice::Row => pols[0].as_str(),'
plant "window binding: two counts at once bound as a window" src/window.rs '(!name.contains('\''&'\'')).then_some(name)' 'Some(name)'
plant "seat law tables: a fraction of 1/2 read as at least half" src/tables.rs '("fraction", Some(1), Some(2)) => Policy::Strict(1, 2),' '("fraction", Some(1), Some(2)) => Policy::AtLeast(1, 2),'
plant "seat law tables: a fraction read as strictly more" src/tables.rs '("fraction", Some(n), Some(d)) => Policy::AtLeast(n, d),' '("fraction", Some(n), Some(d)) => Policy::Strict(n, d),'
plant "seat law tables: one_of_n unread" src/tables.rs '("one_of_n", ..) => Policy::One,' '("one_of_n", ..) => Policy::NotACount,'
plant "seat law tables: the duty counts read off the enact cell" src/tables.rs '"duty_confer" => Some(Policy::DutyConfer),' '"duty_confer" => None,'
plant "seat law tables: the recall's floor unread" src/tables.rs '("fraction", Some(n), Some(d), "voices", Some(c)) => Policy::Recall(n, d, c),' '("fraction", Some(n), Some(d), "voices", Some(_)) => Policy::Recall(n, d, 2),'
plant "seat law tables: a protocol's rule unread" src/tables.rs '"all" => Some(Policy::Unanimous),' '"all" => Some(Policy::Strict(1, 2)),'
plant "seat law tables: an unknown acts word dropped silently" src/tables.rs 'no("acts", &key, cell, LawWhy::Unknown);' '{}'
plant "seat law tables: a duplicate acts row unrefused" src/tables.rs 'if seen.contains(&k) {' 'if false {'
plant "seat law tables: an acts policy with no row unrefused" src/tables.rs 'if !families.iter().any(|f| f.family == q) {' 'if false {'
plant "seat law tables: the removal floor unread" src/tables.rs 'law.removal_floor = r.count.unwrap_or(0) as usize,' 'law.removal_floor = 2,'
plant "seat law tables: a held row counted" src/tables.rs '        let p = if shut.contains(&f.family) {' '        let p = if false {'
plant "seat law tables: the halt counted by its enact" src/tables.rs '            Policy::Strict(1, 2)
        } else if f.family == "moderator_recall" {' '            Policy::One
        } else if f.family == "moderator_recall" {'
plant "a receipt with the target's row in its past is still a receipt" src/window.rs 'return Some(Ok(!rows.iter().any(|q| q.signer() == t && q.id() != o.id() && !p.past(q.id(), o.id()))));' 'return Some(Ok(true));'
plant "a window's opener held to the counted scope"     src/window.rs 'let scope = w.opener.as_ref().unwrap_or(&w.counted);' 'let scope = &w.counted;'
plant "a floored majority read without its floor"       src/window.rs '&How::MoreAtLeast(num, den, least) => more(num, den, n) && y >= least as u128,' '&How::MoreAtLeast(num, den, _) => more(num, den, n),'
plant "the fallback counted over silent members"        src/window.rs 'more(*num, *den, y + no as u128) && y >= *least as u128' 'more(*num, *den, n) && y >= *least as u128'
plant "the fallback read without its floor"             src/window.rs 'more(*num, *den, y + no as u128) && y >= *least as u128' 'more(*num, *den, y + no as u128)'
plant "a vote beside a moderator's answer unsays it"    src/window.rs 'let moot = |a: &R| person(a).is_some_and(|p| acted.contains(&p)) && duty_word(a).is_none();' 'let moot = |_a: &R| false;'
plant "an act that opens its own window skips the seat" src/window.rs '        if matches!(r.seat_kind(), SeatKind::Offer | SeatKind::Unseat) {
            match seat::seat_rule_why(' '        if false {
            match seat::seat_rule_why('
plant "a withdrawn ballot is still a ballot"           src/window.rs '.filter(|a| !says(*a).is_some_and(|v| words.contains(v)) || !wd.contains(&(a.id(), a.signer())))' '.filter(|_| true)'
plant "a ballot's withdrawal concurrent with a landing not recounted" src/window.rs 'let wrows: Vec<&R> = mine.iter().chain(&conc).map(|&q| g.row(q)).collect();' 'let wrows: Vec<&R> = mine.iter().map(|&q| g.row(q)).collect();'
plant "a vote against is no ballot to withdraw"         src/window.rs 'out.insert(against.as_str());' ''
plant "the overturn's author concludes its landing"   src/window.rs 'if r.signer() == o.signer() && author_apart(&w) {' 'if false {'
plant "a stated base shrinks below the members seated" src/window.rs 'Base::Stated(s) => m.max(*s as u128),' 'Base::Stated(s) => *s as u128,'
plant "a stated base read through a 32-bit cast"       src/window.rs 'Base::Stated(s) => m.max(*s as u128),' 'Base::Stated(s) => m.max(*s as u32 as u128),'
plant "a withdrawal matched to a ballot by its id alone" src/window.rs '!wd.contains(&(a.id(), a.signer()))' '!wd.iter().any(|(t, _)| *t == a.id())'
plant "every answer read as withdrawn, not only a ballot" src/window.rs '!says(*a).is_some_and(|v| words.contains(v)) || ' ''
plant "a ballot's withdrawal not read with no landing" src/window.rs 'let counted: Vec<&R> = c.cs().iter().copied().filter(|&r| !late(r)).map(|r| g.row(r)).collect();' 'let counted: Vec<&R> = Vec::new();'
plant "a stated base's voices read without the opener" src/window.rs 'Base::All | Base::Stated(_) => ("all", self.w.counted.as_str()),' 'Base::All => ("all", self.w.counted.as_str()), Base::Stated(_) => ("others", self.w.counted.as_str()),'
plant "a withdrawal of a withdrawal revives the ballot" src/window.rs 'let wd: BTreeSet<(&R::Id, &R::Key)> = own_withdrawals(rows.iter().copied());' 'let all = own_withdrawals(rows.iter().copied()); let wd: BTreeSet<(&R::Id, &R::Key)> = own_withdrawals(rows.iter().copied().filter(|w| !all.contains(&(w.id(), w.signer()))));'
plant "a moderator's lone removal reaches a person's seat" src/seat.rs 'let agent = scope.as_ref() == AGENT;' 'let agent = law.roster_seats.iter().any(|s| s == scope.as_ref());'
plant "any key removes an agent's key alone"            src/seat.rs '    members_at_with(p, law, spec, &obj, r.head(), "moderate", cache).contains(r.signer())
}' '    true
}'
plant "the re-seating counts the author over"           src/seat.rs '        let (mem, v) = pp.count(&mem, &v, None, &[author]);' '        let (mut mem, v) = pp.count(&mem, &v, None, &[author.clone()]);
        mem.insert(pp.member(&author));'
plant "an agent's key is counted over in a count"     src/seat.rs '    persons(m, &agents_at_with(p, law, spec, obj, heads, cache))' '    let mut m = m;
    m.extend(agents_at_with(p, law, spec, obj, heads, cache));
    m'
plant "an agent's key is counted over in a window"    src/window.rs 'let mut others = persons(sets[0].clone(), &agents);' 'let mut others: BTreeSet<R::Key> = sets[0].union(&agents).cloned().collect();'
plant "an agent holding a duty bars the lone holder" src/seat.rs '    let held = persons(seats.holders("duty", &obj, None), &seats.holders(AGENT, &obj, None));' '    let held = seats.holders("duty", &obj, None);'
plant "the roster leaves out the agents"              src/seat.rs '        m.extend(self.holders(AGENT, o, None));' ''
plant "a lone removal's end unread"                 src/seat.rs 'None => out_of_force(c, law, spec, own, &by, &unseats, cache.unwrap_or(&local)),' 'None => BTreeSet::new(),'
plant "a remover's own receipt keeps its removal"   src/seat.rs '    duty.remove(m);
' ''
plant "a removed key's receipt keeps" src/seat.rs '            (!cut).then_some((q, false))' '            Some((q, false))'
plant "a conferrer's own end lifts nothing" src/seat.rs '                .is_some_and(|t| t.seat_kind() == SeatKind::Offer && !t.to().contains(er.signer())),' '                .is_some_and(|_| false),'
plant "a lone removal out of force still ends a standing (cascade)" src/seat.rs 'let excl: BTreeSet<usize> = out.iter().map(|&j| acts[j]).collect();' 'let excl: BTreeSet<usize> = BTreeSet::new();'
plant "the room's counted receipt unread" src/seat.rs 'return count_receipt(c, q, x, law, spec, cache).then_some((q, true));' 'return None;'
plant "a failed counted receipt read as its signer's" src/seat.rs 'return count_receipt(c, q, x, law, spec, cache).then_some((q, true));' 'if count_receipt(c, q, x, law, spec, cache) {
                    return Some((q, true));
                }'
plant "the count's receipt over any room" src/seat.rs 'if qr.obj().as_ref() != Some(&obj) || qr.over().is_some_and(|o| o != obj) {' 'if false {'
plant "the count's receipt at an older head" src/seat.rs 'if qr.head().is_empty() || !qr.head().iter().all(fresh) {' 'if qr.head().is_empty() {'
plant "a founding duty read as the offer's scope" src/seat.rs '        && (seat_scopes(m, k, signed_by(m, k)).iter().any(|s| s.s() == us.as_ref())' '        && (m.scope() == Some(us)'
plant "an agent's receipt keeps a lone removal" src/seat.rs '    duty.retain(|k| !agents.contains(k));
' ''
plant "a receipt after the unseat keeps" src/seat.rs '                    && !g.in_past(q, *u)
' '                    && !g.in_past(q, *u)
                    && !g.in_past(*u, q)
'
plant "a lone removal lifts" src/seat.rs 'SeatKind::Unseat => er.conf() == Some(Conf::Group) && !lone.contains(&e),' 'SeatKind::Unseat => er.conf() == Some(Conf::Group),'
plant "the holder's own end lifts" src/seat.rs '.is_some_and(|t| t.seat_kind() == SeatKind::Offer && !t.to().contains(er.signer())),' '.is_some_and(|t| t.seat_kind() == SeatKind::Offer),'
plant "an ordered pair read as mutual" src/seat.rs '(0..n).map(|i| (0..n).filter(|&j| dep(i, j) && !after[i].contains(&j)).collect()).collect();' '(0..n).map(|i| (0..n).filter(|&j| dep(i, j)).collect()).collect();'
plant "an act decided before an earlier act in its past (cascade through an ordered pair)" src/seat.rs '(0..n).map(|i| (0..n).filter(|&j| dep(i, j) && !after[i].contains(&j)).collect()).collect();' '(0..n).map(|i| (0..n).filter(|&j| dep(i, j) && !g.in_past(acts[j], acts[i])).collect()).collect();'
plant "the remover left in the count's receipt's base" src/seat.rs '    let (mem, v) = pp.count(&mem, &voices_with(qr, &p, spec), None, &[xr.signer().clone()]);' '    let (mut mem, v) = pp.count(&mem, &voices_with(qr, &p, spec), None, &[xr.signer().clone()]);
    mem.insert(pp.member(xr.signer()));'
plant "a mutual pair decided one then the other" src/seat.rs '                let v = removal_in_force(c, acts[j], law, spec, by, unseats, now, cache, &ex, &lone, "moderate");' '                let ex: BTreeSet<usize> =
                    ex.iter().copied().chain(got.iter().filter(|(_, v)| !*v).map(|(j, _)| acts[*j])).collect();
                let drop2: BTreeSet<R::Id> = ex.iter().map(|&y| g.row(y).id().clone()).collect();
                let now = nows
                    .entry(drop2.clone())
                    .or_insert_with(|| Seats::build(c, law, spec, own, Some(&drop2), Some(cache)));
                let v = removal_in_force(c, acts[j], law, spec, by, unseats, now, cache, &ex, &lone, "moderate");'
plant "the count's receipt read by its row's policy" src/seat.rs '    // the members'"'"' check of one member'"'"'s act, whatever policy or need the row states
    room_count(yes, mem.len())' '    met(law.policy_of(qr.policy().map(|w| w.as_ref())), yes, mem.len(), qr.need())'
plant "the members' check with no floor of two"     src/seat.rs '    2 * yes > base && yes >= 2' '    2 * yes > base'
plant "a count end's lifts unread" src/seat.rs '(counted || e.is_none_or(|e| !lifts(e)))' '(counted || true)'
plant "a receipt after the end keeps a removal"     src/seat.rs 'acks.iter().any(|&(q, counted)| e.is_none_or(|e| !g.in_past(e, q)) &&' 'acks.iter().any(|&(q, counted)| true &&'
plant "a removal at a later head than the end counts" src/seat.rs '!g.in_past(e, x) && !later(head_of(e)) && kept(Some(e))' '!g.in_past(e, x) && kept(Some(e))'
plant "a members' count confers a duty (the gate removed)" src/seat.rs 'if is_offer && !duty_gate(law, spec, &by, p, r) {' 'if false {'
plant "the duty gate reads counted off the room" src/seat.rs 'r.counted().is_some_and(|c| c.as_ref() == "duty") && pol == Some(Policy::DutyConfer)' 'row_of(by, &obj).and_then(|g| g.counted()).is_some_and(|c| c.as_ref() == "duty") && pol == Some(Policy::DutyConfer)'
plant "one duty's holders pass the duty gate" src/seat.rs 'r.counted().is_some_and(|c| c.as_ref() == "duty") && pol == Some(Policy::DutyConfer)' 'r.counted().is_some_and(|c| law.is_duty(c.as_ref(), &declared)) && pol == Some(Policy::DutyConfer)'
plant "the lone founder's word read as another scope than moderate" src/seat.rs 'Sc::Moderate => R::word("moderate"),' 'Sc::Moderate => R::word("review"),'
plant "the window takes a withdrawal's scope at its word" src/window.rs '            if seat::stay_end(law, by, wr, &|a| c.concluded_id(a.id()) && g.id_in_past(a.id(), wi)).as_ref()
                != Some(&obj)
            {' '            if !law.roster_seats.iter().any(|r| Some(r.as_str()) == wr.scope().map(|s| s.as_ref())) {'
# retired at the merge: "a count naming another object's heads" (heads replaces the check by H1: a count's heads are its own object's counted changes)
plant "a lone removal over an object that is no community" src/seat.rs '    if !community(&by, &obj) {
        return false;
    }
    // an unseat of an agent' '    // an unseat of an agent'
plant "a record's declared roster scope read as a duty" src/seat.rs '    d == "member" || d == AGENT
}' '    false
}'
plant "a lone founder holds no duty" src/seat.rs '    if lone_founding(o) {
        let mut out' '    if false {
        let mut out'
plant "a deputy's act reads no edge" src/standing.rs '    let x = match root_edge(x, index, cap)? {' '    let x = match Ok::<Result<&R, Nobody>, R::Id>(Ok(x))? {'
plant "a deputy's edges not passed to conferral" src/standing.rs '(self.kind == conferral::Kind::Act).then(|| self.row.via()).flatten()' 'None'
plant "a root edge by a key that is not the grantee" src/standing.rs 'if (grant.role)(x.signer()) != Role::Grantee {' 'if false {'
plant "two owners read on the deputy's act, not its root edge" src/standing.rs 'Ok(Ok((e, b))) => match two_owners(e, b, rows, past) {' 'Ok(Ok((_e, b))) => match two_owners(x, b, rows, past) {'
plant "two live owners still give an owner"          src/standing.rs 'Ok(true) => drop(out.insert(x.id().clone(), Answer::Nobody(Nobody::TwoOwners))),' 'Ok(true) => at.push((x, b)),'
plant "a remover seated again revives its removal"   src/seat.rs 'if now.stands(m, scope, &obj, None) && standing.iter().any(|s| live.contains(&(&s.0, &s.1)) && !ended.contains(s)) {' 'if now.stands(m, scope, &obj, None) && (standing.is_empty() || !live.is_empty() || !ended.is_empty()) {'
plant "a lone removal reaches a key with no agent's seat (a re-seating then admits a key never seated)" src/seat.rs 'if !agent || !members_at_with(p, law, spec, &obj, r.head(), AGENT, cache).contains(&r.to()[0]) {' 'if !agent {'
plant "an election's tie broken by list order"         src/ranked.rs 'back: if declared { -(index(o) as i64) } else { 0 }' 'back: -(index(o) as i64)'
plant "a version counts though what it builds on does not" src/line.rs 'if builds_on(i).iter().all(|e| out.contains(e)) {' 'if true {'
plant "the lazy closure skips a past it already knows"  src/graph.rs 'Some(pa) => b.union(pa),' 'Some(_) => {}'
plant "a row is concluded before what it names"         src/layers.rs 'order.sort_by_key(|&i| g.level(i));' 'order.sort_by_key(|&i| core::cmp::Reverse(g.level(i)));'
plant "an owner's revocation ends another owner's seat"  src/seat.rs 'if own { r.to()[0] != *r.signer() } else { Obj::Key(r.to()[0].clone()) != obj }' 'if own { false } else { Obj::Key(r.to()[0].clone()) != obj }'
plant "one of two live owners revokes alone"            src/seat.rs 'sole.one(us.as_ref(), &obj).as_ref() == Some(r.signer())' 'sole.stands(r.signer(), us.as_ref(), &obj, None)'
plant "a duty seat stands on a key that is not a member" src/seat.rs 'if held.contains(&true) {' 'if false {'
plant "a resignation ends no duty seat by its past (revival)" src/seat.rs 'if !off_ended(o, k, sc) && !unseated(oi, k, sc) && !resigned(oi, k, sc) && !merged_out(oi, k, sc) {' 'if !off_ended(o, k, sc) && !unseated(oi, k, sc) && !merged_out(oi, k, sc) {'
plant "a removal from the roster cuts the member seat only (revival)" src/seat.rs '                    && (ur.scope().map(|x| x.as_ref()) == Some(sc.s())
                        || (dutyish' '                    && (ur.scope().map(|x| x.as_ref()) == Some(sc.s())
                        || (false'
plant "a holder's end of its stay ends another key's duty seats" src/seat.rs '*k2 == k && oo.as_ref() == Some(room) && g.in_past(oi, *w) && (duty ||' '(*k2 == k || duty) && oo.as_ref() == Some(room) && g.in_past(oi, *w) && (duty ||'
plant "at tips a duty seat does not follow the folded roster" src/seat.rs '!self.duty[i]
            || self.tips_fold("member", &r.obj).is_none_or(|c| c.contains(&r.k))' 'true || self.tips_fold("member", &r.obj).is_none_or(|c| c.contains(&r.k))'
plant "the founding seat is no member seat" src/seat.rs 'let own = (o.obj() == Some(Obj::Row(o.id().clone())) && o.scope().map(|x| x.as_ref()) == Some(s)) || roster;' 'let own = roster;'
plant "every seat over a community asks for membership" src/seat.rs 'community(by, &obj) && !founding(o) && !roster && law.is_duty(sc, &declared(by, &obj))' 'community(by, &obj) && !founding(o) && !roster'
plant "the duty-seat rule reaches duty rooms only" src/seat.rs 'community(by, &obj) && !founding(o) && !roster && law.is_duty' 'duty_room(by, &obj) && !founding(o) && !roster && law.is_duty'
plant "a duty count counts a holder whose resignation is in its past" src/seat.rs '    if law.is_duty(scope, &duties) || role {' '    if false {'
# retired at the heads merge: "a family founder's role survives its leaving" (H1 / the heads' reading of a leaving pre-empt it)
plant "a holder admitted again stays out of the duty count" src/seat.rs 'if !seated_after(p, obj, k, w.id(), |m| roster_offer(law, m)) {' 'if true {'
plant "a founding record's duty holders unread" src/seat.rs '    if o.duty_holders().is_empty() {
        return alloc::vec![Sc::Row(own)];' '    if true {
        return alloc::vec![Sc::Row(own)];'
plant "a founding row with no map seats an unsigned key that accepts later" src/seat.rs '    if !founding(o) {
        // an admission carrying' '    if !founding(o) || (o.duty_holders().is_empty() && !lone_founding(o)) {
        // an admission carrying'
plant "a listed member who did not sign the record is seated" src/seat.rs '    if !signed {
        return Vec::new();' '    if false {
        return Vec::new();'
plant "a withdrawal's scope unread (laying down a duty ends every seat)" src/seat.rs '&& w.scope().is_none_or(|ws| ws.as_ref() == sc.s())' ''
plant "a roster cut ends duty seats of a key that holds no such seat" src/seat.rs '                            && oo.as_ref().is_some_and(|x| holds_roster(c, law, u, k, x))));' '                            && oo.is_some()));'
plant "a withdrawal naming a roster scope ends the stay whatever its target gives" src/seat.rs '
            && seat_scopes(t, k, signed_by(t, k)).iter().any(|s| s.s() == ws.as_ref()))' ')'
plant "E7 read from any standing now" src/seat.rs 'if now.stands(m, scope, &obj, None) && standing.iter().any(|s| live.contains(&(&s.0, &s.1)) && !ended.contains(s)) {' 'if now.stands(m, scope, &obj, None) && !standing.is_empty() && !live.is_empty() && !ended.is_empty() && false {'
plant "a removal the count carries is read as a lone act" src/seat.rs '&& !count_met(&p, law, spec, Some(cache))' ''
plant "room-key finality unread (a removed room key seated again)" src/seat.rs 'if !row_of(by, &obj).is_some_and(|g| community(by, &obj) && g.private_room()) {' 'if true {'
plant "room-key finality reaches a public room" src/seat.rs '|g| community(by, &obj) && g.private_room())' '|_| community(by, &obj))'
plant "a moderator's lone removal of a room key is final" src/seat.rs '        count_met(&Past::new(g, u, &anc), law, spec, cache)' '        { let _ = (spec, cache, Past::new(g, u, &anc)); true }'
plant "a resignation is no end of a room key's seat" src/seat.rs '            w.seat_kind() == SeatKind::Withdraw
                && w.signer() == k' '            false
                && w.signer() == k'
plant "a key's own end voids none of its concurrent voices" src/seat.rs '&& (g.concurrent(row, *w) || g.in_past(row, *w))' '&& false'
plant "a key's own end of one seat voids its voices on another" src/seat.rs '&& same_class(*w, o, os.as_ref())' '&& true'
plant "a key's consent before its own end survives it" src/seat.rs '(g.concurrent(row, *w) || g.in_past(row, *w))' 'g.concurrent(row, *w)'
plant "a key's own end voids another key's voices" src/seat.rs '                *k2 == k
                    && oo.as_ref() == Some(room)
                    && same_class(*w, o, os.as_ref())' '                true
                    && oo.as_ref() == Some(room)
                    && same_class(*w, o, os.as_ref())'
plant "a key's resignation ends another key's seats in its past" src/seat.rs '*k2 == k && oo.as_ref() == Some(room) && g.in_past(oi, *w) && (duty ||' '(*k2 == k || !duty) && oo.as_ref() == Some(room) && g.in_past(oi, *w) && (duty ||'
plant "a resignation ends the row it names only" src/seat.rs '&& (duty || same_class(*w, o, sc.s()))' '&& duty'
plant "the wrap set reads no held withdrawal: a resigner is wrapped until a count cites it (wrap_by_roster)" src/seat.rs '                SeatKind::Withdraw => {
                    if let Some(t) = r.target() {
                        wd.entry(t).or_default().push(r);' '                SeatKind::Withdraw if false => {
                    if let Some(t) = r.target() {
                        wd.entry(t).or_default().push(r);'
plant "seats compared by name, not by what they hold" src/seat.rs 'let holds_member = covers(sc, "member") || law.holds.get(sc).is_some_and(|h| h.iter().any(|x| x == "member"));' 'let holds_member = covers(sc, "member");'
plant "a decline is an end of a stay" src/seat.rs '|| !t.to().contains(k) || !consented(by, t, k, before) {' '|| !t.to().contains(k) {'
plant "a consent read from any row, not the withdrawal's concluded past" src/seat.rs '                && before(*a)
' ''
plant "an offer that used a standing acceptance read from any row" src/seat.rs '                        && before(*m)
' ''
plant "a standing acceptance withdrawn before any offer used it ends a stay" src/seat.rs '&& used).then_some(obj)' ' && (used || !used)).then_some(obj)'
plant "an ended stay does not bar an agent seat" src/seat.rs '.any(|sc| seat_class(law, o, sc.s()).is_some_and(fin) && room_key_ended(' '.any(|sc| sc.s() != AGENT && seat_class(law, o, sc.s()).is_some_and(fin) && room_key_ended('
# retired: "only member and agent by name are roster seats for finality" (since the act-to-policy binding a counted
# row of a scope that holds `member` but is no roster seat is no act over a community, so no fixture row shows it)
plant "an unseat of a seat the key never held is an end" src/seat.rs 'if !p.rows().any(|m| seated_by(law, m, qs, k, obj) && p.past(m.id(), q.id())) {' 'if false {'
plant "one key's own row places a roster seat over a community" src/seat.rs 'if matches!(r.conf(), Some(Conf::Own) | Some(Conf::Seat)) {' 'if false {'
# retired at the merge: "an offer waiving the key's consent places a roster seat over a community" (SeatRow::consent_one is gone: no flag waives an acceptance; RK1 stays a case)
plant "a second seat row of a seated key is refused" src/seat.rs '    removed
        || p.rows().any(|w| {' '    removed
        || p.rows().any(|m| m.seat_kind() == SeatKind::Offer && m.obj().as_ref() == Some(obj) && m.to().contains(k) && !founding(m))
        || p.rows().any(|w| {'
plant "one barred key does not bar a batch admission" src/seat.rs 'keys.into_iter().any(|k| {' 'keys.into_iter().all(|k| {'
plant "a key's person: two persons read as the first" src/seat.rs '    if names.len() == 1 {' '    if !names.is_empty() {'
plant "a key's person: any group is a person" src/seat.rs 'if !is_self_kind(kind_of(law, &get, &o)) {' 'if kind_of(law, &get, &o).is_none() {'
plant "a key's person: the key's own end is not read" src/seat.rs 'if keep(&o, s.as_ref(), &k) && !revoked_itself(rows.iter().copied(), &k) {' 'if keep(&o, s.as_ref(), &k) {'
plant "a key's person: an admission in the past is enough (evictions unread)" src/seat.rs '        for k in seats.holders(s.as_ref(), &o, None) {' '        let seated: BTreeSet<R::Key> = rows.iter().filter(|q| q.seat_kind() == SeatKind::Offer && q.obj().as_ref() == Some(&o)).flat_map(|q| q.to().iter().cloned()).collect();
        for k in seated.into_iter().chain(seats.holders(s.as_ref(), &o, None)) {'
plant "a key's person: an eviction concurrent with the row is not read (rule 4)" src/seat.rs 'let keep = |g: &ObjOf<R>, s: &str, key: &R::Key| key != k || !evicted_from(c, at, g, s, k);' 'let keep = |g: &ObjOf<R>, s: &str, key: &R::Key| key != k || !(false && evicted_from(c, at, g, s, k));'
plant "the remover a voice of the count's receipt" src/seat.rs '    let (mem, v) = pp.count(&mem, &voices_with(qr, &p, spec), None, &[xr.signer().clone()]);
    let yes = v.iter().filter(|k| mem.contains(*k)).count();' '    let v = pp.voices(&voices(qr, &p), &mem);
    let (mem, _) = pp.count(&mem, &voices_with(qr, &p, spec), None, &[xr.signer().clone()]);
    let yes = v.len();'
plant "the count's receipt takes the remover out by key before the base is read by person (KP-C)" src/seat.rs '    let (mem, v) = pp.count(&mem, &voices_with(qr, &p, spec), None, &[xr.signer().clone()]);' '    mem.remove(xr.signer());
    let (mem, v) = pp.count(&mem, &voices(qr, &p), None, &[]);'
plant "a person's keys read without its persons (a key of two persons, a revoked genesis key's devices kept)" src/seat.rs '    cand.into_iter().filter(|k| pp.voice(k).as_ref() == Some(person)).collect()' '    cand'
plant "an owner's nodes read from the offers, not the owner seat" src/seat.rs '        .filter(|n| seats.owner(n).as_ref() == Some(owner) && !revoked_itself(rows.iter().copied(), n))' '        .filter(|n| rows.iter().any(|q| q.seat_kind() == SeatKind::Offer && q.obj() == Some(Obj::Key(n.clone())) && q.to().contains(owner)) && !revoked_itself(rows.iter().copied(), n))'
plant "a node bound to two live owners read as each one's" src/seat.rs '        .filter(|n| seats.owner(n).as_ref() == Some(owner) && !revoked_itself(rows.iter().copied(), n))' '        .filter(|n| seats.holders("owner", &Obj::Key(n.clone()), None).contains(owner) && !revoked_itself(rows.iter().copied(), n))'
plant "a node key that revoked itself stays its owner's node" src/seat.rs '        .filter(|n| seats.owner(n).as_ref() == Some(owner) && !revoked_itself(rows.iter().copied(), n))' '        .filter(|n| seats.owner(n).as_ref() == Some(owner))'
plant "a key's person read per roster, not per identity key (two rosters of one genesis key two persons)" src/seat.rs '    if names.len() == 1 {' '    if hit.len() == 1 {'
plant "an evicted genesis key still speaks as its person (r95 P1b)" src/seat.rs '            [] if self.founders.contains(k) => None,' ''
plant "the key a self roster evicts is a voice of its own eviction" src/seat.rs '    let drop_to = f.exclude_target || f.base_excludes_target || evicts;' '    let drop_to = f.exclude_target || f.base_excludes_target || (evicts && false);'
plant "a second self roster of one identity concludes (r96 G1: re-founding)" src/seat.rs '&& p.rows().any(|q| q.signer() == r.signer() && self_founding(law, q))' '&& false'
plant "rival self rosters of one identity read as the person's (r96 G1)" src/seat.rs '        if self_founding(law, g) && founded.get(g.signer()).is_some_and(|&n| n > 1) {' '        if false {'
plant "no reader's line is read: a rival stalls a reader on the first roster (the reader's line)" src/seat.rs '        if !rivals.is_empty() && rival_row(r, &by, &rivals) {' '        if false && rival_row(r, &by, &rivals) {'
plant "two concurrent lone evictions of each other both land (r99 M1)" src/seat.rs '                    .any(|(j, t2, o2, _, s2)| j != i && o2 == o && t2 == s && t == s2 && g.concurrent(*i, *j))' '                    .any(|_| false)'
plant "a self roster's landed lone-path eviction ends nothing (the window an outcome only)" src/seat.rs '            if landed.iter().any(|(l, t, lo, lsc)| {' '            if false && landed.iter().any(|(l, t, lo, lsc)| {'
plant "a self roster's landed lone-path addition seats nothing" src/seat.rs '            for k in keys.iter().filter(|k| p.signer() == *k || p.cosigners().contains(*k)) {' '            for k in keys.iter().filter(|_| false) {'
plant "a family's founding read as a self roster's (r99 drift)" src/seat.rs '    g.seat_kind() == SeatKind::Offer && founding(g) && is_self_kind(kind_of(law, &get, &Obj::Row(g.id().clone())))
}' '    g.seat_kind() == SeatKind::Offer && founding(g) && is_self_kind(g.scope().and_then(|sc| law.kinds.get(sc.as_ref()).copied()))
}'
plant "a landed self-roster window is no head of a later count" src/seat.rs '        (change(law, q, obj, room.as_deref()) || landed_change(p, q, obj))' '        change(law, q, obj, room.as_deref())'
plant "the reader's line read out of order: a later row over the rival takes it up too (r100r)" src/seat.rs '.filter(|&a| !taking.iter().any(|&b| b != a && g.in_past(b, a)))' '.filter(|_| true)'
plant "another signer's claimed cosigners seed the reader's line (r101 R2)" src/seat.rs '    let mine = r.signer() == own;' '    let mine = r.signer() == own || r.cosigners().contains(own);'
plant "a forged cosigner on a concluded seat row seeds the reader's line (review-48 R2s)" src/seat.rs '    let mine = r.signer() == own;' '    let mine = r.signer() == own || (matches!(r.seat_kind(), SeatKind::Offer | SeatKind::Unseat) && c.concluded(a) && r.cosigners().contains(own));'
plant "the person line reads no key end: a thief's row with the reader's revoked key seeds its line (K1)" src/seat.rs '        Some(kv) => kv.counts(c.g.row(a).id(), own),' '        Some(_) => true,'
plant "a revoked key keeps its voice and its devices speak for it" src/seat.rs '            [g] if !self.revoked.contains(g) => Some(g.clone()),' '            [g] => Some(g.clone()),'
plant "an agent's key of a person's roster speaks for that person" src/seat.rs '        if self.agents.contains(k) {
            return Some(k.clone());
        }' ''
plant "two rosters of one genesis key read as two persons" src/seat.rs '        names.into_iter().collect()' '        let _ = names;
        self.rosters.get(k).map(|v| v.iter().map(|g| g.signer().clone()).collect()).unwrap_or_default()'
plant "a count of keys, not persons" src/seat.rs '        let b = self.base(base);
        voices.iter().filter_map(|v| self.voice(v)).filter(|p| b.contains(p)).collect()' '        voices.intersection(base).cloned().collect()'
plant "the base read by key: a person seated by two keys is two members" src/seat.rs '        keys.iter().map(|k| self.member(k)).collect()' '        keys.clone()'
plant "the lift reads the author's devices as other voices" src/seat.rs '        let (mem, v) = pp.count(&mem, &v, None, &[author]);' '        let (mem, mut v) = pp.count(&mem, &v, None, &[author.clone()]);
        v.extend(pp.voice(&author));'
plant "the fold's lift takes the author out by key before the base is read by person (KP-B)" src/seat.rs '                        let (mem, v) = pp.count(&mem, &v, None, &apart);' '                        let mem: BTreeSet<R::Key> = mem.iter().filter(|k| !apart.contains(*k)).cloned().collect();
                        let (mem, v) = pp.count(&mem, &v, None, &[]);'
plant "a named key set apart by key only, not by person" src/seat.rs '                ks.push(self.member(k));
                ks.extend(self.voice(k));' ''
plant "the recall's holder apart by key, not by person" src/seat.rs '        pp.count(&key_mem, &voices_with(r, p, spec), Some(&vot), r.to())' '        (mem, v)'
plant "a window's answers read by key before the opener's withdrawal" src/window.rs '    let is_wd = |a: &&R| own(a.signer()) == opener_own && a.says().is_some_and(|w| w.as_ref() == "withdraw");' '    let is_wd = |a: &&R| *a.signer() == x.opener_signer && a.says().is_some_and(|w| w.as_ref() == "withdraw");'
plant "the opener's own withdrawal needs a voter person (a key of no person withdraws nothing)" src/window.rs '    let is_wd = |a: &&R| own(a.signer()) == opener_own && a.says().is_some_and(|w| w.as_ref() == "withdraw");' '    let is_wd = |a: &&R| person(a).as_ref() == Some(&opener) && a.says().is_some_and(|w| w.as_ref() == "withdraw");'
plant "a room key's offer accepted again re-seats it" src/seat.rs 'SeatKind::Accept if revoked_before(law, spec, r, p, &by, cache) => false,' 'SeatKind::Accept if false => false,'
plant "a window's base read when asked keeps the agents" src/window.rs '            m = persons(m, &agents);' ''
plant "two bindings one in the other's past read as one stint" src/standing.rs 'if rebinds(*c, b, rows) || rebinds(b, *c, rows) {' 'if past.in_past(c.id(), b.id())? || past.in_past(b.id(), c.id())? {'
plant "a One clause over a duty leaves out an agent's act" src/window.rs '        let keys = if cl.how == How::One { held(&cl.over) } else { base(&cl.over) };' '        let keys = base(&cl.over);'
plant "the tips read as their common members" src/seat.rs 'let t = self.fold_of(s, o, &at);' 'let t = self.tips_common(s, o);'
plant "the fold counts a voice it does not seat" src/seat.rs 'let ok = if over == *o && counted == s { Some(seated.clone()) } else { self.tips_fold(counted, &over) };' 'let ok: Option<BTreeSet<R::Key>> = None;'
plant "a member another tip removed stays in the fold" src/seat.rs 'union.iter().filter(|k| !common.contains(*k) && survives(k)).cloned().collect();' 'union.iter().filter(|k| !common.contains(*k)).cloned().collect();'
plant "tips that differ in policy are folded" src/seat.rs 'if regimes.len() > 1 {' 'if false {'
plant "a key admits itself"                           src/seat.rs 'let yes = || v.intersection(mem).filter(move |k| !(is_offer || unanimous) || !to.contains(k));' 'let yes = || v.intersection(mem).filter(move |k| unanimous && !to.contains(k));'
plant "the member removed is no voice of its removal"  src/seat.rs 'let yes = || v.intersection(mem).filter(move |k| !(is_offer || unanimous) || !to.contains(k));' 'let yes = || v.intersection(mem).filter(move |k| !to.contains(k));'
# retired with the open:self_admit cut (Eric, for 1.0; the sheet at a304b485): "a self-admit removal counts the member named" (the code it broke is gone)
plant "a unanimous removal counts the member named"    src/seat.rs 'let others = mem.iter().filter(|k| !to.contains(k)).count();' 'let others = mem.len();'
plant "the fold default ranks across signers"          src/derived.rs 'let key = (r.signer().clone(), t);' 'let key = (c.g.row(rows[0]).signer().clone(), t);'
plant "a claim is read across signers"                 src/derived.rs 'groups.entry((r.signer().clone(), k)).or_default().push(i);' 'groups.entry((c.g.row(rows[0]).signer().clone(), k)).or_default().push(i);'
plant "of two heads one is the claim"                  src/derived.rs '            _ => Claim::Split(heads),' '            _ => heads.first().map_or(Claim::Split(Vec::new()), |h| Claim::Stands(*h)),'
plant "a recanted claim stands"                        src/derived.rs '            [h] if ends(c.g.row(*h)) => Claim::Ended(*h),' '            [h] if false && ends(c.g.row(*h)) => Claim::Ended(*h),'
plant "a later row replaces one it does not name"      src/derived.rs 'g.iter().copied().filter(|&i| !g.iter().any(|&j| j != i && c.g.in_past(i, j))).collect();' 'g.iter().copied().filter(|&i| !g.iter().any(|&j| j > i)).collect();'
plant "an identity reference of any length"             src/seat.rs 't.len() == 43 &&' ''
plant "the frontier's walk skips a past it already knows" src/graph.rs 'Some(pa) => below.union(pa), // the whole past of p, already known' 'Some(_) => {}'
plant "the frontier's walk stops a level too high"      src/graph.rs 'if self.level[p] < low || below.has(p) {' 'if self.level[p] <= low || below.has(p) {'
plant "a graph keeps the last row of an id"             src/graph.rs 'index.dedup_by(|b, a| a.0 == b.0);' 'index.dedup_by(|b, a| { let same = a.0 == b.0; if same { core::mem::swap(a, b); } same });'
plant "the no-cut shortcut taken with cuts"             src/cut.rs 'if self.cuts.is_empty() {' 'if true {'
plant "a kept status answers for another row"           src/cut.rs '*self.memo[i].get_or_init(|| self.solve(i))' '*self.memo[0].get_or_init(|| self.solve(i))'
plant "an offer seating many reads one key's signature for all" src/seat.rs 'let signed = if many { sig.contains(k) } else { signed_by(o, k) };' 'let signed = if many { sig.contains(o.signer()) } else { signed_by(o, k) };'
plant "acceptances filed under one key"                 src/seat.rs 'SeatKind::Accept => acc.entry(r.signer()).or_default().push(i),' 'SeatKind::Accept => acc.entry(g.row(cs[0]).signer()).or_default().push(i),'
plant "any withdrawal ends every acceptance"            src/seat.rs 'let ended = |row: &R| !wd_of(row.id()).is_empty();' 'let ended = |_row: &R| !wd.is_empty();'
plant "kept tips answer for another object"             src/seat.rs 'if let Some(t) = self.tips_memo.borrow().get(o) {' 'if let Some(t) = self.tips_memo.borrow().values().next() {'
plant "kept folded holders answer for another scope"    src/seat.rs 'let at = (String::from(s), o.clone());' 'let at = (String::new(), o.clone());'
plant "the members at a head leave out the head"        src/seat.rs 'hs.iter().any(|&hi| q == hi || g.ancestors(hi).has(q))' 'hs.iter().any(|&hi| g.ancestors(hi).has(q))'
plant "a window's counted scope read as moderate"       src/window.rs 'cache.insert("all".into(), persons(sets[0].clone(), &agents));' 'cache.insert("all".into(), persons(sets[1].clone(), &agents));'
plant "the trust walk's index skips a key's own edges" src/trust.rs 'let lo = by_src.partition_point(|&x| edges[x].src < *k);' 'let lo = by_src.partition_point(|&x| edges[x].src <= *k);'
plant "reach walks one layer too many"                  src/derived.rs '    for _ in 0..depth {' '    for _ in 0..=depth {'
plant "a key's end read from any key"                   src/key_end.rs 'let ended = |k: &R::Key| rev.get(k).is_some_and(|a| now >= *a) || !open.contains(k);' 'let ended = |k: &R::Key| rev.get(k).is_some_and(|a| now >= *a) || open.is_empty();'
plant "retained marks no past below a row"              src/key_end.rs 'todo.push(p);' ''
plant "a view reads another act's receipts"             src/head.rs 'let lo = v.partition_point(|(o, _)| o < a);' 'let lo = v.partition_point(|(o, _)| o <= a);'
plant "a view's member set read as its complement"      src/head.rs 'Members::Set(m) => m.contains(k),' 'Members::Set(m) => !m.contains(k),'
plant "the reader's line forgets what is live"          src/line.rs '.into_iter().filter(|&i| cut_counts(i)).collect();' '.into_iter().collect();'
plant 'a view'"'"'s answer index takes every kind'       src/head.rs 'if r.kind == Kind::Answer {' 'if true {'
plant 'a view never builds its indexes'                  src/head.rs 'let index = me.rec.len() > scanned;' 'let index = false;'
plant 'a window'"'"'s others keep the opener'            src/window.rs 'others.remove(&self.opener_signer);' ''
plant 'a window'"'"'s scope named all fills Base::All'"'"'s name' src/window.rs 'if named.iter().any(|s| *s == "all" || *s == "others") {' 'if false {'
plant 'members at a head read unconcluded rows'          src/seat.rs 'let sc = concluded_over(anc.iter().filter(|&&q| read(q)).map(|&q| g.row(q)));' 'let sc = concluded_over((0..g.len()).filter(|&q| at(q)).map(|q| g.row(q)));'
plant 'the members cache ignores the scope'              src/seat.rs 'let key = (hs, own, void, obj.clone(), String::from(scope));' 'let key = (hs, own, void, obj.clone(), String::new());'
plant 'the members cache ignores a head'                 src/seat.rs 'hs.dedup();' 'hs.dedup(); hs.truncate(1);'
plant 'a weighted sum wraps'                             src/seat.rs 'let sum: u128 = yes().map(|k| weight(k) as u128).sum();' 'let sum: u128 = yes().map(&weight).fold(0u64, |a, x| a.wrapping_add(x)) as u128;'
plant 'a ranked count answered as a count'               src/seat.rs 'if matches!(pol, Some(Policy::Ranked)) {' 'if false {'
plant 'a re-admission read by no count'                 src/seat.rs 'if own && !seated_after(p, obj, w.signer(), w.id(), |m| m.scope().is_some_and(|s| s.as_ref() == scope)) {' 'if own {'
plant 'a seating after a leaving never read'            src/seat.rs '            && p.past(w, m.id())' '            && false'
plant 'a strict fraction read as at least'              src/seat.rs 'let strict = |num: u64, den: u64| y * den as u128 > num as u128 * n;' 'let strict = |num: u64, den: u64| y * den as u128 >= num as u128 * n;'
plant "a recall's floor unread"                          src/seat.rs '=> strict(num, den) && y >= least as u128,' '=> strict(num, den),'
plant 'a recall read as a plain StrictFloor count'      src/seat.rs 'if !is_offer && matches!(pol, Some(Policy::Recall(..))) {' 'if false {'
plant 'a recall counted over its holder'                src/seat.rs 'let base = mem.iter().filter(|k| !to.contains(k)).count();' 'let base = mem.len();'
plant "a recall's holder a voice of it"                  src/seat.rs 'let yes = v.intersection(mem).filter(|k| !to.contains(k)).count();' 'let yes = v.intersection(mem).count();'
plant "a runoff step's tie goes on"                      src/ranked.rs 'let Some(w) = ranked(ballots, &opts, floor, declared).0 else { break };' 'let Some(w) = ranked(ballots, &opts, floor, declared).0 else { opts.remove(0); continue };'
plant 'the runoff order stops at its winner'             src/ranked.rs 'opts.retain(|o| *o != w);' 'opts.clear();'
plant 'options holding no ballot eliminated one by one'  src/ranked.rs 'if s.standing.iter().any(|o| n(o) == 0) {' 'if false {'
plant 'the duty gate reads the stated policy'           src/seat.rs '    let pol = fs.first().and_then(|f| f.pol);' '    let pol = law.policy_of(r.policy().map(|x| x.as_ref()));'
plant 'the lift told by its policy only'                src/seat.rs '        Some((act, _, _)) => act == Act::Lift,' '        Some(_) => pol == Some(Policy::Lift),'
plant "a change of the record's protocol unread"         src/seat.rs '    if am.is_empty() {
        return Some(g);' '    if true {
        return Some(g);'
plant 'a change of the record no act'                   src/seat.rs '            if offer && sc == "record" {' '            if false {'
plant 'a stated regime unread'                          src/seat.rs '                if r.regime().is_some_and(|g| r.obj().and_then(|o| protocol_of(p, law, spec, &o)) != Some(g)) {' '                if false {'
plant 'tips read by their stated regime'                src/seat.rs '                if self.law.acts.is_none() {
                    return (g.row(t).regime(), own);' '                if true {
                    return (g.row(t).regime(), own);'
plant 'the acts table read by no count'                  src/seat.rs '    if law.acts.is_some() {
        match (act_of(law, get, r), r.obj()) {' '    if false {
        match (act_of(law, get, r), r.obj()) {'
plant "a fixed act's stated policy unread"               src/seat.rs 'if stated.is_some_and(|s| s != one.as_str()) {' 'if false {'
plant "a row's choice not held to its act's rows"        src/seat.rs 'if !stated.is_some_and(|s| pols.iter().any(|p| p == s)) {' 'if false {'
plant 'a protocol row counted with no protocol'         src/seat.rs '    if pol != Some(Policy::Protocol) {' '    if true {'
plant 'act_of: the lift read as an admission'          src/seat.rs '                if lift {' '                if false {'
plant 'act_of: a roster seat read as a duty'            src/seat.rs '            if law.roster_seats.iter().any(|x| x == sc) {' '            if false {'
plant "act_of: the election's seating read as a conferral" src/seat.rs '                if sc == "moderate" && law.policy_of(r.policy().map(|x| x.as_ref())) == Some(Policy::Ranked) {' '                if false {'
plant "act_of: a ranked offer of any duty the election"  src/seat.rs 'if sc == "moderate" && law.policy_of(r.policy().map(|x| x.as_ref())) == Some(Policy::Ranked) {' 'if law.policy_of(r.policy().map(|x| x.as_ref())) == Some(Policy::Ranked) {'
plant "C1: the electorate read at the id row, not its vacancy" src/seat/election.rs '        if seats.is_empty() {
            return Some(alloc::vec![ei]);' '        if true {
            return Some(alloc::vec![ei]);'
plant "C1: one end of the seat read, the others not" src/seat/election.rs '(ended.len() == seats.len()).then_some(ends)' '(ended.len() == seats.len()).then_some(ends.iter().copied().max_by_key(|&w| self.row(w).id().clone()).into_iter().collect())'
plant "C1: the electorate read over the whole past" src/seat/election.rs 'let heads: Vec<R::Id> = v.iter().map(|&h| self.row(h).id().clone()).collect();' 'let heads: Vec<R::Id> = self.c.g.frontier(p).iter().map(|&h| self.row(h).id().clone()).collect();'
plant "C1: the ends of the vacancy read as one fold" src/seat/election.rs 'for h in heads.chunks(1) {' 'for h in core::iter::once(&heads[..]) {'
# restored after the batch merge: the electorate is read per end over its own past (C1, F1, F2), so a leaver the
# seating's set names is struck by the count alone, as check_election.py's leaver_voice cases show
plant "C1: a leaver a voice" src/seat/election.rs 'let voters: BTreeSet<R::Key> = el.iter().filter(|k| !left.contains(k)).cloned().collect();' 'let voters: BTreeSet<R::Key> = el.iter().cloned().collect();'
plant "C2: a seating beside a live duty holder" src/seat/election.rs 'if seats.holders("duty", &obj, None).iter().any(|k| !agents.contains(k)) {' 'if false {'
plant "C2: a later election's row in the past unread" src/seat/election.rs '|| is_election(law, q)) && of_later(q))' '|| is_election(law, q)) && of_later(q) && false)'
plant "C4: every seating stands" src/seat/election.rs '        let sets: Vec<BTreeSet<R::Id>> = seatings.iter().map(|&q| self.view(q).2).collect();' '        return seatings.iter().copied().collect();'
plant "C4: twins name two elections" src/seat/election.rs 'match (is_election(self.law, e), e.obj()) {' 'match (false, e.obj()) {'
plant "C4: a twin's withdrawal ends nothing" src/seat.rs 'wd_of(o.id()).iter().any(own) || twin_ids.get(o.id()).unwrap_or(&none_ids).iter().any(twin)' 'wd_of(o.id()).iter().any(own)'
plant "C5: no election closes" src/seat/election.rs '        let seats = self.seatings_of(ek, rows, obj);
        if seats.is_empty() {' '        let seats = self.seatings_of(ek, rows, obj);
        if true {'
plant "C5: a receipt counts though its seating did not stand in its past" src/seat/election.rs 'if self.standing(&here).contains(&s) {' 'if true {'
plant "C5: concurrent receipts of different sets a say" src/seat/election.rs 'if sets.len() != 1 {' 'if sets.is_empty() {'
plant "C5: a leaver kept in the closing base" src/seat/election.rs '            base.retain(|k| !gone.contains(k));' ''
plant "C5: a rival of a closed election stands" src/seat/election.rs 'Some(grp) => el.iter().copied().filter(|&q| self.view(q).2 == grp).collect(),' 'Some(_) => self.standing(el),'
plant "C3, C5: any row named as an election is one" src/seat/election.rs 'if Obj::Row(e.id().clone()) == obj {' 'if true {'
plant "an election's set holds rows signed outside its electorate" src/seat/election.rs '        if !el.contains(q.signer()) {' '        if false {'
plant "a ballot ranking outside the electorate counts" src/seat/election.rs '                && b.ranking().iter().all(|k| voters.contains(k))
' ''
plant "a ballot ranking more than three counts" src/seat/election.rs '                && b.ranking().len() <= ELECTION_RANKS
' ''
plant "a seating signed by another than the winner concludes" src/seat/election.rs 'won.as_ref() == Some(winner) && r.signer() == winner' 'won.as_ref() == Some(winner)'
plant "the fold counts an election's seating as a plain count" src/seat.rs 'Some(Policy::Ranked) => true, // an election' 'Some(Policy::Ranked) => false, // an election'
plant "E3: an unclosed seating that stood and ended names no next election" src/seat/election.rs 'self.standing(&here).contains(&ei) && self.vacancy(ei, p, None).is_some()' 'false'
plant "E3, C3: an election superseded by its ended seating still takes rows" src/seat/election.rs 'if !cx.valid_id(ei, ri, &past) || cx.superseded(ei, &past) {' 'if !cx.valid_id(ei, ri, &past) {'
plant "(2): a fork keeps the forker in the closing base" src/seat/election.rs '            base.retain(|k| !fork.contains(k));' ''
plant "(2): a fork reopens the close for all (the old E2)" src/seat/election.rs 'let fork = self.forkers(ek, rows, rows, obj, &BTreeSet::new());' 'let fork = self.forkers(ek, rows, rows, obj, &BTreeSet::new());
        if !fork.is_empty() {
            return None;
        }'
plant "(1): rows of two elections read as a fork" src/seat/election.rs 'SeatKind::Ballot | SeatKind::Decline => named(r),' 'SeatKind::Ballot | SeatKind::Decline => true,'
plant "(3): an end named by no ballot of the set read as its vacancy" src/seat/election.rs 'if !ballots.iter().any(|b| b.names().contains(&e) && at.contains(b.signer())) {' 'if false {'
plant "F3: a next election stands though its id row is beaten" src/seat/election.rs '            if add.is_empty() {' '            if true {'
plant "F2: an end the seating does not name read as its vacancy" src/seat/election.rs ' || named.is_some_and(|n| !n.contains(wr.id()))' ''
plant "F1: the count reads leavings and withdrawals off the seating's past, not its set" src/seat/election.rs 'let rows: Vec<&R> = all.iter().copied().filter(|q| mine.contains(q.id())).collect();' 'let rows: Vec<&R> = all.clone();'
plant "a seating behind the reader's line read in C4" src/seat.rs 'let beaten = if elections { ecx.beaten(&stale) } else { BTreeSet::new() };' 'let beaten = if elections { ecx.beaten(&BTreeSet::new()) } else { BTreeSet::new() };'
plant "N2: a leaving before the vacancy strikes a re-admitted member" src/seat/election.rs 'let window = !ends.iter().any(|&e| self.c.g.in_past(qi, e));' 'let window = true || ends.is_empty();'
plant "(i): a seating is no say of its signer's" src/seat/election.rs '                _ => sids.contains(r.id()) || ends.contains(r.id()),' '                _ => ends.contains(r.id()),'
plant "(4): the fork read per voice, not per key" src/seat/election.rs 'mine.entry((r.signer(), r.signing_key().unwrap_or(r.signer()))).or_default().push(q);' 'mine.entry((r.signer(), r.signer())).or_default().push(q);'
plant "(1): a row the key only cosigns read as part of a fork" src/seat/election.rs '                mine.entry((r.signer(), r.signing_key().unwrap_or(r.signer()))).or_default().push(q);
            }' '                mine.entry((r.signer(), r.signing_key().unwrap_or(r.signer()))).or_default().push(q);
            }
            if r.obj().as_ref() == Some(obj) {
                for c in r.cosigners() {
                    mine.entry((c, c)).or_default().push(q);
                }
            }'
plant "(4): a device label the row body states read as the signing key" tests/common/mod.rs '        match self.m.get("dev") {' '        match self.m.get("device_label").or(self.m.get("dev")) {'
plant "(ii): of two closes over the rows held, the first stands" src/seat/election.rs '            _ => return None,' '            _ => return Some(met[0].clone()),'
plant "G1: a counted unseat read as its signer's election row" src/seat/election.rs '        ends.retain(|e| self.idx(e).is_some_and(|i| self.row(i).seat_kind() == SeatKind::Withdraw));' ''
plant "G2: the closing base read per group, over its receipts' pasts" src/seat/election.rs '            base.retain(|k| !gone.contains(k));' '            for &a in rs {
                let p = self.past(a);
                for (k, _) in self.departures(&p, obj) {
                    base.remove(&k);
                }
            }'
plant "H1: a leaving that holds its receipt voids it" src/seat/election.rs 'let held = |k: &R::Key, d: usize| by_p.get(k).is_some_and(|rs| rs.iter().any(|&a| g.in_past(a, d)));' 'let held = |_k: &R::Key, _d: usize| false;'
plant "the closing base read from each seating's own electorate" src/seat/election.rs '            let el = common.clone();' '            let el = self.view(s).1;'
plant "the close's base the union of the election's electorates" src/seat/election.rs 'let common: BTreeSet<R::Key> = els.fold(first, |acc, e| acc.intersection(&e).cloned().collect());' 'let common: BTreeSet<R::Key> = els.fold(first, |acc, e| acc.union(&e).cloned().collect());'
plant "(2): an end of an ended seat concludes" src/seat.rs '    let seats = ends_of(by, r);
    if seats.is_empty() {' '    let seats = ends_of(by, r);
    if true {'
plant "(2): a contested end blocks a later end" src/seat.rs '        !dropped.contains(q.id())
    };' '        let _ = dropped;
        true
    };'
plant "rule 5: a one-sided cut contested too" src/seat.rs '        .filter(|u| !d.contains(u))' '        .filter(|u| threats.contains_key(u) || threats.values().any(|t| t.iter().any(|(x, _)| x == u)))'
plant "a left key's offer still standing for the lone holder" src/seat.rs 'a.seat_kind() == SeatKind::Accept && a.signer() == k && a.of() == Some(o.id()))' 'a.seat_kind() == SeatKind::Accept && a.signer() == k && a.of() == Some(o.id()) && !gone.contains(a.id()))'
plant "one target: a removal may name several" src/seat.rs '                            EndKind::Removal => return false,' '                            EndKind::Removal => {}'
plant "one target: a recall may name several" src/seat.rs '                            EndKind::Recall => return false,' '                            EndKind::Recall => {}'
plant "one target: a duty withdrawal may name several" src/seat.rs '                            EndKind::DutyWithdraw => return false,' '                            EndKind::DutyWithdraw => {}'
plant "one target: a demotion may name several" src/seat.rs '                            EndKind::Demotion => return false,' '                            EndKind::Demotion => {}'
plant "FA6: a dissolution read apart from rule 5" src/seat.rs 'is_dissolve(q) && cut.counts(i) && !stale.contains(&i) && !dropped.contains(q.id())' 'false && is_dissolve(q)'
plant "C2: the amendment wait read over a row's own past only" src/seat.rs 'mem.retain(|k| !held.contains(k));' 'let _ = &held;'
plant "H4: a lay-down behind the reader's line read as a vacancy end" src/seat/election.rs 'if self.memo.rends.borrow().contains(wr.id()) {' 'if false {'
plant "F1: the electorate read with every withdrawal of the seating's past" src/seat/election.rs 'let pe: Vec<usize> = p.iter().copied().filter(|&q| q == e || self.c.g.in_past(q, e)).collect();' 'let pe: Vec<usize> = p.to_vec();'
plant "(2): a re-seating after the first end not read" src/seat.rs '                && !obj.as_ref().is_some_and(|o| {
                    seated_after(p, o, k, q.id(), |m| {' '                && !obj.as_ref().is_some_and(|o| false && {
                    seated_after(p, o, k, q.id(), |m| {'
plant 'act_of: a detector seat read as no act'          src/seat.rs '            if sc == "detect" || sc.starts_with("detect:") {' '            if false {'
plant 'act_of: the recall read as the withdrawal'       src/seat.rs '"member" => Some((Act::Recall, ScopeClass::Duty, kind)),' '"member" => Some((Act::DutyWithdraw, ScopeClass::Duty, kind)),'
plant 'act_of: a recall or withdrawal counts any body'  src/seat.rs '                "member" => Some((Act::Recall, ScopeClass::Duty, kind)),
                _ => None,' '                "member" => Some((Act::Recall, ScopeClass::Duty, kind)),
                _ => Some((Act::Recall, ScopeClass::Duty, kind)),'
plant 'act_of: every founding row a community'          src/seat.rs '    let kind = g.scope().and_then(|sc| law.kinds.get(sc.as_ref()).copied()).unwrap_or(CommunityKind::Community);' '    let kind = CommunityKind::Community;'
plant 'kind_of: a founding scope the map names not no kind' src/seat.rs '    let kind = g.scope().and_then(|sc| law.kinds.get(sc.as_ref()).copied()).unwrap_or(CommunityKind::Community);' '    let kind = law.kinds.get(g.scope()?.as_ref()).copied()?;'
plant 'the protocol set open: any word read as majority' src/seat.rs '        community_protocol(word.as_ref(), rec.need(), rec.weights()).ok_or(())?' '        community_protocol(word.as_ref(), rec.need(), rec.weights()).unwrap_or(RoomProtocol::Majority)'
plant 'a change of the record may name any word'        src/seat.rs 'community_protocol(w.as_ref(), r.need(), r.weights()).is_some()' 'true'
plant "a quorum's number read from the row's need"       src/seat.rs 'RoomProtocol::Quorum(m, _) => (Policy::Declared, Some(usize::try_from(m).map_err(|_| ())?)),' 'RoomProtocol::Quorum(..) => (Policy::Declared, r.need()),'
plant "a weighted protocol reads the row's weights"      src/seat.rs '        weights: Some(rec),
        no_self_removal' '        weights: None,
        no_self_removal'
plant "the protocol's body unread"                      src/seat.rs '    if counted != body {' '    if false {'
# retired with the open:self_admit cut (Eric, for 1.0; the sheet at a304b485): 'open:self_admit governs any act, not admissions alone' (the code it broke is gone)
plant 'the order of changes read over the whole graph'  src/seat.rs 'let newest: Vec<&'"'"'a R> = am.iter().copied().filter(|q| !anc.iter().any(|a| a.contains(q.id()))).collect();' 'let newest: Vec<&'"'"'a R> = am.iter().copied().filter(|q| !am.iter().any(|x| x.id() != q.id() && p.past(q.id(), x.id()))).collect();'
plant 'of disagreeing changes one in force'              src/seat.rs 'newest.iter().all(|q| stated(q) == one).then_some(first)' 'Some(first)'
plant 'any change of the record in force, not the newest' src/seat.rs 'newest.iter().all(|q| stated(q) == one).then_some(first)' 'Some(am[0])'
plant 'a change of the record counted under the founding protocol' src/seat.rs '    let rec = protocol_record(p, law, spec, &obj).ok_or(())?;' '    let rec = match &obj { Obj::Row(i) if r.scope().is_some_and(|s| s.as_ref() == "record") => p.get(i), o => protocol_record(p, law, spec, o) }.ok_or(())?;'
plant "an infrastructure quorum not its N's strict majority" src/seat.rs 'RoomProtocol::Quorum(m, n) if m >= 2 && m == n / 2 + 1 => Some(p),' 'RoomProtocol::Quorum(m, _) if m >= 2 => Some(p),'
plant 'an infrastructure quorum of one voice'           src/seat.rs 'RoomProtocol::Quorum(m, n) if m >= 2 && m == n / 2 + 1 => Some(p),' 'RoomProtocol::Quorum(m, n) if m == n / 2 + 1 => Some(p),'
# retired: "an infrastructure quorum's N the record's" (N is the founder seats at the row's heads, P1 redo; the plants on M below)
plant "an infrastructure record change counted as a community's" src/seat.rs '    if kind_of(law, get, &obj) == Some(CommunityKind::Infrastructure) {' '    if kind_of(law, get, &obj) == Some(CommunityKind::Infrastructure) && !r.scope().is_some_and(|s| s.as_ref() == "record") {'
# retired with the open:self_admit cut (Eric, for 1.0; the sheet at a304b485): 'under open:self_admit a record change an admission' (the code it broke is gone)
# retired with the open:self_admit cut (Eric, for 1.0; the sheet at a304b485): 'under open:self_admit a removal counted' (the code it broke is gone)
plant "an act's body the row's"                          src/seat.rs 'if counted != body_of(get, (act, sc, kind), &obj) {' 'if false {'
plant 'an infrastructure community counted over its members' src/seat.rs '        if counted != "founder" {' '        if counted != "founder" && counted != "member" {'
plant "an infrastructure community's M recomputed from the founders" src/seat.rs 'need: f.need };' 'need: f.infra.map_or(f.need, |_| Some(mem.len() / 2 + 1)) };'
plant "an infrastructure founding word's N free"        src/seat.rs 'if core::ptr::eq(rec, founding) && founders_of(get, &obj) != n {' 'if false {'
plant 'an infrastructure record not entrenched'          src/seat.rs '        if founding.protocol_entrenched() != Some(true) {' '        if false {'
# retired: 'an infrastructure founder seat by a plain widening' (the acts table has no admit / founder / infrastructure row at 8c75ae7)
plant "an infrastructure amendment's N free"             src/seat.rs '                if usize::try_from(n2) != Ok(n_after) {' '                if false {'
plant 'an infrastructure amendment restates the word always' src/seat.rs '            if unchanged && n_after > n {' '            if unchanged && (n_after > n || !new.is_empty()) {'
plant 'an infrastructure amendment lowers M'             src/seat.rs '                if !usize::try_from(m2).is_ok_and(|m2| m2 >= m) {' '                if false {'
plant 'a stalled room seats a founder by amendment'      src/seat.rs '            if !new.is_empty() && mem.len() < m + 1 {' '            if false {'
plant "an infrastructure amendment's basis moved"        src/seat.rs '        if r.admission_quorum_basis().is_some_and(|b| b.as_ref() != "founders") {' '        if false {'
plant 'a stalled infrastructure room admits and removes' src/seat.rs '&& mem.len() < m + 1 {' '&& false {'
# retired: "an infrastructure room's N caps nothing" (the cap is gone: founder seats come by amendment)
plant 'a new founder need not sign its amendment'       src/seat.rs '            if !new.iter().all(|k| v.contains(*k)) {' '            if false {'
# retired: 'a recovery widening counted as a widening' (no founder widening concludes now: dead)
plant "an admission's role unread"                        src/seat.rs '            o.role().filter(|x| (x.as_ref() == "founder" || x.as_ref() == OFFICER) && o.conf() == Some(Conf::Group))' '            o.role().filter(|_| false)'
plant 'a role read on an own offer'                      src/seat.rs '            o.role().filter(|x| (x.as_ref() == "founder" || x.as_ref() == OFFICER) && o.conf() == Some(Conf::Group))' '            o.role().filter(|x| x.as_ref() == "founder" || x.as_ref() == OFFICER)'
plant 'a role read outside a family'                     src/seat.rs '                if r.role().is_some()
                    && !matches!(' '                if false
                    && !matches!('
plant 'an own offer of an infrastructure founder seat'   src/seat.rs '                    if r.scope().is_some_and(|s| s.as_ref() == "founder")
                        && kind_of(' '                    if false
                        && kind_of('
plant 'a conferred founder role outlives the stay'       src/seat.rs '            (sc == "founder" && g.group_kind().is_some_and(|k| k.as_ref() == "family"))' '            (false && g.group_kind().is_some_and(|k| k.as_ref() == "family"))'
plant "a change of the record meets either joined policy" src/seat.rs '!fs.is_empty() && fs.iter().all(|f| count_under(p, law, spec, cache, f, void))' '!fs.is_empty() && fs.iter().any(|f| count_under(p, law, spec, cache, f, void))'
# retired with the open:self_admit cut (Eric, for 1.0; the sheet at a304b485): 'the cosigned_act half blocks where the protocol states no rule' (the code it broke is gone)
plant 'a policy governing alone takes no floor'          src/seat.rs '    if f.floor > 0 && v.iter().filter(|k| mem.contains(*k) && !to.contains(k)).count() < f.floor {' '    if false {'
plant "a community removal's floor unread"              src/seat.rs 'floor: if r.seat_kind() == SeatKind::Unseat && !family { law.removal_floor } else { 0 },' 'floor: 0,'
plant "the founders all the founding row's signers"     src/seat.rs '.filter(|k| g.to().contains(*k))' '.filter(|_| true)'
plant 'a change may weigh one key twice'                 src/seat.rs 'if weights.iter().enumerate().any(|(i, (k, _))| weights[..i].iter().any(|(j, _)| j == k)) =>' 'if false =>'
plant 'a family takes the two-voice floor'               src/seat.rs '        RoomProtocol::parse(word.as_ref()).ok_or(())?
    } else {' '        community_protocol(word.as_ref(), rec.need(), rec.weights()).ok_or(())?
    } else {'
plant 'an entrenched protocol amendable'                 src/seat.rs '    if rec.protocol_entrenched() != Some(true) {
        return true;' '    if true {
        return true;'
plant 'an entrenched record refuses every amendment'     src/seat.rs '    let Some(w) = r.consensus_protocol() else { return r.protocol_entrenched() != Some(false) };' '    let Some(w) = r.consensus_protocol() else { return false };'
plant "an entrenched weighted record's weights free"    src/seat.rs '    if weighted && (r.need() != rec.need() || set(r) != set(rec)) {' '    if false {'
plant 'the contested pair scoped to two kinds'          src/seat.rs '.filter(|&u| g.row(u).conf() == Some(Conf::Group) && !lone_act(c, u, law, spec, cache))' '.filter(|&u| g.row(u).conf() == Some(Conf::Group) && !lone_act(c, u, law, spec, cache) && g.row(u).obj().is_some_and(|o| matches!(kind_of(law, &|i: &R::Id| g.idx(i).map(|j| g.row(j)), &o), Some(CommunityKind::Family | CommunityKind::Infrastructure))))'
plant "a removal voids a voice at any head"             src/seat.rs 'g.row(u2).head().iter().all(|h2| {' 'true || g.row(u2).head().iter().all(|h2| {'
plant 'concurrent counted removals both in force'        src/seat.rs '    if grp.is_empty() || grp.len() + grp_a.len() < 2 {
        return BTreeSet::new();' '    if true {
        return BTreeSet::new();'
plant "concurrent founders' amendments free"             src/seat.rs '        if !pair_keys.is_empty() {
            if r.scope()' '        if false {
            if r.scope()'
plant 'a dissolution leaves the seats'                   src/seat.rs '            if !gone.is_empty() && o.obj().is_some_and(|ob| gone.contains(&ob)) {' '            if false {'
plant 'a row over a dissolved group concludes'           src/seat.rs '            if !founding(r) && r.obj().is_some_and(|o| dissolved_in(p, &o)) {' '            if false {'
# retired at the heads merge: 'a dissolution at any heads' (H1 / the heads' reading of a leaving pre-empt it)
# retired: 'a self-removal read as the leaving' (the member a removal names is no voice of it: F3 follows)
plant "a family's founder_only removal by its target"    src/seat.rs '    let drop_to = f.exclude_target || f.base_excludes_target || evicts;' '    let drop_to = f.base_excludes_target || evicts;'
plant 'a removal counts the member it removes'          src/seat.rs 'base_excludes_target: r.seat_kind() == SeatKind::Unseat && proto != RoomProtocol::Unanimous,' 'base_excludes_target: false,'
plant 'a family with a duty map'                         src/seat.rs '        if p.get(i).ok_or(())?.duty_holders().iter().any(|(d, _)| d.as_ref() != "founder") {' '        if false {'
plant 'a family read as a community'                     src/seat.rs '    if g.group_kind().is_some_and(|k| k.as_ref() == "family") {' '    if false {'
plant 'a one-voice community protocol'                   src/seat.rs 'RoomProtocol::FounderOnly | RoomProtocol::Quorum(1, _) => None,' 'RoomProtocol::FounderOnly => None,'
plant 'founder_only a community protocol'                src/seat.rs 'RoomProtocol::FounderOnly | RoomProtocol::Quorum(1, _) => None,' 'RoomProtocol::Quorum(1, _) => None,'
plant "an infrastructure community's record change no act" src/seat.rs '"record" if offer => return Some((Act::RecordChange, ScopeClass::Record, kind)),' '"record" if false => return Some((Act::RecordChange, ScopeClass::Record, kind)),'
plant "a node's seat waits for the node's acceptance"    src/seat.rs '&& o.scope().is_some_and(|x| x.as_ref() == NODE)' '&& false'
plant "act_of: a record's cohort_subkind unread"         src/seat.rs '    if kind == CommunityKind::Community && g.cohort_subkind().is_some_and(|c| c.as_ref() == "infrastructure") {' '    if false {'
plant 'act_of: a key object of no kind'                 src/seat.rs '        Obj::Key(_) => return Some(CommunityKind::SelfRoster),' '        Obj::Key(_) => return None,'
plant 'a row'"'"'s concluded past read as its first row' src/layers.rs 'self.p.binary_search(&q).is_ok()' 'self.p.first() == Some(&q)'
plant "voices counts a cosignature the row does not name"  src/seat.rs 'for n in r.names() {' 'for n in p.rows().map(|q| q.id()) {'
plant "a cycle of names walked without its stack"       src/graph.rs '                    if l >= WAITING {' '                    if l == WAITING {'
plant "a view walks a cycle of names without its stack"  src/head.rs '                if d >= WAIT {' '                if d == WAIT {'
plant "a held view's receipt leaves its act clean"      src/held_view.rs '            if view.rec.contains_key(a) {' '            if view.rec.contains_key(a) && false {'
plant "a late head leaves the void set as it was"       src/held_view.rs '        let mut whole = !readers.is_empty();' '        let mut whole = false;'
plant "a new entry voided by a head after it"           src/held_view.rs 'v.v.contains(h) && (v.depth[h], h) < me)' 'v.v.contains(h) && me == me)'
plant "a resumed stub keeps its signatures"             src/held_view.rs '            if e.stub {' '            if false {'
plant "a foreign row made dirty"                        src/held.rs '            if !fx {' '            if true {'
plant "the end's line not sibling-safe"              src/conferral.rs '|h| Ok(behind(h)? && !self.past.in_past(e.id(), h)?))?;' '|h| Ok(self.later(Some(h), e.head())? && !self.past.in_past(e.id(), h)?))?;'
plant "is_founder read at the tips of everything held" src/seat.rs '    let Some(i) = g.idx(at) else { return false };
    let anc: Vec<usize> = c.cs().iter().copied().filter(|&q| g.in_past(q, i)).collect();' '    let Some(i) = g.idx(at) else { return false };
    if kind_of(law, &|x| g.idx(x).map(|j| g.row(j)), obj).is_some() {
        return Seats::new(c, law, spec, None).holders("founder", obj, None).contains(key);
    }
    let anc: Vec<usize> = c.cs().iter().copied().filter(|&q| g.in_past(q, i)).collect();'
plant "a one-seat affiliation's removal decides without a countersign" src/seat.rs 'if !needs_countersign(&pu, law, spec) {' 'if true {'
plant "the acting seat countersigns its own act"     src/seat.rs 'signers(u).into_iter().filter(|k| !officer_key(&pp, &seats, k)).collect();' 'signers(u).into_iter().collect();'
plant "the official read from the founding record"   src/seat.rs '    if vs.is_empty() {
        return alloc::vec![g];' '    if true {
        return alloc::vec![g];'
plant "an overseer's review seat not read"           src/seat.rs '        Some(b) if pu.get(b).is_some() => {' '        Some(b) if false && pu.get(b).is_some() => {'
plant "a body of two seats removes on one voice"     src/seat.rs '    pp.count(&seats, &vs, None, &targets).1.len() >= 2' '    pp.count(&seats, &vs, None, &targets).1.len() >= 1'
plant "an agent's duty with no owner's signature"   src/seat.rs 'if on[j] && held[j] && (!member || (agent && !bound(oi, k))) {' 'if on[j] && held[j] && (!member || (agent && false && !bound(oi, k))) {'
plant "two owners of an agent's key read as one"     src/seat.rs 'let one = ws.iter().all(|(w, _)| *w == ws[0].0);' 'let one = true;'
plant "officer_from_founders: the deciding seats read as the members" src/seat.rs '    members_at_with(p, law, spec, obj, heads, OFFICER, None)' '    members_at_with(p, law, spec, obj, heads, "member", None)'
plant "affiliation_body_members: an affiliation's protocol counted over its members" src/seat.rs '    } else if affiliation {' '    } else if false && affiliation {'
plant "no_officer_locks: an affiliation with no officer keeps its seats" src/seat.rs '        if !ended.is_empty() {' '        if false && !ended.is_empty() {'
plant "lone_act_counted: any member's lone act concludes" src/seat.rs '        && members_at_with(p, law, spec, &obj, heads, duty, None).contains(r.signer())' '        && members_at_with(p, law, spec, &obj, heads, "member", None).contains(r.signer())'
plant "lone_act_cosigned: a cosigned lone act concludes" src/seat.rs '        && signers(r).len() == 1' '        && !signers(r).is_empty()'
plant "lone_act_end_unread: a lone act outlives its signer's standing" src/seat.rs '        } else if !removal_in_force(' '        } else if false && !removal_in_force('
plant "lone_act_lift_unread: the members' lift of a lone act not read" src/seat.rs '        if !lifted.is_empty() {' '        if false && !lifted.is_empty() {'
plant "reconsideration_unread: a reversal keeps the takedown" src/seat.rs '            if !reversed.is_empty() {' '            if false && !reversed.is_empty() {'
plant "release_unread: a release naming a withhold lifts nothing" src/seat.rs '        if releases.iter().any(|&j| act_in_force(c, law, spec, g.row(j).id(), own)) {' '        if false && releases.iter().any(|&j| act_in_force(c, law, spec, g.row(j).id(), own)) {'
plant "unproven_fires: a not_proven verdict fires" src/seat.rs '    if r.seat_kind() == SeatKind::Slashing && r.family_param().is_none_or(|o| o.as_ref() != "proven_rogue") {' '    if false && r.seat_kind() == SeatKind::Slashing {'
plant "a one-officer affiliation's lone act decided without a countersign" src/seat.rs '        if needs_countersign(&p, law, spec) && !decided_over(g, c.cs(), &p, law, spec) {' '        if false {'
plant "root_gate_unread: a root chain's gate read from the row's mark" src/seat.rs '    if top.conf() == Some(Conf::Root) {' '    if false && top.conf() == Some(Conf::Root) {'
plant "root_seat_unchecked: a root seat stands without its grant" src/seat.rs '        return r.obj().is_some_and(|obj| root_seat(spec, r, &obj));' '        return r.obj().is_some();'
plant "root_seat_any_duty: a root seat of any duty" src/root.rs 'if g.duty().as_ref() != duty {' 'if false {'
plant "owner_acceptance_unread: the owner's cosignature on the agent's acceptance not read" src/seat.rs '                        .chain(c.cs().iter().copied().filter(|&a| {' '                        .chain(c.cs().iter().copied().filter(|&a| false && {'
plant "root_through_lone_gate: a root seat read by the lone-holder gate" src/seat.rs '    if r.conf() == Some(Conf::Root) {' '    if false && r.conf() == Some(Conf::Root) {'
plant "the lift's base read at its own heads alone"    src/seat.rs '        mem.retain(|k| at_rem.contains(k));
    }
    mem
}' '        let _ = at_rem;
    }
    mem
}'
plant "the lift's base read at the removal's head alone" src/seat.rs '        mem.retain(|k| at_rem.contains(k));
    }
    mem
}' '        mem = at_rem;
    }
    mem
}'
plant "rule 5 reads removals only"                   src/seat.rs '    let grp_a: Vec<usize> = acts.iter().copied().filter(|&a| g.row(a).conf() == Some(Conf::Group)).collect();' '    let grp_a: Vec<usize> = acts.iter().copied().filter(|_| false).collect();'
plant "a contested removal takes a voice"              src/seat.rs '    let live = &d;' '    let live = &pos;'
plant "release_by_any_holder: another holder's release lifts a withhold (G21)" src/seat.rs '                if w.signer() != r.signer() {' '                if false {'
plant "self_release: a content's author reverses its takedown" src/seat.rs '    if act_targets(t, &|i: &R::Id| p.get(i)).contains(r.signer()) {' '    if false && act_targets(t, &|i: &R::Id| p.get(i)).contains(r.signer()) {'
plant "target_any_room: a takedown of another room's content" src/seat.rs '            if r.family_param().is_none() || cr.room().or(cr.obj()).as_ref() != Some(&obj) {' '            if r.family_param().is_none() {'
plant "target_any_room: a marker of a key not seated in the room" src/seat.rs '    if let Some(t) = key.as_ref().filter(|_| matches!(k, SeatKind::Quarantine | SeatKind::Slashing)) {' '    if let Some(t) = key.as_ref().filter(|_| false) {'
plant "binding_on_carrier: a new binding revives an old conferral" src/seat.rs '                        g.idx(b).is_some_and(|bi| g.in_past(bi, oi))' '                        g.idx(b).is_some_and(|bi| carriers.iter().any(|&ci| g.in_past(bi, ci)))'
plant "agent_by_seat_only: an agent admitted as a member needs no owner" src/seat.rs '.filter(|&&(_, k, sc)| sc.s() == AGENT || registered.contains(k))' '.filter(|&&(_, _k, sc)| sc.s() == AGENT)'
plant "a registered agent admitted as a member is counted in a count's base" src/seat.rs '    out.extend(registered_agents(p.rows()));' ''
plant "the person map recognises an agent by its seat only (a registered agent admitted as a member speaks)" src/seat.rs '    agents.extend(registered_agents(rows.iter().copied()));' ''
plant "overseer_end_unread: an ex-overseer countersigns" src/seat.rs '|| !body.as_ref().is_some_and(|b| overseer_cut(g, rows.iter().copied(), ui, b, k))' '|| true'
plant "countersign_against_member_only: a one-officer body appoints an officer alone" src/seat.rs '    !admission
}' '    !admission && affiliation_removal(law, get, r)
}'
plant "an admission by the one officer is a proposal" src/seat.rs '    !admission
}' '    true
}'
plant "an undecided appointment seats" src/seat.rs '        stale.extend(undecided);' '        let _ = undecided;'
plant "an undecided record change is in force in a later row's past" src/seat.rs '    if !needs_countersign(&pq, law, spec) {
        return true;
    }' '    if true {
        return true;
    }'
plant "edge_countersign_unread: a one-officer affiliation's edge needs no countersign" src/trust_rows.rs '        if !countersigned(seats, i) {' '        if false {'
plant "an edge's countersign is no countersign" src/seat.rs '        return kind_of(law, get, &b) == Some(CommunityKind::Affiliation);' '        return false;'
plant "lone_regrowth_unread: a lone conferral concurrent with the grown body's act stands (r81 B2)" src/seat.rs '        if !regrown.is_empty() {' '        if false {'
plant "a reconsideration citing the takedown is not read (G23)" src/seat.rs '                    && the_cite(x) == Some(act)' '                    && false'
plant "a lift's cited act is not read (G24)" src/seat.rs '    cited(r, get, &|q: &R| lone_act_duty(q.seat_kind()).is_some() || q.seat_kind() == SeatKind::Unseat)' '    cited(r, get, &|_q: &R| false)'
plant "an outside voice on a one-officer act that is no countersigner is taken (G15)" src/seat.rs '        return vs.iter().all(|k| officer_key(&pp, &seats, k) || cs.contains(k));' '        return true;'
plant "first_cite: a row citing several reads its first (r98)" src/seat.rs '        [one] => Some(one),' '        [one, ..] => Some(one),'
plant "officers_by_key: two keys of one person are two officers" src/seat.rs '    officers(p, law, spec, &obj).base(&seats).len() == 1' '    seats.len() == 1'
plant "release_end_read: a release falls with its author's standing" src/seat.rs '        if release {
            if end_never_revived(c, &by, i, duty, &counts) {' '        if false {
            if end_never_revived(c, &by, i, duty, &counts) {'
plant "release_concurrent_kept: an end concurrent with a release does not cut it" src/seat.rs 'k == r.signer() && ob == obj && sc.is_none_or(|s| s == scope || roster_word(s))' 'false && k == r.signer() && ob == obj && sc.is_none_or(|s| s == scope || roster_word(s))'
plant "root_seat_stored: a lapsed root seat held from its conclusion" src/seat.rs '            if o.conf() == Some(Conf::Root) && !o.obj().is_some_and(|ob| root_seat(spec, o, &ob)) {' '            if false && o.conf() == Some(Conf::Root) {'
plant "founder_raw_head: is_founder read at the heads the row states" src/seat.rs '    let heads: Vec<R::Id> = {
        let room = room_in(&p, obj);' '    let heads: Vec<R::Id> = if !p.row().head().is_empty() {
        p.row().head().to_vec()
    } else {
        let room = room_in(&p, obj);'
plant "an act naming the end still counts"            src/conferral.rs 'return Ok((false, false, Rule::NamesEnd));' 'return Ok((true, false, Rule::NamesEnd));'
plant "the grantee receipts its own act"              src/conferral.rs 'Role::Grantee | Role::Other => Ok(false),' 'Role::Grantee | Role::Other => Ok(true),'
plant "a receipt after the end keeps the act"         src/conferral.rs 'Ok(!self.key_cut(q)? && self.eligible(q, e)? && !self.past.in_past(e.id(), q.id())?)' 'Ok(!self.key_cut(q)? && self.eligible(q, e)?)'
plant "a past that cannot tell reads as no"            src/conferral.rs 'Err(i) => need = need.or(Some(i)),' 'Err(_) => {}'
plant "a deputy keeps force its edge has lost"         src/conferral.rs '(c, f) = (c && uc, c && f && uf);' '(c, f) = (c && uc, c && f);'
plant "an onward hop passes as its signer's plain act" src/conferral.rs 'if let Some(above) = up.and_then(|u| self.edge(u)) {' 'if let Some(above) = up.and_then(|u| self.edge(u)).filter(|_| false) {'
plant "the cap on a chain of deputies is not read"     src/conferral.rs 'if self.edges(x)? > self.st.deputy_depth {' 'if false {'
plant "sub-delegation asked of the act's own edge"     src/conferral.rs 'if let Some(above) = up.and_then(|u| self.edge(u)) {' 'if let Some(above) = up {'
plant "in force under the grant alone"                 src/standing.rs 'in_force: g.in_force && u.in_force,' 'in_force: g.in_force,'
plant "counted under the binding alone"                src/standing.rs 'counted: g.counted && u.counted,' 'counted: u.counted,'
plant "an act naming the binding stands under it"      src/standing.rs 'Kind::Binding => return Ok(Err(Nobody::NamesBinding)),' 'Kind::Binding => return Ok(Ok(a)),'
plant "any key's acceptance is the owner's"            src/standing.rs '    if b.owner() != Some(a.signer()) {' '    if false {'
plant "a cited binding not live at the acceptance stands (N7)" src/standing.rs '        if past.in_past(e.id(), a.id())? {' '        if false && past.in_past(e.id(), a.id())? {'
plant "an acceptance citing two rows read as citing the first (N7)" src/standing.rs '        _ => return Ok(Err(Nobody::AcceptanceOtherBinding)),' '        _ => &cites[0],'
plant "a cited binding of another key than the grantee stands (N7)" src/standing.rs '    if !b.node().is_some_and(|n| (grant.role)(n) == Role::Grantee) {' '    if b.node().is_some_and(|n| (grant.role)(n) != Role::Grantee) {'
plant "a re-binding does not end the binding before it" src/standing.rs 'Kind::Binding if row.on() == Some(bid) => (conferral::Kind::End, Some(bid)),' 'Kind::Binding if row.on() == Some(bid) => (conferral::Kind::Other, None),'
plant "the member's own end adds tips beside a counted end" src/content.rs 'if ends.iter().any(|e| counts(e) && is_count(e)) {' 'if false {'
plant "the member's own ends are joined, not met"       src/content.rs 'Some(o) => o.intersection(&g).copied().collect(),' 'Some(o) => o.union(&g).copied().collect(),'
plant "a tips row signed by the member is read"         src/content.rs 'for t in self.of_kind(Kind::Tips).filter(|t| is_count(t) && !line.contains(t.id())) {' 'for t in self.of_kind(Kind::Tips).filter(|t| !line.contains(t.id())) {'
plant "the walk passes through a co-member's row"       src/content.rs 'if x.kind() != Kind::Content || !(self.seat.member)(x.signer()) || self.cuts.any.contains(*id) {' 'if x.kind() != Kind::Content || self.cuts.any.contains(*id) {'
plant "a co-member's retraction takes a row out"        src/content.rs 'let content: Vec<&R> =
        rows.iter().copied().filter(|r| r.kind() == Kind::Content && (seat.member)(r.signer())).collect();
    let all' 'let content: Vec<&R> = rows.iter().copied().filter(|r| r.kind() == Kind::Content).collect();
    let all'
plant "a later seat's rows are judged by an earlier end" src/content.rs 'if a.id() == h || past.in_past(a.id(), h)? {' 'if false {'
plant "a row between seats counts"                      src/content.rs 'if at.seat() == SeatAt::Out {' 'if false {'
plant "a row naming the removal as its head waits on it" src/content.rs 'if ends.iter().any(|e| e.id() == h) {' 'if false {'
plant "a retraction is read in its own seat only"       src/content.rs 'out.extend(seat_answers(&sub, seat, past, &retracted, cuts));' 'let sr: BTreeSet<&R::Id> = retracted.iter().copied().filter(|t| sub.iter().any(|w| w.retracts() == Some(*t))).collect(); out.extend(seat_answers(&sub, seat, past, &sr, cuts));'
plant "an end with an end in its past still ends"       src/content.rs 'Ok(seated.then_some(Void::SeatEnded))' 'Ok(seated.then_some(Void::SeatEnded).filter(|_| false))'
plant "an affiliation's record is a plain community's"  src/seat.rs 'if kind == CommunityKind::Community && g.declared_cohort().is_some_and(|c| c.as_ref() == "affiliations") {' 'if false {'
plant "a change of an affiliation's record is no act"   src/seat.rs 'CommunityKind::Affiliation => {' 'CommunityKind::Affiliation if false => {'
plant "an appointment to an affiliation is no act"      src/seat.rs '"member" | OFFICER => Some((if offer { Act::Admit } else { Act::Remove }, ScopeClass::Member, kind)),' '"member" | OFFICER if !offer => Some((Act::Remove, ScopeClass::Member, kind)),'
plant "an affiliation's removal counted as any removal" src/seat.rs '} else if affiliation_removal(law, &|i: &R::Id| by.get(i).copied(), r) {' '} else if false {'
plant "only an affiliation's record is a charter"       src/charter.rs '[CommunityKind::Community, CommunityKind::Infrastructure, CommunityKind::Affiliation];' '[CommunityKind::Affiliation, CommunityKind::Affiliation, CommunityKind::Affiliation];'
plant "a dissolved group still declares"                src/charter.rs 'if seats.dissolved(&obj) {' 'if false {'
plant "a record's stated end is not read"               src/charter.rs 'if now.is_some_and(|t| r.valid_until().is_some_and(|u| *t >= u)) {' 'if false {'
plant "a class's legal weight is not read"              src/charter.rs 'r.licence_classes().map(|c| c.iter().cloned().collect()).unwrap_or_default()' 'r.licence_classes().map(|c| c.iter().map(|(k, _)| (k.clone(), false)).collect()).unwrap_or_default()'
plant "the founding classes stay in force"              src/charter.rs 'if vs.is_empty() {
        return Some(classes_of(g.row(gi), now));' 'if true {
        return Some(classes_of(g.row(gi), now));'
plant "two version tips declare what either lists"      src/charter.rs 'Some(o) => o.intersection(&here).cloned().collect(),' 'Some(o) => o.union(&here).cloned().collect(),'
plant "a version naming both tips decides nothing"      src/charter.rs 'for &t in vs.iter().filter(|&&t| !vs.iter().any(|x| anc[x].contains(&t))) {' 'for &t in vs.iter() {'
plant "a supplied charter widens the one read"          src/trust.rs 'Some(have) => have.retain(|c| new.contains(c)),' 'Some(have) => have.extend(new),'
plant "an acceptance edge admits every class"           src/trust.rs 'if e.refusal().is_some() || !e.admits(c) {' 'if e.refusal().is_some() {'
plant "an empty trust_classes list is admitted"         src/trust.rs 'Some(cs) if cs.is_empty() || cs.windows(2).any(|w| w[0] >= w[1]) => Some(CLASSES_MALFORMED),' 'Some(cs) if cs.windows(2).any(|w| w[0] >= w[1]) => Some(CLASSES_MALFORMED),'
plant "a refused edge is walked"                        src/trust.rs 'if e.refusal().is_some() || !e.admits(c) {' 'if !e.admits(c) {'
plant "an edge for another counts whoever signs it"   src/trust_rows.rs 'Obj::Key(k) => who.contains(k) || seats.holders("key", src, None).iter().any(|x| who.contains(x)),' 'Obj::Key(_) => true,'
plant "a person's roster keys do not speak for it"     src/trust_rows.rs 'Obj::Key(k) => who.contains(k) || seats.holders("key", src, None).iter().any(|x| who.contains(x)),' 'Obj::Key(k) => who.contains(k),'
plant "a community's edge counts its members"          src/trust_rows.rs 'let duty = seats.authority_body(src);' 'let duty: BTreeSet<R::Key> = BTreeSet::new();'
plant "the trust_edge acts row is not read"            src/trust_rows.rs '.is_some_and(|(p, _)| p.len() == 1 && p[0] == "duty_confer");' '.is_some_and(|_| false);'
plant "a delegates_to bearing anything is an edge"     src/trust_rows.rs 'if !r.is_delegates_to() || r.bears().is_none_or(|b| b.as_ref() != BEARS) {' 'if !r.is_delegates_to() {'
plant "an edge row's malformed classes are admitted"   src/trust_rows.rs 'if let Some(why) = e.refusal() {' 'if let Some(why) = None::<&'"'"'static str> {'
plant "an edge's depth above five is capped"           src/trust_rows.rs 'd @ 0..=5 => Some(Ok(Accepts { depth: d as u32, ..e })),' 'd @ 0..=5 => Some(Ok(Accepts { depth: d as u32, ..e })),
        d if d > 5 => Some(Ok(Accepts { depth: 5, ..e })),'
plant "an absent depth is refused"                     src/trust_rows.rs 'match r.trust_depth().unwrap_or(0) {' 'match r.trust_depth().unwrap_or(-1) {'
plant "a withdrawn edge is walked"                     src/trust_rows.rs 'if !ended {' 'if true {'
plant "any key's licence is the authority's act"       src/trust_rows.rs 'if is_the_authority(&at, r.signer(), &a) {' 'if true {'
plant "a license seat is not read"                     src/trust_rows.rs 'if !at.stands(r.signer(), "license", &a, None) {' 'if true {'
plant "a locked community issues its own licence"     src/trust_rows.rs 'if !locked(&at, &a) {' 'if true {'
plant "a community's licence counts a fixed majority"  src/trust_rows.rs 'if declared_count(&past, at.law(), at.spec(), &a, &at.protocol_body(&a), &v) {' 'if counted(v.iter().filter(|k| at.protocol_body(&a).contains(*k)).count(), at.protocol_body(&a).len()) {'
plant "a community's quorum does not issue"            src/trust_rows.rs 'if is_community(&at, &a) {' 'if false {'
plant "a person's roster key is not the person"        src/trust_rows.rs 'Obj::Key(x) => x == k || seats.holders("key", a, None).contains(k),' 'Obj::Key(x) => x == k,'
plant "a community's license seat is no act"           src/seat.rs 'if sc == "license" {' 'if false {'
plant "the root: an iat mismatch read (count)" src/root.rs 'if *iat != b.iat() {' 'if false {'
plant "the root: a first bundle counted by any holder" src/root.rs 'b.holders().iter().all(|k| v.contains(k))' 'b.holders().iter().any(|k| v.contains(k))'
plant "the root: a later bundle counted over its own holders" src/root.rs '.live(q.holders().iter().cloned())' '.live(b.holders().iter().cloned())'
plant "the root: a revoked key stays live" src/root.rs 'hs.into_iter().filter(|k| !un.contains(k)).collect()' 'hs.into_iter().filter(|k| un.contains(k) || true).collect()'
plant "the root: a bound unread" src/root.rs 'continue; // after the bound' '// after the bound'
plant "the root: version unread" src/root.rs 'if b.version() != top + 1 {' 'if false {'
plant "the root: family unread" src/root.rs 'ps.iter().all(|p| p.family() == b.family())' 'ps.iter().all(|p| p.family() == p.family())'
plant "the root: recovery commitments unread" src/root.rs 'return Some("recovery_commitments_not_holders"); // a detail of genesis_bundle_malformed' '// a detail of genesis_bundle_malformed'
plant "the root: a recovery may change another seat" src/root.rs '        if !same {' '        if false {'
plant "the root: a spent commitment concludes" src/root.rs 'return Some(Err("recovery_commitment_spent"));' ''
plant "the root: no bundle self-forked (S'')" src/root.rs 'cs.iter().copied().filter(|b| forked(b)).collect();' 'cs.iter().copied().filter(|b| false && forked(b)).collect();'
plant "the root: T unread" src/root.rs 'if ko.difference(&km).count() > km.difference(&ko).count() {' 'if true {'
plant "the root: two recoveries of one seat both stand" src/root.rs 'if !line.is_disjoint(&tied) && !tied.is_subset(&line) {' 'if false {'
plant "the root: forked joins both stand" src/root.rs '            if self.contested_join(c.id()) {' '            if false && self.contested_join(c.id()) {'
plant "the root: a grant's head rule unread" src/root.rs 'return false; // the head rule' '// the head rule'
plant "the root: a recovery exempt from S''" src/root.rs 'let first = b.prev().is_empty(); // a recovery is no exemption' 'let first = b.prev().is_empty() || b.recovers().is_some();'
plant "the root: recoveries of one seat not settled by T" src/root.rs 'tv.insert(r.clone()); // short of the most: void' ''
plant "the root: a grant's bundles need not be an antichain" src/root.rs '!named.iter().any(|a| named.iter().any(|b| self.in_past(a, b)))' 'true'
plant "the root: a join counted over its predecessors' common holders (join_common_base)" src/root.rs '.filter(|k| !gone.contains(k) && within.is_none_or(|w| w.contains(k)))' '.filter(|k| prevs.iter().all(|x| self.b(x).is_some_and(|xb| xb.holders().contains(k))) && within.is_none_or(|w| w.contains(k)))'
plant "the root: a join naming a void predecessor blocked (join_void_prev_blocks)" src/root.rs 'continue; // a join is judged by its own count, and heals the fork' '// blocked'
plant "the root: a join naming a reader-void predecessor blocked" src/root.rs 'b.prev().len() < 2 && b.prev().iter().any(|p| out.contains(p))' 'b.prev().iter().any(|p| out.contains(p))'
plant "the root: the reader's line unread" src/root.rs 'if !rv.contains(a) && !self.contested(&rest).contains(a) {' 'if true {'
plant "the root: a rotation outlives the seat" src/root.rs '*n == k && rotates' '*n == k && rotates && false'
plant "the root: the join's prev unread" src/root.rs 'if first.map(|q| q.id()) != Some(&b.prev()[0]) {' 'if false {'
plant "the root: a join revives a retired key" src/root.rs 'let gone = if prevs.len() >= 2 { self.retired(prevs) } else { BTreeSet::new() };' 'let gone: BTreeSet<B::Key> = BTreeSet::new();'
plant "the root: a grant resolves without the in-force count" src/root.rs 'if 2 * voices <= held.len() {' 'if false {'
plant "the root: a grant's cosignatures unread" src/root.rs '            if r.cosigns() == Some(gid) {' '            if false && r.cosigns() == Some(gid) {'
plant "the root: a double signer a voice on both siblings (rule 6)" src/root.rs 'self.voices(b).iter().map(|k| self.owner(k)).filter(|k| oc.contains(k)).collect();' 'Vec::new();'
plant "the root: a double signer a voice for a grant at that head" src/root.rs 'self.grant_voices(gid).into_iter().filter(|k| held.contains(k) && !ns.contains(&self.owner(k))).count();' 'self.grant_voices(gid).into_iter().filter(|k| held.contains(k) || ns.is_empty() && false).count();'
plant "the root: a double signer a voice for settling (only on the successors it signed)" src/root.rs 'let d = ds.get(&p).unwrap_or(&none);' 'let d = if bs.iter().any(|c| self.siblings(b, c) && (self.cuts_kept(b, c) || self.cuts_kept(c, b))) { ds.get(&p).unwrap_or(&none) } else { &none };'
plant "the root: a double signer's halt suppressed" src/root.rs 'if !self.live(self.fold(&hs).0).contains(h.signer()) {' 'if !self.live(self.fold(&hs).0).contains(h.signer()) || self.no_say(rd).contains(&self.owner(h.signer())) {'
plant "the root: the double signer's mark carried to later heads" src/root.rs '.filter(|(p, _)| p.is_subset(&hs))' '.filter(|(p, _)| !p.is_empty() || p.is_subset(&hs))'
plant "the root: rule 5 unread" src/root.rs '        out.extend(dep);' '        let _ = dep;'
plant "the root: a recovery behind its holder's head concludes" src/root.rs 'if behind_head {' 'if false {'
plant "an explicit acknowledgement reads no S'' over its own past" src/seat.rs 'let explicit = if ar.seat_kind() == SeatKind::Ack { ar.room() } else { None };' 'let explicit: Option<ObjOf<R>> = None;'
plant "the root: concurrent acknowledgements read as one chain" src/root.rs 'Some(a) => a.get(i).cloned().unwrap_or_default(),' 'Some(_) => (0..i).collect(),'
plant "the root: a settler that states something counted over the reduced base" src/root.rs 'b.names().contains(x.id()) && !states' 'b.names().contains(x.id()) && (states || !states)'
plant "the root: double signers left in the settler's base" src/root.rs '.filter(|k| !d.contains(&self.owner(k))).collect();' '.filter(|k| d.is_empty() || !d.is_empty()).collect();'
plant "the root: a holder's two settlers at one head both counted" src/root.rs 'd.extend(self.settler_double_signers(b.prev()));' 'let _ = self.settler_double_signers(b.prev());'
plant "the root: a settler's target not checked (a dummy target)" src/root.rs 'let Some(x) = target else { return Err("genesis_bundle_count_unmet") };' 'let Some(x) = target.or(kids.first().copied()) else { return Err("genesis_bundle_count_unmet") };'
plant "the root: a settler's base over the siblings it names only" src/root.rs 'let ds = self.double_signers(&kids);' 'let named: Vec<&B> = b.names().iter().filter_map(|n| self.b(n)).collect(); let ds = self.double_signers(&named);'
plant "the root: a concurrent row's settled bundle kept, not its line" src/root.rs '.flat_map(|(_, x)| self.line(x))' '.flat_map(|(_, x)| [x.clone()])'
plant "the root: a settler closed by the reader's line" src/root.rs 'let mut rest: BTreeSet<B::Id> = ids.difference(&st).cloned().collect();' 'let mut rest: BTreeSet<B::Id> = ids.clone();'
plant "the root: a settler overturns a reader settled past the contest" src/root.rs 'if self.b(i).and_then(|b| b.settles()).is_some_and(|x| out.contains(x)) {' 'if self.b(i).and_then(|b| b.settles()).is_some_and(|x| out.contains(x) && false) {'
plant "the root: a contested join's token unread" src/root.rs 'Some(if self.contested_join(i) { "genesis_join_contested" } else { "void" })' 'Some("void")'
plant "the root: the fold always common" src/root.rs '        if charters.len() > 1 {' '        if true {'
plant "the root: differing charters fold" src/root.rs '        if charters.len() > 1 {' '        if false {'
plant "the root: the fold unguarded" src/root.rs 'self.removals(t2, k, field).iter().all(|r| a.as_ref().is_some_and(|a| self.in_past(r, a)))' 'true'
plant "the root: the anchor unread" src/root.rs 'rd.anchor.as_ref().filter(|a| firsts.contains(a))' 'firsts.first().copied()'
plant "the root: two thumbprint matches pick one" src/root.rs '(m.len() == 1).then(|| m[0].clone())' 'm.first().map(|x| (*x).clone())'
plant "the root: who else signs unread" src/root.rs '}) && self.join_signers(b).iter().all(|(_, ks)| ks.iter().any(|k| voices.contains(k)))' '})'
plant "the root: a retired or left key re-seated" src/root.rs 'if b.holders().iter().any(|k| retired.contains(k) || left.contains(k)) {' 'if false {'
plant "the root: a commitment spent on a branch" src/root.rs 'if b.recovery().iter().any(|(_, c)| spent.contains(c)) {' 'if false {'
plant "the root: behind read as any past" src/root.rs '&& self.behind(b, x)' '&& self.in_past(&b.prev()[0], x.id())'
plant "the root: a detail given as the name" src/root.rs 'self.counted_raw(i).map_err(|why| detail_of(why).unwrap_or(why))' 'self.counted_raw(i)'
plant "the root: in force global" src/root.rs 'held.iter().filter(|i| accepted.contains(*i)).cloned().collect();' 'held.iter().cloned().collect();'
plant "the root: a grant's charter unread" src/root.rs 'self.b(n).is_none_or(|b| !b.duties().contains(g.duty()))' 'false'
plant "the root: the scope in force unread" src/root.rs 'if !self.scope_in_force(rd).contains(g.duty()) {' 'if false {'
plant "the root: a recovery grant's resolution unread" src/root.rs '        self.root.grant_in_force(grant, &self.reader)?;' ''
plant "the root: a recovery grant's room scope unread" src/root.rs 'if *room != crate::seat::Obj::Row(g.scope().clone()) {' 'if false {'
plant "the root: a recovery key's identity unread" src/root.rs 'if !id.user || id.node {' 'if false {'
plant "stalled read over the row's own counted scope" src/seat.rs '    let scope = "founder";' '    let scope = p.row().counted().map(|c| c.as_ref()).unwrap_or("member");'
plant "a stalled recovery while live" src/seat.rs '    if founders > m {' '    if false {'
plant "a stalled recovery that changes more" src/seat.rs 'if r.to().len() != 1 || r.consensus_protocol().is_some() || !r.cosigners().is_empty() {' 'if false {'
plant "a stalled recovery signed by another key" src/seat.rs 'if r.to()[0] != named || *r.signer() != named {' 'if false {'
plant "a roster merge counted with its own keys as no voices (not as an admission at the tip)" src/seat.rs '    let to: &[R::Key] = if merging { &[] } else { r.to() };' '    let to: &[R::Key] = r.to();'
plant "a roster merge in an infrastructure room counted" src/seat.rs 'let infra_merge = kind_of(law, &|i| p.get(i), &obj) == Some(CommunityKind::Infrastructure);' 'let infra_merge = false;'
plant "a roster merge signed by a stalled tip (infrastructure)" src/seat.rs 'if founders.len() <= m ||' 'if false ||'
plant "a roster merge keeps the old word above N (infrastructure)" src/seat.rs 'if nf <= n {' 'if true {'
plant "a roster merge stating any roster" src/seat.rs '    if stated != members {' '    if false {'
plant "merge_ends_duties: a roster merge ends every duty seat in its past (N5)" src/seat.rs '                    sc.s() == "member" && !m.merge_members().contains(k)' '                    sc.s() != "member" || !m.merge_members().contains(k)'
plant "a roster merge voided with a void head (S'')" src/seat.rs '&& !g.row(q).merge()' '&& !g.row(q).merge() || false'
plant "a roster merge concluded again for the reader" src/seat.rs 'return c.g.idx(p.row().id()).is_some_and(|i| c.cs().contains(&i));' 'return seat_rule_with(p, law, spec, &|_| true, Some(&cache));'
plant "a roster merge ends no seat it does not state" src/seat.rs '&& !resigned(oi, k, sc) && !merged_out(oi, k, sc) {' '&& !resigned(oi, k, sc) {'
plant "a roster merge behind for a reader (its void head blocks it)" src/seat.rs '        r.merge()' '        false && r.merge()'
plant "a roster merge asks each key's acceptance" src/seat.rs '            if o.merge() {' '            if false && o.merge() {'
plant "merge: a void tip read (r76 MG6)" src/seat.rs 'if tips.iter().any(|&t| void.contains(g.row(t).id())) {' 'if tips.iter().any(|&t| void.contains(g.row(t).id()) && false) {'
plant "merge: the tip's departed founders by the seat's own leaving only (drift)" src/seat.rs 'for k in count_left(&ps, law, &obj, "founder") {' 'for k in left_in_past(&ps, &obj, "founder") {'
plant "left_in_past: a scopeless withdrawal of a role seat unread" src/seat.rs '&& seat_scopes(t, w.signer(), false).iter().any(|s| s.s() == scope);' '&& seat_scopes(t, w.signer(), false).iter().any(|s| s.s() == scope) && false;'
plant "consent: a grant's classes unread" src/consent.rs '            .filter(|g| covers(g.classes(), class))' '            .filter(|_| true)'
plant "consent: a class entry covers by raw prefix, colon or not" src/consent.rs '        if e.ends_with(":") {' '        if true {'
plant "consent: a grant whose classes are no sorted set concludes" src/consent.rs '        Kind::Grant => well_formed(r),' '        Kind::Grant => true,'
plant "consent: the key view unread" src/consent.rs '    rd.counts(r.id(), r.signer())' '    rd.counts(r.id(), r.signer()) || true'
plant "consent: the key view asked about the peer's key" src/consent.rs '    rd.counts(r.id(), r.signer())' '    rd.counts(r.id(), r.peer().unwrap_or(r.signer()))'
plant "consent: a federation grant with an unannounced party placed" src/consent.rs '                && placed(c, i, rd)' '                && (placed(c, i, rd) || true)'
plant "consent: an announcement counted without the key view" src/consent.rs 'c.g.in_past(a, g) && rd.counts(q.id(), k)' 'c.g.in_past(a, g)'
plant "consent: a grant not in the reading row's past read" src/consent.rs '                && at.is_none_or(|a| upto(c, i, a))' '                && at.is_none_or(|_| true)'
plant "consent: the signer's other device no withdrawer" src/consent.rs '        if person_stands(c, w, k, p, rd) {' '        if person_stands(c, w, k, p, rd) && false {'
plant "consent: the peer no withdrawer" src/consent.rs '    if gr.peer() == Some(k) {' '    if false && gr.peer() == Some(k) {'
plant "consent: a node the grant is for no withdrawer" src/consent.rs '&& rd.person(&o, wr.id(), false) == pg && uncut(c, w, k, &o, rd) {' '&& rd.person(&o, wr.id(), false) == pg && uncut(c, w, k, &o, rd) && false {'
plant "consent: the owner no withdrawer" src/consent.rs '&& rd.person(&o, wr.id(), false) == pw && uncut(c, w, gr.signer(), &o, rd) {' '&& rd.person(&o, wr.id(), false) == pw && uncut(c, w, gr.signer(), &o, rd) && false {'
plant "consent: an ownership's end does not cut a concurrent withdrawal" src/consent.rs '    uncut_by(c, w, ownership_ends(c, node, owner, rd))' '    let _ = ownership_ends(c, node, owner, rd); true'
plant "consent: a device's end as the person's does not cut its withdrawal" src/consent.rs '    rd.counts(c.g.row(w).id(), k) && uncut_by(c, w, person_ends(c, k, person, rd))' '    let _ = (w, k, person, rd); true'
plant "consent: a withdrawal ends the grant by past only" src/consent.rs 'Some(a) => !(a != w && c.g.in_past(a, w)),' 'Some(a) => upto(c, w, a),'
plant "consent: a withdrawal read over every held row ends nothing" src/consent.rs '                None => true,' '                None => false,'
plant "consent: the term read as closed" src/consent.rs '(Some(u), Some(t)) => crate::covers_at(None, Some(u), &t),' '(Some(u), Some(t)) => t <= u,'
plant "consent: a term read without an instant" src/consent.rs '(Some(_), None) => false,' '(Some(_), None) => true,'
plant "consent: the owner not a principal" src/consent.rs 'core::iter::once(node.clone()).chain(rd.owner(node, at, true)).collect()' 'core::iter::once(node.clone()).collect()'
plant "the fold default reads the instant before the past" src/derived.rs '.filter(|x| !strong.contains(x))' '.filter(|_| true)'
plant "the fold default: a row beats only its own past, not what its past beat" src/derived.rs '            st.extend(inherited);' '            let _ = inherited;'
plant "the fold default: the earliest instant wins among the concurrent" src/derived.rs '&& c.g.concurrent(x, y) && ikey(y) > ikey(x)' '&& c.g.concurrent(x, y) && ikey(y) < ikey(x)'
plant "the fold default: an instant tie to the highest id" src/derived.rs '        (at(r), core::cmp::Reverse(r.id()))' '        (at(r), core::cmp::Reverse(core::cmp::Reverse(r.id())))'
plant "key_end: an ended key's vote counted because a live row cites it (ended_vote_retained_by_cite)" src/key_end.rs '        before(c, i, e, ra)' '        (before(c, i, e, ra) || c.cs().iter().any(|&x| c.g.in_past(i, x) && c.g.row(x).signer() != k))'
plant "key_end: the bytes of a counted row of an ended key kept (no stub reading)" src/key_end.rs '|| (stubs && r.statement().is_some() && counts(c, i))' '|| (r.statement().is_some() && counts(c, i))'
plant "seat: the key view not read at the voices step (key_view_unread)" src/seat.rs 'let Some(kv) = spec.key_view() else { return voices(r, p) };' 'let Some(kv) = spec.key_view().filter(|_| false) else { return voices(r, p) };'
plant "seat: only the counted row's signer read by the key view (cosigner_key_unchecked)" src/seat.rs '.filter(|k| kv.counts(r.id(), k))' '.filter(|k| k != r.signer() || kv.counts(r.id(), k))'
plant "window: the key view not read for answers (window_key_view_unread)" src/window.rs 'kept = answers.iter().copied().filter(|a| kv.counts(a.id(), a.signer())).collect();' 'kept = answers.iter().copied().filter(|a| kv.counts(a.id(), a.signer()) || true).collect();'
plant "election: the key view not read for ballots (ballot_key_view_unread)" src/seat/election.rs '&& spec.key_view().is_none_or(|kv| kv.counts(b.id(), b.signer()))' '&& spec.key_view().is_none_or(|kv| kv.counts(b.id(), b.signer()) || true)'
plant "seat: a lift objection not read by the key view (lift_key_view_unread)" src/seat.rs '&& spec.key_view().is_none_or(|kv| kv.counts(c.id(), c.signer()))' '&& spec.key_view().is_none_or(|kv| kv.counts(c.id(), c.signer()) || true)'
plant "seat: a lone removal's single-key receipt not read by the key view (receipt_key_view_unread)" src/seat.rs 'if spec.key_view().is_some_and(|kv| !kv.counts(qr.id(), qr.signer())) {' 'if spec.key_view().is_some_and(|kv| !kv.counts(qr.id(), qr.signer()) && false) {'
plant "seat: a lone act not read by the key view (lone_key_view_unread)" src/seat.rs 'if spec.key_view().is_some_and(|kv| !kv.counts(r.id(), r.signer())) {' 'if spec.key_view().is_some_and(|kv| !kv.counts(r.id(), r.signer()) && false) {'
plant "key_end: a reader's own row after its key's end on its line (reader_line_unchecked)" src/key_end.rs '    crate::seat::own_row(c, a, own, &|a| es.iter().all(|&(e, ra)| before(c, a, e, ra)))' '    crate::seat::own_row(c, a, own, &|_| es.is_empty() || true)'
plant "key_end: own_row reads only concluded rows the reader signed (own_unconcluded_unread)" src/seat.rs '    let mine = r.signer() == own;' '    let mine = r.signer() == own && c.concluded(a);'
# folded into the one own_row (seat::own_row): key_end: own_row reads no voice of a concluded seat row (own_voice_unread), as the r101 plants on it
# folded into the one own_row (seat::own_row): key_end: own_row reads any row claiming the reader as a cosigner (own_claimed_cosigner), as the r101 plants on it
plant "seat: with no key view, a registered self-unseat read by past only (registered_by_past)" src/seat.rs '    move |a| rs.iter().all(|&x| c.g.in_past(a, x))' '    move |a| rs.iter().all(|&x| !c.g.in_past(x, a))'
plant "key_end: a revoked key's rotation concludes (revoked_key_rotates, r114 TR2)" src/key_end.rs '                !revoked
                    && prev' '                true
                    && prev'
plant "key_end: a rotation over its key's registered self-unseat concludes (r114 TR2, the seat lane's form)" src/key_end.rs 'if p.ancestors().iter().any(|&i| crate::seat::registered_self_unseat(g.row(i), old)) {' 'if false && p.ancestors().iter().any(|&i| crate::seat::registered_self_unseat(g.row(i), old)) {'
plant "key_end: the key lane's conclusion concludes a seat row (key_rule_concludes_seat_rows, the K2 class)" src/key_end.rs '        return crate::seat::seat_rule(p, law, spec, &|_| true);' '        return true;'
plant "key_end: after the roster's void a later rotation retires the key again (void_reopens, r118 TR1v2)" src/key_end.rs '    rots.retain(|&r| closing.iter().all(|&v| c.g.in_past(v, r)));' '    let _ = &closing;'
plant "key_end: after the roster's void a later rotation names a successor (r118 TR1v2)" src/key_end.rs '        .filter(|&i| closing.iter().all(|&v| c.g.in_past(v, i)))' '        .filter(|&i| closing.is_empty() || i < usize::MAX)'
plant "key_end: a revocation an end while a rotation stands (retired_key_revokes, r114 ruled (1))" src/key_end.rs 'pub fn revocation_stands(rots: &[usize]) -> bool {
    rots.is_empty()' 'pub fn revocation_stands(rots: &[usize]) -> bool {
    rots.is_empty() || true'
plant "seat: registered_ends reads no order against the rotations (retired_registered_ends, r110 RK2)" src/seat.rs '    c.cs().iter().copied().filter(|&e| registered_self_unseat(c.g.row(e), k) && keep(e)).collect()' '    c.cs().iter().copied().filter(|&e| registered_self_unseat(c.g.row(e), k)).collect()'
plant "seat: the seat-lane revocation no end of the key (registered_end_unread)" src/seat.rs '    c.cs().iter().copied().filter(|&e| registered_self_unseat(c.g.row(e), k) && keep(e)).collect()' '    c.cs().iter().copied().filter(|&e| false && keep(e)).collect()'
plant "seat: an unconcluded registered self-unseat an end (registered_unconcluded_counted)" src/seat.rs '    c.cs().iter().copied().filter(|&e| registered_self_unseat(c.g.row(e), k) && keep(e)).collect()' '    (0..c.g.len()).filter(|&e| registered_self_unseat(c.g.row(e), k) && keep(e)).collect()'
plant "seat: the person map reads no key-lane revocation (person_key_lane_unread)" src/seat.rs '            revoked.extend(ks.into_iter().filter(|k| kv.revoked(k, &ids)));' '            let _ = (ks, ids, kv);'
plant "key_end: a voided rotation names a successor (successor_roster_unread)" src/key_end.rs '        .filter(|&i| !voided(c, i, roster))' '        .filter(|&i| !voided(c, i, roster) || true)'
plant "key_end: the reader's taken-up line unread (taken_up_unread)" src/key_end.rs '|| own.iter().any(|&a| (a == i || c.g.in_past(i, a)) && !c.g.in_past(e, a))' '|| own.is_empty() && false'
plant "key_end: a count final by acknowledgement reopened (final_count_unread)" src/key_end.rs '|| finals.iter().any(|&fi| !c.g.in_past(e, fi))' '|| (finals.is_empty() && false)'
plant "key_end: a final count protects a voice cast after its end (final_protects_late)" src/key_end.rs '|| finals.iter().any(|&fi| !c.g.in_past(e, fi))' '|| finals.iter().any(|&fi| fi == fi)'
plant "seat: an unclean receipt counted toward finality (receipt_unclean_counts)" src/seat.rs 'let Some((kc, roster)) = keys else { return true };' 'let Some((kc, roster)) = keys else { return true }; if roster.len() < usize::MAX { return true; }'
plant "key_end: a rotation the self roster voids still an end (rotation_void_unread)" src/key_end.rs 'q.roster_end() == Some(x.key) && q.names().contains(r.id())' 'false && q.roster_end() == Some(x.key) && q.names().contains(r.id())'
plant "key_end: a voided rotation's rotated-to key kept (voided_successor_kept)" src/key_end.rs 'if q.roster_end() == Some(k)' 'if false && q.roster_end() == Some(k)'
plant "seat: the old key a cited rotation claims to succeed a voice (disputed_key_voices)" src/seat.rs '            v.remove(old);' '            let _ = old;'
plant "seat: finality's clean test reads the row's own signers only (clean_signers_only)" src/seat.rs '    let voices = voices(r, &p);' '    let voices = signers(r);'
plant "seat: a roster act over any object read as the self roster's (roster_end_any_object)" src/seat.rs 'if kind_of(law, &|i| by.get(i).copied(), &obj) != Some(CommunityKind::SelfRoster) {' 'if false && kind_of(law, &|i| by.get(i).copied(), &obj) != Some(CommunityKind::SelfRoster) {'
plant "seat: a withdrawal of the act in a receipt's past left clean" src/seat.rs '|| g.row(x).target() == Some(r.id()))' '|| (g.row(x).target() == Some(r.id()) && false))'
plant "seat: the one owner reading ignores a re-binding" src/seat.rs '&& self.has(r, "owner") && !rebound(&r.offer)).map(|r| &r.k),' '&& self.has(r, "owner")).map(|r| &r.k),'
plant "an affiliation's edge is a duty conferral"      src/trust_rows.rs 'if kind_of(seats.law(), &get, src) == Some(CommunityKind::Affiliation) {' 'if false {'
plant "a dissolved authority's edges are walked"       src/trust_rows.rs 'if matches!(e.src, Obj::Row(_)) && seats.dissolved(&e.src) {' 'if false {'
plant "a dissolved authority's licence is live"        src/trust_rows.rs 'if is_community(seats, &auth) && seats.dissolved(&auth) {' 'if false {'
plant "a dissolved authority's class is not judged at issuance" src/trust_rows.rs 'if !charters(&at, supplied, now).declares(&auth, cls) {' 'if false {'
plant "a key's own offer of a duty ungated outside a duty room" src/seat.rs '&& !authority_gate(law, spec, r, p, &by, cache, duty_seat(law, &by, r) || own_duty())' '&& !authority_gate(law, spec, r, p, &by, cache, duty_seat(law, &by, r))'
plant "a founding signer's own officer or license seat revives a group" src/seat.rs 'body.len() == 1 && body.contains(r.signer())' 'true'
plant "the ends the reader holds are not read"         src/trust_rows.rs '    if read {
        rows.extend(' '    if false {
        rows.extend('
plant "an end cuts nothing concurrent with it"         src/trust_rows.rs 'rows.retain(|j| !cut.contains(j));' 'let _ = &cut;'
plant "a licence stating no instant meets a term"      src/seat.rs '.any(|r| r.k == *k && g.idx(&r.offer).is_some_and(|i| g.row(i).valid_until().is_none()));' '.any(|r| r.k == *k);'
plant "any signer of an edge withdraws it"            src/trust_rows.rs '&& speaks_at(seats, j, &e.src, own)' ''
plant "an edge is judged at issuance only"             src/trust_rows.rs '[false, true].iter().all(|&read| speaks_over(seats, i, &ended_for_reader(seats, i, read, own), src))' '[false].iter().all(|&read| speaks_over(seats, i, &ended_for_reader(seats, i, read, own), src))'
plant "a licence may predate what it cites"            src/trust_rows.rs 'if (0..c.g.len()).any(|j| anc.has(j) && c.g.row(j).asserted_at().is_some_and(|u| u > t)) {' 'if false {'
plant "a licence's instant is bounded by the reader's rows" src/trust_rows.rs 'if (0..c.g.len()).any(|j| anc.has(j) && c.g.row(j).asserted_at().is_some_and(|u| u > t)) {' 'if (0..c.g.len()).any(|j| j != i && c.g.row(j).asserted_at().is_some_and(|u| u > t)) {'
plant "an edge's term is not read"                     src/trust_rows.rs '(None, _) | (Some(_), None) => false,' '(None, _) | (Some(_), None) => true,'
plant "a concurrent amendment reads as a cut"          src/trust_rows.rs 'Some(_) if issuance(seats, i, &ended_for_reader_with(seats, i, true, false, own)).is_none() => {' 'Some(_) if false => {'
plant "growth the reader holds is not read for the act" src/trust_rows.rs '    if read && amend {
        if let Some(o) = authority_act_over(c, c.g.row(i)) {' '    if false {
        if let Some(o) = authority_act_over(c, c.g.row(i)) {'
plant "a concurrent lone seat is not re-counted"       src/trust_rows.rs '|| (qr.licence_authority().is_none() && !recounted(seats, q, &o))' '|| false'
plant "a holder's own lone conferrals regrow each other" src/seat.rs '                && !one_batch(c, law, q, x, o)' ''
plant "counted_recount_unread: a counted conferral from an old past not re-counted on growth" src/seat.rs '    count_met(&past, law, spec, Some(&local))
}' '    true
}'
plant "growth_ends_read: an end read as body growth" src/seat.rs '    let grows = |q: &R| q.seat_kind() == SeatKind::Offer && body_change(q, o);' '    let grows = |q: &R| body_change(q, o);'
plant "growth_any_body: a counted conferral re-counted against any growth" src/seat.rs '.filter(|&x| offer_of(x).is_some_and(|xr| seats_body(xr) && !same_batch(xr)))' '.filter(|&x| offer_of(x).is_some())'
plant "accept_of_past_grows: an acceptance of an offer in the act's past is growth (r97 A1)" src/seat.rs '                && !of_past' ''
plant "batch_any_heads: the same voices' duty conferrals are one batch at any heads (r97 B6)" src/seat.rs 'own(x) == own(qr) && same_heads(x);' 'own(x) == own(qr);'
plant "growth_ends_unread: the grown body keeps the ends the reader holds (r97 V1, V2)" src/seat.rs 'with_growth_ends(c, q, o, void, with_growth(c, q, &growth))' 'with_growth(c, q, &growth)'
plant "a record change re-counted on growth" src/seat.rs '!roster_word(s.as_ref()) && s.as_ref() != "record")' '!roster_word(s.as_ref()))'
plant "an end cuts whatever its key still holds"       src/trust_rows.rs '*ob == o && who.contains(k) && need.iter().any(|cls| loses(seats, &judged, k, ob, cls))' '*ob == o && who.contains(k)'
plant "a second end cancels the first's cut"           src/trust_rows.rs 'let without: Vec<usize> = judged.iter().copied().filter(|&x| !mine.contains(&x) && !after(x)).collect();' 'let without: Vec<usize> = judged.iter().copied().filter(|&x| mine.first() != Some(&x) && !after(x)).collect();'
# retired at the one-target merge: "a re-seat masks the cut" (the seat model discounts a voice its concurrent end removes itself; check_trust_rows states it)
plant "an end cuts a whole counted row"                src/trust_rows.rs 'if !is_counted_row(c.g.row(*q)) || !recount_without(seats, *q, gone) {' 'if true {'
plant "a full end cuts only its named scope"           src/trust_rows.rs '            for (k, ob, _) in &ks {
                if *ob == o && who.contains(k) && need.iter().any(|cls| loses(seats, &judged, k, ob, cls)) {' '            for (k, ob, sc) in &ks {
                if *ob == o && who.contains(k) && need.iter().any(|cls| scope_class(c, seats.law(), ob, sc.as_ref().map(|w| w.as_ref())).as_deref() == Some(cls.as_str()) && loses(seats, &judged, k, ob, cls)) {'
plant "the reader's line not read on an end"           src/content.rs 'if line.contains(e.id()) {' 'if false {'
plant "a tips row behind the reader's line is read"    src/content.rs 'is_count(t) && !line.contains(t.id())' 'is_count(t)'
plant "an acknowledgement un-voids (ack_unvoids)"      src/content.rs 'if !held.contains(m.id()) && self.past.in_past(m.id(), a.id())? {' 'if self.past.in_past(m.id(), a.id())? {'
plant "the line not sibling-safe"                     src/content.rs 'if !any3(own_heads(m).iter(), |t| self.past.in_past(h, t))? {' 'if !self.past.in_past(h, m.id())? {'
plant "a key removal cuts nothing"                      src/content.rs '    if ends.is_empty() {
        return Ok(out);
    }
    let acks' '    if true {
        return Ok(out);
    }
    let acks'
plant "the walk passes through a cut row"               src/content.rs '|| self.cuts.any.contains(*id) {' '{'
plant "a key removal voids the member's end"         src/content.rs '            if line.contains(e.id()) {' '            if self.cuts.any.contains(e.id()) || line.contains(e.id()) {'
plant "the room's count removes a key"                 src/content.rs '(seat.member)(q.signer()) && (q.removes() == Some(q.signer()) || q.concludes())' '((seat.member)(q.signer()) || (seat.counted)(q.signer())) && (q.removes() == Some(q.signer()) || q.concludes() || (seat.counted)(q.signer()))'
plant "an unconcluded eviction is read"               src/content.rs '&& (q.removes() == Some(q.signer()) || q.concludes())' '&& true'
plant "a row the reader took up is cut"               src/content.rs '            if !taken {' '            if true || !taken {'
plant "the content anchor back (review r83)"           src/content.rs '            if !taken {
                out.any.insert(r.id().clone());
            }' '            let built = r.kind() == Kind::Content
                && any3(
                    rows.iter().copied().filter(|b| {
                        b.kind() == Kind::Content && !(seat.member)(b.signer()) && b.room() == r.room()
                    }),
                    |b| Ok(past.in_past(r.id(), b.id())? && !past.in_past(q.id(), b.id())?),
                )?;
            if !taken && !built {
                out.any.insert(r.id().clone());
            }'
plant "a person-level seat row seats a room"           src/audience.rs 'pub fn seats_of<R: AudienceRow>(r: &R) -> &[R::Key] {
    let seat_family = family_of(r.family()).is_some_and(|f| SEAT_FAMILIES.contains(&f.0));' 'pub fn seats_of<R: AudienceRow>(r: &R) -> &[R::Key] {
    let seat_family = family_of(r.family())
        .is_some_and(|f| SEAT_FAMILIES.contains(&f.0) || f.0 == "identity:occurrence" || f.0 == "self:delegates_to");'
plant "a retraction a key removal cuts is read"         src/content.rs '.filter(|w| !cuts.any.contains(w.id()))' ''
plant "the rooms read as one"                           src/content.rs 'by_room.entry(r.room()).or_default().push(r);' 'by_room.entry(None).or_default().push(r);'
plant "a key removal's walk crosses rooms"            src/content.rs 'if from.is_some_and(|room| room != x.room()) || !out.insert(*id) {' 'if !out.insert(*id) {'
plant "a key removal keeps its causal past only"      src/content.rs 'if kept.contains(r.id()) || past.in_past(r.id(), q.id())? {' 'if past.in_past(r.id(), q.id())? {'
plant "an undecided family takes the default"           src/audience.rs 'FamilyPlacement::Undecided => return Placed::Undecided(fam),' 'FamilyPlacement::Undecided => &[Placement::SelfCollective, Placement::TargetedFamily, Placement::TargetedRoom, Placement::Commons][..],'
plant "a pinned family takes any placement"             src/audience.rs 'if !allowed.contains(&placement) {' 'if false && !allowed.contains(&placement) {'
plant "a targeted row names keys off the roster"        src/audience.rs 'if !r.named().iter().all(|k| within.contains(k) || seats.contains(&k)) {' 'if false {'
plant "a seat row's own keys held to named_within"      src/audience.rs 'within.contains(k) || seats.contains(&k)' 'within.contains(k)'
plant "named_within read on the current roster"       src/audience.rs 'let within = (joins.at_head)(room, r.id());' 'let within = members.clone();'
plant "a seat row over another object seats"          src/audience.rs 'r.seat_act().is_some() && r.obj().is_some() && r.obj() == r.room()' 'r.seat_act().is_some()'
plant "a self row carried by another's row (c.3)"      src/audience.rs '    if !same_person(person, d.signer(), r.signer()) {' '    if false && !same_person(person, d.signer(), r.signer()) {'
plant "a key outside the row's audience carries"      src/audience.rs '|| !ar.holds(d.signer())' ''
plant "a row that does not conclude carries"          src/audience.rs 'if !d.concluded() || key_grant' 'if key_grant'
plant "carried to a key off the roster (c.2)"          src/audience.rs 'let on_roster = |room: &R::Id| aud.meet(&Audience::Keys(roster(room)));' 'let on_roster = |_: &R::Id| aud.clone();'
plant "a key grant carried"                            src/audience.rs '|| key_grant ||' '||'
plant "a seat row of any family seats"                src/audience.rs 'if seat_family && r.seat_act()' 'if r.seat_act()'
plant "a follows row unchecked"                       src/audience.rs '    if let Err(why) = named {
        return Placed::Refused(why);' '    if let Err(why) = named {
        let _ = why;
        return own;'
plant "a follows row read by any reference"           src/audience.rs '        Some(FollowsRef::Evidence) => r.evidence().ok_or(Refusal::FollowsNotNamed),' '        Some(FollowsRef::Evidence) => r.evidence().or(r.cites().first()).ok_or(Refusal::FollowsNotNamed),'
plant "a follows row wider than its own"              src/audience.rs 'Follows::Narrower if within(a, fa, person) => own,' 'Follows::Narrower => own,'
plant "narrower read by keys, not persons"            src/audience.rs 'a.iter().all(|k| b.contains(k) || (person.voice)(k).is_some_and(|p| held.contains(&p)))' '{ let _ = &held; a.is_subset(b) }'
plant "a cited row of any family is followed"         src/audience.rs 'FollowsRef::Cites(of) => family_of(x.family()).is_some_and(|f| of.contains(&f.0)),' 'FollowsRef::Cites(_) => true,'
plant "an owner binding by family alone"              src/seat.rs 'family == OWNER_BINDING_FAMILY && purpose == Some("owner_binding")' 'family == OWNER_BINDING_FAMILY && purpose.is_some_and(|_| true) || family == OWNER_BINDING_FAMILY'
plant "a key of no person read as its own person"    src/audience.rs 'k == of || (person.voice)(of).is_some_and(|p| (person.voice)(k) == Some(p))' 'k == of || (person.voice)(of).is_some_and(|p| (person.voice)(k).is_none_or(|q| q == p))'
plant "a follows row follows an unconcluded row"      src/audience.rs '.filter(|f| by.get(*f).is_some_and(|x| x.concluded()))' '.filter(|f| by.get(*f).is_some())'
plant "a tie takes the first pattern"                 src/audience.rs 'Some((b, _)) if k == b => tie = true,' 'Some((b, _)) if k == b => {}'
plant "the first matching family pattern decides"       src/audience.rs 'Some((b, _)) if k < b => {}' 'Some(_) => {}'
plant "a duty seat seats an outsider"                 src/audience.rs 'let duty = DUTY_SEAT_FAMILIES.contains(&fam);' 'let duty = false && DUTY_SEAT_FAMILIES.contains(&fam);'
plant "a one-officer body's own licence needs no countersign" src/trust_rows.rs 'None if own_licence(seats, i, &ended_for_reader(seats, i, false, own)) && !countersigned(seats, i) => {' 'None if false => {'
# retired at the one-target merge: "an out-of-force removal still ends" (the loss is read through Seats' holders, which drop a contested end; the skip is kept as a shortcut; check_trust_rows states it)
plant_run "a conformance run that never reports"          tests/trust.rs 'report("trust walk, TrustSet.lean worked world", n, 0);' 'let _ = ("trust walk, TrustSet.lean worked world", n, 0);'
if [ "$n" -eq 1 ]; then
  echo "ciris-kernel plants: $caught of $total caught"
else
  echo "ciris-kernel plants: $caught of $total caught (shard $k of $n; $seen plants in all)"
fi
[ $total -gt 0 ] && [ $caught -eq $total ]
