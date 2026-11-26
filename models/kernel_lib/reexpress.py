"""
The models' decisions written again with library calls only. Each function body uses sel, group, in_range,
rule, fix, set membership on their results, and arithmetic on instants and counts. Nothing else decides.
"""
import kernel_lib as K

t_of = lambda r: None if r is None else r["t"]


# ---- takedown (formal/takedown/takedown_model.py: fold) -------------------------------------------------
def takedown(H, now, basis, W, hold_wins):
    """H: rows {k, basis, t} held by now. basis: {leaf: 'immediate' | 'windowed'}."""
    hold_from = K.group(K.sel(H, k="hold"), None, "min")
    hold_to = K.group(K.sel(H, k="hold_lifted"), None, "min")
    destroyed, live_notice = False, False
    for n in K.sel(H, k="notice"):
        if K.rule(basis, n["basis"]) == "immediate":
            at, undone = n["t"], False
        else:
            close = n["t"] + W
            undone = bool(K.sel(H, before=close, k={"reversal", "lift"}))
            at = close if not undone and K.in_range(now, close) else None
        if hold_wins and K.in_range(at, hold_from, hold_to): at = hold_to
        destroyed |= at is not None
        live_notice |= not undone
    return "destroyed" if destroyed else "withheld" if live_notice else "served"


# ---- deletion (formal/deletion/deletion_model.py: fold) -------------------------------------------------
def deletion(H, now, table, W):
    """H: rows {k, t} held by now. table: {'starts': kinds, 'excuses': kinds}."""
    start = K.group(K.sel(H, k=K.rule(table, "starts")), None, "min")
    if start is None: return "none"
    if K.sel(H, before=start + W, k=K.rule(table, "excuses")): return "met"
    return "breach" if K.in_range(now, start + W) else "running"


# ---- owner_binding (formal/owner_binding/owner_binding_model.py: run, the fold reading) ----------------
def owner_of(H):
    """H: rows {k: bind|withdraw|occurrence, x, cos, t}."""
    live = [b for b in K.sel(H, k="bind", cos=True) if not K.sel(H, k="withdraw", x=b["x"])]
    return K.group(live, None, "one", "x")


# ---- guardianship (formal/guardianship/guardianship_model.py: fold) -------------------------------------
BAND = {  # which attestations count beside the named guardian's, and what silences one
    "under_13": {"voices": {"order_displaced"}, "unless": {}},
    None:       {"voices": {"order_displaced"}, "unless": {}},
    "13_15":    {"voices": {"order_minor", "order_displaced"}, "unless": {}},
    "16_17":    {"voices": {"order_minor", "order_displaced"}, "unless": {"order_displaced": "refusal"}},
}


def guardianship(H, band):
    """H: rows {k, t}."""
    r = K.rule(BAND, band)
    voices = [v for v in K.sel(H, k=r["voices"]) if not K.sel(H, k=K.rule(r["unless"], v["k"], "-"))]
    order = bool(K.sel(H, k="order_named")) and K.in_range(K.group(voices, None, "count", "k"), 1)
    stepped, bound = bool(K.sel(H, k="step_down")), bool(K.sel(H, k="bind_named"))
    guardian = "named" if (order or stepped) and bound else "none" if stepped else "current"
    contested = bool(K.sel(H, k={"order_minor", "order_displaced", "order_named"})) and not order and not stepped
    acts = set() if contested else {a["k"] for a in K.sel(H, k={"current": "act_displaced", "named": "act_named"}.get(guardian, "-"))}
    return {"guardian": guardian, "contested": contested, "mode": "stopped" if guardian == "none" else "floor" if contested else "normal",
            "report": contested, "acts": frozenset(acts)}


# ---- ranked_choice (formal/ranked_choice/ranked_choice_model.py: winner = finish . summary . dedupe) ----
MUT = set()   # named mutations, switched on by a check (models/causal_kernel/check_ranked.py)


def ranked(rows, options, floor=2, declared=True):
    """rows: (person, ranking). Returns (winner or None, rounds). declared=False: the election's count, with no
    declared order, where a tie for weakest is refused by the reducer and seats nobody (CC 4.5.13). In each round the
    options holding no first choice are eliminated together, before the weakest is sought (CIRISConstitution#241 E1:
    every ranked count)."""
    winner, rounds, _out = _count(rows, options, floor, declared)
    return winner, rounds


def runoff(rows, options, floor=2, declared=True):
    """The runoff order (CC 4.5.13: a decline "passes the duty to the next in runoff order"): the one count repeated.
    The first is the count's winner; the next is the winner of the same count over the same ballots with those ahead
    of it struck; and so on. A step that yields nobody (a tie) ends the order there (CIRISConstitution#241)."""
    order, opts = [], list(options)
    if "runoff_from_eliminations" in MUT:                  # MUTATION: the order read off one count's eliminations
        w, _, out = _count(rows, opts, floor, declared)
        return () if w is None else (w,) + tuple(o for o in reversed(out) if o != w)
    while opts:
        w = ranked(rows, opts, floor, declared)[0]
        if w is None:
            if "runoff_tie_continues" not in MUT: break
            opts = opts[1:]; continue                      # MUTATION: a step's tie strikes one option and goes on
        order.append(w)
        opts = [o for o in opts if o != w]
    return tuple(order)


def _count(rows, options, floor, declared):
    """The one count: (winner, rounds, the options eliminated in turn)."""
    ballots = K.group([{"person": p, "ranking": r, "t": 0} for p, r in rows], "person", "one", "ranking")
    if not K.in_range(len(ballots), min(floor, max(len(options), 1))): return None, 0, ()
    marks = [{"person": p, "option": o, "rank": i, "t": 0} for p, r in ballots.items() for i, o in enumerate(r)]

    def round_(state):
        standing, winner, done, rounds, out = state
        if done: return state
        tops = K.group(K.sel(marks, option=set(standing)), "person", "least", "rank")
        first = K.group(list(tops.values()), "option", "count", "person")
        if not tops: return standing, None, True, rounds, out
        table = [{"o": o, "n": first.get(o, 0), "back": -options.index(o) if declared else 0} for o in standing]
        top_n = K.group(table, None, "max", "n")
        if K.in_range(2 * top_n, len(tops) + 1) or len(standing) == 1:
            return standing, K.group(K.sel(table, n=top_n), None, "one", "o"), True, rounds, out
        # the options holding no ballot are eliminated together (no ballot passes when one goes, so their order
        # cannot change the count); a tie for weakest is then among options that hold ballots
        none = tuple(o for o in standing if first.get(o, 0) == 0)
        if none and "zero_strike_off" not in MUT:
            return tuple(o for o in standing if o not in none), None, False, rounds + 1, out + none
        try:
            weakest = K.group(table, None, "least", ("n", "back"))
        except K.Tie:
            return standing, None, True, rounds, out                  # no declared order: a tie seats nobody
        return tuple(o for o in standing if o != weakest["o"]), None, False, rounds + 1, out + (weakest["o"],)

    _, winner, _, rounds, out = K.fix(round_, (tuple(options), None, False, 0, ()), len(options) + 1)
    return winner, rounds, out


# ---- set_item (formal/set_item/set_item_model.py: item_counts, the reading `both`) ----------------------
def set_item(H, leaf, A, W):
    """H: rows {k: header|leaf, item, digest, n, t}. A fork is a second header of the item with another digest;
    a leaf names the digest its proof was made against."""
    header = K.group(K.sel(H, k="header"), "item", "one", "digest")
    for l in K.sel(H, k="leaf", n=leaf):
        parts = [l] + K.sel(H, k="header", item=l["item"], digest=l["digest"])
        if K.rule(header, l["item"]) == l["digest"] and K.in_range(K.group(parts, None, "max"), ALWAYS, A + W + 1): return True
    return False


ALWAYS = K.ALWAYS
