from __future__ import annotations

import pandas as pd

from brasileirao_data_lab.ml.backtest import (
    AggregateResult,
    build_backtest_fold,
    select_backtest_winner,
)


def test_backtest_fold_uses_only_past_seasons():
    dataframe = pd.DataFrame(
        {
            "season": [
                2021,
                2022,
                2023,
                2024,
            ],
            "target": [
                "HOME",
                "DRAW",
                "AWAY",
                "HOME",
            ],
        }
    )

    train, validation = (
        build_backtest_fold(
            dataframe=dataframe,
            validation_season=2024,
        )
    )

    assert set(
        train[
            "season"
        ]
    ) == {
        2021,
        2022,
        2023,
    }

    assert set(
        validation[
            "season"
        ]
    ) == {
        2024,
    }


def test_backtest_winner_uses_lowest_mean_log_loss():
    results = [
        AggregateResult(
            model_name="a",
            folds=3,
            mean_accuracy=0.55,
            mean_log_loss=1.01,
            mean_brier=0.61,
        ),
        AggregateResult(
            model_name="b",
            folds=3,
            mean_accuracy=0.49,
            mean_log_loss=0.98,
            mean_brier=0.63,
        ),
        AggregateResult(
            model_name="c",
            folds=3,
            mean_accuracy=0.52,
            mean_log_loss=1.00,
            mean_brier=0.60,
        ),
    ]

    winner = select_backtest_winner(
        results
    )

    assert winner == "b"


def test_backtest_winner_uses_brier_as_tiebreaker():
    results = [
        AggregateResult(
            model_name="a",
            folds=3,
            mean_accuracy=0.55,
            mean_log_loss=1.00,
            mean_brier=0.61,
        ),
        AggregateResult(
            model_name="b",
            folds=3,
            mean_accuracy=0.49,
            mean_log_loss=1.00,
            mean_brier=0.59,
        ),
    ]

    winner = select_backtest_winner(
        results
    )

    assert winner == "b"