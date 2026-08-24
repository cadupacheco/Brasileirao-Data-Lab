from __future__ import annotations

import pandas as pd
import pytest

from fastapi.testclient import (
    TestClient,
)

import brasileirao_data_lab.api.player_router as comparison_api
from brasileirao_data_lab.api.app import (
    app,
)


def create_comparison_matches(
) -> pd.DataFrame:
    """
    Campeonato mínimo para
    testar a comparação.
    """

    return pd.DataFrame(
        [
            {
                "season": 2026,
                "round": 1,
                "match_id": 101,
                "match_number": 1,
                "group": "A",
                "date": "2026-01-10",
                "time": "18:00",
                "home_team_id": 1,
                "home_team": "Time A",
                "home_goals": 2,
                "away_team_id": 2,
                "away_team": "Time B",
                "away_goals": 0,
                "venue": "Estádio A",
                "city": "Cidade A",
                "state": "SP",
                "championship": (
                    "Brasileirão"
                ),
            },
            {
                "season": 2026,
                "round": 2,
                "match_id": 102,
                "match_number": 2,
                "group": "A",
                "date": "2026-01-17",
                "time": "20:00",
                "home_team_id": 2,
                "home_team": "Time B",
                "home_goals": 1,
                "away_team_id": 1,
                "away_team": "Time A",
                "away_goals": 1,
                "venue": "Estádio B",
                "city": "Cidade B",
                "state": "RS",
                "championship": (
                    "Brasileirão"
                ),
            },
            {
                "season": 2026,
                "round": 3,
                "match_id": 103,
                "match_number": 3,
                "group": "A",
                "date": "2026-01-24",
                "time": "18:00",
                "home_team_id": 1,
                "home_team": "Time A",
                "home_goals": 0,
                "away_team_id": 2,
                "away_team": "Time B",
                "away_goals": 1,
                "venue": "Estádio A",
                "city": "Cidade A",
                "state": "SP",
                "championship": (
                    "Brasileirão"
                ),
            },
            {
                "season": 2026,
                "round": 4,
                "match_id": 104,
                "match_number": 4,
                "group": "A",
                "date": "2026-01-31",
                "time": "18:00",
                "home_team_id": 2,
                "home_team": "Time B",
                "home_goals": None,
                "away_team_id": 1,
                "away_team": "Time A",
                "away_goals": None,
                "venue": "Estádio B",
                "city": "Cidade B",
                "state": "RS",
                "championship": (
                    "Brasileirão"
                ),
            },
        ]
    )


@pytest.fixture
def client(
    monkeypatch,
) -> TestClient:
    monkeypatch.setattr(
        comparison_api,
        "load_comparison_matches",
        create_comparison_matches,
    )

    return TestClient(
        app
    )


def test_compare_clubs(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/clubs/compare"
        "?team_a=1"
        "&team_b=2"
    )

    assert (
        response.status_code
        == 200
    )

    data = (
        response.json()
    )

    assert (
        data[
            "team_a"
        ][
            "team"
        ]
        == "Time A"
    )

    assert (
        data[
            "team_b"
        ][
            "team"
        ]
        == "Time B"
    )

    assert (
        data[
            "head_to_head"
        ][
            "matches"
        ]
        == 3
    )

    assert (
        data[
            "head_to_head"
        ][
            "team_a_wins"
        ]
        == 1
    )

    assert (
        data[
            "head_to_head"
        ][
            "team_b_wins"
        ]
        == 1
    )

    assert (
        data[
            "head_to_head"
        ][
            "draws"
        ]
        == 1
    )

    assert (
        len(
            data[
                "metric_winners"
            ]
        )
        > 0
    )


def test_compare_same_club_is_rejected(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/clubs/compare"
        "?team_a=1"
        "&team_b=1"
    )

    assert (
        response.status_code
        == 400
    )

    assert (
        response.json()[
            "detail"
        ]
        == (
            "Os clubes da comparação "
            "devem ser diferentes."
        )
    )


def test_compare_unknown_club_returns_404(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/clubs/compare"
        "?team_a=1"
        "&team_b=999"
    )

    assert (
        response.status_code
        == 404
    )


def test_compare_rejects_invalid_recent_n(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/clubs/compare"
        "?team_a=1"
        "&team_b=2"
        "&recent_n=0"
    )

    assert (
        response.status_code
        == 422
    )