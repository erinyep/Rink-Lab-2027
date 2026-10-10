"""Prevent live actuals or wrong-season ESPN splits entering a benchmark."""
import unittest

from scripts.export_espn_projection_benchmark import projection_entry


class ESPNProjectionBenchmarkTests(unittest.TestCase):
    @staticmethod
    def split(season=2027, source=1, split_type=0, period=0, shots=280):
        return dict(seasonId=season, statSourceId=source, statSplitTypeId=split_type,
                    scoringPeriodId=period, stats={"29": shots, "34": 80})

    def test_only_matching_season_total_projection_selected(self):
        player = dict(id=1, fullName="Example", stats=[
            self.split(source=0, shots=5),
            self.split(season=2026, shots=300),
            self.split(split_type=5, period=12, shots=3),
            self.split(),
        ])
        row = projection_entry(player, 2027)
        self.assertEqual(row["stats"], {"29": 280, "34": 80})
        self.assertEqual(row["projection_entry_count"], 1)

    def test_missing_projection_does_not_fall_back_to_actual(self):
        row = projection_entry(dict(id=1, stats=[self.split(source=0)]), 2027)
        self.assertEqual(row["stats"], {})
        self.assertEqual(row["projection_entry_count"], 0)

    def test_identical_duplicates_audited_and_conflicts_rejected(self):
        row = projection_entry(dict(id=1, stats=[self.split(), self.split()]), 2027)
        self.assertEqual(row["projection_entry_count"], 2)
        with self.assertRaises(ValueError):
            projection_entry(dict(id=1, stats=[self.split(), self.split(shots=281)]), 2027)


if __name__ == "__main__":
    unittest.main()
