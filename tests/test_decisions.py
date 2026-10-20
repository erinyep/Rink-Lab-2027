import unittest
from datetime import datetime, timezone
from src.fantasy.decisions import fit_lineup, category_rules, dominates, acquisition_window_open


class DecisionsTests(unittest.TestCase):
    def test_acquisitions_close_at_first_game_even_for_later_players(self):
        first=datetime(2026,10,17,17,tzinfo=timezone.utc)
        late=datetime(2026,10,17,23,tzinfo=timezone.utc)
        self.assertFalse(acquisition_window_open([first,late],first))
        self.assertTrue(acquisition_window_open([first,late],datetime(2026,10,17,16,tzinfo=timezone.utc)))
        with self.assertRaises(ValueError):
            acquisition_window_open([],first)

    def test_flexible_player_moves_to_preserve_defense_slot(self):
        players=[dict(id=1,eligible=['Defense','Util']),dict(id=2,eligible=['Defense'])]
        result=fit_lineup(players,{'Defense':1,'Util':1})
        self.assertEqual(result,{1:'Util',2:'Defense'})

    def test_locked_player_cannot_move_to_make_room(self):
        players=[dict(id=1,eligible=['Defense','Util'],fixed_slot='Defense'),
                 dict(id=2,eligible=['Defense'])]
        self.assertIsNone(fit_lineup(players,{'Defense':1,'Util':1}))

    def test_one_player_cannot_fill_two_slots(self):
        with self.assertRaises(ValueError):
            fit_lineup([dict(id=1,eligible=['Forward']),dict(id=1,eligible=['Util'])],{'Forward':1,'Util':1})

    def test_unsupported_scoring_fails_instead_of_inventing_points(self):
        with self.assertRaises(ValueError):
            category_rules({'scoringSettings':{'scoringType':'H2H_POINTS'}})
        with self.assertRaises(ValueError):
            category_rules({'scoringSettings':{'scoringType':'H2H_CATEGORY','scoringItems':[{'statId':32}]}})

    def test_category_tradeoff_is_not_called_dominant(self):
        cats=[dict(model_event='shots',lower_is_better=False),dict(model_event='assists',lower_is_better=False)]
        self.assertFalse(dominates({'expected_shots_if_plays':4,'expected_assists_if_plays':.1},
                                   {'expected_shots_if_plays':2,'expected_assists_if_plays':.5},cats))
        self.assertTrue(dominates({'expected_shots_if_plays':4,'expected_assists_if_plays':.5},
                                  {'expected_shots_if_plays':2,'expected_assists_if_plays':.5},cats))


if __name__=='__main__': unittest.main()
