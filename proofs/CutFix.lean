/-
  CutFix.lean: the cut's well-founded fixed point (KERNEL.md section 6 rule 4; crates/ciris-kernel src/cut.rs).

  The cut computes `L` by repeating `T ∘ T` from the empty set, where `T A` is the set of cuts that count if
  exactly the cuts in `A` do the voiding, and then `U = T L`. A cut is *counts* in `L`, *contested* in `U \ L`
  and *void* outside `U`. `T` is antitone: more cuts doing the voiding void more. This file proves, for any
  antitone `T`, that the iteration climbs, that the set where it stops is a fixed point of `T ∘ T` below its
  image, and that what is in `L` counts whatever the undecided cuts do. Then it instantiates `T` with the
  shape `cut.rs` uses (a cut counts iff it is not voided and enough of its voices are not voided) and proves
  that shape antitone. Core Lean 4.14, no Mathlib.
-/
namespace CutFix

variable {α : Type}

/-- `A ⊆ B` for sets as predicates. -/
def Sub (A B : α → Prop) : Prop := ∀ x, A x → B x

/-- `T` reverses inclusion. -/
def Antitone (T : (α → Prop) → (α → Prop)) : Prop := ∀ A B, Sub A B → Sub (T B) (T A)

/-- The iterates the cut computes: `∅`, `T (T ∅)`, `T (T (T (T ∅)))`, … -/
def iter (T : (α → Prop) → (α → Prop)) : Nat → (α → Prop)
  | 0 => fun _ => False
  | n + 1 => T (T (iter T n))

theorem sub_trans {A B C : α → Prop} (h1 : Sub A B) (h2 : Sub B C) : Sub A C := fun x h => h2 x (h1 x h)

/-- `T ∘ T` is monotone. -/
theorem tt_mono {T : (α → Prop) → (α → Prop)} (hT : Antitone T) (A B : α → Prop) (h : Sub A B) :
    Sub (T (T A)) (T (T B)) :=
  hT _ _ (hT _ _ h)

/-- Every iterate lies below its image: `iter n ⊆ T (iter n)`, so `L ⊆ U` wherever the iteration stops. -/
theorem iter_below {T : (α → Prop) → (α → Prop)} (hT : Antitone T) : ∀ n, Sub (iter T n) (T (iter T n))
  | 0 => fun _ h => False.elim h
  | n + 1 => by
    have h1 : Sub (T (T (iter T n))) (T (iter T n)) := hT _ _ (iter_below hT n)
    exact hT _ _ h1

/-- The iteration climbs. -/
theorem iter_mono {T : (α → Prop) → (α → Prop)} (hT : Antitone T) : ∀ n, Sub (iter T n) (iter T (n + 1))
  | 0 => fun _ h => False.elim h
  | n + 1 => tt_mono hT _ _ (iter_mono hT n)

/-- Where the iteration stops (`iter (n+1) ⊆ iter n`, the test `fix` makes), `L = iter n` is a fixed point of
    `T ∘ T`. -/
theorem stop_is_fixed {T : (α → Prop) → (α → Prop)} (hT : Antitone T) (n : Nat)
    (hstop : Sub (iter T (n + 1)) (iter T n)) : ∀ x, iter T n x ↔ T (T (iter T n)) x :=
  fun x => ⟨fun h => iter_mono hT n x h, fun h => hstop x h⟩

/-- **Counts whatever the undecided cuts do.** For a fixed point `L` of `T ∘ T` with `L ⊆ T L`, and any set `A`
    of cuts doing the voiding that contains every cut of `L` and none outside `U = T L`, every cut of `L` still
    counts (`L ⊆ T A`), and nothing outside `U` comes to count (`T A ⊆ U`). -/
theorem counts_whatever {T : (α → Prop) → (α → Prop)} (hT : Antitone T) (L : α → Prop)
    (hfix : ∀ x, L x ↔ T (T L) x) (A : α → Prop) (hLA : Sub L A) (hAU : Sub A (T L)) :
    Sub L (T A) ∧ Sub (T A) (T L) := by
  refine ⟨?_, hT _ _ hLA⟩
  intro x hx
  exact hT A (T L) hAU x ((hfix x).1 hx)

/-- The same at the set where the iteration stops: what the cut reports as *counts* is in every resolution. -/
theorem stopped_counts {T : (α → Prop) → (α → Prop)} (hT : Antitone T) (n : Nat)
    (hstop : Sub (iter T (n + 1)) (iter T n)) (A : α → Prop)
    (hLA : Sub (iter T n) A) (hAU : Sub A (T (iter T n))) :
    Sub (iter T n) (T A) ∧ Sub (T A) (T (iter T n)) :=
  counts_whatever hT _ (stop_is_fixed hT n hstop) A hLA hAU

/-- A fixed point of `T` itself (a resolution with nothing contested) lies between `L` and `U`. -/
theorem total_between {T : (α → Prop) → (α → Prop)} (hT : Antitone T) (A : α → Prop)
    (hA : ∀ x, A x ↔ T A x) : ∀ n, Sub (iter T n) A ∧ Sub A (T (iter T n))
  | 0 => ⟨fun _ h => False.elim h, fun x h => hT _ _ (fun _ h' => False.elim h') x ((hA x).1 h)⟩
  | n + 1 => by
    have ih := total_between hT A hA n
    have hAeq : T A = A := funext fun y => propext (hA y).symm
    have up : Sub (iter T (n + 1)) A := by
      intro x hx
      have h2 := hT _ _ (hT _ _ ih.1) x hx
      rw [hAeq, hAeq] at h2
      exact h2
    exact ⟨up, fun x hx => hT _ _ up x ((hA x).1 hx)⟩

/-! ## The shape `cut.rs` computes -/

/-- A count over a list, by recursion: the number of elements satisfying `p`. -/
def cnt {β : Type} (p : β → Prop) [DecidablePred p] : List β → Nat
  | [] => 0
  | x :: xs => (if p x then 1 else 0) + cnt p xs

theorem cnt_mono {β : Type} (p q : β → Prop) [DecidablePred p] [DecidablePred q] (h : ∀ x, p x → q x) :
    ∀ l, cnt p l ≤ cnt q l
  | [] => Nat.le_refl 0
  | x :: xs => by
    simp only [cnt]
    have ih := cnt_mono p q h xs
    by_cases hp : p x
    · simp [hp, h x hp]; omega
    · by_cases hq : q x <;> simp [hp, hq] <;> omega

/-- The cut's step. `isCut c`: a concluded row that cuts. `hits x c`: cut `x` voids row `c` (concurrent on a
    slot, or a rejection naming it). `voices c`: the rows whose signers count for `c`. `need c`: how many must
    stay unvoided. A cut counts iff no cut of `A` voids it and at least `need c` of its voices are not voided
    by a cut of `A`. -/
structure Shape (α : Type) where
  isCut : α → Prop
  hits : α → α → Prop
  voices : α → List α
  need : α → Nat

def voided (S : Shape α) (A : α → Prop) (c : α) : Prop := ∃ x, A x ∧ S.hits x c

open Classical in
noncomputable def step (S : Shape α) (A : α → Prop) (c : α) : Prop :=
  S.isCut c ∧ ¬ voided S A c ∧ S.need c ≤ cnt (fun v => ¬ voided S A v) (S.voices c)

open Classical in
/-- **The cut's step is antitone**, so every theorem above holds of it. -/
theorem step_antitone (S : Shape α) : Antitone (step S) := by
  intro A B hAB c hc
  obtain ⟨h1, h2, h3⟩ := hc
  have hv : ∀ v, voided S A v → voided S B v := fun v ⟨x, hx, hh⟩ => ⟨x, hAB x hx, hh⟩
  exact ⟨h1, fun h => h2 (hv c h),
    Nat.le_trans h3 (cnt_mono _ _ (fun v hb ha => hb (hv v ha)) (S.voices c))⟩

/-- **The cut, as `cut.rs` solves it**: where the iteration stops, every cut it reports as counting counts in
    every resolution of the undecided ones, and no cut it reports void comes to count. -/
theorem cut_wfs (S : Shape α) (n : Nat) (hstop : Sub (iter (step S) (n + 1)) (iter (step S) n))
    (A : α → Prop) (hLA : Sub (iter (step S) n) A) (hAU : Sub A (step S (iter (step S) n))) :
    Sub (iter (step S) n) (step S A) ∧ Sub (step S A) (step S (iter (step S) n)) :=
  stopped_counts (step_antitone S) n hstop A hLA hAU

/-- And what it reports as counting is never reported void: `L ⊆ U`. -/
theorem cut_counts_not_void (S : Shape α) (n : Nat) : Sub (iter (step S) n) (step S (iter (step S) n)) :=
  iter_below (step_antitone S) n

end CutFix

#print axioms CutFix.iter_below
#print axioms CutFix.iter_mono
#print axioms CutFix.stop_is_fixed
#print axioms CutFix.counts_whatever
#print axioms CutFix.stopped_counts
#print axioms CutFix.total_between
#print axioms CutFix.cnt_mono
#print axioms CutFix.step_antitone
#print axioms CutFix.cut_wfs
#print axioms CutFix.cut_counts_not_void
