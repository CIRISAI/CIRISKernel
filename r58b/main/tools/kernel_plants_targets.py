#!/usr/bin/env python3
"""
kernel_plants_targets.py: every planted break of tools/kernel_crate_plants.sh names text that is in the file it
plants into. The plants script finds a stale target only when it reaches that plant, a quarter of an hour in and
in one shard of four; this reads the script and the sources and takes a second.

    python3 -I tools/kernel_plants_targets.py     exit 1 if a plant's target is not in its file
"""
import os
import shlex
import sys

root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bad = 0
n = 0
lines=open(os.path.join(root,'tools/kernel_crate_plants.sh')).read().split('\n')
i=0
while i < len(lines):
    l=lines[i]
    if l.startswith('plant ') or l.startswith('plant_run '):
        buf=l
        while True:
            try: parts=shlex.split(buf); break
            except ValueError:
                i+=1; buf+='\n'+lines[i]
        name,f,old=parts[1],parts[2],parts[3]
        src=open(os.path.join(root,'crates/ciris-kernel',f)).read()
        n+=1
        if old not in src: bad+=1; print("MISSING:",name,"|",old[:90])
    i+=1
print("kernel_plants_targets: %d plants, %d with a target that is not in its file" % (n, bad))
sys.exit(1 if bad else 0)
