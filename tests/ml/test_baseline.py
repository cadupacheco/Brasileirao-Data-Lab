from __future__ import annotations

import numpy as np
import pandas as pd

from brasileirao_data_lab.ml.baseline import (
    CLASS_ORDER,
    FEATURE_COLUMNS,
    build_model,
    multiclass_brier_score,
    split_by_time,
)


def build_test_dataframe() -> pd.DataFrame:
    rows = []

    for season in (
        2023,
        2024,
        2025,
        2026,
    ):
        for index, target in enumerate(
            (
                "HOME",
                "DRAW",
                "AWAY",
            )
        ):
            row = {
                "season": season,
                "target": target,
            }

            for column_index, column in enumerate(
                FEATURE_COLUMNS
            ):
                row[
                    column
                ] = float(
                    season
                    + index
                    + column_index
                )

            rows.append(
                row
            )

    return pd.DataFrame(
        rows
    )


def test_temporal_split_does_not_mix_future_seasons():
    dataframe = build_test_dataframe()

    split = split_by_time(
        dataframe
    )

    assert (
        split.train[
            "season"
        ].max()
        == 2024
    )

    assert set(
        split.validation[
            "season"
        ]
    ) == {
        2025
    }

    assert set(
        split.test[
            "season"
        ]
    ) == {
        2026
    }


def test_logistic_model_probabilities_sum_to_one():
    dataframe = build_test_dataframe()

    split = split_by_time(
        dataframe
    )

    model = build_model()

    model.fit(
        split.train[
            list(
                FEATURE_COLUMNS
            )
        ],
        split.train[
            "target"
        ],
    )

    probabilities = model.predict_proba(
        split.validation[
            list(
                FEATURE_COLUMNS
            )
        ]
    )

    assert np.allclose(
        probabilities.sum(
            axis=1
        ),
        1.0,
    )


def test_multiclass_brier_is_zero_for_perfect_predictions():
    y_true = pd.Series(
        [
            "AWAY",
            "DRAW",
            "HOME",
        ]
    )

    probabilities = np.eye(
        3
    )

    score = multiclass_brier_score(
        y_true=y_true,
        probabilities=probabilities,
        classes=np.array(
            CLASS_ORDER
        ),
    )

    assert score == 0.0