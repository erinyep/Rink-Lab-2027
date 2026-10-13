import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.evaluate_daily_forecasts import (CATEGORIES, score_players, score_teams,
    score_goalies, verify_hash, digest, validate_timing, reading_views, load_goalie_source)


def timing(late=False):
    return dict(start_time_utc="2026-10-10T23:00:00Z",
                issued_at_utc="2026-10-11T00:00:00Z" if late else "2026-10-10T22:00:00Z",
                issue_timing="late_not_pregame" if late else "pregame")


def skater(pid, seconds, shots):
    row = {c: 0. for c in CATEGORIES}
    row.update(game_id=1, player_id=pid, team="AAA", toi_seconds=seconds,
               toi_minutes=seconds / 60, shots=shots, goals=1, points=1)
    return row


class DailyEvaluationTests(unittest.TestCase):
    def test_incomplete_bundle_reading_views_preserve_frozen_means(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'inputs').mkdir()
            pd.DataFrame([dict(game_id=1,player_id=10,selected_for_trial=True,selection_reason='prior_game')]).to_csv(root/'inputs/lineup_audit.csv',index=False)
            players=pd.DataFrame([dict(game_id=1,player_id=10,model='default',team='AAA',opponent='BBB',category=c,model_projection_if_plays=float(i),**timing()) for i,c in enumerate(CATEGORIES)])
            teams=pd.DataFrame([dict(game_id=1,team='AAA',opponent='BBB',model='default',category='shots',projection_mean=30.,opponent_projection_mean=25.,whole_number_guess=29,**timing())])
            wide,tw=reading_views(root,players,teams)
            self.assertEqual(wide.expected_shots_if_plays.iloc[0],2.)
            self.assertTrue(wide.selected_for_trial.iloc[0])
            self.assertEqual(tw.expected_shots_against.iloc[0],25.)
            self.assertIsNone(load_goalie_source(root,None,[]))
            self.assertFalse((root/'player_projections.csv').exists())

    def test_absent_and_zero_toi_players_remain_unknown_and_timing_separate(self):
        forecasts = pd.DataFrame([dict(game_id=1, player_id=p, model="default", category="shots",
            model_projection_if_plays=2., actual=np.nan, whole_number_guess=2,
            simulation_p10=0, simulation_p90=4, **timing(p == 4)) for p in [1, 2, 3, 4]])
        actuals = pd.DataFrame([skater(1, 900, 4), skater(2, 0, 0), skater(4, 900, 1)])
        scored, metrics = score_players(forecasts, actuals)
        self.assertEqual(scored.actual.notna().sum(), 2)
        self.assertTrue(scored[scored.player_id.isin([2, 3])].actual.isna().all())
        self.assertEqual(metrics.set_index("issue_timing").loc["pregame", "mae"], 2)
        self.assertEqual(metrics.set_index("issue_timing").loc["late_not_pregame", "mae"], 1)
        self.assertTrue(forecasts.actual.isna().all())

    def test_team_shots_are_official_but_goals_exclude_shootout_bonus(self):
        forecasts = pd.DataFrame([dict(game_id=1, team="AAA", model="default", category=c,
            projection_mean=3., whole_number_guess=3, simulation_p10=0, simulation_p90=9,
            **timing()) for c in ["shots", "goals"]])
        actuals = pd.DataFrame([skater(1, 900, 4), skater(2, 900, 3)])
        boxes = {1: dict(homeTeam=dict(abbrev="AAA", sog=8, score=3),
                         awayTeam=dict(abbrev="BBB", sog=10, score=2))}
        result, _ = score_teams(forecasts, actuals, boxes)
        result = result.set_index("category")
        self.assertEqual(result.loc["shots", "actual"], 8)
        self.assertEqual(result.loc["shots", "actual_skater_sum"], 7)
        self.assertEqual(result.loc["goals", "actual"], 2)

    def goalie_fixture(self):
        forecasts = []
        for pid, share in [(1, .6), (2, .25), (3, .15), (4, 0.)]:
            row = dict(game_id=1, team="AAA", player_id=pid, model="goalie_history_baseline",
                       start_share_provisional=share, **timing())
            for category, mean in [("shots_against", 30), ("saves", 27), ("goals_against", 3)]:
                row[category + "_if_full_start"] = mean
                row[category + "_simulation_p10"] = 0
                row[category + "_simulation_p90"] = 40
            forecasts.append(row)
        actual = []
        for pid, seconds, starter, shots, saves in [(1, 3500, True, 30, 27),
                                                   (2, 100, False, 2, 2), (3, 0, False, 0, 0)]:
            actual.append(dict(game_id=1, team="AAA", player_id=pid, starter=starter,
                toi_seconds=seconds, shots_against=shots, saves=saves, goals_against=shots-saves,
                wins=int(starter), gaa=3 if seconds else np.nan,
                save_percentage=saves/shots if shots else np.nan, count_identity_ok=True))
        return pd.DataFrame(forecasts), pd.DataFrame(actual)

    def test_goalie_roles_missing_counts_and_team_level_brier(self):
        forecasts, actuals = self.goalie_fixture()
        result, metrics, starters = score_goalies(forecasts, actuals)
        result = result.set_index("player_id")
        self.assertEqual(result.loc[1, "actual_role"], "starter")
        self.assertEqual(result.loc[2, "actual_role"], "relief")
        self.assertEqual(result.loc[3, "actual_role"], "unused_backup")
        self.assertEqual(result.loc[4, "actual_role"], "not_in_boxscore")
        self.assertTrue(np.isnan(result.loc[4, "actual_shots_against"]))
        self.assertEqual(result.loc[4, "actual_starter"], 0)
        self.assertTrue(np.isnan(result.loc[3, "shots_against_absolute_error"]))
        self.assertEqual(set(metrics.population), {"actual_starters", "starters_55_to_65_minutes", "relief_appearances"})
        self.assertAlmostEqual(starters.iloc[0].brier_score, .4**2 + .25**2 + .15**2)

    def test_starter_outside_candidates_is_penalized_and_unknown_starter_not_invented(self):
        forecasts, actuals = self.goalie_fixture()
        actuals.loc[actuals.player_id.eq(1), "player_id"] = 999
        _, _, starters = score_goalies(forecasts, actuals)
        self.assertAlmostEqual(starters.iloc[0].brier_score, 1 + .6**2 + .25**2 + .15**2)
        self.assertFalse(starters.iloc[0].actual_starter_in_candidates)
        self.assertTrue(np.isinf(starters.iloc[0].log_loss))
        actuals["starter"] = False
        result, _, starters = score_goalies(forecasts, actuals)
        self.assertTrue(result.actual_starter.isna().all())
        self.assertEqual(starters.iloc[0].scoring_status, "unknown_starter_or_probability")

    def test_timing_and_hash_tampering_are_rejected(self):
        row = timing()
        row["issue_timing"] = "late_not_pregame"
        with self.assertRaisesRegex(ValueError, "Issue timing"):
            validate_timing(pd.DataFrame([row]))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "frozen.csv"
            path.write_text("original")
            expected = digest(path)
            path.write_text("changed")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                verify_hash(path, expected, [])


if __name__ == "__main__":
    unittest.main()
