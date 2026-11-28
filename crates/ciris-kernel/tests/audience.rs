//! Differential: where a row is placed and who it is for, family by family, against
//! `models/causal_kernel/audience.py` (fixture `audience.json`, written by `check_audience.py`): every family
//! pattern of the table in every cohort scope, and the hand-written cases, the copy rule among them.

mod common;
use ciris_kernel::audience::{
    audiences, family_in, family_of, follow, history_of, place, seats_of, Audience, AudienceRow, FamilyMatch,
    FamilyPlacement, Follows, History, Joins, PersonsOf, Placed, Placement, SeatAct, FAMILIES, FAMILY_MODEL_SHA256,
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
    seat: Option<SeatAct>,
    obj: Option<String>,
    to: Vec<String>,
    history: Option<History>,
    evidence: Option<String>,
    stream: Option<String>,
    cites: Vec<String>,
    purpose: Option<String>,
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
    fn seat_act(&self) -> Option<SeatAct> {
        self.seat
    }
    fn obj(&self) -> Option<&String> {
        self.obj.as_ref()
    }
    fn to(&self) -> &[String] {
        &self.to
    }
    fn history_on_join(&self) -> Option<History> {
        self.history
    }
    fn evidence(&self) -> Option<&String> {
        self.evidence.as_ref()
    }
    fn stream(&self) -> Option<&String> {
        self.stream.as_ref()
    }
    fn cites(&self) -> &[String] {
        &self.cites
    }
    fn purpose(&self) -> Option<&str> {
        self.purpose.as_deref()
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
        seat: match j.get("kind").and_then(|v| v.opt_s()).as_deref() {
            Some("offer") => Some(SeatAct::Offer),
            Some("unseat") => Some(SeatAct::Unseat),
            _ => None,
        },
        obj: j.get("obj").and_then(|v| v.opt_s()),
        to: j.get("to").map(|v| v.strs()).unwrap_or_default(),
        // a word the door would refuse is absent
        history: j.get("history_on_join").and_then(|v| History::from_word(v.s())),
        evidence: j.get("evidence").and_then(|v| v.opt_s()),
        stream: j.get("stream").and_then(|v| v.opt_s()),
        cites: j.get("cites").map(|v| v.strs()).unwrap_or_default(),
        purpose: j.get("purpose").and_then(|v| v.opt_s()),
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

// the rosters, and the persons as the seat model's one persons function gave them (seat.rep_of: a key's person,
// none for a key of two persons; seat.person_keys: a person's live keys)
type Voices = BTreeMap<String, Option<String>>;
fn world(fx: &J) -> (BTreeMap<String, BTreeSet<String>>, (Voices, BTreeMap<String, BTreeSet<String>>)) {
    let m = |k: &str| fx.at(k).obj().iter().map(|(a, v)| (a.clone(), v.str_set())).collect();
    let voice: Voices = fx.at("voice").obj().iter().map(|(k, v)| (k.clone(), v.opt_s())).collect();
    (m("roster"), (voice, m("person_keys")))
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
    let (vo, pk) = (
        |k: &String| person.0.get(k).cloned().unwrap_or_else(|| Some(k.clone())),
        |p: &String| person.1.get(p).cloned().unwrap_or_else(|| [p.clone()].into()),
    );
    let pe = PersonsOf { voice: &vo, keys: &pk };
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
            seat: None,
            obj: None,
            to: vec![],
            history: None,
            evidence: None,
            stream: None,
            cites: vec![],
            purpose: None,
        };
        n += 1;
        // the generated rows: no member changes, so the members at a row's head are the roster
        let none = Joins { history: &|_| None, at_head: &|rm, _| ro(rm) };
        let got = enc(&place(&r, &ro, &pe, &none));
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
    let (vo, pk) = (
        |k: &String| person.0.get(k).cloned().unwrap_or_else(|| Some(k.clone())),
        |p: &String| person.1.get(p).cloned().unwrap_or_else(|| [p.clone()].into()),
    );
    let pe = PersonsOf { voice: &vo, keys: &pk };
    let (mut n, mut bad) = (0, 0);
    for c in fx.at("cases").arr() {
        let rows: Vec<ARow> = c.at("rows").arr().iter().map(arow).collect();
        // the case's view of the room: the record's history_on_join, the members at each row's own head
        let w = c.at("joins");
        let history: BTreeMap<String, String> = w
            .get("history")
            .map(|h| h.obj().iter().map(|(k, v)| (k.clone(), v.s().to_string())).collect())
            .unwrap_or_default();
        let hi = |room: &String| history.get(room).and_then(|v| History::from_word(v));
        let heads: BTreeMap<String, BTreeSet<String>> = w
            .get("at_head")
            .map(|h| h.obj().iter().map(|(k, v)| (k.clone(), v.str_set())).collect())
            .unwrap_or_default();
        // a case that states none: no member changed, the roster
        let ah = |rm: &String, i: &String| heads.get(i).cloned().unwrap_or_else(|| ro(rm));
        let joins = Joins { history: &hi, at_head: &ah };
        let refs: Vec<&ARow> = rows.iter().collect();
        let rev: Vec<&ARow> = rows.iter().rev().collect();
        for list in [refs, rev] {
            let got = audiences(&list, &ro, &pe, &joins);
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

/// Two family patterns that tie on a name decide nothing; a synthetic table, since the pinned one has no tie
/// (`check_audience.py`'s TIES).
#[test]
fn ties_refuse() {
    let fx = fixture("audience.json");
    let (mut n, mut bad) = (0, 0);
    for t in fx.at("ties").arr() {
        let pats = t.at("families").strs();
        let table: Vec<(&str, FamilyPlacement)> =
            pats.iter().map(|p| (p.as_str(), FamilyPlacement::Allowed(&[Placement::Commons]))).collect();
        let got = match family_in(&table, t.at("name").s()) {
            FamilyMatch::None => J::Null,
            FamilyMatch::Tie => J::Str("ambiguous".into()),
            FamilyMatch::One(f) => J::Str(f.0.to_string()),
        };
        n += 1;
        if &got != t.at("answer") {
            bad += 1;
            eprintln!("{} over {pats:?}: got {got:?}, want {:?}", t.at("name").s(), t.at("answer"));
        }
    }
    report("family names that tie (audience.py)", n, bad);
    assert_eq!(bad, 0);
}

/// The `history_on_join` a caller reads for a kept stream: the row's own, else the record's, else from_join; an
/// unknown word is absent (`check_audience.py`'s HISTORY). It changes no audience.
#[test]
fn history_on_join_words() {
    let fx = fixture("audience.json");
    let (mut n, mut bad) = (0, 0);
    for h in fx.at("history").arr() {
        let rec = h.get("record").and_then(|v| v.opt_s());
        let r = ARow {
            id: "m".into(),
            family: "chat:general".into(),
            scope: "community".into(),
            room: Some("r3".into()),
            signer: "a".into(),
            named: vec![],
            names: vec![],
            concluded: true,
            seat: None,
            obj: None,
            to: vec![],
            history: h.get("row").and_then(|v| v.opt_s()).and_then(|w| History::from_word(&w)),
            evidence: None,
            stream: None,
            cites: vec![],
            purpose: None,
        };
        let hi = |_: &String| rec.as_deref().and_then(History::from_word);
        let got = history_of(&r, &Joins { history: &hi, at_head: &|_, _| BTreeSet::new() });
        let want = History::from_word(h.at("answer").s()).expect("a word");
        n += 1;
        if got != want {
            bad += 1;
            eprintln!("row {:?}, record {rec:?}: got {got:?}, want {want:?}", h.get("row"));
        }
    }
    report("history_on_join words (audience.py)", n, bad);
    assert_eq!(bad, 0);
}

/// The keys a seat row seats, derived from the row: a room seat family's offer or unseat over its own room only
/// (`check_audience.py`'s SEATS).
#[test]
fn seats_derived() {
    let fx = fixture("audience.json");
    let (mut n, mut bad) = (0, 0);
    for c in fx.at("seats").arr() {
        let r = arow(c.at("row"));
        let got: Vec<String> = seats_of(&r).to_vec();
        n += 1;
        if got != c.at("seats").strs() {
            bad += 1;
            eprintln!("{} {:?}: got {got:?}, want {:?}", r.family, r.seat, c.at("seats").strs());
        }
    }
    report("seats derived from the seat row (audience.py)", n, bad);
    assert_eq!(bad, 0);
}

// an answer from the fixture's form
fn dec(j: &J) -> Placed<String> {
    let a = j.arr();
    match a[0].s() {
        "placed" => {
            let p = [
                Placement::SelfCollective,
                Placement::TargetedFamily,
                Placement::TargetedRoom,
                Placement::Commons,
                Placement::Addressed,
            ]
            .into_iter()
            .find(|p| p.word() == a[1].s())
            .expect("a placement");
            let aud = match &a[2] {
                J::Str(s) if s == "everyone" => Audience::Everyone,
                k => Audience::Keys(k.str_set()),
            };
            Placed::Placed(p, aud)
        }
        "refused" => {
            use ciris_kernel::audience::Refusal::*;
            let all = [
                FamilyUnknown,
                ScopeUnknown,
                PlacementNotAllowed,
                NamedOutsideAudience,
                NoRoom,
                FamilyAmbiguous,
                FollowsNotNamed,
                FollowsNotHeld,
                FollowsUnplaced,
                FollowsMismatch,
                FollowsAmbiguous,
                FollowsWider,
            ];
            Placed::Refused(all.into_iter().find(|r| r.as_str() == a[1].s()).expect("a refusal"))
        }
        _ => panic!("not an answer this test decodes: {j:?}"),
    }
}

/// The rule of a `follows` family over answers stated directly (`check_audience.py`'s FOLLOW).
#[test]
fn follows_rule() {
    let fx = fixture("audience.json");
    let (mut n, mut bad) = (0, 0);
    for c in fx.at("follow").arr() {
        let own = dec(c.at("own"));
        let followed = c.get("followed").filter(|f| !f.is_null()).map(dec);
        let rule = if c.at("rule").s() == "same" { Follows::Same } else { Follows::Narrower };
        let (_, person) = world(&fx);
        let (vo, pk) = (
            |k: &String| person.0.get(k).cloned().unwrap_or_else(|| Some(k.clone())),
            |p: &String| person.1.get(p).cloned().unwrap_or_else(|| [p.clone()].into()),
        );
        let pe = PersonsOf { voice: &vo, keys: &pk };
        let named = if c.at("named").b() { Ok(()) } else { Err(ciris_kernel::audience::Refusal::FollowsNotNamed) };
        let got = enc(&follow(named, own, followed.as_ref(), rule, &pe));
        n += 1;
        if &got != c.at("answer") {
            bad += 1;
            eprintln!("{:?}: got {got:?}, want {:?}", c.at("own"), c.at("answer"));
        }
    }
    report("the follows rule (audience.py)", n, bad);
    assert_eq!(bad, 0);
}

/// The Undecided path, over a synthetic table (the pinned one has none since d5d42bf; `check_audience.py`'s
/// UNDECIDED).
#[test]
fn undecided_path() {
    let fx = fixture("audience.json");
    let (roster, person) = world(&fx);
    let ro = |r: &String| roster.get(r).cloned().unwrap_or_default();
    let (vo, pk) = (
        |k: &String| person.0.get(k).cloned().unwrap_or_else(|| Some(k.clone())),
        |p: &String| person.1.get(p).cloned().unwrap_or_else(|| [p.clone()].into()),
    );
    let pe = PersonsOf { voice: &vo, keys: &pk };
    let u = fx.at("undecided");
    // a table that lives as long as the test binary, as FAMILIES does
    let table: Vec<(&'static str, FamilyPlacement)> = u
        .at("families")
        .arr()
        .iter()
        .map(|f| {
            let name: &'static str = Box::leak(f.arr()[0].s().to_string().into_boxed_str());
            let cell = if f.arr()[1].is_null() {
                FamilyPlacement::Allowed(&[Placement::SelfCollective])
            } else {
                FamilyPlacement::Undecided
            };
            (name, cell)
        })
        .collect();
    let table: &'static [(&'static str, FamilyPlacement)] = Box::leak(table.into_boxed_slice());
    let joins = Joins { history: &|_| None, at_head: &|rm, _| ro(rm) };
    let (mut n, mut bad) = (0, 0);
    for c in u.at("cases").arr() {
        let scope = c.at("scope").s().to_string();
        let r = ARow {
            id: "u".into(),
            family: c.at("family").s().to_string(),
            room: if scope == "community" { Some("r1".into()) } else { None },
            scope,
            signer: "a".into(),
            named: vec![],
            names: vec![],
            concluded: true,
            seat: None,
            obj: None,
            to: vec![],
            history: None,
            evidence: None,
            stream: None,
            cites: vec![],
            purpose: None,
        };
        let got = enc(&place_in(table, &r, &ro, &pe, &joins));
        n += 1;
        if &got != c.at("answer") {
            bad += 1;
            eprintln!("{}: got {got:?}, want {:?}", r.family, c.at("answer"));
        }
    }
    report("the Undecided path over a synthetic table (audience.py)", n, bad);
    assert_eq!(bad, 0);
}

/// End to end: the crate's own persons, `seat::Persons::over(..).voice` and `seat::person_keys` over the seat-model
/// rows the reference read (`persons_world`: a2 seated in a's self roster, a3 evicted, t2 a key of two persons),
/// agree with the reference's tables, and the case table placed through that `PersonsOf` gives the reference's
/// answers.
#[test]
fn persons_from_the_seat_model() {
    use ciris_kernel::layers::{conclude, kept};
    use ciris_kernel::seat::{person_keys, seat_rule, Persons};
    let fx = fixture("audience.json");
    let law = law_of(fixture("seat.json").at("law"));
    let w = fx.at("persons_world");
    let refs: BTreeMap<String, String> =
        w.at("refs").obj().iter().map(|(k, v)| (k.clone(), v.s().to_string())).collect();
    let rows = rows_with_refs(w.at("rows").arr(), &refs);
    let c = conclude(kept(&rows, |_| true), |p| seat_rule(p, &law, &DictCut, &|_| true), None);
    let held: Vec<&TRow> = c.cs().iter().map(|&i| c.g.row(i)).collect();
    let pp = Persons::over(&held, &law, &DictCut, None);
    let vo = |k: &String| pp.voice(k);
    let pk = |p: &String| person_keys(&c, &law, &DictCut, p);
    let (mut n, mut bad) = (0, 0);
    // the tables the reference read
    for (k, v) in fx.at("voice").obj() {
        n += 1;
        if vo(k) != v.opt_s() {
            bad += 1;
            eprintln!("voice of {k}: got {:?}, want {:?}", vo(k), v.opt_s());
        }
    }
    for (p, ks) in fx.at("person_keys").obj() {
        n += 1;
        if pk(p) != ks.str_set() {
            bad += 1;
            eprintln!("keys of {p}: got {:?}, want {:?}", pk(p), ks.str_set());
        }
    }
    // the case table placed through the seat model's persons
    let (roster, _) = world(&fx);
    let ro = |r: &String| roster.get(r).cloned().unwrap_or_default();
    let pe = PersonsOf { voice: &vo, keys: &pk };
    for case in fx.at("cases").arr() {
        let crows: Vec<ARow> = case.at("rows").arr().iter().map(arow).collect();
        let list: Vec<&ARow> = crows.iter().collect();
        let jw = case.at("joins");
        let heads: BTreeMap<String, BTreeSet<String>> = jw
            .get("at_head")
            .map(|h| h.obj().iter().map(|(k, v)| (k.clone(), v.str_set())).collect())
            .unwrap_or_default();
        let history: BTreeMap<String, String> = jw
            .get("history")
            .map(|h| h.obj().iter().map(|(k, v)| (k.clone(), v.s().to_string())).collect())
            .unwrap_or_default();
        let hi = |room: &String| history.get(room).and_then(|v| History::from_word(v));
        let ah = |rm: &String, i: &String| heads.get(i).cloned().unwrap_or_else(|| ro(rm));
        let got = audiences(&list, &ro, &pe, &Joins { history: &hi, at_head: &ah });
        for (i, want) in case.at("answers").obj() {
            n += 1;
            if got.get(i).map(enc).as_ref() != Some(want) {
                bad += 1;
                eprintln!("{}: {i} got {:?}, want {want:?}", case.at("name").s(), got.get(i).map(enc));
            }
        }
    }
    report("audience over the seat model's own persons (seat::Persons, person_keys)", n, bad);
    assert_eq!(bad, 0);
}
