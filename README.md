# CIRISKernel

**What a group of people needs in order to talk, share and govern itself with nobody in the middle, stated as
one function and proved.**

A network with no operator has no company to keep the files, order the messages, confirm a vote, decide who is
in a room, or remove someone who abuses it. Each of those jobs is why a platform sits in the middle today. This
repository is the part of the CIRIS constitution that does those jobs with nothing but the signed statements
people's own devices hold.

On one page, with a ten-person vote run three ways: <https://cirisai.github.io/CIRISKernel/>.

## What it is for

- **Your things on your devices.** Your files live on the devices you own and copy between them. A family's
  files live on the family's devices. Nothing is kept by a provider, because no provider is needed to say which
  copy is right.
- **Rooms without a host.** A room's members, its keys and its moderators are signed rows the members hold. A
  live video call or a group chat runs between the members' devices; no service in the middle admits people,
  holds the key or keeps the recording.
- **Decisions that are the group's.** A vote no single voice can carry, a moderator the members can recall, a
  removal that takes a count: each is a row signed by enough of the people it binds, and anyone holding it can
  check it.
- **AI agents that answer to people.** An agent acts under a named person's consent. What it cannot undo, it
  does only with the acknowledgement of those who could have stopped it. A halt reaches every node that
  receives it, and nothing an agent holds can disarm one in advance.

The kernel does not carry the bytes. It decides what the bytes mean: who is in the room, who holds the key,
what counts, what is still in force. The network that runs on it is described in the parent specification.

## Four constraints, and how each is met

For people to socialise and govern themselves with no operator, four things have to be true. Each is a reason
platforms exist; each is met here without one. That the four are needed is argued below. That the kernel meets
them is proved or run, with the limits stated.

| | The constraint | Without it | How the kernel meets it | Status |
|---|---|---|---|---|
| 1 | **Everyone holding the same statements reaches the same answer**, whatever order they arrived in. | Someone has to put events in order for everyone, and that someone is the middle. | The only order is what rows name. Admission reaches one kept set in every arrival order. | PROVED: [`Causal.lean`](proofs/Causal.lean), [`Order.lean`](proofs/Order.lean). RUN: [`check.py`](models/causal_kernel/check.py) |
| 2 | **A decision can become final without asking a central party, and without everyone online.** | Every admission, grant and vote waits on a confirming service, or can be undone for ever. | An act is final once n − t + 1 of the n members who could undo it have acknowledged it, where t can cut it. The number is exact, and it is the least coordination that works. | PROVED: [`Settled.lean`](proofs/Settled.lean) |
| 3 | **Nobody gains by saying two things, holding an office, or arriving later.** | Whoever equivocates fastest, or holds the admin seat, owns the group. | A seat is two consents. One signature never removes. A voice that both acknowledged and cut has no say there. A later officer acts forward and never rewrites what counted. | PROVED: [`Consent.lean`](proofs/Consent.lean), [`RosterHead.lean`](proofs/RosterHead.lean), [`Settled.lean`](proofs/Settled.lean). RUN: [`check_attacks.py`](models/causal_kernel/check_attacks.py) |
| 4 | **A phone can forget what is settled and still be right.** | Only a data centre can hold the whole history, and the data centre is the middle. | A node may cache, checkpoint and drop the bytes of settled acts. Dropping an unsettled act's rows is proved unsafe, with the case exhibited. | PROVED for a sufficient set: [`Settled.lean`](proofs/Settled.lean). RUN: [`check_purge.py`](models/causal_kernel/check_purge.py). OPEN: the least set to keep |

What is not shown: that these four are enough. That is a wager, stated with what would settle it in
[`OBJECT.md`](OBJECT.md) (move 8): an independent implementation that agrees with these models, and a deployment
under partition, delay, equivocation and crash. The implications for governing people and AI agents are in
[`GOVERNANCE.md`](GOVERNANCE.md), each with its evidence and what it does not give.

## The screen is the same function

Software has long tried to keep what a screen offers in step with what the system will accept, and has mostly
done it by synchronising two things: a model of the state and a view of it. Here there is one thing. A screen
is a function of the rows a node holds, the viewer's key and the clock, the same inputs as the kernel, so what
a person is offered, what an act would change, and whether the door admits it are one answer.

- **Proved, over one abstract family** (parent, [`formal/event_lifecycle`](https://github.com/CIRISAI/CIRISConstitution/tree/v1.0-rc19/formal/event_lifecycle)):
  every item a person is offered is a transition the door admits, and every transition it admits is offered
  (`queue_sound`, `queue_complete`, `door_is_queue`); the view an item previews is the view its execution gives
  (`preview_is_execution`).
- **Run, over the specification's own tables and the kernel's own rows** (parent,
  [`formal/screen`](https://github.com/CIRISAI/CIRISConstitution/tree/v1.0-rc19/formal/screen)): six properties, each
  with planted breaks that are caught. Nothing is drawn that the door refuses. Nothing admitted goes undrawn.
  Every arrival order draws the same screen. A fact that was not sent is never drawn as sent. Waiting is drawn
  as waiting, with what it waits on, never as refused or done. A confirmation appears exactly when an act
  widens who can see something or has no way back.
- **The vocabulary** is twenty-four screen primitives ([`data/ui_primitives.json`](data/ui_primitives.json),
  a draft standard: card, field row, item row, scope pill, action, confirm sheet, receipt sheet, and the rest),
  drawn in states the kernel names. A client builds its screens from these and checks them against the file.
- **The limit, measured:** twenty-five ways back that the text states have no transition in the table, so no
  screen built from the table can offer them. The screen checks run in the parent repository; they need its
  rule tables.

So a person is never shown a button the network would refuse, or a state that only their own device believes.

## Voting over the internet

The standing objection to voting over the internet is that somebody has to run the election: keep the roll,
collect the ballots, count them and announce the result. That party can be bought, blocked or broken, and the
voters cannot check it. Here nobody runs it.

- **The roll** is the group's own roster at the head the vote names. It is fixed by that head, every member can
  read it, and no one admitted later changes who was eligible.
- **One member, one say.** A person is one voice however many devices sign. A person whose ballots disagree has
  none.
- **An open vote** is signatures on a row. Anyone holding the rows recounts it, in any order of arrival, to the
  same result, and it is final once the count is met.
- **A secret vote** is counted without anyone seeing a ballot: each member's choice is split between two
  members drawn from the roster for that period, each adds up what it received, and only the total is
  published, above a minimum number of voters. Each accepted ballot adds exactly one to exactly one option. A
  member sends the same amount of data whether or not a vote is open, so an outsider cannot tell that one is
  being held.
- **Ranked choice** runs as one count that gives the same winner from the same ballots in any order.

What backs it, in the parent: the secret tally's invariants model-checked with a twin for each defence switched
off ([`formal/census_ballot`](https://github.com/CIRISAI/CIRISConstitution/tree/v1.0-rc19/formal/census_ballot)); ranked choice as an order-free count
([`formal/ranked_choice`](https://github.com/CIRISAI/CIRISConstitution/tree/v1.0-rc19/formal/ranked_choice)); an election's count proved, with a tie seating nobody
([`formal/moderator_election`](https://github.com/CIRISAI/CIRISConstitution/tree/v1.0-rc19/formal/moderator_election)). The kernel's part is the roll at a named head, the one
say, and the finality of a count.

**Its reach, stated exactly.** This is a solution for a body that admits its own members: a family, a co-op, a
union, a board, a neighbourhood, an online community, a federation of them. The members are the roll, and the
count needs no official. It is not shown for a public election, and four things stand between it and one:

- that each key is one living person is the group's own admission, and the kernel does not establish it;
- a ballot's secrecy assumes the two members who tally do not both collude, and the validity proof is assumed
  sound;
- nothing here stops a voter who is watched or paid from voting as told, and nothing protects a vote cast from
  a device someone else controls;
- members who withhold can stop a count from being met, though not falsify one.

## Where this comes from

The kernel is what results when a relational ontology is applied to ethics. The parent text's first commitment
is that a person is a person through other persons (the Ubuntu commitment, CC 1.13.1 of the parent, with the
same structure read from other traditions). Taken as engineering, that means nothing in the system has a state
of its own: every fact about a person, a device, a group or an authority is a signed relation between keys.
Standing is then consent between those it binds, authority is never a list, and the function over those
relations is the kernel. The ethics came first; the mechanism is what it required.

The full formal record, of which this repository carries the kernel's part, is the parent's
[`formal/`](https://github.com/CIRISAI/CIRISConstitution/tree/v1.0-rc19/formal): the life of a mesh as one model
that closes, the halt's fire path, consent, retirement, the census and the rest, each with its checks.

## What the kernel is

A function from a set of signed rows, a clock and a key to what every row means to the holder of that key. The
only order it uses is what rows name: a row names other rows by digest, and two rows where neither names the
other are concurrent. Standing comes only from signed consent, walked from the reader's own key. No node agrees
an order with another, and no coordinator is used.

The page: [`kernel/KERNEL.md`](kernel/KERNEL.md). The normative text: [`kernel/TEXT.md`](kernel/TEXT.md).

## The result, exactly

For any set of signed rows a node holds, and every later set containing them, every answer the kernel gives is
one of three kinds:

- **final by form**: whether a row is kept; its conclusion over its own causal past; a row that names a
  blocking set of receipts;
- **final by acknowledgement**: whether an act counts at the head it names, once n − t + 1 of the n members at
  that head have given clean receipts, where t can cut it. The threshold is exact in both directions;
- **provisional**: everything else, including whether the act is still in force at a later head. A voice seated
  later acts forward, never backwards.

No global order, no coordinator and no knowledge of the full row set is used. A node may cache, checkpoint and
purge accordingly, and dropping an unsettled act's rows is proved unsafe by an exhibited witness pair. One rule
is forced by symmetry and closure: a voice that has both acknowledged an act and voted to cut it, in rows
neither of which names the other, has no say there.

This is finality of authorisation against cuts. A key revoked back to a bound, a row's own stated end and a
reader's own trust are outside it; it says nothing about execution. **Not established**: the least set of rows
a node must keep; that a withdrawn receipt still blocks. The fork result is reader-relative until the
acknowledgement is held. Necessity assumes each voice that could cut can still sign. Nothing has been validated
by an independent implementation or a deployment under partition.

## Status

| Proved (Lean) | Run (models, to a bound) | Open |
|---|---|---|
| three kinds of finality, exact threshold, say rule, checkpoint: [`Settled.lean`](proofs/Settled.lean) | purge equals keeping everything, eight plants caught: [`check_purge.py`](models/causal_kernel/check_purge.py) | least set of rows to keep |
| one kept set in every arrival order: [`Causal.lean`](proofs/Causal.lean), [`Order.lean`](proofs/Order.lean) | one answer in every arrival order: [`check.py`](models/causal_kernel/check.py), [`check_cut.py`](models/causal_kernel/check_cut.py) | withdrawn receipt |
| a seat is two consents; one signature never removes: [`Consent.lean`](proofs/Consent.lean), [`RosterHead.lean`](proofs/RosterHead.lean) | thirty-four attacks, classed: [`check_attacks.py`](models/causal_kernel/check_attacks.py) | many acts purged at once |
| a reader's own line: [`Reader.lean`](proofs/Reader.lean) | one roster, five instances: [`check_rosters.py`](models/causal_kernel/check_rosters.py) | independent implementation; deployment |

Every theorem in plain words: [`proofs/README.md`](proofs/README.md). Every open item: [`REVIEW.md`](REVIEW.md).

## Build and run

Needs Lean 4.14.0 (no Mathlib) and Python 3.12 (standard library). Lean installs as the parent's
continuous build does it:

```
curl -sSfL https://github.com/leanprover/elan/releases/latest/download/elan-x86_64-unknown-linux-gnu.tar.gz | tar xz
./elan-init -y --default-toolchain leanprover/lean4:v4.14.0
```

Then, from the repository root, `./check.sh`. It compiles the twenty-six proof files, runs ten model checks
one after another and counts the divergence list, one line per step. It prints
`proofs: 26 files, 600 theorems reported, rc=0`, in about two minutes. Some checks use three worker processes.
The nineteen files carried from the parent are unchanged; the seven added here prove the crate's gaps
([`crates/ciris-kernel/FORMAL_GAPS.md`](crates/ciris-kernel/FORMAL_GAPS.md)).

Four steps build and test the Rust crate [`crates/ciris-kernel`](crates/ciris-kernel/README.md), the kernel as
pure functions with no dependencies, against the Python models' own cases; they need cargo. The last step
model-checks the five TLA+ specs of [`models/tla/`](models/tla) with TLC, each with a planted break it must
catch, and needs Java. The run ends `all 18 steps passed`.

## Lineage

The arithmetic is classical. Quorum intersection is Gifford, "Weighted Voting for Replicated Data" (SOSP '79);
the same argument where some voices sign both ways is Malkhi and Reiter, "Byzantine Quorum Systems"
(*Distributed Computing* 11(4), 1998). Finality from a locally checkable set of signed acknowledgements, with no
total order, is the approach of Guerraoui, Kuznetsov, Monti, Pavlovič and Seredinschi, "The Consensus Number of
a Cryptocurrency" (PODC '19). The split between answers that only grow and answers a later row can change is
Hellerstein and Alvaro, "Keeping CALM" (*CACM* 63(9), 2020). The closure normal form behind the checkpoint, that
a view is closed under adding rows exactly when no witness pair exists, is a standard factorisation argument
restated in `Settled.lean`. None of the pieces is new. What is here is the four constraints met together, for the acts by which people
share, admit, decide and remove, in one function with its proofs: the application of those results to a
governance grammar of signed rows, and the rules that application forces.

## What this is not

Not a consensus algorithm, and not a replacement for one: it gives no total order. Not a solution to
coordination in general: it answers whether an act's authorisation can still be cut, and who must acknowledge
it for that answer to be final. Not validated in deployment. Not a judgement of whether an act is wise.

## How to attack it

[`REVIEW.md`](REVIEW.md) gives the assumptions, the open problems, the adversarial runs already made, and how to
return a counterexample: a set of rows, one named question, the verdict the kernel gives and the verdict you
claim. [`OBJECT.md`](OBJECT.md) states the strongest defensible reading as eight moves, each with what would
kill it. [`CHARACTERISTICS.md`](CHARACTERISTICS.md) and [`GOVERNANCE.md`](GOVERNANCE.md) give its properties and
its implications for governing people and AI agents, each with its evidence.

## Where it comes from

The kernel of the CIRIS constitution, edition 1.0-rc19 (tag `v1.0-rc19`, carried from commit `60c741e`) of
<https://github.com/CIRISAI/CIRISConstitution>. The parent specification is the normative home; this is an
extract for review ([`PROVENANCE.md`](PROVENANCE.md)). Licence AGPL-3.0-or-later. Maintained by the CIRIS project.
