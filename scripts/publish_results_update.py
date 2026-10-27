#!/usr/bin/env python3
"""Publish a dated results update without changing original forecast artifacts."""
import argparse
from datetime import datetime,timezone
from html import escape
import json
from pathlib import Path
import shutil
import sys
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.evaluate_daily_forecasts import verify_manifest_files,digest
from scripts.evaluate_october_9 import table


def page(title,body):
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)}</title><style>body{{font:16px system-ui;color:#172c38;max-width:1100px;margin:32px auto;padding:20px;line-height:1.5}}a{{color:#08777c}}table{{border-collapse:collapse}}td,th{{padding:8px;text-align:left;border-bottom:1px solid #ddd}}main{{overflow:auto}}img{{max-width:100%}}</style></head><body><h1>{escape(title)}</h1>{body}</body></html>'''


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for key in ['review','decisions','broader','scoreboard','probability-results','out']:
        ap.add_argument('--'+key,type=Path,required=True)
    ap.add_argument('--from-date',required=True)
    ap.add_argument('--archive-date',required=True)
    ap.add_argument('--saved-fantasy-report',type=Path)
    a=ap.parse_args()
    if a.out.exists():raise ValueError('Preserve previous result reports')
    sources={k:verify_manifest_files(getattr(a,k),[]) for k in ['review','decisions','broader','scoreboard','probability_results']}
    rm=sources['review'];through=rm['through']
    for key in ['decisions','broader','scoreboard']:
        if sources[key]['review_sha256']!=digest(a.review/'manifest.json'):raise ValueError('Mixed review vintages')
    source_boxes=Path(rm['boxscores']);games=[]
    coverage=pd.read_csv(a.review/'game_coverage.csv').set_index('game_id')
    for s in json.loads((source_boxes/'metadata.json').read_text())['sources']:
        if not s['file'].startswith('boxscore_'):continue
        path=source_boxes/s['file']
        if digest(path)!=s['sha256']:raise ValueError('Changed official game')
        b=json.loads(path.read_text())
        if not a.from_date<=b['gameDate']<=through:continue
        games.append(dict(game_id=b['id'],date=b['gameDate'],away=b['awayTeam']['abbrev'],home=b['homeTeam']['abbrev'],
            away_score=b['awayTeam']['score'],home_score=b['homeTeam']['score'],
            final_period_type=b['periodDescriptor']['periodType'],saved_daily_forecast=bool(coverage.loc[b['id'],'daily_trial'])))
    games=pd.DataFrame(games).sort_values(['date','game_id'])
    a.out.mkdir(parents=True);games.to_csv(a.out/'game_results.csv',index=False)
    latest=None
    for folder in rm['evaluations']:
        root=Path(folder);em=verify_manifest_files(root,[])
        if a.from_date<=em['date']<=through:
            if em['actuals_manifest_sha256']!=rm['actuals_sha256']:raise ValueError('Mixed actuals')
            # Publish compact reading views; keep the large simulation rows local.
            target=a.out/('daily_'+em['date']);target.mkdir()
            for name in em['files']:
                if name not in ['simulation_summary.csv','source_hash_audit.csv']:
                    shutil.copy2(root/name,target/name)
            exported=dict(em,publication_scope='reading views; full simulation rows retained locally',
                          source_evaluation_manifest_sha256=digest(root/'manifest.json'),
                          files={p.name:digest(p) for p in target.iterdir() if p.is_file()})
            (target/'manifest.json').write_text(json.dumps(exported,indent=2)+'\n')
            if latest is None or em['date']>latest[0]:latest=(em['date'],root)
    if latest is None:raise ValueError('No issued daily models in requested results window')
    when,ev=latest
    if a.saved_fantasy_report:
        report=json.loads(a.saved_fantasy_report.read_text())
        if report['date']!=when:raise ValueError('Roster report date mismatch')
        roster=pd.DataFrame(report['roster']);roster=roster[~roster.is_goalie & roster.has_game].copy()
        roster=roster[['nhl_player_id','lineup_slot','is_current_active']].rename(columns={'nhl_player_id':'player_id'})
        p=pd.read_csv(ev/'player_projections.csv');p=p[p.model.eq('default')]
        saved=p.merge(roster,on='player_id',validate='many_to_one')
        saved.to_csv(a.out/'saved_fantasy_skaters.csv',index=False)
    metrics=pd.read_csv(a.review/'model_metrics.csv')
    shots=metrics[metrics.category.eq('shots')][['level','model','rows','games','mae']]
    probabilities=pd.read_csv(a.probability_results/'metrics.csv')
    pairs=pd.read_csv(a.decisions/'paired_uncertainty.csv');pairs=pairs[pairs.population.eq('saved_fantasy_roster')&pairs.category.eq('shots')]
    missing=pd.read_csv(ev/'unmodeled_actual_skaters.csv')
    headline=f'{len(games)} finals in this update; {games.saved_daily_forecast.sum()} have saved daily-model forecasts. '
    headline+=f'Season history contains {len(coverage)} finals. Full model comparisons cover {int(shots.games.max())} games.'
    links=' · '.join(f'<a href="../history/{getattr(a,k).name}/README.md">{label}</a>' for k,label in [('decisions','Fantasy/role uncertainty'),('broader','xG, defense and injuries'),('scoreboard','Rolling scoreboard'),('probability_results','Probability vs Kalshi results')])
    body=f'<p>{headline}</p><p>{links}</p><h2>October 24–25 finals</h2><main>{games.to_html(index=False)}</main>'
    body+='<p>Games without a saved forecast are observed results and coverage gaps, not reconstructed forecast tests.</p>'
    body+='<h2>All saved daily-model shots errors</h2><main>'+shots.round(4).to_html(index=False)+'</main>'
    body+='<h2>First prospective probability slate</h2><main>'+probabilities.round(4).to_html(index=False)+'</main><p>One home outcome per game. Saved pregame quotes, no market blend. NHL-outcome scores, not exchange settlement or trading returns. Twelve games do not establish durable superiority.</p>'
    body+='<h2>Fantasy shots: paired changes versus default</h2><main>'+pairs.round(4).to_html(index=False)+'</main><p>Intervals are exploratory game bootstraps; no automatic model promotion.</p>'
    body+=f'<h2>Latest forecast coverage</h2><p>{len(missing)} actual skaters lacked a saved forecast; their outcomes are retained in the coverage audit.</p><main>{missing.to_html(index=False)}</main>'
    body+='<h2>Detailed files</h2><p><a href="game_results.csv">All final scores CSV</a> · <a href="README.md">Methods and limitations</a></p>'
    for filename in ['player_projections','team_projections','goalie_projections','fantasy_player_metrics','game_team_coverage']:
        body+=f'<p><a href="daily_{when}/{filename}.csv">{when} {filename.replace("_"," ")}</a></p>'
    if a.saved_fantasy_report:body+='<p><a href="saved_fantasy_skaters.csv">Your saved October 24 skater projections versus actuals</a>. Active/bench labels come from the saved pregame roster, not verified final ESPN lineup decisions.</p>'
    (a.out/'index.html').write_text(page('Results through '+through,body))
    (a.out/'README.md').write_text(f'''# Results through {through}

{headline}

[Interactive results](index.html) · [Every final score](game_results.csv).

{table(games)}

Frozen forecasts are preserved. Official scoring excludes shootout deciding goals from player/team scoring counts;
final game winners include overtime and shootouts. No forecast is reconstructed for uncovered dates.
Every daily evaluation uses the same actuals vintage as the season review. Missing participants are not scored as
zero conditional production. Fantasy roster labels reflect the saved issue, not current ownership.

## Probability benchmark

{table(probabilities)}

One binary home outcome per game; the complementary away contract is not another sample.
These are official NHL-outcome probability scores, not exchange settlement verification or P&L.
No model promotion from one slate. The broader historical probability screen remains separate.

## Fantasy shots uncertainty

{table(pairs)}

## Missing forecasts on {when}

{table(missing)}

The saved fantasy skater CSV, when supplied, uses original active/bench labels and is not an audit of final ESPN lineup changes.
''')
    manifest=dict(created_at_utc=datetime.now(timezone.utc).isoformat(),through=through,from_date=a.from_date,
        sources={k:dict(path=str(getattr(a,k)),manifest_sha256=digest(getattr(a,k)/'manifest.json')) for k in sources},
        saved_fantasy_report_sha256=digest(a.saved_fantasy_report) if a.saved_fantasy_report else None,
        files={str(p.relative_to(a.out)):digest(p) for p in a.out.rglob('*') if p.is_file()})
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    archive=Path('docs/archive')/a.archive_date
    if archive.exists():raise ValueError('Archive date already exists; do not overwrite')
    archive.mkdir(parents=True)
    for name in ['games','report','history','evidence','results']:shutil.copytree(Path('docs')/name,archive/name)
    shutil.copy2('docs/index.html',archive/'index.html')
    for key in sources:shutil.copytree(getattr(a,key),Path('docs/history')/getattr(a,key).name)
    shutil.copytree(a.out,'docs/results',dirs_exist_ok=True)
    (Path('docs/history')/'index.html').write_text(page('Model history through '+through,
        '<p>'+headline+'</p><p><a href="../results/">October 24–25 results and detailed evaluations</a></p><p>'+links.replace('../history/','')+'</p><main>'+shots.round(4).to_html(index=False)+'</main>'))
    Path('docs/index.html').write_text(page('Rink Lab — results through '+through,
        '<p>'+headline+'</p><p><a href="results/">Start here: October 24–25 results</a></p><p><a href="history/">Model history, fantasy uncertainty, defense/xG and injuries</a></p>'
        f'<p><a href="history/{a.probability_results.name}/README.md">First prospective model-versus-Kalshi comparison</a></p>'
        '<p><a href="games/">Saved October 24 game forecasts</a> · <a href="report/">Saved October 24 fantasy report</a> · <a href="evidence/">Saved defense feature trials</a></p><p>These forecast pages are historical snapshots, not current lineups or a new pregame release.</p>'))
    # Publish a dated notice without changing the frozen data behind earlier views.
    notice=f'<aside style="padding:16px;background:#fff3cf"><strong>Historical October 24 snapshot.</strong> <a href="../results/">Results through {through} are now available</a>. This is not a current pregame report.</aside>'
    for name in ['games','report','evidence']:
        folder=Path('docs')/name;index=folder/'index.html';s=index.read_text()
        pos=s.find('<h1')
        if pos<0:raise ValueError('Missing report heading')
        index.write_text(s[:pos]+notice+s[pos:])
        manifest_path=folder/'manifest.json';view=json.loads(manifest_path.read_text())
        view['results_notice_through']=through
        for filename in view['files']:view['files'][filename]=digest(folder/filename)
        manifest_path.write_text(json.dumps(view,indent=2)+'\n')
    print('Results published locally:',a.out)


if __name__=='__main__':main()
