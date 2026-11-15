/-
  Versions.lean: built on, for roster versions (KERNEL.md section 8a, "a counted row counts only if every
  counted row it is built on counts"; crates/ciris-kernel src/line.rs, `versions`). G3 of
  proofs/proposed/Proposed.lean, proved, and the recursion's fuel shown not to matter once it suffices.
-/
namespace Versions

/-- A version counts iff it is counted over the heads it extends and every version it extends counts. -/
def counts (valid : Nat → Bool) (builds : Nat → List Nat) : Nat → Nat → Bool
  | 0, _ => false
  | f + 1, i => valid i && (builds i).all (fun e => counts valid builds f e)

/-- G3. Built on: a version that counts has every version it extends counting, at one less fuel. -/
theorem counts_built_on (valid : Nat → Bool) (builds : Nat → List Nat) (f i e : Nat)
    (h : counts valid builds (f + 1) i = true) (he : e ∈ builds i) : counts valid builds f e = true := by
  simp only [counts, Bool.and_eq_true, List.all_eq_true] at h
  exact h.2 e he

/-- A version that counts is valid itself. -/
theorem counts_valid (valid : Nat → Bool) (builds : Nat → List Nat) (f i : Nat)
    (h : counts valid builds f i = true) : valid i = true := by
  cases f with
  | zero => simp [counts] at h
  | succ f => simp only [counts, Bool.and_eq_true] at h; exact h.1

/-- More fuel never takes a count back: once the recursion has reached the bottom of the line, the answer is
    fixed. -/
theorem counts_fuel_mono (valid : Nat → Bool) (builds : Nat → List Nat) :
    ∀ f i, counts valid builds f i = true → counts valid builds (f + 1) i = true
  | 0, _, h => by simp [counts] at h
  | f + 1, i, h => by
    simp only [counts, Bool.and_eq_true, List.all_eq_true] at h
    show (valid i && (builds i).all fun e => counts valid builds (f + 1) e) = true
    simp only [Bool.and_eq_true, List.all_eq_true]
    exact ⟨h.1, fun e he => counts_fuel_mono valid builds f e (h.2 e he)⟩

/-- An invalid version voids everything built on it, down the whole line. -/
theorem void_down_the_line (valid : Nat → Bool) (builds : Nat → List Nat) (f i e : Nat)
    (he : e ∈ builds i) (hv : ∀ g, counts valid builds g e = false) : counts valid builds (f + 1) i = false := by
  cases h : counts valid builds (f + 1) i with
  | false => rfl
  | true => have := counts_built_on valid builds f i e h he; rw [hv f] at this; exact absurd this (by simp)

end Versions

#print axioms Versions.counts_built_on
#print axioms Versions.counts_valid
#print axioms Versions.counts_fuel_mono
#print axioms Versions.void_down_the_line
