#!/bin/bash
# run one command through grace from the worktree; usage: one.sh "<kind>" <peak> <command...>
cd /home/emoore/CIRISKernel/.claude/worktrees/release-0.5.0
k="$1"; p="$2"; shift 2
grace-sched run --owner CIRISKernel --kind "$k" --peak "$p" --priority low -- bash -c "$*" 2>&1 | grep -v "^grace-sched: .*\(queued\|running\)"
