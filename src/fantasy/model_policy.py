"""Guard the production selections supported by prospective model reviews."""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOG_EFFECTIVE_FROM = '2026-11-04'
TOI_EFFECTIVE_FROM = '2026-11-14'
PRIMARY_SOG_MODEL = 'calibrated_opponent_sog_trial'
PRIMARY_TOI_MODEL = 'usage_toi_only_trial'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def _read(relative_path):
    return json.loads((ROOT / relative_path).read_text())


def validate_fantasy_policy(target_date, policy):
    """Keep fantasy SOG at default and apply only the reviewed TOI change."""
    if str(target_date) >= TOI_EFFECTIVE_FROM:
        require(policy.get('baseline') == 'default',
                'Fantasy category baseline must remain default')
        require(policy.get('effective_from') == TOI_EFFECTIVE_FROM and
                policy.get('category_models') == {'toi_minutes': PRIMARY_TOI_MODEL},
                'Fantasy policy must select usage-only TOI and leave shots on default')


def validate_current_model_policy(target_date):
    """Fail before acquisition if active config drifts from reviewed selections."""
    target_date = str(target_date)
    daily = _read('config/daily_forecast_trial.json')
    fantasy = _read('config/fantasy_category_policy.json')
    team = _read('config/team_goal_model_active.json')

    if target_date >= SOG_EFFECTIVE_FROM:
        require(daily.get('primary_sog_effective_from') == SOG_EFFECTIVE_FROM,
                'Primary NHL shots effective date differs from reviewed policy')
        require(daily.get('primary_sog_model') == PRIMARY_SOG_MODEL,
                f'For {target_date}, primary NHL shots must use {PRIMARY_SOG_MODEL}')
        require(PRIMARY_SOG_MODEL in daily.get('models', []),
                f'Missing primary NHL shots model: {PRIMARY_SOG_MODEL}')
    if target_date >= TOI_EFFECTIVE_FROM:
        require(daily.get('primary_toi_effective_from') == TOI_EFFECTIVE_FROM,
                'Primary NHL TOI effective date differs from reviewed policy')
        require(daily.get('primary_toi_model') == PRIMARY_TOI_MODEL,
                f'For {target_date}, primary NHL TOI must use {PRIMARY_TOI_MODEL}')
        require(PRIMARY_TOI_MODEL in daily.get('models', []),
                f'Missing primary NHL TOI model: {PRIMARY_TOI_MODEL}')
        validate_fantasy_policy(target_date, fantasy)

    require(team.get('selected_probability_model') == 'raw_direct_team',
            'Raw direct-team probabilities must remain selected')
    require(team.get('probability_calibration_status') == 'challenger_only',
            'Probability calibration must remain a challenger')
    return dict(primary_sog_model=daily.get('primary_sog_model'),
                primary_toi_model=(daily.get('primary_toi_model')
                                   if target_date >= daily.get('primary_toi_effective_from', '9999-12-31')
                                   else 'default'),
                fantasy_shots_model=fantasy.get('category_models', {}).get('shots',
                                                                          fantasy.get('baseline')),
                fantasy_toi_model=fantasy.get('category_models', {}).get('toi_minutes'),
                selected_probability_model=team['selected_probability_model'],
                probability_calibration_status=team['probability_calibration_status'])


def validate_frozen_model_policy(target_date, issue_config):
    """Check that a finalized bundle carries the reviewed all-player selections."""
    target_date = str(target_date)
    models = set(issue_config.get('models', []))
    expected_sog = PRIMARY_SOG_MODEL if target_date >= SOG_EFFECTIVE_FROM else issue_config.get('primary_sog_model', 'default')
    expected_toi = PRIMARY_TOI_MODEL if target_date >= TOI_EFFECTIVE_FROM else 'default'
    if target_date >= SOG_EFFECTIVE_FROM:
        require(issue_config.get('primary_sog_effective_from') == SOG_EFFECTIVE_FROM,
                'Frozen SOG effective date differs from reviewed policy')
        require(expected_sog in models, f'Frozen bundle omits required SOG model {expected_sog}')
        require(issue_config.get('primary_sog_model') == expected_sog,
                f'Frozen SOG selection must be {expected_sog} for {target_date}')
    if target_date >= TOI_EFFECTIVE_FROM:
        require(issue_config.get('primary_toi_effective_from') == TOI_EFFECTIVE_FROM,
                'Frozen TOI effective date differs from reviewed policy')
        require(expected_toi in models, f'Frozen bundle omits required TOI model {expected_toi}')
        require(issue_config.get('primary_toi_model') == PRIMARY_TOI_MODEL,
                f'Frozen TOI configuration must name {PRIMARY_TOI_MODEL}')
    return dict(primary_sog_model=expected_sog, primary_toi_model=expected_toi,
                fantasy_shots_model='default' if target_date >= TOI_EFFECTIVE_FROM else 'default',
                team_probability_model='raw_direct_team',
                probability_calibration_status='challenger_only')
