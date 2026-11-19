from contextlib import redirect_stderr
from io import StringIO
import subprocess
import unittest
from unittest.mock import patch

from scripts.issue_daily_forecasts import run


class DailyForecastRunnerTests(unittest.TestCase):
    def test_failed_child_logs_only_safe_stage_and_error_class(self):
        failure = subprocess.CompletedProcess(
            args=['python', 'scripts/acquire_current_game_history.py'],
            returncode=1,
            stdout='Traceback (most recent call last):\nValueError: private response body\n',
        )
        diagnostic = StringIO()
        with patch('scripts.issue_daily_forecasts.subprocess.run', return_value=failure):
            with redirect_stderr(diagnostic):
                with self.assertRaises(subprocess.CalledProcessError):
                    run('acquire_current_game_history.py', ['--through', '2026-11-18'])

        self.assertIn('acquire_current_game_history.py', diagnostic.getvalue())
        self.assertIn('ValueError', diagnostic.getvalue())
        self.assertNotIn('private response body', diagnostic.getvalue())


if __name__ == '__main__':
    unittest.main()
