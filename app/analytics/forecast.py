"""
Phase 6 - Forecasting.

Pure functions only: no database, no network. Give them a list of prices,
get numbers back. That makes them easy to test and easy to reason about.

Method: Holt's linear exponential smoothing (a smoothed "level" plus a
smoothed "trend", projected forward). It is deliberately simple. Crypto
prices behave close to a random walk, so the honest question is not "does
the model look clever" but "does it beat the naive baseline that just
repeats the last price". backtest() answers exactly that.
"""

from __future__ import annotations

DEFAULT_ALPHA = 0.5  # how fast the level reacts to new prices
DEFAULT_BETA = 0.3   # how fast the trend reacts


def holt_forecast(
    series: list[float],
    horizon: int = 5,
    alpha: float = DEFAULT_ALPHA,
    beta: float = DEFAULT_BETA,
) -> list[float]:
    """Forecast the next `horizon` values of `series` (oldest price first)."""
    if len(series) < 2:
        raise ValueError("Need at least 2 data points to forecast")

    level = series[0]
    trend = series[1] - series[0]
    for y in series[1:]:
        prev_level = level
        level = alpha * y + (1 - alpha) * (level + trend)
        trend = beta * (level - prev_level) + (1 - beta) * trend

    return [level + h * trend for h in range(1, horizon + 1)]


def naive_forecast(series: list[float], horizon: int = 5) -> list[float]:
    """Baseline: assume the price stays exactly where it is now."""
    return [series[-1]] * horizon


def mape(actual: list[float], predicted: list[float]) -> float | None:
    """Mean absolute percentage error, in percent. None if nothing to score."""
    errors = [abs(a - p) / abs(a) for a, p in zip(actual, predicted) if a != 0]
    if not errors:
        return None
    return 100.0 * sum(errors) / len(errors)


def backtest(
    series: list[float],
    horizon: int = 1,
    min_train: int = 10,
    alpha: float = DEFAULT_ALPHA,
    beta: float = DEFAULT_BETA,
) -> dict:
    """
    Walk-forward backtest: at each point, train only on the past, forecast
    `horizon` steps ahead, and compare with what actually happened. Never
    peeks at the future. Scores Holt and the naive baseline side by side.
    """
    actual: list[float] = []
    holt_preds: list[float] = []
    naive_preds: list[float] = []

    for t in range(min_train, len(series) - horizon + 1):
        train = series[:t]
        actual.append(series[t + horizon - 1])
        holt_preds.append(holt_forecast(train, horizon, alpha, beta)[-1])
        naive_preds.append(naive_forecast(train, horizon)[-1])

    holt_score = mape(actual, holt_preds)
    naive_score = mape(actual, naive_preds)

    return {
        "horizon": horizon,
        "samples": len(actual),
        "holt_mape": holt_score,
        "naive_mape": naive_score,
        "beats_naive": (
            holt_score is not None
            and naive_score is not None
            and holt_score < naive_score
        ),
    }
