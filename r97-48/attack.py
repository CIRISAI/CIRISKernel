"""Re-attack on consent.py (origin/consent-set c4732be). python3 -I attack.py <src>/models/causal_kernel
Grants are held between the two nodes (fed=False) unless a case says federation."""
import sys
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import consent as C
import key_end as KE
ST, CK = C.ST, C.CK
W, N_, B, AN = C.withdraws, C.note, C.binding, C.announce
CAP, TRC = "capacity:cpu:v1", "trace:complete:v1"
def G(*a, fed=False, **kw): return C.grant(*a, fed=fed, **kw)
def rev(id, key, ra, names=()): return CK.row(id, "revoke", key, tuple(names), key=key, ra=ra)

def show(name, rows, asks, reader=None):
    S = C.state(rows)
    kv = C.key_view(S, reader)
    print(name + ("   [reader %s]" % reader if reader else ""))
    for a in asks:
        if a[0] == "send": got = C.may_send(S, *a[1:], kv=kv)
        elif a[0] == "peers": got = sorted(C.peer_set(S, *a[1:], kv=kv))
        elif a[0] == "concl": got = bool(S.C.get(a[1]))
        print("   ", a, "->", got)

# ---- the earlier attacks, re-run
show("A1 thief grant to A at=2 < ra=3, concurrent with N's revocation (names g1)",
     [G("g1", "N", "P", ("capacity:",), 1), rev("rv", "N", 3, ("g1",)), G("gt", "N", "A", ("capacity:", "trace:"), 2, ("g1",))],
     [("send", "N", "A", TRC, None, None), ("peers", "N", None, None)])
show("A2 thief grant to P at=2.5 over honest g1",
     [G("g1", "N", "P", ("capacity:",), 1), rev("rv", "N", 3, ("g1",)), G("gt", "N", "P", ("capacity:", "trace:"), 2.5, ("g1",))],
     [("send", "N", "P", TRC, None, None), ("send", "N", "P", CAP, None, None)])
A3 = B("b", "N", "O") + [G("g0", "O", "Q", ("x:",), 1, ("ab",)), rev("rv", "O", 3, ("g0",)),
                         G("gt", "O", "A", ("trace:",), 1, ("g0",)), N_("n", "N", ("ab", "gt"))]
show("A3 owner O revoked; thief's grant, N's row n names it (N had not held rv)", A3,
     [("send", "N", "A", TRC, "n", None), ("send", "N", "A", TRC, None, None)])
show("A3 same, read for reader N (the sending node)", A3, [("send", "N", "A", TRC, "n", None), ("send", "N", "A", TRC, None, None)], reader="N")
show("A3 + N later holds rv and names it: still taken up on N's line", A3 + [N_("n2", "N", ("n", "rv"))],
     [("send", "N", "A", TRC, "n2", None)], reader="N")
show("A3 + who can end gt: N's own withdrawal of O's grant", A3 + [W("wn", "N", "gt"), N_("n3", "N", ("wn",))],
     [("concl", "wn"), ("send", "N", "A", TRC, "n3", None)], reader="N")
show("A3 + the revoked O key withdraws gt (no key view on withdrawals)", A3 + [W("wo", "O", "gt", ("rv",)), N_("n3", "N", ("wo",))],
     [("concl", "wo"), ("send", "N", "A", TRC, "n3", None)], reader="N")
show("A5 g1 at=5 withdrawn, regrant g2 at=3 naming w",
     [G("g1", "N", "P", ("capacity:",), 5), W("w", "N", "g1"), G("g2", "N", "P", ("capacity:",), 3, ("w",)), N_("n", "N", ("g2",))],
     [("send", "N", "P", CAP, "n", None)])
show("A6 g9 at=10**18 withdrawn, regrant at=7 naming w",
     [G("g9", "N", "P", ("x:",), 10**18), W("w", "N", "g9"), G("g2", "N", "P", ("capacity:",), 7, ("w",)), N_("n", "N", ("g2",))],
     [("send", "N", "P", CAP, "n", None)])
show("A6b g9 at=10**18 concurrent with a regrant that does not name it (not withdrawn): g9 wins",
     [G("g9", "N", "P", ("x:",), 10**18), G("g2", "N", "P", ("capacity:",), 7), N_("n", "N", ("g2", "g9"))],
     [("send", "N", "P", CAP, "n", None), ("send", "N", "P", "x:y", "n", None)])
show("A7 O's grant made before the binding",
     [G("go", "O", "P", ("trace:",), 1)] + B("b", "N", "O", ("go",)) + [N_("n", "N", ("ab",))], [("send", "N", "P", TRC, "n", None)])
show("A8 N revoked; owner O withdraws N's grant",
     B("b", "N", "O") + [G("g1", "N", "P", ("trace:",), 1, ("ab",)), rev("rv", "N", 3, ("g1",)), W("wo", "O", "g1", ("g1", "rv")),
                         N_("n", "N", ("ab", "wo"))], [("concl", "wo"), ("send", "N", "P", TRC, "n", None)])
show("D1 a grant with no asserted_at beside one with",
     [G("g1", "N", "P", ("trace:",), None), G("g2", "N", "P", ("capacity:",), 1)], [("send", "N", "P", CAP, None, None)])

# ---- new attacks
# K1: the thief holds the SENDING node's key; it signs a row as N naming its grant and not the revocation
K1 = [G("g1", "N", "P", ("capacity:",), 1), rev("rv", "N", 3, ("g1",)),
      G("gt", "N", "A", ("trace:",), 2, ("g1",)), N_("nt", "N", ("gt",))]
show("K1 thief grant + thief row as N naming it; no reader", K1, [("send", "N", "A", TRC, None, None)])
show("K1 the same for reader N (the node whose key was stolen reads its own line)", K1, [("send", "N", "A", TRC, None, None)], reader="N")
# K2: the window: the honest revocation names the key's last rows the owner holds, which include a thief's grant
K2 = [G("g1", "N", "P", ("capacity:",), 1), G("gt", "N", "A", ("trace:",), 2.9, ("g1",)), rev("rv", "N", 3, ("gt",))]
show("K2 thief grant at=2.9 in the revocation's past (owner named its last held rows): stands", K2, [("send", "N", "A", TRC, None, None)])
# F1: former owner withdraws a grant from a past before its ownership ended
F = B("b", "N", "O") + [G("gn", "N", "P", ("trace:",), 1, ("ab",)), ST.withdraw("wb", "O", "ab", ("gn",))]
show("F0 O gave up ownership (wb); N's grant gn", F + [N_("n", "N", ("wb",))], [("send", "N", "P", TRC, "n", None)])
show("F1 former owner O withdraws gn from a past without wb", F + [W("wo", "O", "gn"), N_("n", "N", ("wb", "wo"))],
     [("concl", "wo"), ("send", "N", "P", TRC, "n", None)])
show("F2 the same withdrawal naming wb", F + [W("wo", "O", "gn", ("wb",)), N_("n", "N", ("wb", "wo"))],
     [("concl", "wo"), ("send", "N", "P", TRC, "n", None)])
# F3: a later grant N makes after O left, not naming wb (N need not hold O's withdrawal)
show("F3 N's later grant gn2 (not naming wb) withdrawn by former owner O",
     F + [G("gn2", "N", "Q", ("trace:",), 2, ("gn",)), W("wo", "O", "gn2"), N_("n", "N", ("wb", "wo", "gn2"))],
     [("concl", "wo"), ("send", "N", "Q", TRC, "n", None)])
# P1: the peer withdraws a grant naming another peer; and the owner's grant to it
show("P1 P withdraws N's grant to Q (not its own)",
     [G("gq", "N", "Q", ("trace:",), 1), W("wp", "P", "gq"), N_("n", "N", ("wp",))], [("concl", "wp"), ("send", "N", "Q", TRC, "n", None)])
show("P2 P withdraws owner O's grant to P: ends it for every node O owns",
     B("b", "N", "O") + B("c", "M", "O") + [G("go", "O", "P", ("trace:",), 1), W("wp", "P", "go"), N_("n", "N", ("ab", "ac", "wp"))],
     [("concl", "wp"), ("send", "N", "P", TRC, "n", None), ("send", "M", "P", TRC, "n", None)])
# AN: federation announcements
show("AN1 federation grant, P's 'announcement' signed by N",
     [AN("aN", "N"), CK.row("aP", "announce", "N", (), about="P"), C.grant("g", "N", "P", ("trace:",), 1, ("aN", "aP")), N_("n", "N", ("g",))],
     [("concl", "g"), ("send", "N", "P", TRC, "n", None)])
show("AN2 federation grant to a revoked peer P (its announcement still counts)",
     [AN("aN", "N"), AN("aP", "P"), rev("rvp", "P", 1, ("aP",)), C.grant("g", "N", "P", ("trace:",), 2, ("aN", "aP", "rvp")), N_("n", "N", ("g",))],
     [("concl", "g"), ("send", "N", "P", TRC, "n", None)])
show("AN3 the same grant marked fed=False with no announcements at all",
     [G("g", "N", "P", ("trace:",), 1), N_("n", "N", ("g",))], [("concl", "g"), ("send", "N", "P", TRC, "n", None)])
show("AN4 announcement by a thief of P's key after P's revocation (concurrent)",
     [AN("aN", "N"), rev("rvp", "P", 1), AN("aP", "P"), C.grant("g", "N", "P", ("trace:",), 2, ("aN", "aP")), N_("n", "N", ("g",))],
     [("concl", "g"), ("send", "N", "P", TRC, "n", None)])
# SW: a 'narrowing' that widens
show("SW1 a later grant naming the first, with wider classes: moves the wider set",
     [G("g1", "N", "P", ("capacity:",), 1), G("g2", "N", "P", ("capacity:", "trace:"), 2, ("g1",)), N_("n", "N", ("g2",))],
     [("send", "N", "P", TRC, "n", None)])
# CF: the causal fold with a fork: a withdrawn winner and a regrant that names it revive the other branch
CF = [G("g3", "N", "P", ("capacity:", "trace:"), 4), G("g2", "N", "P", ("capacity:",), 5), W("w", "N", "g2"),
      G("g4", "N", "P", ("capacity:",), 3, ("w",)), N_("n", "N", ("g3", "g4"))]
show("CF1 fork g3 (at 4, wide) | g2 (at 5, narrow); g2 withdrawn; regrant g4 at=3 names w only", CF,
     [("send", "N", "P", TRC, "n", None), ("send", "N", "P", CAP, "n", None)])
show("CF2 before the regrant: nothing (no revival)", CF[:3] + [N_("n", "N", ("g3", "w"))], [("send", "N", "P", TRC, "n", None)])
