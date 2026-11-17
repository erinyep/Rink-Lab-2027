import unittest
import pandas as pd
from scripts.build_team_total_trial import select_lineup
from scripts.snapshot_nhl_lineups import ArticleParagraphs, parse_lineups


class PublishedLineupTests(unittest.TestCase):
    def setUp(self):
        self.players = pd.DataFrame(dict(player_id=range(20), injury_status='UNKNOWN',
            has_forecast=True, position_group=['F']*14+['D']*6,
            played_last_team_game=True, toi_minutes_per_game=20))
        self.published = pd.DataFrame(dict(player_id=list(range(2,14))+list(range(14,20)),
            role=['F']*12+['D']*6, projected_status='projected_skater'))

    def test_complete_source_replaces_heuristic_and_keeps_other_players(self):
        result = select_lineup(self.players, published_lineup=self.published)
        self.assertEqual(set(result.loc[result.selected_for_trial, 'player_id']), set(range(2,20)))
        self.assertEqual(len(result),20)
        self.assertTrue(result.published_lineup_applied.all())

    def test_incomplete_unresolved_or_duplicate_source_preserves_heuristic(self):
        expected = select_lineup(self.players).selected_for_trial.tolist()
        for source in [self.published.iloc[:-1], self.published.assign(player_id=None),
                       pd.concat([self.published.iloc[:-1], self.published.iloc[[0]]])]:
            result = select_lineup(self.players, published_lineup=source)
            self.assertEqual(result.selected_for_trial.tolist(),expected)
            self.assertFalse(result.published_lineup_applied.any())

    def test_article_inline_markup_and_line_separator(self):
        parser=ArticleParagraphs()
        parser.feed('<article><p>Wild projected lineup</p><p>A -- B -- C</p>'
                    '<p>D – E</p><p><strong>Injured:</strong> F (upper body)</p></article>')
        rows=parse_lineups(parser.paragraphs, {'MIN':'Minnesota Wild'})
        self.assertEqual([r['player_name'] for r in rows],list('ABCDEF'))
        self.assertEqual(rows[-1]['projected_status'],'injured')


if __name__ == '__main__':
    unittest.main()
