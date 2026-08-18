from pathlib import Path

import pytest

from brasileirao_data_lab.scrapers.cbf import (
    fetch_round,
    parse_location,
    parse_match_date,
    parse_match_time,
    parse_round_matches,
    parse_standings,
    resolve_next_opponents,
)


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

HTML_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "cbf_serie_a_2026.html"
)


# =============================================================================
# Fixtures auxiliares
# =============================================================================


def load_html() -> str:
    """Carrega o HTML real salvo durante a coleta."""

    return HTML_FILE.read_text(
        encoding="utf-8"
    )


def get_standings():
    """Retorna a classificação processada."""

    html = load_html()

    standings = parse_standings(
        html
    )

    return resolve_next_opponents(
        standings
    )


# =============================================================================
# Testes da classificação
# =============================================================================


def test_standings_has_20_teams():
    standings = get_standings()

    assert len(standings) == 20


def test_positions_are_unique():
    standings = get_standings()

    positions = [
        team["position"]
        for team in standings
    ]

    assert len(positions) == len(
        set(positions)
    )


def test_team_ids_are_unique():
    standings = get_standings()

    team_ids = [
        team["team_id"]
        for team in standings
    ]

    assert len(team_ids) == len(
        set(team_ids)
    )


def test_points_are_consistent():
    standings = get_standings()

    for team in standings:

        expected_points = (
            team["wins"] * 3
            + team["draws"]
        )

        assert (
            team["points"]
            == expected_points
        )


def test_matches_are_consistent():
    standings = get_standings()

    for team in standings:

        expected_matches = (
            team["wins"]
            + team["draws"]
            + team["losses"]
        )

        assert (
            team["matches"]
            == expected_matches
        )


def test_goal_difference_is_consistent():
    standings = get_standings()

    for team in standings:

        expected_difference = (
            team["goals_for"]
            - team["goals_against"]
        )

        assert (
            team["goal_difference"]
            == expected_difference
        )


def test_next_opponents_exist():
    standings = get_standings()

    teams = {
        team["team"]
        for team in standings
    }

    for team in standings:

        opponent = team[
            "next_opponent"
        ]

        if opponent is not None:
            assert opponent in teams


# =============================================================================
# Testes dos jogos
# =============================================================================


def test_parse_completed_match():
    data = {
        "grupos": [
            "GRUPO ÚNICO"
        ],
        "jogos": [
            {
                "grupo": "GRUPO ÚNICO",
                "jogo": [
                    {
                        "id_jogo": "831894",
                        "num_jogo": "6",
                        "rodada": "1",
                        "grupo": "GRUPO ÚNICO",
                        "mandante": {
                            "id": "62194",
                            "nome": "Atlético Mineiro",
                            "gols": "2",
                        },
                        "visitante": {
                            "id": "20002",
                            "nome": "Palmeiras",
                            "gols": "2",
                        },
                        "local": (
                            "ARENA MRV - "
                            "Belo Horizonte - MG"
                        ),
                        "campeonato": (
                            "Campeonato Brasileiro"
                        ),
                        "data": " 28/01/2026",
                        "hora": "19:00",
                    }
                ],
            }
        ],
    }

    matches = parse_round_matches(
        data
    )

    assert len(matches) == 1

    match = matches[0]

    assert match["season"] == 2026
    assert match["round"] == 1
    assert match["match_id"] == 831894
    assert match["match_number"] == 6

    assert match["home_team_id"] == 62194
    assert (
        match["home_team"]
        == "Atlético Mineiro"
    )
    assert match["home_goals"] == 2

    assert match["away_team_id"] == 20002
    assert (
        match["away_team"]
        == "Palmeiras"
    )
    assert match["away_goals"] == 2

    assert match["date"] == "2026-01-28"
    assert match["time"] == "19:00"

    assert match["venue"] == "ARENA MRV"
    assert match["city"] == "Belo Horizonte"
    assert match["state"] == "MG"


def test_parse_future_match():
    data = {
        "jogos": [
            {
                "jogo": [
                    {
                        "id_jogo": "832133",
                        "num_jogo": "244",
                        "rodada": "25",
                        "grupo": "GRUPO ÚNICO",
                        "mandante": {
                            "id": "20001",
                            "nome": "Corinthians",
                            "gols": None,
                        },
                        "visitante": {
                            "id": "20008",
                            "nome": "Santos FC",
                            "gols": None,
                        },
                        "local": (
                            "Neo Química Arena - "
                            "Sao Paulo - SP"
                        ),
                        "campeonato": (
                            "Campeonato Brasileiro"
                        ),
                        "data": "A Definir",
                        "hora": "A Definir",
                    }
                ]
            }
        ]
    }

    matches = parse_round_matches(
        data
    )

    assert len(matches) == 1

    match = matches[0]

    assert match["home_goals"] is None
    assert match["away_goals"] is None

    assert match["date"] is None
    assert match["time"] is None

    assert match["round"] == 25

    assert (
        match["home_team"]
        == "Corinthians"
    )

    assert (
        match["away_team"]
        == "Santos FC"
    )


def test_parse_location():
    venue, city, state = parse_location(
        "Neo Química Arena - Sao Paulo - SP"
    )

    assert venue == "Neo Química Arena"
    assert city == "Sao Paulo"
    assert state == "SP"


def test_invalid_round():
    with pytest.raises(ValueError):
        fetch_round(0)

    with pytest.raises(ValueError):
        fetch_round(39)


def test_undefined_match_date():
    assert (
        parse_match_date("A Definir")
        is None
    )

    assert (
        parse_match_date("A Confirmar")
        is None
    )

    assert (
        parse_match_date(None)
        is None
    )


def test_undefined_match_time():
    assert (
        parse_match_time("A Definir")
        is None
    )

    assert (
        parse_match_time("A Confirmar")
        is None
    )

    assert (
        parse_match_time(None)
        is None
    )