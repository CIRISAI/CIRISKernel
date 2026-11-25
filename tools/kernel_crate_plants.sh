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
plant "a key's end read inclusively"                   src/key_end.rs 'x.until.is_none_or(|u| now < u)' 'x.until.is_none_or(|u| now <= u)'
plant "the reader's line ignored"                      src/line.rs '(built_ok && !mine.iter().any(|&m| behind(r, m)))' 'built_ok'
plant "a met count is read only by a landing" src/window.rs 'return if got == "open" { Outcome::Open } else { Outcome::Landed(got) };' 'return Outcome::Open;'
plant "a withdrawal takes back the proposer's approval" src/window.rs 'let by = ops::group_by(answers.iter().copied().filter(|a| voters.contains(a.signer()) && !is_wd(a)), |a| {' 'let by = ops::group_by(answers.iter().copied().filter(|a| voters.contains(a.signer())), |a| {'
plant "an approval that names the withdrawal still approves" src/window.rs 'answers.iter().copied().filter(|a| !(says(a, "approve") && wd.iter().any(|w| past(w, a.id())))).collect()' 'answers.iter().copied().collect()'
plant "concurrent answers not recounted"               src/window.rs 'answers.extend(ans);' ''
plant "a receipt with the target's row in its past is still a receipt" src/window.rs 'return Some(!rows.iter().any(|q| q.signer() == t && q.id() != o.id() && !p.past(q.id(), o.id())));' 'return Some(true);'
plant "a window's opener held to the counted scope"     src/window.rs 'let scope = w.opener.as_ref().unwrap_or(&w.counted);' 'let scope = &w.counted;'
plant "a floored majority read without its floor"       src/window.rs '&How::MoreAtLeast(num, den, least) => yes * den > num * n && yes >= least,' '&How::MoreAtLeast(num, den, _) => yes * den > num * n,'
plant "the fallback counted over silent members"        src/window.rs 'yes * den > num * (yes + no) && yes >= *least' 'yes * den > num * n && yes >= *least'
plant "the fallback read without its floor"             src/window.rs 'yes * den > num * (yes + no) && yes >= *least' 'yes * den > num * (yes + no)'
plant "a vote beside a moderator's answer unsays it"    src/window.rs 'let moot = |a: &R| acted.contains(a.signer()) && duty_word(a).is_none();' 'let moot = |_a: &R| false;'
plant "an act that opens its own window skips the seat" src/window.rs 'if matches!(r.seat_kind(), SeatKind::Offer | SeatKind::Unseat) && !seat_rule(p, law, spec, &|_| true) {' 'if false {'
plant "a moderator removes any key alone"               src/seat.rs '|| r.conf() != Some(Conf::Group) || !r.removes_agent() || r.to().len() != 1 {' '|| r.conf() != Some(Conf::Group) || r.to().len() != 1 {'
plant "any key removes an agent's key alone"            src/seat.rs '        && members_at_with(p, law, spec, &obj, r.head(), "moderate", cache).contains(r.signer())' ''
plant "the re-seating counts the author over"           src/seat.rs 'mem.remove(&author); // the author is not among the members the majority is taken of' ''
plant "the removed key is counted over in its re-seating" src/seat.rs 'mem.retain(|k| !r.to().contains(k)); // nor is the key removed: an agent has no vote' ''
plant "the removed key is counted over in the lift"     src/window.rs 'others.retain(|k| !self.removed.contains(k));' ''
plant "a re-seating admits a key never seated"          src/seat.rs 'if !r.to().iter().all(|k| mem.contains(k)) {' 'if false {'
plant "an election's tie broken by list order"         src/ranked.rs 'back: if declared { -(index(o) as i64) } else { 0 }' 'back: -(index(o) as i64)'
plant "a version counts though what it builds on does not" src/line.rs 'if builds_on(i).iter().all(|e| out.contains(e)) {' 'if true {'
plant "the lazy closure skips a past it already knows"  src/graph.rs 'Some(pa) => b.union(pa),' 'Some(_) => {}'
plant "a row is concluded before what it names"         src/layers.rs 'order.sort_by_key(|&i| g.level(i));' 'order.sort_by_key(|&i| core::cmp::Reverse(g.level(i)));'
plant "an owner's revocation ends another owner's seat"  src/seat.rs 'if own { r.to()[0] != *r.signer() } else { Obj::Key(r.to()[0].clone()) != obj }' 'if own { false } else { Obj::Key(r.to()[0].clone()) != obj }'
plant "one of two live owners revokes alone"            src/seat.rs 'sole.one(us.as_ref(), &obj).as_ref() == Some(r.signer())' 'sole.stands(r.signer(), us.as_ref(), &obj, None)'
plant "a duty seat stands on a key that is not a member" src/seat.rs 'if held.contains(&true) {' 'if false {'
plant "a resignation ends no duty seat by its past (revival)" src/seat.rs 'if !off_ended(o, k, sc) && !unseated(oi, k, sc) && !resigned(oi, k, sc) {' 'if !off_ended(o, k, sc) && !unseated(oi, k, sc) {'
plant "a removal from the roster cuts the member seat only (revival)" src/seat.rs 'let held = same && (ur.scope() == Some(sc) || (dutyish && member(ur.scope())));' 'let held = same && ur.scope() == Some(sc);'
plant "a holder's end of its stay ends another key's duty seats" src/seat.rs '*k2 == k && oo.as_ref() == Some(room) && g.in_past(oi, *w)' 'oo.as_ref() == Some(room) && g.in_past(oi, *w)'
plant "at tips a duty seat does not follow the folded roster" src/seat.rs '!self.duty[i] || self.tips_fold("member", &r.obj).is_none_or(|c| c.contains(&r.k))' 'true'
plant "the founding seat is no member seat" src/seat.rs 'let own = (o.obj() == Some(Obj::Row(o.id().clone())) && o.scope().map(|x| x.as_ref()) == Some(s)) || roster;' 'let own = roster;'
plant "every seat the duty holders place asks for membership" src/seat.rs 'duty_seat(law, by, o) && law.is_duty(sc.as_ref(), &declared(by, &obj))' 'duty_seat(law, by, o)'
plant "a duty count counts a holder whose resignation is in its past" src/seat.rs 'if !mem.is_empty() && law.is_duty(counted, &duties) {' 'if false {'
plant "a holder admitted again stays out of the duty count" src/seat.rs 'if !back {' 'if true {'
plant "a founding record's duty holders unread" src/seat.rs 'if o.duty_holders().is_empty() || !founding(o) {' 'if true {'
plant "a listed member who did not sign the record is seated" src/seat.rs '    if !signed {
        return Vec::new();' '    if false {
        return Vec::new();'
plant "a withdrawal's scope unread (laying down a duty ends every seat)" src/seat.rs '&& w.scope().is_none_or(|ws| ws == sc)' ''
plant "the tips read as their common members" src/seat.rs 'let t = self.fold_of(s, o, &at);' 'let t = self.tips_common(s, o);'
plant "the fold counts a voice it does not seat" src/seat.rs 'let ok = if over == *o && counted == s { Some(seated.clone()) } else { self.tips_fold(counted, &over) };' 'let ok: Option<BTreeSet<R::Key>> = None;'
plant "a member another tip removed stays in the fold" src/seat.rs 'union.iter().filter(|k| !common.contains(*k) && survives(k)).cloned().collect();' 'union.iter().filter(|k| !common.contains(*k)).cloned().collect();'
plant "tips that differ in policy are folded" src/seat.rs 'if regimes.len() > 1 {' 'if false {'
plant "an authored head narrows a count" src/seat.rs 'if !heads.iter().any(|h| row(h).is_some_and(|r| authored_head(law, r))) {' 'if true {'
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
plant "the members at a head leave out the head"        src/seat.rs 'anc.iter().filter(|&&q| q == hi || past.has(q))' 'anc.iter().filter(|&&q| past.has(q))'
plant "a window's counted scope read as moderate"       src/window.rs 'cache.insert("all".into(), sets[0].clone());' 'cache.insert("all".into(), sets[1].clone());'
plant "the trust walk's index skips a key's own edges" src/trust.rs 'let lo = by_src.partition_point(|&x| edges[x].src < k);' 'let lo = by_src.partition_point(|&x| edges[x].src <= k);'
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
plant 'members at a head read unconcluded rows'          src/seat.rs 'anc.iter().filter(|&&q| q == hi || past.has(q)).map(|&q| g.row(q))' '(0..g.len()).filter(|&q| q == hi || past.has(q)).map(|q| g.row(q))'
plant 'the members cache ignores the scope'              src/seat.rs 'let key = (hs, obj.clone(), String::from(scope));' 'let key = (hs, obj.clone(), String::new());'
plant 'the members cache ignores a head'                 src/seat.rs 'hs.dedup();' 'hs.dedup(); hs.truncate(1);'
plant 'a weighted sum wraps'                             src/seat.rs 'let sum: u128 = yes().map(|k| weight(k) as u128).sum();' 'let sum: u128 = yes().map(&weight).fold(0u64, |a, x| a.wrapping_add(x)) as u128;'
plant 'a ranked count answered as a count'               src/seat.rs 'if matches!(pol, Some(Policy::Ranked)) {' 'if false {'
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
plant_run "a conformance run that never reports"          tests/trust.rs 'report("trust walk, TrustSet.lean worked world", n, 0);' 'let _ = ("trust walk, TrustSet.lean worked world", n, 0);'
if [ "$n" -eq 1 ]; then
  echo "ciris-kernel plants: $caught of $total caught"
else
  echo "ciris-kernel plants: $caught of $total caught (shard $k of $n; $seen plants in all)"
fi
[ $total -gt 0 ] && [ $caught -eq $total ]
