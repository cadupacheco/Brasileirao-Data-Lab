from __future__ import annotations

import pandas as pd
import pytest
from fastapi.testclient import TestClient

import brasileirao_data_lab.api.app as api_module


def create_prediction_matches() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "season": 2026,
                "round": 24,
                "match_id": 1001,
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
                "match_id": 1002,
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


def create_prediction_standings() -> pd.DataFrame:
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


@pytest.fixture
def prediction_client(
    monkeypatch,
) -> TestClient:
    monkeypatch.setattr(
        api_module,
        "load_match_predictions",
        create_prediction_matches,
    )

    monkeypatch.setattr(
        api_module,
        "load_season_simulation",
        create_prediction_standings,
    )

    return TestClient(
        api_module.app
    )


def test_prediction_matches_endpoint(
    prediction_client: TestClient,
):
    response = prediction_client.get(
        "/api/predictions/matches"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(
        data
    ) == 2

    assert data[
        0
    ][
        "home_team"
    ] == "Fluminense"

    assert data[
        0
    ][
        "home_probability_pct"
    ] == 67.0

    total = (
        data[
            0
        ][
            "home_probability"
        ]
        + data[
            0
        ][
            "draw_probability"
        ]
        + data[
            0
        ][
            "away_probability"
        ]
    )

    assert abs(
        total
        - 1.0
    ) < 1e-9


def test_prediction_matches_endpoint_filters_round(
    prediction_client: TestClient,
):
    response = prediction_client.get(
        "/api/predictions/matches?round_number=24"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(
        data
    ) == 1

    assert data[
        0
    ][
        "round"
    ] == 24


def test_prediction_matches_endpoint_filters_team(
    prediction_client: TestClient,
):
    response = prediction_client.get(
        "/api/predictions/matches?team_id=10"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(
        data
    ) == 2


def test_prediction_matches_endpoint_validates_round(
    prediction_client: TestClient,
):
    response = prediction_client.get(
        "/api/predictions/matches?round_number=39"
    )

    assert response.status_code == 422


def test_prediction_standings_endpoint(
    prediction_client: TestClient,
):
    response = prediction_client.get(
        "/api/predictions/standings"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(
        data
    ) == 2

    assert data[
        0
    ][
        "projected_position"
    ] == 1

    assert data[
        0
    ][
        "team_name"
    ] == "Flamengo"

    assert data[
        0
    ][
        "champion_probability_pct"
    ] == 55.25

    assert data[
        0
    ][
        "simulations"
    ] == 10000