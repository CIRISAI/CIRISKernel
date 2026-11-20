/-
  Repurge.lean — repeated purges, by composition

  The question. `Settled.lean` Part 10 proves one purge safe: the pruned view of one act is closed
  under every admissible extension (`pruned_view_closed`). CC 2.7.10 lets a node purge again, and
  purge for many acts. `check_purge.py` runs a store purged again after each part of an extension
  has arrived; that was run, not proved. This file proves it, by one rule: closed views compose.

  What this file proves.
    Part 1  Composition. If `v` is closed under the steps `T` with the coarse law `h`, and `w` is
            closed under `h`, then `w ∘ v` is closed under `T` (`closedBy_comp`), and along any
            list of steps the coarse run is the fine run read through the view (`closedBy_run`).
    Part 2  One purge, any act. For an answer `B` monotone in the rows held and a set `D` of rows
            dropped once `B` holds, the purge view is closed under adding rows (`purge_closedBy`).
            `Settled.prunedView` is the case `D` = every row (`prunedView_is_purgeView`).
    Part 3  The same purge again, at any time. Purging a stub again changes nothing
            (`repurge_purgeView`), so under every schedule of extensions and repeated purges the
            stub is the purge of the full store (`any_schedule`), and its answers are the full
            store's (`schedule_answers`).
    Part 4  Two acts, one purge after the other. The second purge is a view of the first one's
            stub. It is closed under the first purge's law when each act's answer reads no row the
            other's purge may drop (`second_closedBy`); then the two together are closed under
            adding rows (`two_purges_closedBy`, `two_purges_run`), they read what the full store
            reads (`two_purges_read`), and the order of the two purges does not matter
            (`two_purges_commute`).
    Part 5  The condition is needed. Where one act's answer reads a row the other's purge drops
            (a receipt the two acts share), the second purge, judged on the stub, reads the act
            unsettled while the full store reads it settled (`shared_drop_misreads`).

  Not proved here. Purges of three or more acts (each further purge is one more application of
  `closedBy_comp`, with the condition of Part 4 for each pair, not mechanized); that the kernel's
  `blocked` answers meet the condition of Part 4 (it is a property of the rule tables: a receipt
  row naming two acts breaks it, and Part 5 is that case); the least set to keep.

  Native to this repository: not carried from the parent, which has no counterpart.

  Core Lean 4.14, no Mathlib, no `sorry`, no axioms beyond core. Imports Settled.lean.
-/

import Settled

namespace Kernel

namespace Repurge

open Settled

/-! ## Part 1. Composition of closed views -/

section Compose

variable {α β γ ι : Type}

/-- `v` is closed under the steps `T` with the coarse law `h`. -/
def ClosedBy (v : α → β) (T : ι → α → α) (h : ι → β → β) : Prop :=
  ∀ i s, v (T i s) = h i (v s)

/-- `Settled.Closed` is the existence of such a law. -/
theorem closed_iff_closedBy (v : α → β) (T : ι → α → α) :
    Closed v T ↔ ∃ h, ClosedBy v T h := Iff.rfl

/-- Closed views compose: a view closed under the coarse law of a closed view is, through it,
    closed under the fine steps. -/
theorem closedBy_comp {v : α → β} {w : β → γ} {T : ι → α → α} {h : ι → β → β}
    {h' : ι → γ → γ} (hv : ClosedBy v T h) (hw : ClosedBy w h h') :
    ClosedBy (fun s => w (v s)) T h' :=
  fun i s => by
    show w (v (T i s)) = h' i (w (v s))
    rw [hv, hw]

theorem closed_comp {v : α → β} {w : β → γ} {T : ι → α → α} {h : ι → β → β}
    (hv : ClosedBy v T h) (hw : Closed w h) : Closed (fun s => w (v s)) T :=
  let ⟨h', hw'⟩ := hw
  ⟨h', closedBy_comp hv hw'⟩

/-- Run a list of steps, first to last. -/
def run (T : ι → α → α) : List ι → α → α
  | [], s => s
  | i :: is, s => run T is (T i s)

/-- Along any list of steps the coarse run is the fine run read through the view. -/
theorem closedBy_run {v : α → β} {T : ι → α → α} {h : ι → β → β} (hv : ClosedBy v T h) :
    ∀ (is : List ι) (s : α), v (run T is s) = run h is (v s)
  | [], _ => rfl
  | i :: is, s => by
    show v (run T is (T i s)) = run h is (h i (v s))
    rw [← hv]
    exact closedBy_run hv is (T i s)

end Compose

/-! ## Part 2. One purge -/

section Purge

variable {Row : Type}

/-- The rows of `H`, with those of `D` dropped when `b` holds. -/
def keep (b : Prop) (D H : Row → Prop) : Row → Prop := fun r => H r ∧ ¬ (b ∧ D r)

/-- An answer that, once true, stays true when rows are added. -/
def Mono (B : (Row → Prop) → Prop) : Prop :=
  ∀ H H' : Row → Prop, Extends H H' → B H → B H'

/-- Two sets of rows that agree outside `D`. -/
def Agree (D H S : Row → Prop) : Prop := ∀ r, ¬ D r → (H r ↔ S r)

/-- `B` reads no row of `D`: two sets agreeing outside `D` give one answer. -/
def Blind (B : (Row → Prop) → Prop) (D : Row → Prop) : Prop :=
  ∀ H S : Row → Prop, Agree D H S → (B H ↔ B S)

theorem keep_false {b : Prop} (hb : ¬ b) (D H : Row → Prop) : keep b D H = H :=
  funext fun _ => propext ⟨fun h => h.1, fun h => ⟨h, fun h' => hb h'.1⟩⟩

theorem keep_keep (b : Prop) (D H : Row → Prop) : keep b D (keep b D H) = keep b D H :=
  funext fun _ => propext ⟨fun h => h.1, fun h => ⟨h, h.2⟩⟩

theorem keep_agree (b : Prop) (D H : Row → Prop) : Agree D (keep b D H) H :=
  fun _ hr => ⟨fun h => h.1, fun h => ⟨h, fun h' => hr h'.2⟩⟩

theorem agree_symm {D H S : Row → Prop} (h : Agree D H S) : Agree D S H :=
  fun r hr => (h r hr).symm

theorem addRows_agree {D H S : Row → Prop} (X : Row → Prop) (h : Agree D H S) :
    Agree D (addRows X H) (addRows X S) :=
  fun r hr => ⟨fun h' => h'.elim (fun a => Or.inl ((h r hr).1 a)) Or.inr,
    fun h' => h'.elim (fun a => Or.inl ((h r hr).2 a)) Or.inr⟩

theorem keep_agree_of_agree {D D' H S : Row → Prop} (b : Prop) (h : Agree D H S) :
    Agree D (keep b D' H) (keep b D' S) :=
  fun r hr => ⟨fun h' => ⟨(h r hr).1 h'.1, h'.2⟩, fun h' => ⟨(h r hr).2 h'.1, h'.2⟩⟩

/-- Once `D` is dropped, sets agreeing outside `D` keep the same rows. -/
theorem keep_eq_of_agree {b : Prop} (hb : b) {D H S : Row → Prop} (h : Agree D H S) :
    keep b D H = keep b D S :=
  funext fun r => propext (by
    by_cases hr : D r
    · exact ⟨fun h' => absurd ⟨hb, hr⟩ h'.2, fun h' => absurd ⟨hb, hr⟩ h'.2⟩
    · exact ⟨fun h' => ⟨(h r hr).1 h'.1, h'.2⟩, fun h' => ⟨(h r hr).2 h'.1, h'.2⟩⟩)

/-- The purge of the rows `D` behind the answer `B`: the answer, and the rows with `D` dropped
    once the answer holds. -/
def purgeView (B : (Row → Prop) → Prop) (D : Row → Prop) (H : Row → Prop) :
    Prop × (Row → Prop) :=
  (B H, keep (B H) D H)

/-- The law the stub follows: add the rows, judge the answer on what the stub holds, drop again. -/
def purgeLaw (B : (Row → Prop) → Prop) (D : Row → Prop) (X : Row → Prop)
    (p : Prop × (Row → Prop)) : Prop × (Row → Prop) :=
  (p.1 ∨ B (addRows X p.2), keep (p.1 ∨ B (addRows X p.2)) D (addRows X p.2))

/-- One purge is closed under every admissible extension, for any monotone answer and any set of
    rows dropped behind it. -/
theorem purge_closedBy {B : (Row → Prop) → Prop} (D : Row → Prop) (hB : Mono B) :
    ClosedBy (purgeView B D) (fun X H => addRows X H) (purgeLaw B D) := by
  intro X H
  have e : B (addRows X H) = (B H ∨ B (addRows X (keep (B H) D H))) := by
    apply propext
    by_cases hb : B H
    · exact ⟨fun _ => Or.inl hb, fun _ => hB H _ (fun _ h => Or.inl h) hb⟩
    · rw [keep_false hb]
      exact ⟨Or.inr, fun h => h.elim (fun h' => absurd h' hb) id⟩
  show (B (addRows X H), keep (B (addRows X H)) D (addRows X H)) =
    (B H ∨ B (addRows X (keep (B H) D H)),
      keep (B H ∨ B (addRows X (keep (B H) D H))) D (addRows X (keep (B H) D H)))
  rw [← e]
  congr 1
  by_cases hb : B H
  · exact keep_eq_of_agree (hB H _ (fun _ h => Or.inl h) hb)
      (agree_symm (addRows_agree X (keep_agree (B H) D H)))
  · rw [keep_false hb]

/-- `Settled.prunedView` is the purge that drops every row once the act is blocked. -/
theorem prunedView_is_purgeView {K : Type} [DecidableEq K] (parent : Row → Row → Prop)
    (sig : Row → K → Prop) (isCutOf isAck : Row → Prop) (act : Row) (M : List K) (q : Nat) :
    prunedView parent sig isCutOf isAck act M q =
      purgeView (blocked parent sig isCutOf isAck act M q) (fun _ => True) :=
  funext fun _ => Prod.ext rfl (funext fun _ => propext
    ⟨fun h => ⟨h.2, fun h' => h.1 h'.1⟩, fun h => ⟨fun hb => h.2 ⟨hb, trivial⟩, h.1⟩⟩)

/-- `blocked` is monotone, so `pruned_view_closed` is an instance of `purge_closedBy`. -/
theorem blocked_mono' {K : Type} [DecidableEq K] (parent : Row → Row → Prop)
    (sig : Row → K → Prop) (isCutOf isAck : Row → Prop) (act : Row) (M : List K) (q : Nat) :
    Mono (blocked parent sig isCutOf isAck act M q) :=
  fun H H' h hb => blocked_mono parent sig isCutOf isAck act M q H H' h hb

/-- `Settled.pruned_view_closed`, recovered as an instance of `purge_closedBy`. -/
theorem pruned_view_closed_again {K : Type} [DecidableEq K] (parent : Row → Row → Prop)
    (sig : Row → K → Prop) (isCutOf isAck : Row → Prop) (act : Row) (M : List K) (q : Nat) :
    Closed (prunedView parent sig isCutOf isAck act M q) (fun X H => addRows X H) := by
  rw [prunedView_is_purgeView]
  exact ⟨_, purge_closedBy _ (blocked_mono' parent sig isCutOf isAck act M q)⟩

end Purge

/-! ## Part 3. The same purge again, at any time -/

section Schedule

variable {Row : Type}

/-- Purge a stub again: judge the answer on the rows it holds and drop behind it. -/
def repurge (B : (Row → Prop) → Prop) (D : Row → Prop) (p : Prop × (Row → Prop)) :
    Prop × (Row → Prop) :=
  (p.1 ∨ B p.2, keep (p.1 ∨ B p.2) D p.2)

/-- Purging a purged store again changes nothing. -/
theorem repurge_purgeView (B : (Row → Prop) → Prop) (D H : Row → Prop) :
    repurge B D (purgeView B D H) = purgeView B D H := by
  show (B H ∨ B (keep (B H) D H), keep (B H ∨ B (keep (B H) D H)) D (keep (B H) D H)) =
    (B H, keep (B H) D H)
  by_cases hb : B H
  · have e : (B H ∨ B (keep (B H) D H)) = B H := propext ⟨fun _ => hb, Or.inl⟩
    rw [e, keep_keep]
  · simp only [keep_false hb, or_self]

/-- A step of a schedule: rows arrive, or the node purges again. -/
inductive Step (Row : Type) where
  | ext (X : Row → Prop)
  | again

/-- The full store under a schedule: it holds every row that arrived. -/
def runFull : List (Step Row) → (Row → Prop) → (Row → Prop)
  | [], H => H
  | .ext X :: ss, H => runFull ss (addRows X H)
  | .again :: ss, H => runFull ss H

/-- The stub under a schedule: it follows the purge law on arrival and purges again when told. -/
def runStub (B : (Row → Prop) → Prop) (D : Row → Prop) :
    List (Step Row) → Prop × (Row → Prop) → Prop × (Row → Prop)
  | [], p => p
  | .ext X :: ss, p => runStub B D ss (purgeLaw B D X p)
  | .again :: ss, p => runStub B D ss (repurge B D p)

/-- Under every schedule of arrivals and repeated purges, the stub is the purge of the full store. -/
theorem any_schedule {B : (Row → Prop) → Prop} (D : Row → Prop) (hB : Mono B) :
    ∀ (ss : List (Step Row)) (H : Row → Prop),
      runStub B D ss (purgeView B D H) = purgeView B D (runFull ss H)
  | [], _ => rfl
  | .ext X :: ss, H =>
    (congrArg (runStub B D ss) (purge_closedBy D hB X H)).symm.trans
      (any_schedule D hB ss (addRows X H))
  | .again :: ss, H => by
    show runStub B D ss (repurge B D (purgeView B D H)) = purgeView B D (runFull ss H)
    rw [repurge_purgeView]
    exact any_schedule D hB ss H

/-- So the purged store answers as the full one: the same answer, and every row outside `D`, and
    every row at all while the answer does not hold. -/
theorem schedule_answers {B : (Row → Prop) → Prop} (D : Row → Prop) (hB : Mono B)
    (ss : List (Step Row)) (H : Row → Prop) :
    ((runStub B D ss (purgeView B D H)).1 ↔ B (runFull ss H)) ∧
    (∀ r, ¬ D r → ((runStub B D ss (purgeView B D H)).2 r ↔ runFull ss H r)) ∧
    (¬ B (runFull ss H) → ∀ r, ((runStub B D ss (purgeView B D H)).2 r ↔ runFull ss H r)) := by
  rw [any_schedule D hB ss H]
  exact ⟨Iff.rfl, keep_agree _ D _, fun hn r => by
    show keep (B (runFull ss H)) D (runFull ss H) r ↔ _
    rw [keep_false hn]⟩

end Schedule

/-! ## Part 4. Two acts, one purge after the other -/

section Two

variable {Row : Type}
variable (B₁ B₂ : (Row → Prop) → Prop) (D₁ D₂ : Row → Prop)

/-- The second purge, as a view of the first one's stub: the first answer, the second answer
    judged on the stub, and the stub's rows with `D₂` dropped behind it. -/
def second (p : Prop × (Row → Prop)) : Prop × Prop × (Row → Prop) :=
  (p.1, B₂ p.2, keep (B₂ p.2) D₂ p.2)

/-- The law of the twice-purged stub: the first purge's law on what it holds, then the second
    answer judged and `D₂` dropped again. -/
def secondLaw (X : Row → Prop) (p : Prop × Prop × (Row → Prop)) : Prop × Prop × (Row → Prop) :=
  ((purgeLaw B₁ D₁ X (p.1, p.2.2)).1,
   p.2.1 ∨ B₂ (purgeLaw B₁ D₁ X (p.1, p.2.2)).2,
   keep (p.2.1 ∨ B₂ (purgeLaw B₁ D₁ X (p.1, p.2.2)).2) D₂ (purgeLaw B₁ D₁ X (p.1, p.2.2)).2)

/-- The second purge is closed under the first one's law, when each answer reads no row the
    other purge may drop. -/
theorem second_closedBy (hB₂ : Mono B₂) (s₁ : Blind B₁ D₂) (s₂ : Blind B₂ D₁) :
    ClosedBy (second B₂ D₂) (purgeLaw B₁ D₁) (secondLaw B₁ B₂ D₁ D₂) := by
  intro X p
  cases p with
  | mk b K =>
  have hA : Agree D₂ (addRows X (keep (B₂ K) D₂ K)) (addRows X K) :=
    addRows_agree X (keep_agree (B₂ K) D₂ K)
  have e1 : B₁ (addRows X (keep (B₂ K) D₂ K)) = B₁ (addRows X K) := propext (s₁ _ _ hA)
  show ((b ∨ B₁ (addRows X K)),
      B₂ (keep (b ∨ B₁ (addRows X K)) D₁ (addRows X K)),
      keep (B₂ (keep (b ∨ B₁ (addRows X K)) D₁ (addRows X K))) D₂
        (keep (b ∨ B₁ (addRows X K)) D₁ (addRows X K))) =
    ((b ∨ B₁ (addRows X (keep (B₂ K) D₂ K))),
      B₂ K ∨ B₂ (keep (b ∨ B₁ (addRows X (keep (B₂ K) D₂ K))) D₁ (addRows X (keep (B₂ K) D₂ K))),
      keep (B₂ K ∨ B₂ (keep (b ∨ B₁ (addRows X (keep (B₂ K) D₂ K))) D₁
          (addRows X (keep (B₂ K) D₂ K)))) D₂
        (keep (b ∨ B₁ (addRows X (keep (B₂ K) D₂ K))) D₁ (addRows X (keep (B₂ K) D₂ K))))
  rw [e1]
  by_cases hc : B₂ K
  · have h2 : B₂ (keep (b ∨ B₁ (addRows X K)) D₁ (addRows X K)) :=
      (s₂ _ _ (keep_agree _ D₁ _)).2 (hB₂ K _ (fun _ h => Or.inl h) hc)
    have ec : (B₂ K ∨ B₂ (keep (b ∨ B₁ (addRows X K)) D₁ (addRows X (keep (B₂ K) D₂ K)))) = True :=
      propext ⟨fun _ => trivial, fun _ => Or.inl hc⟩
    rw [ec, eq_true h2]
    exact Prod.ext rfl (Prod.ext rfl (keep_eq_of_agree trivial
      (keep_agree_of_agree _ (agree_symm hA))))
  · rw [keep_false hc]
    have ec : (B₂ K ∨ B₂ (keep (b ∨ B₁ (addRows X K)) D₁ (addRows X K))) =
        B₂ (keep (b ∨ B₁ (addRows X K)) D₁ (addRows X K)) :=
      propext ⟨fun h => h.elim (fun h' => absurd h' hc) id, Or.inr⟩
    rw [ec]

/-- Two purges, one after the other, are closed under every admissible extension. -/
theorem two_purges_closedBy (hB₁ : Mono B₁) (hB₂ : Mono B₂) (s₁ : Blind B₁ D₂)
    (s₂ : Blind B₂ D₁) :
    ClosedBy (fun H => second B₂ D₂ (purgeView B₁ D₁ H)) (fun X H => addRows X H)
      (secondLaw B₁ B₂ D₁ D₂) :=
  closedBy_comp (purge_closedBy D₁ hB₁) (second_closedBy B₁ B₂ D₁ D₂ hB₂ s₁ s₂)

/-- Along any list of arrivals, the twice-purged stub run by its own law is the twice-purged full
    store. -/
theorem two_purges_run (hB₁ : Mono B₁) (hB₂ : Mono B₂) (s₁ : Blind B₁ D₂) (s₂ : Blind B₂ D₁)
    (Xs : List (Row → Prop)) (H : Row → Prop) :
    second B₂ D₂ (purgeView B₁ D₁ (run (fun X H => addRows X H) Xs H)) =
      run (secondLaw B₁ B₂ D₁ D₂) Xs (second B₂ D₂ (purgeView B₁ D₁ H)) :=
  closedBy_run (two_purges_closedBy B₁ B₂ D₁ D₂ hB₁ hB₂ s₁ s₂) Xs H

/-- What the two purges read: both answers as the full store gives them, and the rows of the
    full store with each act's dropped rows gone once its answer holds. -/
theorem two_purges_read (s₂ : Blind B₂ D₁) (H : Row → Prop) :
    second B₂ D₂ (purgeView B₁ D₁ H) =
      (B₁ H, B₂ H, fun r => H r ∧ ¬ (B₁ H ∧ D₁ r) ∧ ¬ (B₂ H ∧ D₂ r)) := by
  have e : B₂ (keep (B₁ H) D₁ H) = B₂ H := propext (s₂ _ _ (keep_agree _ D₁ _))
  show (B₁ H, B₂ (keep (B₁ H) D₁ H), keep (B₂ (keep (B₁ H) D₁ H)) D₂ (keep (B₁ H) D₁ H)) = _
  rw [e]
  exact Prod.ext rfl (Prod.ext rfl (funext fun _ => propext
    ⟨fun ⟨⟨a, b⟩, c⟩ => ⟨a, b, c⟩, fun ⟨a, b, c⟩ => ⟨⟨a, b⟩, c⟩⟩))

/-- The order of the two purges does not matter. -/
theorem two_purges_commute (s₁ : Blind B₁ D₂) (s₂ : Blind B₂ D₁) (H : Row → Prop) :
    (second B₂ D₂ (purgeView B₁ D₁ H)).2.2 = (second B₁ D₁ (purgeView B₂ D₂ H)).2.2 ∧
    (second B₂ D₂ (purgeView B₁ D₁ H)).1 = (second B₁ D₁ (purgeView B₂ D₂ H)).2.1 ∧
    (second B₂ D₂ (purgeView B₁ D₁ H)).2.1 = (second B₁ D₁ (purgeView B₂ D₂ H)).1 := by
  rw [two_purges_read B₁ B₂ D₁ D₂ s₂, two_purges_read B₂ B₁ D₂ D₁ s₁]
  exact ⟨funext fun _ => propext
    ⟨fun ⟨a, b, c⟩ => ⟨a, c, b⟩, fun ⟨a, b, c⟩ => ⟨a, c, b⟩⟩, rfl, rfl⟩

end Two

/-! ## Part 5. The condition is needed -/

section Shared

/-- Row 0 is the first act's settling receipt, row 1 a receipt the two acts share. The first
    act's purge drops both; the second act's answer reads row 1. -/
def shH : Nat → Prop := fun r => r = 0 ∨ r = 1
def shB₁ : (Nat → Prop) → Prop := fun H => H 0
def shD₁ : Nat → Prop := fun r => r = 0 ∨ r = 1
def shB₂ : (Nat → Prop) → Prop := fun H => H 1
def shD₂ : Nat → Prop := fun r => r = 1

/-- The second answer reads a row the first purge drops. -/
theorem shared_not_blind : ¬ Blind shB₂ shD₁ := fun h =>
  ((h (fun r => r = 1) (fun _ => False) (fun _ hr => ⟨fun e => hr (Or.inr e), False.elim⟩)).1
    rfl)

/-- Both answers are monotone, so the purge itself is closed; but the second purge, judged on
    the first one's stub, reads the second act unsettled where the full store reads it settled. -/
theorem shared_drop_misreads :
    Mono shB₂ ∧ shB₂ shH ∧ ¬ (second shB₂ shD₂ (purgeView shB₁ shD₁ shH)).2.1 :=
  ⟨fun _ _ h hb => h 1 hb, Or.inr rfl, fun h =>
    have h' : shH 1 ∧ ¬ (shH 0 ∧ shD₁ 1) := h
    h'.2 ⟨Or.inl rfl, Or.inr rfl⟩⟩

end Shared

#print axioms closedBy_comp
#print axioms purge_closedBy
#print axioms any_schedule
#print axioms schedule_answers
#print axioms second_closedBy
#print axioms two_purges_closedBy
#print axioms two_purges_run
#print axioms two_purges_read
#print axioms two_purges_commute
#print axioms prunedView_is_purgeView
#print axioms shared_drop_misreads
#print axioms shared_not_blind
#print axioms pruned_view_closed_again

end Repurge

end Kernel
