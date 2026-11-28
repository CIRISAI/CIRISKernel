"""r105-49: the opening's voices through the key view. A, B and D open (3 of 5). D revokes its key with the opening
in the revocation's past (a signature before the end: counts), or with only g there (the cosign is not before the
end: no voice, the opening is 2 of 5).
Run: python3 -I attack_open_kv.py <tree root>"""
import sys
sys.path.insert(0, sys.argv[1] + "/models/causal_kernel")
import check_election_close as CC  # noqa: E402
KE, B, SEAT, OPEN = CC.KE, CC.B, CC.SEAT, CC.OPEN
rows = [CC.G5, CC.LM, OPEN("op", "lm", ("A", "B", "D"))] + CC.H5 + [SEAT("ec", "C", CC.IDS)]
for label, names, want in (("D's revocation holds the opening and its ballot", ("g", "op", "bd"), (True, False)),
                           ("D's revocation names its ballot (which names the opening)", ("g", "bd"), (True, False)),
                           ("D's revocation holds only g", ("g",), (False, False))):
    got = CC.answer(rows, "ec", ("C", "moderate"), None, CC.RECS + [KE.revoke("vD", "D", 0, names=names)])
    print("%-52s C moderate, closed: %s%s" % (label, got, "" if got == want else "  (WANT %s)" % (want,)))
