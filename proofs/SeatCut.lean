/-
  SeatCut.lean — an act under a seat follows the cut; the members at a head stay by past

  CC 2.4.1.1 (ruled 2026-11-21): "A withdraws row retires its target as a cut does (CC 2.7.7). An act
  under the target that the withdrawal has among its ancestors stands. One that has the withdrawal in its
  own past, or is concurrent with it, does not count." The same holds of an unseat and of a resignation
  (the holder's own withdrawal). The kernel's answer is `seat::exercised_stands` (`seat.py`): act x, which
  k exercises under its seat, stands iff
    (a) the seat walk over x's own past seats k, and
    (b) no counting ending cut on the seat is concurrent with x.

  THE MODEL. Over a `RosterHead.Lineage` (what rows name, well-founded), an `Ending` gives the two things
  the answer reads beyond the lineage: `seated P x k`, the walk over x's past, which is any function of the
  rows strictly in x's past (`walk_local`), and `ends P w k`, that row w is a counting ending cut on k's
  seat (which cuts count is the rule-4 fixed point, CutFix.lean, and is left abstract here).

  Proved here.
   (1) `in_past_stands`, `walk_ignores_later`: an act in the withdrawal's past stands, and the walk at it
       is the same with the withdrawal held or not.
   (2) `concurrent_does_not_stand`: an act concurrent with a counting ending cut does not stand, whatever
       the walk says.
   (3) `members_ignore_outside`, `cut_acts_members_hold`: the members at a head (RosterHead's `mem`, and
       whether a version stands) are the same with any rows outside the head's past held or not, ending
       cuts included. So with a withdrawal concurrent with an act, the act does not stand while the members
       at every head in the act's past are those without the withdrawal.
   (4) `named_cut_does_not_stand`: an act naming an ending cut does not stand when the walk honours the
       cuts in its past (`honours`, a hypothesis on the walk: the kernel's walk reads the withdrawal).

  Core Lean 4.14, no Mathlib, no `sorry`, no axioms beyond core. Imports RosterHead.lean.
-/

import RosterHead

namespace Kernel

namespace SeatCut

open Relation RosterHead

variable {Row Key : Type} (L : Lineage Row Key)

/-- `a` and `b` are concurrent: neither is the other or in its past. -/
def conc (a b : Row) : Prop := ¬ pastOrSelf L a b ∧ ¬ pastOrSelf L b a

/-- What the answer reads beyond the lineage. -/
structure Ending (L : Lineage Row Key) where
  /-- The seat walk over `x`'s own past seats `k`. -/
  seated : (Row → Prop) → Row → Key → Prop
  /-- The walk reads only the rows strictly in `x`'s past. -/
  walk_local : ∀ P P' x k, (∀ r, TransGen L.parent r x → (P r ↔ P' r)) → (seated P x k ↔ seated P' x k)
  /-- Row `w` is a counting ending cut on `k`'s seat (a withdrawal, an unseat, a resignation). -/
  ends : (Row → Prop) → Row → Key → Prop

variable (E : Ending L)

/-- Act `x`, exercised by `k` under its seat, stands: (a) and (b). -/
def exercised (P : Row → Prop) (x : Row) (k : Key) : Prop :=
  E.seated P x k ∧ ∀ w, P w → E.ends P w k → ¬ conc L w x

/-- What rows name has no cycle. -/
theorem no_cycle (a : Row) : ¬ TransGen L.parent a a := by
  have w : WellFounded (TransGen L.parent) := WellFounded.transGen L.wf
  induction a using WellFounded.induction w with | _ a ih => exact fun h => ih a h h

theorem asymm (a b : Row) (h1 : TransGen L.parent a b) (h2 : TransGen L.parent b a) : False :=
  no_cycle L a (TransGen.trans h1 h2)

/-- (1) THE WALK IGNORES A LATER ROW. A row that has `x` in its past is not in `x`'s past, so holding it
    changes nothing in the walk at `x`. -/
theorem walk_ignores_later (P : Row → Prop) (x W : Row) (k : Key) (hx : TransGen L.parent x W) :
    E.seated P x k ↔ E.seated (fun r => P r ∨ r = W) x k := by
  apply E.walk_local
  intro r hr
  refine ⟨Or.inl, fun h => h.elim id (fun e => ?_)⟩
  subst e
  exact absurd (asymm L x r hx hr) id

/-- (1) AN ACT IN THE WITHDRAWAL'S PAST STANDS: the withdrawal is not concurrent with it, so it is no
    obstacle; with the walk seating `k` and no other ending cut concurrent, the act stands. -/
theorem in_past_stands (P : Row → Prop) (x W : Row) (k : Key) (hx : TransGen L.parent x W)
    (hs : E.seated P x k) (hothers : ∀ w, P w → E.ends P w k → w ≠ W → ¬ conc L w x) :
    exercised L E P x k := by
  refine ⟨hs, fun w hw he hc => ?_⟩
  by_cases e : w = W
  · subst e
    exact hc.2 (Or.inr hx)
  · exact hothers w hw he e hc

/-- (2) A CONCURRENT ACT DOES NOT STAND. -/
theorem concurrent_does_not_stand (P : Row → Prop) (x W : Row) (k : Key) (hW : P W)
    (he : E.ends P W k) (hc : conc L W x) : ¬ exercised L E P x k :=
  fun h => h.2 W hW he hc

/-- (4) AN ACT NAMING THE CUT does not stand, where the walk honours the ending cuts in its past. -/
theorem named_cut_does_not_stand (P : Row → Prop) (x W : Row) (k : Key) (hW : P W)
    (he : E.ends P W k) (hn : TransGen L.parent W x)
    (honours : ∀ w, P w → E.ends P w k → TransGen L.parent w x → ¬ E.seated P x k) :
    ¬ exercised L E P x k :=
  fun h => honours W hW he hn h.1

/-- (3) THE MEMBERS AT A HEAD IGNORE ROWS OUTSIDE ITS PAST, ending cuts included (RosterHead). -/
theorem members_ignore_outside (P X : Row → Prop) (h : Row) (hX : ∀ r, X r → ¬ pastOrSelf L r h) :
    (standsV L P h ↔ standsV L (fun r => P r ∨ X r) h) ∧
      ∀ k, mem L P h k ↔ mem L (fun r => P r ∨ X r) h k :=
  rows_outside_change_nothing L P X h hX

/-- (3) THE CUT ACTS, THE MEMBERS HOLD. Let ending cut `W` be concurrent with act `x`. Then `x` does not
    stand, while at every head `h` in `x`'s past (or `x` itself as a head) the members, and whether the
    version stands, are the same with `W` held or not. -/
theorem cut_acts_members_hold (P : Row → Prop) (x W h : Row) (k : Key) (hW : P W)
    (he : E.ends P W k) (hc : conc L W x) (hh : pastOrSelf L h x) :
    ¬ exercised L E P x k ∧
      (standsV L P h ↔ standsV L (fun r => P r ∨ r = W) h) ∧
      ∀ k', mem L P h k' ↔ mem L (fun r => P r ∨ r = W) h k' := by
  refine ⟨concurrent_does_not_stand L E P x W k hW he hc, ?_⟩
  apply members_ignore_outside L P (fun r => r = W) h
  intro r e hr
  subst e
  -- r is in h's past and h in x's: r is in x's past, which concurrency denies
  apply hc.1
  cases hh with
  | inl e => exact e ▸ hr
  | inr t =>
    cases hr with
    | inl e => exact Or.inr (e ▸ t)
    | inr t' => exact Or.inr (TransGen.trans t' t)

end SeatCut

#print axioms SeatCut.no_cycle
#print axioms SeatCut.asymm
#print axioms SeatCut.walk_ignores_later
#print axioms SeatCut.in_past_stands
#print axioms SeatCut.concurrent_does_not_stand
#print axioms SeatCut.named_cut_does_not_stand
#print axioms SeatCut.members_ignore_outside
#print axioms SeatCut.cut_acts_members_hold

end Kernel
