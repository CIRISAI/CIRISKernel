/-
  Proposed statements for crates/ciris-kernel/FORMAL_GAPS.md. NOT built by proofs/build.sh, which compiles a
  fixed list of files and refuses `sorry`. Each statement is small and believed true; none is proved here.
  Core Lean 4.14, no Mathlib.
-/

namespace Proposed

/-- `ops::least`: the element least by `key`, `none` when the list is empty or two different elements share
    the least key. The tie is refused, never broken by position. -/
def leastNoTie (key : Nat × Nat → Nat) (l : List (Nat × Nat)) : Option (Nat × Nat) :=
  match l.map key |>.min? with
  | none => none
  | some m =>
    match (l.filter (fun x => key x == m)).eraseDups with
    | [x] => some x
    | _ => none

/-- G1. The least element does not depend on the order of the list. -/
theorem leastNoTie_perm (key : Nat × Nat → Nat) {l l' : List (Nat × Nat)} (h : l.Perm l') :
    leastNoTie key l = leastNoTie key l' := by
  sorry

/-- G2. A refused tie is a real tie: two different elements share the least key. -/
theorem leastNoTie_none_iff (key : Nat × Nat → Nat) (l : List (Nat × Nat)) (hne : l ≠ []) :
    leastNoTie key l = none ↔ ∃ a b, a ∈ l ∧ b ∈ l ∧ a ≠ b ∧ key a = key b ∧ ∀ c ∈ l, key a ≤ key c := by
  sorry

/-- `line::versions` with no reader: a version counts iff it is counted over the heads it extends and every
    version it extends counts. `past` is well founded through `builds`, so the recursion is on `fuel`. -/
def counts (valid : Nat → Bool) (builds : Nat → List Nat) : Nat → Nat → Bool
  | 0, _ => false
  | f + 1, i => valid i && (builds i).all (fun e => counts valid builds f e)

/-- G3. Built on: a version that counts has every version it extends counting, at one less fuel. -/
theorem counts_built_on (valid : Nat → Bool) (builds : Nat → List Nat) (f i e : Nat)
    (h : counts valid builds (f + 1) i = true) (he : e ∈ builds i) : counts valid builds f e = true := by
  sorry

end Proposed
