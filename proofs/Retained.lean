/-
  Retained.lean: the rows that have not lapsed (KERNEL.md section 5, a key's own end; CC 2.7.5;
  crates/ciris-kernel src/key_end.rs, `retained`).

  `retained` keeps every row of a key that has not ended, every revocation, and everything in their past.
  This file proves: the set is closed downwards along what rows name, so a kept row never names a dropped one
  and the store stays a kept set; every revocation is kept; a row outside it is in no kept row's past; and,
  as `now` moves on with the same rows, a seed that stays a seed keeps its whole past (a key that has ended
  stays ended, `KeyEnd.ended_stays_ended`, so the seeds only shrink to those that remain). Core Lean 4.14.
-/
namespace Retained

variable {α : Type}

/-- `TransGen` written out: `past x y`, row `x` is in the past of row `y`. -/
inductive Past (names : α → α → Prop) : α → α → Prop
  | one {x y} : names y x → Past names x y
  | step {x y z} : names z y → Past names x y → Past names x z

theorem past_trans (names : α → α → Prop) {x y z : α} (h1 : Past names x y) (h2 : Past names y z) :
    Past names x z := by
  induction h2 with
  | one h => exact Past.step h h1
  | step h _ ih => exact Past.step h ih

/-- The retained rows: the seeds (rows of keys not ended, and revocations) and everything in their past. -/
def retained (names : α → α → Prop) (seed : α → Prop) (x : α) : Prop :=
  seed x ∨ ∃ s, seed s ∧ Past names x s

/-- **Closed downwards**: a row a retained row has in its past is retained. So compaction leaves a kept set. -/
theorem retained_down_closed (names : α → α → Prop) (seed : α → Prop) {x y : α}
    (hx : retained names seed x) (hy : Past names y x) : retained names seed y := by
  rcases hx with hs | ⟨s, hs, hp⟩
  · exact Or.inr ⟨x, hs, hy⟩
  · exact Or.inr ⟨s, hs, past_trans names hy hp⟩

/-- A row a retained row names directly is retained. -/
theorem named_retained (names : α → α → Prop) (seed : α → Prop) {x y : α} (hx : retained names seed x)
    (hn : names x y) : retained names seed y :=
  retained_down_closed names seed hx (Past.one hn)

/-- Every revocation is retained, whatever ended. -/
theorem revocations_kept (names : α → α → Prop) (seed isRevoke : α → Prop) (h : ∀ r, isRevoke r → seed r)
    (r : α) (hr : isRevoke r) : retained names seed r := Or.inl (h r hr)

/-- A row that is not retained is in the past of no seed. -/
theorem dropped_unnamed (names : α → α → Prop) (seed : α → Prop) {x : α} (h : ¬ retained names seed x)
    (s : α) (hs : seed s) : ¬ Past names x s := fun hp => h (Or.inr ⟨s, hs, hp⟩)

/-- Fewer seeds retain fewer rows: as `now` moves on and keys end, nothing new is kept. -/
theorem retained_mono (names : α → α → Prop) (seed seed' : α → Prop) (h : ∀ s, seed s → seed' s) (x : α)
    (hx : retained names seed x) : retained names seed' x := by
  rcases hx with hs | ⟨s, hs, hp⟩
  · exact Or.inl (h x hs)
  · exact Or.inr ⟨s, h s hs, hp⟩

end Retained

#print axioms Retained.past_trans
#print axioms Retained.retained_down_closed
#print axioms Retained.named_retained
#print axioms Retained.revocations_kept
#print axioms Retained.dropped_unnamed
#print axioms Retained.retained_mono
