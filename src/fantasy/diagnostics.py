"""Interpretable forecast accounting and past-only defense opportunity proxies."""
import numpy as np
import pandas as pd

from .per_game import require


def defense_opportunity(games, before):
    """All-strength D production, not on-ice chances or causal creation.

    A D assist is an assist credit; two defensemen can assist the same goal.
    Never label that sum as a count of distinct offensive opportunities.
    """
    require(not games.duplicated(['game_id', 'player_id']).any(), 'Duplicate player/game')
    g = games[(games.game_date < before) & games.toi_seconds.gt(0)].copy()
    require(g.position.notna().all(), 'Missing position')
    require(g.position.isin(['C', 'L', 'R', 'LW', 'RW', 'F', 'D']).all(), 'Unknown position')
    require(g[['shots', 'assists', 'toi_seconds']].notna().all().all(), 'Missing defense inputs')
    require((g[['shots', 'assists', 'toi_seconds']] >= 0).all().all(), 'Negative defense inputs')
    rows = []
    for team, t in g.groupby('team'):
        d = t[t.position.eq('D')]
        n = t.game_id.nunique()
        rows.append(dict(team=team, before_date=before, games=n,
            latest_game_date=t.game_date.max(), defense_player_games=len(d),
            defense_shots=d.shots.sum(), team_shots=t.shots.sum(),
            defense_shots_per_game=d.shots.sum()/n,
            defense_shot_share=d.shots.sum()/t.shots.sum() if t.shots.sum() else np.nan,
            defense_assist_credits_per_game=d.assists.sum()/n,
            defense_shots_per60_player_minutes=3600*d.shots.sum()/d.toi_seconds.sum() if len(d) else np.nan))
    return pd.DataFrame(rows)


def shot_contributions(context, calibration):
    """Exact sequential accounting for the usage trial's unconstrained SOG.

    Ordering is explicit: baseline -> TOI -> rate -> calibration -> matchup.
    Effects interact; these are forecast movements, not causal importance,
    SHAP values, or measured predictive gains. Constraint residual is external.
    """
    c = context.copy()
    require(c.baseline_toi_minutes.gt(0).all(), 'Nonpositive baseline TOI')
    rate = c.baseline_shots / c.baseline_toi_minutes
    toi = c.usage_toi_minutes * rate
    usage = c.usage_shots_before_context
    c['toi_contribution'] = toi - c.baseline_shots
    c['shot_rate_contribution'] = usage - toi
    c['calibration_contribution'] = usage * (calibration - 1)
    c['matchup_contribution'] = usage * calibration * (c.blended_sog_factor - 1)
    c['reconstructed_usage_shots'] = usage * calibration * c.blended_sog_factor
    cols = ['toi_contribution', 'shot_rate_contribution', 'calibration_contribution', 'matchup_contribution']
    require(np.allclose(c.baseline_shots+c[cols].sum(axis=1), c.reconstructed_usage_shots), 'Accounting failed')
    c['largest_forecast_movement'] = c[cols].abs().idxmax(axis=1)
    return c
