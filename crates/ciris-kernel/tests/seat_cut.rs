//! Differential: `seat::exercised_stands` (an act under a seat follows the cut, CC 2.4.1.1, read forward as
//! CONFERRAL_END.md E2 to E4: counted at its own head, and in force from the end's head on) and the members at
//! every concluded row as a head, against `models/causal_kernel/check_seat_cut.py`'s named cases and every kept
//! set of its two pools (fixture `seat_cut.json`).

mod common;
use ciris_kernel::layers::{conclude, kept, Past};
use ciris_kernel::seat::{exercised_stands, members_at, seat_rule, Exercised, Obj};
use common::*;
use std::collections::BTreeMap;

fn word(e: Exercised) -> &'static str {
    match e {
        Exercised::ConcludesNothing => "concludes nothing",
        Exercised::NotSeated => "not seated",
        Exercised::Stands => "stands",
        Exercised::OutOfForce => "out of force",
        Exercised::NotCounted => "does not count",
        Exercised::Contested { counted: true } => "contested",
        Exercised::Contested { counted: false } => "contested, not counted",
    }
}

#[test]
fn seat_cut_worlds() {
    let fx = fixture("seat_cut.json");
    assert!(fx.at("problems").arr().is_empty());
    let law = law_of(fx.at("law"));
    let spec = DictCut;
    let (mut cases, mut bad) = (0usize, 0usize);
    let mut tally: BTreeMap<&'static str, usize> = BTreeMap::new();
    for w in fx.at("worlds").arr() {
        let name = w.at("name").s();
        let refs: BTreeMap<String, String> =
            w.at("refs").obj().iter().map(|(k, v)| (k.clone(), v.s().to_string())).collect();
        let rows = rows_with_refs(w.at("rows").arr(), &refs);
        let c = conclude(kept(&rows, |_| true), |p| seat_rule(p, &law, &spec, &|_| true), None);
        let mut cmp = |ok: bool, what: String| {
            cases += 1;
            if !ok {
                bad += 1;
                eprintln!("{name}: {what}");
            }
        };
        let ids: Vec<String> = c.g.rows().iter().map(|r| r.id.clone()).collect();
        cmp(ids == w.at("kept").strs(), "kept".into());
        for (i, want) in w.at("c").arr().iter().enumerate() {
            cmp(c.concluded(i) == want.b(), format!("concluded {}", c.g.row(i).id));
        }
        let k = w.at("k").s().to_string();
        let scope = w.at("scope").s();
        let oname = w.at("obj").s();
        // the object, as the rows' own references typed it
        let obj = rows
            .iter()
            .filter_map(|r| r.obj.clone())
            .find(|o| matches!(o, Obj::Row(x) | Obj::Key(x) if x == oname))
            .expect("an object some row names");
        for (x, want) in w.at("acts").obj() {
            let i = c.g.idx(x).unwrap();
            let got = exercised_stands(&c, &law, &spec, i, &k, scope, &obj);
            *tally.entry(word(got)).or_default() += 1;
            cmp(word(got) == want.s(), format!("act {x}: {} (model {})", word(got), want.s()));
            // the two answers, as seat.ANSWERS gives them for the model's word
            let two = match want.s() {
                "stands" => (true, true),
                "out of force" | "contested" => (true, false),
                _ => (false, false),
            };
            cmp((got.counted(), got.in_force()) == two, format!("act {x}: counted, in force"));
        }
        // the members at every concluded row as a head: by past, untouched by the cut
        for (h, want) in w.at("heads").obj() {
            let hi = c.g.idx(h).unwrap();
            let mut anc: Vec<usize> = c.cs().iter().copied().filter(|&q| c.g.in_past(q, hi)).collect();
            anc.push(hi);
            anc.sort();
            let p = Past::new(&c.g, hi, &anc);
            let got = members_at(&p, &law, &spec, &obj, std::slice::from_ref(&h.to_string()), scope);
            cmp(sorted_ids(&got) == want.strs(), format!("members at {h}"));
        }
    }
    eprintln!("  answers: {tally:?}");
    report("exercised_stands and the members at a head (check_seat_cut.py cases and worlds)", cases, bad);
    assert_eq!(bad, 0);
}
