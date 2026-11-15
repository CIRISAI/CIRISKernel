/-
  Ops.lean: the reducer that refuses a tie (KERNEL.md section 4; crates/ciris-kernel src/ops.rs, `least`,
  `greatest`). G1 and G2 of the earlier proposal, proved: the least element does not depend on the order of
  the list, and a refused tie is a real tie. Core Lean 4.14 has no lemmas for `List.eraseDups`, so the ones
  needed are proved here first.
-/
namespace Ops
set_option linter.unusedSectionVars false
variable {α : Type} [BEq α] [LawfulBEq α]

theorem nodup_rev {l : List α} (h : l.Nodup) : l.reverse.Nodup := by
  unfold List.Nodup at *
  rw [List.pairwise_reverse]
  exact List.Pairwise.imp (fun hab hba => hab hba.symm) h

theorem loop_mem (x : α) : ∀ (as bs : List α), x ∈ List.eraseDups.loop as bs ↔ x ∈ as ∨ x ∈ bs
  | [], bs => by simp [List.eraseDups.loop]
  | a :: as, bs => by
    unfold List.eraseDups.loop
    by_cases h : bs.elem a = true
    · simp only [h, ite_true]
      rw [loop_mem x as bs]
      have ha : a ∈ bs := by simpa using h
      constructor
      · rintro (h1 | h1)
        · exact Or.inl (List.mem_cons_of_mem _ h1)
        · exact Or.inr h1
      · rintro (h1 | h1)
        · rcases List.mem_cons.1 h1 with rfl | h2
          · exact Or.inr ha
          · exact Or.inl h2
        · exact Or.inr h1
    · simp only [h]
      rw [loop_mem x as (a :: bs)]
      simp only [List.mem_cons]
      constructor
      · rintro (h1 | h1 | h1)
        · exact Or.inl (Or.inr h1)
        · exact Or.inl (Or.inl h1)
        · exact Or.inr h1
      · rintro ((h1 | h1) | h1)
        · exact Or.inr (Or.inl h1)
        · exact Or.inl h1
        · exact Or.inr (Or.inr h1)

theorem loop_nodup : ∀ (as bs : List α), bs.Nodup → (List.eraseDups.loop as bs).Nodup
  | [], bs, h => by simp [List.eraseDups.loop]; exact nodup_rev h
  | a :: as, bs, h => by
    unfold List.eraseDups.loop
    by_cases he : bs.elem a = true
    · simp only [he, ite_true]; exact loop_nodup as bs h
    · simp only [he]
      apply loop_nodup as (a :: bs)
      have : a ∉ bs := by simpa using he
      exact List.nodup_cons.2 ⟨this, h⟩

theorem mem_eraseDups (x : α) (l : List α) : x ∈ l.eraseDups ↔ x ∈ l := by
  unfold List.eraseDups; rw [loop_mem]; simp

theorem nodup_eraseDups (l : List α) : l.eraseDups.Nodup := loop_nodup l [] List.nodup_nil

theorem nodup_singleton_iff (x : α) : ∀ (l : List α), l.Nodup → (l = [x] ↔ l ≠ [] ∧ ∀ y ∈ l, y = x)
  | [], _ => by simp
  | a :: rest, hn => by
    constructor
    · intro h; cases h; simp
    · intro ⟨_, hall⟩
      have ha : a = x := hall a (List.mem_cons_self _ _)
      subst ha
      cases rest with
      | nil => rfl
      | cons b rest =>
        have hb : b = a := hall b (by simp)
        have := (List.nodup_cons.1 hn).1
        subst hb
        exact absurd (List.mem_cons_self _ _) this

theorem eraseDups_singleton_iff (x : α) (l : List α) : l.eraseDups = [x] ↔ l ≠ [] ∧ ∀ y ∈ l, y = x := by
  rw [nodup_singleton_iff x _ (nodup_eraseDups l)]
  constructor
  · intro ⟨hne, hall⟩
    refine ⟨fun h => hne (by subst h; rfl), fun y hy => hall y ((mem_eraseDups y l).2 hy)⟩
  · intro ⟨hne, hall⟩
    refine ⟨fun h => ?_, fun y hy => hall y ((mem_eraseDups y l).1 hy)⟩
    cases l with
    | nil => exact hne rfl
    | cons a t =>
      have := (mem_eraseDups a (a :: t)).2 (List.mem_cons_self a t)
      rw [h] at this; cases this



def leastNoTie (key : Nat × Nat → Nat) (l : List (Nat × Nat)) : Option (Nat × Nat) :=
  match l.map key |>.min? with
  | none => none
  | some m =>
    match (l.filter (fun x => key x == m)).eraseDups with
    | [x] => some x
    | _ => none

/-- What `leastNoTie` returns: the element least by `key`, when no other element shares its key. -/
theorem leastNoTie_some_iff (key : Nat × Nat → Nat) (l : List (Nat × Nat)) (x : Nat × Nat) :
    leastNoTie key l = some x ↔ x ∈ l ∧ (∀ y ∈ l, key x ≤ key y) ∧ ∀ y ∈ l, key y = key x → y = x := by
  unfold leastNoTie
  split
  · rename_i hm
    simp only [reduceCtorEq, false_iff]
    intro ⟨hx, _⟩
    have : l.map key = [] := List.min?_eq_none_iff.1 hm
    simp at this; subst this; cases hx
  · rename_i m hm
    have hmc := List.min?_eq_some_iff'.1 hm
    obtain ⟨⟨z, hz, hzm⟩, hmin⟩ : (∃ z, z ∈ l ∧ key z = m) ∧ ∀ y ∈ l, m ≤ key y := by
      refine ⟨by simpa using hmc.1, fun y hy => hmc.2 _ (List.mem_map_of_mem _ hy)⟩
    have hfil : ∀ y, y ∈ l.filter (fun x => key x == m) ↔ y ∈ l ∧ key y = m := by
      intro y; simp
    split
    · rename_i x' he
      have ⟨hne, hall⟩ := (eraseDups_singleton_iff x' _).1 he
      have hx'f : x' ∈ l.filter (fun x => key x == m) := by
        cases hf : l.filter (fun x => key x == m) with
        | nil => exact absurd hf hne
        | cons a t => have := hall a (by rw [hf]; exact List.mem_cons_self a t); subst this; exact List.mem_cons_self _ _
      have ⟨hx'l, hx'm⟩ := (hfil x').1 hx'f
      constructor
      · intro h; cases h
        exact ⟨hx'l, fun y hy => hx'm ▸ hmin y hy, fun y hy hk => hall y ((hfil y).2 ⟨hy, hk.trans hx'm⟩)⟩
      · intro ⟨hx, hle, huniq⟩
        have hk : key x = m := Nat.le_antisymm (hzm ▸ hle z hz) (hmin x hx)
        exact congrArg some (huniq x' hx'l (hx'm.trans hk.symm))
    · rename_i e hnot
      simp only [reduceCtorEq, false_iff]
      intro ⟨hx, hle, huniq⟩
      have hk : key x = m := Nat.le_antisymm (hzm ▸ hle z hz) (hmin x hx)
      have : (l.filter (fun x => key x == m)).eraseDups = [x] := by
        rw [eraseDups_singleton_iff]
        refine ⟨fun h => ?_, fun y hy => huniq y ((hfil y).1 hy).1 (((hfil y).1 hy).2.trans hk.symm)⟩
        have : x ∈ l.filter (fun x => key x == m) := (hfil x).2 ⟨hx, hk⟩
        rw [h] at this; cases this
      exact hnot x this

/-- G1. The least element does not depend on the order of the list. -/
theorem leastNoTie_perm (key : Nat × Nat → Nat) {l l' : List (Nat × Nat)} (h : l.Perm l') :
    leastNoTie key l = leastNoTie key l' := by
  have hm : ∀ y, y ∈ l ↔ y ∈ l' := fun y => h.mem_iff
  have key_iff : ∀ x, leastNoTie key l = some x ↔ leastNoTie key l' = some x := by
    intro x
    rw [leastNoTie_some_iff, leastNoTie_some_iff]
    simp only [hm]
  cases h1 : leastNoTie key l with
  | none =>
    cases h2 : leastNoTie key l' with
    | none => rfl
    | some y => have := (key_iff y).2 h2; rw [h1] at this; cases this
  | some x => exact ((key_iff x).1 h1).symm

/-- G2. A refused tie is a real tie: two different elements share the least key. -/
theorem leastNoTie_none_iff (key : Nat × Nat → Nat) (l : List (Nat × Nat)) (hne : l ≠ []) :
    leastNoTie key l = none ↔ ∃ a b, a ∈ l ∧ b ∈ l ∧ a ≠ b ∧ key a = key b ∧ ∀ c ∈ l, key a ≤ key c := by
  -- the least key exists, and is shared by two different elements iff no element is returned
  have hmin : ∃ z ∈ l, ∀ y ∈ l, key z ≤ key y := by
    cases hm : (l.map key).min? with
    | none => have := List.min?_eq_none_iff.1 hm; simp at this; exact absurd this hne
    | some m =>
      have hmc := List.min?_eq_some_iff'.1 hm
      obtain ⟨z, hz, hzm⟩ : ∃ z, z ∈ l ∧ key z = m := by simpa using hmc.1
      exact ⟨z, hz, fun y hy => hzm ▸ hmc.2 _ (List.mem_map_of_mem _ hy)⟩
  obtain ⟨z, hz, hzl⟩ := hmin
  constructor
  · intro h
    have hnz : ¬ (leastNoTie key l = some z) := by rw [h]; simp
    rw [leastNoTie_some_iff] at hnz
    have : ¬ ∀ y ∈ l, key y = key z → y = z := fun hall => hnz ⟨hz, hzl, hall⟩
    have : ∃ y, y ∈ l ∧ key y = key z ∧ y ≠ z := by
      apply Classical.byContradiction
      intro hno
      exact this (fun y hy hk => Classical.byContradiction fun hyz => hno ⟨y, hy, hk, hyz⟩)
    obtain ⟨y, hy, hk, hyz⟩ := this
    exact ⟨z, y, hz, hy, fun e => hyz e.symm, hk.symm, hzl⟩
  · intro ⟨a, b, ha, hb, hab, hk, hal⟩
    cases h : leastNoTie key l with
    | none => rfl
    | some x =>
      have ⟨hx, hxl, hu⟩ := (leastNoTie_some_iff key l x).1 h
      have hax : key a = key x := Nat.le_antisymm (hal x hx) (hxl a ha)
      have e1 := hu a ha hax
      have e2 := hu b hb (hk.symm.trans hax)
      exact absurd (e1.trans e2.symm) hab

end Ops

#print axioms Ops.loop_mem
#print axioms Ops.loop_nodup
#print axioms Ops.mem_eraseDups
#print axioms Ops.nodup_eraseDups
#print axioms Ops.eraseDups_singleton_iff
#print axioms Ops.leastNoTie_some_iff
#print axioms Ops.leastNoTie_perm
#print axioms Ops.leastNoTie_none_iff
