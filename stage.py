"""stage.py k: write the commit-k versions of the split files into the worktree, from scratchpad/final."""
import sys
F = '/tmp/claude-1000/-home-emoore-CIRISKernel/9f476e19-79a3-4f60-8019-6f13a6523575/scratchpad/final/'
W = '/home/emoore/CIRISKernel/.claude/worktrees/room-keys/'
k = int(sys.argv[1])


def cut(s, a, b):
    i = s.index(a)
    j = s.index(b, i)
    return s[:i] + s[j:]


def rep(s, a, b):
    assert a in s, a[:70]
    return s.replace(a, b)


counts = {1: (20, 4), 2: (20, 6), 3: (23, 7)}[k]
s = open(F + 'check_room_keys.py').read()
if k < 3:
    s = cut(s, '# two admissions of one person at once: the kernel', 'PLANTS = (')
    s = rep(s, '''    two admissions      the kernel seats both (CC 3.1.3.2: "no door refuses a widening for either, since no rule of
                standing reads a binding"). What the text owes about it is OPEN (#224).
''', '')
if k < 2:
    s = cut(s, '# a second seat row of one room key\nOPEN += [', '# two admissions' if k >= 3 else 'PLANTS = (')
    s = rep(s, '''    a second seat row   OPEN (#224: "what a second seat row of one room key does"). The text does not say.
''', '')
open(W + 'models/causal_kernel/check_room_keys.py', 'w').write(s)

c = open(F + 'CHANGELOG.md').read()
if k < 3:
    c = cut(c, '**Two admissions of one person at once**', 'The reference: `seat._revoked_before`')
if k < 2:
    c = cut(c, '**A second seat row of one room key**', 'The reference: `seat._revoked_before`')
c = rep(c, 'has 23 cases and 7 OPEN rows', 'has %d cases and %d OPEN rows' % counts)
open(W + 'crates/ciris-kernel/CHANGELOG.md', 'w').write(c)

r = open(F + 'README.md').read()
open_list = {1: 'Four OPEN rows record the answer as built and the candidates: a resignation racing a re-admission or a second acceptance.',
             2: 'Six OPEN rows record the answer as built and the candidates: a resignation racing a re-admission or a second acceptance (four rows), a second seat row of a room key, and a withdrawal of one of two.',
             3: None}[k]
if open_list:
    r = rep(r, 'Seven OPEN rows record the answer as built and the candidates: a resignation racing a re-admission or a second acceptance (four rows), a second seat row of a room key, a withdrawal of one of two, and what the text says of two admissions of one person at once.', open_list)
r = rep(r, '23 cases and 7 OPEN rows', '%d cases and %d OPEN rows' % counts)
open(W + 'models/README.md', 'w').write(r)
kk = rep(open(F + 'KERNEL.md').read(), '23 cases and 7 rows the text leaves OPEN', '%d cases and %d rows the text leaves OPEN' % counts)
open(W + 'kernel/KERNEL.md', 'w').write(kk)
g = rep(open(F + 'FORMAL_GAPS.md').read(), '`check_room_keys.py`, 23 and 7 OPEN', '`check_room_keys.py`, %d and %d OPEN' % counts)
open(W + 'crates/ciris-kernel/FORMAL_GAPS.md', 'w').write(g)
a = open(F + 'ADOPTING.md').read()
bul = '''- A second seat row of a room key already seated, and two admissions of one person under two room keys, are
  seated as any rows are (OPEN in `check_room_keys.py`); the cosigners' checks of the binding are the caller's.
'''
if k == 1:
    a = rep(a, bul, '')
elif k == 2:
    a = rep(a, bul, '''- A second seat row of a room key already seated is seated as any row is (OPEN in `check_room_keys.py`).
''')
open(W + 'crates/ciris-kernel/ADOPTING.md', 'w').write(a)
print("staged", k, counts)
