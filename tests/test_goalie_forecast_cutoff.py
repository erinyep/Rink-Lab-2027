"""Cutoff and role checks for daily goalie issuance."""
import unittest

import pandas as pd

from scripts.build_goalie_game_forecasts import current_goalie_history, issue_timing


class GoalieForecastCutoffTests(unittest.TestCase):
    def appearances(self):
        return pd.DataFrame([
            dict(game_id=2026020066, game_date='2026-10-09', player_id=1,
                 starter=True, toi_seconds=3600, shots_against=30, saves=27,
                 goals_against=3, count_identity_ok=True),
            dict(game_id=2026020066, game_date='2026-10-09', player_id=2,
                 starter=False, toi_seconds=0, shots_against=0, saves=0,
                 goals_against=0, count_identity_ok=True),
            dict(game_id=2026020070, game_date='2026-10-10', player_id=1,
                 starter=True, toi_seconds=3600, shots_against=99, saves=99,
                 goals_against=0, count_identity_ok=True),
        ])

    def test_current_outcomes_excluded_from_both_rates_and_roles(self):
        roles, history, excluded = current_goalie_history(self.appearances(), '2026-10-10', 20262027)
        self.assertEqual(excluded, 1)
        self.assertEqual(roles.game_id.unique().tolist(), [2026020066])
        self.assertEqual(roles.starter.sum(), 1)
        self.assertEqual(history.player_id.tolist(), [1])
        self.assertEqual(history.iloc[0].shots_against, 30)
        self.assertEqual(history.iloc[0].saves, 27)

    def test_count_exception_marks_whole_player_season_ineligible(self):
        frame = self.appearances()
        frame.loc[0, 'shots_against'] = 31
        _, history, _ = current_goalie_history(frame, '2026-10-10', 20262027)
        self.assertFalse(history.iloc[0].eligible_for_valuation)
        self.assertEqual(history.iloc[0].shots_against, 31)

    def test_duplicate_or_wrong_season_rejected(self):
        frame = self.appearances()
        for invalid in [pd.concat([frame, frame.iloc[:1]]), frame.assign(game_id=2025020066)]:
            with self.assertRaises(ValueError):
                current_goalie_history(invalid, '2026-10-10', 20262027)

    def test_issue_timing_is_per_game_and_boundary_is_late(self):
        issued = '2026-10-10T20:30:00Z'
        self.assertEqual(issue_timing('2026-10-10T17:00:00Z', issued), 'late_not_pregame')
        self.assertEqual(issue_timing(issued, issued), 'late_not_pregame')
        self.assertEqual(issue_timing('2026-10-10T23:00:00Z', issued), 'pregame')


if __name__ == '__main__':
    unittest.main()
