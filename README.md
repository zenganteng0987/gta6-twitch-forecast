[![make.fun · gta6-twitch-ccu-forecast-01](https://make.fun/badge/gta6-twitch-ccu-forecast-01.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![rank](https://make.fun/badge/gta6-twitch-ccu-forecast-01/zenganteng0987/gta6-twitch-forecast/rank.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![reward](https://make.fun/badge/gta6-twitch-ccu-forecast-01/zenganteng0987/gta6-twitch-forecast/reward.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)

# Launch Curve — a GTA VI launch-day Twitch forecast

A program that forecasts how many people will watch Grand Theft Auto VI live on Twitch in
each hour of its release day (2026-11-19, UTC), after the first: for hours 2 to 24 it writes
five quantiles (5%, 25%, 50%, 75%, 95%) of that hour's concurrent viewers in the category.

## How it works

A big game's release-day Twitch curve has a shape, and the shape depends most on how big
the launch is. Every case the program is run on carries dozens of past launches with their
full hourly counts (`comparables`). For each past launch the program takes its release-day
hours as log ratios to its own hour 1, weights that launch by how close its hour-1 size is
to this case's hour-1 print — weight `exp(-|ln p1 − ln p1c|)`, one e-fold of size
difference costs one e-fold of weight — and reads the case's five quantiles for each hour
straight off the weighted empirical distribution of those ratios.

No parameters were tuned on any answer: the quantiles are the pooled launches' own, and
the case game's own category history (a premiere spike, not a launch) never votes.

## Backtest

Leave-one-out over the 37 usable comparables of a practice case — each launch forecast
from the others, scored with the contest's pinball loss on the log scale:

| pool | this program | persistence baseline |
| --- | --- | --- |
| all 37 launches | **0.422** | 0.930 |
| hour 1 ≥ 100,000 viewers (16 launches) | **0.216** | 0.261 |

## Running it

```
mkdir -p out
MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Standard library only, no network, deterministic: two runs write byte-identical files.
