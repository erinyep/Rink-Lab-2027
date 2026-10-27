import copy
import unittest
from scripts.evaluate_probability_benchmark import score_game


class ProbabilityEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.f=dict(game_id=1,date='2026-10-24',home='BOS',away='SJS',start_time_utc='2026-10-24T23:00:00Z',
                    issued_at_utc='2026-10-24T11:00:00Z',home_win_probability=.6,away_win_probability=.4)
        self.q=[dict(game_id=1,team=t,sampled_at_utc='2026-10-24T11:02:00Z',yes_bid=p-.01,yes_ask=p+.01,quoted_midpoint=p)
                for t,p in [('BOS',.65),('SJS',.35)]]
        self.b=dict(id=1,gameDate='2026-10-24',season=20262027,gameType=2,gameState='OFF',startTimeUTC=self.f['start_time_utc'],
                    homeTeam=dict(abbrev='BOS',score=3),awayTeam=dict(abbrev='SJS',score=2))

    def test_one_home_outcome_and_brier(self):
        rows=score_game(self.f,self.q,self.b)
        self.assertEqual(len(rows),3)
        self.assertAlmostEqual(rows[0]['brier'],.16)
        self.assertAlmostEqual(rows[1]['brier'],.1225)

    def test_reject_postgame_quote_and_rescheduling(self):
        q=copy.deepcopy(self.q);q[0]['sampled_at_utc']=self.f['start_time_utc']
        with self.assertRaisesRegex(ValueError,'non-pregame'):score_game(self.f,q,self.b)
        b=copy.deepcopy(self.b);b['startTimeUTC']='2026-10-25T23:00:00Z'
        with self.assertRaisesRegex(ValueError,'Rescheduled'):score_game(self.f,self.q,b)

    def test_reject_duplicate_team_and_malformed_probability(self):
        with self.assertRaisesRegex(ValueError,'quote pair'):score_game(self.f,[self.q[0],self.q[0]],self.b)
        f=dict(self.f,away_win_probability=.5)
        with self.assertRaisesRegex(ValueError,'probability pair'):score_game(f,self.q,self.b)
