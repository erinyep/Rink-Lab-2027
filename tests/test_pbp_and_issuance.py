import copy
import unittest
import pandas as pd
from src.fantasy.play_by_play import parse_game, team_measures, lagged_defense_context, lagged_shot_quality
from src.fantasy.issuance import validate_release


class PBPTests(unittest.TestCase):
    def game(self):
        def play(eid,kind,sec,pid,owner,period_type='REG'):
            return dict(eventId=eid,sortOrder=eid,typeDescKey=kind,timeInPeriod=f'00:{sec:02d}',
                periodDescriptor=dict(number=1,periodType=period_type),situationCode='1551',homeTeamDefendingSide='left',
                details=dict(shootingPlayerId=pid,eventOwnerTeamId=owner,xCoord=80,yCoord=0))
        return dict(id=1,gameDate='2026-10-19',gameType=2,gameState='OFF',
            homeTeam=dict(id=10,abbrev='A'),awayTeam=dict(id=20,abbrev='B'),
            rosterSpots=[dict(playerId=1,teamId=10,positionCode='D'),dict(playerId=2,teamId=10,positionCode='C'),
                         dict(playerId=3,teamId=20,positionCode='C')],
            plays=[play(1,'blocked-shot',1,1,20),play(2,'shot-on-goal',5,2,10),
                   play(3,'shot-on-goal',7,3,20),play(4,'shot-on-goal',9,2,10),
                   play(5,'shot-on-goal',10,2,10,'SO')])

    def test_blocked_owner_is_not_shooter_and_sequence_breaks(self):
        e=parse_game(self.game())
        self.assertEqual(len(e),4)
        self.assertEqual(e.iloc[0].team,'A')
        self.assertTrue(e.iloc[0].near_net_attempt)
        self.assertEqual(e.follows_defense_attempt_within10s.tolist(),[False,True,False,False])

    def test_stoppage_resets_and_duplicate_events_fail(self):
        game=self.game(); stop=copy.deepcopy(game['plays'][0])
        stop.update(eventId=11,sortOrder=1.5,typeDescKey='stoppage',timeInPeriod='00:03')
        game['plays'].append(stop)
        self.assertFalse(parse_game(game).follows_defense_attempt_within10s.any())
        game['plays'].append(game['plays'][0])
        with self.assertRaisesRegex(ValueError,'Duplicate event'): parse_game(game)

    def test_lag_and_whole_game_quarantine(self):
        e=parse_game(self.game()); t=team_measures(e)
        future=t.copy(); future['game_id']=2; future['game_date']='2026-10-20'
        good=lagged_defense_context(pd.concat([t,future]),pd.DataFrame([dict(game_id=1,sog_match=True)]),'2026-10-20')
        self.assertTrue(good.games_used.eq(1).all())
        bad=lagged_defense_context(t,pd.DataFrame([dict(game_id=1,sog_match=False)]),'2026-10-20')
        self.assertTrue(bad.games_used.eq(0).all())
        self.assertTrue(bad.quarantined_games.eq(1).all())


class IssuanceTests(unittest.TestCase):
    def sample(self):
        m=dict(created_at_utc='2026-10-20T12:00Z',injuries_as_of_utc='2026-10-20T11:00Z',config=dict(models=['default','candidate']))
        games=[dict(id=1,gameState='FUT',startTimeUTC='2026-10-20T23:00Z',homeTeam=dict(abbrev='A'),awayTeam=dict(abbrev='B'))]
        players=pd.DataFrame([dict(game_id=1,team=t,player_id=i,category='shots',model=model,actual=float('nan'),
            model_projection_if_plays=2.,issue_timing='pregame') for i,t in enumerate(['A','B']) for model in ['default','candidate']])
        players=pd.concat([players.assign(category=c) for c in ['goals','assists','shots','hits','points','pp_points','penalty_minutes','plus_minus','toi_minutes']],ignore_index=True)
        teams=players[players.category.isin(['goals','assists','shots','hits','points','pp_points'])].rename(columns={'model_projection_if_plays':'projection_mean'}).drop(columns='player_id')
        goalies=pd.DataFrame([dict(game_id=1,team=t,player_id=i,model=model,issue_timing='pregame',
            shots_against_if_full_start=30.,saves_if_full_start=27.,goals_against_if_full_start=3.)
            for i,t in enumerate(['A','B']) for model in ['g1','g2']])
        context=pd.DataFrame(dict(moneypuck_missing_nhl_games=[0,0]))
        return [m,games,players,teams,goalies,context,pd.Timestamp('2026-10-20T13:00Z')]

    def test_accepts_complete_fresh_release(self):
        self.assertEqual(validate_release(*self.sample())['games'],1)

    def test_stale_late_missing_models_and_outcomes_fail(self):
        args=self.sample(); args[0]['injuries_as_of_utc']='2026-10-19T01:00Z'
        with self.assertRaisesRegex(ValueError,'Stale'): validate_release(*args)
        args=self.sample(); args[-1]=pd.Timestamp('2026-10-20T22:55Z'); args[0]['injuries_as_of_utc']='2026-10-20T22:00Z'
        with self.assertRaisesRegex(ValueError,'lead time'): validate_release(*args)
        args=self.sample(); args[2]=args[2].iloc[:-1]
        with self.assertRaisesRegex(ValueError,'Incomplete model'): validate_release(*args)
        args=self.sample(); args[2].loc[0,'actual']=0
        with self.assertRaisesRegex(ValueError,'Outcomes'): validate_release(*args)

    def test_lag_requires_explicit_exception(self):
        args=self.sample(); args[5].loc[0,'moneypuck_missing_nhl_games']=1
        with self.assertRaisesRegex(ValueError,'coverage lags'): validate_release(*args)
        validate_release(*args,allow_context_lag=True)

    def test_missing_entire_category_is_rejected(self):
        args=self.sample(); args[2]=args[2][args[2].category.ne('hits')]
        with self.assertRaisesRegex(ValueError,'Incomplete player categories'): validate_release(*args)

    def test_public_mode_requires_unknown_injuries(self):
        args=self.sample(); args[0].update(availability_status='disabled_public_data_only',injuries_as_of_utc=None)
        args[2]['injury_status']='UNKNOWN'; args[4]['injury_status']='UNKNOWN'
        validate_release(*args)
        args[4].loc[0,'injury_status']='ACTIVE'
        with self.assertRaisesRegex(ValueError,'unknown injuries'): validate_release(*args)


class ShotQualityTests(unittest.TestCase):
    def test_quality_excludes_target_day_and_quarantined_sources(self):
        rows=[dict(game_id=i,team='A',strength='all',game_date=day,source_quarantined=bad,
            defense_xg=x,defense_expected_rebounds=x,defense_unblocked_attempts=5,team_xg=2)
            for i,day,bad,x in [(1,'2026-10-18',False,.4),(2,'2026-10-19',True,99),(3,'2026-10-20',False,99)]]
        r=lagged_shot_quality(pd.DataFrame(rows),'2026-10-20').iloc[0]
        self.assertEqual(r.games_used,1)
        self.assertEqual(r.quarantined_games,1)
        self.assertEqual(r.defense_xg_per_game,.4)


if __name__=='__main__': unittest.main()
