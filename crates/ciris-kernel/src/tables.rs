//! **tables**: the seat law's table cells from the Constitution's tables (`seat.py`'s `law_from_tables`).
//!
//! The caller decodes the acts table (`governance_policy_acts.tsv`) into [`ActsRow`]s and the governance policy table
//! into [`PolicyRow`]s and [`ProtocolRow`]s, unchanged; [`law_from_tables`] gives the [`SeatLaw`] cells those tables
//! state: `policy`, `acts` and `removal_floor`. The crate embeds no table and parses none. The rest of the law
//! (duties, holds, confers, ends, final scopes, roster seats, depth, kinds) is the text's, stated by no table; the
//! caller sets it. A window's table from its row is [`crate::window::spec_from_policy`].

use crate::seat::{Act, ActRule, Choice, CommunityKind, Policy, ScopeClass, SeatLaw};
use crate::window::PolicyRow;
use alloc::string::String;
use alloc::vec::Vec;

/// One row of the acts table, its columns as the table writes them.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct ActsRow {
    /// `act`.
    pub act: String,
    /// `scope`: the scope class.
    pub scope: String,
    /// `community_kind`.
    pub community_kind: String,
    /// `policy`: the rows the act may take, joined by `|`; rows joined by `&` must all be met.
    pub policy: String,
    /// `choice`: `fixed` or `row`.
    pub choice: String,
    /// `cc_ref`: carried, no law cell.
    pub cc_ref: String,
}

/// One protocol kind of the policy table's `protocols.kinds`: its `kind` and its `rule` (the other columns state the
/// removal and the votes by set size, which the seat reads from [`crate::seat::RoomProtocol`], not from this).
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct ProtocolRow {
    /// `founder_only`, `unanimous`, `majority`, `quorum:{m}/{n}`, `weighted:{rubric}`.
    pub kind: String,
    /// `role_at:founder:1`, `all`, `strict_majority`, `voices:{m}`, `weight:{rubric}`.
    pub rule: String,
}

/// Why a cell stops the tables giving the law.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum LawWhy {
    /// A word the law does not read.
    Unknown,
    /// A second acts row for one act, scope and kind.
    Duplicate,
    /// A policy the acts table names that the policy table has no row for.
    NoRow,
    /// Two cells of a row disagree.
    Disagrees,
}

/// A cell that stops the tables giving the law: the table (`policy`, `protocols`, `acts`), the row (a family, a
/// protocol kind, or `act|scope|kind`), the cell, and why.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct LawRefusal {
    /// `policy`, `protocols` or `acts`.
    pub table: &'static str,
    /// The row.
    pub row: String,
    /// The cell.
    pub cell: &'static str,
    /// Why.
    pub why: LawWhy,
}

/// The count CC states for a family whose enact cell is not its seat count: CC 4.5.4 (iv) for `duty_confer` and
/// `duty_withdraw` (over the duty holders, the other duty holders); CC 4.5.13 for `moderation_overturn` (the members'
/// check as a counted row).
fn stated_count(family: &str) -> Option<Policy> {
    match family {
        "duty_confer" => Some(Policy::DutyConfer),
        "duty_withdraw" => Some(Policy::DutyWithdraw),
        "moderation_overturn" => Some(Policy::Lift),
        _ => None,
    }
}

/// The [`SeatLaw`] cells the tables state, every other cell left at its default; or every cell that stops them.
///
/// - `policy`, per family, its `enact_rule` as the reference reads it: a fraction of 1/2 a strict majority (CC
///   3.3.6.4), another at least the fraction; `strict_majority` [`Policy::Strict`]`(1, 2)`; `one_of_n` one;
///   `protocol` the room's declared protocol; `ranked_irv` the ranked tally; any other not a count. `duty_confer`,
///   `duty_withdraw` and `moderation_overturn` take the count the text states ([`Policy::DutyConfer`],
///   [`Policy::DutyWithdraw`], [`Policy::Lift`]); `moderator_recall` is [`Policy::Recall`] of its enact fraction and
///   its floor's voices (CC 4.5.13: "more than two thirds of the standing roster ... The floor is two voices").
/// - `policy`, per protocol, `P:{kind}` (the kind's word before `:`): `strict_majority`, `all` (unanimous),
///   `voices:{m}` (declared: the record's m), `weight:{rubric}` (weighted), `role_at:founder:1` (one).
/// - `acts`: one [`ActRule`] per acts row, each word read by its `from_word`; a policy name must be a family.
/// - `removal_floor`: `community_remove`'s `floor_rule` voices.
pub fn law_from_tables(
    acts: &[ActsRow],
    families: &[PolicyRow],
    protocols: &[ProtocolRow],
) -> Result<SeatLaw, Vec<LawRefusal>> {
    let mut why = Vec::new();
    let mut no = |table: &'static str, row: &str, cell: &'static str, w: LawWhy| {
        why.push(LawRefusal { table, row: row.into(), cell, why: w })
    };
    let mut law = SeatLaw::default();
    for f in families {
        let e = &f.enact_rule;
        let p = if let Some(p) = stated_count(&f.family) {
            p
        } else if f.family == "moderator_recall" {
            let fl = &f.floor_rule;
            match (e.kind.as_str(), e.num, e.den, fl.kind.as_str(), fl.count) {
                ("fraction", Some(n), Some(d), "voices", Some(c)) => Policy::Recall(n, d, c),
                _ => {
                    no("policy", &f.family, "floor_rule", LawWhy::Disagrees);
                    continue;
                }
            }
        } else {
            match (e.kind.as_str(), e.num, e.den) {
                ("fraction", Some(1), Some(2)) => Policy::Strict(1, 2),
                ("fraction", Some(n), Some(d)) => Policy::AtLeast(n, d),
                ("strict_majority", ..) => Policy::Strict(1, 2),
                ("one_of_n", ..) => Policy::One,
                ("protocol", ..) => Policy::Protocol,
                ("ranked_irv", ..) => Policy::Ranked,
                _ => Policy::NotACount,
            }
        };
        law.policy.insert(f.family.clone(), p);
    }
    for p in protocols {
        let name = alloc::format!("P:{}", p.kind.split(':').next().unwrap_or(""));
        let got = match p.rule.as_str() {
            "strict_majority" => Some(Policy::Strict(1, 2)),
            "all" => Some(Policy::Unanimous),
            "role_at:founder:1" => Some(Policy::One),
            r if r.starts_with("voices:") => Some(Policy::Declared),
            r if r.starts_with("weight:") => Some(Policy::Weighted),
            _ => None,
        };
        match got {
            Some(g) => {
                law.policy.insert(name, g);
            }
            None => no("protocols", &p.kind, "rule", LawWhy::Unknown),
        }
    }
    let mut rules = Vec::new();
    let mut seen: Vec<(&str, &str, &str)> = Vec::new();
    for a in acts {
        let key = alloc::format!("{}|{}|{}", a.act, a.scope, a.community_kind);
        let act = Act::from_word(&a.act);
        let scope = ScopeClass::from_word(&a.scope);
        let kind = CommunityKind::from_word(&a.community_kind);
        let choice = Choice::from_word(&a.choice);
        for (cell, ok) in [
            ("act", act.is_some()),
            ("scope", scope.is_some()),
            ("community_kind", kind.is_some()),
            ("choice", choice.is_some()),
        ] {
            if !ok {
                no("acts", &key, cell, LawWhy::Unknown);
            }
        }
        let k = (a.act.as_str(), a.scope.as_str(), a.community_kind.as_str());
        if seen.contains(&k) {
            no("acts", &key, "act", LawWhy::Duplicate);
        }
        seen.push(k);
        let policies: Vec<String> = a.policy.split('|').map(String::from).collect();
        for p in &policies {
            for q in p.split('&') {
                if !families.iter().any(|f| f.family == q) {
                    no("acts", &key, "policy", LawWhy::NoRow);
                }
            }
        }
        if let (Some(act), Some(scope), Some(kind), Some(choice)) = (act, scope, kind, choice) {
            rules.push(ActRule { act, scope, kind, policies, choice });
        }
    }
    law.acts = Some(rules);
    let rf = families.iter().find(|f| f.family == "community_remove").map(|f| &f.floor_rule);
    match rf {
        Some(r) if r.kind == "voices" && r.count.is_some() => law.removal_floor = r.count.unwrap_or(0) as usize,
        _ => no("policy", "community_remove", "floor_rule", LawWhy::Unknown),
    }
    if why.is_empty() {
        Ok(law)
    } else {
        Err(why)
    }
}
