import sys
p=sys.argv[1]; out=[]
for l in open(p).read().split('\n'):
    if l.startswith('<<<<<<< ') or l.startswith('>>>>>>> '): continue
    if l == '=======': out.append(''); continue
    out.append(l)
s='\n'.join(out)
while '\n\n\n' in s: s=s.replace('\n\n\n','\n\n')
open(p,'w').write(s)
