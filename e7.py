def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, s.count(a), a)
        s = s.replace(a, b)
    open(p, 'w').write(s)

# ---- the reference
p = 'models/causal_kernel/conferral_end.py'
s = open(p).read()
s = s.replace(', sub=True', '').replace('sub=True, ', '')
assert 'sub=True' not in s
open(p, 'w').write(s)
edit(p, [
('''                  act, from before this change), `sub` true for a deputy edge, `via` the deputy edge a deputy's
                  act is under (a deputy edge with a `via` is an onward hop: a deputy deputizing),
                  `sub_delegation` true on a deputy edge that may be passed on
''','''                  act, from before this change), `via` the deputy edge a deputy's act is under,
                  `sub_delegation` true on a deputy edge that may be passed on. Nothing marks a row as a
                  deputy edge: an act is one exactly when another act's `via` names it, and an edge that
                  itself has a `via` is an onward hop (a deputy deputizing)
'''),
('''    E6.depth             an act more than `deputy_depth` deputy edges from the seat (its `via` chain, and itself
                         if it is a deputy edge): not counted
    E6.no_sub            an onward hop (a deputy edge that has a `via`) under an edge that does not carry
                         `sub_delegation`: not counted. The first hop, an edge of the grantee's own, needs none
    E6.upstream          a deputy's act whose deputy edge does not count (or is not in force)
''','''    E6.depth             an act more than `deputy_depth` `via` hops from the grantee's own edge: not counted
    E6.no_sub            an act whose deputy edge is an onward hop (the edge itself has a `via`) under an edge
                         that does not carry `sub_delegation`: not counted. Read from the rows' `via` alone: the
                         row above the act's edge either carries it or does not. The first hop, an edge of
                         the grantee's own, needs none. The onward row itself, judged as an act, is its
                         signer's own act one hop higher and counts there; it confers nothing
    E6.upstream          a deputy's act whose deputy edge does not count (or is not in force)
'''),
('''    def depth(x):
        """The deputy edges from the seat to `x`: its `via` chain, and itself if it is a deputy edge."""
        n = 1 if by[x].get("sub") else 0
        while by[x].get("via"):''','''    def depth(x):
        """The `via` hops from `x` up to the grantee's own edge."""
        n = 0
        while by[x].get("via"):'''),
('''            elif r.get("via") and r.get("sub") and not by[r["via"]].get("sub_delegation"):
''','''            elif r.get("via") and by[r["via"]].get("via") and not by[by[r["via"]]["via"]].get("sub_delegation"):
'''),
('''    ("deputy_chain_no_sub", "the grantee's edge to C carries no sub-delegation: C's own act counts, C's onward "
     "edge does not, and C2's act under it does not",
     [H0] + CHAIN2(False), {}, {"s1": (T, T, "no_end"), "c1": (T, T, "no_end"), "s2": (F, F, "E6.no_sub"),
                                "c2": (F, F, "E6.upstream")}),
    ("deputy_chain_of_six", "six edges, each carrying sub-delegation: the fifth deputy's act counts; the sixth "
     "edge does not, nor the sixth deputy's act",
     [H0] + CHAIN6, {},
     dict({"s%d" % k: (T, T, "no_end") for k in range(1, 6)},
          c5=(T, T, "no_end"), s6=(F, F, "E6.depth"), c6=(F, F, "E6.depth"))),
    ("deputy_chain_depth_one", "the cap is a parameter of the call: at depth 1 the onward edge does not count, "
     "sub-delegation or not",
     [H0] + CHAIN2(True), {"deputy_depth": 1},
     {"s1": (T, T, "no_end"), "c1": (T, T, "no_end"), "s2": (F, F, "E6.depth"), "c2": (F, F, "E6.depth")}),
''','''    ("deputy_chain_no_sub", "the grantee's edge s1 to C carries no sub-delegation. C's row s2 is a row like "
     "any act of C's, with `via` s1, and nothing marks it as an edge; C2's act c2 has `via` s2. C's own acts "
     "c1 and s2 count, one hop under s1. c2 does not: the row it stands on is an onward hop, and the edge "
     "above that carries no sub-delegation. The gate is read from the `via` of the rows, so no presentation "
     "of s2 passes it",
     [H0] + CHAIN2(False), {}, {"s1": (T, T, "no_end"), "c1": (T, T, "no_end"), "s2": (T, T, "no_end"),
                                "c2": (F, F, "E6.no_sub")}),
    ("deputy_chain_no_sub_at_the_second_edge", "three edges: s1 carries sub-delegation and s2, under it, does "
     "not. C2's act c2 under s2 counts (s2 is an onward hop under s1, which carries it). C2's row s3 is C2's "
     "own act under s2 and counts as that. C3's act c3 under s3 does not count: s3 is an onward hop under "
     "s2. An act under c3 falls with it",
     [H0, act("s1", "H0", sub_delegation=True), act("s2", "H0", ["s1"], signer="C", via="s1"),
      act("c2", "H0", ["s2"], signer="C2", via="s2"), act("s3", "H0", ["s2"], signer="C2", via="s2"),
      act("c3", "H0", ["s3"], signer="C3", via="s3"), act("c4", "H0", ["c3"], signer="C4", via="c3")], {},
     {"s1": (T, T, "no_end"), "s2": (T, T, "no_end"), "c2": (T, T, "no_end"), "s3": (T, T, "no_end"),
      "c3": (F, F, "E6.no_sub"), "c4": (F, F, "E6.no_sub")}),
    ("deputy_chain_of_six", "six edges, each carrying sub-delegation: the fifth deputy's act counts, five hops "
     "from the grantee's edge, and so does its row s6, also five hops; the sixth deputy's act, six hops, "
     "does not",
     [H0] + CHAIN6, {},
     dict({"s%d" % k: (T, T, "no_end") for k in range(1, 7)}, c5=(T, T, "no_end"), c6=(F, F, "E6.depth"))),
    ("deputy_chain_depth_one", "the cap is a parameter of the call: at depth 1 a deputy's deputy does not "
     "count, sub-delegation or not; the deputy's own rows do",
     [H0] + CHAIN2(True), {"deputy_depth": 1},
     {"s1": (T, T, "no_end"), "c1": (T, T, "no_end"), "s2": (T, T, "no_end"), "c2": (F, F, "E6.depth")}),
'''),
('''    if r.get("sub"):
        bits.append("deputy_edge")
    if r.get("sub_delegation"):''','''    if edge:
        bits.append("deputy_edge")
    if r.get("sub_delegation"):'''),
('''def _row_text(r):
    """One row in a compact form for the case table: id:kind:signer, then head=, of=, target=, via=, lifts, names=."""''',
 '''def _row_text(r, edge=False):
    """One row in a compact form for the case table: id:kind:signer, then head=, of=, target=, via=, lifts, names=.
    `edge`: another act's `via` names it (it is a deputy edge by the rows, not by a mark)."""'''),
('''        rt = " | ".join(_row_text(r) for r in rows)''',
 '''        rt = " | ".join(_row_text(r, any(q.get("via") == r["id"] for q in rows)) for r in rows)'''),
])

# ---- the crate
edit('crates/ciris-kernel/src/conferral.rs', [
('''//! * A deputy hangs from an act of the grantee, its deputy edge ([`ConferralRow::via`]). The grantee's own
//!   edge needs nothing more. An onward hop, a deputy's own deputy edge, counts only under an edge that
//!   carries sub-delegation ([`ConferralRow::sub_delegation`]), and no act counts more than
//!   [`Standing::deputy_depth`] edges from the seat. A deputy ends with the seat: the end reaches the edge,
//!   and the edge passes it down.
''','''//! * A deputy hangs from an act of the grantee, its deputy edge ([`ConferralRow::via`]). Nothing marks a row
//!   as an edge: an act is one exactly when another act's `via` names it, and an edge that itself has a
//!   `via` is an onward hop, a deputy deputizing. The grantee's own edge needs nothing more. An act whose edge
//!   is an onward hop counts only if the edge above that one carries sub-delegation
//!   ([`ConferralRow::sub_delegation`]), and no act counts more than [`Standing::deputy_depth`] `via` hops
//!   from the grantee's edge. Both are read from the rows' `via`, so no presentation of the onward row passes
//!   them. A deputy ends with the seat: the end reaches the edge, and the edge passes it down.
'''),
('''    /// The act is a deputy edge: it deputizes another key. One that also has a [`via`](Self::via) is an onward
    /// hop, a deputy deputizing.
    fn deputy_edge(&self) -> bool {
        false
    }
    /// On a deputy edge: the deputy may deputize onward. An onward hop under an edge without it does not count.
''','''    /// On a deputy edge: the deputy may deputize onward. An act two hops below an edge without it does not
    /// count. A fact the edge row states; it is read only when a row under a row under this one is judged.
'''),
('''    /// The most deputy edges an act may be from the seat (the text's cap is [`DEPUTY_DEPTH`]). An act further
    /// down does not count; at 0 no deputy edge counts.
''','''    /// The most `via` hops an act may be from the grantee's own edge (the text's cap is [`DEPUTY_DEPTH`]). An
    /// act further down does not count; at 0 no deputy's act counts.
'''),
('''/// The text's cap on a chain of deputies: at most this many deputy edges from the seat.''',
 '''/// The text's cap on a chain of deputies: at most this many `via` hops from the grantee's own edge.'''),
('''    /// E6: an act more than [`Standing::deputy_depth`] deputy edges from the seat. Not counted.
    Depth,
    /// E6: an onward hop under an edge that does not carry sub-delegation. Not counted.
    NoSub,''','''    /// E6: an act more than [`Standing::deputy_depth`] `via` hops from the grantee's own edge. Not counted.
    Depth,
    /// E6: an act whose deputy edge is an onward hop under an edge that does not carry sub-delegation. Not
    /// counted.
    NoSub,'''),
('''    // The deputy edges from the seat to `x`: its `via` chain, and itself if it is a deputy edge. The walk
    // stops one past the cap, or past the rows (a cycle of names): the count is then already over the cap, or
    // the cycle is left to `judge`. An edge that is not held is the row to fetch.
    fn edges(&self, x: &R) -> Result<usize, R::Id> {
        let mut n = usize::from(x.deputy_edge());
''','''    // The `via` hops from `x` up to the grantee's own edge. The walk stops one past the cap, or past the rows
    // (a cycle of names): the count is then already over the cap, or the cycle is left to `judge`. An edge
    // that is not held is the row to fetch.
    fn edges(&self, x: &R) -> Result<usize, R::Id> {
        let mut n = 0;
'''),
('''            if let (Some(u), true) = (up, x.deputy_edge()) {
                if !u.sub_delegation() {
                    return Ok((false, false, if c { Rule::NoSub } else { rule }));
                }
            }
''','''            // the edge `x` is under is an onward hop where it has a `via` itself: the edge above must carry
            // sub-delegation. Read from the rows, whatever the onward row is presented as
            if let Some(above) = up.and_then(|u| self.edge(u)) {
                if !above.sub_delegation() {
                    return Ok((false, false, if c { Rule::NoSub } else { rule }));
                }
            }
'''),
])
edit('crates/ciris-kernel/tests/conferral_end.rs', [
('''    deputy_edge: bool,
    sub_delegation: bool,
}''','''    sub_delegation: bool,
}'''),
('''    fn deputy_edge(&self) -> bool {
        self.deputy_edge
    }
''',''),
('''        deputy_edge: j.get("sub").is_some_and(|v| v.b()),
''',''),
('''        deputy_edge: false,
''',''),
])
edit('tools/kernel_crate_plants.sh', [
('''plant "an onward hop needs no sub-delegation"          src/conferral.rs 'if !u.sub_delegation() {' 'if false {\'''',
 '''plant "an onward hop passes as its signer's plain act" src/conferral.rs 'if let Some(above) = up.and_then(|u| self.edge(u)) {' 'if let Some(above) = up.and_then(|u| self.edge(u)).filter(|_| false) {\''''),
('''plant "a deputy edge is not among its own edges"       src/conferral.rs 'let mut n = usize::from(x.deputy_edge());' 'let mut n = 0;\'''',
 '''plant "sub-delegation asked of the act's own edge"     src/conferral.rs 'if let Some(above) = up.and_then(|u| self.edge(u)) {' 'if let Some(above) = up {\''''),
])
