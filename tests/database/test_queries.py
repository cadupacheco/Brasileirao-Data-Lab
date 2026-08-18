from __future__ import annotations

import pandas as pd

from brasileirao_data_lab.database.init_db import (
    init_database,
)
from brasileirao_data_lab.database.queries import (
    get_latest_database_season,
    print_recent_query,
    print_round_query,
    print_standings_query,
    print_team_query,
    print_upcoming_query,
    resolve_database_season,
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


def create_queries_matches() -> pd.DataFrame:
    """Dataset pequeno para testar a CLI."""

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


def create_queries_database():
    """Cria e popula banco SQLite em memória."""

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

    matches = create_queries_matches()

    with session_factory() as session:

        sync_database(
            session,
            matches,
        )

        session.commit()

    return session_factory


# =============================================================================
# Temporada
# =============================================================================


def test_latest_database_season():
    session_factory = (
        create_queries_database()
    )

    with session_factory() as session:

        season = (
            get_latest_database_season(
                session
            )
        )

        assert season == 2026


def test_resolve_database_season():
    session_factory = (
        create_queries_database()
    )

    with session_factory() as session:

        automatic = (
            resolve_database_season(
                session
            )
        )

        explicit = (
            resolve_database_season(
                session,
                2025,
            )
        )

        assert automatic == 2026
        assert explicit == 2025


# =============================================================================
# Clube
# =============================================================================


def test_print_team_query(
    capsys,
):
    session_factory = (
        create_queries_database()
    )

    with session_factory() as session:

        print_team_query(
            session,
            "Time A",
        )

    output = capsys.readouterr().out

    assert (
        "Time A"
        in output
    )

    assert (
        "Temporada: 2026"
        in output
    )

    assert (
        "Partidas cadastradas: 3"
        in output
    )


# =============================================================================
# Rodada
# =============================================================================


def test_print_round_query(
    capsys,
):
    session_factory = (
        create_queries_database()
    )

    with session_factory() as session:

        print_round_query(
            session,
            round_number=1,
        )

    output = capsys.readouterr().out

    assert (
        "Rodada: 1"
        in output
    )

    assert (
        "Time A"
        in output
    )

    assert (
        "Time B"
        in output
    )

    assert (
        "2 x 0"
        in output
    )


# =============================================================================
# Recentes
# =============================================================================


def test_print_recent_query(
    capsys,
):
    session_factory = (
        create_queries_database()
    )

    with session_factory() as session:

        print_recent_query(
            session,
            "Time A",
            limit=2,
        )

    output = capsys.readouterr().out

    assert (
        "Jogos recentes"
        in output
    )

    assert (
        "Time A"
        in output
    )

    assert (
        "R2"
        in output
    )

    assert (
        "R1"
        in output
    )


# =============================================================================
# Próximos
# =============================================================================


def test_print_upcoming_query(
    capsys,
):
    session_factory = (
        create_queries_database()
    )

    with session_factory() as session:

        print_upcoming_query(
            session,
            "Time A",
        )

    output = capsys.readouterr().out

    assert (
        "Próximos jogos"
        in output
    )

    assert (
        "R3"
        in output
    )

    assert (
        "A definir"
        in output
    )


# =============================================================================
# Classificação
# =============================================================================


def test_print_standings_query(
    capsys,
):
    session_factory = (
        create_queries_database()
    )

    with session_factory() as session:

        print_standings_query(
            session,
            round_number=1,
        )

    output = capsys.readouterr().out

    assert (
        "Classificação"
        in output
    )

    assert (
        "Rodada 1"
        in output
    )

    assert (
        "Time A"
        in output
    )

    assert (
        "Time B"
        in output
    )