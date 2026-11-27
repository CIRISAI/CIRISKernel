# The kernel declared as a holon

`kernel.holon.json` declares the `ciris-kernel` crate at tag `kernel-v0.2.1` (commit `0e7211e`) in the format of
[CIRISHolon](https://github.com/CIRISAI/CIRISHolon) (`standard/HOLON-DECL.md`, `ciris/holon-decl/0`, branch
`standard/holon-decl-v0` at `e98fc4c`). The Holon session drafted it and the Kernel session corrected and
filled it (issue #27).

What it is:
- A file this repository publishes. It is not a governed row.
- A statement of what was checked. Every view has the status `case_checked`: the Rust agrees with a reference
  on the cases named. Where a view has Lean theorems or a TLA+ spec, they are under `specification`: they are
  proved of a definition, and the Rust is tied to that definition by cases, not by extraction.
- It claims no closure in Holon's terms.

Every `printed` line is from one full `./check.sh` at the tag, run on one machine on 2026-11-23:
`all 19 steps passed`; 26 Lean files, 602 theorems; 36 conformance runs, 7,259,595 cases, 0 disagreements;
63 of 63 planted breaks caught; 5 TLA+ specs.

What it is not:
- Current. Main has moved since the tag, and the file says what it leaves out.
- Stable. The format is version 0 and not frozen; the file may need editing when it changes.
- Checked by anything here. No step of `./check.sh` reads it. Holon's compiler accepts its shape and answers
  `pending`, because the runs and digests it cites are held here and not in Holon's repository.
