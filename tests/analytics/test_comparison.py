import pandas as pd
import pytest

from brasileirao_data_lab.analytics.comparison import (
    compare_teams,
    get_head_to_head,
    get_metric_winner,
    get_team_profile,
    normalize_team_name,
    resolve_team,
)


def create_comparison_matches() -> pd.DataFrame:
    """
    Campeonato fictício com quatro clubes.

    Time A:
    - vence Time B
    - vence Time D
    - perde para Time B

    Isso também cria dois confrontos diretos
    entre Time A e Time B.
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
                "away_goals": 1,
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
                "away_goals": 1,
            },

            # Rodada 3
            {
                "match_id": 105,
                "match_number": 5,
                "round": 3,
                "date": "2026-01-24",
                "time": "18:00",
                "home_team_id": 2,
                "home_team": "Time B",
                "away_team_id": 1,
                "away_team": "Time A",
                "home_goals": 3,
                "away_goals": 1,
            },
            {
                "match_id": 106,
                "match_number": 6,
                "round": 3,
                "date": "2026-01-24",
                "time": "20:00",
                "home_team_id": 3,
                "home_team": "Time C",
                "away_team_id": 4,
                "away_team": "Time D",
                "home_goals": 2,
                "away_goals": 2,
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
# Normalização
# =============================================================================


def test_normalize_team_name():
    assert (
        normalize_team_name(
            "  Atlético   Mineiro "
        )
        == "atletico mineiro"
    )


# =============================================================================
# Resolução de clubes
# =============================================================================


def test_resolve_team_by_id():
    matches = (
        create_comparison_matches()
    )

    team = resolve_team(
        matches,
        1,
    )

    assert team["team_id"] == 1
    assert team["team"] == "Time A"


def test_resolve_team_by_name():
    matches = (
        create_comparison_matches()
    )

    team = resolve_team(
        matches,
        "time a",
    )

    assert team["team_id"] == 1
    assert team["team"] == "Time A"


def test_invalid_team():
    matches = (
        create_comparison_matches()
    )

    with pytest.raises(
        ValueError
    ):
        resolve_team(
            matches,
            "Time Inexistente",
        )


# =============================================================================
# Perfil
# =============================================================================


def test_team_profile():
    matches = (
        create_comparison_matches()
    )

    profile = get_team_profile(
        matches,
        team_id=1,
        recent_n=5,
    )

    assert (
        profile["team"]
        == "Time A"
    )

    assert (
        profile["matches"]
        == 3
    )

    assert (
        profile["wins"]
        == 2
    )

    assert (
        profile["draws"]
        == 0
    )

    assert (
        profile["losses"]
        == 1
    )

    assert (
        profile["points"]
        == 6
    )

    assert (
        profile["goals_for"]
        == 4
    )

    assert (
        profile["goals_against"]
        == 3
    )

    assert (
        profile["recent_form"]
        == "V V D"
    )


# =============================================================================
# Confronto direto
# =============================================================================


def test_head_to_head():
    matches = (
        create_comparison_matches()
    )

    head_to_head = (
        get_head_to_head(
            matches,
            team_a_id=1,
            team_b_id=2,
        )
    )

    assert (
        head_to_head["matches"]
        == 2
    )

    assert (
        head_to_head[
            "team_a_wins"
        ]
        == 1
    )

    assert (
        head_to_head[
            "team_b_wins"
        ]
        == 1
    )

    assert (
        head_to_head["draws"]
        == 0
    )

    assert (
        head_to_head[
            "team_a_goals"
        ]
        == 3
    )

    assert (
        head_to_head[
            "team_b_goals"
        ]
        == 3
    )


# =============================================================================
# Vencedor de métrica
# =============================================================================


def test_metric_winner():
    team_a = {
        "team_id": 1,
        "points": 10,
        "position": 2,
    }

    team_b = {
        "team_id": 2,
        "points": 7,
        "position": 5,
    }

    assert (
        get_metric_winner(
            team_a,
            team_b,
            "points",
        )
        == 1
    )

    assert (
        get_metric_winner(
            team_a,
            team_b,
            "position",
            lower_is_better=True,
        )
        == 1
    )


# =============================================================================
# Comparação completa
# =============================================================================


def test_compare_teams():
    matches = (
        create_comparison_matches()
    )

    comparison = compare_teams(
        matches,
        team_a_id=1,
        team_b_id=2,
        recent_n=5,
    )

    assert (
        comparison[
            "team_a"
        ]["team"]
        == "Time A"
    )

    assert (
        comparison[
            "team_b"
        ]["team"]
        == "Time B"
    )

    assert (
        comparison[
            "head_to_head"
        ]["matches"]
        == 2
    )

    assert (
        "points"
        in comparison[
            "metric_winners"
        ]
    )

    assert (
        1
        in comparison[
            "advantages"
        ]
    )

    assert (
        2
        in comparison[
            "advantages"
        ]
    )


def test_cannot_compare_same_team():
    matches = (
        create_comparison_matches()
    )

    with pytest.raises(
        ValueError
    ):
        compare_teams(
            matches,
            team_a_id=1,
            team_b_id=1,
        )