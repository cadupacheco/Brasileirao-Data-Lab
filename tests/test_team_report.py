import pandas as pd
import pytest

from brasileirao_data_lab.analytics.team_report import (
    format_date,
    get_next_match,
    get_team_averages,
    get_team_evolution_summary,
    get_team_future_matches,
    get_team_overdue_unscheduled_matches,
    get_team_report,
    get_team_unscheduled_matches,
    get_team_upcoming_unscheduled_matches,
)


def create_report_matches() -> pd.DataFrame:
    """
    Dataset fictício para testar
    o relatório individual.
    """

    return pd.DataFrame(
        [
            # -----------------------------------------------------------------
            # Rodada 1
            # -----------------------------------------------------------------
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
                "venue": "Estádio A",
                "city": "Cidade A",
                "state": "SP",
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
                "venue": "Estádio C",
                "city": "Cidade C",
                "state": "RJ",
            },

            # -----------------------------------------------------------------
            # Rodada 2
            # -----------------------------------------------------------------
            {
                "match_id": 103,
                "match_number": 3,
                "round": 2,
                "date": "2026-01-17",
                "time": "18:00",
                "home_team_id": 4,
                "home_team": "Time D",
                "away_team_id": 1,
                "away_team": "Time A",
                "home_goals": 1,
                "away_goals": 1,
                "venue": "Estádio D",
                "city": "Cidade D",
                "state": "MG",
            },
            {
                "match_id": 104,
                "match_number": 4,
                "round": 2,
                "date": "2026-01-17",
                "time": "20:00",
                "home_team_id": 2,
                "home_team": "Time B",
                "away_team_id": 3,
                "away_team": "Time C",
                "home_goals": 0,
                "away_goals": 1,
                "venue": "Estádio B",
                "city": "Cidade B",
                "state": "RS",
            },

            # -----------------------------------------------------------------
            # Rodada 3
            # -----------------------------------------------------------------
            {
                "match_id": 105,
                "match_number": 5,
                "round": 3,
                "date": "2026-01-24",
                "time": "18:00",
                "home_team_id": 1,
                "home_team": "Time A",
                "away_team_id": 3,
                "away_team": "Time C",
                "home_goals": 0,
                "away_goals": 3,
                "venue": "Estádio A",
                "city": "Cidade A",
                "state": "SP",
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
                "venue": "Estádio B",
                "city": "Cidade B",
                "state": "RS",
            },

            # -----------------------------------------------------------------
            # Rodada 4 adiada para o Time A
            # -----------------------------------------------------------------
            {
                "match_id": 109,
                "match_number": 9,
                "round": 4,
                "date": None,
                "time": None,
                "home_team_id": 1,
                "home_team": "Time A",
                "away_team_id": 4,
                "away_team": "Time D",
                "home_goals": None,
                "away_goals": None,
                "venue": None,
                "city": None,
                "state": None,
            },

            # -----------------------------------------------------------------
            # Rodada 5 já realizada entre outros clubes.
            #
            # Isso faz a rodada mais avançada com resultado ser a 5,
            # tornando a partida da rodada 4 uma pendência real.
            # -----------------------------------------------------------------
            {
                "match_id": 110,
                "match_number": 10,
                "round": 5,
                "date": "2026-02-07",
                "time": "18:00",
                "home_team_id": 2,
                "home_team": "Time B",
                "away_team_id": 3,
                "away_team": "Time C",
                "home_goals": 1,
                "away_goals": 1,
                "venue": "Estádio B",
                "city": "Cidade B",
                "state": "RS",
            },

            # -----------------------------------------------------------------
            # Rodada futura ainda sem data
            # -----------------------------------------------------------------
            {
                "match_id": 111,
                "match_number": 11,
                "round": 6,
                "date": None,
                "time": None,
                "home_team_id": 1,
                "home_team": "Time A",
                "away_team_id": 2,
                "away_team": "Time B",
                "home_goals": None,
                "away_goals": None,
                "venue": None,
                "city": None,
                "state": None,
            },

            # -----------------------------------------------------------------
            # Próxima partida com data definida
            # -----------------------------------------------------------------
            {
                "match_id": 107,
                "match_number": 7,
                "round": 24,
                "date": "2026-08-23",
                "time": "18:00",
                "home_team_id": 2,
                "home_team": "Time B",
                "away_team_id": 1,
                "away_team": "Time A",
                "home_goals": None,
                "away_goals": None,
                "venue": "Estádio B",
                "city": "Cidade B",
                "state": "RS",
            },

            # -----------------------------------------------------------------
            # Outra partida com data definida
            # -----------------------------------------------------------------
            {
                "match_id": 108,
                "match_number": 8,
                "round": 25,
                "date": "2026-08-30",
                "time": "20:00",
                "home_team_id": 3,
                "home_team": "Time C",
                "away_team_id": 1,
                "away_team": "Time A",
                "home_goals": None,
                "away_goals": None,
                "venue": "Estádio C",
                "city": "Cidade C",
                "state": "RJ",
            },
        ]
    )


# =============================================================================
# Jogos futuros
# =============================================================================


def test_team_future_matches():
    matches = create_report_matches()

    future = get_team_future_matches(
        matches,
        team_id=1,
    )

    assert len(future) == 4

    assert list(
        future["round"]
    ) == [
        24,
        25,
        4,
        6,
    ]


def test_next_match():
    matches = create_report_matches()

    next_match = get_next_match(
        matches,
        team_id=1,
    )

    assert next_match is not None

    assert (
        next_match["round"]
        == 24
    )

    assert (
        next_match["opponent"]
        == "Time B"
    )

    assert (
        next_match["home"]
        is False
    )

    assert (
        next_match["date"]
        == "2026-08-23"
    )

    assert (
        next_match["venue"]
        == "Estádio B"
    )


def test_next_match_prioritizes_defined_date():
    """
    Jogo antigo sem data não pode
    substituir o próximo compromisso confirmado.
    """

    matches = create_report_matches()

    next_match = get_next_match(
        matches,
        team_id=1,
    )

    assert next_match is not None

    assert (
        next_match["round"]
        != 4
    )

    assert (
        next_match["round"]
        == 24
    )


# =============================================================================
# Jogos sem data
# =============================================================================


def test_unscheduled_matches():
    matches = create_report_matches()

    unscheduled = (
        get_team_unscheduled_matches(
            matches,
            team_id=1,
        )
    )

    assert len(
        unscheduled
    ) == 2

    assert list(
        unscheduled["round"]
    ) == [
        4,
        6,
    ]


def test_overdue_unscheduled_matches():
    matches = create_report_matches()

    overdue = (
        get_team_overdue_unscheduled_matches(
            matches,
            team_id=1,
        )
    )

    assert len(
        overdue
    ) == 1

    assert (
        overdue.iloc[0][
            "round"
        ]
        == 4
    )


def test_upcoming_unscheduled_matches():
    matches = create_report_matches()

    upcoming = (
        get_team_upcoming_unscheduled_matches(
            matches,
            team_id=1,
        )
    )

    assert len(
        upcoming
    ) == 1

    assert (
        upcoming.iloc[0][
            "round"
        ]
        == 6
    )


# =============================================================================
# Evolução
# =============================================================================


def test_team_evolution_summary():
    matches = create_report_matches()

    evolution = (
        get_team_evolution_summary(
            matches,
            team_id=1,
        )
    )

    assert (
        evolution[
            "initial_position"
        ]
        == 1
    )

    assert (
        evolution[
            "best_position"
        ]
        == 1
    )

    assert (
        evolution[
            "worst_position"
        ]
        >= 1
    )

    assert (
        evolution[
            "current_position"
        ]
        is not None
    )


# =============================================================================
# Médias
# =============================================================================


def test_team_averages():
    profile = {
        "matches": 4,
        "goals_for": 8,
        "goals_against": 4,
        "points": 7,
    }

    averages = get_team_averages(
        profile
    )

    assert (
        averages[
            "goals_for_per_match"
        ]
        == 2.0
    )

    assert (
        averages[
            "goals_against_per_match"
        ]
        == 1.0
    )

    assert (
        averages[
            "points_per_match"
        ]
        == 1.75
    )


def test_team_averages_without_matches():
    profile = {
        "matches": 0,
        "goals_for": 0,
        "goals_against": 0,
        "points": 0,
    }

    averages = get_team_averages(
        profile
    )

    assert (
        averages[
            "goals_for_per_match"
        ]
        == 0
    )

    assert (
        averages[
            "goals_against_per_match"
        ]
        == 0
    )

    assert (
        averages[
            "points_per_match"
        ]
        == 0
    )


# =============================================================================
# Relatório completo
# =============================================================================


def test_team_report():
    matches = create_report_matches()

    report = get_team_report(
        matches,
        team_id=1,
        recent_n=5,
    )

    assert (
        report[
            "profile"
        ]["team"]
        == "Time A"
    )

    assert (
        report[
            "profile"
        ]["matches"]
        == 3
    )

    assert (
        len(
            report[
                "recent_matches"
            ]
        )
        == 3
    )

    assert (
        report[
            "next_match"
        ]["round"]
        == 24
    )

    assert (
        len(
            report[
                "unscheduled_matches"
            ]
        )
        == 2
    )

    assert (
        len(
            report[
                "overdue_unscheduled_matches"
            ]
        )
        == 1
    )

    assert (
        len(
            report[
                "upcoming_unscheduled_matches"
            ]
        )
        == 1
    )

    assert (
        "best_position"
        in report[
            "evolution"
        ]
    )

    assert (
        "points_per_match"
        in report[
            "averages"
        ]
    )


def test_invalid_recent_n():
    matches = create_report_matches()

    with pytest.raises(
        ValueError
    ):
        get_team_report(
            matches,
            team_id=1,
            recent_n=0,
        )


# =============================================================================
# Formatação
# =============================================================================


def test_format_date():
    assert (
        format_date(
            "2026-08-30"
        )
        == "30/08/2026"
    )

    assert (
        format_date(None)
        == "A definir"
    )