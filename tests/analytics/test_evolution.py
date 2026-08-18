import pandas as pd
import pytest

from brasileirao_data_lab.analytics.evolution import (
    get_latest_played_round,
    get_leader_changes,
    get_latest_position_changes,
    get_position_history,
    get_round_table,
    get_team_position_history,
)


def create_evolution_matches() -> pd.DataFrame:
    """
    Cria um campeonato fictício com quatro clubes.

    Rodada 1:
    A 2 x 0 B
    C 1 x 0 D

    Rodada 2:
    B 1 x 0 C
    D 0 x 0 A

    Rodada 3:
    C 3 x 0 A
    B 2 x 0 D

    Rodada 4 ainda não aconteceu.
    """

    return pd.DataFrame(
        [
            # Rodada 1
            {
                "match_id": 101,
                "match_number": 1,
                "round": 1,
                "date": "2026-01-10",
                "time": "18:00",
                "home_team_id": 1,
                "home_team": "Time A",
                "away_team_id": 2,
                "away_team": "Time B",
                "home_goals": 2,
                "away_goals": 0,
            },
            {
                "match_id": 102,
                "match_number": 2,
                "round": 1,
                "date": "2026-01-10",
                "time": "20:00",
                "home_team_id": 3,
                "home_team": "Time C",
                "away_team_id": 4,
                "away_team": "Time D",
                "home_goals": 1,
                "away_goals": 0,
            },

            # Rodada 2
            {
                "match_id": 103,
                "match_number": 3,
                "round": 2,
                "date": "2026-01-17",
                "time": "18:00",
                "home_team_id": 2,
                "home_team": "Time B",
                "away_team_id": 3,
                "away_team": "Time C",
                "home_goals": 1,
                "away_goals": 0,
            },
            {
                "match_id": 104,
                "match_number": 4,
                "round": 2,
                "date": "2026-01-17",
                "time": "20:00",
                "home_team_id": 4,
                "home_team": "Time D",
                "away_team_id": 1,
                "away_team": "Time A",
                "home_goals": 0,
                "away_goals": 0,
            },

            # Rodada 3
            {
                "match_id": 105,
                "match_number": 5,
                "round": 3,
                "date": "2026-01-24",
                "time": "18:00",
                "home_team_id": 3,
                "home_team": "Time C",
                "away_team_id": 1,
                "away_team": "Time A",
                "home_goals": 3,
                "away_goals": 0,
            },
            {
                "match_id": 106,
                "match_number": 6,
                "round": 3,
                "date": "2026-01-24",
                "time": "20:00",
                "home_team_id": 2,
                "home_team": "Time B",
                "away_team_id": 4,
                "away_team": "Time D",
                "home_goals": 2,
                "away_goals": 0,
            },

            # Rodada 4 futura
            {
                "match_id": 107,
                "match_number": 7,
                "round": 4,
                "date": "2026-01-31",
                "time": "18:00",
                "home_team_id": 1,
                "home_team": "Time A",
                "away_team_id": 3,
                "away_team": "Time C",
                "home_goals": None,
                "away_goals": None,
            },
            {
                "match_id": 108,
                "match_number": 8,
                "round": 4,
                "date": "2026-01-31",
                "time": "20:00",
                "home_team_id": 4,
                "home_team": "Time D",
                "away_team_id": 2,
                "away_team": "Time B",
                "home_goals": None,
                "away_goals": None,
            },
        ]
    )


# =============================================================================
# Rodada atual
# =============================================================================


def test_latest_played_round():
    matches = create_evolution_matches()

    latest_round = get_latest_played_round(
        matches
    )

    assert latest_round == 3


# =============================================================================
# Classificação por rodada
# =============================================================================


def test_round_table():
    matches = create_evolution_matches()

    table = get_round_table(
        matches,
        round_number=1,
    )

    assert len(table) == 4

    leader = table.iloc[0]

    assert leader["team"] == "Time A"
    assert leader["points"] == 3


# =============================================================================
# Histórico completo
# =============================================================================


def test_position_history():
    matches = create_evolution_matches()

    history = get_position_history(
        matches
    )

    assert len(history) == 12

    assert set(
        history["round"]
    ) == {
        1,
        2,
        3,
    }


# =============================================================================
# Histórico de um clube
# =============================================================================


def test_team_position_history():
    matches = create_evolution_matches()

    history = get_team_position_history(
        matches,
        team_id=1,
    )

    assert list(
        history["position"]
    ) == [
        1,
        1,
        3,
    ]

    assert list(
        history["points"]
    ) == [
        3,
        4,
        4,
    ]


# =============================================================================
# Mudanças de liderança
# =============================================================================


def test_leader_changes():
    matches = create_evolution_matches()

    changes = get_leader_changes(
        matches
    )

    assert len(changes) == 2

    assert (
        changes.iloc[0]["team"]
        == "Time A"
    )

    assert (
        changes.iloc[0]["round"]
        == 1
    )

    assert (
        changes.iloc[1]["team"]
        == "Time C"
    )

    assert (
        changes.iloc[1]["round"]
        == 3
    )


# =============================================================================
# Movimento de posições
# =============================================================================


def test_latest_position_changes():
    matches = create_evolution_matches()

    changes = get_latest_position_changes(
        matches
    )

    team_a = changes[
        changes["team_id"] == 1
    ].iloc[0]

    team_b = changes[
        changes["team_id"] == 2
    ].iloc[0]

    team_c = changes[
        changes["team_id"] == 3
    ].iloc[0]

    assert (
        team_a["previous_position"]
        == 1
    )

    assert (
        team_a["current_position"]
        == 3
    )

    assert (
        team_a["position_change"]
        == -2
    )

    assert (
        team_b["position_change"]
        == 1
    )

    assert (
        team_c["position_change"]
        == 1
    )


# =============================================================================
# Validação
# =============================================================================


def test_invalid_round():
    matches = create_evolution_matches()

    with pytest.raises(ValueError):
        get_round_table(
            matches,
            round_number=0,
        )