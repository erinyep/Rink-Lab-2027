"""Protect research contracts: no future information, no silent attrition, IDs."""
import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from src.fantasy.per_game import EVENTS, TARGETS, evaluate, forecast
from src.fantasy import espn_snapshot
from src.fantasy.schedule import export_schedule_reference, schedule_rows


def example_panel():
    rows = []
    for season in [20222023, 20232024, 20242025, 20252026]:
        for player, position in [(1, "C"), (2, "D")]:
            rows.append(dict(player_id=player, season_id=season, skater_full_name=f"Player {player}",
                             position_code=position, position_group="D" if position == "D" else "F",
                             team_abbrevs="MIN", games_played=20, toi_minutes=300,
                             goals=4, assists=6, points=10, shots=40, hits=20,
                             penalty_minutes=8, pp_points=3, plus_minus=-2))
    return pd.DataFrame(rows)


class ForecastTests(unittest.TestCase):
    def test_future_targets_never_change_prior_forecasts(self):
        panel = example_panel()
        before = forecast(panel, 20242025)
        panel.loc[panel.season_id >= 20242025, EVENTS] = 99999
        pd.testing.assert_frame_equal(before, forecast(panel, 20242025))

    def test_live_update_excludes_later_seasons(self):
        panel = example_panel()
        before = forecast(panel, 20242025, include_current=True)
        panel.loc[panel.season_id > 20242025, EVENTS] = 99999
        pd.testing.assert_frame_equal(before, forecast(panel, 20242025, include_current=True))

    def test_components_and_point_identity(self):
        result = forecast(example_panel(), 20252026)
        np.testing.assert_allclose(result.points_per_game, result.goals_per_game + result.assists_per_game)
        np.testing.assert_allclose(result.goals_per_game, result.shots_per_game * result.shooting_probability)
        np.testing.assert_allclose(result.shots_per_game, result.shots_per_60 * result.toi_minutes_per_game / 60)
        self.assertTrue(result.shooting_observed_weight.between(0, 1).all())

    def test_zero_shots_no_nan_and_past_position_prior(self):
        panel = example_panel()
        panel.loc[panel.player_id == 1, ["shots", "goals"]] = 0
        panel.loc[panel.player_id == 1, "points"] = panel.loc[panel.player_id == 1, "assists"]
        # Keep another forward to provide a nonzero position shooting denominator.
        other = example_panel().query("player_id == 1").copy()
        other["player_id"] = 3
        panel = pd.concat([panel, other], ignore_index=True)
        result = forecast(panel, 20252026, shooting_prior_shots=0)
        self.assertTrue(np.isfinite(result.goals_per_game).all())

    def test_no_target_appearance_is_not_zero_per_game(self):
        panel = example_panel()
        panel = panel[~((panel.season_id == 20252026) & (panel.player_id == 2))]
        prediction = forecast(panel, 20252026)
        metrics, players, coverage = evaluate(prediction, panel, 20252026)
        self.assertEqual(coverage["no_reported_appearance"], 1)
        self.assertEqual(len(players), 2)
        self.assertTrue(players.loc[players.player_id == 2, "goals"].isna().all())
        self.assertTrue((metrics.players == 1).all())

    def test_current_rookie_retained_and_shrunk(self):
        panel = example_panel()
        rookie = panel.iloc[[-1]].copy()
        rookie["player_id"] = 3
        rookie["games_played"] = 1
        rookie["toi_minutes"] = 15
        rookie["shots"] = 10
        rookie["goals"] = 5
        rookie["points"] = rookie.goals + rookie.assists
        result = forecast(pd.concat([panel, rookie]), 20252026, include_current=True)
        row = result.set_index("player_id").loc[3]
        self.assertEqual(row.evidence, "no_completed_season_history")
        self.assertGreater(row.shooting_probability, 0)
        self.assertLess(row.shooting_probability, .5)


class CrosswalkTests(unittest.TestCase):
    def test_pending_drop_overlap_is_preserved_but_unexplained_overlap_fails(self):
        roster = dict(espn_player_id=1, roster_entry_status="FUTURE_DROP", pool_status="WAIVERS", pool_on_team_id=0)
        available = dict(espn_player_id=1, availability_status="WAIVERS")
        checks = espn_snapshot._validate([dict(team_id=1)], [roster], [available])
        self.assertTrue(checks["roster_available_overlap_explained"])
        roster["roster_entry_status"] = "NORMAL"
        with self.assertRaisesRegex(RuntimeError, "overlap"):
            espn_snapshot._validate([dict(team_id=1)], [roster], [available])

    def test_same_name_different_positions(self):
        index = {"eliaspettersson": [dict(nhl_player_id="1", nhl_name="Elias Pettersson", nhl_team="VAN", position="C"),
                                     dict(nhl_player_id="2", nhl_name="Elias Pettersson", nhl_team="VAN", position="D")]}
        player = dict(espn_player_id=100, player_name="Elias Pettersson", nhl_team="Vancouver Canucks", primary_position="Center")
        with patch.object(espn_snapshot, "_nhl_index", return_value=(index, ["source.csv"])):
            result, _ = espn_snapshot._crosswalk_rows([player], [])
        self.assertEqual(result[0]["nhl_player_id"], "1")
        self.assertEqual(result[0]["match_method"], "exact_normalized_name_and_position")

    def test_multiple_seasons_deduplicate_id_without_losing_old_players(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for season, ids in [(20242025, [1, 2]), (20252026, [1])]:
                path = root / f"data/processed/fantasy/fantasy_{season}_20261006T000000Z/historical_skaters.csv"
                path.parent.mkdir(parents=True)
                with path.open("w") as f:
                    writer = csv.DictWriter(f, fieldnames=["player_id", "skater_full_name", "position_code"])
                    writer.writeheader()
                    for player in ids:
                        writer.writerow(dict(player_id=player, skater_full_name=f"Player {player}", position_code="C"))
            with patch.object(espn_snapshot, "REPO_ROOT", root):
                index, _ = espn_snapshot._nhl_index()
            self.assertEqual(len(index["player1"]), 1)
            self.assertEqual(index["player2"][0]["nhl_player_id"], "2")


class ScheduleTests(unittest.TestCase):
    def make_snapshot(self, root):
        team = dict(id=68, abbrev="UTA", placeName={"default": "Utah"}, commonName={"default": "Mammoth"})
        away = dict(id=30, abbrev="MIN", placeName={"default": "Minnesota"}, commonName={"default": "Wild"})
        games = []
        for number, start, state, kind, schedule_state in [
            (1, "2026-10-06T23:00:00Z", "FUT", 2, "OK"),
            (2, "2026-10-06T22:59:00Z", "LIVE", 2, "OK"),
            (3, "2026-10-13T23:00:00Z", "FUT", 2, "OK"),
            (4, "2026-10-07T23:00:00Z", "FUT", 1, "OK"),
            (5, "2026-10-08T23:00:00Z", "FUT", 2, "PPD")]:
            games.append(dict(id=number, season=20262027, gameType=kind, gameState=state,
                              gameScheduleState=schedule_state, startTimeUTC=start, homeTeam=team, awayTeam=away))
        payload = json.dumps(dict(gameWeek=[dict(date="2026-10-06", games=games)])).encode()
        (root / "schedule.json").write_bytes(payload)
        (root / "metadata.json").write_text(json.dumps(dict(season_id=20262027,
            cutoff_utc="2026-10-06T23:00:00+00:00", sources=[dict(file="schedule.json", sha256=hashlib.sha256(payload).hexdigest())])))

    def test_half_open_future_window_regular_season_and_utah_alias(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_snapshot(root)
            rows, teams, _ = schedule_rows(root)
            self.assertEqual(set(rows.game_id), {1})
            self.assertEqual(teams["utahhockeyclub"], "UTA")
            self.assertNotIn("arizonacoyotes", teams)
            (root / "schedule.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                schedule_rows(root)

    def test_unknown_team_and_participation_are_not_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_snapshot(root)
            players = pd.DataFrame([dict(espn_player_id=1, primary_position="Center", nhl_team="Utah Hockey Club", pool="rostered"),
                                    dict(espn_player_id=2, primary_position="Center", nhl_team="Unknown Team", pool="available")])
            for event in TARGETS:
                players[f"{event}_per_game"] = 1.0
            players.to_csv(root / "espn.csv", index=False)
            export_schedule_reference(root / "espn.csv", root, root)
            weekly = pd.read_csv(root / "seven_day_schedule_reference.csv")
            self.assertTrue(weekly.loc[weekly.espn_player_id == 2, "scheduled_team_games"].isna().all())
            games = pd.read_csv(root / "scheduled_skater_game_forecasts.csv")
            self.assertTrue(games.expected_goals.isna().all())
            self.assertEqual(games.goals_if_plays.iloc[0], 1.0)


if __name__ == "__main__":
    unittest.main()
