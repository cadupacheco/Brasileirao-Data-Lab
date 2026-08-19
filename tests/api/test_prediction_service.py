from __future__ import annotations

from pathlib import Path

import pandas as pd

from brasileirao_data_lab.api.prediction_service import (
    get_match_predictions,
    get_standings_predictions,
    load_match_predictions,
    load_season_simulation,
)


def create_match_predictions() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "season": 2026,
                "round": 24,
                "match_id": 1,
                "date": "2026-08-22",
                "time": "16:00",
                "home_team_id": 10,
                "home_team": "Fluminense",
                "home_team_key": "fluminense",
                "away_team_id": 20,
                "away_team": "Remo",
                "away_team_key": "remo",
                "home_probability": 0.67,
                "draw_probability": 0.19,
                "away_probability": 0.14,
                "predicted_result": "HOME",
                "home_probability_pct": 67.0,
                "draw_probability_pct": 19.0,
                "away_probability_pct": 14.0,
            },
            {
                "season": 2026,
                "round": 25,
                "match_id": 2,
                "date": "2026-08-29",
                "time": "18:30",
                "home_team_id": 30,
                "home_team": "Palmeiras",
                "home_team_key": "palmeiras",
                "away_team_id": 10,
                "away_team": "Fluminense",
                "away_team_key": "fluminense",
                "home_probability": 0.55,
                "draw_probability": 0.27,
                "away_probability": 0.18,
                "predicted_result": "HOME",
                "home_probability_pct": 55.0,
                "draw_probability_pct": 27.0,
                "away_probability_pct": 18.0,
            },
        ]
    )


def create_simulation() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "season": 2026,
                "team_key": "flamengo",
                "team_name": "Flamengo",
                "simulations": 10000,
                "expected_points": 76.2,
                "average_position": 1.7,
                "champion_probability": 0.5525,
                "top4_probability": 0.9976,
                "top6_probability": 1.0,
                "relegation_probability": 0.0,
                "champion_probability_pct": 55.25,
                "top4_probability_pct": 99.76,
                "top6_probability_pct": 100.0,
                "relegation_probability_pct": 0.0,
            },
            {
                "season": 2026,
                "team_key": "palmeiras",
                "team_name": "Palmeiras",
                "simulations": 10000,
                "expected_points": 75.3,
                "average_position": 1.9,
                "champion_probability": 0.4345,
                "top4_probability": 0.9974,
                "top6_probability": 0.9999,
                "relegation_probability": 0.0,
                "champion_probability_pct": 43.45,
                "top4_probability_pct": 99.74,
                "top6_probability_pct": 99.99,
                "relegation_probability_pct": 0.0,
            },
        ]
    )


def test_get_match_predictions_filters_round():
    result = get_match_predictions(
        dataframe=create_match_predictions(),
        round_number=24,
    )

    assert len(
        result
    ) == 1

    assert result[
        0
    ][
        "home_team"
    ] == "Fluminense"


def test_get_match_predictions_filters_team():
    result = get_match_predictions(
        dataframe=create_match_predictions(),
        team_id=10,
    )

    assert len(
        result
    ) == 2


def test_match_prediction_probabilities_sum_to_one():
    result = get_match_predictions(
        dataframe=create_match_predictions(),
    )

    for match in result:
        total = (
            match[
                "home_probability"
            ]
            + match[
                "draw_probability"
            ]
            + match[
                "away_probability"
            ]
        )

        assert abs(
            total
            - 1.0
        ) < 1e-9


def test_get_standings_predictions_orders_by_average_position():
    dataframe = create_simulation()

    result = get_standings_predictions(
        dataframe
    )

    assert result[
        0
    ][
        "team_name"
    ] == "Flamengo"

    assert result[
        0
    ][
        "projected_position"
    ] == 1


def test_load_match_predictions_from_csv(
    tmp_path: Path,
):
    path = (
        tmp_path
        / "future_predictions.csv"
    )

    create_match_predictions().to_csv(
        path,
        index=False,
    )

    loaded = load_match_predictions(
        path
    )

    assert len(
        loaded
    ) == 2


def test_load_season_simulation_from_csv(
    tmp_path: Path,
):
    path = (
        tmp_path
        / "season_simulation.csv"
    )

    create_simulation().to_csv(
        path,
        index=False,
    )

    loaded = load_season_simulation(
        path
    )

    assert len(
        loaded
    ) == 2