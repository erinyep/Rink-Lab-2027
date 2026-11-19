import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
EXPORTER = ROOT / 'scripts/export_daily_forecast_template.py'


class DailyForecastTemplateTests(unittest.TestCase):
    def test_exports_hash_verified_minimal_issuance_template(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / 'source'
            output = base / 'template'
            source.mkdir()
            panel = pd.DataFrame({
                'player_id': [10, 20, 10],
                'season_id': [20252026, 20252026, 20262027],
                'position_group': ['F', 'D', 'F'],
                'games_played': [20, 15, 4],
                'goals': [5, 1, 2],
            })
            panel.to_csv(source / 'validated_player_seasons.csv', index=False)
            extra = source / 'current_observed_stats.csv'
            extra.write_text('player_id,season_id\n10,20262027\n')
            goalie_root = base / 'goalie-source'
            source_snapshots = []
            for season in [20232024, 20242025, 20252026]:
                snapshot = f'fantasy_{season}_snapshot'
                path = goalie_root / snapshot / 'historical_goalies.csv'
                path.parent.mkdir(parents=True)
                path.write_text('player_id,season_id\n1,' + str(season) + '\n')
                source_snapshots.append({
                    'season_id': season,
                    'file': f'data/raw/nhl/snapshots/{snapshot}/goalies.csv',
                })
            source_manifest = {
                'created_at_utc': '2026-11-18T15:59:34Z',
                'config': {'target_season': 20262027, 'lookback_seasons': 3,
                           'toi_prior_games': 10},
                'selected_on_validation': {'method': 'weighted', 'decay': 0.5},
                'best_process': {'method': 'process', 'decay': 0.5},
                'current_season_source': {'before_date': '2026-11-18'},
                'espn': {'status': 'disabled_public_data_only'},
                'source_snapshots': source_snapshots,
                'files': {
                    'validated_player_seasons.csv': hashlib.sha256(
                        (source / 'validated_player_seasons.csv').read_bytes()).hexdigest(),
                    'current_observed_stats.csv': hashlib.sha256(extra.read_bytes()).hexdigest(),
                },
            }
            (source / 'manifest.json').write_text(json.dumps(source_manifest))

            result = subprocess.run(
                [sys.executable, str(EXPORTER), '--source', str(source), '--out', str(output),
                 '--goalie-history-root', str(goalie_root)],
                cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)

            manifest = json.loads((output / 'manifest.json').read_text())
            self.assertEqual(manifest['source_bundle_date'], '2026-11-18')
            self.assertEqual(manifest['config'], source_manifest['config'])
            exported_panel = pd.read_csv(output / 'validated_player_seasons.csv')
            self.assertTrue(exported_panel.season_id.lt(20262027).all())
            self.assertEqual(len(exported_panel), 2)
            self.assertEqual(set(manifest['files']), {
                'validated_player_seasons.csv', 'source_manifest.json',
                'goalie_history/fantasy_20232024_snapshot/historical_goalies.csv',
                'goalie_history/fantasy_20242025_snapshot/historical_goalies.csv',
                'goalie_history/fantasy_20252026_snapshot/historical_goalies.csv',
            })
            for name, expected in manifest['files'].items():
                self.assertEqual(hashlib.sha256((output / name).read_bytes()).hexdigest(), expected)
            self.assertEqual(set(manifest['historical_goalie_files']),
                             {'20232024', '20242025', '20252026'})
            self.assertTrue((output / 'source_manifest.json').is_file())
            self.assertFalse((output / 'current_observed_stats.csv').exists())

    def test_rejects_duplicate_player_season_rows(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / 'source'
            output = base / 'template'
            source.mkdir()
            panel_path = source / 'validated_player_seasons.csv'
            pd.DataFrame({
                'player_id': [10, 10], 'season_id': [20252026, 20252026],
            }).to_csv(panel_path, index=False)
            source_manifest = {
                'config': {'target_season': 20262027},
                'selected_on_validation': {},
                'best_process': {},
                'espn': {'status': 'disabled_public_data_only'},
                'source_snapshots': [],
                'files': {'validated_player_seasons.csv': hashlib.sha256(
                    panel_path.read_bytes()).hexdigest()},
            }
            (source / 'manifest.json').write_text(json.dumps(source_manifest))

            result = subprocess.run(
                [sys.executable, str(EXPORTER), '--source', str(source), '--out', str(output)],
                cwd=ROOT, text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('duplicate keys', result.stderr)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
