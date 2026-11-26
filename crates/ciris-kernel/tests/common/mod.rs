//! Shared by the differential tests: a JSON reader (the crate has no dependencies, and neither do its tests),
//! and a row that reads its fields the way the Python models read their dicts.
#![allow(dead_code)]

pub mod eager;

use ciris_kernel::cut::CutSpec;
use ciris_kernel::head::{Duty, Entry, Kind};
use ciris_kernel::key_end::{EndRule, KeyEndRow, Record};
use ciris_kernel::seat::{Conf, Obj, Reference, SeatKind, SeatRow};
use ciris_kernel::window::{WinKind, WindowRow};
use ciris_kernel::Row;
use std::collections::{BTreeMap, BTreeSet};

// ---- JSON --------------------------------------------------------------------------------------------------
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub enum J {
    Null,
    Bool(bool),
    Int(i64),
    Str(String),
    Arr(Vec<J>),
    Obj(BTreeMap<String, J>),
}

impl J {
    pub fn get(&self, k: &str) -> Option<&J> {
        match self {
            J::Obj(m) => m.get(k),
            _ => None,
        }
    }
    pub fn at(&self, k: &str) -> &J {
        self.get(k).unwrap_or_else(|| panic!("no field {k}"))
    }
    pub fn arr(&self) -> &[J] {
        match self {
            J::Arr(v) => v,
            J::Null => &[],
            _ => panic!("not an array: {self:?}"),
        }
    }
    pub fn obj(&self) -> &BTreeMap<String, J> {
        match self {
            J::Obj(m) => m,
            _ => panic!("not an object"),
        }
    }
    pub fn s(&self) -> &str {
        match self {
            J::Str(s) => s,
            _ => panic!("not a string: {self:?}"),
        }
    }
    pub fn i(&self) -> i64 {
        match self {
            J::Int(i) => *i,
            _ => panic!("not an int: {self:?}"),
        }
    }
    pub fn b(&self) -> bool {
        match self {
            J::Bool(b) => *b,
            _ => panic!("not a bool: {self:?}"),
        }
    }
    pub fn is_null(&self) -> bool {
        matches!(self, J::Null)
    }
    pub fn opt_s(&self) -> Option<String> {
        match self {
            J::Null => None,
            J::Str(s) => Some(s.clone()),
            _ => panic!("not a string: {self:?}"),
        }
    }
    /// A string or a list of strings, as a list.
    pub fn strs(&self) -> Vec<String> {
        match self {
            J::Null => vec![],
            J::Str(s) => vec![s.clone()],
            J::Arr(v) => v.iter().map(|x| x.s().to_string()).collect(),
            _ => panic!("not strings: {self:?}"),
        }
    }
    pub fn str_set(&self) -> BTreeSet<String> {
        self.strs().into_iter().collect()
    }
}

pub fn parse(text: &str) -> J {
    let b = text.as_bytes();
    let mut i = 0;
    let v = value(b, &mut i);
    ws(b, &mut i);
    assert_eq!(i, b.len(), "trailing data");
    v
}

fn ws(b: &[u8], i: &mut usize) {
    while *i < b.len() && (b[*i] as char).is_ascii_whitespace() {
        *i += 1;
    }
}

fn value(b: &[u8], i: &mut usize) -> J {
    ws(b, i);
    match b[*i] {
        b'{' => {
            *i += 1;
            let mut m = BTreeMap::new();
            ws(b, i);
            if b[*i] == b'}' {
                *i += 1;
                return J::Obj(m);
            }
            loop {
                ws(b, i);
                let k = match value(b, i) {
                    J::Str(s) => s,
                    _ => panic!("key"),
                };
                ws(b, i);
                assert_eq!(b[*i], b':');
                *i += 1;
                let v = value(b, i);
                m.insert(k, v);
                ws(b, i);
                match b[*i] {
                    b',' => *i += 1,
                    b'}' => {
                        *i += 1;
                        return J::Obj(m);
                    }
                    c => panic!("object: {}", c as char),
                }
            }
        }
        b'[' => {
            *i += 1;
            let mut v = Vec::new();
            ws(b, i);
            if b[*i] == b']' {
                *i += 1;
                return J::Arr(v);
            }
            loop {
                v.push(value(b, i));
                ws(b, i);
                match b[*i] {
                    b',' => *i += 1,
                    b']' => {
                        *i += 1;
                        return J::Arr(v);
                    }
                    c => panic!("array: {}", c as char),
                }
            }
        }
        b'"' => {
            *i += 1;
            let mut s = String::new();
            loop {
                let c = b[*i];
                *i += 1;
                match c {
                    b'"' => return J::Str(s),
                    b'\\' => {
                        let e = b[*i];
                        *i += 1;
                        match e {
                            b'n' => s.push('\n'),
                            b't' => s.push('\t'),
                            b'"' => s.push('"'),
                            b'\\' => s.push('\\'),
                            b'/' => s.push('/'),
                            b'u' => {
                                let h = std::str::from_utf8(&b[*i..*i + 4]).unwrap();
                                *i += 4;
                                s.push(char::from_u32(u32::from_str_radix(h, 16).unwrap()).unwrap_or('?'));
                            }
                            _ => panic!("escape"),
                        }
                    }
                    _ => {
                        // copy one UTF-8 scalar
                        let start = *i - 1;
                        let mut end = *i;
                        while end < b.len() && (b[end] & 0xC0) == 0x80 {
                            end += 1;
                        }
                        s.push_str(std::str::from_utf8(&b[start..end]).unwrap());
                        *i = end;
                    }
                }
            }
        }
        b't' => {
            *i += 4;
            J::Bool(true)
        }
        b'f' => {
            *i += 5;
            J::Bool(false)
        }
        b'n' => {
            *i += 4;
            J::Null
        }
        _ => {
            let start = *i;
            while *i < b.len() && (b[*i] == b'-' || b[*i].is_ascii_digit()) {
                *i += 1;
            }
            J::Int(std::str::from_utf8(&b[start..*i]).unwrap().parse().unwrap())
        }
    }
}

/// An entry of `purge.json` (`purge.py`'s row dicts) as a `head::Entry`.
pub fn head_entry(j: &J) -> Entry<String, String, i64> {
    let kind = match j.at("kind").s() {
        "seat" => Kind::Seat,
        "act" => Kind::Act,
        "ack" => Kind::Ack,
        "rack" => Kind::ReaderAck,
        "cut" => Kind::Cut,
        "open" => Kind::Open,
        "answer" => Kind::Answer,
        _ => Kind::Other,
    };
    let mut e = Entry::new(j.at("id").s().to_string(), kind, j.at("signer").s().to_string(), j.at("names").strs());
    e.head = j.get("head").and_then(|h| h.opt_s());
    e.of = j.get("of").and_then(|h| h.opt_s());
    e.members = j.get("members").map(|m| m.strs()).unwrap_or_default();
    e.q = j.get("q").map_or(0, |q| q.i() as usize);
    e.sigs = j.get("sigs").map(|m| m.strs()).unwrap_or_default();
    e.length = j.get("length").map(|x| x.i());
    e.receipt = j.get("receipt").map(|x| x.i());
    e.delete = j.get("delete").is_some_and(|x| x.b());
    e.duty = j
        .get("duty")
        .map(|d| d.strs())
        .unwrap_or_default()
        .iter()
        .map(|d| match d.as_str() {
            "accountability" => Duty::Accountability,
            "pinned" => Duty::Pinned,
            "hold" => Duty::Hold,
            "floor" => Duty::Floor,
            "owed" => Duty::Owed,
            "preserve" => Duty::Preserve,
            x => panic!("duty {x}"),
        })
        .collect();
    e
}

pub fn fixture(name: &str) -> J {
    let path = format!("{}/tests/fixtures/{}", env!("CARGO_MANIFEST_DIR"), name);
    parse(&std::fs::read_to_string(&path).unwrap_or_else(|e| panic!("{path}: {e}")))
}

/// One line per conformance run, read by check.sh (`tools/kernel_conformance.sh`). The line is one write under
/// the stderr lock, and starts on a line of its own: libtest's "test ... " prefix, written to stdout without a
/// newline, can then neither split it nor stand in front of it.
pub fn report(name: &str, cases: usize, bad: usize) {
    use std::io::Write;
    let line = format!("\nconformance {name}: {cases} cases, {bad} disagreements\n");
    let _ = std::io::stderr().lock().write_all(line.as_bytes());
}

// ---- a row read as the Python models read their dicts -----------------------------------------------------
#[derive(Clone, Debug)]
pub struct TRow {
    pub m: BTreeMap<String, J>,
    pub id: String,
    pub names: Vec<String>,
    pub signer: String,
    pub kind: String,
    pub to: Vec<String>,
    pub cosigners: Vec<String>,
    pub subjects: Vec<String>,
    pub head: Vec<String>,
    pub options: Vec<String>,
    pub ranking: Vec<String>,
    pub duties: Vec<String>,
    /// A founding record's `duty_holders`: (duty, keys) pairs.
    pub duty_holders: Vec<(String, Vec<String>)>,
    pub sigs: Vec<String>,
    pub obj: Option<Obj<String, String>>,
    pub over: Option<Obj<String, String>>,
    pub room: Option<Obj<String, String>>,
    pub scope: Option<String>,
    pub policy: Option<String>,
    pub counted: Option<String>,
    pub of: Option<String>,
    pub target: Option<String>,
    pub content: Option<String>,
    pub under: Option<String>,
    pub window: Option<String>,
    pub says: Option<String>,
    pub receipt: Option<String>,
    pub end: EndRule,
}

impl PartialEq for TRow {
    fn eq(&self, o: &Self) -> bool {
        self.m == o.m
    }
}

fn opt(m: &BTreeMap<String, J>, k: &str) -> Option<String> {
    match m.get(k) {
        None | Some(J::Null) => None,
        Some(J::Str(s)) => Some(s.clone()),
        Some(J::Int(i)) => Some(i.to_string()),
        Some(x) => panic!("field {k}: {x:?}"),
    }
}

fn strs(m: &BTreeMap<String, J>, k: &str) -> Vec<String> {
    m.get(k).map(|x| x.strs()).unwrap_or_default()
}

impl TRow {
    /// `refs`: what each reference of the fixture stands for in the model's own names. Whether an object is a
    /// row or a key is read from the form of its reference alone (`Obj::from_reference`).
    pub fn new(j: &J, refs: &BTreeMap<String, String>) -> TRow {
        let m = j.obj().clone();
        let o = |k: &str| -> Option<Obj<String, String>> {
            let v = m.get(k)?;
            match v {
                J::Null => None,
                J::Arr(a) => {
                    let hex = a[1].s();
                    let bytes: Vec<u8> =
                        (0..hex.len() / 2).map(|i| u8::from_str_radix(&hex[2 * i..2 * i + 2], 16).unwrap()).collect();
                    let r = Reference::Digest { alg: a[0].i(), digest: &bytes };
                    let name = refs[&format!("{}|{}", a[0].i(), hex)].clone();
                    Some(
                        Obj::from_reference(r, |_| name.clone(), |t| t.to_string())
                            .expect("a reference of a known form"),
                    )
                }
                J::Str(t) => Some(
                    Obj::from_reference(Reference::Text(t), |_| String::new(), |t| refs[t].clone())
                        .unwrap_or_else(|| panic!("{k}: {t:?} is not a reference")),
                ),
                J::Bool(_) => None,
                x => panic!("{k}: {x:?}"),
            }
        };
        TRow {
            id: m["id"].s().to_string(),
            names: strs(&m, "names"),
            signer: opt(&m, "signer").unwrap_or_default(),
            kind: opt(&m, "kind").unwrap_or_default(),
            to: strs(&m, "to"),
            cosigners: strs(&m, "cosigners"),
            subjects: strs(&m, "subjects"),
            head: strs(&m, "head"),
            options: strs(&m, "options"),
            ranking: strs(&m, "ranking"),
            duties: strs(&m, "duties"),
            duty_holders: m
                .get("duty_holders")
                .map(|x| x.arr().iter().map(|e| (e.arr()[0].s().to_string(), e.arr()[1].strs())).collect())
                .unwrap_or_default(),
            sigs: strs(&m, "sigs"),
            obj: o("obj"),
            over: o("over"),
            room: o("room"),
            scope: opt(&m, "scope"),
            policy: opt(&m, "policy"),
            counted: opt(&m, "counted"),
            of: opt(&m, "of"),
            target: if m.get("target").is_some_and(|t| matches!(t, J::Str(_))) { opt(&m, "target") } else { None },
            content: opt(&m, "content"),
            under: opt(&m, "under"),
            window: opt(&m, "window"),
            says: if m.get("says").is_some_and(|t| matches!(t, J::Str(_))) { opt(&m, "says") } else { None },
            receipt: opt(&m, "receipt"),
            end: EndRule::Optional,
            m,
        }
    }
    pub fn f(&self, k: &str) -> Option<&J> {
        match self.m.get(k) {
            None | Some(J::Null) => None,
            x => x,
        }
    }
    pub fn fs(&self, k: &str) -> Option<&str> {
        self.f(k).map(|x| x.s())
    }
    pub fn fi(&self, k: &str) -> Option<i64> {
        self.f(k).map(|x| x.i())
    }
}

pub fn rows_of(js: &[J]) -> Vec<TRow> {
    rows_with_refs(js, &BTreeMap::new())
}

pub fn rows_with_refs(js: &[J], refs: &BTreeMap<String, String>) -> Vec<TRow> {
    js.iter().map(|j| TRow::new(j, refs)).collect()
}

impl Row for TRow {
    type Id = String;
    type Key = String;
    fn id(&self) -> &String {
        &self.id
    }
    fn names(&self) -> &[String] {
        &self.names
    }
    fn signer(&self) -> &String {
        &self.signer
    }
}

impl SeatRow for TRow {
    type Word = String;
    fn seat_kind(&self) -> SeatKind {
        match self.kind.as_str() {
            "offer" => SeatKind::Offer,
            "accept" => SeatKind::Accept,
            "withdraw" => SeatKind::Withdraw,
            "unseat" => SeatKind::Unseat,
            "cosign" => SeatKind::Cosign,
            "ballot" => SeatKind::Ballot,
            "ack" => SeatKind::Ack,
            // an objection in a window is presented as a voice for the row it answers (seat::lift_voices)
            "answer" if self.says.as_deref() == Some("object") => SeatKind::Cosign,
            _ => SeatKind::Other,
        }
    }
    fn to(&self) -> &[String] {
        &self.to
    }
    fn scope(&self) -> Option<&String> {
        self.scope.as_ref()
    }
    fn obj(&self) -> Option<Obj<String, String>> {
        self.obj.clone()
    }
    fn conf(&self) -> Option<Conf> {
        match self.fs("conf") {
            Some("self") => Some(Conf::Own),
            Some("seat") => Some(Conf::Seat),
            Some("group") => Some(Conf::Group),
            _ => None,
        }
    }
    fn under(&self) -> Option<&String> {
        self.under.as_ref()
    }
    fn cosigners(&self) -> &[String] {
        &self.cosigners
    }
    fn subjects(&self) -> &[String] {
        &self.subjects
    }
    fn consent_one(&self) -> bool {
        self.fs("consent") == Some("one")
    }
    fn sub(&self) -> bool {
        self.f("sub").is_some_and(|x| x.b())
    }
    fn head(&self) -> &[String] {
        &self.head
    }
    fn policy(&self) -> Option<&String> {
        self.policy.as_ref()
    }
    fn counted(&self) -> Option<&String> {
        self.counted.as_ref()
    }
    fn over(&self) -> Option<Obj<String, String>> {
        self.over.clone()
    }
    fn need(&self) -> Option<usize> {
        self.fi("need").map(|n| n as usize)
    }
    fn of(&self) -> Option<&String> {
        self.of.as_ref()
    }
    fn target(&self) -> Option<&String> {
        self.target.as_ref()
    }
    fn content(&self) -> Option<&String> {
        self.content.as_ref()
    }
    fn duties(&self) -> &[String] {
        &self.duties
    }
    fn duty_holders(&self) -> &[(String, Vec<String>)] {
        &self.duty_holders
    }
    fn options(&self) -> &[String] {
        &self.options
    }
    fn ranking(&self) -> &[String] {
        &self.ranking
    }
    fn room(&self) -> Option<Obj<String, String>> {
        self.room.clone()
    }
    fn private_room(&self) -> bool {
        self.fs("membership") == Some("private")
    }
}

impl WindowRow for TRow {
    type T = i64;
    fn win_kind(&self) -> Option<WinKind> {
        match self.kind.as_str() {
            "open" => Some(WinKind::Open),
            // an act that names a window opens it (a moderator's lone removal of an agent's key)
            "unseat" if self.window.is_some() => Some(WinKind::Open),
            "answer" => Some(WinKind::Answer),
            "receipt" => Some(WinKind::Receipt),
            "landing" => Some(WinKind::Landing),
            _ => None,
        }
    }
    fn window(&self) -> Option<&String> {
        self.window.as_ref()
    }
    fn target_key(&self) -> Option<&String> {
        if self.kind == "open" {
            self.target.as_ref()
        } else {
            None
        }
    }
    fn says(&self) -> Option<&String> {
        self.says.as_ref()
    }
    fn receipt(&self) -> Option<&String> {
        self.receipt.as_ref()
    }
    fn at(&self) -> Option<i64> {
        self.fi("at")
    }
}

impl KeyEndRow for TRow {
    type T = i64;
    fn record(&self) -> Option<Record<'_, String, i64>> {
        if self.kind != "rec" {
            return None;
        }
        Some(Record {
            key: match self.m.get("key") {
                Some(J::Str(_)) => self.m_key(),
                _ => &self.signer,
            },
            from: self.fi("vf").unwrap(),
            until: self.fi("vu"),
            succ_of: self.succ_of(),
            at_old: self.fi("at_old"),
            sigs: &self.sigs,
            end: self.end,
        })
    }
    fn statement(&self) -> Option<(i64, &String)> {
        match self.kind.as_str() {
            "att" | "edge" => Some((self.fi("at").unwrap(), self.cover())),
            _ => None,
        }
    }
    fn revocation(&self) -> Option<(&String, i64)> {
        if self.kind == "revoke" {
            Some((self.m_key(), self.fi("ra").unwrap()))
        } else {
            None
        }
    }
}

impl TRow {
    fn m_key(&self) -> &String {
        match self.m.get("key") {
            Some(J::Str(s)) => s,
            _ => panic!("key"),
        }
    }
    fn succ_of(&self) -> Option<&String> {
        match self.m.get("succ_of") {
            Some(J::Str(s)) => Some(s),
            _ => None,
        }
    }
    fn cover(&self) -> &String {
        match self.m.get("cover") {
            Some(J::Str(s)) => s,
            _ => panic!("cover"),
        }
    }
}

/// The cut as `cut.py` reads a row's dict fields.
pub struct DictCut;

impl CutSpec<TRow> for DictCut {
    type Slot = J;
    type Say = J;
    fn key_slot(&self, k: &String) -> J {
        J::Arr(vec![J::Str("key".into()), J::Str(k.clone())])
    }
    fn on_slots(&self, r: &TRow) -> BTreeSet<J> {
        let mut s = BTreeSet::new();
        s.insert(self.key_slot(&r.signer));
        if let Some(x) = r.f("slot") {
            s.insert(x.clone());
        }
        if let Some(on) = r.f("on") {
            s.extend(on.arr().iter().cloned());
        }
        s
    }
    fn cuts_of(&self, r: &TRow) -> BTreeSet<J> {
        let mut s: BTreeSet<J> = r.f("cuts").map(|c| c.arr().iter().cloned().collect()).unwrap_or_default();
        if let Some(k) = r.fs("removes") {
            s.insert(self.key_slot(&k.to_string()));
        }
        if r.kind == "decider" {
            if let Some(x) = r.f("slot") {
                s.insert(x.clone());
            }
        }
        s
    }
    fn says(&self, r: &TRow) -> J {
        if let Some(x) = r.m.get("says") {
            return x.clone();
        }
        if let Some(x) = r.m.get("picks") {
            return x.clone();
        }
        if r.f("removes").is_some() {
            return J::Str("out".into());
        }
        J::Str(r.id.clone())
    }
    fn need(&self, r: &TRow) -> usize {
        r.fi("need").map_or(1, |n| n as usize)
    }
    fn rejects(&self, r: &TRow) -> Vec<String> {
        r.f("rejects").map(|x| x.strs()).unwrap_or_default()
    }
    fn is_voice_for(&self, cosign: &TRow, cut: &TRow) -> bool {
        cosign.kind == "cosign" && cosign.f("of") == cut.f("content")
    }
}

pub fn sorted_ids<'a>(it: impl IntoIterator<Item = &'a String>) -> Vec<String> {
    let mut v: Vec<String> = it.into_iter().cloned().collect();
    v.sort();
    v
}

// ---- the tables a fixture carries ---------------------------------------------------------------------
use ciris_kernel::seat::{Over, Policy, SeatLaw};
use ciris_kernel::window::{Base, Clause, How, WindowSpec};

pub fn law_of(j: &J) -> SeatLaw {
    let mut law = SeatLaw {
        duties: j.at("duties").strs(),
        final_scopes: j.at("final").strs(),
        roster_seats: j.at("roster_seats").strs(),
        depth: j.at("depth").i() as usize,
        ..Default::default()
    };
    for (k, v) in j.at("holds").obj() {
        law.holds.insert(k.clone(), v.strs());
    }
    for (k, v) in j.at("ends").obj() {
        law.ends.insert(k.clone(), v.strs());
    }
    for (k, v) in j.at("confers").obj() {
        let a = v.arr();
        let over = if a[1].s() == "same" { Over::Same } else { Over::Holder };
        law.confers.insert(k.clone(), (a[0].strs(), over));
    }
    for (k, v) in j.at("policy").obj() {
        let a = v.arr();
        let (num, den) = (a[1].i() as u64, a[2].i() as u64);
        let p = match a[0].s() {
            "atleast" => Policy::AtLeast(num, den),
            "strict" => Policy::Strict(num, den),
            "one" => Policy::One,
            "declared" => Policy::Declared,
            "ranked" => Policy::Ranked,
            "duty" if k == "duty_confer" => Policy::DutyConfer,
            "duty" if k == "duty_withdraw" => Policy::DutyWithdraw,
            "lift" => Policy::Lift,
            _ => Policy::NotACount,
        };
        law.policy.insert(k.clone(), p);
    }
    law
}

pub fn windows_of(j: &J) -> BTreeMap<String, WindowSpec<i64>> {
    let clauses = |a: &J| -> Vec<Clause> {
        a.arr()
            .iter()
            .map(|c| {
                let c = c.arr();
                Clause {
                    value: c[0].s().into(),
                    how: match &c[1] {
                        J::Str(h) if h == "one" => How::One,
                        J::Str(_) => How::Strict,
                        J::Arr(t) if t[0].s() == "atleast" => {
                            How::AtLeast(t[1].i() as u64, t[2].i() as u64, t[3].i() as u64)
                        }
                        J::Arr(t) if t[0].s() == "voted" => {
                            How::MoreOfVoted(t[1].i() as u64, t[2].i() as u64, t[3].i() as u64, t[4].s().into())
                        }
                        J::Arr(t) if t[3].i() > 0 => {
                            How::MoreAtLeast(t[1].i() as u64, t[2].i() as u64, t[3].i() as u64)
                        }
                        J::Arr(t) => How::More(t[1].i() as u64, t[2].i() as u64),
                        x => panic!("clause {x:?}"),
                    },
                    over: match c[2].s() {
                        "all" => Base::All,
                        "others" => Base::Others,
                        "opener" => Base::Opener,
                        s => Base::Scope(s.into()),
                    },
                    out: c[3].s().into(),
                }
            })
            .collect()
    };
    j.obj()
        .iter()
        .map(|(k, w)| {
            (
                k.clone(),
                WindowSpec {
                    counted: w.at("counted").s().into(),
                    concluder: w.at("concluder").s().into(),
                    opener: w.get("opener").and_then(|x| x.opt_s()),
                    opener_says: w.at("opener_says").opt_s(),
                    at_once: clauses(w.at("at_once")),
                    silent: w.at("silent").opt_s(),
                    at_close: clauses(w.at("at_close")),
                    default: w.at("default").s().into(),
                    target_votes: w.get("target_votes").is_some_and(|x| x.b()),
                    secs: w.at("secs").i(),
                },
            )
        })
        .collect()
}
