"""Status exclusions are operational rules, not calibrated participation forecasts."""
BLOCKED_STATUSES={'OUT','INJURY_RESERVE','SUSPENSION','IR'}


def excluded_by_status(status):
    return str(status).strip().upper() in BLOCKED_STATUSES
