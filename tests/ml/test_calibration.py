from __future__ import annotations

import numpy as np
import pandas as pd

from brasileirao_data_lab.ml.calibration import (
    build_calibration_split,
    fit_temperature,
    temperature_scale_probabilities,
)


def test_temperature_scaling_preserves_probability_sum():
    probabilities = np.array(
        [
            [0.20, 0.30, 0.50],
            [0.60, 0.25, 0.15],
        ],
        dtype=float,
    )

    calibrated = (
        temperature_scale_probabilities(
            probabilities=probabilities,
            temperature=1.5,
        )
    )

    assert np.allclose(
        calibrated.sum(
            axis=1
        ),
        1.0,
    )


def test_temperature_one_preserves_probabilities():
    probabilities = np.array(
        [
            [0.20, 0.30, 0.50],
            [0.60, 0.25, 0.15],
        ],
        dtype=float,
    )

    calibrated = (
        temperature_scale_probabilities(
            probabilities=probabilities,
            temperature=1.0,
        )
    )

    assert np.allclose(
        calibrated,
        probabilities,
    )


def test_temperature_scaling_preserves_argmax():
    probabilities = np.array(
        [
            [0.20, 0.30, 0.50],
            [0.60, 0.25, 0.15],
        ],
        dtype=float,
    )

    calibrated = (
        temperature_scale_probabilities(
            probabilities=probabilities,
            temperature=2.0,
        )
    )

    assert np.array_equal(
        np.argmax(
            probabilities,
            axis=1,
        ),
        np.argmax(
            calibrated,
            axis=1,
        ),
    )


def test_fit_temperature_returns_positive_value():
    y_true = pd.Series(
        [
            "HOME",
            "DRAW",
            "AWAY",
            "HOME",
            "HOME",
            "DRAW",
        ]
    )

    classes = np.array(
        [
            "AWAY",
            "DRAW",
            "HOME",
        ]
    )

    probabilities = np.array(
        [
            [0.10, 0.20, 0.70],
            [0.10, 0.70, 0.20],
            [0.70, 0.20, 0.10],
            [0.10, 0.20, 0.70],
            [0.15, 0.20, 0.65],
            [0.10, 0.65, 0.25],
        ],
        dtype=float,
    )

    temperature = fit_temperature(
        y_true=y_true,
        probabilities=probabilities,
        classes=classes,
    )

    assert temperature > 0.0


def test_calibration_split_is_temporal():
    dataframe = pd.DataFrame(
        {
            "season": [
                2021,
                2022,
                2023,
                2024,
                2025,
                2026,
            ],
            "target": [
                "HOME",
                "DRAW",
                "AWAY",
                "HOME",
                "DRAW",
                "AWAY",
            ],
        }
    )

    split = build_calibration_split(
        dataframe
    )

    assert set(
        split.base_train[
            "season"
        ]
    ) == {
        2021,
        2022,
        2023,
        2024,
    }

    assert set(
        split.calibration[
            "season"
        ]
    ) == {
        2025,
    }

    assert set(
        split.reference[
            "season"
        ]
    ) == {
        2026,
    }