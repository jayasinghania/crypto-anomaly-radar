"""Forecast math: pure functions, no database."""

import random

import pytest

from app.analytics.forecast import backtest, holt_forecast, mape, naive_forecast


def test_holt_extends_a_clean_linear_trend():
    series = [100 + 2 * i for i in range(30)]
    assert holt_forecast(series, 3) == pytest.approx([160.0, 162.0, 164.0])


def test_holt_needs_at_least_two_points():
    with pytest.raises(ValueError):
        holt_forecast([100.0])


def test_naive_repeats_the_last_price():
    assert naive_forecast([1.0, 2.0, 3.0], 3) == [3.0, 3.0, 3.0]


def test_mape_is_a_percentage():
    assert mape([100, 200], [110, 180]) == pytest.approx(10.0)


def test_mape_skips_zero_actuals():
    assert mape([0, 100], [5, 110]) == pytest.approx(10.0)


def test_mape_is_none_when_nothing_can_be_scored():
    assert mape([0], [1]) is None
    assert mape([], []) is None


def test_backtest_sample_count_matches_walk_forward_windows():
    series = [float(100 + i) for i in range(50)]
    for horizon in (1, 3, 5):
        result = backtest(series, horizon=horizon, min_train=10)
        assert result["samples"] == len(series) - 10 - horizon + 1


def test_backtest_on_a_trend_beats_naive():
    series = [100 + 2 * i for i in range(30)]
    result = backtest(series, horizon=3)
    assert result["beats_naive"] is True
    assert result["holt_mape"] == pytest.approx(0.0, abs=1e-9)
    assert result["naive_mape"] > 1.0


def test_backtest_on_a_random_walk_does_not_beat_naive():
    # The honest lesson of Phase 6: with no real pattern in the data,
    # chasing a trend loses to "the price stays where it is".
    random.seed(7)
    walk = [100.0]
    for _ in range(200):
        walk.append(walk[-1] + random.gauss(0, 1))
    assert backtest(walk, horizon=3)["beats_naive"] is False


def test_backtest_with_too_little_data_reports_zero_samples():
    result = backtest([1.0, 2.0, 3.0], horizon=1)
    assert result["samples"] == 0
    assert result["holt_mape"] is None
    assert result["beats_naive"] is False
