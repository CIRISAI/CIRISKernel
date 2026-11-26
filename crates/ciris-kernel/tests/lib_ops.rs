//! Differential: the operators of `models/kernel_lib/kernel_lib.py` over every small input, and the six
//! decisions of `models/kernel_lib/reexpress.py` written again with the crate's operators only
//! (fixtures `lib.json`, `reexpress.json`).

mod common;
use ciris_kernel::ops::{self, Tie};
use ciris_kernel::ranked::{ranked, runoff};
use common::*;
use std::collections::{BTreeMap, BTreeSet};

#[derive(Clone, Debug, PartialEq)]
struct V {
    id: String,
    v: i64,
    p: String,
}

#[test]
fn reducers_and_interval() {
    let fx = fixture("lib.json");
    let (mut cases, mut bad) = (0, 0);
    let mut cmp = |ok: bool, what: &str| {
        cases += 1;
        if !ok {
            bad += 1;
            eprintln!("{what}");
        }
    };
    for c in fx.at("reduce").arr() {
        let rows: Vec<V> = c
            .at("rows")
            .arr()
            .iter()
            .map(|r| V { id: r.at("id").s().into(), v: r.at("v").i(), p: r.at("p").s().into() })
            .collect();
        let refs: Vec<&V> = rows.iter().collect();
        let row_j = |r: Result<Option<&V>, Tie>| match r {
            Err(Tie) => J::Str("Tie".into()),
            Ok(None) => J::Null,
            Ok(Some(r)) => J::Obj(
                [("id", J::Str(r.id.clone())), ("v", J::Int(r.v)), ("p", J::Str(r.p.clone())), ("t", J::Int(0))]
                    .into_iter()
                    .map(|(k, v)| (k.to_string(), v))
                    .collect(),
            ),
        };
        cmp(row_j(ops::least(&refs, |r| r.v)) == *c.at("least"), "least");
        cmp(row_j(ops::greatest(&refs, |r| r.v)) == *c.at("greatest"), "greatest");
        let oi = |x: Option<i64>| x.map_or(J::Null, J::Int);
        cmp(oi(ops::min_of(rows.iter().map(|r| r.v))) == *c.at("min"), "min");
        cmp(oi(ops::max_of(rows.iter().map(|r| r.v))) == *c.at("max"), "max");
        cmp(oi(ops::one(rows.iter().map(|r| r.v))) == *c.at("one"), "one");
        cmp(ops::count(rows.iter().map(|r| r.v)) as i64 == c.at("count").i(), "count");
        cmp(ops::sum_per(rows.iter().map(|r| (r.p.clone(), r.v))) as i64 == c.at("sum").i(), "sum");
        let by: BTreeMap<String, J> = ops::group_by(rows.iter(), |r| r.id.clone())
            .into_iter()
            .map(|(k, rs)| (k, J::Int(ops::count(rs.iter().map(|r| r.v)) as i64)))
            .collect();
        cmp(J::Obj(by) == *c.at("by_id_count"), "group count");
    }
    for c in fx.at("in_range").arr() {
        let a = c.arr();
        let o = |j: &J| if j.is_null() { None } else { Some(j.i()) };
        let (x, lo, hi) = (o(&a[0]), o(&a[1]), o(&a[2]));
        cmp(ops::in_range(x.as_ref(), lo.as_ref(), hi.as_ref()) == a[3].b(), "in_range");
    }
    report("kernel_lib operators", cases, bad);
    assert_eq!(bad, 0);
}

struct H {
    k: String,
    t: i64,
    m: BTreeMap<String, J>,
}

fn hs(j: &J) -> Vec<H> {
    j.arr()
        .iter()
        .map(|r| H { k: r.at("k").s().into(), t: r.get("t").map_or(0, |x| x.i()), m: r.obj().clone() })
        .collect()
}

/// `reexpress.takedown`
fn takedown(h: &[H], now: i64, w: i64, hold_wins: bool) -> &'static str {
    let basis: BTreeMap<&str, &str> = [("imm", "immediate"), ("win", "windowed")].into_iter().collect();
    let hold_from = ops::min_of(ops::sel(h, |r| r.k == "hold").iter().map(|r| r.t));
    let hold_to = ops::min_of(ops::sel(h, |r| r.k == "hold_lifted").iter().map(|r| r.t));
    let (mut destroyed, mut live_notice) = (false, false);
    for n in ops::sel(h, |r| r.k == "notice") {
        let b = n.m["basis"].s();
        let (mut at, undone);
        if ops::rule(&basis, &b) == Some(&"immediate") {
            at = Some(n.t);
            undone = false;
        } else {
            let close = n.t + w;
            undone = !ops::sel_before(h, Some(&close), |r| r.t, |r| r.k == "reversal" || r.k == "lift").is_empty();
            at = if !undone && ops::in_range(Some(&now), Some(&close), None) { Some(close) } else { None };
        }
        if hold_wins && ops::in_range(at.as_ref(), hold_from.as_ref(), hold_to.as_ref()) {
            at = hold_to;
        }
        destroyed |= at.is_some();
        live_notice |= !undone;
    }
    if destroyed {
        "destroyed"
    } else if live_notice {
        "withheld"
    } else {
        "served"
    }
}

/// `reexpress.deletion`
fn deletion(h: &[H], now: i64, w: i64) -> &'static str {
    let Some(start) = ops::min_of(ops::sel(h, |r| r.k == "start").iter().map(|r| r.t)) else { return "none" };
    if !ops::sel_before(h, Some(&(start + w)), |r| r.t, |r| r.k == "excuse").is_empty() {
        return "met";
    }
    if ops::in_range(Some(&now), Some(&(start + w)), None) {
        "breach"
    } else {
        "running"
    }
}

/// `reexpress.owner_of`
fn owner_of(h: &[H]) -> Option<String> {
    let x = |r: &H| r.m.get("x").map(|x| x.s().to_string());
    let live: Vec<&H> = ops::sel(h, |r| r.k == "bind" && r.m.get("cos") == Some(&J::Bool(true)))
        .into_iter()
        .filter(|b| ops::sel(h, |r| r.k == "withdraw" && x(r) == x(b)).is_empty())
        .collect();
    ops::one(live.iter().filter_map(|r| x(r)))
}

/// `reexpress.guardianship`
fn guardianship(h: &[H], band: Option<&str>) -> J {
    let (voices_k, unless): (Vec<&str>, Vec<(&str, &str)>) = match band {
        Some("13_15") => (vec!["order_minor", "order_displaced"], vec![]),
        Some("16_17") => (vec!["order_minor", "order_displaced"], vec![("order_displaced", "refusal")]),
        _ => (vec!["order_displaced"], vec![]),
    };
    let unless: BTreeMap<&str, &str> = unless.into_iter().collect();
    let has = |k: &str| !ops::sel(h, |r| r.k == k).is_empty();
    let voices: Vec<&H> = ops::sel(h, |r| voices_k.contains(&r.k.as_str()))
        .into_iter()
        .filter(|v| !has(ops::rule(&unless, &v.k.as_str()).copied().unwrap_or("-")))
        .collect();
    let order =
        has("order_named") && ops::in_range(Some(&ops::count(voices.iter().map(|v| v.k.clone()))), Some(&1), None);
    let (stepped, bound) = (has("step_down"), has("bind_named"));
    let guardian = if (order || stepped) && bound {
        "named"
    } else if stepped {
        "none"
    } else {
        "current"
    };
    let contested = (has("order_minor") || has("order_displaced") || has("order_named")) && !order && !stepped;
    let act = match guardian {
        "current" => "act_displaced",
        "named" => "act_named",
        _ => "-",
    };
    let acts: BTreeSet<String> =
        if contested { BTreeSet::new() } else { ops::sel(h, |r| r.k == act).iter().map(|a| a.k.clone()).collect() };
    let mode = if guardian == "none" {
        "stopped"
    } else if contested {
        "floor"
    } else {
        "normal"
    };
    J::Obj(
        [
            ("guardian", J::Str(guardian.into())),
            ("contested", J::Bool(contested)),
            ("mode", J::Str(mode.into())),
            ("report", J::Bool(contested)),
            ("acts", J::Arr(acts.into_iter().map(J::Str).collect())),
        ]
        .into_iter()
        .map(|(k, v)| (k.to_string(), v))
        .collect(),
    )
}

/// `reexpress.set_item`
fn set_item(h: &[H], leaf: &str, a: i64, w: i64) -> bool {
    let f = |r: &H, k: &str| r.m.get(k).map(|x| x.s().to_string());
    let header: BTreeMap<String, String> = ops::group_by(ops::sel(h, |r| r.k == "header"), |r| f(r, "item").unwrap())
        .into_iter()
        .filter_map(|(item, rs)| ops::one(rs.iter().map(|r| f(r, "digest").unwrap())).map(|d| (item, d)))
        .collect();
    for l in ops::sel(h, |r| r.k == "leaf" && f(r, "n").as_deref() == Some(leaf)) {
        let mut parts: Vec<&H> = vec![l];
        parts.extend(ops::sel(h, |r| {
            r.k == "header" && f(r, "item") == f(l, "item") && f(r, "digest") == f(l, "digest")
        }));
        let latest = ops::max_of(parts.iter().map(|r| r.t));
        // `ALWAYS` is an interval opened at the beginning: every instant lies above it
        if ops::rule(&header, &f(l, "item").unwrap()) == f(l, "digest").as_ref()
            && latest.is_some_and(|t| t < a + w + 1)
        {
            return true;
        }
    }
    false
}

#[test]
fn reexpressed_decisions() {
    let fx = fixture("reexpress.json");
    let mut per: BTreeMap<&str, (usize, usize)> = BTreeMap::new();
    let mut cmp = |name: &'static str, ok: bool| {
        let e = per.entry(name).or_default();
        e.0 += 1;
        if !ok {
            e.1 += 1;
        }
    };
    for c in fx.at("takedown").arr() {
        let got = takedown(&hs(c.at("H")), c.at("now").i(), c.at("W").i(), c.at("hold_wins").b());
        cmp("takedown", got == c.at("got").s());
    }
    for c in fx.at("deletion").arr() {
        cmp("deletion", deletion(&hs(c.at("H")), c.at("now").i(), c.at("W").i()) == c.at("got").s());
    }
    for c in fx.at("owner_of").arr() {
        cmp("owner_of", owner_of(&hs(c.at("H"))) == c.at("got").opt_s());
    }
    for c in fx.at("guardianship").arr() {
        let band = c.at("band").opt_s();
        cmp("guardianship", guardianship(&hs(c.at("H")), band.as_deref()) == *c.at("got"));
    }
    for c in fx.at("ranked").arr() {
        let rows: Vec<(String, Vec<String>)> =
            c.at("rows").arr().iter().map(|r| (r.arr()[0].s().to_string(), r.arr()[1].strs())).collect();
        let (w, rounds) = ranked(&rows, &c.at("options").strs(), 2, c.at("declared").b());
        cmp("ranked", w == c.at("winner").opt_s() && rounds as i64 == c.at("rounds").i());
        let order = runoff(&rows, &c.at("options").strs(), 2, c.at("declared").b());
        cmp("runoff", order == c.at("order").strs() && order.first().cloned() == w);
    }
    for c in fx.at("set_item").arr() {
        let got = set_item(&hs(c.at("H")), c.at("leaf").s(), c.at("A").i(), c.at("W").i());
        cmp("set_item", got == c.at("got").b());
    }
    let (mut n, mut b) = (0, 0);
    for (k, (cn, cb)) in &per {
        eprintln!("  {k}: {cn} cases, {cb} differ");
        n += cn;
        b += cb;
    }
    report("reexpress.py decisions over the operators", n, b);
    assert_eq!(b, 0);
}
