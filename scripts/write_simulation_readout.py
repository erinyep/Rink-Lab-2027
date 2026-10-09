#!/usr/bin/env python3
"""Write a status readout directly from frozen results and simulation manifests."""
import argparse
import json
from pathlib import Path
import pandas as pd
from compare_october_8_models import table


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--simulation',type=Path,required=True)
    args=parser.parse_args()
    m=json.loads((args.simulation/'manifest.json').read_text())
    forecast=Path(m['forecast']); fm=json.loads((forecast/'manifest.json').read_text())
    coverage=pd.read_csv(args.simulation/'game_team_coverage.csv')
    summary=pd.read_csv(args.simulation/'simulation_summary.csv')
    diagnostics=pd.read_csv(args.simulation/'october_8_poisson_diagnostics.csv')
    comparison=Path('data/processed/forecasts/october_8_comparison_20261009T193905Z')
    metrics=pd.read_csv(comparison/'model_metrics.csv')
    core=metrics[(metrics.group=='all_saved_pool')&metrics.model.isin(['baseline','candidate'])&metrics.category.isin(['goals','assists','shots'])]
    report=['# October 9 simulations and exact model status',
        f'\nSimulation artifact created at **{m["created_at_utc"]}**, before first puck drop. '
        f'All **{m["games"]}** October 9 regular-season games are verified against the official schedule. '
        f'{m["simulated_player_games"]} official-roster skater/game entries receive draws for both models; '
        f'{m["missing_history"]} entries without model history remain explicitly listed.',
        '\n## October 8: what the default actually did',
        '\n'+table(core[['model','category','player_games','projected','actual','mae','bias','rmse']]),
        '\nThe default was close on aggregate goals and assists, and overpredicted shots by 21.9. '
        'The candidate reduced shots MAE 1.65% and assists MAE 1.05%, but undershot their totals and '
        'worsened assist bias. Its October 8 predictions were reconstructed afterward from saved pregame '
        'inputs using factors frozen before reading outcomes. This was not a forecast issued pregame.',
        '\n[Readable October 8 player comparison](../../'+str(comparison)+'/player_comparison_readable.csv) · '
        '[Full October 8 readout](october_8_readout.md)',
        '\n## Default and new test model',
        '\nDefault: GP-exposure-weighted history with completed-season recency weights 1, 0.5, 0.25, '
        'the existing provisional current-season update and rookie shrinkage fallback. Candidate: '
        'the same means with SOG×0.92588 and assists×0.96229, fitted only on October 6–7 with 200 '
        'pseudo expected events. Goals stay unchanged and points=G+A. No promotion or refitting occurred.',
        '\nBoth now have a seeded simulation layer: 10,000 draws per skater/game/model, seed 20261009. '
        'SOG is Poisson; goals are binomial conditional on SOG; assists and hits are Poisson; '
        'points=G+A; PPP is binomial conditional on points. Whole-number draws preserve goals≤SOG and '
        'PPP≤points. Assists/hits and players are otherwise independent; opponent, role and team '
        'dependence are not modeled. PIM, plus/minus, TOI and goalie outcomes are not simulated.',
        '\nA 2.7-shot mean stays 2.7. Individual simulated outcomes can be 0, 1, 2, 3 or higher. '
        'Simulation p10/p90 and event probabilities apply **if the player plays** and are provisional '
        'distribution summaries, not calibrated predictive intervals or appearance probabilities.',
        '\n## Every October 9 game and team',
        '\n'+table(coverage),
        '\nOfficial rosters include players who may not dress and injured players. Injury labels remain '
        'visible and missing history remains listed. Game coverage is complete; confirmed lineup and '
        'player forecast coverage are separate questions. No fantasy roster is used as the NHL population.',
        '\n## Distribution diagnostics and what they imply',
        '\n'+table(diagnostics),
        '\nLower negative log likelihood (NLL) and Brier score are better. A positive-mean Pearson '
        'residual second moment around 1 is consistent with Poisson variance; values around 1.15–1.28 '
        'suggest checking extra variability, but mean error also affects this measure. '
        'Infinite full NLL means a zero-mean forecast assigned no probability to a positive observed '
        'count. These cases are counted, not excluded. The positive-mean diagnostics are explicitly '
        'a subset and do not rescue the complete distribution. No dispersion parameter was selected '
        'from October 8.',
        '\n## Stored data and freshness',
        f'\nForecast: `{forecast}`. Schedule cutoff: **{fm["schedule"]["cutoff_utc"]}**. '
        f'ESPN completed: **{fm["espn"]["retrieved_at_utc"]}**. Source timestamps are UTC; game dates are Eastern.',
        '\nAll 65 completed regular-season games September 29–October 8 are archived: 2,340 skater/game '
        'rows, 260 separate goalie/game rows (including backups), PPP reconstructed from official scoring '
        'summaries. All 642 skaters reconcile with season reports across ten categories. One goalie '
        'count exception remains flagged. ESPN ATOI=TTOI seconds/GP, GAA=GA×3600/goalie seconds and '
        'SV%=SV/SA passed for all six teams; minimum goalie starts and historical lineup eligibility '
        'are not established by those ratio checks.',
        '\n## Next steps, in order',
        '\n1. Freeze this October 9 run and evaluate means and distributions after all four games finish. '
        'Compare default/candidate on identical appearances; preserve absent/unmapped rows. Do not '
        'tune factors after outcomes and call October 9 untouched.',
        '2. Prioritize position-prior shrinkage for sparse/zero-count histories in a separately versioned '
        'candidate: zero means produced impossible-count failures. Define and select the prior using '
        'chronological development/validation windows, not the already-observed October 8 night.',
        '3. Extend prior-season game and historical eligible-roster coverage. Evaluate rolling TOI, '
        'current-season update strength and rookie fallbacks using ordered, non-overlapping windows '
        'before fitting participation. Current-season logs are complete, but historical eligibility '
        'cannot be reconstructed from today’s ESPN roster.',
        '4. Compare Poisson with a negative-binomial candidate using validation-selected dispersion; '
        'check probability/interval coverage and log scores by game/date, not independent player rows. '
        'The present quantiles remain provisional until those checks pass.',
        '5. Add goalie starts/rates after count exceptions and league minimum-start rules are resolved; '
        'then calibrated joint scenarios, feasible replacement and lineup decisions. These gates remain '
        'unfinished rather than being marked complete merely because simulations exist.',
        '\n## Reproduce and inspect',
        f'\n```sh\nrink-lab.venv/bin/python scripts/simulate_game_date.py --date {m["date"]} \\\n'
        f'  --forecast {forecast} --draws {m["draws"]} --seed {m["seed"]} \\\n  --raw-snapshot {m["raw_context"]}\n```',
        '\nThe pregame checks intentionally block replay after puck drop; preserve the run and its '
        'manifest for evaluation instead of issuing it again as a new pregame forecast.',
        f'\n[Simulation summaries](../../{args.simulation}/simulation_summary.csv) · '
        f'[Whole-number example draws](../../{args.simulation}/integer_simulation_examples.csv) · '
        f'[All-game coverage](../../{args.simulation}/game_team_coverage.csv) · '
        f'[Unmodeled roster skaters](../../{args.simulation}/players_without_model_history.csv) · '
        f'[Manifest](../../{args.simulation}/manifest.json)',
    ]
    Path('outputs/per_game_forecast/october_9_simulation_readout.md').write_text('\n'.join(report)+'\n')
    print('Readout written; simulation directory:',args.simulation)


if __name__=='__main__': main()
