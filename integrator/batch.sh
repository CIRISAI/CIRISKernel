#!/bin/bash
# the batch: fixtures, the Python suite, cargo test, one grace job
cd /home/emoore/CIRISKernel/.claude/worktrees/release-0.5.0
fx=$(python3 -I tools/kernel_fixtures.py 2>&1); rc=$?
if [ $rc -ne 0 ]; then echo "fixtures: FAILED rc=$rc"; echo "$fx" | tail -40; exit 1; fi
echo "fixtures: regenerated (rc 0)"; echo "$fx" | grep -i "problem\|refus\|skipp" | head -10
chk=$(python3 -I tools/kernel_fixtures.py --check 2>&1); crc=$?; echo "fixtures --check rc=$crc: $(echo "$chk" | tail -2 | tr '\n' ' ')"
[ $crc -ne 0 ] && { echo "fixtures drift after regeneration"; exit 1; }
git status --short crates/ciris-kernel/tests/fixtures crates/ciris-kernel/tests/vectors | head -20
python3 -I tools/kernel_plants_targets.py
L="check_purge check_time check_key_view check_key_end check_conferral_end check_conferral_content check_conferral_two check_delegation check_duty_seats check_readmit check_recall check_ranked check_election check_acts check_charter check_lone_acts check_trust_rows check_resignation check_audience check_agent_removal check_window_rows check_policy_spec check_agent_seat check_removal_in_force check_room_keys room_key_vectors check_key_person check_count_heads check_roster_merge check_rosters check_consent check_attacks check check_cut check_roomkey"
for c in $L; do [ -f models/causal_kernel/$c.py ] || continue; s=$(date +%s); r=$(python3 -I models/causal_kernel/$c.py 2>&1); e=$?; echo "$c [$e, $(( $(date +%s)-s ))s]: $(echo "$r" | tail -1 | cut -c1-150)"; done
echo -n "check_root: "; python3 -I models/trust_root/check_root.py 2>&1 | tail -1
python3 -I models/roster_fork/fold_check.py 2>&1 | tail -1
cargo test --manifest-path crates/ciris-kernel/Cargo.toml --no-fail-fast > /tmp/claude-1000/-home-emoore-CIRISKernel/9f476e19-79a3-4f60-8019-6f13a6523575/scratchpad/int/ct.txt 2>&1; echo "cargo test rc=$?"
grep -n "^error\|^warning\|FAILED\|panicked\|could not compile\|targets\? failed\|merge refusal" /tmp/claude-1000/-home-emoore-CIRISKernel/9f476e19-79a3-4f60-8019-6f13a6523575/scratchpad/int/ct.txt | head -40
