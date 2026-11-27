R = "/home/emoore/CIRISKernel/.claude/worktrees/agent-ad781c03a48920203/"
def edit(p, reps):
    s = open(R + p).read()
    for a, b in reps:
        assert s.count(a) == 1, (p, s.count(a), a)
        s = s.replace(a, b)
    open(R + p, "w").write(s)

M = "models/causal_kernel/"
edit(M + "check_agent_removal.py", [
('''                   author is not counted over. The window then reads `lifted`, and the key is still out
''', '''                   author is not counted over. The key removed is apart too: an agent "acts under its own key
                   and has no vote", so it is no voice and is not counted over, on every path (the count with no
                   landing, a landing, the recount, the re-seating). The window then reads `lifted`, and the key
                   is still out
'''),
('''                   The key it seats is no voice of it, and it seats the key only with the key's own signature
''', '''                   It seats the key only with the key's own signature
'''),
('''    restores_unseated  the re-seating seats a key that was not on the roster at the head the removal names
The re-seating's floor of two voices has no plant: the key seated is on the roster and no voice, so a strict
majority of that roster is already two.
''', '''    restores_unseated  the re-seating seats a key that was not on the roster at the head the removal names
    removed_counted_over  the removed key is counted over, in the window and in the re-seating
    lift_no_floor      the re-seating has no floor of two voices
'''),
('''a second removal at tips (one tips case is here: an admission beside the re-seating); the removed key's own objection in a landing's past (a landing counts it, the count with no
landing does not: the ended-seat rule of window.outcome); a moderator whose duty ended after the head the removal
names.
''', '''a second removal at tips (one tips case is here: an admission beside the re-seating); a moderator whose duty ended
after the head the removal names; agents' keys in any other count of the room (the kernel cannot see which keys are
agents' beyond the one a removal marks).
'''),
('''    ("A: one objection of three members: the window is open, the key out",
''', '''    ("A: one of the two persons objects, one of two: the window is open, the key out",
'''),
('''    ("A: two objections of three members: the window reads lifted, and the key is still out",
''', '''    ("A: both persons object, two of two: the window reads lifted, and the key is still out",
'''),
('''    ("A: the removed key's own objection is no voice: of the window with no landing, nor of the re-seating",
     A + [XA, O1, OA, reseat("rs", "m1", "AG", "x", "md", ("o1", "oA"))], {"rs": F}, {"m1", "m2"}, {"x": "open"}),
''', '''    ("A: the removed key's own objection is no voice: of the window with no landing, nor of the re-seating",
     A + [XA, O1, OA, reseat("rs", "m1", "AG", "x", "md", ("o1", "oA"))], {"rs": F}, {"m1", "m2"}, {"x": "open"}),
    ("A: nor of a landing: a member lands 'lifted' naming its own objection and the removed key's",
     A + [XA, O1, OA, WN.receipt("r", "m1", "x", 0), WN.landing("L", "m1", "x", "r", "lifted", 0, ("o1", "oA"))],
     {"x": T, "L": F}, {"m1", "m2"}, {"x": "open"}),
    ("A: nor of the recount: 'stands' lands at the close over one objection; the removed key objects, unnamed",
     A + [XA, O1, WN.receipt("r", "m2", "x", 0), WN.landing("L", "m2", "x", "r", "stands", WN.secs(OV), ("o1",)), OA],
     {"x": T, "L": T}, {"m1", "m2"}, {"x": "stands"}),
    ("A: the removed key objects beside both persons: lifted on the two, as without it",
     A + [XA, O1, O2, OA, reseat("rs", "m1", "AG", "x", "md", ("o1", "o2", "oA"))], {"rs": T}, {"m1", "m2", "AG"}, {"x": "lifted"}),
'''),
('''    ("B: two members and the author object: two voices of the four others, and the author is no voice",
     B + [XB, O1, O2, O3, reseat("rs", "m2", "AG", "x", "ag", ("o1", "o2", "o3"))], {"x": T, "rs": F}, {"m1", "m2", "m3", "m4"},
     {"x": "open"}),
    ("B: three of the four others object: lifted, and the re-seating concludes",
     B + [XB, O2, O3, O4, reseat("rs", "m2", "AG", "x", "ag", ("o2", "o3", "o4"))], {"x": T, "rs": T},
     {"m1", "m2", "m3", "m4", "AG"}, {"x": "lifted"}),
    ("C: a roster of four with the moderator on it: two of the three others object, and it lifts",
     C + [remove("x", "m1", "AG", "ag"), O2, O3, reseat("rs", "m2", "AG", "x", "ag", ("o2", "o3"))], {"x": T, "rs": T},
     {"m1", "m2", "m3", "AG"}, {"x": "lifted"}),
    ("C: one of the three others objects: nothing lifts",
''', '''    ("B: one person and the author object: one voice of the three persons, and the author is no voice",
     B + [XB, O1, O2, reseat("rs", "m2", "AG", "x", "ag", ("o1", "o2"))], {"x": T, "rs": F}, {"m1", "m2", "m3", "m4"},
     {"x": "open"}),
    ("B: two of the three other persons object, the removed key apart: lifted, and the re-seating concludes",
     B + [XB, O2, O3, reseat("rs", "m2", "AG", "x", "ag", ("o2", "o3"))], {"x": T, "rs": T},
     {"m1", "m2", "m3", "m4", "AG"}, {"x": "lifted"}),
    ("C: the moderator, the agent and two persons: both persons object, two of two, and it lifts",
     C + [remove("x", "m1", "AG", "ag"), O2, O3, reseat("rs", "m2", "AG", "x", "ag", ("o2", "o3"))], {"x": T, "rs": T},
     {"m1", "m2", "m3", "AG"}, {"x": "lifted"}),
    ("C: one person and the removed key object: one voice of two, and nothing lifts",
     C + [remove("x", "m1", "AG", "ag"), O2, OA, reseat("rs", "m2", "AG", "x", "ag", ("o2", "oA"))], {"x": T, "rs": F},
     {"m1", "m2", "m3"}, {"x": "open"}),
    ("D: the moderator, the agent and one person: the person objects, and the floor of two holds",
     D + [remove("x", "m1", "AG", "ag"), O2, reseat("rs", "m2", "AG", "x", "ag", ("o2",))], {"x": T, "rs": F},
     {"m1", "m2"}, {"x": "open"}),
    ("C: one of the two persons objects: nothing lifts (one of two is no strict majority, and the floor is two)",
'''),
('''T, F = True, False
''', '''# ---- world D: two duty holders and AG -----------------------------------------------------------------------------
GD = ST.offer("g", "m1", ("m1", "m2"), "duty", "@", "self", cosigners=("m2",))
D = [GD, admit("ag", "AG", ("m1", "m2"), "g")]

T, F = True, False
'''),
('''"seated_voice", "lift_over_all", "restores_unseated")''', '''"seated_voice", "lift_over_all", "restores_unseated", "removed_counted_over",
               "lift_no_floor")'''),
])
