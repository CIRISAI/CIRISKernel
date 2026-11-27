p='crates/ciris-kernel/src/conferral.rs'
s=open(p).read()
def rep(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a)
    s=s.replace(a,b)
rep('''//! * An act that authorises a further row passes both down, each to its own (E6).
''','''//! * An act that authorises a further row passes both down, each to its own (E6).
//! * A deputy hangs from an act of the grantee, its deputy edge ([`ConferralRow::via`]). The grantee's own
//!   edge needs nothing more. An onward hop, a deputy's own deputy edge, counts only under an edge that
//!   carries sub-delegation ([`ConferralRow::sub_delegation`]), and no act counts more than
//!   [`Standing::deputy_depth`] edges from the seat. A deputy ends with the seat: the end reaches the edge,
//!   and the edge passes it down.
''')
rep('''    /// The deputy edge a deputy's act is under: itself an act of the grantee.
    fn via(&self) -> Option<&Self::Id> {
        None
    }
''','''    /// The deputy edge a deputy's act is under: itself an act of the grantee, or of a deputy above.
    fn via(&self) -> Option<&Self::Id> {
        None
    }
    /// The act is a deputy edge: it deputizes another key. One that also has a [`via`](Self::via) is an onward
    /// hop, a deputy deputizing.
    fn deputy_edge(&self) -> bool {
        false
    }
    /// On a deputy edge: the deputy may deputize onward. An onward hop under an edge without it does not count.
    fn sub_delegation(&self) -> bool {
        false
    }
''')
rep('''    pub reader_acks: &'a [I],
}''','''    pub reader_acks: &'a [I],
    /// The most deputy edges an act may be from the seat (the text's cap is [`DEPUTY_DEPTH`]). An act further
    /// down does not count; at 0 no deputy edge counts.
    pub deputy_depth: usize,
}

/// The text's cap on a chain of deputies: at most this many deputy edges from the seat.
pub const DEPUTY_DEPTH: usize = 5;''')
rep('''    /// E6: a deputy's act whose deputy edge does not count, or is not in force.
    Upstream,''','''    /// E6: an act more than [`Standing::deputy_depth`] deputy edges from the seat. Not counted.
    Depth,
    /// E6: an onward hop under an edge that does not carry sub-delegation. Not counted.
    NoSub,
    /// E6: a deputy's act whose deputy edge does not count, or is not in force.
    Upstream,''')
rep('''            Rule::Upstream => "E6.upstream",''','''            Rule::Depth => "E6.depth",
            Rule::NoSub => "E6.no_sub",
            Rule::Upstream => "E6.upstream",''')
rep('''            let (mut c, mut f, mut rule) = self.end_rule(x, void)?;
            // a deputy's act follows its deputy edge; a chain of edges longer than the rows is a cycle of names
            let up = x.via().and_then(|v| self.rows.iter().copied().find(|r| r.id() == v && r.kind() == Kind::Act));
            if let (Some(u), true) = (up, depth < self.rows.len()) {
''','''            let (mut c, mut f, mut rule) = self.end_rule(x, void)?;
            if self.edges(x)? > self.st.deputy_depth {
                return Ok((false, false, if c { Rule::Depth } else { rule }));
            }
            // a deputy's act follows its deputy edge; a chain of edges longer than the rows is a cycle of names
            let up = self.edge(x);
            if let (Some(u), true) = (up, x.deputy_edge()) {
                if !u.sub_delegation() {
                    return Ok((false, false, if c { Rule::NoSub } else { rule }));
                }
            }
            if let (Some(u), true) = (up, depth < self.rows.len()) {
''')
rep('''    fn judge(
        &self,''','''    // the deputy edge `x` is under, where it is held
    fn edge(&self, x: &R) -> Option<&'a R> {
        x.via().and_then(|v| self.rows.iter().copied().find(|r| r.id() == v && r.kind() == Kind::Act))
    }

    // The deputy edges from the seat to `x`: its `via` chain, and itself if it is a deputy edge. The walk
    // stops one past the cap, or past the rows (a cycle of names): the count is then already over the cap, or
    // the cycle is left to `judge`. An edge that is not held is the row to fetch.
    fn edges(&self, x: &R) -> Result<usize, R::Id> {
        let mut n = usize::from(x.deputy_edge());
        let mut at = x;
        while let Some(v) = at.via() {
            if n > self.st.deputy_depth || n > self.rows.len() {
                break;
            }
            at = self.edge(at).ok_or_else(|| v.clone())?;
            n += 1;
        }
        Ok(n)
    }

    fn judge(
        &self,''')
open(p,'w').write(s)

p='crates/ciris-kernel/tests/conferral_end.rs'
s=open(p).read()
rep('''    via: Option<String>,
    lifts: bool,
}''','''    via: Option<String>,
    lifts: bool,
    deputy_edge: bool,
    sub_delegation: bool,
}''')
rep('''    fn lifts(&self) -> bool {
        self.lifts
    }
''','''    fn lifts(&self) -> bool {
        self.lifts
    }
    fn deputy_edge(&self) -> bool {
        self.deputy_edge
    }
    fn sub_delegation(&self) -> bool {
        self.sub_delegation
    }
''')
rep('''        lifts: j.get("lifts").is_some_and(|v| v.b()),
''','''        lifts: j.get("lifts").is_some_and(|v| v.b()),
        deputy_edge: j.get("sub").is_some_and(|v| v.b()),
        sub_delegation: j.get("sub_delegation").is_some_and(|v| v.b()),
''')
rep('''        reader_acks: &acks,
    };''','''        reader_acks: &acks,
        deputy_depth: c.at("deputy_depth").i() as usize,
    };''')
rep('''        via: None,
        lifts: false,
    };''','''        via: None,
        lifts: false,
        deputy_edge: false,
        sub_delegation: false,
    };''')
rep('''who: Who::All, reader_acks: &[] };''','''who: Who::All, reader_acks: &[], deputy_depth: DEPUTY_DEPTH };''')
rep("use ciris_kernel::conferral::{answers, Answer,","use ciris_kernel::conferral::{answers, Answer, DEPUTY_DEPTH,")
open(p,'w').write(s)
