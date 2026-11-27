"""Every planted break's target text must occur in its file (the plants script asserts this only when it runs)."""
import shlex, sys, os
root=sys.argv[1]; bad=0; n=0
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
print(root.split('/')[-1],n,"plants,",bad,"with a target that is not in its file")
