/-
  Held.lean — a held view's admission equals the full fold, and a resumed checkpoint equals its view

  The kernel's `held_view::HeldView` (issue #4, slice 4) keeps the answers of a view across admissions. An
  admission extends the offered set `S` to `S'` and recomputes only the dirty cone: the rows not kept before,
  and the rows that have themselves or an ancestor in concurrent conflict with a newly kept row. Every other
  row keeps the answer it held. Its checkpoint is resumed from the rows at or beneath a checkpoint row and
  the rest, re-attached by id.

  Proved here, from `Causal.conclOf_local` through `Settled.concl_ext_local` and `derived_ext_local`, and
  from `Settled.checkpoint_resume`:
    admit_eq          one admission, as the dirty-cone update, gives the full fold's conclusions over `S'`
    admits_eq         so does any sequence of admissions, after every one: the held answers are the fold
                      over the prefix
    admit_dirty_new   every newly kept row is dirty
    admit_derived     a derived answer reading only parties outside the dirty cone is unchanged
    resume_eq         any answer over the resumed set is the answer over the held set
    resume_concl      in particular the conclusions
    resume_admits_eq  resume, then admit: the fold over the prefix, after every admission

  Core Lean 4.14 only, no `sorry`, no axiom beyond propext, Quot.sound and Classical.choice.
-/
import Settled

namespace Kernel

namespace Held

open Relation Causal Settled

section Admit

variable {Row : Type} (parent : Row → Row → Prop) (wf : WellFounded parent)
variable (wellFormed : Row → Prop) (judge : Row → (Row → Prop) → (Row → Prop) → Prop)
variable (conflict : Row → Row → Prop)

/-- The dirty cone of extending `S` to `S'`: a row not kept in `S`, or a row that has itself or an
    ancestor in concurrent conflict with a row newly kept in `S'`. -/
def dirty (S S' : Row → Prop) (r : Row) : Prop :=
  ¬ kept parent wf wellFormed S r ∨
    ∃ q, (q = r ∨ TransGen parent q r) ∧ ∃ y, kept parent wf wellFormed S' y ∧
      ¬ kept parent wf wellFormed S y ∧ conflict y q ∧ conc parent y q

/-- One admission: the dirty cone read from the full fold over `S'`, every other row as held in `H`. -/
def admit (root : Row → Prop) (H S S' : Row → Prop) (r : Row) : Prop :=
  (dirty parent wf wellFormed conflict S S' r ∧ concl parent wf judge wellFormed root S' r) ∨
    (¬ dirty parent wf wellFormed conflict S S' r ∧ H r)

/-- A newly kept row is in the dirty cone. -/
theorem admit_dirty_new (S S' : Row → Prop) (r : Row) (hn : ¬ kept parent wf wellFormed S r) :
    dirty parent wf wellFormed conflict S S' r :=
  Or.inl hn

/-- A row outside the dirty cone was kept, and nothing newly kept is in concurrent conflict with it or an
    ancestor: `concl_ext_local`'s hypotheses. -/
theorem clean_far (S S' : Row → Prop) (r : Row) (hd : ¬ dirty parent wf wellFormed conflict S S' r) :
    kept parent wf wellFormed S r ∧
      ∀ q, (q = r ∨ TransGen parent q r) → ∀ y, kept parent wf wellFormed S' y →
        ¬ kept parent wf wellFormed S y → conflict y q → ¬ conc parent y q :=
  ⟨Classical.byContradiction fun hk => hd (Or.inl hk),
   fun q hq y a b c d => hd (Or.inr ⟨q, hq, y, a, b, c, d⟩)⟩

/-- **The admission is the full fold.** Held answers equal to the fold over `S`, updated on the dirty cone
    of an admissible extension to `S'`, are the fold over `S'`. -/
theorem admit_eq
    (hC : ∀ r P (C C' : Row → Prop), (∀ y, conflict y r → (C y ↔ C' y)) →
      (judge r P C ↔ judge r P C'))
    (root S S' : Row → Prop) (h : Extends S S') (H : Row → Prop)
    (hH : ∀ r, H r ↔ concl parent wf judge wellFormed root S r) (r : Row) :
    admit parent wf wellFormed judge conflict root H S S' r ↔
      concl parent wf judge wellFormed root S' r := by
  by_cases hd : dirty parent wf wellFormed conflict S S' r
  · constructor
    · intro ha
      cases ha with
      | inl a => exact a.2
      | inr a => exact absurd hd a.1
    · intro hc
      exact Or.inl ⟨hd, hc⟩
  · have ⟨hk, hfar⟩ := clean_far parent wf wellFormed conflict S S' r hd
    have e := concl_ext_local parent wf wellFormed judge conflict hC root S S' h r hk hfar
    constructor
    · intro ha
      cases ha with
      | inl a => exact absurd a.1 hd
      | inr a => exact e.1 ((hH r).1 a.2)
    · intro hc
      exact Or.inr ⟨hd, (hH r).2 (e.2 hc)⟩

/-- The held answers after `n` admissions along a chain of offered sets. -/
def heldAfter (root : Row → Prop) (S : Nat → Row → Prop) (H0 : Row → Prop) : Nat → Row → Prop
  | 0 => H0
  | n + 1 => admit parent wf wellFormed judge conflict root (heldAfter root S H0 n) (S n) (S (n + 1))

/-- **After every admission**, the held answers are the full fold over the rows offered so far. -/
theorem admits_eq
    (hC : ∀ r P (C C' : Row → Prop), (∀ y, conflict y r → (C y ↔ C' y)) →
      (judge r P C ↔ judge r P C'))
    (root : Row → Prop) (S : Nat → Row → Prop) (hS : ∀ n, Extends (S n) (S (n + 1)))
    (H0 : Row → Prop) (h0 : ∀ r, H0 r ↔ concl parent wf judge wellFormed root (S 0) r) :
    ∀ n r, heldAfter parent wf wellFormed judge conflict root S H0 n r ↔
      concl parent wf judge wellFormed root (S n) r := by
  intro n
  induction n with
  | zero => exact h0
  | succ n ih =>
    intro r
    exact admit_eq parent wf wellFormed judge conflict hC root (S n) (S (n + 1)) (hS n)
      (heldAfter parent wf wellFormed judge conflict root S H0 n) ih r

/-- A derived answer whose parties are all outside the dirty cone is the same before and after: the
    rows `dirty` leaves out need no rerun. -/
theorem admit_derived
    (hC : ∀ r P (C C' : Row → Prop), (∀ y, conflict y r → (C y ↔ C' y)) →
      (judge r P C ↔ judge r P C'))
    (root S S' : Row → Prop) (h : Extends S S')
    (D : (Row → Prop) → Prop) (T : Row → Prop)
    (hD : ∀ A B : Row → Prop, (∀ r, T r → (A r ↔ B r)) → (D A ↔ D B))
    (hT : ∀ r, T r → ¬ dirty parent wf wellFormed conflict S S' r) :
    D (concl parent wf judge wellFormed root S) ↔ D (concl parent wf judge wellFormed root S') :=
  derived_ext_local parent wf wellFormed judge conflict hC root S S' h D T hD
    (fun r hr => clean_far parent wf wellFormed conflict S S' r (hT r hr))

end Admit

section Resume

variable {Row : Type} (parent : Row → Row → Prop) (wf : WellFounded parent)
variable (wellFormed : Row → Prop) (judge : Row → (Row → Prop) → (Row → Prop) → Prop)

/-- The set a checkpoint resumes: the rows at or beneath checkpoint row `k`, and the rest re-attached. -/
def resumed (k : Row) (S : Row → Prop) : Row → Prop :=
  fun r => beneath parent k r ∨ (S r ∧ ¬ beneath parent k r)

/-- **Resume is the view it came from**: every answer over the resumed set is the answer over the held set. -/
theorem resume_eq {β : Type} (S : Row → Prop) (k : Row) (hk : kept parent wf wellFormed S k)
    (F : (Row → Prop) → β) : F (resumed parent k S) = F S :=
  (checkpoint_resume parent wf wellFormed S k hk F).symm

/-- In particular, the conclusions. -/
theorem resume_concl (root S : Row → Prop) (k : Row) (hk : kept parent wf wellFormed S k) (r : Row) :
    concl parent wf judge wellFormed root (resumed parent k S) r ↔
      concl parent wf judge wellFormed root S r := by
  rw [resume_eq parent wf wellFormed S k hk (concl parent wf judge wellFormed root)]

/-- Resume, then admit along a chain from the held set: after every admission, the full fold over the prefix. -/
theorem resume_admits_eq (conflict : Row → Row → Prop)
    (hC : ∀ r P (C C' : Row → Prop), (∀ y, conflict y r → (C y ↔ C' y)) →
      (judge r P C ↔ judge r P C'))
    (root : Row → Prop) (S : Nat → Row → Prop) (hS : ∀ n, Extends (S n) (S (n + 1)))
    (k : Row) (hk : kept parent wf wellFormed (S 0) k) :
    ∀ n r, heldAfter parent wf wellFormed judge conflict root S
        (concl parent wf judge wellFormed root (resumed parent k (S 0))) n r ↔
      concl parent wf judge wellFormed root (S n) r :=
  admits_eq parent wf wellFormed judge conflict hC root S hS _
    (fun r => resume_concl parent wf wellFormed judge root (S 0) k hk r)

end Resume

#print axioms admit_eq
#print axioms admits_eq
#print axioms admit_dirty_new
#print axioms admit_derived
#print axioms resume_eq
#print axioms resume_concl
#print axioms resume_admits_eq

end Held

end Kernel
