"""Publish the October 27 results and October 28 model decision without altering forecasts."""
from pathlib import Path
import json
import shutil
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from scripts.publish_results_update import page
from scripts.evaluate_daily_forecasts import verify_manifest_files, digest


def main():
    results = Path('outputs/per_game_forecast/results_2026-10-27')
    screen = Path('outputs/per_game_forecast/shots_participation_through_2026-10-27')
    for folder in [results, screen]:
        verify_manifest_files(folder, [])
    old = Path('docs/results/index.html')
    archive = Path('docs/results/through-2026-10-25.html')
    if not archive.exists():
        shutil.copy2(old, archive)
    for source, target in [(results, Path('docs/results/october-27')), (screen, Path('docs/history/shots-participation'))]:
        target.mkdir(parents=True, exist_ok=True)
        # Full candidate audit remains in the repository; avoid duplicating it in the site.
        for p in source.iterdir():
            if p.name != 'participation_player_audit.csv':
                shutil.copy2(p, target/p.name)
        if (source/'participation_player_audit.csv').exists():
            readme = target/'README.md'
            readme.write_text(readme.read_text().replace('(participation_player_audit.csv)', '(https://github.com/erinyep/Rink-Lab-2027/blob/main/'+str(source)+'/participation_player_audit.csv)'))
        manifest = json.loads((source/'manifest.json').read_text())
        manifest['publication_source_manifest_sha256'] = digest(source/'manifest.json')
        manifest['publication_scope'] = 'Compact site export; full candidate audit retained in repository source directory.'
        manifest['files'] = {p.name:digest(p) for p in target.iterdir() if p.is_file() and p.name not in ['manifest.json','index.html']}
        (target/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    repo = 'https://github.com/erinyep/Rink-Lab-2027'
    nav = '<p><a href="../../">Home</a> · <a href="../../results/">October 27 results</a> · <a href="../">Model history</a></p>'
    body = nav + '<p>59 games across six saved dates; 2,121 skater appearances and 423 fantasy appearances. All forecasts re-scored against one actuals vintage.</p><p><strong>Decision: keep the current fantasy shots and lineup defaults, and retain the improved fantasy ice-time model.</strong></p>'
    body += '<h2>Shots</h2><p>Calibrated shots improve overall error. The fantasy improvement remains uncertain; its paired 95% interval crosses zero. Lower MAE is better.</p>'
    z = pd.read_csv(screen/'shots_metrics.csv')
    body += '<main>'+z[['population','model','rows_scored','mae','bias']].round(4).to_html(index=False)+'</main>'
    body += '<h2>Participation</h2><p>Five-game appearance frequency worsened projected nonparticipants from 114 to 144. Using it only as a tiebreaker produced 116. Neither replaces the existing rule. These are retrospective, past-only tests, not issued forecasts.</p>'
    z = pd.read_csv(screen/'participation_metrics.csv')
    body += '<main>'+z.round(4).to_html(index=False)+'</main>'
    body += '<p>Goal overprediction was +0.156 per team pooled versus +0.641 on October 27. Three earlier dates had negative bias; no blanket correction is justified.</p>'
    body += f'<p><a href="{repo}/blob/main/docs/history/shots-participation-decision-2026-10-28.md">Full decision, limitations and reproduction</a> · <a href="{repo}/tree/main/{screen}">All evidence and candidate audit</a></p>'
    for name in ['shots_game_uncertainty','shots_date_uncertainty','shots_leave_one_date_out','participation_by_date','participation_game_uncertainty','participation_team_games']:
        body += f'<p><a href="{name}.csv">{name.replace("_", " ")}</a></p>'
    Path('docs/history/shots-participation/index.html').write_text(page('Shots and participation — October 28 review', body))
    body = '<p><a href="../">Home</a> · <a href="../history/shots-participation/">Expanded model decision</a> · <a href="through-2026-10-25.html">Earlier October 24–25 results</a></p><p>All 11 October 27 games scored against frozen pregame forecasts. No refitting. All 396 actual skater appearances covered.</p><h2>Team models</h2><p>The new model reduced goal error but picked 3/11 winners versus 4/11 for the original. Both probability models scored worse than a 50/50 forecast. Brier and goal MAE: lower is better.</p>'
    body += '<main>'+pd.read_csv(results/'team_metrics.csv').round(4).to_html(index=False, na_rep='—')+'</main>'
    body += '<p>New-minus-original Brier interval: −0.0484 to +0.0338. One slate does not establish superiority. Goal counts exclude the shootout bonus; winner scoring includes shootouts. Original probabilities use the existing Poisson transform of saved goal means.</p><h2>Game-by-game</h2><main>'
    body += pd.read_csv(results/'team_games.csv').round(4).to_html(index=False)+'</main>'
    body += '<h2>Fantasy and goalies</h2><p>Fantasy ice-time MAE improved 2.232 → 2.064 minutes across 76 rostered skaters; Quinn’s 15 observed skaters improved 2.167 → 2.045. Goalie saves error slightly worsened with opponent context: 5.219 versus 5.169 for baseline. Twenty-one selected lineup players did not appear.</p>'
    body += f'<p><a href="{repo}/blob/main/{results}/README.md">Detailed results and methods</a></p>'
    for name in ['team_games','fantasy_player_metrics','goalie_metrics','fantasy_toi_comparison','coverage']:
        body += f'<p><a href="october-27/{name}.csv">{name.replace("_", " ")}</a></p>'
    old.write_text(page('October 27 results — reviewed October 28', body))
    history = Path('docs/history/index.html')
    archive = Path('docs/history/updates-2026-10-27.html')
    if not archive.exists(): shutil.copy2(history,archive)
    history.write_text(page('Model evidence — October 28', '<p><a href="../">Home</a> · <a href="../results/">Latest results</a></p><p><a href="shots-participation/">Expanded shots and participation comparison: 59 games</a></p><p>Current decision: retain production defaults and fantasy ice-time update. Neither recent-participation rule improved lineup selection.</p><p><a href="updates-2026-10-27.html">October 27 model changes and training evidence</a></p>'))
    Path('docs/index.html').write_text(page('Rink Lab — October 28, 2026', '<p><a href="results/">1. October 27 results — how the models performed</a></p><p><a href="history/shots-participation/">2. Expanded shots and lineup tests — 59 games</a></p><p><a href="history/">3. Model decisions and history</a></p><p>Latest update reviews completed games. No October 28 forecasts have been issued in this update.</p><h2>Saved October 27 pregame forecasts</h2><p><a href="team-model/">Team goals and probabilities</a> · <a href="report/">Fantasy report</a> · <a href="games/">Player-sum goals, shots and goalie scenarios</a></p>'))


if __name__ == '__main__': main()
