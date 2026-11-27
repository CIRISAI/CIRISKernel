import sys
p = sys.argv[1] + '/models/causal_kernel/window.py'
s = open(p).read()


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a, s.count(a))
    s = s.replace(a, b)


# ---- the moderation world: the moderator is admitted first (a duty seat stands only on a member), so four members
old_mod = s[s.index("def moderation_world():"):s.index("def halt_world():")]
new_mod = '''def admitted(k, by=("m1", "m3"), founders=("m1", "m2", "m3")):
    """A room of three founding duty holders, and key k admitted to its roster by two of them (k cosigning: its own
    yes). A duty seat stands only on a member (seat.py, `member`), so a world that confers one on k admits k first and
    counts the conferral over the admission."""
    g = ST.offer("g", founders[0], founders, "duty", "@", "self", cosigners=founders[1:])     # three duty holders (CC 4.5.4)
    am = ST.offer("am", by[0], k, "member", "g", "group", ("g",), head=("g",), policy="community_invite", cosigners=tuple(by[1:]) + (k,))
    return g, am


def moderation_world():
    g, am = admitted("MOD")                                                    # MOD is a member, then a moderator
    md = ST.offer("md", "m1", "MOD", "moderate", "g", "group", ("am",), head=("am",), policy="duty_confer", counted="duty",
                  cosigners=("m3", "MOD"))                                     # two of the three confer, MOD accepting
    W = secs("moderation_fallback")
    p = opener("p", "m2", "moderation_fallback", "g", ("md",))
    # four members at the head (m1, m2, m3 and MOD): a strict majority of them is three acts
    acts = [answer("x1", "m1", "p", "act"), answer("x2", "m2", "p", "act"), answer("x3", "m3", "p", "act")]
    xs = ("x1", "x2", "x3")
    A = answer("A", "MOD", "p", "answered")
    base = [g, am, md, p, receipt("r", "m2", "p", 0)] + acts
    L = landing("L", "m2", "p", "r", "fallback", W, xs)
    cases = [
        ("false landing: a member lands the members' moderation; the moderator had answered and the landing leaves the answer unnamed",
         base + [A, L], "present moderator is not overridden", "not fallback"),
        ("false landing, stated falsely: the same landing naming the moderator's answer",
         base + [A, landing("L", "m2", "p", "r", "fallback", W, xs + ("A",))], "present moderator is not overridden", "not fallback"),
        ("false landing, no count: one member lands the fallback alone",
         [g, am, md, p, receipt("r", "m2", "p", 0), landing("L", "m2", "p", "r", "fallback", W)], "the fallback needs the members' majority", "not fallback"),
        ("false landing, short of the count: two members of four act and one of them lands the fallback",
         [g, am, md, p, receipt("r", "m2", "p", 0), acts[0], acts[1], landing("L", "m2", "p", "r", "fallback", W, ("x1", "x2"))],
         "the fallback needs the members' majority", "not fallback"),
        ("withheld answer: an honest member lands; a relay had kept the moderator's answer from the room",
         base + [A, L], "present moderator is not overridden", "not fallback"),
        ("a second landing naming both: another member lands 'answered', naming the first landing and the moderator's answer",
         base + [A, L, receipt("r2", "m1", "p", 0), landing("L2", "m1", "p", "r2", "answered", 0, ("L", "A"))],
         "a row naming both decides", "answered"),
        ("absent moderator: nobody answers in 48 h and the members' majority acts",
         base + [L], "the fallback works when the moderator is absent", "fallback"),
        ("answer signed just after, naming the landing: the moderator returns and answers honestly",
         base + [L, answer("A", "MOD", "p", "answered", ("L",))], "(what an honest late answer is worth)", None),
        ("answer signed just after, leaving the landing unnamed: the moderator returns late",
         base + [L, A], "(a late moderator against the members' act)", None),
        ("a moderator's seat conferred on a key that is not a member: its answer is no moderator's answer, and the members' majority lands",
         [g, dict(md, names=("g",), head=("g",)), dict(p), receipt("r", "m2", "p", 0), acts[0], acts[1], A,
          landing("L", "m2", "p", "r", "fallback", W, ("x1", "x2"))],
         "a duty seat stands only on a member", "fallback"),
    ]
    return "moderation fallback (48 h, absent moderator, members' majority)", cases


'''
s = s.replace(old_mod, new_mod)

old_ov = s[s.index("def overturn_world():"):s.index("WORLDS = (")]
new_ov = '''def overturn_world():
    g, am = admitted("MOD")                                                    # MOD is a member, then a moderator
    md = ST.offer("md", "m1", "MOD", "moderate", "g", "group", ("am",), head=("am",), policy="duty_confer", counted="duty",
                  cosigners=("m3", "MOD"))
    W = secs("moderation_overturn")
    p = opener("p", "MOD", "moderation_overturn", "g", ("md",))         # the duty holder's act opens its own window
    # four members at the head (m1, m2, m3 and MOD, the duty holder): a strict majority of the roster is three objections
    o1, o2, o3 = answer("o1", "m1", "p", "object"), answer("o2", "m2", "p", "object"), answer("o3", "m3", "p", "object")
    base = [g, am, md, p]
    r1, r3 = receipt("r", "m1", "p", 0), receipt("r", "m3", "p", 0)
    stands = landing("L", "m3", "p", "r", "stands", W, ("o1",))
    stands2 = landing("L", "m3", "p", "r", "stands", W, ("o1", "o3"))    # m3 objected itself, and lands on the two objections it names
    g1 = ST.offer("g", "m1", ("m1",), "duty", "@", "self")
    p1 = opener("p", "m1", "moderation_overturn", "g", ("g",))          # the lone duty holder (its founding seat moderates) is the one member
    cases = [
        ("false landing, no count: one member objects and lands the lift alone",
         base + [o1, r1, landing("L", "m1", "p", "r", "lifted", 0, ("o1",))], "the lift needs the members' majority", "not lifted"),
        ("false landing, short of the count: two members of four object and one of them lands the lift",
         base + [o1, o2, r1, landing("L", "m1", "p", "r", "lifted", 0, ("o1", "o2"))], "the lift needs the members' majority", "not lifted"),
        ("the room lifts: three of four object and one of them lands at once",
         base + [o1, o2, o3, r1, landing("L", "m1", "p", "r", "lifted", 0, ("o1", "o2", "o3"))], "the room may lift a duty holder's act", "lifted"),
        ("stands at the close: one objection in 48 h and another member lands",
         base + [o1, r3, stands], "short of the count the act stands", "stands"),
        ("false landing: a member lands 'stands' leaving a third objection unnamed",
         base + [o1, o2, o3, r3, stands2], "a majority's objections are not overridden by a landing", "not stands"),
        ("withheld objection: an honest member lands 'stands'; a relay had kept the third objection from it",
         base + [o1, o2, o3, r3, stands2], "a majority's objections are not overridden by a landing", "not stands"),
        ("a second landing naming both: a member lands 'lifted', naming the first landing and the third objection",
         base + [o1, o2, o3, r3, stands2, receipt("r2", "m1", "p", 0), landing("L2", "m1", "p", "r2", "lifted", 0, ("L", "o2"))],
         "a row naming both decides", "lifted"),
        ("the duty holder objects to its own act, with one member: the landing names both",
         base + [o1, answer("oM", "MOD", "p", "object"), r1, landing("L", "m1", "p", "r", "lifted", 0, ("o1", "oM"))],
         "two voices of four do not lift", "not lifted"),
        ("the duty holder objects to its own act, with two members: the landing names the three",
         base + [o1, o2, answer("oM", "MOD", "p", "object"), r1, landing("L", "m1", "p", "r", "lifted", 0, ("o1", "o2", "oM"))],
         "(the duty holder is a member, and the table counts a member's objection: its own included)", None),
        ("a key with no seat at the head objects, with two members",
         base + [o1, o2, answer("oz", "z", "p", "object"), r1, landing("L", "m1", "p", "r", "lifted", 0, ("o1", "o2", "oz"))],
         "only a member seated at the head the act names counts", "not lifted"),
        ("the floor: in a room of one, the one member (its lone duty holder) objects to its own act and lands",
         [g1, p1, dict(o1), r1, landing("L", "m1", "p", "r", "lifted", 0, ("o1",))], "never fewer than two voices", "not lifted"),
        ("objection signed just after, naming the landing: a member objects late and honestly",
         base + [o1, o3, r3, stands2, answer("o2", "m2", "p", "object", ("L",))], "(what an honest late objection is worth)", None),
        ("objection signed just after, leaving the landing unnamed",
         base + [o1, o3, r3, stands2, o2], "(a late objection against a landing that stands)", None),
    ]
    return "moderation overturn (48 h, the members' check on a duty holder's act)", cases


'''
s = s.replace(old_ov, new_ov)
open(p, 'w').write(s)
