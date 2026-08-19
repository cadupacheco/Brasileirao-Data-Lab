from __future__ import annotations

import pandas as pd
import pytest
from fastapi.testclient import TestClient

import brasileirao_data_lab.api.app as api_module


# =============================================================================
# Dados de teste
# =============================================================================


def create_api_matches() -> pd.DataFrame:
    """Cria um campeonato mínimo para testar a API."""

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
                "championship": "Brasileirão",
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
                "championship": "Brasileirão",
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
                "championship": "Brasileirão",
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
                "championship": "Brasileirão",
            },
        ]
    )


@pytest.fixture
def client(
    monkeypatch,
) -> TestClient:
    """Cria cliente HTTP utilizando dados controlados."""

    monkeypatch.setattr(
        api_module,
        "load_api_matches",
        create_api_matches,
    )

    return TestClient(
        api_module.app
    )


# =============================================================================
# Health
# =============================================================================


def test_health(
    client: TestClient,
):
    response = client.get(
        "/api/health"
    )

    assert response.status_code == 200

    assert response.json() == {
        "status": "ok",
        "version": "0.6.0",
    }


# =============================================================================
# Resumo
# =============================================================================


def test_championship_summary(
    client: TestClient,
):
    response = client.get(
        "/api/championship/summary"
    )

    assert response.status_code == 200

    data = response.json()

    assert data[
        "season"
    ] == 2026

    assert data[
        "total_matches"
    ] == 4

    assert data[
        "played_matches"
    ] == 3

    assert data[
        "future_matches"
    ] == 1

    assert data[
        "total_goals"
    ] == 5

    assert data[
        "latest_played_round"
    ] == 3

    assert data[
        "leader"
    ][
        "team"
    ] == "Time A"


# =============================================================================
# Classificação
# =============================================================================


def test_standings(
    client: TestClient,
):
    response = client.get(
        "/api/standings"
    )

    assert response.status_code == 200

    standings = response.json()

    assert len(
        standings
    ) == 2

    assert standings[
        0
    ][
        "team"
    ] == "Time A"

    assert standings[
        0
    ][
        "points"
    ] == 4

    assert standings[
        0
    ][
        "position"
    ] == 1


# =============================================================================
# Forma recente
# =============================================================================


def test_recent_form(
    client: TestClient,
):
    response = client.get(
        "/api/recent-form?last_n=2"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(
        data
    ) == 2

    assert all(
        team[
            "matches"
        ] == 2
        for team
        in data
    )


def test_recent_form_rejects_invalid_limit(
    client: TestClient,
):
    response = client.get(
        "/api/recent-form?last_n=0"
    )

    assert response.status_code == 422