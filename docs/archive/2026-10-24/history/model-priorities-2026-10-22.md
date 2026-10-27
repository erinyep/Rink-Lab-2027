# Model decisions before October 22 games

There are worthwhile improvements to test. Current performance does not support
one replacement model across every population and category. Tonight's issued
forecasts remain frozen so their evaluation stays prospective.

| Priority | Evidence so far | Next test |
| --- | --- | --- |
| Goalie starter and duration modeling | October 20 saves p10–p90 ranges covered only 59.1% of 22 starts, versus nominal 80%; full-start counts face variable game duration. | Model start/relief and minutes separately; assess dispersion and interval coverage on future games, with an unchanged baseline. Do not multiply intervals by a hand-picked correction from one slate. |
| Calibrated opponent SOG challenger | Across 24 pregame games/864 appearances, MAE 1.0416 versus default 1.0583; lower game error in 20/24. | Continue as the main all-player SOG challenger. Keep dates and fantasy populations separate; three dates do not establish durable performance. |
| Fantasy-specific validation | On 179 saved fantasy appearances, default MAE 1.3499, opponent-only 1.3477, calibrated opponent 1.3609. | Retain default in the fantasy report; compare opponent-only on further frozen slates. A 0.0023-shot point-estimate advantage is insufficient evidence to switch. |
| Defense and shot quality | On the only completed prospective slate (11 games), D-only improves its own team-SOG control 5.792→5.344; its paired interval includes no improvement. The main opponent model is better at 4.775. | Continue all four separate experiments on October 22 with the frozen October 20 coefficients. Do not add a D bonus to individual means. |
| Opportunity and recent-rate updates | October 20 ordered component accounting: TOI improves player SOG MAE about 0.005; recent shot-rate adjustment worsens it about 0.012. | Test past-only role/TOI and rate shrinkage separately, using chronological training and untouched future evaluation. Ordered reconstructions are not independent causal effects. |

These are development priorities, not changes to tonight's fitted models. Avoid
promoting all-player shot improvements to goals, assists, goalie performance or
fantasy decisions without category-specific evidence.

[Expanded evidence and paired uncertainty](../archive/2026-10-20/history/multi_date.md)
· [October 20 protocol results](../results/README.md)
· [Current count-error scoreboard](scoreboard_2026-10-22/model_scoreboard.csv)
· [Tonight's frozen feature trials](../evidence/README.md).
