import unittest

import numpy as np
import pandas as pd

from src.fantasy.shot_context import build_shot_context, matchup_shot_factors


def nhl_game(game_id, game_date, sf=30, sa=20):
    return pd.DataFrame([
        dict(game_id=game_id, game_date=game_date, season_id=20262027,
             team="AAA", opponent="BBB", sf=sf, sa=sa),
        dict(game_id=game_id, game_date=game_date, season_id=20262027,
             team="BBB", opponent="AAA", sf=sa, sa=sf),
    ])


def mp_game(game_id, game_date, sf=30, sa=20, xfor=25., xagainst=15., playoff=0):
    rows = []
    for situation in ["all", "5on5"]:
        for team, opposing, own, opp, xown, xopp in [
            ("AAA", "BBB", sf, sa, xfor, xagainst),
            ("BBB", "AAA", sa, sf, xagainst, xfor),
        ]:
            rows.append(dict(team=team, opposingTeam=opposing, season=game_id // 1000000,
                             gameId=game_id, gameDate=int(game_date.replace("-", "")),
                             situation=situation, playoffGame=playoff, iceTime=3000.,
                             shotsOnGoalFor=own, shotsOnGoalAgainst=opp,
                             xOnGoalFor=xown, xOnGoalAgainst=xopp))
    return pd.DataFrame(rows)


class ShotContextTests(unittest.TestCase):
    def setUp(self):
        self.nhl = nhl_game(2026020001, "2026-10-08", 40, 20)
        self.mp = pd.concat([mp_game(2025020001, "2025-10-01"),
                             mp_game(2026020001, "2026-10-08", 40, 20, 35, 15)],
                            ignore_index=True)

    def context(self, nhl=None, mp=None):
        return build_shot_context(self.nhl if nhl is None else nhl,
                                  self.mp if mp is None else mp,
                                  "2026-10-10", 20262027)

    def test_cutoff_excludes_target_future_and_playoffs(self):
        expected = self.context()
        future_nhl = pd.concat([self.nhl, nhl_game(2026020002, "2026-10-10", 999, 999),
                                nhl_game(2026020003, "2026-10-11", 888, 888)], ignore_index=True)
        future_mp = pd.concat([self.mp, mp_game(2026020002, "2026-10-10", 999, 999),
                               mp_game(2026020003, "2026-10-11", 888, 888),
                               mp_game(2025030111, "2026-05-01", 99, 99, playoff=1)],
                              ignore_index=True)
        pd.testing.assert_frame_equal(expected, self.context(future_nhl, future_mp))

    def test_previous_team_prior_and_original_factor_remain_distinct(self):
        frame = self.context()
        a = frame.set_index("team").loc["AAA"]
        self.assertAlmostEqual(a.shrunken_sf, (40 + 20 * 30) / 21)
        self.assertAlmostEqual(a.original_current_sf, (40 + 20 * 30) / 21)
        self.assertEqual(a.prior_league_sog, 25)
        self.assertEqual(a.current_league_sog, 30)
        self.assertEqual(a.prior_5v5_seconds, 20 * 3000)
        self.assertAlmostEqual(a.xongoal_for_5v5_per60, (35 + 20 * 25) * 3600 / (21 * 3000))
        f = matchup_shot_factors(frame, "AAA", "BBB")
        self.assertNotEqual(f["original_current_sog_factor"], f["prior_season_sog_factor"])
        self.assertAlmostEqual(f["blended_sog_factor"],
                               np.sqrt(f["prior_season_sog_factor"] * f["xongoal_factor"]))

    def test_missing_chance_columns_are_neutral_and_flagged(self):
        f = matchup_shot_factors(self.context(mp=self.mp.drop(columns=["xOnGoalFor", "xOnGoalAgainst"])),
                                 "AAA", "BBB")
        self.assertEqual(f["xongoal_factor"], 1)
        self.assertTrue(f["xongoal_context_missing"])
        missing = matchup_shot_factors(self.context(), "UNKNOWN", "BBB")
        for key in ["original_current_sog_factor", "prior_season_sog_factor", "xongoal_factor", "blended_sog_factor"]:
            self.assertEqual(missing[key], 1)
        self.assertTrue(missing["prior_context_missing"])

    def test_disputed_game_excluded_from_chance_features_not_nhl(self):
        disputed = self.mp.copy()
        disputed.loc[(disputed.gameId == 2026020001) & (disputed.team == "AAA"), "shotsOnGoalFor"] = 39
        disputed.loc[(disputed.gameId == 2026020001) & (disputed.team == "BBB"), "shotsOnGoalAgainst"] = 39
        c = self.context(mp=disputed).set_index("team")
        self.assertEqual(c.loc["AAA", "nhl_games"], 1)
        self.assertTrue(c.moneypuck_shot_discrepancy_games.eq(1).all())
        self.assertTrue(c.moneypuck_5v5_games_used.eq(0).all())
        self.assertAlmostEqual(c.loc["AAA", "xongoal_for_5v5_per60"], 25 * 3600 / 3000)

    def test_invalid_pairs_duplicates_and_season_raise(self):
        with self.assertRaisesRegex(ValueError, "Incomplete NHL"):
            self.context(nhl=self.nhl.iloc[:1])
        with self.assertRaisesRegex(ValueError, "Duplicate NHL"):
            self.context(nhl=pd.concat([self.nhl, self.nhl.iloc[:1]]))
        with self.assertRaisesRegex(ValueError, "Duplicate MoneyPuck"):
            self.context(mp=pd.concat([self.mp, self.mp.iloc[:1]]))
        malformed = self.mp.copy()
        malformed.loc[malformed.gameId.eq(2026020001), "season"] = 2025
        with self.assertRaisesRegex(ValueError, "season mismatch"):
            self.context(mp=malformed)


if __name__ == "__main__":
    unittest.main()
