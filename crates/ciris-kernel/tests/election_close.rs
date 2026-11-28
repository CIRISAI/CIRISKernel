//! The ruled election close (the Constitution, 2026-11-28), against `models/causal_kernel/check_election_close.py`
//! (fixture `election_close.json`): one election per seat end (a fork opens nothing), the opening row and its count,
//! the electorate at the opening's heads, rival openings, the reader's wait, persons and the key view at the close's
//! inputs. Each case: the standing it asks and whether the seating's election is closed for the reader, with the key
//! view read over the seat and key rows where the case has key rows.

mod common;
use ciris_kernel::cut::CutSpec;
use ciris_kernel::key_end::{conclude_rule, KeyReading, KeyView};
use ciris_kernel::layers::{conclude, kept};
use ciris_kernel::seat::{election_closed, for_reader, seat_rule, Obj, SeatLaw, Seats};
use common::*;
use std::collections::{BTreeMap, BTreeSet};

/// DictCut, with a key view.
struct KeyCut<'k> {
    kv: Option<&'k dyn KeyView<String, String>>,
}

impl CutSpec<TRow> for KeyCut<'_> {
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
    fn key_view(&self) -> Option<&dyn KeyView<String, String>> {
        self.kv
    }
}

fn answer(
    rows: &[TRow],
    law: &SeatLaw,
    spec: &KeyCut<'_>,
    ask: (&str, &str, &str),
    seating: &str,
    reader: Option<&String>,
) -> (bool, bool) {
    let c = conclude(kept(rows, |_| true), |p| seat_rule(p, law, spec, &|_| true), None);
    let (rc, rv) = for_reader(&c, law, spec, reader);
    let q = match reader {
        Some(k) => Seats::for_reader(&rc, law, spec, k, &rv),
        None => Seats::new(&rc, law, spec, None),
    };
    let stands = q.stands(&ask.0.to_string(), ask.1, &Obj::Row(ask.2.to_string()), None);
    (stands, election_closed(&c, law, spec, &seating.to_string(), reader))
}

#[test]
fn election_close_cases() {
    let fx = fixture("election_close.json");
    let law: SeatLaw = law_of(fx.at("law"));
    let (mut cases, mut bad) = (0, 0);
    for c in fx.at("cases").arr() {
        let name = c.at("name").s();
        let refs: BTreeMap<String, String> =
            c.at("refs").obj().iter().map(|(k, v)| (k.clone(), v.s().to_string())).collect();
        let all = rows_with_refs(c.at("rows").arr(), &refs);
        let seat_ids: BTreeSet<String> = c.at("seat").strs().into_iter().collect();
        let seat_rows: Vec<TRow> = all.iter().filter(|r| seat_ids.contains(&r.id)).cloned().collect();
        let ask = c.at("ask").strs();
        let reader = c.get("reader").and_then(|r| r.opt_s());
        let seating = c.at("seating").s();
        let want: Vec<bool> = c.at("want").arr().iter().map(|x| x.b()).collect();
        // the key lane and the seat rows in one causal order, concluded by the end rule: the key view
        let kc = conclude(kept(&all, |_| true), conclude_rule, None);
        let reading = KeyReading { c: &kc, reader: None, final_: BTreeSet::new(), roster: BTreeSet::new() };
        let spec = KeyCut { kv: if c.at("keys").b() { Some(&reading) } else { None } };
        let got = answer(&seat_rows, &law, &spec, (&ask[0], &ask[1], &ask[2]), seating, reader.as_ref());
        cases += 1;
        if [got.0, got.1] != want[..] {
            bad += 1;
            eprintln!("{name}: got {got:?}, want {want:?}");
        }
    }
    report("the ruled election close (check_election_close.py)", cases, bad);
    assert_eq!(bad, 0);
}
