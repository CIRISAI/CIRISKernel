//! Differential: the reader's trust walk from acceptance edge rows and the issuer's standing, against
//! `models/causal_kernel/check_trust_rows.py` (fixture `trust_rows.json`), under the pending rulings and under the
//! model's stand-in (a member of a community speaks for it and issues its licences), with the rows as listed and in
//! reverse.

mod common;
use ciris_kernel::cut::CutSpec;
use ciris_kernel::layers::{conclude, kept};
use ciris_kernel::seat::{for_reader, seat_rule, Obj, Seats};
use ciris_kernel::trust::Charters;
use ciris_kernel::trust_rows::{is_community, read_licence, refusal, Pending, Ruled, Rulings};
use common::{fixture, law_of, report, rows_with_refs, DictCut, TRow, J};
use std::collections::BTreeMap;

fn refs_of(c: &J) -> BTreeMap<String, String> {
    c.at("refs").obj().iter().map(|(k, v)| (k.clone(), v.s().to_string())).collect()
}

fn obj(rows: &[TRow], n: &str) -> Obj<String, String> {
    if rows.iter().any(|r| r.id == n) {
        Obj::Row(n.to_string())
    } else {
        Obj::Key(n.to_string())
    }
}

/// The model's stand-in for rulings (a) and (b): a member of a community speaks for it, and a licence a member signs
/// is its act.
struct Members;

impl<S: CutSpec<TRow>> Rulings<TRow, S> for Members {
    fn speaks_for(&self, seats: &Seats<'_, '_, TRow, S>, row: &TRow, src: &Obj<String, String>) -> Ruled {
        if is_community(seats, src) {
            if seats.holders("member", src, None).contains(&row.signer) {
                Ruled::Yes
            } else {
                Ruled::No
            }
        } else {
            Pending.speaks_for(seats, row, src)
        }
    }
    fn issued_by(&self, seats: &Seats<'_, '_, TRow, S>, lic: &TRow, auth: &Obj<String, String>) -> Ruled {
        if is_community(seats, auth) {
            if seats.holders("member", auth, None).contains(&lic.signer) {
                Ruled::Yes
            } else {
                Ruled::No
            }
        } else {
            Pending.issued_by(seats, lic, auth)
        }
    }
}

#[test]
fn trust_rows_replay() {
    let fx = fixture("trust_rows.json");
    let law = law_of(fixture("seat.json").at("law"));
    let spec = DictCut;
    let (mut cases, mut bad) = (0, 0);
    for c in fx.at("cases").arr() {
        let rows = rows_with_refs(c.at("rows").arr(), &refs_of(c));
        let mut supplied = Charters::new();
        for (a, cs) in c.at("supplied").obj() {
            supplied.meet(obj(&rows, a), cs.strs());
        }
        let want = if c.at("honoured").b() { None } else { Some(c.at("reason").s().to_string()) };
        let reader = obj(&rows, c.at("reader").s());
        let lic = c.at("licence").s().to_string();
        for rev in [false, true] {
            let mut rs = rows.clone();
            if rev {
                rs.reverse();
            }
            let cc = conclude(kept(&rs, |_| true), |p| seat_rule(p, &law, &spec, &|_| true), None);
            let (rc, _) = for_reader(&cc, &law, &spec, None);
            let q = Seats::new(&rc, &law, &spec, None);
            let got = match c.at("rulings").s() {
                "members" => read_licence(&q, &Members, &reader, &lic, &supplied, None),
                _ => read_licence(&q, &Pending, &reader, &lic, &supplied, None),
            }
            .err()
            .map(|u| u.word().to_string());
            cases += 2;
            if !cc.concluded_id(&lic) {
                bad += 1;
                eprintln!("{} (reversed: {rev}): the licence row is not admitted", c.at("name").s());
            }
            if got != want {
                bad += 1;
                eprintln!("{} (reversed: {rev}): got {got:?}, want {want:?}", c.at("name").s());
            }
        }
    }
    for c in fx.at("refusals").arr() {
        let rows = rows_with_refs(c.at("rows").arr(), &refs_of(c));
        let cc = conclude(kept(&rows, |_| true), |p| seat_rule(p, &law, &spec, &|_| true), None);
        let q = Seats::new(&cc, &law, &spec, None);
        let want = c.get("refusal").filter(|x| !x.is_null()).map(|x| x.s().to_string());
        let got = refusal(&q, &Pending, &rows[0]).map(str::to_string);
        cases += 1;
        if got != want {
            bad += 1;
            eprintln!("refusal {}: got {got:?}, want {want:?}", c.at("name").s());
        }
    }
    report("the trust walk from rows against check_trust_rows.py", cases, bad);
    assert_eq!(bad, 0);
}
