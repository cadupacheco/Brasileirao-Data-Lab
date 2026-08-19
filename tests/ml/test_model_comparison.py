from __future__ import annotations

import numpy as np
import pandas as pd

from brasileirao_data_lab.ml.baseline import (
    FEATURE_COLUMNS,
    Metrics,
)
from brasileirao_data_lab.ml.model_comparison import (
    build_candidate_models,
    get_model_classes,
    select_best_model_name,
)


def build_training_dataframe() -> pd.DataFrame:
    rows = []

    targets = (
        "HOME",
        "DRAW",
        "AWAY",
    )

    for index in range(
        60
    ):
        target = targets[
            index
            % len(
                targets
            )
        ]

        row = {
            "target": target,
        }

        for feature_index, column in enumerate(
            FEATURE_COLUMNS
        ):
            row[
                column
            ] = float(
                (
                    index
                    % 10
                )
                + feature_index
                * 0.1
                + (
                    index
                    % 3
                )
                * 0.05
            )

        rows.append(
            row
        )

    return pd.DataFrame(
        rows
    )


def test_all_candidate_models_return_probabilities():
    dataframe = build_training_dataframe()

    x = dataframe[
        list(
            FEATURE_COLUMNS
        )
    ]

    y = dataframe[
        "target"
    ]

    for model in (
        build_candidate_models()
        .values()
    ):
        model.fit(
            x,
            y,
        )

        probabilities = (
            model.predict_proba(
                x
            )
        )

        assert np.allclose(
            probabilities.sum(
                axis=1
            ),
            1.0,
        )

        classes = get_model_classes(
            model
        )

        assert set(
            classes
        ) == {
            "HOME",
            "DRAW",
            "AWAY",
        }


def test_model_selection_uses_lowest_log_loss():
    metrics = {
        "model_a": Metrics(
            accuracy=0.60,
            log_loss=1.05,
            brier=0.60,
        ),
        "model_b": Metrics(
            accuracy=0.45,
            log_loss=0.98,
            brier=0.62,
        ),
        "model_c": Metrics(
            accuracy=0.55,
            log_loss=1.00,
            brier=0.58,
        ),
    }

    winner = select_best_model_name(
        metrics
    )

    assert winner == "model_b"


def test_brier_breaks_log_loss_tie():
    metrics = {
        "model_a": Metrics(
            accuracy=0.50,
            log_loss=1.00,
            brier=0.61,
        ),
        "model_b": Metrics(
            accuracy=0.49,
            log_loss=1.00,
            brier=0.59,
        ),
    }

    winner = select_best_model_name(
        metrics
    )

    assert winner == "model_b"