/-
  SeatWalk.lean: the bounded walk of live seats, and tips wait (KERNEL.md sections 5 and 7;
  crates/ciris-kernel src/seat.rs, `Seats::new`, `stands`, `holders`, `tips_common`).

  `Seats::new` keeps the pairs (offer, key) that are live by the two consents, and walks them: a pair whose
  offer is conferred by the object's own key or by a group is a root, at depth 0; a pair whose offer is
  conferred under a seat is live at depth d + 1 when the seat it is under is live at depth d for the offer's
  signer, and that seat may confer it. The walk is repeated `depth + 1` times. This file proves that the walk
  is exactly the bounded chains: a pair is reached at depth d within n passes iff a chain of d links leads to
  it from a root and d < n; so a seat stands only through a chain of live seats to a root, no longer than the
  bound, and every such chain is found. It then proves the reading of tips: with several tips a key holds a
  scope only if every tip seats it, and a further tip never adds a holder. Core Lean 4.14, no Mathlib.
-/
namespace SeatWalk

/-- The live pairs before the walk, and what the walk reads of each. -/
structure Base (O K : Type) where
  live : O → K → Prop            -- offered, accepted, not withdrawn, not cut
  root : O → Prop                -- conferred by the object's own key or by a group
  under : O → O                  -- the seat a conferred offer is under
  signer : O → K                 -- the offer's signer
  mayConfer : O → O → Prop       -- the seat of the first may confer the second (table data)

variable {O K : Type}

/-- The pairs reached within `n` passes, at depth `d`. -/
def reached (B : Base O K) : Nat → O → K → Nat → Prop
  | 0, _, _, _ => False
  | n + 1, o, k, d =>
    reached B n o k d ∨
      (B.live o k ∧ ((B.root o ∧ d = 0) ∨
        (∃ d', d = d' + 1 ∧ reached B n (B.under o) (B.signer o) d' ∧ B.mayConfer (B.under o) o)))

/-- A chain of `d` links from a root to the pair. -/
inductive Chain (B : Base O K) : O → K → Nat → Prop
  | root (o : O) (k : K) : B.live o k → B.root o → Chain B o k 0
  | link (o : O) (k : K) (d : Nat) : B.live o k → Chain B (B.under o) (B.signer o) d →
      B.mayConfer (B.under o) o → Chain B o k (d + 1)

theorem reached_chain (B : Base O K) : ∀ n o k d, reached B n o k d → Chain B o k d ∧ d < n
  | 0, _, _, _, h => False.elim h
  | n + 1, o, k, d, h => by
    rcases h with h | ⟨hl, ⟨hr, hd⟩ | ⟨d', hd, hu, hm⟩⟩
    · have := reached_chain B n o k d h; exact ⟨this.1, by omega⟩
    · subst hd; exact ⟨Chain.root o k hl hr, by omega⟩
    · subst hd
      have := reached_chain B n _ _ d' hu
      exact ⟨Chain.link o k d' hl this.1 hm, by omega⟩

theorem reached_mono (B : Base O K) : ∀ n o k d, reached B n o k d → reached B (n + 1) o k d :=
  fun _ _ _ _ h => Or.inl h

theorem chain_reached (B : Base O K) : ∀ o k d, Chain B o k d → ∀ n, d < n → reached B n o k d := by
  intro o k d h
  induction h with
  | root o k hl hr =>
    intro n hn
    cases n with
    | zero => omega
    | succ n => exact Or.inr ⟨hl, Or.inl ⟨hr, rfl⟩⟩
  | link o k d hl _ hm ih =>
    intro n hn
    cases n with
    | zero => omega
    | succ n => exact Or.inr ⟨hl, Or.inr ⟨d, rfl, ih n (by omega), hm⟩⟩

/-- **The walk is the bounded chains.** Within `n` passes a pair is reached at depth `d` iff a chain of `d`
    links leads to it from a root, and `d < n`. With `n = depth + 1`, a seat stands only through at most
    `depth` links, and every such chain is found. -/
theorem walk_iff_chain (B : Base O K) (n : Nat) (o : O) (k : K) (d : Nat) :
    reached B n o k d ↔ Chain B o k d ∧ d < n :=
  ⟨reached_chain B n o k d, fun ⟨h, hd⟩ => chain_reached B o k d h n hd⟩

/-- A pair not live by the two consents is never reached, whatever chain leads to its offer's seat. -/
theorem unlive_never_reached (B : Base O K) (n : Nat) (o : O) (k : K) (d : Nat) (h : ¬ B.live o k) :
    ¬ reached B n o k d := by
  intro hr
  have := (reached_chain B n o k d hr).1
  cases this with
  | root _ _ hl _ => exact h hl
  | link _ _ _ hl _ _ => exact h hl

/-- A conferred seat falls with the seat it is under: if no chain reaches the seat it is under, it is not
    reached either (unless it is itself a root). -/
theorem falls_with_upstream (B : Base O K) (n : Nat) (o : O) (k : K) (d : Nat) (hnr : ¬ B.root o)
    (hup : ∀ d', ¬ Chain B (B.under o) (B.signer o) d') : ¬ reached B n o k d := by
  intro hr
  have := (reached_chain B n o k d hr).1
  cases this with
  | root _ _ _ hr' => exact hnr hr'
  | link _ _ d' _ hc _ => exact hup d' hc

/-! ## Tips wait -/

/-- The holders of a scope while tips wait: the keys held at the set read, and at every tip. -/
def holders (heldAll : K → Prop) (tips : List (K → Prop)) (k : K) : Prop :=
  heldAll k ∧ (tips.length ≤ 1 ∨ ∀ t ∈ tips, t k)

/-- With several tips a key holds the scope only if every tip seats it. -/
theorem holder_every_tip (heldAll : K → Prop) (tips : List (K → Prop)) (h2 : 1 < tips.length) (k : K)
    (h : holders heldAll tips k) : ∀ t ∈ tips, t k := by
  obtain ⟨_, hh⟩ := h
  cases hh with
  | inl h1 => exact absurd h1 (Nat.not_le.mpr h2)
  | inr h1 => exact h1

/-- A further tip never adds a holder, once there are two. -/
theorem another_tip_adds_nobody (heldAll : K → Prop) (tips : List (K → Prop)) (t : K → Prop)
    (h2 : 1 < tips.length) (k : K) (h : holders heldAll (t :: tips) k) : holders heldAll tips k := by
  obtain ⟨ha, hh⟩ := h
  refine ⟨ha, Or.inr ?_⟩
  cases hh with
  | inl h1 =>
    exfalso
    have h3 : tips.length + 1 ≤ 1 := by simpa using h1
    exact Nat.lt_irrefl 1 (Nat.lt_of_lt_of_le h2 (Nat.le_of_succ_le_succ (Nat.le_trans h3 (Nat.le_succ 1))))
  | inr h1 => exact fun s hs => h1 s (List.mem_cons_of_mem _ hs)

/-- Holders while tips wait are among the holders of the whole set: tips never list a key the set does not. -/
theorem tips_list_no_one_new (heldAll : K → Prop) (tips : List (K → Prop)) (k : K)
    (h : holders heldAll tips k) : heldAll k := h.1

end SeatWalk

#print axioms SeatWalk.reached_chain
#print axioms SeatWalk.chain_reached
#print axioms SeatWalk.walk_iff_chain
#print axioms SeatWalk.unlive_never_reached
#print axioms SeatWalk.falls_with_upstream
#print axioms SeatWalk.holder_every_tip
#print axioms SeatWalk.another_tip_adds_nobody
#print axioms SeatWalk.tips_list_no_one_new
