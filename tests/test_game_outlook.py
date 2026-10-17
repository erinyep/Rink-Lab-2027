import unittest
from src.fantasy.game_outlook import game_outlooks


class GameOutlookTests(unittest.TestCase):
    def fixture(self):
        game=dict(id=1,startTimeUTC='2026-10-17T20:00:00Z',homeTeam=dict(abbrev='H'),awayTeam=dict(abbrev='A'))
        rows=[dict(game_id=1,model='default',team=t,opponent=o,start_time_utc=game['startTimeUTC'],issue_timing='pregame',
                   expected_goals=goals,expected_shots=30,goals_p10=1,goals_p90=6,shots_p10=23,shots_p90=37,
                   identified_skaters=18,unidentified_replacement_skaters=0) for t,o,goals in [('A','H',4),('H','A',3)]]
        return rows,[game]

    def test_pairs_home_away_by_schedule_not_csv_order(self):
        rows,games=self.fixture();r=game_outlooks(rows,games)[0]
        self.assertEqual(r['home_expected_goals'],3)
        self.assertEqual(r['away_expected_goals'],4)
        self.assertEqual(r['higher_scoring_mean'],'A')
        self.assertEqual(r['home_goal_edge'],-1)
        self.assertNotIn('win_probability',r)

    def test_late_forecast_label_is_preserved(self):
        rows,games=self.fixture()
        for r in rows:r['issue_timing']='late_not_pregame'
        self.assertEqual(game_outlooks(rows,games)[0]['issue_timing'],'late_not_pregame')

    def test_missing_duplicate_or_invalid_counts_fail(self):
        rows,games=self.fixture()
        with self.assertRaises(ValueError):game_outlooks(rows[:1],games)
        with self.assertRaises(ValueError):game_outlooks(rows+rows[:1],games)
        rows[0]['expected_goals']=float('nan')
        with self.assertRaises(ValueError):game_outlooks(rows,games)

    def test_every_model_must_cover_the_same_slate(self):
        rows,games=self.fixture()
        game=dict(games[0],id=2);games.append(game)
        with self.assertRaisesRegex(ValueError,'every scheduled game'):
            game_outlooks(rows,games)


if __name__=='__main__':unittest.main()
