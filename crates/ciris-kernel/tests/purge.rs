//! Differential: answers by head, receipts and one say, settled and missing, the reader's line, windows read
//! at now, and checkpoint and purge, against every replay `models/causal_kernel/check_purge.py` runs over
//! `purge.py`'s nine histories under both readings (fixture `purge.json`).

mod common;
use ciris_kernel::head::{purge, Answers, Duty, Entry, Kind, Reading, View, WindowState};
use common::*;
use std::collections::BTreeMap;

type E = Entry<String, String, i64>;

fn entry(j: &J) -> E {
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
    e.delete = j.get("delete").map_or(false, |x| x.b());
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

fn ws(w: WindowState) -> &'static str {
    match w {
        WindowState::Open => "open",
        WindowState::Answered => "answered",
        WindowState::Lapsed => "lapsed",
    }
}

fn to_j(a: &Answers<String, String>) -> J {
    let s = |x: &String| J::Str(x.clone());
    let pairs = |v: &[(String, bool)]| J::Arr(v.iter().map(|(i, b)| J::Arr(vec![s(i), J::Bool(*b)])).collect());
    let mut m = BTreeMap::new();
    m.insert("kept".into(), J::Arr(a.kept.iter().map(s).collect()));
    m.insert("concluded".into(), pairs(&a.concluded));
    m.insert("countsAt".into(), pairs(&a.counts_at));
    m.insert("carried".into(), pairs(&a.carried));
    m.insert("settled".into(), pairs(&a.settled));
    m.insert(
        "missing".into(),
        J::Arr(a.missing.iter().map(|(i, ks)| J::Arr(vec![s(i), J::Arr(ks.iter().map(s).collect())])).collect()),
    );
    m.insert("void".into(), J::Arr(a.void.iter().map(s).collect()));
    m.insert(
        "window".into(),
        J::Arr(a.window.iter().map(|(i, w)| J::Arr(vec![s(i), J::Str(ws(*w).into())])).collect()),
    );
    J::Obj(m)
}

fn subsets<T: Clone>(v: &[T], k: usize) -> Vec<Vec<T>> {
    if k == 0 {
        return vec![vec![]];
    }
    let mut out = vec![];
    for i in 0..v.len() {
        for mut rest in subsets(&v[i + 1..], k - 1) {
            rest.insert(0, v[i].clone());
            out.push(rest);
        }
    }
    out
}

#[test]
fn purge_replays() {
    let fx = fixture("purge.json");
    let (mut cases, mut bad, mut replays) = (0, 0, 0);
    let mut cmp = |ok: bool, what: String| {
        cases += 1;
        if !ok {
            bad += 1;
            eprintln!("{what}");
        }
    };
    let mut kept_rows: BTreeMap<&str, (usize, usize)> = BTreeMap::new();
    for h in fx.arr() {
        let reading = if h.at("reading").s() == "broad" { Reading::Broad } else { Reading::Narrow };
        let own = h.at("own").s().to_string();
        let now0 = h.at("now").i();
        let name = format!("{} [{}]", h.at("name").s(), h.at("reading").s());
        let base: BTreeMap<String, E> = h.at("rows").arr().iter().map(|r| (r.at("id").s().to_string(), entry(r))).collect();
        let pool: Vec<E> = h.at("pool").arr().iter().map(entry).collect();
        let (first, tips) = purge(&base, own.clone(), now0, reading);
        // the first purge, row by row
        for (id, w) in h.at("first").obj() {
            let e = &first[id];
            let ok = e.stub == w.at("stub").b()
                && e.final_counts == w.at("final").get_bool()
                && e.settled_stub == w.at("settled_stub").b()
                && e.dropped == w.at("dropped").b()
                && e.ackers == w.at("ackers").strs()
                && e.acks == w.at("acks").strs();
            cmp(ok, format!("{name}: stored {id} differs: {e:?} against {w:?}"));
        }
        cmp(first.len() == h.at("first").obj().len(), format!("{name}: store size"));
        cmp(tips == h.at("tips").strs(), format!("{name}: checkpoint names"));
        let whole = first.values().filter(|e| !e.stub).count();
        let stubs = first.values().filter(|e| e.stub).count();
        cmp(whole as i64 == h.at("whole").i() && stubs as i64 == h.at("stubs").i(), format!("{name}: whole/stub"));
        let k = kept_rows.entry(if reading == Reading::Broad { "broad" } else { "narrow" }).or_default();
        k.0 += whole;
        k.1 += stubs;
        // every replay
        let mut it = h.at("replays").arr().iter();
        for n in 0..=pool.len() {
            for x in subsets(&pool, n) {
                let mut cases_x: Vec<(Vec<E>, BTreeMap<String, E>)> = vec![(vec![], first.clone())];
                for k1 in 1..x.len() {
                    for x1 in subsets(&x, k1) {
                        let v = View::new(&first, &x1, own.clone(), reading, true);
                        cases_x.push((x1, purge(&v.rec, own.clone(), now0, reading).0));
                    }
                }
                for (x1, store) in &cases_x {
                    let rest: Vec<E> = x.iter().filter(|r| !store.contains_key(&r.id)).cloned().collect();
                    for now in h.at("nows").arr() {
                        let now = now.i();
                        let r = it.next().expect("a replay the fixture does not have");
                        replays += 1;
                        let ids = |v: &[E]| v.iter().map(|e| e.id.clone()).collect::<Vec<_>>();
                        cmp(
                            r.at("x").strs() == ids(&x) && r.at("x1").strs() == ids(x1) && r.at("now").i() == now,
                            format!("{name}: replay order"),
                        );
                        let want = View::new(&base, &x, own.clone(), reading, true).answers(now);
                        let got = View::new(store, &rest, own.clone(), reading, true).answers(now);
                        cmp(to_j(&want) == *r.at("want"), format!("{name}: answers with nothing purged, {:?} now {now}", ids(&x)));
                        cmp(to_j(&got) == *r.at("got"), format!("{name}: answers after purge, {:?} / {:?} now {now}", ids(&x), ids(x1)));
                        cmp(want == got, format!("{name}: purge changed an answer"));
                    }
                }
            }
        }
        cmp(it.next().is_none(), format!("{name}: replays the fixture has and the test did not run"));
    }
    eprintln!("  replays: {replays}; rows kept whole / as stubs over the nine histories: {kept_rows:?}");
    report("checkpoint and purge (check_purge.py replays)", cases, bad);
    assert_eq!(bad, 0);
}

trait GetBool {
    fn get_bool(&self) -> Option<bool>;
}
impl GetBool for J {
    fn get_bool(&self) -> Option<bool> {
        match self {
            J::Bool(b) => Some(*b),
            _ => None,
        }
    }
}
