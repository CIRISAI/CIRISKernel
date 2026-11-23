/-
  SeatCount.lean: the count a counted row is read by (KERNEL.md section 5, **stands**; CC 2.7.5, CC 3.3.4,
  CC 4.4.3.6; crates/ciris-kernel src/seat.rs, `seat_rule` and `met`).

  Over a finite universe `U` of keys, a counted row's voices are the keys that signed it, are members at the
  head it names, and are not keys the row itself seats (on a removal the member removed is a voice like any
  other, so there `named` is empty). This file proves: no key admits itself
  (its own signature never moves the count); the count never falls when a signature is added, so a count once
  met stays met; each policy is met by more voices whenever it is met by fewer; under `unanimous` a two-member
  group removes only with the consent of the one removed (CC 4.5.13, "at two coincide only if the one removed
  consents"); under
  `open:self_admit` one voice never removes; and a duty withdrawal never stands on one voice where there are
  two holders or more (CC 4.5.4 (iv)). Core Lean 4.14, no Mathlib.
-/
namespace SeatCount

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

theorem cnt_congr {β : Type} (p q : β → Prop) [DecidablePred p] [DecidablePred q] (h : ∀ x, p x ↔ q x) :
    ∀ l, cnt p l = cnt q l := fun l =>
  Nat.le_antisymm (cnt_mono p q (fun x hx => (h x).1 hx) l) (cnt_mono q p (fun x hx => (h x).2 hx) l)

open Classical

/-- The voices of a counted row: signed, a member at the head it names, and not a key the row names. -/
noncomputable def yes {K : Type} (U : List K) (signed mem named : K → Prop) : Nat :=
  cnt (fun k => signed k ∧ mem k ∧ ¬ named k) U

/-- **No key admits itself** (CC 2.7.5): whether a key the row seats signed it never moves the count. -/
theorem no_key_admits_itself {K : Type} (U : List K) (signed signed' mem named : K → Prop)
    (h : ∀ k, ¬ named k → (signed k ↔ signed' k)) : yes U signed mem named = yes U signed' mem named := by
  unfold yes
  apply cnt_congr
  intro k
  by_cases hn : named k
  · simp [hn]
  · have := h k hn; constructor <;> intro ⟨a, b, c⟩ <;> exact ⟨by first | exact this.1 a | exact this.2 a, b, c⟩

/-- A further signature never lowers the count: a count once met is final against the members' later rows. -/
theorem yes_mono {K : Type} (U : List K) (signed signed' mem named : K → Prop) (h : ∀ k, signed k → signed' k) :
    yes U signed mem named ≤ yes U signed' mem named :=
  cnt_mono _ _ (fun k ⟨a, b, c⟩ => ⟨h k a, b, c⟩) U

/-- The policies of the table, as the kernel reads them (`seat::Policy`). -/
inductive Policy
  | atLeast (num den : Nat)
  | strict (num den : Nat)
  | one
  | declared (need : Nat)
  | unanimous (others : Nat)     -- the members the row does not name
  | notACount

/-- `seat::met`, with `unanimous` as CC 3.3.4 reads it for a removal: every other member, and a strict
    majority of the roster. -/
def met : Policy → Nat → Nat → Prop
  | .atLeast num den, y, n => 0 < n ∧ num * n ≤ y * den
  | .strict num den, y, n => num * n < y * den
  | .one, y, _ => 1 ≤ y
  | .declared need, y, _ => need ≤ y
  | .unanimous others, y, n => y = others ∧ n < 2 * y
  | .notACount, _, _ => False

/-- More voices never fail a count that fewer met (`unanimous` is exact, so it is met only at all others). -/
theorem met_mono (p : Policy) (y y' n : Nat) (hy : y ≤ y') (hp : ∀ o, p ≠ .unanimous o) (h : met p y n) :
    met p y' n := by
  cases p with
  | atLeast num den => exact ⟨h.1, Nat.le_trans h.2 (Nat.mul_le_mul_right den hy)⟩
  | strict num den => exact Nat.lt_of_lt_of_le h (Nat.mul_le_mul_right den hy)
  | one => exact Nat.le_trans h hy
  | declared need => exact Nat.le_trans h hy
  | unanimous o => exact absurd rfl (hp o)
  | notACount => exact h

/-- Under `unanimous`, the other member of a two-member group does not remove alone (CC 4.5.13): `y` here is
    the others' voices, the one removed not signing. -/
theorem unanimous_two_others_alone_remove_nobody (y : Nat) : ¬ met (.unanimous 1) y 2 := by
  intro ⟨h1, h2⟩; omega

/-- A `unanimous` removal with the voice of the one removed counted (CC 2.7.5, CC 4.5.13): every other member
    signs (`yo` of `others`), and the voices `y`, the one removed among them if it signed, are a strict
    majority of the roster `n`. Its yes cannot stand in for another's. -/
def unanimousRemoves (others yo y n : Nat) : Prop := yo = others ∧ n < 2 * y

/-- At two, a `unanimous` removal stands only if the one removed consents: its voice is counted beside the
    other's. -/
theorem unanimous_two_only_by_consent (yo y : Nat) (hy : y ≤ yo + 1) (h : unanimousRemoves 1 yo y 2) :
    y = yo + 1 := by
  obtain ⟨h1, h2⟩ := h; omega

/-- And with that consent it stands. -/
theorem unanimous_two_with_consent : unanimousRemoves 1 1 2 2 := ⟨rfl, by omega⟩

/-- The yes of the one removed never stands in for a member who did not sign. -/
theorem unanimous_consent_is_no_substitute (others yo y n : Nat) (hm : yo < others) :
    ¬ unanimousRemoves others yo y n := by
  intro ⟨h1, _⟩; omega

/-- Under `unanimous`, a removal by every other member of three or more stands. -/
theorem unanimous_others_remove (n : Nat) (h : 3 ≤ n) : met (.unanimous (n - 1)) (n - 1) n := by
  refine ⟨rfl, ?_⟩; omega

/-- A strict majority of n is met by one voice only when n = 0 or n = 1. -/
theorem strict_one_voice (n : Nat) (h : met (.strict 1 2) 1 n) : n ≤ 1 := by
  simp [met] at h; omega

/-- `open:self_admit`: a removal takes two voices besides the member named, so one never removes. -/
def selfAdmitRemoves (y : Nat) : Prop := 2 ≤ y

theorem self_admit_one_never_removes : ¬ selfAdmitRemoves 1 := by
  unfold selfAdmitRemoves; omega

/-- CC 4.5.4 (iv), the duty withdrawal over `n` holders with `y` of the others signing: a strict majority of
    the others, and two voices where there are two holders or more. -/
def dutyWithdraws (y n : Nat) : Prop := (n - 1) < 2 * y ∧ (2 ≤ y ∨ n < 2)

theorem duty_withdrawal_needs_two (n : Nat) (h : 2 ≤ n) : ¬ dutyWithdraws 1 n := by
  intro ⟨_, h2⟩; omega

/-- The weighted sum of the voices (CC 3.3.4 `weighted:{rubric}`): whole-number weights from the record. -/
def wsum {K : Type} (w : K → Nat) (p : K → Prop) [DecidablePred p] : List K → Nat
  | [] => 0
  | k :: ks => (if p k then w k else 0) + wsum w p ks

theorem wsum_mono {K : Type} (w : K → Nat) (p q : K → Prop) [DecidablePred p] [DecidablePred q]
    (h : ∀ k, p k → q k) : ∀ l, wsum w p l ≤ wsum w q l
  | [] => Nat.le_refl 0
  | k :: ks => by
    simp only [wsum]
    have ih := wsum_mono w p q h ks
    by_cases hp : p k
    · simp [hp, h k hp]; omega
    · by_cases hq : q k <;> simp [hp, hq] <;> omega

/-- Under `weighted`, a further signature never lowers the sum, so a threshold once met stays met; and a key
    the row seats adds nothing whether it signed or not. -/
theorem weighted_mono {K : Type} (U : List K) (w : K → Nat) (signed signed' mem named : K → Prop)
    (h : ∀ k, signed k → signed' k) :
    wsum w (fun k => signed k ∧ mem k ∧ ¬ named k) U ≤ wsum w (fun k => signed' k ∧ mem k ∧ ¬ named k) U :=
  wsum_mono w _ _ (fun k ⟨a, b, c⟩ => ⟨h k a, b, c⟩) U

end SeatCount

#print axioms SeatCount.cnt_mono
#print axioms SeatCount.cnt_congr
#print axioms SeatCount.no_key_admits_itself
#print axioms SeatCount.yes_mono
#print axioms SeatCount.met_mono
#print axioms SeatCount.unanimous_two_others_alone_remove_nobody
#print axioms SeatCount.unanimous_two_only_by_consent
#print axioms SeatCount.unanimous_two_with_consent
#print axioms SeatCount.unanimous_consent_is_no_substitute
#print axioms SeatCount.unanimous_others_remove
#print axioms SeatCount.strict_one_voice
#print axioms SeatCount.self_admit_one_never_removes
#print axioms SeatCount.duty_withdrawal_needs_two
#print axioms SeatCount.wsum_mono
#print axioms SeatCount.weighted_mono
