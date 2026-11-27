def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, s.count(a), a)
        s = s.replace(a, b)
    open(p, 'w').write(s)

edit('crates/ciris-kernel/src/lib.rs', [
('''//! | [`content`] | CC 2.4.1.1 | room content after a member's seat ends: the rows the end holds good |
''','''//! | [`content`] | CC 2.4.1.1 | room content after a member's seat ends: the rows the end holds good |
//! | [`standing`] | CC 3.1.2.1 | one row under a root grant and an owner binding: the chain of names, per owner |
'''),
('''pub mod seat;
pub mod trust;''','''pub mod seat;
pub mod standing;
pub mod trust;'''),
])
edit('models/causal_kernel/check_conferral_two.py', [
('''    which it ends), `acceptance` (`on` the binding it is made under), `act` (`head` the bundle version it names,
    `on` the row it stands on), `end` (the grant's end, `head`), `receipt` (`on` the act).
''','''    which it ends), `acceptance` (`on` the binding it is made under), `act` (`head` the bundle version it names,
    `on` the row it stands on), `end` (the grant's end, `head`), `receipt` (`on` the act), `removal` (`target`
    the key; read in both records. No case has one).
'''),
('''            if k == "receipt":
                row["of"] = r["on"]
''','''            if k == "receipt":
                row["of"] = r["on"]
            if k == "removal":
                row["target"] = signer_of(r["target"])
'''),
('''    kinds = {"bundle": "head", "act": "act", "end": "end", "receipt": "receipt"}
''','''    kinds = {"bundle": "head", "act": "act", "end": "end", "receipt": "receipt", "removal": "removal"}
'''),
('''            return ("receipt" if r["kind"] == "receipt" else "other"), None
''','''            return (r["kind"] if r["kind"] in ("receipt", "removal") else "other"), None
'''),
])
edit('tools/kernel_fixtures.py', [
('''              root grant): its case table, per act and owner. No Rust test reads it; it is for Verify's
              standing walk and an adopter's own code.
''','''              root grant), and a later bundle version: its case table, per act and owner, with why.
              tests/conferral_two.rs replays it through standing::answers; it is also for Verify's standing
              walk and an adopter's own code.
'''),
])
s = open('tools/kernel_conformance_runs.txt').read()
s += '''one row under a root grant and an owner binding (check_conferral_two.py case table, acc)
one row under a root grant and an owner binding, one row not held (undecided, never a wrong bit)
'''
open('tools/kernel_conformance_runs.txt', 'w').write(s)
