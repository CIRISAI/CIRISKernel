R = "/home/emoore/CIRISKernel/.claude/worktrees/agent-ad781c03a48920203/models/causal_kernel/"
def edit(p, reps):
    s = open(p).read()
    for a, b in reps:
        assert s.count(a) == 1, (s.count(a), a)
        s = s.replace(a, b)
    open(p, "w").write(s)

edit(R + "window.py", [
('''    others            the same, less the opener's signer: out of the voices and out of the size counted over
    all_opener_mute   the same as `all` in size; the opener's signer is no voice among it (the members' check:
                      "a strict majority of the roster at the head the act names", the act's author no voice)
''', '''    others            the same, less the opener's signer: out of the voices and out of the size counted over (the
                      members' check: "a strict majority of the members seated at the head the act names, the
                      act's author apart")
'''),
('''    # CC 4.5.13, the members' check: a duty holder's act takes effect at once and is itself the opener; a strict
    # majority of the roster at the head the act names, never fewer than two voices, lifts it by objecting; short of
    # that at the close it stands. The duty holder has no say in the lift of its own act: where it is itself on the
    # roster it is counted over and its objection is no voice (all_opener_mute)
''', '''    # CC 4.5.13, the members' check: a duty holder's act takes effect at once and is itself the opener. "The act is
    # lifted when a strict majority of the members seated at the head the act names, the act's author apart, has
    # objected within the 48-hour window. ... The floor is two voices. The author's own objection is no voice, and the
    # author is not among the members the majority is taken of. Where the author is one of two members no lift is
    # possible." Short of that at the close it stands. So the base is `others`
'''),
('''"at_once": (("object", ("more", 1, 2, 2), "all_opener_mute", "lifted"),),''', '''"at_once": (("object", ("more", 1, 2, 2), "others", "lifted"),),'''),
('''BASES = ("all", "others", "all_opener_mute", "opener")''', '''BASES = ("all", "others", "opener")'''),
('''        keys = base(over)
        voice = keys - {p["signer"]} if over == "all_opener_mute" else keys     # counted over all; the opener's signer no voice
''', '''        keys = voice = base(over)
        # MUTATION overturn_whole_roster: the opener's signer is no voice and is still counted over
        if over == "others" and "overturn_whole_roster" in MUT: keys = base("all")
'''),
('''            scope = spec["counted"] if name in ("all", "others", "all_opener_mute") else name''', '''            scope = spec["counted"] if name in ("all", "others") else name'''),
('''    # the moderator is itself on the roster (a duty holder is a member and holds every duty): it is counted over, and
    # its own objection is no voice. Ruled by the Constitution session on 2026-11-25
''', '''    # the moderator is itself on the roster (a duty holder is a member and holds every duty): its own objection is no
    # voice and it is not among the members the majority is taken of
'''),
('''        ("room of three, the moderator a member: both others object",
         [g, pm, o2, o3, r2, lift("o2", "o3")], "the room may lift a duty holder's act", "lifted"),
        ("room of three, the moderator a member: one other and the moderator object",
         [g, pm, o1, o2, r2, lift("o1", "o2")], "the author's objection is no voice", "not lifted"),
        ("room of four, the moderator a member: two of the three others object",
         [g4, pm, o2, o3, r2, lift("o2", "o3")], "the author is counted over: a strict majority of the roster", "not lifted"),
        ("room of four, the moderator a member: the moderator and two others object",
         [g4, pm, o1, o2, o3, r2, lift("o1", "o2", "o3")], "the author's objection is no voice", "not lifted"),
        ("room of four, the moderator a member: all three others object",
         [g4, pm, o2, o3, o4, r2, lift("o2", "o3", "o4")], "the room may lift a duty holder's act", "lifted"),
''', '''        ("room of three, the moderator a member: both others object, two of two",
         [g, pm, o2, o3, r2, lift("o2", "o3")], "the room may lift a duty holder's act", "lifted"),
        ("room of three, the moderator a member: one other objects alone",
         [g, pm, o2, r2, lift("o2")], "never fewer than two voices", "not lifted"),
        ("room of three, the moderator a member: one other and the moderator object",
         [g, pm, o1, o2, r2, lift("o1", "o2")], "the author's objection is no voice", "not lifted"),
        ("room of four, the moderator a member: two of the three others object",
         [g4, pm, o2, o3, r2, lift("o2", "o3")], "the author is not among the members the majority is taken of", "lifted"),
        ("room of four, the moderator a member: one of the three others objects",
         [g4, pm, o2, r2, lift("o2")], "the lift needs the members' majority", "not lifted"),
        ("room of four, the moderator a member: one other and the moderator object",
         [g4, pm, o1, o2, r2, lift("o1", "o2")], "the author's objection is no voice", "not lifted"),
'''),
('''         [g2, pm, o1, o2, r2, lift("o1", "o2")], "in a room of two no lift is possible", "not lifted"),''',
 '''         [g2, pm, o1, o2, r2, lift("o1", "o2")], "where the author is one of two members no lift is possible", "not lifted"),'''),
('''         [g2, pm, o2], "in a room of two no lift is possible", "open"),''',
 '''         [g2, pm, o2], "where the author is one of two members no lift is possible", "open"),'''),
])
edit(R + "seat.py", [
('''                  removal's author is no voice, and neither is the key it seats. It concludes when those voices
                  are a strict majority of the members at that head, never fewer than two: the overturn's count.
''', '''                  removal's author is no voice, and neither is the key it seats. It concludes when those voices
                  are a strict majority of the members at that head, the removal's author apart, never fewer than
                  two: the overturn's count.
'''),
('''    """The overturn's count (window.py, moderation_overturn) over the objections a re-seating row names: a strict
    majority of the members at the head, the removal's author and the key seated no voice, never fewer than two."""
''', '''    """The overturn's count (window.py, moderation_overturn) over the objections a re-seating row names: a strict
    majority of the members at the head, the removal's author apart (no voice, and not counted over); the key seated
    is counted over and is no voice; never fewer than two."""
'''),
('''    if "lift_over_others" in MUT: mem = mem - {by[r["content"]]["signer"]}     # MUTATION: the author out of the size too
    # the floor of two is the window's; here it follows from the rest (the key seated is on the roster and no voice)
    return 2 * len(yes) > len(mem) and len(yes) >= 2
''', '''    if "lift_over_all" not in MUT: mem = mem - {by[r["content"]]["signer"]}    # MUTATION lift_over_all: the author counted over
    # the floor of two is the window's; here it follows from the rest (the key seated is counted over and no voice)
    return 2 * len(yes) > len(mem) and len(yes) >= 2
'''),
('''                    v = lift_voices(r, P, past, {q["id"]: q for q in P}) or frozenset()
                    yes = (v & mem) - frozenset(r["to"])
                    if not (2 * len(yes) > len(mem) and len(yes) >= 2): return False
''', '''                    v = lift_voices(r, P, past, {q["id"]: q for q in P}) or frozenset()
                    yes = (v & mem) - frozenset(r["to"])
                    mem = mem - {S.by[r["content"]]["signer"]} if v else mem      # the removal's author apart
                    if not (2 * len(yes) > len(mem) and len(yes) >= 2): return False
'''),
])
edit(R + "check_agent_removal.py", [
('''    the lift       a strict majority of the roster at the head the removal names, never fewer than two voices, by
                   objecting; the removal's author is counted over and is no voice (ruled by the Constitution
                   session on 2026-11-25). The window then reads `lifted`, and the key is still out
''', '''    the lift       "a strict majority of the members seated at the head the act names, the act's author apart",
                   by objecting, never fewer than two voices; the author's own objection is no voice and the
                   author is not counted over. The window then reads `lifted`, and the key is still out
'''),
('''    lift_over_others   the re-seating is counted over the roster less the author (the reading ruled out)
''', '''    lift_over_all      the re-seating is counted over the whole roster, the author with it (the reading ruled out)
'''),
('''    overturn_others    the lift is counted over the roster less the author (the base `others`)
''', '''    overturn_whole_roster  the author is no voice and is still counted over (the reading ruled out)
'''),
('''    ("B: two members and the author object, three of five: the author is no voice, of the window or of the re-seating",
''', '''    ("B: two members and the author object: two voices of the four others, and the author is no voice",
'''),
('''    ("B: the three other members object, three of five: lifted, and the re-seating concludes",
''', '''    ("B: three of the four others object: lifted, and the re-seating concludes",
'''),
('''    ("C: a roster of four with the moderator on it: the two other members object, two of four, and nothing lifts",
     C + [remove("x", "m1", "AG", "ag"), O2, O3, reseat("rs", "m2", "AG", "x", "ag", ("o2", "o3"))], {"x": T, "rs": F},
     {"m1", "m2", "m3"}, {"x": "open"}),
''', '''    ("C: a roster of four with the moderator on it: two of the three others object, and it lifts",
     C + [remove("x", "m1", "AG", "ag"), O2, O3, reseat("rs", "m2", "AG", "x", "ag", ("o2", "o3"))], {"x": T, "rs": T},
     {"m1", "m2", "m3", "AG"}, {"x": "lifted"}),
    ("C: one of the three others objects: nothing lifts",
     C + [remove("x", "m1", "AG", "ag"), O2, reseat("rs", "m2", "AG", "x", "ag", ("o2",))], {"x": T, "rs": F},
     {"m1", "m2", "m3"}, {"x": "open"}),
'''),
('''"seated_voice", "lift_over_others", "restores_unseated")''', '''"seated_voice", "lift_over_all", "restores_unseated")'''),
('''    ("overturn_others", clause("moderation_overturn", "at_once", over="others")),
''', '''    ("overturn_whole_roster", lambda W: WN.MUT.add("overturn_whole_roster")),
'''),
('''    overturn_all       the author's objection is a voice of the lift (the base `all`, the clause until now)
''', '''    overturn_all       the author's objection is a voice of the lift, and the author counted over (the base `all`,
                       the clause until now)
'''),
])
