"""Attacks on consent.py (origin/consent-set 4b13dc6). python3 -I attack.py <src>/models/causal_kernel"""
import sys
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import consent as C
import key_end as KE
ST, CK = C.ST, C.CK
G, W, N_, B = C.grant, C.withdraws, C.note, C.binding
CAP, TRC = "capacity:cpu:v1", "trace:complete:v1"

def show(name, rows, asks):
    S = C.state(rows)
    out = []
    for a in asks:
        if a[0] == "send": out.append(("send",) + a[1:] + (C.may_send(S, *a[1:]),))
        elif a[0] == "peers": out.append(("peers",) + a[1:] + (sorted(C.peer_set(S, *a[1:])),))
        elif a[0] == "owner": out.append(("owner",) + a[1:] + (C.owner(S, *a[1:]),))
    print(name); [print("   ", o) for o in out]

# A1: the revoked key's thief writes a grant concurrent with the revocation, backdated before revoked_after
show("A1 thief grant at=2 < ra=3, concurrent with N's revocation, to attacker peer A",
     [G("g1", "N", "P", ("capacity:",), 1), KE.revoke("rv", "N", 3), G("gt", "N", "A", ("capacity:", "trace:"), 2)],
     [("send", "N", "A", TRC, None, None), ("peers", "N", None, None)])
# A2: the same thief takes over the fold of the honest grant to P (later instant, still < ra), broadening classes
show("A2 thief grant to P at=2.5 < ra=3 over honest g1 at=1 (capacity only)",
     [G("g1", "N", "P", ("capacity:",), 1), KE.revoke("rv", "N", 3), G("gt", "N", "P", ("capacity:", "trace:"), 2.5)],
     [("send", "N", "P", TRC, None, None)])
# A3: the owner's key revoked: its thief's backdated grant moves every owned node's rows
show("A3 owner O revoked ra=3; thief's grant at=1 concurrent with rv moves N's rows to A",
     B("b", "N", "O") + [KE.revoke("rv", "O", 3), G("gt", "O", "A", ("trace:",), 1), N_("n", "N", ("ab", "gt"))],
     [("send", "N", "A", TRC, "n", None), ("send", "N", "A", TRC, None, None)])
# A4: owner seat taken by a counted offer with no heads under a declared policy, need 0
xo = ST.offer("bx", "X", "X", "owner", "N", "group", (), policy="P:quorum", need=0)
show("A4 X offers itself N's owner seat, conf group, P:quorum need=0, no heads; no binding by N",
     [xo, G("gx", "X", "A", ("trace:",), 1), N_("n", "N", ("bx", "gx"))],
     [("owner", "N", "n"), ("send", "N", "A", TRC, "n", None)])
show("A4b the same beside N's real binding to O: two live owners, O's grant disabled",
     B("b", "N", "O") + [xo, G("go", "O", "P", ("trace:",), 1), N_("n", "N", ("ab", "bx", "go"))],
     [("owner", "N", "n"), ("send", "N", "P", TRC, "n", None)])
# A5: a regrant after a withdrawal with an earlier asserted_at than the withdrawn grant never takes effect
show("A5 g1 at=5 withdrawn, regrant g2 at=3 after it (clock skew): nothing moves",
     [G("g1", "N", "P", ("capacity:",), 5), W("w", "N", "g1"), G("g2", "N", "P", ("capacity:",), 3, ("w",)),
      N_("n", "N", ("g2",))], [("send", "N", "P", CAP, "n", None), ("peers", "N", "n", None)])
# A6: a far-future grant (pre-revocation thief, or a bad clock) locks the (signer, peer) chain for good
show("A6 g9 at=10**18 withdrawn; honest later regrant at=7 never in force",
     [G("g9", "N", "P", ("x:",), 10**18), W("w", "N", "g9"), G("g2", "N", "P", ("capacity:",), 7, ("w",)), N_("n", "N", ("g2",))],
     [("send", "N", "P", CAP, "n", None)])
# A7: a grant by O made before O was N's owner moves N's rows once the binding is held
show("A7 O's grant made before (not naming) the binding counts once O is owner",
     [G("go", "O", "P", ("trace:",), 1)] + B("b", "N", "O", ("go",)) + [N_("n", "N", ("ab",))],
     [("send", "N", "P", TRC, "n", None)])
# A8: the node's own pre-revocation grant: the owner cannot withdraw it; only the revoked key can
show("A8 N revoked; owner O's withdrawal of N's grant concludes nothing",
     B("b", "N", "O") + [G("g1", "N", "P", ("trace:",), 1), KE.revoke("rv", "N", 3, ), W("wo", "O", "g1", ("g1", "rv")),
                         N_("n", "N", ("ab", "wo"))],
     [("send", "N", "P", TRC, "n", None)])
# D1: a grant with no asserted_at
for nm, rows in (("D1 two grants, one without at", [G("g1", "N", "P", ("trace:",), None), G("g2", "N", "P", ("trace:",), 1)]),):
    try: show(nm, rows, [("send", "N", "P", TRC, None, None)])
    except Exception as e: print(nm, "-> Python raises", type(e).__name__, e)
