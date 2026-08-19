from __future__ import annotations

import numpy as np
import pandas as pd

from brasileirao_data_lab.ml.predictions import (
    build_prediction_context,
    probability_for_class,
)


def build_small_history() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "season": 2025,
                "round": 1,
                "match_id": 1,
                "match_number": 1,
                "date": "2025-03-01",
                "time": "16:00",
                "home_team_id": 1,
                "home_team": "Palmeiras",
                "home_goals": 2,
                "away_team_id": 2,
                "away_team": "Flamengo",
                "away_goals": 1,
                "status": "played",
                "result": "HOME",
            },
            {
                "season": 2026,
                "round": 1,
                "match_id": 2,
                "match_number": 1,
                "date": "2026-01-01",
                "time": "19:00",
                "home_team_id": 2,
                "home_team": "Flamengo",
                "home_goals": 1,
                "away_team_id": 1,
                "away_team": "Palmeiras",
                "away_goals": 1,
                "status": "played",
                "result": "DRAW",
            },
            {
                "season": 2026,
                "round": 2,
                "match_id": 3,
                "match_number": 11,
                "date": "2026-01-08",
                "time": "19:00",
                "home_team_id": 1,
                "home_team": "Palmeiras",
                "home_goals": None,
                "away_team_id": 2,
                "away_team": "Flamengo",
                "away_goals": None,
                "status": "upcoming",
                "result": None,
            },
        ]
    )


def test_prediction_context_uses_only_played_matches():
    history = build_small_history()

    context = build_prediction_context(
        history
    )

    palmeiras = context.season_states[
        "palmeiras"
    ]

    flamengo = context.season_states[
        "flamengo"
    ]

    assert palmeiras.matches == 1
    assert flamengo.matches == 1

    assert palmeiras.points == 1
    assert flamengo.points == 1


def test_prediction_context_keeps_historical_h2h():
    history = build_small_history()

    context = build_prediction_context(
        history
    )

    pair = tuple(
        sorted(
            (
                "palmeiras",
                "flamengo",
            )
        )
    )

    assert (
        context.h2h_states[
            pair
        ].meetings
        == 2
    )


def test_probability_for_class_returns_correct_column():
    probabilities = np.array(
        [
            [0.20, 0.30, 0.50],
            [0.40, 0.35, 0.25],
        ]
    )

    classes = np.array(
        [
            "AWAY",
            "DRAW",
            "HOME",
        ]
    )

    home = probability_for_class(
        probabilities,
        classes,
        "HOME",
    )

    assert np.allclose(
        home,
        np.array(
            [
                0.50,
                0.25,
            ]
        ),
    )