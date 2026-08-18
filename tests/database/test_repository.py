from __future__ import annotations

import pandas as pd
import pytest

from brasileirao_data_lab.database.init_db import (
    init_database,
)
from brasileirao_data_lab.database.repository import (
    get_matches_by_round,
    get_recent_team_matches_from_database,
    get_standings_by_round,
    get_team_matches_from_database,
    get_team_standings_history,
    get_upcoming_team_matches_from_database,
    resolve_team_from_database,
)
from brasileirao_data_lab.database.session import (
    create_database_engine,
    create_session_factory,
)
from brasileirao_data_lab.database.sync import (
    sync_database,
)


# =============================================================================
# Dataset
# =============================================================================


def create_repository_matches() -> pd.DataFrame:
    """
    Dataset com quatro clubes,
    três rodadas disputadas
    e duas partidas futuras.
    """

    return pd.DataFrame(
        [
            # -----------------------------------------------------------------
            # Rodada 1
            # -----------------------------------------------------------------
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
                "round": 1,
                "match_id": 102,
                "match_number": 2,
                "group": "A",
                "date": "2026-01-10",
                "time": "20:00",
                "home_team_id": 3,
                "home_team": "Time C",
                "home_goals": 1,
                "away_team_id": 4,
                "away_team": "Time D",
                "away_goals": 0,
                "venue": "Estádio C",
                "city": "Cidade C",
                "state": "RJ",
                "championship": "Brasileirão",
            },

            # -----------------------------------------------------------------
            # Rodada 2
            # -----------------------------------------------------------------
            {
                "season": 2026,
                "round": 2,
                "match_id": 103,
                "match_number": 3,
                "group": "A",
                "date": "2026-01-17",
                "time": "18:00",
                "home_team_id": 2,
                "home_team": "Time B",
                "home_goals": 1,
                "away_team_id": 3,
                "away_team": "Time C",
                "away_goals": 1,
                "venue": "Estádio B",
                "city": "Cidade B",
                "state": "RS",
                "championship": "Brasileirão",
            },
            {
                "season": 2026,
                "round": 2,
                "match_id": 104,
                "match_number": 4,
                "group": "A",
                "date": "2026-01-17",
                "time": "20:00",
                "home_team_id": 4,
                "home_team": "Time D",
                "home_goals": 0,
                "away_team_id": 1,
                "away_team": "Time A",
                "away_goals": 3,
                "venue": "Estádio D",
                "city": "Cidade D",
                "state": "MG",
                "championship": "Brasileirão",
            },

            # -----------------------------------------------------------------
            # Rodada 3
            # -----------------------------------------------------------------
            {
                "season": 2026,
                "round": 3,
                "match_id": 105,
                "match_number": 5,
                "group": "A",
                "date": "2026-01-24",
                "time": "18:00",
                "home_team_id": 1,
                "home_team": "Time A",
                "home_goals": 1,
                "away_team_id": 3,
                "away_team": "Time C",
                "away_goals": 2,
                "venue": "Estádio A",
                "city": "Cidade A",
                "state": "SP",
                "championship": "Brasileirão",
            },
            {
                "season": 2026,
                "round": 3,
                "match_id": 106,
                "match_number": 6,
                "group": "A",
                "date": "2026-01-24",
                "time": "20:00",
                "home_team_id": 2,
                "home_team": "Time B",
                "home_goals": 2,
                "away_team_id": 4,
                "away_team": "Time D",
                "away_goals": 0,
                "venue": "Estádio B",
                "city": "Cidade B",
                "state": "RS",
                "championship": "Brasileirão",
            },

            # -----------------------------------------------------------------
            # Rodada 4 futura com data
            # -----------------------------------------------------------------
            {
                "season": 2026,
                "round": 4,
                "match_id": 107,
                "match_number": 7,
                "group": "A",
                "date": "2026-01-31",
                "time": "18:30",
                "home_team_id": 3,
                "home_team": "Time C",
                "home_goals": None,
                "away_team_id": 1,
                "away_team": "Time A",
                "away_goals": None,
                "venue": "Estádio C",
                "city": "Cidade C",
                "state": "RJ",
                "championship": "Brasileirão",
            },

            # -----------------------------------------------------------------
            # Rodada 5 futura sem data
            # -----------------------------------------------------------------
            {
                "season": 2026,
                "round": 5,
                "match_id": 108,
                "match_number": 8,
                "group": "A",
                "date": None,
                "time": None,
                "home_team_id": 1,
                "home_team": "Time A",
                "home_goals": None,
                "away_team_id": 2,
                "away_team": "Time B",
                "away_goals": None,
                "venue": None,
                "city": None,
                "state": None,
                "championship": "Brasileirão",
            },
        ]
    )


def create_repository_database():
    """Cria e popula SQLite em memória."""

    database_engine = (
        create_database_engine(
            "sqlite+pysqlite:///:memory:"
        )
    )

    init_database(
        database_engine
    )

    session_factory = (
        create_session_factory(
            database_engine
        )
    )

    matches = (
        create_repository_matches()
    )

    with session_factory() as session:

        sync_database(
            session,
            matches,
        )

        session.commit()

    return session_factory


# =============================================================================
# Resolução do clube
# =============================================================================


def test_resolve_team_by_id_and_name():
    session_factory = (
        create_repository_database()
    )

    with session_factory() as session:

        by_id = (
            resolve_team_from_database(
                session,
                1,
            )
        )

        by_numeric_string = (
            resolve_team_from_database(
                session,
                "1",
            )
        )

        by_name = (
            resolve_team_from_database(
                session,
                "Time A",
            )
        )

        assert (
            by_id.team_id
            == 1
        )

        assert (
            by_numeric_string.team_id
            == 1
        )

        assert (
            by_name.team_id
            == 1
        )

        assert (
            by_name.name
            == "Time A"
        )


def test_resolve_invalid_team():
    session_factory = (
        create_repository_database()
    )

    with session_factory() as session:

        with pytest.raises(
            ValueError
        ):

            resolve_team_from_database(
                session,
                "Clube Inexistente",
            )


# =============================================================================
# Rodada
# =============================================================================


def test_get_matches_by_round():
    session_factory = (
        create_repository_database()
    )

    with session_factory() as session:

        matches = get_matches_by_round(
            session,
            season=2026,
            round_number=1,
        )

        assert len(
            matches
        ) == 2

        assert [
            match[
                "match_id"
            ]
            for match in matches
        ] == [
            101,
            102,
        ]

        assert (
            matches[0][
                "home_team"
            ]
            == "Time A"
        )


# =============================================================================
# Jogos do clube
# =============================================================================


def test_get_team_matches():
    session_factory = (
        create_repository_database()
    )

    with session_factory() as session:

        matches = (
            get_team_matches_from_database(
                session,
                team_id=1,
                season=2026,
            )
        )

        assert len(
            matches
        ) == 5

        assert [
            match[
                "round"
            ]
            for match in matches
        ] == [
            1,
            2,
            3,
            4,
            5,
        ]


# =============================================================================
# Jogos recentes
# =============================================================================


def test_get_recent_team_matches():
    session_factory = (
        create_repository_database()
    )

    with session_factory() as session:

        matches = (
            get_recent_team_matches_from_database(
                session,
                team_id=1,
                season=2026,
                limit=2,
            )
        )

        assert len(
            matches
        ) == 2

        assert [
            match[
                "round"
            ]
            for match in matches
        ] == [
            3,
            2,
        ]

        assert (
            matches[0][
                "match_id"
            ]
            == 105
        )


# =============================================================================
# Próximos jogos
# =============================================================================


def test_get_upcoming_team_matches():
    session_factory = (
        create_repository_database()
    )

    with session_factory() as session:

        matches = (
            get_upcoming_team_matches_from_database(
                session,
                team_id=1,
                season=2026,
            )
        )

        assert len(
            matches
        ) == 2

        assert (
            matches[0][
                "match_id"
            ]
            == 107
        )

        assert (
            matches[0][
                "round"
            ]
            == 4
        )

        assert (
            matches[1][
                "match_id"
            ]
            == 108
        )

        assert (
            matches[1][
                "date"
            ]
            is None
        )


# =============================================================================
# Classificação
# =============================================================================


def test_get_standings_by_round():
    session_factory = (
        create_repository_database()
    )

    with session_factory() as session:

        standings = (
            get_standings_by_round(
                session,
                season=2026,
                round_number=1,
            )
        )

        assert len(
            standings
        ) == 4

        assert [
            item[
                "position"
            ]
            for item in standings
        ] == [
            1,
            2,
            3,
            4,
        ]

        assert (
            standings[0][
                "points"
            ]
            == 3
        )


# =============================================================================
# Histórico
# =============================================================================


def test_get_team_standings_history():
    session_factory = (
        create_repository_database()
    )

    with session_factory() as session:

        history = (
            get_team_standings_history(
                session,
                season=2026,
                team_id=1,
            )
        )

        assert len(
            history
        ) == 3

        assert [
            item[
                "round"
            ]
            for item in history
        ] == [
            1,
            2,
            3,
        ]

        assert all(
            item[
                "team"
            ]
            == "Time A"
            for item in history
        )