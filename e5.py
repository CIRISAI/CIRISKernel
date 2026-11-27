def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, s.count(a), a)
        s = s.replace(a, b)
    open(p, 'w').write(s)

edit('crates/ciris-kernel/src/standing.rs', [
('''/// The answer for every act, by the act's id.
pub type Answers<I, K> = BTreeMap<I, Answer<I, K>>;
''','''/// The answer for every act, by the act's id.
pub type Answers<I, K> = BTreeMap<I, Answer<I, K>>;

/// What [`answers`] returns: the answers, or why none is given.
pub type Outcome<I, K> = Result<Answers<I, K>, Refused<I>>;
'''),
(''') -> Result<Answers<R::Id, R::Key>, Refused<R::Id>> {''', ''') -> Outcome<R::Id, R::Key> {'''),
])
edit('tools/kernel_crate_plants.sh', [
('''plant "the member's own end adds tips beside a counted end"''',
'''plant "an onward hop needs no sub-delegation"          src/conferral.rs 'if !u.sub_delegation() {' 'if false {'
plant "the cap on a chain of deputies is not read"     src/conferral.rs 'if self.edges(x)? > self.st.deputy_depth {' 'if false {'
plant "a deputy edge is not among its own edges"       src/conferral.rs 'let mut n = usize::from(x.deputy_edge());' 'let mut n = 0;'
plant "in force under the grant alone"                 src/standing.rs 'in_force: g.in_force && u.in_force,' 'in_force: g.in_force,'
plant "counted under the binding alone"                src/standing.rs 'counted: g.counted && u.counted,' 'counted: u.counted,'
plant "an act naming the binding stands under it"      src/standing.rs 'Kind::Binding => return Ok(Err(Nobody::NamesBinding)),' 'Kind::Binding => return Ok(Ok(a)),'
plant "any key's acceptance is the owner's"            src/standing.rs 'if b.owner() != Some(a.signer()) {' 'if false {'
plant "a re-binding does not end the binding before it" src/standing.rs 'Kind::Binding if row.on() == Some(bid) => (conferral::Kind::End, Some(bid)),' 'Kind::Binding if row.on() == Some(bid) => (conferral::Kind::Other, None),'
plant "the member's own end adds tips beside a counted end"'''),
])
