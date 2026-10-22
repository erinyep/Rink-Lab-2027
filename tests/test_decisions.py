import unittest
from datetime import datetime, timezone
from src.fantasy.decisions import fit_lineup, category_rules, dominates, acquisition_window_open, category_comparison, goalie_qualification


class DecisionsTests(unittest.TestCase):
    def test_matchup_start_minimum_is_not_active_slot_capacity(self):
        def goalie(name, team, slot='Goalie', **kw):
            return dict(player_name=name,schedule_team=team,lineup_slot=slot,is_goalie=True,
                        has_game=True,blocked=False,locked=False,**kw)
        roster=[goalie('Garand','NYR'),goalie('Wallstedt','MIN'),goalie('Saros','NSH','Bench')]
        result=goalie_qualification(2,3,2,roster)
        self.assertEqual(result['needed'],1)
        self.assertEqual([r['total'] for r in result['scenarios']],[2,3,4])
        self.assertEqual([r['minimum_met'] for r in result['scenarios']],[False,True,True])
        self.assertEqual(result['bench_names'],['Saros'])
        roster[1]['blocked']=True
        self.assertEqual(len(goalie_qualification(2,3,2,roster)['scenarios']),2)
        roster[0]['locked']=True
        self.assertEqual(len(goalie_qualification(2,3,2,roster)['scenarios']),1)

    def test_goalie_scenarios_respect_same_team_and_missing_scores(self):
        roster=[dict(player_name=str(i),schedule_team='NYR',lineup_slot='Goalie',is_goalie=True,
                     has_game=True,blocked=False,locked=False) for i in range(2)]
        self.assertEqual(len(goalie_qualification(3,3,2,roster)['scenarios']),2)
        self.assertEqual(goalie_qualification(3,3,2,roster)['needed'],0)
        self.assertEqual(goalie_qualification(float('nan'),3,2,roster)['scenarios'],[])

    def test_uninitialized_goalie_rate_is_not_an_invented_advantage(self):
        row=category_comparison('GAA',2.4,float('inf'),True)
        self.assertIsNone(row['opponent'])
        self.assertIsNone(row['advantage'])
        self.assertEqual(row['status'],'unavailable')
        self.assertEqual(category_comparison('GAA',2.4,3.1,True)['status'],'ahead')

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
