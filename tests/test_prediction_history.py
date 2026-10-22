import json
from pathlib import Path
import tempfile
import unittest

from src.fantasy.history import archive_snapshot, digest


class PredictionHistoryTests(unittest.TestCase):
    def test_idempotency_corrections_and_tampering(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base/'source'
            source.mkdir()
            data = source/'actuals.csv'
            def version(value):
                data.write_text(value)
                (source/'manifest.json').write_text(json.dumps({'files': {'actuals.csv': digest(data)}}))
            version('shots\n2\n')
            first = archive_snapshot(source, base/'history', 'actuals')
            self.assertEqual(first, archive_snapshot(source, base/'history', 'actuals'))
            version('shots\n3\n')
            second = archive_snapshot(source, base/'history', 'actuals')
            self.assertNotEqual(first, second)
            self.assertEqual((first/'actuals.csv').read_text(), 'shots\n2\n')
            (second/'actuals.csv').write_text('corrupt')
            with self.assertRaisesRegex(ValueError, 'Changed archive'):
                archive_snapshot(source, base/'history', 'actuals')
            data.write_text('corrupt source')
            with self.assertRaisesRegex(ValueError, 'Changed source'):
                archive_snapshot(source, base/'history', 'actuals')
