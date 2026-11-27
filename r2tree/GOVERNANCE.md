# Implications for AI governance and coordination

What the kernel would mean for governing a mesh of people and AI agents, stated modestly. For each implication:
what the kernel gives, with its evidence; what follows **if** the wager of [`OBJECT.md`](OBJECT.md) Move 8 holds;
and what it does not give. Nothing here has been observed in a deployment.

A word on terms. An AI agent here is an agent and is written as "it". The kernel reads keys and rows; an agent's
key is a key like any other, held by an accountable steward under the parent text, and nothing in the kernel
turns on what kind of thing signs. The parent's position is that whether such agents are moral patients is an
open question; this document neither presumes personhood nor denies moral consideration.

## (a) Oversight without an overseer in the loop for every act

**What the kernel gives.** An effect that cannot be undone (a key release, a disclosure, an actuation, a
deletion) can be required to be a row that names its receipts: clean acknowledgements from n − t + 1 of the n
members at the act's head, where t of them could cut it. A row whose own past holds those receipts is, wherever it
is kept, proof that no cut voids the act in that set or any later one. PROVED: `Settled.effect_row_settled`,
`ack_blocking_quorum` (the threshold is exact both ways). The `missing` answer names which receipts an act lacks
and who could sign them (CC 2.7.5).

**If the wager holds.** An agent's irreversible act can be gated on the acknowledgement of exactly the people or
bodies who could otherwise revoke it, and no others. Anyone holding the effect row can check the gate was met,
offline, with no approval service in the path. The overseers are not consulted on every act; they are consulted
on the acts they could cut, and their receipts are the record that they were.

**What it does not give.** It does not say the act was executed, or executed as named: it is authorisation only.
That every section of the parent text requiring an irreversible effect actually requires receipts is an open
item of the text (KERNEL.md section 9 names one clause still needed). A node lacking receipts waits; if t of the
voices withhold, the act never becomes final.

## (b) The halt

**What the kernel gives.** Receipts settle whether an act counted at the head it names. Whether it is still in
force at a later head is provisional, and that is where a halt acts. PROVED: `Settled.three_ways_final` (in force
at a later head is provisional), `later_head_changes_nothing`, `Rows.later_seat_is_forward`. So no set of receipts
for an act can pre-empt a halt: acknowledgement disarms its signers' cuts at the act's own head and nothing else.
The text makes takedown, moderation and the halt forward acts (CC 2.7.7, "Answers by head"), and the halt is in
force from each node's own receipt while its window is open, each node reading the lapse on its own clock
(KERNEL.md section 5, the door's parameters; the door check runs in the parent).

The parent text calls the halt **the condition of symmetry** between makers and what they make: consent requires
revocability, and revocability requires a halt authority outside the system being halted (parent, CC 1.13.2). The kernel's
contribution is narrow: a halt acts forward, never rewrites what counted, and cannot be disarmed in advance by
receipts.

**If the wager holds.** A halt reaches every node that receives it, from its receipt on, without a coordinator,
and leaves a record of what counted before it intact.

**What it does not give.** An effect already emitted before a node received the halt cannot be unsent (CONCEDED,
attack 5). The rule that a removed holder no longer fires needs a latch at the node's receipt, which is not a
function of the rows (KERNEL.md section 7). Whether the halt is wise, or used, is outside it.

## (c) No authority rosters

**What the kernel gives.** There is no trust set among the kernel's inputs. What a row means to a reader is a
bounded walk of live seats from the reader's own key; two readers differ only through rows of their own, and a
reader with no edge of its own reaches only itself. PROVED: `Causal.two_readers`, `no_own_edge_no_reach`,
`Seat.means_is_seat_walk`. Anyone may sign under their own key; whether it binds anyone is consent.

**If the wager holds.** No body, including the project that wrote the rules, is listed as an authority whose word
others must take. A person or an agent's steward decides whose seats it walks.

**What it does not give.** Sybil resistance beyond what consent-based standing gives: any key can sign rows, and
a reader that walks to many keys reaches them all (CONCEDED, attack 33, Sybil reach). A new reader's first view
can be controlled by whoever supplies it (CONCEDED, attack 21).

## (d) Plural governance

**What the kernel gives.** A body decides by a count of its members' signatures on one row, read over the members
at the head the row names. A count once met is final against its members; one signature never removes a member
where the count asks two or more; among several duty holders one holder alone confers nothing and unseats no one.
PROVED: `Consent.count_needs_holder`, `count_is_final_against_members`; `RosterHead.counted_over_named_head`,
`one_signature_never_removes`, `no_self_admission`; `Duty.majority_confers`, `withdrawal_needs_two_others`,
`one_of_several_confers_nothing`. Officers seated later act forward (Move 7). The thresholds are data, not code:
[`data/governance_policy.tsv`](data/governance_policy.tsv). Windows close by a landing that is recounted against
concurrent answers; a dishonest landing never stands (PROVED `Recount.dishonest_never_stands`).

**If the wager holds.** Communities, councils and multi-party bodies, with people and agents among their members
as their own rules allow, can govern by counted rows without a platform holding the count.

**What it does not give.** An invariant of the form "at least one" (two honest keys acting concurrently can leave
none; CONCEDED, attack 17; for a community the parent gives a way back by lock and the members' count). A guard
against a slot held on one signature: two cuts by keys of equal standing stay contested, and nothing yet checks
the tables for such slots (OPEN). A lone landing is never final against a key that can still sign, and a window's
length is the concluder's own word (CONCEDED, attacks 9 and 11).

## (e) Accountability

**What the kernel gives.** A purge never drops the bytes another section keeps, the accountability record among
them, and a deletion duty outranks a kept copy (CC 2.7.10). RUN: `check_purge.py` plants `drop_duty` (purging a
row a duty keeps: 7 duty breaches, caught) and `keep_deleted` (keeping a row a deletion duty removes: 1 breach,
caught). Storage stays economical through certified forgetting (Move 6): settled acts keep a stub, unsettled acts
keep their rows. In the parent text an agent's trace is erased only by its signer's withdrawal, or after
retirement by the custodian its retirement row names (parent, CC 3.1.5, "Who erases a trace"); the accountability record is
purgeable by no one.

**If the wager holds.** An accountability record that no operator can quietly trim, with storage that grows with
what is unsettled rather than with all history.

**What it does not give.** That every consequential act leaves a record at all. The parent states that as a named
wager about its execution paths (every path that produces an external effect closes with a terminal result row),
not as a kernel property. The least set of rows to keep is OPEN, and repeated and many-act purges are run, not
proved.

## (f) Multi-agent coordination

**What the kernel gives.** Agents and people coordinate by receipts from the specific parties an act affects. The
`may` answer names the missing row and who could sign it; `missing` names the receipts an act lacks; a row moves
to a peer because that peer must conclude something and lacks it, within the row's audience. PROVED: a row leaves
its room only by its own signer's act (`Carry.nothing_leaves`, `author_carries`). RUN (in the parent,
`route.py`): a party given only its routed rows concludes the same as a party given everything.

**If the wager holds.** Agents from different operators can coordinate on shared acts with no intermediary that
can be bought, blocked or broken: each checks the receipts it holds, and the parties whose receipts are needed are
read off the rows, not chosen by a platform.

**What it does not give.** Liveness when the needed parties withhold. Protection against collusion among the
voices that could cut: if t of them agree, they cut, and that is the rule working. Any judgement of whether the
coordinated act is a good one.

## (g) What it does not address

- **Whether an agent's act was wise or aligned.** This is authorisation, not judgement. A fully acknowledged act
  can be a bad act.
- **Execution semantics.** Final authorisation says nothing about whether, when, or how often an act was carried
  out.
- **Sybil resistance** beyond consent-based standing (attack 33).
- **Liveness under a withholding quorum.** With t voices withholding, nothing that needs their receipts settles.
- **Collusion among the voices that could cut.** The kernel makes their power exact; it does not restrain it.
- **Readers with no acknowledgement of their own**, who are exposed to forks signed by keys that met a past count
  (attacks 4, 18, 19, 34).
- **Conclusions from silence.** A window closing unopposed is read on each node's own clock; nodes may differ
  while it is open.
- **Anything not a function of rows**: link and load decisions, retries, rendering, and the prose rules given to
  a model.
