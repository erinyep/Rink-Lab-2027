"""Category-aware roster feasibility; no invented points or win probabilities."""
from .availability import excluded_by_status

SKATER_CATEGORIES = {
    13: ('G', 'goals'), 14: ('A', 'assists'), 15: ('+/-', 'plus_minus'),
    17: ('PIM', 'penalty_minutes'), 27: ('ATOI', 'toi_minutes'),
    29: ('SOG', 'shots'), 31: ('HIT', 'hits'), 38: ('PPP', 'pp_points'),
}
GOALIE_CATEGORIES = {1: 'W', 10: 'GAA', 11: 'SV%'}


def goalie_qualification(starts, minimum, slots, roster):
    """Separate cumulative matchup starts from simultaneous active slots.

    Upcoming team games are opportunities, not calibrated start probabilities.
    Bench, injured and already-locked goalies cannot supply an assumed new start.
    Two goalies from one NHL team cannot both start the same game.
    """
    import math
    if starts is None or minimum is None or not all(math.isfinite(float(v)) for v in [starts, minimum]):
        return dict(summary='Matchup goalie-start qualification unavailable.', scenarios=[], active_names=[], bench_names=[])
    active = [r for r in roster if r['is_goalie'] and r['lineup_slot'] == 'Goalie'
              and r['has_game'] and not r['blocked'] and not r['locked']]
    bench = [r['player_name'] for r in roster if r['is_goalie'] and r['lineup_slot'] == 'Bench' and r['has_game']]
    maximum = min(slots, len({r['schedule_team'] for r in active}))
    needed = max(0, minimum-starts)
    summary = (f'Matchup goalie starts: {starts:g} of {minimum:g} minimum recorded. '
               + (f'{needed:g} more qualifying start(s) needed this matchup. ' if needed else 'Minimum already met. ')
               + f'You have {slots} active goalie slots at a time; the minimum accumulates across the matchup.')
    return dict(recorded=starts, minimum=minimum, needed=needed, active_slots=slots,
        active_names=[r['player_name'] for r in active], bench_names=bench, summary=summary,
        scenarios=[dict(additional_starts=n, total=starts+n, minimum_met=starts+n >= minimum) for n in range(maximum+1)])
SLOT_NAMES = {0:'Center',1:'Left Wing',2:'Right Wing',3:'Forward',
              4:'Defense',5:'Goalie',6:'Util',7:'Bench',8:'IR'}


def category_rules(rules):
    scoring = rules['scoringSettings']
    if scoring['scoringType'] != 'H2H_CATEGORY':
        raise ValueError('This report currently supports H2H_CATEGORY only')
    output = []
    for item in scoring['scoringItems']:
        stat = item['statId']
        if stat not in SKATER_CATEGORIES and stat not in GOALIE_CATEGORIES:
            raise ValueError(f'Unsupported scored category {stat}; do not silently omit it')
        name = SKATER_CATEGORIES[stat][0] if stat in SKATER_CATEGORIES else GOALIE_CATEGORIES[stat]
        output.append(dict(stat_id=stat, name=name, lower_is_better=bool(item['isReverseItem']),
                           model_event=SKATER_CATEGORIES[stat][1] if stat in SKATER_CATEGORIES else None))
    return output


def active_slots(rules):
    counts = rules['rosterSettings']['lineupSlotCounts']
    unknown = [k for k,v in counts.items() if v and int(k) not in SLOT_NAMES]
    if unknown:
        raise ValueError(f'Unsupported lineup slots: {unknown}')
    return {SLOT_NAMES[int(k)]:int(v) for k,v in counts.items()
            if v and int(k) not in (7,8)}


def fit_lineup(players, capacities):
    """Bipartite matching, preserving fixed slots for already-locked active players.

    Each input: id, eligible list, optional fixed_slot. Fixed bench players must
    not be supplied. Return assignments, or None if the full set cannot fit.
    """
    slots = [(name,i) for name,n in capacities.items() for i in range(n)]
    occupied, fixed = {}, set()
    ids = [p['id'] for p in players]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate player in lineup')
    eligible = {p['id']:set(p['eligible']) for p in players}
    for p in players:
        if not p.get('fixed_slot'):
            continue
        choices = [s for s in slots if s[0] == p['fixed_slot'] and s not in occupied]
        if not choices or p['fixed_slot'] not in eligible[p['id']]:
            return None
        occupied[choices[0]] = p['id']
        fixed.add(p['id'])

    def place(pid, visited):
        for slot in slots:
            if slot in visited or slot[0] not in eligible[pid]:
                continue
            visited.add(slot)
            previous = occupied.get(slot)
            if previous is None or (previous not in fixed and place(previous, visited)):
                occupied[slot] = pid
                return True
        return False

    for p in players:
        if p['id'] not in fixed and not place(p['id'],set()):
            return None
    return {pid:slot[0] for slot,pid in occupied.items()}


def dominates(candidate, incumbent, categories):
    """True only if candidate is no worse in every scored skater mean, better in one."""
    deltas = []
    for category in categories:
        if category['model_event'] is None:
            continue
        key = 'expected_'+category['model_event']+'_if_plays'
        if candidate.get(key) is None or incumbent.get(key) is None:
            return False
        delta = candidate[key]-incumbent[key]
        deltas.append(-delta if category['lower_is_better'] else delta)
    return bool(deltas) and all(d >= 0 for d in deltas) and any(d > 0 for d in deltas)


def acquisition_window_open(game_starts, as_of):
    """ESPN current-day adds lock at the first scheduled game, not player puck drop."""
    if not game_starts:
        raise ValueError('Cannot establish acquisition deadline without scheduled games')
    return as_of < min(game_starts)


def category_comparison(category, own, opponent, lower_is_better=False):
    """Missing/nonfinite ESPN rates are unavailable, never an invented lead."""
    import math
    own = float(own) if math.isfinite(float(own)) else None
    opponent = float(opponent) if math.isfinite(float(opponent)) else None
    if category == 'ATOI':
        own = own / 60 if own is not None else None
        opponent = opponent / 60 if opponent is not None else None
    delta = None if own is None or opponent is None else (opponent-own if lower_is_better else own-opponent)
    status = 'unavailable' if delta is None else 'tied' if abs(delta)<1e-9 else 'ahead' if delta>0 else 'behind'
    return dict(category=category,own=own,opponent=opponent,advantage=delta,lower_is_better=lower_is_better,status=status)
