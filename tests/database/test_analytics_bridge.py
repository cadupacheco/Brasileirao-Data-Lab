from __future__ import annotations

import pandas as pd
import pytest

from brasileirao_data_lab.database.analytics_bridge import (
    build_analytics_snapshot,
    compare_analytics_sources,
    get_latest_analytics_season,
    load_matches_for_analytics,
)
from brasileirao_data_lab.database.init_db import (
    init_database,
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


def create_bridge_matches() -> pd.DataFrame:
    """
    Campeonato fictício com quatro clubes,
    três rodadas realizadas e uma futura.
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
            # Rodada 4 futura
            # -----------------------------------------------------------------
            {
                "season": 2026,
                "round": 4,
                "match_id": 107,
                "match_number": 7,
                "group": "A",
                "date": "2026-01-31",
                "time": "18:00",
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
            {
                "season": 2026,
                "round": 4,
                "match_id": 108,
                "match_number": 8,
                "group": "A",
                "date": None,
                "time": None,
                "home_team_id": 4,
                "home_team": "Time D",
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


def create_bridge_database():
    """Cria SQLite em memória já populado."""

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

    matches = create_bridge_matches()

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


def test_get_latest_analytics_season():
    session_factory = (
        create_bridge_database()
    )

    with session_factory() as session:

        season = (
            get_latest_analytics_season(
                session
            )
        )

        assert season == 2026


# =============================================================================
# Carregamento
# =============================================================================


def test_load_matches_for_analytics():
    session_factory = (
        create_bridge_database()
    )

    with session_factory() as session:

        matches = (
            load_matches_for_analytics(
                session
            )
        )

        assert len(
            matches
        ) == 8

        assert set(
            matches[
                "season"
            ].dropna()
        ) == {
            2026
        }

        assert set(
            matches[
                "home_team"
            ]
        ) == {
            "Time A",
            "Time B",
            "Time C",
            "Time D",
        }


# =============================================================================
# Snapshot
# =============================================================================


def test_build_analytics_snapshot():
    matches = create_bridge_matches()

    snapshot = (
        build_analytics_snapshot(
            matches
        )
    )

    assert (
        "summary"
        in snapshot
    )

    assert (
        "standings"
        in snapshot
    )

    assert (
        "home_away"
        in snapshot
    )

    assert (
        "recent_form"
        in snapshot
    )

    assert (
        "position_history"
        in snapshot
    )


# =============================================================================
# Paridade
# =============================================================================


def test_identical_analytics_sources_match():
    matches = create_bridge_matches()

    result = (
        compare_analytics_sources(
            matches,
            matches.copy(),
        )
    )

    assert (
        result[
            "exact_match"
        ]
        is True
    )

    assert all(
        result[
            "sections"
        ].values()
    )


def test_database_produces_same_analytics_as_dataframe():
    csv_matches = (
        create_bridge_matches()
    )

    session_factory = (
        create_bridge_database()
    )

    with session_factory() as session:

        database_matches = (
            load_matches_for_analytics(
                session
            )
        )

    result = (
        compare_analytics_sources(
            csv_matches,
            database_matches,
        )
    )

    assert (
        result[
            "exact_match"
        ]
        is True
    )

    assert result[
        "sections"
    ] == {
        "summary": True,
        "standings": True,
        "home_away": True,
        "recent_form": True,
        "position_history": True,
    }


# =============================================================================
# Divergência
# =============================================================================


def test_analytics_bridge_detects_difference():
    csv_matches = (
        create_bridge_matches()
    )

    database_matches = (
        csv_matches.copy()
    )

    database_matches.loc[
        database_matches[
            "match_id"
        ] == 101,
        "home_goals",
    ] = 9

    result = (
        compare_analytics_sources(
            csv_matches,
            database_matches,
        )
    )

    assert (
        result[
            "exact_match"
        ]
        is False
    )

    assert (
        not all(
            result[
                "sections"
            ].values()
        )
    )


# =============================================================================
# Temporada inexistente
# =============================================================================


def test_load_missing_season():
    session_factory = (
        create_bridge_database()
    )

    with session_factory() as session:

        with pytest.raises(
            ValueError,
            match=(
                "Nenhuma partida encontrada"
            ),
        ):

            load_matches_for_analytics(
                session,
                season=2025,
            )