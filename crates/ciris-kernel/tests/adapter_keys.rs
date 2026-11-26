//! A guard on the fixture replay: every key a fixture row carries is read somewhere by the test adapter that
//! replays it. A row accessor with a default body (`None`, `false`) that the adapter never implements makes the
//! crate's rule unreachable while the Python reads the field, so the replay passes silently (`regime` was so,
//! until the binding's step 5). A key no adapter names fails here, and is then read, or listed in `IGNORED`.

mod common;
use common::{fixture, J};
use std::collections::BTreeSet;

/// Keys no rule reads by design: the model's own bookkeeping, carried for the reader of the fixture.
const IGNORED: [&str; 2] = ["family", "id"];

/// Each fixture whose rows a crate rule reads, with the sources of the adapters that read them. (`tables.json`
/// replays recorded verdicts, not its rows.)
const FIXTURES: [(&str, &[&str]); 6] = [
    ("seat.json", &[include_str!("common/mod.rs"), include_str!("seat.rs")]),
    ("acts.json", &[include_str!("common/mod.rs"), include_str!("acts.rs")]),
    ("conferral_two.json", &[include_str!("conferral_two.rs")]),
    ("conferral_end.json", &[include_str!("conferral_end.rs")]),
    ("conferral_content.json", &[include_str!("content.rs")]),
    ("conferral_content_worlds.json", &[include_str!("content.rs")]),
];

/// The keys of every row in `j`: an object with an `id` and a `kind` (or `k`).
fn row_keys(j: &J, out: &mut BTreeSet<String>) {
    match j {
        J::Obj(m) => {
            if m.contains_key("id") && (m.contains_key("kind") || m.contains_key("k")) {
                out.extend(m.keys().cloned());
            }
            m.values().for_each(|v| row_keys(v, out));
        }
        J::Arr(a) => a.iter().for_each(|x| row_keys(x, out)),
        _ => {}
    }
}

#[test]
fn every_row_key_is_read_by_an_adapter() {
    for (f, readers) in FIXTURES {
        let mut keys = BTreeSet::new();
        row_keys(&fixture(f), &mut keys);
        let unread: Vec<&String> = keys
            .iter()
            .filter(|k| !IGNORED.contains(&k.as_str()))
            .filter(|k| !readers.iter().any(|src| src.contains(&format!("\"{k}\""))))
            .collect();
        assert!(unread.is_empty(), "{f}: row keys no adapter reads: {unread:?}");
    }
}
