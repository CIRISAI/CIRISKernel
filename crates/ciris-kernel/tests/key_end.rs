//! Differential: a key's own end, against every world `models/causal_kernel/check_key_end.py` generates, at
//! every instant it reads (fixture `key_end.json`).

mod common;
use ciris_kernel::derived;
use ciris_kernel::key_end::{
    bytes_retained, conclude_rule, counts, ended, live, retained, successor, well_formed, EndRule,
};
use ciris_kernel::layers::{conclude, kept};
use common::*;

#[test]
fn key_end_worlds() {
    let fx = fixture("key_end.json");
    let ceil = fx.at("ceil").i();
    let keys = fx.at("keys").strs();
    let parties = fx.at("parties").strs();
    let subjects = fx.at("subjects").strs();
    let nows: Vec<i64> = fx.at("nows").arr().iter().map(|x| x.i()).collect();
    let required = fx.at("required").str_set();
    let forbidden = fx.at("forbidden").str_set();
    let pool = fx.at("pool").arr();
    let (mut cases, mut bad) = (0, 0);
    for (wi, w) in fx.at("worlds").arr().iter().enumerate() {
        let js: Vec<J> = w.at("rows").arr().iter().map(|i| pool[i.i() as usize].clone()).collect();
        let mut rows = rows_of(&js);
        for r in rows.iter_mut() {
            if r.kind == "rec" {
                let typ = r.fs("typ").unwrap_or("").to_string();
                let room = r.f("room").is_some_and(|x| x.b());
                r.end = if forbidden.contains(&typ) {
                    EndRule::Forbidden
                } else if required.contains(&typ) && !room {
                    EndRule::Required
                } else {
                    EndRule::Optional
                };
            }
        }
        let c = conclude(kept(&rows, |r| well_formed(r, ceil)), conclude_rule, None);
        let mut cmp = |ok: bool, what: String| {
            cases += 1;
            if !ok {
                bad += 1;
                eprintln!("world {wi}: {what}");
            }
        };
        let kept_ids: Vec<String> = c.g.rows().iter().map(|r| r.id.clone()).collect();
        cmp(kept_ids == w.at("kept").strs(), "kept".into());
        let want_c: Vec<bool> = w.at("c").arr().iter().map(|x| x.b()).collect();
        cmp(c.all() == &want_c[..], "concluded".into());
        for (now, a) in nows.iter().copied().zip(w.at("a").arr()) {
            let ret = retained(&c, now);
            let lv: String = keys.iter().filter(|k| live(&c, k, now)).cloned().collect();
            cmp(lv == a.at("live").s(), format!("live at {now}"));
            let en: String = keys.iter().filter(|k| ended(&c, k, now)).cloned().collect();
            cmp(en == a.at("ended").s(), format!("ended at {now}"));
            let succ: Vec<J> = keys
                .iter()
                .filter_map(|k| {
                    successor(&c, k, Some(&ret), &std::collections::BTreeSet::new())
                        .map(|s| J::Arr(vec![J::Str(k.clone()), J::Str(s)]))
                })
                .collect();
            cmp(succ == a.at("succ").arr(), format!("successor at {now}"));
            let edges: Vec<(String, String)> = c
                .cs()
                .iter()
                .copied()
                .filter(|i| ret.contains(i))
                .map(|i| c.g.row(i))
                .filter(|r| r.kind == "edge")
                .filter_map(|r| r.fs("to").map(|t| (r.signer.clone(), t.to_string())))
                .filter(|(s, t)| live(&c, s, now) && live(&c, t, now))
                .collect();
            for (p, wr) in parties.iter().zip(a.at("reach").arr()) {
                let r: String = derived::reach(p, keys.len() + 1, &edges).into_iter().collect();
                cmp(wr.arr()[1].s() == r, format!("reach of {p} at {now}"));
            }
            for (s, ws) in subjects.iter().zip(a.at("score").arr()) {
                let sc: std::collections::BTreeSet<String> = c
                    .cs()
                    .iter()
                    .copied()
                    .filter(|&i| counts(&c, i)) // a count reads the end rule, never what is retained
                    .map(|i| c.g.row(i))
                    .filter(|r| r.kind == "att" && r.fs("about") == Some(s.as_str()))
                    .map(|r| r.signer.clone())
                    .collect();
                cmp(ws.arr()[1].s() == sc.into_iter().collect::<String>(), format!("score of {s} at {now}"));
            }
            let ret_ids = sorted_ids(ret.iter().map(|&i| &c.g.row(i).id));
            cmp(ret_ids == a.at("ret").strs(), format!("retained at {now}"));
            let byt = bytes_retained(&c, now);
            let byt_ids = sorted_ids(byt.iter().map(|&i| &c.g.row(i).id));
            cmp(byt_ids == a.at("bytes").strs(), format!("bytes retained at {now}"));
        }
    }
    // the stub pin (K14): stubs keeping only id, signer, names and at give every counts_by answer of the full rows
    let pin = fx.at("pin");
    for which in ["rows", "stubs"] {
        let rows = rows_of(pin.at(which).arr());
        let c = conclude(kept(&rows, |_| true), conclude_rule, None);
        for a in pin.at("answers").arr() {
            let (row, key, want) = (a.arr()[0].s().to_string(), a.arr()[1].s().to_string(), a.arr()[2].b());
            let got = c.g.idx(&row).is_some_and(|i| ciris_kernel::key_end::counts_by(&c, i, &key));
            cases += 1;
            if got != want {
                bad += 1;
                eprintln!("stub pin ({which}): counts_by({row}, {key}) = {got}");
            }
        }
    }
    report("a key's own end (check_key_end.py worlds)", cases, bad);
    assert_eq!(bad, 0);
}
