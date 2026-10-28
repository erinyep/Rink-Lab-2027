"""Past-only lineup ranking challengers; these are not calibrated probabilities."""
import pandas as pd
from src.fantasy.availability import excluded_by_status


def rank_recent_lineup(candidates, history, target_date, last_game_first=False):
    """Rank by appearances in the last five TEAM games, then baseline TOI.

    The alternate rule retains last-game priority and uses frequency only as a
    tiebreaker. Both preserve saved injury exclusions and the 12F/6D scenario.
    Missing history is zero evidence, not a reason to drop a roster candidate.
    """
    if candidates.duplicated('player_id').any() or candidates.team.nunique() != 1:
        raise ValueError('Expected unique candidates for one team/game')
    team = candidates.team.iloc[0]
    past = history[(history.game_date < target_date) & history.team.eq(team) & history.toi_seconds.gt(0)]
    games = past[['game_date', 'game_id']].drop_duplicates().sort_values(['game_date', 'game_id']).tail(5)
    recent = past[past.game_id.isin(games.game_id)]
    counts = recent.groupby('player_id').game_id.nunique()
    last = set(recent[recent.game_id.eq(games.game_id.iloc[-1])].player_id) if len(games) else set()
    out = candidates.copy()
    out['recent_team_games'] = len(games)
    out['recent_appearances'] = out.player_id.map(counts).fillna(0).astype(int)
    out['played_last_team_game'] = out.player_id.isin(last)
    out['latest_history_date'] = games.game_date.max() if len(games) else None
    out['selected_recent'] = False
    eligible = ~out.injury_status.map(excluded_by_status)
    order = (['played_last_team_game'] if last_game_first else []) + ['recent_appearances', 'expected_toi_minutes_if_plays', 'player_id']
    for pos, slots in [('F', 12), ('D', 6)]:
        z = out[eligible & out.position_group.eq(pos)].sort_values(order, ascending=[False]*(len(order)-1)+[True])
        out.loc[z.head(slots).index, 'selected_recent'] = True
    return out
