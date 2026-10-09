#!/usr/bin/env python3
"""Pregame team-total scenarios from a documented, unconfirmed lineup heuristic."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np
import pandas as pd
from src.fantasy.per_game import require
from src.fantasy.simulation import simulate_counts


def select_lineup(players):
    """Trial 12F/6D scenario: last appearance first, then baseline predicted TOI.

Do not infer actual scratches from this heuristic. Retain all selection reasons.
    """
    result=players.copy()
    blocked={'OUT','INJURY_RESERVE','SUSPENSION','IR'}
    result['eligible_for_trial']=~result.injury_status.fillna('UNKNOWN').isin(blocked) & result.has_forecast
    result['selected_for_trial']=False
    result['selection_reason']=np.where(result.has_forecast,'outside_trial_lineup','missing_model_history')
    result.loc[result.injury_status.isin(blocked),'selection_reason']='excluded_by_saved_injury_label'
    for position,slots in [('F',12),('D',6)]:
        candidates=result[result.eligible_for_trial & (result.position_group==position)]
        ordered=candidates.sort_values(['played_last_team_game','toi_minutes_per_game','player_id'],ascending=[False,False,True])
        selected=ordered.head(slots)
        require(len(selected)==slots,f'Insufficient {position} coverage for an 18-skater scenario')
        result.loc[selected.index,'selected_for_trial']=True
        result.loc[selected.index,'selection_reason']=np.where(selected.played_last_team_game,
            'last_game_appearance_in_trial','replacement_by_predicted_toi')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--simulation',type=Path,required=True)
    parser.add_argument('--game-stats',type=Path,required=True)
    args=parser.parse_args()
    manifest=json.loads((args.simulation/'manifest.json').read_text())
    for filename,expected in manifest['files'].items():
        require(hashlib.sha256((args.simulation/filename).read_bytes()).hexdigest()==expected,'Simulation hash mismatch')
    forecast=Path(manifest['forecast']); raw=Path(manifest['raw_context'])
    rates=pd.read_csv(forecast/'current_per_game_forecast.csv').set_index('player_id')
    summary=pd.read_csv(args.simulation/'simulation_summary.csv')
    require(datetime.now(timezone.utc)<pd.to_datetime(summary.start_time_utc,utc=True).min().to_pydatetime(),
            'Trial must be frozen before first puck drop')
    history=pd.read_csv(args.game_stats)
    require((history.game_date<manifest['date']).all(),'Lineup history includes target/future outcomes')
    coverage=pd.read_csv(args.simulation/'game_team_coverage.csv')
    audits=[]; team_rows=[]; probabilities=[]
    for _,context in coverage.iterrows():
        roster=json.loads((raw/f'roster_{context.team}.json').read_text())
        team_history=history[(history.team==context.team)&(history.toi_seconds>0)]
        require(not team_history.empty,'No prior team lineup')
        previous=team_history.sort_values(['game_date','game_id']).iloc[-1]
        previous_ids=set(team_history[team_history.game_id==previous.game_id].player_id)
        players=[]
        team_summary=summary[(summary.team==context.team)&(summary.model=='default')].drop_duplicates('player_id').set_index('player_id')
        for group,roster_players in [('F',roster['forwards']),('D',roster['defensemen'])]:
            for player in roster_players:
                pid=player['id']; has=pid in rates.index
                players.append(dict(game_id=context.game_id,team=context.team,opponent=context.opponent,player_id=pid,
                    player_name=player['firstName']['default']+' '+player['lastName']['default'],position_group=group,
                    has_forecast=has,injury_status=team_summary.loc[pid,'injury_status'] if pid in team_summary.index else 'UNKNOWN',
                    played_last_team_game=pid in previous_ids,previous_game_id=previous.game_id,
                    toi_minutes_per_game=float(rates.loc[pid,'toi_minutes_per_game']) if has else np.nan))
        lineup=select_lineup(pd.DataFrame(players)); audits.append(lineup)
        selected=lineup[lineup.selected_for_trial]
        for model in ['default','candidate']:
            totals={event:np.zeros(manifest['draws'],dtype=np.int64) for event in ['goals','assists','shots','hits','points','pp_points']}
            means={event:0. for event in totals}
            for pid in selected.player_id:
                row=summary[(summary.game_id==context.game_id)&(summary.player_id==pid)&(summary.model==model)]
                player_means=row.set_index('category').mean_if_plays.to_dict()
                samples=simulate_counts(player_means,draws=manifest['draws'],seed=manifest['seed'],key=f'{context.game_id}:{pid}')
                for event in totals:
                    totals[event]+=samples[event]; means[event]+=player_means[event]
            for event,values in totals.items():
                counts=np.bincount(values)
                # Each marginal sum is Poisson under the trial assumptions.
                # Use its analytical mode, not a noisy Monte Carlo histogram maximum.
                # Integer means have two modes; choose the lower one (except zero).
                mode=max(0,int(np.ceil(means[event]))-1)
                team_rows.append(dict(game_id=context.game_id,team=context.team,opponent=context.opponent,model=model,
                    category=event,projection_mean=means[event],whole_number_guess=mode,
                    probability_of_guess=float(counts[mode]/len(values)),
                    simulation_p10=int(np.quantile(values,.1,method='inverted_cdf')),
                    simulation_p90=int(np.quantile(values,.9,method='inverted_cdf')),
                    assumed_skaters=18,actual=np.nan,absolute_error=np.nan,exact_guess_correct=pd.NA,
                    lineup_status='unconfirmed_12F_6D_trial',distribution_status='provisional_not_calibrated'))
                for total,count in enumerate(counts):
                    probabilities.append(dict(game_id=context.game_id,team=context.team,model=model,category=event,
                        exact_total=total,probability=float(count/len(values))))
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out=Path('data/processed/forecasts')/f'team_trial_{manifest["date"]}_{stamp}'
    out.mkdir(parents=True,exist_ok=False)
    pd.DataFrame(team_rows).to_csv(out/'team_projected_vs_actual.csv',index=False)
    pd.DataFrame(probabilities).to_csv(out/'team_exact_total_probabilities.csv',index=False)
    pd.concat(audits,ignore_index=True).to_csv(out/'trial_lineup_audit.csv',index=False)
    require(datetime.now(timezone.utc)<pd.to_datetime(summary.start_time_utc,utc=True).min().to_pydatetime(),'Run finished after first puck drop')
    (out/'manifest.json').write_text(json.dumps(dict(created_at_utc=datetime.now(timezone.utc).isoformat(),
        simulation=str(args.simulation),game_history=str(args.game_stats),games=int(coverage.game_id.nunique()),
        seed=manifest['seed'],draws=manifest['draws'],
        lineup_rule='12F/6D; eligible last-game appearances first, then predicted baseline TOI; exclude saved OUT/IR/SUSPENSION labels; DTD/UNKNOWN retained.',
        limitations=['Lineup is an unconfirmed scenario, not fitted participation or announced lineup.',
                     'No opponent/team dependence; PPP/assists are not constrained to team goal accounting.',
                     'Goal totals exclude shootout deciding goals; compare against non-shootout player goals.',
                     'No goalie scoring contribution; exact-total frequencies are Monte Carlo estimates.'],
        game_history_sha256=hashlib.sha256(args.game_stats.read_bytes()).hexdigest(),
        simulation_manifest_sha256=hashlib.sha256((args.simulation/'manifest.json').read_bytes()).hexdigest(),
        files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.csv')}),indent=2)+'\n')
    print('Team trial output:',out)
    print(pd.DataFrame(team_rows).query("model=='default' and category in ['goals','hits']")[[
        'team','opponent','category','projection_mean','whole_number_guess','probability_of_guess']].to_string(index=False))


if __name__=='__main__': main()
