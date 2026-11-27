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
plant "a named head may be any row (H1, H3, H8)" src/seat.rs '.any(|&h| *obj != Obj::Row(h.clone()) && !p.get(h).is_some_and(|q| change(law, q, obj, room.as_deref())))' '.any(|_: &&R::Id| false)'
plant "a counted change of any object moves the head (H1)" src/seat.rs '    if LineSpec::<R>::counted_act(&SeatLine, q).is_some_and(|(o, _)| o == *obj) {' '    if LineSpec::<R>::counted_act(&SeatLine, q).is_some() {'
plant "a counted change behind a named head moves it (H1)" src/seat.rs '&& !heads.iter().any(|&h| h == q.id() || p.past(q.id(), h))' '&& !heads.iter().any(|&h| h == q.id())'
plant "a self-admission is a counted change (H3)"      src/seat.rs '        return law.acts.is_some() || !authored_head(law, q);' '        return true;'
plant "a count over another room concludes (H2)"       src/seat.rs '                    if r.over().is_some_and(|o| o != obj) {
                        return false;
                    }' ''
plant "a lone removal read before the newest-heads rule (H4)" src/seat.rs 'if newer_head_in_past_v(p, law, &obj, r.head(), &signers(r), &cache.current_void()) {' 'if !(!is_offer && lone_removal(r, p, law, spec, Some(cache))) && newer_head_in_past_v(p, law, &obj, r.head(), &signers(r), &cache.current_void()) {'
plant "the withdrawals of a row's past not read with its heads (H4)" src/seat.rs 'let read = |q: usize| at(q) || g.row(q).seat_kind() == SeatKind::Withdraw || acc.contains(g.row(q).id());' 'let read = |q: usize| at(q) || acc.contains(g.row(q).id());'
plant "a holder's own acceptance in a row's past not read (acceptances, (a))" src/seat.rs 'let read = |q: usize| at(q) || g.row(q).seat_kind() == SeatKind::Withdraw || acc.contains(g.row(q).id());' 'let read = |q: usize| at(q) || g.row(q).seat_kind() == SeatKind::Withdraw;'
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
plant "a withdrawal takes back the proposer's approval" src/window.rs 'let by = ops::group_by(answers.iter().copied().filter(|a| voters.contains(a.signer()) && !is_wd(a)), |a| {' 'let by = ops::group_by(answers.iter().copied().filter(|a| voters.contains(a.signer())), |a| {'
plant "an approval that names the withdrawal still approves" src/window.rs 'answers.iter().copied().filter(|a| !(says(a, "approve") && wd.iter().any(|w| past(w, a.id())))).collect()' 'answers.iter().copied().collect()'
plant "concurrent answers not recounted"               src/window.rs 'answers.extend(ans);' ''
plant "a receipt with the target's row in its past is still a receipt" src/window.rs 'return Some(!rows.iter().any(|q| q.signer() == t && q.id() != o.id() && !p.past(q.id(), o.id())));' 'return Some(true);'
plant "a window's opener held to the counted scope"     src/window.rs 'let scope = w.opener.as_ref().unwrap_or(&w.counted);' 'let scope = &w.counted;'
plant "a floored majority read without its floor"       src/window.rs '&How::MoreAtLeast(num, den, least) => more(num, den, n) && y >= least as u128,' '&How::MoreAtLeast(num, den, _) => more(num, den, n),'
plant "the fallback counted over silent members"        src/window.rs 'more(*num, *den, y + no as u128) && y >= *least as u128' 'more(*num, *den, n) && y >= *least as u128'
plant "the fallback read without its floor"             src/window.rs 'more(*num, *den, y + no as u128) && y >= *least as u128' 'more(*num, *den, y + no as u128)'
plant "a vote beside a moderator's answer unsays it"    src/window.rs 'let moot = |a: &R| acted.contains(a.signer()) && duty_word(a).is_none();' 'let moot = |_a: &R| false;'
plant "an act that opens its own window skips the seat" src/window.rs 'if matches!(r.seat_kind(), SeatKind::Offer | SeatKind::Unseat) && !seat_rule(p, law, spec, &|_| true) {' 'if false {'
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
plant "the re-seating counts the author over"           src/seat.rs 'mem.remove(&author); // the author is not among the members the majority is taken of' ''
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
plant "the remover a voice of the count's receipt" src/seat.rs '    v.remove(xr.signer());
    let yes' '    let yes'
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
plant "the remover left in the count's receipt's base" src/seat.rs '    mem.remove(xr.signer());
    let mut v = voices(qr, &p);' '    let mut v = voices(qr, &p);'
plant "a mutual pair decided one then the other" src/seat.rs '                let v = removal_in_force(c, acts[j], law, spec, by, unseats, now, cache, &ex, &lone);' '                let ex: BTreeSet<usize> =
                    ex.iter().copied().chain(got.iter().filter(|(_, v)| !*v).map(|(j, _)| acts[*j])).collect();
                let drop2: BTreeSet<R::Id> = ex.iter().map(|&y| g.row(y).id().clone()).collect();
                let now = nows
                    .entry(drop2.clone())
                    .or_insert_with(|| Seats::build(c, law, spec, own, Some(&drop2), Some(cache)));
                let v = removal_in_force(c, acts[j], law, spec, by, unseats, now, cache, &ex, &lone);'
plant "the count's receipt read by its row's policy" src/seat.rs '    // the members'"'"' check of one member'"'"'s act, whatever policy or need the row states
    room_count(yes, mem.len())' '    met(law.policy_of(qr.policy().map(|w| w.as_ref())), yes, mem.len(), qr.need())'
plant "the members' check with no floor of two"     src/seat.rs '    2 * yes > base && yes >= 2' '    2 * yes > base'
plant "a count end's lifts unread" src/seat.rs '(counted || e.is_none_or(|e| !lifts(e)))' '(counted || true)'
plant "a receipt after the end keeps a removal"     src/seat.rs 'acks.iter().any(|&(q, counted)| e.is_none_or(|e| !g.in_past(e, q)) &&' 'acks.iter().any(|&(q, counted)| true &&'
plant "a removal at a later head than the end counts" src/seat.rs '!g.in_past(e, x) && !later(head_of(e)) && kept(Some(e))' '!g.in_past(e, x) && kept(Some(e))'
plant "a members' count confers a duty (the gate removed)" src/seat.rs 'if is_offer && !duty_gate(law, &by, p, r) {' 'if false {'
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
plant "a key's own offer of a duty ungated outside a duty room" src/seat.rs '&& (duty_seat(law, &by, r) || own_duty())' '&& duty_seat(law, &by, r)'
plant "a lone founder holds no duty" src/seat.rs '    if lone_founding(o) {
        let mut out' '    if false {
        let mut out'
plant "a deputy's act reads no edge" src/standing.rs '    let x = match root_edge(x, index, cap)? {' '    let x = match Ok::<Result<&R, Nobody>, R::Id>(Ok(x))? {'
plant "a deputy's edges not passed to conferral" src/standing.rs '(self.kind == conferral::Kind::Act).then(|| self.row.via()).flatten()' 'None'
plant "a root edge by a key that is not the grantee" src/standing.rs 'if (grant.role)(x.signer()) != Role::Grantee {' 'if false {'
plant "two owners read on the deputy's act, not its root edge" src/standing.rs 'Ok(Ok((e, b))) => match two_owners(e, b, rows, past) {' 'Ok(Ok((_e, b))) => match two_owners(x, b, rows, past) {'
plant "two live owners still give an owner"          src/standing.rs 'Ok(true) => drop(out.insert(x.id().clone(), Answer::Nobody(Nobody::TwoOwners))),' 'Ok(true) => at.push((x, b)),'
plant "a remover seated again revives its removal"   src/seat.rs '    if now.stands(m, "moderate", &obj, None)
        && standing.iter().any(|s| live.contains(&(&s.0, &s.1)) && !ended.contains(s))' '    if now.stands(m, "moderate", &obj, None)
        && (standing.is_empty() || !live.is_empty() || !ended.is_empty())'
plant "a lone removal reaches a key with no agent's seat (a re-seating then admits a key never seated)" src/seat.rs 'if !agent || !members_at_with(p, law, spec, &obj, r.head(), AGENT, cache).contains(&r.to()[0]) {' 'if !agent {'
plant "an election's tie broken by list order"         src/ranked.rs 'back: if declared { -(index(o) as i64) } else { 0 }' 'back: -(index(o) as i64)'
plant "a version counts though what it builds on does not" src/line.rs 'if builds_on(i).iter().all(|e| out.contains(e)) {' 'if true {'
plant "the lazy closure skips a past it already knows"  src/graph.rs 'Some(pa) => b.union(pa),' 'Some(_) => {}'
plant "a row is concluded before what it names"         src/layers.rs 'order.sort_by_key(|&i| g.level(i));' 'order.sort_by_key(|&i| core::cmp::Reverse(g.level(i)));'
plant "an owner's revocation ends another owner's seat"  src/seat.rs 'if own { r.to()[0] != *r.signer() } else { Obj::Key(r.to()[0].clone()) != obj }' 'if own { false } else { Obj::Key(r.to()[0].clone()) != obj }'
plant "one of two live owners revokes alone"            src/seat.rs 'sole.one(us.as_ref(), &obj).as_ref() == Some(r.signer())' 'sole.stands(r.signer(), us.as_ref(), &obj, None)'
plant "a duty seat stands on a key that is not a member" src/seat.rs 'if held.contains(&true) {' 'if false {'
plant "a resignation ends no duty seat by its past (revival)" src/seat.rs 'if !off_ended(o, k, sc) && !unseated(oi, k, sc) && !resigned(oi, k, sc) {' 'if !off_ended(o, k, sc) && !unseated(oi, k, sc) {'
plant "a removal from the roster cuts the member seat only (revival)" src/seat.rs '                    && (ur.scope().map(|x| x.as_ref()) == Some(sc.s())
                        || (dutyish' '                    && (ur.scope().map(|x| x.as_ref()) == Some(sc.s())
                        || (false'
plant "a holder's end of its stay ends another key's duty seats" src/seat.rs '*k2 == k && oo.as_ref() == Some(room) && g.in_past(oi, *w) && (duty ||' '(*k2 == k || duty) && oo.as_ref() == Some(room) && g.in_past(oi, *w) && (duty ||'
plant "at tips a duty seat does not follow the folded roster" src/seat.rs '!self.duty[i]
            || self.tips_fold("member", &r.obj).is_none_or(|c| c.contains(&r.k))' 'true || self.tips_fold("member", &r.obj).is_none_or(|c| c.contains(&r.k))'
plant "the founding seat is no member seat" src/seat.rs 'let own = (o.obj() == Some(Obj::Row(o.id().clone())) && o.scope().map(|x| x.as_ref()) == Some(s)) || roster;' 'let own = roster;'
plant "every seat over a community asks for membership" src/seat.rs 'community(by, &obj) && !founding(o) && !roster && law.is_duty(sc, &declared(by, &obj))' 'community(by, &obj) && !founding(o) && !roster'
plant "the duty-seat rule reaches duty rooms only" src/seat.rs 'community(by, &obj) && !founding(o) && !roster && law.is_duty' 'duty_room(by, &obj) && !founding(o) && !roster && law.is_duty'
plant "a duty count counts a holder whose resignation is in its past" src/seat.rs 'if !mem.is_empty() && (law.is_duty(counted, &duties) || role) {' 'if false {'
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
plant "a withdrawal naming a roster scope ends the stay whatever its target gives" src/seat.rs '            || !seat_scopes(t, k, signed_by(t, k)).iter().any(|s| s.s() == ws.as_ref())
' ''
plant "E7 read from any standing now" src/seat.rs '        && standing.iter().any(|s| live.contains(&(&s.0, &s.1)) && !ended.contains(s))
    {' '        && !standing.is_empty() && !live.is_empty() && !ended.is_empty() && false
    {'
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
plant "a room key's offer accepted again re-seats it" src/seat.rs 'SeatKind::Accept if revoked_before(law, spec, r, p, &by, cache) => false,' 'SeatKind::Accept if false => false,'
plant "a window's base read when asked keeps the agents" src/window.rs '            m = persons(m, &agents);' ''
plant "two bindings one in the other's past read as one stint" src/standing.rs 'if rebinds(*c, b, rows) || rebinds(b, *c, rows) {' 'if past.in_past(c.id(), b.id())? || past.in_past(b.id(), c.id())? {'
plant "a One clause over a duty leaves out an agent's act" src/window.rs '        let keys = if cl.how == How::One { x.held(&cl.over) } else { x.base(&cl.over) };' '        let keys = x.base(&cl.over);'
plant "the tips read as their common members" src/seat.rs 'let t = self.fold_of(s, o, &at);' 'let t = self.tips_common(s, o);'
plant "the fold counts a voice it does not seat" src/seat.rs 'let ok = if over == *o && counted == s { Some(seated.clone()) } else { self.tips_fold(counted, &over) };' 'let ok: Option<BTreeSet<R::Key>> = None;'
plant "a member another tip removed stays in the fold" src/seat.rs 'union.iter().filter(|k| !common.contains(*k) && survives(k)).cloned().collect();' 'union.iter().filter(|k| !common.contains(*k)).cloned().collect();'
plant "tips that differ in policy are folded" src/seat.rs 'if regimes.len() > 1 {' 'if false {'
plant "a key admits itself"                           src/seat.rs 'let yes = || v.intersection(mem).filter(move |k| !(is_offer || unanimous) || !to.contains(k));' 'let yes = || v.intersection(mem).filter(move |k| unanimous && !to.contains(k));'
plant "the member removed is no voice of its removal"  src/seat.rs 'let yes = || v.intersection(mem).filter(move |k| !(is_offer || unanimous) || !to.contains(k));' 'let yes = || v.intersection(mem).filter(move |k| !to.contains(k));'
plant "a self-admit removal counts the member named"   src/seat.rs 'v.iter().filter(|k| mem.contains(*k) && !to.contains(k)).count() >= 2' 'v.iter().filter(|k| mem.contains(*k)).count() >= 2'
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
plant 'a stated regime unread'                          src/seat.rs '                if r.regime().is_some_and(|g| r.obj().and_then(|o| protocol_of(p, &o)) != Some(g)) {' '                if false {'
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
plant "rule 5: a one-sided cut contested too" src/seat.rs '    grp.iter().copied().filter(|u| !d.contains(u)).map(|u| g.row(u).id().clone()).collect()' '    grp.iter().copied().filter(|u| threats.contains_key(u) || threats.values().any(|t| t.iter().any(|(x, _)| x == u))).map(|u| g.row(u).id().clone()).collect()'
plant "a left key's offer still standing for the lone holder" src/seat.rs 'a.seat_kind() == SeatKind::Accept && a.signer() == k && a.of() == Some(o.id()))' 'a.seat_kind() == SeatKind::Accept && a.signer() == k && a.of() == Some(o.id()) && !gone.contains(a.id()))'
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
plant 'open:self_admit governs any act, not admissions alone' src/seat.rs '    if proto == RoomProtocol::SelfAdmit
        && (r.seat_kind() != SeatKind::Offer' '    if false
        && (r.seat_kind() != SeatKind::Offer'
plant 'the order of changes read over the whole graph'  src/seat.rs 'let newest: Vec<&'"'"'a R> = am.iter().copied().filter(|q| !anc.iter().any(|a| a.contains(q.id()))).collect();' 'let newest: Vec<&'"'"'a R> = am.iter().copied().filter(|q| !am.iter().any(|x| x.id() != q.id() && p.past(q.id(), x.id()))).collect();'
plant 'of disagreeing changes one in force'              src/seat.rs 'newest.iter().all(|q| stated(*q) == one).then_some(first)' 'Some(first)'
plant 'any change of the record in force, not the newest' src/seat.rs 'newest.iter().all(|q| stated(*q) == one).then_some(first)' 'Some(am[0])'
plant 'a change of the record counted under the founding protocol' src/seat.rs '    let rec = protocol_record(p, &obj).ok_or(())?;' '    let rec = match &obj { Obj::Row(i) if r.scope().is_some_and(|s| s.as_ref() == "record") => p.get(i), o => protocol_record(p, o) }.ok_or(())?;'
plant "an infrastructure quorum not its N's strict majority" src/seat.rs 'RoomProtocol::Quorum(m, n) if m >= 2 && m == n / 2 + 1 => Some(p),' 'RoomProtocol::Quorum(m, _) if m >= 2 => Some(p),'
plant 'an infrastructure quorum of one voice'           src/seat.rs 'RoomProtocol::Quorum(m, n) if m >= 2 && m == n / 2 + 1 => Some(p),' 'RoomProtocol::Quorum(m, n) if m == n / 2 + 1 => Some(p),'
# retired: "an infrastructure quorum's N the record's" (N is the founder seats at the row's heads, P1 redo; the plants on M below)
plant "an infrastructure record change counted as a community's" src/seat.rs '    if kind_of(law, get, &obj) == Some(CommunityKind::Infrastructure) {' '    if kind_of(law, get, &obj) == Some(CommunityKind::Infrastructure) && !r.scope().is_some_and(|s| s.as_ref() == "record") {'
plant 'under open:self_admit a record change an admission' src/seat.rs '&& (r.seat_kind() != SeatKind::Offer || !r.scope().is_some_and(|s| s.as_ref() == "member"))' '&& r.seat_kind() != SeatKind::Offer'
plant 'under open:self_admit a removal counted'          src/seat.rs '&& (r.seat_kind() != SeatKind::Offer || !r.scope().is_some_and(|s| s.as_ref() == "member"))' '&& r.seat_kind() == SeatKind::Offer && !r.scope().is_some_and(|s| s.as_ref() == "member")'
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
plant "an admission's role unread"                        src/seat.rs '        if let Some(role) = o.role().filter(|x| x.as_ref() == "founder" && o.conf() == Some(Conf::Group)) {' '        if let Some(role) = o.role().filter(|_| false) {'
plant 'a role read on an own offer'                      src/seat.rs '        if let Some(role) = o.role().filter(|x| x.as_ref() == "founder" && o.conf() == Some(Conf::Group)) {' '        if let Some(role) = o.role().filter(|x| x.as_ref() == "founder") {'
plant 'a role read outside a family'                     src/seat.rs '                if r.role().is_some()
                    && !matches!(' '                if false
                    && !matches!('
plant 'an own offer of an infrastructure founder seat'   src/seat.rs '                    if r.scope().is_some_and(|s| s.as_ref() == "founder")
                        && kind_of(' '                    if false
                        && kind_of('
plant 'a conferred founder role outlives the stay'       src/seat.rs '    sc == "founder"
        && !founding(o)' '    false
        && !founding(o)'
plant "a change of the record meets either joined policy" src/seat.rs '!fs.is_empty() && fs.iter().all(|f| count_under(p, law, spec, cache, f, void))' '!fs.is_empty() && fs.iter().any(|f| count_under(p, law, spec, cache, f, void))'
plant 'the cosigned_act half blocks where the protocol states no rule' src/seat.rs '    let dropped = unstated().is_some();' '    let dropped = unstated().is_some() && false;'
plant 'a policy governing alone takes no floor'          src/seat.rs '    if f.floor > 0 && v.iter().filter(|k| mem.contains(*k) && !r.to().contains(k)).count() < f.floor {' '    if false {'
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
plant 'concurrent counted removals both in force'        src/seat.rs '    if grp.len() < 2 {
        return BTreeSet::new();' '    if true {
        return BTreeSet::new();'
plant "concurrent founders' amendments free"             src/seat.rs '        if !pair_keys.is_empty() {
            if !r.scope()' '        if false {
            if !r.scope()'
plant 'a dissolution leaves the seats'                   src/seat.rs '            if !gone.is_empty() && o.obj().is_some_and(|ob| gone.contains(&ob)) {' '            if false {'
plant 'a row over a dissolved group concludes'           src/seat.rs '            if !founding(r) && r.obj().is_some_and(|o| dissolved_in(p, &o)) {' '            if false {'
# retired at the heads merge: 'a dissolution at any heads' (H1 / the heads' reading of a leaving pre-empt it)
# retired: 'a self-removal read as the leaving' (the member a removal names is no voice of it: F3 follows)
plant "a family's founder_only removal by its target"    src/seat.rs '    let drop_to = f.exclude_target || f.base_excludes_target;' '    let drop_to = f.base_excludes_target;'
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
plant "any key's acceptance is the owner's"            src/standing.rs 'if b.owner() != Some(a.signer()) {' 'if false {'
plant "a re-binding does not end the binding before it" src/standing.rs 'Kind::Binding if row.on() == Some(bid) => (conferral::Kind::End, Some(bid)),' 'Kind::Binding if row.on() == Some(bid) => (conferral::Kind::Other, None),'
plant "the member's own end adds tips beside a counted end" src/content.rs 'if ends.iter().any(|e| counts(e) && is_count(e)) {' 'if false {'
plant "the member's own ends are joined, not met"       src/content.rs 'Some(o) => o.intersection(&g).copied().collect(),' 'Some(o) => o.union(&g).copied().collect(),'
plant "a tips row signed by the member is read"         src/content.rs 'for t in self.of_kind(Kind::Tips).filter(|t| is_count(t)) {' 'for t in self.of_kind(Kind::Tips) {'
plant "the walk passes through a co-member's row"       src/content.rs 'if x.kind() != Kind::Content || !(self.seat.member)(x.signer()) || !out.insert(id) {' 'if x.kind() != Kind::Content || !out.insert(id) {'
plant "a co-member's retraction takes a row out"        src/content.rs 'let content: Vec<&R> =
        rows.iter().copied().filter(|r| r.kind() == Kind::Content && (seat.member)(r.signer())).collect();
    let all' 'let content: Vec<&R> = rows.iter().copied().filter(|r| r.kind() == Kind::Content).collect();
    let all'
plant "a later seat's rows are judged by an earlier end" src/content.rs 'if a.id() == h || past.in_past(a.id(), h)? {' 'if false {'
plant "a row between seats counts"                      src/content.rs 'if at.seat() == SeatAt::Out {' 'if false {'
plant "a row naming the removal as its head waits on it" src/content.rs 'if ends.iter().any(|e| e.id() == h) {' 'if false {'
plant "a retraction is read in its own seat only"       src/content.rs 'out.extend(seat_answers(&sub, seat, past, &retracted));' 'let sr: BTreeSet<&R::Id> = retracted.iter().copied().filter(|t| sub.iter().any(|w| w.retracts() == Some(*t))).collect(); out.extend(seat_answers(&sub, seat, past, &sr));'
plant "an end with an end in its past still ends"       src/content.rs 'Ok(seated.then_some(Void::SeatEnded))' 'Ok(seated.then_some(Void::SeatEnded).filter(|_| false))'
plant "the root: an iat mismatch read (count)" src/root.rs 'if *iat != b.iat() {' 'if false {'
plant "the root: a first bundle counted by any holder" src/root.rs 'b.holders().iter().all(|k| v.contains(k))' 'b.holders().iter().any(|k| v.contains(k))'
plant "the root: a later bundle counted over its own holders" src/root.rs '.live(q.holders().iter().cloned())' '.live(b.holders().iter().cloned())'
plant "the root: a revoked key stays live" src/root.rs 'hs.into_iter().filter(|k| !un.contains(k)).collect()' 'hs.into_iter().filter(|k| un.contains(k) || true).collect()'
plant "the root: a bound unread" src/root.rs 'continue; // after the bound' '// after the bound'
plant "the root: version unread" src/root.rs 'if b.version() != top + 1 {' 'if false {'
plant "the root: family unread" src/root.rs 'ps.iter().all(|p| p.family() == b.family())' 'ps.iter().all(|p| p.family() == p.family())'
plant "the root: recovery commitments unread" src/root.rs 'return Some("genesis_bundle_malformed"); // recovery_commitments are keys exactly the holders' '// recovery_commitments are keys exactly the holders'
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
plant "the root: a contested join's token unread" src/root.rs 'Some(if self.contested_join(i) { "genesis_join_contested" } else { "void" })' 'Some("void")'
plant "the root: the fold always common" src/root.rs '        if charters.len() > 1 {' '        if true {'
plant "the root: differing charters fold" src/root.rs '        if charters.len() > 1 {' '        if false {'
plant "the root: the fold unguarded" src/root.rs 'self.removals(t2, k, field).iter().all(|r| a.as_ref().is_some_and(|a| self.in_past(r, a)))' 'true'
plant "the root: the anchor unread" src/root.rs 'rd.anchor.as_ref() == Some(*i)' 'true'
plant "the root: in force global" src/root.rs 'held.iter().filter(|i| accepted.contains(*i)).cloned().collect();' 'held.iter().cloned().collect();'
plant "the root: a grant's charter unread" src/root.rs 'self.b(n).is_none_or(|b| !b.duties().contains(g.duty()))' 'false'
plant "the root: the scope in force unread" src/root.rs 'if !self.scope_in_force(rd).contains(g.duty()) {' 'if false {'
plant "the root: a recovery grant's resolution unread" src/root.rs '        self.root.grant_in_force(grant, &self.reader)?;' ''
plant "the root: a recovery grant's room scope unread" src/root.rs 'if *room != crate::seat::Obj::Row(g.scope().clone()) {' 'if false {'
plant "the root: a recovery key's identity unread" src/root.rs 'if !id.user || id.node {' 'if false {'
plant "stalled read over the row's own counted scope" src/seat.rs '    let scope = "founder";' '    let scope = p.row().counted().map(|c| c.as_ref()).unwrap_or("member");'
plant "a stalled recovery while live" src/seat.rs '    if founders >= m + 1 {' '    if false {'
plant "a stalled recovery that changes more" src/seat.rs 'if r.to().len() != 1 || r.consensus_protocol().is_some() || !r.cosigners().is_empty() {' 'if false {'
plant "a stalled recovery signed by another key" src/seat.rs 'if r.to()[0] != named || *r.signer() != named {' 'if false {'
plant_run "a conformance run that never reports"          tests/trust.rs 'report("trust walk, TrustSet.lean worked world", n, 0);' 'let _ = ("trust walk, TrustSet.lean worked world", n, 0);'
if [ "$n" -eq 1 ]; then
  echo "ciris-kernel plants: $caught of $total caught"
else
  echo "ciris-kernel plants: $caught of $total caught (shard $k of $n; $seen plants in all)"
fi
[ $total -gt 0 ] && [ $caught -eq $total ]
