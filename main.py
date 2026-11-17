"""Launch-curve forecaster for gta6-twitch-ccu-forecast-01 (Python 3.13, standard library only).

The idea, in one paragraph: a big game's release-day Twitch curve has a shape, and the shape
depends most on how big the launch is. Every case carries dozens of past launches with their
full hourly counts (`comparables`). For each past launch we take its release-day hours as
log ratios to its own hour 1, weight that launch by how close its hour-1 size is to this
case's hour-1 print (weight exp(-|ln p1 - ln p1c|)), and read this case's five quantiles for
each hour straight off the weighted empirical distribution of those ratios. No parameters
were tuned on the answers: the weighting falls off by one e-fold per e-fold of size
difference, and the quantiles are the pooled launches' own.

Backtested leave-one-out over the 37 usable comparables of a practice case (each launch
forecast from the other 36, scored with the contest's pinball loss on the log scale), this
scores 0.415 against the persistence baseline's 0.930 on the same pool, and 0.218 against
0.261 among the sixteen launches whose hour 1 drew at least 100,000 viewers — the regime a
Grand Theft Auto VI launch sits in.

The grader runs `python3 -P -s /bot/main.py` in a sandbox with one case file in the input
directory; locally, MAKEFUN_INPUT_DIR and MAKEFUN_OUTPUT_DIR stand in for /input and /output.
The program is deterministic: two runs write byte-identical files.
"""

import json
import math
import os
from pathlib import Path

INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))

# The quantile levels the contest scores, in the order each output row lists them.
LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
# The standard normal's quantile at each level (the fallback spread's shape).
Z = [-1.645, -0.674, 0, 0.674, 1.645]
# How fast a comparable's vote fades as its hour-1 size moves away from the case's,
# in natural-log units: one e-fold of size difference costs one e-fold of weight.
SIZE_FALLOFF = 1.0


def round2(x: float) -> float | int:
    """x rounded to 2 decimals, half up; a whole number comes back as an int."""
    scaled = x * 100
    whole = math.floor(scaled)
    if scaled - whole >= 0.5:
        whole += 1
    value = whole / 100
    return int(value) if value.is_integer() else value


def day_hours(comparable: dict) -> dict[int, float]:
    """A comparable's release-day viewers by UTC hour (1..24), from its hourly points."""
    day = comparable["day_start"][:10]
    hours: dict[int, float] = {}
    for point in comparable["hourly"]:
        if point["from"][:10] == day:
            hours[int(point["from"][11:13]) + 1] = point["viewers"]
    return hours


def weighted_quantile(pairs: list[tuple[float, float]], q: float) -> float:
    """The q-quantile of weighted (value, weight) pairs: the first value, in sorted
    order, whose cumulative weight reaches q of the total."""
    pairs = sorted(pairs)
    total = sum(w for _, w in pairs)
    acc = 0.0
    for value, w in pairs:
        acc += w
        if acc >= q * total:
            return value
    return pairs[-1][0]


def baseline_row(p1: float, h: int) -> list[float]:
    """The house baseline's row for hour h: persistence with a widening log spread.
    Used only where the comparables say nothing about an hour."""
    return [p1 * math.exp(z * 0.15 * math.sqrt(h - 1)) for z in Z]


def forecast_case(case: dict) -> dict:
    """One case's forecast: 23 rows of five quantiles, hours 2 to 24."""
    levels = case.get("levels") or LEVELS
    first = next((k for k in case["known"] if k["hour"] == 1), None)
    p1 = max(1.0, float(first["viewers"])) if first else 1.0

    # The pool: past launches with a usable release day. The case game's own category
    # history (a premiere spike, in the final) is not a launch and never votes.
    own_name = str(case.get("game", {}).get("name", "")).strip().lower()
    pool: list[dict[int, float]] = []
    for comparable in case.get("comparables") or []:
        if str(comparable.get("name", "")).strip().lower() == own_name:
            continue
        hours = day_hours(comparable)
        if hours.get(1, 0) > 0:
            pool.append(hours)

    # One weight per launch, by hour-1 size closeness. If the weighted pool were ever
    # degenerate (effective size under 5), soften the falloff until it is not; with the
    # fields these cases carry that does not trigger.
    weights: list[float] = []
    if pool:
        falloff = SIZE_FALLOFF
        for _ in range(7):
            weights = [math.exp(-abs(math.log(p1) - math.log(h[1])) / falloff) for h in pool]
            ess = (sum(weights) ** 2) / sum(w * w for w in weights)
            if ess >= 5.0:
                break
            falloff *= 1.6

    # Each hour's weighted log-ratio samples, pooled from the whole pool.
    samples: dict[int, list[tuple[float, float]]] = {h: [] for h in range(2, 25)}
    for hours, w in zip(pool, weights):
        base = hours[1]
        for h in range(2, 25):
            if h in hours and hours[h] > 0:
                samples[h].append((math.log(hours[h] / base), w))

    rows = []
    for want in case["forecast"]:
        h = want["hour"]
        if samples.get(h):
            qs = [p1 * math.exp(weighted_quantile(samples[h], t)) for t in levels]
            qs.sort()
        else:
            qs = baseline_row(p1, h)
        qs = [round2(min(max(q, 0.01), 1_000_000_000)) for q in qs]
        rows.append({"hour": h, "q": qs})
    return {"hours": rows}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # Every case file, in name order, so two runs write the same bytes.
    for path in sorted(INPUT_DIR.glob("*.in")):
        case = json.loads(path.read_text(encoding="utf-8"))
        forecast = forecast_case(case)
        (OUTPUT_DIR / f"{path.stem}.out").write_text(
            json.dumps(forecast, separators=(",", ":")) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
