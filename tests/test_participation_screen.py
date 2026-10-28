import unittest
import pandas as pd
from src.fantasy.participation_screen import rank_recent_lineup


class ParticipationTest(unittest.TestCase):
    def test_team_game_denominator_target_exclusion_and_injury(self):
        c = pd.DataFrame([dict(player_id=i, team='A', position_group='D', injury_status='OUT' if i == 7 else 'ACTIVE', expected_toi_minutes_if_plays=i) for i in range(1, 8)])
        h = pd.DataFrame([dict(game_id=g, game_date=f'2026-10-{g:02d}', player_id=p, team='A', toi_seconds=100) for g, p in [(1,1),(2,1),(2,2),(3,3),(4,6),(4,7)]])
        z = rank_recent_lineup(c, h, '2026-10-04').set_index('player_id')
        self.assertEqual(z.loc[1, 'recent_team_games'], 3)
        self.assertEqual(z.loc[1, 'recent_appearances'], 2)
        self.assertEqual(z.loc[6, 'recent_appearances'], 0)
        self.assertFalse(z.loc[7, 'selected_recent'])
        self.assertEqual(z.selected_recent.sum(), 6)
        self.assertEqual(z.latest_history_date.max(), '2026-10-03')

    def test_frequency_changes_selection_with_fixed_capacity(self):
        c = pd.DataFrame([dict(player_id=i, team='A', position_group='D', injury_status='ACTIVE', expected_toi_minutes_if_plays=i) for i in range(1,8)])
        h = pd.DataFrame([dict(game_id=g, game_date=f'2026-10-{g:02d}', player_id=p, team='A', toi_seconds=100) for g,p in [(1,1),(2,1),(3,7)]])
        z = rank_recent_lineup(c,h,'2026-10-04').set_index('player_id')
        self.assertTrue(z.loc[1,'selected_recent'])
        self.assertFalse(z.loc[2,'selected_recent'])


if __name__ == '__main__':
    unittest.main()
