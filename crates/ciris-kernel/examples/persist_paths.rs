//! The kernel functions persist calls, at roster and row sizes 3, 16, 128, 1,024 and 16,384, with no
//! dependency (the crate has none, and CI runs `--offline`). The rows are shaped as persist's adapter
//! presents them (`src/kernel/` in CIRISPersist: a 32-byte row id, a `String` key, the seat fields).
//!
//!     cargo run --release --example persist_paths [filter | =name] [--sizes 3,16,128] [--list]
//!
//! A filter runs the benches whose names contain it; `=name` runs that one bench alone, and only its own
//! section's setup (`tools/kernel_bench_ab.py` runs each bench so, in a process of its own).
//!
//! Prints one TSV line per bench: name, size, median nanoseconds per call, samples, iterations per sample,
//! and allocations per call (a counting global allocator). A bench whose next size, read quadratically from
//! its last, would take over two seconds a call is printed as skipped.
//! Every bench computes its answer once before timing and checks the timed calls give the same answer, so
//! a fast wrong path cannot pass unnoticed here either.
#[path = "../tests/common/dag.rs"]
mod dag;

use ciris_kernel::cut::CutSpec;
use ciris_kernel::graph::Graph;
use ciris_kernel::head::{self, Entry, Kind, Reading};
use ciris_kernel::held::{Held, HeldSpec, Rules};
use ciris_kernel::key_end::{self, EndRule, KeyEndRow, Record};
use ciris_kernel::layers::{self, Concluded, Past};
use ciris_kernel::line;
use ciris_kernel::seat::{
    self, group_count, Conf, GroupCount, Obj, Policy, SeatKind, SeatLaw, SeatLine, SeatRow, Seats,
};
use ciris_kernel::trust::{self, Accepts};
use ciris_kernel::window::{self, Base, Clause, How, WinKind, WindowRow, WindowSpec};
use ciris_kernel::{derived, Row};
use std::collections::{BTreeMap, BTreeSet};
use std::hint::black_box;
use std::time::Instant;

type Id = [u8; 32];

/// Counts allocations, so a bench reports allocations per call beside its time.
struct Counting;
static ALLOCS: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
unsafe impl std::alloc::GlobalAlloc for Counting {
    unsafe fn alloc(&self, l: std::alloc::Layout) -> *mut u8 {
        ALLOCS.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
        unsafe { std::alloc::System.alloc(l) }
    }
    unsafe fn dealloc(&self, p: *mut u8, l: std::alloc::Layout) {
        unsafe { std::alloc::System.dealloc(p, l) }
    }
    unsafe fn realloc(&self, p: *mut u8, l: std::alloc::Layout, n: usize) -> *mut u8 {
        ALLOCS.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
        unsafe { std::alloc::System.realloc(p, l, n) }
    }
}
#[global_allocator]
static GLOBAL: Counting = Counting;

fn allocs() -> u64 {
    ALLOCS.load(std::sync::atomic::Ordering::Relaxed)
}

fn rid(tag: u8, i: u32) -> Id {
    let mut out = [0u8; 32];
    out[0] = 0xff;
    out[1] = tag;
    out[28..].copy_from_slice(&i.to_be_bytes());
    out
}

fn key(i: usize) -> String {
    format!("urn:ietf:params:oauth:ckt:sha-256:k{i:042}")
}

/// A row as persist's `KRow` presents it.
#[derive(Clone, Debug)]
struct B {
    id: Id,
    names: Vec<Id>,
    signer: String,
    kind: SeatKind,
    to: Vec<String>,
    scope: Option<String>,
    obj: Option<Obj<Id, String>>,
    conf: Option<Conf>,
    cosigners: Vec<String>,
    head: Vec<Id>,
    policy: Option<String>,
    counted: Option<String>,
    need: Option<usize>,
    of: Option<Id>,
    target: Option<Id>,
    win: Option<WinKind>,
    window: Option<String>,
    says: Option<String>,
    receipt: Option<Id>,
    at: Option<i64>,
    rec: Option<(String, i64, Option<i64>)>,
    sigs: Vec<String>,
}

impl B {
    fn new(id: Id, names: Vec<Id>, signer: String) -> B {
        B {
            id,
            names,
            signer,
            kind: SeatKind::Other,
            to: Vec::new(),
            scope: None,
            obj: None,
            conf: None,
            cosigners: Vec::new(),
            head: Vec::new(),
            policy: None,
            counted: None,
            need: None,
            of: None,
            target: None,
            win: None,
            window: None,
            says: None,
            receipt: None,
            at: None,
            rec: None,
            sigs: Vec::new(),
        }
    }
}

impl Row for B {
    type Id = Id;
    type Key = String;
    fn id(&self) -> &Id {
        &self.id
    }
    fn names(&self) -> &[Id] {
        &self.names
    }
    fn signer(&self) -> &String {
        &self.signer
    }
}

impl SeatRow for B {
    type Word = String;
    fn seat_kind(&self) -> SeatKind {
        self.kind
    }
    fn to(&self) -> &[String] {
        &self.to
    }
    fn scope(&self) -> Option<&String> {
        self.scope.as_ref()
    }
    fn obj(&self) -> Option<Obj<Id, String>> {
        self.obj.clone()
    }
    fn conf(&self) -> Option<Conf> {
        self.conf
    }
    fn cosigners(&self) -> &[String] {
        &self.cosigners
    }
    fn head(&self) -> &[Id] {
        &self.head
    }
    fn policy(&self) -> Option<&String> {
        self.policy.as_ref()
    }
    fn counted(&self) -> Option<&String> {
        self.counted.as_ref()
    }
    fn need(&self) -> Option<usize> {
        self.need
    }
    fn of(&self) -> Option<&Id> {
        self.of.as_ref()
    }
    fn target(&self) -> Option<&Id> {
        self.target.as_ref()
    }
}

impl WindowRow for B {
    type T = i64;
    fn win_kind(&self) -> Option<WinKind> {
        self.win
    }
    fn window(&self) -> Option<&String> {
        self.window.as_ref()
    }
    fn says(&self) -> Option<&String> {
        self.says.as_ref()
    }
    fn receipt(&self) -> Option<&Id> {
        self.receipt.as_ref()
    }
    fn at(&self) -> Option<i64> {
        self.at
    }
}

impl KeyEndRow for B {
    type T = i64;
    fn record(&self) -> Option<Record<'_, String, i64>> {
        self.rec.as_ref().map(|(k, from, until)| Record {
            key: k,
            from: *from,
            until: *until,
            succ_of: None,
            at_old: None,
            sigs: &self.sigs,
            end: EndRule::Optional,
        })
    }
}

/// Persist's `NoCut`: every row on its signer's key slot, no row a cut.
struct NoCut;
impl CutSpec<B> for NoCut {
    type Slot = String;
    type Say = ();
    fn key_slot(&self, k: &String) -> String {
        k.clone()
    }
    fn on_slots(&self, r: &B) -> BTreeSet<String> {
        std::iter::once(r.signer.clone()).collect()
    }
    fn cuts_of(&self, _r: &B) -> BTreeSet<String> {
        BTreeSet::new()
    }
    fn says(&self, _r: &B) {}
}

/// Persist's `law::seat_law()`.
fn law() -> SeatLaw {
    SeatLaw {
        roster_seats: vec!["member".into(), "founder".into()],
        depth: 1,
        policy: [
            ("founder_only", Policy::One),
            ("open:self_admit", Policy::SelfAdmit),
            ("unanimous", Policy::Unanimous),
            ("majority", Policy::Strict(1, 2)),
            ("quorum", Policy::Declared),
            ("weighted", Policy::Weighted),
        ]
        .iter()
        .map(|(w, p)| (w.to_string(), *p))
        .collect(),
        ..Default::default()
    }
}

/// A ballot as persist's `consensus::ballot_rows` presents it: the founding row `G`, one offer per other
/// member, the version `V` naming every seat, and the counted row `C` at head `[V]` with `voices` voices.
fn ballot(n: usize, voices: usize, policy: &str) -> Vec<B> {
    let gid = rid(0, 0);
    let members: Vec<String> = (0..n).map(key).collect();
    let g_signer = members[0].clone();
    let mut rows = Vec::with_capacity(n + 3);
    let mut g = B::new(gid, Vec::new(), g_signer.clone());
    g.kind = SeatKind::Offer;
    g.to = vec![g_signer.clone()];
    g.scope = Some("member".into());
    g.obj = Some(Obj::Row(gid));
    g.conf = Some(Conf::Own);
    rows.push(g);
    let mut version = vec![gid];
    for (i, k) in members.iter().enumerate().skip(1) {
        let id = rid(1, i as u32);
        version.push(id);
        let mut o = B::new(id, vec![gid], g_signer.clone());
        o.kind = SeatKind::Offer;
        o.to = vec![k.clone()];
        o.scope = Some("member".into());
        o.obj = Some(Obj::Row(gid));
        o.conf = Some(Conf::Own);
        o.cosigners = vec![k.clone()];
        rows.push(o);
    }
    let head = rid(2, 0);
    rows.push(B::new(head, version, g_signer.clone()));
    let mut c = B::new(rid(3, 0), vec![head], members[0].clone());
    c.kind = SeatKind::Offer;
    c.to = vec![key(n + 7)];
    c.scope = Some("member".into());
    c.obj = Some(Obj::Row(gid));
    c.conf = Some(Conf::Group);
    c.cosigners = members[1..voices.max(1)].to_vec();
    c.head = vec![head];
    c.policy = Some(policy.into());
    c.counted = Some("member".into());
    rows.push(c);
    rows
}

/// Owner bindings as persist's `owner::owner_rows` presents them: `n` offers of `owner` over the node's key,
/// conferred by the node and accepted by the owner's cosignature; every other one withdrawn by its owner.
fn owner(n: usize) -> Vec<B> {
    let node = key(1_000_000);
    let mut rows = Vec::new();
    for i in 0..n {
        let mut o = B::new(rid(4, i as u32), Vec::new(), node.clone());
        o.kind = SeatKind::Offer;
        o.to = vec![key(i)];
        o.scope = Some("owner".into());
        o.obj = Some(Obj::Key(node.clone()));
        o.conf = Some(Conf::Own);
        o.cosigners = vec![key(i)];
        rows.push(o);
    }
    for i in (0..n).step_by(2) {
        let t = rid(4, i as u32);
        let mut w = B::new(rid(5, i as u32), vec![t], key(i));
        w.kind = SeatKind::Withdraw;
        w.target = Some(t);
        rows.push(w);
    }
    rows
}

/// A group's ledger: the ballot's roster, then `n` counted acts in a chain, each at the head of the one
/// before, with one fork at the middle; for `line::settle` and `Seats::tips`.
fn ledger(n: usize) -> Vec<B> {
    let mut rows = ballot(n.min(64), 1, "founder_only");
    rows.pop();
    let gid = rid(0, 0);
    let mut prev = rid(2, 0);
    for i in 0..n {
        let mut c = B::new(rid(6, i as u32), vec![prev], key(0));
        c.kind = SeatKind::Offer;
        c.to = vec![key(10_000 + i)];
        c.scope = Some("member".into());
        c.obj = Some(Obj::Row(gid));
        c.conf = Some(Conf::Group);
        c.head = vec![prev];
        c.policy = Some("founder_only".into());
        rows.push(c);
        if i == n / 2 {
            let mut f = rows.last().unwrap().clone();
            f.id = rid(7, 0);
            f.to = vec![key(20_000)];
            rows.push(f);
        }
        prev = rid(6, i as u32);
    }
    rows
}

fn chain_edges(n: usize, extra: usize) -> Vec<Accepts<String, ()>> {
    let mut e: Vec<Accepts<String, ()>> =
        (0..n).map(|i| Accepts { src: key(i), dst: key(i + 1), classes: Vec::new(), depth: 5 }).collect();
    let mut g = dag::Lcg(3);
    for _ in 0..extra {
        let a = (g.next() as usize) % (n + 1);
        let b = (g.next() as usize) % (n + 1);
        e.push(Accepts { src: key(a), dst: key(b), classes: Vec::new(), depth: (g.next() % 6) as u32 });
    }
    e
}

/// A window: the ballot's roster (`n` members), an opener at head `[V]`, an answer from each member, the
/// concluder's receipt and its landing.
fn window_rows(n: usize) -> Vec<B> {
    let mut rows = ballot(n, 1, "founder_only");
    rows.pop();
    let head = rid(2, 0);
    let mut o = B::new(rid(8, 0), vec![head], key(0));
    o.win = Some(WinKind::Open);
    o.window = Some("w".into());
    o.obj = Some(Obj::Row(rid(0, 0)));
    o.head = vec![head];
    let oid = o.id;
    rows.push(o);
    let mut ans = Vec::new();
    for i in 0..n {
        let mut a = B::new(rid(9, i as u32), vec![oid], key(i));
        a.win = Some(WinKind::Answer);
        a.of = Some(oid);
        a.says = Some(if i % 3 == 0 { "no".into() } else { "approve".into() });
        ans.push(a.id);
        rows.push(a);
    }
    let mut r = B::new(rid(10, 0), vec![oid], key(0));
    r.win = Some(WinKind::Receipt);
    r.of = Some(oid);
    r.at = Some(0);
    let recid = r.id;
    rows.push(r);
    let mut l = B::new(rid(11, 0), [vec![recid], ans].concat(), key(0));
    l.win = Some(WinKind::Landing);
    l.of = Some(oid);
    l.receipt = Some(recid);
    l.at = Some(100);
    l.says = Some("enact".into());
    rows.push(l);
    rows
}

fn window_spec() -> WindowSpec<i64> {
    WindowSpec {
        counted: "member".into(),
        concluder: "member".into(),
        opener_says: Some("approve".into()),
        at_once: vec![Clause {
            value: "approve".into(),
            how: How::AtLeast(2, 3, 1),
            over: Base::All,
            out: "enact".into(),
        }],
        silent: None,
        at_close: vec![Clause { value: "approve".into(), how: How::Strict, over: Base::All, out: "enact".into() }],
        default: "cancel".into(),
        target_votes: false,
        secs: 50,
    }
}

/// Key records: `n` keys, each with a record and a renewal naming it; every third key's records end.
fn key_rows(n: usize) -> Vec<B> {
    let mut rows = Vec::new();
    for i in 0..n {
        let k = key(i);
        let until = if i % 3 == 0 { Some(50) } else { Some(1_000) };
        let mut r = B::new(rid(12, i as u32), Vec::new(), k.clone());
        r.rec = Some((k.clone(), 0, until));
        r.sigs = vec![k.clone()];
        let mut s = B::new(rid(13, i as u32), vec![r.id], k.clone());
        s.rec = Some((k.clone(), 10, until.map(|u| u + 10)));
        s.sigs = vec![k.clone()];
        rows.push(r);
        rows.push(s);
    }
    rows
}

type HStore = BTreeMap<u32, Entry<u32, u32, i64>>;

/// A head store: one roster version with `n` members, `n` acts at it, one receipt per act from a member.
fn head_store(n: usize) -> HStore {
    let mut s = BTreeMap::new();
    let mut v = Entry::new(0u32, Kind::Seat, 0u32, Vec::new());
    v.members = (0..n as u32).collect();
    v.q = n / 3 + 1;
    s.insert(0, v);
    for i in 0..n as u32 {
        let a = 1 + 2 * i;
        let mut e = Entry::new(a, Kind::Act, i, vec![0]);
        e.head = Some(0);
        s.insert(a, e);
        let mut k = Entry::new(a + 1, Kind::Ack, (i + 1) % n as u32, vec![a]);
        k.of = Some(a);
        s.insert(a + 1, k);
    }
    s
}

// ---- the harness ------------------------------------------------------------------------------------------

struct H {
    filter: Option<String>,
    /// The last median of each bench, by name, with its size: a bench whose next size would take more
    /// than the budget, read quadratically from the last, is skipped and printed as such.
    last: std::cell::RefCell<BTreeMap<String, (usize, f64)>>,
    /// Print each bench's name instead of running it (`--list`).
    list: bool,
}

impl H {
    /// Whether a section holds a bench the filter names: its setup is skipped otherwise, so a bench run alone
    /// (`=name`, in a process of its own) has the same heap before it in every binary.
    fn wants(&self, prefixes: &[&str]) -> bool {
        self.filter.as_ref().is_none_or(|f| match f.strip_prefix('=') {
            Some(x) => prefixes.iter().any(|p| x.starts_with(p)),
            None => prefixes.iter().any(|p| p.contains(f.as_str()) || f.starts_with(p)),
        })
    }

    fn named(&self, name: &str) -> bool {
        self.filter.as_ref().is_none_or(|f| match f.strip_prefix('=') {
            Some(x) => name == x,
            None => name.contains(f.as_str()),
        })
    }
    fn run<T: PartialEq + std::fmt::Debug>(&self, name: &str, n: usize, mut f: impl FnMut() -> T) {
        if !self.named(name) {
            return;
        }
        if self.list {
            println!("{name}");
            return;
        }
        if let Some(&(m, ns)) = self.last.borrow().get(name) {
            let r = n as f64 / m as f64;
            if ns * r * r > 2e9 {
                println!("{name}\t{n}\tskipped\t0\t0\t-");
                return;
            }
        }
        let want = f();
        let a0 = allocs();
        let t = Instant::now();
        let got = black_box(f());
        let one = t.elapsed().as_nanos().max(1) as f64;
        let per = allocs() - a0;
        assert_eq!(got, want, "{name}/{n}: a second call answered differently");
        // a sample is at least 20 ms; 9 samples, fewer for slow calls
        let iters = ((20e6 / one).ceil() as usize).clamp(1, 1_000_000);
        let samples = if one > 300e6 { 3 } else { 9 };
        let mut ts = Vec::with_capacity(samples);
        for _ in 0..samples {
            let t = Instant::now();
            for _ in 0..iters {
                black_box(f());
            }
            ts.push(t.elapsed().as_nanos() as f64 / iters as f64);
        }
        ts.sort_by(|a, b| a.partial_cmp(b).unwrap());
        let med = ts[samples / 2];
        self.last.borrow_mut().insert(name.to_string(), (n, med));
        println!("{name}\t{n}\t{med:.1}\t{samples}\t{iters}\t{per}");
    }
}

impl H {
    /// A bench of a call that changes its state (`Held::admit`): each sample gets a fresh state from `setup`,
    /// built outside the timing, and times one call on it. Prints the median of 31 samples; the answer of
    /// every call must be the first one's.
    fn run_mut<S, T: PartialEq + std::fmt::Debug>(
        &self,
        name: &str,
        n: usize,
        setup: impl Fn() -> S,
        mut f: impl FnMut(&mut S) -> T,
    ) {
        if !self.named(name) {
            return;
        }
        if self.list {
            println!("{name}");
            return;
        }
        let mut st = setup();
        let a0 = allocs();
        let want = f(&mut st);
        let per = allocs() - a0;
        drop(st);
        let samples = 31;
        let mut ts = Vec::with_capacity(samples);
        for _ in 0..samples {
            let mut st = setup();
            let t = Instant::now();
            let got = black_box(f(&mut st));
            ts.push(t.elapsed().as_nanos() as f64);
            assert_eq!(got, want, "{name}/{n}: a later call answered differently");
            drop(st);
        }
        ts.sort_by(|a, b| a.partial_cmp(b).unwrap());
        println!("{name}\t{n}\t{:.1}\t{samples}\t1\t{per}", ts[samples / 2]);
    }
}

/// `n` rows shaped as persist's `KRow`, each naming up to three of the 64 before it (`dag::dag(n, 3, 64, 7)`).
fn held_rows(n: usize) -> Vec<B> {
    dag::dag(n as u32, 3, 64, 7)
        .into_iter()
        .map(|d| B::new(rid(9, d.id), d.names.iter().map(|&q| rid(9, q)).collect(), key(d.signer as usize)))
        .collect()
}

/// A copy of a held view with room for the next admissions: a clone has none, and its first push would
/// copy every buffer, which no caller holding one view pays.
fn fresh<'a, S: Clone + HeldSpec<B>>(b: &Held<'a, B, S>) -> Held<'a, B, S> {
    let mut c = b.clone();
    c.reserve(512, 1024);
    c
}

fn concluded<'a>(rows: &'a [B], law: &SeatLaw) -> Concluded<'a, B> {
    layers::conclude(rows.iter(), |p| seat::seat_rule(p, law, &NoCut, &|_| true), None)
}

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let mut sizes = vec![3usize, 16, 128, 1_024, 16_384];
    let mut filter = None;
    let mut list = false;
    let mut i = 0;
    while i < args.len() {
        if args[i] == "--list" {
            list = true;
            sizes = vec![3];
            i += 1;
        } else if args[i] == "--sizes" {
            sizes = args[i + 1].split(',').map(|s| s.parse().unwrap()).collect();
            i += 2;
        } else {
            filter = Some(args[i].clone());
            i += 1;
        }
    }
    let h = H { filter, last: Default::default(), list };
    let law = law();
    if !h.list {
        println!("bench\tsize\tns_per_call\tsamples\titers\tallocs_per_call");
    }
    for &n in &sizes {
        let gobj = Obj::Row(rid(0, 0));
        if h.wants(&["graph::"]) {
            // the graph
            let d = dag::dag(n as u32, 3, 64, 7);
            h.run("graph::Graph::new", n, || Graph::new(d.iter()).len());
            h.run("graph::Graph::new+ancestors(last)", n, || Graph::new(d.iter()).depth(n - 1));
        }
        if h.wants(&["seat::seat_rule/"]) {
            // the seat rule over a ballot, as persist first called it, and its parts
            for (pol, v) in [("majority", n / 2 + 1), ("founder_only", 1), ("unanimous", n)] {
                let rows = ballot(n, v, pol);
                h.run(&format!("seat::seat_rule/ballot/{pol}"), n, || {
                    let c = concluded(&rows, &law);
                    c.concluded(c.g.len() - 1)
                });
            }
        }
        // <group_count>
        if h.wants(&["seat::group_count"]) {
            // the same counts over the roster already resolved (persist's `consensus::count` shape): the sets given,
            // and the sets built from the roster's keys on every call, as persist's adapter builds them
            let keys: Vec<String> = (0..n).map(key).collect();
            for (pol, v) in [("majority", n / 2 + 1), ("founder_only", 1), ("unanimous", n)] {
                let policy = law.policy.get(pol).copied();
                let to = [key(n + 7)];
                let mem: BTreeSet<&str> = keys.iter().map(String::as_str).collect();
                let vs: BTreeSet<&str> = keys[..v.max(1)].iter().map(String::as_str).collect();
                let to_s: Vec<&str> = to.iter().map(String::as_str).collect();
                h.run(&format!("seat::group_count/{pol}"), n, || {
                    let c = GroupCount { policy, offer: true, to: &to_s, members: &mem, voices: &vs, need: None };
                    group_count(&c, |_| 1)
                });
                h.run(&format!("seat::group_count+sets/{pol}"), n, || {
                    let mem: BTreeSet<&str> = keys.iter().map(String::as_str).collect();
                    let vs: BTreeSet<&str> = keys[..v.max(1)].iter().map(String::as_str).collect();
                    let c = GroupCount { policy, offer: true, to: &to_s, members: &mem, voices: &vs, need: None };
                    group_count(&c, |_| 1)
                });
                let rows = ballot(n, v, pol);
                h.run(&format!("seat::group_count=seat_rule/{pol}"), n, || {
                    let c = concluded(&rows, &law);
                    let direct = GroupCount { policy, offer: true, to: &to_s, members: &mem, voices: &vs, need: None };
                    assert_eq!(Some(c.concluded(c.g.len() - 1)), group_count(&direct, |_| 1), "{pol}/{n}");
                    0u8
                });
            }
        }
        // </group_count>
        if h.wants(&[
            "seat::members_at",
            "seat::voices",
            "seat::left_in_past",
            "seat::met",
            "seat::Seats::new",
            "seat::Seats::holders",
            "seat::Seats::one",
            "seat::Seats::new/one_offer_seats_all",
        ]) {
            let rows = ballot(n, n / 2 + 1, "majority");
            let c = concluded(&rows, &law);
            let last = c.g.len() - 1;
            let anc: Vec<usize> = c.g.ancestors(last).iter().filter(|&q| c.concluded(q)).collect();
            let p = Past { g: &c.g, i: last, p: &anc };
            let head = [rid(2, 0)];
            h.run("seat::members_at", n, || seat::members_at(&p, &law, &NoCut, &gobj, &head, "member").len());
            h.run("seat::voices", n, || seat::voices(p.row(), &p).len());
            h.run("seat::left_in_past", n, || seat::left_in_past(&p, &gobj, "member").len());
            h.run("seat::met", n, || seat::met(Some(Policy::Strict(1, 2)), black_box(n / 2 + 1), black_box(n), None));
            h.run("seat::Seats::new", n, || Seats::new(&c, &law, &NoCut, None).recs().len());
            // one founding offer seating every member, each its cosigner (the first shape of persist's ballot)
            let mut one = B::new(rid(0, 0), Vec::new(), key(0));
            one.kind = SeatKind::Offer;
            one.to = (0..n).map(key).collect();
            one.cosigners = (1..n).map(key).collect();
            one.scope = Some("member".into());
            one.obj = Some(Obj::Row(rid(0, 0)));
            one.conf = Some(Conf::Own);
            let one_rows = vec![one];
            let one_c = concluded(&one_rows, &law);
            h.run("seat::Seats::new/one_offer_seats_all", n, || Seats::new(&one_c, &law, &NoCut, None).recs().len());
            let s = Seats::new(&c, &law, &NoCut, None);
            h.run("seat::Seats::holders", n, || s.holders("member", &gobj, None).len());
            h.run("seat::Seats::one", n, || s.one("member", &gobj));
        }
        if h.wants(&["owner/"]) {
            // the owner seat
            let rows = owner(n);
            let node = Obj::Key(key(1_000_000));
            h.run("owner/conclude+Seats::holders", n, || {
                let c = concluded(&rows, &law);
                Seats::new(&c, &law, &NoCut, None).holders("owner", &node, None).len()
            });
            let c = concluded(&rows, &law);
            h.run("owner/Seats::new+one", n, || Seats::new(&c, &law, &NoCut, None).one("owner", &node));
        }
        if h.wants(&["trust::", "derived::"]) {
            // the trust walk
            let e = chain_edges(n, n);
            let last_key = key(n);
            let near = key(3.min(n));
            h.run("trust::reaches/hit", n, || trust::reaches(&e, &key(0), &(), trust::HOP_CAP, &near));
            h.run("trust::reaches/miss", n, || trust::reaches(&e, &key(0), &(), trust::HOP_CAP, &key(n + 9)));
            h.run("trust::honours", n, || trust::honours(&e, &key(0), |_, _| true, &last_key, &()));
            let pairs: Vec<(String, String)> = e.iter().map(|x| (x.src.clone(), x.dst.clone())).collect();
            h.run("derived::reach/5", n, || derived::reach(&key(0), 5, &pairs).len());
            // <index>
            // the edges indexed once, for a caller that walks them again and again
            let ix = trust::EdgeIndex::new(&e);
            h.run("trust::EdgeIndex::reaches/hit", n, || ix.reaches(&key(0), &(), trust::HOP_CAP, &near));
            h.run("trust::EdgeIndex::reaches/miss", n, || ix.reaches(&key(0), &(), trust::HOP_CAP, &key(n + 9)));
            h.run("trust::EdgeIndex::new", n, || trust::EdgeIndex::new(&e).reaches(&key(0), &(), 0, &near));
            // </index>
        }
        if h.wants(&["line::", "seat::Seats::tips"]) {
            // the reader's line
            let rows = ledger(n);
            let c = concluded(&rows, &law);
            let own = key(0);
            h.run("line::settle", n, || line::settle(&c, &SeatLine, &gobj, Some(&own), |_| true).len());
            h.run("line::void", n, || line::void(&c, &SeatLine, Some(&own), |_| true).len());
            let s = Seats::new(&c, &law, &NoCut, None);
            h.run("seat::Seats::tips", n, || s.tips(&gobj).len());
        }
        if h.wants(&["head::"]) {
            // head
            let store = head_store(n);
            h.run("head::View::new", n, || head::View::new(&store, &[], 0u32, Reading::Broad, true).c().len());
            let v = head::View::new(&store, &[], 0u32, Reading::Broad, true);
            h.run("head::View::answers", n, || v.answers(10).counts_at.len());
            h.run("head::View::settled(one act)", n, || v.settled(&1));
            h.run("head::purge", n, || head::purge(&store, 0u32, 10, Reading::Broad).0.len());
        }
        if h.wants(&["held::"]) {
            // issue #4: one row admitted against a held view, against the whole fold over the same rows
            let rows = held_rows(n);
            let spec =
                Rules { wf: |_: &B| true, rule: |p: &Past<'_, '_, B>| seat::seat_rule(p, &law, &NoCut, &|_| true) };
            let m = n as u32;
            let tips = [rid(9, m - 1), rid(9, m - 2), rid(9, m / 2)];
            let x = B::new(rid(9, m), tips.to_vec(), key(3));
            let base = Held::new(spec, rows.iter());
            assert_eq!(base.len(), n);
            h.run_mut("held::admit(one)", n, || fresh(&base), |hv| hv.admit(&x).unwrap().visited);
            // the kernel's own work, with a rule that reads nothing: what is left is the rule's
            let free = Rules { wf: |_: &B| true, rule: |_: &Past<'_, '_, B>| true };
            let base_free = Held::new(free, rows.iter());
            h.run_mut(
                "held::admit(one)/rule_reads_nothing",
                n,
                || fresh(&base_free),
                |hv| hv.admit(&x).unwrap().visited,
            );
            h.run("held::past_of_x(depth)", n, || base.concluded().g.depth(m as usize - 1));
            let mut with_x = rows.clone();
            with_x.push(x.clone());
            h.run("held::refold(one)", n, || concluded(&with_x, &law).cs().len());
            let mut shuffled = rows.clone();
            let mut g = dag::Lcg(5);
            for i in (1..shuffled.len()).rev() {
                shuffled.swap(i, (g.next() as usize) % (i + 1));
            }
            h.run("held::new/in_order", n, || Held::new(spec, rows.iter()).len());
            h.run("held::new/shuffled", n, || Held::new(spec, shuffled.iter()).len());
            // one new row with `d` dependents already waiting on it: the re-fold persist runs today
            for d in [1usize, 16, 256] {
                let deps: Vec<B> = (0..d as u32)
                    .map(|j| B::new(rid(10, j), vec![rid(9, m), rid(9, (j * 7) % m)], key(j as usize % 16)))
                    .collect();
                let waiting = {
                    let mut hv = fresh(&base);
                    for r in &deps {
                        assert!(hv.admit(r).unwrap().waiting);
                    }
                    hv
                };
                h.run_mut(
                    &format!("held::admit_dependents/{d}"),
                    n,
                    || fresh(&waiting),
                    |hv| {
                        let a = hv.admit(&x).unwrap();
                        assert_eq!(a.kept.len(), d + 1);
                        // the bound: the rows kept and what they name, never the store
                        assert_eq!(a.visited, (d + 1) + 3 + 2 * d);
                        a.dirty.len()
                    },
                );
                let mut all = with_x.clone();
                all.extend(deps.iter().cloned());
                h.run(&format!("held::refold_dependents/{d}"), n, || concluded(&all, &law).cs().len());
            }
            h.run("held::clone", n, || base.clone().len());
        }
        if h.wants(&["window::"]) {
            // window
            let rows = window_rows(n);
            let spec = window_spec();
            let tables = |w: &String| if w == "w" { Some(spec.clone()) } else { None };
            let rule = |p: &Past<'_, '_, B>| {
                window::rule(p, &tables, &law, &NoCut).unwrap_or_else(|| seat::seat_rule(p, &law, &NoCut, &|_| true))
            };
            h.run("window::rule/conclude", n, || {
                let c = layers::conclude(rows.iter(), rule, None);
                c.concluded(c.g.len() - 1)
            });
            let c = layers::conclude(rows.iter(), rule, None);
            let op = c.g.idx(&rid(8, 0)).unwrap();
            h.run("window::outcome", n, || window::outcome(&c, op, &tables, &law, &NoCut, &|_| true));
        }
        if h.wants(&["key_end::"]) {
            // key end
            let rows = key_rows(n);
            let c = layers::conclude(rows.iter(), key_end::conclude_rule, None);
            let k0 = key(1);
            h.run("key_end::live", n, || key_end::live(&c, &k0, 20));
            h.run("key_end::ended", n, || key_end::ended(&c, &k0, 60));
            h.run("key_end::retained", n, || key_end::retained(&c, 60).len());
            h.run("key_end::conclude", n, || layers::conclude(rows.iter(), key_end::conclude_rule, None).cs().len());
        }
    }
}
