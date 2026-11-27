//! Differential: where a row is placed and who it is for, family by family, against
//! `models/causal_kernel/audience.py` (fixture `audience.json`, written by `check_audience.py`): every family
//! pattern of the table in every cohort scope, and the hand-written cases, the copy rule among them.

mod common;
use ciris_kernel::audience::{
    audiences, family_of, place, Audience, AudienceRow, FamilyPlacement, Placed, FAMILIES, FAMILY_MODEL_SHA256,
};
use common::*;
use std::collections::{BTreeMap, BTreeSet};

struct ARow {
    id: String,
    family: String,
    scope: String,
    room: Option<String>,
    signer: String,
    named: Vec<String>,
    names: Vec<String>,
    concluded: bool,
}

impl AudienceRow for ARow {
    type Id = String;
    type Key = String;
    fn id(&self) -> &String {
        &self.id
    }
    fn family(&self) -> &str {
        &self.family
    }
    fn scope(&self) -> &str {
        &self.scope
    }
    fn room(&self) -> Option<&String> {
        self.room.as_ref()
    }
    fn signer(&self) -> &String {
        &self.signer
    }
    fn named(&self) -> &[String] {
        &self.named
    }
    fn names(&self) -> &[String] {
        &self.names
    }
    fn concluded(&self) -> bool {
        self.concluded
    }
}

fn arow(j: &J) -> ARow {
    ARow {
        id: j.at("id").s().to_string(),
        family: j.at("family").s().to_string(),
        scope: j.at("scope").s().to_string(),
        room: j.get("room").and_then(|v| v.opt_s()),
        signer: j.at("signer").s().to_string(),
        named: j.at("named").strs(),
        names: j.at("names").strs(),
        concluded: j.at("concluded").b(),
    }
}

fn s(x: &str) -> J {
    J::Str(x.to_string())
}

// an answer in the fixture's form
fn enc(a: &Placed<String>) -> J {
    match a {
        Placed::Placed(p, Audience::Everyone) => J::Arr(vec![s("placed"), s(p.word()), s("everyone")]),
        Placed::Placed(p, Audience::Keys(ks)) => {
            J::Arr(vec![s("placed"), s(p.word()), J::Arr(ks.iter().map(|k| s(k)).collect::<Vec<J>>())])
        }
        Placed::Refused(r) => J::Arr(vec![s("refused"), s(r.as_str())]),
        Placed::Undecided(f) => J::Arr(vec![s("undecided"), s(f)]),
    }
}

fn world(fx: &J) -> (BTreeMap<String, BTreeSet<String>>, BTreeMap<String, BTreeSet<String>>) {
    let m = |k: &str| fx.at(k).obj().iter().map(|(a, v)| (a.clone(), v.str_set())).collect();
    (m("roster"), m("person"))
}

/// The table the crate carries is the one the fixture was written from.
#[test]
fn the_pinned_table() {
    let fx = fixture("audience.json");
    assert_eq!(FAMILY_MODEL_SHA256, fx.at("source").at("sha256").s(), "re-run tools/family_placement.py");
    assert_eq!(FAMILIES.len() as i64, fx.at("source").at("families").i());
    let undecided = FAMILIES.iter().filter(|(_, c)| *c == FamilyPlacement::Undecided).count() as i64;
    assert_eq!(undecided, fx.at("source").at("undecided").i());
    // a name built from each pattern resolves to it
    for (p, _) in FAMILIES {
        let name: Vec<&str> =
            p.split(':').map(|s| if s == "*" || (s.starts_with('{') && s.ends_with('}')) { "x" } else { s }).collect();
        assert_eq!(family_of(&name.join(":")).map(|f| f.0), Some(*p), "{p}");
    }
}

#[test]
fn every_family_in_every_scope() {
    let fx = fixture("audience.json");
    let (roster, person) = world(&fx);
    let ro = |r: &String| roster.get(r).cloned().unwrap_or_default();
    let pe = |k: &String| person.get(k).cloned().unwrap_or_else(|| [k.clone()].into());
    let (mut n, mut bad) = (0, 0);
    for g in fx.at("generated").arr() {
        let room = g.get("room").and_then(|v| v.opt_s());
        let r = ARow {
            id: "x".into(),
            family: g.at("name").s().to_string(),
            scope: g.at("scope").s().to_string(),
            named: if room.is_some() { vec!["b".into()] } else { vec![] },
            room,
            signer: "a".into(),
            names: vec![],
            concluded: true,
        };
        n += 1;
        let got = enc(&place(&r, &ro, &pe));
        if &got != g.at("answer") {
            bad += 1;
            eprintln!("{} at {}: got {got:?}, want {:?}", g.at("family").s(), g.at("scope").s(), g.at("answer"));
        }
    }
    report("placement and audience of every family in every scope (audience.py)", n, bad);
    assert_eq!(bad, 0);
}

#[test]
fn case_table() {
    let fx = fixture("audience.json");
    let (roster, person) = world(&fx);
    let ro = |r: &String| roster.get(r).cloned().unwrap_or_default();
    let pe = |k: &String| person.get(k).cloned().unwrap_or_else(|| [k.clone()].into());
    let (mut n, mut bad) = (0, 0);
    for c in fx.at("cases").arr() {
        let rows: Vec<ARow> = c.at("rows").arr().iter().map(arow).collect();
        let refs: Vec<&ARow> = rows.iter().collect();
        let rev: Vec<&ARow> = rows.iter().rev().collect();
        for list in [refs, rev] {
            let got = audiences(&list, &ro, &pe);
            for (i, want) in c.at("answers").obj() {
                n += 1;
                let g = got.get(i).map(enc);
                if g.as_ref() != Some(want) {
                    bad += 1;
                    eprintln!("{}: {i} got {g:?}, want {want:?}", c.at("name").s());
                }
            }
        }
    }
    report("audience cases, the copy rule among them (audience.py)", n, bad);
    assert_eq!(bad, 0);
}
