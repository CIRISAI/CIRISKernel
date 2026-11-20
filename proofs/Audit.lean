/-  The semantic audit. Elaborating this file is the check: every theorem, lemma and definition declared in the
    proof stack (the modules imported below) depends on no axiom beyond propext, Quot.sound and Classical.choice.
    That covers sorryAx, which a sorry anywhere leaves behind, including in a lemma no printed theorem uses.
    build.sh checks only the theorems with a #print axioms line; this checks every declaration.
    Run by build.sh after the stack is built. build.sh fills in the imports and the module list from its own
    files= list, so a file added to the stack is audited without a second list to keep. -/
import Lean
-- IMPORTS: build.sh puts one `import` per file of its files= list here

open Lean Elab Command

/-- The modules of the stack: the files build.sh compiles. -/
def stackModules : List Lean.Name := [] -- MODULES: build.sh lists the same files here

def coreAxioms : List Lean.Name := [``propext, ``Quot.sound, ``Classical.choice]

#eval show Lean.Elab.Command.CommandElabM Unit from do
  let env ← getEnv
  let mods := stackModules
  let mut checked := 0
  let mut bad : Array (Lean.Name × Array Lean.Name) := #[]
  for (c, _) in env.constants.toList do
    let some idx := env.getModuleIdxFor? c | continue
    let some m := env.header.moduleNames[idx.toNat]? | continue
    unless mods.contains m do continue
    if c.isInternal then continue
    checked := checked + 1
    let axs ← liftCoreM (Lean.collectAxioms c)
    let extra := axs.filter (fun a => !coreAxioms.contains a)
    unless extra.isEmpty do bad := bad.push (c, extra)
  if bad.isEmpty then
    logInfo m!"audit: {checked} declarations in {mods.length} modules, every one on core axioms only"
  else
    for (c, e) in bad do logError m!"audit: {c} depends on {e}"
    throwError m!"audit: {bad.size} declarations depend on an axiom beyond the three of core"
