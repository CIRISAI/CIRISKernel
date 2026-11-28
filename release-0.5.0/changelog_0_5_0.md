## 0.5.0

**What 0.5.0 is.** The kernel now decides who holds what over a room, and how a row counts, from rows alone.
No stated instant decides a verdict, and the host clock decides none.

- **The seat model.** Every seat is two consents. A seat ends by ancestry, never by an instant. Counted acts name the
  newest counted changes in their own past (heads H1 to H8). Rule 5 holds on every counted act. Families,
  infrastructure communities (M of N), affiliations with officers, and lone duty acts (quarantine, slashing,
  takedown, reconsideration) are all read by one seat walk.
- **Persons.** Every count is a count of persons. A person is named by its self roster's genesis key, and its other
  live keys are its devices (`seat::Persons`). Officers are counted by person too.
- **The key view.** Every count's voices step reads the key view first: a dead key is out, and only then are the
  living keys mapped to persons (`CutSpec::key_view`, `key_end::counts_by`).
- **Windows from the policy table.** A window's rule is read from the pinned governance policy table
  (`window::spec_from_policy`). The table's cells decide the opener, the base, the count and the leaves.
- **The consent peer set.** A `consent:replication:v1` grant moves the classes it names to one peer, and nothing else
  (`consent::in_force`, `peer_set`, `may_send`, `replication_set`).
- **The election close.** An election closes on rows. Its seating is read by C1 to C5 at the reader's line
  (`seat::election_closed`).
- **The wire map and 70 vectors.** `WIRE_MAP.md` maps every row-view field to its `ceg-row/2` source. `VECTORS.md`
  states 70 neutral cases, each with its rows, its query and its expected answer, for Verify to mint.

**BREAKING for adopters.** "Adopting 0.5.0 from 0.2.2" below lists every change. In brief:

- New required trait methods: `SeatRow::word`, and `SeatRow::consensus_protocol` in practice (with `None`, no room
  has a protocol). There are new traits: `Dated`, `TrustRow`, `RootBundle`, `RootGrant`, `RootView`, `StandingRow`,
  `ConsentRow`, `AudienceRow`, `KeyView`.
- Enum changes an exhaustive `match` must add. `SeatKind` gains `Decline` and the four lone-act kinds; there is no
  `Countersign`, because a countersign is a voice on the act's own row. `Policy` and `RoomProtocol` lose
  `SelfAdmit`, since open admission is cut for 1.0.
- Struct changes: `SeatLaw` gains `acts`, `kinds` and `removal_floor`. `window::PolicyRow` gains the table's new
  cells. `head::Entry` gains `at`.
- Removed: `trust::honours`, `charter::read_licence`, `SeatRow::consent_one`, `SeatRow::merge_duties`.
- Keys: `seat::registered_ends` takes `rotated`, so a retired key's registered self-unseat is no end (review-48's
  r110, r114). `seat::Persons::over` takes the key view, so no person map silently misses a key-lane revocation
  (r108); `key_end::none()` names the view for an adopter with no key lane. `consent::Reading` is required.
- Owners come from concluded rows only (review-53's r116 K2 class): a holder's keys merge only through a concluded
  recovery or a concluded rotation its old key signs. A row that concludes nothing (a junk `rotates` or
  `recovers`) merges no keys, so it cannot capture another holder's seat.
- The device-stolen remedy: another live device of the granting person withdraws its grant
  (`consent::may_withdraw`), and the end of a device key as the person's (an eviction, or a `registered`
  revocation concurrent with the withdrawal) cuts a withdrawal standing on it.
- Presentation rules that change answers with no error: the heads H1 to H8, the reader's line (`for_reader`), the act
  binding, the closed protocol set, persons over keys, the key view, and real rows only.
- A row cites by `cites()` exactly one row (a reconsideration its notice, a lift its act). A quarantine release names
  its withhold by `target()`.

**Stated residuals.** Each is a case. No rule can close them, because the rows do not show them.

- **One or two keys.** A self roster's evicted key is no voice of its own eviction. So a roster whose only live key
  is its genesis key cannot evict that key, and a two-key roster evicts only by the lone path, when the other key
  is silent through the window. A person with one key whose key is stolen and then revoked has no other device to
  withdraw with.
- **The lone-add entrenchment** (CC 3.3.6.4, in the Constitution's words): "a holder of one key of three that adds a
  key while one other is silent holds half the roster, and no count or lone path removes it".
- **The unlinked-keys residual.** Two keys one person keeps unlinked, in no shared roster, are two persons to every
  rule. Persons are read in the act's own past: a binding written alongside the act or after it does not make an
  outside voice (an outside countersign included) the person's own.
- **A fresh reader holding rivals waits.** One self roster per identity is read by the reader's line. A reader whose
  line takes up neither rival founding, or both, reads no person through them and waits.
- **The election close.** A holder that lays a seat down twice, once stale and once current, with the election
  citing the stale one: a reader that acknowledged a head between them sees an empty seat until it acknowledges
  the election's seating, and then it converges.
- **One batch at one head.** A reader at g, whose line holds only g or a change at g, reads the same voices' duty
  conferrals at g as one batch until it acknowledges anything newer than g or holds any later row by the signers.
- **The FD1 split** (r103). The signer's own concurrent regrants, each naming one fork, settle nothing (the fold
  fails closed). The next regrant naming both does.

**Undecided cells.**

- Family placement: 189 families, 143 on the default and 46 pinned by the table, 0 undecided. The pin is
  CIRISConstitution rc23-next 0e80f21 (policy pin 85750784; `family_model.json` sha256
  9d49c2a7d197cb95310165ca8052732c6c274b27e09e61da3d43dae6dce66bcc). It becomes final once the Constitution's formal
  run lands rc23 on it.
- The policy table (pin 85750784): four families carry `unstated` cells.
  - `custodian_replace`, `affiliation_member_action` and `cosigned_act` have an unstated counted voice; the first
    two also have an unstated `counted_at`.
  - `poll` has an unstated opener, `opener_says` and answer words.
  - The seat law (`tables::law_from_tables`) reads only a family's enact cell. So the three counted families take
    their counts from the table: `custodian_replace` and `affiliation_member_action` at least 2 of 2, and
    `cosigned_act` under the room's declared protocol. `poll` has no count (`NotACount`). The unstated voice cell is
    not read there, and no fallback is stated. A count reads voices by person through `seat::Persons`, not from
    this cell. `cosigned_act` and `affiliation_member_action` are read with the voices the Constitution's rulings
    give (the body's deciding seats under its protocol; one officer and one eligible outside key), pending those
    cells in the policy table; `custodian_replace` is held shut. The cells go into the table with the text after
    the tag.
  - `window::spec_from_policy` gives none of the four a window table. Each is refused by its kind (`not_a_window`:
    cosigned and tally rows give no window table even with every cell stated), and also on its unstated cells. So
    the unstated cells block nothing in the window path today. A poll is not in this tag, and the adopter holds it
    shut.
- Where the crate answers `Undecided`, re-ask once the row it names is held.
