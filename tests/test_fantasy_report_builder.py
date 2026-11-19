import unittest

import pandas as pd

from scripts.build_today_report import join_goalie_roster


class GoalieRosterJoinTests(unittest.TestCase):
    def test_unmatched_roster_goalies_do_not_break_matched_forecast_join(self):
        projections = pd.DataFrame([
            {'player_id': 10, 'model': 'goalie_history_baseline', 'injury_status': 'UNKNOWN'},
            {'player_id': 20, 'model': 'goalie_history_baseline', 'injury_status': 'UNKNOWN'},
        ])
        own = pd.DataFrame([
            {'is_goalie': True, 'nhl_player_id': 10, 'lineup_slot': 'G',
             'injury_status': 'ACTIVE', 'start_local': '7:00 PM'},
            {'is_goalie': True, 'nhl_player_id': None, 'lineup_slot': 'Bench',
             'injury_status': 'ACTIVE', 'start_local': ''},
            {'is_goalie': True, 'nhl_player_id': None, 'lineup_slot': 'Bench',
             'injury_status': 'ACTIVE', 'start_local': ''},
        ])

        result = join_goalie_roster(projections, own)

        self.assertEqual(result.player_id.tolist(), [10])
        self.assertEqual(result.lineup_slot.tolist(), ['G'])

    def test_duplicate_matched_roster_goalies_fail_with_clear_message(self):
        projections = pd.DataFrame([
            {'player_id': 10, 'model': 'goalie_history_baseline', 'injury_status': 'UNKNOWN'},
        ])
        own = pd.DataFrame([
            {'is_goalie': True, 'nhl_player_id': 10, 'lineup_slot': 'G',
             'injury_status': 'ACTIVE', 'start_local': '7:00 PM'},
            {'is_goalie': True, 'nhl_player_id': 10, 'lineup_slot': 'Bench',
             'injury_status': 'ACTIVE', 'start_local': ''},
        ])

        with self.assertRaisesRegex(ValueError, 'Duplicate matched goalie identity'):
            join_goalie_roster(projections, own)


if __name__ == '__main__':
    unittest.main()
