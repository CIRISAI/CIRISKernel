import sys
root = sys.argv[1]


def edit(path, pairs):
    p = root + '/' + path
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (path, a, s.count(a))
        s = s.replace(a, b)
    open(p, 'w').write(s)


edit('check.sh', [('''step "check_delegation (a chain)"         deleg     python3 -I models/causal_kernel/check_delegation.py
''', '''step "check_delegation (a chain)"         deleg     python3 -I models/causal_kernel/check_delegation.py
step "check_duty_seats (on a member)"     dutyseat  python3 -I models/causal_kernel/check_duty_seats.py
''')])
edit('README.md', [('The run ends `all 24 steps passed`.', 'The run ends `all 25 steps passed`.')])
edit('models/README.md', [('''| `python3 -I models/causal_kernel/check_delegation.py` |''', '''| `python3 -I models/causal_kernel/check_duty_seats.py` | a duty seat stands only on a member (CC 4.5.4), read by the seat walk: a conferral on a non-member seats nobody and is no voice in a duty count, and stands when the widening lands; a resignation or a counted removal ends the duty seats in its past; nothing revives; a conferral between the end and a re-admission waits; the founding with a member seat beside the duty seat; two tips; what the rule does not reach. 37 hand-written cases in every arrival order (a sample above six rows), five planted breaks caught |
| `python3 -I models/causal_kernel/check_delegation.py` |''')])
edit('models/causal_kernel/README.md', [('recount breaks none of forty-seven checks over five windows', 'recount breaks none of fifty checks over five windows')])
edit('kernel/KERNEL.md', [
    ('forty-seven checks of what each exis', 'fifty checks of what each exis'),
    ('''withdrawn by a strict majority of the others, never on fewer than two voices where there are two holders.
**run**: five properties''', '''withdrawn by a strict majority of the others, never on fewer than two voices where there are two holders.
A duty seat stands only on a member: it stands only where its holder holds the roster's seat over the same
community at the same reading, so a conferral on a key that is not a member seats nobody and is no voice in a
duty count, and it stands with no further row when the key's widening lands. An end of the holder's stay as a
member, its own resignation or a counted removal, ends the duty seats whose offers are in that end's past, and
a later admission revives none of them; a conferral that is not in the end's past waits for the next
admission. At tips the duty seat follows the folded roster. The founding seat holds `member`, so a founding
holder's membership is its founding duty seat unless a member seat is presented beside it. A seat the duty
holders place that makes its holder no duty holder (a node's detector seat) is not asked for membership.
**run** (`models/causal_kernel/check_duty_seats.py`): 37 cases in every arrival order, five planted breaks
caught. **open**: two founders have no presentation in which either lays down its duty and stays a member;
the members' check (`moderation_overturn`) counts the objection of the duty holder whose act it is, now that
the duty holder is a member, and the sentence that it has no say in the lift is not a rule of the table.
**run**: five properties'''),
])
edit('crates/ciris-kernel/CHANGELOG.md', [('''# Changelog — ciris-kernel

''', '''# Changelog — ciris-kernel

## Unreleased

**A duty seat stands only on a member** (CC 4.5.4, "a non-member holds no duty"). Answers change; no signature
does, and one function is added (`seat::stay_ended_in_past`).

Reached: a community whose founding row is of scope `duty`, and there a seat that makes its holder a duty
holder (`duty`, a duty the law names, a duty the founding row declares). Not reached: any other community; a
seat the duty holders place that is no duty (a node's detector seat); a count over a scope that is no duty.

- `seat::Seats::recs`, `stands`, `holders`, `holders_at`, `stands_at`, `one`, and through them
  `seat::members_at`, `members_in`, `count_members` and `seat_rule`: a duty seat conferred on a key that holds
  no roster seat over the community (a `member` seat, or the founding seat where it holds `member`) is not
  live. Before, `duty_confer` on a non-member seated it. When the key's widening lands the seat is live with no
  further row. Such a key is no duty holder, so it is not counted in, and is no voice of, a duty count.
- A holder's own withdrawal of a seat that holds `member` over the community (its member seat, its acceptance of
  one, or the founding row) ends the duty seats whose offers are in that withdrawal's past. Before, a member
  had to withdraw each offer. A counted removal from the roster ended them already and still does.
- Nothing revives: a later admission of the key does not make live a duty offer so ended. A conferral that is
  not in the end's past (made after it, or concurrent with it) is not ended by it: it waits for the next
  admission like any conferral on a non-member.
- At several tips a duty seat is live only where the folded roster (`tips_fold("member", ..)`) seats its
  holder.
- `seat::count_members` (and so `seat_rule`): a count over duty holders also leaves out a holder whose own end
  of its stay as a member is in the counted row's past with no admission of it after (`stay_ended_in_past`,
  new and public). A caller of `group_count` that subtracts `left_in_past` itself subtracts this too for a
  count over duty holders.
- A founding holder whose duty the others withdraw is no member afterwards (its membership was its founding
  seat, as before), so conferring its duty again now takes its admission first.

Presenting a founding so that a holder can lay down its duty and stay a member is in ADOPTING.md. Two founders
have no such presentation; that is open.

The reference: `models/causal_kernel/seat.py`, with `check_duty_seats.py` (37 hand-written cases, every arrival
order, five planted breaks). The cases are in the `seat` fixture with the standing each asks for, the cases of
persist's table (`HOLDS.duty = ("member",)`) under that table. Nine plants in `tools/kernel_crate_plants.sh`.
The worlds of `attacks.py`, `window.py` and `check_rosters.py` that conferred a duty on a key that was no
member now admit that key first; the two moderation windows therefore run over four members, and the adversary
table is 61 rows and 50 checks (recount breaks none).

''')])
edit('crates/ciris-kernel/ADOPTING.md', [('''**A private room.** The signer of every row is the voice''', '''**A community's founding and its duty seats**, for `seat::Seats` (unreleased; see the CHANGELOG).
- The founding row: an Offer, `Conf::Own`, scope `duty`, whose object is its own id, `to` the union of the duty
  holders, each a cosigner. With `SeatLaw::holds["duty"]` containing `member`, each founding holder is a member
  by that seat: its membership is its founding duty seat, and its withdrawal of the founding row, or the
  others' withdrawal of its duty, ends both.
- A named duty is a chained counted row: an Offer, `Conf::Group`, policy `duty_confer`, counted `duty`, over
  the head it extends. With `holds["duty"] = ["member"]` only, a founding holder holds no named duty until such
  a row. It lays that duty down by withdrawing that offer, and stays a member and a duty holder.
- A duty seat is live only on a member. Present the widening that admits a key before, or with, the conferral
  on it: a conferral on a key that is not yet a member seats nobody, with no error, and is live once the
  widening is held.
- A member's resignation (a Withdraw by the member of its member offer or of its own acceptance of it) and a
  counted removal (an Unseat of scope `member`) end its duty seats whose offers are in that row's past. Present
  them as that one row; do not also unseat each duty. After a re-admission present fresh conferrals: the old
  offers stay ended.
- For a founding holder to lay down its founding duty seat and stay a member it needs a member seat beside it.
  With three founders or more: one chained counted Offer of scope `member` per founding holder, signed by the
  other holders (a key the row seats is no voice of its count, so one row seating all founders on their own
  voices concludes nothing). With one founder: its own Offer of `member` to itself over the founding row,
  `Conf::Own`. With two founders neither runs (one voice of two meets no count, and an own offer over a
  founding row that seats several stands only while its signer's founding seat does): this is open.
- A holder's withdrawal of the founding row ends the duty seats conferred on it in that withdrawal's past too.
- Cases: `models/causal_kernel/check_duty_seats.py`, all in the `seat` fixture.

**A private room.** The signer of every row is the voice''')])
