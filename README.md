# CIRISKernel

**What a group of people needs in order to talk, share and govern itself with nobody in the middle, stated as
one function and proved.**

A network with no operator has no company to keep the files, order the messages, confirm a vote, decide who is
in a room, or remove someone who abuses it. Each of those jobs is why a platform sits in the middle today. This
repository is the part of the CIRIS constitution that does those jobs with nothing but the signed statements
people's own devices hold.

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

Then, from the repository root, `./check.sh`. It compiles the nineteen proof files, runs ten model checks one
after another and counts the divergence list, one line per step. At the commit it was carried at it prints
`proofs: 19 files, 548 theorems reported, rc=0` and ends `all 12 steps passed`, in about two minutes.
Some checks use three worker processes.

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

The kernel of the CIRIS constitution, edition 1.0-rc19, commit `60c741e` of
<https://github.com/CIRISAI/CIRISConstitution>. The parent specification is the normative home; this is an
extract for review ([`PROVENANCE.md`](PROVENANCE.md)). Licence AGPL-3.0. Maintained by the CIRIS project.
