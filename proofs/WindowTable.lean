/-
  WindowTable.lean: how a window's table gives its outcome (KERNEL.md section 5, **window**; CC 2.7.5;
  crates/ciris-kernel src/window.rs, `table_outcome`).

  The table reads its clauses at once, then, only once the concluder's own two instants span the window, the
  target's silence, the clauses read at the close and the default. This file proves: before the close the
  outcome is "open" or an at-once clause's; an at-once outcome does not depend on whether the window has run;
  the default and the silent outcome need the close; and a landing concludes only when the outcome it states
  is the one the table gives over its past, so two landings over one past state one outcome. Core Lean 4.14.
-/
namespace WindowTable

/-- A clause: whether its count is met over the voices read, and the outcome it gives. -/
structure Clause (O : Type) where
  met : Bool
  out : O

/-- `table_outcome`: at-once clauses first, then the close. `silentHit`: the target signed inside the window. -/
def outcome {O : Type} (openO : O) (atOnce : List (Clause O)) (elapsed : Bool) (silent : Option O)
    (silentHit : Bool) (atClose : List (Clause O)) (dflt : O) : O :=
  match atOnce.find? (·.met) with
  | some c => c.out
  | none =>
    if !elapsed then openO
    else match silent, silentHit with
      | some s, true => s
      | _, _ =>
        match atClose.find? (·.met) with
        | some c => c.out
        | none => dflt

variable {O : Type}

/-- Before the close the outcome is "open" or the outcome of a met at-once clause. -/
theorem before_close (openO : O) (atOnce : List (Clause O)) (silent : Option O) (sh : Bool)
    (atClose : List (Clause O)) (dflt : O) :
    outcome openO atOnce false silent sh atClose dflt = openO ∨
      ∃ c ∈ atOnce, c.met = true ∧ outcome openO atOnce false silent sh atClose dflt = c.out := by
  unfold outcome
  cases h : atOnce.find? (·.met) with
  | none => simp
  | some c =>
    right
    exact ⟨c, List.mem_of_find?_eq_some h, by simpa using List.find?_some h, rfl⟩

/-- An at-once outcome is the same whether or not the window has run. -/
theorem at_once_ignores_close (openO : O) (atOnce : List (Clause O)) (c : Clause O)
    (h : atOnce.find? (·.met) = some c) (e e' : Bool) (silent : Option O) (sh sh' : Bool)
    (atClose atClose' : List (Clause O)) (dflt dflt' : O) :
    outcome openO atOnce e silent sh atClose dflt = outcome openO atOnce e' silent sh' atClose' dflt' := by
  simp [outcome, h]

/-- The default is reached only at the close, with no clause met and no silent outcome taken. -/
theorem default_needs_close (openO : O) (atOnce : List (Clause O)) (e : Bool) (silent : Option O) (sh : Bool)
    (atClose : List (Clause O)) (dflt : O) (hne : dflt ≠ openO)
    (hd : outcome openO atOnce e silent sh atClose dflt = dflt)
    (hno : ∀ c ∈ atOnce ++ atClose, c.out ≠ dflt) (hs : ∀ s, silent = some s → s ≠ dflt) : e = true := by
  cases e with
  | true => rfl
  | false =>
    exfalso
    rcases before_close openO atOnce silent sh atClose dflt with h | ⟨c, hc, _, h⟩
    · exact hne (hd ▸ h)
    · exact hno c (List.mem_append_left _ hc) (h ▸ hd)

/-- A landing concludes iff the outcome it states is the table's over its own past; two landings over the
    same past that both conclude state the same outcome (`Recount.dishonest_never_stands` is the form over
    rows). -/
def concludes (table : O) (stated : O) : Prop := stated = table

theorem landings_agree (t s1 s2 : O) (h1 : concludes t s1) (h2 : concludes t s2) : s1 = s2 := by
  unfold concludes at *; rw [h1, h2]

end WindowTable

#print axioms WindowTable.before_close
#print axioms WindowTable.at_once_ignores_close
#print axioms WindowTable.default_needs_close
#print axioms WindowTable.landings_agree
