//! The trust root's fork fold (`ciris_kernel::root`), replayed from `models/trust_root/check_root.py` (fixture
//! `root.json`): every bundle's count, the void (S'' and T, contested recoveries), the reader's bundles in force,
//! its holders and seats, the grants as rows and as they resolve for the reader; and stalled recoveries judged by
//! the seat rule against the root (`seat::recovery_verdict`).

mod common;
use ciris_kernel::cut::CutSpec;
use ciris_kernel::layers::{conclude, kept, Past};
use ciris_kernel::root::{Identity, Reader, Revocation, Root, RootBundle, RootGrant, RootReading, RootView};
use ciris_kernel::seat::{recovery_verdict, seat_rule, Obj, Seats};
use common::{fixture, law_of, report, rows_with_refs, DictCut, TRow, J};
use std::collections::{BTreeMap, BTreeSet};

struct TB {
    id: String,
    family: String,
    version: u64,
    prev: Vec<String>,
    holders: Vec<String>,
    seats: Vec<String>,
    charter: String,
    duties: Vec<String>,
    iat: u64,
    recovery: Vec<(String, String)>,
    recovers: Option<(String, String)>,
    stmts: Vec<(String, u64)>,
}

impl RootBundle for TB {
    type Id = String;
    type Key = String;
    type Word = String;
    fn id(&self) -> &String {
        &self.id
    }
    fn family(&self) -> &String {
        &self.family
    }
    fn version(&self) -> u64 {
        self.version
    }
    fn prev(&self) -> &[String] {
        &self.prev
    }
    fn holders(&self) -> &[String] {
        &self.holders
    }
    fn seats(&self) -> &[String] {
        &self.seats
    }
    fn charter(&self) -> &String {
        &self.charter
    }
    fn duties(&self) -> &[String] {
        &self.duties
    }
    fn recovery(&self) -> &[(String, String)] {
        &self.recovery
    }
    fn recovers(&self) -> Option<(&String, &String)> {
        self.recovers.as_ref().map(|(a, b)| (a, b))
    }
    fn iat(&self) -> u64 {
        self.iat
    }
    fn statements(&self) -> &[(String, u64)] {
        &self.stmts
    }
}

/// A row of the root's lane: a grant, or an acceptance edge (`head`).
struct TG {
    id: String,
    names: Vec<String>,
    grant: bool,
    head: Option<String>,
    bundles: Vec<String>,
    to: String,
    scope: String,
    signers: Vec<String>,
    identity: Vec<String>,
    duty: String,
}

impl ciris_kernel::Row for TG {
    type Id = String;
    type Key = String;
    fn id(&self) -> &String {
        &self.id
    }
    fn names(&self) -> &[String] {
        &self.names
    }
    fn signer(&self) -> &String {
        self.signers.first().unwrap_or(&self.to)
    }
}

impl RootGrant for TG {
    type Word = String;
    fn is_grant(&self) -> bool {
        self.grant
    }
    fn attached_head(&self) -> Option<&String> {
        self.head.as_ref()
    }
    fn bundles(&self) -> &[String] {
        &self.bundles
    }
    fn to(&self) -> &String {
        &self.to
    }
    fn scope(&self) -> &String {
        &self.scope
    }
    fn signers(&self) -> &[String] {
        &self.signers
    }
    fn duty(&self) -> &String {
        &self.duty
    }
}

fn pair(j: &J) -> (String, String) {
    let a = j.arr();
    (a[0].s().to_string(), a[1].s().to_string())
}

fn bundles(j: &J) -> Vec<TB> {
    j.arr()
        .iter()
        .map(|b| TB {
            id: b.at("id").s().into(),
            family: b.at("family").s().into(),
            version: b.at("version").i() as u64,
            prev: b.at("prev").strs(),
            holders: b.at("holders").strs(),
            seats: b.at("seats").strs(),
            charter: b.at("charter").s().into(),
            duties: b.at("duties").strs(),
            iat: b.at("iat").i() as u64,
            recovery: b.at("recovery").arr().iter().map(pair).collect(),
            recovers: b.get("recovers").filter(|x| !x.is_null()).map(pair),
            stmts: b.at("stmts").arr().iter().map(|s| (s.arr()[0].s().to_string(), s.arr()[1].i() as u64)).collect(),
        })
        .collect()
}

fn grants(j: &J) -> Vec<TG> {
    let st = |g: &J, k: &str| g.get(k).and_then(|x| x.opt_s()).unwrap_or_default();
    let ss = |g: &J, k: &str| g.get(k).filter(|x| !x.is_null()).map(|x| x.strs()).unwrap_or_default();
    j.arr()
        .iter()
        .map(|g| TG {
            id: g.at("id").s().into(),
            names: ss(g, "names"),
            grant: g.at("kind").s() == "grant",
            head: g.get("head").and_then(|h| h.opt_s()),
            bundles: ss(g, "bundles"),
            to: st(g, "to"),
            scope: st(g, "scope"),
            signers: ss(g, "signers"),
            identity: ss(g, "identity"),
            duty: st(g, "duty"),
        })
        .collect()
}

fn reader(j: &J) -> Reader<String, String> {
    Reader {
        anchor: j.get("anchor").and_then(|a| a.opt_s()),
        thumbs: j.get("thumbs").filter(|t| !t.is_null()).map(|t| t.str_set()),
        acks: j.at("acks").str_set(),
    }
}

fn sorted(s: impl IntoIterator<Item = String>) -> Vec<String> {
    let mut v: Vec<String> = s.into_iter().collect();
    v.sort();
    v
}

#[test]
fn root_replay() {
    let fx = fixture("root.json");
    let (mut cases, mut bad) = (0, 0);
    for c in fx.at("cases").arr() {
        let bs = bundles(c.at("bundles"));
        let revs: Vec<Revocation<String, String>> = c
            .at("revokes")
            .arr()
            .iter()
            .map(|r| Revocation { key: r.at("key").s().into(), bound: r.get("bound").and_then(|b| b.opt_s()) })
            .collect();
        let gs = grants(c.at("grants"));
        let rd = reader(c.at("reader"));
        let root = Root::new(&bs, &revs, &gs);
        let name = c.at("name").s();
        let mut fail = |what: &str, got: String| {
            bad += 1;
            eprintln!("root {name}: {what}: got {got}");
        };
        for (i, want) in c.at("concluded").obj() {
            if root.counted(i).is_ok() != want.b() {
                fail(&format!("counted {i}"), format!("{:?}", root.counted(i)));
            }
        }
        if sorted(root.void()) != c.at("void").strs() {
            fail("void", format!("{:?}", root.void()));
        }
        let heads = root.heads(&rd);
        let want_heads = c.get("heads").filter(|h| !h.is_null()).map(|h| h.strs());
        if heads.clone().map(sorted) != want_heads {
            fail("heads", format!("{heads:?}"));
        }
        let f = root.in_force(&rd);
        let want_h = c.get("holders").filter(|h| !h.is_null()).map(|h| h.strs());
        let want_s = c.get("seats").filter(|h| !h.is_null()).map(|h| h.strs());
        if f.as_ref().map(|(h, _)| sorted(h.iter().cloned())) != want_h
            || f.as_ref().map(|(_, s)| sorted(s.iter().cloned())) != want_s
        {
            fail("in force", format!("{f:?}"));
        }
        for (g, want) in c.at("grant").obj() {
            let got = root.grant_in_force(g, &rd);
            let w = want.arr();
            let want: Result<(), String> = if w[0].b() { Ok(()) } else { Err(w[1].s().to_string()) };
            if got.map_err(String::from) != want {
                fail(&format!("grant {g}"), format!("{got:?}"));
            }
        }
        for (g, want) in c.at("row").obj() {
            if root.grant_row(g) != want.b() {
                fail(&format!("row {g}"), format!("{}", root.grant_row(g)));
            }
        }
        cases += 1;
    }
    report("the trust root's lineage against check_root.py", cases, bad);
    assert_eq!(bad, 0);
}

/// DictCut, with a trust root read.
struct RootCut<'v>(Option<&'v dyn RootView<String, String, Obj<String, String>>>);

impl CutSpec<TRow> for RootCut<'_> {
    type Slot = J;
    type Say = J;
    fn key_slot(&self, k: &String) -> J {
        DictCut.key_slot(k)
    }
    fn on_slots(&self, r: &TRow) -> BTreeSet<J> {
        DictCut.on_slots(r)
    }
    fn cuts_of(&self, r: &TRow) -> BTreeSet<J> {
        DictCut.cuts_of(r)
    }
    fn says(&self, r: &TRow) -> J {
        DictCut.says(r)
    }
    fn need(&self, r: &TRow) -> usize {
        DictCut.need(r)
    }
    fn rejects(&self, r: &TRow) -> Vec<String> {
        DictCut.rejects(r)
    }
    fn is_voice_for(&self, cosign: &TRow, cut: &TRow) -> bool {
        DictCut.is_voice_for(cosign, cut)
    }
    fn trust_root(&self) -> Option<&dyn RootView<String, String, Obj<String, String>>> {
        self.0
    }
}

#[test]
fn stalled_recovery_replay() {
    let fx = fixture("root.json");
    let law = law_of(fixture("seat.json").at("law"));
    let (mut cases, mut bad) = (0, 0);
    for c in fx.at("recovery").arr() {
        let refs: BTreeMap<String, String> =
            c.at("refs").obj().iter().map(|(k, v)| (k.clone(), v.s().to_string())).collect();
        let rows = rows_with_refs(c.at("rows").arr(), &refs);
        let bs = c.get("bundles").filter(|b| !b.is_null()).map(bundles);
        let gs = grants(c.at("grants"));
        let revs: Vec<Revocation<String, String>> = Vec::new();
        // the store's one fact: a key's identity type, from its key record (here, the grant naming it)
        let identity = |k: &String| {
            let ids: Vec<String> = gs.iter().find(|g| &g.to == k).map(|g| g.identity.clone()).unwrap_or_default();
            Identity { user: ids.iter().any(|i| i == "user"), node: ids.iter().any(|i| i == "node") }
        };
        let root = bs.as_ref().map(|bs| Root::new(bs, &revs, &gs));
        let view = root.as_ref().map(|root| RootReading { root, reader: reader(c.at("reader")), identity: &identity });
        let spec = RootCut(view.as_ref().map(|v| v as &dyn RootView<String, String, Obj<String, String>>));
        let k = kept(&rows, |_| true);
        let cc = conclude(k, |p| seat_rule(p, &law, &spec, &|_| true), None);
        let i = cc.g.rows().iter().position(|r| r.id == "rv").expect("the recovery row");
        let anc: Vec<usize> = cc.cs().iter().copied().filter(|&q| cc.g.in_past(q, i)).collect();
        let p = Past::new(&cc.g, i, &anc);
        let why = recovery_verdict(&p, &law, &spec).err();
        let concluded = cc.cs().contains(&i);
        let f4 = Seats::new(&cc, &law, &spec, None).holders("founder", &Obj::Row("g".to_string()), None).contains("f4");
        let want_why = c.get("reason").and_then(|r| r.opt_s());
        cases += 1;
        if concluded != c.at("concluded").b() || why.map(String::from) != want_why || f4 != c.at("f4").b() {
            bad += 1;
            eprintln!("recovery {}: got concluded {concluded}, {why:?}, f4 {f4}", c.at("name").s());
        }
    }
    report("stalled recovery against the trust root, against check_root.py", cases, bad);
    assert_eq!(bad, 0);
}
