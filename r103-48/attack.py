"""r103-48: re-attack on consent.py at consent-set c218a93. python3 -I attack.py <src>/models/causal_kernel
Grants are held between the two nodes (fed=False) unless a case says federation."""
import sys
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import consent as C
ST, CK = C.ST, C.CK
W, N_, B, AN = C.withdraws, C.note, C.binding, C.announce
CAP, TRC = "capacity:cpu:v1", "trace:complete:v1"
def G(*a, fed=False, **kw): return C.grant(*a, fed=fed, **kw)
def rev(id, key, ra, names=()): return CK.row(id, "revoke", key, tuple(names), key=key, ra=ra)
def found_self(i, k): return ST.offer(i, k, (k,), "self", "@", "self")
def add_self(i, roster, k, signers, heads):
    return ST.offer(i, signers[0], k, "self", roster, "group", tuple(heads), head=tuple(heads), policy="self_roster_add",
                    counted="self", cosigners=tuple(signers[1:]) + (k,))
def evict(i, roster, k, signers, heads):
    return ST.unseat(i, signers[0], k, "self", roster, "group", tuple(heads), head=tuple(heads), policy="self_roster_evict",
                     counted="self", cosigners=tuple(signers[1:]))

def show(name, rows, asks, reader=None):
    S = C.state(rows)
    kv = C.key_view(S, reader)
    print(name + ("   [reader %s]" % reader if reader else ""))
    for a in asks:
        if a[0] == "send": got = C.may_send(S, *a[1:], kv=kv)
        elif a[0] == "peers": got = sorted(C.peer_set(S, *a[1:], kv=kv))
        elif a[0] == "wd": got = C.may_withdraw(S, S.by[a[1]], S.by[a[2]])
        elif a[0] == "person": got = C.person_over(C._rows_before(S, a[1], True), a[2])
        print("   ", a, "->", got)

# ---- r97 re-run
K1 = [G("g1", "N", "P", ("capacity:",), 1), rev("rv", "N", 3, ("g1",)), G("gt", "N", "A", ("trace:",), 2, ("g1",)), N_("nt", "N", ("gt",))]
show("K1 thief grant + thief row as N, reader N", K1, [("send", "N", "A", TRC, None, None)], reader="N")
show("K1' the honest revocation names the thief's row (owner named every row it held of its key)",
     K1[:1] + [G("gt", "N", "A", ("trace:",), 2, ("g1",)), N_("nt", "N", ("gt",)), rev("rv", "N", 3, ("nt",))],
     [("send", "N", "A", TRC, None, None)], reader="N")
A3 = B("b", "N", "O") + [G("g0", "O", "Q", ("x:",), 1, ("ab",)), rev("rv", "O", 3, ("g0",)),
                         G("gt", "O", "A", ("trace:",), 1, ("g0",)), N_("n", "N", ("ab", "gt"))]
show("A3 revoked owner's thief grant taken up by N", A3, [("send", "N", "A", TRC, "n", None)], reader="N")
show("A3 + N withdraws gt (a node the grant is for)", A3 + [W("wn", "N", "gt", ("n",)), N_("n3", "N", ("wn",))],
     [("wd", "wn", "gt"), ("send", "N", "A", TRC, "n3", None)], reader="N")
CF = [G("g3", "N", "P", ("capacity:", "trace:"), 4), G("g2", "N", "P", ("capacity:",), 5), W("w", "N", "g2"),
      G("g4", "N", "P", ("capacity:",), 3, ("w",)), N_("n", "N", ("g3", "g4"))]
show("CF1 fork revival", CF, [("send", "N", "P", TRC, "n", None), ("send", "N", "P", CAP, "n", None)])
F = B("b", "N", "O") + [G("gn", "N", "P", ("trace:",), 1, ("ab",)), ST.withdraw("wb", "O", "ab", ("gn",))]
show("F1 former owner withdraws from a past without wb", F + [W("wo", "O", "gn"), N_("n", "N", ("wb", "wo"))],
     [("wd", "wo", "gn"), ("send", "N", "P", TRC, "n", None)])
show("F3 a later grant not naming wb", F + [G("gn2", "N", "Q", ("trace:",), 2, ("gn",)), W("wo", "O", "gn2"), N_("n", "N", ("wb", "wo", "gn2"))],
     [("wd", "wo", "gn2"), ("send", "N", "Q", TRC, "n", None)])
show("AN4 announcement by P's key concurrent with P's revocation",
     [AN("aN", "N"), rev("rvp", "P", 1), AN("aP", "P"), C.grant("g", "N", "P", ("trace:",), 2, ("aN", "aP")), N_("n", "N", ("g",))],
     [("send", "N", "P", TRC, "n", None)])
show("A5 regrant after withdrawal, earlier instant",
     [G("g1", "N", "P", ("capacity:",), 5), W("w", "N", "g1"), G("g2", "N", "P", ("capacity:",), 3, ("w",)), N_("n", "N", ("g2",))],
     [("send", "N", "P", CAP, "n", None)])

# ---- new
# FD: two forks, each regranted with a lower instant than the other fork's head: every row beaten, nothing in force
FD = [G("g1", "N", "P", ("capacity:",), 10), G("h1", "N", "P", ("capacity:",), 10),
      G("g2", "N", "P", ("capacity:",), 1, ("g1",)), G("h2", "N", "P", ("capacity:",), 1, ("h1",)), N_("n", "N", ("g2", "h2"))]
show("FD1 two forks, each regranted at a lower instant: no winner", FD, [("send", "N", "P", CAP, "n", None)])
show("FD2 one fork only (g1, h1 concurrent; g2 names g1)", FD[:3] + [N_("n", "N", ("g2", "h1"))], [("send", "N", "P", CAP, "n", None)])
# PE: the person arm has no end cut: an evicted device withdraws the person's grant from a past before its eviction
PR = [found_self("SO", "O"), add_self("aO2", "SO", "O2", ("O",), ("SO",)), add_self("aO3", "SO", "O3", ("O", "O2"), ("aO2",)),
      G("g", "O", "P", ("trace:",), 1, ("aO3",))]
EV = evict("ev", "SO", "O2", ("O", "O3"), ("aO3",))
show("PE0 the person's grant; O2 evicted", PR + [EV, N_("n", "O", ("ev", "g"))],
     [("person", "ev", "O2"), ("send", "O", "P", TRC, "n", None)])
show("PE1 evicted O2 withdraws O's grant from a past without its eviction", PR + [EV, W("w2", "O2", "g"), N_("n", "O", ("ev", "w2"))],
     [("wd", "w2", "g"), ("send", "O", "P", TRC, "n", None)])
show("PE2 the same naming its eviction", PR + [EV, W("w2", "O2", "g", ("ev",)), N_("n", "O", ("ev", "w2"))],
     [("wd", "w2", "g"), ("send", "O", "P", TRC, "n", None)])
# PR: a revoked device's key (a thief) withdraws, concurrent with the revocation
show("PR1 O2's key revoked; a withdrawal by O2 concurrent with it",
     PR + [rev("rv2", "O2", 5, ("aO3",)), W("w2", "O2", "g"), N_("n", "O", ("rv2", "w2"))],
     [("wd", "w2", "g"), ("send", "O", "P", TRC, "n", None)])
# NF: 'a node the grant is for' - any node the granting person owns may withdraw the owner's grant for ALL its nodes
NF = B("b", "N", "O") + B("c", "M", "O") + [G("go", "O", "P", ("trace:",), 1, ("ab", "ac")), W("wm", "M", "go"),
                                            N_("n", "N", ("wm",))]
show("NF1 node M (owned by O) withdraws O's grant: N's rows stop too", NF, [("wd", "wm", "go"), ("send", "N", "P", TRC, "n", None)])
# NF2: a node whose binding to O ended withdraws concurrently
NF2 = B("b", "N", "O") + B("c", "M", "O") + [G("go", "O", "P", ("trace:",), 1, ("ab", "ac")), ST.withdraw("wc", "M", "c", ("go",)),
                                             W("wm", "M", "go"), N_("n", "N", ("wc", "wm"))]
show("NF2 M unbinds itself (wc) and withdraws concurrently", NF2, [("wd", "wm", "go"), ("send", "N", "P", TRC, "n", None)])
# NB: a node binds itself to a person's key to become 'a node the grant is for': is acceptance needed?
NB = [ST.offer("bx", "X", "O", "owner", "X", "self"), G("go", "O", "P", ("trace:",), 1), W("wx", "X", "go", ("bx",)), N_("n", "O", ("wx",))]
show("NB1 X offers O ownership of X (not accepted), then withdraws O's grant", NB, [("wd", "wx", "go"), ("send", "O", "P", TRC, "n", None)])
